# 抗体编号方案：不做比对也能对齐所有抗体（Kabat / Chothia / IMGT）

> 视频来源：[Antibody Numbering Schemes](https://www.youtube.com/watch?v=8QLqX1_NJ9A&t=0)（YouTube · NaturalAntibody）
> 本文基于视频演说图文稿整理，配图截自视频。

## 本讲要解决的核心问题（SCQA）

**背景**：分析一类蛋白质时，想知道"哪些位置保守、哪些位置可变"，标准做法是收集大量同源序列做多序列比对（MSA），再逐列观察。

**冲突**：抗体序列数量庞大且彼此高度相似，每来一条新序列就重新收集数据库、重新做一遍 MSA，既慢又不现实；而且不同抗体的 CDR 长短不一，两条序列直接摆在一起根本对不齐。

**疑问**：有没有一种办法，拿到一条新的抗体序列，立刻就能知道"这个位置属于框架区（FR）还是 CDR"，并且让任意两条抗体序列天然可比？

**回答（中心思想）**：抗体编号方案（numbering scheme）就是这套"预先算好的公共坐标系"。Kabat、Chothia、IMGT 等方案把抗体每个位置都编好了号，新序列只需"对号入座"。使用时的关键只有一条：**全程锁定同一种方案**，序列之间才有可比性。

![视频标题页：Antibody Numbering Schemes](assets/Antibody%20Numbering%20Schemes/00005.webp)

## 一、编号方案是什么：一套预计算的多序列比对

### 1.1 常规做法：先做 MSA 再看保守性

比如拿到 100 条同源蛋白的序列，把它们逐列对齐（这就是**多序列比对 MSA**），某一列几乎全是同一个氨基酸 → 这个位置保守；某一列五花八门 → 这个位置可变。问题是：这套流程对每批新序列都要重来一遍。

### 1.2 抗体的特殊之处：比对可以"预计算"

抗体彼此非常相似，所以这个比对可以**提前算好、固化下来**——这就是编号方案的本质，相当于"用一套编号体系给 MSA 的每一列起好名字"。之后 [【跳转到 00:55】](https://www.youtube.com/watch?v=8QLqX1_NJ9A&t=55)：

- 每拿来一条**新的**抗体序列，不用再做 MSA，直接查表：这个位置对应预计算比对中的哪一列；
- 立刻知道它是**框架区（framework）的一部分还是 CDR**；
- 任意两条抗体序列自动落在同一套功能区的语境下，可比性问题迎刃而解。

一句话：编号方案用"预计算 MSA"换掉了"每次现做 MSA"。

## 二、三大方案怎么来：Kabat → Chothia → IMGT

### 2.1 Kabat：一切的起点 [【跳转到 01:30】](https://www.youtube.com/watch?v=8QLqX1_NJ9A&t=90)

Kabat 和 Wu 很多年前首次收集了一批抗体序列并做了 MSA。从这个比对中，抗体的经典结构图景浮现出来：**保守的框架区（framework）**与**可变的 CDR**。这就是第一个抗体编号方案——后续所有方案都沿用了"框架区 + CDR"这幅地图。

![Kabat 方案：从抗体序列的 MSA 中浮现出框架区与 CDR 的结构图景](assets/Antibody%20Numbering%20Schemes/00115.webp)

### 2.2 Chothia 与 IMGT：补上"结构"与"插入缺失"两块短板 [【跳转到 01:55】](https://www.youtube.com/watch?v=8QLqX1_NJ9A&t=115)

随着更多抗体序列和结构出现，新方案相继问世：

- **Chothia**：更侧重**结构**视角的方案；
- **IMGT**：能更好地处理 CDR 内的**插入与缺失（indel）**。CDR 长短不一，IMGT 的编号方式让不同长度的 CDR 也能彼此对齐比较。

当然，方案远不止这三个——比如下文实例里还会出现 Martin、AHo。

![三大方案与后续方案同框：Kabat、Chothia、IMGT](assets/Antibody%20Numbering%20Schemes/00140.webp)

## 三、同一个曲妥珠单抗，四种方案画出不同的 CDR 边界

### 3.1 实例：CDR 定义差别相当大 [【跳转到 02:29】](https://www.youtube.com/watch?v=8QLqX1_NJ9A&t=149)

视频用**曲妥珠单抗（trastuzumab，赫赛汀）**的序列演示：同一条序列，用几种不同方案分别编号。肉眼可见的结果是——**各方案给出的 CDR 定义差别相当大**：同一片段，在 IMGT 里从第 27 位开始算 CDR，在 Kabat 里可能从第 31 位才算，Chothia、Martin 又各不相同。

![曲妥珠单抗序列按 IMGT / Kabat / Chothia / Martin 分别编号，CDR 起点各不相同](assets/Antibody%20Numbering%20Schemes/00149.webp)

![换一个位置继续看：不同方案对同一片段的编号与区域归属并不一致](assets/Antibody%20Numbering%20Schemes/00154.webp)

再往后滚动还能看到更多方案（如 AHo）——它们对同一段序列的编号也各有出入。

![更多编号方案（如 AHo）对同一条序列的另一种编号方式](assets/Antibody%20Numbering%20Schemes/00169.webp)

### 3.2 选择建议：一致性优先，比较 CDR 用 IMGT [【跳转到 02:49】](https://www.youtube.com/watch?v=8QLqX1_NJ9A&t=169)

作者反复强调：**这并不是说哪个定义一定更好**。真正的要点是：

- **从头到尾只用一种方案**。如果你的组织出于历史原因（legacy reasons）仍在用 Kabat 或 Chothia 这类较老的方案，那就坚持用下去，保证序列之间始终可比；
- 如果你的目标更多是**比较不同的 CDR**（尤其是长度不一的 CDR），建议选 **IMGT**，因为它对插入的处理最好。

## 四、编号软件：氨基酸与核苷酸两条路线 [【跳转到 03:14】](https://www.youtube.com/watch?v=8QLqX1_NJ9A&t=194)

### 4.1 氨基酸路线：统计式 vs 比对式

输入可变区的**氨基酸序列**，软件直接套用某种编号方案。代表工具（见下图幻灯片）：

- **AntPack、ANARCI**：以统计方式（如隐马尔可夫模型式的概型匹配）实现编号；
- **RIOT**（NaturalAntibody 自家软件）：走更确定性、老式的序列比对路线。

### 4.2 核苷酸路线：IgBLAST [【跳转到 03:49】](https://www.youtube.com/watch?v=8QLqX1_NJ9A&t=229)

手里只有**核苷酸序列**时，一般用 **IgBLAST**：它先从原始核苷酸序列中划出 CDR，再把它们翻译成氨基酸序列做编号。RIOT 的设计初衷正是把这两条路线**合而为一**——一个软件同时支持氨基酸与核苷酸序列分析。

![编号工具全景：氨基酸序列分析（ANARCI / AntPack / RIOT）与核苷酸序列分析（IgBLAST）两条路线](assets/Antibody%20Numbering%20Schemes/00254.webp)

### 4.3 免费学术工具与商业平台 [【跳转到 04:39】](https://www.youtube.com/watch?v=8QLqX1_NJ9A&t=279)

视频里提到的工具绝大多数**免费**：ANARCI 应该是学术界使用最多的免费氨基酸序列编号软件；IgBLAST 同样免费，在核苷酸序列注释领域应用非常广。此外还有 AbNum、AbRSA 等工具与商业发现平台（见下图）。

![更完整的工具清单：AbNum、AbRSA、企业级发现平台等也在此列](assets/Antibody%20Numbering%20Schemes/00279.webp)

以 NaturalAntibody 平台为例，编号功能分成三个模块：

| 模块 | 适用场景 | 你能得到什么 |
| --- | --- | --- |
| Sequence Engineering [【跳转到 05:04】](https://www.youtube.com/watch?v=8QLqX1_NJ9A&t=304) | 注释**单条**序列 | 种系基因（germline）上下文、CDR 标注、多种编号方案，附带大量其他注释 |
| Structure Numbering [【跳转到 05:16】](https://www.youtube.com/watch?v=8QLqX1_NJ9A&t=316) | 给编号加**结构**语境 | 编号结果直接标注到结构上 |
| Batch Sequence Annotation [【跳转到 05:31】](https://www.youtube.com/watch?v=8QLqX1_NJ9A&t=331) | **批量**序列（氨基酸/核苷酸皆可） | 按你指定的方案编号，结果可下载或继续在线分析 |

![单条序列注释：原始/目标种系基因、CDR 与编号一并输出](assets/Antibody%20Numbering%20Schemes/00304.webp)

![逐位置给出 IMGT / Kabat 的编号与区域（region）归属](assets/Antibody%20Numbering%20Schemes/00309.webp)

![结构编号：把编号连同 CDR-3、FW-4 等区域标注到序列与结构上](assets/Antibody%20Numbering%20Schemes/00326.webp)

![批量序列注释：一批序列按选定方案统一编号](assets/Antibody%20Numbering%20Schemes/00336.webp)

## 小结

- 编号方案 = **预计算的多序列比对**：给抗体每列比对结果起好名字，新序列"对号入座"即可判断属于框架区还是 CDR。
- 三大方案各有所长：**Kabat** 是起点（从 MSA 中浮现框架区/CDR 图景）、**Chothia** 侧重结构、**IMGT** 最好地处理 CDR 的插入缺失。
- 同一条序列（如曲妥珠单抗）在不同方案下 **CDR 边界差别很大**——方案没有绝对优劣，**一致性**才是生命线。
- 软件分两条路线：**氨基酸**（AntPack / ANARCI 统计式，RIOT 比对式）与**核苷酸**（IgBLAST）；ANARCI 与 IgBLAST 免费、最常用。
- 从单条（Sequence Engineering）、结构（Structure Numbering）到批量（Batch Annotation），商业平台把三种场景都覆盖了。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| 编号方案（numbering scheme） | 给抗体序列每个位置分配标准编号的坐标系，如 Kabat / Chothia / IMGT |
| MSA（多序列比对） | 把多条同源序列逐列对齐，用于找保守/可变位置 |
| 框架区（FR，framework） | 抗体可变区中保守的骨架部分，支撑 CDR 成环 |
| CDR（互补决定区） | 可变区中直接结合抗原的高变环 |
| trastuzumab（曲妥珠单抗） | 抗 HER2 单抗（商品名赫赛汀），视频中用作编号演示序列 |
| germline（种系基因） | 抗体序列从之重排而来的胚系基因，是序列归类的参照 |
| ANARCI / AntPack | 统计式氨基酸抗体编号工具（免费学术软件的代表） |
| IgBLAST | 面向核苷酸序列的免疫球蛋白专用比对注释工具（NCBI） |
