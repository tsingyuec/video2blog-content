# 骨架修饰与语言模型并跑：用两条互补路线把 7 分命中分子改到 9 分

> 视频来源：[Molecular Generation： Designing better molecules with scaffold decoration and generative AI](https://www.youtube.com/watch?v=CXWFlZ408xs)（Digital Screeny「AI for Drug Discovery」系列第 8 讲，约 50 分钟实操课）。本博客基于视频字幕与画面整理，数据与结论均以讲者演示为准。

## 本讲要解决的核心问题（SCQA）

**背景**：这是系列课程的第 8 讲。前 7 讲已经走完一条完整流水线：虚拟筛出 20 个 EGFR 命中化合物，用 5 个 ADMET 预测模型给它们打分排序，得到 3 个 **7/10 分**的短名单候选。课程为"自动晋级"设定的分数线是 **8 分**——没有人达标。

**冲突**：逐个看这 3 个分子的短板（对应 7/10 的扣分项）：排名最前的 **797** 拥有全组最强的 BBB 排斥（入脑概率仅 0.063，对肺癌 EGFR 抑制剂是好事），但 ClinTox 毒性风险中等（0.43）；**582** 毒性最低（0.17），溶解度却只是临界水平。也就是说：**每个分子都各有一处 ADMET 短板**。下一步就是湿实验，而实验又贵又慢——直接把"带伤"的分子送去合成并不划算。

**疑问**：能不能在计算机里设计新分子——既修掉这些 ADMET 短板，又保住 EGFR 结合能力（potency）？

**回答（中心思想）**：本讲用**两条互补路线**回答这个问题。路线 A 是药化学家式的 **scaffold decoration（骨架装饰）**：保住驱动靶点结合的分子骨架，系统性替换外围基团，每一步都有明确的化学理由，产出 8 个**可解释**的类似物；路线 B 是生成式的 **SELFIES GPT**：让语言模型从 1400 多个真实 EGFR 抑制剂中自学化学语法，靠 SELFIES 表征保证 100% 化学有效率，一次生成 367 个独特而新颖的分子。两条路线的产物用同一把 ADMET 尺子重打分：路线 A 的 8 个分子**全部超过母体化合物**（最高 8/10），路线 B 最高冲到 **9/10**。真实药物发现项目里两条路线并行——这正是本讲最重要的方法论结论。

![讲者逐一检查三个 7 分命中分子的 ADMET 短板：797 的 BBB 排斥最强但 ClinTox 中等，582 毒性最低但溶解度临界](assets/Molecular%20Generation： Designing%20better%20molecules%20with%20scaffold%20decoration%20and%20generative%20AI/00160.webp)

## 一、上下文：三个 7 分命中，为何还差一口气

[【跳转到 01:20】](https://www.youtube.com/watch?v=CXWFlZ408xs&t=80)

先定位坐标：第 1–4 讲打基础（靶点识别、分子指纹、QSAR 建模、IC50 预测）；第 5–7 讲是筛选阶段（虚拟筛选得到 20 个命中 → cell painting 成像从形态学确认 → ADMET 预测排序）。现在进入**先导优化（lead optimization）阶段**：从打分排名中拿出最好的化合物，在合成任何东西之前，先在计算机里改进它。用讲者的话说，这是药物发现从"找到起点"迈向"**设计值得合成的分子**"的一步。

三个命中分子的短板（上期已算出）：

| 化合物 | 亮点 | 短板 |
| --- | --- | --- |
| ChEMBL…797 | 全组最强 BBB 排斥（入脑概率 0.063） | ClinTox 风险中等（0.43） |
| ChEMBL…582 | ClinTox 风险最低（0.17） | 溶解度临界 |
| ChEMBL…462 | （同样 7/10） | 各有一处待改进 |

所以本讲的中心问题：**能否设计新分子，修复这些弱点，同时保住 EGFR 结合能力？**

## 二、路线 A：scaffold decoration——药化学家的"精准修枝"

[【跳转到 04:45】](https://www.youtube.com/watch?v=CXWFlZ408xs&t=285)

scaffold decoration 是**药物化学（medicinal chemistry）方法**：由化学直觉与领域知识引导——**保住驱动靶点结合的分子骨架（scaffold），系统性地修改外围取代基，以修复 ADMET 性质**。这样生成的每个分子都有清晰的化学依据；训练有素的化学家看一眼结果，就能立刻明白每个化合物为什么被提出。

![本讲两条设计路线：scaffold decoration（药化学家式）与 SELFIES GPT（生成式 AI）](assets/Molecular%20Generation： Designing%20better%20molecules%20with%20scaffold%20decoration%20and%20generative%20AI/00285.webp)

### 2.1 第一步：分子分解——找到核心与"手臂"

[【跳转到 07:50】](https://www.youtube.com/watch?v=CXWFlZ408xs&t=470)

把药物分子想象成两部分：一是**刚性核心（central core）**——物理上嵌入靶蛋白、真正做结合功的部分；二是挂在核心上的**"手臂"（arms，外围基团）**——影响药物在体内行为的部分。第一步用 RDKit 的算法（Murcko scaffold）自动识别并提取母体化合物的核心，其余一切都被视为可替换的手臂。

![scaffold decoration 第一步——分子分解：刚性核心（结合靶点）与外围"手臂"（影响体内行为）](assets/Molecular%20Generation： Designing%20better%20molecules%20with%20scaffold%20decoration%20and%20generative%20AI/00470.webp)

### 2.2 第二步：选定要改的 R 基团位点

改哪条手臂？原则很明确：**不碰帮助分子结合 EGFR 的那条**——那会毁掉费力预测来的 potency；要改的是**对外周结合有贡献、但带来毒性问题**的外围手臂。改动它应当改善安全性，同时不破坏分子"抓住"靶点的方式。

### 2.3 第三步：构建替换片段库

[【跳转到 09:55】](https://www.youtube.com/watch?v=CXWFlZ408xs&t=595)

课程构建了一个精选片段库：**15 个片段，分 3 类**，直接对准上期发现的弱点——

- **增溶解**（solubility improvers）；
- **降 BBB**（BBB reducers）——让分子更难进脑，这对肺癌药是好事；
- **降毒性**（toxicity-alert reducers）——去掉毒性模型标记的结构模式。

关键点：**每个替换都有明确理由**——不是随机探索。

![第三步：构建替换片段库——15 个片段分三类（增溶解、降 BBB、降毒性）](assets/Molecular%20Generation： Designing%20better%20molecules%20with%20scaffold%20decoration%20and%20generative%20AI/00595.webp)

### 2.4 第四步：生成并过滤

用 RDKit（整个系列的"老黄牛"）把原手臂系统地换成库中每个替代片段，再用基础成药性标准过滤掉不可行的口服候选（Lipinski 类规则：分子量 <600、logP ≤6 等），并过滤条件确保：替换确实发生在目标手臂上（算法找到了 3 个可替换位点，因为母体里相似结构模式不止一处）、分子保持连通、**保留对结合很重要的含氟（CF3）基团**。

### 2.5 结果：8 个可解释的分子

[【跳转到 22:02】](https://www.youtube.com/watch?v=CXWFlZ408xs&t=1322)

15 个替代片段最终产出 **8 个独特的骨架装饰分子**——不是每个组合都能通过成药性过滤或产出合法结构，这是正常现象。数量小，但这正是 scaffold decoration 的精髓：**它追求的不是成千上万个候选，而是一小撮有理有据的提议**——每个都能说清"为什么改、想修什么问题"。不是黑箱。

这种可解释性是它相对语言模型方法的主要优势，也是大多数实验室**两条路线都做**的原因之一：实验又贵又慢，推进到下一阶段之前，你希望一切可解释。可视化时，每个分子的结构变化一目了然（苯胺苯基被替换的位置清晰可见）；化学家甚至在送 ADMET 打分之前就能对哪个最有希望形成判断。

![路线 A 产出：8 个骨架装饰分子——结构改动一目了然，可解释性强](assets/Molecular%20Generation： Designing%20better%20molecules%20with%20scaffold%20decoration%20and%20generative%20AI/01497.webp)

## 三、路线 B：SELFIES GPT——让语言模型学化学语法

### 3.1 为什么不直接用 SMILES

[【跳转到 11:49】](https://www.youtube.com/watch?v=CXWFlZ408xs&t=709)

给分子配语言模型，最直接的想法是把 **SMILES 当文本**：每个字符是一个 token（C、N、O、括号、数字……），在上面训练 GPT。但问题是 **SMILES 语法太复杂**：括号必须配平、环闭合数字必须成对、每个原子必须满足合法化合价。语言模型能学会其中一些约束，却很难同时全部守住——**字符级 SMILES 模型的化学有效率通常只有 10–30%**，意味着你生成的大多数东西都得扔掉。

![路线 B 的起点：把 SMILES 当文本，字符级训练 GPT](assets/Molecular%20Generation： Designing%20better%20molecules%20with%20scaffold%20decoration%20and%20generative%20AI/00709.webp)

### 3.2 SELFIES：把"合法性"焊进表征本身

[【跳转到 13:04】](https://www.youtube.com/watch?v=CXWFlZ408xs&t=784)

**SELFIES**（Self-Referencing Embedded Strings，自引用嵌入字符串）就是为解决这个问题发明的。它的每个 token 代表一个**完整的化学基团**（如 [C]、[N]、[F]、[Branch1]、[Ring1]），而其语法的核心性质是：**任何可能的 token 序列——无论按什么顺序排列——都解码为一个化学有效的分子**。合法性由表征本身保证，不靠模型学习语法规则，也不需要事后修补坏字符串。节目先亮出结果垫底：本讲实测 **100% 有效率**。

![SELFIES 的每个 token 代表完整化学基团（如 [C]、[N]、[F]、[Branch1]、[Ring1]）](assets/Molecular%20Generation： Designing%20better%20molecules%20with%20scaffold%20decoration%20and%20generative%20AI/00784.webp)

### 3.3 模型规格：一只"小矮人"，但正合适

[【跳转到 16:37】](https://www.youtube.com/watch?v=CXWFlZ408xs&t=997)

- 训练数据：从 ChEMBL 取 **约 1400 个 EGFR 抑制剂**，去重、校验、按分子量（150–700）过滤后剩 **1472 个**，全部编码为 SELFIES（无一损失）；词表 **45 个 SELFIES token**，序列长度 95 分位为 70 个 token。
- 模型：**6 层 GPT Transformer**，隐藏维 256，4 个注意力头，参数量 **约 480 万**——相比现代语言模型是个"小矮人"，但对 1472 个抑制剂要学的化学语法来说**正是合适的尺寸**：要的是泛化，不是记忆。
- 训练：40 个 epoch，AdamW（权重衰减 0.1）+ 余弦学习率调度 + 100 步预热；训练/验证损失同步下降、验证略高但无过拟合迹象，收敛到约 0.6。

### 3.4 生成成绩：100% 有效率 + 高新颖度

[【跳转到 31:12】](https://www.youtube.com/watch?v=CXWFlZ408xs&t=1872)

两种模式各生成 500 个：

- **无条件生成**：500 个分子**全部化学有效**（100% validity）；**98% 唯一性**（490/500）+ **95% 新颖度**（475/500 不在训练集里）——模型学到了化学，而不是在背诵训练数据。
- **条件生成**：用母体化合物（ChEMBL 797）的前 **23/46 个 SELFIES token**（正好半个分子）做前缀（priming），生成 500 个；过滤唯一性与新颖度后得到 **367 个独特而新颖的分子**，同样 100% 有效。

100% 有效率就是 SELFIES 保证的直接体现：模型生成的每个 token 序列都解码为真实分子，无需语法强制或后处理修补。

![SELFIES GPT 训练曲线：训练与验证损失同步下降，无明显过拟合](assets/Molecular%20Generation： Designing%20better%20molecules%20with%20scaffold%20decoration%20and%20generative%20AI/01872.webp)

## 四、同一把尺子：ADMET 重打分

[【跳转到 34:57】](https://www.youtube.com/watch?v=CXWFlZ408xs&t=2097)

为公平比较，课程重建了上期的 5 个 ADMET 模型（数据集：ESOL 溶解度、AstraZeneca 脂溶性、BBBP、ClinTox、Tox21），同样用 **Morgan 分子指纹 + 梯度提升（XGBoost）**，再按上期的计分公式折算成 10 分制总分。

一个小插曲很好地说明了"计算打分"的性质：母体化合物这次复打只得 **6/10**（上期是 7）。这不是数据错了——模型每次都从零重训（笔记本之间不保存），训练/测试切分存在随机波动，6 与 7 之差在这个涨落范围内。这个细节值得所有做虚拟筛选的人记住：**计算分数有噪声，趋势比单点更可靠**。

![实操全流程：ChEMBL 797 做骨架装饰 + 训练 SELFIES GPT 生成 500 条条件补全](assets/Molecular%20Generation： Designing%20better%20molecules%20with%20scaffold%20decoration%20and%20generative%20AI/00889.webp)

## 五、结果对比：A 全员改善，B 冲到 9/10

[【跳转到 37:27】](https://www.youtube.com/watch?v=CXWFlZ408xs&t=2247)

- **路线 A（骨架装饰）**：8 个分子最好的拿到 **8/10**；而且**我们尝试的每一个片段替换，都产生了比母体更好的 ADMET 剖面**——这正是本讲设计片段库的意图：对准弱点、逐一修复。
- **路线 B（SELFIES GPT）**：367 个独特新颖分子中最好的拿到 **9/10**。按 5 个 XGBoost 模型的评估，这个分子几乎没有 ADMET 顾虑——**每个 flag 都是绿色**，非常强的信号。

但讲者立刻补上了重要的"清醒剂"：这是**计算预测，不是实验测量**。模型有不确定性、训练数据有偏差，分子可能在纸面上完美，却因为模型从未见过的原因失败。9/10 或 8/10 真正的含义是：**这个化合物值得更仔细地看**——不是"保证能在实验室成功"。

![两种方法生成分子的 ADMET 得分分布：红色虚线是母体化合物的 6 分基线，其右侧全部为改善](assets/Molecular%20Generation： Designing%20better%20molecules%20with%20scaffold%20decoration%20and%20generative%20AI/02372.webp)

得分分布图给出了整体图景：分布峰值在 6 分附近，并带有一直延伸到 9–10 分的有意义长尾；红色虚线是母体化合物的基线分——**虚线右侧的每一个点都是对基线的改善**。

![预测溶解度 × 毒性散点：越靠左下 ADMET 越好；菱形为骨架装饰分子，青色点为生成分子](assets/Molecular%20Generation： Designing%20better%20molecules%20with%20scaffold%20decoration%20and%20generative%20AI/02447.webp)

溶解度—毒性散点图（x 轴：预测 log 溶解度；y 轴：预测 ClinTox 概率；**越靠左下越好**）：

- **红星**是母体化合物；
- **菱形**是 8 个骨架装饰分子——它们紧聚在母体右侧：溶解度更好，ClinTox 风险相当甚至更低，每一个都朝设计目标的方向改善；
- **青色圆点**是语言模型的产物——在性质空间里大范围铺开，这正是生成模型应有的样子：**跨越大范围性质空间的多样提议**。

## 六、性质分布的三个信号：模型学到了什么，又"偏"在哪

[【跳转到 43:00】](https://www.youtube.com/watch?v=CXWFlZ408xs&t=2580)

把生成分子与训练集的性质分布叠在一起看，有三个信号：

1. **logP 几乎完美匹配**：生成与训练分布几乎重合，都 centered 在 4 附近，形状与展布一致——模型把 EGFR 抑制剂的脂溶性剖面学得很到位。
2. **分子量整体偏低**：训练集峰值在 425–450 Da 附近，生成分子峰值在 300–350 Da——有大量重叠，但确实偏低。
3. **TPSA 是最醒目的差异**：训练集从约 30 一直铺到 150，生成分子紧聚在约 30–70。TPSA（拓扑极性表面积）低于 60 通常预示良好的口服吸收与膜通透性——对口服药是好事；**但 TPSA<60 也与 BBB 渗透相关**，而对外周 EGFR 靶点我们恰恰要避免入脑。ADMET 管线里的 BBB 模型能部分捕捉这一点，但 TPSA 上的这个缺口值得作为**局限**记录下来。

![生成分子与训练集的性质分布对比：分子量、logP、TPSA——logP 几乎重合，TPSA 差距最明显](assets/Molecular%20Generation： Designing%20better%20molecules%20with%20scaffold%20decoration%20and%20generative%20AI/02580.webp)

这些分布的实际含义：**生成分子在结构上比典型 EGFR 抑制剂更简单**。这可以是资产——更简单的分子更容易合成，选择性剖面往往更干净；但同时意味着**不能假设生成化合物会表现得像训练集里那些复杂 EGFR 抑制剂一样**。任何入围候选都需要**实验性 EGFR 结合确认**，而不是只靠计算 ADMET 打分。

## 七、方法对比与启示：两条路线，一个闭环

[【跳转到 48:00】](https://www.youtube.com/watch?v=CXWFlZ408xs&t=2880)

- **路线 A 总结**：8 个可解释的骨架装饰类似物，全部超过母体基线；每一个都能立刻看懂"改了什么结构、想修什么 ADMET 问题"——化学家引导的提议。
- **路线 B 总结**：300 多个独特、有效且新颖的分子（结果部分口径为 367 个），最好的拿到 9/10，约 100 个超过母体；全程 100% 化学有效率——因为合法性由 SELFIES 表征保证，而非语法学习。
- **核心洞察**：两条路线探索的是**不同的领地**。骨架装饰保守、有针对性、立即可懂；语言模型分子多样、结构新颖——包含片段式方法不会自然产生的环系与取代模式。
- **真实项目怎么做**：讲者与多位从业者交流后的结论是——**两条路线并行**，产物交给化学家，由化学家运用专业知识决定哪些分子优先合成。计算方法负责"铺开可能性"，人负责"收口"。

## 小结

- 三个 7/10 命中分子各有 ADMET 短板，8 分晋级线无人达标——本讲的问题：**计算机里先修好再合成**。
- **scaffold decoration 四步法**：Murcko 分解（核心 + 手臂）→ 选定 R 基团位点（不碰结合臂）→ 构建三类替换片段库（增溶解/降 BBB/降毒性）→ RDKit 系统替换 + 成药性过滤；产出 8 个可解释分子。
- **SELFIES GPT**：SMILES 字符级模型有效率仅 10–30%，SELFIES 把合法性焊进表征（任意 token 序列都解码为有效分子）；480 万参数的小模型在 1472 个 EGFR 抑制剂上训练 40 epochs，即达 100% 有效率、98% 唯一性、95% 新颖度。
- **同一把 ADMET 尺子**重打分：路线 A 全员改善（最高 8/10），路线 B 最高 9/10、约 100 个超过母体；计算分数有随机涨落（母体 7→6 的复打示例），趋势比单点可靠。
- 性质分布提醒：logP 匹配极好；生成分子更小、TPSA 更低——口服吸收友好但 BBB 渗透风险值得记录为局限；**候选仍需实验性结合确认**。
- 方法论结论：两条路线探索不同领地，**真实项目并行使用**，最终由化学家把关合成优先级。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| scaffold decoration（骨架装饰） | 保留驱动靶点结合的分子骨架，系统替换外围基团以修复 ADMET 缺陷的药物化学方法 |
| Murcko scaffold | 用 RDKit 从分子中提取的环状骨架，代表"做结合功"的刚性核心 |
| R 基团位点（R-group site） | 分子上可被替换的外围基团附着点；选择标准是"改它有收益、不碰结合臂" |
| ADMET | 吸收、分布、代谢、排泄与毒性；本讲用 5 个数据集训练的模型给每个候选打 10 分制总分 |
| BBB / BBBP | 血脑屏障；BBBP 数据集用于预测分子入脑概率，外周靶点（如肺癌 EGFR）希望"不入脑" |
| ClinTox / Tox21 / ESOL | 三个公开毒性/溶解度数据集，与 AstraZeneca 脂溶性数据集一起构成 ADMET 打分基础 |
| SMILES | 分子的线性文本表示；语法复杂（括号配平、环闭合、化合价），字符级语言模型产出有效率仅 10–30% |
| SELFIES | Self-Referencing Embedded Strings：每个 token 是完整化学基团，任意 token 序列都解码为化学有效分子 |
| validity / uniqueness / novelty | 生成质量三指标：化学有效率、去重后的唯一性、不在训练集中的新颖度 |
| priming（条件生成） | 用母体化合物的前一半 SELFIES token 作为前缀，让模型补全另一半 |
| Morgan 指纹 + XGBoost | 分子指纹 + 梯度提升树，本系列构建 ADMET 回归/分类模型的标准组合 |
| TPSA | 拓扑极性表面积；<60 利于口服吸收，但与 BBB 渗透相关——本讲记录为生成分子的局限 |
