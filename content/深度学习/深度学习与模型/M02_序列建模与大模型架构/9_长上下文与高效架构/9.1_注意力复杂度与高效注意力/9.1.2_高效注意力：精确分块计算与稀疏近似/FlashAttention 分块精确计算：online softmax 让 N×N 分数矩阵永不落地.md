# FlashAttention 分块精确计算：online softmax 让 N×N 分数矩阵永不落地

> 视频来源：[第 1 课 FlashAttention v1：从完整矩阵到分块精确计算](https://www.bilibili.com/video/BV1Dje66pEZY/)（B 站 · 想躺平的程序员 · 时长约 42 分钟）
> 本文基于视频演说图文稿整理，配图截自视频。这支视频的讲法是**逐帧手算**：先用一个 $4\times 2$ 的小矩阵把标准 attention 的每一步算成具体分数，再把同一组数字搬进分块流程，让你亲眼看到"分块直接算 softmax 会错"，以及 online softmax 的修正因子怎样把错的结果掰回来。

## 本讲要解决的核心问题（SCQA）

**背景**：标准 attention 只有三步——算分数 $S=QK^\top/\sqrt{d}$、沿 Key 方向归一化 $P=\mathrm{softmax}(S)$、加权求和 $O=PV$。三步都是普通矩阵运算，数学上没有任何问题。

**冲突**：问题出在"中间结果要落地"。$S$、$E=\exp(S-m)$、$P$ 都是 $N\times N$ 的矩阵，而 GPU 的片上高速存储（SRAM）装不下它们，只能写回全局显存（HBM）再读回来。$N=4096$、$d=128$ 时，输入输出各只有 2 MiB，中间搬运却要 512 MiB。

**疑问**：能不能把大矩阵切成片上装得下的小块，边算边丢？可是 softmax 的分母要看到**整行**分数，只看一块算出来的概率是错的——分块之后怎么还能得到和标准 attention 完全一样的结果？

**回答（中心思想）**：能，而且结果严格等价。把输出改写成"分子 / 分母"两个**可累加**的量，再用 running max 与重缩放因子 $\alpha,\beta$ 把各块的统计量递推合并（online softmax），$N\times N$ 矩阵就再也不需要落地。**FlashAttention 改变的是计算过程与访存顺序，不改变模型假设**——它算的还是那个 softmax attention，只是换了一条路走。这也正是本小节要划的那条线：精确分块属于"改计算"，稀疏/线性近似才属于"改假设"。

---

## 一、标准 attention 的代价不在算术，在搬运

![标准 attention 的三步公式与符号表：S 是 N_q×N_k 的匹配分数，P 沿 Key 方向归一化，O 是 Value 加权和](assets/FlashAttention%20分块精确计算：online%20softmax%20让%20N×N%20分数矩阵永不落地/00079.webp)

先把记号钉死。$Q\in\mathbb{R}^{N_q\times d}$、$K\in\mathbb{R}^{N_k\times d}$、$V\in\mathbb{R}^{N_k\times d}$，这里的 $d$ 是**单个 head** 的向量维度，不是整个模型的 hidden size；输出 $O$ 也还没有做多头拼接和输出投影。

$$
S=\frac{QK^\top}{\sqrt{d}}\in\mathbb{R}^{N_q\times N_k},\qquad
P=\mathrm{softmax}_{\text{row}}(S)\in\mathbb{R}^{N_q\times N_k},\qquad
O=PV\in\mathbb{R}^{N_q\times d}
$$

三步各管一件事：**匹配**（每个 Query 与每个 Key 做点积，得到 $N_q\times N_k$ 个分数）、**归一化**（每行减最大值、取指数、除以行和，使每行概率和为 1）、**加权**（每行概率乘以对应 Value 再求和）。

### 1.1 一组能手工核对的小数字

![Q/K/V 的数值示例：四行、宽度 d=2，Q 用 √2、K 用 ln2 与 ln4，目的是让分数恰好落在 0、ln2、ln4 上](assets/FlashAttention%20分块精确计算：online%20softmax%20让%20N×N%20分数矩阵永不落地/00179.webp)

讲者特意构造了一组"好算"的数，四行、宽度 $d=2$，缩放系数 $1/\sqrt{d}=1/\sqrt{2}$：

$$
Q=\begin{bmatrix}\sqrt2 & 0\\ 0 & \sqrt2\\ \sqrt2 & \sqrt2\\ \sqrt2 & -\sqrt2\end{bmatrix},\quad
K=\begin{bmatrix}0&0\\ \ln2&0\\ \ln4&\ln2\\ 0&\ln4\end{bmatrix},\quad
V=\begin{bmatrix}1&0\\0&1\\1&1\\2&0\end{bmatrix}
$$

$Q$ 里放 $\sqrt2$、$K$ 里放 $\ln2$ 和 $\ln4$，是为了让点积再乘 $1/\sqrt2$ 之后正好得到 $0,\ln2,\ln4$ 这样的整数倍对数，取指数后变成 $1,\frac12,\frac14$ 这类分数，手算得动、也方便核对 [【跳转到 02:54】](https://www.bilibili.com/video/BV1Dje66pEZY/?t=174)。

### 1.2 第一步：算分数矩阵 S

![S 的第一行：√2×0+0×0 除以 √2 得 0，√2×ln2 除以 √2 得 ln2，依次得到 [0, ln2, ln4, 0]](assets/FlashAttention 分块精确计算：online softmax 让 N×N 分数矩阵永不落地/00229.webp)

以第一条 Query $q=[\sqrt2,0]$ 为例，它与四个 Key 的点积再乘 $1/\sqrt2$：

$$
S[0,:]=\left[0,\ \ln2,\ \ln4,\ 0\right]
$$

把四条 Query 都算完，得到完整的 $4\times4$ 分数矩阵：

$$
S=\begin{bmatrix}0&\ln2&\ln4&0\\ 0&\ln2&\ln4&0\\ 0&\ln2&\ln8&\ln4\\ 0&\ln2&-\ln2&-\ln4\end{bmatrix}
$$

注意这一步是**纯矩阵乘法**，每个分数只依赖对应的 Query 和 Key，天然可以分块——后面会看到，问题不在这一步。

### 1.3 第二步：数值稳定的 softmax

![E 与分母 l：每行减去行最大值后取指数，第一行得到 1/4、1/2、1、1/4，行和为 2](assets/FlashAttention%20分块精确计算：online%20softmax%20让%20N×N%20分数矩阵永不落地/00385.webp)

直接算 $e^{s}$ 会溢出（$s$ 稍大就超出浮点上界），所以用"减最大值"的稳定版本：

$$
m_i=\max_j S[i,j],\qquad E[i,j]=e^{S[i,j]-m_i},\qquad l_i=\sum_j E[i,j],\qquad P[i,j]=\frac{E[i,j]}{l_i}
$$

本例中行最大值向量是 $m=[\ln4,\ln4,\ln8,\ln2]$，指数矩阵 $E$ 的第一行是 $[\frac14,\frac12,1,\frac14]$，行和 $l_0=2$；四行的分母分别是 $2,\ 2,\ \frac{15}{8},\ \frac{21}{8}$ [【跳转到 04:17】](https://www.bilibili.com/video/BV1Dje66pEZY/?t=257)。

### 1.4 第三步：加权求和得到 O

![第四步：回读 P 与 V，把概率乘以 Value 再沿 Key 方向求和，第一行得到 [7/8, 6/8]](assets/FlashAttention 分块精确计算：online softmax 让 N×N 分数矩阵永不落地/00440.webp)

$$
O[0,:]=\frac18[1,0]+\frac28[0,1]+\frac48[1,1]+\frac18[2,0]=\left[\frac78,\ \frac68\right]
$$

到这里，标准 attention 的账算完了。**每一步的输入都要从 HBM 读到片上，结果再写回 HBM**——这是理解 FlashAttention 的全部前提 [【跳转到 07:32】](https://www.bilibili.com/video/BV1Dje66pEZY/?t=452)。

### 1.5 把搬运量算成数字

![显存与访存账本：单个 Q/K/V/O 只有 2 MiB，单个 S/E/P 却有 64 MiB，S+E+P 同时存在占 192 MiB，逻辑访问合计 512 MiB](assets/FlashAttention%20分块精确计算：online%20softmax%20让%20N×N%20分数矩阵永不落地/00532.webp)

把上面的小例子放大到真实尺寸：$N_q=N_k=N=4096$、$d=128$、FP32（每元素 4 字节）。

| 对象 / 成本 | 计算 | 结果 |
| --- | --- | --- |
| 单个 Q、K、V 或 O | $4096\times128\times4$ 字节 | 2 MiB |
| 单个 S、E 或 P | $4096^2\times4$ 字节 | 64 MiB |
| S、E、P 同时存在 | $3\times64$ MiB | 192 MiB |
| S：一次写入、两次读取 | $3\times64$ MiB | 192 MiB |
| E：一次写入、两次读取 | $3\times64$ MiB | 192 MiB |
| P：一次写入、一次读取 | $2\times64$ MiB | 128 MiB |
| S/E/P 中间矩阵的逻辑访问合计 | $8\times64$ MiB | 512 MiB |
| $QK^\top$ 与 $PV$ 两次矩阵乘法 | $4\times4096^2\times128$，乘加计 2 FLOPs | 约 8.59 GFLOPs |

**输入输出只有 2 MiB，中间搬运 512 MiB**——差了 256 倍。瓶颈不在算力，在 HBM 带宽 [【跳转到 08:52】](https://www.bilibili.com/video/BV1Dje66pEZY/?t=532)。

---

## 二、分块：把大矩阵切成片上装得下的小块

### 2.1 只能沿序列方向切，不能切向量内部

直观的解法是分块：既然中间结果太大，就把它切成小块，让每一块都在片上算完再丢。切法有讲究——**每个 Query/Key/Value 向量必须保持完整**，因为点积要求两个向量维度对齐，所以只能沿"行"（序列方向）切，不能把一个 128 维向量劈成两半。

讲者的例子：取 $Q$ 的第一行，$K$ 和 $V$ 各取前两行，得到一个小矩阵，完全可以在片上走完 $S\to E\to P\to O$ 的全流程；然后再取 $K,V$ 的后两行，用同一条 Query 再算一遍 [【跳转到 11:07】](https://www.bilibili.com/video/BV1Dje66pEZY/?t=667)。

### 2.2 分块之后，softmax 立刻算错

问题来了。第一行分数是 $[0,\ln2,\ln4,0]$，分成两块：$A=[0,\ln2]$、$B=[\ln4,0]$。

- 只对 $A$ 做 softmax：$m_A=\ln2$，$E_A=[\frac12,1]$，$l_A=\frac32$，于是 $P_A=[\frac13,\frac23]$。
- 但整行的真实概率是 $[\frac18,\frac28,\frac48,\frac18]$，前两位是 $[\frac18,\frac28]$。

$\frac13\ne\frac18$。**"每块分别做 softmax 再拼起来"会改变结果**，因为 softmax 的分母是整行的指数和，而当前块根本不知道后面还有没有更大的分数 [【跳转到 15:17】](https://www.bilibili.com/video/BV1Dje66pEZY/?t=917)。

如果为了知道分母而把分数存回 HBM、等所有 Key 到齐再归一化，那就退回了原来的中间矩阵读写——分块白做了。所以必须解决一个矛盾：**在还不知道整行分母的时候，先把当前块的贡献算出来并释放掉。**

---

## 三、把 softmax 拆成"可累加的分子与分母"

![分子与分母的累积：把公分母提到求和号外面，O 变成"指数加权 Value 之和"除以"指数之和"，两项都不需要提前知道后续 Key](assets/FlashAttention%20分块精确计算：online%20softmax%20让%20N×N%20分数矩阵永不落地/01260.webp)

关键一步是代数变形：把 softmax 的分母从"每个概率各自除"改成"整体最后除" [【跳转到 20:35】](https://www.bilibili.com/video/BV1Dje66pEZY/?t=1235)。

$$
o=\sum_j \frac{e^{s_j-m}}{\sum_k e^{s_k-m}}v_j=\frac{\sum_j e^{s_j-m}v_j}{\sum_j e^{s_j-m}}
$$

这样，**分母（指数和）与分子（指数加权 Value 之和）都是可累加的量**，当前块算完就能把分数丢掉，只留下两个累计量。对每条 Query，需要保存的"状态"是：一个标量分母、一个 $d$ 维向量分子，再加一个当前最大值。

### 3.1 三个统计量：m、l、u

![历史状态与当前块：m_A 是已处理 Key 的最大分数，l_A 是该基准下的指数和，u_A 是同一基准下的 Value 加权分子](assets/FlashAttention%20分块精确计算：online%20softmax%20让%20N×N%20分数矩阵永不落地/01443.webp)

固定一条 Query，用 $A$ 表示已经处理过的 Key 集合，$B$ 表示当前新块：

$$
m_A=\max_{j\in A}s_j,\qquad
l_A=\sum_{j\in A}e^{s_j-m_A},\qquad
u_A=\sum_{j\in A}e^{s_j-m_A}v_j
$$

$m_A$ 是当前最大值，$l_A$ 是**该基准下**的指数和，$u_A$ 是同一基准下的加权分子。注意"同一基准"这四个字：一旦最大值变了，之前算的 $l_A$、$u_A$ 全部要按新基准重新缩放。

### 3.2 递推：换基准，再合并

![加权分子的递推：u_new = α·u_A + β·u_B，其中 α = e^{m_A-m_new}、β = e^{m_B-m_new}，修正因子对块内所有位置相同，可以从向量和中提出来](assets/FlashAttention%20分块精确计算：online%20softmax%20让%20N×N%20分数矩阵永不落地/01770.webp)

新块 $B$ 也能算出自己的 $(m_B,l_B,u_B)$。合并时先取新的全局最大值，再把两块的统计量搬到同一基准上：

$$
m_{\text{new}}=\max(m_A,m_B),\qquad
\alpha=e^{m_A-m_{\text{new}}},\qquad
\beta=e^{m_B-m_{\text{new}}}
$$

$$
l_{\text{new}}=\alpha\,l_A+\beta\,l_B,\qquad
u_{\text{new}}=\alpha\,u_A+\beta\,u_B,\qquad
O_{\text{new}}=\frac{u_{\text{new}}}{l_{\text{new}}}
$$

为什么可以这样提出来？因为 $\alpha,\beta$ 对**块内所有位置都相同**（它们只跟最大值有关），所以能直接从向量和里提到外面。这就是 online softmax 的核心：**旧分母先换基准，再加上同一基准下的新块分母**，只需当前块，不需要重新扫描 $A$ [【跳转到 29:05】](https://www.bilibili.com/video/BV1Dje66pEZY/?t=1745)。

### 3.3 用同一组数字验证一遍

回到第一行 $[0,\ln2,\ln4,0]$，分成 $A=[0,\ln2]$、$B=[\ln4,0]$：

| 步骤 | 计算 | 结果 |
| --- | --- | --- |
| 块 A | $m_A=\ln2$，$E_A=[\frac12,1]$ | $l_A=\frac32$，$u_A=(\frac12,1)$ |
| 块 B | $m_B=\ln4$，$E_B=[1,\frac14]$ | $l_B=\frac54$，$u_B=(\frac32,1)$ |
| 新基准 | $m_{\text{new}}=\max(\ln2,\ln4)=\ln4$ | $\alpha=\frac12$，$\beta=1$ |
| 合并分母 | $\frac12\cdot\frac32+1\cdot\frac54$ | $l_{\text{new}}=2$ |
| 合并分子 | $\frac12(\frac12,1)+1(\frac32,1)$ | $u_{\text{new}}=(\frac74,\frac32)$ |
| 输出 | $u_{\text{new}}/l_{\text{new}}$ | $O=(\frac78,\frac34)$ |

$\frac78$ 和 $\frac34$ 正是第 1.4 节用完整矩阵算出的 $O[0,:]=[\frac78,\frac68]$。**分块算两遍，结果与一次算完完全一致** [【跳转到 34:14】](https://www.bilibili.com/video/BV1Dje66pEZY/?t=2054)。

### 3.4 多行版本：行与行之间不合并统计量

![两条 Query 的状态对照：Key 0,1 时第一行 m=ln2、l=3/2、O=[1/3,2/3]；加入 Key 2,3 后 m 变为 ln4、l=2、O=[7/8,3/4]](assets/FlashAttention 分块精确计算：online softmax 让 N×N 分数矩阵永不落地/02237.webp)

上面的推导是单条 Query。推广到多条 Query 时，$m$、$l$ 变成**每条 Query 一份**的向量，$u$ 变成 $N_q\times d$ 的矩阵，而**行与行之间不共享、不合并统计量**——每条 Query 有自己的最大值和分母。

上表还暴露了 FA1 的一个代价：同一个 KV 块，第一行和第二行的最大值可能不同（$\ln2$ 与 $0$），所以两行要各自修正。加入 Key 2、3 后，两行的最大值都变成 $\ln4$，历史修正因子分别是 $\frac12$ 和 $\frac14$，各行分别修正。**同一个矩阵块里的所有行，也必须分别修正**。

---

## 四、代价转移：从 512 MiB 到 198 MiB

![分块前后的访存对比：显式 S/E/P 基线约 520 MiB，FA1 用 32 个 KV 块降到 198 MiB](assets/FlashAttention%20分块精确计算：online%20softmax%20让%20N×N%20分数矩阵永不落地/02413.webp)

完整 $S/E/P$ 的读写消失了，但 FA1 每处理一个 KV 块都要重新访问 $Q$ 和行状态。仍用 $N=4096$、$d=128$、FP32，取块大小 $B_r=16$、$B_c=128$，一共 $4096/128=32$ 个 KV 块：

| 对象的逻辑访问 | 显式 S/E/P 基线 | FA1：32 个 KV 块 |
| --- | --- | --- |
| K/V | 4 MiB | 4 MiB |
| Q | 2 MiB | $32\times2=64$ MiB |
| O | 写出 2 MiB | $32\times(2+2)=128$ MiB |
| m/l | 各写读一次，共 0.0625 MiB | $32\times0.0625=2$ MiB |
| S/E/P | 512 MiB | 0 |
| 合计 | 520.0625 MiB | 198 MiB |

**用 Q 和小型行状态的重复访问，替代三个完整中间矩阵的读写**——这就是 FA1 的取舍。逻辑访问从约 520 MiB 降到 198 MiB，192 MiB 的 $S/E/P$ 存储被片上工作区和行状态取代 [【跳转到 40:13】](https://www.bilibili.com/video/BV1Dje66pEZY/?t=2413)。

几点必须说清楚：

- **算术复杂度没变**。$QK^\top$ 与 $PV$ 仍是 $O(N^2d)$，FLOPs 一分没省；省的是显存与 HBM 流量。所以 FlashAttention 属于"**改计算过程**"，不是"改模型假设"。
- **块大小是权衡**。切太细，重复访问 $Q$ 和行状态的次数多；切太粗，片上装不下。讲者的说法是"不能划分太细也不能太粗"，实际取值由 SRAM 容量与寄存器/共享内存分配决定 [【跳转到 40:38】](https://www.bilibili.com/video/BV1Dje66pEZY/?t=2438)。
- **持久化内存仍在**。$O$ 占 $N_qd$ 个元素，$m$、$l$ 各占 $N_q$ 个，随 Query 数量线性增长；当前块的工作区由块大小决定。所以是 $O(N)$ 而不是零。

---

## 五、这条分界线：改计算，还是改假设

把这一讲放回本小节的主题里，它给出的是一条清晰的分界：

| 路线 | 代表 | 数学结果 | 改变了什么 |
| --- | --- | --- | --- |
| 精确分块 + online softmax | FlashAttention | 与标准 attention 等价（仅浮点误差） | 只改计算顺序与访存，**模型假设不变** |
| 改变可见性 | 局部窗口、随机/全局 token、block-sparse（BigBird 类） | 只对部分 $(i,j)$ 求和 | 改变"谁能看见谁"，**改模型假设** |
| 改变函数形式 | 线性注意力、低秩近似、压缩记忆（Infini-attention 类） | 用 $d\times d$ 摘要替代 $N\times N$ 分数 | 改变"注意力算什么"，**改模型假设** |

判据很简单：**把 $N$ 改成 2 倍，结果是否逐元素不变？** 不变的是精确分块；变了的是稀疏与近似。前者换来的是同样的结果跑得更快、更省显存；后者换来的是复杂度降阶，代价是表达力与精度。

窗口类方法的具体机制（滑动窗口、rolling buffer KV cache）已在 [§8.3.1 滑动窗口注意力与滚动缓存](../../../README.md#m02-8-3-1) 讲过，这里不再重复；KV 压缩（MQA/GQA、MLA）见 [§7.1](../../../README.md#m02-7-1) 与 [§8.3.2](../../../README.md#m02-8-3-2)。本篇只负责把"精确"这一侧钉死。

---

## 小结

- 标准 attention 的瓶颈不是 FLOPs，而是 $S$、$E$、$P$ 三个 $N\times N$ 中间矩阵必须写回 HBM 再读回来：$N=4096$、$d=128$ 时输入输出各 2 MiB，中间搬运 512 MiB。
- 分块只能沿序列方向切，每个向量必须完整；但"每块各自 softmax 再拼"是错的——$[\frac13,\frac23]$ 不等于 $[\frac18,\frac28]$。
- 解法是把输出改写成"指数加权 Value 之和 ÷ 指数之和"，让分母和分子都变成可累加量。
- 换基准靠两个修正因子：$m_{\text{new}}=\max(m_A,m_B)$、$\alpha=e^{m_A-m_{\text{new}}}$、$\beta=e^{m_B-m_{\text{new}}}$，于是 $l_{\text{new}}=\alpha l_A+\beta l_B$、$u_{\text{new}}=\alpha u_A+\beta u_B$。
- 修正因子对块内所有位置相同，所以能从向量和里提出来；行与行之间不合并统计量，每条 Query 各存一份 $m$、$l$。
- 结果与标准 attention 完全等价（$4\times2$ 例子两次都得到 $[\frac78,\frac34]$），HBM 逻辑访问从 520 MiB 降到 198 MiB。
- 算术复杂度仍是 $O(N^2d)$，显存从 $O(N^2)$ 降到 $O(N)$。**它改的是计算过程，不是模型假设**——这是与稀疏/线性近似的根本区别。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| HBM | GPU 的全局显存，容量大但带宽有限，片上 SRAM 装不下的中间结果都得先落到这里 |
| SRAM / 片上存储 | 靠近计算单元的高速小容量存储，FlashAttention 的分块必须装得进它 |
| 分块（tiling） | 把 $N\times N$ 的大矩阵沿序列方向切成小块，在片上算完一块就释放一块 |
| online softmax | 边遍历边维护 running max 与指数和，用重缩放因子把新块并入旧统计量的 softmax 算法 |
| running max $m$ | 当前已处理 Key 的最大分数，作为指数运算的数值稳定基准 |
| 修正因子 $\alpha,\beta$ | $e^{m_{\text{旧}}-m_{\text{新}}}$，把旧块的指数和与分子搬到新基准上 |
| 精确（exact）注意力 | 与标准 softmax attention 数学等价，只改变计算顺序与访存，不改变可见性或函数形式 |
| IO 感知（IO-aware） | 以 HBM 读写次数而非 FLOPs 为主要优化目标的算法设计视角 |