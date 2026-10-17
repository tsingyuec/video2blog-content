# De Novo Protein Design in Practice： What's Actually Working（with Michael Holden）

> 视频来源：YouTube《De Novo Protein Design in Practice: What's Actually Working (with Michael Holden)》（RANOMICS 频道 Protein Engineering in Practice 系列第一期直播，约 60 分钟）。对谈双方：**Leo Wan**（RANOMICS 创始人，多伦多蛋白与细胞工程 CRO）与 **Michael Holden**（计算蛋白设计咨询顾问，先后任职再生元 Regeneron、多特异性 ADC 公司）。本篇对应管线 A 的收官一步——**迭代筛选**：设计生成之后，"筛什么、怎么筛、筛完的数据怎么反哺下一轮"。

## 本讲要解决的核心问题（SCQA）

**背景**：管线 A 的前三步已经就位——RFdiffusion 生成骨架（见 6.1.2）、ProteinMPNN 配序列（见 6.1.3）、Protenix/OpenFold3 回折验证（见 6.1.4）。跑完一轮，手里可能有几万条通过 ipTM 闸门的候选 binder。

**冲突**：通过计算验证不等于会结合，更不等于有功能。置信分数与真实亲和力几乎零相关；数万条候选不可能全部进实验；96 孔板+BLI、酵母展示、噬菌体展示各有通量与信息量的错配。缺的不是生成能力，而是"迭代筛选"的实战视角。

**疑问**：一次 campaign 到底怎么筛？哪些指标能用、哪些会骗人？模型怎么选、硬件要多少？筛完的数据怎么用？

**回答（中心思想）**：把 in silico 设计当作管线的"上游供应商"而非终点——多模型并行生成、多指标统一打分做阴性过滤；按靶标信息量决定筛选规模（高置信少筛、新表位大筛）；把实验数据（尤其阴性数据）回流训练，形成 lab-in-a-loop 闭环。

## 一、为什么此刻人人都能做 de novo 蛋白设计

### 1.1 两件事在此刻汇流

de novo（从头）蛋白设计——不模仿任何天然蛋白、从零写出能结合目标的氨基酸序列——过去是大药企的专利，现在"数学中等、显卡一张"的普通实验室也能上手。Michael 归因于两件事在此刻汇流（[【跳转到 04:31】](https://www.youtube.com/watch?v=cVmGeFGsVA0&t=271)）：

1. **开源模型的质量与可获得性大幅提升**：普通科学家就能用上产出过竞赛冠军、皮摩尔级（picomolar，10⁻¹² mol/L，极强结合）结合结果的工具；
2. **基础设施更易得**：比特币矿潮退去后 GPU 好买了，一张够强的显卡插进桌下主机就能本地跑全部流程，避开高昂的云计算开销。

![de novo 设计为何此刻爆发：开源模型 + 消费级 GPU 两大条件汇流](assets/De%20Novo%20Protein%20Design%20in%20Practice：%20What's%20Actually%20Working（with%20Michael%20Holden）/00276.webp)

### 1.2 它是互补位，不是取代者

这套工作流的定位不是"自成支柱"，而是与实验室已有能力互补（[【跳转到 05:26】](https://www.youtube.com/watch?v=cVmGeFGsVA0&t=326)）：很多公司本来就在做噬菌体展示或酵母展示，上下游检测能力是现成的；团队也可能在做经典杂交瘤（hybridoma，杂交瘤细胞产单抗的经典技术）campaign——计算设计同样能补位，因为拿抗原难、筛鼠源抗体带偏差是老痛点。于是它提供了**第三条**产出"能结合、有生物学意义的新序列"的路径。

### 1.3 大家都在设计什么

Leo 的问题很直接：大家都在设计什么？Michael 的答案是"能做的分子类型已经铺开"（[【跳转到 06:41】](https://www.youtube.com/watch?v=cVmGeFGsVA0&t=401)）：多肽、scFv（单链可变片段）、scFab，当然还有 VHH（纳米抗体）及其人源化；客户横跨农业生物、制药、生物科技、化妆品等行业——应用面的广度和深度才刚刚开垦（[【跳转到 07:06】](https://www.youtube.com/watch?v=cVmGeFGsVA0&t=426)）。

![应用面横跨农业、制药、生物科技、化妆品等多个行业](assets/De%20Novo%20Protein%20Design%20in%20Practice：%20What's%20Actually%20Working（with%20Michael%20Holden）/00451.webp)

## 二、从业者的来路：从 Word 里手改序列到 AI 设计

### 2.1 再生元岁月与酶项目

Michael 是经典蛋白质化学出身：在再生元做首席科学家兼组长时，基于 UniProt 序列和 PDB 结构**在 Word 里手改序列**，再用 ExPASy 等生信工具预判表达量与蛋白质量，然后转化/转染表达——先后做过神经退行性疾病蛋白、药用蛋白、多特异性 ADC（抗体偶联药物）与连接子技术（[【跳转到 09:11】](https://www.youtube.com/watch?v=cVmGeFGsVA0&t=551)）。

他深知小公司的难处：需求很定制，却没有资源做抗原、跑整套杂交瘤 campaign，项目只能搁置。除 binder 外，另一大应用是**酶**——这正是他热情的起点（[【跳转到 10:01】](https://www.youtube.com/watch?v=cVmGeFGsVA0&t=601)）：在再生元做酶项目时，他想要一条与在研酶功能相同的新序列，于是改造了一个开源模型来用。

![从酶项目起步：在再生元用改造的开源模型设计新酶序列](assets/De%20Novo%20Protein%20Design%20in%20Practice：%20What's%20Actually%20Working（with%20Michael%20Holden）/00626.webp)

### 2.2 旧笔记本上的第一套流程

第一套完整流程跑在一台 **2016 年的旧笔记本**上——自带显卡很弱，但勉强够用。整套东西演示给管理层后，有人感兴趣也有人不感冒，但它点燃了一个信念：GitHub 上的免费工具真的能落地（[【跳转到 10:51】](https://www.youtube.com/watch?v=cVmGeFGsVA0&t=651)）。

### 2.3 企业级成果不需要企业级基础设施

Michael 最近去电子产品卖场买了几台高端游戏主机，配置是特意选的：既吃满机器潜力，又**不必花两万美元买二手 A100**（[【跳转到 11:16】](https://www.youtube.com/watch?v=cVmGeFGsVA0&t=676)）。用开源模型本地跑、成本极低；若再配上湿实验平台，一次就能筛几百到几千条（取决于平台通量）。真正的机会是**把反馈闭环接起来**：把 RANOMICS 实验室的实验数据和你的 in silico 设计对接，从数据中学习，让下一轮设计更准（[【跳转到 11:41】](https://www.youtube.com/watch?v=cVmGeFGsVA0&t=701)）。

![本地硬件起步：游戏主机级算力即可跑设计，不必买两万美元的二手 A100](assets/De%20Novo%20Protein%20Design%20in%20Practice：%20What's%20Actually%20Working（with%20Michael%20Holden）/00676.webp)

## 三、迭代筛选的第一问：数万条候选怎么筛

### 3.1 序列无限，"测什么、扔什么"才是新前沿

Leo 点出行业现状：电脑产序列几乎无限，大家还在卷模型、提命中率，但**行业当下真正的关键正是"测什么、扔什么"**（[【跳转到 12:31】](https://www.youtube.com/watch?v=cVmGeFGsVA0&t=751)）。如果你生成了 5 万、10 万条序列，怎么筛？

![数万条候选怎么筛：测什么、扔什么才是行业新前沿](assets/De%20Novo%20Protein%20Design%20in%20Practice：%20What's%20Actually%20Working（with%20Michael%20Holden）/00751.webp)

### 3.2 只有两条路：96 孔板+BLI vs 展示通筛

路其实只有两条（[【跳转到 12:56】](https://www.youtube.com/watch?v=cVmGeFGsVA0&t=776)）：

1. **96 孔板 + 无细胞表达 + BLI**：非常适合 mini protein 和 VHH——如今技术最擅长的就是这种尺寸的小蛋白；结合的再进 SPR 深测 kon/koff 动力学；
2. **噬菌体/酵母展示大规模通筛**：把生成的全部序列丢进展示库，一网打尽。

### 3.3 什么时候只筛 100 条：高置信就少筛

5 万条设计里只挑 100 条进实验，什么时候成立？Leo 的答案（也是团队共识）：**靶标已被充分验证、结构信息丰富，且设计本身高置信**——比如只是把别的蛋白的 CDR（互补决定区）嫁接到支架上做小改动——前置知识足够多，就可以少筛，命中数也更高（[【跳转到 14:11】](https://www.youtube.com/watch?v=cVmGeFGsVA0&t=851)）。

### 3.4 什么时候必须大筛：表位越"新"，未知越多

反过来，做更新颖的东西时——"新"可以新到表位本身：哪怕某蛋白已解出一千个晶体结构、有一千种抗体针对它，只要你瞄准的是**定制表位、结合模式未知**，实验上的未知量就大，必须大量测试筛选——这正是大规模展示系统的用武之地（[【跳转到 15:01】](https://www.youtube.com/watch?v=cVmGeFGsVA0&t=901)）。

### 3.5 噬菌体 vs 酵母展示：通量错配与单价亲和力

Leo 用三个要点讲清两大平台的选择逻辑（[【跳转到 16:16】](https://www.youtube.com/watch?v=cVmGeFGsVA0&t=976)）：

- **噬菌体展示**：基于最简单的生物，通量最高（10¹⁰~10¹¹），但这个通量与计算设计的输出（一次最多约 10 万条）是**错配**的——杀鸡用牛刀；
- **噬菌体的真本事**：给出**真实的单价（monovalent）亲和力**——一条噬菌体只展示一个蛋白拷贝，没有亲合力（avidity，多价同时结合带来的"虚高"）效应，这点常被忘记。畅销十年的修美乐（Humira）就是噬菌体展示抗体，技术久经考验；
- **酵母展示**：通量数量级与计算设计输出**在同一量级**，匹配度好得多；酵母同样能展示 VHH 等多种蛋白。现在很多人做 Fab，但完整 Fab 序列的计算设计还不成熟。

![噬菌体展示与酵母展示：通量与计算设计输出的数量级错配](assets/De%20Novo%20Protein%20Design%20in%20Practice：%20What's%20Actually%20Working（with%20Michael%20Holden）/01001.webp)

Michael 补充了一个进阶细节：BoltzGen 这类模型已经能生成**单链 Fab**——轻重链可变区连同恒定区一起建出来；但很多模型只在两条链之间放一个**通用连接子**，无法预先指定你要的连接子（[【跳转到 18:21】](https://www.youtube.com/watch?v=cVmGeFGsVA0&t=1101)）。想要刚性连接子把两个结构域撑成相对姿态（适合双价设计），或要柔性 GS 连接子让两者一起扣住同一个 GPCR 复合物，都得自己优化长度——模型如何产出这些仍有工作要做。

### 3.6 模型输出仍要理性把关

这一条是全场的"安全带"：**这些是模型输出，拿到后仍要按蛋白设计的老规矩理性把关**——表面疏水斑块合理吗？送 DNA 核心设施或 GenScript 之前用过的那套验证原则和工具，对 in silico 设计同样适用（[【跳转到 19:36】](https://www.youtube.com/watch?v=cVmGeFGsVA0&t=1176)）。大家都要接受"命中率不是 100%、系统不完美"的现实——而且坦白讲，噬菌体、酵母、杂交瘤同样不完美：杂交瘤 campaign 出来的并非个个成药，有的要在噬菌体里再盘几年（[【跳转到 20:26】](https://www.youtube.com/watch?v=cVmGeFGsVA0&t=1226)）。把计算设计放进管线里、与互补技术占同样的位置就好。

![命中率不是 100%：模型输出与杂交瘤一样需要后续优化流程](assets/De%20Novo%20Protein%20Design%20in%20Practice：%20What's%20Actually%20Working（with%20Michael%20Holden）/01226.webp)

### 3.7 酵母展示的配套：流式 + NGS + 阴性数据

酵母展示最妙的是真核折叠质量，再耦合流式细胞术：可同时测多个靶标——on-target、off-target 与相似靶标用不同荧光基团区分；再配上流程化的 NGS（二代测序）——载体设计时就定好 index 与 barcode 位置，PCR 测序即得海量数据（[【跳转到 21:16】](https://www.youtube.com/watch?v=cVmGeFGsVA0&t=1276)）。关键升级在于：如今不仅能测**结合的**，也能测**不结合的**——这对训练模型同样重要，因为当前基础数据集严重偏科：几乎全是阳性数据（[【跳转到 21:41】](https://www.youtube.com/watch?v=cVmGeFGsVA0&t=1301)）。

## 四、模型怎么选：多模型并行与统一打分

### 4.1 差异在架构与训练数据

"AlphaFold、Rosetta、BindCraft……这些工具有何区别？"Michael 的回答：差异主要在**技术架构与训练数据**（[【跳转到 22:31】](https://www.youtube.com/watch?v=cVmGeFGsVA0&t=1351)）。做扩散模型，公开训练数据就是几万个 PDB 结构；做 Transformer 可以训练在序列上，UniRef 里有数百万条。目前"最低垂的果实"是保证**能结合**——训练数据给的就是 CDR 与 partner 强结合时的精确取向与行为；而**阴性数据**——明明存在于产出这些结果的实验室——从未被报道。

### 4.2 外推性有限 → 多模型采样不同角落

这些模型的外推能力有限：训练分布里见过的可能很好，更新颖的可能就不行；而且训练集到底用了哪些蛋白并不总是公开（[【跳转到 24:11】](https://www.youtube.com/watch?v=cVmGeFGsVA0&t=1451)）。所以 Michael 的做法是**多模型并用**：这些模型都是 MIT 许可证，用多个模型各生成几千条序列，用同一套标准统一打分，再叠加其他 in silico 生信检测，从中挑高置信的输出（[【跳转到 25:01】](https://www.youtube.com/watch?v=cVmGeFGsVA0&t=1501)）。

### 4.3 BoltzGen 很方便，但只采样一个角落

单押一个模型的问题：它只能采样抗原结合空间的一个角落——训练数据是某个子集，架构本身也给扩散输出加了约束，于是输出被它的偏好所偏置；而 RFdiffusion、ProteinMPNN 的输出偏置可能不同，在某些抗原条件下有利、某些条件下不利（[【跳转到 25:26】](https://www.youtube.com/watch?v=cVmGeFGsVA0&t=1526)）。这些边界在哪，目前还没有严格且公开的定论——很多人正在用实验去搞清楚。

![单一模型只采样设计空间的一个角落：多模型并行、统一打分](assets/De%20Novo%20Protein%20Design%20in%20Practice：%20What's%20Actually%20Working（with%20Michael%20Holden）/01526.webp)

## 五、置信分数的边界：能过滤"不可能"，不能预测"多好"

### 5.1 700 万条亲和力 vs ipTM/ipSAE：几乎零相关

观众之问："你偏好的置信度指标与亲和力有相关性吗？"Leo 的答案：**没有**（[【跳转到 26:41】](https://www.youtube.com/watch?v=cVmGeFGsVA0&t=1601)）。原因：现有模型都是按"结构上结合/不结合"训练的，从未被训练去回答"结合得多好"。证据是 AlphaFold 团队上周发的博文：内部数据库有**超过 700 万条实测蛋白结合亲和力**，拿去与 ipTM、ipSAE 等分数对比——**几乎零相关**（[【跳转到 27:31】](https://www.youtube.com/watch?v=cVmGeFGsVA0&t=1651)）。他们发现这些分数作为**阴性过滤器**倒是很好用：ipTM/ipSAE 低的基本可以放弃；但分数高也依然不能预测亲和力。

![AlphaFold 团队 700 万条亲和力数据：与 ipTM/ipSAE 几乎零相关，只能当阴性过滤器](assets/De%20Novo%20Protein%20Design%20in%20Practice：%20What's%20Actually%20Working（with%20Michael%20Holden）/01651.webp)

### 5.2 双刃剑：阴性过滤器与"错杀"风险

Michael 补充这是把双刃剑（[【跳转到 28:46】](https://www.youtube.com/watch?v=cVmGeFGsVA0&t=1726)）：ipSAE、pLDDT、ipTM 与真实结合并非线性关系——有一定相关性、适合做阴性过滤器；但你也可能**把标量指标差的好设计错杀**：可能是那次运行的随机种子不巧，也可能是训练数据不够全面——实验室里看得到的好结合，in silico 里看不到。

### 5.3 激进多指标打分与前沿数据缺口

实操建议很明确（[【跳转到 30:01】](https://www.youtube.com/watch?v=cVmGeFGsVA0&t=1801)）：**计算筛选很便宜，远比进实验室便宜——在做任何 DNA 合成之前，应该激进地用尽可能多的指标打分**：Boltz-2 能给不少有用输出；用法巧妙的话还能直接用 BoltzGen 打分；Rosetta、分子动力学（MD）等手段都可用。但眼下语言模型侧最常见的三个结合指标——ipSAE、ipTM、confidence score——与结合的相关性并非百分之百。

这促使 Michael 在丹佛大学做访问学者，专门研究这个问题：生成 5 万~10 万个数据点，全部回头对照 in silico 分数，看相关到底有多好（[【跳转到 30:51】](https://www.youtube.com/watch?v=cVmGeFGsVA0&t=1851)）——**当初想要"能结合"，就用会结合的数据训练了；现在要区分结合强弱、改进支架，这些数据还不存在**。药企手里有大数据库但既不公开也不授权；圈外人可以与 CRO 合作生成高置信的大数据集，再训练一个算力要求不高、却能区分强/弱结合的 Transformer。

![下一步前沿：生成 5~10 万实测数据点，回头校准 in silico 指标](assets/De%20Novo%20Protein%20Design%20in%20Practice：%20What's%20Actually%20Working（with%20Michael%20Holden）/01851.webp)

## 六、跑起来的硬件与工程：从一块显卡到夜间自动化

### 6.1 16GB 显存起步，芯片代际也重要

观众问"家里电脑最低要什么 GPU"。Michael 跑的是一支分布式 GPU 集群——大多是 Nvidia 芯片的 Windows 主机、自己装了 Linux。最低要求约 **16GB 显存**：一块 RTX 5060 Ti 插进现代主板，一千美元上下（[【跳转到 32:31】](https://www.youtube.com/watch?v=cVmGeFGsVA0&t=1951)）。除了容量，**芯片代际**也重要：最新的 Blackwell 架构推理更快——他做过对照实验，租一张 A100（大家心中的"推理猛兽"）与 Blackwell 同题对跑，在非虚拟化工作流下 Blackwell 明显更快；生成几千个设计时，几秒半分钟的差距就是墙钟时间的大头（[【跳转到 33:46】](https://www.youtube.com/watch?v=cVmGeFGsVA0&t=2026)）。

### 6.2 统一内存路线：Mac 反而更快

现在很流行用统一内存机器做推理：Apple 自研芯片推理很强；Nvidia 的 DGX Spark 也是台不错的推理机，但**同样显存下 Mac 通常推理更快**——芯片设计方式使然（[【跳转到 35:01】](https://www.youtube.com/watch?v=cVmGeFGsVA0&t=2101)）。一台 128GB 统一内存的顶配 MacBook Pro 相当能打，本场聊的所有模型（到 BindCraft 为止）都能跑。唯一问题：散热不如正经显卡，统一内存一热就降频——得一边管温度一边管显存。

![统一内存推理：同显存下 Mac 通常快于 DGX Spark，但散热是短板](assets/De%20Novo%20Protein%20Design%20in%20Practice：%20What's%20Actually%20Working（with%20Michael%20Holden）/02101.webp)

### 6.3 YAML → Docker → 云上并行

Leo 分享了 RANOMICS 的起步经验：先用云实例（Google Cloud、AWS 起步很划算），关键是把实例配对、Python 库对齐。而一旦环境就绪，很多模型基本只需要一个 **YAML 文件**——靶标是谁、热点在哪、哪些区域不许碰，全写在里面，然后让机器自己转（[【跳转到 36:41】](https://www.youtube.com/watch?v=cVmGeFGsVA0&t=2201)）。Michael 的工程化建议：把依赖装齐、连同模型写进 Dockerfile，推上 DockerHub，再到任意云上快速部署；先本地冒烟测试，就绪后在 A100 或 B100 上并行跑多个容器，几天之内把所有设计跑完（[【跳转到 37:31】](https://www.youtube.com/watch?v=cVmGeFGsVA0&t=2251)）。

![从 YAML 到 Docker 到云端并行：一套可复用的部署路径](assets/De%20Novo%20Protein%20Design%20in%20Practice：%20What's%20Actually%20Working（with%20Michael%20Holden）/02276.webp)

### 6.4 AI 智能体已经在接管夜间班表

Leo 提到 Adaptyv 即将举办"人类 vs AI 智能体"蛋白设计竞赛；Michael 则分享了自己的真实工作流（[【跳转到 40:01】](https://www.youtube.com/watch?v=cVmGeFGsVA0&t=2401)）：他给 bot 发 Telegram 指令——"看看 Redis 队列还剩什么；低于 3 个时（约好凌晨三点会发生，那时我在睡觉）——拿出研究计划，往 Redis 提交一个 BoltzGen campaign，把 GPU 占满"。这已经相当有效：从文献里挖表位、配好 YAML、扔进队列、两台机器自动接活。已有公司在做科学向 AI 智能体（如 Potato AI）；他不认为它抢得走工作，但它可以是位**能在下班时间干活的好"科研助理"**。

### 6.5 需要会写代码吗

简短答案：早期规划不需要——已有很多公司在算法之上做了网页封装（如 Cameron、BioLoom、Arctoris 等），点几下就能出设计；但代价是失去全部自定义能力。Michael 自己用 **Claude Code** 写代码：代码库约两三万行、十月起步，已进生产环境、非常稳健（[【跳转到 42:06】](https://www.youtube.com/watch?v=cVmGeFGsVA0&t=2526)）——把编码当作学习机会，而不是入行门槛。

## 七、实验伪影与"结合 ≠ 功能"

### 7.1 陷阱一：过度依赖标量指标

最常见的陷阱就是**过度依赖标量指标**。评判蛋白的手段就那么几个，不得不用，但要保持怀疑：有结构生物学朋友的话，请他来看看残基堆积是否真实；你不会盲信每一个 B 细胞都在产好抗体，同理也不该盲信每个模型的输出（[【跳转到 45:23】](https://www.youtube.com/watch?v=cVmGeFGsVA0&t=2723)）。

### 7.2 伪影一：增溶标签抬高表达量

做大规模酵母展示想确认所有东西都表达时，有人会在末端加**增溶标签**（solubility tag）——染色时荧光很漂亮，VHH 表达看似很好；但等你把它作为独立蛋白生产、用更挑剔的大肠杆菌表达时，标签没了——你是不是人为抬高了表达量？酵母展示的荧光本来就是第一道表达量读数，而且它与下游稳定性、可制造性相关良好；一旦加了掩盖这一效应的东西，就成了实验伪影（[【跳转到 47:03】](https://www.youtube.com/watch?v=cVmGeFGsVA0&t=2823)）。

### 7.3 伪影二：酵母展示的平衡时间

酵母体系里你其实不知道多久达到平衡——它不像 SPR 那样干净地给出速率，你看到的是终点读数，而终点何时到达并不清楚：有人孵 1 小时、有人 2 小时；Michael 团队第一轮稳妥起见**过夜**，也可以倒推验证终点（[【跳转到 48:43】](https://www.youtube.com/watch?v=cVmGeFGsVA0&t=2923)）。

### 7.4 大头：结合 ≠ 功能

整场最重要的一句话：**结合 ≠ 功能（binding is not function）**（[【跳转到 49:08】](https://www.youtube.com/watch?v=cVmGeFGsVA0&t=2948)）。"能结合"不一定成药、不一定有活性、不一定特异——可能只是范德华塌缩（两个黏糊糊的东西贴在一起），或电荷相互作用（物理成立、生物学无关）。

Michael 给出实操展开（[【跳转到 50:23】](https://www.youtube.com/watch?v=cVmGeFGsVA0&t=3023)）：先按结合过滤（展示平台），对高置信结合者重组表达后测 kon/koff 与 KD；接下来**取决于目的**——做 ADC 要求快结合、极慢解离（让药被内吞）；若只是激活信号，快 on/off 或许无妨。然后构建**报告细胞**（reporter cells）做细胞水平实验——因为到那时你仍然只是"假设表位"：**结合在哪里直接决定生物学输出**。他举了两个教科书案例：HER2 上两个抗体结合在不同位置，结果完全不同；经典的 PD-1/PD-L1 抗体也一样——结合区域不同、输出不同（[【跳转到 51:13】](https://www.youtube.com/watch?v=cVmGeFGsVA0&t=3073)）。

![结合≠功能：同一靶标上结合位置不同，生物学输出完全不同](assets/De%20Novo%20Protein%20Design%20in%20Practice：%20What's%20Actually%20Working（with%20Michael%20Holden）/02973.webp)

## 八、酶 vs binder：两条不同的成熟度曲线

### 8.1 酶设计从 2021 年那波走来

观众问：设计酶 vs 设计 binder，算法到什么水平了？Michael：领域其实从酶起步，热度高峰大约在 2021 年前后（Baker 实验室那批论文），确实有被验证的工具（如塑料降解酶）；但你仍需构建大文库、做 in silico 验证，用配体对接、pose 分析等手段判断"这个酶真的可能干我想让它干的事吗"——活性位点会不会整个散开、被氧化（[【跳转到 52:28】](https://www.youtube.com/watch?v=cVmGeFGsVA0&t=3148)）。

![酶设计的门槛：大文库 + in silico 验证 + 酶学判断缺一不可](assets/De%20Novo%20Protein%20Design%20in%20Practice：%20What's%20Actually%20Working（with%20Michael%20Holden）/03198.webp)

### 8.2 RANOMICS 的聚合酶案例：定制 LLM 路线

Leo 分享了他们的判断：酶训练数据太少，通用开源模型成功率会很低；**为目标酶类定制数据集、训练专用 LLM** 命中率更高。两年前的聚合酶项目：先做深度扫描突变（deep scanning mutagenesis），把数据喂给定制 LLM，产出离野生型 7~10 个突变、纯随机采样永远碰不到的第二、三代酶，且活性更契合用途（[【跳转到 54:08】](https://www.youtube.com/watch?v=cVmGeFGsVA0&t=3248)）。如今 LLM 强到 96 孔板级别的数据就够起步，也已有伙伴提供定制训练服务。

### 8.3 RFdiffusion 3 与开放心态

Michael：事物总是一波一波来——RFdiffusion 3 的预印本快出来了，值得一看；de novo 酶设计还需打磨，但**优化 binder 与酶已经完全可行**。正如噬菌体展示会建议你绝不会想到的突变，模型同样如此——保持开放心态很重要（[【跳转到 55:23】](https://www.youtube.com/watch?v=cVmGeFGsVA0&t=3323)）。

### 8.4 ProteinMPNN 的"多聚 G/A"陷阱与调权

实操细节：Michael 用 ProteinMPNN 时常拿到大量"多聚 G/A"（甘氨酸/丙氨酸富集）输出——有一次 campaign 里 G/A 富集的蛋白占比高达 **30%**，等于花了大量算力生产垃圾（[【跳转到 56:38】](https://www.youtube.com/watch?v=cVmGeFGsVA0&t=3398)）。对策是**输入不同权重**改变其行为；SolubleMPNN 对 G/A 的偏置略小，但对 E（谷氨酸）与 S（丝氨酸）偏置更强，同样可能要调。这些工具本就设计得"通用"，输入要像 PCR assay 一样为具体实验定制；Tamarind 等在线平台可单独跑模型，想控制到极细粒度（锁定残基、只扩散某些区段、只优化 CDR 或只优化支架）还是得本地部署。

## 小结

- **迭代筛选的本质**是把 in silico 设计当作管线上游：多模型并行生成 → 统一多指标打分 → 按靶标信息量选筛选规模 → 实验数据回流训练，形成 lab-in-a-loop。
- **筛选规模由信息量决定**：高置信设计（CDR 嫁接、结构信息丰富）少筛；新表位、未知结合模式必须大筛。
- **平台匹配**：96 孔板+BLI 适合 mini protein/VHH 的高置信候选；酵母展示通量与计算设计同量级；噬菌体展示通量错配但给真单价亲和力（Humira 即例证）。
- **置信分数的边界**：ipTM/ipSAE 低→基本放弃；分数高≠高亲和力（700 万实测亲和力 vs 指标几乎零相关）。多指标激进打分、小心错杀。
- **模型选择**：多模型并行采样设计空间的不同角落，统一打分后再挑；单模型的输出带架构偏置。
- **结合 ≠ 功能**：结合位置决定生物学输出；ADC 要快 kon/慢 koff，功能要靠报告细胞验证。
- **实验伪影清单**：增溶标签抬高表达量、酵母平衡时间未知、过度信任标量指标。
- **硬件门槛**：16GB 显存起步（5060 Ti 级），Blackwell/统一内存更快，YAML→Docker→云端并行是标准路径。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| de novo 蛋白设计 | 不模仿天然蛋白，从零设计全新氨基酸序列 |
| ipTM / ipSAE | 结构预测模型对"界面"的置信分数；能当阴性过滤器，不能预测亲和力 |
| pLDDT | AlphaFold 类模型的逐残基置信度（0~100） |
| BLI / SPR | 生物层干涉/表面等离子共振：测结合与 kon/koff 动力学的仪器方法 |
| kon / koff / KD | 结合速率/解离速率/解离常数（亲和力） |
| 酵母展示 | 在酵母表面展示蛋白库，用流式分选的高通量筛选技术 |
| 噬菌体展示 | 用噬菌体展示蛋白库的筛选技术；通量 10¹⁰~10¹¹，天然单价 |
| 亲合力（avidity） | 多价同时结合带来的表观亲和力"虚高"效应 |
| 杂交瘤（hybridoma） | 经典单抗制备技术；拿抗原难、带免疫偏置 |
| hard negative | "看似该结合却没结合"的负样本，决策边界上的训练教材 |
| lab-in-a-loop | 设计→筛选→数据→再设计的闭环迭代 |
| mini protein / VHH | 小分子量结合蛋白 / 纳米抗体（单域抗体） |
| scFv / scFab | 单链可变片段 / 单链抗原结合片段（含恒定区） |
| ADC | 抗体偶联药物；常要求内吞（快 kon、慢 koff） |
| 增溶标签（solubility tag） | 表达时加的助溶尾段；会人为抬高酵母展示读数 |
| 报告细胞（reporter cells） | 携带信号读出的细胞实验体系，验证结合是否带来功能 |
