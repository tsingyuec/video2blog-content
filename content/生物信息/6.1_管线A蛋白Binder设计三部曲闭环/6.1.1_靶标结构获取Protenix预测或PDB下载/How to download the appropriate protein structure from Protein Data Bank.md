# 如何从 PDB 挑选并下载合适的蛋白结构（含 Pharos 可成药靶点库）

> 视频来源：[How to download the appropriate protein structure from Protein Data Bank](https://www.youtube.com/watch?v=PRx-iyY96q0)（YouTube，26 分钟）

## 本讲要解决的核心问题（SCQA）

**背景**：药物发现与对接研究都需要靶标蛋白的三维结构，PDB（Protein Data Bank）是最大的生物大分子 3D 结构公共库（视频录制时收录 21 万余个结构）。

**冲突**：搜一个「hemoglobin」，PDB 返回约 3,950 个结构——物种、解析方法、分辨率、突变状态、有无配体各不相同；单独的蛋白结构和与配体共晶的复合物结构，在对接中的表现还不一样；而且晶体结构普遍缺残基。

**疑问**：怎么从几千个结构里挑出「合适」的那个？如果连选哪个靶点都不确定，又该去哪查？

**回答（中心思想）**：先用「物种 → 实验方法 → 分辨率」三层过滤把候选收敛到几十几百个，再按「关联论文目的、共晶配体、野生型、无缺失残基」四条标准定稿；下载后在可视化软件里清理水分子与杂原子、检查缺失残基；选靶点本身可以借助 NIH 的 Pharos 数据库，按 Tdark/Tbio/Tchem/Tclin 四级筛选可成药靶点。

## 一、PDB 搜索：从 3,950 个血红蛋白结构开始

### 1.1 PDB 是什么

在 Google 搜「Protein Data Bank」进入 [RCSB PDB](https://www.rcsb.org)。PDB 是最大的生物大分子三维结构库，绝大多数是蛋白结构，全部由实验方法测定。

![RCSB PDB 主页](assets/How%20to%20download%20the%20appropriate%20protein%20structure%20from%20Protein%20Data%20Bank/00090.webp)

### 1.2 关键词搜索

在搜索框输入感兴趣的蛋白名（视频以血红蛋白 hemoglobin 为例——它负责氧气运输，存在于红细胞中），返回约 **3,950** 个结构；每页显示条数可调（25 或 50）。

![搜索 hemoglobin 返回约 3,950 个结构](assets/How%20to%20download%20the%20appropriate%20protein%20structure%20from%20Protein%20Data%20Bank/00111.webp)

## 二、三层筛选：物种 → 方法 → 分辨率

### 2.1 第一层：按物种过滤

用左侧 Refinement 面板选 **Homo sapiens**（人类）：3,950 个中来自人源的有 1,114 个，点击后列表只剩这些人源结构。

![按 Homo sapiens 过滤](assets/How%20to%20download%20the%20appropriate%20protein%20structure%20from%20Protein%20Data%20Bank/00197.webp)

### 2.2 第二层：按实验方法过滤

这些结构都是实验方法解析的——X 射线晶体学、NMR 或电镜等，而不是 AI 生成的方法。其中用 X 射线衍射（X-ray diffraction）解析的有 1,019 个。**优先选 X-ray 结构**；如果目标蛋白没有 X-ray 结构，再考虑电镜、NMR 或其他方法。

![按实验方法 X-ray diffraction 过滤](assets/How%20to%20download%20the%20appropriate%20protein%20structure%20from%20Protein%20Data%20Bank/00222.webp)

### 2.3 第三层：按分辨率过滤

分辨率（resolution）衡量晶体结构细节与清晰程度，是评估三维原子模型质量的关键参数，单位是 Å（埃）——**Å 数值越小，分辨率越高**，结构越清晰、细节越多。

在分辨率面板里：0.5–1.0 Å 区间只有 5 个结构；视频勾选了 0.5–1、1–1.5、1.5–2，再加上 2–2.5 这个可接受的范围，筛选后列表只剩 **832** 个结构。

![勾选 0.5–2.5 Å 分辨率区间](assets/How%20to%20download%20the%20appropriate%20protein%20structure%20from%20Protein%20Data%20Bank/00297.webp)

![筛选后剩 832 个高分辨结构](assets/How%20to%20download%20the%20appropriate%20protein%20structure%20from%20Protein%20Data%20Bank/00322.webp)

选结构的第一条准则就是：**分辨率越高越好**；当然还有其他准则，要结合研究目的来综合筛选。

## 三、点开 7JY3：按研究目的定稿

### 3.1 先读关联论文的目的

视频选中 PDB ID **7JY3** 打开详情页。选 PDB ID 的第二条重要准则，是看它**关联的论文**：作者解析了血红蛋白晶体并上传了 4 个不同的晶体结构，先搞清楚为什么解析 4 个、研究目的是什么。这项研究的目的，是设计血红蛋白的调节剂（modulator）——他们设计的 23 号合成抑制剂（compound 23，即 PF-0705901）是强效调节剂。

![打开 7JY3 详情页](assets/How%20to%20download%20the%20appropriate%20protein%20structure%20from%20Protein%20Data%20Bank/00372.webp)

### 3.2 下载共晶复合物作对照

所以应该下载 **23 号合成抑制剂与血红蛋白共晶**的那个结构。它能帮你把自己药物分子与血红蛋白的相互作用，和 23 号抑制剂的相互作用做对比——这个复合物就是研究的**对照**；还能从配体结合信息里看到参与相互作用的关键残基。

![7JY3 与 compound 23 共晶信息](assets/How%20to%20download%20the%20appropriate%20protein%20structure%20from%20Protein%20Data%20Bank/00430.webp)

### 3.3 野生型优先

详情页还会写明这个结构有没有突变。7JY3 没有任何突变——这不是突变研究而是药物设计研究，结构是**野生型（wild type）**。做药物设计时始终优先选野生型结构，因为氨基酸残基上任何突变都会改变蛋白的结合亲和力。

![检查突变信息：野生型](assets/How%20to%20download%20the%20appropriate%20protein%20structure%20from%20Protein%20Data%20Bank/00540.webp)

### 3.4 结合的分子与 IC50

这个血红蛋白结构上结合着血红素基团（heme group）、合成调节剂、氧分子和另一个合成小分子。蛋白结构的分辨率等细节都在详情页里，有时结合配体的 **IC50 值**也会标出来。

### 3.5 为什么选复合物而不是单独的蛋白

PDB 里也常有「只有蛋白」的结构。如果研究目的是药物发现，建议下载与已知抑制剂共晶的结构，因为：你可以把这个已知抑制剂**重新对接（re-dock）**到分子活性位点的口袋里得到一个对接打分，再拿它和待测分子的打分作比较——这是很好的验证做法。

更深一层的原因是**诱导契合（induced fit）**：配体结合后，蛋白的形状与活性位点的体积都会改变；抑制剂结合进活性位点口袋后，位点的大小和形状随之变化。把待测分子对接到这种「装过配体」的活性位点里更合理。而且对接软件通常把蛋白当成刚体——结晶后分子变刚性、位点形状保持不变，蛋白像一块石头，你是在石头的空腔里对接配体。所以**优先选蛋白-配体复合物，而不是单独的蛋白**。

## 四、下载与结构体检

### 4.1 下载 PDB 格式

在 7JY3 详情页点 **Download Files → PDB Format**，就会下载 `7JY3.pdb` 到本地。

![Download Files 下载 PDB 格式](assets/How%20to%20download%20the%20appropriate%20protein%20structure%20from%20Protein%20Data%20Bank/00753.webp)

### 4.2 可视化与清理

PDB 结构需要用可视化软件打开。常用软件里 **BIOVIA Discovery Studio** 是免费的，Windows/Mac 都能装。下载的蛋白结构里除了氨基酸，还有：水分子（图中红点）、结晶所需的各类离子等「杂质」，以及结合的配体和其他杂原子——都可以在软件里移除。

![Discovery Studio 打开结构，红点为水分子](assets/How%20to%20download%20the%20appropriate%20protein%20structure%20from%20Protein%20Data%20Bank/00859.webp)

### 4.3 缺失残基检查

下载后必须检查结构**有没有缺失残基（missing residues）**：

- 这条多肽链的第一个氨基酸是 **Gln 8**——1～7 号残基缺失了。因为这段是**环区（loop）**，很细，电子密度图很难解析，作者知道序列但定不出坐标；
- 链应该在 Lys 43 之后接 44、45、46……但直接跳到了 **Lys 53**——中间约 10 个残基缺失，多肽链实际上是断裂的。

![序列视图中缺失残基的断口](assets/How%20to%20download%20the%20appropriate%20protein%20structure%20from%20Protein%20Data%20Bank/01014.webp)

缺失残基对**分子对接影响不大**（对接中蛋白是刚性的，不会动），但对**分子动力学模拟是隐患**：MD 里蛋白会水化、运动，两个断片可能分开。所以优先选无缺失残基的结构；实在没有，就用软件补——**MODELLER**（常用于同源建模）、**PDBFixer** 等都能添加缺失残基，但最好还是避开有缺失的结构。

## 五、Pharos：不知道选什么靶点时去这里

### 5.1 数据库定位

[Pharos](https://pharos.nih.gov) 由美国国立卫生研究院（NIH）维护，收录**可成药蛋白靶点（druggable protein targets）**的信息。Google 搜「Pharos database」即可进入。

![Google 搜索 Pharos database](assets/How%20to%20download%20the%20appropriate%20protein%20structure%20from%20Protein%20Data%20Bank/01134.webp)

### 5.2 LDHA 示例：Tdark / Tbio / Tchem / Tclin

视频以乳酸脱氢酶 A（LDHA）为例。靶点页面有蛋白摘要，以及 **IDG development level** 四个类别：

| 类别 | 含义 |
| --- | --- |
| Tdark | 几乎没有任何信息 |
| Tbio | 有部分信息（如已关联某些疾病） |
| Tchem | 已有活性配体/合成抑制剂报道 |
| Tclin | 已有上市批准药物 |

LDHA 有合成抑制剂报道，所以是 **Tchem**；但还没有针对它的上市药物，所以不是 Tclin。想找「尚无上市药物」的靶点就筛 Tchem，想找已有药物的靶点就筛 Tclin。也可以按疾病搜索，服务器会列出该疾病可能作为药物设计靶点的蛋白。

![Pharos 的 LDHA 靶点页（Tchem）](assets/How%20to%20download%20the%20appropriate%20protein%20structure%20from%20Protein%20Data%20Bank/01198.webp)

### 5.3 从 Pharos 直达 PDB

靶点页还列出该蛋白的序列与结构信息：所有 PDB ID 及其分辨率，点击链接直接跳到 PDB（视频里打开了 [1I10](https://www.rcsb.org/structure/1I10)）。该靶点已知的合成抑制剂及 IC50 值也都能查到——文献综述之外，这是一个快速圈定靶点的实用工具。

![从 Pharos 跳转到 PDB 的 1I10](assets/How%20to%20download%20the%20appropriate%20protein%20structure%20from%20Protein%20Data%20Bank/01392.webp)

## 小结

- 挑结构的顺序：物种 → 实验方法（X-ray 优先）→ 分辨率（Å 越小越好），三层过滤快速收敛。
- 定稿四问：关联论文的研究目的是什么？有没有共晶配体？是不是野生型？有没有缺失残基？
- 药物发现优先选「蛋白-配体共晶复合物」：可作为 re-dock 对照，且活性位点形态更接近真实结合状态（诱导契合）。
- 下载 PDB 格式后，在 Discovery Studio 等软件里清理水分子/离子/杂原子，并检查缺失残基；缺失残基对接无碍、MD 有碍，可用 MODELLER / PDBFixer 修补。
- 选靶点不确定时，用 Pharos 按 Tdark/Tbio/Tchem/Tclin 分级筛选，还能从靶点页直达 PDB 结构与抑制剂 IC50 信息。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| PDB（RCSB PDB） | 收录实验测定生物大分子三维结构的公共数据库 |
| X-ray diffraction | X 射线衍射，解析蛋白晶体的主流实验方法 |
| resolution（分辨率） | 结构细节清晰程度的度量，单位 Å，数值越小越好 |
| 野生型（wild type） | 无人为引入突变的序列；药物设计优先选它 |
| 共晶复合物（co-complex） | 蛋白与配体一起结晶的结构，可作对接对照 |
| 诱导契合（induced fit） | 配体结合会改变蛋白活性位点大小与形状的理论 |
| 缺失残基（missing residues） | 晶体中电子密度不清晰、未解析出坐标的残基，链在此断开 |
| MODELLER / PDBFixer | 同源建模/补全缺失残基的常用软件 |
| Pharos | NIH 维护的可成药靶点数据库，按 Tdark/Tbio/Tchem/Tclin 分级 |
| IC50 | 抑制剂半数抑制浓度，数值越小活性越强 |
