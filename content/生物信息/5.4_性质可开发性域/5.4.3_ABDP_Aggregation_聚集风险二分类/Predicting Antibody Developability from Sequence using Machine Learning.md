# Predicting Antibody Developability from Sequence using Machine Learning

> 来源视频：[Predicting Antibody Developability from Sequence using Machine Learning](https://www.youtube.com/watch?v=0CcVCrUtWsk)（YouTube，4 分 26 秒，en-orig 原声字幕）。本文基于该视频的「图-字幕」演说稿整理，所有结论均出自视频画面与口播，内容可核查。

## 本讲要解决的核心问题（SCQA）

**背景**：抗体的可开发性指数（Developability Index，DI）度量抗体形成聚集的倾向——从抗体结构计算出来，再用来给候选抗体排序，提前筛掉易聚集的分子。

**冲突**：DI 依赖结构，而结构的确定（实验解析或计算建模）都可能有成本；候选抗体序列成百上千，逐个建模不现实。

**疑问**：能不能跳过结构，直接从氨基酸序列判断一个抗体"高/低可开发"？

**回答（中心思想）**：可以。视频展示了完整做法：用 SAbDab 抗体结构库计算 DI 作为标签（二分类），把序列特征化后组合训练 532 个机器学习模型，用混淆矩阵与 ROC AUC 评估，最优组合是"随机森林 + MSA 理化特征"，并诚实报告了验证集上的过拟合信号。这正是可开发性平台里"聚集风险二分类"的一种实现思路。

## 一、DI：从结构算出的"聚集倾向分"

DI 的定义与动机 [【跳转到 00:09】](https://www.youtube.com/watch?v=0CcVCrUtWsk&t=9)、[【跳转到 00:14】](https://www.youtube.com/watch?v=0CcVCrUtWsk&t=14)：

- DI 是抗体聚集倾向的度量，从抗体结构计算，用于抗体之间的排序；
- 但确定结构——无论实验解析还是计算建模——都可能有成本，这就是"从序列直接预测"的动机。

![DI 的定义与"从序列直接预测"的动机](assets/Predicting%20Antibody%20Developability%20from%20Sequence%20using%20Machine%20Learning/00014.webp)

## 二、四步工作流：特征化 → 打标签 → 训练 → 评估

工作流分四部分 [【跳转到 00:37】](https://www.youtube.com/watch?v=0CcVCrUtWsk&t=37)：序列特征化；把抗体标注为高/低可开发性；训练机器学习模型；评估模型性能并挑选最优模型与超参数 [【跳转到 00:42】](https://www.youtube.com/watch?v=0CcVCrUtWsk&t=42)。

整个工作流在 **BIOVIA Pipeline Pilot**（可视化编程与流水线工具）中实现：自动完成抗体标注 [【跳转到 00:42】]、序列特征化，以及数百个不同模型的构建与评估 [【跳转到 01:07】](https://www.youtube.com/watch?v=0CcVCrUtWsk&t=67)。

![四步工作流与 Pipeline Pilot](assets/Predicting%20Antibody%20Developability%20from%20Sequence%20using%20Machine%20Learning/00042.webp)

## 三、数据与标签：SAbDab + Discovery Studio 计算 DI

- 抗体结构来自 **SAbDab**（Structural Antibody Database，结构抗体数据库）[【跳转到 01:13】](https://www.youtube.com/watch?v=0CcVCrUtWsk&t=73)。

![SAbDab：结构抗体数据库](assets/Predicting%20Antibody%20Developability%20from%20Sequence%20using%20Machine%20Learning/00073.webp)
- **BIOVIA Discovery Studio** 经 Pipeline Pilot 自动化：清洗 PDB 结构文件与序列，并计算各结构的 DI [【跳转到 01:18】](https://www.youtube.com/watch?v=0CcVCrUtWsk&t=78)。
- 标签划分：DI 中 20% 标为"高可开发"，其余 80% 标为"低"——模型要预测新抗体序列属于哪一类 [【跳转到 01:18】]。聚集倾向直接决定这个二分类标签，因此它本质上就是"聚集风险二分类"。

![SAbDab 数据与 20/80 标签](assets/Predicting%20Antibody%20Developability%20from%20Sequence%20using%20Machine%20Learning/00078.webp)

## 四、特征与模型：532 个模型的组合搜索

- **特征化** [【跳转到 01:43】](https://www.youtube.com/watch?v=0CcVCrUtWsk&t=103)、[【跳转到 01:48】](https://www.youtube.com/watch?v=0CcVCrUtWsk&t=108)：理化特征（由 EMBOSS pepstats、ExPASy ProtParam 计算）+ Python 实现的学习型嵌入（learned embeddings）。
- **组合搜索与评估** [【跳转到 02:05】](https://www.youtube.com/watch?v=0CcVCrUtWsk&t=125)：用 Pipeline Pilot 组合训练模型；10 折交叉验证为每种模型类型确定最优超参数；全部模型建好后，在测试数据集上评估，计算混淆矩阵与 ROC AUC。
- **规模** [【跳转到 02:30】](https://www.youtube.com/watch?v=0CcVCrUtWsk&t=150)、[【跳转到 02:35】](https://www.youtube.com/watch?v=0CcVCrUtWsk&t=155)：共 532 个模型，覆盖 6 种模型类型 + 随机对照，76 种特征集。

![特征化：理化特征 + 学习型嵌入](assets/Predicting%20Antibody%20Developability%20from%20Sequence%20using%20Machine%20Learning/00108.webp)

![组合训练与评估流程](assets/Predicting%20Antibody%20Developability%20from%20Sequence%20using%20Machine%20Learning/00125.webp)

## 五、读结果：AUC 热图与最优模型

热图（x 轴 = 模型类型，y 轴 = 特征集）展示每个模型 ROC 曲线下面积（AUC）[【跳转到 02:35】]：

- 理化特征与 k-mer 长度 2、3、4 的嵌入特征表现最好；
- 支持向量机（SVM）、随机森林、XGBoost 三类模型优于多层感知机（MLP）、高斯朴素贝叶斯与逻辑回归 [【跳转到 03:00】](https://www.youtube.com/watch?v=0CcVCrUtWsk&t=180)；
- 总体最优：**随机森林 + MSA（多序列比对）理化特征**。

![模型 × 特征集的 AUC 热图](assets/Predicting%20Antibody%20Developability%20from%20Sequence%20using%20Machine%20Learning/00155.webp)

## 六、诚实的一课：验证集上的过拟合信号

把模型在验证集上的表现与训练集对比 [【跳转到 03:23】](https://www.youtube.com/watch?v=0CcVCrUtWsk&t=203)、[【跳转到 03:28】](https://www.youtube.com/watch?v=0CcVCrUtWsk&t=208)：

- 不同模型类型的 sensitivity 与 Cohen's kappa 在验证集上出现陡降；
- balanced error rate 上升；
- 随机森林在所有特征集上也有类似趋势。

作者把这视为需要改进的方向，留待后续研究 [【跳转到 03:53】](https://www.youtube.com/watch?v=0CcVCrUtWsk&t=233)。

![过拟合：验证集 vs 训练集](assets/Predicting%20Antibody%20Developability%20from%20Sequence%20using%20Machine%20Learning/00208.webp)

## 小结

- 可行性得到验证：机器学习可以直接从序列预测抗体可开发性（DI 高/低二分类）[【跳转到 03:59】](https://www.youtube.com/watch?v=0CcVCrUtWsk&t=239)。
- 最优组合：随机森林 + MSA 理化特征；理化特征与 k-mer 2/3/4 嵌入特征总体最好。
- 评估用混淆矩阵与 ROC AUC；同时观察到验证集 sensitivity、Cohen's kappa 下降与 balanced error rate 上升的过拟合信号。
- 更多细节见同题 preprint（bioRxiv）[【跳转到 04:04】](https://www.youtube.com/watch?v=0CcVCrUtWsk&t=244)；工作主要由 Harvey Mudd College 的学生与教授完成 [【跳转到 04:09】](https://www.youtube.com/watch?v=0CcVCrUtWsk&t=249)。

![总结页](assets/Predicting%20Antibody%20Developability%20from%20Sequence%20using%20Machine%20Learning/00239.webp)

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| DI（Developability Index，可开发性指数） | 度量抗体聚集倾向的分数，从抗体结构计算，用于抗体间排序 |
| SAbDab | Structural Antibody Database，结构抗体数据库，本工作的结构来源 |
| BIOVIA Pipeline Pilot | 可视化编程与流水线工具，自动化标注、特征化与模型训练评估 |
| 特征化（featurization） | 把氨基酸序列转成数值特征（理化性质、学习型嵌入等） |
| k-mer | 连续 k 个氨基酸的片段，本工作用 k=2/3/4 构建嵌入特征 |
| 10 折交叉验证 | 数据分 10 份轮流做验证，为每种模型类型选最优超参数 |
| 混淆矩阵 / ROC AUC | 二分类性能评估工具：看模型把高/低可开发性分对了多少 |
| 过拟合 | 训练集表现好、验证集变差；本工作表现为 sensitivity 与 Cohen's kappa 下降、balanced error rate 上升 |
