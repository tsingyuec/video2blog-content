# 把 MHA 变成 MQA：从计算图与 shape 看 MLA 矩阵吸收

> 视频来源：[【手撕MLA】一行行代码讲清Deepseek MLA矩阵吸收](https://www.bilibili.com/video/BV1F5NvzbEdy/)（Bilibili · UP 主 不归牛顿管的熊猫）｜时长约 28 分钟
> 导读：这支视频不推公式，而是拿两张计算图（naive 版 / 吸收版）和一段可以跑的 `forward`，把 MLA 矩阵吸收拆成「找到 number heads 从哪来 → 把它搬走 → 用 `torch.bmm` 对齐形状」三步。它的独特视角是：**矩阵吸收的实质是把 MHA 改写成 MQA**。字幕口误（`懒EAM`→naive、`contact`→concat、`赵辰`→造成、`sheep`→shape、`未定`→v dim、`扣`→q、`洛尔`→lora）已按上下文订正。MLA 的低秩压缩本身见同系列 §8.3.2，本文只讲吸收这一步。

## 本讲要解决的核心问题（SCQA）

**背景**：MLA 把每个 token 的 K/V 压成一条共享的隐向量 `latent kv cache`，需要时再用上投影矩阵 `kv_proj_up` 还原成每个头的 K 和 V。这是 §8.3.2 的内容。

**冲突**：还原这一步在 decode 阶段非常昂贵——它要对**整条上下文**的隐向量重做一次升维，而且升维结果带着 `number heads` 这一维，等于把压缩省下来的空间又按头数乘了回去。更麻烦的是，naive 实现里还有两个 `concat`，每次都要开新显存、搬数据。

**疑问**：能不能把这个上投影矩阵整个「搬走」，让隐向量直接参与注意力计算？

**回答（中心思想）**：能，而且搬走之后你会发现一件事——**KV 侧的头数变成了 1，Q 侧还是 `number heads`，这正是 MQA 的定义**。所以矩阵吸收不是「省一次矩阵乘法」这么简单，它是**把 MLA 的 decode 计算从 MHA 形态改写成 MQA 形态**：`kv_proj_up` 的权重被切成 $W^{UK}$ 与 $W^{UV}$ 两段，$W^{UK}$ 搬到 query 侧与 `q_nope` 做一次 `torch.bmm`，$W^{UV}$ 搬到输出侧与注意力结果做一次 `torch.bmm`。两个 `concat` 也随之消失。[【跳转到 00:29】](https://www.bilibili.com/video/BV1F5NvzbEdy/?t=29)

---

## 一、先找出「万恶之源」：`number heads` 是哪一步冒出来的

UP 主的分析路径很工程化：**不要先问「怎么吸收」，先问「MHA 的形状是哪一行代码造成的」**。

naive 版的计算图长这样：输入 hidden states 分两路，左路走 `q_proj_down → q_proj_up → split` 得到 `q_nope` 与 `q_rope`；右路走 `kv_proj_down` 得到 `latent kv cache`，再经 `kv_proj_up` 升维、`split` 成 `k_nope` 与 `v`，同时另有一条 `RoPE → broadcast` 得到 `k_rope`。两条路各自 `concat`，然后送进 `MHA`。[【跳转到 00:54】](https://www.bilibili.com/video/BV1F5NvzbEdy/?t=54)

![naive 版计算图：kv_proj_up 之后才出现 number heads，两个 concat 用红圈标出](assets/把%20MHA%20变成%20MQA：从计算图与%20shape%20看%20MLA%20矩阵吸收/00054.webp)

UP 主指着图说：KV 经过这一系列线性变换之后，头的数量是 `number heads`。**如果把它变成 1**，也就是 KV 的头数都是 1、而 Q 的头数是 `number heads`，那这里就是 MQA 了。[【跳转到 00:54】](https://www.bilibili.com/video/BV1F5NvzbEdy/?t=54)

那么 `number heads` 是在哪一步形成的？他直接给答案：在 `kv_proj_up` 这个线性层。看它的 weight 形状——`number heads × (qk_nope_dim + v_dim)`。注意 `kv_proj_up` 的**输入**（也就是 `latent kv cache`）在图里根本没有 `number heads` 这一维，没写出来就默认是 1。[【跳转到 01:04】](https://www.bilibili.com/video/BV1F5NvzbEdy/?t=64)

结论就出来了：只要干掉 `kv_proj_up`、把它挪到别处，让隐向量直接参与注意力，KV 侧的头数就永远是 1，attention 自动变成 MQA。

## 二、搬走之后：计算图变成什么样

吸收版的计算图把 `kv_proj_up` 的权重 `split` 成两部分——$W^{UK}$ 和 $W^{UV}$：

- $W^{UK}$ 搬到左边，去和 `q_nope` 相乘。乘出来的结果**仍然叫 `q_nope`**，但它的最后一维已经不是 nope 维，而是**压缩维度 `kv_lora_rank`**。
- $W^{UV}$ 搬到最下面，放到 `o_proj` 之前，去乘注意力算完之后的结果。

![吸收版计算图：kv_proj_up 的权重被 split 成 W^UK 与 W^UV，前者进 torch.bmm 与 q_nope 相乘，后者放到 o_proj 之前](assets/把%20MHA%20变成%20MQA：从计算图与%20shape%20看%20MLA%20矩阵吸收/00184.webp)

UP 主在这张图上逐个标注了 shape，这是全片信息密度最高的一帧 [【跳转到 06:15】](https://www.bilibili.com/video/BV1F5NvzbEdy/?t=375)：

| 张量 | shape |
| --- | --- |
| `k_rope` | `(batchsize, seqlen_k, 1, q_rope_dim)`，头数为 1 |
| `k_nope` | `(batchsize, seqlen_k, 1, kv_lora_rank)`，头数为 1 |
| `q_nope`（吸收前） | `(batchsize, seqlen, num_heads, q_nope_dim)` |
| `q_nope`（吸收后） | `(batchsize, seqlen, num_heads, kv_lora_rank)` |
| `q_rope` | `(batchsize, seqlen, num_heads, q_rope_dim)` |
| $W^{UK}$ | `(num_heads, q_nope_dim, kv_lora_rank)` |
| $W^{UV}$ | `(kv_lora_rank, num_heads * v_dim)` |

![吸收版的 shape 标注：q_nope 吸收后末维变成 kv_lora_rank，KV 侧头数为 1，图中把 attention 标成 MQA](assets/把%20MHA%20变成%20MQA：从计算图与%20shape%20看%20MLA%20矩阵吸收/00615.webp)

对着这张表就能看出「MQA」是怎么来的：

- `q_rope` 的头数是 `num_heads`，`k_rope` 的头数是 1 → 这一支是 MQA；
- `q_nope` 的头数是 `num_heads`，`k_nope`（就是隐向量本身）的头数是 1 → 这一支也是 MQA。

UP 主原话：「这个时候 shape 就匹配了，`q_rope` 和 `k_rope` 算一下、`q_nope` 和 `k_nope` 算一下，大家做的都是 MQA，所以这里就变成了 MQA。」[【跳转到 09:25】](https://www.bilibili.com/video/BV1F5NvzbEdy/?t=565)

## 三、为什么可以这样搬：一行结合律

UP 主说推导写在他的公众号里，屏幕上只给了三行 [【跳转到 10:15】](https://www.bilibili.com/video/BV1F5NvzbEdy/?t=615)：

$$
\text{attention score} = Q K = (W^{UQ} c^{Q})\,(W^{UK} c^{KV}) = (W^{UQ\top} W^{UK})\, c^{Q\top} c^{KV}
$$

也就是把 $W^{UK}$ 从 KV 侧挪到 Q 侧，让它和 `W^UQ` 先乘一次。落到代码里，这一步就是 `torch.bmm(q_nope, q_absorb)`——`q_nope` 已经是 `W^UQ` 乘过的结果，再乘一次 $W^{UK}$ 就等价于「先合并两个矩阵、再乘隐向量」。UP 主强调这里能一一对上：`q_proj_up` 就是 `W^UQ`，做完 `W^UQ` 后再与 $W^{UK}$ 相乘。[【跳转到 10:20】](https://www.bilibili.com/video/BV1F5NvzbEdy/?t=620)

value 侧同理，只是方向相反：$W^{UV}$ 带着 `number heads` 这个维度「也很烦」，所以把它**踢到后面去**，放在注意力加权求和之后、`o_proj` 之前。这样中间结果的头数维度虽然还在，但乘的对象已经从「每个历史 token」变成了「每个新 token」，规模差了一个上下文长度。[【跳转到 11:00】](https://www.bilibili.com/video/BV1F5NvzbEdy/?t=660)

## 四、代码怎么改：三处 `split` 加两次 `bmm`

### 4.1 切权重

UP 主把 naive 版里所有跟 `kv_projection_up` 相关的代码「和你前女友有关的一切都抹掉」，然后重新写 [【跳转到 07:14】](https://www.bilibili.com/video/BV1F5NvzbEdy/?t=434)：

```python
# 把 number heads 提到第一维
kv_b_proj = self.kv_b_proj.weight.view(
    self.num_heads, -1, self.kv_lora_rank
)
# W^UK：吸收进 Q，取到 q_nope_dim 为止
q_absorb  = kv_b_proj[:, : self.qk_nope_head_dim, :]
# W^UV：踢到后面给 output，从 q_nope_dim 开始到末尾
out_absorb = kv_b_proj[:, self.qk_nope_head_dim :, :]
```

![代码里把 kv_b_proj 的权重 view 成 (num_heads, -1, kv_lora_rank) 再切成 q_absorb 与 out_absorb](assets/把%20MHA%20变成%20MQA：从计算图与%20shape%20看%20MLA%20矩阵吸收/00756.webp)

UP 主解释为什么要先 `view`：原始权重是 `(kv_lora_rank, num_heads * (q_nope_dim + v_dim))`，`number heads` 藏在第二维里面，必须把它提到第一维才能按头切开。

### 4.2 第一次 `bmm`：query 侧吸收

```python
q_nope = torch.bmm(q_nope, q_absorb)
```

写下去就报错，因为 `torch.bmm` 要求两个张量的**第一维是批（这里就是 head）且相等**。而 `q_nope` 现在的形状是 `(batch, seq, num_heads, q_nope_dim)`，head 在第三维。UP 主来回 `view`、`transpose` 了好几次，最后「一次到位」[【跳转到 09:54】](https://www.bilibili.com/video/BV1F5NvzbEdy/?t=594)：

```python
q_nope = q_nope.view(self.num_heads, batch, seq, self.qk_nope_head_dim)
q_nope = torch.bmm(q_nope, q_absorb)   # -> (num_heads, batch, seq, kv_lora_rank)
q_nope = q_nope.view(batch, seq, self.num_heads, self.kv_lora_rank)
```

中间结果的形状是 `number heads × batch size × kv lora rank`——**最后一维是压缩维度**，这就是「吸收完成」的标志。

![bmm 前后的 shape 对齐：q_nope 需要把 num_heads 提到第一维，结果末维变成 kv_lora_rank](assets/把%20MHA%20变成%20MQA：从计算图与%20shape%20看%20MLA%20矩阵吸收/00994.webp)

### 4.3 分数分两段算

```python
scores = torch.bmm(q_rope, k_rope.transpose(1, 2)) \
       + torch.bmm(q_nope, kv)
```

UP 主说 `k_rope` 也要 `transpose` 一下，把 head 维度提到前面；`q_nope` 则是和 `kv`（也就是隐向量本身，形状 `(batch, seqlen, kv_lora_rank)`）直接相乘。两支都是 MQA 形状，所以能直接相加。[【跳转到 12:02】](https://www.bilibili.com/video/BV1F5NvzbEdy/?t=722)

![rope 分支的 score 计算，k_rope 需要 transpose 把 head 提到第一维](assets/把%20MHA%20变成%20MQA：从计算图与%20shape%20看%20MLA%20矩阵吸收/01202.webp)

### 4.4 第二次 `bmm`：输出侧吸收

```python
y = torch.bmm(attn, kv)              # (num_heads, batch, seq, kv_lora_rank)
y = torch.bmm(y, out_absorb.mT)      # -> (num_heads, batch, seq, v_dim)
y = y.view(batch, seq, self.num_heads * self.v_dim)
y = self.o_proj(y)
```

`attn` 是 softmax 之后的注意力权重，它乘的是**隐向量 `kv`** 而不是升维后的 value——这就是 value 吸收在代码里的样子。乘完 `out_absorb` 的转置后，`kv_lora_rank` 被消掉，最后一维变成 `v_dim`，再 `view` 成 `num_heads * v_dim` 交给 `o_proj`。[【跳转到 15:02】](https://www.bilibili.com/video/BV1F5NvzbEdy/?t=902)

### 4.5 前后对照

UP 主把 naive 版的 MHA 段和吸收版并排放，差别一目了然 [【跳转到 15:77】](https://www.bilibili.com/video/BV1F5NvzbEdy/?t=977)：

- naive 版：`scores = torch.matmul(q.transpose(1,2), k.transpose(-2,-1)) / sqrt(...)`，然后 `y = torch.matmul(attn, v)`，其中 `k`、`v` 都是 `kv_b_proj` 升维出来的完整张量；
- 吸收版：`scores = bmm(q_rope, k_rope) + bmm(q_nope, kv)`，`y = bmm(attn, kv)` 再 `bmm(y, out_absorb.mT)`。

![naive 版 MHA 段：k、v 都由 kv_b_proj 升维得到，attention 用完整头数的 matmul](assets/把%20MHA%20变成%20MQA：从计算图与%20shape%20看%20MLA%20矩阵吸收/01502.webp)

![吸收版全貌：kv_b_proj 切成 q_absorb 与 out_absorb，两次 bmm 完成吸收，attention 变成 MQA](assets/把%20MHA%20变成%20MQA：从计算图与%20shape%20看%20MLA%20矩阵吸收/01577.webp)

UP 主最后总结这次改造「最主要的就是把 70 到 73 行这个 `kv_proj` 分割成了 74 到 76 行」，然后基于分割重算 `q_nope`、改 attention、把 $W^{UV}$ 吸收到 output 这里，「变化主要就是这里，仅此而已」。[【跳转到 16:02】](https://www.bilibili.com/video/BV1F5NvzbEdy/?t=962)

## 五、这套改造省下的到底是什么

把 UP 主的两张图和一次 shape 对照串起来，收益可以归成三条：

1. **不再生成「每头 × 每 token」的完整 K/V**。naive 版 `kv_proj_up` 的输出形状是 `(batchsize, seqlen_k, num_heads, q_nope_dim + v_dim)`，seqlen 是整条上下文；吸收后这条路径彻底消失，attention 直接吃 `(batchsize, seqlen_k, kv_lora_rank)` 的隐向量。
2. **两个 `concat` 被删掉**。naive 版要用 `torch.empty` 开新张量再把 nope、rope 两段拷进去，UP 主说「这个也会做一些内存搬运操作，比较耗时」；吸收版让两段各自算一个 score 再相加，因为点积对拼接是可加的。[【跳转到 00:29】](https://www.bilibili.com/video/BV1F5NvzbEdy/?t=29)
3. **计算形态从 MHA 变成 MQA**。KV 侧头数为 1、Q 侧为 `number heads`，可以直接套用现成的 MQA 优化路径。

代价则体现在实现层面：`torch.bmm` 强制要求批维在第一维，所以代码里塞满了 `view` / `transpose`；UP 主在视频里反复因为形状对不上而报错重来，这本身就是吸收版实现的主要工作量。[【跳转到 09:44】](https://www.bilibili.com/video/BV1F5NvzbEdy/?t=584)

## 小结

- 找 MHA 形状的来源，比直接背公式有效：`number heads` 是在 `kv_proj_up` 这一步冒出来的，干掉它，KV 侧头数就永远是 1。
- 吸收 = 把 `kv_proj_up` 的权重切成 $W^{UK}$ 与 $W^{UV}$，前者搬到 query 侧、后者搬到输出侧，各做一次 `torch.bmm`。
- 吸收后 `q_nope` 的最后一维从 nope 维变成压缩维 `kv_lora_rank`，这是判断「吸收成功」的标志。
- 分数分两段算（rope 一支、nope 一支）再相加，可以删掉两个 `concat`，因为点积对拼接是可加的。
- 本质是 **MHA → MQA**：KV 侧单头共享、Q 侧多头，于是能复用 MQA 的优化路径。
- 实现代价是大量的形状对齐工作，`torch.bmm` 的批维要求是主要摩擦点。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| naive 实现 | 每步 decode 都从隐向量升维出完整 K/V 再算 MHA 的版本 |
| `kv_proj_up` | 把共享隐向量升维成每头 K/V 的上投影层，`number heads` 由它引入 |
| $W^{UK}$ / $W^{UV}$ | 上投影权重被切成的两段，分别吸收进 query 侧与输出侧 |
| `q_absorb` / `out_absorb` | 代码里对这两段的命名 |
| `torch.bmm` | 批矩阵乘，要求批维在第一维，所以吸收版代码里到处是 `view` / `transpose` |
| `kv_lora_rank` | 隐向量的压缩维度，吸收后它成为 `q_nope` 与注意力中间结果的末维 |
| move elision | 不拼接 rope 与 nope，两段分数分别算再相加 |
| MQA 形态 | KV 侧单头共享、Q 侧多头，矩阵吸收后 MLA 的 decode 计算即为此形态 |