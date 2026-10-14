# 预测突变的影响：从蛋白稳定性到结合 ΔΔG

> 视频来源：[Predicting the Effect of Mutation on Protein Stability and Binding](https://www.youtube.com/watch?v=ZSSRQprN3lI)（YouTube，约 45 分钟，MolSoft ICM 网络研讨会）。本文基于该视频的演说图文稿整理而成；演示软件为商业软件 ICM Pro，但其中的概念（ΔΔG 定义、界面扫描、按能量排序突变）是通用的，同样适用于 FoldX、Rosetta 等工具。关键结论均可在对应时间戳核对。

## 本讲要解决的核心问题（SCQA）

**背景**：蛋白质工程与抗体亲和力成熟的核心操作就是"改残基"：改错了蛋白可能失稳、丧失功能；改对了可能结合更强、表达更好。描述这件事的通用语言是自由能：ΔG 与"突变前后之差" ΔΔG。

**冲突**：实验测一个突变点的 ΔΔG（热漂移、ITC、_SPR_ 等）既慢又贵，不可能把饱和突变全测一遍；而且 ΔΔG 的符号方向（正、负到底谁好）在不同语境下还容易记混。

**疑问**：ΔΔG 怎么定义、怎么算？除了单体稳定性，突变对**蛋白-蛋白结合**、**肽结合**、**小分子结合**的影响又怎么预测、怎么批量排序？

**回答（中心思想）**：**ΔΔG = ΔG(突变体) − ΔG(野生型)**。稳定性语境：ΔΔG > 0 表示突变使蛋白更不稳，< 0 表示更稳或基本不变；结合语境：ΔΔG < 0 表示突变增强了结合，> 0 表示削弱。用能量模型配合侧链柔性采样（如偏置概率蒙特卡洛 BPMC）可以对单个位点乃至整个界面/口袋做**饱和突变扫描，按 ΔΔG 排序**，把实验资源集中到最有希望的少数突变上。

![研讨会主题：预测突变对稳定性与结合的影响](assets/Predicting%20the%20Effect%20of%20Mutation%20on%20Protein%20Stability%20and%20Binding/00000.webp)

## 一、为什么要预测突变：三个真实案例

### 1.1 稳定性与功能直接挂钩

野生型蛋白的功能与其**折叠自由能**（即稳定性）直接相关；错义突变、天然变异都可能改变稳定性。实验上人们也常在体外做点突变，来衡量某个氨基酸对蛋白稳定性的贡献——若能事先**预测**突变的影响，就能指导实验设计、少走弯路。[【跳转到 03:36】](https://www.youtube.com/watch?v=ZSSRQprN3lI&t=216)

### 1.2 案例：线粒体呼吸链复合物

讲师展示了一篇用 ICM 完成的工作：在人类线粒体呼吸链复合物中找出**功能相关的突变位点**，并把它做成可交互的文档——表格里列出各突变及可能的功能解释，点选残基即可在 3D 结构中查看。[【跳转到 04:37】](https://www.youtube.com/watch?v=ZSSRQprN3lI&t=277)

### 1.3 案例：GPCR 的热稳定化

更有代表性的是 USC Stevens 实验室的工作：G 蛋白偶联受体（GPCR）做结构解析前往往需要热稳定化突变。他们把**序列分析 + 结构信息 + 机器学习**结合起来预测热稳定化突变（方法名 CompoMug），在血清素受体上实验验证，成功解析了**活性与非活性两种状态**的晶体结构。[【跳转到 07:31】](https://www.youtube.com/watch?v=ZSSRQprN3lI&t=451)

## 二、先会"做"突变，再谈"算"影响（示例：1TP5）

### 2.1 从 PDB 到可编辑模型

演示从 PDB 读入结构 **1TP5**——PSD-95 蛋白的第三个 PDZ 结构域，结合着一段 6 肽配体 KKETWV。注意第一步不是直接改：PDB 晶体结构要先"转换"成可建模的对象——**补加氢原子、优化 Asn/Gln 侧链翻转**等。[【跳转到 08:25】](https://www.youtube.com/watch?v=ZSSRQprN3lI&t=505)

![1TP5：PDZ 结构域（紫）与结合肽段（黄）](assets/Predicting%20the%20Effect%20of%20Mutation%20on%20Protein%20Stability%20and%20Binding/00505.webp)

![转换后的 ICM 对象：已加氢、可用于建模](assets/Predicting%20the%20Effect%20of%20Mutation%20on%20Protein%20Stability%20and%20Binding/00560.webp)

### 2.2 看清界面再动手

用"分子表面 + 接触（contacts）"显示，能直接看到肽段嵌在一个**部分埋藏的口袋**里，主要靠疏水相互作用贴合。[【跳转到 10:45】](https://www.youtube.com/watch?v=ZSSRQprN3lI&t=645)

![蛋白表面的接触图：肽段结合口袋](assets/Predicting%20the%20Effect%20of%20Mutation%20on%20Protein%20Stability%20and%20Binding/00650.webp)

### 2.3 建一个突变并优化侧链

右键残基即可"突变氨基酸"，随后对侧链做优化——新侧链会"四处试探"寻找能塞进口袋的构象。讲师故意把一个苯丙氨酸突变成放不进去的大残基：侧链转了半天也找不到落脚点，还与周围产生**原子冲突（clash）**——这直观说明"空间适配"是突变可否的第一道门槛。此外还能连糖基、换成 20 种之外的非天然氨基酸。[【跳转到 12:03】](https://www.youtube.com/watch?v=ZSSRQprN3lI&t=723)

![侧链优化：新残基"跳舞"寻找可容纳的构象](assets/Predicting%20the%20Effect%20of%20Mutation%20on%20Protein%20Stability%20and%20Binding/00723.webp)

**划重点**：这一步只是**建模（modeling）**——造出突变的几何模型；它回答不了"这个突变是好是坏"。要回答后者，需要**预测（prediction）**。

## 三、预测稳定性 ΔΔG：1HB6 的 F26A

### 3.1 方法定义

稳定性预测方法计算的是：**单点突变引起的蛋白稳定性变化**

$$\Delta\Delta G = \Delta G_{\text{突变体}} - \Delta G_{\text{野生型}}$$

比较的是**折叠态与去折叠态**：去折叠态的自由能近似为各残基"特异性能量"之和；突变后，仅对突变残基及其邻近侧链做**偏置概率蒙特卡洛（BPMC）**柔性采样，蛋白其余部分保持固定。[【跳转到 14:36】](https://www.youtube.com/watch?v=ZSSRQprN3lI&t=876)

**符号约定**（Q&A 环节明确）：ΔΔG **> 0 → 突变体更不稳定**；ΔΔG **< 0 → 稳定性提高或维持**。[【跳转到 26:43】](https://www.youtube.com/watch?v=ZSSRQprN3lI&t=1603)

### 3.2 实操：选残基、跑预测

示例结构 **1HB6**——牛酰基-CoA 结合蛋白（ACBP），文献中积累了大量突变实验数据，适合对照。演示选取其中的 **Phe26**，做 **F26A**（苯丙氨酸→丙氨酸）：[【跳转到 16:27】](https://www.youtube.com/watch?v=ZSSRQprN3lI&t=987)

![1HB6（牛 ACBP）：待突变的 Phe26 以棒状显示](assets/Predicting%20the%20Effect%20of%20Mutation%20on%20Protein%20Stability%20and%20Binding/01000.webp)

![选中 Phe26 并以棒状显示](assets/Predicting%20the%20Effect%20of%20Mutation%20on%20Protein%20Stability%20and%20Binding/01082.webp)

菜单路径为 **MolMechanics → Mutation → Protein Stability**。对话框里可以一次勾选多个候选氨基酸（甚至全部 20 种天然氨基酸），也可以从**非天然氨基酸列表**里选，或用内置的类 ChemDraw 绘图器现画一个新侧链；还有骨架弛豫、保留其他链等选项。[【跳转到 19:25】](https://www.youtube.com/watch?v=ZSSRQprN3lI&t=1165)

![Protein Stability 预测对话框](assets/Predicting%20the%20Effect%20of%20Mutation%20on%20Protein%20Stability%20and%20Binding/01165.webp)

### 3.3 读结果：一张表 + 一次验证

预测完成后得到结果表：蛋白名、链、残基号、野生型、突变型，以及 **ΔΔG 预测值**和**溶解度变化**。[【跳转到 23:19】](https://www.youtube.com/watch?v=ZSSRQprN3lI&t=1399)

![稳定性预测结果表：ΔΔG 与溶解度](assets/Predicting%20the%20Effect%20of%20Mutation%20on%20Protein%20Stability%20and%20Binding/01399.webp)

对本例，文献的实验 ΔΔG 与预测值相当接近（约 1.x kcal/mol 的量级）。双击表中的行，工作区会加载出突变体对象，与原始晶体结构并列，可逐一核对突变位点的几何。[【跳转到 24:12】](https://www.youtube.com/watch?v=ZSSRQprN3lI&t=1452)

## 四、预测结合 ΔΔG：1CBW 的界面扫描

### 4.1 与稳定性预测的差别：要有"相互作用区"

**蛋白-蛋白相互作用的突变效应**流程略有不同：能量按"突变体复合物 vs 野生型复合物"计算，骨架固定，只优化突变残基邻域的侧链——**包括界面另一侧链的残基**（若突变靠近对方分子）。因此对话框里多了"相互作用区（interacting parts）"的设置。[【跳转到 25:23】](https://www.youtube.com/watch?v=ZSSRQprN3lI&t=1523)

示例结构 **1CBW**：Kunitz 族抑制剂 BPTI 与胰凝乳蛋白酶的复合物（2.6 Å）。对应论文正是用**噬菌体展示**随机突变了抑制剂的结合决定残基（11、13、15、17、19 位），积累了大量可比数据。[【跳转到 28:02】](https://www.youtube.com/watch?v=ZSSRQprN3lI&t=1682)

![1CBW：BPTI（橙）-胰凝乳蛋白酶复合物](assets/Predicting%20the%20Effect%20of%20Mutation%20on%20Protein%20Stability%20and%20Binding/01682.webp)

### 4.2 先找出"谁在接触"：接触面积表

动手前用 **Tools → Analysis → Contact Areas** 生成一张按**接触面积排序**的残基表：哪个残基与对面分子接触最多一目了然；结构视图中侧链的粗细也按接触面积缩放。示例聚焦链 D 的 **Lys15**——它正是 BPTI 的 P1 特异性位点，同时与 B、C 两条链都有接触。[【跳转到 30:12】](https://www.youtube.com/watch?v=ZSSRQprN3lI&t=1812)

![接触面积表：按残基接触大小排序](assets/Predicting%20the%20Effect%20of%20Mutation%20on%20Protein%20Stability%20and%20Binding/01908.webp)

![Lys15（P1 位点）与多条链形成接触](assets/Predicting%20the%20Effect%20of%20Mutation%20on%20Protein%20Stability%20and%20Binding/01812.webp)

### 4.3 跑批量突变，按 ΔΔG 排序

菜单 **MolMechanics → Mutation → Protein-Protein Binding**：突变所在的链设为 interacting part 1，与其接触的链设为其余 interacting parts。[【跳转到 33:46】](https://www.youtube.com/watch?v=ZSSRQprN3lI&t=2026) 演示中对 Lys15 尝试了全部 20 种替换，结果表给出每种的 **ΔΔG(结合)**、ΔG(稳定性) 与溶解度三列——可以点击列头排序、右键彩虹着色，还能把"结合 ΔΔG"与"稳定性"两列做成**柱状图联筛**：两个都低（结合更强且不失稳）的突变才值得做实验。[【跳转到 36:05】](https://www.youtube.com/watch?v=ZSSRQprN3lI&t=2165)

![结果表：ΔΔG 结合 / 稳定性 / 溶解度三列](assets/Predicting%20the%20Effect%20of%20Mutation%20on%20Protein%20Stability%20and%20Binding/02216.webp)

![按 ΔΔG 排序并用图表联筛](assets/Predicting%20the%20Effect%20of%20Mutation%20on%20Protein%20Stability%20and%20Binding/02109.webp)

本例的"冠军"其实是野生型 Lys→Lys（ΔΔG=0），随后是 **Lys→Arg**——保留正电荷、只微调几何，正是 P1 位点的常见优化方向。双击任意行即可加载对应突变体，另存为 PDB 供后续流程使用。[【跳转到 39:25】](https://www.youtube.com/watch?v=ZSSRQprN3lI&t=2365)

## 五、肽与小分子：同一思路的推广

肽结合与小分子结合的预测流程与蛋白-蛋白一致，差别只在对话框：

- **肽**：可扫描肽序列上的**每一个残基**（逐个试或全部 20 种），按突变对**肽结合 ΔΔG** 的影响排序；示例回到 1TP5（PDZ 域 + KKETWV 肽）。[【跳转到 41:01】](https://www.youtube.com/watch?v=ZSSRQprN3lI&t=2461)
- **小分子**：用 **scan pocket surface** 选项扫描**配体结合口袋周围的所有残基**，批量预测哪个点的突变最能改变（通常希望是增强或调整）结合。[【跳转到 42:04】](https://www.youtube.com/watch?v=ZSSRQprN3lI&t=2524)

![扫描肽序列每个位置的突变影响](assets/Predicting%20the%20Effect%20of%20Mutation%20on%20Protein%20Stability%20and%20Binding/02461.webp)

## 六、把三讲串起来：ΔG → Kd → ΔΔG

本条目（1.5.1）的三段内容至此闭环：

1. **ΔG**（结合自由能）：决定结合是否自发，由焓（广义静电）与熵（疏水效应等）构成——见《[结合热力学：读懂 Kd、Ka 与 ΔG](<Biochemical binding thermodynamics - Kd, Ka, and their interpretation.md>)》；
2. **Kd**：ΔG 的宏观体现（ΔG 与 Kd 通过平衡常数相关），单位是浓度，直觉是"一半结合所需的浓度"——见《[Kd，解离常数：它到底是什么？](<Kd, the Dissociation Constant： What is it？.md>)》；
3. **ΔΔG**：突变前后 ΔG 之差。稳定性上正负号回答"蛋白是否更稳"；结合上它直接映射为 Kd 的变化——**ΔΔG(结合) < 0 → 亲和力更强（Kd 更小）**。这就是亲和力成熟（dyMEAN 的 `optimize` 任务、BioPhi/ProteinMPNN 后的验证环节）在能量语言下的含义。

两点务实提醒（来自本讲）：

- 预测基于半经验能量模型，**绝对值只作量级参考（±1~2 kcal/mol 内），排序比绝对值可靠**——所以实践里都是"批量预测 → 排序 → 少量实验验证"；
- 界面上的"好突变"常受**稳定性约束**：只筛结合 ΔΔG 可能选到不稳定的突变体，两列联筛才是正确姿势。

## 小结

- **ΔΔG = ΔG(突变体) − ΔG(野生型)**；稳定性语境 >0 去稳定、<0 更稳；结合语境 <0 增强结合（对应 Kd 变小）。
- 预测流程：PDB → 补氢/优化 → 突变建模 → 能量采样（只柔性化突变残基及邻域侧链，BPMC）→ ΔΔG 报告。
- 结合预测需要**相互作用区**设置；先用接触面积表找界面热点残基（如 BPTI 的 P1 Lys15）。
- 批量扫描 + 按 ΔΔG 排序 + 结合/稳定性**联筛**，是理性设计与亲和力成熟的标准姿势。
- 肽与小分子只是把扫描范围换成"肽上每个残基"或"口袋表面"。
- 预测值作量级与排序参考，最终以实验（热漂移、ITC、SPR 等）验证。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| ΔΔG | 突变体与野生型的自由能之差；稳定性上 >0 不稳，结合上 <0 更强 |
| BPMC | 偏置概率蒙特卡洛：对侧链构象做偏置随机搜索的最小化方法 |
| P1 位点 | 抑制剂/底物与蛋白酶特异性口袋直接相触的关键残基（如 BPTI 的 Lys15） |
| 接触面积（contact area） | 残基与对面分子接触的面积大小，用于找界面热点 |
| interacting parts | 结合 ΔΔG 预测中参与相互作用的分子（链）分组 |
| 饱和突变扫描 | 对某位点尝试全部 20 种氨基酸（或更多）并按 ΔΔG 排序 |
| 溶解度列 | 预测突变对蛋白溶解度的影响，辅助排除易聚集的突变 |
