# Dr. Yu Li - RNA structure prediction with deep learning

> 视频来源：[YouTube《Dr. Yu Li - RNA structure prediction with deep learning》](https://www.youtube.com/watch?v=fdMkEk84Y4A)（44:25），主讲人 **李煜（Yu Li）**（香港中文大学计算机科学与工程系助理教授，AI & Healthcare 组带头人；本科于中国科学技术大学生物科学，博士于沙特 KAUST 计算机科学，曾在 MIT/哈佛与 James Collins 合作）。这是 CASP RNA 特别兴趣组（RNA SIG）系列研讨会的开场报告，也是 **RNA-FM 与 RhoFold 两个模型的作者亲讲**：从"RNA 结构预测为什么比蛋白质难"讲起，到 RNA-FM 预训练语言模型、二级结构预测 E2Efold、三维结构预测 RhoFold 的完整流水线与 CASP15/RNA-Puzzle 成绩单，最后是蛋白-RNA 相互作用（NucleicNet）。视频字幕为英文自动生成，本文基于文稿整理翻译；文中数字与结论均出自视频内容，可点击时间戳回看核对。

## 本讲要解决的核心问题（SCQA）

**背景**：在蛋白质领域，"给一段序列、预测三维结构"已经被 AlphaFold 和蛋白质语言模型改写成常规操作；结构生物学家和 AI 方法都把蛋白质当成了成熟战场。

**冲突**：RNA 领域完全是另一番景象。数据上，到 2022 年 5 月，PDB 数据库里蛋白质结构约有 18.5 万个，而 RNA 结构只有约 5 千个（还包含蛋白-RNA 复合物），去掉冗余后所剩无几（[【跳转到 03:04】](https://www.youtube.com/watch?v=fdMkEk84Y4A&t=184)）；方法上，主流预测依赖约 40 年历史的动态规划做能量最小化，35 年间进步有限，而且根本无法处理假结（[【跳转到 07:19】](https://www.youtube.com/watch?v=fdMkEk84Y4A&t=439)）。

**疑问**：在这样数据稀缺、结构柔性的对象上，深度学习和语言模型还能学到什么？没有足够结构数据，模型拿什么"学折叠"？

**回答（中心思想）**：把"从序列学语言"这条路搬到 RNA 上。用 RNA Central 约 2700 万条非编码 RNA 序列做自监督预训练，得到 **RNA-FM（RNA foundation model）**——它的嵌入同时携带序列模式与进化信息；把这层嵌入接入二级结构预测（修复 E2Efold 的过拟合）和三维结构预测（RhoFold：MSA + RNA-FM 嵌入 → Rhoformer → 结构模块 → 坐标 + 置信度），就能在 CASP15 与 RNA-Puzzle 上达到最优水平，并且被证明学到的是**折叠原理**而不是死记 PDB（[【跳转到 25:07】](https://www.youtube.com/watch?v=fdMkEk84Y4A&t=1507)）。

## 一、RNA 结构预测为什么比蛋白质难

### 1.1 结构层级：和蛋白质同构，但每一步都更难

[【跳转到 02:14】](https://www.youtube.com/watch?v=fdMkEk84Y4A&t=134)

开场先把 RNA 的结构层级和蛋白质对齐：一级序列 → 碱基配对形成二级结构 → 进一步折叠成三级结构 → 三级结构与其他分子接触、行使功能。这条链路蛋白质和 RNA 是同构的，但 RNA 相对蛋白质更柔性，结构数据也更稀缺——这正是后面所有方法设计的出发点。

![RNA 与蛋白质同构的结构层级：一级序列、二级结构、三级结构与功能](assets/Dr.%20Yu%20Li%20-%20RNA%20structure%20prediction%20with%20deep%20learning/00134.webp)

### 1.2 数据瓶颈：18.5 万对 5 千

[【跳转到 03:04】](https://www.youtube.com/watch?v=fdMkEk84Y4A&t=184)

主讲人给出一组决定性的数字：截至 2022 年 5 月，PDB 中蛋白质结构约 185k，RNA 结构仅约 5k（含蛋白-RNA 复合物），去冗余后"所剩有限"。更麻烦的是，大量非编码 RNA 连功能注释都没有。

![RNA 与蛋白质的结构数据量对比：PDB 中蛋白约 18.5 万、RNA 约 5 千](assets/Dr.%20Yu%20Li%20-%20RNA%20structure%20prediction%20with%20deep%20learning/00184.webp)

但硬币的另一面是机会：RNA 重要且丰富——**如果可以开发靶向 RNA 的药物，可靶点空间可能比蛋白质多 100 倍**，因为很多 RNA 根本不会被翻译成蛋白。而最大的序列库 RNA Central 已有约 2700 万条非编码 RNA 序列（[【跳转到 03:54】](https://www.youtube.com/watch?v=fdMkEk84Y4A&t=234)）。结构数据稀缺、序列数据海量——这个反差正是语言模型的用武之地。

### 1.3 经典方法的三宗罪

[【跳转到 06:29】](https://www.youtube.com/watch?v=fdMkEk84Y4A&t=389)

二级结构预测的传统做法：给每对碱基一个能量项，优化所有碱基对的能量总和，用动态规划求解。这套框架从约 40 年前沿用至今，连几年前的明星方法 LinearFold 也仍是动态规划。问题有三：**慢**；**35 年来性能提升不显著**；**无法处理假结**（pseudoknot，即交叉配对，动态规划的递归结构表达不了）。

## 二、RNA-FM：用 2700 万条序列学"RNA 语文"

### 2.1 预训练：遮住一段，猜一段

[【跳转到 04:44】](https://www.youtube.com/watch?v=fdMkEk84Y4A&t=284)

RNA-FM 的预训练方式与自然语言模型一致：把 RNA Central 的全部非编码 RNA 序列喂给模型，**遮住序列的一段，用左侧序列预测被遮的部分**（masked language modeling），全程自监督、不需要任何结构标注。训练完成后，模型可以为任意输入序列输出表示（representation），供下游结构与功能预测任务取用。

![RNA-FM 预训练：在海量非编码 RNA 序列上做掩码自监督学习](assets/Dr.%20Yu%20Li%20-%20RNA%20structure%20prediction%20with%20deep%20learning/00284.webp)

### 2.2 嵌入里有什么：序列模式 + 进化信息

[【跳转到 05:34】](https://www.youtube.com/watch?v=fdMkEk84Y4A&t=334)

预训练到底学到了什么？把所有序列的嵌入（embedding，即模型对每条序列的内部表示向量）用 t-SNE 投影到二维平面上，可以看到序列模式与进化信息被模型自动抓取——模型在"读完"2700 万条序列后，学到了 RNA 的"语言"，其中既有序列模式，也有通常需要多序列比对（MSA）才能获得的进化信息。

## 三、先拿二级结构练手：E2Efold 与 RNA-FM 嵌入

### 3.1 问题形式化：一张 0/1 配对矩阵

[【跳转到 06:29】](https://www.youtube.com/watch?v=fdMkEk84Y4A&t=389)

二级结构预测的形式化描述：给定一级序列，预测其内部的碱基配对。它可以表示成图，也可以表示成矩阵——若第 i、j 位配对，则在 L×L 稀疏矩阵中置 1。这张 0/1 矩阵就是**接触图（contact map）**，它与二级结构一一对应（[【跳转到 08:41】](https://www.youtube.com/watch?v=fdMkEk84Y4A&t=521)）。

### 3.2 E2Efold：把预测当"翻译"

与其做能量最小化，E2Efold 把问题当成**翻译问题**：把序列"翻译"成接触图矩阵，用深度学习直接端到端实现，并把先验知识作为约束注入以限制搜索空间。在约三年前，这个思路带来了大幅提升；但随后暴露出**过拟合**——模型只会预测训练数据里出现过的 RNA 家族（[【跳转到 09:06】](https://www.youtube.com/watch?v=fdMkEk84Y4A&t=546)）。

![E2Efold：把二级结构预测当成"序列→接触图"的翻译任务](assets/Dr.%20Yu%20Li%20-%20RNA%20structure%20prediction%20with%20deep%20learning/00521.webp)

### 3.3 RNA-FM 嵌入修复过拟合

[【跳转到 09:31】](https://www.youtube.com/watch?v=fdMkEk84Y4A&t=571)

解法出人意料地简单：把 RNA-FM 的嵌入接进去，即使只做很简单的改造，就超越了此前所有方法（包括 2022 年初发表的最新方法），并且预测能力可以外推到训练集中**未见过的 RNA 家族**——后续实验（未发表）证实了这一点。这是"语言模型嵌入携带通用序列知识"的第一次实战验证。

## 四、RhoFold：MSA + RNA-FM → 三维坐标

### 4.1 为什么还需要 3D 专用方法

[【跳转到 12:46】](https://www.youtube.com/watch?v=fdMkEk84Y4A&t=766)

三维预测面临同样的数据稀缺，而且传统手段更笨重：物理/模拟方法需要大规模采样，耗时且算力昂贵。既有方法分三类：**模板建模**（已解析 RNA 结构太少、模板库小）、**RNA 片段组装折叠**（组合爆炸、算力昂贵）、**深度学习打分函数**（如 Rhiju Das 组的工作，但仍需要先有候选 3D 结构）（[【跳转到 12:59】](https://www.youtube.com/watch?v=fdMkEk84Y4A&t=779)）。RhoFold 的设计动机由此而来：直接做**端到端**的序列→3D 结构预测，充分利用训练数据、加快预测；用计算增广与额外数据库信息补充进化信息、缓解过拟合；强迫模型学"折叠原理"而不是背训练集；并注入专家知识作为约束（[【跳转到 13:03】](https://www.youtube.com/watch?v=fdMkEk84Y4A&t=783)）。

![RhoFold 设计动机：端到端预测、数据增广、学折叠原理而非背训练集](assets/Dr.%20Yu%20Li%20-%20RNA%20structure%20prediction%20with%20deep%20learning/00783.webp)

### 4.2 流水线：两个嵌入源 + Rhoformer + 结构模块

[【跳转到 14:17】](https://www.youtube.com/watch?v=fdMkEk84Y4A&t=857)

RhoFold 的完整流水线（方法与作者此前的 E2Efold 一脉相承，但因 RNA 与蛋白性质不同，各模块都为 RNA 重新定制）：

1. **MSA 构建**：给定的 RNA 序列先去数据库构建 RNA 多序列比对；
2. **双路嵌入**：把 MSA 与原始序列分别通过 RNA-FM，提取模式与进化信息，得到**成对嵌入**与**单序列嵌入**两路表示；
3. **Rhoformer**：两路嵌入进入 12 层的 Rhoformer 进一步提炼——这里浓缩了来自数据库比对的大量进化信息与序列模式；
4. **结构模块**：把提炼后的表示转成 RNA 内原子的三维坐标，模块设计基于 RNA 领域的专家知识；
5. **置信度输出**：除坐标外，还预测每个区域的预测置信度——同一个结构里，哪些区域可信、哪些区域预测可能不准，一目了然（[【跳转到 15:32】](https://www.youtube.com/watch?v=fdMkEk84Y4A&t=932)）。

![RhoFold 流水线：MSA 与 RNA-FM 嵌入进入 12 层 Rhoformer，再由结构模块输出坐标与置信度](assets/Dr.%20Yu%20Li%20-%20RNA%20structure%20prediction%20with%20deep%20learning/00857.webp)

模型还显式注入了多类先验：二级结构、局部坐标系与扭转角、三维空间中的碱基配对约束（[【跳转到 16:15】](https://www.youtube.com/watch?v=fdMkEk84Y4A&t=975)）。

## 五、成绩单：RNA-Puzzle、CASP15 与全 PDB 基准

评价体系相当全面：收集 PDB 中全部 RNA 结构数据做必要过滤后，从多个角度评估——常规基准、RhoFold 交叉验证、跨家族（cross-family）甚至跨类型（cross-type）验证（[【跳转到 16:22】](https://www.youtube.com/watch?v=fdMkEk84Y4A&t=982)）。顺带一提，开场主持人介绍的就是这支在 CASP RNA-Puzzles 盲测中表现亮眼的团队：他们同时提交了经典采样方法与深度学习方法两套方案，结果古典方法反而胜过自家深度学习方案和其他所有参赛组——这个"意外"也是本场报告的引子。

### 5.1 RNA-Puzzle：几乎全面最佳，一个假结案例

[【跳转到 17:12】](https://www.youtube.com/watch?v=fdMkEk84Y4A&t=1032)

在 RNA-Puzzle 靶标上，RhoFold 几乎在所有靶标上给出最佳表现。唯一表现不佳的是 Puzzle 24——检查原因后发现，这个结构里有一个**假结**：不知道二级结构信息时预测会走偏；把假结位置作为约束告诉模型，表现就相当好（[【跳转到 18:02】](https://www.youtube.com/watch?v=fdMkEk84Y4A&t=1082)）。这个案例后来在 Q&A 中被进一步引申为"先验信息值多少钱"的活教材。

![RNA-Puzzle 成绩单：RhoFold 在几乎全部靶标上领先，Puzzle 24 因假结失手](assets/Dr.%20Yu%20Li%20-%20RNA%20structure%20prediction%20with%20deep%20learning/01032.webp)

![Puzzle 24 的假结：不知道二级结构时预测不佳，给出假结约束后表现变好](assets/Dr.%20Yu%20Li%20-%20RNA%20structure%20prediction%20with%20deep%20learning/01082.webp)

### 5.2 过拟合检验：低相似度仍有性能

[【跳转到 18:27】](https://www.youtube.com/watch?v=fdMkEk84Y4A&t=1107)

"考得好是因为会，还是因为背过题？"检验方式：把靶标与训练集之间的最大序列相似度作为横轴。当相似度低至 0.5 时，相当一部分 RNA 靶标的性能依然在线——不是靠记忆数据。

### 5.3 速度：MSA 就绪后约 1 秒一个结构

[【跳转到 18:52】](https://www.youtube.com/watch?v=fdMkEk84Y4A&t=1132)

若多序列比对（MSA）已预先构建好，RhoFold 本体约 1 秒即可完成一个结构的预测。当前瓶颈在 MSA 构建（依赖 Infernal 等工具，仍然耗时），团队正在改进构建速度。

### 5.4 CASP15：天然 RNA 接近最佳，人工设计 RNA 暴露短板

[【跳转到 19:42】](https://www.youtube.com/watch?v=fdMkEk84Y4A&t=1182)

CASP15 盲测的四条天然 RNA 中，除一条表现不佳外，其余非常接近所有方法中的最佳水平。表现拉胯的是**人工设计的 RNA**：一是其设计模式人类专家也能推断，靶标偏向"人工可解"；二是这类序列偏长，而 RhoFold 处理长目标还不够强（[【跳转到 20:07】](https://www.youtube.com/watch?v=fdMkEk84Y4A&t=1207)）。

### 5.5 全 PDB 基准：长度是主要短板

[【跳转到 20:57】](https://www.youtube.com/watch?v=fdMkEk84Y4A&t=1257)

对 PDB 全部 RNA 结构做跨折叠验证：大多数 RNA 表现尚可，**序列越长表现越差**。原因不难猜：PDB 里长 RNA 结构本来就少，训练不充分。因此有理由期待：未来数据库里长链结构多了，长序列预测会跟着变好（[【跳转到 21:22】](https://www.youtube.com/watch?v=fdMkEk84Y4A&t=1282)）。

![全 PDB 跨折叠验证：短序列表现稳定，长序列因训练数据不足而下滑](assets/Dr.%20Yu%20Li%20-%20RNA%20structure%20prediction%20with%20deep%20learning/01307.webp)

低序列相似度场景下性能并未显著下降——再次确认没有严重过拟合（[【跳转到 21:47】](https://www.youtube.com/watch?v=fdMkEk84Y4A&t=1307)）。还有一个漂亮的小实验：从训练集里找出与靶标最相似的序列，把它的结构（蓝色）与 RhoFold 预测（紫色）、实验结构（粉色）三方对比——RhoFold 的预测并没有"抄"最相似序列的作业，而是真正在预测结构（[【跳转到 22:12】](https://www.youtube.com/watch?v=fdMkEk84Y4A&t=1332)）。

跨家族验证中，留出整个 RNA 家族做测试，大多数家族表现尚可、少数家族还不好；跨类型验证（更难）的性能相对跨家族明显下降，但与已有方法相比仍相当或略优（[【跳转到 23:27】](https://www.youtube.com/watch?v=fdMkEk84Y4A&t=1407)、[【跳转到 24:17】](https://www.youtube.com/watch?v=fdMkEk84Y4A&t=1457)）。

### 5.6 "ground truth 不是 ground truth"

[【跳转到 24:42】](https://www.youtube.com/watch?v=fdMkEk84Y4A&t=1482)

PPT 上有一张耐人寻味的案例：粉色是数据库里的"标准答案"，蓝线是 RhoFold 的预测。结论是 RhoFold 重构出的反而是**生物学相关的构象**，而不是 PDB 晶体中的构象伪影——RNA 是动态分子，晶体锁住的未必是溶液中的主导构象。由此可以判断：模型学到的是折叠原理，而不是死记数据库（[【跳转到 25:07】](https://www.youtube.com/watch?v=fdMkEk84Y4A&t=1507)）。

![ground truth 不是 ground truth：RhoFold 预测重构出生物学构象而非晶体伪影](assets/Dr.%20Yu%20Li%20-%20RNA%20structure%20prediction%20with%20deep%20learning/01482.webp)

### 5.7 回顾性研究：螺旋间角也能预测

[【跳转到 26:47】](https://www.youtube.com/watch?v=fdMkEk84Y4A&t=1607)

这不是预测任务，而是回顾性研究：检验 RhoFold 能否预测结构内的**螺旋间角**（inter-helical angle）——这个量对三聚体/二聚体的设计很有用。结果显示，预测与实验值（无论冷冻电镜还是其它实验手段）相当接近。

![螺旋间角预测与实验高度吻合，可服务于多聚体设计](assets/Dr.%20Yu%20Li%20-%20RNA%20structure%20prediction%20with%20deep%20learning/01607.webp)

## 六、蛋白-RNA 相互作用：NucleicNet 与 RNA-FM 嵌入

[【跳转到 27:37】](https://www.youtube.com/watch?v=fdMkEk84Y4A&t=1657)

报告的最后一部分转向功能预测：蛋白-RNA 相互作用。实验上测定它有两类手段：解析 RNA-蛋白复合物的结构快照，或用体外实验测结合偏好（如 RNAcompete、SELEX）。已有计算方法中，基于序列的做结合偏好预测或"能否结合"的二分类；而想用结构数据的方法，则要面对多个结合口袋、取向与旋转都复杂的难题。

作者的思路是：扫描**整个蛋白表面**并提取旋转环境特征，预测整个表面的结合"景观"——这就是 **NucleicNet**：在蛋白表面任意位置预测结合偏好。它发表早于 RhoFold，当时可用的数据还很有限；现在团队正计划把 RhoFold 与 RNA 领域的新进展接进来做扩展（[【跳转到 28:57】](https://www.youtube.com/watch?v=fdMkEk84Y4A&t=1737)）。

![NucleicNet：扫描整个蛋白表面预测 RNA 结合景观](assets/Dr.%20Yu%20Li%20-%20RNA%20structure%20prediction%20with%20deep%20learning/01737.webp)

这里再次出现了 RNA-FM 嵌入的身影：交叉验证与体外实验显示，**仅用 RNA-FM 的嵌入就能达到与使用真实二级结构 profile 相当的性能**——语言模型嵌入又一次顶替了昂贵的外部信息（[【跳转到 29:41】](https://www.youtube.com/watch?v=fdMkEk84Y4A&t=1781)）。全部软件、代码教程与服务器均已公开（[【跳转到 30:06】](https://www.youtube.com/watch?v=fdMkEk84Y4A&t=1806)）。

![软件、代码教程与服务器一览：全部公开可取用](assets/Dr.%20Yu%20Li%20-%20RNA%20structure%20prediction%20with%20deep%20learning/01806.webp)

## 七、Q&A 精华

[【跳转到 30:56】](https://www.youtube.com/watch?v=fdMkEk84Y4A&t=1856)

问答环节信息密度很高，按主题整理：

1. **PDB 伪影从哪来**：一是**浓度依赖**——RNA 结构随浓度变化，模型没有把这个条件纳入预测；二是 PDB 沉积的常是**片段**而非完整分子（核糖开关往往只是超长 RNA 的 5' 域）；三是**末端化学**被忽略——细菌 5' 端是三磷酸而非单磷酸，3' 端还可能继续延伸。预测 RNA 时应把"末端之外还有没有东西"考虑进来（例如病毒 RNA 的 3' UTR）（[【跳转到 31:26】](https://www.youtube.com/watch?v=fdMkEk84Y4A&t=1886)）。
2. **长度上限与廉价先验**：高质量预测的上限约 125-130 nt，更大的 RNA 结构域本身就不常见。除了 X 射线与冷冻电镜，**化学探测**（单残基信号，便宜易得）和**交联**实验都可以辅助；把程序或实验确定的二级结构作为约束输入，能显著提升性能——Puzzle 24 加入假结约束后表现立刻改善（[【跳转到 33:31】](https://www.youtube.com/watch?v=fdMkEk84Y4A&t=2011)）。
3. **人工设计 RNA 为何难**：模式可被人类专家推断（数据偏向人工可解），且序列偏长（[【跳转到 35:50】](https://www.youtube.com/watch?v=fdMkEk84Y4A&t=2150)）。
4. **不用 MSA 行不行**：MSA 目前靠 Infernal 等工具构建；团队已尝试"语言模型替代 MSA"的单序列路线（类似 OmegaFold 的思路），稿件撰写中：性能与 OmegaFold 相当，从序列到结构约 10 秒，略逊于 MSA 版本，全 PDB 基准约 9 Å（[【跳转到 37:19】](https://www.youtube.com/watch?v=fdMkEk84Y4A&t=2239)）。
5. **冷冻电镜结构该进训练集**：人类与大肠杆菌核糖体冗余很低；把高质量冷冻电镜结构加进去，数据量能翻 3-4 倍，是"game changer"。本工作的数据截至 2022 年 5 月，这些结构当时尚未释出；而且早期冷冻电镜结构好的部分分辨率甚至优于 2 Å——能看清五元环中的孔洞（[【跳转到 38:59】](https://www.youtube.com/watch?v=fdMkEk84Y4A&t=2339)）。
6. **蛋白-RNA 复合物**：现有模型/方法都还不足以预测复合物，问题规模进一步增大；目前能单独预测蛋白或 RNA 结构，复合物还不行（[【跳转到 41:04】](https://www.youtube.com/watch?v=fdMkEk84Y4A&t=2464)）。
7. **多构象生成**：目前每次只生成一个结构；借助 recycling 等机制可以定制生成多构象（审稿人也提过这个问题），RhoFold 暂不生成多构象（[【跳转到 41:54】](https://www.youtube.com/watch?v=fdMkEk84Y4A&t=2514)）。
8. **晶体接触怎么办**：有评论打趣说"AlphaFold 学会的是晶体里的蛋白"；对蛋白这尚可接受，对 RNA 则常常不成立——晶体稳定的构象未必是溶液中的主导构象。理想方案是把晶体接触信息注入训练，但当前 PDB 没有这类元数据，需要数据库层面的重构才能实现（[【跳转到 43:09】](https://www.youtube.com/watch?v=fdMkEk84Y4A&t=2589)）。

## 小结

- RNA 结构预测的两大瓶颈：**数据**（PDB 中 RNA 结构约 5 千 vs 蛋白 18.5 万）与**经典方法的表达力**（动态规划慢、35 年进步有限、无法处理假结）。
- **RNA-FM** 用约 2700 万条非编码 RNA 序列自监督预训练，嵌入同时携带序列模式与进化信息，且即插即用：修复 E2Efold 的过拟合、在蛋白-RNA 结合预测中顶替真实二级结构 profile。
- **RhoFold** 流水线：MSA + RNA-FM 双路嵌入 → 12 层 Rhoformer → 为 RNA 定制的结构模块 → 原子坐标 + 逐区域置信度；MSA 就绪后约 1 秒出一个结构，并显式注入二级结构、局部坐标系/扭转角与碱基配对约束。
- 成绩单：RNA-Puzzle 几乎全面最佳（假结案例点出先验的价值）、CASP15 天然 RNA 接近最佳、跨家族/跨类型与低相似度检验均无明显过拟合。
- 模型学到的是**折叠原理**而非背 PDB：能重构生物学构象而非晶体伪影、能预测螺旋间角、不会照抄训练集中最相似的序列。
- 局限与方向：长序列（约 125 nt 以上）、人工设计 RNA、蛋白-RNA 复合物、MSA 构建速度，以及 PDB 数据质量本身（浓度、片段化、末端化学、晶体接触）。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| RNA-FM | 用约 2700 万条非编码 RNA 序列自监督预训练的 RNA 语言模型，输出携带序列模式与进化信息的嵌入 |
| 嵌入（embedding） | 模型对输入序列的内部向量表示，可直接喂给下游预测任务 |
| 接触图（contact map） | L×L 的 0/1 矩阵，1 表示第 i、j 位配对/靠近，与二级结构一一对应 |
| 假结（pseudoknot） | 交叉的碱基配对模式，经典动态规划无法表达 |
| MSA（多序列比对） | 同源序列的比对结果，携带进化信息；RhoFold 的输入之一 |
| Rhoformer | RhoFold 中 12 层的注意力模块，提炼成对/单序列两路嵌入 |
| 置信度 | RhoFold 对逐区域预测可靠性的自评输出 |
| RNA-Puzzle / CASP | RNA 结构预测的盲测竞赛，用于检验方法的真实水平 |
| NucleicNet | 在蛋白表面任意位置预测 RNA 结合偏好的框架 |
| RNAcompete / SELEX | 体外测定蛋白-RNA 结合偏好的实验方法 |
| t-SNE | 把高维嵌入投影到二维可视化的方法 |
| 扭转角（torsion angle） | 描述骨架局部几何的角度量，RhoFold 的显式约束之一 |
