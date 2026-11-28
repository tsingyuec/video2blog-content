# 用 Request、Sector、Wavefront 诊断访存瓶颈

> 视频来源：[Nsight Compute 内存分析详解：Request、Sector、Wavefront](https://www.bilibili.com/video/BV1YQ836wEGt/)（Bilibili · UP 主 noinfra）｜时长约 12.5 分钟
> 导读：本文不复述 Nsight Compute 怎么打开、面板在哪，而是把 Memory Workload Analysis 里最容易被跳过的三个计数单位（request / wavefront / sector）拆开，用六个真实实验说明「什么样的数字算浪费」，最后给出一张「指标 → 判断 → 处方」的对照表。

## 本讲要解决的核心问题（SCQA）

**背景**：你已经会用 Nsight Compute 采集 kernel 的指标，也知道 Memory Workload Analysis 面板里有 `Requests`、`Wavefronts`、`Sectors`、`Bank Conflicts` 这几列。

**冲突**：这些数字单独看都"有值"，但到底多少算正常？`Sectors/Req = 32` 是好还是坏？`Wavefronts` 比 `Requests` 大八倍意味着什么？面板不会直接告诉你。

**疑问**：怎样从这三个计数单位反推出「这次访存到底浪费了多少带宽」，以及该改代码的哪一行？

**回答（中心思想）**：访存效率的本质是**一个 warp 的一次请求，究竟搬回了多少有用的字节**。理想情况是一分钱一分货：`1 request → 4 sector → 1 wavefront`（128 字节全部用上）。凡是 `Sectors/Req` 远大于 4、或 `Wavefronts` 被拆成好几份，就说明你在为「不连续」和「bank 冲突」付钱；对应的处方只有两类：让相邻线程访问相邻地址（合并访存），以及调整 shared memory 的访问步长（消除 bank 冲突）。

## 一、先分清三个计数单位：请求、波前、扇区

Nsight Compute 的内存面板之所以难读，是因为它同时用了三层计数：warp 层、搬运层、字节层。先把这三层对齐，后面的数字才有意义。

![三个计数单位的定义：一个 warp 的 32 个线程合成一个 request，一个 request 拆成多个 wavefront，一个 wavefront 搬运 1 到 4 个 32 字节的 sector](assets/用%20Request、Sector、Wavefront%20诊断访存瓶颈/00125.webp)

- **内存请求（request）**：一个 warp 的 32 个线程一起去访存，它们合在一起生成**一个**内存请求。所以面板里的 `Requests` 数，基本等于「执行了多少次访存指令 × warp 数」。
- **波前（wavefront）**：一次请求要搬运的数据，会被硬件拆成若干个波前分批发出去。**一个 wavefront 最多搬运 4 个 sector**（128 字节），这是后面所有判断的基准。
- **扇区（sector）**：访存的**最小单位**，32 字节。哪怕你只读一个 4 字节的 `float`，硬件也要把包含它的那 32 字节整个搬进来。

三者关系可以记成一句话：**request 是"我要什么"，wavefront 是"分几趟搬"，sector 是"每趟实际搬了多少字节"**。

[【跳转到 02:30】](https://www.bilibili.com/video/BV1YQ836wEGt/?t=150)

[【跳转到 01:37】](https://www.bilibili.com/video/BV1YQ836wEGt/?t=97)

顺带把视频开头列出的指令清单放在这里，因为后面讨论的每一种访问模式，都对应清单里的一条指令：

![CUDA 中四类内存访问指令：global↔寄存器（LDG/STG）、global→shared（cp.async、TMA）、shared→寄存器（LDS、ldmatrix）、寄存器→shared（STS、stmatrix）](assets/用%20Request、Sector、Wavefront%20诊断访存瓶颈/00014.webp)

## 二、global 到寄存器：六种访问模式，六种账单

视频用同一块 GPU、同一条 `LDG` 指令，只改线程访问的地址模式，做了六组实验。这六组就是「访存诊断」的标尺。

![六种待测的访问模式：从完全连续的 128 字节，到完全不连续的一列，再到 32 个线程读同一个地址](assets/用%20Request、Sector、Wavefront%20诊断访存瓶颈/00175.webp)

### 2.1 基准线：32 个线程读 32 个连续 float

每个线程读一个 4 字节 `float`，32 个线程合起来正好 128 字节连续数据，这就是教科书里的**合并访存（coalesced access）**。

![合并访存实测：128 字节 = 4 个 sector，4 个 sector 合成 1 个 wavefront，Sectors/Req = 4](assets/用%20Request、Sector、Wavefront%20诊断访存瓶颈/00246.webp)

面板上的数字是：`Requests = 1`、`Wavefronts = 1`、`Sectors = 4`、`Sectors/Req = 4`。128 字节 ÷ 32 字节 = 4 个 sector，4 个 sector 刚好塞满一个 wavefront。**这就是"满分"的样子：一趟搬完，一个字节都不浪费。**

[【跳转到 04:06】](https://www.bilibili.com/video/BV1YQ836wEGt/?t=246)

### 2.2 唯一的特例：每个线程读 16 字节

第二种情况是每个线程读一个 `float4`（16 字节），32 个线程合起来 512 字节。

![float4 合并访存实测：512 字节 = 16 个连续 sector，仍然只用 1 个 wavefront，Sectors/Req = 16](assets/用%20Request、Sector、Wavefront%20诊断访存瓶颈/00262.webp)

面板显示 `Sectors = 16`、`Wavefronts = 1`、`Sectors/Req = 16`。注意这里**违反**了"一个 wavefront 最多 4 个 sector"的经验——因为 16 个 sector 是完全连续的，硬件可以一次性搬完。视频特别强调这是**最特殊的一种**，不要拿它当通例。

[【跳转到 04:22】](https://www.bilibili.com/video/BV1YQ836wEGt/?t=262)

### 2.3 反面教材：32 个线程读同一列

第三种情况，32 个线程各读 4 字节，但地址是矩阵的一列，彼此完全不连续。

![跨列访问实测：32 个不连续的 4 字节访问，实际搬运 32 个 sector、拆成 8 个 wavefront，Sectors/Req = 32](assets/用%20Request、Sector、Wavefront%20诊断访存瓶颈/00335.webp)

这里的推理链条值得记住：每个线程只要 4 字节，但 sector 是 32 字节，所以每个线程都要独占一个 sector；32 个线程就是 **32 个 sector**；4 个 sector 一组，于是拆成 **8 个 wavefront**。面板上 `Sectors/Req = 32`，而理想值是 4。

**判断**：`Sectors/Req` 从 4 涨到 32，意味着你为了取 128 字节的有效数据，实际搬了 32×32 = 1024 字节，**有效带宽只有 1/8**。

[【跳转到 05:35】](https://www.bilibili.com/video/BV1YQ836wEGt/?t=335)

### 2.4 部分连续：4 组 32 字节

第四种情况介于两者之间：32 个线程各读 4 字节，但分成 4 组，每组 32 字节是连续的。

![部分连续访问：4 组各 32 字节连续，刚好凑成 4 个 sector、1 个 wavefront](assets/用%20Request、Sector、Wavefront%20诊断访存瓶颈/00376.webp)

结果是 `Sectors = 4`、`Wavefronts = 1`——**和完全合并访存一样好**。视频特意指出：组与组之间有没有数据、连不连续都无所谓，只要每个 sector 被"用满"，账单就不会变差。这条结论很实用：**判断标准不是"地址连续"，而是"每个 sector 里的字节有没有被用上"**。

[【跳转到 06:16】](https://www.bilibili.com/video/BV1YQ836wEGt/?t=376)

### 2.5 半浪费：8 组 16 字节

第五种情况是 8 组、每组 16 字节连续，组间有空隙。

![8 组 16 字节连续：需要 8 个 sector、拆成 2 个 wavefront，一半带宽被浪费](assets/用%20Request、Sector、Wavefront%20诊断访存瓶颈/00428.webp)

每个线程只要 4 字节，但每组 16 字节落在同一个 sector 里，于是 8 组 = 8 个 sector，拆成 2 个 wavefront。视频的结论是：**这里有一半的内存带宽被浪费**；空隙再大一些，浪费比例还会继续上升（视频提到过 7/8 的极端情况）。

[【跳转到 07:08】](https://www.bilibili.com/video/BV1YQ836wEGt/?t=428)

### 2.6 六种模式的账单汇总

| 访问模式 | 有效字节 | Sectors | Wavefronts | Sectors/Req | 判断 |
| --- | --- | --- | --- | --- | --- |
| 32 线程 × 4B 连续 | 128 B | 4 | 1 | 4 | 理想 |
| 32 线程 × 16B 连续 | 512 B | 16 | 1 | 16 | 特例，仍理想 |
| 32 线程 × 4B 跨列 | 128 B | 32 | 8 | 32 | 严重浪费 |
| 4 组 × 32B 连续 | 128 B | 4 | 1 | 4 | 理想 |
| 8 组 × 16B 连续 | 128 B | 8 | 2 | 8 | 浪费一半 |

视频还提到第六种情况「32 个线程访问同一个数据」，这类访问由硬件广播处理，不在上面的实测截图里，判断规则也不变。

## 三、shared memory：bank 冲突会直接变成 wavefront

shared memory 没有 sector 的概念，它的最小单位是 bank（32 个 bank，每个 4 字节，合计 128 字节）。所以这一节的判断标准变成：**一次请求是不是被拆成了多个 wavefront**。

### 3.1 无冲突：1 个 request 对应 1 个 wavefront

![LDS 无 bank 冲突：32 个线程各读 4 字节、落在 32 个不同 bank 上，1 个 request 只需 1 个 wavefront](assets/用%20Request、Sector、Wavefront%20诊断访存瓶颈/00492.webp)

`LDS R0, [R7]` 这条指令，32 个线程读 32 个不同 bank，面板显示 `Requests = 1`、`Wavefronts = 1`、`Bank Conflicts = 0`。

[【跳转到 08:12】](https://www.bilibili.com/video/BV1YQ836wEGt/?t=492)

### 3.2 有冲突：一次请求被拆成两趟

如果线程访问的地址错位，导致两个线程落到同一个 bank，硬件只能串行：第一次 wavefront 搬第一行，第二次搬第二行。**一次 request 因此变成两个 wavefront**，这就是 bank 冲突在指标上的样子。

### 3.3 LDS.128：看起来有冲突，其实没有

![LDS.128 实测：一个线程搬 16 字节，共 512 字节，被拆成 4 个 wavefront，但 Bank Conflicts 仍为 0](assets/用%20Request、Sector、Wavefront%20诊断访存瓶颈/00567.webp)

这里有个容易误判的点：0 号线程和 8 号线程访问同一块 bank，看上去该冲突了，但面板显示 `Wavefronts = 4`、`Bank Conflicts = 0`。原因是这条指令本来就被拆成 4 个 wavefront，每个 wavefront 只搬 128 字节、恰好覆盖 32 个 bank，**拆开之后每一趟都不冲突**。

**判断**：`Wavefronts > Requests` 不一定是坏事，要结合指令宽度看。对 `LDS.128` 这种一次搬 16 字节的指令，4 个 wavefront 是设计使然；**真正要看的是 `Bank Conflicts` 这一列**。

[【跳转到 09:27】](https://www.bilibili.com/video/BV1YQ836wEGt/?t=567)

### 3.4 ldmatrix：给错地址，冲突会翻倍

`ldmatrix` 是 Tensor Core 时代的关键指令：传入 8 个行地址，每个地址拷 16 字节，一共 128 字节，再按固定格式分给 32 个线程。

![ldmatrix ×1 给列地址：产生 7 次 bank 冲突，128 字节被拆成 8 个 wavefront](assets/用%20Request、Sector、Wavefront%20诊断访存瓶颈/00683.webp)

给一行地址（或斜着给）时，1 个 request、1 个 wavefront 就搬完；但**给一列的地址**时，面板显示 `Wavefronts = 8`、`Bank Conflicts = 7`——一趟变八趟。

[【跳转到 11:23】](https://www.bilibili.com/video/BV1YQ836wEGt/?t=683)

![ldmatrix ×4 给行地址：4 个 wavefront、0 冲突；换成四列地址则要 32 个 wavefront、28 次冲突](assets/用%20Request、Sector、Wavefront%20诊断访存瓶颈/00749.webp)

`ldmatrix ×4` 更极端：给行地址是 4 个 wavefront、0 冲突；给四列地址，第一次搬运就有 7 次冲突，四次合起来 28 次，**要拆成 32 个 wavefront**。这就是很多手写 GEMM 在 `ldmatrix` 前后加 swizzle（把 shared memory 的列地址打散重排）的原因。

[【跳转到 12:19】](https://www.bilibili.com/video/BV1YQ836wEGt/?t=739)

## 四、把指标变成判断：一张对照表

视频最后把这些访问模式对应的指标收在一起。整理成「看到什么数字 → 说明什么 → 改哪里」的对照表，就是这一节最实用的产出：

| 你在面板上看到 | 说明什么 | 处方 |
| --- | --- | --- |
| `Sectors/Req = 4`，`Wavefronts = Requests` | 合并访存，128 字节全用上 | 不用改 |
| `Sectors/Req` 明显大于 4（如 8、32） | 相邻线程地址不连续，每个 sector 只用了一部分 | 让 `threadIdx` 对应连续地址；必要时先转置/重排数据 |
| `Wavefronts` 是 `Requests` 的数倍，且指令是 `LDG` | 一次请求被拆成多趟搬运 | 同上，优先改数据布局而不是改指令 |
| `Bank Conflicts` 大于 0（`LDS`/`STS`） | shared memory 访问步长与 bank 数不互质 | 加 padding 或 swizzle，把列访问改成行访问 |
| `Bank Conflicts` 大于 0（`ldmatrix`） | 给 `ldmatrix` 的地址是列方向 | 换行地址，或对 shared tile 做 XOR swizzle |
| `Wavefronts > Requests` 但 `Bank Conflicts = 0` | 指令本身就是宽指令（`LDS.128`、`ldmatrix ×4`） | 正常现象，不必优化 |

[【跳转到 12:29】](https://www.bilibili.com/video/BV1YQ836wEGt/?t=749)

## 五、这套方法在诊断流程里的位置

回到本小节的主题——**根据指标判断瓶颈类型**。这篇视频给的是"访存瓶颈"这一支的判断依据，可以嵌进一个固定的顺序里：

1. **先看吞吐**：如果 Memory Throughput 已经接近峰值、而 Compute 那一侧还有余量，说明瓶颈在访存侧，继续往下看。
2. **再看 `Sectors/Req`**：它回答"我搬的字节里有多少是有效的"。这个数只跟**地址模式**有关，跟 kernel 算得多快无关，所以它是纯诊断量。
3. **再看 `Wavefronts/Requests`**：它回答"一次请求被拆成了几趟"。拆得越多，占用内存流水线的时间越长，其他 warp 就得排队。
4. **最后看 `Bank Conflicts`**：它只对 shared memory 有意义，是"片上"的访存瓶颈，和显存带宽无关，但同样会拖慢 MIO 流水线。

把这四步走完，你得到的不再是"一堆数字"，而是**一句可以直接改代码的结论**：是地址不连续、还是 bank 冲突、还是指令宽度导致的正常拆分。

## 小结

- 访存效率的度量单位是三层：`request`（warp 级请求）→ `wavefront`（分几趟搬）→ `sector`（每趟搬 32 字节）。
- 理想账单是 `1 request → 4 sector → 1 wavefront`；`Sectors/Req = 4` 就是满分，超过 4 就是在为不连续付钱。
- 判断标准不是"地址是否连续"，而是"**每个 sector 里的字节有没有被用上**"：4 组各 32 字节连续，效果和完全连续一样好。
- 跨列访问会把 `Sectors/Req` 推到 32、`Wavefronts` 推到 8，有效带宽只剩 1/8。
- shared memory 没有 sector，看 `Wavefronts` 与 `Bank Conflicts`；`LDS.128` 拆成 4 个 wavefront 是设计使然，不算冲突。
- `ldmatrix` 给列地址会产生 7 次（×1）或 28 次（×4）bank 冲突，这是手写 GEMM 必须做 swizzle 的直接原因。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| request（内存请求） | 一个 warp 的 32 个线程一起访存时合成的**一个**请求，是面板 `Requests` 列的单位 |
| wavefront（波前） | 一次请求分批发出的"趟"，一个 wavefront 最多搬 4 个 sector（128 字节） |
| sector（扇区） | 访存的最小单位，32 字节；只读 4 字节也要搬整个 sector |
| `Sectors/Req` | 每个请求平均搬了几个 sector；合并访存是 4，越大越浪费 |
| 合并访存（coalescing） | 相邻线程访问相邻地址，使一次请求的字节被完整利用 |
| bank conflict | shared memory 中两个线程同时访问同一 bank，只能串行，表现为 `Wavefronts` 变多、`Bank Conflicts` 大于 0 |
| `ldmatrix` | 把 shared memory 中 8×8 的小块按格式搬进寄存器，供 Tensor Core 使用的指令 |
| swizzle | 把 shared memory 的列地址按异或等方式打散重排，用来消除 bank 冲突 |