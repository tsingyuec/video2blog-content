# 配对 MSA：AlphaFold-Multimer 预测蛋白复合体的输入关键——按物种配对，DockQ 从 0.01 拉到 0.9

> 视频来源：[基于人工智能的蛋白质复合体三维空间结构预测：AlphaFold-Multimer原理介绍 - 李盼博士 ｜ 钰沐菡 公益公开课](https://www.bilibili.com/video/BV1xB4y1i7x3/?t=0)（Bilibili · 钰沐菡-YuMuhan）
> 本文基于视频演说图文稿整理，配图截自视频。

## 本讲要解决的核心问题（SCQA）

**背景**：AlphaFold2（下称 AF2）已经把**单条**蛋白质链的结构预测得非常准——CASP14 上 Cα 骨架 RMSD 达到 0.96 Å。但细胞里的蛋白质大多以**复合体**（多条链绑在一起）的形式发挥功能，光知道每条链自己的结构并不够。

**冲突**：把两条序列直接拼起来丢给 AF2，搜出来的 MSA（多序列比对）里大量位置是 gap（空白）——链与链之间的共进化信号断了，复合体预测效果很差。

**疑问**：怎么构造一个能让"链与链之间"也产生共进化信号的 MSA？AlphaFold-Multimer（下称 AF-Multimer）又为此改了什么？

**回答（中心思想）**：用**配对 MSA**——把不同蛋白各自搜到的同源序列，按**物种**一一配对再拼接。单个例子上，只用非配对 MSA 或只用配对 MSA 的 DockQ 分别只有 0.01 和 0.02，两者合并后冲到 0.9；在 1480 个复合体的大规模验证里，"配对 + 非配对合并"让一半以上复合体的预测超过成功线（DockQ 0.23）。AF-Multimer 把这套思路做进了系统：换用带物种信息的 UniProt 数据库、按物种拼接 MSA、spatial cropping 强调界面、引入链编码与同源链匹配、用 ipTM 评分。

![本讲大纲：背景 → AF2 回顾 → 已有方法 → AF-Multimer 原理与使用](assets/基于人工智能的蛋白质复合体三维空间结构预测：AlphaFold-Multimer原理介绍%20-%20李盼博士%20｜%20钰沐菡%20公益公开课/00123.webp)

---

## 一、背景：为什么复合体预测难

### 1.1 蛋白质结构的四个层次

蛋白质结构分四个层次：**一级结构**是 20 种氨基酸的排列组合（一条链，相邻氨基酸以肽键相连）；**二级结构**是相邻氨基酸主链之间通过氢键等作用形成的有规则局部结构（α 螺旋、β 折叠、loop）；**三级结构**是较远的氨基酸侧链之间相互作用形成的三维结构；**四级结构**就是多条链之间的相互作用——复合体预测要解决的正是这一层 [【跳转到 02:03】](https://www.bilibili.com/video/BV1xB4y1i7x3/?t=123)。

氨基酸两两原子之间的距离都落在相对固定的范围（比如 Cα—C 约 1.5 Å），ω 角比较固定、约束 Cα—C—N—Cα 共平面，φ/ψ 二面角则集中在 Ramachandran 图的特定区域（α 螺旋区、β 折叠区）——**蛋白质三维结构是有规律可循的**，这正是模型能学的前提。

蛋白质链之间的相互作用依靠静电力、氢键、疏水作用等**非共价**相互作用。按链的来源分两类：**homomeric**（同源多聚体，每条链序列相同）和 **heteromeric**（异源多聚体，各链序列不同）。

### 1.2 共进化：MSA 为什么能预测结构

![共进化原理：三维空间中接近且有功能的两个氨基酸，在进化中协同突变](assets/基于人工智能的蛋白质复合体三维空间结构预测：AlphaFold-Multimer原理介绍%20-%20李盼博士%20｜%20钰沐菡%20公益公开课/00398.webp)

如果在三维空间中两个氨基酸比较接近、且这种相互作用对功能重要，那么当其中一个发生突变时，另一个也会在物种进化过程中**对应地突变**（否则功能被破坏）。于是：把一条序列的同源序列上下排成一列（MSA），找出"总是共同变化"的残基对，就能反推它们在空间中接近——**这就是 AF2 能预测结构的基本原理** [【跳转到 06:38】](https://www.bilibili.com/video/BV1xB4y1i7x3/?t=398)。注意这个推理的前提：MSA 里得有足够多"共同变化"的例子。

### 1.3 AlphaFold2 流程回顾

![AF2 流程：搜同源序列与模板 → 特征构造 → Evoformer 48 个 block 交换信息 → 结构模块 → 5 个模型取最优](assets/基于人工智能的蛋白质复合体三维空间结构预测：AlphaFold-Multimer原理介绍%20-%20李盼博士%20｜%20钰沐菡%20公益公开课/00498.webp)

AF2 分几个阶段 [【跳转到 08:18】](https://www.bilibili.com/video/BV1xB4y1i7x3/?t=498)：

1. **搜库（CPU）**：用 JackHMMER/HHblits 搜同源序列（UniRef90 约 58GB、UniClust30、DeepMind 自建的 BFD），到按 70% 相似性去重的 pdb70 里搜模板，取 CIF 文件解析模板坐标；
2. **特征构造**：把 MSA 和模板表示成神经网络输入——**MSA representation** 装着同源序列信息，**pair representation** 初始化主要靠模板（没有模板时基本是空的，信息大多先在 MSA representation 里）；
3. **Evoformer（48 个 block）**：让两种表征反复交换信息，把距离、坐标信息逐渐过渡到 pair representation；
4. **结构模块**：迭代 8 次 ×3 次 recycle 输出全原子坐标（GPU，JAX 实现），5 个模型出 5 个结构，OpenMM 做 relax 去掉原子冲突，最后排序取最优。

AF2 训练技巧很多（块删除、MSA 聚类、random mask、随机模板；cropping、bfloat16、梯度检查点、sub-batch 省显存；UniClust30 自蒸馏），核心都是**提高鲁棒性**——这为后面"MSA 少/有扰动也能预测"埋下伏笔。

## 二、把两条序列直接连起来，为什么预测不好复合体

### 2.1 先看四类"土办法"：都是在硬掰 AF2

在 AF-Multimer 出现之前，大家改造 AF2 预测蛋白质-蛋白质相互作用（PPI）的方法大概有四类 [【跳转到 30:40】](https://www.bilibili.com/video/BV1xB4y1i7x3/?t=1840)：

1. **添加 linker**：两条序列中间加一段随机 linker（或 poly-GS linker）连成一条，重跑 AF2；
2. **修改 residue index**：不连序列，但在特征提取时把第二条序列的 residue index 抬高，使两链 index 差 ≥32，让 AF2"以为"是两条不同的链；
3. **结合 docking 工具**：按方法 2 得到结构后，把结构塞回 AF2 的模板里反复迭代；
4. **结合 RosettaFold**：两条序列分别搜 MSA 再拼接，用更快的 RosettaFold 初筛、AF2 精筛（适合大规模预测，单用哪个都太慢）。

### 2.2 要害：拼接后的 MSA 里全是 gap，共进化信号断了

![poly-GS 连接后搜出的 MSA：黑色为残基匹配区，黄色为 gap 区——链间同时匹配的行才是有效信号](assets/基于人工智能的蛋白质复合体三维空间结构预测：AlphaFold-Multimer原理介绍%20-%20李盼博士%20｜%20钰沐菡%20公益公开课/01972.webp)

为什么直接拼接不行？把蛋白 1 和蛋白 2 用 poly-GS linker 连成一条再去搜同源序列，得到的 MSA 里：**黑色**部分是有残基匹配的区域，**黄色**部分是没有匹配、用短横线填充的 gap 区——很多行只有"其中一条链"有信息 [【跳转到 32:52】](https://www.bilibili.com/video/BV1xB4y1i7x3/?t=1972)。

而共进化推理需要的是**最下面那种行**：蛋白质 1 和蛋白质 2 上**都有**序列。只有这种行才能提供"链 A 的残基 i 与链 B 的残基 j 共同变化"的信号，从而指导界面残基对的预测。只有单边信息的行，对预测链间相互作用**没有贡献**。

## 三、配对 MSA：按物种把序列"结对"

### 3.1 朴素思路与真正的难点

![朴素思路：蛋白 1 与蛋白 2 各自搜 MSA，把"相同物种"的序列连接起来](assets/基于人工智能的蛋白质复合体三维空间结构预测：AlphaFold-Multimer原理介绍%20-%20李盼博士%20｜%20钰沐菡%20公益公开课/02047.webp)

解决思路说来简单：蛋白 1、蛋白 2 各自去搜 MSA，把**来自相同物种**的序列连接起来（图中紫色连紫色、绿色连绿色）[【跳转到 34:07】](https://www.bilibili.com/video/BV1xB4y1i7x3/?t=2047)。

但实际操作会发现：**一个物种往往能搜到很多条序列**——到底拿哪一条去和另一条链配？MSA 拼接远不是"同色相连"这么简单。

### 3.2 原核生物：用基因组邻近关系配对

针对**原核生物**，有工作利用了一个基本假设：原核基因组紧凑，相互作用的蛋白基因在基因组上往往相邻（操纵子结构），因此可以用**基因邻近关系**来给序列配对。

### 3.3 真核生物：按物种聚类 + 与 query 的相似性排序

![真核策略：两链同源序列按物种归类，再按与 query 的相似性排序一一配对，配不上的用 gap 填充](assets/基于人工智能的蛋白质复合体三维空间结构预测：AlphaFold-Multimer原理介绍%20-%20李盼博士%20｜%20钰沐菡%20公益公开课/02145.webp)

针对**真核生物**的做法（AF-Multimer 直接继承了它）：把蛋白 1、蛋白 2 搜到的所有同源序列，先**按物种归类**，再在每个物种内按与 query 序列的相似性排序，两链**一一配对**；配不上的位置用 gap 填充 [【跳转到 35:45】](https://www.bilibili.com/video/BV1xB4y1i7x3/?t=2145)。

这样得到的 MSA 里，每个"物种块"内部，两条链的行是对齐的——共进化信号在链间接通了。

## 四、配对 MSA 到底有没有用：从 0.01 到 0.9

### 4.1 先明确"及格线"：DockQ

评价复合体预测准确性用 **DockQ**，它由三部分取平均：**Fnat**（预测出的界面接触在真实接触中的比例）、**LRMS**（较长链叠合后较短链的 RMSD）、**iRMS**（界面上相距 10 Å 以内原子的 RMSD），后两者经 RMS scale 公式归一化到 0~1 [【跳转到 26:55】](https://www.bilibili.com/video/BV1xB4y1i7x3/?t=1615)。

![同一个靶标的三种预测：DockQ 从 0.061（差）到 0.478（中）到 0.86（好）](assets/基于人工智能的蛋白质复合体三维空间结构预测：AlphaFold-Multimer原理介绍%20-%20李盼博士%20｜%20钰沐菡%20公益公开课/01765.webp)

按 DockQ 文章的定义：**>0.23 算成功（successful），>0.49 中等（medium），>0.8 高精度（high）** [【跳转到 29:25】](https://www.bilibili.com/video/BV1xB4y1i7x3/?t=1765)。

### 4.2 三种 MSA 输入的对照实验

![三种 MSA 输入对比：只用 linker 直搜 0.01、只用配对 0.02、两者合并 0.9](assets/基于人工智能的蛋白质复合体三维空间结构预测：AlphaFold-Multimer原理介绍%20-%20李盼博士%20｜%20钰沐菡%20公益公开课/02281.webp)

那篇真核配对方法的论文做了三种条件的测试 [【跳转到 38:01】](https://www.bilibili.com/video/BV1xB4y1i7x3/?t=2281)：

| MSA 输入 | DockQ（单例） |
| --- | --- |
| ① 两条序列用 poly-GS linker 连接后直接搜 | 0.01 |
| ② 只用配对 MSA | 0.02 |
| ③ 两种 MSA **合并** | **0.9** |

单看哪种都不行，**合并起来效果惊人**——配对 MSA 提供链间信号，非配对 MSA 保留链内信号，缺一不可。

### 4.3 1480 个复合体的大规模验证

![大规模比较：引入配对 MSA 并与非配对 MSA 整合后，过半复合体超过成功线](assets/基于人工智能的蛋白质复合体三维空间结构预测：AlphaFold-Multimer原理介绍%20-%20李盼博士%20｜%20钰沐菡%20公益公开课/02331.webp)

同一个工作又用 **1480 个复合体**做了大规模比较：RosettaDock、刚性对接、TM-align（基于模板）、AF2+linker，以及若干引入配对 MSA 的方法 [【跳转到 38:51】](https://www.bilibili.com/video/BV1xB4y1i7x3/?t=2331)。结论一致：**引入配对 MSA、且与非配对 MSA 整合后，效果大幅提高**；按 DockQ 0.23 的及格线，**一半以上复合体可以被成功预测**。

同时期还有两条互补路线：AF2 排名第一的模型交给 ClusPro 再对接，取前十结果连同 AF2 自身 5 个模型共 15 个结构，按 PAE 排序选最优（17 个复合体的 benchmark 上"AF2 refined ClusPro"表现最好）[【跳转到 40:06】](https://www.bilibili.com/video/BV1xB4y1i7x3/?t=2406)；David Baker 组则用快 100 倍的 RosettaFold 对酵母全蛋白组两两初筛、AF2 精筛，效率远高于直接用 AF2 全跑 [【跳转到 41:26】](https://www.bilibili.com/video/BV1xB4y1i7x3/?t=2486)。

## 五、AlphaFold-Multimer：把"配对"做进系统

AF-Multimer 基于 AF2，大部分相同；下面只讲**不一样的地方**。

### 5.1 数据库：换成带物种信息的 UniProt

![AF-Multimer 的搜库：用包含物种信息的 UniProt，模板改用整个 PDB](assets/基于人工智能的蛋白质复合体三维空间结构预测：AlphaFold-Multimer原理介绍%20-%20李盼博士%20｜%20钰沐菡%20公益公开课/02511.webp)

输入可以是 1 条或多条序列，分别搜库。数据库与 AF2 基本一致，但多了一个关键角色：**UniProt——每条序列自带所属物种信息**，这正是按物种拼接 MSA 的前提 [【跳转到 41:51】](https://www.bilibili.com/video/BV1xB4y1i7x3/?t=2511)。模板搜索也从 pdb70 换成**整个 PDB**。

### 5.2 MSA 拼接：按物种匹配，配不上用 gap token

![AF-Multimer 的 MSA 拼接：输入 A、B、C 三条链，在每个物种内把各链序列排序后一一配对](assets/基于人工智能的蛋白质复合体三维空间结构预测：AlphaFold-Multimer原理介绍%20-%20李盼博士%20｜%20钰沐菡%20公益公开课/02836.webp)

具体流程：输入 A、B、C 三条链，各自搜 MSA；对每个物种，把 A、B、C 在该物种下的序列做匹配 [【跳转到 47:16】](https://www.bilibili.com/video/BV1xB4y1i7x3/?t=2836)——每链只有一条就直接拼；有多条就按与 query 的相似性排序后一一对应；配不上的位置用 **gap token** 顶替。

### 5.3 训练难点与配套改造

**① 复合体数据少**：PDB 里单体远多于复合体 → 把单体结构也加入训练集，另做一套单体自蒸馏集（大库里挑长度 >200 的序列，用 teacher model 预测、筛置信度高的加入训练）[【跳转到 42:41】](https://www.bilibili.com/video/BV1xB4y1i7x3/?t=2561)。测试集 Recent-PDB-Multimer 取 2018-04-30~2021-08-02 之间、2~8 条链、<1536 残基的复合体，去重后 **4433 个** [【跳转到 44:46】](https://www.bilibili.com/video/BV1xB4y1i7x3/?t=2686)。

**② 更强调界面（interface）**：AF2 只有 continuous cropping（随机裁固定长度省显存），AF-Multimer 50% 用 continuous、50% 用 **spatial cropping**——从界面上取点、把它空间邻近的残基裁出来做训练样本，逼模型把容量花在界面上。

**③ 让模型分得清"哪条链"**：引入三种链编码——链索引（每链一个编号）、去重链索引（序列相同的链共号）、相同序列链计数（相同序列的第 1、2 条）[【跳转到 49:46】](https://www.bilibili.com/video/BV1xB4y1i7x3/?t=2986)。

**④ 同源多聚体的 loss 匹配**：六聚体的 6 条链都一样，预测链和真实链谁对谁无从知道。AF-Multimer 用启发式对齐：先选**歧义最小**的链当 anchor（出现次数少的，如 3 条 A + 2 条 B 里选 B），用它把预测和真实结构对齐，再算每条链 Cα 中心坐标的两两距离矩阵，从最小的点开始启发式配对，取总距离最小的方案 [【跳转到 51:51】](https://www.bilibili.com/video/BV1xB4y1i7x3/?t=3111)。

### 5.4 评分：从 pTM 到 ipTM

![ipTM 强调链间关系；模型 confidence = 0.8×ipTM + 0.2×pTM](assets/基于人工智能的蛋白质复合体三维空间结构预测：AlphaFold-Multimer原理介绍%20-%20李盼博士%20｜%20钰沐菡%20公益公开课/03361.webp)

TM-score 可理解为归一化的 RMSD（对每个残基求和、按链长 L 归一化、取使分数最大的叠合）。AF2 用 head 预测 **pTM**（predicted TM-score），但它是单体指标、每个残基等权。AF-Multimer 引入 **ipTM**，更强调**两条链之间的关系**（界面）[【跳转到 56:01】](https://www.bilibili.com/video/BV1xB4y1i7x3/?t=3361)。最终模型 confidence = **0.8×ipTM + 0.2×pTM**，5 个模型都跑，用它排序取最优。

## 六、效果与边界

### 6.1 效果：heteromeric 提升最大

![4433 个复合体按 homo/hetero 分组：hetero（异源）上 AF-Multimer 远超 AF2](assets/基于人工智能的蛋白质复合体三维空间结构预测：AlphaFold-Multimer原理介绍%20-%20李盼博士%20｜%20钰沐菡%20公益公开课/03536.webp)

在 17 个复合体的 benchmark 上，AF-Multimer 的 DockQ 明显高于 AF2+linker、AF2 改 residue index、ClusPro 等一众方法；在 4433 个复合体上按 homo/hetero 分组看：**homomeric 有提高但不多，heteromeric 上 AF-Multimer 远远超过 AF2** [【跳转到 58:56】](https://www.bilibili.com/video/BV1xB4y1i7x3/?t=3536)。这也呼应了配对 MSA 的逻辑——异源多聚体最缺的就是链间信号。

### 6.2 AF2 的老毛病：越"爱交往"的蛋白越测不准

AF-Multimer 论文还指出了 AF2 的一个问题：把蛋白按"与其他蛋白的接触多少"（contact 阈值 2.5）分成两类，**接触多的蛋白用 AF2 预测，准确性明显更低** [【跳转到 60:16】](https://www.bilibili.com/video/BV1xB4y1i7x3/?t=3616)。三链复合体实验进一步说明：预测复合体要用 AF-Multimer（远超 AF2），但 **AF-Multimer 预测单体反而比 AF2 更差** [【跳转到 61:31】](https://www.bilibili.com/video/BV1xB4y1i7x3/?t=3691)——它为了强调界面（ipTM、spatial cropping），牺牲了一部分单体精度。答疑中主讲人也确认了这一点是"用界面换单体"的设计取舍。

![三链复合体实验：预测复合体时 AF-Multimer 远超 AF2，但预测单体时 AF-Multimer 反而更差](assets/基于人工智能的蛋白质复合体三维空间结构预测：AlphaFold-Multimer原理介绍%20-%20李盼博士%20｜%20钰沐菡%20公益公开课/03691.webp)

### 6.3 局限：没有共进化的地方，配对 MSA 也救不了

论文自述的不足 [【跳转到 62:21】](https://www.bilibili.com/video/BV1xB4y1i7x3/?t=3741)：

- 没实现**多聚体模板**搜索（仍用单体模板）；
- 没实现**多聚体自蒸馏**（仍是单体自蒸馏集）；
- 同源多聚体效果更好，作者认为是因为同源多聚体的 MSA 更容易获得；
- 最关键的：AF-Multimer 的原理是共进化/共变信息，**对抗原-抗体结合无能为力**——抗体与抗原之间不存在这种进化上的配对关系（答疑中做双特异性抗体的听众也验证了这一点）[【跳转到 70:39】](https://www.bilibili.com/video/BV1xB4y1i7x3/?t=4239)。

### 6.4 怎么用：流程、输出与可视化

使用流程 [【跳转到 63:11】](https://www.bilibili.com/video/BV1xB4y1i7x3/?t=3791)：输入一条或多条序列 → 搜同源序列与模板（输出 `features.pkl`）→ 5 个模型在 GPU 上推理 → OpenMM 做 refinement → 按 0.8×ipTM+0.2×pTM 排序选最优。

输出文件里注意两点：FASTA 的 header 可以任意长，但 PDB 链名只有 1 个字符（A、B、C、D），要用输出的 chain map（json）把链名映射回输入序列；`result_model_1-5.pkl` 字典里存着大量中间结果，可供分析与可视化 [【跳转到 64:26】](https://www.bilibili.com/video/BV1xB4y1i7x3/?t=3866)。可视化用 Chimera 即可：matchmaker 叠合 PDB 参考结构、按链着色、按 pLDDT 着色（黄=低置信）；看**亚基之间**相互作用是否可信则看 PAE（Predicted Aligned Error）——亚基间块的误差值小说明界面距离预测可信 [【跳转到 67:00】](https://www.bilibili.com/video/BV1xB4y1i7x3/?t=4020)。没有本地环境也可以用在线版 ColabFold：注册账号、输入两条链、点运行即可，但预测不了很长的链 [【跳转到 67:48】](https://www.bilibili.com/video/BV1xB4y1i7x3/?t=4068)。

答疑里还有两个实用结论：多聚体建模（如 20 个单链）可以用 AF-Multimer，但总长五六千残基会非常慢甚至爆显存，链短则没问题；ipTM/pTM 从 0.8 降到 0.7 只说明模型对加入 C 后的预测**不自信**了，不能据此判断 C 与 A 没有相互作用 [【跳转到 72:19】](https://www.bilibili.com/video/BV1xB4y1i7x3/?t=4339)。另外主讲人比较过 AF2 单独预测抗体结构：**AF-Multimer > AF2 > DeepAb**，最难的是 H3 环区（非常柔性）[【跳转到 73:34】](https://www.bilibili.com/video/BV1xB4y1i7x3/?t=4414)。

（片尾主讲人还介绍了水木未来的冷冻电镜业务与和清华大学张晓峰老师合作的 PrimeNet——输入三维电子云密度图、输出原子模型，可在 primenet.ai 在线试用，此处不展开。）

## 小结

- **复合体预测难在链间信号**：把两条序列直接拼起来搜 MSA，gap 会让共进化信号断掉，只有"两条链都有序列"的行才有用。
- **配对 MSA 是胜负手**：按物种把两链的同源序列配对拼接——原核用基因组邻近，真核用"按物种归类 + 与 query 相似性排序、一一配对、gap 补齐"。
- **配对 + 非配对要合并用**：单例上 0.01/0.02 → 合并 0.9；1480 复合体上一半以上超过 DockQ 0.23 成功线。
- **AF-Multimer 的系统改造**：UniProt 提供物种信息、模板换全 PDB、50% spatial cropping 强调界面、三种链编码、同源链 anchor 启发式匹配、ipTM 评分（confidence=0.8·ipTM+0.2·pTM）。
- **效果与边界**：heteromeric 提升最大；预测复合体用 Multimer、预测单体用 AF2；**没有共进化的抗原-抗体结合预测不了**——那是另一类方法（如 dyMEAN、RFantibody 等）的战场。
- **评价体系**：单体看 RMSD/TM-score/GDT_TS/lDDT，复合体看 DockQ（0.23/0.49/0.8 三档），输出置信度看 pTM/ipTM/PAE。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| MSA | 多序列比对，把同源序列上下排成一列，共进化信号的载体 |
| 配对 MSA（paired MSA） | 不同链的同源序列按**物种**配对后拼接的 MSA，提供链间共进化信号 |
| 非配对 MSA（unpaired MSA） | 每条链各自的 MSA，只含链内信号 |
| poly-GS linker | 甘氨酸-丝氨酸重复短肽，用来把两条序列连成一条喂给 AF2 |
| residue index 偏移 | 把第二条链的残基编号抬高 ≥32，让 AF2 识别为独立链 |
| 共进化（co-variation） | 空间接近且有功能的残基对在进化中协同突变的现象 |
| DockQ | 复合体预测评价指标，=Fnat/LRMS/iRMS 归一化平均；>0.23 成功、>0.49 中等、>0.8 高 |
| Fnat / LRMS / iRMS | 界面接触召回率 / 长链叠合后短链 RMSD / 界面 10 Å 内原子 RMSD |
| pTM / ipTM | 模型预测的全局结构置信度 / 界面（链间）置信度 |
| confidence | AF-Multimer 综合评分 = 0.8×ipTM + 0.2×pTM |
| spatial cropping | 以界面为中心裁剪训练样本，迫使模型重视 interface |
| 链编码 | 链索引、去重链索引、相同序列链计数三种位置编码，帮模型区分链 |
| anchor 启发式匹配 | 同源多聚体算 loss 前，选歧义最小的链对齐，再按链中心距离矩阵贪心配对 |
| PAE | Predicted Aligned Error，看亚基间相对位置预测是否可信 |
| UniProt | 带物种注释的蛋白序列库，是按物种配对 MSA 的信息来源 |
