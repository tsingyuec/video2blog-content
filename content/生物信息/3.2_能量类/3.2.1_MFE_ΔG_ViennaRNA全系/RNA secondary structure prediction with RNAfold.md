# 看懂 RNAfold 的输出：MFE 的 ΔG 越负越稳定，但完整的读法是"一个结构 + 一个系综"

> 来源视频：[RNA secondary structure prediction with RNAfold](https://www.youtube.com/watch?v=2rFY9vke1-U) · 时长 11:40
> 本篇基于视频 AI 字幕与画面整理，时间戳可跳转回原视频对应位置。

## 本讲要解决的核心问题（SCQA）

**背景**：RNAfold 是 ViennaRNA 套件里最常用的 RNA 二级结构预测工具（web server 免费、无需安装）。输入一段 FASTA 序列，点一下 Proceed，它会返回一整页结果：一个点括号结构、好几个以 **kcal/mol** 为单位的能量数字、还有一些百分比和图。

**冲突**：结果页里的数字**不是同一个东西**——`-28.90`、`-29.97`、`17.57%`、`16.60`，有的描述**单个结构**，有的描述**整个系综（ensemble）**。初学者最容易犯的错误，就是把系综自由能当成"那个结构"的能量，或者把 MFE 的 ΔG 孤立地看。

**疑问**：MFE 的 ΔG 到底是什么？"越负越稳定"该怎么理解？结果页里每个数字分别回答什么问题？

**回答（中心思想）**：RNAfold 的输出要按"**一个结构 + 一个系综**"两层来读——**MFE 结构的 ΔG**（本视频示例为 -28.90 kcal/mol）是最稳定构象的热力学标尺，**越负越稳定**；而**系综自由能**（-29.97 kcal/mol）、**MFE 结构在系综中的频率**（17.57%）、**系综多样性**（16.60）这三个数，告诉你折叠 landscape 里还有多少备选构象、MFE 结构是不是唯一主角。

![RNAfold：ViennaRNA 套件中的 RNA 二级结构预测工具](assets/RNA%20secondary%20structure%20prediction%20with%20RNAfold/00010.webp)

---

## 一、为什么要预测 RNA 二级结构：功能挂在结构上

### 1.1 结构性 RNA 的功能清单

视频开篇先回答"为什么要做这件事"：许多功能性 RNA 会形成**保守的结构**，而这些保守的结构性 RNA 参与众多细胞功能 [【跳转到 00:29】](https://www.youtube.com/watch?v=2rFY9vke1-U&t=29)：

- **翻译**：核糖体 RNA（rRNA）、转运 RNA（tRNA）；
- **RNA 切割**：RNase P 等核酶（ribozyme）；
- **蛋白质定位**：SRP（信号识别颗粒）；
- **基因调控**：在转录与翻译两个层面起作用的核糖开关（riboswitch）与 microRNA。

结构探测实验已经发现了大量**有表达、但功能尚未确定的 RNA**，因此有必要考察它们是否凭借某种 RNA 结构发挥功能 [【跳转到 00:59】](https://www.youtube.com/watch?v=2rFY9vke1-U&t=59)。结构信息能为解读 RNA 功能提供重要线索。

### 1.2 方法谱系：热力学路线与概率路线

从序列预测二级结构的计算方法由来已久 [【跳转到 01:19】](https://www.youtube.com/watch?v=2rFY9vke1-U&t=79)：

- **热力学路线**：mfold、RNAstructure、NUPACK、Sfold 等经典方法，借助热力学参数预测**最稳定的折叠**；
- **概率路线**：CONTRAFold、RNAsoft 等方法使用概率上下文无关文法或条件随机场，给出**可能性最大**的一组兼容碱基对。

视频强调了一个共性：这些方法无论用自由能、稳定性、概率还是任意评分来衡量结构，**设计原则一致、算法相似**——都是搜索整条 RNA 的最优最终构象，而**不考虑折叠过程的动力学**（尽管也有专门研究折叠动力学的工作）[【跳转到 01:49】](https://www.youtube.com/watch?v=2rFY9vke1-U&t=109)。

![核酶的折叠过程示意：从伸展链经折叠中间体到天然构象](assets/RNA%20secondary%20structure%20prediction%20with%20RNAfold/00084.webp)

### 1.3 这些预测还有什么用：系统发育

视频还列出了一层应用视角 [【跳转到 02:14】](https://www.youtube.com/watch?v=2rFY9vke1-U&t=134)：保守序列集合常被用来构建系统发育树——序列相似的生物亲缘关系较近。序列怎么选，取决于研究的分类学范围：

- 最保守的基因（如 **16S rRNA** 及其它核糖体序列）适合重建**深层**系统发育关系，并在宏基因组研究中鉴定细菌的门级类群；
- 在演化枝内保守、但带有一些突变的序列（如**看家基因**）适合研究物种间亲缘关系；
- **内转录间隔区（ITS）** 位于保守基因之间、演化很快，常用于真菌分类以及快速演化细菌的菌株分型。

---

## 二、RNAfold 是什么：一次提交，两套输出

### 2.1 软件定位

本视频使用的软件是 **RNAfold**：它从**单条 RNA 或 DNA 序列**出发，预测两样东西 [【跳转到 03:10】](https://www.youtube.com/watch?v=2rFY9vke1-U&t=190)：

1. **最小自由能（MFE）结构**——热力学上最稳定的那个构象；
2. **碱基配对概率**——每个位置跟谁配对、配对把握有多大。

### 2.2 折叠算法与基本选项

服务器输入页下方是"折叠算法与基本选项" [【跳转到 05:38】](https://www.youtube.com/watch?v=2rFY9vke1-U&t=338)：

![RNAfold 的折叠算法选项：MFE+配分函数、仅 MFE、无末端 GU 配对、避免孤立碱基对](assets/RNA%20secondary%20structure%20prediction%20with%20RNAfold/00363.webp)

- **minimum free energy (MFE) and partition function**：最小自由能 + 配分函数（本视频选择，也是默认）；
- **minimum free energy (MFE) only**：只算最小自由能结构；
- **no GU pairs at the end of helices**：螺旋末端不含 GU 配对；
- **avoid isolated base pairs**：避免孤立碱基对（`-d2`，默认勾选）。

### 2.3 长度限制

页面上写明了当前限制：**配分函数计算最多 7,500 nt，仅 MFE 预测最多 10,000 nt** [【跳转到 07:18】](https://www.youtube.com/watch?v=2rFY9vke1-U&t=438)。再长的序列需要拆分或用本地命令行处理。

![RNAfold 输入页：FASTA 粘贴框、文件上传与长度限制说明](assets/RNA%20secondary%20structure%20prediction%20with%20RNAfold/00438.webp)

### 2.4 输出选项

- 交互式 RNA 二级结构图；
- **带可靠性标注**的二级结构图（仅配分函数折叠提供——这正是配分函数的价值所在）；
- 山形图（Mountain plot）。

如果不想在页面上等结果，填入邮箱即可接收结果邮件；否则点击 **Proceed**，任务可能先进入队列，稍等片刻 [【跳转到 06:53】](https://www.youtube.com/watch?v=2rFY9vke1-U&t=413)。

---

## 三、实操：从 FASTA 序列到结果页

视频的实操路径很简单 [【跳转到 04:38】](https://www.youtube.com/watch?v=2rFY9vke1-U&t=278)：

1. Google 搜索 "RNAfold"，点击 **RNAfold web server**；
2. 在输入框粘贴序列（**FASTA 格式，以 `>` 符号开头**），或点击 sample sequence 载入服务器自带的示例序列（一条 74 nt 的短序列），也可以用 Choose File 上传序列文件；
3. 保持默认选项（MFE + 配分函数、避免孤立碱基对），点击 **Proceed**。

![RNAfold web server 首页：粘贴序列、上传文件或使用示例序列](assets/RNA%20secondary%20structure%20prediction%20with%20RNAfold/00313.webp)

示例序列很短，一分钟内就能出结果。结果可以保存、分析，并用于论文 [【跳转到 07:32】](https://www.youtube.com/watch?v=2rFY9vke1-U&t=452)。

---

## 四、读数（一）：MFE 结构的 ΔG——越负越稳定

### 4.1 最优结构与它的能量

结果页第一部分是"**Results for minimum free energy prediction**"：以**点括号表示法**（dot-bracket，配对位置写 `()`、未配对写 `.`）给出**最优二级结构**，并标注其最小自由能 [【跳转到 07:57】](https://www.youtube.com/watch?v=2rFY9vke1-U&t=477)：

> The optimal secondary structure in dot-bracket notation with a **minimum free energy of -28.90 kcal/mol** is given below.

这就是 MFE 的 ΔG——对这条 74 nt 的示例序列是 **-28.90 kcal/mol**。

![RNAfold 结果页：MFE 结构 -28.90 kcal/mol 与系综三个数](assets/RNA%20secondary%20structure%20prediction%20with%20RNAfold/00477.webp)

### 4.2 ΔG 的直觉含义

怎么理解这个数？用热力学的语言：**ΔG 越负，结构越稳定、越容易自发形成**。mfold/RNAfold 这类工具的全部逻辑，就是在所有可能的碱基配对组合里，找出让自由能**降到最低**的那一个组合——组合中每形成一个螺旋（stacking 堆积有利）能量下降，每留一个环（loop 有代价）能量上升，最终的 ΔG 就是这笔账的总和，单位 **kcal/mol**（千卡每摩尔）。

MFE 结构可以下载为 **Vienna Format** 或 **CT Format**；如果想知道这个结构的热力学细节（每一项能量贡献），可以把结构提交给 **RNAeval** web server 复核 [【跳转到 08:22】](https://www.youtube.com/watch?v=2rFY9vke1-U&t=502)。

---

## 五、读数（二）：系综三个数——单一结构之外的全部真相

结果页第二部分是"**Results for thermodynamic ensemble prediction**"，这是选了"配分函数"才会有的输出，也是最容易误读的地方。三个数字 + 一个结构：

### 5.1 系综自由能：-29.97 kcal/mol

> The free energy of the thermodynamic ensemble is **-29.97 kcal/mol**.

注意：它**不是 MFE 结构的能量**，而是整个**系综**（ensemble，所有可能构象按玻尔兹曼权重分布）的自由能。因为它汇总了大量结构，数值可以比 MFE 更负——本例 -29.97 比 -28.90 更负，就是这个原因。

### 5.2 MFE 结构的频率：17.57%

> The frequency of the MFE structure in the ensemble is **17.57%**.

它回答"MFE 结构在系综里占多大分量"。17.57% 说明：对这条短序列，最稳定构象确实是大头，但也远非唯一——系综里还有大量相近的备选构象。

### 5.3 系综多样性：16.60

> The ensemble diversity is **16.60**.

它衡量系综里结构之间的**平均差异**：数值越大，备选构象彼此越不同，单一预测越需要谨慎看待。

### 5.4 centroid 结构：-28.10 kcal/mol

> The centroid secondary structure in dot-bracket notation with a **minimum free energy of -28.10 kcal/mol** is given below.

**centroid（中心）结构**是与系综平均离得最近的代表结构。注意它的 ΔG（-28.10）反而比 MFE（-28.90）**高一点**——centroid 追求的是"代表性"，不是"能量最低"。还可以查看包含碱基配对概率的**点阵图（dot plot）**，可下载 EPS/PDF 或用图像转换器转换格式 [【跳转到 08:22】](https://www.youtube.com/watch?v=2rFY9vke1-U&t=502)。

![结果页下半部：centroid 结构 -28.10 kcal/mol 与点阵图入口](assets/RNA%20secondary%20structure%20prediction%20with%20RNAfold/00502.webp)

### 5.5 一个提醒：序列越长，系综越大

这组数有多依赖序列长度？在这套笔记的姊妹篇里，同一条管线处理**约 1.4 kb 的完整基因 mRNA** 时，MFE 结构在系综中的频率只有 **0.00%**、系综多样性高达 390——序列越长，可能构象越爆炸，MFE 结构几乎只是沧海一粟。所以：**短序列可以更信任 MFE 结构本身；长序列要更多依赖配对概率与可靠性标注，而不是只盯一个 ΔG**（参见 [Secondary structure prediction using mFOLD and Forna](Secondary%20structure%20prediction%20using%20mFOLD%20and%20Forna｜mRNA%20structure%20forecast%20tools.md)）。

---

## 六、图形化输出：让数字看得见

### 6.1 交互式结构图与着色

结果页下方的图形输出区提供 [【跳转到 08:49】](https://www.youtube.com/watch?v=2rFY9vke1-U&t=529)：

![结构显示选项：MFE 结构与 centroid 结构、Plain Sequence 与 No Sequence](assets/RNA%20secondary%20structure%20prediction%20with%20RNAfold/00554.webp)

- **MFE 结构**与 **centroid 结构**两套图分别可看；
- 序列显示选项：**Plain Sequence**（标注碱基）/ **No Sequence**（只留图形）；
- 其它显示选项：**按碱基配对概率着色**、**按位置熵（positional entropy）着色**或不着色——颜色直接把"哪些配对有把握"画在结构上 [【跳转到 09:14】](https://www.youtube.com/watch?v=2rFY9vke1-U&t=554)。

![着色与下载选项：配对概率、位置熵、EPS/PDF、VIEW IN FORNA](assets/RNA%20secondary%20structure%20prediction%20with%20RNAfold/00606.webp)

图片提供多种下载格式：**EPS、PDF**，还有 IMAGE CONVERTER 转换为其它格式，甚至 **VIEW IN FORNA** 直接在浏览器里动态查看（Forna 的用法见姊妹篇）。

### 6.2 山形图与命令行等价物

**山形图（Mountain plot）** 用另一种方式概括结果：横轴是序列位置，纵轴刻画配对情况随位置的变化，把 MFE 结构、centroid 结构与配对概率画在一起对比 [【跳转到 10:01】](https://www.youtube.com/watch?v=2rFY9vke1-U&t=601)。

结果页底部还写着本次计算使用的版本与**等价命令行** [【跳转到 10:31】](https://www.youtube.com/watch?v=2rFY9vke1-U&t=631)：

![结果页底部：RNAfold 2.4.18 与等价命令行 RNAfold -p -d2 --noLP](assets/RNA%20secondary%20structure%20prediction%20with%20RNAfold/00631.webp)

```bash
RNAfold -p -d2 --noLP < test_sequence.fa > test_sequence.out
```

这正是 ViennaRNA 全系的用法：网页里点一下的每个选项，都对应命令行的一个参数（`-p` 配分函数、`-d2` 避免孤立碱基对、`--noLP` 无孤立配对）。本地批量处理长序列时，走的就是这条路。

![系综三数与点阵图：-29.97 kcal/mol、17.57%、16.60](assets/RNA%20secondary%20structure%20prediction%20with%20RNAfold/00657.webp)

---

## 七、多序列保守区：方框里的系统发育线索

视频最后补了一个延伸用法 [【跳转到 10:52】](https://www.youtube.com/watch?v=2rFY9vke1-U&t=652)：如果想找**多条序列的保守区域**（系统发育分析常用），需要**同时提交不止一条序列**——各序列中保守的部分会用**方框**标出。本例只有一条序列，没有可比对的保守区，所以没有出现方框；提交多条序列时方框就会显现，可用于系统发育分析。

---

## 小结

- RNAfold（ViennaRNA 套件）输入 FASTA 序列，同时输出 **MFE 结构**与**碱基配对概率**两套结果；网页版限制：配分函数 7,500 nt、仅 MFE 10,000 nt。
- **MFE 的 ΔG 是热力学标尺：越负越稳定**（示例：-28.90 kcal/mol）；配对有奖、成环有价，ΔG 就是这笔账的总和。
- 完整读法是"**一个结构 + 一个系综**"：系综自由能（-29.97，比 MFE 更负属正常）、MFE 结构频率（17.57%）、系综多样性（16.60）、centroid 结构（-28.10，求代表性不求能量最低）。
- **序列越长系综越大**：短序列可更信任 MFE 结构；长序列的 MFE 结构频率可能趋近 0%，要靠配对概率/可靠性标注辅助判断。
- 图形输出按**配对概率/位置熵**着色，山形图横向对比多个代表结构；结果页的**等价命令行**（`RNAfold -p -d2 --noLP`）是通往 ViennaRNA 本地批处理的桥。
- 多条序列一起提交，可用方框标注保守区域，服务系统发育分析。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| MFE（minimum free energy） | 最小自由能：所有可能构象中能量最低的结构，是工具搜索的目标 |
| ΔG / kcal/mol | 自由能变化及其常用单位；对折叠而言**越负越稳定、越可能自发形成** |
| 点括号表示法（dot-bracket） | 用 `()` 与 `.` 书写二级结构的文本记法，见 2.4 节 |
| 配分函数（partition function） | 对整个系综加权求和的计算；由此得到配对概率与系综各项指标 |
| 系综（ensemble） | 所有允许构象按玻尔兹曼权重组成的集合，"结构云" |
| 系综自由能 | 整个系综的自由能（`-RT·ln Z`），不是单个结构的能量 |
| MFE 结构频率 | MFE 结构在系综中占的概率质量；17.57% 说明它是大头但非唯一 |
| 系综多样性 | 系综内结构间的平均差异，越大越说明备选构象五花八门 |
| centroid 结构 | 离系综平均最近的代表结构；ΔG 可以比 MFE 略高 |
| dot plot | L×L 点阵图，点的深浅 = 相应碱基对的配对概率 |
| RNAeval | ViennaRNA 家族中复核给定结构热力学细节的工具 |
| FASTA | 以 `>` 开头的序列文本格式，几乎所有预测工具的基础输入 |
| 位置熵（positional entropy） | 每个位置配对不确定性的度量，可用来着色 |
