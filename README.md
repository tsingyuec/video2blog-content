# 视频知识库

把 Bilibili / YouTube 上分散的课程、讲座与源码剖析，整理成**有骨架、可检索、每一句都能回到原片**的知识库。

**视频是素材，知识体系是骨架。** 先为一个主题搭出知识目录，再为目录里的每个小节找 1–3 支讲得最透的视频；每支视频各写一篇初学者能读懂的博客，多支视频不合并。于是一个小节可以有多篇各自独立的博客，一支视频也可以只服务于它讲得最好的那个小节。

## 为什么以「小节」为单位

- **视频是线性的，知识是网状的。** 一支 60 分钟的讲座常横跨四五个知识点，按视频归档，等于让讲者的顺序决定读者的路径。
- **一个知识点可以由多支视频分别讲透。** 有人讲直觉，有人推公式，有人给源码；每支视频的博客独立成篇，读者按需要选读。
- **小节是进度、命名与验收的最小单位。** 目录里的一行就是一个小节，通常包含 1–3 篇各自独立的博客；读完哪一行、还缺哪一行，一目了然。

## 三个产物

| 产物 | 位置 | 作用 |
| --- | --- | --- |
| **知识目录** | `content/<领域>/<脉络>/README.md` | 章 → 节 → 小节；读什么、读到哪、还缺什么，都看这一份 |
| **博客** | `content/<领域>/<脉络>/X_Y_<章>/X.Y_<节>/X.Y.Z_<小节>/<标题>.md` | 每小节通常 1–3 篇，每支视频一篇（同一支视频接近 60 分钟可拆篇）；结论先行，公式、配图、时间戳齐全 |
| **配图** | 博客同目录的 `assets/<博客名>/` | 从视频代表帧里挑，图注说明它在解释什么 |

视频、抽帧、字幕与「图-字幕」图文稿等中间产物放在 `_work/`，不进版本库。

## 怎么读

- 从下面的[系列索引](#系列索引)进入；每个系列的 `README.md` 就是它的目录与进度页。
- 博客按小节与视频角度命名；同一小节下的多支视频各自成篇，不合并。
- 正文的每个关键结论都带 `【跳转到 MM:SS】` 链接，点开就回到原片的对应位置；配图也是原片画面，不是后配的示意图。
- 文章按金字塔结构组织：开头 SCQA 交代问题与结论，正文按知识逻辑分章，末尾有小结与术语速查。

## 怎么维护

维护由 Agent 完成，三条指令对应三种工作：

| 指令 | 作用 | 产物 |
| --- | --- | --- |
| `explore:<关键词>` | 双路探索：平台优先 + 体系优先，抓字幕精排 | 候选表；不写 `content/` |
| `catalog:<主题>` | 搭知识目录：章 / 节 / 小节 | `content/<领域>/<脉络>/README.md` |
| `build:<系列>` | 按目录逐小节成稿 | 博客、配图、进度与链接 |

`build` 的流水线：**每批两个小节**；每个小节派一个子智能体，自行探索、定选、逐支写作与自检；验收后回写进度。子智能体负责该小节的探索与写作，不改 README、不碰别的小节。

完整规则见 [AGENTS.md](AGENTS.md)；探索、下载、抽帧、字幕、文稿与写作规范见 [`video2blog`](https://github.com/tsingyuec/video2blog-skill) skill。

## 目录结构

```
_work/                          # 中间产物（体积大、可再生，不进版本库）
└─ <系列>/
   ├─ _explore/                 # 候选期的字幕与笔记（可清理）
   └─ X.Y.Z_<小节>/
      ├─ _selection.md         # 选题单
      └─ <视频ID>/             # 视频、抽帧、字幕、图文稿

content/                        # 最终产物：博客 + 配图 + 索引
├─ <系列>/
│  ├─ README.md                  # 知识目录（站点里即该系列的首页）
│  ├─ 1.1_<节名>/
│  │  ├─ 1.1.1_<小节名>/
│  │  │  ├─ <博客标题>.md
│  │  │  └─ assets/<博客标题>/
│  │  └─ …
│  └─ 2.1_<节名>/
└─ <分组目录>/<系列>/             # 可选，如 vllm_group/、protein_group/

scripts/check/                  # 内容公式检查（KaTeX + 构建产物 HTML）
site/                           # 站点构建：content/ -> build/docs -> build/site
vendor/katex/                   # KaTeX 发行包：站点构建与内容公式检查
```

目录规则只有一条：`README.md` 是所在目录的索引，博客与它的 `assets/` 同级。层级随主题而定，站点不要求固定的 `blog/` 层。

## 站点

`content/` 由 `site/build_site.py` 装配成 `build/docs`（重写文内链接、按目录树生成侧栏），再由 `mkdocs build` 输出静态站到 `build/site`；推送到 `main` 后由 GitHub Actions 自动发布。本地预览：

```bash
pip install -r requirements.txt
python site/build_site.py && mkdocs serve
```


## 脉络索引

### 生命科学 · 生命科学基础

| 脉络 | 规模 | 入口 |
| --- | --- | --- |
| B01 生命科学基础主干 | 51 小节 · DONE 50 / WAITING 1 / REUSE 0 | [README](content/生命科学/生命科学基础/B01_生命科学基础主干/README.md) |
| B02 基因组与基因调控基础 | 64 小节 · DONE 49 / WAITING 5 / REUSE 10 | [README](content/生命科学/生命科学基础/B02_基因组与基因调控基础/README.md) |
| B03 蛋白质结构与功能基础 | 50 小节 · DONE 13 / WAITING 29 / REUSE 8 | [README](content/生命科学/生命科学基础/B03_蛋白质结构与功能基础/README.md) |
| B04 细胞与组学测量基础 | 59 小节 · DONE 44 / WAITING 1 / REUSE 14 | [README](content/生命科学/生命科学基础/B04_细胞与组学测量基础/README.md) |
| B05 免疫与抗体生物学基础 | 56 小节 · DONE 13 / WAITING 32 / REUSE 11 | [README](content/生命科学/生命科学基础/B05_免疫与抗体生物学基础/README.md) |
| B06 化学生物学与药物发现基础 | 54 小节 · DONE 8 / WAITING 36 / REUSE 10 | [README](content/生命科学/生命科学基础/B06_化学生物学与药物发现基础/README.md) |

### 生命科学 · 生物数据

| 脉络 | 规模 | 入口 |
| --- | --- | --- |
| D01 基因组与遗传变异数据 | 31 小节 · DONE 1 / WAITING 20 / REUSE 10 | [README](content/生命科学/生物数据/D01_基因组与遗传变异数据/README.md) |
| D02 蛋白质序列家族与结构数据 | 31 小节 · DONE 5 / WAITING 12 / REUSE 14 | [README](content/生命科学/生物数据/D02_蛋白质序列家族与结构数据/README.md) |
| D03 单细胞图谱与扰动数据 | 40 小节 · DONE 11 / WAITING 11 / REUSE 18 | [README](content/生命科学/生物数据/D03_单细胞图谱与扰动数据/README.md) |
| D04 分子功能网络与通路数据 | 34 小节 · DONE 4 / WAITING 17 / REUSE 13 | [README](content/生命科学/生物数据/D04_分子功能网络与通路数据/README.md) |
| D05 生物医学本体与表型数据 | 28 小节 · DONE 2 / WAITING 19 / REUSE 7 | [README](content/生命科学/生物数据/D05_生物医学本体与表型数据/README.md) |
| D06 化学实体与活性数据 | 28 小节 · DONE 1 / WAITING 16 / REUSE 11 | [README](content/生命科学/生物数据/D06_化学实体与活性数据/README.md) |
| D07 抗体实验与公共参照数据 | 39 小节 · DONE 1 / WAITING 16 / REUSE 22 | [README](content/生命科学/生物数据/D07_抗体实验与公共参照数据/README.md) |

### 生命科学 · 生物建模

| 脉络 | 规模 | 入口 |
| --- | --- | --- |
| P01 生物分子结构预测 | 72 小节 · DONE 26 / WAITING 25 / REUSE 21 | [README](content/生命科学/生物建模/P01_生物分子结构预测/README.md) |
| P02 蛋白质生成与序列设计 | 55 小节 · DONE 22 / WAITING 14 / REUSE 19 | [README](content/生命科学/生物建模/P02_蛋白质生成与序列设计/README.md) |
| P03 抗体建模设计与可开发性 | 70 小节 · DONE 28 / WAITING 17 / REUSE 25 | [README](content/生命科学/生物建模/P03_抗体建模设计与可开发性/README.md) |
| P04 功能肽与环肽设计 | 47 小节 · DONE 13 / WAITING 13 / REUSE 21 | [README](content/生命科学/生物建模/P04_功能肽与环肽设计/README.md) |
| P05 结合位点与分子对接 | 52 小节 · DONE 13 / WAITING 22 / REUSE 17 | [README](content/生命科学/生物建模/P05_结合位点与分子对接/README.md) |
| P06 分子生成与优化 | 50 小节 · DONE 7 / WAITING 22 / REUSE 21 | [README](content/生命科学/生物建模/P06_分子生成与优化/README.md) |
| P07 核酸序列与结构建模 | 53 小节 · DONE 16 / WAITING 17 / REUSE 20 | [README](content/生命科学/生物建模/P07_核酸序列与结构建模/README.md) |
| P08 单细胞分析与基础模型 | 66 小节 · DONE 9 / WAITING 27 / REUSE 30 | [README](content/生命科学/生物建模/P08_单细胞分析与基础模型/README.md) |
| P09 细胞扰动响应预测 | 82 小节 · DONE 23 / WAITING 13 / REUSE 46 | [README](content/生命科学/生物建模/P09_细胞扰动响应预测/README.md) |
| P10 分子动力学与构象系综 | 55 小节 · DONE 12 / WAITING 26 / REUSE 17 | [README](content/生命科学/生物建模/P10_分子动力学与构象系综/README.md) |

### 深度学习

| 脉络 | 规模 | 入口 |
| --- | --- | --- |
| M01 统计学习与科学评估基础 | 60 小节 · DONE 55 / WAITING 5 / REUSE 0 | [README](content/深度学习/数学与统计基础/M01_统计学习与科学评估基础/README.md) |
| M02 序列建模与大模型架构 | 67 小节 · DONE 35 / WAITING 25 / REUSE 7 | [README](content/深度学习/深度学习与模型/M02_序列建模与大模型架构/README.md) |
| M03 图神经网络与几何学习 | 46 小节 · DONE 28 / WAITING 8 / REUSE 10 | [README](content/深度学习/深度学习与模型/M03_图神经网络与几何学习/README.md) |
| M04 概率生成与扩散模型 | 52 小节 · DONE 2 / WAITING 36 / REUSE 14 | [README](content/深度学习/深度学习与模型/M04_概率生成与扩散模型/README.md) |
| R01 强化学习 | 70 小节 · DONE 70 / WAITING 0 / REUSE 0 | [README](content/深度学习/强化学习/R01_强化学习/README.md) |

### 计算机系统

| 脉络 | 规模 | 入口 |
| --- | --- | --- |
| S01 大模型推理系统 | 104 小节 · DONE 19 / WAITING 85 / REUSE 0 | [README](content/计算机系统/大模型推理系统/S01_大模型推理系统/README.md) |
| S02 GPU 内核与性能工程 | 36 小节 · DONE 11 / WAITING 25 / REUSE 0 | [README](content/计算机系统/算子与性能工程/S02_GPU 内核与性能工程/README.md) |
| S03 容器隔离、镜像、运行时与网络 | 105 小节 · DONE 105 / WAITING 0 / REUSE 0 | [README](content/计算机系统/云原生与容器/S03_容器隔离、镜像、运行时与网络/README.md) |
| S04 Kubernetes 集群 | 67 小节 · DONE 67 / WAITING 0 / REUSE 0 | [README](content/计算机系统/云原生与容器/S04_Kubernetes 集群/README.md) |

### 杂项

不适合进入知识脉络的碎片内容，保留来源目录结构。

| 分类 | 规模 | 入口 |
| --- | --- | --- |
| 工具与排障 | 14 篇 | [README](content/杂项/工具与排障/README.md) |
| 未成系列 | 234 篇 | [README](content/杂项/未成系列/README.md) |
| 观点与评测 | 0 篇 | [README](content/杂项/观点与评测/README.md) |
| 其他 | 0 篇 | [README](content/杂项/其他/README.md) |

## 质量与约定

- **有据可查**：博客只依据「图-字幕」图文稿写作；关键结论带时间戳，配图来自原片。
- **时间戳够用**：每篇至少 10 个，并随视频时长递增；接近 60 分钟时可按内容结构拆篇，拆后文件名加 `-1` / `-2` 标号。
- **完整覆盖**：不因篇幅省略难讲的段落；宁可长，不可粗。
- **公式、图片与时间戳**：图片与时间戳由 skill 的 check 脚本报告，公式由本仓库的 `scripts/check/` 报告；按输出修到 0。配图直接使用原片代表帧，保持原始画面。
- **进度可追踪**：`README.md` 行尾的 `[WAITING]` / `[PROCESSING]` / `[DONE]` / `[REUSE]` / `[ABORT]` 是唯一进度标记。`[REUSE]` 是终态，表示该小节由另一脉络的已 `[DONE]` 小节满足，不另建正文。

## 工具与依赖

```bash
# 安装 video2blog skill（本项目内容由它生成）
npx skills add tsingyuec/video2blog-skill

# Python 依赖：抽帧、图像处理、视频下载
pip install -r ~/.agents/skills/video2blog/requirements.txt

# 图片/时间戳检查用 Python；公式检查需要 Node.js 与 vendor/katex/
SKILL="${VIDEO2BLOG_SKILL:-$HOME/.agents/skills/video2blog}"
python3 "$SKILL/scripts/check/check_images.py" content/<系列>
python3 "$SKILL/scripts/check/check_blog.py" content/<系列>
node scripts/check/check_md_math.mjs content/<系列>
python site/build_site.py --check
```

图片与时间戳检查在 skill 的 `scripts/check/`；公式检查在本仓库的 `scripts/check/`，依赖 `vendor/katex/`。

## 维护

- 新增系列：先 `catalog:<主题>` 生成目录，再在根 README 的「系列索引」登记，最后 `build:<系列>` 逐批成稿。
- 调整目录：同步 README 行、博客目录与根索引链接，改完跑死链检查。
- 已发布的博客只做挂接，不改正文、不搬文件；需要改写时另开任务。

Agent 的完整规则见 [AGENTS.md](AGENTS.md)。
