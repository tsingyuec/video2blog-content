# Nsight Compute 的 SOL 段：用两个吞吐占比判断瓶颈在哪一侧

> 视频来源：[SOL Analysis with NVIDIA Nsight Compute](https://www.youtube.com/watch?v=uHN5fpfu8As)（YouTube · NVIDIA Developer，讲者 Bob Crovella，NVIDIA 解决方案架构团队）｜时长约 17 分钟
> 简要导读：这是 NVIDIA 官方「CUDA Developer Tools」系列里讲 Nsight Compute **SOL 段**的一集。它不教你怎么敲命令，而是逐行拆解 SOL 段里每一个数字的含义，并用一个 `normcdf` 内核（double → float 只改一行）演示「读数 → 定位 → 改代码 → 用 baseline 复测」的完整闭环。字幕为 YouTube 自动生成，术语已订正（SOL / Throughput / pipe / baseline 等）。

## 本讲要解决的核心问题（SCQA）

**背景**：你已经会用 `ncu` 或 Nsight Compute 的图形界面剖析一个内核了。打开报告，第一段永远是 **SOL**（GPU Speed Of Light Throughput）。

**冲突**：这一段里密密麻麻十几个百分比，还有毫秒、周期数、频率。初学者最常见的两种误读是：只看 `Duration`（耗时）判断快慢，或者把某个百分比当成「GPU 利用率」——以为 84% 就是「GPU 用了 84%」。可 SOL 段里每一个百分比的分母都不一样：有的是 SM 计算峰值的百分比，有的是 DRAM 带宽峰值的百分比。分母不同，百分比之间就不能直接比大小，更不能和 `nvidia-smi` 的 GPU-Util 混为一谈。

**疑问**：SOL 段里每个数字到底在量什么？拿到这些数字之后，怎么判断「这个内核卡在计算还是卡在访存」？判断出来之后，下一步该看哪一段、改什么？

**回答（中心思想）**：SOL 段的读法是**先横向比两个占比，再纵向拆到管线**。横向比的是 `Compute (SM) Throughput` 与 `Memory Throughput` 这两个「占各自可达峰值的百分比」——哪个高，耗时就被哪一侧主导；纵向拆的是 `Compute Throughput Breakdown` / `Memory Throughput Breakdown`，把那个高占比拆到具体的 «pipe»（功能单元）或具体的存储层级上，于是「该改什么」就变成一个具体的动作。视频的演示里，`Compute (SM) Throughput` 是 84.46%、`DRAM Throughput` 只有 3.71%，拆开一看是 FP64 管线撑满；把 `double` 换成 `float` 之后耗时从 2.71 毫秒掉到 62.98 微秒（−97.68%），内存利用率反而从 3% 量级升到 77.61%——**同一个内核，瓶颈从计算侧换到了访存侧**。

---

## 一、SOL 段是默认输出，也是最该先看的一段

SOL 是 **Speed Of Light（光速）** 的缩写。这个名字本身就是它的用法说明：它回答的问题不是「这个内核花了多久」，而是「**相对于相关的上限，这段代码的表现如何、设备利用率有多高**」。

[【跳转到 00:11】](https://www.youtube.com/watch?v=uHN5fpfu8As&t=11)

为什么它被默认放在报告最前面？视频给的理由很实在：与相关上限的对比，是**选择下一步调查方向的良好起点**。分析驱动的优化里，你会反复问同一个问题——「当前限制代码性能的是什么？」SOL 段能在较高层次上先给出一个方向。

[【跳转到 00:50】](https://www.youtube.com/watch?v=uHN5fpfu8As&t=50)

几个使用上的事实：

- SOL 段属于**默认**报告的一部分。`ncu` 不加任何选项跑，SOL 段就在 CLI 输出里；GUI 打开报告时它也默认存在。
- 报告是**按内核调用（kernel invocation）分别生成**的。你剖析了 10 次内核启动，就有 10 份 SOL 段。
- CLI 的输出默认比 GUI 简略，想要更多细节加 `--print-details all`。
- 没有图形界面的机器上，可以用 `ncu -o report` 生成报告文件，再拷到有 GUI 的机器上导入查看。

[【跳转到 01:40】](https://www.youtube.com/watch?v=uHN5fpfu8As&t=100)

---

## 二、上半区：五个吞吐 + 四个时间量

SOL 段的上半区是一个两列的表格，左列是「吞吐占比」，右列是「时间与频率」。

[【跳转到 04:14】](https://www.youtube.com/watch?v=uHN5fpfu8As&t=254)

![Nsight Compute 的 SOL 段：左列五个吞吐占比（Compute 84.46%、Memory 3.71%、L1/TEX 1.30%、L2 2.23%、DRAM 3.71%），右列是 Duration、Elapsed Cycles、SM Active Cycles 与两个频率；下方 High Throughput 是规则输出](assets/Nsight%20Compute%20的%20SOL%20段：用两个吞吐占比判断瓶颈在哪一侧/00254.webp)

左列五个吞吐，全部是「**占可达峰值（peak achievable）的百分比**」：

| 指标 | 量的是什么 |
| :--- | :--- |
| `Compute (SM) Throughput [%]` | SM 的活动水平，占 SM 计算峰值的百分比 |
| `Memory Throughput [%]` | GPU 内存流水线的活动水平，占其峰值的百分比 |
| `L1/TEX Cache Throughput [%]` | 到 L1 / TEX 单元的流量占比 |
| `L2 Cache Throughput [%]` | 流向 L2 的流量占比 |
| `DRAM Throughput [%]` | 到 GPU 片外 DRAM 的流量占比 |

这里有两个容易踩的坑。

**第一，`Memory Throughput` 不等于 `DRAM Throughput`。** 前者是整个内存流水线的活动水平，后者只是「GPU 与挂在 GPU 上的那片 DRAM 芯片之间的流量」。一个内核完全可能 `Memory Throughput` 很高而 `DRAM Throughput` 接近 0——数据全卡在片上的 L1/L2 里打转。后面那支 Glass Box 的视频里就有一个 `Memory Throughput` 98.42%、`DRAM Throughput` 0.44% 的真实例子。

**第二，`Compute (SM) Throughput` 高是好事，但它同时是「该往哪儿优化」的指示。**

[【跳转到 03:52】](https://www.youtube.com/watch?v=uHN5fpfu8As&t=232) 视频的原话是：这个数字高既是我们想达到的目标，也是「该往哪儿使劲」的总体指示。听起来矛盾，其实不矛盾——它衡量的是「你离这条管线的上限有多近」，离得近说明这条管线就是当前的限制项。

右列是四个量，它们之间有一个可以手算校验的关系：

| 指标 | 含义 |
| :--- | :--- |
| `Duration [msecond]` | 内核消耗的流逝时间，毫秒 |
| `Elapsed Cycles [cycle]` | 同一个量，用 GPU 核心时钟周期数表示 |
| `SM Frequency [cycle/nsecond]` | SM 频率 |
| `SM Active Cycles [cycle]` | 「至少有一个 warp 处于活动状态」的流逝周期数，上界是 `Elapsed Cycles` |
| `DRAM Frequency [cycle/nsecond]` | DRAM 时钟，单位 cycles/ns |

`Duration` 与 `Elapsed Cycles` 通过 `SM Frequency` 关联：

$$
\text{Duration}_{ns} \times \text{SM Frequency}_{cycles/ns} \approx \text{Elapsed Cycles}
$$

拿截图里的数字验一下：$2.71\ \text{ms} = 2.71 \times 10^6\ \text{ns}$，乘以 $1.52\ \text{cycle/ns}$ 约等于 $4.12 \times 10^6$，而 `Elapsed Cycles` 是 $4{,}134{,}771$。对得上。这个关系很有用：**当 `Duration` 看起来「不对劲」时，先看 `SM Frequency`**——后面 Glass Box 那支视频会讲，`ncu` 会锁频，所以它报出来的毫秒数不能拿去和正常运行比。

关于 `DRAM Frequency` 还有一个细节：它表示的是「每秒传输次数」意义上的频率，不是 DRAM 的基础时钟频率。现代 DRAM 一次时钟传多次数据（倍泵），所以这个数字会比标称基础频率高。

[【跳转到 05:54】](https://www.youtube.com/watch?v=uHN5fpfu8As&t=354)

`SM Active Cycles` 也值得单独说：它数的是「至少有一个 warp 活着」的周期。如果它远小于 `Elapsed Cycles`，说明内核有相当一段时间 SM 上根本没有活干的 warp——这是「内核太小 / 网格没铺满」的信号，而不是「某个单元太忙」。

---

## 三、案例：SM 84.46%，DRAM 3.71%

视频剖析的代码很简单：对一个 `double2` / `float2` 数组逐元素算 CUDA 数学库里的 `normcdf`（正态分布累积分布函数）。代码里用 `USE_DOUBLE` 这个宏切换 `double` 与 `float` 两个版本，这就是后面「只改一行」的实验装置。

[【跳转到 02:05】](https://www.youtube.com/watch?v=uHN5fpfu8As&t=125)

![被剖析的内核：cdf_kernel 对 double2/float2 数组逐元素调用 normcdf；USE_DOUBLE 宏决定用 double 还是 float 版本，ds 约 100 万个元素，22 个 block、每块 1024 线程](assets/Nsight%20Compute%20的%20SOL%20段：用两个吞吐占比判断瓶颈在哪一侧/00150.webp)

在 GTX 1660 Ti、CUDA 12.0 上剖析 `double` 版本，读出来的上半区是：

| 指标 | 值 |
| :--- | :--- |
| Compute (SM) Throughput | 84.46% |
| Memory Throughput | 3.71% |
| L1/TEX Cache Throughput | 1.30% |
| L2 Cache Throughput | 2.23% |
| DRAM Throughput | 3.71% |

把这两侧放在一起看，结论直接出来了：**SM 相当忙，内存子系统几乎闲着**。所以这个内核的耗时主要由计算决定，而不是访存。

于是优化的方向也就定了：想缩短耗时，就得**减少计算量**；在这个情形下，减少访存或提升访存效率「不太可能带来多少收益」。这句话很重要——它替你省掉了「去优化一个本来就不是瓶颈的东西」的时间。

[【跳转到 06:44】](https://www.youtube.com/watch?v=uHN5fpfu8As&t=404)

---

## 四、规则输出：把专家经验变成一句话

SOL 段中间有一条带信息图标的提示，标题是 **High Throughput**：

> The kernel is utilizing greater than 80.0% of the available compute or memory performance of the device. To further improve performance, work will likely need to be shifted from the most utilized to another unit. Start by analyzing workloads in the Compute Workload Analysis section.

[【跳转到 07:09】](https://www.youtube.com/watch?v=uHN5fpfu8As&t=429)

这是 Nsight Compute 里一条 **Rule（规则）** 的输出。Rule 的作用是「处理指标数据，给出带分析结论的文字」。视频对它的评价是：**对初学者极有价值**，因为它基于 Nsight Compute 开发团队提供的专家经验来分析数据，本质上是一套专家系统。

规则输出有两种形态：像这条一样的**提示（information）**，以及**警告（warning）**——警告意味着更严重的性能问题。规则文字通常还会**指向下一个该看的报告段**（这条指向 Compute Workload Analysis），这就是「下一步该点哪里」的答案。

---

## 五、Breakdown：把 84.46% 拆到具体管线

上半区只告诉你「计算侧是瓶颈」。要变成可执行的动作，还得知道**计算侧里是哪一部分**。这就是 SOL 段下半区的两列：

- `Compute Throughput Breakdown`：把计算吞吐拆到各个 **pipe（管线）**；
- `Memory Throughput Breakdown`：把内存子系统利用率拆到 DRAM、L2、L1/TEX、LSU（Load/Store 单元）等具体机制。

[【跳转到 09:00】](https://www.youtube.com/watch?v=uHN5fpfu8As&t=540)

「pipe」这个词需要解释一下：它是 GPU 或 SM 内部**处理某类指令/运算的功能单元**。做算术时，整数运算和浮点运算可能走不同的 pipe；具体列出来的有 64 位浮点、32 位浮点、整数、Tensor Core 等。

[【跳转到 08:35】](https://www.youtube.com/watch?v=uHN5fpfu8As&t=515)

![SOL 段展开后的完整视图：上方柱状图对比 Compute 与 Memory，下方两列分别是 Compute Throughput Breakdown（SM: Pipe Fp64 Cycles Active 84.46% 排第一）与 Memory Throughput Breakdown（DRAM: Cycles Active 3.71% 排第一）](assets/Nsight%20Compute%20的%20SOL%20段：用两个吞吐占比判断瓶颈在哪一侧/00540.webp)

这张图里最关键的一行是 `SM: Pipe Fp64 Cycles Active [%] = 84.46`——它和上半区的 `Compute (SM) Throughput` 是同一个数。也就是说：**整个计算侧的 84.46%，几乎全部由 FP64 管线贡献**。

视频对这个结果的解读分两层：

1. 代码在算 `normcdf` 时大量使用 64 位浮点运算；
2. GTX 1660 Ti 上处理 64 位浮点的单元数量**相对很少**（消费级卡对 FP64 一向吝啬）。

两者叠加，这项特性就成了「**长杆（long pole）**」——最该动手的地方。同时注意 `Memory Throughput Breakdown` 那一列最高的也只有 3.71%（`DRAM: Cycles Active`），再次印证内存侧整体很闲。

还有一个容易忽略的细节：**Breakdown 里的行序不是固定的，而是按帕累托顺序排列**。哪条管线最忙，哪条就排在最上面。所以你不能靠「第几行」来认管线，只能靠名字。

---

## 六、改一行 `double` → `float`，用 baseline 做对比

[【跳转到 11:30】](https://www.youtube.com/watch?v=uHN5fpfu8As&t=690)

线索齐了：瓶颈是 FP64 管线，而这张卡 FP64 很弱。最直接的改法就是把 64 位浮点换成 32 位浮点——用 `float` 代替 `double`，用 32 位版本的 `normcdff`。代码里已经有这个开关：不定义 `USE_DOUBLE` 编译即可。

[【跳转到 12:42】](https://www.youtube.com/watch?v=uHN5fpfu8As&t=762)

重新剖析之前，视频先用了一个 GUI 的基础功能：**baseline（基线）**。在旧报告页点 `Add Baseline`，再切到新报告页，两次剖析的数据就并排显示在一张表里，每个数字后面还带着相对基线的变化百分比。

[【跳转到 13:07】](https://www.youtube.com/watch?v=uHN5fpfu8As&t=787)

![baseline 对比视图：Current（float 版）耗时 62.98 微秒，Baseline 1（double 版）耗时 2.71 毫秒；Compute 69.95%（−17.18%）、Memory 77.61%（+1990.72%）、DRAM 77.61%（+1990.72%），规则输出变成 Balanced Throughput](assets/Nsight%20Compute%20的%20SOL%20段：用两个吞吐占比判断瓶颈在哪一侧/00854.webp)

变化很大，逐条读：

| 指标 | double（基线） | float（当前） | 变化 |
| :--- | ---: | ---: | ---: |
| Duration | 2.71 ms | 62.98 μs | −97.68% |
| Elapsed Cycles | 4,134,771 | 95,288 | −97.70% |
| SM Active Cycles | 4,057,665 | 88,773 | −97.81% |
| Compute (SM) Throughput | 84.46% | 69.95% | −17.18% |
| Memory Throughput | 3.71% | 77.61% | +1990.72% |
| DRAM Throughput | 3.71% | 77.61% | +1990.72% |

**耗时降了 97% 以上。** 但更值得注意的是两个吞吐占比的走向：计算侧从 84.46% 降到 69.95%，内存侧从 3.71% 涨到 77.61%。规则输出也从 `High Throughput` 变成了 `Balanced Throughput`：

> Compute and memory are well-balanced: To reduce runtime, both computation and memory traffic must be reduced.

「balanced（均衡）」的意思是：相对设备的理论峰值，计算与内存的利用率大致相当。之前是「不均衡」——64 位浮点是限制项，内存利用率很低；现在两侧都高，**再想变快就得两边一起减**。

再看 Breakdown，管线的归属也变了：

[【跳转到 14:37】](https://www.youtube.com/watch?v=uHN5fpfu8As&t=877)

![float 版的 Breakdown：Compute 侧第一名变成 SM: Pipe Fma Cycles Active 69.95%（+11252.08%），而 SM: Pipe Fp64 Cycles Active 变成 0（−100%）；Memory 侧 DRAM: Cycles Active 77.61%（+1990.72%）](assets/Nsight%20Compute%20的%20SOL%20段：用两个吞吐占比判断瓶颈在哪一侧/00877.webp)

- `SM: Pipe Fma Cycles Active [%]` 变成第一名，69.95%——FMA 管线正是处理 32 位浮点计算的那条；
- `SM: Pipe Fp64 Cycles Active [%]` 变成 0（−100%），FP64 完全不再被使用。

---

## 七、为什么「数据量减半」不是耗时骤降的主要原因

这里有一个很值得学的推理，因为直觉容易归错因。

换到 `float` 之后，每个元素占的空间只有 `double` 的一半，所以这个版本**读写的数据量确实减半**。但视频强调：耗时的大幅缩短**主要来自计算管线利用率的变化**，而不是数据量减半。

理由是：GTX 1660 Ti 处理 32 位浮点的能力比处理 64 位浮点强得多。耗时骤降之后，虽然读写的数据量只有一半，但**读写活动持续的总时间短得多**。于是「实际流量 ÷ 峰值带宽」这个比值反而大幅上升——内存利用率从 3%–4% 的量级升到了 70% 以上。

换句话说：内存利用率的上升，不是因为搬了更多数据，而是因为**分母里的时间变短了**。这也是为什么读 SOL 段时不能只看单个百分比，必须把「耗时」和「占比」放在一起看。

---

## 八、SOL 段是起点，不是终点

视频结尾把 SOL 段的定位说得很清楚：它只是 Nsight Compute 众多报告段中的一段，但被视为**起点**、最该先看的一段，所以在报告里排在最前面。它的规则输出会把你导向别的报告段（比如 Compute Workload Analysis、Memory Workload Analysis），让你继续往下查。

所以一条可复用的读法是：

1. 看 `Compute (SM) Throughput` 与 `Memory Throughput` 两个占比，**定方向**（计算侧 / 访存侧 / 两侧都低）；
2. 看对应那一侧的 Breakdown，**定单元**（哪条 pipe、哪一级存储）；
3. 读规则输出，**定下一步该看哪一段**；
4. 改一处，用 baseline 复测，看数字有没有真的动。

---

## 小结

- SOL 段里每个百分比的分母都是「**该单元自己的可达峰值**」，不是整机峰值，也不是 `nvidia-smi` 的 GPU-Util。所以不同百分比之间不能直接比大小，只能和同一行比。
- 定方向看两个数：`Compute (SM) Throughput` 与 `Memory Throughput`。案例里 84.46% vs 3.71%，结论是「耗时由计算驱动」，于是「减少访存帮助不大」。
- `Memory Throughput` ≠ `DRAM Throughput`：前者是整个内存流水线，后者只是到片外 DRAM 的流量。片上打转的内核可以前者很高、后者接近 0。
- 定单元看 Breakdown：`SM: Pipe Fp64 Cycles Active 84.46%` 说明计算侧的负载几乎全压在 FP64 管线上。Breakdown 的行序是按帕累托排的，认名字不要认行号。
- `Duration`、`Elapsed Cycles`、`SM Frequency` 三者满足 $\text{Duration}_{ns} \times f_{cycles/ns} \approx \text{Elapsed Cycles}$，可以手算校验。`SM Active Cycles` 远小于 `Elapsed Cycles` 说明 SM 有空转。
- 规则（Rule）输出是内置的专家系统，会直接告诉你「下一步看哪一段」，对初学者尤其有用。
- baseline 功能让新旧两份剖析并排显示并自动算变化百分比。案例里 `double → float` 让耗时从 2.71 ms 降到 62.98 μs（−97.68%），瓶颈从 FP64 计算侧换到了访存侧（Memory 3.71% → 77.61%），规则输出从 `High Throughput` 变成 `Balanced Throughput`。
- 内存利用率上升不一定意味着搬了更多数据，也可能只是**时间变短了**——占比的分母是时间。

## 关键术语速查

| 术语 | 一句话解释 |
| :--- | :--- |
| SOL（Speed Of Light） | Nsight Compute 报告的第一段，用「占各自可达峰值的百分比」刻画各单元利用率 |
| Compute (SM) Throughput | SM 计算活动水平占其峰值的百分比，高说明计算侧接近上限 |
| Memory Throughput | GPU 内存流水线的活动水平占其峰值的百分比（不等于 DRAM 吞吐） |
| DRAM Throughput | GPU 与片外 DRAM 之间的流量占峰值的百分比 |
| pipe（管线） | GPU/SM 内处理某类指令的功能单元，如 FP64、FMA、整数、Tensor Core |
| Breakdown | SOL 段下半区的两列，把计算/内存吞吐拆到具体 pipe 或存储层级 |
| Rule（规则） | Nsight Compute 内置的分析规则，输出提示或警告，并指向下一个该看的报告段 |
| baseline（基线） | GUI 功能，把某份报告设为参照，新报告里显示相对变化百分比 |
| Balanced Throughput | 规则判定计算与内存利用率大致相当，此时要降耗需两边一起减 |
| long pole | 比喻「最长的那根杆」，指当前最该动手优化的限制项 |