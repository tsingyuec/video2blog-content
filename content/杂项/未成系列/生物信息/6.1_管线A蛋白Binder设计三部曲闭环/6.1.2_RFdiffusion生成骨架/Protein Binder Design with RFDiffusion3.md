# RFdiffusion3 开发者亲讲：全原子 Binder 设计、YAML 配置与参数实测

> 视频来源：[Protein Binder Design with RFDiffusion3](https://www.youtube.com/watch?v=LVN2l587C3M)（YouTube，30 分 59 秒，Baker 实验室二年级博士生、RFdiffusion3 开发团队成员主讲）

## 本讲要解决的核心问题（SCQA）

**背景**：RFdiffusion 已是蛋白 binder 设计的主力工具，而 RFdiffusion3（下称 RFD3）是它的新一代版本，由 Baker 实验室开发。经典版的产出是多聚甘氨酸骨架（见 5.2.1a 与本条目 RosettaCommons 教程篇），序列要交给 ProteinMPNN 补。

**冲突**：对新手来说有三重变化需要消化：RFD3 改成了全原子模型，输出物、配置文件（JSON/YAML）与一系列开关（原子级热点、non-loopy、采样温度……）都和旧版不同；参数怎么选直接影响「回折通过率」与「设计多样性」的平衡；而且市面上还有 BindCraft、BoltzGen 等同类工具，不知道该用哪个。

**疑问**：RFD3 到底变了什么？一份标准 PPI（蛋白-蛋白相互作用）配置怎么写？参数与工具该怎么选？

**回答（中心思想）**：RFD3 的三个关键变化是——全原子输出（序列与侧链构象一并产出）、训练数据覆盖整个 PDB（配体/核酸/糖/金属/翻译后修饰都在分布内）、速度比 RFD1/RFD2 快约一个数量级；配置的核心是把经典 contigs 语法升级为 context 字符串三要素——`新生成残基长度 /0 链断点 / 从输入文件加载的链与残基范围`（如 `40-120/0/E6-155`），hotspot 升级为原子级（4.5 Å 精度）；实操上推荐「non-loopy + 低温采样」起步，并用 Foldseek 聚类通过率监控多样性，最后按任务在 RFD3、BoltzGen、BindCraft 等工具间试点。

## 一、RFD3 的三件新事

### 1.1 全原子：序列和侧链一起出来

与只输出骨架坐标的旧版不同，RFD3 是**全原子（all-atom）**设计模型：输出的不只是主链坐标，还有全部侧链原子的精确坐标——序列（sequence）与侧链构象（rotamer）都直接由模型给出。

![RFD3 全原子模型介绍页](assets/Protein%20Binder%20Design%20with%20RFDiffusion3/00015.webp)

[【跳转到 00:15】](https://www.youtube.com/watch?v=LVN2l587C3M&t=15)

### 1.2 训练数据覆盖整个 PDB

RFD3 用除结晶辅助分子与坏结构外的**整个 PDB** 训练，因此配体、核酸、糖链、金属、翻译后修饰（PTM）、非典型氨基酸等 PDB 里常见的「模态」都在分布内——当然，训练数据里越少见的东西对模型越难。

### 1.3 快约一个数量级

RFD3 比 RFD1/RFD2 **快约一个数量级**（取决于体系长度）。这解锁了一种高效工作流：先给出很苛刻的约束，在生成阶段就按「约束是否满足」过滤，再花钱跑回折模型——不必每个设计都回折一遍。

## 二、PPI 条件控制：原子级热点与质心推断

### 2.1 从残基级到原子级热点

旧版 RFdiffusion 的热点（hotspot）是**残基级**的；RFD3 可以指定**原子级**热点——你想要靶标上某个具体原子（供体/受体）与设计蛋白相互作用。这是更硬的约束，模型并非每次都精确满足：实测约 **2/3** 的设计能让指定原子落在 4.5 Å 内，但「与该残基的某个原子发生近距离相互作用」几乎总能做到。

### 2.2 质心（center of mass）条件

可以给设计蛋白指定一个大致的质心区域（不必亚埃级精确）。多数 PPI 场景下这个位置其实由热点决定：官方推荐的做法是**由热点推断**——取热点质心、沿法线方向外推约 10 Å。主讲人建议新手从这里起步；当然也可以直接给三维坐标。

[【跳转到 03:40】](https://www.youtube.com/watch?v=LVN2l587C3M&t=220)

### 2.3 单模型，无适配器

RFD3 只有一个模型、没有隐藏适配器（adapters）：PPI、indexed/unindexed motif scaffolding、tip-atom motif scaffolding、氢键与 RSA 条件……全部在同一个模型的能力范围内，不用担心「换个任务就出分布」。

![单模型支持全部条件类型](assets/Protein%20Binder%20Design%20with%20RFDiffusion3/00245.webp)

[【跳转到 04:05】](https://www.youtube.com/watch?v=LVN2l587C3M&t=245)

## 三、YAML 配置逐行拆解（胰岛素受体示例）

### 3.1 文件结构

RFD3 的输入是一个 **JSON 或 YAML 文件**（两者嵌套结构与参数名完全一致，随个人喜好），命令行传给 RFD3。最基础的 PPI 用例只需要两件事：hotspot 位置 + 一个包含靶标结构的 PDB/SIF 文件（支持相对/绝对路径；示例用 RCSB 上裁剪好的胰岛素受体文件）。顶层可以有**多个 task**，一次运行依次解决多个设计问题。工具、教程与文档都在 GitHub 的 RosettaCommons/Foundry 仓库。

![YAML 顶层：task 与输入文件](assets/Protein%20Binder%20Design%20with%20RFDiffusion3/00400.webp)

[【跳转到 06:40】](https://www.youtube.com/watch?v=LVN2l587C3M&t=400)

### 3.2 context 字符串：三要素

context 字符串是 RFD3 指定输入的核心方式，包含三类组件——这正是经典 contigs（如条目里的 `A1-59/0 30-50`）在 RFD3 中的对应写法：

![context 字符串三要素](assets/Protein%20Binder%20Design%20with%20RFDiffusion3/00450.webp)

1. **diffused 残基**：完全交给模型设计的区域，没有链 ID（残基是全新实例化的）。`40-120` 表示每个 batch 从 40~120 残基中采样一个长度。
2. **链断点**：`/0` 语法。mini-binder 与靶标要放在不同的链上，所以在 binder 与靶标之间写链断点——与经典版 contigs 里 `/0` 的含义一致。
3. **从输入文件加载**：链 ID + 残基范围，如 `E6-155` 表示加载输入文件里 E 链第 6~155 位残基（双闭区间）作为靶标。

[【跳转到 07:30】](https://www.youtube.com/watch?v=LVN2l587C3M&t=450)

### 3.3 length 标志与 hotspots 块

- **length 标志**：基础 PPI 用不到；做 motif scaffolding 时有用——比如 motif 两侧各接一段 60~80 的新生成残基，又要求 mini-binder 总长不超过 150，就靠 length 约束实现「两段不能同时取到上限」。
- **hotspots 块**：在 `select_hotspots` 下指定链 ID + 残基号（必须是已从输入加载的范围内的残基，如 E 链 64 号），再为每个残基写明**原子名**，获得 4.5 Å 的原子级热点条件。

![select_hotspots：链 + 残基 + 原子名](assets/Protein%20Binder%20Design%20with%20RFDiffusion3/00525.webp)

[【跳转到 08:45】](https://www.youtube.com/watch?v=LVN2l587C3M&t=525)

### 3.4 non-loopy 标志

`non_loopy` 会把输出**偏向更有序的二级结构**。为什么推荐？PDB 里很多形成 PPI 界面的蛋白其实相当「loopy」（多环），但 AlphaFold3/RoseTTAFold3 这类回折模型对松散无序结构的置信度低——回折通过率会明显下降。除非你有特别理由需要完整的二级结构谱系，PPI 设计建议默认打开。

![non-loopy 标志的解释](assets/Protein%20Binder%20Design%20with%20RFDiffusion3/00625.webp)

[【跳转到 10:25】](https://www.youtube.com/watch?v=LVN2l587C3M&t=625)

### 3.5 运行命令与采样温度

克隆仓库、安装并下载权重后，运行形如 `rfd3 design` 的命令：给输出目录（设计文件与元数据都在这）、指向 YAML/JSON 的 `input`、权重 checkpoint 路径，外加两个可选的温度参数。**降低采样温度**的直观含义：更少从模型学到的高斯分布「边缘」采样，更多落在「中心」——产出更像正常蛋白、更有序的结构。是否要低温取决于用例（见下一节的多样性代价）。

## 四、参数实测：温度与 non-loopy 怎么影响设计

### 4.1 基准设定

评测用「可设计性（designability）= 回折通过率」：实心柱是整体通过率（每个骨架跑 4 条 MPNN 序列后回折），阴影柱是 **Foldseek 聚类通过率**（通过设计覆盖了多少聚类，衡量多样性）。对照组：蓝 = 低温 + non-loopy，橙 = 默认温度 + non-loopy，绿 = 完全基线（默认温度、无 non-loopy），红 = RFD1。回折用公开的 RFD3（性能与 AF3 相近），阈值较严格——binder 自身 pTM > 0.8、靶标对齐 binder RMSD < 2.5 Å（与 AlphaProteo 论文口径一致）。

![四组设置的回折通过率对比](assets/Protein%20Binder%20Design%20with%20RFDiffusion3/00710.webp)

[【跳转到 11:50】](https://www.youtube.com/watch?v=LVN2l587C3M&t=710)

### 4.2 低温：通过率换多样性

低温采样（蓝 vs 橙） unsurprisingly 提高整体通过率——采样到的都是「更正常」的东西；但许多任务的**聚类通过率反而下降**：默认温度下模型采样到分布边缘，设计彼此差异更大、聚类数明显更多。想要多样性就别把温度压太低。

### 4.3 non-loopy：删掉它，螺旋大减

温度对二级结构分布影响不大，但**去掉 non-loopy** 后分布显著移动：β 折叠略增、α 螺旋大减、环增多——作为对照，RFD1 基本是一台「螺旋束制造机」。去 non-loopy 换来一些多样性，但回折模型对这类松散设计的通过率明显更低。结论：PPI 场景把 non-loopy 当默认起点。

![二级结构分布：有无 non-loopy 的差别](assets/Protein%20Binder%20Design%20with%20RFDiffusion3/00835.webp)

[【跳转到 13:55】](https://www.youtube.com/watch?v=LVN2l587C3M&t=835)

### 4.4 Q&A：step_scale 与 gamma_0

两个参数殊途同归，都通向「低温采样」：`step_scale` 是把采样往分布中心推的力度；`gamma_0` 是每步加回的噪声量（下限 0，即完全不加噪、直接按模型偏好采样）。想压到比 `gamma_0=0` 更低的「温度」，就用 `step_scale`。

## 五、工具选型与两个「为什么」（Q&A 精华）

### 5.1 快生成 vs 幻觉反推：先想清楚要哪类

主讲人把设计模型分成两类：**快但命中率非满分**的生成-过滤型（RFD3），与**回折通过率极高但很慢**的「幻觉/反传」型（BindCraft、BoltzGen）。如果你要求「每个产出都过 AlphaFold」，选 BindCraft 这类，但要忍受更长的单设计耗时；想要单位时间出更多骨架、再用过滤收敛，RFD3 更合适。

### 5.2 RFD3 vs BoltzGen vs Complexa

同一基准上三方对比：RFD3 在 5 个任务中 3 个最好，但也有短板——胰岛素受体任务上 Complexa 明显更强，IL-7 受体 α 上 BoltzGen 最佳；多样性上 BoltzGen 偏低、Complexa 偏高。主讲人的建议很务实：如果搭建成本不高，**先在几个模型上试点**，看哪个对你的靶标最灵。

![RFD3 与 BoltzGen、Complexa 的对比](assets/Protein%20Binder%20Design%20with%20RFDiffusion3/01581.webp)

[【跳转到 26:21】](https://www.youtube.com/watch?v=LVN2l587C3M&t=1581)

### 5.3 为什么全原子了还要跑 ProteinMPNN

这是被问到最尖锐的问题。答案在 RFD3 的 **Atom14 表述**：每个残基用 14 个原子槽位（上限是色氨酸），残基用不到的槽位算「虚拟原子」，统一放到 Cβ 位置、最后清理。这个表述对人直观，但对模型很难：侧链是离散的、彼此在三维空间里差异很大，模型若想「把谷氨酰胺换成谷氨酸」，就得让原子在连续空间里横穿一段「两种残基之间全是垃圾」的插值路径——所以 RFD3 自带的序列设计质量还不理想，实验室正在改进。NVIDIA 的 LaProteina/Complexa 走潜空间路线，潜空间里化学相似残基彼此靠近、表示更平滑，是另一种思路。目前实践仍是 RFD3 生成骨架 →（旧版）ProteinMPNN 序列设计。

![Atom14 表述与虚拟原子](assets/Protein%20Binder%20Design%20with%20RFDiffusion3/01334.webp)

[【跳转到 22:14】](https://www.youtube.com/watch?v=LVN2l587C3M&t=1334)

### 5.4 实验数据：别忘了「甘氨酸 bug」星号

Q&A 里披露了一段内幕：早前实验室内部基准用的开发版模型有一个严重 bug——**从不生成甘氨酸**，导致骨架对甘氨酸不友好、MPNN 重设计命中率受损；当时多数靶标只拿到弱命中（微摩尔级~高纳摩尔级），PDL1 属于「最容易的靶标」。这些旧数字不能当作 RFD1 vs RFD3 的严格头对头结论；RFD3 目前的湿实验数据还在积累中。

## 小结

- RFD3 三大变化：全原子输出（序列+侧链坐标直接产出）、训练覆盖整个 PDB、比 RFD1/RFD2 快约一个数量级。
- 配置核心是 context 字符串三要素：diffused 残基（采样长度）、`/0` 链断点、`链+残基范围` 加载靶标——即经典 contigs 的 RFD3 版写法。
- 热点从残基级升级为原子级（4.5 Å）；质心可由热点推断（热点质心沿法向外推约 10 Å），新手推荐。
- 参数实测：低温提整体通过率但降聚类多样性；PPI 默认开 non-loopy（否则螺旋大减、回折通过率下滑）；`step_scale` 与 `gamma_0` 是控制「温度」的两个旋钮。
- 工具选型：快生成-过滤型（RFD3）与幻觉反推型（BindCraft/BoltzGen）各有分工；RFD3 并非全能（胰岛素受体任务败给 Complexa），建议多模型试点。
- 全原子不等于告别 ProteinMPNN：Atom14 表述下离散侧链的连续插值是模型短板，序列设计环节仍建议用 MPNN。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| 全原子（all-atom） | 模型直接输出主链 + 侧链全部原子坐标，序列与 rotamer 一并给出 |
| context 字符串 | RFD3 指定输入的核心语法：diffused 残基 / `/0` 链断点 / 从输入加载（链+残基范围） |
| `/0`（链断点） | 与经典 contigs 相同的链分隔记号，让 binder 与靶标分属不同的链 |
| 原子级热点 | 指定靶标上具体原子参与相互作用，精度 4.5 Å（约 2/3 设计精确满足） |
| 质心条件 | 约束设计蛋白质心的落点；可由热点质心沿法向外推约 10 Å 推断 |
| non-loopy | 偏向有序二级结构的开关；PPI 场景默认推荐，否则回折通过率下降 |
| 采样温度 | 越低越采样分布中心（更像正常蛋白），代价是多样性下降 |
| designability（可设计性） | 回折通过率：MPNN 序列回折后满足阈值（如 pTM>0.8、RMSD<2.5 Å）的比例 |
| Foldseek 聚类通过率 | 通过设计覆盖的 Foldseek 聚类数占比，衡量设计多样性 |
| Atom14 | 每残基 14 个原子槽位的全原子表述，用不到的槽位为「虚拟原子」（放 Cβ） |
| BindCraft / BoltzGen | 「幻觉/反传」类设计工具：回折通过率高但慢，与 RFD3 的快生成-过滤路线互补 |
