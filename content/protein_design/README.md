# 系列：AI + 蛋白质设计

- **平台**：Bilibili、YouTube
- **来源**：BV1mkdwBoE6Z、BV1PudwBnEtq、BV1zu4y1J7MJ、o8JWPjSH1Ig、6z4XmUAwdNA
- **视频数**：5
- **主题**：第 1 课从蛋白质结构基础出发，依次讲透「经典力场设计」（统计势、Rosetta 打分函数、无先验知识的 RF binder 设计）与「深度学习设计」（ANN、GNN、MPNN、ProteinMPNN）；第 2 课是实践操作，讲 RosettaScripts 脚本编写与 ProteinMPNN 网页工具的完整使用流程；第 3 篇是 ProteinMPNN 原作者 Justas Dauparas 的论文精讲报告，系统讲清模型的动机、架构、消融、与 Rosetta 的对比、以及多状态设计等扩展；第 4 篇是 Ian Anderson 的实操讲解，从「图 / 局部注意力 / 消息传递」的概念入手，把 ProteinMPNN 与 ESM-IF、LigandMPNN 的发展脉络和输入特征讲清楚，并给出上手任务；第 5 篇是一节课程讲解，从「固定主链设计」讲到 Ingraham 2019 的 MPNN 与 ProteinMPNN 的架构、消融表和核心/表面性能分析。

## 视频索引

| 视频键 | 标题 | 时长 | 视频演说图文稿 | 博客 | 配图 | 原视频 |
| --- | --- | ---: | --- | --- | ---: | --- |
| BV1mkdwBoE6Z | AI+蛋白质设计第1课（完整版） | 2:52:18 | [文稿](transcripts/第01讲_AI+蛋白质设计基础.md) | [博客](blog/第01讲_AI+蛋白质设计基础.md) | 16 | [B站](https://www.bilibili.com/video/BV1mkdwBoE6Z/) |
| BV1PudwBnEtq | AI+蛋白质设计第2课（完整版，实践操作） | 1:04:26 | [文稿](transcripts/第02讲_实践操作_RosettaScripts与ProteinMPNN.md) | [博客](blog/第02讲_实践操作_RosettaScripts与ProteinMPNN.md) | 11 | [B站](https://www.bilibili.com/video/BV1PudwBnEtq/) |
| BV1zu4y1J7MJ | ProteinMPNN 论文精读：稳健的深度学习蛋白质序列设计 | 53:42 | [文稿](transcripts/ProteinMPNN论文精读_稳健的深度学习蛋白质序列设计.md) | [博客](blog/ProteinMPNN论文精读_稳健的深度学习蛋白质序列设计.md) | 18 | [B站](https://www.bilibili.com/video/BV1zu4y1J7MJ/) |
| o8JWPjSH1Ig | 用 ProteinMPNN 进行逆折叠（实操讲解） | 29:56 | [文稿](transcripts/用ProteinMPNN进行逆折叠.md) | [博客](blog/用ProteinMPNN进行逆折叠.md) | 11 | [YouTube](https://youtu.be/o8JWPjSH1Ig) |
| 6z4XmUAwdNA | MPNN：用机器学习做蛋白质序列设计 | 25:30 | [文稿](transcripts/MPNN：用机器学习做蛋白质序列设计.md) | [博客](blog/MPNN：用机器学习做蛋白质序列设计.md) | 8 | [YouTube](https://youtu.be/6z4XmUAwdNA) |

## 博客结构速览

**第 1 讲：AI + 蛋白质设计基础——从经典力场到深度学习**

- 一、蛋白质结构基础：从数据获取到能量计算（PDB / UniProt、二面角、MM/PBSA）
- 二、基于统计势函数的蛋白质设计：Rosetta 打分函数
- 三、无先验知识的蛋白质药物设计：RF 方法
- 四、基于深度学习的蛋白质设计：从 ANN 到 ProteinMPNN
- 五、实践准备：Linux 常用命令速成

**第 2 讲：实践操作——RosettaScripts 与 ProteinMPNN 网页工具**

- 一、RosettaScripts 实操：用 XML 脚本编排蛋白质设计（七类模块、两个例子、design、运行与踩坑）
- 二、ProteinMPNN 网页工具实操：从骨架到序列再到 AlphaFold2 验证（参数、Colab/Hugging Face、结果解读）

**第 3 篇：ProteinMPNN 论文精读——稳健的深度学习蛋白质序列设计**

- 一、ProteinMPNN 是什么：给骨架「配」序列的逆折叠模型（结构↔序列、类比、问题陈述）
- 二、实验证明它能干什么：从一个失败到拿到晶体结构（对称蛋白增溶、大结构、纳米颗粒、模体支架、binder）
- 三、模型怎么设计：轻量、局部、抗噪（数据防泄露、交叉熵、自回归+随机解码、输入特征、编解码器、主链噪声）
- 四、为什么这样设计：逐项消融（距离特征 41%→49%、边更新、随机解码）
- 五、表现如何：与 Rosetta 对比的四个发现（核心 90%、几何函数、采样温度、氨基酸偏差、不确定性排序）
- 六、如何评估与扩展：正向折叠、共识序列、多状态设计、开源易用
- 七、问答精选

**第 4 篇：用 ProteinMPNN 进行逆折叠——从图、注意力到消息传递**

- 一、先修概念：图（序列相似性网络）、局部注意力 vs 全局注意力
- 二、逆折叠简史：Ingraham 2019（K=30）→ ESM-IF 2022（1200 万结构、54%）→ ProteinMPNN 2022
- 三、ProteinMPNN 怎么工作：消息传递 ≠ 注意力、16 维距离输入、三轮编码、概率矩阵与温度
- 四、局限与后续版本：可溶权重、LigandMPNN
- 五、实操任务：ProteinMPNN vs LigandMPNN、换折叠模型、MSA 找最不保守位点

**第 5 篇：MPNN——用机器学习做蛋白质序列设计（课程讲解）**

- 一、从结构预测到序列设计：固定主链设计
- 二、复习蛋白质的机器学习表示（one-hot、进化信息、二级结构、距离/角度、表面、坐标、图）
- 三、MPNN 基础架构（Ingraham 2019）：消息传递、自回归、边特征（邻域/稀疏/朝向）、对比 Rosetta
- 四、ProteinMPNN：架构总览、随机解码 + 绑定链、性能分解表
- 五、性能分析：核心 vs 表面、单体 vs 多聚体

## 核心知识点速览

- **结构地基**：X 射线 / 冷冻电镜 / NMR 三大测定手段；PDB 文件各列含义与原子命名；结构四级层次、φ/ψ/ω 二面角与 Ramachandran 图；domain、motif、别构调控、同源建模；能量 = 分子力学 + 溶剂化能 → MM/PBSA、MM/GBSA、gmx_MMPBSA。
- **经典设计**：统计势 `U = -kT ln P`；Rosetta 打分函数 `ΔE_total = Σ w_i·E_i`（范德华拆 fa_atr/fa_rep、距离依赖介电常数静电、FASol/LKBWTD 溶剂化、氢键单列、rama_prepro/p_aa_pp 扭转能、rotamer 离散化）；能量零点与 ΔΔG；热点残基与 PPI 对接分析。
- **RF 方法**：攀岩类比（室内 hotspot vs 野外无先验）；RFgen 六维哈希表把采样复杂度降到 O(1)；小蛋白骨架库；RFdock；MULTIGRAFT 嫁接；聚类迭代；CD/SPR/ITC/酵母展示验证；局限指向经验能量函数的人为性。
- **深度学习**：ANN/DNN、RNN→LSTM、Transformer、CNN、GAN、GNN；MPNN 源于量子化学（替代 DFT）；ProteinMPNN 在已知骨架上设计序列，节点与边同步更新、随机解码、0.02 Å 骨架扰动，序列恢复率约 52% 且可溶性、稳定性更优，代价是失去物理可解释性。
- **实践**：`pwd`、`cd`、`ls`、`vim`、`cp`、`rm`、`source`、`sudo` 八个 Linux 命令。
- **RosettaScripts 实操**：XML 脚本 `<ROSETTASCRIPTS>` 一头一尾；七类模块 scorefunction（推荐 `beta_nov16`）、residue selector、task operation、SimpleMetrics、filter（SASA/ddG/shape complementarity/interface HB）、Mover、PROTOCOL；用 `-l` pdb list + `-parser:protocol` + `@xxx.flags` 运行；踩坑聚焦格式、命名、环境（`dos2unix`）。
- **ProteinMPNN 网页实操**：`RFdiffusion（生成无序列骨架）→ ProteinMPNN（设计序列）→ AlphaFold2（验证）` 流水线；关键参数 number、sampling temperature、model、omit amino acids、fixed positions；Colab vs Hugging Face 的取舍；读懂氨基酸概率热力图、pLDDT 与 PAE。
- **ProteinMPNN 论文精读**：逆折叠（结构→序列）；按单链收集 PDB、30% 一致性、3.5 Å、>70% 相似则必须预测所有链以防泄露；逐残基交叉熵；自回归 + 随机解码顺序；局部邻域 + ±32 相对位置 + 链内/间指示 + 16 通道 RBF 距离编码；3 层编码器 + 3 层解码器、约 170 万参数；训练加 0.02–0.3 Å 主链高斯噪声、推理不加；消融：距离特征 41%→49%；核心区恢复率约 90% 且全面优于 Rosetta；采样温度控制确定性/多样性；模型偏爱在表面放 Glu/Lys（有助可溶）；负对数概率可给设计排序；支持正向折叠、共识序列、多状态/伪对称设计。
- **逆折叠实操**：逆折叠 = 结构→序列；图（节点/边）、序列相似性网络、局部注意力（Ingraham K=30）vs 全局注意力（ESM-IF）；三代模型 Ingraham 2019（50%）→ ESM-IF 2022（折 1200 万结构、54%、但慢/幻觉/合成偏置）→ ProteinMPNN；ProteinMPNN 不是 Transformer，用消息传递（48 邻居、不加权求和）而非注意力，边输入为 16 维主链原子两两距离（最近邻仅用 Cα 是隐患），编码器三轮 48³ 覆盖，解码器输出概率矩阵、温度 >1 退化；后续：可溶性权重、LigandMPNN（1D 配体-配体、6D 蛋白-配体、映射到 128 维）。
- **MPNN 课程讲解**：固定主链设计（主链不动、只设计序列）；MPNN = 消息传递神经网络，节点=残基、边=几何关系（距离/方向/旋转）；自回归逐位预测、交叉熵损失；边特征含邻域大小（越近越重要）与朝向（点云+坐标系）；Ingraham 2019 在 103 蛋白上 27.6% vs Rosetta 17.9%，速度 CPU/GPU 快几个数量级；ProteinMPNN 三处改进（加 N/Cα/C/Cβ/O 距离、更新编码器边、随机解码顺序）→ 41.2%→50.8%（AlphaFold 准确率 46.9%），支持多链与同源多聚体的绑定链解码；性能规律：核心比表面易恢复（埋藏度），多聚体（0.55）略优于单体（0.52）。
