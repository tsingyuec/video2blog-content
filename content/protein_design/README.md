# 系列：AI + 蛋白质设计

- **平台**：Bilibili
- **来源**：BV1mkdwBoE6Z、BV1PudwBnEtq
- **视频数**：2
- **主题**：第 1 课从蛋白质结构基础出发，依次讲透「经典力场设计」（统计势、Rosetta 打分函数、无先验知识的 RF binder 设计）与「深度学习设计」（ANN、GNN、MPNN、ProteinMPNN）；第 2 课是实践操作，讲 RosettaScripts 脚本编写与 ProteinMPNN 网页工具的完整使用流程。

## 视频索引

| 视频键 | 标题 | 时长 | 视频演说图文稿 | 博客 | 配图 | 原视频 |
| --- | --- | ---: | --- | --- | ---: | --- |
| BV1mkdwBoE6Z | AI+蛋白质设计第1课（完整版） | 2:52:18 | [文稿](transcripts/第01讲_AI+蛋白质设计基础.md) | [博客](blog/第01讲_AI+蛋白质设计基础.md) | 16 | [B站](https://www.bilibili.com/video/BV1mkdwBoE6Z/) |
| BV1PudwBnEtq | AI+蛋白质设计第2课（完整版，实践操作） | 1:04:26 | [文稿](transcripts/第02讲_实践操作_RosettaScripts与ProteinMPNN.md) | [博客](blog/第02讲_实践操作_RosettaScripts与ProteinMPNN.md) | 11 | [B站](https://www.bilibili.com/video/BV1PudwBnEtq/) |

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

## 核心知识点速览

- **结构地基**：X 射线 / 冷冻电镜 / NMR 三大测定手段；PDB 文件各列含义与原子命名；结构四级层次、φ/ψ/ω 二面角与 Ramachandran 图；domain、motif、别构调控、同源建模；能量 = 分子力学 + 溶剂化能 → MM/PBSA、MM/GBSA、gmx_MMPBSA。
- **经典设计**：统计势 `U = -kT ln P`；Rosetta 打分函数 `ΔE_total = Σ w_i·E_i`（范德华拆 fa_atr/fa_rep、距离依赖介电常数静电、FASol/LKBWTD 溶剂化、氢键单列、rama_prepro/p_aa_pp 扭转能、rotamer 离散化）；能量零点与 ΔΔG；热点残基与 PPI 对接分析。
- **RF 方法**：攀岩类比（室内 hotspot vs 野外无先验）；RFgen 六维哈希表把采样复杂度降到 O(1)；小蛋白骨架库；RFdock；MULTIGRAFT 嫁接；聚类迭代；CD/SPR/ITC/酵母展示验证；局限指向经验能量函数的人为性。
- **深度学习**：ANN/DNN、RNN→LSTM、Transformer、CNN、GAN、GNN；MPNN 源于量子化学（替代 DFT）；ProteinMPNN 在已知骨架上设计序列，节点与边同步更新、随机解码、0.02 Å 骨架扰动，序列恢复率约 52% 且可溶性、稳定性更优，代价是失去物理可解释性。
- **实践**：`pwd`、`cd`、`ls`、`vim`、`cp`、`rm`、`source`、`sudo` 八个 Linux 命令。
- **RosettaScripts 实操**：XML 脚本 `<ROSETTASCRIPTS>` 一头一尾；七类模块 scorefunction（推荐 `beta_nov16`）、residue selector、task operation、SimpleMetrics、filter（SASA/ddG/shape complementarity/interface HB）、Mover、PROTOCOL；用 `-l` pdb list + `-parser:protocol` + `@xxx.flags` 运行；踩坑聚焦格式、命名、环境（`dos2unix`）。
- **ProteinMPNN 网页实操**：`RFdiffusion（生成无序列骨架）→ ProteinMPNN（设计序列）→ AlphaFold2（验证）` 流水线；关键参数 number、sampling temperature、model、omit amino acids、fixed positions；Colab vs Hugging Face 的取舍；读懂氨基酸概率热力图、pLDDT 与 PAE。
