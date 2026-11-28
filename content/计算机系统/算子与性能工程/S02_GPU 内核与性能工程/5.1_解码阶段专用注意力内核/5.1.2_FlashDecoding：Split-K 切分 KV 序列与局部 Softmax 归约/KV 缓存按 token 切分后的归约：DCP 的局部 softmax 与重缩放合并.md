# 把 KV 缓存按 token 分给两张卡：DCP 的局部 softmax 与重缩放合并

> 视频来源：[Decode Context Parallelism (DCP): Splitting the KV Cache by Tokens](https://www.youtube.com/watch?v=21UD05Ohrqs)（YouTube · Deep Optimus）｜时长约 19 分钟
> 导读：这支视频讲 vLLM 的 DCP（decode context parallelism）——当张量并行把同一份 KV 缓存复制到多张卡上时，按 token 把这份缓存切开，再用「局部最大值 + 局部指数和 + 重缩放合并」把两边算出的局部注意力拼回精确结果。它的尺度是「两张 GPU」，而 FlashDecoding 的 Split-K 是「一个内核里的多个 block」，但两者用的是**同一套切分与归约数学**；这支视频的价值正在于它把归约那一步算到了具体数字。

## 本讲要解决的核心问题（SCQA）

**背景**：张量并行（TP）把模型的权重按 head 切到多张 GPU 上。当 GPU 数多于 key/value head 数时，一个 KV head 只能落到多张卡上，而跟着权重一起过去的还有它的 KV 缓存。

**冲突**：于是同一份缓存被存了两遍。视频的例子里，每张 GPU 为每个 token 保存约 48 KB 缓存（跨 94 层），一段 10 万 token 的对话每张卡占 4.8 GB，其中一半是纯拷贝——这些显存本可以装下更多请求。

**疑问**：能不能不复制？如果把一份缓存按 token 分给两张卡，每个 query head 又需要全部 token 才能算注意力，结果还能对吗？

**回答（中心思想）**：可以。注意力是对全部 token 求和，而**和可以拆开**：每张卡只在自己那半 token 上算，额外保留三个数——局部最大值 $M$、局部指数和 $L$、局部加权输出 $O$；再用一次 all-gather 交换 $M$ 与 $L$，按 online softmax 的重缩放规则把两半合成全局结果。这与单卡上 FlashDecoding 的 Split-K 归约是同一套规则，区别只在切分的粒度和通信的介质：那边是内核里的多个 block 写临时缓冲区，这边是两张 GPU 之间发消息。

## 一、问题出在「GPU 比 KV head 多」

### 1.1 权重怎么切，缓存就跟着怎么复制

视频用一个具体模型走了一遍：例子模型只有 4 个 key/value head，却要跑在 8 张 GPU 上，于是张量并行只能把每个 key/value head 交给两张 GPU——GPU 0 和 GPU 1 都持有 head 0，GPU 2 和 GPU 3 都持有 head 1，其余依此类推。[【跳转到 01:24】](https://www.youtube.com/watch?v=21UD05Ohrqs&t=84)

GPU 1 为什么需要 head 0？因为每 16 个 query head 共享一个 key/value head，而它的 head 8 到 15 正属于 head 0 这一组。跟着这些权重一起过来的还有缓存：两张 GPU 都为 head 0 保存此前每个 token 的 key 和 value，也就是同一批数字的两份拷贝。[【跳转到 02:09】](https://www.youtube.com/watch?v=21UD05Ohrqs&t=129)

![缓存的每一行是一个 token，每一格是该 token 在一个 KV head 上的 key 或 value（128 个数）](assets/KV%20缓存按%20token%20切分后的归约：DCP%20的局部%20softmax%20与重缩放合并/00245.webp)

算一下代价：跨全部 94 层，每张 GPU 为每个 token 保存约 48 KB 缓存；一段 10 万 token 的对话因此在每张 GPU 上占 4.8 GB，其中一半是拷贝。[【跳转到 02:59】](https://www.youtube.com/watch?v=21UD05Ohrqs&t=179)

### 1.2 修复只针对这些拷贝

vLLM 的 DCP 规则很短：**DCP 大小最大不超过张量并行大小除以 key/value head 的数量**。这里的 DCP 大小，指有多少张 GPU 共享同一个 head 的缓存。[【跳转到 02:59】](https://www.youtube.com/watch?v=21UD05Ohrqs&t=179)

对 8 卡上的这个 4 KV head 模型，上限算出是每个 head 两张 GPU——正好就是共享同一个 key/value head 的那一对对 GPU，每一对构成一个 DCP 组。而且只有缓存被切分，key 和 value 的**权重**仍然保持拷贝，因为它们很小而且不会增长。[【跳转到 03:34】](https://www.youtube.com/watch?v=21UD05Ohrqs&t=214)

## 二、切分：token 像发牌一样轮流分配

在每一对内部，两张 GPU 不再拷贝，而是按 token 把这个 head 的缓存分给彼此：第一个 token 留在 GPU 0，第二个给 GPU 1，第三个又回到第一张。在 vLLM 里这就是默认的交错大小 1（配置项 `cp_kv_cache_interleave_size`），第 $i$ 个 token 交给它所在那一对里位置为 $i \bmod 2$ 的 GPU。[【跳转到 03:09】](https://www.youtube.com/watch?v=21UD05Ohrqs&t=189)

![token i 交给所在那一对里位置为 i mod 2 的 GPU，交错大小为 1](assets/KV%20缓存按%20token%20切分后的归约：DCP%20的局部%20softmax%20与重缩放合并/00330.webp)

一个工程上的小细节：每张 GPU 都知道每个 token 的位置，所以它自己就能算出归属，不需要查表。[【跳转到 03:34】](https://www.youtube.com/watch?v=21UD05Ohrqs&t=214)

效果是缓存直接减半：每张 GPU 每个 token 从约 48 KB 降到约 24 KB，那段 10 万 token 的对话从 4.8 GB 降到 2.4 GB，腾出的一半可以装别的请求。[【跳转到 03:54】](https://www.youtube.com/watch?v=21UD05Ohrqs&t=234)

## 三、切了之后：每个 query head 仍需要全部 token

### 3.1 和可以拆开

缓存切开之后立刻出现一个矛盾：每个 query head 都要拿自己和**每个** key 打分，softmax 把这些分数变成加起来等于 100% 的权重，head 的输出就是全部 value 的加权和——注意力是对所有 token 求和。只有一半 token 的 GPU 0 怎么算？[【跳转到 06:26】](https://www.youtube.com/watch?v=21UD05Ohrqs&t=386)

答案是：**一个和可以拆开**。GPU 0 可以把自己那些 token 加起来，GPU 1 把剩下的加起来，两部分之后再合并。[【跳转到 04:18】](https://www.youtube.com/watch?v=21UD05Ohrqs&t=258)

![GPU 0 持偶数位置 token、GPU 1 持奇数位置 token，各自算自己那半的分数](assets/KV%20缓存按%20token%20切分后的归约：DCP%20的局部%20softmax%20与重缩放合并/00410.webp)

但有两个麻烦要一起解决：

1. **分母是全局的**：每个权重都要除以全部 8 个 token 的总和，而两张 GPU 谁都不知道这个总和；
2. **query head 本身也被切开了**：GPU 0 持有 query head 0 到 7，GPU 1 持有接下来 8 个 head。普通张量并行下这没问题，因为每张卡都有全部 token；现在 GPU 0 只有偶数 token，它的 query head 还需要 GPU 1 上的奇数 token。

### 3.2 让 query 移动，而不是让缓存移动

解决第二个麻烦有两条路：把缓存搬过去，或者把 query 搬过来。视频算了一笔账：GPU 0 的 8 个 query head 一共 1,024 个数，每层只有 2 KB；而 GPU 1 持有另一半缓存，对一段 10 万 token 的对话，每层约 25.6 MB，而且还会继续增长。[【跳转到 08:14】](https://www.youtube.com/watch?v=21UD05Ohrqs&t=494)

所以选择让 **query 移动、缓存留在原地**：每一对内部先对 query 做一次 all-gather，两张卡于是都持有全部 16 个 query head，它们都要读这个 key/value head。这些副本只用于这一步，用完就丢。[【跳转到 05:19】](https://www.youtube.com/watch?v=21UD05Ohrqs&t=319)

视频顺带对比了三种并行方式，这段对比很有助于理解「谁该移动」：

| 方式 | 切的是什么 | 谁在移动 |
| --- | --- | --- |
| 长 prompt 上的上下文并行 | 每张卡有许多自己的 query token | key 和 value 移动 |
| 序列并行 | 只在 norm 与残差相加处切 token，注意力仍看全部 token | 不需要为注意力搬数据 |
| DCP（decode） | 每张卡只有一行 query，缓存按 token 切 | query 与 M/L 移动 |

[【跳转到 05:44】](https://www.youtube.com/watch?v=21UD05Ohrqs&t=344)

## 四、局部注意力：三个数就够了

现在每张 GPU 为全部 16 个 head 跑注意力，但只在自己那些 token 上跑，结果只是局部的。视频用一个 8 token 的玩具例子把它算穿：每张卡拿 query 与自己的 4 个 key 打分，然后保留三个运行中的数。[【跳转到 09:29】](https://www.youtube.com/watch?v=21UD05Ohrqs&t=569)

$$
M = \max_{j \in S} s_j,\qquad
L = \sum_{j \in S} e^{s_j - M},\qquad
O = \sum_{j \in S} e^{s_j - M} v_j
$$

其中 $S$ 是这张卡负责的 token 集合。三个数各有分工：$M$ 是见过的最大分数，作用是让每个指数不超过 1、不溢出；$L$ 是这些指数之和；$O$ 是按同样指数加权后的 value 之和。于是**一张卡自己的答案是 $O/L$**。[【跳转到 05:59】](https://www.youtube.com/watch?v=21UD05Ohrqs&t=359)

![每张卡保留 m、l、O 三个数，局部答案是 O/l；但每个只见过一半 token](assets/KV%20缓存按%20token%20切分后的归约：DCP%20的局部%20softmax%20与重缩放合并/00595.webp)

但 $O/L$ 只是局部的：每个只见过一半 token。视频给的对照是——如果 8 个 token 都在，单张 GPU 会得到 $1.08$。[【跳转到 06:24】](https://www.youtube.com/watch?v=21UD05Ohrqs&t=384)

## 五、归约：把两半拼成精确结果

### 5.1 先交换 M 与 L

要合并两个答案，每张 GPU 都需要对方的 $M$ 和 $L$。所以第二条消息是对每个 head 的这两个数做 all-gather，收到后把两者打包成每个 head 一个数，叫做 **log-sum-exp**：

$$
\mathrm{LSE} = M + \log L
$$

[【跳转到 06:29】](https://www.youtube.com/watch?v=21UD05Ohrqs&t=389)

### 5.2 取全局最大值，把指数和搬到同一基准

拿到两对数之后，每张 GPU 先找全局最大值：例子里是 $3.0$，来自第一张卡。然后把两个指数和相加——注意 GPU 1 的 $1.73$ 是在 $M=2.5$ 的基准下算的，要先乘上 $e^{2.5-3.0}$ 搬到 $3.0$ 的基准下：

$$
M = \max(3.0,\ 2.5) = 3.0,\qquad
L = 1.55 + 1.73\,e^{2.5-3.0} = 1.55 + 1.05 = 2.60
$$

[【跳转到 06:54】](https://www.youtube.com/watch?v=21UD05Ohrqs&t=414)

![合并第一步：取全局最大值 3.0，把另一张卡的指数和按 e^{2.5-3.0} 搬到同一基准，得到 2.60](assets/KV%20缓存按%20token%20切分后的归约：DCP%20的局部%20softmax%20与重缩放合并/00660.webp)

### 5.3 按份额重缩放，再相加

有了全局的 $M$ 与 $L$，每张卡的**份额**就确定了——它的 token 分到了多少注意力：GPU 0 是 $0.60$，剩下 $0.40$ 归另一张。每张卡用自己的局部答案乘上自己的份额：

$$
o = 0.60 \times 0.50 + 0.40 \times 1.94 = 0.30 + 0.78 = 1.08
$$

结果 $1.08$ 正好等于单张 GPU 拿全部 8 个 token 得到的值。[【跳转到 11:19】](https://www.youtube.com/watch?v=21UD05Ohrqs&t=679)

![合并第二步：按份额 0.60 / 0.40 重缩放局部答案，相加得到 1.08，与单卡结果完全一致](assets/KV%20缓存按%20token%20切分后的归约：DCP%20的局部%20softmax%20与重缩放合并/00690.webp)

视频在这里下了一个关键判断：**这与 online softmax 的重缩放规则是同一套，所以切分 token 完全不改变结果。**[【跳转到 07:06】](https://www.youtube.com/watch?v=21UD05Ohrqs&t=426) 回到 GPU 上，这些重缩放后的答案仍然是局部和，16 个 head 各一个，还需要在一对 GPU 之间相加；而每张 GPU 只需要自己那 8 个 head，因为输出矩阵正是按这些 head 做行切分的。只需要自己那一片的局部和，对应的是 **reduce-scatter**——这就是第三条消息。[【跳转到 07:02】](https://www.youtube.com/watch?v=21UD05Ohrqs&t=422)

### 5.4 三条消息的分工

把归约拆开看，DCP 在一次 decode 的每个注意力层里只加三条小消息，而且每条都留在一对 GPU 内部：

1. **all-gather query**：让两张卡都拿到全部 16 个 query head；
2. **all-gather $M$ 与 $L$**：交换合并所需的两个数（打包成 LSE）；
3. **reduce-scatter $O$**：把重缩放后的局部和按 head 切回各自的卡。

[【跳转到 08:52】](https://www.youtube.com/watch?v=21UD05Ohrqs&t=532)

其余部分完全不变：输出矩阵产生局部和，由全部 8 张 GPU 上的 all-reduce 加起来；专家（MoE）部分一行代码都不用改。[【跳转到 07:27】](https://www.youtube.com/watch?v=21UD05Ohrqs&t=447)

## 六、什么时候有用：DCP 大小的上限

视频最后把规则收拢成一张图：

$$
\text{DCP size} \le \frac{\text{TP size}}{\text{KV heads}}
$$

![DCP 大小上限与三种情形：Qwen3 4 KV head 可切 2，潜在注意力可切 8，8 KV head 在 8 卡上无可切](assets/KV%20缓存按%20token%20切分后的归约：DCP%20的局部%20softmax%20与重缩放合并/01135.webp)

三种情形对比得很清楚：

- **Qwen3-235B（GQA）**：4 个 KV head 在 8 张 GPU 上，每个被复制两次 → DCP 最多 2；
- **潜在注意力（DeepSeek-V3、Kimi）**：每个 token 只有一个共享的潜在向量服务所有 head，8 张卡就是 8 份拷贝 → DCP 最多 8；
- **8 个 KV head 跑在 8 张 GPU 上**：每张卡拿到自己的 head，没有任何拷贝 → DCP 为 1，切了也没收益。

[【跳转到 11:35】](https://www.youtube.com/watch?v=21UD05Ohrqs&t=695)

vLLM 在一个 8 卡 NVIDIA B200 节点上，用带潜在注意力的 Kimi K2.6 测过 DCP：腾出的缓存能同时装更多请求，吞吐从每张 GPU 约 1,863 token/s 升到约 6,091 token/s。[【跳转到 11:30】](https://www.youtube.com/watch?v=21UD05Ohrqs&t=690)

代价也写在规则里：vLLM 的文档把取舍说得很直白——**DCP 组越大，拷贝的缓存越少，但通信越多**。[【跳转到 10:50】](https://www.youtube.com/watch?v=21UD05Ohrqs&t=650)

## 七、一个 token 走完全程：DCP 只动了注意力那一格

视频用后半段把一个新 token 从 ID 一路跟到下一个 token，用来确认「DCP 到底改了哪些地方」。

**入口：embedding 的行切分。** 每段文本先经 tokenizer 变成一个整数 ID，ID 指出该 token 在 151,936 行词表里的那一行。8 张 GPU 都收到同一个 ID；这一行只落在其中一张卡负责的区段里，那张卡取到真实数字，其余 7 张写全零向量。于是 8 个向量都是局部和，相加时零不改变结果，总和就是该 token 的精确向量。因为第 0 层开头是一个完整的 RMS norm 和 W_Q 的列切分，两者都需要每张卡上都有完整 token，所以这次 all-reduce 把总和发回每一张卡。[【跳转到 07:52】](https://www.youtube.com/watch?v=21UD05Ohrqs&t=472)

**层内：五条消息。** 每张卡像普通张量并行那样生成自己 8 个 head 的 query；随后是 DCP 的三条消息（all-gather query、共享 $M$ 与 $L$、reduce-scatter $O$）；之后又是普通张量并行的 all-reduce（W_O 之后、专家 down 矩阵之后）。所以一层里一共五条消息，其中只有三条是 DCP 带来的。[【跳转到 08:27】](https://www.youtube.com/watch?v=21UD05Ohrqs&t=507)

**出口：输出层的列切分。** 第 93 层之后是一次 RMS norm（权重很小，每张卡保留完整副本），接着输出层把这 4,096 个数变成词表里每个 token 的分数。列切分给出的是成品而不是局部和，所以每张卡持有自己那一段词表的最终分数，这里不需要相加，只需要把各段拼起来——那是 all-gather 的工作。每张卡把自己那 18,992 个分数发给另外 7 张，于是每张卡都拿到整个词表的分数。之所以每张卡都要全部分数，是因为下一步是在全部 8 张卡上做的查表，每张都需要下一个 token 的 ID。[【跳转到 09:48】](https://www.youtube.com/watch?v=21UD05Ohrqs&t=588)

视频最后把「什么时候需要哪条消息」总结成一张对照表，这张表很值得记住：

| 切分方式 | 留下什么 | 用什么合并 |
| --- | --- | --- |
| 行切分（embedding、W_O、专家 down） | 局部和 | all-reduce |
| 列切分（Q/K/V、gate/up、输出层） | 成品（整块） | all-gather |
| DCP 的缓存切分 | 局部注意力（$M$、$L$、$O$） | all-gather $M/L$ + reduce-scatter $O$ |

[【跳转到 10:20】](https://www.youtube.com/watch?v=21UD05Ohrqs&t=620)

## 八、和 FlashDecoding 的 Split-K 对照着看

把两支视频放在一起，会发现「切分 + 局部 softmax + 归约」是一套可以搬来搬去的模式：

| 维度 | FlashDecoding 的 Split-K | DCP |
| --- | --- | --- |
| 切什么 | 一条请求的 KV 缓存沿序列维切块 | 一个 KV head 的缓存按 token 切给两张卡 |
| 谁来做每个 split | 一个线程块（block） | 一张 GPU |
| 局部结果 | 局部 $m_i$、$\ell_i$、$o_i$ | 局部 $M$、$L$、$O$ |
| 归约介质 | 第二个内核读临时缓冲区 | all-gather $M/L$ + reduce-scatter $O$ |
| 切多少 | 缓存总长 ÷ 线程块数的「公平份额」 | $\text{TP size} / \text{KV heads}$ 的上限 |
| 结果是否精确 | 是（与顺序无关） | 是（与 online softmax 同一规则） |
| 主要代价 | 临时缓冲区 + 一次合并内核 | 每个注意力层三条跨卡消息 |

两者的共同点正是这一小节要抓住的东西：**局部 softmax 的归约不是近似，而是一次「换基准 + 重新分配份额」的重缩放**。只要每个局部结果都带着自己的最大值和指数和，无论切分发生在块内、内核间还是跨卡，合并公式都一样。

## 小结

- 张量并行在「GPU 数 > KV head 数」时会复制 KV 缓存；视频例子里每张卡为每个 token 存约 48 KB，10 万 token 的对话占 4.8 GB，一半是拷贝。
- DCP 只切缓存、不切权重：一个 head 的缓存按 token 交错分给共享它的那几张卡，默认交错大小为 1，第 $i$ 个 token 归 $i \bmod 2$ 那张卡。
- 切分后缓存减半（48 KB → 24 KB / token），代价是每张卡只有一半 token，而每个 query head 都需要全部 token。
- 让 query 移动、缓存不动：每层 query 只有 2 KB，而半份缓存每层约 25.6 MB。
- 每张卡保留三个数：局部最大值 $M$、局部指数和 $L$、局部加权输出 $O$，局部答案是 $O/L$。
- 归约三步：all-gather $M/L$（打包成 $\mathrm{LSE}=M+\log L$）→ 取全局最大值并把指数和搬到同一基准（$1.55+1.73e^{-0.5}=2.60$）→ 按份额重缩放相加（$0.60\times0.50+0.40\times1.94=1.08$）。
- 这与 online softmax 的重缩放规则相同，切分不改变结果；最后用 reduce-scatter 把各自那 8 个 head 还回去。
- 适用条件是「缓存被复制」：Qwen3 的 4 KV head 在 8 卡上可切 2，潜在注意力可切 8，8 KV head 在 8 卡上无可切；实测吞吐 1,863 → 6,091 token/s per GPU。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| DCP（decode context parallelism） | 把一份 KV 缓存按 token 切给多张共享同一 KV head 的 GPU，decode 时各自算局部注意力再合并 |
| 交错大小（interleave size） | 按 token 轮流分配的粒度，默认 1 表示第 $i$ 个 token 归 $i \bmod 2$ 那张卡 |
| 局部最大值 $M$ | 一张卡在自己那段 token 上见过的最大分数，用来防指数溢出 |
| 局部指数和 $L$ | $\sum_j e^{s_j-M}$，这张卡负责的那段 token 的总权重 |
| 局部输出 $O$ | 按同样指数加权的 value 之和，$O/L$ 是这张卡的局部答案 |
| log-sum-exp（LSE） | $M+\log L$，把「最大值 + 指数和」压成一个数，便于跨卡交换与缩放 |
| 份额（share） | 一张卡的指数和在全局指数和里的占比，用来重缩放它的局部答案 |
| reduce-scatter | 归约后每张卡只保留自己需要的那一片结果（这里是自己的 8 个 head） |
| 潜在注意力（MLA） | 每个 token 只有一个共享潜在向量服务所有 head，因此每张卡都持有同一份缓存，DCP 收益最大 |
| 张量并行（TP） | 把权重按 head/列/行切到多张 GPU，GPU 数超过 KV head 数时会复制 KV 缓存 |