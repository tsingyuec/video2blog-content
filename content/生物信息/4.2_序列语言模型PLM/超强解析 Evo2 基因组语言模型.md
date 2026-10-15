# 超强解析 Evo2 基因组语言模型

> 来源：[超强解析 Evo2 基因组语言模型](https://www.bilibili.com/video/BV1NU93YEEGK/)（Bilibili，钟博子韬，约 89 分钟直播讲座）。本博客由视频演说图文稿整理而成，内容可核查。
>
> 注：本条目还包含 LOGOS（统一科学语法）部分；因 B 站 / YouTube 均未检索到讲解该模型的合适视频，本文仅覆盖 Evo 2。

## 本讲要解决的核心问题（SCQA）

**背景**：蛋白质语言模型（如 ESM 系列）已经把「序列即语言」这条路走通了——在海量蛋白序列上自监督预训练，学到有用的表征和数据分布，进而能做功能预测、突变预测、蛋白生成。

**冲突**：但蛋白质只是生命的一小部分。讲者引用一句话：蛋白质并不算 formally alive（正式意义上的"活的"）——想学基因簇、物种进化、细胞分化、代谢通路，甚至设计一个人工合成的细胞，蛋白模型都无能为力；而且蛋白数据本身也开始"不够用"了。 [【跳转到 07:31】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=451)

**疑问**：能不能让 AI 直接把 DNA 当语言来学？毕竟在中心法则里 DNA 处在最上游——一个 DNA 模型理论上能同时覆盖 DNA、RNA、蛋白三层信息。 [【跳转到 08:40】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=520)

**回答（中心思想）**：可以。Arc Institute 的 **Evo 2** 就是这样一个「DNA GPT」：400 亿参数、近 10 万亿核苷酸上预训练、**100 万碱基**的超长上下文，用 GPT 式的"下一个碱基预测"（next-token prediction）建模所有生命域的基因组。它能给突变打分（连"ATG 起始密码子不能突变"这种生物学常识都对得上）、能按 prompt 生成基因和线粒体基因组、甚至用染色质可及性当"摩斯电码"把自己的名字写进基因组。但讲者也反复提醒：它在突变预测上仍打不过 AlphaMissense 这类蛋白模型，在结构预测上打不过 AlphaFold，而且它更像一只"拷贝猫"——生成的东西很像天然序列，离真正的 de novo（从头）设计还有距离。

## 一、什么是"基础模型"：一个 3A 模型

### 1.1 NVIDIA 的定义

讲座从概念铺起：foundation model（基础模型）的定义其实一直比较模糊，讲者摘了 NVIDIA 博客里的一句话——**foundation model 是一种在海量数据上做无监督学习训练、并且能被适配去完成广泛任务的神经网络**。 [【跳转到 00:47】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=47)

![NVIDIA 对 foundation model 的定义幻灯片](assets/超强解析%20Evo2%20基因组语言模型/00047.webp)

例子随手可举：ChatGPT、Grok、Llama，以及国内的 DeepSeek、通义千问、Kimi，某种程度上都能算 foundation model。

### 1.2 更好记的类比：3A 模型

讲者给了个通俗类比：游戏圈有"3A 游戏"（大投入、大制作、大体量），foundation model 就是 **3A 模型**——用了 a lot of data（大量数据）、a lot of parameters（大量参数）、还能做 a lot of tasks（大量任务）。 [【跳转到 01:37】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=97)

## 二、生物学的 foundation model：按"吃什么数据"分类

### 2.1 三类数据来源

给生物学基础模型分类，最方便的维度就是**训练数据是什么**： [【跳转到 02:07】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=127)

1. **纯文本**（比如科研论文）训练的模型——目前还没有真正投入应用；
2. **蛋白质序列**当文本训练——之前的主流方案，代表是 Meta 的 ESM 系列及其后继公司 EvolutionaryScale；
3. **DNA 序列**——今天的主角 Evo / Evo 2 就是这一类的佼佼者。 [【跳转到 02:57】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=177)

### 2.2 蛋白模型内部也分好几派

![生物学大模型的一张分类表](assets/超强解析%20Evo2%20基因组语言模型/00214.webp)

蛋白模型虽多，核心都没跳出蛋白（序列或结构）数据的范围：结构预测（AlphaFold 2/3、ESMFold）、序列表征（ESM）、蛋白生成（像"蛋白质的 GPT"ProGen）、序列+结构联合（Prost、ESM 3）、从结构到序列的条件生成（ESM 3、ProteinMPNN）、序列与结构共设计（RFdiffusion）…… [【跳转到 03:34】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=214)

不过讲者用一句打油诗概括了它们的价值差异：**蛋白大模型的价值总共一石，AlphaFold 独占八斗**——其他模型的应用多围绕 ESM 展开，很少有像 AlphaFold 那样明确而广泛的影响力。 [【跳转到 04:24】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=264)

### 2.3 蛋白模型学到了两样东西

蛋白质大模型能做功能预测、蛋白生成、突变预测、结构预测，本质上都围绕两个点： [【跳转到 05:05】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=305)

- **有意义的表征（meaningful representation）**：相似功能的蛋白有相似的表征、相似结构的蛋白有相似的表征，结构相似的局部片段也有相似的表征；
- **数据分布（data distribution / pattern recognition）**：学到所有蛋白的分布就能生成蛋白；学到某个功能家族的分布就能生成该家族的蛋白；学到某一位点的分布就能指导突变设计；学到氨基酸两两之间的联合分布（joint distribution），就能判断哪两个氨基酸空间距离近——这正是进化上的**共进化（co-evolution）**信号。 [【跳转到 06:20】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=380)

### 2.4 做不了的事：一切需要"活"系统的任务

蛋白质的局限就是蛋白模型的局限。讲者引用："Proteins are organic molecules……not formally alive in any sense of the word"——蛋白质是死的、不是活的。所以当一个任务需要多个蛋白、需要整个生命体的复杂交互时，蛋白模型就很难独立完成： [【跳转到 07:31】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=451)

- 学习 gene cluster（基因簇）；
- 学习整个物种的进化；
- 学习细胞分化；
- 学习细胞内的代谢通路（metabolic pathway）；
- 设计一个全新的人工合成细胞。 [【跳转到 07:56】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=476)

## 三、为什么轮到 DNA：中心法则给了它"全权"

### 3.1 DNA 模型 = 跨尺度统一信息

很多科学家把目光投向基因组序列——数据集从 protein sequence 换成 genome sequence。依据正是中心法则（central dogma）：**DNA 里已经编码了 RNA 的信息和蛋白质的信息**。 [【跳转到 08:15】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=495)

所以一个 DNA 模型理论上能 unify information across multiple scales（跨尺度统一信息）——同时覆盖 DNA、RNA、蛋白三层；能捕捉系统层面的相互作用（system-wide interactions），也就更有可能设计更复杂的体系（sophisticated functions）。 [【跳转到 08:40】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=520)

### 3.2 两大难点之一：context length（上下文长度）

蛋白很短：真核蛋白平均约 400 个氨基酸，细菌 300 多，古菌只有 200 多，1000 个氨基酸对 Transformer 轻轻松松。DNA 完全不是一回事： [【跳转到 09:05】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=545)

- 只看编码序列（coding sequence），平均长度就将近 1000 个碱基；
- 长一点的基因可达 3000、5000 以上；
- 更复杂的是调控元件：增强子、激活子与它们的目标基因之间的距离可以达到 **100 万碱基**的量级。 [【跳转到 09:55】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=595)

摄影圈说"底大一级压死人"，DNA 模型里就是**"读长大一级压死人"**。 [【跳转到 10:20】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=620)

### 3.3 两大难点之二：tokenization（怎么切 token）

一个碱基算一个 token？三个碱基（正好一个密码子）？还是六个碱基？ [【跳转到 10:20】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=620)

- **6 碱基一个 token**：很大程度上是为了"妥协读长不够"——很多 Transformer 撑不到百万量级的上下文；
- **3 碱基一个 token**：符合密码子长度，有生物学合理性，但跟启动子这些非编码元件就对不上了；
- **1 碱基一个 token**：主流做法，但要付出更多计算消耗。 [【跳转到 10:45】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=645)

此外，DNA 模型还能做更多样的任务：判断序列来自原核还是真核、找调控序列等等。 [【跳转到 11:10】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=670)

## 四、"DNA GPT"能干什么：打分与生成

如果真有了一个用 DNA 训练的 ChatGPT——你能用 DNA 序列跟它"对话"——它能做什么？讲者自己 brainstorm 了一轮，所有能力都围绕两件事： [【跳转到 11:30】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=690)

### 4.1 打分：判断序列"合不合理"

GPT 能判断一句话像不像人话，DNA GPT 就能判断一段序列像不像"合理的 DNA"。对应的应用包括： [【跳转到 12:20】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=740)

- 给蛋白编码序列的突变打分、给调控序列打分；
- 找出基因组里哪些部分是"必需的"（突变了影响很大）、哪些部分"可有可无"；
- 给不同密码子打分；评判某个启动子适不适配后面的序列；
- 学习基因与基因之间的相关性、增强子与基因之间的相关性。 [【跳转到 13:10】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=790)

### 4.2 生成：从新基因到紧凑基因组

- 生成一个新基因、新的多基因基因簇；
- 给目标蛋白生成启动子——启动子也是 DNA；
- 物种迁移：把人类蛋白的序列"翻译"成 E. coli 风格——模型知道人类基因长什么样、大肠杆菌的基因排布又是什么样； [【跳转到 13:35】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=815)
- 甚至生成一整条基因组，把"没用的部分"全部删掉，造一个紧凑（compact）的基因组。

## 五、Evo 团队是谁：Arc Institute 与它的"八卦"

### 5.1 两位创始人

Evo 系列的核心发起人两位：**Brian Hie** 与 **Patrick Hsu**。 [【跳转到 19:35】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=1175)

- **Patrick Hsu**：这位华人帅哥是张锋（就是做 CRISPR-Cas9 那位）实验室的博士，做过很多 CRISPR 相关工作，之后在 Editas 待过一年，去 Salk Institute 做过 PI，如今是 UC Berkeley 的 PI；
- **Brian Hie**：出自 MIT Bonnie Berger 实验室，计算生物学背景，曾加入 Meta 参与 ESM 系列模型（ESM 相关论文里能看到他的名字），如今是 Stanford 的 PI。 [【跳转到 20:25】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=1225)

两人虽然分属 Stanford 和 UC Berkeley，但同属一个机构——**Arc Institute**。讲者还分享了一个科研圈小段子：一位很出名的 billionaire 跟一位知名女科学家结了婚，捐了很多钱专门建了个研究所、让她当 PI 不用再愁经费——这个研究所就是 Arc Institute。 [【跳转到 20:50】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=1250)

### 5.2 Evo 系列时间线

![Evo 系列模型时间线与团队背景](assets/超强解析%20Evo2%20基因组语言模型/01275.webp)

- **HyenaDNA**（NeurIPS 2023 spotlight）：Evo 团队前身成员的工作，只有 6.6M 参数，但靠 Hyena 架构做到了 100 万碱基的上下文；
- **Evo 1**（Science 2024）：一作 Eric Nguyen，数据只有原核生物，7B/40B 级别的大模型；预印本更早；
- **Evo 1.5**：中间版本；
- **Evo 2**（2025）：今天的正主——数据集从原核扩展到**原核 + 真核**（multi-species）。 [【跳转到 22:30】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=1350)

讲者评价：Evo 1 → Evo 2 最大的变化在数据集，架构从 StripedHyena 1 到 StripedHyena 2 在他个人看来没有特别大的变化。 [【跳转到 22:55】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=1375)

## 六、Evo 2 两大亮点：100 万上下文 + 多物种数据

### 6.1 100 万碱基能"罩住"什么

![Evo 2 的训练流程、长上下文覆盖范围与 StripedHyena 2 架构](assets/超强解析%20Evo2%20基因组语言模型/01400.webp)

100 万碱基的上下文是什么概念？它能覆盖： [【跳转到 23:20】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=1400)

- 真核基因的全长、细菌基因；
- 非编码 RNA、操纵子（operon）；
- 完整的线粒体基因组（细胞器基因组）；
- 整个噬菌体基因组（约 10⁵ 碱基量级）；
- 完整的真核基因、完整的酵母染色体；
- 以及 Human TAD（讲者坦言自己对 TAD 不太熟）。

一句话：如果两个元件在 100 万碱基的范围内有互作，Evo 2 理论上有机会"看见"。 [【跳转到 23:45】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=1425)

### 6.2 StripedHyena 2：不是 attention 的架构

Evo 2 用的是 **StripedHyena 2** 架构——不是 Transformer 的 attention 路线，可以类比最近很热门的 Mamba 架构。Hyena/Mamba 这类架构天生能适应长读长，这正是 DNA 建模最需要的。 [【跳转到 21:40】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=1300)

具体改动：把原架构中的一部分 long convolution 换成三种层的混合——SE（short explicit）、MR（medium regularized）、LI（long implicit），Evo 1 里全黄的层在 Evo 2 里变成黄绿蓝混着用。讲者直言"我个人不是很能判断这到底有多大用"，感兴趣的同学去看原文。 [【跳转到 33:13】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=3313)

Scaling 表现倒是很硬核：Evo 2 的 perplexity 随训练稳定下降，40B 且 context 最长的模型达到了 **2.5**（Evo 1 时代还是三点几），7B 模型的 perplexity 则明显更高。 [【跳转到 33:38】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=3338)

### 6.3 大海捞针：长上下文的验收考试

![Evo 2 的 DNA 版大海捞针实验](assets/超强解析%20Evo2%20基因组语言模型/01680.webp)

GPT 圈有个著名的"大海捞针"（needle in a haystack）测试：在一大篇文章里藏一句"我最喜欢的水果是西瓜"，看模型能不能把它捞出来。Evo 2 团队做了一个 DNA 版： [【跳转到 25:55】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=1555)

- **大海（haystack）**：随机生成的 100 万长度随机序列；
- **针（needle）**：其中只埋 100 个碱基的特定序列；
- **任务**：让模型在"读完"100 万长度之后，把这段 100 bp 的 needle 完整还原出来。

注意 Evo 2 并不是为这个任务训练的——它的训练目标只是"预测下一个碱基"，所以团队是给 needle 加扰动、再看模型生成的 100 bp 与扰动的相关性。结果：相关性 score 大于 0.8 的占了绝大多数，而且不管针埋在开头、中间还是结尾都成立。具体的相关性算法（借用了 Sergey Ovchinnikov 团队的方法、用到雅可比矩阵）讲者建议大家读原文。 [【跳转到 28:00】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=1680)

## 七、Evo 2 的四大任务：打分是真的强，生成要打折看

讲者把 Evo 2 论文的工作分成四类任务（他自嘲"其实也就三类"）：突变预测、临床致病突变、蛋白/基因组生成、表观基因组生成。 [【跳转到 28:22】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=1702)

### 7.1 任务一：突变打分——它学会了"生物学常识"

原理很直白：模型既然能生成合理的 DNA，就说明它知道"合理的 DNA 长什么样"。给输入序列加一个随机突变，看 likelihood 是升是降，就能给突变打分，判断它对蛋白（或功能性 RNA）是变好还是变坏。 [【跳转到 28:47】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=1727)

![Evo 2 突变打分与生物学常识的对应](assets/超强解析%20Evo2%20基因组语言模型/01702.webp)

**先看它有没有学到基本生物学概念**（这一段是全场最精彩的部分之一）： [【跳转到 29:37】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=1777)

- **起始密码子不能动**：编码区第一个位置就是 ATG 起始密码子——一个碱基都不能突变，突变了就不是起始密码子了。Evo 2 的打分图谱里，ATG 这三个位置正好是"黄色"（突变后 likelihood 大幅下降）；
- **密码子前两位降分多、第三位降分少**：三联体密码子的第三个位置（摇摆位）突变影响小——这完全符合生物学常识（讲者还留了个"课后作业"：为什么第三位可以突变？建议自己查）；
- **5' UTR 影响不大**：转录起始位点（TSS）前面的一堆序列突变了，打分也不会明显下降； [【跳转到 30:27】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=1827)
- **3' UTR 有分界**：终止密码子三个位置不能突变，终止密码子之后的 3' UTR 又变成可以突变——也符合生物学观念；
- **非编码 RNA 里 rRNA 和 tRNA 最不能动**：它们本身就是有重要功能的 RNA； [【跳转到 31:17】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=1877)
- **编码区看突变类型**：同义突变基本不降分；非同义突变（改变氨基酸）降一部分分；提前出现终止密码子（严重破坏蛋白结构）大幅降分；单个碱基的**删除**降分最狠——毕竟插入删除对序列影响是巨大的。

**再拿到真正的考试里比**：ProteinGym 这类 benchmark 用高通量实验（DMS）实测了大量突变体的功能变化，模型打分与实验排序的相关性就是成绩单。 [【跳转到 32:12】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=1932)

![三大突变打分基准上的结果与讲者的"有趣发现"](assets/超强解析%20Evo2%20基因组语言模型/01982.webp)

结果与讲者的三条"有趣发现"： [【跳转到 33:02】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=1982)

1. **小模型胜过大模型**：细菌蛋白打分上，Evo 2 的 7B 比 40B 更好（ESM 3 也有类似结论，650M 左右可能是"甜点大小"）；
2. **还是打不过蛋白模型**：人类蛋白打分上 Evo 2 比 Evo 1 强不少（Evo 1 没见过人类序列），但仍然不敌 ESM-1v 等蛋白模型；非编码 RNA 是蛋白模型做不了的，Evo 2 在这里领先；
3. **缺了结构模型这条赛道**：ProteinGym 榜单上表现最好的现在大多是蛋白"序列+结构"混合模型，论文只比了纯序列模型。

还有一个计算机背景同学容易忽略的点：**看绝对值**。蛋白区的 correlation 只有 0.4 几、将近 0.5，lncRNA 只有 0.35 出头——真要拿去指导实验设计，成功率没有想象中高。 [【跳转到 34:17】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=2057)

**顺带两件事也能做**：

- **必需基因鉴定**：给基因加提前终止子，看 likelihood 掉多少——掉分不多说明这基因可有可无（nonessential），掉分严重就是必要基因。不过 AUROC 只有 0.65，远不如内含子/外显子那种接近 1.0 的分类；非编码 RNA 的必要性则用 10 个碱基的删除来测（终止密码子可挡不住 RNA 表达）； [【跳转到 37:08】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=2214) [【跳转到 36:49】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=2149)
- **外显子/内含子划分**：加一点监督学习（fine-tune）就能学，比 Nucleotide Transformer 和 Evo 1 都强——但 Evo 1 没见过真核序列，这个对比有点"欺负人"，而且它没跟很多传统方法比。 [【跳转到 36:14】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=2174)

### 7.2 任务二：临床致病突变（ClinVar）

第二类任务还是突变打分，但聚焦"会致病的突变"，对应 benchmark 是 **ClinVar**（收集病人数据、分成 pathogenic 致病 / benign 良性）。这个赛道的现任霸主是约两年前 AlphaFold/Google 团队（合并前）发表的 **AlphaMissense**——一个基于结构做预训练、再在突变预测上做 fine-tune 的模型。 [【跳转到 38:49】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=2329)

![ClinVar 各区域上 Evo 2 与 AlphaMissense、ESM-1b、GPN-MSA 等的对比](assets/超强解析%20Evo2%20基因组语言模型/02404.webp)

结论可以总结成一句话：**AlphaMissense 能做的任务，Evo 2 一般打不过；AlphaMissense 做不了的，Evo 2 才有机会排第一。** [【跳转到 41:19】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=2479)

- 编码区 SNV（单碱基替换）：超过其他 DNA 模型，但明显落后 AlphaMissense 和 ESM-1b；编码区插入删除：AlphaMissense 做不了，Evo 2 排第一；
- 非编码区：蛋白模型都做不了，Evo 2 排在第一二位（不过编码区上 GPN-MSA 仍是更强的 DNA 模型）； [【跳转到 40:04】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=2404)
- 补充数据集：剪接突变 **SpliceVarDB** 上 Evo 2 最好；**BRCA1**（乳腺癌相关）上有不错表现但明显落后 AlphaMissense；只有 non-coding SNV 上 Evo 2 领先——因为 AlphaMissense 干不了这个。 [【跳转到 40:54】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=2454)

### 7.3 任务三：从生成蛋白到生成基因组

蛋白生成不新鲜：Evo 1 当年就生成过全新的 CRISPR-Cas 基因簇和 TnpB 一类短 CRISPR 系统——但那是**微调之后**才靠谱的。Evo 2 模型更大、数据更多，玩法更简单：**prompt 就是目标基因上游约 1500–2000 个碱基的调控序列**，模型"读懂"这段序列之后接的该是什么基因，就往下生成。 [【跳转到 41:49】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=2509)

![蛋白生成任务：prompt 与生成的氨基酸回复率](assets/超强解析%20Evo2%20基因组语言模型/02509.webp)

成绩单：在来自 E. coli、酵母、人类等不同物种的蛋白上，Evo 2 生成序列与野生型的**氨基酸回复率达到 90% 以上**，有些接近 95%、讲者看图甚至"将近 100%"。对比之下，Evo 1 不做微调只有约 30% 的回复率，而且生成的多是 nonsense、garbage 蛋白。配合 AlphaFold 结构预测（结构高度相似、置信度高），"从序列相似度、结构相似度、结构可信度"三个维度看，Evo 2 确实无可争议地生成了对应功能的蛋白——**尽管没有做功能验证**。 [【跳转到 43:29】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=2609)

但讲者马上补了一刀：**相似度太高本身就是 limitation**——你到底要一个"新的"蛋白，还是一个"像的"蛋白？要像的，去隔壁物种找一个不就行了？这就是序列模型绕不过去的"拷贝猫"问题。 [【跳转到 44:44】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=2684)

**基因组生成**则选了个聪明的考题：线粒体基因组（只有 16 KB）。 [【跳转到 45:27】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=2727)

![Evo 2 生成线粒体基因组的结果](assets/超强解析%20Evo2%20基因组语言模型/02727.webp)

- rRNA 数量对了；coding sequence 大概 13 个（有的少了几个）；tRNA 应该是 22 个，生成了 20 或 15 个——接近但不完全等于合理数量； [【跳转到 45:52】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=2752)
- 序列相似度 80–90%，能覆盖 80% 左右的基因；预测出的蛋白结构（比如最大的那个复合物）与野生型"像那么一回事"；基因图谱上虚线框出的野生型基因，它缺了几个； [【跳转到 46:42】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=2802)
- 讲者的两盆冷水：线粒体总共就 13 个基因，缺一两个大概率就不能 work 了；而且 80% 的相似度太高——人和牛的线粒体基因组相似度可能都没这么高，很难承认这是"全新"的线粒体。 [【跳转到 47:07】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=2827)

**全基因组生成**：Evo 2 生成的基因组有约 60% 的基因能在蛋白家族数据库 PFAM 中找到家族，Evo 1 只有 20%——讲者的解读是：Evo 1 那 80% 找不到归属的序列，不是"发现了新家族"，而是"生成了什么都不剩的蛋白"。蛋白长度分布、二级结构分布、结构预测这些指标，都是**必要条件而非充分条件**——只有实验验证才是唯一金标准。 [【跳转到 48:02】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=2882)

### 7.4 任务四：表观基因组生成——给 DNA 写"摩斯电码"

第四个任务是生成**表观基因组（epigenomics）**：染色体上的染色质有时"打开"（accessible，基因可表达）、有时"关闭"（not accessible，基因被包裹着没法表达）。 [【跳转到 50:16】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=3016)

![表观基因组生成的"生成-判别"循环](assets/超强解析%20Evo2%20基因组语言模型/03116.webp)

Evo 2 团队的做法是一个**"生成—判别"循环**： [【跳转到 51:31】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=3091)

1. Evo 2 生成一段 DNA；
2. 判别模型（Enformer 和 Basenji 2）预测这段序列的 promoter accessibility；
3. 符合设计目标的 accept（黑线），不符合的 reject 扔掉；
4. 回到第 1 步，继续迭代。

生物学家可以把这理解成"定向进化"的 AI 版。最有梗的彩蛋：他们用这种"一段开、一段关"的模式把 **Evo 2 自己的名字编码进了基因组序列**——像摩斯电码一样。当然，这些黑线蓝线都只是模型预测，没有实验验证。 [【跳转到 52:21】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=3141)

## 八、吃了多少数据：OpenGenome2

模型开源了训练数据集 **OpenGenome2**。它继承了 OpenGenome 1（GTDB 细菌/古菌基因组 + 噬菌体 + 质粒序列）并做了更新，核心增量是**加了真核生物的序列**： [【跳转到 53:00】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=3180)

- 真核生物：NCBI 上 1 万多个基因组；
- 宏基因组：NCBI、JGI、MGNIFY、MG-RAST 等来源；
- 细胞器基因组：NCBI 里 3 万多个（线粒体、叶绿体、质体等）；
- mRNA 与大量非编码 RNA 转录序列：Ensembl、Rfam、RNAcentral；
- 真核生物启动子序列。 [【跳转到 53:50】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=3230)

![OpenGenome2 的物种构成：真核碱基远超原核](assets/超强解析%20Evo2%20基因组语言模型/03255.webp)

一个反直觉的事实：**真核基因组的碱基数（约 6.98 T）远超宏基因组和原核基因组**——虽然大家直觉里"蛋白序列都是原核的多"，但真核基因组实在长。病毒、质粒这些只占少数。 [【跳转到 54:15】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=3255)

训练分两段：pretraining（8k context 的 base model）+ midtraining（做 context 扩展），最终有 Evo 2 40B 和 7B 两个底座。 [【跳转到 23:20】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=1400)

## 九、可解释性：给 32768 个通道起名字

论文还加了一段模型可解释性（讲者坦承"我对这个结果还不是非常相信"，所以只简单讲讲）。方法借用 Anthropic（Claude 背后的公司）的 **SAE——稀疏自编码器（sparse autoencoder）**。 [【跳转到 33:53】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=3393)

常规 autoencoder 中间的 embedding 是个瓶颈（比输入小），他们反其道而行：把 4096 维的 embedding **放大 8 倍成 32768 维**，并且让大多数维度为 0（稀疏）。这样一来，原本混杂在一起的 4096 维信号被"摊开"，信息集中到一两个通道上，每个通道就代表一个可命名的概念。 [【跳转到 34:43】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=3443)

![SAE 稀疏自编码器的通道含义示例](assets/超强解析%20Evo2%20基因组语言模型/03493.webp)

讲者举的例子：

- 通道 **13606** = 这段是不是编码序列（open reading frame / ORF）；
- 某通道 = 这段是不是 tRNA；通道 **2812** = 这段是不是 rRNA——把 rRNA 序列喂给模型，2812 通道的信号就"亮"了，非 rRNA 就不亮； [【跳转到 35:18】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=3518)
- 有的通道对应蛋白里的 α helix 片段，通道 **22326** 对应 β sheet；某基因的启动子对应通道 **24019**；
- 猛犸象（woolly mammoth）的序列上，哪段是 coding sequence、哪段是内含子、哪段是外显子起始（带剪切信号）、哪段是外显子结束，都各自对应了某个通道。 [【跳转到 35:43】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=3576)

注意：这不是在解释原来那 4096 维 embedding 里每一维的含义，而是**新训练了一个稀疏表示**再去做解释（通常是原长度的 4–8 倍甚至更高）。Claude 当年用类似方法找出过"景点通道""风景通道""交通工具通道"，算是从语言模型研究里借鉴来的有趣玩法。 [【跳转到 36:01】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=3601)

## 十、讲者的四点冷思考

讲座最后，讲者跳出 Evo 2 本身，对整个序列模型领域抛出了讨论（这里也是本次讲座最有价值的部分之一）： [【跳转到 38:49】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=3876)

![讲者的讨论幻灯片：序列模型的四个追问](assets/超强解析%20Evo2%20基因组语言模型/04026.webp)

### 10.1 最好的序列模型仍然打不过结构模型

> "Sequence models put in all their effort, just to reach the starting point of structure models."（序列模型倾尽全力，也只够到结构模型的起点。）

反例链很扎心：**ESM 3 < ESMFold < AlphaFold**——ESM 3 参数量远超 AlphaFold，结构预测却连 AlphaFold 2 都打不过。而且把蛋白（序列）模型的数据量翻三倍变成 DNA 序列模型，还是打不过结构模型——AlphaMissense 的数据量远小于 Evo 2，突变预测上却稳赢。 [【跳转到 39:26】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=3926)

### 10.2 序列模型是"拷贝猫"（copycat）

很多序列模型本质上是在**复述自然界的序列**：只能创造与自然界序列差不多、符合同一个分布的东西，很难创造全新的（brand new）东西，很难做真正的 de novo design。它创造的蛋白与天然蛋白同属一个家族，甚至结构一模一样——ProGen、Evo 1、Evo 2 生成的都是序列相似度非常高的东西。 [【跳转到 39:51】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=3951)

### 10.3 哪些应用场景是不可替代的？

突变预测、结构预测、蛋白生成、功能预测四类应用，其实都可能被替代：

- 突变预测：ProteinGym 上有个不用深度学习的著名模型 **GEMME**；
- 结构预测：明显不如 AlphaFold（MSA 路线）；
- 蛋白生成：不如 ProteinMPNN 这类结构（逆折叠）模型；
- 功能预测：主流靠序列相似度（BLAST、HMMER），结构相似度才是更好的标准，CLEAN 这类模型还有可解释性问题。 [【跳转到 40:26】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=4026)

### 10.4 除了进化和结构，它还学到了什么？

讲者最后留了个开放式问题：序列模型除了进化和结构信息之外，到底还学到了什么？他现在没有看到任何一篇文章能回答——这是个很值得讨论的点。 [【跳转到 40:51】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=4076)

（讲者也顺带交代了自己的知识边界：熟悉蛋白结构/预测/语言模型/设计，不懂单细胞生物学、表观基因组学、细胞生物学和衰老——相关讨论他答不了。） [【跳转到 41:01】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=4101)

## 十一、QA 环节精华

最后 40 分钟的问答里，有几个问题值得记录： [【跳转到 41:38】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=4138)

- **打分会受训练数据影响吗？**肯定受。但 ProteinGym、ClinVar 都有实验/临床金标准兜底；Evo 1 没见过人类序列所以人类突变打分很差，Evo 2 见过就好得多。另外打分低 ≠ 有害——有害是要实验验证的。 [【跳转到 44:12】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=4412)
- **生成是"抄作业"吗？**"它的训练损失函数就是抄作业"——讲者承认序列到序列的生成本质上就是在学"自然界这里后面接什么"。
- **Evo 2 能在线用吗？**有官网可以试突变打分；本地部署要求很高——A100 不行，得多卡 H100（弹幕补充：推理 7B 也要 15G+ 显存）。 [【跳转到 45:52】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=4552)
- **密码子表不止一种怎么办？**讲者知道，文章也知道：补充材料里有不同物种不同密码子表（包括非经典 ATG 起始密码子）的分析。 [【跳转到 46:02】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=4602)
- **训练数据用的 GRCh38 还是泛基因组？**用了 GRCh38（在 NCBI reference genome 里）。Enformer 和 Basenji 都是 Kelley 参与做的。 [【跳转到 47:26】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=4746)
- **物种分布偏差 / 去重？**肯定存在（有的物种很多、有的只有一两个）；他们做了比较简单的去重，没考虑物种关系等复杂因素，去重方法本身"怎么做比较讲究"。 [【跳转到 47:57】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=4757)
- **只研究酵母，用酵母基因组专门训一个更好吗？**不一定——酵母数据可能根本喂不饱这么大的模型。 [【跳转到 47:41】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=4741)
- **会出 Evo 3 吗？**"我猜会，但最简单的办法是去问 Brian 老哥，他人很好。"
- **Evo 2 能做 PPI（蛋白互作）预测吗？**基因组里肯定包含基因互作的信息，尽管文章没做，理论上可以从里面挖。 [【跳转到 52:10】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=5210)
- **Hyena 架构的优势到底在哪？**attention 架构"能 work"但算力需求大；Hyena 这类架构天生适合长上下文、能用很少的算力做超长读长——可以参考 Mamba 与 attention 的区别。 [【跳转到 52:60】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=5260)

结尾还有一首仿《沁园春》的打油诗，回应"Evo 2 是生物学界的 DeepSeek"的说法："惜 DeepSeek，空有文藻；序列巧匠，别有匠人。一代天骄 AlphaFold，唯会结构，管中窥豹。俱往矣，问生命之谜，还看今朝。" [【跳转到 41:38】](https://www.bilibili.com/video/BV1NU93YEEGK/?t=4138)

## 小结

- **Evo 2 = "DNA GPT"**：40B 参数、近 10 万亿核苷酸、100 万碱基上下文，用 next-token prediction 建模原核 + 真核的全生命域基因组；架构是不同于 attention 的 StripedHyena 2（可类比 Mamba）。
- **打分能力扎实**：突变打分对上了起始密码子、密码子第三位、UTR、同义/非同义突变、rRNA/tRNA 等一整套"生物学常识"；非编码区是它相对蛋白模型的主场（但绝对相关系数 0.35–0.5，别指望直接拿来指导实验）。
- **临床赛道有天花板**：一句话——AlphaMissense 能做的它打不过，AlphaMissense 不能做的（非编码、插入删除）它才有机会第一。
- **生成是"像"不是"新"**：氨基酸回复率 90%+ 的"很像"蛋白、缺了几个基因的线粒体基因组、60% 基因能归入 PFAM 家族——但高相似度本身限制了 de novo 设计。
- **可解释性有亮色**：SAE 把 embedding 摊成 32768 个稀疏通道，ORF、rRNA、tRNA、β sheet、启动子各归其位。
- **冷思考**：最好的序列模型仍打不过结构模型；序列模型是"拷贝猫"；不可替代的应用场景存疑；"除了进化和结构还学到了什么"仍是悬而未决的问题。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| foundation model（基础模型） | 海量数据上无监督预训练、能适配大量下游任务的大模型；讲者的"3A 模型"类比 |
| next-token prediction（NTP） | GPT 式训练目标：预测下一个 token；Evo 2 里即"预测下一个碱基" |
| masked language model（MLM） | BERT 式训练目标：遮住一部分再预测；Nucleotide Transformer、DNABERT 属于这类 |
| context length（读长/上下文长度） | 模型一次能"看到"的序列长度；DNA 建模的生死线，"读长大一级压死人" |
| tokenization | 一个 token 代表几个碱基：1 nt（主流）/ 3 nt（密码子）/ 6 nt（妥协读长） |
| StripedHyena | Evo 系列的非 attention 架构，天生适合长上下文，可类比 Mamba |
| needle in a haystack（大海捞针） | 在超长序列里埋一小段"针"，考察模型能否还原——长上下文的验收考试 |
| zero-shot likelihood 打分 | 不经微调，直接用模型对突变前后的似然变化给突变打分 |
| ProteinGym / DMS | 高通量突变实验构建的突变效应预测基准 |
| ClinVar | 收集致病（pathogenic）/良性（benign）临床突变的数据库与基准 |
| AlphaMissense | AlphaFold/Google 团队的致病突变预测模型，临床赛道的现任霸主 |
| GPN-MSA | 多序列比对（MSA）加持的 DNA 模型，编码区 ClinVar 上仍强于 Evo 2 |
| SAE（稀疏自编码器） | 把 embedding 放大成稀疏高维、让每个通道对应一个可命名概念的可解释性方法 |
| PFAM | 蛋白质家族数据库；基因组生成质量的"归属率"指标 |
| promoter accessibility | 染色质可及性——表观基因组生成任务的优化目标 |
| copycat（拷贝猫） | 讲者对序列模型的批评：复述自然界分布，难做真正的 de novo 设计 |
