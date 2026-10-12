# 分组：AI + 蛋白质（Protein）

- **平台**：Bilibili、YouTube、GitHub、个人博客
- **说明**：本分组下辖 Rosetta 系列工作坊 / 训练营两个系列——蛋白-蛋白相互作用（PPI）设计工作坊（protein_interaction）与机器学习训练营（protein_ml_bootcamp）。
- **共同主线**：现代蛋白质工程的一条完整流水线——**结构预测与验证（AlphaFold2 / AlphaFold3 / ESMFold / OpenFold）→ 骨架生成（RFdiffusion / RF 方法）→ 序列设计（MPNN / ProteinMPNN / LigandMPNN）→ 打分与实验分析（Rosetta 打分函数、DockQ、pLDDT/PAE）**。本分组从「相互作用 / binder 设计」与「机器学习工具链」切入，可与 [biomodel](../biomodel/README.md) 下的模型专题互相参照。

> 原属本分组的 `protein_design`、`alphafold` 两个系列已按「具体模型」重组进 [biomodel](../biomodel/README.md)（现含 alphafold / proteinmpnn / rfdiffusion / rosettafold / protein_design / highfold 六个模型专题）。

## 系列索引

| 系列 | 主题 | 视频数 | 入口 |
| --- | --- | --- | --- |
| protein_interaction | Rosetta 蛋白-蛋白相互作用（PPI）设计工作坊（2025） | 8（已整理 2） | [protein_interaction](protein_interaction/README.md) |
| protein_ml_bootcamp | Rosetta ML Bootcamp：蛋白质建模与设计的机器学习方法 | 18（已整理 7） | [protein_ml_bootcamp](protein_ml_bootcamp/README.md) |

## 各系列简介

### [protein_interaction](protein_interaction/README.md) — 蛋白-蛋白相互作用设计工作坊

2025 年 Rosetta Commons 主办的 PPI 设计工作坊（主讲 Amrita Nallathambi）。以「结合体（binder）设计 + 笼状（cage）组装」为主线，串起 **RFdiffusion 生成骨架 → ProteinMPNN 设计序列 → AlphaFold 预测验证 → Rosetta 打分分析** 的经典流水线。目前整理前 2 讲（总览 + 深度学习导论）。

### [protein_ml_bootcamp](protein_ml_bootcamp/README.md) — Rosetta ML Bootcamp

2024 年 Rosetta Commons 主办的机器学习训练营（主讲 Nick Randolph）。前半程打地基——蛋白质与深度学习复习、常用工具（PyMOL / VS Code）、结构预测（Anfinsen 假说、Levinthal 悖论、CASP、评价指标、AlphaFold）；后半程进入设计主流程——**AlphaFold2/OpenFold/ESMFold/AlphaFold3 结构预测 → RFdiffusion 生成骨架 → ProteinMPNN/LigandMPNN 设计序列 → DiffDock-PP 分子对接**。目前整理前 7 讲，并附 PyMOL 配套代码。
