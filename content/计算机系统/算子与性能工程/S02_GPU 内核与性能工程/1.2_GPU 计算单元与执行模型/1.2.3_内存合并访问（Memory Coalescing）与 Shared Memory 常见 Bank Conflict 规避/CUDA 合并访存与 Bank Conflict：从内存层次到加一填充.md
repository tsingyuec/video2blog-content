# CUDA 合并访存与 Bank Conflict：从内存层次到加一填充

> 视频来源：[CUDA Memory Hierarchy: Coalescing, Shared Memory, Bank Conflicts — GPU Programming in C/CUDA | Ep 5](https://www.youtube.com/watch?v=LieS0bBgy0w)（YouTube · Glass Box Computing）｜时长约 27.7 分钟
> 导读：这是一门 CUDA 课程的第 5 部分，用动画把「内存金字塔 → 合并访存 → shared memory 与栅栏 → 32 个 bank 与 +1 填充 → constant memory 广播」一条线讲完。本文按原片顺序复述，重点补上初学者最容易漏掉的两条判据：一次读要花几个 sector、一个 warp 的 32 个 lane 落在几个 bank 上。

## 本讲要解决的核心问题（SCQA）

**背景**：到目前为止写的每个 kernel 都算对了，但「算对」不等于「跑得快」。绝大多数 kernel 是 memory-bound 的——它们的速度由字节到达的速度决定，而不是由芯片算得多快决定。

**冲突**：同一个 warp 的 32 个线程，只要把 `threadIdx.x` 从「沿行」改成「沿列」，数学上完全等价，速度却可能差好几倍；把 shared memory 的行宽从 32 改成 33，代码几乎没变，bank 冲突就消失了。这些差异在源码里看不出来，只体现在硬件怎么把 32 个 lane 的请求打包成事务。

**疑问**：怎么判断一次访存到底合不合并？shared memory 的 bank conflict 又该怎么规避？

**回答（中心思想）**：把两件事都还原成「数数」——global memory 上数**一个 warp 的请求落在几个 32 字节 sector 里**（越少越好，最好让 `threadIdx.x` 沿内存走）；shared memory 上数**一个 warp 的 32 个 lane 落在几个 bank 上**（一 lane 一 bank 最好，行宽是 32 的倍数时用 +1 填充错开）。

## 一、先定位：GPU 内存是一座金字塔，越往上越快、越窄

先看一眼 Roofline 图，就能明白这一讲为什么重要：横轴是 FLOPs per byte，对角线从原点升到脊点，之后是一条平的算力天花板。我们的向量加法 kernel 落在离天花板很远的左下方，深深待在 memory-bound 区域里——这一讲剩下的所有技巧，都是在把这个点往上推。

[【跳转到 01:46】](https://www.youtube.com/watch?v=LieS0bBgy0w&t=106)

![Roofline 图：向量加法 kernel 落在带宽对角线下方很靠左的位置，属于 memory-bound；本讲后续技巧都是把这个点往上推](assets/CUDA%20合并访存与%20Bank%20Conflict：从内存层次到加一填充/00106.webp)

顺带纠正一个常见直觉：**用「启动了多少线程」去猜 kernel 快不快是错的**。线程数完全说明不了一个 kernel 是不是 memory-bound；决定速度的是它每做一个有用的 FLOP 要搬多少字节。两个线程数相同的 kernel，只要一个搬的数据多得多，速度就可能差很远。

### 1.1 没有「一个内存」，只有一层层作用域不同的存储

GPU 并不是给你一块内存，而是给你一个层次结构：每一层有自己的速度，也有自己的**作用域**（谁能看见它）。越往上越快，作用域越窄；越往下越慢，作用域越宽。

- **寄存器（registers）**：属于**单个线程**，是放一个值最快的地方。
- **shared memory 与 L1 cache**：两者共用同一块片上 SRAM。shared memory 是**每个 block** 的，由你手工管理；L1 是**每个 SM** 的缓存，硬件自动填充和淘汰。
- **L2 cache**：属于整个 GPU，所有 SM 共享。
- **global memory（也就是显存 VRAM）**：属于整个 GPU，最慢，作用域最宽。课程用的 NVIDIA L4 上是 GDDR6；A100、H100 这类卡用的是 HBM（高带宽显存）。

[【跳转到 03:32】](https://www.youtube.com/watch?v=LieS0bBgy0w&t=212)

![GPU 内存的四个层次：越往上越快、作用域越窄，越往下越慢、作用域越宽](assets/CUDA%20合并访存与%20Bank%20Conflict：从内存层次到加一填充/00212.webp)

### 1.2 同一块 SRAM，两种完全不同的工具

shared memory 和 L1 在物理上是同一块片上 SRAM，但它们是两个东西：shared memory 由你决定放什么进去，L1 由硬件自己填、自己淘汰。判断「我现在碰的是哪一层」，比记住容量数字更重要。

这张图画的不是数据流动的路线，而是同一个值**可能**待的位置：一个值此刻可能在寄存器里（最快的家），也可能在 shared memory 或 L1 里，再往下是 L2，最后是 global memory。层级越低，取它越慢。

### 1.3 一个不报错的坑：局部数组溢出到 local memory

循环里一个 float 型的累加变量很可能全程待在寄存器里，循环体内零次访存；而 `a[i]` 这种数组元素每次循环都要去 global memory 取一次——这次取可能命中 L1 或 L2，两个都不命中就是一次慢速的片外读。

真正阴险的是另一种情况：kernel 里声明了一个很大的定长局部数组，你以为它在寄存器文件里。但局部数组可能超出编译器的寄存器预算，也可能被一个编译期无法确定的运行时下标索引——这两种情况都会让它**溢出到 local memory**，而 local memory 物理上就在板上那块慢速的 global DRAM 里。没有报错，没有警告，你的「片上数组」已经变成片外的了，kernel 就慢下来了。

[【跳转到 07:19】](https://www.youtube.com/watch?v=LieS0bBgy0w&t=439)

## 二、合并访存：一个 warp 的请求落在几个 32 字节 sector 里

### 2.1 硬件按固定大小的块读 global memory

global memory 是按固定大小的块读的。一个 warp **一次性**要了什么，决定了这次读要花几个块。当 warp 的 32 个 lane 读的是 32 个连续的 4 字节字时，硬件把它们折叠成少数几个 32 字节 sector 事务——这个折叠就叫**合并访存（coalescing）**。每个被取回的字节都被用上了。

[【跳转到 08:44】](https://www.youtube.com/watch?v=LieS0bBgy0w&t=524)

![合并访存的定义：warp 的 32 个 lane 读 32 个连续的 4 字节字，硬件把它们折叠成少数几个 32 字节 sector 事务](assets/CUDA%20合并访存与%20Bank%20Conflict：从内存层次到加一填充/00524.webp)

下图是这个折叠的示意：上面一行是 global memory 里 32 个连续的 4 字节字，下面是 warp 的 32 个 lane（lane 0 在最左，lane 31 在最右），每个 lane 笔直指向自己正上方那个对齐的字——一 lane 一字。为了图面可读，32 条连线只画了 11 条。

[【跳转到 09:09】](https://www.youtube.com/watch?v=LieS0bBgy0w&t=549)

![连续访存：每个 lane 正对上方一个对齐的字，32 次对齐读折叠成少数几个「胖」sector 事务，取回的字节全部有用](assets/CUDA%20合并访存与%20Bank%20Conflict：从内存层次到加一填充/00549.webp)

### 2.2 把地址散开，折叠就没了

同样 32 个 lane，如果每个 lane 要的字在内存里相隔很远，这些读就再也折不到一起了。每个 lane 各自花掉一个 sector，事务又多又细，每个取回的 sector 里大部分字节都被扔掉。

[【跳转到 10:49】](https://www.youtube.com/watch?v=LieS0bBgy0w&t=649)

![跨步访存：每个 lane 伸向内存中很远的一个字（32 个 lane 只画了 8 个），每个 lane 各付一个 sector，取回的大部分字节被浪费](assets/CUDA%20合并访存与%20Bank%20Conflict：从内存层次到加一填充/00649.webp)

### 2.3 判断方法：看 `threadIdx.x` 是沿行还是沿列

拿一个 row-major 的二维数组举例。如果让 `threadIdx.x` 去索引**列**，那么相邻 lane 落在相邻内存上——一个 warp 横扫第 0 行，第 0 行在内存里是一整块连续区域，读就合并了。row-major 布局 + `threadIdx.x` 在列上：数组里的邻居就是内存里的邻居。

[【跳转到 11:14】](https://www.youtube.com/watch?v=LieS0bBgy0w&t=674)

![沿行访问：row-major 二维数组，threadIdx.x 索引列，一个 warp 读第 0 行，内存中这一行是连续的，所以合并](assets/CUDA%20合并访存与%20Bank%20Conflict：从内存层次到加一填充/00674.webp)

现在保持同一个 row-major 数组，只把 `threadIdx.x` 改成索引**行**。数学看起来是对称的，内存访问模式却完全不是：一个 warp 现在沿着第 0 列往下读，这些元素在内存里相隔整整一个行宽（位置 0、8、16、24……），每两个被碰到的格子之间都是大段空隙。合并访存被彻底破坏，尽管数学上完全等价。

[【跳转到 11:39】](https://www.youtube.com/watch?v=LieS0bBgy0w&t=699)

![沿列访问（column-walk bug）：同一个 row-major 数组，threadIdx.x 索引行，相邻 lane 的地址相隔一个行宽，合并被破坏](assets/CUDA%20合并访存与%20Bank%20Conflict：从内存层次到加一填充/00699.webp)

### 2.4 判据：数 sector，不数线程

判断一次访存合不合并，只需要问一句：**这个 warp 的 32 个请求落在几个 32 字节 sector 里？**

- 落在少数几个 sector 里 → 合并。32 个连续字是最干净的情形，但一个**置换过**的读、或者只有部分 lane 活跃的读，只要还落在那少数几个 sector 里，同样算合并。
- 散落在很多 sector 里 → 每个 sector 都要单独一次事务，而且每个 sector 里大部分字节被浪费。

所以结论很直接：**让 `threadIdx.x` 沿内存走（走行），不要穿过内存走（走列）**。

[【跳转到 12:20】](https://www.youtube.com/watch?v=LieS0bBgy0w&t=740)

![小结：warp 的读落在少数 32 字节 sector 里就合并；让 threadIdx.x 沿内存走（行），而不是穿过它（列）](assets/CUDA%20合并访存与%20Bank%20Conflict：从内存层次到加一填充/00740.webp)

## 三、shared memory：先把 tile 装进来，再设一道栅栏

### 3.1 它是你自己管理的片上暂存区

shared memory 是一块很小、很快的片上区域，**只属于一个 block**。和 cache 不同，放什么进去由你决定。典型用法是：一个 block 协作把一块 tile 数据从 global memory 搬一次进来，然后每个线程在片上反复复用——这正是分块（tiling）能省带宽的原因。

但线程一旦开始通过它协作，就需要一道屏障来保持同步。

### 3.2 写 → 栅栏 → 读

设想 8 个线程（t0 到 t7）各自带一个值，要写进下面一个 8 槽的 shared tile。每个线程写自己那一槽，然后一道闸门把所有人拦住，直到 8 个线程都写完；闸门打开后，整个 block 才一起读这块已经完工的 tile。

这道闸门就是 `__syncthreads`。

[【跳转到 13:33】](https://www.youtube.com/watch?v=LieS0bBgy0w&t=813)

![栅栏：8 个线程各自把一个值写进 shared tile 的 8 个槽，闸门等所有线程写完才打开，然后整个 block 一起读](assets/CUDA%20合并访存与%20Bank%20Conflict：从内存层次到加一填充/00813.webp)

一次协作装载加一次反向读，可以塞进同一个很小的 kernel：

```cuda
__global__ void reverse8(const float* in, float* out) {
    __shared__ float tile[8];          // 每个 block 一块 8 个 float 的暂存区
    int t = threadIdx.x;
    tile[t] = in[t];                   // 每个线程写自己那一槽
    __syncthreads();                   // 等所有写完成
    out[t] = tile[7 - t];              // 读别人写的槽：只有过了栅栏才安全
}
```

`tile[7 - t]` 读的是**另一个线程**写的那一槽，它之所以安全，正是因为栅栏保证了整块 tile 已经完工。把 `__syncthreads` 去掉，这次反向读就变成了竞态：某个线程可能读得太早，而拥有那一槽的线程还没写，于是读到旧值、残留值或者垃圾数据。

[【跳转到 14:23】](https://www.youtube.com/watch?v=LieS0bBgy0w&t=863)

### 3.3 陷阱：单 warp 时去掉栅栏也「看起来是对的」

这里有个坑。上面这 8 个线程是**同一个 warp** 的 lane，它们本来就锁步执行，所以这个小 kernel 即使删掉栅栏，往往也能跑出正确答案。**跑一次看到正确答案，什么也证明不了**。一旦 block 长过 1 个 warp，或者换了编译器、换了 GPU，错误答案随时可能出现。

栅栏的作用是让这次读**在构造上正确**，而不是**靠运气正确**。它是必需的，不是可选的。

[【跳转到 15:13】](https://www.youtube.com/watch?v=LieS0bBgy0w&t=913)

## 四、Bank Conflict：32 个 bank，word i 落在 bank i mod 32

### 4.1 规则只有一条

shared memory 有一个隐藏成本：它在物理上被切成 **32 个 bank**。32 个 bank 可以同时读，一个 warp 的每个 lane 对应一个 bank。每个 bank 宽 4 字节，**下标为 $i$ 的 word 落在 bank $i \bmod 32$**。后面所有结论都从这条规则推出来。

[【跳转到 16:49】](https://www.youtube.com/watch?v=LieS0bBgy0w&t=1009)

![shared memory 被切成 32 个 bank，可同时读，一个 warp 的每个 lane 对应一个 bank；bank 宽 4 字节，word i 落在 bank i mod 32](assets/CUDA%20合并访存与%20Bank%20Conflict：从内存层次到加一填充/01009.webp)

### 4.2 快的情形：一 lane 一 bank

如果 32 个 lane 各自碰到**不同**的 bank，32 次访问一趟就全部完成，没有任何 bank conflict 惩罚。

### 4.3 冲突：同一个 bank 里的不同地址要串行

把 stride 改一下，让这些 lane 读的**不同** word 全部映射到**同一个** bank：32 次访问没法一起跑，只能串行，变成 32 趟而不是 1 趟。这就是 **bank conflict**——不同地址落在同一个 bank 里，不能并行。

[【跳转到 18:04】](https://www.youtube.com/watch?v=LieS0bBgy0w&t=1084)

![bank conflict：warp 的 32 个 lane 都指向同一个 bank，但各自要的是不同的 word，只能串行，付出 32 趟的代价](assets/CUDA%20合并访存与%20Bank%20Conflict：从内存层次到加一填充/01084.webp)

### 4.4 例外：所有 lane 读同一个 word 是广播，不是冲突

有一种情形看起来像冲突，其实不是：32 个 lane 读**完全相同**的那个 word。因为地址是同一个，硬件把这个值一次性广播给所有 lane，没有冲突。

[【跳转到 18:54】](https://www.youtube.com/watch?v=LieS0bBgy0w&t=1134)

![广播：32 个 lane 指向同一个 word，硬件一次读出并广播给所有 lane，这不是 bank conflict](assets/CUDA%20合并访存与%20Bank%20Conflict：从内存层次到加一填充/01134.webp)

### 4.5 典型 bug：`tile[32][32]` 按列访问 → 32 路冲突

设想一块 32×32 个 float 的方形 tile，按列访问 `tile[threadIdx.x][k]`。每一行正好 32 个 float 宽，所以相隔一行的两个 word 下标差正好 32，落在**同一个 bank**。读第 $k$ 列时，每个 lane 的 word 全挤在那一个 bank 里——32 路冲突。

### 4.6 解法：把行宽从 32 改成 33（+1 填充）

把声明改成 32×33：每行错开一个 float，于是 32 个 lane 就摊到 32 个不同的 bank 上，冲突消失。

```cuda
// 只是索引算术的示意，不是可运行的 kernel
int k = 0;                              // 固定列；lane 0..31 各读一行
__shared__ float tile[32][32];          // 每行正好 32 个 float
float v = tile[threadIdx.x][k];         // 读第 k 列：32 路 bank conflict

__shared__ float pad[32][33];           // +1 填充，每行错开一个 bank
float w = pad[threadIdx.x][k];          // 现在摊到 32 个不同 bank
```

[【跳转到 19:44】](https://www.youtube.com/watch?v=LieS0bBgy0w&t=1184)

![加一填充：tile[32][32] 按列读会 32 路冲突；改成 pad[32][33] 后每行错开一个 bank，冲突消失](assets/CUDA%20合并访存与%20Bank%20Conflict：从内存层次到加一填充/01184.webp)

值得注意的是：把 shared tile 的行宽设成 32 的倍数，感觉上是最自然的选择，但这恰恰是让按列访问撞在同一个 bank 上的原因。修法是经典的 **+1 填充**，而不是把 tile 改小。

## 五、constant memory：warp 内同地址的广播

还有一类内存值得单独说。当每个线程同时读**同一个只读值**时，constant memory 能帮上忙：它把那个值一次性广播给整个 warp。

典型场景是滤波器系数、物理常数这类「只读且 warp 内人人相同」的数据。constant memory 很小，而且有缓存。当一个 warp 里每个 lane 都读同一个地址时，硬件把这个值广播给 warp，32 个 lane 同时拿到——这和合并访存的「32 个并行读」是两回事。

[【跳转到 21:37】](https://www.youtube.com/watch?v=LieS0bBgy0w&t=1297)

![constant memory 的广播：constant memory 里 c[0] 一个地址，一个值同时扇出到 warp 的全部 32 个 lane](assets/CUDA%20合并访存与%20Bank%20Conflict：从内存层次到加一填充/01297.webp)

一个最小的系数例子（不是完整的卷积）：每个线程把自己的元素乘上同一个系数 `c[0]`。host 端通过 `cudaMemcpyToSymbol` 把 `__constant__` 修饰的数组 c 填好，kernel 里每个线程算自己的全局下标，在范围内就乘一次。

```cuda
__constant__ float c[8];                       // host 侧用 cudaMemcpyToSymbol 填充

__global__ void scale(const float* in, float* out, int n) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n) out[i] = in[i] * c[0];          // warp 内所有 lane 读同一地址 -> 广播
}
```

**但把数组搬进 constant memory 并不保证一定变快**。如果线程读的是它的**不同**地址（比如把 constant memory 当 per-thread 查找表用），分散的地址会串行，反而更慢。constant memory 只在「整个 warp 同时要同一个地址」时才有用。

[【跳转到 22:52】](https://www.youtube.com/watch?v=LieS0bBgy0w&t=1372)

## 六、两个可以动笔算的实验

课程最后留了两个「先在纸上预测，再上机验证」的实验。它们的价值在于：预测错了，说明你对 sector 和 bank 的映射还没真正建立起来。

**实验一（global memory）**：一个 warp 的 32 个 lane 各自从一维数组读 `a[threadIdx.x]`。先问：lane 0 读哪个地址？lane 1 呢？lane 2 呢？这些地址是邻居还是相隔很远？所以这个 warp 合不合并？

答案：lane $k$ 读 `a[k]`，相邻 lane 读相邻 word，合并——少数几个事务，没有浪费的字节。

**实验二（shared memory）**：一个 warp 从 32×32 个 float 的 shared tile 里读 `tile[threadIdx.x][0]`。先问：`tile[0][0]` 落在哪个 bank？`tile[1][0]`？`tile[2][0]`？它们是同一个 bank 还是不同 bank？**只改一个字符**，怎么把它们摊开？

答案：每行正好 32 个 float，所以 column 0 的每个元素都落在同一个 bank，是 32 路冲突；把声明从 32 改成 33 就修好了。

[【跳转到 25:14】](https://www.youtube.com/watch?v=LieS0bBgy0w&t=1514)

![两个实验的收束：金字塔说明数据住在哪一层，合并访存与无冲突访问各自挣到该层承诺的带宽（示意图，两组柱状图不互相比较）](assets/CUDA%20合并访存与%20Bank%20Conflict：从内存层次到加一填充/01471.webp)

注意这张图里的两组柱状图**不能互相比较**：shared memory 本来就比 global memory 快得多，所以只能在各自组内比较。合并访存让 global memory 的读逼近这一层承诺的带宽，无冲突访问让 shared memory 做到同样的事。

最后一个容易算错的细节：用「只算读了多少字节」去反推实际带宽，会漏掉一次完整往返还要**写出**一个结果。这会低估总搬运字节数，让一个本来很快的合并访存 kernel 看起来比实际更慢。

[【跳转到 26:29】](https://www.youtube.com/watch?v=LieS0bBgy0w&t=1589)

## 小结

- 绝大多数 kernel 是 memory-bound 的，目标是「搬更少的数据，搬得更快」。
- 先认清层级：寄存器 → shared memory / L1 → L2 → global VRAM；越往上越快、作用域越窄。局部数组溢出到 local memory 时不报错，但会悄悄变慢。
- 合并访存的判据是**数 sector**：一个 warp 的 32 个请求落在少数几个 32 字节 sector 里就合并。做法是让 `threadIdx.x` 沿内存走（行），不要穿过内存走（列）。
- shared memory 是 per-block 的手工暂存区；协作装载后必须 `__syncthreads`，单 warp 时删掉栅栏也「看起来对」，那是运气不是正确。
- bank conflict 的判据是**数 bank**：`word i` 落在 `bank i mod 32`；一 lane 一 bank 最快，同一 bank 里不同地址要串行，所有 lane 读同一个 word 是广播。
- 行宽是 32 的倍数时，按列访问会 32 路冲突；把行宽 +1（`[32][33]`）就摊开了。
- constant memory 是给「warp 内同地址的只读值」用的广播，不是通用的只读缓存；线程读不同地址会串行。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| memory-bound | kernel 的速度由字节到达速度决定，而不是由算力决定 |
| sector | global memory 一次事务搬运的固定大小块，本讲中为 32 字节 |
| coalescing（合并访存） | 一个 warp 的多个 lane 请求落在少数几个 sector 里，被硬件折叠成少数几次事务 |
| column-walk bug | row-major 数组里让 `threadIdx.x` 索引行，相邻 lane 的地址相隔一个行宽，合并被破坏 |
| shared memory | 每个 block 私有的片上暂存区，放什么由程序员决定 |
| `__syncthreads` | block 级栅栏，保证所有线程的写都完成之后才允许读 |
| bank | shared memory 被切成的 32 个可并行访问的 4 字节宽单元 |
| bank conflict | 一个 warp 内两个以上 lane 从同一个 bank 读**不同**地址，只能串行 |
| broadcast | 一个 warp 内所有 lane 读同一个 word，硬件一次读出并分发给所有 lane，不算冲突 |
| padding（+1 填充） | 把 shared tile 行宽从 32 改成 33，让按列访问摊到 32 个不同 bank |
| constant memory | 小的、带缓存的只读内存，warp 内同地址时广播；地址分散则串行 |
| local memory | 寄存器溢出时局部数组的落点，物理上在片外 global DRAM 里 |