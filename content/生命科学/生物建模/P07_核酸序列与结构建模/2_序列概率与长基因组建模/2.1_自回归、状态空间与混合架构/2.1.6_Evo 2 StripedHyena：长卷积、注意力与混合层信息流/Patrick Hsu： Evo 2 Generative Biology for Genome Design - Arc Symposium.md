# Patrick Hsu： Evo 2 Generative Biology for Genome Design - Arc Symposium

> 来源：[Patrick Hsu: Evo 2 Generative Biology for Genome Design - Arc Symposium](https://www.youtube.com/watch?v=Q1WNmfHz5sA)（YouTube，Arc Institute 联合创始人 Patrick Hsu 在 Arc Symposium 的报告，约 21 分钟）。本博客由视频演说图文稿整理而成，内容可核查。

## 本讲要解决的核心问题（SCQA）

**背景**：机器学习正在革新生物学——AlphaFold、ESM 这类模型已经能从序列预测蛋白质结构、蛋白-蛋白/蛋白-配体相互作用乃至 RNA 折叠。定向进化先驱 Frances Arnold 的观察是：80 年代我们不知道 DNA 如何编码酶功能，而今天"从实际操作上说，我们能读取和编辑任何 DNA 序列，却不能'谱写'它"。 [【跳转到 02:23】](https://www.youtube.com/watch?v=Q1WNmfHz5sA&t=143)

**冲突**：与整个细胞相比，这些分子层面的进展仍然相形见绌——细胞的结构与功能由各种分子间天文数字般的组合相互作用构成，比单个分子复杂许多个数量级。 [【跳转到 03:01】](https://www.youtube.com/watch?v=Q1WNmfHz5sA&t=181)

**疑问**：所有这些复杂性其实都编码在 DNA 这一条序列里，且进化通过突变在生命之树上代代"写下"功能适应——能否训练一台机器，从完整基因组中学会这门进化的"语法"，进而直接设计基因组？ [【跳转到 03:40】](https://www.youtube.com/watch?v=Q1WNmfHz5sA&t=220)

**回答（中心思想）**：可以。Arc 的 **Evo 系列证明"下一 token 预测"在 DNA 上同样成立**：Evo 1 用 3000 亿 token 的单细胞与噬菌体基因组预训练，131,072 碱基长上下文即学会多模态、多尺度的分子相互作用，能共设计 CRISPR-Cas 系统与转座子、零样本预测基因必需性、非受限生成百万碱基序列；Evo 2 把这条路推到全生命域——7B 与 40B 两档模型、数万亿 token 的 DNA 数据（接近 Llama 3 / GPT-4 的训练量）、100 万碱基上下文，在零样本变异效应预测（ClinVar、BRCA1）上成为通用强基线，SAE 可解释性读出生物学概念，并能生成线粒体基因组与整条酵母染色体，再挂奖励模型即可按需设计染色质可及性。 [【跳转到 07:58】](https://www.youtube.com/watch?v=Q1WNmfHz5sA&t=478)

## 一、动机：学会生命的语言

### 1.1 从"能读能改"到"能写"

Frances Arnold 的原话点出差距：我们可以从大自然"目录"里剪切、粘贴片段，却写不出一个酶的"音符"。所以在 Arc，团队想的是用学习模型设计**所有序列**——不仅是蛋白质，还包括基因组本身。 [【跳转到 01:59】](https://www.youtube.com/watch?v=Q1WNmfHz5sA&t=119)

![Frances Arnold 与蛋白质工程早期：能读能改 DNA，但不能谱写](assets/Patrick%20Hsu：%20Evo%202%20Generative%20Biology%20for%20Genome%20Design%20-%20Arc%20Symposium/00119.webp)

### 1.2 中心法则里藏着层级结构

DNA 转录为 RNA、翻译为蛋白质，但其中嵌着大量结构信息：序列连续、从左到右；转化与传递中有多层级的组织——信息层级跨越不同尺度。 [【跳转到 04:16】](https://www.youtube.com/watch?v=Q1WNmfHz5sA&t=256)

![中心法则示意图：DNA → RNA → 蛋白质及其中的信息层级](assets/Patrick%20Hsu：%20Evo%202%20Generative%20Biology%20for%20Genome%20Design%20-%20Arc%20Symposium/00256.webp)

## 二、"下一 token 预测"为什么普适

对英语来说，"to be or not to be"的下一个 token 人人都知道；对 DNA 来说，CRISPR 的"发明者"是细菌——给你 GTG，下一个核苷酸是什么？事实证明，**预测下一个 token 的能力惊人地普适**： [【跳转到 05:04】](https://www.youtube.com/watch?v=Q1WNmfHz5sA&t=304)

- 自然语言模型从下一词预测中学到的不只是语法：世界知识（阿塞拜疆首都是巴库）、空间推理（"走进厨房泡茶……然后离开厨房"）；
- 生物序列同理：残基的生化性质（疏水/亲水、结合口袋、疾病状态），以及功能相关基因在原核生物中以**操纵子（operon）**聚集的组织方式，都可以从序列中自学。 [【跳转到 05:28】](https://www.youtube.com/watch?v=Q1WNmfHz5sA&t=328)

![语言模型从下一词预测中学到语法之外的知识——生物序列同理](assets/Patrick%20Hsu：%20Evo%202%20Generative%20Biology%20for%20Genome%20Design%20-%20Arc%20Symposium/00328.webp)

## 三、Evo 1：第一次尝试（多模态 + 多尺度）

Evo 1 在 3000 亿 token 的单细胞生命与噬菌体基因组上预训练。把它做成 131,072 碱基的长上下文版本后，一段序列就能容纳 DNA 中的各种功能组件——调控 DNA、RNA 等都嵌在遗传密码里，模型随之学到分子间相互作用的规律。 [【跳转到 06:42】](https://www.youtube.com/watch?v=Q1WNmfHz5sA&t=402)

用机器学习的话说，Evo 1 是**多模态、多尺度**的： [【跳转到 07:17】](https://www.youtube.com/watch?v=Q1WNmfHz5sA&t=437)

![Evo 1 的跨模态共设计：蛋白质-RNA-DNA 语言模型协同](assets/Patrick%20Hsu：%20Evo%202%20Generative%20Biology%20for%20Genome%20Design%20-%20Arc%20Symposium/00437.webp)

- **跨中心法则层级共设计**：最早的蛋白质-RNA 或 DNA 协同设计例子——做出有功能的 CRISPR-Cas 系统、能真的在基因组里跳来跳去的 DNA 转座子；
- **生成之外还能预测**：在 CRISPR 筛选场景里，用神经网络的一次前向传播替代繁琐的湿实验判断基因必需性；
- **跨尺度生成**：完全不受约束的基因组生成，生成长达 **100 万碱基**的序列——正是这让团队决定把模型做大。 [【跳转到 07:58】](https://www.youtube.com/watch?v=Q1WNmfHz5sA&t=478)

## 四、Evo 2：把规模推到全生命域

Evo 2 是第一个在整个生命领域数据上训练的此类模型（不只是细菌，还有古菌与所有真核生物），训练了 7B 与 40B 两个模型，数据达数万亿 token 的 DNA——规模已接近最大的自然语言模型（Meta 的 Llama 3、DeepSeek、OpenAI 的 GPT-4）。 [【跳转到 08:38】](https://www.youtube.com/watch?v=Q1WNmfHz5sA&t=518)

![Evo 2 的 7B 与 40B：数据规模接近最大自然语言模型](assets/Patrick%20Hsu：%20Evo%202%20Generative%20Biology%20for%20Genome%20Design%20-%20Arc%20Symposium/00518.webp)

真核基因组极大，为此训练分两阶段：初始预训练每次 8,000 碱基，然后中期训练（mid-training）把上下文扩到 **100 万碱基**（约 Evo 1 的 10 倍）——单个分子、操纵子、原核基因组、带大量内含子的完整真核基因、乃至 M. genitalium 与酵母染色体都能装进上下文。 [【跳转到 09:08】](https://www.youtube.com/watch?v=Q1WNmfHz5sA&t=548)

架构上是改进的状态空间方案 **StripedHyena**：用改进版卷积在超长上下文上高效建模，吞吐量与迭代时间的衰减远小于稠密注意力 Transformer，显著提升大规模训练效率。 [【跳转到 09:33】](https://www.youtube.com/watch?v=Q1WNmfHz5sA&t=573)

## 五、零样本变异效应预测：从论文走向临床

第一篇论文之后，团队想做一个更有"转化"色彩的方向：**基因效应预测**。假如你在某个基因（比如 BRCA1）里有一个突变——它是致癌的因果突变，还是非致病的？由于模型在广阔的进化数据上训练，它对你的突变有一个"观点"：一个似然，可以用于零样本的变异效应预测。 [【跳转到 10:58】](https://www.youtube.com/watch?v=Q1WNmfHz5sA&t=658)

![用 ClinVar 数据检验 Evo 2 的零样本变异效应预测](assets/Patrick%20Hsu：%20Evo%202%20Generative%20Biology%20for%20Genome%20Design%20-%20Arc%20Symposium/00658.webp)

把 ClinVar（临床遗传突变数据库，标注致病/良性/未知）喂进去检验：在预测编码 SNV 或 indel 上，Evo 2 比专门针对编码 SNV 的模型稍差一点；但关键在于它是一个**通用模型**——能同时覆盖结构变异（SV）、非 SNV 与非编码突变。在"突变对基因表达/功能的影响"上 Evo 2 同样达到最先进水平；若再用模型嵌入训练监督头，分类效果还能更好。展望：随着基因组测序普及，这些模型的更强版本有望帮助解读全基因组范围内"意义未知"的变异。 [【跳转到 11:35】](https://www.youtube.com/watch?v=Q1WNmfHz5sA&t=695)

## 六、可解释性：模型"自己学会"了什么

机器学习里有可解释性（interpretability）方向：Anthropic（训练 Claude 的公司）在模型上训练**稀疏自编码器（SAE）**来学习模型识别的语义特征。最著名的例子是"金门大桥"特征——把该特征钳制（clamp）后，模型会说自己"就是金门大桥，旧金山湾区那座著名的悬索桥"。 [【跳转到 13:30】](https://www.youtube.com/watch?v=Q1WNmfHz5sA&t=810)

![Anthropic 的"金门大桥"特征：钳制后模型自称金门大桥](assets/Patrick%20Hsu：%20Evo%202%20Generative%20Biology%20for%20Genome%20Design%20-%20Arc%20Symposium/00830.webp)

团队对 Evo 2 做了同样的事：在模型某一层训练 SAE 去识别生物学特征。例子：有特征在真核基因组的**内含子**上、或外显子-内含子边界上激发；而且特征不只存在于 DNA——因为蛋白质信息同样嵌在基因组里，还有特征会在 **α 螺旋或 β 折叠**上点亮。 [【跳转到 14:34】](https://www.youtube.com/watch?v=Q1WNmfHz5sA&t=874)

## 七、谱写基因组：线粒体、酵母

回到生成。Evo 1 展示过非受限基因组生成的早期尝试；现在既然模型是通用的，团队能否生成人类线粒体基因组、染色体、乃至整个基因组？做法如同 ChatGPT 界面：**输入 DNA，返回 DNA**。给一段人类线粒体 DNA 提示，模型在不同轮生成中创造出多样的线粒体基因组，并保持人类线粒体基因组的共线性（synteny）——例如线粒体电子传递链（参与呼吸）的不同核心亚基；尽管序列多样性不同于天然，这些人工序列保持着正确的蛋白质相互作用。 [【跳转到 15:49】](https://www.youtube.com/watch?v=Q1WNmfHz5sA&t=949)

![线粒体基因组生成：多样但保持共线性与核心亚基的相互作用](assets/Patrick%20Hsu：%20Evo%202%20Generative%20Biology%20for%20Genome%20Design%20-%20Arc%20Symposium/00965.webp)

质量随模型规模"水涨船高"：从 Evo 1 到 Evo 2 7B 再到 40B，生成质量急剧上升——聚焦并打磨模型就能产出"有生命的序列"。除了完整基因组，团队还能生成真核染色体：酵母 3 号染色体，结果连贯、合理。 [【跳转到 16:50】](https://www.youtube.com/watch?v=Q1WNmfHz5sA&t=1010)

## 八、表观遗传与可控生成：把信息写进 DNA

DNA 语言模型绕不开的问题：**表观遗传学**怎么办——让细胞真正响应环境的那套东西？演示任务是用模型**设计染色质可及性**：把生成模型接到一个奖励模型上（判断生成的序列会带来高还是低的可及性），迭代地给奖励信号改变生成方向——可以做出宽的或窄的 ATAC-seq 峰；再加上推理时（inference-time）缩放规律，进一步提升命中高/低可及性的程度。这些预测目前正在湿实验中、在活细胞里检验。 [【跳转到 17:34】](https://www.youtube.com/watch?v=Q1WNmfHz5sA&t=1054)

![用生成模型+奖励模型设计染色质可及性（宽/窄 ATAC-seq 峰）](assets/Patrick%20Hsu：%20Evo%202%20Generative%20Biology%20for%20Genome%20Design%20-%20Arc%20Symposium/01054.webp)

你甚至能把信息"写"进 DNA：用摩斯电码写"Arc"或"Evo 2"——直接存储信息，还可能以染色质形式存储**表观遗传状态**。 [【跳转到 18:31】](https://www.youtube.com/watch?v=Q1WNmfHz5sA&t=1111)

## 九、结语：从比特到原子的通用范式

团队把这一切总结为一个非常通用的范式：**生成模型 + 任意序列-功能预测器**（结构、蛋白质、剪接……）。Evo 2 是"生物学的模型"——在生物信息的最基础层面训练，在 RNA、蛋白质乃至细胞尺度都有应用空间；其上可以长出一整个"应用商店"，服务各种计算或湿实验任务。 [【跳转到 19:09】](https://www.youtube.com/watch?v=Q1WNmfHz5sA&t=1149)

下一步是"从比特对齐到原子"：让大模型与实验数据对齐、改进预测；再往前，是超越"在活细胞中修改单个基因"——替换整条染色体、染色体臂，创造新的生物学：一个正在萌芽的领域——**生成式基因组设计（generative genome design）**。在 Arc 的技术中心，团队还在把不同模型与细胞状态测量整合，预测细胞对基因扰动与环境变化的响应。 [【跳转到 19:21】](https://www.youtube.com/watch?v=Q1WNmfHz5sA&t=1161)

## 小结

- **一条主线**：把"下一 token 预测"从英语搬到 DNA——Evo 1（3000 亿 token、131k 上下文）验证范式，Evo 2（7B/40B、数万亿 token、1M 上下文、全生命域）完成规模扩展；
- **读懂**：零样本似然即变异效应——ClinVar 上覆盖编码/非编码、SNV/indel/SV，BRCA1 表达效应达到最先进，嵌入+监督头可再增强；
- **看懂**：SAE 可解释性读出内含子、外显子边界、α 螺旋、β 折叠等概念；
- **谱写**：线粒体基因组（共线性+核心亚基正确相互作用）、酵母 3 号染色体；质量随 Evo 1 → 7B → 40B 快速上升；
- **可控**：生成模型 + 奖励模型设计染色质可及性（宽/窄 ATAC-seq 峰），推理时缩放加持，湿实验验证进行中；还能用摩斯电码把信息写进 DNA；
- **愿景**："生成模型 + 任意序列-功能预测器"的通用范式、从比特到原子的对齐、染色体级替换——生成式基因组设计。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| 生成生物学（generative biology） | 用生成式模型设计生物序列（蛋白、RNA、基因组）的方向 |
| 下一 token 预测 | 给定前文预测下一个词/碱基；Evo 系列逐碱基自回归建模 DNA |
| 操纵子（operon） | 原核生物中功能相关基因串联成簇的组织方式，可从序列中学到 |
| CRISPR 筛选 | 大规模扰动实验；Evo 可用一次前向传播替代湿实验预测基因必需性 |
| ClinVar | 临床遗传突变公共数据库（致病/良性/未知），用于检验变异效应预测 |
| SV / SNV / indel | 结构变异 / 单核苷酸变异 / 插入缺失——Evo 2 作为通用模型全覆盖 |
| SAE（稀疏自编码器） | 可解释性方法，把模型激活拆成可读概念（如"金门大桥"、内含子） |
| 共线性（synteny） | 基因顺序与组成的保守关系；生成的线粒体基因组保持了它 |
| 染色质可及性 / ATAC-seq | DNA 被调控元件"打开"的程度及其测量方法；本讲用它演示可控生成 |
| 生成式基因组设计 | Patrick Hsu 提出的萌芽领域：从修改单基因走向染色体级的设计与替换 |
