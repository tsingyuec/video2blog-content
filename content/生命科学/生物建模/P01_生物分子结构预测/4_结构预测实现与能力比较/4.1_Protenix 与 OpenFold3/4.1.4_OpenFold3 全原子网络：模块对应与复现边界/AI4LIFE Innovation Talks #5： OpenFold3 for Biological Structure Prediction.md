# AI4LIFE Innovation Talks #5： OpenFold3 for Biological Structure Prediction

> 视频来源：[YouTube《AI4LIFE Innovation Talks #5: OpenFold3 for Biological Structure Prediction》](https://www.youtube.com/watch?v=S6H_INT5hzc)（42:44），AI for Life 开源社区第五期创新讲座。主讲人 Jennifer Wei 博士（哈佛化学物理博士、前 Google DeepMind）是 OpenFold 联盟 **OpenFold3 技术负责人**。讲座系统拆解了 OpenFold3——AlphaFold3 的开源复刻——的使命、架构、输出解读、路线图，并附 Vecura 平台 3 分钟实操演示与约 20 分钟 Q&A。视频字幕为英文自动生成，本文基于文稿整理翻译；文中数字与结论均出自视频内容，可点击时间戳回看核对。

## 本讲要解决的核心问题（SCQA）

**背景**：结构预测已成为药物发现的基础工具——想设计药物，先要知道靶点蛋白长什么样。但最强的 AF3 类模型普遍以专有平台形式提供服务：每天有查询配额、权重看不见、训练代码更不用想。

**冲突**：学术界和工业界都需要能**自己训练、微调、扩展**的模型：在自己的数据上微调、把预测接入自己的管线、甚至改造模型本身。专有平台给不了这种自由；而自己复现 AlphaFold3，架构复杂、数据与训练管线都要从零搭，门槛极高。

**疑问**：社区能不能有一个既达到 AF3 水准、又**全链路开放**（数据集 + 训练代码 + 模型代码 + 权重）的替代品？

**回答（中心思想）**：**OpenFold3 用"全开放"回答了这个问题**——训练数据集、训练管线、模型代码、参数权重全部公开，2025 年 Q3 发布以来社区活跃贡献（化学转向 steering、口袋约束、模板管线修复等大特性都来自社区 PR）；模型本体沿用 AlphaFold3 的"Pairformer 三角更新 + 扩散生成"架构，输入端集成 ColabFold 一键获取 MSA，输出端提供 pTM/ipTM/pLDDT 全套置信度；安装已简化到 PyPI 两条命令，并已规划 OpenBind Zero、V1 版本、化学转向与水分子建模等路线。本讲由技术负责人逐层拆解，并给出 GPU 需求、抗体预测策略、下游工具打通等一手实践建议。

## 一、OpenFold 联盟：造一个"我们能掌控命运"的模型

[【跳转到 02:49】](https://www.youtube.com/watch?v=S6H_INT5hzc&t=169)

OpenFold 的使命一句话：**为蛋白质建模与设计交付开源、高质量的机器学习模型**。开源在这里不是口号，而是四件实打实的事（[【跳转到 02:49】](https://www.youtube.com/watch?v=S6H_INT5hzc&t=169)）：

1. **数据集开放**：所有训练数据集公开，任何人可用；
2. **训练管线开放**：不只开源模型代码，连训练代码也开源——可以自己跑训练、审查训练代码、随手修改；
3. **参数权重开放**：拿到权重就能跑推理；
4. **方向可参与**：模型引入什么组件、增加什么能力、用什么数据训练，由社区共同决定。

用主讲人的话说："社区应该拥有一个**我们自己掌控命运**的模型。"

### 1.1 组织形态：OMSF 旗下的项目群

OpenFold 是开源分子软件基金会 **OMSF（Open Molecular Software Foundation）** 托管的项目之一。OMSF 旗下还有 **OpenADMET**（药物 ADMET 性质预测）等项目，共同推进开源科学软件。想参与或了解更多，可从 OMSF 的项目列表进入（[【跳转到 03:44】](https://www.youtube.com/watch?v=S6H_INT5hzc&t=224)）。

### 1.2 联盟的三个科研方向

[【跳转到 04:20】](https://www.youtube.com/watch?v=S6H_INT5hzc&t=260)

OpenFold 联盟目前有三条线：

- **OpenFold3**（主线）：由哥伦比亚大学 Mohammed AlQuraishi 教授领导，即本讲主角；
- **稳定性测量**：由西北大学 Gabriel Rocklin 教授领导，已发展出**一次测量数百万蛋白质稳定性**的技术，而且数据集中蛋白是可控设计的——大量围绕**点突变**构建，目的是让模型学会"突变如何影响稳定性、是否导致错误折叠"。主讲人直言：这是 AlphaFold3 类模型**目前最缺的能力**；
- **蛋白质设计**：近期与 David Baker 实验室（Institute for Protein Design）开启合作，方向偏蛋白质设计。

## 二、架构拆解：AlphaFold3 的"输入—Pairformer—扩散"三段式

[【跳转到 05:28】](https://www.youtube.com/watch?v=S6H_INT5hzc&t=328)

OpenFold3 基于 Google DeepMind 2024 年发布的 **AlphaFold3**。沿革是这样的：AlphaFold2 只能预测蛋白质（先是单链，后扩展到多链 multimer）；**AlphaFold3 把覆盖面扩展到更宽的化学空间——蛋白质、小分子、核酸都能一起预测**。OpenFold3 的目标就是把这个能力开源复刻。

![OpenFold3 基于 AlphaFold3：从"仅蛋白质"扩展到蛋白质 + 小分子 + 核酸的共折叠](assets/AI4LIFE%20Innovation%20Talks%20%235：%20OpenFold3%20for%20Biological%20Structure%20Prediction/00328.webp)

主讲人坦诚说明：模型很大、组件很多，本讲只讲能帮你建立直觉的关键点。想深入可读她在文稿中推荐的 Elana Simon 与 Jake Silberg 的交互式博客（[【跳转到 06:48】](https://www.youtube.com/watch?v=S6H_INT5hzc&t=408)）。

### 2.1 整体结构图：一张图看全流程

[【跳转到 06:43】](https://www.youtube.com/watch?v=S6H_INT5hzc&t=403)

![AlphaFold3 整体架构图：左侧三类输入，中间 Pairformer 主干，右侧扩散模块输出结构](assets/AI4LIFE%20Innovation%20Talks%20%235：%20OpenFold3%20for%20Biological%20Structure%20Prediction/00403.webp)

这张架构图是全讲的地图：左边的**输入处理**，中间的 **Pairformer 主干**，右边的**扩散模块**——下面逐段展开。

### 2.2 三类输入：MSA、模板、构件

[【跳转到 07:15】](https://www.youtube.com/watch?v=S6H_INT5hzc&t=435)

模型的输入可以概括为三块：

1. **MSA（多序列比对）**：对输入序列做进化史检索，回答"你的序列在进化上和哪些蛋白相似"。它提供的是**模式上下文**——不一定有结构，但能告诉模型这类序列里哪些位置保守、哪些常变。
2. **模板（templates）**：从 PDB 里找与目标序列相似的已知结构作为参考。注意这**不是同源建模（homology modeling）**：同源建模是把已知结构直接改造出答案；而这里模板只是被模型**当作输入特征**加工，最终结构仍由模型自己预测（[【跳转到 08:05】](https://www.youtube.com/watch?v=S6H_INT5hzc&t=485)）。
3. **构件（building blocks）**：组成体系的"零件清单"——氨基酸残基，以及可能存在的配体（视频以血红素 heme 为例）。毕竟做结构预测时没有现成结构，但"用了哪些零件"是知道的（[【跳转到 08:52】](https://www.youtube.com/watch?v=S6H_INT5hzc&t=532)）。

![三类输入：多序列比对（进化信息）、模板（相似结构）、构件（氨基酸与配体）](assets/AI4LIFE%20Innovation%20Talks%20%235：%20OpenFold3%20for%20Biological%20Structure%20Prediction/00435.webp)

### 2.3 构件的"粗结构"：RDKit 构象生成

[【跳转到 09:17】](https://www.youtube.com/watch?v=S6H_INT5hzc&t=557)

小分子配体只有二维描述怎么办？模型用 **RDKit** 为构件生成**构象（conformer）**——即粗略的三维摆位。之后，MSA、模板、构象三路信息一起送入**输入嵌入器（input embedder）**，生成模型后续要用的初始特征。输入处理到此结束。

![RDKit 为小分子构件生成三维构象，作为模型输入之一](assets/AI4LIFE%20Innovation%20Talks%20%235：%20OpenFold3%20for%20Biological%20Structure%20Prediction/00557.webp)

### 2.4 Pairformer：每个节点听"两个邻居"的话

[【跳转到 09:47】](https://www.youtube.com/watch?v=S6H_INT5hzc&t=587)

模型主干是 transformer——在 AF3 里叫 **Pairformer**。要带走的关键设计是**三角更新（triangle update）**：更新每个节点时，不只看紧邻的下游层，而是同时看**两个邻居**——注意力机制里的每个节点都接收来自两个方向的信息。直观理解：残基 i、j、k 之间的两两关系构成"三角"，信息沿三角的边互相校正，这对几何推理极其重要。

![Pairformer 主干：三角更新让每个节点接收两个邻居的信息](assets/AI4LIFE%20Innovation%20Talks%20%235：%20OpenFold3%20for%20Biological%20Structure%20Prediction/00587.webp)

代价也很直白：算全这些两两相邻关系是 **O(N³)** 的开销（N 为体系规模）——这正是这类模型"贵"的核心原因之一。但正是这套设计让 AlphaFold2、以及沿用同架构的 AlphaFold3 如此成功（[【跳转到 10:32】](https://www.youtube.com/watch?v=S6H_INT5hzc&t=632)）。

![三角更新示意：两两相邻关系的计算开销为 O(N³)](assets/AI4LIFE%20Innovation%20Talks%20%235：%20OpenFold3%20for%20Biological%20Structure%20Prediction/00598.webp)

### 2.5 扩散模块：把"图像生成"搬进原子世界

[【跳转到 10:53】](https://www.youtube.com/watch?v=S6H_INT5hzc&t=653)

Pairformer 的输出是**潜在表示（latent representation）**，交给**扩散模块（diffusion module）**生成最终结构。扩散模型与 Stable Diffusion 等图像生成模型同源：训练时给样本加噪、再学习去噪；生成时从纯噪声出发一步步"雕"出结果。AF3 把同一套技术搬进三维空间——**撒进空间里的不是随机像素，而是随机原子**，再逐步去噪成结构（[【跳转到 11:06】](https://www.youtube.com/watch?v=S6H_INT5hzc&t=666)）。

![潜在表示送入扩散模块：与 Stable Diffusion 同源，只是把随机像素换成随机原子](assets/AI4LIFE%20Innovation%20Talks%20%235：%20OpenFold3%20for%20Biological%20Structure%20Prediction/00653.webp)

扩散模块还有第二个作用：自带**置信度头（confidence head）**，对每个候选结构自评"我有多确信这是真实结构"——因此可以生成多个候选再按置信度排序（[【跳转到 11:43】](https://www.youtube.com/watch?v=S6H_INT5hzc&t=703)）。

![扩散模块：把随机原子逐步去噪为结构，并输出自评置信度](assets/AI4LIFE%20Innovation%20Talks%20%235：%20OpenFold3%20for%20Biological%20Structure%20Prediction/00666.webp)

## 三、看懂输出：两个实例 + 一套置信度语言

### 3.1 例一：激酶——三次采样几乎完美对齐实验结构

[【跳转到 12:27】](https://www.youtube.com/watch?v=S6H_INT5hzc&t=747)

第一个例子是激酶（kinase）预测：红色为对应 PDB 实验结构，不同深浅的蓝色为 OpenFold3 的**三次扩散采样**（同一 seed、多次输出）。结果：**口袋里的配体与实验结构几乎完美对齐**——这是一个"预测得很好"的案例。

![激酶预测：红色为 PDB 实验结构，三种蓝色为三次扩散采样，口袋配体几乎完美对齐](assets/AI4LIFE%20Innovation%20Talks%20%235：%20OpenFold3%20for%20Biological%20Structure%20Prediction/00747.webp)

### 3.2 置信度语言：pTM / ipTM / pLDDT

[【跳转到 13:04】](https://www.youtube.com/watch?v=S6H_INT5hzc&t=784)

OpenFold3 提供 AlphaFold 风格的全套指标：pTM、ipTM、平均 pLDDT 等，并有完整文档可查。重点理解 **pLDDT**：它是**逐残基的局部置信度**——模型对"这个原子/残基的局部位置摆得对不对"的自我打分；**平均 pLDDT** 则是对全体残基的聚合。

![三次采样的置信度汇总：pTM、ipTM、平均 pLDDT 与逐残基 pLDDT](assets/AI4LIFE%20Innovation%20Talks%20%235：%20OpenFold3%20for%20Biological%20Structure%20Prediction/00784.webp)

### 3.3 例二：无实验覆盖的区域——模型会"自首"

[【跳转到 14:10】](https://www.youtube.com/watch?v=S6H_INT5hzc&t=850)

第二个例子更有教育意义：图中绿色的 PDB 晶体结构只覆盖了蛋白的一小段，其余长链在实验中**完全没有解析**。对这段"没见过的区域"，模型基本是在猜——而且它自己知道：**给这些长链打出了很低的逐残基 pLDDT**，整个结构属于"试探性答案（tentative）"。主讲人提醒：校准并非完美，但足以给你一个 ballpark——**哪些区域可信、哪些区域是猜测**。

![PDB（绿色）只覆盖部分蛋白：模型对未解析的长链给出低 pLDDT](assets/AI4LIFE%20Innovation%20Talks%20%235：%20OpenFold3%20for%20Biological%20Structure%20Prediction/00850.webp)

### 3.4 Runs 'N' Poses 基准：越像训练集，预测越好

[【跳转到 15:07】](https://www.youtube.com/watch?v=S6H_INT5hzc&t=907)

聚合评估用 **Runs 'N' Poses** 数据集——专门按"与训练集的相似度"分组来衡量模型表现。OpenFold3 训练数据部分来自 PDB；Runs 'N' Poses 把查询按与 PDB 训练集的（口袋）相似度分组：右侧高相似、左侧低相似。结论不出意料：**查询与训练集越相似，性能越好**；对训练分布之外的查询，模型会更吃力（[【跳转到 16:22】](https://www.youtube.com/watch?v=S6H_INT5hzc&t=982)）。因此"如何提升低相似度区间的预测"是当前活跃的研究方向（[【跳转到 16:47】](https://www.youtube.com/watch?v=S6H_INT5hzc&t=1007)）。

![Runs 'N' Poses 基准：按与 PDB 训练集相似度分组，相似度越高性能越好](assets/AI4LIFE%20Innovation%20Talks%20%235：%20OpenFold3%20for%20Biological%20Structure%20Prediction/00907.webp)

## 四、路线图：安装、社区、新模型与新能力

### 4.1 工程体验：两条命令装好

[【跳转到 17:28】](https://www.youtube.com/watch?v=S6H_INT5hzc&t=1048)

开发期做了大量"减法"：过去安装 OpenFold 要走很长的流程，现在已上架 **PyPI**，安装 + 验证安装就是两条命令的事（[【跳转到 17:53】](https://www.youtube.com/watch?v=S6H_INT5hzc&t=1073)）。

![OpenFold3 安装已简化为 PyPI 两条命令](assets/AI4LIFE%20Innovation%20Talks%20%235：%20OpenFold3%20for%20Biological%20Structure%20Prediction/01048.webp)

### 4.2 社区贡献已经"挑大梁"

[【跳转到 17:58】](https://www.youtube.com/watch?v=S6H_INT5hzc&t=1078)

2025 年 Q3 发布以来，社区 PR 与 issue 持续涌入，而且不是小修小补：**立体化学转向（stereochemistry steering）、口袋约束（pocket constraints）、模板管线的重要修复**等大特性都来自社区贡献。

![OpenFold3 社区贡献时间线：立体化学转向、口袋约束等大特性来自社区 PR](assets/AI4LIFE%20Innovation%20Talks%20%235：%20OpenFold3%20for%20Biological%20Structure%20Prediction/01078.webp)

### 4.3 模型路线：OpenBind Zero 已发，V1 在路上

[【跳转到 18:37】](https://www.youtube.com/watch?v=S6H_INT5hzc&t=1117)

- 本讲展示的结果基于 **Preview 2**；**OpenBind Zero** 在讲座前一周刚发布——与 OpenFold3 同族，但训练数据截止时间从 2021 年推进到 **2025 年**，已有官方博客可读；
- **V1** 计划 2025 年 Q4 发布，会引入更多更新与更好的采样，预期进一步抬升性能。

### 4.4 微调改造与三大新能力方向

[【跳转到 19:02】](https://www.youtube.com/watch?v=S6H_INT5hzc&t=1142)

微调文档已有，但流程偏长、依赖多、中间文件多；正在做"一站式"改造——**用户只需给一个 CIF 文件目录，其余全托管**。能力侧三个方向（[【跳转到 19:27】](https://www.youtube.com/watch?v=S6H_INT5hzc&t=1167)）：

1. **稳定性数据**：把 Rocklin 的百万级稳定性数据集用于训练，补上 AF3 类模型"不懂点突变"的短板；
2. **亲和力（affinity）**：结合强度预测——本系列另一场活动的主角正是做这件事的 AQAffinity；
3. **关键水分子**：目前训练集普遍排除水，模型也不摆放水；但活性位点里有些水是"关键角色"，计划让模型学会放置关键水。

## 五、三分钟上手：在 Vecura 浏览器里跑 OpenFold3

[【跳转到 21:17】](https://www.youtube.com/watch?v=S6H_INT5hzc&t=1277)

讲座现场播放了 Vecura 平台的 3 分钟演示。**Vecura** 是一个云端工作区（workspace），OpenFold3 已上架其中，**浏览器内即可运行**，无需本地 GPU 驱动、conda 环境或命令行比对工具（[【跳转到 21:42】](https://www.youtube.com/watch?v=S6H_INT5hzc&t=1302)）。演示覆盖两个典型案例（[【跳转到 22:07】](https://www.youtube.com/watch?v=S6H_INT5hzc&t=1327)）：

1. **泛素（ubiquitin，76 氨基酸）× no-MSA 模式**：只给序列、不跑比对搜索、不带额外文件，几秒内得到完整三维结构——适合快速试水；
2. **T4 溶菌酶 + 配体 × upload-A3M 模式**：上传预先算好的 **A3M 比对文件**提供进化信息（通常能提升精度），配体以 **SMILES 字符串**给出，提交即可运行。

OpenFold3 不只预测单蛋白：**多链复合物、蛋白-小分子、蛋白-DNA/RNA** 都可在同一入口一站式提交。

![Vecura 演示：泛素 76 氨基酸 no-MSA 模式，数秒得到三维结构](assets/AI4LIFE%20Innovation%20Talks%20%235：%20OpenFold3%20for%20Biological%20Structure%20Prediction/01327.webp)

![Vecura 演示：T4 溶菌酶 + 配体，上传 A3M 比对文件提供进化信息以提升精度](assets/AI4LIFE%20Innovation%20Talks%20%235：%20OpenFold3%20for%20Biological%20Structure%20Prediction/01352.webp)

## 六、Q&A 精华：开源、硬件、抗体、冲突、下游与学习路径

### 6.1 为什么要坚持开源

[【跳转到 24:07】](https://www.youtube.com/watch?v=S6H_INT5hzc&t=1447)

问：专有平台有每日配额、权重不可见，OpenFold3 全开源对学术与工业实验室意味着什么？答：这正是联盟成立的初衷——社区要有一个能"随便折腾"的模型：**用自己的数据再训练、换新数据集训练都行**，代码与数据全开放。这不仅利好个体，更让整个社区变强：大家共享发现，一起把模型做得更好。

### 6.2 推理硬件：GPU 显存 ≥ 40 GB，最长约 4000 残基

[【跳转到 25:22】](https://www.youtube.com/watch?v=S6H_INT5hzc&t=1522)

大复合物的推理很吃资源：**CPU 跑不动，需要 GPU，显存至少 40 GB 左右**。提供**低内存模式（low-memory mode）**预设：把更多中间结果写出去、需要时重算——用更长的运行时间换取更低的显存峰值。当前容量上限视序列而定约 **4000 残基**（该测试在 80 GB 显存的机器上完成）。

### 6.3 MSA 与 ColabFold：浅 MSA 很敏感，抗体的正确姿势是多采样

[【跳转到 26:37】](https://www.youtube.com/watch?v=S6H_INT5hzc&t=1597)

OpenFold3 内置了 **ColabFold 服务器**对接：查询序列直接发给 ColabFold 拿回 MSA 与模板，无需自建序列数据库、自装比对软件（[【跳转到 27:02】](https://www.youtube.com/watch?v=S6H_INT5hzc&t=1622)）。但要清楚：**浅 MSA（同源序列少）会显著拉低预测质量**。最典型的是**抗体**——抗体需要序列与结构多样性才能发挥功能，天然缺乏进化约束，MSA 质量差，预测天然更难（[【跳转到 27:52】](https://www.youtube.com/watch?v=S6H_INT5hzc&t=1672)）。实践方案：**大量采样 + 按置信度过滤**，这是抗体预测的通行做法（[【跳转到 28:17】](https://www.youtube.com/watch?v=S6H_INT5hzc&t=1697)）。

### 6.4 复合物的空间冲突：基线无校正，"化学转向"在路上

[【跳转到 28:42】](https://www.youtube.com/watch?v=S6H_INT5hzc&t=1722)

问：多链复合物如何保持坐标精度、避免原子碰撞？答：AF3 基线模型其实**没有专门的防碰撞机制**，靠的是从 PDB 学到的先验——能复现螺旋、口袋和配体的合理摆位。**Boltz 与 Protenix 等同类模型已加入额外的冲突惩罚组件**：在扩散融合时刻起作用，属于"建模期干预"而非力场优化。OpenFold 正在加入同类**化学转向（chemical steering）**能力；更远期可能提供力场优化选项，帮助精修最终结构（[【跳转到 29:57】](https://www.youtube.com/watch?v=S6H_INT5hzc&t=1797)）。

### 6.5 下游打通：OpenFE 与 OpenADMET

[【跳转到 30:47】](https://www.youtube.com/watch?v=S6H_INT5hzc&t=1847)

问：预测结果如何接入药物发现下游（虚拟筛选、对接、ADMET）？答：这是新领域，方向很多。OMSF 内已有项目把 **OpenFold3 预测接入 OpenFE 做（自由能）计算**；团队与 **OpenADMET** 紧密合作，在其多个盲测数据集上试验 OpenFold3 微调的效果。总体仍处早期，还没有"标准答案"，但正因为全开源，社区可以自由组合工具、共享管线。

### 6.6 抗原-抗体预测：能做，靠"多预测 + 排序"

[【跳转到 32:52】](https://www.youtube.com/watch?v=S6H_INT5hzc&t=1972)

问：OpenFold3 能做抗体-抗原预测吗？答：能，但不容易。关键做法（主讲人不愿称之为 trick）：**大量预测 + 排序**。现场用曲线演示：单次单 seed 预测的对接得分可能平平；把预测次数提到几十、几百、上千次，结果质量显著上升（[【跳转到 34:11】](https://www.youtube.com/watch?v=S6H_INT5hzc&t=2051)）。排序有两种：一是"神谕（oracle）"——直接与真值对比，只能用于基准测试；实用的是**用模型自带的置信度自评分排序**，同样能看到随预测次数提升的趋势。这套"多预测 + 置信度排序"的能力正是 AF3 论文的特色，各家开源复刻都在跟进。

### 6.7 新手学习路径：课程 + 直接上手玩

[【跳转到 35:11】](https://www.youtube.com/watch?v=S6H_INT5hzc&t=2111)

问：生物技术背景、没有结构生信经验，先学什么？答：**EMBL 的课程**——有一门围绕 AlphaFold3 的课，此外还有生信方向的系列课程，资源集中（链接见视频页）。其次是**直接上手玩工具**：把蛋白、分子丢进 Vecura 这类平台，改改配体、突变几个残基，观察结构怎么变，培养直觉（[【跳转到 36:11】](https://www.youtube.com/watch?v=S6H_INT5hzc&t=2171)）。

### 6.8 为什么模型需要进化信息

[【跳转到 36:53】](https://www.youtube.com/watch?v=S6H_INT5hzc&t=2213)

问：预测复杂结构为什么需要 MSA？答：这是开放研究问题。有人说 ESM 这类纯语言模型可以绕开 MSA——但**它们本质上也是在海量进化数据上训练出来的**。根本原因是数据量级：**PDB 只有约 25 万个结构**，是几十年艰苦实验攒下来的，很难再多；而**序列数据库里有数以百万计的序列**。对大型模型来说，即使没有真实结构，"这类序列、这类 motif 在生物里很常见"本身就是极有价值的模式——所以各家模型都把进化史作为输入，借这套丰富的模式库做预测（[【跳转到 38:15】](https://www.youtube.com/watch?v=S6H_INT5hzc&t=2295)）。

### 6.9 治理：门槛降低之后，如何防止过度解读

[【跳转到 38:48】](https://www.youtube.com/watch?v=S6H_INT5hzc&t=2328)

问：自动化 MSA 管线与无代码工作流让 OpenFold3 更易用，如何平衡"平民化"与"非专家误用"？答：关键在结果的呈现与解读方式；模型方能做到的是尽力解释输出含义。就现阶段而言，OpenFold3 还比较"简单直接"——输入序列/配体/核酸，输出结构，不至于像基因组学工具那样给出"这个基因与癌症相关"这类需要谨慎对待的惊人结论（[【跳转到 40:04】](https://www.youtube.com/watch?v=S6H_INT5hzc&t=2404)）。

## 小结

- OpenFold3 是 AlphaFold3 的**全链路开源复刻**：数据集、训练管线、模型代码、权重全部开放；由 OpenFold 联盟（OMSF 托管）维护，主线由哥伦比亚大学 AlQuraishi 教授领导。
- 架构三段式：**三类输入**（MSA + 模板 + 构件构象）→ **Pairformer 三角更新**（O(N³) 代价换来高精度）→ **扩散模块**（把图像生成技术搬进原子世界，自带置信度头）。
- 读输出先看**置信度**：pLDDT 是逐残基局部置信度，未解析区域模型会"自首"；pTM/ipTM 看全局与界面质量。
- **相似度决定上限**：Runs 'N' Poses 显示查询越像训练集性能越好，低相似度区间仍是研究前沿。
- 落地门槛已大幅降低：PyPI 两条命令安装；或直接用 **Vecura** 浏览器工作区（学术邮箱验证后赠 200 美元算力，[【跳转到 41:41】](https://www.youtube.com/watch?v=S6H_INT5hzc&t=2501)）。
- 实践要点：GPU 显存 ≥ 40 GB；浅 MSA/抗体场景用**多采样 + 置信度排序**；复合物防碰撞等化学转向组件正在加入。
- 路线图：OpenBind Zero（2025 数据截止）已发布，V1 预计 2025 Q4；微调一站式改造、稳定性数据、亲和力、关键水分子在计划中。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| OpenFold3 (OF3) | AlphaFold3 的开源复刻：预测蛋白质及其与小分子、核酸等相互作用的结构模型 |
| OpenFold Consortium | 开放分子软件基金会（OMSF）旗下的联盟，维护 OpenFold 系模型与数据 |
| MSA | 多序列比对：用进化史上的同源序列为模型提供模式上下文 |
| 模板 (templates) | PDB 中与目标相似的已知结构，作为模型输入特征（≠ 同源建模） |
| 构象生成 (conformer generation) | 用 RDKit 为小分子构件生成粗略三维摆位 |
| Pairformer | AF3 的主干 transformer；核心是三角更新，每个节点接收两个邻居的信息 |
| 扩散模块 | 从随机原子出发逐步去噪生成结构，与 Stable Diffusion 同源 |
| pLDDT | 逐残基局部置信度；低分区域通常是模型在"猜" |
| Runs 'N' Poses | 按与训练集相似度分组的蛋白-配体预测基准 |
| ColabFold 集成 | 内置 MSA/模板检索服务，免自建序列数据库 |
| 低内存模式 | 用更长运行时间换更低显存峰值（≥40 GB 显存仍是底线） |
| 化学转向 (chemical steering) | 在扩散过程中施加的化学约束/惩罚（如防原子碰撞、口袋约束） |
