# ProteinDJ：把「出骨架 → 配序列 → 回折验证 → 出报告」串成一条开源流水线，让 binder 设计告别 Python 黑带

> 视频来源：[ProteinDJ: A modular and open-source framework for protein design workflows](https://www.youtube.com/watch?v=xwvF62HxaF0)（Australian BioCommons「结构生物学计算」系列网研会，约 56 分钟；主讲人 Dr. Josh Hardy——WEHI 高级研究员、冷冻电镜专家，NHMRC 新兴领袖奖学金获得者，Monash 大学博士，2020 年起在 WEHI 研究假激酶、细胞因子受体与微管相关蛋白的结构；ProteinDJ 由 Josh 与软件工程背景的 Dylan 合作开发，代码与预印本见其 GitHub）

## 本讲要解决的核心问题（SCQA）

**背景**：binder 设计「三部曲」——RFdiffusion 生成骨架、ProteinMPNN 配序列、AlphaFold2 回折验证——工具全部开源，上一讲的 ChuA 案例也证明了：设计模型可以和实验结构对得上。单看每个工具，教程和实操视频都不缺。

**冲突**：但把它们**串成一条能日常跑的流水线**是另一回事。第一，binder 设计失败率极高：结构预测通过率随靶标和参数在 0–5% 之间波动，你必须生成成百上千个设计；第二，软件像游戏里的「科技树」——要逐级解锁、逐个配环境，讲者原话是「感觉需要一条 Python 黑带才能跑起来」，装好了还可能跑错资源（该用 GPU 的程序在 CPU 上慢 10 倍）。

**疑问**：能不能有一条**开箱即用、资源高效、参数透明、还能容纳未来新工具**的标准流水线，把「设计 → 序列 → 回折验证 → 报告」一站式做完？

**回答（中心思想）**：ProteinDJ 给出了肯定答案。它用「容器 + Nextflow + Python」三件套，把 binder 设计组织成四个阶段：**RFdiffusion 用四种模式出骨架**（de novo / fold conditioning / partial diffusion / motif scaffolding）→ **两个程序配序列**（ProteinMPNN+FastRelax / full-atom MPNN）→ **两个程序回折验证**（AlphaFold2 initial guess / Boltz）→ **分析报告**（CSV 元数据表）。加上早期骨架过滤、BindSweeper 参数扫描和 Seqera 网页界面，一个不写代码的实验生物学家用两步安装就能在 HPC 上批量设计 binder。本次报告还附赠了上手建议和这个项目一年的开发幕后。

## 一、binder 设计为什么难：两大拦路虎

这次网研会是 Australian BioCommons 面向澳大利亚结构生物学计算社区做的系列讲座之一，主题是「用深度学习设计定制蛋白 binder」。主讲人 Josh 自嘲是这条路上的「过来人」：他一年前对 RFdiffusion 一无所知，正是踩遍了坑，才和 Dylan 一起做出了 ProteinDJ。先看两个所有人都绕不开的拦路虎。

### 1.1 拦路虎一：失败率——结构预测通过率只有 0–5%

binder（结合蛋白）是蛋白设计的一个「子门类」：创造新的蛋白去结合另外的蛋白。它的用途横跨生物、化学、医学——抗毒素、抗蛇毒血清、调控受体信号、阻断病毒进入细胞，以及 CRISPR、抗体、癌症疗法等更进阶的方向 [【跳转到 04:55】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=295)。

![binder 的应用全景：从抗毒素、抗蛇毒到受体调控、抗病毒、抗体与癌症疗法](assets/ProteinDJ：%20A%20modular%20and%20open-source%20framework%20for%20protein%20design%20workflows/00295.webp)

但好用不等于好做。深度学习之前，做一个能用的 binder 需要表达**成百上千**个蛋白才能碰上一个成功的；如今结构预测方法提高了成功率，但湿实验阶段仍然要测**几十个**设计 [【跳转到 07:47】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=467)。更麻烦的是，即便只看「回折验证」这一步，通过率也只有 **0–5%**——取决于你的靶标和参数设置。所以你必须生成成百上千个设计，才够送进湿实验室、最终拿到一个真正能用的 binder。

失败还有两种典型死法（来自一篇 Nature Communications 论文的总结图）[【跳转到 08:12】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=492)：

![binder 设计的两大失败类型：左为 binder 自身没有折叠成设计的构象，右为 binder 没有按预期与靶标结合](assets/ProteinDJ：%20A%20modular%20and%20open-source%20framework%20for%20protein%20design%20workflows/00517.webp)

- **类型一：binder 自身没折叠**——实际折叠方式与设计的骨架对不上；
- **类型二：binder 没按预期结合**——折叠是对的，但与靶标的相互作用方式不对，或者根本不结合。

### 1.2 拦路虎二：软件「科技树」——从安装到跑快，处处是坑

第二个挑战对新手尤其劝退：要在脑中理清一大堆软件，感觉就像游戏里的科技树，要**逐级解锁**才能到达「设计出 binder」的终点 [【跳转到 08:37】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=517)。很多程序需要安装特定的运行环境；团队里的人形容「你需要一条 Python 黑带才能让这些程序跑起来」。而且装上≠能跑：Josh 亲历过一个程序本该用 GPU、实际却在用 CPU，整整慢了 10 倍 [【跳转到 08:58】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=538)。

![binder 设计的软件科技树：RFdiffusion、ProteinMPNN、AlphaFold2 等层层依赖，逐级解锁才能走到终点](assets/ProteinDJ：%20A%20modular%20and%20open-source%20framework%20for%20protein%20design%20workflows/00538.webp)

先把「科技树」本身理一遍——这也是理解 ProteinDJ 四阶段的前提：

- **生成式方法**：在 PDB 数据库上训练深度学习模型，从随机噪声出发逐步「去噪」，生成全新的蛋白折叠。代表就是 RFdiffusion [【跳转到 05:45】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=345)。
- **幻觉式方法**：从一条随机序列出发，反复做结构预测，一轮轮优化序列，直到它演化出一个高置信度的 binder。BindCraft 是这类方法的代表 [【跳转到 06:10】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=370)。

RFdiffusion 这类生成式方法**只给骨架不给序列**，所以还需要：**ProteinMPNN**（有 soluble MPNN、LigandMPNN 等变体）按骨架设计序列；再把序列交给 **AlphaFold2** 做结构预测，对比「预测结构 vs 输入骨架」，一致就说明这条序列可信 [【跳转到 06:58】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=418)。

## 二、ProteinDJ 的答案：容器 + Nextflow + Python，四阶段一条线

面对两大拦路虎，WEHI 的 Josh（结构生物学背景）和 Dylan（软件工程背景）合作写出了 ProteinDJ——名字就来自两人（**D**ylan + **J**osh）。他们的设计目标 [【跳转到 09:40】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=580)：

- **易安装**、**资源高效**（别再让 GPU 活白跑在 CPU 上）；
- **灵活可配置**，同时**结果一致**；
- **开源透明**——程序在干什么一目了然，元数据全部记录、可消化可处理；
- **模块化**——这是最难的一条：不只是「眼下能用」，而是搭一个能不断纳入新工具的框架。

### 2.1 四阶段总览

ProteinDJ 的主流程只有一条直线，四个阶段 [【跳转到 10:35】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=635)：

![ProteinDJ 四阶段总览：RFdiffusion 出骨架 → 序列设计（每骨架 10–20 条）→ 结构预测回折验证 → 分析报告](assets/ProteinDJ：%20A%20modular%20and%20open-source%20framework%20for%20protein%20design%20workflows/00660.webp)

1. **Stage 1｜骨架生成**：RFdiffusion 从噪声去噪出 binder 骨架；
2. **Stage 2｜序列设计**：每个骨架展开 10–20 条序列（两个程序可选）；
3. **Stage 3｜结构预测**：通过回折验证的序列继续往下走（两个程序可选）；
4. **Stage 4｜分析与报告**：为存活的设计补充更多指标，汇总成 CSV。

## 三、Stage 1：RFdiffusion 出骨架的四种模式

RFdiffusion 单个设计通常要 **1–3 分钟**，耗时随 binder 与靶标尺寸大致**指数增长**。从 Dylan 论文里的结果图能看到，它产出的骨架种类极其丰富 [【跳转到 11:30】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=690)。

![RFdiffusion 生成的 binder 骨架多样性（来自 Dylan 的论文）](assets/ProteinDJ：%20A%20modular%20and%20open-source%20framework%20for%20protein%20design%20workflows/00690.webp)

但 RFdiffusion 原版「灵活到令人不知所措」。ProteinDJ 把它简化、梳理成**四种使用模式** [【跳转到 11:55】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=715)：

![ProteinDJ 对 RFdiffusion 的四种封装模式：de novo、fold conditioning、partial diffusion、motif scaffolding](assets/ProteinDJ：%20A%20modular%20and%20open-source%20framework%20for%20protein%20design%20workflows/00715.webp)

### 3.1 模式一：de novo——从无到有，热点可选

这是 RFdiffusion 最著名的用法：从噪声出发，凭空扩散出一个 binder，可以靠近你指定的**热点残基**（hotspots），也可以完全不限位置。带热点与不带热点**建议都试**——看看「RFdiffusion 想去哪里」和你认为「binder 该去哪里」有什么不同，对新结构来说这本身就很有趣 [【跳转到 12:20】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=740)。

### 3.2 模式二：fold conditioning——用经典折叠约束，把多样性「烤」进设计集

与 de novo 的天马行空相反，这一模式用**特定的折叠与二级结构信息**做条件约束——RFdiffusion 之前的主流思路就是「拿一个久经考验的模板折叠，在里面试新序列」。Josh 从 Baker 实验室收集了一批「金标准」 minibinder 折叠接进 RFdiffusion，让你能拿到折叠类型的多样性 [【跳转到 13:02】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=782)。

它的价值在基准测试里一目了然：流感 A 型血凝素（HA）是他们的测试靶标之一，结构预测通过率只有约 **2–3%**；用 de novo 模式，通过验证的全是**α 螺旋** binder——即使专门换上偏向 β 的模型，也拿不到一个含 β 折叠的成功设计；而换用 **ferredoxin 折叠的 β 股模型**做 fold conditioning，就拿到了含 β 片层的成功 binder [【跳转到 13:50】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=830)。

![HA 靶标上的对比实验：de novo 模式只有 α 螺旋 binder 通过验证，fold conditioning 模式拿到了 β 片层 binder](assets/ProteinDJ：%20A%20modular%20and%20open-source%20framework%20for%20protein%20design%20workflows/00830.webp)

Josh 的建议是：**别把宝押在单一折叠上**，把不同类型的 minibinder 一起带进湿实验室。

### 3.3 模式三：partial diffusion——给现有设计做「局部重掷」

当你已经有一个 binder、只想优化它（比如指标尚可但预测置信度想再提一提）时，可以把它重新喂给 RFdiffusion，只加**部分噪声**再降噪：噪声加满（完全扩散）会得到一个完全不同的蛋白，**只走到一半就停**，得到的则是原骨架的变体——步数（time steps）控制了变异幅度，也是给设计集引入多样性的手段 [【跳转到 14:45】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=885)。

### 3.4 模式四：motif scaffolding——把已知结合基序装进新骨架

当你手里已经有「会结合的那一段」——一段肽或一个螺旋——想让它在更大的 binder 里继续工作，或者想把自己的基序插进一个新骨架，就用这一模式。它的难点在于要**非常小心地摆放基序与骨架、指定插入与缺失的位置**，所以配置最复杂；但在「已有天然结合序列想扩展」这类场景里有不可替代的位置 [【跳转到 15:10】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=910)。

![motif scaffolding：把已知结合基序安放进新骨架，需要精确指定基序、骨架与插入缺失位置](assets/ProteinDJ：%20A%20modular%20and%20open-source%20framework%20for%20protein%20design%20workflows/00910.webp)

### 3.5 Stage 1 出口：先把明显不合格的骨架过滤掉

扩散类模型偶尔会产出「废片」——用过 AI 绘画的人都懂。ProteinDJ 因此加了一个**早期过滤**阶段：只含一根螺旋、回转半径过大（折叠不紧凑）之类的骨架可以直接丢掉，省下后续阶段的算力 [【跳转到 16:00】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=960)。

## 四、Stage 2：序列设计——ProteinMPNN+FastRelax 对决 full-atom MPNN

有了骨架，下一步是配序列。ProteinDJ 默认**每个骨架展开 10–20 条序列**，把候选规模滚起来；并内置了两个算法不同的程序 [【跳转到 16:55】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=1015)。

### 4.1 老将：ProteinMPNN + FastRelax

ProteinMPNN 是序列设计的名宿；ProteinDJ 把它和 **FastRelax**（Rosetta 的结构松弛程序）配合使用，让两者**循环接力**：MPNN 出一条序列 → FastRelax 松弛一下骨架 → MPNN 再来一条。实测它能提高成功率 [【跳转到 17:20】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=1040)——代价是慢：松弛步骤**没有 GPU 加速**，每轮要多花几分钟。这是「质量换数量」的取舍，你可以跳过它，但同样的骨架下成功率确实更好。

### 4.2 新秀：full-atom MPNN

一个更新的程序：在 MPNN 基础上**迭代地同时设计序列与侧链**——摆上侧链、看它们与靶标的契合度、把没把握的剪掉再来，直到完成整条序列。它有 GPU 加速、速度快，但**不松弛主链**、只调侧链，与 FastRelax 路线正好互补 [【跳转到 18:07】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=1087)。

### 4.3 五个靶标的实测对比

full-atom MPNN 此前没人用于 binder 设计，Josh 顺手做了横向对比（含 ProteinMPNN 的 vanilla 模型——用全部 PDB 训练——与 soluble 模型——只用可溶性蛋白训练）[【跳转到 18:52】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=1132)。五个基准靶标、约 15 次运行的结论 [【跳转到 19:17】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=1157)：

- **FastRelax 稳定最佳**：五个靶标全部提升成功率，但时间成本高；
- **full-atom MPNN 表现不稳定**：有时比 ProteinMPNN 好、有时更差，**因靶标而异**——对你的靶标哪个更好，只能试。

### 4.4 序列层面的过滤：价值仍未定

与骨架过滤对应，序列阶段也有各自的打分（两个程序算分方式不同），也可以按分过滤。但 Josh 坦言**这一步的价值还不清楚**：Dylan 在论文里分析过分数与最终成功率的相关性，发现很难定出一个「低于它后面必挂」的阈值。当前的做法是先把数据都记下来，留待回顾分析——这是个开放问题 [【跳转到 19:42】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=1182)。

## 五、Stage 3：回折验证——AF2 initial guess 与 Boltz

这是整个流水线**最关键也最耗时**的阶段：回折验证是在硅内（in silico）检验设计的最有效手段，在真实运行里**必然成为瓶颈** [【跳转到 20:32】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=1232)。

### 5.1 AlphaFold2 initial guess：只给序列，不给答案

ProteinDJ 的第一个验证程序是 binder 设计圈用了几年的 **AlphaFold2 initial guess** 玩法 [【跳转到 20:57】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=1257)：

![AlphaFold2 initial guess：把靶标结构作为初始猜测、只给 binder 序列，让 AF2 独立预测复合物，再与设计对比](assets/ProteinDJ：%20A%20modular%20and%20open-source%20framework%20for%20protein%20design%20workflows/01257.webp)

- 给 AF2 的信息是**受限的**：靶标的结构作为初始猜测（initial guess）提供，而 binder **只给序列**、不给任何结构信息；
- AF2 独立预测复合物结构后，与输入对比：binder 是否折叠成设计的样子、是否出现在设计的位置上；
- 用结构预测程序来「考」binder 序列。注意这不是原版 AF2，而是**大幅跳过 MSA 步骤的加速实现**——对 binder 设计够用，也快得多；
- 两个关键过滤指标：**PAE interaction score** 与**输入/输出间的 RMSD** [【跳转到 21:47】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=1307)。

### 5.2 Boltz：开源的「3 代」新选择

Josh 还想纳入下一代（「3」时代）结构预测程序，最终选了开源的 **Boltz**——成功率已非常接近 AlphaFold3，而开源对整个项目是巨大加分 [【跳转到 22:17】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=1337)。同样是用精度换速度：要过成百上千个设计，快比极致准确重要。他们还在为 Boltz 补充自定义的对比指标，目前对**多链靶标与断链较多**的情形仍有局限，还在迭代 [【跳转到 22:42】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=1362)。

### 5.3 拿哪些指标过滤？领域仍在争论

结构预测的指标很多，重要性却不一样。Josh 强烈推荐一篇近期的预印本：作者回顾性分析了 **4000 个 binder**，把所有预测指标都算了一遍，看哪些与湿实验成功率相关 [【跳转到 23:12】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=1392)。ProteinDJ 团队自己用 AF2 initial guess 时沿袭 RFdiffusion 论文的做法：**binder RMSD + PAE interaction score + pLDDT** 三件套 [【跳转到 23:37】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=1417)。但领域对「该用哪些指标」尚无共识——所以 ProteinDJ 干脆**把所有选项都做进配置**，不替你做决定。

## 六、Stage 4：分析与报告——把「选哪个」变成看表排序

挺过结构预测与指标过滤后还有存货的话，就进入相对轻量的分析阶段：为高度排名的设计**打破平局**补充更多信息——埋藏表面积（buried surface area，两个蛋白接触时被「埋」进去的面积，越大通常结合越稳）、界面的 ΔG，以及一切湿实验层面的考量 [【跳转到 24:11】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=1451)：

- 你的应用可能要求 binder 有特定的 **pI**（等电点）或电荷；
- 记得查**消光系数**：如果蛋白里没有芳香族氨基酸，它在紫外分光光度计下就是「隐形」的——浓度都测不了。这些属于「生活质量」功能。

所有结果最终汇成一个 **CSV 表**（Excel 直接打开）：每行一个设计，带上骨架 ID、序列 ID 与全部相关指标，排序、筛选、人工策展都很方便；PDB 结构文件一并输出 [【跳转到 24:36】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=1476)。

### 6.1 边界：ProteinDJ 不适合做什么

![ProteinDJ 的适用边界：不适用于抗体、酶与小分子 binder 设计，也不内置 BindCraft](assets/ProteinDJ：%20A%20modular%20and%20open-source%20framework%20for%20protein%20design%20workflows/01501.webp)

- **不做抗体、酶、小分子 binder**：这些需要别的工具（如 RFantibody、LigandMPNN），ProteinDJ 尚未纳入，不建议硬用；它最擅长的是**蛋白–蛋白结合**这类相互作用 [【跳转到 25:01】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=1501)；
- **BindCraft 暂未纳入**：它给出的 binder 与 RFdiffusion 不同，建议两个都试——团队不推销某个特定设计程序 [【跳转到 25:26】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=1526)；
- **流程是线性的**：没有「最优设计自动回炉再设计」的迭代闭环（编程太复杂）。想做迭代，可以用 partial diffusion 或 motif scaffolding 手动把好设计喂回去 [【跳转到 25:51】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=1551)；
- **没有在所有 HPC 上测试过**：你的环境里大概率会冒出 bug——发邮件或去 GitHub 提 issue，社区反馈会持续改进文档与教程 [【跳转到 26:16】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=1576)。

## 七、上手建议：从理解靶标到 BindSweeper 扫参数

这一系列讲座已有多场精彩报告，Josh 从自己的踩坑经历里补了五条「掏心窝」的建议 [【跳转到 26:41】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=1601)。

### 7.1 先懂靶标，再谈设计

所有软件都只是流程的一部分：**理解靶标蛋白的结构、工作机制、你想用 binder 达成什么**，才是成败关键。RFdiffusion 对**疏水补丁**有天然的亲和性——有的靶标很容易出 binder，有的很难 [【跳转到 26:51】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=1611)。做不动时：换热点、绕着蛋白表面换位置采样、换输入结构，最坏情况下换靶标或用同源蛋白。RFdiffusion 对输入 PDB 模型**非常敏感**，是彻底的「质量进、质量出」[【跳转到 27:16】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=1636)：晶体结构质量好吗？冷冻电镜结构可信吗？是不是用结构预测程序更好？有没有该删的多余部分、或者删错了该保留的部分？

### 7.2 裁剪有风险：断链与暴露的内侧残基

大结构跑得慢，所以大家常把靶标裁到只剩感兴趣的结构域——但必须小心。Josh 用**胰岛素受体**举例 [【跳转到 28:00】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=1680)：沿着一条蛋白序列整整齐齐地切，切口处有给 binder 的体面空间，没问题；但如果把结构域**拦腰切断**，就会产生断链和暴露在外的内侧残基——RFdiffusion 几乎必然去结合这些「假表面」，设计出的 binder 在真实上下文里毫无意义 [【跳转到 28:25】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=1705)。

为此 ProteinDJ 加了一个新特性：**RFdiffusion 用裁剪后的小结构跑**（它才是慢的那一步），而**结构预测阶段喂入完整未裁剪的结构**——预测更快，却能为评估提供完整上下文。效果立竿见影：一个三聚体靶标被裁掉一条链后，binder 被设计到了正常情况下根本接触不到的界面上；提供完整结构后，这个设计被自动**标记为有问题** [【跳转到 28:43】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=1723)。很多同行都抱怨过 RFdiffusion 的尺寸限制，这个功能就是为此而生。

### 7.3 好 binder 长什么样：小而精也可以

文献里成功的 binder 形状各异、因靶标而异，但共性是 [【跳转到 29:33】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=1773)：有**疏水核心**、侧链被埋进去帮助折叠；与靶标有**形状互补**（表面贴合）；有体面的**接触埋藏面积**；氢键可有可无。这些都能提高拿到高亲和力 binder 的概率。

另一个反直觉的点：**更大不总是更好**。60 个残基的 minibinder 也有成功的——除非应用有特殊要求，不必非设计一个庞然大物。建议对 binder 尺寸做**一个范围的尝试**，看什么适合你的靶标 [【跳转到 30:03】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=1803)。

### 7.4 下单之前：ChimeraX 里亲眼看一遍

CSV、指标、统计再漂亮，**下单合成基因之前**也要把最好的几个设计放进 ChimeraX（分子可视化软件）里亲眼过一遍：检查有没有原子冲突、放进上下文看看、留意柔性区域；分子动力学分析也有助于判断优劣（虽然那不是 Josh 的专长）[【跳转到 30:28】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=1828)。并且牢记：哪怕一切步骤都做对、预测分数很高，**它也只是一个预测**——总有一部分设计在实验室里不表达、不结合 [【跳转到 30:53】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=1853)。

### 7.5 BindSweeper：把参数扫描交给程序

新手最难判断「哪些参数重要」。Josh 自己就做过这种苦工：测试不同的 MPNN 模型检查点、再试不同折叠——五个基准靶标、约 15 次独立运行，进度全靠手动管理 [【跳转到 31:18】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=1878)。他向 Dylan抱怨「要是有个程序替我干这个就好了」，于是有了 **BindSweeper** [【跳转到 31:43】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=1903)：

![BindSweeper：为每组参数组合批量启动 ProteinDJ 任务并汇报成功率](assets/ProteinDJ：%20A%20modular%20and%20open-source%20framework%20for%20protein%20design%20workflows/01928.webp)

- 设定好参数组合（不同热点集合、不同噪声尺度 noise scale——ProteinDJ 里任何参数都行），它会为每组组合启动 ProteinDJ 任务，汇报各自的成功率 [【跳转到 32:08】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=1928)；
- 定位是**大规模运行前的小规模试探**：先扫出有希望的参数，再全力跑；
- 目前只有命令行界面，比主界面复杂一点 [【跳转到 32:33】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=1953)。

## 八、幕后：一个冷冻电镜学者的一年编程史

报告的后半段，Josh 把 ProteinDJ 的开发过程摊开讲了讲——对想造类似工具的人，这部分可能比工具本身更有价值。

### 8.1 从 BigScript 到 ProteinDJ

Josh 入场时对 RFdiffusion 一无所知，幸运的是身边全是墨尔本的先驱者——Rhys、Maria、Gavin、Cynthia、Martin、Richard（其中多位在本系列讲座亮过相）[【跳转到 33:11】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=1991)。当时团队用三个程序：RFdiffusion、ProteinMPNN、AlphaFold2。Josh 的第一份工作是**把它们装起来跑通**——这花了两周；GPU 令他头疼的还有：有的程序用 GPU 有的不用、各家元数据格式五花八门，甚至还有一种叫 **silent file** 的东西（压缩版的 PDB 文件），起初完全摸不着头脑 [【跳转到 33:36】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=2016)。

他的第一版工作流叫 **BigScript**（顾名思义的玩笑）：一个巨大的 Bash 脚本顺序执行所有命令 [【跳转到 34:17】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=2057)。问题一大堆：只在他自己的 WEHI HPC 账号上能跑；不需要 GPU 的任务也去占 GPU 节点（HPC 管理员很不高兴）；所有参数埋在一个巨大文件里，换个靶标就得进文件里翻找调试 [【跳转到 34:42】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=2082)。但它展示了潜力：**24 小时生成一千个设计**、并行跑起来——Josh 知道自己写的东西不好用，但方向是对的 [【跳转到 35:07】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=2107)。

触到计算机技能的天花板后，团队请来了救兵：软件工程背景的 Dylan（在另一个实验室做荣誉学位，导师 Tony）。Dylan 提出三个技术方案：**Apptainer**（容器化，让软件跨系统运行）、**Nextflow**（把所有步骤串成工作流）、**Python 脚本**（粘合程序、处理元数据）[【跳转到 35:22】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=2122)。这个跨学科团队（还有 Julie、Juni、Andrew 与双方导师的支持）沟通起来并不轻松，但最终产出了一个真正好用的工具。Josh 也在这两年里完成了一次大跨越：从「修改 Dylan 的第一版——通常是改坏它」开始，靠教材、文档和生成式 AI 硬啃三门编程语言 [【跳转到 36:21】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=2181)。

### 8.2 用生成式 AI 学编程：四条实战经验

Josh 特意分享了他用 AI 辅助编程的心得——因为他本人就是这么学会写代码的，他相信这也是如今大多数人学编程的方式 [【跳转到 37:01】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=2221)：

- **强项**：AI 很擅长理解你的意图，给出的代码注释和函数文档往往比人写的还清楚，还会主动建议改进与排错方向；
- **盲区**：它默认你给它的起点是能用的——**很少会推倒重来**，哪怕重来更高效；你不明说自己不确定，它就当你胸有成竹；
- **血泪教训**：**一切都要自己验证**。程序经常打出「alignment completed successfully」「statistics calculated」之类的消息，但如果你不用另一个软件包交叉验证、不把结构下载下来亲自分析，就可能被误导——分数算错了、比对根本没发生，你都浑然不知 [【跳转到 37:51】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=2271)；
- **聊天机器人并不平等**：对比过 ChatGPT 与 Claude 之后，他发现**跑代码时 Claude 更可靠、成功率更高**；「推理/思考」类模型适合整体架构设计这类难题，小问题反而没必要；他订阅了 Perplexity Pro，可以随时在多个模型间切换 [【跳转到 38:16】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=2296)。

另外两条沟通技巧：和 AI 协作像和另一个程序员结对，**开局就把细节给足**——附上日志文件、示例输入、期望输出的样例，比「挤牙膏式」来回一小时高效得多 [【跳转到 38:41】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=2321)；而随着自己学会了 Python、看懂了函数在干什么，他慢慢能自己发现问题、提出可行的改进建议——不懂语言，你连需求都描述不清楚 [【跳转到 39:31】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=2371)。

### 8.3 三大组件的分工

ProteinDJ 的技术栈就三样东西 [【跳转到 40:01】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=2401)：

- **容器**：Josh 用「器官移植」作类比——让软件在不同计算机之间搬家而不散架；还能让依赖冲突的程序（各自需要不同版本的库）在同一台机器上和平共处；也能整体搬上云。搭建有门槛，但一旦就位极其灵活；
- **Nextflow**：生物信息学里处理测序数据的老牌流水线语言，兼容容器与 HPC，如今也被用于蛋白结构。数据与文件在**通道（channel）**里流动，每流过一个任务就被处理一次——Josh 画了一张地铁线路图式的示意图 [【跳转到 41:14】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=2474)；

![Nextflow 流水线的「地铁图」：数据在通道中流动，沿途任务逐文件执行](assets/ProteinDJ：%20A%20modular%20and%20open-source%20framework%20for%20protein%20design%20workflows/02474.webp)

- **Python**：负责 Nextflow 搞不定的小事——结构比对、序列提取等，重度依赖 PyRosetta 与 Biopython 这两个自带相关功能的库 [【跳转到 41:32】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=2492)。

一个必须知道的限制：因为用了 PyRosetta，**商业项目使用 ProteinDJ 需要购买授权**（其他一些工具同样如此）；Josh 注意到已有人在开发绕开 PyRosetta 的免费版本，值得观望 [【跳转到 41:57】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=2517)。

### 8.4 元数据规则：让异构程序说同一种语言

开发中最大的设计挑战：各程序输出的格式和文件五花八门，怎么让它们互相「对话」？团队试过不同方案，早期版本的文件流向图「一团乱麻」[【跳转到 42:22】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=2542)。最终定下的规则很朴素 [【跳转到 42:47】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=2567)：

- 每个结构**一个独立的 PDB 文件**，配**一个独立的 JSON 元数据文件**（机器最好读的格式）；
- 每份元数据里有**骨架 ID** 和**序列 ID** 两个标签，同时写进 PDB 文件名与元数据——确保元数据永远映射到正确的结构；
- 指标与参数用**前缀**标明出处：这是 RFdiffusion 的 mode、那是 ProteinMPNN 的 temperature——对程序员排查问题也极友好。

整个设计的目标是**互操作性**：每个模块有统一的入口和出口 [【跳转到 43:37】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=2617)。在最终的「地铁图」上，四个阶段（骨架设计、序列设计、结构预测、分析与报告）用灰框标出，所有步骤吐出的元数据在最后一级汇总收集 [【跳转到 43:53】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=2633)。想深挖细节，可以读他们的 bioRxiv 预印本。

![ProteinDJ 架构总览：四个灰框阶段串联，全程元数据汇入最终报告](assets/ProteinDJ：%20A%20modular%20and%20open-source%20framework%20for%20protein%20design%20workflows/02633.webp)

## 九、安装与运行：两步装好，两种跑法

### 9.1 两步安装

Josh 把安装简化到了极限 [【跳转到 44:37】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=2677)：

1. **克隆 GitHub 仓库**：几秒钟；
2. **下载模型与检查点**：RFdiffusion、AlphaFold2 等程序不是他们写的，权重需要单独下载——他写了个脚本代劳，视网速约 10–15 分钟。

之后即可运行：容器托管在云端，首次运行各阶段时自动下载暂存（也可以自己构建、放在中心位置，但不强求）[【跳转到 45:02】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=2702)。如果用的 GPU 型号与他们不同，可能要调整资源申请配置——都很直接，GitHub 文档有说明。

### 9.2 命令行或网页

发起一次运行需要准备：设计参数 + 输入文件（靶标结构文件就位、想用的热点）[【跳转到 45:27】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=2727)。之后有两种交互方式：

- **命令行**：Nextflow 读一个配置文件，四大参数带注释、可选项说明齐全 [【跳转到 46:11】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=2771)；还支持 **profiles**——参数「片段」，覆盖配置里的默认值，管理起来更聚焦；每种设计模式都有现成示例可以改着用。运行时 Nextflow 追踪所有任务、逐个打勾，结束后给出设计数量与结果的总结 [【跳转到 46:36】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=2796)；
- **网页（Seqera）**：命令行不是人人爱用，所以 ProteinDJ 也支持通过 Seqera（Nextflow 的商业平台服务，可在云端或 HPC 上跑 Nextflow 流水线）发起 [【跳转到 47:01】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=2821)。每种设计模式一个定制表单、预填默认值、自动校验输入格式；所有运行中的任务与进度一目了然、可同时盯多个 [【跳转到 47:22】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=2842)。WEHI 与 BioCommons 合作接入了这项服务，感兴趣者推荐联系开通 [【跳转到 47:47】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=2867)。

![Seqera 网页界面：每种设计模式一张表单，自动校验输入并展示任务进度](assets/ProteinDJ：%20A%20modular%20and%20open-source%20framework%20for%20protein%20design%20workflows/02842.webp)

### 9.3 它会走向哪里

收尾时 Josh 强调：这一年来程序不断演化，团队想做的**不只是一个当下好用的工具，而是一个面向未来的框架**——软件版图瞬息万变，领域需要规范与互操作，代码全部开源正是为了促成协作 [【跳转到 48:08】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=2888)。接下来的计划：让程序在不同环境跑得更稳、修 bug；纳入 BindCraft 等新软件；并吸收那篇 4000 binder 回顾论文新提出的指标公式，升级结构预测过滤 [【跳转到 53:51】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=3231)。最后是致谢：Dylan 是 ProteinDJ 的头脑与初始开发者、Josh 的编程导师；Andrew 与 Juni 负责测试；Julia 搭建 HPC 环境、修复容器；Tony 在管理层面支持了项目 [【跳转到 48:38】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=2918)。

## 十、问答摘要

- **怎么决定收录哪些程序？** 很难——每个程序都要花数周到数月去吃透、有时还要改源码才能接进流水线；开源是硬标准，收录工作仍在继续 [【跳转到 50:06】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=3006)。
- **含 β 折叠的 binder 溶解性和稳定性更好吗？** Josh 自己没做过太多 binder，无法现身说法；自然界两种都有。要注意的是**算法偏差**：如果设计算法一开始就不产出某类折叠，它们根本进不了湿实验。Baker 实验室约 2017–2018 年的综述发现：小型螺旋束比含 β 股的蛋白更可溶——但两者都有成功案例，并不互斥 [【跳转到 51:21】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=3081)。
- **能用 de novo binder 反过来重新设计靶标吗？** 他不确定有没有人做过；把 Boltz 接进流水线正是为了「靶标与 binder 共折叠」（co-fold），这是理解相互作用的一种有趣视角；也想试 BindCraft（它在早期阶段做类似的事）。结合会伴随**诱导契合（induced fit）**，他认为分子动力学未来会在「设计能诱导靶标特定构象的 binder」上发挥大作用 [【跳转到 52:36】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=3156)。
- **ProteinDJ 下一步？** 见 9.3：环境适配与修 bug、纳入 BindCraft、引入新指标公式 [【跳转到 53:51】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=3231)。

主持人最后补充：预印本与 GitHub 链接见聊天区、幻灯片会后分享；本系列还有后续场次；想入坑者可以加入澳大利亚结构生物学计算社区的 Slack 与定期例会 [【跳转到 55:19】](https://www.youtube.com/watch?v=xwvF62HxaF0&t=3319)。

## 小结

- **四阶段一条线**：RFdiffusion 四种模式出骨架 → 每骨架 10–20 条序列（ProteinMPNN+FastRelax 或 full-atom MPNN）→ AF2 initial guess 或 Boltz 回折验证 → 分析报告出 CSV——binder 设计的「科技树」从此变成一条可复现的流水线。
- **回折验证是流水线的瓶颈，也是质量闸门**：只给序列不给结构答案的 initial guess 玩法 + PAE interaction score / RMSD / pLDDT 三件套；指标共识未定，好工具应该把所有选项都给你。
- **多样性是对抗 0–5% 通过率的武器**：fold conditioning 能把 β 折叠带进全是 α 螺旋的候选集；partial diffusion 局部重掷；binder 不求大，60 残基的 minibinder 也能成功。
- **理解靶标重于调参**：输入 PDB 质量决定一切；裁剪小心断链与暴露残基，新特性「RFdiffusion 用裁剪结构、结构预测用完整结构」能自动揪出坏设计；下单前务必 ChimeraX 目检。
- **元数据是一等公民**：每结构一个 PDB + 一个 JSON，骨架/序列双 ID 贯穿文件名与元数据，前缀标明指标出处——可追溯、可回顾、可互操作。
- **工具会过时，框架不会**：容器 + Nextflow + Python 的模块化设计，让 RFdiffusion、AF2 随时可以替换成下一代（BindCraft 与新指标公式已在路上）。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| ProteinDJ | WEHI 开发的模块化开源 binder 设计流水线（Dylan + Josh），容器 + Nextflow + Python 三件套实现 |
| binder | 设计出来专门结合某个靶标蛋白的新蛋白 |
| 生成式 / 幻觉式设计 | 前者从噪声去噪出骨架（RFdiffusion）；后者从随机序列反复结构预测迭代优化（BindCraft） |
| RFdiffusion | 从高斯噪声去噪生成蛋白骨架的扩散模型（Baker 实验室） |
| hotspot（热点残基） | 靶标上指定的关键结合残基，引导 binder 设计到附近 |
| fold conditioning | 用已知折叠/二级结构信息约束 RFdiffusion，为候选集引入折叠多样性 |
| partial diffusion | 对已有设计只加部分噪声再降噪，生成其变体（加满则得到全新蛋白） |
| motif scaffolding | 把已知结合基序安放进新骨架，需精确指定基序位置与插入缺失 |
| 回转半径 | 衡量结构紧凑度；过大说明折叠松散，Stage 1 据此过滤废骨架 |
| ProteinMPNN | 读入骨架、逐位置设计氨基酸序列的图神经网络；vanilla 模型用全 PDB 训练，soluble 模型只用可溶性蛋白 |
| FastRelax | Rosetta 的骨架松弛程序，与 ProteinMPNN 循环接力可提高成功率，但无 GPU 加速、较慢 |
| full-atom MPNN | 迭代设计序列与侧链的新程序，GPU 加速、快，但不松弛主链；效果因靶标而异 |
| AF2 initial guess | 回折验证玩法：靶标结构作初始猜测、binder 只给序列，用加速版 AF2（跳过 MSA）预测并与设计对比 |
| Boltz | 开源的 AF3 代结构预测程序，成功率接近 AF3；ProteinDJ 的第二验证选项，多链靶标仍有局限 |
| PAE interaction score | 从预测对齐误差派生的界面结合打分，越小越好 |
| pLDDT | AlphaFold 系模型的逐残基置信度（0–100） |
| RMSD | 回折验证中输入骨架与预测结构间的偏差，越小说明序列忠实复现了设计 |
| BindSweeper | 配套参数扫描工具：为每组参数组合批量启动 ProteinDJ 并汇报成功率（仅命令行） |
| BindCraft | 幻觉式 binder 设计流水线，与 RFdiffusion 产物互补，暂未纳入 ProteinDJ |
| Apptainer | HPC 常用容器运行时，让软件跨机器一致运行、依赖互不冲突 |
| Nextflow | 流水线语言：数据在通道中流动、任务逐文件执行，兼容容器与 HPC |
| Seqera | Nextflow 的商业平台服务，提供网页表单、输入校验与任务监控 |
| PyRosetta | ProteinDJ 使用的结构计算库；商业使用需购买授权 |
| silent file | Rosetta 系工具的压缩 PDB 类结构文件格式 |
| 埋藏表面积（BSA） | 界面接触面积的度量，Stage 4 用于打破平局 |
| 消光系数 | 由芳香族氨基酸决定；无芳香族残基的蛋白在紫外分光光度计下测不出浓度 |
