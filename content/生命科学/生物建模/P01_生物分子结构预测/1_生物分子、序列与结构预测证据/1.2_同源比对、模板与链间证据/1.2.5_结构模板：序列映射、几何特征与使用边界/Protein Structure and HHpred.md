# 蛋白质结构与 HHpred：学会读懂一份 HHR 比对

> 视频来源：[Protein Structure and HHpred](https://www.youtube.com/watch?v=vHNW--EbEN4&t=0)（YouTube · Sally Molloy）
> 本文基于视频演说图文稿整理，配图截自视频。

## 本讲要解决的核心问题（SCQA）

**背景**：噬菌体基因组里大量蛋白没有实验解析的结构，功能未知。用 BLASTP 做序列相似性搜索、借"已知功能蛋白"来注释新蛋白，是最常用的思路。

**冲突**：结构往往比序列更保守——两个三级结构相同、功能也相同的蛋白，序列一致性可能低到 BLAST 根本比对不上；而且 BLAST 的结论还依赖目标蛋白上的注释本身是否可信。

**疑问**：序列对不上的远缘蛋白，怎么推断它的结构与功能？

**回答（中心思想）**：用 **HHpred** 做 HMM-HMM 匹配，输出一份可逐行研读的 **HHR 比对**：看 **probability 分数**（≥90% 才可信）、比对区间与**覆盖度**、共识行的颜色（氨基酸化学性质）与上下两条**二级结构行**（H=α 螺旋、E=β 折叠）是否吻合，再结合文献核对结构域与保守基序（如 Walker A/B），就能把新蛋白定位到已知结构家族并给出功能判断；HHpred 失灵时，还可以用 DeepTMHMM 预测跨膜区做补充判断。

---

## 一、先补齐结构词汇：从一级到四级

### 1.1 一级结构：氨基酸序列，N 端与 C 端

蛋白质里第一个被装配进去的氨基酸，带一个不参与肽键的**氨基**（含氮），称为 **N 端**；最后一个氨基酸带一个不参与肽键的**羧基**，称为 **C 端**。 [【跳转到 00:50】](https://www.youtube.com/watch?v=vHNW--EbEN4&t=50)

![一级结构：clipper gene 8 的 N 端（Met 起步）与 C 端（Val 收尾）](assets/Protein%20Structure%20and%20HHpred/00100.webp)

### 1.2 二级结构：α 螺旋、β 折叠与无规卷曲

蛋白质靠非共价键（常见氢键）在**局部**折叠：相邻氨基酸之间的氢键把一段序列拧成 **α 螺旋**——只有部分序列能形成这类相互作用；另一些序列则靠**两条肽段之间**的氢键拼成 **β 折叠**（示意图里画成小箭头），肽段之间由无结构卷曲/转角相连。 [【跳转到 02:13】](https://www.youtube.com/watch?v=vHNW--EbEN4&t=133)

![α 螺旋：相邻氨基酸之间的氢键](assets/Protein%20Structure%20and%20HHpred/00133.webp)

![β 折叠：肽段之间的氢键，箭头表示折叠方向](assets/Protein%20Structure%20and%20HHpred/00183.webp)

### 1.3 三级与四级结构：单链折叠与多亚基成团

**三级结构**是整条肽链折叠出的三维形状，由无结构转角、α 螺旋、有时还有 β 折叠搭成；许多蛋白还要和其它蛋白分子组装成复合物才能工作——这就是**四级结构**，例如血红蛋白需要 4 条独立亚基组装到一起才能发挥功能。 [【跳转到 03:28】](https://www.youtube.com/watch?v=vHNW--EbEN4&t=208)

![血红蛋白：四条亚基组成的四级结构](assets/Protein%20Structure%20and%20HHpred/00233.webp)

把四个层级放一张图里：一级=序列顺序；二级=局部折叠（α 螺旋/β 折叠/无结构卷曲）；三级=整链三维折叠；四级=与其它蛋白分子形成的最终复合物。 [【跳转到 05:13】](https://www.youtube.com/watch?v=vHNW--EbEN4&t=313)

![结构四层级一览](assets/Protein%20Structure%20and%20HHpred/00313.webp)

### 1.4 结构域：一条链上的多个"功能零件"

以噬菌体 terminase（末端酶）大亚基为例：它会形成**环状复合物**来执行功能；单个亚基的 **N 端是 ATPase 结构域**，**C 端是核酸酶（nuclease）结构域**。也就是说，一条蛋白链可以包含多个各自折叠、各自有独立活性的**结构域**。 [【跳转到 06:11】](https://www.youtube.com/watch?v=vHNW--EbEN4&t=371)

![terminase 大亚基：环状复合物，每个亚基两段功能](assets/Protein%20Structure%20and%20HHpred/00371.webp)

![单个亚基的带状图：N 端 ATPase、C 端 nuclease](assets/Protein%20Structure%20and%20HHpred/00396.webp)

## 二、BLASTP 能做什么、不能做什么

### 2.1 近缘匹配很灵：orf2 ≈ SW2 terminase 大亚基

用 BLASTP 把 oregano 噬菌体的一条蛋白（orf2）比对到数据库，它与 SW2 terminase 大亚基几乎完美匹配：518 个氨基酸对上了 519 个。**一级结构相似 → 功能相似**，这条推断在近缘时非常可靠。 [【跳转到 07:13】](https://www.youtube.com/watch?v=vHNW--EbEN4&t=433)

![BLASTP：orf2 与 SW2 terminase 大亚基近乎完美匹配](assets/Protein%20Structure%20and%20HHpred/00433.webp)

### 2.2 两个坑

- **注释可信度**：用 BLAST 结果下结论时，其实是在假设"给目标蛋白标注功能的人当初标对了"。所以务必先确认你信任目标蛋白上的原始注释，再谈功能转移。 [【跳转到 08:03】](https://www.youtube.com/watch?v=vHNW--EbEN4&t=483)
- **结构比序列保守**：把 oregano 的 GP2 通过 BLAST 比到一种肠杆菌噬菌体的 terminase 大亚基上——比对很差、序列一致性很低，但两者折叠出的**三级结构相似**，功能很可能也相同。这类远缘关系会被 BLAST 漏掉。 [【跳转到 08:53】](https://www.youtube.com/watch?v=vHNW--EbEN4&t=533)

![GP2 的 BLAST 比对很差，但三级结构与功能可能相同](assets/Protein%20Structure%20and%20HHpred/00533.webp)

## 三、HHpred：从序列直接预测结构

HK97 terminase 大亚基的**晶体结构**是已知的——这个蛋白怎么折叠、每个氨基酸在三维结构中的位置，都精确到埃级。HHpred 做的事，是依据查询序列的**一级序列**（氨基酸的化学性质 + 排列顺序），同时预测它的**二级和三级结构**：拿查询蛋白的"轮廓"去匹配已知结构蛋白的"轮廓"。 [【跳转到 09:39】](https://www.youtube.com/watch?v=vHNW--EbEN4&t=579)

![HK97 terminase 大亚基的已知晶体结构](assets/Protein%20Structure%20and%20HHpred/00579.webp)

## 四、逐行读懂 HHpred 的 HHR 比对

以 oregano2 查询、命中 HK97 terminase 大亚基为例，一份 HHpred 比对按五步读。

### 4.1 布局与两条二级结构行

比对最上面是查询（query）序列，最下面是命中（hit）蛋白的序列。目标序列下方标的是**已知二级结构**，查询序列上方标的是**预测二级结构**——红色 H 代表 α 螺旋，蓝色 E 代表 β 折叠。本例 HK97 这段是"α 螺旋-卷曲-β 折叠-卷曲-α 螺旋"，oregano2 的预测几乎一样；顺着比对各行看，二级结构基本对齐。 [【跳转到 11:06】](https://www.youtube.com/watch?v=vHNW--EbEN4&t=666)

![HHpred 比对布局：上下序列与两条二级结构行（H/E）](assets/Protein%20Structure%20and%20HHpred/00666.webp)

### 4.2 共识行与颜色 = 化学性质

两条序列中间的一行叫**共识（consensus）**：里面的标记指出哪些位置氨基酸完全相同（如一个谷氨酰胺在两边同一位点），哪些是相似氨基酸。每种氨基酸还有颜色：**同色 = 化学性质相同**——红=带正电（R/K），蓝=带负电（D/E），绿=疏水（如异亮氨酸、半胱氨酸）。所以即使氨基酸不同，同色也意味着性质相似。 [【跳转到 12:21】](https://www.youtube.com/watch?v=vHNW--EbEN4&t=741)

![共识行颜色：红=R/K 正电，蓝=D/E 负电，绿=疏水](assets/Protein%20Structure%20and%20HHpred/00766.webp)

### 4.3 Probability 比 E-value 更重要

**probability 分数**告诉我们这个匹配是真匹配而非随机的概率；讲者的经验法则是**只看 probability ≥ 90% 的命中**。E-value 也看——它表示匹配随机出现的概率，希望趋近于零——但它会受**比对长度**影响，所以参考权重放低，最看重的是 probability。 [【跳转到 13:36】](https://www.youtube.com/watch?v=vHNW--EbEN4&t=816)

### 4.4 比对区间与覆盖度

看查询蛋白的哪些氨基酸与目标蛋白对上了：本例查询第 59 位氨基酸对应目标第 36 位，一路延伸到查询第 493 位对应目标第 499 位；括号里的数字是每条蛋白的氨基酸总数。由此判断：查询蛋白覆盖了目标蛋白的大部分——**比对的总覆盖度**是必看的数据。 [【跳转到 14:26】](https://www.youtube.com/watch?v=vHNW--EbEN4&t=866)

### 4.5 用文献核对结构域与基序

最后一步是带着文献读比对：先查文献确定 HK97 terminase 上 **ATPase 结构域**的区段，在比对里标黄——本例的比对**完整覆盖**了整个 ATPase 结构域；再核对 ATP 酶必备的 **Walker A / Walker B 基序**是否在比对中保守；C 端同样查文献确定 **nuclease 结构域**区段并标注。两个结构域都在比对里出现，就可以相当有把握地把 oregano2 判定为 terminase 大亚基。 [【跳转到 15:41】](https://www.youtube.com/watch?v=vHNW--EbEN4&t=941)

![标黄的 ATPase 结构域被比对完整覆盖](assets/Protein%20Structure%20and%20HHpred/00941.webp)

## 五、HHpred 之外：DeepTMHMM 判断球状还是膜蛋白

有时 HHpred 给不出足够明确的功能信息。这时还可以从另一个角度提问：这个蛋白是**球状可溶**（待在细胞质里）还是**插在膜上**？用 **DeepTMHMM** 预测**跨膜 α 螺旋**即可。图示横轴是序列位置，纵轴是这段序列涉及跨膜区的概率：没有峰 = 球状蛋白；成簇的峰 = 跨膜区——1 个跨膜区是"穿过膜一次"，3 个像缝衣针把蛋白缝进缝出（几段留在细胞质、几段暴露胞外），还有 5 个以上的。例如 clipper 的一条约 140 多个氨基酸的蛋白就有 4 个跨膜结构域。 [【跳转到 18:09】](https://www.youtube.com/watch?v=vHNW--EbEN4&t=1089)

![DeepTMHMM：clipper 蛋白的 4 个跨膜结构域](assets/Protein%20Structure%20and%20HHpred/01114.webp)

## 小结

- 蛋白质结构分四级：序列 → 局部折叠（α 螺旋/β 折叠/卷曲）→ 整链 3D → 多亚基复合物；
- 一条链可含多个结构域，各自折叠、各有功能（如 terminase 的 ATPase + nuclease）；
- BLASTP 适合近缘功能转移，但受制于目标注释的可信度，且会漏掉"序列不像、结构像"的远缘同源；
- HHpred 用 HMM-HMM 匹配把查询与已知结构蛋白对齐，输出 HHR 比对；
- 读 HHR 五步：二级结构行（H/E）→ 共识行颜色 → probability（≥90% 优先）→ 覆盖度 → 文献核对结构域/基序；
- HHpred 之外，DeepTMHMM 可判断球状/膜蛋白，补充功能判断。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| N 端 / C 端 | 序列起点（游离氨基，含 N）/ 终点（游离羧基，含 C） |
| α 螺旋 / β 折叠 | 氢键维持的两类二级结构；HHpred 比对中记作 H / E |
| 结构域（domain） | 链上折叠成独立功能单元的区段 |
| 四级结构 | 多条蛋白分子（亚基）组装成的复合物 |
| HHR | HH-suite 的搜索结果文件：查询与各模板命中的逐行比对 |
| 共识行（consensus） | 两条序列中间的标记行：相同/相似残基 + 颜色表示化学性质 |
| probability | HHpred 的匹配可信度分数，≥90% 才值得细看 |
| E-value | 匹配随机出现的期望次数，越低越好，但受比对长度影响 |
| Walker A / Walker B | 具备 ATPase 功能必须保守的两个基序 |
| DeepTMHMM | 跨膜 α 螺旋预测工具，区分球状蛋白与膜蛋白 |
