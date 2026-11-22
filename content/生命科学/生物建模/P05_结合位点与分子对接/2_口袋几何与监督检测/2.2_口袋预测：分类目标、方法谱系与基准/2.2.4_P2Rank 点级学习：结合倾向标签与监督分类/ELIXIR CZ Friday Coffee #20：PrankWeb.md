# ELIXIR CZ Friday Coffee #20：PrankWeb——用随机森林在蛋白表面「圈出」配体结合口袋

> 视频来源：YouTube《ELIXIR CZ Friday Coffee #20: PrankWeb》（22 分 17 秒）。
> 讲者：Marian Novotný（查理大学 Charles University）；工具核心开发者：David Hoksza、Radoslav Krivák、Lukas Jendele 等。
> 本文基于视频「图-字幕」文稿整理；关键数字与名称均可在文内时间戳处回看视频核对。

## 本讲要解决的核心问题（SCQA）

**背景**：结构生物学进入快车道——连功能未知的蛋白也能解出三维结构。PDB 数据库里已经有超过 2000 个结构，名字里带着「推定蛋白/可能蛋白/假设蛋白」的字样 [【跳转到 02:14】](https://www.youtube.com/watch?v=bWp3-4F1qEw&t=134)。

**冲突**：结构有了，功能没谱：我们不知道这些蛋白能结合什么、在表面哪个位置结合，药物设计与功能注释都无从下手。

**疑问**：能不能只凭一组三维坐标，就自动指出「蛋白表面哪里可能结合小分子」？

**回答（中心思想）**：可以。**P2Rank** 用随机森林对蛋白表面网格点逐点预测「可配体结合性」，聚集成口袋并排序；**PrankWeb** 把它做成网页工具，并叠加「保守性」特征——预测更快、更准，还能滤掉大量弱预测。

![ELIXIR CZ Friday Coffee #20 报告：PrankWeb](assets/ELIXIR%20CZ%20Friday%20Coffee%20%2320：PrankWeb/00000.webp)

## 一、动机：结构解析普及了，功能注释没跟上

讲者先向工具的真正作者致意：这项工作在查理大学数学物理学院完成，核心出自 **David Hoksza** 与 **Radoslav Krivák** 之手，后来 **Lukas Jendele** 也参与进来；理学院与数学物理学院随后共建了联合生物信息学团队，讲者正是在那时加入 [【跳转到 01:00】](https://www.youtube.com/watch?v=bWp3-4F1qEw&t=60)。团队里还有同事专门负责 web 服务器维护与保守性（conservation）分析管线 [【跳转到 01:25】](https://www.youtube.com/watch?v=bWp3-4F1qEw&t=85)。

![致谢页：P2Rank/PrankWeb 背后的开发团队](assets/ELIXIR%20CZ%20Friday%20Coffee%20%2320：PrankWeb/00030.webp)

做这个工具的动机很直接：过去解析结构又贵又慢，只有明确目的时才会做；如今结构解析普及，**功能未知的蛋白也能出结构** [【跳转到 01:49】](https://www.youtube.com/watch?v=bWp3-4F1qEw&t=109)。PDB 里超 2000 个「假设蛋白」结构 [【跳转到 02:14】](https://www.youtube.com/watch?v=bWp3-4F1qEw&t=134) 就是证据。要用三维结构信息描述这些蛋白的功能或演化，就需要新工具——其中一类就是**配体结合位点预测**：既能帮功能未知蛋白找线索，也能服务药物设计与蛋白质工程 [【跳转到 02:39】](https://www.youtube.com/watch?v=bWp3-4F1qEw&t=159)。

![PDB 中 2000+ 个「假设蛋白」结构是工具的用武之地](assets/ELIXIR%20CZ%20Friday%20Coffee%20%2320：PrankWeb/00134.webp)

## 二、P2Rank / PrankWeb：预测「能不能结合」，不预测「结合的是谁」

这套工具**两个名字一套算法**：算法本体叫 **P2Rank**（由 David 开发），网页版叫 **PrankWeb** [【跳转到 03:04】](https://www.youtube.com/watch?v=bWp3-4F1qEw&t=184)。

![两个名字一套算法：P2Rank 与 PrankWeb](assets/ELIXIR%20CZ%20Friday%20Coffee%20%2320：PrankWeb/00184.webp)

任务定义要划清界限：它在蛋白表面找出「**有可能结合某种小分子**」的区域——**不预测具体会结合哪个配体**，只指出这个位置很可能能结合东西 [【跳转到 03:29】](https://www.youtube.com/watch?v=bWp3-4F1qEw&t=209)。输入是一个蛋白结构——可以是建模出来的结构，但**必须有三维坐标**；输出是一列可能结合配体的表面区域 [【跳转到 03:54】](https://www.youtube.com/watch?v=bWp3-4F1qEw&t=234)。

## 三、算法三步走：逐点打分 → 聚成口袋 → 排序输出

### 3.1 训练：Chen 数据集与逐点标注

P2Rank 是机器学习方法，用**随机森林**区分结合位点与非结合位点 [【跳转到 04:19】](https://www.youtube.com/watch?v=bWp3-4F1qEw&t=259)。训练数据从 **Chen 数据集**起步：约 200 个带配体的结构、约 450 个配体；挑选得很仔细——**每个 SCOP 家族只取一个代表结构**，并剔除盐、溶剂等生物学上不相关的配体 [【跳转到 04:44】](https://www.youtube.com/watch?v=bWp3-4F1qEw&t=284)。

标注方式很巧妙：对每个结构，用一张「网」（mesh）**覆盖蛋白表面** [【跳转到 05:09】](https://www.youtube.com/watch?v=bWp3-4F1qEw&t=309)；网格上每个点计算「理化性质+结构特征」的特征向量，再依据蛋白-配体复合物里配体的实际位置，给每个点标注「结合/不结合」[【跳转到 05:34】](https://www.youtube.com/watch?v=bWp3-4F1qEw&t=334)。这样训练出的模型，给定特征向量就能输出「这个点位于结合口袋的概率」。

![表面网格与逐点特征：把蛋白表面「织」成一张网](assets/ELIXIR%20CZ%20Friday%20Coffee%20%2320：PrankWeb/00309.webp)

### 3.2 特征：35 个理化+几何特征，protrusion 最重要

特征既有疏水性、电荷等**理化性质**，也有**几何性质**，共 **35 个**；其中看起来最重要的是 **protrusion（凸出度）**——衡量网格点周围一定距离内有多少个原子 [【跳转到 06:24】](https://www.youtube.com/watch?v=bWp3-4F1qEw&t=384)。

![35 个特征中最重要的是 protrusion（凸出度）](assets/ELIXIR%20CZ%20Friday%20Coffee%20%2320：PrankWeb/00384.webp)

### 3.3 预测：ligandability → 聚类 → 口袋分数 → 残基映射

对新结构：覆盖网格 → 套用模型 → 每点得到概率，称为 **ligandability score（可配体结合性分数）** → 滤掉低分点 → 把剩余点**聚类**成口袋——因为方法是「口袋级」而非「残基级」→ 累加口袋内各点分数得到口袋分 → 把点映射回残基，得到「哪些残基构成口袋」[【跳转到 06:49】](https://www.youtube.com/watch?v=bWp3-4F1qEw&t=409)~[【跳转到 07:39】](https://www.youtube.com/watch?v=bWp3-4F1qEw&t=459)。

![逐点分数聚类成口袋并累加打分](assets/ELIXIR%20CZ%20Friday%20Coffee%20%2320：PrankWeb/00434.webp)

## 四、保守性：把进化信息变成过滤弱口袋的利器

PrankWeb 在 P2Rank 之外引入了**保守性（conservation）**特征：既可以作为模型的又一个输入参数，也可以作为**后处理**——用保守性对找到的口袋重新打分 [【跳转到 07:50】](https://www.youtube.com/watch?v=bWp3-4F1qEw&t=470)。保守性从多序列比对（MSA）计算：可以直接查 **HSSP** 数据库，也可以自己用 **BLAST** 在 **Swiss-Prot / UniProt** 里搜序列再算 [【跳转到 08:15】](https://www.youtube.com/watch?v=bWp3-4F1qEw&t=495)。这一步较慢，但思路很硬——**越保守的位点通常越可能结合配体**，实测确实能提升结果 [【跳转到 08:40】](https://www.youtube.com/watch?v=bWp3-4F1qEw&t=520)。

![保守性特征：从 MSA 计算，可入模也可后处理](assets/ELIXIR%20CZ%20Friday%20Coffee%20%2320：PrankWeb/00495.webp)

成绩单用两个标准测试集：**Coach**（约 400 个单链蛋白）与 **holo4k**（大 10 倍、含多聚体蛋白），好处是可以与其他方法直接比较 [【跳转到 09:05】](https://www.youtube.com/watch?v=bWp3-4F1qEw&t=545)。指标不用常规的残基层面指标，而是「**成功率（success rate）**」：以口袋中心为参考，看 **4 埃阈值**内能否覆盖到配体 [【跳转到 09:55】](https://www.youtube.com/watch?v=bWp3-4F1qEw&t=595)。结果：所测方法中 **P2Rank 最佳**；把保守性作为参数加入后还会更好——该数据集上不明显，其余三个场景都有提升 [【跳转到 10:20】](https://www.youtube.com/watch?v=bWp3-4F1qEw&t=620)~[【跳转到 10:45】](https://www.youtube.com/watch?v=bWp3-4F1qEw&t=645)。

![基准测试：Coach 与 holo4k](assets/ELIXIR%20CZ%20Friday%20Coffee%20%2320：PrankWeb/00545.webp)

![4 埃成功率指标下 P2Rank 表现最佳](assets/ELIXIR%20CZ%20Friday%20Coffee%20%2320：PrankWeb/00620.webp)

## 五、不止本地工具：PDBe-KB 把口袋预测织进了蛋白视图

获取渠道有三个：**GitHub**（完整功能都在那里）、**web 服务器**（马上演示），以及 **PDBe Knowledge Base（PDBe-KB）**[【跳转到 10:45】](https://www.youtube.com/watch?v=bWp3-4F1qEw&t=645)。PDBe-KB 在 Friday Coffee 系列里介绍过：它尝试从「蛋白」而非「单个结构」的视角组织蛋白结构——输入 UniProt ID，就能看到该蛋白所有结构及各类信息，并集成了许多工具，P2Rank 也在其中 [【跳转到 11:10】](https://www.youtube.com/watch?v=bWp3-4F1qEw&t=670)。

![PDBe-KB：以蛋白为中心集成 P2Rank](assets/ELIXIR%20CZ%20Friday%20Coffee%20%2320：PrankWeb/00670.webp)

以**人肌动蛋白（human actin）**为例：输出展示各晶体结构中结合的配体与残基层面的口袋映射，与已知情况吻合得相当好；网页上还能看到每个残基属于哪个口袋 [【跳转到 12:00】](https://www.youtube.com/watch?v=bWp3-4F1qEw&t=720)。

![人肌动蛋白的 PDBe-KB 口袋映射](assets/ELIXIR%20CZ%20Friday%20Coffee%20%2320：PrankWeb/00720.webp)

## 六、边界在哪里：金属离子、核酸与隐蔽口袋还在路上

讲者坦率列出了局限：工具目前**未针对金属离子、多肽结合、核酸结合训练** [【跳转到 12:25】](https://www.youtube.com/watch?v=bWp3-4F1qEw&t=745)。计划中的方向有两个：一是为金属离子/核酸结合构建新数据集并训练模型，「应该很快会落地」[【跳转到 13:00】](https://www.youtube.com/watch?v=bWp3-4F1qEw&t=780)；二是训练识别**隐蔽结合位点（cryptic binding sites）**——这类位点在非结合（apo）与结合（holo）构象之间变化很大，通常是难啃的硬骨头 [【跳转到 13:25】](https://www.youtube.com/watch?v=bWp3-4F1qEw&t=805)。另外，现有保守性管线较慢，正在替换得**更快也更精确** [【跳转到 13:50】](https://www.youtube.com/watch?v=bWp3-4F1qEw&t=830)。

## 七、实战 KRAS：从「不可成药」到 AMG 510

网页操作非常简单：上传自己的结构，或直接填 PDB 编号（它会告诉你有几条链，可限定单链或对整结构做预测）[【跳转到 14:08】](https://www.youtube.com/watch?v=bWp3-4F1qEw&t=848)；可选跑不跑保守性计算（未预计算时可能很慢），也**可以自带 MSA**——如果你手里有一套很好的多序列比对，多数情况下会比它自动生成的更好 [【跳转到 14:58】](https://www.youtube.com/watch?v=bWp3-4F1qEw&t=898)。算法很快，**几乎瞬间出结果** [【跳转到 15:23】](https://www.youtube.com/watch?v=bWp3-4F1qEw&t=923)。

演示例子是 **KRAS 蛋白**——它对精准医疗很有意义，也是 ELIXIR 捷克想重点投入的方向：KRAS 是多种癌症中突变最多的癌基因之一 [【跳转到 15:48】](https://www.youtube.com/watch?v=bWp3-4F1qEw&t=948)。其中 **G12C**（第 12 位甘氨酸变成半胱氨酸）出现在近 10% 的肺腺癌中；长期以来它被认为不可成药，直到有人想到用突变出来的半胱氨酸做**共价修饰**——由此诞生了一批药物，其中一个就是安进的 **AMG 510** [【跳转到 16:13】](https://www.youtube.com/watch?v=bWp3-4F1qEw&t=973)。

![KRAS 与 G12C：精准医疗的明星靶点](assets/ELIXIR%20CZ%20Friday%20Coffee%20%2320：PrankWeb/00948.webp)

预测输出四个口袋，按分数排序（分数可以是绝对值也可以是概率），算了保守性还会多一个保守性分数；值得注意的是，**排名第一的口袋并不是有配体的那个** [【跳转到 16:38】](https://www.youtube.com/watch?v=bWp3-4F1qEw&t=998)~[【跳转到 17:03】](https://www.youtube.com/watch?v=bWp3-4F1qEw&t=1023)。

![KRAS 输出四个口袋，按分数排序](assets/ELIXIR%20CZ%20Friday%20Coffee%20%2320：PrankWeb/01023.webp)

可视化用 **Molstar**——这是 ELIXIR 捷克不同团队之间的一次漂亮合作。讲者笑说要向 Molstar 作者 David Sehnal 反馈一个「有趣」的表现：KRAS 的主要配体 **GDP** 这次没有被显示为配体（原因不明），不过它周围的结合位点相当清晰，而且**第二个口袋**正对应这个配体——可以看到工具对已知结合位点预测得相当好 [【跳转到 17:28】](https://www.youtube.com/watch?v=bWp3-4F1qEw&t=1048)~[【跳转到 17:53】](https://www.youtube.com/watch?v=bWp3-4F1qEw&t=1073)。

![Molstar 可视化：第二口袋对应 GDP 结合区](assets/ELIXIR%20CZ%20Friday%20Coffee%20%2320：PrankWeb/01073.webp)

打开保守性分数再跑一遍：输出几乎一样，只是**只剩三个口袋**——有一个「滥竽充数」的弱口袋被过滤掉了。这是保守性的另一大优势：**用上保守性后能滤掉大量很弱的预测** [【跳转到 18:18】](https://www.youtube.com/watch?v=bWp3-4F1qEw&t=1098)。不喜欢网页可视化？可以**下载全部结果**——得到 Molstar 配色标注的结果文件，以及蛋白序列层面的口袋映射 [【跳转到 19:08】](https://www.youtube.com/watch?v=bWp3-4F1qEw&t=1148)。

![下载结果：Molstar 配色与序列映射](assets/ELIXIR%20CZ%20Friday%20Coffee%20%2320：PrankWeb/01123.webp)

## 八、Q&A：分数怎么读、指纹怎么用

- **问：如果未知蛋白其实没有结合位点，工具能区分 binder 与 non-binder 吗？** 答：没有非常严格地测试过，但分数应该有指示性——不过它并不完美：大口袋的分数天然会比小口袋高很多。好在蛋白结构「什么都不结合」的情况其实很少见；但它结合的也可能是**蛋白-蛋白相互作用界面**——这个没训练过，据观察预测的基本都是配体结合位点，还需更细致的验证 [【跳转到 19:29】](https://www.youtube.com/watch?v=bWp3-4F1qEw&t=1169)~[【跳转到 20:19】](https://www.youtube.com/watch?v=bWp3-4F1qEw&t=1219)。真正实用的经验是：**口袋分数可以很低——如果你拿到的最高口袋分数只有 1、2 或 0.96 这种量级，那它几乎不可能是真正的口袋** [【跳转到 20:44】](https://www.youtube.com/watch?v=bWp3-4F1qEw&t=1244)。
- **问：配体和结合位点都有「指纹」（fingerprint），能否用指纹匹配来识别结合位点？** 答：没有训练过这个；如果有足够数据，对特定类型配体应该可行。但就目前而言，它只是一个非常通用的预测工具，没有针对任何特定配体做过训练 [【跳转到 21:34】](https://www.youtube.com/watch?v=bWp3-4F1qEw&t=1294)。

## 小结

- PrankWeb = P2Rank 算法 + 网页服务：输入三维坐标，输出「可能结合小分子」的口袋清单与排序——预测的是**可结合性**，不是具体配体。
- 算法核心：表面网格逐点 ligandability 打分（35 个理化+几何特征，protrusion 最重要）→ 滤低分、聚类成口袋 → 口袋分数 → 残基映射。
- 保守性特征（HSSP 或 BLAST 查 Swiss-Prot/UniProt）可入模可后处理：基准上再涨分，实战中还能滤掉弱口袋。
- 成绩单：Coach（约 400 单体）与 holo4k（10 倍、含多聚体）上按「4 埃成功率」优于所测同类方法。
- 入口三处：GitHub、web 服务器、PDBe-KB（以 UniProt 蛋白为中心集成）。
- 边界：金属离子/多肽/核酸未训练，隐蔽口袋与更快的保守性管线在路上；分数过低（1~2 量级）≈ 不是真口袋。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| P2Rank | PrankWeb 背后的随机森林口袋预测算法，GitHub 开源 |
| PrankWeb | P2Rank 的 web 版（prankweb.cz），支持保守性与在线可视化 |
| ligandability score | 网格点的「可配体结合性」概率，逐点输出 |
| protrusion | 网格点周围一定距离内的原子计数，最重要的几何特征 |
| 保守性（conservation） | 由多序列比对算出的位点进化保守程度 |
| Coach / holo4k | 两个标准配体结合位点基准测试集 |
| 成功率（success rate） | 口袋中心 4 埃内覆盖到配体的比例 |
| PDBe-KB | 以 UniProt 蛋白为中心组织 PDB 结构与工具的知识库 |
| G12C / AMG 510 | KRAS 第 12 位甘氨酸→半胱氨酸突变；安进据此思路开发的共价抑制剂 |
| 隐蔽结合位点（cryptic site） | apo→holo 构象变化后才出现的结合口袋 |
