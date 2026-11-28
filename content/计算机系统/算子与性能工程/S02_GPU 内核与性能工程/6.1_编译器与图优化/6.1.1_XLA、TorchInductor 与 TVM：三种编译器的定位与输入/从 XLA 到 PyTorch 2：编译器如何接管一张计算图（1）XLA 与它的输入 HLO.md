# 从 XLA 到 PyTorch 2：编译器如何接管一张计算图（1）XLA 与它的输入 HLO

> 视频来源：[Deep Dive: Compiling deep learning models, from XLA to PyTorch 2](https://www.youtube.com/watch?v=Oo07fFb-aH0)（YouTube · Julien Simon，2024-02）｜时长约 39 分钟
> 导读：本文是该视频的上半篇，只讲 XLA 这一支：它为什么诞生、它的输入是什么、它把图交给谁。下半篇《（2）TorchInductor 与它的输入 FX 图》接着讲 PyTorch 2 的编译栈。视频字幕为 YouTube 自动字幕，术语按上下文订正。

## 本讲要解决的核心问题（SCQA）

**背景**：深度学习框架写模型，本质是写一串张量运算。TensorFlow 1.x 时代这些运算先被拼成一张图，再整张图交给运行时执行。

**冲突**：既然整张图、所有张量形状、所有数据类型在执行前就已经确定，那"人工去优化这张图"就变得多余——为什么不让一个编译器自动做？可 PyTorch 走的是另一条路（边算边执行），根本没有"一张完整的图"可交给编译器。

**疑问**：XLA 到底吃进去什么、吐出来什么？它凭什么能同时服务 TensorFlow、JAX 和 PyTorch？

**回答（中心思想）**：XLA 的定位是**"图级优化器 + 设备代码生成器"**，它的输入是一张已经完整可见的计算图，中间表示叫 HLO（现在以 StableHLO 的形式独立成标准），输出是面向 CPU/GPU/TPU 的原生机器码。它在这三种编译器里的位置是**最靠上游、最贴近"整张图"的那一层**：XLA 不关心你的 Python 长什么样，只关心你交来的那张图长什么样。

## 一、XLA 诞生的前提：先得有一张静态图

### 1.1 define-then-run：把模型写成一张图

TensorFlow 1.x 的写法是先用变量和算子把整张图"定义"出来，再"运行"它。视频里给的例子是两层全连接。[【跳转到 02:10】](https://www.youtube.com/watch?v=Oo07fFb-aH0&t=130)

```python
# 第一层：128 个神经元
w1 = tf.Variable(tf.random_normal([128, x_dim]), name='w1')
b1 = tf.Variable(tf.constant(0.1, shape=(128, 1)), name='b1')
y1 = tf.nn.relu(tf.add(tf.matmul(w1, x), b1))

# 第二层：256 个神经元
w2 = tf.Variable(tf.random_normal([256, 128]), name='w2')
b2 = tf.Variable(tf.constant(0.1, shape=(256, 1)), name='b2')
y2 = tf.nn.relu(tf.add(tf.matmul(w2, y1), b2))
```

![TensorFlow 1.x 的 define-then-run 写法：模型是一张待执行的图，而不是立刻发生的计算](assets/从%20XLA%20到%20PyTorch%202：编译器如何接管一张计算图（1）XLA%20与它的输入%20HLO/00205.webp)

写完这段代码，**什么计算都还没发生**。它只是在描述"将来训练或推理时会发生什么"。这种模式叫 **define-then-run**（先定义后运行），也叫 **graph mode**（图模式）：框架在后台建好一张执行图，用 TensorBoard 就能把这张图直接画出来。[【跳转到 04:40】](https://www.youtube.com/watch?v=Oo07fFb-aH0&t=280)[【跳转到 04:15】](https://www.youtube.com/watch?v=Oo07fFb-aH0&t=255)

### 1.2 静态图带来的优化机会，正是编译器的用武之地

图一旦完整可见，可做的优化就非常具体：张量形状已知，可以预分配内存；算子相邻，可以合并；数据类型已知，可以挑更省的选择。这些都是"在图上做文章"的经典手段。[【跳转到 05:05】](https://www.youtube.com/watch?v=Oo07fFb-aH0&t=305)

于是问题自然变成：**能不能让工具自动做这件事**，而不是靠人手工改图？XLA 就是这个问题的答案。

## 二、XLA 的定位：一张图进来，机器码出去

XLA 全称 **Accelerated Linear Algebra**（加速线性代数），2017 年随 TensorFlow 1.0 的首个候选版本一起出现。它的官方描述可以拆成四句，正好对应一个编译器的四个动作：[【跳转到 05:55】](https://www.youtube.com/watch?v=Oo07fFb-aH0&t=355)

![XLA 的四项职责：按真实维度特化、消除冗余并融合算子、为 CPU/GPU/TPU 生成原生机器码](assets/从%20XLA%20到%20PyTorch%202：编译器如何接管一张计算图（1）XLA%20与它的输入%20HLO/00480.webp)

1. **按真实的张量维度和数据类型特化这张图**——因为图是静态的，编译器知道每个张量到底多大、是什么 dtype，可以据此做内存分配与内存优化。
2. **消除冗余、尽可能融合算子**——"先乘后加"可以变成一条乘加指令；一串连续的加法或乘法可以合并成更少的算子，省下反复读写内存的开销。
3. **为 CPU、GPU、TPU 生成设备相关的原生机器码**。
4. 因此整个流程天然分成两段：**前端**做与设备无关的图级优化，**后端**把优化后的图变成与设备相关的代码。

这就是所有编译器的标准骨架：**前端吃图、后端出码**。[【跳转到 08:00】](https://www.youtube.com/watch?v=Oo07fFb-aH0&t=480)

### 2.1 两种触发时机：JIT 与 AOT

编译什么时候发生，有两种选择：

- **JIT（just-in-time，即时编译）**：代码跑起来、真正要评估这张图的那一刻才编译。灵活，但每次运行都要付一次编译成本。
- **AOT（ahead-of-time，提前编译）**：先把模型编译成产物，再把产物部署出去。视频举的例子很直白——同一个模型要部署到 50 台服务器上，你显然不希望编译 50 次。

这两种时机在后面 PyTorch 2 的部分还会再出现一次，是理解"编译器在什么位置介入"的关键坐标。[【跳转到 08:25】](https://www.youtube.com/watch?v=Oo07fFb-aH0&t=505)

## 三、PyTorch 阵营的第一次尝试：TorchScript 与它的 IR

### 3.1 问题：eager 模式没有图可交

PyTorch 默认是 **eager mode**（也叫 define-by-run，边定义边运行）：写一行执行一行，算子立刻在硬件上跑完。好处是灵活、好调试；代价是**根本不存在一张完整的图**，而没有图就无法做图级优化。[【跳转到 15:17】](https://www.youtube.com/watch?v=Oo07fFb-aH0&t=917)

PyTorch 的第一版答案是 **TorchScript**：Python 的一个静态类型子集。静态类型让"提前把一切说清楚"成为可能，`torch.jit.trace()` / `torch.jit.script()` 负责把 Python 代码转成 TorchScript，再存盘、加载。

### 3.2 TorchScript 的 IR：把语言收敛成少数底层原语

TorchScript 再往下走一步，就导出成一份 **IR（intermediate representation，中间表示）**。这份 IR 只使用非常底层的 PyTorch 原语，看起来极其啰嗦，但啰嗦是有原因的：

![同一段 Python 代码的三级形态：Python 源码 → TorchScript → 只含底层原语的 TorchScript IR](assets/从%20XLA%20到%20PyTorch%202：编译器如何接管一张计算图（1）XLA%20与它的输入%20HLO/00705.webp)

- 每个常量都显式定义，且**只赋值一次**（SSA 形式）；
- 只保留一个很小的算子集合。PyTorch 有上千个高层算子，编译器不可能逐个优化，必须先收敛到几百个底层算子；
- 剩下的都是循环、基本算术这类原语。

这正是编译器的常规套路：**先把五花八门的写法归一化成少数原语，再在这些原语上做优化**。[【跳转到 12:10】](https://www.youtube.com/watch?v=Oo07fFb-aH0&t=730)有了这份 IR，既可以转成 C++ 集成进 C++ 工程，也可以直接交给某个加速器的编译后端。

### 3.3 TorchScript 的局限

TorchScript 有两个硬伤：**不支持动态形状**，**不支持非 PyTorch 代码**（比如中间夹了 NumPy 运算）。视频里明确说它现在处于维护模式（maintenance mode），不建议再投入太多精力——但它是一次有价值的中间尝试。[【跳转到 13:50】](https://www.youtube.com/watch?v=Oo07fFb-aH0&t=830)

## 四、PyTorch/XLA：用"懒张量"把图抓出来

### 4.1 冲突点：eager 模式怎么喂给一个图编译器

2018 年 PyTorch 与 Google 开始合作把 PyTorch 跑上 TPU。矛盾立刻出现：XLA 要一张图，PyTorch 不产图。

### 4.2 解法：lazy tensor（懒张量）

2019 年底发布的 **PyTorch/XLA** 引入 **lazy tensor**：你照常写 PyTorch 代码，但算子**不立刻执行**，而是被记录下来；图在记录中逐渐成形；直到不得不算的那一刻（做反向传播、更新参数）才一次性编译并执行。

![PyTorch/XLA 的定位：用懒张量把 eager 代码的图记录下来，再交给 XLA 编译到加速器](assets/从%20XLA%20到%20PyTorch%202：编译器如何接管一张计算图（1）XLA%20与它的输入%20HLO/00967.webp)

这个"记录算子而不执行"的过程叫 **tracing（追踪）**。它对用户代码的侵入极小：模型、损失函数、优化器、训练循环全都不用改。

### 4.3 完整链路：tracing → lowering → HLO → 编译 → 执行

把上面几步串起来，就是 XLA 的完整输入输出链路：

1. **tracing**：在 host（服务器 CPU）上跑训练循环，所有算子被记录下来，攒出一份内部表示；
2. **lowering（下降）**：把这份内部表示翻译成 **HLO（High-Level Operations，高层操作）**；
3. **编译**：把 HLO 交给编译器，生成设备相关的机器码；
4. **执行**：把编译产物加载到 XLA 设备（比如 TPU）上运行。

![PyTorch/XLA 的 Hello World：橙色的三行是唯一需要新增的代码，最后一句 mark_step 调用触发编译与执行](assets/从%20XLA%20到%20PyTorch%202：编译器如何接管一张计算图（1）XLA%20与它的输入%20HLO/01174.webp)

代码上只多三样东西：导入 XLA 的模型模块、取一个 XLA 设备、以及在优化器更新之后加一句 `mark_step` 调用：

```python
import torch_xla.core.xla_model as xm

device = xm.xla_device()
model = MNIST().train().to(device)
# ...（训练循环与原始 PyTorch 完全一致）...
xm.mark_step()   # 现在才真正编译并执行
```
**橙色框里的整个训练循环一行都不用改，而且里面不发生任何计算**——它只是在建图。[【跳转到 19:59】](https://www.youtube.com/watch?v=Oo07fFb-aH0&t=1199)

### 4.4 HLO 长什么样：一个 MNIST 层

HLO 是给编译器看的，不是给人看的。视频里给了一个完整的例子，其实就是"reshape → 矩阵乘 → 加偏置 → ReLU"：

![HLO/StableHLO 形式的 MNIST 单层：`stablehlo.reshape`、`stablehlo.dot`、`stablehlo.add`、`stablehlo.maximum` 四步](assets/从%20XLA%20到%20PyTorch%202：编译器如何接管一张计算图（1）XLA%20与它的输入%20HLO/01324.webp)

读法很朴素：输入是 28×28 的图像、784×10 的权重、10 维的偏置；`reshape` 把图像拉平成 784 维；`dot` 乘权重；`add` 加偏置；`maximum` 和一个 0 常量比较，把负数压到 0——这就是 ReLU。[【跳转到 22:04】](https://www.youtube.com/watch?v=Oo07fFb-aH0&t=1324)

注意这里出现的算子名是 `stablehlo.*` 而不是 `xla.*`，这就是下一节要讲的 OpenXLA 带来的变化。

## 五、OpenXLA：把 XLA 从 TensorFlow 里拆出来

### 5.1 为什么要拆

设备越来越多：新的 GPU 厂商、Graphcore 和 AWS 这类自研加速器、各种 CPU。如果 XLA 只长在 TensorFlow 里，其他框架和芯片厂商都用不上它。

### 5.2 拆成什么样

2022 年发起的 **OpenXLA** 做了两件事：[【跳转到 24:09】](https://www.youtube.com/watch?v=Oo07fFb-aH0&t=1449)把 XLA 编译器和 HLO 规范都变成独立项目，搬进 GitHub 上的 OpenXLA 组织；同时明确 **StableHLO 是 OpenXLA 的输入格式**。

![OpenXLA 的三段式架构：TensorFlow / PyTorch / JAX 都先降到 StableHLO，再经与目标无关的优化器，最后交给各硬件厂商的优化与代码生成](assets/从%20XLA%20到%20PyTorch%202：编译器如何接管一张计算图（1）XLA%20与它的输入%20HLO/01499.webp)

这张图把 XLA 的定位讲得最清楚，从上到下三段：

1. **前端框架**：TensorFlow、PyTorch、JAX 三个完全不同的框架，**共同的下游接口就是 StableHLO**；
2. **与目标无关的优化器**（Target-independent Optimizer）：代数化简、算子/内核融合、权重更新分片、全图布局传播、调度、SPMD 并行。这一段不关心你最终跑在什么芯片上；
3. **硬件优化与目标**：AWS Trainium/Inferentia、AMD GPU、Arm CPU、Google TPU、Graphcore IPU、NVIDIA GPU……这一段由芯片厂商各自实现。

也就是说，**XLA 的"输入"在工程上已经收敛为一个格式：StableHLO**。谁想接入 XLA 生态，谁就把自己的图降到 StableHLO。[【跳转到 25:24】](https://www.youtube.com/watch?v=Oo07fFb-aH0&t=1524)

### 5.3 落到真实硬件：同一套 API 换一个 SDK

视频用 AWS Inferentia 2 演示了这套抽象有多薄：把 `torch_xla` 换成厂商的 `torch_neuronx`，其余代码几乎逐字相同。

![在 Inferentia 2 上跑 PyTorch/XLA：多一行导入厂商 SDK（torch_neuronx），硬件与 SDK 的细节被 torch_xla 的 API 吸收掉](assets/从%20XLA%20到%20PyTorch%202：编译器如何接管一张计算图（1）XLA%20与它的输入%20HLO/01604.webp)

Habana 的 Gaudi 2 也是同一套写法，只是把 SDK 换掉。这就是 OpenXLA 想要的效果：**框架侧只认 StableHLO，硬件侧只认自己的后端编译器，中间那层由 XLA 统一**。[【跳转到 26:29】](https://www.youtube.com/watch?v=Oo07fFb-aH0&t=1589)

## 六、把 XLA 放回三种编译器的坐标系里

本小节要比较的是 XLA、TorchInductor、TVM 三者的定位与输入。看完这一篇，XLA 这一格可以先填上：

| 维度 | XLA |
| --- | --- |
| 定位 | 图级优化器 + 设备代码生成器；跨框架的编译后端 |
| 输入 | 一张完整的静态计算图，工程上收敛为 **StableHLO / HLO** |
| 图从哪来 | TensorFlow 的 graph mode 直接产出；PyTorch 靠 `torch_xla` 的懒张量 tracing 追出来；JAX 天然产出 |
| 中间表示 | HLO / StableHLO（与目标无关的优化在这一层做） |
| 后端与目标 | CPU、GPU、TPU，以及通过厂商 SDK 接入的自研加速器（Inferentia、Gaudi 等） |
| 典型适用场景 | 静态形状为主、要跨多种加速器部署、希望"框架无关"地复用同一套编译后端；尤其适合 TPU 这类非 NVIDIA 硬件 |
| 主要代价 | 需要先有图：eager 框架要靠 tracing 补出图；动态形状、数据相关的控制流是天然难点 |

一句话概括它与另外两者的差别：**XLA 站在"整张图"这一层，输入是 StableHLO，目标是让同一张图能落到尽可能多的硬件上**。TorchInductor 则站在"PyTorch 的图"这一层，输入是 Dynamo 追出来的 FX 图；TVM 站在"算子/循环"这一层，输入是用索引表达式写成的张量描述。这三层的分工，正是下一篇和 TVM 那篇要展开的内容。

## 小结

- XLA 出现的前提是 **define-then-run 的静态图**：图完整可见，才有"按形状特化、融合算子、预分配内存"的空间。
- XLA 的四项职责是：**按真实维度与 dtype 特化 → 消除冗余并融合 → 生成设备相关机器码**；流程上分前端（图级、与设备无关）与后端（代码生成）两段。
- 编译时机有 **JIT** 与 **AOT** 两种，生产部署一般选 AOT。
- PyTorch 阵营先有 **TorchScript**（静态类型子集 + 只含底层原语的 IR），但它不支持动态形状与非 PyTorch 代码，已进入维护模式。
- **PyTorch/XLA 用 lazy tensor 把 eager 代码的图追出来**，链路是 tracing → lowering 成 HLO → 编译 → 在设备上执行，用户代码几乎不用改。
- **OpenXLA 把 XLA 与 HLO 从 TensorFlow 里拆出来**，StableHLO 成为统一输入格式，硬件厂商各自接后端。
- 定位上一句话：**XLA 是"整张图"这一层的编译器，输入 StableHLO，卖点是跨硬件**。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| define-then-run / graph mode | 先完整定义一张执行图，再整张图运行；TensorFlow 1.x 的写法 |
| define-by-run / eager mode | 写一行算一行，算子立刻执行；PyTorch 默认行为 |
| XLA | Accelerated Linear Algebra，分析并优化整张图、再生成设备原生代码的编译器 |
| HLO | High-Level Operations，XLA 的中间表示，描述"对张量做什么" |
| StableHLO | HLO 的可移植子集，OpenXLA 规定的统一输入格式，TensorFlow/PyTorch/JAX 都往它下降 |
| lowering（下降） | 把高层表示翻译成更低层表示的过程，如 IR → HLO、HLO → 机器码 |
| lazy tensor（懒张量） | 不立刻求值的张量，用于在 eager 框架里把算子记录下来拼成图 |
| tracing（追踪） | 跑一遍代码、记录所有算子以还原计算图的技术 |
| JIT / AOT | 即时编译（运行时才编译）/ 提前编译（先编译成产物再部署） |
| TorchScript | Python 的静态类型子集，PyTorch 早期的图导出方案，现已进入维护模式 |