# RNA structure prediction lecture

> 视频来源：[YouTube《RNA structure prediction lecture》](https://www.youtube.com/watch?v=iN6VBU2jm1M)（38:58），一节面向初学者的 RNA 二级结构预测课程：从"为什么要预测 RNA 结构"讲起，过一遍结构层次与亚型，再分头介绍 **ab initio（从头预测）** 与 **比较法** 两大流派，并用 **Nussinov 动态规划矩阵**做了逐格演算的完整演示——是理解 RNAfold/MFold 这类工具背后原理的最短路径。视频字幕为英文自动生成，本文基于文稿整理翻译；文中数字与结论均出自视频内容，可点击时间戳回看核对。

## 本讲要解决的核心问题（SCQA）

**背景**：RNA 是三大生物大分子之一，其结构直接关联基因表达、病毒感染与免疫等机制（[【跳转到 01:00】](https://www.youtube.com/watch?v=iN6VBU2jm1M&t=60)）。

**冲突**：实验测结构只有 X 射线晶体学与 NMR 两条路，都极其耗时、昂贵、依赖专家，小误差就全盘报废——不可能对所有 RNA 都测一遍（[【跳转到 02:00】](https://www.youtube.com/watch?v=iN6VBU2jm1M&t=120)）。

**疑问**：于是计算预测成为替代方案。但 RNA 结构千姿百态，从哪入手？算法又怎么从一条序列"算"出结构？

**回答（中心思想）**：从**二级结构**入手（配对关系，比三维结构容易得多）。预测分两大流派：**ab initio**——假设结构由序列唯一决定，搜索自由能最低（或配对最多）的结构，核心是 Nussinov 动态规划；**比较法**——假设同源 RNA 保留相同结构，从协变突变里读出保守配对。本讲把两条路的原理与代表性程序（MFold/RNAfold、Foldalign/Dynalign）一次讲清。

## 一、为什么要预测 RNA 结构

[【跳转到 00:30】](https://www.youtube.com/watch?v=iN6VBU2jm1M&t=30)

RNA 携带遗传信息，三种经典形态各司其职：mRNA 指挥蛋白质合成，rRNA 在核糖体内搭建结构支架，tRNA 是多肽合成时的氨基酸搬运工（[【跳转到 03:30】](https://www.youtube.com/watch?v=iN6VBU2jm1M&t=210)）。后来的发现不断扩编：RNA 有催化活性（核酶），参与剪接、加工与编辑；微 RNA（miRNA）这类小非编码 RNA 通过与 mRNA 互作调控基因表达（[【跳转到 04:30】](https://www.youtube.com/watch?v=iN6VBU2jm1M&t=270)）。

![X 射线晶体学与 NMR：准确但昂贵、耗时、依赖专家](assets/RNA%20structure%20prediction%20lecture/00205.webp)

而结构与功能的关系因分子而异：mRNA 基本呈线性、无需折叠；rRNA 与 tRNA 则**必须**折叠出特定二级、三级结构才能行使功能——所以搞清它们的结构尤为重要（[【跳转到 06:30】](https://www.youtube.com/watch?v=iN6VBU2jm1M&t=390)）。

## 二、结构层次与亚型

### 2.1 与 DNA 的关键区别

[【跳转到 05:30】](https://www.youtube.com/watch?v=iN6VBU2jm1M&t=330)

DNA 主要以双链存在；RNA 是单链，但可在局部自杂交形成**部分双链区段**——这正是二级结构的来源。

![DNA 双链 vs RNA 单链自杂交](assets/RNA%20structure%20prediction%20lecture/00355.webp)

### 2.2 三级结构层次

[【跳转到 07:00】](https://www.youtube.com/watch?v=iN6VBU2jm1M&t=420)

- **一级结构**：A/C/G/U 四种碱基的线性序列；
- **二级结构**：配对区与单链区的总体排布——配对以 Watson-Crick（A-U、G-C）为主，也有稳定性较低、常嵌在螺旋中的 **G-U 摆动配对**（wobble）；
- **三级结构**：碱基的三维排布，复杂得多。

![一级/二级/三级结构层次](assets/RNA%20structure%20prediction%20lecture/00430.webp)

### 2.3 四种经典亚型

[【跳转到 09:30】](https://www.youtube.com/watch?v=iN6VBU2jm1M&t=570)

按螺旋配对的排布，二级结构有四种基本亚型（[【跳转到 10:30】](https://www.youtube.com/watch?v=iN6VBU2jm1M&t=630)）：

1. **发夹环（hairpin loop）**：单链区把两端连回一个配对区——最经典的结构单元；
2. **突起环（bulge loop）**：单链区从螺旋一侧"鼓"出来；
3. **内环（interior loop）**：两条链上各有一段单链区，夹在两个相邻配对区段之间——两侧同时鼓出；
4. **多分支环（multibranch loop）**：把三个或以上配对区段聚拢的连接区，也叫螺旋连接（helical junction）。

![四种经典亚型：发夹、突起、内环、多分支环](assets/RNA%20structure%20prediction%20lecture/00595.webp)

### 2.4 超出经典模型的元素

[【跳转到 12:00】](https://www.youtube.com/watch?v=iN6VBU2jm1M&t=720)

还有三类"超纲"结构，传统预测算法大多不覆盖：**假结（pseudoknot）**——发夹环内的残基与环外残基配对；**kissing hairpin**——两个发夹的环残基互相氢键结合；**发夹-突起接触（hairpin-bulge contact）**——发夹环残基与突起残基互作。这类超二级结构在自然结构中相对少见，多数常规预测算法默认不管（[【跳转到 13:00】](https://www.youtube.com/watch?v=iN6VBU2jm1M&t=780)）。

![假结、kissing hairpin 与发夹-突起接触](assets/RNA%20structure%20prediction%20lecture/00760.webp)

## 三、Ab initio 方法：从序列搜能量最低解

[【跳转到 13:30】](https://www.youtube.com/watch?v=iN6VBU2jm1M&t=810)

ab initio 方法的公理只有一条：**RNA 的结构由其序列唯一决定**，所以设计算法搜索"稳定"结构即可——自由能越低越好。形成碱基对释放能量，配对越多能量越低，因此早期程序直接**最大化配对数**；参数来自小分子的经验测定：G-C 比 A-U 稳，A-U 又比 G-U 稳（[【跳转到 15:00】](https://www.youtube.com/watch?v=iN6VBU2jm1M&t=900)）。

但配对不是独立事件：**螺旋堆积力（stacking）**让相邻配对互相稳定——这就是螺旋形成的协同性；紧邻环与突起的配对则会被去稳定。所以完整算法是：先找所有可能的配对方案，再把稳定与去稳定因素全算进去，取总能量最低的构象（[【跳转到 17:00】](https://www.youtube.com/watch?v=iN6VBU2jm1M&t=1020)）。

![ab initio：搜所有配对方案，取自由能最低者](assets/RNA%20structure%20prediction%20lecture/00896.webp)

### 3.1 动态规划与它的缺陷

[【跳转到 20:00】](https://www.youtube.com/watch?v=iN6VBU2jm1M&t=1200)

找所有配对区有三种常用工具：动态规划、配分函数、点阵图（dot plot）。点阵图对小分子找单一结构很有效；动态规划适合大分子在多方案中选最稳的一种；但它只输出**单一最优解**——现实中 RNA 常有一批能量几乎相同、配对却不同的亚优结构，这是 DP 的固有缺陷（[【跳转到 21:30】](https://www.youtube.com/watch?v=iN6VBU2jm1M&t=1290)）。补救办法是加**配分函数**：在热力学平衡下算出每个配对出现的概率分布，在给定能量范围内枚举亚优结构（[【跳转到 22:30】](https://www.youtube.com/watch?v=iN6VBU2jm1M&t=1350)）。

![DP 只给单一最优解；配分函数补上概率分布](assets/RNA%20structure%20prediction%20lecture/01257.webp)

两个最著名的 ab initio 程序由此得名：**MFold** 与 **RNAfold**（[【跳转到 23:30】](https://www.youtube.com/watch?v=iN6VBU2jm1M&t=1410)）。

## 四、Nussinov 算法逐步演算

### 4.1 动态规划思想

[【跳转到 23:30】](https://www.youtube.com/watch?v=iN6VBU2jm1M&t=1410)

Nussinov 算法是动态规划类的代表：把大问题拆成易算的子问题，解出子问题后通过**回溯（backtrace）**还原完整解。目标：在一条核苷酸链上找最优配对方式；打分方案可以简单到"每对配对 +1，其余 +0"（[【跳转到 24:30】](https://www.youtube.com/watch?v=iN6VBU2jm1M&t=1470)）。

![Nussinov：子问题求解 + 回溯](assets/RNA%20structure%20prediction%20lecture/01420.webp)

记 OPT(i, j) 为位置 i 与 j 之间的最高得分。给结构立四条规则（[【跳转到 26:00】](https://www.youtube.com/watch?v=iN6VBU2jm1M&t=1560)）：

1. **配对必须合法**：i 与 j 必须能形成 Watson-Crick 配对（A-U 或 G-C）；
2. **留出间距**：i < j − 4，至少隔四个位置——太近的配对会有空间位阻、不稳定；
3. **不交叉**：若 (i, j) 与 (k, l) 同时在结构中且 i < k，必须满足 i < k < j < l——交叉配对就是假结，Nussinov 直接禁止；
4. **一夫一妻**：任一位置最多出现在一个配对里。

### 4.2 矩阵怎么填

[【跳转到 28:30】](https://www.youtube.com/watch?v=iN6VBU2jm1M&t=1710)

把序列写在矩阵上方与侧方，对角线初始化为 0，然后逐格填：每个位置取四种情形的最大值——i 不配（取 OPT(i+1, j)）、j 不配（取 OPT(i, j−1)）、i 与 j 恰好配对（对角线 + 1）、或在此处分裂成两个子问题（OPT(i, k) + OPT(k+1, j)，k 遍历中间）。讲课中用一条短序列把矩阵一格一格填满，直观展示了"配对加一、不配取邻"的机械流程（[【跳转到 29:30】](https://www.youtube.com/watch?v=iN6VBU2jm1M&t=1770)）。

![Nussinov 矩阵逐格填充演示](assets/RNA%20structure%20prediction%20lecture/01782.webp)

填完矩阵后从右上角回溯，配过的位置连起来就是预测的碱基对集合（[【跳转到 32:30】](https://www.youtube.com/watch?v=iN6VBU2jm1M&t=1950)）。

![回溯得到配对；Nussinov 的局限清单](assets/RNA%20structure%20prediction%20lecture/02004.webp)

### 4.3 Nussinov 的局限

[【跳转到 33:30】](https://www.youtube.com/watch?v=iN6VBU2jm1M&t=2010)

单纯最大化配对数得到的结构**生物学上往往不靠谱**：没考虑堆积能量、不区分环的大小、多环没有专门打分、只给一个解（许多亚优解进不了视野）、更不可能给出交叉配对（假结）。它真正的价值是骨架——把打分换成自由能参数、加上配分函数，就是 MFold/RNAfold 的工作方式。

## 五、比较法：让进化替你标出配对

[【跳转到 34:00】](https://www.youtube.com/watch?v=iN6VBU2jm1M&t=2040)

第二条路线的假设：**同源 RNA 进化中保留相同二级结构**。功能基序要保结构，于是配对位点上的突变必须"成对补偿"——一条链变了，另一条跟着变回配对（C-G→U-G→U-A），这就是**协变（covariation）**；不协变的突变会破坏结构、进而破坏功能（[【跳转到 35:00】](https://www.youtube.com/watch?v=iN6VBU2jm1M&t=2100)）。

![协变性：配对位点的补偿突变暴露保守结构](assets/RNA%20structure%20prediction%20lecture/02187.webp)

算法先对一组同源序列做比对，再从比对里找相关突变模式、推断共同保守的配对。按输入不同分两类（[【跳转到 36:00】](https://www.youtube.com/watch?v=iN6VBU2jm1M&t=2160)）：

1. **需要预比对**：用标准比对程序（如 T-Coffee、Clustal）先做好多序列比对，再在其上推断共识结构；实践中常与热力学项结合以提高精度。成败全看序列组：**要足够像（比对得准）又要足够不像（协变得出来）**；
2. **不需预比对**：算法同时完成比对与折叠，打分里兼顾序列相似性与能量项；完整的多序列动态规划计算量爆炸，所以现行程序（**Foldalign**、**Dynalign**）都限制在两条序列（[【跳转到 37:30】](https://www.youtube.com/watch?v=iN6VBU2jm1M&t=2250)）。

![两类比较法程序：先比对 vs 同时比对折叠](assets/RNA%20structure%20prediction%20lecture/02262.webp)

## 写在最后

这节课把 RNA 二级结构预测的地基铺完了：结构层次与亚型是"对象"，ab initio 与比较法是"两条算法路线"，Nussinov 矩阵是"最小可运行原型"。理解了它，再去读 RNAfold 文档（把打分表换成 Turner 能量参数、把 max 换成配分函数）就会豁然开朗；而假结、kissing hairpin 这些"超纲"元素，正是进阶算法（如 5.5.1 条目中 Lorenz 与 Condon 两讲）要接管的内容。
