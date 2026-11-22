# [OpenFold3] Open-Source Drug Discovery： How OpenFold3 Changes Protein Engineering Structural Biology

> 视频来源：[YouTube《[OpenFold3] Open-Source Drug Discovery: How OpenFold3 Changes Protein Engineering Structural Biology》](https://www.youtube.com/watch?v=P-nHDE9Mqeo)（20:22）。这是一期 NotebookLM 式的"深度拆解"播客，素材不是论文或发布会 PPT，而是 **OpenFold3 Preview 2 的官方 GitHub 仓库结构、模型文档与技术报告**——两位主持人以对谈形式逐层拆解这个 AlphaFold3 的全开源复刻：模型能建什么、内部怎么算、训练管线怎么搭、推理怎么省显存、成绩追平了谁。视频字幕为英文自动字幕（yt-dlp 直拉成功），已逐窗口通顺化并纠正错拼（"ligans"→ligands、"multime"→multi-chain、"parapformer"→Pairformer、"4A embedding"→Fourier embedding、"Nvidia Q covariance"→NVIDIA cuEquivariance、"pretend V1 and bolts 1 and two"→Protenix v1 与 Boltz-1/2 等）；本文基于文稿整理翻译，数字与结论均可点时间戳回看核对。

## 本讲要解决的核心问题（SCQA）

**背景**：小分子药物发现的第一步是拿到**靶标蛋白**（以及它与配体结合时）的三维结构。AF3 类模型是目前最强的工具，但最强的一批普遍以封闭平台提供服务；OpenFold 联盟——一个开发免费开源生物学/药物发现软件的**非营利研发联盟**——刚刚发布了旗舰模型 **OpenFold3 Preview 2**（[【跳转到 00:00】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=0)）。

**冲突**：想自己训练、微调、改造模型时，"精致的白皮书 + 锁死的 API"给不了答案。而要真正开源复刻 AlphaFold3，等于把**数学基础、模型架构、训练管线、原始代码**全部摊开——这件事极少有人做全（[【跳转到 00:12】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=12)）。

**疑问**：OpenFold3 Preview 2 究竟开源到什么程度？模型内部到底怎么工作？成绩追上 AlphaFold 3 了吗？

**回答（中心思想）**：本讲把"工厂蓝图"逐层拆开：OpenFold3 是一个**全原子（all-atom）扩散结构生成器**，蛋白质、RNA、DNA、小分子配体、多链大复合物都能建，每个非氢原子都有精确三维坐标；引擎是 **Pairformer 的三角数学 + EDM 扩散雕刻**，训练靠**自蒸馏 1300 万无标签序列**，推理端有 **chunking/LMA/激活检查点**省显存三件套。成绩单上，它是**目前唯一在单链 RNA 上追平 AlphaFold 3 的全开放模型**（INF 0.74），药物结合预测与 Protenix v1 相当、显著缩小与 AF3 的差距，抗体-抗原复合物仍是全体开放模型共同的前沿——而正因为训练数据、代码、权重全公开，社区可以众包微调去攻克它。

## 一、开源蓝图：不是又一篇论文，而是整座工厂

[【跳转到 00:12】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=12)

这期拆解与"典型 AI 发布会"的根本区别在于**透明度**（[【跳转到 00:37】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=37)）：我们看的不是打磨过的白皮书或锁死的 API，而是直接综合自官方 GitHub 仓库的信息——数学基础、模型文档、OpenFold3 Preview 2 技术报告与联盟最新发布（[【跳转到 00:42】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=42)）。用主持人的话说："他们真的把**蓝图**交了出来。"无论你是被 GPU 显存折磨的机器学习工程师，还是好奇扩散模型如何"雕刻"原子的生物学家，这期内容都是一份大师课（[【跳转到 00:57】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=57)）。

![从官方 GitHub 仓库与技术报告出发的 OpenFold3 深度拆解](assets/[OpenFold3]%20Open-Source%20Drug%20Discovery：%20How%20OpenFold3%20Changes%20Protein%20Engineering%20Structural%20Biology/00012.webp)

## 二、模型能建什么：全原子扩散结构生成器

[【跳转到 01:15】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=75)

看复杂数学之前，先搞清这台机器**造什么**。OpenFold3 是一个**全原子的、基于扩散的结构生成器**，而且关键在于"不再只服务蛋白质"（[【跳转到 01:15】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=75)）：

- **覆盖面**：RNA、DNA、**小分子配体**，以及**大型多链复合物**，全都在一台机器里；
- **全原子精度**：每个**非氢原子**都拿到精确的三维坐标。早期模型可能只给出蛋白主链，而**侧链**——恰恰是与药物相互作用的部分——只是近似（[【跳转到 01:34】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=94)）；
- **尺度跨度**：从巨大的蛋白复合物到结合在上面的一粒小分子药物，模型追踪的是**同一套精确的空间现实**（[【跳转到 01:59】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=119)）。

![全原子生成器：RNA、DNA、小分子配体与多链复合物全覆盖，每个非氢原子都有精确坐标](assets/[OpenFold3]%20Open-Source%20Drug%20Discovery：%20How%20OpenFold3%20Changes%20Protein%20Engineering%20Structural%20Biology/00094.webp)

对药物发现管线（管线 C 第一步"靶标蛋白"）的意义很直接：靶标蛋白、靶标-配体复合物的结构，都可以从序列+SMILES 出发交给它预测。

## 三、代码工厂的结构：一间"模块化厨房"

[【跳转到 02:30】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=150)

仓库里的代码组织得异常干净：`loss`、`kernels`、`model`、`data` 等模块**完美分离**（[【跳转到 01:59】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=119)）。别把它想象成缠绕的代码网，把它想象成**高度模块化的厨房**（[【跳转到 02:30】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=150)）：

- `data` 目录是**备菜台**：拉取原始食材；
- `kernels` 是**工业烤箱**：承担重计算；
- `model`（特别是其中的 latent 目录）是**主厨的食谱**：决定一切的去向。

![代码工厂的模块化结构：data 备菜、kernels 烤箱、model 主厨食谱各司其职](assets/[OpenFold3]%20Open-Source%20Drug%20Discovery：%20How%20OpenFold3%20Changes%20Protein%20Engineering%20Structural%20Biology/00150.webp)

这种严格分离之所以对科研社区重要，是纯功能性的：代码库把**置信度头（confidence heads）**从主网络的繁重计算里清楚隔离出来，研究者可以轻松"拧下"默认打分机制、换上自己的自定义头（[【跳转到 03:05】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=185)）——想让模型学会预测某类特定的化学结合？架构主动邀请你修改它，而**不破坏核心引擎**。

顺带把一条分子的"生命周期"交代了：文档里的 **Algorithm 1** 规定模型分三个阶段运转——**主干（trunk）、扩散 rollout、置信度头**（[【跳转到 03:30】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=210)）。下面逐段拆。

## 四、数据的两种形态与"循环"机制

[【跳转到 03:39】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=219)

要跟上数据的流向，得先理解信息的"形状"——张量维度。原始生物序列流入时，模型同时追踪**两条现实流**（[【跳转到 03:39】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=219)）：

1. **单体表示（single representation）**：记录每个"个体"（残基/原子 token）的身份与状态，通道数 **c_s ≈ 384**；
2. **成对表示（pair representation）**：记录任意两个元素之间的关系，通道数 **c_z ≈ 128**。

把单体表示想成**一份"个人名单"**，把成对表示想成**一张"谁跟谁什么关系"的大网格**（[【跳转到 04:14】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=254)）。

![序列进入主干：48 个 Pairformer 块对"个人名单 + 关系网格"做密集数学变换](assets/[OpenFold3]%20Open-Source%20Drug%20Discovery：%20How%20OpenFold3%20Changes%20Protein%20Engineering%20Structural%20Biology/00254.webp)

序列进入主干后，先经过 **Pairformer 堆叠：48 个高度密集的数学变换块**。但这里有个反直觉的设计——系统会把数据**反复送回同一个主干**。既然已经过了 48 个大块，为什么还要循环（recycle）？算一次不够吗？（[【跳转到 04:39】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=279)）

![单链表示与成对表示：个人名单 + 关系网格，经 48 个 Pairformer 块反复精炼](assets/[OpenFold3]%20Open-Source%20Drug%20Discovery：%20How%20OpenFold3%20Changes%20Protein%20Engineering%20Structural%20Biology/00219.webp)

答案是：**循环是模型"渐进地看见结构"的方式**——迭代精炼。张量每穿过 48 个块一次，就把上一轮学到的结构语境带回来（[【跳转到 04:49】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=289)）。像画肖像：第一遍勾出轮廓，把轮廓反馈给眼睛，第二遍细化明暗。等数据走完所有循环，模型在真正生成三维坐标**之前**，已经在内部建立了非常强的**空间先验**（[【跳转到 05:14】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=314)）。

## 五、从序列到张量：原子编码器与 MSA 模块

[【跳转到 05:24】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=324)

氨基酸字母串怎么变成上面那些张量？第一步是**原子注意力编码器（atom attention encoder）**：它对**参考构象（reference conformer）**做局部自注意力（local self-attention），让**同一残基里的原子**——同一块积木——彼此关注（[【跳转到 05:24】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=324)）；元素类型、电荷、原子名这些原子级特征被汇集到一起，把高度复杂的微观数据**压缩成 token 级表示**，同时不丢失化学现实（[【跳转到 05:49】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=349)）。

接着模型要理解序列的"进化史"——**MSA（多序列比对）模块**登场（[【跳转到 05:59】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=359)）。它把**共进化信号**经**外积均值（outer product mean）**投影进成对表示网格。

![原子注意力编码器与 MSA 模块：共进化信号经外积均值进入成对表示](assets/[OpenFold3]%20Open-Source%20Drug%20Discovery：%20How%20OpenFold3%20Changes%20Protein%20Engineering%20Structural%20Biology/00394.webp)

主持人给外积均值打了个比方——**社交网络分析**（[【跳转到 06:24】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=384)）：想了解两个人真实的关系，不能只问他们本人，要看他们在**几千个"群聊"里的互动行为**——这正是进化数据的含义：在不同上下文里观察互动，推断底层联系（[【跳转到 06:34】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=394)）。

这一步的精髓是**成对导出的加性偏置（pair-derived additive bias）**，数学上记作 b^A：token A 与 token B 之间**已有的空间关系**，会主动偏置模型对其**共同进化历史**的关注程度（[【跳转到 06:59】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=419)）——空间关系与进化关系就此交织在一起，这为整台机器的引擎做好了铺垫：**Pairformer 与它的三角数学**（[【跳转到 07:09】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=429)）。

## 六、引擎：Pairformer 与三角数学

MSA 模块铺好关系，**Pairformer 堆叠负责执行三维几何的"物理法则"**（[【跳转到 07:09】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=429)）。48 个块联合更新单体与成对表示；核心是**三角乘法更新（triangular multiplicative updates）**：对入边/出边做 sigmoid 门控计算（[【跳转到 07:44】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=464)），同时对成对矩阵的行和列做自注意力；单体轨道则在成对表示偏置的注意力下更新（[【跳转到 08:09】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=489)）。

![Pairformer 的三角乘法更新：把三角形不等式硬编码进潜空间](assets/[OpenFold3]%20Open-Source%20Drug%20Discovery：%20How%20OpenFold3%20Changes%20Protein%20Engineering%20Structural%20Biology/00464.webp)

为什么是三角形？模型天生**不懂物理**，必须逼它懂（[【跳转到 08:19】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=499)）。三维空间中任意三点的距离严格受**三角形不等式**约束：任何一边的长度都不能超过另外两边之和。强迫网络**只通过三角运算**更新内部表示，开发者不是在"希望"模型学会空间规则，而是把物理几何逻辑**硬编码进潜空间**——网络在物理上**无法**构造几何上不可能的关系（[【跳转到 08:44】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=524)）。就像把物理法则浇筑进工厂的地板（[【跳转到 08:54】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=534)）。

## 七、雕刻：扩散模块如何把噪声变成结构

Pairformer 画好完美的内部地图，接下来轮到"雕刻家"——**扩散模块**。它用 **EDM 风格的预条件去噪器（preconditioned denoiser）**：训练时跑一个随机采样循环，从纯混沌噪声出发，目标是把混沌**去噪**成完美的生物结构（[【跳转到 08:54】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=534)）。

![扩散模块：EDM 预条件去噪器从纯噪声雕刻出生物结构](assets/[OpenFold3]%20Open-Source%20Drug%20Discovery：%20How%20OpenFold3%20Changes%20Protein%20Engineering%20Structural%20Biology/00534.webp)

噪声采样用**对数正态（log-normal）分布**，原因很讲究（[【跳转到 09:19】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=559)）：给的全是纯噪声，模型学不到细节；给的全是干净结构，模型学不会修复大错。对数正态分布逼着模型把大部分练习时间花在"**适度损坏**"数据的黄金区间（Goldilocks zone）（[【跳转到 09:29】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=569)）。

![对数正态噪声调度：让模型在"适度损坏"的黄金区间练习](assets/[OpenFold3]%20Open-Source%20Drug%20Discovery：%20How%20OpenFold3%20Changes%20Protein%20Engineering%20Structural%20Biology/00569.webp)

文档里另一个让主持人惊叹的设计：告诉网络"当前结构被加了多少噪声"的 **Fourier 嵌入**用的是**固定随机种子**——完全不经训练，只是个数学锚点（[【跳转到 09:54】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=594)）。为什么？固定种子就能产生稠密、连续的嵌入而**不引入可学习参数**，而可学习参数可能对训练数据过拟合（[【跳转到 10:04】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=604)）。模型只需要一个可靠的信号"你在噪声等级 5 / 等级 10"，不需要学会怎么量噪声——它只需要测量值本身（[【跳转到 10:04】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=604)）。

同样为了防止作弊：**中心随机增强（centre random augmentation，Algorithm 19）**——每个扩散步之前，把整团原子坐标随机旋转 + 平移（[【跳转到 10:29】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=629)）。否则模型会记住"原子 X 总在左上角"这类全局绝对坐标；随机转移之后，它只能依赖前面说的**相对三角关系**——理解内部结构，而不是背下一张图（[【跳转到 10:39】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=639)）。

## 八、裁判：总损失与三件置信度指标

结构雕完，得有人裁判雕得好不好——这就是**总损失函数与置信度头**：把**去噪得分匹配（denoising score matching）**与直方图**交叉熵**混在一起（[【跳转到 11:04】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=664)）。置信度三件套（[【跳转到 11:14】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=674)）：

- **pLDDT**（predicted local distance difference test）：给**局部原子邻域**的置信度打分；
- **PAE**（predicted aligned error）：检查较大的结构域**彼此相对摆放**是否正确；
- **PDE**（predicted distance error）：预测距离误差。

不过数学再完美、打分再精巧，没有合适的数据与训练基础设施也是白搭——AI 的智能完全取决于它"吃"进去什么（[【跳转到 11:39】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=699)）。

## 九、数据与训练管线：自蒸馏 1300 万无标签序列

[【跳转到 11:49】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=709)

落地到数据、训练与配置。MSA 管线用 **JackHMMER 与 HHsearch**——把它们想成高度专业化的"进化搜索引擎"：在海量数据库里搜出目标序列的"进化表亲"，构建前面说的关键 MSA 数据（[【跳转到 11:49】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=709)）。整套操作由 **ML Collections 配置层级**驱动管理（[【跳转到 12:14】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=734)）。

![数据与训练管线：JackHMMER/HHsearch 构建 MSA，ML Collections 管理配置](assets/[OpenFold3]%20Open-Source%20Drug%20Discovery：%20How%20OpenFold3%20Changes%20Protein%20Engineering%20Structural%20Biology/00709.webp)

训练管线分三个阶段：**初始训练 → 用 1300 万序列蒸馏 → 置信度微调**（[【跳转到 12:23】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=743)）。蒸馏集最值得停下来说：这 1300 万序列**完全没有结构标签**——没有 3D 标签怎么学 3D 结构？答案是**自蒸馏（self-distillation）**，这也是 OpenFold3 独特力量的一大来源（[【跳转到 12:23】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=743)）：拿一个**较早、已经训练好的自己**给这批原始序列预测 3D 结构（先"猜"出结构），然后**严格过滤掉低置信度预测**，只保留模型绝对有把握的结构（[【跳转到 12:58】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=778)）。模型给自己当老师：用自己最好的预测结构训练自己，把智力"自举"到比原始人工标注数据更深的进化模式里——就像学生批改自己的练习、发现强项，再用它写出一本更好的备考教材（[【跳转到 13:23】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=803)）。

训练还配了复杂的学习率调度器——**AlphaFold LR ruler**：预热（warm-up）→ 平台期 → 指数衰减，管理权重更新速度（[【跳转到 13:33】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=813)）。

另一个精妙细节是**多链置换对齐（multi-chain permutation alignment）**（[【跳转到 13:33】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=813)）。预测"五个相同蛋白组成的环"这类**对称多链复合物**时，模型自动把预测对齐到**数学上拟合最好的链置换**（[【跳转到 14:08】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=848)）——预测出完美形状，不会因为把相同的链编号成另一种同样合法的顺序而受罚。模型**懂对称性**（[【跳转到 14:08】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=848)）。当然，这些训练要**成百上千张 H100 GPU 昼夜运转**（[【跳转到 14:08】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=848)）。

## 十、推理实战：CIF/JSON 输出与省显存"三件套"

文档同样深讲了研究者怎么在**自己的硬件**上跑这个大家伙做推理（[【跳转到 14:08】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=848)）。如果你经历过 GPU 显存飙到 99% 然后整个系统崩溃，这一节就是给你的（[【跳转到 14:08】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=848)）。

输出格式：标准 **CIF 文件**（三维结构）+ **JSON 文件**（置信度分数）（[【跳转到 14:33】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=873)）。处理这些大矩阵需要内核加速：项目重度依赖 **DeepSpeed for Science 的 Evoformer 内核**与 **NVIDIA cuEquivariance**——定制构建的软件例程直接对接 GPU 硬件，把三角数学算得飞快，专门瞄准 **Pairformer 块**这个全模型数学最稠密的瓶颈；用上它们，OpenFold 在这个最重的环节拿到大幅加速（[【跳转到 14:43】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=883)、[【跳转到 15:08】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=908)）。

即便有定制内核，要同时追踪成千上万原子及其关系，**显存管理**仍是难关。三板斧（[【跳转到 15:18】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=918)）：

1. **分块（chunking）**：把序列切进 128 行的小块分批计算，不让显卡"噎住"；
2. **低显存注意力（LMA, low-memory attention）**：把运行压在 80 GB 显存的硬限制以内——对多数研究实验室至关重要；
3. **激活检查点（activation checkpointing）**：经典但必要。像一次艰苦的登山：与其背着装满全部补给（所有网络激活值）的巨型背包上山，不如轻装上阵，**在下降途中（反向传播）再重算**当前需要的补给——用一点额外计算时间换大量显存节省（[【跳转到 15:43】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=943)、[【跳转到 15:53】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=953)）。

![省显存三件套：chunking、LMA 与激活检查点](assets/[OpenFold3]%20Open-Source%20Drug%20Discovery：%20How%20OpenFold3%20Changes%20Protein%20Engineering%20Structural%20Biology/00953.webp)

仓库的故障排查（troubleshooting）部分直接给出药方：验证损失停滞或报 OOM？开启 chunking、打开 LMA、用上检查点——原本会让系统当场崩溃的巨大生物序列，现在就能顺利处理（[【跳转到 16:18】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=978)）。

## 十一、成绩单：RNA 追平 AF3，药物结合逼近，抗体-抗原仍是前沿

数学有了、代码有了、GPU 也优化了，实际效果如何？看 **OpenFold3 Preview 2 技术报告**的记分板：对比对象是 AlphaFold 3、Protenix v1、Boltz-1 与 Boltz-2（[【跳转到 16:23】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=983)）。

![OpenFold3 Preview 2 技术报告成绩单：与 AF3、Protenix v1、Boltz-1/2 对比](assets/[OpenFold3]%20Open-Source%20Drug%20Discovery：%20How%20OpenFold3%20Changes%20Protein%20Engineering%20Structural%20Biology/00983.webp)

- **单链 RNA**：OpenFold3 Preview 2 是**目前唯一在单链 RNA 结构上追平 AlphaFold 3 的全开放模型**，取得 **INF 0.74**——INF 评估复合物 RNA 主链与碱基配对的准确度（[【跳转到 16:48】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=1008)、[【跳转到 16:56】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=1016)）；
- **药物结合**：在 **Runs N Poses 蛋白-配体数据集**（检验模型预测药物结合好坏）上，与 **Protenix v1 大致相当**，并显著缩小了与 AlphaFold 3 的历史差距（[【跳转到 16:56】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=1016)）；
- **剩余前沿：抗体-抗原复合物预测**——免疫学与疫苗设计的"圣杯"，也是当前最难的部分（[【跳转到 17:21】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=1041)）。

看 **DockQ** 分数（评估两个蛋白对接好坏的标准指标），进化数据的缩放曲线分出了高下：给 1000 个 MSA 种子的大池子时，AlphaFold 3 仍然扩展得明显更好（[【跳转到 17:26】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=1046)）。既然架构几乎一样，为什么 AF3 还能在这些高度特化的免疫相互作用上领先？归因于两个瓶颈：**训练算力的总量**，以及 **Google DeepMind 这类公司实验室手里的海量专有训练数据**（[【跳转到 17:57】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=1077)）。

报告的缩放曲线还揭示了一个微妙事实：OpenFold3 有**潜在能力**生成正确的抗体-抗原姿态——原始生成能力非常强——但有时**没能把正确姿态排到第一名**（[【跳转到 17:57】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=1077)）。用主持人的话："它造得出来，只是没意识到那是最好的一个。"（[【跳转到 18:22】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=1102)）

## 十二、真正的突破：把引擎交给大家

关键的收获不是差距本身，而是：OpenFold 连**完整训练数据集与未编译代码**都放出，全球科学社区现在就能进场（[【跳转到 18:22】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=1102)、[【跳转到 18:32】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=1112)）。研究者不必等某一家公司实验室来优化——社区可以**众包定向微调**，去攻克上面那个抗体-抗原问题（[【跳转到 18:32】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=1112)）。

![开源的不只是软件：训练数据、自蒸馏管线、推理代码、权重与三角数学全部交出](assets/[OpenFold3]%20Open-Source%20Drug%20Discovery：%20How%20OpenFold3%20Changes%20Protein%20Engineering%20Structural%20Biology/01112.webp)

这才是真正的突破：OpenFold 交出的不只是一个强大的软件玩具，而是把**海量训练数据、自蒸馏管线、低显存推理代码、权重，以及 Pairformer 背后超专业的三角数学**全部开源——**把生物分子 AI 的地基民主化**。像把一台终极生物显微镜拆到基础零件，把蓝图交到每个人手里（[【跳转到 18:57】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=1137)、[【跳转到 19:07】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=1147)）。

![拆开引擎之后的想象：不是预测自然里已有的生物学，而是从头生成全新的功能生物系统](assets/[OpenFold3]%20Open-Source%20Drug%20Discovery：%20How%20OpenFold3%20Changes%20Protein%20Engineering%20Structural%20Biology/01197.webp)

过去几年，我们用 AI **预测自然里已存在的生物学**——建模"已经在那里的东西"；而有了完全开放、数学严谨、可修改的 OpenFold3 这样的地基，研究者可以开始**拆开引擎**：把扩散模型反过来用——不是从已知序列预测结构，而是**从零生成全新的、高度功能化的生物系统**（[【跳转到 19:32】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=1172)）。代码就在那里，工厂已经开门——"你打算造什么？"（[【跳转到 19:57】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=1197)）

下次再看医学影像、或读到一项新药发现：我们看到的不再是教科书里的静态图，而是一片**动态的、可计算的地形**——而这片地形的导航工具，终于属于所有人（[【跳转到 20:10】](https://www.youtube.com/watch?v=P-nHDE9Mqeo&t=1210)）。

## 小结

- OpenFold3 Preview 2 是 AlphaFold3 的**全开源复刻**：数学、架构、训练管线、原始代码全部可查；代码按 loss/kernels/model/data 模块化分离，置信度头可以整体替换成自定义头；
- 模型是**全原子扩散结构生成器**：蛋白、RNA、DNA、小分子配体、多链复合物通吃，每个非氢原子都有精确 3D 坐标——与药物相互作用的侧链不再是近似；
- 数据有两套"形态"：单体表示（c_s≈384）与成对表示（c_z≈128），经 **48 个 Pairformer 块 + 多次循环**迭代精炼出空间先验；
- 三角乘法更新把**三角形不等式硬编码**进潜空间——网络物理上无法构造几何上不可能的关系；
- 扩散模块三件套：**EDM 预条件去噪器 + 对数正态噪声调度（黄金区间练习）+ 中心随机增强（防背坐标）**；噪声等级用**固定种子的 Fourier 嵌入**做数学锚点；
- 训练管线：**JackHMMER/HHsearch** 建 MSA + **1300 万无标签序列自蒸馏**（严格置信度过滤）+ 多链置换对齐（懂对称性），配 AlphaFold LR ruler 学习率调度；
- 推理省显存三件套：**chunking（128 行）/ LMA / 激活检查点**；**cuEquivariance 与 DeepSpeed4Science 内核**专攻 Pairformer 三角计算瓶颈；
- 成绩：单链 RNA 追平 AF3（**INF 0.74**），Runs N Poses 药物结合与 Protenix v1 相当并显著逼近 AF3，**抗体-抗原复合物仍是开放模型共同前沿**（"造得出、排序偶尔失手"）；
- 最大价值在"全开放"：社区可众包定向微调，甚至**反转扩散模型**、从零设计全新生物系统——"工厂已经开门"。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| OpenFold3 Preview 2 | OpenFold 联盟发布的 AlphaFold3 全开源复刻（第二版预览），代码/数据/权重全部公开 |
| 全原子（all-atom） | 不只建主链，侧链与配体的每个非氢原子都给出精确三维坐标 |
| 扩散模型（diffusion） | 从纯噪声出发逐步去噪、生成结构的生成式方法（见 4.3.1） |
| Pairformer / 三角更新 | AF3 类模型主干：48 个块用三角乘法更新维护"关系网格"，满足三角形不等式（见 4.4.2） |
| MSA / 外积均值 | 多序列比对携带共进化信号，经外积均值投影进成对表示 |
| 循环（recycling） | 数据多次穿过同一主干，像画肖像一样迭代精炼空间先验 |
| 自蒸馏（self-distillation） | 用模型自己高置信度的预测结构当"伪标签"训练自己（本例 1300 万无标签序列） |
| Fourier 噪声嵌入 | 固定随机种子的数学锚点，告诉网络当前噪声等级，不引入可学习参数 |
| cuEquivariance | NVIDIA 定制 GPU 内核，加速 Pairformer 三角数学（见 4.4.2 注） |
| LMA / 激活检查点 | 低显存注意力与"反向传播时重算激活"两项省显存技巧 |
| pLDDT / PAE / PDE | 局部原子邻域置信度 / 域间相对摆放误差 / 预测距离误差（见 3.1） |
| INF / DockQ / Runs N Poses | RNA 复合物碱基配对准确度指标 / 蛋白对接质量标准指标 / 蛋白-配体药物结合基准集 |
