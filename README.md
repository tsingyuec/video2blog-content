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
| **知识目录** | `content/<系列>/README.md` | 章 → 节 → 小节；读什么、读到哪、还缺什么，都看这一份 |
| **博客** | `content/<系列>/X.Y_<节>/X.Y.Z_<小节>/<标题>.md` | 每小节通常 1–3 篇，每支视频一篇（同一支视频接近 60 分钟可拆篇）；结论先行，公式、配图、时间戳齐全 |
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
| `catalog:<主题>` | 搭知识目录：章 / 节 / 小节 | `content/<系列>/README.md` |
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


## 系列索引

### 大模型与推理系统

| 系列 | 主题 | 规模 | 入口 |
| --- | --- | --- | --- |
| AI基建 | AI 基础设施知识体系：Transformer 解剖、Attention/RoPE、KV Cache、量化、算子、vLLM/SGLang、投机采样、分布式推理 | 159 小节 · 7 篇（整理中） | [content/AI基建](content/AI基建/README.md) |
| cs336 | Stanford CS336 从零构建大语言模型 | 19 篇 | [content/cs336](content/cs336/README.md) |
| minimind | 从零手敲大模型（Minimind） | 25 篇 | [content/minimind](content/minimind/README.md) |
| vllm | 从零手撸 vLLM（推理引擎） | 15 篇 | [content/vllm_group/vllm](content/vllm_group/vllm/README.md) |
| vllm_class | vLLM 小课堂（vLLM 官方直播系列） | 21 篇 | [content/vllm_group/vllm_class](content/vllm_group/vllm_class/README.md) |
| vllm_meetup | vLLM Meetup 线下演讲 | 1 篇 | [content/vllm_group/vllm_meetup](content/vllm_group/vllm_meetup/README.md) |
| aiinfra | 手撕 AI Infra 算子（CUDA + Triton + PyTorch） | 5 篇 | [content/aiinfra](content/aiinfra/README.md) |
| aiinfra_learning | AI INFRA 学习（vLLM 推理优化） | 5 篇 | [content/aiinfra_learning](content/aiinfra_learning/README.md) |
| flash_attention | Flash Attention 学习过程详解 | 8 篇 | [content/flash_attention](content/flash_attention/README.md) |

### 智能体与强化学习

| 系列 | 主题 | 规模 | 入口 |
| --- | --- | --- | --- |
| reinforcement_learning | 强化学习知识体系：MDP / 动态规划 / MC / TD / DQN / 策略梯度 / Actor-Critic / PPO / SAC / MBRL / 模仿学习 / 离线 RL / MARL / RLHF | 70 小节 · 128 篇（整理中） | [content/reinforcement_learning](content/reinforcement_learning/README.md) |

### 云原生与系统

| 系列 | 主题 | 规模 | 入口 |
| --- | --- | --- | --- |
| K8s集群 | Kubernetes 集群架构与数据面：组件职责 / 声明式 API / 控制器 / 调度 / CNI / Service / CSI / 准入 | 67 小节 · 139 篇（整理中） | [content/K8s集群](content/K8s集群/README.md) |
| 容器技术 | 容器技术知识体系：Linux 基础 / 镜像 / 存储 / 网络 / eBPF / 运行时 | 109 小节 · 279 篇 | [content/容器技术](content/容器技术/README.md) |
| gpu | 显卡 / GPU 的工作原理 | 3 篇 | [content/gpu](content/gpu/README.md) |
| network_mtu | MTU / MSS、PMTUD 网络黑洞与 IPsec 排障 | 4 篇 | [content/network_mtu](content/network_mtu/README.md) |

### 生命科学与 AI4S

| 系列 | 主题 | 规模 | 入口 |
| --- | --- | --- | --- |
| 生物信息 | 生物信息知识体系：格式 / 结构 / 预测 / 生成 / 管线 | 123 小节 · 284 篇 | [content/生物信息](content/生物信息/README.md) |
| biomodel | 生物分子与细胞建模：AlphaFold / ProteinMPNN / RFdiffusion / RoseTTAFold / GROMACS | 55 篇 | [content/biomodel](content/biomodel/README.md) |
| 虚拟细胞 | 虚拟细胞精选版（总览 / 数据 / 评价 / 三个模型 / 选型）＋ 实验基础四类 | 19 篇 | [content/虚拟细胞](content/虚拟细胞/README.md) |
| biodata | 生物数据站点（STRING / UniProt） | 5 篇 | [content/biodata](content/biodata/README.md) |
| biobasic | 公共生物学（PPI 概念 / 互作研究技术 / 酵母双杂交） | 4 篇 | [content/biobasic](content/biobasic/README.md) |
| protein_interaction | Rosetta 蛋白-蛋白相互作用（PPI）设计工作坊（2025） | 8 小节 · 2 篇（整理中） | [content/protein_group/protein_interaction](content/protein_group/protein_interaction/README.md) |
| protein_ml_bootcamp | Rosetta ML Bootcamp：蛋白质建模与设计的机器学习方法 | 18 小节 · 7 篇（整理中） | [content/protein_group/protein_ml_bootcamp](content/protein_group/protein_ml_bootcamp/README.md) |
| drug_design | AI 药物发现与分子生成（GenMol） | 1 篇 | [content/drug_design](content/drug_design/README.md) |
| ai4s_tasks | AI for Science 核心任务：逆合成 / 口袋识别 / 分子生成 / MOF / 蛋白编辑 / 抗体 CDR | 6 篇 | [content/ai4s_tasks](content/ai4s_tasks/README.md) |

### 图学习

| 系列 | 主题 | 规模 | 入口 |
| --- | --- | --- | --- |
| graph_deep_learning | 图深度学习：理论与应用（原著作者精讲） | 9 篇 | [content/graph_deep_learning](content/graph_deep_learning/README.md) |

## 质量与约定

- **有据可查**：博客只依据「图-字幕」图文稿写作；关键结论带时间戳，配图来自原片。
- **时间戳够用**：每篇至少 10 个，并随视频时长递增；接近 60 分钟时可按内容结构拆篇，拆后文件名加 `-1` / `-2` 标号。
- **完整覆盖**：不因篇幅省略难讲的段落；宁可长，不可粗。
- **公式、图片与时间戳**：图片与时间戳由 skill 的 check 脚本报告，公式由本仓库的 `scripts/check/` 报告；按输出修到 0。配图直接使用原片代表帧，保持原始画面。
- **进度可追踪**：`README.md` 行尾的 `[WAITING]` / `[PROCESSING]` / `[DONE]` / `[ABORT]` 是唯一进度标记。

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
