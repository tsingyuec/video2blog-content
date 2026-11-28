# 从 atomicAdd 到 warp shuffle 归约：把一百万元素求和从 3.79 ms 压到 0.204 ms

> 视频来源：[CUDA Programming Part 4 - Atomic Add, Reduction, & Warp Shuffling](https://www.youtube.com/watch?v=BTB7wzmv6kw)（YouTube · Sloppy Code）｜时长约 32.4 分钟
> 导读：这是「CUDA 编程系列」第四天的一集，主题是**归约（reduction）**——把一个大数组压成一个数。讲者先用白板把 warp、竞争条件、二叉归约画清楚，再打开编辑器逐行读两个 kernel：一个朴素 `atomicAdd` 版本，一个用 shared memory + warp shuffle 的版本，最后在 Colab 里跑出两者的耗时对比。本文按「白板推导 → 逐行读代码 → 看实测」的顺序复述，代码与数字以画面里实际出现的为准。

## 本讲要解决的核心问题（SCQA）

**背景**：GPU 的价值在于「一次开几百万个线程」。求和这种操作看起来最适合并行——每个线程读一个元素，加到同一个结果变量上，理论上应该比 CPU 的 for 循环快几个数量级。

**冲突**：真这么写会得到**错误答案**。几百万个线程同时对同一个 `out` 变量做「读-加-写」，谁先谁后完全随机，这是教科书级的竞争条件。而 `__syncthreads()` 在这里帮不上忙——它只能同步**一个 block 内部**的线程，管不了几百万个线程跨 block 的写入。

**疑问**：那么，怎样在保证结果正确的前提下，让几百万个线程合作算出一个和？

**回答（中心思想）**：分两层解决。**block 内部**用二叉归约（binary reduction）把 256 个线程的部分和压成 1 个，其中前一半靠 shared memory + `__syncthreads()`，后一半（warp 内）靠寄存器级的 `__shfl_down_sync` 直接读邻居的值，连屏障都省了；**block 之间**只剩每个 block 的 1 个部分和，用 `atomicAdd` 汇总，冲突从「几百万次」降到「block 个数次」。实测一百万元素求和从 3.790 ms 降到 0.204 ms。

## 一、先补一块拼图：warp 是寄存器级的「共享内存」

在讲归约之前，讲者先复习了 warp，因为后面 warp shuffle 那一段全靠它。

**是什么**：一个 block 里的线程会被硬件按固定大小分组，每组 32 个线程，叫一个 **warp**。这个 32 是硬编码在 GPU 里的，讲者的说法是「据我所知你改不了」。

**为什么重要**：同一个 warp 里的线程可以**直接读彼此寄存器里的值**，既不用调 `__syncthreads()`，也不用经过 shared memory。讲者的原话是「这比从 shared memory 读还要快得多」。[【跳转到 00:50】](https://www.youtube.com/watch?v=BTB7wzmv6kw&t=50)

![白板上的层级关系：GM → SM → block → 线程，线程再组成 warp；一个 warp 固定 32 个线程](assets/从%20atomicAdd%20到%20warp%20shuffle%20归约：把一百万元素求和从%203.79%20ms%20压到%200.204%20ms/00150.webp)

于是存储层级可以排成一条从快到慢的线：

| 层级 | 谁可以访问 | 速度 |
| --- | --- | --- |
| 寄存器（register file） | 同一 warp 内的线程可以互相读 | 最快 |
| shared memory | 同一 block 内的所有线程 | 很快 |
| global memory | 所有线程 | 带宽最大，但最慢 |

讲者特意强调「global memory 带宽最大但最慢，寄存器容量最小但最快」，所以优化的方向永远是**把数据尽量往上面两层搬**。这句话是理解后面所有代码的钥匙。[【跳转到 02:25】](https://www.youtube.com/watch?v=BTB7wzmv6kw&t=145)

## 二、归约是什么，以及为什么不能直接并行

**是什么**：归约是把一个数组压成一个更小的结果，比如

$$
\text{sum} = \sum_{i=1}^{n} a_i, \qquad \text{min} = \min_{i=1}^{n} a_i
$$

求和、求最小值、求最大值、求积，都是归约。

**CPU 怎么做**：一个 `sum = 0`，一个 `for i = 1..n`，`sum += a[i]`。简单，但 n 是一百万时就是一百万次串行加法，而且 CPU 的线程数很少。[【跳转到 03:25】](https://www.youtube.com/watch?v=BTB7wzmv6kw&t=205)

**GPU 想怎么做**：开一百万个线程，每个线程读一个元素，加到 `out` 上。

这里有个值得记住的对比：CPU 只有很少的线程，它靠**降低延迟**（把单次访问做快）取胜；GPU 靠的是**大吞吐**，宁可接受一点延迟，也要把成千上万个线程同时堆上去。所以 GPU 上正确的思路不是「让每个线程更快」，而是「让一万个线程同时有事干」。

**为什么这样不行**：这就是竞争条件。视频里的例子很直白——`out` 当前是 10，线程 T1 打算把它加 1；在 T1 写回之前，T2 把 `out` 读走了，T2 看到的还是 10 而不是 11。两边各自加完写回，结果就少加了一次。

![白板上的竞争条件推导：T0 到 T3 各读一个元素、各自往 out 上累加，最终结果不可预测](assets/从%20atomicAdd%20到%20warp%20shuffle%20归约：把一百万元素求和从%203.79%20ms%20压到%200.204%20ms/00450.webp)

讲者在这里点出一个关键判断：**这种场景不能用 `__syncthreads()`**。原因很简单——屏障是 block 级原语，而这里的冲突发生在**不同 block 之间**。[【跳转到 06:00】](https://www.youtube.com/watch?v=BTB7wzmv6kw&t=360)

## 三、第一版：一行 `atomicAdd` 就能算对

CUDA 提供的解法是**原子操作（atomic operation）**。所谓原子，就是「这一串读-改-写在硬件上不可分割」，其他线程要么看到改之前的值，要么看到改之后的值，不会看到中间态。[【跳转到 08:45】](https://www.youtube.com/watch?v=BTB7wzmv6kw&t=525)

```cuda
__global__ void atomicAddNaive(const double* d_a, double* d_out, int N){
    int idx = blockDim.x * blockIdx.x + threadIdx.x;
    if (idx < N){
        atomicAdd(d_out, d_a[idx]);
    }
}
```

![朴素版本 kernel：算全局下标、做边界检查、一次 atomicAdd](assets/从%20atomicAdd%20到%20warp%20shuffle%20归约：把一百万元素求和从%203.79%20ms%20压到%200.204%20ms/00630.webp)

三行有效代码：算下标（前面几讲的老公式）、`if (idx < N)` 做边界保护、`atomicAdd(d_out, d_a[idx])`。函数签名就是「目标地址 + 要加的值」，执行完目标变量里就多了这个值。

这一版**结果是对的**，讲者把它当作基线（baseline）。但它有两个问题：[【跳转到 11:35】](https://www.youtube.com/watch?v=BTB7wzmv6kw&t=695)

1. **一百万个线程全挤在同一个地址上**。硬件必须把它们排成一队串行执行，`atomicAdd` 变成了一个超长的串行队列。
2. **每个线程只干了「加一个数」这点活**，绝大部分时间花在排队上。

换句话说，这个 kernel 把「并行」用在了错误的地方：本来应该并行的是**加法**，它却把一百万个线程并行地送进了同一个队列。

## 四、第二版：二叉归约，把 $O(n)$ 步压成 $\log_2 n$ 步

### 4.1 思路：两两相加，每轮规模减半

讲者先用 8 个元素、4 个线程的手算例子把算法讲透。数组是 `1 2 3 4 5 6 7 8`，每个线程负责**两个**元素，而且是**隔开一半**的两个：

- T0 负责 `a[0]` 和 `a[4]` → 1 + 5 = 6
- T1 负责 `a[1]` 和 `a[5]` → 2 + 6 = 8
- T2 负责 `a[2]` 和 `a[6]` → 3 + 7 = 10
- T3 负责 `a[3]` 和 `a[7]` → 4 + 8 = 12

写成表格更直观：

| 线程 | 第一个元素 | 第二个元素 | 部分和 |
| --- | --- | --- | --- |
| T0 | `a[0]` = 1 | `a[4]` = 5 | 6 |
| T1 | `a[1]` = 2 | `a[5]` = 6 | 8 |
| T2 | `a[2]` = 3 | `a[6]` = 7 | 10 |
| T3 | `a[3]` = 4 | `a[7]` = 8 | 12 |

注意「隔一半」这个设计不是随便选的：它让每个线程的第二个元素都落在数组的后半段，于是**第一轮就把前后两半对上了**，也为后面 shared memory 上的折半循环铺好了下标关系（`S[tid] += S[tid + s]` 里的 `s` 就是「一半」）。

四个部分和写进 shared memory，得到 `6 8 10 12`。然后继续两两相加，讲者在白板上把下一层写成 `18 18`，再合成 `36`。不管具体怎么配对，**每一轮元素个数减半**，三轮之后就是总和 36。

![白板上的二叉归约：8 个元素 → 4 个部分和 → 2 个 → 1 个，共 log2(8)=3 步](assets/从%20atomicAdd%20到%20warp%20shuffle%20归约：把一百万元素求和从%203.79%20ms%20压到%200.204%20ms/00979.webp)

这就是「二叉」的含义：串行加法要 $n-1$ 步，二叉归约只要 $\log_2 n$ 步。8 个元素是 3 步，一百万个元素是 20 步。[【跳转到 16:19】](https://www.youtube.com/watch?v=BTB7wzmv6kw&t=979)

### 4.2 下标公式：讲者自己先写错了一次

每个线程要处理两个元素，所以**线程数只需要元素数的一半**。下标公式在朴素版的基础上多乘一个 2：

```cuda
int i = blockDim.x * blockIdx.x * 2 + threadIdx.x;
```

![下标映射：T0→0 和 4，T1→1 和 5，T2→2 和 6，T3→3 和 7](assets/从%20atomicAdd%20到%20warp%20shuffle%20归约：把一百万元素求和从%203.79%20ms%20压到%200.204%20ms/00870.webp)

视频里有一段很真实的插曲：讲者一开始漏了 `* 2`，用 `blockDim.x * blockIdx.x + threadIdx.x` 去算 block 1 的线程该处理谁，算出 `5 6 7 8`，越算越不对，最后自己发现「我忘了乘 2」。补上之后 block 1 的四个线程分别处理 `8/12`、`9/13`、`10/14`、`11/15`——正好接在 block 0 的 `0..7` 后面，两个 block 覆盖 16 个元素。

这个细节值得记下来：**乘 2 不只是为了少开线程，它保证了下标映射在 block 之间是连续且不重叠的**。[【跳转到 18:29】](https://www.youtube.com/watch?v=BTB7wzmv6kw&t=1109)

## 五、逐行读那个 256 线程的归约 kernel

真正的 kernel 用 256 个线程一个 block。完整代码如下（画面里滚动出现的两段拼起来）：

```cuda
#define threads_per_block 256

__global__
void atomicAddReduced(const double* d_a, double* d_out, int N){
    __shared__ double S[threads_per_block];
    int i   = blockDim.x * blockIdx.x * 2 + threadIdx.x;
    int tid = threadIdx.x;

    double sum = 0.0;
    if (i < N)                    sum += d_a[i];
    if (i + blockDim.x < N)       sum += d_a[i + blockDim.x];
    S[tid] = sum;
    __syncthreads();

    for (int s = blockDim.x/2; s > 32; s >>= 1){
        if (tid < s) S[tid] += S[tid + s];
        __syncthreads();
    }

    if (tid < 32){
        double val = S[tid] + S[tid + 32];
        for (int offset = 16; offset > 0; offset >>= 1){
            val += __shfl_down_sync(0xffffffff, val, offset);
        }
        S[tid] = val;
    }

    if (tid == 0){
        atomicAdd(d_out, S[tid]);
    }
}
```

![kernel 前半段：声明 shared memory、算下标、累加两个元素、写回 shared、第一次 __syncthreads()](assets/从%20atomicAdd%20到%20warp%20shuffle%20归约：把一百万元素求和从%203.79%20ms%20压到%200.204%20ms/01350.webp)

![kernel 后半段：warp 内用 __shfl_down_sync 做最后 5 轮，再由 tid==0 做一次 atomicAdd](assets/从%20atomicAdd%20到%20warp%20shuffle%20归约：把一百万元素求和从%203.79%20ms%20压到%200.204%20ms/01535.webp)

下面按执行顺序拆开讲。

### 5.1 第一层：每个线程先把自己的两个元素加起来

```cuda
double sum = 0.0;
if (i < N)                sum += d_a[i];
if (i + blockDim.x < N)   sum += d_a[i + blockDim.x];
S[tid] = sum;
__syncthreads();
```

- `__shared__ double S[threads_per_block]`：每个 block 私有一块 256 个 `double` 的片上空间，block 内所有线程都能访问。
- `int tid = threadIdx.x`：把线程在 block 内的编号单独存一份。讲者的解释是「存下来方便后面反复用」——后面写 `S[tid]`、判断 `tid < s`、最后 `tid == 0` 都要用到它，而 `i` 是**全局**下标，两者不能混。
- 两次 `if` 都是边界检查。注意第二个检查是 `i + blockDim.x < N`——这正是「隔一半」的偏移量，也是 4.2 里那个 `* 2` 的来源。
- `S[tid] = sum` 把部分和写进 shared memory，下标就是线程自己的 `tid`，天然不冲突。
- `__syncthreads()`：**必须在这里**。因为下一步要读 `S[tid + s]`，那是别的线程写的，如果不屏障，读到的可能是还没写进去的垃圾值。[【跳转到 22:30】](https://www.youtube.com/watch?v=BTB7wzmv6kw&t=1350)

### 5.2 第二层：shared memory 上的二叉归约，循环到 32 为止

```cuda
for (int s = blockDim.x/2; s > 32; s >>= 1){
    if (tid < s) S[tid] += S[tid + s];
    __syncthreads();
}
```

`blockDim.x = 256`，所以 `s` 依次取 128、64，然后停在 32（因为条件是 `s > 32`）。

- 第一轮 `s = 128`：`tid < 128` 的线程做 `S[tid] += S[tid + 128]`，后一半加到前一半上。
- 第二轮 `s = 64`：`tid < 64` 的线程做 `S[tid] += S[tid + 64]`。
- 每轮规模减半，且**每轮之后都要 `__syncthreads()`**——因为下一轮读的 `S[tid + s]` 是上一轮别人刚写的结果。

把 256 个线程的循环摊开看：

| 轮次 | `s` | 参与线程 | 做的事 | 有效元素数 |
| --- | --- | --- | --- | --- |
| 起始 | — | 全部 256 | 各自算两个元素的部分和 | 256 |
| 1 | 128 | `tid < 128` | `S[tid] += S[tid+128]` | 128 |
| 2 | 64 | `tid < 64` | `S[tid] += S[tid+64]` | 64 |
| 退出循环 | — | — | 交给 warp 段处理 | 64 |

注意每轮**只有一半线程干活**，另一半在屏障处等——这正是二叉归约的代价：步数从 $n$ 降到 $\log n$，但每一步的并行度也在减半。

讲者特别强调这个循环为什么停在 32 而不是 0：**再往下就是单个 warp 内部的事了，不需要屏障**。他给了一个可以自己动手验证的实验——把 `s > 32` 改成 `s >= 0`，代码仍然能算对，但会**慢一点**，因为放弃了 warp 寄存器互读这条快车道。[【跳转到 26:00】](https://www.youtube.com/watch?v=BTB7wzmv6kw&t=1560)

### 5.3 第三层：warp 内用 `__shfl_down_sync` 读邻居的寄存器

```cuda
if (tid < 32){
    double val = S[tid] + S[tid + 32];
    for (int offset = 16; offset > 0; offset >>= 1){
        val += __shfl_down_sync(0xffffffff, val, offset);
    }
    S[tid] = val;
}
```

这一段是全集最绕的地方，讲者自己也说「我也是花了很久才搞懂」。

**先看 `if (tid < 32)`**：此时 shared memory 里还剩 64 个部分和（`S[0..63]`）。只让前 32 个线程参与，每个线程先把 `S[tid]` 和 `S[tid + 32]` 加起来，于是 64 个数变成 32 个数，**正好装进一个 warp**。

**再看 `__shfl_down_sync`**：它的作用是「把同一个 warp 里、下标比我大 `offset` 的那个线程的寄存器值取过来」。

- `offset = 16` 时：T0 拿到 T16 的 `val`，T1 拿到 T17 的，……T15 拿到 T31 的。
- `offset = 8` 时：T0 拿到 T8 的（此时 T8 里已经是它自己和 T24 的和），以此类推。
- 一路 `16 → 8 → 4 → 2 → 1`，5 轮之后 T0 的 `val` 就是这 32 个数的总和。

因为**读的是寄存器、走的是 warp 内的直连通路**，这 5 轮**一次 `__syncthreads()` 都不需要**——这就是第一节里「warp 是寄存器级共享内存」那句话的兑现。[【跳转到 26:50】](https://www.youtube.com/watch?v=BTB7wzmv6kw&t=1610)

**那个奇怪的第一个参数 `0xffffffff`** 是**掩码（mask）**。讲者的解释是：它告诉编译器「这个 warp 里 32 个线程全部参与这次操作」，硬件据此知道该从哪些 lane 取值。全 1 表示全员参与。[【跳转到 27:35】](https://www.youtube.com/watch?v=BTB7wzmv6kw&t=1655)

最后 `S[tid] = val` 把结果写回 shared memory，此时 `S[0]` 就是整个 block 的总和。

![kernel 末尾：warp 内折半到 1 个值，再由 tid==0 对 d_out 做一次 atomicAdd](assets/从%20atomicAdd%20到%20warp%20shuffle%20归约：把一百万元素求和从%203.79%20ms%20压到%200.204%20ms/01655.webp)

### 5.4 收尾：每个 block 交一个数给 `atomicAdd`

```cuda
if (tid == 0){
    atomicAdd(d_out, S[tid]);
}
```

**为什么这里还要原子操作？** 讲者的回答是：每个 block 有自己的 shared memory，`S[0]` 只包含**这个 block** 负责的那一段的和。block 0 算的是 `0..7`，block 1 算的是 `8..15`，它们之间没有任何屏障可用（`__syncthreads()` 管不到别的 block）。所以最后一步必须用 `atomicAdd` 把各 block 的部分和累到全局的 `d_out` 上。[【跳转到 29:16】](https://www.youtube.com/watch?v=BTB7wzmv6kw&t=1756)

关键在于**冲突规模变了**：

| 版本 | `atomicAdd` 的调用次数 | 竞争程度 |
| --- | --- | --- |
| 朴素版 | 每个元素一次（100 万次） | 100 万个线程抢一个地址 |
| 归约版 | 每个 block 一次（$2^{20}/(256\times 2) = 2048$ 次） | 只与 block 数同阶 |

这就是整个优化的骨架：**能在片上解决的，绝不放到全局去抢**。

把两个版本的结构放在一起对比，差异一目了然：

| | 朴素版 | 归约版 |
| --- | --- | --- |
| 线程数 | 每个元素一个线程 | 每两个元素一个线程 |
| 片上空间 | 不用 | 每 block 256 个 `double` |
| 屏障 | 不用 | 第一层 1 次 + 每轮 1 次 |
| warp 特殊指令 | 不用 | `__shfl_down_sync` |
| `atomicAdd` 次数 | 与元素数同阶 | 与 block 数同阶 |
| 算法复杂度 | $O(n)$ 次串行原子加 | $O(\log n)$ 步树形归约 |

## 六、实测：3.790 ms → 0.204 ms

讲者在 Colab 里用 `N = 1 << 20`（约一百万个元素）跑两个 kernel，画面里的输出是：

![Colab 里的实测：归约版 0.204 ms，朴素版 3.790 ms，两者结果都是 549755289600](assets/从%20atomicAdd%20到%20warp%20shuffle%20归约：把一百万元素求和从%203.79%20ms%20压到%200.204%20ms/01836.webp)

| 版本 | 耗时 | 结果 |
| --- | --- | --- |
| `atomicAddNaive` | 3.790 ms | 549755289600.000000 |
| `atomicAddReduced` | 0.204 ms | 549755289600.000000 |

讲者口述「大约快 18 倍」，按画面上的数字算 $3.790 / 0.204 \approx 18.6$，和他说的吻合。更重要的是**两个版本结果完全一致**——`549755289600` 正是 $0+1+\cdots+(2^{20}-1)$ 的值，说明归约版没有算错。[【跳转到 30:36】](https://www.youtube.com/watch?v=BTB7wzmv6kw&t=1836)

## 七、讲者留的三个动手实验

视频最后没有停在「跑通了」，而是给了三个改代码的练习，用来建立对这套写法的直觉：

1. **删掉 `for` 循环里的某一步**（他指的是 30–34 行那一段），结果会变，借此理解为什么每一层都不能省。
2. **整个 block 删掉试试**，看会发生什么。
3. **把 `s > 32` 改成 `s >= 0`**：代码仍然正确，但会变慢，因为放弃了 warp 寄存器互读的优势。

他的建议是「拿笔和纸，就按 1 到 8 的数组画一遍，没有别的办法」。这句话对归约这种「树形」算法是实话——光看代码很难看出每一轮在做什么，画出来就一目了然。他还特意区分了三个实验的预期：改 30–34 行那一步会让**结果不一样**（借此看出这一层不能省）；把 `s > 32` 改成 `s >= 0` 则**结果仍然正确、只是变慢**；至于直接删掉某一块会发生什么，他没给答案，留给自己试。[【跳转到 31:29】](https://www.youtube.com/watch?v=BTB7wzmv6kw&t=1889)

## 小结

- **归约**是把数组压成一个值的操作（求和、最值、求积），串行需要 $O(n)$ 步，二叉归约只要 $\log_2 n$ 步。
- **`atomicAdd` 能保证正确性**，但一百万个线程抢同一个地址会退化成串行队列，所以它只适合做「最后一公里」的汇总。
- **`__syncthreads()` 是 block 级原语**，跨 block 无效；因此 block 之间的汇总必须靠原子操作。
- **二叉归约分三段**：每线程先加两个元素 → shared memory 上折半到 64 个 → warp 内用 `__shfl_down_sync` 折半到 1 个。
- **warp 内不需要屏障**，因为 `__shfl_down_sync` 读的是寄存器，硬件保证同一个 warp 的 lane 之间可以直接取数；`0xffffffff` 掩码表示 32 个 lane 全员参与。
- **优化的通用套路**：把冲突从全局搬到片上，把串行从 $n$ 步压到 $\log n$ 步。实测收益是 18.6 倍。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| 归约（reduction） | 把数组压成一个值的操作，如求和、求最大值 |
| 竞争条件（race condition） | 多线程无顺序地读写同一地址，结果不可预测 |
| 原子操作（atomic operation） | 硬件保证不可分割的读-改-写，如 `atomicAdd` |
| 二叉归约（binary reduction） | 每轮两两相加、规模减半，共 $\log_2 n$ 轮 |
| warp | 32 个线程组成的硬件调度单位，lane 之间可互读寄存器 |
| `__shfl_down_sync` | 取同一 warp 中「下标 + offset」那个线程的寄存器值 |
| 掩码（mask） | `__shfl_*` 的第一个参数，声明哪些 lane 参与这次交换 |
| `__syncthreads()` | block 级屏障，只能同步同一个 block 内的线程 |