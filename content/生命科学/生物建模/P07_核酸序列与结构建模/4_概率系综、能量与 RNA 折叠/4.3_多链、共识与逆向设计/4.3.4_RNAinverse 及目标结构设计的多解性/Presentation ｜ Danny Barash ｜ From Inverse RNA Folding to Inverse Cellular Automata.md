# Presentation ｜ Danny Barash ｜ From Inverse RNA Folding to Inverse Cellular Automata

> 本文整理自 Danny Barash（本-古里安大学）在 Wolfram Institute 直播讲座，全长约 89 分钟。讲座分两半：前半讲**逆 RNA 折叠（inverse RNA folding）**——给定目标二级结构，设计会折叠成它的 RNA 序列，这正是 ViennaRNA 包中 `RNAinverse` 工具所解决的问题；后半讲他把同一套"逆问题"思想推广到 Stephen Wolfram 的元胞自动机生物进化最小模型上（inverse cellular automata）。全部内容以讲座字幕与幻灯片为据：[【跳转到开头】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=39)。

## 本讲要解决的核心问题（SCQA）

**背景**：RNA 的功能与其**二级结构**（碱基配对模式）密切相关。从序列出发预测结构——"正向折叠问题"——自 1980 年代起就有成熟工具：Mfold、ViennaRNA 的 RNAfold、RNAstructure，全都是"最小自由能 + 动态规划"这一套 [【跳转到 04:40】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=280)。

**冲突**：合成生物学要的往往是反方向：手里有一个目标二级结构，要**设计**出折叠成它的序列。长度为 n 的 RNA 有 4^n 种候选序列，暴力枚举不可行 [【跳转到 07:52】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=472)；而且"长得像"只是及格线——真正可用的设计还要热力学稳定、抗突变，甚至要能与 BLAST 这样的序列搜索工具配合，去自然界里"按图索骥"。

**疑问**：逆折叠（inverse folding，又叫 RNA design）到底怎么解？三十年间求解器走到了哪一步？这个"逆问题"的思想还能推广到哪儿去？

**回答（中心思想）**：逆折叠的解法谱系从 ViennaRNA 的 **RNAinverse**（1994，随机优化：随机兼容序列 → 分段随机突变 → 最小化"预测结构与目标结构"的距离，能量只作次级目标）出发，经蚁群、约束规划、遗传算法，到如今的复制交换蒙特卡洛 DesiRNA，再到"用 Transformer 学 RNAfold、给蒙特卡洛更好起点"的预处理思路；Barash 组把问题**扩展**——允许非关键基序 ±1 个核苷酸、把热力学稳定性与突变鲁棒性写进目标函数——做成 incaRNAtion 网页服务器，并用"逆折叠作为 BLAST 前置"的管线寻找真核核糖开关；最后，"逆问题 + 中性网络"的思想被搬上元胞自动机：inverse cellular automata，尝试给生物进化建一个最小模型。一句话记住本讲：**正向问题一个序列对应一个结构，逆向问题一个结构对应海量序列——这正是设计空间的自由度所在。**

## 一、正向与反向：RNA 折叠的两副面孔

### 1.1 先分清三级表示：序列、二级结构、三维结构

RNA 是重要的生物大分子——mRNA 疫苗让它家喻户晓 [【跳转到 02:07】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=127)。它有三层表示：

- **一级结构**：A、C、G、U 四种核苷酸排成的序列；
- **三级结构**：折叠后每个原子在三维空间中的位置；
- **二级结构**：单链 RNA 自身回折、通过**沃森-克里克碱基配对**（A-U、C-G，以氢键结合）形成的配对模式。讲座强调：与蛋白质的二级结构相比，**RNA 的二级结构对功能的指示性强得多**。

二级结构里有一批反复出现的"基序（motif）"：发卡环（hairpin）、茎区（stem，一串连续碱基对）、凸起（bulge）、多分支环（multibranch loop）、内部环（internal loop），还有一种与三维结构挂钩的特殊结构——**假结（pseudoknot）** [【跳转到 03:55】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=235)。

### 1.2 正向问题：序列 → 结构，四十年的成熟工具

"给一段 RNA 序列，预测它的二级结构"是计算 RNA 生物学的经典问题，自 1970 年代起被持续投入 [【跳转到 04:40】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=280)。三代代表软件 [【跳转到 05:11】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=311)：

![三类经典 RNA 折叠软件：Zuker 的 Mfold、ViennaRNA 的 RNAfold、Rochester 的 RNAstructure，同为"最小自由能 + 动态规划"路线，结果相近](assets/Presentation%20｜%20Danny%20Barash%20｜%20From%20Inverse%20RNA%20Folding%20to%20Inverse%20Cellular%20Automata/00336.webp)

- **Zuker**（1980 年代，Mfold）→ **ViennaRNA 的 RNAfold**（1990 年代）→ **RNAstructure**（罗切斯特大学 David Mathews）；
- 三家算法骨架相同：**最小自由能（MFE）+ 动态规划**，能量参数来自生化实验测量（Mathews 很早即为 Mfold 与 RNAfold 测过参数）；
- 各有细节差异，但结果高度一致。

### 1.3 反向问题：目标结构 → 序列设计（= RNA design）

把箭头反过来：**给定一个二级结构，设计会折叠成它的 RNA 序列** [【跳转到 06:14】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=374)。这个问题有两个名字：因为方向反过来，叫**逆折叠**；因为本质是在"设计"，又叫 **RNA design**。起点是 1994 年 Hofacker 发布 ViennaRNA 包时附带的第一个解法；如今还有公民科学游戏 **Eterna**——玩家靠积累对"RNAfold 脾气"的直觉来解设计谜题，越会预判 RNAfold 输出的玩家，设计越准 [【跳转到 06:37】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=397)。

![逆问题的定义：从目标二级结构出发反向求序列；正向问题"一序列一结构"，反向问题"一结构多序列"](assets/Presentation%20｜%20Danny%20Barash%20｜%20From%20Inverse%20RNA%20Folding%20to%20Inverse%20Cellular%20Automata/00374.webp)

## 二、RNAinverse：第一个逆折叠算法（1994）

### 2.1 为什么不能暴力搜索：4^n 的组合爆炸

长度 n 的序列有 4^n 种可能——序列越长，搜索空间指数爆炸，逐一遍历不可行 [【跳转到 07:52】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=472)。所以逆折叠从第一天起就是"搜索 + 启发式"的问题。

### 2.2 随机优化三步走

ViennaRNA 内置的 **RNAinverse** 至今仍是最基础、使用最广的逆折叠算法 [【跳转到 08:15】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=495)。它的流程 [【跳转到 08:44】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=524)：

1. **随机起点**：生成一条与目标结构"兼容"（即碱基对位置都能配上对）的随机序列 S，把它拆成若干子序列；
2. **自适应突变**：对子序列做随机突变，目标是把"当前序列经 RNAfold 折出的预测结构"与"目标结构"的**距离**（主目标函数）一步步压小；
3. **能量兜底 + 重组装**：若找不到能降低结构距离的突变，就沿**能量**梯度走（次级目标函数）；最后把子序列重组装回完整序列。

反复迭代，直到预测结构与目标结构一致——这就是一个极简但完整的逆折叠求解器。

![RNAinverse 流程示意：随机兼容序列起步，分段自适应突变最小化结构距离；距离卡住时按能量梯度走](assets/Presentation%20｜%20Danny%20Barash%20｜%20From%20Inverse%20RNA%20Folding%20to%20Inverse%20Cellular%20Automata/00524.webp)

### 2.3 工程侧记：把 ViennaRNA 搬进 Wolfram 语言

讲座的夏季学校项目线也值得记录 [【跳转到 09:34】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=574)：

- 团队开始写 **paclet**（Wolfram 语言的软件包格式），把 ViennaRNA 的 RNAfold / RNAdistance / RNAinverse 封装进来：Christopher 在 Mac 上先跑通了 RNAfold，Christian 推进 Windows 等多平台，尚未完全成功 [【跳转到 09:59】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=599)；
- 讲座之前 Barash 在会议上与 ViennaRNA 团队和 Eterna 交流，对方愿意协助 API [【跳转到 10:49】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=649)；
- 目前 Wolfram 语言内置的只有 **Nussinov 1978** 的最大碱基配对算法——它不做能量最小化，所以实际研究者仍用 Mfold / RNAfold / RNAstructure [【跳转到 11:14】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=674)；
- 许可证是另一道坎：也许可以通过引入 RNAstructure 的许可来绕开 [【跳转到 12:04】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=724)。

## 三、求解器的三十年演进：从元启发式到蒙特卡洛，再到神经网络预处理

### 3.1 元启发式百花齐放（约 2015）

逆折叠求解器在 2015 年前后迎来一波爆发：蚁群设计、约束规划（牛津）、以及因幻灯片上 RNA 画得像怪物而得名的 **Frankenstein**（遗传算法 + 统计手段）[【跳转到 17:04】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=1024)。它们比 RNAinverse 更高效，但思路仍是"再发明一个更聪明的搜索算法"。

![2015 前后的逆折叠求解器生态：蚁群设计、约束规划与"Frankenstein"遗传算法](assets/Presentation%20｜%20Danny%20Barash%20｜%20From%20Inverse%20RNA%20Folding%20to%20Inverse%20Cellular%20Automata/01049.webp)

### 3.2 DesiRNA：当前最强的复制交换蒙特卡洛

Barash 认为当前最强的逆折叠求解器是 **DesiRNA**——Bujnicki 组的**复制交换蒙特卡洛**（replica exchange Monte Carlo）方法，讲座时点刚发表 [【跳转到 13:44】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=824)。直觉上，它让多个"温度"副本并行探索并互相交换，既能精细下降又能跳出局部极小——Eterna 里最难的挑战，它能在 24 小时内解掉。

### 3.3 Transformer 预处理：不解题，只给好起点

Barash 组在夏季学校的方案是给蒙特卡洛加一个**神经网络前置** [【跳转到 12:54】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=774)：

- 用海量"序列 → RNAfold 预测结构"数据训练一个 **encoder-decoder Transformer**，等于让它"学会 RNAfold"；
- 推理时，模型直接生成比随机猜测好得多的**起点序列**，再交给蒙特卡洛求解器精修 [【跳转到 13:44】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=824)；
- 它**不直接解决**逆折叠问题，但能把收敛时间大幅缩短——缩短多少取决于训练质量：生手带队收益有限，像导师 Geoffrey 这样的熟手带队会有质的差别 [【跳转到 14:59】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=899)。

![Transformer 预处理 + DesiRNA：神经网络先生成高质量起点序列，复制交换蒙特卡洛负责精修](assets/Presentation%20｜%20Danny%20Barash%20｜%20From%20Inverse%20RNA%20Folding%20to%20Inverse%20Cellular%20Automata/00824.webp)

他们用 Eterna 的"shooting star"（流星）挑战做验证——这是现实中自然界不会出现的花式结构，只有资深玩家敢尝试 [【跳转到 15:49】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=949)。法国合作者、博弈搜索专家 **Tristan Cazenave**（曾为 Barash 参与主编的 RNA design 书撰稿）给出了概念验证，虽然还没做到"在 Wolfram 语言里完全解决"，但方向可行 [【跳转到 16:14】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=974)。

## 四、扩展逆折叠：允许"差不多像"，换来可设计性

### 4.1 动机：生物学家不必逐基序较真

Barash 组的独特选择：不去再发明一个更快的求解器，而是**扩展问题本身** [【跳转到 17:54】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=1074)。现实里，合成生物学家想要的 RNA 结构中，某些基序多一个或少一个核苷酸无伤大雅——离功能位点远、不重要的基序，何必逼求解器逐核苷酸严格服从？允许"差不多像"，就把省下的自由度拿去满足更重要的约束 [【跳转到 18:19】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=1099)。

### 4.2 两个非结构约束：稳定 + 鲁棒

有了弹性，就能把"结构像不像"之外的要求写进目标函数 [【跳转到 18:44】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=1124)：

- **热力学稳定性**：基态自由能足够低，且基态能量附近几乎没有备选二级结构（不容易被热运动"抖"进别的构象）；
- **突变鲁棒性**：RNA 在单点突变后仍保持同一二级结构的能力。

讲座埋了个伏笔：自然 RNA 经数十亿年进化淘汰，恰恰既热力学稳定、又突变鲁棒——这个概念在下半场讲元胞自动机进化模型时还会回来 [【跳转到 19:09】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=1149)。

### 4.3 表示：dot-bracket 与粗粒化树图

- **dot-bracket 记法**：由 ViennaRNA 发明——未配对核苷酸记 `.`，发生配对处记一对开合括号 `()` [【跳转到 20:24】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=1224)；
- **粗粒化树图**：把环、茎抽象成树的节点。不同的二级结构，只要基序布局相同，就归并到同一棵树——这为"允许基序伸缩"提供了形式化语言 [【跳转到 21:14】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=1274)。

![dot-bracket 记法与粗粒化树图：不同碱基配对细节被归并到同一棵树，为"基序伸缩"提供形式化语言](assets/Presentation%20｜%20Danny%20Barash%20｜%20From%20Inverse%20RNA%20Folding%20to%20Inverse%20Cellular%20Automata/01274.webp)

### 4.4 求解：模拟退火 + 核苷酸前瞻

目标函数是可加的：结构距离 + 稳定性 + 鲁棒性（+ 可选的基序项）。求解用**模拟退火**（允许短期变差以跳出局部极小的随机搜索）配 **n 核苷酸前瞻局部搜索**（一次评估往后 n 个位置的突变方案）[【跳转到 22:04】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=1324)。

### 4.5 效果：microRNA-146 案例与"严格模式"

用真实的 microRNA-146 做对比：与 Vienna 的 RNAinverse 相比，扩展逆折叠能把内部环"上移"到更有利的位置，再叠加非结构约束后定量结果更好（随机优化要多次运行取统计）[【跳转到 24:09】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=1449)。

![microRNA-146 对比实验：扩展逆折叠（允许基序伸缩 + 非结构约束）相比 Vienna RNAinverse 做得更好](assets/Presentation%20｜%20Danny%20Barash%20｜%20From%20Inverse%20RNA%20Folding%20to%20Inverse%20Cellular%20Automata/01474.webp)

弹性与严格可以兼得：若生物学家声明"这个基序对我在实验室的问题至关重要"，就在目标函数里加一个高权重项，令**选中的基序严格服从输入结构、其余基序仍可偏离** [【跳转到 25:24】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=1524)。整套方法做成了网页服务器 **incaRNAtion**（与法国、加拿大合作者共建）：用户提交目标二级结构，服务器返回柔性设计；这是 Barash 此前一位博士生的成果 [【跳转到 27:29】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=1649)。

![incaRNAtion 网页服务器：输入目标二级结构，得到带稳定性/鲁棒性约束的柔性设计](assets/Presentation%20｜%20Danny%20Barash%20｜%20From%20Inverse%20RNA%20Folding%20to%20Inverse%20Cellular%20Automata/01674.webp)

## 五、用逆折叠做"结构感知搜索"：寻找真核核糖开关

### 5.1 为什么要拿逆折叠配 BLAST

设计不止于设计本身——Barash 组真正想要的是**发现新的 RNA 调控元件** [【跳转到 28:19】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=1699)。经典工具 **BLAST**（Basic Local Alignment Search Tool，基本局部比对搜索工具）的工作方式：从鸟的 DNA 里取一段重要子序列，到鱼的整个基因组里找它落在哪儿——本质是动态规划做局部比对 [【跳转到 29:09】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=1749)。BLAST 是序列级搜索，威力强大，但会漏掉"结构保守、序列漂移"的实例；RNA 界的结构感知搜索工具是 Infernal（哈佛 Sean Eddy 开发）[【跳转到 30:24】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=1824)。Barash 的思路：**用逆折叠做预处理，把结构信息注入序列搜索**。

![BLAST：从鸟基因组取子序列，在鱼全基因组中做局部比对定位——序列级搜索会漏掉结构保守的实例](assets/Presentation%20｜%20Danny%20Barash%20｜%20From%20Inverse%20RNA%20Folding%20to%20Inverse%20Cellular%20Automata/01774.webp)

### 5.2 背景一页：RNA 世界与核糖开关

中心法则之外还有"**RNA 世界假说**"——生命的一切从 RNA 开始：DNA 只是组分几乎相同（U 换成 T）的近亲，而 RNA 自带催化能力（核酶，Cech 与 Altman 因此获第一个与 RNA 有关的诺贝尔奖）[【跳转到 30:49】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=1849)[【跳转到 32:04】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=1924)。microRNA 与基因沉默的故事同构：先有人工"反义靶向"设计（让短 RNA 钩住 mRNA 阻断它），后来才发现自然界早已在用同样机制——又一个诺贝尔奖 [【跳转到 33:04】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=1984)。

**核糖开关（riboswitch）**由 Breaker（耶鲁）于 2002 年发现 [【跳转到 32:29】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=1949)：mRNA 上的一段结构能感应小分子配体并发生变构，从而开关基因表达。讲座用细菌维生素 B1 合成举例 [【跳转到 34:33】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=2073)：B1 的衍生物 TPP（焦磷酸硫胺素）在培养基中过量时，会结合适体（aptamer，感应配体的结构域），触发从"终止子"到"抗终止子"的剧烈构象切换。

![核糖开关机制示意：TPP 结合适体后，终止子/抗终止子之间发生剧烈构象切换](assets/Presentation%20｜%20Danny%20Barash%20｜%20From%20Inverse%20RNA%20Folding%20to%20Inverse%20Cellular%20Automata/02098.webp)

### 5.3 管线：BLAST 游走 → 扩展逆折叠捡回来

挑战在于分布：核糖开关在原核细菌里遍地都是，**真核生物里却几乎一个都没找到**——大家相信存在，但没人够得着 [【跳转到 35:37】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=2137)。检测手段方面，Breaker 实验室拿过专利的 sequence sniffer（模式匹配）找到过最早的真核候选，如今最强的是 Infernal [【跳转到 36:27】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=2187)。

Barash 组的搜索管线 [【跳转到 37:09】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=2229)：

1. 从一个众所周知的**原核**核糖开关出发，不断做点突变，每步都过 BLAST——它能找到序列相近的细菌同源物；
2. 一路突变，直到 BLAST 返回空——序列层面的线索断了；
3. 此时启动**扩展逆折叠**：进化中"结构保守、序列漂移"（数十亿年里突变可以累积很多，结构却保住了），所以在序列空间的**远处**找回"结构与起点几乎相同"的序列，就是别人没发现的候选 [【跳转到 37:34】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=2254)。

先在细菌内部验证方法正确，再到真菌等高等生物中找候选 [【跳转到 38:49】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=2329)；实验者要求"要家族、不要单点"，于是又有从 RNA 家族数据库出发、经逆折叠求解器与 GUI 批量生成候选家族的完整管线 [【跳转到 39:39】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=2379)。

![真核核糖开关搜索管线：BLAST 游走到无候选后，用扩展逆折叠在序列空间远处找回同结构序列，并生成家族](assets/Presentation%20｜%20Danny%20Barash%20｜%20From%20Inverse%20RNA%20Folding%20to%20Inverse%20Cellular%20Automata/02254.webp)

### 5.4 实验验证：inline probing 初步信号

真菌候选已送进实验室：波士顿学院的实验合作者用最简单的 **inline probing**（放射性标记）试了多种配体——在 ATP 泳道里出现了"不该亮却亮了"的条带 [【跳转到 40:56】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=2456)。若真菌核糖开关最终被确证，可能是 RNA 调控领域的一次突破；当然也可能是假阳性 [【跳转到 41:56】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=2516)。计算部分已完成，现在球在实验侧：合作、写基金、等湿实验结果。

## 六、从逆折叠到逆元胞自动机：给进化建一个最小模型

### 6.1 Wolfram 的最小进化模型与适应度高原

下半场换赛道：解**元胞自动机的逆问题**，来研究生物进化 [【跳转到 44:21】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=2661)。Stephen Wolfram 在讲座前一年提出用元胞自动机构造"生物进化及其他适应过程的最小模型"。横轴是累计突变步数，纵轴是规则达到的**最大寿命**（适应度）[【跳转到 44:50】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=2690)。曲线上出现大片**适应度高原**——大量突变不改变适应度（适合度中性突变），适应度相同的规则之间可以互相"游"过去。

![Wolfram 最小进化模型：突变步数 vs 最大寿命曲线，出现大片适应度高原](assets/Presentation%20｜%20Danny%20Barash%20｜%20From%20Inverse%20RNA%20Folding%20to%20Inverse%20Cellular%20Automata/02690.webp)

### 6.2 中性网络：一个来自 RNA 折叠的概念

**中性网络（neutral network）**：由点突变相连、适应度等价的序列（或规则）集合，可视作适合度地貌上的平原 [【跳转到 46:55】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=2815)。中性进化中，基因可以在网络里随机游走、穿越序列/规则空间——这对鲁棒性与可进化性都有直接后果 [【跳转到 47:20】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=2840)。这两个概念不依赖具体模型，是进化生物学的基本概念；突变鲁棒性在 RNA 折叠与逆折叠语境里已经出现过，而可进化性指"通过自然选择进行适应性进化的能力" [【跳转到 48:10】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=2890)。高原不是死水：在大中性网络里游走，是在为跳向更高的适应度峰积蓄突变——大网络对可进化性与鲁棒性都是利好。

这个概念 Barash 正是从 RNA 折叠学来的：1990 年代 ViennaRNA 组有一系列论文把 RNA 折叠当作生物进化的模型。里程碑是 Schuster、Fontana、Stadler、Hofacker 1994 年的《From sequences to shape and back》——第一件事就是用 Vienna 的逆折叠枚举"折叠成同一结构"的全部序列，以定位并研究中性网络；"中性路径网络贯通整个序列空间"这一事实，对分子进化乃至实验室进化研究都有深远影响 [【跳转到 49:00】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=2940)。

![Schuster 等 1994《From sequences to shape and back》：用 Vienna 逆折叠枚举同结构序列，定位 RNA 中性网络](assets/Presentation%20｜%20Danny%20Barash%20｜%20From%20Inverse%20RNA%20Folding%20to%20Inverse%20Cellular%20Automata/02940.webp)

Fontana 在学生会闲聊时给过一个好类比：中性网络有大小之分，就像欧洲的国家——法国很大，摩纳哥很小；网络的**直径**对表型多样性至关重要，网络拓扑决定种群动力学、进而影响鲁棒性的进化，创新能力则取决于基因型在网络中的位置 [【跳转到 51:55】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=3115)。把这些量（如网络直径）量化测出来，就能检验最小进化模型到底捕获了多少真实进化的性质——可进化性、鲁棒性的进化、表型多样性、创新 [【跳转到 52:45】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=3165)。

### 6.3 逆元胞自动机想做什么

目标：在 Wolfram 语言里写一个**逆元胞自动机**程序——给定任意预设的目标适应度，找到能达它的规则，从而在最小进化模型上研究中性网络的性质 [【跳转到 49:50】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=2990)。

## 七、第一步：一次刻意"人工"的逆 CA 实验

### 7.1 设定：随机目标适应度 + 随机搜索

当前进度（报告者坦承还很初步）[【跳转到 53:35】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=3215)：随机生成目标适应度值；算法是随机的，所以多次运行、收集成功解；框架借助 AI agent 搭建。目前用的是 r=1、k=3 的元胞自动机加随机梯度下降——**并非** Wolfram 最小进化模型的规则与度量，只是一个刻意的人工示例 [【跳转到 55:15】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=3315)。

### 7.2 目标适应度 64：人工中性网络雏形

把目标适应度设为 64，运行 5000 次，展示其中 4 个成功解 [【跳转到 56:05】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=3365)：不同规则达到同一适应度，而输出模式截然不同——这已构成"人工中性网络"的雏形，说明框架能跑通；下一步是换上 Wolfram 模型的正确组件重做。

![人工逆 CA 实验：目标适应度 64、5000 次运行中的 4 个成功解——不同规则同适应度，构成人工中性网络雏形](assets/Presentation%20｜%20Danny%20Barash%20｜%20From%20Inverse%20RNA%20Folding%20to%20Inverse%20Cellular%20Automata/03365.webp)

### 7.3 卡点：未文档化的 Wolfram 函数

按 Wolfram 的最小进化模型，k=3、r=1 的规则每个有 52 种（讲座口径）可能的单点突变：缩短寿命或无限延长寿命的会被自然选择淘汰，延长或不改变寿命的才是值得留下继续进化的 [【跳转到 57:24】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=3444)。

而官方模型代码里有一批**尚未文档化**的函数：random rule mutation（对规则做随机突变）、test lifetime（测突变后的寿命）、rule mutation list（汇总被接受的突变规则）、rule mutation plot、custom style data [【跳转到 58:14】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=3494)。团队正在逆向工程这些命令，同时寻求官方支持：比如 random rule mutation 是不是规则的 8 位数字形式？它会不会枚举所有可达的突变？没有文档就只能靠猜——而这正是他们最想避免的 [【跳转到 59:29】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=3569)。Q&A 里 Wolfram 方承诺提供包含全部函数定义的笔记本，交流就此接上 [【跳转到 86:57】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=5217)。

![最小进化模型代码中未文档化的函数：random rule mutation、test lifetime 等，逆向工程完成后才能替换人工示例](assets/Presentation%20｜%20Danny%20Barash%20｜%20From%20Inverse%20RNA%20Folding%20to%20Inverse%20Cellular%20Automata/03519.webp)

### 7.4 教育联动：HEDA 高中生项目

这条研究线还与教育结合：以色列特拉维夫的天才高中生中心 HEDA——2024 年 12 月 Barash 上门推广 Mathematica 未果，却偶然结识一位 11 年级学生；该学生明年（12 年级）正把"逆元胞自动机"申报为 HEDA 项目，审批进行中。研究、科普与教育在这里接到了一起 [【跳转到 61:34】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=3694)。

## 八、Q&A 精华：RNA、DNA 与蛋白质折叠的边界

### 8.1 DNA 为什么"没什么可折叠"

观众问 RNA 与 DNA 折叠的区别：DNA 是双链配对成的"梯子"，盘成双螺旋，没有单链回折的"多余环"；RNA 是单链，自己折向自己 [【跳转到 66:34】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=3994)。A-U、C-G 之间是强氢键，此外还有较弱的 **wobble 配对**；DNA 折叠也"拉链式"地存在一些结构，但远不如 RNA 丰富。Mfold 与 RNAstructure 也支持按 DNA 参数做 DNA 折叠，只是做的人很少 [【跳转到 68:15】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=4095)。

### 8.2 蛋白质折叠为什么遥遥领先

蛋白质的二级结构（α 螺旋、β 折叠）不像 RNA 二级结构那样直接指示功能；蛋白质三级结构预测依赖海量实验数据、同源建模与机器学习，有 CASP 竞赛推动，AlphaFold 连年夺魁；而 RNA 实验数据稀缺—— AlphaFold 离可靠预测 RNA 三级结构还非常远 [【跳转到 71:35】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=4295)。核苷酸与氨基酸也是两套化学：核酸四种碱基自带氢键配对面，蛋白质 20 种氨基酸则没有这种"残基级配对"。

![Q&A：蛋白质结构预测有 CASP 竞赛与 AlphaFold 加持；RNA 三级结构因数据稀缺而远远落后](assets/Presentation%20｜%20Danny%20Barash%20｜%20From%20Inverse%20RNA%20Folding%20to%20Inverse%20Cellular%20Automata/04295.webp)

### 8.3 逆折叠的输入与约束

逆折叠的输入是"粗粒度"的图结构——只给环与茎的布局，不指定链长与环大小；链长、环尺寸、已知配体结合位点处的核苷酸等都可以作为**约束**插入（核糖开关项目就是这么做的）[【跳转到 76:10】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=4570)。

### 8.4 一个序列对应几个结构？

折叠是时间依赖过程，可能困在局部极小再挣脱；到达稳态后，每个序列对应**一个**最低能结构——这正是 Mfold/RNAfold/RNAstructure 这些动态规划折叠包给出的答案 [【跳转到 79:30】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=4770)。而逆问题正相反：一个目标结构对应**海量**可设计序列 [【跳转到 80:45】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=4845)。

### 8.5 单点突变会破坏结构吗

自然 RNA 突变鲁棒：单点突变大概率保结构，要多个突变才会改变它——细胞里的功能结构本来就该经得起扰动 [【跳转到 82:25】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=4945)。当然有例外：Barash 组也开发过专门寻找"单点突变引发整体构象重排"的工具（分子开关思路）；但就本例外部环里的单点突变，他判断结构不会变 [【跳转到 83:15】](https://www.youtube.com/watch?v=DMQOReMjbW4&t=4995)。

## 小结

- 逆折叠 = "目标二级结构 → 序列"的搜索问题；4^n 的组合爆炸使暴力不可行，随机优化是底线方案：**RNAinverse**（1994）= 随机兼容序列 + 分段自适应突变 + 结构距离主目标、能量次目标；
- 求解器三十年演进：蚁群 / 约束规划 / 遗传算法（Frankenstein）→ 复制交换蒙特卡洛（DesiRNA）→ "Transformer 学 RNAfold、给蒙特卡洛好起点"的预处理；Wolfram 语言侧的 paclet 封装仍在路上；
- Barash 组的扩展路线：非关键基序 ±1 核苷酸的柔性 + 热力学稳定性/突变鲁棒性写进目标函数 + 模拟退火与核苷酸前瞻求解 → **incaRNAtion** 网页服务器；关键基序可加高权重强制严格；
- 应用范式：逆折叠作为 BLAST 前置，把"结构保守、序列漂移"的进化假设变成可执行的搜索——真核核糖开关候选已进入 inline probing 实验验证，ATP 泳道已有初步信号；
- 思想外推：逆问题 + 中性网络搬上 Stephen Wolfram 的元胞自动机最小进化模型（inverse cellular automata）；目前处于人工示例阶段（目标适应度 64 的成功解构成人工中性网络），卡在未文档化 Wolfram 函数的逆向工程上；
- 一句话：**正向问题一对一，逆向问题一对多；结构比序列更耐突变**——这既是设计空间的来源，也是中性进化理论的直觉起点。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| 正向折叠问题 | 给序列预测二级结构：最小自由能 + 动态规划（Mfold / RNAfold / RNAstructure） |
| 逆折叠 / RNA design | 给目标二级结构设计序列；一个结构对应海量序列 |
| RNAinverse | ViennaRNA 的第一个逆折叠程序：随机优化，把预测结构"推"向目标结构 |
| dot-bracket 记法 | `.` 表未配对、`()` 表配对的二级结构文本表示 |
| 热力学稳定性 | 基态自由能低、基态附近几乎没有备选二级结构 |
| 突变鲁棒性 | 单点突变后仍保持同一二级结构的能力 |
| 中性网络 | 点突变相连、适应度等价的序列/规则集合，适合度地貌上的平原 |
| Eterna | 公民科学 RNA 设计游戏，玩家凭对 RNAfold 的直觉解设计谜题 |
| DesiRNA | Bujnicki 组的复制交换蒙特卡洛逆折叠求解器 |
| incaRNAtion | Barash 组的扩展逆折叠网页服务器（法国、加拿大合作） |
| 核糖开关（riboswitch） | 感应小分子配体后变构、从而调控基因表达的 RNA 元件 |
| Infernal | 结构感知的 RNA 同源搜索工具（Sean Eddy，哈佛） |
| BLAST | 基本局部比对搜索工具，序列级同源搜索 |
| 元胞自动机 | 离散格点上按局部规则迭代的计算模型；Wolfram 用它建生物进化最小模型 |
| CASP | 蛋白质结构预测全球竞赛，AlphaFold 的加冕地 |
