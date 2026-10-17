# Webinar：Predicting RNA Structure Utilizing Attention from Pretrained Language Models

> 视频来源：[YouTube《Webinar: "Predicting RNA Structure Utilizing Attention from Pretrained Language Models"》](https://www.youtube.com/watch?v=0W7JpfqdZ7k)（67:00），主讲人 **Ioannis Papazoglou**（雅典生物医学研究基金会 Cournia 课题组硕士生）与 **Zoe Cournia** 教授，论文《Predicting RNA Structure Utilizing Attention from Pretrained Language Models》发表于 *Journal of Chemical Information and Modeling*（JCIM，2025）。本场 webinar 是作者对论文的完整讲解：系统检验**现成核酸语言模型（含 RNA-FM）的注意力图能否像蛋白质语言模型那样直接解码 RNA 结构**——统计公式、六类分类器、CNN 图像分类三层评测，外加与 RhoFold+ 等前沿方法的基准对比。视频字幕为英文自动生成，本文基于文稿整理翻译；文中数字与结论均出自视频内容，可点击时间戳回看核对。

## 本讲要解决的核心问题（SCQA）

**背景**：蛋白质语言模型已经证明了一件惊人的事：只用序列做自监督预训练、从未见过结构的 ESM，其部分注意力头（attention head）能无监督地对齐接触图；ESMFold 借此把预测速度做到 AlphaFold 的 6 倍而精度相近（[【跳转到 09:39】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=579)）。

**冲突**：RNA 这边还没有等价验证。RNA 语言模型比蛋白质语言模型小得多——参数、注意力层数都不到人家的一半，训练序列还少约 7 倍，而且 RNA 只有 4 个字母的"词汇表"（[【跳转到 17:03】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=1023)）；同时，可用的 RNA 三级结构只有 425 条，连训练一个模型都不够（[【跳转到 28:40】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=1720)）。

**疑问**：现成的核酸语言模型——RNA-FM、RNA-Bert、RiNALMo、DNA-Bert——它们的注意力图里，到底有没有可解码的 RNA 结构信息？

**回答（中心思想）**：基本没有（至少目前）。统计公式、六类分类器、CNN 三层评测一致表明：蛋白质语言模型确实无监督地学到了结构、且少样本即可精修（20 条蛋白训练的逻辑回归 F1≈0.8）；而 RNA 语言模型对**三级结构**几乎不含信息、对**二级结构**仅有微弱对齐且噪声大，RNA-FM 看似 100% 的对齐其实是阈值伪影。要榨出结构，得像 RhoFold+ 那样在 RNA-FM 后面接上 AlphaFold2 级别的重型架构；根本出路是训练十亿参数级的新 RNA 语言模型（[【跳转到 55:06】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=3306)）。

## 一、15 分钟速成：语言模型为什么可能"懂"结构

### 1.1 Transformer 与 BERT：只有编码器的表示学习

[【跳转到 12:28】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=748)

Ioannis 先补齐背景：语言模型基于 2017 年提出的 Transformer 架构（编码器+解码器两部分）；2018 年的 BERT 只保留编码器——输入序列，输出"机器可读、人不可读"的表示。生物序列模型普遍采用后者。

### 1.2 Q/K/V：注意力图就是一张"成对关系热图"

[【跳转到 14:08】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=848)

多头注意力（multi-head attention）在多层中并行重复。输入序列经三组线性投影生成 query、key、value 三个张量；query 与 key 做点积、过 softmax 得到概率，再与 value 相乘得到最终嵌入。关键洞察：**query×key 的点积矩阵本身就是一个"序列对自身关系的成对表示"**——模型据此学习每个核苷酸/氨基酸与序列中其它位置的相关性。

![Q/K/V 注意力机制：query 与 key 的点积构成序列的成对表示热图](assets/Webinar：Predicting%20RNA%20Structure%20Utilizing%20Attention%20from%20Pretrained%20Language%20Models/00848.webp)

### 1.3 注意力头是"功能探头"：ESM 的结构头现象

[【跳转到 15:28】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=928)

可以把一套注意力机制总结为一组"注意力头"。研究者发现，在生物模型中**每个头会专门解码语言的某一属性**。在蛋白质语言模型中，部分头与接触图（contact map）高度相似——而这些模型只训练过序列、从未见过结构，却通过"读懂蛋白质语言"解码出了结构。这直接引出本讲的问题：核酸语言模型能否同样无监督解码 RNA 结构？

![蛋白质语言模型中部分注意力头与接触图高度相似——只学序列也能"看见"结构](assets/Webinar：Predicting%20RNA%20Structure%20Utilizing%20Attention%20from%20Pretrained%20Language%20Models/00961.webp)

## 二、研究问题与现有工具

### 2.1 中心法则与 RNA 的结构层级

[【跳转到 03:15】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=195)

Zoe 先用中心法则铺垫：遗传信息从 DNA 经转录到 RNA、再翻译成蛋白。RNA 因此分两类——**编码的 mRNA**（传递遗传信息，多为线性分子）与**非编码 RNA**（调控基因表达、催化蛋白合成，具有三维结构）。本讲的对象正是后者：结构化的非编码 RNA。

![中心法则：DNA 复制、转录与翻译，RNA 居中承接](assets/Webinar：Predicting%20RNA%20Structure%20Utilizing%20Attention%20from%20Pretrained%20Language%20Models/00195.webp)

[【跳转到 04:35】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=275)

RNA 的结构分三级：**一级**是 C/U/A/G 四种核苷酸排成的序列；**二级**是邻近碱基间的氢键配对（A-U、G-C，以及 RNA 特有的 G-U 摆动配对），可用 **dot-bracket** 记号表示；**三级**是一级序列中看似相距很远、在空间中却凑在一起相互作用的碱基对（[【跳转到 05:44】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=344)）。

![RNA 三级结构：远距离碱基在空间中靠近，可用接触图或原子坐标表示](assets/Webinar：Predicting%20RNA%20Structure%20Utilizing%20Attention%20from%20Pretrained%20Language%20Models/00344.webp)

这些空间相互作用可以画成**接触图**——一张 L×L 的 0/1 矩阵，1 表示对应两残基在空间中直接相互作用。它是对三维结构"最经济"的简化表示（[【跳转到 34:35】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=2075)）。贯穿全场的核心假设是：**折叠指南编码在序列里**——RNA 有三维结构，而三维结构决定了分子的功能（[【跳转到 06:09】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=369)）。

### 2.2 现有工具盘点：三级与二级两大家族

[【跳转到 06:54】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=414)

RNA 结构预测的现有工具分两摊。**三级结构**：Rosetta RNA、RhoFold、AlphaFold 3、DeepFoldRNA、FarFar2——多为 AI 方法，有的用 MSA 有的不用；**二级结构**：SPOT-RNA2、RNAfold、MXfold2、RNA-MSM。开场抛出的判断是：仅凭 RNA 序列，目前这些工具很难预测出未知结构（[【跳转到 01:55】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=115)）。

![RNA 结构预测现状：三级与二级两类工具盘点](assets/Webinar：Predicting%20RNA%20Structure%20Utilizing%20Attention%20from%20Pretrained%20Language%20Models/00414.webp)

### 2.3 蛋白质侧的成功：从 AlphaFold 到 ESMFold

[【跳转到 09:39】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=579)

蛋白质这边给出了模板：蛋白质序列的 20 种氨基酸好比 20 个"单词"，可以当作一门语言。AlphaFold 依赖 MSA（多序列比对）获取进化信息；Meta AI 则用在海量序列上预训练的蛋白质语言模型 **ESM2**——它从进化中学到包括结构信息在内的生物分子性质，再经 **ESMFold** 完成三维预测。结果：**ESMFold 比 AlphaFold 快 6 倍**（无需做 MSA），精度却相近（[【跳转到 10:54】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=654)）。

于是问题自然浮出水面：文献里已有的**核酸语言模型**，能否同样用来预测 RNA 的三维结构？（[【跳转到 11:44】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=704)）

![从蛋白质语言模型到核酸语言模型：本讲要回答的问题](assets/Webinar：Predicting%20RNA%20Structure%20Utilizing%20Attention%20from%20Pretrained%20Language%20Models/00704.webp)

## 三、评测设计：4 个模型 × 两类靶标 × 6 种分类器

### 3.1 候选模型与排除名单

[【跳转到 17:03】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=1023)

作者盘点了当时全部 6 个核酸语言模型，发现其中 5 个有硬伤：参数量远小于蛋白质语言模型、注意力层数与头数少、训练序列也少得多。最终进入评测的有 4 个：**RNA-Bert、RNA-FM、RiNALMo**（三者只吃单序列）加 **DNA-Bert**（DNA 语言模型，因核酸语言相通而一并测试）。两个落选者：**RNA-MSM** 输入的是 MSA 而非单序列——用它就丢掉了"免 MSA"的速度优势；**UniRNA** 体量很大但代码从未发布、权重拿不到（[【跳转到 20:23】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=1223)）。

![核酸语言模型盘点：参数量、注意力深度与蛋白质语言模型的差距一目了然](assets/Webinar：Predicting%20RNA%20Structure%20Utilizing%20Attention%20from%20Pretrained%20Language%20Models/01023.webp)

顺带一提，RNA-MSM 的作者自己验证过：这个以 MSA 为输入的模型确实学到了二级结构，把它跑一条序列，能找到与目标接触图相似的注意力头（[【跳转到 21:18】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=1278)）。这为"注意力里有结构"的假设提供了先例，但也让"单序列模型是否同样如此"成为悬念。

### 3.2 统计公式：注意力里有多少结构

[【跳转到 22:08】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=1328)

第一层评测借用了 2021 年一篇预印本提出的公式：对每个碱基对 (i, j)，取注意力图中**超过阈值 theta** 的注意力之和，除以模型全部注意力头数——得到"该注意力指向结构的比例"。theta 通常取 0.3：小的注意力权重是噪声，直接置零（[【跳转到 25:41】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=1541)）。在数据集层面汇总，就得到"该模型的注意力有多大概率在表示结构"这个数。Q&A 中有人把 theta 误当成角度，主讲人澄清：**theta 是阈值，不是角度**——本层评测完全在二维接触图层面，不涉及三维角度（[【跳转到 24:01】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=1441)）。

![注意力-接触图对齐公式：超过阈值 theta 的注意力之和占总注意力的比例](assets/Webinar：Predicting%20RNA%20Structure%20Utilizing%20Attention%20from%20Pretrained%20Language%20Models/01328.webp)

公式只是"对齐度"，还不够深入——于是有第二层：**把每个碱基对当样本、该对的注意力权重当特征、是否配对当标签**，让分类器去注意力权重里挖模式（[【跳转到 26:53】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=1613)）。分类器阵容：逻辑回归（Meta 当年的选择）、决策树、随机森林、XGBoost（支持 GPU 并行），以及两个神经网络——经典 MLP 与 CNN（[【跳转到 37:09】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=2229)）。

### 3.3 数据集：425 条三级结构与 3 万条二级结构

[【跳转到 27:25】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=1645)

三级结构数据从 PDB 与 Nucleic Acid Knowledge Base 全量整理：多链保留单链模型、NMR 只取第一模型、删除无效结构；语言模型只认 4 种标准碱基，修饰/异常碱基的序列剔除；有缺口（缺失残基）的结构会破坏接触图维度，同样剔除；最后用 CD-HIT 以 80% 序列相似度聚类、每组留一个代表——只按序列聚类不按结构，因为语言模型只见序列（[【跳转到 28:15】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=1695)）。结果：**425 条三级结构**——离"够训练一个模型"还差得远，但足够做探针。

![三级结构数据集构建：PDB+NAB 全量清洗、修饰碱基剔除、CD-HIT 去冗余](assets/Webinar：Predicting%20RNA%20Structure%20Utilizing%20Attention%20from%20Pretrained%20Language%20Models/01645.webp)

二级结构这边宽裕得多：RNASTRAND v2.0、bpRNA 等开源数据集约 15 万条（计算预测为主、部分实验验证，不如 PDB 可靠），清洗+聚类后剩 3 万条（[【跳转到 29:35】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=1750)）。目标接触图两种做法：3D 版由原子距离阈值二值化；2D 版由 dot-bracket 直接转 0/1 矩阵（[【跳转到 30:17】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=1817)）。

### 3.4 预处理三件事：去对角线、3-mer 转换、欠采样

[【跳转到 31:12】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=1872)

按 Meta 的建议先做两个变换。其一，**删对角线**：对角线是每个残基的直接邻居（前 4 个），反映的是一级结构——语言模型本来就吃着序列，留着它只会喂进噪声。其二，**DNA-Bert 的 3-mer 适配**：DNA-Bert 把序列按 3 个碱基一组切分（3-mer 分词），与逐碱基的接触图维度不匹配；解法是用一个核窗口扫描接触图，遇到 1 就在窗口周围打印 9 个 1，把 1-mer 接触图转成 3-mer 接触图（[【跳转到 31:37】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=1897)）。

![接触图预处理：删除对角线近邻、DNA-Bert 的 3-mer 维度适配](assets/Webinar：Predicting%20RNA%20Structure%20Utilizing%20Attention%20from%20Pretrained%20Language%20Models/01872.webp)

其三，样本生成后暴露了 RNA 的本性难题：**95% 的碱基对不发生相互作用**（类 0），数据严重不平衡。解法很直接——对类 0 随机欠采样到与类 1 相同规模，最终得到数百万个样本（[【跳转到 36:19】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=2179)）。评价指标以 F1 为主，后期加入更耐不平衡的 MCC（Matthews 相关系数）（[【跳转到 37:30】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=2250)）。

## 四、对照实验：蛋白质语言模型确实"无监督学结构"

### 4.1 注意力头热图：高层最强，最高触及 90%

[【跳转到 38:20】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=2300)

方法论是否靠谱，先拿蛋白质当试金石。对 ESMFold 各版本（从最小到第二大）逐一计算注意力-结构对齐：每个版本——哪怕最小的——都出现了"暗点"，即高度对齐结构的注意力头，最高触及 **90%**：意味着该头 90% 的成对表示都在指向结构。**ProtT5** 的两个版本（分别用 4500 万与 21 亿条蛋白序列训练）同样拥有大量结构头，且都集中在**高层**——原因是结构是极其复杂的生物属性，需要多轮注意力重复才能解码（[【跳转到 39:35】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=2375)）。

![ESMFold 各版本与 ProtT5 的注意力头热图：高层的暗点即结构头](assets/Webinar：Predicting%20RNA%20Structure%20Utilizing%20Attention%20from%20Pretrained%20Language%20Models/02325.webp)

### 4.2 20 条蛋白训练的逻辑回归：F1≈0.8

[【跳转到 40:19】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=2419)

机器学习层验证更惊人：只用 **20 条蛋白**训练一个逻辑回归分类器（以注意力权重为特征、是否接触为标签），从注意力的成对表示中就能重建出与目标接触图非常接近的预测，**F1 约 0.8**；而且这个只见过 20 条蛋白的模型，在 1.5 万条蛋白上测试依然表现良好——蛋白质语言模型的注意力里，结构信息是真实存在且可被极少量样本"钓"出来的。

![仅用 20 条蛋白训练的逻辑回归即可重建高质量接触图](assets/Webinar：Predicting%20RNA%20Structure%20Utilizing%20Attention%20from%20Pretrained%20Language%20Models/02444.webp)

### 4.3 这张对角线矩阵为什么值钱：ESMFold 快 6 倍的原因

[【跳转到 41:48】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=2508)

Q&A 中有人问：接触图里那种沿对角线的规整图案能提供什么信息？回答是：这正是 AlphaFold 从 MSA 中解码的关键信息。Meta AI 的做法是**完全丢弃 MSA**（慢），把预测的接触图作为 Evoformer 里的成对表示，再送入 IPA（不变点注意力）模块预测三维坐标——这就是 ESMFold 快 6 倍的底层原因。对模型而言，这张"人眼看来平淡"的矩阵是**信息密度极高的数学表示**。

两种独立方法（统计公式与逻辑回归系数）还交叉验证了同一个结论：高层注意力头贡献了绝大部分结构信息（[【跳转到 43:26】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=2606)）。

## 五、RNA 的答案：三级几乎为零，二级微弱对齐

### 5.1 RNA-FM 的"100% 对齐"是伪影

[【跳转到 43:51】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=2631)

镜头转向 RNA。用 5 个核酸语言模型对三级结构做同样的计算，结果里最扎眼的是 **RNA-FM：出现了 100% 可能性的注意力头**——理论上这个头把接触图"完全解析"了。深挖后发现这是个**阈值伪影**：注意力机制产生了概率接近 1（0.99+）的信号，经 theta=0.3 阈值过滤背景噪声后，这些信号恰好都落在接触对上，于是凑出一个虚假的 100%（[【跳转到 44:41】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=2681)）。

![RNA-FM 的 100% 注意力对齐实为阈值伪影：接近 1 的信号过滤后恰好落在接触对上](assets/Webinar：Predicting%20RNA%20Structure%20Utilizing%20Attention%20from%20Pretrained%20Language%20Models/02631.webp)

解决方式是对 RNA/DNA 语言模型**完全去掉 theta 阈值**——因为它们的注意力里结构信息本就不足，必须保留低强度信号。但这也意味着同时扔掉了过滤噪声的手段（[【跳转到 45:06】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=2706)）。

### 5.2 三级结构：一切都是随机水平

[【跳转到 45:31】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=2731)

把最大的两个 RNA 语言模型（RNA-FM 与 RiNALMo）的注意力图打印出来：**没有任何明显的对齐**。分类器验证同样如此——用 20 条结构训练、再用全部收集的三级结构训练，结果都接近随机。结论明确：这些 RNA 语言模型的注意力里，几乎不含三级结构信息（[【跳转到 47:36】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=2856)）。为什么蛋白质行而 RNA 不行？因为 RNA 的语言更难解码，而且这些模型的架构**连蛋白质语言模型的一半都不到**（[【跳转到 46:46】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=2806)）。

### 5.3 二级结构：微弱对齐，模型越大越清晰

[【跳转到 48:51】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=2931)

二级结构是 RNA 结构的简化版，也许语言模型能找到？最小的 RNA-Bert 与 DNA-Bert 依旧无信息；**RiNALMo 的部分注意力头与二级结构有对齐**——但噪声仍然很大。分类器层面，在 2.5 万条分子上训练后依旧接近随机，偶有异常值拉高 F1，也只是个例（[【跳转到 49:16】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=2956)）。

唯一的积极信号藏在趋势里：从最小的 DNA-Bert 到最大的 RiNALMo，**模型越大，注意力图中的结构模式越清晰**——更大的模型能解码更多语言属性（[【跳转到 49:41】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=2981)）。

![二级结构上的微弱对齐：模型从 DNA-Bert 到 RiNALMo 越大，模式越清晰](assets/Webinar：Predicting%20RNA%20Structure%20Utilizing%20Attention%20from%20Pretrained%20Language%20Models/02931.webp)

少样本实验同样不乐观：把 2.5 万条训练集切成 20 条、再逐级扩大到全集分别训练，没能发现 RNA 语言模型的少样本能力（[【跳转到 50:06】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=3006)）。

### 5.4 CNN：把注意力图当图像也不行

[【跳转到 50:56】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=3056)

最后一搏换了思路：不再逐碱基对分类，而是把**整张注意力图**当作图像——填充到固定维度后过卷积+池化+全连接层，在 2.5 万条二级结构上训练。结果：CNN 依然找不到结构模式。Q&A 里 Ioannis 解释了设计动机：注意力图是成对表示，每个注意力权重当像素、不同层当通道、"图像分辨率"就是最大序列长度——注意力图与接触图都长得像图像，那就试试图像分类。直觉聪明，但这次的架构不够重；换更重的架构也许能挖出点什么（[【跳转到 63:41】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=3821)）。

## 六、RhoFold+ 的启示与基准对比

### 6.1 Nature 新论文：RNA-FM + AlphaFold2 架构 = 唯一走通的路线

[【跳转到 51:51】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=3111)

CNN 失败之际，Nature 上发表了 RhoFold+——用的正是本讲评测的同一个语言模型 RNA-FM。它的高明之处：不在语言模型后面接轻量分类器，而是**直接接上 AlphaFold2 的完整架构**，把语言模型的成对表示（注意力图）当作结构信息源去"深加工"。结果确实做出来了，但仍带着两条硬限制：只能预测**天然序列**（语言模型只在天然序列上训练，合成序列精度损失大）；**序列越长精度越差**。启示很明确：给语言模型配一个重型下游架构，也许真能榨出预测能力。

![RhoFold+：RNA-FM 之后接 AlphaFold2 架构，用成对表示做出结构](assets/Webinar：Predicting%20RNA%20Structure%20Utilizing%20Attention%20from%20Pretrained%20Language%20Models/03136.webp)

### 6.2 独立测试集基准：语言模型+分类器够不着 SOTA

[【跳转到 53:26】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=3206)

最后做一个基准：从 PDB 取 33 条与训练集无关的独立测试结构。三维侧，用 trRosetta-RNA、RhoFold、AlphaFold 3、FarFar2、DeepFoldRNA 各自预测，再把它们的 3D 预测转成接触图，与"语言模型+随机森林"的接触图对比——语言模型达不到既有方法的精度，意料之中。二级结构侧与 SPOT-RNA、RNAfold、MXfold2、RNA-MSM 对比同样如此；唯一的例外：**输入 MSA 的 RNA-MSM 的 F1 与 RiNALMo+随机森林相当**（[【跳转到 53:51】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=3231)）。压轴的参数量对照表把差距摆得明明白白——这正是作者决定"自己动手"的理由（[【跳转到 54:41】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=3281)）。

## 七、结论与展望

[【跳转到 55:36】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=3336)

把结论收拢成三句话：蛋白质语言模型**无监督**地学到了结构、且少样本可精修（20 条微调出精修接触图）；RNA 语言模型对三级结构**几乎不含信息**（除非加大架构）；对二级结构有一点进展，但远未到位。

[【跳转到 56:01】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=3361)

作者归纳了四大局限：**其一，架构小**；**其二，训练数据比蛋白质语言模型少至少 7 倍**；**其三，语言本质**——RNA 只有 4 个字母的"词汇表"，用 4 个词解码一门语言太难（蛋白质有 20 个词，人类语言有百万词）；**其四，RNA 的本性**——结构极其柔性，多数时候要靠四级结构中的其它分子来稳定。展望：需要**十亿参数级**的新 RNA 语言模型来跨越这些限制，相关工作已在进行、结果即将公布（[【跳转到 55:06】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=3306)）。

![结论页：RNA 语言模型的四大局限与十亿参数级新模型的展望](assets/Webinar：Predicting%20RNA%20Structure%20Utilizing%20Attention%20from%20Pretrained%20Language%20Models/03386.webp)

致谢与开源：算力来自 Amazon Web Services 与 GRNET；论文代码全部开放在 GitHub，主讲人与听众都呼吁"去读代码，看注意力图是怎么被操作的"（[【跳转到 65:15】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=3915)）。

Q&A 还有两问值得记录：其一，这算不算迁移学习？——语言模型只在序列上训练、从未见过结构、不受任何结构约束，在无监督状态下解码结构，这正是规避 RNA 结构数据稀缺的尝试，但当前模型受架构所限做不到（[【跳转到 61:30】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=3690)）；其二，为什么选 CNN 而不是 MLP？——因为注意力图天然是"图像"（权重当像素、层当通道），值得试图像分类的直觉，尽管成绩不佳，提问者也称赞其"相当聪明"（[【跳转到 63:16】](https://www.youtube.com/watch?v=0W7JpfqdZ7k&t=3796)）。

## 小结

- 蛋白质语言模型的注意力里**真实存在结构信息**：高层注意力头最高 90% 对齐接触图，20 条蛋白训练的逻辑回归 F1≈0.8；接触图正是 ESMFold 替代 MSA、快 6 倍的底牌。
- 核酸语言模型的答案是**否定**的：三级结构信息几乎为零（RNA-FM 的 100% 是 theta 阈值伪影），二级结构仅有微弱对齐且噪声大；唯一的积极趋势是**模型越大、模式越清晰**。
- 三层评测（统计公式 → 六类分类器 → CNN 图像分类）互相印证，方法本身先在蛋白质上验证过——这是一套可复用的"注意力探针"评测框架。
- RhoFold+ 证明：RNA-FM + AlphaFold2 级重型架构是当前唯一走通的"语言模型出结构"路线，但限于天然序列与较短长度。
- 四大局限（架构小、数据少 7 倍、4 字母词汇表、四级结构稳定化）指向同一个出路：十亿参数级新 RNA 语言模型。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| RNA-FM | 本讲重点评测的 RNA 语言模型，也是 RhoFold+ 的底座 |
| 注意力头（attention head） | 多头注意力中的并行单元；生物模型中各自解码语言的特定属性 |
| 接触图（contact map） | L×L 二值矩阵，1 表示两残基在空间中相互作用；注意力图的"结构版" |
| dot-bracket | 用 `.` `(` `)` 表示 RNA 二级结构配对关系的记法 |
| theta 阈值 | 统计公式中过滤噪声注意力权重的阈值，通常取 0.3（不是角度） |
| RNA-MSM | 以 MSA 为输入的 RNA 语言模型（因失去免 MSA 速度优势被排除出主评测） |
| RiNALMo | 本讲评测中最大的 RNA 语言模型 |
| DNA-Bert | 以 3-mer 切分的 DNA 语言模型，接触图需做 3-mer 维度适配 |
| 少样本（few-shot） | 只用极少量样本（如 20 条）微调即可获得目标能力 |
| Evoformer | AlphaFold 中处理 MSA 与成对表示的主干模块 |
| IPA（不变点注意力） | AlphaFold 中处理三维等变性的注意力模块 |
| XGBoost | 支持 GPU 并行的梯度提升树分类器 |
| MCC | Matthews 相关系数，比 F1 更耐不平衡数据的分类指标 |
| CD-HIT | 按序列相似度聚类去冗余的工具（本讲用 80% 阈值） |
