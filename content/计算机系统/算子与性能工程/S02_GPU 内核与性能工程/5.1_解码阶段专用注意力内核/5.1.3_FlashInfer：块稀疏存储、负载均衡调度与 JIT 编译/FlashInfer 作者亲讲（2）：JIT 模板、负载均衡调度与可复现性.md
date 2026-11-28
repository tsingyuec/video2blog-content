# FlashInfer 作者亲讲（2）：JIT 模板、负载均衡调度与可复现性

> 视频来源：[Lecture 41: FlashInfer | GPU MODE](https://www.youtube.com/watch?v=iOLBJwENuvA)（YouTube · GPU MODE，讲者 Zihao Ye）｜全长约 69 分钟，本篇覆盖 25 分钟之后（计算与调度部分）
> 导读：第二篇讲「算」和「怎么分活」：先看 JIT 模板如何用几行说明生成一个专用核函数，再看稀疏访存为什么不能用 TMA，然后是编译期选 tile、运行时按工作量切块调度，最后是实验与路线图。文中保留了作者对「为什么不用 MLIR」「为什么不用原子聚合」这类设计取舍的现场解释。

## 本讲要解决的核心问题（SCQA）

**背景**：第一篇已经把键值缓存统一成块稀疏格式，注意力 kernel 现在只需要面对一种存储布局。

**冲突**：但 kernel 这一侧还有三件麻烦事。第一，注意力变体太多——GQA、MLA、ALiBi、RoPE、滑动窗口、sigmoid 注意力，每加一个就要改一遍 CUDA 实现和 C++/Python 胶水；第二，块稀疏的访存是**非线性 gather**，Hopper 上最快的 TMA 用不了；第三，一个 batch 里长短请求混跑，按请求切活必然拖尾。

**疑问**：能不能让用户只描述「这个变体长什么样」，剩下的交给编译器？稀疏访存拿不到 TMA 的红利，代价有多大？长请求拖尾该怎么切、又怎么保证结果可复现？

**回答（中心思想）**：FlashInfer 把这三件事拆成三层：**JIT 模板**用字符串拼接把用户写的几个变换函数填进 CUDA 模板，生成专用 kernel；**编译期调度**按 prefill/decode/append 的工作负载特征预编译不同 tile 大小的 kernel；**运行时调度**按工作量把键值缓存切成工作块、用优先队列做贪心分配，并刻意避开原子聚合以保证输出确定。[【跳转到 24:46】](https://www.youtube.com/watch?v=iOLBJwENuvA&t=1486)

## 一、JIT 模板：用户写十几行，编译器生成一整个 kernel

### 1.1 变体之多，已经不能靠改代码库解决

作者列了一串现实中的注意力变体：GQA、MLA、各种带自定义 mask 或自定义 score 变换的方案。它们**只改动注意力的一小部分逻辑，却往往要动整个实现**——改 CUDA 实现、改 C++ 与 Python 之间的胶水，费时且很难合回上游，也跟不上主线库的迭代。[【跳转到 25:11】](https://www.youtube.com/watch?v=iOLBJwENuvA&t=1511)

PyTorch 的 FlexAttention 给了很好的启发：把「可定制的部分」抽成几个函数（score 变换、mask 变换），其余交给模板。FlashInfer 沿用了这个思路，并把它和块稀疏存储、编译期调度结合起来。

### 1.2 四个可编程的「函子」

模板把可定制点收敛成四个函数：**QueryTransform、KeyTransform、LogitsTransform、LogitsMask**。用户把它们写成大约十行 CUDA 代码、以 Python 字符串的形式嵌入，再通过一个 `AttentionSpec` 类声明数据类型、额外张量和标量。[【跳转到 28:01】](https://www.youtube.com/watch?v=iOLBJwENuvA&t=1681)

以 sigmoid 注意力为例，它把 softmax 换成 sigmoid：

$$
\mathrm{SigmoidAttn}(X) = \sigma\!\left(QK^\top / \sqrt{d_{qk}}\right) V, \qquad \sigma(u + b) = \left(1 + e^{-(u+b)}\right)^{-1}
$$

要实现它，只需提供 `LogitsTransform`：把 logits 做缩放、加偏置、过一遍 sigmoid，再返回。

![JIT 编译器：用户用 Python 字符串声明注意力变体（Query/Key/Logits 变换与 mask），模板分四部分——核参数结构体、核特征类、核主体、注册为 PyTorch 自定义算子](assets/FlashInfer%20作者亲讲（2）：JIT%20模板、负载均衡调度与可复现性/01913.webp)

同一套机制也覆盖了更常见的变体：ALiBi 是给 logits 加相对位置偏置；RoPE 是在算点积前对 Q、K 各做一次旋转；滑动窗口是给 logits 加一个「位置差小于 $w$」的掩码。**它们都只是 LogitsTransform 或 LogitsMask 的一种写法**。[【跳转到 31:16】](https://www.youtube.com/watch?v=iOLBJwENuvA&t=1876)

![JIT 变体举例：ALiBi、RoPE、滑动窗口注意力都可由 Query/Logits 变换与掩码函数表达](assets/FlashInfer%20作者亲讲（2）：JIT%20模板、负载均衡调度与可复现性/01876.webp)

### 1.3 为什么是 C++ 模板，而不是 MLIR

主持人问了一个很尖锐的问题：PyTorch 2 的 torch.compile 走的是模板路线，JAX 走的是 MLIR 这类编译器基础设施，为什么你们选模板？

作者的回答很坦诚：**因为简单**。用 MLIR 那套，用户改一点东西就要重新编译整个产品；用模板，Python 端 `torch.load` 一下就能加载新生成的 kernel。代价是模板没有类型检查、出错时极难调试——但作者认为这是**开发者的痛点，不是用户的痛点**；对用户来说，能直接看到最终生成的代码反而更好理解。[【跳转到 29:41】](https://www.youtube.com/watch?v=iOLBJwENuvA&t=1781)

他还补了一句关键实现细节：**整个 JIT 就是字符串拼接，没有任何复杂的编译 pass**——「它就是能跑，这算是运气好」。

## 二、稀疏访存：拿不到 TMA 的红利，代价是寄存器

### 2.1 连续存储走 TMA，稀疏存储只能一条条搬

模板里最脏的一段是「全局内存到共享内存」的搬运。对**连续存储**，可以按 tile 发 TMA 指令；对**稀疏存储**，只能发多条 `LDGSTS`（Ampere 风格的异步拷贝），**一行一条**，地址要经过 `indices` 数组查表得到。[【跳转到 32:37】](https://www.youtube.com/watch?v=iOLBJwENuvA&t=1957)

![稀疏与稠密的全局到共享内存搬运对比：稠密按 tile 发 TMA，稀疏要按行查索引发 LDGSTS](assets/FlashInfer%20作者亲讲（2）：JIT%20模板、负载均衡调度与可复现性/02082.webp)

为什么不能用 TMA？因为 **TMA 2D 只适用于连续张量**，而这里的全局地址到共享内存地址的映射是**非线性的**，必须经过一次间接索引。作者说实测性能损失不算大，代价主要在**寄存器**：做指针算术要占用更多寄存器，于是生产者/消费者之间的寄存器预算要重新调，否则会寄存器溢出（spill），性能会掉得很厉害；连带的后果是 K 维的 tile 大小也得缩小。[【跳转到 34:17】](https://www.youtube.com/watch?v=iOLBJwENuvA&t=2057)

## 三、编译期调度：不同阶段的「算子强度」不一样

### 3.1 四种工作负载，四种形状

推理不是一个形状固定的任务。作者把它拆成四种：[【跳转到 35:07】](https://www.youtube.com/watch?v=iOLBJwENuvA&t=2107)

- **Prefill（预填充）**：一次处理整段输入，$\mathrm{len}(Q) = \mathrm{len}(KV)$，掩码是三角形；
- **Decode（解码）**：每次生成一个 token，$\mathrm{len}(Q) = 1$，相当于在三角形里新填一行；
- **Append（增量预填充）**：一次追加几个 token，比如推测解码草稿模型给出 5 到 10 个候选，$\mathrm{len}(Q)$ 是 5 或 10；
- **Chunked prefill（分块预填充）**：一次只喂新加的 1000 个 token，$\mathrm{len}(Q) < \mathrm{len}(KV)$，掩码是三角形加一条梯形。

![推理服务中的工作负载异构：decode 的 Q 长度为 1、append 为多个 token、prefill 的 Q 长度等于 KV 长度](assets/FlashInfer%20作者亲讲（2）：JIT%20模板、负载均衡调度与可复现性/02157.webp)

这四种形状的**算子强度（operational intensity）差别很大**，所以不能用同一个 kernel 配置打天下。

### 3.2 按形状选 tile，并把候选全部预编译

具体做法是提供一组查询 tile 大小（16、32、64、128）的 kernel 变体，根据输入特征（比如平均查询长度）挑最合适的一个；这些变体**全部预编译**，运行时只做选择。[【跳转到 37:12】](https://www.youtube.com/watch?v=iOLBJwENuvA&t=2232)

举个具体判断：纯解码 + 多头注意力（MHA）时，算子强度只有 1，这时更偏好用 CUDA core 实现，tile 可以开得很大；而在 append、prefill 或者带 GQA 的解码里，**GQA 让多个查询头共享同一组键值头，算子强度被抬高**，就该走 tensor core 路径。对 Hopper（FA3），管线设计还要额外做线程束专用化（warp specialization）。

## 四、运行时调度：按工作量切，且必须确定

### 4.1 算法：切块、排序、优先队列

编译期决定「用哪个 kernel」，运行时决定「这个 kernel 怎么分活」。算法和论文一致：[【跳转到 38:27】](https://www.youtube.com/watch?v=iOLBJwENuvA&t=2307)

1. 把每个请求的注意力计算按查询 tile 切开；
2. 用总工作量除以 CTA 数量，得到**每个 CTA 平均要处理的键值长度**，作为单个工作块的最大长度；
3. 把所有工作块**按长度从大到小排序**；
4. 维护每个 CTA 的累计代价，每轮把**最长的工作块分给累计代价最小的 CTA**；
5. 循环到所有工作块分配完，此时各 CTA 的总代价几乎相等。

作者把目标说得很直白：一是**负载均衡**（太长的序列必须切开），二是**消除波量化（zero wave quantization）**——不要让一部分 SM 空转、另一部分 SM 排队。分配结果（工作块到 CTA 的映射）会被缓存下来。

![运行时调度器：按工作量把工作块分给各 CTA，注意力核先产出部分输出（O 与 LSE），再由收缩核归约成最终输出](assets/FlashInfer%20作者亲讲（2）：JIT%20模板、负载均衡调度与可复现性/02357.webp)

### 4.2 两阶段 persistent kernel 与「不用原子加」

切开的键值缓存意味着一个请求会产生多份部分输出。所以 FlashInfer 提供两个 kernel：**第一阶段**算每个工作块的输出，写进临时缓冲区（partial output）；**第二阶段**用收缩核（contraction kernel）把同一请求的所有部分输出合并。两个 kernel 都写成 **persistent kernel** 形式，配置一致。[【跳转到 40:32】](https://www.youtube.com/watch?v=iOLBJwENuvA&t=2432)

这套设计受 Stream-K 启发，但**刻意没有采用 Stream-K 的原子聚合**。原因不是性能而是正确性：原子加法的浮点累加顺序不确定，输出就不可复现；而作者在和多家推理框架交流后发现，**它们要求 kernel 输出确定**。[【跳转到 41:22】](https://www.youtube.com/watch?v=iOLBJwENuvA&t=2482)

### 4.3 现场提问：怎么保证所有 SM 都在干活

有人问：CTA 到 SM 的映射由硬件调度器决定、并不公开，你怎么保证所有 SM 都被占满？

作者的回答是：先调用 occupancy API 拿到**每个 SM 最多能放几个 CTA**，然后用「每个 SM 的最大 CTA 数 × SM 总数」作为启动的 CTA 数。对 H100 而言，kernel 本身已经吃掉了大部分寄存器和共享内存，**一个 SM 通常只能放一个 CTA**，所以数量就是 SM 数。[【跳转到 43:27】](https://www.youtube.com/watch?v=iOLBJwENuvA&t=2607)

### 4.4 与推理框架的接口：init / plan / run

对上层框架，FlashInfer 暴露三个阶段：[【跳转到 44:58】](https://www.youtube.com/watch?v=iOLBJwENuvA&t=2698)

- **Init**：按配置创建 `AttentionWrapper`，把任务信息传进去；如果需要新的注意力变体，就在这里做 JIT 编译；
- **Plan**：每个生成步开始时执行一次，跑负载均衡调度，输出确定的调度结果；
- **Run**：按 plan 的结果执行 kernel。

![计算抽象：init 阶段 JIT 编译、plan 阶段做动态调度、run 阶段执行；plan 在图外、run 被 CUDA Graph 捕获](assets/FlashInfer%20作者亲讲（2）：JIT%20模板、负载均衡调度与可复现性/02748.webp)

三个工程细节值得记住：

1. **plan 的开销可以摊薄**：多数推理引擎的各层可以复用同一套键值缓存布局，所以**一次 plan 可以给上百层复用**；
2. **double buffering**：执行当前步的同时预计算下一步的 plan，进一步隐藏开销；
3. **CUDA Graph 兼容**：plan 在 CPU 上、不进图；run 在 GPU 上、被图捕获。重放时先 plan，再重放整个「逐层计算」的图（不只是注意力算子，还有 LayerNorm 等）。

## 五、结果：每一层设计各自的收益

### 5.1 稀疏存储的代价：10% 以内

![向量稀疏（page_size=1）与稠密注意力的对比：FA2 模板下差距在 10% 以内，FA3 模板差距略大但仍超过 500 TFLOPs](assets/FlashInfer%20作者亲讲（2）：JIT%20模板、负载均衡调度与可复现性/02923.webp)

在分页注意力工作负载上，把页大小设为 1（即最细粒度的向量稀疏）与稠密键值缓存相比：FA2 模板下差距在 10% 以内；FA3 模板差距更大一些，原因是 FA3 通常用 TMA 搬键值缓存，而稀疏场景只能退回 `LDGSTS`，指针算术带来寄存器压力。即便如此，**向量稀疏仍能跑到 500 TFLOPs 以上**。[【跳转到 49:08】](https://www.youtube.com/watch?v=iOLBJwENuvA&t=2948)

### 5.2 变长负载：调度器的主场

![变长 Split-K 的负载均衡效果：恒定长度分布下与基线相当，均匀与偏斜分布下带宽/算力利用率明显更高](assets/FlashInfer%20作者亲讲（2）：JIT%20模板、负载均衡调度与可复现性/03148.webp)

对比三种序列长度分布：**恒定**（所有请求键值长度一样）、**均匀**（5 到 2048 之间随机）、**偏斜**（Zipf 分布）。恒定分布下 FlashInfer 与基线差不多——因为没有可均衡的差异；均匀和偏斜分布下明显更好，**这正是调度器起作用的地方**。[【跳转到 51:13】](https://www.youtube.com/watch?v=iOLBJwENuvA&t=3073)

主持人追问「Zipf 真的能代表真实负载吗」，作者的回答很克制：真实分布不完全符合其中任何一种，这里只是**模拟**；很多公司有真实统计但不便公开。

### 5.3 端到端：最多 2 倍

![端到端结果：SGLang 搭配 FlashInfer 与搭配 Triton 后端相比，在 8B/70B、ShareGPT/变长负载上最多降低 2 倍延迟](assets/FlashInfer%20作者亲讲（2）：JIT%20模板、负载均衡调度与可复现性/03254.webp)

在 SGLang 上对比 Triton 后端与 FlashInfer 后端，模型是 Llama 3.1 8B（单卡 H100）和 70B（四卡 H100），负载是 ShareGPT 与变长分布，**最多可降低 2 倍延迟**。作者归因于两点：用上了最新的库特性（如线程束专用化），以及专门设计的稀疏访存加载模块（把稀疏行从全局内存 gather 到共享内存）——后者是 Triton 当时缺失的。[【跳转到 53:18】](https://www.youtube.com/watch?v=iOLBJwENuvA&t=3198)

### 5.4 定制注意力的价值：融合 RoPE

![定制注意力结果：Streaming-LLM 中融合 RoPE 的注意力核，kernel 级 2 倍加速、端到端延迟降低约 30%](assets/FlashInfer%20作者亲讲（2）：JIT%20模板、负载均衡调度与可复现性/03304.webp)

流式推理（Streaming-LLM）里无法预先对键做 RoPE 再存进缓存，所以必须有一个**融合 RoPE 的注意力 kernel**。用定制模板实现后，kernel 级约 2 倍加速，端到端 token 间延迟降低约 30%。[【跳转到 54:14】](https://www.youtube.com/watch?v=iOLBJwENuvA&t=3254)

### 5.5 可组合格式在并行生成上的收益

在 ShareGPT 上使用 OpenAI API 的 `n` 参数（一次并行生成 n 个回答）时，这些回答共享同一段前缀，正好是可组合格式的用武之地：中等规模（n 在 4 到 32 之间）时 token 间延迟约提升 50%，首 token 延迟最多提升 20%；n 更大后收益消失，因为这时注意力已经不是主导因素。[【跳转到 55:04】](https://www.youtube.com/watch?v=iOLBJwENuvA&t=3304)

## 六、路线图：可复现性是个真问题

演讲最后提到三个方向，其中「完全可复现」最值得初学者注意。

![路线图：不同 Split-K/Stream-K 策略会改变 kernel 输出，而某些任务（如基于 LLM 的压缩）要求完全可复现](assets/FlashInfer%20作者亲讲（2）：JIT%20模板、负载均衡调度与可复现性/03854.webp)

问题是这样产生的：**一个请求单独跑时可能被切成多块（split-K），和别人一起组成 batch 跑时可能不切**，两条路径的浮点累加顺序不同，输出就会有微小差异。多数场景无所谓，但有些场景不能容忍——比如用 LLM 做数据压缩时，压缩端和解压端必须得到完全一致的 logits 排序，否则整个算法失效。[【跳转到 62:09】](https://www.youtube.com/watch?v=iOLBJwENuvA&t=3729)

目标因此写得很具体：**prefill 与 decode 之间可复现、跨机器可复现、不同 batching 策略之间可复现**。代价是可能要牺牲一部分性能（比如对某些工作负载禁用 split-K）。社区已经提出了对应的 RFC。

另外两个方向是：为 NanoFlow 这类「按 SM 子集执行」的范式提供支持（把计算、访存、通信算子分配到不同 SM 上重叠执行），以及和 FlexAttention 对齐、提供 CUDA 后端。

![社区与采用情况：FlashInfer 已被 MLC-LLM、vLLM、SGLang、Hugging Face TGI、NanoFlow 等引擎采用](assets/FlashInfer%20作者亲讲（2）：JIT%20模板、负载均衡调度与可复现性/03454.webp)

## 小结

- **JIT 模板 = 模板 + 说明**：用户只写 Query/Key/Logits 变换与 mask 四个函子（约十行 CUDA），模板负责生成 kernel 并注册成 PyTorch 算子；实现上就是字符串拼接，好处是简单、用户可读，代价是缺少类型检查。
- **稀疏访存取不到 TMA**：非线性 gather 只能用逐行的 `LDGSTS`，代价是寄存器压力，进而限制 tile 大小；向量稀疏相对稠密的性能差距约 10%。
- **编译期调度按形状选 tile**：prefill、decode、append、chunked prefill 的算子强度不同，是否用 tensor core、tile 开多大都要跟着变，候选 kernel 全部预编译。
- **运行时调度按工作量切块**：最大块长 = 总工作量 / CTA 数，最长块优先分给最空闲的 CTA，目标是负载均衡与零波量化。
- **确定性优先于极致性能**：不用原子聚合，保证同样的输入得到同样的输出；plan 在 CPU、run 在 GPU，兼顾自适应与 CUDA Graph。
- **可复现性是新战场**：split-K 带来的累加顺序差异在 LLM 压缩这类任务里是致命的，社区已提出 RFC 并接受一定的性能损失。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| 注意力变体（Attention Variant） | 在标准注意力上改一点逻辑的版本，如 GQA、ALiBi、滑动窗口、sigmoid 注意力 |
| 函子（Functor） | 传给模板的可替换函数，如 QueryTransform、LogitsTransform、LogitsMask |
| JIT 编译 | 运行时按具体配置即时生成并编译 kernel，而不是事先全量编译 |
| ALiBi | 用相对位置偏置直接加在注意力 logits 上的位置编码方案 |
| RoPE | 旋转位置编码，通过对 Q/K 做旋转把位置信息编码进点积 |
| TMA | Hopper 的张量内存加速器，异步批量搬运连续张量；不支持非线性 gather |
| LDGSTS | Ampere 引入的异步拷贝指令，全局内存到共享内存，一条管一行 |
| 算子强度（Operational Intensity） | 每字节访存对应的浮点运算量，决定走算力路径还是带宽路径 |
| 波量化（Wave Quantization） | 任务数不是 SM 数整数倍时，最后一波只有部分 SM 有活干造成的浪费 |
| Split-K | 把键值序列维切开分给多个 CTA 并行算，再归约 |
| 收缩核（Contraction Kernel） | 把多个部分输出（O 与 LSE）按组合律合并成最终输出的 kernel |
| Persistent Kernel | 一次启动、常驻 GPU，循环领取任务而不是每个任务启动一次 |
| CUDA Graph | 把一串 kernel 启动录制成图后重放，降低启动开销 |
| 确定性 / 可复现性 | 相同输入在任意切分、任意 batch 组合下都得到逐位相同的输出 |