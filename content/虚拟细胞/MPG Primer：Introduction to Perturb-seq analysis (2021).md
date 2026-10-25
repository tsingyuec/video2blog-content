# MPG Primer: Introduction to Perturb-seq analysis (2021)

- 视频标题：MPG Primer: Introduction to Perturb-seq analysis (2021)
- 视频链接：<https://www.youtube.com/watch?v=K73VyTp5eXE>
- 时长：43:54
- 字幕：YouTube 英文自动字幕

## 本讲要解决的核心问题（SCQA）

**背景**：研究一个基因的功能，最直接的办法是扰动它，再看细胞发生了什么变化。虚拟细胞要预测“没做过的扰动”，同样需要大量“扰动—响应”配对数据。

**冲突**：传统小鼠敲除模型一次只研究一个基因，建系传代很慢；pooled CRISPR 筛选虽然能一次并行成千上万个扰动，但读出通常只是细胞长得快不快、活不活，回答不了“细胞内部哪些基因变了”。

**疑问**：能不能既保留“并行扰动”的规模，又给每个细胞装一个高信息量的读数，并且知道它究竟拿到了哪条 guide？

**回答（中心思想）**：Perturb-seq 把 pooled CRISPR 文库和液滴单细胞 RNA 测序接进同一个实验：同一个液滴既捕获细胞的 mRNA，也捕获 guide 自带的条形码。测序后得到“细胞×基因”表达矩阵和“细胞×guide”扰动矩阵，再用差异表达、回归、共功能模块与交互项，把扰动翻译成“哪些基因、哪些程序、哪些细胞类型发生了变化”。

## 一、Perturb-seq 要解决的是“并行扰动”与“高信息量读出”的矛盾

经典扰动逻辑很直观：假设基因 A 影响某表型，就敲掉它再看表型。幻灯片里的例子是细胞组成——敲掉基因 A 后，紫色和黄色细胞变多，绿色和蓝色细胞变少，于是把基因 A 与组成变化联系起来。[【跳转到 02:35】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=155)

![经典扰动实验：敲掉一个基因，比较细胞组成等表型是否改变](<assets/MPG Primer：Introduction to Perturb-seq analysis (2021)/00155.webp>)

但体内敲除模型一次只做一个基因，建系传代都耗时，难以扩展到成百上千个基因。[【跳转到 03:00】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=180) pooled CRISPR 把大量 guide 装进一个文库，一次转染一群细胞，每个细胞随机拿到一个扰动，最后靠 guide 丰度判断哪些扰动让细胞变少或变多。[【跳转到 03:25】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=205) 代价是**读数和表型都必须预设**：通常只能看 guide 丰度、细胞生长或存活。[【跳转到 03:50】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=230) 于是同一个表型背后的不同机制、细胞类型差异、同时变化的多个表型、乃至分化这类没有现成读数的过程，都容易被漏掉。[【跳转到 04:15】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=255)

解法是换“高含量”读数：单细胞 RNA 测序一次读出每个细胞的全转录组，把并行 CRISPR 筛选接到复杂表型上。Perturb-seq 就是这类“pooled CRISPR + 单细胞 profiling”的代表；讲者口中的 Perturb-seq 是宽泛说法。[【跳转到 05:05】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=305)

![Perturb-seq 的两半：左侧是并行遗传扰动，右侧是高含量单细胞读数](<assets/MPG Primer：Introduction to Perturb-seq analysis (2021)/00336.webp>)

## 二、实验设计：每个基因 3–5 条 guide，理想状态是“一个细胞一个扰动”

典型文库围绕几百到几千个目标基因展开，每个基因设计 3–5 条 guide，并加入不靶向任何基因的对照 guide——对照回答的是“没有这个扰动时，细胞本来是什么样”。文库用慢病毒递送，转染后再筛选出真正带 guide 的细胞。[【跳转到 05:54】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=354)

这里的 **guide** 就是 sgRNA，一段引导序列，决定 CRISPR 系统去基因组哪个位置；**pooled** 指所有 guide 混在一个文库、一次实验完成，而不是一个基因一个孔地做。

关键参数 **MOI（multiplicity of infection，感染复数）** 控制平均每个细胞拿到几条 guide。理想是“至少一条、最好只有一条”：一条都没有就没有扰动信息；两条以上则多个扰动混在一起，难以归因。[【跳转到 10:52】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=652)

## 三、技术核心：让 poly(T) 在同一液滴里既抓 mRNA，也抓 guide

液滴单细胞测序的珠子上有一小段 oligonucleotide（寡核苷酸），包含三部分：**细胞条形码**标记这个液滴捕获的是哪个细胞；**UMI（分子条形码）**标记每一条被捕获的 mRNA；**poly(T) 引物**通过碱基配对抓住 mRNA 的 poly(A) 尾巴。[【跳转到 07:44】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=464)

![液滴测序的三段式标识：细胞条形码、UMI 与 poly(T)](<assets/MPG Primer：Introduction to Perturb-seq analysis (2021)/00473.webp>)

Perturb-seq 的巧思，是给 guide 也造一个可被 poly(T) 抓住的身份：病毒构建里，guide 旁边带 guide barcode（或 guide 序列本身），再接一个 poly(A) 尾巴。于是同一个液滴里，poly(T) 既可能抓细胞的 mRNA，也可能抓这条 guide 构建。[【跳转到 09:44】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=584)

![同一个 poly(T) 有两种抓取对象：mRNA 转录本，或带 poly(A) 的扰动构建](<assets/MPG Primer：Introduction to Perturb-seq analysis (2021)/00629.webp>)

测序时 mRNA 文库还会带上 feature barcode，用来说明细胞携带哪条 guide。[【跳转到 11:36】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=696) 因为转录本远多于 guide 分子，通常再用 dial-out PCR 富集 guide 片段，最终拆成两个文库：mRNA 文库给出“细胞×基因”表达矩阵，guide 文库给出“细胞×guide”扰动矩阵。[【跳转到 11:44】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=704) 原始扰动矩阵是连续值，需要估计背景分布、设定阈值，转成 0/1 矩阵。[【跳转到 13:29】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=809) 预处理可用 10x 的 Cell Ranger 或 Broad 的云端流程 Cumulus。[【跳转到 12:34】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=754)

## 四、拿到两张矩阵，先做 QC：确认“扰动真的发生了”

先看 **guide 分布**：大多数细胞是否只有一条 guide。幻灯片里约七成细胞只有一条，符合“一细胞一扰动”的设计。[【跳转到 14:33】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=873)

![QC 的第一眼：大多数细胞只检测到 1 条 sgRNA，说明 MOI 控制得当](<assets/MPG Primer：Introduction to Perturb-seq analysis (2021)/00873.webp>)

再看 **每个扰动的细胞数**：追单基因要更多细胞，看基因模块或表达程序则可以少一些。[【跳转到 14:58】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=898) 还要检查 **双细胞率**——一个液滴捕获两个细胞时，转录组和 guide 会混在一起，需要用工具检测并剔除。[【跳转到 15:23】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=923)

最容易被忽略的是确认**靶基因真的被扰动**：比较带扰动 guide 与对照 guide 的细胞，看靶基因表达有没有按预期下降。[【跳转到 15:48】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=948) 以及**必需基因**问题：细胞离开它活不了，敲掉后直接死亡，数据里根本看不到——这不是“没有效应”，而是幸存者偏差。[【跳转到 16:13】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=973)

## 五、从差异表达到效应矩阵：把“每个扰动对每个基因的影响”估出来

有了两张矩阵，就可以沿五个问题从基因走向功能：系统里有哪些细胞类型/状态？扰动改变了哪些转录状态？哪些扰动效应相似？组合会怎样？效应是否有细胞类型特异性？[【跳转到 16:38】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=998)

最直接的是**差异表达**：带某扰动的细胞对比带对照 guide 的细胞，找出显著上调和下调的基因，再做功能注释。[【跳转到 20:48】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=1248)

更系统的是回归。MIMOSA 写成 `Y = Xβ + 协变量`：`Y` 是“细胞×基因”表达矩阵，`X` 是“细胞×扰动”的 0/1 设计矩阵，`β` 是每个扰动对每个基因的效应量；批次、细胞质量等可作为协变量一起校正。[【跳转到 21:34】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=1294)

![MIMOSA 的回归框架：表达矩阵 Y 由扰动设计矩阵 X 解释，目标是推断系数矩阵 β](<assets/MPG Primer：Introduction to Perturb-seq analysis (2021)/01294.webp>)

现实问题是：细胞可能拿到 guide 却未被真正扰动。原始论文会依据一个分数更新 0/1 矩阵；Mixscape 则把这类细胞称为 “escaping cells”（逃逸细胞）单独识别。[【跳转到 22:35】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=1355)

把 `β` 排成“基因×扰动”矩阵画热图，红色表示上调、蓝色表示下调。[【跳转到 23:26】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=1406)

![效应矩阵热图：每一列是一条 guide，每一行是一个基因，红蓝表示效应方向](<assets/MPG Primer：Introduction to Perturb-seq analysis (2021)/01417.webp>)

热图里的成块模式对应两类结构：**共功能扰动模块**——一组扰动影响相似基因，可能作用于同一通路；以及**基因表达程序**——一组基因被相似扰动共同带动。[【跳转到 24:15】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=1455) 把模块和程序画成网络，红线、蓝线分别表示抑制与激活，就能把统计模式接到功能注释上。[【跳转到 24:58】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=1498)

![共功能模块与基因表达程序：左侧是效应热图，右侧把模块与程序连成调控网络](<assets/MPG Primer：Introduction to Perturb-seq analysis (2021)/01523.webp>)

若不想逐基因看，可把回归的因变量换成“基因集合分数”——主题模型、矩阵分解或 WGCNA 得到的模块分数，或一个低维嵌入。这样得到“模块×扰动”矩阵；案例研究里就为每个细胞簇配专属基因模块，再估计扰动对模块分数的影响，于是能看到细胞类型特异性。[【跳转到 26:06】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=1566)

判断“哪些扰动相似”，可直接算效应向量的相关矩阵；全基因组筛选时这张图能一眼看出潜在模块。相关系数直方图还显示，同一基因的不同 guide 相关性更高，跨基因更低，而单细胞稀疏性会压低整体相关性。[【跳转到 28:21】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=1701) 模块的效应还可以是细胞类型特异的：同一个扰动只在某类神经元里显著影响某个模块。[【跳转到 29:37】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=1777)

## 六、组合扰动与规模化：从“一个扰动”走到“扰动之间”

如果细胞里真的出现两条 guide，可在回归里加**交互项**，估计组合效应：两个扰动是简单相加，还是协同/拮抗。原始论文的可视化里，某些组合的效应会富集在特定细胞状态。[【跳转到 30:50】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=1850)

扩大规模常用**细胞哈希**：往微流控通道里“超载”多个样本，用抗体哈希标记来源，再判断液滴里是单细胞还是多细胞。于是有三张表——表达矩阵、细胞×抗体哈希矩阵、扰动矩阵；`demuxEM` 负责把单细胞与多细胞分开，只保留有把握的单细胞。[【跳转到 33:14】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=1994)

读数也不限于 RNA。**perturb-CITE-seq** 在单细胞 RNA 测序前加一步抗体染色，同时读出细胞表面蛋白和转录组；代价是蛋白只覆盖一小组预先选定的表面标记。[【跳转到 35:44】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=2144) 讲者最后还给出一张扰动建模方法总表，按分类/回归、因子模型、非线性模型、网络模型列出代表工具。[【跳转到 37:16】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=2236)

问答里还有两个边界：一个细胞里超过四条 guide 时，细胞通常难以存活，组合扰动不能无限叠加；[【跳转到 40:29】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=2429) 体内 Perturb-seq 比体外更难，复杂组织与原代细胞的可操作性是现实瓶颈。[【跳转到 41:30】](https://www.youtube.com/watch?v=K73VyTp5eXE&t=2490)

## 小结

- **Perturb-seq = pooled CRISPR + 单细胞 RNA 测序**：并行成百上千个基因扰动，读出每个细胞的全转录组，而不只是“死没死”。
- 设计关键是“**一个细胞一个扰动**”：每个基因 3–5 条 guide，加对照 guide，用 MOI 控制导引数量。
- 同时读到 mRNA 和 guide 的关键，是给 guide 接 poly(A) 尾巴/条形码，让同一个 poly(T) 有两种抓取对象；测序后拆成表达矩阵与扰动矩阵。
- QC 不只看测序质量：guide 分布、每个扰动的细胞数、双细胞率、靶基因是否真的下降、必需基因是否丢失，都会决定结论是否可信。
- 分析主线是“**效应矩阵**”：差异表达给基因列表，MIMOSA 一类回归给效应量，热图、共功能模块、基因程序与相关矩阵把效应读成生物学。
- 组合扰动用交互项估计协同/拮抗；细胞哈希把多个样本塞进一次测序，perturb-CITE-seq 把 RNA 与表面蛋白一起读。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| Perturb-seq | 把 pooled CRISPR 扰动与单细胞 RNA 测序结合，读出每个被扰动细胞的全转录组。 |
| guide / sgRNA | 引导 CRISPR 系统定位到目标基因的一段 RNA；一个基因通常设计多条。 |
| MOI | 感染复数，控制平均每个细胞拿到几条 guide；理想是“一细胞一扰动”。 |
| 细胞条形码 / UMI | 前者标记细胞，后者标记每条 mRNA，用于把 reads 归属到细胞并去除 PCR 重复。 |
| poly(T) / poly(A) | poly(T) 抓 mRNA 的 poly(A) 尾巴；给 guide 加 poly(A) 就能被同一引物捕获。 |
| 双细胞（doublet） | 一个液滴捕获两个细胞，转录组与 guide 混合，需要检测并剔除。 |
| 效应矩阵 | “扰动×基因”的系数表，元素表示某扰动对某基因表达的影响大小与方向。 |
| 共功能模块 / 基因程序 | 前者是一组效应相似的扰动，后者是一组被相似扰动共同带动的基因。 |
