# 系列：手撕 AI Infra 算子（CUDA + Triton + PyTorch）

- **平台**：Bilibili
- **UP 主**：杜子源源
- **来源**：合集《从零到一：像刷力扣一样手撕100个AI算子》（season_id 7903388）
- **本系列已整理**：系列 3–7，共 5 集（约 1 小时 20 分）
- **主题**：用「一个算子、三种写法」的方式，从环境搭起，逐层讲透 CUDA、Triton、PyTorch 的算子实现与优化

## 建议学习路线

| 阶段 | 讲次 | 内容 |
| --- | --- | --- |
| 环境准备 | 03 | 极速环境配置：NVIDIA 驱动 → CUDA Toolkit → uv 虚拟环境 → PyTorch/Triton |
| 建立认知 | 04 | CUDA/Triton/PyTorch 的前世今生与设计哲学（选型基础） |
| 第一个算子 | 05 | element-wise 逐元素算子：PyTorch / Triton / CUDA 三种实现与向量化、grid loop |
| 工业级实现 | 06 | 工业级 Element-Wise：OneFlow 200 行代码的分层与三大设计支柱 |
| 二维与进阶 | 07 | Matrix Addition：Triton 的 offset、`make_block_ptr` 与 CUDA 四个版本 |

## 分讲索引

| 讲次 | 标题 | 时长 | 视频演说图文稿 | 博客 | 配图 | 原视频 |
| ---: | --- | ---: | --- | --- | ---: | --- |
| 03 | 极速环境配置 | 20:54 | [文稿](transcripts/第03讲_极速环境配置.md) | [博客](blog/第03讲_极速环境配置.md) | 13 | [B站](https://www.bilibili.com/video/BV1VvQ3BSELZ/) |
| 04 | CUDA、Triton、Pytorch 的前世今生 | 17:45 | [文稿](transcripts/第04讲_CUDA、Triton、Pytorch的前世今生.md) | [博客](blog/第04讲_CUDA、Triton、Pytorch的前世今生.md) | 16 | [B站](https://www.bilibili.com/video/BV147dYBLEi4/) |
| 05 | element_wise 算子详解 | 20:27 | [文稿](transcripts/第05讲_element_wise算子详解.md) | [博客](blog/第05讲_element_wise算子详解.md) | 15 | [B站](https://www.bilibili.com/video/BV1L6oNBSEGc/) |
| 06 | 工业级 Element_Wise 的实现（Oneflow 详解） | 09:04 | [文稿](transcripts/第06讲_工业级Element_Wise的实现_Oneflow详解.md) | [博客](blog/第06讲_工业级Element_Wise的实现_Oneflow详解.md) | 13 | [B站](https://www.bilibili.com/video/BV1npovBCE1r/) |
| 07 | Matrix Addition 详解 | 11:26 | [文稿](transcripts/第07讲_Matrix_Addition详解.md) | [博客](blog/第07讲_Matrix_Addition详解.md) | 12 | [B站](https://www.bilibili.com/video/BV1PvoeB2E2h/) |

## 核心知识点速览

- **第03讲**：四层组件关系（驱动全局唯一 / CUDA Toolkit 多版本 / 框架在虚拟环境 / Runtime 随框架）；驱动、CUDA Toolkit（3 个避坑操作）、多版本切换（改 `.zshrc` 的 `PATH` 与 `LD_LIBRARY_PATH`）、`uv` 建环境与一键装 PyTorch/Triton。
- **第04讲**：CUDA 由顶点/像素处理器的三大缺陷「逼」出（Tesla 统一 TPC）；CUDA 三大设计（异构、核函数、grid/block/thread）；PyTorch 的两个「爹」（Torch、Chainer）与动态图；Triton 屏蔽线程、专注 tile，Roofline 逼近 cuBLAS。
- **第05讲**：element-wise 的两大特性（无依赖、瓶颈在带宽）；两个通杀优化——**向量化**与 **grid loop**；Triton 的 `@triton.autotune`；CUDA 四版本；模板化与 OneFlow。
- **第06讲**：工业级实现分四层（接口层 / 分发层 / 内核实现层 / 打包层）；三大支柱 **Memory Packing（128-bit 对齐）、SFINAE 编译期优化、Adaptive Grid Sizing**。
- **第07讲**：Triton 的 **offset 广播计算**与 **`tl.make_block_ptr`**；CUDA 的 naive / grid-stride / float4 / 二维四版本；合并访问与 `__ldg`。

## 相关资源（来自视频与讲义）

- LeetGPU（算子练习/测评）：https://leetgpu.com/challenges
- LeetCUDA（CUDA 算子实现库）：https://github.com/xlite-dev/LeetCUDA
- OneFlow（国产开源深度学习框架）：https://github.com/Oneflow-Inc/oneflow
- SOL-ExecBench（英伟达算子基准/竞赛）：https://research.nvidia.com/benchmarks/sol-execbench
- UP 主博客（CUDA 学习之路系列）：https://dlog.com.cn/
