# 读懂数据库里的 AlphaFold 多聚体：从 pLDDT 到 ipSAE 的五级置信度体系

> 来源视频：[Confidence metrics used in the AlphaFold Database multimers](https://www.youtube.com/watch?v=k4yBqddtPyQ) · 时长 45:08
> 本篇基于视频 AI 字幕与画面整理（EMBL-EBI 培训出品，AlphaFold 数据库外展项目），时间戳可跳转回原视频对应位置。

## 本讲要解决的核心问题（SCQA）

**背景**：AlphaFold 数据库（AlphaFold Database）近年大规模扩展到**蛋白质复合物**——NVIDIA、首尔国立大学、PDBe 与 Google DeepMind 合作，用 AlphaFold-Multimer 为模式生物的蛋白对批量建模，入库了约 **180 万个高置信复合物模型**。

**冲突**：结构看着合理，不等于可信。单链时代的 pLDDT、PAE 回答不了"**链与链之间的界面建模对不对**"——而复合物的活性位点、结合口袋、变构位点往往**只在链间界面上形成**，界面才是功能单元。

**疑问**：面对一个多聚体预测条目，该看哪几个数字？每个数字到底在测什么？高分就一定可靠吗？

**回答（中心思想）**：复合物级有**五个指标**——**average pLDDT**（链自身折叠质量）、**ipTM**（链间相对定位的全局置信度，0–1）、**ipSAE**（只统计界面残基的 ipTM 精修版）、**pDockQ2**（界面物理合理性，阈值有结构含义）、**LIS**（界面局部相互作用密度）。它们的共同设计出发点：**判断一个多聚体预测好不好，本质上是判断"界面建模对不对"**。而读数的总原则是——**分数是分诊（triage），不是判决（verdict）**。

![本讲核心问题：多聚体预测看起来合理，但如何判断它可信？](assets/Confidence%20metrics%20used%20in%20the%20AlphaFold%20Database%20multimers/00005.webp)

---

## 一、先补课：复合物靠什么成立，为什么"界面即功能单元"

### 1.1 三类复合物

按"蛋白在跟什么相互作用"，复合物分三大类 [【跳转到 02:30】](https://www.youtube.com/watch?v=k4yBqddtPyQ&t=150)：

![蛋白复合物三大类：蛋白-蛋白、蛋白-配体、蛋白-核酸](assets/Confidence%20metrics%20used%20in%20the%20AlphaFold%20Database%20multimers/00150.webp)

- **蛋白-蛋白相互作用（PPI）**：包括同源二聚体（homodimer，两个相同亚基）、异源二聚体（heterodimer，两个不同亚基）以及更多链组装成的大复合物；
- **蛋白-配体相互作用（PLI）**：酶-底物、受体-药物，以及**变构（allosteric）分子**——结合在远离活性位点的地方却能调控蛋白功能；
- **蛋白-核酸相互作用（PNI）**：蛋白-DNA、蛋白-RNA，以及蛋白与 RNA 共同组成功能单元的核糖核蛋白复合物。

本视频聚焦第一类（PPI）。

### 1.2 界面是功能单元

复合物是两条以上多肽链的稳定结合，主要靠**非共价相互作用**维系，形成确定的三维组装（即四级结构）[【跳转到 03:58】](https://www.youtube.com/watch?v=k4yBqddtPyQ&t=238)。组装可以是**同源寡聚化**（相同亚基形成高阶结构），也可以是**异源组装**——视频用**鞭毛马达**做例子：多条蛋白链高度有序地装配，马达的正常功能依赖各组件精确就位 [【跳转到 04:48】](https://www.youtube.com/watch?v=k4yBqddtPyQ&t=313)。

为什么异源组装重要？因为**活性位点、结合口袋、变构位点经常只在链与链的交界处形成**——"界面就是功能单元" [【跳转到 06:16】](https://www.youtube.com/watch?v=k4yBqddtPyQ&t=376)：

![活性位点与结合口袋常在链间界面形成：界面即功能单元](assets/Confidence%20metrics%20used%20in%20the%20AlphaFold%20Database%20multimers/00376.webp)

所以当我们问"这是个好的 AlphaFold 多聚体预测吗"，真正在问的是"**界面建模正确吗**"——这正是本视频所有指标的设计出发点。

---

## 二、数据库里的多聚体是哪来的：3100 万候选到 180 万模型

AlphaFold 数据库的复合物扩展来自一项多方合作研究（NVIDIA、首尔国立大学、PDBe、Google DeepMind）[【跳转到 06:51】](https://www.youtube.com/watch?v=k4yBqddtPyQ&t=411)。流程是：

1. 从约 4700 个顶级模式生物与 WHO 优先物种出发，构建约 **3100 万候选蛋白对**（同源二聚体 + 异源二聚体）；
2. 用质量标准过滤（视频给出的两条：**pDockQ2 ≥ 0.23、ipSAE ≥ 0.6**）；
3. 最终留下约 **180 万个高置信模型**放入数据库 [【跳转到 07:16】](https://www.youtube.com/watch?v=k4yBqddtPyQ&t=436)。

![从 3100 万候选对到 180 万高置信模型的筛选流程](assets/Confidence%20metrics%20used%20in%20the%20AlphaFold%20Database%20multimers/00436.webp)

这是变革性的资源，但"规模大"也带来责任：**下结论之前，必须先学会读这些置信度分数**。

---

## 三、基础指标：单链也能用的 pLDDT 与 PAE

这一节是"地基"——无论单体还是多聚体，任何 AlphaFold 预测都会给出这两个分数 [【跳转到 08:04】](https://www.youtube.com/watch?v=k4yBqddtPyQ&t=484)。

### 3.1 pLDDT：每个残基的局部打包质量（0–100）

**pLDDT（predicted local distance difference test）是逐残基分数**：结构里每个残基都有自己的 0–100 分，越高说明 AlphaFold 对该残基**局部堆积（local packing）**越有信心 [【跳转到 08:16】](https://www.youtube.com/watch?v=k4yBqddtPyQ&t=496)：

![pLDDT 定义：逐残基 0–100 分，衡量局部堆积](assets/Confidence%20metrics%20used%20in%20the%20AlphaFold%20Database%20multimers/00496.webp)

两个关键点 [【跳转到 08:41】](https://www.youtube.com/watch?v=k4yBqddtPyQ&t=521)：

- **它不是拍脑袋的置信数**：训练与验证目标就是"局部距离差异检验（LDDT）"——用分辨率优于 3.5 Å 的实验 PDB 结构算出的真实构象质量分；
- **关键词是"局部"**：只管每个残基的紧邻环境，**不管整体、也不管各结构域之间的相对摆放**——那需要另外的指标。

LDDT 怎么算 [【跳转到 11:32】](https://www.youtube.com/watch?v=k4yBqddtPyQ&t=692)：对每个残基，检查它与 **15 Å 范围内**各 Cα 原子的距离，距离误差是否落在 **0.5、1、2、4 Å** 四档之内，做四次二值判定；先对每对残基取平均，再对邻近所有残基对平均，最后缩放到 0–100。

读结构的经验法则 [【跳转到 10:02】](https://www.youtube.com/watch?v=k4yBqddtPyQ&t=602)：蓝色（>90）区域可放心当"结构良好的部分"；黄/橙区域常是**无序环区或柔性末端**，解读要多加小心。视频里示例模型的平均 pLDDT 为 80.56，属高置信档。下面这张图最能说明问题：同一个蛋白，左边是实验解析的 PDB 结构，右边是 AlphaFold 预测模型（按 pLDDT 着色）——**蓝色高分区与实验解析出的结构对应得很好** [【跳转到 10:42】](https://www.youtube.com/watch?v=k4yBqddtPyQ&t=642)：

![AF2 预测（按 pLDDT 着色）与实验 PDB 结构对照：蓝色高分区吻合](assets/Confidence%20metrics%20used%20in%20the%20AlphaFold%20Database%20multimers/00642.webp)

### 3.2 PAE：两个残基的相对定位误差（Å）

**PAE（predicted aligned error，预测对齐误差）回答的是另一个问题**：pLDDT 问"这个残基本身的局部结构我有多确定"，PAE 问"**两个残基的相对位置我有多确定**" [【跳转到 12:17】](https://www.youtube.com/watch?v=k4yBqddtPyQ&t=737)。

![PAE 矩阵定义：第 (x,y) 格 = 残基 x 相对残基 y 的预期位置误差](assets/Confidence%20metrics%20used%20in%20the%20AlphaFold%20Database%20multimers/00737.webp)

- 矩阵第 (x, y) 格的颜色 = 把预测结构与真实结构**在残基 y 上对齐**后，残基 x 的**预期位置误差（埃）**；
- 数值范围约 **0–30 Å**：深绿 = 误差低、高置信；浅绿/黄 = 误差高、不确定 [【跳转到 12:42】](https://www.youtube.com/watch?v=k4yBqddtPyQ&t=762)；
- 单体场景的用法：**找出柔性连接区（flexible linker）或独立结构域**——动画演示里，方块选中"堆叠良好"的结构域，选中高误差区块则暴露出中间的柔性连接区 [【跳转到 13:07】](https://www.youtube.com/watch?v=k4yBqddtPyQ&t=787)；
- 矩阵**不对称**：A 相对 B 的定位误差 ≠ B 相对 A 的定位误差 [【跳转到 13:32】](https://www.youtube.com/watch?v=k4yBqddtPyQ&t=812)。

### 3.3 多聚体的 PAE 分块读法：对角管链内，非对角管链间

对复合物，PAE 矩阵会**按链分块**：对角线上的块是**链内置信度**（每条链自身内部结构好不好），**非对角块是链间 PAE——这才是复合物的关键** [【跳转到 14:34】](https://www.youtube.com/watch?v=k4yBqddtPyQ&t=874)：

![多聚体 PAE 分块：对角块=链内，非对角块=链间](assets/Confidence%20metrics%20used%20in%20the%20AlphaFold%20Database%20multimers/00874.webp)

练眼法 [【跳转到 17:39】](https://www.youtube.com/watch?v=k4yBqddtPyQ&t=1059)：

- 非对角块里出现**深绿斑块** = AlphaFold 找到了链间**具体且可信的接触**；斑块越紧凑、越深，预测的界面越可信；
- 非对角块**整体浅色、近乎空白 = 红旗**：链虽然被放进了同一个模型，但**并没有真正建模出界面** [【跳转到 18:04】](https://www.youtube.com/watch?v=k4yBqddtPyQ&t=1084)。

![非对角块空白是红旗： chains 放在一起但没有真实界面](assets/Confidence%20metrics%20used%20in%20the%20AlphaFold%20Database%20multimers/01084.webp)

---

## 四、复合物级指标：五个数字各管一件事

进入正题。AlphaFold 数据库的多聚体条目有**五个质量指标** [【跳转到 18:42】](https://www.youtube.com/watch?v=k4yBqddtPyQ&t=1122)：

![复合物级五大指标一览](assets/Confidence%20metrics%20used%20in%20the%20AlphaFold%20Database%20multimers/01122.webp)

| 指标 | 全称 | 管什么 | 范围 |
| --- | --- | --- | --- |
| **average pLDDT** | 平均预测局部距离差异检验 | 蛋白级（各链）结构质量 | 0–100 |
| **ipTM** | interface predicted template modeling score | 链间相对定位的整体置信度 | 0–1 |
| **ipSAE** | interface prediction score from aligned error | 只统计"真界面"残基的 ipTM 精修版 | 0–1 |
| **pDockQ2** | predicted interface DockQ, version 2 | 界面物理合理性 | 0–1 |
| **LIS** | local interaction score | 低误差链-链相互作用的局部密度 | 0–1 |

注意：AlphaFold Server / ColabFold 只直接产出 **average pLDDT 和 ipTM**，其余三个要用其他工具或 AlphaFold 数据库工具箱计算 [【跳转到 19:32】](https://www.youtube.com/watch?v=k4yBqddtPyQ&t=1172)。下面逐个拆解。

### 4.1 average pLDDT：链自身折得好不好（必要不充分）

多聚体的 average pLDDT 算法与单体相同：把**所有链**的逐残基 pLDDT 取平均 [【跳转到 20:14】](https://www.youtube.com/watch?v=k4yBqddtPyQ&t=1214)。它告诉你"**每条链自身折叠得好不好**"。

但有个重要警告：**它对界面一无所知**。两条链可以各自折叠得非常漂亮（pLDDT 很高），彼此的相对摆放却完全错误。所以 average pLDDT 必须与界面指标一起解读——它是好预测的**必要条件，不是充分条件** [【跳转到 20:39】](https://www.youtube.com/watch?v=k4yBqddtPyQ&t=1239)。

视频里两个锚点例子 [【跳转到 21:25】](https://www.youtube.com/watch?v=k4yBqddtPyQ&t=1285)：异源二聚体 average pLDDT = 82.99（高置信），同源二聚体 = 93.64（非常高）——但这两个数**只评价链的质量，不评价界面质量**。

### 4.2 ipTM：链间相对定位的全局置信度

ipTM 是"**界面版的 TM-score**"，理解它要先懂 TM-score [【跳转到 22:12】](https://www.youtube.com/watch?v=k4yBqddtPyQ&t=1332)：

![TM-score 定义：真实误差除以长度修正因子 d0，取最优叠合](assets/Confidence%20metrics%20used%20in%20the%20AlphaFold%20Database%20multimers/01332.webp)

**TM-score 的原理**：把预测结构与实验结构做叠合（superposition），对每个等价原子对 J 计算 3D 距离误差 dJ，除以**长度修正因子 d0**——d0 随蛋白长度变化，避免"大蛋白原子多、漂移概率大"被不公平地惩罚。比值恒在 0–1：完美叠合 = 1，误差越大越接近 0。公式还**对叠合方式取最大值（max over i）**——先找最好的叠合再打分。这使 TM-score 成为**真正全局**的结构一致性度量 [【跳转到 22:37】](https://www.youtube.com/watch?v=k4yBqddtPyQ&t=1357)。

**AlphaFold 的巧思**：它手里没有实验结构，算不出真实误差 dJ。解决办法是**用自己内部的误差估计——PAE——替代 dJ**，公式其余部分不变 [【跳转到 23:02】](https://www.youtube.com/watch?v=k4yBqddtPyQ&t=1382)：

![pTM 的实现：把 TM-score 公式里的真实误差替换成 PAE](assets/Confidence%20metrics%20used%20in%20the%20AlphaFold%20Database%20multimers/01407.webp)

- 这样得到的 **pTM** 回答的问题是："**各结构域的朝向可信吗？各结构区相对摆放可信吗？**"（全局/链内）[【跳转到 23:52】](https://www.youtube.com/watch?v=k4yBqddtPyQ&t=1432)；
- **ipTM** 把同一思想搬到**链间**：对 A、B 两条链，用**跨链残基对**的 PAE 值计算一个 TM-score 式的度量，问"AlphaFold 对这两条链的相对定位与朝向有多确信" [【跳转到 24:17】](https://www.youtube.com/watch?v=k4yBqddtPyQ&t=1457)：

![ipTM：以链 A 为参照、用跨链 PAE 评估链 B 的定位置信度](assets/Confidence%20metrics%20used%20in%20the%20AlphaFold%20Database%20multimers/01457.webp)

**ipTM(A→B) 的四步算法**（视频用"链 A 的丙氨酸 25"做逐步演算）[【跳转到 25:32】](https://www.youtube.com/watch?v=k4yBqddtPyQ&t=1532)：

1. **选锚点**：从链 A 取一个残基（如丙氨酸 25），对链 B 的每个残基 J 计算 PTM(25, J)——值来自 PAE，含义是"模型对残基 J 相对残基 25 位置的确信度"；
2. **对链 B 平均**：得到单一数值 S25——"如果用丙氨酸 25 作对齐锚点，整条链 B 相对它的位置我掌握了多好" [【跳转到 26:22】](https://www.youtube.com/watch?v=k4yBqddtPyQ&t=1582)；
3. **遍历链 A**：对链 A 每个残基重复，得到 S1, S2, S3, … [【跳转到 26:47】](https://www.youtube.com/watch?v=k4yBqddtPyQ&t=1607)；
4. **取最大值**：ipTM(A→B) = max(S1, S2, S3, …)——AlphaFold 在问"链 A 里哪个残基是摆好链 B 的最佳锚点"，并保留这个最佳分数 [【跳转到 27:12】](https://www.youtube.com/watch?v=k4yBqddtPyQ&t=1632)。

由于分数**不对称**，还要算一遍 ipTM(B→A)，最终 **ipTM = max(A→B, B→A)** [【跳转到 27:37】](https://www.youtube.com/watch?v=k4yBqddtPyQ&t=1657)。

**阈值**（依 AlphaFold-Multimer 官方指南）[【跳转到 27:52】](https://www.youtube.com/watch?v=k4yBqddtPyQ&t=1672)：**ipTM > 0.8** 一般视为高置信预测；**< 0.6** 往往意味着链摆放错误。

### 4.3 ipSAE：只看"真界面"残基的 ipTM 精修版

**ipTM 有个系统性缺陷**：它对复合物**全部残基**取平均——包括无序尾巴、柔性连接区、以及喂进 AlphaFold 但根本不参与相互作用的区域 [【跳转到 28:27】](https://www.youtube.com/watch?v=k4yBqddtPyQ&t=1707)。这些区域天然 PAE 高（不确定性大），会**把 ipTM 拖低，即便真实界面建模得很好**。

**ipSAE 的修正**：只用**相距 15 Å 以内、且 PAE < 10 Å** 的残基对来计算——即只统计"真正位于界面、且被高置信预测"的残基 [【跳转到 28:52】](https://www.youtube.com/watch?v=k4yBqddtPyQ&t=1732)：

![ipSAE：只用 15 Å 内且 PAE<10 Å 的残基对](assets/Confidence%20metrics%20used%20in%20the%20AlphaFold%20Database%20multimers/01732.webp)

要点：

- 它**不是同一公式换个阈值**，而是**从根本上换了残基对子集**——问的问题变成："对于那些 AlphaFold 认为在界面上的残基，它对它们的相对排布有多确信？"（无序尾巴在有些蛋白里占序列的 30–40%，在这里被完全排除）[【跳转到 30:12】](https://www.youtube.com/watch?v=k4yBqddtPyQ&t=1812)；
- 对**全长 UniProt 序列**（而非只提交结构域）做预测时尤其重要；
- 公式与 ipTM 相同、外加 PAE 截断；d0 依赖参与残基数 L（链 B 中 PAE 低于截断的独立残基数），并设下限——视频提到 d0 最小值取 1、L 最小取 19（因为 18 会给出负数）[【跳转到 31:02】](https://www.youtube.com/watch?v=k4yBqddtPyQ&t=1862)；
- **方向性**与 ipTM 相同（ipSAE A→B / B→A），最终取两者最大 [【跳转到 31:27】](https://www.youtube.com/watch?v=k4yBqddtPyQ&t=1887)。

**ipSAE 阈值**（比 ipTM 更严格，因为计算更苛刻、更聚焦）[【跳转到 32:14】](https://www.youtube.com/watch?v=k4yBqddtPyQ&t=1934)：

| ipSAE | 解读 |
| --- | --- |
| ≥ 0.88 | 非常高置信，界面建模准确 |
| 0.7 – 0.8 | 高置信，多半正确 |
| 0.6 – 0.7 | 置信较低，谨慎解读 |
| < 0.6 | 预测的相互作用多半不可靠 |

![ipSAE 阈值表：0.88 / 0.7 / 0.6 三条分界线](assets/Confidence%20metrics%20used%20in%20the%20AlphaFold%20Database%20multimers/01934.webp)

**一个最能说明问题的对照** [【跳转到 33:00】](https://www.youtube.com/watch?v=k4yBqddtPyQ&t=1980)：左例 **ipTM = 0.38**（按阈值判"界面错误"），但 **ipSAE = 0.75**——说明界面本身其实建模得不错，低 ipTM 是被全长序列里的无序区拖下来的；右例 ipTM 0.82、ipSAE 0.75，两者一致地高置信。**结论：全长序列 + 低 ipTM + 较高 ipSAE 时，别急着扔掉预测——先看 ipSAE 和 PAE 矩阵里有没有真界面。**

![同一界面：ipTM 0.38 vs ipSAE 0.75——无序区拖累了 ipTM](assets/Confidence%20metrics%20used%20in%20the%20AlphaFold%20Database%20multimers/01980.webp)

**统计学证据**：把全长 UniProt 序列喂给 AF2，比较 42 个真实复合物与 74 个"假复合物"（蛋白实际并不相互作用）[【跳转到 34:05】](https://www.youtube.com/watch?v=k4yBqddtPyQ&t=2045)。**ipSAE 的真假分布几乎不重叠**（干净分离），而 **ipTM 的分布重叠可观**——在需要给成百上千候选相互作用排序的筛查场景里，这种区分度上的差距是决定性的：**ipSAE 是更好的过滤器** [【跳转到 34:30】](https://www.youtube.com/watch?v=k4yBqddtPyQ&t=2070)。

![ipSAE 对真假复合物的分离度显著优于 ipTM](assets/Confidence%20metrics%20used%20in%20the%20AlphaFold%20Database%20multimers/02045.webp)

### 4.4 pDockQ2：界面物理合理性，阈值有结构含义

第四个指标换个思路：**pDockQ2（predicted interface DockQ, version 2）把两类信息合起来**——链间**平均 PAE**（讲了很多）与**界面残基的平均 pLDDT**。公式逐残基加权这两者，再对界面残基对取最大值 [【跳转到 35:02】](https://www.youtube.com/watch?v=k4yBqddtPyQ&t=2102)。

它最大的实用优势：**校准到实验结构**，所以阈值有直接的"结构含义" [【跳转到 35:27】](https://www.youtube.com/watch?v=k4yBqddtPyQ&t=2127)：

| pDockQ2 | 界面质量 |
| --- | --- |
| > 0.5 | 高质量界面 |
| 0.23 – 0.5 | 中等质量 |
| < 0.23 | 低质量 |

![pDockQ2 阈值：>0.5 高质量、0.23–0.5 中等、<0.23 低质量](assets/Confidence%20metrics%20used%20in%20the%20AlphaFold%20Database%20multimers/02127.webp)

### 4.5 LIS：界面"小而真"的局部相互作用分数

最后是 **LIS（local interaction score，局部相互作用分数）**。它针对一种常见情形：**真实的界面接触在 PAE 矩阵上表现为离散的深蓝/低误差小岛**——这些岛不必很大、不必连续，**一小片低 PAE 就足以支撑真实的结合** [【跳转到 38:24】](https://www.youtube.com/watch?v=k4yBqddtPyQ&t=2304)。

![LIS：界面块内离散的低 PAE 小岛](assets/Confidence%20metrics%20used%20in%20the%20AlphaFold%20Database%20multimers/02304.webp)

做法：把这些低误差区反演到 0–1 尺度（PAE = 0 → 得分 1，达到或超过截断 → 趋近 0），再对被标记的残基对取平均，平均值即 LIS（视频示例：0.457 与 0.39 取平均）[【跳转到 38:49】](https://www.youtube.com/watch?v=k4yBqddtPyQ&t=2329)。

**为什么需要 LIS**：ipTM 在**整个界面上平均**，一小块高置信接触可能被周围不确定的残基"稀释"；**LIS 只在确信定位的残基对上平均**——这种刻意的"局部性"正是它的立身之本，特别适合**无序或柔性结合区**：信号是真的，只是空间上 confined（局限在小区域）[【跳转到 39:14】](https://www.youtube.com/watch?v=k4yBqddtPyQ&t=2354)。

---

## 五、实战：读一条真实的数据库条目（IL-12β / IL-23α）

把五个指标用在一条真实条目上：**白细胞介素-12 亚基 β（interleukin-12 subunit beta）与白细胞介素-23 亚基 α（interleukin-23 subunit alpha）**的复合物 [【跳转到 39:48】](https://www.youtube.com/watch?v=k4yBqddtPyQ&t=2388)。IL-23 是适应性免疫与炎症的关键调控因子，这个界面正是**细胞因子信号转导界面**——生物学意义重大。

![实战条目：IL-12β / IL-23α 复合物的数据库页面](assets/Confidence%20metrics%20used%20in%20the%20AlphaFold%20Database%20multimers/02420.webp)

逐个读数 [【跳转到 40:20】](https://www.youtube.com/watch?v=k4yBqddtPyQ&t=2420)：

| 指标 | 数值 | 解读 |
| --- | --- | --- |
| average pLDDT | 82.05 | 高——各链自身结构良好 |
| ipSAE | 0.77 | 高置信区间，良好 |
| ipTM | 0.8 | 同样达高置信 |
| pDockQ2 | 0.54 | 越过 0.5 → 高质量界面 |
| LIS | 0.52 | 与其他指标一致，支持存在有生物学意义的相互作用 |

**五个指标指向同一方向**：这是一个高置信、真实且建模良好的界面——"这正是所有指标协同工作时你希望看到的样子" [【跳转到 40:45】](https://www.youtube.com/watch?v=k4yBqddtPyQ&t=2445)。

---

## 六、总原则：分数是分诊，不是判决

视频最后强调全片最重要的观念：**置信度分数是分诊（triage），不是判决（verdict）**——它们必须与生物学判断和实验验证配合使用 [【跳转到 41:24】](https://www.youtube.com/watch?v=k4yBqddtPyQ&t=2484)。

![核心观念：Confidence scores are triage, not verdicts](assets/Confidence%20metrics%20used%20in%20the%20AlphaFold%20Database%20multimers/02484.webp)

两个"预测 + 实验验证"的正面案例 [【跳转到 41:37】](https://www.youtube.com/watch?v=k4yBqddtPyQ&t=2497)：

- **Humphreys 等（2021）**：用 AlphaFold 与 RoseTTAFold 筛查 **830 万个酵母蛋白对**，标记出约 1500 个可能的相互作用，并为约 900 个组装体拿到高置信结构模型——这种规模是任何实验方法单独无法企及的，而置信度分数正是实现这种**优先级排序**的关键 [【跳转到 42:01】](https://www.youtube.com/watch?v=k4yBqddtPyQ&t=2521)；
- **Gu 等（2023）**：预测 **midnolin** 通过一段特定 β 链"停靠"在捕获域（catch domain）中来捕捉底物（如 IRF4）；随后在实验中**恰好删除/突变那段被预测的区域**，相互作用果然如模型所述被消除——堪称教科书级的验证 [【跳转到 42:26】](https://www.youtube.com/watch?v=k4yBqddtPyQ&t=2546)。

同时记住两条"反直觉"提醒 [【跳转到 43:00】](https://www.youtube.com/watch?v=k4yBqddtPyQ&t=2580)：

- **低分 ≠ 没有相互作用**：瞬态、柔性或固有无序区介导的结合常常被保守地打低分；
- **独立实验验证始终不可少**：这些分数是证据链上正当的一环，**但不是终点**。

---

## 小结

- 复合物的核心在**界面**：活性位点、结合口袋、变构位点常只在链间交界处形成，所以评价多聚体预测＝评价界面建模质量。
- **average pLDDT** 只说明各链自身折叠得好（必要不充分）；**PAE 矩阵的非对角块**是看界面的第一现场——深绿斑块可信，整块空白是红旗。
- **ipTM** 的算法本质是"用 PAE 代替真实误差的 TM-score"：逐残基选锚点 → 对另一条链平均 → 遍历取最大；>0.8 高置信，<0.6 链摆放多半有误。
- **ipSAE** 只统计 15 Å 内且 PAE < 10 Å 的残基对，剔除了无序尾巴的干扰；全长序列上低 ipTM + 较高 ipSAE ≠ 预测失败，先看 ipSAE；真假复合物分离度上 ipSAE 明显优于 ipTM。
- **pDockQ2** 给出有结构含义的阈值（>0.5 高质量界面）；**LIS** 专治"小而真"的局部接触，不会被界面其余部分稀释。
- 最终心法：**分数用于排序与分诊，配合生物学判断与实验验证使用；低分不等于无相互作用，实验验证永远是必需的一环。**

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| pLDDT | 逐残基局部打包质量分（0–100），以实验结构上的 LDDT 为训练目标 |
| LDDT | 局部距离差异检验：检查 15 Å 内 Cα 距离误差是否落在 0.5/1/2/4 Å 四档内 |
| PAE | 预测对齐误差：残基 x 相对残基 y 的预期位置误差（Å），矩阵不对称 |
| TM-score | 全局结构相似度：真实距离误差 / 长度因子 d0，取最优叠合，0–1 |
| pTM | 把 TM-score 公式中的真实误差换成 PAE 得到的整体折叠置信度 |
| ipTM | 跨链残基对的 pTM：链间相对定位置信度；>0.8 高置信，<0.6 多半摆错 |
| ipSAE | 只统计 15 Å 内且 PAE<10 Å 界面残基对的 ipTM 精修版，抗无序区干扰 |
| pDockQ2 | 链间平均 PAE 与界面残基平均 pLDDT 的加权组合，>0.5 为高质量界面 |
| LIS | 局部相互作用分数：只对低误差"小岛"残基对平均，适合柔性/无序结合 |
| 分诊 vs 判决 | 置信度分数用于排序候选、指导验证，不单独下生物学结论 |
