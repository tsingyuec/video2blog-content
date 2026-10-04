# 分组：AI + 蛋白质（Protein）

- **平台**：Bilibili、YouTube、GitHub、个人博客
- **说明**：本分组汇集与「蛋白质」相关的四个系列——结构预测与算法解析（alphafold）、蛋白质设计（从经典力场到深度学习，protein_design）与 Rosetta 系列工作坊 / 训练营（protein_interaction、protein_ml_bootcamp）。
- **共同主线**：现代蛋白质工程的一条完整流水线——**结构预测与验证（AlphaFold2 / AlphaFold3 / ESMFold / OpenFold）→ 骨架生成（RFdiffusion / RF 方法）→ 序列设计（MPNN / ProteinMPNN / LigandMPNN）→ 打分与实验分析（Rosetta 打分函数、DockQ、pLDDT/PAE）**。四个系列分别从「算法解析」「设计原理」「相互作用 / binder 设计」「机器学习工具链」切入，可互相参照。

## 系列索引

| 系列 | 主题 | 视频数 | 入口 |
| --- | --- | --- | --- |
| protein_design | AI + 蛋白质设计（从经典力场到深度学习、AlphaFold 实践） | 12 | [protein_design](protein_design/README.md) |
| alphafold | AlphaFold 图解与算法解析（中译长文 + 中文逐层拆解 + 视频博客） | 9 篇 | [alphafold](alphafold/README.md) |
| protein_interaction | Rosetta 蛋白-蛋白相互作用（PPI）设计工作坊（2025） | 8（已整理 2） | [protein_interaction](protein_interaction/README.md) |
| protein_ml_bootcamp | Rosetta ML Bootcamp：蛋白质建模与设计的机器学习方法 | 18（已整理 7） | [protein_ml_bootcamp](protein_ml_bootcamp/README.md) |

## 各系列简介

### [protein_design](protein_design/README.md) — AI + 蛋白质设计

从**经典力场设计**（统计势、Rosetta 打分函数、无先验知识的 RF binder 设计）讲到**深度学习设计**（ANN、GNN、MPNN、ProteinMPNN），并配实践操作（RosettaScripts、ProteinMPNN 网页工具）。同时保留 **AlphaFold 实践**内容：AlphaFold3 官方文档「输入设置」两集，以及一篇《AlphaFold 的原理和展望》（讲清 AlphaFold2 为什么准、AlphaFold-Multimer 的复合物预测与工程优化）。更偏算法与架构解析的 AlphaFold 资料见 [alphafold 系列](alphafold/README.md)。

### [alphafold](alphafold/README.md) — AlphaFold 图解与算法解析

专门收录 AlphaFold（AF2/AF3）架构与算法的中文资料：英文长文 *The Illustrated AlphaFold*（Elana Simon、Jake Silberg）的中文翻译、GitHub 仓库 `shenyichong/alphafold3-architecture-walkthrough` 的中文逐层拆解（输入准备 / 表征学习 / 结构预测 / 损失函数），以及从 `protein_design` 迁移过来的 4 篇视频博客（AlphaFold2 关键算法介绍、AlphaFold3 算法详解 01–03）。适合从「整体直觉」到「逐张量实现」逐级深入。

### [protein_interaction](protein_interaction/README.md) — 蛋白-蛋白相互作用设计工作坊

2025 年 Rosetta Commons 主办的 PPI 设计工作坊（主讲 Amrita Nallathambi）。以「结合体（binder）设计 + 笼状（cage）组装」为主线，串起 **RFdiffusion 生成骨架 → ProteinMPNN 设计序列 → AlphaFold 预测验证 → Rosetta 打分分析** 的经典流水线。目前整理前 2 讲（总览 + 深度学习导论）。

### [protein_ml_bootcamp](protein_ml_bootcamp/README.md) — Rosetta ML Bootcamp

2024 年 Rosetta Commons 主办的机器学习训练营（主讲 Nick Randolph）。前半程打地基——蛋白质与深度学习复习、常用工具（PyMOL / VS Code）、结构预测（Anfinsen 假说、Levinthal 悖论、CASP、评价指标、AlphaFold）；后半程进入设计主流程——**AlphaFold2/OpenFold/ESMFold/AlphaFold3 结构预测 → RFdiffusion 生成骨架 → ProteinMPNN/LigandMPNN 设计序列 → DiffDock-PP 分子对接**。目前整理前 7 讲，并附 PyMOL 配套代码。

## 各主线之间的交汇

- **结构预测与算法解析**：`alphafold` 集中了 AlphaFold2/3 的中译长文与逐层拆解；`protein_design` 提供 AlphaFold3 官方文档精讲与实践向的《原理和展望》；`protein_ml_bootcamp` 提供从 AlphaFold2 到 ESMFold/AlphaFold3 的实操横向对比。
- **序列设计**：`protein_design` 覆盖 MPNN / ProteinMPNN 的理论与论文精读，`protein_ml_bootcamp` 与 `protein_interaction` 给出 ProteinMPNN / LigandMPNN 的上手与工作流位置。
- **骨架与验证**：`protein_interaction` 与 `protein_ml_bootcamp` 都把 RFdiffusion、AlphaFold 验证、Rosetta 打分串成可复现的设计闭环。
