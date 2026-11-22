# OpenFold3 and AQAffinity： A New Era of Open-Source Molecular Modeling

> 视频来源：[YouTube《OpenFold3 and AQAffinity: A New Era of Open-Source Molecular Modeling》](https://www.youtube.com/watch?v=_DUzHDwDX9Q)（56:50），OpenFold 联盟 × NVIDIA × SandboxAQ 三方联合网络研讨会。嘉宾：**Mohammed AlQuraishi**（哥伦比亚大学教授、OpenFold 联盟首席研究员）、**Roy Tal**（NVIDIA 数字生物学高级联盟经理，BioNeMo 平台）、**Adam Lewis**（SandboxAQ AI-sim 部门研发负责人）。对话覆盖 OpenFold 联盟的组织形态、OpenFold3 的定位与训练规模、NVIDIA 的开源模型与加速生态、SandboxAQ 的 LQM 理念与 **AQAffinity** 亲和力模型、社区采用的两个标志性项目，以及三方对"下一个五年"的判断。视频字幕为英文自动生成，本文基于文稿整理翻译；文中数字与结论均出自视频内容，可点击时间戳回看核对。

## 本场要解决的核心问题（SCQA）

**背景**：AF3 类共折叠模型已被证明能真正服务药物发现（2025 年起达到"实验级可用"），其开源复刻 OpenFold3 也已发布——结构预测这一环开始普及。

**冲突**：但药物发现的瓶颈远不止结构。**亲和力预测**（分子与靶点"粘得多牢"）要么靠实验（慢、贵、难接入计算链路），要么靠传统计算方法（慢、不准、还必须先拿到结构）；而且"选靶点—设计分子"两步严重串行，假设错了要到临床试验才发现——九成失败源于最初假设。

**疑问**：开源生态能不能把**结构预测、亲和力预测、算力加速**三块拼成一条真正可用的新管线？

**回答（中心思想）**：能，而且三方在本次研讨会上展示了拼图如何咬合：**OpenFold3** 提供全开源、训练最充分的结构共折叠基座（数百万 GPU 小时）；**AQAffinity** 在 OpenFold3 之上数周内搭出亲和力预测头——直接从序列到亲和力，比 FEP 自由能计算快约数千倍且不需要先有结构，权重与代码同样全开源；**NVIDIA** 用 BioNeMo 平台与 cuEquivariance 专用内核把三角算子等折叠模型专属计算大幅加速（GPU 利用率可推到 95%，数据管线 3 个月压缩到 3 周）。三方共同判断：2025 年是"模型开始真正可用"之年，2026 年是**部署之年**，而推理时扩展（第三缩放定律）与虚拟细胞是下一个前沿。

## 一、OpenFold 联盟：把 DeepMind 式的"团队科学"搬进学术界

### 1.1 使命：让分子建模民主化

[【跳转到 03:24】](https://www.youtube.com/watch?v=_DUzHDwDX9Q&t=204)

AlQuraishi 对联盟使命的概括：**让分子建模在规模上民主化**——让公司、个人、学术界与工业界的科学家，都能以可及的方式使用最前沿的蛋白质结构与相互作用建模工具。联盟做的同时也是一种**科学组织方式的实验**：用不同于传统学术"单打独斗"（一个博士生/博后扛一个课题）的方式做科学。

![OpenFold 联盟使命：让分子建模在规模上民主化](assets/OpenFold3%20and%20AQAffinity：%20A%20New%20Era%20of%20Open-Source%20Molecular%20Modeling/00169.webp)

### 1.2 为什么说这是"科学的新范式"

[【跳转到 04:48】](https://www.youtube.com/watch?v=_DUzHDwDX9Q&t=288)

AlphaFold 展示了另一种可能：DeepMind 集结高水准团队攻坚科学基础问题，与学术界"个体中心"的传统形成鲜明对比。OpenFold 联盟想做的，是**把这种"团队科学"模式搬进学术场景**：大学与实验室牵头攻关大问题，产业伙伴提供支持，而且**方向可被产业校准（steerable）**——制药业最关心的问题可以在学术环境中被优先 tackle，基础问题与应用问题并举。用他的话说：这是一种"以前没人做过"的、真正桥接产业与学术的做科学方式。

### 1.3 成员构成：学界 + 联盟全职团队 + 产业

[【跳转到 05:13】](https://www.youtube.com/watch?v=_DUzHDwDX9Q&t=313)

联盟成员分三类：

1. **学术实验室**：如 AlQuraishi 自己的实验室，负责构建这类模型；
2. **联盟全职团队**：OpenFold 组织内雇佣的工程师、科学家、项目经理——通常比普通学术实验室的成员更资深，与学术实验室协同做技术工作；
3. **产业伙伴**：以生物制药为主，也有科技公司。他们的参与方式是多维的——**一起做科学**（如 SandboxAQ 与联盟合作开发亲和力模型）、**共同决定方向与优先级**，并提供算力、资金与工程资源。

## 二、OpenFold3：定位、用户与"训练最充分的开源共折叠模型"

### 2.1 模型定位：不止蛋白质，而是"分子间相互作用"

[【跳转到 07:06】](https://www.youtube.com/watch?v=_DUzHDwDX9Q&t=426)

OpenFold3 是一个**共折叠（co-folding）模型**：预测的不只是蛋白质本身，而是**蛋白质与其他分子的相互作用**——小分子药物、抗体-抗原、甚至核酸。这为什么对药物发现关键？因为药物发现的第一步往往就是：搞清楚要调控哪个蛋白靶点，再设计能结合并调节它的小分子。

![OpenFold3 定位：预测蛋白质与小分子、抗体、核酸等的相互作用](assets/OpenFold3%20and%20AQAffinity：%20A%20New%20Era%20of%20Open-Source%20Molecular%20Modeling/00426.webp)

### 2.2 谁在用：三类用户

[【跳转到 07:56】](https://www.youtube.com/watch?v=_DUzHDwDX9Q&t=476)

- **生物学家与药物化学家**：有具体感兴趣的蛋白或核酸，用 OpenFold3 理解分子行为；
- **公司的计算科学家**：把 OpenFold3 当作**新模型的起点**，在自己的数据上继续训练，增强内部研发能力；
- **学术方法开发者**：站在一个"高得多的起跑线"上开发下一代技术。

### 2.3 两个"最"：许可最宽松 + 训练最充分

[【跳转到 08:54】](https://www.youtube.com/watch?v=_DUzHDwDX9Q&t=534)

OpenFold3 完全开源、免费，采用**非常宽松的开源许可**。另一个被主持人特意点出的数据：它是**训练最充分的共折叠模型**——用了数百万 GPU 小时与海量数据点。为什么"训练充分"重要？见下一节的飞轮逻辑。

### 2.4 飞轮效应：把算力变成数据

[【跳转到 09:29】](https://www.youtube.com/watch?v=_DUzHDwDX9Q&t=569)

AlQuraishi 给出了一个贯穿全场的方法论：**用不够强的初始模型生成"好假设"，再把假设当数据训练更强的模型**。在通用 AI 领域这已验证（早期模型产出数学证明、能跑通的代码，形成自我强化的飞轮）；在结构预测里，**初始版本 OpenFold3 生成的预测结构被当作合成数据，用于训练更强的后续版本**。这就是"算力可以转化为数据"，也是算力在 OpenFold3 中如此关键的深层原因。

![飞轮效应：初始模型生成合成数据，训练更强的后续版本](assets/OpenFold3%20and%20AQAffinity：%20A%20New%20Era%20of%20Open-Source%20Molecular%20Modeling/00569.webp)

### 2.5 S 数据集与 DiffDock 微调：生态互相"磨刀"

[【跳转到 11:03】](https://www.youtube.com/watch?v=_DUzHDwDX9Q&t=663)

Adam 补充了一个生态案例：SandboxAQ 近期发布了 **S 数据集**——**最大的带结合亲和力标注的 3D 结构共折叠数据集**；NVIDIA 随即用它**微调了 DiffDock**，对接精度有可见提升。"就像铁磨铁（iron sharpens iron）"——开放数据集反过来增强了社区里其他模型。

![S 数据集：最大的带亲和力标注的 3D 结构共折叠数据集](assets/OpenFold3%20and%20AQAffinity：%20A%20New%20Era%20of%20Open-Source%20Molecular%20Modeling/00663.webp)

## 三、NVIDIA 的角色：从 GPU 到 BioNeMo 加速生态

### 3.1 为什么 NVIDIA 押注开放模型

[【跳转到 11:43】](https://www.youtube.com/watch?v=_DUzHDwDX9Q&t=703)

Roy 的回答从公司战略讲起：**开放是扩大 AI 采用、维持创新速度的必要条件**——所以 NVIDIA 重投入开源：开放权重、开放训练代码、发论文，"从 Jensen 往下"都是这个共识。语言领域有 Nemotron 等开放模型；**生命科学领域则是 Clara 开放模型系列**。NVIDIA 的独特之处在于：自己做研究并开放，同时**深度服务生态伙伴**（产业如 SandboxAQ、学术如 OpenFold 联盟），帮他们创新、发布（最好开源的）模型；作为加速计算平台，NVIDIA 负责把计算瓶颈解决掉，让产业专注研发本身。

![NVIDIA 的开放模型战略：语言侧 Nemotron，生命科学侧 Clara 开放模型](assets/OpenFold3%20and%20AQAffinity：%20A%20New%20Era%20of%20Open-Source%20Molecular%20Modeling/00792.webp)

### 3.2 BioNeMo 平台：生命科学的"模型 + 工具 + 数据"全家桶

[【跳转到 15:26】](https://www.youtube.com/watch?v=_DUzHDwDX9Q&t=926)

**BioNeMo** 是 NVIDIA 面向生命科学的平台：硬件之上的低层加速库、垂直化的领域工具、模型与数据集。Roy 强调了一个关键观察：**折叠类模型的架构（三角算子等）在语言/视觉模型里并不存在**，所以需要为这些架构定制软件。BioNeMo 同时支持合成数据生产——无论是模拟，还是"用模型跑推理造数据"（比如 OpenFold3 使用的自蒸馏数据与 S 数据集）。

![NVIDIA BioNeMo 平台：面向生命科学的软件工具、模型与数据集](assets/OpenFold3%20and%20AQAffinity：%20A%20New%20Era%20of%20Open-Source%20Molecular%20Modeling/00926.webp)

### 3.3 cuEquivariance：给三角算子造专用内核

[【跳转到 17:20】](https://www.youtube.com/watch?v=_DUzHDwDX9Q&t=1040)

具体到 OpenFold3：它的架构里有**三角乘法、三角注意力**等几何感知算子，在 3D 空间上有独特计算模式，图像/语言领域用不上，因此通用内核效率不高。NVIDIA 为这类算子开发了定制 CUDA 内核库 **cuEquivariance**——**在 OpenFold3 发布时就已接入**，显著加速训练与推理；更快的推理意味着可以上更长上下文，进而表达更大的生物分子体系（[【跳转到 20:27】](https://www.youtube.com/watch?v=_DUzHDwDX9Q&t=1227)）。

![三角乘法与三角注意力：折叠模型专属算子，由 cuEquivariance 定制内核加速](assets/OpenFold3%20and%20AQAffinity：%20A%20New%20Era%20of%20Open-Source%20Molecular%20Modeling/01040.webp)

### 3.4 一个实战数字：GPU 利用率 95%，3 个月 → 3 周

[【跳转到 21:28】](https://www.youtube.com/watch?v=_DUzHDwDX9Q&t=1288)

Adam 给出了与 NVIDIA AI 加速器团队合作的实测收益：换新代 GPU 已有提速，再与该团队协同优化后，**GPU 利用率达到 95%**（他被告知这本身就是个亮眼数字）；他们原计划 3 个月的数据集构建管线，**压缩到了 3 周**。AQAffinity 能在 OpenFold3 发布后几周内上线，这种工程协同是重要前提。

## 四、SandboxAQ 与 AQAffinity：给结构加上"结合力"这一维

### 4.1 SandboxAQ 的使命与 LQM

[【跳转到 23:10】](https://www.youtube.com/watch?v=_DUzHDwDX9Q&t=1390)

SandboxAQ 的使命很直白：**让发现新药更快、更便宜**，路线是押注计算方法。他们内部把这些模型叫 **LQM（Large Quantitative Models，大规模定量模型）**——刻意与 LLM 区分开。Adam 的"赌注"论证很生动：往聊天机器人里灌更多文本、更多"猫视频"，模型会推理、会干很多事，但**它们大概率不会直接替你找到新药**——它们顶多指挥别的模型去找。LQM 是另一条路：直接对分子、对定量实验数据建模。

![SandboxAQ 使命与 LQM 理念：用大规模定量模型直接对分子建模](assets/OpenFold3%20and%20AQAffinity：%20A%20New%20Era%20of%20Open-Source%20Molecular%20Modeling/01390.webp)

### 4.2 计算方法的"物理优势"：信息不占地方

[【跳转到 24:00】](https://www.youtube.com/watch?v=_DUzHDwDX9Q&t=1440)

为什么计算方法值得押注？Adam 给出第一性原理：**把对象表示成信息后，"测试"它不会像物理实验那样互相挤占**——一个预测结构的模型、一个预测药效的模型、一个预测细胞影响的模型，不需要在物理空间里各占一块实验台。长期看，多种计算模型的协同应用能带来传统湿实验**难以企及（虽然并非不可能）**的加速。湿实验永远有用，但它**没法同时检验很多事**——实验室存在于真实物理世界里。

### 4.3 结构是关键阻塞，OpenFold 是关键伙伴

[【跳转到 25:09】](https://www.youtube.com/watch?v=_DUzHDwDX9Q&t=1509)

Adam 强调：LQM 蓝图里最大的堵点之一就是**把分子的结构搞对**。当下药物项目周期长、失败晚，重要原因是**为新靶点拿到实验结构太难**——没法快速通用地"看一眼"成百上千个靶点的形状。这也是为什么他们把 OpenFold 视为整体愿景的关键伙伴。同时他们把 AI 药物发现看作**公共资源**："所有船一起涨"对整个行业都有利——这不是一个"机会有限、要抢一小块"的零和游戏。

### 4.4 AQAffinity 是什么：在 OpenFold3 上加一个"亲和力头"

[【跳转到 26:00】](https://www.youtube.com/watch?v=_DUzHDwDX9Q&t=1560)

**AQAffinity**（AQ 是 SandboxAQ 的品牌前缀）是 SandboxAQ 与 OpenFold 联盟合作、**构建在 OpenFold3 之上**的亲和力预测模型。分工是这样的：

- **OpenFold3**：预测蛋白质结构 + 配体在结合位点的**位姿（pose）**；
- **AQAffinity**：在此之上额外输出一个数——**亲和力**，粗略地说就是"这个分子对这个蛋白有多粘"。

![AQAffinity：构建在 OpenFold3 之上的亲和力预测模型](assets/OpenFold3%20and%20AQAffinity：%20A%20New%20Era%20of%20Open-Source%20Molecular%20Modeling/01119.webp)

为什么需要这个数？Adam 用受体举例：你想让一个分子**牢牢驻留**在体内某个受体上，挡住别的激素——分子必须"粘得住"，这就需要对该位点有好的亲和力（[【跳转到 26:43】](https://www.youtube.com/watch?v=_DUzHDwDX9Q&t=1603)）。

### 4.5 与现有方法对比：快数千倍，且不需要先有结构

[【跳转到 27:36】](https://www.youtube.com/watch?v=_DUzHDwDX9Q&t=1656)

亲和力测定当然已是药物发现管线的既有环节，但现状两难：

- **实验方法**：相对慢，且难以与计算模型串联；
- **传统计算方法**：慢、不够准，而且**必须先有结构作为输入**——只能用于"复杂数据已备齐"的一小部分任务。

AQAffinity 的愿景是放宽这个限制：**以远超 FEP（自由能微扰）计算的速度（约快数千倍）预测亲和力，且不需要那些精细的结构输入**——让亲和力评估能进入"大规模快速筛选"的场景（[【跳转到 28:04】](https://www.youtube.com/watch?v=_DUzHDwDX9Q&t=1684)）。

许可与开放程度：与 OpenFold3 相同的宽松许可、非常少的限制——**权重完全公开，可实验、可魔改（remix）**，模型托管在 Hugging Face。

## 五、为什么是现在：四十年的老领域，等来了临界点

[【跳转到 29:08】](https://www.youtube.com/watch?v=_DUzHDwDX9Q&t=1748)

AlQuraishi 回顾：计算机辅助药物设计（computer-aided drug design）不是新事物——**历史能追溯到 20 世纪中叶**，也确实长期在工业界发挥作用。真正的拐点是 AlphaFold：它是 2010 年代 AI 进展的"生长物"——**第一次能把结构数据、亲和力数据等各类物理测量喂给模型并得到高性能输出**，去年（2024）的诺贝尔化学奖是对这条线的确认。

更深一层：**OpenFold 联盟这种组织形态，在这个拐点之前根本不可能存在**——工业界没有理由资助一个学术倡议；正是这些工具"有用到足以推动业务"，才腾出了产研共建的空间。所以他判断：我们正处在**能力刚刚解锁、才刚开始刮开表层**的时刻——这些工具还处于"新生期（nascent）"，会变得更强大、更普适。

![为什么是现在：从计算机辅助药物设计到 AlphaFold 的拐点](assets/OpenFold3%20and%20AQAffinity：%20A%20New%20Era%20of%20Open-Source%20Molecular%20Modeling/01748.webp)

## 六、社区采用：两个"几乎前所未有"的项目

[【跳转到 32:24】](https://www.youtube.com/watch?v=_DUzHDwDX9Q&t=1944)

发布几个月，除了常规采用指标（产业与学术用户的求助与合作），AlQuraishi 重点介绍了两个规模空前的项目：

### 6.1 药企数据联盟（AISB）：把私有数据池化

[【跳转到 33:00】](https://www.youtube.com/watch?v=_DUzHDwDX9Q&t=1980)

一个由药企组成的联盟，**把各自的数据池起来，训练超越公开数据的 OpenFold 变体**。妙处在于：这些公司平时未必愿意彼此合作，却共同出资造了一个"**水涨船高**"的模型——每家都变得更强。

![药企数据联盟：把私有数据池化，共同训练超越公开数据的 OpenFold 变体](assets/OpenFold3%20and%20AQAffinity：%20A%20New%20Era%20of%20Open-Source%20Molecular%20Modeling/01980.webp)

### 6.2 OpenBind：让模型告诉我们要采什么数据

[【跳转到 33:50】](https://www.youtube.com/watch?v=_DUzHDwDX9Q&t=2030)

另一个是 **OpenBind**：**从零生成全新的结构与亲和力数据**，且从一开始就定位为全开源——不只服务 OpenFold，而是服务所有想造这类模型的人。OpenFold 在其中的角色非常有趣：**当"向导"**。我们已经知道这些模型有盲区、需要更多数据，但"该采哪些数据"过去靠拍脑袋；现在让模型自己指出：**哪些化学空间、哪些蛋白类别，对训练下一代共折叠模型最有信息量**。OpenFold 像一个 oracle，为 OpenBind 的数据采集排定优先级——采数据不再是"能采多少采多少"，而是瞄准最有影响力的蛋白与化合物。

（SandboxAQ 自己也是受益者：Adam 提到 OpenFold3 发布后，"超充"了他们的药物发现项目。）

## 七、AQAffinity 的差异化与它打开的新玩法

[【跳转到 36:16】](https://www.youtube.com/watch?v=_DUzHDwDX9Q&t=2176)

问：相对现有方案，AQAffinity 解决什么问题？未来走向哪？Adam 的三点定位：

- **技术路线**：从蛋白序列**直接**到亲和力的机器学习模型；同赛道最新的对手是 Boltz-2，AQAffinity 的架构部分受其启发；
- **相对 FEP 等慢方法**：不需要结构输入 + 纯粹的速度优势；
- **相对其他模型**：完全开源，且完全融入 OpenFold 生态——能借力整个社区。

![AQAffinity 是什么：OpenFold3 给结构与位姿，AQAffinity 再给出"有多粘"](assets/OpenFold3%20and%20AQAffinity：%20A%20New%20Era%20of%20Open-Source%20Molecular%20Modeling/01560.webp)

[【跳转到 37:00】](https://www.youtube.com/watch?v=_DUzHDwDX9Q&t=2220)

对药物发现的实际意义：**不用把自己锁死在某一个结构上，也不必等实验结构出炉**，分子搜索可以快得多。更激动人心的是那些"以前根本不可行"的搜索：在蛋白质组尺度上扫靶点、同时检查多个靶点、在不同靶点与不同分子假设之间来回迭代——只有在"不必为每个蛋白等一个结构好几年"的前提下才可行（他自己纠正：不是五年，但确实漫长）。

核心观点：这些技术让"选靶点 ↔ 提假设 ↔ 找分子"从**严格串行**变成**迭代闭环**——而这正是药物发现慢、失败率高的症结之一。

## 八、三方对未来的判断

### 8.1 Roy（NVIDIA）：2025 可用，2026 部署，然后是第三缩放定律

[【跳转到 40:28】](https://www.youtube.com/watch?v=_DUzHDwDX9Q&t=2428)

- **2025 = 模型开始"真的能用"**：至少在开放科学圈，这些模型首次在实验层面成立——跨治疗领域、难靶点、多种模态（从抗体、纳米抗体到小分子），大量论文（他点名 BoltzGen、Chai-2）覆盖数十个合作者的**前瞻性（prospective）验证**；
- **2026 = 部署之年**：J.P. Morgan 医疗健康大会前后，技术生物学基础模型公司与药企的整合交易密集出现——不再只是联合研发，而是**软件级部署**；产业对这些模型与软件的信任度显著上升（当然还需微调，尚未完全"开箱即用"）（[【跳转到 41:40】](https://www.youtube.com/watch?v=_DUzHDwDX9Q&t=2500)）；
- **第三缩放定律**：预训练、后训练之外，行业此前在**推理时扩展（test-time scaling）**上滞后；现在模型足够强、足够生成式，推理阶段的算力投入开始产生回报——这是 NVIDIA 在生物学里看到的新前沿（[【跳转到 42:44】](https://www.youtube.com/watch?v=_DUzHDwDX9Q&t=2564)）；
- **更远期**：突破体系大小限制 → 更大的生物分子系统与通路 → **多模态、多尺度的虚拟细胞**：把整个细胞表示为数字孪生；冷冻电镜（cryo-EM）等实验创新在铺路（[【跳转到 43:34】](https://www.youtube.com/watch?v=_DUzHDwDX9Q&t=2614)，[【跳转到 43:59】](https://www.youtube.com/watch?v=_DUzHDwDX9Q&t=2639)）。

![2026 部署之年：模型软件直接进驻药企，JPM 大会交易密集](assets/OpenFold3%20and%20AQAffinity：%20A%20New%20Era%20of%20Open-Source%20Molecular%20Modeling/02500.webp)

![第三缩放定律：预训练、后训练之后，推理时扩展成为生物学新前沿](assets/OpenFold3%20and%20AQAffinity：%20A%20New%20Era%20of%20Open-Source%20Molecular%20Modeling/02564.webp)

![虚拟细胞：把整个细胞表示为数字孪生，多模态多尺度生物学](assets/OpenFold3%20and%20AQAffinity：%20A%20New%20Era%20of%20Open-Source%20Molecular%20Modeling/02639.webp)

### 8.2 Adam（SandboxAQ）：从"串行"到"迭代"

[【跳转到 44:58】](https://www.youtube.com/watch?v=_DUzHDwDX9Q&t=2698)

他在 JPM 现场的观察与 Roy 一致：SandboxAQ 宣布了两个药物发现合作——**MapLight** 与**巴林王国**。而他对技术路线的判断更"狠"（[【跳转到 51:03】](https://www.youtube.com/watch?v=_DUzHDwDX9Q&t=3063)）：

现在的药物发现是"卡通式"的：生物学家先找靶点——然后"生物学被遗忘四五年"（他自嘲这有点夸张）——化学家做出在既定目标上表现很好的分子——进入临床，**十次里九次失败**。逐条排查失败原因，最核心的一条：**最初的假设（那个靶点、那条通路）从一开始就不太对**。为什么改不了？因为为新靶点拿新分子太难，而且生物学与化学被当成两个割裂的阶段：先做生物学，再做化学。SandboxAQ 的愿景是把两者变成**一个能自我反馈的统一迭代过程**——别等到最后一刻才知道"大体量上会发生什么"。

### 8.3 Mohammed（AlQuraishi）：自底向上与自顶向下会师

[【跳转到 46:30】](https://www.youtube.com/watch?v=_DUzHDwDX9Q&t=2790)

他把未来分成三个时间尺度：

- **1–2 年**：更大的体系——多蛋白、多核酸组成的分子机器（细胞里的东西从不孤立存在）；这是共折叠方法的主场，也是 OpenFold 打算引领的方向（[【跳转到 47:20】](https://www.youtube.com/watch?v=_DUzHDwDX9Q&t=2840)）；
- **2–5 年**：**构象系综（conformational ensembles）**——蛋白不是刚性物体，今天的刚体建模只是简化；蛋白乃至药物的功能常常依赖固有柔性，要能表示并预测构象系综与构象动力学；
- **5–10 年（但"有生之年"可见）**：**自底向上与自顶向下会师**（[【跳转到 48:27】](https://www.youtube.com/watch?v=_DUzHDwDX9Q&t=2907)）。Arc Institute、Chan Zuckerberg Biohub 等已在构建"虚拟细胞"模型——在细胞层面（如转录状态）自顶向下建模；而 OpenFold3 这类模型在原子层面自底向上建模。两者相差几个数量级的空间分辨率。把它们连起来——**细胞模型的生理学 + 分子模型的机理与因果**——就是把系统生物学"规模化、分子级落地"。他怀疑这将占据未来 5–10 年，并最终改变治疗学：**从设计单个分子，走向设计并调控通路与系统**（[【跳转到 49:00】](https://www.youtube.com/watch?v=_DUzHDwDX9Q&t=2940)）。

## 九、如何参与：模型、代码、算力的入口

[【跳转到 52:27】](https://www.youtube.com/watch?v=_DUzHDwDX9Q&t=3147)

![参与入口汇总：OpenFold3/AQAffinity 模型、NIM 服务、Hugging Face 与联盟链接](assets/OpenFold3%20and%20AQAffinity：%20A%20New%20Era%20of%20Open-Source%20Molecular%20Modeling/03147.webp)

- **OpenFold 联盟**：官网 **openfold.io** 是所有活动的枢纽；模型代码在 **GitHub 的 OpenFold3 仓库**，有问题提 issue 即可（[【跳转到 53:05】](https://www.youtube.com/watch?v=_DUzHDwDX9Q&t=3185)）；
- **NVIDIA**：**build.nvidia.com** 上可试用 **OpenFold3 NIM** 微服务；模型与工具（如 cuEquivariance）的仓库持续更新，欢迎 issue 反馈；创业公司可申请 **NVIDIA Inception 计划**——已有 3500+ 医疗健康与生命科学初创加入（[【跳转到 53:42】](https://www.youtube.com/watch?v=_DUzHDwDX9Q&t=3222)，[【跳转到 54:32】](https://www.youtube.com/watch?v=_DUzHDwDX9Q&t=3272)）；
- **SandboxAQ**：AQAffinity 托管在 **Hugging Face**，完全开源、下载即用；提问或洽谈合作可通过其联系入口。

## 小结

- OpenFold 联盟 = 把 DeepMind 式"团队科学"搬进学术界：学界实验室 + 全职团队 + 产业伙伴（算力/资金/方向校准），OpenFold3 是其旗舰开源共折叠模型。
- OpenFold3 的两个"最"：**许可最宽松 + 训练最充分**（数百万 GPU 小时）；方法论核心是**飞轮**——用初始模型产出合成数据训练更强版本，"把算力变成数据"。
- NVIDIA 的角色不只是算力：BioNeMo 平台 + Clara 开放模型 + **cuEquivariance 定制内核**（针对三角算子），OpenFold3 发布即接入；合作案例：GPU 利用率 95%、数据管线 3 个月 → 3 周。
- AQAffinity = OpenFold3 之上的"亲和力头"：在结构 + 位姿之外再加"有多粘"这一个数；相对 FEP 快约数千倍、无需先有结构；权重全开、上架 Hugging Face。
- 采用的两个标志：药企数据联盟（私有数据池化，训练超越公开数据的变体）与 OpenBind（让模型当 oracle，指导全新开源数据的采集）。
- 时间表共识：2025 模型实验级可用（抗体/纳米抗体/小分子多模态前瞻验证）→ 2026 **部署之年** → 之后是**第三缩放定律**（推理时扩展）与**虚拟细胞**（多尺度生物学）。
- 药物发现方法论的最大改动：把"选靶点 → 设计分子"的串行流程改成**迭代闭环**——九成临床失败源于最初假设，闭环迭代才是治本。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| OpenFold Consortium | OMSF 旗下的产研联盟：学界实验室 + 全职团队 + 产业伙伴，维护 OpenFold 系开源模型 |
| OpenFold3 | 开源共折叠模型：蛋白 + 小分子/抗体/核酸相互作用结构预测，AF3 的开源复刻 |
| AQAffinity | SandboxAQ 与联盟合作、构建在 OpenFold3 之上的亲和力预测模型（序列 → 亲和力） |
| LQM | Large Quantitative Model，SandboxAQ 对"非 LLM 的大规模定量模型"的统称 |
| S 数据集 | SandboxAQ 发布的最大带亲和力标注的 3D 结构共折叠数据集 |
| BioNeMo | NVIDIA 面向生命科学的平台：加速库、工具、模型与数据集 |
| cuEquivariance | NVIDIA 为三角算子等几何感知算子开发的定制 CUDA 内核库 |
| NIM | NVIDIA 推理微服务；OpenFold3 NIM 可在 build.nvidia.com 试用 |
| FEP | 自由能微扰：传统高精度亲和力计算方法，慢且需要结构 |
| pose（位姿） | 配体在结合位点中的三维摆放方式 |
| 药企数据联盟 | 各药企把私有数据池化，共同训练超越公开数据的 OpenFold 变体 |
| OpenBind | 从零生成全开源结构与亲和力数据的计划，用 OpenFold 当"数据采集向导" |
| 第三缩放定律 | 预训练、后训练之外的第三个扩展维度：推理时（test-time）算力扩展 |
| 虚拟细胞 (virtual cell) | 把整个细胞表示为可计算数字孪生的多尺度生物学愿景 |
