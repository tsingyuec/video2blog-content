# Alphafold 2 Explained：WHY DeepMind had revolutionary results at CASP14

> 视频来源：[Alphafold 2 Explained: WHY DeepMind had revolutionary results at CASP14](https://www.youtube.com/watch?v=bvZ1NsB1pes)（YouTube，约 17 分钟，2020 年）。UP 主此前做过蛋白质结构预测研究、现转做机器学习，从"内行"视角拆解 AlphaFold 2 成功的原因。本文基于该视频的图文稿整理，所有内容均可回溯到视频对应时间点。

## 本篇要解决的核心问题（SCQA）

**背景**：把一条氨基酸序列变成它的三维结构，是生物学五十多年来的大问题。2020 年的 CASP14 竞赛上，DeepMind 的 AlphaFold 2 拿出了令人咋舌的成绩。

**冲突**：2018 年的 AlphaFold 1 已经表现不错，但 AF2 的提升幅度大得"像不可能发生"——连业内人都觉得争议纷纷 [【跳转到 03:52】](https://www.youtube.com/watch?v=bvZ1NsB1pes&t=232)。

**疑问**：AlphaFold 2 凭什么比前代好这么多？

**回答（中心思想）**：两个关键要素的合体——**多序列比对（MSA）提供的进化信息** + **注意力机制（attention）把整份 MSA 一次性读完**。AF2 不是在猜结构，而是从"上亿年的进化实验数据"里读出了残基之间的约束。（而 MSA 从哪来？正是本系列 5.7.1 关注的 **MSA 搜索**这一前置步骤。）

![视频开场：AlphaFold 2 论文讲解](assets/Alphafold%202%20Explained%EF%BC%9AWHY%20DeepMind%20had%20revolutionary%20results%20at%20CASP14/00000.webp)

## 一、问题设定：从文本到坐标

"结构预测"说穿了就是 [【跳转到 00:25】](https://www.youtube.com/watch?v=bvZ1NsB1pes&t=25)：

- **输入**：一条氨基酸序列——一串由 20 种标准氨基酸字母组成的"文本"；
- **输出**：这条链在细胞里折叠完成后每个原子的三维坐标。

输出通常存成 **PDB 文件**。视频带观众翻了一个真实的 PDB 文件：前面是序列（SEQRES），往下翻到 ATOM 记录，就是逐原子罗列的"这是氮原子、这是它的 XYZ 坐标" [【跳转到 01:33】](https://www.youtube.com/watch?v=bvZ1NsB1pes&t=93)。所以结构预测的本质是：**怎么从一串文本，算出这一堆坐标？**

![问题设定：序列（文本）是输入，三维坐标是输出](assets/Alphafold%202%20Explained%EF%BC%9AWHY%20DeepMind%20had%20revolutionary%20results%20at%20CASP14/00050.webp)

![PDB 文件实读：序列与逐原子坐标](assets/Alphafold%202%20Explained%EF%BC%9AWHY%20DeepMind%20had%20revolutionary%20results%20at%20CASP14/00093.webp)

## 二、怎么给预测打分：CASP 竞赛

评价方法很朴素：拿实验解析的结构（比如 X 射线晶体结构）当标准答案，算预测结构与它的距离。常用度量有 **RMSD**（均方根偏差）和 **GDT**，AlphaFold 还用了对局部折叠差异更敏感的 lDDT 类指标 [【跳转到 02:50】](https://www.youtube.com/watch?v=bvZ1NsB1pes&t=170)。

成绩单来自 **CASP**（Critical Assessment of Structural Prediction，结构预测关键评估）——一个两年一届的"结构预测奥林匹克" [【跳转到 03:27】](https://www.youtube.com/watch?v=bvZ1NsB1pes&t=207)。AlphaFold 1 在 2018 年已经领先，而 AlphaFold 2 在 2020 年的 CASP14 上把精度曲线拉到了与实验结构难分伯仲的位置。

![CASP 历年成绩曲线：AF2 的跃升一目了然](assets/Alphafold%202%20Explained%EF%BC%9AWHY%20DeepMind%20had%20revolutionary%20results%20at%20CASP14/00207.webp)

## 三、秘密武器之一：进化信息（MSA）

### 3.1 CASP 参赛者的共识：光看一条序列不够

从 CASP12 前后起，参赛者们就形成了一个共识：**预测结构时不能只看目标序列本身，还要把它与序列数据库比对，找出所有同源序列** [【跳转到 04:47】](https://www.youtube.com/watch?v=bvZ1NsB1pes&t=287)。这就是**多序列比对（MSA）**：把目标序列和一大堆同源序列按列对齐排成矩阵。

![CASP12 起的共识：进化同源序列是关键](assets/Alphafold%202%20Explained%EF%BC%9AWHY%20DeepMind%20had%20revolutionary%20results%20at%20CASP14/00312.webp)

为什么有用？视频举了个直观例子：拿一段查询序列去数据库里搜，会找到很多"长得像"的序列 [【跳转到 09:43】](https://www.youtube.com/watch?v=bvZ1NsB1pes&t=583)。比如搜回来的同源序列里，你的序列某个位置是 I（异亮氨酸），别人的是 V（缬氨酸）[【跳转到 10:20】](https://www.youtube.com/watch?v=bvZ1NsB1pes&t=620)——

![MSA 示意：查询序列与搜回的同源序列逐列对齐](assets/Alphafold%202%20Explained%EF%BC%9AWHY%20DeepMind%20had%20revolutionary%20results%20at%20CASP14/00583.webp)

![搜到一条相似序列：同一位置的 I 变成了 V](assets/Alphafold%202%20Explained%EF%BC%9AWHY%20DeepMind%20had%20revolutionary%20results%20at%20CASP14/00620.webp)

这两个氨基酸都是**非极性**的，互换对结构影响不大——比对打分时也不会狠罚。这就是 MSA 里隐含的生物学直觉：**亿万年进化替你做过无数次"突变实验"，哪些位置能变、哪些位置不能变，都写在同源序列里了** [【跳转到 10:41】](https://www.youtube.com/watch?v=bvZ1NsB1pes&t=641)。

### 3.2 AF1 用了 MSA，但用得"不完整"

AlphaFold 1 其实也用进化序列，而且成绩已经很好。但它的架构是**三个独立网络**分别模拟不同的域，最后还要"退火"（anneal）到一起，没有做到真正的端到端整合 [【跳转到 05:37】](https://www.youtube.com/watch?v=bvZ1NsB1pes&t=337)。AF2 在 CASP14 上的飞跃，正是把这条路走通了。

![AlphaFold 2 论文摘要页：输入序列、MSA 与模板](assets/Alphafold%202%20Explained%EF%BC%9AWHY%20DeepMind%20had%20revolutionary%20results%20at%20CASP14/00671.webp)

## 四、秘密武器之二：注意力机制

### 4.1 一段简史：从 ImageNet 到文本

为什么偏偏是 attention？视频给了一段机器学习简史 [【跳转到 06:21】](https://www.youtube.com/watch?v=bvZ1NsB1pes&t=381)：当年 **AlexNet** 在 ImageNet 图像分类的 top-5 错误率上碾压式领先，从此"不用深度学习就没法参赛"；同样的剧情后来在机器翻译、情感分析、问答等**文本任务**上重演。而结构预测——"从文本（序列）到结构"——本质上也是个文本问题。

### 4.2 attention 与 LSTM/CNN 的本质区别

- **LSTM/RNN**：逐词读入，读到第 200 个词时才"见过"它，信息一路递推、容易丢失；
- **CNN**：卷积核一次只看局部窗口，抓不到长程依赖；
- **attention**：**把整个输入一次性摊在眼前**，直接算出"哪些位置之间有关系" [【跳转到 08:26】](https://www.youtube.com/watch?v=bvZ1NsB1pes&t=506)。

这一点对折叠问题致命地重要：蛋白质里，第 10 个残基和第 900 个残基可能在空间上紧贴——这种**长程相互作用**恰恰是逐读/局部方法的天敌、注意力机制的强项。

## 五、合体：attention 读完整个 MSA

AF2 的做法是把两个武器焊在一起：**用注意力机制处理整份 MSA**——不是用互信息（mutual information）、伪似然（pseudo-likelihood）这类"摘要统计量"，而是把整个比对（所有同源序列）直接喂进网络 [【跳转到 14:03】](https://www.youtube.com/watch?v=bvZ1NsB1pes&t=843)。论文原话："现有深度学习架构过度偏好序列局部的相互作用，未能充分考虑全局结构约束"——AF2 用"attention over full MSA"正面修复了这一点。

![论文关键引文：现有架构偏好局部、AF2 用 attention 读全 MSA](assets/Alphafold%202%20Explained%EF%BC%9AWHY%20DeepMind%20had%20revolutionary%20results%20at%20CASP14/00843.webp)

输入输出清单 [【跳转到 12:23】](https://www.youtube.com/watch?v=bvZ1NsB1pes&t=743)：

- **输入**：输入序列、MSA、模板命中（template hits）；序列数据来自 **UniRef、BFD、MGnify** 三个公开数据库，结构数据来自 PDB；

![AF2 构建 MSA 所用的公开序列数据库：UniRef、BFD、MGnify](assets/Alphafold%202%20Explained%EF%BC%9AWHY%20DeepMind%20had%20revolutionary%20results%20at%20CASP14/00743.webp)
- **输出**：残基间距离、骨架扭转角、原子坐标估计、逐残基 α 碳的局部距离差异测试（lDDT 类指标，修正 RMSD/GDT 对微小局部差异的误判 [【跳转到 13:38】](https://www.youtube.com/watch?v=bvZ1NsB1pes&t=818)）。

视频还画了一个"距离矩阵 + 注意力远距连边"的示意：因为用 attention 而非 AF1 时代的 CNN，残基对之间的"边"可以拉到任意远 [【跳转到 11:36】](https://www.youtube.com/watch?v=bvZ1NsB1pes&t=696)。

![残基两两距离矩阵：attention 可以连接任意远的残基对](assets/Alphafold%202%20Explained%EF%BC%9AWHY%20DeepMind%20had%20revolutionary%20results%20at%20CASP14/00721.webp)

另外两个细节：AF2 最后用 Amber 力场做了一次弛豫（relaxation），但论文自己承认 RMSD 指标基本没变 [【跳转到 14:53】](https://www.youtube.com/watch?v=bvZ1NsB1pes&t=893)；最终模型是单一神经网络、只用公开数据训练 [【跳转到 09:13】](https://www.youtube.com/watch?v=bvZ1NsB1pes&t=553)。

## 六、一点冷静的批评

UP 主也指出了论文的软肋 [【跳转到 15:23】](https://www.youtube.com/watch?v=bvZ1NsB1pes&t=923)：CASP14 时对 3 个蛋白做了**人工干预**（手动调参）——这意味着它并非"百分百端到端"。3 个占总体比例不大，做项目时"针对蛋白调一调"也属正常操作，但严格来说会引入人为因素；他很好奇"零人工干预"版本的真实成绩。

![对 CASP14 人工干预的批评与讨论](assets/Alphafold%202%20Explained%EF%BC%9AWHY%20DeepMind%20had%20revolutionary%20results%20at%20CASP14/00923.webp)

## 小结

- 结构预测 = 序列（文本）→ 原子坐标；成绩用 CASP 竞赛 + RMSD/GDT/lDDT 类指标评判；
- **MSA 是结构预测的信息之源**：同源序列里的共变模式记录了哪些残基在结构上相互锁定；
- **注意力机制是处理 MSA 的正确工具**：一次看全、能抓长程关系，替代逐读的 LSTM 和局部的 CNN；
- AF2 的胜利 = **attention over full MSA**：不用摘要统计量，整份比对直接进网络，端到端单一模型；
- MS 并不是凭空来的——它来自预测前的**数据库搜索**（UniRef/BFD/MGnify），也就是本系列 5.7.1 "MSA Search (ColabFold)" 条目要做的事。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| MSA（多序列比对） | 把目标序列与同源序列按列对齐的矩阵；进化信息的载体，AlphaFold 的核心输入 |
| 同源序列 | 从共同祖先演化来、序列相似的蛋白；在数据库中搜"长得像"的序列得到 |
| CASP | 结构预测关键评估：两年一届的竞赛，衡量各家模型的真实水平 |
| RMSD / GDT | 预测结构与实验结构之间的距离度量；lDDT 类指标对局部折叠差异更敏感 |
| attention（注意力） | 把整个输入一次性读入、直接建模任意两位置之间关系的机制 |
| LSTM / CNN | 逐读与局部窗口式架构，难以捕捉长程依赖，是 AF1 时代与 attention 的对照 |
| 互信息 / 伪似然 | 从 MSA 中"压缩"共变信号的传统统计量；AF2 不用摘要，直接读全量比对 |
| 模板命中（template hits） | PDB 里与输入序列相似、已有实验结构的蛋白，可作为额外输入 |
| UniRef / BFD / MGnify | AlphaFold2 构建 MSA 所用的三大公开序列数据库 |
