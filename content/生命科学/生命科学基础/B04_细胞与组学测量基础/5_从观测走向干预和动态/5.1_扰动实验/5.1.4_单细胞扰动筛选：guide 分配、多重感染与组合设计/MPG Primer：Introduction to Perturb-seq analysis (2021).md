# MPG Primer: Introduction to Perturb-seq analysis (2021)

- 视频标题：MPG Primer: Introduction to Perturb-seq analysis (2021)
- 视频链接：<https://www.youtube.com/watch?v=K73VyTp5eXE>
- 时长：43:54
- 字幕：YouTube 英文自动字幕

## 视频主线

Perturb-seq 把 pooled CRISPR 筛选和单细胞 RNA 测序接进同一个实验：一次并行扰动几百到几千个基因，同时读出每个细胞的全转录组。讲者先说明传统敲除和 pooled 筛选为什么不够，再分别拆开实验的两个半边、讲清 guide 如何与 mRNA 一起被捕获，最后按“细胞类型与状态 → 差异表达与回归 → 共功能模块 → 组合扰动”的顺序，演示这套数据能回答哪些生物学问题。他也反复提醒：Perturb-seq 在这里是宽泛说法，泛指 CROP-seq、Mosaic-seq 这类“pooled CRISPR + 单细胞 profiling”的筛选。讲者还说明，这场报告不是逐步操作教程，而是提供“数据长什么样、该怎么想、能回答哪些问题”的直觉。

## 一、扰动是理解机制与因果的入口，但传统方法卡在“规模”和“读出”

讲者先给了一个系统生物学的循环：选一个能观测表型的系统，用基因组学方法测量它——例如测每个基因的 RNA 水平，得到表达谱，可以是一块组织里许多细胞的混合样本，也可以是逐个单细胞；据此建立一个“系统如何工作”的模型；然后扰动模型里的遗传或非遗传组分，再回头观测表型如何变化，用新观测更新模型，再扰动、再观测。[【跳转到 01:20】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=80) 扰动之所以核心，是因为它把“相关”推进到“机制与因果”。[【跳转到 02:10】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=130)

经典扰动逻辑很直观：假设基因 A 影响某表型，就敲掉它再看表型。幻灯片里的例子是细胞组成——敲掉基因 A 后，紫色和黄色细胞变多，绿色和蓝色细胞变少，于是把基因 A 与组成变化联系起来。[【跳转到 02:35】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=155)

![经典扰动实验：敲掉一个基因，比较细胞组成等表型是否改变](<assets/MPG Primer：Introduction to Perturb-seq analysis (2021)/00155.webp>)

但体内敲除模型——比如全身或条件性基因敲除小鼠——虽然好用，却一次只研究一个基因，建系传代都很耗时，很难扩展到成百上千个基因。[【跳转到 03:00】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=180) pooled（混合）CRISPR 筛选把大量 guide 装进一个文库，一次转染一群细胞，每个细胞随机拿到一个扰动，最后靠 guide 丰度判断哪些扰动让细胞变少或变多。[【跳转到 03:25】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=205) 代价是**读数和表型都必须事先定好**：通常只能看 guide 丰度、细胞生长或存活。[【跳转到 03:50】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=230)

这就挡住了更深入的问题：同一个表型可能来自不同分子机制；细胞有异质性，不同细胞类型或状态对扰动的反应可能不同；我们可能想同时预测多个表型的调控因子，比如细胞处在细胞周期的哪个阶段、另一条通路又如何响应；也可能想研究分化这类**没有现成读数**的复杂生物学。传统实验还得为读数选择做大量优化。[【跳转到 04:15】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=255) [【跳转到 04:40】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=280)

解法是换“高含量”读数：单细胞 RNA 测序或成像，一次读出每个细胞的全转录组或图像表型，把并行 CRISPR 筛选接到复杂表型上。[【跳转到 05:05】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=305) Perturb-seq 就是这类“pooled CRISPR + 高含量单细胞 profiling”的代表；讲者口中的 Perturb-seq 是宽泛说法，也包括 CROP-seq、Mosaic-seq 等。[【跳转到 05:30】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=330)

![Perturb-seq 的两半：左侧是并行遗传扰动，右侧是高含量单细胞读数](<assets/MPG Primer：Introduction to Perturb-seq analysis (2021)/00336.webp>)

## 二、pooled CRISPR 这一半：每个靶基因 3–5 条 guide，外加不靶向的对照

讲者先讲实验的左半边。典型文库围绕一个感兴趣的系统和一到几个假设展开，先选出几百到几千个靶基因——例如 GWAS 研究给出的候选基因。[【跳转到 05:54】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=354) 每个靶基因通常设计 3–5 条 guide；除此之外还要有不靶向任何基因的**对照 guide**，因为判断“扰动做了什么”，必须和“没拿到这个扰动的细胞”比较。文库用慢病毒载体递送，转染后再把真正带 guide 的细胞筛出来、扩增起来。[【跳转到 06:19】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=379)

这里的 **guide** 就是 sgRNA，一段引导序列，决定 CRISPR 系统去基因组哪个位置；**pooled** 指所有 guide 混在一个文库、一次实验完成，而不是一个基因一个孔地做。到这一步，只是完成了“大规模并行扰动”这一半；还缺高含量读出。

## 三、单细胞 RNA 测序这一半：细胞条形码、UMI 与 poly(T) 三件套

单细胞 RNA 测序这几年改变了生物学研究的分辨率，关键技术突破是能在许多细胞里给每个细胞一个身份标识。[【跳转到 06:44】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=404) 基于液滴的技术尤其通用、可扩展：油包里包着带珠子的液滴，微流控系统把细胞和珠子一起封进液滴；珠子表面伸出许多 oligonucleotide（寡核苷酸）构建。[【跳转到 07:19】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=439)

把构建简化，可以看成三段：**细胞条形码**（cell identifier）标记这个液滴捕获的是哪个细胞；**UMI（unique molecule identifier，分子条形码）**标记每一条被捕获的 mRNA；**poly(T) 引物**通过碱基配对抓住 mRNA 的 poly(A) 尾巴。[【跳转到 07:44】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=464) 一个液滴里有无数条这样的构建，就能抓住这个细胞转录组的很大一部分。[【跳转到 08:18】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=498)

![液滴测序的三段式标识：细胞条形码、UMI 与 poly(T)](<assets/MPG Primer：Introduction to Perturb-seq analysis (2021)/00473.webp>)

讲者用三个液滴、三种颜色的细胞做示意：每个液滴里有带上述构建的珠子，捕获各自细胞的 mRNA，再做建库和测序；测出来的每一条 read 都带着细胞条形码、UMI，以及它捕获的那段转录本。[【跳转到 08:50】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=530) [【跳转到 09:15】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=555) 到这里，单细胞测序这一半也齐了。

## 四、把两半接起来：给 guide 加 poly(A)，让同一个 poly(T) 有两种抓取对象

要把两半合并，必须再给每个细胞一个“扰动身份”。原始 Perturb-seq 论文设计了一个相当复杂、很有创造性的慢病毒构建，关键部件是 **guide barcode**：在 guide 旁边放一段可读出的条形码（或者直接用 guide 序列本身），再接一个 poly(A) 尾巴。[【跳转到 09:30】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=570) [【跳转到 09:44】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=584)

于是同一个液滴里，poly(T) 既可能抓住细胞的 mRNA，也可能抓住这条带 poly(A) 的扰动构建。细胞条形码告诉我们“这是哪个细胞”，guide barcode 告诉我们“这个细胞拿到了哪条 guide”，两个身份就都齐了。[【跳转到 10:05】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=605) [【跳转到 10:29】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=629)

![同一个 poly(T) 有两种抓取对象：mRNA 转录本，或带 poly(A) 的扰动构建](<assets/MPG Primer：Introduction to Perturb-seq analysis (2021)/00629.webp>)

### 4.1 MOI 决定一个细胞平均拿到几条 guide

回到完整流程：先有 CRISPR 文库，转染细胞；关键参数 **MOI（multiplicity of infection，感染复数）** 控制平均每个细胞拿到几条 guide。理想是“至少一条、最好只有一条”：一条都没有就没有扰动信息；两条以上则多个扰动混在一起，难以归因。[【跳转到 10:52】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=652) 转染后还要筛选，确保留下的是带 guide 的细胞（扰动 guide 或对照 guide 都算）。[【跳转到 11:17】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=677)

### 4.2 dial-out PCR 拆出表达矩阵与扰动矩阵

建库时，mRNA 文库除了液滴条形码，还会带一个 **feature barcode（扰动条形码）**，用来说明细胞携带哪条 guide。[【跳转到 11:36】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=696) 但一个细胞的转录本远多于 guide 分子，所以通常再用 **dial-out PCR** 专门富集 guide 片段，最后拆成两个文库：mRNA 文库给出“细胞×基因”表达矩阵，guide 文库给出“细胞×guide”扰动矩阵。[【跳转到 11:44】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=704) 预处理可用 10x 的 Cell Ranger（已适配 CRISPR 筛选），也可用 Broad 开发的云端流程 Cumulus。[【跳转到 12:09】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=729)

### 4.3 连续值扰动矩阵要估背景、定阈值，才变成 0/1

表达矩阵里每个元素是某个基因转录本被捕获到的 unique molecule 数；扰动矩阵里则是每个细胞捕获到某条 guide 序列的 UMI 数。[【跳转到 12:59】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=779) 这时扰动矩阵还是连续值，但我们通常只关心“这个细胞有没有这条 guide”。液滴可能捕获到周围环境里的 **ambient RNA**（游离 RNA），所以标准软件会先估计背景分布，再定阈值，判断扰动信号是否真的被检测到，最后转成 0/1 矩阵。[【跳转到 13:29】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=809) [【跳转到 13:54】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=834)

## 五、QC 要先确认“扰动真的发生了”，而不是只看测序质量

拿到扰动矩阵后，讲者先做几项 sanity check。第一看 **guide 分布**：幻灯片里约七成细胞只有一条 guide，符合“一细胞一扰动”的设计，说明 MOI 控制得当。[【跳转到 14:33】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=873)

![QC 的第一眼：大多数细胞只检测到 1 条 sgRNA，说明 MOI 控制得当](<assets/MPG Primer：Introduction to Perturb-seq analysis (2021)/00873.webp>)

第二看 **每个扰动的细胞数**：要追到单基因层面的细节，细胞越多越好；如果只关心基因模块或表达程序的模式，每个扰动少一些细胞也够。[【跳转到 14:58】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=898) 第三看 **双细胞率**：一个液滴捕获两个细胞时，转录组和 guide 会混在一起，已有多种工具可以检测并剔除。[【跳转到 15:23】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=923)

最容易被忽略的是确认**靶基因真的被扰动**：如果是敲除，就比较带扰动 guide 与带对照 guide 的细胞，看靶基因表达有没有按预期下降。[【跳转到 15:48】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=948) 还有一个陷阱是**必需基因**：细胞离开它活不了，敲掉后直接死亡，数据里根本看不到——这不是“没有效应”，而是幸存者偏差。[【跳转到 16:13】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=973)

## 六、有了两张矩阵，讲者列了五个问题，然后先从细胞类型与状态讲起

### 6.1 从基因走向功能的五个问题

讲者把分析拆成五个问题：系统里有哪些细胞类型/状态？扰动改变了哪些转录状态、哪些细胞回路？哪些扰动有相似的转录效应（共功能扰动模块）？扰动的组合会怎样？以及扰动效应是否有细胞类型特异性？[【跳转到 16:38】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=998) 他并没有按列表顺序讲，而是先把“细胞异质性”讲透，再进入转录变化、共功能模块，最后回到细胞类型特异性和组合扰动。

### 6.2 先看细胞类型与状态

从“细胞×基因”矩阵出发，用标准单细胞流程：挑高变基因、降到低维、做图聚类，得到可能代表细胞类型或状态的簇。[【跳转到 18:18】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=1098) 讲者举了一篇体内 Perturb-seq 研究：用 GWAS 找到的自闭症相关基因，在小鼠脑发育中做扰动，发现了五种细胞类型；在每个类型内部还能继续做亚聚类，识别更细的细胞状态。[【跳转到 18:48】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=1128) [【跳转到 19:13】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=1153)

### 6.3 再看扰动是否改变细胞组成

有了细胞类型，就能问：不同扰动下细胞组成是否变化？有没有些扰动因为转录效应而偏向某些细胞类型？同一个研究里，可以看到五种细胞类型的比例如何随扰动基因变化。[【跳转到 19:38】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=1178) 还能进一步看同一细胞类型里出现了哪些状态：例如三个状态中有两个是“激活”状态，细胞还处在细胞周期的不同阶段。[【跳转到 20:07】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=1207)

### 6.4 差异表达给出基因列表

接下来问“每个扰动对每个基因做了什么”。最直接的是**差异表达**：把带某扰动的细胞与带对照 guide 的细胞比较，找出显著上调和下调的基因，再用常见工具做功能注释。[【跳转到 20:48】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=1248) [【跳转到 21:13】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=1273)

### 6.5 MIMOSA 把效应估成系数矩阵

更系统的做法是回归。Perturb-seq 原论文提出的 **MIMOSA** 把模型写成 `Y = Xβ + 协变量`：`Y` 是“细胞×基因”表达矩阵，`X` 是“细胞×扰动”的 0/1 设计矩阵（也就是前面那张扰动矩阵），`β` 是每个扰动对每个基因的效应量；批次、细胞质量等可以作为协变量一起校正。我们真正想推断的就是这个系数矩阵（也可叫调控矩阵）。[【跳转到 21:34】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=1294) [【跳转到 21:59】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=1319)

![MIMOSA 的回归框架：表达矩阵 Y 由扰动设计矩阵 X 解释，目标是推断系数矩阵 β](<assets/MPG Primer：Introduction to Perturb-seq analysis (2021)/01294.webp>)

讲者在这里插了一个重要限定：细胞可能拿到了 guide，却因为系统不完美而没有真正被扰动。原始论文会依据某个分数更新 0/1 矩阵；**Mixscape** 则把这类细胞称为 “escaping cells”（逃逸细胞）单独识别。[【跳转到 22:35】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=1355) [【跳转到 23:00】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=1380)

### 6.6 效应热图的成块模式

把 `β` 排成“基因×扰动”矩阵画热图：红色表示扰动后表达上升，蓝色表示下降。[【跳转到 23:26】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=1406)

![效应矩阵热图：每一列是一条 guide，每一行是一个基因，红蓝表示效应方向](<assets/MPG Primer：Introduction to Perturb-seq analysis (2021)/01417.webp>)

## 七、效应热图的成块模式就是共功能扰动模块与基因表达程序

热图不只是逐格看效应，还能看到成块的模式，对应两类结构：**共功能扰动模块**——一组扰动以相似方式影响一批基因，可能作用于同一通路或彼此配合；以及**基因表达程序**——一组基因被某些扰动以相似方式共同带动。[【跳转到 24:15】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=1455) [【跳转到 24:46】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=1486)

把模块和程序画成网络，是另一种可视化方式：红线和蓝线分别表示激活与抑制，程序框里的词是对这组基因的功能注释。[【跳转到 24:58】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=1498) 还可以只挑出其中的转录因子，画它们之间如何互相调控。[【跳转到 25:23】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=1523) [【跳转到 25:48】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=1548)

![共功能模块与基因表达程序：左侧是效应热图，右侧把模块与程序连成调控网络](<assets/MPG Primer：Introduction to Perturb-seq analysis (2021)/01523.webp>)

## 八、换成基因集分数与相关矩阵：哪些扰动相似、效应是否细胞类型特异

### 8.1 不必逐基因看，可以把因变量换成基因集分数

如果只关心“扰动对一组基因/一个表达模式的影响”，可以沿用同一套回归，但把因变量从单个基因表达换成**基因集分数**：主题模型、矩阵分解或 WGCNA 得到的模块分数，或者一个低维嵌入。这样得到的是“模块（或嵌入）×扰动”矩阵，而不是“基因×扰动”。[【跳转到 26:06】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=1566) [【跳转到 26:31】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=1591)

讲者一直用作案例的那篇论文就是这么做的：先对每个细胞簇识别基因模块，把模块配到特定细胞类型，再估计每个扰动对该模块分数的影响。于是每一行是一个模块（如 P1、P2），可以看到某些模块的效应是**细胞类型特异**的。[【跳转到 26:56】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=1616) [【跳转到 27:21】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=1641) 同类工具还有用主题模型的 **MUSIC**、用回归框架的 **scMAGIC**。[【跳转到 27:46】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=1666)

### 8.2 相关矩阵一眼看出哪些扰动相似

更紧凑的表示是**相关矩阵**：每个元素是两条 guide 效应向量的相关系数；如果两条 guide 以相似方式影响基因，它们应该高度相关。对全基因组规模的大筛选，这张图能一眼看出系统里可能存在哪些模块、下一步该追什么。[【跳转到 28:21】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=1701)

右侧的相关系数直方图还给出一个符合预期的结果：同一基因的不同 guide 之间相关性更高，跨基因更低；但由于单细胞读数稀疏，整体相关系数没有想象中那么高。[【跳转到 28:51】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=1731) [【跳转到 29:16】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=1756)

### 8.3 同一扰动在不同细胞类型里可以有不同效应

回到那个自闭症相关基因的体内研究：某些扰动只以细胞类型特异的方式影响某些模块。例如 P1 模块由一组基因代表，特异于兴奋性神经元的 PN 簇，并在该簇显著富集；其他模块也有类似的细胞类型特异性。[【跳转到 29:37】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=1777) [【跳转到 29:50】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=1790) [【跳转到 30:15】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=1815) 讲者强调，这类信息是非 Perturb-seq 的筛选拿不到的。

## 九、组合扰动：在回归里加交互项，判断相加还是协同/拮抗

如果细胞里真的出现两条 guide，可以在同一回归框架里加**交互项**。设计矩阵仍是 0/1 扰动矩阵，但因变量除了单扰动效应，还要估计扰动组合的交互效应。[【跳转到 30:50】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=1850) [【跳转到 31:15】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=1875) 这能回答：两个扰动是简单相加，还是协同、拮抗？原始论文的可视化里，某些扰动组合的效应会富集在特定细胞状态（编号 0–6 是聚类得到的细胞状态）。[【跳转到 31:40】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=1900)

## 十、规模化：细胞哈希把更多样本塞进一次测序，perturb-CITE-seq 再加一层蛋白

讲者先小结前半场：Perturb-seq 把 pooled CRISPR 与高含量单细胞 profiling 结合；我们走过了它帮助回答的生物学问题——共功能扰动模块、表达程序、如何可视化和连接它们、这些程序的细胞类型特异性，以及组合扰动如何起作用。[【跳转到 32:05】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=1925)

### 10.1 细胞哈希：超载微流控通道，再判断单细胞还是多细胞

要扩大到更多细胞、更多样本（乃至更多小鼠），常用**细胞哈希**（cell hashing）：往微流控通道里“超载”多个样本，用抗体哈希标记来源，之后再推断每个液滴捕获的是一个细胞还是多个细胞。[【跳转到 32:53】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=1973) [【跳转到 33:14】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=1994)

与前面的流程相比，多了一个富集的抗体 hashtag 文库，于是有三张表：细胞×基因表达矩阵、细胞×抗体哈希矩阵、细胞×guide 扰动矩阵。[【跳转到 33:39】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=2019) 标准预处理软件能处理这类数据；关键一步是把哈希矩阵解卷积，判断单细胞/多细胞，`demuxEM`（属于 Cumulus 套件）可以做这件事。[【跳转到 34:04】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=2044) [【跳转到 34:29】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=2069) 这给原始 RNA 数据多加了一层 QC：只保留有把握是单细胞的液滴。

讲者还回头补了一句“需要多少细胞、测多深”：仍然取决于生物学问题——追单个基因需要更多细胞，追 signature 或程序则每个扰动少一些细胞也够。[【跳转到 34:54】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=2094)

### 10.2 读数不止 RNA：perturb-CITE-seq 同时读表面蛋白

Perturb-seq 不必局限于转录组，也可以加其他信息丰富的单细胞读数，比如蛋白或染色质。**perturb-CITE-seq** 就是多模态遗传筛选：在单细胞 RNA 测序前加一步 CITE-seq 抗体染色，同时读出细胞表面蛋白和转录组。[【跳转到 35:44】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=2144) [【跳转到 36:08】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=2168) 限定是：不可能覆盖整个蛋白质组，通常只能看一小组预先选定的表面蛋白。[【跳转到 36:33】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=2193) 分析上仍可沿用共功能模块与程序的思路，只是现在能同时知道扰动对 RNA 和蛋白特征的影响。[【跳转到 36:51】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=2211)

## 十一、想继续深入：建模方法总表、公开数据与几个现实边界

讲者最后推荐了一篇刚发表的综述，里面有一张表，把已发表的单细胞扰动建模方法按类别汇总：今天讲过的分类/回归框架、因子模型或基因模块模型，还有今天没展开的非线性模型等；综述也列出了可以拿来练手的公开扰动数据集。[【跳转到 37:21】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=2241) [【跳转到 37:46】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=2266)

问答里，讲者划了几条边界：

- **组合扰动不能无限叠加**：一般细胞里超过四条 guide 就难以存活；是否存在特定“致死的 guide 组合”仍是有趣但未解的问题。[【跳转到 40:29】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=2429)
- **细胞类型可操作性不同**：很多研究在体外做，体内 Perturb-seq 明显更难；早期研究多用免疫细胞或容易体外培养的细胞，复杂组织会遇到和单细胞 RNA 测序类似的挑战。讲者说自己不是实验专家，细节要问做实验的同事。[【跳转到 41:30】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=2490) [【跳转到 42:05】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=2525)
- **“扰动”可以更宽泛**：有听众问能否把温度等环境因素当作扰动，用同一套分析框架研究跨物种响应。讲者认为只要实验里有“在环境中/不在环境中”的对照和观测，就可以套用差异分析的思路；具体取决于读数是不是转录组或其他系统级表型。[【跳转到 42:17】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=2537) [【跳转到 43:10】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=2590) [【跳转到 43:37】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=2617)

## 小结

- **Perturb-seq = pooled CRISPR + 单细胞 RNA 测序**：并行成百上千个基因扰动，读出每个细胞的全转录组，而不只是“死没死”。
- 设计关键是“**一个细胞一个扰动**”：每个基因 3–5 条 guide，加对照 guide，用 MOI 控制导引数量。
- 同时读到 mRNA 和 guide 的关键，是给 guide 接 poly(A) 尾巴/条形码，让同一个 poly(T) 有两种抓取对象；dial-out PCR 再拆成表达矩阵与扰动矩阵，并把连续值二值化。
- QC 不只看测序质量：guide 分布、每个扰动的细胞数、双细胞率、靶基因是否真的下降、必需基因是否丢失，都会决定结论是否可信。
- 分析先看细胞类型/状态与组成，再走差异表达和 MIMOSA 回归；效应热图的块对应共功能扰动模块与基因表达程序，换成基因集分数还能看细胞类型特异性。
- 相关矩阵用来找相似扰动；组合扰动用交互项估计协同/拮抗；细胞哈希把更多样本塞进一次测序，perturb-CITE-seq 把 RNA 与表面蛋白一起读。
- 讲者最后强调边界：超过四条 guide 细胞难存活，体内实验比体外难，环境扰动也可以借用这套框架但要先设计好对照与读数。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| Perturb-seq | 把 pooled CRISPR 扰动与单细胞 RNA 测序结合，读出每个被扰动细胞的全转录组。 |
| guide / sgRNA | 引导 CRISPR 系统定位到目标基因的一段 RNA；一个基因通常设计多条。 |
| MOI | 感染复数，控制平均每个细胞拿到几条 guide；理想是“一细胞一扰动”。 |
| 细胞条形码 / UMI | 前者标记细胞，后者标记每条 mRNA，用于把 reads 归属到细胞并去除 PCR 重复。 |
| poly(T) / poly(A) | poly(T) 抓 mRNA 的 poly(A) 尾巴；给 guide 加 poly(A) 就能被同一引物捕获。 |
| 双细胞（doublet） | 一个液滴捕获两个细胞，转录组与 guide 混合，需要检测并剔除。 |
| 扰动矩阵 / 设计矩阵 | “细胞×扰动”的 0/1 矩阵；在回归里作为设计矩阵 X，告诉模型每个细胞拿到了哪条 guide。 |
| 效应矩阵 | “扰动×基因”的系数表，元素表示某扰动对某基因表达的影响大小与方向。 |
| 共功能模块 / 基因程序 | 前者是一组效应相似的扰动，后者是一组被相似扰动共同带动的基因。 |
| 细胞哈希 | 用抗体条形码标记样本来源，超载微流控通道后把单细胞与多细胞分开。 |
| perturb-CITE-seq | 在 Perturb-seq 前加抗体染色，同时读出转录组与一小组表面蛋白。 |
