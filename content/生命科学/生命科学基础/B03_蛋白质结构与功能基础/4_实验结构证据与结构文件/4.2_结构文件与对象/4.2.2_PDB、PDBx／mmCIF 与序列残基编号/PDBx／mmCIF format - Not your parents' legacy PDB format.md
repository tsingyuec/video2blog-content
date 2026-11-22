# PDBx/mmCIF format - Not your parents' legacy PDB format

> 视频来源：[PDBx/mmCIF format - Not your parents' legacy PDB format](https://www.youtube.com/watch?v=VTufgSK9_LU)（RCSB PDB mmCIF 课程，John Westbrook 主讲，约 16.7 分钟）。本文基于该视频的「图-字幕」演说文稿整理，所有要点均可回看视频核对。

**一句话结论：PDBx/mmCIF 用「字典驱动的分类表」取代了旧 PDB 格式的「固定列文本」——取值有字典管着、写法灵活等价、字段宽度与精度不受限，还能随实验方法演进不断扩展。**

## 本讲要解决的核心问题（SCQA）

**背景**：上一代的 legacy PDB 格式你已经很熟：每行固定列宽，原子坐标一行一个，看一眼就知道哪几列是什么。

**冲突**：可正是这套固定列设计，让旧格式装不下大分子研究需要的新数据：精度被列宽卡死、新实验方法产生的新数据类型无处安放，格式也不敢随便改——改了全世界的解析器都会坏。

**疑问**：既要能装下不断演进的新数据，又要让全球的软件都能稳定读写，格式该怎么设计？

**回答（中心思想）**：PDBx/mmCIF 的答案是「**把格式规则从文件里挪进字典**」：文件本身是自由的分类表（category），字段类型、取值范围、枚举、分类之间的关系全部由一本公开的字典（dictionary）来定义和校验——格式因此可扩展，数据质量还有保障。

## 一、这个格式有四个过人之处

作者开篇就给 PDBx/mmCIF 画了像 [【跳转到 00:00】](https://www.youtube.com/watch?v=VTufgSK9_LU&t=0)，四个特性环环相扣：

1. **灵活、可扩展**：可以按需扩展，新方法出现时字典跟着长 [【跳转到 00:19】](https://www.youtube.com/watch?v=VTufgSK9_LU&t=19)；
2. **机器为设计目标，人类也能读**：虽然是给机器读的格式，但示例文件人直接看也不吃力；
3. **字段宽度和精度无限制**：旧 PDB 格式装不下的大数字、高精度数值，这里随便放 [【跳转到 00:44】](https://www.youtube.com/watch?v=VTufgSK9_LU&t=44)；
4. **取值由字典控制**：每个值必须符合字典定义的类型——正则表达式、枚举（enumeration）、范围限制（limit）等。

第 4 点是精髓，下一节展开。

## 二、字典：给数据请的"质检员"

### 2.1 取值范围：硬约束与软建议

以结晶条件的 pH 为例，字典里写了两层规则 [【跳转到 03:36】](https://www.youtube.com/watch?v=VTufgSK9_LU&t=216)：

- **允许范围（allowed range）**：对多数生物样本，pH 取 0–14。存档中不应出现违反该范围的数据——这是硬约束；
- **建议边界条件（advisory boundary conditions）**：对所有已存入 PDB 的结构做统计分析后发现，结晶 pH 大多落在 **3.5–10** 之间。但这不是禁止——档案里就有 pH 3.0 长出的溶菌酶晶体：允许，只是不寻常 [【跳转到 04:01】](https://www.youtube.com/watch?v=VTufgSK9_LU&t=241)。

![pH 字典示例：允许范围 0–14 是硬约束，统计得出的 3.5–10 只是建议边界](assets/PDBx／mmCIF%20format%20-%20Not%20your%20parents'%20legacy%20PDB%20format/00241.webp)

### 2.2 枚举：从源头防错拼

另一类约束是**枚举**。例如"辐射源"（radiation source）字段，枚举里列出了全部合法取值——各同步辐射光源及其束线站（beamline）[【跳转到 04:26】](https://www.youtube.com/watch?v=VTufgSK9_LU&t=266)。提交者只能从列表里选，想手滑敲个错拼都敲不出来，数据从源头得到质量控制。

![辐射源枚举示例：从同步辐射装置到束线站，取值只能从列表中选](assets/PDBx／mmCIF%20format%20-%20Not%20your%20parents'%20legacy%20PDB%20format/00266.webp)

### 2.3 父子关系：分类之间也能挂上钩

分类与分类之间通过**父子关系（parent-child relationship）**约束。典型例子：一条引文（citation）是一个分类，它的作者（author）是另一个分类——一条引文可以有许多作者，靠 ID 把多个取值链接到一个上级分类上 [【跳转到 01:09】](https://www.youtube.com/watch?v=VTufgSK9_LU&t=69)。

### 2.4 字典本身是谁管的

这套字典并非 wwPDB 独家编写：它诞生于 1990 年代末，由国际晶体学联合会（IUCr）特许的工作组开发，目的是把 CIF 扩展到 macromolecular 数据 [【跳转到 02:46】](https://www.youtube.com/watch?v=VTufgSK9_LU&t=166)。如今的输入来自四方：wwPDB 作为贡献者之一、晶体学专家组成的 PDBx/mmCIF 工作组、为自有字典做扩展的开发者、以及广大用户的反馈 [【跳转到 03:11】](https://www.youtube.com/watch?v=VTufgSK9_LU&t=191)。字典在网站上公开可得，还配套了用字典校验数据的工具 [【跳转到 01:34】](https://www.youtube.com/watch?v=VTufgSK9_LU&t=94)。

![pH 结晶条件字典：展示字典如何为单个字段定义取值约束](assets/PDBx／mmCIF%20format%20-%20Not%20your%20parents'%20legacy%20PDB%20format/00191.webp)

### 2.5 一套体系，养出一族字典

PDBx/mmCIF 还是其他字典的基础 [【跳转到 01:34】](https://www.youtube.com/watch?v=VTufgSK9_LU&t=94)：

- **模型字典**：AlphaFold 与 AlphaFold DB 用的格式与 PDBx/mmCIF 相似、外加一些扩展，核心部分直接互通 [【跳转到 01:59】](https://www.youtube.com/watch?v=VTufgSK9_LU&t=119)；
- **IHM 字典**：由 PDB-Dev 存档系统使用，面向整合/混合建模（integrative hybrid methods）——坐标部分与各方法高度相似。

因为结构标题等公共信息在所有这些字典里表示一致，**你的解析器只要能读其中一种字典，为另一种新字典做少量扩展就能兼容** [【跳转到 02:24】](https://www.youtube.com/watch?v=VTufgSK9_LU&t=144)。对做 AI 结构模型的人来说，这是个直接利好。

![衍生字典生态：AlphaFold 模型字典与 IHM 字典都与 PDBx/mmCIF 同源](assets/PDBx／mmCIF%20format%20-%20Not%20your%20parents'%20legacy%20PDB%20format/00119.webp)

## 三、语法：两种等价写法

### 3.1 条目 = 分类 + 属性

PDBx/mmCIF 的数据以"条目-值"（item-value）对呈现。一个**条目（item）**定义为一个**分类（category）**加一个**属性（attribute）**的组合 [【跳转到 04:51】](https://www.youtube.com/watch?v=VTufgSK9_LU&t=291)：比如 `citation` 是分类名、`ID` 是属性名，两者合起来就是条目 `citation.ID`。

![条目的定义：分类名加属性名，如 citation.ID](assets/PDBx／mmCIF%20format%20-%20Not%20your%20parents'%20legacy%20PDB%20format/00291.webp)

### 3.2 晶胞实例：一个值怎么写、一张表怎么写

以脱氧血红蛋白 **4HHB** 条目为例，它的晶胞（unit cell）报告为 `cell` 分类下的各属性：a、b、c 三条轴的长度和三个夹角 [【跳转到 05:41】](https://www.youtube.com/watch?v=VTufgSK9_LU&t=341)。

同一份数据有两种完全等价的写法 [【跳转到 06:06】](https://www.youtube.com/watch?v=VTufgSK9_LU&t=366)：

- **item-value 对**：一个条目一行 `名 值`，适合单值；
- **loop（循环）语法**：先列举条目名，再跟一列数据值，天然呈表格形式，适合多行数据。

讲者展示了同一文本的四种写法：朴素的条目-值、跨多行的引号文本、以及需要时的 loop 多行表格——两种语法都支持这些变化 [【跳转到 06:31】](https://www.youtube.com/watch?v=VTufgSK9_LU&t=391)。另外，文本引号沿用 CIF 规范：字符串里可以包含单引号、双引号 [【跳转到 05:16】](https://www.youtube.com/watch?v=VTufgSK9_LU&t=316)。

![4HHB 晶胞示例：cell 分类下的 a/b/c 轴长与夹角](assets/PDBx／mmCIF%20format%20-%20Not%20your%20parents'%20legacy%20PDB%20format/00341.webp)

![loop 语法示例：先列条目名再列数据值，天然成表](assets/PDBx／mmCIF%20format%20-%20Not%20your%20parents'%20legacy%20PDB%20format/00366.webp)

## 四、entity：把所有分类串起来的核心概念

### 4.1 entity 是什么

把数据文件里众多分类串起来的核心概念是 **entity（实体）** [【跳转到 08:00】](https://www.youtube.com/watch?v=VTufgSK9_LU&t=480)。一个 entity 代表：

- 一条具体的**大分子聚合物链**（蛋白 / DNA / RNA）；
- 一个**分支状的碳水化合物**；
- 一个**配体或非聚合物**小分子；
- 或者一个**水分子**。

每个聚合物 entity 带着自己的序列，文件里所有相关分类都通过同一个实体 ID 关联起来 [【跳转到 08:25】](https://www.youtube.com/watch?v=VTufgSK9_LU&t=505)。

![entity 概念：聚合物链、分支碳水化合物、配体/非聚合物、水分子都算实体](assets/PDBx／mmCIF%20format%20-%20Not%20your%20parents'%20legacy%20PDB%20format/00480.webp)

### 4.2 序列怎么表示：非标准残基怎么办

读 mmCIF 序列时常见一个问题：那些没法用单字母编码表示的残基怎么办？mmCIF 提供了扩展格式——把内部使用的配体代码写进括号里 [【跳转到 08:50】](https://www.youtube.com/watch?v=VTufgSK9_LU&t=530)。讲者举了**磷酸丝氨酸**的例子：它本质上就是一个多带了一个修饰基团的丝氨酸；文件同时给出规范的单字母编码（按丝氨酸 S 计），所以做 BLAST 搜索时，用丝氨酸去搜就能命中。

![非标准残基的序列表示：括号内写配体代码，同时保留规范单字母编码](assets/PDBx／mmCIF%20format%20-%20Not%20your%20parents'%20legacy%20PDB%20format/00530.webp)

### 4.3 两套残基编号：序列序号 vs 作者编号

mmCIF 提供了一层映射：一边是作者在公开文件里使用的残基编号，另一边是 mmCIF 内部按序列顺序编排的编号 [【跳转到 09:12】](https://www.youtube.com/watch?v=VTufgSK9_LU&t=552)。做生信的人常常只想知道"这是序列里的第几个残基"——不关心作者把残基编成几号。这套映射正是为你准备的。

- 例一：序列中的**第一个**残基是组氨酸，但作者把它编为 B 链的 **311** 号残基 [【跳转到 09:37】](https://www.youtube.com/watch?v=VTufgSK9_LU&t=577)；
- 例二：4LAD 结构里序列有一大段空缺——521 到 572 之间在结构中缺失（图上以虚线表示）[【跳转到 10:02】](https://www.youtube.com/watch?v=VTufgSK9_LU&t=602)。mmCIF 的编号方式把这种缺失登记得清清楚楚，实验所及的每个残基都能对上号；
- 作者编号完全由作者自定：我们常看到**表达标签用负数开头**，这完全合法；唯一的要求是沿序列走下去编号必须递增 [【跳转到 11:50】](https://www.youtube.com/watch?v=VTufgSK9_LU&t=710)。

![两套编号对照：序列第一个残基是组氨酸，作者却编为 B 链 311 号](assets/PDBx／mmCIF%20format%20-%20Not%20your%20parents'%20legacy%20PDB%20format/00577.webp)

![4LAD 的序列空缺：521–572 在结构中缺失，用虚线表示](assets/PDBx／mmCIF%20format%20-%20Not%20your%20parents'%20legacy%20PDB%20format/00602.webp)

![作者编号可以很任性：表达标签用负数开头完全合法，只要求沿序列递增](assets/PDBx／mmCIF%20format%20-%20Not%20your%20parents'%20legacy%20PDB%20format/00710.webp)

### 4.4 asym ID：给每条链、每个配体发唯一"工牌"

坐标部分比旧版 PDB 丰富，其中第一个重点是 **asym ID**：每条聚合物链从 A 到 Z 依次标注，26 个字母用完后接着用双字母；每个配体也以类似方式标注，保证唯一 [【跳转到 11:00】](https://www.youtube.com/watch?v=VTufgSK9_LU&t=660)。想想这种情况：一个结构里同一聚合物链有两份拷贝——它们同属一个 entity、序列完全相同——但两个实例会分别拿到 A 链和 B 链的标识 [【跳转到 11:25】](https://www.youtube.com/watch?v=VTufgSK9_LU&t=685)。

![同一个 entity 的两份拷贝：序列相同，实例分别标为 A 链和 B 链](assets/PDBx／mmCIF%20format%20-%20Not%20your%20parents'%20legacy%20PDB%20format/00685.webp)

非聚合物（配体、离子、水）也用独立编号体系逐一枚举，既能保留作者的残基编号，也能盘点结构里的每个组成部分——比如这个结构里同时有硫酸根离子和乙酸根离子 [【跳转到 10:26】](https://www.youtube.com/watch?v=VTufgSK9_LU&t=626)。

## 五、struct_conn：把"连接关系"显式写进文件

分子内的连接关系用 **struct_conn** 分类显式记录 [【跳转到 12:23】](https://www.youtube.com/watch?v=VTufgSK9_LU&t=743)。讲者以**锌指**为例：锌离子与两个组氨酸、两个半胱氨酸之间的金属配位连接（metallo-link），涉及的残基（如 201 号）都逐条写明。

![struct_conn 示例：锌指结构中锌与两个组氨酸、两个半胱氨酸的金属配位](assets/PDBx／mmCIF%20format%20-%20Not%20your%20parents'%20legacy%20PDB%20format/00743.webp)

这些信息旧版 PDB 里其实也有，只是放的位置不同。真正的差距在**精度**：PDB 格式的距离只能写到 **2.14 Å**（列宽卡死），mmCIF 里可以写 **2.138**——没有空间限制 [【跳转到 12:48】](https://www.youtube.com/watch?v=VTufgSK9_LU&t=768)。

![精度对比：旧 PDB 格式只能写 2.14 Å，mmCIF 可以写 2.138](assets/PDBx／mmCIF%20format%20-%20Not%20your%20parents'%20legacy%20PDB%20format/00768.webp)

## 六、问答实录：三个你想问的问题

讲完正题，现场 Q&A 补充了不少实用信息 [【跳转到 13:52】](https://www.youtube.com/watch?v=VTufgSK9_LU&t=832)：

- **扩展 PDB ID 的正则表达式哪里找？** 发布在 wwPDB 的新闻页上，直播中稍后把链接发到了聊天区；
- **扩展 ID 的首字符定了吗？** 还没定（可能是数字，待确认）。设计时的两个考量 [【跳转到 14:42】](https://www.youtube.com/watch?v=VTufgSK9_LU&t=882)：一是文献中出现的任何 PDB ID 都应能被检索到——所以才加 `pdb_` 前缀；二是保证未来依然可用；
- **蛋白-配体相互作用记到什么程度？** 共价连接会明确记录——比如氯甲基酮类抑制剂与蛋白形成的共价键，在 struct_conn 里如实声明 [【跳转到 15:07】](https://www.youtube.com/watch?v=VTufgSK9_LU&t=907)；而只是空间邻近的非共价相互作用**不再记录**。以前用 SITE 记录表示的结合位点，大约四年前已停用；想看水分子或配体周边环境，可以去 rcsb.org 网站结构摘要页的配体专区，模型文件里没有这些内容 [【跳转到 15:32】](https://www.youtube.com/watch?v=VTufgSK9_LU&t=957)。

![总结页：字典与工具共同支撑约束良好的存档体系，且持续演进](assets/PDBx／mmCIF%20format%20-%20Not%20your%20parents'%20legacy%20PDB%20format/00798.webp)

## 小结

- PDBx/mmCIF = **分类表 + 字典**：文件是自由的分类表，字段类型、取值范围、枚举、分类间关系全由公开字典定义和校验；
- 格式四大特性：可扩展、机器可读人也-readable、字段宽度与精度无限制、取值受字典控制；
- 硬约束与软建议分层：pH 允许范围 0–14 是硬约束，统计得出的 3.5–10 只是建议；
- 两种等价语法：item-value 对与 loop 表格，单值多值各得其所；
- **entity** 串起所有分类；序列里非标准残基用括号扩展码，同时保留单字母编码供 BLAST；
- 两套残基编号（序列序号 vs 作者编号）通过映射共存，表达标签负数编号也合法，只要求递增；
- **asym ID** 给每条链、每个配体实例发唯一标识，同一 entity 的多份拷贝也能区分；
- **struct_conn** 显式记录共价/金属配位连接，精度不再受列宽限制。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| PDBx/mmCIF | PDB 生态的现代结构数据格式，"分类表 + 字典"取代固定列文本 |
| category / attribute / item | 分类（表）、属性（列）、条目（分类+属性的组合，即单元格） |
| dictionary（字典） | 定义字段类型、取值范围、枚举与分类关系的公开规范文件 |
| allowed range | 字典中的硬性取值范围，如 pH 0–14 |
| loop 语法 | mmCIF 的表格写法：先列条目名，再列数据值 |
| entity（实体） | 结构中的分子单元：聚合物链、分支碳水、配体/非聚合物或水 |
| asym ID | 链/实例标识（A–Z、双字母），同一 entity 的多份拷贝各有唯一 ID |
| struct_conn | 显式记录共价键、金属配位等连接关系的分类 |
| IHM 字典 | 面向整合/混合建模的 PDB-Dev 存档字典，坐标部分与 mmCIF 相通 |
| SITE 记录 | 旧格式中标注结合位点的方式，mmCIF 生态已停用（约四年前） |
