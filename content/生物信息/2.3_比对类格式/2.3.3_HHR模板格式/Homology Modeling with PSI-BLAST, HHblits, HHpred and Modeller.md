# 同源建模全流程：PSI-BLAST → HHblits → HHpred → Modeller

> 视频来源：[Homology Modeling with PSI-BLAST, HHblits, HHpred and Modeller](https://www.youtube.com/watch?v=_G7r799GjL0&t=0)（YouTube · Gabriel Axel）
> 本文基于视频演说图文稿整理，配图截自视频。

## 本讲要解决的核心问题（SCQA）

**背景**：序列相似性是几乎所有蛋白质结构与功能研究的地基。但单条序列携带的信息有限——要推断结构域、结合位点这类"有统计意义"的特征，至少得构建一张**多序列比对（MSA）**。

**冲突**：用 BLAST 找到的前几名命中来建 MSA，里面全是彼此高度相似的序列，提供不了多少统计信息。真正有价值的线索往往藏在**远缘同源**里，而普通序列搜索抓不到它们。

**疑问**：怎么把更远的同源序列一步步"滚"进比对，并最终把它们变成可用于结构预测的**模板**？

**回答（中心思想）**：把搜索灵敏度逐级放大——**BLAST → PSSM / PSI-BLAST → HMM → HMM-HMM（HHblits / HHsearch）**；再用 **HHpred** 把灵敏搜索与结构信息打包，命中结果直接当模板；最后交给 **Modeller** 用"空间约束满足"法搭出三维模型。本讲走完这整条流水线。

---

## 一、从一条序列到一张打分表：PSSM

### 1.1 BLAST：从查询序列出发的第一轮搜索

从一条查询序列出发，第一步是找出与它有良好**局部比对**的序列，常用工具是 BLAST。用 BLAST 的前几名命中与查询序列一起，就能拼出第一张 MSA。 [【跳转到 00:45】](https://www.youtube.com/watch?v=_G7r799GjL0&t=45)

![从查询序列出发：BLAST 找局部比对，前几名命中拼成 MSA](assets/Homology%20Modeling%20with%20PSI-BLAST,%20HHblits,%20HHpred%20and%20Modeller/00045.webp)

问题随之而来：这些命中彼此太像了，用它们建的 MSA 统计意义有限。我们真正想要的，是能匹配"**整条多序列比对**"的更远序列，而不只是匹配起始查询序列。 [【跳转到 01:10】](https://www.youtube.com/watch?v=_G7r799GjL0&t=70)

### 1.2 PSSM：给"每个位置、每种氨基酸"单独打分

双序列比对用**替换矩阵**给"某位置出现某氨基酸"打分；放到 MSA 里，我们需要一个新结构：**位置特异性打分矩阵（PSSM，Position Specific Scoring Matrix）**——每一行是序列上的一个位置，每一列是一种氨基酸，格子里的分数表示该氨基酸在该位置出现的倾向，权重由整条 MSA 统计得出。 [【跳转到 01:35】](https://www.youtube.com/watch?v=_G7r799GjL0&t=95)

![PSSM：行是位置，列是氨基酸，权重反映该位置的保守性](assets/Homology%20Modeling%20with%20PSI-BLAST,%20HHblits,%20HHpred%20and%20Modeller/00095.webp)

### 1.3 3DCONS DB：把 PSSM "看见"

**3DCONS DB** 收录了从 PDB 结构预编译好的 PSSM。挑一个 PDB 条目，右侧就是它编译出的 PSSM：不同位置的权重不同，权重高低通常对应位置的**保守程度**。页面还会把权重画成曲线、标注结构域，并把三维结构按权重着色——聚焦一个高保守位置，就能看到它在 3D 结构中的落点，把"序列保守性"和"结构重要性"直接对应起来。 [【跳转到 02:00】](https://www.youtube.com/watch?v=_G7r799GjL0&t=120)

![3DCONS DB：某个 PDB 条目编译出的 PSSM](assets/Homology%20Modeling%20with%20PSI-BLAST,%20HHblits,%20HHpred%20and%20Modeller/00136.webp)

![权重曲线、结构域注释与按权重着色的三维结构联动](assets/Homology%20Modeling%20with%20PSI-BLAST,%20HHblits,%20HHpred%20and%20Modeller/00161.webp)

## 二、PSI-BLAST：迭代着把远缘同源"滚"进来

有了 PSSM，就能搜索比原始查询更远的序列：把新命中的远缘序列加入 MSA → 重建一张新 PSSM → 再搜一轮。这个可以反复多轮的过程，正是 **PSI-BLAST**（Position Specific Iterative BLAST）名字里 "Iterative" 的含义。 [【跳转到 03:17】](https://www.youtube.com/watch?v=_G7r799GjL0&t=197)

![PSI-BLAST：每一轮把更远的序列加入 MSA，重建 PSSM](assets/Homology%20Modeling%20with%20PSI-BLAST,%20HHblits,%20HHpred%20and%20Modeller/00197.webp)

在 **MPI Bioinformatics Toolkit** 的 "Search" 标签下可以跑 PSI-BLAST：选目标数据库，设打分矩阵、E-value 阈值、迭代次数；跑完看命中列表（hits）和比对（alignments）。经验法则：**E-value 越低，匹配越可靠**；结果可以下载，也可以转发给其它程序继续用。 [【跳转到 03:49】](https://www.youtube.com/watch?v=_G7r799GjL0&t=229)

## 三、从 PSSM 到 HMM：补上"相邻位置"的依赖

### 3.1 PSSM 的短板

PSSM 只在"位置"这一层携带信息，**不考虑相邻位置之间的依赖**——而现实里相邻残基是相互影响的。解决办法是**隐马尔可夫模型（HMM，Hidden Markov Model）**：它在估计"每个位置出现每种氨基酸"的可能性时，会**依赖前一个位置的氨基酸**。 [【跳转到 04:42】](https://www.youtube.com/watch?v=_G7r799GjL0&t=282)

### 3.2 HMM 搜索的三个层级，灵敏度逐级上升

1. **序列搜 HMM 库**：拿一条新蛋白的序列，去搜结构域 HMM 库（如 Pfam，每个结构域由一个 HMM 表示），结果告诉我们序列里哪些区段匹配已知结构域； [【跳转到 05:12】](https://www.youtube.com/watch?v=_G7r799GjL0&t=312)
2. **HMM 搜序列库**：反过来拿查询 HMM 去搜序列数据库。这两类搜索的流行工具是 **HMMER**，通常比 PSI-BLAST 找得更远；
3. **HMM 搜 HMM（HMM-HMM）**：最灵敏的一档——拿查询 HMM 去搜目标 HMM 库，代表工具是 **HHsearch / HHblits**。

![HMM 搜索的三个层级：最灵敏的是 HMM-HMM（HHsearch/HHblits）](assets/Homology%20Modeling%20with%20PSI-BLAST,%20HHblits,%20HHpred%20and%20Modeller/00337.webp)

### 3.3 HHblits 实操

MPI 工具箱 "Search" 下的 **HHblits** 与 PSI-BLAST 用法几乎一致：设 E-value 阈值与迭代次数，跑示例序列，得到 hits、比对，并能把结果转发给其它程序。 [【跳转到 06:02】](https://www.youtube.com/watch?v=_G7r799GjL0&t=362)

## 四、HHpred：把灵敏搜索与结构信息打包成模板

目标是结构预测时，需要**灵敏搜索 + 结构信息**二合一，这就是 **HHpred**。它能替我们自动完成整条流水线： [【跳转到 06:44】](https://www.youtube.com/watch?v=_G7r799GjL0&t=404)

1. 用 PSI-BLAST 或 HHblits 搜同源序列；
2. 用命中构建多序列比对（MSA）；
3. 用 **PSIPRED** 给 MSA 注上二级结构预测；
4. 把带注释的 MSA 转成 HMM，去搜一个**同样带二级结构信息的 HMM 库**；
5. 命中的蛋白既与查询序列同源、又带结构信息——可直接用作**同源建模的模板**。

![HHpred 流水线：建 MSA → 二级结构注释 → 转 HMM → 搜结构库](assets/Homology%20Modeling%20with%20PSI-BLAST,%20HHblits,%20HHpred%20and%20Modeller/00438.webp)

实操要点：在 HHpred 页面选库——注意这些库**全都包含结构信息**，还可以把搜索限定到特定蛋白质组；"Parameters" 里选构建初始 MSA 的方法（HHblits 或 PSI-BLAST）以及前面见过的其它参数。 [【跳转到 07:56】](https://www.youtube.com/watch?v=_G7r799GjL0&t=476)

![HHpred 页面：选择含结构信息的数据库与参数](assets/Homology%20Modeling%20with%20PSI-BLAST,%20HHblits,%20HHpred%20and%20Modeller/00476.webp)

结果出来后，在 "Hits" 里勾选一个或多个命中，就可以把它们作为模板转发给同源建模程序。 [【跳转到 08:33】](https://www.youtube.com/watch?v=_G7r799GjL0&t=513)

![HHpred 命中列表：勾选结果即可转发](assets/Homology%20Modeling%20with%20PSI-BLAST,%20HHblits,%20HHpred%20and%20Modeller/00513.webp)

## 五、Modeller：用"空间约束满足"把模板变成模型

### 5.1 方法原理

**Modeller** 是常用的基于同源建模预测蛋白结构的工具。它和所有同源建模方法一样，基于一个假设：**从查询序列与模板序列之间的序列相似性，可以推断结构相似性**。实现方法是"**空间约束满足**"（satisfaction of spatial restraints）： [【跳转到 08:54】](https://www.youtube.com/watch?v=_G7r799GjL0&t=534)

- 空间约束可以基于多种结构性质，例如 Cα 原子之间的距离、主链二面角；
- Modeller 用大量已知结构的蛋白训练过，掌握了序列与结构性质之间的相关性；
- 查询序列与模板序列比对好之后，对比对区域逐一评估可能的空间约束，每个约束用**概率密度函数**建模——假设是：模板符合训练得到的期望值，查询序列也会如此；
- 可以用**多个模板**，获得对查询序列更好的覆盖；
- 不同约束的概率密度函数合并成一个分子的概率密度函数，再通过优化尽量满足所有约束。

![Modeller：把每个空间约束建成概率密度函数，再优化求模型](assets/Homology%20Modeling%20with%20PSI-BLAST,%20HHblits,%20HHpred%20and%20Modeller/00534.webp)

### 5.2 从 HHpred 结果到 PDB 模型

使用 Modeller（本地或网页版）前，需先到官网注册，获取一个**免费的学术 key**。回到 HHpred 结果页：勾选结果 → 点 "Model using selection" 生成 **PIR 文件**（Modeller 的输入格式）→ 点 "Forward to Modeller" → 在新页面填入 key（第一次填过之后会被记住）→ 得到预测结果 → 下载为 PDB 文件，进一步分析。 [【跳转到 10:25】](https://www.youtube.com/watch?v=_G7r799GjL0&t=625)

![从 HHpred 结果生成 PIR 文件，填入 key 转发给 Modeller](assets/Homology%20Modeling%20with%20PSI-BLAST,%20HHblits,%20HHpred%20and%20Modeller/00655.webp)

## 六、把流程跑稳：参数、验证与迭代

至此走完了整条流程：查询序列 → 找同源 → 用它们做结构预测。视频最后强调了两件事： [【跳转到 11:29】](https://www.youtube.com/watch?v=_G7r799GjL0&t=689)

- **盯住数据库与参数**：所选数据库和参数直接影响最终预测的质量；
- **验证模型**：例如用 **Ramachandran 图**检查主链构象是否合理，并评估模型是否符合预期的生物学功能。

实践中非常常见的做法是：换不同参数反复迭代、把多种方法组合使用，直到得到一个可信的模型。

![流程回顾与模型验证：Ramachandran 图检查构象合理性](assets/Homology%20Modeling%20with%20PSI-BLAST,%20HHblits,%20HHpred%20and%20Modeller/00694.webp)

## 小结

- 单条序列信息有限，结构/功能推断的起点是多序列比对（MSA）；
- BLAST 命中太相似 → 用 PSSM 概括 MSA → PSI-BLAST 迭代纳入远缘同源；
- PSSM 丢掉了相邻位置的依赖 → HMM 补上；HMM-HMM（HHblits / HHsearch）是灵敏度最高的一档；
- HHpred 自动完成"建 MSA → 注二级结构 → 转 HMM → 搜结构库"，命中即模板；
- Modeller 用"空间约束满足"法把模板变成 3D 模型，多模板可提高覆盖；
- 数据库与参数决定质量；模型要用 Ramachandran 图等手段验证，并按需迭代。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| MSA | 多序列比对：把同源序列排成列，相同/相似残基落进同一列 |
| PSSM | 位置特异性打分矩阵：行=位置，列=氨基酸，分数来自整条 MSA |
| PSI-BLAST | 用 PSSM 迭代搜索的 BLAST：每轮纳入更远同源、重建 PSSM |
| HMM | 隐马尔可夫模型：打分时考虑相邻位置依赖的统计模型 |
| HMMER | 序列↔HMM 库双向搜索的流行工具，比 PSI-BLAST 更灵敏 |
| HHblits / HHsearch | HMM-HMM 搜索工具，HHR 结果文件即由这类搜索产生 |
| HHpred | MPI 工具箱的一站式模板搜索：建 MSA → 注二级结构 → HMM-HMM 搜索 |
| 模板（template） | 同源建模中提供结构信息的已知结构蛋白 |
| Modeller | "空间约束满足"法同源建模工具，输出 PDB 模型 |
| Ramachandran 图 | 检查主链二面角是否落在合理区域的模型验证手段 |
