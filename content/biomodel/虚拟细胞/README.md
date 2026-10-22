# 虚拟细胞小册子

> 目标：用 10 个小节、每节 1–2 页，快速建立「虚拟细胞」的任务、数据、做法与结果框架。
> 每个小节基于 1–3 个视频整理，博客按顺序编号；中间产物放在 `_work/虚拟细胞/`。

## 阅读路径

- **30 分钟速览**：01 → 02 → 05 → 06 → 10
- **1 小时建立框架**：01 → 02 → 03 → 05 → 06 → 10
- **半天深入**：按 01–10 顺序读，07–09 配合论文与代码

## 小节索引

| # | 小节 | 博客 | 主要视频 | 状态 |
| --- | --- | --- | --- | --- |
| 01 | 虚拟细胞是什么 | [01_虚拟细胞是什么.md](01_虚拟细胞是什么.md) | [What is a virtual cell?](https://www.youtube.com/watch?v=2-Ou1BLkpQQ) | 已整理 |
| 02 | 预测任务有哪几种 | [02_预测任务有哪几种.md](02_预测任务有哪几种.md) | [A Systematic Comparison of Single-Cell Perturbation Response Prediction Models](https://www.youtube.com/watch?v=pFRuCfn6pFE) · [Interpretable ML to Model Drug Perturbations](https://www.youtube.com/watch?v=blbmQJtutJg) | 已整理 |
| 03 | 数据从哪里来 | [03_数据从哪里来.md](03_数据从哪里来.md) | [Perturb-seq 技术](https://www.bilibili.com/video/BV1o5iQBhEaw/) · [Tahoe-100M](https://www.bilibili.com/video/BV1khg5z9EpZ/) | 已整理 |
| 04 | 一份数据怎么用 | [04_一份数据怎么用.md](04_一份数据怎么用.md) | [AnnData 数据结构](https://www.bilibili.com/video/BV1WGZSYwEZ2/) · [Perturb-seq analysis](https://www.youtube.com/watch?v=K73VyTp5eXE) | 已整理 |
| 05 | 主流做法有哪几类 | [05_主流做法有哪几类.md](05_主流做法有哪几类.md) | [GEARS](https://www.youtube.com/watch?v=maUpBKEBXmw) · [chemCPA](https://www.youtube.com/watch?v=nsL_NOwYf1c) · [Tahoe-x1](https://www.youtube.com/watch?v=BoGYADxG_ys) | 已整理 |
| 06 | 怎么判断预测得准 | [06_怎么判断预测得准.md](06_怎么判断预测得准.md) | [Linear Baselines](https://www.youtube.com/watch?v=ldYJ703CPBA) · [PerturBench](https://www.youtube.com/watch?v=5M0HWIjmEhQ) | 已整理 |
| 07 | GEARS 怎么做 | [07_GEARS怎么做.md](07_GEARS怎么做.md) | [GEARS 作者讲解](https://www.youtube.com/watch?v=maUpBKEBXmw) · [Linear Baselines](https://www.youtube.com/watch?v=ldYJ703CPBA) | 已整理 |
| 08 | chemCPA 怎么做 | [08_chemCPA怎么做.md](08_chemCPA怎么做.md) | [chemCPA 作者讲解](https://www.youtube.com/watch?v=nsL_NOwYf1c) · [CPA 基础](https://www.youtube.com/watch?v=blbmQJtutJg) | 已整理 |
| 09 | Tahoe-x1 怎么做 | [09_Tahoe-x1怎么做.md](09_Tahoe-x1怎么做.md) | [Tahoe-x1 作者报告](https://www.youtube.com/watch?v=Nky3tlQ7phA) · [Tahoe-x1 速览](https://www.youtube.com/watch?v=BoGYADxG_ys) | 已整理 |
| 10 | 三个模型怎么选 | [10_三个模型怎么选.md](10_三个模型怎么选.md) | [Benchmarking Perturbation Models](https://www.youtube.com/watch?v=EjgmO8VV_EU) · [Virtual Cell Challenge 2026](https://www.youtube.com/watch?v=Jm4oNbfqYoE) | 已整理 |

## 十节内容

1. **虚拟细胞是什么**：输入「细胞状态 + 扰动」，输出「扰动后状态」；与聚类、注释、基础模型的区别。
2. **预测任务有哪几种**：基因 / 药物 / 剂量 / 组合 / 跨细胞系；已见扰动、未见扰动、零样本。
3. **数据从哪里来**：Perturb-seq、化学筛选、观测图谱；Norman、sci-Plex3、Tahoe-100M、DepMap。
4. **一份数据怎么用**：h5ad 结构、对照细胞、基因 ID 对齐、归一化、数据划分与泄漏。
5. **主流做法有哪几类**：均值/线性基线、潜变量（CPA/chemCPA）、图先验（GEARS）、基础模型（Tahoe-x1）。
6. **怎么判断预测得准**：表达、差异基因、扰动判别性、生物意义；为什么只看 MSE 会骗人。
7. **GEARS 怎么做**：GO 图 + 图神经网络 + 解码；Norman 数据上的结果；强在哪、弱在哪。
8. **chemCPA 怎么做**：CPA + 分子编码 + 剂量缩放 + 从 L1000 迁移；sci-Plex3 结果；局限。
9. **Tahoe-x1 怎么做**：266M 细胞预训练、基因 token、细胞嵌入；DepMap 与零样本；局限。
10. **三个模型怎么选**：能力矩阵、适用场景、选型建议；简单基线很强、零样本仍难。

## 说明

- 博客按 `01_…` 到 `10_…` 顺序命名；每篇可综合 1–3 个视频，正文标注时间戳回链。
- 视频质量评估与数量选择参考 `content/生物信息/AGENT_TASK.md`：先筛标题简介，再抓字幕精排，同分 B 站优先，单视频能覆盖则只选 1 个。
- 字幕来自平台 AI 字幕/自动字幕，术语已按上下文校正；配图来自视频关键帧。
- 视频与配图版权归原作者，本目录仅用于学习交流；引用论文时请以原文为准。

## 制作说明

本目录使用 `video2blog` skill 的流程：下载视频 → 1fps 抽帧 → 抓取字幕 → 生成「图-字幕」文稿 → 写博客。中间产物在 `_work/虚拟细胞/`，不进入版本库。
