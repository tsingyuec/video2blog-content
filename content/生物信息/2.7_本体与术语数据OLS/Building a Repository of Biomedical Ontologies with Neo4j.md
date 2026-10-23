# OLS 用 Neo4j 属性图替代 RDF，以有损转换换取可查询性

> 视频：[Building a Repository of Biomedical Ontologies with Neo4j](https://www.youtube.com/watch?v=jZND2WYT4GE)（Neo4j，15:25，2016）

## 本讲要解决的核心问题（SCQA）

**背景**：OLS 要统一访问 140 多个生物医学本体、约 450 万个概念、1100 万条关系；用户大多数时候不是点网页，而是通过 REST API 批量访问。

**冲突**：本体的标准表示是 OWL/RDF，但 RDF 三元组库对 OWL 语义的支持并不完整；SPARQL 学习曲线陡，而且和 Spring 这类 Web 框架配合得不好。直接用 RDF 做 OLS 的后端，开发和维护都很别扭。

**疑问**：有没有一种后端，既能把本体当“图”来查，又能快速、自动地暴露 REST API？

**回答（中心思想）**：OLS 把 OWL **有损转换**成 Neo4j 属性图，用 Solr 做全文索引，用 Spring Data REST 自动生成超媒体 API；索引每晚重建，再分发到多个数据中心。这样既保留了“术语 + 关系”的图结构，又拿到了成熟的 Web 开发栈。

![用色盲例子说明术语不统一导致检索结果差异](assets/Building%20a%20Repository%20of%20Biomedical%20Ontologies%20with%20Neo4j/00135.webp)

## 一、问题起点：生物数据互联，先要统一“说的是什么”

EBI 的数据库彼此高度关联：同一个蛋白可能出现在多个数据库里，同一个基因、同一条通路也可能有多个名字。要整合这些数据，第一步是知道“这个数据到底是什么类型”——是基因、蛋白，还是通路。

本体就是做这件事的：它用受控词表（controlled vocabulary）给概念分配唯一 ID，再用关系把它们组织起来。讲者仍然用色盲举例 [【跳转到 02:15】](https://www.youtube.com/watch?v=jZND2WYT4GE&t=135)：

- 搜 `color blindness`：647 条结果；
- 搜 `dichromatopsia`：270 条结果；
- 搜更泛的 `abnormality of the eye`：0 条结果。

普通搜索引擎不理解“色盲是眼部异常的一种”，所以不会自动扩展查询。本体则可以把这层关系显式写出来。

![生物医学本体覆盖从基因型到表型的完整谱系](assets/Building%20a%20Repository%20of%20Biomedical%20Ontologies%20with%20Neo4j/00197.webp)

构建本体的两步是：

1. **Accessioning**：给领域里的术语分配 ID；
2. **建立关系**：例如 dichromatopsia `is_a` 色觉异常，dichromatopsia 的病变位置在 eye（来自解剖学本体）。

此外还要补充元数据：同义词（color blindness）、文本定义等。这样，一个术语就同时有了“身份证”“位置”和“解释”。

## 二、OLS 新版：140 个本体、450 万概念、1100 万关系

讲者介绍的是 OLS 的一次重写 [【跳转到 03:42】](https://www.youtube.com/watch?v=jZND2WYT4GE&t=222)。新版当时处于 beta，规模是：

- **140 个**生物医学本体；
- 约 **450 万个**生物概念；
- 约 **1100 万条**概念之间的关系。

访问方式有三层 [【跳转到 04:07】](https://www.youtube.com/watch?v=jZND2WYT4GE&t=247)：

- **Solr**：负责文本搜索的索引；
- **Neo4j**：负责术语之间的连接关系；
- **Spring Data**：负责构建 REST API。

讲者强调，大多数用户真正需要的是 **REST API**，而不是网页。因此 OLS 把“程序化访问”当成一等公民；整个项目开源，代码可以按组件复用。

![OLS 新版：140 个本体、450 万概念、1100 万关系](assets/Building%20a%20Repository%20of%20Biomedical%20Ontologies%20with%20Neo4j/00222.webp)

![OLS 的技术栈：Solr 做文本索引，Neo4j 存图，Spring Data 生成 REST API](assets/Building%20a%20Repository%20of%20Biomedical%20Ontologies%20with%20Neo4j/00247.webp)

## 三、为什么不用 RDF / SPARQL？

本体的标准表示是 **OWL**（Web Ontology Language），它是 W3C 标准。OWL 里有三类核心对象：

- **class**（类）：概念，例如 heart；
- **property**（属性/关系）：例如 part_of；
- **individual**（个体）：类的实例。

OWL 还可以把本体序列化成 RDF 图，所以看起来“图数据库应该很合适”。但讲者团队实际评估后 [【跳转到 06:29】](https://www.youtube.com/watch?v=jZND2WYT4GE&t=389)，发现了两个问题：

1. **RDF 三元组库对 OWL 语义的支持不完整**：OWL 的表达能力很强，但现有三元组库很难完整利用这些语义；
2. **SPARQL 与 Web 框架的配合不好**：SPARQL 本身有学习成本，而当时主流的 Web 开发框架（如 Spring）对语义 Web 技术的支持很弱。

换句话说，直接用 RDF/SPARQL 做应用后端，理论上“纯”，工程上“难”。

![OWL 是 W3C 标准，但多数使用场景只关心术语和关系](assets/Building%20a%20Repository%20of%20Biomedical%20Ontologies%20with%20Neo4j/00314.webp)

![RDF 三元组库对 OWL 语义支持不完整，SPARQL 与 Web 框架配合也弱](assets/Building%20a%20Repository%20of%20Biomedical%20Ontologies%20with%20Neo4j/00389.webp)

## 四、OWL → Neo4j：一次“有损但够用”的转换

于是团队做了一个 Neo4j 试点 [【跳转到 06:54】](https://www.youtube.com/watch?v=jZND2WYT4GE&t=414)：能不能把 OWL 简化成属性图，覆盖大多数使用场景？答案是够用。

转换规则大致如下 [【跳转到 07:26】](https://www.youtube.com/watch?v=jZND2WYT4GE&t=446)：

- 把 OWL 里的 **class、property、individual** 三类对象都建成节点；
- 给节点打标签，标明它是哪一类，以及它来自哪个本体；
- **每个本体一个索引**，方便按本体过滤；
- 把 OWL 的 annotation properties（label、description、comment 等元数据）直接存成节点的属性；
- 只保留 OWL 关系的一个子集，并把复杂公理“压平”成直接关系。

最后一条是关键 [【跳转到 08:11】](https://www.youtube.com/watch?v=jZND2WYT4GE&t=491)。OWL 里“heart 是 cardiovascular system 的一部分”可能写成一条复杂的类表达式，并不是两个类之间的直接边。OLS 把它简化成：

```text
heart -[:part_of]-> cardiovascular system
```

这是一次**有损转换**：丢掉了一部分严格的逻辑语义，但保留了用户最常查的“术语—关系”结构。讲者说，具体支持 OWL 的哪些部分，项目文档里有说明。

![把 OWL 有损转换成 Neo4j：class/property/individual 三类节点](assets/Building%20a%20Repository%20of%20Biomedical%20Ontologies%20with%20Neo4j/00446.webp)

![OWL 的复杂公理被压平成直接关系：heart part_of cardiovascular system](assets/Building%20a%20Repository%20of%20Biomedical%20Ontologies%20with%20Neo4j/00491.webp)

## 五、Cypher：把本体结构变成可查询的图

有了属性图，就可以用 **Cypher** 查询 [【跳转到 08:41】](https://www.youtube.com/watch?v=jZND2WYT4GE&t=521)。讲者给了几个典型例子：

- **色盲的传递子类**：Human Phenotype Ontology（HPO）里有 color blindness 的 ID，从它出发取所有传递子类，就能得到一棵子图；
- **眼的部件与相关疾病**：先从 Uberon 找“eye 的 part_of 部件”，再找“病变位置在 eye 的疾病”，两条路径一拼，就能回答“哪些眼的部件和疾病相关”；
- **共同祖先 / 最短路径**：例如找共同分类学上的“超科”，这类查询在 Neo4j 里很自然；
- **心脏的 partonomy**：查 heart 的部分-整体结构，用来生成可视化。

这些查询直接驱动了 OLS 的树视图和图视图。讲者特别提到，**共同祖先、最短路径**这类查询在 Neo4j 里“开箱即用”，而他们最初评估的一些 RDF 数据库并不能直接支持。

![Cypher 查询示例：色盲的传递子类、眼的部件与相关疾病](assets/Building%20a%20Repository%20of%20Biomedical%20Ontologies%20with%20Neo4j/00521.webp)

## 六、REST API：Spring Data REST 的“超媒体 + 可爬取”

OLS 的 API 不是手写一堆 Controller [【跳转到 10:50】](https://www.youtube.com/watch?v=jZND2WYT4GE&t=650)，而是用 **Spring Data REST** 把数据仓库直接暴露成 REST 接口。效果是：

- 可以从“本体列表”导航到“某个本体”；
- 再导航到“某个术语”；
- 再拿到该术语的所有关系；
- 整个 API 是**可爬取**的（fully crawlable）。

这正好符合 OLS 的用户需求：很多人不是来浏览网页，而是写脚本把整个本体或一批术语抓下来做注释。讲者说，beta 阶段大约有 2000 个活跃用户，很多流量都来自 API。

![Spring Data REST 生成可爬取、超媒体驱动的 API](assets/Building%20a%20Repository%20of%20Biomedical%20Ontologies%20with%20Neo4j/00650.webp)

## 七、索引构建与部署：每晚 4 小时重建

OLS 的数据不是静态的 [【跳转到 11:15】](https://www.youtube.com/watch?v=jZND2WYT4GE&t=675)。团队每晚检查约 140 个外部本体，只要有文件变化就重建索引：

1. 维护一个 **master Neo4j index**；
2. 发现某个本体变化，就把该本体从索引里移除；
3. 用 **batch inserter** 重新加载；
4. 全量重建时间**不到 4 小时**。

batch inserter 的速度很快，但它**不是事务安全的**：如果中途失败，索引可能损坏。团队接受这个风险，因为每晚都能重建；讲者也向现场的 Neo4j 专家请教有没有更好的优化方式。

索引构建完成后，会被推送到多个数据中心，并在几台机器之间做负载均衡。这样 API 的扩展性就不依赖单机。

![每晚检查 140 个本体，变化的本体整体重载，全量重建不到 4 小时](assets/Building%20a%20Repository%20of%20Biomedical%20Ontologies%20with%20Neo4j/00675.webp)

## 八、成果、边界与 Q&A

讲者总结这套架构的几个优点 [【跳转到 11:53】](https://www.youtube.com/watch?v=jZND2WYT4GE&t=713)：

- **可扩展**：离线建索引，多机房分发；
- **统一访问**：140 多个本体放在同一个查询入口；
- **通用**：不绑定生命科学，任何 OWL 本体都可以用这套代码建 Neo4j 索引；
- **开发效率高**：Neo4j + Spring Data 只需很少代码就能得到强大的 REST API；
- **有实际采用**：beta 阶段约 2000 用户，一些药企也希望直接用这套方案解决“本体太多、太难整合”的问题。

![结论：统一访问、可扩展、通用（任何 OWL 本体）](assets/Building%20a%20Repository%20of%20Biomedical%20Ontologies%20with%20Neo4j/00713.webp)

Q&A 里有一个很重要的问题 [【跳转到 13:49】](https://www.youtube.com/watch?v=jZND2WYT4GE&t=829)：**OLS 会不会自动合并不同本体里的相同概念？**

讲者的回答是：不会。OLS 只是把本体放在一起、提供统一查询；他们做的最多是“谓词规范化”（例如不同本体用不同的属性名描述同一种元数据），但**不做自动的术语等价判断或本体合并**。跨本体的映射主要靠人工策展，这也是团队下一步的项目。

这说明 OLS 的定位是“统一访问层”，不是“本体融合器”。它让你能在一个地方查到所有本体，但“这两个术语是不是同一个概念”仍然需要领域专家判断。

## 小结

- **OLS 的核心矛盾**：本体天然是图，但 RDF/SPARQL 的工程体验不够好；团队选择把 OWL 有损转换成 Neo4j 属性图。
- **三类节点**：class、property、individual；按本体打标签、建索引；annotation 变成节点属性。
- **关系被压平**：`heart subClassOf part_of some cardiovascular system` 变成 `heart -part_of-> cardiovascular system`，牺牲部分逻辑精度，换取可查询性。
- **Cypher 擅长传递闭包、最短路径、共同祖先**，这些查询直接驱动 OLS 的树和图可视化。
- **Spring Data REST** 让 API 自动具备超媒体导航和可爬取性，符合批量注释用户的需求。
- **每晚重建 + 多机房分发**解决了本体频繁更新和 API 扩展性问题；代价是 batch inserter 非事务安全。
- **OLS 不做本体合并**：它统一访问，不做自动等价推理；跨本体映射仍靠人工策展。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| OWL | W3C 的本体表示语言，包含 class、property、individual |
| RDF | 用“主语-谓语-宾语”三元组表示数据；OWL 可以序列化成 RDF |
| SPARQL | 查询 RDF 三元组的语言，类似关系数据库里的 SQL |
| Neo4j | 属性图数据库，用节点、关系、属性存储数据 |
| Cypher | Neo4j 的图查询语言，擅长路径、传递闭包、最短路径 |
| Solr | 全文搜索引擎，OLS 用它做术语的文本检索 |
| Spring Data REST | 把数据仓库自动暴露成 REST API 的框架 |
| batch inserter | Neo4j 的批量导入工具，速度快但非事务安全 |
| 有损转换 | 只保留 OWL 的一部分语义，把复杂公理简化为直接关系 |
| hypermedia API | 响应里带导航链接，客户端可以顺着链接爬取 |
