# PSI-BLAST 迭代搜索与 profile：MSA 是怎么造出来的

> 视频来源：[结构生物信息学【密歇根大学张阳】：d2-多序列比对 (MSA, PSI-Blast)](https://www.bilibili.com/video/BV1jp421m7FW/?t=0)（Bilibili · 张阳，2017 年武汉结构生物信息学讲习班 · 时长约 64 分钟）
> 导读：这是一堂带大量学生提问的板书课，讲的是"给定一条 query，怎么在序列库里把它的同源序列搜出来并排成多序列比对"。本文按视频顺序整理：BLAST 的三步 → PSI-BLAST 用 profile 迭代 → 弱同源为什么重要 → profile/PSSM 怎么算（伪计数与 Neff）→ 跑一次 PSI-BLAST 的参数与输出。字幕为自动识别，术语已按幻灯片订正；比对的基础定义见本系列 1.2.1，协变信号如何变成接触图见 1.2.3。

## 本讲要解决的核心问题（SCQA）

**背景**：结构预测的输入端是一个多序列比对（MSA）：每一行是一条同源序列，每一列是同一个残基位置。有了比对，才有"这一列在所有物种里都不变"（保守）和"这两列一起变"（共变）这两类证据。

**冲突**：但 MSA 不会自己出现。你手上只有一条 query，库里却有上千万条序列；真正对你有用的往往不是 identity 90% 的近亲（那种"傻瓜都知道是一样的"），而是 identity 只剩 20%、却仍然折叠成同一结构的远亲——单靠两条序列直接比对，根本认不出它们。

**疑问**：搜索算法具体怎么走？为什么"拿一批同源序列做成一个表再去搜"就能找到远亲？搜到什么程度算够、搜得多是不是就等于信息多？

**回答（中心思想）**：PSI-BLAST 把"搜索"和"比对"接成了一个循环——先用 query 找到高打分片段，带空位延伸后按 E-value 过滤，把留下的序列排成 MSA，再把这个 MSA 压成一个**位置特异性打分矩阵（profile/PSSM）**，用矩阵代替单条序列回去重搜；循环的关键不是搜到更多序列，而是把"哪些位置重要"这件事写进了打分表，因此第二轮起找的是"亲戚的亲戚"。而 profile 能不能算稳，取决于每个位置上有多少条**独立**的序列——这正是伪计数与有效序列数 $N_c$ 要解决的问题。

---

## 一、MSA 是搜索的产物，不是给定的输入

![PSI-BLAST 要解决的问题：一条 query 序列 + 序列数据库 → 相关序列的多序列比对](assets/PSI-BLAST%20迭代搜索与%20profile：MSA%20是怎么造出来的/00000.webp)

课上把问题写得很直白：**给定一条 query 序列，怎么从库里找出所有与它同源的序列** [【跳转到 00:00】](https://www.bilibili.com/video/BV1jp421m7FW/?t=0)。左边是 query（一条未知结构、未知功能的序列），中间是三个库：核酸库（GenBank）、蛋白库（SwissProt）、结构库（PDB），右边出来的是"相关序列的多序列比对"。幻灯片引的是 Altschul 等人 1997 年那篇 Gapped BLAST 与 PSI-BLAST 的论文。

这里有个容易被忽略的区分：**比对（MSA）和搜索（PSI-BLAST）是两件事**。老师在后半段专门强调过 [【跳转到 27:08】](https://www.bilibili.com/video/BV1jp421m7FW/?t=1628)：

- 比对算法（如 ClustalW 一类）做的是"**已经知道这些序列同源**，怎么把它们排整齐"——它要用动态规划，甚至要考虑进化树；
- PSI-BLAST 做的是"**给定一条序列，去库里找同源成员**"——它不做进化树，用的是很快的启发式搜索，输出虽然也是比对，但那是"搜出来的序列排在一起"。

所以本文讲的是后者：MSA 是怎么被"搜"出来的。

### 1.1 从一条 query 到一列证据

![PSI-BLAST 流程图：query → 找 word/HSP → 动态规划延伸 → E-value<0.01 → 多序列比对 → 构造 profile → 迭代](assets/PSI-BLAST%20迭代搜索与%20profile：MSA%20是怎么造出来的/00025.webp)

整支视频其实就是这张流程图的展开 [【跳转到 00:25】](https://www.bilibili.com/video/BV1jp421m7FW/?t=25)：

1. **Identify words**：在 query 里找出短片段（word），到库里比对，得到高打分片段对（HSP，high-scoring segment pair）；
2. **Extension of HSP by dynamic programming**：把 HSP 向两边延伸，这一步用动态规划，因此**可以引入空位**；
3. **E-value < 0.01 only**：只留下统计上显著的命中；
4. **Multiple sequence alignment**：把留下的序列排成比对；
5. **Construction of profile**：把比对压成一个打分矩阵；
6. 若迭代次数小于 3，回到第 1 步，但这次**用 profile 去搜**，而不是用 query 序列；迭代到 3 次或比对收敛，输出最终结果。

### 1.2 word、HSP 与带 gap 的延伸

![两条序列的点阵图：对角线上的点就是匹配，连成斜线的一段就是 word/HSP](assets/PSI-BLAST%20迭代搜索与%20profile：MSA%20是怎么造出来的/00241.webp)

word 是怎么找的？把 query 和库里一条序列画成点阵：横纵坐标分别是两条序列的残基序号，对角线上的点表示匹配 [【跳转到 04:01】](https://www.bilibili.com/video/BV1jp421m7FW/?t=241)。如果若干点能连成一条 45 度的斜线，就说明这一段对得很好。幻灯片用蚕豆血红蛋白和马血红蛋白做例子，图上能清楚看到几段斜线。

![动态规划延伸允许空位：点阵图里出现"断开的斜线"，比对结果里就出现 gap](assets/PSI-BLAST%20迭代搜索与%20profile：MSA%20是怎么造出来的/00366.webp)

延伸这一步的差别很关键：**BLAST 的延伸不引入空位（ungapped），PSI-BLAST 用动态规划延伸，可以插入空位** [【跳转到 06:06】](https://www.bilibili.com/video/BV1jp421m7FW/?t=366)。点阵图里表现为斜线断开、错开一段再接上；右下角的比对文本里就出现了 `-`（gap），D 表示完全相同、L 表示相似但不相同。老师顺带提了一句工程上的细节：完整动态规划要把所有点都算一遍，很慢；这里只从 word 出发向两边延伸，所以快得多。

## 二、PSI-BLAST 的关键改动：用 profile 去搜索

### 2.1 两个中等 word 优于一个高分 word

BLAST 与 PSI-BLAST 的第一个差别：**BLAST 只找一个高分的 word，PSI-BLAST 允许两个分数稍低的 word** [【跳转到 04:51】](https://www.bilibili.com/video/BV1jp421m7FW/?t=291)。

道理不难：如果把 word 的阈值定得很高（比如要求 score 等于 100），会漏掉很多真实但分数中等的匹配；而如果两个中等分数的 word 恰好落在同一条 45 度对角线的两个位置上，它们合起来提供的证据可能比一个大 word 更强 [【跳转到 05:16】](https://www.bilibili.com/video/BV1jp421m7FW/?t=316)。这是"提高灵敏度"的第一处设计。

### 2.2 profile-sequence 比对：把"哪些位置重要"写进矩阵

![profile 与序列比对：上方是一条 query，下方是多序列比对，彩色列表示该位置偏好的残基](assets/PSI-BLAST%20迭代搜索与%20profile：MSA%20是怎么造出来的/00422.webp)

第三步是整个算法有效的原因 [【跳转到 07:02】](https://www.bilibili.com/video/BV1jp421m7FW/?t=422)：一开始是 query 与库里一条序列的比对（sequence-sequence），现在你手上已经有一批同源序列了，于是变成 **profile 与序列的比对（profile-sequence）**。

为什么这样更准？因为把一批同源序列摞在一起之后，你就能看出**哪些位置重要、哪些位置不重要** [【跳转到 07:27】](https://www.bilibili.com/video/BV1jp421m7FW/?t=447)。单条序列比对时，你不知道这个位置的 I 是"必须"还是"碰巧"；现在你知道这一列是保守的，必须是 I 才好，于是比对更精确，能往下找到更远、更弱的同源序列。

### 2.3 迭代：找"亲戚的亲戚"

![如何构造多序列比对：一堆同源序列怎么排成列，列上还标了每个位置的保守程度](assets/PSI-BLAST%20迭代搜索与%20profile：MSA%20是怎么造出来的/01633.webp)

课堂上学生反复追问"profile 到底怎么来的"，老师的回答是这条链 [【跳转到 10:08】](https://www.bilibili.com/video/BV1jp421m7FW/?t=608)：

1. 找到 query 的所有同源序列（"你的亲戚"）；
2. 把这些亲戚排成比对，得到一个数表，就是 profile——**它包含了所有这些同源序列的信息**；
3. 拿这个表回去搜，它会找到比你第一次更准确的结果，因为它是"**亲戚的亲戚**"，离你更近；
4. 新找到的序列再排进比对、再生成新的 profile、再搜……

为什么要绕这一圈？老师的说法是：库里几十万上百万条序列，你怎么知道哪一条和你相关？靠的就是搜索函数足够敏感 [【跳转到 08:17】](https://www.bilibili.com/video/BV1jp421m7FW/?t=497)。而 profile 里已经标出了"哪些位置重要"，比对时如果恰好是 I 就给很高的分、是 F 就给低分，打分自动完成——所以它对单条序列的比对更敏感，这就是它能找到弱同源、同时又能守住保守位点的原因 [【跳转到 15:08】](https://www.bilibili.com/video/BV1jp421m7FW/?t=908)。

## 三、弱同源才是重点

![黑板上画的进化树：同一个祖先分出的几支，彼此 identity 可能只剩 20%，却仍是同源](assets/PSI-BLAST%20迭代搜索与%20profile：MSA%20是怎么造出来的/01012.webp)

这一段是全场最值得记住的判断 [【跳转到 15:53】](https://www.bilibili.com/video/BV1jp421m7FW/?t=953)：

- 如果两个蛋白 identity 高达 80%，那叫 **close homolog（近缘同源）**，"傻瓜都知道这两个蛋白是一样的"，找出来没有难度；
- 但绝大多数蛋白在进化过程中同源关系已经**弱化**了：两条序列 identity 可能只剩 20%，单独拿序列去搜根本找不到，可它们仍然有同样的结构和功能。

为什么弱同源还能保持同样的结构？因为结构靠的是**某些关键位点**（相互独立的几个残基）被保住了；如果把关键位置都突变掉，结构就不一样了 [【跳转到 18:49】](https://www.bilibili.com/video/BV1jp421m7FW/?t=1129)。所以算法的目标就是：**把 identity 阈值往下压一点，把那些"弱但真实"的同源捞出来**——老师给了一个很直观的说法，identity 阈值每降低 1%，能解决的问题会明显增多 [【跳转到 18:21】](https://www.bilibili.com/video/BV1jp421m7FW/?t=1101)。

这也解释了为什么"搜得多"和"信息多"不是一回事：库里堆的是大量近重复的序列，它们不带来新信息；真正有价值的是**跨越更大进化距离的那部分多样性**。

## 四、profile 怎么算：从频率到 PSSM

![计算 PSI-BLAST profile：Gribskov 的频率加权法与 PSI-BLAST 的对数几率法](assets/PSI-BLAST%20迭代搜索与%20profile：MSA%20是怎么造出来的/01823.webp)

给定一个比对，怎么把它压成 20×L 的矩阵？课上给了两条路线 [【跳转到 29:33】](https://www.bilibili.com/video/BV1jp421m7FW/?t=1773)：

- **Gribskov 路线**：把该位置上各种残基的频率，按替换矩阵（BLOSUM）加权求和，得到 $S(i,j)$；
- **PSI-BLAST 路线**：算对数几率

$$
S(i,j)=\log\frac{Q_{ij}}{P_i}
$$

其中 $Q_{ij}$ 是"残基 $A_i$ 出现在位置 $j$ 的估计概率"，$P_i$ 是该残基的**背景概率**（在整个数据库里随机碰到它的概率）[【跳转到 30:23】](https://www.bilibili.com/video/BV1jp421m7FW/?t=1823)。

对数几率的好处是：如果某个位置强烈偏好 I，那么 $Q_{Ij}$ 远大于背景 $P_I$，分数为正；如果某个位置对 F 很排斥，分数为负。矩阵的每一列就是"这个位置喜欢什么、讨厌什么"。

### 4.1 伪计数：样本少的时候不能直接除

![伪计数公式：N 大时直接用观测频率，N 小时用背景概率平滑](assets/PSI-BLAST%20迭代搜索与%20profile：MSA%20是怎么造出来的/01954.webp)

这里有个统计学上的坑。老师在黑板上用抛硬币打比方 [【跳转到 31:44】](https://www.bilibili.com/video/BV1jp421m7FW/?t=1904)：抛 $N$ 次、出现 $K$ 次，用 $K/N$ 估计概率，只有当 $N$ 很大时才成立。而在 MSA 的某一列上，$N$ 常常很小——**你只有两三条序列，其中一条碰巧是某个稀有残基，直接算频率就会得到一个荒谬的概率**。

解决办法是加伪计数（pseudo count）[【跳转到 32:34】](https://www.bilibili.com/video/BV1jp421m7FW/?t=1954)：

$$
P_i=\frac{k_i+P_B\cdot B}{N+B}=(1-w)P_i+wP_B,\qquad w=\frac{B}{N+B}
$$

- $P_B$ 是背景概率；
- $B$ 是伪计数的强度；
- 当 $N$ 很小，$w\to 1$，估计值退回背景概率，不会出现奇异性；当 $N$ 很大，$w\to 0$，估计值就是观测频率。

老师对这个 trick 的评价很直接："很简单的 trick，但非常有用，特别是做大数据处理的时候" [【跳转到 34:14】](https://www.bilibili.com/video/BV1jp421m7FW/?t=2054)。

### 4.2 Neff：每个位置到底有几个"独立"的残基

![PSI-BLAST 的完整打分式：伪计数、背景频率与 Nc 都出现在同一个式子里](assets/PSI-BLAST%20迭代搜索与%20profile：MSA%20是怎么造出来的/02129.webp)

真实库里同源序列高度冗余，同一列上出现的 100 条序列可能只代表 5 个独立观察。所以 PSI-BLAST 的式子里带了一个 $N_c$ 参数 [【跳转到 35:29】](https://www.bilibili.com/video/BV1jp421m7FW/?t=2129)：

![Nc 的定义：沿序列统计每个位置上不同残基类型的数目，再对全长取平均](assets/PSI-BLAST%20迭代搜索与%20profile：MSA%20是怎么造出来的/02204.webp)

$$
N_c=\frac{1}{L}\sum_{j=1}^{L} n_j
$$

其中 $n_j$ 是位置 $j$ 上**独立**氨基酸的数目，$L$ 是序列长度 [【跳转到 36:44】](https://www.bilibili.com/video/BV1jp421m7FW/?t=2204)。幻灯片上写得很清楚：$N_c$ 是"mean number of different residue types"，也就是**平均每个位置上有多少种不同的残基**。

这就是"搜索深度"和"有效信息量"的分水岭：**序列条数是深度，$N_c$ 才是有效信息量**。堆一万条几乎相同的序列，$N_c$ 几乎不动；而几十条分布很散的远亲，$N_c$ 可能明显更高。这个量在后面所有基于 MSA 的方法（包括 AlphaFold 的输入）里都会反复出现。

## 五、跑一次 PSI-BLAST：参数、库与输出

![运行 PSI-BLAST 的命令行参数：-b 控制显示条数、-j 控制迭代次数、-h 是 E-value 阈值、-db 指定库](assets/PSI-BLAST%20迭代搜索与%20profile：MSA%20是怎么造出来的/02404.webp)

老师给了一条实际命令 [【跳转到 40:04】](https://www.bilibili.com/video/BV1jp421m7FW/?t=2404)：

```bash
blastp -b 1000 -j 3 -h 0.001 -d db -i protein.fasta -C pssm.chk -Q pssm.txt > blast.out
```

- `-b 1000`：输出时显示最前面的 1000 条序列（这个数可以改）；
- `-j 3`：迭代次数。**不是越多越好**——迭代太多次有时会过拟合，结果反而不如次数少的；经验上大家都用三次 [【跳转到 40:29】](https://www.bilibili.com/video/BV1jp421m7FW/?t=2429)；
- `-h 0.001`：E-value 阈值，即"多大的 E-value 才算有意义"；
- `-d db`：指定数据库。

### 5.1 库的选择：nr 与 SwissProt

![NCBI BLAST 网页上选择数据库：UniProt/Swiss-Prot 小而注释好，nr 大而全](assets/PSI-BLAST%20迭代搜索与%20profile：MSA%20是怎么造出来的/02894.webp)

课上提到库里的序列"大概 8500 万条"，但其中有冗余，所以实际用的是**非冗余库（nr, non-redundant）**，条数会少一些 [【跳转到 41:19】](https://www.bilibili.com/video/BV1jp421m7FW/?t=2479)。

在网页版演示里，老师特意对比了两个选项 [【跳转到 48:14】](https://www.bilibili.com/video/BV1jp421m7FW/?t=2894)：选"很大的库"（所有序列都在里面），还是选 **UniProt/Swiss-Prot**（库比较小，但注释更好）。这是一个典型的取舍：**库越大越可能找到远亲，但也越慢、噪音越多；库越小越快、注释越干净，但可能什么都找不到**。

### 5.2 读输出：先看 database 行，再看 round 和 E-value

![PSI-BLAST 的文本输出：database 行给出库规模与字母总数，每轮结果列出 score 与 E-value](assets/PSI-BLAST%20迭代搜索与%20profile：MSA%20是怎么造出来的/02579.webp)

文本输出长这样 [【跳转到 42:59】](https://www.bilibili.com/video/BV1jp421m7FW/?t=2579)：

- `Database: nr` 一行给出库的规模（示例里是 10,772,401 条序列、3,674,955,464 个字母）——**先看这一行，你就知道这次搜索的"分母"有多大**；
- `Results from round N`：第几轮迭代的结果；
- 每条命中给出 score 与 E-value。示例里最好的命中 E-value 是 $4\times10^{-35}$，"非常靠得住，肯定跟这个 query 同源"；而 E-value 大于 0.01 的命中基本可以不考虑 [【跳转到 43:49】](https://www.bilibili.com/video/BV1jp421m7FW/?t=2629)。

### 5.3 网页版演示：coverage 与 identity 要分开看

![网页版 BLAST 结果表：Max score、Total score、Query cover、E value、Ident 是五个不同的列](assets/PSI-BLAST%20迭代搜索与%20profile：MSA%20是怎么造出来的/02986.webp)

在网页演示里，老师放进去一条 154 个残基的序列，几秒钟就出结果 [【跳转到 49:21】](https://www.bilibili.com/video/BV1jp421m7FW/?t=2961)。结果表里要分清几列：

- **Max score / Total score**：打分；
- **Query cover**：这条命中覆盖了 query 的多大比例（示例里是 100%，说明全长都对上了）；
- **E value**：显著性，示例是 $2\times10^{-107}$；
- **Ident**：identity，示例 99%。

老师看到 99% identity、100% coverage 时的判断是："这个模板跟你的 query 几乎就是同一个东西" [【跳转到 49:46】](https://www.bilibili.com/video/BV1jp421m7FW/?t=2986)。这里要注意：**coverage 和 identity 是两个独立的维度**——一条序列可以 identity 很高但只覆盖 query 的一小段（比如只对上了某个结构域），也可以 coverage 很高但 identity 很低（远亲）。判断"这条命中能不能当模板"，两个都要看。

### 5.4 迭代之后 identity 下降是正常的

![迭代到第三轮的结果：命中的 identity 明显低于第一轮，但找到的是更远的同源序列](assets/PSI-BLAST%20迭代搜索与%20profile：MSA%20是怎么造出来的/03136.webp)

演示里有个现象值得单独说：第一轮 top hit 的 identity 是 99%，但迭代到第二、第三轮时，找到的序列 identity 明显变低了 [【跳转到 52:16】](https://www.bilibili.com/video/BV1jp421m7FW/?t=3136)。这不是出错，而是必然：

- 你不再用 query 序列去搜，而是用它的"亲戚"组成的 profile 去搜 [【跳转到 58:36】](https://www.bilibili.com/video/BV1jp421m7FW/?t=3516)；
- 亲戚的亲戚离你更远，identity 自然更低，但**结构和功能可能仍然相同**；
- 从"找整个家族"的角度看，这恰恰是你想要的——老师用了一个说法：迭代到后面，你反映的是整个 family 的规律，而不是"跟最初那条序列最像的那几条" [【跳转到 60:53】](https://www.bilibili.com/video/BV1jp421m7FW/?t=3653)。

反过来，迭代也不是无脑加次数。老师两次强调"三次"这个经验值 [【跳转到 63:23】](https://www.bilibili.com/video/BV1jp421m7FW/?t=3803)：迭代太多次，profile 会漂移到家族的某个局部，甚至过拟合；所以"在准确的情况下，大家都用三次迭代"。

## 六、这套流程留给下游什么

课堂最后有个学生提问很关键：一个位置一个位置的矩阵（PSSM）是"单点"的，那两个位点**同时变化**怎么办？老师回答 "Great point"，并把这个话题接到了 co-evolution [【跳转到 22:15】](https://www.bilibili.com/video/BV1jp421m7FW/?t=1335)：

- 单个位置的矩阵只能告诉你"这一列保守"；
- 如果两个位点**一起变**（一个变，另一个也跟着变），说明它们在空间上可能相互接触——这就是共变（co-evolution）信号 [【跳转到 23:24】](https://www.bilibili.com/video/BV1jp421m7FW/?t=1404)；
- 有了两两接触，就能约束拓扑结构；这条线后来发展成接触图预测，再往后就是端到端结构预测。

所以一份 MSA 交给下游时，其实同时交出了两类证据：**列内的保守性**（哪些位置不能动）和**列间的相关性**（哪些位置一起动）。前者的质量取决于比对是否正确、$N_c$ 是否够大；后者如何变成接触图、精度怎么评估，属于 1.2.3 的内容。

## 小结

- **MSA 是搜出来的，不是排出来的**：PSI-BLAST 把"搜索 → 比对 → 压成 profile → 再搜索"接成循环，输出才是 MSA。
- **profile 的价值在于位置权重**：单条序列比对时你不知道某位置重不重要；profile 把"这一列偏好什么残基"写进 20×L 的矩阵，于是能往下找到 identity 只有 20% 的远亲。
- **弱同源才是主战场**：近缘同源"傻瓜都能找到"，真正决定方法能力的是能不能捞出那些结构相同、序列已高度分化的成员。
- **伪计数解决小样本**：某一列只有两三条序列时，直接算频率会得到荒谬的概率；用 $(1-w)P_i+wP_B$ 把估计往背景拉，结果才稳定。
- **$N_c$ 是"有效信息量"**：序列条数是深度，$N_c$（平均每个位置有多少种独立残基）才是有效信息量；堆近重复序列不会让 $N_c$ 变大。
- **迭代三次是经验值**：迭代让 profile 反映整个家族，但次数过多会漂移、过拟合；identity 逐轮下降是正常现象。
- **读结果要分开看 coverage 与 identity**：前者说"覆盖了 query 多长"，后者说"对上的部分有多像"，两者共同决定这条命中能不能用。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| query | 你手上那条待检索的序列，结构和功能通常未知 |
| word / HSP | 库里比对的短片段 / 由 word 延伸得到的高打分片段对 |
| E-value | 在这么大的库里，随机出现同样好或更好命中的期望次数；越小越显著 |
| MSA | 多序列比对：每行一条同源序列，每列一个残基位置 |
| profile / PSSM | 把 MSA 压成的 20×L 打分表，每列给出该位置对 20 种残基的偏好分数 |
| 对数几率 | $S(i,j)=\log(Q_{ij}/P_i)$，观测概率与背景概率之比取对数 |
| 伪计数 | 给每个残基的计数加一个背景先验，避免小样本导致的奇异概率 |
| $N_c$（Neff） | 有效序列数：平均每个位置上独立残基类型的数目，衡量 MSA 的真实信息量 |
| coverage | 命中序列覆盖 query 长度的比例 |
| identity | 比对区域内相同残基所占比例 |
| close homolog / 弱同源 | 近缘同源（identity 很高）/ 序列已分化但结构功能仍相同的远亲 |
| co-evolution | 两个位点同步突变的现象，提示空间上可能接触 |