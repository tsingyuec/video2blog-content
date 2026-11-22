# Jacobian 矩阵：向量值函数的局部导数表与逐层维度传递

> 视频来源：[The Jacobian Matrix - Explained](https://www.youtube.com/watch?v=6FesMicc844)（YouTube · DataMListic）｜时长约 5 分钟
> 这是一支概念短片：从一元导数、偏导数一路推到 Jacobian 矩阵，再用一个三层小网络说明"每层的 Jacobian 形状由输入输出个数决定，整条链的敏感度是它们的乘积"。本文按本节目标整理，重点在**形状与相乘顺序**，具体求导算例见同节另一篇多元链式法则。

## 本讲要解决的核心问题（SCQA）

**背景**：一元函数 $f(x)=x^2$ 的导数是 $2x$，一个输入、一个输出、一个数，形状问题根本不存在。

**冲突**：一旦函数有多个输入，导数就变成一组偏导数；如果函数还有多个输出，"每个输出对每个输入的变化率"就有 $m\times n$ 个。把它们散着写既记不住，也没法代进复合函数的链式法则。

**疑问**：多个函数、多个变量时，这些偏导数应该怎么组织？组织成矩阵之后，复合函数的求导为什么变成矩阵相乘？形状怎么对上？

**回答（中心思想）**：**把"第 $i$ 个输出对第 $j$ 个输入"的偏导数放在第 $i$ 行第 $j$ 列，就得到 Jacobian 矩阵 $J_f$，它的形状是"输出个数 × 输入个数"。** 这个矩阵是向量值函数在某点的局部线性近似；复合函数 $g\circ f$ 的 Jacobian 就是两个 Jacobian 的乘积，而乘积能成立，正是因为前一个的列数（输入个数）等于后一个的行数（输出个数）。

---

## 一、从一元导数到偏导数：输入变多，一个数变成一组数

### 1.1 一元情形：导数是一个数

对 $f(x)=x^2$ 求导得 $\dfrac{df}{dx}=2x$ [【跳转到 00:00】](https://www.youtube.com/watch?v=6FesMicc844&t=0)。它回答的问题是："输入 $x$ 变一点点，输出变多少？"因为输入只有一个、输出也只有一个，答案就是一个数。

![一元函数是整条推论的起点：一个输入、一个输出，导数就是一个数，还没有"形状"可言](assets/Jacobian%20矩阵：向量值函数的局部导数表与逐层维度传递/00025.webp)

### 1.2 多变量情形：每个输入各给一个偏导数

如果函数接受多个输入，例如 $f(x_1,x_2)$，就要问"只让 $x_1$ 变、$x_2$ 不动"和"只让 $x_2$ 变、$x_1$ 不动"两个问题，答案分别是 $\dfrac{\partial f}{\partial x_1}$ 和 $\dfrac{\partial f}{\partial x_2}$ [【跳转到 00:25】](https://www.youtube.com/watch?v=6FesMicc844&t=25)。

![多变量函数：输入从 1 个变成 2 个，导数从 1 个数变成 2 个偏导数，但输出仍然只有 1 个](assets/Jacobian%20矩阵：向量值函数的局部导数表与逐层维度传递/00050.webp)

此时输出还是标量，所以这组偏导数可以排成一个**行向量**（梯度）。注意"输入个数"决定了这组数有几个分量——这是后面形状规则的第一个半边。

### 1.3 真正的跃迁：输出也变成多个

Jacobian 要处理的是更一般的情形 [【跳转到 00:50】](https://www.youtube.com/watch?v=6FesMicc844&t=50)：**多个函数，每个都依赖多个变量**。也就是向量进、向量出。

视频给的例子是一个从二维输入到二维输出的函数 [【跳转到 01:15】](https://www.youtube.com/watch?v=6FesMicc844&t=75)：

$$
\mathbf{f}(\mathbf{x})=
\begin{pmatrix} f_1(x_1,x_2)\\ f_2(x_1,x_2)\end{pmatrix}
=
\begin{pmatrix} x_1^2+x_2\\ x_1+x_2^2\end{pmatrix}
$$

这里 $f_1$、$f_2$ 是两个**输出分量**，$x_1$、$x_2$ 是两个**输入分量**。要完整描述局部变化，必须回答"每一个输出对每一个输入"如何变化。

![多个函数、多个变量：输入是二维向量，输出也是二维向量，两个分量各自依赖两个输入](assets/Jacobian%20矩阵：向量值函数的局部导数表与逐层维度传递/00100.webp)

## 二、Jacobian 就是"输出 × 输入"的偏导数表

### 2.1 数一数有几个偏导数

两个输出、两个输入，组合起来正好四个偏导数 [【跳转到 01:40】](https://www.youtube.com/watch?v=6FesMicc844&t=100)：

- $f_1$ 对 $x_1$、$f_1$ 对 $x_2$；
- $f_2$ 对 $x_1$、$f_2$ 对 $x_2$。

把它们按"行是输出、列是输入"摆进表格，就得到 $2\times 2$ 的 Jacobian 矩阵 [【跳转到 02:05】](https://www.youtube.com/watch?v=6FesMicc844&t=125)：

$$
J_f=
\begin{pmatrix}
\dfrac{\partial f_1}{\partial x_1} & \dfrac{\partial f_1}{\partial x_2}\\
\dfrac{\partial f_2}{\partial x_1} & \dfrac{\partial f_2}{\partial x_2}
\end{pmatrix}
=
\begin{pmatrix}
2x_1 & 1\\
1 & 2x_2
\end{pmatrix}
$$

![Jacobian 矩阵：第 i 行是第 i 个输出对所有输入的偏导，第 j 列是第 j 个输入对所有输出的偏导；这个例子算出来是 2×2](assets/Jacobian%20矩阵：向量值函数的局部导数表与逐层维度传递/00125.webp)

### 2.2 形状规则：行数 = 输出个数，列数 = 输入个数

把上面的例子抽象一下，就得到本节最该记住的一条：

$$
\mathbf{f}:\mathbb{R}^n\to\mathbb{R}^m
\quad\Longrightarrow\quad
J_f\in\mathbb{R}^{m\times n}
$$

- **行数 $m$**：输出向量有几个分量，就有几行。
- **列数 $n$**：输入向量有几个分量，就有几列。
- 元素 $[J_f]_{ij}=\dfrac{\partial f_i}{\partial x_j}$：第 $i$ 个输出对第 $j$ 个输入的偏导。

用这个规则回看前面的情形：标量函数 $f(x_1,x_2)$ 是 $m=1,n=2$，Jacobian 是 $1\times 2$ 的行向量，也就是梯度；一元函数是 $m=1,n=1$，退化成 $1\times 1$ 的一个数。**梯度、导数都是 Jacobian 的特例。**

### 2.3 为什么它叫"局部线性近似"

视频把 Jacobian 描述为"包含向量值函数如何变化的全部局部线性近似信息" [【跳转到 02:30】](https://www.youtube.com/watch?v=6FesMicc844&t=150)。意思是：在一点附近，一个非线性函数可以近似成一个线性映射

$$
\mathbf{f}(\mathbf{x}+\Delta\mathbf{x})\approx \mathbf{f}(\mathbf{x})+J_f\,\Delta\mathbf{x}
$$

右边的 $J_f\Delta\mathbf{x}$ 是矩阵乘向量：$m\times n$ 乘 $n\times 1$，得到 $m\times 1$，正好是输出的增量。**形状在这里第一次发挥作用**——如果 $J_f$ 的列数不等于 $\Delta\mathbf{x}$ 的长度，这个乘法根本写不出来。

## 三、网络里的维度链条：每层一个 Jacobian，整条链是乘积

### 3.1 一个三层小网络

视频用一个极简网络做例子 [【跳转到 02:55】](https://www.youtube.com/watch?v=6FesMicc844&t=175)：输入一个标量 $x$，第一层产生两个隐藏激活 $a_1,a_2$，第二层产生 $b_1,b_2$，最后合成一个输出 $p$。

$$
x\;\longrightarrow\;(a_1,a_2)\;\longrightarrow\;(b_1,b_2)\;\longrightarrow\;p
$$

每一层都是"向量进、向量出"，所以每一层都有自己的 Jacobian [【跳转到 03:20】](https://www.youtube.com/watch?v=6FesMicc844&t=200)：

| 层 | 映射 | 输入个数 | 输出个数 | Jacobian 形状 |
| --- | --- | --- | --- | --- |
| 第 1 层 | $x\to(a_1,a_2)$ | 1 | 2 | $2\times 1$ |
| 第 2 层 | $(a_1,a_2)\to(b_1,b_2)$ | 2 | 2 | $2\times 2$ |
| 第 3 层 | $(b_1,b_2)\to p$ | 2 | 1 | $1\times 2$ |

![三层网络与三个 Jacobian：J1 是 2×1、J2 是 2×2、J3 是 1×2，形状完全由每层的输入、输出个数决定](assets/Jacobian%20矩阵：向量值函数的局部导数表与逐层维度传递/00250.webp)

### 3.2 相乘顺序就是数据流动的反向

视频的结论是：输出对输入的总体敏感度 $\dfrac{dp}{dx}$，等于把这些 Jacobian "按顺序相乘" [【跳转到 03:45】](https://www.youtube.com/watch?v=6FesMicc844&t=225)。

这里的"顺序"要按形状来定，因为矩阵乘法不满足交换律。$p$ 是标量、$x$ 是标量，最终结果必须是 $1\times 1$；只有一种排法能让相邻的维度接上：

$$
\underbrace{J_3}_{1\times 2}\;
\underbrace{J_2}_{2\times 2}\;
\underbrace{J_1}_{2\times 1}
\;\Longrightarrow\;
1\times 1
$$

逐项检查：$(1\times 2)(2\times 2)=(1\times 2)$，再乘 $(2\times 1)$ 得 $(1\times 1)$。**相邻两个矩阵的"内维"必须相等**——前一个的列数（该层的输入个数）等于后一个的行数（下一层的输出个数）。这不是巧合：第 2 层的输入就是第 1 层的输出，维度天然对齐。

### 3.3 这条链条和反向传播的关系

把上面的例子一般化：一个 $L$ 层的网络，整体 Jacobian 是

$$
J=J_L\,J_{L-1}\cdots J_1
$$

每层只需要提供自己的局部 Jacobian，乘起来就得到"输出对输入"的完整导数表。这正是反向传播高效的原因：**局部导数可以逐层复用，不必把整个复合函数展开**。

如果最终输出是标量损失 $\mathcal{L}$，那么 $J_L$ 是 $1\times n_L$ 的行向量（损失对最后一层激活的梯度），一路左乘回输入层，就得到损失对每个参数的敏感度。本节只需要建立这条"形状链条"，具体的反向递推算法留到 2.2.1。

## 四、把规则压缩成三句话

1. **数形状**：函数从 $\mathbb{R}^n$ 到 $\mathbb{R}^m$，Jacobian 就是 $m\times n$。
2. **填表**：第 $i$ 行第 $j$ 列放 $\partial f_i/\partial x_j$；求某一列时只让那个输入动。
3. **串链条**：复合函数的 Jacobian 是各层 Jacobian 的乘积，顺序按"输出在最左、输入在最右"排，相邻内维必须相等。

## 小结

- 一元导数是 $1\times 1$ 的 Jacobian，梯度是 $1\times n$ 的 Jacobian；Jacobian 是它们的统一形式。
- Jacobian 的形状由"输出个数 × 输入个数"决定，与函数内部多复杂无关。
- Jacobian 是函数在某点的局部线性映射：$\Delta\mathbf{f}\approx J_f\Delta\mathbf{x}$，形状决定了这个乘法能否成立。
- 复合函数（多层网络）的整体 Jacobian 等于各层 Jacobian 依次相乘；相邻矩阵的内维必须相等，这条约束同时给出了相乘的顺序。
- 局部 Jacobian 可以逐层复用，这是反向传播高效计算梯度的结构基础。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| 向量值函数 | 输出是向量的函数，如 $\mathbf{f}:\mathbb{R}^2\to\mathbb{R}^2$ |
| 偏导数 $\partial f_i/\partial x_j$ | 只让第 $j$ 个输入变、其余冻结时，第 $i$ 个输出的变化率 |
| Jacobian 矩阵 $J_f$ | 把所有 $\partial f_i/\partial x_j$ 按"行=输出、列=输入"排成的 $m\times n$ 矩阵 |
| 局部线性近似 | 在一点附近用 $J_f$ 这个线性映射代替原函数 |
| 内维 | 矩阵乘法中前一个矩阵的列数与后一个矩阵的行数，必须相等才能相乘 |