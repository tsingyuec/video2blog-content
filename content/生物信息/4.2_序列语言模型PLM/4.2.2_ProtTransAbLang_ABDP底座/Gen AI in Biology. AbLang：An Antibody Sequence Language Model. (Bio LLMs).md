# AbLang2：跑在 CPU 上的抗体「语法专家」，亚秒级预测最优突变

> 来源：YouTube 视频《Gen AI in Biology. AbLang: An Antibody Sequence Language Model. (Bio LLMs)》（频道：Byte Goose AI，[T9MfPvjn8aw](https://www.youtube.com/watch?v=T9MfPvjn8aw)，时长 02:18，2025-10-25 发布）。
> 本文基于视频字幕与画面逐窗口整理而成，配图取自视频截图，时间戳可跳回原视频对应位置核对。
> 导读：视频标题写的是 AbLang，旁白介绍的实为该家族的新一代 **AbLang2**——与上一篇（AbLang 一作 ISMB 2022 报告）对照阅读：一代证明了「抗体值得专属语言模型」，这条短视频则展示它实用化之后的模样：小、快、专。

## 本讲要解决的核心问题（SCQA）

**背景**：抗体药物设计越来越依赖序列数据与语言模型（AbLang 一代已证明抗体专属语言模型的价值，见本系列上一篇）。

**冲突**：设计所用的数据常有缺角——关键数据库里**大量序列缺失开头几个氨基酸**；老办法依赖「基因蓝图」（即种系序列）来填补，结果造成向「预期序列」的偏置；而研发节奏又要求快。

**疑问**：有没有一个又专又快的抗体序列模型？

**回答（中心思想）**：AbLang2——在超过 3500 万条序列上训练的抗体专属掩码语言模型，把一件事做到极致：**预测最优突变**。它小而灵，在 CPU（而非耗电的 GPU）上就能亚秒级处理成批序列；但它是专才，不预测 3D 结构、不算结合强弱。

## 一、要解决的问题：缺角数据与蓝图偏置

[【跳转到 00:17】](https://www.youtube.com/watch?v=T9MfPvjn8aw&t=17)

设计抗体这类「活的药物」很难，首要麻烦是数据缺角：一个关键数据库（即上一篇的 OAS）里，很大一部分序列缺失开头几个氨基酸。

![视频讲解数据库序列缺角问题时的画面](assets/Gen%20AI%20in%20Biology.%20AbLang：An%20Antibody%20Sequence%20Language%20Model.%20%28Bio%20LLMs%29/00017.webp)

[【跳转到 00:33】](https://www.youtube.com/watch?v=T9MfPvjn8aw&t=33)

老办法依赖「基因蓝图」（种系序列），这带来了偏向「预期序列」的偏置。要绕开偏置与数据缺口，就需要一个专门工具——AbLang2。

![视频讲解老方法带来序列偏置时的画面](assets/Gen%20AI%20in%20Biology.%20AbLang：An%20Antibody%20Sequence%20Language%20Model.%20%28Bio%20LLMs%29/00033.webp)

## 二、学习方式：3500 万条序列上的「完形填空」

[【跳转到 00:45】](https://www.youtube.com/watch?v=T9MfPvjn8aw&t=45)

AbLang2 是一个专为抗体的语言模型，从真实世界数据中学习、用来预测突变。它训练了超过 3500 万条序列，基本学会了「抗体语法」。

![视频讲解 3500 万序列训练时的画面](assets/Gen%20AI%20in%20Biology.%20AbLang：An%20Antibody%20Sequence%20Language%20Model.%20%28Bio%20LLMs%29/00050.webp)

[【跳转到 01:04】](https://www.youtube.com/watch?v=T9MfPvjn8aw&t=64)

核心玩法是生物版**完形填空**——掩码语言建模（原理见本系列 4.2.1）：给模型一条带未知位置的序列（用星号标出），它预测该位置最可能的氨基酸，把这句话补完整。

![视频展示掩码语言模型完形填空时的画面](assets/Gen%20AI%20in%20Biology.%20AbLang：An%20Antibody%20Sequence%20Language%20Model.%20%28Bio%20LLMs%29/00064.webp)

## 三、能干什么、不能干什么

[【跳转到 01:24】](https://www.youtube.com/watch?v=T9MfPvjn8aw&t=84)

对研究者，它能：优化抗体、**虚拟筛选**抗体文库、提前发现潜在问题。

[【跳转到 01:34】](https://www.youtube.com/watch?v=T9MfPvjn8aw&t=94)

真正的卖点在速度：**成批序列亚秒级处理**——因为它是更小、更灵巧的模型，为 CPU 而不是耗电的 GPU 而生。

![视频展示亚秒级推理速度时的画面](assets/Gen%20AI%20in%20Biology.%20AbLang：An%20Antibody%20Sequence%20Language%20Model.%20%28Bio%20LLMs%29/00094.webp)

[【跳转到 01:49】](https://www.youtube.com/watch?v=T9MfPvjn8aw&t=109)

但它是一个「专才」，能力边界必须清楚：**不预测 3D 结构，也不评估结合强弱**——这些要交给别的工具（结构预测见本系列 5.1，结合评估见 5.3）。

![视频讲解模型能力边界时的画面](assets/Gen%20AI%20in%20Biology.%20AbLang：An%20Antibody%20Sequence%20Language%20Model.%20%28Bio%20LLMs%29/00109.webp)

## 四、一句话总结

[【跳转到 01:59】](https://www.youtube.com/watch?v=T9MfPvjn8aw&t=119)

AbLang2 让抗体设计更快、更聪明，靠的是把一件事做到极致：**预测最优突变**。视频最后留了一个开放问题：AI 会成为未来药物的主设计师吗？

![视频结尾总结时的画面](assets/Gen%20AI%20in%20Biology.%20AbLang：An%20Antibody%20Sequence%20Language%20Model.%20%28Bio%20LLMs%29/00119.webp)

## 小结

- 数据缺角 + 蓝图偏置 → 需要抗体专属、不依赖种系蓝图的模型。
- AbLang2：3500 万+ 序列、掩码完形填空、学会「抗体语法」。
- 用途：突变预测、虚拟筛选、问题预警；模型小，CPU 上亚秒级处理成批序列。
- 边界：不预测 3D 结构、不评估结合——用 AbLang2 补序列、筛突变，再用结构/结合工具验证。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| AbLang2 | 抗体专属掩码语言模型（AbLang 家族新一代，视频旁白称 AbLang2） |
| 掩码语言建模 | 挖空一个位置、预测最可能氨基酸的自监督「完形填空」 |
| 虚拟筛选 | 先用计算在抗体库里筛一轮，代替盲目实验 |
| 基因蓝图（种系）偏置 | 用种系序列填补缺口，使结果偏向「预期序列」 |
