# 抗体人源化与回复突变：框架区不是"背景板"，而是 CDR 的地基

> 视频来源：[Antibody Humanization and Back Mutations](https://www.youtube.com/watch?v=7fHEKCQuj3I&t=0)（YouTube · Schrödinger）
> 本文基于视频演说图文稿整理，配图截自视频。

## 本讲要解决的核心问题（SCQA）

**背景**：早期的治疗性抗体多来自小鼠等非人物种，结合特异性很好；但人体免疫系统会把它们当作"外来物"，产生免疫原性（immunogenicity）风险。

**冲突**：把整条抗体换成人的序列，特异性就没了；只把非人的 CDR 移植到人源抗体上，又可能丢掉框架区中**暗中决定 CDR 形状**的关键残基，稳定性与亲和力双双受损。

**疑问**：人源化到底该怎么"移"，才能既保住结合活性，又把免疫原性降下来？

**回答（中心思想）**：主流答案是 **CDR 移植（CDR grafting）**——但移植时必须连框架区中的 **CSR（规范结构残基）** 与 **Vernier 区残基**一起带走，移植后再用**回复突变（back mutations）**修补稳定性与亲和力。一句话：框架区不是背景板，而是 CDR 的"地基"。

![视频标题页：Antibody Humanization and Back Mutations（Schrödinger）](assets/Antibody%20Humanization%20and%20Back%20Mutations/00007.webp)

## 一、三种人源化策略 [【跳转到 00:07】](https://www.youtube.com/watch?v=7fHEKCQuj3I&t=7)

历史上为降低免疫原性风险，出现过三种流行策略：

### 1.1 嵌合抗体（chimeric antibody） [【跳转到 00:22】](https://www.youtube.com/watch?v=7fHEKCQuj3I&t=22)

把**一个物种抗体的可变区**与**人类抗体的恒定区**融合在一起。第一个嵌合抗体于 **1994 年**获 FDA 批准；不过近年来，它已不如后面两种技术流行。

![嵌合抗体示意：非人可变区（VH/VL）+ 人源恒定区](assets/Antibody%20Humanization%20and%20Back%20Mutations/00022.webp)

### 1.2 CDR 移植（CDR grafting） [【跳转到 00:47】](https://www.youtube.com/watch?v=7fHEKCQuj3I&t=47)

比嵌合抗体更进一步：只把**非人的 CDR** 移植到**人的框架区（human framework）**上，框架区也换成人的，免疫原性更低。

![CDR 移植示意：非人 CDR 移到人类框架区上](assets/Antibody%20Humanization%20and%20Back%20Mutations/00047.webp)

### 1.3 转基因动物（transgenic animals） [【跳转到 01:12】](https://www.youtube.com/watch?v=7fHEKCQuj3I&t=72)

通过基因改造，把动物（通常是小鼠）基因组中自身的免疫球蛋白基因替换成**人类免疫球蛋白基因**，让动物直接合成"人源"抗体，从源头消除免疫原性顾虑。在 **2002–2018 年**间获 FDA 批准的 **28 个人源化抗体**中，大多数都借助了某种转基因小鼠。

本视频聚焦第二种——CDR 移植（当然，嵌合抗体也可以在抗体结构预测面板中构建）。

![三种策略同框：嵌合抗体、CDR 移植、转基因小鼠](assets/Antibody%20Humanization%20and%20Back%20Mutations/00072.webp)

## 二、CDR 移植是一个迭代过程 [【跳转到 01:34】](https://www.youtube.com/watch?v=7fHEKCQuj3I&t=94)

CDR 移植不是"一次移植、一锤定音"，而是一个循环：

1. **找到潜在的人类框架供体**；
2. 移植后，**保留或突变回**部分框架残基到非人形式（back mutation 的伏笔）；
3. **实验评估**所得抗体；
4. 根据结果**进一步调整**：决定保留哪些非人残基，必要时**更换新的框架供体**，回到第 1 步。

![CDR 移植的迭代闭环：识别框架供体并移植 CDR → 保留或回复突变部分非人残基 → 制作、测试与分析](assets/Antibody%20Humanization%20and%20Back%20Mutations/00094.webp)

## 三、计算人源化的整体流程 [【跳转到 01:56】](https://www.youtube.com/watch?v=7fHEKCQuj3I&t=116)

基于 CDR 移植的计算机辅助人源化，流程分四步：

1. **载入**（鼠源）抗体结构；
2. **筛选兼容的人类框架**：扫描 PDB 数据库，用打分函数排序；
3. 在排序最高的框架上**执行 CDR 移植**；
4. （可选）进行**回复突变（back mutations）**。

其中第 2 步筛选时就要圈定移植对象：除了 CDR H1–H3 / L1–L3，还有 **VZ 和 CSR**——这正是下一节的主角。

![计算人源化四步：载入结构 → 检测兼容人类框架 → 在最高排名框架上移植 CDR → 回复突变](assets/Antibody%20Humanization%20and%20Back%20Mutations/00116.webp)

## 四、为什么框架区不能丢：CSR 与 Vernier 区 [【跳转到 02:15】](https://www.youtube.com/watch?v=7fHEKCQuj3I&t=135)

移植时如果只搬 CDR、丢掉框架区，常常会出问题——因为框架区里藏着两类"决定 CDR 长什么样"的残基：

### 4.1 CSR：规范结构残基（canonical structural residues）

CSR 是**框架区中决定 CDR 构象（conformation）的关键残基**。Biogen 2013 年的论文指出了 CSR 对抗体**亲和力与稳定性**的作用：突变 CSR 时，通常会出现**稳定性下降与亲和力下降相伴**的现象。

### 4.2 Vernier 区（VZ）：垫在 CDR 下面的 30 个残基 [【跳转到 02:40】](https://www.youtube.com/watch?v=7fHEKCQuj3I&t=160)

Vernier 区残基是**影响 CDR 构象的 30 个残基**：重链可变区（VH）16 个、轻链可变区（VL）14 个。2008 年的一篇论文发现，突变 Vernier 区残基会带来**显著的热力学后果**——说明它们既参与抗体与抗原的结合，突变它们也有风险。

![非人结构示意：CDR H1–H3、L1–L3 之外的 VZ（Vernier Zone）与 CSR（Canonical Structural Residues）位于框架区](assets/Antibody%20Humanization%20and%20Back%20Mutations/00135.webp)

### 4.3 成功案例：赫赛汀 [【跳转到 03:05】](https://www.youtube.com/watch?v=7fHEKCQuj3I&t=185)

总的来说，**保留 Vernier 区残基的 CDR 移植是成功的**——最著名的例子就是赫赛汀（Herceptin，即曲妥珠单抗 trastuzumab）。

## 五、怎么挑人类框架供体：序列相似性 + stem 几何 [【跳转到 03:21】](https://www.youtube.com/watch?v=7fHEKCQuj3I&t=201)

无论人类框架来自预置数据库还是自建数据库，排序都靠同一个**打分函数**，它由两部分组成：

1. **序列相似性**：候选框架与待人源化抗体轻重链序列的相似程度；
2. **stem 几何适配分**：衡量 CDR 环根部形状的兼容性。**stem 残基**是框架区中**直接连接 CDR 环**的残基——环安在什么样的"插座"上，直接影响环的构象。

![打分函数的两大组成：序列相似性 + stem 几何适配分（数值越低越好）](assets/Antibody%20Humanization%20and%20Back%20Mutations/00201.webp)

### 5.1 几何分怎么算 [【跳转到 03:46】](https://www.youtube.com/watch?v=7fHEKCQuj3I&t=226)

几何分比较的是**天然抗体**与**移植后抗体**之间，stem 残基与 CDR 环首/末残基之间那个肽键上的三项几何量的 RMSD：

- **C–N 距离**（跨肽键的两个原子间距）；
- **C–N–C 键角**；
- **C–C–N–C 二面角**。

该打分函数**数值越低越好**。

### 5.2 移植：VZ + CSR 随非人 CDR 一起走 [【跳转到 04:05】](https://www.youtube.com/watch?v=7fHEKCQuj3I&t=245)

人类框架选定后，构建人源化模型时，把 **Vernier 区残基、CSR 与非人 CDR 一起移植**过去——而不只是 CDR。

![鼠源的 VZ 与 CSR 随非人 CDR 一起移植到人类框架上](assets/Antibody%20Humanization%20and%20Back%20Mutations/00245.webp)

### 5.3 回复突变：修补移植留下的毛病

移植完成后，模型上难免出现**空间冲突（steric clashes）**等问题残基，这时用**回复突变（back mutations）**处理：要么把该位置**变回非人抗体中的原始残基**，要么换成**种系基因库中该位置最常见的残基**——这正是"人源框架 + 回复突变"的意义。

![回复突变：在人源框架上保留/引入回复残基，解决空间冲突等问题残基](assets/Antibody%20Humanization%20and%20Back%20Mutations/00270.webp)

## 小结

- 人源化三策略：**嵌合抗体**（1994 首个获批）、**CDR 移植**（本视频主角）、**转基因动物**（2002–2018 年 28 个获批人源化抗体的大多数）。
- CDR 移植是**迭代**过程：选供体 → 移植 → 评估 → 回复突变或换供体。
- 框架区里有两类"CDR 地基"残基：**CSR**（决定 CDR 构象；突变常伴随稳定性与亲和力双降）与 **Vernier 区**（30 个残基：VH 16 + VL 14；突变有显著热力学后果）。
- 挑人类框架供体的打分 = **序列相似性 + stem 几何适配**；几何分考察 C–N 距离、C–N–C 键角、C–C–N–C 二面角的 RMSD，越低越好。
- 移植时 **VZ + CSR 随非人 CDR 一起走**；之后用**回复突变**（回非人原始残基或种系常见残基）解决空间冲突——赫赛汀是保留 VZ 的 CDR 移植最著名成功案例。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| 免疫原性（immunogenicity） | 药物被人体免疫系统当作外来物攻击的风险 |
| 嵌合抗体（chimeric antibody） | 非人可变区 + 人源恒定区的融合抗体 |
| CDR 移植（CDR grafting） | 把非人 CDR 移植到人类框架区上的人源化方法 |
| 转基因动物 | 基因组中替换入人免疫球蛋白基因、直接产人源抗体的小鼠等 |
| 框架供体（framework donor） | 提供人源框架区的参照抗体 |
| CSR（canonical structural residues） | 框架区中决定 CDR 构象的规范结构残基 |
| Vernier 区（VZ） | 垫在 CDR 之下、影响其构象的 30 个框架残基（VH 16 + VL 14） |
| stem 残基 | 框架区中直接连接 CDR 环的残基，决定环的"插座"几何 |
| 回复突变（back mutations） | 人源化后把个别位置改回非人原始残基或种系常见残基，修补稳定性/亲和力 |
| Herceptin（赫赛汀） | 曲妥珠单抗的商品名，保留 VZ 的 CDR 移植最著名成功案例 |
