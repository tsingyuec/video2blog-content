# AlphaFold 3 强在哪、翻车在哪：扩散模块、PAE 读法与服务器限制一览

> 视频来源：[Bilibili《AlphaFold3的突破 - 钟博子韬深度解析AlphaFold3｜钰沐菡公开课》](https://www.bilibili.com/video/BV1yi421U76X/)（约 74 分钟）
> 本文基于视频演说图文稿撰写，观点与数据均可回看视频核对。

## 这支视频要解决的核心问题（SCQA）

**背景**：管线 B 验证步的另一半靠 AF3 类模型（开源复刻即 Protenix）预测抗体-抗原复合物，再用 ipTM 等置信度判定设计成立与否。谷歌 DeepMind 与 Isomorphic Labs 于 3 月 8 日发布 AlphaFold 3，主讲人钟博子韬（上海交通大学自然科学研究院，洪亮教授课题组）在钰沐菡公开课上做全景解读（[00:25](https://www.bilibili.com/video/BV1yi421U76X/?t=25)）。

**冲突**：AlphaFold 2 只认 20 种标准氨基酸，论文亲口不推荐用它做抗体-抗原复合物；配体、翻译后修饰、核酸统统做不了；而 RNA 在 PDB 里只有约 1 万条结构、小分子种类多而每种样例都少——数据并没有变多（[04:50](https://www.bilibili.com/video/BV1yi421U76X/?t=290)、[29:32](https://www.bilibili.com/video/BV1yi421U76X/?t=1772)）。

**疑问**：AF3 凭什么在数据不变多的情况下全面提升？预测结果该信到什么程度、置信度怎么读、什么时候会翻车？服务器上到底能用什么？

**回答（中心思想）**：AF3 把任务从"蛋白质结构预测"扩成"**生物分子结构预测**"——架构上 Evoformer 换成 Pairformer（对 MSA 的依赖降低），结构模块换成**全原子扩散模块**（直接对原子坐标去噪）；蛋白-小分子共折叠在 PoseBusters 上成功率 76.4%（给 6 Å 口袋可达 90%+），蛋白-抗体复合物从不到 30% 拉到 60% 以上；读结果**不能只看 pLDDT，要看 PAE**（7T82 反例：pLDDT 全蓝、界面照样上下颠倒）；幻觉靠无序区自蒸馏压制；服务器限一天 20 个任务、5000 token、只支持 14 种小分子。

![AF2 是蛋白质结构预测软件，AF3 是生物分子结构预测软件](assets/AlphaFold3的突破%20-%20钟博子韬深度解析AlphaFold3｜钰沐菡公开课/00100.webp)

## 一、先回顾：AF2 实现的是"共进化 → 结构"

AF2 的输入是 MSA（多序列比对）加模板，核心是 Evoformer（为 MSA 设计的 transformer）与 3D 等变结构模块，外加 recycling 与置信度预测（[03:10](https://www.bilibili.com/video/BV1yi421U76X/?t=190)）。但要强调：AF2 实现的是**从共进化到结构的映射**，不是从序列到结构——它需要从多序列比对里提取共进化信息再预测结构。这一点直接决定了三代的改造方向（[04:00](https://www.bilibili.com/video/BV1yi421U76X/?t=240)）。

## 二、AF2 的五个未解问题

1. **配体**：只接受 20 种常见氨基酸，小分子进不去；
2. **复合物**：AlphaFold-Multimer 一路迭代到 2.3 仍是"能做但不够准"，尤其抗体-抗原——AF2 与 Multimer 的论文都明确不推荐（[05:20](https://www.bilibili.com/video/BV1yi421U76X/?t=320)）；
3. **共价修饰**：翻译后修饰的蛋白与核酸都处理不了；
4. **核酸**：DNA、RNA 不能预测；
5. **动力学**：多次采样能拿到一些构象多样性，但并没有真正解决（[05:45](https://www.bilibili.com/video/BV1yi421U76X/?t=345)）。

![AF2 的五点限制清单；前四点 AF3 都能做了](assets/AlphaFold3的突破%20-%20钟博子韬深度解析AlphaFold3｜钰沐菡公开课/00295.webp)

前四点 AF3 全部拿下：核糖体 RNA-蛋白复合物、糖基化修饰、抗体-短肽结合、三种药物与靶标的复合物（配体 RMSD 都小于 2 Å）都有精准示例（[06:10](https://www.bilibili.com/video/BV1yi421U76X/?t=370)、[08:00](https://www.bilibili.com/video/BV1yi421U76X/?t=480)）。第五点动力学仍是 AF3 的短板，后面细说。

## 三、架构变化：Pairformer 与扩散模块

AF3 架构与 AF2 大体相似，两处关键改动：**Evoformer → Pairformer**（学 MSA 表示的部分），**结构模块 → Diffusion module**（文生图、文生视频里同款"扩散模型"概念）（[07:05](https://www.bilibili.com/video/BV1yi421U76X/?t=425)）。这两处改动的细节在第十、十一节展开。

![AF3 架构总览：Evoformer→Pairformer，结构模块→扩散模块](assets/AlphaFold3的突破%20-%20钟博子韬深度解析AlphaFold3｜钰沐菡公开课/00425.webp)

## 四、成绩单一：共折叠取代分子对接？

传统 docking 的流程是"输入蛋白结构（有的还要指定口袋）→ 把小分子放进结合位点"；AF3 走的是另一条路：**蛋白和小分子一起折叠**，讲者给它起名叫 **co-folding（共折叠）**（[08:55](https://www.bilibili.com/video/BV1yi421U76X/?t=535)）。基准是 **PoseBusters**：428 个 2021 年之后解析的、同时含小分子与蛋白的 PDB 晶体结构，成功率定义为小分子口袋内 RMSD < 2 Å——这个标准下不会找错口袋、也不会出现大构象翻转（[09:45](https://www.bilibili.com/video/BV1yi421U76X/?t=585)）。

结果：老牌物理能量法 AutoDock Vina 能到 50% 以上；RoseTTAFold All-Atom、UMol 等共折叠前辈反而不到 50%，难以超过 Vina；**AF3 以 76.4% 超过所有方法**（[11:00](https://www.bilibili.com/video/BV1yi421U76X/?t=660)、[11:25](https://www.bilibili.com/video/BV1yi421U76X/?t=685)）。而且 docking 类方法有个隐藏"优势"——通常拿 holo 结构（已结合配体、口袋暴露的蛋白）当输入，换成 apo 状态效果会打折；共折叠方法不需要这些，等于让着对方，AF3 依然领先（[11:50](https://www.bilibili.com/video/BV1yi421U76X/?t=710)）。如果再给 AF3 口袋信息，成功率能上 90%——不过 Q&A 里澄清了这个数字的来历：Uni-Mol v2 曾用"配体周围 6 Å 以内氨基酸"的小口袋设置做到 77%，AF3 团队就用同样苛刻的 6 Å 设置回应出 90%+；对比其他方法用的 22 Å（KarmaDock、DiffDock）、8 Å（Uni-Mol）、约 12 Å（Vina 的 24³ 盒子）大口袋，参考价值有限，**日常还是按 76.4% 评估**（[12:40](https://www.bilibili.com/video/BV1yi421U76X/?t=760)、[13:05](https://www.bilibili.com/video/BV1yi421U76X/?t=785)、[51:04](https://www.bilibili.com/video/BV1yi421U76X/?t=3064)）。一个不需要蛋白结构的算法超过了所有 docking 算法——这个领域的现状确实被改变了（[13:30](https://www.bilibili.com/video/BV1yi421U76X/?t=810)）。

![docking vs 共折叠：AF3 在 PoseBusters 上超过 Vina 与所有深度学习前辈](assets/AlphaFold3的突破%20-%20钟博子韬深度解析AlphaFold3｜钰沐菡公开课/00660.webp)

## 五、成绩单二：核酸、修饰，与"最难啃"的抗体复合物

**核酸**：与 Baker 实验室的 RoseTTAFold-NA 相比，AF3 在蛋白-RNA、蛋白-双链 DNA 复合物以及纯 RNA、纯 DNA 结构上全面领先（[13:45](https://www.bilibili.com/video/BV1yi421U76X/?t=825)）。唯一的例外在 CASP15：RNA 赛道 8 个 target 里，AF3 超过了 RoseTTAFold-NA，但没超过冠军 AIchemy_RNA2——后者靠人类专家知识调整预测结果（[14:35](https://www.bilibili.com/video/BV1yi421U76X/?t=875)）。**共价修饰**：共价配体、糖基化、蛋白/DNA/RNA 上的修饰，准确率都在 50% 以上（[15:25](https://www.bilibili.com/video/BV1yi421U76X/?t=925)）。

**复合物**：单体上 AF3 只比 AF2 略强——本来就近 90%，很难再涨；蛋白-蛋白复合物从 60% 多提到 70 多；**提升最猛的是蛋白-抗体复合物：从不到 30% 拉到 60% 以上**。这里的成功率标准是 DockQ > 0.23——大意是界面/表位找对了，细节还可能有错（[17:05](https://www.bilibili.com/video/BV1yi421U76X/?t=1025)、[17:30](https://www.bilibili.com/video/BV1yi421U76X/?t=1050)）。

![蛋白-抗体复合物：DockQ>0.23 成功率从 <30% 提到 60%+](assets/AlphaFold3的突破%20-%20钟博子韬深度解析AlphaFold3｜钰沐菡公开课/01025.webp)

## 六、为什么提升：MSA 依赖降低了

抗原文体难做，一个老原因是**配对 MSA 不好找**：两个蛋白各自的 MSA 好找，但谁跟谁能配对很难判断，之前的算法基本靠"同物种就配"的启发式；抗体更惨——体细胞超突变让 CDR 突变太多，共进化信号几乎为零，这也解释了为什么此前众多用 MSA 或语言模型预测抗体的方法都不尽人意（[18:20](https://www.bilibili.com/video/BV1yi421U76X/?t=1100)、[19:10](https://www.bilibili.com/video/BV1yi421U76X/?t=1150)）。数据上的旁证是 MSA 数量与精度的关系：AF2 要 30 条以上 MSA 才稳定；AF-Multimer 约 10 条；**AF3 在 10 条以下仍能保持高精度（pLDDT 70+），明显强于 AF-Multimer 2.3**——它对 MSA 的依赖确实下降了（[20:00](https://www.bilibili.com/video/BV1yi421U76X/?t=1200)、[20:25](https://www.bilibili.com/video/BV1yi421U76X/?t=1225)）。

## 七、置信度怎么读：pLDDT 之外，必须看 PAE

AF3 除了逐残基的 pLDDT，还给出链间 ipTM（越高复合物越可信）与 **PAE**——即"两个残基之间距离预测的误差"，越接近 0 说明模型越自认这段距离靠谱（[20:49](https://www.bilibili.com/video/BV1yi421U76X/?t=1249)、[21:33](https://www.bilibili.com/video/BV1yi421U76X/?t=1293)）。

关键案例是 PDB **7T82**（抗体-抗原复合物）：AF3 的 pLDDT 图大片蓝色、看起来很靠谱；但和真实结构一对照，预测完全**上下颠倒**——表位找错了（[22:23](https://www.bilibili.com/video/BV1yi421U76X/?t=1343)、[22:48](https://www.bilibili.com/video/BV1yi421U76X/?t=1368)）。翻车信号在 PAE 里：抗原内部（A-F 链间）与抗体内部（C-D 链间）的 PAE 接近 0，而抗原 A 链与抗体 C、D 链之间的 PAE 高达约 30 Å——模型自己都不信这对界面。事实正是：**链内部全对，抗体-抗原之间的相互作用全错**（[23:13](https://www.bilibili.com/video/BV1yi421U76X/?t=1393)、[24:03](https://www.bilibili.com/video/BV1yi421U76X/?t=1443)）。这正是 5.3.3 那场"结构置信度不等于结合判别力"研讨会的实例注脚：判断复合物可信度，看界面 PAE/ipTM，别只看整体 pLDDT。

![7T82 案例：pLDDT 全蓝却是错的，PAE 揭示界面不可信](assets/AlphaFold3的突破%20-%20钟博子韬深度解析AlphaFold3｜钰沐菡公开课/01343.webp)

## 八、失败模式清单

- **手性翻转**：AF3 预测小分子约有 4% 概率搞错手性；用户应核对自己输入分子的手性，删掉错误预测（[24:37](https://www.bilibili.com/video/BV1yi421U76X/?t=1477)）；
- **链重叠**：偶发多条链叠在一起（连 DNA 链也会重复）；这类通常会被置信度扣分筛掉，碰到就手动删（[25:02](https://www.bilibili.com/video/BV1yi421U76X/?t=1502)）；
- **动力学**：E3 泛素连接酶 apo 时 open（两结构域分开）、结合底物时 closed；**AF3 在两种情况下都预测成 closed**，抓不到 open 状态（[25:51](https://www.bilibili.com/video/BV1yi421U76X/?t=1551)）。二代解决不了的问题三代也没解决，这点要在管线里当成已知局限。

## 九、抗体的特殊技巧：多跑 1000 次

抗体任务上有个实操技巧：**多跑几次、按置信度挑最好的**。以 DockQ > 0.23 计，跑一次成功率不到 40%，跑 1000 次挑最优能到约 60%；若要求 DockQ > 0.8（相互作用也全对），单次约 10%，1000 次可到近 30%（[27:22](https://www.bilibili.com/video/BV1yi421U76X/?t=1642)）。但注意：**只有含抗体的任务受益明显**，普通蛋白-蛋白、蛋白-小分子、蛋白-DNA 复合物多跑几次收益甚微（[27:47](https://www.bilibili.com/video/BV1yi421U76X/?t=1667)）。

![多跑采样：抗体任务 40%→60%（DockQ>0.23）、10%→30%（DockQ>0.8）](assets/AlphaFold3的突破%20-%20钟博子韬深度解析AlphaFold3｜钰沐菡公开课/01642.webp)

## 十、它怎么做到的：数据、token 与扩散模块

**数据效率**：AF3 官方说法是"提升了数据利用效率"——PDB 总共 20 多万条结构，其中 RNA 只有约 1 万条或更少，小分子种类多而每种样例少。AF3 的态度是：数据集不是上限，靠更好的架构、训练策略与半监督/自监督式数据增强，一样能突破（[28:42](https://www.bilibili.com/video/BV1yi421U76X/?t=1722)、[29:57](https://www.bilibili.com/video/BV1yi421U76X/?t=1797)）。

![数据不是瓶颈：架构与训练策略也能榨出更多](assets/AlphaFold3的突破%20-%20钟博子韬深度解析AlphaFold3｜钰沐菡公开课/01797.webp)

**训练数据**（细节多在补充材料）：按"训练集 → 数据集 → 局部裁剪"三级采样；以 PDB 为主，混入 AF2 预测的单体结构、无序蛋白训练集（治幻觉），还用训练了一半的 AF3 预测无结构 RNA、用快训完的 AF3 预测蛋白-DNA 复合物——这就是二代玩过的**自蒸馏（self-distillation）**，三代把它扩展到了 RNA 与 DNA（小分子没有增强，仍来自 PDB）（[31:28](https://www.bilibili.com/video/BV1yi421U76X/?t=1888)、[32:43](https://www.bilibili.com/video/BV1yi421U76X/?t=1963)）。

**token 定义**：氨基酸与核苷酸按残基成 token（蛋白以 Cα 为中心、核酸以 C1′ 为中心）；翻译后修饰、小分子、金属离子则按**单原子**成 token（[33:54](https://www.bilibili.com/video/BV1yi421U76X/?t=2034)）。

**Pairformer**：原 Evoformer 拆成 MSA 模块（48 层减到 4 层）与 Pairformer（48 层）；三角更新、三角自注意力这些核心操作原样保留——变化没有想象中大（[35:14](https://www.bilibili.com/video/BV1yi421U76X/?t=2114)）。

![Pairformer vs Evoformer：三角更新与三角注意力都还在](assets/AlphaFold3的突破%20-%20钟博子韬深度解析AlphaFold3｜钰沐菡公开课/02114.webp)

**扩散模块**：AF2 的消融实验早已显示，删掉几何约束影响不大；AF3 干脆认为 SE(3) 等变这个"符合人类几何直观"的性质没有必要，直接对**全原子坐标做去噪**——严格说它对旋转不再不变（会有小扰动，靠一些方式抵消）（[36:14](https://www.bilibili.com/video/BV1yi421U76X/?t=2174)、[37:04](https://www.bilibili.com/video/BV1yi421U76X/?t=2224)）。扩散模块本质是**条件生成模型**：类比文生图，条件是 MSA 与 token 相互作用信息，生成的是结构；内部按"原子 → token（一个氨基酸/核苷酸那群原子）→ 原子"三轮更新、多轮迭代，从带噪坐标去噪成最终结构（[37:54](https://www.bilibili.com/video/BV1yi421U76X/?t=2274)、[38:44](https://www.bilibili.com/video/BV1yi421U76X/?t=2324)）。有趣的是，带噪坐标的输入只过一个线性层——明显不符合等变性，照样好用（[39:34](https://www.bilibili.com/video/BV1yi421U76X/?t=2374)）。

![条件扩散：MSA/相互作用为条件，全原子坐标去噪生成结构](assets/AlphaFold3的突破%20-%20钟博子韬深度解析AlphaFold3｜钰沐菡公开课/02274.webp)

## 十一、生成模型的代价：幻觉与自蒸馏

扩散生成模型和 ChatGPT 一样有**幻觉**问题：一个只有部分区段解析出结构的蛋白，AF-Multimer 2.3 给未解析区域一团无规卷曲，AF3 却把它们整齐地折成α螺旋——pLDDT 虽低，但生物学家看着就难受（[40:04](https://www.bilibili.com/video/BV1yi421U76X/?t=2404)）。对策就是前面说的**无序蛋白训练集 + 自蒸馏**：不调整时 AF3 会把大段无序区全折起来，调整后才收敛到合理结果（[40:54](https://www.bilibili.com/video/BV1yi421U76X/?t=2454)）。副产品是 AF3 可以用 pLDDT 或溶剂可及面积（SASA）**找无序区**——pLDDT 两条路都能用；SASA 只有做了蒸馏才可靠，没蒸馏的 SASA 曲线是图上唯一离开主流的离群线（[41:10](https://www.bilibili.com/video/BV1yi421U76X/?t=2470)）。

![幻觉示例：AF3 把未解析区域折成整齐螺旋；自蒸馏治幻觉](assets/AlphaFold3的突破%20-%20钟博子韬深度解析AlphaFold3｜钰沐菡公开课/02429.webp)

## 十二、任务强弱地图与服务器限制

任务画像：蛋白、DNA、RNA、配体"内部"结构都还可以（配体内部最简单）；单体 RNA 偏弱；复合物里蛋白-小分子精度最高（正是共折叠对接能力强），蛋白-蛋白次之，**最差的是蛋白-RNA 复合物**（[43:15](https://www.bilibili.com/video/BV1yi421U76X/?t=2595)、[43:40](https://www.bilibili.com/video/BV1yi421U76X/?t=2620)）。

目前只能用谷歌服务器（承诺约半年内开源但还没开）：谷歌账号即可，操作简单，但限制不少（[44:13](https://www.bilibili.com/video/BV1yi421U76X/?t=2653)）：

- **一天 20 个任务**（此前 10 个，最近才上调）；
- **单任务最多 5000 token**（一个氨基酸/核苷酸/小分子原子都算一个 token）；
- 支持蛋白、DNA、RNA、小分子、离子、翻译后修饰与糖基化：修饰蛋白 23 种、DNA 9 种、RNA 15 种；糖基化 6 种（常见类型与支链糖都覆盖）；金属离子 10 种；
- **小分子只支持 14 种**——ATP/ADP/AMP/GTP/GDP、FAD/NAD、heme、PLM/OLA 等常见生物学分子；想拿它做药物对接"想都不用想"（[44:38](https://www.bilibili.com/video/BV1yi421U76X/?t=2678)、[45:53](https://www.bilibili.com/video/BV1yi421U76X/?t=2753)）。讲者认为这多半是 Isomorphic Labs 想让自家团队先用起来，等开源应该会放开（[46:18](https://www.bilibili.com/video/BV1yi421U76X/?t=2778)）。

![服务器限制：一天 20 任务、5000 token、14 种小分子](assets/AlphaFold3的突破%20-%20钟博子韬深度解析AlphaFold3｜钰沐菡公开课/02678.webp)

## 十三、社区脑洞与"物理直觉"之问

小分子限制挡不住想象力：有人塞 256 个脂肪酸 OLA，居然拼出一个像模像样的**脂质双分子层**，再把蛋白放进去还能找到跨膜区；还有人调节 OLA 与 PLM（棕榈酸）的比例来避免胶束、促成双分子层（[47:03](https://www.bilibili.com/video/BV1yi421U76X/?t=2823)）。这些"自然界不太会存在"的结构能被折出来，引出一个悬而未决的问题：**AF3 到底学没学到疏水亲水这类物理信息？学了多少？**（[47:53](https://www.bilibili.com/video/BV1yi421U76X/?t=2873)）——扩散模块学的是一个全原子的"能量函数"，它与分子动力学的关系值得开源后深挖（[63:28](https://www.bilibili.com/video/BV1yi421U76X/?t=3808)）。

![256 个 OLA 脂肪酸拼出双分子层：AF3 疑似学到了物理信息](assets/AlphaFold3的突破%20-%20钟博子韬深度解析AlphaFold3｜钰沐菡公开课/02848.webp)

另一些尝试提醒我们 RNA 仍是软肋：预测转录泡有模有样，但给它互补配对反而折出怪结构；预测结果里出现 GG、GA、AC、CA 这类违背物理的碱基配对——这是 **RNA 的幻觉**：蛋白的幻觉靠无序训练集压住了，RNA 没有对应的疗法（AF2 也从没预测过 RNA）（[48:48](https://www.bilibili.com/video/BV1yi421U76X/?t=2928)）。核糖开关找靶标有时找错，蛋白-DNA 复合物准确度约 50%——特异性要求高的任务仍要小心（[49:13](https://www.bilibili.com/video/BV1yi421U76X/?t=2953)）。

## 十四、Q&A 补充与药物研发视角

- **与 RFAA 比**：讲者的判断是各领域 AF3 都强不少，PoseBusters 上近乎碾压、成功率有时直接翻倍（[53:59](https://www.bilibili.com/video/BV1yi421U76X/?t=3239)）。
- **侧链**：AF2 侧链本就不准，AF3 可能同样；开源后值得拿酶-底物复合物试试会不会改善——但服务器只有 14 种小分子，眼下没法测（[54:24](https://www.bilibili.com/video/BV1yi421U76X/?t=3264)）。
- **与 MD 结合**：AF3 预测结果直接当 MD 输入；或用 AF3 替代 docking 再跑 MD；AF2 时代结合增强动力学的 AF2RAVE 思路也值得迁移（[55:39](https://www.bilibili.com/video/BV1yi421U76X/?t=3339)）。
- **多构象蛋白会倾向哪个态？** 给了小分子后大概率倾向 closed/结合态——模型要照顾小分子附近的局部环境；但像激酶 DFG-in/out 两种构象都能结合药物的体系，倾向哪个就说不准了。动力学预测远谈不上好，或许四代五代会解决（讲者笑言这只是畅想）（[60:53](https://www.bilibili.com/video/BV1yi421U76X/?t=3653)、[62:13](https://www.bilibili.com/video/BV1yi421U76X/?t=3733)）。
- **小分子输入格式**：模型本体可以接受手性、成键信息；但当前服务器只能给 **CCD token**（PDB 三字母代码），相当于让 AF3 自己查分子再搬进来，手性无法手动控制（[65:22](https://www.bilibili.com/video/BV1yi421U76X/?t=3922)）。
- **小分子构象从哪来？** 训练时用 RDKit 力场采样一堆候选构象当"小分子模板"喂给模型，由模型挑一个放进口袋——可能挑错；对 AI 生成的虚拟化合物，没学透的物理可能给出带张力、不成立的构象（[69:03](https://www.bilibili.com/video/BV1yi421U76X/?t=4143)）。难度排序：**RNA 最难**（单链、构象灵活、配对形式复杂），DNA 有互补配对较容易，小分子居中；且小分子 RMSD 指标本身就"宽容"（[69:53](https://www.bilibili.com/video/BV1yi421U76X/?t=4193)）。

![小分子模板：RDKit 力场采样多构象，模型负责挑对的那个](assets/AlphaFold3的突破%20-%20钟博子韬深度解析AlphaFold3｜钰沐菡公开课/04143.webp)

- **会颠覆药物研发吗？** 短期不会：虚拟筛选不适合 AF3（算力扛不住超大库）；它的实际用途是"已知活性分子、不知道结合方式"这类场景——而这用现有对接软件大概率也能解决；限速步骤在后续的分子优化与 SAR，不在结构预测。相比之下，**AF3 对大分子（抗体、RNA 药物）帮助更大**——这些领域此前没有小分子对接这么成熟的工具链；而 PK/PD 等体内优化早已超出结构的管辖范围（[70:43](https://www.bilibili.com/video/BV1yi421U76X/?t=4243)、[72:23](https://www.bilibili.com/video/BV1yi421U76X/?t=4343)）。

## 小结

- **定位变了**：从蛋白质结构预测软件变成生物分子结构预测软件——蛋白、DNA、RNA、小分子、修饰一锅端，且用统一架构（残基或原子）描述（[28:42](https://www.bilibili.com/video/BV1yi421U76X/?t=1722)）。
- **两个架构关键词**：Pairformer（MSA 依赖降低，<10 条 MSA 仍高精度，这正是抗体-抗原复合物从 <30% 到 60%+ 的关键）与全原子扩散模块（放弃 SE(3) 等变，直接去噪）。
- **读数习惯**：界面可信度看 PAE/ipTM，别被漂亮的 pLDDT 骗（7T82 案例）；抗体任务多跑几次按置信度挑优。
- **已知翻车点**：手性 ~4%、链重叠、open/closed 动力学、RNA 幻觉——设计验证流程里要设检查点。
- **服务器现实**：一天 20 任务、5000 token、14 种小分子，做药筛先死心；等开源再谈定制输入。
- 对管线 B：AF3/Protenix 负责复合物层面的"回折验证"，但验证的是"界面找没找对"（DockQ/ipTM 口径），结合强度仍要交给亲和力预测与实验。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| co-folding（共折叠） | 蛋白与配体一起折叠出复合物，不需要先有蛋白结构 |
| PoseBusters | 蛋白-小分子共折叠基准：2021 年后 PDB 晶体 428 例，口袋内 RMSD<2Å 记成功 |
| DockQ / ipTM | 复合物质量与链间置信度指标；DockQ>0.23 约等于界面/表位找对 |
| PAE | 两残基间距离的预测误差；判界面真假比 pLDDT 更灵（7T82 案例） |
| Pairformer | AF3 取代 Evoformer 的模块；三角更新保留，MSA 依赖降低 |
| diffusion module | 全原子条件扩散生成模块；放弃 SE(3) 等变，直接对坐标去噪 |
| self-distillation（自蒸馏） | 用中间版模型的预测扩充训练集；AF3 用它治幻觉、扩展到 RNA/DNA |
| CCD token | PDB 三字母分子代码；当前服务器唯一的小分子输入方式 |
