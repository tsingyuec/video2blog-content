# Bioexcel webinar #85： Modelling antibodies in the post-Alphafold era： where are we now？

> 视频来源：YouTube《Bioexcel webinar #85: Modelling antibodies in the post-Alphafold era: where are we now?》（BioExcel 卓越中心系列网络研讨会第 85 期，约 60 分钟）。讲者 Marco Giulini（乌得勒支大学 Bijvoet 中心，Alexander Bonvin 组——HADDOCK 开发团队），主持 Alessandra Villa。对应系列条目 **6.2.1 抗原结构（Protenix）**：拿到抗原结构之后，「抗体怎么结合抗原」是下一个问题——本讲给出「什么时候信 AlphaFold、什么时候转物理对接、H3 环怎么救」的完整决策地图，是姊妹篇《AlphaFold 3 Accuracy on Antibody Binding…》的「解决方案篇」。

## 本讲要解决的核心问题（SCQA）

**背景**：AlphaFold 问世后，抗体**可变域**的预测已基本解决——五个 CDR 环的平均误差只有约 1 埃。

**冲突**：抗体-**抗原复合物**仍有约一半建错。根本原因是抗体与抗原序列之间**不存在共进化**——AlphaFold 靠多序列比对（MSA）里的共变信号约束结构，但这套线索在抗体-抗原界面上失效；最关键的 CDR-H3 环平均误差近 3 埃、大量超过 4 埃（不可救药），且其构象大多在「非抗体世界」的 PDB 里从未出现过。

**疑问**：什么时候可以直接信 AF？不自信时怎么办？H3 环救得回来吗？纳米抗体（VHH）是不是更难？

**回答（中心思想）**：按「AF 置信度」三分流——自信就直接用；中间情形把 AF 结构当**模板**交给物理对接（HADDOCK3）；不自信就用物理对接 + 表位信息。H3 环则用 AlphaFlow（AF2 + 流匹配）做大规模构象采样，聚类成「簇扩散集成」再送 HADDOCK 对接——把成功率从 AF 基线的约 30% 提到约 80%。纳米抗体更难（CDR3 更长、框架也上界面），但组合 AF-Multimer + ImmuneBuilder 可把失败率压到 10%。

## 一、抗体建模的难点点：没有共进化

### 1.1 抗体 30 秒入门

抗体是 Y 形分子：深色的**重链** + 紫色的**轻链**；结合抗原的是 Y 臂尖端两个可变域上的**六个 CDR 环**（轻链三个、重链三个），高特异性全靠它们（[【跳转到 05:07】](https://www.youtube.com/watch?v=kLrlQE2ElsE&t=307)）。应用侧：目前已有超过 500 种单抗获批或处于临床研究，市场规模巨大。

![抗体的 Y 形结构与六个 CDR 环：轻链三环 + 重链三环，高特异性结合抗原的部位](assets/Bioexcel%20webinar%20%2385： Modelling%20antibodies%20in%20the%20post-Alphafold%20era： where%20are%20we%20now？/00337.webp)

### 1.2 为什么 AF 在界面上失灵

AlphaFold 类方法靠 MSA 中的**共进化**信号推断「序列上不相邻、空间上相邻」的氨基酸对，进而设置距离约束、解开结构（[【跳转到 07:36】](https://www.youtube.com/watch?v=kLrlQE2ElsE&t=456)）。但抗体与抗原**没有共进化**：是免疫系统单独「训练」出抗体去打抗原，两个分子此前从未见面——所以 AF 在复合物界面上表现弱。实验室经验法则：**AF 不自信时，转向基于物理的预测**，尤其当你对抗原表位（epitope，抗体在抗原上的结合区域）有了解时——从「精确的表位定位」到「只知道一个补丁」都行。

![MSA 共变信号如何变成距离约束——以及为什么抗体-抗原之间没有这种信号](assets/Bioexcel%20webinar%20%2385： Modelling%20antibodies%20in%20the%20post-Alphafold%20era： where%20are%20we%20now？/00481.webp)

## 二、HADDOCK3：模块化的物理对接

### 2.1 从固定管线到 20+ 模块

HADDOCK3 是 HADDOCK 的新一代：HADDOCK2 只有一条固定流程，HADDOCK3 把代码拆成 **20 多个可互换的模块**——精修、采样（真正的对接）、分析各有多套，用户自由组装工作流；pip 即可安装，代码与手册公开（[【跳转到 10:38】](https://www.youtube.com/watch?v=kLrlQE2ElsE&t=638)）。

![HADDOCK3 的模块化架构：精修 / 采样 / 分析模块可自由组合](assets/Bioexcel%20webinar%20%2385： Modelling%20antibodies%20in%20the%20post-Alphafold%20era： where%20are%20we%20now？/00638.webp)

### 2.2 抗体-抗原工作流

要点：抗体在 PDB 里几乎找不到「未结合态」，先用 AI 工具生成；**抗原优先用 PDB 实验结构或同源结构**——通常比 AF 预测更准；抗体输入**多个模型组成的集成（ensemble）**更好。流程（[【跳转到 11:44】](https://www.youtube.com/watch?v=kLrlQE2ElsE&t=704)）：

1. **刚性体对接**：抗体与抗原当刚体凑对，找能量局部极小；
2. **seletop**：挑出约 200 个模型；
3. **柔性精修（flexref）**：扭转角空间分子动力学，界面侧链与骨架松绑、能量最小化；
4. 短能量最小化 → **FCC 聚类**（共同接触比例）→ **CAPRI 分析**出图挑模型。

![HADDOCK3 抗体-抗原对接工作流：刚性对接 → 挑选 → 柔性精修 → 聚类与评估](assets/Bioexcel%20webinar%20%2385： Modelling%20antibodies%20in%20the%20post-Alphafold%20era： where%20are%20we%20now？/00704.webp)

### 2.3 基准：AF2 25% vs HADDOCK

在一个**不属于 AlphaFold 训练集**的抗体-抗原数据集上（当时还没有 AF3）：AlphaFold2 只有约 **25%** 正确；由「一般/很好界面知识」驱动的 HADDOCK 好得多，且**抗体集成输入**比单结构输入准确率更高（「真实表位」「宽松表位」两种场景都成立）（[【跳转到 17:29】](https://www.youtube.com/watch?v=kLrlQE2ElsE&t=1049)）。提醒：该协议为速度牺牲了采样，加大采样还会更好。

![基准结果：AF2 约 25% 正确；HADDOCK 在两种表位信息场景下大幅领先，ensemble 输入更好](assets/Bioexcel%20webinar%20%2385： Modelling%20antibodies%20in%20the%20post-Alphafold%20era： where%20are%20we%20now？/01049.webp)

## 三、中间情形：把 AF 当模板

第三种情形最微妙：AF 置信度「还行」——界面位置大致对，但接触质量不好。方案：**把 AF 结构作为 HADDOCK 对接的模板**。CAPRI 靶标 235（TCR-肽 MHC 复合物）实测：只用 AF 界面 RMSD 约 4 埃（勉强及格）；AF 作模板进 HADDOCK 后降到 **1.7 埃**（[【跳转到 19:51】](https://www.youtube.com/watch?v=kLrlQE2ElsE&t=1191)）。此法未做系统评测，但「AI 定大方向、物理修细节」的思路值得纳入工具箱。

## 四、H3 环：抗体建模的「狂野西部」

### 4.1 V(D)J 重组与非抗体世界

HADDOCK 也会失败的根源在 **CDR-H3 环**——抗原识别最关键的部位。它在基因层面位于 V、D、J 三个片段的交界处，序列多样性极大；已证明：H3 能采取的构象**大多数在全部「非抗体」PDB 结构里不存在**——抗体上有这么一块，长得像我们从未见过的东西（[【跳转到 21:43】](https://www.youtube.com/watch?v=kLrlQE2ElsE&t=1291)）。而且 H3 的 MSA 信号稀疏——那里的同源序列更短、更不像，信息量几乎为零。

![H3 环位于 V、D、J 基因片段交界：序列与结构多样性极大，且构象在非抗体 PDB 中不存在](assets/Bioexcel%20webinar%20%2385： Modelling%20antibodies%20in%20the%20post-Alphafold%20era： where%20are%20we%20now？/01291.webp)

### 4.2 五环已解决、H3 仍难

实测：其他五个环（H1、H2、L1、L2、L3）AF 平均误差约 **1 埃**——直接信就好；H3 平均近 **3 埃**，大量案例超过 4 埃——超过 4 埃基本救不回来（[【跳转到 22:49】](https://www.youtube.com/watch?v=kLrlQE2ElsE&t=1369)）。

![六个 CDR 环的预测误差分布：五个环约 1 埃（已解决），H3 平均近 3 埃、大量超过 4 埃](assets/Bioexcel%20webinar%20%2385： Modelling%20antibodies%20in%20the%20post-Alphafold%20era： where%20are%20we%20now？/01369.webp)

### 4.3 pLDDT 能「报警」

好消息：把 pLDDT（逐残基置信度）在 H3 上取平均，与实际精度相当相关——**平均 pLDDT > 80** 时预测很少错（多在 2 埃内）；**低于 80** 则多半是错的（[【跳转到 24:04】](https://www.youtube.com/watch?v=kLrlQE2ElsE&t=1444)）。也就是说：AF 在告诉你「这个 H3 别信」时，你该换方法。

![H3 环平均 pLDDT 与实际 RMSD 的相关：>80 基本可信，<80 多半要出事](assets/Bioexcel%20webinar%20%2385： Modelling%20antibodies%20in%20the%20post-Alphafold%20era： where%20are%20we%20now？/01444.webp)

## 五、给 AF「扩样」：从 MSA 截断到 AlphaFlow

### 5.1 三种旧思路

想多采样几套 H3 构象，先看 AF 自身：它的采样**非常同质**——「最异构」的几个模型其实长得一样，一个错全错（[【跳转到 24:54】](https://www.youtube.com/watch?v=kLrlQE2ElsE&t=1494)）。此前社区的扩样尝试：①**随机 MSA 子采样**（深度降 10~20 倍能出两种构象，砍太狠如只留 16 条会崩）；②**MSA 聚类**（在变形蛋白上常能同时找到两个构象盆地）；③**MassiveFold**（暴力跑 5000 个模型、调网络版本与参数，AF2.1 表现最好）——本质上都是「把 AF 逼出舒适区」，而 AF 本是为静态结构预测设计的。

### 5.2 AlphaFlow：AF + 流匹配

MIT 团队的预印本 **AlphaFlow** 把 AF2 与流匹配（flow matching）结合，将 AF 从回归模型改造成**生成式**框架：大幅提升输出多样性、同时保住 AF 精度（[【跳转到 28:46】](https://www.youtube.com/watch?v=kLrlQE2ElsE&t=1726)）。

### 5.3 实战：7MSQ 的 H3 环

以抗体 7MSQ 为例：橙色是实验构象——H3 往回折、贴在框架上；蓝色是 AF 预测——拉得老长、悬在溶剂里，错得离谱且救无可救（[【跳转到 30:06】](https://www.youtube.com/watch?v=kLrlQE2ElsE&t=1806)）。用 AlphaFlow 围绕采样：初期模型仍糟糕，但随后出现了与实验结构相像的构象——不完美，但方向对了。

![7MSQ 的 H3 环：橙色实验构象折回框架，蓝色 AF 预测长伸悬空——AlphaFlow 采样把它拉了回来](assets/Bioexcel%20webinar%20%2385： Modelling%20antibodies%20in%20the%20post-Alphafold%20era： where%20are%20we%20now？/01831.webp)

基准：每条重链生成 **10000** 个模型，AlphaFlow **总能**恢复出 RMSD<3 埃的 H3（可直接下游使用）；AF2 标准集成只有 25 个模型，常常全军覆没。但新问题来了：AlphaFlow 给出的 pLDDT 与真实精度**失去相关性**——好模型混在池子里，怎么挑？

## 六、簇扩散集成：采样 → 聚类 → 对接

### 6.1 工作流

Bonvin 组的答案（[【跳转到 31:53】](https://www.youtube.com/watch?v=kLrlQE2ElsE&t=1913)）：AF 对某抗体 H3 低置信 → 做 **H3 聚焦的 AlphaFlow 扩散采样**（数百种构象）→ **完全联结 + 最大熵结构聚类**（实测最优的聚类方式，保证集成里至少有一个好模型）→ 得到约 **10 个模型**的异构小集成——**簇扩散集成（cluster diffusion ensemble）**。

![簇扩散集成工作流：H3 低置信 → AlphaFlow 数百构象 → 完全联结 + 最大熵聚类 → 约 10 模型集成](assets/Bioexcel%20webinar%20%2385： Modelling%20antibodies%20in%20the%20post-Alphafold%20era： where%20are%20we%20now？/01938.webp)

### 6.2 成绩单

把簇扩散集成喂给 HADDOCK 做靶向对接，在两种表位信息场景下**全面超越 AF2 基线**：约 **80%** 的情况给出准确答案（AF 约 30%），「中等质量」模型数量也大增（[【跳转到 33:22】](https://www.youtube.com/watch?v=kLrlQE2ElsE&t=2002)）。成功案例：单抗-病毒糖蛋白复合物——抗原取向预测正确，H3 虽不完美但足以让对接落到正确界面。

![基准对比：簇扩散集成 + HADDOCK 约 80% 准确，AF2 基线约 30%；中等质量模型大增](assets/Bioexcel%20webinar%20%2385： Modelling%20antibodies%20in%20the%20post-Alphafold%20era： where%20are%20we%20now？/02002.webp)

### 6.3 AF3 到了，解决了吗？

AF3 大幅提高了复合物建模成功率（论文声称最高 **60%**），而且它弱化了 MSA 的重要性、内置扩散模块带来更多多样性——方向上对抗体友好。但在讲者的 9 个极难案例上，**AF3 只帮上 1 例**，且 H3 RMSD 只到 2 埃——重要一步，远未解决一切（[【跳转到 34:37】](https://www.youtube.com/watch?v=kLrlQE2ElsE&t=2077)）。

## 七、纳米抗体：更小也更难

### 7.1 VHH 是什么

纳米抗体（nanobody/VHH）是「最小抗原结合单元」：常规 IgG 有 12 个结构域、大多保守，真正结合抗原的只有 VH+VL；骆驼科动物演化中缺失了轻链，于是重链可变域单独扛起结合任务（[【跳转到 36:13】](https://www.youtube.com/watch?v=kLrlQE2ElsE&t=2173)）。它小（利于溶解度优化）、亲和力与特异性却不逊于抗体。序列上：CDR1 略长，**CDR3 长得多**；由于没有轻链，**框架残基**也更多地参与结合——CDR3 依旧是绝对主角。

![IgG 的 12 个结构域与骆驼科纳米抗体：只有重链可变域承担抗原结合](assets/Bioexcel%20webinar%20%2385： Modelling%20antibodies%20in%20the%20post-Alphafold%20era： where%20are%20we%20now？/02173.webp)

### 7.2 两种结合模式

把已知纳米抗体-抗原复合物分类，得到两簇：约三成只用 CDR 接触抗原（CDR3 必在场）；其余约七成是「协作式」——框架残基也大量出现在界面（[【跳转到 39:28】](https://www.youtube.com/watch?v=kLrlQE2ElsE&t=2368)）。

![纳米抗体的两种结合模式：纯 CDR 结合 vs 框架残基参与界面的协作式结合](assets/Bioexcel%20webinar%20%2385： Modelling%20antibodies%20in%20the%20post-Alphafold%20era： where%20are%20we%20now？/02368.webp)

### 7.3 基准：更难，但组合拳有效

纳米抗体基准（剔除 AF 训练集冗余、只用最新复合物）：所有受测方法约 **20~25%** 的案例搞不定 CDR3——比抗体更难。组合拳有效：**AF-Multimer + ImmuneBuilder** 集成后仅 **10%** 失败；有趣的是 AlphaFlow 在这里**没有**补益（[【跳转到 41:05】](https://www.youtube.com/watch?v=kLrlQE2ElsE&t=2465)）。对接场景里 Miguel 加了「突变扫描式」设定——只知道表位上 2 个残基、对抗纳米抗体一无所知，只用 CDR 环做主动残基：界面信息好时 HADDOCK 明显胜过 AF；信息一般时与 AF3 打平、远好于 AF2。注意：**两者成绩相当 ≠ 案例相同**——各有所长，结合使用才是正解（[【跳转到 42:43】](https://www.youtube.com/watch?v=kLrlQE2ElsE&t=2528)）。

![纳米抗体建模与对接基准：各方法 CDR3 失败率约 20~25%，AF-Multimer+ImmuneBuilder 组合降至 10%](assets/Bioexcel%20webinar%20%2385： Modelling%20antibodies%20in%20the%20post-Alphafold%20era： where%20are%20we%20now？/02528.webp)

反例警示：一个 AF3 给出很差模型的案例（灰色为正确复合物，AF3 的模型偏到一边），用 HADDOCK + 突变扫描式约束拿到了可直接用于抗体设计的好模型（[【跳转到 43:18】](https://www.youtube.com/watch?v=kLrlQE2ElsE&t=2573)）。

![AF3 的失败案例（红）与 HADDOCK + 突变扫描约束的好模型（对比灰色真值）](assets/Bioexcel%20webinar%20%2385： Modelling%20antibodies%20in%20the%20post-Alphafold%20era： where%20are%20we%20now？/02573.webp)

## 八、Q&A 精华与给我们的路线图

- **与 RFdiffusion 对比？** 没有——HADDOCK 处理的是序列已知的抗体，不做骨架生成（[【跳转到 45:30】](https://www.youtube.com/watch?v=kLrlQE2ElsE&t=2744)）；
- **同一抗原多个抗体怎么筛？** 至少要有一个（模糊的）表位定义才能用 HADDOCK 筛；零表位信息时先试 AF（从头端到端方法更适合），拿到候选再精修（[【跳转到 47:24】](https://www.youtube.com/watch?v=kLrlQE2ElsE&t=2794)）；
- **MD 采样 H3 可行吗？** 可行：BioExcel 有 GROMACS + HADDOCK 工作流（GROMACS 采样 H3 构象→聚类→HADDOCK），与 AlphaFlow 路线互补，只是 MD 更慢（[【跳转到 48:49】](https://www.youtube.com/watch?v=kLrlQE2ElsE&t=2904)）；
- **双抗怎么建？** 先分别预测每条 Fab 臂与抗原的结合，再同源建模/HADDOCK 合体（[【跳转到 50:31】](https://www.youtube.com/watch?v=kLrlQE2ElsE&t=3031)）；
- **「界面信息」要多细？** 一份「可能与抗体接触的氨基酸列表」（抗原上的一个补丁）就够；知道单一接触也能指定——HADDOCK 能吃任何类型的实验信息，这是它最大的威力；
- **性能**：Python 只是包装，计算内核在 CNS（Fortran 变体）；标准工作流约 1~2 小时 @10 核 CPU；AF3 更快但不免费商用；
- **糖相互作用**：HADDOCK 现在就支持（几乎所有糖都在支持列表，另有共价糖基化建模，教程见 bonvinlab.org）；
- **展望**：关注 Baker 实验室的轨迹——抗体/纳米抗体的结构预测已强大到「全计算 in silico 抗体设计流程」可行，能省大量实验时间；但当下，**AI（AF）+ 物理化学（HADDOCK/MD）+ 实验数据**三者结合仍是最稳的路线。

## 小结

- 抗体可变域五环已解决（~1 埃）；复合物约一半建错，根因是界面**无共进化信号**；
- 按 AF 置信度分流：自信→直接用；中间→AF 当模板进 HADDOCK（TCR 案例 4 埃→1.7 埃）；不自信→物理对接 + 表位信息；
- H3 环是硬骨头：V(D)J 交界、非抗体世界、MSA 无信号；平均 pLDDT>80 可信、<80 换方法；
- 扩样路线：AlphaFlow（AF2+流匹配）10,000 模型总能捞出 RMSD<3 埃的 H3，但 pLDDT 失效；
- 簇扩散集成（采样数百→完全联结+最大熵聚类→~10 模型）+ HADDOCK：约 30% → 80%；
- AF3 声称 60% 但在 9 个极难案例只帮 1；纳米抗体更难，AF-Multimer+ImmuneBuilder 组合把失败率压到 10%；
- HADDOCK 吃任何实验信息（残基列表即可）；1~2 小时 @10 核；糖相互作用已支持。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| CDR / H3 | 互补决定区，共 6 个；H3（重链第三环）由 V(D)J 重组产生，多样性最大、最难预测 |
| 共进化 | MSA 中成对协同突变→空间相邻的信号；AlphaFold 距离约束的来源，抗体-抗原界面缺失 |
| 表位（epitope） | 抗原上被抗体结合的区域；HADDOCK 的「主动残基」信息来源 |
| HADDOCK3 | 信息驱动的模块化物理对接平台；刚性对接→柔性精修→FCC 聚类→CAPRI 评估 |
| seletop / flexref | HADDOCK3 模块：挑选 top 模型（约 200）/ 扭转角空间 MD 柔性精修 |
| FCC | Fraction of Common Contacts，按共同接触比例聚类 |
| AlphaFlow | AF2 与流匹配结合的生成式改造：高多样性采样、保持 AF 精度（MIT 预印本） |
| 簇扩散集成 | H3 聚焦 AlphaFlow 采样 + 完全联结/最大熵聚类得到的小型异构集成（约 10 模型） |
| pLDDT | 逐残基置信度；H3 平均值与实际精度相关，>80 可信、<80 多半错 |
| ImmuneBuilder | 抗体/纳米抗体/TCR 专用快速建模工具（见 5.1.6）；与 AF-Multimer 组合成互补集成 |
| VHH / 纳米抗体 | 骆驼科缺失轻链后的重链可变域；最小抗原结合单元，CDR3 更长、框架参与结合 |
| 突变扫描式场景 | 只知表位少量残基（来自突变实验）+ 以 CDR 为主动残基的对接设定 |
