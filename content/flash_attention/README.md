# 系列：Flash Attention 学习过程详解

- **平台**：Bilibili
- **UP 主**：比飞鸟贵重的多_HKL
- **来源**：多 P 视频《Flash Attention 学习过程【详】解（已完成！）》（[BV1FM9XYoEQ5](https://www.bilibili.com/video/BV1FM9XYoEQ5/)）
- **本系列已整理**：第02–09讲（p=2~9），共 8 集（约 143 分）
- **主题**：不只讲知识点，更讲「学习过程」——以 FlashAttention 为例，演示如何从零找到切入点、搭建可调试的 LibTorch 最小工程、逐步推导并实现 CUDA 算子

## 建议学习路线

| 阶段 | 讲次 | 内容 |
| --- | --- | --- |
| 寻找切入点 | 02 | 认清 attention 的访存瓶颈与算子融合本质；对比 llama.cpp、官方实现与 minimal 实现，选定 LibTorch + flash-attention-minimal 作为载体 |
| 环境搭建 | 03 | LibTorch 环境搭建：官网下载 → CMake `CMAKE_PREFIX_PATH` → 把 Python 代码翻译成 C++ → `cuda-gdb` 调试 kernel |
| 分块乘法 | 04 | 算子融合与三个矩阵相乘合并：attention 的 softmax 难点、R 矩阵的开销、分块让 R 不落显存 |
| softmax 基础 | 05 | naive & safe softmax：两次/三次遍历、exp 溢出、减最大值为何能防溢出 |
| 核心推导 | 06–07 | online softmax（合并 max/sum 遍历）、online softmax 与 value 点积优化（免存 R） |
| 代码实现 | 08 | CUDA 算子解析：并行划分、两层循环、分块与 SRAM、逐步拆解 kernel |
| 答疑复盘 | 09 | 疑惑与思考：手写 CUDA 的痛点、优秀开源的标准、vLLM/llama.cpp/CUTLASS 的取舍 |

## 分讲索引

| 讲次 | 标题 | 时长 | 视频演说图文稿 | 博客 | 配图 | 原视频 |
| ---: | --- | ---: | --- | --- | ---: | --- |
| 02 | 寻找切入点 | 14:16 | [文稿](transcripts/第02讲_寻找切入点.md) | [博客](blog/第02讲_寻找切入点.md) | 13 | [B站 p=2](https://www.bilibili.com/video/BV1FM9XYoEQ5/?p=2) |
| 03 | libtorch 环境搭建 | 21:22 | [文稿](transcripts/第03讲_libtorch环境搭建.md) | [博客](blog/第03讲_libtorch环境搭建.md) | 9 | [B站 p=3](https://www.bilibili.com/video/BV1FM9XYoEQ5/?p=3) |
| 04 | 三个矩阵相乘合并 | 14:56 | [文稿](transcripts/第04讲_三个矩阵相乘合并.md) | [博客](blog/第04讲_三个矩阵相乘合并.md) | 6 | [B站 p=4](https://www.bilibili.com/video/BV1FM9XYoEQ5/?p=4) |
| 05 | naive & safe softmax | 08:36 | [文稿](transcripts/第05讲_naive&safe_softmax.md) | [博客](blog/第05讲_naive&safe_softmax.md) | 4 | [B站 p=5](https://www.bilibili.com/video/BV1FM9XYoEQ5/?p=5) |
| 06 | online softmax（重制版） | 17:38 | [文稿](transcripts/第06讲_online_softmax（重制版）.md) | [博客](blog/第06讲_online_softmax（重制版）.md) | 6 | [B站 p=6](https://www.bilibili.com/video/BV1FM9XYoEQ5/?p=6) |
| 07 | online softmax 与 value 的点积优化 | 15:37 | [文稿](transcripts/第07讲_online_softmax与value的点积优化.md) | [博客](blog/第07讲_online_softmax与value的点积优化.md) | 6 | [B站 p=7](https://www.bilibili.com/video/BV1FM9XYoEQ5/?p=7) |
| 08 | cuda 算子解析 | 18:00 | [文稿](transcripts/第08讲_cuda算子解析.md) | [博客](blog/第08讲_cuda算子解析.md) | 5 | [B站 p=8](https://www.bilibili.com/video/BV1FM9XYoEQ5/?p=8) |
| 09 | 疑惑与思考（请认真听很关键！） | 26:24 | [文稿](transcripts/第09讲_疑惑与思考（请认真听很关键！）.md) | [博客](blog/第09讲_疑惑与思考（请认真听很关键！）.md) | 5 | [B站 p=9](https://www.bilibili.com/video/BV1FM9XYoEQ5/?p=9) |

## 系列全部分 P（来源：B 站投稿信息）

| 分P | 分P标题 | 时长 | 状态 |
| ---: | --- | ---: | --- |
| 1 | 【Flash Atten】0.预告 | 04:48 | 未整理 |
| 2 | 【Flash Atten】1.寻找切入点 | 14:16 | ✅ 已整理 |
| 3 | 【Flash Atten】2.libtorch 环境搭建 | 21:22 | ✅ 已整理 |
| 4 | 【Flash Atten】3.三个矩阵相乘合并 | 14:56 | ✅ 已整理 |
| 5 | 【Flash Atten】4.naive & safe softmax | 08:36 | ✅ 已整理 |
| 6 | 【Flash Atten】5.online softmax（重制版） | 17:38 | ✅ 已整理 |
| 7 | 【Flash Atten】6.online softmax 与 value 的点积优化 | 15:37 | ✅ 已整理 |
| 8 | 【Flash Atten】7.cuda 算子解析 | 18:00 | ✅ 已整理 |
| 9 | 【Flash Atten】8.疑惑与思考（请认真听很关键！） | 26:24 | ✅ 已整理 |

## 核心知识点速览

- **第02讲**：FlashAttention 的本质是解决 attention 的**访存瓶颈**（`QKᵀ → softmax → V` 三步产生大量 HBM 读写，属 memory bound），核心手段是**算子融合**——把「三次读、三次写」压成「读一次、写一次」，中间结果留在 SRAM；学习方法上先**锁定核心目标（理解思想 + 读懂代码）并简化非核心因素**，最终放弃耦合重的 llama.cpp 与庞大的官方实现，选用约 100 行的 `tspeterkim/flash-attention-minimal`，再借助 **LibTorch** 摆脱 Python 绑定、直接在 C++ 中调试 CUDA 代码。
- **第03讲**：LibTorch 环境搭建。原则是**先看官网**；下载选 **Linux + C++11 ABI + 匹配的 CUDA 版本**；CMake 用 `CMAKE_PREFIX_PATH` 指向 libtorch 让 `find_package(Torch)` 生效；**LibTorch 就是 PyTorch 的 C++ 前端**，API 几乎一一对应（`torch::Tensor`、`.to("cuda")`、`.size()`、`.data_ptr<float>()`），照着把 Python 抄成 C++ 即可；用 `launch.json` 配 **`cuda-gdb`** 就能断点进 kernel。
- **第04讲**：三个矩阵相乘合并（分块乘法）。**算子融合**适用于「逐元素独立、无依赖」的算子（如「加一乘五」，2 读 2 写 → 1 读 1 写）；attention 的融合难点在 **softmax 必须整行算完**；常规做法产生巨大的 N×N 中间矩阵 R（写回再读出，是显存与速度的双重打击）；FlashAttention 把 Q、K、V 分块进 **shared memory**，算完一块 `QKᵀ` 立刻乘 V、**中间结果不写回**，R 被消灭，结果由多块**累加**得到、**无精度损失**；softmax 留待后续攻克。
- **第05讲**：naive & safe softmax。naive softmax 两次遍历（先求和再归一化）但 `exp` 易溢出；safe softmax 先求最大值 `M` 再用 `e^{x−M}` 计算，数值安全但**三次遍历**；因分子分母同时约掉 `e^{−M}`，两者结果等价。softmax 的多次遍历是访存开销，也是 online softmax 要压缩的对象。
- **第06讲**：Online Softmax。safe softmax 需三次遍历（求 max、求 sum、算输出）；用「**加减同一个数 + 指数拆分**」的技巧，把 `D` 改写成迭代式 `D_j = D_{j-1} · e^{M_{j-1} − M_j} + e^{x_j − M_j}`，从而把求 max 与求 sum 合并进**一次遍历**；代码里用 `pre_max_value` 保存上一轮最大值、`sum` 必须初始化为 0（否则 NaN）。
- **第07讲**：Online Softmax × Value（FlashAttention 最核心）。把「softmax 结果乘 V」也做成在线迭代：`O_j = O_{j-1} · (D_{j-1}/D_j) · e^{M_{j-1} − M_j} + (e^{x_j − M_j}/D_j) · V_j`；于是 attention 可「边扫分数边累加输出」，块间只传 `M、D、O` 等小状态量，**无需存储中间权重矩阵 R**——这正是 FlashAttention 分块在线计算成立的根本。
- **第08讲**：CUDA 算子解析。grid 按 (batch, head) 分 16 个 block、每块 32 线程；**外层循环 K/V（慢）、内层循环 Q（快）**，K 与 V 一起移动；分块 `Bc = ⌈M/(4d)⌉`、`Br = min(⌈M/(4d)⌉, d)`，`BC=BR=32`；kernel 流程：QKV 偏移 → 搬 K/V 到 SRAM → 算 QKᵀ（不转置、利于合并访存）→ 乘 `1/√d` → 行 max/exp/sum → 用 online 公式更新 O 与 L/M → 写回 L/M。中间矩阵不落 HBM，只落 L/M/O 等状态量。
- **第09讲**：疑惑与思考。手写 CUDA 的四大痛点（索引多易错、无封装难复用、要惦记访存合并/边界/线程数统一、参考实现写死线程数只能当 demo）；优秀开源的标准；三家实现取舍——**vLLM 用 Triton**（编译器帮忙）、**llama.cpp 用 Tensor Core（WMMA）**（`-FA` 启用，V1/V2 仅调换循环顺序）、**其他开源用 CUTLASS**；核心方法论是**按需学习**（先有问题与需求再学工具），即「不止 FlashAttention」。

## 相关资源（来自视频）

- flash-attention-minimal（约 100 行 CUDA 实现）：https://github.com/tspeterkim/flash-attention-minimal
- 官方 FlashAttention：https://github.com/Dao-AILab/flash-attention
