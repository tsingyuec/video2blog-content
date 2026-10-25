# BioML Seminar 4.4 - Shreshth Gandhi on Scaling Perturbation-Trained Single-Cell Foundation Models

> **视频**：[BioML Seminar 4.4 - Shreshth Gandhi on Scaling Perturbation-Trained Single-Cell Foundation Models](https://www.youtube.com/watch?v=Nky3tlQ7phA)
> **时长**：约 61 分钟（含问答）
> **说明**：这是 Tahoe Therapeutics 的 Shreshth Gandhi 关于 Tahoe-100M 数据与 Tahoe-x1 基础模型的报告。文中时间戳均指向该视频；数字尽量按讲者口径标注，论文口径另作说明。

## 视频主线

Shreshth 先解释为什么扰动数据难做，以及 Tahoe-100M 如何用“混池 + 遗传解复用”把通量提高约 50 倍。接着他拆开 Tahoe-x1 的架构与工程优化，再按 DepMap、通路、细胞类型、扰动预测四类任务评估嵌入质量。报告最后没有回避短板：少样本扰动预测接近噪声上限，零样本仍贴近基线，后续的 BT2 和 AutoResearch 都是在补这个缺口。

## 一、数据困境的解法：把 50 条癌细胞系混进 3D 球，一次实验换 50 倍通量

Shreshth 从数据是怎么造出来的讲起。扰动实验贵、通量低，公开的带药数据加起来远小于观测图谱；要把基础模型做大，先得把扰动数据做多。图左侧是来自几十到几百个病人模型的细胞；在 Top-100M 这个数据集里，用的是 **50 条癌细胞系**。他们把不同细胞系混在一起，做成 **3D 球状体（spheroid）**，一起加药、一起做单细胞测序，再用**遗传解复用（genetic demultiplexing）**把每个细胞认回它原来的细胞系（[00:00](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=0)、[00:05](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=5)）。

对机器学习的人来说，这套做法的直接收益是：**同样成本下通量提高约 50 倍**，可以在很宽的细胞系 panel 上生成约 50 倍的数据。最终 Top-100M 测了 **50 个癌症模型、约 1,200 个药物—剂量条件**（讲者口语称 “1,200 drugs”），规模大约是所有已发表扰动数据的 50 倍。讲者把它类比成扰动领域的“ImageNet 时刻”：数据量终于大到可以尝试很多以前根本做不了的想法（[00:30](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=30)、[00:46](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=46)）。

![Tahoe-100M 的规模：约 1 亿单细胞、50 个癌症模型、约 1.2 千个药物扰动条件](assets/BioML Seminar 4.4 - Shreshth Gandhi on Scaling Perturbation-Trained Single-Cell Foundation Models/b01_tahoe100m.webp)

数据的结构也决定了模型要学什么。t-SNE 上每个点是一个细胞，明显的“岛屿”是不同细胞系；也就是说，**最大的变异来源是细胞系，第二来源才是药物**。在细胞系内部，又会按药物分出子簇；不同作用方式的药物，响应可能弥散，也可能形成紧致的小岛（[01:11](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=71)、[01:16](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=76)、[01:41](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=101)）。

![Mosaic 实验：多种细胞模型混池，一次读出每个细胞对药物的响应](assets/BioML Seminar 4.4 - Shreshth Gandhi on Scaling Perturbation-Trained Single-Cell Foundation Models/b02_mosaic.webp)

混池会不会牺牲质量？讲者说他们专门比较过“混池”与“低通量独立实验”的得失：结论是两者相当接近，用同样的数据能做同样的分析，阳性对照也能得到同样结论；难点在于 pool balancing，不能让某条细胞系压过其他细胞系。经过大量 QC 工作，现在的结果几乎等同于做了多个独立实验（[02:05](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=125)、[02:30](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=150)、[02:55](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=175)）。这套混池与平衡的具体工艺，讲者说是实验生物学里偏“专有”的部分。

## 二、Tahoe-x1 的目标不是端到端预测，而是先训一个通用细胞/基因嵌入

有了数据，下一步就是模型。Tahoe-x1 的预训练语料有三个来源（[03:20](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=200)、[03:32](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=212)）：

- **Tahoe-100M**：前面说的约 1 亿扰动细胞；
- **SCBaseCount**：Arc Institute 汇总的公开数据集；
- **CellxGene**：公开单细胞图谱（讲者称由 CCIS 汇总的 “CellxGene corpus”）。

他们问的问题是：**拿到 1 亿个扰动细胞，应该做什么？** 答案是训练一个通用的**细胞嵌入和基因嵌入**模型，能跨不同应用工作。背后的判断是：先把一个很丰富的嵌入空间训出来，之后在它上面接更简单的模型做具体任务，会比每个任务都从头训一个复杂模型更省力。讲者说这个设想后来被证明是对的（[03:32](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=212)、[03:57](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=237)、[04:22](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=262)）。

问答里补充了语料比例：约 **1 亿来自 Tahoe-100M**，约 **1.5 亿来自 SCBaseCount 和 CellxGene 等其他来源**；Tahoe 部分主要是癌细胞系，另外两部分则大多是原代细胞、非癌细胞系（[59:07](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=3547)、[59:32](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=3572)）。

## 三、架构：基因 token + 表达分箱 + 药物 token + CLS 双解码器

Tahoe-x1 的骨架是一个 Transformer，讲者说如果看过 BERT，会觉得非常熟悉（[04:22](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=262)、[04:47](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=287)）。

**基因 token。** 单细胞数据是整数计数：一个细胞是一串基因 ID，以及等长的计数串。比如基因 ID 62,000 被检测到 12 次，就写成“基因 62,000 / 12”。基因通过固定词表转成 ID，词表约 **6.5 万个基因**，覆盖数据集中检测到的所有基因，而不只限蛋白编码基因。很多单细胞模型为了用 ESM 之类的蛋白嵌入只保留蛋白编码基因，但他们发现这样做没有差别，反而无谓地缩小了词表（[05:12](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=312)、[05:37](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=337)、[06:02](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=362)）。

**掩码目标与双解码器。** 训练目标很直接：遮住一部分表达值，在输出端预测被遮的值。序列开头放一个特殊的 **CLS token**（图里写作 expression $-1$、gene 0），最后一层取 CLS 的嵌入作为整个细胞的表示。模型有两个头（[06:02](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=362)、[06:27](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=387)）：

- **细胞头**：只允许用 CLS 的嵌入去预测所有被遮基因的表达。这迫使 CLS 真正总结整个细胞，否则损失会惩罚它。
- **基因头**：在最后一层做逐 token 的重建，让每个被遮基因用自己的上下文恢复表达。

讲者说，他们的目标是简化前代架构。模型大量借鉴 scGPT，但 scGPT 用了多个损失、结构更复杂；他们想砍到最本质的部分，好把模型做大、把重点放在效率上。最后保留下来、被认为真正驱动嵌入质量的就是上面这两个组件（[06:52](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=412)、[07:17](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=437)）。

**表达分箱。** 原始 count 的动态范围很大，直接回归很难学。模型先对 count 做分箱，再转成百分位，最后变成 1–50 的整数；讲者用图像里固定 0–255 的动态范围作类比。只要变换是单调的，具体分箱细节会改变损失数值，但下游嵌入质量变化不大（[07:42](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=462)、[08:07](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=487)、[09:22](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=562)、[09:47](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=587)）。

**药物 token。** 药物不按名字查表，而是用 **Morgan 指纹**——一种把分子结构编码成定长位串的经典化学信息学表示。指纹先经过一个端到端的化学嵌入层变成药物 token；这一层用离散指纹初始化，但允许训练中更新。药物 token 会被所有基因 token 关注，类似 **cross-attention（交叉注意力）**，药物信息在后续层里逐层进入基因表示，最后也进入细胞嵌入（[07:17](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=437)、[08:32](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=512)、[08:57](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=537)、[11:02](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=662)）。

**输入与掩码细节。** 数据加载器在期望意义上每行就是一个随机细胞，只会按细胞系做少量分组。每个细胞只保留有表达的基因，补齐到 **2,000** 个位置；他们试过用零计数 padding 把输入拉长，但嵌入质量没有提升，计算量却增加很多，所以最终只对表达基因做掩码。一个 batch 里所有细胞都补齐到 2,000 个基因，训练时遮住其中 **50%**（[08:07](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=487)、[08:32](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=512)、[11:02](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=662)、[11:27](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=687)、[19:06](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=1146)、[19:31](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=1171)）。

注意力上，未被遮的基因彼此全稠密可见；被遮基因可以看自己和所有可见基因，但看不到其他被遮基因的表达值，避免“偷看答案”。讲者也解释了为什么后来允许“可见基因也看部分被污染的输入”：如果只做很硬的掩码，模型反而失去了用上下文纠错的机会，而实验发现放松这一点几乎不损害性能（[19:31](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=1171)、[19:56](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=1196)、[20:21](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=1221)、[20:46](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=1246)）。

数据质量方面，他们假设输入都是单细胞（singlets）。Tahoe-100M 是自己生成的，所以过了双细胞检测和 QC；讲者提到实际规模约为 **9,560 万**细胞，而“100M”是数据集的口径，其中去掉了未通过质量控制的少量细胞（[10:12](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=612)、[10:37](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=637)）。

![Tahoe-x1 架构：基因 token、表达分箱、药物指纹 token、CLS 与双解码头](assets/BioML Seminar 4.4 - Shreshth Gandhi on Scaling Perturbation-Trained Single-Cell Foundation Models/b03_architecture.webp)

## 四、工程：70M 做实验，3B 压到约 4.5 万美元

讲者把“降低成本”当成训练这个模型的关键目标之一。模型有三个规模：**70M、1B、3B**。**3B 模型按 H100 市场价训练约 4.5 万美元**；讲者给出的单位算力成本约为每 ZFLOP 2,000（按视频口径），相比它借鉴的模型是很大的改进。模型受 Geneformer 和 scGPT 启发，但目标是把模型做小（[11:52](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=712)、[12:17](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=737)、[12:42](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=762)）。

为了快速试错，他们大量使用 **70M 模型**做实验：哪些目标函数有用、哪些部分可以砍掉、什么真正驱动性能。小改动也会影响训练，例如从 post-norm 换成 pre-norm，就必须调整嵌入的动态范围和缩放；层的位置也要试。70M 训得快，所以可以大量迭代（[12:42](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=762)、[13:07](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=787)、[13:32](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=812)）。

注意力实现是工程上的重点。早期单细胞模型规定：可见基因之间做全稠密注意力，被遮基因不能互相看；这相当于一个 prefix LM 式的掩码，无法直接使用 FlashAttention 这类标准加速。团队先用 Triton 写了一个自定义 kernel，用约 $-\infty$ 的注意力偏置模拟掩码，比 PyTorch 原生 SDPA 快很多。后来他们发现：**干脆允许全稠密注意力，只在输入侧遮住表达值**，性能几乎不降，还能直接用 FlashAttention，速度更快。1B 模型用的是自定义 kernel，更大的模型则用 FlashAttention 版本（[13:32](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=812)、[13:43](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=823)、[14:08](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=848)、[14:33](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=873)、[14:58](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=898)、[15:23](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=923)）。

多机训练用了**流式数据加载（streaming dataset）**：3B 模型在 **128 张 GPU**、多个节点上训练，节点不需要等整个数据集拷贝完才能开始，因此单 GPU 和 128 GPU 的吞吐大致相同（[15:23](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=923)、[15:48](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=948)、[16:13](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=973)）。

![效率优化：流式数据加载、FlashAttention 与多节点训练](assets/BioML Seminar 4.4 - Shreshth Gandhi on Scaling Perturbation-Trained Single-Cell Foundation Models/b04_efficiency.webp)

## 五、第一层评估：先看验证损失，再看线性探测和下游小模型

讲者把评估分成几层。最基础的一层是**留出数据上的验证损失**。因为数据预处理一直在变，而且输入上做了多种单调变换，损失绝对值并不固定，所以他们主要看 **Spearman 相关**，而不是直接比 loss 数值（[16:56](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=1016)、[17:01](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=1021)）。

第二层是**线性探测（linear probe）**：冻结嵌入，只用线性分类器去判断细胞类型等标签。更复杂的下游应用，则要在嵌入上再训一个单独模型（随机森林或神经网络）。讲者强调：表征学习训练时用的是简单的代理任务，方便模型之间比较；真正接近应用的任务，通常要在嵌入之上再训模型。细胞嵌入和基因嵌入都会用到——扰动预测多用细胞嵌入，按功能给基因分类则用基因嵌入（[17:01](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=1021)、[17:26](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=1046)、[17:51](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=1071)、[18:16](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=1096)）。

他们构造嵌入时基本是均匀选细胞，但会按三个数据源分别取约 1% 的细胞，而不是只从 Tahoe-100M 里抽（[18:16](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=1096)、[18:41](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=1121)）。

## 六、DepMap：基因嵌入能预测“敲掉这个基因细胞会不会死”

第一个真正体现生物学能力的任务是 **DepMap 基因依赖性**。DepMap 用 CRISPR 敲除每个基因，测量癌细胞还活不活，得到一个“细胞系 × 基因”的矩阵；每个元素表示“在这个细胞系里敲掉这个基因，细胞死亡的概率”，可以理解为基因对该细胞系的必需性（[21:11](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=1271)、[21:19](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=1279)、[21:24](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=1284)）。

做法是：用 CCLE 的 bulk RNA-seq 匹配到相应细胞系，得到该细胞系的表达值；把它送进 Tahoe-x1，取最后一层里目标基因的上下文嵌入。这个嵌入可以看成“在给定其他基因表达的背景下，这个基因的语义表示”；再用它训练随机森林，预测 DepMap 的实验测量（[21:49](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=1309)、[22:14](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=1334)、[22:39](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=1359)）。

他们比较了多种嵌入来源：Tahoe-x1、Arc 的 SE、Transcriptformer、NVIDIA 的 Transformer、PCA；所有方法用同样的源数据，随机森林也做同等的小范围调参。结果 Tahoe-x1 的嵌入在“细胞系特异必需性”和“把矩阵压成向量后的整体必需性”两种设定下都更高（[22:39](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=1359)、[22:48](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=1368)、[23:13](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=1393)、[23:38](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=1418)）。

这里没有标签泄漏：DepMap 的标签从未参与训练；模型只是可能在预训练语料里见过相似细胞系的表达数据（[23:58](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=1438)、[24:06](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=1446)）。讲者也坦承，他们没有解释随机森林权重，因此很难说到底是嵌入里的什么语义在驱动性能，只能确定这个嵌入来源在这个指标上更高（[24:36](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=1476)、[24:47](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=1487)、[25:12](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=1512)、[25:37](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=1537)）。

![用基因嵌入预测 DepMap 的基因必需性](assets/BioML Seminar 4.4 - Shreshth Gandhi on Scaling Perturbation-Trained Single-Cell Foundation Models/b05_depmap.webp)

## 七、MSigDB：基因嵌入也带着通路归属信息

第二个任务是 **MSigDB / cancer hallmark 基因集归属**。每个功能类别（通路）有一组成员基因；任务是给一个基因，预测它属于哪些基因集。作者用基因嵌入训练一个**多标签 MLP**：一个基因可以同时属于多个类别，输出向量里对应多个 1；评估时逐个基因集看，但一次预测所有标签（[25:37](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=1537)、[25:58](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=1558)、[27:38](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=1658)、[27:43](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=1663)、[28:08](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=1688)）。

他们做了**留出基因**的评估：在一部分基因上训练 MLP，在剩下的基因上预测它属于哪些基因集，报告 **AUPRC**（精确率—召回率曲线下面积）。对比对象包括蛋白质模型；结果显示，Tahoe-x1 学到的基因嵌入在 hallmark 基因集上表现更好。这里用的是模型第一层学到的**基因嵌入**，不是细胞系特异的上下文嵌入（[26:23](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=1583)、[26:48](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=1608)、[27:13](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=1633)）。

具体数字上，3B 模型约 **0.35**，高于 SE-600M 的 0.24、Transcriptformer 的 0.21、nv-Geneformer-100M 的 0.20 和 PCA 的 0.30。这说明模型在没有显式通路监督时，也学出了有功能意义的结构。

![MSigDB hallmark 基因集归属：Tahoe-x1 的基因嵌入表现最好](assets/BioML Seminar 4.4 - Shreshth Gandhi on Scaling Perturbation-Trained Single-Cell Foundation Models/b06_pathway.webp)

## 八、扰动预测：少样本接近噪声上限，零样本仍贴着基线

第三个任务直接对应药物发现，也是讲者最关心的应用：**用细胞嵌入做扰动预测**。在 Tahoe-100M 里，可以把数据看成“细胞系 × 药物”的矩阵，留出一些“细胞系—药物”组合不参与微调，然后预测这些组合下所有基因的表达，再和真实测量比较（[28:08](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=1688)、[28:33](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=1713)、[28:58](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=1738)）。

指标是 **PDCorr（Pearson delta correlation）**：先算每个基因相对对照的倍数变化（fold change），例如 2 表示比对照高两倍、$-2$ 表示是对照的 $e^{-2}$，再看预测的倍数变化向量和真实倍数变化有多相关（[29:23](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=1763)、[29:48](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=1788)）。

模型侧，他们用了 **State** 框架里的 **State Transport**，但换成 Tahoe-x1 自己的嵌入：在嵌入空间里做“搬运”，再映射回表达（[29:48](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=1788)、[30:13](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=1813)、[30:38](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=1838)）。

设定分两种（[30:38](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=1838)、[31:03](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=1863)）：

- **少样本（few-shot）**：预测没见过的“药物 × 细胞系”组合，但该细胞系的其他药物在训练集里出现过。
- **零样本（zero-shot）**：细胞系完全没见过，训练中没有该细胞系的任何药物数据。

结果差距很大：少样本时 PDCorr 可以到 **0.8–0.9**，接近重复实验的噪声上限；零样本只有 **0.4–0.5**，和 Mean、Global 等简单基线相差不大。讲者的判断很直接：**见过一点数据时嵌入很有用，完全没见过时模型基本学不到交互，性能很差**（[31:03](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=1863)、[38:51](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2331)、[39:16](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2356)）。

![少样本与零样本扰动预测：零样本性能贴近基线，是最诚实的短板](assets/BioML Seminar 4.4 - Shreshth Gandhi on Scaling Perturbation-Trained Single-Cell Foundation Models/b07_zeroshot.webp)

他们还把“Tahoe-x1 + State Transport”模型迁移到另一个数据集：**Parse PBMC 的细胞因子扰动**。相比随机初始化的模型有提升，而且用嵌入比直接在基因空间上做更好；但这是零样本场景，所以性能仍不如少样本时高（[33:08](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=1988)、[33:33](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2013)、[33:58](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2038)）。

问答里澄清了微调时的药物编码：State Transport 有一个在微调中单独学习的药物编码器，没有用结构初始化；因此同作用机制（MoA）的药物嵌入会在微调后变得相似，也可以选择用基于化学结构的编码器来初始化它（[31:53](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=1913)、[32:18](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=1938)、[32:43](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=1963)）。

## 九、细胞类型注释接近饱和，稀有类型才拉开差距

最后一个“饱和”的应用是**细胞类型注释**。用 Tabula Sapiens 这类有大量人工标注的图谱做线性探测，各模型都接近满分；主要差别在**稀有细胞类型**，更大的模型在数据效率上更好。讲者也提醒这个基准有点“循环”：标注本身常来自先用 PCA/t-SNE 聚类，而聚类又用了表达特征；但它仍能说明模型学到了有用的东西（[33:58](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2038)、[34:11](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2051)、[34:36](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2076)、[35:01](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2101)）。

问答里说明，这个数据集不是癌细胞系，很多是原代细胞；标签是器官来源（肺、皮肤等），不是恶性/良性。讲者认为，如果转录信号里包含疾病状态信息，模型理论上也能用于区分恶性与健康细胞，只是这篇工作没有做（[35:31](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2131)、[35:56](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2156)、[36:21](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2181)）。

## 十、规模确实有效，但有些指标只挪一点

把前面的结果放在一起看，讲者做了**缩放行为（scaling behavior）**的总结（[36:46](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2206)、[36:59](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2219)）。

验证损失随模型变大而改善，这并不意外；更重要的是，一些更下游、更抽象的任务也随规模改善。这个趋势在使用基因嵌入和细胞嵌入、在扰动预测和基因功能预测上都一致（[36:59](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2219)、[37:24](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2244)）。

讲者也提醒看图的细节：有些坐标轴被放大了，数值差距其实很小。例如 DepMap 上下文任务的 ROC 只从 **0.63 到 0.64**。这不是巨大提升，而且绝对性能还取决于微调模型有多复杂；如果在下游投更多算力，可能整体更高。但用来比较不同嵌入来源，这种缩放图仍然有用（[37:49](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2269)、[38:14](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2294)、[38:39](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2319)）。

## 十一、BT2：在嵌入空间做流匹配，训练快 25 倍，零样本补上一截

讲者把零样本性能单拎出来，作为最想改进的短板（[38:51](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2331)）。

他们先估计**噪声上限（noise ceiling）**：把真实数据拆成两半，用其中一半去“预测”另一半，计算指标。这代表如果还有一份同分布的真实数据，指标最高能做到多少（[39:08](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2348)、[39:16](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2356)）。

后续模型 **BT2** 在少样本上几乎达到重复实验的相关性，零样本也从“接近基线”提升到更接近噪声上限。同时训练时间大幅下降：BT2 约 **2–3 小时（讲者说 290 分钟）**，而原来的 State Transport 在同样数据上要 **3–4 天**，大约快 25 倍，因此可以快速试很多想法（[39:41](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2381)、[40:06](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2406)、[40:31](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2431)、[40:56](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2456)）。

BT2 的做法是在 Tahoe-x1 嵌入空间里做**流匹配（flow matching）**：训练一个条件生成模型，直接生成扰动后的细胞嵌入。讲者认为，Tahoe-x1 的嵌入空间是一个更平滑的流形，所以在这里做扩散/流匹配可以用很简单的模型；如果直接在基因空间做，就还得把一部分表示学习塞进后训练模型里，模型会复杂得多（[40:56](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2456)、[41:09](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2469)、[41:34](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2494)）。

模型把细胞系嵌入和药物嵌入组合起来，直接生成扰动细胞，不需要“对照—扰动”细胞配对；数据加载器从 $n^2$ 的配对变成 $n$ 级别，这是训练快的主要原因。模型里还有基因头，把生成的嵌入解码回表达空间；**联合训练**很重要，因为训练时输入的是“真实嵌入 + 高斯噪声”的混合，模型必须学会从带噪嵌入解码回表达（[41:34](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2494)、[41:59](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2519)、[42:24](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2544)、[42:49](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2569)）。

代价在推理：训练时可以在“纯高斯噪声 → 真实嵌入”的线性插值上一步预测速度，但推理时每个时间步都要一个速度项，要用 ODE 求解器迭代约 **50 步**才收敛到真实嵌入。先验用的是各向同性高斯，他们没有试别的先验结构（[43:34](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2614)、[43:59](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2639)、[44:24](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2664)、[44:49](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2689)）。

![BT2：在 Tahoe-x1 嵌入空间做条件生成，不需要对照—扰动配对](assets/BioML Seminar 4.4 - Shreshth Gandhi on Scaling Perturbation-Trained Single-Cell Foundation Models/b08_bt2.webp)

问答里进一步区分了“生成单个细胞”与“预测指标”：多数评测最后都会把细胞平均成细胞系层面的指标，例如 Virtual Cell Challenge 的指标就在细胞系层面；只有需要比较整个细胞群体分布时（例如用 MMD），才真的需要生成单个细胞。如果只关心细胞系层面的均值，直接预测分布参数或围绕质心采样可能就够了（[47:32](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2852)、[47:37](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2857)、[48:02](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2882)、[48:27](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2907)、[48:52](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2932)）。

## 十二、AutoResearch：一个晚上搜出来的模型，超过几年手工设计

讲者还讲了一个“最近两周”的新尝试：Tahoe-x1 是他们花了很多时间手工设计架构、做实验、做工程优化才得到的；他们好奇，如果把这件事交给一个自动研究智能体，会怎样（[44:49](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2689)、[45:03](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2703)）。

他们用 Google Brain 团队的一个新仓库（讲者称 **auto research**）搭了一个沙盒：给编码智能体数据访问权限，让它在有明确性能度量的前提下持续实验、发明新架构。任务选的是零样本预测，输入是 Tahoe-x1 嵌入的**质心**（每条细胞系一个向量）以及测试细胞系的基线嵌入，先用一个很简单的线性回归模型做种子，然后让它跑一整夜（[45:03](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2703)、[45:28](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2728)、[45:50](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2750)）。

因为在质心空间工作，训练非常简单：不生成单个细胞，而是直接预测最后的指标，因为多数指标本来就是伪 bulk 层面的。智能体可以直接建模“倍数变化”本身，结果发现这样效果相当好。讲者说，前面展示的那个很强的零样本结果，**不是人做的，而是 AutoResearch 完整搜出来的**；换不同数据划分，它看起来也是 state of the art（[45:50](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2750)、[46:15](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2775)、[46:40](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2800)、[46:52](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2812)、[46:57](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2817)）。

他的感慨很直接：过去几年做的很多工作，AI 一个晚上就能做完（[47:22](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2842)）。

## 十三、局限与下一步：跨数据集、原代细胞、可解释推理

讲者最后把边界和未来放在一起讲。

**第一，现有评测大多在同一数据集内划分。** 无论是少样本还是零样本，模型都能利用共享方差；他们真正想做的是 Tahoe 式的“滚动实验”：一批 1 亿细胞之后再来一批，模型随时间演化，并能泛化到药物集合完全不同的新数据集。这需要架构层面的创新（[49:15](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2955)、[49:20](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2960)、[49:45](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2985)）。

**第二，零样本仍然需要“种子数据”。** 新细胞系完全没数据时性能明显退化；作者的经验是至少给 **5–10 个药物**的小样本，才能接近“见过一百多个药物”的水平（[56:12](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=3372)、[56:37](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=3397)、[57:02](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=3422)）。

**第三，数据仍以体外癌细胞系为主。** 真实肿瘤有免疫细胞、基质、血管和空间结构，这些不在 Tahoe-100M 里；他们接下来想做原代细胞、iPSC 诱导细胞系，并对模型预测做前瞻性实验验证（[49:20](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2960)、[50:35](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=3035)、[51:00](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=3060)）。

**第四，算力与推理成本不低。** 3B 训练要 128 张 GPU、约 4.5 万美元；流匹配推理还要约 50 步 ODE。复现门槛并不低（[12:17](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=737)、[43:59](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2639)）。

**第五，组合扰动与遗传扰动还没覆盖。** 公开数据里基本没有药物组合；遗传扰动的组合也常见“加性基线就能做得差不多”的情况，他们自己还没试。把扰动预测作为预训练的辅助目标、和嵌入模型联合训练是可行的，只是更贵（[57:27](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=3447)、[57:52](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=3472)、[58:17](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=3497)、[58:42](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=3522)）。

**第六，dropout 没有被显式校正。** 他们假设 dropout 存在，希望掩码目标隐式地纠正它：模型在 dropout 程度不同的细胞上始终预测被遮的一半表达，训练目标会自己适应这种缺失（[59:57](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=3597)、[60:22](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=3622)、[60:47](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=3647)）。对 10x Visium 等空间测序技术，讲者表示自己了解不多，没有展开。

展望部分，讲者最兴奋的几条是（[49:45](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=2985)、[50:10](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=3010)、[50:35](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=3035)、[51:00](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=3060)）：

- 跨数据集、跨药物集合的泛化，以及随时间滚动的模型；
- 把 **LLM 推理模型**和嵌入结合，例如 BioReason 这类工作，不只给倍数变化，还给推理链，提升可解释性；
- 从癌细胞系走向原代细胞、iPSC，并做前瞻性验证；
- 把 AutoResearch 扩展到更大规模，让智能体自动探索架构，追求“指数级自我改进”。

问答里还提到：对药物发现管线最直接的价值，是零样本 Pearson 相关如果到 0.7，大约解释了 50% 的倍数变化信号；这样生物学家不必先花大成本获取细胞系和数据，就能在硅上先筛假设，减少试错成本。开源方面，他们欢迎贡献，尤其是 CLI 工具、化学 token 的探索，以及把作用机制（MoA）信息加入对比学习目标（[54:32](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=3272)、[54:57](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=3297)、[55:22](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=3322)、[55:47](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=3347)、[52:52](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=3172)、[53:17](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=3197)、[53:42](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=3222)、[54:07](https://www.youtube.com/watch?v=Nky3tlQ7phA&t=3247)）。

## 小结

- Tahoe-100M 用“混池 + 遗传解复用”把扰动数据做到约 1 亿细胞、50 条癌细胞系、约 1,200 个药物—剂量条件，成本换取约 50 倍通量；论文过滤后是 379 种药物、1,135 个组合。
- Tahoe-x1 把细胞写成“基因 token + 表达分箱 + Morgan 指纹药物 token”，用 CLS 表示整个细胞，用两个解码头逼出全局表示。
- 预训练语料约 2.5 亿细胞（1 亿 Tahoe + 1.5 亿公开图谱），模型有 70M / 1B / 3B 三个规模；3B 在 128 张 GPU 上训练，工程优化把成本压到约 4.5 万美元。
- 评估覆盖 DepMap 必需性、MSigDB 通路、细胞类型和扰动预测；规模越大越好，但部分任务提升有限。
- **少样本扰动预测接近噪声上限，零样本仍接近基线**；BT2 用流匹配把零样本推高，但没有改变“需要数据支持”这个前提。
- AutoResearch 一个晚上搜出的模型在零样本上达到 state of the art，说明架构搜索本身也可能成为规模化的一部分。
- 定位：Tahoe-x1 提供的是**细胞与基因的表征**，不是端到端的虚拟细胞；它的价值取决于下游模型，也受限于体外癌细胞系、数据覆盖与算力。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| 单细胞基础模型 | 在大量单细胞数据上自监督预训练、输出通用细胞/基因表示的模型 |
| CLS token | 序列开头的特殊标记，最后一层的 CLS 向量用来概括整个细胞 |
| Morgan 指纹 | 把分子结构编码成定长位串的经典化学信息学表示 |
| 掩码重建 | 遮住一部分输入，让模型从上下文预测被遮住的值 |
| DepMap | 用 CRISPR 敲除测基因必需性的公共数据库 |
| MSigDB hallmark | 一组按癌症相关功能整理的基因集 |
| PDCorr | 比较预测与真实的倍数变化向量的 Pearson 相关 |
| 流匹配 | 学习从噪声到数据分布的连续变换，用 ODE 逐步生成样本 |

## 相关阅读

- [GEARS：预测未见多基因组合的转录结果](<Graph Neural Networks User Group Meetup 9／29／2022.md>)
- [chemCPA：从化学结构预测未见药物](<Predicting Single-Cell Perturbation Responses For Unseen Drugs ｜ Leon Hetzel and Simon Böhm.md>)
- [Deep-learning-based Gene Perturbation Effect Prediction Does Not Yet Outperform Linear Baselines](Deep-learning-based Gene Perturbation Effect Prediction Does Not Yet Outperform Linear Baselines.md)
- [PerturBench: Benchmarking Machine Learning Models for Cellular Perturbation Analysis](<PerturBench：Benchmarking Machine Learning Models for Cellular Perturbation Analysis.md>)
