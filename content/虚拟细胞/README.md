# 虚拟细胞（精选版）

> 按视频质量与相关性筛选，**每个视频一篇博客**；博客标题与视频标题一致，不合并多个视频。
> 更完整的 10 节旧版见 [content/biomodel/虚拟细胞](../biomodel/虚拟细胞/README.md)。

## 选题原则

- 先按标题/简介筛选，再抓字幕精排；同分时 B 站优先。
- 只保留作者本人报告、实验室组会、会议 seminar、课程等高质量来源；泛泛的新闻、2 分钟快讯、多人 panel 混剪不纳入。
- 每个视频单独成篇；找不到同时满足相关性和质量的视频就不写。
- 最终保留 11 篇，对应 11 个视频。

## 阅读路径

- **30 分钟速览**：What is a virtual cell? → Tahoe-100M → Deep-learning-based... → 502-Benchmarking...
- **1 小时建立框架**：再加 Yusuf Roohani、MPG Primer、PerturBench、1661-Virtual Cell Challenge
- **按模型深入**：Graph Neural Networks User Group Meetup（GEARS）→ Predicting...Unseen Drugs（chemCPA）→ BioML Seminar（Tahoe-x1）

## 实验基础（湿实验侧）

> 上面几节讲的是**扰动数据与模型**（Perturb-seq 分析、Tahoe-100M、GEARS/chemCPA、基准与挑战）；下面四个子目录补的是**这些数据在湿实验里怎么产生**：文库怎么建、载体怎么装、sgRNA 怎么设计、基因怎么敲掉。
> 选题来自 `explore`：文库构建 / 表达载体 / sgRNA / 基因敲除，每类取精排前两条，一视频一篇博客。

| 子系列 | 主题 | 视频数 | 入口 |
| --- | --- | ---: | --- |
| 文库构建 | CRISPR 文库筛选（筛选侧）＋ NGS 建库（测序侧） | 2 | [文库构建](文库构建/README.md) |
| 表达载体 | sgRNA 表达框与克隆构建 ＋ 慢病毒递送载体 | 2 | [表达载体](表达载体/README.md) |
| sgRNA | 靶点选择、序列/引物设计、验证 | 2 | [sgRNA](sgRNA/README.md) |
| 基因敲除 | 敲除原理与策略、单克隆株获取与验证 | 2 | [基因敲除](基因敲除/README.md) |

## 总览

| 博客（标题=视频标题） | 视频 | 配图 |
| --- | --- | ---: |
| [What is a virtual cell? Biohub's $1.8 billion data push, and the AI models it is for](<What is a virtual cell？Biohub's $1.8 billion data push, and the AI models it is for.md>) | [YouTube `2-Ou1BLkpQQ`](https://www.youtube.com/watch?v=2-Ou1BLkpQQ) | 8 |
| [Yusuf Roohani at ARDD2025: Building a Virtual Cell: an AI platform for engineering cell state](<Yusuf Roohani at ARDD2025：Building a Virtual Cell：an AI platform for engineering cell state.md>) | [YouTube `k2VCADF3TwI`](https://www.youtube.com/watch?v=k2VCADF3TwI) | 8 |

## 数据

| 博客（标题=视频标题） | 视频 | 配图 |
| --- | --- | ---: |
| [MPG Primer: Introduction to Perturb-seq analysis (2021)](<MPG Primer：Introduction to Perturb-seq analysis (2021).md>) | [YouTube `K73VyTp5eXE`](https://www.youtube.com/watch?v=K73VyTp5eXE) | 8 |
| [Tahoe-100M：千兆级单细胞扰动图谱 \|\| Dr. Johnny Yu](<Tahoe-100M：千兆级单细胞扰动图谱 ｜｜ Dr. Johnny Yu.md>) | [Bilibili `BV1khg5z9EpZ`](https://www.bilibili.com/video/BV1khg5z9EpZ/) | 8 |

## 评价

| 博客（标题=视频标题） | 视频 | 配图 |
| --- | --- | ---: |
| [Deep-learning-based Gene Perturbation Effect Prediction Does Not Yet Outperform Linear Baselines](Deep-learning-based Gene Perturbation Effect Prediction Does Not Yet Outperform Linear Baselines.md) | [YouTube `ldYJ703CPBA`](https://www.youtube.com/watch?v=ldYJ703CPBA) | 7 |
| [PerturBench: Benchmarking Machine Learning Models for Cellular Perturbation Analysis](<PerturBench：Benchmarking Machine Learning Models for Cellular Perturbation Analysis.md>) | [YouTube `5M0HWIjmEhQ`](https://www.youtube.com/watch?v=5M0HWIjmEhQ) | 8 |

## 模型

| 博客（标题=视频标题） | 视频 | 配图 |
| --- | --- | ---: |
| [Graph Neural Networks User Group Meetup 9/29/2022](<Graph Neural Networks User Group Meetup 9／29／2022.md>) | [YouTube `maUpBKEBXmw`](https://www.youtube.com/watch?v=maUpBKEBXmw) | 8 |
| [Predicting Single-Cell Perturbation Responses For Unseen Drugs \| Leon Hetzel and Simon Böhm](<Predicting Single-Cell Perturbation Responses For Unseen Drugs ｜ Leon Hetzel and Simon Böhm.md>) | [YouTube `nsL_NOwYf1c`](https://www.youtube.com/watch?v=nsL_NOwYf1c) | 8 |
| [BioML Seminar 4.4 - Shreshth Gandhi on Scaling Perturbation-Trained Single-Cell Foundation Models](BioML Seminar 4.4 - Shreshth Gandhi on Scaling Perturbation-Trained Single-Cell Foundation Models.md) | [YouTube `Nky3tlQ7phA`](https://www.youtube.com/watch?v=Nky3tlQ7phA) | 8 |

## 选型与挑战

| 博客（标题=视频标题） | 视频 | 配图 |
| --- | --- | ---: |
| [502-Benchmarking Single-Cell Perturbation Response Models](502-Benchmarking Single-Cell Perturbation Response Models.md) | [YouTube `EjgmO8VV_EU`](https://www.youtube.com/watch?v=EjgmO8VV_EU) | 3 |
| [1661-Virtual Cell Challenge 2026](1661-Virtual Cell Challenge 2026.md) | [YouTube `Jm4oNbfqYoE`](https://www.youtube.com/watch?v=Jm4oNbfqYoE) | 4 |

## 说明

- 每篇博客只基于对应视频的文稿，正文时间戳可回跳原片；配图来自视频关键帧或据视频内容重绘。
- 视频与配图版权归原作者，仅用于学习交流；论文数字以原文为准。
- 中间产物在 `_work/虚拟细胞/` 与 `_work/虚拟细胞_v2/`，不进入版本库。
