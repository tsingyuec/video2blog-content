# Bank Conflict 实测与填充技巧：从 2 个时钟周期到 79 个

> 视频来源：[NVIDIA CUDA Tutorial 9: Bank Conflicts](https://www.youtube.com/watch?v=CZgM3DEBplE)（YouTube · Creel）｜时长约 24.1 分钟
> 导读：这支视频只讲一件事——shared memory 的 bank conflict。它先把 32 个 bank 的物理组织讲清楚，再把几种访问模式的代价用 `clock()` 真测出来（2 / 4 / 6 / 21 / 79 个时钟周期），最后用填充把最坏情况修回最快情况。原片是课堂录屏，口语较随意，本文按「组织 → 模式 → 实测 → 何时不必管」复述。

## 本讲要解决的核心问题（SCQA）

**背景**：shared memory 几乎总是比 global memory 快，所以我们把热数据搬进片上暂存区，指望它稳定地快。

**冲突**：但有些访问模式下它会慢得相当夸张。同一个 warp 的 32 个线程去读 shared memory，访问模式不同，实测耗时可以从 **2 个时钟周期**涨到 **79 个时钟周期**——差了近 40 倍，而源码里只是下标表达式换了个乘数。

**疑问**：到底什么样的访问模式会触发 bank conflict？怎么改才能避开？

**回答（中心思想）**：shared memory 被切成 32 个 bank，只要**一个 warp 内没有两个线程从同一个 bank 读不同的 word**，就是最快的一档；一旦出现冲突，最常用的修法是把「偶数个 word」的结构或行宽**加一个 word 的填充**改成奇数，让 32 个 lane 重新摊到 32 个 bank 上。

## 一、先复习 warp：32 个线程一组，锁步执行

一个 thread block 里的线程会被切成 32 个一组，每组叫一个 **warp**。同一个 warp 里的线程有着连续的 `threadIdx.x`，由 SM 里的执行单元以 SIMD 方式执行——只要不遇到分支，它们就一起往前走。

一旦遇到 `if` 这类分支，一部分线程走一条路、另一部分走另一条路，warp 就被拆开，先执行走第一条路的那批线程，再执行走另一条路的那批。这就是 CUDA 里分支可能非常昂贵的原因：warp 被切碎、串行执行。

还有一条容易搞错的事实：**warp 从不跨 block 创建**。你不会遇到「16 个线程属于这个 block、16 个属于那个 block」凑成一个 warp 的情况。

[【跳转到 00:28】](https://www.youtube.com/watch?v=CZgM3DEBplE&t=28)

## 二、shared memory 的物理组织：4 字节 word 与 32 个 bank

### 2.1 64 KB 的 shared/L1 被切成 4 字节的 word

每个 SM 上有 64 KB 的 shared memory / L1，它被切成一个个 4 字节的区域，叫做 **word**。4 字节可以装一个 32 位 int、一个 float、两个 short，或者半个 double，装什么无所谓；通常按小端排列，一个 word 的第一个字节是最低有效字节。

[【跳转到 02:19】](https://www.youtube.com/watch?v=CZgM3DEBplE&t=139)

![shared memory 的物理组织：64 KB 的 shared/L1 被切成 4 字节的 word（Word 0、Word 1……），每个 word 属于一个 bank](assets/Bank%20Conflict%20实测与填充技巧：从%202%20个时钟周期到%2079%20个/00189.webp)

### 2.2 规则：word $i$ 属于 bank $i \bmod 32$

shared memory 一共有 **32 个 bank**，每个连续的 word 属于下一个 bank：word 0 属于 bank 0，word 1 属于 bank 1……一直到 word 31 属于 bank 31，然后 **word 32 又回到 bank 0**。

换句话说：bank 0 拥有所有下标能被 32 整除的 word；bank 1 拥有所有除以 32 余 1 的 word；bank 2 的 word 除以 32 余 2，依此类推。注意这里说的是 **word 地址**，不是字节地址。

[【跳转到 03:34】](https://www.youtube.com/watch?v=CZgM3DEBplE&t=214)

![bank 的划分：bank 0 拥有下标 0、32、64、96……，bank 1 拥有 1、33、65……，word 下标除以 32 的余数就是 bank 号](assets/Bank%20Conflict%20实测与填充技巧：从%202%20个时钟周期到%2079%20个/00361.webp)

### 2.3 两个容易忽略的细节

**shared memory 总是整字读**。即使你的线程只要一个字节，shared memory 也会把整个 4 字节 word 读出来，再把你要的那个字节给你。如果你要的是一个「错位」的 word（低半和高半分属不同 bank），那就得发两次 bank 请求。

**数组首元素落在哪个 bank，你其实不确定**。比如一个 1024 个元素的 shared 数组，从 block 内部你无法确定它的第一个元素落在哪个 bank。不过这通常不影响结论。

另外，在 **pre-Fermi** 的老卡上只有 **16 个 bank**，那种卡要考虑的是「半个 warp」（16 个线程）。本讲不涉及。

[【跳转到 04:46】](https://www.youtube.com/watch?v=CZgM3DEBplE&t=286)

## 三、三种「快」的模式

一个 warp 请求的地址可以是 32 个 bank 的任意排列：从「32 个线程全要 bank 0」到「32 个线程全要 bank 31」，中间什么组合都有，完全取决于程序员怎么写。其中有三类是快的。

### 3.1 broadcast：所有线程读同一个值

如果 warp 里每个线程读的是**完全相同**的那个值，shared memory 只读一次，然后把值广播给所有线程——没有 bank conflict，非常快。

三种常见的「天然 broadcast」写法：

```cuda
arr[threadIdx.x * 0]   // 恒为 0：同一个地址
arr[12]                // 常量下标：同一个地址
arr[blockIdx.x * 3]    // 同一个 warp 内 blockIdx.x 相同，算出来也是同一个地址
```

[【跳转到 08:26】](https://www.youtube.com/watch?v=CZgM3DEBplE&t=506)

![broadcast：warp 内所有线程读同一个值（例如 arr[threadIdx.x*0]、arr[12]、arr[blockIdx.x*3]），只读一次再广播，没有冲突](assets/Bank%20Conflict%20实测与填充技巧：从%202%20个时钟周期到%2079%20个/00581.webp)

### 3.2 multicast：多个线程读同一个 word

还有一类很快的操作叫 **multicast**（compute capability 2.0 起支持）：不管多少个线程读某个 bank 里的**同一个 word**，shared memory 只读一次，然后把值分发给需要它的线程。比如 5 个线程读 bank 2 的 word 0，另外 5 个线程读 bank 30 的某个 word，只要每个 bank 里被读的是**同一个 word**，就没问题。

### 3.3 一 lane 一 bank：`arr[threadIdx.x]`

最自然也最快的写法是用 `threadIdx.x` 直接当下标：32 个线程各读一个 word，正好落在 32 个不同的 bank 上，一趟读完。它的速度和 broadcast 完全一样——broadcast 不比它快，它也不比 broadcast 慢。

[【跳转到 10:03】](https://www.youtube.com/watch?v=CZgM3DEBplE&t=603)

## 四、冲突：同一个 bank 里的不同 word

### 4.1 定义只有一句话

**只要两个或更多线程从同一个 bank 读不同的值，就是 bank conflict。** 前面说的 broadcast 和 multicast 都要求「同一个 word」，一旦同一个 bank 里出现了第二个不同的 word，就冲突了。

### 4.2 2-way conflict：`arr[threadIdx.x * 2]`

最典型的两路冲突来自 stride 2：

```cuda
arr[threadIdx.x * 2]   // 每个线程读的下标是 threadIdx.x 的两倍
```

32 个线程全部落在**偶数 bank** 上，奇数 bank 完全闲着——每个 bank 被两个线程要不同的 word，所以读的耗时翻倍。什么时候会写出这种代码？当你处理 **double**（一个 double 占两个 word）、**两个 float 的结构体**、或者任何 **8 字节**的数据结构，并且每个线程访问数组里连续的一个元素时。

代价不算大：从 shared memory 读进寄存器这一步会花掉两倍的时钟周期。

[【跳转到 10:36】](https://www.youtube.com/watch?v=CZgM3DEBplE&t=636)

![2-way bank conflict：threadIdx.x*2 让 32 个线程全落在偶数 bank（图中红色格子），奇数 bank 闲置，每个 bank 被要两个不同的 word](assets/Bank%20Conflict%20实测与填充技巧：从%202%20个时钟周期到%2079%20个/00636.webp)

### 4.3 一个意外的好消息：3 个 word 的结构反而无冲突

如果结构体是 3 个 word（12 字节），比如一个 x、y、z 都是 float 的三维点，那么 `arr[threadIdx.x * 3]` 的访问模式**完全没有 bank conflict**——因为 3 与 32 互质，相邻线程会依次错开 3 个 bank，正好铺满 32 个 bank。

不过讲者提醒：实际测下来，这种 3 word 结构未必比 double 快，具体要看卡。理论只是理论，测一测才知道。

[【跳转到 11:26】](https://www.youtube.com/watch?v=CZgM3DEBplE&t=686)

### 4.4 4-way conflict：`arr[threadIdx.x * 12]`

真正糟糕的是 stride 12：

```cuda
arr[threadIdx.x * 12]   // 48 字节的结构体，每个线程访问连续一个
```

每第 4 个 bank 被要 4 个不同的值，中间三个 bank 完全没被用到——这是 **4-way bank conflict**，一次读要花四趟。

[【跳转到 12:16】](https://www.youtube.com/watch?v=CZgM3DEBplE&t=736)

![4-way bank conflict：threadIdx.x*12 让每第 4 个 bank 被要 4 个不同的值（红色格子），中间三个 bank 闲置](assets/Bank%20Conflict%20实测与填充技巧：从%202%20个时钟周期到%2079%20个/00761.webp)

### 4.5 修法：把 12 改成 13

给结构体**多加一个 word 的填充**，把下标乘数从 12 改成 13：

```cuda
arr[threadIdx.x * 13]   // 13 与 32 互质，32 个 lane 摊到 32 个 bank
```

访问模式立刻从 4-way conflict 变成零冲突，每个 bank 都被要到一个值，速度回到 broadcast 那一档。这就是本讲最重要的一条经验：**把结构体的 word 数从偶数改成奇数**。

[【跳转到 13:19】](https://www.youtube.com/watch?v=CZgM3DEBplE&t=799)

![填充后的访问模式：把 48 字节结构体填充到 52 字节，下标乘数从 12 变成 13，32 个 lane 沿对角线摊开，每个 bank 各被要一次](assets/Bank%20Conflict%20实测与填充技巧：从%202%20个时钟周期到%2079%20个/00799.webp)

## 五、实测：`clock()` 量出来的数字

讲者写了一个小测试程序，只启动**一个 warp（32 个线程）**，用 CUDA 的 `clock()` 设备函数在 shared memory 读写前后各取一次时钟计数，差值就是这次访问花掉的时钟周期。

```cuda
__global__ void MyKernel(unsigned long long* time) {
    __shared__ float shared[1024];
    unsigned long long startTime = clock();
    shared[threadIdx.x * 2]++;          // 换不同的访问模式
    unsigned long long finishTime = clock();
    *time = (finishTime - startTime);
}
```

两个实用细节：每种模式都跑 10 次取一个稳定值；如果之后要用 profiler，程序结束时要调用 `cudaDeviceReset()`，因为设备是在执行它之后才把性能指标写出来的。

[【跳转到 17:24】](https://www.youtube.com/watch?v=CZgM3DEBplE&t=1044)

![用 clock() 计时的小 kernel：在 shared memory 访问前后各取一次 clock()，差值写回 time；这里测的是 shared[threadIdx.x*2]++ 的两路冲突](assets/Bank%20Conflict%20实测与填充技巧：从%202%20个时钟周期到%2079%20个/01173.webp)

### 5.1 五种访问模式的实测结果

| 访问模式 | bank 情况 | 实测时钟周期 |
| --- | --- | --- |
| `shared[0]`（broadcast） | 全部读同一个 word | 2 |
| `shared[threadIdx.x]` | 一 lane 一 bank | 4 |
| `shared[threadIdx.x * 2]` | 2-way conflict | 6 |
| `shared[threadIdx.x * 8]` | 4-way conflict | 21 |
| `shared[threadIdx.x * 32]` | 32-way conflict | 79 |

几个值得注意的点：

- broadcast 只要 **2 个时钟周期**；`threadIdx.x` 是 **4 个**，多出来的两个是稍复杂的地址计算开销。这两档都属于「没有冲突」。
- 两路冲突是 **6 个**，讲者的评价是「还行，能忍」，因为实际运行时同时有多个 warp，冲突的延迟往往被掩盖。
- 跳到 `* 8` 就变成 **21 个**，差距开始明显。
- 最坏的是 `* 32`：每个线程都从 bank 0 读**不同**的值，32 路冲突，实测 **79 个时钟周期**——和刚才的 4 个周期比，这是灾难性的。

[【跳转到 18:59】](https://www.youtube.com/watch?v=CZgM3DEBplE&t=1139)

[【跳转到 20:02】](https://www.youtube.com/watch?v=CZgM3DEBplE&t=1202)

![实测输出：32 路 bank conflict 下每次 shared memory 访问要 79 个时钟周期，控制台里连续十行都是 Time: 79](assets/Bank%20Conflict%20实测与填充技巧：从%202%20个时钟周期到%2079%20个/01218.webp)

### 5.2 结构体实验：11 个周期，加一个填充回到 4

讲者接着把 float 数组换成一个 4 个 float 的结构体（相当于一个 4 维点，x、y、z、w），每个线程访问 `shared[threadIdx.x]`。因为每个元素占 4 个 word，这等价于 `threadIdx.x * 4`，应当出现冲突。

实测是 **11 个时钟周期**——不算太糟，但离「2 或 4」这一档还差得远，说明里面确实有冲突。

然后给结构体加一个填充字段，让它从 4 个 word 变成 5 个 word：

```cuda
struct Pehw {
    float x, y, z, w;
    float padding;      // 加这一个 word，4 -> 5
};
```

再测，回到 **4 个时钟周期**。就这么简单。

[【跳转到 21:58】](https://www.youtube.com/watch?v=CZgM3DEBplE&t=1318)

![给 4 个 float 的结构体加一个 padding 字段，结构体从 4 个 word 变成 5 个 word，访问模式从冲突变回零冲突](assets/Bank%20Conflict%20实测与填充技巧：从%202%20个时钟周期到%2079%20个/01356.webp)

### 5.3 规律会重复：64、128 个 word 的结构体一样惨

讲者补充了一条幻灯片里没写的规律：这个模式是**周期性重复**的。如果结构体是 64 个 word 长，效果和 32 个 word 一样；128 个 word 也一样——只要长度是 32 的倍数，就永远是 32 路冲突，直到你加上那一个填充 word 把它变成奇数。

[【跳转到 22:46】](https://www.youtube.com/watch?v=CZgM3DEBplE&t=1366)

![结构体长 32 个 word 时每个线程都落在同一个 bank；长度是 32 的倍数（64、128……）时同样如此，加一个填充 word 才能打破](assets/Bank%20Conflict%20实测与填充技巧：从%202%20个时钟周期到%2079%20个/01391.webp)

## 六、什么时候其实不必管它

这一节是整支视频最容易被忽略、但也最实用的部分。

### 6.1 少量冲突的影响很小

讲者自己说：他费了很大劲画图解释 bank conflict，但**很多时候这点延迟被完全掩盖了**，根本不是瓶颈。shared memory 的读写本来就非常快，即使有两三个 bank conflict 也一样。所以：先在代码里试试加填充、改访问模式，看有没有变快；如果没变快，就别硬改。

### 6.2 单 warp 测试会夸大影响

他的测试只启动一个 warp，这「不是最实际的例子」。真实 kernel 里同时有多个 warp 在跑，bank conflict 造成的性能下降往往远没有测试里那么夸张。

### 6.3 先问 profiler：你到底是不是 shared memory 受限

正确的做法是用 profiler 判断你的 kernel 到底受限于什么：是 shared memory、是算术、还是 global memory 读。如果瓶颈不在 shared memory，改 bank conflict 一点用都没有。

另外，**block 之间不存在 bank conflict**：一个 block 从 bank 0 读一个值、另一个 block 同时从 bank 0 读另一个值，不会有任何冲突。冲突只在 warp 级别讨论。

[【跳转到 13:44】](https://www.youtube.com/watch?v=CZgM3DEBplE&t=824)

[【跳转到 14:34】](https://www.youtube.com/watch?v=CZgM3DEBplE&t=874)

## 小结

- 一个 warp 是 32 个线程，锁步执行；分支会把 warp 拆开串行，warp 从不跨 block。
- shared memory 由 4 字节的 word 组成，**word $i$ 属于 bank $i \bmod 32$**；它总是整字读，错位的 word 要两次请求。
- 三档最快：broadcast（全读同一个值）、multicast（多线程读同一个 word）、一 lane 一 bank（`arr[threadIdx.x]`）。
- 冲突的定义只有一句：**两个以上线程从同一个 bank 读不同的 word**。
- 实测代价：broadcast 2、一 lane 一 bank 4、2-way 6、4-way 21、32-way 79 个时钟周期。
- 修法是填充：把结构体或行宽从**偶数个 word 改成奇数个**（12→13、4→5），让 32 个 lane 重新铺满 32 个 bank。
- 长度是 32 的倍数的结构体永远是 32 路冲突；规律在 64、128 个 word 时重复。
- 但先别急着改：少量冲突的延迟常被掩盖，单 warp 测试会夸大影响；用 profiler 确认瓶颈是不是 shared memory 再说。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| warp | 一个 block 里 32 个连续 `threadIdx.x` 的线程组，锁步执行 |
| word | shared memory 的基本单元，4 字节；bank 号按 word 下标算，不按字节 |
| bank | shared memory 被切成的 32 个可并行访问的单元，word $i$ 落在 bank $i \bmod 32$ |
| bank conflict | 一个 warp 内两个以上线程从同一个 bank 读**不同**的 word，只能串行 |
| broadcast | warp 内所有线程读同一个值，只读一次再分发，不算冲突 |
| multicast | 多个线程读同一个 bank 里的**同一个 word**，只读一次再分发 |
| n-way conflict | 同一个 bank 里被要了 n 个不同的 word，这次访问要花 n 趟 |
| padding（填充） | 给结构体或数组行宽多加一个 word，把偶数 word 数改成奇数，从而摊开 bank |
| `clock()` | CUDA 设备函数，返回时钟计数，用来测一段 shared memory 访问花了多少周期 |
| `cudaDeviceReset()` | 程序结束时调用，设备才会把 profiler 需要的性能指标写出来 |