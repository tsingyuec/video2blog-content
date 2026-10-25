# What is a virtual cell? Biohub's $1.8 billion data push, and the AI models it is for

## 所用视频

- 标题：**What is a virtual cell? Biohub's $1.8 billion data push, and the AI models it is for**
- 平台与视频 ID：YouTube `2-Ou1BLkpQQ`
- 时长：20:47
- 字幕：中文自动字幕
- [视频链接](https://www.youtube.com/watch?v=2-Ou1BLkpQQ)

## 视频主线

这篇视频从 10 月 7 日 Biohub 联合美国能源部、NIH 以及 Google DeepMind、Isomorphic Labs、Meta 投入 18 亿美元的新闻切入，先问“虚拟细胞是什么、需要什么、Biohub 在建什么”。讲者随后按这条线展开：细胞为什么难建模、AI 虚拟细胞如何组织输入输出与三项能力、Perturb-seq 怎样提供“扰动—响应”数据，以及 2025 年的基准为什么给基础模型泼冷水。再往后，他回到 Biohub 的开放数据与测量工具计划，用哥伦比亚大学的肿瘤案例说明“计算预测—湿实验验证”的闭环，最后逐一回答开头的问题。

## 一、新闻由头：18 亿美元投的是“让 AI 能用的生物数据”

10 月 7 日，Biohub 宣布大幅扩大一项国际合作，目标是产生并开放预测式 AI 生物模型所需要的资料。合作方包括美国能源部、美国国家卫生研究院，以及新的出资伙伴 Google DeepMind、Isomorphic Labs 和 Meta；合计投入 **18 亿美元**，用于经费、数据、运算以及新的测量技术。新闻稿说，这是到目前为止为了产生可供 AI 使用的生物数据，规模最大的一次协同投入。[【跳转到 00:00】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=0) [【跳转到 00:25】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=25)

具体分工是：能源部将在五年内投入超过 **5 亿美元**，用于实验室测量、建模和运算；国家卫生研究院会整合先前联邦投入超过 5 亿美元所建立的资料集与知识库；Google DeepMind、Isomorphic Labs 和 Meta 合计投入 **3 亿美元**，支持 Biohub 的虚拟生物学计划。[【跳转到 00:25】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=25) [【跳转到 00:50】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=50) [【跳转到 01:15】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=75)

Biohub 的科学主管 Alex Rives 说，建立虚拟细胞是下一个科学时代最重要的挑战之一。讲者随即把问题拆成三个：虚拟细胞是什么？它需要什么？Biohub 又在建造什么？[【跳转到 01:15】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=75)

## 二、细胞是动态适应系统：有些方面很稳健，有些一个点突变就推向疾病

细胞是生命的基本单位，也非常难以建立模型。[【跳转到 01:40】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=100) Bunne 和同事把每个细胞描述成一个动态、会适应的系统：复杂的行为来自数量庞大的分子交互作用。细胞有些方面非常稳健，即使基因被移除或被换成其他物种的版本，这些方面也能维持；另一些方面则很敏感，一个点突变或一个外在因素就可能把细胞推向疾病。[【跳转到 01:46】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=106) [【跳转到 02:11】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=131)

为了理解细胞，科学家一直尝试建立虚拟细胞。Bunne 和同事把虚拟细胞定义为一种**运算模型，用来模拟细胞的生物功能与交互作用**。[【跳转到 02:11】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=131)

## 三、旧模型靠规则加参数，难同时覆盖原子到组织、海量组分与非线性

现有的细胞模型大多以规则为基础：研究者把对机制的假设和由数据拟合出来的参数结合起来，使用微分方程、随机模拟或代理人基模型。[【跳转到 02:32】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=152) [【跳转到 02:51】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=171)

作者指出三项挑战：细胞在许多空间与时间尺度上运作，从原子一直到组织；细胞含有数量庞大、彼此交互作用的组分；大部分过程又是非线性的，所以输入的一点小变化可能造成复杂的输出变化。[【跳转到 02:56】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=176) [【跳转到 03:06】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=186) 如果模型有用，研究人员就能在电脑上做一些实验；这些实验在实验室里不是成本太高，就是根本做不到。[【跳转到 03:18】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=198)

第一个全细胞模型出现在 2012 年，涵盖一种细菌已知的全部 **482 个基因与分子功能**。从那以后，科学家也为其他细菌建立了全基因组模型，包括大肠杆菌；但作者说，这些方法仍然无法掌握许多面向，不论是在细菌还是人类细胞这类更复杂的系统。[【跳转到 03:18】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=198) [【跳转到 03:43】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=223)

## 四、组学与 AI 两场革命，把路线推向“多尺度多模态”的 AI 虚拟细胞

作者主张，现在有两场革命提供了新的路径：**组学技术**能以越来越大的规模测量细胞，**人工智能**能直接从数据中学习规律。[【跳转到 04:08】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=248) 他们提出的是**人工智能虚拟细胞**：一个多尺度、多模态的大型神经网络，能表示并模拟分子、细胞和组织在各种状态下的行为。[【跳转到 04:16】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=256) [【跳转到 04:21】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=261)

首先是测量数据进来：基因组序列、单细胞 RNA 数据、分子在细胞内的位置，以及细胞在组织中的位置，全都送进同一个基础模型。[【跳转到 04:36】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=276) [【跳转到 04:41】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=281)

## 五、输出先有三层表示，再叠上“虚拟仪器”：解码器与操纵器

输出的是三个尺度的通用表示：分子、细胞和多细胞。[【跳转到 04:47】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=287) 这里的表示就是**嵌入**（embedding）：把高维、稀疏、带噪声的测量压成一串数字，同时保留数据中有意义的关系。[【跳转到 04:47】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=287) [【跳转到 04:57】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=297)

在分子尺度，DNA、RNA 和蛋白质都能写成由字母组成的序列，适合用最初为语言而发展的方法；细胞尺度把这些分子和它们的数量与位置结合起来；多细胞尺度再加上细胞如何彼此沟通、形成组织。每一个尺度都建立在下一层之上。[【跳转到 05:08】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=308) [【跳转到 05:22】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=322) [【跳转到 05:27】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=327)

![分子、细胞与多细胞三个尺度的通用表示，是虚拟细胞的第一层输出](assets/What is a virtual cell？Biohub's $1.8 billion data push, and the AI models it is for/00287.webp)

在这些表示之上，是**虚拟仪器**，这也是虚拟细胞和普通表征学习的分水岭：以表示作为输入、再产生输出的神经网络——**解码器**把表示转成人看得懂的东西，例如细胞类型的标签或合成的显微镜影像；**操纵器**则把一种表示转成另一种，例如细胞受到扰动之后的状态。[【跳转到 05:33】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=333) [【跳转到 05:38】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=338)

只有表示、没有操纵器，模型能很好分群，却回答不了“敲掉这个基因会怎样”；只有操纵器、没有好表示，预测又容易退化成记住训练集的平均效应。

![操纵器负责“扰动→新状态”，解码器负责“表示→可读输出”](assets/What is a virtual cell？Biohub's $1.8 billion data push, and the AI models it is for/00368.webp)

## 六、讲者把“至少该做到什么”列成三件事，并强调模拟不必完全准确

作者列出这样的模型应该做到的三件事。[【跳转到 05:38】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=338) [【跳转到 06:03】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=363)

**第一，能表示不同物种与条件下的生物状态。** 这听起来像聚类，但目标不同：聚类把已测到的细胞分成若干群；虚拟细胞的表示要能在物种、供体、实验条件之间对齐，为比较和预测提供共同坐标。[【跳转到 06:03】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=363)

**第二，能预测细胞的行为与反应，包括实验室还没测试过的扰动。** 这是最核心、也最容易被高估的一条：它要求模型不仅拟合已见扰动，还要在未见扰动、细胞系、供体上泛化。[【跳转到 06:08】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=368)

**第三，能进行电脑内的模拟实验，指引下一步该收集什么数据。** 这类实验在真实实验室里往往太贵、太慢或做不到。虚拟细胞先筛出最有希望的假设，再让湿实验验证，从而缩小搜索范围。[【跳转到 06:13】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=373) [【跳转到 06:21】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=381)

作者补充说，电脑内的模拟实验不一定总是完全准确，但只要先挑出最有希望的虚拟结果，虚拟细胞就能缩小假说的搜寻范围、降低实验成本。它的价值在排序和缩小假设空间，而不是替代实验。[【跳转到 06:21】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=381) [【跳转到 06:28】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=388)

## 七、Perturb-seq 把“扰动”与“读数”对上，规模的价值在平方级的比较

要预测细胞对改变有什么反应，模型需要有被改变过的细胞当范例。Bunne 和同事说，AI 虚拟细胞应该同时从**刻意施加扰动的数据**以及**没有扰动的数据**中学习；制造这类数据的一种方法是 **Perturb-seq**。Replogle 和同事报告了第一批全基因组规模的 Perturb-seq 筛选，发表于 2022 年。[【跳转到 06:28】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=388) [【跳转到 06:53】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=413)

Perturb-seq 把 CRISPR 扰动与单细胞 RNA 测序接起来：细胞带上 CRISPR 干扰工具和向导 RNA 库，每一个向导都针对单一基因，所以每个细胞都有一个基因被调低；接着，细胞被送进微滴中做单细胞 RNA 定序，所用方法也能捕捉向导 RNA。这样一来，每个细胞的 RNA 表现谱就能对应到被调低的那个基因。[【跳转到 07:18】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=438) [【跳转到 07:23】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=443) [【跳转到 07:34】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=454) [【跳转到 07:39】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=459)

![Perturb-seq 在同一个液滴里同时捕获表达谱和对应的向导 RNA](assets/What is a virtual cell？Biohub's $1.8 billion data push, and the AI models it is for/00459.webp)

作者把这些表现谱分群，归纳扰动所造成的基因表现程式；他们也把扰动本身分群，借此界定每个基因的功能。[【跳转到 07:39】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=459) [【跳转到 07:50】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=470) [【跳转到 07:55】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=475)

在基因组规模上，有一组筛选在 K562 白血病细胞中针对所有有表现的基因；第二组筛选在 K562 和 RPE1 细胞中针对常见的必需基因。过滤之后，作者保留了超过 **250 万个细胞**，每个扰动的细胞数中位数超过 **100 个**。[【跳转到 08:04】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=484) [【跳转到 08:09】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=489)

![过滤后保留超过 250 万个细胞，每个扰动的细胞数中位数超过 100 个](assets/What is a virtual cell？Biohub's $1.8 billion data push, and the AI models it is for/00489.webp)

为什么要做到全基因组规模？作者指出，成本随着扰动的数目成正比增加，但两两比较的数目却随着它的平方增加——扰动越多，能组合出的基因关系越多，大型筛选在依功能归类基因时才真正有用。[【跳转到 08:31】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=511) [【跳转到 08:36】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=516)

Bunne 和同事补充说，细胞的大型参考数据集大约每六个月就增加一倍，而且这些测量现在能搭配系统性的扰动。[【跳转到 08:51】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=531)

## 八、2025 年基准泼冷水：五个基础模型加两个深度学习模型，没有稳定胜过简单基线

有了这样的数据，研究人员已经建立 AI 模型来预测扰动的效果。Ahlmann-Eltze 和同事指出，已有数个基础模型以来自数百万个细胞的单细胞数据训练而成，其中两个，**scGPT** 和 **scFoundation**，宣称能预测基因遭到扰动后基因表现会怎么改变。在 2025 年发表于《自然方法》的论文中，他们把五个基础模型和另外两个深度学习模型，拿来和刻意设计得很简单的基线比较。[【跳转到 09:07】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=547) [【跳转到 09:32】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=572)

两个关键基线是：**“不改变”**，永远预测和未处理的对照组一样的表现；**“相加”**，把两个扰动各自单独的效果加起来，作为这一对扰动的预测。[【跳转到 09:45】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=585) [【跳转到 09:55】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=595)

第一项测试在 K562 细胞中同时打开成对的基因。模型看过全部 100 个单一扰动和一半的成对扰动，再用另一半来测试；依作者的说法，所有模型的预测误差都明显高于“相加”基线。[【跳转到 10:03】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=603) [【跳转到 10:08】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=608) 作者接着问：模型能不能预测基因交互作用，也就是一对扰动产生出人意料的结果？他们报告说，没有任何一个模型比“不改变”基线更好。[【跳转到 10:26】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=626)

第二项测试用的是没看过的单一扰动，资料来自 Replogle 和同事以及 Adamson 和同事。作者报告说，没有任何一个深度学习模型能稳定胜过简单平均预测或线性模型。只有一种方法稳定胜过其他所有方法：一个线性模型，使用以 Replogle 资料预先训练的扰动表示，并用一种细胞株来预测另一种细胞株。作者的结论是：用单细胞图谱资料预先训练，只比随机嵌入好一点点；而用扰动资料预先训练，则能改善预测。[【跳转到 10:26】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=626) [【跳转到 10:51】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=651) [【跳转到 11:02】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=662) [【跳转到 11:27】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=687)

作者推论：他们的简单基线无法表现真实的生物复杂度，但基础模型却没有胜过它们；要得到能推广的细胞状态表示、并预测尚未做过的实验，这个目标仍然难以达成。他们也说明自己的限制：只用了四组资料，并预期严谨的基准测试会帮助这个领域最终成功。[【跳转到 11:32】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=692) [【跳转到 11:57】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=717)

![在受测数据上，五个基础模型与两个深度学习模型并未稳定胜过简单基线](assets/What is a virtual cell？Biohub's $1.8 billion data push, and the AI models it is for/01194.webp)

Bunne 和同事从另一个角度说明了同样的需求：基准测试必须和模型一起不断进步；资料必须涵盖生物学的广度，包括不同的物种和模态，同时要有足够的深度，才能分辨真正的信号和杂讯。[【跳转到 12:04】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=724) [【跳转到 12:16】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=736)

这也解释了为什么“相加”有时反而是很强的基线：数据不足时，线性近似更稳。虚拟细胞的核心难题，未必是模型不够大，而是数据里有没有足够的“扰动—响应”因果信息，以及评测有没有真正模拟湿实验。

## 九、回到 Biohub：18 亿美元建的是开放数据、共通标准和测量工具

现在回到 Biohub。2026 年 4 月宣布的虚拟生物学计划，将协调各机构与各学科的资料产生，目标是建立可供 AI 使用的开放数据集，让生命的预测模型成为可能。[【跳转到 12:27】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=747) Biohub 最初的承诺是 **5 亿美元**：其中 4 亿美元支持新的技术、扩大生物学家能够测量的范围；另外 1 亿美元则资助 Biohub 以外的研究。[【跳转到 12:52】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=772)

新闻稿点出三类技术：**低温电子断层摄影术**，能解析细胞内近原子等级的细节；**显微术**，能对活组织中数百万到数十亿个细胞成像；**工程工具**，能在分子、细胞、组织和整个生物体的层次上建造并扰动生物系统。[【跳转到 13:17】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=797) [【跳转到 13:25】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=805)

这些资料会扩充细胞对各种介入的反应资料，涵盖的细胞类型和条件远比目前研究过的更多；计划也会建立并验证新的技术，让研究细胞和细胞间交互作用的规模更大、速度更快、准确度更高。[【跳转到 13:25】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=805) [【跳转到 13:35】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=815) [【跳转到 13:40】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=820)

能源部带来百亿亿次级的超级电脑、X 光与中子散射、低温电子显微术与断层摄影术，以及遍布国家实验室的自动化实验室。国家卫生研究院则带来国家级的生物医学数据库，以及已经在发展生物图谱和共通资料标准的计划。[【跳转到 13:40】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=820) [【跳转到 13:56】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=836) [【跳转到 14:01】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=841) [【跳转到 14:11】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=851)

也有其他机构加入，协助凝聚科学社群，包括 Allen Institute、Broad Institute、Gladstone Institutes、Human Cell Atlas、Human Protein Atlas 和 Wellcome Sanger Institute；NVIDIA 以加速运算支援这项工作，Renaissance Philanthropy 则协助扩大资料产生的经费。[【跳转到 14:11】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=851) [【跳转到 14:25】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=865) [【跳转到 14:42】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=882)

Biohub 说，它正在建造一个让所有数据集能统一运作的层：共通标准、共通识别码以及单一的存取入口；它也希望围绕这些资源建立科学社群。[【跳转到 14:53】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=893) [【跳转到 15:04】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=904) 这建立在先前的工作之上：Biohub 曾主导 Tabula Sapiens、OpenCell 和 Zebrahub 等计划，也维护社群数据基础设施，包括 CELLxGENE 和 CryoET Data Portal。[【跳转到 15:04】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=904) [【跳转到 15:12】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=912)

Google DeepMind 的 Pushmeet Kohli 说，若没有前所未有规模的开放实验资料，这项挑战就无法解决。国家卫生研究院的 Nicole Kleinstreuer 则谈到，具备足够生物复杂度的通用细胞模型，能预测任何细胞对介入的反应。[【跳转到 15:25】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=925) [【跳转到 15:30】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=930)

![Biohub 计划推进的三类测量技术：低温电子断层摄影、活组织显微成像与工程扰动工具](assets/What is a virtual cell？Biohub's $1.8 billion data push, and the AI models it is for/00805.webp)

![Biohub 要建的是开放、标准化的“细胞如何回应改变”的数据，以及测量这些数据的工具](assets/What is a virtual cell？Biohub's $1.8 billion data push, and the AI models it is for/01218.webp)

## 十、哥伦比亚大学的肿瘤案例：先算再验，把“状态”和“药物”配对

一个相关的例子来自癌症研究。Biohub 和哥伦比亚大学的研究者（包括 Andrea Califano）在 2026 年发表了两篇《自然遗传学》论文；两篇都没有谈到虚拟细胞，但都用运算来预测细胞的行为，再在肿瘤里测试这些预测。[【跳转到 15:55】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=955) [【跳转到 16:00】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=960)

他们的出发点是：肿瘤里细胞以数种分子特性各异的状态并存，不同状态的药物敏感性可能互不重叠，因而可能造成治疗抗药性。为了界定这些状态，团队用 **ARACNe** 和 **VIPER** 算法估计每个细胞中超过 **1,800 个调节蛋白**的活性；主导某个状态的蛋白质，称为这个状态的主调节因子。[【跳转到 16:25】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=985) [【跳转到 16:50】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=1010)

在胰腺癌中，8 月的论文描述了三种发育谱系状态，每一种各有两个亚状态，总共六种状态；在弥漫性中线神经胶质瘤这种致命的儿童脑瘤中，4 月的论文找到七种并存的状态。以条码追踪谱系的实验显示，胰腺癌细胞可以在不同状态之间转换，不论是自发的还是在治疗之下；表现某个状态的主调节因子，能有效地把细胞重新编程成那个状态，不论是在培养皿中还是在活体动物身上。[【跳转到 16:57】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=1017) [【跳转到 17:02】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=1022) [【跳转到 17:17】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=1037)

接着，团队针对神经胶质瘤测量药物如何改变细胞：他们用 **372 种**经 FDA 核准或处于后期的肿瘤药物处理两种神经胶质瘤细胞株，24 小时后定序 RNA；然后，VIPER 估计每种药物如何改变主调节因子的活性；OncoTreat 与 OncoTarget 则预测哪些药物应该能逆转每一种状态的主调节因子活性。[【跳转到 17:34】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=1054) [【跳转到 17:39】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=1059) [【跳转到 17:54】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=1074) [【跳转到 17:59】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=1079) [【跳转到 18:04】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=1084)

其中 **9 种**预测药物在神经胶质瘤的小鼠模型中接受测试；针对特定状态的药物敏感性有 **8 种**获得验证，包括 avapritinib、ruxolitinib 和 larotrectinib。接着，团队在脑中长肿瘤的小鼠模型里，把针对互补状态的药物配成组合；论文报告说，**6 组组合中有 4 组**显著延长了存活时间，优于对应的单一药物。Avapritinib 加 ruxolitinib 让中位存活时间比载体对照组延长将近三倍，比单用 avapritinib 延长 1.5 倍。[【跳转到 18:10】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=1090) [【跳转到 18:15】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=1095) [【跳转到 18:29】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=1109) [【跳转到 18:34】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=1114)

这两种药物都已通过 FDA 核准用于其他病症，但以前没有用来治疗这种肿瘤。Biohub 的文章说，团队现在正和合作伙伴一起筹备临床试验。[【跳转到 18:57】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=1137) [【跳转到 19:02】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=1142)

![预测出的互补药物组合在小鼠模型中显著延长生存时间](assets/What is a virtual cell？Biohub's $1.8 billion data push, and the AI models it is for/01114.webp)

## 十一、讲者最后逐一回到开头的三个问题

Bunne 和同事为虚拟细胞描述了类似的循环：预测指引下一步的实验，新的数据再改进模型。[【跳转到 19:02】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=1142)

那么，虚拟细胞是什么？在 Bunne 和同事的构想里，它是一个**学习出来的细胞模拟器**：能表示细胞状态、预测细胞如何反应，并在电脑上进行实验。[【跳转到 19:18】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=1158) 它需要什么？需要从刻意改变过的细胞所得到的资料，涵盖许多细胞类型与条件；也需要能跟上模型进展的基准测试。[【跳转到 19:39】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=1179) [【跳转到 19:44】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=1184) [【跳转到 19:49】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=1189)

模型现在走到哪里了？在一项基准测试中，就所测试的资料而言，5 个基础模型和另外 2 个深度学习模型，在预测扰动效果上没有胜过简单基线。[【跳转到 19:54】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=1194) [【跳转到 20:04】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=1204)

那 Biohub 在建造什么？是开放、标准化、关于细胞如何回应改变的资料，以及测量这些资料的工具；背后有公私伙伴投入的 18 亿美元经费、资料、运算与技术。[【跳转到 20:04】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=1204) [【跳转到 20:11】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=1211) [【跳转到 20:18】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=1218) 目前，新闻稿把虚拟细胞称为下一个科学时代的挑战，而 Bunne 和同事则把它描述为一个协同研究议程的愿景。[【跳转到 20:30】](https://www.youtube.com/watch?v=2-Ou1BLkpQQ&t=1230)

## 小结

- 虚拟细胞是**以未扰动状态和扰动为输入、以扰动后状态为输出**的学习型模拟器，不是细胞图谱，也不是“更花的聚类”。
- 输入是多尺度、多模态测量；输出先是三层**表示**，再由解码器和操纵器变成可读结果与扰动预测。
- 三类用途是**表示状态、预测未见扰动、在电脑上做实验**；第三类不追求完全准确，而是排序假设、缩小搜索空间。
- 数据燃料是 Perturb-seq 这类“扰动—响应”数据；规模重要，但对照、覆盖和评测拆分同样重要。
- 2025 年的基准提醒我们：**基础模型不等于虚拟细胞**，单细胞图谱预训练帮助有限，扰动数据预训练才有明显收益。
- Biohub 的 18 亿美元主要投向开放数据和测量工具；哥伦比亚大学的肿瘤案例展示了“计算预测—湿实验验证—临床准备”的闭环。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| 虚拟细胞 | 以细胞状态和扰动为输入、预测扰动后状态的计算模型或平台 |
| 嵌入（embedding） | 模型学出的低维数字表示，保留对下游任务有用的关系 |
| 解码器 / 操纵器 | 前者把表示变成可读输出，后者把一种状态表示变成另一种 |
| Perturb-seq | 把 CRISPR 扰动与单细胞 RNA 测序结合，读出每个扰动的表达响应 |
| 主调节因子 | 在某种细胞状态中起主导调控作用的蛋白 |
| 反事实预测 | 对训练时没做过、但可以真实执行的扰动给出可检验的预测 |

## 相关阅读

- [Yusuf Roohani at ARDD2025: Building a Virtual Cell](<Yusuf Roohani at ARDD2025：Building a Virtual Cell：an AI platform for engineering cell state.md>)
- [MPG Primer: Introduction to Perturb-seq analysis](<MPG Primer：Introduction to Perturb-seq analysis (2021).md>)
- [Tahoe-100M：千兆级单细胞扰动图谱](<Tahoe-100M：千兆级单细胞扰动图谱 ｜｜ Dr. Johnny Yu.md>)
- [Deep-learning-based Gene Perturbation Effect Prediction Does Not Yet Outperform Linear Baselines](Deep-learning-based Gene Perturbation Effect Prediction Does Not Yet Outperform Linear Baselines.md)
- [PerturBench: Benchmarking Machine Learning Models for Cellular Perturbation Analysis](<PerturBench：Benchmarking Machine Learning Models for Cellular Perturbation Analysis.md>)
