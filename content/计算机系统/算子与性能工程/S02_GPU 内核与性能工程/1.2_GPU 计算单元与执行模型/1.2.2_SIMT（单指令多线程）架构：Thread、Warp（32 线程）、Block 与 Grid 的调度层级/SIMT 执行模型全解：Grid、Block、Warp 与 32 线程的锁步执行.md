# SIMT 执行模型全解：Grid、Block、Warp 与 32 线程的锁步执行

> 视频来源：[CUDA Warps and Blocks: the SIMT Model and Warp Divergence — GPU Programming in C/CUDA | Ep 2](https://www.youtube.com/watch?v=3iTRA3Y8d-g)（YouTube · Glass Box Computing）｜时长约 26.7 分钟
> 导读：这支视频把「一行 kernel 启动代码如何变成几万个线程、硬件又如何按 32 个一组把它们跑起来」拆成五步讲完：层级、warp、分歧、SM 延迟隐藏、纸笔推演。本文按同样的顺序复述，所有公式与例子都对应视频画面。

## 本讲要解决的核心问题（SCQA）

**背景**：CUDA 里启动一个 kernel 只需要一行代码，`myKernel<<<100, 256>>>(...)`，括号里两个数字分别表示「多少个 block」和「每个 block 多少个线程」。

**冲突**：这一行代码凭空造出了 25600 个线程，可显卡上并没有 25600 个核。你也没有逐个指定「谁先跑、谁后跑」。那这些线程到底由谁执行、按什么顺序执行？

**疑问**：如果硬件只能一次跑一小批线程，那 thread / block / grid 这些层级到底对应什么物理事实？为什么写代码时还要关心「warp」这个从没在代码里出现过的词？

**回答（中心思想）**：GPU 的执行模型是**三级逻辑层级 + 一级硬件分组**。逻辑上线程被组织成 grid → block → thread，线程靠自己的坐标算出一个唯一的数据下标；物理上硬件把线程按 **32 个一组**打包成 **warp**，warp 才是真正被调度的单位。正因为一个 warp 共享一条指令流，warp 内部一旦走不同分支，两条路径只能**排队串行**执行——这就是 warp 分歧的代价。

## 一、一行启动代码造出一群「有结构」的线程

视频开篇先纠正一个常见误解：写个普通 C 的 `for` 循环，编译器不会自动帮你并行化。并行是**你主动设计**的——你写一个 kernel，再给它一个 launch configuration（启动配置），也就是 block 数和每 block 线程数。

`myKernel<<<100, 256>>>(...)` 展开后是：

$$
100 \text{ blocks} \times 256 \text{ threads/block} = 25600 \text{ threads}
$$

这 25600 个线程不是一堆乱麻，而是有严格结构的。[【跳转到 01:46】](https://www.youtube.com/watch?v=3iTRA3Y8d-g&t=106)

![一行启动代码 myKernel<<<100, 256>>> 展开成 25600 个线程，每个小方块是一个线程](assets/SIMT%20执行模型全解：Grid、Block、Warp%20与%2032%20线程的锁步执行/00106.webp)

## 二、三级坐标系：grid → block → thread

CUDA 把线程分成三层，从大到小是：

1. **grid（网格）**：一次 kernel 启动的全部线程，是最大的一层；
2. **block（线程块）**：grid 由若干 block 组成，block 是能互相协作、能同步的最小单位；
3. **thread（线程）**：block 由若干线程组成，是最小的一层。

关键在于：**线程不自动拥有数据槽位，它得用自己在层级里的坐标算出一个数组下标**。算得好，没有两个线程抢同一个槽位。

### 2.1 从「一维平铺」到「分块」

视频先用最简单的例子：12 个数据格、12 个线程，一个线程对一个格，线程 $k$ 就负责数组第 $k$ 格。这在一维平铺时毫无问题。[【跳转到 03:10】](https://www.youtube.com/watch?v=3iTRA3Y8d-g&t=190)

![12 个数组格与 12 个线程一一对应，线程 k 拥有第 k 格](assets/SIMT%20执行模型全解：Grid、Block、Warp%20与%2032%20线程的锁步执行/00260.webp)

但真实的启动总是多 block 的。把同样 12 个线程分成 3 个 block、每 block 4 个线程后，出现了三个新名字：

- `blockIdx.x`：你在第几个 block（这里是 0、1、2）；
- `threadIdx.x`：你在本 block 内的局部编号，**每个 block 都从 0 重新开始**；
- `blockDim.x`：一个 block 有多大（这里是 4）。

问题随之而来：block 2 里的局部编号是 0、1、2、3，可它们应该负责数组的第 8、9、10、11 格。**光有局部编号已经不够用了**。[【跳转到 04:45】](https://www.youtube.com/watch?v=3iTRA3Y8d-g&t=285)

![同样 12 个线程被分成 3 个 block，每块内部 threadIdx.x 从 0 重新计数](assets/SIMT%20执行模型全解：Grid、Block、Warp%20与%2032%20线程的锁步执行/00310.webp)

### 2.2 全局下标公式

对「一维 grid + 一维 block」这种最常见的情形，全局下标由线程已知的三个量拼出来：

$$
\text{global index} = \text{blockIdx.x} \times \text{blockDim.x} + \text{threadIdx.x}
$$

读法是：先跳到本 block 的起点（`blockIdx.x × blockDim.x`），再加上自己在 block 内的偏移（`threadIdx.x`）。[【跳转到 05:45】](https://www.youtube.com/watch?v=3iTRA3Y8d-g&t=345)

![全局下标公式：blockIdx.x 乘 blockDim.x 再加 threadIdx.x](assets/SIMT%20执行模型全解：Grid、Block、Warp%20与%2032%20线程的锁步执行/00345.webp)

视频当场验算了一个真实线程：想拿到第 9 格的线程在 block 2、局部编号 1，代入公式

$$
2 \times 4 + 1 = 9
$$

正好落在第 9 格上。[【跳转到 06:35】](https://www.youtube.com/watch?v=3iTRA3Y8d-g&t=395)

### 2.3 新手最常犯的错：只用了 threadIdx.x

如果偷懒只写 `threadIdx.x` 当下标，会发生什么？block 0 写第 0～3 格，block 1 的局部编号也是 0～3，于是**也去写第 0～3 格**。所有 block 都盯着数组开头那几个位置，写入互相覆盖，数组大部分区域永远没人碰。

程序能跑通、不报错，但结果是错的。修法就是回到完整公式。[【跳转到 07:00】](https://www.youtube.com/watch?v=3iTRA3Y8d-g&t=420)

![只使用 threadIdx.x 时所有 block 都写同一批格子，写入冲突且大部分数组未被访问](assets/SIMT%20执行模型全解：Grid、Block、Warp%20与%2032%20线程的锁步执行/00420.webp)

## 三、硬件真正调度的单位是 warp，不是 thread

到这里都还是「逻辑层级」。往下走一层就进入硬件：**硬件既不一次跑一个线程，也不一次跑一整个 block，而是按 32 个一组来跑**。这 32 个线程叫一个 **warp（线程束）**。视频称这是本部分最重要的硬件概念。[【跳转到 08:08】](https://www.youtube.com/watch?v=3iTRA3Y8d-g&t=488)

### 3.1 一个 warp = 32 条 lane 共享一条指令流

把 warp 画成一行 32 个格子，每个格子叫一条 **lane（通道）**。lane 上方是这条 warp 要执行的指令流：LOAD → MUL → ADD → STORE。**32 条 lane 共享这一条流**，不是各自挑指令。[【跳转到 09:02】](https://www.youtube.com/watch?v=3iTRA3Y8d-g&t=542)

![一个 warp 是 32 条 lane，上方是一条共享的指令流 LOAD、MUL、ADD、STORE](assets/SIMT%20执行模型全解：Grid、Block、Warp%20与%2032%20线程的锁步执行/00542.webp)

执行时整条 warp 一起走：轮到 LOAD，32 条 lane 全亮；轮到 ADD，32 条 lane 又全亮。这种「全组同进同退」叫 **lockstep（锁步）**。所以 warp 不是 32 个独立工人，而是**绑在同一条指令流上的 32 条 lane**。

视频还补了一个重要限定：自 Volta 架构起，硬件其实可以独立调度 warp 内的 lane（independent thread scheduling，独立线程调度）。但**把 warp 当作锁步整体来推理，在这门课里能得到正确答案**，所以后面一直沿用这个模型。

### 3.2 一个 block 被切成整数个 warp

256 个线程的 block，硬件看到的是 $256 \div 32 = 8$ 个 warp：warp 0 是线程 0～31，warp 1 是 32～63，……warp 7 是 224～255，正好整除。[【跳转到 10:32】](https://www.youtube.com/watch?v=3iTRA3Y8d-g&t=632)

![256 个线程的 block 被切成 8 个 warp，每个 warp 32 线程](assets/SIMT%20执行模型全解：Grid、Block、Warp%20与%2032%20线程的锁步执行/00632.webp)

但 block size 不是 32 的倍数时会浪费。启动 100 个线程的 block，硬件只能按整 warp 分配，于是给出 4 个 warp = 128 条 lane：前三个 warp 满员（96 个线程），最后一个 warp 只有 4 条 lane 干活，**另外 28 条 lane 每次启动都空转**。[【跳转到 11:22】](https://www.youtube.com/watch?v=3iTRA3Y8d-g&t=682)

![100 个线程的 block 仍占 4 个 warp，最后一个 warp 有 28 条 lane 长期空闲](assets/SIMT%20执行模型全解：Grid、Block、Warp%20与%2032%20线程的锁步执行/00682.webp)

这就是为什么大家习惯把 block size 取成 32 的倍数：64、128、256 都是好选择。

## 四、warp 分歧：一个分支要付两条路径的钱

既然 32 条 lane 共享一条指令流，那 `if-else` 就出问题了：一部分 lane 想走 if，另一部分想走 else，可**一条指令流没法同时跑两段代码**。这就是 **warp divergence（warp 分歧）**。[【跳转到 12:44】](https://www.youtube.com/watch?v=3iTRA3Y8d-g&t=764)

### 4.1 机制：先跑一条，把另一条掩掉

硬件的做法是**串行 + 掩码（mask）**：

1. 先跑其中一条分支，把没走这条分支的 lane **掩掉**（masked，暂时关闭）；
2. 再切换，跑另一条分支，掩掉上一批 lane。

顺序（先 if 后 else）只是示意，硬件不承诺固定顺序。

视频用一个具体条件演示：`if (threadIdx.x % 2 == 0)`，即 lane 编号为偶数走 if。16 条偶数 lane 想走 if，16 条奇数 lane 想走 else，32 条 lane 一起走到分支处，然后必须分裂。

**Phase A**：先跑 if 分支（记作 A），偶数 lane 亮绿，奇数 lane 变灰被掩掉。此刻只有半个 warp 在干有用活。[【跳转到 14:04】](https://www.youtube.com/watch?v=3iTRA3Y8d-g&t=844)

![Phase A：偶数 lane 执行 if 分支 A，奇数 lane 被掩码关闭](assets/SIMT%20执行模型全解：Grid、Block、Warp%20与%2032%20线程的锁步执行/00869.webp)

**Phase B**：掩码翻转，奇数 lane 跑 else 分支 B，偶数 lane 变灰。两条分支**一前一后，从未同时运行**。[【跳转到 14:54】](https://www.youtube.com/watch?v=3iTRA3Y8d-g&t=894)

![Phase B：掩码翻转，奇数 lane 执行 else 分支 B，偶数 lane 等待](assets/SIMT%20执行模型全解：Grid、Block、Warp%20与%2032%20线程的锁步执行/00894.webp)

### 4.2 代价是「加法」，不是「取大」

不分歧时，整条 warp 走同一条路径，只付一条分支的时间。分歧时，warp 的总时间约等于

$$
T_{\text{divergent}} \approx T_A + T_B
$$

是**两者之和**，不是两者取大。所以一个有分歧的分支，确实比单独走任何一条路径都慢——你把两条路径都付了钱。[【跳转到 15:19】](https://www.youtube.com/watch?v=3iTRA3Y8d-g&t=919)

![不分歧只付一条分支；分歧要付 A+B 两条分支的时间和](assets/SIMT%20执行模型全解：Grid、Block、Warp%20与%2032%20线程的锁步执行/00919.webp)

这个代价特别容易被忽略：代码完全正确，每条 lane 都算对了，输出看不出任何异常，**只有速度受损**。所以视频提醒：要么给 kernel 计时，要么直接对着分支推理，不能只看 profiler 的「正确性」信号。分歧是性能代价，有时是必要的，并不总是 bug。

## 五、SM 与延迟隐藏：warp 调度器为什么总有活干

warp 经常要等，通常是等内存数据。这段等待本来可能让整台机器闲置——只要 **SM（streaming multiprocessor，流多处理器）** 里还有别的就绪 warp，就不会。[【跳转到 16:53】](https://www.youtube.com/watch?v=3iTRA3Y8d-g&t=1013)

视频把 SM 画成一个大盒子，里面住着 4 条 warp（4 行）。蓝色表示 ready（有活可干），灰色表示 waiting（等数据）。SM 内部的 **warp scheduler（warp 调度器）** 挑一条 ready 的 warp 来跑：

1. warp 1 发起一次长延迟的 load，没有别的活可干，转灰等待；
2. 调度器立刻切到 ready 的 warp 2 并运行它——SM 没有闲置；[【跳转到 18:37】](https://www.youtube.com/watch?v=3iTRA3Y8d-g&t=1117)
3. 时间过去，warp 3 也发起 load 并 stall，两条 warp 在等；调度器再切到 warp 4；
4. 只要还有一条 ready 的 warp，SM 就有活干——这是「always-has-work」循环；
5. warp 1 的数据回来，重新变蓝；warp 3 的数据也回来；warp 2 又有了新活；warp 4 跑完回到 ready；
6. 四条 warp 全部重新变蓝，回到起点，循环可以再来一遍。

![warp 1 等内存时，调度器切到 ready 的 warp 2，SM 不闲置](assets/SIMT%20执行模型全解：Grid、Block、Warp%20与%2032%20线程的锁步执行/01117.webp)

这套机制有个正式名字：**latency hiding by oversubscription（靠超额订阅隐藏延迟）**。latency 是等内存的时间；oversubscription 是让 SM 上驻留的 warp 数**多于**同时能运行的 warp 数。因为有多余的，一条 stall 时通常总能找到另一条 ready 的。**内存延迟并没有消失，只是被别的 warp 的有用工作遮住了。**[【跳转到 21:31】](https://www.youtube.com/watch?v=3iTRA3Y8d-g&t=1291)

![延迟隐藏靠超额订阅：驻留 warp 多于同时可运行数，等待被别的 warp 遮住](assets/SIMT%20执行模型全解：Grid、Block、Warp%20与%2032%20线程的锁步执行/01291.webp)

反过来，如果只启动一条 warp 呢？它发起 load 后 stall，调度器**无人可切**，整个 SM 就干等内存——延迟隐藏彻底失效。[【跳转到 22:01】](https://www.youtube.com/watch?v=3iTRA3Y8d-g&t=1321)

![SM 里只有 1 条 warp 时，它等内存就没有别的 warp 可切，整个 SM 闲置](assets/SIMT%20执行模型全解：Grid、Block、Warp%20与%2032%20线程的锁步执行/01321.webp)

那驻留多少条 warp 取决于什么？视频给了两个因素：**每个 block 有多大**，以及**每个 block 占用了多少 SM 有限的片上资源**。它并不只取决于 block 的数量。

## 六、动手推演：用纸笔预测掩码

视频最后给了一个极其实用的练习法：**在跑代码之前，先在纸上预测硬件会怎么做**。方法是把每个 `threadIdx.x` 代入分支条件，逐 lane 标 true / false；如果两组都存在，warp 就分歧。

**Lab 1**：条件 `threadIdx.x < 20`。lane 0～19 为 true（20 条），lane 20～31 为 false（12 条），两组都存在 → 分歧。注意边界：lane 19 是 true，lane 20 是 false。

**Lab 2**：条件 `(threadIdx.x / 8) % 2 == 0`，整数除法。按 8 条一组分带：

- lane 0～7：$0/8=0$，偶数 → true
- lane 8～15：$8/8=1$，奇数 → false
- lane 16～23：$16/8=2$，偶数 → true
- lane 24～31：$24/8=3$，奇数 → false

于是 warp 分成 4 个 8 条的带，两真两假 → 分歧。[【跳转到 24:24】](https://www.youtube.com/watch?v=3iTRA3Y8d-g&t=1464)

![Lab 2：把 threadIdx.x 逐一带入 (threadIdx.x / 8) % 2 == 0，判断哪些 8 条带为真](assets/SIMT%20执行模型全解：Grid、Block、Warp%20与%2032%20线程的锁步执行/01489.webp)

视频特别点名一个常见错误：**靠感觉猜分歧，而不是逐 lane 算条件**，出错几乎总在边界 lane 上（比如「小于 20」的最后一条 true 是 19 还是 20？答案是 19）。

## 小结

- **一行启动代码 = 一群有结构的线程**：`<<<blocks, threads>>>` 决定总量，并行是你主动设计的，编译器不会替你找。
- **三级逻辑层级**：grid → block → thread；线程用 `blockIdx.x × blockDim.x + threadIdx.x` 算出唯一数据下标，只写 `threadIdx.x` 会让所有 block 撞在同一批格子上。
- **warp 是硬件调度的真正单位**：32 条 lane 共享一条指令流、锁步推进；block 被切成整数个 warp，block size 不是 32 的倍数就会白白浪费 lane。
- **分歧的代价是加法**：一个 warp 同时只能处于一条指令，分支分裂后两条路径串行执行，$T \approx T_A + T_B$，而且是「结果正确、速度受损」的隐形代价。
- **延迟隐藏靠超额订阅**：SM 驻留多条 warp，一条 stall 就切到另一条 ready 的；warp 太少，这套机制立刻失效。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| grid | 一次 kernel 启动的全部线程，层级最顶层 |
| block | grid 的组成单位，块内线程可协作、可同步 |
| thread | 最小逻辑单位，用坐标算出自己负责的数据下标 |
| warp | 硬件调度单位，固定 32 条 lane 共享一条指令流 |
| lane | warp 里的一条通道，对应一个线程的执行位 |
| lockstep | 整个 warp 一起推进同一指令的锁步执行方式 |
| warp divergence | warp 内线程走不同分支，两条路径被迫串行 |
| masking | 把不参与当前分支的 lane 暂时关闭的机制 |
| SM | streaming multiprocessor，持有并切换多条 warp 的硬件单元 |
| latency hiding | 用其他 ready warp 的工作遮住内存等待时间 |
| oversubscription | 让驻留 warp 数多于同时可运行数，制造可切换的备胎 |