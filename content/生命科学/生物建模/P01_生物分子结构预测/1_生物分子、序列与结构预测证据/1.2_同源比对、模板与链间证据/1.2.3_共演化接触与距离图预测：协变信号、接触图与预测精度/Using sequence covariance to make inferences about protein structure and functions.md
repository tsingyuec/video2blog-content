# 从序列共变读出三维结构：MSA 里藏着折叠的信息

> 视频来源：[Using sequence covariance to make inferences about protein structure and functions](https://www.youtube.com/watch?v=EjgOQJNSFpg&t=0)（YouTube · Harvard CMSA · Lucy Colwell）
> 本文基于视频演说图文稿整理，配图截自视频。

## 本讲要解决的核心问题（SCQA）

**背景**：测序越来越便宜，一个蛋白家族动辄能拿到上万条同源序列，排成一张**多序列比对**（MSA）；而测定一个蛋白质的三维结构，实验上虽然可行，却依然昂贵而困难。 [【跳转到 10:53】](https://www.youtube.com/watch?v=EjgOQJNSFpg&t=653)

**冲突**：只看"哪些列保守"（一阶统计、隐马尔可夫模型）远远不够——保守性只说明"重要"，给不出三维结构；而真正与结构相关的信号藏在**哪两列一起变**（共变）里，可朴素的统计又会被相关性的"传递性"淹没。 [【跳转到 07:32】](https://www.youtube.com/watch?v=EjgOQJNSFpg&t=452)

**疑问**：能不能把 MSA 里的共变"反演"成残基接触，再把接触折叠成完整的三维结构？序列少了还行不行？又怎么**事先**判断数据够不够？

**回答（中心思想）**：能。用**最大熵（波茨）模型**把序列共变转化为接触预测，再用**距离几何**把接触约束折叠成三维结构——在序列充足时能做出接近晶体结构的预测；但成败取决于**采样量**，而且样本间的亲缘相关会扭曲统计谱的形状，需要**随机矩阵理论**来把关。

---

## 一、问题设定：从一条线性链到三维结构

任何生物里，蛋白质刚被核糖体合成出来时都是一条**未折叠的线性多肽链**——一串氨基酸，图中一个小格子代表一个残基，按序列位置 1、2、3…编号。 [【跳转到 02:19】](https://www.youtube.com/watch?v=EjgOQJNSFpg&t=139)

![线性氨基酸链与序列位置编号](assets/Using%20sequence%20covariance%20to%20make%20inferences%20about%20protein%20structure%20and%20functions/00156.webp)

核心事实是：这条聚合物会**自组装**成某个唯一的三维结构，而且每次都以同样的方式折叠；折叠好的结构再与自身拷贝或其他蛋白相互作用，形成有功能的复合物。 [【跳转到 03:01】](https://www.youtube.com/watch?v=EjgOQJNSFpg&t=181) 从"氨基酸字母串"到"折叠好的功能分子"，只凭序列预测结构与功能——这就是经典的**蛋白质折叠问题**。 [【跳转到 03:26】](https://www.youtube.com/watch?v=EjgOQJNSFpg&t=206)

## 二、建模思路：给蛋白家族建一个概率模型

氨基酸共 20 种，序列的每个位置可取约 20 种状态（外加空位）。讲者的目标很明确：为你感兴趣的蛋白（比如血红蛋白）建一个**概率模型**——以序列位置为变量（1 到 L），判断哪些序列属于这个家族。 [【跳转到 04:08】](https://www.youtube.com/watch?v=EjgOQJNSFpg&t=248)

数据从哪来？测序成本下降让每个蛋白都积累了大量"版本"：图里每一行就是血红蛋白的一个版本。这些不同的序列版本，本质上是**数百万次演化实验的成绩单**——物种演化中突变不断发生：能让蛋白继续工作的被接受，否则那个个体被淘汰。 [【跳转到 05:13】](https://www.youtube.com/watch?v=EjgOQJNSFpg&t=313)

![血红蛋白家族的多序列比对：每一行是一个物种的版本](assets/Using%20sequence%20covariance%20to%20make%20inferences%20about%20protein%20structure%20and%20functions/00288.webp)

注意看这张比对：绝大多数列**相当保守**——整列从头到尾都是同一个氨基酸。但保守性只是故事的一半，接下来会看到它"说不出"什么。

蛋白质执行的功能——配体结合、维持三维结构、与其他蛋白结合、执行特定任务——通常由**一组氨基酸**共同控制。我们想知道：序列里到底是哪些位置组控制着这些功能？想改造蛋白让它为我们做事，就得先搞清线性序列与功能之间的这层关系——也就是**反向利用序列数据，找出这些约束**。 [【跳转到 06:21】](https://www.youtube.com/watch?v=EjgOQJNSFpg&t=381)

## 三、一阶模型（HMM）：只有保守性，没有结构

很长时间里，人们用的是**一阶模型**：只含线性项，每一项只涉及单个序列位置，并假设各位置**独立演化**——没有相互作用。基于这个假设的隐马尔可夫模型（HMM）非常成功：它让我们能构建大规模蛋白序列比对，得到包含成千上万条序列的蛋白家族。 [【跳转到 06:44】](https://www.youtube.com/watch?v=EjgOQJNSFpg&t=404)

![一阶模型与隐马尔可夫模型：只用单位置信息](assets/Using%20sequence%20covariance%20to%20make%20inferences%20about%20protein%20structure%20and%20functions/00404.webp)

但关键问题是：这些模型能告诉我们**结构与功能**的什么？它们有局限——只涉及单个位置。我们能说的基本只有："演化中不怎么变的位置通常对功能重要"，仅此而已。一阶统计的保守性，**推不出任何三维结构信息**。 [【跳转到 07:52】](https://www.youtube.com/watch?v=EjgOQJNSFpg&t=472)

## 四、共变从哪来：电荷配对玩具模型

要更进一步，就必须在模型里加入位置之间的**相互作用**（高阶项）。一个玩具模型说明二阶项为何重要：蛋白质里两个带相反电荷的氨基酸发生**电荷配对**。 [【跳转到 08:22】](https://www.youtube.com/watch?v=EjgOQJNSFpg&t=502)

![电荷配对玩具模型：双突变恢复功能](assets/Using%20sequence%20covariance%20to%20make%20inferences%20about%20protein%20structure%20and%20functions/00502.webp)

想象一个突变改变了一个电荷——蛋白可能无法正确折叠；但若第二个突变把另一处的电荷也翻转过来，电荷配对恢复，就得到**有功能的双突变体**。 [【跳转到 08:47】](https://www.youtube.com/watch?v=EjgOQJNSFpg&t=527)

推论很妙：在序列数据库里，你只会看到"野生型组合"（如 D–N–K）或"双突变组合"（如 R–N–D），**绝不会看到**只突变一半的中间组合——因为它不是有功能的折叠分子。于是，把玩具比对的各列并排看：第一列与最后一列的变化几乎完全同步——这就是**共变（correlation/covariance）**。 [【跳转到 09:12】](https://www.youtube.com/watch?v=EjgOQJNSFpg&t=552)

即使在小数据集里也能找到这样的两列。它们可能是真的在相互作用，也可能只是样本太小、运气好——但这就是我们要找的信号。 [【跳转到 09:55】](https://www.youtube.com/watch?v=EjgOQJNSFpg&t=595)

![玩具比对：两列的变化几乎完全同步](assets/Using%20sequence%20covariance%20to%20make%20inferences%20about%20protein%20structure%20and%20functions/00595.webp)

## 五、朴素尝试：互信息为什么失败

目标明确了：在大规模 MSA 里测列与列的相关性，找出**在折叠三维结构中彼此靠近**的残基对——把观测到的相关"反演"成结构信息。 [【跳转到 10:28】](https://www.youtube.com/watch?v=EjgOQJNSFpg&t=628)

做法很直接：取 1 万~2 万条序列、150~300 个位置的 MSA，对每一对列计算**互信息**（mutual information，衡量两个变量统计关联的量），构建 L×L 的相关矩阵。 [【跳转到 11:06】](https://www.youtube.com/watch?v=EjgOQJNSFpg&t=666)

检验标准是**接触图（contact map）**：把实验测定的三维结构表示成二值矩阵——两个位置在三维结构中靠近（如序列位置 160 与 110）就在格子里记 1，对角线恒为 1（每个残基都紧挨相邻残基）。把互信息最高的 150 对叠画上去：若方法有效，红点应落在蓝点（真实接触）上。 [【跳转到 11:54】](https://www.youtube.com/watch?v=EjgOQJNSFpg&t=714)

结果失败了：出现一大团一大团的高互信息红点，与真实接触的蓝点大多不重合。 [【跳转到 13:00】](https://www.youtube.com/watch?v=EjgOQJNSFpg&t=780)

![互信息叠加在接触图上：红色团块与真实接触不吻合](assets/Using%20sequence%20covariance%20to%20make%20inferences%20about%20protein%20structure%20and%20functions/00780.webp)

失败的原因是相关的**传递性**：K 与 D 在空间上靠近 → E 变 K 变、K 变 D 变；而 K 还与 E 靠近、D 还与 R 靠近……于是 E–D、乃至一整片位置对之间都表现出相关——**即使它们在三维结构里并不靠近**。相关太多了。 [【跳转到 14:15】](https://www.youtube.com/watch?v=EjgOQJNSFpg&t=855)

## 六、最大熵（波茨）模型：把"相关"变成可解的方程

解法是构造一个**把相互作用考虑进去**的概率模型：用观测到的相关来**约束**模型，并在所有能复现这些相关的模型里，选**约束最少**的那个——即**最大熵模型**。 [【跳转到 15:05】](https://www.youtube.com/watch?v=EjgOQJNSFpg&t=905)

它的函数形式包含两部分：单位置的**线性项**（场，h）与位置对的**成对项**（耦合，e_ij）——基本上就是一个伊辛/波茨（Ising/Potts）模型。 [【跳转到 15:30】](https://www.youtube.com/watch?v=EjgOQJNSFpg&t=930)

![最大熵模型：线性项 + 成对项](assets/Using%20sequence%20covariance%20to%20make%20inferences%20about%20protein%20structure%20and%20functions/00930.webp)

剩下的问题是从数据推断参数 e_ij 与 h_i。做一个朴素的**平均场近似**（假设耦合项远小于场项），则**只需对观测到的协方差矩阵求一次逆**，就能一步解出全部参数。 [【跳转到 15:55】](https://www.youtube.com/watch?v=EjgOQJNSFpg&t=955) 对连续变量的多元高斯这是精确的；这里的变量是离散的（约 20 种取值），所以只是近似——但值得试。

实践中的一个坑：数据不够多时，协方差矩阵常有整列全零、**矩阵奇异不可逆**；绕开的办法是加**伪计数（pseudocounts）**，把零稍微推离。 [【跳转到 16:42】](https://www.youtube.com/watch?v=EjgOQJNSFpg&t=1002)

效果立竿见影：用这个概率模型找出的最高分配对（红点），大体都落在真实接触（灰点）上——对比下方象限的互信息结果（几乎找不到真实接触），**仅凭序列数据**，接触预测的质量已大幅提高。 [【跳转到 16:53】](https://www.youtube.com/watch?v=EjgOQJNSFpg&t=1013)

![波茨模型预测的接触（红）与真实接触（灰）高度吻合](assets/Using%20sequence%20covariance%20to%20make%20inferences%20about%20protein%20structure%20and%20functions/01013.webp)

## 七、从接触到结构：距离几何 + 模拟退火

拿到一堆接触预测后，一个自然的疑问：**这些信息够不够把整个结构定下来**？蛋白质从线性多肽链折叠成三维结构，如果我们知道足够多"哪些残基对相互接触"，累积到某一点，结构就被完全确定了——而刚才那组高分对看起来就是个不错的起点。 [【跳转到 17:18】](https://www.youtube.com/watch?v=EjgOQJNSFpg&t=1038)

检验的唯一的办法就是动手折叠。讲者用了实验结构测定中常见的**距离几何（distance geometry）**：从一条完全伸展开的多肽链出发，给每个高分残基对加上硬约束——"你们在三维空间中的距离必须小于 7 埃"——然后寻找满足全部约束的三维构象。 [【跳转到 18:18】](https://www.youtube.com/watch?v=EjgOQJNSFpg&t=1098)

现成软件包 **CNS**（可在线免费下载）用距离几何加上少量**模拟退火**（把叠在一起的残基分开）完成这一步，让整个流程变得相当容易复现。 [【跳转到 18:43】](https://www.youtube.com/watch?v=EjgOQJNSFpg&t=1123)

![距离几何 + CNS：从接触约束到三维构象](assets/Using%20sequence%20covariance%20to%20make%20inferences%20about%20protein%20structure%20and%20functions/01123.webp)

结果令人振奋：预测结构与实验解出的晶体结构**看起来相当像**，均方根偏差（RMSD）约 3 埃。当然不完美——某些 β 折叠股的形状不对、个别环的构象有偏差——但作为纯预测结果已相当合理。 [【跳转到 19:33】](https://www.youtube.com/watch?v=EjgOQJNSFpg&t=1173)

![预测结构（约 3 埃 RMSD）与实验晶体结构的对比](assets/Using%20sequence%20covariance%20to%20make%20inferences%20about%20protein%20structure%20and%20functions/01173.webp)

更大的蛋白（161/166 个残基）同样得到合理预测；在已知晶体结构的一批蛋白上，这个方法被验证得相当广泛——下图中灰色是晶体结构，紫色是预测结构。 [【跳转到 20:41】](https://www.youtube.com/watch?v=EjgOQJNSFpg&t=1241)

![一批蛋白的验证结果：灰色晶体结构 vs 紫色预测结构](assets/Using%20sequence%20covariance%20to%20make%20inferences%20about%20protein%20structure%20and%20functions/01241.webp)

## 八、盲测：给没有晶体结构的蛋白做预测

更有意思的应用场景是**结构尚未解出**的蛋白，尤其是**跨膜蛋白**：它们嵌在膜里、非常疏水，实验解析特别困难——恰好是预测方法可以大显身手的地方。 [【跳转到 21:07】](https://www.youtube.com/watch?v=EjgOQJNSFpg&t=1267)

先用已解出结构的 β2 肾上腺素受体"练手"：接触图叠加显示预测找接触找得相当好，约 3 埃 RMSD。 [【跳转到 21:25】](https://www.youtube.com/watch?v=EjgOQJNSFpg&t=1285) 然后是一组 11 个**结构从未被解出**的蛋白：序列足够多、预测结果作为蛋白结构看上去足够合理，于是正式给出预测——这些结构没有晶体可对照。 [【跳转到 22:06】](https://www.youtube.com/watch?v=EjgOQJNSFpg&t=1326)

![对未解出结构的蛋白家族做出预测](assets/Using%20sequence%20covariance%20to%20make%20inferences%20about%20protein%20structure%20and%20functions/01326.webp)

## 九、序列数量决定成败：从 2 万条到几百条的断崖

方法不是万能的，**数据量是命门**：

- **序列充足**：约 2 万条序列、约 360 个变量的蛋白，随着统计的高分配对越来越多，真阳性率长期维持在 80% 上下（七八成）。 [【跳转到 23:08】](https://www.youtube.com/watch?v=EjgOQJNSFpg&t=1388)
- **序列不足**：变量更多、序列少得多的蛋白，各方法（正则化不同、本来表现接近）的曲线都**快速掉落**——而现实是，大多数我们想预测结构的蛋白恰恰序列很少。 [【跳转到 23:33】](https://www.youtube.com/watch?v=EjgOQJNSFpg&t=1413)

有一个便宜的补救：**收缩（shrinkage）**——不再直接用协方差矩阵，而是加大其对角线权重。零收缩时前 100 对的真阳性率约 60%；增大收缩强度后升到 80% 以上、接近 90%。这反过来证实：问题确实主要出在**欠采样**。 [【跳转到 24:14】](https://www.youtube.com/watch?v=EjgOQJNSFpg&t=1454)

![收缩强度对真阳性率的提升](assets/Using%20sequence%20covariance%20to%20make%20inferences%20about%20protein%20structure%20and%20functions/01454.webp)

## 十、谱理论把关：亲缘相关会改写"噪声"的形状

怎么**事先**知道数据够不够、预测可不可信？讲者用随机矩阵理论搭了一个分析框架。玩具设定：不用 20 种氨基酸，只用 2 种（二元系统）；取长度 160 的二元字符串，复制多份、各自突变上千次，构建协方差矩阵、看特征值分布。 [【跳转到 25:05】](https://www.youtube.com/watch?v=EjgOQJNSFpg&t=1505)

如果序列**彼此独立**采样，谱的形状有解析答案：**Marchenko–Pastur 定律**（真实协方差为单位阵时的特征值分布）——绿色理论曲线与蓝色观测谱拟合得很好。 [【跳转到 26:00】](https://www.youtube.com/watch?v=EjgOQJNSFpg&t=1560)

一旦加入相互作用，就会出现**脱离大块（bulk）的离散特征值**——这暗示也许光看谱就能发现相互作用的踪迹。 [【跳转到 26:50】](https://www.youtube.com/watch?v=EjgOQJNSFpg&t=1610)

![加入相互作用后，谱出现脱离大块的离散特征值](assets/Using%20sequence%20covariance%20to%20make%20inferences%20about%20protein%20structure%20and%20functions/01610.webp)

但现实数据有个大麻烦：样本序列**并非独立**——它们由**系统发生**（演化亲缘）联系着。仿真显示：一旦强制引入一棵分支树，序列协方差矩阵就出现明显的**块结构**，经验谱分布显著偏离 Marchenko–Pastur——**即使没有任何真实信号**。 [【跳转到 28:51】](https://www.youtube.com/watch?v=EjgOQJNSFpg&t=1731)

好在这是一个可以解析的马尔可夫链：定义参数 α（取决于每分支突变次数与变量数），真实协方差矩阵的元素是 α 的简单函数；用施图姆定理（Sturm's theorem）能写出"大块边缘随 α 变化"的解析曲线，模拟与之吻合得很好；两块分开的临界值大体呈**平方根**关系——变量数与样本数之比（浓度参数）的函数。 [【跳转到 31:39】](https://www.youtube.com/watch?v=EjgOQJNSFpg&t=1899)

由此得到本讲最深刻的教训：**样本间的相关（亲缘）会在没有信号时显著改写经验谱**，让"从数据中识别信号模式"变得困难——除非知道样本间的亲缘树；而想从数据本身推断这棵树，又要用我们正在分析的相关本身，有点鸡生蛋的困境。可行的一条路是借助同一物种的其他蛋白来估计系统发生。 [【跳转到 33:49】](https://www.youtube.com/watch?v=EjgOQJNSFpg&t=2029)

## 十一、总结与未竟问题

讲者总结：**序列共变能够准确预测蛋白质结构**——至少在序列足够多时。 [【跳转到 34:32】](https://www.youtube.com/watch?v=EjgOQJNSFpg&t=2072)

![总结：序列共变 → 接触预测 → 三维结构](assets/Using%20sequence%20covariance%20to%20make%20inferences%20about%20protein%20structure%20and%20functions/02072.webp) 但仍有一串未解决的问题：

- 需要多少条序列？序列之间要有多不同？预测接触的期望误差多大、如何随数据变化？——我们要**理解**方法，而不只是能用它； [【跳转到 34:57】](https://www.youtube.com/watch?v=EjgOQJNSFpg&t=2097)
- 玩具模型里相互作用只有 0 和 1，真实世界的相互作用强度多大、反映什么，我们并不清楚； [【跳转到 35:22】](https://www.youtube.com/watch?v=EjgOQJNSFpg&t=2122)
- 若相互作用并非低秩信号，它们可能改变底层谱的形状——这令人担忧；精确的模型是驾驭这些数据的前提。 [【跳转到 36:12】](https://www.youtube.com/watch?v=EjgOQJNSFpg&t=2172)

（讲者特别感谢博士生李冲（Chong Li）完成了这项工作的许多理论部分。 [【跳转到 36:24】](https://www.youtube.com/watch?v=EjgOQJNSFpg&t=2184)）

## 小结

- 序列便宜、结构昂贵：MSA 是数百万次演化实验的成绩单，但**一阶统计（保守性）推不出 3D 结构**； [【跳转到 07:52】](https://www.youtube.com/watch?v=EjgOQJNSFpg&t=472)
- 结构信号藏在**共变**里：功能约束（如电荷配对）让"半突变"无法存活，数据库里只留下"同变"的列对； [【跳转到 08:47】](https://www.youtube.com/watch?v=EjgOQJNSFpg&t=527)
- 朴素互信息会因**相关的传递性**产生大片假阳性；**最大熵/波茨模型**用"最小相互作用复现观测相关"的原则把相关变成可解的方程； [【跳转到 14:15】](https://www.youtube.com/watch?v=EjgOQJNSFpg&t=855)
- 平均场近似 + 协方差矩阵求逆 + 伪计数，即可一步得到耦合参数；预测接触的质量远超互信息； [【跳转到 16:53】](https://www.youtube.com/watch?v=EjgOQJNSFpg&t=1013)
- 高分配对 → 距离约束（<7 Å）→ 距离几何/模拟退火折叠成 3D 结构，与晶体结构相差约 3 埃，并可盲测未解出结构的蛋白； [【跳转到 19:33】](https://www.youtube.com/watch?v=EjgOQJNSFpg&t=1173)
- 数据量是命门：序列充足时真阳性率 ~80%，序列少则崩；收缩可以部分挽救欠采样； [【跳转到 24:14】](https://www.youtube.com/watch?v=EjgOQJNSFpg&t=1454)
- 系统发生相关会改写噪声谱的形状，随机矩阵理论（Marchenko–Pastur、Sturm 定理）提供了判别信号与噪声的数学框架。 [【跳转到 26:50】](https://www.youtube.com/watch?v=EjgOQJNSFpg&t=1610)

> 回到本系列的语境：这就是为什么下游模型（如 MSA Search→Protenix 一类结构预测流程）对**配对 MSA** 的质量和**序列的多样性**如此挑剔——它们决定共变信号能否被读出来。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| 共变（covariance） | MSA 中两列残基"一起变"的统计关联，可反映残基在空间上靠近/相互作用 |
| 接触图（contact map） | L×L 二值矩阵：两个位置在 3D 结构中靠近记 1 |
| 互信息（MI） | 衡量两列统计关联的量；受相关性传递性影响产生假阳性 |
| 最大熵模型 | 在复现观测约束的模型中选约束最少（熵最大）的那个 |
| 波茨/伊辛模型 | 含单位置"场"项与位置对"耦合"项的概率模型 |
| 平均场近似 | 假设耦合远小于场，从而协方差矩阵求逆一步解参数 |
| 伪计数（pseudocount） | 加在计数矩阵上的小常数，避免零列导致矩阵奇异 |
| 距离几何 | 由位点间距离约束求三维构象的技术（配合模拟退火） |
| RMSD | 均方根偏差，衡量预测结构与晶体结构的平均偏离 |
| Marchenko–Pastur 定律 | 随机矩阵理论中样本协方差矩阵特征值的分布定律 |
| 系统发生（phylogeny） | 序列之间的演化亲缘关系；会使样本相关、扭曲经验谱 |
| 低秩信号 | 相互作用集中在少数模式上；低秩与否影响谱形状是否可控 |
