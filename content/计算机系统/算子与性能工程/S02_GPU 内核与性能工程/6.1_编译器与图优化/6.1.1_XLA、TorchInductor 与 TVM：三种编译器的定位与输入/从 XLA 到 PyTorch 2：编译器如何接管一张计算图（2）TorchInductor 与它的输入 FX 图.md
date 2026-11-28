# 从 XLA 到 PyTorch 2：编译器如何接管一张计算图（2）TorchInductor 与它的输入 FX 图

> 视频来源：[Deep Dive: Compiling deep learning models, from XLA to PyTorch 2](https://www.youtube.com/watch?v=Oo07fFb-aH0)（YouTube · Julien Simon，2024-02）｜时长约 39 分钟
> 导读：本文是该视频的下半篇，专讲 PyTorch 2 的编译栈：`torch.compile` 背后三个阶段的工具分别是谁、TorchInductor 吃什么、吐什么。上半篇《（1）XLA 与它的输入 HLO》讲 XLA 那一支。视频字幕为 YouTube 自动字幕，术语按上下文订正。

## 本讲要解决的核心问题（SCQA）

**背景**：上一篇看到，XLA 靠"懒张量 + tracing"从 PyTorch 里把图追出来，代价是要改设备、要加一句 mark_step 调用，而且 TorchScript 那条路已经走不通了（不支持动态形状、不支持非 PyTorch 代码）。

**冲突**：PyTorch 需要一个**不用改代码**、又能容忍动态形状和数据相关控制流的编译方案。可编译器天生喜欢静态图，这两件事是矛盾的。

**疑问**：PyTorch 2 是怎么在保持 eager 体验的前提下，把图抓到手的？抓到之后交给谁编译？编译器的输入到底是什么？

**回答（中心思想）**：PyTorch 2 把"编译一个模型"拆成三段——**抓图（graph acquisition）、下降（graph lowering）、编译（graph compilation）**。抓图由 **TorchDynamo + AOTAutograd** 完成，产物是一张 **FX 图**（`torch.fx` 格式）；编译由 **TorchInductor** 完成，它为 CPU 生成 C++/OpenMP、为 GPU 生成 **Triton** 代码，再交给 LLVM 之类的后端编译器出机器码。TorchInductor 在这三种编译器里的位置是：**"框架自己的图"这一层的编译器**——输入是 PyTorch 自己的 FX 图，而不是跨框架的 StableHLO。

## 一、工作流没变，变的只是工具

PyTorch 2 的官方教程里有一张流程图，是整个下半篇的地图。它的三段与本篇的三段严格对应：

![PyTorch 2 的编译栈：Graph Acquisition（TorchDynamo + AOTAutograd）→ Graph Lowering（AtenPrim IR）→ Graph Compilation（TorchInductor，默认由 Triton 驱动）](assets/从%20XLA%20到%20PyTorch%202：编译器如何接管一张计算图（2）TorchInductor%20与它的输入%20FX%20图/01775.webp)

- **Graph Acquisition（抓图）**：TorchDynamo 负责前向，AOTAutograd 负责反向；
- **Graph Lowering（下降）**：把图降到 **AtenPrim IR**，也就是只剩底层原语的 Aten 算子；
- **Graph Compilation（编译）**：TorchInductor 出码，默认由 Triton 驱动。

视频里反复强调的一句话是：**步骤一个都没少，只是工具全换了**。[【跳转到 29:10】](https://www.youtube.com/watch?v=Oo07fFb-aH0&t=1750)[【跳转到 29:40】](https://www.youtube.com/watch?v=Oo07fFb-aH0&t=1780)

图的下半部分还画了后端的接入方式：`Frontend` 是 Dynamo（老式的 `FX Tracer` 已标为 legacy），往下是 `FX graph in Torch IR`，再经 `AOTAutograd` 变成 `FX graph in Aten/Prim IR`，然后交给 `Backend`——可选 `Inductor` 或 `nvFuser`，最后落到 `Codegen Backends`：`Triton` 与 `C++/OpenMP`。**这条链就是"PyTorch 2 允许第三方后端接入"的接口定义**。

## 二、抓图：TorchDynamo + AOTAutograd

### 2.1 分工

- **TorchDynamo**：负责**前向**路径的抓图；
- **AOTAutograd**：负责**反向**路径的抓图。

两者合起来，意味着**训练的前向和反向都能被加速**，而不只是推理。这一点比 TorchScript 时代强得多。[【跳转到 30:00】](https://www.youtube.com/watch?v=Oo07fFb-aH0&t=1800)

### 2.2 抓完的图长什么样：FX 图

抓图的产物是一张 **FX 图**，并以 `torch.fx` 格式保存。图里只使用底层原语——因为 PyTorch 有上千个高层算子，编译器不可能逐个优化，必须先收敛到几百个底层算子。这一步和 TorchScript 的思路完全一致：**先归一化，再优化**。[【跳转到 30:50】](https://www.youtube.com/watch?v=Oo07fFb-aH0&t=1850)

### 2.3 它解决了 TorchScript 的三个硬伤

这是 PyTorch 2 相对之前方案最实质的进步：

1. **数据相关的控制流**能处理了——`if` 的条件来自张量值也没问题；[【跳转到 31:15】](https://www.youtube.com/watch?v=Oo07fFb-aH0&t=1875)
2. **动态形状**能处理了——输入张量尺寸不同也支持；
3. **非 PyTorch 代码**能处理了——中间夹一段 NumPy 运算，同样会被优化。

![TorchDynamo + AOTAutograd 的三个"打勾"：数据相关控制流、动态形状、非 PyTorch 代码都支持](assets/从%20XLA%20到%20PyTorch%202：编译器如何接管一张计算图（2）TorchInductor%20与它的输入%20FX%20图/01950.webp)

图中还标出了 TorchInductor 的两个出码后端：**CPU 走 OpenMP/C++，GPU 走 OpenAI Triton**。这句话就是"TorchInductor 的输出是什么"的答案。[【跳转到 32:05】](https://www.youtube.com/watch?v=Oo07fFb-aH0&t=1925)

### 2.4 三代方案摆在一起看

视频把 PyTorch 阵营的三次尝试串成了一条线，正好可以对照：

| 方案 | 图从哪来 | 输入表示 | 主要短板 |
| --- | --- | --- | --- |
| TorchScript（2018） | 静态类型子集 + `trace`/`script` | TorchScript IR（只含底层原语） | 不支持动态形状、不支持非 PyTorch 代码；已维护模式 |
| PyTorch/XLA（2019） | 懒张量 tracing | HLO | 要改设备、要手动触发 mark_step；本质是把图交给外部编译器 |
| PyTorch 2（2023 起） | Dynamo + AOTAutograd 顺路抓 | FX 图 → Aten/Prim IR | 运行时编译有开销，需要缓存管理；AOT 导出到 2.2 才有 |

这条演进线的共同点很值得注意：**三代方案都在解决同一个问题——如何在一个 eager 框架里"造出"编译器需要的那张图**。差别只在造图的手段：静态类型（TorchScript）、惰性求值（PyTorch/XLA）、还是字节码级的追踪（Dynamo）。

## 三、下降与编译：从 FX 图到 Triton 内核

### 3.1 中间那一段：Graph Lowering 到 AtenPrim IR

抓到的 FX 图并不直接喂给 Inductor。流程图的中间一段叫 **Graph Lowering**，产物是 **AtenPrim IR**——只剩 Aten 底层算子（`aten::add`、`aten::mm` 这类）与少量原语的图。

为什么要多这一步？因为**图里算子的粒度决定了后端能做什么优化**。如果图里还留着"LayerNorm"这种高层算子，后端只能整体调一个现成内核；降到 Aten 原语之后，后端看到的是逐元素的加、乘、归约，才有机会自己决定怎么融合、怎么排循环。

### 3.2 它在前端还是后端

视频里的措辞很关键：**TorchInductor 是 frontend compiler（前端编译器）**。意思是它负责"把图翻译成某个可编译的源代码"，真正的机器码由更下面的后端编译器（LLVM 等）生成。

所以 TorchInductor 的完整链路是：[【跳转到 32:05】](https://www.youtube.com/watch?v=Oo07fFb-aH0&t=1925)

```
FX 图（Aten/Prim IR）
   └─ TorchInductor（前端编译器）
        ├─ CPU 目标 → C++ / OpenMP 源码
        └─ GPU 目标 → Triton 内核源码
             └─ 后端编译器（LLVM 等）→ 机器码
```

### 3.3 它也补上了 AOT

PyTorch 2.2 之前，这条链路只有 **JIT**。2.2 之后增加了 **AOT 导出**：可以把模型编译成一个几乎等同于共享库（shared library）的产物，直接在 CPU 或 GPU 上运行。这正好对应上一篇讲的"生产部署要 AOT"——同一个模型部署到多台机器时，不必每台都重新编译。[【跳转到 32:55】](https://www.youtube.com/watch?v=Oo07fFb-aH0&t=1975)

### 3.4 可扩展性：OpenXLA 作为后端

一个编译栈如果只能服务现有的设备，就没有意义。视频指出 PyTorch 明确表示会用 **OpenXLA 作为后端**，这意味着芯片厂商可以把自己的后端编译器插进 TorchInductor。

![PyTorch 2 的后端接入点：Dynamo → FX 图 → AOTAutograd → Backend（Inductor / nvFuser）→ Codegen Backends（Triton / C++ OpenMP）](assets/从%20XLA%20到%20PyTorch%202：编译器如何接管一张计算图（2）TorchInductor%20与它的输入%20FX%20图/01825.webp)

这就是上一篇 OpenXLA 那张架构图的下半段：[【跳转到 33:45】](https://www.youtube.com/watch?v=Oo07fFb-aH0&t=2025)**XLA 负责"跨框架、跨硬件"的通用后端，TorchInductor 负责"PyTorch 内部"的图到代码，两者通过 OpenXLA 后端接口接上**。视频作者的原话大意是：如果这套新栈无法扩展到未来五年的新设备上，那它就没有意义。[【跳转到 33:20】](https://www.youtube.com/watch?v=Oo07fFb-aH0&t=2000)

## 四、用起来是什么样：一行 `torch.compile`

### 4.1 一行代码

对 Hugging Face 的模型，加速就是加一行：

```python
model = BertModel.from_pretrained("bert-base-uncased").to(device=device)
model = torch.compile(model, backend="inductor")   # 就这一行
```

![一行 `torch.compile(model, backend="inductor")` 就能让 BERT 走完整条编译栈，CPU 和 GPU 通用](assets/从%20XLA%20到%20PyTorch%202：编译器如何接管一张计算图（2）TorchInductor%20与它的输入%20FX%20图/02133.webp)

`backend` 参数默认就是 `inductor`，也可以换成别的。[【跳转到 35:08】](https://www.youtube.com/watch?v=Oo07fFb-aH0&t=2108)对 pipeline 也一样：Stable Diffusion 里只需要编译 UNet 这一段"重活"。[【跳转到 35:33】](https://www.youtube.com/watch?v=Oo07fFb-aH0&t=2133)

### 4.2 实测：BERT 在 CPU 上的三个数字

视频最后做了一个 CPU 上的基准测试（PyTorch 2.2，Intel CPU，序列长度 420，跑 1000 次取平均）：

![BERT 在 CPU 上的基准：baseline 34.13 ms、Inductor 31.83 ms、再叠加 IPEX 30.86 ms](assets/从%20XLA%20到%20PyTorch%202：编译器如何接管一张计算图（2）TorchInductor%20与它的输入%20FX%20图/02222.webp)

| 配置 | 平均耗时 | 相对 baseline |
| --- | --- | --- |
| 原始模型（baseline） | 34.13 ms | — |
| `torch.compile(backend="inductor")` | 31.83 ms | 约快 7% |
| 再加 Intel Extension for PyTorch（IPEX） | 30.86 ms | 约快 10% |

视频作者自己的说法是"开箱即得 9–10% 的提升"（按幻灯片上的数字算是约 7%，量级一致），并强调**具体数字强依赖模型、硬件和序列长度**，要自己测。IPEX 在 `torch.compile` 之上又加了一点额外优化，收益很小（大约再 1%），但"在规模上 1% 也是巨大的收益"。

值得注意的还有代码里那两行：

```python
print(torch._dynamo.list_backends())   # 看当前有哪些后端可用
torch._dynamo.reset()                  # 清掉编译缓存，重新编译
```

前者说明"后端"是可插拔的一等公民，后者说明编译结果是被缓存的——这也是 JIT 方案的日常操作。[【跳转到 37:27】](https://www.youtube.com/watch?v=Oo07fFb-aH0&t=2247)

## 五、把 TorchInductor 放回三种编译器的坐标系里

| 维度 | TorchInductor |
| --- | --- |
| 定位 | PyTorch 自己的前端编译器：把 FX 图翻译成 Triton / C++ 源码 |
| 输入 | **FX 图**（`torch.fx` 格式），经 AOTAutograd 下降为 **Aten/Prim IR** |
| 图从哪来 | TorchDynamo（前向）+ AOTAutograd（反向）在 eager 执行中"顺路"抓出来 |
| 中间表示 | Aten/Prim IR（只剩底层原语的 Aten 算子）→ Inductor 的 loop-level IR |
| 后端与目标 | CPU：C++/OpenMP；GPU：OpenAI Triton；再往下一层交给 LLVM 等后端编译器；可通过 OpenXLA 接口接第三方硬件 |
| 典型适用场景 | 已经在用 PyTorch、不想改代码、模型含动态形状或数据相关控制流；训练与推理都覆盖 |
| 主要代价 | 编译发生在运行时（JIT），有编译开销与缓存管理问题；AOT 导出到 2.2 才有 |

把它和 XLA 摆在一起看，差别非常清楚：

- **XLA 的输入是跨框架的 StableHLO**，它服务的是"很多框架 → 很多硬件"这个矩阵；PyTorch 只是它的一个前端。
- **TorchInductor 的输入是 PyTorch 自己的 FX 图**，它服务的是"PyTorch → 各种硬件"这一条线；它是 PyTorch 内部的一环，而不是外部后端。
- 两者在工程上会接起来：**TorchInductor 可以把 OpenXLA 当作后端**，此时链路变成 FX 图 → Inductor → StableHLO → XLA → 硬件。

## 小结

- PyTorch 2 的 `torch.compile` 不是"一个 API"，而是**一整套栈**：抓图 → 下降 → 编译三段，流程与 XLA 时代完全一样，工具全换。
- **抓图**：TorchDynamo 管前向、AOTAutograd 管反向，产物是 **FX 图**；它一次解决了 TorchScript 的三个硬伤（数据相关控制流、动态形状、非 PyTorch 代码）。
- **下降**：FX 图降到只含底层原语的 **Aten/Prim IR**，把上千个高层算子收敛到几百个。
- **编译**：**TorchInductor 是前端编译器**——CPU 出 C++/OpenMP，GPU 出 Triton，再由 LLVM 一类后端编译器生成机器码。
- **AOT**：2.2 起支持把模型导出成近乎共享库的产物，解决了"部署 50 台机器要编译 50 次"的问题。
- **可扩展**：PyTorch 用 **OpenXLA 作为后端接口**，芯片厂商可以把自家编译器插进 TorchInductor。
- 定位上一句话：**TorchInductor 是"框架自己的图"这一层的编译器，输入 FX 图，卖点是零改码 + 容忍动态性**。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| `torch.compile` | PyTorch 2 的编译入口，一行代码接入整套编译栈 |
| TorchDynamo | PyTorch 的抓图器，在 eager 执行中记录算子并产出 FX 图 |
| AOTAutograd | 负责反向路径抓图的组件，让训练的前向与反向都能被编译 |
| FX 图 | `torch.fx` 格式的计算图，PyTorch 编译栈的通用交换格式 |
| Aten / Prim IR | 只含底层原语 Aten 算子的中间表示，是 Inductor 的直接输入 |
| TorchInductor | PyTorch 的前端编译器，把 FX 图翻译成 Triton 或 C++/OpenMP 代码 |
| Triton | OpenAI 的 GPU 内核语言，TorchInductor 的 GPU 出码目标 |
| nvFuser | PyTorch 2 里另一个可选后端，与 Inductor 并列 |
| backend（后端） | `torch.compile` 的可插拔编译目标，默认 `inductor` |
| AOT 导出 | PyTorch 2.2 起支持，把模型编译成可独立部署的产物 |