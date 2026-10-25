# Predicting Single-Cell Perturbation Responses For Unseen Drugs | Leon Hetzel and Simon Böhm

> **视频**：[Predicting Single-Cell Perturbation Responses For Unseen Drugs | Leon Hetzel and Simon Böhm](https://www.youtube.com/watch?v=nsL_NOwYf1c)
> **时长**：约 58 分钟（含问答）
> **说明**：这是 chemCPA 作者 Leon Hetzel 与 Simon Böhm 的报告；文中时间戳均指向该视频。

## 本讲要解决的核心问题（SCQA）

**背景（S）**：单细胞 RNA 测序能逐个细胞读出基因表达。给定细胞当前状态 $x_{\text{old}}$ 和一个条件 $p$（比如用哪种药、什么剂量），研究者想问：能不能找到一个函数 $f$，预测扰动后的新状态 $x_{\text{new}}$（[03:30](https://www.youtube.com/watch?v=nsL_NOwYf1c&t=210)）。

**冲突（C）**：药物空间太大，能做的实验太少。CPA（Compositional Perturbation Autoencoder，组合扰动自编码器）已经把细胞状态、细胞系和药物拆成潜空间里可以相加的向量，能组合出没测过的“药物 × 细胞系”；但它把药物存成一张**查找表**：训练集里没有的药，模型连一个向量都拿不出来，剂量也只是一个粗略的强度标量（[15:34](https://www.youtube.com/watch?v=nsL_NOwYf1c&t=934)、[16:24](https://www.youtube.com/watch?v=nsL_NOwYf1c&t=984)）。

**疑问（Q）**：能不能把“药物 ID”换成“化学结构”，让模型从结构推断扰动方向？剂量能不能学成非线性响应？能不能先用大规模的 L1000 bulk 数据预训练，再迁移到单细胞？

**回答（A）**：chemCPA 保留 CPA 的编码器—解码器与对抗解耦，只换掉药物那一侧：加一个**预训练的分子结构编码器**和一个**剂量缩放器**；再用“L1000 预训练 + architecture surgery + sci-Plex3 微调”把知识搬到单细胞。它让“未见药物”从不可做变成可做，但天花板仍由数据决定。

![chemCPA 的编码器—解码器：表达谱被压到 32 维潜空间，再还原](assets/Predicting Single-Cell Perturbation Responses For Unseen Drugs ｜ Leon Hetzel and Simon Böhm/a01_encoder_decoder.webp)

## 一、CPA 的三个动作：编码、解耦、再加回去

CPA 的出发点很朴素：如果“药物效应”和“细胞背景”能在潜空间里分开，换药、换细胞系就可以像做向量加法一样组合。

**第一步是编码。** 输入是细胞的基因表达向量 $x_i$，维度随测序 panel 从一千到五千以上不等；编码器 $E_\theta$ 把它压成一个固定的 **32 维**潜向量 $z_i$（[12:14](https://www.youtube.com/watch?v=nsL_NOwYf1c&t=734)）。解码器 $D_\psi$ 再从潜向量还原表达谱，训练时主要优化重建损失。

**第二步是对抗解耦。** 如果放任编码器，它会把“这是什么药”“这是什么细胞系”全塞进 $z_i$，后面再手动加属性就没有意义。CPA 因此接了两个对抗分类器：一个从潜向量预测药物，一个预测细胞系；分类器的交叉熵损失反过来惩罚编码器，迫使它“删掉”这些信息（[13:54](https://www.youtube.com/watch?v=nsL_NOwYf1c&t=834)）。训练稳定后得到的 $z_{\text{basal}}$ 就是**基底状态（basal state）**，一个尽量只保留细胞自身状态的表示（[15:09](https://www.youtube.com/watch?v=nsL_NOwYf1c&t=909)）。

![对抗解耦：两个分类器分别试图从基底状态预测药物和细胞系，编码器则被惩罚](assets/Predicting Single-Cell Perturbation Responses For Unseen Drugs ｜ Leon Hetzel and Simon Böhm/a02_adversarial.webp)

**第三步是加回属性。** 把基底状态、细胞系嵌入、药物嵌入相加：

$$z'_i = z_{\text{basal}} + z_{\text{cell line}} + s_d \cdot z_{\text{drug}}$$

其中 $s_d$ 是剂量强度。这里体现了 CPA 的**组合属性**：药物不是 one-hot 查表，而是潜空间里的一个方向；两个单扰动都见过时，可以把方向相加去近似组合扰动。要做反事实推断也很直接：把扰动后的细胞编码回基底状态，换一个药物向量，再解码，就得到“如果当时用另一种药会怎样”（[16:24](https://www.youtube.com/watch?v=nsL_NOwYf1c&t=984)）。

问题也在这里：$z_{\text{drug}}$ 来自查找表。新药没有 ID，就没有方向；剂量只是一个乘数，难以表达“低剂量没反应、高剂量突然起效”的非线性。

## 二、chemCPA 把药物查表换成结构编码 + 剂量缩放

chemCPA 把药物查找表换成一个**扰动网络（perturbation network）**，由三部分组成（[17:39](https://www.youtube.com/watch?v=nsL_NOwYf1c&t=1059)）。

![扰动网络：分子编码器 G、扰动编码器 M、剂量缩放器 S](assets/Predicting Single-Cell Perturbation Responses For Unseen Drugs ｜ Leon Hetzel and Simon Böhm/a03_perturbation_network.webp)

1. **分子结构编码器 $G$**：输入药物的 SMILES 字符串（用文本表示分子结构的写法），输出定长化学表示。$G$ 预训练好后**冻结**，训练 chemCPA 时不再更新；这样每个分子只需前向一次、把结果存成表，也能直接借用 GROVER 这类大 Transformer（[18:04](https://www.youtube.com/watch?v=nsL_NOwYf1c&t=1084)）。
2. **扰动编码器 $M$**：把不同来源、不同维度的化学表示统一映射到 32 维潜空间，得到 $z_{d_i}$；它让 $G$ 可以随时替换。
3. **剂量缩放器 $S$**：输入实验浓度，输出“有效剂量”$\hat{s}_i$，再与药物向量相乘。它是一个可学习的小网络，因此能表达非线性剂量响应；如果某个药在该条件下确实无效，$S$ 也可以把有效剂量压到接近零（[20:47](https://www.youtube.com/watch?v=nsL_NOwYf1c&t=1247)）。

作者试了三类 $G$：**RDKit** 指纹、**JT-VAE** 和 **GROVER** Transformer。结果反直觉：**最简单的 RDKit 反而最稳**（[41:01](https://www.youtube.com/watch?v=nsL_NOwYf1c&t=2461)、[50:45](https://www.youtube.com/watch?v=nsL_NOwYf1c&t=3045)）。瓶颈不在编码器复杂度，而在数据能支持多细的区分；GROVER 预训练的分子性质任务，和“药物如何扰动转录组”并不是一回事（[57:31](https://www.youtube.com/watch?v=nsL_NOwYf1c&t=3451)）。

![chemCPA 全景：编码器—解码器、细胞系嵌入、扰动网络与两个对抗分类器](assets/Predicting Single-Cell Perturbation Responses For Unseen Drugs ｜ Leon Hetzel and Simon Böhm/a04_architecture_overview.webp)

## 三、数据接力：L1000 预训练，surgery 扩维，sci-Plex3 微调

chemCPA 的训练分源域和目标域两步。

**源域是 L1000。** Broad Institute 用 bulk（把一群细胞混起来测，只得到平均值）方式构建连接图谱，选了 **978 个 landmark 基因**（一组精选的代表性基因），覆盖约 **1.7 万种化合物、72 条细胞系、130 万条观测**（[22:27](https://www.youtube.com/watch?v=nsL_NOwYf1c&t=1347)）。它规模大、药物多，但有三重局限：不是单细胞，看不到异质性；基于杂交荧光，需要反卷积，和 RNA-seq 不是同一套测量；只有 978 个基因，很多化合物的效应很弱甚至没有（[24:07](https://www.youtube.com/watch?v=nsL_NOwYf1c&t=1447)、[24:32](https://www.youtube.com/watch?v=nsL_NOwYf1c&t=1472)）。

![L1000：978 个 landmark 基因、约 130 万条观测，但它是 bulk 且基于杂交信号](assets/Predicting Single-Cell Perturbation Responses For Unseen Drugs ｜ Leon Hetzel and Simon Böhm/a05_l1000.webp)

**目标域是 sci-Plex3。** 这是单细胞药物扰动数据：约 **65 万个细胞、188 种药、3 条癌细胞系**（A549 肺癌、K562 白血病、MCF7 乳腺癌）、**7,500 个基因**（[28:33](https://www.youtube.com/watch?v=nsL_NOwYf1c&t=1713)）。它更接近真实应用，但规模小，多数药物效应偏弱，细胞系间反应也不一致（[26:23](https://www.youtube.com/watch?v=nsL_NOwYf1c&t=1583)、[27:43](https://www.youtube.com/watch?v=nsL_NOwYf1c&t=1663)）。

两个数据域的基因集不同。作者用基因注释取交集，得到 **977 个共同 landmark 基因**，先把源域和目标域都限制在这 977 个基因上，验证迁移本身能不能工作（[31:03](https://www.youtube.com/watch?v=nsL_NOwYf1c&t=1863)）。然后做 **architecture surgery**（给预训练网络“动手术”）：在编码器和解码器上各加一层，把输入/输出维度从 977 扩到“977 + 1000 多个高变基因”，再用单细胞数据微调（[31:28](https://www.youtube.com/watch?v=nsL_NOwYf1c&t=1888)）。

![architecture surgery：保留 L1000 权重，在编码器和解码器上加层，扩展到单细胞的基因维度](assets/Predicting Single-Cell Perturbation Responses For Unseen Drugs ｜ Leon Hetzel and Simon Böhm/a06_architecture_surgery.webp)

关键是**加层而不是重训**：主体权重保留 bulk 学到的药物效应，新层只负责对齐新的基因维度。相同基因集用来验证迁移；扩展基因集更接近真实使用，也更难，因为新增基因在预训练时从未出现过。

## 四、结果：预训练把“看不见的药”拉回可预测区间

评估协议值得先讲清楚。作者只把**对照细胞**送进编码器，得到基底状态，再手动加上目标细胞系和药物属性，解码后与真实表达比较（[32:18](https://www.youtube.com/watch?v=nsL_NOwYf1c&t=1938)）。基线完全丢弃药物信息，相当于“假装这个细胞没被扰动”；任何超过基线的部分，才能归因于药物知识。指标是 $R^2$（拟合优度，越接近 1 越好），同时看全部基因和每个“药物 × 细胞系”条件下差异表达最强的 50 个基因（DEG，differentially expressed genes）。

为公平比较，作者固定剂量，只留出一个没见过的“药物 × 细胞系”组合。10 µM 下的结果很能说明问题（[43:06](https://www.youtube.com/watch?v=nsL_NOwYf1c&t=2586)、[44:21](https://www.youtube.com/watch?v=nsL_NOwYf1c&t=2661)）：

| 模型（10 µM） | 全部基因 $E[R^2]$ | DEG $E[R^2]$ |
| --- | ---: | ---: |
| 无药物基线 | 0.50 | 0.29 |
| scGen | 0.62 | 0.47 |
| CPA | 0.54 | 0.34 |
| chemCPA（不预训练） | 0.71 | 0.58 |
| **chemCPA（L1000 预训练）** | **0.76** | **0.68** |

![与 CPA、scGen、无药物基线的对比：预训练版本在全部基因和差异表达基因上都最高](assets/Predicting Single-Cell Perturbation Responses For Unseen Drugs ｜ Leon Hetzel and Simon Böhm/a07_baseline_table.webp)

结论：chemCPA 即使不预训练也已优于 CPA 和 scGen，因为它真正用上了化学结构；预训练进一步拉开差距，尤其在 DEG 上。1 µM 时差距缩小（基线 0.69、预训练 0.77），因为低剂量下多数药效应弱，更容易“猜对”。

## 五、真正未见过的药：能奏效，但不是每个都奏效

上面的“未见组合”其实还见过药物本身。真正的外推测试，是从 sci-Plex3 挑出 **9 个 OOD 药物**（分布外，训练和模型选择阶段完全不接触），标准是效应足够强、并覆盖组蛋白乙酰化、酪氨酸激酶、细胞周期、蛋白折叠等多条通路（[30:13](https://www.youtube.com/watch?v=nsL_NOwYf1c&t=1813)、[30:38](https://www.youtube.com/watch?v=nsL_NOwYf1c&t=1838)）。

趋势是：预训练版本在 0.01–10 µM 的各个剂量上都更稳，收敛更好，解耦分数也更高（[45:11](https://www.youtube.com/watch?v=nsL_NOwYf1c&t=2711)）。但并非每个药都成功：两个 HDAC 抑制剂表现不错，另一个提升有限（[49:46](https://www.youtube.com/watch?v=nsL_NOwYf1c&t=2986)）。

![未见药物的剂量响应：预训练版本整体更好，但不同药物之间差异明显](assets/Predicting Single-Cell Perturbation Responses For Unseen Drugs ｜ Leon Hetzel and Simon Böhm/a08_unseen_dose.webp)

扩展基因集上整体 $R^2$ 会下降：新增高变基因没在 L1000 出现过。更有意思的是 DEG 指标：那些差异表达基因很可能并不属于 977 个 landmark，模型仍能在部分药物上给出可用预测，说明“结构 → 扰动方向”的映射可迁移；但也有药物明显失败（[49:21](https://www.youtube.com/watch?v=nsL_NOwYf1c&t=2961)、[50:11](https://www.youtube.com/watch?v=nsL_NOwYf1c&t=3011)）。

另有两个能力。其一，药物扰动向量的 UMAP（降维可视化）上，同类机制药物会聚在一起，例如 HDAC 抑制剂形成较清晰的簇，说明潜空间学到了可解释的化学—生物关系（[46:51](https://www.youtube.com/watch?v=nsL_NOwYf1c&t=2811)）。其二，用最近邻距离和通路信息构造**不确定性分数**，标出高/低置信区，提醒使用者“这个区域的预测别太当真”（[48:06](https://www.youtube.com/watch?v=nsL_NOwYf1c&t=2886)）。

## 六、边界：数据决定天花板

chemCPA 的局限几乎都来自数据，而不是网络结构。

**第一，sci-Plex3 太小。** 只有 3 条细胞系、188 种药、约 7,500 个基因；很多药的效应很弱，甚至在不同细胞系上方向不一致。作者说它已是当时最好的单细胞单药筛选之一，但仍然有限（[47:16](https://www.youtube.com/watch?v=nsL_NOwYf1c&t=2836)）。

**第二，977 个基因是硬约束。** L1000 只有 978 个 landmark，和单细胞数据的交集是 977 个。扩展基因集能覆盖更多基因，但整体性能下降，因为新基因没有预训练支持。

**第三，解耦并不完美。** 用非线性分类器检查，细胞系和药物信息仍有残留；作者允许 0.5–0.7 的分类准确率，说明基底状态并不完全干净；性能提升不能百分百归功于药物向量（[35:13](https://www.youtube.com/watch?v=nsL_NOwYf1c&t=2113)、[36:28](https://www.youtube.com/watch?v=nsL_NOwYf1c&t=2188)）。

**第四，潜空间加法可能太简单。** 多药组合时简单相加未必成立；作者把最优传输等更丰富的潜空间算术列为未来方向（[51:35](https://www.youtube.com/watch?v=nsL_NOwYf1c&t=3095)）。基因扰动也不能直接套用，因为 CRISPR 没有 SMILES（[52:50](https://www.youtube.com/watch?v=nsL_NOwYf1c&t=3170)）。

## 小结

- CPA 的核心是“编码器—解码器 + 对抗解耦 + 潜空间相加”：把细胞状态、细胞系、药物拆成可组合的向量，基底状态负责承载细胞自身的信息。
- CPA 的硬伤是药物查表，无法外推新药；chemCPA 用**分子结构编码器**把 SMILES 映射成扰动方向，再用**剂量缩放器**学习非线性有效剂量。
- 迁移学习的关键是 **977 个共同 landmark 基因 + architecture surgery**：保留 L1000 预训练权重，加层扩展基因维度，再用 sci-Plex3 微调。
- 未见“药物 × 细胞系”组合上，10 µM 全部基因 $R^2$：chemCPA 0.71、预训练 0.76，高于 scGen 0.62、CPA 0.54、基线 0.50；DEG 差距更大。
- 真正未见药物的预测“能奏效，但不是每个都奏效”；最简单的 RDKit 指纹反而最强，说明瓶颈在数据覆盖，而不在编码器有多复杂。
- 3 条细胞系、188 种药、977 个基因、bulk 与单细胞的测量差异，决定了当前上限。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| CPA | 组合扰动自编码器，用潜空间向量相加表示“细胞系 + 药物” |
| 基底状态 | 对抗训练后被尽量去掉药物和细胞系信息的细胞潜向量 |
| chemCPA | 在 CPA 上加入分子结构编码器与剂量缩放器的版本 |
| SMILES | 用文本字符串表示分子结构的标准写法 |
| L1000 | Broad Institute 的 bulk 扰动图谱，测 978 个 landmark 基因 |
| landmark 基因 | 一组精选的、能代表更大基因表达空间的基因 |
| sci-Plex3 | 单细胞药物扰动数据集，3 条细胞系、188 种药 |

## 相关阅读

- [GEARS：预测未见多基因组合的转录结果](<Graph Neural Networks User Group Meetup 9／29／2022.md>)
- [Tahoe-x1：规模化扰动训练的单细胞基础模型](BioML Seminar 4.4 - Shreshth Gandhi on Scaling Perturbation-Trained Single-Cell Foundation Models.md)
- [Deep-learning-based Gene Perturbation Effect Prediction Does Not Yet Outperform Linear Baselines](Deep-learning-based Gene Perturbation Effect Prediction Does Not Yet Outperform Linear Baselines.md)
- [PerturBench: Benchmarking Machine Learning Models for Cellular Perturbation Analysis](<PerturBench：Benchmarking Machine Learning Models for Cellular Perturbation Analysis.md>)
