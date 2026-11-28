# 用 Triton 手写 LayerNorm（2）：反向传播与原子累加

> 视频来源：[Triton Layernorm Kernel | A MyTorch Sidequest](https://www.youtube.com/watch?v=DdDr6VXftig)（YouTube · Priyam Mazumdar）｜时长约 46 分钟
> 导读：这是两篇中的第二篇，接续[前向内核](用%20Triton%20手写%20LayerNorm（1）：前向内核与%20PyTorch%20对拍.md)。前向把「七到八次内核启动」压成一次，反向的难点则完全不同：**`gamma` 被 N 行共享，梯度必须跨 PID 累加**，而 PID 之间不能直接通信。本文沿着「公式为什么长这样 → 竞态怎么发生 → `atomic_add` 怎么解决 → 指针怎么分两类 → 为什么重算 $\hat{x}$ → 对拍结果」这条线展开。

## 本讲要解决的核心问题（SCQA）

**背景**：前向已经跑通，`mean` 和 `inv_var` 也按计划存了下来。现在要写反向：给定上游梯度 $dy$，算出 $dx$、$d\gamma$、$d\beta$ 三样东西。

**冲突**：$dx$ 好办，一行一行算就行；但 $d\gamma$ 和 $d\beta$ 的形状是长度 $E$ 的向量，而**每一行都要往同一个位置贡献梯度**。在 Triton 里，一行对应一个 PID，PID 之间是并行的、没有共享内存、也不能互相求和。如果直接写 `+=`，所有 PID 会同时读到同一个旧值再各自加，结果互相覆盖——这就是竞态（race condition）。

**疑问**：PyTorch 里一句「沿第 0 维求和」就能解决的事，在 Triton 里怎么落地？既然不能跨 PID 求和，那这个和由谁来做？做了之后又怎么保证数值正确、精度够？

**回答（中心思想）**：把「求和」从**时间上的归约**换成**空间上的累加**——预先分配一个全零的 `dgamma` 缓冲，每个 PID 用 `tl.atomic_add` 把自己的贡献原子地加进去。`atomic_add` 保证同一地址上的加法串行执行，于是 N 个 PID 的贡献被安全地累加成一份结果。配套的两个工程决策是：**累加器用 fp32**（避免 fp16 累加丢精度），**$\hat{x}$ 用 `mean` 和 `inv_var` 在反向现场重算**（比存一整个 `(N, E)` 的中间张量便宜得多）。

---

## 一、反向要算三个东西

### 1.1 公式

给定 $y_i = \gamma \hat{x}_i + \beta$ 和上游梯度 $g_i = \partial L/\partial y_i$，LayerNorm 的反向需要：

$$
\frac{\partial L}{\partial \gamma} = \sum_{i=1}^{N} g_i \hat{x}_i,
\qquad
\frac{\partial L}{\partial \beta} = \sum_{i=1}^{N} g_i
$$

$$
\frac{\partial L}{\partial x} = \frac{1}{\sqrt{\sigma^2+\epsilon}}\left[\hat{g} - \operatorname{mean}(\hat{g}) - \hat{x}\cdot\operatorname{mean}(\hat{g}\odot\hat{x})\right]
$$

其中 $\hat{g} = g \cdot \gamma$ 是「穿过 gamma 之后的上游梯度」，$\odot$ 表示逐元素相乘。

![反向公式：dgamma 与 dbeta 是对 N 行求和，dx 里则出现了两个 mean 项](assets/用%20Triton%20手写%20LayerNorm（2）：反向传播与原子累加/02466.webp)

[【跳转到 04:27】](https://www.youtube.com/watch?v=DdDr6VXftig&t=267)

作者没有现场推导这三条式子，而是直接引用（他说推导在另一支「手写 Transformer」的视频里）。本文也照此处理：**把公式当既定事实，重点看它怎样变成代码**。

### 1.2 那个 Σ 是广播留下的账

为什么 $d\gamma$ 要跨 N 行求和？作者的追问很到位：「这个 sum 是从哪来的？」

答案是**前向的广播**。前向里 `gamma` 只有一个长度 $E$ 的向量，却乘在了 $N$ 行上——实现上是把它复制了 $N$ 份。反向时，每一行都会算出自己那份「对 gamma 的梯度」，形状是 $(N, E)$；但 `gamma` 只有 $(E,)$，形状对不上。

![广播累加示意：dGamma 是 (N, E) 的矩阵，gamma 只有 (E,)，所以必须把 N 行加起来](assets/用%20Triton%20手写%20LayerNorm（2）：反向传播与原子累加/00361.webp)

[【跳转到 06:01】](https://www.youtube.com/watch?v=DdDr6VXftig&t=361)

这不是「形状不匹配的 bug」，而是**广播的数学后果**：同一个 `gamma` 元素被 $N$ 行共用，所以这 $N$ 份梯度贡献都必须还给它。加起来，就是公式里那个 $\sum_{i=1}^{N}$。

---

## 二、跨 PID 求和：为什么必须用 atomic_add

### 2.1 一个 PID 一行，但 gamma 只有一个

前向的并行结构是「一个 PID 一行」。到了反向，这个结构带来一个麻烦：**每个 PID 都想往同一个 `dgamma` 向量里写**。

作者的原话是：「我们不能简单地在 PID 之间求和，那不是它工作的方式。」PID 是独立的执行实例，没有跨实例的归约原语。所以只能换个思路——**创建一个累加器**：先分配一个全零的长度 $E$ 的向量，让每个 PID 把自己的贡献加进去。

### 2.2 竞态：四个 PID 都读到 0

问题在于「加进去」这个动作本身。作者用一组数字演示了错误发生的过程：

假设四个 PID 同时要往同一个位置累加，贡献分别是 1、2、3、4，初始值是 0。

- 如果它们**同时读到 0**，各自算 `0 + 自己的值`，再写回；
- 那么四个 PID 分别认为结果应该是 1、2、3、4；
- 最终留在内存里的，是**最后一次写入的值**，而不是 1+2+3+4=10。

[【跳转到 07:18】](https://www.youtube.com/watch?v=DdDr6VXftig&t=438)

这就是经典的读-改-写竞态：**并发的加法不是加法**。

### 2.3 atomic_add 把并发变成排队

`atomic_add` 的作用是让「读-改-写」这一整段变成**不可分割**的操作：一个线程做完，下一个才能开始。

![Atomic Add 示意：每一行的梯度（紫）原子地累加到同一个 dGamma 向量（灰）的对应位置](assets/用%20Triton%20手写%20LayerNorm（2）：反向传播与原子累加/00438.webp)

[【跳转到 08:08】](https://www.youtube.com/watch?v=DdDr6VXftig&t=488)

作者把它描述成「排队」：一个线程完成累加后，下一个才轮到。代价是**串行化**——这正是原子操作的性能成本。但在 LayerNorm 这里，累加的量只有长度 $E$ 的一小段，串行化的代价可以接受。

---

## 三、驱动程序：fp32 累加器与输出缓冲

```python
def fused_layer_norm_backward(x, mean, inv_var, dy, gamma=None, beta=None,
                              use_dlpack=True):
    ...
    grad_dtype = torch.float32
    dx     = torch.empty_like(dy)
    dgamma = torch.zeros(n_cols, dtype=grad_dtype, device=dy.device) if gamma is not None else None
    dbeta  = torch.zeros(n_cols, dtype=grad_dtype, device=dy.device) if beta is not None else None

    stride_x  = x.stride(0)
    stride_dx = dx.stride(0)
    stride_dy = dy.stride(0)
    dtype_flag = 0 if dy.dtype == torch.float32 else 1

    grid = (n_rows,)
    layer_norm_kernel_backward[grid](
        x, gamma, mean, inv_var, dx, dgamma, dbeta, dy,
        stride_x, stride_dx, stride_dy, n_cols, BLOCK_SIZE, dtype_flag,
    )
```

![反向驱动程序：dx 用 empty_like，dgamma/dbeta 用 zeros 且强制 fp32，grid 仍是每行一个 PID](assets/用%20Triton%20手写%20LayerNorm（2）：反向传播与原子累加/01931.webp)

[【跳转到 32:11】](https://www.youtube.com/watch?v=DdDr6VXftig&t=1931)

三个细节值得单独说：

- **`dgamma` / `dbeta` 用 `torch.zeros` 而不是 `empty`**：它们是累加器，初值必须是 0，否则会加到一个随机数上。
- **强制 `dtype=torch.float32`**：作者明确说这是「为了最大精度」。如果参数是 fp16，用 fp16 累加几百上千行的贡献会明显丢精度；先累到 fp32，最后再转回去。
- **`dx` 用 `torch.empty_like`**：它是逐行独立写出的，不需要初值，也不需要累加。

---

## 四、内核：两类指针

### 4.1 二维数组跨 stride，一维向量加行号

反向内核里同时存在两种张量，指针算法完全不同：

```python
    ### 2d arrays
    row_x_ptr  = x_ptr  + row_idx * stride_x
    row_dX_ptr = dX_ptr + row_idx * stride_dx
    row_dY_ptr = dY_ptr + row_idx * stride_dy

    ### 1d Vectors
    row_mean_ptr    = mean_ptr    + row_idx
    row_inv_var_ptr = inv_var_ptr + row_idx
```

![两类指针：x / dx / dy 是二维数组，要乘 stride；mean / inv_var 是一维向量，只加行号](assets/用%20Triton%20手写%20LayerNorm（2）：反向传播与原子累加/02306.webp)

[【跳转到 36:01】](https://www.youtube.com/watch?v=DdDr6VXftig&t=2161)

作者用一张示意图强调这个区别：要定位二维矩阵的第 3 行，得往下跳 3 个 stride；而要定位一维向量的第 3 个元素，只需偏移 3 个元素。**混用这两种算法是这类内核的常见错误来源**——写成「`mean_ptr` 加行号乘 stride」就会读到越界位置。

### 4.2 统一 cast 到 fp32

```python
    cols = tl.arange(0, BLOCK_SIZE)
    mask = cols < n_cols

    if gamma_ptr is not None:
        gamma = tl.load(gamma_ptr + cols, mask=mask, other=0.).to(tl.float32)
    else:
        gamma = 1.0
```

![内核开头：列偏移、mask、加载 gamma 并统一转成 fp32；没有 gamma 时用 1.0 占位](assets/用%20Triton%20手写%20LayerNorm（2）：反向传播与原子累加/02100.webp)

[【跳转到 35:00】](https://www.youtube.com/watch?v=DdDr6VXftig&t=2100)

注意「`gamma` 不存在时直接取常数 1.0」这个写法——**用一个常数占位，而不是写一堆分支**。这样后面算 `wdy`（`gamma` 乘 `dy_row`）时不用判断 `gamma` 是否存在，代码只有一条路径。

所有加载都跟了 `.to(tl.float32)`。作者的理由是：反向里有除法、有均值、有平方，**中间运算如果留在 fp16，误差会累积得很快**；统一升到 fp32 算完，最后 `tl.store` 时再转回原 dtype。

---

## 五、重算 x̂ 而不是存它

```python
    x_hat = (x_row - row_mean) * row_inv_std
    wdy   = gamma * dy_row      # 穿过 gamma 之后的上游梯度
```

![用前向存下的 mean 与 inv_var 现场重算 x_hat，再乘 gamma 得到 wdy](assets/用%20Triton%20手写%20LayerNorm（2）：反向传播与原子累加/02412.webp)

[【跳转到 38:26】](https://www.youtube.com/watch?v=DdDr6VXftig&t=2306)

这里有个看似反常的决定：前向明明算过 $\hat{x}$（就是 `normed`），为什么不存下来？

作者的解释是**存储成本**：$\hat{x}$ 的形状和 $x$ 一样，是 $(N, E)$；而 `mean` 和 `inv_var` 只有 $(N,)$。存 $\hat{x}$ 要多占一整个输入规模的显存，而重算只需要一次减法和一次乘法——**用两个小向量换一个大张量，稳赚**。

这和第 1 篇里「存 `mean`/`inv_var`」并不矛盾，反而是一条统一的判据：

> 存「每行一个数」的，重算「每行一整行」的。

作者还补了一句反向的对照案例：FlashAttention 里连注意力概率都不存，宁可重算，因为那是 $N \times N$。

---

## 六、dx 的落地：mean1 与 mean2

公式里的 $\operatorname{mean}(\hat{g})$ 和 $\operatorname{mean}(\hat{g}\odot\hat{x})$，在代码里被拆成两个标量：

```python
    mean1 = tl.sum(x_hat * wdy, axis=0) / n_cols
    mean2 = tl.sum(wdy, axis=0) / n_cols
    dx = row_inv_std * (wdy - (x_hat * mean1 + mean2))
```

![dx 的落地：mean1 是 x_hat 与 wdy 的内积均值，mean2 是 wdy 的均值，最后按公式组合](assets/用%20Triton%20手写%20LayerNorm（2）：反向传播与原子累加/02641.webp)

[【跳转到 41:06】](https://www.youtube.com/watch?v=DdDr6VXftig&t=2466)

对照公式逐项看：

| 公式里的项 | 代码里的名字 | 含义 |
| --- | --- | --- |
| $\hat{g}$ | `wdy` | 穿过 gamma 的上游梯度 |
| $\operatorname{mean}(\hat{g}\odot\hat{x})$ | `mean1` | 梯度与归一化输入的「相关度」 |
| $\operatorname{mean}(\hat{g})$ | `mean2` | 梯度的均值 |
| $\frac{1}{\sqrt{\sigma^2+\epsilon}}$ | `row_inv_std` | 前向存下的 `inv_var` |

作者在写 `dx` 时还做了一次代数整理：公式里是「减一个均值、再减另一个」，他写成「`wdy` 减 `x_hat` 乘 `mean1`、再减 `mean2`」的形式，并说明「这和减两次是一样的，结果没变，只是写法不同」。

写回时注意 `dx` 要转回原来的 dtype：

```python
    tl.store(row_dX_ptr + cols, dx.to(pointer_type), mask=mask)
```

[【跳转到 42:34】](https://www.youtube.com/watch?v=DdDr6VXftig&t=2554)

---

## 七、dgamma / dbeta：atomic_add 的两行

```python
    if dGamma_ptr is not None:
        dw = dy_row * x_hat
        tl.atomic_add(dGamma_ptr + cols, dw, mask=mask)

    if dB_ptr is not None:
        tl.atomic_add(dB_ptr + cols, dy_row, mask=mask)
```

[【跳转到 43:43】](https://www.youtube.com/watch?v=DdDr6VXftig&t=2623)

这两行就是第 2 节讨论的落地：

- `dw`（即 `dy_row` 乘 `x_hat`）对应 $\partial L/\partial\gamma = \sum g_i\hat{x}_i$ 的**单项**；
- `dbeta` 的单项就是 `dy_row` 本身，对应 $\sum g_i$；
- 求和由 `tl.atomic_add` 完成——每个 PID 把自己的那一行贡献原子地加到「`dGamma_ptr` 加列偏移」指向的位置。

注意指针里带的是 `cols`（列偏移）而不是行号：**`dgamma` 的长度是 $E$，每一行贡献的都是同一个长度为 $E$ 的向量**，所以所有行都在往同一片地址上累加。这正是必须用原子操作的原因。

作者在这里又强调了一次竞态：如果写成 `+=`，所有线程会同时读到那个初始的 0，各加各的，最后只剩一个值。`tl.atomic_add` 把这件事交给硬件排好队。

---

## 八、对拍：一个拼写错误与 1e-2 的容差

测试脚本的思路和 softmax 那篇一样：用 PyTorch 的 `layer_norm` 做参考，逐项比较前向输出、`dx`、`dgamma`、`dbeta`。

第一次运行直接报错：

![第一次运行：CompilationError，Triton 说 tl.load 收到了一个不认识的参数 maks](assets/用%20Triton%20手写%20LayerNorm（2）：反向传播与原子累加/02699.webp)

[【跳转到 44:54】](https://www.youtube.com/watch?v=DdDr6VXftig&t=2694)

原因是手滑：`mask=mask` 被打成了 `maks=mask`。作者在文件里搜 `maks` 找到那一处，改回来。

![在编辑器里搜索 maks，定位到拼错的那一行](assets/用%20Triton%20手写%20LayerNorm（2）：反向传播与原子累加/02724.webp)

[【跳转到 45:24】](https://www.youtube.com/watch?v=DdDr6VXftig&t=2724)

改完再跑，四项全部通过：

- `forward`：通过
- `dx`：通过
- `dgamma`：通过
- `dbeta`：通过

容差用的是 `rtol=1e-2, atol=1e-2`——比 PyTorch 默认的 `1e-5` 宽得多。作者对此的解释很坦诚：

- 输入是 **fp16**，本身就只保留约三位十进制有效数字；
- 中间虽然升到 fp32 运算，但 Triton 对某些运算的实现方式（他提到「像 TensorFlow 处理 fp32 那样」）会引入细微差异；
- 所以「有极小的精度偏差是正常的」，只要在 1e-2 内就算通过。

**这一点对「数值一致」这件事很重要**：一致性不是「逐位相同」，而是「在给定 dtype 与容差下等价」。fp16 的算子用 `1e-5` 去卡，只会得到永远失败的测试。

---

## 小结

- **反向要算三样**：$dx$（逐行独立）、$d\gamma$、$d\beta$（跨 N 行求和）。
- **那个 Σ 来自前向的广播**：同一个 `gamma` 被 N 行共用，所以 N 份梯度必须还给同一个位置。
- **PID 之间不能求和**，只能靠「预分配全零累加器 + `tl.atomic_add`」把时间上的归约变成空间上的累加。
- **原子操作是排队**：它保证正确性，代价是串行化；好在 LayerNorm 的累加量只有一个长度 $E$ 的向量。
- **累加器用 fp32**：`dgamma`/`dbeta` 强制 fp32，算完再转回原 dtype，避免 fp16 累加丢精度。
- **两类指针不能混**：二维数组要乘 stride，一维向量只加行号。
- **$\hat{x}$ 重算不存**：用两个 `(N,)` 的小向量换掉一个 `(N, E)` 的大张量。
- **用常数 1.0 占位**：`gamma` 不存在时直接取 1.0，用常数代替分支，让内核只有一条执行路径。
- **容差要匹配 dtype**：fp16 的算子用 `1e-2` 是合理的，用 `1e-5` 只会永远失败。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| 上游梯度 | 从下一层传回来的 $\partial L/\partial y$，代码里叫 `dy` |
| 广播累加 | 前向广播出去的参数，反向要把 N 行的梯度加回同一位置 |
| 竞态（race condition） | 多个线程同时读-改-写同一地址，结果取决于调度顺序 |
| `tl.atomic_add` | 原子加法，保证同一地址上的读-改-写不可分割 |
| 累加器 | 预先分配的全零缓冲，用来收集各 PID 的贡献 |
| `inv_var` | 逆标准差 $1/\sqrt{\sigma^2+\epsilon}$，反向直接复用 |
| `x_hat` | 归一化后的输入 $\hat{x}$，反向用 `mean` 与 `inv_var` 现场重算 |
| `wdy` | 穿过 gamma 的上游梯度 $\hat{g} = g\cdot\gamma$ |
| `rtol` / `atol` | 相对/绝对容差，判断两个张量「数值一致」的阈值 |
| 重算 vs 存储 | 每行一个数的中间量存下来，每行一整行的中间量现场重算 |