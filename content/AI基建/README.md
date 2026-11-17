# AI 基建知识体系

> 状态：`[WAITING]` 待处理 · `[PROCESSING]` 已认领 · `[DONE]` 已验收 · `[ABORT]` 无合适素材。规则见仓库根 `AGENTS.md`。

## 第 1 章：Transformer 解码器（Decoder-Only）核心解剖

### 1.1 自回归生成（Autoregressive Generation）机制

- 1.1.1 条件概率链式法则与 Next-Token Prediction 数学表达 [DONE]
- 1.1.2 因果掩码（Causal Mask）的下三角矩阵构造与防穿越原理 [DONE]
- 1.1.3 输出层 Logits 计算、温度缩放（Temperature）与 Softmax 归一化 [DONE]
- 1.1.4 解码采样策略：Greedy Search、Top-K、Top-P（Nucleus）与重复惩罚（Repetition Penalty） [DONE]

### 1.2 分词器（Tokenizer）与词嵌入（Embedding）

- 1.2.1 Byte-level BPE（字节级字节对编码）算法与 Tiktoken 实现机制 [DONE]
- 1.2.2 词表大小（Vocabulary Size）对 Embedding 层显存及 LM Head 计算量的影响 [DONE]
- 1.2.3 Special Tokens（BOS, EOS, PAD, Chat Template 控制符）的状态机控制逻辑 [PROCESSING]

### 1.3 归一化层演进：从 LayerNorm 到 RMSNorm

- 1.3.1 Post-Norm 与 Pre-Norm 的梯度流差异及深层网络训练稳定性 [PROCESSING]
- 1.3.2 RMSNorm（均方根归一化）省去均值中心化的数学简化与加速收益 [WAITING]
- 1.3.3 残差连接（Residual Connection）与归一化算子的访存融合优化 [WAITING]

### 1.4 前馈神经网络（FFN）与激活函数升级

- 1.4.1 激活函数演进：ReLU、GELU 到 Swish（SiLU）的平滑性与门控特性 [WAITING]
- 1.4.2 SwiGLU 结构拆解：Gate Proj、Up Proj 与 Down Proj 三个线性层的矩阵变换 [WAITING]
- 1.4.3 隐藏层维度缩放：为什么 SwiGLU 的中间层维度通常设定为 $\frac{8}{3}d$ 并向硬件对齐 [WAITING]

## 第 2 章：注意力机制（Attention）与位置编码的工程优化

### 2.1 标准多头注意力（MHA）的计算与显存剖析

- 2.1.1 Q、K、V 线性投影与多头切分（Head Splitting）的张量重排（Transpose/Reshape） [WAITING]
- 2.1.2 缩放点积注意力（Scaled Dot-Product Attention）中 $\sqrt{d_k}$ 防止 Softmax 饱和的数学原理 [WAITING]
- 2.1.3 序列长度 $N^2$ 复杂度在长文本推理下的显存爆炸与计算瓶颈 [WAITING]

### 2.2 键值缓存压缩：MQA 与 GQA

- 2.2.1 多查询注意力（MQA）：所有 Query 头共享单组 K/V 头的带宽节省与精度折衷 [WAITING]
- 2.2.2 分组查询注意力（GQA）：Llama-2/3 中 Group 数量的选择与张量广播（Broadcast）实现 [WAITING]
- 2.2.3 MHA、MQA 与 GQA 在推理阶段的 KV Cache 体积对比与访存带宽测算 [WAITING]

### 2.3 旋转位置编码（RoPE）

- 2.3.1 绝对位置编码与相对位置编码的局限性 [WAITING]
- 2.3.2 RoPE 复数空间推导：通过二维平面旋转矩阵注入相对位置信息 [WAITING]
- 2.3.3 RoPE 的远程衰减特性（Long-term Decay）与旋转频率基数（Base $\theta$）的作用 [WAITING]
- 2.3.4 RoPE 算子实现：实数域逐元素乘加（Element-wise）与预计算 Cos/Sin 缓存表 [WAITING]

### 2.4 长上下文外推与上下文窗口扩展

- 2.4.1 位置线性内插（Position Interpolation, PI）的原理与高频信息丢失问题 [WAITING]
- 2.4.2 神经正切核感知缩放（NTK-Aware Scaling）与动态 NTK（Dynamic NTK） [WAITING]
- 2.4.3 YaRN（Yet another RoPE extensioN）：分频段缩放（高频不插值、低频内插）与注意力温度补偿 [PROCESSING]

## 第 3 章：主流开源模型架构变体（Llama 之后的世界）

### 3.1 稠密模型（Dense）标杆演进

- 3.1.1 Llama 1 到 Llama 3 的架构参数变迁：词表扩充、GQA 普及与 RoPE 基数调整 [PROCESSING]
- 3.1.2 Qwen 与 Mistral 系列的局部微调：QKV Bias 取舍、Embedding 权重绑定（Tied Weights） [WAITING]
- 3.1.3 权重张量命名规范：HuggingFace Safetensors 格式与模型结构映射 [WAITING]

### 3.2 混合专家模型（MoE）推理架构

- 3.2.1 稀疏激活原理：门控路由网络（Gating Network / Router）的 Top-K Softmax 选择机制 [WAITING]
- 3.2.2 粗粒度专家（如 Mixtral 8x7B）与细粒度 + 共享专家架构（如 DeepSeek-MoE） [WAITING]
- 3.2.3 MoE 推理的特殊困境：总参数量巨大导致的显存容量压力与单次激活稀疏导致的访存碎片化 [WAITING]

### 3.3 新兴高效注意力变体

- 3.3.1 滑动窗口注意力（Sliding Window Attention, SWA）与滚动缓存（Rolling Buffer KV Cache） [WAITING]
- 3.3.2 多头潜在注意力（Multi-head Latent Attention, MLA）：低秩键值联合压缩（Low-Rank KV Compression） [WAITING]
- 3.3.3 MLA 中的矩阵吸收技巧（Matrix Absorption）：如何在推理时避免解压 KV Cache 直接计算 [WAITING]

## 第 4 章：LLM 推理的两阶段动力学与 KV Cache

### 4.1 预填充阶段（Prefill Phase）剖析

- 4.1.1 Prompt 并行处理特征：通用矩阵乘法（GEMM）主导的计算模式 [WAITING]
- 4.1.2 算子耗时分布：为什么 Prefill 阶段是典型的 Compute-Bound（计算受限） [WAITING]
- 4.1.3 超长 Prompt 下的显存峰值管理与中间激活值（Activations）开销 [WAITING]

### 4.2 解码阶段（Decode Phase）剖析

- 4.2.1 逐 Token 自回归特征：矩阵-向量乘法（GEMV）主导的计算模式 [WAITING]
- 4.2.2 权重重复搬运困境：生成单个 Token 需遍历全量模型权重导致的 Memory-Bound（访存受限） [WAITING]
- 4.2.3 GPU 计算单元闲置率分析与提高 Batch Size 转向 GEMM 的必要性 [WAITING]

### 4.3 键值缓存（KV Cache）深度精算

- 4.3.1 空间换时间：缓存历史 Token 的 K/V 张量如何将单步计算复杂度从 $O(N^2)$ 降至 $O(N)$ [WAITING]
- 4.3.2 KV Cache 显存占用精确公式推导（含层数、头数、头维度、精度、Batch 与序列长度） [WAITING]
- 4.3.3 模型权重、KV Cache 与运行时激活值（Activation）三者的显存占比动态变化规律 [WAITING]

## 第 5 章：GPU 硬件架构与算术强度（Roofline Model）

### 5.1 现代 GPU 存储层次结构（Memory Hierarchy）

- 5.1.1 高带宽显存（HBM）：容量优势、带宽演进（A100 vs H100）与高访问延迟 [WAITING]
- 5.1.2 片上高速缓存：L2 Cache 的全局共享机制与 L1 Cache / Shared Memory（SRAM）的程序员可控性 [WAITING]
- 5.1.3 寄存器文件（Register File）：最顶层存储与 Warp 级数据驻留限制 [WAITING]

### 5.2 GPU 计算单元与执行模型

- 5.2.1 流多处理器（SM）内部构造：CUDA Core（标量/向量运算）与 Tensor Core（矩阵乘加 MMA） [WAITING]
- 5.2.2 SIMT（单指令多线程）架构：Thread、Warp（32线程）、Block 与 Grid 的调度层级 [WAITING]
- 5.2.3 内存合并访问（Memory Coalescing）与 Shared Memory 常见 Bank Conflict 规避 [WAITING]

### 5.3 Roofline 性能模型实战

- 5.3.1 算术强度（Arithmetic Intensity, FLOPs/Byte）的定义与物理意义 [WAITING]
- 5.3.2 硬件屋顶线绘制：峰值算力（Peak TFLOPS）与峰值带宽（Peak GB/s）交汇的拐点计算 [WAITING]
- 5.3.3 线性层（Linear）与注意力层（Attention）在不同 Batch Size 和序列长度下的 Roofline 落点推导 [WAITING]

## 第 6 章：推理系统的核心性能指标与权衡（Trade-offs）

### 6.1 延迟（Latency）度量体系

- 6.1.1 首字延迟（TTFT, Time To First Token）：决定用户感知响应快慢的 Prefill 指标 [WAITING]
- 6.1.2 单 Token 生成延迟（TPOT, Time Per Output Token / ITL）：决定阅读流畅度的 Decode 指标 [WAITING]
- 6.1.3 端到端请求延迟（End-to-End Latency）：排队时间 + TTFT + TPOT × 生成长度 [WAITING]

### 6.2 吞吐量（Throughput）与服务质量（SLO）

- 6.2.1 系统吞吐量维度：每秒请求数（QPS/RPS）、每秒输入 Token 数与每秒输出 Token 数 [WAITING]
- 6.2.2 有效吞吐量（Goodput）：满足特定 TTFT 与 TPOT 服务等级目标（SLO）前提下的最大吞吐 [WAITING]
- 6.2.3 尾部延迟（P90 / P99 Latency）抖动成因与长尾请求治理 [WAITING]

### 6.3 延迟与吞吐量的帕累托前沿（Pareto Frontier）

- 6.3.1 Batch Size 增大如何提升 Tensor Core 利用率但同时拉长单步 TPOT [WAITING]
- 6.3.2 显存容量墙对最大并发 Batch Size 的硬性约束 [WAITING]
- 6.3.3 实时交互场景（低延迟优先）与离线批处理场景（高吞吐优先）的参数配置策略 [WAITING]

## 第 7 章：模型量化技术（Quantization）全解

### 7.1 神经网络数值表示与量化数学基础

- 7.1.1 浮点格式解剖：FP32、FP16、BF16（动态范围优势）与 FP8（E4M3 与 E5M2 适用场景） [WAITING]
- 7.1.2 整型均匀量化：对称量化（Symmetric）与非对称量化（Asymmetric）、Scale 与 Zero-Point 计算 [WAITING]
- 7.1.3 量化粒度对比：Per-Tensor、Per-Channel（Per-Token）与 Group-wise（分组量化，如 Group=128） [WAITING]

### 7.2 仅权重量化（Weight-Only Quantization, W4A16/W8A16）

- 7.2.1 为什么 Decode 阶段仅量化权重（W4A16）就能获得显著加速：减少 HBM 权重搬运量 [WAITING]
- 7.2.2 GPTQ 算法：基于近似二阶海森矩阵（Hessian Matrix）的逐列误差补偿机制 [WAITING]
- 7.2.3 AWQ（Activation-aware Weight Quantization）：观察激活值分布、保护 1% 显著权重的等效缩放策略 [WAITING]
- 7.2.4 Marlin 等高性能 W4A16 混合精度 GEMM 内核的在线反量化（Dequantization）流水线 [WAITING]

### 7.3 权重与激活双量化（W8A8）

- 7.3.1 大模型激活值异常值（Outliers）现象：为什么直接 INT8 量化激活会导致精度崩溃 [WAITING]
- 7.3.2 SmoothQuant 核心思想：通过数学等价变换将激活层的量化难度转移至权重层 [WAITING]
- 7.3.3 Hopper 架构原生 FP8 W8A8 量化：动态缩放因子（Dynamic Scaling）与 Tensor Core 硬件直通 [WAITING]

### 7.4 KV Cache 量化

- 7.4.1 Key 异常值分布规律（Channel 维度异常）与 Value 分布规律（Token 维度平滑） [WAITING]
- 7.4.2 KIVI 等非对称 KV 量化方案：Per-Channel Key 量化与 Per-Token Value 量化 [WAITING]
- 7.4.3 vLLM / SGLang 中的 FP8 KV Cache 实践：显存减半收益与 Attention 内核内联反量化开销 [WAITING]

## 第 8 章：注意力与核心算子级加速（Kernel Optimization）

### 8.1 FlashAttention 系列算法演进

- 8.1.1 标准 Attention 的 HBM 读写灾难：$N \times N$ 注意力矩阵的反复物化（Materialization） [WAITING]
- 8.1.2 在线 Softmax（Online Softmax / Safe Softmax）：局部最大值递推更新与单次遍历求和 [WAITING]
- 8.1.3 FlashAttention-1：基于 SRAM 分块（Tiling）的融合计算与重计算（Recomputation）原理 [WAITING]
- 8.1.4 FlashAttention-2：调整内外循环顺序（外层循环 Q、内层循环 K/V）与 Warp 级工作切分优化 [WAITING]
- 8.1.5 FlashAttention-3：利用 H100 TMA（张量内存加速器）异步拷贝与 WGMMA 指令实现计算通信重叠 [WAITING]

### 8.2 解码阶段专用注意力内核：FlashDecoding 与 FlashInfer

- 8.2.1 FlashAttention 在 Decode 阶段的短板：Query 长度为 1 导致 SM 线程块并行度严重不足 [WAITING]
- 8.2.2 FlashDecoding（Split-K 思想）：沿 KV 序列长度维度切分并行计算，最后归约（Reduction）局部 Softmax 结果 [WAITING]
- 8.2.3 FlashInfer 架构：统一块稀疏（Block-Sparse）存储格式、负载平衡调度与 JIT 编译优化 [WAITING]

### 8.3 算子融合（Operator Fusion）与 CUDA Graph

- 8.3.1 常见算子融合模式：QKV 投影合并、RoPE + Attention 融合、Add + RMSNorm 融合、Gate + Up 投影融合 [WAITING]
- 8.3.2 Python 解释器与 CUDA Kernel Launch Overhead（内核启动开销）在 Decode 阶段的性能占比 [WAITING]
- 8.3.3 CUDA Graph 原理与局限：录制静态计算图一次性下发、动态 Shape 补齐（Padding）与显存池绑定 [WAITING]

## 第 9 章：边缘端与异构推理引擎：llama.cpp 与 GGML 深度解析

### 9.1 GGML 张量库架构设计

- 9.1.1 极简 C/C++ 无依赖设计与静态内存池（Static Memory Arena）：推理全程零动态 `malloc` [WAITING]
- 9.1.2 `ggml_tensor` 数据结构剖析：维度数组、步长（Strides）表示与操作数指针链 [WAITING]
- 9.1.3 两阶段执行引擎：`ggml_cgraph` 静态计算图的拓扑构建与多线程工作窃取（Work-Stealing）执行 [WAITING]

### 9.2 GGUF 模型格式与 K-Quants 量化体系

- 9.2.1 GGUF 二进制文件布局：文件头（Header）、元数据键值对（Metadata KV）与内存对齐的张量数据区 [WAITING]
- 9.2.2 `mmap`（内存映射）零拷贝极速加载模型权重的操作系统底层机制 [WAITING]
- 9.2.3 K-Quants（如 `Q4_K_M`, `Q5_K_S`）双重缩放结构：Super-block 与 Sub-block 的多级 Scale 压缩 [WAITING]
- 9.2.4 重要性矩阵（Importance Matrix, `imatrix`）：校准数据引导下的极低比特（2-bit / IQ 系列）量化保护 [WAITING]

### 9.3 跨平台异构计算与层卸载（Layer Offloading）

- 9.3.1 CPU 端极致优化：AVX2 / AVX-512 / ARM NEON 向量内联汇编（Intrinsics）实现量化点积 [WAITING]
- 9.3.2 Apple Silicon 统一内存架构（Unified Memory）优势与 Metal 着色器（Compute Shaders）加速 [WAITING]
- 9.3.3 CPU + GPU 混合推理（`-ngl` 参数）：按层切分模型权重与 PCIe 跨设备激活值传输开销分析 [WAITING]

## 第 10 章：动态调度与连续批处理（Continuous Batching）

### 10.1 从静态批处理到迭代级调度

- 10.1.1 静态批处理（Static Batching）的木桶效应：短请求等待长请求生成完毕造成的 GPU 算力空泡（Bubble） [WAITING]
- 10.1.2 Orca 迭代级调度（Iteration-Level Scheduling）：以单个 Token 生成步（Step）为粒度的队列状态更新 [WAITING]
- 10.1.3 异构长度混合执行：Attention 层按请求独立寻址与 Linear 层拼接（Concatenate）为大张量统一计算 [WAITING]

### 10.2 Prefill 与 Decode 的调度博弈与分块预填充（Chunked Prefill）

- 10.2.1 传统 Prefill 优先策略（如 vLLM V0）的问题：新进入的长 Prompt 阻塞正在进行的 Decode 导致 TPOT 剧烈抖动 [WAITING]
- 10.2.2 Sarathi / Chunked Prefill 核心机制：将长 Prompt 切分为固定大小的 Token 块（Chunks） [WAITING]
- 10.2.3 混合批次（Hybrid Batching / Piggybacking）：在单次迭代中将 Prefill 块与存量 Decode Token 打包同算，借 Decode 搭车利用计算余量 [WAITING]

### 10.3 显存过载与抢占恢复机制（Preemption）

- 10.3.1 动态生成长度不可预知性引发的显存耗尽（OOM）风险与 FCFS（先来先服务）淘汰原则 [WAITING]
- 10.3.2 交换策略（Swapping）：将被害请求的物理 KV 块通过 PCIe 异步拷贝至 CPU 内存（Pinned Memory） [WAITING]
- 10.3.3 重计算策略（Recomputation）：直接丢弃 KV Cache，待显存充裕时拼接已生成 Token 重新 Prefill（何时重计算比 Swap 更快） [WAITING]

## 第 11 章：显存管理革命 —— vLLM 与 PagedAttention

### 11.1 传统连续显存分配的三大碎片顽疾

- 11.1.1 预留浪费（Reservation Waste）：按模型最大上下文长度预分配连续显存槽位 [WAITING]
- 11.1.2 内部碎片（Internal Fragmentation）：实际生成长度远小于预分配长度导致的闲置空间 [WAITING]
- 11.1.3 外部碎片（External Fragmentation）：不同长度请求频繁申请释放导致的非连续显存空洞 [WAITING]

### 11.2 PagedAttention 虚拟内存映射架构

- 11.2.1 操作系统分页启发：将连续的逻辑 KV Cache 切分为固定大小（如 16 或 32 Tokens）的逻辑块（Logical Blocks） [WAITING]
- 11.2.2 物理块池（Physical Block Pool）与块表（Block Table）：按需动态分配非连续显存与地址转换 [WAITING]
- 11.2.3 PagedAttention CUDA 内核改造：在 Attention 计算循环中通过 Block Table 指针跳转（Gather）读取非连续 KV 块 [WAITING]

### 11.3 基于块共享的高级解码与零拷贝优化

- 11.3.1 并行采样（Parallel Sampling, `n > 1`）：多个输出序列共享同一份 Prompt 物理 KV 块与引用计数（Reference Counting） [WAITING]
- 11.3.2 写时复制（Copy-on-Write, CoW）：当共享最后一个未满物理块的多个分支各自生成新 Token 时的块分裂机制 [WAITING]
- 11.3.3 束搜索（Beam Search）中的动态块共享与淘汰分支物理块的即时回收 [WAITING]
- 11.3.4 vLLM V1 架构演进：极简主循环重构、零开销前缀缓存与 CPU 调度开销的极致剥离 [WAITING]

## 第 12 章：前缀复用与结构化生成 —— SGLang 与 RadixAttention

### 12.1 复杂大模型程序（LLM Programs）的计算冗余

- 12.1.1 单次问答之外的真实负载：多轮对话历史、System Prompt、Few-Shot 示例与 RAG 文档复用 [WAITING]
- 12.1.2 Agent 树状推理搜索（Tree-of-Thoughts）、多步工作流与结构化 API 调用的拓扑特征 [WAITING]
- 12.1.3 传统引擎在跨请求间丢失 KV Cache 导致的重复 Prefill 算力浪费 [WAITING]

### 12.2 RadixAttention：基于基数树的自动 KV 缓存管理

- 12.2.1 基数树（Radix Tree / 压缩前缀树）数据结构：以 Token 序列为边（Edge）、Paged KV 块指针为节点 [WAITING]
- 12.2.2 树节点的动态生命周期：新请求前缀匹配（Prefix Matching）、节点分裂（Splitting）与插入 [WAITING]
- 12.2.3 基于引用计数与 LRU（最近最少使用）策略的叶子节点级联驱逐（Eviction）机制 [WAITING]

### 12.3 缓存感知调度器（Cache-Aware Scheduling）

- 12.3.1 先来先服务（FCFS）调度如何导致 Radix Tree 缓存频繁抖动（Cache Thrashing） [WAITING]
- 12.3.2 最长共享前缀优先（Longest-Shared-Prefix-First）批处理重排算法：最大化当前显存树命中率 [WAITING]
- 12.3.3 SGLang 前端原语（`gen`, `select`, `fork`）与后端运行时异步流式调度的协同设计 [WAITING]

### 12.4 极速结构化输出与约束解码（Constrained Decoding）

- 12.4.1 为什么大模型原生输出 JSON 或特定语法容易格式错误：开放词表采样与语法规则的冲突 [WAITING]
- 12.4.2 有限状态机（FSM）引导解码（Outlines 原理）：将正则表达式或 JSON Schema 编译为状态转移图与 Token 掩码（Logits Mask） [WAITING]
- 12.4.3 跳跃前向解码（Jump-Forward Decoding）：遇到确定性语法片段（如 `"name": "`）时跳过模型单步 Decode 直接拼接并转为 Prefill [WAITING]
- 12.4.4 XGrammar 与下推自动机（Pushdown Automaton）：支持上下文无关文法（CFG）与零开销 CPU 掩码并行预计算 [WAITING]

## 第 13 章：打破自回归枷锁 —— 投机采样（Speculative Decoding）

### 13.1 投机采样核心框架与无损证明

- 13.1.1 核心洞察：利用 Decode 阶段闲置的算力余量，将串行生成转化为并行验证（Draft-then-Verify） [WAITING]
- 13.1.2 大小模型协同范式：轻量草稿模型（Draft Model）自回归连猜 $\gamma$ 步 + 目标大模型（Target Model）单次前向并行打分 [WAITING]
- 13.1.3 修正拒绝采样（Modified Rejection Sampling）：对比 $p(x)$ 与 $q(x)$ 概率比值，数学证明输出分布与纯目标模型 100% 一致 [WAITING]

### 13.2 投机采样的性能收益边界分析

- 13.2.1 接受率（Acceptance Rate $\alpha$）、草稿步数 $\gamma$ 与草稿模型相对开销系数 $c$ 的加速比公式推导 [WAITING]
- 13.2.2 Batch Size 增大时投机采样收益衰减现象：当系统从 Memory-Bound 转向 Compute-Bound 时的算力反噬 [WAITING]
- 13.2.3 动态草稿长度调整（Dynamic Speculation Length）与 KV Cache 回滚（Rollback）机制 [WAITING]

### 13.3 无独立小模型的自投机变体与树状验证

- 13.3.1 Prompt Lookup Decoding（PLD / N-gram 匹配）：直接从输入上下文中检索高频词组作为草稿（极适合代码修改与文档摘要） [WAITING]
- 13.3.2 Medusa（美杜莎架构）：在目标模型最后一层附加多个并行解码头（Decoding Heads）同时预测未来多个位置 [WAITING]
- 13.3.3 EAGLE（Extrapolation Algorithm for Greater Language-model Efficiency）：在倒数第二层特征向量（Feature Level）上进行超轻量自回归预测 [WAITING]
- 13.3.4 树状注意力验证（Tree Attention）：构造多分支候选 Token 树与定制化 Tree Mask 单次并行验证 [WAITING]

## 第 14 章：大规模分布式并行推理架构

### 14.1 张量并行（Tensor Parallelism, TP）

- 14.1.1 Megatron-LM 切分范式：为什么 FFN 第一个线性层按列切分（Column Parallel），第二个按行切分（Row Parallel） [WAITING]
- 14.1.2 Attention 层的张量并行：按注意力头（Attention Heads）均匀切分到不同 GPU，实现局部无通信计算 [WAITING]
- 14.1.3 集合通信原语开销：每层两次 `All-Reduce`（或 `Reduce-Scatter` + `All-Gather`）对 NVLink 带宽的极高要求与跨机 TP 性能悬崖 [WAITING]

### 14.2 流水线并行（Pipeline Parallelism, PP）

- 14.2.1 按模型层（Layers）纵向切分：为什么跨节点（Inter-node）低带宽网络环境下 PP 优于 TP [WAITING]
- 14.2.2 点对点通信（P2P `Send`/`Recv`）：仅传输层间微小的隐藏状态张量（Hidden States） [WAITING]
- 14.2.3 流水线气泡（Pipeline Bubbles）消除：微批次切分（Micro-batching）与连续批处理下的异步流水线交错调度 [WAITING]

### 14.3 上下文并行（Context Parallelism, CP）与 Ring Attention

- 14.3.1 百万级超长上下文的痛点：单卡无法容纳单个请求的完整 KV Cache 与中间激活值 [WAITING]
- 14.3.2 Ring Attention 环形拓扑：将序列沿长度维度切分，各卡计算局部 Q，同时在环状网络中流式传递 K/V 块 [WAITING]
- 14.3.3 因果掩码下的负载均衡：Striped Attention（交错切分）或 ZigZag 切分解决下三角矩阵导致的各卡计算量不均问题 [WAITING]

### 14.4 专家并行（Expert Parallelism, EP）

- 14.4.1 MoE 模型的天然切分维度：将不同专家权重分布在独立 GPU 上，Attention 层保持 TP 或数据并行（DP） [WAITING]
- 14.4.2 两次 `All-to-All` 集合通信：Token 按路由结果分发（Dispatch）至目标专家卡，计算后再收集（Combine）回原卡 [WAITING]
- 14.4.3 DeepSeek EP 通信优化：节点内 NVLink 与节点间 InfiniBand RDMA 的分层转发、计算与通信双微批次重叠（Dual-Batch Overlap） [WAITING]

## 第 15 章：下一代生产级推理集群架构与服务治理

### 15.1 Prefill-Decode 分离架构（PD Disaggregation）

- 15.1.1 同构混部（Colocated）的根本矛盾：Prefill 追求高算力大吞吐、Decode 追求高带宽低延迟，二者互相干扰且硬件配比需求迥异 [WAITING]
- 15.1.2 PD 物理隔离架构（Splitwise / DistServe / Mooncake）：独立部署计算型 Prefill 节点池与访存型 Decode 节点池，分别配置最优 TP/PP 策略 [WAITING]
- 15.1.3 跨节点 KV Cache 极速传输：基于 GPUDirect RDMA 或 NVLink 将 Prefill 产出的 KV 块零拷贝推送至 Decode 节点（Layer-by-Layer 边算边传） [WAITING]

### 15.2 分布式 KV Cache 存储池与智能路由

- 15.2.1 多级缓存池化（如 Mooncake / LMCache）：串联 GPU HBM、主机 CPU DRAM 与本地 NVMe SSD / 远端分布式内存池 [WAITING]
- 15.2.2 全局缓存感知负载均衡器（Global Cache-Aware Router）：网关层维护全局 Radix Tree 视图，将请求精准路由至持有最长公共前缀 KV 的实例 [WAITING]
- 15.2.3 P/D 实例比例动态弹性缩放：应对突发长文本洪峰或长输出流量的自适应重配置 [WAITING]

### 15.3 多租户 LoRA 服务与生产工程闭环

- 15.3.1 高并发多 LoRA 动态服务（Punica / S-LoRA）：共享基础模型（Base Model）权重，使用 Segmented Gather-Matrix-Vector Multiplication (SGMV) 内核在同一 Batch 中并行计算不同请求的 LoRA 分支 [WAITING]
- 15.3.2 OpenAI 兼容 API 服务层：流式输出（Server-Sent Events, SSE）、异步引擎封装（AsyncLLMEngine）与 Tokenizer 独立进程池卸载 [WAITING]
- 15.3.3 推理压测与可观测性体系：基于真实数据集（ShareGPT）构建负载生成器、Prometheus 核心指标监控（KV Cache 使用率、排队长度、TTFT/TPOT 分位数）与算力成本核算（USD/1M Tokens） [WAITING]
