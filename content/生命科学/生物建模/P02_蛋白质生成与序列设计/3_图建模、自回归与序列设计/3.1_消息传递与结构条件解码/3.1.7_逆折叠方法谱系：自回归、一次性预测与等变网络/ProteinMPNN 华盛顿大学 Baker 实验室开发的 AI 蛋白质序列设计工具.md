# ProteinMPNN：华盛顿大学 Baker 实验室开发的 AI 蛋白质序列设计工具

> 视频来源：[ProteinMPNN 华盛顿大学 Baker 实验室开发的 AI 蛋白质序列设计工具](https://www.bilibili.com/video/BV15DTj6ZEzU/)（约 7 分钟，含完整实操演示）

## 本讲要解决的核心问题（SCQA）

**背景**：AlphaFold 解决了「从序列预测结构」，RFdiffusion 能「无中生有」生成全新蛋白骨架——结构预测与骨架生成这两端都已经很成熟。

**冲突**：可当你手里只有一个「骨架」时——可能是天然蛋白抽掉侧链的坐标，也可能是 RFdiffusion 刚生成的全新骨架——上面并没有一条可用的氨基酸序列；传统蛋白质工程只在天然序列上做点突变，没法从结构出发直接写出一条完整序列。

**疑问**：给定一个蛋白质主链骨架，怎么反推出一条能折叠成这个骨架的氨基酸序列？

**回答（中心思想）**：这就是 ProteinMPNN 要解决的「逆折叠」（inverse folding）问题。它读入主链骨架坐标，用消息传递图神经网络逐位置预测氨基酸；本讲以 1ENH 小蛋白为例，完整走一遍「输入骨架 → 生成 32 条序列 → AlphaFold 回折验证」的闭环，并讲清每个参数、每个输出文件、每项结果指标怎么读。

## 一、ProteinMPNN 是什么：把「折叠」反过来做

### 1.1 与 AlphaFold 方向正好相反

AlphaFold 做的是从序列预测结构；ProteinMPNN 做的是相反方向——**给定一个蛋白质骨架，反推出可能折叠成这个骨架的氨基酸序列**，所以它解决的是 inverse folding（逆折叠）问题 [【跳转到 00:05】](https://www.bilibili.com/video/BV15DTj6ZEzU/?t=5)。

![AlphaFold 从序列到结构，ProteinMPNN 从结构反推序列](assets/ProteinMPNN%20华盛顿大学%20Baker%20实验室开发的%20AI%20蛋白质序列设计工具/00005.webp)

### 1.2 模型怎么「读懂」一个骨架

ProteinMPNN 的输入不是 DNA 序列，也不是普通氨基酸序列，而是**蛋白质三维结构中的主链骨架坐标**。模型把蛋白看成一张图 [【跳转到 00:30】](https://www.bilibili.com/video/BV15DTj6ZEzU/?t=30)：

- 每个残基是一个**节点**；
- 残基之间的空间距离和相对方向是**边**的信息；
- 通过 message passing neural network（消息传递图神经网络）把每个残基周围的几何环境整合起来，最后**逐个位置**预测这个位置适合放哪一种氨基酸。

![把蛋白看成图：残基为节点，距离与方向为边](assets/ProteinMPNN%20华盛顿大学%20Baker%20实验室开发的%20AI%20蛋白质序列设计工具/00030.webp)

### 1.3 它在设计流水线中的位置

传统蛋白质工程通常是在天然序列上做点突变；ProteinMPNN 则可以直接**从结构出发**设计序列。因此在现代蛋白质设计流程中，它经常处在「中间这一步」 [【跳转到 00:55】](https://www.bilibili.com/video/BV15DTj6ZEzU/?t=55)：

1. 前面用 **RFdiffusion** 生成一个理想骨架；
2. **ProteinMPNN** 负责给这个骨架配序列；
3. 后面再用 **AlphaFold 或 ESMFold** 回测：新序列是否还能折回目标结构。

这套「骨架 → 序列 → 回折验证」的三步，正是从头设计蛋白（binder 设计三部曲）的标准闭环。

## 二、实操：以 1ENH 为例跑通一次设计

### 2.1 为什么选 1ENH 这个测试题

演示选择的是 **1ENH**（PDB 编号）这个小型单链蛋白，而不是复杂酶蛋白——因为 1ENH 结构短、单链，没有底物、辅因子或催化三联体这些复杂限制，更适合用来演示 ProteinMPNN 的基本能力：给定骨架后重新设计序列，并验证能否返折回原骨架 [【跳转到 01:20】](https://www.bilibili.com/video/BV15DTj6ZEzU/?t=80)。

![1ENH 小型单链蛋白结构](assets/ProteinMPNN%20华盛顿大学%20Baker%20实验室开发的%20AI%20蛋白质序列设计工具/00080.webp)

### 2.2 参数设置逐项看

| 参数 | 本次取值 | 含义 |
| --- | --- | --- |
| 模型 | v_48_020 | ProteinMPNN 预训练版本 |
| 输入 | PDB 1ENH，链选择 A 链 | 待重设计的骨架 |
| fixed_positions | 保留部分结构核心位点 | 这些位置固定不变，模型不把整个蛋白完全随机重写 |
| Inverse | 未勾选 | 表示 fixed_positions 里的位置固定、其余位置允许设计 |
| omit_AA | 去掉 C | 半胱氨酸被排除，避免模型引入不必要的二硫键相关干扰 |
| num_seq | 32 | 生成 32 条候选序列 |
| sampling temperature | 0.1 | 控制采样随机性，温度越低设计越保守，越容易得到稳定结果 |

![参数设置总览](assets/ProteinMPNN%20华盛顿大学%20Baker%20实验室开发的%20AI%20蛋白质序列设计工具/00105.webp)

其中 fixed_positions（固定位置）与 omit_AA（排除氨基酸）是最常用的「约束」手段 [【跳转到 02:00】](https://www.bilibili.com/video/BV15DTj6ZEzU/?t=120)；而采样温度是新手最容易疑惑的参数——它与蛋白质表达或稳定的物理温度无关，只是一个计算参数 [【跳转到 02:25】](https://www.bilibili.com/video/BV15DTj6ZEzU/?t=145)。

![fixed_positions 与 omit_AA 的设置](assets/ProteinMPNN%20华盛顿大学%20Baker%20实验室开发的%20AI%20蛋白质序列设计工具/00120.webp)

### 2.3 运行后得到哪些文件

运行后程序会给出几个核心文件 [【跳转到 02:50】](https://www.bilibili.com/video/BV15DTj6ZEzU/?t=170)：

- `mpnn_results.csv`：记录每条序列的 ProteinMPNN score 和序列回收率；
- `PSSM.txt`：对应氨基酸被选概率矩阵；
- AlphaFold 回测结果 CSV：后续结构回测的指标；
- 此外还有预测结构文件和动画，可以用来观察设计序列是否还能折回目标骨架 [【跳转到 03:05】](https://www.bilibili.com/video/BV15DTj6ZEzU/?t=185)。

![输出文件清单](assets/ProteinMPNN%20华盛顿大学%20Baker%20实验室开发的%20AI%20蛋白质序列设计工具/00185.webp)

结果画面里蛋白整体呈蓝色，说明它的置信度较高 [【跳转到 03:38】](https://www.bilibili.com/video/BV15DTj6ZEzU/?t=218)。

![回折观察界面](assets/ProteinMPNN%20华盛顿大学%20Baker%20实验室开发的%20AI%20蛋白质序列设计工具/00203.webp)

## 三、结果判读：32 条序列质量如何

### 3.1 序列回收率 38%–57%：中等幅度改造

ProteinMPNN 一共生成了 32 条设计序列，而且这 32 条**完全不一样**，说明模型完成的是真正的重设计。设计序列和天然 1ENH 序列的**序列回收率**大概在 38% 到 57% 之间——这个结果比较理想，因为它说明模型不是简单复制天然序列，而是在保留骨架信息的前提下进行了中等幅度的序列改造 [【跳转到 03:57】](https://www.bilibili.com/video/BV15DTj6ZEzU/?t=237)。

![32 条设计序列的回收率表格](assets/ProteinMPNN%20华盛顿大学%20Baker%20实验室开发的%20AI%20蛋白质序列设计工具/00218.webp)

在表格里选五条代表性序列来看：设计 15 的序列回收率是 38.1%，pLDDT 达到 85.97，整体 RMSD 只有 0.79；设计 18 的 pLDDT 是 84.15、RMSD 是 1.01；其余候选也基本达到 **pLDDT 大于 80、RMSD 小于 2** 的标准 [【跳转到 04:27】](https://www.bilibili.com/video/BV15DTj6ZEzU/?t=267)。这两个指标的含义：

- **pLDDT**：AlphaFold 对局部结构预测的置信度，越高说明预测结构越可信；
- **RMSD**：预测结构和原始 1ENH 骨架之间的空间偏差，越低说明越接近原骨架。

![代表性序列的 pLDDT 与 RMSD](assets/ProteinMPNN%20华盛顿大学%20Baker%20实验室开发的%20AI%20蛋白质序列设计工具/00237.webp)

![pLDDT/RMSD 指标解读](assets/ProteinMPNN%20华盛顿大学%20Baker%20实验室开发的%20AI%20蛋白质序列设计工具/00267.webp)

### 3.2 PSSM 热图：哪里不能动、哪里随便换

PSSM 热图展示的是 ProteinMPNN 在**每个位置**选择不同氨基酸的概率 [【跳转到 05:01】](https://www.bilibili.com/video/BV15DTj6ZEzU/?t=301)：横坐标是序列位置，纵坐标是 20 种氨基酸，颜色越亮说明这个氨基酸在该位置被模型选择的概率越高。

![PSSM 概率热图](assets/ProteinMPNN%20华盛顿大学%20Baker%20实验室开发的%20AI%20蛋白质序列设计工具/00301.webp)

怎么读这张图：

- 有些位置出现**特别亮的点**——这些位置对维持结构比较关键，模型倾向于只选少数几种氨基酸；
- 有些位置颜色**比较分散**——这些区域更容易被替代，通常是表面区域或相对骨架约束较弱的位置。

### 3.3 AlphaFold 回折验证：序列变了，骨架没变

代表性序列的 AlphaFold 回测结果 [【跳转到 05:31】](https://www.bilibili.com/video/BV15DTj6ZEzU/?t=331)：

- 左侧结构按 pLDDT 着色，主体大部分是浅蓝色到青色，说明整体局部置信度较高；
- 右侧 PAE 图大部分区域也是蓝色，说明残基之间相对位置误差比较低；
- 下方蓝色点表示发生氨基酸替换的位置。

结合动画可以看到，设计后序列仍然保持一个和原始 1ENH 相近的小型螺旋骨架 [【跳转到 05:41】](https://www.bilibili.com/video/BV15DTj6ZEzU/?t=341)。

![AlphaFold 回测：pLDDT 着色与 PAE 图](assets/ProteinMPNN%20华盛顿大学%20Baker%20实验室开发的%20AI%20蛋白质序列设计工具/00341.webp)

所以这次实验的核心结论是：**ProteinMPNN 可以在给定 1ENH 骨架的情况下，生成与天然序列明显不同、但仍然能在 AlphaFold 中回折回目标结构的序列**。它证明的不是这个蛋白一定有某种功能，而是这些序列在结构层面有较好的折叠潜力 [【跳转到 06:11】](https://www.bilibili.com/video/BV15DTj6ZEzU/?t=371)。

## 四、优势与边界：它能做什么、不能做什么

最后总结这个工具的优势和边界：

- **优势**：速度快、操作门槛低，适合快速生成大量候选序列，可以和 AlphaFold、RFdiffusion 等工具形成完整的蛋白设计流程 [【跳转到 06:11】](https://www.bilibili.com/video/BV15DTj6ZEzU/?t=371)。
- **局限**：它主要优化的是**结构可折叠性**，并不能直接证明蛋白功能活性或真实实验稳定性 [【跳转到 06:36】](https://www.bilibili.com/video/BV15DTj6ZEzU/?t=396)。如果涉及酶活性、底物结合、金属离子或者辅因子，就需要更复杂的约束，甚至使用 **LigandMPNN**，并且最终仍需要实验验证。

![优势与边界总结](assets/ProteinMPNN%20华盛顿大学%20Baker%20实验室开发的%20AI%20蛋白质序列设计工具/00371.webp)

![局限：可折叠性 ≠ 功能，需实验验证](assets/ProteinMPNN%20华盛顿大学%20Baker%20实验室开发的%20AI%20蛋白质序列设计工具/00396.webp)

## 小结

- ProteinMPNN 是 Baker 实验室开发的**逆折叠**模型：输入主链骨架坐标，输出氨基酸序列，方向与 AlphaFold 相反。
- 模型把蛋白看成图：残基为节点、距离与方向为边，用消息传递图神经网络逐位置预测氨基酸。
- 在设计流水线中它处于中间环节：RFdiffusion 生成骨架 → ProteinMPNN 配序列 → AlphaFold/ESMFold 回折验证。
- 1ENH 实操中用 fixed_positions 固定核心位点、omit_AA 排除半胱氨酸、num_seq=32、温度 0.1（越低越保守）。
- 结果判读三件套：序列回收率（38%–57%，中等改造）、pLDDT/RMSD（>80 / <2 为达标）、PSSM 热图（亮=关键位点，散=可替换）。
- AlphaFold 回折验证确认：序列虽明显不同，仍能折回目标骨架——证明的是折叠潜力，不是功能。
- 局限：只优化可折叠性；功能、稳定性要靠湿实验，配体场景考虑 LigandMPNN。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| 逆折叠（inverse folding） | 给定主链骨架，反推能折叠成它的氨基酸序列 |
| 主链骨架坐标 | 蛋白三维结构中不含侧链的骨架原子坐标，ProteinMPNN 的输入 |
| 消息传递图神经网络 | 把残基周围几何环境沿「边」整合、逐位置打分的网络结构 |
| fixed_positions | 指定保持固定不变的残基位置，模型不得改动 |
| omit_AA | 排除氨基酸参数，如去掉 C（半胱氨酸）避免二硫键干扰 |
| sampling temperature | 采样随机性参数，越低越保守，与物理温度无关 |
| 序列回收率 | 设计序列与天然序列一致残基的占比 |
| pLDDT | AlphaFold 逐残基局部置信度，>80 视为高置信 |
| RMSD | 预测结构与参考骨架之间的空间偏差 |
| PSSM | 位置特异的氨基酸被选概率矩阵，热图中越亮概率越高 |
| PAE | 预测对齐误差，衡量残基之间相对位置的误差 |
| LigandMPNN | 考虑配体/辅因子的 MPNN 变体 |
