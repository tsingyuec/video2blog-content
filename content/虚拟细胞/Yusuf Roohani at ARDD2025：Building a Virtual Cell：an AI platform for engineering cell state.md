# Yusuf Roohani at ARDD2025: Building a Virtual Cell: an AI platform for engineering cell state

## 所用视频

- 标题：**Yusuf Roohani at ARDD2025: Building a Virtual Cell: an AI platform for engineering cell state**
- 平台与视频 ID：YouTube `k2VCADF3TwI`
- 时长：22:15（演讲约 19 分钟 + 问答）
- 字幕：英文自动字幕
- [视频链接](https://www.youtube.com/watch?v=k2VCADF3TwI)

## 视频主线

Roohani 先用 AlphaFold 说明“在电脑上预演实验”的力量，再把这个思路推到细胞层面，并强调虚拟细胞必须与实验平台闭合成环。接着他按团队的四条工作线展开：把任务形式化为“未扰动状态 + 扰动 → 扰动后状态”，解释为何选转录组、为何最关心跨供体泛化，再介绍 State 如何对细胞集合建模、评测如何复现 Perturb-seq，以及 Virtual Cell Challenge 如何把评测变成社区标尺。最后两个智能体项目分别解决数据整理与实验设计，问答则补充了数据偏差与 Arc/CZI 的路线差异。

## 一、AlphaFold 说明实验可以在电脑里预演，但它只走到蛋白质层面

Roohani 领导 Arc Institute 的机器学习小组。Arc 是位于加州帕洛阿尔托的非营利研究机构，关注研究复杂疾病的新方法；他的小组用 AI 建立更好的细胞状态模型，再用来预测细胞在未见干预下的行为。他同时在斯坦福做访问学者，大约一年前刚在斯坦福完成博士。[【跳转到 00:00】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=0) [【跳转到 00:05】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=5) [【跳转到 00:10】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=10) [【跳转到 00:15】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=15) [【跳转到 00:20】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=20) [【跳转到 00:25】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=25) [【跳转到 00:30】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=30)

他用 **AlphaFold** 开场：它输入蛋白质序列、输出结构；训练时看过一批实验解析的结构，学到序列与结构的关系，再把这个关系用到没见过的序列上。那些序列在训练数据里大概没有实验结构，但模型仍然能给出预测。[【跳转到 00:44】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=44) [【跳转到 00:53】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=53)

一种理解方式是：AlphaFold 让你**在硅基环境里做结构推断实验**，计算地预测“如果真去湿实验室做这个实验，结果会是什么”。这种不真正跑实验就能预演实验的范式非常强大。[【跳转到 01:18】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=78)

![AlphaFold 把“序列→结构”的实验搬进电脑，虚拟细胞想把同样的事搬到细胞层面](assets/Yusuf Roohani at ARDD2025：Building a Virtual Cell：an AI platform for engineering cell state/00053.webp)

这个视角把科学发现看成一个**搜索问题**：在大量假设中寻找最能回答某个问题的那一个，而 AI 让搜索过程更高效，让我们更快地看过多组假设，不把时间浪费在意义不大或产出不高的实验上。[【跳转到 01:43】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=103) [【跳转到 01:50】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=110) [【跳转到 02:00】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=120) [【跳转到 02:05】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=125)

但 AlphaFold 的局限也很清楚：它只处理蛋白质层面。团队想再往上走一层，从序列层面的表示和基础模型，走到**细胞层面**的表示，去回答“如果有一些正在退化或衰老的神经元，怎样把它们推回功能正常的状态”。如果真正有了好的细胞状态模型、也知道怎样扰动它，就能做很强的推断，帮助发现新药靶点、理解生物机制——这个清单可以一直列下去。[【跳转到 02:05】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=125) [【跳转到 02:22】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=142) [【跳转到 02:47】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=167)

## 二、虚拟细胞不能孤立存在，真正的效果来自与实验平台闭合成环

Roohani 强调，再往深想一层就会发现：**虚拟细胞不能孤立存在**。它真正的效果，来自与实验平台一起构建——既包括实验侧的数据生成和数据整理，也包括模型训练与优化。[【跳转到 02:47】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=167) [【跳转到 03:12】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=192)

Arc 和他的小组谈虚拟细胞时，总是把它谈成一个**完整平台**：实验侧、数据生成、数据整理，以及模型训练和优化，全都在内。这是一条闭环。他们去年在《Cell》上发表了一篇观点文章，描述虚拟细胞的愿景：它是一个设计实验、理解细胞表型的工具——提出假设，在实验室验证，再把结果和分析回灌到虚拟细胞模型里，如此循环，逐渐理解感兴趣的表型。[【跳转到 03:12】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=192) [【跳转到 03:37】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=217) [【跳转到 04:02】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=242)

## 三、团队的四条工作线：模型开发、模型评测、数据整理、指导数据生成

在这个愿景下，团队过去一年的工作落在四个方向。[【跳转到 04:02】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=242) 他们不只关心怎样建立预测模型，也关心怎样用 AI 生成正确的数据来支撑这些模型。也就是说，AI 不只用在预测侧，还用在“元层面”：判断哪些数据该进入模型，以及如何更好地利用已经存在的数据。[【跳转到 04:16】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=256)

这对应四条线：**模型开发、模型评测、数据整理、指导数据生成**。[【跳转到 04:16】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=256) [【跳转到 04:27】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=267)

随后他给出整场演讲的路线图：先讲 **State**——一个基于 Transformer、预测实验室尚未做过的扰动结果的模型；再讲 **Virtual Cell Challenge**——一个衡量不同虚拟细胞模型或扰动预测模型表现的竞赛；然后讲如何用智能体整理出最大的、由智能体整理的生物数据仓库；最后讲如何用智能体不只整理已有数据，还指导新数据生成，以得到更好的预测模型。[【跳转到 04:52】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=292) [【跳转到 04:57】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=297) [【跳转到 05:22】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=322) [【跳转到 05:35】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=335) [【跳转到 05:42】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=342)

## 四、这个愿景并不新，变的是基础模型让“通用底座 + 下游任务”成为可能

在讲 State 之前，Roohani 先做一点背景交代。他说虚拟细胞是个棘手话题，很多人理解很不一样，他并不想把 Arc 的定义强加给在场的人；但他认为多数研究者会同意虚拟细胞背后的共同愿景。[【跳转到 05:50】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=350) [【跳转到 05:55】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=355) [【跳转到 06:00】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=360) [【跳转到 06:06】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=366)

这个愿景在 2000 年代初就出现过：Uriel 的团队建立微分方程模型，研究细胞生理和各种化学动力学。大约十年前，Marcus Covert 建立全细胞模型并发表在《Cell》，考察细胞内各种组分、各种细胞器如何相互作用。当时的目标和现在一样：建立理解细胞运作的预测模型，再用它推断细胞面对新实验、新干预时会怎样。[【跳转到 06:06】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=366) [【跳转到 06:20】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=380) [【跳转到 06:45】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=405) [【跳转到 06:50】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=410)

不同的是，我们现在有了**基础模型**这条路。[【跳转到 07:00】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=420) Roohani 在斯坦福 AI 实验室参与过引入“基础模型”一词的文章，发表时间比 ChatGPT 早几个月。他记得当时的 Slack 讨论：怎样定义一类模型，它能成为底座，让人在其上训练其他可能与初始任务并不直接相关的模型？[【跳转到 07:05】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=425) [【跳转到 07:10】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=430)

思路是：拿大量数据，学一个通用目的的底座模型，对关注的系统形成通用理解，再把它应用到各种下游任务；很多下游任务在训练基础模型时根本没直接训练过。就像模型没有直接训练来回答问题，但因为学到了好的文本表示，就能用来回答问题。[【跳转到 07:35】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=455) [【跳转到 07:41】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=461)

## 五、把虚拟细胞写成一个精确任务：Xp = f(X0, p)

于是问题变成：怎样把这个想法带到细胞上？他们没有展开太多细节，而是先形式化一个非常精确、要聚焦的任务。[【跳转到 07:41】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=461) [【跳转到 07:58】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=478)

这个任务就是建立计算模型，预测细胞对扰动的反应，并且特别针对转录组数据：给定未扰动的细胞，施加一个扰动，预测这群细胞的反应。可以写成：

> **Xp = f(X0, p)**：输入未扰动状态 X0 和扰动 p，输出扰动后状态 Xp。

这就是他们理解的“预测细胞对扰动的响应”。[【跳转到 08:14】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=494) [【跳转到 08:25】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=505)

![虚拟细胞的形式化：给定未扰动细胞群 X0 和扰动 p，预测扰动后的细胞群 Xp](assets/Yusuf Roohani at ARDD2025：Building a Virtual Cell：an AI platform for engineering cell state/00505.webp)

## 六、选转录组作读数，是因为它表达力强，而且团队已经把它规模化

“细胞状态”可以有很多种读法。对这个听众来说，表观遗传可能很有意思，比如 DNA 甲基化；细胞年龄也可能很有意思。他们最终选择**转录组**作为读数，主要因为它的表达力，也因为团队已经在“把这种模态规模化”上投入了很多。[【跳转到 08:25】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=505) [【跳转到 08:41】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=521)

数据规模支撑了这个选择：他们用 AI 智能体扩大训练数据，现在有超过 **6 亿个细胞**可用于训练，覆盖不同组织。[【跳转到 08:59】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=539) [【跳转到 09:05】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=545)

扰动方式上，他们聚焦 **CRISPR**，因为 Arc 内部有这方面的专长；同时他们有大量 Perturb-seq 数据，可以用超过 **1 亿个细胞**、超过 **5,000 个不同扰动**来训练大模型。[【跳转到 09:05】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=545) [【跳转到 09:16】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=556)

## 七、最关心的是跨生物上下文泛化：来了新供体、新患者还能不能预测

扰动预测任务有很多种定义，他们最关心的是**跨生物上下文泛化**。假设模型已经见过若干供体，也见过这些供体上的一组扰动；现在来了一个新供体，能不能预测扰动在新供体上的效果？他们把这个叫 context generalization task。[【跳转到 09:16】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=556) [【跳转到 09:33】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=573)

这对应现实中的新患者：你想知道某种药对他是否有效，或者他携带某个突变、受到其他形式的扰动后，对药物是否敏感。[【跳转到 09:38】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=578) [【跳转到 09:54】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=594)

## 八、State 不建模单个细胞，而是建模一组细胞

已有的扰动预测方法，通常从群体里随机取一个未扰动细胞、再取一个扰动后细胞，训练 Transformer 学“这个输入到那个输出”的映射。问题在于：这样做会把**整个分布里的信息**丢掉，而细胞异质性本身就是生物学信号。[【跳转到 10:07】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=607) [【跳转到 10:12】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=612)

他们想要的是既能用 Transformer 扩展、又能考虑细胞异质性的方法，于是建了 **State**：它不工作在单个细胞上，而是工作在一组细胞上。这样 Transformer 能可扩展地在一整个细胞分布上学习；借助自注意力机制，不需要硬编码细胞应该如何行为，模型自己找出分布的细微结构，从而更好地推断整个群体对某个扰动的反应。[【跳转到 10:12】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=612) [【跳转到 10:37】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=637) [【跳转到 10:55】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=655)

![State 对细胞集合建模：输入未扰动细胞群，输出预测的扰动后细胞群](assets/Yusuf Roohani at ARDD2025：Building a Virtual Cell：an AI platform for engineering cell state/00663.webp)

## 九、评测的目标是复现一次真实的 Perturb-seq

模型变强不等于预测有用。Roohani 团队的评测套件围绕一个目标设计：**多大程度上复现一次真实的 Perturb-seq 实验**。[【跳转到 11:03】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=663) 他们重点看表达计数、细胞聚类与组成、不同扰动能否被区分、差异表达基因能否被识别，以及预测的效应量是否合理；这些由多个指标衡量。[【跳转到 11:03】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=663) [【跳转到 11:15】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=675)

![评测套件从表达计数、差异表达、效应量等维度检验模型能否复现真实 Perturb-seq](assets/Yusuf Roohani at ARDD2025：Building a Virtual Cell：an AI platform for engineering cell state/00700.webp)

在差异表达基因检测上，蓝色曲线是 State，其他颜色是均值、线性、深度学习和基础模型基线；结果显示，**对细胞集合建模带来了显著提升**，而这类任务上最强的对手往往是均值基线。[【跳转到 11:15】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=675) [【跳转到 11:40】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=700)

![State 在差异表达基因检测上的 precision-recall 曲线明显高于均值、线性与基础模型基线](assets/Yusuf Roohani at ARDD2025：Building a Virtual Cell：an AI platform for engineering cell state/00725.webp)

他们还看了一个更贴近生理的场景：用针对 BRAF 突变黑色素瘤的药物处理 BRAF 突变细胞系，这个细胞系在训练中部分留出。State 能比当时最好的基线（实际上也是均值基线）更有效地捕捉受扰动影响的真实显著基因。[【跳转到 12:05】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=725) 模型对细胞存活的预测也与实验观察相当吻合。[【跳转到 12:42】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=762)

这也给出一个判断标准：虚拟细胞要复现的不只是表达矩阵的数值，还包括细胞组成、扰动区分度、效应量和未见供体上的表现。只看一个误差指标，很容易把“记住训练集平均值”误当成“学会了生物学”。

## 十、Virtual Cell Challenge：把“什么算对”交给社区一起定义

模型建好后，团队想推动社区一起回答：什么才是对的评测框架、任务和数据集？于是发起了 **Virtual Cell Challenge**。[【跳转到 12:47】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=767) [【跳转到 12:52】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=772) 逻辑很直接：Arc 给出一个“虚拟细胞至少应该能做到”的任务，社区提交模型，同时反馈还缺哪些任务、指标和数据集。[【跳转到 13:02】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=782)

这个挑战两个月前启动，相关论文今年 6 月发表在《Cell》，距离结束还有大约两个半月。[【跳转到 12:57】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=777) [【跳转到 13:02】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=782) [【跳转到 13:07】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=787) 启动约两个月，已有约 **3,000 名注册者、450 多支队伍**。[【跳转到 13:32】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=812)

他们花了很多时间构建这个非常特定的数据集。Roohani 认为比赛最有意思的部分，是设计**可重复的实验**，让测量真正捕捉生物信号。他也希望衰老研究社区提出值得预测的衰老表型，纳入下一届。[【跳转到 13:37】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=817)

比赛由 Arc 内部出人出钱主办，不是 consortium，有专门的团队负责，计划每年举办。[【跳转到 13:37】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=817) [【跳转到 13:53】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=833)

## 十一、数据瓶颈用智能体解决：从 SRA 整理出 scBaseCount

讲完模型，Roohani 转向数据：不只是建模型，还要用智能体和 AI 生成、整理训练这些模型所需的数据集。[【跳转到 14:18】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=858) [【跳转到 14:23】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=863)

单细胞 RNA 测序数据最常用的仓库是 **Cell by Gene**，约 1 亿个细胞；但 NIH 的 **Sequence Read Archive（SRA）** 保存所有原始测序数据，规模大好几个数量级，而且增长很快。[【跳转到 14:23】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=863) [【跳转到 14:31】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=871)

为什么不直接挖 SRA？因为元数据整理极其痛苦：要逐项解析、判断正确的术语、测定类型和物种，再送进另一条流水线处理单细胞数据。[【跳转到 14:31】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=871) [【跳转到 14:56】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=896)

他们用**智能体**做这件事：让 Agentic AI 动态浏览数据库，找出相关元数据，再自动送入下游处理，为前面展示的模型生成越来越多训练数据。整个系统是一个智能体网络：一半负责注释和识别每个数据集的相关元数据，另一半的流水线处理送过来的数据集，最后通过读段比对完成定量。[【跳转到 14:56】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=896) [【跳转到 15:14】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=914)

结果是一个名为 **scBaseCount** 的数据集：比当时最大的单细胞仓库大 **5 倍**，覆盖 **25 个物种**（Cell by Gene 只有 5 个）。[【跳转到 15:31】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=931) [【跳转到 15:56】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=956) 它还是最大的非编码基因表达仓库——已测序的 5 亿个细胞都有非编码表达，而且全部统一处理、批次效应很小。更重要的是，这是第一个由 AI 智能体整理、并**自主持续更新**的大型生物数据仓库：智能体还在继续浏览数据库，寻找更多数据集。[【跳转到 16:16】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=976) [【跳转到 16:41】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=1001)

![scBaseCount：统一处理、覆盖非编码表达、由 AI 智能体整理并持续更新](assets/Yusuf Roohani at ARDD2025：Building a Virtual Cell：an AI platform for engineering cell state/00976.webp)

这一步的意义不只是“数据更多”。它说明 AI 不只在模型开发里有用，也能处理模型开发周围那些“无聊但关键”的工作：清洗数据、准备元数据、扩大覆盖。Roohani 也希望其他人把这条路用到其他类型的生物数据上。[【跳转到 15:56】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=956) [【跳转到 16:41】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=1001)

## 十二、智能体也能设计实验：从整理数据到“虚拟生物学家”

最后一个项目把智能体从“整理已有数据”推进到“指导新数据生成”。他们设计了一个智能体，让它提出下一批基因扰动实验；实验通过模拟执行（因为所需数据已经存在），结果再喂回智能体，让它决定下一步，如此迭代，去优化某个特定表型。[【跳转到 17:04】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=1024) [【跳转到 17:16】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=1036)

![BioDiscovery Agent：让智能体提出下一批基因扰动，再把结果回灌形成迭代](assets/Yusuf Roohani at ARDD2025：Building a Virtual Cell：an AI platform for engineering cell state/01052.webp)

每一轮提出 **128 个基因**的扰动，每轮虚拟实验后计算命中率，看模型这一轮表现如何；模型会随轮次逐渐抓到更多命中。[【跳转到 17:32】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=1052) [【跳转到 17:37】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=1057) 与更简单的基线相比，它在几乎所有情况下都不差于最好的基线，很多时候还明显更好。平均性能提升 **21%**；对更难发现的非必需基因，提升约 **42%**（幻灯片标注为 +43%）。[【跳转到 18:02】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=1082) [【跳转到 18:08】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=1088) [【跳转到 18:13】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=1093)

![智能体逐轮提出扰动，命中率随时间上升；平均提升 21%，非必需基因约 42%](assets/Yusuf Roohani at ARDD2025：Building a Virtual Cell：an AI platform for engineering cell state/01093.webp)

这个闭环把虚拟细胞从“预测器”推向“实验合作者”：模型提出假设，实验（或模拟）给出反馈，反馈再改进下一轮假设。Roohani 用 Dario Amodei 的一句话收尾：AI 在这个领域不应只被看作数据分析工具，而应被看作**虚拟生物学家**。他们正在这些智能体框架里思考：如何用这些 AI 工具去赋能“虚拟生物学家”，看看这个组合系统能走多远。[【跳转到 18:18】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=1098) [【跳转到 18:23】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=1103) [【跳转到 18:36】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=1116)

演讲最后，他回顾了前面介绍的几篇论文，给出个人网站上的链接，并致谢小组、Arc 和斯坦福的合作者。[【跳转到 18:48】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=1128) [【跳转到 18:54】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=1134) [【跳转到 18:59】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=1139)

## 十三、问答划出两条边界：数据可能有偏，Arc 与 CZI 路线不同

### 13.1 人类注释会漏信息，智能体也可能出错

有听众问：人类常犯错，可能不经意地犯错，约一半已发表论文可能含有一些错误；有没有计算的方法判断哪些生物数据是真的、哪些可能不是？Roohani 说，scBaseCount 有一篇更新预印本即将发布；他们分析了从 SRA 得到的数据，发现很多数据集富集了 T 细胞。即使数据集没有被标注为某种疾病，也很有可能很多样本本来就来自病人。这些是看数据时得到的有趣洞见，而人类注释常因各种原因漏掉它们。[【跳转到 19:31】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=1171) [【跳转到 19:37】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=1177) [【跳转到 19:42】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=1182) [【跳转到 20:07】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=1207) [【跳转到 20:32】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=1232)

他说，让一个中立的智能体做数据解析、不带入人类偏见是好事；但智能体自己也可能出错，他们正在探索这个问题。[【跳转到 20:37】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=1237) [【跳转到 20:42】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=1242)

### 13.2 Arc 选择所有环节自做，CZI 更偏计算并外包数据生成

另一个问题问 Arc 与 Chan Zuckerberg Initiative 的异同。Roohani 说，CZI 更偏计算侧，资助外部机构为他们生成数据；Arc 则坚持所有环节都在内部做，希望做 AI 和机器学习的人与做实验的人坐在同一张桌子旁，在数据生成时就参与讨论。关键差异是：Arc 在数据生成现场，而 CZI 把数据生成外包出去。Arc 团队更小，自己建模型，非常专注于扰动预测；CZI 还在看不少其他方向。[【跳转到 21:04】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=1264) [【跳转到 21:09】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=1269) [【跳转到 21:16】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=1276) [【跳转到 21:21】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=1281) [【跳转到 21:26】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=1286) [【跳转到 21:51】](https://www.youtube.com/watch?v=k2VCADF3TwI&t=1311)

## 小结

- 虚拟细胞在 Arc 的语境里是一个**闭环平台**：模型、评测、数据整理、数据生成四件事必须一起做。
- 任务被形式化为 **Xp = f(X0, p)**；他们选择转录组作为读数，并聚焦 CRISPR 扰动。
- State 的关键不是“更大的 Transformer”，而是**对细胞集合建模**：用自注意力保留群体异质性，并专门评测对新供体的上下文泛化。
- 评测要复现真实 Perturb-seq 的多个侧面；Virtual Cell Challenge 把这个评测变成社区共同迭代的标尺。
- 数据瓶颈用**智能体**解决：scBaseCount 比当时最大仓库大 5 倍、覆盖 25 个物种，且由 AI 整理并持续更新。
- 智能体还能**指导实验**：每轮 128 个基因，平均命中率提升 21%，非必需基因约 42%；但注释偏差和智能体自身的错误仍需警惕。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| 细胞状态 | 用某个可测模态（如转录组）刻画的细胞当前状况 |
| 扰动 | 对细胞施加的改变，如 CRISPR 敲低、药物处理 |
| 上下文泛化 | 在见过的供体/条件上训练，预测新供体或新条件下的响应 |
| Perturb-seq | 将 CRISPR 扰动与单细胞 RNA 测序结合，读出每个扰动的表达响应 |
| scBaseCount | 由 AI 智能体整理、统一处理并持续更新的大型单细胞数据仓库 |
| 虚拟生物学家 | 用 AI 智能体承担提出假设、设计实验、分析结果等科研工作 |

## 相关阅读

- [What is a virtual cell? Biohub 的 18 亿美元数据计划](<What is a virtual cell？Biohub's $1.8 billion data push, and the AI models it is for.md>)
- [BioML Seminar 4.4 - Tahoe-x1 作者报告](BioML Seminar 4.4 - Shreshth Gandhi on Scaling Perturbation-Trained Single-Cell Foundation Models.md)
