# 系列：生物数据资源与分析（biodata）

- **平台**：Bilibili
- **来源**：BV1hA411V7UX、BV1fLZ1YkEwU、BV1dM41187Gy、BV1ZjmPYeEVz
- **视频数**：4
- **主题**：本目录收录「生物数据资源与分析」相关的视频整理博客。当前三篇围绕蛋白质互作：第一篇系统介绍 **STRING 数据库**的定位、数据下载、单 / 多蛋白检索、PPI 网络的节点 / 证据视图 / 图例颜色、Settings 筛选、GO/KEGG/Reactome/UniProt/Pfam 功能富集、聚类与导出，并介绍「差异基因」新功能；第二篇是**蛋白质互作（PPI）网络构建**的实操，讲清「单个 / 多个基因」×「按名称 id / 按序列」四种入口、非模式物种的映射、Settings 调参（置信度、shell）以及 SVG/PNG/TSV 导出并接入 Cytoscape；第三篇《什么是蛋白质-蛋白质相互作用》讲清二元交互概念与 PPI 的核心逻辑（由已知推未知），并以酵母双杂交为例；第四篇《蛋白质互作研究技术》按「研究对象 × 体内/体外」系统梳理六大技术的原理与用途——酵母单杂交（Y1H）与 EMSA（蛋白-DNA），酵母双杂交（Y2H）与双分子荧光互补（BiFC，体内蛋白-蛋白），免疫共沉淀（Co-IP）与 pull-down（体外蛋白-蛋白）。

## 视频索引

| 视频键 | 标题 | 时长 | 博客 | 配图 | 原视频 |
| --- | --- | ---: | --- | ---: | --- |
| BV1hA411V7UX | 【string数据库】【生物信息学】STRING数据库的介绍和使用 | 15:10 | [博客](blog/STRING数据库的介绍和使用.md) | 14 | [B站](https://www.bilibili.com/video/BV1hA411V7UX/) |
| BV1fLZ1YkEwU | 蛋白质互作网络构建 | 10:56 | [博客](blog/蛋白质互作网络构建.md) | 8 | [B站](https://www.bilibili.com/video/BV1fLZ1YkEwU/) |
| BV1dM41187Gy | 什么是蛋白—蛋白相互作用？lncRNA/miRNA/cicRNA，医学热点知识 | 9:01 | [博客](blog/什么是蛋白质-蛋白质相互作用.md) | 3 | [B站](https://www.bilibili.com/video/BV1dM41187Gy/) |
| BV1ZjmPYeEVz | 生化分子复盘（十）：DNA与蛋白质以及蛋白质与蛋白质互作研究技术 | 35:55 | [博客](blog/蛋白质互作研究技术.md) | 7 | [B站](https://www.bilibili.com/video/BV1ZjmPYeEVz/) |

## 博客结构速览

**STRING 数据库的介绍和使用——从蛋白互作网络到功能富集分析**

- 一、STRING 是什么：一站式蛋白互作与功能富集数据库（四类数据来源、核心功能、加权整合与可靠指数、版本与收录规模）
- 二、数据怎么拿：Download（整库 / 物种子集 / 原始文件 / SQL）与 My Data（上传自己的实验数据）
- 三、检索蛋白互作：单蛋白（输出全部互作）与多蛋白 / 序列（只输出输入蛋白之间）的区别
- 四、读懂网络里的节点与证据（点击节点看信息与 PDB / SWISS-MODEL 结构，点击连线看证据）
- 五、证据视图：experiments / databases / textmining / cooccurrence / coexpression / neighborhood / fusion
- 六、读懂图例（Legend）：节点颜色与内容、八类边颜色、连线粗细的含义
- 七、自定义网络：Settings（证据集合、evidence / confidence、来源勾选、最低得分与显示数量）
- 八、功能富集分析：GO / KEGG / Reactome / UniProt / Pfam
- 九、导出与聚类：把结果带走（PNG / SVG / TSV，按综合得分聚类）
- 十、多蛋白查询与新功能：差异基因（悬停 GO id 高亮通路）

**蛋白质互作网络构建——从单个基因到多基因、再到可发表的图**

- 一、STRING 是构建 PPI 网络最常用的数据来源（收录范围、数据来源）
- 二、先理清四种构建方式：单个 / 多个基因 × 按名称 id / 按序列
- 三、单个基因的 PPI 网络（三步输入 + 示例 TP53 + Continue）
- 四、多个基因（按名称 / id）的 PPI 网络（Multiple proteins，示例拟南芥 PP2C 家族）
- 五、多个基因（按序列）与非模式物种映射（Multiple sequences + mapping 比对率）
- 六、读懂网络：节点与连线（Legend）
- 七、调参：Settings（数据来源、置信度 0.4、shell 添加 10）
- 八、让图更干净并导出（显示选项、SVG / PNG / TSV、接入 Cytoscape）

**什么是蛋白质-蛋白质相互作用——二元交互与核心研究逻辑（解螺旋）**

- 一、二元交互：两个分子之间的直接结合（元素可以是蛋白/mRNA/lncRNA/miRNA/circRNA/DNA；最常见的是蛋白-蛋白、蛋白-RNA）
- 二、PPI 的核心研究逻辑：由已知（蛋白 A）推未知（蛋白 B），并证明二者结合
- 三、研究技术示例：酵母双杂交（GAL4 的 BD/AD 拆分；筛选 + 验证）

**蛋白质互作研究技术——从酵母单杂、EMSA 到酵母双杂、BiFC、Co-IP、pull-down（lyrical79）**

- 一、总览：六大技术按「研究对象 × 体内/体外」分组
- 二、酵母单杂交（Y1H）：研究蛋白-DNA（分离结合特定 DNA 的蛋白、鉴定 DNA 结合域）
- 三、凝胶阻滞（EMSA）：研究蛋白-DNA（结合后迁移变慢）
- 四、酵母双杂交（Y2H）：体内研究蛋白-蛋白（X-BD 与 Y-AD 组成完整转录因子）
- 五、双分子荧光互补（BiFC）：体内研究蛋白-蛋白（荧光蛋白切两半、重组发光）
- 六、免疫共沉淀（Co-IP）：体外研究蛋白-蛋白（抗体捕获靶蛋白及其互作蛋白）
- 七、pull-down（GST）：体外研究蛋白-蛋白（GST-X 作诱饵挂柱「钓」Y）

## 核心知识点速览

- **STRING 数据库**：检索已知 / 预测的蛋白-蛋白质相互作用，数据来自实验、文本挖掘、其他数据库与生物信息学预测，可与 Cytoscape 联用；所有互作加权整合并给出可靠指数（score），录制时约 5,090 物种、2,458 万蛋白、31 亿互作；检索规则：单蛋白 → 输出该蛋白的全部互作，多蛋白 / 序列 → 只输出输入蛋白之间的互作；节点=蛋白（红=查询蛋白及第一层、白=第二层），点击节点看信息与 PDB / SWISS-MODEL 结构，点击连线看证据；边颜色=证据类型（蓝=策展数据库、粉红=实验、绿=基因邻域、红=基因融合、深蓝=基因共现、黄=文本挖掘、黑=共表达、浅蓝=同源性），粗细=相互作用强度；Settings 可按 evidence / confidence 与来源、最低得分、显示数量筛选；Analysis 提供 GO / KEGG 富集并链接 Reactome、UniProt、Pfam、SMART；Exports 支持 PNG / 高分辨率 PNG / SVG / TSV（含 node1、node2、accession、annotation、综合得分）；Clusters 聚类后同簇同色、簇间虚线；多蛋白支持列表或文件上传，新增「差异基因」功能可悬停 GO id 在网络上高亮通路。
- **PPI 网络构建**：STRING 覆盖 5,090 种生物、两千四百多万种蛋白，互作来自实验与预测；四种入口 = 单个 / 多个基因 × 按名称 id / 按序列（Protein by name、Protein by sequence、Multiple proteins、Multiple sequences）；通用规则——先选物种，物种未被收录就选相近种或模式生物，id 认不出就改用序列；匹配到多个候选时用 Continue 确认；非模式物种按序列检索需做 mapping，按比对率选最高；Settings 可设数据来源、置信度（常用 0.4）、给输入蛋白加一层 shell（如添加 10 个）；可隐藏 3D 结构与孤立节点、显示 / 隐藏名称；导出 SVG / 高像素 PNG / TSV（可导入 Cytoscape）/ 蛋白注释文件。
- **什么是 PPI（解螺旋）**：二元交互=任意两个分子之间的直接结合，最常见的是蛋白-蛋白与蛋白-RNA；「交互」指直接结合，区别于间接的二元/三元变量研究；PPI 核心逻辑=由已知蛋白 A 找未知蛋白 B 并证明结合；以酵母双杂交为例（GAL4 拆成 BD/AD，X-BD 与 Y-AD 结合后组成完整转录因子激活报告基因，既可筛选 cDNA 文库又可验证）。
- **蛋白质互作研究技术（lyrical79）**：按研究对象与体内/体外分组——蛋白-DNA（酵母单杂 Y1H：启动子上游插已知顺势作用元件、下游报告基因，cDNA-AD 融合，用于分离结合特定 DNA 的蛋白、鉴定 DNA 结合域；EMSA：DNA-蛋白结合后分子量增大、迁移变慢）；体内蛋白-蛋白（Y2H：X-BD 与 Y-AD 互作后激活报告基因；BiFC：荧光蛋白切两半、互作时重组发光）；体外蛋白-蛋白（Co-IP：固体基质+抗体捕获靶蛋白 X，互作的 Y 被一起沉淀；pull-down：GST-X 作诱饵挂在 GSH 柱上「钓」出 Y）；易错点——酵母单杂与 EMSA 研究的是蛋白-DNA，不是 PPI。
