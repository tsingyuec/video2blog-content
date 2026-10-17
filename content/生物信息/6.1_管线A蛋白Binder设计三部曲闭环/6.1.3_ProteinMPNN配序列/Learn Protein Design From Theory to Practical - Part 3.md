# RFdiffusion → ProteinMPNN → AlphaFold 全流程实操：重新设计 SRLip 脂肪酶（Bioinformatics Insights 第三期）

> 视频来源：[Learn Protein Design From Theory to Practical - Part 3](https://www.youtube.com/watch?v=WhaOqO4-9L8)（YouTube，34 分 14 秒，Bioinformatics Insights 频道，主讲人 Ashfaq Ahmed；蛋白设计系列前两讲理论之后的实操篇）

## 本讲要解决的核心问题（SCQA）

**背景**：RFdiffusion 生成骨架、ProteinMPNN 配序列、AlphaFold 回折验证——三部曲的理论已在前两讲分别铺垫；这一次在 Google Colab 里把三步**一次跑通**，而且对象是一个真实的酶，不是一个玩具示例。

**冲突**：设计目标是改造 SRLip 胞外脂肪酶（PDB 5MAL，催化二联体 Ser10 + His216，全长约 234 个氨基酸）：想要更好的脂酶活性、且能耐受高温，但**绝不能丢掉催化二联体**；而教程为了快速演示，每批只设计 1 条、迭代仅 25 步——这离真实科研的距离，讲者最后也坦诚交代。

**疑问**：contigs 怎么写才能「保住 motif、换掉其余」？ProteinMPNN 的 sampling temperature、「移除氨基酸」、设计数量怎么设置？跑出来的序列又怎么验证、怎么筛？

**回答（中心思想）**：用 contig「`A1-15/10 A210-234`」保留极 N 端与极 C 端片段、中段让模型新插 10 个残基；ProteinMPNN 用 **sampling temperature** 控制多样性（建议低值，>1.0 接近随机）、按需在「移除氨基酸」栏排除残基；生成的 2 条序列用 AlphaFold 验证（pLDDT 73%/72%）；真实研究要扫参数（中段 10/50/100/200…）、每批 16~32 条、配尽量高的迭代——找到最优设计约需一两天。

## 一、设计对象与假设：SRLip 与它的催化二联体

### 1.1 SRLip：来自链霉菌的胞外脂肪酶

今天的设计对象是 PDB 数据库里的一个结构：来自链霉菌 *Streptomyces rimosus* 的胞外脂肪酶，简称 SRLip。该结构已知具有多种酶活性（口播列举了脂酶、硫酯酶、酯酶、磷脂酶等），晶体结构由 X 射线衍射解析，分辨率 1.75 Å。[【跳转到 01:14】](https://www.youtube.com/watch?v=WhaOqO4-9L8&t=74)

### 1.2 催化二联体：Ser10 + His216

多数水解酶的活性中心是**催化三联体**（triad），而这个酶只有**二联体**（dyad）：Ser10 与 His216 两个残基，负责与底物相互作用——当甘油三酯底物进入活性口袋时，这两个残基相互作用并「抓住」它。PDB 编号是 **5MAL**，任何人都可以去下载；整条蛋白约 234 个氨基酸。[【跳转到 01:39】](https://www.youtube.com/watch?v=WhaOqO4-9L8&t=99)

![SRLip 的催化二联体：Ser10 与 His216 与底物相互作用](assets/Learn%20Protein%20Design%20From%20Theory%20to%20Practical%20-%20Part%203/00124.webp)

### 1.3 今天的假设

做实验性工作必须有假设。今天的假设就是：**重新设计 SRLip**——提高效率，在保持同样架构与活性位点的同时得到不同的拓扑结构；问题设定具体化为：获得更好的脂酶活性、且能耐受高温。[【跳转到 03:19】](https://www.youtube.com/watch?v=WhaOqO4-9L8&t=199)

## 二、蛋白设计四法与本次的选择

动手之前，讲者先快速过了一遍蛋白设计的四种方法——这也解释了「为什么选这个方法」：[【跳转到 04:14】](https://www.youtube.com/watch?v=WhaOqO4-9L8&t=254)

1. **无条件蛋白设计**（unconditional PD，PD 即 protein design）：不带任何预设知识设计一个蛋白，动机是探索各种可能的结构折叠（fold）；
2. **binder 设计**：通常人们找小分子化合物作抑制剂、激活剂或配体去作用某个蛋白；另一条路是为已有蛋白设计一个小的结合肽、小蛋白或另一个蛋白；
3. **基序支架**（motif scaffolding）：几乎每个蛋白里都有短小基序（motif），有些非常出名——比如 DNA 结合蛋白里的 **HTH 基序**（螺旋-转角-螺旋），正是它在与 DNA 互作。基序支架就是改造已有基序、或在蛋白里生成新基序：可以让重设计后的蛋白带上某个 HTH，也可以删掉某个基序看它表现如何；
4. **局部扩散**（partial diffusion）：不想改动整个结构，只改动一部分并按自己的意愿重新生成。

今天的教程做的就是**基序支架**（也可以叫局部扩散，两者相近）：保住催化二联体 Ser10+His216、改造其余结构来提高效率。[【跳转到 05:31】](https://www.youtube.com/watch?v=WhaOqO4-9L8&t=331)

![蛋白设计四种方法：无条件设计、binder 设计、基序支架、局部扩散](assets/Learn%20Protein%20Design%20From%20Theory%20to%20Practical%20-%20Part%203/00279.webp)

## 三、Colab 实操：RFdiffusion 生成骨架

### 3.1 notebook 入口与安装

实操照例在 Colab 里做（云端 notebook）：打开 Google Colab → 点 GitHub 选项卡 → 输入讲者的 GitHub 用户名 **AH100** → 选择仓库——这里有个小插曲：讲者先说成了 RFdiffusion，随后纠正其实是 **PD（protein design）仓库** → 点开 **RF Diffusion V1** 这个 ipynb（名字叫「training on RF Diffusion」，是面向初学者与研究生的蛋白设计教学 notebook；使用该方法当然要引用论文，点链接可见原文）。[【跳转到 05:53】](https://www.youtube.com/watch?v=WhaOqO4-9L8&t=353)

notebook 顶部就是四个选项：**无条件设计、条件设计、基序支架（motif scaffolding）、binder 设计**——与第二节的四法一一对应。运行第一个 cell 安装依赖，约 3 分钟。[【跳转到 06:52】](https://www.youtube.com/watch?v=WhaOqO4-9L8&t=412)

### 3.2 模板结构：5MAL 去水重命名为 ABC1

讲者用的模板结构放在下载文件夹，命名为 **ABC1.pdb**——其实就是 5MAL，只是去掉了结构里的水分子并重命名。为什么不直接从 PDB 读 5MAL？因为大多数时候你想用的是**自己本地的模型**，这个教程正好演示怎么读入自有结构。[【跳转到 07:22】](https://www.youtube.com/watch?v=WhaOqO4-9L8&t=442)

序列视图里可以定位 Ser10 与 His216；切到 3D 视图（白底）能看到活性位点的两个二联体残基—— somewhere 这里会捕获甘油三酯底物，并把它催化分解为脂肪酸。正因如此，这类脂酶有商用价值：用作洗涤剂添加剂等，去除油腻与各类脂肪污渍。[【跳转到 02:47】](https://www.youtube.com/watch?v=WhaOqO4-9L8&t=167)

![3D 视图中的两个催化二联体残基（白底高亮）](assets/Learn%20Protein%20Design%20From%20Theory%20to%20Practical%20-%20Part%203/00829.webp)

### 3.3 contigs 三段式拆解（本讲核心之一）

先给设计起名 **design_1**。接下来是 **contig（片段规划）**部分——它决定程序的哪些部分被约束、哪些被重新设计：[【跳转到 02:47】](https://www.youtube.com/watch?v=WhaOqO4-9L8&t=167)

原始写法 `A1-10` 表示第 1 到第 10 位氨基酸保持原样；讲者把它改成 `A1-15`；「斜杠 50」改成 10；后面是 `A210-234`。所以这条 contig 有**三段信息**：[【跳转到 02:47】](https://www.youtube.com/watch?v=WhaOqO4-9L8&t=167)

- **`A1-15`**：第 1–15 位保留原始结构的氨基酸（极 N 端片段）；
- **`/10`**：中间让程序**新插入 10 个氨基酸**（这正是要设计的部分）；
- **`A210-234`**：第 210–234 位保留原始结构（极 C 端片段）。

完整构建体就是 15 + 10 + 约 24 ≈ **49 个氨基酸**的小蛋白。注意保留下来的两端正是要「保住活性位点」的关键：Ser10 在 N 端片段里，His216 在 C 端片段里。[【跳转到 02:47】](https://www.youtube.com/watch?v=WhaOqO4-9L8&t=167)

![contig 三段式：A1-15 / 新插 10 残基 / A210-234](assets/Learn%20Protein%20Design%20From%20Theory%20to%20Practical%20-%20Part%203/00947.webp)

![完整构建体：15 + 10 + 约 24 ≈ 49 个氨基酸](assets/Learn%20Protein%20Design%20From%20Theory%20to%20Practical%20-%20Part%203/01022.webp)

### 3.4 其余参数与第一次报错

剩余参数逐个过：[【跳转到 05:39】](https://www.youtube.com/watch?v=WhaOqO4-9L8&t=339)

- **模板上传**：PDB 一栏有两个输入框。如果直接从 PDB 库读结构，两处都写编号（比如 `5MAL 5MAL`）；如果像本例读本地文件，先上传 → 点「复制路径」→ **别动冒号** → 选中文件名并把 `.pdb` 后缀去掉；
- **迭代步数**（iterations）：越高程序越慢但精度越高，教程选 **25**；
- **热点残基**（hotspot）：做 binder 设计、围绕特定残基设计结合蛋白时才用，本例**留空**；
- **设计数量**：最多可到 32，本例只设计 1 条；
- **对称性**（symmetry）：让程序 auto 自选，或指定二聚体=2、三聚体=3、四聚体=4；链名想改也行。

![notebook 参数区：迭代步数、热点残基（binder 设计专用）等](assets/Learn%20Protein%20Design%20From%20Theory%20to%20Practical%20-%20Part%203/01139.webp)

第一次运行报错了——教训很典型：**以为不填 PDB 也行，其实必须填**。补上后顺利跑通。想展示结果可选 DPI 分辨率、按链或按 pLDDT 着色，或像动画一样播放。[【跳转到 05:39】](https://www.youtube.com/watch?v=WhaOqO4-9L8&t=339)

## 四、ProteinMPNN 配序列（本讲核心之二）

### 4.1 sampling temperature 与移除氨基酸

骨架生成后，进入 **ProteinMPNN** cell——它的作用在理论部分已详细讲过（见同条目《MPNN - ML for protein sequence design》一篇）。这里有两个参数值得逐字理解：[【跳转到 09:32】](https://www.youtube.com/watch?v=WhaOqO4-9L8&t=572)

![notebook 中的 ProteinMPNN 参数区](assets/Learn%20Protein%20Design%20From%20Theory%20to%20Practical%20-%20Part%203/01289.webp)

- **「移除氨基酸」栏**：如果想让蛋白耐受高温，通常做法是**引入半胱氨酸**形成二硫键；而本示例的这一栏里恰恰预先写了半胱氨酸（表示要把它从设计中排除）。你可以排除它，也可以不管——讲者演示时把它从栏里删掉了；
- **sampling temperature（采样温度）**：可以调高或调低。这是控制设计多样性的关键旋钮——强烈建议去读这套流程的论文原文，理解每个参数怎么用；否则每个区块都配例子讲下去，这期视频要超过两三个小时。

另外：multimer（多聚体）选项没勾；只要 **2 条序列**——其实这个 notebook 对一个骨架**最多能设计 64 条**序列。[【跳转到 09:32】](https://www.youtube.com/watch?v=WhaOqO4-9L8&t=572)

![ProteinMPNN 参数区：sampling temperature 可调、移除氨基酸栏](assets/Learn%20Protein%20Design%20From%20Theory%20to%20Practical%20-%20Part%203/01339.webp)

### 4.2 两条序列与 AlphaFold 回折验证

程序生成了 2 条序列，然后自动运行 **AlphaFold 验证**：看新序列能不能折叠成这类结构。[【跳转到 09:49】](https://www.youtube.com/watch?v=WhaOqO4-9L8&t=589)

结果给出序列 1 与序列 2，并附上 pTM 分数、pLDDT 分数——pLDDT 相当不错，**73% 和 72%**——以及 PAE（位置对齐误差）与 RMSD 等。选「显示最佳结果」，再打包下载全部产物。这正是三部曲的第三步「回折验证」：序列好不好，让折叠模型说了算。[【跳转到 09:49】](https://www.youtube.com/watch?v=WhaOqO4-9L8&t=589)

![两条设计序列的 AlphaFold 验证结果：pTM / pLDDT 73% 与 72%](assets/Learn%20Protein%20Design%20From%20Theory%20to%20Practical%20-%20Part%203/01439.webp)

## 五、批次二与「扫参数」工作法

下载的同时，讲者只改**一个值**再跑一次：把 contig 的中段从 10 改成 50——批次二里，N 端片段与 C 端片段之间由 50 个氨基酸连接；名字改为 **design_2**。可以说他在做两个批次：批次一中段 10 个氨基酸、批次二 50 个；可以看到 design_2 得到的蛋白比批次一大了一点。[【跳转到 09:49】](https://www.youtube.com/watch?v=WhaOqO4-9L8&t=589)

![批次设置对比：中段 10 vs 50 个氨基酸](assets/Learn%20Protein%20Design%20From%20Theory%20to%20Practical%20-%20Part%203/01514.webp)

讲者反复强调教程设置与真实研究的差距：每批 1 条、迭代 25 步只是演示。**真实研究要增加设计数量、提高迭代步数，并用不同设置大量生成设计**——中段长度扫 50、10、20、100、200、150……这样铺开。[【跳转到 09:49】](https://www.youtube.com/watch?v=WhaOqO4-9L8&t=589)

## 六、离线分析与筛选：best PDB 的喜与忧

两个结果包下载解压后，进入 design_1 的结果输出目录，载入 **best PDB** 到查看器（PyMOL/ChimeraX 之类）观察：Ser 在这里，His 来自 C 端片段这一侧——看起来很不错，两个残基距离很近，有较大概率保持功能。[【跳转到 09:49】](https://www.youtube.com/watch?v=WhaOqO4-9L8&t=589)

![design_1 best PDB：Ser 与 His 距离很近](assets/Learn%20Protein%20Design%20From%20Theory%20to%20Practical%20-%20Part%203/01832.webp)

但讲者指出一个大问题：**His 落在了 loop 区**——loop 非常灵活，柔性可能影响结合，实验室场景下他不太敢用这种结构。这是筛选环节最常见的坑：指标（pLDDT/pTM）好看，但结构细节（关键残基落在柔性区）不可靠。

design_2 的 best 结构则明显不完美——每批只设计 1 条，本来就难出好结构（正常应该每批设计很多条）。改进路径与第五节一致：**提高迭代步数、每批设计 16~32 条、再扫不同中段长度生成多个批次**——找到最佳设计几乎要花一两天的工作量。[【跳转到 09:49】](https://www.youtube.com/watch?v=WhaOqO4-9L8&t=589)

![给初学者的建议：增加迭代与每批设计数量](assets/Learn%20Protein%20Design%20From%20Theory%20to%20Practical%20-%20Part%203/01934.webp)

## 七、给初学者的科研建议

讲者在等待计算时专门聊了如何把这套方法做成硕士/博士课题：[【跳转到 09:32】](https://www.youtube.com/watch?v=WhaOqO4-9L8&t=572)

1. 选一个酶，定一个假设（保活性位点 + 改某种性质，如耐温、活性）；
2. 用 contig 保留 motif（本例的催化二联体）；
3. 扫参数（中段长度、设计数量、迭代步数）生成大量设计；
4. AlphaFold 回折验证，离线打开 best PDB 逐个检查（重点看关键残基是否落在稳定结构区而非 loop）；
5. 筛出最优设计交给实验验证。

这个系列到此完结：前两讲是理论、本讲是初步实操，往后的蛋白设计视频会更专门、更进阶。[【跳转到 09:32】](https://www.youtube.com/watch?v=WhaOqO4-9L8&t=572)

## 小结

- 本讲把三部曲在 Colab 里一次跑通：RFdiffusion 生成骨架 → ProteinMPNN 配序列 → AlphaFold 回折验证。
- 设计对象 SRLip（PDB 5MAL）只有催化**二联体** Ser10+His216（多数酶是三联体）——contig 用 `A1-15/10 A210-234` 三段式保住两个关键残基、中段新插 10 残基（构建体 ≈ 49 aa）。
- **sampling temperature** 是 ProteinMPNN 控制多样性的关键参数：可高可低，建议低值；「移除氨基酸」栏可排除半胱氨酸（若不追求二硫键）。
- AlphaFold 验证给出 pTM/pLDDT/PAE/RMSD——本例 pLDDT 73%/72%，指标好看。
- 筛选不能只看指标：design_1 的 His 落在柔性 loop 区，实验室可用性存疑；design_2 结构不完美。
- 教程级设置（1 条设计、25 步迭代）≠ 真实科研：每批 16~32 条、高迭代、扫中段长度多批次，找最优约需一两天。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| SRLip | 来自 *Streptomyces rimosus* 的胞外脂肪酶（PDB 5MAL，1.75 Å），本讲的设计对象 |
| 催化二联体（dyad） | 由两个残基（Ser10+His216）组成的活性中心；多数水解酶是三联体（triad） |
| motif scaffolding（基序支架） | 围绕既有功能基序生成/改造蛋白结构，让新结构把基序「装进去」 |
| partial diffusion（局部扩散） | 只改动结构的一部分并重新生成，与基序支架相近 |
| contig | RFdiffusion 的残基配置串：`A1-15/10 A210-234` = 保留 1–15、新插 10、保留 210–234 |
| hotspot（热点残基） | binder 设计中指定 binder 与之互作的靶标残基；本例不用、留空 |
| sampling temperature | ProteinMPNN 的采样温度：控制逐位置采样的随机程度，越低越保守、越高（>1.0）越接近随机 |
| pTM / pLDDT / PAE | AlphaFold 输出的置信度指标：全局折叠置信度 / 逐残基置信度 / 逐残基对误差 |
| 「移除氨基酸」栏 | 指定设计时不允许出现的残基（本例预填 CYS，讲者演示将其删除） |
