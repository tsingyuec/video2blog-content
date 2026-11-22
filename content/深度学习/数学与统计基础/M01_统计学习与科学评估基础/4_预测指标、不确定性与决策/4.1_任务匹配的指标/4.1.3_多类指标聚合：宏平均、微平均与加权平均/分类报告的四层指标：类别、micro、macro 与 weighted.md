# 分类报告的四层指标：类别、micro、macro 与 weighted

> 视频来源：[C09 多分类模型评价指标——TP、TN、FP、FN、混淆矩阵、准确率、精确率、召回率、F1-score、分类报告（Bilibili）](https://www.bilibili.com/video/BV1DkXuYSEgX/)，时长约 69 分钟（动手哥123）。本文基于视频演说图文稿整理，时间戳可跳转到对应讲解。

## 本讲要解决的核心问题（SCQA）

**背景**：二分类的准确率、精确率、召回率、F1 已经熟悉，换成 10 类手写数字识别，`classification_report` 一下吐出几十个数。

**冲突**：同一份预测，精确率可以报 0.8451（macro）、0.8455（weighted）、0.8425（micro）三个不同的值；到底哪个才是"模型的精确率"？

**疑问**：这三个数分别怎么算出来？分类报告里那些行（每类一行、accuracy、macro avg、weighted avg）各是什么？什么时候该看哪一行？

**回答（中心思想）**：多分类里每一个指标都有**四个层次**——先按类别各算一个，再用三种方式合成：micro 把各类 TP/FP/FN 累加后再算，macro 对类别直接求平均，weighted 按各类样本数（support）加权平均。三者的差别只在"合成"这一步，分子分母的定义完全相同。

## 一、多分类的 TP/FP/FN/TN 是按类别定义的

多分类的 TP、TN、FP、FN 与二分类类似，但定义更复杂：不再是简单的阳性/阴性，而是多个类别之间的比较。关键一句是——**多分类中的 TP、TN、FP、FN 是针对每个类别分别而言的**，换一个类别，这组数就变 [【跳转到 00:30】](https://www.bilibili.com/video/BV1DkXuYSEgX/?t=30)。

以三分类 A、B、C 为例，对类别 A [【跳转到 01:20】](https://www.bilibili.com/video/BV1DkXuYSEgX/?t=80)：

- **TP(A)**：被正确预测为 A 的样本数；
- **TN(A)**：真实标签不是 A、预测也不是 A 的样本数；
- **FP(A)**：实际为 B 或 C、却被错误预测为 A 的样本数；
- **FN(A)**：实际为 A、却被错误预测为 B 或 C 的样本数。

视频把命名规律总结成一句口诀：**T/F 表示预测对错，P/N 表示预测为该类 / 非该类** [【跳转到 01:45】](https://www.bilibili.com/video/BV1DkXuYSEgX/?t=105)。

![三分类下每个类别各有一套 TP/TN/FP/FN 的定义](assets/分类报告的四层指标：类别、micro、macro%20与%20weighted/00105.webp)

### 手算：15 个样本的三分类

视频给了一张 15 个样本的表（样本编号、真实标签、预测标签）[【跳转到 03:00】](https://www.bilibili.com/video/BV1DkXuYSEgX/?t=180)：

![15 个样本的真实标签与预测标签](assets/分类报告的四层指标：类别、micro、macro%20与%20weighted/00180.webp)

逐类数格子，得到 [【跳转到 06:20】](https://www.bilibili.com/video/BV1DkXuYSEgX/?t=380)：

| 类别 | TP | TN | FP | FN |
| --- | --- | --- | --- | --- |
| A | 4 | 8 | 2 | 1 |
| B | 3 | 8 | 2 | 2 |
| C | 3 | 9 | 1 | 2 |

三个类别的 TP 相加是 4+3+3 = 10，正对应 15 个样本里判对的 10 个。

## 二、混淆矩阵：行是真实，列是预测

把同一批样本汇总成混淆矩阵，行索引是 A、B、C，列名称也是 A、B、C [【跳转到 07:35】](https://www.bilibili.com/video/BV1DkXuYSEgX/?t=455)。对角线是各类的 TP；某一行的非对角元素之和是该类的 FN，某一列的非对角元素之和是该类的 FP。

![3×3 混淆矩阵：行是真实标签，列是预测标签](assets/分类报告的四层指标：类别、micro、macro%20与%20weighted/00455.webp)

换成真实数据集，视频用 sklearn 的 digits（1797 张 8×8 手写数字图，10 类）训练一棵决策树，再用 `confusion_matrix` 计算、用 seaborn 热力图可视化 [【跳转到 12:45】](https://www.bilibili.com/video/BV1DkXuYSEgX/?t=765)。10×10 的矩阵已经很难用眼睛读，这正是后面需要"聚合成一个数"的原因。

![digits 数据集的 10×10 混淆矩阵热力图](assets/分类报告的四层指标：类别、micro、macro%20与%20weighted/00765.webp)

## 三、准确率：对角线之和除以总数

多分类的准确率是所有正确预测的样本占总样本的比例 [【跳转到 13:40】](https://www.bilibili.com/video/BV1DkXuYSEgX/?t=820)：

**Accuracy = Σ TP_i / N**，其中 N 是样本总数，也就是混淆矩阵所有元素之和。

![准确率公式：所有类别 TP 求和，除以样本总数](assets/分类报告的四层指标：类别、micro、macro%20与%20weighted/00820.webp)

15 样本的例子：(4+3+3)/15 = 10/15 ≈ 0.667；digits 验证集上 `accuracy_score` 给出 0.8611 [【跳转到 15:20】](https://www.bilibili.com/video/BV1DkXuYSEgX/?t=920)。

## 四、精确率的四个层次

多分类的精确率有四个：**类别精确率、微平均（micro）、宏平均（macro）、加权平均（weighted）** [【跳转到 15:20】](https://www.bilibili.com/video/BV1DkXuYSEgX/?t=920)。前三个层次的定义如下 [【跳转到 16:10】](https://www.bilibili.com/video/BV1DkXuYSEgX/?t=970)：

- **类别**：Precision_i = TP_i / (TP_i + FP_i)，分母是"被判为类别 i 的全部样本"，即混淆矩阵第 i 列之和。
- **micro**：Micro Precision = Σ TP_i / Σ(TP_i + FP_i)。先把所有类别的 TP 与 FP 分别累加，再算一次除法。
- **macro**：Macro Precision = (1/C) Σ Precision_i。对各类精确率**直接求平均**，不看各类样本数 [【跳转到 17:00】](https://www.bilibili.com/video/BV1DkXuYSEgX/?t=1020)。
- **weighted**：Weighted Precision = Σ (Precision_i × support_i) / Σ support_i。以各类样本数 support 为权重做加权平均 [【跳转到 17:25】](https://www.bilibili.com/video/BV1DkXuYSEgX/?t=1045)。

![micro 精确率：先累加 TP 与 FP，再相除](assets/分类报告的四层指标：类别、micro、macro%20与%20weighted/00970.webp)

![macro 精确率：对各类精确率直接求平均，不考虑样本数](assets/分类报告的四层指标：类别、micro、macro%20与%20weighted/01045.webp)

### 手算：15 个样本上的四个精确率

类别精确率 [【跳转到 18:15】](https://www.bilibili.com/video/BV1DkXuYSEgX/?t=1095)：

- P(A) = 4/(4+2) = 4/6 ≈ 0.667
- P(B) = 3/(3+2) = 3/5 = 0.60
- P(C) = 3/(3+1) = 3/4 = 0.75

micro：分子 4+3+3 = 10，分母 (4+2)+(3+2)+(3+1) = 15，得 10/15 ≈ 0.667。macro：(0.667+0.60+0.75)/3 ≈ 0.673。weighted：三类各 5 个样本，权重相同，所以也是 (0.667×5+0.60×5+0.75×5)/15 ≈ 0.673。

这个例子有个陷阱：**三类样本数相同（各 5 个），macro 与 weighted 必然相等**，看不出两者的区别。要看区别必须换成样本数不等的真实数据。

### 在 digits 上看 macro 与 weighted 分岔

10 类数字的样本数并不相等：类别 0 有 53 个、类别 1 有 50 个、类别 2 有 47 个…… [【跳转到 32:25】](https://www.bilibili.com/video/BV1DkXuYSEgX/?t=1945)。于是 [【跳转到 32:00】](https://www.bilibili.com/video/BV1DkXuYSEgX/?t=1920)：

- `precision_score(average='macro')` = **0.8451**（各类精确率直接平均）
- `precision_score(average='weighted')` = **0.8455**（按 support 加权）
- `precision_score(average='micro')` = **0.8425**

![macro 与 weighted 的差别：weighted 用各类样本数作权重](assets/分类报告的四层指标：类别、micro、macro%20与%20weighted/01970.webp)

三个数都在 0.84–0.85 之间，但含义不同：micro 是"每一列都按样本数堆起来"的全局比例，macro 是"每个类别一票"，weighted 是"每个样本一票、但先按类别算再平均"。micro 精确率 455/540 与 accuracy 0.8425 是同一个数，原因见第八节。

## 五、召回率的四个层次

召回率的层次结构与精确率完全平行 [【跳转到 34:05】](https://www.bilibili.com/video/BV1DkXuYSEgX/?t=2045)：

- **类别**：Recall_i = TP_i / (TP_i + FN_i)，分母是"真实为类别 i 的全部样本"，即混淆矩阵第 i 行之和。
- **micro**：Micro Recall = Σ TP_i / Σ(TP_i + FN_i)。
- **macro**：Macro Recall = (1/C) Σ Recall_i。
- **weighted**：Weighted Recall = Σ (Recall_i × support_i) / Σ support_i。

![micro 召回率：先累加 TP 与 FN，再相除](assets/分类报告的四层指标：类别、micro、macro%20与%20weighted/02070.webp)

15 样本上手算：R(A) = 4/(4+1) = 0.80，R(B) = 3/(3+2) = 0.60，R(C) = 3/(3+2) = 0.60；micro = 10/15 ≈ 0.667；macro = (0.80+0.60+0.60)/3 ≈ 0.667；weighted 因三类样本数相同也是 0.667。

digits 上三者分岔：micro = 455/540 = **0.8425**（455 是对角线之和，540 是验证集样本数）[【跳转到 44:55】](https://www.bilibili.com/video/BV1DkXuYSEgX/?t=2695)；macro = **0.8390**；weighted = **0.8425** [【跳转到 46:10】](https://www.bilibili.com/video/BV1DkXuYSEgX/?t=2770)。

## 六、F1 的四个层次

F1 是精确率与召回率的调和平均，多分类同样有四个层次 [【跳转到 47:50】](https://www.bilibili.com/video/BV1DkXuYSEgX/?t=2870)：

- **类别**：F1_i = 2 × Precision_i × Recall_i / (Precision_i + Recall_i)。
- **micro**：先算 Micro Precision 与 Micro Recall，再对这两个数取调和平均。
- **macro**：Macro F1 = (1/C) Σ F1_i，对各类 F1 求平均。
- **weighted**：Weighted F1 = Σ (F1_i × support_i) / Σ support_i。

![micro F1 由 micro 精确率与 micro 召回率求得；macro F1 对各类 F1 求平均](assets/分类报告的四层指标：类别、micro、macro%20与%20weighted/03070.webp)

15 样本上手算 [【跳转到 52:00】](https://www.bilibili.com/video/BV1DkXuYSEgX/?t=3120)：F1(A) = 2×0.667×0.80/(0.667+0.80) ≈ 0.727，F1(B) = 0.60，F1(C) = 2×0.75×0.60/(0.75+0.60) ≈ 0.667。于是 micro 的 P 与 R 都是 10/15，micro F1 = 0.667；macro = (0.727+0.60+0.667)/3 ≈ 0.664；weighted 同样 ≈ 0.664。

digits 上：micro F1 = **0.8425**，macro F1 = **0.8408**，weighted F1 = **0.8429** [【跳转到 61:10】](https://www.bilibili.com/video/BV1DkXuYSEgX/?t=3670)。

## 七、分类报告怎么读

`classification_report` 把上面所有层次排进一张表，主要指标是精确率、召回率、F1 分数和支持度（support）[【跳转到 62:25】](https://www.bilibili.com/video/BV1DkXuYSEgX/?t=3745)。它的结构分三段 [【跳转到 64:30】](https://www.bilibili.com/video/BV1DkXuYSEgX/?t=3870)：

1. **每个类别一行**：类别 0 到 9 各自的 precision、recall、f1-score，最后一列 support 是该类真实样本数；
2. **accuracy 一行**：整体准确率，右侧的 support 是总样本数（540）；
3. **macro avg 与 weighted avg 两行**：分别是对类别求平均、按 support 加权平均得到的三个指标，support 同样是 540。

![分类报告：逐类一行，末尾是 accuracy、macro avg、weighted avg](assets/分类报告的四层指标：类别、micro、macro%20与%20weighted/03895.webp)

视频逐项做了对账 [【跳转到 67:00】](https://www.bilibili.com/video/BV1DkXuYSEgX/?t=4020)：`precision_score(average=None)` 返回的 10 个类别精确率与报告里的逐类行一一对应；`recall_score`、`f1_score` 同理；`value_counts()` 数出的 53、50、47…… 就是 support 列；accuracy 0.8425、macro avg 0.8451/0.8390/0.8408、weighted avg 0.8455/0.8425/0.8429 也都能用对应参数复现。

![逐类指标与报告行的一一对应关系](assets/分类报告的四层指标：类别、micro、macro%20与%20weighted/04120.webp)

## 八、四个层次怎么选

视频只讲了机制，没给选择规则。按上面的构造可以读出三条判读规则（**以下为本文推论，非视频原话**）：

1. **micro 与 accuracy 在这类单标签任务上是同一个数**：micro 精确率的分母 Σ(TP_i+FP_i) 是各列之和、micro 召回率的分母 Σ(TP_i+FN_i) 是各行之和，两者都等于总样本数 N，分子又都是 ΣTP_i（对角线之和），所以 micro P = micro R = accuracy。本讲 digits 上三者都是 0.8425，可以对照验证。因此 micro 高只说明"整体判对得多"，不说明每个类别都好。
2. **macro 把每个类别当一票**：一个只有 47 个样本的类别与有 66 个样本的类别权重相同。少数类判得差，macro 会明显掉下来，而 weighted 与 micro 会被大类稀释。所以**要看少数类是否失败，看逐类行与 macro**。
3. **weighted 回答的是"按样本平均，这个模型表现如何"**：它最接近"随机抽一个样本"的体验，但也最容易掩盖小类别的崩塌。报告里 macro 与 weighted 的差值，就是"小类别被牺牲程度"的一个粗指标。

## 小结

- 多分类的 TP/TN/FP/FN 按类别定义：TN/FP/FN 都要用"非该类"的视角去数。
- 混淆矩阵行是真实、列是预测；对角线是 TP，行内非对角是 FN，列内非对角是 FP。
- 每个指标四个层次：类别 → micro（先累加计数）→ macro（对类别求平均）→ weighted（按 support 加权）。
- macro 与 weighted 只有在各类样本数不等时才会分岔；样本数相等时两者必然相同。
- 分类报告 = 逐类行 + accuracy + macro avg + weighted avg；support 既是每类样本数，也是总样本数那一行的注脚。
- 聚合分数是入口不是结论：判断少数类是否失败，必须回到逐类行与 macro。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| 类别精确率 | TP_i/(TP_i+FP_i)，分母是混淆矩阵第 i 列之和 |
| 类别召回率 | TP_i/(TP_i+FN_i)，分母是混淆矩阵第 i 行之和 |
| Micro | 先把各类 TP/FP/FN 累加，再套一次公式 |
| Macro | 先算各类指标，再对类别直接求平均 |
| Weighted | 先算各类指标，再以各类样本数为权重求平均 |
| support | 该类别的真实样本数；也是分类报告最后一行总样本数 |
| 分类报告 | 逐类指标 + accuracy + macro avg + weighted avg 的汇总表 |