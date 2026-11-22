# Boltz-2 特性与实战：五大特性、四条局限，以及在 Rowan 平台跑通蛋白-配体共折叠

> 视频来源：B 站《To use Boltz-2 for affinity predictions》（UP：Asha Ahmed），[BV1mANUzVErw](https://www.bilibili.com/video/BV1mANUzVErw/)。
> 本文基于该视频的「图-字幕」演说文稿整理，所有关键操作与数字都可在原视频中核查。

## 本讲要解决的核心问题（SCQA）

**背景**：共折叠工具（AlphaFold3、Protenix、Chai-1 等）已经能一次预测「蛋白 + 配体」复合物的结构，并附上 pTM/ipTM 置信度（见 3.1）。但药物设计真正关心的下一个问题是：**结合得有多强**？

**冲突**：在 Boltz-2 之前，这些程序通常只提供 pTM/ipTM 分数，不直接给亲和力；而专门的亲和力手段（自由能扰动 FEP、分子动力学 MD）计算成本高、周期长。

**疑问**：有没有模型能在一次共折叠预测里，顺手把亲和力也算出来？

**回答（中心思想）**：Boltz-2 做到了——它在 pTM/ipTM 之外**直接输出亲和力分数与物理有效性评估**，结构预测在 RNA/DNA-蛋白复合物上表现最佳。本讲先盘点它的**五大特性与使用局限**，再以 Rowan 平台为例，走通「注册 → 填蛋白序列与配体 SMILES → 提交共折叠 → 读 pKd 与结合概率」的完整实操。

![开场：Asha Ahmed 与本讲主题——用 Boltz-2 做亲和力预测](assets/To%20use%20Boltz-2%20for%20affinity%20predictions/00000.webp)

## 一、定位：第一次把「亲和力」塞进共折叠的模型

Boltz-2 由一个基于 MIT 的研究小组开发，是 Boltz 系列的新版本，目前在科学界很流行——因为它把**计算结合亲和力**的能力做到了同类第一梯队：视频制作时，Boltz-1/Boltz-2 系列已经能直接计算蛋白与小分子的亲和力，而 Chai-1、AlphaFold3、Protenix 等程序的跟进还在预期之中 [【跳转到 00:50】](https://www.bilibili.com/video/BV1mANUzVErw/?t=50)、[【跳转到 01:15】](https://www.bilibili.com/video/BV1mANUzVErw/?t=75)。

结构预测本身也没落下。在 PDB 数据集的评估中，Boltz-1/Boltz-2 与 Chai-1、AlphaFold3、Protenix 比较：**在 RNA/DNA-蛋白质复合物上表现最佳**，其他类别仍然可比，个别类别 AlphaFold3 稍好 [【跳转到 01:45】](https://www.bilibili.com/video/BV1mANUzVErw/?t=105)、[【跳转到 02:10】](https://www.bilibili.com/video/BV1mANUzVErw/?t=130)。

关键的跃迁在输出上：过去程序在给出亲和力之前，通常只提供 pTM 或 ipTM 分数；Boltz-2 在此基础上**直接给出亲和力分数，外加物理有效性（physical validity）评估**，几乎全面超越其他程序——对结构预测与亲和力两者都是如此 [【跳转到 02:35】](https://www.bilibili.com/video/BV1mANUzVErw/?t=155)、[【跳转到 03:00】](https://www.bilibili.com/video/BV1mANUzVErw/?t=180)。

![评估图表：Boltz 系列与 Chai-1/AF3/Protenix 在 PDB 数据集上的比较](assets/To%20use%20Boltz-2%20for%20affinity%20predictions/00105.webp)

![Boltz-2 的新输出：亲和力分数 + 物理有效性](assets/To%20use%20Boltz-2%20for%20affinity%20predictions/00180.webp)

## 二、五大特性速览

按视频的展开顺序，Boltz-2 的特性可以归成五组 [【跳转到 01:15】](https://www.bilibili.com/video/BV1mANUzVErw/?t=75)：

1. **亲和力分数**：与结构一起输出，见上一节；
2. **物理有效性**：对预测结果做物理合理性检验 [【跳转到 03:25】](https://www.bilibili.com/video/BV1mANUzVErw/?t=205)；
3. **局部蛋白质动力学**：Boltz-2 给出的不是静态刚性结构，它能理解**局部环区（loop）与二级结构的变化** [【跳转到 03:30】](https://www.bilibili.com/video/BV1mANUzVErw/?t=210)、[【跳转到 03:55】](https://www.bilibili.com/video/BV1mANUzVErw/?t=235)。注意：**不要把它与大规模分子动力学（MD）研究混淆**——这里说的是局部动力学。直觉上，对接若是柔性的而非刚性的，成功率更高 [【跳转到 04:20】](https://www.bilibili.com/video/BV1mANUzVErw/?t=260)。这一项的评测指标包括 Spearman / Pearson 相关系数、召回率（recall）与多样性（diversity）；
4. **基于物理的自由能扰动（FEP）**：用不同基准检验，Boltz-2 在一些地方勉强持平、在另一些地方完全出色 [【跳转到 04:51】](https://www.bilibili.com/video/BV1mANUzVErw/?t=291)；
5. **大规模虚拟筛选**：Boltz 系列都可用于虚拟筛选，视频给出了效率/性能/平均精度的分析 [【跳转到 05:16】](https://www.bilibili.com/video/BV1mANUzVErw/?t=316)。

![局部动力学：Boltz-2 能理解环区与二级结构的柔性变化](assets/To%20use%20Boltz-2%20for%20affinity%20predictions/00210.webp)

![FEP 基准：部分持平、部分出色](assets/To%20use%20Boltz-2%20for%20affinity%20predictions/00291.webp)

![虚拟筛选：效率与平均精度分析](assets/To%20use%20Boltz-2%20for%20affinity%20predictions/00316.webp)

作者强烈建议阅读论文本身：《Boltz-2: Towards Accurate and Efficient Binding Affinity Prediction》——免费获取、非常详细；如果你想理解整件事，就去读它 [【跳转到 05:41】](https://www.bilibili.com/video/BV1mANUzVErw/?t=341)、[【跳转到 08:05】](https://www.bilibili.com/video/BV1mANUzVErw/?t=485)。

## 三、局限与使用须知

「用之前先知道它不能干什么」——视频在进入教程前专门讲了限制 [【跳转到 05:56】](https://www.bilibili.com/video/BV1mANUzVErw/?t=356)：

- **不提供结合能量分解**。Boltz-2 给出的是 pIC50 形式的结合亲和力——实际上它并不直接给出 pIC50 的值，而是一个原始数值；
- **数值需要转换**：接下来要介绍的程序（Rowan）会自动把该值转换为结合自由能或 pIC50 [【跳转到 06:21】](https://www.bilibili.com/video/BV1mANUzVErw/?t=381)；
- **只适用于蛋白-配体**（更准确说，配体是有机分子的情况）；**蛋白-蛋白相互作用的结合亲和力，Boltz-2 不提供** [【跳转到 06:46】](https://www.bilibili.com/video/BV1mANUzVErw/?t=406)；
- **不能替代大规模分子动力学**：它适合局部动力学研究与结合亲和力。

还有一条方法论层面的提醒：**不要盲目相信这些 AI 程序**。它们训练于特定描述符与数据集，结合亲和力的训练数据来自不同实验、在不同条件下测得，这些差异可能影响你的研究结论 [【跳转到 07:11】](https://www.bilibili.com/video/BV1mANUzVErw/?t=431)、[【跳转到 07:36】](https://www.bilibili.com/video/BV1mANUzVErw/?t=456)。

![局限说明：不提供结合能量分解，仅限蛋白-配体](assets/To%20use%20Boltz-2%20for%20affinity%20predictions/00356.webp)

## 四、教程环境：为什么这次不跑 Colab

作者此前通常在 Colab 上做免费教程，但这次没有：Boltz-2 需要安装一些外部依赖，而 Colab 的免费 T4 GPU、甚至专业版的 L4 与 A100 GPU，到视频制作时都还跑不动它。一旦跑通，作者会再出免费教程 [【跳转到 09:04】](https://www.bilibili.com/video/BV1mANUzVErw/?t=544)、[【跳转到 09:29】](https://www.bilibili.com/video/BV1mANUzVErw/?t=569)。

替代方案是 **Rowan**——一个机器学习驱动的分子设计与模拟平台（浏览器输入 rowan 即可找到），其中的共折叠任务使用的底层模型就是 Boltz-2 [【跳转到 09:57】](https://www.bilibili.com/video/BV1mANUzVErw/?t=597)、[【跳转到 11:37】](https://www.bilibili.com/video/BV1mANUzVErw/?t=697)。

![Rowan 平台：机器学习驱动的分子设计与模拟](assets/To%20use%20Boltz-2%20for%20affinity%20predictions/00597.webp)

## 五、Rowan 实操全流程：从注册到提交

按视频的操作顺序 [【跳转到 11:12】](https://www.bilibili.com/video/BV1mANUzVErw/?t=672)：

1. **注册账户**：Rowan 并未对所有国家开放注册，未开放地区的用户需要自行想办法 [【跳转到 10:22】](https://www.bilibili.com/video/BV1mANUzVErw/?t=622)；注册后赠送 **100 个免费信用点（credits）**，据作者记忆每周还会补约 20 个（以官网说明为准）[【跳转到 10:47】](https://www.bilibili.com/video/BV1mANUzVErw/?t=647)；
2. **找到入口**：登录后向下滚动，在 **Drug Discovery（药物发现）** 分区点击 **Protein-Ligand Co-Folding（蛋白质-配体共折叠）**，再点「运行新的蛋白质-配体共折叠」——它使用的模型就是 Boltz-2 [【跳转到 11:37】](https://www.bilibili.com/video/BV1mANUzVErw/?t=697)；
3. **填蛋白侧**：粘贴你的蛋白序列（示例用 EGFR），再给工作流起个名字 [【跳转到 11:37】](https://www.bilibili.com/video/BV1mANUzVErw/?t=697)；
4. **填配体侧**：输入配体 **SMILES**，或直接在表单里绘制。SMILES 从哪来？去 **PubChem** 搜化合物名（示例：对乙酰氨基酚 acetaminophen），把 SMILES 复制过来粘贴即可 [【跳转到 12:39】](https://www.bilibili.com/video/BV1mANUzVErw/?t=759)；
5. **可选项**：需要时可以使用 MSA 服务器，否则不用管 [【跳转到 12:44】](https://www.bilibili.com/video/BV1mANUzVErw/?t=764)；
6. **提交**：序列与 SMILES 都填好后，提交按钮激活；费用按结构与配体状态计——作者的第一单扣了 **9.4 个信用点**，账户剩 90.59 [【跳转到 13:09】](https://www.bilibili.com/video/BV1mANUzVErw/?t=789)。

![co-folding 入口：Drug Discovery 分区](assets/To%20use%20Boltz-2%20for%20affinity%20predictions/00672.webp)

![填蛋白序列与工作流名称](assets/To%20use%20Boltz-2%20for%20affinity%20predictions/00697.webp)

![去 PubChem 检索化合物的 SMILES](assets/To%20use%20Boltz-2%20for%20affinity%20predictions/00759.webp)

![提交与扣费：第一单 9.4 信用点](assets/To%20use%20Boltz-2%20for%20affinity%20predictions/00789.webp)

## 六、读懂结果：pKd、结合概率与 PDB 下载

结果页用一个已完成的任务演示：蛋白是 **NDM-1**（一种 β-金属内酰胺酶），配体是简单的**青霉素（penicillin）**分子——SMILES 取自 PubChem [【跳转到 13:43】](https://www.bilibili.com/video/BV1mANUzVErw/?t=823)：

- **pKd = 5.147**：预测的 pKd 值，**越高越好**；
- **结合概率 ≈ 0.97（97%）**：结合概率与置信度分数的取值都在 **0 到 1** 之间，**越接近 1 信心水平越高** [【跳转到 14:08】](https://www.bilibili.com/video/BV1mANUzVErw/?t=848)；
- **下载结构**：点击下载即可拿到 PDB 文件，在 Discovery Studio、PyMOL 等查看器中打开分析 [【跳转到 14:33】](https://www.bilibili.com/video/BV1mANUzVErw/?t=873)。

![结果矩阵：pKd 5.147](assets/To%20use%20Boltz-2%20for%20affinity%20predictions/00823.webp)

![结合概率与置信度：0~1，越高越好](assets/To%20use%20Boltz-2%20for%20affinity%20predictions/00848.webp)

![一键下载 PDB，用 Discovery Studio / PyMOL 查看](assets/To%20use%20Boltz-2%20for%20affinity%20predictions/00873.webp)

作者最后提醒：**信用点省着用**，别一次烧完——把 Boltz-2 当成自己实验里的工具，细水长流 [【跳转到 15:10】](https://www.bilibili.com/video/BV1mANUzVErw/?t=910)。

## 小结

- Boltz-2 的核心跃迁：在 pTM/ipTM 之外**直接输出亲和力分数 + 物理有效性**；结构预测在 RNA/DNA-蛋白复合物上最佳。
- 五大特性：亲和力分数、物理有效性、局部动力学（柔性）、FEP 基准、大规模虚拟筛选。
- 四条局限：无结合能量分解；数值需转换（如 Rowan 自动转 pIC50 / 结合自由能）；仅限蛋白-有机小分子配体（无蛋白-蛋白亲和力）；不能替代大规模 MD。
- Rowan 实操五步：注册领 100 信用点 → Drug Discovery 的 Protein-Ligand Co-Folding → 填蛋白序列 + 配体 SMILES（PubChem 检索）→ 提交扣点（示例 9.4）→ 读 pKd 与结合概率。
- NDM-1 + 青霉素示例：pKd 5.147，结合概率 ≈0.97；pKd 越高越好，概率/置信度 0~1 越接近 1 越好。
- 方法论提醒：AI 预测基于特定训练数据、条件各异，**不要盲信**；使用 Boltz-2 记得引用论文。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| 共折叠（co-folding） | 把多个分子（蛋白+配体等）放进同一个预测任务，一起出复合物结构 |
| pKd | 解离常数 Kd 的负对数，衡量结合强度，越高结合越强（见 1.5.1） |
| pIC50 | 抑制浓度 IC50 的负对数，同样是「越高结合越强」的亲和力刻度 |
| 结合自由能（ΔG） | 结合的热力学度量，越负越有利；可由 Boltz-2 原始数值转换而来 |
| FEP（自由能扰动） | 基于物理模拟的亲和力计算方法，精确但昂贵；Boltz-2 以其为对照基准之一 |
| SMILES | 分子的线性文本表示（见 1.3.1），在 Rowan 表单中直接粘贴 |
| MSA 服务器 | 多序列比对在线服务（见 2.3.1），共折叠的可选输入 |
| 信用点（credits） | Rowan 平台计费单位，注册赠 100，按任务扣费 |
