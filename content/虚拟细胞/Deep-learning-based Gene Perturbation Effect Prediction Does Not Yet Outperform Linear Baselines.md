# Deep-learning-based Gene Perturbation Effect Prediction Does Not Yet Outperform Linear Baselines

- 视频标题：Deep-learning-based Gene Perturbation Effect Prediction Does Not Yet Outperform Linear Baselines
- 视频链接：https://www.youtube.com/watch?v=ldYJ703CPBA
- 时长：约 58 分钟（58:22）

## 本讲要解决的核心问题（SCQA）

**背景**：单细胞扰动实验能一次读出扰动后成千上万个基因的表达变化。“扰动”（perturbation）指用 CRISPR 或药物改变某个基因的状态，而“转录组”是一次测到的全部基因表达量。数据越攒越多，深度学习模型便声称能预测“没做过的扰动”会让细胞变成什么样。

**冲突**：一批高影响力论文报告了很强的预测能力，但各自的数据、切分和指标并不统一。把它们放进同一基准、补上几条几乎不用学习的线性基线后，宣传中的优势没有出现。

**疑问**：模型究竟学到了可迁移的基因调控知识，还是只学会“表达谱大致长什么样”？问题出在模型还是指标？

**回答（中心思想）**：在双扰动与未见单扰动任务上，可加（additive）基线和“不变化/取均值”基线不输、甚至优于深度模型；模型没有表现出额外的生物学知识。指标确有缺陷，但换指标救不了复杂模型。出路是换更相关的训练数据，并重新追问“模型要回答什么生物学问题”。

## 一、基准的第一课：先定义“质量”，再谈分数

Wolfgang Huber 先泼了一盆冷水：**比较模型之前，必须先说清“质量”指什么**。一种定义是“符合规格”（adherence to specifications），比如零件尺寸、精度是否达标；另一种是“适合用途”（fitness for purpose），即能否解决你的问题。前者可量化，后者高度依赖场景——独自横跨大陆自驾，和接送四个孩子去训练，需要的车完全不同。[【跳转到 01:23】](https://www.youtube.com/watch?v=ldYJ703CPBA&t=83)

更难的是古德哈特定律（Goodhart's law）：**当一个度量变成目标，它就不再是一个好度量**。指标一旦成为目标，就会被优化甚至被钻空子。[【跳转到 03:41】](https://www.youtube.com/watch?v=ldYJ703CPBA&t=221) 扰动预测原则上存在“标准答案”，但选哪些基因、用什么距离、拿什么当对照，都会改变结论。[【跳转到 04:39】](https://www.youtube.com/watch?v=ldYJ703CPBA&t=279)

![“质量”有两种定义：符合规格与适合用途；这决定了基准要测什么](assets/Deep-learning-based Gene Perturbation Effect Prediction Does Not Yet Outperform Linear Baselines/00122.webp)

## 二、任务、数据与参战模型：预测“没做过”的扰动

作者把读出限定在转录组，因为它最容易大规模获取、又能反映细胞状态。可预测对象包括细胞命运、形态、代谢物等；报告主要聚焦**未见双扰动**，也涉及**未见单扰动**。[【跳转到 05:39】](https://www.youtube.com/watch?v=ldYJ703CPBA&t=339)

双扰动的设定很直观：训练集见过扰动 A 与 B 各自造成的状态，测试时把 A、B 同时施加，问模型能否预测“混合”后的状态。关键不在混合，而在**能否学到具体的混合方式**——简单相加，还是出现新相互作用。[【跳转到 06:29】](https://www.youtube.com/watch?v=ldYJ703CPBA&t=389)

基准使用 Norman 2019 数据：K562 细胞系，CRISPR 激活（CRISPRa，实际是过表达而非敲除），含 101 个单扰动、62 个双扰动、约 11 万个细胞。训练用全部单扰动加一半双扰动，测试另一半，并重复五个随机切分。[【跳转到 06:42】](https://www.youtube.com/watch?v=ldYJ703CPBA&t=402)

参战模型分三类：宣称可做扰动预测的 scGPT、scFoundation、GEARS；CPA 自编码器；外加线性解码器的 UCE、scBERT、Geneformer。对照组是“笨”基线：两单扰动变化直接相加的 **additive**、预测完全不变化的 **no-change**、预测已见扰动平均效果的 **mean**。[【跳转到 07:07】](https://www.youtube.com/watch?v=ldYJ703CPBA&t=427)

![Norman 2019：K562、CRISPR 激活、101 个单扰动与 62 个双扰动](assets/Deep-learning-based Gene Perturbation Effect Prediction Does Not Yet Outperform Linear Baselines/00402.webp)

## 三、核心结果：可加基线在双扰动上明显更好

作者用预测误差（predicted 与 observed 表达谱之间的 L2 距离）比较各模型。这里有个容易踩的坑：直接看所有基因的 R²，几乎所有方法都接近 1，因为基因间表达量差异远大于扰动效应，模型只要把高表达基因预测得高就能拿好分数。**只有先减去基线，扰动效应才会显露出来**。[【跳转到 08:22】](https://www.youtube.com/watch?v=ldYJ703CPBA&t=502)

在五个切分、上千个测试基因上，additive 基线的误差最低，明显优于 GEARS、scGPT、scFoundation。换成 Pearson delta（先减去对照均值再算相关）后结论几乎不变。[【跳转到 09:37】](https://www.youtube.com/watch?v=ldYJ703CPBA&t=577) 换前 100、前 1000 个高表达基因或差异表达基因，additive 优势仍稳定。[【跳转到 10:02】](https://www.youtube.com/watch?v=ldYJ703CPBA&t=602)

![减去基线前后：上半部分是原始表达，下半部分才看得见各方法的差异](assets/Deep-learning-based Gene Perturbation Effect Prediction Does Not Yet Outperform Linear Baselines/00552.webp)

作者自己也吃了一惊，便联系原论文作者，问是否把对方模型“调坏了”。回应之一是：重点也许不该是整体预测，而是“能否找出非可加基因”。于是有了第二轮检验。

## 四、非可加效应与未见单扰动：模型没有多学到生物学

非可加效应指双扰动的效果不能由两个单扰动相加解释：$\Delta_{AB} \neq \Delta_A + \Delta_B$。若实际效果落在“不扰动”和“可加预测”之间，称为**缓冲（buffering）**；超过可加预测则称为**协同（synergy）**。作者统计“观测值减可加预期”的分布，用正态零分布拟合钟形主体，把两侧超过 95% 置信界限的基因视为真正非可加；12 万个读出基因中筛出约 5000 个。[【跳转到 11:42】](https://www.youtube.com/watch?v=ldYJ703CPBA&t=702) [【跳转到 12:32】](https://www.youtube.com/watch?v=ldYJ703CPBA&t=752)

![用零分布划出非可加区间：缓冲落在对照与可加预测之间，协同则更高](assets/Deep-learning-based Gene Perturbation Effect Prediction Does Not Yet Outperform Linear Baselines/00752.webp)

再按预测偏离可加预期的程度排序，固定错误发现比例（FDP），看能召回多少真正非可加基因（TPR）。scGPT 的召回率低于 **no-change 基线**——直接预测“扰动不改变表达”，反而比 scGPT 更能找出真正的非可加基因。[【跳转到 14:37】](https://www.youtube.com/watch?v=ldYJ703CPBA&t=877) [【跳转到 15:02】](https://www.youtube.com/watch?v=ldYJ703CPBA&t=902)

![按预测偏离排序后，no-change 基线的真阳性率反而高于 scGPT](assets/Deep-learning-based Gene Perturbation Effect Prediction Does Not Yet Outperform Linear Baselines/00902.webp)

限制是 no-change 只预测缓冲、不预测协同；但模型也很少预测协同。no-change 并不完美，只是其他模型连这个下限都没稳定超过。[【跳转到 15:52】](https://www.youtube.com/watch?v=ldYJ703CPBA&t=952)

第三轮是未见单扰动：测试一个全新基因，最简单基线是直接预测已见扰动的平均状态。在 Replogle K562 上，mean 基线与各基础模型、深度学习模型相当；RPE1 与 Adamson 结论类似。模型没有证明自己学到了额外的基因调控网络。[【跳转到 17:32】](https://www.youtube.com/watch?v=ldYJ703CPBA&t=1052) [【跳转到 17:57】](https://www.youtube.com/watch?v=ldYJ703CPBA&t=1077)

唯一真正带来提升的做法，是在一个已测细胞系上训练线性模型，再迁移到另一个细胞系。这提示：**用更相关的扰动数据训练，可能比在庞大但嘈杂的观测图谱上预训练更有效**。[【跳转到 18:22】](https://www.youtube.com/watch?v=ldYJ703CPBA&t=1102)

![在 Replogle K562 上，mean 基线与各模型的单扰动预测误差相当](assets/Deep-learning-based Gene Perturbation Effect Prediction Does Not Yet Outperform Linear Baselines/01102.webp)

## 五、指标之争：换一把尺子，结论会变吗？

论文发表后，出现两篇“也许我们看错了指标”的工作：Systema 与 Miller 等。前者提出**质心准确率（centroid accuracy）**——看预测状态是否比任何其他扰动状态都更接近真实状态；以及**以扰动均值为参照的 Pearson delta**——先减观测扰动均值再算相关，以抵消系统性批次效应。[【跳转到 19:38】](https://www.youtube.com/watch?v=ldYJ703CPBA&t=1178) [【跳转到 20:03】](https://www.youtube.com/watch?v=ldYJ703CPBA&t=1203)

作者对第二点提出尖锐批评：在“未见扰动”任务里，基线本来就是所有扰动的均值；若预测和观测都减去它，additive 会被**强制变成 0**，根本没机会表现好。因此不能据此说“additive 不优”，除非重新设计对照。[【跳转到 23:20】](https://www.youtube.com/watch?v=ldYJ703CPBA&t=1400)

Miller 等的思路更有建设性：不只看负对照，还构造**正对照**。把观测细胞随机分半，用一半预测另一半；若某指标连“同一扰动的另一半细胞”都无法与负对照区分，它就不是好指标。用这种“校准”筛选指标后，他们认为按差异表达加权的均方误差（MSE）校准较好。[【跳转到 21:28】](https://www.youtube.com/watch?v=ldYJ703CPBA&t=1288) [【跳转到 22:32】](https://www.youtube.com/watch?v=ldYJ703CPBA&t=1352)

作者自己的取舍是：**用 MSE，且只在最高表达的一批基因上算**。因为单细胞计数在高表达基因上更可靠；只用差异表达基因会丢掉“没有变化”的负例——到处预测“有变化”的模型也能看起来不错。[【跳转到 24:10】](https://www.youtube.com/watch?v=ldYJ703CPBA&t=1450) [【跳转到 25:00】](https://www.youtube.com/watch?v=ldYJ703CPBA&t=1500)

![作者对各类指标与基因子集优缺点的总结：没有一个是完美选择](assets/Deep-learning-based Gene Perturbation Effect Prediction Does Not Yet Outperform Linear Baselines/01400.webp)

## 六、跳出指标：模型应该回答什么生物学问题

只争论“哪个指标最适合模型”仍是在盒子里思考：我们真正想理解的是增殖、T 细胞耗竭、收缩力这类**表型**，最终还要走向时空数据。[【跳转到 25:18】](https://www.youtube.com/watch?v=ldYJ703CPBA&t=1518)

讨论人补充：在批次校正、细胞注释、基因网络、插补等单细胞任务上，基础模型也常没超过专门设计的简单工具。[【跳转到 30:59】](https://www.youtube.com/watch?v=ldYJ703CPBA&t=1859) 一个常被忽略的因素是预训练数据。最大的模型用了约 5000 万个细胞，按 2 万个基因折算约一万亿 token，看似与语言模型同量级；但细胞来自少数供体、基因与细胞高度相关，**有效样本量**远没这么大。[【跳转到 33:11】](https://www.youtube.com/watch?v=ldYJ703CPBA&t=1991) 论文自己也承认：用单细胞图谱预训练相对随机嵌入收益很小，而用扰动数据预训练能提升预测。[【跳转到 33:57】](https://www.youtube.com/watch?v=ldYJ703CPBA&t=2037)

“更大”也不总是更好：规模与多样性增加不一定提升性能，可能存在学习饱和；更严重的是数据质量——一些低 intron fraction 的液滴其实是细胞碎片背景 RNA，却被原注释当成不同细胞状态，直接污染预训练。[【跳转到 34:58】](https://www.youtube.com/watch?v=ldYJ703CPBA&t=2098) 何况约 2 万维的表达向量本身就是很强的嵌入，是否还需要再学一层？再加上预训练、微调与推理成本，都值得权衡。[【跳转到 36:55】](https://www.youtube.com/watch?v=ldYJ703CPBA&t=2215)

问答部分给出两个方向。第一，**以线性模型为基线，学习残差**（如 salt-and-pepper），比从零训练复杂模型更务实。[【跳转到 48:52】](https://www.youtube.com/watch?v=ldYJ703CPBA&t=2932)第二，双扰动尤其是协同效应仍很难，可能需要新的表示方式，而非直接丢给梯度下降。[【跳转到 55:57】](https://www.youtube.com/watch?v=ldYJ703CPBA&t=3357) 作者也提醒：现有数据几乎都来自易转染、遗传背景单一的细胞系，既不像人体也无遗传多样性；用已知应影响转录的基因（转录因子、磷酸酶、酪氨酸激酶）构造正负对照，也许更贴近生物学。[【跳转到 46:22】](https://www.youtube.com/watch?v=ldYJ703CPBA&t=2782)

## 小结

- 在统一基准下，双扰动预测的赢家是**可加基线**；换 Pearson delta、换基因子集，结论依然稳定。
- 在“找非可加基因”和“预测未见单扰动”上，模型也没有超过 no-change 或 mean 这类下限，说明它们没有展现出额外的调控网络知识。
- 指标确实有坑：以扰动均值为参照的 Pearson delta 会把 additive 强制归零；只用差异表达基因则缺少负例。
- 作者推荐 MSE + 高表达基因，但承认没有完美指标；更根本的是先明确“模型要服务什么生物学问题”。
- 数据比架构更值得投资：在相关扰动数据上训练、跨细胞系迁移，比在庞大但嘈杂的观测图谱上预训练更有希望。
- 基准研究本身很难，也很难被看见；但正是它让“复杂模型是否真有增量”变成可以检验的问题。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| 扰动（perturbation） | 用 CRISPR、药物等手段改变细胞中某个基因或通路的状态。 |
| 双扰动 / 组合扰动 | 同时改变两个基因，检验两个单扰动是简单相加还是产生新效应。 |
| Pearson delta | 先减去对照（或扰动）均值再计算相关系数，用来聚焦扰动带来的变化。 |
| 质心准确率 | 看预测状态是否比任何其他扰动状态都更接近真实状态。 |
| buffering / synergy | 双扰动效果弱于/强于两个单扰动之和，分别对应缓冲与协同。 |
| FDP / TPR | 错误发现比例 / 真阳性率；固定 FDP 比较召回，是评估“找非可加基因”的方式。 |
