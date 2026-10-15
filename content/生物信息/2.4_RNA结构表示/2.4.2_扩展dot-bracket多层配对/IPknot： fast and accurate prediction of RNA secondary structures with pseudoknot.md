# IPknot：整数规划 + 分层近似，预测带假结的 RNA 二级结构

> 视频来源：[IPknot: fast and accurate prediction of RNA secondary structures with pseudoknots - Kengo Sato - ISMB/ECCB 2011](https://www.youtube.com/watch?v=zKMVPjOoW8s&t=0)（YouTube · ISMB/ECCB 2011 会议报告）
> 本文基于视频演说图文稿整理，配图截自视频。

## 一句话结论

假结（pseudoknot）是 RNA 二级结构中重要却难算的交叉配对拓扑：精确算法只能处理受限类别（预测全部类别是 NP 难，单序列 O(n⁴)–O(n⁶)），启发式算法覆盖广但可能不稳。讲者 Kengo Sato 的 IPknot 走第三条路：**把含假结的结构按"层"分解成若干无假结子结构，在碱基配对概率上按 MEA（最大期望准确度）原则用整数规划求最优解，再用"阈值裁剪"压缩搜索空间**——实验显示比现有假结方法更准、对比对误差更鲁棒、也更快。

## 一、背景：假结重要，但多数算法不允许

RNA 不只是信使，也是调控元件；结构与功能强相关。**假结是 RNA 二级结构中一类重要的拓扑**。讲者给出直观定义：把碱基对用弧线连出来、沿序列从 5' 描画到 3'，**只要有两段茎（配对区）相互交叉，这个结构就含假结**——经典例子是"简单 H 型假结"。 [【跳转到 01:49】](https://www.youtube.com/watch?v=zKMVPjOoW8s&t=109)

![简单 H 型假结：把碱基对画成弧线即可看出交叉](assets/IPknot：%20fast%20and%20accurate%20prediction%20of%20RNA%20secondary%20structures%20with%20pseudoknot/00109.webp)

生物学上，假结参与翻译的程序性移码与剪接，并辅助 RNA 在三维空间中的折叠。但"现有多数二级结构预测算法出于计算代价不允许任何假结"。 [【跳转到 02:39】](https://www.youtube.com/watch?v=zKMVPjOoW8s&t=159)

## 二、为什么难：精确与启发式的两难

现有假结预测方法大致分两类。 [【跳转到 03:04】](https://www.youtube.com/watch?v=zKMVPjOoW8s&t=184)

![现有方法的两类划分](assets/IPknot：%20fast%20and%20accurate%20prediction%20of%20RNA%20secondary%20structures%20with%20pseudoknot/00209.webp)

- **动态规划（精确算法）**：只能处理受限的假结类别——预测全部假结类别已被证明是 NP 难；对单条序列，时间复杂度按类别不同从 O(n⁴) 到 O(n⁶) 不等。
- **启发式算法**：能覆盖更广的类别，但可能损失预测能力。

雪上加霜的是概率化：连"可被 DP 预测的受限类别"，要精确计算其后验概率分布也需要 O(n⁶) 的不现实时间。IPknot 选择绕开精确计算。 [【跳转到 06:49】](https://www.youtube.com/watch?v=zKMVPjOoW8s&t=409)

## 三、方法概览：三步走

IPknot = **I**nteger **P**rogramming（整数规划）预测 RNA 假结结构。 [【跳转到 04:19】](https://www.youtube.com/watch?v=zKMVPjOoW8s&t=259)

![IPknot 方法概览](assets/IPknot：%20fast%20and%20accurate%20prediction%20of%20RNA%20secondary%20structures%20with%20pseudoknot/00259.webp)

1. **近似后验配对概率**（[04:44](https://www.youtube.com/watch?v=zKMVPjOoW8s&t=284)）：不精确计算含假结结构的配分函数，而是做近似；
2. **MEA 目标**（[05:34](https://www.youtube.com/watch?v=zKMVPjOoW8s&t=334)）：给定概率分布，预测使"收益函数"期望最大的结构——收益 = 真阳性与真阴性碱基对数目的加权和，权重 γ 平衡特异性与灵敏度。讲者强调，同一套 MEA 框架此前已实现为无假结预测器 **CentroidFold**——"不含假结的 RNA 二级结构预测中最好的工具之一"；
3. **整数规划求解**（[11:49](https://www.youtube.com/watch?v=zKMVPjOoW8s&t=709)）：把"每一层选哪些配对"写成 0-1 变量的优化问题，交给 IP 求解器（实现支持两个商业求解器和一个免费求解器）。

## 四、三个关键机制

**① 分层（level）因子分解**（[07:39](https://www.youtube.com/watch?v=zKMVPjOoW8s&t=459)）。把含假结结构的概率分布按层级分解——每个因子是一个规范（无假结）子结构上的分布，这些子结构称为"层"；分解后各项都能在 O(n³) 内算出，目标函数也变成各层期望收益之和。 [【跳转到 07:39】](https://www.youtube.com/watch?v=zKMVPjOoW8s&t=459)

![分层因子分解：含假结结构按层拆解](assets/IPknot：%20fast%20and%20accurate%20prediction%20of%20RNA%20secondary%20structures%20with%20pseudoknot/00459.webp)

**② 碱基配对概率矩阵**（[08:54](https://www.youtube.com/watch?v=zKMVPjOoW8s&t=534)）。p_ij = 第 i、j 个碱基配对的概率；整张矩阵可用 ViennaRNA 包中基于 Boltzmann 参数的程序在 O(n³) 内算出，IPknot 的实现即基于此。 [【跳转到 08:54】](https://www.youtube.com/watch?v=zKMVPjOoW8s&t=534)

![碱基配对概率矩阵](assets/IPknot：%20fast%20and%20accurate%20prediction%20of%20RNA%20secondary%20structures%20with%20pseudoknot/00534.webp)

**③ 阈值裁剪（threshold cut）**（[10:09](https://www.youtube.com/watch?v=zKMVPjOoW8s&t=609)）。逐层用自适应阈值筛配对：被选中的碱基对必须配对概率为正，且解要满足一致性约束——每个碱基至多配一个、层级化分解、分解唯一。它大幅压缩搜索空间，**即便用免费 IP 求解器，IPknot 也足够快**。 [【跳转到 10:09】](https://www.youtube.com/watch?v=zKMVPjOoW8s&t=609)

![阈值裁剪：压缩搜索空间](assets/IPknot：%20fast%20and%20accurate%20prediction%20of%20RNA%20secondary%20structures%20with%20pseudoknot/00609.webp)

另外，IPknot 还能扩展到**共识（consensus）结构预测**：把多条同源序列的平均配对概率喂给同一个 IP 程序即可。 [【跳转到 14:29】](https://www.youtube.com/watch?v=zKMVPjOoW8s&t=869)

## 五、实验：更准、更稳、更快

**单序列，PK-388 数据集**（388 条取自 RNA STRAND 数据库、参考结构均含假结）：在 PPV–灵敏度散点图上，IPknot（红点，γ 扫描）落在最靠右上角的位置，MCC 为所有参数中最高；现有假结方法为蓝点，无假结方法为黑点。 [【跳转到 15:44】](https://www.youtube.com/watch?v=zKMVPjOoW8s&t=944)

![PK-388 上的 PPV–灵敏度图](assets/IPknot：%20fast%20and%20accurate%20prediction%20of%20RNA%20secondary%20structures%20with%20pseudoknot/00944.webp)

**多序列共识预测**（取自 Rfam 的 67 个比对）：IPknot 对比对误差更鲁棒——高质量结构比对非常昂贵，鲁棒性是实打实的优点。 [【跳转到 18:19】](https://www.youtube.com/watch?v=zKMVPjOoW8s&t=1099)

**时间性能**（五条不同长度序列）：IPknot 比现有假结方法快得多，与无假结方法速度相当。 [【跳转到 19:36】](https://www.youtube.com/watch?v=zKMVPjOoW8s&t=1176)

![时间性能对比](assets/IPknot：%20fast%20and%20accurate%20prediction%20of%20RNA%20secondary%20structures%20with%20pseudoknot/01176.webp)

## 六、边界说明与延伸阅读

- 这场 2011 年的报告聚焦方法本身，**未展示** `() {} []` 多层括号记法的具体写法；IPknot 的"层"可视为"多层配对"思想的算法化——含假结的结构被拆成若干层无假结子结构分别处理。
- 视频也未涉及 ViennaRNA 的 RNAcentroid（系综中心结构）工具。
- 单层 dot-bracket 记法本身见同系列上一篇 [《RNA Folding： How to Use Dot-Bracket Notation》](../2.4.1_dot-bracket/RNA%20Folding：%20How%20to%20Use%20Dot-Bracket%20Notation.md)；MIT 第 11 讲从记法讲到 Nussinov 动态规划与"交叉弧线难算"的分界（[《11. RNA Secondary Structure; Biological Functions and Predictions》](11.%20RNA%20Secondary%20Structure;%20Biological%20Functions%20and%20Predictions.md)）。
