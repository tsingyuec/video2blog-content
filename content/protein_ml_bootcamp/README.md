# 系列：Rosetta ML Bootcamp — 蛋白质建模与设计的机器学习方法

- **平台**：YouTube
- **来源**：RosettaCommons 频道播放列表《Machine Learning Methods for Protein Modeling and Design - A Rosetta Bootcamp》（`PLFavr8uo6kSpbIQKodSYA6reiG-RDXnWq`）
- **主讲**：课程讲师 Nick Randolph（UNC Chapel Hill）；助教 Fatima Hitawala、Amrita Nallathambi、Ben Orr
- **背景**：2024 年 10 月 Rosetta Commons 主办的机器学习训练营（ML Bootcamp），由 Rosetta Commons 与美国国家科学基金会（NSF）支持
- **视频数**：18
- **已整理**：前 3 讲（总览与基础 + PyMOL/VS Code 工具课 + 结构预测导论）
- **主题**：面向"用机器学习做蛋白质建模与设计"的系列训练营。前半程打地基——蛋白质与深度学习复习、常用工具（PyMOL / VS Code）、结构预测（Anfinsen 假说、Levinthal 悖论、CASP、评价指标、AlphaFold）；后半程进入设计主流程——**AlphaFold2/OpenFold/ESMFold/AlphaFold3 做结构预测 → RFdiffusion 生成骨架 → ProteinMPNN/LigandMPNN 设计序列 → DiffDock-PP 做分子对接**。

## 视频索引

| # | 标题 | 时长 | 视频演说图文稿 | 博客 | 配图 | 原视频 |
| ---: | --- | ---: | --- | --- | ---: | --- |
| 01 | Introduction to Protein Design with ML | 10:33 | [文稿](transcripts/第01讲_Introduction%20to%20Protein%20Design%20with%20ML.md) | [博客](blog/第01讲_Introduction%20to%20Protein%20Design%20with%20ML.md) | 10 | [YouTube](https://youtu.be/ekeXqoPSusI) |
| 02 | PyMol and VS Code (Mini-session) | 29:40 | [文稿](transcripts/第02讲_PyMol%20and%20VS%20Code%20%28Mini-session%29.md) | [博客](blog/第02讲_PyMol%20and%20VS%20Code%20%28Mini-session%29.md) | 16 | [YouTube](https://youtu.be/7fh90mdg2pI) |
| 03 | Protein Structure Prediction Introduction | 20:22 | [文稿](transcripts/第03讲_Protein%20Structure%20Prediction%20Introduction.md) | [博客](blog/第03讲_Protein%20Structure%20Prediction%20Introduction.md) | 11 | [YouTube](https://youtu.be/NPmz1ln9AYQ) |
| 04 | Structure Prediction with AlphaFold2 and OpenFold | 1:39:36 | — | — | — | [YouTube](https://youtu.be/Y5-lhdwdJC0) |
| 05 | Version Control with Git (Mini-session) | 11:31 | — | — | — | [YouTube](https://youtu.be/uieL4B09SK8) |
| 06 | Structure Prediction with ESMFold | 10:32 | — | — | — | [YouTube](https://youtu.be/IkckNa6fVXo) |
| 07 | Structure Prediction with AlphaFold3 | 42:51 | — | — | — | [YouTube](https://youtu.be/zkvk2k7KE8M) |
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

> 说明：本系列按播放列表顺序整理，目前仅收录**前 3 讲**的图文稿与博客，其余讲次待后续整理。

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

## 核心知识点速览

- **第 1 讲**：蛋白质由 20 种标准氨基酸组成，骨架相同、性质差异由 **R 基团（侧链）**决定——非极性残基填充核心、极性残基多居表面、带电残基参与盐桥；氨基酸靠**肽键**连成多肽，骨架扭转由 **φ/ψ 二面角**描述；结构分**一级→二级（α 螺旋/β 折叠）→三级→四级**四层，本课程重点研究三级与四级，且三级结构是动态的、并非所有蛋白都有稳定结构（内在无序）。深度学习侧：数据质量是第一位（**垃圾进，垃圾出**），数据按**训练/验证/测试（约 80/10/10）**划分；**损失函数**衡量误差、驱动参数更新；学习靠**前向+反向传播**，单层只是「线性变换 + 非线性激活」，复杂性来自层层堆叠；训练是一遍遍循环直到验证分数满意；**验证集用于选架构、测试集用于终考**（因验证集参与决策会轻微泄漏信息）。
- **第 2 讲**：**PyMOL** 是内置 Python 的分子可视化软件——`fetch` 取结构、`remove hetatm/water` 清理、`A/S/H`（Action/Show/Hide）控制显示、`color` 按 element/SS/**B Factor**/chain 上色（B Factor 在 AlphaFold 输出里代表**逐残基置信度**）、`align` 做结构+序列比对、`set cartoon_transparency, 数值, 对象` 高亮重点、`ray`+`save image` 出发表级图片；命令语法见 PyMOLWiki。**VS Code** 是最流行的 IDE，装 **Remote-SSH** 扩展后输入 `邮箱ID@主机名` 即可 SSH 登录计算集群；远程科研三件套——**Jupyter notebook**（集群上就地绘图、markdown 做大纲）、**tmux**（后台任务不因关电脑而中断）、**Protein Viewer**（远程直接看 PDB，不用搬数据）。
- **第 3 讲**：结构预测 = 由线性氨基酸序列求三维（三级）结构，多链时还要给出四级相互作用。**Anfinsen 假说**：天然结构处在自由能极小值；**Levinthal 悖论**：101 个残基就有超过 3²⁰⁰ 种构象，暴力搜索不可行；**折叠漏斗**（能量景观不是只有一个洞的高尔夫球场，而是带方向性引导）解释了自然为何能快速折叠。**CASP**（1994 年起、每两年一次）用未发表结构做盲测推动领域进步；方法从**片段组装 → MSA + 共进化 → CNN → AlphaFold1（CASP13，非端到端，用深度学习势能引导能量极小化）**一路演进。四个评价指标各有分工：**RMSD**（单位 Å、依赖长度、最简单）、**lDDT**（(0,1]、不依赖长度、看局部/结构域）、**GDT**（%、多阈值多次对齐、更稳健）、**TM-score**（(0,1]、不依赖长度、要求序列一致）；AlphaFold2 自带 **pLDDT/pTM** 置信度，TM-score 常用经验阈值 **0.5**。应用：**分子置换**（补全/增强实验结构）、解读实验结果、功能预测与假说检验、作为设计与工程的起点。

## 相关资源

- Rosetta Commons 官网：https://rosettacommons.org/
- 播放列表：https://www.youtube.com/playlist?list=PLFavr8uo6kSpbIQKodSYA6reiG-RDXnWq
- RosettaCommons YouTube 频道：https://www.youtube.com/@RosettaCommons
