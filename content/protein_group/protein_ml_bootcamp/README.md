# 系列：Rosetta ML Bootcamp — 蛋白质建模与设计的机器学习方法

- **平台**：YouTube
- **来源**：RosettaCommons 频道播放列表《Machine Learning Methods for Protein Modeling and Design - A Rosetta Bootcamp》（`PLFavr8uo6kSpbIQKodSYA6reiG-RDXnWq`）
- **主讲**：课程讲师 Nick Randolph（UNC Chapel Hill）；助教 Fatima Hitawala、Amrita Nallathambi、Ben Orr
- **背景**：2024 年 10 月 Rosetta Commons 主办的机器学习训练营（ML Bootcamp），由 Rosetta Commons 与美国国家科学基金会（NSF）支持
- **视频数**：18
- **已整理**：前 7 讲（总览与基础 + PyMOL/VS Code 工具课 + 结构预测导论 + AlphaFold2/OpenFold 结构预测 + Git 版本控制 + ESMFold 结构预测 + AlphaFold3 结构预测）
- **主题**：面向"用机器学习做蛋白质建模与设计"的系列训练营。前半程打地基——蛋白质与深度学习复习、常用工具（PyMOL / VS Code）、结构预测（Anfinsen 假说、Levinthal 悖论、CASP、评价指标、AlphaFold）；后半程进入设计主流程——**AlphaFold2/OpenFold/ESMFold/AlphaFold3 做结构预测 → RFdiffusion 生成骨架 → ProteinMPNN/LigandMPNN 设计序列 → DiffDock-PP 做分子对接**。

## 视频索引

| # | 标题 | 时长 | 视频演说图文稿 | 博客 | 配图 | 原视频 |
| ---: | --- | ---: | --- | --- | ---: | --- |
| 01 | Introduction to Protein Design with ML | 10:33 | [文稿](transcripts/第01讲_Introduction%20to%20Protein%20Design%20with%20ML.md) | [博客](blog/第01讲_Introduction%20to%20Protein%20Design%20with%20ML.md) | 10 | [YouTube](https://youtu.be/ekeXqoPSusI) |
| 02 | PyMol and VS Code (Mini-session) | 29:40 | [文稿](transcripts/第02讲_PyMol%20and%20VS%20Code%20%28Mini-session%29.md) | [博客](blog/第02讲_PyMol%20and%20VS%20Code%20%28Mini-session%29.md) | 16 | [YouTube](https://youtu.be/7fh90mdg2pI) |
| 03 | Protein Structure Prediction Introduction | 20:22 | [文稿](transcripts/第03讲_Protein%20Structure%20Prediction%20Introduction.md) | [博客](blog/第03讲_Protein%20Structure%20Prediction%20Introduction.md) | 11 | [YouTube](https://youtu.be/NPmz1ln9AYQ) |
| 04 | Structure Prediction with AlphaFold2 and OpenFold | 1:39:36 | [文稿](transcripts/第04讲_Structure%20Prediction%20with%20AlphaFold2%20and%20OpenFold.md) | [博客](blog/第04讲_Structure%20Prediction%20with%20AlphaFold2%20and%20OpenFold.md) | 16 | [YouTube](https://youtu.be/Y5-lhdwdJC0) |
| 05 | Version Control with Git (Mini-session) | 11:31 | [文稿](transcripts/第05讲_Version%20Control%20with%20Git%20%28Mini-session%29.md) | [博客](blog/第05讲_Version%20Control%20with%20Git%20%28Mini-session%29.md) | 3 | [YouTube](https://youtu.be/uieL4B09SK8) |
| 06 | Structure Prediction with ESMFold | 10:32 | [文稿](transcripts/第06讲_Structure%20Prediction%20with%20ESMFold.md) | [博客](blog/第06讲_Structure%20Prediction%20with%20ESMFold.md) | 7 | [YouTube](https://youtu.be/IkckNa6fVXo) |
| 07 | Structure Prediction with AlphaFold3 | 42:51 | [文稿](transcripts/第07讲_Structure%20Prediction%20with%20AlphaFold3.md) | [博客](blog/第07讲_Structure%20Prediction%20with%20AlphaFold3.md) | 11 | [YouTube](https://youtu.be/zkvk2k7KE8M) |
| 08 | Developing ML models with PyTorch (Mini-session) | 36:49 | — | — | — | [YouTube](https://youtu.be/ge-Tf6OwaoQ) |
| 09 | Backbone Generation Introduction | 11:05 | — | — | — | [YouTube](https://youtu.be/3z2Q4DTb4-A) |
| 10 | Backbone Generation with RFdiffusion | 25:35 | — | — | — | [YouTube](https://youtu.be/gYJLw40UojU) |
| 11 | Backbone Generation with RFdiffusion All-Atom | 13:41 | — | — | — | [YouTube](https://youtu.be/2FHNM6USHw0) |
| 12 | CPU vs GPU Hardware for Protein Design (Mini-session) | 15:36 | — | — | — | [YouTube](https://youtu.be/GJIjlmSpnsM) |
| 13 | Sequence Design Introduction | 13:46 | — | — | — | [YouTube](https://youtu.be/a975ZPy4tdw) |
| 14 | Sequence Design with ProteinMPNN | 33:41 | — | — | — | [YouTube](https://youtu.be/zbpWFKjiXEk) |
| 15 | Sequence Design with LigandMPNN | 17:39 | — | — | — | [YouTube](https://youtu.be/5drpdgMtwu4) |
| 16 | Protein Docking Introduction | 11:18 | — | — | — | [YouTube](https://youtu.be/Jq7jD6LvLeU) |
| 17 | Protein Docking with DiffDock-PP | 21:19 | — | — | — | [YouTube](https://youtu.be/HSOscmos6nE) |
| 18 | Other Protein ML Tools | 25:35 | — | — | — | [YouTube](https://youtu.be/DA0aMt_f2T0) |

> 说明：本系列按播放列表顺序整理，目前收录**前 7 讲**的图文稿与博客，其余讲次待后续整理。

## 博客结构速览

**第 1 讲：用机器学习做蛋白质设计，先要打好「蛋白质」和「深度学习」两块地基**

- 一、蛋白质是生命的执行者，而氨基酸是它的 20 种「积木块」
- 二、R 基团的化学性质，决定了氨基酸「住在哪、干什么」
- 三、肽键把氨基酸串成链，二面角决定骨架怎么扭
- 四、蛋白质有四个结构层次，本课程主要研究三级和四级
- 五、深度学习的成败，首先取决于数据质量
- 六、三份数据各司其职：训练、验证、测试
- 七、损失函数是模型学习的「方向盘」
- 八、前向传播与反向传播：深度学习是如何「学」的
- 九、训练是一个循环：训练→算损失→更新参数→验证
- 十、既然有测试集，为什么还要验证集？

**第 2 讲：用 PyMOL 看结构、用 VS Code 连集群——蛋白质建模的两把必备工具**

- 一、PyMOL 是什么：一个内置 Python 的分子可视化软件
- 二、PyMOL 界面总览：命令行、选择模式与序列面板
- 三、从 fetch 到清理：最常用的 PyMOL 命令
- 四、A / S / H：控制"显示什么"的核心三键
- 五、上色的威力：element、SS、B Factor 与按链上色
- 六、对齐与选区：把结构叠合、把 CDR 存成对象
- 七、Cartoon transparency 与出图：把重点"提"出来
- 八、VS Code 与扩展：最流行的 IDE 长什么样
- 九、用 VS Code SSH 远程登录计算集群
- 十、Jupyter、tmux 与 Protein Viewer：远程科研三件套

**第 3 讲：蛋白质结构预测入门——能量景观解释了「为什么能折叠」，评价指标决定了「预测得好不好」**

- 一、结构预测要回答的核心问题：给定一维序列，求三维结构
- 二、Anfinsen 假说与 Levinthal 悖论：为什么蛋白质能找到天然结构
- 三、折叠漏斗：能量景观不是高尔夫球场
- 四、CASP：用「盲测」客观衡量结构预测
- 五、从片段组装到共进化：CASP 早期的两支主力
- 六、深度学习登场：从 CNN 到 AlphaFold1
- 七、评价指标决定了「预测得好不好」：RMSD、lDDT、GDT、TM-score 各有分工
- 八、指标怎么选：没有万能指标，AlphaFold 还会自带置信度
- 九、结构预测能拿来做什么：从补全实验结构到指导设计

**第 4 讲：用 AlphaFold2 / OpenFold 做结构预测——从 CASP14 的惊艳登场，到 Evoformer、结构模块与训练损失**

- 一、AlphaFold2 在 CASP14 上的登场：把中位 RMSD 从约 3 Å 拉到约 1 Å
- 二、AlphaFold2 与 OpenFold：一份「忠实但可训练」的复现
- 三、AlphaFold2 的输入输出：MSA + 模板进，结构与置信度出
- 四、性能与置信度校准：RMSD 分布、侧链 χ1、pLDDT/pTM
- 五、MSA 有多重要：N_eff 曲线与消融实验
- 六、AlphaFold2 整体架构：一条从序列到 3D 结构的流水线
- 七、Evoformer 内部：注意力、门控与三角操作
- 八、结构模块：残基气体、IPA、SE(3) 与 FAPE 损失
- 九、训练损失与两个阶段：FAPE、distogram、masked MSA 与置信度
- 十、AlphaFold2 的局限：它不是完美系统
- 十一、扩展生态：从 Multimer 到 BindCraft

**第 5 讲：用 Git 做版本控制——从「为什么」到亲手跑一遍 init、add、commit、branch、merge**

- 一、为什么需要 Git：多人协同时不要互相覆盖
- 二、Git 的三个区域：工作区、暂存区、仓库
- 三、动手教程：init → status → add → commit
- 四、分支与合并：branch / checkout / merge，以及冲突处理

**第 6 讲：用 ESMFold 做结构预测——不靠 MSA，让蛋白质语言模型直接「读出」结构**

- 一、ESM 家族：从 Facebook AI Research 到 Evolutionary Scale
- 二、ESMFold 与 AlphaFold 的根本区别：用语言模型取代 MSA 和模板
- 三、为什么语言模型可以预测结构：序列数据远多于结构数据
- 四、性能：有 MSA 时略逊，无 MSA 时反超
- 五、ESMFold 的架构：ESM-2 → 折叠主干 → 结构模块
- 六、扩展：ESM Atlas、可编程设计语言与 ESM3

**第 7 讲：用 AlphaFold3 做结构预测——一个同时建模蛋白质、核酸、小分子与离子的统一模型**

- 一、AlphaFold3 的新意：不止蛋白质，还能预测核酸、小分子、离子与共价修饰
- 二、置信度校准：pLDDT / pTM / ipTM 都能信
- 三、整体架构：从输入到结构的一条新流水线
- 四、Token 化难题：用小分子和修饰「拆成原子」来解决
- 五、从 Evoformer 到 Pairformer：MSA 只负责「提取」，不再一路携带
- 六、扩散模块：用「加噪—去噪」取代确定性的结构模块
- 七、AlphaProteo 实例：扩散过程长什么样
- 八、扩散模块与结构模块的差别：确定性 vs 随机性
- 九、训练损失与等变性：用数据增强而非架构来保证等变
- 十、局限（一）：对困难靶点需要海量随机种子，而且不强制手性
- 十一、局限（二）：幻觉、断链与冲突
- 十二、局限（三）：多状态采样不可靠，且仍是闭源
- 十三、复现与替代：HelixFold3、Chai-1 与 Lucidrains

## 核心知识点速览

- **第 1 讲**：蛋白质由 20 种标准氨基酸组成，骨架相同、性质差异由 **R 基团（侧链）**决定——非极性残基填充核心、极性残基多居表面、带电残基参与盐桥；氨基酸靠**肽键**连成多肽，骨架扭转由 **φ/ψ 二面角**描述；结构分**一级→二级（α 螺旋/β 折叠）→三级→四级**四层，本课程重点研究三级与四级，且三级结构是动态的、并非所有蛋白都有稳定结构（内在无序）。深度学习侧：数据质量是第一位（**垃圾进，垃圾出**），数据按**训练/验证/测试（约 80/10/10）**划分；**损失函数**衡量误差、驱动参数更新；学习靠**前向+反向传播**，单层只是「线性变换 + 非线性激活」，复杂性来自层层堆叠；训练是一遍遍循环直到验证分数满意；**验证集用于选架构、测试集用于终考**（因验证集参与决策会轻微泄漏信息）。
- **第 2 讲**：**PyMOL** 是内置 Python 的分子可视化软件——`fetch` 取结构、`remove hetatm/water` 清理、`A/S/H`（Action/Show/Hide）控制显示、`color` 按 element/SS/**B Factor**/chain 上色（B Factor 在 AlphaFold 输出里代表**逐残基置信度**）、`align` 做结构+序列比对、`set cartoon_transparency, 数值, 对象` 高亮重点、`ray`+`save image` 出发表级图片；命令语法见 PyMOLWiki。**VS Code** 是最流行的 IDE，装 **Remote-SSH** 扩展后输入 `邮箱ID@主机名` 即可 SSH 登录计算集群；远程科研三件套——**Jupyter notebook**（集群上就地绘图、markdown 做大纲）、**tmux**（后台任务不因关电脑而中断）、**Protein Viewer**（远程直接看 PDB，不用搬数据）。
- **第 3 讲**：结构预测 = 由线性氨基酸序列求三维（三级）结构，多链时还要给出四级相互作用。**Anfinsen 假说**：天然结构处在自由能极小值；**Levinthal 悖论**：101 个残基就有超过 3²⁰⁰ 种构象，暴力搜索不可行；**折叠漏斗**（能量景观不是只有一个洞的高尔夫球场，而是带方向性引导）解释了自然为何能快速折叠。**CASP**（1994 年起、每两年一次）用未发表结构做盲测推动领域进步；方法从**片段组装 → MSA + 共进化 → CNN → AlphaFold1（CASP13，非端到端，用深度学习势能引导能量极小化）**一路演进。四个评价指标各有分工：**RMSD**（单位 Å、依赖长度、最简单）、**lDDT**（(0,1]、不依赖长度、看局部/结构域）、**GDT**（%、多阈值多次对齐、更稳健）、**TM-score**（(0,1]、不依赖长度、要求序列一致）；AlphaFold2 自带 **pLDDT/pTM** 置信度，TM-score 常用经验阈值 **0.5**。应用：**分子置换**（补全/增强实验结构）、解读实验结果、功能预测与假说检验、作为设计与工程的起点。
- **第 4 讲**：AlphaFold2 在 **CASP14**（2018）以**端到端**方式把中等难度靶点的中位 Cα RMSD 从约 **3 Å** 拉到约 **1 Å**；**OpenFold** 是它"忠实但可训练"的开源复现（快 **3–5 倍**、更省显存、改用 **PyTorch**；原版用 **JAX**）。输入 = **MSA + 模板**，输出 = **3D 结构 + 置信度**（逐残基 **pLDDT**、整体 **pTM**、成对 **PAE**），其中 **MSA 是最重要的输入**（仅一条序列时表现大跌，约 30 条后趋缓）。架构：序列 →（序列库搜索得 MSA / 结构库搜索得模板）→ **Evoformer（48 blocks）** → 单链表示 + 配对表示 → **结构模块（8 blocks）** → 3D 结构，**recycling 三次**（共前向四次）。Evoformer 用**按行/按列门控注意力**更新 MSA（行=序列内、列=跨物种进化史），用**三角操作**给配对表示注入**三角不等式**等几何先验（三元组残基互相交流）；结构模块从**黑洞初始化**出发、以**残基气体**打破链式结构以并行精修，用 **IPA** 与 **SE(3)** 的**不变性/等变性**、以 **FAPE** 为主损失迭代展开成原子坐标（残基框架由 N–Cα–C 定义，侧链用 χ 角参数化）。训练损失 = FAPE + 辅助（Cα FAPE + χ1 MSE）+ distogram + masked MSA + 置信度，微调再加"实验解析残基/结构违规"；**分两阶段训练**是为避免损失景观过于崎岖。局限：突变效应、全新折叠、多状态、无序区（只能拉出"意面"）、不显式建模非蛋白分子。生态：**AlphaFold-Multimer**（对称性 + 跨链 MSA + 裁剪，**DockQ** 更好）、**AlphaFold DB**（两亿+单体结构）、**AFsample**（dropout + 更多 recycling 造多样性，约千倍算力）、**AF-Cluster**（MSA 聚类偏向状态）、**AF2Rank**（把置信度当能量函数给 decoy 排序）、**EvoPro/Marita**（遗传算法工作流）、**BindCraft**（AlphaFold-Multimer 反向传播设计序列）。
- **第 5 讲**：Git 用"**共享仓库 + 分支 + 合并**"替代"复制目录/互相覆盖"。仓库分三区：**工作目录 →（`git add`）→ 暂存区 →（`git commit`）→ `.git` 仓库**，`git checkout` 可把版本拉回工作区。最小流程：`git init` → `git status` → `git add` → `git commit -m "..."`；新文件先是 **untracked（红）**，add 后进入暂存区并转为追踪（绿），改过已提交的文件要重新 add。`git branch <名>` 建分支、`git checkout <名>` 切换，留在 main 上 `git merge <名>` 合并；两边改同一处会产生**冲突（conflict）**，需人工逐一处理、保留双方改动后再提交。
- **第 6 讲**：ESM 家族由 FAIR 发起、后独立为 **Evolutionary Scale**，成员含 **ESM2**（语言模型）、**ESMFold**、**ESM-MSA**、**ESM-1v**（变异效应）、**ESM-IF1**（反向折叠）、**ESM3**（同时推理结构/序列/功能）。**ESMFold 的核心创新**是**不用 MSA、不用模板**，改用**蛋白质语言模型**把整条序列编码成嵌入再送进折叠网络——因为它把**数十亿条序列**（远多于 PDB 的约 20 万结构）通过**掩码语言建模**内化成了参数。性能上：**有 MSA 时略逊于 AlphaFold/RoseTTAFold，无 MSA 时明显更好**。架构：单序列 → **ESM-2** → **Folding Trunk（48 blocks，用序列表示 + 自注意力替代按列注意力 + 三角更新）** → **Structure Module（8 blocks，与 OpenFold 相同）** → 结构与置信度 + recycling；配对表示由序列外积得到。损失与 AlphaFold 基本相同（去掉 masked MSA），局限类似（多状态、其他分子），但**从头设计与突变**相对没那么糟（仍未真正解决）。扩展：**ESM Atlas**（7.72 亿条预测结构，多来自宏基因组）、可编程设计语言、**ESM3**。
- **第 7 讲**：AlphaFold3 同时建模**蛋白质、核酸、小分子、离子与共价修饰**。**统一 token 化**是前提：蛋白质/核酸用构筑单元当 token，**小分子与共价修饰的每个原子拆成独立 token**（单链表示 token×通道，配对表示 token×token×通道）；小分子先由 RDKit 生成若干**代表构象**。架构替换：**MSA module（4 blocks）** 一次性提取信息、**不再一路携带巨型 MSA 表示**（省显存），**Pairformer（48 blocks）** 取代 Evoformer，**扩散模块（3+24+3 blocks）** 取代结构模块，另有 Template module、Input embedder、Confidence module（4 blocks）。**扩散**：前向加噪到随机先验、只学习逆向去噪；约第 60 步收敛到整体结构、其余步骤精修；随机过程，**每运行一次结果都不同**（区别于结构模块的确定性）。损失把 **FAPE 换成 diffusion loss**，另有 distogram 与 confidence；**不再约束键长/键角、不强制手性**，**等变性靠数据增强（随机旋转/平移）而非架构**（引发"等变性是否必须进架构"的争议）。置信度 pLDDT↔lDDT、pTM↔TM、ipTM↔界面 lDDT 校准良好。局限：困难靶点需**海量 seed**（抗体 5000 个 seed 才约 60%）、**手性错误约 4–5%**、**幻觉**（把无序区做得"像蛋白质"，甚至用 AF2-M 结构微调以在不确定处产生"意面"）、**链重叠冲突**（扩散损失无物理约束）、**多状态占据比不可靠**、**仍是服务器闭源**（承诺约十一月开源）。复现：**HelixFold3**、**Chai-1**、**Lucidrains 的纯 PyTorch 复现**。

## 相关资源

- Rosetta Commons 官网：https://rosettacommons.org/
- 播放列表：https://www.youtube.com/playlist?list=PLFavr8uo6kSpbIQKodSYA6reiG-RDXnWq
- RosettaCommons YouTube 频道：https://www.youtube.com/@RosettaCommons
