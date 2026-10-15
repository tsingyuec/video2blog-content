# EMBL-EBI 官方教程：相似度指标与置信度分数——读懂结构预测输出的每一个数字

> 来源视频：[Similarity Metrics & Confidence Scores in Protein Structure Prediction | EMBL-EBI Tutorial](https://www.youtube.com/watch?v=dVFHr0ZV4-0) · 时长 21:42
> 本篇基于视频 AI 字幕与画面整理（EMBL-EBI 培训，主讲人 Yonathan Goldtzvik 博士），时间戳可跳转回原视频对应位置。

## 本讲要解决的核心问题（SCQA）

**背景**：AlphaFold 等结构预测模型已经能批量产出蛋白质乃至蛋白质复合物的三维模型。打开任何一个模型的输出，你都会看到一串分数——pLDDT、PAE、pTM、ipTM，以及由它们汇总而来的综合置信度（confidence score）。它们就是各类模型输出里 `confidence_score` 的"家族成员"。

**冲突**：这些分数各有含义、各有阈值、各有盲区。不搞清它们的来龙去脉，就只会机械地"比大小"——而这很容易被误导：高 pLDDT 不保证结构正确，低 ipTM 也未必说明界面错了。

**疑问**：这些分数到底从哪来？各自测量什么？阈值怎么定？什么时候会骗人？

**回答（中心思想）**：**所有预测置信度分数都由"如何定量比较两个结构"这一基础问题发展而来**——RMSD → TM-score → LDDT / aligned error，再到它们的"预测版" pLDDT / PAE / pTM / ipTM。每个分数只在回答特定问题时才可靠：**先用对指标，再谈分数高低**。

![EMBL-EBI 官方培训：相似度指标与置信度分数](assets/Similarity%20Metrics%20%26%20Confidence%20Scores%20in%20Protein%20Structure%20Prediction%20｜%20EMBL-EBI%20Tutorial/00013.webp)

---

## 一、为什么需要"定量比较两个结构"

### 1.1 动机一：给蛋白质结构分类

蛋白质是一条条通常具有确定三维结构的链。正因为结构规整、确定，我们才可能把不同蛋白质放在一起做**结构比较**，看它们的形状是否相似 [【跳转到 01:06】](https://www.youtube.com/watch?v=dVFHr0ZV4-0&t=66)。

![为什么要计算蛋白质相似度：结构规整才可比较](assets/Similarity%20Metrics%20%26%20Confidence%20Scores%20in%20Protein%20Structure%20Prediction%20｜%20EMBL-EBI%20Tutorial/00066.webp)

第一个动机是**结构分类**：历史上几项大型工程对所有已知蛋白结构做了归类，正因为能够量化结构相似度，我们才识别出不同的蛋白质**结构家族**（structural families），对蛋白质的结构多样性有了整体认识 [【跳转到 01:31】](https://www.youtube.com/watch?v=dVFHr0ZV4-0&t=91)。

### 1.2 动机二：评估预测算法靠不靠谱

第二个动机和结构预测直接相关：拿**预测模型**和**实验解析结构**做比较，看算法给出的预测是否真的接近实验观察。想象 AlphaFold 生成了一批预测，我们想知道这些预测是否接近实验结构——这就需要某种"度量" [【跳转到 01:56】](https://www.youtube.com/watch?v=dVFHr0ZV4-0&t=116)。

归纳一下：我们需要相似度分数，是为了有一个**定量且一致**的方式来比较蛋白质结构——既能用来发现结构相似的蛋白质，也能用来评估预测模型的好坏 [【跳转到 02:21】](https://www.youtube.com/watch?v=dVFHr0ZV4-0&t=141)。

---

## 二、全局对齐路线：RMSD → TM-score

### 2.1 RMSD：最朴素的全局差异度量

最直观的做法是：先**对齐**两个结构，再定量测量差异 [【跳转到 02:47】](https://www.youtube.com/watch?v=dVFHr0ZV4-0&t=167)。实现这一点的经典方法叫 **RMSD**（root mean square deviation，均方根偏差）[【跳转到 03:12】](https://www.youtube.com/watch?v=dVFHr0ZV4-0&t=192)。

![RMSD：先在空间中对齐两条蛋白链](assets/Similarity%20Metrics%20%26%20Confidence%20Scores%20in%20Protein%20Structure%20Prediction%20｜%20EMBL-EBI%20Tutorial/00192.webp)

计算 RMSD 分三步：

1. **空间对齐**：若两条链长度相同，残基间存在一一对应关系；"对齐"就是把两个蛋白质摆放到空间中，使两个结构的吻合度最优（有不同算法可实现）。若长度不同，则要先决定一个蛋白的哪些残基对应另一个蛋白的哪些残基，通常按"使对齐最优"的准则来做 [【跳转到 03:34】](https://www.youtube.com/watch?v=dVFHr0ZV4-0&t=214)。
2. **逐残基求距离**：设 D(I) 为残基 I 在结构一和结构二中位置之间的距离。结构高度相似时，同一残基在两个模型中的空间位置会很接近；差异大时则可能相距很远 [【跳转到 04:24】](https://www.youtube.com/watch?v=dVFHr0ZV4-0&t=264)。
3. **平方取均值再开根**：RMSD 就是这些距离**平方的均值再开平方** [【跳转到 04:49】](https://www.youtube.com/watch?v=dVFHr0ZV4-0&t=289)。

![RMSD 公式与判读：差异越小分数越小](assets/Similarity%20Metrics%20%26%20Confidence%20Scores%20in%20Protein%20Structure%20Prediction%20｜%20EMBL-EBI%20Tutorial/00289.webp)

判读约定：两个结构越相似 RMSD 越小，差异越大 RMSD 越大；**RMSD ≤ 2 Å 通常表示两个结构高度相似**。

### 2.2 RMSD 的天生缺陷：长度依赖

RMSD 有一个众所周知的弱点——**受所比较蛋白质的长度影响**。比较两条短蛋白时算的距离数少，比较两条长蛋白时算的距离数多；而结构间总归存在一些差异，累积起来**越长的蛋白往往 RMSD 越大** [【跳转到 05:14】](https://www.youtube.com/watch?v=dVFHr0ZV4-0&t=314)。

### 2.3 TM-score：把长度效应修正掉

绕开这一问题的成功方案是 **TM-score**（template modeling score，模板建模分数）——结构生物信息学中使用极广的相似度分数 [【跳转到 05:39】](https://www.youtube.com/watch?v=dVFHr0ZV4-0&t=339)。

![TM-score：公式中含长度修正项 D0](assets/Similarity%20Metrics%20%26%20Confidence%20Scores%20in%20Protein%20Structure%20Prediction%20｜%20EMBL-EBI%20Tutorial/00364.webp)

它相对 RMSD 有三个关键区别 [【跳转到 06:04】](https://www.youtube.com/watch?v=dVFHr0ZV4-0&t=364)：

- **公式里有一个 D₀ 项**，其取值依赖于目标蛋白的长度——正是这一项修正了长度效应，使 TM-score **不依赖蛋白长度**；
- **取值 0 到 1**：1 表示两个结构完全相似，0 表示毫无相似之处；
- **多重对齐取最优**：TM-score 会把多个结构对齐方案都作为输入，采用使 TM-score 最高的那一种，且只把参与对齐的残基计入最终计算 [【跳转到 06:29】](https://www.youtube.com/watch?v=dVFHr0ZV4-0&t=389)。

### 2.4 RMSD 与 TM-score 的共同盲区：域取向

即便是 TM-score 也有局限。设想两个各含两个**结构域**（domain）的蛋白质，整体结构几乎一样，唯一区别是两个域之间的**相对取向**不同——可以把连接两个域的 linker 上某个残基想象成一个"铰链" [【跳转到 06:50】](https://www.youtube.com/watch?v=dVFHr0ZV4-0&t=410)。

在这种情形下计算 RMSD 或 TM-score：必须先对齐，但两个域的取向不同意味着对齐总顾此失彼——最好情况也只能一次对齐一个域，另一个域存在错位 [【跳转到 07:22】](https://www.youtube.com/watch?v=dVFHr0ZV4-0&t=442)。因此这两个全局分数**总会受域取向影响**，而对齐这类结构从来不是一件容易事。要绕开这个问题，需要一个**对域取向不敏感的局部指标** [【跳转到 07:47】](https://www.youtube.com/watch?v=dVFHr0ZV4-0&t=467)。

## 三、局部路线：LDDT 与 aligned error

### 3.1 LDDT：不看对齐、只看局部邻域

**LDDT**（local distance difference test，局部距离差异检验）正是为上述情形设计的相似度分数：它度量**局部**相似性，对域取向不敏感，而且**不依赖对齐**——计算它根本不需要先做结构对齐 [【跳转到 08:02】](https://www.youtube.com/watch?v=dVFHr0ZV4-0&t=482)。

![LDDT：局部相似度，不依赖空间对齐](assets/Similarity%20Metrics%20%26%20Confidence%20Scores%20in%20Protein%20Structure%20Prediction%20｜%20EMBL-EBI%20Tutorial/00482.webp)

计算流程 [【跳转到 08:27】](https://www.youtube.com/watch?v=dVFHr0ZV4-0&t=507)：

1. 仍需建立残基间的一一对应关系，但**不需要在空间中对齐**；
2. 先选一个**截断距离**（cutoff），对每个残基，找出两个结构中落在截断距离内的所有"邻居残基"；
3. 分别测出这些邻居距离，统计**有多大的百分比距离保持不变**（用多档阈值判定）。

这个百分比就是该残基的 LDDT 分数，取值 0–100；既可以逐残基计算，也可以对整条蛋白取平均 [【跳转到 08:52】](https://www.youtube.com/watch?v=dVFHr0ZV4-0&t=532)。正因为能算到残基级别，我们可以看出两个蛋白中**哪些区域最相似**。

![LDDT 判读阈值：≥80 高相似，<50 差](assets/Similarity%20Metrics%20%26%20Confidence%20Scores%20in%20Protein%20Structure%20Prediction%20｜%20EMBL-EBI%20Tutorial/00557.webp)

判读阈值：**≥ 80 表示高度相似**，更低表示有一定相似性，**< 50 表示相似性差** [【跳转到 09:17】](https://www.youtube.com/watch?v=dVFHr0ZV4-0&t=557)。

### 3.2 设计上的取舍：域取向信息被丢弃了

LDDT 是局部分数——**域间取向的信息被有意丢弃了**。但有时我们恰恰关心域取向，想要一个聚焦"域间相对摆放"的补充分数。专门为此设计的相似度分数，就是 **aligned error**（对齐误差）[【跳转到 09:42】](https://www.youtube.com/watch?v=dVFHr0ZV4-0&t=582)。

### 3.3 aligned error：逐残基对测域取向

aligned error 在**残基对**之间计算 [【跳转到 10:07】](https://www.youtube.com/watch?v=dVFHr0ZV4-0&t=607)：

1. 在第一个蛋白中选两个残基 I 和 J，并在第二个蛋白中找到对应的 I、J；
2. 用残基 I 来对齐两个蛋白——即调整摆放使**残基 I 的全部原子**在两个蛋白中重叠最优；
3. 对齐后，测量残基 J 的 Cα 碳原子在两个蛋白中的位置距离 [【跳转到 10:32】](https://www.youtube.com/watch?v=dVFHr0ZV4-0&t=632)。这个距离就是残基对 (I, J) 的 aligned error。

如果两个蛋白的域间取向相近，这个距离会很小；取向差异大，距离就大 [【跳转到 10:57】](https://www.youtube.com/watch?v=dVFHr0ZV4-0&t=657)。对每一对 (I, J) 都算一遍，就得到一个 **aligned error 矩阵**——热图中越暗的区域 aligned error 越低（对应结构在两个蛋白中相似的结构域），越亮的区域误差越高（对应域间取向的显著差异）[【跳转到 11:22】](https://www.youtube.com/watch?v=dVFHr0ZV4-0&t=682)。

![aligned error 热图：暗区=域内相似，亮区=域取向差异大](assets/Similarity%20Metrics%20%26%20Confidence%20Scores%20in%20Protein%20Structure%20Prediction%20｜%20EMBL-EBI%20Tutorial/00682.webp)

### 3.4 注意：矩阵不对称

一个重要细节：残基对 (I, J) 的 aligned error **不等于** (J, I) 的值——对齐基准从 I 换成 J，测得的距离就会不同 [【跳转到 12:15】](https://www.youtube.com/watch?v=dVFHr0ZV4-0&t=735)。因此 aligned error 矩阵**并不对称**，哪怕乍看之下像是对称的 [【跳转到 12:39】](https://www.youtube.com/watch?v=dVFHr0ZV4-0&t=759)。

---

## 四、把"相似度"升级为"预测置信度"

### 4.1 预测分数 = 相似度分数的预测版

讲完相似度分数，就可以进入主题：如何评估**预测结构**的质量。预测分数与相似度分数同源——相似度分数测的是"两个结构有多像"，预测分数测的是"**我们对预测有多大信心**"；许多预测分数正是从相似度分数发展来的，代表选手有：**pLDDT**（predicted LDDT）、**PAE**（predicted aligned error，预测对齐误差）和 **pTM**（predicted TM score，预测 TM 分数）。它们都与预测质量**相关** [【跳转到 13:02】](https://www.youtube.com/watch?v=dVFHr0ZV4-0&t=782)。

![预测置信度分数家族：pLDDT、PAE、pTM](assets/Similarity%20Metrics%20%26%20Confidence%20Scores%20in%20Protein%20Structure%20Prediction%20｜%20EMBL-EBI%20Tutorial/00782.webp)

### 4.2 pLDDT：AlphaFold 的首选逐残基分数

pLDDT 是最广为人知的预测置信度分数。它遵循与 LDDT 相似的原则、可逐残基计算，取值 0–100，也是 AlphaFold 的首选置信度分数 [【跳转到 13:32】](https://www.youtube.com/watch?v=dVFHr0ZV4-0&t=812)。与 LDDT 不同，它**不表示两个结构的相似度**，而是与"预测结构与实验结构之间的真实 LDDT"**相关** [【跳转到 13:32】](https://www.youtube.com/watch?v=dVFHr0ZV4-0&t=812)。

关键提醒：**相关不等于相等**——差的预测可能拿到高 pLDDT，好的预测也可能拿到低 pLDDT。所以 pLDDT 更应该理解为"**AlphaFold 对自己预测的信心**" [【跳转到 13:57】](https://www.youtube.com/watch?v=dVFHr0ZV4-0&t=837)。

判读阈值 [【跳转到 14:22】](https://www.youtube.com/watch?v=dVFHr0ZV4-0&t=862)：

- **≥ 90**：对模型信心很高；
- **≥ 70**：模型大体正确，可以合理信赖；
- **< 70**：低置信，不应信任模型。

### 4.3 PAE：残基对级别的"取向信心"

前面 aligned error 度量的是两个结构间域取向的相似度；对应地，**PAE** 度量的是**预测中域间取向的置信度** [【跳转到 14:37】](https://www.youtube.com/watch?v=dVFHr0ZV4-0&t=877)。计算方式：对每一对残基 (I, J)，生成一个 aligned error 值的**分布**，PAE 就是这个分布的**加权平均**。PAE 与 aligned error 一样，是分配给**残基对**的分数 [【跳转到 14:54】](https://www.youtube.com/watch?v=dVFHr0ZV4-0&t=894)。

![PAE：预测的残基对取向误差，逐残基对给出](assets/Similarity%20Metrics%20%26%20Confidence%20Scores%20in%20Protein%20Structure%20Prediction%20｜%20EMBL-EBI%20Tutorial/00877.webp)

### 4.4 pTM：把 PAE 汇总成全局分数

我们常想要一个**全局**分数来概括"域间取向的整体置信度"。做法是把 PAE 与 TM-score 的思路结合 [【跳转到 15:15】](https://www.youtube.com/watch?v=dVFHr0ZV4-0&t=915)：TM-score 原本是对距离求和，现在把求和中的**距离换成残基对之间的 PAE**。与 TM-score 尝试多种对齐、选最优一样，pTM 遍历不同的残基 I，对每个 I 把 (I, J) 的 PAE 项对 J 求和，再选出使 pTM 最大的残基 I [【跳转到 16:05】](https://www.youtube.com/watch?v=dVFHr0ZV4-0&t=965)。可以把求和项理解为与残基对 (I, J) 关联的"pTM(I,J)"，pTM 就是选择使这些项对 J 的平均值最大的 I [【跳转到 16:30】](https://www.youtube.com/watch?v=dVFHr0ZV4-0&t=990)。

> 视频特别说明：上面是便于理解的"朴素版"推导，与实践中 pTM 的实际计算存在细微差别，但**本质思想一致** [【跳转到 16:55】](https://www.youtube.com/watch?v=dVFHr0ZV4-0&t=1015)。

---

## 五、复合物预测：界面 PAE 与 ipTM

### 5.1 复合物的 PAE 矩阵：重点看界面块

从单体转向**蛋白质复合物**（以两条链为例）。与单体一样，可以计算复合物的 PAE 矩阵，用它评估模型中**链间相对取向**的置信度——正如单体中评估域间取向那样 [【跳转到 17:31】](https://www.youtube.com/watch?v=dVFHr0ZV4-0&t=1051)。理论上可以用整张 PAE 矩阵算整个复合物的 pTM；但实践中我们往往只关心矩阵中对应**两条链界面**的区域 [【跳转到 17:56】](https://www.youtube.com/watch?v=dVFHr0ZV4-0&t=1076)：界面区 PAE 低 → 两条链相对摆放的置信度高；界面区 PAE 高 → 置信度低。

![复合物 PAE 矩阵：界面块的颜色决定链间摆放可信度](assets/Similarity%20Metrics%20%26%20Confidence%20Scores%20in%20Protein%20Structure%20Prediction%20｜%20EMBL-EBI%20Tutorial/01051.webp)

### 5.2 ipTM：只对界面区域计算的 pTM

于是有了 **ipTM**（interface predicted TM score，界面预测 TM 分数）：不在整张矩阵上算 pTM，而**只在两条链的界面区域上算** [【跳转到 18:21】](https://www.youtube.com/watch?v=dVFHr0ZV4-0&t=1101)。又因为 PAE 矩阵不对称，正确的做法是把**两个界面块都算一遍，取最大值**——与 TM/pTM 取最优的思路一致 [【跳转到 18:46】](https://www.youtube.com/watch?v=dVFHr0ZV4-0&t=1126)。

![ipTM：只在链间界面区域计算](assets/Similarity%20Metrics%20%26%20Confidence%20Scores%20in%20Protein%20Structure%20Prediction%20｜%20EMBL-EBI%20Tutorial/01101.webp)

---

## 六、解读与局限：分数是"分诊"，不是"判决"

### 6.1 pLDDT 的两个告诫

其一，pLDDT 与真实 LDDT 只是相关：真实 LDDT 低时 pLDDT 可能很高，反之亦然；把它当作"模型自己的信心"更合适 [【跳转到 19:15】](https://www.youtube.com/watch?v=dVFHr0ZV4-0&t=1155)。其二，有观点认为低 pLDDT 对应蛋白的**内在无序区**（intrinsically disordered regions），但这一关联要谨慎解读——pLDDT 主要取决于 AlphaFold 预测时可用的**进化数据量**；低 pLDDT 可能确实意味着无序区，**也可能只是数据不足、无法给出自信预测** [【跳转到 19:40】](https://www.youtube.com/watch?v=dVFHr0ZV4-0&t=1180)。

### 6.2 TM 与 ipTM 的长度敏感问题

TM-score（进而 ipTM）已被发现的一个重要弱点：**受目标蛋白与参考蛋白长度差异的影响**。对 ipTM 而言，**不直接参与相互作用区域**的任何差异都会**拉低** ipTM [【跳转到 20:13】](https://www.youtube.com/watch?v=dVFHr0ZV4-0&t=1213)。因此会出现这种情况：**ipTM 低，并不真正反映我们对模型的合理信心**。存在能绕开这一问题的替代分数，本视频未展开 [【跳转到 20:38】](https://www.youtube.com/watch?v=dVFHr0ZV4-0&t=1238)。

### 6.3 场景对号入座

收尾总结 [【跳转到 21:03】](https://www.youtube.com/watch?v=dVFHr0ZV4-0&t=1263)：

- 判断**模型整体该有多少信心** → 看 **pLDDT**；
- 判断**域间取向**预测得好不好 → 看 **PAE 矩阵与 pTM**；
- 判断**复合物中链间取向**的质量 → 看 **ipTM**。

所有分数都有各自的适用场景与局限——选用哪个指标、如何解读读数，都要把这些记在心里。

---

## 小结

- 一切始于"定量比较两个结构"：既为结构分类，也为评估预测。
- **RMSD**：先对齐再算均方根距离；≤2 Å 算高相似；天生**长度依赖**。
- **TM-score**：用 D₀ 修正长度效应，0–1，多对齐取最优；与 RMSD 一样怕"域取向不同"。
- **LDDT**：局部、免对齐，统计截断范围内邻居距离不变的百分比；≥80 高、<50 差；设计上**丢掉域取向**。
- **aligned error**：以残基 I 对齐后测 J 的 Cα 距离，逐残基对成矩阵；矩阵**不对称**。
- **预测版三件套**：pLDDT（逐残基信心，阈值 90/70）、PAE（残基对取向信心）、pTM（PAE 汇总成全局分数）。
- **复合物**：看 PAE 矩阵的界面块；**ipTM** 只对界面计算、两块取最大。
- **pLDDT 低 ≠ 一定是无序区**，也可能是进化数据不足；**ipTM 低 ≠ 界面一定错**，可能被非界面差异拖累。分数是分诊，不是判决。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| RMSD | 对齐后逐残基距离平方均值的平方根；≤2 Å 视为高度相似；受蛋白长度影响 |
| TM-score | 含长度修正项 D₀ 的全局相似度，0–1，多对齐取最优 |
| LDDT | 局部距离差异检验：截断范围内邻居距离不变的百分比，0–100，免对齐、不敏感于域取向 |
| aligned error | 以残基 I 的原子对齐后测残基 J 的 Cα 距离；逐残基对，矩阵不对称 |
| pLDDT | predicted LDDT：AlphaFold 逐残基置信度，0–100；≥90 高、≥70 基本可靠、<70 勿信 |
| PAE | predicted aligned error：残基对上 aligned error 分布的加权平均，反映取向预测置信度 |
| pTM | predicted TM score：把 TM-score 求和中的距离换成 PAE 的全局取向置信度 |
| ipTM | 只在复合物链间界面区域计算的 pTM；因 PAE 不对称取两个界面块的最大值 |

