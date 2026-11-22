# Confidence Scores Don't Predict Affinity：%20Negative Data and AlphaSeq（A-alpha Bio）

> 视频来源：YouTube《Confidence Scores Don't Predict Affinity: Negative Data and AlphaSeq (A-alpha Bio)》（RANOMICS 频道 Protein Engineering in Practice 系列，约 51 分钟）。主持：Leo Wan（RANOMICS）与 Michael Holden；嘉宾：**Joseph**（A-alpha Bio 首席科学家，de novo 蛋白设计背景）与 **Natasha**（A-alpha Bio 应用数据科学与 ML 总监）。本篇是 6.1.5「迭代筛选」的姊妹篇：上一讲确立"置信分数不能预测亲和力、必须实验筛选"；本讲回答**筛出来的数据（尤其是阴性数据）如何变成模型的教材**。

## 本讲要解决的核心问题（SCQA）

**背景**：管线 A 走完生成（RFdiffusion）→ 配序列（ProteinMPNN）→ 回折验证（Protenix/ipTM）后，你手里有数万条候选和一批实测结合数据。大家都知道"数据是模型的秘方"，但**阴性数据从哪来**、什么叫 hard negative、百万级互作数据怎么变成训练集，仍是黑箱。

**冲突**：PDB 里只有阳性样本——"不结合的晶体结构"根本不会被解析；可重复性危机让大量失败数据锁在抽屉里。当前模型只学"什么黏得住"，不学"什么别做"；而 ipTM/ipSAE 置信分与真实亲和力几乎零相关。

**疑问**：怎么系统性地生成带标注的阴性数据？高通量结合数据怎么转成监督学习问题？置信分数到底差在哪、mini binder 能期待什么亲和力？

**回答（中心思想）**：用"库对库"酵母展示（AlphaSeq）把结合测量变成百万级监督数据——设计"看似该结合"的准结构（pseudostructure）再实验验证，构造 **hard negatives**；用浅层编辑局部亲和力地形 + "跑到崩为止"的优化管线把 binder 推向可开发性；置信度只回答"结构是否成立"，结合与否必须**正交测量**。

## 一、A-alpha Bio 与 AlphaSeq：把 PPI 变成大数据

### 1.1 库对库酵母展示：一次实验测百万级互作

A-alpha Bio 自我定位是一家**蛋白-蛋白相互作用（PPI）公司**。它的核心武器 AlphaSeq 是一个"库对库"（library-on-library）酵母展示平台：一次实验能**定量测数百万个蛋白-蛋白相互作用**；公司成立近十年，这样的实验做了几百次，积累了抗体、抗原及各类 PPI 的海量亲和力数据（[【跳转到 03:50】](https://www.youtube.com/watch?v=9zFnXwpbHyc&t=230)）。如今他们围绕这些数据训练与开发机器学习模型，目标是更好地发现与优化高质量药物。

![AlphaSeq：库对库酵母展示，一次实验定量测数百万个蛋白-蛋白相互作用](assets/Confidence%20Scores%20Don't%20Predict%20Affinity：%20Negative%20Data%20and%20AlphaSeq（A-alpha%20Bio）/00280.webp)

### 1.2 赋能数据层：两种语言都要会说

Natasha 把公司定位画得很清楚：这些模型的"秘方"就是数据集，而**好模型需要好数据、好数据又需要懂模型**——鸡生蛋蛋生鸡。A-alpha Bio 把自己放在中间的"赋能数据层"，模型的语言和实验的语言都得会说（[【跳转到 05:05】](https://www.youtube.com/watch?v=9zFnXwpbHyc&t=305)）。

## 二、阴性数据：模型缺失的另一半

### 2.1 可重复性危机与 PDB 的幸存者偏差

科学历来奖励阳性——"成了、分子很好"；但没人看到背后的无数次失败。Michael 从发表者视角补了一刀：过去十年湿实验科学的一大问题是**可重复性危机**，原因之一是只有"矛尖"上了期刊——最终进 PDB 的是晶体学家的最佳选择：成功的那一个突变体、最"能用"的那组设计（[【跳转到 06:45】](https://www.youtube.com/watch?v=9zFnXwpbHyc&t=405)）。语料库里缺的、实际上大量存在却锁在文件柜与硬盘里的，是**无数负向数据**。

### 2.2 别把模型变成悲观主义者

阴性数据也不是越多越好：历史上发现，负向数据太多会把模型变成"悲观主义者"——它说"什么都不行"就永远对了。AlphaSeq 的妙处在于**规模足够大，能同时拿到足够的正、负样本**，比例又足以保留可训练的信号（[【跳转到 08:00】](https://www.youtube.com/watch?v=9zFnXwpbHyc&t=480)）。

### 2.3 hard negatives：决策边界上的教材

A-alpha 的哲学是：按"应该结合"的思路生成序列与结构——理论上都该是阳性、都该工作；**当然现实从不如此，但这依然是极有用的信息**。他们称之为 **hard negatives**——处在决策边界上、"看似该行却没行"的貌似结合物。用它教模型：在分布内部，你的表征错在哪里（[【跳转到 09:15】](https://www.youtube.com/watch?v=9zFnXwpbHyc&t=555)）。"不结合的晶体结构"根本不会存在，但实验上做得到——这就把设计问题变成了**监督学习问题**。

![hard negatives：决策边界上"看似该结合却没结合"的样本，是模型的教材](assets/Confidence%20Scores%20Don't%20Predict%20Affinity：%20Negative%20Data%20and%20AlphaSeq（A-alpha%20Bio）/00555.webp)

### 2.4 失败也要标注：非特异 vs 折叠但不结合

Leo 强调：负向数据不只是数据，还要好好标注——哪种失败、什么技术问题。Natasha 补充实操：把 in silico 指标与实测耦合起来就能开始拆解失败模式——蛋白失败的方式有几十种（表达、折叠……），AlphaSeq 可以分辨：这个负样本是**非特异性**，还是"仍正确折叠、只是不结合"？（[【跳转到 10:30】](https://www.youtube.com/watch?v=9zFnXwpbHyc&t=630)）这类数据对教模型区分好坏非常有价值。

## 三、从数据到模型：ML 管线的 80/20

### 3.1 先问要建模什么：亲和力回归 vs 相对亲和力

Natasha 透露日常主业的心法：任何 ML 管线都是老话——**算法只占 20%，80% 在把数据整理到算法真能学的程度**（他们已在 Hugging Face 开源了几份数据集，合计约几百万数据点）。第一步是弄清楚你要问什么问题：大家都以为亲和力是个扁平分数（越低越好），但直接建模很难——一堆不结合的、一堆结合的，中间过渡区间采样很少；所以可以把问题转换成**相对亲和力**：与母本相比，这个变体好多少？（[【跳转到 18:25】](https://www.youtube.com/watch?v=9zFnXwpbHyc&t=1105)）

### 3.2 PPI 至少两条序列：A 与 alpha

与其它蛋白建模范式不同，PPI 至少需要**两条输入序列**——对 A-alpha Bio 来说是 A（antibody）与 alpha（antigen），永远是 binder-target 对。所以先要决定模型架构怎么"吃进"两条序列（[【跳转到 18:00】](https://www.youtube.com/watch?v=9zFnXwpbHyc&t=1080)）。

### 3.3 实验设计比跑实验更重要

Joseph 点出一个被低估的环节：**实验设计**。AlphaSeq 可以把成千上万条 binder、target 及其变体按任意组合放进实验，于是问题变成"你要解决什么问题、在这些约束内能构建什么数据集"——有结构的话聚焦界面吗？是不是做 zero-shot 类问题？他们花在这些思考上的时间比跑实验、做 ML 还多（[【跳转到 19:15】](https://www.youtube.com/watch?v=9zFnXwpbHyc&t=1155)）。

### 3.4 一轮多久：深度与广度两种玩法

实操时间账：受限于 DNA 订购（2~4 周），一轮 AlphaSeq 实验本身约 **3~5 周**（[【跳转到 20:30】](https://www.youtube.com/watch?v=9zFnXwpbHyc&t=1230)）。玩法有两种（[【跳转到 16:20】](https://www.youtube.com/watch?v=9zFnXwpbHyc&t=980)）：

- **深度**：一条抗体 × 一个抗原，抗体侧/抗原侧或双侧各做几万个突变，深挖这组相互作用；
- **广度**：几百个抗原对几百个抗体（比如关心同源蛋白结合时）；突变落在 CDR 还是框架区均可，"说到底取决于你最后想订哪些 DNA"。

## 四、AlphaBind 与抗体优化管线

### 4.1 750 万条抗体-抗原互作：从架构到生产线

AlphaBind 不只是一个已发表的架构/数据集（**750 万条抗体-抗原结合相互作用**），更是抗体优化生产管线的组成部分。圣杯当然是**零样本（zero-shot）优化**——我有一条 binder、有喜欢的性质，想改造它、扩展序列多样性，怎么做？（[【跳转到 12:35】](https://www.youtube.com/watch?v=9zFnXwpbHyc&t=755)）

### 4.2 Genmab 对照 VH：区分"稳定性问题"与"亲和力问题"

合作者 Genmab 刚发表的论文提供了一个巧妙设计：比较"**对照 VH 与常规 VH 结合抗原**"。设你有一个抗原、两个靶向不同表位的 VH：改变后若两个 VH 都受影响，说明问题在所表达蛋白的**稳定性**；若只有测试的那个受影响，那就是**结合几何与亲和力**的问题（[【跳转到 11:45】](https://www.youtube.com/watch?v=9zFnXwpbHyc&t=705)）。

### 4.3 AbOpt 管线：浅层编辑地形 + "跑到崩为止"

AbOpt 管线的做法：生成"浅层编辑"变体——单突变、少量双/三突变，绘制**局部亲和力地形图**，据此理解结合几何的敏感度。工作流是：生成浅层编辑局部地形 → 测结合 → 微调模型 → 跑优化管线。管线哲学是**"跑到崩为止"**：尽量走出 10、20、30 个突变，看结合是否保留；因为有全局图景，许多提议的编辑走出 10~20 个突变仍保留对目标靶的亲和力（[【跳转到 13:25】](https://www.youtube.com/watch?v=9zFnXwpbHyc&t=805)）。

### 4.4 过了结合这一关：免疫原性、Tm 与交叉反应

走出 10、20 个突变之后呢？有时 5 个突变就够拿一个新专利了。这时精彩的事才开始：如何保证**不引发免疫原性**？如何有**热稳定性（Tm）**？如何保证想要的**交叉反应**？现在手上有高度多样的 binder 阵地，可以开始为这些性质做优化（[【跳转到 14:15】](https://www.youtube.com/watch?v=9zFnXwpbHyc&t=855)）。

![过了结合关之后：免疫原性、热稳定性与交叉反应成为新的优化目标](assets/Confidence%20Scores%20Don't%20Predict%20Affinity：%20Negative%20Data%20and%20AlphaSeq（A-alpha%20Bio）/00855.webp)

### 4.5 用 pH/盐扰动逼近可开发性

可开发性是药企第一关注。在酵母展示里测熔解温度当然更难，但 A-alpha 正在尝试 R&D 路线：**扰动 AlphaSeq 实验环境——改 pH、改盐浓度**——给亲和力测量引入生物物理扰动，再尝试与下游可开发性性质关联；还没有定论，但方向明确（[【跳转到 15:05】](https://www.youtube.com/watch?v=9zFnXwpbHyc&t=905)）。

## 五、SEPIA：给抗体做 mini binder，把设计问题变成监督问题

### 5.1 PDB 的偏置与"表位场"

Joseph 从论点说起：训练更好的抗体设计模型需要更多数据，而 PDB 这份几代人几十年的心血，**全部公开数据里抗体-抗原结构也就一万上下的量级**，且偏置严重——只有能结合的、集中在人源治疗靶点或病毒抗原、基本没有亲和力标签（[【跳转到 22:10】](https://www.youtube.com/watch?v=9zFnXwpbHyc&t=1330)）。

### 5.2 反其道而行：设计"针对抗体的" mini binder

SEPIA 的顿悟：设计**针对抗体的 mini binder**可能比反方向（设计针对抗原的 de novo 抗体）更容易、更快、成功率也许更高——mini binder 比抗体小，计算与实验两端都更容易、更便宜；若聚焦表位/抗原生成，几乎可以采样一个"**表位场**"（epitope field）——任何想让 VHH 或 scFv 抓住的表位、任意构象、非常多样的结构（[【跳转到 23:25】](https://www.youtube.com/watch?v=9zFnXwpbHyc&t=1405)）。Leo 评价这几乎是反其道而行之：**"你们在做抗独特型 binder（anti-idiotype）"**——他在药企做过独特型抗体，认为这是个好主意。

![SEPIA 思路：聚焦表位生成，采样任意构象的"表位场"](assets/Confidence%20Scores%20Don't%20Predict%20Affinity：%20Negative%20Data%20and%20AlphaSeq（A-alpha%20Bio）/01405.webp)

### 5.3 准结构（pseudostructure）：把设计问题变成监督问题

SEPIA 的核心概念是**准结构**：计算设计出来、未必有实验解析、但**已被实验验证**（结合或不结合）的结构。PDB 只有阳性样本，模型学到的只是"什么看起来像合理的结合界面"；生成"看似应该结合"的准结构、再实验验证结合与否，就把问题变成监督学习问题，进而可探索 hard negatives——怎么告诉模型"别做什么"（[【跳转到 25:30】](https://www.youtube.com/watch?v=9zFnXwpbHyc&t=1530)）。

![准结构：计算设计、实验验证结合与否，把设计问题变成监督学习](assets/Confidence%20Scores%20Don't%20Predict%20Affinity：%20Negative%20Data%20and%20AlphaSeq（A-alpha%20Bio）/01530.webp)

### 5.4 验证有效：数据训练出的过滤器优于标准过滤器

闭环的产出：在 in silico 生成几万、几十万这样的结构 → AlphaSeq 确认结合与否、测特异性与亲和力 → 用数据训练 ML 模型（或做"选设计进实验室"的过滤器）时，**真的看到方法有效——用这类数据训练的模型，表现优于标准过滤器**（[【跳转到 24:40】](https://www.youtube.com/watch?v=9zFnXwpbHyc&t=1480)）。团队复盘这段思路的形成也很有意思：这是个 ML 中心的问题，缺的就是这类数据，于是"灵光一现"——给抗体做 mini binder 吧，为什么？不重要——都是蛋白-蛋白相互作用，反过来做容易得多（[【跳转到 28:00】](https://www.youtube.com/watch?v=9zFnXwpbHyc&t=1680)）。

![湿实验+干实验配对：从"缺什么数据"倒推出 SEPIA 的反转向设计](assets/Confidence%20Scores%20Don't%20Predict%20Affinity：%20Negative%20Data%20and%20AlphaSeq（A-alpha%20Bio）/01680.webp)

## 六、置信分数的边界与无序蛋白的教训

### 6.1 一句话框架：confidence ≠ biophysics

Natasha 给了全场最简短的框架：**置信（confidence）≠ 生物物理（biophysics）**——置信度告诉你"结构是否成立"，不告诉你"会不会结合"。所以需要**正交的测量**来引导这些指标：可能是另一种形式的 confidence、可能是 ipSAE 等模型置信度的改造版，但需要一个明确衡量"实际结合亲和力合理性"的新指标（[【跳转到 28:50】](https://www.youtube.com/watch?v=9zFnXwpbHyc&t=1730)）。

### 6.2 数据驱动的"隐式生物物理"

Joseph 的回答分两层。其一，A-alpha **没有**在直接构建显式考虑蛋白生物物理的模型；他们在做的是数据驱动——AlphaSeq 数据本质是逐对的结合亲和力读出，其中**隐含**着生物物理（必须折叠、必须结合、必须以特定方式相互作用），用序列、结构和功能读出把它表示出来，"我愿意认为这比单看 ipSAE 更好"（[【跳转到 30:05】](https://www.youtube.com/watch?v=9zFnXwpbHyc&t=1805)）。其二，要厚道地说：这些置信度指标出自**结构预测模型**，本来就没人打算用它解这个问题；因为方便、现成、有信号，大家到处用——而那个信号只是"两样东西结合"这一静态预测的表征，并不总反映真实生化。任何做过分子动力学、处理过无序蛋白的人都会说：你的结构八成本来就不对（[【跳转到 30:55】](https://www.youtube.com/watch?v=9zFnXwpbHyc&t=1855)）。

### 6.3 tau 蛋白与"概率的概率"

Leo 用自己的研究经历给出边界案例：抗体类结构有领域知识与 repertoire 约束，模型表现尚可；但**酶的原肽（propeptide）**与**内在无序蛋白（IDP）**就不好使——他研究 tau 蛋白（441 个氨基酸的人源神经元内在无序蛋白）多年，做过溶液 NMR、FRET、单分子各向异性，那类问题要从完全不同的角度切入（[【跳转到 31:45】](https://www.youtube.com/watch?v=9zFnXwpbHyc&t=1905)）。更深一层：这些指标本就是概率——**结构是个概率，结合界面是概率的概率**，一层层下来，离真实生化越来越远。未来除了可开发性评分，也许还要给出"可能性区间"的概率分。

### 6.4 mini binder 能期待什么亲和力

面对"用 BindCraft 和 BoltzGen 跑 mini binder campaign，能期待什么亲和力"的高频问题，Joseph 的答案很冷静（[【跳转到 33:50】](https://www.youtube.com/watch?v=9zFnXwpbHyc&t=2030)）：按抗原、按表位算的成功率都千差万别——连"能不能结合"都高度可变；近两年论文总高亮"皮摩尔/纳摩尔 binder"，但其余大多结合并不强。A-alpha 的立场是**数据驱动：全部实测**。实践中，mini binder 常能到**亚纳摩尔至 10~100 纳摩尔**区间；抗体似乎能推得更远，但真的需要精调优化（AlphaBind 之类的亲和力成熟方法）。想继续往下推，就变成"**最后一 10%**"的优化问题——也许正是最难的那 10%。

![mini binder 亲和力期望：亚纳摩尔到 10~100 纳摩尔，变数很大，全靠实测](assets/Confidence%20Scores%20Don't%20Predict%20Affinity：%20Negative%20Data%20and%20AlphaSeq（A-alpha%20Bio）/02055.webp)

## 七、hit 的定义与行业基准

### 7.1 "黏住一切"的假阳性

Natasha 的一点提醒值得放大：报告 hit/no-hit 时往往只关心"是否结合目标"，但**造一个"黏住一切"的蛋白太容易了**——不测 off-target，它看着像好 binder，其实什么靶都结合，包括所有你不想要的（[【跳转到 36:20】](https://www.youtube.com/watch?v=9zFnXwpbHyc&t=2180)）。所以"什么才算真正的、on-target 的 hit"是个精细的舞蹈：不只是结合你该结合的，还要确保**不以相近的特异性程度结合其他任何东西**（[【跳转到 42:34】](https://www.youtube.com/watch?v=9zFnXwpbHyc&t=2554)）。

![假阳性警示：不测 off-target，"黏住一切"的蛋白也会被当成好 binder](assets/Confidence%20Scores%20Don't%20Predict%20Affinity：%20Negative%20Data%20and%20AlphaSeq（A-alpha%20Bio）/02180.webp)

### 7.2 一锅审问与交叉反应：VH72 的例子

很多人设计完直接"无细胞表达+BLI"——但走那条路，就错失了用展示平台看**非特异结合**的机会：一锅（one-pot）实验里高通量同时审问不同蛋白（[【跳转到 36:45】](https://www.youtube.com/watch?v=9zFnXwpbHyc&t=2205)）。反过来也有人想要交叉反应：治疗分子进临床前要用其他哺乳动物做临床前实验，希望同一分子通吃同源蛋白。Joseph 的回答：带这类信息的数据集极少；新冠里研究得最透——比如 **VH72 最初是为 SARS-CoV-1 的 RBD 设计的，但对 SARS-CoV-2 也有效**，他们为两者都做过优化 campaign（[【跳转到 38:00】](https://www.youtube.com/watch?v=9zFnXwpbHyc&t=2280)）。一个 binder 若能结合某个直系同源物，大概率也能结合另一个——只要有信号，就能开始"走出"两头通吃的设计；AlphaSeq 的规模正好支持"横跨动物园"式的训练（[【跳转到 38:25】](https://www.youtube.com/watch?v=9zFnXwpbHyc&t=2305)）。

### 7.3 SAbDab 矩阵验证实验

Joseph 最喜欢的验证实验之一（已写在博客上）：把一大组已知复合物的 VH-抗原对（源自 SAbDab 数据）**全部丢进一次 AlphaSeq 测个遍**。结果是一个矩阵：对角线全是 on-target 相互作用，非对角线全是 off-target；非对角线上大多很弱——充分优化的抗体-抗原对之间基本看不到结合——但也确实冒出意料之外的交叉反应与宽非特异性（[【跳转到 40:29】](https://www.youtube.com/watch?v=9zFnXwpbHyc&t=2429)）。在做 de novo 设计的 campaign 里，"黏住一切"的候选会被挑出来标记为**负面样本**教模型：别这样。

![SAbDab 矩阵实验：对角线 on-target、非对角线 off-target 的全景验证](assets/Confidence%20Scores%20Don't%20Predict%20Affinity：%20Negative%20Data%20and%20AlphaSeq（A-alpha%20Bio）/02429.webp)

### 7.4 数据量级与"连我们自己都没想到"

这些数据集常常**百万级以上**，聚合后远超百万。有时让人抓狂："这明明是 off-target，可这两个抗原明明是直系同源"——遇到这种独特案例就深挖。Leo 还提到一篇药企论文：把已上市或临床期抗体拿去测**多特异性（polyspecificity）**，结果出人意料——这么靠后的候选竟然也有（[【跳转到 42:59】](https://www.youtube.com/watch?v=9zFnXwpbHyc&t=2579)）。令人鼓舞的是：拿 SAbDab 等库里充分验证的分子，A-alpha 能在内部复现数据、确认其合理特异（排除直系同源等）。

### 7.5 模型对打与今夏的公开 benchmark

规模带来的独特能力：**让 de novo 模型互相对打**——用六个模型各生成几百个设计、对着一批抗原，在一个实验、一个 batch 里测完，所有模型的交叉反应性一览无余（"晾晒脏衣服"）：哪个模型爱产非特异 binder、哪种序列生成方法爱产非特异 binder，方法学上一目了然（[【跳转到 43:24】](https://www.youtube.com/watch?v=9zFnXwpbHyc&t=2604)）。Michael 预告：**今年夏天 A-alpha 将发布公开基准（benchmark）**——建模者提交设计、统一评估，配合标准化 playbook，让大家能问"这个应用、这个表位，我该用哪个工具"，缩短 lead time（[【跳转到 44:39】](https://www.youtube.com/watch?v=9zFnXwpbHyc&t=2679)）。

![模型对打：一个 batch 里晾出所有模型的交叉反应"脏衣服"](assets/Confidence%20Scores%20Don't%20Predict%20Affinity：%20Negative%20Data%20and%20AlphaSeq（A-alpha%20Bio）/02729.webp)

### 7.6 收尾带走的话与 Atlas 联盟

最后每人一句"明天成为更好的蛋白设计师"：Michael——**观点多样性**，别把某一个指标当"统治一切的指标"，电荷、疏水性等生物物理性质要整体地看（[【跳转到 46:44】](https://www.youtube.com/watch?v=9zFnXwpbHyc&t=2804)）；Natasha——**集体讨论**，把"什么才算真正好"摆到明面上、贡献数据集与模型，"科学里所有好事都来自集体交流"；Joseph——**集体地生成数据**才是前进之路，无论形式。A-alpha 即将发布 **Atlas** 数据目录生态，还有一个成员联盟（consortia）集体设计数据集、成员间互相可见（[【跳转到 49:14】](https://www.youtube.com/watch?v=9zFnXwpbHyc&t=2954)）。

## 小结

- **AlphaSeq**：库对库酵母展示，一次实验定量测数百万个 PPI；定位是"赋能数据层"，模型与实验两种语言都要会说。
- **阴性数据是模型缺失的另一半**：PDB 只有阳性（不结合的晶体不存在）；hard negatives（看似该结合却没结合）把设计问题变成监督学习问题。
- **负样本要平衡**：太多会把模型变成"悲观主义者"；失败还要标注类型（非特异 vs 折叠但不结合）。
- **ML 管线 80/20**：算法只占 20%，80% 在把数据整成可学的形态；PPI 至少两条序列；直接亲和力难建模时可转相对亲和力。
- **AbOpt 优化管线**：浅层编辑画局部亲和力地形 → 微调 → "跑到崩为止"（走出 10~20 个突变仍保留结合）；之后再攻免疫原性、Tm、交叉反应。
- **SEPIA**：给抗体设计 de novo 表位（反转向），用准结构 + AlphaSeq 验证生成带标注的正负数据；训出的过滤器优于标准过滤器。
- **confidence ≠ biophysics**：置信分只回答"结构是否成立"；结合与否必须正交测量——结构是概率、界面是概率的概率。
- **亲和力期望要实测**：mini binder 常见亚纳摩尔~10-100 nM，个体差异极大；"最后一 10%"最难。
- **hit 的定义**：结合目标 ≠ hit——还要求不以相近特异性结合其他一切；SAbDab 矩阵实验是现成的特异性验证范式。
- **行业走向**：模型对打、公开 benchmark（今夏）、Atlas 数据联盟——集体生成数据是北极星。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| AlphaSeq | A-alpha Bio 的库对库酵母展示平台，一次实验定量测数百万个 PPI |
| 库对库（library-on-library） | binder 库与靶标库两两相遇的大规模筛选格式 |
| 阴性/负向数据 | 实测"不结合"或失败的数据；PDB 类数据库中几乎缺失 |
| hard negative | 决策边界上"看似该结合却没结合"的样本，监督学习的重点教材 |
| 准结构（pseudostructure） | 计算设计、未必有实验解析、但已实验验证（结合与否）的结构 |
| AlphaBind | A-alpha 发布的抗体-抗原互作数据集（750 万条）与优化方法体系 |
| AbOpt | A-alpha 的抗体优化管线：浅层编辑地形 + 微调 + 优化 |
| shallow edits | 单突变及少量双/三突变，用于绘制局部亲和力地形 |
| 相对亲和力 | 与母本相比的改善幅度；规避"不结合/强结合"双峰难建模的问题 |
| 可开发性（developability） | 成药性质的总称：免疫原性、热稳定性（Tm）、聚集、特异性行 |
| 多特异性（polyspecificity） | 一个抗体结合多种不相关抗原的倾向，是隐性风险 |
| anti-idiotype（抗独特型） | 针对抗体可变区（独特型）的结合剂；SEPIA 反转向的类比 |
| one-pot 一锅实验 | 一个孔/一次实验里同时审问多对相互作用的高通量格式 |
| SAbDab | 结构抗体数据库（牛津）；含抗体-抗原复合物结构 |
| VH72 | 新冠研究中跨 SARS-CoV-1/2 起效的 VH 家族抗体案例 |
| Atlas | A-alpha 即将发布的数据目录生态与成员联盟（consortia） |
