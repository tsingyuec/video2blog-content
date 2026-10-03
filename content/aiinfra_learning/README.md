# 系列：AI INFRA 学习（vLLM 推理优化）

- **平台**：Bilibili
- **UP 主**：Se7en的架构笔记
- **来源**：合集《AI INFRA》（season_id 5602052）
- **已整理**：5 / 5 集（约 6 小时 3 分）
- **主题**：从 LLM 全景图与 vLLM 快速入门起步，逐层深入 vLLM 的核心机制（PagedAttention、Prefix Caching、Chunked Prefill）与主流推理优化技术（Speculative Decoding）

## 建议学习路线

| 阶段 | 讲次 | 内容 |
| --- | --- | --- |
| 入门认知 | 01 | LLM 全景图介绍、vLLM 快速入门：从大模型推理全貌到把 vLLM 跑起来 |
| 核心机制 | 02 | vLLM PagedAttention 论文精读：KV cache 显存浪费与分页式内存管理 |
| 优化技术 | 03 | Prefix Caching 原理详解：共享前缀的 KV 复用 |
| 优化技术 | 04 | Speculative Decoding 实现方案：小模型起草、大模型验证的加速范式 |
| 优化技术 | 05 | Chunked-Prefills 分块预填充：把长 Prefill 切块以平滑调度 |

## 分讲索引

| 讲次 | 标题 | 时长 | 视频演说图文稿 | 博客 | 配图 | 原视频 |
| ---: | --- | ---: | --- | --- | ---: | --- |
| 01 | LLM 全景图介绍 & vLLM 快速入门 | 1:03:25 | [文稿](transcripts/第01讲_LLM全景图介绍&vLLM快速入门.md) | [博客](blog/第01讲_LLM全景图介绍与vLLM快速入门.md) | 12 | [B站](https://www.bilibili.com/video/BV1T2EGzLEHi/) |
| 02 | vLLM PagedAttention 论文精读 | 1:54:06 | [文稿](transcripts/第02讲_vLLM_PagedAttention论文精读.md) | [博客](blog/第02讲_vLLM_PagedAttention论文精读.md) | 16 | [B站](https://www.bilibili.com/video/BV1GWjjzfE1b/) |
| 03 | Prefix Caching 原理详解 | 1:01:15 | [文稿](transcripts/第03讲_Prefix_Caching原理详解.md) | [博客](blog/第03讲_Prefix_Caching原理详解.md) | 12 | [B站](https://www.bilibili.com/video/BV1jgTRzSEjS/) |
| 04 | Speculative Decoding 实现方案 | 57:03 | [文稿](transcripts/第04讲_Speculative_Decoding实现方案.md) | [博客](blog/第04讲_Speculative_Decoding实现方案.md) | 11 | [B站](https://www.bilibili.com/video/BV1Q5KWzQEhn/) |
| 05 | Chunked-Prefills 分块预填充 | 1:07:07 | [文稿](transcripts/第05讲_Chunked_Prefills分块预填充.md) | [博客](blog/第05讲_Chunked_Prefills分块预填充.md) | 13 | [B站](https://www.bilibili.com/video/BV1f2uczGEqt/) |

## 核心知识点速览

- **第01讲**：LLM 推理全流程与 AI Infra 的分层；vLLM 的定位、特性与快速上手（安装、启动、接口调用）。
- **第02讲**：PagedAttention 论文精读——KV cache 的 reserved 与内/外部碎片三种浪费；把操作系统的分页思想搬到 KV cache，用 block table 做逻辑块到物理块的映射；共享前缀、并行采样与 copy-on-write；block size 与重计算/换出（recomputation/swapping）的权衡。
- **第03讲**：Prefix Caching（前缀缓存）原理——相同前缀的 KV 如何跨请求复用，命中判定与淘汰策略，对首 token 延时的影响。
- **第04讲**：Speculative Decoding（投机解码）实现方案——草稿模型/草稿序列如何生成，目标模型如何一次验证多个 token 并保证输出分布不变。
- **第05讲**：Chunked Prefill（分块预填充）——把长 Prefill 拆成多个 chunk 与 Decode 混批，改善调度与显存利用。

## 相关资源

- vLLM 项目：https://github.com/vllm-project/vllm
