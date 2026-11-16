# 视频图文博客库

把 Bilibili / YouTube 视频整理成「**视频演说图文稿** + **初学者也能看懂的博客**」的合集。
内容按**主题系列**分目录，每个目录一个 `README.md` 作索引。处理过程中的文稿与其它中间结果放在 `_work/`，最终博客放在 `content/`。

> **给 Agent 的规则**（目录结构 / 处理约定 / skill 安装 / 处理流程 / 调度 / 交互约定）见 [AGENTS.md](AGENTS.md)；
> **单条任务的执行细则**见 [SUBAGENTS.md](SUBAGENTS.md)。

## 目录结构

```
_work/                          # 处理中间结果（体积大、可再生，不进版本库）
└─ <系列>/<条目名>/ …            # 视频、抽帧、字幕、图文稿
content/                        # 最终产物：博客 + 配图 + 索引
└─ <系列>/
   ├─ README.md                  # 该系列的视频索引
   ├─ <名称>.md                  # 博客（可直接放，也可按主题再分目录）
   └─ assets/<名称>/             # 博客配图
```

`content/` 的层级随主题而定，规则只有一条：`README.md` 是所在目录的索引，`<名称>.md` 是博客正文，`assets/<名称>/` 是它的配图。详见 [AGENTS.md](AGENTS.md#目录结构)。

## 站点

`content/` 由 `site/build_site.py` 装配成 `build/docs`（重写文内链接、按目录树生成侧栏），再由 `mkdocs build` 输出静态站到 `build/site`；推送到 `main` 后由 GitHub Actions 自动发布。本地预览：

```bash
pip install -r requirements.txt
python site/build_site.py && mkdocs serve
```

内容质检（公式 / 图片 / 构建产物公式）见 [scripts/README.md](scripts/README.md)。

## 系列索引

| 系列 | 主题 | 视频数 | 入口 |
| --- | --- | --- | --- |
| cs336 | Stanford CS336 从零构建大语言模型 | 18 | [content/cs336](content/cs336/README.md) |
| agent | 智能体系统（RSI 综述：模型参数与脚手架的自我改进） | 1 | [content/agent](content/agent/README.md) |
| graph_deep_learning | 图深度学习：理论与应用（原著作者精讲） | 9 | [content/graph_deep_learning](content/graph_deep_learning/README.md) |
| gpu | 显卡 / GPU 的工作原理 | 1 | [content/gpu](content/gpu/README.md) |
| network_mtu | MTU / MSS、PMTUD 网络黑洞与 IPsec 排障 | 4 | [content/network_mtu](content/network_mtu/README.md) |
| minimind | 从零手敲大模型（Minimind） | 25 | [content/minimind](content/minimind/README.md) |
| vllm | 从零手撸 vLLM（推理引擎） | 15 | [content/vllm_group/vllm](content/vllm_group/vllm/README.md) |
| vllm_class | vLLM 小课堂（vLLM 官方直播系列） | 21 | [content/vllm_group/vllm_class](content/vllm_group/vllm_class/README.md) |
| vllm_meetup | vLLM Meetup 线下演讲 | 1 | [content/vllm_group/vllm_meetup](content/vllm_group/vllm_meetup/README.md) |
| aiinfra | 手撕 AI Infra 算子（CUDA + Triton + PyTorch） | 5 | [content/aiinfra](content/aiinfra/README.md) |
| aiinfra_learning | AI INFRA 学习（vLLM 推理优化） | 5 | [content/aiinfra_learning](content/aiinfra_learning/README.md) |
| flash_attention | Flash Attention 学习过程详解 | 8 | [content/flash_attention](content/flash_attention/README.md) |
| biomodel | 生物分子与细胞建模（AlphaFold / ProteinMPNN / RFdiffusion / RoseTTAFold / 蛋白质设计 / HighFold / GROMACS / 虚拟细胞） | 53 | [content/biomodel](content/biomodel/README.md) |
| 虚拟细胞 | 虚拟细胞精选版（每个视频一篇：总览 / 数据 / 评价 / 三个模型 / 选型）＋ 实验基础四类（文库构建 / 表达载体 / sgRNA / 基因敲除） | 11 ＋ 8 | [content/虚拟细胞](content/虚拟细胞/README.md) |
| biodata | 生物数据站点（STRING / UniProt） | 5 | [content/biodata](content/biodata/README.md) |
| biobasic | 公共生物学（PPI 概念 / 互作研究技术 / 酵母双杂交） | 4 | [content/biobasic](content/biobasic/README.md) |
| protein_interaction | Rosetta 蛋白-蛋白相互作用（PPI）设计工作坊（2025） | 8（已整理 2） | [content/protein_group/protein_interaction](content/protein_group/protein_interaction/README.md) |
| protein_ml_bootcamp | Rosetta ML Bootcamp：蛋白质建模与设计的机器学习方法 | 18（已整理 7） | [content/protein_group/protein_ml_bootcamp](content/protein_group/protein_ml_bootcamp/README.md) |
| K8s集群 | Kubernetes 集群架构与数据面（组件职责 / 声明式 API / 控制器 / 调度 / CNI / Service / CSI / 准入） | 6 章 · 17 小节 · 67 条目（整理中） | [content/K8s集群](content/K8s集群/README.md) |
| reinforcement_learning | 强化学习知识体系（MDP / 动态规划 / MC / TD / DQN / 策略梯度 / Actor-Critic / PPO / SAC / MBRL / 模仿学习 / 离线 RL / MARL / RLHF） | 5 篇 · 14 章 · 70 条目（整理中） | [content/reinforcement_learning](content/reinforcement_learning/README.md) |
| drug_design | AI 药物发现与分子生成（GenMol） | 1 | [content/drug_design](content/drug_design/README.md) |
| ai4s_tasks | AI for Science 核心任务（逆合成/口袋识别/分子生成/MOF/蛋白编辑/抗体CDR） | 6 | [content/ai4s_tasks](content/ai4s_tasks/README.md) |
| 生物信息 | 生物信息知识体系（格式 / 结构 / 预测 / 生成 / 管线，284 篇） | 284 | [content/生物信息](content/生物信息/README.md) |
| 容器技术 | 容器技术知识体系（Linux 基础 / 镜像 / 存储 / 网络 / eBPF / 运行时，279 篇） | 279 | [content/容器技术](content/容器技术/README.md) |
