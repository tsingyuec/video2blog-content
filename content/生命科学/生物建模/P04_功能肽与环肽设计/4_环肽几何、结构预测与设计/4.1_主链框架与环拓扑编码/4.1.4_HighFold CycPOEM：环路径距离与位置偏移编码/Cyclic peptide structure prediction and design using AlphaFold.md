# Cyclic peptide structure prediction and design using AlphaFold（用 AlphaFold 做环肽结构预测与设计）

> 视频：[ML for protein engineering seminar series · Cyclic peptide structure prediction and design using AlphaFold](https://www.youtube.com/watch?v=SDxy5E8fvXY)（2023-06-07，1:07:20，英文字幕）
> 主讲：Stephen（华盛顿大学蛋白质设计研究所，Bhardwaj 实验室）＋ Simon（哈佛大学 Sergey Ovchinnikov 实验室）
> 说明：本篇是知识库条目 **5.1.5 HighFold——环肽 / 环肽-蛋白复合物（CycPOEM）** 的领域背景笔记。HighFold 正是把 AlphaFold 扩展到环肽与环肽-蛋白复合物结构预测的工作，本视频讲的是同一路线的代表性实践。

## 本讲要解决的核心问题（SCQA）

**背景**：环肽（cyclic peptide）被认为是站在抗体药物与小分子药物之间的"桥梁"药物形态：既有接近抗体的结合特异性，又可能像小分子一样口服、穿膜。明星分子环孢素 A（cyclosporine）证明了这条路能走通。

**冲突**：设计环肽长期以来是一门"手艺活"——用 Rosetta 的运动学算法采样骨架、人工挑选，验证一个设计还要海量算力。2020 年后 AlphaFold 让蛋白质预测与设计脱胎换骨，但它只见过线性蛋白：不认识 D 型氨基酸，更没见过首尾相连的环肽。做环肽的人用不上这件新武器。

**疑问**：能不能让预训练的 AlphaFold 理解环肽？能不能把环肽设计的整条流水线——序列设计、骨架生成、结合剂设计——都搬到它上面？

**回答（中心思想）**：可以，而且改动小得出人意料。给 AlphaFold 的位置编码加一个**循环偏移**（cyclic offset），预训练模型就能直接预测环肽结构——80 个天然环肽中一半通过双标准检验；再用 [ColabDesign/AFDesign](https://github.com/sokrypton/ColabDesign) 把损失函数定义在 AlphaFold 输出上做梯度优化，**序列重设计**、**骨架从头"幻觉"**、**靶向 MDM2 的结合剂设计**全部跑通：8 个设计拿到晶体结构（最高 0.3 Å），结合剂筛选命中 IC50 ≈ 350 nM。

---

## 一、为什么是环肽：站在抗体与小分子之间

把抗体和青霉素放在一起看尺寸，两种药物形态的优缺点一目了然（[【跳转到 01:30】](https://www.youtube.com/watch?v=SDxy5E8fvXY&t=90)）：

- **抗体（生物制剂）**：分子量巨大，能对靶点形成巨大的结合界面，因此同时拿到极高的特异性和亲和力；但它是蛋白质——口服会被消化酶分解，体积也大到穿不过细胞膜，只能注射给药，且够不到细胞内靶点。
- **小分子**：分子量小（通常 < 500 Da），能口服、能穿膜、能打细胞内靶点；但想靶向大的蛋白质表面或干扰蛋白-蛋白相互作用时，它的结合表面积不够，而且能进膜的分子到处都进，脱靶效应并不少见。

环肽恰好可能落在中间地带。最好的例子是**环孢素 A**：FDA 批准的免疫抑制剂，一个环肽却做到了小分子才擅长的事——跨膜、口服，靶向细胞内蛋白**亲环蛋白 A（cyclophilin A）**；更妙的是它与靶点结合后形成新的界面，再去结合第二个靶点**钙调磷酸酶（calcineurin）**。这种"双靶操作"你很难指望一个只有三个残基大小的小分子做到（[【跳转到 01:55】](https://www.youtube.com/watch?v=SDxy5E8fvXY&t=115)）。

![环孢素 A 与亲环蛋白 A 的共晶结构：一个环肽同时具备穿膜、口服与胞内靶点结合能力](assets/Cyclic%20peptide%20structure%20prediction%20and%20design%20using%20AlphaFold/00192.webp)

正是因为这个例子太有说服力，Bhardwaj 实验室一直想**设计**出具有同样性质的环肽。

## 二、深度学习之前：Rosetta 时代的环肽设计工艺

### 2.1 用"机器人臂"采样环肽骨架（GenKIC）

深度学习爆发之前，设计环肽骨架靠的是**广义运动学闭合算法（generalized kinematic closure，GenKIC）**——2017 年由 Priyadarshini 与 Vikram Mulligan 等详细发表。思路借自机器人学（[【跳转到 04:27】](https://www.youtube.com/watch?v=SDxy5E8fvXY&t=267)）：

1. 在肽链上选 **3 个"枢轴"残基**（pivot），把它们当作机器人臂的关节；
2. 其余残基按 Ramachandran 图上合理的 φ/ψ 扭角随机化；
3. 把"首尾相连成环"当作机械臂从位置 A 运动到位置 B 的运动学问题，用算法解出枢轴处的扭角，使肽链恰好闭合。

这样就能在 Rosetta 里海量采样结构合理的环肽骨架，再交给 Rosetta 的快速设计协议分配序列。

![GenKIC：三个灰色枢轴残基 + 黄色待随机化残基，环化被当作机械臂运动学问题求解](assets/Cyclic%20peptide%20structure%20prediction%20and%20design%20using%20AlphaFold/00292.webp)

### 2.2 D/L 混用：异手性带来刚性与稳定性

环肽是化学合成的，不受 20 种天然氨基酸限制——可以用非天然残基，甚至用它们的镜像 **D 型氨基酸**。团队的用法是：负 φ 区用传统 L 型氨基酸，而正 φ 区不再只依赖甘氨酸，改用对应氨基酸的 D 型镜像。这样做出的环肽内部有大量氢键网络和 β-转角，再到处塞脯氨酸，目标是把整条肽**锁死在单一构象**（conformationally locked）上（[【跳转到 05:55】](https://www.youtube.com/watch?v=SDxy5E8fvXY&t=355)）。

锁死构象有两个好处：一是便于解析结构、且预组织成结合姿态后更容易设计结合剂；二是 D/L 混用的异手性肽能抵抗蛋白酶水解——体内的蛋白酶只认 L 型氨基酸，而环化又让外切蛋白酶无处下嘴。

设计的环肽交给 Varani 实验室做 NMR，结构系综与设计模型达到了**原子级吻合**（[【跳转到 07:16】](https://www.youtube.com/watch?v=SDxy5E8fvXY&t=436)）。

![设计模型与 NMR 结构系综高度重合：Rosetta 时代环肽设计的验证方式](assets/Cyclic%20peptide%20structure%20prediction%20and%20design%20using%20AlphaFold/00436.webp)

### 2.3 改造膜透性：把"该锁的"都锁起来

环化对穿膜有帮助，但不够。要让环肽穿膜，必须把暴露在溶剂中、会和水的酰胺氮（amide N-H）"去溶剂化"——这很难。团队的配方是（[【跳转到 08:23】](https://www.youtube.com/watch?v=SDxy5E8fvXY&t=503)）：

- 把骨架 NH **锁进分子内氢键网络**；
- 能用脯氨酸的地方都用脯氨酸（脯氨酸没有酰胺氢）；
- 实在锁不住的酰胺氮做 **N-甲基化**修饰——环孢素 A 也是这么干的，而且化学合成中不难做。

全部做到后，设计的环肽可以**被动穿膜**。验证用了两个实验：**PAMPA**（平行人工膜通透性实验，测被动穿膜速率）和 **Caco-2 转孔实验**（结肠癌细胞单层，更接近真实肠道吸收）。尺寸上，设计出了 6～12 个残基的环肽——普遍超过 Lipinski 五规则的 500 Da，和环孢素 A 体量相当，照样能穿过细胞单层（[【跳转到 09:13】](https://www.youtube.com/watch?v=SDxy5E8fvXY&t=553)）。

![PAMPA 实验数据：部分设计环肽能快速被动穿过人工膜](assets/Cyclic%20peptide%20structure%20prediction%20and%20design%20using%20AlphaFold/00528.webp)

### 2.4 以小分子为起点"长"出环肽

2021 年 Teresa Zenzola 与 Vikram Mulligan 发表了两个"从小分子出发造环肽"的范例（[【跳转到 10:08】](https://www.youtube.com/watch?v=SDxy5E8fvXY&t=608)）：

- HDAC 抑制剂天然产物 **Largazole** 看上去像一条"超长半胱氨酸"——把它参数化成非Canonical残基，环化后这条超长侧链恰好能伸进 HDAC 与锌离子相互作用，得到 HDAC2/6 的**低纳摩尔级 IC50** 抑制剂；
- 另一个小分子像"半胱氨酸＋脯氨酸"二肽，围绕它环化，用更大的分子体积带来额外接触与特异性（挡住相似蛋白）。

![Largazole 与"超长半胱氨酸"非天然氨基酸：从小分子起点构建功能环肽](assets/Cyclic%20peptide%20structure%20prediction%20and%20design%20using%20AlphaFold/00633.webp)

### 2.5 工艺的天花板

把"穿膜环肽"和"靶向设计"两套方法拼起来，似乎万事大吉。但Stephen 强调：这是个**手艺活（artisanal process）**——不是"输入靶标结构、点击运行、输出答案"的即插即用流程，需要深厚的 Rosetta 经验，普适性有限（[【跳转到 11:48】](https://www.youtube.com/watch?v=SDxy5E8fvXY&t=708)）。

验证设计还要烧大量算力：对每个设计做"反向预测"——固定序列、采样其它构象，画出能量- RMSD 能量地形。好的设计有又深又窄的漏斗和巨大的能量缺口；地形平坦或存在替代极小值的设计只能扔掉。

## 三、AlphaFold 来了——但环肽用不了

AlphaFold 把结构预测精度提升了一个量级，还附带一个礼物：连蛋白复合物也预测得很好（视频里展示的正是 AlphaFold-Multimer 权重的预印本，[【跳转到 13:51】](https://www.youtube.com/watch?v=SDxy5E8fvXY&t=831)）。这对"设计完再验证复合物"是质的飞跃——物理模型很难做到的事，它信手拈来。

问题在于：**做环肽的人用不了它**。AlphaFold 不认识 D 型氨基酸，训练数据里全是线性蛋白，没见过首尾相连的环。

![AlphaFold（含 Multimer 权重）带来蛋白质结构预测与设计的飞跃](assets/Cyclic%20peptide%20structure%20prediction%20and%20design%20using%20AlphaFold/00831.webp)

团队决定先做减法：D 型氨基酸暂时放弃（反正可以合成后镜像），先解决"环"的问题。于是他们请来 Simon 和 Sergey Ovchinnikov 帮忙——接下来是本视频最核心的部分。

## 四、让 AlphaFold 认识环肽：一个"循环偏移"就够了

### 4.1 关键观察：AlphaFold 的位置感是"喂"进去的

Simon 从架构讲起。AlphaFold 是基于注意力（attention）的架构——残基集合作为输入时，架构本身把它们当作**无序集合**（unordered set）里的独立对象，靠注意力去两两查看。那么模型是从哪里知道"这是第 1 个残基、那是第 2 个残基"的呢？

答案是：**位置关系不是架构内建的，而是作为输入特征喂进去的**——它藏在 pair representation 里。对每对残基，pair representation 里编码了它们的**相对位置**（会有上限截断），配上相应的 embedding。模型对"氨基酸顺序"的全部认知都来自这些特征（[【跳转到 16:30】](https://www.youtube.com/watch?v=SDxy5E8fvXY&t=990)）。

![AlphaFold 的 pair representation：残基对的相对位置特征是模型"顺序感"的唯一来源](assets/Cyclic%20peptide%20structure%20prediction%20and%20design%20using%20AlphaFold/01015.webp)

### 4.2 cyclic offset：把"首尾相邻"告诉模型

既然位置只是输入特征，那就喂一个环状的相对位置——**把首尾残基的相对位置设为 -1**，其余照旧（[【跳转到 17:19】](https://www.youtube.com/watch?v=SDxy5E8fvXY&t=1039)）。对比两种输入：线性 8 肽的位置编码 vs 环肽的位置编码，差别只在这一个格点。

![线性肽与环肽的相对位置编码：环肽只是让首尾残基的相对位置变为 -1](assets/Cyclic%20peptide%20structure%20prediction%20and%20design%20using%20AlphaFold/01039.webp)

**实验一（异想天开但成立）**：喂一条全丙氨酸（alanine）的长序列——丙氨酸偏好形成螺旋，模型通常输出一条直线螺旋；改成带循环偏移的输入，AlphaFold 居然预测出一个**环形**结构（[【跳转到 18:04】](https://www.youtube.com/watch?v=SDxy5E8fvXY&t=1084)）。也就是说，预训练模型对训练中从未见过的"相对位置模式"具备泛化能力。

![全丙氨酸序列 + 循环偏移：AlphaFold 输出环形螺旋，证明泛化能力](assets/Cyclic%20peptide%20structure%20prediction%20and%20design%20using%20AlphaFold/01084.webp)

**实验二（真刀真枪）**：拿天然环肽做对比测试，有/无循环偏移的预测 RMSD 差距巨大。没有偏移时，模型把它当线性肽预测，N 端和 C 端在结构里相距甚远，误差惨不忍睹；加上偏移后，首尾被"告知"相连，预测大幅改善（[【跳转到 19:10】](https://www.youtube.com/watch?v=SDxy5E8fvXY&t=1150)）。

![有/无循环偏移的预测对比：无偏移时 N/C 端相距过远导致精度崩溃](assets/Cyclic%20peptide%20structure%20prediction%20and%20design%20using%20AlphaFold/01150.webp)

一个值得玩味的细节：AlphaFold 训练数据的长度下限大约是 16 个残基，而这些环肽又短又环——**双重 out-of-distribution** 的输入它照样泛化了。

## 五、80 个天然环肽的体检：一半达标，置信度可信

有了循环偏移，第一件事是"体检"：从 PDB 挑出 **80 个环状且全 L 氨基酸**的结构（D 型仍是当前的局限），逐一预测（[【跳转到 20:33】](https://www.youtube.com/watch?v=SDxy5E8fvXY&t=1233)）。

评估用双标准：横轴 pLDDT（AlphaFold 自身的置信度，> 0.7 为 DeepMind 定义的高置信），纵轴对天然结构的 RMSD（< 1.5 Å 算预测良好）。结果：**恰好 50 个落入双达标区**——一半以上的天然环肽被正确预测。更有用的是置信度的"人品"：**模型自信时通常是对的，不自信时通常是错的**——设计时这就成了可靠的取舍信号（[【跳转到 21:23】](https://www.youtube.com/watch?v=SDxy5E8fvXY&t=1283)）。

![80 个天然环肽的 pLDDT vs RMSD 散点图：50 个同时满足高置信与小 RMSD](assets/Cyclic%20peptide%20structure%20prediction%20and%20design%20using%20AlphaFold/01283.webp)

体检样本里不乏硬骨头：30 多个残基、带全套二硫键网络的 **cyclotide**（环肽毒素）——二硫键完全没做任何约束，AlphaFold 自己"找"出来的；也有传统 β 折叠拓扑；甚至还有 2015 年首次引入 GenKIC 算法的那个 de novo 蛋白。

## 六、AFDesign：把环肽序列设计变成梯度下降

### 6.1 逆向问题与可微损失

下一步是设计。问题定义叫 **backbone design**（骨架设计）：给定骨架，求能折叠成它的序列。AlphaFold 干的是反方向（序列 → 结构），但没关系——把它包进损失函数里就行（[【跳转到 24:58】](https://www.youtube.com/watch?v=SDxy5E8fvXY&t=1498)）：

1. 随机序列 + 循环偏移喂给 AlphaFold，得到输出的 **distogram**（残基对距离直方图）；
2. 定义可微损失：预测 distogram 与目标骨架真实 distogram 的相似度；
3. 沿损失**反向传播穿过整个预训练模型**——不是更新权重，而是更新**输入序列**。

![AlphaFold 输出的 distogram：每对残基的距离概率直方图是设计损失的基础](assets/Cyclic%20peptide%20structure%20prediction%20and%20design%20using%20AlphaFold/01498.webp)

### 6.2 离散序列怎么求导："软化—锐化"

序列是离散对象，没法直接求导。AFDesign 的秘诀是先"软化"：不让模型接收 one-hot 向量，而是接收一个带概率的连续分布向量，梯度流向每个残基每个位置上的 logits；优化过程中不断**锐化**这个分布，直到只剩一个峰，最后回到离散序列（[【跳转到 27:28】](https://www.youtube.com/watch?v=SDxy5E8fvXY&t=1648)）。加上论文里的一堆技巧，最终得到的序列能以很高的 pLDDT 置信度被 AlphaFold 预测成目标结构。

### 6.3 为什么用"折叠模型"做设计反而更稳

用结构→序列的模型直接设计，可能找到一个能折叠成目标的序列，但它**同时也能折叠成别的结构**。而 AlphaFold 这类折叠模型被定义所迫——给它一条序列，它必须判断这条序列在能量地形上的归宿——所以它优化的是整张地形图，找到的序列不容易"一心二用"，从而减少脱靶折叠（[【跳转到 28:36】](https://www.youtube.com/watch?v=SDxy5E8fvXY&t=1716)）。

## 七、第一次实验验证：重设计 + 外消旋结晶

Stephen 拿一个"中等难度"骨架做测试：GenKIC 生成的较螺旋的环肽（含 D/L 氨基酸），结构预测勉强过线——故意不给最难的题（[【跳转到 30:01】](https://www.youtube.com/watch?v=SDxy5E8fvXY&t=1801)）。

AFDesign 用全 L 氨基酸重设计序列后，再画能量地形：**能量缺口深了一大截**——AlphaFold 全局优化序列、避开替代极小值的说法得到了呼应。

![AFDesign 重设计后的能量地形：能量缺口显著加深，替代极小值被避开](assets/Cyclic%20peptide%20structure%20prediction%20and%20design%20using%20AlphaFold/01876.webp)

湿实验验证用的是**外消旋结晶**（racemic crystallography）：同时合成全 L 设计与它的镜像（全 D），等摩尔混合后结晶——这能借用小分子结晶学里常见的额外空间群，大幅提高小肽结晶成功率。结果拿到**高分辨晶体，Cα RMSD 仅 0.3 Å**，连不少侧链 rotamer 都严丝合缝（[【跳转到 32:31】](https://www.youtube.com/watch?v=SDxy5E8fvXY&t=1951)）。

![外消旋结晶拿到 0.3 Å 高分辨结构：设计模型（蓝）与晶体（灰）几乎重合](assets/Cyclic%20peptide%20structure%20prediction%20and%20design%20using%20AlphaFold/01951.webp)

## 八、AFDesign 骨架"幻觉"：连 Rosetta 都不用了

### 8.1 换个损失函数，就能"无中生有"

既然序列设计走通了，能不能连骨架也从 AlphaFold 里"长"出来？可以——只需要换损失函数（[【跳转到 33:20】](https://www.youtube.com/watch?v=SDxy5E8fvXY&t=2000)）。不再要求 distogram 匹配某个给定骨架，而是要求模型**对预测本身足够自信**：

- **pLDDT 置信损失**：整体置信度要高；
- **pAE 分数**：成对置信度也要高（模型对每个残基对的距离判断要"有把握"）；
- **接触数损失**：鼓励骨架拥有天然蛋白量级的接触数——否则优化器最喜欢输出"无聊但稳定"的纯螺旋。

优化协议与序列设计完全相同，损失一换，跑出来的就是从未有过目标、从零"幻觉"出来的新骨架。

### 8.2 五万条骨架的大规模幻觉

团队对 **7～13 个残基**的每个尺寸各幻觉了 **50,000 条**环肽，并用基于扭角的聚类去重，保证骨架彼此独立。分布图显示绝大多数过了 DeepMind 的 0.7 置信线；但团队故意苛刻：只取 **pLDDT > 0.9** 的尖子生——7 残基只剩 **182 条**。再对这批骨架做能量地形复检，**114 条**漏斗良好，从中挑选代表性设计送去结晶（[【跳转到 37:18】](https://www.youtube.com/watch?v=SDxy5E8fvXY&t=2238)）。

### 8.3 八个晶体结构：从小螺旋到 β 折叠

首批 7～10 残基设计的结果（[【跳转到 38:02】](https://www.youtube.com/watch?v=SDxy5E8fvXY&t=2282)）：

- **7 / 9 / 10-mer**：与设计模型肉眼可见地吻合；
- **8-mer** 最弱：一个甘氨酸的 φ 角翻转，导致些许偏差；
- 更大的 **11-mer**：高分辨 0.3 Å，螺旋清清楚楚；
- **12 / 13-mer**：被挑中的设计是 **β 折叠**拓扑——证明这套方法不只会造螺旋。

这些骨架大多**没有规则二级结构**，却能拿到这种精度的晶体——说明模型并未依赖"传统二级结构元素"的老本。

![11 残基螺旋环肽的 0.3 Å 晶体结构：设计（蓝）与实验（灰）高度一致](assets/Cyclic%20peptide%20structure%20prediction%20and%20design%20using%20AlphaFold/02341.webp)

统计下来：**8 个设计拿到实验验证**；幻觉流程还留下约 **20,000 个未验证的高置信骨架**，且数量仍在增长——还没到"再也长不出新结构"的饱和点（[【跳转到 39:30】](https://www.youtube.com/watch?v=SDxy5E8fvXY&t=2370)）。

## 九、走向治疗性环肽：MDM2 结合剂全流程

有了两万多个骨架，下一步直奔主题：**治疗性环肽**。Stephen 选了一个容易验证的切入点：许多蛋白-蛋白界面由螺旋介导，而幻觉骨架中约 50% 含螺旋——那就把骨架"嫁接"到已知的螺旋识别界面上（[【跳转到 40:26】](https://www.youtube.com/watch?v=SDxy5E8fvXY&t=2426)）。

靶点选 **MDM2**——经典癌症靶点，p53 的"负调控者"。p53 来源的 15 残基螺旋肽以高亲和力结合 MDM2。流程（[【跳转到 41:16】](https://www.youtube.com/watch?v=SDxy5E8fvXY&t=2476)）：

1. **取材**：从 p53 肽上取 5 个残基作为识别 motif；
2. **嫁接（threading）**：把约 25,000 个骨架逐一"穿"到这个 motif 上，得到 18,000 个嫁接了螺旋的候选；
3. **配序列**：用 **ProteinMPNN**（Justas Dauparas 开发的消息传递神经网络，给骨架分配序列的利器）为每个候选设计序列；
4. **预测复合物**：把靶标结构当模板、只给环肽序列，让 AlphaFold 回答两个问题——它还折叠成环吗？它与靶点形成结合复合物吗？大部分候选在此被淘汰；
5. **挑 14 个合成**：综合 **AlphaFold Multimer** 与 Rosetta 指标——接口残基的 **pAE**（界面置信度）、**接触分子表面积（contact molecular surface）**、**界面结合能 dDG**；
6. **湿实验筛选**：用 **AlphaLISA** 均相实验（检测 MDM2–p53 肽复合物的抑制）做单浓度初筛——14 个中有 **3 个命中**；再做完整 IC50，最佳一条 **≈ 350 nM**（[【跳转到 43:18】](https://www.youtube.com/watch?v=SDxy5E8fvXY&t=2598)）。

![AlphaLISA 单浓度筛选：末尾三个候选显著抑制 MDM2–p53 肽复合物](assets/Cyclic%20peptide%20structure%20prediction%20and%20design%20using%20AlphaFold/02598.webp)

![三个命中物的完整 IC50 曲线：最佳约 350 nM](assets/Cyclic%20peptide%20structure%20prediction%20and%20design%20using%20AlphaFold/02623.webp)

Stephen 特意泼了盆冷水：MDM2 是"好打的靶"——文献里已有皮摩尔级结合剂，这正说明流程通了；如果连它都打不中，才真要重新思考路线。

## 十、问答精华

问答环节信息密度同样很高（[【跳转到 44:31】](https://www.youtube.com/watch?v=SDxy5E8fvXY&t=2671)）：

- **更长的序列？** 现在已采到 16～18 残基（结合界面更大），瓶颈是**合成难度**随长度上升。另一个技术风险：设计长蛋白时，优化器可能找到"对抗性序列"骗过 AlphaFold；短而强约束的环肽里这个问题少得多。
- **D 型与非天然氨基酸？** 全 D 肽直接镜像即可；真正的难题是"用 D 肽打 L 靶点"——模型没见过 D/L 混合界面。根本瓶颈在**数据**：PDB 里 D/L 混合物太少。出路可能是正在发展的全原子模型。
- **"热环"（hot loops）**：有听众提到 2014 年 Parisa（Zanzida Hanover）组与 Josh Kritzer 的论文——抗体中驱动结合的"热环"约 90% 可以支架化成有序大环。这给了社区信心，但讲者也提醒：实验上让这些环真正折叠并不容易。
- **构象系综？** AlphaFold 默认输出 5 个模型，可当作"微调参考"；但当前设计流程用单一静态结构，未主动处理柔性——而柔性对环肽其实非常重要。
- **低 pLDDT 骨架还有救吗？** 很可能：用 ProteinMPNN 重新设计序列，也许能"回捞"一大批当时被扔掉的骨架。
- **怎么设计既能穿膜的环肽？** AFDesign 里还没有现成功能；可行组合拳是：只用疏水氨基酸做幻觉 → 拿到 Rosetta 里做 N-甲基化 / D 型锁定。好消息是这套梯度框架足够模块化——未来可以把"透性预测模型"直接挂进损失做端到端优化。
- **AF 与 Rosetta 是不是重复劳动？** 讲者承认这是公平的批评：验证集里只挑了"全部指标都过"的设计。但反过来说，**多个不同源的模型都认可**本身就是最强的入选信号——ProteinMPNN 出的序列过一遍 AlphaFold 复检，已是标配操作。

## 小结

- 环肽想同时获得小分子的口服穿膜与抗体的高特异性；深度学习之前的设计工艺（GenKIC + Rosetta）有效但属"手艺活"。
- AlphaFold 的顺序感来自输入的 pair representation——把首尾相对位置改成 -1（**循环偏移**），预训练模型就理解了环肽，80 个天然环肽一半预测达标。
- **AFDesign** 把设计定义在 AlphaFold 输出的可微损失上（distogram / pLDDT / pAE / 接触数），梯度穿过冻结的模型直达输入序列，"软化—锐化"解决离散求导。
- 序列重设计经外消旋结晶验证达 **0.3 Å**；置信度损失的骨架"幻觉"一次产出约 2 万个新环肽骨架，8 个晶体验证从螺旋到 β 折叠。
- MDM2 结合剂全流程（嫁接 → ProteinMPNN → AlphaFold 复合物预测 → AlphaLISA）命中 **350 nM**——为 HighFold 这类"环肽/环肽-蛋白复合物预测"方法铺平了道路。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| 环肽 / cyclic peptide | 首尾（或侧链间）共价成环的肽，兼具刚性与可修饰性 |
| 环孢素 A (cyclosporine) | FDA 批准的免疫抑制剂环肽，能口服、穿膜、靶向胞内蛋白 |
| GenKIC | generalized kinematic closure，借机器人学解"肽链如何首尾闭合"的 Rosetta 算法 |
| pLDDT | AlphaFold 逐残基置信度（0-100 / 0-1），> 0.7 视为高置信 |
| RMSD | 预测结构与参考结构间原子距离均方根偏差，越小越准 |
| 循环偏移 (cyclic offset) | 在 pair representation 中把首尾残基相对位置设为 -1，令模型"看见"环 |
| distogram | AlphaFold 输出的残基对距离概率直方图 |
| AFDesign / ColabDesign | 在预训练 AlphaFold 上做可微设计（损失→梯度→输入序列）的开源框架 |
| 幻觉 (hallucination) | 不给目标结构、仅以"自信度"为损失，让模型生成全新骨架 |
| ProteinMPNN | 消息传递神经网络，按骨架设计氨基酸序列 |
| 外消旋结晶 (racemic crystallography) | 等摩尔混合全 L 与全 D 版本一起结晶，提高小肽结晶成功率 |
| AlphaLISA | 均相免疫实验，此处用于检测 MDM2–p53 肽复合物是否被抑制 |
| pAE / 接口 pAE | 预测对齐误差；界面残基 pAE 低意味着模型对结合界面有把握 |
| dDG / 接触分子表面积 | Rosetta 的界面结合能与界面接触面积度量，用于候选排序 |
