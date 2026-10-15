# WeMol 实操 ProteinMPNN：结构前处理、序列设计与 score / global score 读法

> 视频来源：[WeMol教程_18| 蛋白序列设计ProteinMPNN](https://www.bilibili.com/video/BV1RemgYjEgk)（Bilibili · 唯信计算 · 6:25）
> 本文基于视频演说图文稿整理，配图截自视频。

## 本讲要解决的核心问题（SCQA）

**背景**：做蛋白序列设计，ProteinMPNN（David Baker 实验室开发的深度学习逆折叠工具）是标配。不想折腾命令行，可以上 WeMol 这类在线平台，点点鼠标就能跑。

**冲突**：跑完设计，输出表格里躺着五条序列和一串看不懂的列——`T`、`sample`、`score`、`global score`、`seq recovery`。不知道每列是什么，就没法判断哪条序列值得拿去实验。 [【跳转到 03:08】](https://www.bilibili.com/video/BV1RemgYjEgk/?t=188)

**疑问**：这些分数分别衡量什么？怎么据此挑出"可折叠性"最好的设计？

**回答（中心思想）**：`score` 是**逐残基的概率打分**、`global score` 是**整条序列所有残基的概率打分**、`seq recovery` 是**与原始序列的恢复率**。前两者源自模型的逐位置预测概率（对应 ProteinMPNN 的 NLL 类指标，越低代表模型越确信序列能折叠成目标骨架），后者越高说明与野生型越保守。配合 AlphaFold2 回折验证，才是完整的设计闭环。 [【跳转到 03:14】](https://www.bilibili.com/video/BV1RemgYjEgk/?t=194)

---

## 一、ProteinMPNN 是什么

ProteinMPNN 是诺贝尔化学奖得主 David Baker 团队开发的、基于深度学习的蛋白质序列设计方法：**给定蛋白骨架结构，恢复或设计氨基酸序列**。它可以配合 RFdiffusion 和 AlphaFold2 使用，也可以直接用于蛋白或抗体序列设计；设计完成后输出氨基酸序列，可直接进入可视化插件 View 操作。 [【跳转到 00:05】](https://www.bilibili.com/video/BV1RemgYjEgk/?t=5)

![开场介绍：ProteinMPNN 的定位与能力](assets/WeMol教程_18｜%20蛋白序列设计ProteinMPNN/00005.webp)

## 二、第一步：结构前处理（Structure Preparation）

导入待设计的 PDB 文件后先"体检"：示例结构是蛋白-蛋白复合物，存在**残基缺失**，还挂着**钠离子和水分子**。用 Structure Preparation 一键处理：补齐缺失残基、删掉离子和水分子。处理完保存到个人数据中心或本地备用。 [【跳转到 00:40】](https://www.bilibili.com/video/BV1RemgYjEgk/?t=40)

![Structure Preparation：补齐缺失残基、去除离子与水分子](assets/WeMol教程_18｜%20蛋白序列设计ProteinMPNN/00040.webp)

## 三、第二步：设定"哪里不动、哪里重设计"

进入 Design → ProteinMPNN，核心参数是**链**与**位点**：

- **Chain**：输入待设计的链，示例选 A 链；
- **Number of Sequences**：输出序列条数，一般用默认（本例输出 5 条）；
- **Position Type**：`Fix` 表示 Position 里的残基**保持不变**；`Design` 表示 Position 里的残基**参与设计**，其余未指定的残基保持不变。 [【跳转到 01:05】](https://www.bilibili.com/video/BV1RemgYjEgk/?t=65)

![参数面板：Chain、序列条数与 Fix/Design 模式](assets/WeMol教程_18｜%20蛋白序列设计ProteinMPNN/00090.webp)

那"该重设计哪一段"怎么定？示例用 Analyze → **Interface** 做结合位点分析，发现 A 链 C 端 **118~127** 位于结合界面——就选这段做设计。在结构里选中残基后点 Sync Selection，残基序号自动填入 Position 输入框。注意：这里的编号**从 1 开始**，不是原始 PDB 编号。 [【跳转到 02:01】](https://www.bilibili.com/video/BV1RemgYjEgk/?t=121)

![用 Interface 分析找到界面残基 118~127 并同步到 Position](assets/WeMol教程_18｜%20蛋白序列设计ProteinMPNN/00121.webp)

## 四、关键旋钮：温度、禁用残基与专用模型

- **Sampling Temp**：残基采样温度——调高更多样、调低更保守（对应概率分布的"尖锐度"，与 NLL 的关系见姊妹篇《Sequence Design with ProteinMPNN》）；
- **Omit AAs**：指定结果序列里**不许出现**的氨基酸；
- **Other Parameter**：`Homo-oligomer` 用于同源多聚体设计；
- **Soluble Model**：可溶性蛋白专用模型（避免膜蛋白偏好）；
- **Antibody Design**：切换到抗体优化模型 ABMPNN 做抗体序列设计；
- **Save Probability**：勾选后可保存每个位置的预测概率。 [【跳转到 02:28】](https://www.bilibili.com/video/BV1RemgYjEgk/?t=148)

![Sampling Temp 与 Omit AAs 等参数](assets/WeMol教程_18｜%20蛋白序列设计ProteinMPNN/00148.webp)

![可溶性模型与抗体设计（ABMPNN）等模型选项](assets/WeMol教程_18｜%20蛋白序列设计ProteinMPNN/00160.webp)

参数齐了就提交任务。

## 五、第三步：读懂结果——score / global score / seq recovery

计算完成后自动跳转序列编辑器，本例输出 5 条设计序列。**列名就是成绩单**： [【跳转到 03:08】](https://www.bilibili.com/video/BV1RemgYjEgk/?t=188)

| 列名 | 含义 | 怎么用 |
| --- | --- | --- |
| `T` | 该条序列生成时的采样温度 | 对照多样性来源 |
| `sample` | 序列编号（sample=1 即第 1 条） | 区分多条设计 |
| `score` | **设计残基的概率打分** | 数值越低，模型对"这条序列适配骨架"越有信心（对应 NLL 类指标） |
| `global score` | **整条序列所有残基的概率打分** | 序列整体适配合成的一个分数，跨条目横向比较 |
| `seq recovery` | **序列恢复率**（与原始序列的一致率） | 越高越保守；做定点改造时反而别追求太高 |

![结果编辑器：T / sample / score / global score / seq recovery 列](assets/WeMol教程_18｜%20蛋白序列设计ProteinMPNN/00194.webp)

挑选原则：**score 与 global score 偏低**（模型有信心）通常优先入围；`seq recovery` 则按设计意图取舍——想保持野生型性质就选恢复率高的，想大胆改造就容忍更低恢复率。但分数只是初筛，**下一节的回折验证才是终审**。

## 六、第四步：与野生型比对，定位突变位点

把原始 PDB 结构导入序列编辑器，B 链移出比对，野生型 A 链调到首行；点击星号按钮把保守残基标记为星号，序列编号可在 POS 编号 / 原始 PDB 编号等模式间切换。 [【跳转到 03:43】](https://www.bilibili.com/video/BV1RemgYjEgk/?t=223)

对照后发现：设计区 118~127 里，**119、120、123、125、127** 五个位点发生了突变。选中这些位点，用 Structure → Site View 在三维结构里放大查看突变位置的具体环境。 [【跳转到 04:08】](https://www.bilibili.com/video/BV1RemgYjEgk/?t=248)

![序列比对：星号标保守残基，圈出五个突变位点](assets/WeMol教程_18｜%20蛋白序列设计ProteinMPNN/00223.webp)

![Site View 在结构中查看突变位点的环境](assets/WeMol教程_18｜%20蛋白序列设计ProteinMPNN/00248.webp)

## 七、第五步：AF2 回折验证与结构叠合

把设计的序列（连同 B 链）粘进 AlphaFold2 的 Multimer 模式重新预测结构：本例预测打分均在 **0.87** 左右，说明复合物结构可靠；`ranked_0.pdb` 就是打分最好的模型。 [【跳转到 05:00】](https://www.bilibili.com/video/BV1RemgYjEgk/?t=300)

![AF2 预测结果：打分 0.87 左右，ranked_0.pdb 为最优模型](assets/WeMol教程_18｜%20蛋白序列设计ProteinMPNN/00300.webp)

结果的 **PAE 热图**衡量"两个残基相对位置"的预测置信度：深蓝方块=预测良好，浅色=较差。本例整体深蓝，复合物可信。 [【跳转到 05:16】](https://www.bilibili.com/video/BV1RemgYjEgk/?t=316)

![PAE 热图：深蓝代表残基对相对位置预测良好](assets/WeMol教程_18｜%20蛋白序列设计ProteinMPNN/00321.webp)

最后在 View 里把野生型与突变型结构叠合（Superposition），**RMSD 仅 0.86**，说明突变没有破坏整体折叠；逐位点查看 119/121/125，突变后的互作比野生型还多一些——设计结果合理。 [【跳转到 05:53】](https://www.bilibili.com/video/BV1RemgYjEgk/?t=353)

![野生型与设计序列的叠合：RMSD 0.86](assets/WeMol教程_18｜%20蛋白序列设计ProteinMPNN/00353.webp)

## 小结

- 流程五步：**结构前处理 → 选定设计位点 → 设参数跑设计 → 读分数挑序列 → AF2 回折验证**。
- 结果表三兄弟：`score`（逐残基概率打分）、`global score`（全序列概率打分）、`seq recovery`（序列恢复率）——前两者**越低模型越有信心**，后者按设计意图取舍。
- 分数只是初筛：温度/噪声等旋钮会推高分数却可能改善真实折叠性，**终审永远交给回折验证**（打分、PAE、RMSD）。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| Structure Preparation | 补齐缺失残基、去除离子/水分子，给设计一个干净的骨架 |
| Fix / Design | 指定哪些残基保持不变、哪些参与重新设计 |
| Sampling Temp | 采样温度：调高更多样、调低更保守 |
| Omit AAs | 禁止出现在设计结果中的氨基酸 |
| score / global score | 逐残基 / 全序列的概率打分，源自模型预测概率（NLL 类指标），越低越有信心 |
| seq recovery | 设计序列与原始序列的一致率 |
| PAE | 预测对齐误差热图，衡量残基对相对位置的预测置信度 |
| RMSD | 叠合后原子偏差均方根，衡量突变是否破坏整体折叠 |
