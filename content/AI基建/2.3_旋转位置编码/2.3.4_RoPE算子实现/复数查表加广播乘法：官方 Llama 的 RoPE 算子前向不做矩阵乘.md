# 复数查表加广播乘法：官方 Llama 的 RoPE 算子前向不做矩阵乘

> 视频来源：[Llama源码讲解之RoPE旋转位置编码](https://www.bilibili.com/video/BV1Zr421c76A/?t=0)（Bilibili · deep_thoughts）
> 本文基于视频演说图文稿整理，配图截自视频。
> 导读：这支约 26 分钟的视频，前 9 分钟回顾位置编码的三条路线（绝对、相对、旋转），剩下时间逐行读官方 llama 仓库（视频里打开的是 `github/external/llama`）的 `model.py`，重点是三个函数：`precompute_freqs_cis`、`reshape_for_broadcast`、`apply_rotary_emb`。本文把原理回顾压成必要的几句，篇幅留给代码——每一行在算什么形状、为什么必须这么写。同一算子的另一种写法（预计算 cos/sin 表 + 前后半拆分的逐元素乘加）见本小节另一篇博客。

## 本讲要解决的核心问题（SCQA）

**背景**：Llama 2 与 Llama 3 用的是同一个位置编码方案 RoPE（Rotary Position Embedding，旋转位置编码）——它既不像原始 Transformer 那样给每个位置发一个独立的向量，也不像后来的一些相对位置编码那样直接改注意力矩阵，而是**按位置把向量整体转一个角度** [【跳转到 00:20】](https://www.bilibili.com/video/BV1Zr421c76A/?t=20)。旋转矩阵、$m\theta_i$ 这些数学形式，本系列 2.3.2 那篇已经推过。

**冲突**：公式里只写了"一个二维旋转"，落到张量上却完全不是二维的。Q 是 $[B,\ T,\ H,\ d]$ 四维张量（batch、序列长度、head 数、每头维度），每个 batch、每个头、每个位置、每一对维度，要转的角度都不一样。初学者最直觉的写法是打循环，或者给每个位置造一个 $d\times d$ 的大旋转矩阵去乘——前者在 GPU 上慢得没有意义，后者要存 $T$ 个稠密矩阵，绝大部分元素还是 0。

**疑问**：官方实现凭什么把"每个位置 × 每对维度都转不同角度"压进几十行代码，而且全程没有一次矩阵乘？

**回答（中心思想）**：**官方实现把"角度"和"向量"彻底拆开：位置信息全部预计算成一张 $[T,\ d/2]$ 的复数表 `freqs_cis`，前向时只做三件事——把相邻两维打包成一个复数、把表按位置和 head 广播过去、两个复数相乘（乘数的模恒为 1，所以只改角度不改长度），再转回实数。** 一次乘法对应一次旋转，广播负责把一张表铺到所有 batch 与 head 上，这就是它不需要矩阵乘也不需要循环的原因。

---

## 一、RoPE 只挂在 attention 的两个入参上

![Attention.forward 里 Q、K 先 view 成四维，再交给 apply_rotary_emb 注入位置信息](assets/复数查表加广播乘法：官方%20Llama%20的%20RoPE%20算子前向不做矩阵乘/00604.webp)

`model.py` 里的 `Attention.forward` 是整段故事的上下文 [【跳转到 10:04】](https://www.bilibili.com/video/BV1Zr421c76A/?t=604)：

```python
bsz, seqlen, _ = x.shape
xq, xk, xv = self.wq(x), self.wk(x), self.wv(x)

xq = xq.view(bsz, seqlen, self.n_local_heads, self.head_dim)
xk = xk.view(bsz, seqlen, self.n_local_kv_heads, self.head_dim)
xv = xv.view(bsz, seqlen, self.n_local_kv_heads, self.head_dim)

xq, xk = apply_rotary_emb(xq, xk, freqs_cis=freqs_cis)
```

三点值得记：

1. **先切头，再旋转**。线性层输出的最后一维是 `dim`，`view` 之后才拆成 `n_local_heads` 与 `head_dim` 两个维度。原因是 RoPE 的旋转是按 head 内部的维度做的，两个 head 之间互不相干 [【跳转到 10:24】](https://www.bilibili.com/video/BV1Zr421c76A/?t=624)。
2. **只旋转 q 和 k，v 不参与**。因为位置信息要进入的是 $q\cdot k^{\top}$ 这个内积，value 后面直接加权求和，转它没有意义 [【跳转到 10:44】](https://www.bilibili.com/video/BV1Zr421c76A/?t=644)。
3. **`freqs_cis` 是外部传进来的**，不在 `Attention` 里现算。函数签名里能看到它是必选参数；而 `apply_rotary_emb` 也只需要三个参数：q、k、频率表 [【跳转到 11:24】](https://www.bilibili.com/video/BV1Zr421c76A/?t=684)。

返回的 `xq, xk` 形状与传入时完全一样，只是每个位置、每对维度上多了一份"转过的角度"[【跳转到 11:04】](https://www.bilibili.com/video/BV1Zr421c76A/?t=664)。这一点很重要：**RoPE 是一个形状不变算子**，所以它能插进 attention 的计算链路而不惊动别处。

---

## 二、`precompute_freqs_cis`：整张角度表一次算完

![precompute_freqs_cis 的三个核心行：频率、位置外积、转成复指数](assets/复数查表加广播乘法：官方%20Llama%20的%20RoPE%20算子前向不做矩阵乘/00704.webp)

这个函数的名字直译是"预计算频率的复指数表"。复数里的"cis"就是 $\cos\theta + i\sin\theta$，也就是 $e^{i\theta}$ 的另一种写法——视频里把它称作**复指数（complex exponential）** [【跳转到 11:44】](https://www.bilibili.com/video/BV1Zr421c76A/?t=704)。

```python
def precompute_freqs_cis(dim: int, end: int, theta: float = 10000.0):
    freqs = 1.0 / (theta ** (torch.arange(0, dim, 2)[: (dim // 2)].float() / dim))
    t = torch.arange(end, device=freqs.device)
    freqs = torch.outer(t, freqs).float()
    freqs_cis = torch.polar(torch.ones_like(freqs), freqs)
    return freqs_cis
```

四行代码，对应四个物理量，逐个拆开看。

### 2.1 第一行：第 $i$ 组的角速度 $\theta_i$

旋转角度是 $m\theta_i$，$m$ 是位置，$\theta_i$ 是第 $i$ 组的**角速度**——同一个位置 $m$，第 0 组转得多、越靠后的组转得越少。视频先给论文里的写法：

$$
\theta_i = 10000^{-\frac{2i-1}{d}}
$$

再指到代码里，`torch.arange(0, dim, 2)` 取的是 $0, 2, 4, \dots$ 这些**偶数维**的下标，除以 `dim` 之后作为指数 [【跳转到 12:44】](https://www.bilibili.com/video/BV1Zr421c76A/?t=764)，于是代码这一行等价于

$$
\theta_i = \frac{1}{\text{theta}^{\,\frac{2i}{d}}}, \qquad i = 0, 1, \dots, \frac{d}{2}-1
$$

两种写法都给出 $\frac{d}{2}$ 个数，都随 $i$ 单调递减——也就是 2.3.3 那篇讲过的"频率阶梯"：靠前的维度转得快（高频，对小位移敏感），靠后的维度转得慢（低频，负责长距离）[【跳转到 13:04】](https://www.bilibili.com/video/BV1Zr421c76A/?t=784)。

### 2.2 第二行：位置 $m$

`t = torch.arange(end)` 就是从 0 到 `end - 1` 的位置索引 [【跳转到 12:24】](https://www.bilibili.com/video/BV1Zr421c76A/?t=744)。**这里藏着一个很关键的设计**：位置不是算出来的，而是"数出来的"——0、1、2……直到预设的最大长度。所以 RoPE 天然知道每个 token 的绝对位置，$m$ 越大转得越多 [【跳转到 08:40】](https://www.bilibili.com/video/BV1Zr421c76A/?t=520)；同时两个位置的夹角差只取决于 $m-n$，这才有"相对位置"的味道。绝对位置与相对关系在同一个角度里，是 RoPE 相比前两代位置编码的核心优势。

### 2.3 第三行：外积一次性排好整张表

`torch.outer(t, freqs)` 把长度为 $T$ 的位置向量和长度为 $\frac{d}{2}$ 的角速度向量做外积，得到一个 $T \times \frac{d}{2}$ 的矩阵 [【跳转到 13:24】](https://www.bilibili.com/video/BV1Zr421c76A/?t=804)。矩阵的第 $m$ 行、第 $i$ 列就是 $m\theta_i$。也就是说，**这张表就是"所有位置 × 所有维度对"的角度清单**，一次算完，后面反复取用。

### 2.4 第四行：`torch.polar` 把角度变成复数

`torch.polar(幅度, 角度)` 按极坐标构造复数：幅度是到原点的距离，角度是辐角 [【跳转到 14:44】](https://www.bilibili.com/video/BV1Zr421c76A/?t=884)。这里幅度传的是一个全 1 张量（`torch.ones_like`，形状与角度完全一样），因为旋转矩阵不改变向量长度，模必须恒为 1。于是

$$
\text{freqs\_cis}[m, i] = 1 \cdot e^{\,i\,m\theta_i} = \cos(m\theta_i) + i\,\sin(m\theta_i)
$$

到这里，一张复数表就代表了"所有位置、所有维度对"的旋转矩阵。视频特别强调了这个表的数据类型是 `complex64`（代码里 `# complex64` 的注释）[【跳转到 15:24】](https://www.bilibili.com/video/BV1Zr421c76A/?t=924)。

---

## 三、为什么非要用复数：模为 1 的乘法只转角度

复数在这里不是炫技，而是把"旋转矩阵乘向量"这件事化简成**一次标量乘法**。

二维情况下，旋转 $\alpha$ 角度是

$$
\begin{pmatrix} x' \\ y' \end{pmatrix}
=
\begin{pmatrix} \cos\alpha & -\sin\alpha \\ \sin\alpha & \cos\alpha \end{pmatrix}
\begin{pmatrix} x \\ y \end{pmatrix}
=
\begin{pmatrix} x\cos\alpha - y\sin\alpha \\ x\sin\alpha + y\cos\alpha \end{pmatrix}
$$

如果先把 $(x, y)$ 打包成复数 $z = x + iy$，把旋转写成 $e^{i\alpha} = \cos\alpha + i\sin\alpha$，那么

$$
z' = z \cdot e^{i\alpha}
= (x\cos\alpha - y\sin\alpha) + i\,(x\sin\alpha + y\cos\alpha)
$$

实部虚部一摊开，和上面的矩阵乘法一模一样。区别只在计算量：矩阵写法要做 4 次乘法 2 次加法、还得存一个 2×2 矩阵；复数写法只要一次复数乘。而乘数的模是 1，所以 $|z'| = |z|$——**长度不变，只有角度被加上去**，这正是视频反复强调的那句"幅度不变、角度变换"[【跳转到 22:44】](https://www.bilibili.com/video/BV1Zr421c76A/?t=1364)。

还有一层巧合让这个写法特别顺：$d$ 维向量按相邻两维分组，$(x_0, x_1)$、$(x_2, x_3)$、…… 每一组正好是一个复数的实部和虚部。所以"把相邻两维配成一对"和"把相邻两个实数读成一个复数"是同一个动作，代码里不需要任何额外搬运。

---

## 四、`apply_rotary_emb`：五次 reshape 完成一次旋转

![apply_rotary_emb 全貌：打包复数、重排频率表、相乘、转回实数](assets/复数查表加广播乘法：官方%20Llama%20的%20RoPE%20算子前向不做矩阵乘/01104.webp)

整个函数只有五行有效代码：

```python
xq_ = torch.view_as_complex(xq.float().reshape(*xq.shape[:-1], -1, 2))
xk_ = torch.view_as_complex(xk.float().reshape(*xk.shape[:-1], -1, 2))
freqs_cis = reshape_for_broadcast(freqs_cis, xq_)
xq_out = torch.view_as_real(xq_ * freqs_cis).flatten(3)
xk_out = torch.view_as_real(xk_ * freqs_cis).flatten(3)
return xq_out.type_as(xq), xk_out.type_as(xk)
```

### 4.1 先 `.float()`：一次保险

`xq.float()` 把张量转成 32 位浮点，不影响形状 [【跳转到 17:04】](https://www.bilibili.com/video/BV1Zr421c76A/?t=1024)。为什么要这一步：`view_as_complex` 对输入的 dtype 有要求，混合精度训练或半精度推理时直接传进来会报错，先统一成 float 最省事。

### 4.2 `reshape(*xq.shape[:-1], -1, 2)`：把最后一维拆成"对"和"2"

这是全篇最需要读懂的语法 [【跳转到 17:24】](https://www.bilibili.com/video/BV1Zr421c76A/?t=1044)：

- `xq.shape[:-1]` 取"从第一维到倒数第二维"，也就是 `[batch, seqlen, heads]` 这三个数；
- 前面的星号是**解包**：`[2, 4, 6]` 加上星号就变成 `2, 4, 6`，方括号没了、展开成三个独立参数 [【跳转到 17:44】](https://www.bilibili.com/video/BV1Zr421c76A/?t=1064)；
- 后面再补两个数 `-1, 2`，其中 `2` 是硬指定（每两个实数一组），`-1` 让 PyTorch 自己算"一共有多少组"，结果就是 $\frac{d}{2}$。

所以形状从四维 `[B, T, H, d]` 变成五维 `[B, T, H, d/2, 2]`——新增的第五维固定是 2 [【跳转到 18:04】](https://www.bilibili.com/video/BV1Zr421c76A/?t=1084)。

### 4.3 `view_as_complex`：把最后一维的两个实数读成一个复数

`view_as_complex` 顾名思义是"当作复数来看"：它要求张量的最后一维长度恰好是 2，然后**把这两个实数当作实部与虚部**，拼成一个复数，那一维随之消失 [【跳转到 18:24】](https://www.bilibili.com/video/BV1Zr421c76A/?t=1104)。于是 `xq_` 的形状是

$$
[B,\ T,\ H,\ d/2]
$$

维度少了一个，因为两个数合成了一个数 [【跳转到 18:44】](https://www.bilibili.com/video/BV1Zr421c76A/?t=1124)。注意它是"看"而不是"拷"：底层还是同一块内存，只是换了个解释方式。这也是为什么前一步必须自己 `reshape` 好——`view_as_complex` 不会帮你拆维度。

### 4.4 `reshape_for_broadcast`：把 $[T, d/2]$ 的表铺成 $[1, T, 1, d/2]$

![reshape_for_broadcast 的实现：只保留序列长度与 head_dim/2 两维，其余置 1](assets/复数查表加广播乘法：官方%20Llama%20的%20RoPE%20算子前向不做矩阵乘/01264.webp)

```python
ndim = x.ndim
assert 0 <= 1 < ndim
assert freqs_cis.shape == (x.shape[1], x.shape[-1])
shape = [d if i == 1 or i == ndim - 1 else 1 for i, d in enumerate(x.shape)]
return freqs_cis.view(*shape)
```

这段不长，但每行都有讲究 [【跳转到 20:04】](https://www.bilibili.com/video/BV1Zr421c76A/?t=1204)：

1. **两条断言是防呆**。断言要求 `freqs_cis` 的形状恰好等于「`x` 的序列长度维 × `x` 的最后一维」这个二元组，也就是第一维等于序列长度、第二维等于 $\frac{d}{2}$：位置数对不上就是取错了区间，维度对不上就是 head_dim 记错了，两种情况都直接报错比算出静默错误强 [【跳转到 20:24】](https://www.bilibili.com/video/BV1Zr421c76A/?t=1224)。
2. **只保留两维，其余压成 1**。遍历 `x.shape`，下标是 1（序列长度）或最后一维（$\frac{d}{2}$）就原样保留，其他维度一律写 1。于是形状变成 $[1, T, 1, \frac{d}{2}]$ [【跳转到 21:24】](https://www.bilibili.com/video/BV1Zr421c76A/?t=1284)。
3. **第一维是 1，不是 batch**。视频里讲到这里时口误说成 batch，随即自己纠正：batch 维也置 1 [【跳转到 22:04】](https://www.bilibili.com/video/BV1Zr421c76A/?t=1324)。这个 1 就是广播的关键：只有 1 才能被"免费"复制到 $B$ 份。

### 4.5 相乘：两个复数一乘，角度就加上了

![freqs_cis 广播后的形状注释：1、T、1、head_dim 的一半](assets/复数查表加广播乘法：官方%20Llama%20的%20RoPE%20算子前向不做矩阵乘/01344.webp)

`xq_` 与 `freqs_cis` 做的是逐元素复数乘，`freqs_cis` 靠广播自动展开成 $[B,\ T,\ H,\ d/2]$。乘完之后，第 $m$ 个位置、第 $i$ 对维度的复数，辐角被加上了 $m\theta_i$ [【跳转到 23:04】](https://www.bilibili.com/video/BV1Zr421c76A/?t=1384)。

这里把"谁在变"讲清楚：

- $m$ 随 token 位置变——同一个头，第 5 个词和第 500 个词转的角度不同；
- $\theta_i$ 随复数是第几维变——同一个位置，前几对维度转得多、后几对转得少 [【跳转到 23:24】](https://www.bilibili.com/video/BV1Zr421c76A/?t=1404)。

而模是 1，所以这只是"角度相加"，总模长不变 [【跳转到 23:44】](https://www.bilibili.com/video/BV1Zr421c76A/?t=1424)。

### 4.6 `view_as_real` + `flatten(3)`：原路返回

![view_as_real 之后还要把多出来的那一维拉平，形状才能回到最初的样子](assets/复数查表加广播乘法：官方%20Llama%20的%20RoPE%20算子前向不做矩阵乘/01444.webp)

`view_as_real` 是 `view_as_complex` 的逆操作：把复数的实部与虚部取出来，在最后补一维长度 2，形状回到 `[B, T, H, d/2, 2]` [【跳转到 24:04】](https://www.bilibili.com/video/BV1Zr421c76A/?t=1444)。但注意，它**并没有把 `d/2` 和 `2` 两维合并**——所以还要 `flatten(3)`，从第 3 维（0 起算，即 `d/2` 那一维）开始往后拉平，得到 `[B, T, H, d]`，与最初一模一样。

最后 `type_as` 把 dtype 转回输入的类型：进来是半精度就还半精度，不让 RoPE 悄悄改变下游的数值格式。

`xk` 走完全相同的流程，只是角度表共用——同一张 `freqs_cis` 同时服务 q 和 k，这也是 RoPE 的性质：**q 与 k 转同样的角度，内积里才只剩角度差** [【跳转到 24:24】](https://www.bilibili.com/video/BV1Zr421c76A/?t=1464)。

---

## 五、表在什么时候建、在什么时候取

![Transformer 的 `__init__` 里调用 precompute_freqs_cis，注释解释了为什么乘 2](assets/复数查表加广播乘法：官方%20Llama%20的%20RoPE%20算子前向不做矩阵乘/01524.webp)

这张表不是每层算一遍，而是在模型构造时算一次、挂成成员变量：

```python
self.freqs_cis = precompute_freqs_cis(
    # Note that self.params.max_seq_len is multiplied by 2 because ...
    self.params.dim // self.params.n_heads, self.params.max_seq_len * 2
)
```

三个实参分别是 head_dim、`max_seq_len` 的两倍、默认的 10000 [【跳转到 15:44】](https://www.bilibili.com/video/BV1Zr421c76A/?t=944)。

**为什么乘 2**：`end` 取 4096 已经够 Llama 2 用了，之所以再乘一倍，是为了给推理时的动态扩展留出余量——代码注释里写得很直白，不用 4096 这个硬数字，而是用一个可以放大的上界 [【跳转到 16:04】](https://www.bilibili.com/video/BV1Zr421c76A/?t=964)。

**为什么 `dim` 传的是 head_dim**：因为算 QKV 时已经分成多个头，旋转是在每个头内部做的 [【跳转到 15:44】](https://www.bilibili.com/video/BV1Zr421c76A/?t=944)。

![forward 里按 start_pos 与 seqlen 从表里切出这一段位置](assets/复数查表加广播乘法：官方%20Llama%20的%20RoPE%20算子前向不做矩阵乘/00944.webp)

真正用到时只剩一次切片：

```python
freqs_cis = self.freqs_cis[start_pos : start_pos + seqlen]
```

`start_pos` 是这次前向处理的第一个 token 的绝对位置，`seqlen` 是本次的 token 数，切出来的正是"这一段序列各自该转的角度"[【跳转到 25:24】](https://www.bilibili.com/video/BV1Zr421c76A/?t=1524)。这也解释了 decode 阶段为什么只要第 `start_pos` 那一行——生成第 $n$ 个 token 时，序列长度是 1，切出来的表只有一行。

KV cache 的写法让这个设计更顺：q 只需要当前位置的角度，k 需要"历史 + 当前"所有位置的角度，而表按绝对位置索引，两者共用同一张[【跳转到 25:04】](https://www.bilibili.com/video/BV1Zr421c76A/?t=1504)。

---

## 六、几个容易踩的坑

1. **`view_as_complex` 的输入，最后一维长度必须是 2**。前面那次 `reshape` 不是可选的装饰，`view_as_real` 之后也必须 `flatten` 才能回到原形状，两步是一对。
2. **角度表的第二维是 $\frac{d}{2}$ 而不是 $d$**。因为它按"对"计数，实数维度 $d$ 打包成复数后只剩 $\frac{d}{2}$ 个。这也是 `reshape_for_broadcast` 里那条断言的存在理由。
3. **`assert` 不是可删的调试代码**。视频特意逐条解释两条断言：一条防维度数不够，一条防"表与张量对不上"[【跳转到 20:04】](https://www.bilibili.com/video/BV1Zr421c76A/?t=1204)。把断言去掉，错误会推迟到乘法广播那一步，报出来的信息完全看不出原因。
4. **不要手写 cos 和 sin**。`torch.polar` 一次给出复指数，省掉两次三角函数和两次内存写入；而且后面复数乘法只需要一个乘数，不需要分别保存 cos 表和 sin 表。
5. **同一张表要在 q 和 k 上复用**。如果给 q 和 k 用不同的角度（比如漏了某个 head），内积里就不再只剩相对角度差，RoPE 的性质直接被破坏。

---

## 七、这套写法的取舍

用一句话概括官方实现的设计：**用"预计算 + 复数 + 广播"三件套，把逐位置、逐维度的旋转摊平成一次逐元素乘法。**

它换来的好处：

- **零矩阵乘、零显式循环**。整个算子在 PyTorch 层面只有 reshape、复数乘、flatten，全是 element-wise 或元数据操作，编译器优化空间大。
- **表只算一次**。$T\times\frac{d}{2}$ 的复数表在构造时生成，推理时全部是切片，不重复做三角函数。
- **广播代替复制**。`[1, T, 1, d/2]` 的表靠广播铺到 $B\times H$ 份，不额外占显存。
- **形状不变**。进出都是 `[B, T, H, d]`，dtype 也靠 `type_as` 还原，插入 attention 不牵连别处。

代价也很清楚：

- **复数在 GPU 上要拆成两路实数运算**。`view_as_complex` / `view_as_real` 本身不搬数据，但复数乘法底层仍是实部虚部分别算，前后还夹着 `reshape` 与 `flatten` 的元数据整理；一旦某处不连续，就会触发真正的内存拷贝。
- **代码可读性靠注释撑着**。`reshape(*xq.shape[:-1], -1, 2)` 这种写法，离开注释几乎不可能一眼看懂。
- **复数表占的显存是实数表的一半**，但 dtype 是 `complex64`，对某些只支持实数 kernel 的后端（自定义 CUDA/Triton 算子）不友好。

也正因为如此，实际部署里还有另一条路：**不打包复数，直接把 cos 和 sin 存成一张实数缓存表，前向用几次逐元素乘法把旋转写完**。形状更啰嗦，但没有复数拆装，也更容易下沉到自定义 kernel。那套写法在本小节另一篇博客里逐行拆解，两篇对照着看，能看清"复数乘"与"逐元素乘加"其实是同一旋转的两种记法。

---

## 小结

- **RoPE 是形状不变算子**：只作用在 q 和 k 上，进出形状都是 `[B, T, H, d]`，位置信息藏在角度里。
- **位置不是算出来的，是数出来的**：`torch.arange` 按最大长度生成 $0, 1, 2 \dots$ 作为绝对位置 $m$，角度 $m\theta_i$ 里同时包含绝对位置与相对间隔。
- **角速度是频率阶梯**：$\theta_i$ 随维度序号单调递减，前几对维度高频、后几对低频。
- **复数表 = 所有位置的旋转清单**：$T\times\frac{d}{2}$ 的 `freqs_cis` 用 `torch.polar` 生成，模恒为 1，因此乘法只转角度。
- **前向就是五次 reshape**：拆出长度 2 的尾维 → 读成复数 → 广播表 → 复数乘 → 转回实数并拉平。
- **广播靠把无关维度置 1**：`reshape_for_broadcast` 输出 $[1, T, 1, \frac{d}{2}]$，batch 与 head 都不复制实体。
- **表在构造时建一次，前向只切片**：表长按 `max_seq_len` 的两倍建，是为动态扩展留余量，decode 时只取一行。
- **断言是设计的一部分**：序列长度与 $\frac{d}{2}$ 两维对不上必须当场报错。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| RoPE | 旋转位置编码，按位置把 q、k 的相邻两维当成平面上的点整体转一个角度 |
| freqs_cis | 预计算好的复指数表，第 $m$ 行第 $i$ 列是 $e^{i m\theta_i}$ |
| cis | $\cos\theta + i\sin\theta$ 的缩写，等同于 $e^{i\theta}$ |
| torch.polar | 按极坐标（幅度、角度）构造复数 |
| view_as_complex | 把最后一维长度 2 的实数张量读成复数，不拷贝数据 |
| view_as_real | 上一步的逆操作，把复数拆成实部虚部两列 |
| reshape_for_broadcast | 把 $[T, d/2]$ 的角度表重排成 $[1, T, 1, d/2]$，让 batch 与 head 维走广播 |
| head_dim | 单个注意力头的维度，也是 RoPE 旋转的维度范围 |
| 角速度 $\theta_i$ | 第 $i$ 对维度每前进一个位置转过的弧度，随 $i$ 递减 |
| 广播 broadcast | 形状为 1 的维度自动复制成目标长度，且不真实占内存 |
| flatten(3) | 从第 3 维开始往后拉平，用来把实部虚部两维合回 head_dim |
