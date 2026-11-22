# AlphaFold 3 Accuracy on Antibody Binding and Protein Interactions

> 视频来源：YouTube《AlphaFold 3 Accuracy on Antibody Binding and Protein Interactions》（约 34.6 分钟，5.7k+ 播放）。讲者 Bruce 的演讲《α 螺旋的九种视图》（Nine views of an alpha helix）：他所在的实验室设计过多个「真的能用」的抗 HIV 抗体，本讲用这些体系当考卷，**可视化**检验 AlphaFold 3 对抗体-蛋白相互作用的预测。对应系列条目 **6.2.1 抗原结构（Protenix）** 的另一半：姊妹篇《How to Perform Molecular Docking with AlphaFold3： Protenix》教你「怎么预测」，本篇回答「预测结果能不能信」。

## 本讲要解决的核心问题（SCQA）

**背景**：管线 B 拿到抗原结构后，下一步是预测「抗体怎么结合抗原」。AF3/Protenix 一键就能输出看起来漂漂亮亮的复合物模型，置信度还很高。

**冲突**：讲者实验室把自己的抗体-抗原体系逐个喂给 AF3，再与冷冻电镜/晶体真值对比——结果抗体**结合位置全错**（结合在「侧面」而不是「顶部」），而且 5 个预测无一幸免、置信度依然高企。官方口径里 antibody-antigen 也只有 51% 的准确率。

**疑问**：怎么判断一个 AlphaFold 预测是「真的好」还是「幻觉」？模型给出的置信度分数还能信吗？

**回答（中心思想）**：把结构**画出来**与实验真值对比，并学会读 PAE（期望位置误差）矩阵——AF3 对「单体部件」很自信、对「怎么拼到一起」极不自信（界面误差可达 30 埃）。换句话说，**AF3 似乎知道自己可能错，但照样给你一个结构**。现阶段把 AF3 的抗体-抗原预测直接送进设计流程不可靠，独立验证不可省。

## 一、先学会「看」蛋白：从原子球到样条速写

### 1.1 一条螺旋的九种视图

要判断预测对错，先得会看结构。讲者以 HIV 的 GP41 蛋白为例，取出一条 α 螺旋，逐层抽象：原子球体填满空间 → 带全部侧链的棒状（sticks）→ 只看骨架 → 一条样条曲线（[【跳转到 03:09】](https://www.youtube.com/watch?v=E61wJXlENoE&t=189)）。最后这种「速写」正是 Jane Richardson（杜克大学）把这种骨架图形命名为 α 螺旋的动机——把复杂分子降维成可画、可比对的图形。

![从原子球到骨架到样条：α 螺旋的层层抽象，是肉眼比对结构的基础](assets/AlphaFold%203%20Accuracy%20on%20Antibody%20Binding%20and%20Protein%20Interactions/00235.webp)

β 折叠同理：电子密度是三维实空间上的标量场，把分子「拟合」进去就得到模型；Jane Richardson 发明的箭头表示法把 β 链简化成带方向（N→C）的箭头（[【跳转到 08:00】](https://www.youtube.com/watch?v=E61wJXlENoE&t=480)）。

## 二、什么叫「错」：从 DALL·E 的幻觉说起

### 2.1 装错轮子的汽车

「错」也分程度——《生活大爆炸》的台词说得好：「说番茄是蔬菜只是有点错，说它是悬索桥就是大错特错。」讲者让生成式 AI 画「一辆轮子装错了的车」，得到的图能认出是车和轮胎，但轮胎没装对位置，甚至中间还多了个大脑——这就是 AI 的「幻觉」：组件还在，装配错了（[【跳转到 05:17】](https://www.youtube.com/watch?v=E61wJXlENoE&t=317)）。

![生成式 AI 幻觉出的「组件装配」：能认出是车，但轮胎装错、中间还多了个大脑](assets/AlphaFold%203%20Accuracy%20on%20Antibody%20Binding%20and%20Protein%20Interactions/00317.webp)

### 2.2 AF3 在蛋白复合物上也会「装错」

AlphaFold 3 对蛋白-蛋白复合物的预测出现了同款现象：部件（单体结构）看着都不错，**界面**却可能整个错位。这正是把它用于抗体-抗原这类复合物时要小心的原因（[【跳转到 06:05】](https://www.youtube.com/watch?v=E61wJXlENoE&t=365)）。

## 三、案例一：螺旋完全装反——电子密度说了算

### 3.1 癌症相关复合物里，螺旋的 N→C 朝向反了

杜克的合作者（PJO）研究一个癌症中非常重要的蛋白复合物：一个富含 α 螺旋的蛋白，结合一条独立的、同样带 α 螺旋的肽（[【跳转到 06:26】](https://www.youtube.com/watch?v=E61wJXlENoE&t=386)）。AlphaFold Multimer（AF3 的前身）返回的结构里，**肽的螺旋完全装反**——彩虹着色从 N 端到 C 端，一眼就能看出朝向反了。

![AF-Multimer 预测（彩虹色）与实验结构对比：螺旋的 N→C 朝向完全相反](assets/AlphaFold%203%20Accuracy%20on%20Antibody%20Binding%20and%20Protein%20Interactions/00411.webp)

### 3.2 晶体学电子密度是「真值」

这不是「数据没看清」：晶体衍射测得的电子密度（图中的网格 mesh）清楚地把螺旋钉在真实位置——解析得非常好，确实表明螺旋是反的（[【跳转到 07:51】](https://www.youtube.com/watch?v=E61wJXlENoE&t=471)）。后果严重：两种取向的**界面完全不同**，做药物设计会拿到完全错误的结果。

![晶体学电子密度（网格）清楚显示螺旋的真实位置，与 AF 预测相反](assets/AlphaFold%203%20Accuracy%20on%20Antibody%20Binding%20and%20Protein%20Interactions/00476.webp)

**现场 Q&A 值得一记**：有观众问「AF 是不是在最小化能量、正确解与错误解能量差多少？」讲者回答：AlphaFold 是深度学习，**不做能量最小化**；晶体结构是实验测量，测量结果就是「它不同」。就算把 AF 的解丢进 Rosetta/分子动力学里能量不高，也只说明你的能量函数**区分不了真假**，不能反过来证明 AF 对（[【跳转到 09:27】](https://www.youtube.com/watch?v=E61wJXlENoE&t=567)）。

## 四、案例二、三：设计的抗体结合 HIV 包膜——错在「侧面」

### 4.1 五个预测全错

讲者学生 Katherine 用 AF3 测试了实验室设计的抗体结合 HIV 包膜（Env）三聚体。正确结构（合作者的冷冻电镜）里，抗体结合在三聚体**顶部**；AF3 却让它结合在**侧面**——就像轮胎装到了车身上错误的位置。本例中 AF3 给出的 5 个预测**全部错误**（[【跳转到 15:26】](https://www.youtube.com/watch?v=E61wJXlENoE&t=926)）。第二个设计的抗体（由 Cu 设计）如出一辙。

![AF3 预测（左，抗体结合侧面）与冷冻电镜真值（右，结合顶部）：对称轴一比即知](assets/AlphaFold%203%20Accuracy%20on%20Antibody%20Binding%20and%20Protein%20Interactions/00926.webp)

### 4.2 置信度很高，但错得离谱

更麻烦的是置信度：结构按置信度着色大部分是蓝色（约 90%）、期望位置误差看起来也很小（[【跳转到 17:40】](https://www.youtube.com/watch?v=E61wJXlENoE&t=1060)）。AF3 每次只给 5 个预测、按置信度排序——本例 5 个全错。顺带一提：AF2 时代可以取 25 个样本，AF3 网页版只有 5 个。

![AF3 的置信度着色：大部分区域约 90% 高置信——但结合位点照样错了](assets/AlphaFold%203%20Accuracy%20on%20Antibody%20Binding%20and%20Protein%20Interactions/01060.webp)

### 4.3 训练机制 Q&A：结构 + MSA，不学亲和力

AF2/AF3 把结构表示成**距离矩阵**，学习距离矩阵上的分布，用结构与多序列比对（MSA）训练；**完全没用** PDBbind 之类的亲和力数据（[【跳转到 20:57】](https://www.youtube.com/watch?v=E61wJXlENoE&t=1257)）。一个讽刺的细节：讲者实验室的这些结构**就在 PDB 里**——AF3 本可以「背下来」，但预测照样错；也许发布时还没来得及用它重新训练。另外 AF3 是专有代码，网页版限 5 次预测、限配体数量，因为他们要把专有版本投入制药导向的商业项目。

## 五、官方口径 vs 实测

AF3 的「万圣节更新版」官方声称：抗体-抗原预测准确率从 AlphaFold Multimer 的 **23%** 提升到 **51%**（以 DockQ<0.23 为二元判据，[【跳转到 24:36】](https://www.youtube.com/watch?v=E61wJXlENoE&t=1476)）。换句话说，即便按官方最乐观的说法，抗体-抗原复合物预测**仍有一半是错的**。讲者在自己实验室约 10 个体系上的实测全军覆没——这是轶事不是统计，但与官方口径的「抗体仍是短板」一致。

![AF3 官方口径：抗体-抗原准确率 23%（AF-Multimer）→ 51%（AF3 latest），DockQ<0.23 判据](assets/AlphaFold%203%20Accuracy%20on%20Antibody%20Binding%20and%20Protein%20Interactions/01476.webp)

## 六、一线希望：PAE 矩阵——它「知道」自己不自信

### 6.1 Allan 的发现

讲者与博士后 Allan 重看结果，发现了关键：AF 输出的 **PAE（Predicted Aligned Error，期望位置误差）矩阵**——横纵轴都是残基编号（本例 1~2300）。矩阵里对角块（抗体自身、HIV 三聚体自身）误差很小，但**跨块**（抗体 ↔ HIV 之间）的误差高达 30 埃——而正常结构里残基间距离量级是 2~3 埃（[【跳转到 25:57】](https://www.youtube.com/watch?v=E61wJXlENoE&t=1557)）。

![PAE 矩阵：抗体与 HIV 三聚体各自（对角块）高置信，两者之间（跨块）误差高达 30 埃](assets/AlphaFold%203%20Accuracy%20on%20Antibody%20Binding%20and%20Protein%20Interactions/01557.webp)

### 6.2 第二个体系同样

第二个例子一样：对紫色块（较接近真值的部分）的信心还算合理，对品红（HIV）与绿/青（抗体）之间的相对位置**零信心**（[【跳转到 26:52】](https://www.youtube.com/watch?v=E61wJXlENoE&t=1612)）。

![第二个体系的 PAE 矩阵：部件内自信、部件间不自信的模式复现](assets/AlphaFold%203%20Accuracy%20on%20Antibody%20Binding%20and%20Protein%20Interactions/01625.webp)

### 6.3 Glimmer in the gloom

这就是标题里「黑暗中的微光」：**AF3 似乎知道自己可能错**——界面处的期望误差它如实报了 30 埃——但它照样乐意给你一个看起来完整的结构。结论：现阶段把 AF3 用于抗体-抗原流程大概率不准，但它「自我报告」的能力值得利用（先看 PAE 跨块误差，再决定要不要信），而且未来可能改进。

## 七、对管线 B 的意义

- 抗原-抗体复合物的 AF3/Protenix 预测**必须验证**：与实验/同源结构对齐看主链与界面 RMSD；没有真值时，至少检查 PAE 矩阵的「跨块误差」；
- 「部件好看 + 高置信」≠「界面正确」——抗体药物设计恰恰全靠界面；
- 与系列条目呼应：6.1.4（回折验证与 ipTM 判定）、5.1.3（置信度指标）、5.3.3（结构置信度不能当结合分类器）说的是同一件事：**结构置信度 ≠ 结合证据**；
- 想知道「不自信时该怎么办」，看姊妹篇《Bioexcel webinar #85》：物理对接 HADDOCK3 + AlphaFlow 采样的完整路线。

## 小结

- 会「看」结构是验证的前提：球 → 棒 → 骨架 → 样条；β 折叠箭头带 N→C 方向；
- AF3 的错误模式是「幻觉式装配」：部件对、界面错，与 DALL·E 装错轮子的车同构；
- 三个实测案例：螺旋 N→C 装反（电子密度证实）、两个设计抗体结合 HIV Env 全部错在「侧面」、5 个预测全错；
- 官方口径：抗体-抗原 23%→51%（DockQ<0.23）——即一半仍是错的；
- PAE 矩阵是诚实的信号：部件内低误差、部件间 30 埃+ —— AF3「知道自己可能错」，用它来预警；
- 现阶段抗体-抗原 AF3 预测不可直接采信，独立验证不可省。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| α 螺旋 / β 折叠 | 蛋白二级结构；常用样条/箭头抽象表示（Jane Richardson 命名） |
| 电子密度 | 晶体学衍射测得的「真值」，把分子拟合进去即得模型 |
| cryoEM | 冷冻电镜；本讲抗体-Env 复合物的实验真值来源 |
| PAE | Predicted Aligned Error，成对残基期望位置误差矩阵；跨块误差大 = 界面不可信 |
| DockQ | 复合物模型质量指标；AF3 官方以 DockQ<0.23 为「可接受」判据 |
| 幻觉（hallucination） | 生成式模型输出「部件真实、装配错误」结果的现象 |
| ipTM / 置信度着色 | 模型自报的界面/逐残基置信度；高置信 ≠ 界面正确（见 6.1.4、5.1.3） |
