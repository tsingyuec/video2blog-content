# Decode 只有一行 Query：并行度塌缩与三条出路

> 视频来源：[第4课 Decode Attention：Paged KV、GQA 与 Split-KV](https://www.bilibili.com/video/BV13Fa667Epd/)（Bilibili · 想躺平的程序员）｜时长约 20 分钟
> 导读：一支以幻灯片为主线的进阶课，先把「decode 时只有一行 query」这件事算清楚（含 16 MiB KV Cache 的定量例子），再讲 GQA、Paged KV、Split-KV 三条优化各自解决什么。本文按「问题为什么发生 → 任务数不够时 GPU 闲在哪 → 三条出路各自管什么」组织，Split-KV 只讲到动机与代价，具体归约实现留给后续小节。

## 本讲要解决的核心问题（SCQA）

**背景**：FlashAttention 是大家熟悉的注意力内核，它把 Q、K、V 切成小块在片上反复计算，避免 $N\times N$ 的中间矩阵落回 HBM，因此长序列的 prefill 阶段能跑得很满。

**冲突**：到了逐 token 生成的 decode 阶段，每个请求每一步只输入一个 token，query 只有一行。FlashAttention 最自然的并行方式——沿 query 序列切块——突然没有东西可切了。

**疑问**：只有一行 query 时，GPU 上到底还剩多少任务可做？为什么「历史很长」反而帮不上忙？有哪些手段能把并行度补回来？

**回答（中心思想）**：decode 的瓶颈不是「算得不够快」，而是「读取很多、任务很少」——一行 query 仍要读完整条历史的 K/V，但可供 GPU 调度的线程块数量塌缩到接近「并发请求数 × KV head 数」。三条优化分别作用在三个不同层面：GQA 决定**保存哪些** KV，Paged KV 决定**数据在哪里**，Split-KV 决定**有多少个任务**来处理这些数据。只有第三条直接补并行度，而它要付一次段间归约的代价。

## 一、Decode 的瓶颈：读取很多，任务很少

### 1.1 公式没变，变的是 Q 和 KV 的规模

课程一开始就把一个容易混淆的点摆清楚：FlashAttention 是注意力的**计算算法与内核实现**，decode 是**执行注意力的一个场景**，两者并不互斥。进入 decode 后，计算公式一个字都没改，变的是 query 与历史 KV 的规模。[【跳转到 02:03】](https://www.bilibili.com/video/BV13Fa667Epd/?t=123)

固定一个请求、一个 query head，当前 K/V 已经写入缓存。设可见 KV 位置总数为 $N$、每个向量的维度为 $d$，那么这个 query head 的输入输出形状是：

$$
Q \in \mathbb{R}^{1\times d},\qquad K, V \in \mathbb{R}^{N\times d},\qquad O \in \mathbb{R}^{1\times d}
$$

prefill 时 $Q$ 是 $N\times d$，注意力分数是 $N\times N$；decode 时分数只有 $1\times N$——它退化成了一个向量，不再是方阵。[【跳转到 03:43】](https://www.bilibili.com/video/BV13Fa667Epd/?t=223)

![Decode 下的 Q、K、V、O 形状与 16 MiB KV Cache 的定量例子：Q 只有 1×d，K/V 是 N×d](assets/Decode%20只有一行%20Query：并行度塌缩与三条出路/00198.webp)

注意这里有一个容易被误解的地方：FlashAttention 的核心优势——让分数和概率等中间矩阵不落 HBM——在 decode 下**依然成立**。$1\times N$ 的分数向量本来也不大。真正变差的是另一件事：这一行 query 仍然要和**全部**可见的 K 匹配、把对应的 V 汇总起来，读取量一点没少，但能干活的并行单元少了。[【跳转到 04:08】](https://www.bilibili.com/video/BV13Fa667Epd/?t=248)

### 1.2 并行度从哪里来：FlashAttention 沿 Q 切分

要理解「并行度塌缩」，得先看清 FlashAttention 的并行维度是怎么来的。它的两层循环是：**外层遍历每一块 Q，内层遍历每一块 KV**。对某一块 Q，把内层所有 KV 块走一遍，就得到 O 的对应那一块——因为 Q 和 O 在序列维度上是一一对应的。

于是天然可并行的维度有三个：

1. **batch（请求）维度**：不同样本互不相干，分到不同线程块即可；
2. **query 序列维度**：每块 Q 独立算出一块 O，互不依赖；
3. **head 维度**：不同注意力头之间也独立。

decode 把第 2 个维度直接抹掉了：序列长度是 1，只剩一块 Q，外层循环只转一圈。剩下能用的就是「请求数 × head 数」。课程里说得很直白：切分的时候如果只有一个 query，这个并行维度就不够了；虽然还可以沿 head 切分，但可供 GPU 调度的任务数量还是不太够。[【跳转到 03:18】](https://www.bilibili.com/video/BV13Fa667Epd/?t=198)

### 1.3 量化一下：16 MiB 的 KV 对 1×d 的 Query

光说「并行度不够」太抽象，课程给了一个可以直接算的例子：一个请求有 8 个 query head、2 个 KV head，$N=16384$，$d=128$，K/V 使用 BF16，则单层缓存的有效数据量为

$$
2 \times 16384 \times 2 \times 128 \times 2\ \text{bytes} = 16\ \text{MiB}
$$

五个因子依次是：K/V 两份数据、位置数 $N$、KV head 数、向量维度 $d$、每个元素的字节数。[【跳转到 04:33】](https://www.bilibili.com/video/BV13Fa667Epd/?t=273)

一边是 16 MiB 要读，另一边是 $1\times 128$ 的一行 query——这个对比就是 decode 的全部矛盾。课程也提醒了严谨性：实际 HBM 流量还受缓存命中和内核复用方式影响，不能直接把 16 MiB 当作实测读取量。[【跳转到 04:58】](https://www.bilibili.com/video/BV13Fa667Epd/?t=298)

## 二、任务数不够时，GPU 到底闲在哪

GPU 的调度单位是线程块（block），线程块被分配到 SM（Streaming Multiprocessor，流多处理器）上执行。一张卡有多少 SM 是固定的，比如几十到一百多个；**能同时开工的线程块数量，直接由「有多少个互不依赖的任务」决定**。

decode 的处境是：

- 任务数 ≈ 并发请求数 × KV head 数（再乘上内核自己做的少量切分）；
- 每个任务要沿整条历史 KV 循环一遍，读 16 MiB 级别的数据；
- 如果任务数少于 SM 数，多出来的 SM 就无事可做，只能等那几个线程块慢慢跑完。

课程对这一步的描述是：如果只有少数线程块沿着历史循环，**增加历史长度只会让这些任务执行得更久，其他 SM 未必能参与**。[【跳转到 05:23】](https://www.bilibili.com/video/BV13Fa667Epd/?t=323)

![Decode 瓶颈的定义：读取很多、任务很少；少数线程块沿历史循环，其他 SM 空闲](assets/Decode%20只有一行%20Query：并行度塌缩与三条出路/00000.webp)

这里还有一个很关键的判断，课程专门点了出来：**任务不足时，增加并行度可能提高实际带宽利用；带宽已经饱和时，继续拆任务不会减少必要的数据读取**。也就是说，「并行度不够」是一个有前提的诊断——只有当 SM 闲着、带宽没打满时，拆任务才有意义。另外，这一课讨论的只是单层 attention 的这条路径，整轮 decode 还包括模型权重读取、线性层等工作，端到端瓶颈未必在这里。[【跳转到 05:35】](https://www.bilibili.com/video/BV13Fa667Epd/?t=335)

## 三、三条出路各自解决什么

课程把优化分成三个层面，这个划分本身就是最值得记住的框架：

| 优化 | 一句话职责 | 回答的问题 |
| --- | --- | --- |
| GQA | 多个 query head 共享同一个 KV head | 保存**哪些**数据 |
| Paged KV | 用页表把逻辑页映射到物理页 | 数据**在哪里** |
| Split-KV | 沿 KV 序列位置把任务拆开 | 有**多少个**任务 |

课程的原话是：共享解决的是保存哪些数据，分页解决的是数据在哪里，而 Split-KV 解决的是有多少个任务。[【跳转到 09:44】](https://www.bilibili.com/video/BV13Fa667Epd/?t=584)

### 3.1 GQA：减少要保存的 KV head

GQA（Grouped-Query Attention，分组查询注意力）让多个 query head 共用同一个 KV head。课程的小例子是 4 个 query head、2 个 KV head：

| Query head | 读取的 KV head | 各自产生的输出 |
| --- | --- | --- |
| 0、1 | 0 | $O_0, O_1$ |
| 2、3 | 1 | $O_2, O_3$ |

![GQA 的分组关系：query head 0、1 共享 KV head 0，2、3 共享 KV head 1，KV 数据量减半](assets/Decode%20只有一行%20Query：并行度塌缩与三条出路/00382.webp)

同样序列长度、向量维度和精度下，这个例子只需保存 2 个 KV head，而不是普通多头注意力中与 4 个 query head 对应的 4 个 KV head，KV 数据量直接减半。[【跳转到 06:47】](https://www.bilibili.com/video/BV13Fa667Epd/?t=407) 如果只有一个 KV head、所有 query head 都共享它，这种极端情形叫 MQA（Multi-Query Attention，多查询注意力）。

有两点必须说清楚，否则容易误解 GQA 的作用：

- **KV head 数是模型结构的一部分**。vLLM 只是按模型已有的分组关系读取和复用 K/V，不会在运行时把普通多头注意力改成 GQA。所以这是「训练时就决定好的省显存手段」，不是推理框架能现场加的优化。
- **共享 K/V 不等于计算量按同比例减少**。同一个 token 的两个 query head 即使读取相同的 K/V，也分别计算自己的分数、概率和输出；内核能否减少重复加载，取决于这些 head 是否一起计算、如何复用已读到的数据。

GQA 对并行度的影响是间接的：KV Cache 变小，显存压力下降，才有可能把 batch 开大；而 batch 正是 decode 阶段剩下的主要并行维度。

### 3.2 Paged KV：逻辑上连续，物理上按页存放

Paged KV 把 KV Cache 切成固定大小的页，用页表记录逻辑页到物理页的映射。请求增长时逐页分配空间，不必为每个请求预留一整段最大长度的连续缓存。[【跳转到 07:24】](https://www.bilibili.com/video/BV13Fa667Epd/?t=444)

定位一个 token 的 K/V 只要两步：先由位置算出逻辑页号，再查页表拿物理页号，最后在页内取偏移。

$$
\text{logical page} = \left\lfloor \frac{t}{P} \right\rfloor,\qquad \text{offset} = t \bmod P
$$

其中 $P$ 是每页能放的位置数。课程的小例子是每页 2 个位置、页表为 $[3,1,6,4]$：要读位置 5，先算 $5 \div 2 = 2$ 得到逻辑页 2，查页表得到物理页 6，再对页大小求余 $5 \bmod 2 = 1$ 得到页内偏移，于是定位到物理页 6 的第 1 个槽位。[【跳转到 09:19】](https://www.bilibili.com/video/BV13Fa667Epd/?t=559)

![Paged KV 的页表机制：逻辑页连续、物理页可以不连续，按页逐块分配](assets/Decode%20只有一行%20Query：并行度塌缩与三条出路/00492.webp)

同样要划清边界：**分页本身不减少这个请求有效的 K/V 数值，也不减少 attention 需要访问的逻辑位置**。它省的是显存碎片和预留浪费，换来的是「同样的显存能装下更多请求」，从而间接把 batch 做大。真正减少读取量的是 GQA 那一层。

### 3.3 Split-KV：把长历史交给多个任务

共享和分页解决了「保存哪些数据」和「数据在哪里」，但**还没有决定由多少任务来处理这些数据**。在讲切分之前，课程先说明了默认的任务组织方式：同组 query head 由一个任务一起计算。对那个 8 个位置的小例子，不分段时只有 2 个任务，每个任务沿全部 8 个位置计算；同组的两个 query head 是两行独立计算，并不共享 softmax 结果。所选 vLLM Triton 内核的「query 行与 head 映射」就采用了这种分组方式——这是内核的任务安排，不是 GQA 规定的唯一实现。[【跳转到 10:34】](https://www.bilibili.com/video/BV13Fa667Epd/?t=634)

Split-KV 的做法是：沿 Key/Value 的**序列位置**拆分任务。FlashAttention 原本的分块是「一个任务逐块更新同一份 online softmax 状态」；Split-KV 把不同历史段交给**独立任务**，各自维护状态，结束后再归并。[【跳转到 10:09】](https://www.bilibili.com/video/BV13Fa667Epd/?t=609)

![Split-KV 的任务表：2 个 KV head × 2 段 = 4 个分段任务，每个任务负责一段位置范围并读取对应物理页](assets/Decode%20只有一行%20Query：并行度塌缩与三条出路/00634.webp)

把位置 0-7 分成 A、B 两段后，任务表是这样的：

| 任务 | 使用的 Query head | 使用的 KV head | 负责的位置 | 读取的物理页 |
| --- | --- | --- | --- | --- |
| 第 0 组 A 段 | 0、1 | 0 | 0-3 | 3、1 |
| 第 0 组 B 段 | 0、1 | 0 | 4-7 | 6、4 |
| 第 1 组 A 段 | 2、3 | 1 | 0-3 | 3、1 |
| 第 1 组 B 段 | 2、3 | 1 | 4-7 | 6、4 |

于是有 2 个 KV head × 2 段 = 4 个分段任务。要注意几个细节：

- 同一物理页里包含不同 KV head 的数据，两组任务各自选择自己 head 的切片；
- 每个任务读取**完整**的 Query，K/V 向量也保留**全部**特征；
- 切开的是**位置范围**，不是向量宽度。

这三点合起来说明：Split-KV 不是把工作变轻，而是把「一条长循环」摊成「多条短循环」，让它们能独立调度到不同 SM 上。[【跳转到 11:24】](https://www.bilibili.com/video/BV13Fa667Epd/?t=684)

课程也给了诚实的限定：这些任务可以独立调度到不同 SM，但**不保证同时运行，也不保证任务越多越快**；8 个位置的小例子只用来展示分工。[【跳转到 11:49】](https://www.bilibili.com/video/BV13Fa667Epd/?t=709)

## 四、一个串起三步的小例子

课程用一个 $d=2$、4 个 query head、2 个 KV head 的例子，把 GQA、Paged KV、Split-KV 三步串起来。$q_0 = [\sqrt{2}, 0]$，$q_0$ 与 $q_1$ 读 KV head 0，$q_2$ 与 $q_3$ 读 KV head 1；$q_0$ 再被拆成 task A（位置 0-3）与 task B（位置 4-7）。[【跳转到 11:59】](https://www.bilibili.com/video/BV13Fa667Epd/?t=719)

![三步串起来的算例：GQA 分组 → Split-KV 按位置分段 → Paged KV 查物理页 → 各段算局部结果再合并](assets/Decode%20只有一行%20Query：并行度塌缩与三条出路/00819.webp)

接下来每一步都能对上：

1. **切分**：位置 0-3 归 task A（逻辑页 L0、L1），位置 4-7 归 task B（L2、L3）；
2. **查页表**：L0→P3、L1→P1、L2→P6、L3→P4，物理页可以不连续；
3. **算分数**：$q_0$ 与某个 K 做点积再除以 $\sqrt{2}$ 做缩放（因为向量维度是 2）；
4. **取指数、乘 V**：得到各段未归一化的加权和；
5. **归并**：把两段的分子相加，分母（指数和）也相加，再做一次除法得到最终输出。

课程在归并这一步只讲到这里：两段各自的分子加起来、指数加起来作为分母，就得到结果。[【跳转到 15:44】](https://www.bilibili.com/video/BV13Fa667Epd/?t=944) 同时它提醒，真实算子里要减去最大值做数值修正，只是这个纯数学例子不需要。[【跳转到 16:09】](https://www.bilibili.com/video/BV13Fa667Epd/?t=969) 归约的严格推导（log-sum-exp 与对角化）属于 FlashDecoding 的正文内容，这里先记住结论：**并行度是用一次额外的归约换来的**。

## 五、vLLM 里怎么落地

以 vLLM v0.25.1 的普通 Triton Attention 后端为例，BF16、标准因果 decode 的执行分三步：[【跳转到 17:19】](https://www.bilibili.com/video/BV13Fa667Epd/?t=1039)

![vLLM 的分段与归并三步：选择分段路径、各段独立计算并写出状态、归并成完整输出](assets/Decode%20只有一行%20Query：并行度塌缩与三条出路/01039.webp)

1. **选择分段路径**：`unified_attention()` 根据 query 长度、请求数和工作区等条件决定是否拆分。启用后，任务坐标从 `(query_block, kv_head)` 增加为 `(query_block, kv_head, segment)`，不同任务处理不同历史段。
2. **各段独立计算并写出状态**：每段通过页表读取 K/V，逐 tile 更新 online softmax，最后写出**局部最大值、指数和、未归一化的 Value 加权和**。这些状态使用各段自己的最大值作为指数基准。
3. **归并成完整输出**：随后的 `reduce_segments()` 先统一各段的指数基准，再分别合并分子、分母，执行最终除法。每个 query head 得到自己的输出。

分段与归并内核在同一个 CUDA stream 中依次执行，保证归并时各段结果已经写完。[【跳转到 17:44】](https://www.bilibili.com/video/BV13Fa667Epd/?t=1064) 这也解释了为什么归约不能省：各段用的是**各自的**最大值做指数基准，不先统一基准就直接相加，结果会错。

## 六、收益、代价与适用条件

![Split-KV 的收益与代价：更多 SM 参与、不减少 KV 读取量；代价是额外的分段状态与归并内核](assets/Decode%20只有一行%20Query：并行度塌缩与三条出路/01089.webp)

课程把账算得很清楚：[【跳转到 18:09】](https://www.bilibili.com/video/BV13Fa667Epd/?t=1089)

- **收益**：把少数长任务拆成更多可并行的任务，让更多 SM 参与计算，提高任务不足时的带宽利用率。它**不减少** attention 必须读取的 KV 数据量。
- **代价**：需要额外保存、写入和读取分段状态，并启动归并内核；各段还会重复读取 Query。
- **适用条件**：长历史、小并发、原有任务少时更容易获益；历史短、并行任务已经足够或 HBM 带宽已饱和时，继续拆分可能无益，甚至变慢。

判断是否真的加速，要比较**分段计算与归并的总耗时**，不能只看分段计算变快了多少。[【跳转到 19:04】](https://www.bilibili.com/video/BV13Fa667Epd/?t=1144)

课程结尾回到方法论：算 attention 是非常灵活的，没有一定之规。decode 的瓶颈如果是长的 KV Cache，切分 KV 可能是好选择；prefill 的瓶颈不同，切分 query 反而是好选择——具体问题具体分析。[【跳转到 19:27】](https://www.bilibili.com/video/BV13Fa667Epd/?t=1167)

## 小结

- decode 的计算公式没变，变的是规模：$Q \in \mathbb{R}^{1\times d}$、$K,V \in \mathbb{R}^{N\times d}$，分数从 $N\times N$ 退化成 $1\times N$。
- FlashAttention 的可并行维度是 batch、query 序列、head；decode 把 query 序列维度抹掉，只剩「请求数 × head 数」。
- 一个请求 8 个 query head、2 个 KV head、$N=16384$、$d=128$、BF16 时，单层 KV Cache 是 16 MiB，而 query 只有 $1\times 128$——读取很多、任务很少。
- 任务数少于 SM 数时，多出来的 SM 只能空等；增加历史长度只会让少数线程块跑得更久。
- 三条出路分工明确：GQA 决定保存哪些 KV（KV 数据减半），Paged KV 决定数据在哪里（不减少读取量，但省显存、利于做大 batch），Split-KV 决定有多少个任务（直接补并行度）。
- Split-KV 切开的是位置范围而不是向量宽度，每个任务仍读完整 Query 与完整 K/V 特征；并行度是用一次段间归约换来的。
- 判断是否值得拆分要看总耗时（分段 + 归并），并且只在「任务不足、带宽未饱和」时才有收益。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| Prefill | 一次性处理整段输入 prompt 的阶段，query 有很多行，GPU 容易跑满 |
| Decode | 逐 token 生成的阶段，每步只输入一个 token，query 只有一行 |
| SM（Streaming Multiprocessor） | GPU 上执行线程块的单元，数量固定，任务数少于它就会有 SM 空闲 |
| KV Cache | 缓存历史 token 的 K/V，避免每步重算；decode 时读取量的主要来源 |
| GQA（分组查询注意力） | 多个 query head 共享一个 KV head，KV 数据量按分组比例下降 |
| MQA（多查询注意力） | GQA 的极端情形：所有 query head 共享唯一的 KV head |
| Paged KV | 把 KV Cache 按固定大小的页管理，用页表做逻辑页到物理页的映射 |
| Split-KV | 沿 K/V 的序列位置把任务拆开，各段独立算局部结果再归约 |
| Online Softmax | 分块计算时逐块更新最大值与指数和的技巧，使结果与整块计算等价 |
| log-sum-exp | 把各段的局部指数和合并成全局归一化因子的数学工具 |