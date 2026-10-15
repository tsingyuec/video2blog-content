# 湿实验之前先算一次人源性：OASis 评分如何在先导筛选里排雷免疫原性

> 来源视频：[How to Predict Antibody Immunogenicity Before Testing: Humanness Score](https://www.youtube.com/watch?v=QirzmIzzBG8) · 时长 4:10 · MiLaboratories
> 本篇基于视频英文 AI 字幕与画面整理（中译），时间戳可跳转回原视频对应位置。

## 本讲要解决的核心问题（SCQA）

**背景**：先导抗体筛选通常按 panning（淘选）轮次的富集倍数挑 clone——越到后面轮次越富集的序列越受青睐。

**冲突**：一个在第二轮就高度富集的 clone，人源性分数可能非常低 [【跳转到 02:22】](https://www.youtube.com/watch?v=QirzmIzzBG8&t=142)。患者免疫系统一旦把药物当外来物，就会产生 **anti-drug antibodies（ADA，抗药物抗体）**：药被更快清除、停止起效，最坏情况患者发生严重反应 [【跳转到 00:00】](https://www.youtube.com/watch?v=QirzmIzzBG8&t=0)。等进了实验才发现，前面的筛选就白做了。

**疑问**：能不能在把抗体拿去做实验**之前**，就预测这种行为？

**回答（中心思想）**：可以——用基于 OASis 算法的人源性评分（humanness score，0–100）当第二层过滤器：分数越低，越难在人抗体库中找到类似序列；分数越高，越像一条天然的初始人抗体。先按 70 分预过滤，再在簇内按分数排序，最后拿到高亲和力、高人源性兼顾的先导面板 [【跳转到 02:44】](https://www.youtube.com/watch?v=QirzmIzzBG8&t=164)。

![抗药物抗体问题：免疫系统把治疗抗体当外来物，药物被快速清除](assets/How%20to%20Predict%20Antibody%20Immunogenicity%20Before%20Testing：%20Humanness%20Score/00000.webp)

---

## 一、免疫原性为什么要在最前面排雷

视频开篇把问题说得很直白：当患者的免疫系统认定你的抗体是"外来物"时，它会产生抗药物抗体（ADA）[【跳转到 00:00】](https://www.youtube.com/watch?v=QirzmIzzBG8&t=0)。后果有三层：

- 药物被更快清除出体内；
- 药物停止起效；
- 最坏情况下，患者出现严重的不良反应。

所以关键问题是：**在上实验之前，能不能预测这种行为**？这正是人源性评分要回答的事。

## 二、OASis 评分：0 到 100 的直觉含义

平台引入的 humanness score 基于**广泛使用的 OASis 算法** [【跳转到 00:25】](https://www.youtube.com/watch?v=QirzmIzzBG8&t=25)。思路很简单：检查你的抗体序列与"广为人知的抗体库"（人源抗体序列池）有多接近，并给每条抗体打一个分数 [【跳转到 00:34】](https://www.youtube.com/watch?v=QirzmIzzBG8&t=34)。

- **0 分**：在人源抗体库中几乎找不到这样的序列——免疫系统大概率会把它当外来物；
- **100 分**：看起来就像一条天然的初始人抗体（naive human antibody，未经抗原驱动成熟的自然人抗体）。

![OASis 评分：0 分意味着人库里几乎找不到，100 分意味着像天然人抗体](assets/How%20to%20Predict%20Antibody%20Immunogenicity%20Before%20Testing：%20Humanness%20Score/00034.webp)

在实际项目里，一轮淘选 campaign 的候选抗体分数分布很散：有的只有 20 分，有的能到 90 分 [【跳转到 01:08】](https://www.youtube.com/watch?v=QirzmIzzBG8&t=68)。这个信息让我们可以**按"离天然人源抗体库有多近"来过滤先导（leads）**。

## 三、富集 × 人源性：把第二层过滤器叠上去

视频用一个标准的纳米抗体 panning 实验演示叠加逻辑 [【跳转到 01:38】](https://www.youtube.com/watch?v=QirzmIzzBG8&t=98)：

1. **第一层：富集分析**。两轮选择后，一批 leads 已经富集出来 [【跳转到 01:33】](https://www.youtube.com/watch?v=QirzmIzzBG8&t=93)；
2. **第二层：人源性过滤**。在富集结果之上，再按 humanness score 过滤数据 [【跳转到 01:38】](https://www.youtube.com/watch?v=QirzmIzzBG8&t=98)。

在序列空间里可以直接看到人源性分数沿整个候选库的分布 [【跳转到 01:57】](https://www.youtube.com/watch?v=QirzmIzzBG8&t=117)；还可以把富集质量叠加上去，只高亮稳定结合者等目标 clone。

![序列空间中的人源性分布：把富集质量与人源性叠在一起看](assets/How%20to%20Predict%20Antibody%20Immunogenicity%20Before%20Testing：%20Humanness%20Score/00117.webp)

效果立刻显现：**有些 clone 在第二轮高度富集，但人源性分数非常低**——它们会被放弃；真正要聚焦的是既富集、又接近天然人抗体的那部分序列 [【跳转到 02:22】](https://www.youtube.com/watch?v=QirzmIzzBG8&t=142)。

## 四、落地两招：先按 70 分过滤，再在簇内排序

到了先导选择（lead selection）阶段，视频演示了人源性分数的两种用法 [【跳转到 02:44】](https://www.youtube.com/watch?v=QirzmIzzBG8&t=164)：

1. **预过滤**：所有 leads 先按 humanness score > 70 过滤——这一步就留下了一大批非常"像人"的抗体；
2. **簇内排序**：在用于构建多样性面板的每个簇（cluster）内，再按人源性分数排序——即使都已过 70 分，也优先推进分数更高者 [【跳转到 03:09】](https://www.youtube.com/watch?v=QirzmIzzBG8&t=189)。

![先导选择：按人源性 >70 预过滤，再在簇内按分数排序](assets/How%20to%20Predict%20Antibody%20Immunogenicity%20Before%20Testing：%20Humanness%20Score/00164.webp)

最终得到的先导面板是 **20–26 个高亲和力、高人源性**的抗体，而且已同步按可开发性（developability）过滤 [【跳转到 03:34】](https://www.youtube.com/watch?v=QirzmIzzBG8&t=214)。视频的结论是：这些 leads 潜在的表现，会明显好于只按富集分析选出来的候选 [【跳转到 03:59】](https://www.youtube.com/watch?v=QirzmIzzBG8&t=239)。

![最终先导面板：高亲和力 + 高人源性 + 可开发性过滤](assets/How%20to%20Predict%20Antibody%20Immunogenicity%20Before%20Testing：%20Humanness%20Score/00214.webp)

## 小结

- 免疫原性风险要在**进实验之前**排雷：ADA 会让药物被快速清除、失效，甚至引发严重反应。
- **OASis 人源性评分**给出 0–100 的直觉标尺：分数越高，序列越像天然人抗体库里的抗体。
- 富集分析只回答"结合好不好"，人源性分数回答"人体接不接受"——**两层过滤器要叠加使用**。
- 落地两招：先按 70 分预过滤，再在簇内按分数排序；最终面板兼顾亲和力、人源性与可开发性。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| ADA（anti-drug antibodies） | 患者针对治疗性抗体产生的抗药物抗体，导致药效下降与安全风险 |
| humanness score | 基于 OASis 的人源性评分，0–100，越高越接近天然人抗体 |
| OASis | 用抗体序列在人源抗体库中检索匹配程度的经典算法 |
| naive human antibody | 未经抗原驱动成熟的天然人抗体，评分 100 的参照 |
| panning | 噬菌体展示等筛选技术中，用抗原反复淘选富集结合克隆的轮次过程 |
| cluster（簇） | 按序列相似性聚类的抗体分组，用于构建多样性面板 |
| developability（可开发性） | 抗体能否顺利做成药物的工程性质（表达、稳定、聚集等） |
| lead / leads | 从筛选中胜出、值得继续开发的先导抗体 |

> 延伸阅读：OASis 九肽机制的原理与 KT3 案例的具体数字，见 [AbNatiV抗体人源化科普教程](AbNatiV抗体人源化科普教程.md)；OASis 所在的 BioPhi 平台全景，见 [BioPhi Antibody design platform： Intro](BioPhi%20Antibody%20design%20platform：%20Intro.md)。
