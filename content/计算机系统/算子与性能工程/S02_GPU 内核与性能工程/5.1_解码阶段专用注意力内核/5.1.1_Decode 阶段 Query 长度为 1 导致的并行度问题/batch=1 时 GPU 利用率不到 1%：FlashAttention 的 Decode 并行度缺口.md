# batch=1 时 GPU 利用率不到 1%：FlashAttention 的 Decode 并行度缺口

> 视频来源：[【LLM推理】FlashDecoding 解析：用 FlashAttention 加速长上下文推理](https://www.bilibili.com/video/BV1n8XwY1EW7/)（Bilibili · 我是小小升）｜时长约 6 分钟
> 导读：一支 6 分钟的精讲，前半段用 FlashAttention V2 的伪代码说明「并行维度是怎么来的」，后半段说明 decode 为什么把这个维度弄丢了、损失有多大（batch=1 时利用率不到 1%），以及补回并行度为什么必须付一次归约的代价。本文的主线是**问题本身**：并行度缺口有多大、缺口从哪里来。

## 本讲要解决的核心问题（SCQA）

**背景**：FlashAttention 靠分块把注意力算得又快又省显存，训练时它能在 batch size 和序列长度两个维度上并行，GPU 基本能跑满。

**冲突**：到了推理的 decode 阶段，每一步只输入一个新生成的 token，序列长度变成 1。FlashAttention 最依赖的那个并行维度——沿 query 序列切块——直接消失了。

**疑问**：少了一个并行维度到底损失多少？为什么长上下文会让情况更糟？补回并行度要付出什么代价？

**回答（中心思想）**：FlashAttention 的并行度来自「batch size × query 序列长度 × head」；decode 把 query 序列长度固定成 1，只剩 batch 维度。当 batch 小于一张卡的 SM 数时，一部分 SM 根本分不到任务——官方博客给出的极端例子是 batch=1 时 GPU 利用率不到 1%。而长上下文让 KV Cache 吃掉大量显存，batch 又被迫压小，两个效应叠加，并行度缺口越拉越大。

## 一、先复习：FlashAttention 在训练阶段怎么并行

### 1.1 分块矩阵乘：外层遍历 Q，内层遍历 KV

注意力本身只有三步：$S = QK^\top$，$P = \mathrm{softmax}(S)$，$O = PV$。FlashAttention 不改数学，只改执行顺序：把 Q、K、V 都切成小块，在片上反复算，避免 $N\times N$ 的中间矩阵落回 HBM。[【跳转到 00:24】](https://www.bilibili.com/video/BV1n8XwY1EW7/?t=24)

FlashAttention V2 是**两层循环**：外层遍历每一块 Q，内层遍历每一块 KV。外层走到某一块 Q 时，内层把每一块 KV 都走一遍，就能算出 O 对应的那一块——因为 Q 和 O 在序列维度上一一对应。[【跳转到 00:49】](https://www.bilibili.com/video/BV1n8XwY1EW7/?t=49)

![分块矩阵乘：Q 的一块乘 K 的每一块得到 S/P 的一行四块，再分别乘 V 的每一块求和得到 O 的一块](assets/batch=1%20时%20GPU%20利用率不到%201%：FlashAttention%20的%20Decode%20并行度缺口/00024.webp)

具体到每一块：Q 的第一块乘 K 的每一块，得到 S（也就是 P）第一行的四块；这四块分别乘 V 的对应块——第一块乘第一块、第二块乘第二块——最后把四块加起来，就是 O 的第一块。

### 1.2 伪代码里的划分方式

在 FlashAttention V2 的伪代码里，分块矩阵乘的部分就是图中用蓝线圈出来的那些行：把 Q 沿 sequence length 维度划分成 $T_r$ 块，K/V 沿同一维度划分成 $T_c$ 块，O 也按 Q 的方式划分成 $T_r$ 块。[【跳转到 01:10】](https://www.bilibili.com/video/BV1n8XwY1EW7/?t=70)

![FlashAttention V2 伪代码：外层遍历 Q 块、内层遍历 KV 块，逐块更新 online softmax 与 O](assets/batch=1%20时%20GPU%20利用率不到%201%：FlashAttention%20的%20Decode%20并行度缺口/00095.webp)

循环体里做的事是：算出新的 $S = QK^\top$，再算出新的 $P$，把这一块的 $PV$ 累加到前面已经得到的 $PV$ 和上，这就是 O；最后再统一除以 row sum（行和）。

### 1.3 于是有了两个天然的并行维度

这个循环结构直接决定了并行方式：

- **batch size 维度**：不同样本互不相干，分到不同的线程块上算，有点像数据并行（DataParallel）；
- **sequence length 维度**：因为外层循环遍历的是 Q，对每一块 Q 可以算出对应的一块 O，所以沿 Q 划分很自然，伪代码很方便就能翻译成实际的 kernel 代码。

课程把这一点讲得很清楚：可并行不是「算法厉害」，而是**循环结构允许把哪一维切开**。[【跳转到 01:35】](https://www.bilibili.com/video/BV1n8XwY1EW7/?t=95)

## 二、推理阶段：并行维度塌掉一个

### 2.1 decode 把序列长度固定成 1

推理分两个阶段：先做一次 prefill，处理整段 prompt；然后进入 decode，每次只把新生成的一个 token 输入模型，得到下一个 token 的分布。这时候 sequence length 就是 1，因为只输入了一个 token。[【跳转到 02:00】](https://www.bilibili.com/video/BV1n8XwY1EW7/?t=120)

于是 FlashAttention 在 decode 阶段**只能在 batch size 维度上并行**。原来那个「沿 Q 切块」的维度只剩一块，外层循环只转一圈。

### 2.2 batch 小于 SM 数，就有一部分 SM 分不到任务

GPU 的并行度最终要落到硬件上：一张卡有固定数量的 SM（Streaming Multiprocessor，流多处理器），每个 SM 同时能跑若干个线程块。任务数少于 SM 数时，多出来的 SM 就分不到活。

课程的原话是：如果 batch size 比一张卡上 SM 的数目还小，那这些 SM 就不能全部利用。[【跳转到 02:25】](https://www.bilibili.com/video/BV1n8XwY1EW7/?t=145)

### 2.3 长上下文让情况更糟：KV Cache 挤占 batch

更麻烦的是，长上下文会从另一个方向掐住并行度。上下文越长，KV Cache 越大、占用的显存越多，模型在 decode 阶段能开的 batch size 就越小，并行度也就跟着下降。

这就形成了一个负反馈：**上下文越长 → KV Cache 越大 → batch 越开不大 → 并行度越低 → 越跑不满 GPU**。[【跳转到 02:25】](https://www.bilibili.com/video/BV1n8XwY1EW7/?t=145)

### 2.4 缺口的量级：不到 1%

FlashDecoding 的官方博客给了一个极端例子：batch size 等于 1 时，GPU 利用率会小于 1%。[【跳转到 02:50】](https://www.bilibili.com/video/BV1n8XwY1EW7/?t=170)

![FlashDecoding 论文的 Challenge 页：训练可在 batch size 与 query length 上并行，推理的 query length 通常是 1；batch 小于 SM 数就只用上一小部分 GPU，batch=1 时利用率不到 1%](assets/batch=1%20时%20GPU%20利用率不到%201%：FlashAttention%20的%20Decode%20并行度缺口/00170.webp)

视频作者对这个数字保持了诚实：他说不清楚这个数据是在什么条件下测出来的，但它想表达的意思是明确的——**FlashAttention 直接用在推理阶段会面临并行度不够的问题**。这也是为什么「batch=1、长上下文」成了后续一系列 decode 专用内核的靶心。

## 三、把并行维度补回来：沿 KV 序列切分

既然 query 那边没得切，那就换一个方向切：**在 KV 的 sequence length 维度上也做并行**。[【跳转到 03:15】](https://www.bilibili.com/video/BV1n8XwY1EW7/?t=195)

做法很朴素：

1. 把 K/V 按 sequence length 切成若干块；
2. 每一块内部做**标准的 FlashAttention**（query 只有一行，仍要读这一块的全部 K/V）；
3. 每一块得到自己的局部 O，最后用 log-sum-exp 把这些 O 合并成一个。

![FlashDecoding 的思路：新增一个并行维度——K/V 的 sequence length，把 KV 切成 5 份并行算，再归约](assets/batch=1%20时%20GPU%20利用率不到%201%：FlashAttention%20的%20Decode%20并行度缺口/00212.webp)

这样任务数就从「batch × head」变成了「batch × head × 分段数」，KV 越长可以切得越多，SM 也就越能吃满。视频里合并的是 5 块的 O。

## 四、并行度的代价：必须做一次归约

补并行度不是免费的。原来一个任务从头算到尾，online softmax 的状态一直在自己手里；现在每块各算各的，**每块手里的 O 都是「只除以自己那一段的 row sum」的半成品**，必须再做一次归约才能拼成正确答案。[【跳转到 03:32】](https://www.bilibili.com/video/BV1n8XwY1EW7/?t=212)

### 4.1 局部 O 除以的是局部 row sum

推导从第一块开始。对 Block 1，它算出的 softmax 是「每个元素取以 e 为底的指数，再除以这些元素的和」，这个和称为 row sum，记作这一块的和。它再乘 V 就得到 $O_1$。

问题在于：$O_1$ 里每个元素除的是**第一块自己的 row sum**；而合并成完整的 O 时，理论上每个元素应该除以**所有块的总 row sum**。[【跳转到 04:24】](https://www.bilibili.com/video/BV1n8XwY1EW7/?t=264)

所以还原的办法是：先把原来那块 row sum 乘回去（把半成品还原成「未归一化的加权和」），再除以完整的 row sum。

### 4.2 用 log-sum-exp 合并

每一块都做同样的操作。假设一共 $B$ 块，第 $i$ 块的状态记作 $L_i$、局部输出记作 $O_i$，则

$$
L = \ln\left(\sum_{i=1}^{B} e^{L_i}\right),\qquad O = \sum_{i=1}^{B} \mathrm{diag}\left(e^{L_i - L}\right) O_i
$$

![FlashDecoding 的 Reduce：各段 O 先按自己的 row sum 还原，再用全局 log-sum-exp 归一化后相加](assets/batch=1%20时%20GPU%20利用率不到%201%：FlashAttention%20的%20Decode%20并行度缺口/00289.webp)

这两个式子的含义正好对应上面的推导：

- $L$ 是全局的 log-sum-exp，$e^{L}$ 就是所有块的 row sum 之和，也就是完整的分母；
- $e^{L_i - L}$ 就是「本块 row sum ÷ 全局 row sum」这个系数；
- 把每个局部 $O_i$ 乘上这个系数再相加，等价于「先乘回自己的 row sum、再统一除以全局 row sum」。

而这个 $L_i$ 并不需要额外算：它就是 FlashAttention 循环里本来就在累积的那个 logsumexp。视频特别指出，这个量原本是在反向传播时才会用到的，在这里正好拿来合并不同块的 O。[【跳转到 03:44】](https://www.bilibili.com/video/BV1n8XwY1EW7/?t=224)

### 4.3 为什么要写 diag：decode 与 prefill 的区别

公式里出现 $\mathrm{diag}$ 是因为 $L$ 的形态随场景变化：

- 在 decode 阶段 sequence length 是 1，$L$ 是一个**标量**，乘上去就是普通的数乘；
- 在 prefill 阶段 sequence length 不只是 1，$L$ 就是一个**向量**，每个 query 行有自己的 row sum。这时要把 $L$ 做成对角矩阵，左乘 $O$ 就相当于「用这个向量的每个元素去乘 O 的每一行」。[【跳转到 05:14】](https://www.bilibili.com/video/BV1n8XwY1EW7/?t=314)

把各行乘完再求和，就得到完整的 O。这就是 FlashDecoding 里对 O 做 reduce 的全过程。[【跳转到 05:39】](https://www.bilibili.com/video/BV1n8XwY1EW7/?t=339)

## 小结

- FlashAttention 的并行维度来自循环结构：外层遍历 Q 块、内层遍历 KV 块，所以 batch 和 query 序列都能切开。
- decode 每步只输入一个 token，sequence length 变成 1，只剩 batch 这一个并行维度。
- batch 小于一张卡的 SM 数时，一部分 SM 分不到任务；官方博客的极端例子是 batch=1 时 GPU 利用率不到 1%。
- 长上下文让 KV Cache 吃掉显存，batch 被迫压小，与「并行维度只剩 batch」形成负反馈。
- 补并行度的方向是沿 KV 的 sequence length 切分，每块做标准 FlashAttention，再把局部 O 归约。
- 归约不能省：局部 O 除的是局部 row sum，必须用全局 log-sum-exp 重新归一化；$L$ 就是 FlashAttention 里累积的那个 logsumexp。
- decode 时 $L$ 是标量、prefill 时 $L$ 是向量（需要 diag），这是同一个公式的两种形态。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| prefill | 一次性处理整段 prompt 的阶段，query 有多行，并行度高 |
| decode | 逐 token 生成的阶段，每步只输入一个 token，query 只有一行 |
| SM（Streaming Multiprocessor） | GPU 上执行线程块的单元，数量固定；任务数少于它就会有 SM 空闲 |
| batch size | 一次同时处理的请求数，decode 阶段唯一剩下的主要并行维度 |
| KV Cache | 缓存历史 token 的 K/V，长上下文时占用大量显存，反过来限制 batch |
| online softmax | 分块计算时逐块更新最大值与指数和的技巧，使结果与整块计算等价 |
| logsumexp（$L$） | 每块累积的「指数和的对数」，FlashDecoding 用它把各块 O 归一化合并 |
| row sum | 一行 softmax 的分母（指数之和）；分块后每块只有局部 row sum |
| reduce / 归约 | 把多个分段的局部结果按统一基准合并成最终输出的一步 |