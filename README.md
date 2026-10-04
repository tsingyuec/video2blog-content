# 视频图文博客库

把 Bilibili / YouTube 视频整理成「**视频演说图文稿** + **初学者也能看懂的博客**」的合集。
内容按**主题系列**分目录，每个系列一个 `README.md`，用于索引该系列下的视频。

## 目录结构

```
content/
└─ <系列>/
   ├─ README.md                    # 该系列的视频索引
   ├─ transcripts/
   │  ├─ <名称>.md                 # 视频演说图文稿（图-字幕对照）
   │  └─ img/<名称>/               # 文稿中的代表帧
   └─ blog/
      ├─ <名称>.md                 # 博客
      └─ assets/<名称>/            # 博客配图
```

- **`<名称>`**：博客与视频演说图文稿按视频名称命名——多 P 系列为 `第NN讲_<分P标题>`（如 `第07讲_理论：RMSNorm`），单视频为视频名称。
- **版本控制**：仓库只收录各系列的 `README.md`、`blog/` 与 `transcripts/`（含各自配图）。下载的视频（`videos/`）、1fps 抽帧（`frames/`）、字幕（`subs/`）、系列元数据（`series.json`）与处理工具体积大且可再生，均由 `.gitignore` 排除。

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
| protein_design | AI + 蛋白质设计（从经典力场到深度学习 / 实践操作） | 2 | [content/protein_design](content/protein_design/README.md) |
| protein_interaction | Rosetta 蛋白-蛋白相互作用（PPI）设计工作坊（2025） | 8（已整理 2） | [content/protein_interaction](content/protein_interaction/README.md) |
| protein_ml_bootcamp | Rosetta ML Bootcamp：蛋白质建模与设计的机器学习方法 | 18（已整理 3） | [content/protein_ml_bootcamp](content/protein_ml_bootcamp/README.md) |

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
- 博客严格基于视频演说图文稿撰写，内容可核查；字幕来自 B 站 AI 字幕，已逐窗口纠正错拼。
