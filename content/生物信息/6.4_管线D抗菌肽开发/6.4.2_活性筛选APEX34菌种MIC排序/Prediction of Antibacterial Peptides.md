# 抗菌肽活性预测二十年：AntiBP 系列的演进与肽药设计资源全景（G. P. S. Raghava 讲座）

> 视频来源：YouTube《Prediction of Antibacterial Peptides》，讲者 Gajendra P. S. Raghava（印度 IMTech 昌迪加尔教授，其团队维护着约 300 个免费开放的预测服务器与数据库），时长约 14 分半。
> 本篇是「管线 D：抗菌肽开发」**活性筛选步**（6.4.2）的配套视频，承担"经典 ML 活性预测方法"面：与 de la Fuente 讲座（APEX 本体与大规模挖掘，见同目录另一篇）、AMPFormer 报告（预测+生成一体基础模型）构成"经典方法 → 大规模挖掘 → 基础模型"的预测方法光谱。平台管线用 APEX 做 34 菌种 MIC 排序；本篇回答的是更古老也更基础的问题——**怎么判断一条肽是不是抗菌肽、该改哪个残基**。

## 本讲要解决的核心问题（SCQA）

**背景**：肽疗法不是噱头而是真实市场——团队建立的"FDA 批准治疗性肽/蛋白"数据库显示，2017 年已有 **160 个**获批品种，最近更新后数字**翻倍**。[【跳转到 02:27】](https://www.youtube.com/watch?v=6vA_aA00UNw&t=147)

**冲突**：要预测抗菌肽活性，机器学习要求**固定长度向量**，而肽长 15~60 氨基酸不等；相似性与基序类方法敏感度又差——怎么把"变长序列"变成"定长特征"？数据质量参差时预测等于垃圾进垃圾出。

**疑问**：能不能可靠预测"给定肽是否抗菌"？能不能告诉实验者"改哪个残基能变抗菌"？更大的肽里哪一段才是"抗菌区"？

**回答（中心思想）**：能。本讲拆解 AntiBP 系列二十年的演进——AntiBP（2006，N/C 端定长编码 + SVM/ANN/数量矩阵，92.8% 准确率）→ AntiBP2（2010，数据翻倍、分型）→ AntiBP3（革兰阳性/阴性/不定三模型分离，基于 APD3 等最大数据）；配套 design（穷举突变并预测最优）、protein scan（虚拟扫描蛋白找抗菌区）等用户导向模块；最后给出把肽推向市场的全套资源：毒性、致敏性、血脑屏障、半衰期与化学修饰后的性质/结构预测。[【跳转到 08:33】](https://www.youtube.com/watch?v=6vA_aA00UNw&t=513)

## 一、数据与第一个预测方法：AntiBP（2006）

### 1.1 数据源头：APD 数据库

团队自 2006 年起做抗菌肽预测，数据取自 **APD**（Antimicrobial Peptide Database）并做标准去冗余处理。Raghava 反复强调数据质量的第一性：**"预测质量取决于数据质量——垃圾进，垃圾出"**，而 APD 的注释质量极佳，这也是 AntiBP 系列一直锚定 APD 的原因。[【跳转到 03:32】](https://www.youtube.com/watch?v=6vA_aA00UNw&t=212)

### 1.2 定长难题的解法：两端取片段

抗菌肽长度 15~60 aa 不等，而 2006 年的机器学习（SVM 等）要固定长度向量。解法朴素而有效：**从 N 端取 5/10/15 个残基 + 从 C 端取片段**，同时剔除过短与过长肽，把变长序列压成定长输入。[【跳转到 04:22】](https://www.youtube.com/watch?v=6vA_aA00UNw&t=262)

![AntiBP 的定长编码：N 端 5/10/15 残基 + C 端片段](assets/Prediction%20of%20Antibacterial%20Peptides/00262.webp)

### 1.3 三种技术与残基偏好

用**支持向量机（SVM）**、**人工神经网络（ANN）**与**数量矩阵**（统计方法）三种技术建模，独立测试集准确率 **92.8%**。模型还给出残基偏好分析——哪些残基在抗菌肽中占优（如 Cys 突出）、哪些残基与不稳定性相关——为后续"设计"模块埋下伏笔。[【跳转到 04:47】](https://www.youtube.com/watch?v=6vA_aA00UNw&t=287)

![SVM + ANN + 数量矩阵：92.8% 准确率与残基偏好](assets/Prediction%20of%20Antibacterial%20Peptides/00287.webp)

## 二、从论文到服务：web server 与肽段映射

团队的理念是"**目标不是发论文，而是给社区提供服务**"：AntiBP 上线为 web server，用户提交序列即可判别"是不是抗菌肽"。更实用的一个模块是 **peptide mapping**——用户手里是一整个大蛋白时，预测**哪一段区域**负责抗菌活性；这篇论文多年后仍以每年三四十次的速度被引用。[【跳转到 05:42】](https://www.youtube.com/watch?v=6vA_aA00UNw&t=342)

![peptide mapping：预测蛋白中负责抗菌活性的区段](assets/Prediction%20of%20Antibacterial%20Peptides/00342.webp)

## 三、AntiBP2 → AntiBP3：数据、分型与三模型

- **AntiBP2（2010）**：抗菌肽数据逐年增长，新版本把训练数据翻倍，并开始关注抗菌肽的**类型/类别**。
- **AntiBP3**（撰稿时在审）：用上 APD3 等能拿到的**最大规模数据**；分析发现**革兰阳性、革兰阴性、革兰不定（variable）三类细菌需要不同的模型**，因此分别训练。[【跳转到 07:32】](https://www.youtube.com/watch?v=6vA_aA00UNw&t=452)
- 方法论上的取舍：相似性方法与基序方法都试过，**敏感度差**，最终回到机器学习路线。[【跳转到 08:33】](https://www.youtube.com/watch?v=6vA_aA00UNw&t=513)

![AntiBP3：革兰阳性/阴性/不定三类细菌分模型](assets/Prediction%20of%20Antibacterial%20Peptides/00477.webp)

## 四、面向实验者的设计模块

AntiBP3 不止于"批量判别"，几个模块直接对准实验者的日常问题：

- **design**：对给定肽**穷举所有可能的突变肽并逐一预测**，排出抗菌潜力最高的方案——回答"我该改哪个残基才能让它变得抗菌/更抗菌"；[【跳转到 08:55】](https://www.youtube.com/watch?v=6vA_aA00UNw&t=535)
- **protein scan（虚拟扫描）**：在完整蛋白中定位负责抗菌活性的区段；
- **motif scan / BLAST**：在自有肽/蛋白中搜索已知抗菌基序，或按相似性做同源检索。

![design 模块：穷举突变并预测最优抗菌变体](assets/Prediction%20of%20Antibacterial%20Peptides/00535.webp)

## 五、走向临床的资源栈：从毒性到修饰结构

Raghava 强调抗菌活性只是一环，肽要成药还得过一连串关卡，其团队几乎每关都建了预测工具：

- **递送与穿透**：肿瘤归巢肽（tumor homing peptides，用于药物递送定点）、细胞穿透肽（能不能进细胞）；[【跳转到 10:06】](https://www.youtube.com/watch?v=6vA_aA00UNw&t=606)
- **血脑屏障（BBB）**预测——中枢相关设计必备；[【跳转到 10:31】](https://www.youtube.com/watch?v=6vA_aA00UNw&t=631)
- **过敏性与毒性**：肽可能致敏、可能有血液毒性；**ToxinPred** 近年被大量使用——"在临床失败前预判毒性（细胞毒性）"。[【跳转到 11:46】](https://www.youtube.com/watch?v=6vA_aA00UNw&t=706)
- **半衰期与化学修饰**：天然肽在体液中半衰期有限，必须化学修饰（N 端修饰、C 端修饰、其他修饰）才能走向市场；团队开发了预测**修饰后肽**抗菌/溶血效力的方法；[【跳转到 10:56】](https://www.youtube.com/watch?v=6vA_aA00UNw&t=656)
- **修饰肽结构预测**：AlphaFold 等工具都不处理**化学修饰肽**的结构——这是缺口；团队的 PepStructure 模块专补"修饰后长什么样"。[【跳转到 12:36】](https://www.youtube.com/watch?v=6vA_aA00UNw&t=756)

![ToxinPred：临床失败前预判肽毒性](assets/Prediction%20of%20Antibacterial%20Peptides/00731.webp)

## 六、Q&A：预测的边界

观众问及 ToxinPred 等工具对个别肽（如 L37）预测不准的问题，Raghava 的回应坦率：预测给出的是**倾向/概率**，100% 准确不现实；团队能证明的是自家方法**比其他方法更准**。这提示平台管线的使用姿势：**预测值用于排序与优先级，而非替代湿实验验证**——与 6.4.2 的"MIC 排序 + 实验验证"闭环完全一致。[【跳转到 14:06】](https://www.youtube.com/watch?v=6vA_aA00UNw&t=846)

## 小结

本讲把"活性筛选"的计算地基铺陈得很清楚：**数据质量优先（APD 锚定）、变长序列定长化（两端取片段）、按菌种分型建模（G⁺/G⁻/variable）、面向实验者的设计与扫描模块、以及从活性到毒性/致敏/修饰结构的全链条资源**。对照管线 D：APEX（de la Fuente 讲座，同目录另一篇）代表"标准化实验数据 + 深度学习"的当代形态，AntiBP 系列则是同一问题二十年前的方法原型——两者共同回答"预测值怎么来"，而 AMPFormer（第三篇）回答"预测与生成如何合体"。
