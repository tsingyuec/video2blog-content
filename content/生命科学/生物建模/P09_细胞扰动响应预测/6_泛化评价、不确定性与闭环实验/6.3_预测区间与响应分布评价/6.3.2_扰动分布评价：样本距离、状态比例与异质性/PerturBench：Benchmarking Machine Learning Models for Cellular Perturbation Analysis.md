# PerturBench: Benchmarking Machine Learning Models for Cellular Perturbation Analysis

- 视频标题：PerturBench: Benchmarking Machine Learning Models for Cellular Perturbation Analysis
- 视频链接：https://www.youtube.com/watch?v=5M0HWIjmEhQ
- 时长：约 55 分钟（55:52）

## 视频主线

这是 Altos Labs 的 Yan Wu 与 Esther 在 Multiomics Reading Group 上介绍 PerturBench：一个把数据、切分、加载器、模型和指标拆成模块的扰动预测基准。她们先解释为什么虚拟细胞模型需要统一评测，再按“数据—指标—主结果—消融—数据实验—局限”的顺序展示实验。核心结论是：简单模型在部分指标上不输复杂模型，新的 rank 指标能揭穿“把所有扰动预测成同一个平均态”的塌缩，而数据规模、不平衡与组合扰动仍是开放问题。

## 一、为什么需要 PerturBench：扰动空间不可穷举，虚拟细胞只能补响应空间

讲者先从实验端讲起：高通量筛选方法的进步，让湿实验人员可以一次敲低或扰动上万个、甚至上十万个基因，并配合某种细胞读出。她们关注的模型主要使用**单细胞 RNA 测序**——一种高维、信息丰富的读出，可以理解基因表达程序以及扰动的真实效应。小分子化学扰动、成像等其他技术也打开了这个空间，但这项工作的重点仍是**转录组表型**。[【跳转到 01:00】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=60) [【跳转到 01:25】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=85) [【跳转到 01:50】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=110) [【跳转到 02:15】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=135)

但即使有这些高通量技术，要在人体所有细胞类型与状态（脑、皮肤、肺……）里穷举测量扰动效应，成本仍然高得不可行；一旦涉及组合，就几乎不可能。人类基因组约有 2 万个蛋白编码基因，每一对基因都做实验，在任何实验形式下都基本不现实。之所以关心不同细胞类型与状态，是因为神经元并不等于阿尔茨海默病中的神经元，后者的细胞状态会发生明显偏移，而高通量基因组 profiling 让领域得以更好地理解这些差异。[【跳转到 02:40】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=160) [【跳转到 03:05】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=185)

这正是虚拟细胞模型的用武之地：帮助预测扰动效应，勾勒出一个用其他方式无法绘制的响应空间。讲者举了一个例子（也只是例子）：Yusuf Roohani 的模型预测了 5000 对双扰动效应，而训练只用了约 120 对。这样可以把手头宝贵的湿实验资源集中在最有趣、最可能与疾病相关的扰动上。[【跳转到 03:05】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=185) [【跳转到 03:30】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=210) [【跳转到 03:55】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=235)

## 二、真正难的是训练数据：测量是破坏性的，只有“条件配对”的两群细胞

虚拟细胞模型的关键挑战是：**无法测量同一个细胞扰动前和扰动后的状态**。大多数测量技术是破坏性的，会把细胞裂解。我们能得到的只是**条件配对**的训练数据：一群没有受扰动的对照细胞，以及分别接受不同扰动的细胞群，但并不知道哪个对照细胞对应哪个扰动细胞。模型真正要做的是**反事实预测**——假如这团对照细胞接受了某个扰动，它会变成什么样。这也决定了必须仔细设计训练策略。[【跳转到 04:20】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=260) [【跳转到 04:45】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=285)

报告聚焦两类反事实任务。第一类是**组合扰动预测**：已经见过扰动 A 和 B 单独作用，预测 A+B 同时施加的效果。第二类是**细胞状态迁移**：在细胞类型 1、2 中见过某扰动，预测它在细胞类型 3（或细胞系 3）中的效果。论文没有覆盖所有任务，只集中在这两类。[【跳转到 05:10】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=310) [【跳转到 05:35】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=335)

## 三、三个缺口与五块积木：现有工作缺生物学指标、统一框架与开发评测一体

这个方向已有不少相关工作，包括 2025 年正在进行的 ARC 虚拟细胞竞赛，以及多篇针对单细胞基础模型、调控网络、多样数据集的基准论文。讲者没有逐篇展开，而是指出三个仍然重要的缺口。[【跳转到 05:35】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=335) [【跳转到 06:00】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=360)

第一，缺少**生物学相关的指标**，尤其是能评价“扰动排序”和“扰动在细胞间的完整异质效应”、而不只是平均效应的指标。第二，缺少统一的软件框架，来系统做模型与数据消融、规模扩展实验。第三，现有工作里还没有一个平台同时支持“开发模型”和“评测模型”。[【跳转到 06:00】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=360) [【跳转到 06:25】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=385) [【跳转到 06:50】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=410)

PerturBench 提供的就是这五块积木：跨多个规模、同时包含遗传与化学小分子扰动的单细胞扰动数据集；带**生物学相关切分**的数据切分器（对应细胞状态迁移与组合预测两类问题）；匹配两条主流训练策略的预置数据加载器；模块化模型库（已发表模型 + 强基线，并能消融组件）；以及包含新式 rank/排序指标和分布指标的标准基准。[【跳转到 06:50】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=410) [【跳转到 07:15】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=435) [【跳转到 07:40】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=460) [【跳转到 08:05】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=485)

![PerturBench 的五个模块：数据集、生物学切分、加载器、模型库与标准化基准](assets/PerturBench：Benchmarking Machine Learning Models for Cellular Perturbation Analysis/00435.webp)

## 四、两条训练路线：对照匹配与表示解耦

既然没有真正一对一的“扰动前—扰动后”配对，训练策略主要有两派。[【跳转到 08:05】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=485)

第一派做**对照匹配（control matching）**：为每个扰动细胞随机抽一个对照细胞，并施加条件，比如二者必须来自同一细胞类型；如果有批次等协变量，还可以要求同一批次。大多数基础模型采用这种策略，最早由 GEARS 的 data loader 引入。更复杂的做法不只是随机抽样，而是用最优传输之类的方法，为给定扰动细胞匹配“最可能”的对照细胞，例如较新的 CellFlow。[【跳转到 08:30】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=510) [【跳转到 08:55】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=535) [【跳转到 09:20】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=560)

第二派做**表示解耦（disentanglement）**：这些模型本质上是自编码器，输入是扰动细胞的表达谱，输出是同一个扰动细胞表达谱的重建。但为了让模型不能像普通自编码器那样“原样传过去”，它必须把潜在空间拆成“扰动表示”和“未扰动表示”两部分；推理时就可以把新的扰动与未扰动表示组合，得到有意义的反事实预测。CPA、SAM-VAE、BioLord 属于这一类，各自有不同的解耦策略。[【跳转到 09:45】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=585) [【跳转到 10:10】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=610) [【跳转到 10:35】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=635)

## 五、强基线：latent additive、decoder-only、covariate-only

模型库里不只有已发表模型，还有几条很强的基线，而不只是“均值预测”这种简单参照。[【跳转到 10:35】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=635)

**latent additive** 采用 GEARS 的对照采样思路：抽一个随机对照细胞，按协变量与扰动细胞条件匹配；把对照细胞与协变量编码到潜在空间，再加上扰动的潜在表示，最后解码出扰动细胞表达。论文里扰动表示用的是 one-hot 编码，但也可以换成其他嵌入。[【跳转到 11:00】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=660) [【跳转到 11:25】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=685)

为了弄清“到底是哪个组件在贡献性能”，他们又做了更简单的消融版本。**decoder-only** 完全不编码对照细胞的表达，只用 MLP 把扰动 + 协变量（论文里都是 one-hot）映射到扰动细胞表达；**covariate-only** 则进一步把扰动信息也去掉，只看协变量。[【跳转到 11:25】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=685) [【跳转到 11:50】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=710)

![基线模型：latent additive 在潜在空间相加，decoder-only 完全跳过对照细胞表达](assets/PerturBench：Benchmarking Machine Learning Models for Cellular Perturbation Analysis/00710.webp)

## 六、已发表模型怎么重实现：GEARS 加 scGPT 嵌入，CPA 去对抗，SAM 去稀疏

论文重实现了几个已发表模型。GEARS 做对照匹配，并用图神经网络从基因本体（GO）与共表达信息中嵌入扰动；作者还用 scGPT 生成细胞嵌入，替代基因表达作为模型输入，想测试这些嵌入作为细胞状态表示到底有多强。[【跳转到 11:50】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=710) [【跳转到 12:15】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=735) [【跳转到 12:40】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=760)

对 CPA 和 SAM-VAE，他们重点做了组件消融。CPA 是组合扰动自编码器，包含一个**对抗分类器**来解耦潜在空间；他们去掉对抗组件再测。SAM-VAE 则通过对潜在空间加正则，保证扰动效应稀疏；他们去掉这个稀疏正则，再测模型的核心组件。[【跳转到 12:40】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=760) [【跳转到 13:05】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=785)

## 七、为什么自建框架：现有工具都围绕单一模型，消融很难做

讲者认为 PerturBench 补上了模型开发基础设施的一个缺口。现在很多公开的扰动效应预测模型（也就是常说的“虚拟细胞”）通常围绕**单一模型**设计；单细胞 RNA 测序/组学领域已有的基础设施也往往围绕单一模型类，比如很流行的 scvi-tools 就围绕变分自编码器。这导致用现有基础设施做模型与数据消融常常很困难，因为这些仓库都是围绕某个模型搭的。[【跳转到 13:05】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=785) [【跳转到 13:30】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=810) [【跳转到 13:55】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=835)

他们想要一个**对深度学习方法不敏感**的平台：可以用任何深度学习架构，甚至非深度学习架构；模块化，任何组件都能独立替换；可配置，容易跑实验、试新想法；可扩展，容易加新模型和新数据集。框架的相当一部分架构由同事 Marcel 设计。[【跳转到 13:55】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=835) [【跳转到 14:20】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=860)

## 八、数据集：6 个数据集、9 万到 160 万细胞，按生物学问题切分

PerturBench 收录 6 个单细胞扰动数据集，讲者没有逐个展开，只说明它们覆盖化学小分子与遗传扰动，规模差异很大——从约 9 万个细胞到 160 万个细胞——并包含多种生物学状态（细胞类型或细胞状态），以及单扰动与双扰动。[【跳转到 14:20】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=860) [【跳转到 14:45】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=885)

切分按生物学问题组织：组合任务留出部分双扰动，迁移任务留出部分细胞状态。这样评测的就不是随机插值，而是“对新组合”或“对新细胞状态”的泛化。[【跳转到 07:15】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=435) [【跳转到 14:45】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=885)

## 九、指标：只看 RMSE 与余弦不够，要看排序与分布

很多基准研究关注“模型拟合得好不好”，PerturBench 也收录了这些指标，比如均方根误差（RMSE）、扰动相对对照的 log fold change 的余弦相似度，用来衡量绝对与相对预测误差。[【跳转到 15:10】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=910) [【跳转到 15:35】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=935)

但讲者认为，真正缺的是能抓住**关键生物学用例**和**关键失败模式**的指标。他们实现了新的 **rank 指标**，检查扰动是否被正确排序。做法是：拿真实扰动 A 的表达谱，与模型对 A、B、C……所有扰动的预测逐一算余弦相似度，再按相似度排序。如果模型学得好，预测的 A 应该与真实 A 最相似、排第一；如果预测的 B 排到中间，就说明没有正确排序。[【跳转到 15:35】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=935) [【跳转到 16:00】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=960) [【跳转到 16:25】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=985) [【跳转到 16:50】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1010)

他们没有用更常见的 k-recall，是因为不同数据集的扰动数量差别很大：有时 100 个，有时 300 个，有时 3000 个，k-recall 难以跨数据集比较；这个 rank 指标是为本基准“按用途定制”的，更可校准。完美排序记为 0，随机排序为 0.5，因此**越低越好**。[【跳转到 16:50】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1010) [【跳转到 17:15】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1035)

![排序指标：预测的扰动 A 应排在与真实 A 最相似的位置；排错则说明模型没有扰动特异性](assets/PerturBench：Benchmarking Machine Learning Models for Cellular Perturbation Analysis/00960.webp)

另外两个是**分布指标**，用来捕捉扰动响应的异质性。过去很多研究只看模型是否准确预测了平均扰动响应，他们还想看模型能否捕捉细胞层面的异质性——不是每个细胞都会以同样方式响应，有些细胞甚至完全不响应。[【跳转到 17:40】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1060) [【跳转到 18:05】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1085)

第一个是**最大均值差异（MMD）**，比较预测分布与真实分布的整体形状，而不只是均值，能覆盖数据的多个模态。第二个是**差异表达基因召回（DEG recall）**，对应“哪些基因在动”这一核心生物学用例：用差异表达基因 calling 衡量模型能找回多少真实变化的基因。[【跳转到 18:05】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1085) [【跳转到 18:30】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1110)

![MMD 比较整个分布，DEG recall 看前 20 个差异表达基因找回多少](assets/PerturBench：Benchmarking Machine Learning Models for Cellular Perturbation Analysis/01085.webp)

## 十、实验设置：重实现模型，每个数据集 60 组超参、4 个种子

讲者先概括这项工作的复杂度：扰动响应建模有很多可变的维度——扰动细胞如何与对照细胞匹配、数据如何处理、data loader、模型本身、模型特征，以及判断模型好坏的基准。他们希望代码库能让这些决策点的收益容易被分析，并通过消融严格检验。[【跳转到 18:55】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1135) [【跳转到 19:12】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1152) [【跳转到 19:37】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1177)

实现上，他们自行重实现了 CPA、SAM-VAE 和 BioLord；GEARS 通过 wrapper 使用相同的数据集与切分。基线包括线性模型、latent additive，以及 latent additive 的子集 decoder-only 和 covariate-only。[【跳转到 19:37】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1177) [【跳转到 20:02】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1202)

每个数据集、每个模型都做 60 组超参数搜索，用验证集上的 RMSE 与 RMSE rank 选最佳；找到最优超参后，再用 4 个不同随机种子重训。此外还测试了用 scGPT 嵌入替代基因表达后，对 latent additive 与 CPA 的影响。[【跳转到 20:02】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1202) [【跳转到 20:27】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1227)

![实验设置：重实现 CPA、SAM-VAE、BioLord，每个数据集 60 组超参、4 个种子，并测试 scGPT 嵌入](assets/PerturBench：Benchmarking Machine Learning Models for Cellular Perturbation Analysis/01252.webp)

## 十一、先用 Srivatsan20 试水：小、平衡、化学效应强

他们的“首选”数据集是一个较小的化学扰动数据集 Srivatsan20。之所以每引入一个新特性都先在这里试，是因为它规模小、完全平衡：188 个扰动分布在 3 个细胞系中（每个细胞系留出 30% 药物做测试）。而且化学扰动的效应通常比遗传扰动更强，更容易识别，也更容易让模型收敛、调参和逐步放大。[【跳转到 20:27】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1227) [【跳转到 20:52】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1252) [【跳转到 21:17】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1277)

## 十二、平均效应：SAM-VAE 与 CPA 的“核心创新”都不是性能来源

第一张表看平均效应。提醒一下：余弦相似度越高越好，rank 越低越好；加粗的是每个指标下最好的模型。[【跳转到 21:17】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1277) [【跳转到 21:42】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1302)

结果有三点值得注意。第一，**SAM-VAE 去掉稀疏正则后取得最好的余弦相似度，CPA 去掉对抗解耦后取得最好的 rank**。也就是说，这两篇论文的招牌创新并不是带来好性能的原因。这正说明消融的必要性：模型引入不同特性时，必须一项一项测。[【跳转到 21:42】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1302) [【跳转到 22:07】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1327) [【跳转到 22:32】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1352)

第二，加入 scGPT 细胞嵌入后性能几乎不变。这说明，如果 scGPT 嵌入真有什么价值，我们还没找到正确用法，它带来的增量仍有很大问号。[【跳转到 22:32】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1352) [【跳转到 22:57】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1377)

## 十三、rank 指标揭穿塌缩：covariate-only 余弦尚可，排序却接近随机

第三点最能说明新指标的意义：**covariate-only** 完全不编码扰动信息，也不编码基因表达，只凭协变量。它在余弦相似度上表现还算可以，看起来“还行”；但 rank 非常差，基本等于随机。[【跳转到 23:22】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1402)

这正是模型**塌缩**：它预测的东西与具体扰动无关，只是一个模糊的平均响应；而 rank 指标把它揪了出来。讲者对此很满意，因为这个指标能检验模型是否真的具有**扰动特异性**，也正在被扰动响应建模领域采纳——ARC 虚拟细胞竞赛就把它作为“扰动判别分数”使用，只是略有变体。[【跳转到 23:22】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1402) [【跳转到 23:47】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1427) [【跳转到 24:12】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1452)

## 十四、分布指标：自编码器在 MMD 上占优，但 DEG recall 全员很差

第二张表看分布指标 MMD 与 DEG recall。首先，**自编码器模型优于基线**，这是个好迹象，说明更复杂的模型确实捕捉到一部分分布层面的复杂性。[【跳转到 24:37】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1477) [【跳转到 25:02】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1502)

但**所有模型的 DEG recall 都很差**。讲者的解释是：这个领域还处在早期，模型本身可能还不够精细，预测能力存在天花板；这些都是开放问题。[【跳转到 25:02】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1502) [【跳转到 25:27】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1527)

他们还观察到另一个现象：在 OP3 数据上（没有展示表格），自编码器与基线的 MMD 差距更大。他们的假设是，这个数据集在细胞类型内部的异质性更强，因此“平均细胞”不足以代表整个分布。这意味着需要先刻画数据特征，再想办法把这些特征纳入模型。新指标让这些学习点变得可见，但仍有工作要做。[【跳转到 25:27】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1527) [【跳转到 25:52】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1552) [【跳转到 26:17】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1577) [【跳转到 26:42】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1602)

## 十五、组合扰动：多数效应可加，深度学习赢在非线性，latent additive 总体最好

组合任务使用 Norman 2019：131 个双基因扰动，训练见过全部单扰动、留出 70% 的双扰动。公开的组合扰动数据不多，这基本是首选数据集。[【跳转到 26:42】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1602) [【跳转到 27:07】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1627)

结果发现，**多数双扰动效应近似线性可加**，线性模型表现尚可；但深度学习模型更好，说明它们已经能捕捉一部分非线性相互作用。讲者认为，这正是扰动响应建模相对实验的价值所在：当实验搜索空间太大时，可以用计算模型去缩小候选组合，而有意义的组合很可能就在非线性空间里。[【跳转到 27:07】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1627) [【跳转到 27:32】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1652)

在这个任务上，**latent additive 总体最好**；非稀疏版 SAM-VAE 与非对抗版 CPA 再次优于原版，进一步说明“逐项测试”的必要。[【跳转到 27:32】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1652) [【跳转到 27:57】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1677) [【跳转到 28:22】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1702)

![Norman19 组合扰动：多数效应线性可加，latent additive 总体最好](assets/PerturBench：Benchmarking Machine Learning Models for Cellular Perturbation Analysis/01677.webp)

## 十六、decoder-only 的启示：当前扰动表示比基因表达更值钱

看到非稀疏 SAM 与非对抗 CPA 反而更好，讨论人忍不住问：去掉这些组件，究竟反映了**模型归纳偏置与扰动数据结构的错配**，还是仅仅因为生物噪声太难解耦，去掉约束反而提升了性能？作者坦言不知道，认为两种假设都值得测。[【跳转到 28:22】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1702) [【跳转到 28:47】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1727) [【跳转到 29:12】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1752)

Yan 补充：归纳偏置的角度很有意思，因为经常看到组件越少、模型越简单反而越好。部分原因可能是他们对每个数据集上的每个模型都做了超参搜索，调得很充分；也可能某些组件让模型更鲁棒。要真正理解对抗组件在做什么，可能得看梯度之类的东西，还需要深挖。[【跳转到 29:12】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1752) [【跳转到 29:37】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1777) [【跳转到 30:02】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1802)

另一个让他们意外的结果是 **decoder-only 模型表现很好**：它完全不看对照细胞的基因表达，只凭扰动与协变量就能预测得不错。甚至只输入嵌入、不输入基因表达数据的模型，整体表现也相当好。这暗示“潜在扰动表示”里可能真有实质结构——**当前阶段，扰动表示本身的价值可能比基因表达更大**。[【跳转到 30:02】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1802) [【跳转到 30:27】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1827) [【跳转到 30:52】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1852)

不过也要留个限定：covariate-only 是一个下界；decoder-only 表现好，说明这些模型**还没能充分利用基因表达信息**，也可能只是基因表达里的噪声盖过了信号。[【跳转到 30:52】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1852) [【跳转到 31:17】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1877)

## 十七、数据变多不一定更好：复杂模型在更大更复杂的数据上反而退化

第一组数据实验使用 McFaline-Figueroa23：525 个基因敲低、15 种细胞状态，留出 3 个细胞状态中 70% 的敲低。作者把数据子集分成小、中、大训练集，想看“数据变多后性能如何变化”。[【跳转到 31:17】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1877) [【跳转到 31:42】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1902)

直觉是数据越多越好，但数据同时也更复杂。结果恰恰相反：**CPA（金色线）的性能随训练数据增加大幅下降；SAM-VAE（青绿色线）也随数据变多而变差**。也就是说，数据的复杂度本身构成了挑战。需要思考能否给模型加入一些特征，去刻画数据的这种“性格”。[【跳转到 31:42】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1902) [【跳转到 32:07】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1927) [【跳转到 32:32】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1952)

![随训练数据增大，部分复杂模型的排序性能反而下降，latent additive 最稳](assets/PerturBench：Benchmarking Machine Learning Models for Cellular Perturbation Analysis/01952.webp)

## 十八、数据不平衡：所有模型都变差，latent additive 受影响最大

第二组实验人为制造**数据不平衡**。Srivatsan20 原本完全平衡：每个细胞系都能看到全部扰动；他们取子集、换不同 data loader，让某些细胞系只见到部分扰动。具体包括 0.0（188, 188, 188）、0.1（188, 117, 50）、0.2（188, 81, 30）、0.3（188, 30, 30）几种不平衡程度。[【跳转到 32:57】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=1977) [【跳转到 33:22】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=2002)

结果是**所有模型性能都下降**，其中 latent additive 受影响最大；一个初步迹象是 scGPT 嵌入可能提供一定缓冲，也就是这类嵌入或许带来某种鲁棒性。但要注意，他们没有为每一种不平衡程度重新做超参搜索，所以这只能算初步结果。讲者强调，不平衡才是更真实的世界：高通量 Perturb-seq 数据往往不会在每个细胞类型里都覆盖每个扰动，整合不同数据集时更是如此。[【跳转到 33:22】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=2002) [【跳转到 33:47】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=2027) [【跳转到 34:12】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=2052)

![数据越不平衡，所有模型都变差；scGPT 嵌入可能带来一些鲁棒性](assets/PerturBench：Benchmarking Machine Learning Models for Cellular Perturbation Analysis/02027.webp)

## 十九、“生物噪声地板”讨论：降噪、正则与损失加权都是开放问题

讨论人把“数据变复杂反而更差”引向一个更根本的问题：是否存在某种**内在的生物噪声极限**，使得多出来的数据并不能转化为更干净的信号？另一种解释在模型侧——更复杂的模型就是不会正则化，而简单模型只拟合它知道的东西，数据一多反而不行。如果真能找到办法去掉这层掩盖真实信号的噪声地板（组合数据也许能提供干净的扰动贡献），降噪会不会有帮助？或者，一个带强正则项的复杂模型能否缓解数据问题？[【跳转到 34:12】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=2052) [【跳转到 34:37】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=2077) [【跳转到 35:02】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=2102) [【跳转到 35:27】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=2127) [【跳转到 35:52】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=2152)

作者回应：这些实验用的都是平均指标，换成分布指标后，更复杂的模型也许仍会占优，这个实验应该补做。做特征选择、把信号从噪声里挑出来很诱人，但模型又很容易塌缩、过度简化；存在一个权衡——究竟是真的预测到了一些信号，还是只预测了一个“代表真实总体”的东西。[【跳转到 36:17】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=2177) [【跳转到 36:42】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=2202) [【跳转到 37:07】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=2227)

另一位讲者补充：Shift Bioscience 出过几篇预印本，讨论如何在这些数据上度量误差。他们发现，在非常大的基因表达向量上直接算 MSE 往往很吵；如果在损失函数中给效应更强的扰动（或它们影响的基因）更高权重，性能可以更好。所以数据噪声、以及如何从超大数据集中提取信号，仍然完全是开放问题。[【跳转到 37:07】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=2227) [【跳转到 37:32】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=2252) [【跳转到 37:57】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=2277)

## 二十、局限与结论：rank 指标是最该带走的东西

讲者主动交代了几条局限。第一，部分模型是他们自行重实现的，虽然尽力而为，但可能漏掉原实现的某些细节。第二，超参搜索有可能卡在局部最优。第三，论文发表后出现了 CellFlow 与 STATE 两个很有影响的新模型，本研究没有纳入，但用这个代码库完全可以补测。[【跳转到 38:22】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=2302) [【跳转到 38:47】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=2327)

总结起来：**简单模型在某些指标、某些场景下确实优于复杂模型；但自编码器在分布层面仍优于基线**。消融研究极其重要——创新点很多、决策点很多，必须一项一项测。decoder-only 表现这么好，说明当前**扰动表示比基因表达更重要**；而很多模型容易塌缩，新的 rank 指标能在很大程度上防止这种塌缩。[【跳转到 38:47】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=2327) [【跳转到 39:12】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=2352) [【跳转到 39:37】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=2377)

如果只能从报告里带走一件事，那就是**使用 rank 指标**；如果能带走两件，第二件是去看看 PerturBench 仓库——里面有模型、数据集、指标和评测，也可以只拿自己的模型来评。代码已公开，NeurIPS 还有报告与海报。[【跳转到 40:02】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=2402) [【跳转到 40:27】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=2427)

## 二十一、问答：扰动表示是端到端学的，虚拟细胞还远不是水晶球

第一个问题问 latent additive 里的扰动表示是怎么学的：是在自编码器潜在空间里端到端训练，还是当成一个单独任务？如果单独学，是否正是这种灵活性解释了它为何能赢过更复杂的模型？[【跳转到 40:52】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=2452) [【跳转到 41:17】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=2477) [【跳转到 41:42】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=2502)

讲者解释：CPA 与 SAM-VAE 这类自编码器，如果把对照细胞输入换成扰动细胞输入，训练方式其实几乎一样；它们都对扰动表示做加性条件。区别在于 SAM-VAE 试图让这个向量稀疏，CPA 则用一个辅助分类器，试图把扰动信息从“未扰动表示”里剥离出去。[【跳转到 42:07】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=2527) [【跳转到 42:32】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=2552) [【跳转到 42:57】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=2577)

需要澄清的是：被编码为“扰动”的并不是扰动细胞本身，而是扰动的 **one-hot 表示**；对照/未扰动细胞则与扰动表示一起，被解码成扰动细胞。现在也有人用蛋白质语言模型 ESM2 表示基因、或用其他方式表示小分子，但这项研究里统一用 one-hot。所有模型都是端到端训练的；至于先把扰动表示单独学好、再喂给 latent additive，是个有意思的想法，但本文没有这样做。[【跳转到 43:22】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=2602) [【跳转到 43:47】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=2627) [【跳转到 44:12】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=2652) [【跳转到 44:37】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=2677) [【跳转到 45:02】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=2702) [【跳转到 45:27】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=2727)

另一位听众提到已有工作专门预训练扰动表示（讲者提到一篇叫 PR 的论文），并讨论先验知识图谱。讲者回应：这确实是很活跃的方向；decoder-only 能工作，本身就说明扰动表示很重要。不过本文没有深入比较不同表示或先验知识图谱，建议去看 PR 及同类工作。[【跳转到 47:32】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=2852) [【跳转到 47:57】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=2877) [【跳转到 48:22】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=2902) [【跳转到 48:47】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=2927) [【跳转到 49:12】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=2952) [【跳转到 49:37】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=2977)

还有人问：能不能像强化学习那样“在硅基里”生成扰动，而不是依赖真实数据？讲者澄清，他们**全部使用实验产生的 Perturb-seq 数据**：遗传或化学扰动施加到真实细胞上，读出转录组；测量是破坏性的，没有任何合成数据。当然，未来并非不可能。[【跳转到 45:52】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=2752) [【跳转到 46:17】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=2777) [【跳转到 46:42】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=2802) [【跳转到 47:07】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=2827)

最后一个“蓝天”问题：如果要把 PerturBench 演化成虚拟细胞建模的“图灵测试”，会加入什么、怎么扩展？Yan 先说，她不太喜欢“虚拟细胞”这个模糊的词，更愿意聚焦具体问题——生成反事实预测。这个方向正在变好，Shift Bioscience 的预印本也给出了多组指标。她认为一个大缺口是**多模态**：JUMP Cell Painting 联盟有大量成像扰动数据，但通常没有和单细胞 RNA 测序一起用，打通这些模态会很有意思。另一个、也是最大的缺口仍是**数据**：公开数据不少，但需要把数据结构化到能做真正泛化实验的程度；Tahoe-100M 这类大规模化学扰动（癌球）数据里有大量细胞类型、状态和供体，可以检验真正的跨细胞类型泛化，而只有 3 个细胞类型时大多数模型很难泛化。组合扰动空间里，Norman 2019 仍最大的数据集，可能还需要大两个数量级的数据才能真正理解组合扰动。[【跳转到 50:02】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=3002) [【跳转到 50:27】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=3027) [【跳转到 50:52】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=3052) [【跳转到 51:17】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=3077) [【跳转到 51:42】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=3102) [【跳转到 52:07】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=3127) [【跳转到 52:32】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=3152) [【跳转到 52:57】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=3177) [【跳转到 53:22】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=3202)

Esther 补充：很多实验是在“超干净”、一切都分割好的条件下做的，建模时必须想清楚怎么处理生物噪声，但这可能是另一个话题。她认为，虽然不抓眼球，但**高质量指标**的价值才刚刚开始被挖掘；进入多模态后可能还需要新的指标。选择这么多、噪声这么大，更要保持严谨，这是 PerturBench 想坚持的事。她也同样不喜欢“虚拟细胞”一词，因为它暗示某种水晶球；尤其在转录组层面，预测的精细度有真实上限，这一点必须清醒。[【跳转到 53:22】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=3202) [【跳转到 53:47】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=3227) [【跳转到 54:12】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=3252) [【跳转到 54:37】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=3277) [【跳转到 55:02】](https://www.youtube.com/watch?v=5M0HWIjmEhQ&t=3302)

## 小结

- 统一基准后，**简单模型在若干指标与场景下不输复杂模型**；复杂自编码器只在分布层面占优。
- **rank 指标**是本次最重要的工具：它能让“所有扰动都预测成同一个平均态”的模型原形毕露，已被 ARC 竞赛采用。
- **消融必须逐项做**：SAM-VAE 的稀疏约束、CPA 的对抗解耦都不是性能来源，去掉反而更好。
- **扰动表示比基因表达更关键**：decoder-only 模型表现很好，说明当前模型还没充分利用对照细胞的表达信息。
- **数据不是越多越好**：规模与复杂度上升可能伤害复杂模型；数据不平衡会伤害所有模型。
- 基准本身很难，但正是它把“模型是否真的有用”变成可复现、可比较的问题。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| 组合扰动 | 同时施加两个扰动，检验效应能否由两个单扰动相加得到。 |
| 反事实预测 | 预测“这团对照细胞接受某个扰动后会变成什么样”。 |
| 对照匹配 | 为每个扰动细胞匹配一个同类型、同批次的对照细胞，作为“扰动前”的近似。 |
| 表示解耦 | 把潜在空间拆成未扰动与扰动两部分，以便组合出新扰动。 |
| latent additive | 在潜在空间把对照细胞表示与扰动表示相加，再解码成扰动细胞。 |
| decoder-only / covariate-only | 前者只看扰动与协变量，后者连扰动也不看，用来定位性能来自哪个组件。 |
| rank 指标 | 按预测与真实扰动的相似度排序；完美为 0，随机为 0.5。 |
| MMD | 最大均值差异，比较两个分布整体形状，而不只是均值。 |
| DEG recall | 差异表达基因召回，衡量模型找回真实变化基因的能力。 |
