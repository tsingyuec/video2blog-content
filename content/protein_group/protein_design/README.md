# 系列：AI + 蛋白质设计

- **平台**：Bilibili、YouTube
- **来源**：BV1mkdwBoE6Z、BV1PudwBnEtq、BV1zu4y1J7MJ、o8JWPjSH1Ig、6z4XmUAwdNA、BV1VBdDYLE8i、YouTube c2kFHtuEt8s、8rePVA8rpoY、s75eFLYe3cc、BV1yzzjYZETU、BV11BzjYbEgD、BV1fm4y1D7Wz
- **视频数**：12
- **主题**：第 1 课从蛋白质结构基础出发，依次讲透「经典力场设计」（统计势、Rosetta 打分函数、无先验知识的 RF binder 设计）与「深度学习设计」（ANN、GNN、MPNN、ProteinMPNN）；第 2 课是实践操作，讲 RosettaScripts 脚本编写与 ProteinMPNN 网页工具的完整使用流程；第 3 篇是 ProteinMPNN 原作者 Justas Dauparas 的论文精讲报告，系统讲清模型的动机、架构、消融、与 Rosetta 的对比、以及多状态设计等扩展；第 4 篇是 Ian Anderson 的实操讲解，从「图 / 局部注意力 / 消息传递」的概念入手，把 ProteinMPNN 与 ESM-IF、LigandMPNN 的发展脉络和输入特征讲清楚，并给出上手任务；第 5 篇是一节课程讲解，从「固定主链设计」讲到 Ingraham 2019 的 MPNN 与 ProteinMPNN 的架构、消融表和核心/表面性能分析；第 6 篇把视角从蛋白质扩展到 DNA/RNA，讲清如何把 FASTA 序列与原子坐标处理成图神经网络的输入（字母编码、Top-K 邻接图、二面角/RBF/方向等节点与边特征）。其后新增 AlphaFold3 官方文档讲解的「输入设置」两集（序列定义与整体结构、MSA/模板/共价键/CCD）。最新收录一篇「AlphaFold 的原理和展望」（钟博子韬，钰沐菡公益公开课）：从五大关键设计讲清 AlphaFold2 为什么准、AlphaFold-Multimer 复合物预测的改进与不足，并给出作者的高通量工程优化（POWERFOLD）与大量实测案例，重点回答「AlphaFold 到底学到了什么、能做什么、不能做什么」。

## 视频索引

| 视频键 | 标题 | 时长 | 视频演说图文稿 | 博客 | 配图 | 原视频 |
| --- | --- | ---: | --- | --- | ---: | --- |
| BV1mkdwBoE6Z | AI+蛋白质设计第1课（完整版） | 2:52:18 | [文稿](transcripts/第01讲_AI+蛋白质设计基础.md) | [博客](blog/第01讲_AI+蛋白质设计基础.md) | 16 | [B站](https://www.bilibili.com/video/BV1mkdwBoE6Z/) |
| BV1PudwBnEtq | AI+蛋白质设计第2课（完整版，实践操作） | 1:04:26 | [文稿](transcripts/第02讲_实践操作_RosettaScripts与ProteinMPNN.md) | [博客](blog/第02讲_实践操作_RosettaScripts与ProteinMPNN.md) | 11 | [B站](https://www.bilibili.com/video/BV1PudwBnEtq/) |
| BV1zu4y1J7MJ | ProteinMPNN 论文精读：稳健的深度学习蛋白质序列设计 | 53:42 | [文稿](transcripts/ProteinMPNN论文精读_稳健的深度学习蛋白质序列设计.md) | [博客](blog/ProteinMPNN论文精读_稳健的深度学习蛋白质序列设计.md) | 18 | [B站](https://www.bilibili.com/video/BV1zu4y1J7MJ/) |
| o8JWPjSH1Ig | 用 ProteinMPNN 进行逆折叠（实操讲解） | 29:56 | [文稿](transcripts/用ProteinMPNN进行逆折叠.md) | [博客](blog/用ProteinMPNN进行逆折叠.md) | 11 | [YouTube](https://youtu.be/o8JWPjSH1Ig) |
| 6z4XmUAwdNA | MPNN：用机器学习做蛋白质序列设计 | 25:30 | [文稿](transcripts/MPNN：用机器学习做蛋白质序列设计.md) | [博客](blog/MPNN：用机器学习做蛋白质序列设计.md) | 8 | [YouTube](https://youtu.be/6z4XmUAwdNA) |
| BV1VBdDYLE8i | 【AI4science】如何将DNA/RNA数据输入机器学习或深度学习网络模型！ | 12:17 | [文稿](transcripts/DNA与RNA数据如何输入机器学习模型.md) | [博客](blog/DNA与RNA数据如何输入机器学习模型.md) | 14 | [B站](https://www.bilibili.com/video/BV1VBdDYLE8i/) |
| c2kFHtuEt8s | Lecture 1 - Protein transformers from scratch | 13:09 | [文稿](transcripts/从零实现蛋白质Transformer（第1讲）.md) | — | — | [YouTube](https://youtu.be/c2kFHtuEt8s) |
| 8rePVA8rpoY | Lecture 2 - Protein transformers from scratch | 25:11 | [文稿](transcripts/从零实现蛋白质Transformer（第2讲）.md) | — | — | [YouTube](https://youtu.be/8rePVA8rpoY) |
| s75eFLYe3cc | Lecture 3 - Protein transformers from scratch | 26:43 | [文稿](transcripts/从零实现蛋白质Transformer（第3讲）.md) | — | — | [YouTube](https://youtu.be/s75eFLYe3cc) |
| BV1yzzjYZETU | alphafold3官方文档讲解:01 输入设置:兼容性,整体结构,序列定义 | 10:57 | [文稿](transcripts/AlphaFold3官方文档讲解01_输入设置_序列定义与整体结构.md) | [博客](blog/AlphaFold3官方文档讲解01_输入设置_序列定义与整体结构.md) | 9 | [B站](https://www.bilibili.com/video/BV1yzzjYZETU/) |
| BV11BzjYbEgD | alphafold3官方文档讲解:02 输入设置:MSA,模板,共价键,CCD定义 | 12:27 | [文稿](transcripts/AlphaFold3官方文档讲解02_输入设置_MSA模板共价键与CCD.md) | [博客](blog/AlphaFold3官方文档讲解02_输入设置_MSA模板共价键与CCD.md) | 11 | [B站](https://www.bilibili.com/video/BV11BzjYbEgD/) |
| BV1fm4y1D7Wz | AlphaFold的原理和展望 - 钟博子韬 \| 钰沐菡 公益公开课 | 1:17:03 | [文稿](transcripts/AlphaFold的原理和展望.md) | [博客](blog/AlphaFold的原理和展望.md) | 18 | [B站](https://www.bilibili.com/video/BV1fm4y1D7Wz/) |

> 说明：`c2kFHtuEt8s` / `8rePVA8rpoY` / `s75eFLYe3cc` 来自 Alex Carlin 的《Protein transformers from scratch》系列（播放列表共 3 讲），目前仅收录视频演说图文稿，博客暂缺。
>
> AlphaFold 相关的 4 篇博客（`AlphaFold2关键算法介绍`、`AlphaFold3算法详解 01–03`）已迁移至 [alphafold 系列](../alphafold/README.md)。

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

**第 6 篇：DNA/RNA 数据如何输入机器学习模型——从序列到几何图**

- 一、结构定级别：一级看序列、二级看连接、三级看空间
- 二、数据长什么样：FASTA 序列 + `.npy` 坐标（每残基 P/O5'/C5'/C4'/C3'/O3' 六原子）
- 三、`create_dataset`：SeqIO 读 FASTA、`np.load` 读坐标并按原子拆列
- 四、一级结构处理：`alphabet='AUCG'` 字母编码、padding 对齐、mask 标记有效位
- 五、三级结构第一步：用距离 + Top-K 近邻构建邻接图（`_dist`、`E_idx`）
- 六、节点特征：二面角（α/β/γ/δ/ε/ζ/χ 转 cos/sin）+ RBF 距离升维 + 方向/朝向
- 七、边特征与最终产物：原子对 RBF 距离汇总成 `h_E`，输出序列/节点/边/邻接/batch

**AlphaFold3 输入设置（一）：序列定义与整体结构**

- 一、先分清两套输入格式：服务器版（旧）与开源版（新）（`--json_path`/`--input_dir`、自动转换、不能塞列表）
- 二、顶层 JSON 结构：认识 7 个字段（name、modelSeeds、sequences、bondedAtomPairs、userCCD、dialect、version）
- 三、序列定义：蛋白 / RNA / DNA / 配体（id、sequence、modifications、MSA、模板、配体三种写法）

**AlphaFold3 输入设置（二）：MSA、模板、共价键与 CCD**

- 一、MSA：让模型「看到」进化信息（RNA 三种写法、蛋白五种组合、自己提供 MSA 的三条硬规矩、多链 MSA 匹配）
- 二、结构模板：只对蛋白有意义（mmcif、queryIndices、templateIndices）
- 三、共价键：把实体「焊」在一起（bondedAtomPairs 的原子三字段、仅支持共价键）
- 四、聚糖与用户自定义 CCD（用配体表示聚糖、userCCD 三条格式规则、CCDUtils）

**AlphaFold 的原理和展望——从序列到结构，它到底学到了什么、能做什么、不能做什么**

- 一、为什么需要蛋白质结构预测：从中心法则、Anfinsen's Dogma 到序列/结构 gap 与 CASP
- 二、传统思路：多序列比对 → 共进化 → Contact Map，AlphaFold 一代（2018）
- 三、AlphaFold2 的五大关键设计：MSA、Recycling、Evoformer、Structure Module、pLDDT（+ 自蒸馏）
- 四、AlphaFold2 到底学到了什么：共进化 ≠ 物理，学的是「序列→晶体结构」
- 五、AlphaFold-Multimer（2.1）：cross-chain MSA 配对、链间不设阈值的 FAPE、ipTM
- 六、讲者的工程改造与实测：POWERFOLD 高通量优化，pLDDT/PAE 评估，好/中/差三类案例
- 七、怎样正确使用：版本选择、环境与运行时间、常见报错（HHblits 先更新 UniClust 数据库等）
- 八、能做什么、不能做什么：结构可预测，稳定性/功能不能（但可接 MLP「捞」稳定性）
- 九、答疑精选（受力信息、柔性 linker、抗原抗体、动态折叠、复合物判读等）

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
- **DNA/RNA 输入**：RNA/DNA 分三级结构（一级序列 / 二级连接关系 / 三级空间构象）；FASTA 提供序列，`.npy` 提供坐标（每残基 P、O5'、C5'、C4'、C3'、O3' 六主链原子，形状 `(N,6,3)`）；一级处理用 `alphabet='AUCG'` 编码 + padding + mask；三级把结构转成几何图——选主链代表原子（代码用 P）定位残基，`_dist` 算两两距离并取 Top-K 近邻得到邻接关系 `E_idx`；节点特征 = 二面角（α/β/γ/δ/ε/ζ/χ，转 cos/sin）+ RBF 距离升维（`num_rbf=16`）+ 方向/朝向；边特征用 `P-P、O5-P、C5-P、C4-P、C3-P、O3-P` 原子对的 RBF 距离汇总；最终产出序列 `S`、节点 `h_V`、边 `h_E`、邻接矩阵与 batch，可直接输入图神经网络。
- **AlphaFold3 输入（一）**：两套格式——旧 `alphafoldserver` 可被 `run_alphafold.py` 自动转成新 `alphafold3`；指定文件用 `--json_path` / `--input_dir`，新版一个 JSON 只对应一个任务（塞列表报错）；顶层 7 字段 name / modelSeeds / sequences / bondedAtomPairs / userCCD / dialect / version；新版种子必须显式指定且写成列表、离子统一视为配体、每个实体需唯一大写 id（列表表示同聚物）；蛋白含 modifications/unpairedMsa/pairedMsa/templates，RNA 只有 unpairedMsa 无配对/模板，DNA 只有序列与修饰，配体三法（ccdCodes / smiles / 自定义 CCD）互斥。
- **AlphaFold3 输入（二）**：MSA 不设即自动用 Jackhmmer/Hmmer 搜库；RNA 的 unpairedMsa 三态（null / "" / A3M），蛋白 unpairedMsa+pairedMsa 五种组合且「一起设或一起不设」；自提供 MSA 需 A3M 格式、首条=查询序列、非插入长度一致；多链才需 MSA 匹配（靠 pairedMsa 的 UniProt 物种 id）；模板只对蛋白有效（mmcif/queryIndices/templateIndices，0 基、等长、单链）；bondedAtomPairs 用 (实体 id, 残基号 1 基, 原子名) 描述、仅支持共价键；聚糖用配体+共价键；userCCD 名不含下划线、换行用 `\n`、化学式单引号，可用 CCDUtils 生成。
- **AlphaFold 原理和展望**：AlphaFold2 五大设计——MSA（UniRef/MGnify/BFD + PDB 70% 去重，决定精度上限，深度 >30 即可、>100 无益）、Recycling（输出回灌输入，默认 3 轮共 4 次，复杂蛋白如 T1064 到第 4 轮才折叠正确）、Evoformer（MSA 表示 × pair 表示，逐行/列注意力 + 三角几何更新）、Structure Module（IPA + residue gas，3D 等变、全原子输出、无需 refinement，仅 AMBER 侧链优化）、pLDDT（逐残基 0–100 置信度，>90 准、<50 基本错）；本质是「共进化 → contact」而非物理，学的是「序列 → 晶体结构」；Multimer（2.1）通过 cross-chain MSA 配对（原核用基因组距离、真核用序列相似性排序）、链间不设阈值的 FAPE、新增 ipTM（model confidence=0.8·ipTM+0.2·pTM）预测复合物，但常「训练过度、坍缩成球」，建议与 ColabFold（AF2+gap）并用；POWERFOLD 把 CPU/GPU 串行流程拆分、多线程加速 MSA（-67%）、减少重复编译，约 2 万小蛋白在 16 张 V100 上从上千小时降到 3–5 小时；实测：突变结构（GA98/GB98）可试不保、Ras-Raf 极好（0.898）、TCR-MHC 中等（0.552）、RBD-ACE2 失败（0.333、偏向柔性区）、Spike 三聚体坍缩、Aβ42 淀粉样 Multimer 失败而 ColabFold 更像；常见报错：MSA 内存不足（加内存/核数）、HHblits failed（把 UniClust 从 2018-08 更新到 2020-06）、IndexError（复合物任务误用单体模型）、CUDA OOM（多卡共享显存）、Tensor >2GB（限制 MSA 深度）、运行极慢（检查 GPU/CUDA）；能力边界：不能预测稳定性（pLDDT/ΔΔG 相关性差，接 MLP 后 r≈0.8），更不能预测功能（GFP 荧光与 pLDDT 几乎无关）。
