# 系列：AlphaFold 图解与算法解析

- **平台**：Bilibili、个人博客、GitHub
- **说明**：本系列专门收录 **AlphaFold（AlphaFold2 / AlphaFold3）架构与算法**的中文整理资料。既有英文优质长文的中文翻译，也有中文社区原创的逐层拆解，以及来自视频讲解的图文博客，适合从「整体直觉」到「逐张量实现」逐级深入。
- **内容来源**：
  - 英文博客 *The Illustrated AlphaFold*（Elana Simon、Jake Silberg，Stanford，2024）——**中文翻译**
  - GitHub 仓库 [shenyichong/alphafold3-architecture-walkthrough](https://github.com/shenyichong/alphafold3-architecture-walkthrough)（MIT）——**中文版**（作者 Yichong Shen）
  - B 站视频「alphafold2关键算法介绍」（`BV1ucYmesENM`）、「AlphaFold3算法详解」三集（`BV1CNeKeYE7u`、`BV1kNeKeYEEn`、`BV1ANeKeeESs`）

> 本系列的 4 篇视频博客（`AlphaFold2关键算法介绍`、`AlphaFold3算法详解 01–03`）原先收录于 [protein_design](../protein_design/README.md)，现统一迁移至此，便于集中查阅。

## 内容索引

| 名称 | 类型 | 来源 | 博客 | 配图 |
| --- | --- | --- | --- | ---: |
| AlphaFold3 图解（The Illustrated AlphaFold） | 图文长文（中文翻译） | [elanapearl.github.io](https://elanapearl.github.io/blog/2024/the-illustrated-alphafold/) | [博客](blog/AlphaFold3图解_The%20Illustrated%20AlphaFold.md) | 52 |
| AlphaFold3 架构解析 01：输入准备 | 中文逐层拆解（shenyichong，已通顺化） | [GitHub](https://github.com/shenyichong/alphafold3-architecture-walkthrough) | [博客](blog/AlphaFold3架构解析01_输入准备.md) | 31 |
| AlphaFold3 架构解析 02：表征学习 | 中文逐层拆解（shenyichong，已通顺化） | [GitHub](https://github.com/shenyichong/alphafold3-architecture-walkthrough) | [博客](blog/AlphaFold3架构解析02_表征学习.md) | 19 |
| AlphaFold3 架构解析 03：结构预测 | 中文逐层拆解（shenyichong，已通顺化） | [GitHub](https://github.com/shenyichong/alphafold3-architecture-walkthrough) | [博客](blog/AlphaFold3架构解析03_结构预测.md) | 22 |
| AlphaFold3 架构解析 04：损失函数 | 中文逐层拆解（shenyichong，已通顺化） | [GitHub](https://github.com/shenyichong/alphafold3-architecture-walkthrough) | [博客](blog/AlphaFold3架构解析04_损失函数.md) | 16 |
| AlphaFold2 关键算法介绍 | 视频博客 | [B站 BV1ucYmesENM](https://www.bilibili.com/video/BV1ucYmesENM/) | [博客](blog/AlphaFold2关键算法介绍.md) | 13 |
| AlphaFold3 算法详解 01：输入处理 | 视频博客 | [B站 BV1CNeKeYE7u](https://www.bilibili.com/video/BV1CNeKeYE7u/) | [博客](blog/AlphaFold3算法详解01_输入处理.md) | 11 |
| AlphaFold3 算法详解 02：Pairformer | 视频博客 | [B站 BV1kNeKeYEEn](https://www.bilibili.com/video/BV1kNeKeYEEn/) | [博客](blog/AlphaFold3算法详解02_Pairformer.md) | 12 |
| AlphaFold3 算法详解 03：扩散部分 | 视频博客 | [B站 BV1ANeKeeESs](https://www.bilibili.com/video/BV1ANeKeeESs/) | [博客](blog/AlphaFold3算法详解03_扩散部分.md) | 8 |

## 阅读路径建议

1. **先建立直觉**：读 [AlphaFold3 图解（The Illustrated AlphaFold）](blog/AlphaFold3图解_The%20Illustrated%20AlphaFold.md)，它从「输入准备 → 表征学习 → 结构预测」三段式，用大量图示讲清每个张量的形状变化与操作动机。
2. **再看逐层拆解**：读 shenyichong 的 [架构解析系列](blog/AlphaFold3架构解析01_输入准备.md)（输入准备 / 表征学习 / 结构预测 / 损失函数），它更贴近论文公式与实现细节。
3. **对照视频讲解建立主线**：读 [AlphaFold2 关键算法介绍](blog/AlphaFold2关键算法介绍.md) 了解五十年结构预测史与 Evoformer，再读 [AlphaFold3 算法详解 01–03](blog/AlphaFold3算法详解01_输入处理.md) 梳理输入处理、Pairformer 与扩散模块。

## 博客结构速览

**AlphaFold3 图解（The Illustrated AlphaFold，中译）**

- 引言：谁适合阅读、架构总览、变量与图示约定
- 一、输入准备：分词（Tokenization）、检索（MSA 与模板）、构建原子级表示、Atom Transformer、原子级→token 级聚合
- 二、表征学习：Template Module、MSA Module（外积均值、行式门控自注意力）、Pairformer（三角更新 / 三角注意力、单体注意力带配对偏置）
- 三、结构预测：扩散基础、Diffusion Module 四步
- 四、损失函数与其他训练细节：distogram / diffusion / confidence 损失、Recycling、交叉蒸馏、裁剪与训练阶段、碰撞、batch size
- 从 ML 趋势视角的思考（RAG、配对偏置注意力、自监督、分类 vs 回归、与 RNN/LSTM 的相似性等）

**AlphaFold3 架构解析（shenyichong，中文原创）**

- 01 输入准备：MSA 与 Templates 从何而来、如何表征、如何构建 atom-level 与 token-level 表征
- 02 表征学习：Template Module、MSA Module、Pairformer Module
- 03 结构预测：Diffusion 基本概念、Sample Diffusion 与 Diffusion Module（推理过程）
- 04 损失函数：`L_distogram`、`L_diffusion`、`L_confidence`

**AlphaFold2 关键算法介绍（视频）**

- 前 AlphaFold 时代：结构预测的探索（Pauling 折纸、肌红蛋白与 PDB、contact map、SwissModel、共进化、2017 卷积网络）
- AlphaFold1 与 AlphaFold2：从 contact map 到端到端
- AlphaFold2 的核心：Evoformer（两个三维张量、按行/列切片、row-wise gated self-attention with pair bias、门控、外积注入）

**AlphaFold3 算法详解（视频，三集）**

- 01 输入处理：三段式总览、把分子切成 token、六个输入张量、Atom Transformer / SwiGLU
- 02 Pairformer：Template module、MSA module、pair 表示的三角更新与三角注意力
- 03 扩散部分：扩散模块总览、token/原子级条件张量、坐标无量纲化、为什么不用等变网络

## 致谢与许可

- *The Illustrated AlphaFold* 由 Elana Simon 与 Jake Silberg 创作，本仓库收录其中文翻译与原文配图，版权归原作者，仅供学习交流。
- [alphafold3-architecture-walkthrough](https://github.com/shenyichong/alphafold3-architecture-walkthrough) 采用 **MIT License**（Copyright © 2025 shenyichong），本仓库收录其中文文档与配图。
- 视频博客均由 `video2blog` skill 基于 B 站 AI 字幕与幻灯片整理生成。
