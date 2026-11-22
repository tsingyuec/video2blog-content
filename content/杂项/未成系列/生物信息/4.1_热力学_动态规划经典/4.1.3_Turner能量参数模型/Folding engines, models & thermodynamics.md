# Folding engines, models & thermodynamics

> 视频来源：[Folding engines, models & thermodynamics](https://www.youtube.com/watch?v=mmdiGHgwYko)（Eterna 官方频道，Eternacon 2016 演讲，讲者 Nando / ElNando88，约 39 分钟）。本文基于该视频的「图-字幕」演说文稿整理，所有要点均可回看视频核对。

**一句话结论：所有 RNA 二级结构预测引擎共用同一套「最近邻」热力学参数（Turner 1999 / Turner 2004），但每个引擎对这套参数的取舍与实现并不相同——同一个多分支环，ViennaRNA 1.x 评 −0.1 kcal、ViennaRNA 2 评 +2.3 kcal、NUPACK 评 +5.6 kcal；对在 2–3 kcal 量级做开关的 RNA 设计来说，这种差异足以完全翻转预测结果。**

## 本讲要解决的核心问题（SCQA）

**背景**：在 Eterna 这类 RNA 设计游戏里，玩家看到的每个发夹环、凸环、多分支环旁都标着一个 kcal 数值。这些数字来自 ViennaRNA、NUPACK 等「折叠引擎」，而引擎的地基是 Turner 1999 / Turner 2004 最近邻参数 [【跳转到 03:28】](https://www.youtube.com/watch?v=mmdiGHgwYko&t=208)。

**冲突**：同一条在实验室实测过的设计（Exclusion-3），三个引擎对同一个多分支环给出了从 −0.1 到 +5.6 kcal 的判读——有的说开关能工作，有的说不能 [【跳转到 07:38】](https://www.youtube.com/watch?v=mmdiGHgwYko&t=458)。

**疑问**：Turner 参数模型到底是什么？各引擎究竟实现了它多少？设计者该信谁？

**回答（中心思想）**：把 Turner 2004 发表的参数逐项与 ViennaRNA 源码对账就会发现：常数项 a 与分支项 c 的自由能值大体一致，但焓值可疑、不对称修正 b 被故意省略——按完整公式重算，Exclusion-3 的多分支环罚分应在 5 kcal 上下而不是 2.3。理解每个引擎「实现了哪些参数、省略了哪些修正」，是解读预测结果的前提。

## 一、四十年的演进：从「数碱基对」到「算自由能」

讲者先花两分钟梳理了 RNA 二级结构预测模型的历史脉络 [【跳转到 01:30】](https://www.youtube.com/watch?v=mmdiGHgwYko&t=90)：

![RNA 折叠模型历史线：1970 年代最早尝试、1981 年 Zuker 自由能最小化、1990 年代配分函数](assets/Folding%20engines,%20models%20&%20thermodynamics/00090.webp)

1. **1970 年代**：最早的尝试是「数碱基对」——Tinoco 一脉的思路后来被 Nussinov 算法固化为「碱基对最大化」：对一条序列， simply 试着让能配上的碱基对越多越好。这是个很朴素的方案 [【跳转到 01:30】](https://www.youtube.com/watch?v=mmdiGHgwYko&t=90)。
2. **1981 年，Zuker**：提出基于**自由能最小化**的更成熟模型——这就是今天我们所说的**最近邻模型（nearest-neighbor model）**的雏形。当时只求最小自由能结构（MFE）[【跳转到 01:55】](https://www.youtube.com/watch?v=mmdiGHgwYko&t=115)。
3. **1990 年代，McCaskill**：把它发展成完整的**配分函数**（partition function），给出整段 RNA 结构系综的热力学图景，而不再只看一个最优解 [【跳转到 02:20】](https://www.youtube.com/watch?v=mmdiGHgwYko&t=140)。

### 1.1 最近邻模型的一句话直觉

把被碱基对和骨架围起来的每一个「区域」（发夹环、内部环、凸环、多分支环、堆叠区……）当成一个独立的能量单元，给每个单元分配一个自由能贡献——这些就是玩家在 Eterna 游戏里看到的那些 kcal 数值；每个单元各有自己的参数 [【跳转到 02:45】](https://www.youtube.com/watch?v=mmdiGHgwYko&t=165)。整条序列的自由能就是各单元之和，自由能最低的结构即 MFE 结构。

![最近邻模型：以碱基对与骨架围出的环为能量单元，逐个赋予 kcal 贡献](assets/Folding%20engines,%20models%20&%20thermodynamics/00170.webp)

## 二、Eterna 的三台引擎与它们背后的参数集

讲者作为 Eterna 折叠引擎的开发者，介绍了平台引擎与参数集的历史 [【跳转到 03:28】](https://www.youtube.com/watch?v=mmdiGHgwYko&t=208)：

![Eterna 引擎与参数集历史：ViennaRNA 1.x 配 Turner 1999，第二台引擎默认 Turner 2004，另有 Andronescu 2007 与 NUPACK](assets/Folding%20engines,%20models%20&%20thermodynamics/00208.webp)

- **第一台引擎：ViennaRNA 1.x**，自带参数集名为 **Turner 1999**。
- **第二台引擎**（讲者在项目中主导集成）：默认参数集为 **Turner 2004**，并可选其他模型——例如 **Andronescu 2007** 参数集 [【跳转到 03:53】](https://www.youtube.com/watch?v=mmdiGHgwYko&t=233)。
- **新加入的 NUPACK**：可计算全部 ΔG；但它的默认参数集是 **1995 年**的那一套。至于 1995 参数到底出自谁之手，讲者与 Cody Geary 讨论过也拿不准（一个说法与 Mathews 相关），他有意不点名 [【跳转到 04:18】](https://www.youtube.com/watch?v=mmdiGHgwYko&t=258)。
- Eterna 也可选用 **Turner 1999**，但有个讲者至今未解的谜：**Turner 1999 不带焓（enthalpy）参数**——焓参数本可用于估算熔点、评估随温度的变化；NUPACK 因此没有，而 ViennaRNA 里却「不知从哪来的」有焓参数 [【跳转到 05:08】](https://www.youtube.com/watch?v=mmdiGHgwYko&t=308)。

> 名词卡：**参数集（parameter set）**指一套针对各类结构单元（堆叠、发夹环、凸环、内部环、多分支环、悬垂碱基等）的自由能/焓数值表；**Turner 1999 / 2004** 是 Mathews、Turner 等人整理的两代标准参数集，2004 版是多数引擎当前的默认。

## 三、一个翻车案例：Exclusion-3 开关设计

讲者把全场重点放在一条具体设计上 [【跳转到 05:58】](https://www.youtube.com/watch?v=mmdiGHgwYko&t=358)：

![Exclusion-3 谜题设计：同一多分支环，三个引擎给出三个截然不同的 ΔG](assets/Folding%20engines,%20models%20&%20thermodynamics/00358.webp)

这是 Eterna 的 **Exclusion-3** 谜题的一条玩家设计（由 Salish99 等贡献，且在实验室做过实测）。三个引擎对其中同一个**多分支环（multiloop）**的判读 [【跳转到 06:23】](https://www.youtube.com/watch?v=mmdiGHgwYko&t=383)：

| 引擎 | 多分支环 ΔG | 言外之意 |
| --- | --- | --- |
| ViennaRNA 1.x | **−0.1 kcal**（几乎"稳定"） | 荒谬：在实验室待过的人一眼就会觉得不对——悬垂碱基怎么可能因此稳定 |
| ViennaRNA 2 | **+2.3 kcal** | 仍低估了不稳定性 |
| NUPACK | **约 +5.6 kcal** | 最接近完整 Turner 2004 公式的结果 |

![三引擎对同一多分支环的评价值对比：−0.1 / +2.3 / +5.6 kcal](assets/Folding%20engines,%20models%20&%20thermodynamics/00458.webp)

差异直接改变结论 [【跳转到 07:38】](https://www.youtube.com/watch?v=mmdiGHgwYko&t=458)：按 ViennaRNA 的评估，这个**开关（switch）不会工作**；若多分支环真有 +5.6 kcal 那么不稳定（NUPACK 的判读），开关就会工作。**谁对？为什么？**

ViennaRNA 用的理论上是 Turner 2004 参数 [【跳转到 08:03】](https://www.youtube.com/watch?v=mmdiGHgwYko&t=483)。正是这个矛盾促使讲者去查公开资料。

## 四、查公开资料：Turner 2004 怎么算多分支环

答案在 **NNDB（Nearest Neighbor Database，最近邻参数数据库）**——全部公开，稍加挖掘就能找到 Turner 2004 的完整计算细节 [【跳转到 08:42】](https://www.youtube.com/watch?v=mmdiGHgwYko&t=522)。

![NNDB 上 Turner 2004 多分支环起始公式的讲解页：参数 a、b、c](assets/Folding%20engines,%20models%20&%20thermodynamics/00547.webp)

把堆叠、错配介导的堆叠、共轴堆叠等复杂修正先放在一边，只看多分支环的**起始 ΔG**。公式里有四个参数，其中三个最重要，记作 **a、b、c** [【跳转到 09:07】](https://www.youtube.com/watch?v=mmdiGHgwYko&t=547)：

- **a：常数项**——多分支环的「基础不稳定性」，约 +9.3 kcal；
- **b：不对称修正（asymmetry）**——按每个分支两侧未配对段的长度差施加的罚分，取平均；
- **c：分支数项**——每条分支螺旋通常带来一个**稳定化**（负值）贡献。

### 4.1 不对称修正怎么算

![不对称修正示例：三处分支的未配对段长度差分别约 11、11、0，平均约 7.3](assets/Folding%20engines,%20models%20&%20thermodynamics/00615.webp)

看一个螺旋堆叠处，比较它两侧未配对段的长度 [【跳转到 09:50】](https://www.youtube.com/watch?v=mmdiGHgwYko&t=590)：比如一侧是 1 个碱基、另一侧是 12 个，差值 11 就是这一支的不对称度；三支的不对称度分别是 11、11、0，平均约 7.3 [【跳转到 10:15】](https://www.youtube.com/watch?v=mmdiGHgwYko&t=615)。注意 b 项有**封顶**：超过 2.0 的一律按 2.0 计 [【跳转到 10:35】](https://www.youtube.com/watch?v=mmdiGHgwYko&t=635)。

## 五、逐项对账：Turner 论文 vs ViennaRNA 源码

讲者把 Turner 2004 发表的参数（屏幕左下）与 ViennaRNA 团队公布的源码参数（右侧）逐点对比 [【跳转到 11:05】](https://www.youtube.com/watch?v=mmdiGHgwYko&t=665)：

![Turner 2004 发表参数与 ViennaRNA 源码参数的逐项对比表（注意 kcal 与 dcal 单位差 100 倍）](assets/Folding%20engines,%20models%20&%20thermodynamics/00690.webp)

> **单位陷阱**：Turner 论文用 kcal，ViennaRNA 源码文件用 dcal，换算要乘或除以 100 [【跳转到 11:30】](https://www.youtube.com/watch?v=mmdiGHgwYko&t=690)。

对账结果 [【跳转到 11:55】](https://www.youtube.com/watch?v=mmdiGHgwYko&t=715)：

| 参数 | Turner 2004 发表值 | ViennaRNA 源码值 | 讲者评语 |
| --- | --- | --- | --- |
| a（ΔG） | 9.30 | 9.25 | 非常接近，没问题 |
| a（ΔH 焓） | 30.0 | 34.8 / 34.9 | 在误差范围内，尚可 |
| c（ΔG，每分支） | 约 −0.6 ~ −0.8 | −0.9 | **每分支差约 0.3 kcal，偏多** [【跳转到 12:31】](https://www.youtube.com/watch?v=mmdiGHgwYko&t=751) |
| c（ΔH 焓） | 应为 −11 ~ −12 | −2 | **完全在误差棒之外，非常奇怪** [【跳转到 12:56】](https://www.youtube.com/watch?v=mmdiGHgwYko&t=776) |
| b（不对称修正） | 存在 | **完全找不到** | 见下 |

### 5.1 b 的缺席是「故意的」

不对称项在 ViennaRNA 里不存在——而这根本不是谜 [【跳转到 13:46】](https://www.youtube.com/watch?v=mmdiGHgwYko&t=826)：2011 年 ViennaRNA 包发布新版本时的论文写明，他们**有意不实现**一些「高度特化的配置（highly specialized configurations）」，其中之一就是多分支环的平均不对称修正罚分。此外，Turner 2004 规定的「三分支环且未配对碱基 ≤1 时」的额外罚分也没有实现——不过讲者认为这条影响相对次要 [【跳转到 14:21】](https://www.youtube.com/watch?v=mmdiGHgwYko&t=861)。

![ViennaRNA 2.0（2011）论文：有意省略不对称修正等「高度特化配置」](assets/Folding%20engines,%20models%20&%20thermodynamics/00861.webp)

## 六、重算 Exclusion-3：应约 5 kcal，而不是 2.3

回到那条谜题设计。它是一个三分支环：按 Turner 2004 完整公式，分支数修正贡献约 0.9 kcal 的罚分，环的不对称性再带来 1 kcal 多的额外罚分——**总罚分应在 5 kcal 上下，绝不可能是 2.3** [【跳转到 14:57】](https://www.youtube.com/watch?v=mmdiGHgwYko&t=897)。

![按完整 Turner 2004 公式重算：该多分支环罚分应约 5 kcal，NUPACK 的判读更接近](assets/Folding%20engines,%20models%20&%20thermodynamics/00947.webp)

这为什么致命？因为 Eterna 的**开关设计恰恰在 2–3 kcal 的窗口内切换构象**——2.3 与 5 之间的差别，足以把「开关能动」判成「开关不能动」，完全推翻你在这个量级上做的任何设计与预测 [【跳转到 15:22】](https://www.youtube.com/watch?v=mmdiGHgwYko&t=922)。

## 七、引擎为什么长这样：自然 RNA 基准的「偏见」

以上对账都是有据可查的（讲者提供了幻灯片与所有出处的链接）。接下来的部分他明说「更多是个人观点」[【跳转到 15:47】](https://www.youtube.com/watch?v=mmdiGHgwYko&t=947)。

### 7.1 IRE hack：写进参数表的生物学特例

讲者展示的第一条线索，是他称之为 **IRE hack** 的东西：引擎里有一批「特例参数」，对特定序列的六元发夹环（hexaloop）给予额外稳定化 [【跳转到 17:52】](https://www.youtube.com/watch?v=mmdiGHgwYko&t=1072)。这些序列正是 **IRE（iron responsive element，铁响应元件）**的发夹环——一个在人类与哺乳动物基因组中、成千上万基因的非翻译区（UTR）里都能找到的信号，与铁代谢的调控密切相关 [【跳转到 18:17】](https://www.youtube.com/watch?v=mmdiGHgwYko&t=1097)。

![IRE 六元环特例参数：为铁响应元件的发夹环专门加权，讲者称之为 hack](assets/Folding%20engines,%20models%20&%20thermodynamics/01147.webp)

他的质疑是：**这凭什么写进一个通用折叠引擎？**这条信号之所以特殊，是因为 C、G 倾向于配对形成类似三碱基环的结构，并且它能结合 IRP（铁响应蛋白）——它本质上是一个**适配体（aptamer）**，是调控网络的一环 [【跳转到 19:07】](https://www.youtube.com/watch?v=mmdiGHgwYko&t=1147)。把某个生物学信号的加分硬编码进引擎，讲者认为动机很可疑。

### 7.2 基准数据集本身有偏

引擎的评判方式给出了线索 [【跳转到 20:43】](https://www.youtube.com/watch?v=mmdiGHgwYko&t=1243)：软件可以从两面评价——性能与存储占用这类**客观指标**，以及在固定基准上的**灵敏度/特异性**。后者常用的目标集是 **RNA STRAND 数据库**，而它收录的 RNA 全部是**天然存在**的。Eterna 玩家设计的人工序列显然不属于这一类——讲者直言这是偏见：引擎作者的参数（包括 IRE 特例）是在这个天然 RNA 数据集上「调」到最好看的，而多分支环恰恰是各类结构单元中**数据最少**的一类，怎么调都几乎不影响总分 [【跳转到 21:58】](https://www.youtube.com/watch?v=mmdiGHgwYko&t=1318)。

![以 RNA STRAND 数据库为基准的引擎评估：全是天然 RNA，讲者认为对人工设计存在偏见](assets/Folding%20engines,%20models%20&%20thermodynamics/01243.webp)

穿插的问答也印证了信息缺口：Rachel 问「Turner 99 参数里多分支环的自由能贡献为什么是负的」，讲者表示没查过 ViennaRNA 1.8 的源码、无法回答；「各种 boost 都应用了吗？——我想是吧」[【跳转到 16:37】](https://www.youtube.com/watch?v=mmdiGHgwYko&t=997)。

### 7.3 讲者的「悲观」设计

他自己能做的补救有限 [【跳转到 22:47】](https://www.youtube.com/watch?v=mmdiGHgwYko&t=1367)：把自己的设计全部打上 **pessimistic（悲观）**标签——把 −0.9 的分支参数手动改回 −0.6，对多分支环折叠、FMN 适配体结合等都按更悲观的口径评估。唯独不对称修正他加不进去——那要深入动态规划的底层；他一直梦想有一台属于自己的、面向对象的重写引擎，但看了多年源码后承认那些代码「又好又糟」，重写是个浩大工程 [【跳转到 23:37】](https://www.youtube.com/watch?v=mmdiGHgwYko&t=1417)。

## 八、工程现实：参数可以换，特征改不动

有观众问：能不能复用现有引擎、只调参数？讲者的回答是「这是两件事」[【跳转到 24:27】](https://www.youtube.com/watch?v=mmdiGHgwYko&t=1467)：

- **参数可以换**：Eterna 的脚本接口有一个 API，可以把整套装好的参数上传给指定引擎——他已经在 ViennaRNA 上试过，能用；缺的只是文档 [【跳转到 36:07】](https://www.youtube.com/watch?v=mmdiGHgwYko&t=2167)。
- **特征改不动**：不对称罚分、配体结合这类「特征」必须深挖动态规划的实现。他为配体结合写过自己的 hack，结果被 ViennaRNA 在 2.2 前后用更通用的实现「截胡」[【跳转到 25:17】](https://www.youtube.com/watch?v=mmdiGHgwYko&t=1517)；不对称修正他也因此迟迟不敢动手——万一半年后 ViennaRNA 官方实现了呢？他还认真考虑过从苏黎世飞两小时去维也纳当面请托，苦于自己没有学术身份 [【跳转到 25:42】](https://www.youtube.com/watch?v=mmdiGHgwYko&t=1542)。

其他工程背景同样能解释引擎的现状 [【跳转到 27:47】](https://www.youtube.com/watch?v=mmdiGHgwYko&t=1667)：三台引擎的源码都是 C++，当年是靠一个早已停止维护的产品 **Alchemy** 把 C++ 编译成 Flash 字节码才跑进 Eterna 的——三台引擎能一起工作「不是天才，是运气」[【跳转到 28:12】](https://www.youtube.com/watch?v=mmdiGHgwYko&t=1692)。如今 ViennaRNA 2.x 开始提供面向对象 API、把底层原语藏到接口后面，代码看起来干净多了，只是刚发布、坑还多，讲者打算等几个月再看 [【跳转到 29:02】](https://www.youtube.com/watch?v=mmdiGHgwYko&t=1742)。

最后是一个乐观的注脚：过去只有生物化学家能一小批一小批地测稳定性数据，而 Eterna 玩家已经积累了海量训练数据；他与 RNAstructure 的作者 Dave Matthews（以及参数命名中的 Doug Turner）保持交流——Matthews 想做支持修饰核苷酸能量的折叠器，面向对象分支可能年内合并 [【跳转到 30:17】](https://www.youtube.com/watch?v=mmdiGHgwYko&t=1817)。讲者很乐意牵线，避免重复劳动。

## 九、为什么只有动态规划：多项式时间的唯一解

还有观众提出「自带模型（bring your own model）」的畅想：做一个通用的能量模型平台，让玩家自带参数、即时试算「如果这个多环再不稳定一点会怎样」。讲者的回答很冷静 [【跳转到 33:37】](https://www.youtube.com/watch?v=mmdiGHgwYko&t=2017)：

![动态规划的两个阶段：填大表与回溯——参数好换，特征难加](assets/Folding%20engines,%20models%20&%20thermodynamics/02267.webp)

- **参数层面**：换参数文件、微调数值都不难；
- **特征层面**：像「给多分支环内部加不对称罚分」这类新特征，要写进填表与回溯两个阶段，极难，尤其还想做成可插拔/可动态调整——讲者坦言自己也不知道怎么解 [【跳转到 34:52】](https://www.youtube.com/watch?v=mmdiGHgwYko&t=2092)。

更深一层的理由：最近邻模型若不用动态规划，复杂度是指数级甚至阶乘级的；**迄今唯一已知的多项式时间解法就是动态规划**（N³ 或 N⁴，取决于具体变体）——「这是 Zuker 的天才之举」[【跳转到 37:47】](https://www.youtube.com/watch?v=mmdiGHgwYko&t=2317)。换别的算法可以，但会撞上规模墙，目前还没有人做成 [【跳转到 38:37】](https://www.youtube.com/watch?v=mmdiGHgwYko&t=2317)。

## 小结

- 最近邻模型把 RNA 结构自由能拆成「逐单元之和」：发夹环、凸环、内部环、多分支环、堆叠……各有参数；Turner 1999/2004 是两代标准参数集，ViennaRNA、NUPACK、RNAstructure 等引擎都建在其上。
- **引擎 ≠ 参数集**：ViennaRNA 2 出于明确的设计决策省略了不对称修正 b 与若干特例罚分，分支项 c 每分支偏差约 0.3 kcal，焓值与论文相差悬殊。
- 多分支环是各类单元中实验数据最少、引擎间分歧最大的；对在 2–3 kcal 量级切换构象的开关设计，这种分歧足以翻转「能/不能工作」的结论。
- 判读预测时要问三件事：用的哪代参数集？省略了哪些修正项？基准数据集（天然 RNA）与你的设计（人工序列）是否同类？
- 动态规划是最近邻模型唯一已知的多项式时间解法，也正因如此，「参数可上传、特征难插件化」是所有引擎的共同工程约束。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| 最近邻模型 | 把被碱基对/骨架围出的环与堆叠当作独立能量单元、整链自由能为各单元之和的热力学模型 |
| Turner 1999 / 2004 | 两代标准 RNA 最近邻参数集，2004 版为多数引擎当前默认 |
| NNDB | Nearest Neighbor Database，公开查询 Turner 参数公式与数值的网站 |
| MFE | 最小自由能结构：所有候选二级结构中自由能最低者 |
| 配分函数 | McCaskill 提出的系综算法，给出全部结构的热力学权重而非单一最优解 |
| 多分支环（multiloop） | 三条及以上螺旋从一点分出的环；ΔG 由常数 a、不对称修正 b、分支项 c 共同决定 |
| 不对称修正（asymmetry） | 按分支两侧未配对段长度差施加的罚分；取平均后封顶 2.0 kcal；ViennaRNA 未实现 |
| dcal | 0.01 kcal；ViennaRNA 源码参数单位，与论文 kcal 相差 100 倍 |
| 焓参数（ΔH） | 用于温度外推（如估算熔点）的配套参数；Turner 1999 不含，NUPACK 因此也没有 |
| IRE / IRP | 铁响应元件及其结合蛋白；其六元发夹环被参数表特殊加权，讲者称之为 hack |
| RNA STRAND | 已知 RNA 二级结构数据库；常用作引擎评估基准，但全部为天然 RNA |
| 动态规划 | 「填表 + 回溯」两阶段算法；最近邻模型多项式时间（N³/N⁴）求解的唯一已知途径 |
