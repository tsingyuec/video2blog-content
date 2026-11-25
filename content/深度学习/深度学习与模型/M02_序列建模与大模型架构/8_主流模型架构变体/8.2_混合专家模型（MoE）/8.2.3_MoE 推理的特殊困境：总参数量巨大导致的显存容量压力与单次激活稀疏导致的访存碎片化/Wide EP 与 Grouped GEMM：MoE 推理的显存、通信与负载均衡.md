# Wide EP 与 Grouped GEMM：MoE 推理的显存、通信与负载均衡

> 视频来源：[MoE 模型推理软硬件协同优化实践：多 GPU 专家并行 EP](https://www.bilibili.com/video/BV1dgBDBwEmY/)（Bilibili · UP 主「荒野芯智观察」）｜时长约 26 分钟
> 导读：这支视频把 MoE 推理的三件事串成一条线——为什么单卡装不下（显存容量）、为什么收到 token 不能直接算（Grouped GEMM 与访存碎片）、为什么把专家摊到 72 张卡上反而更快（NVLink 72 + 负载均衡 + 软硬协同）。本文按他的讲解顺序整理，并把那张「232 个专家」的部署图拆开算了一遍。字幕中的口误（`MOVE`、`EEP`、`Y 的 1P`、`DBCR1`、`GPA3` 等）已订正为 MoE、EP、Wide EP、DeepSeek-R1、GPT-3。

## 本讲要解决的核心问题（SCQA）

**背景**：MoE 相对稠密模型的优势很清楚——每个 token 只激活很少一部分参数，算得省。但劣势同样清楚：**总参数量太大，一张 GPU 装不下全部专家**，所以必须多卡并行，这种并行叫专家并行（EP）。

**冲突**：EP 一宽，问题就来了。第一，每张卡收到的 token 是按来源排的、指向不同专家，**不能直接喂给矩阵乘法单元**；第二，GPU 越多，卡间通信的对象越多——8 卡时每张卡最多和 3 张卡说话，72 卡时要和 71 张卡说话。通信成本会不会把显存优化的收益全部吃掉？

**疑问**：大规模 EP 到底怎么部署？收到的一堆散 token 怎么算？通信和负载不均怎么处理？

**回答（中心思想）**：三件事缺一不可。**Grouped GEMM** 把路由到同一专家的 token 聚成一个矩阵，让 GPU 的矩阵单元跑满（不聚成矩阵会慢五倍以上）；**Wide EP** 把专家摊到更多卡上，每卡专家变少、显存腾出来给并发；**NVLink 72 + EPLB + TensorRT-LLM** 用更高的卡间带宽、动态负载均衡和通信优化把这笔账扳回来——实测 EP32 比 EP8 每卡输出吞吐高 **1.8 倍**。[【跳转到 21:24】](https://www.bilibili.com/video/BV1dgBDBwEmY/?t=1284)

---

## 一、MoE 的显存困境，与 EP 的两种规模

### 1.1 优势在算力，劣势在显存

UP 主一上来就把账分清：MoE 的优势是「能够激活更少的参数量，进行一个更高效的激活方式」；劣势是「对显存的要求太高了，因为参数量太大了」。[【跳转到 00:25】](https://www.bilibili.com/video/BV1dgBDBwEmY/?t=25)

这个判断值得展开一句：MoE 的稀疏是**逐 token 动态**的，路由在运行时才知道结果，所以你不能提前把「这个请求用不到」的专家权重从显存里挪走。**所有专家的权重都必须常驻**，稀疏省下的是 FLOPs，不是显存。这就是 MoE 推理第一个结构性困境。

### 1.2 Small EP 与 Large EP：同一个 MoE 层的两种切法

EP 的定义很直白：把 MoE 模型里的专家分散到多个 GPU 上，利用各设备的综合算力和内存带宽；在小规模下，EP 通过在设备间均衡分配任务，缓解内存压力并维持较高的算力利用率。[【跳转到 02:04】](https://www.bilibili.com/video/BV1dgBDBwEmY/?t=124)

![Small Scale EP 与 Large Scale EP：前者每卡放很多专家，后者每卡只放很少专家、但集群更大](assets/Wide%20EP%20与%20Grouped%20GEMM：MoE%20推理的显存、通信与负载均衡/00124.webp)

两种规模的区别就是一句话：

- **Small EP**：GPU 少，每层 N 个专家，那每张卡就要负责更多专家；
- **Large EP（Wide EP）**：GPU 多，每张卡只负责更少的专家，实现 MoE 层的高效扩展。[【跳转到 02:19】](https://www.bilibili.com/video/BV1dgBDBwEmY/?t=139)

好处有两层。第一层是显存：如果一张卡里装那么多专家，「显存有可能就爆掉了，就不够用了」。第二层更关键——**每张卡上的东西少了，剩下的显存就可以用来做多 batch 推理，应对更多并发**。[【跳转到 02:44】](https://www.bilibili.com/video/BV1dgBDBwEmY/?t=164)

### 1.3 代价：通信对象从 3 个变成 71 个

UP 主没有回避代价：「在小型 EP 的情况下，每个 GPU 只需要和最多其他三个 GPU 进行通信；但 Wide EP 这种情况，你这个 GPU 要和其他的 N 个 GPU 进行通信。」如果 N 等于 72，那其中一张卡就要和另外 71 张卡通信。[【跳转到 03:09】](https://www.bilibili.com/video/BV1dgBDBwEmY/?t=189)

于是他抛出了全片的中心问题：**「这样通信成本是否真的能够抵消掉这种方式带来的显存优化的成本呢？」** 后面所有内容——Grouped GEMM、NVLink 72、EPLB、Dynamo、TensorRT-LLM——都是在回答这一问。

---

## 二、Grouped GEMM：为什么收到 token 不能直接算

### 2.1 一堆散 token 指向不同专家

这是 MoE 推理里最容易被忽略、也最影响性能的一步。UP 主设了一个场景：一张 GPU 上部署了很多专家，每个专家都会收到不同的、选择它的 token。[【跳转到 04:19】](https://www.bilibili.com/video/BV1dgBDBwEmY/?t=259)

假设路由结果是：X1、X2 选中了这张卡上的专家一，X3、X4 选中了专家二，X5 选中了专家三。**同一个 GPU 并不代表同一个专家**——这一点是理解后面所有内容的前提。[【跳转到 05:21】](https://www.bilibili.com/video/BV1dgBDBwEmY/?t=321)

### 2.2 归类成矩阵

「如果这些东西单独进来，我们不可能给它单独处理。」所以要把它们**归类**：X1 归到专家一，X2 归到专家二，X3 归到专家三，直到每一组都拼成一个矩阵。[【跳转到 05:46】](https://www.bilibili.com/video/BV1dgBDBwEmY/?t=346)

![Grouped GEMM：路由到同一专家的 token 被打包成一个大矩阵，一张 GPU 上所有专家在一次融合的 Grouped GEMM kernel 里跑完，权重只加载一次](assets/Wide%20EP%20与%20Grouped%20GEMM：MoE%20推理的显存、通信与负载均衡/00365.webp)

### 2.3 为什么非要矩阵：GPU 只为矩阵做过优化

UP 主的解释很硬核：从 V100 之后，所有 AI 芯片都是为矩阵运算做过专门优化的——英伟达的 Tensor Core、AMD 的 Matrix Core，都是专门用来算矩阵乘法的。「同一个东西，它是矩阵比它不是矩阵，速度要快五倍以上。」[【跳转到 06:30】](https://www.bilibili.com/video/BV1dgBDBwEmY/?t=390)

这句话解释了为什么 GPU 的算力参数（TFLOPS）都是按矩阵乘标定的：**你按非矩阵的方式喂它，速度会慢很多**。所以「把 token 按专家聚成矩阵」不是工程上的洁癖，而是能不能用上硬件算力的分水岭。

### 2.4 权重只加载一次，跨 token 复用

归类成矩阵之后，还有一个附带的大好处。UP 主念了一段原文：`All experts on this GPU are executed in one fused Grouped GEMM kernel. Expert weights are loaded once into shared memory, reused across many tokens.` 他的翻译是：「我们 GPU 只需要加载一次模型权重，就可以复用了。」[【跳转到 07:20】](https://www.bilibili.com/video/BV1dgBDBwEmY/?t=440)

这正是 MoE 推理「访存碎片化」的解药：如果每个 token 单独触发一次专家调用，那 18 兆的专家权重就要被读很多遍；聚成一个矩阵之后，**一次读取服务很多 token**，每字节权重能支撑的 FLOPs 就上去了。

### 2.5 Wide EP 如何缓解 Grouped GEMM 的瓶颈

UP 主的总结是：大规模 EP 在专家并行配置中引入更多 GPU，每个 GPU 分到的专家更少，负载压力就减少；同时 Grouped GEMM 的内核能够更高效地复用权重，**运算强度更高**（每个字节的加载权重可以支持更多 FLOPs），在内核层面实现更优的计算与内存平衡。[【跳转到 07:41】](https://www.bilibili.com/video/BV1dgBDBwEmY/?t=461)

但 EP 也不是万灵药：对超大规模的 MoE 模型，光靠 EP 也有困难，所以要用 Wide EP，从算法层面识别计算与内存瓶颈，并与硬件结合。[【跳转到 08:24】](https://www.bilibili.com/video/BV1dgBDBwEmY/?t=504)

---

## 三、把 256 个专家铺到 64 张卡：232 这个数字怎么来的

这是全片信息密度最高的一段，UP 主说这张图「非常非常重要」，因为它解释了传统 MoE（包括 GPT-3 那一代）到底怎么部署到多张 GPU 上。[【跳转到 09:34】](https://www.bilibili.com/video/BV1dgBDBwEmY/?t=574)

### 3.1 先数清模型结构

以 DeepSeek-R1 为例：256 个专家、6710 亿参数，其中 **58 个 MoE 层**，每层 256 个专家。dense 层（密集层）先不管。[【跳转到 09:58】](https://www.bilibili.com/video/BV1dgBDBwEmY/?t=598)

### 3.2 横向切分：每层每卡 4 个

部署用 64 张 GPU 并行。每层 256 个专家分给 64 张卡：

$$
\frac{256}{64} = 4 \quad \text{（每张卡每层 4 个专家）}
$$

再乘层数：

$$
58 \times 4 = 232 \quad \text{（每张卡共负责 232 个专家）}
$$

这就是图里那个「232 Experts per GPU」的来历。[【跳转到 10:53】](https://www.bilibili.com/video/BV1dgBDBwEmY/?t=653)

![GB200 NVL72 中的部署方案：每层仅 4 个专家被激活，每张 GPU 负责 232 个专家（58 层 × 每层 4 个），72 张 GPU 组成一个 NVLink 域](assets/Wide%20EP%20与%20Grouped%20GEMM：MoE%20推理的显存、通信与负载均衡/00558.webp)

UP 主还补充了分配的具体规则：第 1 层的 4 个专家放在这张卡上，第 2 层的 4 个也放这张卡上……一直放到第 58 层，凑够 232 个；第 N 张卡则从第 256 个专家往后接着分。[【跳转到 11:43】](https://www.bilibili.com/video/BV1dgBDBwEmY/?t=703)

注意这里的算术揭示了一个残酷事实：**每层只激活 4 个专家，但每张卡要养 232 个**。也就是说，一张卡上 232 个专家权重里，绝大多数在这一层是「待命」状态——它们必须驻留显存，但这一轮不参与计算。这就是「总参数量巨大导致的显存容量压力」与「单次激活稀疏」在同一张图上的样子。

### 3.3 72 张 GPU 组成一个 NVLink 域

接下来是硬件部分。GB200 的一个托盘、又一个托盘，通过 NVSwitch 把这些 GPU 全部连接起来。UP 主强调的突破点是：**「我们不是说八个 GPU 一组，而是 72 个 GPU 一组。」** 这样 NVLink 的带宽就比走交换机高很多，通信问题能优化得更好。[【跳转到 12:08】](https://www.bilibili.com/video/BV1dgBDBwEmY/?t=728)

---

## 四、NVLink 72：把通信留在机柜里

### 4.1 1.8T/s 对 900GB/s，差两倍

UP 主给了一组对比：在 NVLink 72 里面，NVLink 第五代的速度达到 **1.8T 每秒**；而哪怕用最先进的交换机（比如英伟达的 Spectrum-X），也只能做到 **900GB 每秒**。差了两倍。[【跳转到 12:58】](https://www.bilibili.com/video/BV1dgBDBwEmY/?t=778)

所以工程上的取向很明确：**尽量把通信留在 NVLink 域内**。因为 MoE 每一层都要做 token 的分发与回收，「转完了第一层，接下来要进第二层了，然后就要到其他的 GPU 去找别的专家」，这是一个每层都会发生的、绕不开的通信。[【跳转到 13:23】](https://www.bilibili.com/video/BV1dgBDBwEmY/?t=803)

### 4.2 聚合带宽 130T/s

单个 GPU 对的带宽是 1.8T/s，但域里有 72 张卡，UP 主提醒要乘一下：

$$
1.8\text{T/s} \times 72 \approx 130\text{T/s}
$$

这是**聚合带宽**，不是两个 GPU 之间——两个 GPU 之间还是 1.8T/s。[【跳转到 15:04】](https://www.bilibili.com/video/BV1dgBDBwEmY/?t=904)

### 4.3 但 gather 会吃掉收益

UP 主没有把话说满：「尽管大规模 EP 能够降低专家负载的开销，但有可能会被 token gather 集群带来的通信开销所抵消。」[【跳转到 13:53】](https://www.bilibili.com/video/BV1dgBDBwEmY/?t=833)

原因在于 combine 之后还得整理：集群需要整合来自分布式专家的输出，对 token 重新排序，然后才能传给下一个 Transformer 块或最终的 softmax 层。[【跳转到 14:13】](https://www.bilibili.com/video/BV1dgBDBwEmY/?t=853)

「如果没有这个带宽的话，如此复杂的通信方式还将会使得我们的大规模 EP 难以应用。」[【跳转到 14:49】](https://www.bilibili.com/video/BV1dgBDBwEmY/?t=889) 这句话把逻辑闭环了：**Wide EP 的可行性，本质上是被卡间带宽撑起来的**。

---

## 五、负载均衡：热门专家与冷门专家

### 5.1 短板效应

UP 主说负载均衡「一直都是 MoE 模型碰到的最大问题」。原因很自然：某些专家负责的是常规知识、语义理解这类内容，很多 token 都会涉及，于是它「突然就比较受欢迎」。如果这个热门专家所在的 GPU 很忙，而另一张卡很冷淡，最终是**短板效应**——「你最终的耗时取决于你这个忙的 GPU」，冷淡的卡「没什么事做，只能干等着」。[【跳转到 15:33】](https://www.bilibili.com/video/BV1dgBDBwEmY/?t=933)

### 5.2 EPLB：把专家在容器之间搬一搬

英伟达的做法叫**专家并行负载均衡器（EPLB）**：采用一种策略，将热门专家与冷门专家重新分配；该过程会触发权重更新，通过容器化架构实现专家在容器间的动态分配，确保在不破坏 CUDA 图执行的前提下完成专家迁移；这些权重更新被安排在前向传播之间、以非阻塞方式进行。[【跳转到 16:23】](https://www.bilibili.com/video/BV1dgBDBwEmY/?t=983)

![EPLB 的工作方式：把 GPU2 上过热的专家容器 C 与 GPU3 上偏冷的容器 E 对调，让三张卡的负载接近](assets/Wide%20EP%20与%20Grouped%20GEMM：MoE%20推理的显存、通信与负载均衡/00933.webp)

UP 主用一句大白话翻译了这套机制：一开始 GPU2 非常忙、GPU3 非常闲，于是把两个专家的**权重参数对调**——「名字还叫 expert C、还叫 container C，名字没变，结果权重变了」。这样路由在做选择时，就会更多地选中现在放在 GPU3 上的那个专家，负载自然就均衡了。[【跳转到 17:41】](https://www.bilibili.com/video/BV1dgBDBwEmY/?t=1061)

### 5.3 静态与动态两种方式

- **静态、基于历史数据**：历史数据告诉你「大概率 GPU2 会火爆、GPU3 不火爆」，那就优先把更多 token 分配给 GPU3；
- **在线动态**：实时看到 GPU2 很忙，就给 GPU3 更多点活。[【跳转到 18:25】](https://www.bilibili.com/video/BV1dgBDBwEmY/?t=1105)

---

## 六、Dynamo 与 TensorRT-LLM：指挥者与执行者

专家打散之后，还需要软件配合才能跑快。UP 主用一张表对比了两个组件，并把它们的关系概括成「指挥官」和「执行引擎」。[【跳转到 19:04】](https://www.bilibili.com/video/BV1dgBDBwEmY/?t=1144)

![TensorRT-LLM 与 NVIDIA Dynamo 的分工：前者是支持专家并行解码的执行引擎，后者是分解推理的编排层](assets/Wide%20EP%20与%20Grouped%20GEMM：MoE%20推理的显存、通信与负载均衡/01144.webp)

- **NVIDIA Dynamo**：一个**编排层**，负责宏观调度，决定让谁算、怎么算。它能做 SLA 感知——监控任务是否超时、延迟高不高；请求太多就自动扩容。UP 主的比喻是「包工头」「交通指挥」：看着整个 Kubernetes 集群，确保只有在需要的时候才把 GPU 开起来。[【跳转到 19:25】](https://www.bilibili.com/video/BV1dgBDBwEmY/?t=1165)
- **TensorRT-LLM**：一个**执行层**，直接跑在 GPU 上，处理矩阵乘法，负责 Wide EP 这类 64 卡、72 卡的场景。它的本事是「懂得如何榨干 NVLink 72 的高带宽」，把 GPU 之间的通信开销做到最低。UP 主的比喻是「流水线上的熟练工」。[【跳转到 20:14】](https://www.bilibili.com/video/BV1dgBDBwEmY/?t=1214)

---

## 七、结果：EP32 比 EP8 快 1.8 倍

### 7.1 反直觉的实测

UP 主用一张图回答了开头那个问题：小切分好还是大切分好？直觉上，8 张卡通信消耗少、但每卡显存占用大；32 张卡每卡显存占用少、但通信消耗大。实测结果是：**32 卡的大规模 EP 比 8 卡的小规模 EP，推理速度提高 1.8 倍**。[【跳转到 21:19】](https://www.bilibili.com/video/BV1dgBDBwEmY/?t=1279)

![Large Scale EP 推理性能（DeepSeek-R1）：EP=8 与 EP=32 对比，每卡每秒输出 token 提升 1.8 倍](assets/Wide%20EP%20与%20Grouped%20GEMM：MoE%20推理的显存、通信与负载均衡/01284.webp)

### 7.2 原因：EP8 时显存带宽是瓶颈

为什么会出现这种「反直觉」的结果？UP 主的解释直接落在带宽上：DeepSeek-R1 总参数量 671B、激活 37B。**在 EP 等于 8 的时候，每个 GPU 要加载和读取海量的专家数据，显存带宽就成了最大瓶颈**——如果每张卡要放十个专家，那这十个专家的权重全部要读进来，带宽必然成瓶颈。[【跳转到 22:11】](https://www.bilibili.com/video/BV1dgBDBwEmY/?t=1331)

而 EP 等于 32 时，虽然卡间的通信需求变多了，但可以通过 TensorRT-LLM 这类软件去优化不同专家的通信，「这个通信时间其实并没有大家想象的这么多」。[【跳转到 22:54】](https://www.bilibili.com/video/BV1dgBDBwEmY/?t=1374)

这正好把 MoE 推理的瓶颈说清了：**它不是 FLOPs 瓶颈，而是显存带宽瓶颈 + 通信瓶颈**。EP8 输在带宽（每卡要读太多专家权重），EP32 靠更少的每卡专家把字节数压下来，再用高带宽的 NVLink 把多出来的通信吃掉。

### 7.3 还叠加了 MTP

UP 主最后提到，这个结果还结合了多 token 预测（MTP）——一次生成多个 token，而不是传统的一次一个。[【跳转到 23:24】](https://www.bilibili.com/video/BV1dgBDBwEmY/?t=1404)

这也符合前文的逻辑：既然解码一步的时间主要花在读权重上，多塞几个 token 进来几乎不额外花钱，那 MTP 就是「白赚」的。反过来说，**如果 EP 变宽没有带来收益，那 NVLink 72 这种机柜就没有存在价值了**。[【跳转到 23:49】](https://www.bilibili.com/video/BV1dgBDBwEmY/?t=1429)

---

## 八、把那张部署图再读一遍

UP 主在结尾把最重要的东西又指了一次：那张图。它的意思是——

1. **按层部署**：每一层在每张 GPU 上放 4 个专家（或更多）；第 1 张卡放第 1 层的 1–4、第 2 层的 1–4……一直放到 232 个；第 2 张卡从第 1 层的 5–8 开始；直到 256 个专家全部铺完。[【跳转到 24:09】](https://www.bilibili.com/video/BV1dgBDBwEmY/?t=1449)
2. **尽量减少卡间开销**：路由到某张卡之后位置是固定的，但最终还是要合并，合并就有通信开销。
3. **软硬协同**：通信开销要靠硬件（NVLink）和软件（TensorRT-LLM）一起去压，最终才拿到 32 卡比 8 卡高 1.8 倍的结果。[【跳转到 25:04】](https://www.bilibili.com/video/BV1dgBDBwEmY/?t=1504)

---

## 小结

- MoE 的优势在算力（稀疏激活），劣势在显存（总参数必须全驻留）。单卡装不下，就必须 EP。
- **Small EP** 每卡放很多专家、通信对象少；**Wide EP** 每卡放很少专家、显存腾出来给并发，但每张卡要和几十张卡通信。
- 收到 token 不能直接算：必须先按专家**归类成矩阵**（Grouped GEMM），因为 GPU 只为矩阵做过优化，非矩阵会慢五倍以上；聚成矩阵后权重只加载一次、跨 token 复用。
- 部署算术：58 个 MoE 层 × 每层每卡 4 个专家 = 每卡 232 个专家；每层只激活 4 个，其余全部待命占显存。
- NVLink 72 把 72 张卡放进一个域，单对 1.8T/s、聚合约 130T/s，是 Wide EP 可行的物理前提；但 combine 之后的 gather 与重排序会吃掉一部分收益。
- 负载不均是短板效应：最忙的那张卡决定整层耗时。EPLB 通过容器间搬专家（换权重、不换名字）来均衡，分静态（历史）与动态（在线）两种。
- Dynamo 是编排层（指挥者），TensorRT-LLM 是执行层（熟练工），一个决定让谁算，一个把通信压到最低。
- 最终结果：EP32 比 EP8 每卡输出吞吐高 1.8 倍，因为 EP8 的瓶颈是显存带宽，而 EP32 的额外通信被软件与 NVLink 消化掉了。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| EP（专家并行） | 把 MoE 的不同专家放到不同 GPU 上，每卡只保存一部分专家 |
| Small EP / Wide EP | 前者卡少、每卡专家多；后者卡多、每卡专家少 |
| Grouped GEMM | 把路由到同一专家的 token 聚成矩阵，再一次内核跑完所有专家，权重只加载一次 |
| 计算强度 | 每读一个字节能支撑多少次 FLOPs；聚成矩阵后它会上升 |
| NVLink 72 域 | 72 张 GPU 通过 NVSwitch 连成一个高带宽域，单对 1.8T/s |
| EPLB | 专家并行负载均衡器：把热门与冷门专家在容器间对调，缓解短板效应 |
| Dynamo | 推理编排层，负责 SLA 感知、扩缩容与调度 |
| TensorRT-LLM | 执行引擎，负责在 GPU 上跑 Wide EP 并把卡间通信压到最低 |
| MTP | 多 token 预测，一次生成多个 token，摊薄「读权重」的固定成本 |