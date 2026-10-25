# Graph Neural Networks User Group Meetup 9/29/2022

> **视频**：[Graph Neural Networks User Group Meetup 9/29/2022](https://www.youtube.com/watch?v=maUpBKEBXmw)
> **时长**：约 31 分钟
> **说明**：本视频是 GEARS 作者 Yusuf Roohani（Stanford 博士生）在 GNN User Group 的讲解。标题是 meetup 名称，内容就是 GEARS 这项工作的作者报告。视频开头主持人还简要介绍了 DGL 新版本及面向大规模图训练的数据分块流水线，随后进入报告。

## 视频主线

Yusuf 先从中心法则讲起：细胞的状态可以写成约两万个基因的表达向量，而扰动一个基因会牵动许多其他基因。问题在于，组合扰动的空间远远超过湿实验通量，于是他想用图神经网络把“基因之间如何相互影响”的先验知识注入模型。整场报告沿着“为什么难 → 过去怎么做 → GEARS 怎么把两套嵌入和两张图接起来 → 怎么训练 → 在什么设定下有效”的顺序展开。

## 一、先补生物学坐标：扰动改变的是细胞的基因表达向量

讲者先做了一段生物学 primer，因为后面会反复用到这些概念（[02:35](https://www.youtube.com/watch?v=maUpBKEBXmw&t=155)）。

生物学里的**中心法则**描述的是从基因型到表型的链路：DNA 上的基因转录成 RNA，RNA 再产生蛋白质；蛋白质是生命系统主要的功能执行者。这场报告主要关注 RNA 这一层，也就是**基因表达（gene expression）**——DNA 里有很多基因，每个基因会产生自己的转录本，测到某个基因的转录本数量，就说这个基因被“表达”了多少（[03:00](https://www.youtube.com/watch?v=maUpBKEBXmw&t=180)）。

实验上，基因表达是直接数出来的：取一个细胞，把里面的 RNA 转录本抽出来，数一数“基因 1 有 5 条、基因 3 有 23 条、基因 4 有 20 条”，就得到一个特征向量。人类细胞大约有两万个蛋白编码基因，每个基因对应一个计数，这个向量就是该细胞的**基因表达状态**。把所有细胞堆起来，就得到一个通常有几千个细胞、数万个特征的大矩阵（[03:25](https://www.youtube.com/watch?v=maUpBKEBXmw&t=205)、[04:15](https://www.youtube.com/watch?v=maUpBKEBXmw&t=255)）。

这个矩阵有两件事要记住。第一，基因表达对判断细胞身份、它在执行什么功能非常重要，几乎包含了细胞当前状态的全部信息。第二，**基因之间并不独立**：提高某一个基因的表达，通常会连带影响许多其他基因。GEARS 想近似的，正是这些基因之间的联合分布（[04:40](https://www.youtube.com/watch?v=maUpBKEBXmw&t=280)、[05:05](https://www.youtube.com/watch?v=maUpBKEBXmw&t=305)）。

## 二、要解决的问题：没做过的基因扰动，表达会怎么变

讲者引用了分子生物学教科书开头的一句话：我们对宇宙结构的理解，在很多方面反而好于对活细胞运作的理解；如果突变一个此前没研究过的基因，我们仍然无法预测细胞会怎样表现（[05:30](https://www.youtube.com/watch?v=maUpBKEBXmw&t=330)、[05:41](https://www.youtube.com/watch?v=maUpBKEBXmw&t=341)）。

GEARS 要回答的就是这句话的机器学习版本：**扰动一个基因、或一组没有做过实验的基因之后，基因表达响应是什么？** 思路是用机器学习学习基因之间的潜在分布，这样改变其中任何一个基因的表达，就能预测其他基因会怎么变（[06:06](https://www.youtube.com/watch?v=maUpBKEBXmw&t=366)）。

形式化地看，输入有两部分：未扰动细胞的表达状态 $x$，以及一个二值扰动向量 $p$，标出哪些基因被上调、哪些被下调；输出是扰动后所有基因的表达。这里的扰动可以是 CRISPR 等基因编辑技术造成的表达升高或降低（[06:39](https://www.youtube.com/watch?v=maUpBKEBXmw&t=399)、[07:04](https://www.youtube.com/watch?v=maUpBKEBXmw&t=424)、[07:29](https://www.youtube.com/watch?v=maUpBKEBXmw&t=449)）。

这件事不只对理解生物学有用。讲者列了三类应用（[08:02](https://www.youtube.com/watch?v=maUpBKEBXmw&t=482)、[08:27](https://www.youtube.com/watch?v=maUpBKEBXmw&t=507)、[08:52](https://www.youtube.com/watch?v=maUpBKEBXmw&t=532)、[09:17](https://www.youtube.com/watch?v=maUpBKEBXmw&t=557)）：

- **药物发现**：如果知道扰动会让细胞怎么响应，就有可能找到把细胞从疾病状态推回健康状态的扰动。讲者用单细胞数据的低维图举例：蓝色是健康细胞的生命轨迹，黄色是癌细胞，绿色是其他疾病细胞，理想情况是找到把疾病细胞推回健康轨迹的干预。
- **理解交互效应**：比如某个基因单独敲除不会杀死癌细胞，另一个也不会，但同时敲掉两个却会——这就是**合成致死（synthetic lethality）**。如果模型能预测组合响应，也许就能预测这类交互。
- **细胞重编程**：抗衰老、改造 T 细胞攻击癌症等方向，本质上都依赖有策略地改变某些基因的表达。

## 三、组合爆炸是硬约束，所以必须用计算去补实验做不完的空间

为什么不直接做实验？因为组合数爆炸得太快（[09:42](https://www.youtube.com/watch?v=maUpBKEBXmw&t=582)、[09:55](https://www.youtube.com/watch?v=maUpBKEBXmw&t=595)）。

仅考虑约两万个已知蛋白编码基因，两两组合在讲者的口径下就有约 $4\times10^8$ 种；三基因、四基因及更高阶组合还会再高几个数量级。而目前多数实验一次只看几千个扰动。也就是说，实验通量和组合空间之间差着好几个数量级，必然需要计算来覆盖组合扰动的结果空间（[10:20](https://www.youtube.com/watch?v=maUpBKEBXmw&t=620)）。

![为什么需要计算预测：组合扰动空间太大，湿实验无法穷举](assets/Graph Neural Networks User Group Meetup 9／29／2022/01_combination_explosion.webp)

## 四、过去两条路线：一条难学准，一条无法外推新扰动

这个问题并不新。讲者把过去的方法归成两条路线，各有各的短板（[10:45](https://www.youtube.com/watch?v=maUpBKEBXmw&t=645)）。

**第一条是推断基因调控网络。** 过去很强调把基因关系学成一张网络，通常是**基因调控网络（gene regulatory network）**，也可以理解成有方向的因果网络。难点在于：单细胞数据往往有两万个变量、几百到几千个观测，现有网络推断算法在这种规模上大多表现不好，很多直接失败；而且现有实现不太容易纳入非线性，像基因 1 和基因 2 同时被扰动时产生的非线性效应就更难捕捉（[11:10](https://www.youtube.com/watch?v=maUpBKEBXmw&t=670)、[11:35](https://www.youtube.com/watch?v=maUpBKEBXmw&t=695)）。

**第二条是跳过网络，直接用自编码器或潜变量模型映射。** 这类方法不再显式推断变量之间的图，而是从“施加的扰动 + 起始表达状态”直接映射到最终状态。但问题是它们并不真正理解扰动在生物学上意味着什么：如果训练时只见过基因 2 或基因 4 被扰动，模型就不知道基因 3 被扰动意味着什么。它们通常用 **one-hot 编码**表示扰动，而 one-hot 的坐标完全由训练数据决定，因此很难显著扩展到训练集之外（[12:00](https://www.youtube.com/watch?v=maUpBKEBXmw&t=720)、[12:25](https://www.youtube.com/watch?v=maUpBKEBXmw&t=745)）。

GEARS 想拿两边的好处：仍然用深度学习捕捉基因之间的复杂关系，同时把生物学先验做成知识图；遇到新基因时，回到图里找功能邻居，据此判断它被扰动后应该发生什么。这样才有机会准确表示训练时没见过的扰动（[12:25](https://www.youtube.com/watch?v=maUpBKEBXmw&t=745)、[12:50](https://www.youtube.com/watch?v=maUpBKEBXmw&t=770)）。

讲者给方法起的名字是 **Graph-Enhanced Gene Activation and Repression Simulator（GEARS）**，一句话概括就是：**用基因—基因关系先验约束的深度学习模型**（[13:15](https://www.youtube.com/watch?v=maUpBKEBXmw&t=795)）。

## 五、两套嵌入：基因是谁，和被扰动后会产生什么影响

GEARS 的输入就是前面说的未扰动表达向量和二值扰动向量。第一步是给每个基因、以及每个基因的扰动，各建一个多维嵌入：$n$ 个基因嵌入向量，$n$ 个扰动嵌入向量（[13:40](https://www.youtube.com/watch?v=maUpBKEBXmw&t=820)）。

为什么不用一个标量、而要给每个基因配多维向量？讲者在真实扰动数据里看到，不同基因对扰动的响应差异很大，基因表达响应的变异系数跨度很宽；一维标量容量不够，装不下这种异质性（[14:05](https://www.youtube.com/watch?v=maUpBKEBXmw&t=845)、[14:30](https://www.youtube.com/watch?v=maUpBKEBXmw&t=870)）。

第二，两套嵌入让扰动可以在**潜空间里做加法**。讲者借了 NLP 里的经典例子：`king` 的嵌入加上“女性”方向的嵌入，会接近 `queen`。GEARS 同理：把每个被扰动基因的扰动嵌入，加到所有基因的基因嵌入上。比如同时扰动基因 2 和基因 4，就把 $p_2$、$p_4$ 都加进每个基因的表示里，相当于在潜空间里模拟“这两个扰动作用在所有基因上”（[14:55](https://www.youtube.com/watch?v=maUpBKEBXmw&t=895)、[15:20](https://www.youtube.com/watch?v=maUpBKEBXmw&t=920)）。

![两套嵌入相加：每个基因的表示都加上被扰动基因的扰动向量](assets/Graph Neural Networks User Group Meetup 9／29／2022/02_two_embeddings.webp)

不过，随机初始化的嵌入本身没有生物学含义，没见过的基因也拿不到靠谱坐标。这正是接下来两张图要解决的问题。

## 六、两张图 + GCN：让没见过的基因借功能邻居获得坐标

GEARS 用了两张图，节点都是基因，节点特征都是嵌入向量；两张图各跑一个**图卷积网络（GCN，Graph Convolutional Network；让每个节点聚合邻居信息）**（[15:20](https://www.youtube.com/watch?v=maUpBKEBXmw&t=920)、[15:45](https://www.youtube.com/watch?v=maUpBKEBXmw&t=945)）。

1. **基因共表达图（gene co-expression graph）**：约束 **gene embedding**。经常一起变化的基因连在一起，GCN 促使邻居共享信息、表示趋于相似。表达模式相似，面对扰动时也可能有相似响应。
2. **基因本体图（GO graph，Gene Ontology）**：约束 **perturbation embedding**。功能相近、属于同一 GO 条目的基因，其“被扰动后的影响”也应该相似。

GCN 的作用是让相连的邻居交换信息。效果是：如果某个扰动从没做过，模型可以顺着 GO 图找到功能相近的邻居，借它们来推断这个扰动应该是什么表示；如果一个基因本身没出现过，共表达图也能把它放到相似基因旁边（[16:10](https://www.youtube.com/watch?v=maUpBKEBXmw&t=970)、[16:35](https://www.youtube.com/watch?v=maUpBKEBXmw&t=995)）。

这个设计不是凭空的。讲者展示了真实单细胞扰动数据：横轴是不同扰动、纵轴是不同基因的响应，可以看到很多扰动产生相似效果，形成**共功能模块（co-functional modules）**；也有很多基因对不同扰动做出相似响应，形成**共调控程序（co-regulated programs）**。把这些关系做成先验，既能显著扩大可预测空间，也起到额外正则化的作用（[17:00](https://www.youtube.com/watch?v=maUpBKEBXmw&t=1020)、[17:25](https://www.youtube.com/watch?v=maUpBKEBXmw&t=1045)）。

![两张图分别约束两套嵌入：共表达图管基因本身，GO 图管扰动效应](assets/Graph Neural Networks User Group Meetup 9／29／2022/03_two_graphs.webp)

## 七、跨基因层补次级效应，基因特异解码器保留异质性

到上一步，每个基因还是“各算各的”。但扰动常有**次级效应**：扰动基因 4 可能间接影响基因 9，而基因 9 并不在扰动列表里。GEARS 因此加了一个**跨基因 MLP 层（cross-gene MLP）**：把所有基因扰动后的嵌入汇总成一个全局状态，让每个基因参考这个全局状态更新自己。这样，如果 $p_2$ 和 $p_4$ 让基因 4 的表达升高，基因 9 就能通过全局状态调整自己的值（[17:50](https://www.youtube.com/watch?v=maUpBKEBXmw&t=1070)、[18:15](https://www.youtube.com/watch?v=maUpBKEBXmw&t=1095)）。

最后是**基因特异解码器（gene-specific decoder）**：每个基因有自己的解码参数，把最终嵌入映射回表达值，从而保留不同基因在响应幅度和模式上的异质性（[18:15](https://www.youtube.com/watch?v=maUpBKEBXmw&t=1095)）。

这里有个容易误解的细节：GEARS **不是自编码器**。每个基因的输出都直接连到最终解码器，同时又接受全局状态调制，而不是被迫先从全局状态重建所有嵌入。讲者说，这样可以减轻模型的学习负担（[18:40](https://www.youtube.com/watch?v=maUpBKEBXmw&t=1120)）。整套结构端到端训练：嵌入随机初始化，GCN 和所有 MLP 的参数一起更新（[19:05](https://www.youtube.com/watch?v=maUpBKEBXmw&t=1145)）。

![完整前向链路：两套嵌入 → 两张图 → 逐基因相加 → 跨基因层 → 基因特异解码](assets/Graph Neural Networks User Group Meetup 9／29／2022/04_architecture.webp)

## 八、两项损失：别被大量“没变化”的基因稀释，也别丢方向

训练数据是若干千个被不同方式扰动的细胞，每个细胞都有扰动后的真实状态。最直接的损失就是**均方误差（MSE）**：比较预测表达和真实表达，对所有基因、所有细胞、所有扰动求平方误差（[19:30](https://www.youtube.com/watch?v=maUpBKEBXmw&t=1170)）。

但直接用它有两个偏差，GEARS 各加了一项修正（[19:55](https://www.youtube.com/watch?v=maUpBKEBXmw&t=1195)）。

- **autofocus loss**：扰动一个细胞后，绝大多数基因不会发生变化，真正有明显响应的可能只有几百个。如果对所有基因一视同仁，损失会被大量“零”主导。GEARS 在误差上引入一个 $\gamma$ 项（把指数从 2 提到 $2+\gamma$），降低低变化基因的权重，把注意力放到高扰动基因上，这也是生物学家更关心的部分（[20:20](https://www.youtube.com/watch?v=maUpBKEBXmw&t=1220)、[20:45](https://www.youtube.com/watch?v=maUpBKEBXmw&t=1245)）。
- **方向性损失（directionality loss）**：在基因组学里，表达变化的方向（上调还是下调）有时比变化幅度更重要。讲者举例：两个预测可以有相同的 MSE，但一个方向对、一个方向错；对生物学用途来说，方向正确的那个更有价值。GEARS 因此额外约束预测的变化方向与真实方向一致——这里的“方向”指相对于未扰动状态的变化符号（[21:10](https://www.youtube.com/watch?v=maUpBKEBXmw&t=1270)、[21:35](https://www.youtube.com/watch?v=maUpBKEBXmw&t=1295)、[22:00](https://www.youtube.com/watch?v=maUpBKEBXmw&t=1320)）。

![autofocus + 方向性损失：同样的误差，方向正确的预测更有生物学价值](assets/Graph Neural Networks User Group Meetup 9／29／2022/05_losses.webp)

## 九、泛化按“没见过的基因数”分三档，GEARS 平均好约 45%

先看一个具体例子。讲者以 FOSB + CEBPB 的组合扰动为例：纵轴是相对对照（未扰动细胞）的表达变化，箱线表示真实扰动后状态，绿色虚线是未扰动水平，红点是 GEARS 的预测（[22:50](https://www.youtube.com/watch?v=maUpBKEBXmw&t=1370)、[23:15](https://www.youtube.com/watch?v=maUpBKEBXmw&t=1395)）。

GEARS 跟上了真实表达的上调、下调趋势。更关键的是，**CEBPB 在训练时从未被实验扰动过**：用 one-hot 的旧模型到这里没有坐标，无法做这个预测；GEARS 因为注入了先验知识，才能推断 CEBPB 被扰动后会发生什么（[23:40](https://www.youtube.com/watch?v=maUpBKEBXmw&t=1420)）。

讲者把“双基因组合”的泛化难度形式化成三档（[24:05](https://www.youtube.com/watch?v=maUpBKEBXmw&t=1445)、[24:30](https://www.youtube.com/watch?v=maUpBKEBXmw&t=1470)）：

- **0 unseen of 2**：两个基因都分别被扰动过，只是没做过这个组合；这是最简单的泛化。
- **1 unseen of 2**：其中一个基因从未被扰动过，另一个见过；至少要为一个没见过的基因做预测。
- **2 unseen of 2**：两个基因都没被单独扰动过，却要预测它们的组合；这是最难的一档。

从左到右，泛化难度递增。作者在数据集的三档设定上都做了比较，GEARS 相对两个基线**平均提升约 45%**：一个是线性模型（用共表达图加线性权重去拟合表达变化），另一个是 **CPA**（不用任何先验知识的自编码器类神经网络）（[24:55](https://www.youtube.com/watch?v=maUpBKEBXmw&t=1495)、[25:20](https://www.youtube.com/watch?v=maUpBKEBXmw&t=1520)）。

![三种泛化设定：从左到右，训练集里没见过的基因从 0 个增加到 2 个](assets/Graph Neural Networks User Group Meetup 9／29／2022/06_generalization.webp)

## 十、交互不总是相加：协同、抑制、上位，GEARS 都要能抓到

接下来讲者专门看**交互效应**。以两个基因的组合扰动为例：如果只看单个扰动的堆叠柱，一个朴素模型会把两个效应直接相加；但真实数据里，组合效应可能远大于相加，这叫**协同（synergy）**。GEARS 能相当准确地预测这种非加性效应（[25:45](https://www.youtube.com/watch?v=maUpBKEBXmw&t=1545)、[26:10](https://www.youtube.com/watch?v=maUpBKEBXmw&t=1570)）。

讲者把交互放到全转录组层面定义。设扰动 $x$ 的效果是向量 $X$，扰动 $y$ 的效果是向量 $Y$，组合的真实效果是 $Z$（[27:00](https://www.youtube.com/watch?v=maUpBKEBXmw&t=1620)、[27:25](https://www.youtube.com/watch?v=maUpBKEBXmw&t=1645)）：

- 如果只是简单相加，应有 $Z=X+Y$；
- **协同**时 $Z>X+Y$，组合效果大于两个单基因效果之和；
- **抑制（suppression）**时 $Z<X+Y$，组合效果小于相加；
- 还可以依此类推定义新形态、冗余、上位等其他交互类型。

定义好交互类型后，作者回到数据里，对每一类交互预测“最强的 10 个交互”，再和真实答案比较，用 **precision@10**（预测的前 10 个里有多少确实属于该类交互）衡量。GEARS 的 precision@10 显著高于现有基线，在检测遗传交互上**约提升 50%**（[27:50](https://www.youtube.com/watch?v=maUpBKEBXmw&t=1670)、[28:15](https://www.youtube.com/watch?v=maUpBKEBXmw&t=1695)）。

![非加性交互的几种类型：协同、抑制、新形态、冗余、上位](assets/Graph Neural Networks User Group Meetup 9／29／2022/07_interactions.webp)

## 十一、最终落点是外推：236 个扰动训练，5000 个没做过的扰动预测

讲者对 GEARS 的实践定位说得很明确：生物学家会先针对自己关心的一部分基因和组合做实验，然后用模型去**填满剩下的组合空间**，预测那些太贵、做不起的组合（[28:40](https://www.youtube.com/watch?v=maUpBKEBXmw&t=1720)）。

他们用真实数据做了这个实验：只用 **236 个扰动**训练，然后用 GEARS 预测 **5000 个没见过的扰动**，并从中找到了一些此前没有观察到的表型。讲者把总结落在三句话：这是第一个能可靠预测“未在实验中扰动过的基因组合”的计算方法；它能覆盖更大的组合扰动空间；它能帮助设计新的扰动实验（[28:40](https://www.youtube.com/watch?v=maUpBKEBXmw&t=1720)、[29:05](https://www.youtube.com/watch?v=maUpBKEBXmw&t=1745)）。

![用少量实验训练，再预测大量未做组合：GEARS 的定位是扩展实验空间](assets/Graph Neural Networks User Group Meetup 9／29／2022/08_extrapolation.webp)

## 十二、边界：45% 是三档平均，模型是实验的补充而不是替代

讲者在报告里没有把结论说成“全面超过实验”，边界可以从他的表述里读出来。

第一，**45% 是三档泛化设定的平均值**，不是每一档都提升 45%；讲者明确把三档设计成从左到右难度递增，最难的 2 unseen of 2 并不会因为平均值而被抹平（[24:55](https://www.youtube.com/watch?v=maUpBKEBXmw&t=1495)、[25:20](https://www.youtube.com/watch?v=maUpBKEBXmw&t=1520)）。

第二，**外推能力依赖图先验**。GEARS 之所以能处理没见过的扰动，是因为 GO 图和共表达图能提供功能邻居；反过来说，注释不完整、邻居很少的基因，能借到的信息就有限（[16:35](https://www.youtube.com/watch?v=maUpBKEBXmw&t=995)、[17:25](https://www.youtube.com/watch?v=maUpBKEBXmw&t=1045)）。

第三，**它的输出是基因表达层面的预测，价值在于缩小实验范围**。讲者的原话是先做一部分实验、再用模型填满组合空间，而不是用模型替代湿实验（[28:40](https://www.youtube.com/watch?v=maUpBKEBXmw&t=1720)）。

## 小结

- **问题**：组合扰动空间远大于实验通量，模型必须在“没做过某个扰动”时仍给出可检验的预测。
- **表示**：**gene embedding** 描述基因本身，**perturbation embedding** 描述“这个基因被扰动”，两者相加即可组合多个扰动。
- **先验**：**基因共表达图**约束 gene embedding，**GO 图**约束 perturbation embedding，再用 GCN 聚合邻居，让没见过的基因借功能邻居获得坐标。
- **结构**：**跨基因 MLP 层**负责次级效应，**基因特异解码器**保留异质性；模型不是自编码器，每个基因直接连到解码器并接受全局状态调制。
- **损失**：**autofocus loss** 对抗大量“没变化”的基因，**方向性损失**保证上调/下调方向正确。
- **结果**：三档泛化设定上平均优于线性与 CPA 基线约 45%，能预测协同、抑制等非加性交互，并展示了“236 个扰动训练 → 5000 个扰动外推”。它的价值是**扩展实验空间**，不是替代实验。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| 基因表达向量 | 一个细胞里各基因转录本数量组成的高维向量，描述细胞当前状态 |
| Perturb-seq | 把 CRISPR 扰动与单细胞 RNA 测序结合，读出扰动后的表达变化 |
| gene embedding | 描述“基因本身是谁”的可学习多维向量 |
| perturbation embedding | 描述“这个基因被扰动后产生什么影响”的可学习多维向量 |
| 共表达图 | 表达模式相似的基因连边的图，用来约束 gene embedding |
| GO 图 | 按基因功能注释建边的图，用来约束 perturbation embedding |
| 非加性交互 | 组合扰动效果不等于两个单扰动效果之和，如协同、抑制 |
| precision@10 | 排序任务里，预测的前 10 个结果中正确项所占比例 |

## 相关阅读

- [chemCPA：从化学结构预测未见药物](<Predicting Single-Cell Perturbation Responses For Unseen Drugs ｜ Leon Hetzel and Simon Böhm.md>)
- [Tahoe-x1：规模化扰动训练的单细胞基础模型](BioML Seminar 4.4 - Shreshth Gandhi on Scaling Perturbation-Trained Single-Cell Foundation Models.md)
- [Deep-learning-based Gene Perturbation Effect Prediction Does Not Yet Outperform Linear Baselines](Deep-learning-based Gene Perturbation Effect Prediction Does Not Yet Outperform Linear Baselines.md)
- [PerturBench: Benchmarking Machine Learning Models for Cellular Perturbation Analysis](<PerturBench：Benchmarking Machine Learning Models for Cellular Perturbation Analysis.md>)
