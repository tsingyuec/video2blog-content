# DDIM 加速采样：把马尔可夫链换成非马尔可夫过程，用跳步换速度

> 视频来源：[64、扩散模型加速采样算法DDIM论文精讲与PyTorch源码逐行解读](https://www.bilibili.com/video/BV1JY4y1N7dn/)（Bilibili · deep_thoughts）｜时长约 130 分钟
> 导读：这是一次两小时多的直播，前半段逐节讲 DDIM 论文（ICLR 2021），后半段在 Vim 里逐行读 OpenAI improved diffusion 项目的 `training_losses`、`ddim_sample` 与 `respace.py`。本文按视频顺序复述：为什么采样慢、DDIM 怎样在不重训模型的前提下换掉前向过程、$\sigma=0$ 为什么得到确定性采样、respacing 怎样把 1000 步压到 10~50 步，以及代码里那个容易看漏的"时间步映射"。概率流 ODE 的理论留给本系列 3.2.3。

## 本讲要解决的核心问题（SCQA）

**背景**：DDPM 训练时用 1000 步把图片加噪成噪声，采样时也要迭代 1000 步、每一步跑一次 U-Net。用过 Stable Diffusion 在线 API 的人都有体感：输入一句话，要等一两分钟才返回一张图。[【跳转到 00:30】](https://www.bilibili.com/video/BV1JY4y1N7dn/?t=30)

**冲突**：这 1000 步并不是"物理定律"要求的，而是**为了模拟前向那条马尔可夫链**。视频里给了个量级：生成 5 万张 32×32 的图片要 20 小时，生成 256×256 的图片要 1000 小时；而 GAN 只要一次前向计算，可能一分钟就做完。[【跳转到 20:17】](https://www.bilibili.com/video/BV1JY4y1N7dn/?t=1217)

**疑问**：既然慢的根源是"必须模拟马尔可夫链"这个假设，那这个假设能不能去掉？去掉之后还能不能复用已经训好的模型？

**回答（中心思想）**：能，而且不需要重训。关键在于一个发现——**DDPM 的训练目标 $L_{\text{simple}}$ 只依赖边缘分布 $q(x_t\mid x_0)$，不依赖联合分布 $q(x_{1:T}\mid x_0)$**。于是可以构造一族非马尔可夫的前向过程（引入超参数向量 $\sigma$），只要边缘分布不变，同一个模型就能用；$\sigma$ 取特定值时还原成 DDPM，取零时得到确定性采样（这就是 DDIM）；再在时间轴上取一个子序列（respacing）采样，就能用 10~50 步拿到接近 1000 步的质量。[【跳转到 2:29】](https://www.bilibili.com/video/BV1JY4y1N7dn/?t=149)

## 一、慢的根源：步数被"模拟马尔可夫链"绑死

### 1.1 1000 步是怎么来的

DDPM 的生成过程被定义成前向加噪的逆过程：前向有 $T$ 步，生成也就被强行设成 $T$ 步。视频的解释很直白：因为前向扩散是从数据到噪声、有上千步加噪，所以逆过程也要上千步把噪声变回数据。[【跳转到 19:27】](https://www.bilibili.com/video/BV1JY4y1N7dn/?t=1167)

而这是一个**自回归**的迭代：后一个时刻依赖前一个时刻的结果，不像 Transformer 那样能并行，所以整个过程非常慢。[【跳转到 34:25】](https://www.bilibili.com/video/BV1JY4y1N7dn/?t=2065)

### 1.2 关键发现：目标函数只认边缘分布

视频把 DDPM 的推导重新走了一遍，为的是指出一件事：推导 $L_{\text{simple}}$ 时用到的只有两样东西——贝叶斯公式，以及"给定 $x_0$ 时任意时刻 $x_t$ 服从高斯分布"这个边缘分布性质；**从来没有用到联合分布 $q(x_{1:T}\mid x_0)$ 的具体形式**。[【跳转到 43:40】](https://www.bilibili.com/video/BV1JY4y1N7dn/?t=2620)

更进一步：推到 $L_{\text{simple}}$ 时，前面那些权重（$\sigma_t$、$\alpha_t$、$\bar\alpha_t$、$\beta_t$）全被丢掉了，只剩下 $\|\epsilon-\epsilon_\theta\|^2$。而这些权重才是跟"马尔可夫链加噪"绑定的东西。[【跳转到 44:45】](https://www.bilibili.com/video/BV1JY4y1N7dn/?t=2685)

于是结论是：**只要 $q(x_t\mid x_0)$ 的形式不变，加噪过程用什么联合分布都行**。这也顺带解释了另一件事——$L_{\text{simple}}$ 其实就是分数匹配的目标函数，而分数模型本来就没有马尔可夫假设。[【跳转到 46:51】](https://www.bilibili.com/video/BV1JY4y1N7dn/?t=2811)

## 二、非马尔可夫前向过程：只改联合分布，不动边缘分布

### 2.1 引入超参数向量 $\sigma$

论文设计了一族推断分布，用一个实数向量 $\sigma\in\mathbb{R}^T_{\ge 0}$ 来索引。这个 $\sigma$ 是**超参数**：不需要训练，但可以自己调。[【跳转到 51:01】](https://www.bilibili.com/video/BV1JY4y1N7dn/?t=3061)

新的联合分布不再是一串条件概率的连乘（马尔可夫链），而是：

$$
q_\sigma(x_{1:T}\mid x_0) := q_\sigma(x_T\mid x_0)\prod_{t=2}^{T} q_\sigma(x_{t-1}\mid x_t, x_0)
$$

其中每一项都是高斯：

$$
q_\sigma(x_T\mid x_0)=\mathcal{N}\!\left(\sqrt{\alpha_T}x_0,\ (1-\alpha_T)I\right)
$$

$$
q_\sigma(x_{t-1}\mid x_t,x_0)=\mathcal{N}\!\left(\sqrt{\alpha_{t-1}}x_0+\sqrt{1-\alpha_{t-1}-\sigma_t^2}\cdot\frac{x_t-\sqrt{\alpha_t}x_0}{\sqrt{1-\alpha_t}},\ \sigma_t^2 I\right)
$$

注意两个变化：条件里多了 $x_0$（所以不是马尔可夫链），并且**多了一个 $\sigma_t$**。视频强调，这三个公式（联合分布、边缘分布、后验分布）都是作者"定义"的，不是推出来的。[【跳转到 51:51】](https://www.bilibili.com/video/BV1JY4y1N7dn/?t=3111)

![论文第 4 节：用 sigma 索引的一族推断分布，式 (6)(7)(8) 分别是联合分布、后验分布与贝叶斯改写](assets/DDIM%20加速采样：非马尔可夫前向过程、确定性采样与跳步预算/03111.webp)

### 2.2 为什么边缘分布没变：一个归纳法证明

定义了新过程之后，必须回答一个问题：任意时刻的 $q_\sigma(x_t\mid x_0)$ 还等于 DDPM 里那个高斯吗？如果不等，$L_{\text{simple}}$ 就不能用了。

论文用数学归纳法证明它确实不变。视频为了让听众跟上，先补了两个前置知识：一是"已知边缘高斯和条件高斯，求另一个变量的边缘高斯"的定理（均值 $A\mu+b$，方差 $L^{-1}+A\Lambda^{-1}A^{\top}$），二是数学归纳法本身（还现场证了一道 $5^n+3^n\ge 2^{2n+1}$ 的题）。[【跳转到 55:14】](https://www.bilibili.com/video/BV1JY4y1N7dn/?t=3314)

证明的骨架是：以 $t=T$ 为初始条件（已定义好），假设 $t$ 时刻成立，把 $q_\sigma(x_{t-1}\mid x_0)=\int q_\sigma(x_t\mid x_0)q_\sigma(x_{t-1}\mid x_t,x_0)\,dx_t$ 用上面的高斯定理算一遍，得到均值 $\sqrt{\alpha_{t-1}}x_0$、方差 $(1-\alpha_{t-1})I$——正好是 $t-1$ 时刻该有的形式。于是归纳成立。[【跳转到 61:29】](https://www.bilibili.com/video/BV1JY4y1N7dn/?t=3689)

这一步是整个 DDIM 的合法性来源：**边缘分布不变 ⟹ 目标函数不变 ⟹ 模型可以直接复用**。

### 2.3 后验分布变了，采样公式就变了

新旧后验分布的区别只有一个 $\sigma_t$：DDPM 的后验均值是 $x_0$ 与 $x_t$ 的线性组合、方差是常数；新后验里多了一个可调的 $\sigma_t$。[【跳转到 1:10:39】](https://www.bilibili.com/video/BV1JY4y1N7dn/?t=4239)

为什么这个差别重要？因为采样时要做的重参数化，用的正是后验的均值和方差：$\sigma_t$ 不同，均值和方差就不同，采样结果就不同。**换句话说，$\sigma$ 是"采样器"的旋钮，不是"模型"的旋钮。** 视频还提到，论文也证明了新的变分目标 $J_\sigma$ 与 $L_\gamma$ 只差一个常数，所以优化 $L_{\text{simple}}$ 就等于优化 $J_\sigma$。[【跳转到 1:18:51】](https://www.bilibili.com/video/BV1JY4y1N7dn/?t=4731)

## 三、$\sigma$ 的两个端点：DDPM 与 DDIM

### 3.1 采样公式

把后验代进重参数化，就得到论文的式 (12)：[【跳转到 1:19:54】](https://www.bilibili.com/video/BV1JY4y1N7dn/?t=4794)

$$
x_{t-1}=\sqrt{\alpha_{t-1}}\underbrace{\left(\frac{x_t-\sqrt{1-\alpha_t}\,\epsilon_\theta^{(t)}(x_t)}{\sqrt{\alpha_t}}\right)}_{\text{预测的 } x_0}+\underbrace{\sqrt{1-\alpha_{t-1}-\sigma_t^2}\,\epsilon_\theta^{(t)}(x_t)}_{\text{指向 } x_t \text{ 的方向}}+\underbrace{\sigma_t\epsilon_t}_{\text{随机噪声}}
$$

三个括号把结构讲清楚了：第一项是"先预测 $x_0$"，第二项是"朝 $x_t$ 的方向补一段"，第三项是"再加一点随机噪声"。**$\sigma_t$ 只控制第三项的大小。**

### 3.2 $\sigma$ 取 DDPM 值：还原马尔可夫采样

当 $\sigma_t=\sqrt{(1-\alpha_{t-1})/(1-\alpha_t)}\sqrt{1-\alpha_t/\alpha_{t-1}}$ 时，式 (12) 完全退化成 DDPM 的采样式。所以 DDIM 论文提出的其实是一个**更一般的采样算法**，DDPM 是它的一个特例。[【跳转到 1:21:34】](https://www.bilibili.com/video/BV1JY4y1N7dn/?t=4894)

### 3.3 $\sigma=0$：确定性采样，DDIM 名字的来源

当 $\sigma_t=0$，第三项随机噪声消失，整个生成过程变成确定性的：给定一个初始的 $x_T$，后面每一步都是确定的，没有任何一步引入新噪声。[【跳转到 1:22:49】](https://www.bilibili.com/video/BV1JY4y1N7dn/?t=4969)

这种"从固定潜变量出发、按固定过程生成样本"的模型，作者命名为 **denoising diffusion implicit model（DDIM）**——名字里的 implicit 指的是它是个隐式概率模型：**用 DDPM 的目标训练，但生成过程已经不是扩散了**。[【跳转到 1:22:49】](https://www.bilibili.com/video/BV1JY4y1N7dn/?t=4969)

![式 (12) 与 DDIM 的定义：sigma 取 DDPM 值退化为 DDPM，取零则随机项消失，得到隐式概率模型 DDIM](assets/DDIM%20加速采样：非马尔可夫前向过程、确定性采样与跳步预算/04969.webp)

视频顺带做了一个类比：确定性采样让 DDIM 有点像 GAN——都是从随机噪声出发、经过一套确定的运算得到结果；区别是 DDIM 要迭代很多次，GAN 一次前向就出结果。[【跳转到 1:24:04】](https://www.bilibili.com/video/BV1JY4y1N7dn/?t=5044)

**但确定性本身并不省时间**：$\sigma=0$ 只是去掉了随机项，迭代次数还是 $T$ 次。真正省时间的是下一节的技巧。[【跳转到 1:25:24】](https://www.bilibili.com/video/BV1JY4y1N7dn/?t=5124)
## 四、respacing：在时间子序列上采样

### 4.1 从完整链到子序列 $\tau$

论文的思路是：既然 $L_{\text{simple}}$ 不依赖前向过程的长度，那就在 $1,\dots,T$ 里取一个递增子序列 $\tau_1<\dots<\tau_S$，只在这个子序列上采样。视频用卷积的 dilation 打比方：卷积核还是三个点，但不再是相邻像素，而是隔一个取一个——感受野变大、计算量不变。[【跳转到 1:28:04】](https://www.bilibili.com/video/BV1JY4y1N7dn/?t=5284)

对应地定义 $q(x_{\tau_i}\mid x_0)=\mathcal{N}(\sqrt{\alpha_{\tau_i}}x_0,(1-\alpha_{\tau_i})I)$——**边缘分布的形式一点没变**，只是索引换成了子序列的下标。于是生成过程就在这条"采样轨迹（sampling trajectory）"上走，长度从 $T$ 变成 $S$。[【跳转到 1:29:01】](https://www.bilibili.com/video/BV1JY4y1N7dn/?t=5341)

![论文第 8 节：把前向过程定义在子序列 tau 上，采样轨迹长度远小于 T，从而大幅提升效率](assets/DDIM%20加速采样：非马尔可夫前向过程、确定性采样与跳步预算/05341.webp)

### 4.2 训练步数与采样步数解耦

这一步最值得记住的一句话是：**训练时可以用任意多的前向步数，采样时只从其中取一部分**。视频的表述是：训练时把 $T$ 设成 1000、2000、3000 都可以，采样时不必从 3000 逐一递推到零，可以 3000→2500→2000→1500→1000→500→0 这样跳。[【跳转到 1:31:22】](https://www.bilibili.com/video/BV1JY4y1N7dn/?t=5482)

至于具体跳多少、是均匀取还是先密后疏地划分子序列，这些都属于超参数，需要自己挑。[【跳转到 1:32:12】](https://www.bilibili.com/video/BV1JY4y1N7dn/?t=5532)

### 4.3 代价：跳步换来的误差

跳步不是免费的。视频在讲实验时反复强调一个对比：**respacing 用在 DDPM 上，采样质量下降会比较快；用在 DDIM 上，质量下降就没那么快**。[【跳转到 5:24】](https://www.bilibili.com/video/BV1JY4y1N7dn/?t=324)

原因可以从式 (12) 看出来：DDPM 的每一步都要注入一份新的随机噪声，跳步相当于把好几步的随机注入压缩成一次，噪声日程的匹配被打乱；而 DDIM 的 $\sigma=0$，每一步是确定性的"预测 $x_0$ + 朝 $x_t$ 校正"，跳步只是让这条折线变粗，不会打乱随机性的节奏。

## 五、实验：步数、$\eta$ 与 FID

### 5.1 表格怎么读

论文在 CIFAR-10（32×32）和 CelebA（64×64）上做了网格实验，三个维度是：子序列长度 $S$、$\eta$（控制 $\sigma$ 的系数，$\eta=0$ 即 DDIM，$\eta=1$ 即 DDPM）、以及 DDPM 那一行里噪声标准差是否用 $\tilde\sigma$ 的变体。[【跳转到 1:37:51】](https://www.bilibili.com/video/BV1JY4y1N7dn/?t=5871)

![Table 1：横轴是采样步数 S，纵轴是 eta 与 sigma 变体，格子里是 FID；同一列里 eta=0（DDIM）明显优于 eta=1（DDPM）](assets/DDIM%20加速采样：非马尔可夫前向过程、确定性采样与跳步预算/05871.webp)

### 5.2 关键数字

视频挑了几个数念出来，很能说明问题：[【跳转到 1:38:41】](https://www.bilibili.com/video/BV1JY4y1N7dn/?t=5921)

- CIFAR-10 上，**DDPM 用 50 步 FID 是 8，DDIM 用 50 步是 4**；
- **DDPM 用 20 步 FID 是 18，DDIM 用 20 步是 6**；
- 也就是说，DDIM 用 20 步的效果比 DDPM 用 50 步还好。

把整张表连起来看，趋势是：步数越大 FID 越小（这条对两种采样器都成立），但**DDIM 的曲线下降得更快、更早进入平台**，所以"少步"这件事只有对 DDIM 才划算。[【跳转到 1:37:51】](https://www.bilibili.com/video/BV1JY4y1N7dn/?t=5871)

另外两个细节：CIFAR-10 上最好的一组是 $\tilde\sigma$ 那一行（1000 步 FID 3.17），也就是每一步的噪声标准差不必固定为 1，而是由 $\alpha$ 决定；CelebA 上 DDPM 1000 步是 5.98、DDIM 1000 步是 6，两者几乎持平——**说明 DDIM 在满步数时并不比 DDPM 差，加速是净赚的**。[【跳转到 1:39:56】](https://www.bilibili.com/video/BV1JY4y1N7dn/?t=5996)

视频的实用结论是：如果算力受限，可以用 DDIM 这种采样方式来减少采样耗时。[【跳转到 1:40:21】](https://www.bilibili.com/video/BV1JY4y1N7dn/?t=6021)

## 六、代码：一个函数改采样，一个类改时间表

视频后半段打开 OpenAI 的 improved diffusion 项目，只讲三处与本文相关的代码。

### 6.1 `training_losses`：训练目标与采样器解耦的地方

`gaussian_diffusion.py` 里的 `training_losses` 就是 DDPM 的训练函数。流程是：先用 `q_sample` 从 $x_0$ 和 $t$ 采出一个 $x_t$（边缘分布的重参数化，**注意必须是采样，不能拿确定值**），送进模型得到 `model_output`，再和 target 算平方差。[【跳转到 1:45:00】](https://www.bilibili.com/video/BV1JY4y1N7dn/?t=6300)

关键在 target 那个字典：如果模型预测的是均值，target 就是后验均值；预测 $x_0$，target 就是 $x_0$；预测噪声，target 就是刚刚采出来的那个 $\epsilon$。默认走的是预测噪声，所以 loss 就是 $L_{\text{simple}}$。[【跳转到 1:48:20】](https://www.bilibili.com/video/BV1JY4y1N7dn/?t=6500)

![training_losses 里的 target 字典：预测什么，target 就是什么；默认预测噪声，对应 L_simple](assets/DDIM%20加速采样：非马尔可夫前向过程、确定性采样与跳步预算/06600.webp)

这段代码正好印证了论文的立论：训练只关心 $q(x_t\mid x_0)$，不关心链怎么走——所以后面换采样器才不需要动它。

### 6.2 `ddim_sample`：式 (12) 的逐行实现

`ddim_sample` 是**单步**采样函数（一个时刻），整条链的采样靠外层的 for 循环。它先调 `p_mean_variance` 拿到上一时刻的均值和方差、以及预测的 $x_0$，然后照式 (12) 写：[【跳转到 1:50:00】](https://www.bilibili.com/video/BV1JY4y1N7dn/?t=6600)

1. 由 $x_t$、$t$、$x_0$ 反推 $\epsilon$（虽然模型已经给出，再推一遍等价）；
2. 写出 $\sigma=\eta\sqrt{(1-\bar\alpha_{t-1})/(1-\bar\alpha_t)}\sqrt{1-\bar\alpha_t/\bar\alpha_{t-1}}$，$\eta=1$ 对应 DDPM、$\eta=0$ 对应 DDIM；[【跳转到 1:52:04】](https://www.bilibili.com/video/BV1JY4y1N7dn/?t=6724)
3. 算均值：$\sqrt{\bar\alpha_{t-1}}\cdot\text{pred\_xstart}+\left(\sqrt{1-\bar\alpha_{t-1}-\sigma^2}\right)\epsilon$；
4. 均值加上 $\sigma\times$ 噪声，得到 sample。

这里有个容易看漏的细节：代码里有一个 `mask`，**当 $t=0$ 时把随机项去掉，直接输出均值**。这是 improved diffusion 的一个采样技巧——最后一刻不再注入噪声。[【跳转到 1:54:13】](https://www.bilibili.com/video/BV1JY4y1N7dn/?t=6853)

### 6.3 `respace.py`：把 500 步"翻译"回 1000 步

`respace.py` 只有一百多行，三样东西：函数 `space_timesteps`、类 `SpacedDiffusion`、以及包裹模型的 `_WrappedModel`。[【跳转到 1:55:32】](https://www.bilibili.com/video/BV1JY4y1N7dn/?t=6932)

![论文第 8 节的措辞与代码对应：前向过程定义在子序列上，采样轨迹变短，但训练目标不变](assets/DDIM%20加速采样：非马尔可夫前向过程、确定性采样与跳步预算/06932.webp)

**`space_timesteps`**：输入原始步数 `num_timesteps` 和 `section_counts`（每段取多少步，或直接写 `ddimN` 表示取 N 步），输出一个新的时间序列——也就是论文里的子序列 $\tau$。[【跳转到 1:57:17】](https://www.bilibili.com/video/BV1JY4y1N7dn/?t=7037)

**`SpacedDiffusion`**：继承 `GaussianDiffusion`，在 `__init__` 里按 `use_timesteps` 筛出新的 `betas`，然后**直接把父类的 `betas` 成员变量替换掉**，于是父类的"总步数"就缩短了——这就是 respacing 的实现方式。[【跳转到 2:02:42】](https://www.bilibili.com/video/BV1JY4y1N7dn/?t=7362)

**`_WrappedModel`**：这是全片最绕、也最值得看的一处。因为 `ddim_sample_loop` 里的 `indices` 是对**新的** `num_timesteps` 做 range 得到的（连续整数 0,1,2,…），但模型需要的是**原始的**时间步（比如 1000、998、996…）。所以包裹层的 `__call__` 里要做一次映射 `new_ts = timestep_map[ts]`，把"第几个采样步"翻译成"原始时间步"，再送进 U-Net。[【跳转到 2:07:56】](https://www.bilibili.com/video/BV1JY4y1N7dn/?t=7676)

![左侧 ddim_sample_loop 用连续 indices 迭代，右侧 respace.py 用 timestep_map 把 ts 映射回原始时间步，并做 rescale](assets/DDIM%20加速采样：非马尔可夫前向过程、确定性采样与跳步预算/07676.webp)

视频还提醒了一个工程细节：`rescale_timesteps` 始终把送进模型的时间步压在 0~1000 以内，无论你训练时用的是 1000 还是 2000 步。[【跳转到 2:08:21】](https://www.bilibili.com/video/BV1JY4y1N7dn/?t=7701)

## 七、这套做法的边界

- **确定性带来的是可复现与可插值，不是免费加速**。$\sigma=0$ 只是去掉随机项；真正省时间的是 respacing。视频也提到，正因为生成过程确定，在隐空间上做插值才更有意义。[【跳转到 15:17】](https://www.bilibili.com/video/BV1JY4y1N7dn/?t=917)
- **跳步的误差是离散化误差**。把 $T$ 段折线换成 $S$ 段折线，每段跨度变大，近似误差随之变大；DDIM 之所以比 DDPM 抗跳步，是因为它的每步更新是确定性的、不依赖噪声日程的逐步匹配。
- **它仍然是一阶方法**。DDIM 的更新式本质上是把 ODE 的一小段用一条直线近似；想再往下压步数，就得换更高阶的求解器（如 DPM-Solver 一类），那是另一个话题。
- **它不改模型**。这是 DDIM 最实用的地方：已经训好的 DDPM，只要换一个 sampler 函数、换一个时间表，就能加速，参数一个都不用动。

## 小结

- **慢的根源是假设，不是物理**。采样要 1000 步，是因为要模拟前向那条马尔可夫链。
- **目标函数只认边缘分布**。$L_{\text{simple}}$ 不依赖联合分布，所以前向过程可以随便换——这是 DDIM 全部推论的支点。
- **用 $\sigma$ 索引一族前向过程**。引入超参数向量 $\sigma$，保持 $q(x_t\mid x_0)$ 不变（归纳法证明），于是模型可以直接复用。
- **$\sigma$ 是采样器的旋钮**。取 DDPM 值还原马尔可夫采样；取零得到确定性采样，即 DDIM。
- **respacing 把训练步数与采样步数解耦**。在子序列 $\tau$ 上采样，1000 步可以只走 10~50 步；代价是离散化误差变大，DDIM 比 DDPM 更抗这个代价。
- **代码上只动三处**：`training_losses` 不动、`ddim_sample` 按式 (12) 写、`respace.py` 换 `betas` 并做时间步映射。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| DDPM | 去噪扩散概率模型，用马尔可夫链加噪、用马尔可夫链去噪，采样步数等于训练步数 |
| 非马尔可夫前向过程 | 条件分布里额外依赖 $x_0$，不再是一条链；只要边缘分布不变，训练目标照样能用 |
| $\sigma$（sigma 向量） | 索引一族前向过程的超参数，不参与训练，只影响采样时的均值和方差 |
| $\eta$（eta） | 代码里控制 $\sigma$ 的系数，$\eta=0$ 是 DDIM、$\eta=1$ 是 DDPM |
| DDIM | 隐式概率扩散模型：用 DDPM 目标训练、但生成过程确定的模型（$\sigma=0$） |
| respacing | 在 $1..T$ 里取子序列 $\tau$ 采样，训练步数与采样步数解耦 |
| 采样轨迹 | 采样实际走过的时间点序列，长度 $S$ 可远小于 $T$ |
| $L_{\text{simple}}$ | DDPM 的简化损失 $\lVert\epsilon-\epsilon_\theta(x_t,t)\rVert^2$，只依赖边缘分布 |
| FID | 用预训练特征比较生成分布与真实分布的距离，越低越好 |
