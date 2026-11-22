# S01 大模型推理系统

编号：S01 · 类型：模型专题 · 目录规模：104 个小节（三级叶子节点）。

> 本文件是 `content-new` 的完整目录草案。状态统一为 `[WAITING]`，待 Phase 2 映射 video2blog 博客后更新。

## 脉络章程

**知识主线**：从 Prefill/Decode 两阶段出发，沿 KV Cache、批处理、显存管理、解码加速、量化、分布式推理到服务治理，理解一个推理引擎为什么这样设计。

**一句话范围**：不重复讲模型结构（归 M02），也不深入 CUDA 内核实现（归 S02）；重点是系统层的调度、显存、吞吐与延迟权衡。

**学习入口 → 学习出口**：Transformer 基础与 KV Cache 概念（可复用 M02） → 能读懂 vLLM/SGLang 的核心模块，能解释 PagedAttention、连续批处理、投机采样、量化和分布式推理的收益与代价。

**完整问题链**：
1. LLM 推理的两阶段动力学与 KV Cache
2. 推理系统的核心性能指标与权衡（Trade-offs）
3. 动态调度与连续批处理（Continuous Batching）
4. 显存管理革命 —— vLLM 与 PagedAttention
5. 前缀复用与结构化生成 —— SGLang 与 RadixAttention
6. 打破自回归枷锁 —— 投机采样（Speculative Decoding）
7. 模型量化技术（Quantization）全解
8. 边缘端与异构推理引擎：llama.cpp 与 GGML 深度解析
9. 大规模分布式并行推理架构
10. 下一代生产级推理集群架构与服务治理

**与相邻脉络的关系**：Transformer 基础与 KV Cache 概念（可复用 M02）

> 博客已从 `content` 的 vLLM / AI Infra 系列迁入对应小节；暂无合适博客的小节保持 `[WAITING]`。

## 目录

<a id="s01-1"></a>
## 1 LLM 推理的两阶段动力学与 KV Cache

<a id="s01-1-1"></a>
### 1.1 预填充阶段（Prefill Phase）剖析

- 1.1.1 Prompt 并行处理特征：通用矩阵乘法（GEMM）主导的计算模式 <a id="s01-1-1-1"></a> [WAITING]
- 1.1.2 算子耗时分布：为什么 Prefill 阶段是典型的 Compute-Bound（计算受限） <a id="s01-1-1-2"></a> [WAITING]
- 1.1.3 超长 Prompt 下的显存峰值管理与中间激活值（Activations）开销 <a id="s01-1-1-3"></a> [WAITING]

<a id="s01-1-2"></a>
### 1.2 解码阶段（Decode Phase）剖析

- 1.2.1 逐 Token 自回归特征：矩阵-向量乘法（GEMV）主导的计算模式 <a id="s01-1-2-1"></a> [WAITING]
- 1.2.2 权重重复搬运困境：生成单个 Token 需遍历全量模型权重导致的 Memory-Bound（访存受限） <a id="s01-1-2-2"></a> [WAITING]
- 1.2.3 GPU 计算单元闲置率分析与提高 Batch Size 转向 GEMM 的必要性 <a id="s01-1-2-3"></a> [WAITING]

<a id="s01-1-3"></a>
### 1.3 键值缓存（KV Cache）深度精算

- 1.3.1 空间换时间：缓存历史 Token 的 K/V 张量如何将单步计算复杂度从 $O(N^2)$ 降至 $O(N)$ <a id="s01-1-3-1"></a> [DONE]
- 1.3.2 KV Cache 显存占用精确公式推导（含层数、头数、头维度、精度、Batch 与序列长度） <a id="s01-1-3-2"></a> [DONE]
- 1.3.3 模型权重、KV Cache 与运行时激活值（Activation）三者的显存占比动态变化规律 <a id="s01-1-3-3"></a> [WAITING]

<a id="s01-2"></a>
## 2 推理系统的核心性能指标与权衡（Trade-offs）

<a id="s01-2-1"></a>
### 2.1 延迟（Latency）度量体系

- 2.1.1 首字延迟（TTFT, Time To First Token）：决定用户感知响应快慢的 Prefill 指标 <a id="s01-2-1-1"></a> [WAITING]
- 2.1.2 单 Token 生成延迟（TPOT, Time Per Output Token / ITL）：决定阅读流畅度的 Decode 指标 <a id="s01-2-1-2"></a> [WAITING]
- 2.1.3 端到端请求延迟（End-to-End Latency）：排队时间 + TTFT + TPOT × 生成长度 <a id="s01-2-1-3"></a> [WAITING]

<a id="s01-2-2"></a>
### 2.2 吞吐量（Throughput）与服务质量（SLO）

- 2.2.1 系统吞吐量维度：每秒请求数（QPS/RPS）、每秒输入 Token 数与每秒输出 Token 数 <a id="s01-2-2-1"></a> [WAITING]
- 2.2.2 有效吞吐量（Goodput）：满足特定 TTFT 与 TPOT 服务等级目标（SLO）前提下的最大吞吐 <a id="s01-2-2-2"></a> [WAITING]
- 2.2.3 尾部延迟（P90 / P99 Latency）抖动成因与长尾请求治理 <a id="s01-2-2-3"></a> [WAITING]

<a id="s01-2-3"></a>
### 2.3 延迟与吞吐量的帕累托前沿（Pareto Frontier）

- 2.3.1 Batch Size 增大如何提升 Tensor Core 利用率但同时拉长单步 TPOT <a id="s01-2-3-1"></a> [WAITING]
- 2.3.2 显存容量墙对最大并发 Batch Size 的硬性约束 <a id="s01-2-3-2"></a> [WAITING]
- 2.3.3 实时交互场景（低延迟优先）与离线批处理场景（高吞吐优先）的参数配置策略 <a id="s01-2-3-3"></a> [WAITING]

<a id="s01-3"></a>
## 3 动态调度与连续批处理（Continuous Batching）

<a id="s01-3-1"></a>
### 3.1 从静态批处理到迭代级调度

- 3.1.1 静态批处理（Static Batching）的木桶效应：短请求等待长请求生成完毕造成的 GPU 算力空泡（Bubble） <a id="s01-3-1-1"></a> [WAITING]
- 3.1.2 Orca 迭代级调度（Iteration-Level Scheduling）：以单个 Token 生成步（Step）为粒度的队列状态更新 <a id="s01-3-1-2"></a> [WAITING]
- 3.1.3 异构长度混合执行：Attention 层按请求独立寻址与 Linear 层拼接（Concatenate）为大张量统一计算 <a id="s01-3-1-3"></a> [WAITING]

<a id="s01-3-2"></a>
### 3.2 Prefill 与 Decode 的调度博弈与分块预填充（Chunked Prefill）

- 3.2.1 传统 Prefill 优先策略（如 vLLM V0）的问题：新进入的长 Prompt 阻塞正在进行的 Decode 导致 TPOT 剧烈抖动 <a id="s01-3-2-1"></a> [WAITING]
- 3.2.2 Sarathi / Chunked Prefill 核心机制：将长 Prompt 切分为固定大小的 Token 块（Chunks） <a id="s01-3-2-2"></a> [DONE]
- 3.2.3 混合批次（Hybrid Batching / Piggybacking）：在单次迭代中将 Prefill 块与存量 Decode Token 打包同算，借 Decode 搭车利用计算余量 <a id="s01-3-2-3"></a> [WAITING]

<a id="s01-3-3"></a>
### 3.3 显存过载与抢占恢复机制（Preemption）

- 3.3.1 动态生成长度不可预知性引发的显存耗尽（OOM）风险与 FCFS（先来先服务）淘汰原则 <a id="s01-3-3-1"></a> [WAITING]
- 3.3.2 交换策略（Swapping）：将被害请求的物理 KV 块通过 PCIe 异步拷贝至 CPU 内存（Pinned Memory） <a id="s01-3-3-2"></a> [WAITING]
- 3.3.3 重计算策略（Recomputation）：直接丢弃 KV Cache，待显存充裕时拼接已生成 Token 重新 Prefill（何时重计算比 Swap 更快） <a id="s01-3-3-3"></a> [WAITING]

<a id="s01-4"></a>
## 4 显存管理革命 —— vLLM 与 PagedAttention

<a id="s01-4-1"></a>
### 4.1 传统连续显存分配的三大碎片顽疾

- 4.1.1 预留浪费（Reservation Waste）：按模型最大上下文长度预分配连续显存槽位 <a id="s01-4-1-1"></a> [WAITING]
- 4.1.2 内部碎片（Internal Fragmentation）：实际生成长度远小于预分配长度导致的闲置空间 <a id="s01-4-1-2"></a> [WAITING]
- 4.1.3 外部碎片（External Fragmentation）：不同长度请求频繁申请释放导致的非连续显存空洞 <a id="s01-4-1-3"></a> [WAITING]

<a id="s01-4-2"></a>
### 4.2 PagedAttention 虚拟内存映射架构

- 4.2.1 操作系统分页启发：将连续的逻辑 KV Cache 切分为固定大小（如 16 或 32 Tokens）的逻辑块（Logical Blocks） <a id="s01-4-2-1"></a> [DONE]
- 4.2.2 物理块池（Physical Block Pool）与块表（Block Table）：按需动态分配非连续显存与地址转换 <a id="s01-4-2-2"></a> [DONE]
- 4.2.3 PagedAttention CUDA 内核改造：在 Attention 计算循环中通过 Block Table 指针跳转（Gather）读取非连续 KV 块 <a id="s01-4-2-3"></a> [WAITING]

<a id="s01-4-3"></a>
### 4.3 基于块共享的高级解码与零拷贝优化

- 4.3.1 并行采样（Parallel Sampling, `n > 1`）：多个输出序列共享同一份 Prompt 物理 KV 块与引用计数（Reference Counting） <a id="s01-4-3-1"></a> [WAITING]
- 4.3.2 写时复制（Copy-on-Write, CoW）：当共享最后一个未满物理块的多个分支各自生成新 Token 时的块分裂机制 <a id="s01-4-3-2"></a> [WAITING]
- 4.3.3 束搜索（Beam Search）中的动态块共享与淘汰分支物理块的即时回收 <a id="s01-4-3-3"></a> [WAITING]
- 4.3.4 vLLM V1 架构演进：极简主循环重构、零开销前缀缓存与 CPU 调度开销的极致剥离 <a id="s01-4-3-4"></a> [WAITING]

<a id="s01-5"></a>
## 5 前缀复用与结构化生成 —— SGLang 与 RadixAttention

<a id="s01-5-1"></a>
### 5.1 复杂大模型程序（LLM Programs）的计算冗余

- 5.1.1 单次问答之外的真实负载：多轮对话历史、System Prompt、Few-Shot 示例与 RAG 文档复用 <a id="s01-5-1-1"></a> [WAITING]
- 5.1.2 Agent 树状推理搜索（Tree-of-Thoughts）、多步工作流与结构化 API 调用的拓扑特征 <a id="s01-5-1-2"></a> [WAITING]
- 5.1.3 传统引擎在跨请求间丢失 KV Cache 导致的重复 Prefill 算力浪费 <a id="s01-5-1-3"></a> [WAITING]

<a id="s01-5-2"></a>
### 5.2 RadixAttention：基于基数树的自动 KV 缓存管理

- 5.2.1 基数树（Radix Tree / 压缩前缀树）数据结构：以 Token 序列为边（Edge）、Paged KV 块指针为节点 <a id="s01-5-2-1"></a> [DONE]
- 5.2.2 树节点的动态生命周期：新请求前缀匹配（Prefix Matching）、节点分裂（Splitting）与插入 <a id="s01-5-2-2"></a> [WAITING]
- 5.2.3 基于引用计数与 LRU（最近最少使用）策略的叶子节点级联驱逐（Eviction）机制 <a id="s01-5-2-3"></a> [WAITING]

<a id="s01-5-3"></a>
### 5.3 缓存感知调度器（Cache-Aware Scheduling）

- 5.3.1 先来先服务（FCFS）调度如何导致 Radix Tree 缓存频繁抖动（Cache Thrashing） <a id="s01-5-3-1"></a> [WAITING]
- 5.3.2 最长共享前缀优先（Longest-Shared-Prefix-First）批处理重排算法：最大化当前显存树命中率 <a id="s01-5-3-2"></a> [WAITING]
- 5.3.3 SGLang 前端原语（`gen`, `select`, `fork`）与后端运行时异步流式调度的协同设计 <a id="s01-5-3-3"></a> [WAITING]

<a id="s01-5-4"></a>
### 5.4 极速结构化输出与约束解码（Constrained Decoding）

- 5.4.1 为什么大模型原生输出 JSON 或特定语法容易格式错误：开放词表采样与语法规则的冲突 <a id="s01-5-4-1"></a> [WAITING]
- 5.4.2 有限状态机（FSM）引导解码（Outlines 原理）：将正则表达式或 JSON Schema 编译为状态转移图与 Token 掩码（Logits Mask） <a id="s01-5-4-2"></a> [WAITING]
- 5.4.3 跳跃前向解码（Jump-Forward Decoding）：遇到确定性语法片段（如 `"name": "`）时跳过模型单步 Decode 直接拼接并转为 Prefill <a id="s01-5-4-3"></a> [WAITING]
- 5.4.4 XGrammar 与下推自动机（Pushdown Automaton）：支持上下文无关文法（CFG）与零开销 CPU 掩码并行预计算 <a id="s01-5-4-4"></a> [WAITING]

<a id="s01-6"></a>
## 6 打破自回归枷锁 —— 投机采样（Speculative Decoding）

<a id="s01-6-1"></a>
### 6.1 投机采样核心框架与无损证明

- 6.1.1 核心洞察：利用 Decode 阶段闲置的算力余量，将串行生成转化为并行验证（Draft-then-Verify） <a id="s01-6-1-1"></a> [DONE]
- 6.1.2 大小模型协同范式：轻量草稿模型（Draft Model）自回归连猜 $\gamma$ 步 + 目标大模型（Target Model）单次前向并行打分 <a id="s01-6-1-2"></a> [WAITING]
- 6.1.3 修正拒绝采样（Modified Rejection Sampling）：对比 $p(x)$ 与 $q(x)$ 概率比值，数学证明输出分布与纯目标模型 100% 一致 <a id="s01-6-1-3"></a> [WAITING]

<a id="s01-6-2"></a>
### 6.2 投机采样的性能收益边界分析

- 6.2.1 接受率（Acceptance Rate $\alpha$）、草稿步数 $\gamma$ 与草稿模型相对开销系数 $c$ 的加速比公式推导 <a id="s01-6-2-1"></a> [WAITING]
- 6.2.2 Batch Size 增大时投机采样收益衰减现象：当系统从 Memory-Bound 转向 Compute-Bound 时的算力反噬 <a id="s01-6-2-2"></a> [WAITING]
- 6.2.3 动态草稿长度调整（Dynamic Speculation Length）与 KV Cache 回滚（Rollback）机制 <a id="s01-6-2-3"></a> [DONE]

<a id="s01-6-3"></a>
### 6.3 无独立小模型的自投机变体与树状验证

- 6.3.1 Prompt Lookup Decoding（PLD / N-gram 匹配）：直接从输入上下文中检索高频词组作为草稿（极适合代码修改与文档摘要） <a id="s01-6-3-1"></a> [WAITING]
- 6.3.2 Medusa（美杜莎架构）：在目标模型最后一层附加多个并行解码头（Decoding Heads）同时预测未来多个位置 <a id="s01-6-3-2"></a> [WAITING]
- 6.3.3 EAGLE（Extrapolation Algorithm for Greater Language-model Efficiency）：在倒数第二层特征向量（Feature Level）上进行超轻量自回归预测 <a id="s01-6-3-3"></a> [WAITING]
- 6.3.4 树状注意力验证（Tree Attention）：构造多分支候选 Token 树与定制化 Tree Mask 单次并行验证 <a id="s01-6-3-4"></a> [WAITING]

<a id="s01-7"></a>
## 7 模型量化技术（Quantization）全解

<a id="s01-7-1"></a>
### 7.1 神经网络数值表示与量化数学基础

- 7.1.1 浮点格式解剖：FP32、FP16、BF16（动态范围优势）与 FP8（E4M3 与 E5M2 适用场景） <a id="s01-7-1-1"></a> [WAITING]
- 7.1.2 整型均匀量化：对称量化（Symmetric）与非对称量化（Asymmetric）、Scale 与 Zero-Point 计算 <a id="s01-7-1-2"></a> [WAITING]
- 7.1.3 量化粒度对比：Per-Tensor、Per-Channel（Per-Token）与 Group-wise（分组量化，如 Group=128） <a id="s01-7-1-3"></a> [DONE]

<a id="s01-7-2"></a>
### 7.2 仅权重量化（Weight-Only Quantization, W4A16/W8A16）

- 7.2.1 为什么 Decode 阶段仅量化权重（W4A16）就能获得显著加速：减少 HBM 权重搬运量 <a id="s01-7-2-1"></a> [WAITING]
- 7.2.2 GPTQ 算法：基于近似二阶海森矩阵（Hessian Matrix）的逐列误差补偿机制 <a id="s01-7-2-2"></a> [DONE]
- 7.2.3 AWQ（Activation-aware Weight Quantization）：观察激活值分布、保护 1% 显著权重的等效缩放策略 <a id="s01-7-2-3"></a> [WAITING]
- 7.2.4 Marlin 等高性能 W4A16 混合精度 GEMM 内核的在线反量化（Dequantization）流水线 <a id="s01-7-2-4"></a> [WAITING]

<a id="s01-7-3"></a>
### 7.3 权重与激活双量化（W8A8）

- 7.3.1 大模型激活值异常值（Outliers）现象：为什么直接 INT8 量化激活会导致精度崩溃 <a id="s01-7-3-1"></a> [WAITING]
- 7.3.2 SmoothQuant 核心思想：通过数学等价变换将激活层的量化难度转移至权重层 <a id="s01-7-3-2"></a> [WAITING]
- 7.3.3 Hopper 架构原生 FP8 W8A8 量化：动态缩放因子（Dynamic Scaling）与 Tensor Core 硬件直通 <a id="s01-7-3-3"></a> [WAITING]

<a id="s01-7-4"></a>
### 7.4 KV Cache 量化

- 7.4.1 Key 异常值分布规律（Channel 维度异常）与 Value 分布规律（Token 维度平滑） <a id="s01-7-4-1"></a> [WAITING]
- 7.4.2 KIVI 等非对称 KV 量化方案：Per-Channel Key 量化与 Per-Token Value 量化 <a id="s01-7-4-2"></a> [WAITING]
- 7.4.3 vLLM / SGLang 中的 FP8 KV Cache 实践：显存减半收益与 Attention 内核内联反量化开销 <a id="s01-7-4-3"></a> [WAITING]

<a id="s01-8"></a>
## 8 边缘端与异构推理引擎：llama.cpp 与 GGML 深度解析

<a id="s01-8-1"></a>
### 8.1 GGML 张量库架构设计

- 8.1.1 极简 C/C++ 无依赖设计与静态内存池（Static Memory Arena）：推理全程零动态 `malloc` <a id="s01-8-1-1"></a> [WAITING]
- 8.1.2 `ggml_tensor` 数据结构剖析：维度数组、步长（Strides）表示与操作数指针链 <a id="s01-8-1-2"></a> [WAITING]
- 8.1.3 两阶段执行引擎：`ggml_cgraph` 静态计算图的拓扑构建与多线程工作窃取（Work-Stealing）执行 <a id="s01-8-1-3"></a> [WAITING]

<a id="s01-8-2"></a>
### 8.2 GGUF 模型格式与 K-Quants 量化体系

- 8.2.1 GGUF 二进制文件布局：文件头（Header）、元数据键值对（Metadata KV）与内存对齐的张量数据区 <a id="s01-8-2-1"></a> [WAITING]
- 8.2.2 `mmap`（内存映射）零拷贝极速加载模型权重的操作系统底层机制 <a id="s01-8-2-2"></a> [WAITING]
- 8.2.3 K-Quants（如 `Q4_K_M`, `Q5_K_S`）双重缩放结构：Super-block 与 Sub-block 的多级 Scale 压缩 <a id="s01-8-2-3"></a> [WAITING]
- 8.2.4 重要性矩阵（Importance Matrix, `imatrix`）：校准数据引导下的极低比特（2-bit / IQ 系列）量化保护 <a id="s01-8-2-4"></a> [WAITING]

<a id="s01-8-3"></a>
### 8.3 跨平台异构计算与层卸载（Layer Offloading）

- 8.3.1 CPU 端极致优化：AVX2 / AVX-512 / ARM NEON 向量内联汇编（Intrinsics）实现量化点积 <a id="s01-8-3-1"></a> [WAITING]
- 8.3.2 Apple Silicon 统一内存架构（Unified Memory）优势与 Metal 着色器（Compute Shaders）加速 <a id="s01-8-3-2"></a> [WAITING]
- 8.3.3 CPU + GPU 混合推理（`-ngl` 参数）：按层切分模型权重与 PCIe 跨设备激活值传输开销分析 <a id="s01-8-3-3"></a> [WAITING]

<a id="s01-9"></a>
## 9 大规模分布式并行推理架构

<a id="s01-9-1"></a>
### 9.1 张量并行（Tensor Parallelism, TP）

- 9.1.1 Megatron-LM 切分范式：为什么 FFN 第一个线性层按列切分（Column Parallel），第二个按行切分（Row Parallel） <a id="s01-9-1-1"></a> [DONE]
- 9.1.2 Attention 层的张量并行：按注意力头（Attention Heads）均匀切分到不同 GPU，实现局部无通信计算 <a id="s01-9-1-2"></a> [DONE]
- 9.1.3 集合通信原语开销：每层两次 `All-Reduce`（或 `Reduce-Scatter` + `All-Gather`）对 NVLink 带宽的极高要求与跨机 TP 性能悬崖 <a id="s01-9-1-3"></a> [DONE]

<a id="s01-9-2"></a>
### 9.2 流水线并行（Pipeline Parallelism, PP）

- 9.2.1 按模型层（Layers）纵向切分：为什么跨节点（Inter-node）低带宽网络环境下 PP 优于 TP <a id="s01-9-2-1"></a> [WAITING]
- 9.2.2 点对点通信（P2P `Send`/`Recv`）：仅传输层间微小的隐藏状态张量（Hidden States） <a id="s01-9-2-2"></a> [WAITING]
- 9.2.3 流水线气泡（Pipeline Bubbles）消除：微批次切分（Micro-batching）与连续批处理下的异步流水线交错调度 <a id="s01-9-2-3"></a> [WAITING]

<a id="s01-9-3"></a>
### 9.3 上下文并行（Context Parallelism, CP）与 Ring Attention

- 9.3.1 百万级超长上下文的痛点：单卡无法容纳单个请求的完整 KV Cache 与中间激活值 <a id="s01-9-3-1"></a> [DONE]
- 9.3.2 Ring Attention 环形拓扑：将序列沿长度维度切分，各卡计算局部 Q，同时在环状网络中流式传递 K/V 块 <a id="s01-9-3-2"></a> [WAITING]
- 9.3.3 因果掩码下的负载均衡：Striped Attention（交错切分）或 ZigZag 切分解决下三角矩阵导致的各卡计算量不均问题 <a id="s01-9-3-3"></a> [WAITING]

<a id="s01-9-4"></a>
### 9.4 专家并行（Expert Parallelism, EP）

- 9.4.1 MoE 模型的天然切分维度：将不同专家权重分布在独立 GPU 上，Attention 层保持 TP 或数据并行（DP） <a id="s01-9-4-1"></a> [WAITING]
- 9.4.2 两次 `All-to-All` 集合通信：Token 按路由结果分发（Dispatch）至目标专家卡，计算后再收集（Combine）回原卡 <a id="s01-9-4-2"></a> [WAITING]
- 9.4.3 DeepSeek EP 通信优化：节点内 NVLink 与节点间 InfiniBand RDMA 的分层转发、计算与通信双微批次重叠（Dual-Batch Overlap） <a id="s01-9-4-3"></a> [DONE]

<a id="s01-10"></a>
## 10 下一代生产级推理集群架构与服务治理

<a id="s01-10-1"></a>
### 10.1 Prefill-Decode 分离架构（PD Disaggregation）

- 10.1.1 同构混部（Colocated）的根本矛盾：Prefill 追求高算力大吞吐、Decode 追求高带宽低延迟，二者互相干扰且硬件配比需求迥异 <a id="s01-10-1-1"></a> [WAITING]
- 10.1.2 PD 物理隔离架构（Splitwise / DistServe / Mooncake）：独立部署计算型 Prefill 节点池与访存型 Decode 节点池，分别配置最优 TP/PP 策略 <a id="s01-10-1-2"></a> [DONE]
- 10.1.3 跨节点 KV Cache 极速传输：基于 GPUDirect RDMA 或 NVLink 将 Prefill 产出的 KV 块零拷贝推送至 Decode 节点（Layer-by-Layer 边算边传） <a id="s01-10-1-3"></a> [DONE]

<a id="s01-10-2"></a>
### 10.2 分布式 KV Cache 存储池与智能路由

- 10.2.1 多级缓存池化（如 Mooncake / LMCache）：串联 GPU HBM、主机 CPU DRAM 与本地 NVMe SSD / 远端分布式内存池 <a id="s01-10-2-1"></a> [DONE]
- 10.2.2 全局缓存感知负载均衡器（Global Cache-Aware Router）：网关层维护全局 Radix Tree 视图，将请求精准路由至持有最长公共前缀 KV 的实例 <a id="s01-10-2-2"></a> [WAITING]
- 10.2.3 P/D 实例比例动态弹性缩放：应对突发长文本洪峰或长输出流量的自适应重配置 <a id="s01-10-2-3"></a> [WAITING]

<a id="s01-10-3"></a>
### 10.3 多租户 LoRA 服务与生产工程闭环

- 10.3.1 高并发多 LoRA 动态服务（Punica / S-LoRA）：共享基础模型（Base Model）权重，使用 Segmented Gather-Matrix-Vector Multiplication (SGMV) 内核在同一 Batch 中并行计算不同请求的 LoRA 分支 <a id="s01-10-3-1"></a> [WAITING]
- 10.3.2 OpenAI 兼容 API 服务层：流式输出（Server-Sent Events, SSE）、异步引擎封装（AsyncLLMEngine）与 Tokenizer 独立进程池卸载 <a id="s01-10-3-2"></a> [DONE]
- 10.3.3 推理压测与可观测性体系：基于真实数据集（ShareGPT）构建负载生成器、Prometheus 核心指标监控（KV Cache 使用率、排队长度、TTFT/TPOT 分位数）与算力成本核算（USD/1M Tokens） <a id="s01-10-3-3"></a> [WAITING]

## 学习出口

能读懂 vLLM/SGLang 的核心模块，能解释 PagedAttention、连续批处理、投机采样、量化和分布式推理的收益与代价。

## 导航

[返回分类目录](../README.md) · [知识总目录](../../../README.md)
