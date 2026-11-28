# Triton 手写 softmax 前向：从 PyTorch 语义到指针、mask 与归约

> 视频来源：[Coding a Triton Kernel for Softmax (fwd pass)](https://www.youtube.com/watch?v=Z5EcYhGf-Mk)（YouTube · SOTA Deep Learning Tutorials）｜时长约 23 分钟
> 导读：一支「从零把 PyTorch 的 `softmax` 翻译成 Triton 内核」的实操录屏。作者先写 PyTorch 参考实现当靶子，再写 driver program 和 kernel 两段代码，跑通后立刻用肉眼对拍数值——结果第一版就错了，输出行重复。本文按「参考实现 → 驱动程序 → 内核指针 → 归约 → 写回 → 对拍 → 性能」的顺序还原这条改写路径，重点放在**怎样把 PyTorch 的语义逐句落到指针和 mask 上**，以及**怎样用最小代价发现数值不一致**。

## 本讲要解决的核心问题（SCQA）

**背景**：你已经会用 PyTorch 写算子。`torch.softmax(x, dim=1)` 一行就能算完，语义清清楚楚：对每一行做「减最大值、取指数、除以和」。你也知道 GPU 上这类逐行归约是访存瓶颈，想自己写内核来控制数据搬运。

**冲突**：PyTorch 里「一行」是一个逻辑概念，落到 Triton 里却要变成**指针算术**：基址加多少、列偏移怎么生成、超出边界的那些 lane 怎么办、归约沿哪个轴做。这些细节任何一处写错，代码都能跑、不报错，只是**结果悄悄不对**。视频里的作者第一版就踩了这个坑——输出矩阵的每一行都变成了同一行。

**疑问**：把一个 PyTorch 算子改写成 Triton，需要按什么顺序拆解？PyTorch 的每一步（`max`、减法、`exp`、`sum`、除法）分别对应 Triton 的哪个原语？写完之后，怎样用最低成本确认「数值一致」？

**回答（中心思想）**：改写可以拆成固定的五步——**先钉住 PyTorch 参考实现，再把形状信息翻译成驱动参数（grid / block size / num_warps / stride），然后在核心里用 `program_id` 定位一行、用 `arange` 生成列偏移、用 mask 圈出有效数据，接着把逐行归约映射成 `tl.max` / `tl.sum` 并指定 `axis`，最后用同一个 mask 写回**。而数值一致性的验证不必等单元测试框架：**一张 2×5 的小样本 + 三个 `print`，就足以让错误暴露出来**。

---

## 一、改写的起点：一个算子要写两段代码

### 1.1 kernel 与 driver program 的分工

作者开篇先纠正一个常见误解：写 GPU 内核，你实际要写的是**两段**代码。

- **kernel 本身**：一段会被同时启动成千上万份实例的并行代码。
- **driver program（驱动程序）**：负责准备元信息——切多大的块、启动多少个实例、输入输出缓冲在哪、步长是多少。

[【跳转到 00:00】](https://www.youtube.com/watch?v=Z5EcYhGf-Mk&t=0)

这个分工是理解后面所有代码的钥匙：**driver 在 CPU 侧决定「怎么切」，kernel 在 GPU 侧只负责「我这一份怎么算」**。kernel 里永远不出现「总共有多少行」这种全局信息，它只通过 `program_id` 知道自己是第几份。

### 1.2 先把 PyTorch 参考实现钉死

在写任何 Triton 代码之前，作者先手写了一个「naive softmax」作为数值靶子：

```python
def naive_softmax(x: torch.Tensor) -> torch.Tensor:
    """eager mode Softmax"""
    x_max = x.max(dim=1)[0]
    safe_x = x - x_max[:, None]
    numerator = torch.exp(safe_x)
    denominator = numerator.sum(dim=1)
    sm_out = numerator / denominator[:, None]
    return sm_out
```

![PyTorch 参考实现 naive_softmax 与空的 Triton 内核占位：改写时先把语义写清楚，再逐句翻译](assets/Triton%20手写%20softmax%20前向：从%20PyTorch%20语义到指针、mask%20与归约/00475.webp)

[【跳转到 07:55】](https://www.youtube.com/watch?v=Z5EcYhGf-Mk&t=475)

这段代码值得逐行看，因为它就是后面 kernel 的「施工图」：

1. 沿第 1 维（列方向）取每行的最大值：`x.max` 配 `dim=1`；
2. 每行减去自己的最大值：`x_max` 是每行的最大值，用 `[:, None]` 扩成 `(rows, 1)` 以便广播；
3. 取指数：`torch.exp`；
4. 每行求和：`x.sum` 配 `dim=1`；
5. 分子除以分母 —— 归一化，同样是广播。

**这五行就是 kernel 里要复现的五步**，一步都不能少、顺序也不能变。作者特意强调：先有可读的参考实现，后面调 bug 时才有「正确答案」可比。

---

## 二、driver program：把形状信息翻译成内核参数

### 2.1 并行维度决定 grid

softmax 是**逐行独立**的运算：第 $i$ 行的结果只依赖第 $i$ 行。所以最自然的并行方式是「一行一个 program」：

```python
grid = (rows,)
```

[【跳转到 02:30】](https://www.youtube.com/watch?v=Z5EcYhGf-Mk&t=150)

作者的说法很直白：如果有一千行，就相当于同时启动一千份 kernel，每份处理一行。**grid 的形状直接对应「谁和谁可以并行」**，这是改写时第一个要做的判断。

### 2.2 block size 为什么必须是 2 的幂

每个 program 要一次性把整行读进来，所以块大小取列数：

```python
block_size = triton.next_power_of_2(cols)
```

[【跳转到 02:55】](https://www.youtube.com/watch?v=Z5EcYhGf-Mk&t=175)

这里有两个关键点：

- **`next_power_of_2` 向上取整**：一千列会变成 1024。Triton 的 `tl.arange` 要求长度是 2 的幂，这是硬约束。
- **多出来的位置是「假数据」**：1024 的块里只有前 1000 个是真实列，后 24 个是越界区域。它们不能参与归约，否则 max 和 sum 都会被污染——这正是后面 `mask` 存在的理由。

### 2.3 num_warps：线程密度旋钮

块大，就需要更多线程来分摊：

```python
num_warps = 4  # 32 线程/warp
if block_size > 2047:   # 2048
    num_warps = 8
if block_size > 4095:   # 4096
    num_warps = 16
```

[【跳转到 03:45】](https://www.youtube.com/watch?v=Z5EcYhGf-Mk&t=225)

作者把 `num_warps` 解释为「线程密度」：一个 warp 是 32 个线程，取 4 就是 128 个线程一起处理这一行。块越大，需要的线程越多，于是按块大小分档上调。

### 2.4 输出缓冲与 stride

最后是输出缓冲和步长：

```python
sm_out = torch.empty_like(x)      # 与输入同形状、同 dtype、同设备的空壳
_softmax_fwd_kernel[grid](
    sm_out, sm_out.stride(0),
    x,      x.stride(0),
    cols,
    block_size=block_size,
    num_warps=num_warps,
)
return sm_out
```

![driver program 全貌：assert 形状、算 block size、按块大小调 num_warps、grid 按行数、输出用 empty_like](assets/Triton%20手写%20softmax%20前向：从%20PyTorch%20语义到指针、mask%20与归约/00350.webp)

[【跳转到 05:50】](https://www.youtube.com/watch?v=Z5EcYhGf-Mk&t=350)

为什么必须显式传 stride？作者的解释是：**内存里的张量是一维铺开的，逻辑上的二维形状只是视图**。要跳到下一行，就得跨过「一行的宽度」那么多个元素。这个宽度就是 `stride(0)`，对连续的二维张量它恰好等于列数，但显式传参才通用。

注意 `block_size` 在参数表里带 `tl.constexpr` 标记——它会被编译器吸收成常量，不会真的作为运行时参数传进内核。这一点在函数签名里看得最清楚。

---

## 三、kernel 内部：从 program_id 到一行数据的指针

### 3.1 内核签名与行指针

```python
@triton.jit
def _softmax_fwd_kernel(
    output_ptr,
    stride_output_row,
    input_ptr,
    stride_input_row,
    num_cols,
    block_size: tl.constexpr,
):
    row_index = tl.program_id(0)
    row_start_ptr = input_ptr + (row_index * stride_input_row)
```

![内核签名：输出指针、输出行步长、输入指针、输入行步长、列数、块大小（constexpr）](assets/Triton%20手写%20softmax%20前向：从%20PyTorch%20语义到指针、mask%20与归约/00550.webp)

[【跳转到 08:20】](https://www.youtube.com/watch?v=Z5EcYhGf-Mk&t=500)

`tl.program_id` 传入 0 就是「我是第几份」。因为 grid 是一维的（按行），所以取 axis 0。

行指针的算法是**基址 + 行号 × 行步长**：想处理第 3 行，就从左上角出发跳 3 个 stride。这是整个改写里最容易出错、也最值得函数化的一段。

### 3.2 列偏移与 mask

有了行起点，再生成列方向的一串偏移：

```python
col_offsets = tl.arange(0, block_size)
input_pointers = row_start_ptr + col_offsets
row_mask = col_offsets < num_cols
```

![列偏移与指针数组：row_start_ptr + col_offsets 得到整行每个位置的指针，mask 用列偏移与列数比较](assets/Triton%20手写%20softmax%20前向：从%20PyTorch%20语义到指针、mask%20与归约/00700.webp)

[【跳转到 11:15】](https://www.youtube.com/watch?v=Z5EcYhGf-Mk&t=675)

注意这里 `input_pointers` 不是一个指针，而是**一串指针**（长度等于 `block_size`）。Triton 的块级编程就是靠这种「指针数组 + 向量化运算」来表达并行的：你写的是「这一整块」，编译器负责把它拆到线程上。

`row_mask` 表达的是「列偏移小于真实列数」，也就是「哪些列是真的」。作者说这个 mask 会被复用两次——读的时候用一次，写的时候再用一次。

### 3.3 tl.load 的 other：给无效位置一个不参与运算的值

```python
row = tl.load(input_pointers, mask=row_mask, other=float("-inf"))
```

![tl.load 带 mask 与 other=-inf：越界位置填负无穷，保证它在 max 里不会赢、在 exp 后变成 0](assets/Triton%20手写%20softmax%20前向：从%20PyTorch%20语义到指针、mask%20与归约/00800.webp)

[【跳转到 13:20】](https://www.youtube.com/watch?v=Z5EcYhGf-Mk&t=800)

`other` 是「被 mask 掉的位置填什么」。这里填负无穷，理由是它**在两个后续运算里都无害**：

- 求最大值时，$-\infty$ 永远赢不了真实数据；
- 取指数时，$\exp(-\infty - m) = 0$，对求和没有贡献。

如果这里随手填 0，而真实数据里有负数，最大值就会被 0 顶掉，softmax 立刻算错。**`other` 的取值不是随便填的，它必须让被屏蔽的 lane 在后续所有归约里都「不存在」**。

---

## 四、把 softmax 的三步映射成三次归约

### 4.1 max → 减 → exp → sum → 除

进入核心部分，代码几乎就是 `naive_softmax` 的逐句翻译：

```python
row_max    = tl.max(row, axis=0)
safe_row   = row - row_max
numerator  = tl.exp(safe_row)
denominator= tl.sum(numerator, axis=0)
sm_out     = numerator / denominator
```

![softmax 主体：tl.max 求行最大值，减去后取 exp 得分子](assets/Triton%20手写%20softmax%20前向：从%20PyTorch%20语义到指针、mask%20与归约/00850.webp)

[【跳转到 14:10】](https://www.youtube.com/watch?v=Z5EcYhGf-Mk&t=850)

对照 PyTorch 版本，一一对应：

| PyTorch | Triton | 说明 |
| --- | --- | --- |
| `x.max` 配 `dim=1` | `tl.max` 配 `axis=0` | 块内只有一行，所以沿 axis 0 归约 |
| `x` 减 `x_max` | `row` 减 `row_max` | 标量自动广播到整块 |
| `torch.exp` | `tl.exp` | 逐元素 |
| `x.sum` 配 `dim=1` | `tl.sum` 配 `axis=0` | 同样沿 axis 0 |
| `numerator` 除以 `denominator` | 同名变量相除 | 标量广播 |

**唯一容易搞混的是 `axis`**：PyTorch 里 `dim=1` 是「列方向」，而 Triton 里这一整行被压成了一个一维块，所以列方向变成了 `axis=0`。作者在视频里也停顿确认了一下「是 axis 0 吧」——这个转换是改写时的高频错点。

### 4.2 为什么先减最大值

这是数值稳定性问题，不是数学必需。$\exp$ 增长极快，输入稍大（比如 90 以上）就会在 fp32 里溢出成 `inf`，除以 `inf` 得到 `nan`。减掉每行最大值后，最大的那一项变成 $\exp(0)=1$，其余都 $\le 1$，指数运算永远安全。

数学上这个变换是恒等的：

$$
\operatorname{softmax}(x_i) = \frac{e^{x_i - m}}{\sum_j e^{x_j - m}}, \quad m = \max_j x_j
$$

分子分母同乘 $e^{-m}$，值不变，但中间结果被压到了安全区间。

### 4.3 归约发生在片上，不是显存里

作者反复强调的一点：一旦这一行被 `tl.load` 读进片上存储（他用 SRAM 泛指寄存器/共享内存这一层），后面的 max、减、exp、sum 全都在**同一个 kernel 里**完成，不会像 PyTorch eager 那样每步都写回显存再读出来。

代价是**指针算术的开销**：为了换来细粒度的访存控制，你必须手写一堆偏移计算。作者把这称为「性能与开发复杂度之间的交换」。

---

## 五、写回：同一个 mask 再用一次

```python
output_row_ptr = output_ptr + row_index * stride_output_row
output_pointers = output_row_ptr + col_offsets
tl.store(output_pointers, sm_out, mask=row_mask)
```

![写回阶段：输出行指针同样由 program_id 与输出行步长决定，store 复用同一个 row_mask](assets/Triton%20手写%20softmax%20前向：从%20PyTorch%20语义到指针、mask%20与归约/00925.webp)

[【跳转到 15:50】](https://www.youtube.com/watch?v=Z5EcYhGf-Mk&t=950)

写回的逻辑与读入完全对称：**同样的行定位、同样的列偏移、同样的 mask**。mask 在这里的作用是防止把越界位置写进别人的内存——那会直接破坏别的张量，比读错更危险。

到这里，一个能跑的 softmax 前向内核就完整了。作者随即做了一次回顾：定位行 → 算指针 → 建 mask → 读入 → 算 softmax → 写回。**六步，每一步都能对应回 PyTorch 的一行**。

---

## 六、数值对拍：一次「看起来对」的失败

### 6.1 小样本 + 三个 print 是最便宜的验证

作者没有搭测试框架，而是造了一个 2×5 的小样本：

```python
sample = torch.tensor([[1,2,3,4,5], [5,4,3,2,1]], dtype=torch.float32, device='cuda')
ref_out    = F.softmax(sample, dim=1)   # PyTorch 官方实现
eager_out  = naive_softmax(sample)      # 自己写的 PyTorch 参考实现
triton_out = softmax(sample)            # Triton 内核
```

选这个样本是有讲究的：第一行递增、第二行递减，**softmax 之后必然是一升一降**。任何「行错位」「行重复」的问题，肉眼一眼就能看出来，根本不用算数值。

### 6.2 症状：输出行重复

第一次运行，输出是这样的：

![第一次运行的结果：triton_out 的两行完全相同，都是递增序列，第二行本应是递减](assets/Triton%20手写%20softmax%20前向：从%20PyTorch%20语义到指针、mask%20与归约/01075.webp)

[【跳转到 17:55】](https://www.youtube.com/watch?v=Z5EcYhGf-Mk&t=1075)

`ref_out` 和 `eager_out` 都是「升、降」两行，`triton_out` 却是**两行一样的递增序列**。作者的原话是「something's off with our stride」——他一开始怀疑步长。

### 6.3 根因：指针被就地改写

真正的错误在写回那一段。第一版代码是这么写的：

```python
output_ptr = output_ptr + row_index * stride_output_row   # 错：把基址覆盖了
...
```

因为 `output_ptr` 被**就地覆盖**，第二个 program 拿到的「基址」已经是第一个 program 偏移后的地址，于是所有 program 都在往同一行写——最终显存里留下的是最后一次写入的结果，看起来就是「每行都一样」。

作者借这个 bug 说了一句很关键的观察：**这类错误不会让程序崩溃**。没有越界（偏移还在张量范围内）、没有非法访存，只是数据被反复覆盖。所以「跑通了」和「算对了」是两件事。

### 6.4 修复与教训：把指针算术函数化

修复很朴素——换一个变量名，不要动基址：

```python
output_row_ptr = output_ptr + row_index * stride_output_row
output_pointers = output_row_ptr + col_offsets
tl.store(output_pointers, sm_out, mask=row_mask)
```

![修复后的写回与正确输出：triton_out 与 ref_out 完全一致，一行升一行降](assets/Triton%20手写%20softmax%20前向：从%20PyTorch%20语义到指针、mask%20与归约/01150.webp)

[【跳转到 19:10】](https://www.youtube.com/watch?v=Z5EcYhGf-Mk&t=1150)

改完之后三行输出完全一致。作者顺势提出一个工程建议：**把这类指针算术封装成函数**（传入基址、行号、步长，返回行指针），既避免「就地覆盖基址」这类低级错误，也让 kernel 主体更可读。这是他踩坑之后的第一反应，也是这类代码最值得复用的部分。

---

## 七、性能对拍：GB/s 视角下的 Triton、torch 与 eager

数值对了，接下来看快不快。作者沿用了教程里的基准测试脚本：

```python
quantiles = [0.5, 0.2, 0.8]
ms, min_ms, max_ms = triton.testing.do_bench(lambda: softmax(x), quantiles=quantiles)
gbps = lambda ms: 2 * x.nelement() * x.element_size() * 1e-9 / (ms * 1e-3)
```

![基准测试脚本：用 do_bench 取分位数，用「读一遍 + 写一遍」的字节数除以耗时换算成 GB/s](assets/Triton%20手写%20softmax%20前向：从%20PyTorch%20语义到指针、mask%20与归约/01275.webp)

[【跳转到 21:15】](https://www.youtube.com/watch?v=Z5EcYhGf-Mk&t=1275)

指标为什么是 GB/s 而不是 FLOPS？因为 softmax 的算术强度极低：每个元素只做几次加法和一次 exp，却要读一次、写一次。**它几乎必然是带宽瓶颈**，所以用「有效带宽」衡量才合理。公式里的 `2 *` 就是「读 + 写」两趟。

跑在 A10 上的结果（作者也提到在 A100 上跑过）：

- 最小的张量（序列长度约 372）上，Triton 是 372 GB/s，torch 原生是 409 GB/s——**torch 略快**；
- 到 768 附近，Triton 开始反超；
- 张量继续变大，Triton 稳定在 470 GB/s 上下，而 torch 原生一路下滑到 250 GB/s 左右；
- 自己写的 eager 版 `naive_softmax` 只有约 120 GB/s，**慢近三倍**。

![性能曲线：Triton（蓝）随规模上升后稳定在约 470 GB/s，torch 原生（绿）在大规模上掉到约 250 GB/s，eager 版（虚线）始终在 120 GB/s 附近](assets/Triton%20手写%20softmax%20前向：从%20PyTorch%20语义到指针、mask%20与归约/01344.webp)

[【跳转到 22:29】](https://www.youtube.com/watch?v=Z5EcYhGf-Mk&t=1349)

作者对这个形状的解读是：**torch 显然针对常见的小规模场景做过调优**（小张量上它更快），但规模一大就掉队；而 Triton 内核一旦块大小设置合理，带宽利用率能一直维持在较高水平。这也回答了「为什么要自己写内核」——不是为了在所有尺寸上赢，而是为了在**你关心的那个尺寸区间**上不被框架的通用策略拖住。

---

## 小结

- **一个算子要写两段代码**：driver program 决定「怎么切」，kernel 只回答「我这一份怎么算」。改写时先写 driver，能逼你把形状、步长、块大小想清楚。
- **改写顺序是固定的**：钉住 PyTorch 参考实现 → 决定并行维度（这里按行）→ 算块大小（`next_power_of_2`）→ 生成列偏移 → 建 mask → 归约 → 写回。
- **`axis` 会变**：PyTorch 的 `dim=1`（列方向）在「一行压成一维块」的 Triton 里变成 `axis=0`，这是高频错点。
- **`other` 不是随便填的**：被 mask 的位置必须填一个在后续归约里「不存在」的值，softmax 里用 $-\infty$。
- **mask 要用两次**：读一次防止读到别人的数据，写一次防止覆盖别人的内存。
- **数值验证不必等框架**：一个递增 + 一个递减的小样本，三个 `print`，就能让「行重复」这种静默错误立刻现形。
- **指针算术要函数化**：把基址变量就地改写（`output_ptr` 被重新赋值为「基址 + 行偏移」）是这类 bug 的典型来源，换个变量名或封装成函数即可根治。
- **性能看 GB/s**：softmax 是带宽瓶颈算子，用有效带宽对比才有意义；Triton 在小尺寸上未必赢，但在大尺寸上能明显拉开差距。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| driver program | 在 CPU 侧准备 grid、块大小、步长、输出缓冲的那段 Python 代码 |
| `tl.program_id` | 当前这份 kernel 实例的编号，用来定位「我处理第几行」 |
| `tl.arange` | 生成从 0 到 block_size 减 1 的连续整数，用作列偏移 |
| `tl.constexpr` | 编译期常量标记，值会被编译器吸收，不占运行时参数 |
| block size | 一次处理的元素个数，必须是 2 的幂，通常取列数向上取整 |
| `num_warps` | 参与执行一个 program 的 warp 数，一个 warp 为 32 线程 |
| mask | 布尔数组，标记哪些位置是有效数据，读和写各用一次 |
| `other` | `tl.load` 对被 mask 位置填入的替代值 |
| `tl.max` / `tl.sum` | 块内归约原语，用 `axis` 指定沿哪一维归约 |
| stride | 从一行跳到下一行需要跨过的元素个数，连续二维张量中等于列数 |
| `torch.empty_like` | 按输入的形状、dtype、设备分配一块未初始化的输出缓冲 |
| 有效带宽（GB/s） | 读写字节数除以耗时，衡量访存瓶颈算子的核心指标 |