# DDPM 损失函数推导：为什么网络只预测噪声

> 视频来源：[Diffusion ｜ DDPM ｜ 5 - 损失函数](https://www.bilibili.com/video/BV1ju4y1x7L4/)（Bilibili · Enzo_Mi）｜时长约 13 分钟
> 导读：这支视频属于一个 DDPM 系列的第 5 讲，只回答一个问题——训练循环里那行「预测噪声的均方误差」是怎么从最大似然一步步推出来的。本文按视频顺序复述推导，并在关键处补上"这一步在做什么"的说明；前向加噪与反向去噪的细节请配合本系列 3.1.1、3.1.2 两节阅读。

## 本讲要解决的核心问题（SCQA）

**背景**：DDPM 的训练伪代码只有几行——取一张图 $x_0$，随机抽时间步 $t$，抽一份高斯噪声 $\epsilon$，然后对
$\lVert \epsilon - \epsilon_\theta(\sqrt{\bar\alpha_t}x_0+\sqrt{1-\bar\alpha_t}\epsilon,\ t)\rVert^2$
做一次梯度下降。网络输出的是噪声，不是图像。

**冲突**：我们真正想要的明明是"生成一张图"，为什么监督信号不是原图 $x_0$，也不是反向过程的均值，而是那份人为加进去的噪声？

**疑问**：从"最大化训练数据的似然"到"预测噪声的均方误差"，中间每一步的依据是什么？

**回答（中心思想）**：损失函数的目标是最大化 $\log p_\theta(x_0)$；它无法直接求导，于是转成最大化 ELBO；ELBO 化简后只剩一项"去噪匹配"，即两个高斯分布的 KL 散度；两个高斯的 KL 只由均值差决定，而真实分布的均值解析可求、网络分布的均值待定；把均值里的未知量替换成 $\epsilon$ 之后，网络唯一要预测的东西就是噪声，损失自然退化成 $\epsilon$ 的均方误差。

## 一、损失函数的目标：让训练样本出现的概率最大

### 1.1 先把图像看成采样

视频从最朴素的极大似然估计讲起。把训练样本中图像的每一个像素，都看成从"对应位置的分布"中采样得到的一个样本；我们想通过这些采样，反过来求出该分布的参数。

具体假设是：图像（每个像素）服从正态分布。于是目标变成——找出一对均值与方差，使得从该正态分布中采样出这些样本值的概率最大。

[【跳转到 00:50】](https://www.bilibili.com/video/BV1ju4y1x7L4/?t=50)

![极大似然估计：求解参数 θ 使似然函数最大，并说明取对数的三个理由](assets/DDPM%20损失函数推导：为什么网络只预测噪声/00050.webp)

写成公式，就是找一组参数 $\hat\theta=\{\mu,\sigma\}$，使似然函数

$$
L(\theta)=\prod_{i=1}^{n}p(x_i \mid \theta)
$$

最大。取对数后连乘变成求和：

$$
\log L(\theta)=\sum_{i=1}^{n}\log p(x_i \mid \theta)
$$

视频里给了三个取对数的理由：求导容易（乘法变加法）、保持单调性（最大值位置不变）、避免大量概率连乘因计算机精度下溢成 0。放到扩散模型里，目标就是找 $\hat\theta$ 使 $\log p_\theta(x_0)$ 最大——因为最终要的是 $t=0$ 时刻那张图。

### 1.2 直接对 $\log p_\theta(x_0)$ 求导行不通

通常求极值的做法是对参数求导。但 $p_\theta(x_0)$ 要把所有中间状态 $x_1$ 到 $x_T$ 积分掉，而 $x_1,\dots,x_T$ 的搭配方式"超级多"，每一种搭配下 $p_\theta(x_0)$ 都不一样。所以这个量既算不出来，也求不了导。

于是换一条路：把"最大化对数似然"改写成"最大化 ELBO（证据下界，Evidence Lower Bound）"。视频说明这一步的推导与前面"基础知识准备"一讲相同，不逐行展开。

[【跳转到 02:30】](https://www.bilibili.com/video/BV1ju4y1x7L4/?t=150)

## 二、ELBO 化简：只剩一项"去噪匹配"

### 2.1 三项分解

对 ELBO 继续化简，最后得到三个部分：

[【跳转到 03:20】](https://www.bilibili.com/video/BV1ju4y1x7L4/?t=200)

![ELBO 的展开：从 log p(x) 的下界一路改写为含 p(x_T)、p_θ(x_0|x_1) 与逐时刻条件分布的表达式](assets/DDPM%20损失函数推导：为什么网络只预测噪声/00200.webp)

- **重建项** $\mathbb{E}_{q(x_1\mid x_0)}[\log p_\theta(x_0\mid x_1)]$：从 $x_1$ 还原 $x_0$ 的能力。
- **先验匹配项** $D_{KL}(q(x_T\mid x_0)\,\Vert\,p(x_T))$：视频指出它是一个**已知常数**——$q(x_T\mid x_0)$ 来自已知的正向加噪过程，$p(x_T)$ 是人为设定的标准高斯，两者都已知，KL 也就是常数。
- **去噪匹配项** $\sum_{t=2}^{T}\mathbb{E}\left[D_{KL}(q(x_{t-1}\mid x_t,x_0)\,\Vert\,p_\theta(x_{t-1}\mid x_t))\right]$：每一步"真实的反向分布"与"网络给出的反向分布"之间的差距。

[【跳转到 04:10】](https://www.bilibili.com/video/BV1ju4y1x7L4/?t=250)

![ELBO 化简后的三项：重建项、先验匹配项（已知常数）与去噪匹配项，前两项可合并进求和](assets/DDPM%20损失函数推导：为什么网络只预测噪声/00250.webp)

### 2.2 合并成逐时刻 KL

重建项可以改写成同一形式的 KL，并合并进求和里（它在 $t=1$ 处，去噪匹配项从 $t=2$ 开始，正好接上）。因为原式前面带负号，最大化就变成最小化：

$$
\min_\theta \sum_{t=1}^{T}\mathbb{E}_{q(x_t\mid x_0)}\left[D_{KL}(q(x_{t-1}\mid x_t,x_0)\,\Vert\,p_\theta(x_{t-1}\mid x_t))\right]
$$

[【跳转到 05:00】](https://www.bilibili.com/video/BV1ju4y1x7L4/?t=300)

到这里，训练目标已经非常像普通的回归问题：真实分布 $q(x_{t-1}\mid x_t,x_0)$ 是"标签"，网络分布 $p_\theta(x_{t-1}\mid x_t)$ 是"预测"，损失是两者的 KL。要注意的是**标签里带着 $x_0$**——训练时我们手上正好有 $x_0$，所以这个"标签"是可算的；生成时没有 $x_0$，才需要网络去猜。

## 三、两个高斯的 KL 只差一个均值

### 3.1 方差固定，监督落在均值上

视频直接引用两个高斯分布 KL 的结论：

$$
\mathrm{KL}\big(\mathcal{N}(\mu_1,\Sigma_1)\,\Vert\,\mathcal{N}(\mu_2,\Sigma_2)\big)=\frac{1}{2}\left[\log\frac{\lvert\Sigma_2\rvert}{\lvert\Sigma_1\rvert}-K+\mathrm{tr}(\Sigma_2^{-1}\Sigma_1)+(\mu_1-\mu_2)^{\mathsf T}\Sigma_2^{-1}(\mu_1-\mu_2)\right]
$$

[【跳转到 06:15】](https://www.bilibili.com/video/BV1ju4y1x7L4/?t=375)

关键处理是：**把 $p_\theta(x_{t-1}\mid x_t)$ 的方差设为固定值**。视频给出的理由是"实验证明对结果无影响"。方差一固定，KL 里与协方差有关的项就都成了常数，能变的只有均值——于是"最小化 KL"等价于"让两个均值尽量接近"，也就是让网络的预测结果去拟合真实分布的均值。

[【跳转到 07:05】](https://www.bilibili.com/video/BV1ju4y1x7L4/?t=425)

![两个高斯分布的 KL 公式，以及真实反向分布 q(x_{t-1}|x_t,x_0) 的均值与方差](assets/DDPM%20损失函数推导：为什么网络只预测噪声/00350.webp)

### 3.2 $q(x_{t-1}\mid x_t,x_0)$ 的均值可以解析求出

真实反向分布用贝叶斯公式展开：

$$
q(x_{t-1}\mid x_t,x_0)=\frac{q(x_t\mid x_{t-1},x_0)\,q(x_{t-1}\mid x_0)}{q(x_t\mid x_0)}
$$

因为正向过程是马尔可夫链，$q(x_t\mid x_{t-1},x_0)=q(x_t\mid x_{t-1})$。把三个已知的高斯表达式（$q(x_t\mid x_{t-1})$、$q(x_{t-1}\mid x_0)$、$q(x_t\mid x_0)$）都代进去，用一元二次方程的配方法整理，得到一个高斯分布：

[【跳转到 07:30】](https://www.bilibili.com/video/BV1ju4y1x7L4/?t=450)

![用贝叶斯公式与配方法把 q(x_{t-1}|x_t,x0) 化成标准高斯形式](assets/DDPM%20损失函数推导：为什么网络只预测噪声/00450.webp)

$$
q(x_{t-1}\mid x_t,x_0)=\mathcal{N}\!\left(\frac{\sqrt{\alpha_t}(1-\bar\alpha_{t-1})}{1-\bar\alpha_t}x_t+\frac{\sqrt{\bar\alpha_{t-1}}\beta_t}{1-\bar\alpha_t}x_0,\ \frac{\beta_t(1-\bar\alpha_{t-1})}{1-\bar\alpha_t}\right)
$$

其中用到了两个定义 $\beta_t=1-\alpha_t$、$\bar\alpha_t=\alpha_t\cdot\bar\alpha_{t-1}$。方差里全是 $\alpha_t,\bar\alpha_t,\beta_t$ 这些**预先定好的常数**，所以方差是常数；均值则是"一个系数乘 $x_t$ 加另一个系数乘 $x_0$"。

[【跳转到 09:10】](https://www.bilibili.com/video/BV1ju4y1x7L4/?t=550)

## 四、监督对象为什么落到 $\epsilon$ 上

### 4.1 把 $x_0$ 换成 $x_t$ 与 $\epsilon$

均值里出现了 $x_0$，但网络在训练和采样时都只有 $x_t$。利用加噪的一步到位式

$$
x_t=\sqrt{\bar\alpha_t}\,x_0+\sqrt{1-\bar\alpha_t}\,\epsilon
$$

反解出

$$
x_0=\frac{x_t-\sqrt{1-\bar\alpha_t}\,\epsilon}{\sqrt{\bar\alpha_t}}
$$

[【跳转到 10:00】](https://www.bilibili.com/video/BV1ju4y1x7L4/?t=600)

![把 x0 用 x_t 与 ε 表示，再代回均值表达式](assets/DDPM%20损失函数推导：为什么网络只预测噪声/00600.webp)

代回均值后，均值可以整理成

$$
\mu_\theta(x_t,t)=\frac{1}{\sqrt{\alpha_t}}\left(x_t-\frac{1-\alpha_t}{\sqrt{1-\bar\alpha_t}}\,\epsilon_\theta(x_t,t)\right)
$$

### 4.2 常数项网络已知，只剩 $\epsilon$ 要预测

现在看这个均值：$1/\sqrt{\alpha_t}$、$(1-\alpha_t)/\sqrt{1-\bar\alpha_t}$ 都是常数，$x_t$ 是网络输入，对网络来说全部已知；**唯一未知的就是 $\epsilon$**。既然如此，就不必让网络去预测整个均值，直接让它预测 $\epsilon$ 就行——这就是"U-Net 预测噪声"的由来。

[【跳转到 11:15】](https://www.bilibili.com/video/BV1ju4y1x7L4/?t=675)

![最小化 KL 等价于让 U-Net 预测出的均值去拟合真实均值](assets/DDPM%20损失函数推导：为什么网络只预测噪声/00650.webp)

于是损失函数写成 $\epsilon$ 与 $\epsilon_\theta$ 的均方误差：

$$
\mathcal{L}=\mathbb{E}_{t,x_0,\epsilon}\left[\left\lVert \epsilon-\epsilon_\theta\!\left(\sqrt{\bar\alpha_t}x_0+\sqrt{1-\bar\alpha_t}\epsilon,\ t\right)\right\rVert^2\right]
$$

[【跳转到 11:40】](https://www.bilibili.com/video/BV1ju4y1x7L4/?t=700)

![最小化目标已变成逐时刻 KL，而 U-Net 负责预测该分布的均值](assets/DDPM%20损失函数推导：为什么网络只预测噪声/00700.webp)

![训练算法：采样 x0、t、ε，构造 x_t 输入 U-Net，对 ε 与 ε_θ 的平方误差做梯度下降](assets/DDPM%20损失函数推导：为什么网络只预测噪声/00725.webp)

### 4.3 伪代码括号里的两个输入

视频最后解释了一个容易看漏的记号：论文伪代码里 $\epsilon_\theta$ 后面跟着一个括号，括号里是 $\left(\sqrt{\bar\alpha_t}x_0+\sqrt{1-\bar\alpha_t}\epsilon,\ t\right)$。对照推导可知，前一项就是 $x_t$。加这个括号是想说明：**这个 U-Net 的输入有两样东西，一是 $x_t$，二是时间步 $t$**。

[【跳转到 12:05】](https://www.bilibili.com/video/BV1ju4y1x7L4/?t=725)

![训练流程示意：ε 与 x0 合成 x_t，与 ᾱ_t、t 一起送入 U-Net，输出 ε_θ 后与真值 ε 比较](assets/DDPM%20损失函数推导：为什么网络只预测噪声/00750.webp)

## 五、这条推导给出的三个判断

1. **监督对象不是随便选的**：它由"KL 只由均值决定 + 均值里只有 $\epsilon$ 未知"这两步共同锁定。换成别的参数化（例如直接预测 $x_0$ 或预测速度 $v$），改变的是同一个均值公式里"把哪个量交给网络"。
2. **方差被固定，是这套推导能落到均方误差的前提**：方差一旦也交给网络学，KL 里就会出现与协方差相关的项，损失不再是纯粹的均值回归。
3. **训练时用 $x_0$ 造标签，生成时不用**：$q(x_{t-1}\mid x_t,x_0)$ 里的 $x_0$ 只在训练时存在；采样时网络只能靠 $x_t$ 与 $t$ 估计 $\epsilon$，再按上式换回均值。训练与采样的这个不对称，是后面所有采样器讨论的起点。

## 小结

- 损失函数的目标是最大化 $\log p_\theta(x_0)$，即让训练图像出现的概率最大。
- $\log p_\theta(x_0)$ 要对所有中间状态积分，无法直接求导，因此转成最大化 ELBO。
- ELBO 化简为三项：重建项、先验匹配项（常数）、去噪匹配项；前两项可合并，最终只剩逐时刻的高斯 KL。
- 两个高斯的 KL 在方差固定后只由均值差决定，所以训练等价于"让网络输出的均值逼近真实均值"。
- 真实均值解析可求，其中 $x_0$ 可用 $x_t$ 与 $\epsilon$ 替换；替换后均值里只有 $\epsilon$ 未知，于是网络改为预测 $\epsilon$，损失成为 $\epsilon$ 的均方误差。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| 极大似然估计 | 选一组参数，使已观测样本出现的联合概率最大 |
| ELBO | 对数似然的下界，最大化它等价于间接最大化似然 |
| 去噪匹配项 | 每一步真实反向分布与网络反向分布的 KL，是最终唯一要优化的项 |
| 重参数化一步到位式 | $x_t=\sqrt{\bar\alpha_t}x_0+\sqrt{1-\bar\alpha_t}\epsilon$，可由 $x_0$ 直接得到任意时刻的加噪样本 |
| $\epsilon$ 参数化 | 让网络输出噪声估计 $\epsilon_\theta(x_t,t)$，再由它换算出反向均值 |
| 固定方差 | 把 $p_\theta(x_{t-1}\mid x_t)$ 的方差设成与时间步有关的常数，使 KL 只依赖均值 |