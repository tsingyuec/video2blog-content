# Tahoe-100M：千兆级单细胞扰动图谱 || Dr. Johnny Yu

- 视频标题：Tahoe-100M：千兆级单细胞扰动图谱 || Dr. Johnny Yu
- 视频链接：<https://www.bilibili.com/video/BV1khg5z9EpZ/>
- 时长：62:59（正片约 53 分钟 + 问答）
- 字幕：Bilibili 中文 AI 字幕
- 讲者：Dr. Johnny Yu，Tahoe Therapeutics 联合创始人兼首席科学官

## 视频主线

Tahoe-100M 想回答一个问题：能不能把几十个患者肿瘤模型和上千个药物—剂量条件装进同一套实验，一次读出每个细胞的转录组？讲者的叙述从药物发现的技术史开始，先讲 Mosaic 如何把患者模型混成一块“马赛克肿瘤”，再讲 Tahoe-100M 的规模、96 孔板流程与 Parse 组合索引，最后用三个用例说明这份图谱能做什么。他的核心判断是：数据集的价值不只在“大”，更在统一、可复现、低批次，因而能直接支撑药物发现与虚拟细胞模型。他也提醒，其中不少工作尚未发表。

## 一、药物发现每个十年都有新技术，讲者押注单细胞组学成为下一个

讲者先拉远视角：单细胞技术真正受到关注其实只有十年左右，但要理解它为什么重要，得从更早的药物发现讲起。[【跳转到 04:06】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=246) [【跳转到 04:23】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=263)

1939 年，Gerhard Domagk 的工作是最早的抗生素故事之一：他提取煤焦油染料的成分，用来治疗被细菌感染的小鼠，观察哪些组分能阻止感染；有趣的是，他的首个临床试验对象是自己的女儿。[【跳转到 04:29】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=269) [【跳转到 04:54】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=294)

从那以后，药物发现的面貌变化很大：1980 年代开始用微孔板做高通量筛选；1990 年代组合化学让合成更容易、化学搜索空间大幅扩展；2000 年人类基因组计划让我们能识别致病变异、追溯到基因和可靶向的特定突变；2010 年代抗体、ADC、肽类、降解剂和基因治疗等模态取得进展。[【跳转到 05:19】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=319) [【跳转到 05:44】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=344)

讲者的判断是：**每个十年都会出现一种新技术推动药物发现，下一个十年将是单细胞组学**——它终于成熟到可以做“前沿规模”的数据集。Tahoe 相信，生成前沿规模的数据集本身就是推动发现的基础设施，而不只是发一篇论文。[【跳转到 06:09】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=369) [【跳转到 06:27】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=387)

## 二、单细胞技术用十年走到这里，2025 年可以把规模再推高一个量级

2014–2015 年，人们开始意识到单细胞组学的可能性。Evan Macosko 等人展示了最早的油包水乳液方法，2015 年发表在《Cell》；他们当时的设想甚至包括让每个实验室自己搭建定制的微流控系统，并把 Drop-seq 开源，确保任何实验室都能自己搭。[【跳转到 06:52】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=412) [【跳转到 07:17】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=437) [【跳转到 07:22】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=442)

之后十年，技术迭代很快：2015–2016 年 10x Genomics 推出 Chromium；2017 年出现单细胞一体化方案；2018 年 CITE-seq 做细胞表面蛋白 profiling，Alex Rosenberg 的 Split-seq 展示了完全不同的非液滴路线；2019 年大规模样本哈希让多样本进入同一次单细胞实验，这对新冠研究很关键；2021 年 Parse 推出试剂盒，全基因组扰动等技术继续扩展；2024 年早期单细胞基础模型出现，为后续发展打底。[【跳转到 07:52】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=472) [【跳转到 08:17】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=497)

讲者说，Tahoe 想做的就是在这个时间点“再突破一次边界”——构建 Tahoe-100M 这样的数据集，这是他们 2025 年完成的。[【跳转到 08:42】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=522)

## 三、Mosaic 把几十个患者模型混成一块“马赛克肿瘤”

讲者简单介绍了公司：四位联合创始人，团队在 UCSF 起步，顾问里有小分子肿瘤、临床非小细胞肺癌和 AI/NLP 领域的专家；公司成立三年、完成两轮共 4,500 万美元融资，所有工作都建立在此前的学术研究上。[【跳转到 08:51】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=531) [【跳转到 09:10】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=550) [【跳转到 09:35】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=575)

平台叫 **Mosaic**，核心想法是把多种患者模型放进同一个实验单元。在癌症里，这意味着收集不同患者、不同器官的肿瘤——脑癌、肺癌、结直肠癌——把它们混成一块“马赛克肿瘤”，再植入小鼠或类器官，从而可重复地筛选数千种化合物。[【跳转到 10:00】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=600) [【跳转到 10:25】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=625)

加药后把肿瘤解离成单细胞，做单细胞 RNA 测序。读出有两层：**敏感性**——哪些患者模型对药物敏感；以及**转录组变化**——药物把细胞推到了什么状态。后者能揭示机制，区分靶向与脱靶效应，这是只做存活/表型筛选拿不到的。[【跳转到 10:50】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=650)

![Mosaic 平台：把 10–100 个患者模型混成一个异质性细胞池，在单个类器官/小鼠实验里加药，再做单细胞读出](<assets/Tahoe-100M：千兆级单细胞扰动图谱 ｜｜ Dr. Johnny Yu/00625.webp>)

## 四、Mosaic 的第一批结果：热图上既有已知突变，也有表型筛选看不到的生物学

### 4.1 原始热图一行就是几十个患者模型、数万个细胞

Mosaic 的原始数据是“数千种化合物 × 数百个患者模型”的热图：每一行是一种化合物，每一列是一个患者模型，深蓝色表示敏感。理论上这是一次“全对全”搜索，可以筛出海量“哪种药对哪种患者有效”的组合。[【跳转到 11:15】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=675) [【跳转到 11:20】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=680)

数据密度很惊人：只取热图里的一行，就代表一种药物、一只携带马赛克肿瘤的小鼠、生活在这只小鼠体内的 50–100 个患者模型，覆盖数百个关键驱动基因和癌症类型、数万个单细胞的全基因表达空间。[【跳转到 11:45】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=705) [【跳转到 12:07】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=727)

### 4.2 平台先复现已知生物学：敏感模型带着对应的驱动突变

作为 sanity check，讲者先看平台能不能复现已知生物学。UMAP 上每个簇来自不同的癌症模型，他们在三种药物条件下处理：DMSO 对照（无药）、靶向 KRAS G12C 的药物、靶向 RAF 激酶的药物，这些都是临床已知分子。[【跳转到 12:19】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=739) [【跳转到 12:44】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=764)

结果符合预期：vemurafenib 最敏感的模型带 BRAF V600E；ARS-1620 最敏感的模型带 KRAS G12C。用机器学习模型去预测致病驱动因素，也能从数据里提取出这些突变——说明数据里确实有可被模型学到的因果信号。[【跳转到 13:09】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=789)

### 4.3 PDX/类器官保留更多微环境，剂量给出连续响应梯度

Mosaic 不只做细胞系，还能做 **PDX（患者来源异种移植）** 和 **PDO（患者来源类器官）**。这些模型从未接触过塑料，可能只传了四次，离患者体内状态更近，保留了更完整的微环境多样性；讲者在四种 PDX/类器官模型里都做了 Mosaic 实验。[【跳转到 13:39】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=819) [【跳转到 13:49】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=829)

从 DMSO 到低、中、高剂量，UMAP 上的转录状态呈连续响应梯度：剂量越高，细胞状态偏离对照越远。[【跳转到 14:14】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=854)

### 4.4 反直觉现象：加药后线粒体转录本下降，耐药模型线粒体更少

数据还带出一个反直觉现象：药物处理后，所有模型里线粒体靶向转录本都显著减少。[【跳转到 14:39】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=879) [【跳转到 14:46】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=886)

对熟悉单细胞研究的人来说，这不容易解释：高线粒体转录本常意味着细胞快死了，但“低线粒体转录本”并没有那么直观。更奇怪的是，他们用传统实验构建了一个耐药模型，经过数月药物治疗仍保持耐药，测它的线粒体含量反而显著更低。[【跳转到 15:11】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=911) [【跳转到 15:36】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=936)

讲者强调，这正是转录组读出的价值：像 Broad 的 PRISM 这类表型筛选只能得到“敏感/不敏感”，而这里能进一步看到细胞内部发生了什么，提出新的机制假设。

### 4.5 转录组还能反推联合用药靶点

既然能看到药物上调了哪些基因，就可以反过来找联合用药的靶点。幻灯片点名 GPX4、促凋亡基因、mTOR/Raptor 等通路；在 G12C 模型上测试相应组合，能看到很强的协同效应。[【跳转到 16:01】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=961) [【跳转到 16:09】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=969)

讲者解释，联合疗法的搜索空间会从“线性”变成“平方级”：原来只需看药物 A、药物 B 各自的效果，现在要看所有两两组合的协同，组合数量爆炸；而有了转录组，就能先大幅缩小候选范围，再在实验里验证。[【跳转到 16:34】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=994) [【跳转到 16:59】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=1019)

## 五、Tahoe-100M 的规模与覆盖：50 个模型 × 1,200 个药物—剂量条件 = 1 亿细胞

讲者把 Tahoe-100M 称为一个里程碑：它不仅大，而且是一个统一、极其可复现、严格对照、低批次、专为药物发现设计的数据集。他认为这种“前沿规模 + 统一流程”的数据集，会像基础设施一样持续被挖掘很多年。[【跳转到 17:22】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=1042) [【跳转到 17:38】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=1058)

这里有一个容易被误读的口径。现场有人问“1,200 种治疗是单药还是组合”，讲者澄清：**这些处理都是单药**，这样药物和浓度带来的才是干净、独立的基准信号；组合当然也能做，而且组合会带来指数级的信息量，但 Tahoe-100M 这一版主要不是组合筛选。[【跳转到 18:03】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=1083) [【跳转到 18:28】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=1108)

规模可以拆成四个数字：**50 个癌症模型**（不同患者、不同起源器官，目标是覆盖全癌领域而不是深挖某一种癌）、**约 1,200 个药物—剂量条件**（400 种药物 × 3 个剂量）、**约 6 万次实验**（50 × 1,200）、**约 1 亿个细胞**。讲者说，无论模型系统数量、扰动次数还是数据集规模，都远超此前最大的全基因组 Perturb-seq 和 sci-Plex3 等药物基因组数据集；能做到这一点，靠的是 Parse 这类高通量组合索引技术。[【跳转到 18:53】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=1133) [【跳转到 19:18】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=1158) [【跳转到 19:43】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=1183)

![Tahoe-100M 的规模：50 个癌症模型、1,200 个药物处理、约 6 万次实验、1 亿细胞](<assets/Tahoe-100M：千兆级单细胞扰动图谱 ｜｜ Dr. Johnny Yu/01158.webp>)

> 口径补充：视频里的“1,200 个药物处理”指**药物—剂量条件**（400 种药物 × 3 个剂量），不是 1,200 种药；论文过滤后为 **379 种药物、1,135 个组合**。

### 5.1 50 个模型覆盖约 80% 的相关癌症基因

这 50 个模型不是随便挑的：每个模型有不同的致癌驱动因素，合起来基本覆盖约 80% 的相关癌症基因和驱动突变。讲者以 p53 为例——如果你关心 p53，数据里包含 p53 的多种变异，这些不是专门为某个项目加的，而是生物多重化检测自然覆盖到的。[【跳转到 20:08】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=1208) [【跳转到 20:17】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=1217) [【跳转到 20:42】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=1242)

### 5.2 药物偏向已获批或临床验证的分子

药物端也有取舍：Tahoe 主要聚焦**已获批或已在临床试验中验证**的分子，因为这类药物有大量安全性数据可以复用，也能直接回答“这个通路被打掉会怎样”。覆盖面包括 PI3K、JAK-STAT、mTOR、微管抑制剂（如化疗药）、DNA 合成与修复，以及 Hedgehog 等定制通路。[【跳转到 21:07】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=1267) [【跳转到 21:13】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=1273) [【跳转到 21:38】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=1298) [【跳转到 22:03】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=1323)

## 六、实验流程与组合索引：96 孔板加药 2–4 小时，第一轮条形码给药物、SNP 给细胞系

### 6.1 高度并行的 96 孔板流程

流程本身被拆成高度并行的步骤：50 个癌症模型先以高通量方式扩增，再接种到 96 孔板，**每个孔是一个独立的肿瘤样本**，作为生物重复；然后对每个孔加不同药物和浓度，处理 2–4 小时后移除药物。为什么是 2–4 小时？讲者说，这是足以让转录组发生机制性变化、但还没造成大规模细胞死亡的时间窗。[【跳转到 22:13】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=1333)

之后解离细胞，直接进入 **Parse Gigalab** 做高通量组合索引，把生物检测转成单细胞 RNA 测序文库。[【跳转到 22:38】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=1358) [【跳转到 23:03】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=1383)

![Tahoe-100M 的数据生成：96 孔板加药、解离、Parse Gigalab 条形码与单细胞建库](<assets/Tahoe-100M：千兆级单细胞扰动图谱 ｜｜ Dr. Johnny Yu/01333.webp>)

组合索引的关键是：第一轮条形码编码**药物处理**，同时给细胞做哈希（细胞哈希也集成在 Parse 流程里，不需要额外单独做）；后续轮次再把样品拆成单个细胞；细胞属于哪个患者模型，最后由 SNP 基因分型决定。[【跳转到 23:03】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=1383)

### 6.2 读段怎么拆：SNP + cDNA + 条形码 + UMI

具体到一条测序 read，可以拆成几段：**SNP**、**cDNA 插入片段**、**条形码**（处理 ID、细胞哈希）和 **UMI**。同一组条形码的 reads 归为一个细胞；第一条条形码给出药物处理条件；细胞系身份则来自 SNPs——不是简单数 reads，而是对每个单细胞做基因分型，再把它分配回原来的患者模型。[【跳转到 23:28】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=1408) [【跳转到 24:06】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=1446) [【跳转到 24:31】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=1471)

![读段解卷积：处理 ID 来自第一条条形码，细胞身份由哈希条形码与 SNP 基因分型共同确定](<assets/Tahoe-100M：千兆级单细胞扰动图谱 ｜｜ Dr. Johnny Yu/01446.webp>)

## 七、数据质量：UMAP 上簇就是模型，14 个批次不用校正，方差主要来自药物和剂量

### 7.1 遗传多重化干净，批次几乎不可见

UMAP 上的簇几乎就是一个个癌症模型，边界清楚，而且绝大多数细胞都直接来自对应患者，说明遗传多重化（混样后再拆开）做得足够干净。[【跳转到 24:56】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=1496) [【跳转到 25:21】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=1521)

更难得的是批次。单细胞数据整合最常见的问题就是大规模批次效应，但这里有 **14 个批次**，**不做任何批次校正**，UMAP 上也几乎看不到按批次分开的簇。[【跳转到 25:31】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=1531)

讲者顺势回答了一个方法论问题：为什么需要“前沿规模”的数据集，而不是生成一千个小数据集？因为如果数据不能统一，价值会大打折扣；全球最大的数据集如果完全没有批次效应，就说明统一流程本身是可行的。[【跳转到 25:56】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=1556)

![14 个批次的数据不做批次校正，UMAP 上仍几乎看不到批次分离](<assets/Tahoe-100M：千兆级单细胞扰动图谱 ｜｜ Dr. Johnny Yu/01531.webp>)

### 7.2 覆盖均匀，没有模型或药物被过度采样

覆盖也均匀：模型 × 药物热图没有大片空缺，没有某个模型或某种药物被过度采样，每个模型的细胞数也大致相当。这相当于又一层质量控制。[【跳转到 26:16】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=1576) [【跳转到 26:41】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=1601)

### 7.3 方差分解：药物与剂量是主信号

最后看方差来自哪里。按转录距离衡量，**药物×浓度**和**药物本身**的效应最大，细胞周期和细胞系的影响小得多。[【跳转到 26:52】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=1612) 剂量越高，转录距离越大；sci-Plex3 也观察到同样趋势。[【跳转到 27:17】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=1637)

讲者还横向比较了 pooled 基因扰动数据：把基因按非必需、未分类、必需来分，必需基因的信号最强，说明同一个“转录距离”指标也能捕捉到真实的生物学强度。这些比较说明数据集能把“多患者效应”作为主要研究对象，而不被批次和细胞系差异淹没。[【跳转到 27:42】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=1662) [【跳转到 28:07】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=1687)

![方差分解：药物与剂量是转录距离的主要来源，细胞周期和细胞系的影响小得多](<assets/Tahoe-100M：千兆级单细胞扰动图谱 ｜｜ Dr. Johnny Yu/01662.webp>)

## 八、用例一：沙奎那韦的转录组最近邻是心脏药物

讲者说，接下来是最令人兴奋的部分：这份数据集能做什么。他先讲了沙奎那韦（Saquinavir）的故事。

沙奎那韦是罗氏 1995 年上市的 HIV 蛋白酶抑制剂，也是首个获批的 HIV 蛋白酶抑制剂；它作为鸡尾酒疗法的一部分，把艾滋病相关死亡率压低了 60%–80%，让艾滋病从“死刑判决”变成可以主动管理的疾病。[【跳转到 28:49】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=1729) [【跳转到 29:14】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=1754)

但 2016 年，在临床使用近 21 年后，FDA 和临床医生发现问题：它与异常心律和其他心脏症状相关；2019 年罗氏将其撤市。[【跳转到 29:31】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=1771) [【跳转到 29:56】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=1796)

把它放进 Tahoe-100M 做**药物相似性分析**——把未知药物与数据库里已有临床表型的药物比较，看转录组最像谁。最相似的不是抗 HIV 药，而是**去甲肾上腺素**和**维兰特罗（Vilanterol）**：两者都是肾上腺素能受体激动剂，临床用于心脏相关疾病。[【跳转到 30:02】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=1802) [【跳转到 30:27】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=1827)

（字幕把 Vilanterol 误写成“缬沙坦”，以幻灯片为准。）

![沙奎那韦在转录组空间中最接近去甲肾上腺素与维兰特罗，提示其心脏相关副作用](<assets/Tahoe-100M：千兆级单细胞扰动图谱 ｜｜ Dr. Johnny Yu/01827.webp>)

讲者感叹：这份数据集一次分析就复现了临床医生用二十年、靠人体实验才发现的关联。[【跳转到 30:52】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=1852) [【跳转到 31:09】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=1869) 这里他插了一段题外话：团队本可以不公开这份数据，但他们自己研究时发现内容太丰富，认为它会是社区的重要资源，于是选择开源；现在每天都有很多人在分析它。[【跳转到 31:25】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=1885) [【跳转到 32:40】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=1960) [【跳转到 33:05】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=1985)

机制也说得通：这类心脏药物是 β 肾上腺素能受体激动剂，关键下游节点之一是 CREB 磷酸化（pCREB）。DMSO 对照几乎没有 pCREB，去甲肾上腺素如预期诱导 pCREB；沙奎那韦处理也出现同样的 pCREB 诱导，等于给相似性结果补了一条直接机制证据。[【跳转到 33:10】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=1990) [【跳转到 33:35】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=2015) [【跳转到 34:00】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=2040)

讲者还专门澄清“这只是结构相似吗”：去甲肾上腺素和维兰特罗的结构确实相近，但沙奎那韦与它们在化学结构上相差很远。结构很重要，但只是药物作用的一部分；只靠分子对接的 AI 模型，不一定能轻易发现这条关联。[【跳转到 34:25】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=2065) [【跳转到 34:43】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=2083) [【跳转到 35:08】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=2108)

## 九、用例二：用复合基因集筛 MHC-I 上调剂

第二个用例不生成新数据，只是换一种问法。肿瘤细胞常把 MHC-I 从表面移除以躲开免疫识别，这也是免疫疗法无效的常见原因；如果能找到让 MHC-I 呈递/转运回到表面的药物，免疫细胞就更容易识别肿瘤。[【跳转到 35:33】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=2133) [【跳转到 35:38】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=2138) [【跳转到 36:03】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=2163)

作者没有只看单个基因，而是同时看两个基因集：一个刻画 MHC-I 呈递/转运，另一个刻画干扰素 α 响应；他们从文献里精选了约 50 个基因，再跨基因集给药物打分。[【跳转到 36:28】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=2188) [【跳转到 36:33】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=2193)

排在前面的既有已知的 MEK 抑制剂（此前已在临床前/临床研究中显示可上调 MHC-I，并与免疫疗法联用），也有许多新化合物，可能直接进入临床试验或作为化学骨架继续优化。[【跳转到 36:58】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=2218) [【跳转到 37:23】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=2243)

他们随后用 FITC 标记的抗 MHC-I 抗体做传统验证：部分候选在加药三天后显著提高细胞表面 MHC-I，效果与临床验证过的阳性对照相当。[【跳转到 37:31】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=2251) [【跳转到 37:56】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=2276)

讲者把方法推广到更一般的情形：只要你能把关心的表型定义成“哪些基因该升、哪些该降”，无论是自定义 signature、疾病 vs 健康状态，还是多基因集组合，都可以用这套数据做多因素筛选，优先挑新骨架、活性化合物或老药新用。[【跳转到 38:15】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=2295) [【跳转到 38:40】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=2320)

## 十、用例三：把药物扰动与基因扰动拼起来，做靶点解卷积和结构优化

第三个用例把两类数据接起来：一边是药物扰动（Tahoe-100M / Mosaic），另一边是基因扰动（CROP-seq 这类敲除筛选，来自外部数据集）。核心思路是：如果药物扰动和基因扰动发生在同一个癌症模型里，就可以把转录组当作桥梁，比较“药物引起的状态变化”和“敲掉某个基因引起的状态变化”，从而把药物映射到靶点，或反过来为某个靶点找药。[【跳转到 38:52】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=2332) [【跳转到 39:00】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=2340) [【跳转到 39:25】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=2365)

讲者特别强调，必须做**配对分析**：药物扰动和基因扰动要在同一个癌症模型里比较，否则跨模型的差异会淹没信号；他们只取两边都覆盖的同一批模型。[【跳转到 43:10】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=2590) [【跳转到 43:15】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=2595)

这带来两个应用。第一是**靶点解卷积**：对每个药物，找到遗传空间里最相似的基因敲除，从而推断它作用在哪个基因/通路上。第二是**遗传表型模拟指导结构优化**：比如你想要 CDK4 的效应、同时避开 CDK6，就定义“靠近 CDK4 状态、远离 CDK6 状态”的方向，再在化合物里筛最符合这个方向的分子——相当于在传统构效关系上叠加一层遗传优化。[【跳转到 39:50】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=2390) [【跳转到 40:15】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=2415) [【跳转到 40:40】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=2440)

![遗传表型模拟指导药物发现：整合药物扰动与基因敲除，做靶点解卷积和结构优化](<assets/Tahoe-100M：千兆级单细胞扰动图谱 ｜｜ Dr. Johnny Yu/02440.webp>)

具体例子：trametinib 和 RMC-6236 都作用在 MAPK 通路，但靶点位于级联的不同位置；分析 top10 最相似的基因敲除，几乎全在 MAPK 通路。[【跳转到 43:48】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=2628) [【跳转到 44:13】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=2653) [【跳转到 44:28】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=2668) 讲者说，在可能的两万个基因里，前十个有八个属于 MAPK，已经足以较好推断“这是一个 MAPK 靶向剂”；而且靶向 MAPK 不同节点的药物最终会汇聚到相同信号，这一点很重要。[【跳转到 44:33】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=2673) [【跳转到 44:58】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=2698)

更有意思的是一个“标注错了”的分子：它被标注为 ATR 抑制剂（靶向 DNA 复制/修复），但转录相似性分析显示 top10 里有九个落在 MAPK 通路。用 pERK 做验证：DMSO 下 pERK 高，传统 MEK 抑制剂会关掉信号；这个“ATR 抑制剂”也完全消除了 pERK 信号——说明它实际表现出 MAPK 通路抑制机制，是此前文献不知道的新机制。[【跳转到 45:23】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=2723) [【跳转到 45:28】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=2728) [【跳转到 45:53】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=2753) [【跳转到 46:18】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=2778) [【跳转到 46:43】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=2803)

讲者说，这意味着只要有一个化合物库，就可以把任何机制追踪到特定基因或通路，代价只是把药物扰动数据和患者/基因扰动数据整合起来。[【跳转到 46:43】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=2803)

## 十一、AI agent 与基础模型：让这份图谱可以用自然语言查询

讲者说，三个用例只是开始，数据里还有大量生物学等待挖掘。他接着介绍团队如何用 AI 工具降低使用门槛：过去需要生物信息学家、实验肿瘤学家和实验室验证人员组成高度专注的团队；在 AI 时代，他们想看看 agent 能走多远。[【跳转到 47:08】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=2828) [【跳转到 47:30】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=2850)

他们做了一个自然语言查询 agent：用一句话提问，它会查阅科学文献、理解问题、生成并运行 Python 代码，最后给出图表和结论。关键点是它**不是让聊天模型“看着数据瞎猜”**，而是生成可执行代码来做精确分析，因此结果可追溯、可复现。[【跳转到 47:55】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=2875) [【跳转到 48:02】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=2882) [【跳转到 48:27】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=2907) [【跳转到 48:52】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=2932)

他现场演示了 MHC-I 那个问题：“哪些药物在干扰素 α 和 MHC-I 呈递中上调最显著？”agent 一边读数据、一边生成中间图表，查文献、迭代分析，最后筛出可测试的药物，并标出哪些是已知、哪些是未知；结果与手工分析找到的是同一批分子。[【跳转到 49:10】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=2950) [【跳转到 49:15】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=2955) [【跳转到 49:40】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=2980)

外部团队也在用这份数据训练基础模型。ARC Institute 的 **STATE** 模型部分基于 Tahoe-100M，讲者说它接近“生物领域的 GPT-2”时刻：能在分布外做细胞响应预测，这是以前做不到的。[【跳转到 51:22】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=3082) [【跳转到 51:39】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=3099) [【跳转到 52:09】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=3129)

讲者在结尾把定位说清楚：Tahoe-100M 是一个**开源药物发现资源**，能回答多种生物学、癌症和药物问题，也能支撑下一代虚拟细胞基础模型。[【跳转到 52:26】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=3146) [【跳转到 52:51】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=3171)

问答里，讲者补充 Tahoe 自己也在训练基础模型（他说下个月会发布），并把它定位为“跨癌症模型、跨患者泛化”的工具：给一个没见过的患者、它的转录状态和遗传背景，模型能预测某种药物会把它带向什么状态；他们还希望把癌症之外的正常细胞、不同疾病数据也整合进来，验证分布外泛化。[【跳转到 53:51】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=3231) [【跳转到 54:19】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=3259) [【跳转到 54:30】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=3270) [【跳转到 55:07】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=3307) [【跳转到 55:37】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=3337)

## 十二、边界与下一步：2–4 小时快照、模态有限、空间转录组

问答里还谈了一个方法边界：有人问遗传扰动数据通常较嘈杂，药物效应与遗传效应还能对上吗？讲者说效果“惊人地有效”，并举例：HDAC 抑制剂最相似的基因大多与染色质重塑有关，普伐他汀对应 FDFT1，PI3K 抑制剂对应 PI3K 基因。他的经验是数据越干净，这种关联越可靠；公开的遗传扰动数据可以用，但大规模、自主生成、可重复的数据效果最好。[【跳转到 56:16】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=3376) [【跳转到 56:31】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=3391) [【跳转到 56:52】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=3412) [【跳转到 57:18】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=3438) [【跳转到 57:43】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=3463)

接着是模态范围：主体是 50 个癌症模型和小分子；虽然也试过抗体、ADC、降解剂、组合乃至肽类，平台并不受模态限制，但离“所有模态、所有疾病”还很远。[【跳转到 58:26】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=3506) [【跳转到 58:38】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=3518) [【跳转到 59:15】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=3555) [【跳转到 59:30】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=3570)

还有一条是时间窗口：从实验设计就能看出，这是加药 2–4 小时的转录组快照，捕获的是早期响应，不是长期耐药或更晚的细胞命运。[【跳转到 22:13】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=1333)

最后，他给社区列了三个可以做的方向：一是用这份数据回答各种生物学问题；二是用它训练、调整基础模型架构；三是继续扩展平台和数据生成——包括更大规模的基因组扰动，以及明年的**空间转录组**。空间读数还能看细胞间通讯，例如免疫细胞与不同癌细胞在特定药物环境下的交流，这是下一步很强大的方向。[【跳转到 59:35】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=3575) [【跳转到 60:18】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=3618) [【跳转到 60:29】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=3629) [【跳转到 60:54】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=3654) [【跳转到 61:19】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=3679) [【跳转到 61:44】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=3704) [【跳转到 61:52】](https://www.bilibili.com/video/BV1khg5z9EpZ/?t=3712)

## 小结

- **Tahoe-100M 是药物扰动的规模化代表**：50 个癌症模型、约 1,200 个药物—剂量条件（400 种药物 × 3 个剂量）、约 6 万次实验、约 1 亿细胞；论文过滤后为 379 种药物、1,135 个组合。
- **Mosaic + Parse 组合索引**把多个患者模型混成“马赛克肿瘤”，用条形码编码药物处理与细胞哈希，再用 SNP 分型把细胞分配回细胞系，这是规模化的关键。
- 数据质量体现在三件事：14 个批次无需校正、模型与药物覆盖均匀、方差主要来自药物和剂量而非细胞系或细胞周期；这也是“一个前沿数据集”优于“很多小数据集”的理由。
- 三个用例展示了图谱的价值：沙奎那韦的心脏副作用（并用 pCREB 验证机制）、MHC-I 上调剂筛选、药物—基因整合做靶点解卷积与结构优化。
- 它也是虚拟细胞的基础数据：可用于药物响应预测、跨患者泛化、自然语言分析 agent 与基础模型；边界是 2–4 小时快照、以癌症小分子为主，空间转录组是下一步。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| Tahoe-100M | 50 个癌症模型 × 约 1,200 个药物—剂量条件 × 约 1 亿细胞的单细胞药物扰动图谱。 |
| Mosaic | 把多个患者来源肿瘤模型混成一块“马赛克肿瘤”，在一次体内/类器官实验中一起加药。 |
| PDX / PDO | 患者来源异种移植 / 类器官，传代少、保留更多患者肿瘤的微环境。 |
| 组合索引 | 用多轮条形码把大量样本混进一次测序，再在分析时拆开。 |
| SNP 基因分型 | 读取每个细胞的单核苷酸多态性，把它分配回原来的细胞系/患者模型。 |
| 药物相似性分析 | 比较药物在转录组空间中的效应向量，找出机制或表型最接近的已知药物。 |
| 方差分解 | 把细胞间转录距离拆到药物、剂量、细胞系、细胞周期等因素上，判断主信号来自哪里。 |
| 遗传表型模拟 | 用基因敲除的转录效应去匹配药物效应，从而推断药物靶点或指导结构优化。 |
