# Memory Workload Analysis：从 cache line 与 sector 看访存效率

> 视频来源：[Memory Analysis with NVIDIA Nsight Compute](https://www.youtube.com/watch?v=GCkdiHk6fUY)（YouTube · NVIDIA Developer，讲者 Maximilian，NVIDIA 开发者技术部门）｜时长约 18 分钟
> 简要导读：这是 NVIDIA 官方「CUDA Developer Tools」系列里讲 Nsight Compute **Memory Workload Analysis（内存工作负载分析）** 的一集。它先花一半时间讲清 cache line 与 sector 的粒度，再用一个「RGBA 转灰度」的小内核做四轮迭代：纵向读 → 横向读 → 一线程多值 → 向量化读写，每一轮都拿报告里的数字说话。字幕为 YouTube 自动生成，术语已订正（sector / cache line / LSU / spilling 等）。

## 本讲要解决的核心问题（SCQA）

**背景**：GPU 工作负载经常是**重度访存受限**的，而计算量还在不断增长。内容创作类应用尤其典型：视频帧在内存里流过，有时只做一个调色滤镜。所以「把内存带宽用满、把数据访问模式调好」往往比优化算术更值钱。

**冲突**：麻烦在于，SOL 段会骗人——不是它算错了，而是它的前提被违反了。Nsight Compute 只有在**算法本身确实被硬件限制**时，才能给出正确的 SOL 测量值；它无法告诉你「你的处理方式是否次优、是否做了多余的事」。视频里的例子非常刺眼：一个内核的 Memory SOL 达到 81.28%，看起来「内存带宽快用满了，很棒」，可实际上它只是**把 32 字节的 sector 当成 4 字节来用**——读 1 个字节也要搬 32 个字节。带宽确实用满了，但用的是废带宽。

**疑问**：那怎么看出「带宽用满了但用错了」？内存分析图里的箭头、字节数、命中率分别该怎么读？为什么纵向读一张图会慢 8 倍？为什么「一个线程处理 4 个像素」这种看起来很对的优化几乎没收益？

**回答（中心思想）**：读内存分析的关键是**始终带着「粒度」这个尺子**。GPU 上最小的通信单位是 **sector（32 字节）**，缓存分配单位是 **cache line（128 字节 = 4 个 sector）**；你请求 1 个字节，硬件也至少搬 32 字节、至少占 128 字节的 cache line。于是衡量访存效率的核心指标就是「**每次请求实际用到多少字节 / 硬件搬了多少字节**」，Nsight Compute 把它算成 `sectors per request`（理想值是 1.0）。案例里纵向读是 **31.8 sectors/request**，改成横向读降到 **4.0**，耗时从 324.22 微秒降到 42.85 微秒（−86.78%）；而「一个线程处理 4 个值」之所以没收益，是因为它减少的是**请求数**，没减少**sector 数**。

---

## 一、内存分析图：绿色是软件地址空间，蓝色是硬件单元

Memory Workload Analysis 段的核心是一张 **Memory Chart（内存图）**。

[【跳转到 00:59】](https://www.youtube.com/watch?v=GCkdiHk6fUY&t=59)

![内存图的两类元素：绿色方框是软件侧的逻辑地址空间（Global、Local、Texture、Surface、Load Global Store Shared、Shared），蓝色方框是硬件物理单元（L1/TEX Cache、L2 Cache、System Memory、Device Memory、Peer Memory、Shared Memory），箭头上的数字是这条连线上读写的字节数](assets/Memory%20Workload%20Analysis：从%20cache%20line%20与%20sector%20看访存效率/00084.webp)

图里有两类元素，颜色就是图例：

| 颜色 | 含义 | 例子 |
| :--- | :--- | :--- |
| 绿色 | 软件侧的逻辑单元（地址空间） | Global、Local、Texture、Surface、Shared |
| 蓝色 | 硬件物理单元 | L1/TEX Cache、L2 Cache、Device Memory、Shared Memory |

箭头连线表示物理单元之间**读写的字节数**；箭头的**颜色**反映我们离这条互连的峰值吞吐有多远（右侧有 0%–100% 的色标）。通过下拉菜单 `Show As`，可以在「总字节数（Transfer Size）」与「峰值吞吐百分比」两种标注之间切换。

图里还直接标了两个命中率：`L1/TEX Cache` 下方的 `Hit Rate: 61.43%` 和 `L2 Cache` 下方的 `Hit Rate: 93.81%`。这两个数字是后面所有分析的主角。

一次内存请求的路径在图上是这样的：内核发出请求 → 查地址背后的那个 **sector** 是否已在 L1 → 不在就落到 L2 再查 → 都不在就从设备内存取。

这里有一个必须记住的结构性事实：**L2 是所有 SM 的「真相之源」**。所有内存流量都必须经过 L2，包括 PCIe 拷贝和设备内存写。只有当要读的 sector 已经在 L1 里时，才不经过 L2。原因也很清楚：L2 是全 GPU 共享的，L1 只属于一个 SM；L2 保证没有 SM 会读到「尚未写回设备内存的无效数据」。

于是「减少流量」有两条正交的路：

- 提高 **L2 命中率** → 减少 L2 与设备内存之间的流量；
- 提高 **L1 命中率** → 减少 L1 与 L2 之间的流量；
- 还有第三条更根本的：**改算法，让需要搬运的数据本身变少**。

这些命中率之所以重要，是因为**从设备内存取数据要花很多周期**——命中得越早，延迟越低。

---

## 二、粒度：cache line 是 128 字节，sector 是 32 字节

要理解命中率怎么算，先得知道各单元之间**以什么粒度通信**。

[【跳转到 03:04】](https://www.youtube.com/watch?v=GCkdiHk6fUY&t=184)

![cache line 与 sector 的关系：L1 和 L2 里的 cache line 是 128 字节，由 4 个 32 字节的 sector 组成；GPU 上任何通信都以 sector 为单位](assets/Memory%20Workload%20Analysis：从%20cache%20line%20与%20sector%20看访存效率/00232.webp)

- **cache line = 128 字节**，是 L1 和 L2 里的分配单位；
- **sector = 32 字节**，是 GPU 上任何通信的最小单位。新硬件上一次可以传不止一个 sector，但单个 sector 仍是最小粒度。

「分配单位」这个词是理解一切的关键：**我们不能只分配单个 sector，而总是分配整条 cache line**，读的时候再把连续的 sector 填进去。所以哪怕你只读 4 个字节，占用的也是 128 字节的缓存空间。

视频用一个极简的例子说明这件事的后果：假设缓存只能放 2 条 cache line，现在读一张每行超过 128 字节的图。

- **按列读**：读第一行第一个元素、第二行第一个元素，各分配一条 cache line；再读第三行时，就必须淘汰一条才能读下一个，之前那些 cache line 一个都复用不上。这实际上把可用缓存容量降到了 **25%**。
- **按行读**：读满一条 cache line 再读下一条，读完两条同样要淘汰，但**能留住多得多的 sector**，也就留住更多数值更久。而且当预取更宽（一次传 2 个 sector）时，延迟也会改善。

这套解释对 L2 和 L1 都成立。

---

## 三、命中率怎么算：两个极端例子

视频给了两个可以直接心算的例子，把「命中率」和「粒度」绑在一起：

| 访问模式 | L1 命中率 | L2 命中率 | 原因 |
| :--- | ---: | ---: | :--- |
| 一个 SM 里连续读 32 字节 | 97% | 0% | 只向 L2 发了一次请求，之后数据都在 L1，后续请求全命中 |
| 按 32 字节跨步读（每个 sector 只取第一个值） | 0% | 每读 4 个值才重新分配一条 cache line | L1 里没有任何可复用的数据 |

第二个例子值得细看：按 32 字节跨步读时，**每个 sector 里只用了第一个值**，其余 28 字节全浪费。L2 那边因为一条 cache line 覆盖 4 个 sector，所以每读 4 个值才需要重新分配一条 cache line——但（假设没有预取）**每次请求都得向设备内存要数据**。

这就是「带宽用满但用错了」的数学形态：sector 数不变，有用字节数只有 1/8。

---

## 四、shared memory 与 local memory：两个特殊角色

**shared memory** 是每个 SM 的片上内存，本质上就是 L1 内存，区别是它**不会被写回设备内存**，而是当作工作区使用。申请 shared memory 会减少可用的 L1 容量。它的价值在于：让同一个 SM（CTA）里的所有线程共享数据，而**不必经过 L2**；当自动缓存达不到预期时，这也是手动管理 L1 的有效手段。

Ampere 引入了 `LDGSTS`（Load Global Store Shared）指令，可以**绕过非托管的 L1**，把数据直接从全局内存读进 shared memory。视频顺带提了一个常见套路：先把数据预载到 shared memory 是**滑动窗口类算子（比如卷积）**的标准做法——用 CTA 里所有线程一起预载，之后其他线程再访问，例如让权重常驻在 L1 里。

**local memory** 则完全相反：**任何 local load/store 通常都是我们想消除的东西**。它的来源往往是**寄存器溢出（register spilling）**——内核没能力把工作数据留在物理寄存器堆里，只能写回内存。视频原话是「这对性能影响非常大」。

要定位这些 local 操作，有两条路：

1. 看内存图里 **Local 这一行**的指令数/请求数；
2. 用 Nsight Compute 的 **Source 页面**去找 `LDL` 与 `STL` 指令，能精确定位到是哪一行代码产生的 local 访问。

内存图里所有绝对值都列在图下方的表格里。图是给「形状」的，表是给「数字」的。

---

## 五、案例：RGBA 转灰度，纵向读的灾难

示例程序很简单：把一张 8 位 PNG 从 RGBA 转成灰度。内核读 4 个连续像素值（RGBA 四个通道），各乘一个系数后相加得到一个灰度 float，再降位写回输出缓冲。

[【跳转到 08:49】](https://www.youtube.com/watch?v=GCkdiHk6fUY&t=529)

![示例内核 rgba2grayscale：每个线程算一个像素，按 idx_y * in_pitch + idx_x * channel 取 4 个通道做加权求和，再 static_cast 成 uint8 写回；下面还有 multiple_values 与 wide 两个模板版本](assets/Memory%20Workload%20Analysis：从%20cache%20line%20与%20sector%20看访存效率/00529.webp)

剖析之前先算**理论值**，这一步是后面所有判断的基准：

| 项目 | 理论值 |
| :--- | :--- |
| 输入 | 4 通道 `uint8_t`，3840×2160 |
| 输出 | 1 通道 `uint8_t`，3840×2160 |
| 预期读 | 约 33.2 MB |
| 预期写 | 约 8.3 MB |

为什么要先算？因为视频反复强调一句话：**Nsight 能测出你离硬件上限有多远，但测不出你的处理方式是否次优**。只有先知道「应该搬多少」，才能判断「实际搬了多少」是否离谱。

### 5.1 第一眼：Memory SOL 81.28%

[【跳转到 10:52】](https://www.youtube.com/watch?v=GCkdiHk6fUY&t=652)

![纵向读版本的报告：Memory Throughput 81.28%、L1/TEX 51.61%、L2 81.28%、DRAM 12.13%，而 Compute (SM) 只有 3.72%；柱状图里 Memory 几乎顶满、Compute 只有一小截](assets/Memory%20Workload%20Analysis：从%20cache%20line%20与%20sector%20看访存效率/00652.webp)

| 指标 | 值 |
| :--- | ---: |
| Duration | 324.22 μs |
| Compute (SM) Throughput | 3.72% |
| Memory Throughput | 81.28% |
| L1/TEX Cache Throughput | 51.61% |
| L2 Cache Throughput | 81.28% |
| DRAM Throughput | 12.13% |

Memory SOL 81.28%，按 SOL 段的常规读法，这「通常说明内核性能不错」。但 Compute SOL 低得可疑——一个逐点操作不该这么低。再看内存图，问题就露出来了：

[【跳转到 11:42】](https://www.youtube.com/watch?v=GCkdiHk6fUY&t=702)

![纵向读版本的内存图：设备内存到 L2 的连线吞吐很低（颜色偏冷），但 L1/TEX 到 L2 之间流量高达 293.88 MB，远超逐点操作应有的量；L1 命中率 59.37%、L2 命中率 94.10%](assets/Memory%20Workload%20Analysis：从%20cache%20line%20与%20sector%20看访存效率/00677.webp)

- 设备内存那条连线的峰值吞吐**很低**（从颜色就能看出来）；
- 但 **L2 与 L1 之间的流量比这个逐点操作应有的量多得多**（293.88 MB）；
- L2 的缓存命中率看起来还极好（94.10%）。

「L2 命中率极高」在这里恰恰是坏消息：说明数据没怎么从设备内存搬，全在片上反复倒腾——而倒腾的量远超理论值。

### 5.2 病因：纵向读 256 个像素

视频把病因讲得很具体。一个 block 里**纵向读 256 个像素**，每个线程请求一个像素的数据。假设缓存未初始化：

1. 在 L2 和 L1 各分配一条 cache line（128 字节）；
2. 从全局内存把该像素所在的那个 **sector**（32 字节）载进来；
3. 因为纵向处理，一共请求了 **256 条 cache line、256 个 sector**；
4. 但只从这些 sector 里读了 $256 \times 4 = 1024$ 字节——**每个 sector 只用了 4 个字节**。

写灰度数据更糟：为了写数据请求 256 个 sector，**只写 1 字节，却要把整个 sector 写回**。

[【跳转到 12:29】](https://www.youtube.com/watch?v=GCkdiHk6fUY&t=749)

![写灰度值的代价：改 1 个字节也必须先把整个 sector 读进 L1/L2，改完再刷回去；L2 全 GPU 共享，所以只有内核退出后才真正写回设备内存](assets/Memory%20Workload%20Analysis：从%20cache%20line%20与%20sector%20看访存效率/00774.webp)

这张图说清了「写 1 字节」背后的实际动作：先读整个 sector → 改 1 个字节 → 再刷回。这种「读-改-写」在按列写的时候每个像素都要来一遍。

好消息是：这个问题的数据量小，能装进 L2，否则 L2 会向设备内存发出更多请求。也正因为如此，Nsight Compute 给出了明确的警告。

### 5.3 报告里的那句话：`sectors per request`

[【跳转到 13:09】](https://www.youtube.com/watch?v=GCkdiHk6fUY&t=789)

![纵向读版本的 Memory Workload Analysis 表格：Memory Throughput 102.33 GB/s、Mem Busy 56.39%、L1/TEX Hit Rate 59.37%、L1 Hit Rate 81.28%、L2 Hit Rate 94.10%；底部 L1/TEX Global Load Access Pattern 显示 31.8 sectors per request，理想值 1.0](assets/Memory%20Workload%20Analysis：从%20cache%20line%20与%20sector%20看访存效率/00814.webp)

底部那条 `L1/TEX Global Load Access Pattern` 是整支视频里最该记住的一行：

> The memory access pattern for global loads in L1TEX might not be optimal. On average, this kernel accesses 1.0 bytes per thread per memory request; but the address pattern, possibly caused by the stride between threads, results in **31.8 sectors per request**, or 0.3*32 = 1016.5 bytes of cache data transfers per request. The optimal thread address pattern for 1.0 byte accesses would result in 1.0*32 = 32.0 bytes of cache data transfers per request, to maximize L1TEX cache performance.

翻译成一句话：**每个线程平均只用了 1 个字节，但一次请求牵动了 31.8 个 sector**（理想值是 1.0）。这正好对应上面「每 sector 只用 4 字节」的分析。

同一段里还有一个 `L2 Store Access Pattern` 的警告，说的是写侧：L1TEX 到 L2 的请求粒度是 128 字节的 cache line（4 个连续的 32 字节 sector），而这个内核平均只用了 4 个 sector 里的 1 个。

---

## 六、第二轮：按行读，快 8 倍

改法小得惊人：**把访问从按列改成按行，对这个处理来说只要改内核启动时的 block 维度即可**。视频预设了另一个优化级别，换个命令行参数启动就行。

先把当前这个未对齐的报告设为基线，再跑对齐版本：

[【跳转到 13:53】](https://www.youtube.com/watch?v=GCkdiHk6fUY&t=833)

![横向读版本与纵向读基线的对比：Duration 42.85 μs（−86.78%）、Compute 28.30%（+660.83%）、Memory 92.21%（+13.44%）、L1/TEX 29.09%（−43.64%）、L2 25.62%（−68.48%）、DRAM 92.21%（+660.04%）；底部 L1/TEX Global Load Access Pattern 变成 4.0 sectors per request](assets/Memory%20Workload%20Analysis：从%20cache%20line%20与%20sector%20看访存效率/00841.webp)

| 指标 | 纵向读（基线） | 横向读 | 变化 |
| :--- | ---: | ---: | ---: |
| Duration | 324.22 μs | 42.85 μs | −86.78% |
| Compute (SM) Throughput | 3.72% | 28.30% | +660.83% |
| Memory Throughput | 81.28% | 92.21% | +13.44% |
| L1/TEX Cache Throughput | 51.61% | 29.09% | −43.64% |
| L2 Cache Throughput | 81.28% | 25.62% | −68.48% |
| DRAM Throughput | 12.13% | 92.21% | +660.04% |
| L1 Hit Rate | 59.37% | 74.1% | +24.81% |
| Memory Throughput（带宽） | 102.33 GB/s | 774.32 GB/s | +656.69% |
| sectors per request | 31.8 | 4.0 | — |

**快了大约 8 倍。** 这张表最值得琢磨的是「谁涨谁跌」：

- **DRAM 吞吐涨了 6.6 倍**（12.13% → 92.21%）：现在真的在从设备内存搬数据了，而且搬到了接近峰值（774.32 GB/s）。
- **L2 吞吐反而跌了 68%**（81.28% → 25.62%）：因为不再需要那么多片上倒腾。
- **L1 命中率升到 74.1%**：因为我们把相邻像素的字节都请求到了。视频的原话是「75% 的 L1 命中率，因为把相邻像素的字节都请求到了」——4 个通道共 4 字节，一条 32 字节 sector 里装得下 8 个像素，所以 8 个里命中 7 个左右。
- **sectors per request 从 31.8 降到 4.0**：这是所有变化里最「因」的那个。

内存图也印证了：设备内存到 L2 的连线**非常接近峰值性能**，L2 到 L1 的加载量符合预期。

---

## 七、第三轮：一个线程处理 4 个值，为什么没收益

报告还告诉了我们一件事：这个内核是**重度访存延迟受限**的——每个像素都要等设备内存。这种情况下，「让一个线程处理多个值」是常见的应对手段（用更多在途请求掩盖延迟）。于是试了「一个线程处理 4 个像素」。

[【跳转到 14:56】](https://www.youtube.com/watch?v=GCkdiHk6fUY&t=896)

结果：**几乎没有收益**。细看内存图才发现原因：

- 到全局内存的**请求数没有下降**；
- L2 到 L1 的加载量也没降（这本来也不该指望）；
- 但 **L1 到 L2 的写却增加了**，而且和预期的 8 MB 对不上。

为什么写变多了？现在每个线程处理 4 个像素，但**每处理完一个像素就往图像里写 1 个字节**。这需要刷到 L2，于是人为地把 L1 到 L2 的吞吐抬高了——因为写的单位是 `uint8`，一次写过去的数据太少。同一时刻写同一个 sector 的线程可以被合并成一次写操作，但**为此等待的时间窗口非常短**。

这是一个很好的反面教材：**减少请求数 ≠ 减少 sector 数**。只要写入的粒度还是 1 字节，sector 的浪费就还在。

---

## 八、第四轮：向量化读写

最后一轮是**向量化加载**。

[【跳转到 15:55】](https://www.youtube.com/watch?v=GCkdiHk6fUY&t=955)

![向量化版本：左边用 uchar4 一次读入一个像素的 4 个通道，但仍写回单个 uint8；右边用 uint4 一次读入 4 个像素（16 字节），再用 union 把 4 个灰度值拼成 uchar4 一次写回](assets/Memory%20Workload%20Analysis：从%20cache%20line%20与%20sector%20看访存效率/00994.webp)

- 用 `uchar4` 一次读入一个像素的所有值（4 字节），但**仍然要写回单个 `uint8`**——写侧的浪费还在；
- 再放宽一点：一次读一个 `uint4`（16 字节 = 4 个像素），一个线程处理 4 个像素，再以 `uchar4` **一次写回 4 个字节**。这基本就是前面「多值内核」该有的样子，只是这次写也向量化了。

做这两种优化时都要注意一个副作用：**要保证还有足够的工作量**，不要把网格里的 block 数减到无法再打满 GPU。

重新剖析后：

| 指标 | 值 |
| :--- | ---: |
| Duration | 43.68 μs |
| Compute (SM) Throughput | 22.63% |
| Memory Throughput | 88.66% |
| DRAM Throughput | 88.66% |
| Memory Throughput（带宽） | 759.66 GB/s |
| Mem Busy | 38.33% |
| Max Bandwidth | 88.66% |
| L1 Hit Rate | 91.68% |
| L2 Hit Rate | 49.54% |

- 写回 L2 的量**回到了预期的 8 MB**；
- **Load/Store 单元（LSU）不再有压力，请求数减少了 90% 以上**；
- 计算 SOL 段也变好了——指针上的索引数学变少了。

但**内核并没有快多少**（43.68 μs vs 42.85 μs），因为前一个版本已经把我们**限制在设备内存上了**（DRAM 92.21%）。这又是一个 SOL 读法的例子：当 Memory SOL 已经接近 100%，再减少请求数也换不来时间。

---

## 九、这段报告的正确用法

视频的结论只有两句，但都是硬道理：

1. **确保你只加载真正需要的内存**——sector 是 32 字节，你请求 1 字节也搬 32 字节；
2. **让读访问对齐到 sector 甚至 cache line 边界**——这非常有益。

以及一个定位技巧：对齐问题在 **Source 段**里也有提示，配合源码关联可以定位内存停顿（那属于另一支教程）。

最后一句提醒值得抄下来贴在显示器上：**Nsight 能测出你离硬件上限有多远，但测不出你的算法是否次优**。所以永远先算理论值（该搬多少字节），再看实测（实际搬了多少），两者的差距才是优化空间。

---

## 小结

- Memory Workload Analysis 段的核心是 Memory Chart：绿色是软件地址空间，蓝色是硬件物理单元，箭头标的是字节数，箭头颜色标的是离峰值吞吐有多远。
- 粒度决定一切：**sector = 32 字节**是最小通信单位，**cache line = 128 字节 = 4 sector** 是缓存分配单位。请求 1 字节也至少搬 32 字节、占 128 字节。
- L2 是所有 SM 的「真相之源」，所有流量都经过它；L1 只属于一个 SM。提高 L2 命中率省的是「L2↔设备内存」流量，提高 L1 命中率省的是「L1↔L2」流量。
- 判断访存效率最直接的一行是 `sectors per request`（理想 1.0）：案例里 31.8 → 4.0，耗时 324.22 μs → 42.85 μs。
- 按列读一张图会把可用缓存容量降到 25%；按行读能留住更多 sector。
- `local` 访问（`LDL`/`STL`）通常来自寄存器溢出，是必须消除的东西；`shared memory` 是手动管理 L1 的手段，Ampere 起可用 `LDGSTS` 绕过 L1 直读。
- 「一个线程处理多个值」减少的是**请求数**，不减少 **sector 数**；只有把**写**也向量化（`uchar4` 写回），写侧的浪费才消失。
- 优化到 DRAM 接近峰值后（92.21%），继续减少请求数不再换来时间——这时的瓶颈已经是设备内存带宽本身。
- 永远先算理论字节数再看实测：SOL 只能告诉你「离硬件上限多远」，不能告诉你「算法是否次优」。

## 关键术语速查

| 术语 | 一句话解释 |
| :--- | :--- |
| Memory Workload Analysis | Nsight Compute 里专门分析访存行为的报告段，核心是 Memory Chart |
| Memory Chart | 内存图，绿色为软件地址空间、蓝色为硬件单元，箭头标注字节数与峰值占比 |
| sector | GPU 内存系统的最小通信单位，32 字节 |
| cache line | 缓存分配单位，128 字节，由 4 个 sector 组成 |
| Hit Rate | 命中率，L1 命中省的是 L1↔L2 流量，L2 命中省的是 L2↔DRAM 流量 |
| sectors per request | 一次内存请求平均牵动多少 sector，理想值 1.0，是访存效率的核心指标 |
| register spilling | 寄存器溢出，工作数据放不进寄存器堆只能写回内存，产生 local 访问 |
| `LDGSTS` | Ampere 引入的 Load Global Store Shared 指令，可绕过 L1 直读进 shared memory |
| LSU | Load/Store Unit，负责执行访存指令的单元 |
| read-modify-write | 改 1 个字节也要先读整个 sector、改完再写回，是窄写的隐藏代价 |