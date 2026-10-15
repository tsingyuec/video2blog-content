# ColabFold：MSA 搜索从一小时到四分钟，结构预测从此人人可跑

> 视频来源：[ColabFold - Making protein folding accessible to all via Google Colab!](https://www.youtube.com/watch?v=Rfw7thgGTwI&t=0)（YouTube · Boston Protein Design and Modeling Club · Sergey Ovchinnikov / Martin Steinegger）
> 本文基于视频演说图文稿整理，配图截自视频。

## 本讲要解决的核心问题（SCQA）

**背景**：AlphaFold2 / RoseTTAFold 这类结构预测网络的输入端都是一个多序列比对（MSA）：拿查询序列去数据库搜索同源序列、按进化关系排成列，模型从"保守的列"读稳定性、从"共变的列"读残基接触。

**冲突**：生成 MSA 的代价高得吓人——AlphaFold2 官方流程要搜三个巨大数据库（约 2.5 TB），单条蛋白在多核机器上要花数小时；DeepMind 官方 Colab 虽然免安装，但只支持单体、只返回一个模型、不能调循环次数，比对一次也要 20–30 分钟。

**疑问**：能不能让任何人打开浏览器就跑上完整的结构预测——既快，又能玩复合物、循环、随机种子这些进阶功能？

**回答（中心思想）**：ColabFold 的答案是**把搜索搬进 MMseqs2**：k-mer 预过滤 + 双对角线命中 + Smith-Waterman 精比对，是唯一同时支持谱信息与迭代搜索的快速搜索方法，比 PSI-BLAST 快约 300–400 倍且更灵敏；配上服务器版，单条查询单核约 4 分钟出 MSA——预测精度与官方系统相当，瓶颈从此反转为 GPU 推理本身。

---

## 一、为什么 MSA 是一切的核心

### 1.1 从一条序列到"一列证据"

![结构预测的总览图：序列 → 搜索得到 MSA → 网络架构 → 输出结构](assets/ColabFold%20-%20Making%20protein%20folding%20accessible%20to%20all%20via%20Google%20Colab!/00224.webp)

只盯一条序列，你能做的很有限：凭生化知识猜猜哪些是亲水/疏水氨基酸，很难判断哪些位置真正重要 [【跳转到 30:08】](https://www.youtube.com/watch?v=Rfw7thgGTwI&t=1808)。而 MSA 的价值正在于此：把同源序列对齐成列之后，**在所有物种里都相同的位置（保守）**提示功能约束，**同步变化的列对（共变）**提示这两个残基在空间上相互接触——共变列正是接触预测的经典证据，AlphaFold 推理的也正是这类模式 [【跳转到 15:51】](https://www.youtube.com/watch?v=Rfw7thgGTwI&t=951)。

> 讲者提醒：MSA 的每一行是一条序列、每一列是一个残基位置；"好比对"意味着每列的残基真的来自共同祖先的那个位置。深度也从来不是越高越好——把同一条序列重复 100 遍不会带来任何信息，该看的是去冗余后的多样性，以及沿全序列的覆盖度 [【跳转到 27:28】](https://www.youtube.com/watch?v=Rfw7thgGTwI&t=1648)。

### 1.2 从传统流水线到端到端

![传统结构预测流水线：MSA → 接触预测/PSSM/片段 → 折叠；或抄模板坐标](assets/ColabFold%20-%20Making%20protein%20folding%20accessible%20to%20all%20via%20Google%20Colab!/00262.webp)

传统做法是一条多步流水线：从 MSA 预测残基接触，再构建 PSSM、预测二级结构、搜索结构片段，用折叠算法（FRAGFOLD、Rosetta）重新组合；若模板命中，甚至可以直接"偷"模板坐标、替换序列 [【跳转到 04:22】](https://www.youtube.com/watch?v=Rfw7thgGTwI&t=262)。AlphaFold1 的进步是把马尔可夫随机场的原始特征直接喂给 ResNet，让它预测二面角与距离；AlphaFold2 则几乎完全端到端：MSA 与模板进 Evoformer 式的 MSA 模块，出初始坐标，再由结构模块精修并反复循环（recycle）[【跳转到 07:42】](https://www.youtube.com/watch?v=Rfw7thgGTwI&t=462)。注意：这些方法无论怎么演进，**全都依赖 MSA 和模板**。

![Evoformer 模块：可理解为共变算法的"展开"版本，同时引入结构先验](assets/ColabFold%20-%20Making%20protein%20folding%20accessible%20to%20all%20via%20Google%20Colab!/02062.webp)

有人问：AlphaFold 需要的序列更少，是不是就不依赖成对（pairwise）上下文了？讲者的解释是：Evoformer 对 MSA 反复处理 48 次，相当于把共变分析"展开"并叠加结构先验，因此用更少的序列也能判定"谁和谁接触" [【跳转到 34:22】](https://www.youtube.com/watch?v=Rfw7thgGTwI&t=2062)。

### 1.3 预测不会比输入更好：MSA 决定上限

这句是全场的题眼：**预测出的结构不会比输入信息更好**。实测发现模板的作用没有想象中大——信息主要来自 MSA [【跳转到 08:32】](https://www.youtube.com/watch?v=Rfw7thgGTwI&t=512)。在 CASP FM（自由建模）目标上的对比显示：MSA 中序列少于 30 条的目标（图中蓝点）预测明显变差；但有个极端例子只找到两三条序列，TM 分数仍有 0.8 以上——前提是这几条序列**足够多样** [【跳转到 16:52】](https://www.youtube.com/watch?v=Rfw7thgGTwI&t=1012)。老方法需要约 1000 条，AlphaFold2 常常 30 条就够，超过 100 条信息量增益已经很小。

---

## 二、AlphaFold 的输入数据库与本地的代价

![AlphaFold2 的输入数据库：UniRef90、宏基因组库（MGnify/BFD）与模板库 PDB70](assets/ColabFold%20-%20Making%20protein%20folding%20accessible%20to%20all%20via%20Google%20Colab!/00537.webp)

Martin 介绍了 AlphaFold2 官方搜索的三个数据库 [【跳转到 08:57】](https://www.youtube.com/watch?v=Rfw7thgGTwI&t=537)：

- **UniRef90**：UniRef 的聚类版，用 jackhmmer 搜索；
- **MGnify**：EBI 维护的宏基因组库（主要是人类肠道来源，含大量原核与部分病毒序列）——专为"难预测目标"补充序列多样性；
- **BFD**（Big Fantastic Database）：随 AlphaFold2 论文发布，主要来自**土壤**宏基因组——土壤是微生物多样性最丰富的环境，作者为此开发了专用组装器；BFD 把蛋白质聚类成隐马尔可夫模型（HMM），可用 HHblits 迭代搜索，越搜越大。

再加上模板库 PDB70（用于模板特征，但如今模板对性能的贡献已经不大）。要在本地完整安装这套流程：数据库约 **2.5 TB**，多核搜一条蛋白也要数小时 [【跳转到 11:27】](https://www.youtube.com/watch?v=Rfw7thgGTwI&t=687)。

---

## 三、MMseqs2：把搜索从小时级压到分钟级

### 3.1 三步走：预过滤 → 双对角线 → 精比对

![MMseqs2 的 k-mer 预过滤：相似 k-mer 列表 + 双对角线命中判据](assets/ColabFold%20-%20Making%20protein%20folding%20accessible%20to%20all%20via%20Google%20Colab!/00737.webp)

ColabFold 用 MMseqs2 取代了 jackhmmer + HHblits 的沉重组合 [【跳转到 11:52】](https://www.youtube.com/watch?v=Rfw7thgGTwI&t=712)。MMseqs2 的搜索分三步：先用**较长的 k-mer** 做预过滤——不只精确匹配，还允许相似 k-mer；当一条数据库序列上有**两条长 k-mer 落在同一对角线上**（双对角线命中）才升级；最后只对幸存者做完整的 Smith-Waterman 精比对 [【跳转到 12:17】](https://www.youtube.com/watch?v=Rfw7thgGTwI&t=737)。关键在于：市面上快速搜索方法很多，但 **MMseqs2 是唯一既能利用谱（profile）信息、又能做迭代搜索的快速方法**——这对构建高质量 MSA 至关重要。

![灵敏度-加速倍数对比图：MMseqs2 比 PSI-BLAST 快约 300–400 倍且更灵敏](assets/ColabFold%20-%20Making%20protein%20folding%20accessible%20to%20all%20via%20Google%20Colab!/00812.webp)

实测曲线上，横轴是灵敏度、纵轴是加速倍数：MMseqs2 比 PSI-BLAST 快约 300–400 倍，灵敏度反而更高，同区间没有对手 [【跳转到 14:22】](https://www.youtube.com/watch?v=Rfw7thgGTwI&t=862)。Milot Mirdita 又为它做了服务器版，单条查询几秒到几分钟即可返回——这正是 ColabFold 能承受社区请求的关键。

### 3.2 瓶颈反转：1 小时 → 4 分钟

![速度对比：DeepMind Colab 与完整系统搜库约 1 小时，MMseqs2 单核 4 分钟](assets/ColabFold%20-%20Making%20protein%20folding%20accessible%20to%20all%20via%20Google%20Colab!/01087.webp)

对比非常直观：DeepMind Colab 对一个目标搜库要约 1 小时，AlphaFold2 完整系统用多核也要约 1 小时；而一条 20 序列的 MSA 用 MMseqs2 在**单核上只要 4 分钟** [【跳转到 18:07】](https://www.youtube.com/watch?v=Rfw7thgGTwI&t=1087)。于是流程反转：以前是"等 MSA 一小时、GPU 推理十几分钟"，现在是"MSA 几分钟、GPU 推理反而更久"——有时 10–15 分钟就能拿到结构。

### 3.3 与 DeepMind Colab 的正面比较

在上一届 CASP 全部 FM 目标上，把 DeepMind Colab、ColabFold 与 AlphaFold2 完整系统三方对比：ColabFold 与 DeepMind Colab 表现相当（部分目标略好），与完整系统也非常接近 [【跳转到 16:02】](https://www.youtube.com/watch?v=Rfw7thgGTwI&t=962)。有意思的是两者的实现路线完全不同：DeepMind Colab **不把序列发到服务器**，而是在内存里建虚拟盘，把缩减后的数据库流式读进 RAM、逐块跑 jackhmmer、搜完即删——所以仍要几十分钟；ColabFold 则把序列交给 MMseqs2 服务器，几分钟内返回 [【跳转到 79:26】](https://www.youtube.com/watch?v=Rfw7thgGTwI&t=4766)。

---

## 四、a3m：MSA 搜索的输出，也是自定义 MSA 的入口

### 4.1 跑完之后，结果包里永远有一份 a3m

![运行结果打包下载：包含生成的 a3m 文件、5 个模型与统计图](assets/ColabFold%20-%20Making%20protein%20folding%20accessible%20to%20all%20via%20Google%20Colab!/04424.webp)

notebook 跑完后会把所有信息打包成 zip 供下载，其中就包括**这次搜索生成的 a3m 文件**、全部 5 个模型（若开启 Amber 弛豫还会有弛豫前后各 5 个）以及统计图片 [【跳转到 1:13:44】](https://www.youtube.com/watch?v=Rfw7thgGTwI&t=4424)。如果你只想要比对、不关心预测，甚至可以只运行输入与搜索相关的几个单元格然后停下——点开文件面板就能看到 a3m，直接下载 [【跳转到 1:16:10】](https://www.youtube.com/watch?v=Rfw7thgGTwI&t=4570)。

### 4.2 搜到了什么：数量与相似度一目了然

![序列覆盖与相似度分布图：每个位置找到多少条序列、离查询序列多远](assets/ColabFold%20-%20Making%20protein%20folding%20accessible%20to%20all%20via%20Google%20Colab!/06194.webp)

搜索完成后，MMseqs2 会明确告诉你**找到了多少条序列**；配图显示每个位置的序列数，以及命中序列与查询序列的相似程度——如果全是紫色，说明命中和查询几乎一致；分布越广说明找到的同源越多样。最终的 zip 里也包含输入 MSA，因此**任何人都能复现你的结果** [【跳转到 1:43:14】](https://www.youtube.com/watch?v=Rfw7thgGTwI&t=6194)。

### 4.3 自定义 MSA 与"配对"问题

如果你已经构建了自己的 MSA，notebook 提供 custom 选项直接上传使用 [【跳转到 1:05:06】](https://www.youtube.com/watch?v=Rfw7thgGTwI&t=3906)。这正呼应了 AlphaFold3 / Protenix 体系的要求：自带 MSA 必须是 **A3M 格式**、第一条序列与查询序列相同、非插入区长度一致（详见本条目另一篇 AF3 输入详解）。而复合物预测里的"配对"更有意思：**RoseTTAFold 必须提供配对好的 MSA**（来自蛋白 A 与蛋白 B 的序列要按物种对应好）才能正确折出复合物；AlphaFold 却出人意料地"不挑食"——把两条链的未配对序列交错着放进去也能工作，甚至看起来比 Rosetta 更常成功 [【跳转到 46:10】](https://www.youtube.com/watch?v=Rfw7thgGTwI&t=2770)。notebook 里的 pair MSA 选项还会自动判断两条序列是否来自同一基因组、是则拼接 [【跳转到 1:09:47】](https://www.youtube.com/watch?v=Rfw7thgGTwI&t=4187)。

---

## 五、复合物预测：一场"意外收获"

### 5.1 两个小技巧：甘氨酸连接子与残基索引

社区最早用"超长甘氨酸连接子"把两条链假装成一条蛋白来预测相互作用 [【跳转到 36:39】](https://www.youtube.com/watch?v=Rfw7thgGTwI&t=2199)；更好的做法是 **Minkyung 提出的残基索引技巧**：把第二条链的残基编号从 2001 开始——仅凭这一点就能"骗"过模型，让它把两条当独立分子建模 [【跳转到 40:07】](https://www.youtube.com/watch?v=Rfw7thgGTwI&t=2407)。实测中后者效果更好：加连接子反而可能把整个组装搞乱，因此 ColabFold 服务器采用残基索引方案 [【跳转到 47:43】](https://www.youtube.com/watch?v=Rfw7thgGTwI&t=2863)。更有趣的是，把单体能预测错方向的一条螺旋，按二聚体建模后竟然被修正了——说明"这两条链在一起"的信息本身就在帮助模型。

### 5.2 同源寡聚与循环对称的"旋转展开"

![多拷贝输入的坐标从同一位置出发，绕对称轴"旋转展开"成圆](assets/ColabFold%20-%20Making%20protein%20folding%20accessible%20to%20all%20via%20Google%20Colab!/05015.webp)

把同一蛋白的多份拷贝一起输入时，所有坐标从同一位置出发、像圆规一样绕对称轴"展开"成圆：给 10 份就绕出 10 份，给 3 份就绕到 3 份为止 [【跳转到 1:23:35】](https://www.youtube.com/watch?v=Rfw7thgGTwI&t=5015)。代价是**循环对称下拷贝数会被"顺势"多放**——界面长得几乎一样，模型分不清六聚体和八聚体；而非循环（反平行）的二聚体界面是"锁死"的，多给拷贝只会得到两个独立复合物 [【跳转到 1:22:43】](https://www.youtube.com/watch?v=Rfw7thgGTwI&t=4963)。

### 5.3 读懂置信度：pLDDT 看单体，PAE 看界面

![pLDDT 与 PAE：前者评每个残基，后者评每对残基的相对位置（单位埃）](assets/ColabFold%20-%20Making%20protein%20folding%20accessible%20to%20all%20via%20Google%20Colab!/02514.webp)

每个残基都有 pLDDT 置信度（0–100，低于 50 就很不可靠）；每对残基之间还有预测对齐误差（PAE），单位埃、越低越好 [【跳转到 41:54】](https://www.youtube.com/watch?v=Rfw7thgGTwI&t=2514)。评估复合物时两者都要看：模型可能对每个结构域内部很自信，但对**结构域之间或链之间的相互作用**没把握——PAE 图中高值（红）区域就是不可信的界面 [【跳转到 42:44】](https://www.youtube.com/watch?v=Rfw7thgGTwI&t=2564)。此外要诚实地说：**AlphaFold 并不是为预测复合物而训练的**——这是发布后社区发现的"非预期用途"，完全实验性；蛋白-多肽方向已有预印本做了基准测试，值得参考 [【跳转到 1:25:27】](https://www.youtube.com/watch?v=Rfw7thgGTwI&t=5127)。

---

## 六、进阶 notebook：循环、种子与多样性

![高级 notebook：可选 MMseqs2 或 DeepMind 的 jackhmmer，还能设循环与种子](assets/ColabFold%20-%20Making%20protein%20folding%20accessible%20to%20all%20via%20Google%20Colab!/05292.webp)

默认 notebook 覆盖单体/同源寡聚的基础场景；**高级 notebook** 面向专家：可选用 MMseqs2 或 DeepMind 的 jackhmmer 方案、可跑单序列、可调循环次数与随机种子 [【跳转到 1:28:12】](https://www.youtube.com/watch?v=Rfw7thgGTwI&t=5292)。要点：

- **循环收敛阈值**：默认只循环 3 次；高级版可设最多 48 次，并在相邻两次循环的距离差低于阈值（如 0.5 埃）时提前停止——这个停止机制是 ColabFold 给 AlphaFold 源码打的补丁 [【跳转到 1:31:07】](https://www.youtube.com/watch?v=Rfw7thgGTwI&t=5467)。预测寡聚体时有时需要约 10 次循环才能"合"到正确构象 [【跳转到 49:34】](https://www.youtube.com/watch?v=Rfw7thgGTwI&t=2974)。
- **批量种子**：填"尝试 1 到 10"即可跑 10 个种子，全部保存、排序后给前 5，命名规则注明"模型参数 + pTM + 种子号" [【跳转到 1:32:47】](https://www.youtube.com/watch?v=Rfw7thgGTwI&t=5567)。
- **turbo 提速**：不用模板时只需编译 1 个模型再换权重，运行飞快；截至报告时未见影响结果，担心可关闭 [【跳转到 1:34:02】](https://www.youtube.com/watch?v=Rfw7thgGTwI&t=5642)。每个模型还会额外输出预测 TM 分数（pTM）[【跳转到 1:35:17】](https://www.youtube.com/watch?v=Rfw7thgGTwI&t=5717)。
- **何时不必要**：如果你有几千条序列，哪怕只循环 1 次往往就直接命中；**循环本质上是低数据场景下的采样过程**——类比 Rosetta 的 ab initio 轨迹采样，MSA 很好时根本不用采样 [【跳转到 1:36:07】](https://www.youtube.com/watch?v=Rfw7thgGTwI&t=5767)。

---

## 七、实用信息速览

- **硬件**：搜库要 CPU 核心数与大内存（约 128 GB 起）+ NVMe 固态盘；模型推理看 GPU 显存（RTX 3090 是好选择）[【跳转到 21:51】](https://www.youtube.com/watch?v=Rfw7thgGTwI&t=1311)。免费 Colab 的 16 GB 显存大约支持 **1400 个氨基酸**的总长度；Colab Pro 只是排队优先级更高 [【跳转到 1:17:25】](https://www.youtube.com/watch?v=Rfw7thgGTwI&t=4645)。notebook 本身是普通 Jupyter 文件，可放到自己的云实例或通过 local runtime 连接本地/学校集群。
- **从头设计蛋白**：没有同源序列可用，选"单序列"模式——这考察的是模型"物理内核"本身 [【跳转到 1:05:06】](https://www.youtube.com/watch?v=Rfw7thgGTwI&t=3906)。
- **RoseTTAFold notebook**：界面几乎相同，但 Colab 版不含 PyRosetta（精修需完整管线，请用 RoseTTAFold Web 服务器）。数据不足时它与 AlphaFold **各有所长**——训练种子与架构差异让两者"专精"不同的结构空间，值得两个都跑 [【跳转到 1:41:29】](https://www.youtube.com/watch?v=Rfw7thgGTwI&t=6089)。
- **循环动画**：讲者现场写了一个能把每次循环的结构对齐、按 Z 轴排序并用彩虹色画出"旋转展开"动画的 notebook——对从头设计蛋白的低数据场景很有启发 [【跳转到 1:43:56】](https://www.youtube.com/watch?v=Rfw7thgGTwI&t=6236)。

---

## 小结

- **MSA 决定上限**：预测不会比输入更好；模板作用有限，信息主要来自 MSA；30 条**多样**序列常常就够，深度不是好指标，多样性与覆盖度才是。
- **MMseqs2 是提速关键**：k-mer 预过滤 + 双对角线命中 + Smith-Waterman 精比对；唯一支持谱信息与迭代搜索的快速方法，比 PSI-BLAST 快 300–400 倍且更灵敏；服务器版让单条查询几分钟出 MSA，瓶颈反转为 GPU 推理。
- **a3m 贯穿始终**：MSA 搜索的输出是 a3m，ColabFold 的结果包里永远有它，也是 AF3/Protenix 自带 MSA 的标准格式；只想要比对就只跑搜索单元格。
- **复合物预测是"意外收获"**：残基索引技巧优于甘氨酸连接子；循环对称会"旋转展开"、拷贝数可能被多放；评估靠 pLDDT + PAE 双指标；这是非预期用途，需保持审慎。
- **循环与种子是多样性旋钮**：默认 3 次循环、阈值收敛可提前停止；数据充足时 1 次循环就够，低数据时循环≈采样；批量种子 + RoseTTAFold 互补可扩大探索。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| MSA | 多序列比对：同源序列排成列，模型从中读保守性与共变（接触）信号 |
| a3m | HH-suite 系紧凑比对格式：对齐列用大写与 `-`，插入用小写；MSA 搜索（ColabFold 等）的标准输出，也是 AF3/Protenix 自带 MSA 的要求格式 |
| unpaired / paired MSA | 未配对 MSA 提供各链进化证据；配对 MSA 让多链中同物种序列对齐到相同列（Rosetta 必需，AlphaFold 交错未配对也常可行） |
| MMseqs2 | 超快序列搜索/聚类工具：k-mer 预过滤 + 双对角线命中 + Smith-Waterman；支持谱与迭代搜索，比 PSI-BLAST 快 300–400 倍 |
| UniRef90 / MGnify / BFD | AlphaFold2 搜索的三大数据库：UniRef 聚类版、肠道宏基因组库、土壤宏基因组库（聚成 HMM 供 HHblits 迭代搜索） |
| recycle | 循环：把上一轮预测作为特征再喂回网络；默认 3 次，低数据场景相当于采样轨迹 |
| pLDDT / PAE / pTM | 三种置信度指标：残基级置信度、残基对相对位置误差（埃）、整体/界面相似性的 TM 分数预测 |
| 残基索引技巧 | 把第二条链的残基编号拉大（如从 2001 起），让模型把两条链当独立分子——比甘氨酸连接子更稳 |
| RoseTTAFold | AlphaFold2 的同期开源竞品；与 AF 架构差异大，低数据场景下与之互补 |
