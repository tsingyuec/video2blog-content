# 用 Triton 手写 MatMul 击败 PyTorch：分块、张量核与自动调优

> 视频来源：[How to Beat PyTorch? Writing a Fast MatMul Kernel in Triton - Tensor Cores, L2 Caching & Auto-Tuning](https://www.youtube.com/watch?v=W8NFUvYX-u8)（YouTube · Qooba，讲者 Kuba）｜时长约 9 分钟
> 导读：一支「一次把 matmul 调到底」的实操视频。作者从能跑通的朴素 kernel 出发，依次加上 L2 分组调度、`@triton.autotune`、张量核、`num_stages` / `num_warps`，最后和 PyTorch 的 cuBLAS 正面对比。本文按这条优化链展开，重点落在自动调优与内核参数上；Triton 的基本语法（`tl.load`、`tl.program_id`）只作必要回顾。

## 本讲要解决的核心问题（SCQA）

**背景**：你已经能用 Triton 写出一个正确的矩阵乘 kernel——把输出矩阵 $C$ 切成块，一个 GPU program 算一块，用 `tl.load` 取数据、`tl.dot` 累加。代码能跑，结果也对。

**冲突**：但第一次和 PyTorch 对比，作者的实现**慢了大约两倍**。正确性只是入场券，性能才是目的；而性能的瓶颈往往不在「算」，在「怎么取数据」和「参数选得对不对」。

**疑问**：从一个能跑的 kernel 到一个能打败 cuBLAS 的 kernel，中间要拧哪几个旋钮？这些旋钮（block size、`num_stages`、`num_warps`）为什么会影响性能？又该怎么自动挑？

**回答（中心思想）**：这条优化链有四步，且顺序不能乱——**先把分块写对（含边界 mask），再让 L2 缓存被复用（分组调度），然后用 `@triton.autotune` 把 block size 的选择自动化，最后用张量核与流水线/occupancy 参数榨干硬件**。其中 autotune 不是「魔法加速器」，它只是把「人工试参数」这一步自动化：编译每一组配置、逐个测速、留下最快的那个。

---

## 一、先有一个正确的 kernel：把 C 切成块，按 K 分块累加

矩阵乘的朴素写法是「一个线程算一个元素」，但 Triton 的思路不同：**把输出矩阵 $C$ 切成一块块 tile，每个 GPU program 负责算一块**。这是后面所有优化的地基。

[【跳转到 01:02】](https://www.youtube.com/watch?v=W8NFUvYX-u8&t=62)

### 1.1 三个 meta-parameter：`BLOCK_SIZE_M/N/K`

kernel 的签名里除了指针和 stride，还有三个用 `tl.constexpr` 声明的编译期常量：

```python
# Meta-parameters
BLOCK_SIZE_M: tl.constexpr,
BLOCK_SIZE_N: tl.constexpr,
BLOCK_SIZE_K: tl.constexpr,
```

`tl.constexpr` 的意思是「编译期已知的常量」。这一点很关键：**block size 不是运行时变量，而是编译参数**。换一个 block size，就等于换一份编译产物——这正是 `@triton.autotune` 能「编译多份、挑一份」的前提。

![kernel 开头的 meta-parameter 声明，BLOCK_SIZE_M/N/K 都是 tl.constexpr](assets/用%20Triton%20手写%20MatMul%20击败%20PyTorch：分块、张量核与自动调优/00094.webp)

[【跳转到 01:29】](https://www.youtube.com/watch?v=W8NFUvYX-u8&t=89)

### 1.2 从 `program_id` 到指针：广播 + stride

每个 program 先算出自己负责哪一块：

```python
pid = tl.program_id(axis=0)
num_pid_n = tl.cdiv(N, BLOCK_SIZE_N)
pid_m = pid // num_pid_n
pid_n = pid % num_pid_n
```

然后算这一块的行列偏移，再用**广播**把一维的行索引和一维的列索引拼成二维的指针数组：

```python
offs_m = pid_m * BLOCK_SIZE_M + tl.arange(0, BLOCK_SIZE_M)
offs_n = pid_n * BLOCK_SIZE_N + tl.arange(0, BLOCK_SIZE_N)
a_ptrs = a_ptr + (offs_m[:, None] * stride_am + offs_k[None, :] * stride_ak)
b_ptrs = b_ptr + (offs_k[:, None] * stride_bk + offs_n[None, :] * stride_bn)
```

`stride` 告诉程序「在内存里往前迈一步要走多远」。因为矩阵在显存里是一维铺开的，行优先还是列优先、转置与否，全都体现在 stride 上。

[【跳转到 02:19】](https://www.youtube.com/watch?v=W8NFUvYX-u8&t=139)

### 1.3 为什么一定要有 mask：M 为 100、BLOCK_SIZE_M 为 64 的情形

`C` 的维度不一定能被 block size 整除。视频举的例子是 $M=100$、`BLOCK_SIZE_M` 取 64：第二个块会去访问第 64～127 行，而第 100～127 行**根本不存在**。

```python
a_mask = (offs_m[:, None] < M) & ((k + offs_k[None, :]) < K)
b_mask = ((k + offs_k[:, None]) < K) & (offs_n[None, :] < N)
a = tl.load(a_ptrs, mask=a_mask, other=0.0)
b = tl.load(b_ptrs, mask=b_mask, other=0.0)
```

mask 是一个和 tile 同形状的布尔数组，越界位置为 `False`，`tl.load` 用 `other=0.0` 把这些位置填 0。**没有 mask，要么非法访存直接崩，要么读到垃圾值污染结果**。填 0 是安全的，因为乘 0 不影响累加。

![完整的 kernel 主体：k 循环、mask 加载、tl.dot 累加、指针按 BLOCK_SIZE_K 前进](assets/用%20Triton%20手写%20MatMul%20击败%20PyTorch：分块、张量核与自动调优/00119.webp)

### 1.4 k 循环与指针前进

一次装不下整行 A 和整列 B，所以沿 $K$ 维分块循环：

```python
accumulator = tl.zeros((BLOCK_SIZE_M, BLOCK_SIZE_N), dtype=tl.float32)
for k in range(0, K, BLOCK_SIZE_K):
    ...
    accumulator += tl.dot(a, b)
    a_ptrs += BLOCK_SIZE_K * stride_ak
    b_ptrs += BLOCK_SIZE_K * stride_bk
```

累加器用 `float32` 初始化，这一点在后面讲张量核时会再次出现——**输入可以降精度，累加不能**。

到这里 kernel 是正确的。第一次 benchmark 的结果是：**比 PyTorch 慢约两倍**。

[【跳转到 03:12】](https://www.youtube.com/watch?v=W8NFUvYX-u8&t=192)

---

## 二、第一个真正的瓶颈：不是算力，是 L2 缓存没被复用

作者给出的诊断很直接：瓶颈是**内存带宽**，以及「我们怎么使用存储层次」。

[【跳转到 03:28】](https://www.youtube.com/watch?v=W8NFUvYX-u8&t=208)

### 2.1 显存金字塔：寄存器比 HBM3 快 41 倍

以 H100 为例，视频给出的一张金字塔图把差距量化了：

| 层级 | 带宽（约） | 容量 |
| --- | --- | --- |
| 寄存器 Registers | ~124 TB/s | 256 KB/SM |
| 共享内存 Shared Memory | ~31 TB/s | 256 KB/s |
| DSMEM | ~21 TB/s | SM-to-SM |
| L2 Cache | ~11 TB/s | 50 MiB |
| HBM3 显存 | 3 TB/s | 80 GB |

寄存器与 HBM3 之间的差距是 **41 倍**。所以「让数据尽量留在片上」是性能的第一性原理，而 L2 是全局共享、容量最大的一层片上缓存——**调度顺序决定了 L2 命中率**。

![H100 的显存金字塔：寄存器 124 TB/s 对 HBM3 3 TB/s，相差 41 倍](assets/用%20Triton%20手写%20MatMul%20击败%20PyTorch：分块、张量核与自动调优/00238.webp)

[【跳转到 03:58】](https://www.youtube.com/watch?v=W8NFUvYX-u8&t=238)

### 2.2 行优先调度为什么浪费：B 的数据被提前逐出

朴素实现按行遍历 block：`(0,0) → (0,1) → (0,2) → …` 一路扫过去。问题在于：算完一整行之后，再回来处理下一行时，**矩阵 B 的同一批数据早被 L2 逐出了**，只能重新从 HBM 读。

[【跳转到 04:28】](https://www.youtube.com/watch?v=W8NFUvYX-u8&t=268)

### 2.3 分组调度：把 4 个 block 当成一个 super block

解法是**分组排序（grouped ordering）**：不再一行行扫，而是把 4 个 block 竖着编成一组，让「用到 A、B 相同部分的 block」在时间上挨在一起，从而在数据被丢弃前多复用几次。

```python
# Optimized grouped ordering implementation to promote L2 data reuse
num_pid_in_group = GROUP_SIZE_M * num_pid_n
group_id = pid // num_pid_in_group
first_pid_m = group_id * GROUP_SIZE_M
group_size_m = min(num_pid_m - first_pid_m, GROUP_SIZE_M)
pid_m = first_pid_m + ((pid % num_pid_in_group) % group_size_m)
pid_n = (pid % num_pid_in_group) // group_size_m
```

注意 `group_size_m` 那一行里的 `min` 取最小值：最后一组可能不满 4 行，要单独处理，否则会越界。这是分组调度里最容易写错的地方。

![行优先与分组排序的代码对比：右侧把 pid 重新映射成竖着走的组](assets/用%20Triton%20手写%20MatMul%20击败%20PyTorch：分块、张量核与自动调优/00288.webp)

这一步**不改一行计算逻辑，只改 block 的执行顺序**，却直接提高了 L2 命中率。它说明一个道理：在访存受限的算子里，调度就是优化。

---

## 三、`@triton.autotune`：把「试参数」这件事自动化

[【跳转到 05:06】](https://www.youtube.com/watch?v=W8NFUvYX-u8&t=306)

### 3.1 硬编码 block size 的问题

第一版 kernel 在调用时把 block size 写死了：

```python
compiled_kernel = matmul_kernel[grid](
    a, b, c,
    M, N, K,
    a.stride(0), a.stride(1),
    b.stride(0), b.stride(1),
    c.stride(0), c.stride(1),
    BLOCK_SIZE_M=64,
    BLOCK_SIZE_N=64,
    BLOCK_SIZE_K=32,
)
```

但作者指出：**最优 block size 取决于太多东西**——矩阵尺寸、GPU 架构、共享内存上限、寄存器压力。要为每种组合都手工搜一遍，是一场噩梦。

![硬编码 block size 的调用点：BLOCK_SIZE_M=64、N=64、K=32](assets/用%20Triton%20手写%20MatMul%20击败%20PyTorch：分块、张量核与自动调优/00306.webp)

[【跳转到 05:43】](https://www.youtube.com/watch?v=W8NFUvYX-u8&t=343)

### 3.2 autotune 做了什么：编译全部、测速全部、留最快的

Triton 的 autotune 机制只有三步，理解了这三步就不会把它当魔法：

1. **用每一组配置各编译一份 kernel**（因为 block size 是 `tl.constexpr`，每组配置都是独立编译产物）；
2. **把每份都跑一遍并计时**；
3. **自动选出最快的那一份**，之后相同条件下的调用直接走它。

![autotune 的两步：先 compile each config，再 benchmark all](assets/用%20Triton%20手写%20MatMul%20击败%20PyTorch：分块、张量核与自动调优/00337.webp)

### 3.3 写法：`triton.Config` 列表 + `key`

启用 autotune 只需要在 kernel 上多加一个装饰器：

```python
@triton.autotune(
    configs=[
        triton.Config({'BLOCK_SIZE_M': 64,  'BLOCK_SIZE_N': 64,  'BLOCK_SIZE_K': 32}),
        triton.Config({'BLOCK_SIZE_M': 128, 'BLOCK_SIZE_N': 128, 'BLOCK_SIZE_K': 32}),
        triton.Config({'BLOCK_SIZE_M': 64,  'BLOCK_SIZE_N': 128, 'BLOCK_SIZE_K': 64}),
        triton.Config({'BLOCK_SIZE_M': 128, 'BLOCK_SIZE_N': 64,  'BLOCK_SIZE_K': 64}),
    ],
    key=[],   # 或 key=['M', 'N', 'K']，如果需要按尺寸分别缓存
)
@triton.jit
def matmul_kernel(...):
    ...
```

两个细节值得停下来看：

- **`triton.Config` 的第一个参数是一个字典**，键名必须和 kernel 里的 `tl.constexpr` 形参同名（这里是 `BLOCK_SIZE_M/N/K`）。多份配置就是「多份候选编译产物」。
- **`key` 决定「什么时候重新调优」**。`key=[]` 表示这个 kernel 只调优一次、全局共用一份结果；`key=['M','N','K']` 表示按形状分别调优、分别缓存——大矩阵和小矩阵各自拿到自己的最优配置。

![autotune 装饰器与 key 的两种写法：key=[] 全局一份，key=['M','N','K'] 按尺寸各一份](assets/用%20Triton%20手写%20MatMul%20击败%20PyTorch：分块、张量核与自动调优/00343.webp)

`key` 的选择本质上是一个权衡：**key 越细，命中率越高但调优次数越多；key 越粗，调优只做一次但配置可能对某些形状不是最优**。视频里 matmul 用 `key=[]` 是为了演示简单；真实项目里如果形状分布很宽（比如 LLM 推理的 prefill 与 decode 差几个数量级），按形状分 key 往往更划算。

### 3.4 autotune 的成本：它是「一次性的」，但不是「免费的」

因为 autotune 要把每份配置都编译并跑一遍，它带来两类成本：

- **编译成本**：配置越多，编译时间越长；
- **预热成本**：第一次遇到某个 key 时要现场测速，这段延迟会落在第一个请求上。

这也解释了为什么生产环境常常把 autotune 的结果缓存下来复用——那是下一篇博客的主题。

---

[【跳转到 05:53】](https://www.youtube.com/watch?v=W8NFUvYX-u8&t=353)

## 四、张量核：一次指令算一个 16×16 的小矩阵

作者把张量核称为「the big one」：**这一项优化的收益超过前面所有优化之和**。

现代 Nvidia GPU 上的张量核（Tensor Core）可以在**一条指令**里完成一个 16×16 的矩阵乘加。在 Triton 里用它，不需要写一行汇编，只要做两件事：

1. **把输入从 float32 换成 float16 或 bfloat16**；
2. **保证 block size 是 16 的倍数**。

Triton 就会自动生成张量核指令。

```python
# 输入用 bf16/fp16，累加器仍用 fp32
accumulator = tl.zeros((BLOCK_SIZE_M, BLOCK_SIZE_N), dtype=tl.float32)
```

第三件事是**数值稳定性**：累加器继续用 float32。低精度只用在「喂给张量核的输入」上，累加过程保持高精度，避免长 $K$ 维累加时的误差堆积。

这也解释了为什么张量核是「有条件的加速」：它换来的是数量级的算力提升，代价是精度下降——**只有当你愿意用低精度时，它才是你的朋友**。

---

## 五、流水线与 occupancy：`num_stages` 和 `num_warps`

最后两个旋钮不是「算法」层面的，而是「硬件利用率」层面的。

[【跳转到 06:46】](https://www.youtube.com/watch?v=W8NFUvYX-u8&t=406)

### 5.1 `num_stages`：让访存和计算重叠

问题是「内存加载很慢」。现代 GPU 可以把访存和计算重叠起来，做法是**软件流水线**：把 k 循环切成若干 stage，当第 $i$ 块还在算的时候，第 $i+1$、$i+2$ 块的加载已经在路上。

作者把 `num_stages` 从 2 提到 5：

```python
num_stages=5,  # 5-6 stages (balance latency hiding vs resources)
num_warps=8    # number of warps (parallelism)
```

stage 越多，能掩盖的访存延迟越长；但每个 stage 都要占用额外的共享内存来暂存数据，**stage 太多会挤占资源、反而降低并发**。所以注释里写的是「5～6 是平衡点」。

### 5.2 `num_warps`：让一个 block 里有更多线程并行

`num_warps` 决定一个 program 用多少个 warp（32 线程为一 warp）来执行。作者把它从 4 提到 8，理由是**提高 GPU occupancy**——让 SM 上有更多可调度的 warp，从而在等待访存时有别的工作可做。

它同样有权衡：warp 越多，每个 warp 分到的寄存器和共享内存越少，可能触发寄存器溢出（spill）。**occupancy 不是越高越好，而是「够高且不溢出」最好**。

![在 triton.Config 里同时指定 num_stages 与 num_warps，注释写明各自的权衡](assets/用%20Triton%20手写%20MatMul%20击败%20PyTorch：分块、张量核与自动调优/00437.webp)

### 5.3 这三个参数为什么必须一起调

到这里可以回答「为什么参数会影响性能」了：

| 参数 | 直接影响的硬件资源 | 调大的收益 | 调大的代价 |
| --- | --- | --- | --- |
| `BLOCK_SIZE_M/N/K` | 共享内存占用、寄存器占用、tile 数量 | 单次搬运的数据更多，复用更好 | 共享内存/寄存器吃紧，occupancy 下降；边界浪费变多 |
| `num_stages` | 共享内存（每 stage 一份缓冲） | 更好地掩盖访存延迟 | 占用更多共享内存，挤掉并发 |
| `num_warps` | 线程数、寄存器文件分配 | 更多并行、更高 occupancy | 每线程寄存器变少，可能 spill |

三者共享同一批硬件资源（共享内存、寄存器），所以**不能独立寻优**——这正是需要 autotune 而不是手工试的原因。

---

[【跳转到 07:27】](https://www.youtube.com/watch?v=W8NFUvYX-u8&t=447)

## 六、最终结果：大多数形状赢，小形状输给 cuBLAS

把上面所有优化叠上去之后，作者跑了最终 benchmark。

中等尺寸（$1024^3$，bf16）的终端输出是：

```
[1/4] PyTorch (cuBLAS)...   0.060 ms, 35.92 TFLOPS
[3/4] Triton Advanced (bfloat16)... 0.055 ms, 38.78 TFLOPS, 1.08x vs PyTorch
```

大尺寸（$2048^3$，bf16）：

```
[1/4] PyTorch (cuBLAS)...   0.409 ms, 42.04 TFLOPS
[3/4] Triton Advanced (bfloat16)... 0.384 ms, 44.78 TFLOPS, 1.07x vs PyTorch
```

![benchmark 终端输出：1024 与 2048 的方阵上，Triton 版分别达到 PyTorch 的 108.0% 与 106.5%](assets/用%20Triton%20手写%20MatMul%20击败%20PyTorch：分块、张量核与自动调优/00452.webp)

但按形状铺开看，结论更诚实：**大多数形状赢，小形状输得很惨**。

![各形状相对 PyTorch cuBLAS 的加速比：1x1536x8960 达 1.34x，而 128x256x1536 只有 0.32x](assets/用%20Triton%20手写%20MatMul%20击败%20PyTorch：分块、张量核与自动调优/00457.webp)

[【跳转到 07:32】](https://www.youtube.com/watch?v=W8NFUvYX-u8&t=452)

### 6.1 为什么小形状会输

作者的解释是：**PyTorch 调用的是 cuBLAS，而 cuBLAS 为每种形状都准备了专门的 kernel**。当 $M=1$ 时，它干脆切换到一套完全不同的算法（本质上是矩阵-向量乘，不需要 tile 化）。

而我们的 kernel 对所有形状都用同一套通用做法：当 $M=1$、`BLOCK_SIZE_M` 取 64 时，一个 64 行的 tile 里只有 1 行是有效数据，**其余 63 行全是 mask 出来的 0，算力全浪费在零上**。

这也说明 autotune 的边界：它能在一组给定配置里挑最好的，但**挑不出「另一种算法」**。要赢小形状，得换 kernel 结构，而不是换参数。

### 6.2 一句话总结这个 trade-off

作者的态度很清醒：这是**纯 Triton、不依赖任何外部库**实现的 kernel，而且完全可控；用通用 kernel 换来了「一套代码打天下」，代价是在极端形状上让位于 cuBLAS 的手工特化。**要不要这么做，取决于你的形状分布是否集中**。

---

## 小结

- **正确性优先**：先写对分块 kernel，`mask` + `other=0.0` 处理边界，`float32` 累加器保证精度。
- **先看访存，再看算力**：H100 上寄存器与 HBM3 相差 41 倍；分组调度（grouped ordering）不改计算、只改 block 顺序，就能提高 L2 命中率。
- **`@triton.autotune` 的本质**：block size 是 `tl.constexpr`，所以每组配置都是独立编译产物；autotune 编译全部、测速全部、留最快的。
- **`key` 决定缓存粒度**：`key=[]` 全局一份，`key=['M','N','K']` 按形状各一份；细 key 更准但调优更贵。
- **张量核是收益最大的一步**：输入换 fp16/bf16、block size 取 16 的倍数、累加器保持 fp32。
- **`num_stages` 与 `num_warps` 是资源博弈**：前者用共享内存换延迟掩盖，后者用寄存器换 occupancy；三者共享资源，必须一起调。
- **autotune 有边界**：它只能在给定配置集里挑最优，挑不出另一种算法；小形状输给 cuBLAS 的特化 kernel 是结构性问题。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| tile / block | 输出矩阵被切出的一小块，一个 GPU program 负责算一块 |
| `tl.constexpr` | 编译期常量；block size 用它声明，所以每组配置都是独立编译产物 |
| mask | 与 tile 同形状的布尔数组，标出哪些位置越界，配合 `other=0.0` 安全加载 |
| grouped ordering | 把若干 block 竖着编组执行，让相邻 program 复用同一批 L2 数据 |
| `@triton.autotune` | 装饰器：按 `configs` 逐份编译、逐份测速、自动选最快的 |
| `triton.Config` | 一组候选参数（block size、`num_warps`、`num_stages` 等） |
| `key` | autotune 的缓存键；决定「什么条件下重新调优」 |
| 张量核 Tensor Core | 一条指令完成 16×16 矩阵乘加的专用单元，需低精度输入 + 16 倍数 block |
| `num_stages` | 软件流水线级数，用共享内存换访存延迟掩盖 |
| `num_warps` | 一个 program 使用的 warp 数，影响 occupancy 与寄存器分配 |
| occupancy | SM 上同时驻留的可调度 warp 比例，太低掩盖不了延迟，太高可能寄存器溢出 |
| cuBLAS | Nvidia 的官方 BLAS 库，为大量形状提供手工特化 kernel |