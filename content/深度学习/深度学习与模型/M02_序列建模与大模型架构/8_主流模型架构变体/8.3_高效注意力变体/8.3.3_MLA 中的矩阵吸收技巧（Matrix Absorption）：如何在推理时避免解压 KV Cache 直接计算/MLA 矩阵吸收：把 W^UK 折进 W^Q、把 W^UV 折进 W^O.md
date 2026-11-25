# MLA 矩阵吸收：把 $W^{UK}$ 折进 $W^{Q}$、把 $W^{UV}$ 折进 $W^{O}$

> 视频来源：[从零手撕DeepSeek MLA矩阵吸收算法（MultiHead Latent Attention）-（矩阵吸收版）](https://www.bilibili.com/video/BV1wjQvY6Enm/)（Bilibili · UP 主 袁朝发）｜时长约 37 分钟
> 导读：这支视频只做一件事——把 MLA 推理时「缓存隐向量」和「不解压隐向量」这对矛盾，用两次矩阵乘法的顺序调整消掉。UP 主先对着自己写的推导页把 key、value 两次吸收的公式逐行念完，再在 Jupyter 里把 naive 版 forward 改成吸收版并跑通。本文按「为什么要吸收 → key 怎么吸收 → value 怎么吸收 → 不拼接 rope/nope → 代码怎么改 → 代价是什么」的顺序整理。字幕口误（`tension`→attention、`升为`→升维、`转制`→转置、`苏建林`→苏剑林、`more elision`→move elision、`contact`→concat）已按上下文订正。MLA 的低秩压缩本身（576 维怎么来的、与 MHA/GQA 的缓存对比）已在同系列 §8.3.2 讲过，本文只在必要处一句话回指。

## 本讲要解决的核心问题（SCQA）

**背景**：MLA 把每个 token 的 K 和 V 联合压成一条低维隐向量 $c_t^{KV}$（DeepSeek-V2 里 512 维），再单开一条 64 维的共享位置分支，缓存里只需要留这两样。这是 §8.3.2 已经算清楚的账。

**冲突**：账算得漂亮，但**官方 HuggingFace 实现并没有真的省**。UP 主点开官方代码指出：原始实现缓存的是「升维之后、并且已经应用了 RoPE 的完整 KV」——也就是每一层、每一个头都存一份完整的 K 和 V，这种实现被称为 **CacheDecompressed（CD）**。就算你改成只缓存 $c_t^{KV}$（**Cache Compressed，CC**），每次 decode 又必须把它重新升维成 128 个头的 K 和 V 才能算注意力，计算量随之暴涨。[【跳转到 00:55】](https://www.bilibili.com/video/BV1wjQvY6Enm/?t=55)

**疑问**：能不能既只存那一条隐向量，又不在每一步解码时把它解压开？

**回答（中心思想）**：能，靠**矩阵吸收（matrix absorption）**。注意力的分数本质是一个点积，而点积里的两个因子都是「隐向量乘一个升维矩阵」得到的。把转置拆开、用乘法结合律重排，升维矩阵就能被搬到对面去：$W^{UK}$ 折进 query 的升维矩阵 $W^{UQ}$，$W^{UV}$ 折进输出的投影矩阵 $W^{O}$。这两个乘积可以离线算好，于是推理时只拿 $c_t^{KV}$ 直接参与点积，**整条链上不再出现「每头每 token 的完整 K/V」这个中间张量**。再加一个「不拼接 rope 与 nope」的小优化，naive 版里的两个 `concat` 也被删掉。[【跳转到 04:46】](https://www.bilibili.com/video/BV1wjQvY6Enm/?t=286)

---

## 一、先分清两种缓存：CD 存完整 KV，CC 只存隐向量

### 1.1 CacheDecompressed：官方原始实现其实没省空间

UP 主把官方 `modeling_deepseek.py` 的 `forward` 摊开，指着入参说：这里传进来的是 `past_key_value`，缓存的是**升维之后、并且已经套过 RoPE 的 kv**，而不是压缩后的 $c_t^{KV}$。代码注释里也写着「实际只要缓存这个就行，不存着 kv states」，但原始实现并没有这么做。[【跳转到 00:55】](https://www.bilibili.com/video/BV1wjQvY6Enm/?t=55)

![官方原始实现把升维后的完整 KV 存进 cache，注释里写着「实际只要缓存 compressed_kv 就行」](assets/MLA%20矩阵吸收：把%20W^UK%20折进%20W^Q、把%20W^UV%20折进%20W^O/00055.webp)

这种实现的好处是**计算路径最短**：缓存里拿出来的就是能直接做点积的 K 和 V，不需要任何额外变换。坏处是缓存体积按「$batch \times seq\_len \times num\_heads \times (nope\_dim + rope\_dim)$」算，MLA 的全部压缩收益都被抵消掉了。

### 1.2 Cache Compressed：缓存只剩隐向量，但每次都要升维

第二种做法是只缓存 $c_t^{KV}$。UP 主给出它的 shape 变化：缓存内容从 $batch \times seq\_len \times num\_heads \times (nope\_dim + rope\_dim)$ 变成 $batch \times seq\_len \times compressed\_dim$。这里省了两笔：

- 最后一维从「每头 nope 维 + rope 维」缩成一条 `compressed_dim`；
- $c_t^{KV}$ 是**所有头共享**的，`num_heads` 这一维直接消失。[【跳转到 01:05】](https://www.bilibili.com/video/BV1wjQvY6Enm/?t=65)

![compressed_kv 的入参与 shape：缓存从 (batch, seq_len, num_head, nope+rope) 变成 (batch, seq_len, compressed_dim)](assets/MLA%20矩阵吸收：把%20W^UK%20折进%20W^Q、把%20W^UV%20折进%20W^O/00105.webp)

省下空间之后，可以直接换更大的 batch size，推理更快。但 UP 主紧接着指出这条路的问题：**实现虽然简单（算的时候重新升维就行），计算量却极大增加**——你要把一条 `compressed_dim` 的向量升到「每头 nope 维 + v 维」，还要复制成 `num_heads` 份。他引清华那篇 blog 的实测对比：压缩后单 token 的 cache 大小明显下降，但计算量明显上升。[【跳转到 01:55】](https://www.bilibili.com/video/BV1wjQvY6Enm/?t=115)

于是矛盾摆在面前：**存得少就要算得多**。矩阵吸收要解决的正是这个矛盾——它让「存得少」不必以「算得多」为代价。

## 二、key 的吸收：把 $W^{UK}$ 折进 $W^{UQ}$

### 2.1 四行推导

UP 主把推导页放在屏幕正中，从注意力分数开始念 [【跳转到 02:46】](https://www.bilibili.com/video/BV1wjQvY6Enm/?t=166)：

$$
\begin{aligned}
\text{attentionweight} &= q_t^\top k_t \\
&= (W^{UQ} c_t^{Q})^\top\, W^{UK} c_t^{KV} \\
&= c_t^{Q\top} W^{UQ\top} W^{UK} c_t^{KV} \\
&= (c_t^{Q\top} W^{UQ\top} W^{UK})\, c_t^{KV}
\end{aligned}
$$

四步分别做了什么：

1. **第一行**是注意力的定义：第 $t$ 个 token 的 query 与 key 做内积，得到相似度分数。
2. **第二行**把 $q_t$、$k_t$ 换回它们的来历：query 是「压缩后的 query 隐向量 $c_t^{Q}$ 乘上投影矩阵 $W^{UQ}$」，key 是「压缩后的 KV 隐向量 $c_t^{KV}$ 乘上投影矩阵 $W^{UK}$」。
3. **第三行**把转置拆进去：$(AB)^\top = B^\top A^\top$，于是 $W^{UQ}$ 的转置跑到前面，两个隐向量各自留在两头。
4. **第四行**用乘法结合律重新加括号：$W^{UQ\top}$ 和 $W^{UK}$ 都是**与输入无关的固定权重**，可以先乘起来变成一个矩阵。

![推导页：key 的矩阵吸收四行公式，以及下方 value 的吸收公式](assets/MLA%20矩阵吸收：把%20W^UK%20折进%20W^Q、把%20W^UV%20折进%20W^O/00230.webp)

### 2.2 为什么这一步能省算力

关键在于**括号的位置决定了中间张量的形状**。

- 吸收前：要先算出 $k_t = W^{UK} c_t^{KV}$，形状是「$num\_heads \times (nope\_dim + rope\_dim)$」——每个头一份，每个历史 token 一份。这一步在 decode 阶段是**对整条上下文重做**的（除非你把它缓存下来，那就退回了 CD）。
- 吸收后：先算 $(c_t^{Q\top} W^{UQ\top} W^{UK})$，这仍然是 query 侧的量，**每个头一份、每个新 token 一份**。decode 时 query 的长度只有 1，所以这个中间量极小；然后它直接和 $c_t^{KV}$ 做点积。

UP 主原话的意思很直白：generate 的时候 Q 的长度很短、只有 1，所以把升维挪到 query 侧，减少了很多浮点运算，运算也就更快 [【跳转到 03:46】](https://www.bilibili.com/video/BV1wjQvY6Enm/?t=226)。

### 2.3 一个必须说明的假设

UP 主特意提到苏剑林博客里的提醒：**想做这件事，核心假设是精度无限**。因为 $W^{UQ\top} W^{UK}$ 这个乘积一旦离线算好，就再也回不到「先升维再点积」的那条路径上了；浮点运算的顺序变了，结果不会逐位相同。精度足够高时，这两种算法在数值上几乎等价，可以放心合并。[【跳转到 03:21】](https://www.bilibili.com/video/BV1wjQvY6Enm/?t=201)

## 三、value 的吸收：把 $W^{UV}$ 折进 $W^{O}$

### 3.1 同样的套路，换一个位置

key 的吸收作用在**点积**上；value 的吸收作用在**加权求和**上。UP 主说网上讲 value 吸收的资料都用爱因斯坦求和方程来解释，他这里直接把公式写出来 [【跳转到 04:21】](https://www.bilibili.com/video/BV1wjQvY6Enm/?t=261)：

$$
\begin{aligned}
\text{finaloutput} &= A_{\text{weight}}\,(W^{UV} C^{KV})\, W^{O} \\
&= A_{\text{weight}}\, C^{KV}\, W^{UV}\, W^{O} \\
&= A_{\text{weight}}\, C^{KV}\, (W^{UV} W^{O})
\end{aligned}
$$

- 第一行是原始路径：先用 $W^{UV}$ 把 $C^{KV}$ 升维成每头的 value，用注意力权重加权求和，最后乘输出投影 $W^{O}$。
- 第二行只是把括号去掉——矩阵乘法本来就满足结合律，这里没有做任何近似。
- 第三行把后两个固定矩阵合成一个：$W^{UV} W^{O}$ 与输入无关，可以离线算好。

于是推理时可以先算 $A_{\text{weight}} C^{KV}$，得到形状 $(b, h, q, c)$ 的中间量，再乘一次合并后的矩阵。**中间张量从「每头 $v\_dim$ 维」变成「每头 $c$ 维（压缩维度）」，显存占用也随之下降**。[【跳转到 05:30】](https://www.bilibili.com/video/BV1wjQvY6Enm/?t=330)

![value 吸收的公式，以及用 einsum 表示的三步运算顺序调整](assets/MLA%20矩阵吸收：把%20W^UK%20折进%20W^Q、把%20W^UV%20折进%20W^O/00446.webp)

### 3.2 einsum 版本：三步顺序调整

UP 主贴出 blog 里的 einsum 写法，把它拆成「原路径」和「重排路径」两段对照 [【跳转到 05:05】](https://www.bilibili.com/video/BV1wjQvY6Enm/?t=305)：

```python
# 原路径：先升维，再加权求和，再输出投影
v_t = einsum('hdc,blc->blhd', W_UV, c_t_KV)   # (1)
o   = einsum('bqhl,blhd->bqhd', a, v_t)      # (2)
u   = einsum('hdd,bqhd->bqh', W_O, o)        # (3)

# 重排路径：先加权求和，再乘合并矩阵
o_  = einsum('bhql,blc->bhqc', a, c_t_KV)    # (4)
o   = einsum('bhqc,hdc->bqhd', o_, W_UV)     # (5)
u   = einsum('hdd,bqhd->bqh', W_O, o)        # (6)
```

![einsum 版的三步重排，注释里点明中间变量从 (b, l, h, d) 变成 (b, h, q, c)](assets/MLA%20矩阵吸收：把%20W^UK%20折进%20W^Q、把%20W^UV%20折进%20W^O/00580.webp)

UP 主念了 blog 里的注释，这句话是全篇的要点：**相对于 (1) 来说，(4) 的中间变量更小，从 $(b, l, h, d)$ 变成了 $(b, h, q, c)$**。其中 $h$ 是头数、$d$ 是 value 维度、$c$ 是压缩维度、$l$ 是上下文长度、$q$ 是 query 长度。decode 时 $q=1$，而 $l$ 可以上万，所以这个差别是数量级的。

## 四、第三个优化：不拼接 rope 与 nope

MLA 的 query 和 key 都是「nope 部分 + rope 部分」拼起来的：nope 部分走低秩主干，rope 部分走那条 64 维的共享位置分支。naive 实现的做法是用 `torch.empty` 开一块新显存，再把两段分别拷进去 [【跳转到 06:32】](https://www.bilibili.com/video/BV1wjQvY6Enm/?t=392)：

```python
query_states = torch.empty(b, num_heads, q_len, q_head_dim, ...)
query_states[..., :qk_nope_head_dim] = q_nope
query_states[..., qk_nope_head_dim:] = q_pe
key_states = torch.empty(b, num_heads, q_len, q_head_dim, ...)
key_states[..., :qk_nope_head_dim] = k_nope
key_states[..., qk_nope_head_dim:] = k_pe
```

![naive 版用 torch.empty 加切片赋值把 nope 与 rope 拼成完整的 query/key](assets/MLA%20矩阵吸收：把%20W^UK%20折进%20W^Q、把%20W^UV%20折进%20W^O/00632.webp)

UP 主把这种拼接称作「产生了很多中间变量」。而**注意力分数对两部分是可加的**——因为拼接后的点积等于两段点积之和：

$$
q^\top k = q_{nope}^\top k_{nope} + q_{rope}^\top k_{rope}
$$

所以完全可以不拼：rope 部分单独算一个分数，nope 部分单独算一个分数，两个分数相加再 softmax。UP 主把这个优化叫 **move elision**（他自己也说不知道该译成什么中文），它的收益是**消掉两块中间显存和两次内存搬运** [【跳转到 06:57】](https://www.bilibili.com/video/BV1wjQvY6Enm/?t=417)。

到这里，吸收版的三个优化就齐了：key 的吸收、value 的吸收、move elision。UP 主强调，这也是为什么吸收版 forward 里「看起来还在做乘法」——它并没有把所有东西都离线合并，而是**调整了乘法的顺序，让中间大矩阵不再生成**。

## 五、代码怎么改：从 naive 到吸收版

### 5.1 入参多了一个 `compressed_kv`

naive 版 forward 的入参是 `hidden_states`、`position_ids`、`attention_mask` 三个；吸收版多了一个 `compressed_kv`，也就是那条隐向量。UP 主特意说明：`hidden_states` 的 shape 是 `batch_size × Q长度 × hidden_size`，**这里的 Q 长度指 generate 时的 query 长度，通常就是 1**；训练时和以前没区别。他测试时会故意把 Q 长度设成 1，好让观众感受「等于 1 和不等于 1」的差别。[【跳转到 08:50】](https://www.bilibili.com/video/BV1wjQvY6Enm/?t=530)

### 5.2 把升维矩阵拆成 `q_absorb` 与 `out_absorb`

这是整个改造的核心一行。UP 主把 `kv_up_proj.weight` 先 `view` 成 `(num_heads, -1, kv_lora_rank)`，再沿中间维度切成两段 [【跳转到 13:46】](https://www.bilibili.com/video/BV1wjQvY6Enm/?t=826)：

```python
kv_up_proj = self.kv_up_proj.weight.view(self.num_heads, -1, self.kv_lora_rank)
# q_absorb 是 W^UK：负责把隐向量映射到每头的 nope 维
q_absorb  = kv_up_proj[:, : self.qk_nope_head_dim, :]
# out_absorb 是 W^UV：负责把隐向量映射到每头的 value 维
out_absorb = kv_up_proj[:, self.qk_nope_head_dim :, :]
```

![把 kv_up_proj 的权重拆成 q_absorb（W^UK）与 out_absorb（W^UV）两段](assets/MLA%20矩阵吸收：把%20W^UK%20折进%20W^Q、把%20W^UV%20折进%20W^O/01366.webp)

UP 主解释命名：K 的升维矩阵要和 query 做吸收，所以叫 `q_absorb`；value 的升维矩阵要和 output 做吸收，所以叫 `out_absorb`。它们本来就是同一个大矩阵的两段，只是被拆成两个小矩阵。

同理，`compressed_kv` 也要沿最后一维拆成两段：前 `kv_lora_rank` 维是隐向量本体，后 `qk_rope_head_dim` 维是那条共享的位置分支。UP 主在这里做了一个简化假设——**`compressed_kv` 里已经包含了 rope 的 embedding**，所以只需要对 query 做位置编码，key 侧不用再做。[【跳转到 14:06】](https://www.bilibili.com/video/BV1wjQvY6Enm/?t=846)

### 5.3 query 侧先吸收

```python
q_nope = torch.matmul(q_nope, q_absorb)
```

这一行就是第二节推导的最后一行：$q_{nope}$ 本来是 $c_t^{Q} W^{UQ}$ 的 nope 部分，再乘上 $W^{UK}$，得到的就是「已经吸收好的 query」。它的形状是 `(batch, seq, num_heads, kv_lora_rank)`——注意最后一维是**压缩维度**，不是 nope 维度。[【跳转到 15:07】](https://www.bilibili.com/video/BV1wjQvY6Enm/?t=907)

![代码里的 q_nope = torch.matmul(q_nope, q_absorb)，紧跟在 rope 位置编码之后](assets/MLA%20矩阵吸收：把%20W^UK%20折进%20W^Q、把%20W^UV%20折进%20W^O/01567.webp)

### 5.4 注意力分数分两段算、再相加

```python
attention_weights = (
    torch.matmul(q_rope, k_rope.mT)                        # rope 分支
    + torch.matmul(q_nope, compressed_kv.unsqueeze(-3).mT)  # nope 分支，直接在隐向量上算
) / math.sqrt(self.q_head_dim)
```

UP 主逐项对照公式：`q_rope @ k_rope.mT` 是 rope 分支的分数，这一段**不涉及矩阵吸收**，因为位置编码是在升维之后才作用上去的，吸收不了；`q_nope @ compressed_kv.mT` 就是吸收后的 nope 分支——`q_nope` 已经乘过 `q_absorb`（也就是 $W^{UK}$），所以直接和隐向量点积即可。`unsqueeze(-3)` 是把隐向量的单头维度补出来，让广播对齐到 `num_heads`。[【跳转到 16:46】](https://www.bilibili.com/video/BV1wjQvY6Enm/?t=1006)

![attention_weights 由 rope 段与 nope 段两个 matmul 相加得到，nope 段直接乘 compressed_kv](assets/MLA%20矩阵吸收：把%20W^UK%20折进%20W^Q、把%20W^UV%20折进%20W^O/01676.webp)

### 5.5 输出侧再吸收

```python
attn_output = torch.einsum("bhql,blc->bhqc", attention_weights, compressed_kv)
attn_output = torch.matmul(attn_output, out_absorb)
attn_output = self.o_proj(attn_output)
```

第一行是 $A_{\text{weight}} C^{KV}$：用注意力权重直接对**隐向量**加权求和，得到 `(b, h, q, c)`，而不是 `(b, l, h, d)`。第二行乘 `out_absorb`（$W^{UV}$）把 $c$ 维还原成 $v$ 维，第三行才是真正的输出投影 $W^{O}$。UP 主在这里补充了一句：清华那篇 blog 实测发现，**把 $W^{UV}$ 和 $W^{O}$ 真的离线乘成一个矩阵，速度反而不如保持两步**——所以代码里保留了两次乘法，靠的只是顺序调整带来的中间张量缩小。[【跳转到 18:50】](https://www.bilibili.com/video/BV1wjQvY6Enm/?t=1130)

![吸收版 forward 全貌：q_nope 先吸收、分数两段相加、输出 einsum 后乘 out_absorb](assets/MLA%20矩阵吸收：把%20W^UK%20折进%20W^Q、把%20W^UV%20折进%20W^O/01885.webp)

### 5.6 跑通时踩的三个坑

UP 主改完直接运行，报错，然后逐个修 [【跳转到 19:11】](https://www.bilibili.com/video/BV1wjQvY6Enm/?t=1151)：

1. **忘记 transpose**：`split` 之后要把 `num_heads` 提到第一维，否则维度对不上；
2. **bmm 的批维顺序**：`torch.bmm` 要求第一维是批（这里是 head），所以必须把张量变成 `(batch, num_heads, seq, dim)` 这种形式；
3. **`view` 的 `-1` 用错**：最后一个维度填 `-1` 时，前面给的维度必须能整除总元素数，这里应该是 `self.head_dim` 而不是随便一个变量。

这三条都是实现细节，但恰好说明「吸收」在纸面上是纯粹的代数恒等式，落到代码里却是**一堆形状对齐工作**。

## 六、代价与约束：吸收不是免费的

### 6.1 精度假设

吸收把「先升维、再点积」改成「先合并矩阵、再点积」，浮点运算顺序变了，结果不再逐位相同。UP 主引苏剑林的说法：这件事成立的前提是**精度足够高**。低精度（如 FP8）推理时，合并矩阵可能放大误差，需要单独评估。[【跳转到 03:21】](https://www.bilibili.com/video/BV1wjQvY6Enm/?t=201)

### 6.2 实测未必更快

这是全片最反直觉的一点：UP 主明确说，**推理时一般不会真的把两个矩阵乘成一个**。清华那篇 blog 的测试显示，直接做完吸收之后运算时间反而更长；真正带来收益的是**调整运算顺序、减少中间大矩阵的生成**。所以吸收版代码里仍然保留了 `out_absorb` 和 `o_proj` 两次乘法。[【跳转到 07:51】](https://www.bilibili.com/video/BV1wjQvY6Enm/?t=471)

换句话说，「矩阵吸收」这个名字容易让人以为收益来自「少算一次矩阵乘法」，实际上收益来自「中间张量从 $O(L \cdot H \cdot D)$ 变成 $O(H \cdot Q \cdot C)$」。

### 6.3 RoPE 挡住了 key 侧的一部分

key 的吸收只对 **nope 分支**成立。位置编码是在升维之后才作用到 key 上的，而 RoPE 是**位置相关**的变换——不同位置的旋转角度不同，没法提前折进一个固定矩阵里。所以 MLA 干脆把位置信息拆到一条独立的 64 维共享分支（解耦 RoPE），让它保持单头、不参与吸收；吸收只处理剩下那条能折进 $W^{UQ}$ 的 nope 分支。这也正是吸收版代码里分数要分两段算、再相加的原因。[【跳转到 16:46】](https://www.bilibili.com/video/BV1wjQvY6Enm/?t=1006)

### 6.4 它把 MHA 变成了 MQA

UP 主在视频后半段点出吸收的一个副产品：吸收之后，key 侧的隐向量是**单头共享**的，query 侧才是多头。这正好就是 MQA（多查询注意力）的形状——所有 query 头共享同一组 K/V。所以矩阵吸收不只是省了显存，它还把 MLA 的 decode 计算**从 MHA 形态改写成了 MQA 形态**，可以复用现成的 MQA 优化路径（包括 FlashMLA 这类融合算子）。[【跳转到 09:50】](https://www.bilibili.com/video/BV1wjQvY6Enm/?t=590)

## 小结

- MLA 的缓存有两种实现：**CD（存解压后的完整 KV）** 计算最省但没省空间，**CC（只存 $c_t^{KV}$）** 省空间但每次 decode 都要升维。矩阵吸收要的是「既省空间又不升维」。
- **key 的吸收**：$(W^{UQ}c^{Q})^\top W^{UK}c^{KV} = (c^{Q\top}W^{UQ\top}W^{UK})c^{KV}$，把 $W^{UK}$ 折进 query 侧，点积直接在隐向量上做。
- **value 的吸收**：$A(W^{UV}C^{KV})W^{O} = A\,C^{KV}(W^{UV}W^{O})$，中间张量从 $(b,l,h,d)$ 缩成 $(b,h,q,c)$。
- **move elision**：注意力分数对 rope / nope 两段可加，不必先 `concat`，省掉两块中间显存和两次搬运。
- 代码上就是把 `kv_up_proj.weight` 拆成 `q_absorb` 与 `out_absorb`，其余是形状对齐工作。
- 代价有三条：需要足够精度、实测「真合并」未必更快（收益来自顺序而非合并）、RoPE 分支吸收不了只能分两段算。
- 副产品：吸收后 key 侧单头共享，MLA 的 decode 计算形态变成了 MQA。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| 矩阵吸收（matrix absorption） | 用乘法结合律把升维矩阵折进另一个固定权重，使推理时不必显式解压隐向量 |
| CD（CacheDecompressed） | 缓存升维后的完整 K/V，官方原始实现采用，计算最省但不省空间 |
| CC（Cache Compressed） | 只缓存 $c_t^{KV}$，省空间但每次 decode 都要重新升维 |
| $W^{UK}$ / $W^{UV}$ | KV 的上投影矩阵，被拆成两段分别吸收进 query 侧与输出侧 |
| `q_absorb` / `out_absorb` | 代码里对 $W^{UK}$、$W^{UV}$ 两段的命名 |
| move elision | 不拼接 rope 与 nope，分数分两段算再相加，省掉中间显存与搬运 |
| MQA 形态 | 吸收后 key 侧单头共享、query 侧多头，形状与 MQA 一致 |
| 中间张量 | 括号位置决定的临时结果，其形状（而非乘法次数）才是吸收的收益来源 |