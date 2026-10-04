# 系列：Rosetta 蛋白-蛋白相互作用（PPI）设计工作坊

- **平台**：YouTube
- **来源**：RosettaCommons 频道播放列表《Designing Protein-Protein Interactions》（`PLFavr8uo6kSo4S7iHQ5eNh6lDoYqTw57`）
- **主讲**：Amrita Nallathambi（UNC Chapel Hill，Kuhlman Group）
- **背景**：2025 年 Rosetta Commons 主办的蛋白-蛋白相互作用设计工作坊，由 Rosetta Commons 与美国国家科学基金会（NSF）支持
- **视频数**：8
- **已整理**：前 2 讲（总览 + 方法导论）
- **主题**：以「结合体（binder）设计 + 笼状（cage）组装」为两条主线，串起现代蛋白质设计的经典流水线——**RFdiffusion 生成骨架 → ProteinMPNN 设计序列 → AlphaFold 预测验证 → Rosetta 打分分析**

## 视频索引

| # | 标题 | 时长 | 视频演说图文稿 | 博客 | 配图 | 原视频 |
| ---: | --- | ---: | --- | --- | ---: | --- |
| 01 | Protein-Protein Interactions Workshop Overview | 3:53 | [文稿](transcripts/第01讲_Protein-Protein%20Interactions%20Workshop%20Overview.md) | [博客](blog/第01讲_Protein-Protein%20Interactions%20Workshop%20Overview.md) | 7 | [YouTube](https://youtu.be/xMUvH57aOHk) |
| 02 | Intro to Deep Learning for Protein Design | 21:29 | [文稿](transcripts/第02讲_Intro%20to%20Deep%20Learning%20for%20Protein%20Design.md) | [博客](blog/第02讲_Intro%20to%20Deep%20Learning%20for%20Protein%20Design.md) | 13 | [YouTube](https://youtu.be/6YuUVgO1VDo) |
| 03 | Protein-Protein Interfaces | 7:49 | — | — | — | [YouTube](https://youtu.be/EhZqF0-VaJ8) |
| 04 | Binder Design Methods Overview | 8:08 | — | — | — | [YouTube](https://youtu.be/fRhhrfsszOU) |
| 05 | Bindcraft | 23:06 | — | — | — | [YouTube](https://youtu.be/aIDgF6BomlE) |
| 06 | Symmetric Protein Assemblies | 2:18 | — | — | — | [YouTube](https://youtu.be/Du5lX6XTP1E) |
| 07 | Designing Self-Assembling Protein Nanoparticles | 34:59 | — | — | — | [YouTube](https://youtu.be/lFgSRmGKQas) |
| 08 | RFDiffusion for Symmetric Applications | 23:09 | — | — | — | [YouTube](https://youtu.be/etV20qEpXrk) |

> 说明：本系列按播放列表顺序整理，仅收录**前 2 讲**的图文稿与博客，其余讲次待后续整理。

## 博客结构速览

**第 1 讲：PPI 工作坊总览——先补齐蛋白质与深度学习两块地基**

- 一、这是一场以动手为主的工作坊，而不是讲座
- 二、蛋白质复习之一：氨基酸是构成蛋白质的「字母表」
- 三、蛋白质复习之二：从肽键、键角到四级结构
- 四、深度学习复习之一：数据是模型的核心
- 五、深度学习复习之二：损失函数、层堆叠与泛化

**第 2 讲：面向蛋白质设计的深度学习导论——三大突破与三件核心工具**

- 一、为什么深度学习改变了蛋白质设计（数据积累 / 生成新序列 / 结构预测）
- 二、突破一：Transformer 与自注意力——让残基「互相交流」
- 三、AlphaFold2：把 Transformer 变成结构预测引擎（三阶段 + recycling、四项可调输入、pLDDT/PAE/pTM/ipTM）
- 四、突破二：图神经网络与 ProteinMPNN——在骨架上「配」序列（消息传递、节点特征、随机解码、概率分布）
- 五、突破三：扩散模型与 RFdiffusion——从噪声「雕刻」出骨架（去噪、RoseTTAFold、无条件生成、势函数）

## 核心知识点速览

- **第 1 讲**：工作坊以动手为主；蛋白质由氨基酸组成（非极性/极性/带正电/带负电四类），氨基酸以肽键相连并遵守特定键角与键长，结构分一级（序列）→二级（α 螺旋/β 折叠/loop）→三级→四级（复合物）；深度学习以数据为核心，常按训练/验证/测试（如 80/10/10）划分，用损失函数驱动训练，最终检验对未见数据的泛化。
- **第 2 讲**：深度学习改变蛋白质设计靠海量数据、生成全新序列的能力、以及 AlphaFold 的高精度结构预测；**Transformer** 的自注意力让序列所有位置互相交流、擅长长程相互作用；**AlphaFold2** 以 MSA+模板为输入、经 Evoformer（48 层）与结构模块（8 块）+ recycling 输出带置信度的 3D 结构，可用 recycles/MSA 深度/模板/种子数调参，用 pLDDT/PAE/pTM/ipTM 解读；**图神经网络**用节点-边-消息传递建模蛋白质，**ProteinMPNN** 输入主链 N/Cα/C/Cβ 特征、编码器+解码器预测每位点概率分布，随机解码便于固定/遮蔽设计；**扩散模型**在噪声与数据间插值，**RFdiffusion** 建立在 RoseTTAFold 上逐步去噪生成骨架，可改造输入做无条件生成/对称/基序设计，并用势函数引导。

## 相关资源

- Rosetta Commons 官网：https://rosettacommons.org/
- 工作坊配套 Notebook（Notion）：https://sweltering-waterfall-a22.notion.site/Designing-Protein-Protein-Interactions-Workshop-18532ee750358095a013d33effff1ca4
- 工作坊代码（GitHub，Amrita Nallathambi）：https://github.com/amritan1707/ppi_workshop
