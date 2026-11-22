# MPNN 与 ProteinMPNN：固定骨架上的序列设计原理（RosettaCommons 教学讲座）

> 视频来源：[MPNN - ML for protein sequence design](https://www.youtube.com/watch?v=6z4XmUAwdNA)（YouTube，25 分 30 秒，RosettaCommons 蛋白设计教学系列讲座）

## 本讲要解决的核心问题（SCQA）

**背景**：蛋白 binder 设计三部曲的第二步是「配序列」。RFdiffusion 生成的只是多聚甘氨酸骨架（只有 Cα 坐标），要变成真正能表达、能折叠的蛋白，必须为骨架配上氨基酸序列。这个「给定结构求序列」的问题是结构预测（序列→结构）的逆问题，叫**固定骨架设计**（fixed backbone design）。

**冲突**：固定骨架设计的搜索空间巨大——能折叠成同一结构的序列有无数种，传统 Rosetta 固定骨架设计流程不仅速度慢（CPU 上每秒设计的氨基酸数远低于 GPU），在 103 个蛋白基准上的序列恢复率也只有约 17.9%。

**疑问**：MPNN／ProteinMPNN 是怎么把一张「结构图」编码成「氨基酸序列」的？哪些架构决策把测试集恢复率从基线 41.2% 一路推到 50.8%？推理时的采样过程又如何控制序列的多样与保守？

**回答（中心思想）**：ProteinMPNN = Ingraham 的 MPNN 消息传递架构（NeurIPS 2019）+ 五类重原子距离特征 + 编码器边更新 + 随机解码顺序（多聚体再加绑定链解码）；训练用逐位置交叉熵，推理时在每个位置输出 20 种氨基酸的概率并采样——temperature 越低越保守、越高越多样（超过 1.0 接近随机）。在 103 蛋白基准上以 temperature=0.1 达到 **27.6%** 恢复率（Rosetta 17.9%），PDB 测试集恢复率 **50.8%**、AlphaFold 模型准确率 **46.9%**。

## 一、任务定义：固定骨架设计——三部曲的第二步

### 1.1 从结构预测到序列设计

课程前半部分讲的是蛋白质结构预测：从单条序列出发，用 AlphaFold 得到完整三维构象。现在把方向反过来——[【跳转到 00:16】](https://www.youtube.com/watch?v=6z4XmUAwdNA&t=16)。

序列设计听起来就是它字面的意思：在**保持结构可能不变**的前提下，找出还能对序列做哪些改动。讲者也快速回顾了机器学习中蛋白质的多种表示：序列的独热编码、以比对形式呈现的进化信息、二级结构、各种残基间距离、扭转角、蛋白表面、坐标，以及把它们组织成的**蛋白图**（protein graph）——这些正是后面模型的原料。[【跳转到 00:51】](https://www.youtube.com/watch?v=6z4XmUAwdNA&t=51)

### 1.2 固定骨架设计：目标不是唯一解

固定骨架设计的任务定义：给定**全部骨架坐标**，在这条不许改动的骨架上设计蛋白序列。目标不是改动骨架本身，而是找到新序列——也就是最终能折叠成**同一结构**的、多种多样的序列。[【跳转到 01:21】](https://www.youtube.com/watch?v=6z4XmUAwdNA&t=81)

这正对应本仓库 6.1 管线 A 的第二步：RFdiffusion 产出骨架 → ProteinMPNN 配序列 → Protenix/OpenFold3 回折验证。

## 二、MPNN 架构：把结构图编码成序列（Ingraham, NeurIPS 2019）

### 2.1 消息传递与自回归解码

在讲 ProteinMPNN 之前，先看它的地基：John Ingraham 等人在 NeurIPS 2019 提出的 MPNN 架构。MPNN 全称**消息传递神经网络**（message passing neural network）。[【跳转到 01:46】](https://www.youtube.com/watch?v=6z4XmUAwdNA&t=106)

![MPNN 论文示意图：黑色曲线为骨架，每个节点对应一个残基](assets/MPNN%20-%20ML%20for%20protein%20sequence%20design/00125.webp)

看这张论文图：黑色曲线是骨架的示意图，每个节点对应一个残基。信息流的起点是**还没填上氨基酸身份的节点**——我们精确知道定义每个节点的坐标，目标就是给每个位置填上应有的氨基酸种类。[【跳转到 02:44】](https://www.youtube.com/watch?v=6z4XmUAwdNA&t=164)

假如从 N 端一路预测到 C 端，一旦进行到预测第 i 个残基，我们不仅能用邻域的**结构**信息，还能用之前预测留下的**序列**信息——先前预测过的位置会为第 i 个位置的设计提供条件。这种「按顺序把每一个空格填满、且顺序本身影响后续预测」的机制，就是**自回归**（autoregressive）。[【跳转到 03:34】](https://www.youtube.com/watch?v=6z4XmUAwdNA&t=214)

### 2.2 输入、输出与损失

从架构层面看：输入是结构图，输出是序列——预测序列并与真实序列（ground truth）比较。MPNN 的损失是**交叉熵**：每次逐位置预测序列，都算一个损失衡量与真实序列差多远；训练的目标是不断强化编码与解码相关的权重——对图的编码越准，从图解码到序列就越准。[【跳转到 03:57】](https://www.youtube.com/watch?v=6z4XmUAwdNA&t=237)

![结构图为输入、序列为输出：编码节点信息、更新边、逐位置解码](assets/MPNN%20-%20ML%20for%20protein%20sequence%20design/00283.webp)

### 2.3 边特征：邻域大小与朝向

边特征有两类值得展开。第一是**邻域**：比如定义一个 30 节点邻域——想预测某个残基的类型时，它周围这约 30 个节点对「这里能容纳什么氨基酸」影响最大。邻域大小是需要实验调节的量：既不能牺牲精度，又要保持计算高效；通过限定邻域引入稀疏性，让模型在关键位置获得更尖锐的响应。一个现成的模式先验：许多大体积残基不可能挤在非常紧凑的邻域里——这类模式能让预测更准。[【跳转到 03:50】](https://www.youtube.com/watch?v=6z4XmUAwdNA&t=230)

![距离特征 + 邻域稀疏性：更近的节点携带的信息权重更高](assets/MPNN%20-%20ML%20for%20protein%20sequence%20design/00430.webp)

第二是**朝向**（orientation）：深入到 α 碳的层面，计算「点云与坐标系框架」——编码两个 α 碳之间相对的几何方向关系。给定蛋白骨架，这些信息都能构建出来。[【跳转到 04:51】](https://www.youtube.com/watch?v=6z4XmUAwdNA&t=291)

## 三、两个关键指标：recovery 与 AlphaFold 模型准确率

### 3.1 recovery：序列一致性，而非相似性

MPNN 论文与当时的 Rosetta 固定骨架设计流程作比较——那是当年蛋白序列设计的主流工具，比较时把 temperature 设为 0.1（temperature 的细节会在实操里深入讲）。[【跳转到 05:21】](https://www.youtube.com/watch?v=6z4XmUAwdNA&t=321)

![MPNN vs Rosetta 对比实验设置：temperature=0.1 与 recovery 指标](assets/MPNN%20-%20ML%20for%20protein%20sequence%20design/00546.webp)

比较用的指标叫 **recovery（序列恢复率）**。它度量的是：设计序列与天然序列**完全一致**的位置百分比。注意是「序列一致性」（identity），不是「序列相似度」——如果第 100 位真实是丙氨酸而你预测成缬氨酸，就算错、恢复率下降；但如果你设计的序列与天然不同、却在相似区域保留了疏水性等化学倾向，整体上仍是有效的多样设计，只是不计入 recovery。

![recovery 示意：蓝色=与天然一致，绿色=唯一错掉的片段](assets/MPNN%20-%20ML%20for%20protein%20sequence%20design/00574.webp)

### 3.2 首战成绩与速度

结果：**27.6% 对 17.9%**——在 103 个蛋白的基准上，MPNN 明显超过了 Rosetta 固定骨架设计流程（以当时发表时点而言）。[【跳转到 05:52】](https://www.youtube.com/watch?v=6z4XmUAwdNA&t=352)

速度上同样优势明显：以「每秒设计一个氨基酸」计，GPU 远快于 CPU。当然也要诚实：103、40 个蛋白的基准都不算大，论文的测试集蛋白远多于 103——也许只是 Rosetta 很难跑出同等的速度。[【跳转到 06:17】](https://www.youtube.com/watch?v=6z4XmUAwdNA&t=377)

![MPNN vs Rosetta：recovery 与速度对比表](assets/MPNN%20-%20ML%20for%20protein%20sequence%20design/00652.webp)

## 四、ProteinMPNN：在 MPNN 之上加了什么（Dauparas 等，Baker 实验室，2022）

### 4.1 重原子坐标与多链支持

ProteinMPNN 发布于 2022 年夏天，出自 David Baker 实验室的 Justas Dauparas 等人，任务同样是「从骨架坐标 → 蛋白序列」，但建立在 Ingraham 的 MPNN 架构之上并大幅强化。[【跳转到 06:58】](https://www.youtube.com/watch?v=6z4XmUAwdNA&t=418)

![ProteinMPNN 论文图 1：重原子距离建边、编码器—解码器、逐位置概率输出](assets/MPNN%20-%20ML%20for%20protein%20sequence%20design/00762.webp)

看论文第一张图，从左往右：

- 输入是目标骨架的**重原子坐标**：氮（N）、α 碳（Cα）、羰基碳（C）、氧（O）、β 碳（Cβ）——基于这些距离构建边；
- 骨架编码器里，节点从全零出发，经**三层 MLP** 在节点层面学习、再更新边；
- 解码器结构与之相似，最终每个位置输出 **20 种氨基酸各自的概率**，再据此采样出各种各样的序列——这就是「配序列」的完整流程。[【跳转到 07:42】](https://www.youtube.com/watch?v=6z4XmUAwdNA&t=462)

![解码器输出：每个位置上 20 种氨基酸的概率，据此采样序列](assets/MPNN%20-%20ML%20for%20protein%20sequence%20design/00862.webp)

配色上链 A 用红色、链 B 用绿色——这是一个**多链**序列设计模型：既能给单体输入设计序列，也能给多聚体输入一次设计多条链的序列。[【跳转到 07:22】](https://www.youtube.com/watch?v=6z4XmUAwdNA&t=442)

### 4.2 解码顺序：从左到右 vs 随机；绑定链解码

既然是自回归模型，就绕不开解码顺序。「从左到右」放到蛋白术语里就是 **N 端 → C 端**；ProteinMPNN 的做法是**随机解码顺序**——不按 1→2→3→4→5 填空，而是以随机顺序逐位预测，这对提高序列恢复率有影响。[【跳转到 08:56】](https://www.youtube.com/watch?v=6z4XmUAwdNA&t=536)

对**同源多聚体**（homomer）还有一件利器：**绑定链解码**（tied chain decoding）。看这个三聚体的例子：无论随机解码到哪个位置，都让链 A、B、C 同步取**相同**的氨基酸——因为对称装配中各链序列必须一致。这样能一次性从三条链收集更多结构信息，给出更好的位置序列预测。[【跳转到 09:35】](https://www.youtube.com/watch?v=6z4XmUAwdNA&t=575)

![同源三聚体的绑定链解码：三链同步取相同氨基酸](assets/MPNN%20-%20ML%20for%20protein%20sequence%20design/00950.webp)

把迭代解码、随机解码顺序加上「从概率中采样」合起来，就是 ProteinMPNN 的推理流程图——temperature 正是在「采样」这一步起作用。[【跳转到 09:55】](https://www.youtube.com/watch?v=6z4XmUAwdNA&t=595)

## 五、消融实验：四步把 41.2% 推到 50.8%

论文的性能拆解表怎么读？度量还是 recovery：单链（单体）、未加粗的「零噪声」列。基线模型基本等价于 Ingraham 的原版 MPNN，测试准确率约 **41.2%**；表里同时报告参数量、困惑度（perplexity），以及一个很实用的指标——**AlphaFold 模型准确率**：把设计的序列喂给 AlphaFold，看它预测出的结构与真实结构有多接近。[【跳转到 10:39】](https://www.youtube.com/watch?v=6z4XmUAwdNA&t=639)

![性能拆解表：从基线到四个实验的递进](assets/MPNN%20-%20ML%20for%20protein%20sequence%20design/01039.webp)

四个实验的递进逻辑非常清晰，值得逐条记住：

1. **实验 1——加距离特征**：加入氮、α 碳、羰基碳、β 碳与氧的距离。起点是什么都不知道时，唯一的信息流就是结构——对结构细节把握得越好，序列一致性恢复越多；
2. **实验 2——更新编码器边**：在编码器的边上做更新，改善节点与边特征的学习；
3. **实验 3——合并**：两者都比基线好，合起来更高；
4. **实验 4——随机解码顺序**：把解码顺序从「从左到右」改成随机，这是最后一块拼图。

最终：测试集准确率 **50.8%**，AlphaFold 模型准确率 **46.9%**——相比基线 41.2% 是相当可观的提升；与 Rosetta 固定骨架流程相比，序列恢复能力更是巨大跃升（当然要记住该对比只覆盖 103 个蛋白）。[【跳转到 12:02】](https://www.youtube.com/watch?v=6z4XmUAwdNA&t=722)

![最终成绩：50.8% 测试准确率、46.9% AlphaFold 模型准确率](assets/MPNN%20-%20ML%20for%20protein%20sequence%20design/01250.webp)

## 六、读成绩单的两个视角：埋藏程度与装配体类型

### 6.1 核心 vs 表面：物理约束决定恢复难度

想更细致地看性能，看这张图：y 轴是序列恢复率，x 轴是「**八个最近邻 β 碳的平均距离**」。这是什么度量？在一个真实蛋白结构里，8 个最近 β 碳贴得最近的地方是蛋白中心——核心（core）；所以 x 轴实际是**埋藏程度**（burial）的指标：从核心残基到表面残基，考察恢复率如何变化。[【跳转到 13:05】](https://www.youtube.com/watch?v=6z4XmUAwdNA&t=785)

![埋藏程度 vs 序列恢复率：越往核心恢复率越高](assets/MPNN%20-%20ML%20for%20protein%20sequence%20design/01294.webp)

趋势一目了然：越靠近核心恢复率越高——核心残基受物理约束强，可放的氨基酸更受限；表面更灵活、约束不足、可选项多，所以更难恢复出「完全相同」的序列。Rosetta（蓝）与 ProteinMPNN（橙）趋势一致。

还有一个初学者容易纠结的问题：恢复率低一定不好吗？不一定——如果你从一条**全新的骨架**（de novo）出发，它可能谁都不像，本来就不存在「标准答案」可恢复，你只是在为骨架设计一条合理序列。100% 恢复率只在「天然序列存在且被精确复刻」时才有意义。[【跳转到 13:46】](https://www.youtube.com/watch?v=6z4XmUAwdNA&t=826)

### 6.2 单体 / 同源多聚体 / 异源多聚体

右图把输入分三类分别绘制恢复率：**单体**（只有链 A 进模型、只产出链 A 的序列）、**同源多聚体**、**异源多聚体**（一次预测多条链的序列）。对比三类输入的准确率，为多链设计（比如蛋白 binder、抗体-抗原复合物的序列设计）提供了参考——哪类装配体最容易设计准，看这张图就知道。[【跳转到 14:41】](https://www.youtube.com/watch?v=6z4XmUAwdNA&t=881)

![三类装配体的序列恢复率对比](assets/MPNN%20-%20ML%20for%20protein%20sequence%20design/01476.webp)

## 小结

- 固定骨架设计是结构预测的逆问题：骨架不动、序列多样，它是 binder 设计三部曲「RFdiffusion → **ProteinMPNN** → 回折验证」的中间步。
- MPNN（Ingraham, NeurIPS 2019）用消息传递把结构图编码成序列：节点=残基、边=结构关系、自回归逐位预测、逐位置交叉熵训练。
- recovery 度量与天然序列的**一致性**（不是相似度）；AlphaFold 模型准确率则检验「设计序列能否真的折叠回目标结构」。
- ProteinMPNN 的四步强化——重原子距离特征、编码器边更新、两者合并、随机解码顺序——把测试集恢复率从 41.2% 推到 **50.8%**（AlphaFold 模型准确率 46.9%）。
- 多聚体场景用**绑定链解码**：对称装配的各链同步取相同氨基酸，一次收集更多结构信息。
- 采样发生在「逐位置概率」这一步：temperature 越低越保守、越高越多样——这就是条目「sampling_temp 控制多样性」的机制所在。
- 埋藏程度决定恢复难度：核心易、表面难；de novo 骨架可能根本没有「正确答案」可恢复。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| 固定骨架设计（fixed backbone design） | 给定不许改动的骨架坐标，设计能折叠成该结构的氨基酸序列 |
| MPNN（消息传递神经网络） | 把蛋白当作「残基为节点、结构关系为边」的图，在图上传递信息并逐位置预测氨基酸（Ingraham, NeurIPS 2019） |
| 自回归（autoregressive） | 按某种顺序逐位填空，已填好的位作为后续预测的条件 |
| recovery（序列恢复率） | 设计序列与天然序列完全一致位置的百分比，度量「一致性」而非「相似度」 |
| AlphaFold 模型准确率 | 把设计序列喂给 AlphaFold，用预测结构与真实结构的接近程度检验设计质量 |
| 随机解码顺序 | 不按 N→C 端顺序、而以随机顺序逐位解码，ProteinMPNN 的重要改进 |
| 绑定链解码（tied chain decoding） | 同源多聚体各链在相同位置同步取相同氨基酸的解码策略 |
| temperature | 采样温度：控制逐位置概率采样的随机程度，越低越保守、越高（>1.0）越接近随机 |

> 配套实操：本讲座为方法面；ProteinMPNN 在管线中的实操（contigs 衔接、temperature 调参、AlphaFold 验证）见同条目另两篇博客——《Learn Protein Design From Theory to Practical - Part 3》与《实操演示：ProteinMPNN定向进化改造蛋白质》。
