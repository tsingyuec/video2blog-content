# n-gram 语言模型：用计数估计序列概率，用平滑对付没见过的组合

> 视频来源：[N-gram Language Models: Full Lecture (Jurafsky & Martin, Chapter 3)](https://www.youtube.com/watch?v=Bw-nefkA4Zg)（YouTube · Qatar AI Institute，按 Jurafsky & Martin《Speech and Language Processing》第三章讲授）｜时长约 41 分钟
> 本文基于视频演说图文稿整理，配图截自视频。这支视频把统计语言模型从"为什么需要"一路讲到"怎么估、怎么评、怎么补救"，正好覆盖 n-gram、马尔可夫假设、最大似然估计、困惑度与平滑四件事。文中公式与数字均取自幻灯片，字幕里的口语碎片已按上下文订正。

## 本讲要解决的核心问题（SCQA）

**背景**：一句话摆在面前——"The water of Walden Pond is so beautifully ___"，大多数人会填 blue、green 或 clear，不会填 refrigerator。人凭语法、常识和对湖泊的了解，就能给候选词排个"合理程度"。

**冲突**：语言模型要做同一件事，但必须用数字做。最直接的办法是数：数"这句前缀后面跟 blue"出现过多少次，再除以"这句前缀"出现的次数。可是语言是创造性的，绝大多数长句子在整个网络上一次都没出现过，于是这个计数永远是"零除以零"。

**疑问**：既然整句数不出来，能不能把整句拆成一小段一小段来数？拆到多短才数得动？拆短了会丢什么？数出来的概率表一定有很多格子是 0，遇到没见过的组合该怎么办？又怎么判断一个模型比另一个好？

**回答（中心思想）**：**n-gram 语言模型用链式法则把整句概率拆成逐词条件概率的乘积，再用马尔可夫假设把"看全部历史"砍成"只看前 $n-1$ 个词"，于是每个因子都能靠语料计数估出来（最大似然估计）；代价是稀疏性——没见过的 n-gram 概率为 0，而 0 会毁掉整句概率和困惑度，所以必须用平滑、回退或插值把概率质量分一点给没见过的组合。** 这条"拆解—估计—评价—补救"的链条，正是今天大语言模型仍在走的路 [【跳转到 10:37】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=637)。

---

## 一、语言模型就是"给下一个词打分"的机器

### 1.1 从"猜下一个词"到概率分布

视频开场用一个填空题说明直觉：读到 "The water of Walden Pond is so beautifully"，你会自动按"有多合理"给候选词排序。语言模型就是把这件工作换成数字的机器：它给词表里**每一个**可能的下一词都分配一个概率，也就是输出一个定义在词表上的概率分布 [【跳转到 00:57】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=57)。

为什么要在意"预测下一个词"？视频给了两层理由 [【跳转到 01:47】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=107)：

1. **它是别的任务的零件**。拼写检查里，"there are two ___ midterms" 中 there 比 their 更可能；语音识别里，"will be back soonish" 和 "I will be bassoonish" 听起来几乎一样，语言模型知道前者更像英语，识别器就会选它。
2. **它本身就是大模型的训练目标**。今天助手背后的模型只做一件事：给定左边所有内容，预测下一个词。这叫从左到右、或自回归（autoregressive）语言建模；生成不过是把同一次操作反复执行——预测一个词、接上去、再预测下一个 [【跳转到 02:37】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=157)。

所以"理解简单的词预测"就是"理解现代 AI 的发动机"。

### 1.2 两个等价的任务

形式化之后有两个目标 [【跳转到 03:01】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=181)：

- 整句概率 $P(w_1, w_2, \dots, w_n)$；
- 给定历史的下一个词概率 $P(w_n \mid w_1, \dots, w_{n-1})$。

任何语言模型算的都是其中之一。视频强调这两个是**同一件事的两个视角**：只要模型能算后者，前者乘起来就有了（下一节就是这件事）。幻灯片下方还有一条小注：这里说"词"，但真实的大模型处理的是 token，往往只是词的一部分。

---

## 二、链式法则：把整句概率拆成逐词概率

### 2.1 为什么不能直接数整句

最朴素的想法是"数了再除"：要估 $P(\text{blue} \mid \text{the water of Walden Pond is so beautifully})$，就数这个前缀后接 blue 出现多少次，再除以前缀出现的次数。问题是长句几乎从不重复出现，分子分母同时为 0 [【跳转到 03:51】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=231)。我们需要一种**不需要见过整句**也能估概率的办法。

### 2.2 链式法则（chain rule）

拆句子的工具是概率课上的链式法则。由条件概率定义 $P(B \mid A) = P(A,B)/P(A)$，移项得 $P(A,B) = P(A)P(B \mid A)$；推广到多个变量：

$$
P(x_1, x_2, \dots, x_n) = P(x_1)\,P(x_2 \mid x_1)\,P(x_3 \mid x_1, x_2)\cdots P(x_n \mid x_1, \dots, x_{n-1})
$$

![链式法则的复习页：从条件概率定义推出多变量乘积形式](assets/n-gram%20语言模型：用计数估计序列概率，用平滑对付没见过的组合/00312.webp)

视频特意强调：**这一步是精确的，没有任何近似** [【跳转到 05:12】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=312)。把链式法则套到词上，"the water of Walden Pond" 的概率就是

$$
P(\text{the})\,P(\text{water}\mid\text{the})\,P(\text{of}\mid\text{the water})\,P(\text{Walden}\mid\text{the water of})\,P(\text{Pond}\mid\text{the water of Walden})
$$

这正好就是"给定历史预测下一个词"的任务。**能预测下一个词的模型，把因子乘起来就能给整句打分**——这就是上一节说两个任务等价的原因 [【跳转到 05:37】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=337)。

### 2.3 马尔可夫假设：把长历史砍成短历史

问题没解决：靠后的因子仍然依赖很长的历史（"Pond 给定 the water of Walden"），而这种长历史同样数不出来。这时 Markov 出场——他研究的是"未来只依赖最近过去"的序列 [【跳转到 06:09】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=369)。

**马尔可夫假设**：不去条件于全部历史，而是只条件于前一个词。

$$
P(\text{blue} \mid \text{The water of Walden Pond is so beautifully}) \approx P(\text{blue} \mid \text{beautifully})
$$

![马尔可夫假设幻灯片：长前缀条件被近似成只看前一个词，右上角是 Andrei Markov 的肖像](assets/n-gram%20语言模型：用计数估计序列概率，用平滑对付没见过的组合/00369.webp)

视频很坦诚：这个近似**一般情况下明显是错的**，但它是一笔交易——用一点准确性，换来"能从数据里估出来"的概率 [【跳转到 06:34】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=394)。所谓马尔可夫模型，就是"预测一个单元时不往太远的过去看"的那一类模型。

把假设代进乘积，每个因子变成 $P(w_k \mid w_{k-1})$，这就是 **bigram（二元）假设**：

$$
P(w_{1:n}) \approx \prod_{k=1}^{n} P(w_k \mid w_{k-1})
$$

![bigram 马尔可夫假设：连乘里每个因子只看前一个词，而不是看 w1 到 wk-1](assets/n-gram%20语言模型：用计数估计序列概率，用平滑对付没见过的组合/00437.webp)

### 2.4 从 bigram 到 n-gram：阶数是一笔交易

推广很自然：bigram 往回看 1 个词，trigram 往回看 2 个词，一般地 **n-gram 条件于前 $n-1$ 个词** [【跳转到 07:17】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=437)。

$$
P(w_k \mid w_1, \dots, w_{k-1}) \approx P(w_k \mid w_{k-n+1}, \dots, w_{k-1})
$$

$n$ 越大，看到的上下文越多，但可能的上下文数量爆炸式增长，需要的数据也暴涨。**选 $n$ 就是在"上下文"和"可靠性"之间做交易**。这条主线后面还会以三种形式反复出现：生成质量、稀疏性、困惑度。

---

## 三、阶数越高越好吗？让模型自己写莎士比亚

理解一个模型学过什么，最直观的办法是让它生成文本。视频用同一份莎士比亚语料，训练了不同阶数的模型 [【跳转到 07:42】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=462)。

![四个阶数并排对比：1-gram 是词的麻袋，2-gram 局部通顺，3-gram 像短语，4-gram 几乎以假乱真](assets/n-gram%20语言模型：用计数估计序列概率，用平滑对付没见过的组合/01674.webp)

- **unigram**（$n=1$，完全忽略上下文）：输出是"莎士比亚词袋"，相邻词之间毫无关系，例如 "to him, swallowed, confess, here, both"，没有语法 [【跳转到 08:23】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=503)。
- **bigram**：每一对相邻词都局部合理（"the King Henry"、"I confess she"），但整体是胡话，因为模型只往回看一个词 [【跳转到 08:07】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=487)。
- **trigram**：开始出现像真莎士比亚的片段，例如 "This shall forbid it should be branded, if renown made it empty" [【跳转到 08:53】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=533)。
- **4-gram**：几乎以假乱真——但视频提醒，这里有个可疑的原因，后面会揭穿。

规律很清楚：**从 unigram 到 4-gram，上下文越多，生成的句子越像英语；代价是数据需求越来越大**。这就是 n-gram 建模的核心交易，一张图就说完了 [【跳转到 09:17】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=557)。

### 3.1 两个结构性弱点

视频点出 n-gram 的两个硬伤 [【跳转到 09:42】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=582)：

1. **抓不住长距离依赖**。"The soups that I made from that new cookbook I bought yesterday were amazingly delicious" 里，动词 were 要和很多词之前的复数 soups 一致；trigram 只看得到 "bought yesterday"，无从知道。
2. **泛化很差**。模型见过 "the cat sat on the mat"，对 "the kitten rested on the rug" 一无所知，尽管两句意思几乎相同——因为它没有"词义相近"的概念。

出路是大语言模型：更长的上下文 + 神经嵌入带来的语义相似性。那为什么还要学 n-gram？Jurafsky 称它们是 NLP 的**果蝇**：生物学家研究果蝇，是因为它简单又能揭示普遍原理。n-gram 几乎引入了语言建模的每一个重要概念——训练集/测试集、困惑度、采样、插值与回退——而且它至今仍然实用：快、便宜，在 LLM 太重的地方照样能用 [【跳转到 10:37】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=637)。
---

## 四、最大似然估计：数一数，除一除

### 4.1 公式只有一行

有了马尔可夫假设，估概率就只剩计数。**最大似然估计（MLE）**的做法是：数这个词对出现多少次，除以第一个词出现多少次 [【跳转到 11:23】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=683)。

$$
P_{\text{MLE}}(w_n \mid w_{n-1}) = \frac{C(w_{n-1} w_n)}{C(w_{n-1})}
$$

用大白话说：**在所有见到第一个词的时刻里，有多大比例后面跟着第二个词？** 之所以叫"最大似然"，是因为这些相对频率恰好是让训练数据在该模型下"最可能出现"的参数取值 [【跳转到 11:28】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=688)。

### 4.2 先在一个三句话的玩具语料上算一遍

视频用三句话的小语料演示，每句都加了开始符号 `<s>` 和结束符号 `</s>`：开始符号让我们能谈论"第一个词"的概率，结束符号让模型成为整句上的合法分布 [【跳转到 11:53】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=713)。

- $P(\text{I} \mid \langle s\rangle) = 2/3$：三句里两句以 I 开头；
- $P(\text{Sam} \mid \text{am}) = 1/2$：am 出现两次，一次接 Sam，一次接 `</s>`；
- $P(\text{do} \mid \text{I}) = 1/3$：I 出现三次。

### 4.3 换一个真实语料：Berkeley Restaurant Project

更大的例子是 Berkeley Restaurant Project：一个餐厅推荐对话系统收集的**口语提问**语料，例如 "can you tell me about any good Cantonese restaurants close by?"、"I'm looking for a good place to eat breakfast"。领域窄，计数好解释 [【跳转到 12:43】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=763)。

![原始 bigram 计数表：行是第一个词、列是后一个词，827 表示 "I want" 出现过 827 次，大片格子是 0](assets/n-gram%20语言模型：用计数估计序列概率，用平滑对付没见过的组合/00784.webp)

这张表来自 9,222 句语料。可以看到 "I want" 827 次、"want to" 608 次、"to eat" 686 次、"chinese food" 82 次。**大多数格子是 0**——视频在这里埋下伏笔：即使这么小的一片，表已经很稀疏，而这个主题会在最后一节变成主角 [【跳转到 13:29】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=809)。

把计数变成概率，只需**按行归一化**：用该行第一个词的 unigram 计数去除。例如 I 出现 2,533 次，所以 $P(\text{want} \mid \text{I}) = 827/2533 \approx 0.33$。结果每行加起来等于 1，即"下一个词"上的一个概率分布 [【跳转到 13:39】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=819)。

![归一化后的 bigram 概率表：P(to|want)=0.66 很高，P(chinese|want) 很小，很多格子正好是 0](assets/n-gram%20语言模型：用计数估计序列概率，用平滑对付没见过的组合/00819.webp)

### 4.4 给整句打分

有了 bigram 概率，就能给整句打分。以 "I want english food" 为例，按链式法则乘起来：

$$
P(\langle s\rangle\ \text{I want english food}\ \langle/s\rangle) = P(\text{I}\mid\langle s\rangle)\cdot P(\text{want}\mid\text{I})\cdot P(\text{english}\mid\text{want})\cdot P(\text{food}\mid\text{english})\cdot P(\langle/s\rangle\mid\text{food}) \approx 0.000031
$$

![bigram 估计的整句概率：五个因子连乘得到 0.000031](assets/n-gram%20语言模型：用计数估计序列概率，用平滑对付没见过的组合/00881.webp)

0.000031 很小，但这是**正常的**：任何句子的概率都很小。真正有意义的是**比较**——这个值比打乱词序的句子高，因为后者会碰到一个极小或为零的因子 [【跳转到 14:41】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=881)。

这些 bigram 概率到底捕获了什么？视频说，捕获的东西相当多：

- $P(\text{to}\mid\text{want}) \approx 0.66$，反映**语法**：want 后面常接不定式 to；
- $P(\text{want}\mid\text{spend}) = 0$、$P(\text{of}\mid\text{to}) = 0$，因为介词 of 不会跟在 to 后面——这是**句法**；
- $P(\text{chinese}\mid\text{want})$ 比 $P(\text{english}\mid\text{want})$ 高，反映**世界知识**：这个语料里人们常想吃中餐；
- dinner 和 lunch 的行为很像，因为它们**语义相关**——教材把这叫分布相似性（distributional similarity），后面讲向量语义时会回来 [【跳转到 15:06】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=906)。

### 4.5 工程细节：下溢与对数概率

一个现实问题：把许多小于 1 的概率相乘，乘积会迅速缩到浮点数表示不了的程度，这叫**下溢（underflow）**。所以实践中语言模型都在**对数空间**里算：乘法变成加法，既稳定又快；真需要概率时最后再取一次指数 [【跳转到 15:37】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=937)。

$$
\log P(w_{1:n}) = \sum_{k=1}^{n} \log P(w_k \mid w_{k-n+1}, \dots, w_{k-1})
$$

真实系统用更大的 n-gram（如 5-gram）。视频提到已有的巨型 n-gram 数据集：十亿词的当代美式英语语料、Google 从万亿词网页里抽的 5-gram；为省空间，概率被量化成 4~8 位而不是 8 字节浮点。最新的想法是 **infini-gram**：不预先算好计数，而是把五万亿词的网页文本存成后缀数组，任何 $n$ 的 n-gram 概率都现场算 [【跳转到 16:32】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=992)。想自己动手，两个经典工具是 SRILM 和 KenLM，其中 KenLM 以极快、极省内存著称。

---

## 五、困惑度：用一个数字衡量"模型有多惊讶"

### 5.1 先分清外在评价与内在评价

语言模型也要被评价。视频先区分两类评价 [【跳转到 17:24】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=1044)：

- **外在（extrinsic / in vivo）评价**：把模型塞进真实应用（机器翻译、语音识别），跑任务、看分数。它直接告诉我们"在意的东西"，但昂贵、慢，常需人工打分，而且结论未必迁移到别的应用。
- **内在（intrinsic / in vitro）评价**：直接用指标衡量"模型预测词预测得多好"，这个指标就是**困惑度（perplexity）**。它不保证下游任务更好，但给出一个通用数字，而且对 LLM 同样适用 [【跳转到 18:14】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=1094)。

评价需要数据切分：训练集上学参数（n-gram 计数），测试集上必须是从未见过的数据，因为我们要量的是**泛化**。视频还提醒两条纪律：

1. **测试集绝不能泄漏进训练集**。一旦某句测试句出现在训练数据里，模型就记住了它的词序，给这句一个虚高的概率，把整个测试集的概率抬高，让模型显得比实际更好——这是坏科学，在网页级训练数据下更是现实隐患 [【跳转到 19:04】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=1144)。
2. **测试集只能跑一次或极少数几次**。反复在测试集上试、只保留有用的改动，等于隐式地把模型调到测试集的怪癖上。调参要用第三个集合：**开发集（dev set）**；调完，最后在测试集上跑一次拿最终数字 [【跳转到 19:54】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=1194)。

### 5.2 直觉：好模型对真实文本"不惊讶"

困惑度的直觉是：好的语言模型更"偏爱"真实句子，给真实常见的句子高概率，给词沙拉（word salad）低概率 [【跳转到 20:19】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=1219)。

第二个直觉来自 **Shannon 游戏**（1951）：给人看句子开头，让他猜下一个词——"Once upon a time, that is a picture of a ___"、"For breakfast, I ate my usual ___"。人很擅长，而好的语言模型就是那个"给真正出现的词更高概率"的模型 [【跳转到 20:49】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=1249)。unigram 在这个游戏里很糟，因为它完全忽略上下文，永远猜 "the"。

把游戏从"一个词"推广到"整个测试集"：把测试集当成一句超长的话，好模型会给它更高的概率——等价于"更少被这段文本惊到" [【跳转到 21:23】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=1283)。

### 5.3 公式：按词数归一化

直接比概率有个坑：测试集越长，概率越小（一直乘小于 1 的数），所以原始概率不能跨不同长度的测试集比较。修法是**按词数归一化**：困惑度是测试集概率的倒数，再按词数开方 [【跳转到 22:13】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=1333)。

$$
\mathrm{PP}(W) = P(w_1 w_2 \cdots w_N)^{-\frac{1}{N}} = \sqrt[N]{\frac{1}{P(w_1 w_2 \cdots w_N)}}
$$

![困惑度公式页：为什么用"测试集概率的 -1/N 次方"，而不是原始概率](assets/n-gram%20语言模型：用计数估计序列概率，用平滑对付没见过的组合/01333.webp)

倒数来自信息论里用交叉熵定义困惑度的原始形式。概率取值在 0 到 1，困惑度取值在 1 到无穷；因为取了倒数，**最小化困惑度 = 最大化概率，越低越好** [【跳转到 22:45】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=1365)。

对 n-gram 模型，先用链式法则把测试集概率拆成逐词因子，再套 n-gram 假设。以 bigram 为例，困惑度就是"每个 bigram 概率的倒数"连乘后开 $N$ 次方：

$$
\mathrm{PP}(W) = \left( \prod_{k=1}^{N} \frac{1}{P(w_k \mid w_{k-1})} \right)^{\frac{1}{N}}
$$

实践中在对数空间计算以保证数值稳定。

### 5.4 第二个解释：加权平均分支因子

困惑度还等于语言的**加权平均分支因子（branching factor）**——分支因子就是"一个词后面可能跟多少个词" [【跳转到 23:10】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=1390)。

视频的例子：一个只有 red、blue、green 三个词、等概率的语言，分支因子是 3，给每个词 1/3 的模型困惑度正好是 3。若测试集是 "red red red red blue"，而模型 B 学到 red 很可能（0.8）、green 和 blue 各 0.1，则

$$
\mathrm{PP}_B = (0.8 \times 0.8 \times 0.8 \times 0.8 \times 0.1)^{-1/5} = 0.04096^{-1/5} \approx 1.89
$$

![分支因子算例：等概率模型困惑度 3，偏向 red 的模型困惑度 1.89](assets/n-gram%20语言模型：用计数估计序列概率，用平滑对付没见过的组合/01440.webp)

1.89 比 3 低，因为它对这段文本**更不惊讶**。所以困惑度可以直观理解为：**模型在多少个"等可能的选项"之间犹豫** [【跳转到 24:00】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=1440)。

真实数据：在 3,800 万词的《华尔街日报》上训练、在 150 万词上测试，unigram 困惑度 962、bigram 170、trigram 109。测试集固定时，预测越好的模型困惑度越低——**更多上下文意味着更少惊讶**。

一条重要警告：**困惑度只在"同一测试集、同一词表"的模型之间可比** [【跳转到 24:32】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=1472)。换词表就等于换了分母，数字没有意义。

---

## 六、从模型里采样：看它到底学到了什么

采样（sampling）就是按概率随机挑点。从语言模型采样，就是按模型给的概率生成句子——这是"看模型学到了什么"最好的办法之一 [【跳转到 25:12】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=1512)。

Shannon 在 1948 年就用字母模型和词模型做过这件事。没有计算机怎么做？他自己的说法是：随便翻开一本书挑一个字母，再翻到另一页读到这个字母，记下它后面那个字母；再翻一页找第二个字母，记下后面是什么……这就是在真实文本上做 bigram 采样 [【跳转到 25:50】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=1550)。

计算上怎么做？最容易理解的是 unigram：把整个词表铺在 0 到 1 的区间上，每个词占的长度正比于它的概率（the 占一大块，生僻词只占一条缝）；取一个 0 到 1 的随机数，看落在哪个词的区间里就输出哪个词。高频词常被选中，生僻词很少 [【跳转到 26:23】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=1583)。

bigram 只是把它串起来：从 `<s>` 开始，按概率采样一个以它开头的 bigram，得到 "I"；再采样以 "I" 开头的，得到 "want"；再以 "want" 开头得到 "to"……直到采样到 `</s>`，把词拼起来就是 "I want to eat Chinese food" [【跳转到 26:48】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=1608)。

神经语言模型还有更精细的采样法：温度采样、top-K、top-P，主要目的都是**避免从分布的长尾里采样**（那里住着古怪的生僻词）。视频说这些留到讲神经解码时再说——它们正是聊天机器人"决定自己多 creative"时在跑的东西 [【跳转到 27:13】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=1633)。

---

## 七、稀疏性：n-gram 的死穴

### 7.1 莎士比亚的账：99.96% 的 bigram 从未出现

视频用莎士比亚全集算了一笔账 [【跳转到 28:24】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=1704)：

- 全部作品约 **884,647 个 token**，词表 **29,066** 个类型；
- 可能的 bigram 约 $29{,}000^2 \approx 8.44$ 亿种；
- 莎士比亚实际只产生了约 **34 万**种不同的 bigram；
- 于是 **99.96% 的可能 bigram 从未出现**。

![莎士比亚语料的稀疏性：844 百万种可能 bigram 里只出现了 30 万种，99.96% 是零](assets/n-gram%20语言模型：用计数估计序列概率，用平滑对付没见过的组合/01704.webp)

4-gram 更糟：稀疏到对大多数上下文只有**唯一一种**后续，模型实际上只是在**背诵**莎士比亚原文。看起来像创造力，其实是记忆 [【跳转到 28:49】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=1729)。

### 7.2 模型学的是"文体"，不是"英语"

换成《华尔街日报》训练的模型，输出立刻变了：满篇百分比、公司、市场，和莎士比亚几乎不重叠。教材的结论是：**n-gram 模型极度依赖训练语料，它学到的是文体（genre），不是一般意义上的英语** [【跳转到 29:10】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=1750)。

视频给了一个小测验：三句来自不同 trigram 模型的采样，能猜出各自训练在什么语料上吗？带百分比、美元、Mexico 和 Brazil 的显然是《华尔街日报》；"this shall forbid it should be branded, if renown made it empty" 是莎士比亚；带 "shays"、"four" 和 "a smile" 的是简·奥斯汀 [【跳转到 29:40】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=1780)。

这对选训练数据有直接后果：任务具体就用同文体的语料（法律翻译用法律文书、临床用病历），还要覆盖不同方言与说话人。幻灯片举的例子是非裔美国人白话英语（AAVE），它有"用助动词标记近将来"这类特征；只用标准书面语训练的模型会把它当噪声，对这些说话人表现更差——这既是准确性问题，也是公平性问题 [【跳转到 30:35】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=1835)。

### 7.3 零概率：为什么它既伤应用又毁评价

即使语料选得好，测试集仍会带来意外。最关键的泛化问题之一就是**零**：训练里从未出现、测试里却出现了的东西 [【跳转到 31:00】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=1860)。

![过拟合的代价：测试集里会出现训练集从未出现的组合，也就是"零"](assets/n-gram%20语言模型：用计数估计序列概率，用平滑对付没见过的组合/01860.webp)

例子：训练语料里 "eight" 后面跟过 lunch、dinner、a、the 各 8 次，但从没跟过 breakfast。于是 $P(\text{breakfast}\mid\text{eight}) = 0$。可测试集里就有 "eight breakfast" 这种完全正常的英语，模型说它不可能。零有两个害处 [【跳转到 31:50】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=1910)：

1. **低估了大量完全合理的序列**，伤害任何下游应用；
2. **对评价是致命的**：只要测试集里有一个 n-gram 概率为 0，整句概率就是 0（因为连乘），困惑度就要除以零，**根本算不出来**。

所以必须有原则性的办法来处理"没见过的组合"。

---

## 八、平滑、回退与插值：把概率分一点给没见过的组合

### 8.1 稀疏性的日常面孔

最大似然估计的根本问题是**稀疏性**：有限的语料必然缺少一些完全正常的序列。语料里可能有 ruby 和 slippers，却恰好没有 ruby slippers，MLE 就说这个短语概率为 0——可我们知道它是个再普通不过的两词短语 [【跳转到 32:45】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=1965)。

视频举了动词宾语的例子：语料里 "denied the" 后面跟过 allegations（3 次）、reports（2 次）、claims（1 次）、request（1 次），合计 7 次；但 "denied the attack"、"denied the outcome"、"denied the man" 计数都是 0，尽管它们都很合理——训练数据只是碰巧没包含 [【跳转到 33:18】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=1998)。

### 8.2 平滑的直觉：削峰填谷

**平滑（smoothing）的直觉是：从已经见过的事件身上取一小块概率质量，分给没见过的那些** [【跳转到 33:39】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=2019)。

- 平滑前：allegations 3、reports 2、claims 1、request 1，共 7；
- 平滑后：allegations 2.5、reports 1.5、claims 0.5、request 0.5，剩下的 2 个单位分给 attack、man、outcome 等词；
- 总数仍然是 7。**高频词被削掉一点，没见过的词不再"不可能"** [【跳转到 34:04】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=2044)。

### 8.3 加一平滑（Laplace smoothing）

最简单的方法是 **add-one**，也叫 Laplace 平滑：假装每个词都比实际多见过一次，给所有计数加 1 [【跳转到 34:22】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=2062)。

$$
P_{\text{Laplace}}(w_n \mid w_{n-1}) = \frac{C(w_{n-1}w_n) + 1}{\sum_{w}\left(C(w_{n-1}w) + 1\right)} = \frac{C(w_{n-1}w_n) + 1}{C(w_{n-1}) + V}
$$

分子加 1；因为词表里有 $V$ 个可能的下一词、每个都多拿了一次计数，所以分母要加 $V$（$V$ 是词表大小）。

![加一平滑公式：MLE 是"对计数/首词计数"，Laplace 是"（对计数+1）/（首词计数+V）"](assets/n-gram%20语言模型：用计数估计序列概率，用平滑对付没见过的组合/02062.webp)

视频顺带澄清了"最大似然"的含义：参数的 MLE 是让训练集在该模型下最可能出现的那个值。若 bagel 在百万词中出现 400 次，MLE 就是 0.0004。对别的语料这也许是个坏估计，但它确实是让"百万词语料里恰好出现 400 次 bagel"这件事最可能的估计。**MLE 完美拟合训练数据，而这份完美正是过拟合与零的来源** [【跳转到 35:12】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=2112)。

### 8.4 加一平滑有多"狠"：重构计数

把 Laplace 平滑用到餐厅计数表上，每个 0 都变成 1，每个计数都加 1，表上不再有洞。但后果是：由于分母多了 $V$，**已观测 bigram 的总概率大幅下降** [【跳转到 35:57】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=2157)。

为了看清"伤害有多大"，教材用了一个可视化技巧：**重构计数（reconstituted counts）** $C^*$——它是"如果除以原来的分母、就能得到平滑后概率"的那个计数：

$$
C^* = \frac{(C + 1)\,C(w_{n-1})}{C(w_{n-1}) + V}
$$

![重构计数对比表：上表是原始计数，下表是加一平滑后的等效计数，chinese food 从 82 掉到 8.2](assets/n-gram%20语言模型：用计数估计序列概率，用平滑对付没见过的组合/02213.webp)

对比一下就很直观："chinese food" 的等效计数从 **82 掉到 8.2**。比值 $D = C^*/C$ 叫**折扣（discount）**，这里是 0.10——**十倍削减**。加一平滑从见过的事件身上抽走了太多概率去喂大量未见过的事件，太激进了 [【跳转到 36:53】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=2213)。

所以 add-one 是把钝器，**n-gram 语言模型一般不用它**；它在朴素贝叶斯文本分类里仍然好用，因为那里的零没这么多。它的变体 **add-k** 加的是 0 到 1 之间的小数 $k$ 而不是整数 1，效果更好 [【跳转到 37:23】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=2243)。

### 8.5 更聪明的思路：回退与插值

更好的想法是：**对长上下文知道得少，就少条件一点**。有两种口味 [【跳转到 37:48】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=2268)：

- **回退（backoff）**：证据够就用 trigram；不够就用 bigram；再不够用 unigram。
- **插值（interpolation）**：永远把 unigram、bigram、trigram 的估计混在一起。

实践中插值效果更好。简单的线性插值给每个阶数一个权重 $\lambda$，权重和为 1，结果仍是合法概率：

$$
P(w_n \mid w_{n-2}, w_{n-1}) = \lambda_1 P(w_n \mid w_{n-2}, w_{n-1}) + \lambda_2 P(w_n \mid w_{n-1}) + \lambda_3 P(w_n)
$$

![回退与插值的对照页：回退是"证据不足就降阶"，插值是"各阶加权混合"](assets/n-gram%20语言模型：用计数估计序列概率，用平滑对付没见过的组合/02268.webp)

还能更进一步：让 $\lambda$ **依赖上下文**——某个 trigram 上下文见过很多次就多信 trigram，很少见就多信低阶模型 [【跳转到 38:13】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=2293)。

$\lambda$ 怎么定？用**留存语料（held-out corpus）**：先固定训练集上的 n-gram 概率，再搜索让留存数据概率最高的 $\lambda$。$\lambda$ 是**超参数**——不是从训练计数里学出来的参数，所以要在留存数据（就像前面说的开发集）上选 [【跳转到 38:38】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=2318)。

### 8.6 回退的两个细节

回退的例子：要算 "delicious soufflé" 后面接 pancakes 的概率，若这个 trigram 计数为 0，就退到 bigram "soufflé pancakes"；若还是 0，再用 pancakes 的 unigram 概率 [【跳转到 39:17】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=2357)。

一个麻烦：高阶概率必须**先打折（discount）**，即稍微减小一点，否则把回退来的概率加上去之后总和会超过 1。经典做法是 **Katz back-off**。还有一个名字很诚实的简化版 **stupid back-off**：完全跳过打折，所以结果不是真正的概率分布，只是在高阶计数为 0 时用低阶估计乘一个常数。听起来很粗暴，但在万亿词的网络规模下它效果出奇地好，而且便宜 [【跳转到 39:42】](https://www.youtube.com/watch?v=Bw-nefkA4Zg&t=2382)。

---

## 小结

- **语言模型 = 给下一个词分配概率的机器**；整句概率与下一词概率通过链式法则等价，链式法则这一步是精确的，没有近似。
- **马尔可夫假设**把"看全部历史"换成"看前 $n-1$ 个词"，这是 n-gram 的全部秘密，也是它全部误差的来源。
- **阶数是一笔交易**：上下文越多，生成越像人话（unigram → 4-gram 的莎士比亚实验），但需要的数据暴涨、稀疏性恶化。
- **最大似然估计就是计数相除**，它完美拟合训练集，而这份完美带来过拟合与零概率。
- **困惑度 = 测试集概率的 $-1/N$ 次方**，越低越好，可解释为"加权平均分支因子"；只在同一测试集、同一词表下可比。
- **稀疏性是死穴**：莎士比亚 99.96% 的可能 bigram 从未出现；一个零就让整句概率和困惑度崩掉。
- **补救有三条路**：平滑（add-1/add-k，削峰填谷但很钝）、回退（证据不足就降阶，Katz/stupid back-off）、插值（各阶加权，实践最好，权重在留存数据上选）。
- 这些概念——下一词预测、留存数据评价、对未见数据的泛化——**正是神经大语言模型在更大尺度上做的事**。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| 语言模型（language model） | 给词表里每个可能的下一词分配概率的模型 |
| 链式法则（chain rule） | 把联合概率拆成逐项条件概率的乘积，$P(x_1,\dots,x_n)=\prod_k P(x_k\mid x_{<k})$ |
| 马尔可夫假设（Markov assumption） | 用"只看前 $n-1$ 个词"近似"看全部历史" |
| n-gram | 连续 $n$ 个 token 的片段；n-gram 模型条件于前 $n-1$ 个词 |
| bigram / trigram | $n=2$ / $n=3$ 的 n-gram，分别往回看 1 个 / 2 个词 |
| 最大似然估计（MLE） | $P(w_n\mid w_{n-1}) = C(w_{n-1}w_n)/C(w_{n-1})$，即计数相除 |
| 下溢（underflow） | 多个小于 1 的概率连乘导致浮点数无法表示，故改用对数概率 |
| 困惑度（perplexity） | 测试集概率的 $-1/N$ 次方，越低越好；可读作"平均分支因子" |
| 稀疏性（sparsity） | 有限语料中大量合法 n-gram 计数为 0，导致概率为 0 |
| 平滑（smoothing） | 从已见事件挪一点概率质量给未见事件，如 add-1 / add-k |
| 折扣（discount） | 平滑后等效计数与原计数之比 $D=C^*/C$，衡量被削掉多少 |
| 回退（backoff） | 高阶 n-gram 计数不足时退回低阶估计（Katz、stupid back-off） |
| 插值（interpolation） | 把不同阶数的估计按权重 $\lambda$ 加权混合，权重和为 1 |
| 留存语料 / 开发集 | 用于选超参数（如 $\lambda$）的数据，与训练集、测试集分开 |
