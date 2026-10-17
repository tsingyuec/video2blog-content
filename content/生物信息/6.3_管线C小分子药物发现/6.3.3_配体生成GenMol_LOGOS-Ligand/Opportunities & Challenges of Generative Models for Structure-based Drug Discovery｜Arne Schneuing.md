# Opportunities & Challenges of Generative Models for Structure-based Drug Discovery｜Arne Schneuing——生成式模型如何「看着口袋画分子」，并一路走到湿实验

> 视频来源：YouTube《Opportunities & Challenges of Generative Models for Structure-based Drug Discovery | Arne Schneuing》（33 分 20 秒，Hi! PARIS 频道 AI 研讨会报告）。
> 讲者：Arne Schneuing（EPFL 蛋白设计与免疫工程实验室博士，报告系统回顾其博士期间的结构导向生成式药物设计工作，现创业继续该方向）。
> 本文基于视频「图-字幕」文稿整理；关键数字与名称均可在文内时间戳处回看视频核对。

## 本讲要解决的核心问题（SCQA）

**背景**：药物发现的主要战场是小分子——在所有 FDA 批准的药物里，**约 77% 是与蛋白结合的小分子** [【跳转到 01:00】](https://www.youtube.com/watch?v=bIAo1xMkPUQ&t=60)。与此同时，AlphaFold 等机器学习突破已彻底改变了蛋白结构预测（发表约 3 年后即获诺贝尔化学奖）[【跳转到 07:27】](https://www.youtube.com/watch?v=bIAo1xMkPUQ&t=447)。

**冲突**：药物研发效率却在反向滑坡——**Eroom 定律**显示每款获批新药的研发成本持续攀升，如今已超过 10 亿美元；数万候选分子走完漏斗通常只剩 1 个上市 [【跳转到 01:43】](https://www.youtube.com/watch?v=bIAo1xMkPUQ&t=103)。从头设计的分子还面临「**画得出、造不出**」的尴尬。

**疑问**：生成式模型能不能直接「看着口袋画分子」，并且画出来的分子真能合成、真有结合活性？

**回答（中心思想）**：能，但要依次闯过三关——**学会分子长什么样**（分布学习）、**按口袋与性质定向生成**（条件化 + 偏好优化）、**把合成约束焊进设计循环**（片段掩码 + 砌块可达性检查）。PGK1 与 KRAS 两个湿实验案例证明路线可行，但亲和力偏弱与数据稀缺仍是当前最硬的挑战。

![Arne Schneuing 在 Hi! PARIS AI 研讨会报告](assets/Opportunities%20%26%20Challenges%20of%20Generative%20Models%20for%20Structure-based%20Drug%20Discovery｜Arne%20Schneuing/00000.webp)

## 一、问题设定：给蛋白口袋找一把「钥匙」

讲者把药物发现设定为一个明确的场景：生物学靶点已经验证——我们知道哪个蛋白与疾病机制相关，现在的任务是**设计一个能结合它、并打断其功能的小分子**（经典例子：布洛芬）[【跳转到 00:35】](https://www.youtube.com/watch?v=bIAo1xMkPUQ&t=35)。

![FDA 批准药物约 77% 是小分子-蛋白结合](assets/Opportunities%20%26%20Challenges%20of%20Generative%20Models%20for%20Structure-based%20Drug%20Discovery｜Arne%20Schneuing/00035.webp)

为什么这件事这么难、这么贵？讲者给出三重解释：

1. **Eroom 定律**（Moore 定律的倒写）：制药研发效率呈指数下滑，每款新药成本已超 10 亿美元 [【跳转到 01:43】](https://www.youtube.com/watch?v=bIAo1xMkPUQ&t=103)。
2. **漏斗效应**：从数万候选出发，每过一道实验关卡就淘汰一批，走完靶点验证→命中发现→先导优化→临床前→临床的全程，往往只剩 1 个分子上市 [【跳转到 02:02】](https://www.youtube.com/watch?v=bIAo1xMkPUQ&t=122)。

![Eroom 定律：每款新药研发成本已超 10 亿美元（对数坐标）](assets/Opportunities%20%26%20Challenges%20of%20Generative%20Models%20for%20Structure-based%20Drug%20Discovery｜Arne%20Schneuing/00103.webp)
3. **生物学跨尺度**：时间上要覆盖飞秒到分钟，空间上从原子级纳米一直到人体米级——每个细胞有数百万蛋白、人体有数万亿细胞，第一性原理无法把这些尺度连起来建模 [【跳转到 03:17】](https://www.youtube.com/watch?v=bIAo1xMkPUQ&t=197)。

于是现实中的药物发现仍是**试错式**的：高通量筛选或 DNA 编码库（DEL）筛选，本质是「逐个分子放进功能实验里看读出」，先看有没有效果、再回头解释为什么——大公司能筛数百万分子，DEL 甚至能到数十亿，但相对整个化学空间仍是「沧海一粟」[【跳转到 04:07】](https://www.youtube.com/watch?v=bIAo1xMkPUQ&t=247)。

![试错式筛选：高通量筛选与 DNA 编码库](assets/Opportunities%20%26%20Challenges%20of%20Generative%20Models%20for%20Structure-based%20Drug%20Discovery｜Arne%20Schneuing/00247.webp)

## 二、换个视角：分子设计是一种「分布学习」

讲者的核心立场是：**分子设计不应被当成回归问题（给一个答案），而应是生成建模/分布学习问题**——学习所有可能分子的分布 P(X)，并从中采样 [【跳转到 05:47】](https://www.youtube.com/watch?v=bIAo1xMkPUQ&t=347)。这样有两个天然的好处：

- **无监督**：不必花海量时间人工标注数据；
- **多候选**：预测很好的单个分子未必在实验里好使，生成模型天然给你一批「都合理」的候选送去实验室检验。

![分子设计 = 从分布 P(X) 中采样](assets/Opportunities%20%26%20Challenges%20of%20Generative%20Models%20for%20Structure-based%20Drug%20Discovery｜Arne%20Schneuing/00347.webp)

承载这一思想的引擎是**扩散模型**：训练时对干净数据（分子结构）施加从弱到强的噪声，在每个噪声级别训练网络预测「干净结构」；推理时从一团随机点云出发，反复应用网络逐步去噪，得到输出分子 [【跳转到 08:17】](https://www.youtube.com/watch?v=bIAo1xMkPUQ&t=497)。

![扩散模型：加噪训练、逐步去噪生成](assets/Opportunities%20%26%20Challenges%20of%20Generative%20Models%20for%20Structure-based%20Drug%20Discovery｜Arne%20Schneuing/00497.webp)

## 三、DrugFlow：一次生成「坐标 + 原子类型 + 键 + 侧链」

讲者团队的 **DrugFlow** 模型把「多模态」做全了——一个去噪网络同时处理三类完全不同的数据 [【跳转到 09:32】](https://www.youtube.com/watch?v=bIAo1xMkPUQ&t=572)：

| 模态 | 性质 | 内容 |
| --- | --- | --- |
| 原子坐标 | 连续 | 配体与口袋中原子的三维位置 |
| 原子/键类型 | 离散 | 构成分子图的元素与化学键 |
| 蛋白侧链角 | 环形量（超环面上） | 结合构象中蛋白侧链的二面角 |

模型还自带一个类似 AlphaFold pLDDT 的功能：**为每个预测原子给出不确定度评分**，提示用户哪些原子可信、哪些需要复核 [【跳转到 09:57】](https://www.youtube.com/watch?v=bIAo1xMkPUQ&t=597)。

![DrugFlow 多模态同时生成：坐标、原子/键类型、侧链角](assets/Opportunities%20%26%20Challenges%20of%20Generative%20Models%20for%20Structure-based%20Drug%20Discovery｜Arne%20Schneuing/00572.webp)

## 四、怎么评估一个「分布学习器」？

既然把分子设计当成分布学习，评估也应按分布学习来做。高维分布没法直接比，团队的折中是**比性质分布**：把生成分子过一遍性质计算，得到一维分布后用 Wasserstein 距离、KL 散度等度量与训练集对比 [【跳转到 10:22】](https://www.youtube.com/watch?v=bIAo1xMkPUQ&t=622)。

更直观的可视化是：用预训练性质预测器的潜空间把分子投影到二维平面，蓝色区域为训练集、黑色线为模型采样。DrugFlow 覆盖了训练集分布的各个「峰」，表现好于对照方法；对同时生成的蛋白侧链 rotamer 分布也能匹配主要模式 [【跳转到 10:47】](https://www.youtube.com/watch?v=bIAo1xMkPUQ&t=647)。

![性质潜空间二维投影：模型样本（黑线）覆盖训练集（蓝区）各模式](assets/Opportunities%20%26%20Challenges%20of%20Generative%20Models%20for%20Structure-based%20Drug%20Discovery｜Arne%20Schneuing/00647.webp)

## 五、从「会画分子」到「按需画分子」：条件生成四条路线

无条件采样只覆盖漏斗的最前端（命中发现），实际设计还要**按性质定向**——用贝叶斯视角说，就是从 P(X|Y) 而不是 P(X) 采样，Y 可以是可溶性、亲和力等任何目标。讲者归纳了四条路线 [【跳转到 12:02】](https://www.youtube.com/watch?v=bIAo1xMkPUQ&t=722)：

1. **直接条件化训练**：训练数据本身带性质标签（条件于蛋白口袋结构就属于这类）；
2. **采样时注入知识**：classifier guidance、粒子法、beam search 等，在多步采样过程中引导方向；
3. **微调预训练模型**：先训练无条件模型，再用偏好优化（preference optimization）注入条件——这正是 ChatGPT 的调教思路；
4. **纯奖励引导优化**：强化学习或搜索类方法，把性质直接写进学习目标。

团队选了第三条。做法是：从参考模型采样 → 用「偏好」把样本分成赢/输两组（偏好甚至可以不是可微函数，人工判定也行）→ 微调时**提高赢者似然、压低输者似然**，并加正则防止偏离参考模型太远 [【跳转到 14:07】](https://www.youtube.com/watch?v=bIAo1xMkPUQ&t=847)。

![偏好优化：从参考模型采样，赢/输样本微调](assets/Opportunities%20%26%20Challenges%20of%20Generative%20Models%20for%20Structure-based%20Drug%20Discovery｜Arne%20Schneuing/00872.webp)

实验里用了四个「预言家」（oracle）：REOS 过滤器（子结构查询，二值）、QED 药物相似性（0~1 连续分，实验中取 0.5 为阈值）、结合亲和力代理、合成可及性代理。结论清晰：**只微调正样本有效但有限；把负样本显式喂进训练后提升巨大**；甚至四属性联合对齐的单模型（略逊于专家模型）也遵循同样规律 [【跳转到 16:12】](https://www.youtube.com/watch?v=bIAo1xMkPUQ&t=972)。

## 六、最大的拦路虎：设计得出，造不出

从头设计有个天然的尴尬：模型在理论上能覆盖整个化学空间，但**没人知道怎么把它做出来**。讲者用一张光谱图说明三种「分子来源」的位置 [【跳转到 17:27】](https://www.youtube.com/watch?v=bIAo1xMkPUQ&t=1047)：

- **物理库筛选**：分子肯定可得（本来就存在），但化学空间受限于库存；
- **从头生成**：化学空间理论全覆盖，但「可得性」最差；
- **按需虚拟化学空间**：中间道路——由砌块库 + 预验证反应**隐式定义**的空间，不枚举全部产物，反应产率高、成功率高。

![分子可得性光谱：筛选库 ↔ 按需虚拟空间 ↔ 从头生成](assets/Opportunities%20%26%20Challenges%20of%20Generative%20Models%20for%20Structure-based%20Drug%20Discovery｜Arne%20Schneuing/01072.webp)

要在这种隐式空间里搜索，常见两条路都有短板：**投影法**（把设计分子换成最近的可合成类似物——但你测的已经不是原设计）与**逆合成规划**（网络预测前体——不保证原料可得、反应可行、步数够少）[【跳转到 18:17】](https://www.youtube.com/watch?v=bIAo1xMkPUQ&t=1097)。团队于是选了更彻底的**自底向上**：把合成约束直接焊进设计过程。

## 七、LDDM：把合成约束「焊」进生成循环

在 DrugFlow 之后，团队训练了加「片段掩码」的版本（讲者称 LDDM，依字幕记录）：训练时先把分子切成片段，再像大语言模型掩码 token 那样**随机掩掉部分片段**要求模型补全 [【跳转到 20:15】](https://www.youtube.com/watch?v=bIAo1xMkPUQ&t=1215)。这样模型不仅认识蛋白口袋，还能**以分子片段为条件**生成。

![LDDM：片段掩码训练（类比 LLM 的 token 掩码）](assets/Opportunities%20%26%20Challenges%20of%20Generative%20Models%20for%20Structure-based%20Drug%20Discovery｜Arne%20Schneuing/01247.webp)

推理时跑一个**合成感知的迭代循环**：第 1 代无条件生成 → 与砌块库做子结构匹配，只保留匹配上的部分 → 条件化生成第 2 代 → 在反应数据库中检查「从第 1 代砌块出发能否经反应到达第 2 代的子结构」→ 重复直到满足成功判据。妙处在于：**每个设计附赠一条合成路线** [【跳转到 21:12】](https://www.youtube.com/watch?v=bIAo1xMkPUQ&t=1272)。

## 八、湿实验验证：PGK1 与 KRAS 两个案例

**案例一：PGK1**。设计数千个分子 → 过滤排序 → 订购计算指标最好的 6 个 → **4 个观察到结合信号**；多周期动力学测得最佳分子 **15 μM**；再用 NMR 谱位移确认结合在正确的结构域（这是个双域蛋白，理论上可能结合错域；尚无晶体结构最终确认结合模式）[【跳转到 23:17】](https://www.youtube.com/watch?v=bIAo1xMkPUQ&t=1397)。

![PGK1 案例：6 个订单 4 个有结合，最佳 15 μM](assets/Opportunities%20%26%20Challenges%20of%20Generative%20Models%20for%20Structure-based%20Drug%20Discovery｜Arne%20Schneuing/01397.webp)

**案例二：KRAS**。合成 5 个、3 个有结合信号，亲和力约 **86 μM**。讲者坦诚：作为药物候选远远太弱，但这已属于高通量筛选也能产出的「命中」级别——**纯计算起点第一次拿到湿实验阳性**的意义大于数字本身 [【跳转到 25:22】](https://www.youtube.com/watch?v=bIAo1xMkPUQ&t=1522)。

![KRAS 案例：5 合 3 中，约 86 μM——命中级别但远非先导](assets/Opportunities%20%26%20Challenges%20of%20Generative%20Models%20for%20Structure-based%20Drug%20Discovery｜Arne%20Schneuing/01547.webp)

## 九、讲者复盘的三大挑战

1. **亲和力必须提升**：计算药物发现的前提是「多迭代、少进实验室」，如今每次都要湿实验优化，前提就不成立 [【跳转到 25:47】](https://www.youtube.com/watch?v=bIAo1xMkPUQ&t=1547)。
2. **多模态调参困难**：每类模态各有去噪时间表，时间表之间的相互作用是连续超参数，极难调优 [【跳转到 26:37】](https://www.youtube.com/watch?v=bIAo1xMkPUQ&t=1597)。
3. **数据稀缺且带噪**：PDB 晶体约 5 万条，筛到「类药 + 去冗余」只剩约 1 万条；还有建模误差、低分辨率、「原子凭直觉摆放」等噪声。小分子口袋里参与相互作用的原子少，**放错一个原子就足以毁掉结合**（对比蛋白 binder 的大界面容错性高得多）[【跳转到 27:27】](https://www.youtube.com/watch?v=bIAo1xMkPUQ&t=1647)。

![数据稀缺且带噪：小分子口袋容错远低于蛋白界面](assets/Opportunities%20%26%20Challenges%20of%20Generative%20Models%20for%20Structure-based%20Drug%20Discovery｜Arne%20Schneuing/01647.webp)

由此引出一条重要告诫：**别盲目照搬大语言模型的缩放经验**——他们最大的模型只有约 1000 万参数，且从未观察到继续加大带来正收益；这个领域需要的是归纳偏置与领域专长 [【跳转到 27:52】](https://www.youtube.com/watch?v=bIAo1xMkPUQ&t=1672)。

## 十、结论与 Q&A 要点

**结论**：扩散模型是跨模态（图像/视频/分子）都稳健的生成框架；从无条件到条件的转换非常灵活；把合成约束内嵌进设计过程，就能让计算与湿实验形成闭环——而真实世界的反馈反过来会推动方法进步 [【跳转到 28:17】](https://www.youtube.com/watch?v=bIAo1xMkPUQ&t=1697)。

![结论页：扩散模型稳健灵活 + 合成约束闭环 + 领域专长关键](assets/Opportunities%20%26%20Challenges%20of%20Generative%20Models%20for%20Structure-based%20Drug%20Discovery｜Arne%20Schneuing/01697.webp)

**Q&A 精华**：

- **序贯蒙特卡洛（SMC）条件采样**试过：用「加噪-去噪」构造 proposal，可行但旋钮太多（噪声级别 + 接受准则），从未优于从纯高斯直接采样到干净数据 [【跳转到 28:54】](https://www.youtube.com/watch?v=bIAo1xMkPUQ&t=1734)。
- **偏好从哪来**：本研究全用计算 oracle（REOS 是天然二值、效果最好；QED 是连续分、取 0.5 阈值较任意）；创业后计划从用户使用反馈中收集化学家标注 [【跳转到 30:09】](https://www.youtube.com/watch?v=bIAo1xMkPUQ&t=1809)。
- **骨干网络**：E(3) 等变几何 GNN（消息传递式；节点全连接，某种意义上更接近 transformer）——在极少数据下等变性比数据增强更有效 [【跳转到 30:22】](https://www.youtube.com/watch?v=bIAo1xMkPUQ&t=1822)。

## 附：与「管线 C」前后步骤的衔接

这篇报告正好填上小分子药物发现管线的「配体生成」一环：上游的**靶标结构获取**与**口袋发现**产出口袋坐标，本讲的 DrugFlow/LDDM 在口袋里生成带不确定度评分、附合成路线的候选配体；下游的**分子对接**（如 DiffDock）与 **MD 精修**（GROMACS）再对候选做验证与稳定性评估。两条生成路线的另一翼——SMILES 化学语言模型——见同目录姊妹篇《Dr. Francesca Grisoni - De novo drug design with chemical language models》。
