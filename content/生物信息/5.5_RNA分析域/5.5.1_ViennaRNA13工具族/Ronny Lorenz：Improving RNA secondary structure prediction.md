# Ronny Lorenz：Improving RNA secondary structure prediction

> 视频来源：[YouTube《Improving RNA secondary structure prediction》](https://www.youtube.com/watch?v=KW3Cz1IQPx8)（89:12），主讲人 **Ronny Lorenz**（维也纳大学 BOKU，ViennaRNA 包核心开发者）。本讲是 ViennaRNA 夏季课程的改进篇：在前一讲 Nussinov/能量最小化经典框架之上，系统回答"**怎样在不放弃二级结构抽象的前提下，把预测做得更准**"——比较法引导、实验探测数据引导、硬/软约束统一框架，以及假结、G-四链体、配体结合三类模型扩展。视频字幕为英文自动生成，本文基于文稿整理翻译；文中数字与结论均出自视频内容，可点击时间戳回看核对。

## 本讲要解决的核心问题（SCQA）

**背景**：经典的最小自由能（MFE）预测算法（Nussinov 式动态规划）复杂度只有 O(n³)，跑起来很快，小 RNA 上也确实准（[【跳转到 01:00】](https://www.youtube.com/watch?v=KW3Cz1IQPx8&t=60)）。

**冲突**：但 RNA 越长，预测越差——可选的亚优结构呈爆炸式增长。原因有三个：能量参数本身带实验误差；预测算法忽略离子条件（参数是在人工高钾浓度下测的，镁离子完全没进模型）；更根本的是，MFE 结构未必是细胞里的"天然态"（[【跳转到 02:30】](https://www.youtube.com/watch?v=KW3Cz1IQPx8&t=150)）。

**疑问**：参数可以慢慢改、离子可以慢慢加，但如果我们想"现在就"得到更好的预测，还有哪些杠杆可用？

**回答（中心思想）**：两条路。第一条是**用额外的信息"引导"预测**——同源序列的比较分析、实验结构探测数据，把它们转成约束或伪能量注入算法；第二条是**扩展二级结构模型本身**——把假结、G-四链体、配体/蛋白结合纳入递归。ViennaRNA 包把这两条路全部做成了通用接口（[【跳转到 03:30】](https://www.youtube.com/watch?v=KW3Cz1IQPx8&t=210)）。本讲就是这两条路的完整导览。

## 一、问题清单：改进预测的六个方向

[【跳转到 04:30】](https://www.youtube.com/watch?v=KW3Cz1IQPx8&t=270)

主讲人开场给出一张"改进路线图"，把可做的事分成两层：

- **留在经典模型内**（引导预测）：更好的能量参数、考虑离子浓度、用同源序列做比较分析/共识结构、用结构探测实验数据引导预测；
- **突破经典模型**（扩展模型）：纳入假结等更多结构基序、考虑外部因子（结合 RNA 的小分子/蛋白/其他 RNA）、以及转录动力学——细胞里的 RNA 边转录边折叠，可能永远到不了我们算出来的"最优态"（[【跳转到 06:30】](https://www.youtube.com/watch?v=KW3Cz1IQPx8&t=390)）。

![开场改进路线图：从能量参数、离子、比较法、探测数据到假结、配体、动力学](assets/Ronny%20Lorenz：Improving%20RNA%20secondary%20structure%20prediction/00384.webp)

受时间限制，本讲跳过"更好参数"与"离子浓度"，聚焦四件事：比较法引导、探测数据引导、约束框架、模型扩展。

## 二、比较法：让同源序列替你"投票"

[【跳转到 07:30】](https://www.youtube.com/watch?v=KW3Cz1IQPx8&t=450)

单序列预测可能给出完全跑偏的结构；但 rRNA 的例子说明：**生物学家早在动态规划出现之前，就靠比对同源序列的协变模式画出了相当好的 rRNA 结构模型**（[【跳转到 08:30】](https://www.youtube.com/watch?v=KW3Cz1IQPx8&t=510)）。原理是配对位点的**一致突变与补偿突变**：C-G 突成 U-A 结构不变，一条链突变另一条跟着补（C-G→U-G→U-A），而把 C-G 突成 A-G 这种"非配对化"突变会直接改变最优结构（[【跳转到 10:00】](https://www.youtube.com/watch?v=KW3Cz1IQPx8&t=600)）。

怎么把这份信息装进预测算法？主讲人归纳了四种范式（[【跳转到 11:30】](https://www.youtube.com/watch?v=KW3Cz1IQPx8&t=690)）：

1. **先比对、后折叠**：对多序列比对结果预测兼容的共识结构——对**比对错误极其敏感**，比对里挪几个位置，预测结构可能面目全非；
2. **先折叠、后比对**：逐条预测结构再做"结构比对"——对**单序列预测错误极其敏感**，一条离群序列可能毁掉整个共识模型；
3. **折叠与比对同时进行**：与 Sankoff 算法同族的动态规划；
4. **免比对预测**：为每条序列预测近优、粗粒度的结构，然后从高频出现的基序里拼出共识模型，全程不比对序列（[【跳转到 14:00】](https://www.youtube.com/watch?v=KW3Cz1IQPx8&t=840)）。

![比较法四种范式：先比对后折叠、先折叠后比对、同时进行、免比对](assets/Ronny%20Lorenz：Improving%20RNA%20secondary%20structure%20prediction/00891.webp)

现成的程序四类都有，详细内容留给后面讲比较建模的专场。这里想强调的是：**比较法的信息可以转成一种"引导势"，作为额外的能量项，把解推向正确的方向**（[【跳转到 09:30】](https://www.youtube.com/watch?v=KW3Cz1IQPx8&t=570)）。

## 三、实验探测数据：最近十年最热的引导手段

### 3.1 探测实验长什么样

[【跳转到 18:30】](https://www.youtube.com/watch?v=KW3Cz1IQPx8&t=1110)

化学或酶法探测的思想很老——不少试剂上世纪 60 年代就有了，比第一个二级结构预测算法还早。把 RNA 放进溶液，加入试剂：有的化学试剂**专挑未配对核苷酸修饰**，有的核酸酶**专切未配对位点或双链区**，于是"配对/未配对"就被翻译成了"修饰/切割"信号。常用试剂一箩筐：RNase 类、铅离子、CMC、DEPC、DMS、SHAPE 试剂，还有让 RNA 自然降解的 inline probing（[【跳转到 20:00】](https://www.youtube.com/watch?v=KW3Cz1IQPx8&t=1200)）。

通用流程：探测实验 → 凝胶电泳/逆转录/高通量测序读出修饰位点 → 换算成每个位点的**反应活性（reactivity）** → 转成约束或伪能量 → 喂给预测算法（[【跳转到 21:00】](https://www.youtube.com/watch?v=KW3Cz1IQPx8&t=1260)）。

![探测数据流程：试剂修饰/切割 → 测序读出 → reactivity → 约束/伪能量](assets/Ronny%20Lorenz：Improving%20RNA%20secondary%20structure%20prediction/01275.webp)

约束可以很硬："这个位点必须未配对"；也可以是概率："70% 未配对"；最常见的形态是**伪能量**——加在经典能量模型之上的一层修正项（[【跳转到 22:00】](https://www.youtube.com/watch?v=KW3Cz1IQPx8&t=1320)）。

### 3.2 SHAPE：为什么它成了默认选项

[【跳转到 23:30】](https://www.youtube.com/watch?v=KW3Cz1IQPx8&t=1410)

SHAPE（Selective 2'-Hydroxyl Acylation analyzed by Primer Extension）探测的是**RNA 骨架的柔性**：骨架越柔韧，试剂越容易挂上去。潜台词是"柔=未配对"。它受欢迎有两个理由：其一，早期很多试剂对特定核苷酸有偏 bias，而 SHAPE 被认为**完全没有核苷酸偏好**；其二，SHAPE 与高通量测序天然兼容，可以全转录组规模地产出数据（[【跳转到 25:00】](https://www.youtube.com/watch?v=KW3Cz1IQPx8&t=1500)）。

### 3.3 把 reactivity 塞进递归的三种方式

**第一种，Deigan 等（2009）**：二级结构分解成环时，对自由能贡献最大的是碱基堆积（stack）。那就直接在递归里给每个 stack 里的四个核苷酸加上正比于 reactivity 的惩罚项，削弱这些 stack——结果是螺旋内部每个位置的 reactivity 会被计入两次（相邻两个 stack 各算一次），螺旋末端只计一次（[【跳转到 26:00】](https://www.youtube.com/watch?v=KW3Cz1IQPx8&t=1560)）。

![Deigan 2009：给 stack 加伪能量，螺旋内位点被计两次](assets/Ronny%20Lorenz：Improving%20RNA%20secondary%20structure%20prediction/01559.webp)

**第二种，Washietl 等**：不挑 stack，而是把实验活性换算成"未配对概率"，**对所有核苷酸**加伪能量——预测算法认为某位点未配对时，加上与实验一致性的奖励/惩罚（[【跳转到 29:00】](https://www.youtube.com/watch?v=KW3Cz1IQPx8&t=1740)）。

![Washietl 方法：对所有核苷酸按配对/未配对加伪能量](assets/Ronny%20Lorenz：Improving%20RNA%20secondary%20structure%20prediction/01786.webp)

**第三种，Lorenz 等（2012）**：前两种都把 reactivity 直接当真。但如果某些区域经典算法本来就预测对了呢？硬加伪能量反而引入人为误差。这第三种思路是把伪能量当**待优化的自由参数**：预测算法能给出每个位点的配对概率，实验也能给出配对/未配对概率，那就去找一组伪能量，使两者的差异最小（[【跳转到 30:00】](https://www.youtube.com/watch?v=KW3Cz1IQPx8&t=1800)）。

![Lorenz 2012：优化伪能量，使预测配对概率与实验概率尽量一致](assets/Ronny%20Lorenz：Improving%20RNA%20secondary%20structure%20prediction/01958.webp)

三种方法放一起跑 benchmark（以阳性预测值 PPV 的提升衡量），结论是：**大多数情况下加入探测数据确实变好，但存在反而变差的案例**——尤其是参考结构里带假结、而预测算法不支持假结的情形：算法给不出假结，探测数据却把假结相互作用也探了进去，换算成伪能量后全是误导（[【跳转到 32:30】](https://www.youtube.com/watch?v=KW3Cz1IQPx8&t=1950)）。

![三种 SHAPE 方法的 benchmark：多数变好，假结案例反而变差](assets/Ronny%20Lorenz：Improving%20RNA%20secondary%20structure%20prediction/02198.webp)

### 3.4 探测数据的四个坑

[【跳转到 36:30】](https://www.youtube.com/watch?v=KW3Cz1IQPx8&t=2190)

- **可重复性不稳**：同实验室、同协议，周五测的和周一测的都可能对不上——"街上卡车经过震一震桌面"都能改变信号；
- **区分度差**：探测活性高≠未配对。发夹环里可以比突起更"僵硬"，探测活性反而更低；柔性只是未配对的粗糙代理（[【跳转到 38:00】](https://www.youtube.com/watch?v=KW3Cz1IQPx8&t=2280)）；
- **ensemble 叠加**：探测测的是一管 RNA 分子，不同分子处于不同构象，信号是所有结构的叠加——某位点 50% 的结构里配对、50% 未配对，信号就变得难以解释（[【跳转到 39:30】](https://www.youtube.com/watch?v=KW3Cz1IQPx8&t=2370)）；
- **三级相互作用**：探测能探到假结、A-minor 这类二级结构模型里根本没有的相互作用，直接当伪能量用会带偏预测（[【跳转到 40:00】](https://www.youtube.com/watch?v=KW3Cz1IQPx8&t=2400)）。

所以主讲人的建议是：数据要经过好的统计处理、工具要能灵活地把数据放进不同类型的结构基序、并且牢记 ensemble 反卷积问题（[【跳转到 42:00】](https://www.youtube.com/watch?v=KW3Cz1IQPx8&t=2520)）。

## 四、统一框架：硬约束与软约束

[【跳转到 43:00】](https://www.youtube.com/watch?v=KW3Cz1IQPx8&t=2580)

上面所有引导手段，最终都落到同一个框架里：

- **硬约束**：布尔开关。"这个核苷酸必须未配对""这里必须配对"——不满足的子结构直接从分解方案的候选中删除，连能量都不用算；
- **软约束**：伪能量或概率。"60% 概率未配对"这种软信息不能硬删子结构，只能修改对应分解步骤的能量贡献，把结构往对的方向拉。

两者在递归里的位置完全一样。把经典分解方案写成递归式后，每个分解分支（i 未配对、i 与 k 配对……）都可以乘上一个布尔因子 X——X=0 表示这个分支被硬约束禁止，X=1 表示放行；而软约束则是加在环能量上的实值修正项（[【跳转到 46:00】](https://www.youtube.com/watch?v=KW3Cz1IQPx8&t=2760)）。

![硬约束=分支上的布尔因子；软约束=环能量上的实值修正](assets/Ronny%20Lorenz：Improving%20RNA%20secondary%20structure%20prediction/02685.webp)

ViennaRNA 的贡献是把这套接口做得**足够通用**：硬约束可以依赖多个核苷酸位置（比如内环要同时约束包裹碱基对与被包碱基对共四个位置），软约束可以挂在任何类型的环上——而不是像老程序那样每种约束各写死一种开关（[【跳转到 48:30】](https://www.youtube.com/watch?v=KW3Cz1IQPx8&t=2910)）。

## 五、模型扩展之一：假结

[【跳转到 49:30】](https://www.youtube.com/watch?v=KW3Cz1IQPx8&t=2970)

约束救不了的场景之一：发夹环和下游序列再配对，形成 H 型假结；两个发夹互相配对，形成 kissing hairpin。自然界里假结相当常见——它让 RNA 在三维上更紧凑——但预测算法默认不带它。**不是因为它稀有，而是因为复杂度**：任意假结的预测是 NP-hard，而且能量模型本身都还没建好——假结能量对离子浓度（尤其镁离子）极其敏感，还叠加各种三级相互作用，怎么写进二级结构范式至今没有好答案（[【跳转到 51:00】](https://www.youtube.com/watch?v=KW3Cz1IQPx8&t=3060)）。

![H 型假结与 kissing hairpin：常见但计算上昂贵](assets/Ronny%20Lorenz：Improving%20RNA%20secondary%20structure%20prediction/03057.webp)

现行的两条折衷路线（[【跳转到 52:30】](https://www.youtube.com/watch?v=KW3Cz1IQPx8&t=3150)）：

1. **限制子类**：只允许 H 型、只允许 H 型+kissing hairpin 等受限子类，重新设计分解方案——复杂度从 O(n³) 涨到 O(n⁴)、O(n⁵)、O(n⁶)，但仍是精确的动态规划；
2. **启发式两步**：先预测不带假结的结构，再分析"哪里可以把未配对的互补片段接起来"补上假结——本质是先折叠、后修正的两阶段法。

## 六、模型扩展之二：G-四链体

### 6.1 结构与生物学

[【跳转到 55:00】](https://www.youtube.com/watch?v=KW3Cz1IQPx8&t=3300)

G-四链体（G-quadruplex）由**富 G 序列**形成：几段连续的 G（G-run，中间隔着短的任意序列），每层四个 G 通过 Hoogsteen 氢键围成一个平面 G-quartet，平面再层层堆叠——π 轨道重叠使它比普通双螺旋**稳定得多**（[【跳转到 57:30】](https://www.youtube.com/watch?v=KW3Cz1IQPx8&t=3450)）。

![G-四链体：G-run → 平面 G-quartet → 层层堆叠](assets/Ronny%20Lorenz：Improving%20RNA%20secondary%20structure%20prediction/03478.webp)

生物学上它无处不在：人类端粒的 DNA 富 G 区、启动子区（G4 挡住双链复性、基因保持可转录）、mRNA 的 5' UTR（G4 卡住翻译机器、翻译效率大降）、3' UTR（外切核酸酶被 G4 卡住、RNA 寿命延长），甚至编码区内也有被蛋白识别、辅助 mRNA 定位的案例（[【跳转到 58:30】](https://www.youtube.com/watch?v=KW3Cz1IQPx8&t=3510)）。

### 6.2 怎么塞进递归

[【跳转到 60:30】](https://www.youtube.com/watch?v=KW3Cz1IQPx8&t=3630)

G-四链体有个好性质：**局部闭合**——有明确的 5'、3' 端，中间的 linkers 全按未配对处理。所以它可以像螺旋一样当一个"闭合子结构"挂进分解方案：原来"i 与 k 配对"的位置，多一个选项"从 i 起形成 G-四链体"。G-run 的扫描本身是线性的，能量可以预处理，动态规划里只需多加一个存放四链体端点能量的三角矩阵（[【跳转到 64:30】](https://www.youtube.com/watch?v=KW3Cz1IQPx8&t=3870)）。

### 6.3 一个简单的能量模型

[【跳转到 65:30】](https://www.youtube.com/watch?v=KW3Cz1IQPx8&t=3930)

2011 年一组 UV melting 实验测了约 40 种不同 linker 组成的 RNA G-四链体。把自由能对"总 linker 长度"作图，是一条近对数曲线。于是有了极简模型：**稳定项正比于堆叠层数减一（层数 L 有 L−1 个层间相互作用），去稳定项正比于 linker 总长 l 的对数**——E = a(T)·(L−1) + b(T)·ln(l)，其中 linkers 的序列组成、内部结构一概忽略。用 melting 数据拟合参数后，模型预测的熔解温度与实验相当接近，足以支撑"螺旋 vs 四链体竞争"的建模（[【跳转到 68:00】](https://www.youtube.com/watch?v=KW3Cz1IQPx8&t=4080)）。

### 6.4 实战：端粒酶 RNA 的模板开关

[【跳转到 72:00】](https://www.youtube.com/watch?v=KW3Cz1IQPx8&t=4320)

人类端粒酶 RNA 组件（hTR）的 5' 端既可能形成 G-四链体，也可能不形成。带 G4 时整体结构一变，**作为端粒模板的识别基序被压在结构里**；不带 G4 时这一段完全暴露、可及。把 G4 支持开与关各跑一遍 RNAfold，预测的模板区可及性概率显著不同——G4 形成则模板不可及，端粒酶无法工作。而配分函数算出的 G4 形成概率约 **60%**：一半多的结构里 G4 在，四成不在。这种"五五开"恰恰意味着外部因子（离子、配体）可以轻易拨动这个开关、诱发大的结构变化（[【跳转到 74:00】](https://www.youtube.com/watch?v=KW3Cz1IQPx8&t=4440)）。

![端粒酶 RNA：G-四链体形成与否决定端粒模板区的可及性](assets/Ronny%20Lorenz：Improving%20RNA%20secondary%20structure%20prediction/04314.webp)

ViennaRNA 里 RNAfold、RNAalifold（比对共识）、RNAcofold（双链互作）、RNALfold/RNAplfold（局部折叠/全基因组扫描）全线支持这套 G4 模型（[【跳转到 70:30】](https://www.youtube.com/watch?v=KW3Cz1IQPx8&t=4230)）。

### 6.5 已知局限

[【跳转到 77:30】](https://www.youtube.com/watch?v=KW3Cz1IQPx8&t=4650)

- linkers 里的结构、G4 拓扑多样性（平行/反平行/混合）全被忽略——DNA 的 G4 拓扑尤其丰富，拓扑不同能量差别很大；
- 不支持分子间 G4（两条链各贡献一半的 G-run），而端粒酶场景恰恰需要 RNA-DNA 分子间 G4；
- 离子浓度完全没进模型——而 G4 形成对钾/镁浓度高度敏感。

## 七、模型扩展之三：配体与蛋白结合

[【跳转到 79:00】](https://www.youtube.com/watch?v=KW3Cz1IQPx8&t=4740)

第三类扩展回答：小分子 aptamer 专用基序、或"逢未配对就结合"的单链结合蛋白，怎么进预测？

**简单情形用约束配分函数**：设配体结合基序为 A，结合态结构集合的配分函数 Q_A 可以用硬约束（"基序处必须未配对"）算出，再乘上**解离常数/浓度（Kd/c）**作为权重，加到总配分函数里——Q = Q_unbound + (Kd/c)·Q_A（[【跳转到 80:30】](https://www.youtube.com/watch?v=KW3Cz1IQPx8&t=4830)）。

![配体结合：约束配分函数 Q_A 乘上 Kd/c 加进总配分函数](assets/Ronny%20Lorenz：Improving%20RNA%20secondary%20structure%20prediction/04818.webp)

**麻烦在组合爆炸**：序列里有 2 个潜在结合位点，就要枚举"只结合第一个/只结合第二个/两个都结合"；3 个位点更糟——需要算的约束配分函数数量随位点数指数增长（[【跳转到 81:30】](https://www.youtube.com/watch?v=KW3Cz1IQPx8&t=4890)）。

**通用解法还是扩递归**：像 G-四链体一样，把"蛋白结合在某段未配对区"作为分解方案的新分支显式建模，ViennaRNA 的 unstructured domains 特性就是这么实现的。代价有两个：模型里**没有协同效应**（"先结合 A 蛋白、才能再结合 B 蛋白"这种顺序依赖表达不了）；**浓度一变就得重算整个递归**——约束法里 Q_A 与浓度无关、只乘系数，扩展法里浓度直接进了递归（[【跳转到 84:00】](https://www.youtube.com/watch?v=KW3Cz1IQPx8&t=5040)）。

## 八、Q&A 精选

[【跳转到 85:30】](https://www.youtube.com/watch?v=KW3Cz1IQPx8&t=5130)

**问：同一条 RNA 的不同 SHAPE 实验之间有相关性吗？**
答：希望有——同一实验室周一和周五测的、不同组测的，多数情况应该相关。但实验条件最轻微的变化都可能改变探测信号（主讲人开玩笑：街上卡车一过、桌面一震都可能影响），轻微的活性差异有时足以完全改变预测结构——总体仍然很噪（[【跳转到 86:30】](https://www.youtube.com/watch?v=KW3Cz1IQPx8&t=5190)）。

**问：配体的结合位点是怎么算出来的？**
答：前提是你已知结合模式。aptamer 场景模式非常特异（特定结构+特定序列组成）；单链结合蛋白则"逢未配对即结合"。通吃做法：线性扫描所有候选位点，逐个算约束配分函数，或者把结合直接做成递归扩展（[【跳转到 87:30】](https://www.youtube.com/watch?v=KW3Cz1IQPx8&t=5250)）。

![Q&A：扫描候选位点 + 约束配分函数/递归扩展](assets/Ronny%20Lorenz：Improving%20RNA%20secondary%20structure%20prediction/05239.webp)

## 写在最后

这一讲把 ViennaRNA 的"改进哲学"讲透了：**能引导就引导（比较法、探测数据→硬/软约束），引导不了就扩展（假结、G-四链体、配体结合→新分解分支）**，而且所有扩展都保持同一个 O(n³)~O(n⁵) 量级的动态规划骨架。对使用者来说，最实用的收获是三点：探测数据好用但有坑、G-四链体已经全线进了 ViennaRNA 的各个程序、配体结合优先想清楚"用约束还是扩递归"。
