# warp 分歧与延迟隐藏：从分支等待到占用率

> 视频来源：[CUDA入门-深入GPU架构（warp & 调度）](https://www.bilibili.com/video/BV1LCeBzTEuM/)（Bilibili · UP 主 铁甲小宝之蜻蜓队长）｜时长约 27 分钟
> 导读：本文按视频的顺序讲清三件事——分支为什么会变成"等待"、warp 停顿之后靠什么顶上、以及"要多少 warp 才够"这个最小法则。文中所有公式与数字都来自视频里展示的讲义，不额外补充。

## 本讲要解决的核心问题（SCQA）

**背景**：你已经知道 GPU 以 warp（32 个线程）为单位调度，也知道 Nsight Compute 会给出 warp 停顿原因（stall reason）和占用率（occupancy）这两个指标。

**冲突**：指标里 `Stall` 一栏最常见的原因是"等待"——等分支、等数据、等同步。但同样是"等"，分支造成的等、访存造成的等、同步造成的等，处方完全不同；而占用率不足又会让你根本没有别的 warp 可以顶上来。

**疑问**：怎样从"warp 为什么停"和"占用率是多少"这两条线索，判断瓶颈属于分支、访存还是占用率，并知道该改哪一段代码？

**回答（中心思想）**：GPU 靠**切换 warp** 来掩盖停顿，所以任何瓶颈最终都表现为「某个周期没有合格的 warp 可发射」。分支让一个 warp 内的线程分头执行、互相等待；访存让整个 warp 停 400 到 800 个周期；占用率决定了你手里到底有多少 warp 可以拿来填这个空档。**先算清需要多少 warp（时延 × 吞吐量），再看实际占用率够不够，就能把三类瓶颈分开。**

## 一、warp 是调度的基本单位，不是"32 个线程的盒子"

视频先纠正了一个常见误解：**一个 SM 里 CUDA core 的数量，不等于这个 SM 能支持的最大线程数**。

![warp 的定义与映射：一个 block 只能在一个 SM 上调度，block 内的线程以 warp 为单位调度；SM 的 CUDA core 数与最大线程数不是一回事](assets/warp%20分歧与延迟隐藏：从分支等待到占用率/00209.webp)

以视频举的特斯拉 V100 为例：每个 SM 最大线程数是 2048，但每个 SM 拥有的 CUDA core 只有 64。开一个 1024 线程的 block，调度时这 1024 个线程会被划分成 32 个 warp，SM 再依次把这些 warp 调度到 CUDA core 上运行——**不是 CUDA core 和线程一对一匹配**。

一个 block 里的 warp 数由这个公式决定：

$$
\text{warp\_per\_block} = \left\lceil \frac{\text{ThreadsPerBlock}}{\text{WarpSize}} \right\rceil
$$

其中 `WarpSize` 一般是 32。取整符号意味着：**block 的线程数不是 32 的倍数时，硬件会多给你一个 warp**，里面那些线程是 inactive 的，但依然占着 SM 资源。这就是"block 大小要设成 32 的倍数"的真正原因——不是为了好看，是为了不浪费一个 warp 的槽位。

[【跳转到 03:29】](https://www.bilibili.com/video/BV1LCeBzTEuM/?t=209)

[【跳转到 03:29】](https://www.bilibili.com/video/BV1LCeBzTEuM/?t=209)

## 二、分支：一个 warp 内的线程必须走同一条指令

### 2.1 为什么"分支"在 GPU 上变成了"等待"

CPU 有复杂的分支预测，猜对了几乎不花钱。GPU 没有这套东西，它靠 SIMT（单指令多线程）：**同一个 warp 内的 32 个线程必须执行相同的指令**。

于是遇到 `if-else` 时，硬件只能串行：先让走 `if` 的线程执行，走 `else` 的线程被阻塞；再反过来。视频用一张时间轴图说明了这件事：

![warp divergence 的时间轴：蓝色是一致执行的指令，橙色是 if 分支，绿色是 else 分支，紫色是停滞等待；每个线程把两条分支的时间都占了一遍](assets/warp%20分歧与延迟隐藏：从分支等待到占用率/00383.webp)

图里横轴是 32 个线程、纵轴是时间。进入分支后，橙色的线程在跑 `if`，绿色的线程就在紫色格子里干等；等 `if` 跑完，绿色线程再跑 `else`，橙色线程进紫色格子。**本来只需要执行一次的分支，现在两条路的耗时都要付。**

[【跳转到 06:23】](https://www.bilibili.com/video/BV1LCeBzTEuM/?t=383)

关键限定：**warp divergence 只发生在同一个 warp 之内**。不同 warp 之间不需要互相等待，所以把分支的粒度从"线程"提高到"warp"，代价就消失了。

### 2.2 一个能直接改的例子

视频给的例子是：把 `A + B` 写进 `C`，线程编号为偶数时结果是 100，奇数时是 200。最直觉的写法是按线程编号判断：

```cuda
__global__ void mathKernel1(float *c) {
    int tid = blockIdx.x * blockDim.x + threadIdx.x;
    float a, b;
    a = b = 0.0f;
    if (tid % 2 == 0) {
        a = 100.0f;
    } else {
        b = 200.0f;
    }
    c[tid] = a + b;
}
```

![按线程编号奇偶分支：同一个 warp 里偶数线程和奇数线程各走一边，必然产生 divergence](assets/warp%20分歧与延迟隐藏：从分支等待到占用率/00547.webp)

一个 warp 里 0、2、4、6……走 `if`，1、3、5、7……走 `else`，于是这个 warp 要把两条分支都执行一遍。

改法是把判断条件从"线程编号"换成"warp 编号"：

```cuda
__global__ void mathKernel2(void) {
    int tid = blockIdx.x * blockDim.x + threadIdx.x;
    float a, b;
    a = b = 0.0f;
    if ((tid / warpSize) % 2 == 0) {
        a = 100.0f;
    } else {
        b = 200.0f;
    }
    c[tid] = a + b;
}
```

![按 warp 编号分支：同一个 warp 内 0 到 31 除以 32 都是 0，全部走同一条路，不再互相等待](assets/warp%20分歧与延迟隐藏：从分支等待到占用率/00622.webp)

现在 0 到 31 号线程除以 32 都是 0，再对 2 取余都是偶数，整个 warp 走 `if`；32 到 63 号线程走 `else`。**warp 内不再有分歧。**

[【跳转到 09:32】](https://www.bilibili.com/video/BV1LCeBzTEuM/?t=572)

视频也诚实地指出这个改法的代价：两段代码的**计算结果并不一样**（前者按线程奇偶，后者按 warp 奇偶），所以它只是一个"展示怎么让 warp 内不等待"的示例，真实场景里要自己权衡语义。

### 2.3 分支瓶颈在指标上长什么样

分支效率（branch efficiency）是专门衡量这件事的指标：

$$
\text{Branch Efficiency} = 100 \times \frac{\#\text{Branches} - \#\text{Divergent Branches}}{\#\text{Branches}}
$$

![分支效率的定义与 nvprof 实测输出，以及 warp 上下文的三部分（程序计数器、寄存器、shared memory）](assets/warp%20分歧与延迟隐藏：从分支等待到占用率/00707.webp)

100% 表示没有分歧，掉到 50% 就说明有一半分支在分头执行。视频里有个值得注意的细节：上面两个 kernel 用 nvprof 的 branch_efficiency 指标测出来**都是 100%**，因为代码足够简单时编译器会把它优化成谓词执行（预测值置 0/1，两个分支都执行、但只有一个结果生效），分支指令根本不存在了。想看真实的分歧，需要用 `-G` 关掉优化重新编译。

这也提醒了一件事：**在源码里看到 `if`，不等于在 SASS 里有分支**。判断分支瓶颈要看实测的分支效率或 stall reason，而不是数源码里的 `if`。

[【跳转到 11:47】](https://www.bilibili.com/video/BV1LCeBzTEuM/?t=707)

### 2.4 判断与处方

| 你看到的现象 | 判断 | 处方 |
| --- | --- | --- |
| 分支条件依赖 `threadIdx` 的奇偶/取模 | warp 内必然分歧 | 把条件改成以 `warpSize` 为步长 |
| 分支里两边的代码量都很小 | 分歧代价可能小于重写成本 | 用谓词（两个分支都算、用掩码选结果）代替跳转 |
| 数据本身杂乱导致分支 | 分歧来自数据布局 | 先对数据排序/分组，让同一 warp 处理同类数据 |
| 循环次数因线程而异 | 短的线程要等最长的线程 | 重新划分任务，让每个线程的工作量接近 |

## 三、warp 的三种状态：谁在等，谁在跑

要理解"停顿"，得先知道 warp 有哪些状态。视频引用的讲义把 active warp 分成三类：

![warp 的三种状态：selected（被选中发射）、eligible（就绪但没被选中）、stalled（停滞）；以及各计算能力等级的 SM 资源上限表](assets/warp%20分歧与延迟隐藏：从分支等待到占用率/00932.webp)

- **selected warp**：这个周期被调度器选中、正在发射指令的 warp。
- **eligible warp**：已经准备好、但这一周期没被选中的 warp（调度器每周期只能发射有限条指令）。
- **stalled warp**：还没准备好执行的 warp。

一个 warp 要能执行，必须同时满足两个条件：**32 个 CUDA core 有空**，以及**当前指令的所有参数都就绪**。缺一个就进 stalled 状态。

[【跳转到 15:32】](https://www.bilibili.com/video/BV1LCeBzTEuM/?t=932)

这也解释了为什么"占用率"不是越高越好、但太低一定不行：**stalled 的 warp 需要有别的 eligible warp 来顶替**，而 eligible warp 的数量上限，由你实际驻留在 SM 上的 warp 数决定。

## 四、延迟隐藏：算术等 10 个周期，访存等 400 个

指令从开始到结束消耗的时钟周期数叫**指令时延（latency）**。视频给了两类指令的量级：

- **算术指令**：10 到 20 个时钟周期（整数加、浮点加）。
- **访存指令（global memory）**：400 到 800 个时钟周期。

差距是几十倍。如果每个周期都有 eligible warp 被调度，计算资源就能被充分利用；反过来，一个 warp 去访存了，它要停几百个周期，这段时间 CUDA core 就空着——**除非你还有别的 warp 可以顶上去**。

![延迟隐藏的执行流程：warp 0 去访存后被挂起，调度器依次发射 warp 2、warp 3、warp 6 等，等 warp 0 的数据回来再切回去](assets/warp%20分歧与延迟隐藏：从分支等待到占用率/01057.webp)

图里 `warp 0 waiting while SM still busy` 这一行是关键：**warp 0 在等，但 SM 没闲着**。这就是延迟隐藏（latency hiding）。

[【跳转到 17:37】](https://www.bilibili.com/video/BV1LCeBzTEuM/?t=1057)它也解释了为什么 GPU 需要那么多寄存器：每个 warp 的上下文都留在片上，切换 warp 只需要一个周期，不像 CPU 线程切换要保存/恢复。

## 五、最小法则：需要多少 warp 才够

视频给的估算方法叫"最小法则"：

$$
\text{所需并行度} = \text{指令时延} \times \text{吞吐量}
$$

其中吞吐量指 SM 每个周期能发射多少条该类型的指令。视频用 Fermi 架构举例，为了好算把算术指令的吞吐量取成 4：

- 算术指令：时延 10 × 吞吐量 4 = **40 个线程**，也就是约 2 个 warp 就够。
- 换个参数：时延 20 × 吞吐量 32 = **640 个线程**，除以 32 得 **20 个 warp**。
- 访存指令：一个 `float4`（16 字节）的 load，需要约 **18500 个线程**，除以 32 约 **579 个 warp** 才能把 memory latency 完全藏住。

![Fermi 上藏住访存延迟的推算：74 KB ÷ 4 字节 ≈ 18500 个线程，除以 32 得 579 个 warp，再按 16 个 SM 分摊到每个 SM 约 36 个 warp](assets/warp%20分歧与延迟隐藏：从分支等待到占用率/01427.webp)

这组数字的意义在于：**它给了你一个"够不够"的标尺**。如果你的 kernel 实际驻留的 warp 数远小于这个值，那么访存延迟就藏不住，Nsight 里会看到大量 memory 相关的 stall；如果已经超过，再加 warp 也没用，该去优化访存本身。

[【跳转到 21:11】](https://www.bilibili.com/video/BV1LCeBzTEuM/?t=1271)

## 六、占用率：把"够不够"变成一个百分比

占用率的定义很直接：

$$
\text{occupancy} = \frac{\text{active warps}}{\text{maximum warps}}
$$

![warp 何时算 eligible、何时算 stalled 的两条判定条件，以及"资源限制了 active warp 数量"的说明——占用率的分子就是这些 active warp](assets/warp%20分歧与延迟隐藏：从分支等待到占用率/01352.webp)

分母 `maximum warps` 可以用 `cudaGetDeviceProperties` 拿到 `maxThreadsPerMultiProcessor` 再换算（上一张图里也给出了这个公式）。视频给的 block/grid 配置准则有五条：

1. 保证 block 里的线程数是 32 的倍数。
2. 避免 block 太小，每个 block 至少 128 或 256 个线程。
3. 根据 kernel 需要的资源（寄存器、shared memory）调整 block 大小。
4. 保证 block 的数量远大于 SM 的数量。
5. 多做实验，找出最好的配置。

视频还特别提醒：**占用率不是唯一的性能指标**。占用率达到某个值之后，再往上调可能就没有效果了，因为瓶颈已经换成了别的东西。

[【跳转到 22:32】](https://www.bilibili.com/video/BV1LCeBzTEuM/?t=1352)

## 七、同步：另一种"等"

视频最后提到同步的两个层次，这是第三类停顿来源：

- **设备级同步**：等待整个 kernel（算子）完成。
- **block 级同步**：等待一个 block 内所有线程都执行到某个点，也就是 __syncthreads() 这类操作。

![同步的两种实现：system-level 用 cudaDeviceSynchronize 等 host 与 device 的工作都完成，block-level 用 __syncthreads 等 block 内所有线程到达同一个点](assets/warp%20分歧与延迟隐藏：从分支等待到占用率/01452.webp)

同步的代价和分支很像：**它把"最快的线程"和"最慢的线程"绑在一起**。如果 block 内不同 warp 的工作量不均，先到的 warp 只能在 barrier 前空转；如果某个 warp 刚好在等一次未命中的访存，整个 block 都跟着等。所以在 Nsight 里看到 barrier 相关的 stall 时，先别急着删 __syncthreads()（它通常是正确性需要的），而要去看**barrier 之前各 warp 的工作量是否均衡、访存是否规整**。

[【跳转到 24:12】](https://www.bilibili.com/video/BV1LCeBzTEuM/?t=1452)

## 八、把三类瓶颈分开：一张诊断顺序表

把视频里的线索串起来，可以得到一个固定的判断顺序：

| 顺序 | 看什么 | 如果是这样 | 判断 | 处方 |
| --- | --- | --- | --- | --- |
| 1 | warp 停顿原因里 branch/divergence 占比高 | 分支条件依赖线程编号 | 分支瓶颈 | 把条件改成以 warp 为单位；或用谓词 |
| 2 | memory 相关 stall 占比高，且占用率低于最小法则算出的需求 | 驻留 warp 不够 | 占用率不足导致的访存停顿 | 减小 block、降寄存器/shared memory 占用，提高驻留 warp 数 |
| 3 | memory 相关 stall 占比高，但占用率已达标 | warp 够多，是访存本身慢 | 访存瓶颈 | 改访问模式（合并访存、减少重复读） |
| 4 | barrier/sync 相关 stall 占比高 | warp 在 barrier 前等待 | 同步瓶颈 | 平衡各 warp 工作量；减少 barrier 次数；把同步点前移/后移错开 |
| 5 | 占用率接近上限、stall 仍然很大 | 没有空位再加 warp | 已到"加 warp 无效"的区间 | 转向减少指令数、提高单 warp 效率 |

**顺序很重要**：占用率是"你有没有资源去掩盖停顿"的前提，所以要先判断它够不够，再去判断停顿本身是什么类型。反过来做，很容易把"占用率不足导致的访存停顿"误判成"访存模式有问题"，然后白改一通。

[【跳转到 26:50】](https://www.bilibili.com/video/BV1LCeBzTEuM/?t=1610)

## 小结

- 一个 SM 的 CUDA core 数不等于最大线程数；block 内的线程以 warp 为单位被调度，warp 数 = ceil(线程数 / 32)。
- 分支在 GPU 上表现为等待：同一个 warp 内的线程必须走同一条指令，`if-else` 会把两条路的时间都付一遍；把分支条件从线程编号改成 warp 编号可以消除 warp 内分歧。
- warp 有三种状态：selected、eligible、stalled；能执行要同时满足"32 个 CUDA core 有空"和"指令参数就绪"。
- 算术指令时延 10 到 20 个周期，global 访存 400 到 800 个周期，差距靠切换 warp 来掩盖。
- 最小法则：所需并行度 = 时延 × 吞吐量；Fermi 上藏住一次 `float4` 访存要约 18500 个线程、579 个 warp。
- 占用率 = active warps / maximum warps；它不是唯一指标，达到某个值后再加 warp 就无效了。
- 同步把最快和最慢的线程绑在一起，barrier 前的等待要先查工作量是否均衡，而不是直接删同步。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| warp | SM 的基本调度与执行单元，含 32 个并行线程，以 SIMT 方式执行同一条指令 |
| SIMT | 单指令多线程：一个 warp 内所有线程在同一周期执行同一条指令，只是数据不同 |
| warp divergence | 同一个 warp 内的线程因分支走不同路径，硬件只能串行执行，造成等待 |
| active / eligible / selected / stalled warp | 分别指驻留、就绪、本周期被选中、未就绪四种状态的 warp |
| 指令时延（latency） | 一条指令从开始到结束消耗的时钟周期数；算术 10–20，global 访存 400–800 |
| 延迟隐藏（latency hiding） | 一个 warp 停顿时切换去执行别的 warp，让计算单元不空闲 |
| 最小法则 | 所需并行度 = 指令时延 × 吞吐量，用来估算需要多少 warp 才能藏住延迟 |
| occupancy（占用率） | 每个 SM 上 active warp 数占最大 warp 数的比例 |
| __syncthreads() | block 级同步，要求 block 内所有线程都到达该点后才能继续 |