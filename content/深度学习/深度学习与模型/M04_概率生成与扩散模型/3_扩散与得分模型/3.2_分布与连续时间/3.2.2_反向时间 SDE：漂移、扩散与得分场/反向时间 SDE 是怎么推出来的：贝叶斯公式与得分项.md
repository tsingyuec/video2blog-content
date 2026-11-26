# 反向时间 SDE 是怎么推出来的：贝叶斯公式与得分项

> 视频来源：[【公式证明】扩散模型中的reverse-time SDE是怎么推导得到的呢？](https://www.bilibili.com/video/BV14n4y1d7vy/)（Bilibili · hallo128）｜时长约 34 分钟
> 导读：这支视频只回答一个问题——前向 SDE 是人为设计的，反向时间 SDE 里那个 $g^2\nabla\log p$ 到底从哪一步冒出来的？讲者跟着苏剑林《生成扩散模型漫谈：一般框架之SDE篇》的思路，把推导拆成「离散化 → 条件高斯 → 贝叶斯 → 泰勒展开 → 配方 → 连续化」六步，全程手写。本文按视频顺序复述这六步，并保留讲者对前提条件与另一条更严格证明路线的说明。

## 本讲要解决的核心问题（SCQA）

**背景**：用 SDE 做扩散模型时，实际只会用到两条方程。前向是

$$
dx = f_t(x)\,dt + g_t\,dw
$$

反向是

$$
dx = \left[f_t(x) - g_t^2\nabla_x\log p_t(x)\right]dt + g_t\,d\bar w
$$

论文里直接把这两条写出来，然后就开始用了。

![讲者手写的两条方程：前向 SDE 与逆向 SDE，差别就在漂移里多减的那一项](assets/反向时间%20SDE%20是怎么推出来的：贝叶斯公式与得分项/00025.jpg)

**冲突**：前向方程是我们自己设计的，$f_t$ 和 $g_t$ 随便挑；可反向方程凭什么长这样？尤其那个多出来的 $-g_t^2\nabla_x\log p_t(x)$，它是从哪里冒出来的？如果只是背下来，一旦换了加噪方式就不知道该怎么改。

**疑问**：能不能只用初等工具，从前向方程一步步推出反向方程？中间那一步"得分函数出现"到底发生在哪里？

**回答（中心思想）**：能，而且不需要随机分析的重型机器。思路是**把连续方程先拆成小步的离散更新，算出"前向一步"的条件分布是一个高斯；再用贝叶斯公式把它翻成"反向一步"；翻的过程中对 $\log p$ 做一阶泰勒展开，展开式里的梯度项 $\nabla_x\log p_t(x)$ 就自然出现了；最后配方、取 $\Delta t\to0$ 的极限，就得到反向时间 SDE。**

## 一、先把前提和路线说清楚

### 1.1 前提：$g_t$ 必须是标量

视频开头先给这条推导划定适用范围：**前向方程里的第二个函数 $g_t$ 必须是实数到实数的标量**。只有当它是标量时，下面这套推导才成立；如果 $g_t$ 是一个矩阵（每个维度上的噪声强度不同），这套写法就不能直接用。[【跳转到 00:50】](https://www.bilibili.com/video/BV14n4y1d7vy/?t=50)

讲者提到他看过两种证明思路，并明确说自己选的是简单的那条：[【跳转到 01:15】](https://www.bilibili.com/video/BV14n4y1d7vy/?t=75)

1. **正态分布重参数化路线**：把每一步的转移写成一个高斯，做重参数化，再用贝叶斯公式翻方向。**前提是 $g_t$ 为标量**，但推导短、只需要初等代数。
2. **常微分方程 + Fokker-Planck 方程路线**：更严谨，$g_t$ 是矩阵也成立，但前置知识多得多（要懂 Fokker-Planck 方程、连续性方程那一套）。

![讲者标注的两条证明路线：一条走正态分布重参数化，一条走常微分方程与 Fokker-Planck 方程](assets/反向时间%20SDE%20是怎么推出来的：贝叶斯公式与得分项/00125.jpg)

本文只复述**第一条路线**。第二条路线涉及 Fokker-Planck 方程的严格条件，属于随机分析的内容，本小节不展开。

### 1.2 目标：把前向方程"翻个方向"

前向方程写成微分形式是[【跳转到 05:20】](https://www.bilibili.com/video/BV14n4y1d7vy/?t=320)

$$
dx = f_t(x)\,dt + g_t\,dw \tag{1}
$$

把它在时间上离散化，就得到每一步的更新规则：

$$
x_{t+\Delta t} - x_t = f_t(x_t)\,\Delta t + g_t\sqrt{\Delta t}\,\epsilon,\qquad \epsilon\sim\mathcal N(0,I) \tag{2}
$$

![前向 SDE 的微分形式（1）与它的离散形式（2）：随机项前面是 √Δt 而不是 Δt](assets/反向时间%20SDE%20是怎么推出来的：贝叶斯公式与得分项/00320.jpg)

注意 (2) 里随机项前面的系数是 $\sqrt{\Delta t}$，不是 $\Delta t$。这个细节是整条推导的支点，下一节专门解释。

**推导目标**：已知 (2) 描述的是"从 $x_t$ 走到 $x_{t+\Delta t}$"，现在要反过来写出"已知 $x_{t+\Delta t}$ 时 $x_t$ 是什么分布"，再取连续极限。

## 二、为什么随机项是 $\sqrt{\Delta t}\,\epsilon$

### 2.1 布朗运动的三个性质

$w$ 是布朗运动（维纳过程）。视频把它的性质列成三条：[【跳转到 04:55】](https://www.bilibili.com/video/BV14n4y1d7vy/?t=295)

1. **正态增量**：对 $s<t$，增量 $w(t)-w(s)$ 服从均值为 $0$、**方差等于时间间隔** $t-s$ 的正态分布，即 $w(t)-w(s)\sim\mathcal N(0,(t-s)I)$。
2. **增量独立**：不重叠时间段上的增量相互独立。
3. **路径连续**：$w(t)$ 是 $t$ 的连续函数。

![布朗运动的三条性质与 SDE 的离散形式：增量方差等于时间间隔，所以标准差是 √Δt](assets/反向时间%20SDE%20是怎么推出来的：贝叶斯公式与得分项/00495.jpg)

### 2.2 从性质 1 推出离散形式

取一小段 $[t,t+\Delta t]$，这段上的布朗增量是 $w(t+\Delta t)-w(t)$。按性质 1，它服从 $\mathcal N(0,\Delta t\,I)$——**均值是 $0$，方差是 $\Delta t$**。[【跳转到 07:25】](https://www.bilibili.com/video/BV14n4y1d7vy/?t=445)

一个零均值、方差为 $\Delta t$ 的高斯变量，可以重参数化成"标准差乘以一个标准正态"：

$$
w(t+\Delta t)-w(t) = \sqrt{\Delta t}\,\epsilon,\qquad \epsilon\sim\mathcal N(0,I)
$$

当 $\Delta t$ 足够小时，左边就写成微分形式 $dw$，于是

$$
dw \approx \sqrt{\Delta t}\,\epsilon
$$

这正是 (2) 里那个 $\sqrt{\Delta t}$ 的来源。[【跳转到 08:40】](https://www.bilibili.com/video/BV14n4y1d7vy/?t=520) 讲者在这里反复强调：**这一点非常重要，因为它是后面所有"方差是 $g^2\Delta t$"结论的根**。

## 三、前向一步是一个高斯

### 3.1 重参数化写出条件分布

把 (2) 里的 $\sqrt{\Delta t}\,\epsilon$ 看成已知方差的噪声，把其余部分看成均值，就得到**给定 $x_t$ 时 $x_{t+\Delta t}$ 的条件分布**：[【跳转到 11:21】](https://www.bilibili.com/video/BV14n4y1d7vy/?t=681)

$$
p(x_{t+\Delta t}\mid x_t) = \mathcal N\left(x_{t+\Delta t};\; x_t + f_t(x_t)\Delta t,\; g_t^2\Delta t\,I\right)
$$

![把离散更新式重参数化：均值是 x_t + f_t Δt，标准差是 g_t √Δt，于是条件分布是高斯](assets/反向时间%20SDE%20是怎么推出来的：贝叶斯公式与得分项/00762.jpg)

写成密度函数、并丢掉与 $x_{t+\Delta t}$ 无关的归一化常数，就是

$$
p(x_{t+\Delta t}\mid x_t) \propto \exp\left(-\frac{\left\lVert x_{t+\Delta t} - x_t - f_t(x_t)\Delta t\right\rVert^2}{2g_t^2\Delta t}\right) \tag{3}
$$

这一步是整个推导的"地基"：**只要前向是线性加高斯的，一步转移就一定是高斯，而高斯的指数里是一个二次型**。后面所有的操作都是在处理这个二次型。

### 3.2 贝叶斯公式翻方向

现在要的是 $p(x_t\mid x_{t+\Delta t})$。按贝叶斯公式：

$$
p(x_t\mid x_{t+\Delta t}) = \frac{p(x_{t+\Delta t}\mid x_t)\,p(x_t)}{p(x_{t+\Delta t})}
$$

视频在这里做了一个小变换，把除法搬进指数里：[【跳转到 15:10】](https://www.bilibili.com/video/BV14n4y1d7vy/?t=910)

$$
p(x_t\mid x_{t+\Delta t}) = p(x_{t+\Delta t}\mid x_t)\exp\left(\log p(x_t) - \log p(x_{t+\Delta t})\right) \tag{4}
$$

这一步是恒等变形（$e^{\log x}=x$，相除在对数里变成相减），但它把"未知的 $p(x_t)$、$p(x_{t+\Delta t})$"变成了"未知的 $\log p$"，而 $\log p$ 是可以做泰勒展开的。

把 (3) 代进 (4) 的 $p(x_{t+\Delta t}\mid x_t)$，得到

$$
p(x_t\mid x_{t+\Delta t}) \propto \exp\left(-\frac{\left\lVert x_{t+\Delta t} - x_t - f_t(x_t)\Delta t\right\rVert^2}{2g_t^2\Delta t} + \log p(x_t) - \log p(x_{t+\Delta t})\right)
$$

## 四、泰勒展开：得分项在这里出现

### 4.1 $\log p$ 是两个变量的函数

展开之前，视频特意停下来解释一个容易踩的坑：$p(x_t)$ 是"$t$ 时刻随机变量取值 $x_t$ 的概率密度"，所以它**同时依赖 $x_t$ 和 $t$**，是一个二元函数。因此对它做一阶展开时，**既要对 $x$ 求偏导，也要对 $t$ 求偏导**，不能只写梯度那一项。[【跳转到 17:15】](https://www.bilibili.com/video/BV14n4y1d7vy/?t=1035)

### 4.2 在 $x_t$ 处展开 $\log p(x_{t+\Delta t})$

把 $\log p(x_{t+\Delta t})$ 在 $x_t$ 处做一阶泰勒展开（$\Delta t$ 很小时 $x_{t+\Delta t}$ 与 $x_t$ 很接近）：[【跳转到 16:00】](https://www.bilibili.com/video/BV14n4y1d7vy/?t=960)

$$
\log p(x_{t+\Delta t}) \approx \log p(x_t) + (x_{t+\Delta t}-x_t)\cdot\nabla_{x_t}\log p(x_t) + \Delta t\,\frac{\partial}{\partial t}\log p(x_t) \tag{5}
$$

![贝叶斯公式（4）与 log p 的一阶泰勒展开（5）：梯度项和对时间的偏导项都在这里出现](assets/反向时间%20SDE%20是怎么推出来的：贝叶斯公式与得分项/00960.jpg)

代回 (4)，$\log p(x_t)$ 与 $-\log p(x_t)$ 正好抵消，剩下

$$
p(x_t\mid x_{t+\Delta t}) \propto \exp\left(-\frac{\left\lVert x_{t+\Delta t} - x_t - f_t(x_t)\Delta t\right\rVert^2}{2g_t^2\Delta t} - (x_{t+\Delta t}-x_t)\cdot\nabla_{x_t}\log p(x_t) - \Delta t\frac{\partial}{\partial t}\log p(x_t)\right)
$$

**得分函数 $\nabla_{x_t}\log p(x_t)$ 就是在这里第一次登场的**——它不是被"设计"进去的，而是贝叶斯公式里那个 $p(x_t)$ 做一阶展开时自动掉出来的。

### 4.3 配方：把两项合成一个平方

上式指数里有两个含 $x_t$ 的项，一个是二次型，一个是线性项。视频接下来做的就是**一元二次配方**：把线性项吸收进平方里，凑成"$x$ 减去某个均值"的平方形式。[【跳转到 24:20】](https://www.bilibili.com/video/BV14n4y1d7vy/?t=1460)

配方过程中，线性项前面要乘上 $\Delta t$（因为要把 $(x_{t+\Delta t}-x_t)$ 与 $\Delta t$ 对齐），分母里会多出一个 $2g_t^2\Delta t$，平方之后系数里的 $2$ 被消掉。剩下的那个只含 $\Delta t$ 的多项式，当 $\Delta t\to0$ 时趋于零，直接忽略。[【跳转到 25:35】](https://www.bilibili.com/video/BV14n4y1d7vy/?t=1535)

配方完成后得到

$$
p(x_t\mid x_{t+\Delta t}) \propto \exp\left(-\frac{\left\lVert x_{t+\Delta t} - x_t + \left[f_t(x_t) - g_t^2\nabla_{x_t}\log p(x_t)\right]\Delta t\right\rVert^2}{2g_t^2\Delta t} + \mathcal O(\Delta t)\right) \tag{6}
$$

![配方之后得到（6）：反向一步仍然是高斯，只是均值里多了 −g²∇log p 这一项](assets/反向时间%20SDE%20是怎么推出来的：贝叶斯公式与得分项/01485.jpg)

### 4.4 读出反向一步的均值与方差

(6) 是一个标准的高斯形式 $\exp\left(-\dfrac{\lVert x-\mu\rVert^2}{2\sigma^2}\right)$，对照着读出来：

- **方差**：分母还是 $2g_t^2\Delta t$，所以方差是 $g_t^2\Delta t$——**和前向一步完全一样**。
- **均值**：括号里是 $x_{t+\Delta t} - x_t + [\cdots]\Delta t$，把它整理成"$x_t$ 减去某个东西"，就得到反向一步的均值。

这里有个小技巧：因为 $(x-\mu)^2=(\mu-x)^2$，整体取负号不影响平方，所以可以把符号整理到更好看的位置。[【跳转到 27:39】](https://www.bilibili.com/video/BV14n4y1d7vy/?t=1659)

## 五、再重参数化，然后取连续极限

### 5.1 反向一步的重参数化

既然反向一步也是高斯，就可以像第 3 节那样再重参数化一次：$x_t = \mu + \sigma\epsilon$。[【跳转到 30:09】](https://www.bilibili.com/video/BV14n4y1d7vy/?t=1809)

把第 4.4 节读出的均值与标准差代进去，得到

$$
x_t = x_{t+\Delta t} - \left[f_t(x_t) - g_t^2\nabla_{x_t}\log p(x_t)\right]\Delta t + g_t\sqrt{\Delta t}\,\epsilon
$$

移项写成增量形式：

$$
x_{t+\Delta t} - x_t = \left[f_t(x_t) - g_t^2\nabla_{x_t}\log p(x_t)\right]\Delta t - g_t\sqrt{\Delta t}\,\epsilon
$$

视频在这里提醒：$\epsilon$ 前面的正负号无所谓，因为 $\epsilon$ 本身是零均值对称分布，把负号吸收进 $\epsilon$ 里完全等价。[【跳转到 32:07】](https://www.bilibili.com/video/BV14n4y1d7vy/?t=1927)

### 5.2 连续化：得到反向时间 SDE

最后一步是把离散式子变回微分：$x_t\to x$，$\Delta t\to dt$，$\sqrt{\Delta t}\,\epsilon\to dw$，$g_t$ 保持不动。[【跳转到 33:22】](https://www.bilibili.com/video/BV14n4y1d7vy/?t=2002)

$$
dx = \left[f_t(x) - g_t^2\nabla_x\log p_t(x)\right]dt + g_t\,dw \tag{8}
$$

![连续化之后得到（8）：这就是反向时间 SDE，最早出现在《Reverse-Time Diffusion Equation Models》](assets/反向时间%20SDE%20是怎么推出来的：贝叶斯公式与得分项/01977.jpg)

![把（7）整理成高斯形式后，就得到反向过程对应的 SDE，即式（8）](assets/反向时间%20SDE%20是怎么推出来的：贝叶斯公式与得分项/01784.jpg)

讲者在画面上标注了这条式子的出处：它最早出现在《Reverse-Time Diffusion Equation Models》这篇文献里。他同时说明，这里特意保留了时间下标，是为了强调 $f_t$、$g_t$、$p_t$ 都是"时刻 $t$ 的"量。[【跳转到 29:44】](https://www.bilibili.com/video/BV14n4y1d7vy/?t=1784)

把 (8) 与 (1) 并排看，差别只有一处：

$$
\underbrace{f_t(x)}_{\text{前向漂移}} \quad\longrightarrow\quad \underbrace{f_t(x) - g_t^2\nabla_x\log p_t(x)}_{\text{反向漂移}}
$$

**扩散系数 $g_t$ 没变，布朗增量没变，只有漂移被减掉了一项 $g_t^2\nabla_x\log p_t(x)$。** 这就是"反向时间 SDE 依赖得分函数"的全部内容。

## 六、这条推导告诉了我们什么

回头看整条链路，每一步都只用到初等工具：

```
前向 SDE (1)
   ↓ 布朗增量方差 = Δt
离散形式 (2)：随机项系数是 √Δt
   ↓ 重参数化（均值 + 标准差 × ε）
一步条件分布是高斯 (3)
   ↓ 贝叶斯公式
反向条件分布 (4)：出现 log p(x_t) 与 log p(x_{t+Δt})
   ↓ 对 log p 做一阶泰勒展开（对 x 和对 t 都要展开）
得分项 ∇log p 出现 (5)
   ↓ 一元二次配方
反向一步仍是高斯，均值多减 g²∇log p (6)
   ↓ 再重参数化 + Δt → 0
反向时间 SDE (8)
```

三个值得记住的结论：

1. **得分项不是设计出来的，是贝叶斯公式的副产品。** 只要反向过程要靠 $p(x_t)$ 来"翻方向"，而 $p(x_t)$ 只能展开、不能解析写出，梯度项就必然出现。
2. **方差不变，只有均值被修正。** 前向和反向每一步的噪声强度都是 $g_t^2\Delta t$；被改的只是"往哪里走"，而修正的方向正是得分函数指的方向。
3. **前提是 $g_t$ 为标量。** 想要更一般的结论（$g_t$ 是矩阵），就得换用常微分方程 + Fokker-Planck 方程那条更严格的路线——那是另一套前置知识，本小节不涉及。

## 小结

- 前向 SDE 的离散形式里，随机项系数是 $\sqrt{\Delta t}$，因为布朗增量的**方差**等于时间间隔。
- 前向一步的条件分布是高斯的，指数里是一个二次型；这是整条推导的地基。
- 用贝叶斯公式翻方向后，未知量变成 $\log p(x_t)$；对它做一阶泰勒展开（对 $x$ 与对 $t$ 都要展开），**梯度项 $\nabla_x\log p$ 自然出现**。
- 配方后反向一步仍是高斯：**方差不变（$g_t^2\Delta t$），均值多减 $g_t^2\nabla_x\log p_t(x)\Delta t$**。
- 取 $\Delta t\to0$ 得到反向时间 SDE：$dx=[f_t-g_t^2\nabla_x\log p_t]dt+g_t\,dw$，即最早见于《Reverse-Time Diffusion Equation Models》的形式。
- 该推导要求 $g_t$ 为标量；更一般的矩阵情形需要 Fokker-Planck 方程路线，本文不展开。

## 关键术语速查

| 术语 | 一句话解释 |
| :--- | :--- |
| 前向 SDE | 人为设计的加噪方程 $dx=f_t\,dt+g_t\,dw$，把数据分布推向高斯 |
| 反向时间 SDE | 沿时间倒放、复现同一串边缘密度的方程，漂移里含得分项 |
| 布朗运动 $w$ | 增量服从 $\mathcal N(0,\Delta t)$ 的连续随机过程，方差等于时间间隔 |
| 重参数化 | 把高斯写成"均值 + 标准差 × 标准正态"，从而把随机性隔离到一个 $\epsilon$ 上 |
| 条件分布 $p(x_{t+\Delta t}\mid x_t)$ | 前向一步的转移密度，在本推导中是均值为 $x_t+f_t\Delta t$、方差为 $g_t^2\Delta t$ 的高斯 |
| 得分函数 $\nabla_x\log p_t(x)$ | 对数密度的梯度，指向概率上升最陡的方向，与归一化常数无关 |
| 配方 | 把二次型加线性项整理成"完全平方 + 常数"，从而读出高斯的均值与方差 |
| Fokker-Planck 方程 | 描述概率密度随 SDE 演化的偏微分方程，另一条更严格证明路线的工具 |
| 标量 $g_t$ | 各维度共用同一噪声强度的情形；本推导的前提条件 |