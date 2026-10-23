# OLS 把 150 多个生物医学本体收进了一个统一检索入口

> 视频：[Ontology Lookup Service (OLS)](https://www.youtube.com/watch?v=p8XF7yJvW4E)（EMBL-EBI，26:58，2016）

## 本讲要解决的核心问题（SCQA）

**背景**：生物医学数据里，同一个概念常有很多种说法；本体（ontology）给概念分配唯一 ID，并用“父子”“部分-整体”等关系把它们组织起来。

**冲突**：如果没有统一入口，这些本体散落在不同站点、不同格式里，更新频率和元数据写法也不一样。更麻烦的是，普通搜索引擎不理解概念之间的上下位关系：搜“色盲”能得到结果，搜更泛的“眼部异常”反而可能是 0 条。

**疑问**：有没有一个地方，能同时搜索、浏览、程序化访问这些生物医学本体？

**回答（中心思想）**：有，就是 **OLS（Ontology Lookup Service）**。它把 150 多个生物医学本体、约 450 万个术语、1100 万条关系放在一个入口里，提供搜索、树/图浏览、版本历史和 REST API，并用 ZOOMA 把自由文本批量映射到本体术语。

![用色盲/色觉异常的例子说明同一概念有多种说法](assets/Ontology%20Lookup%20Service%20%28OLS%29/00104.webp)

## 一、本体解决的是“让数据能对上”，不只是“给概念起名”

先看一个具体例子 [【跳转到 01:44】](https://www.youtube.com/watch?v=p8XF7yJvW4E&t=104)。色盲在医学文献里可能被写成 **color blindness**，也可能写成 **dichromatopsia**（色觉异常的一种）。讲者在 PubMed 上做了三次检索 [【跳转到 02:17】](https://www.youtube.com/watch?v=p8XF7yJvW4E&t=137)：

- 搜 `color blindness`：647 条结果；
- 搜 `dichromatopsia`：270 条结果；
- 搜更泛的 `abnormality of the eye`（眼部异常）：**0 条结果**。

前两个词指的是相关但不完全相同的概念，数量不同可以理解；真正的问题是第三个——搜索引擎不知道“色盲”是“眼部异常”的一种，所以不会自动把下位词的结果带出来。这正是本体要解决的问题。

![PubMed 检索结果：不同说法命中数量不同，泛化说法甚至是 0](assets/Ontology%20Lookup%20Service%20%28OLS%29/00137.webp)

构建一个本体，通常要做三件事 [【跳转到 03:01】](https://www.youtube.com/watch?v=p8XF7yJvW4E&t=181)：

1. **给概念分配 accession（登录号/ID）**：例如给 dichromatopsia 一个稳定 ID，之后所有数据都引用这个 ID，而不是各自的字符串。
2. **描述概念之间的关系**：dichromatopsia 是“色觉异常”的一种（`is_a`），而色觉异常又发生在眼部（`disease location in eye`）。关系不只“父子”，还有“部分-整体”（partonomy）等。
3. **补充元数据**：同义词（color blindness）、人类可读的定义、注释、外部数据库交叉引用等。

这样，数据就不再依赖自由文本，而是用数字 ID 来整合。讲者给了三类典型收益：

- **更聪明的搜索**：EBI 的 ArrayExpress 在后台用本体扩展查询，帮用户找到更多相关结果；
- **数据分析**：Gene Ontology（GO）用于基因功能分析；
- **数据整合与可视化**：GWAS Catalog 用本体术语注释性状，并按解剖部位、细胞类型等维度生成可视化。

![本体覆盖从基因型到表型的多个领域](assets/Ontology%20Lookup%20Service%20%28OLS%29/00217.webp)

## 二、OLS 的定位：150 多个本体的统一入口

OLS 本质上是一个**本体仓库 + 搜索引擎** [【跳转到 05:21】](https://www.youtube.com/watch?v=p8XF7yJvW4E&t=321)。视频里给出的规模是：

- **150 多个**生物医学本体；
- 约 **450 万个**术语；
- 约 **1100 万条**术语之间的关系；
- 每晚检查并更新一次。

数据主要来自 **OBO Foundry / OBO Library**。OBO Foundry 的目标是让生命科学本体互操作、减少范围重叠，因此 OBO Library 里的本体会被自动加载进 OLS；此外，EBI 也会加入与自己数据相关的本体，例如实验因子本体 **EFO**（Experimental Factor Ontology）。原则上，任何以 OBO 格式发布的本体都可以加载进来 [【跳转到 06:41】](https://www.youtube.com/watch?v=p8XF7yJvW4E&t=401)。

![OLS 首页给出本体数量、术语数量与最近更新时间](assets/Ontology%20Lookup%20Service%20%28OLS%29/00321.webp)

OLS 有三种使用方式：

1. **搜索**：按 label、同义词或 ID 找术语；
2. **浏览/可视化**：树视图或图视图；
3. **API**：RESTful API，供程序批量访问。

讲者特别强调：**大多数实际使用是通过 API 发生的**，网页只是入口。OLS 完全开源，代码在 GitHub 上；如果需要在本地访问自己的本体，也可以自己部署一套。

## 三、搜索：先泛搜，还是直接跳到某个本体？

OLS 首页的搜索框有一个很实用的设计：自动补全结果分成两段。

- **第一段是泛搜建议**：你只记得一个词，不确定它属于哪个本体；
- **第二段是 jump to**：如果你知道目标本体，可以直接跳到该本体里的术语。

以 `liver`（肝）为例。liver 在多个本体里都有条目，例如 Uberon（解剖学本体）、BTO、XAO、EMAP 等。知道本体名时，用 jump to 最快；不知道时，就用泛搜 [【跳转到 08:49】](https://www.youtube.com/watch?v=p8XF7yJvW4E&t=529)。

![搜索 liver 的结果页：标识符、描述，以及该术语出现在多个本体中的提示](assets/Ontology%20Lookup%20Service%20%28OLS%29/00584.webp)

结果页里值得注意的几点 [【跳转到 09:44】](https://www.youtube.com/watch?v=p8XF7yJvW4E&t=584)：

- 每条结果会显示 **ID、描述**；
- 排在最前面的通常是某个本体里的“主条目”，同时提示这个术语也出现在很多其他本体中——这往往说明它是一个比较适合作为“参考定义”的术语；
- 左侧可以勾选 **exact match**，只保留 label 完全匹配的结果；
- 也可以按本体过滤。比如只选 Uberon，就能把结果缩到一条。

这套“先看跨本体出现情况，再按本体过滤”的流程，比单纯看搜索排名更可靠。

## 四、术语页：一个 term 的“身份证 + 关系网”

点进一个术语后，页面会把它拆成几块信息 [【跳转到 10:37】](https://www.youtube.com/watch?v=p8XF7yJvW4E&t=637)。

**上方是定义**：这个术语是什么、对应哪个 ID。

**中间是树视图**：展示它在本体中的分类位置。树里不只有 `is_a`（是一种），还可能包含 `part_of`（是……的一部分）和 `develops_from`（由……发育而来）。讲者用 liver 举例：树里能看到 liver 是 exocrine system（外分泌系统）的一部分，而不是 endocrine system（内分泌系统）的一部分——这类区别在只看文字定义时很容易忽略。

![术语页把描述、树状分类和右侧元数据放在同一屏](assets/Ontology%20Lookup%20Service%20%28OLS%29/00637.webp)

**右侧是元数据**：

- 大量 **database cross references**（数据库交叉引用），有些可以直接跳到外部资源；
- depictions（图示）；
- 其他由本体提供的注释信息；
- 右下角的 **logical relationships**：把树里的关系压平成一个列表，方便快速查看；
- **related from**：有哪些术语的关系指向当前术语（incoming relations）。

同一个术语可能有多个父类（polyhierarchy），树视图能同时展示这些分类路径。如果树太深，可以切换到**图视图**：按关系类型开关边、点击节点继续探索 [【跳转到 11:48】](https://www.youtube.com/watch?v=p8XF7yJvW4E&t=708)。

![图视图可以按关系类型开关，并点击节点继续探索](assets/Ontology%20Lookup%20Service%20%28OLS%29/00708.webp)

## 五、本体主页与版本历史：本体是“活”的

每个本体在 OLS 里都有自己的主页 [【跳转到 12:35】](https://www.youtube.com/watch?v=p8XF7yJvW4E&t=755)。主页上可以：

- 下载该本体的各种格式；
- 跳到项目主页；
- 查看维护者联系方式；
- 从根节点开始浏览整个本体。

更重要的是 **history** 标签 [【跳转到 13:14】](https://www.youtube.com/watch?v=p8XF7yJvW4E&t=794)。OLS 不保存每一个历史版本，但会保存版本之间的 **delta（差异）**：哪些术语新增、哪些删除、哪些发生变化。你可以点进某一次 release，看这次具体加了哪些术语；单个术语也有自己的 history，能看到同义词等字段的变更。

![本体主页提供下载、项目主页、联系方式和从根节点浏览](assets/Ontology%20Lookup%20Service%20%28OLS%29/00755.webp)

这件事对实际使用很关键：如果你的数据引用了某个术语，而该术语在新版本里被删除或标记为 obsolete（废弃），你的注释就可能失效。OLS 还提供 API，方便你监控关心的术语是否发生重大变化。

## 六、API 与生态：网页只是入口

OLS 的每个页面右上角都有一个 **JSON 按钮** [【跳转到 14:31】](https://www.youtube.com/watch?v=p8XF7yJvW4E&t=871)，点开就能看到当前视图对应的 API 响应。术语的 JSON 里不仅有元数据，还带有导航链接：

- 指向 parents（父类）；
- 指向 ancestors（祖先）；
- 指向 graph-based representations（图表示）；
- 以及其他关系。

![每个页面右上角的 JSON 按钮把当前视图对应的 API 响应暴露出来](assets/Ontology%20Lookup%20Service%20%28OLS%29/00871.webp)

开发者文档里有完整的 REST API 说明，社区还维护了 Java、R 客户端，Python 客户端当时还在开发中。前端组件也在被做成可复用的 JavaScript 库：树视图、图视图、自动补全框都可以嵌到自己的网站里。

讲者在 Q&A 里补充了实现细节：OLS 底层用 **Neo4j** 存图，界面里的查询用 **Cypher** 写；当时不公开 Neo4j 数据库，但计划把索引放到 FTP 上，方便别人下载后自己跑查询。这也解释了为什么 OLS 能把“术语 + 关系”查得这么快。

## 七、ZOOMA 与下一步：从“查术语”到“批量注释”

OLS 解决的是“我知道一个词，帮我找到对应术语”。但很多时候，手里是一整批自由文本，需要批量映射。这就是 **ZOOMA** 的场景。

在 ZOOMA 里粘贴一批词，点击 annotate，它会返回最可能的 ontology mapping，并给出置信度。置信度来自 EBI 已经人工策展过的数据：某些词以前被映射到哪个术语，系统可以学习这些映射，再用于新数据。ZOOMA 正在被整合进 OLS，未来可以在 OLS 里直接做自动注释 [【跳转到 16:07】](https://www.youtube.com/watch?v=p8XF7yJvW4E&t=967)。

![ZOOMA 把一段自由文本批量映射到本体术语，并给出置信度](assets/Ontology%20Lookup%20Service%20%28OLS%29/00967.webp)

讲者还提到两个后续方向 [【跳转到 18:48】](https://www.youtube.com/watch?v=p8XF7yJvW4E&t=1128)：

- **本体映射服务**：疾病本体之间有很多交叉引用，未来提供一个统一入口，查一个术语在所有相关本体里的对应项；底层会用 identifiers.org 作为规范 URI 基础。
- **文本注释**：NCBO Annotator 可以把论文里的词映射到本体术语；Europe PMC 已经在用 OLS 的术语词典做文本挖掘，并采用 W3C 的 Open Annotation 模型标注文本片段。

Q&A 里还有几个实用细节：

- ZOOMA 可以本地部署，代码在 GitHub；
- OLS 底层用 Solr 做搜索，很多 Solr 查询语法其实可用，但当时没有正式文档；
- OLS 不会随意修改来源本体，OBO Foundry 的本体默认已经过一轮检查；对其他来源的本体会做推理、分类和常见谓词规范化；
- 当时不提供“查询推理后的等价术语”的服务，等价/映射更多依赖交叉引用和人工策展；
- 图视图按钮就在术语页上，只是讲者觉得可以做得更显眼。

## 小结

- **本体不是词典，而是带 ID、带关系、带元数据的知识结构**；它让不同数据库能用同一个 ID 描述同一个概念。
- **OLS 是 150+ 生物医学本体的统一入口**，核心能力是搜索、树/图浏览、版本历史和 REST API。
- **搜索时先判断自己知不知道目标本体**：知道就用 jump to，不知道就用泛搜，并把“跨本体出现”当作术语质量的参考信号。
- **术语页要同时看定义、同义词、树和交叉引用**；树里的 `part_of`、`develops_from` 往往比文字定义更能说明问题。
- **本体是活的**：版本历史能告诉你术语何时新增、删除或废弃，依赖本体做注释的系统必须关注这些变化。
- **API 是 OLS 的主要使用方式**；网页上的 JSON 按钮和开发者文档是理解 API 的捷径。
- **ZOOMA 把“查一个术语”扩展到“批量注释一段文本”**，是从检索走向数据整合的下一步。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| ontology（本体） | 用唯一 ID、关系和元数据描述某个领域概念的规范化知识结构 |
| term（术语） | 本体里的一个概念节点，例如 liver、dichromatopsia |
| accession / ID | 术语的稳定标识符，例如 Uberon 里的 liver ID |
| synonym（同义词） | 指向同一概念的其他叫法，例如 color blindness 是 dichromatopsia 的同义词 |
| `is_a` | “是一种”的父子关系，例如 dichromatopsia `is_a` 色觉异常 |
| `part_of` | “是……的一部分”的部分-整体关系，例如 liver `part_of` exocrine system |
| xref（交叉引用） | 指向其他数据库或本体的等价/相关记录 |
| OBO Foundry | 生命科学本体的社区与规范集合，OLS 的主要数据来源 |
| OLS | Ontology Lookup Service，本视频的主角，统一检索生物医学本体 |
| ZOOMA | 把自由文本批量映射到本体术语的注释服务 |
| REST API | 通过 HTTP 访问本体、术语和关系的程序接口 |
