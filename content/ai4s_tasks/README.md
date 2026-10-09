# 系列：AI for Science 核心任务（ai4s_tasks）

- **平台**：Bilibili / YouTube
- **视频数**：6
- **主题**：本系列围绕 **AI for Science（AI4S）中最具代表性的六类科学任务**——逆合成预测、蛋白质结合位点识别、生成式分子设计、MOF 材料生成、蛋白质定向进化、抗体 CDR 设计——各选一个讲解视频整理成中文图文博客，讲清**每个任务在做什么、为什么难、AI 怎么做**。这六类任务正是通义实验室统一科学模型 **LOGOS**（Language Of Generative Objects in Science）所覆盖的下游方向，可作为理解「一个模型如何统一自然科学生成任务」的背景读物。

> 说明：各篇博客严格基于对应视频的「图-字幕」视频演说图文稿撰写，字幕来自 B 站 AI 字幕 / YouTube 自动字幕，已逐窗口通顺化并纠正专业术语错拼；文中时间戳可跳转到原视频对应位置核查。

## 视频索引

| 任务 | 平台 | 视频键 | 标题 | 时长 | 博客 | 配图 | 原视频 |
| --- | --- | --- | --- | ---: | --- | ---: | --- |
| 逆合成预测 | YouTube | I2cdBHaWDxE | Retrosynthesis in the AI era: opportunities and pitfalls | 42:21 | [博客](blog/逆合成预测：AI%20如何反推分子合成路线.md) | 16 | [YouTube](https://www.youtube.com/watch?v=I2cdBHaWDxE) |
| 蛋白质结合位点识别 | YouTube | OloPSKhdrJA | From Sequence to Target: AI-Powered Protein Modeling & Binding Site Prediction | 46:41 | [博客](blog/蛋白质结合位点识别：AI%20如何找到可成药口袋.md) | 15 | [YouTube](https://www.youtube.com/watch?v=OloPSKhdrJA) |
| 生成式分子设计 | Bilibili | BV18hsFzbEEv | 【AI+分子】基于机器学习的分子生成技术概述 | 17:47 | [博客](blog/生成式分子设计：机器学习如何创造新药分子.md) | 15 | [Bilibili](https://www.bilibili.com/video/BV18hsFzbEEv/) |
| MOF 材料生成 | Bilibili | BV1htawz9EqX | 机器学习 + MOF 全景解析：任务、性质、数据集、方法与未来方向 | 9:07 | [博客](blog/MOF%20材料生成：机器学习如何设计金属有机框架.md) | 12 | [Bilibili](https://www.bilibili.com/video/BV1htawz9EqX/) |
| 蛋白质定向进化 | Bilibili | BV1nJ4m1M7ea | 基于预训练的蛋白质工程通用人工智能 | 21:55 | [博客](blog/蛋白质定向进化：预训练模型如何辅助蛋白工程.md) | 16 | [Bilibili](https://www.bilibili.com/video/BV1nJ4m1M7ea/) |
| 抗体 CDR 设计 | YouTube | kG23dCuv3Qk | RosettaAntibodyDesign (RAbD): Introduction – Rosetta Workshop 2021 | 7:02 | [博客](blog/抗体%20CDR%20设计：AI%20如何设计抗体结合区.md) | 10 | [YouTube](https://www.youtube.com/watch?v=kG23dCuv3Qk) |

## 六篇博客速览

### 1. 逆合成预测：AI 如何反推分子合成路线
> 给目标分子，反推「用哪些原料、按什么顺序反应」才能合成它。

- 逆合成 = 把目标分子倒着拆回「能买到的原料」；核心是「在哪切开 + 按什么顺序切」的搜索问题
- 两条技术路线：专家规则 vs 数据驱动（Iktos 选了后者）
- 断键预测三件套：模板法（把反应规则写成 SMARTS 正则）→ 数据准备（清洗/原子映射/提模板）→ 神经网络把「产物→用哪些模板」当分类问题
- 三大坑：反应可行性、化学选择性、保护基策略
- 搜索用「强化学习 + 带记忆的蒙特卡洛树搜索」；Spaya 网页/API 每分子约 3 秒

### 2. 蛋白质结合位点识别：AI 如何找到可成药口袋
> 只有一条氨基酸序列，如何拿到一个经过验证、并标注了可成药口袋的蛋白结构？

- 以结核潜伏期关键酶（异柠檬酸裂解酶）为靶点，串起完整流程
- 五步：UniProt 拿序列 → AlphaFold 预测结构 → PyMOL 补齐缺失辅因子并验证 → Ramachandran 图/能量最小化 → DeepSite AI 预测结合口袋
- AlphaFold 仅凭序列建模（ranking score 0.98）；DeepSite 用神经网络直接输出口袋分数、中心坐标与残基
- 强调「结构要既几何合理又能量稳定，对接才可信」

### 3. 生成式分子设计：机器学习如何创造新药分子
> 从「筛选已知分子库」转向「直接创造满足性质的新分子」。

- 四重局限驱动生成式方法；分子表征分字符串（SMILES/SELFIES）、拓扑图、几何图
- 三大框架：分布学习（GraphVAE）、条件生成（MolGAN）、分子优化
- 五大深度生成模型：VAE、GAN、归一化流、自回归、扩散；生成/优化策略与评价指标（有效性、唯一性、新颖性、QED、SA score、对接）

### 4. MOF 材料生成：机器学习如何设计金属有机框架
> 原子尺度的「乐高积木」MOF，如何在无限化学空间里找到目标材料？

- MOF = 金属节点 + 有机连接体；超高孔隙率、结构可调
- 核心矛盾是「选择」：已知十万余种、假设超百万种，试错等于在无限谷仓里找针
- ML 四类任务：性能预测、高通量筛选、逆向设计、合成预测；底层是「描述符→数据集→算法」
- 数据是燃料：CoRE MOF / hMOF / QMOF；三大瓶颈：数据、黑箱、可合成性；终局是与科学家的深度融合

### 5. 蛋白质定向进化：预训练模型如何辅助蛋白工程
> 给天然蛋白换几个氨基酸，把它改成工业/医药能用的产品。

- 难点：序列空间天文数字、实验成本高；且「结构 ≠ 功能」，存在上位效应（1+1<2）
- 解法：跳过结构、面向功能直接设计序列——预训练学自然规律 → 功能标注监督学习 → 少量湿实验微调，干湿闭环
- 阳性率可达 30%~50%（随机筛选不到 1%）；七个真实案例横跨 Cas12a、抗体、PETase 等

### 6. 抗体 CDR 设计：AI 如何设计抗体结合区
> 抗体靠 CDR 决定结合特异性，如何把开放式的环设计变成可搜索的问题？

- RAbD（RosettaAntibodyDesign）把 CDR 环设计变成「从合理形状目录里挑选 + 迭代」
- 两块基石：实验解析的 CDR 环聚类数据库（保证环形状） + PyIgClassify（统一编号/分类）
- 核心算法：外层换环、内层改序列的**双层蒙特卡洛**搜索
- 实验验证：抗蜂毒、抗 gp120 真实复合物中确有设计提高结合力

## 核心知识点速览

- **六大任务同源**：都是「给定约束、生成/搜索满足化学或生物学规律的实体」，与 LOGOS 把科学对象编码为统一 token 序列、用 next-token prediction 统一建模的思路一脉相承。
- **两种设计范式**：正向（性质预测/筛选）与逆向（性质→结构生成）。逆合成、MOF 生成、配体生成都属「从结果到原因」的逆向搜索。
- **数据是共同瓶颈**：逆合成的脏反应数据清洗、结合位点的实验结构稀缺、MOF 的高质量数据缺乏、蛋白工程的湿实验通量受限——数据质量普遍决定方法上限。
- **表示决定上限**：分子用 SMILES/图/几何、蛋白用序列/结构、MOF 用节点-连接体——「怎么表示」直接决定模型能学到什么。
- **落地都要闭环**：搜索/生成只是第一步，可行性、可合成性、湿实验验证才是真正的门槛。

## 引用说明

- 逆合成：Chemspace 讲座（YouTube I2cdBHaWDxE）
- 结合位点识别：AlphaFold + PyMOL + DeepSite 实操讲座（YouTube OloPSKhdrJA）
- 分子生成：B 站「小赵老师」机器学习分子生成概述（BV18hsFzbEEv）
- MOF：B 站机器学习 + MOF 科普（BV1htawz9EqX）
- 蛋白工程：B 站「基于预训练的蛋白质工程通用人工智能」（BV1nJ4m1M7ea）
- 抗体设计：Rosetta Workshop 2021（YouTube kG23dCuv3Qk）
