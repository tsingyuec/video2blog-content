# 多模态对比扩散模型 MMCD：同时生成治疗肽的序列与结构

> 视频来源：[A Multi-Modal Contrastive Diffusion Model for Therapeutic Peptide Generation](https://www.youtube.com/watch?v=rhr7C3-55MU)（Machine Learning Studies 频道的论文精讲，约 38 分钟）。本博客基于视频字幕与幻灯片整理，数据与结论均以讲者报告为准。

## 本讲要解决的核心问题（SCQA）

**背景**：治疗肽（therapeutic peptides）——抗菌肽（AMP）、抗肿瘤肽（ACP）等——是一类独特的重要药物；深度生成模型已经在治疗肽生成上展现出可观的潜力。

**冲突**：但现有生成方法要么只学**序列**（残基排布）、要么只学**结构**（主链原子坐标），是"单模态"的；而融合两种模态信息的模型本可以更强。更麻烦的是：图像、文本、蛋白质的生成任务有百万级标注样本，治疗肽的公开数据集通常只有**几千条**。

**疑问**：能不能在一个扩散框架里**同时**生成序列与结构，并把"治疗性"知识注入进去？

**回答（中心思想）**：能——这就是 **MMCD**（Multi-Modal Contrastive Diffusion）：为序列与结构各建一个扩散模型，并在**每个扩散时间步**上施加多模态对比学习——**inter-CL** 对齐同一肽的序列与结构嵌入、**intra-CL** 把治疗肽与非治疗肽拉开。在 AMP/ACP 两个数据集上，MMCD 在相似度、稳定性、治疗分数、结构合理性、RMSD 与对接分数等指标上全面超越当时的 SOTA 基线。

![摘要页：MMCD 在扩散框架中融合序列与结构两种模态，逐步对比学习保证一致性](assets/A%20Multi-Modal%20Contrastive%20Diffusion%20Model%20for%20Therapeutic%20Peptide%20Generation/00050.webp)

## 一、背景：治疗肽与生成模型家族

### 1.1 为什么"筛选"不够用

治疗肽是短氨基酸链，传统发现方式是用噬菌体/酵母展示技术或计算打分工具对序列空间做全面筛选。问题在于：可能的肽组合空间极其庞大，真正满足治疗要求的解只占极小一部分——暴力筛选费时费钱。

### 1.2 深度生成模型四大家族

[【跳转到 03:20】](https://www.youtube.com/watch?v=rhr7C3-55MU&t=200)

生成模型通过神经网络逼近已知肽的底层分布，可以探索更宽的化学空间、创造结构上新颖的肽。四条技术路线：

1. **自回归（RNN）**：把肽序列当成"句子"，逐残基预测排布（Müller 等人 2018）；
2. **VAE**：编码器-解码器学出潜空间，从中采样生成，可把治疗属性作为条件约束；
3. **GAN**：生成器与判别器在已知数据上互相博弈，产出新肽（Tucs 等人 2020）；
4. **扩散模型**：凭借更强的分布拟合能力，如今在蛋白质序列/结构生成中当红，同样有望赋能肽生成。

![四大家族一览：自回归 RNN、VAE、GAN、扩散模型——扩散在蛋白质生成中已占据主流](assets/A%20Multi-Modal%20Contrastive%20Diffusion%20Model%20for%20Therapeutic%20Peptide%20Generation/00225.webp)

### 1.3 本文要填的两个坑

- **单模态**：上述方法要么生成序列、要么生成结构，融合两者的生成器尚未被系统研究；
- **数据稀缺**：治疗肽公开数据集只有几千条序列/结构，必须想办法"注入知识"而不是硬学。

## 二、MMCD 总体框架：一条肽 = (序列, 结构)

### 2.1 问题形式化

[【跳转到 10:50】](https://www.youtube.com/watch?v=rhr7C3-55MU&t=650)

一条含 N 个残基的肽表示为元组 **X = (S, C)**：

- **S**：序列，第 i 个残基取自 20 种标准氨基酸（A/C/D/E/F/G/H/I/K/L/M/N/P/Q/R/S/T/V/W/Y）；
- **C**：结构，第 i 个残基的 4 个主链原子（N、Cα、C、O）的三维笛卡尔坐标。

目标是基于已知肽数据建模**联合分布**——采样时同时得到新序列与新坐标。

### 2.2 序列侧：离散扩散

[【跳转到 14:06】](https://www.youtube.com/watch?v=rhr7C3-55MU&t=846)

残基类型是**类别数据**，于是用 one-hot（20 维）+ **离散扩散**：前向过程通过转移矩阵逐步加噪（采用边缘分布的设计，属 D3PM/多项扩散一类；Austin 等人 2021、Vignac 等人 2023）。反向过程把轨迹参数化为"给定当前状态、预测初始状态 S⁰"的概率——整条序列的概率等于各位置 softmax 概率的乘积。网络 **F_S = Transformer 编码器 + MLP**：前者学习残基的上下文嵌入，后者把嵌入映射到残基类型的噪声。

![序列离散扩散：残基类型 one-hot 后经转移矩阵加噪，反向网络逐步预测初始序列的概率](assets/A%20Multi-Modal%20Contrastive%20Diffusion%20Model%20for%20Therapeutic%20Peptide%20Generation/00846.webp)

### 2.3 结构侧：连续扩散

[【跳转到 16:11】](https://www.youtube.com/watch?v=rhr7C3-55MU&t=971)

原子坐标是三维空间里的**连续变量**：前向过程直接叠加高斯噪声（Ho, Jain & Abbeel 2020 的经典做法）；反向过程由网络 **ε_θ** 逐步预测高斯噪声、恢复结构。噪声预测器 **F_C = EGNN（等变图神经网络）+ MLP**：前者把结构形式化为 3D 图、学习残基的空间嵌入，后者把嵌入映射为噪声。学到的结构嵌入同样参与下游对比学习。

![结构连续扩散：坐标加高斯噪声，EGNN+MLP 组成的 ε_θ 预测噪声并逐步恢复结构](assets/A%20Multi-Modal%20Contrastive%20Diffusion%20Model%20for%20Therapeutic%20Peptide%20Generation/00971.webp)

### 2.4 整体架构与训练目标

[【跳转到 12:26】](https://www.youtube.com/watch?v=rhr7C3-55MU&t=746)

MMCD 的全貌：序列/结构两个扩散过程（前向加噪 Q、反向去噪 P，反向网络用 Transformer 编码器或 EGNN 抽嵌入、再用 MLP 映射到边缘分布或高斯噪声），加上 inter-CL 与 intra-CL 两个对比模块。扩散目标被分解为两项：

- **序列损失 L_S**：真实与预测残基类型之间的**交叉熵**（样本集上取平均）；
- **结构损失 L_C**：预测噪声 ε_θ 与标准高斯噪声 ε 之间的**均方误差（MSE）**。

![MMCD 总览：序列/结构双扩散 + inter-CL/intra-CL 多模态对比学习，在每个时间步施加](assets/A%20Multi-Modal%20Contrastive%20Diffusion%20Model%20for%20Therapeutic%20Peptide%20Generation/00746.webp)

## 三、多模态对比学习：本文的灵魂

### 3.1 为什么要"在扩散里做对比"

[【跳转到 19:06】](https://www.youtube.com/watch?v=rhr7C3-55MU&t=1146)

当序列与结构两种模态共存时，必须捕捉它们之间的**一致性**，压缩模态间的异质差异，才能在生成任务中真正融合。度量这种非线性依赖关系的直接工具是**互信息（Mutual Information, MI）**：最大化模态间的 MI，就能迫使它们对齐、共享关键信息。

对比学习（CL）正是实现手段：把**锚**（anchor，一个数据样本）拉近**正例**（相似实例）、推离众多**负例**（不相似实例），在嵌入空间中优化互信息。正负例怎么构造，很大程度上决定模型成败——此前已有图文对齐（Yuan 等人 2021）、短文本（Wu, Lu & Dong 2022）、蛋白质结构（Jung 等人 2023b）等方案，但都还没延伸到肽领域。MMCD 把 CL 作为**辅助目标**引入肽生成，并且**在每个扩散时间步 t 上都施加**。

![多模态对比学习：把同一肽的序列与结构嵌入拉近（正例），把治疗与非治疗肽的嵌入拉开（负例）](assets/A%20Multi-Modal%20Contrastive%20Diffusion%20Model%20for%20Therapeutic%20Peptide%20Generation/01146.webp)

### 3.2 inter-CL：把序列与结构对齐

[【跳转到 19:56】](https://www.youtube.com/watch?v=rhr7C3-55MU&t=1196)

在每个扩散时间步 t：

- **锚** = 某肽的序列；**正例** = 同一条肽的结构；**负例** = mini-batch 里其他肽的结构；
- 最大化正对（锚-正例）的 MI、最小化负对（锚-负例）的 MI，所用嵌入来自反向网络学到的表示；
- 再做一遍**双向对比**：以结构为锚、序列为实例。

目标函数是 InfoNCE 式的损失：负的"正对相似度与所有对相似度之比"的对数平均，相似度用**带温度系数的余弦相似**度量，M 为 mini-batch 大小。

### 3.3 intra-CL：把治疗肽与非治疗肽拉开

[【跳转到 21:11】](https://www.youtube.com/watch?v=rhr7C3-55MU&t=1271)

第二个问题：训练数据有限时，扩散模型只能"记住"有限的生成模式，对新肽泛化差。办法是用对比学习**丰富监督信号**——但不能靠数据增强造正例：治疗肽哪怕轻微扰动，功能就可能显著改变（Yan, Kumar & Singh 2022）。因此 MMCD 从公共数据库收集**非治疗肽**充当负例：

- **序列向**：治疗肽 i 的序列为锚，另一条治疗肽 j 的序列为正例，非治疗肽 k 的序列为负例；
- **结构向**：用治疗/非治疗肽的结构同样构造锚-正-负。

损失按"是否同类"加权求和：指示函数把同类对（正）与异类对（负）筛选出来。

**为什么这样设计**（讲者给出三点理由）：

1. 非治疗类天然携带与治疗类相反的信息，让模型更具判别力；
2. 最大化类间差异会让治疗肽的嵌入分布产生偏移——这可能指向**更多的潜在生成空间**；
3. 在扩散过程中强化"嵌入 ↔ 类别"的对应关系，维持高生成保真度。

### 3.4 总损失

[【跳转到 24:36】](https://www.youtube.com/watch?v=rhr7C3-55MU&t=1476)

把所有目标加起来（t 在 1..T 上均匀采样）：

**L_total = E_t[ α·(L_S^t + L_C^t) + (1−α)·(L_intra^t + L_inter^t) ]**

其中 α 是平衡"扩散任务"与"对比任务"贡献的超参数。实现细节与肽生成采样过程见论文附录；代码、数据与附录已在 GitHub 开源。

## 四、实验：两个数据集上的全面领先

### 4.1 数据与基线

[【跳转到 25:26】](https://www.youtube.com/watch?v=rhr7C3-55MU&t=1526)

- **数据**：从公共数据库收集治疗肽——**AMP 20,129 条**、**ACP 4,381 条**；其中一部分只有一维序列、没有三维结构，用 Rosetta 系工具从序列预测补全（Chaudhury, Lyskov & Gray 2010）；再为每个数据集配对**等量的非治疗肽**，专供对比学习使用。
- **基线**：序列生成——自回归 RNN（Müller 等人 2018）、GAN 类（Tucs 等人 2020）、VAE 类（含 HydraAMP）；结构生成——结合神经网络与模拟退火的结构预测器；另把蛋白质生成的扩散方法扩展到肽：结构生成的 FoldingDiff、ProDiff，以及序列-结构共设计的扩散方法。

![数据集构成：AMP 20,129 条 + ACP 4,381 条，缺结构的用 Rosetta 系工具补全，非治疗肽等量配对](assets/A%20Multi-Modal%20Contrastive%20Diffusion%20Model%20for%20Therapeutic%20Peptide%20Generation/01526.webp)

### 4.2 六个指标怎么看

[【跳转到 27:31】](https://www.youtube.com/watch?v=rhr7C3-55MU&t=1651)

每个模型生成 **1,000 条**新肽，指标取平均：

| 侧 | 指标 | 含义 |
| --- | --- | --- |
| 序列 | similarity | 与已有肽的最近邻相似度，**越低越新颖** |
| 序列 | instability | 肽的不稳定程度 |
| 序列 | antimicrobial/anti-cancer score | 具有治疗性质的概率，越高越好 |
| 结构 | Ramachandran score | 结构可靠性 |
| 结构 | RMSD | 与已有肽的结构距离，**越低越"真实"** |
| 结构 | docking | 与细菌膜蛋白（PDB 6MI7）的结合程度 |

### 4.3 主要结果：序列与结构双榜第一

[【跳转到 29:11】](https://www.youtube.com/watch?v=rhr7C3-55MU&t=1751)

- **序列生成（Table 1）**：MMCD 的 similarity 与 instability 最低——生成更多样、更稳定；AMP/ACP 分数在两个数据集上都超过所有基线。有意思的对照是：扩散基线（如序列-结构共设计扩散）稳定性和多样性很好，但治疗分数低于"注入了生物学知识"的基线（如 HydraAMP）——而 MMCD 通过对比学习把治疗/非治疗知识注进了扩散模型，于是**各项指标同时最优**。
- **结构生成（Table 2）**：超过所有基线——在 AMP 数据集上，比最好的两个扩散基线 RMSD 低 23.3% 与 12.9%、Ramachandran 高 10.2% 与 5.6%、docking 高 7.4% 与 2.7%。更高的 Ramachandran、更低的 RMSD 说明生成结构可靠；对接分数最佳说明与靶蛋白的结合作用强。

![Table 1 序列生成结果：MMCD 在相似度、稳定性与 AMP/ACP 分数上全面领先](assets/A%20Multi-Modal%20Contrastive%20Diffusion%20Model%20for%20Therapeutic%20Peptide%20Generation/01401.webp)

### 4.4 按长度拆开看：短肽尤其强

[【跳转到 31:16】](https://www.youtube.com/watch?v=rhr7C3-55MU&t=1876)

数据集中肽长从 5 到 50 个残基不等。每个长度生成 20 条新肽（两个无法固定长度的基线被排除）。结果（图 2B）：**每个长度上 MMCD 的 similarity 与 RMSD 都领先**；所有方法都随长度增加而分数上升——序列越长搜索空间越大，且长肽样本稀缺、难以准确估计。结论：MMCD 擅长在不同长度、特别是**较短**长度上生成多样的肽。

![图 2B：不同序列长度下的 similarity 与 RMSD 对比，MMCD 在各长度均领先](assets/A%20Multi-Modal%20Contrastive%20Diffusion%20Model%20for%20Therapeutic%20Peptide%20Generation/01676.webp)

### 4.5 消融：两个对比模块缺一不可

[【跳转到 32:31】](https://www.youtube.com/watch?v=rhr7C3-55MU&t=1951)

- **去掉 inter-CL**：序列与结构生成的所有指标下滑——模态对齐确实重要；
- **去掉 intra-CL**：性能显著下降——区分治疗/非治疗确实有贡献。

t-SNE 可视化（图 3）进一步解释了机制：inter-CL 让序列与结构嵌入对齐，共享关键信息（虚线圈）在扩散中被捕捉；intra-CL 让治疗肽与非治疗肽在嵌入分布中分得更开，由此产生的分布偏移指向更大的生成空间，带来更高的质量与多样性。

![Table 3 消融实验：去掉 inter-CL 或 intra-CL 都会使性能下降](assets/A%20Multi-Modal%20Contrastive%20Diffusion%20Model%20for%20Therapeutic%20Peptide%20Generation/01976.webp)

![图 3 t-SNE：inter-CL 对齐序列/结构嵌入，intra-CL 分开治疗与非治疗肽的嵌入分布](assets/A%20Multi-Modal%20Contrastive%20Diffusion%20Model%20for%20Therapeutic%20Peptide%20Generation/02026.webp)

### 4.6 对接分析：生成的结构真的能结合吗

[【跳转到 35:01】](https://www.youtube.com/watch?v=rhr7C3-55MU&t=2101)

从 AMP 数据集随机选一条参考肽，各方法基于**同一序列**生成结构，然后与细菌外膜的脂多糖相关靶标做分子对接，提取对接复合物中 5 Å 以内的残基来可视化结合作用。结果：所有方法都能产生可结合靶蛋白的结构，但 **MMCD 的对接分数最高、结合残基与参考结构最相似**——生成了结构可靠、具治疗潜力的肽。

![图 4 对接分析：靶蛋白与参考/生成结构的相互作用可视化，粗线为肽残基、细线为结合残基](assets/A%20Multi-Modal%20Contrastive%20Diffusion%20Model%20for%20Therapeutic%20Peptide%20Generation/02184.webp)

## 小结

- 治疗肽生成难在两点：**单模态**（只学生列或只学结构）与**数据稀缺**（几千条 vs 图像/蛋白质的百万级）。
- MMCD 用**双扩散**建模联合分布：序列走离散扩散（Transformer 编码器 + MLP），结构走连续扩散（EGNN + MLP），采样时同时产出序列与主链坐标。
- 灵魂是**逐步多模态对比学习**：inter-CL 在每个扩散时间步对齐同肽的序列/结构嵌入；intra-CL 把治疗肽与非治疗肽拉开——负例来自公共库（数据增强不可行，轻微扰动即改变功能）。
- 总损失 = 扩散项（序列交叉熵 + 结构噪声 MSE）+ 对比项（intra + inter），α 加权。
- 实验：AMP 20,129 / ACP 4,381；序列榜（新颖性、稳定性、治疗分数）与结构榜（Ramachandran、RMSD、docking）全面领先，结构 RMSD 比最好扩散基线低 23.3%/12.9%。
- 消融证明两个 CL 模块缺一不可；t-SNE 与对接分析提供了机制与可靠性的佐证。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| 治疗肽（AMP/ACP） | 有治疗价值的短肽：抗菌肽、抗肿瘤肽 |
| 离散扩散 | 对类别数据（残基类型 one-hot）做加噪/去噪的扩散变体 |
| 连续扩散 | 对连续变量（原子坐标）加高斯噪声并学习逐步去噪 |
| EGNN | 等变图神经网络：把 3D 结构形式化为图并保持空间等变性 |
| inter-CL | 同一肽的序列嵌入与结构嵌入互为正例，跨模态对齐 |
| intra-CL | 治疗肽互为正例、非治疗肽为负例，注入"治疗性"知识 |
| 互信息（MI） | 度量两个变量非线性依赖程度；最大化模态间 MI = 对齐 |
| similarity score | 生成肽与已有肽的最近邻相似度，越低越新颖 |
| instability score | 肽的不稳定程度，越低越好 |
| Ramachandran score | 评估骨架二面角合理性的结构可靠性指标 |
| RMSD | 生成结构与已知肽结构的均方根偏差，越低越真实 |
| docking score | 生成肽与细菌膜蛋白（PDB 6MI7）的结合程度 |
| Rosetta | 结构预测/设计工具族，本文用于从序列补全缺失结构 |
