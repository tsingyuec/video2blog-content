# Kaggle Winners Walkthroughs： Novozymes Enzyme Stability Prediction with Muhammad Ahmed

> 来源视频：[Kaggle Winners Walkthroughs: Novozymes Enzyme Stability Prediction with Muhammad Ahmed](https://www.youtube.com/watch?v=nkGYtv--9AU)（YouTube，30 分 52 秒）。这是 Kaggle「Novozymes 酶稳定性预测」比赛亚军 Muhammad Ahmed 的获奖者分享会实录，由 Novozymes 生物信息与设计部主持。本文基于该视频的「图-字幕」演说稿整理，所有结论均出自视频画面与口播，内容可核查。

## 本讲要解决的核心问题（SCQA）

**背景**：工业酶要在高温等苛刻条件下工作，热稳定性（衡量指标之一就是熔解温度 Tm，蛋白在此温度下失去一半结构）直接决定改造方向。Novozymes 在 Kaggle 上发起「酶稳定性预测」比赛：给定一条野生型酶蛋白的 PDB 结构和它的数千个点突变序列，要求预测每个突变体的热稳定性排序。

**冲突**：测试集只有一条蛋白骨架上的突变，训练数据却是各种蛋白拼凑的"大杂烩"，训练/测试分布严重错位；公开榜与私有榜之间还出现"大洗牌"——大批高分选手在私有榜上跌落。

**疑问**：一个赛前完全没碰过蛋白质的机器学习工程师，怎么在三个月里搭出一套既高分又稳定的方法？

**回答（中心思想）**：亚军 Muhammad Ahmed 的答案是"物理能量法 + 机器学习"的多路集成——以 FoldX、Rosetta（含 FastRelax 松弛版）、ThermoNet 三大主力为骨架，辅以 AlphaFold2 突变体结构差分特征、pLDDT 逐残基代理、RaSP、SDM 等一打网络服务器与软件打分；集成与提交的取舍不只看公开榜分数，还盯住"疑似私有段（约第 500–1600 行）"的预测分布是否被扰动。他估计只用三大主力就能拿到公开榜约 53 的分数，而"物理方法贡献了其中三分之一到三分之二"。

## 一、比赛与选手：一场"外行逆袭"的稳定性预测

### 1.1 Novozymes 团队开场：你设计的正是我们在用的分子

连线由 Novozymes 生物信息与设计部（bioinformatics and design）主持。主持人 Joshua Salomon 自我介绍：他在诺维信做的是酶研究（enzyme research），主要方向是野生型酶发现（wild-type enzyme discovery），本次比赛的目标分子"也正是我们团队一直在尝试设计的分子之一"；团队共六位科学家，覆盖生物信息、野生型酶发现与蛋白工程 [【跳转到 00:10】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=10)、[【跳转到 01:19】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=79)。

![获奖者连线开场：Novozymes 生物信息与设计部主持人介绍团队](assets/Kaggle%20Winners%20Walkthroughs%EF%BC%9A%20Novozymes%20Enzyme%20Stability%20Prediction%20with%20Muhammad%20Ahmed/00015.webp)

### 1.2 亚军 Muhammad：零蛋白经验的三个月逆袭

亚军 Muhammad Ahmed 自我介绍：刚在卡拉奇的大学拿到计算机科学学士学位，住在巴基斯坦，现任一家美国初创公司（口播作 Retropuzzle）的研究工程师，专注计算机视觉与机器学习方向，约两年工作经验。他坦承：参赛之前没有任何蛋白质相关经验，这是他第一个与蛋白沾边的项目——"这三个半月里学了非常多、试了非常多，有一些真的成功了" [【跳转到 01:52】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=112)、[【跳转到 02:17】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=137)。

![亚军 Muhammad 自我介绍：计算机视觉与机器学习背景、零蛋白经验起步](assets/Kaggle%20Winners%20Walkthroughs%EF%BC%9A%20Novozymes%20Enzyme%20Stability%20Prediction%20with%20Muhammad%20Ahmed/00112.webp)

## 二、方案总览：物理 + 机器学习的多路集成

### 2.1 一张图看懂集成框架

拉开方案（solution）的总体图：这是一套**多方法集成（ensemble）**——一部分是能量类的物理方法，一部分是机器学习方法。他还调用了一些网络服务器（web server）与公开可得的资源，以及 FoldX 之类的软件，这些都会在后面的幻灯片中逐一展开 [【跳转到 02:42】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=162)。

![方案总览讲解时刻：能量类物理方法与机器学习方法的多路集成](assets/Kaggle%20Winners%20Walkthroughs%EF%BC%9A%20Novozymes%20Enzyme%20Stability%20Prediction%20with%20Muhammad%20Ahmed/00162.webp)

### 2.2 外部数据：社区共享是半个关键

他同时使用了外部数据——一部分由社区共享给他，一部分本来就是公开数据 [【跳转到 03:07】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=187)。后面会看到，外部数据在两处发挥了关键作用：一是一位 Kaggle 选手用 AlphaFold2 生成并共享的突变体结构（差分特征的原料），二是另一位选手在开赛时公开的一份数据集（机器学习特征的原料）。

## 三、方法清单逐个拆解：从差分特征到压轴 3D 网络

### 3.1 差分特征：AlphaFold2 补出的突变体结构

第一个方法是**差分特征（difference feature）**。比赛方给了野生型 PDB 和对应的测试突变体序列，但没给突变体的 PDB——于是一位 Kaggle 选手用 AlphaFold2 把这些突变体 PDB 生成出来，之后只要对"突变体 PDB vs 野生型 PDB"取差值即可。"仅仅取突变体与野生型之间的差"就得到了非常好的分数 [【跳转到 03:32】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=212)、[【跳转到 03:57】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=237)。

![差分特征讲解时刻：用 AlphaFold2 生成突变体 PDB 再与野生型作差](assets/Kaggle%20Winners%20Walkthroughs%EF%BC%9A%20Novozymes%20Enzyme%20Stability%20Prediction%20with%20Muhammad%20Ahmed/00212.webp)

### 3.2 FoldX5：经验能量项的线性组合

第二个方法是 FoldX5：一个用"经验能量项的线性组合"来计算（突变）能量的软件 [【跳转到 03:57】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=237)。FoldX 后来被证明是三大主力之一（见第五章）。

### 3.3 保守性打分（口播作 "Jamie"）

第三个工具（口播作 "Jamie"，他自承不知道读法，"我就照 Jamie 念了"）的思路是用两个主要参数打分：一是某种**基于保守性的贡献**——衡量特定位点上残基的保守程度；二是**独立贡献**——衡量该位点的残基在那个位置上有多重要 [【跳转到 04:22】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=262)。

### 3.4 机器学习模型 + 特征工程（含 ProtBERT 嵌入）

接下来是带外部数据的机器学习模型。开赛时就有 Kaggle 选手公开共享了一份数据（链接在幻灯片中）；Muhammad 在这份数据之上做了大量特征工程，把众多特征分成几类：属于**蛋白结构**的、属于**蛋白序列**的（氨基酸与若干替换矩阵），再加上 **ProtBERT 嵌入**——ProtBERT 本质上是一个（蛋白质）语言模型，用来估计突变体的嵌入向量 [【跳转到 04:47】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=287)、[【跳转到 05:12】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=312)。特征喂给多个机器学习模型，最终预测取所有模型的集成 [【跳转到 05:37】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=337)。

### 3.5 ModFOLD 与 pLDDT 当 B-factor

下一个是 ModFOLD（口播作 mod fold）——又是一个网络服务器，用神经网络等机器学习技术预测蛋白稳定性 [【跳转到 05:37】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=337)。这里的关键一步是**把 pLDDT 当 B-factor 用**：用 Bio.PDB 库读入 PDB 文件时，B-factor 列对每个残基位置都是独特的；于是可以"完全无视突变体是谁"，直接用该位置的 pLDDT 数值（0–100 分，经 Biopython 库缩放）当作该位置能量变化的代理——同一个位置的所有突变体共用同一个数 [【跳转到 06:02】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=362)、[【跳转到 06:27】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=387)。光靠单个 PDB 的这一招，就能拿到约 0.3 的相关分数 [【跳转到 06:52】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=412)。

![ModFOLD 与 pLDDT-B-factor 讲解时刻：逐残基能量代理估计](assets/Kaggle%20Winners%20Walkthroughs%EF%BC%9A%20Novozymes%20Enzyme%20Stability%20Prediction%20with%20Muhammad%20Ahmed/00362.webp)

### 3.6 MSA + SVM 的网络服务器

接下来是一个网络服务器（口播工具名不清晰，本文按方法记录）：把突变体与多条序列比对（MSA）比较，在此基础上再用支持向量机（SVM）预测稳定性 [【跳转到 06:52】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=412)。

### 3.7 RaSP：在 Rosetta 值上训练的 3D CNN

下一个是 RaSP——一个深度神经网络：输入蛋白的 3D 形式，先过 3D 卷积层，再接下游全连接层；它的训练目标是 Rosetta 计算的值。Muhammad 直接使用了作者放在 GitHub 上的免费预训练模型 [【跳转到 07:17】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=437)。

![RaSP 讲解时刻：3D 卷积网络、以 Rosetta 值为训练目标](assets/Kaggle%20Winners%20Walkthroughs%EF%BC%9A%20Novozymes%20Enzyme%20Stability%20Prediction%20with%20Muhammad%20Ahmed/00437.webp)

### 3.8 RMSD 逐残基估计及其算力墙

RMSD（root-mean-square deviation，均方根偏差）方法：用两个软件工具计算（社区也给出过相关教程）。思路是对野生型蛋白逐残基检查 RMSD 值——某个残基的 RMSD 小，说明它在那个位置非常稳定，"把它去掉会造成很大的不稳定"。他自评这只是个估计，而且明显次优：突变/替换残基并不总会造成扰动。要修正，就得对每个突变体单独算 RMSD——但测试突变体数以千计，算力不允许，只好作罢 [【跳转到 07:42】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=462)、[【跳转到 08:07】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=487)。

### 3.9 Rosetta 与 FastRelax 松弛

下一个是 Rosetta（他原话："不知道怎么拼，就按 Rosetta 来"）：用基于能量的打分函数加蒙特卡洛模拟来预测蛋白稳定性 [【跳转到 08:32】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=512)。再往后还是 Rosetta 协议，但"松弛（relaxed）"了一档：有 Kaggle 选手在讨论区指出，主办方提供的野生型结构是用 FastRelax 算法算的，于是他把所有测试突变体的 PDB 也做了一遍松弛，再取 Rosetta 分数——性能有所提升 [【跳转到 08:57】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=537)。

![Rosetta 与 FastRelax 讲解时刻：松弛突变体结构后再取分](assets/Kaggle%20Winners%20Walkthroughs%EF%BC%9A%20Novozymes%20Enzyme%20Stability%20Prediction%20with%20Muhammad%20Ahmed/00537.webp)

### 3.10 SDM 与 SP server

SDM 又是一个网络服务器，用的是环境特异性替换表（environment-specific substitution tables）——它的出发点是：稳定性深受结构环境影响，于是把突变体文件与 PDB 比较，用带若干"重要特征"的打分函数打分 [【跳转到 09:22】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=562)。倒数第二个是 SP server（口播如此），同样是一个用打分函数的网络服务器。而最后一个方法给了他"非常好的结果" [【跳转到 09:47】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=587)。

### 3.11 压轴方法：Rosetta 松弛 + 体素特征的 3D CNN

压轴方法也是一个 3D 网络，但与 RaSP 有个关键差别：它先用 Rosetta 对结构做精修（refine）——而且不只是野生型，突变体也同样处理；拿到精修后的结构再计算体素（voxel）特征，得到该蛋白（及突变体）的 3D 表征，喂给 3D 卷积网络，后面接一层全连接层 [【跳转到 10:12】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=612)、[【跳转到 10:37】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=637)。

![压轴方法讲解时刻：Rosetta 精修 + 体素特征 + 3D CNN](assets/Kaggle%20Winners%20Walkthroughs%EF%BC%9A%20Novozymes%20Enzyme%20Stability%20Prediction%20with%20Muhammad%20Ahmed/00612.webp)

## 四、训练与提交策略：在"洗牌"中活下来

### 4.1 训练方式：网络服务器只推理，ML 模型要训练

训练过程很直接：对网络服务器来说就是"跑预测"；对 ThermoNet 等机器学习模型则花了一些训练时间。他使用的外部数据大多都是公开共享的 [【跳转到 11:02】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=662)。

### 4.2 私有段猜想：第 500–1600 行

帮他熬过榜单"洗牌"（很多人从榜首直接掉到很低名次）的关键发现是：根据观察和 Kaggle 论坛上的讨论，他估计**第 500–1600 行属于私有数据**。于是每次往集成里加模型时，他不仅看公开榜分数，还盯着这个区间的预测分布——即使某个模型抬高了公开分，但如果它把这个区间的分布搅得太乱（加了太多噪声），他就直接弃用该方法 [【跳转到 11:27】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=687)、[【跳转到 11:52】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=712)。

![私有段发现讲解时刻：盯住第 500–1600 行的分布稳定性](assets/Kaggle%20Winners%20Walkthroughs%EF%BC%9A%20Novozymes%20Enzyme%20Stability%20Prediction%20with%20Muhammad%20Ahmed/00687.webp)

旁证还有一条：很多选手注意到，对第 1–2500 行随便做些随机预测，公开榜分数都会明显变化——这暗示私有数据就藏在这个区间。他自己也真做过随机预测实验：公开榜分数没有变化，于是更确信该区间属于私有段 [【跳转到 19:13】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=1153)、[【跳转到 20:28】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=1228)。

### 4.3 最终提交：稳定性优先于公开榜名次

最终两个提交：一个是他的公开榜最佳模型；另一个是 **618 号方案**——它在公开榜上连他自己的前 40–50 名都进不了，但在（疑似私有段）的分布上非常稳定。正是 618 号把他送上了第二名 [【跳转到 12:17】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=737)、[【跳转到 12:42】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=762)。

### 4.4 训练/测试错位为什么无碍

所有人都注意到训练数据与测试数据不太相关：测试集是一条蛋白及其对应突变体，训练集却是很随机的大杂烩。但他认为问题不大——有三个月时间可以去找重要的数据、凑外部数据、把各种方法都试一遍。此外他还试过很多别的方法：大量网络服务器、大量神经网络 [【跳转到 12:42】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=762)、[【跳转到 13:07】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=787)。

## 五、三大主力与集成权重

### 5.1 只用 FoldX + Rosetta relaxed + ThermoNet ≈ 53 分

他特别强调自己说的是"简单模型"：FoldX 在公开榜和私有榜上表现都不错，Rosetta relaxed 同样，ThermoNet 也是。**这三者是主力——只用它们，公开榜就能拿到约 53 的分数** [【跳转到 13:32】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=812)、[【跳转到 13:49】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=829)。

![三大主力模型讲解时刻：FoldX、Rosetta relaxed 与 ThermoNet](assets/Kaggle%20Winners%20Walkthroughs%EF%BC%9A%20Novozymes%20Enzyme%20Stability%20Prediction%20with%20Muhammad%20Ahmed/00817.webp)

### 5.2 多样性带来稳定

被问"三个主力是相互印证还是互补"时，他指出它们非常**多样**：FoldX 和 Rosetta 是能量类方法，ThermoNet 是神经网络——瞄准预测的不同侧面；而且三者分数非常稳定，公开榜与私有榜差异很小 [【跳转到 15:29】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=929)、[【跳转到 16:03】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=963)。对于公开/私有榜间的差异，主持人觉得有趣：数据是系统化记录的，没理由差这么多——也许有的突变靠近活性位点、有的远离，这可能影响了预测 [【跳转到 16:14】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=974)。

### 5.3 权重怎么定：试错 + 简单加权平均

被问集成权重怎么定，他说基本是**试错法**（也考虑过爬山法），最终就是"看公开榜 + 看测试数据分布"的简单加权平均：FoldX 表现好就多给权重（比如 5），SDM 表现一般就少给（比如 2），最后除以总权重（7）做归一化。集成之后他还用 Spearman 度量（"我叫不上名字的那个指标"）做了排序 [【跳转到 20:53】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=1253)、[【跳转到 21:36】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=1296)、[【跳转到 22:01】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=1321)。主持人补了一句：有些方法可能在蛋白的不同区域（表面 vs 核心）各有所长，这或许间接起了作用 [【跳转到 22:01】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=1321)。

![集成权重策略讲解时刻：按公开榜表现赋权、除以总权重归一化](assets/Kaggle%20Winners%20Walkthroughs%EF%BC%9A%20Novozymes%20Enzyme%20Stability%20Prediction%20with%20Muhammad%20Ahmed/01271.webp)

### 5.4 物理方法贡献了 1/3–2/3 的分数

有选手点评：他先上了大量物理方法、再叠机器学习——这可能正是私有榜也表现好的原因，因为物理方法比"只吃数据"的模型更泛化。Muhammad 回应：最初只有物理方法时分数就已经不错，机器学习方法进一步改进了分数——可以说**三分之一到三分之二的分数来自这些物理方法** [【跳转到 23:16】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=1396)、[【跳转到 23:41】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=1421)。

## 六、问答精华

### 6.1 需要更多骨架的数据吗

Novozymes 团队问：这项工作是否暗示需要为其他骨架（backbone）、其他酶补充数据点？答：测试集只有一条蛋白及其点突变，确实需要相关数据来训练——那些外部数据正是由很多 Kaggle 用户共享的（幻灯片里有清单）。追问"有没有因为缺数据而放弃的方法"，他说方法层面试的不多，但相信**如果给 ThermoNet 喂更多相关数据，应该还能做得更好** [【跳转到 16:44】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=1004)、[【跳转到 17:09】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=1029)、[【跳转到 18:08】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=1088)。

### 6.2 一路稳居前 20 的原因

问：三个月里榜单起起伏伏，你为什么能一直稳在前 20？答：一是**起步很早**，有大量时间把很多方案都试了一遍——幻灯片列的只是最终方案的一部分，此外还试过许多网络服务器和方法；实验做得足够多，自然稳 [【跳转到 24:06】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=1446)、[【跳转到 24:31】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=1471)。

### 6.3 语言模型去哪了

问：最终集成里怎么没看到语言模型？答：有——就是 ProtBERT 嵌入，但它是**作为特征与机器学习模型一起用**的，不是独立的一路 [【跳转到 24:56】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=1496)、[【跳转到 25:02】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=1502)。

### 6.4 重新设计比赛：数据怎么组织

Novozymes 方面坦承：共享单一数据集时没预料到社区这么热情——参赛热度、讨论活跃度、以及"对这一份数据的过拟合"都远超预期。如果重新设计比赛，什么数据最好？答：取决于时间线——如果只有一两周，会准备**非常规整的训练数据**：多个蛋白、多个蛋白折叠（folds），每个带点突变和相应分数；如果有三个月，主办方给的数据其实很合适，因为解题不只是机器学习，还包括清洗数据、调研方法、自己去找数据 [【跳转到 25:22】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=1522)、[【跳转到 26:12】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=1572)、[【跳转到 26:37】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=1597)。追问"就算给 10 条骨架、10 倍数据，三个月后方案也会差不多？"答：会给出很多数据，但期待参赛者自己去挑出重要的、忽略其余 [【跳转到 27:02】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=1622)、[【跳转到 27:27】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=1647)。

### 6.5 未来去向与工业落地

问：接下来打算做什么？答：本科刚毕业，下一步读博，方向未定——他个人非常喜欢这个比赛，也许会进入蛋白相关领域（读博或工作） [【跳转到 27:52】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=1672)、[【跳转到 28:17】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=1697)。Novozymes 一侧也感慨：赛前对蛋白一无所知，三个月做到这个程度"令人印象深刻，把事情放进了 Perspective" [【跳转到 28:42】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=1722)。

最后一个非常实际的问题：公司环境里跑这套管线要什么条件？答：网络服务器部分取决于服务器本身的可用性；软件部分取决于机器——FoldX 他在很旧的笔记本上跑单个突变体都没问题。估算下来，跑 FoldX、Rosetta relaxed、ThermoNet 这三个主力，**一个突变体只要几秒，100 个蛋白约一分钟左右**。当然，FoldX 有授权（licensing）问题 [【跳转到 29:07】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=1747)、[【跳转到 29:32】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=1772)、[【跳转到 29:57】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=1797)、[【跳转到 30:22】](https://www.youtube.com/watch?v=nkGYtv--9AU&t=1822)。

![公司环境落地成本讲解时刻：三大主力的算力与授权提醒](assets/Kaggle%20Winners%20Walkthroughs%EF%BC%9A%20Novozymes%20Enzyme%20Stability%20Prediction%20with%20Muhammad%20Ahmed/01772.webp)

## 小结

- 这是一场典型的"结构信息 + 能量物理 + 机器学习"三路融合的稳定性回归实战：测试集只有一条骨架的突变，解题的关键反而在**数据侧**——AlphaFold2 补结构、社区共享数据集。
- 三大主力（FoldX、Rosetta relaxed、ThermoNet）覆盖能量类与神经网络两类方法，只用它们即可拿约 53 的公开榜分数；多样性带来跨公私有榜的稳定。
- 便宜而有效的特征往往最好用：突变体与野生型 PDB 的差分特征、pLDDT 当 B-factor 的逐残基代理、环境特异性替换表（SDM）。
- 提交策略上的洞察最重要：估计出第 500–1600 行是私有段，用"该区间的分布是否被扰动"作为集成成员的去留标准，最终选了公开榜名次不高的 618 号方案并拿下榜眼。
- 物理方法贡献了三分之一到三分之二的分数——先物理后机器学习，比"只吃数据"更泛化。
- 训练/测试错位并不可怕：给足时间，去补数据、清洗数据、调研方法，本身就是解题的一部分。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| 热稳定性 / Tm | 蛋白抵抗热变性的能力；熔解温度 Tm 是蛋白失去一半结构时的温度，越高越耐热 |
| 点突变 | 蛋白序列中单个氨基酸的替换；本赛题即预测每个点突变对稳定性的影响排序 |
| FoldX | 用经验能量项线性组合估计突变能量的经典软件，本方案主力之一 |
| Rosetta / FastRelax | 基于能量函数与蒙特卡洛模拟的结构建模套件；FastRelax 是其中的结构松弛协议 |
| ThermoNet | 基于神经网络的稳定性（ΔΔG）预测模型，本方案主力之一 |
| RaSP | 以 Rosetta 计算值为训练目标、3D 卷积网络结构的稳定性预测模型 |
| SDM | 用环境特异性替换表、按结构环境给突变打分的网络服务器 |
| pLDDT / B-factor | AlphaFold2 逐残基置信度（0–100），存于 PDB 的 B-factor 列，本方案用作逐残基能量代理 |
| ProtBERT | 蛋白质语言模型，为突变序列提供嵌入特征 |
| 公开榜 / 私有榜 | Kaggle 赛制：公开榜用可见测试子集，私有榜用隐藏子集决定最终名次 |
| Spearman 度量 | 秩相关指标，本赛题的评价指标，用于对集成结果再排序 |
