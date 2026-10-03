# 系列：从0手撸 vLLM —— 从零实现一个推理引擎

- **平台**：Bilibili
- **UP 主**：我十六条
- **来源**：合集《【从0手撸vLLM】》（season_id 7260459）
- **项目仓库**：[Wenyueh/MinivLLM](https://github.com/Wenyueh/MinivLLM)
- **已整理**：15 / 15 集（约 4 小时 33 分）

## 建议学习路线

| 阶段 | 讲次 | 内容 |
| --- | --- | --- |
| 项目准备 | 00 | MiniVLLM 项目介绍、文档与技术路线 |
| 环境与算子基础 | 01 | 安装、`uv` 环境、activation（SiLU 等） |
| 归一化与线性层并行 | 02–06 | RMSNorm；列并行实现与权重加载；合并线性层；QKV 张量并行；行并行 |
| 嵌入层并行 | 07–08 | VocabParallelEmbedding（词表并行嵌入）；lm_head 与词表列并行 |
| 推理引擎核心 | 09.1–13 | Prefill 显存分配与 Triton 网格；FlashAttention 与 Online Softmax；PagedAttention 与 Decode；KV Cache；RoPE；序列管理 |

## 分讲索引

| 讲次 | 标题 | 时长 | 视频演说图文稿 | 博客 | 配图 | 原视频 |
| ---: | --- | ---: | --- | --- | ---: | --- |
| 00 | minivllm项目介绍 | 03:10 | [文稿](transcripts/第00讲_minivllm项目介绍.md) | [博客](blog/第00讲_minivllm项目介绍.md) | 6 | [B站](https://www.bilibili.com/video/BV1Vjz1B2EQu/) |
| 01 | minivllm安装&activation.py实现 | 16:57 | [文稿](transcripts/第01讲_minivllm安装&activation.py实现.md) | [博客](blog/第01讲_minivllm安装&activation.py实现.md) | 11 | [B站](https://www.bilibili.com/video/BV1M4zeB3EoY/) |
| 02 | layernorm.py中的RMSNorm实现 | 10:10 | [文稿](transcripts/第02讲_layernorm.py中的RMSNorm实现.md) | [博客](blog/第02讲_layernorm.py中的RMSNorm实现.md) | 11 | [B站](https://www.bilibili.com/video/BV1sTz9BREvX/) |
| 03 | linear.py&张量并行&线性层列并行实现&权重加载 | 19:02 | [文稿](transcripts/第03讲_linear.py&张量并行&线性层列并行实现&权重加载.md) | [博客](blog/第03讲_linear.py&张量并行&线性层列并行实现&权重加载.md) | 12 | [B站](https://www.bilibili.com/video/BV1Br6iBaEVV/) |
| 04 | linear.py&MergedColumnParallelLinear&合并线性层张量并行 | 09:54 | [文稿](transcripts/第04讲_linear.py&MergedColumnParallelLinear&合并线性层张量并行.md) | [博客](blog/第04讲_linear.py&MergedColumnParallelLinear&合并线性层张量并行.md) | 10 | [B站](https://www.bilibili.com/video/BV11b64BUE5G/) |
| 05 | linear.py&QKV张量并行&合并线性层 | 10:33 | [文稿](transcripts/第05讲_linear.py&QKV张量并行&合并线性层.md) | [博客](blog/第05讲_linear.py&QKV张量并行&合并线性层.md) | 10 | [B站](https://www.bilibili.com/video/BV1kUfDBfEuK/) |
| 06 | linear.py&行并行&张量并行 | 13:49 | [文稿](transcripts/第06讲_linear.py&行并行&张量并行.md) | [博客](blog/第06讲_linear.py&行并行&张量并行.md) | 11 | [B站](https://www.bilibili.com/video/BV1JAFEzPE1F/) |
| 07 | embedding_head.py&嵌入层并行&VocabParallelEmbedding | 22:56 | [文稿](transcripts/第07讲_embedding_head.py&嵌入层并行&VocabParallelEmbedding.md) | [博客](blog/第07讲_embedding_head.py&嵌入层并行&VocabParallelEmbedding.md) | 13 | [B站](https://www.bilibili.com/video/BV1xxcFzbEcb/) |
| 08 | embedding_head.py&lm_head&词表列并行 | 17:26 | [文稿](transcripts/第08讲_embedding_head.py&lm_head&词表列并行.md) | [博客](blog/第08讲_embedding_head.py&lm_head&词表列并行.md) | 14 | [B站](https://www.bilibili.com/video/BV1GWcbzWE1x/) |
| 09.1 | 推理过程中Prefill阶段的GPU显存分配&Triton网格划分逻辑 | 32:22 | [文稿](transcripts/第09.1讲_推理过程中Prefill阶段的GPU显存分配&Triton网格划分逻辑.md) | [博客](blog/第09.1讲_推理过程中Prefill阶段的GPU显存分配&Triton网格划分逻辑.md) | 13 | [B站](https://www.bilibili.com/video/BV1CNDgB4EYy/) |
| 09.2 | FlashAttention&Online Softmax&案例详解 | 37:33 | [文稿](transcripts/第09.2讲_FlashAttention&Online Softmax&案例详解.md) | [博客](blog/第09.2讲_FlashAttention&Online Softmax&案例详解.md) | 15 | [B站](https://www.bilibili.com/video/BV1UaSoBhEco/) |
| 10 | Decode阶段&PagedAttention代码详解&Attention推理过程 | 44:40 | [文稿](transcripts/第10讲_Decode阶段&PagedAttention代码详解&Attention推理过程.md) | [博客](blog/第10讲_Decode阶段&PagedAttention代码详解&Attention推理过程.md) | 13 | [B站](https://www.bilibili.com/video/BV14a5r6YEhY/) |
| 11 | KV Cache存储过程&Triton实现 | 20:13 | [文稿](transcripts/第11讲_KV Cache存储过程&Triton实现.md) | [博客](blog/第11讲_KV Cache存储过程&Triton实现.md) | 13 | [B站](https://www.bilibili.com/video/BV1SR7k67Ee9/) |
| 12 | RoPE 旋转嵌入 | 19:57 | [文稿](transcripts/第12讲_RoPE旋转嵌入.md) | [博客](blog/第12讲_RoPE旋转嵌入.md) | 12 | [B站](https://www.bilibili.com/video/BV1U6jN6MEet/) |
| 13 | sequence.py 序列对象介绍 & 推理引擎中的序列管理 | 05:03 | [文稿](transcripts/第13讲_sequence.py序列对象介绍&推理引擎中的序列管理.md) | [博客](blog/第13讲_sequence.py序列对象介绍&推理引擎中的序列管理.md) | 8 | [B站](https://www.bilibili.com/video/BV1aYMM6wEsm/) |

## 相关资源（来自视频简介）

- MiniVLLM 仓库：https://github.com/Wenyueh/MinivLLM
