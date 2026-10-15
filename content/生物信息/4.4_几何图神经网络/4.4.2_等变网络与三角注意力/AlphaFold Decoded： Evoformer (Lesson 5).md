# AlphaFold Decoded： Evoformer (Lesson 5)

> 来源：[AlphaFold Decoded: Evoformer (Lesson 5)（YouTube，Kilian Mandon）](https://www.youtube.com/watch?v=gY4-vVRTkpk)，时长 24:21，"从零实现 AlphaFold" 系列第 5 讲。本博客基于「图-字幕」视频演说图文稿整理，内容可回视频核查。
>
> 编注：本讲是"三角注意力（triangle attention）"的出处讲解——AlphaFold2 Evoformer 的 pair 栈首次提出三角乘法更新与三角注意力；后续 AlphaFold3 / Protenix 的 Pairformer 延续了这一思路（见本系列 4.3.3、5.1.1 条目）。

## 本讲要解决的核心问题（SCQA）

**背景**：AlphaFold2 用注意力机制从 MSA 与模板特征预测蛋白质结构；序列已由注意力处理过， pair（残基对）表示则承载"哪两个残基相互作用"的信息。

**冲突**：pair 表示的条目数是残基数的平方——400 个残基就是 160,000 个条目，比 GPT-4 的 8,000 token 上下文还大 20 倍；对它做全注意力，仅一个注意力模块就需要约 102 GB 显存，根本不可行。

**疑问**：如何在这么大的张量上做注意力，还能保证残基对之间的距离信息不互相矛盾（不违反三角不等式）？

**回答（中心思想）**：Evoformer 的答案是「行/列注意力 + 三角机制」：注意力只在行或列上做（内存从平方降到可承受），并把 pair 表示自身当作注意力偏置——更新残基对 ij 时必须同时看 ik 与 jk，"补全三角形"的第三条边；整块结构堆叠 48 次，最后取 MSA 表示的第一行作为 single 表示交给结构模块。

---

## 一、Evoformer：AlphaFold2 的"主引擎"

[【跳转到 00:38】](https://www.youtube.com/watch?v=gY4-vVRTkpk&t=38)

在全模型约 93M 参数中，Evoformer 一个组件就占了 88M——它是模型里最大的组件。一个有力的旁证：从 Evoformer 末层的注意力图（热图显示哪些残基被用于注意力更新）看，注意力模式与模型最终预测里的**残基对距离**惊人地相似——说明 Evoformer 已经对蛋白结构有了扎实的把握，随后的结构模块只是把这种"理解"翻译成具体的原子坐标。

![Evoformer 介绍：88M/93M 参数，末层注意力模式 ≈ 最终预测的残基对距离](assets/AlphaFold Decoded： Evoformer %28Lesson 5%29/00038.webp)

### 1.1 两种表示：pair 与 MSA

[【跳转到 2:17】](https://www.youtube.com/watch?v=gY4-vVRTkpk&t=137)

特征嵌入之后得到两种表示：

- **pair 表示**：形状 `R×R×Cz`（R 为残基数，Cz 为嵌入维度），每个条目 z_ij 编码一对残基的关系；
- **MSA 表示**：形状 `S×R×Cm`（S 为输入嵌入时选出的聚类中心序列数，Cm 为嵌入维度）。

顺带速览输入嵌入的几个部件（下一讲细讲）：线性层不新鲜；outer sum 就是把外积的乘法换成加法；rel-pos 是 AlphaFold 处理位置编码的方式——不直接把残基下标换成可学习向量，而是对每对残基取下标之差再查可学习向量；target feat 的 tiling 就是广播到更大形状；pair/MSA 表示旁的两个 R 是**回收嵌入器（recycling embedder）**的位置——AlphaFold 会把整个架构跑多轮，用上一轮输出更新 pair 与 MSA 表示。

## 二、为什么不能做全注意力：行/列注意力

[【跳转到 2:54】](https://www.youtube.com/watch?v=gY4-vVRTkpk&t=174)

Evoformer 由多个结构相同的块堆叠而成，每块同时加工 MSA 表示与 pair 表示，分成上行的 **MSA 栈**与下行的 **pair 栈**，两条信息通道在块间相连。核心矛盾是：想对输入做注意力，但张量太大——

- 400 残基 → pair 表示 160,000 条目，做全注意力的序列长度不可理喻（对比 GPT-4 的 8k 上下文）；
- 注意力内存需求是平方级的：全注意力仅一个模块就要 102 GB 显存；
- 改用**行注意力或列注意力**后，注意力分数只需 400² 个浮点数、总计 400³ 量级——单模块约 256 MB，完全可行。

![Evoformer 块结构：MSA 栈（上）+ pair 栈（下），两条信息通道互通](assets/AlphaFold Decoded： Evoformer %28Lesson 5%29/00174.webp)

![MSA 栈与 pair 栈的完整流程图：行/列注意力、外积均值、三角更新与三角注意力](assets/AlphaFold Decoded： Evoformer %28Lesson 5%29/00248.webp)

## 三、MSA 栈三模块

### 3.1 行注意力：把 pair 表示当偏置（先回顾 gated attention）

[【跳转到 5:43】](https://www.youtube.com/watch?v=gY4-vVRTkpk&t=343)

带门控与偏置的自注意力：对输入序列算四个线性嵌入——key、query、value 与 **gate**；每个 query 与每个 key 做缩放点积、加偏置，softmax 归一化注意力权重；对每个 query 按权重加权 value 得到中间输出；再乘以经 sigmoid 归一到 0–1 的门控嵌入，过线性层得到最终输出。记号约定：线性层从 Ci 到 HC 表示先升维到 H×C 再 reshape。

MSA 栈里的行注意力，输入就是表示的一行；偏置来自 pair 表示——两者形状几乎匹配，只需一个线性嵌入把通道维变到注意力头维度。之所以偏置看起来比 pair 表示"维度更多"，只是可视化用了堆叠热图表示不同的头：pair 表示里每个色块是一个向量，而偏置、点积亲和度与注意力权重里每个色块只是单个数值——两者其实都是三维张量。

### 3.2 伪代码与实现：偏置怎么加、注意力沿哪一维

[【跳转到 6:58】](https://www.youtube.com/watch?v=gY4-vVRTkpk&t=418)

以论文补充材料里 "row-wise gated self-attention with pair bias" 的伪代码为准：先对 MSA 表示 M 做 LayerNorm；第 2、4 行生成 query/key/value 与 gate 嵌入；第 3 行把 pair 表示经 LayerNorm + 线性层变成偏置（通道维 → 头数维）。注意 **b 是唯一不加粗的字母**——偏置的条目是单个数值，其他符号都是向量。第 5、6 行是行注意力的数学形式：行下标 s 在 query/key、门控、注意力分数与 value 里原样携带；注意力发生在**列下标**上——query 的 i 下标与 key 的 j 下标逐元素（entry-wise）相乘，softmax 也沿这一维归一化。第 7 行把各头的输出拼接后过输出线性层。

实际 Python 实现更简单：把 M 和 B 传给初始化时已指定注意力维度的多头注意力模块即可。行注意力要把**列维度**指定为注意力维度（被循环遍历的那一维），就像矩阵按行求和时求和发生在列维度上。列注意力函数与行注意力几乎一样，这次甚至**不用准备偏置**：列下标 i 保持不动，key 与 query 的逐元素乘法沿行维（s、t）进行。讲者指出第 5 行是全系列唯一与论文伪代码不同之处：论文排版时 V 与 95 的下标印成了 st 而不是 ti，他认为是笔误并按自己的写法实现（欢迎观众指正）。

![行注意力伪代码：pair 表示经 LayerNorm+线性层变成偏置 b](assets/AlphaFold Decoded： Evoformer %28Lesson 5%29/00418.webp)

### 3.3 MSA transition：两层前馈网络

[【跳转到 10:03】](https://www.youtube.com/watch?v=gY4-vVRTkpk&t=603)

MSA 栈的最后一部分是 transition：开头 LayerNorm 的两层前馈网络，中间升维 4 倍再降回来——Transformer 网络里典型的前馈块，4 是惯例的缩放因子。

## 四、outer product mean：MSA → pair 的信息通道

[【跳转到 10:38】](https://www.youtube.com/watch?v=gY4-vVRTkpk&t=638)

MSA 栈与 pair 栈靠 **outer product mean** 连接，它把 MSA 表示重塑成 pair 表示的形状。两个要点：

1. 外积不是 M 与自身算，而是 M 的两个线性嵌入 A 与 B 之间算——给模型留出赋予外积含义的灵活性；
2. 实际算了**两次外积**：第一次来自 A、B 的索引方式（A 的列下标 i、B 的列下标 j），张量逐元素计算，得到想要的形状；第二次沿通道维（向量间的叉乘记号），把通道两两相乘扩展到 C×C。展平后沿序列维取均值收缩，再用线性层把 C×C 降回 Cz。

Python 实现用 einsum 表达式：行维收缩，列维与通道维广播。但实现与伪代码有一个真实差异：einsum 只是沿行维求和，而伪代码要求取均值——除以序列数发生在**线性层之后**而不是之前。区别不大，按伪代码训练模型大概率也没问题；但由于我们**不训练**模型，必须严格按真实实现来，预训练权重才能直接用。

![outer product mean：两次外积 + 均值收缩 + 线性层降维](assets/AlphaFold Decoded： Evoformer %28Lesson 5%29/00638.webp)

## 五、三角机制：为什么要"补全三角形"

### 5.1 两种表示各编码什么

[【跳转到 12:55】](https://www.youtube.com/watch?v=gY4-vVRTkpk&t=775)

pair 栈的模块大多以 triangle 开头。理解三角机制前，先想清楚两种表示各编码什么。MSA 表示很直观：一个维度是不同物种（来源生物），另一个维度是残基位置；行向操作让位置之间互相"串门"，但每个物种内部独立；列向操作看同一位置跨物种的信息——这种信息流对结构预测的价值一目了然。

### 5.2 pair 条目 = 有向的残基对相互作用

[【跳转到 13:53】](https://www.youtube.com/watch?v=gY4-vVRTkpk&t=833)

pair 表示里，每个残基对其实有**两个条目**：ij 与 ji。可以设想 ij 携带"从 i 到 j"的信息，ji 携带"从 j 到 i"的信号——比如谷氨酸告诉旁边的甘氨酸"我带负电"，甘氨酸回话"我是中性的，无所谓"。当然这只是理论化的解释：条目的实际取值是学出来的特征，语义并不是预先定义的。但 AlphaFold 大获成功，认真对待其架构背后的理论是值得的。

![pair 表示的两个条目：ij 与 ji 承载有向的残基对相互作用](assets/AlphaFold Decoded： Evoformer %28Lesson 5%29/00968.webp)

### 5.3 outgoing / incoming 更新与三角不等式

[【跳转到 14:48】](https://www.youtube.com/watch?v=gY4-vVRTkpk&t=888)

在这套解释下看"更新"：用 ik 更新 ij，叫 **outgoing 更新**（around the starting node，起始节点周围），第一个下标 i 固定，对应**行向操作**（行注意力、行乘法更新）。AlphaFold 作者认为：此时模型必须拿到 j 与 k 之间相互作用的信息来**补全三角形**——如果条目携带的是距离信息，就必须把 jk 的距离也纳入考虑，否则可能违反三维结构（比如违反距离上的三角不等式）。jk 与 kj 的选择有点随意，但在更新 ij 的语境下，按 outgoing 边的精神选 jk。

incoming 边（around the ending node，结束节点周围）完全对称：用 kj 更新 ji，列下标固定，对应**列向操作**；同样建议把 ki 纳入算式补全最后一条入边。为什么必须补全？想象更新 ij 时只看 ik 就把 i、j 间距离改得特别长，而 jk、ik 没更新——一个三角形一条边太长、另两条太短，**三角不等式**（任何一边不得超过另两边之和）被破坏，三维结构就矛盾了。所以更新 ij 时要同时注意 ik 与 jk 两条边；同时还有许多不同的 k，更新 ij 时要把它们构成的三角形都照顾到。

翻译回注意力语言：query 关注 key 并按 value 更新，依此类推——但并不完全如此：由于 ij 无法做到真正对称，只能"打个补丁"，让 i、j 在每个注意力模块里不被同等对待——这就是为什么有**两个**三角注意力：一个处理 ij，另一个处理 ji。

回到 pair 栈流程：第一、三个模块用 outgoing 边（around the starting node，行向），其余三角更新用 incoming 边（around the ending node，列向）。

## 六、pair 栈四模块

### 6.1 三角乘法更新（outgoing 与 incoming）

[【跳转到 16:23】](https://www.youtube.com/watch?v=gY4-vVRTkpk&t=983)

乘法更新先从 pair 表示创建两个嵌入 A、B（线性嵌入 × 线性-sigmoid 门控嵌入），模块还创建输出门 g 乘在层输出上。关键操作在第 4 行——位置之间真正的 cross-talk：以 outgoing 为例，要用来自不同 k 的出边 ik 更新条目 ij，同时按三角注意力的思路把 jk 也纳入——做法是**向量 A_ik 与 B_jk 逐元素相乘后求和**，随后 LayerNorm、线性层、乘门控。incoming 更新基本相同（黄色高亮为差异）：为更新 ji 看 kj，并补全三角形考虑 ki——具体是**两列逐元素相乘再沿行维求和**。两个算法并排看差异：outgoing 操作的是两行（A_ik、B_jk），incoming 操作的是两列（A_ki、B_kj）。

![三角乘法更新（incoming）：两列逐元素相乘、求和、LayerNorm、线性、门控](assets/AlphaFold Decoded： Evoformer %28Lesson 5%29/01033.webp)

### 6.2 三角注意力：pair 表示自己当偏置

[【跳转到 17:58】](https://www.youtube.com/watch?v=gY4-vVRTkpk&t=1078)

乘法更新之后是 around the starting node 与 around the ending node 的注意力——即再次使用出边与入边。around the starting node 就是**行注意力，偏置用 pair 表示本身**：第 3 行沿用之前的技巧把通道维变成头数维。偏置的用法与"补全三角形"的理论完全吻合：条目 ij 的更新对应一个 query，它可以被所有从 i 出发的 key（k_ik）更新，而 key ik 对应的注意力分数受偏置 **b_jk** 影响——b_jk 正是三角形的第三条边。

around the ending node 基本一样（黄色高亮为差异）：这次是**列注意力**，仍用 pair 表示当偏置，但偏置要**转置**。从第 5 行的下标可见：列下标 j 对 Q、K 固定（符合列注意力），注意力分数下标顺序是 ik，而 B 的索引是 ki——在 PyTorch 里要先转置再相加。与前一算法相同，更新 ij 时来自 kj 的更新受第三条边 ki（经偏置）影响。

![三角注意力 around the ending node：列注意力 + 转置后的 pair 偏置](assets/AlphaFold Decoded： Evoformer %28Lesson 5%29/01128.webp)

### 6.3 pair transition

[【跳转到 19:43】](https://www.youtube.com/watch?v=gY4-vVRTkpk&t=1183)

pair 栈的最后一部分 pair transition 又是一个两层前馈模块，与 MSA 表示处完全一样。

## 七、工程细节与收尾

### 7.1 完整代码与 48 个块

[【跳转到 20:08】](https://www.youtube.com/watch?v=gY4-vVRTkpk&t=1208)

把全部模块拼起来就是 Evoformer 的完整代码，黄色标注的本讲方法按流程图顺序调用：MSA 行注意力（带 pair 偏置）→ MSA 列注意力 → MSA transition → outer product mean（进入 pair 栈）→ outgoing 三角乘法 → incoming 三角乘法 → around the starting node 注意力 → around the ending node 注意力 → pair transition。除这些子方法外还有几个实现细节：

- Evoformer 由多个相同的块组成——确切地说是 **48 个**，每个块有自己独立的权重；
- 行/列 dropout 可以放心忽略：dropout 是训练期正则化（随机置零一些值并放大其余值以保持期望），AlphaFold 把表示的整行或整列置零，但推理时不施加。

![Evoformer 完整代码：按流程图顺序调用各模块，48 个独立权重块](assets/AlphaFold Decoded： Evoformer %28Lesson 5%29/01208.webp)

### 7.2 残差连接：训练稳定的关键

[【跳转到 21:23】](https://www.youtube.com/watch?v=gY4-vVRTkpk&t=1283)

一个大细节：输出不是**替换**操作结果，而是把操作结果**加到输入上**——即注意力篇讲过的**残差连接**。想想乘法更新这种操作：从大张量里取两行、逐元素相乘、求和生成输出——没有残差连接的话这是相当"颠覆性"的变换；有了残差连接，模型可以只学很小的嵌入权重、生成接近零的输出——更像对输入的偏移而不是彻底替换，训练因此稳定得多。

### 7.3 single representation：MSA 第一行留下来

[【跳转到 21:48】](https://www.youtube.com/watch?v=gY4-vVRTkpk&t=1308)

最后，Evoformer 取 MSA 表示的**第一行**过线性层，得到所谓的 **single 表示**——这是 MSA 表示中唯一从 Evoformer 进入结构模块的部分，其余 MSA 表示被丢弃。这有点像注意力篇 notebook 里情感分析的实现：只保留第一个 token 的输出用于分类，模型需要学会把信息聚拢到这个位置。回想 MSA 特征的构造——第一行正来自目标序列，由它"存活"下去合情合理。

### 7.4 全架构回顾

[【跳转到 22:26】](https://www.youtube.com/watch?v=gY4-vVRTkpk&t=1346)

再快速过一遍完整架构：Evoformer 由若干相同的块组成，每块含 MSA 栈与 pair 栈及两条信息通道——MSA 栈三模块（带 pair 偏置的行注意力、列注意力、两层前馈 transition）；outer product mean 沿残基维取外积、沿序列维取均值，把 MSA 表示重塑成 pair 表示的形状并加到 pair 表示上（MSA → pair 的信息流）；pair 栈含两个乘法更新、两个注意力更新与一个 transition——乘法更新是两行或两列逐元素积的和，注意力更新是带 pair 偏置的行注意力与带（转置）pair 偏置的列注意力。

![全架构回顾图：MSA 栈 + outer product mean + pair 栈的完整数据流](assets/AlphaFold Decoded： Evoformer %28Lesson 5%29/01346.webp)

[【跳转到 23:34】](https://www.youtube.com/watch?v=gY4-vVRTkpk&t=1414)

与 Transformer 相比 Evoformer 更复杂一些，但单步并不难：张量太大就用行/列注意力；三角注意力看似聪明，其实本质上就是"把 pair 表示本身当偏置"，也许阴差阳错也能想到。视频简介里附了教程 notebook，可以自己完成 Evoformer 的完整实现（带自动校验）。下一讲将补上特征提取与 Evoformer 之间的空档——祝编码愉快。

![收尾：教程 notebook 与下一讲预告](assets/AlphaFold Decoded： Evoformer %28Lesson 5%29/01414.webp)

---

## 小结

- **体量**：Evoformer 占 AlphaFold2 全模型 93M 参数中的 88M，末层注意力图与残基对距离高度相似——结构信息已在 Evoformer 中成形。
- **两种表示**：pair 表示 `R×R×Cz` 编码残基对关系；MSA 表示 `S×R×Cm` 编码跨物种的残基位置信息。
- **行/列注意力**：pair 张量有 R² 条目（400 残基即 160k），全注意力内存爆炸（102 GB/模块）；行或列注意力把开销降到可承受（约 256 MB/模块）。
- **MSA 栈**：带 pair 偏置的行注意力（偏置=pair 表示过 LayerNorm+线性）→ 无偏置列注意力 → 两层 FFN transition（升维 4 倍）。
- **outer product mean**：MSA → pair 的唯一信息通道；两个线性嵌入之间做两次外积（残基维、通道维），序列维取均值（实现里取均值在线性层之后——与伪代码的细微差异必须遵守，预训练权重才可用）。
- **三角机制的理论根基**：pair 条目是**有向的**残基对相互作用（ij 与 ji）；更新 ij 时必须同时看 ik 与 jk，否则可能违反距离的**三角不等式**，破坏三维结构的一致性。
- **pair 栈**：三角乘法更新（outgoing 看两行 A_ik⊙B_jk 求和；incoming 看两列 A_ki⊙B_kj 求和）+ 三角注意力（around the starting node = 行注意力带 b_jk 偏置；around the ending node = 列注意力带转置偏置）+ pair transition。
- **工程要点**：48 个块各有独立权重；残差连接（加而不换）让训练稳定；推理时忽略 dropout；最终只取 MSA 第一行过线性层作为 single 表示进入结构模块。
- 三角注意力本质：**把 pair 表示自身当注意力偏置**——一句话即可概括其机制。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| Evoformer | AlphaFold2 主干网络：MSA 栈 + pair 栈双塔结构，48 块堆叠 |
| pair 表示 z_ij | R×R×Cz 张量，每条目编码一对残基的关系（可视为有向相互作用） |
| MSA 表示 | S×R×Cm 张量，一维是物种序列、一维是残基位置 |
| 行/列注意力 | 只沿行或列做的注意力，绕开 R² 条目的全注意力内存爆炸 |
| pair bias | 把 pair 表示经 LayerNorm+线性变成注意力偏置，注入残基对关系 |
| gated attention | 带 sigmoid 门控嵌入的自注意力：Q/K/V 外多一个 gate 嵌入 |
| outer product mean | MSA→pair 的信息通道：两个线性嵌入做外积，序列维取均值 |
| 三角乘法更新 | outgoing：A_ik⊙B_jk 沿 k 求和；incoming：A_ki⊙B_kj 求和——跨位置 cross-talk |
| 三角注意力 | 更新 ij 时注意力分数被第三边 b_jk（或 b_ki）调制，"补全三角形" |
| around the starting / ending node | 固定第一个/第二个下标的更新方向，分别对应行向/列向操作 |
| 三角不等式 | 任何一条边长不得超过另两边之和；三角机制用于避免违反它 |
| 残差连接 | 输出加到输入而非替换，训练更稳定；模型可学出近零输出当偏移 |
| recycling embedder | 回收嵌入器：把上一轮整个网络的输出回填进 pair/MSA 表示再跑一轮 |
| single representation | MSA 第一行过线性层，唯一进入结构模块的 MSA 部分（类似 CLS） |
| rel-pos | 相对位置编码：用残基下标之差查可学习向量，而非直接嵌入下标 |
