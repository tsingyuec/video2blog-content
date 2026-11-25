# VAE 的损失函数从哪来：ELBO 拆成重建项与 KL 正则项

> 视频来源：[VAE算法讲解（变分自编码器 Variational Auto-Encoder）](https://www.bilibili.com/video/BV1xFxMz1EMS/)（Bilibili，约 30 分钟，含 PyTorch 实现）
> 导读：这支视频先用「隐空间为什么有空洞」把 VAE 的损失函数**猜**出来，再用最大似然 + Jensen 不等式把它**推**出来，最后把 KL 项在高斯假设下逐项积出解析式，得到能直接写进代码的两项损失。本文只讲目标函数这一条线：近似后验、ELBO、重建项与 KL 项、高斯 KL 的闭式解；网络结构与重参数化技巧分别见 2.1.2 与 2.1.10，本文只在必要处回指。

## 本讲要解决的核心问题（SCQA）

**背景**：我们想生成人脸图片。最直接的想法是学一个概率密度 $p(x)$，然后从里面采样。但图像空间的维度高得离谱（一张 100×100 的彩色图就是 3 万个维度），真正的图像分布极其复杂，既写不出解析式，也不好采样。

**冲突**：引入低维隐变量 $z$ 可以绕开这个困难——先采一个低维的 $z$，再用神经网络把它映射成图片。可是这样一来，训练目标就变成了「让解码器生成真实数据的概率最大」，而这个概率需要对所有 $z$ 积分，同样算不出来。

**疑问**：既然 $\log p_\theta(x)$ 算不出来，我们到底在优化什么？那个「重建损失 + KL 损失」的两项损失是从哪来的，为什么它俩一个管还原、一个管正则？

**回答（中心思想）**：VAE 的损失是**负 ELBO**。用编码器 $q_\phi(z\mid x)$ 做近似后验，对 $\log p_\theta(x)$ 用 Jensen 不等式可得

$$
\log p_\theta(x)\ \ge\ \mathbb{E}_{q_\phi(z\mid x)}\big[\log p_\theta(x\mid z)\big]-D_{KL}\big(q_\phi(z\mid x)\,\Vert\,p(z)\big)
$$

右边就是 ELBO。取负号作为损失，就得到两项：**重建项**（让解码器把采到的 $z$ 还原成 $x$）与 **KL 正则项**（让编码器输出的分布贴近先验 $p(z)$）。在高斯假设下，KL 项有闭式解 $\frac{1}{2}\sum_i\left(\sigma_i^2+\mu_i^2-\log\sigma_i^2-1\right)$，可以直接写进代码。

## 一、为什么需要隐变量

### 1.1 直接学 p(x) 的两个死结

视频开篇先把「图片生成」这件事的本质摆出来[【跳转到 00:05】](https://www.bilibili.com/video/BV1xFxMz1EMS/?t=5)：一张黑白人脸图由几万个像素构成，每个像素的灰度值可以看成一个随机变量，整张照片就是这几万个随机变量的联合分布。在这片高维空间里，真正像人脸的点极其稀少，几乎全是噪声。

![图片生成问题的本质：高维空间里人脸只占极小一块，而 p(x) 既复杂到无法求解，也不好采样](assets/VAE%20的损失函数从哪来：ELBO%20拆成重建项与%20KL%20正则项/00030.webp)

于是有两个死结[【跳转到 00:55】](https://www.bilibili.com/video/BV1xFxMz1EMS/?t=55)：

1. **分布太复杂**：它不像正态分布、均匀分布、Laplace 分布那样几个参数就能写完，复杂到无法求解；
2. **就算求出来也不好采样**：即使拿到了 $p(x)$ 的表达式，也很难从中抽样本。

### 1.2 用低维隐变量绕过去

解法是引入**隐变量**：不从像素层面描述一张脸，而是用「头发长短、脸的宽度、眼睛大小、鼻子高度」这类少量属性来描述，比如用 128 个隐变量。这些隐变量不必人工定义，可以让神经网络自己学，并且规定它们服从一个简单分布（比如标准正态），这样**每一次采样都是有效采样**。再从隐变量到真实图片，中间那个映射交给神经网络拟合[【跳转到 01:50】](https://www.bilibili.com/video/BV1xFxMz1EMS/?t=110)。

一句话：隐变量维度低、好采样，生成就变成了「先采 $z$，再确定性/随机地映射成 $x$」。

### 1.3 普通自编码器为什么不够

学过自编码器的同学会问：训练一个自编码器，只取解码器来生成不就行了？答案是否定的[【跳转到 03:55】](https://www.bilibili.com/video/BV1xFxMz1EMS/?t=235)。

![普通自编码器的隐空间：每张训练图只是一个确定的点，点与点之间大片区域解码出来都是噪声](assets/VAE%20的损失函数从哪来：ELBO%20拆成重建项与%20KL%20正则项/00265.webp)

原因是自编码器的编码器给每张训练图输出一个**确定的点**，隐空间里只有极少数点能被解码器还原成图片，其余区域采样出来都是噪声。自编码器的结构、瓶颈与重建误差见 2.1.1，这里只借用它的结论。

## 二、VAE 的两步改造：输出分布，再把分布拉向标准正态

### 2.1 第一步：编码器输出一个分布

VAE 的第一个改动是让编码器输出的不是点，而是一个**正态分布**，再从这个分布里采样一个点送进解码器[【跳转到 04:50】](https://www.bilibili.com/video/BV1xFxMz1EMS/?t=290)。这样有效可采样的区域大大增加；如果某个采样点同时落在两张训练图各自的分布里，解码器就被要求同时兼顾两者的特征，于是能生成训练集里不存在的新脸。

### 2.2 第二步：把所有分布拉向标准正态

但每个样本的分布均值方差各不相同，覆盖区域也不一样，隐空间里仍有很多空洞。VAE 的第二个改动是：**让所有训练样本经编码器得到的多元正态分布都尽量靠近多元标准正态分布**，且各维独立[【跳转到 06:30】](https://www.bilibili.com/video/BV1xFxMz1EMS/?t=390)。

![VAE 把每个样本的分布都拉向隐空间中心的标准正态，于是从标准正态里随便采一个 z 都能解码出合理图片](assets/VAE%20的损失函数从哪来：ELBO%20拆成重建项与%20KL%20正则项/00390.webp)

这样一来，生成时直接从标准正态里采样，就总能解码出一张人脸。而「尽量靠近」这四个字，正是后面 KL 项的来源。

### 2.3 符号约定

视频随后定义了后面要用的符号[【跳转到 08:20】](https://www.bilibili.com/video/BV1xFxMz1EMS/?t=500)：

![符号定义：编码器给出 q_φ(z|x)，隐空间先验 p(z)，解码器给出 p_θ(x|z)](assets/VAE%20的损失函数从哪来：ELBO%20拆成重建项与%20KL%20正则项/00500.webp)

| 符号 | 含义 |
| --- | --- |
| $x$ | 输入的人脸图片 |
| $q_\phi(z\mid x)$ | 编码器给出的条件分布，$\phi$ 是编码器网络参数 |
| $p(z)$ | 我们期望的隐变量分布，取标准多元正态 |
| $p_\theta(x\mid z)$ | 解码器给出的条件分布，$\theta$ 是解码器网络参数 |

编码器要输出正态分布的两个参数：均值 $\mu$（可正可负）和方差 $\sigma^2$（必须为正）。做法是让网络输出 $\alpha$，再用 $\sigma^2=e^{\alpha}$ 保证非负，所以网络原始输出其实是 $\log\sigma^2$[【跳转到 07:25】](https://www.bilibili.com/video/BV1xFxMz1EMS/?t=445)。解码器这一侧，视频只取正态分布的均值作为输出图片，不再额外采样。

## 三、先猜出来：两项损失各管什么

到这里，视频先用直观方式把损失「猜」出来[【跳转到 11:49】](https://www.bilibili.com/video/BV1xFxMz1EMS/?t=709)：

$$
\mathcal{L}_{\text{VAE}}=\mathcal{L}_{\text{rec}}+\mathcal{L}_{KL}
$$

![两项损失的直观来源：重建损失横跨编码器—解码器，KL 损失作用在隐空间上](assets/VAE%20的损失函数从哪来：ELBO%20拆成重建项与%20KL%20正则项/00734.webp)

- **重建损失 $\mathcal{L}_{\text{rec}}$**：要求重建图片尽可能和原始输入一致，对应自编码器原本的 MSE；
- **KL 损失 $\mathcal{L}_{KL}$**：要求每张图片生成的分布尽可能接近标准多元正态。

视频特别指出，这两项在实际训练中是**互相博弈**的[【跳转到 12:14】](https://www.bilibili.com/video/BV1xFxMz1EMS/?t=734)：要让重建更准，就需要在隐空间里把不同人脸尽量区分开、离得远一些；而 KL 项偏要把所有分布都挤到标准正态附近。这个张力正是 VAE 隐空间既连续又能保留信息的原因。

> 补充一句（视频未涉及）：后来 β-VAE 就是给 KL 项乘一个系数 $\beta$，把这条张力显式地做成可调的旋钮——$\beta$ 大则隐空间更规整、重建更糊。

## 四、再推出来：从最大似然到 ELBO

直观归直观，严谨的做法还是从最大似然出发[【跳转到 13:27】](https://www.bilibili.com/video/BV1xFxMz1EMS/?t=807)。给定样本 $x_1,\dots,x_N$，希望解码器生成每个样本的概率都大，于是最大化连乘（似然）：

$$
\max_\theta\ \prod_{i=1}^{N}p_\theta(x_i)
$$

连乘取 log 变成连加（不改变极值点），再加负号变成最小化，就得到损失：

$$
\mathcal{L}=-\sum_{i=1}^{N}\log p_\theta(x_i)
$$

![优化目标：最大化样本的联合似然，取 log、加负号后变成最小化负对数似然](assets/VAE%20的损失函数从哪来：ELBO%20拆成重建项与%20KL%20正则项/00820.webp)

### 4.1 单项 p(x) 的积分形式

对单个样本，$p_\theta(x)$ 要对隐空间里每个 $z$ 积分：

$$
p_\theta(x)=\int p(z)\,p_\theta(x\mid z)\,dz
$$

![p_θ(x) 等于「取到 z 的概率」乘「取到这个 z 时生成 x 的概率」，再对 z 积分](assets/VAE%20的损失函数从哪来：ELBO%20拆成重建项与%20KL%20正则项/00878.webp)

这个积分要对整个隐空间做，同样算不出来——这就是必须引入 ELBO 的原因。

### 4.2 乘除一个 q，凑出期望

第二步，引入编码器：在积分里同时乘、除以 $q_\phi(z\mid x)$[【跳转到 14:38】](https://www.bilibili.com/video/BV1xFxMz1EMS/?t=878)：

$$
p_\theta(x)=\int q_\phi(z\mid x)\frac{p(z)\,p_\theta(x\mid z)}{q_\phi(z\mid x)}\,dz
=\mathbb{E}_{q_\phi(z\mid x)}\left[\frac{p(z)\,p_\theta(x\mid z)}{q_\phi(z\mid x)}\right]
$$

这一步只是恒等变形，但把积分写成了「在 $q_\phi(z\mid x)$ 下求期望」，而期望可以用采样估计。

### 4.3 Jensen 不等式给出下界

接着对 log 用 **Jensen 不等式**：log 是凹函数，所以「log 的期望」小于等于「期望的 log」，即 $\log\mathbb{E}[X]\le\mathbb{E}[\log X]$。于是

$$
\log p_\theta(x)\ \ge\ \mathbb{E}_{q_\phi(z\mid x)}\left[\log\frac{p(z)\,p_\theta(x\mid z)}{q_\phi(z\mid x)}\right]
$$

![推导链条：积分形式 → 乘除 q 写成期望 → Jensen 不等式把 log 挪到期望里面](assets/VAE%20的损失函数从哪来：ELBO%20拆成重建项与%20KL%20正则项/00928.webp)

不等式右边就是 ELBO。注意方向：**ELBO 是 $\log p_\theta(x)$ 的下界**，所以最大化 ELBO 就是在最大化似然的下界。

### 4.4 拆成两项

对 ELBO 里的 log 做除法变减法、期望拆成两个期望[【跳转到 15:28】](https://www.bilibili.com/video/BV1xFxMz1EMS/?t=928)：

$$
\text{ELBO}=\mathbb{E}_{q}\left[\log\frac{q_\phi(z\mid x)}{p(z)}\right]-\mathbb{E}_{q}\left[\log p_\theta(x\mid z)\right]
$$

第一项正是 $q_\phi(z\mid x)$ 对 $p(z)$ 的 KL 散度。取负号得到损失：

$$
\mathcal{L}_{\text{VAE}}=D_{KL}\big(q_\phi(z\mid x)\,\Vert\,p(z)\big)-\mathbb{E}_{q_\phi(z\mid x)}\big[\log p_\theta(x\mid z)\big]
$$

![推导的最后几行：第一项写成 KL 散度，第二项是重建期望，合起来就是 VAE 的损失](assets/VAE%20的损失函数从哪来：ELBO%20拆成重建项与%20KL%20正则项/00953.webp)

![视频把最终结果单独框出来：L_VAE = KL(q_φ(z|x)‖p(z)) − E[log p_θ(x|z)]](assets/VAE 的损失函数从哪来：ELBO 拆成重建项与 KL 正则项/01003.webp)

> 视频口播到这里时把第一项说成「解码器对一个 X 生成的分布」，从推导看应是**编码器**给出的 $q_\phi(z\mid x)$ 与先验 $p(z)$ 的 KL——KL 约束的是隐空间里的分布，和解码器无关。

### 4.5 两项与直观版本对上

- 第二项前面有负号，在损失里就是**越大越好**：给定 $x$，编码器把它编成一个分布，这个分布里任意采一个 $z$，都要让生成 $x$ 的概率最大。这就是重建项。
- log 在这里不影响函数的单调性——有没有 log，让这一项最大的 $\theta$ 都一样。所以实际实现时可以直接用逐像素 MSE 代替 $\log p_\theta(x\mid z)$[【跳转到 16:18】](https://www.bilibili.com/video/BV1xFxMz1EMS/?t=978)。
- 第一项就是 KL 正则项，把编码器输出拉向标准正态。

于是「猜」出来的两项损失与「推」出来的式子完全一致。

## 五、高斯情形：把 KL 项积出解析式

KL 项里还有积分，不能直接写进代码。视频在**对角高斯**假设下把它算成闭式解[【跳转到 17:08】](https://www.bilibili.com/video/BV1xFxMz1EMS/?t=1028)。

### 5.1 假设与两条 log 密度

假设编码器输出的 $z$ 各维独立，每维服从 $\mathcal{N}(\mu_i,\sigma_i^2)$；先验 $p(z)=\mathcal{N}(0,I)$。KL 的定义展开为

$$
D_{KL}\big(q_\phi(z\mid x)\,\Vert\,p(z)\big)=\int q_\phi(z\mid x)\big(\log q_\phi(z\mid x)-\log p(z)\big)\,dz
$$

![KL 展开成积分，并把 log q_φ(z|x) 与 log p(z) 分别写成对角高斯的显式形式](assets/VAE%20的损失函数从哪来：ELBO%20拆成重建项与%20KL%20正则项/01053.webp)

把两个密度函数代入、log 内连乘化连加、消去指数与 log，得到[【跳转到 19:13】](https://www.bilibili.com/video/BV1xFxMz1EMS/?t=1153)：

$$
\log q_\phi(z\mid x)=-\frac{d}{2}\log(2\pi)-\frac{1}{2}\sum_{i=1}^{d}\log\sigma_i^2-\frac{1}{2}\sum_{i=1}^{d}\frac{(z_i-\mu_i)^2}{\sigma_i^2}
$$

$$
\log p(z)=-\frac{d}{2}\log(2\pi)-\frac{1}{2}\sum_{i=1}^{d}z_i^2
$$

![两条 log 密度的整理结果：对角高斯下各维独立，log 内连乘变连加](assets/VAE%20的损失函数从哪来：ELBO%20拆成重建项与%20KL%20正则项/01203.webp)

### 5.2 三个积分

两式相减，常数项 $-\frac{d}{2}\log(2\pi)$ 正好抵消，剩下三部分分别积分[【跳转到 20:03】](https://www.bilibili.com/video/BV1xFxMz1EMS/?t=1203)：

1. $\frac{1}{2}\sum_i \mathbb{E}[z_i^2]$：由方差公式 $\mathrm{Var}(z_i)=\mathbb{E}[z_i^2]-\mu_i^2$ 得 $\mathbb{E}[z_i^2]=\sigma_i^2+\mu_i^2$；
2. $-\frac{1}{2}\sum_i \log\sigma_i^2$：它是常数，常数的期望还是它自己；
3. $-\frac{1}{2}\sum_i \mathbb{E}\left[\frac{(z_i-\mu_i)^2}{\sigma_i^2}\right]$：括号里的期望就是方差 $\sigma_i^2$，除以 $\sigma_i^2$ 得 1。

![三个积分分别求值：z_i² 的期望拆成方差加均值平方，log σ² 是常数，中心化平方的期望就是方差](assets/VAE%20的损失函数从哪来：ELBO%20拆成重建项与%20KL%20正则项/01278.webp)

三部分相加，得到 KL 的闭式解：

$$
\mathcal{L}_{KL}=\frac{1}{2}\sum_{i=1}^{d}\left(\sigma_i^2+\mu_i^2-\log\sigma_i^2-1\right)
$$

其中 $d$ 是隐空间维度。这个式子里只有编码器输出的 $\mu_i$ 和 $\sigma_i^2$，没有任何积分或采样，可以直接写进损失函数。

### 5.3 最终的损失

把两项合起来[【跳转到 21:59】](https://www.bilibili.com/video/BV1xFxMz1EMS/?t=1319)：

$$
\mathcal{L}_{\text{VAE}}=\underbrace{\text{MSE}(x,\hat{x})}_{\mathcal{L}_{\text{rec}}}+\underbrace{\frac{1}{2}\sum_{i=1}^{d}\left(\sigma_i^2+\mu_i^2-\log\sigma_i^2-1\right)}_{\mathcal{L}_{KL}}
$$

![最终的 VAE 损失：重建项用 MSE，KL 项用高斯闭式解，图中同时标出两项各自作用的位置](assets/VAE%20的损失函数从哪来：ELBO%20拆成重建项与%20KL%20正则项/01319.webp)

这张图把两项的职责画得很清楚：重建损失横跨编码器与解码器，KL 损失只作用在隐空间。$\mu$ 和 $\log\sigma^2$ 都是编码器的输出，$d$ 是隐空间维度。

## 六、落到代码：两项在实现里长什么样

视频后半段是 PyTorch 实现，网络结构（卷积下采样、转置卷积上采样、隐空间维度 128）属于 2.1.2 的内容，这里只保留与目标函数相关的部分。

- 编码器输出两个向量：均值 $\mu$ 和方差的 log 值 $\log\sigma^2$；解码器最后一层用 sigmoid 把像素归一到 $[0,1]$，输入侧用 `ToTensor` 把 0–255 归一化到同一区间，两边尺度对齐，MSE 才有意义[【跳转到 26:34】](https://www.bilibili.com/video/BV1xFxMz1EMS/?t=1594)。
- 采样用重参数化：把 $\log\sigma^2$ 换成标准差，采一个标准正态噪声，再算 $z=\mu+\sigma\cdot\epsilon$。这一步的细节见 2.1.10，这里只需知道它让采样节点可导[【跳转到 27:07】](https://www.bilibili.com/video/BV1xFxMz1EMS/?t=1627)。
- `loss` 函数就两行：第一部分是重建的 MSE，第二部分按上面的闭式解算 KL，然后相加[【跳转到 28:14】](https://www.bilibili.com/video/BV1xFxMz1EMS/?t=1694)。
- 训练循环里分别统计 `recon` 与 `kld` 两个数并打印，每 5 个 epoch 保存两张图：一张是训练图的重建，一张是从隐空间随机采样全新生成的图[【跳转到 29:31】](https://www.bilibili.com/video/BV1xFxMz1EMS/?t=1771)。分开记录这两项很关键——只看总损失，看不出是重建变好还是 KL 在退化。

## 小结

- 直接学 $p(x)$ 有两个死结：分布太复杂写不出来，写出来也不好采样；引入低维隐变量后，生成变成「先采 $z$ 再解码」。
- 普通自编码器的隐空间有大量空洞，因为编码器只输出确定的点；VAE 让编码器输出**分布**，并把这些分布拉向标准正态。
- 训练目标是最大化样本似然 $\prod_i p_\theta(x_i)$，但单项 $p_\theta(x)=\int p(z)p_\theta(x\mid z)dz$ 算不出来。
- 在积分里乘除 $q_\phi(z\mid x)$ 写成期望，再用 **Jensen 不等式**得到 $\log p_\theta(x)\ge$ ELBO；取负号就是 VAE 的损失。
- ELBO 拆成两项：$D_{KL}(q_\phi(z\mid x)\Vert p(z))$ 是**正则项**，把隐空间拉向标准正态；$-\mathbb{E}_q[\log p_\theta(x\mid z)]$ 是**重建项**，要求采到的 $z$ 能还原 $x$。
- 两项互相博弈：重建要求把不同样本在隐空间里分开，KL 要求把它们都挤到标准正态附近。
- 对角高斯假设下 KL 有闭式解 $\frac{1}{2}\sum_i(\sigma_i^2+\mu_i^2-\log\sigma_i^2-1)$，与 MSE 重建项相加就能直接训练。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| 隐变量（latent variable） | 低维、可采样的变量，编码数据的属性，解码器由它生成观测 |
| 近似后验 $q_\phi(z\mid x)$ | 编码器给出的条件分布，用来近似算不出的真实后验 |
| 先验 $p(z)$ | 隐变量的预设分布，VAE 里取标准多元正态 |
| 似然 $p_\theta(x\mid z)$ | 解码器给出的分布，衡量给定 $z$ 时生成 $x$ 的可能性 |
| Jensen 不等式 | 凹函数下 $\log\mathbb{E}[X]\le\mathbb{E}[\log X]$，用来把 log 挪进期望得到下界 |
| ELBO | evidence lower bound，$\log p_\theta(x)$ 的下界，最大化它即最大化似然下界 |
| 重建项 | $-\mathbb{E}_q[\log p_\theta(x\mid z)]$，实现时常取逐像素 MSE |
| KL 正则项 | $D_{KL}(q_\phi(z\mid x)\Vert p(z))$，把编码器输出拉向标准正态 |
| 对角高斯 KL | 各维独立高斯时 KL 的闭式解，只含 $\mu_i$ 与 $\sigma_i^2$ |