# 用 Triton 手写 LayerNorm（1）：前向内核与 PyTorch 对拍

> 视频来源：[Triton Layernorm Kernel | A MyTorch Sidequest](https://www.youtube.com/watch?v=DdDr6VXftig)（YouTube · Priyam Mazumdar）｜时长约 46 分钟
> 导读：这支视频完整实现了 LayerNorm 的前向与反向两个 Triton 内核，并逐项与 PyTorch 对拍。因为信息量太大，本文拆成两篇：**本篇（前向）**讲「PyTorch 的逐向量归一化怎样变成一个 PID 处理一行、一次内核启动完成」，以及为什么要在前向里**额外存下两个每行一个数的中间量**；**下一篇（反向）**讲跨 PID 的梯度累加、`atomic_add` 与 `dx` 的推导落地。视频里作者用的是自己搭的 CuPy 张量后端（MyTorch），所以代码里会出现 DLPack 转换和指针 dtype 标记——这些是框架细节，本文会标出来，读的时候不必被它们绊住。

## 本讲要解决的核心问题（SCQA）

**背景**：LayerNorm 是 Transformer 里最常见的归一化层，公式很短：对每个向量求均值、方差，减均值除标准差，再乘 `gamma` 加 `beta`。用 PyTorch 写出来不到十行，跑得也对。

**冲突**：这十行 PyTorch 代码背后是**七到八次独立的内核启动**——求均值一次、求方差一次、减法一次、除法一次、乘 gamma 一次、加 beta 一次、reshape 又一次……每一次都要把中间结果写回显存再读出来。LayerNorm 本身算术强度极低，这些往返几乎全是浪费。

**疑问**：能不能把这一串小算子**融合成一个内核**？融合之后，原来由 PyTorch 自动管理的「每个向量一个标量」的中间结果该放在哪？哪些必须存下来，哪些可以重算？

**回答（中心思想）**：可以融合，而且融合的骨架非常固定——**一个 PID 负责一行**，把整行读进片上存储后，均值、方差、归一化、仿射全在同一个 kernel 里算完，只写回一次输出。真正需要设计的不是公式，而是两个工程决策：**块大小必须是 2 的幂，所以要用 mask 处理越界位置**；**反向要用到前向算过的 `mean` 和 `inv_var`，它们每行只有一个数、存储极便宜，所以前向就顺手存下来**。

---

## 一、LayerNorm 的语义：逐向量归一化，再缩放平移

### 1.1 公式

给定一个 $N \times E$ 的输入（$N$ 个样本，每个样本是长度 $E$ 的向量），LayerNorm 对**每一个向量单独**做归一化：

$$
\mu = \frac{1}{N}\sum_{i=1}^{N} x_i, \qquad
\sigma^2 = \frac{1}{N}\sum_{i=1}^{N}(x_i - \mu)^2
$$

$$
\hat{x}_i = \frac{x_i - \mu}{\sqrt{\sigma^2 + \epsilon}}, \qquad
y_i = \gamma \hat{x}_i + \beta
$$

![前向公式：均值、方差、归一化、仿射四步，全部在单个向量内部完成](assets/用%20Triton%20手写%20LayerNorm（1）：前向内核与%20PyTorch%20对拍/00076.webp)

[【跳转到 01:16】](https://www.youtube.com/watch?v=DdDr6VXftig&t=76)

作者特别强调「**每一个向量单独**」这一点，因为它直接决定了并行方式：向量之间没有任何依赖，所以可以放心地让一个 program 处理一个向量。

公式里的 $\epsilon$ 是个很小的常数（代码里取 `1e-5`），作用是防止方差为 0 时除零。

### 1.2 gamma 和 beta 是可选的

`gamma`（缩放）和 `beta`（平移）是**可学习参数**，形状都是长度 $E$ 的向量。作者提到一个工程现实：很多现代架构干脆不用这两个参数（比如 RMSNorm 就没有），所以内核里把它们做成**可选**——传 `None` 就退化成「只归一化、不缩放不平移」。

这一点在代码里表现为一串「`gamma_ptr` 是否为 `None`」的分支。初看会觉得啰嗦，但它让同一个内核同时服务两种配置。

### 1.3 广播：为什么反向要对 N 求和

`gamma` 只有一个向量，却要作用在 $N$ 行上。实现上靠**广播**：把 `gamma` 复制 $N$ 份对齐到每一行。

前向没有问题，但作者提前点出了它对反向的影响：**同一个 `gamma` 元素被 $N$ 行共用，所以反向时这 $N$ 份梯度必须加回同一个位置**。这就是反向里那个 $\sum_{i=1}^{N}$ 的来源，也是下一篇要讲的 `atomic_add` 的动机。

---

## 二、先写 PyTorch 参考实现，再数一数它启动了几次内核

### 2.1 naive 实现

和 softmax 那篇一样，改写的第一步是钉住参考实现：

```python
def layer_norm_naive(x, weight, bias=None, eps=1e-5):
    *dims, embed_dim = x.shape

    if len(dims) > 1:
        x_reshaped = x.reshape(-1, embed_dim)
    else:
        x_reshaped = x

    mean = x_reshaped.mean(axis=-1, keepdims=True)
    var  = x_reshaped.var(axis=-1, keepdims=True)
    normed = (x_reshaped - mean) / (cp.sqrt(var + eps))

    out = normed * weight.reshape(1, -1)
    if bias is not None:
        out = out + bias.reshape(1, -1)

    if len(dims) > 1:
        out = out.reshape(*dims, embed_dim)
    return out
```

![PyTorch 参考实现：先 reshape 成 (N, E)，再沿最后一维求均值方差，最后 reshape 回去](assets/用%20Triton%20手写%20LayerNorm（1）：前向内核与%20PyTorch%20对拍/00668.webp)

[【跳转到 09:53】](https://www.youtube.com/watch?v=DdDr6VXftig&t=593)

几个值得注意的细节：

- 第一行把最后一维单独摘出来，前面所有维度都算「样本维」。输入可以是 `(a, b, c, d, E)` 这种任意形状，一律 flatten 成 `(N, E)`。
- `keepdims=True` 是为了让 `mean` 的形状是 `(N, 1)`，能直接和 `(N, E)` 广播相减。
- `weight.reshape(1, -1)` 把 `(E,)` 变成 `(1, E)`，同样是靠广播铺到 $N$ 行——这就是 1.3 节说的那件事。
- 视频里用的是 `cp.sqrt`，因为作者的张量后端是 CuPy；换成 PyTorch 就是 `torch.sqrt`，语义完全一样。

### 2.2 七到八次内核启动

作者一行行数下来：求均值一次、求方差一次、减法一次、除法一次、乘 `weight` 一次、加 `bias` 一次、两次 reshape 各自也要动一次数据——**七到八次内核启动**。

[【跳转到 11:08】](https://www.youtube.com/watch?v=DdDr6VXftig&t=668)

这就是融合的动机：如果能把它们塞进一个 kernel，中间结果就只存在于片上存储，一次读、一次写，剩下的全在寄存器里完成。

---

## 三、驱动程序：一个 PID 一行

### 3.1 形状与 block size

```python
def fused_layer_norm_forward(x, gamma=None, beta=None, eps=1e-5,
                             training=True, use_dlpack=True):
    n_rows, n_cols = x.shape
    BLOCK_SIZE = triton.next_power_of_2(n_cols)
```

![驱动程序开头：n_rows / n_cols 与 next_power_of_2 得到的 BLOCK_SIZE](assets/用%20Triton%20手写%20LayerNorm（1）：前向内核与%20PyTorch%20对拍/00780.webp)

[【跳转到 12:23】](https://www.youtube.com/watch?v=DdDr6VXftig&t=743)

块大小默认取列数，因为**一个 PID 要一次处理完整个向量**。但 Triton 有个硬约束：块大小必须是 2 的幂。所以列数为 7 时块大小得取 8，多出来的那个位置是越界的。

作者补充了一句实务经验：嵌入维度通常本来就设成 512、1024、2048、4096 这种 2 的幂，所以越界浪费不严重；但**代码不能依赖这个假设**，mask 必须写。

### 3.2 输出与「训练才需要的中间量」

```python
    y = torch.empty_like(x)                       # 输出，形状与输入一致
    mean    = torch.empty(n_rows, dtype=x.dtype, device=x.device) if training else None
    inv_var = torch.empty(n_rows, dtype=x.dtype, device=x.device) if training else None
```

[【跳转到 14:15】](https://www.youtube.com/watch?v=DdDr6VXftig&t=855)

注意这两个张量的形状是长度 `n_rows` 的一维向量——**每行只有一个数**。这是整支视频最重要的设计决策，第 7 节会专门展开。

`training` 为假（推理）时它们都是 `None`，内核里对应的写入分支会被跳过。作者的理由很直接：推理不做反向，存了也没人用，白白多一次写显存。

### 3.3 stride 与 dtype flag

```python
    stride_x = x.stride(0)
    stride_y = y.stride(0)
    dtype_flag = 0 if x.dtype == torch.float32 else 1
    grid = (n_rows,)
```

`grid` 是一个只含行数的单元素元组，意思是「启动 n_rows 份 kernel，每份处理一行」，和 softmax 那篇完全一样的思路。

`dtype_flag` 是作者这套 CuPy 后端特有的：Triton 不认识 CuPy 的张量类型，所以要把「数据是 fp32 还是 fp16」作为编译期常量传进去，让内核自己把指针 cast 到正确的类型。**如果你直接用 PyTorch 张量，这一步不需要**——Triton 会自己推断。

```python
    if use_dlpack:
        x     = torch.utils.dlpack.from_dlpack(x)
        if gamma is not None: gamma = torch.utils.dlpack.from_dlpack(gamma)
        if beta  is not None: beta  = torch.utils.dlpack.from_dlpack(beta)
```

DLPack 是一个跨框架的张量交换协议，好处是**零拷贝**：CuPy 数组转成 torch 张量不复制数据，只是换了个「壳」。作者说得很清楚：如果你的数据本来就在 torch 里，这段完全没有必要。

---

## 四、内核：指针、mask、加载

### 4.1 签名

```python
@triton.jit
def layer_norm_kernel_forward_training(
    output_ptr,
    inv_var_ptr,        # 反向需要 (N,)，推理时可以是 None
    mean_ptr,           # 反向需要 (N,)，推理时可以是 None
    input_ptr,
    gamma_ptr,          # 1D 向量，所有样本共享 (E,)，没有权重时是 None
    beta_ptr,           # 1D 向量，所有样本共享 (E,)，没有偏置时是 None
    input_row_stride,
    output_row_stride,
    DTYPE_FLAG: tl.constexpr,
    eps: tl.constexpr,
    n_cols: tl.constexpr,
    BLOCK_SIZE: tl.constexpr,
):
```

![内核签名：输出、两个「每行一个数」的中间量、输入、gamma/beta、两个 stride，以及四个编译期常量](assets/用%20Triton%20手写%20LayerNorm（1）：前向内核与%20PyTorch%20对拍/01150.webp)

[【跳转到 18:45】](https://www.youtube.com/watch?v=DdDr6VXftig&t=1125)

签名基本就是驱动程序那张参数表的镜像。值得留意的是**哪些标了 `tl.constexpr`**：`DTYPE_FLAG`、`eps`、`n_cols`、`BLOCK_SIZE` 都是编译期常量，编译器可以据此展开循环、省掉分支。把它们标出来是 Triton 性能调优的常规操作。

进入内核的第一件事是把指针 cast 成正确的 dtype：

```python
    pointer_dtype = tl.float32 if DTYPE_FLAG == 0 else tl.float16
    output_ptr = tl.cast(output_ptr, tl.pointer_type(pointer_dtype))
    input_ptr  = tl.cast(input_ptr,  tl.pointer_type(pointer_dtype))
    if gamma_ptr is not None:
        gamma_ptr = tl.cast(gamma_ptr, tl.pointer_type(pointer_dtype))
    ...

    row_start_ptr = input_ptr + row_idx * input_row_stride
```

![把每个指针 cast 到 fp32 或 fp16，再算出行起点：这一段是 CuPy 后端特有的，直接用 PyTorch 张量时 Triton 会自动推断](assets/用%20Triton%20手写%20LayerNorm（1）：前向内核与%20PyTorch%20对拍/01292.webp)

[【跳转到 19:35】](https://www.youtube.com/watch?v=DdDr6VXftig&t=1175)

作者再次提醒：**如果你直接传 PyTorch 张量，这一整段都不需要**，Triton 会自己处理类型。它出现在这里，纯粹是因为这套代码要同时服务 CuPy 张量。

### 4.2 行指针与列偏移

```python
    row_idx = tl.program_id(0)
    row_start_ptr = input_ptr + row_idx * input_row_stride
    col_offsets = tl.arange(0, BLOCK_SIZE)
    mask = col_offsets < n_cols
    input_ptrs = row_start_ptr + col_offsets
```

![行指针与列偏移：program_id 定位到第几行，arange 生成列偏移，mask 用列偏移与列数比较](assets/用%20Triton%20手写%20LayerNorm（1）：前向内核与%20PyTorch%20对拍/01399.webp)

[【跳转到 21:32】](https://www.youtube.com/watch?v=DdDr6VXftig&t=1292)

作者用一张图解释 `row_start_ptr`：`input_ptr` 指向矩阵左上角，`row_idx` 是「我在第几行」，乘上行步长就是「要往下跳几行」。**这只是起点**，还要加上列偏移才能覆盖整行；而块大小可能大于列数，所以末尾会「溢出」到无效区域，必须用 mask 圈住。

### 4.3 为什么 other=0 在这里是安全的

```python
    if gamma_ptr is not None:
        gamma_ptrs = gamma_ptr + col_offsets
        gammas = tl.load(gamma_ptrs, mask=mask, other=0.0)

    if beta_ptr is not None:
        beta_ptrs = beta_ptr + col_offsets
        betas = tl.load(beta_ptrs, mask=mask, other=0.0)

    row = tl.load(input_ptrs, mask=mask, other=0.0)
```

![加载 gamma、beta 与整行数据，三者都用同一个 mask，越界位置填 0](assets/用%20Triton%20手写%20LayerNorm（1）：前向内核与%20PyTorch%20对拍/01487.webp)

[【跳转到 23:19】](https://www.youtube.com/watch?v=DdDr6VXftig&t=1399)

softmax 里 `other` 填的是 $-\infty$，这里却填 `0.0`——不是随手换的，而是因为**后面的运算对无效位置的处理方式不同**：

- `gamma`/`beta` 的无效位置填 0：因为最后是「乘以 gamma、加上 beta」，乘 0 得 0、加 0 不变，天然无害。
- 数据行的无效位置填 0：因为求和时不贡献值。但这带来一个副作用——**均值是对的，方差会被污染**（无效位置的值是 0，减完均值就变成 $-\mu$，平方后加进方差里）。所以下一步必须用 `tl.where` 把它们重新清零。

**这就是「`other` 填什么」的真正判据：不是看它像不像数据，而是看它在后续每一步运算里会不会产生副作用。**

---

## 五、行内归约：mean、center、variance、rsqrt

### 5.1 均值

```python
    row_mean = tl.sum(row, axis=0) / n_cols
```

[【跳转到 24:47】](https://www.youtube.com/watch?v=DdDr6VXftig&t=1487)

因为整行被压成了一个一维块，`axis=0` 就是「沿这一行求和」。除以 `n_cols`（真实列数，不是块大小）得到均值——无效位置是 0，对求和没有贡献，所以这个均值是准的。

### 5.2 tl.where 把无效位置清零

```python
    row_mean_centered = tl.where(mask, row - row_mean, 0.)
```

![tl.where 版中心化：有效位置减均值，无效位置直接置 0](assets/用%20Triton%20手写%20LayerNorm（1）：前向内核与%20PyTorch%20对拍/01572.webp)

[【跳转到 25:37】](https://www.youtube.com/watch?v=DdDr6VXftig&t=1537)

这一行是整个前向里最容易被忽略、也最容易写错的地方。如果直接写「`row` 减 `row_mean`」，无效位置会变成 `-row_mean`，它们的平方和会把方差抬高，最终**归一化结果整体偏小**。

`tl.where(mask, a, b)` 的语义是「mask 为真的位置取 a，否则取 b」。这里就是「有效位置做减法，无效位置归零」。作者说这只是众多写法之一，但**最直观**。

### 5.3 方差与 rsqrt

```python
    row_var = tl.sum(row_mean_centered * row_mean_centered, axis=0) / n_cols
    inv_var = tl.rsqrt(row_var + eps)
    normed  = row_mean_centered * inv_var
```

[【跳转到 27:03】](https://www.youtube.com/watch?v=DdDr6VXftig&t=1623)

方差就是「中心化后平方再求平均」，和公式一一对应。

`tl.rsqrt(x)` 是 $1/\sqrt{x}$ 的硬件近似指令。用它而不是「`tl.sqrt` 再取倒数」，是因为 GPU 上有一条专门的倒数平方根指令，一条顶两条。这里算出的 `inv_var` 会被复用两次——一次在前向的 `normed` 里，一次存下来给反向用。

### 5.4 仿射：可选分支

```python
    if gamma_ptr is not None:
        output = normed * gammas
    else:
        output = normed

    if beta_ptr is not None:
        output += betas
```

![仿射变换：有 gamma 就乘、有 beta 就加，都没有则输出就是归一化结果](assets/用%20Triton%20手写%20LayerNorm（1）：前向内核与%20PyTorch%20对拍/01644.webp)

[【跳转到 27:24】](https://www.youtube.com/watch?v=DdDr6VXftig&t=1644)

对应公式 $y = \gamma\hat{x} + \beta$，两个参数各自独立可选。到这里，公式里的四步全部落地。

---

## 六、写回：输出与两个「每行一个数」的中间量

### 6.1 输出

```python
    output_row_start_ptr = output_ptr + row_idx * output_row_stride
    output_ptrs = output_row_start_ptr + col_offsets
    tl.store(output_ptrs, output, mask=mask)
```

![写回输出：与读入完全对称的行定位 + 列偏移 + 同一个 mask](assets/用%20Triton%20手写%20LayerNorm（1）：前向内核与%20PyTorch%20对拍/01756.webp)

[【跳转到 28:51】](https://www.youtube.com/watch?v=DdDr6VXftig&t=1731)

和 softmax 一样，写回是读入的镜像：**同样的行号、同样的列偏移、同样的 mask**。mask 在这里防止把越界位置写进别人的内存。

### 6.2 存下 mean 与 inv_var

```python
    if mean_ptr is not None and inv_var_ptr is not None:
        mean_row_ptrs = mean_ptr + row_idx
        tl.store(mean_row_ptrs, row_mean)

        inv_var_row_ptrs = inv_var_ptr + row_idx
        tl.store(inv_var_row_ptrs, inv_var)
```

[【跳转到 29:16】](https://www.youtube.com/watch?v=DdDr6VXftig&t=1756)

注意这里的指针算术**没有列偏移**：`mean` 和 `inv_var` 是长度 `n_rows` 的一维向量，每个 PID 只写自己那一个位置。作者用一张示意图强调这个区别——二维数组要「跨 stride」，一维向量只需「加行号」。

这个 `if` 同时也是「是否在训练」的开关：推理时两个指针都是 `None`，这两次写入被整个跳过。

---

## 七、存储还是重算：一个贯穿所有训练内核的取舍

为什么要在前向里存 `mean` 和 `inv_var`？作者的解释是**反向会用到它们**：

- 反向要算 $\hat{x} = (x - \mu)\cdot \frac{1}{\sqrt{\sigma^2+\epsilon}}$，而 $\mu$ 和 $1/\sqrt{\sigma^2+\epsilon}$ 恰好在前向已经算过；
- 它们的形状是长度 `n_rows` 的一维向量，**每行只有一个数**，存储成本极低；
- 重算反而更贵——要重新扫一遍整行。

于是结论是「存」。但作者马上给了反例：**FlashAttention 就不能这么干**。它如果要存中间结果，得存 $N \times N$ 的注意力矩阵，代价高到不可接受；那里宁可**在反向时重算**。

[【跳转到 16:15】](https://www.youtube.com/watch?v=DdDr6VXftig&t=975)

所以这条判据可以写成一句话：

> **要存的量如果是「每行一个数」，存；如果是「每行一整行」，重算。**

这也是作者说的「推理内核意外地简单」的原因——推理根本没有反向，不需要为反向预留任何东西，只要把融合做好就行。

---

## 小结

- **LayerNorm 是逐向量运算**，所以并行粒度天然是「一个 PID 一行」，`grid` 只含行数。
- **块大小必须是 2 的幂**（`triton.next_power_of_2` 作用于列数），越界位置靠 mask 圈住；嵌入维度通常是 2 的幂，但不能依赖这个假设。
- **`other` 的取值取决于后续运算**：`gamma`/`beta` 填 0 无害，数据行填 0 后必须用 `tl.where` 把无效位置重新清零，否则方差会被污染。
- **`axis=0` 是「沿这一行」**：整行被压成一维块后，PyTorch 里的 `dim=-1` 就变成了 `axis=0`。
- **`tl.rsqrt` 比 `1/tl.sqrt` 更省**：一条硬件指令顶两条，而且结果要复用两次。
- **前向顺手存 `mean` 与 `inv_var`**：每行一个数，存储极便宜，反向直接拿来重算 $\hat{x}$。
- **存还是重算，看「每行一个数」还是「每行一整行」**：LayerNorm 存，FlashAttention 重算。
- **融合的收益来自消除中间往返**：PyTorch 版七到八次内核启动，融合后只剩一次读、一次写。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| LayerNorm | 对每个样本向量单独做减均值除标准差，再乘 gamma 加 beta |
| `epsilon` | 加在方差上的极小常数，防止除零，通常取 `1e-5` |
| `triton.next_power_of_2` | 把列数向上取整到 2 的幂，作为块大小 |
| `tl.program_id` | 当前实例编号，这里等于行号 |
| `tl.arange` | 生成从 0 到 BLOCK_SIZE 减 1 的列偏移 |
| mask | 布尔数组，标记哪些列是真实数据 |
| `other` | `tl.load` 对越界位置填的替代值 |
| `tl.sum` | 沿整行求和（`axis=0`），得到标量 |
| `tl.where(cond, a, b)` | 按条件逐元素二选一，这里用来把无效位置清零 |
| `tl.rsqrt` | 倒数平方根，即 $1/\sqrt{x}$，一条硬件指令 |
| `inv_var` | 逆标准差 $1/\sqrt{\sigma^2+\epsilon}$，前向算一次、反向复用 |
| DLPack | 跨框架零拷贝张量交换协议，CuPy 数组可直接转成 torch 张量 |
| `tl.constexpr` | 编译期常量，值在编译时确定，不占运行时参数 |