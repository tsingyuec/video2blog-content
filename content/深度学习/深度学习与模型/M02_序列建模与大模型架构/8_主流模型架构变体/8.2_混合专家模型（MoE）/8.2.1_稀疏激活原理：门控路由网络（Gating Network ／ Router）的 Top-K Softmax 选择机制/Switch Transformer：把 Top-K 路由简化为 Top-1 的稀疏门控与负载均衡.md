# Switch Transformer：把 Top-K 路由简化成 Top-1 的稀疏门控与负载均衡

> 视频来源：[Switch Transformer 经典论文解读！](https://www.bilibili.com/video/BV1UsPceJEEQ/)（Bilibili · ZOMI酱）｜时长约 21 分钟
> 导读：ZOMI 逐节读 Switch Transformer 原文，重点落在第 2 章「简化稀疏路由」。视频把论文里的四个公式（门控 softmax、加权求和、专家容量、辅助损失）逐个拆开讲，并配了 encoder block 图、容量因子示意图和 Table 1 的实验数据。本文按「原始 top-k 路由 → 改成 top-1 → 容量因子 → 辅助损失 → 训练稳定性」整理；粗粒度/细粒度专家的架构对比不在本文范围。字幕中的口误（`MV`/`MO1` 指 MoE、`switch 传送门` 指 Switch Transformer、`小夏 SASHA` 指 Noam Shazeer）已按上下文订正。

## 本讲要解决的核心问题（SCQA）

**背景**：MoE 的思路很诱人——只激活一部分专家，就能把模型参数量做大，而每个 token 的浮点运算量（FLOPs）保持不变。2017 年 Shazeer 那篇论文已经给出了完整的 top-k 路由方案：门控网络给 $N$ 个专家打分，取分数最高的 $k$ 个，按分数加权求和。

**冲突**：这套方案一直没能真正跑起来。原因有两个：路由本身带来额外的计算和通信开销；更麻烦的是训练不稳定。而当时的直觉还认为，$k$ 必须大于 1——「学习路由需要至少能比较两个专家，否则门控函数拿不到非平凡的梯度」。

**疑问**：能不能把 $k$ 直接压到 1，让每个 token 只走一个专家？如果这样做，路由的计算、通信、显存怎么安排？专家被挤爆或者被闲置又怎么办？

**回答（中心思想）**：Switch Transformer 把 top-k 路由简化成 **top-1**（论文称之为 Switch layer），并用两个配套机制兜住副作用：**专家容量（capacity factor）** 处理「某个专家被塞爆」，**可微的辅助负载均衡损失** 处理「专家使用不均」。三者合起来，让模型在每 token FLOPs 不变的前提下把参数量推到 1.6T。[【跳转到 20:37】](https://www.bilibili.com/video/BV1UsPceJEEQ/?t=1237)

---

## 一、先看原始 MoE 路由长什么样

### 1.1 门控：一个线性层加 softmax

论文 2.1 节先把 2017 年的方案复述了一遍 [【跳转到 10:08】](https://www.bilibili.com/video/BV1UsPceJEEQ/?t=608)。设输入 token 表示为 $x$，路由变量（router variable）是矩阵 $W_r$，它先算出 $N$ 个专家的 logits：

$$
h(x) = W_r \cdot x
$$

再在 $N$ 个专家上做 softmax，得到第 $i$ 个专家的门控值：

$$
p_i(x) = \frac{e^{h(x)_i}}{\sum_{j=1}^{N} e^{h(x)_j}}
$$

![论文 2.1 节原文：路由矩阵 W_r 产生 logits，经 softmax 得到门控值 p_i(x)，公式 (1)](assets/Switch%20Transformer：把%20Top-K%20路由简化为%20Top-1%20的稀疏门控与负载均衡/00608.webp)

### 1.2 输出：只在选中的 k 个专家上加权

取门控值最高的 $k$ 个专家，记下标集合为 $\mathcal{T}$，这一层的输出是各专家输出的线性加权：

$$
y = \sum_{i \in \mathcal{T}} p_i(x)\, E_i(x)
$$

其中 $E_i(x)$ 是第 $i$ 个专家（一个 FFN）对 $x$ 的计算结果。视频特意点了一句：**正是公式 (2) 里的门控值 $p_i(x)$ 让路由变得可微**——梯度可以穿过权重回到 $W_r$ [【跳转到 11:00】](https://www.bilibili.com/video/BV1UsPceJEEQ/?t=660)。

### 1.3 为什么原来非要 k > 1

Shazeer 等人当年的猜想是：$k>1$ 是拿到非平凡梯度的必要条件，因为「不会比较至少两个专家，就学不会路由」。后续工作（Ramachandran and Le）还进一步研究了 top-k 的取值，发现模型**中低层**用较大的 $k$ 对多层路由的模型更有帮助 [【跳转到 11:36】](https://www.bilibili.com/video/BV1UsPceJEEQ/?t=696)。

所以「$k=1$」在当年是个反直觉的选择——这正是 Switch Transformer 的贡献所在。

---

## 二、Switch layer：只路由到一个专家

### 2.1 反其道而行之

论文的原话是：与这些想法相反，我们用一个简化策略，**只把一个 token 路由到单个专家**，并证明这种简化保持了模型质量、减少了路由计算、表现更好。这个 $k=1$ 的路由策略后来被称为 **Switch layer** [【跳转到 11:41】](https://www.bilibili.com/video/BV1UsPceJEEQ/?t=701)。

![论文原文高亮：只路由到单个专家（route to only a single expert），这个 k=1 的策略被称为 Switch layer，并列出三个好处](assets/Switch%20Transformer：把%20Top-K%20路由简化为%20Top-1%20的稀疏门控与负载均衡/00701.webp)

### 2.2 三个好处

论文列了三条 [【跳转到 12:14】](https://www.bilibili.com/video/BV1UsPceJEEQ/?t=734)：

1. **路由计算减少**：每个 token 只路由到一个专家，门控只用来选一个下标，不用再排序取 top-k。
2. **每个专家的 batch 至少减半**：原来一个 token 要进至少两个专家，现在只进一个，单个专家要处理的 token 数直接减半，专家容量也可以跟着减半。
3. **路由实现简化、通信成本降低**：跨设备的 token 交换量变小，实现也更简单。

### 2.3 结构上改的是 FFN，不是注意力

Switch Transformer 的 encoder block 是把标准 Transformer 里的**稠密 FFN 换成稀疏的 Switch FFN**，其余部分（self-attention、add & norm、残差）都不动 [【跳转到 08:38】](https://www.bilibili.com/video/BV1UsPceJEEQ/?t=518)。

![论文 Figure 2：Switch Transformer encoder block。左侧是整体结构，右侧展开 Switch FFN 层——两个 token（More、Parameters）各自经过 router，被路由到 4 个 FFN 专家中的某一个，输出再乘以门控概率 p（图中 p=0.65 与 p=0.8）](assets/Switch%20Transformer：把%20Top-K%20路由简化为%20Top-1%20的稀疏门控与负载均衡/00518.webp)

放大看这个 Switch FFN 层：token 先过 self-attention 和 add & norm，进入 FFN 层后由 router 打分，只激活一个专家，把该专家的输出乘以概率 $p$ 后输出。**每个 token 独立过一次路由**，token 之间互不影响 [【跳转到 09:25】](https://www.bilibili.com/video/BV1UsPceJEEQ/?t=565)。

![Switch FFN 层内部：Router 输出概率分布，只点亮一个专家（图中 FFN2，p=0.65），输出乘 p 后回传](assets/Switch%20Transformer：把%20Top-K%20路由简化为%20Top-1%20的稀疏门控与负载均衡/00565.webp)

### 2.4 为什么放在 FFN 而不是注意力

论文其实试过两个位置：把 switch layer 放在 FFN 层，以及放在 attention 层。后者的效果没有明显提升，反而增加了计算复杂度，所以最终选择放在 FFN 层——这就是「Switch FFN」的由来 [【跳转到 20:00】](https://www.bilibili.com/video/BV1UsPceJEEQ/?t=1200)。

---

## 三、容量因子：静态显存与动态路由的矛盾

### 3.1 矛盾在哪

工程实现上有个硬约束：所有张量的形状在**编译时静态确定**（论文用的是 TensorFlow + 谷歌 TPU），但**路由决策在训练和推理时是动态的**——哪个 token 去哪个专家，事先不知道 [【跳转到 14:20】](https://www.bilibili.com/video/BV1UsPceJEEQ/?t=860)。

如果某个专家被塞了一堆 token，另一个专家一个都没有，静态形状就没法分配。解决办法是给每个专家预先划一块固定大小的缓冲区，也就是**专家容量（expert capacity）**：

$$
\text{expert capacity} = \frac{\text{tokens per batch}}{\text{num experts}} \times \text{capacity factor}
$$

也就是「一个 batch 的 token 数 ÷ 专家数 × 容量因子」[【跳转到 14:45】](https://www.bilibili.com/video/BV1UsPceJEEQ/?t=885)。

### 3.2 超容量了怎么办

容量因子大于 1 时，会额外创建缓冲区（additional buffer），用来吸收专家之间分配不均的 token。

如果某个专家的 token 数还是超过了容量上限，就**发生溢出**：这部分 token 不被这个专家处理，而是跳过这一层（视频里的说法是「作为残差传给下一层」）[【跳转到 13:09】](https://www.bilibili.com/video/BV1UsPceJEEQ/?t=789)。

![论文 Figure 3：容量因子 1.0 与 1.5 的对比。每个专家只处理固定 batch size 的 token；容量因子 1.0 时（左）有 token 溢出（红色虚线），1.5 时（右）缓冲区变大、溢出减少，但计算与跨设备通信成本上升](assets/Switch%20Transformer：把%20Top-K%20路由简化为%20Top-1%20的稀疏门控与负载均衡/00764.webp)

这张图把权衡画得很清楚：**容量因子调大，溢出变少、质量更稳，但计算和通信成本上升**；调小则相反。

### 3.3 实验：容量因子取多少合适

论文 Table 1 对比了容量因子 1.0、1.25、2.0 下 MoE 与 Switch 的表现 [【跳转到 17:06】](https://www.bilibili.com/video/BV1UsPceJEEQ/?t=1026)：

![论文 Table 1：容量因子从 2.0 降到 1.0，质量（Neg. Log Perp.）几乎没有变差，但速度（examples/sec）明显提升；Switch-Base 在容量因子 1.0 时达到 1000 examples/sec](assets/Switch%20Transformer：把%20Top-K%20路由简化为%20Top-1%20的稀疏门控与负载均衡/01031.webp)

结论是：容量因子从 1 加到 1.25、2.0，模型效果并没有好很多，但会明显影响速度。所以**容量因子取 1 是比较综合的选择**——效果和性能都不错 [【跳转到 17:11】](https://www.bilibili.com/video/BV1UsPceJEEQ/?t=1031)。

---

## 四、负载均衡：一个可微的辅助损失

### 4.1 为什么需要它

容量因子只是「事后补救」：溢出就丢掉。真正的问题是**为什么会有专家被塞爆**——因为门控会偏心，越用越顺手，最后少数专家吃掉大部分 token。这就是专家坍缩。

要治它，得让门控在训练时就被推向均衡。但负载均衡的度量（比如「每个专家分到多少 token」）往往不可微，没法直接加进 loss。论文的做法是设计一个**可微的辅助损失**（auxiliary loss）[【跳转到 15:33】](https://www.bilibili.com/video/BV1UsPceJEEQ/?t=933)。

### 4.2 公式拆解

$$
\text{loss} = \alpha \cdot N \cdot \sum_{i=1}^{N} f_i \cdot P_i
$$

其中：

- $\alpha$ 是超参，控制这个辅助损失在总损失里的权重；
- $N$ 是专家数量；
- $f_i$ 是**被派发到第 $i$ 个专家的 token 比例**：

$$
f_i = \frac{1}{T}\sum_{x\in\mathcal{B}} \mathbb{1}\{\arg\max p(x) = i\}
$$

- $P_i$ 是**整个 batch 里所有 token 分给第 $i$ 个专家的概率之和**（也就是门控给它的平均分数）：

$$
P_i = \frac{1}{T}\sum_{x\in\mathcal{B}} p_i(x)
$$

![论文公式 (4)(5)(6)：辅助损失 loss = α·N·Σ f_i·P_i，f_i 是被分配到第 i 个专家的 token 比例，P_i 是整个 batch 分给第 i 个专家的概率总和](assets/Switch%20Transformer：把%20Top-K%20路由简化为%20Top-1%20的稀疏门控与负载均衡/00958.webp)

### 4.3 为什么这样写就均衡了

关键在于 $f_i$ 和 $P_i$ 的组合。$f_i$ 是**硬分配**（不可微，来自 argmax），$P_i$ 是**软概率**（可微）。两者相乘再求和，梯度只能通过 $P_i$ 回传——于是优化这个损失，等价于把「门控给出的平均概率」往「实际分配比例」上拉，理想状态是两边都等于 $1/N$。

论文的说法是：我们希望这两个向量都取 $1/N$。乘上 $N$ 是为了让数值回到 1 的量级，视频里的解释是「加快计算的效果」[【跳转到 16:36】](https://www.bilibili.com/video/BV1UsPceJEEQ/?t=996)。

---

## 五、把稀疏模型训练起来：稳定性与蒸馏

### 5.1 第四根缩放轴：参数量与计算量解耦

论文在引言里提的贡献是「第四个维度」：**增加参数量的同时保持每个样本的浮点运算量不变**。这句话背后的假设是：参数量与总计算量可以解耦，各自是独立的缩放因子 [【跳转到 07:38】](https://www.bilibili.com/video/BV1UsPceJEEQ/?t=458)。

于是就有了这条路线：MoE 是稀疏结构，不是所有专家同时激活，所以总计算量可以和稠密模型持平，但参数量做大之后效果仍然提升。这也是很多厂商坚持走 MoE 路线的原因 [【跳转到 08:28】](https://www.bilibili.com/video/BV1UsPceJEEQ/?t=508)。

### 5.2 训练稳定性：bf16、小初始化、dropout

稀疏模型比稠密模型更难训，论文给了几条工程手段 [【跳转到 17:36】](https://www.bilibili.com/video/BV1UsPceJEEQ/?t=1056)：

- **bf16 混合精度**：这是第一次用 bf16 训练 MoE 大模型，这个格式后来成了 A100/H100 的标准。
- **更小的初始化**：一开始给一个比较小的初始化超参，而不是随机的超参值，用来稳定训练。
- **专家内的 dropout**：稀疏模型需要额外正则化，加 dropout 能让效果更好。

### 5.3 蒸馏回稠密模型

Switch Transformer 还能把训练好的稀疏模型蒸馏成一个稠密模型，方便部署。视频提到论文里的做法：用大模型当老师，配合 75% 的 ground truth 标签来蒸馏，能带来约 30% 的提升 [【跳转到 18:32】](https://www.bilibili.com/video/BV1UsPceJEEQ/?t=1112)。

### 5.4 最终形态

论文在 2021 年 1 月发表（视频开头的口播说成 2022 年，总结页写的是 2021 年 1 月），在 T5（encoder-decoder）的基础上简化路由策略，实现了 1.6T 参数的 Switch Transformer [【跳转到 20:37】](https://www.bilibili.com/video/BV1UsPceJEEQ/?t=1237)。

![总结页：Switch Transformer 的核心特点是简化 MoE 路由、仅选择单个专家激活；通过稀疏门控机制与专家容量限制优化计算效率和负载均衡，实现万亿参数级模型扩展](assets/Switch%20Transformer：把%20Top-K%20路由简化为%20Top-1%20的稀疏门控与负载均衡/01237.webp)

---

## 小结

- **原始 MoE 路由**：$h(x)=W_r x$ 出 logits，softmax 得门控值 $p_i(x)$，取 top-k 后加权求和 $y=\sum_{i\in\mathcal{T}}p_i(x)E_i(x)$；$p_i(x)$ 是路由可微的来源。
- **Switch 的简化**：把 $k$ 压到 1，每个 token 只走一个专家，路由计算、专家 batch、通信成本三样一起降。
- **容量因子**：$\text{capacity}=(\text{tokens per batch}/\text{num experts})\times\text{factor}$，解决静态形状与动态路由的矛盾；超出容量的 token 跳过该层。实验显示 factor 取 1 性价比最高。
- **辅助损失**：$\text{loss}=\alpha N\sum_i f_i P_i$，用可微的 $P_i$ 去拉不可微的 $f_i$，目标是两边都等于 $1/N$。
- **训练稳定性**：bf16、小初始化、专家内 dropout 是标配；稀疏模型还能蒸馏回稠密模型。
- **位置选择**：switch layer 放在 FFN 有效，放在 attention 收益不明显。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| 路由变量 $W_r$ | 门控网络的权重矩阵，把 token 向量映射成 $N$ 个专家的 logits |
| 门控值 $p_i(x)$ | 第 $i$ 个专家的 softmax 权重，也是让路由可微的乘子 |
| Switch layer | $k=1$ 的稀疏路由层，每个 token 只送进一个专家 |
| 专家容量（expert capacity） | 每个专家能处理的 token 上限，由 batch 大小、专家数和容量因子共同决定 |
| 容量因子（capacity factor） | 容量的放大系数，大于 1 时留出缓冲减少溢出，代价是算力与通信 |
| 溢出（overflow） | 专家收到的 token 超过容量，超出的 token 不被该层处理 |
| 辅助损失（auxiliary loss） | 加在门控分布上的可微损失，惩罚专家使用不均衡 |
| $f_i$ | 实际被派发到第 $i$ 个专家的 token 比例（硬分配，不可微） |
| $P_i$ | 门控给第 $i$ 个专家的平均概率（软概率，可微） |
| 蒸馏（distillation） | 用稀疏的大模型当老师，把能力迁移到一个稠密的小模型上 |