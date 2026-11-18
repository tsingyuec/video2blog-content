# q 和 k 各转各的，内积只剩夹角差：RoPE 旋转矩阵的手推与几何直觉

> 视频来源：[手撕RoPE旋转位置编码推导](https://www.bilibili.com/video/BV1FjrCBdESo/?t=0)（Bilibili · 算法魔法师）
> 本文基于视频演说图文稿整理，配图截自视频。这支视频只有 9 分 47 秒，走的是"高中三角函数 + 一点线性代数"的最小路径：先手算一个 30 度的旋转，再证明 $R(m\theta)^{\top}R(n\theta)=R((n-m)\theta)$，最后用"秒针与时针"解释多尺度频率。它不逐条读论文公式，而是把每一步代数的**几何含义**讲透——所以本文适合作为 2.3.2 那篇论文推导篇的配套直觉篇。

## 本讲要解决的核心问题（SCQA）

**背景**：Transformer 的注意力靠 $q$ 和 $k$ 的点积打分，而点积本身完全不知道顺序。要让它知道顺序，最直接的做法是造一个位置向量，加到词向量上。

**冲突**：加法是有代价的。位置向量一加进去，词向量的模长变了、方向也乱了，你很难分清某个数值里哪一部分是"这个词的意思"、哪一部分是"这个词的位置"。更要命的是点积展开后多出两堆"语义 × 位置"的交叉项，模型得浪费参数去抵消。

**疑问**：有没有一种办法，既告诉模型"这个词在哪"，又完全不改变词向量的模长，还让内积里只留下干净的位置关系？

**回答（中心思想）**：用**旋转**代替加法。第 $m$ 个词的 $q$ 逆时针转 $m\theta$，第 $n$ 个词的 $k$ 逆时针转 $n\theta$，两者各转各的；求注意力分数时先对 $q$ 那一侧取转置——而旋转矩阵的转置恰好是"反着转"，于是两个旋转合成一次 $(n-m)\theta$ 的旋转。**绝对位置在乘法里被自动约掉，只剩夹角差**，模长一点没变。

---

## 一、先看清"往水里兑墨汁"到底损失了什么

![正余弦位置编码的做法：算出一个位置向量，直接加到词向量上](assets/q%20和%20k%20各转各的，内积只剩夹角差：RoPE%20旋转矩阵的手推与几何直觉/00030.webp)

正余弦位置编码（sinusoidal positional encoding）的核心操作只有一句话：为每个位置算一个位置向量，然后**逐元素加到词向量上** [【跳转到 00:20】](https://www.bilibili.com/video/BV1FjrCBdESo/?t=20)。上图就是这个过程：$[0.3, 0.92, -1.23, 0.4, 0.21, -0.9]$ 这样的词向量，加上 $[0.8, 0.21, 0.6, 0.32, 0.98, 0.12]$ 这样的位置向量，得到 $[1.1, 1.13, -0.63, 0.72, 1.19, -0.78]$。

加法确实解决了"位置有无"的问题，但附带两个副作用 [【跳转到 00:30】](https://www.bilibili.com/video/BV1FjrCBdESo/?t=30)：

1. **模长变了。** 每一维都独立相加，向量的总长度自然被拉长或压短；
2. **方向乱了。** 位置向量和语义向量没有共同的坐标系，加完之后的角度既不是原来的语义方向，也没有明确的几何含义。

讲者用了一个很贴切的比方：想标记"这是第几杯水"，就往水里兑不同颜色的墨汁——位置是标上了，但这杯水也被污染了，你再也分不清哪部分是水 [【跳转到 00:54】](https://www.bilibili.com/video/BV1FjrCBdESo/?t=54)。上图里那个 1.13 就是典型：它是 $0.92 + 0.21$，"0.92 的语义"和"0.21 的位置"已经混成一个数，取不出来了。

这正是 RoPE 要解决的问题：既要标出位置，**又不许动模长**，还要让位置关系更纯粹 [【跳转到 01:04】](https://www.bilibili.com/video/BV1FjrCBdESo/?t=64)。

---

## 二、目标可以缩小到一行：让点积里带上相对位置

在动手之前，先把问题简化一下。假设词向量只有两个维度，目标就很明确了：**在算 Attention 点积时，让结果天然包含相对位置信息**。

为什么只盯住点积？因为点积就是在衡量相关度——$q$ 和 $k$ 有多"合得来"，全靠这个数。模型判断"这两个词关系铁不铁"的关键时刻就在这一步，位置关系必须在这里体现出来 [【跳转到 01:25】](https://www.bilibili.com/video/BV1FjrCBdESo/?t=85)。至于 $v$ 和后续的加权求和，都不需要动。

这就把一个大问题砍成了一个小问题：找一个只作用于 $q$、$k$ 的变换，让 $q^{\top}k$ 的结果只跟两个词的相对距离有关。

---

## 三、先手算一遍：把一个箭头逆时针转 30 度

![二维旋转矩阵 R(α) 与单位向量 (1,0)：把它逆时针旋转 30 度](assets/q%20和%20k%20各转各的，内积只剩夹角差：RoPE%20旋转矩阵的手推与几何直觉/00135.webp)

在二维平面上转动一个向量，最标准的工具就是**旋转矩阵**（rotation matrix，一个只负责"转方向"、不负责"改长度"的 $2\times2$ 矩阵）：

$$
R(\alpha) =
\begin{pmatrix}
\cos\alpha & -\sin\alpha\\
\sin\alpha & \cos\alpha
\end{pmatrix}
$$

讲者没有推导这个矩阵，而是带着跑了一遍数值流程。取最简单的单位向量 $(1,0)^{\top}$——长度 1、指向横轴正方向；让它逆时针转 30 度，转完长度仍应是 1 [【跳转到 01:50】](https://www.bilibili.com/video/BV1FjrCBdESo/?t=110)。

![把 30 度代进矩阵再乘 (1,0)：结果是 (√3/2, 1/2)，平方和正好等于 1](assets/q%20和%20k%20各转各的，内积只剩夹角差：RoPE%20旋转矩阵的手推与几何直觉/00160.webp)

代入 $\cos 30^{\circ} = \tfrac{\sqrt{3}}{2}$、$\sin 30^{\circ} = \tfrac{1}{2}$：

$$
\begin{pmatrix}
\dfrac{\sqrt{3}}{2} & -\dfrac{1}{2}\\[6pt]
\dfrac{1}{2} & \dfrac{\sqrt{3}}{2}
\end{pmatrix}
\begin{pmatrix}1\\[4pt] 0\end{pmatrix}
=
\begin{pmatrix}\dfrac{\sqrt{3}}{2}\\[6pt] \dfrac{1}{2}\end{pmatrix}
$$

第一个分量是横轴上的 $\tfrac{\sqrt{3}}{2}$，第二个是竖轴上的 $\tfrac{1}{2}$。用勾股定理验一下：

$$
\left(\frac{\sqrt{3}}{2}\right)^2 + \left(\frac{1}{2}\right)^2 = \frac{3}{4} + \frac{1}{4} = 1
$$

长度果然还是 1 [【跳转到 02:15】](https://www.bilibili.com/video/BV1FjrCBdESo/?t=135)。这一步看起来只是初中几何，但它恰好回答了第一节的痛点：**旋转是全套方案里唯一"只动方向、不动长度"的操作**，所以它不会像加法那样把词向量的模长搞脏。

---

## 四、RoPE 的全部设定：你是第 m 个词，就转 mθ 度

RoPE 的思路就这么简单：如果你是第 $m$ 个字，就把你逆时针旋转 $m$ 个 $\theta$ 角度；如果你（作为 key）是第 $n$ 个词，就逆时针旋转 $n$ 个 $\theta$。这里的 $\theta$ 是角度的基本单位，比如 30 度、20 度 [【跳转到 02:40】](https://www.bilibili.com/video/BV1FjrCBdESo/?t=160)。

!["我"在第 m 位、"你"在第 n 位：q′ = R(mθ)q，k′ = R(nθ)k](assets/q%20和%20k%20各转各的，内积只剩夹角差：RoPE%20旋转矩阵的手推与几何直觉/00185.webp)

于是旋转后的查询和键就是

$$
q' = R(m\theta)\,q, \qquad k' = R(n\theta)\,k
$$

注意这句话里有个容易漏掉的细节：$q$ 和 $k$ 是**两个不同的向量**，它们旋转的角度也不同（$m\theta$ 与 $n\theta$），但两个变换用的是**同一个**旋转矩阵模板，只是角度不同。这就是本文标题说的"各转各的"。

注意力分数就是这两个旋转后向量的内积：

$$
\text{Score} = (q')^{\top}k' = \left(R(m\theta)\,q\right)^{\top}\left(R(n\theta)\,k\right)
$$

接下来只要把这两个旋转"合"起来，看剩下什么。

---

## 五、转置就是反着转：这一步是整段推导的枢纽

![先用转置的乘积法则 (AB)转置 = B转置·A转置，把 Score 写成 q 转置·R(mθ)转置·R(nθ)·k](assets/q%20和%20k%20各转各的，内积只剩夹角差：RoPE%20旋转矩阵的手推与几何直觉/00210.webp)

线性代数里有个基础操作：矩阵乘积的转置等于各自转置后再**反序**相乘，$(AB)^{\top} = B^{\top}A^{\top}$。把它用到 Score 上 [【跳转到 03:05】](https://www.bilibili.com/video/BV1FjrCBdESo/?t=185)：

$$
\text{Score} = q^{\top}R(m\theta)^{\top}R(n\theta)\,k
$$

现在的问题是：$R(m\theta)^{\top}$ 是什么？为了看清楚，令 $\alpha = m\theta$、$\beta = n\theta$ 先简化记号 [【跳转到 03:30】](https://www.bilibili.com/video/BV1FjrCBdESo/?t=210)：

![把 R(α) 转置后调换行列，再用 cos 是偶函数、sin 是奇函数改写，得到 R(−α)](assets/q%20和%20k%20各转各的，内积只剩夹角差：RoPE%20旋转矩阵的手推与几何直觉/00235.webp)

$$
R(\alpha)^{\top} =
\begin{pmatrix}
\cos\alpha & -\sin\alpha\\
\sin\alpha & \cos\alpha
\end{pmatrix}^{\top}
=
\begin{pmatrix}
\cos\alpha & \sin\alpha\\
-\sin\alpha & \cos\alpha
\end{pmatrix}
$$

转置只是把行列互换，真正有意思的是第二步替换。用两条三角函数性质：

- $\cos$ 是**偶函数**：$\cos(-x) = \cos x$，所以 $\cos\alpha$ 可以写成 $\cos(-\alpha)$；
- $\sin$ 是**奇函数**：$\sin(-x) = -\sin x$，所以 $\sin\alpha$ 可以写成 $-\sin(-\alpha)$。

代进去，上面那个矩阵就变成了

$$
\begin{pmatrix}
\cos(-\alpha) & -\sin(-\alpha)\\
\sin(-\alpha) & \cos(-\alpha)
\end{pmatrix} = R(-\alpha)
$$

**这不是新的矩阵，这就是把角度取负的旋转矩阵**。几何含义非常直观：逆时针转 $\alpha$ 的逆操作，就是顺时针转 $\alpha$——而转置恰好就是那个逆操作 [【跳转到 03:55】](https://www.bilibili.com/video/BV1FjrCBdESo/?t=235)。

于是整个 Score 可以读成一句话：**先把 $k$ 转 $n\theta$，再把 $q$ 顺时针转回 $-m\theta$，两次旋转叠加，净效果是转 $(n-m)\theta$**。

---

## 六、矩阵相乘落到和差角公式：结果只剩 $(n-m)\theta$

光靠直觉还不够，讲者又手算了一遍矩阵乘法，让结论在代数上落地 [【跳转到 04:20】](https://www.bilibili.com/video/BV1FjrCBdESo/?t=260)：

![把 R(−mθ)·R(nθ) 展开成四个元素，再用和差角公式合并](assets/q%20和%20k%20各转各的，内积只剩夹角差：RoPE%20旋转矩阵的手推与几何直觉/00288.webp)

$$
R(-\alpha)R(\beta) =
\begin{pmatrix}
\cos\alpha & \sin\alpha\\
-\sin\alpha & \cos\alpha
\end{pmatrix}
\begin{pmatrix}
\cos\beta & -\sin\beta\\
\sin\beta & \cos\beta
\end{pmatrix}
$$

逐元素乘出来是

$$
\begin{pmatrix}
\cos\alpha\cos\beta + \sin\alpha\sin\beta & -\cos\alpha\sin\beta + \sin\alpha\cos\beta\\[4pt]
-\sin\alpha\cos\beta + \cos\alpha\sin\beta & \sin\alpha\sin\beta + \cos\alpha\cos\beta
\end{pmatrix}
$$

看着乱，但对照三角函数的**和差角公式**（两角之和/之差的余弦、正弦展开式）：

$$
\cos(\beta - \alpha) = \cos\beta\cos\alpha + \sin\beta\sin\alpha
$$

$$
\sin(\beta - \alpha) = \sin\beta\cos\alpha - \cos\beta\sin\alpha
$$

四个元素正好一一对上，于是

$$
R(-\alpha)R(\beta) =
\begin{pmatrix}
\cos(\beta-\alpha) & -\sin(\beta-\alpha)\\
\sin(\beta-\alpha) & \cos(\beta-\alpha)
\end{pmatrix}
= R(\beta - \alpha)
$$

讲者特意提了一句：这个和差角公式在他讲正余弦位置编码那一期也出现过，是同一个工具 [【跳转到 04:37】](https://www.bilibili.com/video/BV1FjrCBdESo/?t=277)。把 $\alpha = m\theta$、$\beta = n\theta$ 换回来：

$$
\text{Score} = q^{\top}R\big((n-m)\theta\big)\,k
$$

![最终形式：Score = q 转置·R((n−m)θ)·k，图上标出 (n−m)θ 就是"我"与"你"之间的夹角差](assets/q%20和%20k%20各转各的，内积只剩夹角差：RoPE%20旋转矩阵的手推与几何直觉/00313.webp)

**$m$ 和 $n$ 这两个绝对位置，在乘法的过程中消失了，只剩下 $n-m$** [【跳转到 04:48】](https://www.bilibili.com/video/BV1FjrCBdESo/?t=288)。这就是"用绝对位置的旋转实现相对位置的编码"：

- 不管 $m=11$、$n=15$，还是 $m=100$、$n=104$，相对距离都是 4，中间那个旋转角度就永远是 $4\theta$；
- 句子里同样的两个词，无论整体挪到第几位，注意力分数完全不变。

如果 $q$、$k$ 都是单位向量，这个式子还能再简化成人人都能验算的一句：$\text{Score} = \cos\big((n-m)\theta\big)$。取 $\theta = 30^{\circ}$、相对距离 4，分数就是 $\cos 120^{\circ} = -0.5$；同一个词自己和自己比（$n-m=0$），分数是 $\cos 0 = 1$，最大。位置差就这样被翻译成了夹角差。

---

## 七、二维够用了？不，真实模型要把 4096 维拆成 2048 对

![把 4096 维的词向量拆成 2048 对，每两个数字凑一组](assets/q%20和%20k%20各转各的，内积只剩夹角差：RoPE%20旋转矩阵的手推与几何直觉/00338.webp)

到这儿一定有人要问：向量才两维，实际词向量动不动几千维，怎么办？RoPE 的作者用了一个很朴素的办法，讲者称之为"分置"：假设维度是 4096，就把它拆成 2048 对，每两个数字凑一组，各组**各转各的**，再把这些小旋转矩阵拼起来 [【跳转到 05:13】](https://www.bilibili.com/video/BV1FjrCBdESo/?t=313)。

拼出来的东西在数学上叫**块对角矩阵**（block diagonal matrix）：除了对角线上那些 $2\times2$ 的小旋转矩阵，其它位置全是 0。写成 $4$ 维的样子就是

$$
R_{\Theta,m} =
\begin{pmatrix}
\cos m\theta_1 & -\sin m\theta_1 & 0 & 0\\
\sin m\theta_1 & \cos m\theta_1 & 0 & 0\\
0 & 0 & \cos m\theta_2 & -\sin m\theta_2\\
0 & 0 & \sin m\theta_2 & \cos m\theta_2
\end{pmatrix}
$$

对角线外的 0 意味着"老死不相往来"：第 0、1 维的旋转完全不会干扰第 2、3 维，第 0 组不会影响第 1 组。你自己乘一下就知道了——这正是块对角设计的好处，各组独立，可以并行算 [【跳转到 05:38】](https://www.bilibili.com/video/BV1FjrCBdESo/?t=338)。

---

## 八、转速分级：低维是秒针，高维是时针

拆成多组之后，新的担心来了：角度转一圈 360 度不就重叠了吗？转 16 度和转 370 度指向同一个方向，那两个词向量还怎么靠角度区分距离？

答案藏在 $\theta$ 里。$\theta$ 是每次旋转的角度基本单位，这个单位越大转得越快。RoPE 的作者让**每一组的转速都不相同：组的维度越低，转得越快；维度越高，转得越慢** [【跳转到 06:03】](https://www.bilibili.com/video/BV1FjrCBdESo/?t=363)。

![正余弦位置编码的频率公式被 RoPE 几乎直接照搬：每一组一个频率，配上一张时钟图](assets/q%20和%20k%20各转各的，内积只剩夹角差：RoPE%20旋转矩阵的手推与几何直觉/00413.webp)

最贴切的类比就是钟表：

- **低维像秒针**：位置稍微动一下它就转一大截，对相邻词的微小距离极其敏感，但也最容易"转满一圈"；
- **高维像时针**：位置动了 100 下它可能才转 1 度，转得慢，却能记住很久以前的状态。

而且 RoPE 的频率取法几乎是照抄正余弦位置编码的 $10000^{-2i/d}$ 那一套——只是正余弦编码用它来区分不同维度的**函数周期**，RoPE 用它来区分不同组的**旋转速度** [【跳转到 06:53】](https://www.bilibili.com/video/BV1FjrCBdESo/?t=413)。这也是讲者反复强调"学了正余弦编码再学 RoPE 会很简单"的原因。

至于"重叠"的担心，这时候就能正面回答了：**一个词的位置不是由某一组决定的，而是由这 2048 组一起决定的**。低频组可能已经转了好几圈、看起来重叠了，但高维组还指向不同位置 [【跳转到 07:18】](https://www.bilibili.com/video/BV1FjrCBdESo/?t=438)。讲者打了个比方：虽然秒针又指回 12 点，但我还有一个"3 小时 27 分"在后面兜底。这种多尺度的表达，保证了即使序列很长，整体的旋转状态也不会重复 [【跳转到 07:26】](https://www.bilibili.com/video/BV1FjrCBdESo/?t=446)。

---

## 九、和正余弦编码的正面比较：四项 vs 一项

有人会追问：正余弦编码不也隐含相对位置吗？它的位置向量里确实藏着一个旋转矩阵，能让 $PE(pos)$ 推到 $PE(pos+k)$。那 RoPE 到底好在哪？讲者认为这才是最本质的区别 [【跳转到 07:39】](https://www.bilibili.com/video/BV1FjrCBdESo/?t=459)。

![正余弦编码下 Q 与 K 的写法：Q = W_q(X_m + P_m)，K = W_k(X_n + P_n)](assets/q%20和%20k%20各转各的，内积只剩夹角差：RoPE%20旋转矩阵的手推与几何直觉/00506.webp)

正余弦编码里 $Q = W_q(X_m + P_m)$、$K = W_k(X_n + P_n)$。为了看清结构，假设两个权重矩阵都是单位阵（只看位置怎么进来），Score 展开成四项 [【跳转到 08:01】](https://www.bilibili.com/video/BV1FjrCBdESo/?t=481)：

$$
\text{Score} = X_mX_n^{\top} + X_mP_n^{\top} + P_mX_n^{\top} + P_mP_n^{\top}
$$

![四项的注解：第一项是纯语义，最后一项是纯相对位置，中间两项是"交叉噪声"](assets/q%20和%20k%20各转各的，内积只剩夹角差：RoPE%20旋转矩阵的手推与几何直觉/00531.webp)

- 第一项 $X_mX_n^{\top}$：第 $m$ 个词和第 $n$ 个词的纯语义点积，很好理解；
- 最后一项 $P_mP_n^{\top}$：两个位置之间的纯相对位置，也很好理解；
- 中间两项 $X_mP_n^{\top}$ 和 $P_mX_n^{\top}$：**用语义去乘位置**。

中间那两项就是问题所在。讲者的吐槽很到位：这好比拿你的身高去乘门牌号，算出来的数字毫无意义 [【跳转到 08:26】](https://www.bilibili.com/video/BV1FjrCBdESo/?t=506)。而这就是加法式写法的代价——为了抗干扰，模型必须浪费大量参数去抵消这两项噪声，才能从中提取出一点点位置规律。

RoPE 那边呢？$q$、$k$ 各乘一个旋转矩阵，最后只剩 $q^{\top}R((n-m)\theta)k$ 一项，位置信息被直接注入了向量的角度里，没有交叉项需要抵消，对模型来说相对好学得多 [【跳转到 08:51】](https://www.bilibili.com/video/BV1FjrCBdESo/?t=531)。

一句话总结两者的差别：**加法式位置编码是"掺进去"，RoPE 是"转过去"**。掺进去会改变模长、留下交叉项；转过去只改角度，模长和语义的"长度"都原封不动。

---

## 小结

- 加法式位置编码的代价：模长被改、方向被搅、内积展开多出"语义 × 位置"的交叉噪声。
- RoPE 的设定只有一句：第 $m$ 个词转 $m\theta$，第 $n$ 个词转 $n\theta$，$q$、$k$ 各转各的。
- 整个推导的枢纽是 $R(\alpha)^{\top} = R(-\alpha)$：旋转矩阵的转置就是反方向旋转，靠 $\cos$ 偶、$\sin$ 奇两条性质即可验证。
- 两个旋转矩阵相乘，四个元素正好凑成和差角公式，结果 $R((n-m)\theta)$ 只剩相对角度；单位向量时分数就是 $\cos((n-m)\theta)$。
- 高维向量靠分置：两两一组，拼成块对角矩阵，各组互不干扰。
- 每组转速不同（$10000^{-2i/d}$ 这一套频率）：低频像秒针、高频像时针，多尺度合起来才不重叠。
- 与正余弦编码的正面区别：四项里有两项是无意义的交叉噪声，RoPE 只剩一项。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| 正余弦位置编码 | 用不同频率的 sin/cos 生成位置向量，再逐元素加到词向量上的经典方案 |
| 旋转矩阵 | $2\times2$ 的 $\begin{pmatrix}\cos\alpha & -\sin\alpha\\ \sin\alpha & \cos\alpha\end{pmatrix}$，几何上表示逆时针转 $\alpha$ 角 |
| 转置 | 把矩阵行列互换；对旋转矩阵而言，转置等于反向旋转，即 $R(\alpha)^{\top}=R(-\alpha)$ |
| 偶函数 / 奇函数 | $\cos(-x)=\cos x$（偶）、$\sin(-x)=-\sin x$（奇），是"转置变反方向"的关键 |
| 和差角公式 | $\cos(\beta-\alpha)=\cos\beta\cos\alpha+\sin\beta\sin\alpha$ 等，用于把两个旋转合并成一个 |
| 块对角矩阵 | 对角线外全为 0 的矩阵；这里每个对角块是一个独立的二维旋转 |
| 分置 | 把 $d$ 维词向量两两分组、每组独立旋转的做法 |
| 交叉噪声 | 加法式编码展开后出现的"语义 × 位置"项，对注意力分数没有实际意义 |
