# Dr. Francesca Grisoni - De novo drug design with chemical language models——像学语言一样学「写分子」

> 视频来源：YouTube《Dr. Francesca Grisoni -- De novo drug design with chemical language models》（59 分钟，Chalmers AI4Science 频道研讨会报告，含完整 Q&A）。
> 讲者：Francesca Grisoni（荷兰埃因霍温理工大学分子机器学习课题组 PI，2016 年于米兰大学获博士学位，先后在米兰、制药企业与苏黎世联邦理工 Gisbert Schneider 组工作；本讲多数工作完成于 ETH 时期）。
> 本文基于视频「图-字幕」文稿整理；关键数字与名称均可在文内时间戳处回看视频核对。

## 本讲要解决的核心问题（SCQA）

**背景**：化学宇宙（理论上可合成、可测试的所有分子）估计包含 **10^23 ~ 10^100 个分子**——比银河系的恒星、人体的细胞还多；而人类迄今只发现约 **10^4 个小分子药物**，化学宇宙几乎完全未被勘探 [【跳转到 03:56】](https://www.youtube.com/watch?v=t-7_etI6j9s&t=236)。

**冲突**：深度学习之前的从头设计全靠人工规则——枚举、反应规则、片段生长，规则一多就组合爆炸；而让模型自由生成，分子又往往「画得出、造不出」。

**疑问**：能不能让模型像学自然语言一样学会「写分子」，并且在**极少数据**（每类只有几个、几十个样本）下就能微调出真有活性的分子？

**回答（中心思想）**：把分子表示成 **SMILES 字符串**、用自回归语言模型学习「化学语言」；预训练学**语法**（化学有效性），少量活性分子微调学**语义**（生物活性）。两次湿实验（4/5 与 3/3 分子有活性）加上「设计-制造-测试」自动化流水线（>60% 合成成功率、约 70% 粗品有活性读出）证明这条路走得通；模型自带的**困惑度**还能直接当排序指标用。

![Francesca Grisoni 在 Chalmers AI4Science 研讨会报告](assets/Dr.%20Francesca%20Grisoni%20-%20De%20novo%20drug%20design%20with%20chemical%20language%20models/00000.webp)

## 一、为什么药物设计需要机器学习：fail early, fail cheap

药物开发管线极难走：**每一步都淘汰大量化合物，而且越往后越贵、越慢**。机器学习的价值在于把「失败」提前——尽早、尽量便宜地筛掉没希望的分子 [【跳转到 01:21】](https://www.youtube.com/watch?v=t-7_etI6j9s&t=81)。设计的难点还在于这是个**多目标优化**：分子要可合成、可溶、有生物活性，三者必须同时满足 [【跳转到 02:11】](https://www.youtube.com/watch?v=t-7_etI6j9s&t=131)。

![药物开发管线：每步都在淘汰化合物，越往后越贵](assets/Dr.%20Francesca%20Grisoni%20-%20De%20novo%20drug%20design%20with%20chemical%20language%20models/00236.webp)

## 二、两种映射：虚拟筛选（正向）与从头设计（逆向）

讲者把药物设计看成一个**映射问题**：化学结构空间 ↔ 性质空间 [【跳转到 04:43】](https://www.youtube.com/watch?v=t-7_etI6j9s&t=283)。

- **正向（虚拟筛选）**：用已知活性分子训练模型，给可购买分子库排序，买回排名靠前的测试——常规、成熟；
- **逆向（从头设计）**：先定性质，再反推结构——更难，因为一个性质对应**多种**结构，而且基于人工特征的模型很难「从一串数字倒推回分子」。

![映射问题：正向虚拟筛选 vs 逆向从头设计](assets/Dr.%20Francesca%20Grisoni%20-%20De%20novo%20drug%20design%20with%20chemical%20language%20models/00332.webp)

## 三、深度学习之前：规则式从头设计与组合爆炸

早期代表性方案有三类 [【跳转到 05:57】](https://www.youtube.com/watch?v=t-7_etI6j9s&t=357)：

1. **枚举法（如 GDB）**：从图结构出发逐步加化学规则，系统性枚举所有满足规则的分子——数量惊人，却**连人类已知测试过的分子都覆盖不全**；
2. **反应驱动设计**：砌块库 + 反应规则，聪明地选择组合而非全枚举；
3. **结构驱动设计**：从靶蛋白口袋出发组装片段。

它们的共同软肋：**规则重**——探索越大组合越爆炸。这正是深度学习的切入点。

![GDB 枚举：数量惊人却覆盖不全已知分子](assets/Dr.%20Francesca%20Grisoni%20-%20De%20novo%20drug%20design%20with%20chemical%20language%20models/00382.webp)

## 四、把分子当语言：SMILES + 自回归 LSTM

深度学习路线里最流行、也最有效的一支借自**自然语言处理**：分子是一种「化学语言」，有**语法**（原子怎么连接才化学有效）也有**语义**（原子种类、位置、连接方式决定性质）[【跳转到 08:25】](https://www.youtube.com/watch?v=t-7_etI6j9s&t=505)。

![分子是一种「化学语言」：语法=化学有效，语义=性质](assets/Dr.%20Francesca%20Grisoni%20-%20De%20novo%20drug%20design%20with%20chemical%20language%20models/00505.webp)

具体做法：把分子写成 **SMILES 字符串**，首尾加 GO / EOS 标记，one-hot 编码后喂给 LSTM，训练目标=**逐步预测下一个字符** [【跳转到 09:15】](https://www.youtube.com/watch?v=t-7_etI6j9s&t=555)。训练好后即可自回归生成：从 GO 出发，每步采样一个字符，新输出作为下一步输入，直到 EOS。采样常用**温度采样**——加权随机抽样，温度越高越随机 [【跳转到 10:30】](https://www.youtube.com/watch?v=t-7_etI6j9s&t=630)。

![SMILES + LSTM：逐字符预测下一个符号](assets/Dr.%20Francesca%20Grisoni%20-%20De%20novo%20drug%20design%20with%20chemical%20language%20models/00555.webp)

![温度采样：温度越高，生成越随机](assets/Dr.%20Francesca%20Grisoni%20-%20De%20novo%20drug%20design%20with%20chemical%20language%20models/00630.webp)

## 五、低数据怎么破：迁移学习（先学语法，再学语义）

神经网络爱吃数据，药物发现却是低数据领域。团队的系统答案是**迁移学习**：先在一个大而相关的数据集上预训练，再用小而聚焦的数据集微调 [【跳转到 10:55】](https://www.youtube.com/watch?v=t-7_etI6j9s&t=655)。

预训练语料取自 ChEMBL——所有标注为生物活性的分子（约 100 万+）。预训练后模型生成的字符串 **>90% 化学有效**——说明它学会了 SMILES 的「语法」[【跳转到 11:20】](https://www.youtube.com/watch?v=t-7_etI6j9s&t=680)。剩下的「语义」（活性）交给微调解决。

![迁移学习：ChEMBL 预训练学语法，微调学语义](assets/Dr.%20Francesca%20Grisoni%20-%20De%20novo%20drug%20design%20with%20chemical%20language%20models/00705.webp)

## 六、湿实验一：每类受体只给 25 条 SMILES，5 个合成 4 个有活性

2018 年的首次闭环至今仍是最有说服力的证据：预训练模型分别用 **25 条**已知 RXR、PPAR 受体调节剂的 SMILES 微调 → 采样 1000 条 → 药物化学家按内部工具排序后挑前 5 个合成测试 [【跳转到 12:35】](https://www.youtube.com/watch?v=t-7_etI6j9s&t=755)。

结果：**5 个中 4 个具备目标生物活性**，部分达到纳摩尔级。有意思的是，配体-受体结合本是带动态特征的 3D 过程，而模型只用了一维静态字符串表示就学到了这种关系 [【跳转到 13:25】](https://www.youtube.com/watch?v=t-7_etI6j9s&t=805)。

![湿实验一：25 条 SMILES 微调，5 个合成 4 个有活性](assets/Dr.%20Francesca%20Grisoni%20-%20De%20novo%20drug%20design%20with%20chemical%20language%20models/00805.webp)

## 七、更少数据的技巧与「天然产物」方向

**SMILES 增强**：同一分子可从任意非氢原子、沿任意方向线性化成字符串——一份训练数据变多条，配合温度因子调节，能显著提升生成分子的有效性、唯一性与新颖性 [【跳转到 14:37】](https://www.youtube.com/watch?v=t-7_etI6j9s&t=877)。

**天然产物**：超过一半的已批准药物直接来自天然产物或受其启发——骨架创新、药理性质理想，但难合成。团队的思路是「借天然产物的灵感，同时保持更高的合成可及性」[【跳转到 15:52】](https://www.youtube.com/watch?v=t-7_etI6j9s&t=952)。

一个重要观察：在微调过程中**每个 epoch 都采样**，生成分子的性质（如 sp3 碳分数 FSp3，与临床成功概率正相关、天然产物普遍富集）会在预训练集与微调集之间**连续过渡**——因此可以选择合适的停顿点，让分子「混合」两边性质 [【跳转到 17:39】](https://www.youtube.com/watch?v=t-7_etI6j9s&t=1059)。

![FSp3 分布随微调 epoch 在预训练集与微调集之间连续过渡](assets/Dr.%20Francesca%20Grisoni%20-%20De%20novo%20drug%20design%20with%20chemical%20language%20models/01084.webp)

## 八、湿实验二：beam search 失败 → 两段微调救回（3/3 全活性）

第二个湿实验目标是 LXR 受体的天然产物调节剂，采样策略换成了 **beam search**（每步只扩展概率最高的 k 条序列，天然带排序）——结果失败：分子**不可合成**，而且长得太像「巨型怪物」天然产物，贪心的 beam search 没了探索性 [【跳转到 18:54】](https://www.youtube.com/watch?v=t-7_etI6j9s&t=1134)。

解法很手工也很有效——**两段微调**：先用已知可合成的活性调节剂微调一次，再用 4 个天然产物微调一次，相当于「牵着模型的手」先拖到化学空间边缘再推向目标区域 [【跳转到 20:09】](https://www.youtube.com/watch?v=t-7_etI6j9s&t=1209)。这次生成的 3 个分子**全部成功合成、全部具备目标活性**。

![两段微调：先可合成调节剂、再天然产物——3/3 合成且全活性](assets/Dr.%20Francesca%20Grisoni%20-%20De%20novo%20drug%20design%20with%20chemical%20language%20models/01234.webp)

## 九、设计-制造-测试全自动：把 17 个反应「焊」进预训练

设计自动化只是三分之一，合成才是时间与成本瓶颈。团队把设计引擎接上**微流控辅助合成平台**——只能做 **17 种一步反应**、但完全自动 [【跳转到 22:14】](https://www.youtube.com/watch?v=t-7_etI6j9s&t=1334)。

整合思路：把 17 个反应用 SMARTS 写成过滤器，**预训练集先过滤成「可合成分子」**再训练——预训练语料决定了生成分布，设计出的分子自然更容易通过合成性过滤 [【跳转到 23:54】](https://www.youtube.com/watch?v=t-7_etI6j9s&t=1434)。

结果：生成分子大多**不在任何已知数据库**（新颖），还包含未参与训练的 LXR 调节剂（其中部分已被他人申请专利——模型抓住了真实的相关特征）；**>60% 的设计成功合成**；不纯化直接测粗反应混合物，**约 70% 显示预期活性读出**——可合成性与生物活性被同时满足 [【跳转到 24:44】](https://www.youtube.com/watch?v=t-7_etI6j9s&t=1484)。最终挑 14 个最有希望的纯化重测，多数确认活性，部分达到**亚微摩尔**级。

![17 个 SMARTS 反应写入预训练：设计天然带合成约束](assets/Dr.%20Francesca%20Grisoni%20-%20De%20novo%20drug%20design%20with%20chemical%20language%20models/01434.webp)

## 十、困惑度：让模型自己推荐「该测哪个」

换个角度想：模型真正生成的不是分子，而是**逐 token 的概率**。把每个字符的概率聚合起来，就是**困惑度**——衡量模型对这条字符串有多「确定」[【跳转到 25:48】](https://www.youtube.com/watch?v=t-7_etI6j9s&t=1548)。

两个实用结论：

1. **温度采样的分子困惑度低于 beam search**（越低越好）——加权随机反而产出模型更「确信」的分子；
2. **困惑度可直接当排序指标**，摆脱辅助打分函数；还能当**诊断工具**——微调后的模型理应觉得设计分子比微调前「更可能」，否则这个分子多半是预训练偏差的产物。

![困惑度：聚合逐 token 概率，可直接排序分子](assets/Dr.%20Francesca%20Grisoni%20-%20De%20novo%20drug%20design%20with%20chemical%20language%20models/01548.webp)

## 十一、更多玩法与清醒的边界

- **双向生成（BiModel）**：SMILES 本无方向（从任意非氢原子、任意方向起笔），让字符串**左右交替扩展**比单向从左到右更有效、更多样 [【跳转到 27:28】](https://www.youtube.com/watch?v=t-7_etI6j9s&t=1648)。

![双向生成：字符串左右交替扩展，有效性与多样性更好](assets/Dr.%20Francesca%20Grisoni%20-%20De%20novo%20drug%20design%20with%20chemical%20language%20models/01648.webp)
- **换个预训练目标**：用 ELECTRA 式判别预训练（识别被替换的 token）设计激酶抑制剂；把「字母表」从原子换成氨基酸，同样的框架直接用于**抗癌肽**设计 [【跳转到 28:43】](https://www.youtube.com/watch?v=t-7_etI6j9s&t=1723)。
- **清醒的短板**：对生成分子**缺乏精细的性质控制**——分布能对上微调集，精度还不够；团队正尝试操纵潜空间、做多目标设计（选择性 vs 多药理学），并与 IBM Zurich 合作把这套方法推向 de novo 酶设计 [【跳转到 29:58】](https://www.youtube.com/watch?v=t-7_etI6j9s&t=1798)。
- **activity cliff 的提醒**：团队学生系统对比了深度模型（图/SMILES）与经典描述符（ECFP）在「一原子改变、活性剧变」分子上的表现——**深度学习并不优于 ECFP**，且性能严重依赖数据集；相关工作发布了公开 benchmark [【跳转到 32:03】](https://www.youtube.com/watch?v=t-7_etI6j9s&t=1923)。

![activity cliff 对比：深度学习（图/SMILES）并不优于 ECFP 描述符](assets/Dr.%20Francesca%20Grisoni%20-%20De%20novo%20drug%20design%20with%20chemical%20language%20models/01923.webp)

## 十二、Q&A 精华

- **SMILES vs SELFIES vs InChI**：SMILES 诞生于 80 年代，本是为数据库存储设计、并非为机器学习；SELFIES 是改进尝试但性能差异不大（有研究显示两者都优于图生成）；InChI 语法太难学，基本被放弃。字符串仍是首选，因为**逐 token 拼接对生成最友好**，图结构从零生成、化学有效性难以保证 [【跳转到 39:30】](https://www.youtube.com/watch?v=t-7_etI6j9s&t=2370)。
- **与组合化学的差别**：反应驱动设计本质是「更聪明的组合枚举」；LSTM 则从头生成**聚焦库**——绕开组合爆炸，直接在感兴趣的窄区域采样 [【跳转到 41:53】](https://www.youtube.com/watch?v=t-7_etI6j9s&t=2513)。
- **怎么评估生成模型**：训练监控交叉熵；生成后看有效率、与微调集的相似性等——「没有菜谱，更像一门艺术」，最终检验要靠进实验室 [【跳转到 43:27】](https://www.youtube.com/watch?v=t-7_etI6j9s&t=2607)。
- **表示学习的价值**：在从头设计上无可替代（人工描述符根本无法生成分子）；在性质预测上暂时落后人工特征——毕竟 ECFP 这类描述符凝聚了四五十年的人类直觉——但长期看好可学习表征（不同靶标的相关特征不同，表征可随任务调整）[【跳转到 50:07】](https://www.youtube.com/watch?v=t-7_etI6j9s&t=3007)。
- **其他生成路线**：图直接生成（论文在增但性能尚不及字符串方法）、遗传算法、强化学习都有人探索；但**字符串路线拥有的湿实验成功案例最多**（至少在药物发现语境下）[【跳转到 51:48】](https://www.youtube.com/watch?v=t-7_etI6j9s&t=3108)。
- **多任务/元学习**：值得做——最终要的是「只调这个靶标、别激活其他靶标」（选择性）或反之的多药理学，课题组正往该方向走 [【跳转到 54:17】](https://www.youtube.com/watch?v=t-7_etI6j9s&t=3257)。

## 附：与「管线 C」前后步骤的衔接

本讲覆盖小分子药物发现管线「配体生成」的**SMILES 文本路线**：GenMol（SAFE 片段表征 + 掩码扩散）、LOGOS-Ligand（统一科学语法下的配体生成模态）等方法都属于这条谱系——把分子当 token 序列建模。姊妹篇《Opportunities & Challenges of Generative Models for Structure-based Drug Discovery｜Arne Schneuing》则覆盖口袋条件的 **3D 结构路线**（扩散/流模型直接在口袋里生成坐标）。两条路线殊途同归：产出候选后交给下游的分子对接（DiffDock）与 MD 精修（GROMACS）验证。
