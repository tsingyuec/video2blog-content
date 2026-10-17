# 用 Python 从零构建抗菌肽活性预测模型：数据、特征、模型、评估全流程

> 视频来源：YouTube「Data Professor」频道端到端生物信息学教程《How to build a machine learning model to predict antimicrobial peptides (End-to-end Bioinformatics)》（Chanin Nantasenamat，35 分 45 秒）。
> 视频链接：[0NrFIGLwW0Q](https://www.youtube.com/watch?v=0NrFIGLwW0Q)，文中时间戳均可点击跳转。
> 配套代码：`Antimicrobial-Peptide-QSAR.ipynb`（Google Colab）；特征库 PFeature 来自 Raghava 课题组的 GitHub 仓库。

## 本讲要解决的核心问题（SCQA）

**背景**：抗菌肽（AMP）是对抗耐药菌的希望，机器学习可以"从氨基酸序列预测抗菌活性"。

**冲突**：想上手的人往往卡在链路不完整——序列怎么变成数字？数据从哪来、怎么清洗？模型怎么选、怎么评估才公平？

**疑问**：一个最小可复现的抗菌肽活性分类器，完整要几步？

**回答（中心思想）**：五步——① 准备 FASTA 格式的阳性/阴性数据集，用 CD-HIT 去冗余；② 用 PFeature 把序列变成氨基酸组成（AAC）／二肽组成（DPC）特征；③ 合并正负样本并打标签；④ 80/20 分层划分后，先用 LazyPredict 一键扫 30+ 模型，再用随机森林精做；⑤ 用 MCC、混淆矩阵、分类报告、ROC 与特征重要性做全面评估。

## 一、搭环境：conda + PFeature + CD-HIT

[【跳转到 00:18】](https://www.youtube.com/watch?v=0NrFIGLwW0Q&t=18)

![Colab 笔记本 Antimicrobial-Peptide-QSAR.ipynb：安装 conda 与 PFeature](assets/How%20to%20build%20a%20machine%20learning%20model%20to%20predict%20antimicrobial%20peptides%20%28End-to-end%20Bioinformatics%29/00048.webp)

先做一点铺垫：**肽是氨基酸连成的链**，最短两个氨基酸（二肽），可长到 50 个以上；本教程聚焦有抗菌活性的短肽。PFeature 库计算出的多肽分子性质，将作为机器学习模型的特征（features）——这是"把序列变成数字"的关键一步。环境三件套：

- **conda**（Python 3.7）：提供环境管理；
- **PFeature**：计算氨基酸/多肽分子性质的库，来自 Raghava 教授课题组；尚未发布到 pip，需要下载后进入目录用 `python setup.py install` 手动安装；
- **CD-HIT**：序列去冗余工具，`conda install -c bioconda cd-hit` 即可安装。

## 二、数据：FASTA 格式的阳/阴性集 + CD-HIT 去冗余

[【跳转到 05:03】](https://www.youtube.com/watch?v=0NrFIGLwW0Q&t=303)

![FASTA 格式的训练数据集：标识行 + 单字母氨基酸编码序列](assets/How%20to%20build%20a%20machine%20learning%20model%20to%20predict%20antimicrobial%20peptides%20%28End-to-end%20Bioinformatics%29/00303.webp)

- **数据来源**：发表于 *Molecular Therapy - Nucleic Acids* 的短肽抗菌肽数据集；教程只用其中的训练集，再在内部做 80/20 划分（用测试集做预测留给观众当作业）。
- **FASTA 格式**：每条序列以标识号/名称行开头，后跟单字母编码的肽序列——M 是甲硫氨酸（methionine）、S 是丝氨酸（serine）、G 是甘氨酸（glycine）、I 是异亮氨酸、A 是丙氨酸、R 是精氨酸、P 是脯氨酸……
- **标签约定**：阳性文件是 AMP（有抗菌活性），阴性文件是 non-AMP（无抗菌活性）。

[【跳转到 07:08】](https://www.youtube.com/watch?v=0NrFIGLwW0Q&t=428)

接下来用 **CD-HIT 以 0.99 相似度阈值去冗余**——这是肽类建模的标准协议：相似度高于阈值的冗余肽会被移除（阈值可以调低，移除会更激进）。结果：阳性 1445 → **1337**，阴性 1445 → **1422**。

两个提醒：去冗余后两类样本数不再相等（教程为简单起见不处理类别不平衡，观众可自行对比"不去冗余 vs CD-HIT"的模型差异）；但为了稳健性，强烈建议做去冗余，否则高度相似的序列会让模型产生偏置。

## 三、特征工程：把序列变成数字

[【跳转到 10:53】](https://www.youtube.com/watch?v=0NrFIGLwW0Q&t=653)

![PFeature 可计算的 19 类肽特征总表](assets/How%20to%20build%20a%20machine%20learning%20model%20to%20predict%20antimicrobial%20peptides%20%28End-to-end%20Bioinformatics%29/00653.webp)

PFeature 共提供 **19 类肽特征**；如果再算 N 端（N-terminal）/C 端（C-terminal）版本，可以扩展到 60~70 种——教程为简单起见只演示前两种：

- **AAC（氨基酸组成）**：20 种氨基酸各自在序列中的占比。例：一条约 30 氨基酸的肽里有 2 个 M（甲硫氨酸）→ 2/30 ≈ 6%。
- **DPC（二肽组成）**：相邻二肽的组合占比。20 × 20 = **400 维**。

[【跳转到 15:53】](https://www.youtube.com/watch?v=0NrFIGLwW0Q&t=953)

![AAC 计算结果：1337 行 × 20 列，每行一条肽](assets/How%20to%20build%20a%20machine%20learning%20model%20to%20predict%20antimicrobial%20peptides%20%28End-to-end%20Bioinformatics%29/00953.webp)

实现上用自定义函数 `aac()` 封装 PFeature 的 `aac_wp`（wp = whole peptide，整条肽；还可选 N 端/C 端变体）：读入 CD-HIT 处理后的 txt、输出 `aac.csv`，再用 pandas 读回。随后 `feature_calc()` 把阳性/阴性特征表合并：`pd.concat` **axis=0 上下堆叠**（正样本在上、负样本在下）加 class 标签列，再 **axis=1 左右拼接**（左边 20 列特征 + 右边 1 列标签），得到 21 列的建模数据框。

![合并后的建模数据框：20 列 AAC 特征 + 1 列类别标签](assets/How%20to%20build%20a%20machine%20learning%20model%20to%20predict%20antimicrobial%20peptides%20%28End-to-end%20Bioinformatics%29/01303.webp)

## 四、建模：先 LazyPredict 扫榜，再随机森林精做

[【跳转到 24:13】](https://www.youtube.com/watch?v=0NrFIGLwW0Q&t=1453)

把 20 列特征作为 X、class 列作为 Y（positive=1、negative=0），合计 **2759 条**样本。先做低方差过滤（VarianceThreshold）——AAC 特征下一列都没删（换成 DPC 特征可能会有低方差列被删）。再划分数据集：**80/20、random_state=42、stratify=y**——分层抽样保证正负比例在两个子集中一致。

![80/20 分层划分（stratify=y 保持正负比例）](assets/How%20to%20build%20a%20machine%20learning%20model%20to%20predict%20antimicrobial%20peptides%20%28End-to-end%20Bioinformatics%29/01553.webp)

**第一步扫榜：LazyPredict**。一行代码批量训练 30+ 个模型并排名。评估指标用自定义的 **MCC（马修斯相关系数）**——它同时兼顾混淆矩阵四个格子，对类别不平衡更稳健。训练集上表现最好的是随机森林，**MCC 0.86**。（视频里的小坑：train/test 一起跑会卡住，分开跑即可。）

![LazyPredict 批量对比 30+ 模型（MCC 指标）](assets/How%20to%20build%20a%20machine%20learning%20model%20to%20predict%20antimicrobial%20peptides%20%28End-to-end%20Bioinformatics%29/01653.webp)

**第二步精做：随机森林**。500 棵树，`rf.score` 直接算准确率；也可用 `rf.predict` 分别预测 train/test，再手算准确率、**MCC（测试集 0.4）**、混淆矩阵与分类报告（precision/recall/F1/support 分正负类逐项列出，可保存为报告文件）。

![ROC 曲线：训练集 AUC 0.99，测试集 0.74](assets/How%20to%20build%20a%20machine%20learning%20model%20to%20predict%20antimicrobial%20peptides%20%28End-to-end%20Bioinformatics%29/01992.webp)

**ROC 曲线**：训练集 AUC 0.99、测试集 0.74——两者差距是典型的过拟合信号，也是"数据量有限 + 简单组成特征"下该有的诚实水平。

![随机森林 Gini 特征重要性：K／D／E／L／G 最重要](assets/How%20to%20build%20a%20machine%20learning%20model%20to%20predict%20antimicrobial%20peptides%20%28End-to-end%20Bioinformatics%29/02067.webp)

**特征重要性（Gini 指数）**：最重要的五个氨基酸依次是 **K（赖氨酸）、D（天冬氨酸）、E（谷氨酸）、L（亮氨酸）、G（甘氨酸）**——带正电的 K 与疏水的 L 排在最前，与抗菌肽"正电荷 + 两亲性"的作用机制互相印证（可与本系列 CRIL 管线报告的经验判断环节对照：正电荷 + 两亲性正是作者手工写进管线的两个边界条件）。

## 五、这套教程给了你什么，边界在哪

- **给了**：一条可复现的最小链路——FASTA → CD-HIT → PFeature → 合并打标 → 分层划分 → LazyPredict 扫榜 → 随机森林精做 → MCC/混淆矩阵/分类报告/ROC/特征重要性全评估；
- **两个延伸作业**：把 19 类特征（或 DPC）补全成完整 notebook（作者的"众包"计划，欢迎提交 PR）；对比"不做 CD-HIT vs 做 CD-HIT"的模型差异；
- **边界要清楚**：它做的是"是否抗菌"的**二分类**，不预测 MIC 数值；若要进入"活性排序 + MIC 回归"的完整设计管线，可参考本系列 CRIL 报告一篇（分类 → 排序 → 回归 MIC → 增量学习），以及其中"阴性样本必须参与训练、数据量是第一瓶颈"的提醒。

## 小结

- 环境三件套：conda、PFeature（手动安装）、CD-HIT（bioconda）。
- 数据：*Molecular Therapy - Nucleic Acids* 短肽数据集的训练集；CD-HIT 0.99 去冗余后 1337 阳 / 1422 阴。
- 特征：AAC（20 维）+ DPC（400 维）把序列变成数字；`feature_calc` 拼接打标得到 2759 条建模数据。
- 建模：先 LazyPredict 30+ 模型扫榜（MCC 指标、训练集 RF 0.86），再随机森林（500 树）精做（测试集 MCC 0.4）。
- 评估：ROC-AUC 训练 0.99 vs 测试 0.74，过拟合信号诚实可见；Gini 重要性 K/D/E/L/G 与抗菌肽机理呼应。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| AMP | 抗菌肽（antimicrobial peptide），本教程的预测对象 |
| FASTA | `>标识行 + 单字母序列` 的文本格式，序列数据的标准交换格式 |
| CD-HIT | 按相似度阈值（0.99）去除冗余相似序列的聚类工具 |
| AAC / DPC | 氨基酸组成（20 维）／二肽组成（400 维）序列特征 |
| PFeature | Raghava 组的肽特征计算库，含 19 类特征（N/C 端变体可扩展至 60~70） |
| MCC | 马修斯相关系数：兼顾混淆矩阵四格的综合指标，对类别不平衡稳健 |
| LazyPredict | 一行代码批量训练 30+ 模型并排名的"扫榜"工具 |
| stratify | 划分数据集时保持各类别比例一致的分层抽样参数 |
| Gini 重要性 | 随机森林按"分裂不纯度下降"衡量的特征重要性 |
