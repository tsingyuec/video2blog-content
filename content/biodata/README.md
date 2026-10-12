# 分组：生物数据资源（biodata）

本分组按**数据站点 / 数据库**收录「生物数据资源与分析」相关的视频整理博客。

每个子目录对应一个数据站点，目录内**直接存放博客 `.md` 与配图 `assets/`**（不再有 `README.md` 与 `blog/`）；本页即为整个分组的统一索引。

- **平台**：Bilibili、YouTube
- **视频数**：5（另有 4 篇「公共生物学」博客已移至 [biobasic](../biobasic/README.md)）

## 站点索引

| 子目录 | 主题 | 篇数 |
| --- | --- | ---: |
| `string/` | STRING：蛋白互作网络与功能富集 | 3 |
| `uniprot/` | UniProt：UniProtKB / UniRef / UniParc | 2 |

## `string/` — STRING 蛋白互作数据库

STRING 是「由已知推未知」构建 PPI 网络最常用的数据来源。三篇分别覆盖：从零介绍 STRING 的定位、数据下载、单 / 多蛋白检索、网络节点与证据视图、图例、Settings 筛选、GO / KEGG / Reactome / UniProt / Pfam 功能富集、聚类与导出；实操《蛋白质互作网络构建》（单个 / 多个基因 × 按名称 id / 按序列、非模式物种映射、调参、SVG / PNG / TSV 导出并接入 Cytoscape）；以及 STRING 作者官方简介（七大证据来源、质量打分、校准到 KEGG 金标准、combined score 与同源转移）。

| 视频键 | 标题 | 时长 | 博客 | 配图 | 原视频 |
| --- | --- | ---: | --- | ---: | --- |
| BV1hA411V7UX | 【string数据库】【生物信息学】STRING数据库的介绍和使用 | 15:10 | [博客](string/STRING数据库的介绍和使用.md) | 14 | [B站](https://www.bilibili.com/video/BV1hA411V7UX/) |
| BV1fLZ1YkEwU | 蛋白质互作网络构建 | 10:56 | [博客](string/蛋白质互作网络构建.md) | 8 | [B站](https://www.bilibili.com/video/BV1fLZ1YkEwU/) |
| o208DwyFbNk | The STRING database: Brief introduction to protein networks and how they are made | 05:55 | [博客](string/STRING简介-蛋白网络的证据来源与整合.md) | 6 | [YouTube](https://www.youtube.com/watch?v=o208DwyFbNk) |

## `uniprot/` — UniProt 数据库

辨析 **UniProt 的三大数据库 UniProtKB / UniRef / UniParc** 的分工与用法：Swiss-Prot 与 TrEMBL、FASTA header 的 sp / tr 与 PE 等级、UniRef100 / 90 / 50 的聚类与 80% 覆盖规则、seed 与 representative 的区别、accession 命名，以及 BLAST 目标库与「相似蛋白」面板。另一篇（EMBL-EBI 官方 webinar）手把手讲**怎么用 UniParc 与 UniRef**：UniParc 的 UPI、交叉引用、版本与 active / inactive、下载格式、Proteins API 编程访问，UniRef 的三档聚类、网站检索与 Advanced Search，以及用 BLAST 检索 UniRef90 / 50 的覆盖对比。

| 视频键 | 标题 | 时长 | 博客 | 配图 | 原视频 |
| --- | --- | ---: | --- | ---: | --- |
| uXbwNHnhVoA | UniProt makeup - UniProtKB vs UniRef vs UniParc | 15:52 | [博客](uniprot/UniRef数据库详解（UniProtKB%20vs%20UniRef%20vs%20UniParc）.md) | 8 | [YouTube](https://www.youtube.com/watch?v=uXbwNHnhVoA) |
| wTdtuXXgjmM | Explore the known protein space through UniProt Archive and Clusters | 27:46 | [博客](uniprot/UniParc与UniRef数据库使用指南.md) | 12 | [YouTube](https://www.youtube.com/watch?v=wTdtuXXgjmM) |
