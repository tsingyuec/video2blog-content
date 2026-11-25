# MoE 专家并行：all-to-all 的 dispatch 与 combine 如何搬动 token

> 视频来源：[全面解析 LLM MoE 专家并行 EP all-to-all 算子（小白也能看懂）](https://www.bilibili.com/video/BV1W314BfEHr/)（Bilibili · UP 主「不归牛顿管的熊猫」）｜时长约 21 分钟
> 导读：UP 主用一份 PyTorch 伪代码，把 MoE 专家并行里最贵的那一步——all-to-all——从「为什么需要」讲到「每一行怎么写」：先算发送/接收计数，再拼连续缓冲区，最后按门控权重加权聚合。本文按这条代码链路整理，并补上他提到的三个坑（缓冲区爆掉、通信 hang、FP16 累加误差）。字幕中的口误（`auto all`、`EEP`、`wordsize`、`command` 等）已按上下文订正为 all-to-all、EP、world size、combine。

## 本讲要解决的核心问题（SCQA）

**背景**：MoE（Mixture of Experts，混合专家）把 Transformer 里那个又宽又大的 FFN 拆成若干个结构相同、参数不同的「专家」，每个 token 只走其中 top-k 个。这样一来，模型的**总参数量**可以远远大于**单 token 激活的参数量**。

**冲突**：参数量堆上去之后，一个很朴素的问题立刻出现——**一张 GPU 装不下所有专家了**。哪怕每个 token 只激活两个专家，那没被激活的几十上百个专家，权重也必须老老实实待在显存里，因为下一个 token 可能就选中它们。于是必须把专家分散到多张卡上。

**疑问**：专家分散之后，一个 token 怎么跑到「持有它选中的专家」的那张卡上去算，算完又怎么回来？这一步要花多少代价？

**回答（中心思想）**：MoE 的专家并行（EP，Expert Parallelism）靠一次 **all-to-all** 通信完成「发出去—算一遍—收回来」：先把 token 按目标专家所在的设备**洗牌发出去**（dispatch），本地专家算完，再把结果**发回原来的设备并按门控权重加权求和**（combine）。代价是：**MoE 的稀疏只省了计算，一点也没省显存**；显存不够就得靠 EP 摊开，而 EP 一摊开，all-to-all 的通信就成了新的固定成本。[【跳转到 01:07】](https://www.bilibili.com/video/BV1W314BfEHr/?t=67)

---

## 一、稀疏激活省的是算力，不是显存

### 1.1 为什么非要 EP 不可

UP 主把背景拆成三块，第一块是 MoE 的概念，他只用了两句话带过：把 FFN/MLP 拆成多个独立的专家，每个输入 token 由 top-k 个专家处理，再由门控网络聚合结果。[【跳转到 01:22】](https://www.bilibili.com/video/BV1W314BfEHr/?t=82)

第二块才是重点：**为什么 MoE 需要 EP**。他的原话是「专家数量非常多的时候，很明显我们在单卡上就无法再装下所有专家了」。设总专家数为 $N$、设备数为 $W$，那么

$$
\text{每张卡上的专家数} = \frac{N}{W}
$$

这就是 EP 的动机——不是为了算得快，而是为了**装得下**。[【跳转到 01:07】](https://www.bilibili.com/video/BV1W314BfEHr/?t=67)

![背景页：MoE 把 FFN 拆成多个专家、每卡只保存「专家数除以 world size」个专家，all-to-all 分为 dispatch 与 combine 两步](assets/MoE%20专家并行：all-to-all%20的%20dispatch%20与%20combine%20如何搬动%20token/00182.webp)

这里藏着一个初学者最容易误会的点，值得单独说清：MoE 常被宣传成「671B 参数的模型只要 37B 的算力」，这说的是**算力**。显存是另一回事——路由是逐 token 动态决定的，你无法预知下一个 token 会用到哪个专家，所以**所有专家的权重都必须常驻显存**。稀疏激活省下的是 FLOPs，省不下权重占的那几百 GB。这正是 MoE 推理最特殊的地方：它同时拥有「稠密模型级别的显存占用」和「稀疏模型级别的计算量」。

### 1.2 all-to-all 的两个半程：dispatch 与 combine

既然专家分散在不同卡上，token 就得「走过去」。UP 主把整个过程概括成三步：

1. **dispatch**：把所有 token 高效地分发到「选中专家所在的设备」，重点在**分发**；
2. **MoE function**：每张卡上的专家对收到的 token 做一次小 MLP；
3. **combine**：把专家的输出结果回传到 token 原始所在的设备，并聚合结果，重点在**回传**。

dispatch 和 combine 是一对**互逆**的操作。[【跳转到 01:57】](https://www.bilibili.com/video/BV1W314BfEHr/?t=117)

![all-to-all 的三个阶段：dispatch 把 token 洗牌发到目标 rank，MoE function 在本地算，combine 把结果发回原 rank](assets/MoE%20专家并行：all-to-all%20的%20dispatch%20与%20combine%20如何搬动%20token/00237.webp)

### 1.3 用四个 rank、十六个 token 走一遍

UP 主画了一张图，用四个 rank（四张 GPU）、每张四个 token 来演示。原始状态是 A、B、C、D 四组 token 各就各位：

- 经过 dispatch 相当于**洗一次牌**：A0 被发到 rank1，于是 rank1 上可能是 A0、A1、B1、C1、D1 五个 token；如果 rank1 上还有 token 要发去 rank3（比如 D1），那 rank1 上就剩 A0、A1、B1、C1，而 rank3 上变成 A3、B3、C3、D3、D1。[【跳转到 02:37】](https://www.bilibili.com/video/BV1W314BfEHr/?t=157)
- 每个 rank 上，本地专家对收到的 token 做一次小 MLP。
- 经过 combine，token 又回到它原来的 rank，只是内容换成了「专家算过的版本」——UP 主把它记作 A0 新、B0 新、C0 新、D0 新。

他的总结很到位：「通过这三个阶段一折腾，它无非就是在所有 rank 上的所有 token 去做它对应的专家计算，无非就做这样一件事情，只不过中间涉及到一些发送过去又收回来的操作。」[【跳转到 03:37】](https://www.bilibili.com/video/BV1W314BfEHr/?t=217)

所以 all-to-all 的技术难点不在数学，而在于：**怎么发过去、怎么收回来**。

---

## 二、dispatch：先算账，再打包，最后交换

### 2.1 需要哪些参数

UP 主用 PyTorch 写了一份可读的实现。类 `AllToAll` 的初始化里，几个量先摆清楚：[【跳转到 06:17】](https://www.bilibili.com/video/BV1W314BfEHr/?t=377)

| 参数 | 含义 |
| --- | --- |
| `rank` | 当前设备编号 |
| `world_size` | 总设备数（有多少张卡） |
| `num_local_experts` | 每张卡上的专家数，等于总专家数除以卡数 |
| `max_recv` | 每个 rank 最多能接收的 token 数，等于 `max_num_tokens × world_size` |

`max_recv` 是**留了余量**的上界：不可能每个 rank 都收满，但确实可能出现「rank3 把 rank0 到 rank2 的 12 个 token 全收过来」这种极端情况，所以缓冲区必须按最坏情况开。[【跳转到 06:42】](https://www.bilibili.com/video/BV1W314BfEHr/?t=402)

还有一行非常关键：`meta = 4`，即每个 token 要带四个字段的元数据——`global_expert`、`src_rank`、`src_token`、`src_k`。UP 主把它们比作 token 的**户口**：「我只有知道它来自于哪个 rank，才知道把它发到哪个 rank 上去。有了这些户口之后，我们 combine 的时候才知道把它发到哪里去。」[【跳转到 07:32】](https://www.bilibili.com/video/BV1W314BfEHr/?t=452)

![AllToAll 类的初始化：rank、world_size、每卡专家数、最大接收量，以及 meta=4 的元数据维度](assets/MoE%20专家并行：all-to-all%20的%20dispatch%20与%20combine%20如何搬动%20token/00452.webp)

### 2.2 步骤一：算出发送计数与接收计数

dispatch 的第一件事不是搬数据，而是**数数**：我这张卡要往每张卡发多少个 token？我又要从每张卡收多少个？[【跳转到 08:22】](https://www.bilibili.com/video/BV1W314BfEHr/?t=502)

发送计数来自路由结果。代码遍历 `indices`（每个 token 选中的专家列表），对每个专家 $e$ 算出它所在的设备：

$$
\text{dst\_rank} = \left\lfloor \frac{e}{\text{num\_local\_experts}} \right\rfloor
$$

然后 `send_counts[dst_rank] += 1`，同时把 token 索引记进 `token_map[dst_rank]`。[【跳转到 09:12】](https://www.bilibili.com/video/BV1W314BfEHr/?t=552)

接收计数则靠一次**极小的 all-to-all** 换来：把 `send_counts` 这个长度等于 world size 的向量做一次 `torch.distributed.all_to_all_single`，得到的就是 `recv_counts`。[【跳转到 10:13】](https://www.bilibili.com/video/BV1W314BfEHr/?t=613)

UP 主特别强调这两个变量的语义差别，因为这是最容易讲错的地方：

- `send_counts` 里记的是「**我要发给**目标 rank 多少个 token」；
- `recv_counts` 里记的是「**我当前这个 rank 要接收**多少个 token」。

交换之后，两个视角发生了一次「对称」，而「对称」在通信里是一个非常重要的概念。[【跳转到 11:28】](https://www.bilibili.com/video/BV1W314BfEHr/?t=688)

![dispatch 步骤一：遍历路由结果统计 send_counts，再用 all_to_all_single 交换计数得到 recv_counts](assets/MoE%20专家并行：all-to-all%20的%20dispatch%20与%20combine%20如何搬动%20token/00502.webp)

### 2.3 步骤二：把要发的 token 拼成连续缓冲区

知道要发哪些 token 之后，不能一个个发。UP 主解释得很直白：假设我要发的是第 0 个和第 2 个 token，它们在显存里**不挨着**，中间隔了一个 token 1。所以要用 `torch.cat` 把它们拼成一个连续的 `send_buf`，元数据同样拼成 `send_meta`。[【跳转到 12:11】](https://www.bilibili.com/video/BV1W314BfEHr/?t=731)

这是 GPU 通信的基本功：**一次大传输远比多次小传输便宜**。零散的小块会在带宽和启动开销上双重吃亏——这一点在 MoE 推理里被放大得很厉害，因为每个 token 选中的专家组合都不一样，天然就是「碎片化」的访问模式。

![dispatch 步骤二：用 torch.cat 把要发送的 token 和元数据拼成连续缓冲区](assets/MoE%20专家并行：all-to-all%20的%20dispatch%20与%20combine%20如何搬动%20token/00731.webp)

### 2.4 步骤三：真正做数据交换

有了 `send_buf` / `send_meta`，就可以调用 `dist.all_to_all_single`。这里要传两组 split sizes：`input_split_sizes` 是「我要给每个目标设备发多少」，`output_split_sizes` 是「我要从每个源设备收多少」。元数据那一路还要再乘上 `META_DIM`，因为每个 token 带 4 个整数。[【跳转到 13:41】](https://www.bilibili.com/video/BV1W314BfEHr/?t=821)

每个 rank 都要准备两份缓冲区：一份是「我要发的」，一份是「我要接收的」。交换完成后，`recv_buf` 里就是别的卡发过来的 token。

![dispatch 步骤三：用 all_to_all_single 交换 token 数据与元数据，input_split_sizes 与 output_split_sizes 分别描述发送与接收的分段](assets/MoE%20专家并行：all-to-all%20的%20dispatch%20与%20combine%20如何搬动%20token/00821.webp)

### 2.5 后处理：整理成「按专家分组」的形状

收到 token 之后还不能直接算，因为 `recv_buf` 是按**来源 rank** 排的，而专家需要的是按**专家**排的。所以还要做一步后处理：把收到的 token 拿出来，单独存进一个 `expert_token` 缓冲区，同时统计**每个专家手上有多少个 token**。[【跳转到 14:31】](https://www.bilibili.com/video/BV1W314BfEHr/?t=871)

这一步就是 MoE 推理里那个著名操作的入口——把「散落在很多 token 上的、指向同一个专家的行」聚成一个矩阵，才能喂给 GPU 的矩阵乘法单元。UP 主在视频里只说了「送到每个专家上面去斗地主」，但这一步恰恰是后面「访存碎片化」问题的根源：**token 到专家的映射是稀疏且不规则的，聚合本身就要额外的搬运**。

---

## 三、combine：把结果发回去，再按权重加起来

### 3.1 步骤一：统计回传计数

combine 是 dispatch 的镜像。第一步同样是数数，只是这次数的是「专家的输出要回到哪些设备」。代码遍历本地每个专家、每个它处理过的 token，从元数据里读出 `src_rank`（原始 token 所在设备），累加 `send_counts[dst_rank]`。[【跳转到 15:01】](https://www.bilibili.com/video/BV1W314BfEHr/?t=901)

注意这里的 `send_counts` 和 dispatch 阶段的 `send_counts` 是**同名不同义**的：dispatch 时它记的是「token 要去的设备」，combine 时它记的是「专家输出要回的设备」。名字一样，方向相反。

![combine 步骤一：遍历本地专家的输出，按元数据里的 src_rank 统计回传计数](assets/MoE%20专家并行：all-to-all%20的%20dispatch%20与%20combine%20如何搬动%20token/00901.webp)

### 3.2 步骤二：再发一次 all-to-all

回传同样是「拼连续缓冲区 + `all_to_all_single`」的套路，和 dispatch 一模一样，只是方向反过来。UP 主的评价是「传就完事了」。[【跳转到 15:51】](https://www.bilibili.com/video/BV1W314BfEHr/?t=951)

### 3.3 步骤三：按门控权重加权聚合

数据回到原 rank 之后，最后一步是聚合。因为一个 token 可能被 top-k 个专家算过，每个专家的输出都要乘上它自己的门控权重再加起来：

$$
\text{out}[t] = \sum_{k \in \text{top-}k(t)} w_{t,k} \cdot \text{Expert}_{e(t,k)}(x_t)
$$

代码里就是一行 `out_tokens[src_token] += recv_buf[i] * w`，其中 `w` 从 `weights[src_token, src_k]` 取，`src_k` 记录的正是「这个 token 选中的第 k 个专家」。[【跳转到 16:41】](https://www.bilibili.com/video/BV1W314BfEHr/?t=1001)

![combine 步骤三：按元数据找回原始 token，用门控权重加权累加，得到最终输出](assets/MoE%20专家并行：all-to-all%20的%20dispatch%20与%20combine%20如何搬动%20token/01001.webp)

至此，token 回到了原始 rank，内容变成了「经过 top-k 专家加权」的版本。UP 主的说法是「happy ending 大结局」。[【跳转到 16:41】](https://www.bilibili.com/video/BV1W314BfEHr/?t=1001)

---

## 四、三个真实的坑：缓冲区爆掉、通信 hang、精度掉点

流程看着很顺，但 UP 主特意留了一页讲踩过的坑，这一页比前面所有代码都更接近生产环境。[【跳转到 18:46】](https://www.bilibili.com/video/BV1W314BfEHr/?t=1126)

![常见的坑：专家负载不均衡导致 max_recv 缓冲区爆掉、通信 hang、FP16 all-to-all 累加误差](assets/MoE%20专家并行：all-to-all%20的%20dispatch%20与%20combine%20如何搬动%20token/01126.webp)

### 4.1 专家负载不均衡：一张卡爆掉，全组陪跑

这是 MoE 推理最经典的性能杀手。某些专家天生「受欢迎」——比如负责通用语义理解的那些——于是选中它们的 token 特别多。如果这些专家恰好都落在同一张卡上，那张卡的 `recv_buf` 就可能**爆掉 `max_recv` 缓冲区**；而别的卡上没几个 token，闲着。[【跳转到 17:06】](https://www.bilibili.com/video/BV1W314BfEHr/?t=1026)

后果不是「慢一点」，而是**整个 MoE 层的耗时被最慢的那张卡决定**：所有卡都得等它做完 dispatch、MoE 计算和 combine。UP 主的说法是「性能完全被爆掉 max_recv 缓冲区的那个 rank 给拖累」。[【跳转到 17:31】](https://www.bilibili.com/video/BV1W314BfEHr/?t=1051)

这也解释了为什么工程上要做**负载均衡**：把热门专家和冷门专家重新摆一摆，让每张卡的 token 数接近，才能让所有卡同时开工。反过来，如果负载是均衡的，「每张卡可能都能够同时做完 dispatch、MoE 计算以及 combine，这就是完美的大结局」。

### 4.2 通信 hang：最难查的一类 bug

第二类问题更折磨人：all-to-all 卡住不返回。UP 主列了一串可能的原因——MPI 配置、资源管理、无缘无故的僵尸进程、进程组有没有正确销毁……「非常难找，这里也不太能够说清楚」。[【跳转到 18:21】](https://www.bilibili.com/video/BV1W314BfEHr/?t=1101)

对写 MoE 推理服务的人来说，这条经验很值钱：**all-to-all 是集合通信，任何一个 rank 掉队，整组都会挂住**。所以超时、健康检查、进程清理这些「运维活儿」，在 EP 场景里不是可选项。

### 4.3 精度掉点：FP16 累加会掉精度

第三个坑很隐蔽。combine 阶段要做加权累加，如果权重聚合用 FP16，累加误差会累积；换成 FP32 就基本没有这个问题。[【跳转到 18:46】](https://www.bilibili.com/video/BV1W314BfEHr/?t=1126)

UP 主给的推荐做法很具体：**在 `out_tokens += recv_buf * w` 这一步用 FP32 累加，最后再强制转回 FP16**。这样既保住了数值稳定性，又不影响后续 kernel 的输入格式。

---

## 五、把这一步放回 MoE 推理的整体账本

UP 主在结尾说，他讲这些是因为面试里很多人「只知道 EP 里 all-to-all 很重要，但不知道它的原理和实现过程」。而理解实现过程之后，MoE 推理的几个结构性结论就自然浮出来了：

1. **显存容量是第一道墙**。总参数量必须全部驻留，稀疏激活省的是算力不是显存；单卡装不下就只能 EP，把专家摊到多张卡上，每卡只留 $N/W$ 个专家。
2. **EP 的代价是 all-to-all**。dispatch 和 combine 各一次，每层都要做，40 层就是 80 次；这些通信不在 FLOPs 账本里，却实实在在占时间。
3. **碎片化放大通信成本**。每个 token 选中的专家组合都不同，导致发送目标天然零散；所以实现里必须「拼连续缓冲区」，而负载不均衡又会让某一张卡的缓冲区爆掉、拖慢整组。
4. **瓶颈因此从算力转向带宽与通信**。当一个 token 只激活少数专家时，GPU 的矩阵单元大部分时间是闲的，真正忙的是显存读取和卡间搬运。

这也正是 MoE 推理和稠密模型推理最大的不同：稠密模型的瓶颈是「把权重读一遍」，MoE 的瓶颈是「把权重读一遍 **并且** 把 token 搬来搬去」。前者只能靠更高的显存带宽或更低的精度去缓解，后者还可以靠更好的并行布局、更好的负载均衡、更少的通信轮次去优化。

---

## 小结

- MoE 的稀疏激活**只省算力，不省显存**：路由是逐 token 动态的，所有专家权重必须常驻。单卡装不下，就必须上 EP。
- EP 把 $N$ 个专家摊到 $W$ 张卡上，每卡只存 $N/W$ 个；代价是每层两次 all-to-all。
- all-to-all 分两半：**dispatch** 把 token 发到目标专家所在设备，**combine** 把专家输出发回原设备并聚合。两者互逆。
- 实现套路固定：算发送/接收计数 → 用 `all_to_all_single` 交换计数 → 拼连续缓冲区 → 交换数据 → 后处理成按专家分组的形状。
- 元数据（`global_expert`、`src_rank`、`src_token`、`src_k`）是 token 的「户口」，没有它 combine 就找不回原主。
- 三个坑：负载不均衡让 `max_recv` 缓冲区爆掉并拖慢全组；通信 hang 极难排查；FP16 加权累加会掉精度，应 FP32 累加后转回 FP16。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| EP（Expert Parallelism） | 专家并行：把不同专家放到不同 GPU 上，每卡只保存总专家数除以卡数的那一份 |
| all-to-all | 集合通信原语：每个 rank 都向所有其他 rank 发送一份不同的数据，同时从所有 rank 接收 |
| dispatch | all-to-all 的前半程，把 token 按「选中专家所在设备」分发出去 |
| combine | all-to-all 的后半程，把专家输出回传到原设备并按门控权重聚合 |
| `send_counts` / `recv_counts` | 当前设备要发/要收的 token 数，靠一次小 all-to-all 从「发送视角」翻成「接收视角」 |
| `max_recv` | 单卡最多能接收的 token 数上界，负载不均衡时会被打爆 |
| 元数据（meta） | 每个 token 随身携带的四个字段：全局专家号、源 rank、源 token 索引、第 k 个专家 |
| 负载均衡 | 把热门专家与冷门专家重新摆放，避免某张卡爆缓冲区、拉长整层耗时 |