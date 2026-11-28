# Gate 与 Up 合成一次矩阵乘：在 Triton 里手写融合 SwiGLU

> 视频来源：[Implementing Fused SwiGLU FFN From Scratch in Triton](https://www.youtube.com/watch?v=zklv6OpoqWE)（YouTube · Bielik Anatomy / Kuba）｜时长约 8 分钟
> 导读：一支把「融合省了几次显存传输」数到个位数的实操课：先讲清 SwiGLU 的两条投影与门控，再逐笔数出朴素实现的 7 次 HBM 传输，然后一行行写出融合 kernel，最后给出 RTX 4060 上的实测曲线。适合已经知道矩阵乘怎么分块、想看清「融合到底把哪几笔账砍掉」的读者。

## 本讲要解决的核心问题（SCQA）

**背景**：现代大模型的 FFN（前馈网络）普遍用 SwiGLU：从同一份输入 `x` 出发，一条 gate 投影、一条 up 投影，gate 过 SiLU 当门，与 up 逐元素相乘，最后过 down 投影压回隐藏维度。

**冲突**：在 PyTorch 里照着公式写，会自然写成三个操作——算 gate、算 up、再做 SwiGLU。三个操作就是三个 kernel，而每个 kernel 都要把张量从显存（HBM）搬进搬出。SwiGLU 的算术量小得可怜，可它要搬的数据一点也不少。

**疑问**：这三个 kernel 到底搬了几次？融合成一个 kernel 之后又搬几次？省下来的部分凭什么能变成速度？

**回答（中心思想）**：朴素实现要 **7 次 HBM 传输**（其中 5 次是纯粹为了在 kernel 之间「传话」的浪费），融合实现只要 **2 次**——读一次 `x`、写一次输出，gate 与 up 两份中间结果全程留在寄存器里。**SwiGLU 本身很便宜，瓶颈是显存带宽而不是算术；加速全部来自去掉那些中间结果的 HBM 往返。**

## 一、先看清 SwiGLU 在算什么

### 1.1 两条并行投影，一个门

视频先画出 swish 门控线性单元（SwiGLU，Swish-Gated Linear Unit）的结构：从输入 `x` 出发有两条并行的投影，一条叫 **gate 投影**（权重 $W_{gate}$），另一条叫 **up 投影**（权重 $W_{up}$），两条吃的是同一份输入 `x`。gate 的输出先过 SiLU 激活，然后与 up 的输出**逐元素相乘**——这就是门控的部分。最后还有 **down 投影**（$W_{down}$），把结果压回隐藏维度。[【跳转到 00:25】](https://www.youtube.com/watch?v=zklv6OpoqWE&t=25)

写成公式：

$$
\mathrm{SwiGLU}(x) = \Big(\mathrm{SiLU}(xW_{gate}) \odot xW_{up}\Big) W_{down}
$$

其中 $\odot$ 是逐元素相乘，$\mathrm{SiLU}(z) = z \cdot \sigma(z)$，$\sigma$ 是 sigmoid。

![SwiGLU 结构：输入 x 分成 gate 与 up 两条投影，gate 过 SiLU 后与 up 逐元素相乘，再过 down 投影](assets/Gate%20与%20Up%20合成一次矩阵乘：在%20Triton%20里手写融合%20SwiGLU/00030.webp)

### 1.2 门控到底在做什么

视频给了一张很直观的表：SiLU 的输出相当于一个 **0 到 1 之间的掩码**，乘在 up 投影的数据上。

- 掩码 ≈ 1.0：这一维数据原样通过（Pass）；
- 掩码 ≈ 0.4：这一维被压暗（Dim）；
- 掩码 ≈ 0.0：这一维被丢掉（Drop）。

所以门控是一个**学出来的、依赖输入的过滤器**：对某个 token 来说，只有中间表示里有用的那些维度能活到 down 投影。这也是为什么模型要用它——它按输入抑制无关特征。[【跳转到 00:55】](https://www.youtube.com/watch?v=zklv6OpoqWE&t=55)

![SiLU 输出充当掩码：1.0 通过、0.4 压暗、0.0 丢弃；公式为 SwiGLU(x) = (SiLU(xW_gate) ⊙ xW_up)W_down](assets/Gate%20与%20Up%20合成一次矩阵乘：在%20Triton%20里手写融合%20SwiGLU/00080.webp)

## 二、朴素实现的账：3 个 kernel、7 次显存传输

视频把朴素做法放在硬件层面逐笔数：

1. **第一个 kernel**：从 HBM 读 `x`（1 次读），乘上 $W_{gate}$，把 gate 结果写回 HBM（1 次写）。
2. **第二个 kernel**：又从 HBM 读 `x`（同一份数据，第 2 次读），算出 up 投影，再写回 HBM（1 次写）。
3. **第三个 kernel**：从 HBM 读回 gate 和 up 两份中间结果（2 次读），做 SiLU 与逐元素相乘，写出最终输出（1 次写）。

合计 **4 次读 + 3 次写 = 7 次显存传输**。[【跳转到 01:45】](https://www.youtube.com/watch?v=zklv6OpoqWE&t=105)

![朴素做法：gate 与 up 两份中间结果都落在 HBM，第三个 kernel 再把它们读回来](assets/Gate%20与%20Up%20合成一次矩阵乘：在%20Triton%20里手写融合%20SwiGLU/00130.webp)

这里面有几笔是「必须」的？

- 读 `x` 一次是必须的；读权重（$W_{gate}$、$W_{up}$）是必须的；写最终输出一次是必须的。
- **读 `x` 的第二遍、写 gate、写 up、读回 gate、读回 up——这 5 次纯粹是为了在 kernel 之间传话。** 视频的原话是：你为了在 kernel 之间通信，白付了 5 次往返主存的代价。

## 三、融合实现的账：1 个 kernel、2 次传输

融合做法是**一个 kernel 干完所有事**：从 HBM 读一次 `x`，在寄存器里同时算出两条投影、在寄存器里做完 SwiGLU，然后写出最终结果。**总共 2 次显存传输——读 `x`、写输出**，中间的一切都留在片上快速存储里。[【跳转到 02:10】](https://www.youtube.com/watch?v=zklv6OpoqWE&t=130)

把两套账并排：

| 项目 | 朴素实现 | 融合实现 |
| --- | --- | --- |
| kernel 发射次数 | 3 | 1 |
| HBM 读 | 4 次（`x` 两遍 + gate、up 各一遍） | 1 次（`x`） |
| HBM 写 | 3 次（gate、up、最终输出各一次） | 1 次（最终输出） |
| 合计传输 | 7 次 | 2 次 |
| 中间张量 gate / up | 落在 HBM | 只存在于寄存器 |

视频在这里给出全篇最重要的一句判断：**SwiGLU 本身很便宜，瓶颈是显存带宽而不是算术；去掉那些中间结果的 HBM 往返，加速就从这里来。**[【跳转到 02:35】](https://www.youtube.com/watch?v=zklv6OpoqWE&t=155)

这句话解释了为什么融合对这类算子是「必需品」而不是「优化项」：算力早就过剩了，卡住的是搬运。

## 四、把账本落到代码

### 4.1 函数签名与 tile 常量

kernel 的输入是三组指针（`X`、`W_gate`、`W_up`）加一个输出指针，再加矩阵形状 `M`、`N`、`K`、三个步长，以及五个编译期常量：`BLOCK_M`、`BLOCK_N`、`BLOCK_K`（tile 尺寸）和 `GROUP_M`（用于 swizzling 的分组大小）。[【跳转到 03:05】](https://www.youtube.com/watch?v=zklv6OpoqWE&t=185)

![融合 SwiGLU kernel 全貌：三组输入指针、两个 FP32 累加器、循环里一次加载两次 tl.dot、循环外做 SwiGLU 并只写出一次](assets/Gate%20与%20Up%20合成一次矩阵乘：在%20Triton%20里手写融合%20SwiGLU/00185.webp)

### 4.2 为什么需要 swizzling（GROUP_M）

正常情况下 Triton 一行一行地处理输出块。问题在于：每移到下一个块，就要从慢速的 HBM 里取一整列新的权重，缓存命中率为零，性能很糟。

swizzling 改变了行进路线：不再走直线，而是**按组处理块**。为什么按组有用？因为同一组里的所有 program 需要的正好是同一列权重——第一个 program 从 HBM 把它加载进来，其他的就能瞬间从快速的 **L2 缓存**里拿到。[【跳转到 03:43】](https://www.youtube.com/watch?v=zklv6OpoqWE&t=223)

注意这是**另一笔账**：swizzling 省的是「权重被重复从 HBM 读」，属于分块策略的范畴；而融合省的是「中间结果被写回再读回」。两者常常一起用，但不要混为一谈。

### 4.3 循环体：一次加载，两次矩阵乘

建好三个指针数组（`x_ptrs`、`wg_ptrs`、`wu_ptrs`）之后，两个 FP32 累加器 `acc_gate`、`acc_up` 在整个循环期间都留在寄存器里。每次迭代只加载一块 `x`，并在两次 `tl.dot` 调用里复用它：

```python
acc_gate = tl.zeros((BLOCK_M, BLOCK_N), dtype=tl.float32)
acc_up   = tl.zeros((BLOCK_M, BLOCK_N), dtype=tl.float32)

for k in range(0, tl.cdiv(K, BLOCK_K)):
    x  = tl.load(x_ptrs,  ...)
    wg = tl.load(wg_ptrs, ...)
    wu = tl.load(wu_ptrs, ...)

    acc_gate = tl.dot(x, wg, acc=acc_gate)   # 同一块 x
    acc_up   = tl.dot(x, wu, acc=acc_up)     # 复用同一块 x

    x_ptrs  += BLOCK_K * stride_xk
    wg_ptrs += BLOCK_K * stride_wk
    wu_ptrs += BLOCK_K * stride_wk
```

**一次加载、两次矩阵乘——这就是融合的部分。** 在朴素实现里，这两次矩阵乘分属两个 kernel，`x` 要被从 HBM 读两遍；这里 `x` 只从 HBM 读一遍，第二遍用的是寄存器里那一份。[【跳转到 04:27】](https://www.youtube.com/watch?v=zklv6OpoqWE&t=267)

![循环里一次加载 x、两次 tl.dot：acc_gate 与 acc_up 全程留在寄存器](assets/Gate%20与%20Up%20合成一次矩阵乘：在%20Triton%20里手写融合%20SwiGLU/00267.webp)

### 4.4 循环之后：在寄存器里做 SwiGLU，只写一次

循环结束后，两个累加器里存着这个输出块完整的矩阵乘结果，**还在寄存器里**，于是就在原地做 SwiGLU：

```python
out = acc_gate * tl.sigmoid(acc_gate) * acc_up
out_ptrs = Out_ptr + offs_m[:, None] * stride_om + offs_n[None, :] * stride_on
tl.store(out_ptrs, out.to(Out_ptr.dtype.element_ty), mask=...)
```

把 gate 乘上它自己的 sigmoid（也就是逐元素做一次 SiLU），再乘上 `acc_up`——全程在寄存器里，没有任何访存。然后 `tl.store` 把结果转回输出精度、写进 HBM，**这是整个 kernel 里唯一的一次写出**。[【跳转到 05:17】](https://www.youtube.com/watch?v=zklv6OpoqWE&t=317)

![循环外：out = acc_gate * sigmoid(acc_gate) * acc_up 在寄存器里完成，随后只有一次 tl.store](assets/Gate%20与%20Up%20合成一次矩阵乘：在%20Triton%20里手写融合%20SwiGLU/00342.webp)

这也解释了为什么融合版能省掉那两个中间张量：gate 和 up 从来没有以「张量」的形式存在过，它们只以寄存器里两个累加器的形式存在。

## 五、实测：省下来的传输变成了多少 TFLOPS

测试环境是作者的 RTX 4060，用 Bielik 模型的配置：隐藏维度 1536、中间维度 8960。三个对手：Triton 融合 kernel、`torch.compile` 编译后的 PyTorch、未融合的原生 PyTorch。[【跳转到 05:42】](https://www.youtube.com/watch?v=zklv6OpoqWE&t=342)

### 5.1 随序列长度变化

在很短的序列长度上三者很接近；随着规模上去，Triton 拉开了差距，跑到约 **45 TFLOPS**，编译后的 PyTorch 停在约 **40**，未融合的落在约 **37**。视频还提醒注意未融合 PyTorch 在图右侧的表现：它不是走平，而是**缓慢下降**——中间张量越大，搬运的代价越明显。[【跳转到 06:04】](https://www.youtube.com/watch?v=zklv6OpoqWE&t=364)

![SwiGLU FFN 的 TFLOPS 随序列长度变化：Triton 融合约 45，编译版约 40，未融合约 37 且缓慢下滑](assets/Gate%20与%20Up%20合成一次矩阵乘：在%20Triton%20里手写融合%20SwiGLU/00364.webp)

### 5.2 随中间维度变化

第二张图把中间维度从 1024 扫到约 14000。有意思的是**差距在中间维度较小时最大**：在 1024 时 Triton 领先 30%；随着矩阵变宽，大家都爬上去，领先幅度稳定在 15% 左右。[【跳转到 06:29】](https://www.youtube.com/watch?v=zklv6OpoqWE&t=389)

怎么理解这个形状？中间维度小的时候，矩阵乘的算术量小，整条链更接近「访存受限」，于是省掉 5 次传输的收益占比最大；矩阵变宽后算术量上来了，计算开始占一部分时间，融合的相对收益就被摊薄——但仍然稳定为正。

## 六、这套账本可以照抄到别处

视频最后说，现在零件齐了：RoPE、RMSNorm、FlashAttention、SwiGLU，下一集要拼一个完整的解码层。而它演示的这套记账方法，正是本小节四种融合模式的通用模板：

- **Gate + Up 投影合并**（本文）：两次投影共享输入 `x`，合成一次矩阵乘，省掉一次读 `x` 与两份中间结果的写回/读回。
- **QKV 投影合并**：同理，三次投影共享同一份隐藏状态，把三个权重矩阵堆成一个，一次乘出 Q、K、V。
- **Add + RMSNorm**：残差加法与归一化共享同一份数据，合成一个 kernel，省掉残差和这个整张量中间结果。
- **RoPE + Attention**：若 RoPE 是独立一步，Q、K 必须写回 HBM 再被 attention 读回；把 RoPE 折进 attention 的加载路径，就省掉这一次写回与一次读回。

判断一个融合值不值得做，只要问三个问题：**融合前它写了几次显存、读了几次显存、发射了几次 kernel？融合后各是几次？** 如果省下来的传输量相对算术量足够大（也就是这个算子本来就是访存受限的），融合就一定划算。

## 小结

- SwiGLU 的结构是「两条并行投影 + 一个门」：gate 过 SiLU 当掩码，与 up 逐元素相乘，再过 down 投影。
- 朴素实现是 3 个 kernel、**7 次 HBM 传输**，其中 5 次纯粹是为了在 kernel 之间传话。
- 融合实现是 1 个 kernel、**2 次传输**：读一次 `x`、写一次输出，gate 与 up 只存在于寄存器。
- 关键洞察：**SwiGLU 便宜，瓶颈是显存带宽**；加速来自去掉中间结果的 HBM 往返。
- 代码上的三个要点：两个 FP32 累加器常驻寄存器、循环里「一次加载两次 `tl.dot`」、循环外原地做 SiLU 与相乘后只 `store` 一次。
- swizzling（`GROUP_M`）省的是「权重被重复从 HBM 读」，与融合省的不是同一笔账。
- 实测：RTX 4060 上 45 vs 40 vs 37 TFLOPS；中间维度 1024 时领先 30%，矩阵变宽后稳定在 15%。
- 这套「数传输次数」的账本可以直接套到 QKV 合并、Add + RMSNorm、RoPE + Attention 上。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| SwiGLU | 用 SiLU 做门的门控线性单元，两条并行投影共享输入 |
| gate / up 投影 | 同一份输入乘两个不同权重矩阵，一个当门、一个当数据 |
| HBM | 显卡上的高带宽显存，容量大但访问慢，是这里的瓶颈所在 |
| SRAM / 寄存器 | 片上快速存储；融合的关键就是让中间结果留在这里 |
| 显存传输次数 | 一个 kernel 读、写 HBM 的次数之和，本文的核心度量 |
| `tl.dot` | Triton 里的矩阵乘指令，累加到给定的累加器上 |
| 累加器 | 存放矩阵乘部分和的寄存器数组，融合时它同时充当中间结果 |
| swizzling / `GROUP_M` | 改变块的处理顺序，让同一组 program 复用同一列权重（走 L2） |
| 中间张量 | 中间结果落成的显存张量；融合后它不再存在 |