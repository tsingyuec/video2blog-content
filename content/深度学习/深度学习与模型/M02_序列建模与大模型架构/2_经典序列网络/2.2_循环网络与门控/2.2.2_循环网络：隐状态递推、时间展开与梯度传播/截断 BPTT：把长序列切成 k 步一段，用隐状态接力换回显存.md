# 截断 BPTT：把长序列切成 k 步一段，用隐状态接力换回显存

> 视频来源：[CS 152 NN — 21: RNNs: Truncated BPTT](https://www.youtube.com/watch?v=CrMgI3OiNnw)（YouTube · Neil Rhodes，Harvey Mudd College 神经网络课程）｜时长约 25 分钟
> 导读：这一讲只回答一个问题——序列很长时，完整的 BPTT 为什么跑不动，以及截断 BPTT 的四种配置各付出什么代价。前半段讲 $k_1, k_2$ 两个常数的含义与接缝问题，后半段算一遍张量形状账，最后看 fastai 在文本 RNN 上是怎么落地的。本文承接「循环网络：隐状态递推、按时间展开与梯度传播」一节，默认读者已经知道隐状态递推和梯度沿时间连乘。

## 本讲要解决的核心问题（SCQA）

**背景**：BPTT 的做法是先把整条序列前向跑完，再从最后一个时间步一路反向传播回第一个时间步。序列长度 $n$ 不大时，这没有任何问题。

**冲突**：$n$ 一大，两件事同时出问题。第一，梯度要穿过整条链，越靠前越容易消失或爆炸。第二，也是更要命的一条——**反向传播需要每一步的激活值，这些激活全都得留在显存里**。$n$ 很长、隐藏维度 $l$ 又很大时，显存可能直接不够；就算够，也会把 batch size 压得很小。

**疑问**：能不能不把整条序列一次算完？如果切成几段分别算，段与段之间的历史怎么接上？切段之后梯度还能不能跨段传？框架支持到什么程度？

**回答（中心思想）**：**截断 BPTT 用两个常数 $k_1, k_2$ 描述"前向走几步、反向退几步"：$k_1$ 决定显存里要留多少激活，$k_2$ 决定梯度能回溯多远。$k_1 = k_2 = k$ 是最常用的一档，它把长序列切成 $k$ 步一段，每段只保留 $k$ 份激活，段与段之间靠"把上一段输出的 $h_k$ 当作下一段的 $h_0$"来接力——注意不能用零初始化，否则模型会以为序列重新开始了。代价是段与段之间出现一道"接缝"，梯度不再跨缝回传。**

---

## 一、完整 BPTT 的两个代价

先把 RNN 的展开图摆出来：时间步 1 到时间步 $n$，$h_0$ 进来、$h_1$ 到 $h_{n-1}$ 依次传递，$x_1$ 进、$\hat{y}_1$ 出，$x_2$ 进、$\hat{y}_2$ 出，一直到最后一步 [【跳转到 00:00】](https://www.youtube.com/watch?v=CrMgI3OiNnw&t=0)。

![RNN 展开图：$h_0$ 进、$h_1 \dots h_{n-1}$ 依次传递，每个时间步吃一个 $x_i$、吐一个 $\hat{y}_i$](assets/截断%20BPTT：把长序列切成%20k%20步一段，用隐状态接力换回显存/00132.webp)

传统的 BPTT 就是：**沿着整条序列长度一路前向跑完，然后一路反向传播回去** [【跳转到 00:38】](https://www.youtube.com/watch?v=CrMgI3OiNnw&t=38)。$n$ 变大之后，这么做有两个潜在问题。

### 1.1 问题一：梯度要穿过整条链

如果梯度要沿着所有 $h$ 一路传到最前面，那么在路径早期就可能出现**梯度消失或梯度爆炸**，序列越长越明显 [【跳转到 01:04】](https://www.youtube.com/watch?v=CrMgI3OiNnw&t=64)。

这一条与上一节讲过的连乘是同一件事，这里不重复推导。讲者的态度是：这个问题大家都知道，但**它不是本节要处理的重点**。

### 1.2 问题二（更重要）：激活值全得留在显存里

第二个问题讲者明确说"更重要"：**完整 BPTT 在空间上非常昂贵**。原因是反向传播需要用到每一步的激活值，所以前向过程中每一步的激活都必须保存下来 [【跳转到 01:15】](https://www.youtube.com/watch?v=CrMgI3OiNnw&t=75)。

这些激活全都还在 GPU 上。于是：

- 如果 $n$ 极大，可能**物理上就放不下**；
- 就算放得下，也会**严重限制 batch size**——因为进来的不是一个序列，而是一整批长度为 $n$ 的序列 [【跳转到 01:38】](https://www.youtube.com/watch?v=CrMgI3OiNnw&t=98)。

这就是截断 BPTT 出场的理由：**它首先是一个显存优化手段，其次才是一个梯度路径的取舍。**

---

## 二、截断 BPTT 的定义：两个常数 $k_1, k_2$

截断 BPTT 定义两个常数 $k_1$ 和 $k_2$，两者都落在 $1$ 到 $n$ 之间（$n$ 是序列长度）。记作 $\mathrm{BPTT}(k_1, k_2)$：**$k_1$ 是前向走多少个时间步，$k_2$ 是反向退多少个时间步** [【跳转到 02:03】](https://www.youtube.com/watch?v=CrMgI3OiNnw&t=123)。

下面四种配置，讲者逐个过了一遍。

### 2.1 $\mathrm{BPTT}(n, n)$：就是传统 BPTT

前向走 $n$ 步、反向退 $n$ 步，等价于完整的 BPTT。这是基准线，也是显存最贵的一档 [【跳转到 02:37】](https://www.youtube.com/watch?v=CrMgI3OiNnw&t=157)。

### 2.2 $\mathrm{BPTT}(1, n)$：更新最勤，代价是 $O(n^2)$

这一档是：先前进 1 步，然后往回退 1 步；再前进到第 2 步，往回退 2 步；再前进到第 3 步，往回退 3 步……一直到第 $n$ 步、退 $n$ 步 [【跳转到 03:02】](https://www.youtube.com/watch?v=CrMgI3OiNnw&t=182)。

![$\mathrm{BPTT}(1,n)$ 的走法：每前进一格就多退一格，累计前向 $n$ 步、反向 $1+2+\dots+n$ 步](assets/截断%20BPTT：把长序列切成%20k%20步一段，用隐状态接力换回显存/00262.webp)

累计算一下：前向总共还是 $n$ 步，和传统 BPTT 一样；但反向是 $1 + 2 + 3 + \dots + n$ 步，也就是**$O(n^2)$ 次反向时间步** [【跳转到 03:32】](https://www.youtube.com/watch?v=CrMgI3OiNnw&t=212)。

它的好处是**早期梯度被更新了很多次**：在早期时间步上，权重矩阵被反复更新，某种意义上等于**过度强调**了早期时间步——因为这些权重是基于早期输入更新的，比后期更新得更多 [【跳转到 03:57】](https://www.youtube.com/watch?v=CrMgI3OiNnw&t=237)。

### 2.3 $\mathrm{BPTT}(k, k)$：最常用的一档

这一档是：前进 $k$ 步，退 $k$ 步；再前进 $k$ 步，退 $k$ 步；再前进 $k$ 步，退 $k$ 步……如果 $n$ 不是 $k$ 的整数倍，最后再做一次更小的步数，把剩下几个时间步覆盖掉 [【跳转到 04:22】](https://www.youtube.com/watch?v=CrMgI3OiNnw&t=262)。

![$\mathrm{BPTT}(k,k)$ 的走法：每次前进 $k$ 步、后退 $k$ 步，一段一段往前推](assets/截断%20BPTT：把长序列切成%20k%20步一段，用隐状态接力换回显存/00474.webp)

这一档效果相当好，原因是它**限制了每次要做的传播量**：

- 前向仍然要走完 $n$ 步（这一点没变），但**显存里只需要保留 $k$ 份激活**，所以可以把 batch size 开大 [【跳转到 05:08】](https://www.youtube.com/watch?v=CrMgI3OiNnw&t=308)。

代价是出现了一道**接缝（seam）**：从第 $k+2$ 步到第 $k-2$ 步之间，误差不再往回传 [【跳转到 05:33】](https://www.youtube.com/watch?v=CrMgI3OiNnw&t=333)。

![$\mathrm{BPTT}(k,k)$ 的接缝：段与段之间有一段梯度传不过去，绿色圈标出的就是被切断的位置](assets/截断%20BPTT：把长序列切成%20k%20步一段，用隐状态接力换回显存/00333.webp)

### 2.4 $\mathrm{BPTT}(k, 2k)$：让反向传播跨过接缝

要消掉接缝，一个办法是让反向走得比前向更远：前进 $k$ 步，然后往回退最多 $2k$ 步；再前进 $k$ 步，再退 $2k$ 步；如此往复 [【跳转到 05:46】](https://www.youtube.com/watch?v=CrMgI3OiNnw&t=346)。

![$\mathrm{BPTT}(k,2k)$：反向窗口比前向窗口宽一倍，两段的反向区间互相重叠，接缝被覆盖掉](assets/截断%20BPTT：把长序列切成%20k%20步一段，用隐状态接力换回显存/00365.webp)

这样两段的反向区间就**重叠**了，于是不存在"某几个时间步完全没有被反向传播覆盖"的情况 [【跳转到 06:05】](https://www.youtube.com/watch?v=CrMgI3OiNnw&t=365)。

### 2.5 框架支持到什么程度

讲者给了一张很实用的对照 [【跳转到 06:17】](https://www.youtube.com/watch?v=CrMgI3OiNnw&t=377)：

| 配置 | PyTorch 是否直接支持 | 说明 |
| --- | --- | --- |
| $\mathrm{BPTT}(n, n)$ | 支持 | 直接把整条序列喂进去 |
| $\mathrm{BPTT}(k, k)$ | 支持 | 手动切段 + 传 $h_0$ |
| $\mathrm{BPTT}(1, n)$ | 不支持 | 需要自己实现 |
| $\mathrm{BPTT}(k, 2k)$ | 不支持 | 需要自己实现 |

换句话说，**PyTorch 实际只支持 $k_1 = k_2$ 的情形**；想用 $k_2 \neq k_1$ 的配置，得自己写 [【跳转到 06:34】](https://www.youtube.com/watch?v=CrMgI3OiNnw&t=394)。

![黑板上的对照：$\mathrm{BPTT}(n,n)$ 近似于传统 BPTT，$\mathrm{BPTT}(1,n)$ 与 $\mathrm{BPTT}(k,2k)$ 需要自己实现](assets/截断%20BPTT：把长序列切成%20k%20步一段，用隐状态接力换回显存/00394.webp)

---

## 三、$k, k$ 到底怎么跑：切段 + 隐状态接力

### 3.1 $(n,n)$ 的写法很直接

$\mathrm{BPTT}(n,n)$ 最简单：把整条序列一次性喂给 RNN，$x_1$ 到 $x_n$ 全在里面。$h_0$ 不传的话默认取零向量，然后一路跑完就结束了 [【跳转到 07:03】](https://www.youtube.com/watch?v=CrMgI3OiNnw&t=423)。

### 3.2 $(k,k)$ 要切段，但**不能**用零初始化第二段

$\mathrm{BPTT}(k,k)$ 的做法是把输入**切成若干段**：比如一段长度 300 的输入，切成三段各 100 [【跳转到 07:26】](https://www.youtube.com/watch?v=CrMgI3OiNnw&t=446)。

问题立刻来了：**"一次算到 $n$"和"分三次各算 $n/3$"是同一件事吗？** [【跳转到 07:39】](https://www.youtube.com/watch?v=CrMgI3OiNnw&t=459)

如果第二段也拿零向量当 $h_0$，那就等于告诉 RNN"这是一条新序列的开头"，**前面 $k$ 步的历史全丢了** [【跳转到 08:44】](https://www.youtube.com/watch?v=CrMgI3OiNnw&t=524)。

正确的做法是：**把第一段输出的 $h_k$ 取出来，作为第二段输入的 $h_0$**。这样对第二段这次调用来说，它只有 $k$ 个元素，但它的"第一段历史"是 $h_k$——而 $h_k$ 已经压缩了前 $k$ 个输入的全部信息。于是处理第 $k+1$ 个输入时，模型是**带着完整历史**去解释它的 [【跳转到 09:09】](https://www.youtube.com/watch?v=CrMgI3OiNnw&t=549)。

![把上一段的 $h_k$ 接到下一段的 $h_0$：$h_0$ 只在第一段用零，之后都是接力](assets/截断%20BPTT：把长序列切成%20k%20步一段，用隐状态接力换回显存/01271.webp)

这件事之所以可行，是因为 RNN 的 API 本来就**显式接收 $h_0$**：不传就默认零，传了就用你给的。同时它的输出除了 $\hat{y}$ 之外还包含最终激活层 $h_n$，正好拿来接力 [【跳转到 10:14】](https://www.youtube.com/watch?v=CrMgI3OiNnw&t=614)。

输出里的 $h_n$ 还有第二个用途：**当摘要用**。想知道"这条输入到底让模型学到了什么"，答案就压在 $h_n$ 里 [【跳转到 10:28】](https://www.youtube.com/watch?v=CrMgI3OiNnw&t=628)。

### 3.3 detach：切断还是不切断

在 PyTorch 里，每个 $h_i$ 都是要算梯度的（因为权重矩阵和偏置都要梯度，由它们算出来的东西自然也带梯度）。所以把 $h_n$ 喂给下一次调用时，**要不要 detach，取决于你想用哪种截断策略** [【跳转到 17:32】](https://www.youtube.com/watch?v=CrMgI3OiNnw&t=1052)：

- 做 $\mathrm{BPTT}(k,k)$：**要 detach**。这样上一段的激活图被释放，显存里只留本段的 $k$ 份。
- 做 $\mathrm{BPTT}(k, 2k)$：**不能 detach**。因为反向传播要跨过接缝回到上一段，必须保留上一段（乃至上两段）的计算图 [【跳转到 18:40】](https://www.youtube.com/watch?v=CrMgI3OiNnw&t=1120)。

一句话：**detach 就是"截断"这个动作在代码里的具体形态**；不 detach 就没有截断，显存也就省不下来。

---

## 四、形状账：一次前向到底吃进什么、吐出什么

讲者花了不少时间把张量形状推了一遍，因为**形状对不上是 RNN 实现里最常见的错误来源**。

### 4.1 输入与输出

PyTorch 里输入通常是三维张量：**序列长度 $n$ × batch size × 输入特征数**。每个 $x_i$ 里的元素个数常常是 1（比如词索引），也可以更多（比如三个温度传感器读数就是 3）[【跳转到 11:21】](https://www.youtube.com/watch?v=CrMgI3OiNnw&t=681)。

于是：

- 输入：$n \times \text{batch size} \times \#\text{inputs}$
- 输出 $\hat{y}$：$n \times \text{batch size} \times \#\text{outputs}$
- 输出 $h$：$\text{batch size} \times l$（**没有序列长度这一维**，因为只输出最后一步）[【跳转到 16:09】](https://www.youtube.com/watch?v=CrMgI3OiNnw&t=969)

![黑板上的形状账：input 是 $n \times$ batch size $\times$ #inputs，output 同形但换成 #outputs，output-h 只有 batch size $\times l$](assets/截断%20BPTT：把长序列切成%20k%20步一段，用隐状态接力换回显存/00651.webp)

### 4.2 三个权重矩阵的形状

令隐藏维度为 $l$，则 [【跳转到 12:18】](https://www.youtube.com/watch?v=CrMgI3OiNnw&t=738)：

$$
W_{xh}:\ \#\text{inputs} \times l,\qquad W_{hh}:\ l \times l,\qquad W_{hy}:\ l \times \#\text{outputs}
$$

推一遍就明白为什么：

$$
h_i = g\left(h_{i-1} W_{hh} + x_i W_{xh} + b_h\right)
$$

- $x_i$ 是 $\text{batch size} \times \#\text{inputs}$，乘上 $W_{xh}$（$\#\text{inputs} \times l$）得到 $\text{batch size} \times l$；
- $h_{i-1}$ 是 $\text{batch size} \times l$，乘上 $W_{hh}$（$l \times l$）也得到 $\text{batch size} \times l$；
- 两者相加，再加偏置（$1 \times l$，沿 batch 维广播），过激活函数后形状不变 [【跳转到 14:37】](https://www.youtube.com/watch?v=CrMgI3OiNnw&t=877)。

![隐藏状态公式与每一步的形状标注：$h_{i-1}W_{hh}$ 与 $x_iW_{xh}$ 都是 batch size × l，偏置 1 × l 广播](assets/截断%20BPTT：把长序列切成%20k%20步一段，用隐状态接力换回显存/01095.webp)

### 4.3 隐藏维度 $l$ 的取舍

$l$ 就是"用多少个浮点数来记住历史" [【跳转到 16:53】](https://www.youtube.com/watch?v=CrMgI3OiNnw&t=1013)：

- $l = 1$：整条历史压成一个数，显然非常有限；
- $l$ 变大：记忆容量变大，模型能力变强；
- 但代价是所有矩阵都跟着变大（它们都依赖 $l$），参数更多、更难训、需要更多数据 [【跳转到 17:32】](https://www.youtube.com/watch?v=CrMgI3OiNnw&t=1052)。

---

## 五、工程落地：fastai 的文本 RNN 怎么切

讲者最后用 fastai 的文本 RNN 演示了截断 BPTT 在框架里的样子。你只需要指定一个"序列长度"，也就是上面的 $k$ [【跳转到 19:11】](https://www.youtube.com/watch?v=CrMgI3OiNnw&t=1151)。

### 5.1 切段与 $h$ 接力

假设有三条 Yelp 评论：

```
1: I really liked this shop because it was clean
2: The plumber did a good job
3: Hope to go back again next month
```

fastai 会把它们排成 batch，同时按序列长度切开。若序列长度取 3，那么每条评论被切成若干段，每段 3 个 token [【跳转到 20:37】](https://www.youtube.com/watch?v=CrMgI3OiNnw&t=1237)。

![fastai 把评论排成 batch、再按序列长度切开；左侧标注 input 是 $n \times$ batch size $\times$ #inputs](assets/截断%20BPTT：把长序列切成%20k%20步一段，用隐状态接力换回显存/01237.webp)

喂进 RNN 的张量形状就是 $n \times \text{batch size} \times \#\text{inputs}$，这里 $n=3$、batch size $=3$、每个位置 1 个特征（就是词索引）[【跳转到 21:02】](https://www.youtube.com/watch?v=CrMgI3OiNnw&t=1262)。

接力的规则和第三节讲的一样：**第一段用零作为 $h_0$，之后每一段都用上一段输出的 $h$ 作为自己的 $h_0$** [【跳转到 21:11】](https://www.youtube.com/watch?v=CrMgI3OiNnw&t=1271)。三条评论都跑完之后，再换一批新的 batch [【跳转到 21:29】](https://www.youtube.com/watch?v=CrMgI3OiNnw&t=1289)。

### 5.2 padding 与按长度排序

切段之后有两个副作用要处理：

**第一，段落长度不齐要 padding。** 有些位置没有词，就填 `pad`——这只是词典里一个表示"不是真词"的特殊索引 [【跳转到 22:01】](https://www.youtube.com/watch?v=CrMgI3OiNnw&t=1321)。

**第二，长短混在一起是浪费。** 一千条评论里，有的很短、有的很长。如果把长短塞进同一个 batch，短的那些会被填上大量 padding，纯属浪费。所以 fastai 会**按长度排序**，把长的放一起、短的放一起 [【跳转到 22:37】](https://www.youtube.com/watch?v=CrMgI3OiNnw&t=1357)。长的那些可能需要调用多次 RNN（每次 $k$ 步）才能覆盖完，短的可能两次就够了 [【跳转到 23:02】](https://www.youtube.com/watch?v=CrMgI3OiNnw&t=1382)。

注意这里是**近似排序**而不是严格排序。原因是：每个 epoch 都希望 batch 内容不一样，这种随机性本身就是一种正则化；如果严格按长度排死，每个 epoch 的 batch 就完全一样了 [【跳转到 23:27】](https://www.youtube.com/watch?v=CrMgI3OiNnw&t=1407)。

### 5.3 每个 epoch 抖动序列长度

还有一个更细的处理，直接对应第二节的接缝问题 [【跳转到 23:52】](https://www.youtube.com/watch?v=CrMgI3OiNnw&t=1432)：

因为 $k$ 到 $k+1$ 之间是硬切断的，**梯度永远不会跨过这道缝**。于是 fastai 会**在 epoch 之间微调序列长度**：第一个 epoch 用 3，第二个 epoch 可能用 2，第三个用 4，在你指定的 $k$ 上下浮动。

这样接缝的位置就一直在变，原本"永远传不过去"的那几对时间步，在别的 epoch 里可能就落在同一段内了。讲者的原话是：否则我们永远不会有梯度从第二段传回第一段 [【跳转到 24:42】](https://www.youtube.com/watch?v=CrMgI3OiNnw&t=1482)。

---

## 小结

- **完整 BPTT 的瓶颈首先是显存**：反向传播要用每一步的激活，$n$ 大、$l$ 大时激活占满 GPU，还压死 batch size。梯度消失/爆炸是第二个问题，本节不展开。
- **截断 BPTT 用两个常数描述**：$\mathrm{BPTT}(k_1, k_2)$，$k_1$ 是前向步数（决定显存里留多少激活），$k_2$ 是反向步数（决定梯度回溯多远）。
- **四种配置各有取舍**：$(n,n)$ 是基准；$(1,n)$ 更新最勤但反向是 $O(n^2)$、且过度强调早期时间步；$(k,k)$ 最常用，显存只需 $k$ 份激活；$(k,2k)$ 让反向窗口重叠，消掉接缝。
- **PyTorch 只直接支持 $k_1 = k_2$**；$(1,n)$ 和 $(k,2k)$ 要自己实现。
- **切段的关键是隐状态接力**：第二段绝不能拿零当 $h_0$，必须接上一段的 $h_k$，否则历史全丢。
- **detach 就是"截断"在代码里的形态**：$(k,k)$ 要 detach 才能省显存；$(k,2k)$ 不能 detach，否则梯度跨不过接缝。
- **形状约定**：输入 $n \times \text{batch} \times \#\text{in}$，输出 $n \times \text{batch} \times \#\text{out}$，输出 $h$ 只有 $\text{batch} \times l$；$W_{xh}$ 是 $\#\text{in} \times l$，$W_{hh}$ 是 $l \times l$，$W_{hy}$ 是 $l \times \#\text{out}$。
- **工程上还有两招**：padding + 按长度近似排序以减少填充；每个 epoch 抖动序列长度，让接缝位置变化。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| BPTT | 随时间反向传播，在展开后的 RNN 计算图上做反向传播 |
| 截断 BPTT（truncated BPTT） | 只前向 $k_1$ 步、反向 $k_2$ 步就更新一次，避免整条序列一次算完 |
| 接缝（seam） | $(k,k)$ 截断下两段之间梯度传不过去的位置 |
| $h_0$ 接力 | 把上一段输出的 $h_k$ 当作下一段输入的 $h_0$，保住跨段历史 |
| detach | 切断计算图，让梯度不再往更早的段回传，从而释放那部分激活 |
| 激活值（activation） | 前向过程中每一步的中间结果，反向传播必须用到，是显存的主要开销 |
| 隐藏维度 $l$ | 用多少个浮点数表示历史；越大记忆越强，参数与训练难度也越大 |
| padding | 用特殊索引把不等长序列补齐到同一长度 |
| 近似排序 | 按长度大致分组以减少填充，同时保留每个 epoch 的 batch 随机性 |