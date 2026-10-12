# 分组：生物大分子建模（biomodel）

本分组按**具体模型 / 工具**收录生物大分子（蛋白质、多肽、复合物）的结构预测与设计博客。

每个子目录对应一个模型主题，目录内**直接存放博客 `.md` 与配图 `assets/`**（不再有 `README.md` 与 `blog/`）；本页即为整个分组的统一索引。

## 模型索引

| 子目录 | 主题 | 篇数 |
| --- | --- | ---: |
| `alphafold/` | AlphaFold2 / AlphaFold3 架构、算法与官方文档详解 | 12 |
| `proteinmpnn/` | ProteinMPNN / MPNN：逆折叠序列设计 | 3 |
| `rfdiffusion/` | RFdiffusion / RFdiffusion3：骨架生成与 binder 设计 | 3 |
| `rosettafold/` | RoseTTAFold All-Atom 论文精读 | 1 |
| `protein_design/` | 蛋白质设计通识与课程（经典力场 → 深度学习） | 3 |
| `highfold/` | HighFold / 环肽与二硫键结构预测 | 2 |

## `alphafold/` — AlphaFold 图解与算法解析

专门收录 **AlphaFold（AlphaFold2 / AlphaFold3）架构与算法**的中文整理资料：既有英文优质长文的中文翻译，也有中文社区原创的逐层拆解，以及来自视频讲解的图文博客，适合从「整体直觉」到「逐张量实现」逐级深入。

| 名称 | 类型 | 来源 | 博客 | 配图 |
| --- | --- | --- | --- | ---: |
| AlphaFold3 图解（The Illustrated AlphaFold） | 图文长文（中文翻译） | [elanapearl.github.io](https://elanapearl.github.io/blog/2024/the-illustrated-alphafold/) | [博客](alphafold/AlphaFold3图解_The%20Illustrated%20AlphaFold.md) | 52 |
| AlphaFold3 架构解析 01：输入准备 | 中文逐层拆解（已通顺化） | [GitHub](https://github.com/shenyichong/alphafold3-architecture-walkthrough) | [博客](alphafold/AlphaFold3架构解析01_输入准备.md) | 31 |
| AlphaFold3 架构解析 02：表征学习 | 中文逐层拆解（已通顺化） | [GitHub](https://github.com/shenyichong/alphafold3-architecture-walkthrough) | [博客](alphafold/AlphaFold3架构解析02_表征学习.md) | 19 |
| AlphaFold3 架构解析 03：结构预测 | 中文逐层拆解（已通顺化） | [GitHub](https://github.com/shenyichong/alphafold3-architecture-walkthrough) | [博客](alphafold/AlphaFold3架构解析03_结构预测.md) | 22 |
| AlphaFold3 架构解析 04：损失函数 | 中文逐层拆解（已通顺化） | [GitHub](https://github.com/shenyichong/alphafold3-architecture-walkthrough) | [博客](alphafold/AlphaFold3架构解析04_损失函数.md) | 16 |
| AlphaFold2 关键算法介绍 | 视频博客 | [B站 BV1ucYmesENM](https://www.bilibili.com/video/BV1ucYmesENM/) | [博客](alphafold/AlphaFold2关键算法介绍.md) | 13 |
| AlphaFold3 算法详解 01：输入处理 | 视频博客 | [B站 BV1CNeKeYE7u](https://www.bilibili.com/video/BV1CNeKeYE7u/) | [博客](alphafold/AlphaFold3算法详解01_输入处理.md) | 11 |
| AlphaFold3 算法详解 02：Pairformer | 视频博客 | [B站 BV1kNeKeYEEn](https://www.bilibili.com/video/BV1kNeKeYEEn/) | [博客](alphafold/AlphaFold3算法详解02_Pairformer.md) | 12 |
| AlphaFold3 算法详解 03：扩散部分 | 视频博客 | [B站 BV1ANeKeeESs](https://www.bilibili.com/video/BV1ANeKeeESs/) | [博客](alphafold/AlphaFold3算法详解03_扩散部分.md) | 8 |
| AlphaFold3 官方文档讲解 01：输入设置（序列定义与整体结构） | 视频博客 | [B站 BV1yzzjYZETU](https://www.bilibili.com/video/BV1yzzjYZETU/) | [博客](alphafold/AlphaFold3官方文档讲解01_输入设置_序列定义与整体结构.md) | 9 |
| AlphaFold3 官方文档讲解 02：输入设置（MSA / 模板 / 共价键 / CCD） | 视频博客 | [B站 BV11BzjYbEgD](https://www.bilibili.com/video/BV11BzjYbEgD/) | [博客](alphafold/AlphaFold3官方文档讲解02_输入设置_MSA模板共价键与CCD.md) | 11 |
| AlphaFold 的原理和展望 | 视频博客（公开课） | [B站 BV1fm4y1D7Wz](https://www.bilibili.com/video/BV1fm4y1D7Wz/) | [博客](alphafold/AlphaFold的原理和展望.md) | 18 |

**阅读路径建议**：先建立直觉 → [AlphaFold3 图解](alphafold/AlphaFold3图解_The%20Illustrated%20AlphaFold.md)；再看逐层拆解 → [架构解析系列](alphafold/AlphaFold3架构解析01_输入准备.md)；最后对照视频讲解建立主线 → [AlphaFold2 关键算法介绍](alphafold/AlphaFold2关键算法介绍.md)、[AlphaFold3 算法详解 01–03](alphafold/AlphaFold3算法详解01_输入处理.md)。

## `proteinmpnn/` — ProteinMPNN 与逆折叠序列设计

围绕「给定骨架、设计序列」的逆折叠（inverse folding）主线，收录 ProteinMPNN / MPNN 的原理、论文精读与实操。

| 名称 | 来源 | 博客 | 配图 |
| --- | --- | --- | ---: |
| MPNN：用机器学习做蛋白质序列设计（课程讲解） | [YouTube 6z4XmUAwdNA](https://youtu.be/6z4XmUAwdNA) | [博客](proteinmpnn/MPNN：用机器学习做蛋白质序列设计.md) | 8 |
| ProteinMPNN 论文精读：稳健的深度学习蛋白质序列设计 | [B站 BV1zu4y1J7MJ](https://www.bilibili.com/video/BV1zu4y1J7MJ/) | [博客](proteinmpnn/ProteinMPNN论文精读_稳健的深度学习蛋白质序列设计.md) | 18 |
| 用 ProteinMPNN 进行逆折叠（实操讲解） | [YouTube o8JWPjSH1Ig](https://youtu.be/o8JWPjSH1Ig) | [博客](proteinmpnn/用ProteinMPNN进行逆折叠.md) | 11 |

## `rfdiffusion/` — RFdiffusion 骨架生成与 binder 设计

围绕 RFdiffusion / RFdiffusion3 的扩散式骨架生成：从图像生成范式到蛋白质结构设计的科普、Baker 实验室官方教程（RFD3 设计 binder），以及 Joe Watson & David Juergens 的报告。

| 名称 | 来源 | 博客 | 配图 |
| --- | --- | --- | ---: |
| Baker 实验室官方教程：用 RFdiffusion3 设计蛋白质 Binder | RosettaCommons 官方教程（主讲 Rafi Brent） | [博客](rfdiffusion/Baker实验室官方教程：用RFDiffusion3设计蛋白质Binder.md) | 8 |
| RFdiffusion：从图像生成到蛋白质结构设计 | 知识分享（科普向） | [博客](rfdiffusion/RFdiffusion：从图像生成到蛋白质结构设计.md) | 15 |
| RFdiffusion：结合结构预测与扩散生成模型的精准蛋白质设计 | 报告（Joe Watson、David Juergens） | [博客](rfdiffusion/RFDiffusion：结合结构预测与扩散生成模型的精准蛋白质设计.md) | 17 |

## `rosettafold/` — RoseTTAFold All-Atom

| 名称 | 来源 | 博客 | 配图 |
| --- | --- | --- | ---: |
| RoseTTAFold All-Atom：能建模 PDB 中所有分子的统一网络（论文精读） | 密歇根大学 MaomLab「Molecular ML Reading Group」（主讲 Rohith Krishna） | [博客](rosettafold/RoseTTAFold%20All-Atom%20论文精读（Molecular%20ML%20Reading%20Group）.md) | 12 |

## `protein_design/` — 蛋白质设计通识与课程

不绑定单一模型的通识 / 课程类内容：从经典力场（统计势、Rosetta 打分函数、无先验的 RF 方法）到深度学习设计（ANN、GNN、MPNN、ProteinMPNN），以及「DNA / RNA 数据如何输入机器学习模型」。

| 名称 | 来源 | 博客 | 配图 |
| --- | --- | --- | ---: |
| 第 01 讲：AI + 蛋白质设计基础（从经典力场到深度学习） | [B站 BV1mkdwBoE6Z](https://www.bilibili.com/video/BV1mkdwBoE6Z/) | [博客](protein_design/第01讲_AI+蛋白质设计基础.md) | 16 |
| 第 02 讲：实践操作（RosettaScripts 与 ProteinMPNN） | [B站 BV1PudwBnEtq](https://www.bilibili.com/video/BV1PudwBnEtq/) | [博客](protein_design/第02讲_实践操作_RosettaScripts与ProteinMPNN.md) | 11 |
| DNA 与 RNA 数据如何输入机器学习模型 | [B站 BV1VBdDYLE8i](https://www.bilibili.com/video/BV1VBdDYLE8i/) | [博客](protein_design/DNA与RNA数据如何输入机器学习模型.md) | 14 |

## `highfold/` — HighFold 与环肽 / 二硫键结构预测

围绕「环肽与二硫键的结构预测与设计」，收录两篇 ML for Protein Engineering / Institute for Protein Design 的研讨会报告。

| 名称 | 来源 | 博客 | 配图 |
| --- | --- | --- | ---: |
| 环肽结构预测与设计：用 AlphaFold 攻克「环」的难题 | [YouTube SDxy5E8fvXY](https://www.youtube.com/watch?v=SDxy5E8fvXY) | [博客](highfold/环肽结构预测与设计_基于AlphaFold.md) | 15 |
| 富二硫键微型蛋白的从头设计：靶向 B 类 GPCR | [YouTube T4b9YuMhchg](https://www.youtube.com/watch?v=T4b9YuMhchg) | [博客](highfold/富二硫键微型蛋白的从头设计_靶向B类GPCR.md) | 15 |

## 致谢与许可

- *The Illustrated AlphaFold* 由 Elana Simon 与 Jake Silberg 创作，本仓库收录其中文翻译与原文配图，版权归原作者，仅供学习交流。
- [alphafold3-architecture-walkthrough](https://github.com/shenyichong/alphafold3-architecture-walkthrough) 采用 **MIT License**（Copyright © 2025 shenyichong），本仓库收录其中文文档与配图。
- 视频博客均由 `video2blog` skill 基于 B 站 AI 字幕与幻灯片整理生成。
