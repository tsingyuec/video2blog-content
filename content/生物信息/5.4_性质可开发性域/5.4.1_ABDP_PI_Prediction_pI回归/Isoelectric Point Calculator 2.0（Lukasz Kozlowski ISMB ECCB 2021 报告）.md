# Isoelectric Point Calculator 2.0（IPC 2.0 原作者报告）

> 来源视频：[Isoelectric Point Calculator 2.0 - Lukasz Kozlowski - CompMS - Talk - ISMB/ECCB 2021](https://www.youtube.com/watch?v=T8USjl-Kdg8)（YouTube，8 分 39 秒，ISCB 频道）。本文基于该视频的「图-字幕」演说稿整理，并经幻灯片画面核对，所有结论均出自视频，内容可核查。

## 本讲要解决的核心问题（SCQA）

**背景**：等电点（pI）是蛋白质的基础理化参数——2D 凝胶电泳（2D-PAGE）、毛细管等电聚焦、X-射线晶体学、液相色谱-质谱（LC-MS）都要用到它。

**冲突**：经典预测法是"Henderson–Hasselbalch 公式 + 实验测定的 pKa 值"，但不同实验条件下 pKa 值略有差异，预测准度受限；想更准可以走结构路线（如 Rosetta），但需要结构模型、每个蛋白要算几个小时。

**疑问**：能不能只靠序列，又快又准地预测 pI——甚至把每个带电残基的 pKa 也一并预测出来？

**回答（中心思想）**：可以。报告人 Łukasz Kozlowski（华沙大学）发布的 IPC 2.0（2021）用深度学习取代了 IPC 1.0（2016）的 pKa 优化：蛋白与肽段分别建模，pI 与 pKa 同时预测，基准测试平均更准，而且几秒钟就能出结果。

## 一、等电点：电荷平衡的那个 pH

### 1.1 定义与"电荷随 pH 变化"

等电点是分子表面正、负电荷数量达到平衡（净电荷为零）时的 pH [【跳转到 00:11】](https://www.youtube.com/watch?v=T8USjl-Kdg8&t=11)。谈蛋白质时要始终记住：分子的带电状态随环境 pH 而不同 [【跳转到 00:25】](https://www.youtube.com/watch?v=T8USjl-Kdg8&t=25)——低 pH 时蛋白表面带大量正电荷；到了某个 pH，正负电荷达到平衡，这就是等电点；更高的 pH 下则带负电 [【跳转到 00:50】](https://www.youtube.com/watch?v=T8USjl-Kdg8&t=50)。

报告人用 GFP（绿色荧光蛋白）举例：它是一个研究得很透的蛋白，分子量 26.9 kDa（238 aa）、等电点 5.8——在 pH=2 时质子化、带正电；pH=5.8 时净电荷为零；pH=10 时去质子化、带负电。同一蛋白在细胞里也面对不同 pH 环境：细胞质 pH 7.4、溶酶体 pH 5.5、线粒体 pH 8.0，所以在不同区室里它带的电荷并不一样 [【跳转到 00:25】](https://www.youtube.com/watch?v=T8USjl-Kdg8&t=25)。

![GFP 示例：pH=2 带正电、pH=5.8（pI）净电荷为零、pH=10 带负电，以及细胞内不同区室的 pH](assets/Isoelectric%20Point%20Calculator%202.0%EF%BC%88Lukasz%20Kozlowski%20ISMB%20ECCB%202021%20%E6%8A%A5%E5%91%8A%EF%BC%89/00025.webp)

### 1.2 生物与技术后果：吸引与排斥

当环境 pH 接近蛋白的等电点时，分子之间相互吸引；而在高于或低于等电点的 pH 下，分子之间会相互分开、彼此排斥 [【跳转到 01:00】](https://www.youtube.com/watch?v=T8USjl-Kdg8&t=60)、[【跳转到 01:25】](https://www.youtube.com/watch?v=T8USjl-Kdg8&t=85)。这在生物和技术层面都有重要影响 [【跳转到 00:50】](https://www.youtube.com/watch?v=T8USjl-Kdg8&t=50)。

## 二、为什么想"预测" pI：三个实验场景

这一性质被许多实验技术利用，也正是我们想提前算出 pI 的原因：

1. **X-射线晶体学**：想要长出漂亮的蛋白晶体，就应避免使用 pH 接近靶蛋白等电点的缓冲液（否则蛋白因静电吸引而聚集）[【跳转到 01:35】](https://www.youtube.com/watch?v=T8USjl-Kdg8&t=95)。
2. **2D-PAGE（二维凝胶电泳）**：一维按等电点分离蛋白，再把胶泡进 SDS 溶液、转到 SDS-PAGE 上按分子量做第二维分离——单张 2D 胶上可以分出约 1000 个大肠杆菌蛋白 [【跳转到 01:53】](https://www.youtube.com/watch?v=T8USjl-Kdg8&t=113)。
3. **质谱（LC-MS）**：按等电点对蛋白分组（fraction），可以让分析更简单 [【跳转到 02:13】](https://www.youtube.com/watch?v=T8USjl-Kdg8&t=133)。

![2D-PAGE 流程：先按 pI 分离，泡 SDS 后再按分子量跑 SDS-PAGE](assets/Isoelectric%20Point%20Calculator%202.0%EF%BC%88Lukasz%20Kozlowski%20ISMB%20ECCB%202021%20%E6%8A%A5%E5%91%8A%EF%BC%89/00113.webp)

![X-射线晶体学流程：晶体 → 衍射图样 → 电子密度图 → 蛋白模型，长晶体要避开 pH≈pI 的缓冲液](assets/Isoelectric%20Point%20Calculator%202.0%EF%BC%88Lukasz%20Kozlowski%20ISMB%20ECCB%202021%20%E6%8A%A5%E5%91%8A%EF%BC%89/00095.webp)

把这些场景结合起来，就产生了对"预测等电点"的实际需求 [【跳转到 02:30】](https://www.youtube.com/watch?v=T8USjl-Kdg8&t=150)。

## 三、IPC 2.0 怎么用：网页版一分钟上手

### 3.1 工具形态与输入

为此可以使用报告人的工具 IPC：既有网页版（web server），也有独立程序（standalone）[【跳转到 02:35】](https://www.youtube.com/watch?v=T8USjl-Kdg8&t=155)。网页版里贴入蛋白或肽段序列即可——单条序列用纯文本，多条序列用 FASTA 格式；数据量更大时，官网建议使用独立程序版本（网页版一次约需 20 秒）[【跳转到 02:35】](https://www.youtube.com/watch?v=T8USjl-Kdg8&t=155)。

![IPC 2.0 网页版：贴入序列即可计算，支持蛋白与肽段、单条或多条 FASTA](assets/Isoelectric%20Point%20Calculator%202.0%EF%BC%88Lukasz%20Kozlowski%20ISMB%20ECCB%202021%20%E6%8A%A5%E5%91%8A%EF%BC%89/00155.webp)

### 3.2 三种输出

- **pI × 分子量散点图**：所有输入蛋白按"预测等电点 × 分子量"作图，就像一张 2D-PAGE 胶；例如示例蛋白 W9DWB3 被预测为 pI 8.915、分子量 93 kDa [【跳转到 03:00】](https://www.youtube.com/watch?v=T8USjl-Kdg8&t=180)。
- **多方法 pI 预测**：对单个蛋白，页面给出约 22 种方法的预测值并给出平均值，如示例蛋白：IPC2.protein.svr19 给 7.95、IPC2_protein 给 7.82、旧版 IPC_protein 给 8.31、肽段系列模型给 8.25–8.91 等 [【跳转到 03:00】](https://www.youtube.com/watch?v=T8USjl-Kdg8&t=180)、[【跳转到 03:25】](https://www.youtube.com/watch?v=T8USjl-Kdg8&t=205)。
- **逐残基 pKa**：工具不仅能预测全局等电点，还能预测各个带电残基的 pKa 值与电荷 [【跳转到 03:25】](https://www.youtube.com/watch?v=T8USjl-Kdg8&t=205)。

那 20 多种方法该选哪个？根据报告人最近做的基准测试，**新模型表现最好，建议直接使用新模型**；蛋白和肽段分别有专门的模型 [【跳转到 03:25】](https://www.youtube.com/watch?v=T8USjl-Kdg8&t=205)。

![pI×分子量散点图：像一张 2D-PAGE，示例蛋白 W9DWB3 预测 pI 8.915、93 kDa](assets/Isoelectric%20Point%20Calculator%202.0%EF%BC%88Lukasz%20Kozlowski%20ISMB%20ECCB%202021%20%E6%8A%A5%E5%91%8A%EF%BC%89/00180.webp)

![单蛋白结果面板：22 种方法各给一个 pI，平均值 8.34，新模型 IPC2.protein.svr19 给 7.95](assets/Isoelectric%20Point%20Calculator%202.0%EF%BC%88Lukasz%20Kozlowski%20ISMB%20ECCB%202021%20%E6%8A%A5%E5%91%8A%EF%BC%89/00205.webp)

![逐残基 pKa 预测示例：输入序列后每个带电残基都有自己的 pKa（如 3.46）](assets/Isoelectric%20Point%20Calculator%202.0%EF%BC%88Lukasz%20Kozlowski%20ISMB%20ECCB%202021%20%E6%8A%A5%E5%91%8A%EF%BC%89/00230.webp)

## 四、方法内核：从查 pKa 表到深度学习回归

### 4.1 最简单的算法：Henderson–Hasselbalch + 实验 pKa 值

计算等电点最简单的方法是用 Henderson–Hasselbalch 方程：统计带电残基的数量以及分子末端的电荷，再用简单公式，并代入所谓 pKa 值 [【跳转到 03:50】](https://www.youtube.com/watch?v=T8USjl-Kdg8&t=230)、[【跳转到 04:15】](https://www.youtube.com/watch?v=T8USjl-Kdg8&t=255)。不同带电残基的 pKa 由实验测得——不同实验条件下数值略有差异，这正是误差的一个来源。

### 4.2 IPC 1.0（2016）：把 pKa 变成可优化的参数

2016 年（IPC 1.0）报告人做的事是：对已知数据集——整蛋白或肽段的实测等电点——跑优化算法，得到一组最优化的 pKa 值，使预测结果达到最佳 [【跳转到 04:40】](https://www.youtube.com/watch?v=T8USjl-Kdg8&t=280)。细节不复杂：本质上是一个非常简单的优化算法（basin-hopping + 截断牛顿法）。当年它给出了很好的结果，不过如今有了新版本 [【跳转到 05:05】](https://www.youtube.com/watch?v=T8USjl-Kdg8&t=305)。

### 4.3 IPC 2.0（2021）：深度学习取代优化

新旧两版的分野很清晰：IPC 1.0（2016）只能预测等电点、用的是简单优化模式；IPC 2.0（2021）等电点和 pKa 都能预测、用一系列更先进的机器学习模型——包括深度学习 [【跳转到 05:30】](https://www.youtube.com/watch?v=T8USjl-Kdg8&t=330)。

模型组织上有两条主线：

- **蛋白模型**：支持向量回归（SVR）集成 IPC 1.0 的 19 个方法作为特征，另有 9 个 MLP 模型的深度学习回归集成；幻灯片用两条示例序列演示——prot1 实验测得 pI 7.65，prot2 实验测得 pI 6.89 [【跳转到 05:55】](https://www.youtube.com/watch?v=T8USjl-Kdg8&t=355)。
- **pKa 子模型**：对每个带电残基的 pKa 预测也有专门模型，特征是带电残基周围的 k-mer（局部序列片段）[【跳转到 06:20】](https://www.youtube.com/watch?v=T8USjl-Kdg8&t=380)。

蛋白和肽段分开建模：输入是蛋白还是肽段，就跑对应的模型 [【跳转到 05:55】](https://www.youtube.com/watch?v=T8USjl-Kdg8&t=355)。

![IPC 1.0（2016，仅 pI、优化算法）对比 IPC 2.0（2021，pI+pKa、深度学习）](assets/Isoelectric%20Point%20Calculator%202.0%EF%BC%88Lukasz%20Kozlowski%20ISMB%20ECCB%202021%20%E6%8A%A5%E5%91%8A%EF%BC%89/00330.webp)

![蛋白模型：SVR 集成 IPC 1.0 的 19 个方法 vs 深度学习集成 9 个 MLP 模型](assets/Isoelectric%20Point%20Calculator%202.0%EF%BC%88Lukasz%20Kozlowski%20ISMB%20ECCB%202021%20%E6%8A%A5%E5%91%8A%EF%BC%89/00355.webp)

### 4.4 肽段模型长什么样：一个卷积神经网络

以肽段模型为例：输入是序列本身（one-hot 编码），再加上额外特征——氨基酸指数（AAindex，15 个特征）、氨基酸计数，以及 IPC 1.0 约 20 种方法的预测值；这些合并成多通道输入送入模型，经过卷积层、池化层等结构，最后输出预测结果 [【跳转到 06:30】](https://www.youtube.com/watch?v=T8USjl-Kdg8&t=390)、[【跳转到 06:55】](https://www.youtube.com/watch?v=T8USjl-Kdg8&t=415)。更多细节可以查论文的补充材料 [【跳转到 06:55】](https://www.youtube.com/watch?v=T8USjl-Kdg8&t=415)。

![肽段模型架构：序列 one-hot + AAindex（15 特征）+ 氨基酸计数 + IPC 1.0 预测，多通道进 CNN](assets/Isoelectric%20Point%20Calculator%202.0%EF%BC%88Lukasz%20Kozlowski%20ISMB%20ECCB%202021%20%E6%8A%A5%E5%91%8A%EF%BC%89/00415.webp)

## 五、成绩单：更准、更快

### 5.1 蛋白与肽段基准

幻灯片给出了蛋白基准测试（Protein dataset）：新模型 **IPC2.protein.svr.19** 的 RMSE 0.8479、MAE 0.5906、R² 0.5934，优于 IPC2_protein（0.8608）、旧版 IPC_protein（0.8677）与 ProMoST（0.9113）[【跳转到 07:16】](https://www.youtube.com/watch?v=T8USjl-Kdg8&t=436)。肽段模型与旧方法相比也有不错的表现 [【跳转到 07:16】](https://www.youtube.com/watch?v=T8USjl-Kdg8&t=436)。

![蛋白基准测试表：IPC2.protein.svr.19 的 RMSE/MAE/R² 全面领先旧版与 ProMoST](assets/Isoelectric%20Point%20Calculator%202.0%EF%BC%88Lukasz%20Kozlowski%20ISMB%20ECCB%202021%20%E6%8A%A5%E5%91%8A%EF%BC%89/00436.webp)

### 5.2 pKa 基准：对比 Rosetta

针对 pKa 值还有单独的基准测试，对比对象是 Rosetta：IPC2_pKa 的 RMSE 0.3883、MAE 0.2238，明显好于 Rosetta（Site repack）的 0.7750/0.8193——平均而言 IPC2 更好，但对某些带电残基（幻灯片列出 Asp、Tyr 两类残基的实测分布）偶尔会差一些 [【跳转到 07:37】](https://www.youtube.com/watch?v=T8USjl-Kdg8&t=457)。

不过要始终记住两者的本质差异：**IPC2 的方法只基于序列，而 Rosetta 需要结构或结构模型**。因此 IPC2 的预测几秒钟内就能完成，而结构路线每个蛋白要等几个小时 [【跳转到 08:02】](https://www.youtube.com/watch?v=T8USjl-Kdg8&t=482)。

![pKa 基准对比 Rosetta：IPC2_pKa RMSE 0.3883 vs Rosetta 0.7750/0.8193，且只需序列](assets/Isoelectric%20Point%20Calculator%202.0%EF%BC%88Lukasz%20Kozlowski%20ISMB%20ECCB%202021%20%E6%8A%A5%E5%91%8A%EF%BC%89/00457.webp)

## 小结

- **等电点 pI** = 分子正负电荷平衡、净电荷为零的 pH；环境 pH 偏离 pI 时蛋白带电并相互排斥，接近 pI 时相互吸引。
- pI 直接影响三个实验场景：**长晶体要避开 pH≈pI 的缓冲液**；**2D-PAGE** 一维按 pI 分离；**LC-MS** 可按 pI 分组简化分析。
- **经典算法** = Henderson–Hasselbalch 公式 + 实验测定的 pKa 值；**IPC 1.0（2016）** 把 pKa 变成对实测 pI 数据集优化的参数。
- **IPC 2.0（2021）** 用深度学习（含 9 个 MLP 的集成）取代优化算法，pI 与 pKa 同时预测；蛋白/肽段分模型，pKa 模型用带电残基周围的 k-mer 特征，肽段模型是融合 one-hot、AAindex、氨基酸计数与旧方法预测的 CNN。
- **成绩单**：蛋白基准 RMSE 0.8479 优于旧版与 ProMoST；pKa 基准平均优于 Rosetta（0.3883 vs 0.7750）；只需序列、秒级出结果，而 Rosetta 需要结构、每蛋白数小时。
- 实操建议：数据量大用 standalone 版；多方法结果中优先采用新模型（IPC2 系列）。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| 等电点 pI | 分子正负电荷平衡、净电荷为零时的 pH |
| pKa | 酸碱解离常数，决定各带电残基在不同 pH 下的带电状态 |
| Henderson–Hasselbalch 方程 | 用 pKa 与残基数计算蛋白净电荷/等电点的经典公式 |
| IPC / IPC 2.0 | 华沙大学 Kozlowski 开发的等电点计算器；2.0 版（2021）用深度学习预测 pI 与 pKa |
| SVR（支持向量回归） | IPC 沿用的回归方法，用于集成多个经典方法的预测 |
| MLP | 多层感知机（一种神经网络），IPC 2.0 集成了 9 个 MLP 模型 |
| k-mer | 以带电残基为中心的局部序列片段，pKa 模型的输入特征 |
| Rosetta | 基于结构的建模套件，可算 pKa 但需要结构模型、耗时数小时 |
