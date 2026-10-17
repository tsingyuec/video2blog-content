# RFdiffusion 生成 Binder 骨架：contigs 配置与骨架过滤（RosettaCommons 官方教程）

> 视频来源：[Fundamentals of protein binder design with RFdiffusion](https://www.youtube.com/watch?v=6imf4vFmtbo)（YouTube，20 分 32 秒，RosettaCommons 教程系列，主讲人为 UNC 教堂山分校博士生 Matthew）

## 本讲要解决的核心问题（SCQA）

**背景**：蛋白 binder 设计三部曲的第一步是「骨架生成」。RFdiffusion（RoseTTAFold Diffusion）是 Baker 实验室的扩散生成模型：它像文生图模型一样，从噪声出发一步步「去噪」，直接生成一个全新蛋白的骨架坐标。

**冲突**：但两个难题摆在面前。其一，RFdiffusion 不会自动知道你要「围绕哪个功能 motif 生成、对准靶标上哪些残基」——这些设计意图要靠 contigs（残基配置串）写进命令，而主讲人明确说这是整套配置里「最具挑战、也最重要」的部分。其二，扩散模型会像图像生成画出六根手指那样，输出一部分根本没法用的坏骨架，不筛选就直接送下游序列设计，只会浪费算力。

**疑问**：怎么把设计意图正确写进 contigs？生成的成百上千个骨架，又怎么快速筛出高质量的少数？

**回答（中心思想）**：跑 RFdiffusion 前先在 ChimeraX 里确定三要素——保留的 motif 残基、5~10 个靶标热点、靶标残基范围；配置里靶标各链原样传入并以 `/0` 结尾（链断点），binder 段按「新生成长度 + 保留 motif + 新生成长度」书写且段间不加链断点，使它们落在同一条链上，再用 hotspots 引导界面；跑完后用回转半径、N/C 端朝向、STRIDE 二级结构占比三个指标批量分析并按阈值过滤（示例中 194 个骨架留下 32 个），把干净的多聚甘氨酸骨架交给 ProteinMPNN 做序列设计。

## 一、这条管线在做什么：de novo binder 与 motif scaffolding

### 1.1 从头设计的蛋白 binder

de novo（从头设计）蛋白指完全用计算模型「从零创造」的蛋白质——自然界从未出现过，却能执行特定设计功能，某些情况下甚至优于天然蛋白。其中一个最有力的应用，就是设计能紧密结合既有蛋白的**蛋白 binder**：它们有望成为新的分子研究工具，乃至新一类生物药物。视频开场展示的，就是 Baker 实验室生成的胰岛素 binder 动画。

[【跳转到 00:32】](https://www.youtube.com/watch?v=6imf4vFmtbo&t=32)

### 1.2 motif scaffolding：给功能片段「造壳」

另一类设计目标是 **motif scaffolding（基序支架化）**：围绕一个既有蛋白/多肽上的功能片段，生成一个全新的蛋白结构，让新蛋白把这个功能片段「装进去」。本教程的例子是一个潜在治疗性 binder：它靶向一个参与免疫调节的离子通道，并且把既有肽类毒素 ShK 的**堵孔赖氨酸**保留下来——只留这个插进孔道的关键残基，让 RFdiffusion 围绕它生成全新的骨架，做出「毒素启发的 binder」。

[【跳转到 01:28】](https://www.youtube.com/watch?v=6imf4vFmtbo&t=88)

## 二、跑 RFdiffusion 前的准备

### 2.1 工具与输入

- 需要 RFdiffusion、ChimeraX，以及一块**显存至少 12 GB** 的 GPU；过滤环节还需要 STRIDE（一个二级结构分析程序）。
- 教程提供的输入结构已用 Rosetta 做过松弛（relax）、裁剪（trim）与重编号（renumber）。如果你的靶标是自己的，这些预处理步骤可能必不可少。
- RFdiffusion 会追踪结构里所有的 Cα（α 碳原子），所以先在 ChimeraX 或 PyMOL 里确认哪些部分要保留、哪些可以丢弃——视频里已把起始结构上不必要的部分裁掉，得到干净的输入。

### 2.2 在 ChimeraX 里写下三要素

配置之前，主讲人要求先在可视化软件里写下三件事（这是 contigs 的全部原料）：

1. **要支架化的 motif 残基编号**：本例主要是插进孔道的那个赖氨酸，把鼠标悬停在残基上即可读到链 ID 与残基号（本例为 H 链 462–463）。
2. **热点（hotspots）**：靶标上希望 binder 与之相互作用残基。因为要设计的是「堵孔」binder，热点选在通道上部，跨 A–D 四条靶标链共选 **5~10 个**。
3. **靶标残基范围**：本例靶标已裁剪，A–D 四条链全部残基都要传入。

[【跳转到 03:54】](https://www.youtube.com/watch?v=6imf4vFmtbo&t=234)

## 三、contigs 配置逐行拆解（本讲核心）

### 3.1 命令脚本的骨架

运行脚本（`.sh`）逐行看：第一行用 Python 执行 RFdiffusion 的运行入口脚本（指向本地安装）；第二行指定输出前缀（输出文件名与保存目录）；第三行给出输入 PDB 路径，即刚在 ChimeraX 里检查过的结构。

[【跳转到 05:49】](https://www.youtube.com/watch?v=6imf4vFmtbo&t=349)

### 3.2 contigmap：哪些是靶标、哪些是设计

接下来是最难也最重要的一段——告诉 RFdiffusion 蛋白的哪些部分是靶标（原样传入、不许动）、哪些是要设计的：

![contigmap 中靶标四链的写法](assets/Fundamentals%20of%20protein%20binder%20design%20with%20RFdiffusion/00374.webp)

- **靶标四条链**：`A 1-110`、`B 111-220`、`C 221-330`、`D 331-440`，每条链后面跟一个 `/0`（链断点）。这告诉 RFdiffusion：它们是彼此独立的链，所有 Cα 原样传入、一个都不改。
- **binder 部分**：先写 `30-50`（让模型随机生成 30~50 个残基长度的链），随后是保留的 motif 残基（H 462–463），再接一段 `20-50` 的新生成残基。**这几段之间不写链断点**——因为 motif 与前后新生成的残基要输出到同一条链上，中间不能有断点。这正是条目里 `A1-59/0 30-50` 这种「靶标 + 链断点 + 新链长度」写法的完整实战版。

![binder 段：新生成长度 + 保留 motif + 新生成长度，同链无断点](assets/Fundamentals%20of%20protein%20binder%20design%20with%20RFdiffusion/00399.webp)

[【跳转到 06:14】](https://www.youtube.com/watch?v=6imf4vFmtbo&t=374)

### 3.3 hotspots、引导势与设计数量

- **hotspots 行**：写入刚才在 ChimeraX 里挑好的热点残基，引导生成的 binder 去与这些残基相互作用——既保证 motif 装进去了，也保证整个孔被「堵」住。

![hotspot 残基行](assets/Fundamentals%20of%20protein%20binder%20design%20with%20RFdiffusion/00424.webp)

- **引导势（guiding potentials）**：本例使用 binder 回转半径（radius of gyration）引导势，在扩散过程中加权，偏向更紧凑的最终设计。
- **设计数量**：脚本里设为 500 个。GPU（RTX 4090）上每个设计约 1.5 分钟，CPU 会慢得多。主讲人的实用建议：**正式跑之前先把数量降到 5~10 个**，确认整条流程没问题；全量设计可能需要数千甚至上万个骨架。

![引导势与设计数量配置](assets/Fundamentals%20of%20protein%20binder%20design%20with%20RFdiffusion/00449.webp)

[【跳转到 07:54】](https://www.youtube.com/watch?v=6imf4vFmtbo&t=474)

### 3.4 运行与确认

跑之前先 `nvidia-smi` 确认 GPU 已连接（示例为 4090），然后 `bash` 运行脚本；日志前几行会显示找到了哪块 GPU。**离开电脑前务必确认**终端里在持续输出带逐步时间步（time steps）的行——那才说明 RFdiffusion 真的在正常工作。

![确认去噪时间步在正常输出](assets/Fundamentals%20of%20protein%20binder%20design%20with%20RFdiffusion/00554.webp)

[【跳转到 09:14】](https://www.youtube.com/watch?v=6imf4vFmtbo&t=554)

## 四、输出检查与骨架过滤

### 4.1 先目检：输出长什么样

RFdiffusion **只输出 Cα 原子**（多聚甘氨酸骨架），但链信息会保留。在 ChimeraX 里打开一个输出：可以看到一个三螺旋束（three-helix bundle）正好压在孔域上方，起始的赖氨酸仍待在原位——说明设计按预期生成了。

![输出检查：三螺旋束覆盖孔域，赖氨酸在位](assets/Fundamentals%20of%20protein%20binder%20design%20with%20RFdiffusion/00604.webp)

[【跳转到 10:04】](https://www.youtube.com/watch?v=6imf4vFmtbo&t=604)

### 4.2 为什么会有坏设计

RFdiffusion 与其他扩散生成模型一样：很擅长生成形状互补的 binder，但也会输出不可用的骨架——正如文生图模型会画出六根手指。典型问题包括**拉得过长的单条螺旋**或**完全缺乏结构元件**：两者都意味着蛋白核心没有好好堆叠，成功概率大打折扣。此外还要结合自己的用例考虑，比如本例要在一个末端设计亲和纯化标签，就得保证标签不与结合界面冲突。

[【跳转到 10:59】](https://www.youtube.com/watch?v=6imf4vFmtbo&t=659)

### 4.3 三个质量指标

对每个骨架计算三项指标（好/坏设计的差别就在这三处）：

1. **回转半径（Rg）**：近似衡量 binder 的紧凑度，越小越紧凑。
2. **N/C 端朝向**：计算 N 端与 C 端相对「界面参考点」的距离与骨架质心的关系。先在 ChimeraX 里选界面处一个原子，用 `get_crd` 类命令取其坐标作为参考点；若末端距离比值 **≥ 1**（末端比质心离界面更远），则后续加亲和标签不容易撞上界面，是好苗子。
3. **二级结构占比（STRIDE）**：STRIDE 把残基分为螺旋（H）、折叠片（E）与无规卷曲/转角（C/T）。好设计应有明确的 α 螺旋或 β 折叠，C/T 这类无结构区域占比越小越好。

![三个质量指标的定义](assets/Fundamentals%20of%20protein%20binder%20design%20with%20RFdiffusion/00684.webp)

![STRIDE 的二级结构分类](assets/Fundamentals%20of%20protein%20binder%20design%20with%20RFdiffusion/00724.webp)

[【跳转到 12:04】](https://www.youtube.com/watch?v=6imf4vFmtbo&t=724)

### 4.4 analyze 脚本：一键算出 metrics.csv

教程提供两个脚本：`analyze_backbones`（分析）与 `filter_backbones`（过滤）。给分析脚本传入 PDB 目录、binder 链（本例恒为链 A）、界面参考点坐标、本地 STRIDE 路径与输出 CSV 文件名，脚本很快分析完全部 **194 个**骨架，产出一张表：PDB 文件名、原子数、每个 binder 的 Rg、N/C 端相对参考点的朝向、螺旋/折叠片/卷曲百分比。

![analyze_backbones 的参数与 metrics.csv 输出](assets/Fundamentals%20of%20protein%20binder%20design%20with%20RFdiffusion/00918.webp)

[【跳转到 15:18】](https://www.youtube.com/watch?v=6imf4vFmtbo&t=918)

用这张表能直观看到指标的含义：

- 按 **N 端离界面最近**排序：binder 172 的 N 端整个埋在界面里——若要在 N 端加 His 标签就会完全冲突（坏）；排在另一端的 binder 99 则 N 端离界面很远（好）。
- 按 **Rg 从小到大**排序：binder 128 最紧凑，在 ChimeraX 里是一个扎实的四螺旋束、正好落在核心区；最大（最伸展）的 binder 146 则只有两条拉长的螺旋，甚至伸出了靶标范围。

![Rg 最小的 binder 128：紧凑四螺旋束](assets/Fundamentals%20of%20protein%20binder%20design%20with%20RFdiffusion/01008.webp)

[【跳转到 16:48】](https://www.youtube.com/watch?v=6imf4vFmtbo&t=1008)

### 4.5 filter 脚本：按阈值批量筛

`filter_backbones` 接收 metrics.csv、输出目录与各列的 min/max 阈值。示例目标是「N 端外露 + 紧凑」：设 Rg 最大 10~12 Å、N 端比值最小 1，脚本会报告通过阈值的统计——**194 个骨架中 32 个通过**。这些阈值完全可以按自己的设计目标改：螺旋/折叠片偏好、Rg 范围、N/C 端朝向都可以调整，是一套通用的骨架初筛工具。

![filter_backbones：194 个骨架筛出 32 个](assets/Fundamentals%20of%20protein%20binder%20design%20with%20RFdiffusion/01114.webp)

[【跳转到 18:59】](https://www.youtube.com/watch?v=6imf4vFmtbo&t=1139)

## 五、下一步：序列设计与回折验证

至此「骨架设计 + 过滤」完成，但整条蛋白设计管线还没走完。主讲人在结尾强调：RFdiffusion 输出的是**多聚甘氨酸骨架**，要让蛋白在真实世界存在，还需要用 **ProteinMPNN** 之类的序列设计工具补上氨基酸序列，再用 AlphaFold、RosettaFold 或 Boltz 等结构预测工具回折验证设计序列——这正是三部曲的第二、三步（见 5.2.1b、5.2.1c）。

![下一步：ProteinMPNN + 回折验证](assets/Fundamentals%20of%20protein%20binder%20design%20with%20RFdiffusion/01171.webp)

[【跳转到 19:31】](https://www.youtube.com/watch?v=6imf4vFmtbo&t=1171)

## 小结

- de novo binder 与 motif scaffolding 是同一套管线的两种用法：前者从零生成 binder，后者把既有功能 motif（如 ShK 毒肽的堵孔赖氨酸）装进全新骨架。
- 配置前三要素：motif 残基编号、5~10 个靶标热点、靶标残基范围，全部在 ChimeraX 里预先确认。
- contigs 语法核心：靶标各链原样传入、以 `/0`（链断点）收尾；binder 段「30-50 + motif + 20-50」之间不写断点，保证同链连续。
- hotspots 引导界面、回转半径引导势偏向紧凑设计；正式跑之前先用 5~10 个设计试跑。
- 输出只有 Cα（多聚甘氨酸骨架）；用 Rg、N/C 端朝向、STRIDE 二级结构三指标分析（194 个骨架出一张 CSV），再按阈值过滤（示例留 32 个）。
- 骨架只是起点：ProteinMPNN 序列设计 + 回折验证才是「能存在于真实世界」的完整闭环。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| de novo binder | 用计算模型从零设计、能紧密结合靶标蛋白的全新蛋白 |
| motif scaffolding | 围绕既有功能片段（motif）生成全新蛋白结构，把 motif「装进去」 |
| contigs / contigmap | 告诉 RFdiffusion 哪些残基保留、哪些新生成的残基配置串 |
| `/0`（链断点） | contigs 中的链分隔记号：之后的残基成为新链；靶标链靠它原样传入 |
| hotspot（热点） | 靶标上希望 binder 优先接触的残基，引导界面生成 |
| 引导势 | 扩散去噪过程中的加权项，如回转半径引导势偏向紧凑设计 |
| Cα / 多聚甘氨酸骨架 | RFdiffusion 的输出：仅 α 碳原子、序列未定的骨架 |
| 回转半径 Rg | 衡量结构紧凑程度的指标，越小越紧凑 |
| STRIDE | 二级结构分析程序，把残基分为 H（螺旋）/E（折叠片）/C/T（无结构） |
| ProteinMPNN | 在给定骨架上设计氨基酸序列的逆折叠工具（三部曲第二步） |
