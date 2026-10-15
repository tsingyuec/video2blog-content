# The Definitive Guide to the Matthews Correlation Coefficient（马修斯相关系数完全指南）

> 视频来源：[The Definitive Guide to the Matthews Correlation Coefficient（YouTube）](https://www.youtube.com/watch?v=u-Ez7trpNrM)，时长约 9 分半（Data Science Bits，Felipe）。本文基于视频演说图文稿（YouTube 中文字幕）整理，时间戳可跳转到对应讲解。

## 本讲要解决的核心问题（SCQA）

**背景**：准确率（accuracy）是最常用的分类指标——判对多少除以总数，直观好用，也是混淆矩阵最自然的"浓缩"。

**冲突**：类别分布不平衡时，准确率会"说谎"：负类占绝对多数时，哪怕模型把所有样本都判成负类，准确率也照样很高。

**疑问**：有没有一个对不平衡分布更可靠、且能同等利用混淆矩阵全部四个格子的指标？

**回答（中心思想）**：马修斯相关系数（MCC，Matthews Correlation Coefficient）。它把预测与实际看作一次"相关性检验"：分子是 TP×TN − FP×FN，分母是恒为正的归一化常数，取值 **−1 到 1**。它对四个格子**同等加权**，在不平衡分布下远比准确率诚实。

## 一、回顾：混淆矩阵与准确率

用 0/1 表示类别：0 为负类，1 为正类。实际的 0 预测成 0 是真负类（TN），实际的 1 预测成 1 是真正类（TP）；对角线以外就是错误——假负类（FN）和假正类（FP）[【跳转到 01:16】](https://www.youtube.com/watch?v=u-Ez7trpNrM&t=76)。

![混淆矩阵：对角线为预测正确，反对角线为错误](assets/The%20Definitive%20Guide%20to%20the%20Matthews%20Correlation%20Coefficient/00046.webp)

准确率的分子是 TN + TP 之和，分母是混淆矩阵全部元素之和（即数据集的记录总数）[【跳转到 01:41】](https://www.youtube.com/watch?v=u-Ez7trpNrM&t=101)：

![准确率：对角线之和除以总数](assets/The%20Definitive%20Guide%20to%20the%20Matthews%20Correlation%20Coefficient/00101.webp)

## 二、MCC 公式：从"求和"到"乘积"

MCC 的公式比准确率复杂，视频点出两个关键区别 [【跳转到 02:06】](https://www.youtube.com/watch?v=u-Ez7trpNrM&t=126)：

- 准确率的分子是**求和**，MCC 的分子是**乘积**：TP×TN，再减去两类错误的乘积 FP×FN；
- 分子一共四项。分母则不必细究——它是一个**恒为正的归一化常数**，作用是把 MCC 压进 −1 到 1 之间（正如准确率的分母把结果压进 0 到 1）[【跳转到 02:31】](https://www.youtube.com/watch?v=u-Ez7trpNrM&t=151)。

写成标准形式：

**MCC = (TP×TN − FP×FN) / √((TP+FP)(TP+FN)(TN+FP)(TN+FN))**

![MCC 公式：分子为 TP×TN−FP×FN，分母为归一化常数](assets/The%20Definitive%20Guide%20to%20the%20Matthews%20Correlation%20Coefficient/00126.webp)

分母的四个括号分别是"预测为正""实际为正""预测为负""实际为负"的边缘和——只要四类不全为零，分母就恒为正。你不必背下分母，只要知道它把结果规整到 −1 到 1 之间即可 [【跳转到 02:31】](https://www.youtube.com/watch?v=u-Ez7trpNrM&t=151)。

![分母只是恒为正的归一化常数，把 MCC 保持在 −1 到 1](assets/The%20Definitive%20Guide%20to%20the%20Matthews%20Correlation%20Coefficient/00151.webp)

## 三、三个极限：0、+1、−1

视频用三个极端混淆矩阵确定 MCC 的取值范围 [【跳转到 02:56】](https://www.youtube.com/watch?v=u-Ez7trpNrM&t=176)：

- **MCC = 0**：对角线元素的乘积**等于**反对角线元素的乘积 → 分子 TP×TN − FP×FN = 0，预测与实际**不相关**（比如乱猜）[【跳转到 03:21】](https://www.youtube.com/watch?v=u-Ez7trpNrM&t=201)；
- **MCC = +1**：对角线元素为正、反对角线全为 0（FP = FN = 0）→ 完美预测 [【跳转到 03:46】](https://www.youtube.com/watch?v=u-Ez7trpNrM&t=226)；
- **MCC = −1**：对角线全为 0、反对角线非零（"反对角"矩阵）→ 全部预测反了 [【跳转到 04:11】](https://www.youtube.com/watch?v=u-Ez7trpNrM&t=251)。

![MCC = 1：完美的对角线混淆矩阵](assets/The%20Definitive%20Guide%20to%20the%20Matthews%20Correlation%20Coefficient/00226.webp)

![反对角矩阵：MCC = −1，全部预测反向](assets/The%20Definitive%20Guide%20to%20the%20Matthews%20Correlation%20Coefficient/00251.webp)

准确率只能落在 0 到 1 之间，而 MCC 取值横跨 −1 到 1——**信息量更大**：它能直接告诉你"模型在反向预测"这种极端情况 [【跳转到 04:36】](https://www.youtube.com/watch?v=u-Ez7trpNrM&t=276)。

## 四、阈值扫描 · 平衡分布

先看平衡分布：正负两个分布各含 1000 个样本，两曲线交叉。移动分类阈值（从 0 到 1），右侧生成各指标的曲线 [【跳转到 05:32】](https://www.youtube.com/watch?v=u-Ez7trpNrM&t=332)：

![平衡分布：两个各含 1000 样本的分布交叉](assets/The%20Definitive%20Guide%20to%20the%20Matthews%20Correlation%20Coefficient/00332.webp)

- 召回率**下降**、精确率**上升**，两者始终此消彼长 [【跳转到 05:57】](https://www.youtube.com/watch?v=u-Ez7trpNrM&t=357)；
- 在两分布交叉点，F1 分数达到最大值；
- 准确率趋势类似，某段与精确率曲线重合；阈值接近 0 处升到一个最大值（本例接近 F1 的最大值），随后下降并稳定 [【跳转到 06:22】](https://www.youtube.com/watch?v=u-Ez7trpNrM&t=382)；
- **MCC 的整体取值远低于准确率**，即使极端情况也非常接近 0 [【跳转到 06:47】](https://www.youtube.com/watch?v=u-Ez7trpNrM&t=407)。

![平衡分布：阈值扫描下 recall 降、precision 升](assets/The%20Definitive%20Guide%20to%20the%20Matthews%20Correlation%20Coefficient/00357.webp)

MCC "低调"是好事：在阈值接近 0 或 1 这些**最棘手的位置**，MCC 保持保守（低估而非虚高），不给你虚假的安全感。

## 五、阈值扫描 · 不平衡分布：准确率开始"说谎"

把分布改成不平衡：实际负样本 1000 个，正样本只有 100 个 [【跳转到 07:09】](https://www.youtube.com/watch?v=u-Ez7trpNrM&t=429)。再扫一遍阈值 [【跳转到 07:14】](https://www.youtube.com/watch?v=u-Ez7trpNrM&t=434)：

![不平衡分布：准确率在阈值接近 1 时虚高](assets/The%20Definitive%20Guide%20to%20the%20Matthews%20Correlation%20Coefficient/00434.webp)

- 准确率很快达到最大值后**高位平稳**，在阈值接近 1 的一侧值非常高——把一切判成负类就能白拿的高分；
- F1 与 MCC 的曲线非常接近、最大值位置相似，在这个区域被**强烈抑制** [【跳转到 07:39】](https://www.youtube.com/watch?v=u-Ez7trpNrM&t=459)。

![不平衡分布：准确率误导，F1 与 MCC 被抑制](assets/The%20Definitive%20Guide%20to%20the%20Matthews%20Correlation%20Coefficient/00459.webp)

很明显：**准确率在这个区域误导了你**——让你以为模型非常好，而 MCC 压得很低，反而诚实。视频里引用了数据科学博主 deepikaffa.ai 在 LinkedIn 上发的一个玩笑：分布不平衡时，各种性能指标都被"切进了蛋糕里"，看起来人人漂亮、皆大欢喜——但其实是在骗你 [【跳转到 08:04】](https://www.youtube.com/watch?v=u-Ez7trpNrM&t=484)。

## 六、什么时候用 MCC

视频给出的适用判据 [【跳转到 08:26】](https://www.youtube.com/watch?v=u-Ez7trpNrM&t=506)：

- 你的问题里，**负类和正类同等重要**；
- 真负类、真正类、假负类、假正类四种情况在你问题中**权重相同**。

![MCC 适用场景：正负类同等重要、四格子等权重](assets/The%20Definitive%20Guide%20to%20the%20Matthews%20Correlation%20Coefficient/00506.webp)

既然 MCC 实际上比准确率更好，那么在人们惯用准确率的场合，你应该考虑改用 MCC——或者至少**把两者都算出来对比**，真正理解模型结果 [【跳转到 08:51】](https://www.youtube.com/watch?v=u-Ez7trpNrM&t=531)。这也是本系列"分类算法性能指标"的收官一讲 [【跳转到 09:16】](https://www.youtube.com/watch?v=u-Ez7trpNrM&t=556)。

## 小结

- MCC 的分子是 TP×TN − FP×FN（预测与实际的"相关性"），分母是恒为正的归一化常数，取值 −1 到 1。
- 三个极限记住范围：不相关 = 0，完美 = +1，全部反向 = −1；比准确率的 [0, 1] 信息更多。
- 平衡分布下 MCC 低调保守，在阈值最棘手的位置不会虚高。
- 不平衡分布下准确率会"说谎"（全判负类也能高分），F1 与 MCC 则被诚实抑制——这正是要选它们的理由。
- 适用判据：正负类同等重要、四种情况等权重；惯用准确率的场合值得换成 MCC 或两者对比。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| MCC | 马修斯相关系数，混淆矩阵四个格子的"相关系数"，取值 −1~1 |
| 对角线乘积 TP×TN | 预测与实际一致部分的乘积，越大越好 |
| 反对角乘积 FP×FN | 两类错误的乘积，越大越差 |
| 平衡 / 不平衡分布 | 正负样本量相当 / 相差悬殊（如 1000:100） |
| 阈值扫描 | 移动判正阈值，观察各指标曲线变化 |
| 反对角矩阵 | 对角线全 0、全预测反了的极端混淆矩阵 |
