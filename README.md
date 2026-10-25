# 视频图文博客库

把 Bilibili / YouTube 视频整理成「**视频演说图文稿** + **初学者也能看懂的博客**」的合集。
内容按**主题系列**分目录，每个系列一个 `README.md`，用于索引该系列下的视频。处理过程中的文稿与其它中间结果放在 `_work/`，最终博客放在 `content/`。

> **给 Agent 的规则**（目录结构 / 处理约定 / skill 安装 / 处理流程 / 交互约定）见 [AGENTS.md](AGENTS.md)。

## 目录结构

```
_work/                          # 处理中间结果（体积大、可再生，不进版本库）
└─ <系列>/ …                    # 视频、抽帧、字幕、文稿
content/                        # 最终产物
└─ <系列>/
   ├─ README.md                  # 该系列的视频索引
   └─ blog/                      # 博客与配图
```

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
| biomodel | 生物分子与细胞建模（AlphaFold / ProteinMPNN / RFdiffusion / RoseTTAFold / 蛋白质设计 / HighFold / GROMACS / 虚拟细胞） | 53 | [content/biomodel](content/biomodel/README.md) |
| 虚拟细胞 | 虚拟细胞精选版（每个视频一篇：总览 / 数据 / 评价 / 三个模型 / 选型） | 11 | [content/虚拟细胞](content/虚拟细胞/README.md) |
| biodata | 生物数据站点（STRING / UniProt） | 5 | [content/biodata](content/biodata/README.md) |
| biobasic | 公共生物学（PPI 概念 / 互作研究技术 / 酵母双杂交） | 4 | [content/biobasic](content/biobasic/README.md) |
| protein_interaction | Rosetta 蛋白-蛋白相互作用（PPI）设计工作坊（2025） | 8（已整理 2） | [content/protein_group/protein_interaction](content/protein_group/protein_interaction/README.md) |
| protein_ml_bootcamp | Rosetta ML Bootcamp：蛋白质建模与设计的机器学习方法 | 18（已整理 7） | [content/protein_group/protein_ml_bootcamp](content/protein_group/protein_ml_bootcamp/README.md) |
| kubernetes | Kubernetes RBAC 权限控制（Anton Putra） | 1 | [content/kubernetes](content/kubernetes/README.md) |
| kubernetes_cursor | 40 天 Kubernetes 挑战 / CKA 全课程（Tech Tutorials with Piyush） | 40+（已整理 8） | [content/kubernetes_cursor](content/kubernetes_cursor/README.md) |
| drug_design | AI 药物发现与分子生成（GenMol） | 1 | [content/drug_design](content/drug_design/README.md) |
| ai4s_tasks | AI for Science 核心任务（逆合成/口袋识别/分子生成/MOF/蛋白编辑/抗体CDR） | 6 | [content/ai4s_tasks](content/ai4s_tasks/README.md) |
