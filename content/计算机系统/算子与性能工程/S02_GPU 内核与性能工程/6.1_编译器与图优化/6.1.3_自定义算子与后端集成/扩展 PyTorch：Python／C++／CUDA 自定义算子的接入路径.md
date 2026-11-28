# 扩展 PyTorch：Python／C++／CUDA 自定义算子的接入路径

> 视频来源：[Lightning Talk: Extending PyTorch with Custom Python/C++/CUDA Operators](https://www.youtube.com/watch?v=LI3h8aVchwo)（YouTube · Richard Zou, Meta · PyTorch Conference 2024）｜时长约 8.5 分钟
> 导读：这是一支只有 8 分半的闪电演讲，但把"内核（kernel）"和"算子（operator）"的分界线讲得最清楚：**为什么裸 kernel 接不进 `torch.compile`，而算子可以**。本文按视频顺序讲三条接入路径——Python 算子、C++ 算子、Triton kernel——以及每一步必须补的那几块胶水。字幕为本地 Whisper 转写，术语按上下文订正（演讲中的 "Trident" 即 Triton）。

## 本讲要解决的核心问题（SCQA）

**背景**：PyTorch 自带两千多个算子，但总有一个计算是你必须自己写的：新的激活函数、融合过的 attention、某个第三方库里的图像操作。你把它写成一个函数或一个 CUDA kernel，在 eager 模式下跑得好好的。

**冲突**：一旦你想用 `torch.compile` 加速整个模型，这个裸 kernel 就成了图里的一个"黑洞"——编译器既不知道它的输出形状，也不知道怎么对它求导。视频里说得很直白：**如果你只写了一个裸 kernel，想让它和 `torch.compile` 配合是有点困难的。**

**疑问**：那么，一个自己写的 kernel 要补上哪些东西，才能被 PyTorch 的编译器、autograd、`torch.export` 这些子系统"看见"？

**回答（中心思想）**：你需要把它从 **kernel** 升级成 **operator**。kernel 只负责"用数据指针算出结果"，operator 则是**一层胶水代码**：它告诉 PyTorch 这次计算的签名与语义，再调用一个或多个 kernel 去干活。这层胶水由三部分组成——**名字与 schema、fake/meta kernel（形状推断）、autograd 公式**。补齐这三样，你的 kernel 才真正接入 PyTorch 生态。而如果你用的是 Triton kernel，结论要反过来：**它开箱即用就能和 `torch.compile` 配合，不需要包成算子。**

## 一、先分清两个词：kernel 与 operator

这是全篇的地基，混淆了后面全乱。

### 1.1 kernel：拿数据指针做计算的函数

视频给的定义是：**kernel 是一个用原始数据指针完成计算的函数**。它可以是：

- **C / C++ / CUDA kernel**：拿到张量的数据指针，直接读写那块显存；
- **Python 库**：本质是 C++ 库的 Python 绑定，NumPy 是一个例子，Pillow（图像操作）是另一个；
- **Triton kernel**：用 Python DSL 写，编译成 CUDA kernel。

![Kernels 的定义与三类例子：C/C++/CUDA、Python 库（Pillow、NumPy）、Triton kernels](assets/扩展%20PyTorch：Python／C++／CUDA%20自定义算子的接入路径/00035.webp)

为什么大家还想自己写 kernel？因为 PyTorch 虽然算子很多，但**要真正掌控硬件性能，你往往得自己写一个 kernel**。[【跳转到 00:35】](https://www.youtube.com/watch?v=LI3h8aVchwo&t=35)

### 1.2 operator：让 kernel 能被 PyTorch 子系统"看见"的那层胶水

**算子是一层胶水代码**：它把"这里有一次计算"这件事告诉 PyTorch，然后调用一个或多个 kernel 去真正完成计算。胶水的价值不在于算得快，而在于**接入**——它让自定义算子能和你已经在用的 PyTorch 子系统组合：

- `torch.compile`（图捕获与编译）
- `torch.export`（导出）
- `autograd`（自动微分）
- `vmap`、张量子类（Tensor subclass）等

![Operators 的定义：胶水代码 + 调用 1 个以上 kernel，从而与 torch.compile、torch.export、autograd、vmap、Tensor subclass 组合](assets/扩展%20PyTorch：Python／C++／CUDA%20自定义算子的接入路径/00110.webp)

一句话记住分工：**kernel 决定"算得多快"，operator 决定"能不能被组合"。**[【跳转到 01:25】](https://www.youtube.com/watch?v=LI3h8aVchwo&t=85)

### 1.3 按 kernel 类型选 API

视频给了一张对照表，这是整篇的路线图：

| kernel 类型 | 和 `torch.compile` 配合需要注册算子吗 | 和其它子系统配合需要注册算子吗 | 注册 API |
| --- | --- | --- | --- |
| C / C++ / CUDA | 需要 | 需要 | C++ 的 `TORCH_LIBRARY` |
| Python | 需要 | 需要 | `torch.library.custom_op`（PT 2.4+） |
| Triton | **不需要**（PT 2.3+） | 需要 | `torch.library.custom_op`（PT 2.4+） |

![Custom Operator Registration APIs：C++/CUDA 与 Python 都必须注册算子才能和 torch.compile 配合，Triton 在 PT2.3+ 之后不必](assets/扩展%20PyTorch：Python／C++／CUDA%20自定义算子的接入路径/00135.webp)

这张表最容易被忽略的是最后一列：**Triton kernel 在"和 torch.compile 配合"这一格是"不需要"，但在"和其它子系统配合"这一格仍然是"需要"**。这就是后面第四节那条"建议反过来"的由来。

## 二、路径一：Python kernel → `torch.library.custom_op`

### 2.1 一个"不是算子"的函数长什么样

演讲用的例子是 Pillow 的 `crop`：把张量转成 Pillow 图像、裁剪、再转回张量。

```python
import torch
from torchvision.transforms.functional import to_pil_image, pil_to_tensor

def crop(pic, box):
    img = to_pil_image(pic.cpu())
    cropped_img = img.crop(box)
    return (pil_to_tensor(cropped_img) / 255.).to(pic.device, pic.dtype)
```

![一个普通的 crop 函数：把张量转成 Pillow 图像、裁剪、再转回张量——它还不是算子](assets/扩展%20PyTorch：Python／C++／CUDA%20自定义算子的接入路径/00165.webp)

这个函数能跑，但**它不能和 `torch.compile`、autograd 或其它子系统配合**。原因很朴素：它只是一个 Python 函数，PyTorch 不知道它的算子身份，也就无从在图上为它安排位置。[【跳转到 02:20】](https://www.youtube.com/watch?v=LI3h8aVchwo&t=140)

### 2.2 加一个装饰器，再补三样东西

把它变成算子只需要加一个装饰器，但要真正跑通，**还得补三样东西**：

```python
@torch.library.custom_op("mylib::crop", mutates_args=())
def crop(pic: torch.Tensor, box: Sequence[int]) -> torch.Tensor:
    img = to_pil_image(pic.cpu())
    cropped_img = img.crop(box)
    return (pil_to_tensor(cropped_img) / 255.).to(pic.device, pic.dtype)
```

![用 torch.library.custom_op 装饰 crop：算子名 mylib::crop、mutates_args=()、以及完整的类型标注](assets/扩展%20PyTorch：Python／C++／CUDA%20自定义算子的接入路径/00190.webp)

三样东西分别是：

1. **名字**：PyTorch 里所有自定义算子都必须有名字，形如 `mylib::crop`（命名空间 + 算子名）。
2. **`mutates_args`**：告诉 PyTorch 这个算子会**原地修改**哪些输入。上面写成 `()`，意思是纯函数、不改输入。这一点对和 PyTorch 子系统对接很重要——编译器要靠它判断能不能安全地重排、复用输入。
3. **类型标注**：参数写清 `pic: torch.Tensor, box: Sequence[int]`，返回值写清 `-> torch.Tensor`。**标注不是装饰，它就是 schema**：`torch.compile` 和 `torch.export` 靠它知道这个算子的输入输出是什么类型。

[【跳转到 02:45】](https://www.youtube.com/watch?v=LI3h8aVchwo&t=165)

### 2.3 让 `torch.compile` 认识它：写一个 fake kernel

这是最容易漏、也最容易被问到的一步。

`torch.compile` 的工作方式是：拿一个 Python 函数做**图捕获（graph capture）**，产出一张图。为了抓图，它必须在**没有真实张量**的情况下把你的函数跑一遍——用的是 **fake tensor（假张量）**：形状、dtype、device 都真，就是没有数据。

于是问题变成：**给定一个某种形状的假输入，你的算子输出该是什么形状？** 编译器必须知道答案，才能继续往下排布后续算子。

答案是用 `torch.library.register_fake`（视频里也把它叫 meta kernel / meta 函数）注册一条形状推断规则：

```python
@crop.register_fake
def _(pic, box):
    channels = pic.shape[0]
    x0, y0, x1, y1 = box
    return pic.new_empty(channels, y1 - y0, x1 - x0)
```

![用 register_fake 注册形状推断：从输入张量的 shape 和 box 直接算出输出形状，不需要真的分配数据](assets/扩展%20PyTorch：Python／C++／CUDA%20自定义算子的接入路径/00220.webp)

注意这个函数**只做形状算术**：`channels` 来自输入，高宽来自 box 的差值，用 `new_empty` 造一个同 dtype/device 的空张量占位。它不会真的裁剪任何像素。[【跳转到 04:05】](https://www.youtube.com/watch?v=LI3h8aVchwo&t=245)

> **常见坑**：如果你的 fake kernel 算出的形状和真实 kernel 不一致，`torch.compile` 会在后续算子处报形状不匹配，或者更糟——静默算出错误结果。形状推断必须和真实实现严格对齐。

### 2.4 让 autograd 认识它：`register_autograd` 优先于 `autograd.Function`

自定义算子要和自动微分配合，有两条路：

- **传统做法**：在 Python 里写一个 `torch.autograd.Function`，指定 `forward` 和 `backward`；
- **新 API**：`torch.library.register_autograd`，给定一个已有算子，补上它的前向与反向。

`register_autograd` 接收两样东西：

1. 一个 **setup context** 的函数：建立 context 对象，把反向需要的东西存下来；
2. 一个 **backward 函数**：拿到梯度、拿到你存的 context，真正执行反向。

```python
@torch.library.custom_op("mylib::paste", mutates_args=())
def paste(...): ...

def setup_context(ctx, inputs, output):
    pic, box = inputs
    ctx.coords = box[:2]
    ctx.pic_shape = pic.shape

def backward(ctx, grad_output):
    grad_input = grad_output.new_zeros(ctx.pic_shape)
    grad_input = paste(grad_input, grad_output, ctx.coords)
    return grad_input, None

crop.register_autograd(backward, setup_context=setup_context)
```

![用 register_autograd 给自定义算子补反向：setup_context 存下反向需要的坐标与形状，backward 里用另一个算子把梯度"贴"回原图](assets/扩展%20PyTorch：Python／C++／CUDA%20自定义算子的接入路径/00264.webp)

**为什么推荐 `register_autograd` 而不是 `autograd.Function`？** 视频给了三条理由，都是实战经验：

1. 当你想和 `torch.compile` 组合时，`torch.autograd.Function` 会暴露出**可组合性上的限制**；
2. `register_autograd` 和 `torch.compile` 配合得更好；
3. `torch.autograd.Function` 时不时会把人带进一些**诡异的、静默的错误结果**，而这些在 PyTorch 框架层面很难修。

[【跳转到 05:14】](https://www.youtube.com/watch?v=LI3h8aVchwo&t=314)

## 三、路径二：C++ / CUDA kernel → `TORCH_LIBRARY`

如果你的 kernel 本来就是 C++ 写的，注册成算子也有 C++ 侧的 API，思路和 Python 完全对应：**先声明 schema，再按 dispatch key 注册实现**。

```cpp
TORCH_LIBRARY(mylib, m) {
  m.def("crop(Tensor pic, int[] box) -> Tensor");
}

Tensor crop_cpu(const Tensor& pic, IntArrayRef box) {
  // ...
}

TORCH_LIBRARY_IMPL(mylib, CPU, m) {
  m.impl("crop", &crop_cpu);
}
```

![C++ 侧注册：TORCH_LIBRARY 声明 schema，TORCH_LIBRARY_IMPL 按 dispatch key（这里是 CPU）挂上具体实现](assets/扩展%20PyTorch：Python／C++／CUDA%20自定义算子的接入路径/00389.webp)

两个结构值得注意：

- `m.def("crop(Tensor pic, int[] box) -> Tensor")` 这一行就是 **schema**，和 Python 侧的类型标注是一回事；
- `TORCH_LIBRARY_IMPL` 里的 `CPU` 是 **dispatch key**（分派键）。PyTorch 的 dispatcher 会根据输入张量所在的设备/布局把调用路由到对应实现——所以同一个算子可以同时有 CPU、CUDA 甚至 Meta（形状推断）几份实现。

**Python 还是 C++ 注册？** 视频的答案是：**看哪种你写起来更顺手**。kernel 写在 C++ 里，注册既可以在 Python 里用 `torch.library.custom_op` 包一层，也可以在 C++ 里用 `TORCH_LIBRARY`，两者等价。[【跳转到 06:04】](https://www.youtube.com/watch?v=LI3h8aVchwo&t=364)

> 本系列下一篇《2026 年怎么写好一个 PyTorch C++ 扩展》会把这套 C++ 注册流程完整走一遍，并讲清 ABI 稳定、`TORCH_BOX` 与打包。

## 四、路径三：Triton kernel —— 建议反过来

前面两条路的结论都是"请把 kernel 包成算子"，但 **Triton kernel 是个特例，结论正好相反**。

一个 Triton kernel 长这样（官方教程里的 add kernel）：

```python
@triton.jit
def add_kernel(in_ptr0, in_ptr1, out_ptr, numel, BLOCK_SIZE: "tl.constexpr"):
    pid = tl.program_id(axis=0)
    block_start = pid * BLOCK_SIZE
    offsets = block_start + tl.arange(0, BLOCK_SIZE)
    mask = offsets < numel
    x = tl.load(in_ptr0 + offsets, mask=mask)
    y = tl.load(in_ptr1 + offsets, mask=mask)
    output = x + y
    tl.store(out_ptr + offsets, output, mask=mask)

@torch.compile(fullgraph=True)
def add_fn(x, y):
    output = torch.zeros_like(x)
    numel = output.numel()
    grid = lambda meta: (triton.cdiv(numel, meta["BLOCK_SIZE"]),)
    add_kernel[grid](x, y, output, numel, BLOCK_SIZE=4)
    return output
```

![Triton 的 add kernel 与它的调用方：kernel 用 triton.jit 写，调用方直接 torch.compile——中间没有自定义算子](assets/扩展%20PyTorch：Python／C++／CUDA%20自定义算子的接入路径/00414.webp)

**它能开箱即用地和 `torch.compile` 配合**，所以视频说：没有任何理由把用户自定义的 Triton kernel 再包一层自定义算子。[【跳转到 06:54】](https://www.youtube.com/watch?v=LI3h8aVchwo&t=414)

### 4.1 什么时候仍然要包一层

Triton kernel 也不是万能的。视频给了一张很实用的能力对照表：

| 能力 | 裸 Triton kernel（PT 2.3+） | 用 `torch.library.custom_op` 包一层（PT 2.4+） |
| --- | --- | --- |
| eager 模式可用 | 是 | 是 |
| 支持 `torch.compile` | 大多数情况 | 所有情况 |
| 支持张量子类、`torch.vmap` 等 | 否 | 是 |

![裸 Triton kernel 与包成 custom_op 的能力对照：compile 覆盖度与张量子类/vmap 支持是分水岭](assets/扩展%20PyTorch：Python／C++／CUDA%20自定义算子的接入路径/00453.webp)

所以判据很清楚：**如果你只需要 eager + `torch.compile`，直接用 Triton kernel；如果你需要和 autograd、张量子类、`vmap` 这些完整组合，就在 Triton kernel 外面套一个自定义算子装饰器。**[【跳转到 07:08】](https://www.youtube.com/watch?v=LI3h8aVchwo&t=428)

## 五、结论：默认写算子，Triton 例外

演讲最后把建议浓缩成两句话，值得贴在墙上：

![Takeaways：非 Triton 的 Python/C++/CUDA kernel 优先写成算子；Triton kernel 直接用，它是 CUDA kernel 的可改、可移植替代](assets/扩展%20PyTorch：Python／C++／CUDA%20自定义算子的接入路径/00478.webp)

**对非 Triton 的 Python / C++ / CUDA kernel**：

- **优先写成算子，而不是丢一个裸 kernel 出去**，尤其是当你在写一个库的时候；
- 在 Python 里就用 `torch.library.custom_op` 把 kernel 包成算子。

**对 Triton kernel**：

- 它开箱即用就能和 `torch.compile` 配合；
- 它是 CUDA kernel 的一个**好改（hackable）且高性能**的替代品——不用碰 C++ 就能拿到 CUDA kernel 级别的性能。

视频里那句"如果你在写一个满是自定义算子的库，后来的人看到的是一个算子而不是一个裸 kernel，会容易得多"，说的其实是**可组合性就是可维护性**：算子是有名字、有 schema、有形状推断、有梯度的对象，别人（和编译器）都能理解它；裸 kernel 只是一个黑盒。[【跳转到 07:58】](https://www.youtube.com/watch?v=LI3h8aVchwo&t=478)

## 小结

- **kernel 与 operator 是两个层次**：kernel 用数据指针算结果，operator 是让这次计算能被 `torch.compile`、autograd、`torch.export` 组合的胶水。
- **Python kernel 的接入 = 一个装饰器 + 三样东西**：算子名、`mutates_args`、类型标注（即 schema）。
- **`torch.compile` 靠 fake kernel 抓图**：用 `register_fake` 告诉编译器"给定这个形状的输入，输出是什么形状"，只做形状算术，不碰数据。
- **autograd 优先用 `register_autograd`**：它和 `torch.compile` 组合更好，也避开了 `autograd.Function` 那些静默错误。
- **C++ 侧是同一套逻辑的另一种写法**：`TORCH_LIBRARY` 声明 schema，`TORCH_LIBRARY_IMPL` 按 dispatch key 挂实现。
- **Triton kernel 是例外**：开箱即用支持 `torch.compile`，不要多此一举；只有需要 autograd / 张量子类 / `vmap` 时才包成算子。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| kernel（内核） | 用原始数据指针完成计算的函数，可以是 CUDA、C++、Python 库或 Triton |
| operator（算子） | 告诉 PyTorch "这里有一次计算"并调用 kernel 的胶水代码，是接入各子系统的单位 |
| schema | 算子的签名声明，如 `crop(Tensor pic, int[] box) -> Tensor`；Python 里由类型标注承担 |
| `mutates_args` | 声明算子会原地修改哪些输入；纯函数写 `()` |
| fake tensor | 有形状/dtype/device 但没有数据的假张量，`torch.compile` 抓图时用它跑函数 |
| meta kernel / `register_fake` | 只做形状推断的实现，告诉编译器输出形状 |
| `register_autograd` | 给已有算子补前向/反向的新 API，比 `torch.autograd.Function` 更适配 `torch.compile` |
| dispatch key | 分派键，dispatcher 据此把调用路由到 CPU / CUDA / Meta 等具体实现 |
| Triton | 用 Python DSL 写 GPU kernel 的语言，编译成 CUDA kernel |
| `torch.compile` | PyTorch 2 的编译入口，负责图捕获 + 后端编译 |