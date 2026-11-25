# Mixtral 8x7B 粗粒度专家：47B 总参数、13B 激活的稀疏架构

> 视频来源：[mistral7b、mixtral8x7b,DeepseekMOE技术讲解](https://www.bilibili.com/video/BV18Z421a7x3/)（Bilibili · UP 主 poker125）｜时长约 24 分钟
> 导读：这支视频是一次「三篇论文连着读」的分享，按 Mistral 7B → Mixtral 8x7B → DeepSeekMoE 的顺序讲。本文只整理其中的 **Mixtral 8x7B 部分（约 11:04–17:33）**，Mistral 7B 的滑动窗口注意力与 DeepSeekMoE 的细粒度专家另有专文。UP 主的口误（`mixture 8×7B`、`87B`、`老马七比`、`奔驰 Mark`、`词表 33 万 2000` 等）已按幻灯片与上下文订正；文中公式按论文写法补全，幻灯片原文以配图为准。

## 本讲要解决的核心问题（SCQA）

**背景**：稠密 Transformer 的参数量和每个 token 的计算量是绑死的——想把 FFN 加宽，参数和算力就一起涨。MoE（Mixture of Experts，混合专家）换了个思路：把一层 FFN 拆成多个「专家」，每个 token 只走其中几个，于是参数量可以远大于单 token 的计算量。

**冲突**：Mixtral 8x7B 的名字很容易让人按字面算账——8 个专家、每个 7B，那就是 56B 参数；如果每个 token 还要走 2 个专家，那激活参数岂不是 14B？可它实际发布的权重只有 47B，论文表格里写的激活参数是 13B。名字和账目对不上。

**疑问**：这 47B 与 13B 是怎么来的？「粗粒度专家」这种设计具体长什么样，代价又在哪里？

**回答（中心思想）**：Mixtral 8x7B 只在 **FFN 层**做专家化，注意力层、嵌入层等其余部分所有 token 共享，所以总参数是 47B 而不是 56B；每个 token 只被路由到 8 个专家中的 2 个，因此激活参数约 13B。它证明了「粗粒度专家 + top-2 路由」已经能用 13B 的推理计算量打到 Llama 2 70B 的水平；而它的局限——专家又少又大、每个专家被迫什么都学——正是后来 DeepSeekMoE 用「细粒度切分 + 共享专家」要解决的问题。[【跳转到 11:34】](https://www.bilibili.com/video/BV18Z421a7x3/?t=694)

---

## 一、先把账算对：47B 总参数，13B 激活

### 1.1 8x7B 不是 56B

UP 主开门见山地点出这个常见误解：乍一看，8x7B 会让人以为是一个 56B 的模型，「其实并不是」。他给的做法很朴素——去看 HuggingFace 上开源的权重，看权重大小，「其实只有 47B」[【跳转到 11:34】](https://www.bilibili.com/video/BV18Z421a7x3/?t=694)。

![Mixtral of Experts 论文速览（arXiv:2401.04088）的标题页，视频从这里开始讲 8x7B 的架构](assets/Mixtral%208x7B%20粗粒度专家：47B%20总参数、13B%20激活的稀疏架构/00694.webp)

为什么不是 56B？关键在于**专家只替换了 FFN**。视频后面讲模型结构时明确说：相比原来的 Transformer，它「把中间的 FFN 隔几层替换成 MoE，或者全部替换成 MoE」[【跳转到 12:10】](https://www.bilibili.com/video/BV18Z421a7x3/?t=730)。也就是说，自注意力、归一化、词嵌入这些层在 8 个「专家路径」之间是**共享**的，只有 FFN 被复制成了 8 份。所以：

- 如果连注意力层都复制 8 份，才是 8 × 7B = 56B；
- 实际只复制 FFN，共享部分只算一次，于是总参数落到 47B。

顺带纠正一个命名上的误会：名字里的 `x` 代表 **mixture（混合）**，而 `7B` 指的是它的底座是 Mistral 7B，**不是**「每个专家 7B」。UP 主也确认了这一点：它用的 base model 就是视频前半段讲的那篇 Mistral 7B[【跳转到 14:42】](https://www.bilibili.com/video/BV18Z421a7x3/?t=882)。

### 1.2 13B 激活是怎么算的

论文的结果表里有一列叫 **Active Params（激活参数）**，Mixtral 8x7B 这一行填的是 13B[【跳转到 16:18】](https://www.bilibili.com/video/BV18Z421a7x3/?t=978)。道理和上面一样：每个 token 只被路由到 2 个专家，所以只有 2 份 FFN 参与计算，其余 6 份专家「在推理时并不会被用到」[【跳转到 12:35】](https://www.bilibili.com/video/BV18Z421a7x3/?t=755)。

于是这对数字可以这样记：

| 口径 | 数值 | 含义 |
| --- | --- | --- |
| 总参数 | 47B | 显存里必须放得下的全部权重 |
| 激活参数 | 13B | 单个 token 真正参与计算的权重 |
| 稀疏比 | 约 3.6 倍 | 47 ÷ 13，参数量与计算量被解耦的倍数 |
| 专家数 / 每 token 专家数 | 8 / 2 | 粗粒度：专家少、每个专家大 |

这张表就是「粗粒度专家」四个字的全部含义：**专家数量少（8 个）、单个专家大（一整个标准 FFN）、每个 token 只挑 2 个**。

---

## 二、粗粒度专家的 MoE 层长什么样

### 2.1 一张图看懂数据流

视频用一张 MoE 层的示意图讲清了前向路径：`inputs` 进来先送到 `router`（路由器），router 同时做两件事——决定把 token 发给哪些专家，并输出一组 **gating weights（门控权重）**；被选中的专家算出结果后，用 gating weights 加权求和，得到 `outputs`[【跳转到 12:10】](https://www.bilibili.com/video/BV18Z421a7x3/?t=730)。

![Mixtral 的 MoE 层示意图：router 选出专家并给出 gating weights，专家输出加权求和；图中文字强调这种划分只发生在 feedforward 层](assets/Mixtral%208x7B%20粗粒度专家：47B%20总参数、13B%20激活的稀疏架构/00730.webp)

幻灯片下方的原文值得逐句读，它解释了为什么要这么设计：

> Sparse Mixture of Experts allows one to decouple throughput from memory costs by only activating subsets of the overall model for each token. … This division happens at feedforward layers of the model.

翻译过来就是：稀疏 MoE 通过「每个 token 只激活整体模型的一个子集」，把**吞吐（算力）**和**显存开销（参数量）**解耦；而这种划分发生在**前馈层**。这句话正好印证了上一节的账：解耦的是 FFN，共享的是其余部分。

### 2.2 gating weight 就是 top-k 选择器

UP 主把 gating weight 讲得很直白：它「其实就是一个 top-k」，k 可以取 1、2 或别的值[【跳转到 13:03】](https://www.bilibili.com/video/BV18Z421a7x3/?t=783)。计算上分三步：

1. 输入 $x$ 乘门控矩阵 $W_g$，得到每个专家的打分；
2. 对打分做 softmax，得到一组归一化的权重；
3. 只保留分数最高的 $k$ 个，其余置零。

Mixtral 取 $k=2$。写成公式就是论文里的那一行：

$$
y = \sum_{i=0}^{n-1} \operatorname{Softmax}\big(\operatorname{Top2}(x \cdot W_g)\big)_i \cdot \operatorname{SwiGLU}_i(x)
$$

其中 $n$ 是专家数，$\operatorname{Top2}(\cdot)$ 表示只保留最大的两个分量、其余置零，$\operatorname{SwiGLU}_i$ 是第 $i$ 个专家的 FFN 变换。

这里有两个容易忽略的细节：

- **softmax 在 top-2 之后再做**：先把非选中项置零，再归一化，所以两个专家的权重加起来等于 1，输出是它们的凸组合。这与「先 softmax 再取 top-2」在数值上不同，前者保证权重重新归一化。
- **专家内部用的是 SwiGLU**：UP 主特别指出「这里边还有一个激活函数叫 SwiGLU」[【跳转到 13:28】](https://www.bilibili.com/video/BV18Z421a7x3/?t=808)。也就是说，被复制的不是普通的两层 MLP，而是带门控的 SwiGLU 前馈块。

---

## 三、逐项读配置表：粗粒度体现在哪里

视频把论文的 Table 1 投在屏幕上逐项过了一遍[【跳转到 13:53】](https://www.bilibili.com/video/BV18Z421a7x3/?t=833)。这张表是理解「粗粒度」最直接的证据：

![Mixtral 的架构配置表：dim 4096、32 层、32 个注意力头、head_dim 128、hidden_dim 14336、8 个 KV 头、上下文 32768、词表 32000、8 个专家、top-2](assets/Mixtral%208x7B%20粗粒度专家：47B%20总参数、13B%20激活的稀疏架构/00833.webp)

| 参数 | 取值 | 说明 |
| --- | --- | --- |
| `dim` | 4096 | 隐藏维度，与 Mistral 7B 一致 |
| `n_layers` | 32 | Transformer 层数 |
| `n_heads` / `head_dim` | 32 / 128 | 32 个注意力头，每头 128 维 |
| `n_kv_heads` | 8 | 用了 GQA，K/V 头只有 8 个 |
| `hidden_dim` | 14336 | 单个专家 FFN 的中间维度 |
| `context_len` | 32768 | 上下文长度 |
| `vocab_size` | 32000 | 词表大小 |
| `num_experts` | 8 | 专家数量 |
| `top_k_experts` | 2 | 每个 token 选 2 个专家 |

三点值得展开：

**第一，中间维度 `hidden_dim` 取 14336，这是单专家内部的宽度。** 稠密 Mistral 7B 的 FFN 中间维度是 14336，这里每个专家仍然是 14336——专家没有被切小，只是被复制成了 8 份。这正是「粗粒度」的字面含义：**专家粒度 = 一整个标准 FFN**。

**第二，8 个专家 × 14336 的 FFN 才是参数大头。** 注意力层（含 GQA 压缩后的 K/V）只有一份，被所有 token 共享；参数量因此集中在 8 份 FFN 上。这也解释了为什么总参数 47B，而激活参数只有 13B——13B ≈ 共享部分 + 2 份 FFN。

**第三，`n_kv_heads` 只有 8，说明它同时用了 GQA。** UP 主提到「K/V 是在一起的，一共 8 个」[【跳转到 14:18】](https://www.bilibili.com/video/BV18Z421a7x3/?t=858)，指的是分组查询注意力把 K/V 头压到 8 组。这是省 KV Cache 的手段，与 MoE 省算力是两条独立的优化线，不要混为一谈。

### 3.1 它开源了什么，没开源什么

UP 主还交代了一个工程事实：官方「只公布了预训练权重和推理部分的代码」，训练部分涉及专家混合、流水线并行等复杂工程，视频没有展开[【跳转到 15:03】](https://www.bilibili.com/video/BV18Z421a7x3/?t=903)。对读论文的人来说这意味着：架构可以照着复现，但训练配方（数据配比、并行切分、负载均衡系数）需要另找材料。

---

## 四、粗粒度专家的收益：13B 激活打平 70B

结果表是这支视频里信息密度最高的一页[【跳转到 16:18】](https://www.bilibili.com/video/BV18Z421a7x3/?t=978)：

![Mixtral 与 LLaMA 系列的对比表与折线图：Mixtral 8x7B 的激活参数只有 13B，却在多数基准上超过 LLaMA 2 70B](assets/Mixtral%208x7B%20粗粒度专家：47B%20总参数、13B%20激活的稀疏架构/00978.webp)

表格里 Mixtral 8x7B 的 Active Params 一栏写的是 **13B**，而它对比的 LLaMA 2 70B 是 70B。幻灯片下方的结论是：Mixtral 在几乎所有流行基准上**超过或追平 LLaMA 2 70B，而推理时用的激活参数少 5 倍**。

UP 主按对手逐个点评[【跳转到 16:43】](https://www.bilibili.com/video/BV18Z421a7x3/?t=1003)：

- 对 **Mistral 7B**：所有结果都更高，这是「显而易见的」——毕竟它多了 6 个专家的参数。
- 对 **Llama 2 7B**：更高；而 Mistral 7B 本身已经超过了 Llama 2 7B。
- 对 **Llama 2 13B**：这个档位上各项指标也都更高。
- 对 **33B 的 LLaMA**：Mistral 7B 时代在某些点上还弱一些，Mixtral「全面超越了」。
- 对 **Llama 2 70B**：多数指标反超，但「在某些地方还是稍差一点点」。
- 对 **GPT-3.5**：视频也给出了对比结果[【跳转到 17:08】](https://www.bilibili.com/video/BV18Z421a7x3/?t=1028)。

这就是粗粒度专家路线的说服力所在：**参数堆到 47B，但推理只花 13B 的钱**。它不需要把专家做小、也不需要复杂的共享专家设计，只要「8 个大专家 + top-2」就能拿到这个结果。

---

## 五、粗粒度路线的代价：专家又少又大，只能什么都学

收益讲完，代价也要讲清楚，否则就看不懂后来 DeepSeekMoE 为什么要动手术。

粗粒度专家的核心问题是**每个专家被迫成为「通才」**。设想一个 token 被路由到某个专家，这个专家既要处理代码 token，又要处理多语种 token、数学 token——因为专家只有 8 个，而知识的种类远多于 8。于是：

1. **专家内部知识混杂**：一个专家的参数里塞着好几种互不相关的知识，很难同时用好；
2. **专家之间知识冗余**：不同专家为了应付各自的混合输入，会重复学同一批公共知识（语法、常识、高频搭配），这部分参数被学了 8 遍；
3. **组合空间小**：8 个专家选 2 个，只有 $\binom{8}{2}=28$ 种组合，模型能表达的「专家搭配」非常有限。

这三条不是 Mixtral 的 bug，而是「专家粒度 = 一整个 FFN」这个前提的必然结果。要缓解它，只有两条路：**把专家切小**（同样参数下专家数变多，组合空间爆炸式增长），或者**把公共知识单独拎出来**（共享专家）。DeepSeekMoE 正是同时做了这两件事——细粒度专家切分 + 共享专家隔离，在总参数和激活参数都不变的前提下把 2B 模型做到超过 GShard 2.9B。这部分推导与实验见同目录的另一篇：[DeepSeekMoE：细粒度专家切分与共享专家如何消除专家冗余](DeepSeekMoE：细粒度专家切分与共享专家如何消除专家冗余.md)。

---

## 小结

- **名字会骗人**：Mixtral 8x7B 的 `7B` 指底座 Mistral 7B，`x` 指 mixture；总参数 47B 而非 56B，因为只有 FFN 被复制成 8 份，注意力等层共享。
- **两个关键数字**：总参数 47B（显存放得下），激活参数 13B（每 token 只走 2 个专家）。
- **粗粒度的定义**：8 个专家，每个专家的 FFN 中间维度仍是完整的 14336，即「专家 = 一整个标准 FFN」。
- **路由写法**：$y=\sum_i \operatorname{Softmax}(\operatorname{Top2}(xW_g))_i \cdot \operatorname{SwiGLU}_i(x)$，先 top-2 再 softmax，两个专家权重和为 1。
- **收益**：13B 激活参数在多数基准上超过 LLaMA 2 70B，把参数量与推理算力解耦。
- **代价**：专家少而大 → 单专家知识混杂、专家间冗余、组合空间只有 28 种，这正是细粒度 + 共享专家要解决的问题。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| 粗粒度专家（coarse-grained experts） | 专家数量少、每个专家就是一整个标准 FFN 的 MoE 设计，Mixtral 8x7B 是代表 |
| 稀疏激活 | 每个 token 只计算少数几个专家，参数量与单 token 计算量因此解耦 |
| 总参数 / 激活参数 | 前者是显存里要放的全部权重（47B），后者是单 token 实际参与计算的权重（13B） |
| router / gating network | 给每个 token 打分、决定送给哪些专家的那一层，Mixtral 里就是一个线性层加 top-2 |
| gating weight | router 输出的权重，用来对被选中专家的输出做加权求和 |
| top-k 路由 | 只保留打分最高的 k 个专家，Mixtral 取 k=2 |
| SwiGLU | 带门控的前馈块，Mixtral 的每个专家内部都用它 |
| GQA（分组查询注意力） | 让多个 Query 头共享少量 K/V 头，Mixtral 的 `n_kv_heads` 为 8 即此 |