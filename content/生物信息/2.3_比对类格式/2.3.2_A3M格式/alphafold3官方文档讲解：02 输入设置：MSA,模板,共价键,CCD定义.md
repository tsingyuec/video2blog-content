# AlphaFold3 输入详解：MSA、模板、共价键、自定义 CCD 怎么填

> 视频来源：[alphafold3官方文档讲解:02 输入设置:MSA,模板,共价键,CCD定义](https://www.bilibili.com/video/BV11BzjYbEgD/?t=0)（Bilibili · 水无月的雨rt）
> 本文基于视频演说图文稿整理，配图截自视频。

## 本讲要解决的核心问题（SCQA）

**背景**：AlphaFold3 一次就能预测蛋白、DNA、RNA、小分子配体组成的复合物结构。它的输入是一份 JSON：除了序列本身，真正决定预测质量的，往往是 MSA（多序列比对）和结构模板这些"进化证据"字段。

**冲突**：官方文档里 MSA 字段有 5 种设置组合，自带 MSA 还有格式硬性要求；模板、共价键、自定义 CCD 又各有各的写法陷阱。新手照着文档直接手写 JSON，很容易在语法或语义上出错。

**疑问**：这些输入字段到底该怎么填？哪些必须自己准备，哪些交给 AlphaFold3 自动搜索就好？

**回答（中心思想）**：**先用自动搜索跑通，再按需手动定制**。MSA 可以不填（自动搜索），也可以自带——但必须是 A3M 格式、第一条序列与查询序列相同、非插入区长度一致；多链预测才需要关心 MSA 匹配（pairedMsa）；模板只对蛋白有意义；共价键用 `bondedAtomPairs` 的原子对列表表达；非标准分子靠 `userCCD` 自定义，并注意 JSON 的换行与引号转义。

---

## 一、MSA 字段：给不给、给多少，共 5 种组合

![AlphaFold3 官方文档的 MSA 字段说明：蛋白与 RNA 支持自带 MSA](assets/alphafold3官方文档讲解：02%20输入设置：MSA,模板,共价键,CCD定义/00000.webp)

MSA（Multiple Sequence Alignment，多序列比对）是把同源序列上下排成一列的比对结果：同一列上的残基被认为在进化上相互对应，模型借此判断哪些位置保守、哪些位置共同变化。AlphaFold3 的输入里，蛋白和 RNA 都支持自行提供 MSA；如果你不设置，AlphaFold3 会用两个内置工具自动去搜索序列数据库 [【跳转到 00:00】](https://www.bilibili.com/video/BV11BzjYbEgD/?t=0)。

### 1.1 RNA 的 MSA：三种设置

![RNA 的 unpairedMsa 字段：不设置、置空、或提供 A3M 字符串](assets/alphafold3官方文档讲解：02%20输入设置：MSA,模板,共价键,CCD定义/00025.webp)

RNA 只有一个 `unpairedMsa` 字段，有三种设置 [【跳转到 00:25】](https://www.bilibili.com/video/BV11BzjYbEgD/?t=25)：

1. **不写该字段，或显式设为 null**——不生成 MSA，官方的说法就是「MSA-free」；
2. **设置为空字符串**——效果与上面相同，也不会生成 MSA；
3. **设置为 A3M 格式的字符串**——AlphaFold3 就按你提供的这份 MSA 去做预测。

### 1.2 蛋白的 MSA：unpaired 与 paired 的 5 种组合

![蛋白的 unpairedMsa 与 pairedMsa 字段：可分别独立设置](assets/alphafold3官方文档讲解：02%20输入设置：MSA,模板,共价键,CCD定义/00050.webp)

蛋白的 MSA 分**未配对**（`unpairedMsa`）和**配对**（`pairedMsa`）两个独立字段，组合出 5 种用法 [【跳转到 00:50】](https://www.bilibili.com/video/BV11BzjYbEgD/?t=50)：

| # | unpairedMsa | pairedMsa | 效果 |
| --- | --- | --- | --- |
| 1 | 不填 / null | 不填 / null | 自动搜索数据库并生成两种 MSA（**官方推荐**） |
| 2 | 自带 MSA | 空字符串 | 只用你提供的未配对 MSA 作特征 |
| 3 | 空字符串 | 自带 MSA | 只用配对 MSA（官方不推荐） |
| 4 | 空字符串 | 空字符串 | 完全不使用 MSA |
| 5 | 自带 MSA | 自带 MSA | 完全按你提供的 MSA 预测 |

![第五种组合与"要么都设置、要么都不设置"的配对规则](assets/alphafold3官方文档讲解：02%20输入设置：MSA,模板,共价键,CCD定义/00100.webp)

特别要注意这条提示：对蛋白而言，这两个字段**要么都设置、要么都不设置**——哪怕你不需要配对 MSA，只要定义了 `pairedMsa` 字段，`unpairedMsa` 那边也得同时给出内容 [【跳转到 01:40】](https://www.bilibili.com/video/BV11BzjYbEgD/?t=100)。

![输入示例：模板为空、自带自定义 MSA 的 JSON 片段](assets/alphafold3官方文档讲解：02%20输入设置：MSA,模板,共价键,CCD定义/00120.webp)

示例里模板（templates）设置为空，只提供自定义的 MSA [【跳转到 02:00】](https://www.bilibili.com/video/BV11BzjYbEgD/?t=120)。

### 1.3 自带 MSA 的三条硬性要求（本讲核心）

![官方对自带 MSA 的三点要求：A3M 格式、首条序列一致、非插入区长度一致](assets/alphafold3官方文档讲解：02%20输入设置：MSA,模板,共价键,CCD定义/00133.webp)

如果你要自己指定 MSA，必须满足三点 [【跳转到 02:13】](https://www.bilibili.com/video/BV11BzjYbEgD/?t=133)：

1. **必须是 A3M 格式**。A3M 是 HH-suite 系工具提出的紧凑比对文本格式：对齐列用大写字母和 `-` 表示，相对查询序列的插入片段用小写字母紧跟其后，因此不需要填充空格，比 FASTA 形式的对齐紧凑得多。AlphaFold 体系的 MSA 搜索工具（如 ColabFold / AlphaFold Server 的序列搜索）输出的就是 `.a3m` 文件——这也是 Protenix、OpenFold3 这类兼容 AF3 输入体系的模型，把 MSA 输入指向 `.a3m` 文件的原因（详见本节另一篇 ColabFold 讲座的整理）。
2. **第一条序列必须与查询序列完全相同**——MSA 字段里的第一条，要和上面序列字段里的序列一模一样。
3. **非插入区长度一致**——查询序列与每条命中序列的大写对齐区长度必须相同。这一点只要用正常软件跑出来，一般就不会出错。

### 1.4 实操建议：先自动，再定制

![建议先让 AlphaFold3 自动搜索生成 JSON，再按需修改](assets/alphafold3官方文档讲解：02%20输入设置：MSA,模板,共价键,CCD定义/00158.webp)

UP 主的建议是不要一上来就手动设置：先让 AlphaFold3 自己跑一遍序列搜索，让它生成一个 JSON，再按自己的需要去改这个 JSON 文件；等你熟练之后，可以把其中的一些配置保存下来，作为自己的参考模板，后面继续复用 [【跳转到 02:38】](https://www.bilibili.com/video/BV11BzjYbEgD/?t=158)。

---

## 二、MSA 匹配：只有多链预测才需要操心

### 2.1 它解决什么问题

![MSA 匹配的作用：让多条链中相同物种的序列对齐到相同的 MSA 列](assets/alphafold3官方文档讲解：02%20输入设置：MSA,模板,共价键,CCD定义/00202.webp)

文档里说，只有**多链的折叠**——也就是多链复合体预测时，MSA 匹配才重要 [【跳转到 03:17】](https://www.bilibili.com/video/BV11BzjYbEgD/?t=197)。MSA 匹配的作用，是确保多条链里来自**相同物种**的 MSA 序列排在**相同的 MSA 列**上 [【跳转到 03:22】](https://www.bilibili.com/video/BV11BzjYbEgD/?t=202)。比如你要预测人的某个蛋白复合体，搜索结果里可能有人、小鼠等不同物种的序列，那就必须按固定顺序排列，否则就乱套了。

### 2.2 pairedMsa 如何匹配

![AlphaFold3 用 pairedMsa 字段、依据 UniRef 序列 ID 推断物种进行配对](assets/alphafold3官方文档讲解：02%20输入设置：MSA,模板,共价键,CCD定义/00227.webp)

AlphaFold3 靠 `pairedMsa` 字段来做这个匹配，主要依据 MSA 里的 UniRef 序列 ID 推断物种进行配对 [【跳转到 03:47】](https://www.bilibili.com/video/BV11BzjYbEgD/?t=227)。官方推荐两种做法：要么你**手动做好配对**，要么**只提供未配对的 MSA 字段**——这两种方式都能控制 MSA 的列排布，而不是让 pairedMsa 自动推断；而且你手动设置了 unpairedMsa 之后，配置文件里就不要再出现 pairedMsa 字段 [【跳转到 04:12】](https://www.bilibili.com/video/BV11BzjYbEgD/?t=252)。

### 2.3 文档的矛盾点，以官方回复为准

上面 1.2 节说"设了 pairedMsa 时另一个要设为空"，这一节又说"手动设置 unpairedMsa 后不要再出现 pairedMsa 字段"——两处说法有出入。UP 主的解释是：关于预计算 MSA 这个功能，GitHub 上有人提过问题、代码也做过修改，文档前后可能存在不一致；他打算去 GitHub 上问一下到底以哪种设置为准，到时候看官方怎么回复 [【跳转到 04:36】](https://www.bilibili.com/video/BV11BzjYbEgD/?t=276)。使用时建议自己用小任务验证一下当前版本的行为。

---

## 三、结构模板 templates：只对蛋白有意义

模板只能给**蛋白**设置，因为 RNA、DNA 和小分子配体设置模板没有意义 [【跳转到 05:01】](https://www.bilibili.com/video/BV11BzjYbEgD/?t=301)。

![模板条目：mmcif 字符串 + queryIndices/templateIndices 两个索引](assets/alphafold3官方文档讲解：02%20输入设置：MSA,模板,共价键,CCD定义/00306.webp)

每个模板条目里：第一个属性 `mmcif` 放 mmCIF 格式的字符串；另有 `queryIndices` 和 `templateIndices` 两个索引，编号都从 0 开始，分别是查询序列的编号列表和模板的编号列表，两个列表**长度必须一致** [【跳转到 05:06】](https://www.bilibili.com/video/BV11BzjYbEgD/?t=306)。比如要预测结构的第 0、1、2、3 位，分别对应模板的第 0、2、5、6 位残基。

你可以提供**多个**结构模板——在后面接逗号，接着写下一条模板；但每个模板条目里只能包含**一条链**，否则会报错 [【跳转到 05:31】](https://www.bilibili.com/video/BV11BzjYbEgD/?t=331)。`template` 字段也可以用 null 表示不使用模板进行预测 [【跳转到 05:56】](https://www.bilibili.com/video/BV11BzjYbEgD/?t=356)——或者干脆不写这个字段，让 AlphaFold3 自动从结构数据库里找模板 [【跳转到 06:04】](https://www.bilibili.com/video/BV11BzjYbEgD/?t=364)。

老规矩：如果你不熟悉，就先让 AlphaFold3 自己去找；多跑几个任务之后，看看它更新后的配置里模板字段是怎么写的，仿照着写就行 [【跳转到 06:20】](https://www.bilibili.com/video/BV11BzjYbEgD/?t=380)。

---

## 四、共价键 bondedAtomPairs

### 4.1 能做什么、不能做什么

![bondedAtomPairs：用于共价建模——共价对接、聚糖、短肽链](assets/alphafold3官方文档讲解：02%20输入设置：MSA,模板,共价键,CCD定义/00399.webp)

共价键可以用 `bondedAtomPairs` 字段来指定，用于共价建模，就好比以前的共价对接；也可以用它定义多个 CCD 配体，比如聚糖或者很短的肽链 [【跳转到 06:39】](https://www.bilibili.com/video/BV11BzjYbEgD/?t=399)。两个限制要注意：

- **聚合物内部不允许连键**：蛋白、DNA、RNA 自己内部不能直接用共价键连接，这种需求要用「修饰残基」的方式去定义 [【跳转到 07:04】](https://www.bilibili.com/video/BV11BzjYbEgD/?t=424)；
- **其他键合类型不支持**：比如离子键、金属键这些，目前都不支持 [【跳转到 08:16】](https://www.bilibili.com/video/BV11BzjYbEgD/?t=496)。

### 4.2 定义形式：原子对列表

![bondedAtomPairs 的定义形式：列表里每个元素是一对原子，代表一条共价键](assets/alphafold3官方文档讲解：02%20输入设置：MSA,模板,共价键,CCD定义/00435.webp)

定义形式是：最外层的 `bondedAtomPairs` 是一个列表，列表里每个元素是**一对原子**，代表一条共价键 [【跳转到 07:15】](https://www.bilibili.com/video/BV11BzjYbEgD/?t=435)。例如 A 链第 1405 号残基上的 SG 原子，与 L 链第 1 号残基的 C04 原子相连接；下一条共价键的写法也类似 [【跳转到 07:40】](https://www.bilibili.com/video/BV11BzjYbEgD/?t=460)。

### 4.3 原子名从哪来

对于蛋白、RNA 和 DNA，残基上的原子都有**标准的 CCD 原子名**——每个残基、每个原子的名字都是唯一的；但配体就没法这样定义共价键，这种情况就要用标准 CCD 或者自定义 CCD 来解决 [【跳转到 07:45】](https://www.bilibili.com/video/BV11BzjYbEgD/?t=465)。文档里给了两个例子：第一个是共价结合的配体，第二个是聚糖（糖苷键）[【跳转到 08:09】](https://www.bilibili.com/video/BV11BzjYbEgD/?t=489)。

---

## 五、聚糖：一串糖单元加几条共价键

![聚糖用 ligand 字段表示，再用共价键把糖单元与蛋白残基连起来](assets/alphafold3官方文档讲解：02%20输入设置：MSA,模板,共价键,CCD定义/00504.webp)

聚糖通常由多个糖苷键串联组成，在输入里用**配体**（ligand 字段）表示，然后要定义聚糖内部以及它与蛋白结合的共价键 [【跳转到 08:24】](https://www.bilibili.com/video/BV11BzjYbEgD/?t=504)。文档给的例子是聚糖与蛋白残基共价连接的情形：一个四糖与 A 链蛋白的 ASN 残基结合——你需要先定义 A 链蛋白的序列，配体就是这四个糖单元，然后定义总共四条共价键来表示它们之间的连接关系 [【跳转到 08:49】](https://www.bilibili.com/video/BV11BzjYbEgD/?t=529)。

（UP 主提醒：这一节文档讲得不算细，他自己对聚糖关注也不多，示例仅供参考。）

---

## 六、用户自定义 CCD（userCCD）

### 6.1 命名规则

![userCCD：自定义配体名称不能与已有 CCD 重复，且不要用下划线](assets/alphafold3官方文档讲解：02%20输入设置：MSA,模板,共价键,CCD定义/00559.webp)

你定义的配体名称必须和已有 CCD 配体名称不同，文档里举例叫 LIG1；名字里**不要用下划线**，要用横杠的形式，否则会报错——代码内部下划线有别的含义 [【跳转到 09:19】](https://www.bilibili.com/video/BV11BzjYbEgD/?t=559)。定义完成之后，就可以用这个新配体的名字以及它内部每个原子的名字，来设置 AlphaFold3 的配体和电荷信息；自定义 CCD 必须写在 `userCCD` 字段里 [【跳转到 09:44】](https://www.bilibili.com/video/BV11BzjYbEgD/?t=584)。

### 6.2 JSON 语法陷阱：\n 换行与单引号

JSON 不允许字符串直接换行，所以要用 `\n` 这个转义字符表示换行；化学式需要用**单引号**包围，而不是双引号。这是因为 JSON 的字符串最外层必须用双引号包围，内部如果要表示一段连续字符串（如 SMILES）就得用单引号，否则语法就错了——你内部也用双引号的话，解析器就会认为从前面那个双引号到它是同一个字符串，后面那段就不被当作字符串了 [【跳转到 10:09】](https://www.bilibili.com/video/BV11BzjYbEgD/?t=609)。

### 6.3 必填信息与理想坐标

在 userCCD 里主要需要提供的信息是：**原子名、元素、电荷信息，以及理想坐标**。理想坐标在构象生成失败的时候也可以作为参考。另外 userCCD 也可以重新定义标准残基，不过一般是去定义它的坐标——你改了坐标，对应的键长键角都会跟着变 [【跳转到 10:34】](https://www.bilibili.com/video/BV11BzjYbEgD/?t=634)。

![X7F 配体的 userCCD 示例：坐标与共价键信息，所有换行以 \n 转义](assets/alphafold3官方文档讲解：02%20输入设置：MSA,模板,共价键,CCD定义/00659.webp)

文档给了一个叫 X7F 的配体对应的 userCCD 示例，内容包括原子的坐标部分和共价键的信息。注意：示例里所有换行最终都要替换成 `\n`，呈现为一整行字符串；文档里保留换行符只是为了可读性 [【跳转到 10:59】](https://www.bilibili.com/video/BV11BzjYbEgD/?t=659)。

### 6.4 别手写，用工具生成

![ccdutils：把 PDB 中的化学物质转成 CCD 编码](assets/alphafold3官方文档讲解：02%20输入设置：MSA,模板,共价键,CCD定义/00709.webp)

PDB 官网有关于这个格式的具体说明，但这一长串纯靠手写是不现实的。UP 主找了一个 CCD 生成库，叫 ccdutils，它可以把 PDB 中的化学物质转化成 CCD 编码；不过具体用法他之前也没接触过 CCD，大家可以自己去看这个库的使用方法 [【跳转到 11:49】](https://www.bilibili.com/video/BV11BzjYbEgD/?t=709)。

文档最后给了一个完整的输入示例，主要是从语法角度演示的，它本身并没有什么实际含义。以上就是 AlphaFold3 全部输入项的说明 [【跳转到 12:14】](https://www.bilibili.com/video/BV11BzjYbEgD/?t=734)。

---

## 小结

- **MSA 可不填也可自带**：不填就自动搜索；自带必须满足三点——A3M 格式、第一条序列与查询序列完全相同、非插入区长度一致。
- **蛋白 MSA 两个字段"要么都设置、要么都不设置"**：unpaired 提供单链进化证据，paired 用于多链匹配；只用其中一个时按官方推荐组合填写。
- **MSA 匹配只在多链预测时重要**：目的是让相同物种的序列对齐到相同 MSA 列，靠 UniRef 序列 ID 推断物种；文档在预计算 MSA 的设置上前后有出入，以官方后续回复为准。
- **模板只对蛋白有意义**：mmCIF 字符串 + 从 0 编号的残基索引对，可多条但每条只能一条链；设 null 或不写就走自动搜索。
- **共价键 = `bondedAtomPairs` 原子对列表**：聚合物内部不支持直接连键（用修饰残基表达），离子键/金属键等其他键型不支持。
- **聚糖与自定义 CCD**：聚糖用 ligand + 多条共价键表达；非标准配体写 `userCCD`——命名避下划线、字符串换行用 `\n`、化学式用单引号，提供原子名/元素/电荷/理想坐标，推荐用 ccdutils 生成。
- **实操路线**：先让 AlphaFold3 自动跑通并生成 JSON，再仿照官方生成的配置手动定制，熟练后沉淀为自己的参考模板。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| MSA | 多序列比对：把同源序列排成列，为模型提供进化与保守性证据 |
| A3M | HH-suite 系的紧凑比对文本格式：对齐列用大写字母与 `-`，插入片段用小写字母；AF3 自带 MSA 的要求格式，也是 MSA 搜索工具（如 ColabFold）的标准输出 |
| unpairedMsa / pairedMsa | AF3 输入里两个独立的 MSA 字段：前者提供各链自身的进化证据，后者用于多链预测时同物种序列的列对齐 |
| templates | 结构模板：以 mmCIF 字符串 + 残基索引对的形式提供同源结构，仅对蛋白有意义 |
| bondedAtomPairs | 共价键字段：原子对列表，每对原子代表一条共价键 |
| userCCD | 自定义化学组件字典：定义非标准配体的原子名、元素、电荷、键与理想坐标 |
| ccdutils | 把 PDB 中的化学物质转成 CCD 编码的生成库 |
