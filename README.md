# 视频图文博客库

把 Bilibili / YouTube 视频整理成「**视频演说图文稿** + **初学者也能看懂的博客**」的合集。
内容按**主题系列**分目录，每个系列一个 `README.md`，用于索引该系列下的视频。处理过程中的文稿与其它中间结果放在 `_work/`，最终博客放在 `content/`。

## 目录结构

```
_work/                          # 处理中间结果（体积大、可再生，不进版本库）
└─ <系列>/
   ├─ videos/<视频ID>.mp4        # 下载的视频（仅视频流）
   ├─ frames/<视频ID>/           # 1fps 抽帧
   ├─ subs/<视频ID>.srt          # 字幕
   └─ transcripts/<名称>.md      # 视频演说图文稿（图-字幕对照）

content/                        # 最终产物
└─ <系列>/                       # 也可再套一层分组目录，如 content/protein_group/<系列>/
   ├─ README.md                  # 该系列的视频索引
   └─ blog/
      ├─ <名称>.md               # 博客
      └─ assets/<名称>/          # 博客配图
```

- **处理约定**：处理视频时，所有**中间结果**——下载的视频、1fps 抽帧、字幕，以及「图-字幕」**视频演说图文稿（文稿）**——统一放在 `_work/` 目录下；最终生成的**博客**放在 `content/` 目录下。也就是说，`content/` 只收录博客、配图与系列索引，**不包含文稿**。
- **`<名称>`**：博客按视频名称命名——多 P 系列为 `第NN讲_<分P标题>`（如 `第07讲_理论：RMSNorm`），单视频为视频名称。
- **分组目录**：相关系列可再套一层分组目录，如 `content/vllm_group/`、`content/protein_group/`；分组目录下同样放一个 `README.md` 作为该分组的索引。
- **版本控制**：仓库只收录各系列的 `README.md`、`blog/`（含配图）与 `code/`。中间结果（`_work/` 下的视频、抽帧、字幕、文稿）体积大且可再生，均由 `.gitignore` 排除。

## 系列索引

| 系列 | 主题 | 视频数 | 入口 |
| --- | --- | --- | --- |
| cs336 | Stanford CS336 从零构建大语言模型 | 18 | [content/cs336](content/cs336/README.md) |
| gpu | 显卡 / GPU 的工作原理 | 1 | [content/gpu](content/gpu/README.md) |
| minimind | 从零手敲大模型（Minimind） | 25 | [content/minimind](content/minimind/README.md) |
| vllm | 从零手撸 vLLM（推理引擎） | 15 | [content/vllm_group/vllm](content/vllm_group/vllm/README.md) |
| vllm_class | vLLM 小课堂（vLLM 官方直播系列） | 21 | [content/vllm_group/vllm_class](content/vllm_group/vllm_class/README.md) |
| vllm_meetup | vLLM Meetup 线下演讲 | 1 | [content/vllm_group/vllm_meetup](content/vllm_group/vllm_meetup/README.md) |
| aiinfra | 手撕 AI Infra 算子（CUDA + Triton + PyTorch） | 5 | [content/aiinfra](content/aiinfra/README.md) |
| aiinfra_learning | AI INFRA 学习（vLLM 推理优化） | 5 | [content/aiinfra_learning](content/aiinfra_learning/README.md) |
| flash_attention | Flash Attention 学习过程详解 | 8 | [content/flash_attention](content/flash_attention/README.md) |
| protein_design | AI + 蛋白质设计（从经典力场到深度学习、AlphaFold 实践） | 12 | [content/protein_group/protein_design](content/protein_group/protein_design/README.md) |
| alphafold | AlphaFold 图解与算法解析（中译长文 / 中文逐层拆解 / 视频博客） | 9 篇 | [content/protein_group/alphafold](content/protein_group/alphafold/README.md) |
| protein_interaction | Rosetta 蛋白-蛋白相互作用（PPI）设计工作坊（2025） | 8（已整理 2） | [content/protein_group/protein_interaction](content/protein_group/protein_interaction/README.md) |
| protein_ml_bootcamp | Rosetta ML Bootcamp：蛋白质建模与设计的机器学习方法 | 18（已整理 7） | [content/protein_group/protein_ml_bootcamp](content/protein_group/protein_ml_bootcamp/README.md) |

## 安装 video2blog skill

本项目的内容由 [`video2blog`](https://github.com/tsingyuec/video2blog-skill) skill 生成。

**方式一：交给 Agent 安装（推荐）**

```
Use the skills in "https://github.com/tsingyuec/video2blog-skill" that are relevant to the current task. Run `npx skills add "https://github.com/tsingyuec/video2blog-skill"` and select the relevant skills, then follow their instructions.
```

**方式二：命令行安装**

```bash
npx skills add tsingyuec/video2blog-skill       # 安装到 Agent 技能目录（本机为 ~/.agents/skills/video2blog/）
```

**安装 Python 依赖**（抽帧、图像处理、视频下载）：

```bash
pip install -r ~/.agents/skills/video2blog/requirements.txt   # opencv-python、numpy、pillow、yt-dlp
# 无桌面环境可将 opencv-python 换成 opencv-python-headless
```

- 依赖：Python 3 + `opencv-python` / `numpy`（抽帧）、`pillow`（图像处理）、`yt-dlp`（下载）；字幕抓取为纯标准库实现，无需额外依赖，但需能访问 `kedou.life`。

## 处理流程

基于 `video2blog` skill：**下载 → 抽帧 → 抓取字幕 → 生成「图-字幕」视频演说图文稿 → 通顺化 → 写博客**。

- 多 P 视频按 `?p=N` 逐集下载，时间戳跳转链接为 `?p=N&t=<秒>`；文稿与博客按 `第NN讲_<分P标题>` 命名。
- **产物落位**：下载的视频、抽帧、字幕与文稿都落在 `_work/<系列>/`；最终博客落在 `content/<系列>/blog/`。
- 博客严格基于视频演说图文稿撰写，内容可核查；字幕来自 B 站 AI 字幕，已逐窗口纠正错拼。
