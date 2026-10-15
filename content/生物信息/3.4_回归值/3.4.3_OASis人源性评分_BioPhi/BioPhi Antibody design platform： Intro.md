# BioPhi 官方速览：Sapiens 人源化与 OASis 人源性报告，装进同一个开源平台

> 来源视频：[BioPhi Antibody design platform: Intro](https://www.youtube.com/watch?v=JNfU4cR1hgI) · 时长 1:13 · BioPhi Platform（官方频道）
> 本篇基于视频英文 AI 字幕与画面整理（中译），时间戳可跳转回原视频对应位置。

## 本讲要解决的核心问题（SCQA）

**背景**：抗体设计中的"人源化"与"人源性评估"各有多种方法——传统的 CDR 移植（CDR grafting）、位置残基频率、种系序列同一性，以及新出现的深度学习方法。

**冲突**：这些方法分散在不同工具里，流程难以自动化，初学者难以入手。

**疑问**：有没有一个开源平台，把这些方法装在一起、串成工作流？

**回答（中心思想）**：BioPhi——面向抗体设计的开源平台 [【跳转到 00:00】](https://www.youtube.com/watch?v=JNfU4cR1hgI&t=0)：用 Sapiens 深度学习加传统 CDR grafting 做自动化人源化；人源性报告集成 OASis 九肽搜索与传统指标；Designer 支持按建议突变手动微调；在线免费、GitHub 开源、可持续扩展。

![BioPhi：面向抗体设计的开源平台](assets/BioPhi%20Antibody%20design%20platform：%20Intro/00000.webp)

---

## 一、BioPhi 是什么：开源的抗体设计平台

视频开篇一句话定位：**BioPhi 是一个开源的抗体设计平台** [【跳转到 00:00】](https://www.youtube.com/watch?v=JNfU4cR1hgI&t=0)。它把两件核心的事装进了同一个平台：自动化的人源化工作流，以及人源性（humanness）评估报告。

## 二、自动化人源化工作流：Sapiens 深度学习 + 传统 CDR grafting

BioPhi 的自动化人源化工作流包含两条路线 [【跳转到 00:06】](https://www.youtube.com/watch?v=JNfU4cR1hgI&t=6)：

- **Sapiens**：一种深度学习方法，在大规模天然抗体库（natural antibody repertoires）上训练，学习"人源抗体序列长什么样"；
- **传统方法**：基于 CDR grafting（把非人源抗体的 CDR 移植到人源框架上）的经典人源化策略。

![Sapiens 深度学习 + CDR grafting：两条人源化路线](assets/BioPhi%20Antibody%20design%20platform：%20Intro/00011.webp)

## 三、人源性报告：OASis 九肽搜索 + 两种传统指标

BioPhi 的抗体人源性报告（antibody humanness report）同样"新旧结合" [【跳转到 00:11】](https://www.youtube.com/watch?v=JNfU4cR1hgI&t=11)：

- **OASis**：一种新方法，把序列按九肽（nine-mer，连续 9 个氨基酸的滑窗片段）在人源抗体库中检索，统计匹配程度 [【跳转到 00:20】](https://www.youtube.com/watch?v=JNfU4cR1hgI&t=20)；
- **传统指标**：位置残基频率（positional residue frequency，逐位置统计人源抗体常用哪些残基）与种系序列同一性（germline sequence identity，与最近人源种系基因的相似度）[【跳转到 00:25】](https://www.youtube.com/watch?v=JNfU4cR1hgI&t=25)。

![人源性报告：OASis 九肽搜索加上传统指标](assets/BioPhi%20Antibody%20design%20platform：%20Intro/00020.webp)

## 四、Designer：按三类建议手动微调序列

在 BioPhi Designer 里，抗体序列可以手动调整：系统给出三类**建议突变**，设计者按需采纳 [【跳转到 00:36】](https://www.youtube.com/watch?v=JNfU4cR1hgI&t=36)：

1. Sapiens 置信度分数（confidence score）推荐的突变；
2. 位置残基频率支持的突变；
3. 最接近的种系（germline）序列对应的突变。

![Designer：按 Sapiens 置信度、残基频率与最近种系给出手动调整建议](assets/BioPhi%20Antibody%20design%20platform：%20Intro/00036.webp)

## 五、免费、开源、可扩展

视频最后交代了平台的开放性 [【跳转到 00:49】](https://www.youtube.com/watch?v=JNfU4cR1hgI&t=49)：

- BioPhi 在其官方网站上**免费**提供使用；
- 它是一个整合数据驱动方法的**可扩展平台**，随着新数据集与新方法的出现而成长；
- 欢迎访问其 GitHub 仓库反馈问题、建议新功能或直接贡献代码 [【跳转到 00:55】](https://www.youtube.com/watch?v=JNfU4cR1hgI&t=55)。

## 小结

- BioPhi = 开源抗体设计平台，核心是**人源化工作流**与**人源性报告**两块。
- 人源化两条路：深度学习 **Sapiens** + 传统 **CDR grafting**。
- 人源性评估三把尺：**OASis**（九肽搜索）+ 位置残基频率 + 种系序列同一性。
- **Designer** 把三类建议突变交给设计者手动采纳，人机协同。
- 免费在线、GitHub 开源、可扩展——方法会随数据集成长。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| BioPhi | 开源抗体设计平台，集人源化、人源性评估与序列设计于一体 |
| Sapiens | BioPhi 中基于大规模天然抗体库训练的深度学习人源化方法 |
| CDR grafting | 把非人源抗体的 CDR 移植到人源框架上的经典人源化方法 |
| OASis | 基于九肽片段在人源抗体库中检索的人源性评估方法 |
| 九肽（nine-mer） | 连续 9 个氨基酸的滑窗片段，OASis 的检索单元 |
| 位置残基频率 | 逐位置统计人源抗体在该位置常用残基的传统指标 |
| 种系序列同一性 | 与最近人源种系基因序列的相似度，传统指标之一 |
| humanness report | BioPhi 输出的抗体人源性评估报告 |
| germline（种系） | 未经历体细胞超突变的祖先抗体基因，人源化的参照系 |

> 延伸阅读：OASis 九肽机制的原理、以及 KT3 案例上 OASis identity/percentile 的具体数字，见 [AbNatiV抗体人源化科普教程](AbNatiV抗体人源化科普教程.md)；OASis 评分在先导筛选中的实际用法，见 [How to Predict Antibody Immunogenicity Before Testing： Humanness Score](How%20to%20Predict%20Antibody%20Immunogenicity%20Before%20Testing：%20Humanness%20Score.md)。
