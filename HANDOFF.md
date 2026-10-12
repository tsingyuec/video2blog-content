# HANDOFF

本文件记录**一件事**：本次对话中确定、但**尚未执行**的内容重组任务，以及相关背景，供后续接手。

---

## 一、待执行任务：content 内容重组

把生物相关内容按「模型 / 数据站点 / 公共知识」重新归类。**尚未动手**。

### 目标结构

1. `protein_group/protein_design` 和 `protein_group/alphafold` 的内容 → 移到 `biomodel/` 下，**按具体模型**分子目录；
2. 子目录里**不要** `README.md`、**不要** `blog/`，博客文件**直接放在**子目录里；
3. 现有 `biomodel/highfold` 也**拉平**成同样的结构；
4. `biodata` 也**分层**：像 `biomodel` 一样按**不同数据站点**分子目录；
5. **新建 `content/biobasic/`**，放「公共生物学」博客（不涉及具体模型/数据站点）。

### 已确认的映射表

**`biomodel/`（模型）**

| 目标子目录 | 来源博客 | 篇数 |
| --- | --- | --- |
| `biomodel/alphafold/` | `alphafold/blog/` 全部 9 篇 **＋** `protein_design/blog/` 的 3 篇：`AlphaFold3官方文档讲解01_输入设置_序列定义与整体结构`、`AlphaFold3官方文档讲解02_输入设置_MSA模板共价键与CCD`、`AlphaFold的原理和展望` | 12 |
| `biomodel/proteinmpnn/` | `MPNN：用机器学习做蛋白质序列设计`、`ProteinMPNN论文精读_稳健的深度学习蛋白质序列设计`、`用ProteinMPNN进行逆折叠` | 3 |
| `biomodel/rfdiffusion/` | `Baker实验室官方教程：用RFDiffusion3设计蛋白质Binder`、`RFDiffusion：结合结构预测与扩散生成模型的精准蛋白质设计`、`RFdiffusion：从图像生成到蛋白质结构设计` | 3 |
| `biomodel/rosettafold/` | `RoseTTAFold All-Atom 论文精读（Molecular ML Reading Group）` | 1 |
| `biomodel/protein_design/` | 通识/课程类：`第01讲_AI+蛋白质设计基础`、`第02讲_实践操作_RosettaScripts与ProteinMPNN`、`DNA与RNA数据如何输入机器学习模型`（用户指定放这里） | 3 |
| `biomodel/highfold/` | `biomodel/highfold/blog/` 的 2 篇（拉平：删 `README.md`、去 `blog/`） | 2 |

**`biodata/`（数据站点）**

| 目标子目录 | 来源博客 | 篇数 |
| --- | --- | --- |
| `biodata/string/` | `STRING数据库的介绍和使用`、`STRING简介-蛋白网络的证据来源与整合`、`蛋白质互作网络构建` | 3 |
| `biodata/uniprot/` | `UniParc与UniRef数据库使用指南`、`UniRef数据库详解（UniProtKB vs UniRef vs UniParc）` | 2 |

**`biobasic/`（新建，公共生物学）**

- `什么是蛋白质-蛋白质相互作用`
- `蛋白质互作研究技术`
- `酵母双杂交实验入门与结果解读`
- `酵母双杂交技术（高中生物二轮复习）`

### 关键实现要点（务必注意）

- **配图是相对路径**：博客里图片写的是 `assets/<名称>/xxx.webp`，与对应 `.md` **同处一层**。把 `.md` 和它的 `assets/<名称>/` 目录**一起搬走、保持相对位置**即可，**无需改任何链接**。
- **assets 目录名未必等于文件名**：例如 `UniParc与UniRef数据库使用指南.md` 对应的 assets 目录名是 `UniParc与UniRef使用指南`（少了「数据库」）。搬移时应以 **md 里实际引用的 `assets/<name>`** 去定位 assets 目录，不要用文件名去猜。
- **`transcripts/` 目录未被 git 跟踪**（本地中间产物，站点已排除）：可一并迁移以保持整洁，也可留着或删除，不影响站点与仓库。
- **必须同步改构建脚本**：`scripts/build_site.py` 的 `is_included()` 目前**只收录** `README.md` 与 `/blog/` 下的文件。新结构是 `biomodel/<模型>/*.md`、`biodata/<站点>/*.md`、`biobasic/*.md`，**都不在其内**——不改这个函数，这些博客**不会出现在站点上**。
- **导航**由 `scripts/build_site.py` 按**真实目录树**自动生成到 `build/nav.yml`，`mkdocs.yml` 用 `INHERIT: build/nav.yml` 合并。改完目录结构无需手改 nav。

### 需要一并更新的索引页（README）

- 根 `README.md`「系列索引」表：`protein_design`、`alphafold` 两行改指向 `biomodel/` 下的新路径。
- `content/protein_group/README.md`：移除 `protein_design`、`alphafold` 两行。
- `content/biomodel/README.md`：改为列出各模型子目录（alphafold/proteinmpnn/rfdiffusion/rosettafold/protein_design/highfold）。
- `content/biodata/README.md`：改为列出各数据站点子目录（string/uniprot）。
- 新建 `content/biobasic/README.md`（公共生物学索引）。

---

## 二、本轮对话之前已完成的成果（背景）

网站已搭好并上线，与上面的重组相互独立：

- **站点**：https://tsingyuec.github.io/video2blog-content/ （仓库 `tsingyuec/video2blog-content`，`main` 分支）
- **技术**：MkDocs **Material**；每次 push 到 `main` → GitHub Actions 自动构建并发布 Pages。
- **自动化**：`.github/workflows/deploy-pages.yml`（build → configure-pages → upload → deploy）。
- **构建**：先 `python scripts/build_site.py` 生成 `build/docs` 与 `build/nav.yml`，再 `mkdocs build`；本地预览：`python scripts/build_site.py && python -m mkdocs serve`。
- **站点体积**：约 310 MB（已排除 `transcripts/`、`code/`，二者合计约 1.4 GB，会超 Pages 1 GB 限额）。
- **主题**：复刻本机 Typora 的 **newsprint**——衬线 PT Serif（已打包 woff2，西文用 PT Serif、中文回退系统宋体）+ 米色背景 `#f3f2ee` + 文字 `#1f0909` + 链接 `#065588` + `#dadada` 代码底 + 斜体灰引用块（5px 左边框）。深色为按同色系派生的版本。
- **布局**：桌面端两栏——左目录树 / 右正文；左栏顶部有「文件 / 大纲」切换（大纲由 `scripts/extra.js` 从右侧 TOC 克隆）。
- **重要约束**：**顶栏必须保留**——MkDocs Material 的搜索弹层与深浅色控件都内建在顶栏里，`display:none` 顶栏会让这两个按钮失效。当前顶栏为极简 newsprint 风格细栏。
- **正文规格**：字号 16px、栏宽 640px（≥1400px 时 914px）、行距 1.6。

### 相关文件

| 文件 | 作用 |
| --- | --- |
| `mkdocs.yml` | 站点配置；`INHERIT: build/nav.yml`；`custom_dir` 无；`extra_css/_javascript` 指向 `_static/*` |
| `scripts/build_site.py` | 装配 `content/` → `build/docs`；重写链接；按真实目录树生成 `build/nav.yml`；拷贝 `extra.css/js` 与字体 |
| `scripts/extra.css` | newsprint 复刻样式（字体/配色/排版/双栏） |
| `scripts/extra.js` | 左栏「文件 / 大纲」工具条 |
| `scripts/fonts/*.woff2` | PT Serif（来自 Typora newsprint） |
| `requirements.txt` | `mkdocs-material` |

### 曾遇到的坑（供参考）

- GitHub 账号一度因 **billing issue 锁定**，Actions 无法启动（报 "account is locked due to a billing issue"）；后恢复正常，可正常部署。
- Material 1.6 会校验全部内部链接：页面链接应保留 `.md` 交给 MkDocs 转换，**不要**自行改写成 `.html`（否则告警）。图片相对链接保持与源文件同目录即可。
- 全库仅 2 处**源码本身缺失**的配图（`aiinfra/blog/第06讲_.../00114.webp`、`00148.webp`），属既有问题。

---

## 三、用户在本轮对话中明确表达的偏好

- 顶层标签导航（OI Wiki 风）→ 后改为 **Typora 风：左树右文**。
- 侧栏要**按 `/content` 真实目录结构**展示（原始目录名/文件名，保留 `blog` 层级，**不显示图片目录**）。
- 侧栏选中项**不要灰底**；文件树里**不要内嵌大纲**。
- 字体/背景/间距**照 Typora 的 newsprint**；正文 16px（此前误用 20px 偏大）。
- 顶栏搜索/深浅色按钮**必须可用**（因此顶栏不能隐藏）。
- 本次重组：**按具体模型细分**、**highfold 也拉平**、**通识/课程 3 篇放 `biomodel/protein_design/`**、**不建 `biomodel/base`**、**另建 `biobasic` 放公共博客**、**`biodata` 按数据站点分层**。

> 注：以上映射中的「数据站点 vs 公共」划分（尤其 `蛋白质互作网络构建` 归 `biodata/string`、其余 PPI/Y2H 归 `biobasic`）为我依据 `biodata/README.md` 的说明所作判断，执行前可让用户再过目一次。
