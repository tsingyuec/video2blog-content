# S02 GPU 内核与性能工程

编号：S02 · 类型：系统专题 · 目录规模：36 个小节（三级叶子节点）。

> 本文件是 `content-new` 的完整目录草案。状态统一为 `[WAITING]`，待 Phase 2 映射 video2blog 博客后更新。

## 脉络章程

**知识主线**：先理解 GPU 的存储层次、执行模型与 Roofline，再学 CUDA/Triton 怎么写，接着学 profiling 怎么测，然后以 FlashAttention 为完整案例从零实现一个内核，最后看解码内核、算子融合与编译器如何把“手写优化”变成“系统能力”。

**一句话范围**：只讲单机 GPU 内核的“怎么写、怎么测、怎么优化”；不展开模型结构（归 M02）、推理系统调度与分布式（归 S01）。

**学习入口 → 学习出口**：PyTorch 基础、矩阵乘法与访存直觉（可复用 M01） → 能判断一个算子是算力瓶颈还是访存瓶颈，能写 CUDA/Triton 内核，能读懂 FlashAttention，能用 profiling 定位并优化常见性能问题。

**完整问题链**：
1. GPU 硬件架构与算术强度：为什么同样的 FLOPs，有的算子快、有的慢？
2. CUDA 与 Triton 编程：怎样把计算映射到 thread/block/warp 和 tile 上？
3. 性能剖析：怎样判断瓶颈在算力、访存、同步还是占用率？
4. 案例：从零实现 FlashAttention：怎样用分块、online softmax 和融合消除 N×N 中间矩阵？
5. 解码内核与算子融合：Decode 阶段并行度不足怎么办？多个小算子怎样合并？
6. 编译器与图优化：什么时候该手写内核，什么时候交给 XLA/TorchInductor/TVM？

**与相邻脉络的关系**：上游是 M01 的线性代数与访存直觉、M02 的 Transformer 结构；下游是 S01 的推理系统，S02 提供“内核实现”，S01 决定“何时用、如何调度”。

> 博客已从 `content` 的 GPU / FlashAttention / AI Infra 系列迁入对应小节；暂无合适博客的小节保持 `[WAITING]`。

> 补充：`4.1.1` 已纳入 FlashAttention 访存瓶颈切入点一篇。

## 目录

<a id="s02-1"></a>
## 1 GPU 硬件架构与算术强度（Roofline Model）

<a id="s02-1-1"></a>
### 1.1 现代 GPU 存储层次结构（Memory Hierarchy）

- 1.1.1 高带宽显存（HBM）：容量优势、带宽演进（A100 vs H100）与高访问延迟 <a id="s02-1-1-1"></a> [DONE]
  - 学习目标：说明 HBM 的容量/带宽/延迟取舍，能解释为什么 GPU 需要高带宽显存，不展开显存控制器电路。
- 1.1.2 片上高速缓存：L2 Cache 的全局共享机制与 L1 Cache / Shared Memory（SRAM）的程序员可控性 <a id="s02-1-1-2"></a> [DONE]
  - 学习目标：区分 L2 全局共享与 L1/Shared 程序员可控，说明它们对访存延迟和分块策略的影响。
- 1.1.3 寄存器文件（Register File）：最顶层存储与 Warp 级数据驻留限制 <a id="s02-1-1-3"></a> [DONE]
  - 学习目标：说明寄存器是最高层存储，能解释寄存器压力如何限制 occupancy。

<a id="s02-1-2"></a>
### 1.2 GPU 计算单元与执行模型

- 1.2.1 流多处理器（SM）内部构造：CUDA Core（标量/向量运算）与 Tensor Core（矩阵乘加 MMA） <a id="s02-1-2-1"></a> [DONE]
  - 学习目标：区分 CUDA Core 与 Tensor Core 的分工，说明一个 SM 内有哪些执行单元。
- 1.2.2 SIMT（单指令多线程）架构：Thread、Warp（32 线程）、Block 与 Grid 的调度层级 <a id="s02-1-2-2"></a> [DONE]
  - 学习目标：用 Thread/Warp/Block/Grid 描述 GPU 调度层级，解释 Warp 分歧为什么有代价。
- 1.2.3 内存合并访问（Memory Coalescing）与 Shared Memory 常见 Bank Conflict 规避 <a id="s02-1-2-3"></a> [DONE]
  - 学习目标：判断一次访存是否合并，能给出避免 Bank Conflict 的基本方法。

<a id="s02-1-3"></a>
### 1.3 Roofline 性能模型实战

- 1.3.1 算术强度（Arithmetic Intensity, FLOPs/Byte）的定义与物理意义 <a id="s02-1-3-1"></a> [DONE]
  - 学习目标：定义算术强度，能计算一个算子的 FLOPs/Byte。
- 1.3.2 硬件屋顶线绘制：峰值算力（Peak TFLOPS）与峰值带宽（Peak GB/s）交汇的拐点计算 <a id="s02-1-3-2"></a> [DONE]
  - 学习目标：画出屋顶线，找到算力/带宽拐点，判断算子落在哪一侧。
- 1.3.3 线性层（Linear）与注意力层（Attention）在不同 Batch Size 和序列长度下的 Roofline 落点推导 <a id="s02-1-3-3"></a> [DONE]
  - 学习目标：推导 Linear/Attention 在不同 batch/seq 下的落点，解释 Prefill 与 Decode 的瓶颈差异。

<a id="s02-2"></a>
## 2 CUDA 与 Triton 编程

<a id="s02-2-1"></a>
### 2.1 CUDA 执行模型

- 2.1.1 线程、块、网格与 Warp 调度 <a id="s02-2-1-1"></a> [DONE]
  - 学习目标：能写出一个 CUDA kernel 的 grid/block 配置，说明 threadIdx/blockIdx 的映射。
- 2.1.2 合并访存与共享内存 <a id="s02-2-1-2"></a> [DONE]
  - 学习目标：能用 shared memory 做分块，避免非合并访存。
- 2.1.3 同步、原子操作与流水线 <a id="s02-2-1-3"></a> [DONE]
  - 学习目标：解释 `__syncthreads`、原子操作和流水线的适用场景与代价。

<a id="s02-2-2"></a>
### 2.2 Triton 编程模型

- 2.2.1 Triton 内核与块级编程 <a id="s02-2-2-1"></a> [DONE]
  - 学习目标：能写一个 Triton kernel，理解 program_id、block 与 tile 的概念。
- 2.2.2 自动调优与内核参数 <a id="s02-2-2-2"></a> [DONE]
  - 学习目标：能用 `@triton.autotune` 选择 block size、num_warps 等参数。
- 2.2.3 从 PyTorch 到 Triton 的改写 <a id="s02-2-2-3"></a> [DONE]
  - 学习目标：能把一个 PyTorch 算子改写成 Triton，并保持数值一致。

<a id="s02-2-3"></a>
### 2.3 算子实现实战

- 2.3.1 element-wise 算子：PyTorch / Triton / CUDA 三种写法 <a id="s02-2-3-1"></a> [DONE]
  - 学习目标：比较三种写法的性能与复杂度，解释 element-wise 为什么是带宽瓶颈。
- 2.3.2 矩阵加法：offset 广播、`make_block_ptr` 与向量化 <a id="s02-2-3-2"></a> [DONE]
  - 学习目标：用 offset/make_block_ptr 实现矩阵加法，理解向量化与合并访存。
- 2.3.3 工业级实现：Memory Packing、SFINAE 与 Adaptive Grid Sizing <a id="s02-2-3-3"></a> [DONE]
  - 学习目标：解释 Memory Packing、SFINAE、Adaptive Grid 各自解决什么问题。

<a id="s02-3"></a>
## 3 性能剖析与优化方法

<a id="s02-3-1"></a>
### 3.1 性能剖析

- 3.1.1 Nsight、CUPTI 与指标解读 <a id="s02-3-1-1"></a> [DONE]
  - 学习目标：能用 Nsight 采集 kernel 的耗时、吞吐、占用率与访存指标。
- 3.1.2 常见瓶颈：访存、分支、同步与占用率 <a id="s02-3-1-2"></a> [DONE]
  - 学习目标：根据指标判断瓶颈类型，并给出对应的优化方向。
- 3.1.3 端到端性能回归与基准测试 <a id="s02-3-1-3"></a> [DONE]
  - 学习目标：设计端到端基准，避免只看单 kernel 或单次运行的误导。

<a id="s02-4"></a>
## 4 案例：从零实现 FlashAttention

<a id="s02-4-1"></a>
### 4.1 标准 Attention 的访存瓶颈

- 4.1.1 QKᵀ → softmax → V 的 HBM 读写灾难：N×N 中间矩阵的反复物化 <a id="s02-4-1-1"></a> [DONE]
  - 学习目标：解释标准 attention 为什么是 memory-bound，N×N 矩阵带来多少额外读写。
- 4.1.2 算子融合与分块矩阵乘法：把中间结果留在 SRAM <a id="s02-4-1-2"></a> [DONE]
  - 学习目标：说明 FlashAttention 如何用分块和融合消除 N×N 中间矩阵。

<a id="s02-4-2"></a>
### 4.2 Softmax 的数值稳定与在线化

- 4.2.1 naive softmax 与 safe softmax：两次/三次遍历与 exp 溢出 <a id="s02-4-2-1"></a> [DONE]
  - 学习目标：解释 naive softmax 的溢出问题和 safe softmax 的三次遍历代价。
- 4.2.2 online softmax：合并 max/sum 遍历的递推公式 <a id="s02-4-2-2"></a> [DONE]
  - 学习目标：推导 online softmax 的递推公式，说明为什么只需一次遍历。
- 4.2.3 online softmax × value：边扫分数边累加输出 <a id="s02-4-2-3"></a> [DONE]
  - 学习目标：推导输出 O 的在线更新公式，说明块间只需传 M/D/O 等状态量。

<a id="s02-4-3"></a>
### 4.3 CUDA 内核实现与演进

- 4.3.1 CUDA 算子解析：grid/block 划分、SRAM 分块与状态量写回 <a id="s02-4-3-1"></a> [DONE]
  - 学习目标：读懂一个最小 FlashAttention CUDA kernel 的 grid/block 配置和内外层循环。
- 4.3.2 FlashAttention-2/3：循环顺序、Warp 切分、TMA 与 WGMMA <a id="s02-4-3-2"></a> [DONE]
  - 学习目标：说明 FA2 的循环顺序/Warp 切分和 FA3 的 TMA/WGMMA 各自优化了什么。

<a id="s02-5"></a>
## 5 解码内核与算子融合

<a id="s02-5-1"></a>
### 5.1 解码阶段专用注意力内核

- 5.1.1 Decode 阶段 Query 长度为 1 导致的并行度问题 <a id="s02-5-1-1"></a> [DONE]
  - 学习目标：解释 Query 长度为 1 时为什么 SM 线程块并行度不足。
- 5.1.2 FlashDecoding：Split-K 切分 KV 序列与局部 Softmax 归约 <a id="s02-5-1-2"></a> [DONE]
  - 学习目标：说明 Split-K 如何切分 KV 并归约局部 softmax 结果。
- 5.1.3 FlashInfer：块稀疏存储、负载均衡调度与 JIT 编译 <a id="s02-5-1-3"></a> [DONE]
  - 学习目标：说明块稀疏格式、负载均衡和 JIT 在 FlashInfer 中的作用。

<a id="s02-5-2"></a>
### 5.2 算子融合与 CUDA Graph

- 5.2.1 常见融合模式：QKV 投影合并、RoPE + Attention、Add + RMSNorm、Gate + Up 投影 <a id="s02-5-2-1"></a> [DONE]
  - 学习目标：列举四种融合模式，说明各自减少了哪些读写或启动开销。
- 5.2.2 CUDA Graph 与内核启动开销：录制静态图、动态 Shape 补齐与显存池绑定 <a id="s02-5-2-2"></a> [DONE]
  - 学习目标：解释 CUDA Graph 如何降低 launch overhead，以及动态 shape 带来的限制。

<a id="s02-6"></a>
## 6 编译器与图优化

<a id="s02-6-1"></a>
### 6.1 编译器与图优化

- 6.1.1 XLA、TorchInductor 与 TVM：三种编译器的定位与输入 <a id="s02-6-1-1"></a> [DONE]
  - 学习目标：比较 XLA、TorchInductor、TVM 的定位、输入图与适用场景。
- 6.1.2 图融合、布局与内存规划 <a id="s02-6-1-2"></a> [DONE]
  - 学习目标：说明图融合、布局选择和内存规划如何影响端到端性能。
- 6.1.3 自定义算子与后端集成 <a id="s02-6-1-3"></a> [DONE]
  - 学习目标：说明如何把自定义 CUDA/Triton 内核接入编译器或推理后端。

## 学习出口

能判断一个算子是算力瓶颈还是访存瓶颈；能写 CUDA/Triton 内核；能读懂 FlashAttention 的分块与 online softmax；能用 Nsight/CUPTI 定位瓶颈；能判断什么时候该手写内核、什么时候交给编译器。

## 导航

[返回分类目录](../README.md) · [知识总目录](../../../README.md)
