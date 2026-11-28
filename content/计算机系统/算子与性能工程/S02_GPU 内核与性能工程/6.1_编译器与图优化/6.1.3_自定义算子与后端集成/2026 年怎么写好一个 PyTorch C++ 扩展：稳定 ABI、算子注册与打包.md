# 2026 年怎么写好一个 PyTorch C++ 扩展：稳定 ABI、算子注册与打包

> 视频来源：[How To Write C++ Extensions in 2026](https://www.youtube.com/watch?v=v2LcTzpUOYU)（YouTube · Jane Xu & Mikayla Gawarecki, Meta · PyTorch Conference Europe 2026）｜时长约 24 分钟
> 导读：这是本小节里最"能照着做"的一支：两位 PyTorch 工程师从"为什么要写 C++ 扩展"讲到"怎么只打一个 wheel 就能跨多个 torch 与 Python 版本"，中间把 `torch::stable::Tensor`、`STABLE_TORCH_LIBRARY`、`TORCH_BOX`、`TORCH_TARGET_VERSION`、`Py_LIMITED_API` 这些名词全部落到代码上。字幕为 YouTube 自动字幕，术语按上下文订正。

## 本讲要解决的核心问题（SCQA）

**背景**：你在 PyTorch 里写了一个自定义算子，用 `torch.utils.cpp_extension` 编译成 `.so`，在本地跑得好好的。这套流程很多人都会：include 一堆 `torch/extension.h`，写 `TORCH_LIBRARY`，`setup.py` 里 `CUDAExtension`，编译，`torch.ops.mylib.myop` 调用。

**冲突**：一旦你要把它**发出去**，问题就来了。libtorch 是持续演进的——视频里把它画成一座"锯齿状的山"，锯齿意味着它一直在动。你依赖它，就得跟着它动：**libtorch 一变，你就得重新编译扩展**。而现实里还有第二个维度：Python 版本。于是你要为 "torch 2.10 × Python 3.10"、"torch 2.10 × Python 3.11"、"torch 2.11 × Python 3.10"……各打一个 wheel，构建矩阵是 $O(M \times N)$。

**疑问**：能不能只构建**一个**二进制，让它跨多个 torch 版本、多个 Python 版本都能跑？如果能，写代码时要注意什么、编译时要注意什么、Python 侧又该怎么加载？

**回答（中心思想）**：能，靠**两个维度的 ABI 稳定**——libtorch 侧用 **stable ABI**（C shim + 高层 C++ 封装 + header-only 三类头文件），CPython 侧用 **`Py_LIMITED_API`**。代价是：你只能用 stable 头文件里那个**有限的子集**，注册算子要改用 `STABLE_TORCH_LIBRARY` 并把实现用 `TORCH_BOX` 包一层，编译时要传 `TORCH_TARGET_VERSION` 让编译器帮你把关。做完这些，$O(M \times N)$ 个 wheel 变成 1 个。

## 一、先回答"为什么要写 C++ 扩展"

视频一开头就把问题拆成两个，这个拆法值得学：

**问题一：什么时候你会想扩展 PyTorch？**
当你在用 PyTorch，然后发现"我有个想自己写的算子，它不在这两千多个内置算子里"。视频说这种情况**比你想象的多**。

**问题二：为什么用 C++，而不是 Python？**
技术上用 Python 扩展 PyTorch 非常容易——用 Triton、用别的 DSL、甚至用别的 torch 算子拼出来都行。选 C++ 的理由是：

- 要**针对特定硬件**；
- 要用某些**对自己这个场景性能更好的启发式策略**；
- 或者你就是喜欢写 C++（视频原话："这也完全成立"）。

而无论用哪种方式扩展，你通常还希望**继续用 torch 的其它部分**：autograd、PT2、`torch.compile`、以及和 PyTorch 其它算子协同工作。这句话是本篇的隐含主线——**扩展的价值在于"还能和剩下的东西一起用"**。[【跳转到 00:29】](https://www.youtube.com/watch?v=v2LcTzpUOYU&t=29)

## 二、例子：一个 fused multiply add

全篇用一个极简例子贯穿：$C = A \odot B + c$，即两个张量逐元素相乘再加一个标量。

约定（很重要，因为它决定了后面代码有多简单）：**不管 A、B 长什么样，都返回一个 out-of-place 的连续结果**——即使 A 不连续，也新分配一块内存返回连续的答案。

视频自己承认"fused multiply add 不是什么新功能"，但正因为简单，才能把 ABI、注册、打包这些"与算法无关"的工程问题看清楚。[【跳转到 01:44】](https://www.youtube.com/watch?v=v2LcTzpUOYU&t=104)

## 三、libtorch 的三层头文件：你只能用绿色的那些

### 3.1 那张"锯齿山"图

![libtorch 的三层结构：绿色是 ABI 稳定的部分（header-only API、高层 C++ 封装、C shim），橙色是仍在演进的 libtorch 本体](assets/2026%20年怎么写好一个%20PyTorch%20C++%20扩展：稳定%20ABI、算子注册与打包/00204.webp)

这张图是全篇的地图，从下往上看：

1. **ABI stable C shim**（橙色斜纹那层）：用 C 写的稳定接口。它把所有"锯齿"挡在外面——我们承诺**即使 libtorch 底层在变，这个 C shim 保持不变**。
2. **高层 C++ 封装**（住在 `torch/csrc/stable`）：因为 C 写起来不舒服，所以在 C shim 之上做了一层 C++ 封装。比如你熟悉的 ATen `Tensor`，在 `torch::stable` 里有对应的 `torch::stable::Tensor`，语义看起来很像，"使用体验应该还过得去"。
3. **header-only API**（左边绿色那列）：`dtype`、`device type` 这类**完全用头文件实现**的东西，不依赖 `libtorch.so`，因此 libtorch 动的时候它们也不动。

**结论：只要能用，就用 ABI stable 的 libtorch API。** 理由很实际：libtorch 一变你不想每次都重新更新扩展，"那要重新打的 wheel 太多了"。[【跳转到 03:24】](https://www.youtube.com/watch?v=v2LcTzpUOYU&t=204)

### 3.2 为什么 ABI 稳定能省掉一个维度

![Why ABI stability：横轴 torch 版本、纵轴 Python 版本，不稳定时要为每个格子打一个 Binary](assets/2026%20年怎么写好一个%20PyTorch%20C++%20扩展：稳定%20ABI、算子注册与打包/00372.webp)

这张格子图把成本说清楚了：**每个 (Python 版本, torch 版本) 组合都要一个二进制**。而视频提醒，真实维度比两个还多——还有 CUDA 版本、不同架构。

有了 libtorch 的稳定性，你可以把"每个版本一个二进制"变成"所有版本共用一个二进制"，**消掉一个轴**：从 $O(M \times N)$ 变成 $O(N)$。后面再加 `Py_LIMITED_API` 消掉第二个轴，就变成 1 个。

具体到数字：**对 PyTorch 2.10、2.11、2.12，你只需要构建一个 wheel，而不是三个。** 注意这是 2.10 以上才有的能力。[【跳转到 05:04】](https://www.youtube.com/watch?v=v2LcTzpUOYU&t=304)

### 3.3 只能 include 这几个头文件

![LibTorch ABI stable 扩展只能 include 三类头文件；左边那列（ATen/Operators.h、torch/all.h、torch/library.h……）会让扩展失去稳定性](assets/2026%20年怎么写好一个%20PyTorch%20C++%20扩展：稳定%20ABI、算子注册与打包/00447.webp)

视频把这件事做简单了：**你能 include 的东西只有三样**（严格说是四样，因为有两个 shim）：

- `torch/csrc/stable`：`torch::stable::Tensor`、`torch::stable::Device`；
- `torch/headeronly`：`torch::headeronly::ScalarType` 这类工具；
- `torch/csrc/stable/c/shim.h`（或 inductor/aoti 那份 `c/shim.h`）。

而下面这些**不能再用**：`ATen/Operators.h`、`torch/all.h`、`torch/library.h`、`ATen/cuda/CUDAContext.h`……

**这不是靠自觉，是靠编译器强制**：只要设了 `TORCH_TARGET_VERSION` 这个编译选项，写错就会在编译期报错。视频强调"我们尽量让你尽早拿到信号"。[【跳转到 07:02】](https://www.youtube.com/watch?v=v2LcTzpUOYU&t=422)

## 四、把 kernel 写出来：schema → 检查 → CUDA → 指针与 stream

这一节是"照着写"的部分，顺序很值得记。

### 4.1 先写 schema

大多数算子都要定义 schema，所以**值得先想清楚**。这个例子里很简单：输入两个张量，返回一个张量。

两个细节：

- 一开始就用 `torch::stable::Tensor`，别用 ATen 的 `Tensor`；
- 标量用 `double` 表示 float——"ATen 就是这么处理的，别问我太多为什么"。

视频还强调了一句：这些东西**都有文档**，你应该能直接 Google 到。[【跳转到 07:27】](https://www.youtube.com/watch?v=v2LcTzpUOYU&t=447)

### 4.2 加检查：代码应该"看起来眼熟"

第二步是加输入检查。视频的用意不是教你写 check，而是让你放心：**stable 世界里的代码不该像外星代码**。

- `torch::check` 就是标准的 torch check；
- 你仍然可以调 `.sizes`、`.scalar_type`，可以取 float、可以判断是不是 CUDA；
- 这里检查的是：A 和 B 尺寸相同、都是 float、都在 CUDA 上。

如果你问"我怎么知道有哪些 API 可用"——答案还是在 C++ 文档里。[【跳转到 08:17】](https://www.youtube.com/watch?v=v2LcTzpUOYU&t=497)

### 4.3 写 CUDA：因为假定连续，数学就很轻松

kernel 本身是"非常基础的 CUDA"（视频原话：这不是 PyTorch 内部那种 CUDA，但够用）。因为前面约定了所有张量都是连续的：

- 张量当成 `float*`，那个标量就是 `float`，结果也写进一个 `float*`；
- 数学就是 `A[i] * B[i] + c`。

CUDA 那套 `blockIdx` / `blockDim` / `threadIdx` 的索引计算，视频说"这次分享你不需要完全看懂"——你可以就把它理解成**在三个连续数组上做数学**。调用 kernel 时传的是 CUDA launch params：grid size、block size、shared memory、stream。[【跳转到 09:32】](https://www.youtube.com/watch?v=v2LcTzpUOYU&t=572)

### 4.4 准备指针：`const_data_ptr` 与 `mutable_data_ptr`

真正把参数凑齐时，有几个点值得记：

- **先调 `contiguous()`**：约定是返回连续结果，所以输入要先连续化。stable ABI 也提供了 aten 算子，所以 `contiguous`、`empty_like` 这些都能用；
- **只读的用 `const_data_ptr`**（A、B），**要写的用 `mutable_data_ptr`**（结果）；
- `numel` 就是 `numel`，很简单；
- **stream 的获取看起来有点乱**——视频自己承认："这正是'如果你想走我们的 shim'的样子，它是 C 写的，所以不太好看，我们也会把它改好，今天这是唯一的做法。"

一句话总结这段：**你想要的这些 API 都支持；如果不支持，告诉他们。**[【跳转到 11:12】](https://www.youtube.com/watch?v=v2LcTzpUOYU&t=672)

## 五、注册到 dispatcher：`STABLE_TORCH_LIBRARY` + `TORCH_BOX`

写完 kernel 只是"能算"，还没"能被 PyTorch 调用"。要注册到 dispatcher，视频给了完整代码：

```cpp
STABLE_TORCH_LIBRARY(extension_cpp_stable, m) {
  m.def("mymuladd(Tensor a, Tensor b, float c) -> Tensor");
}

STABLE_TORCH_LIBRARY_IMPL(extension_cpp_stable, CUDA, m) {
  m.impl("mymuladd", TORCH_BOX(&mymuladd_cuda));
}
```

![用 STABLE_TORCH_LIBRARY 声明 schema、STABLE_TORCH_LIBRARY_IMPL 按 CUDA 这个 dispatch key 挂实现，实现要用 TORCH_BOX 包一层](assets/2026%20年怎么写好一个%20PyTorch%20C++%20扩展：稳定%20ABI、算子注册与打包/00772.webp)

和旧的（ABI 不稳定的）写法相比，只有**两处不同**：

1. 头文件从 `torch/library.h` 换成 `stable/torch/library.h`，宏从 `TORCH_LIBRARY` 换成 `STABLE_TORCH_LIBRARY`；
2. **传给 `_IMPL` 的实现必须用 `TORCH_BOX` 宏包一层**。

注册完、编译好，Python 侧就能这样调用：

```python
torch.ops.extension_cpp_stable.mymuladd.default(a, b, c)
```

### 5.1 为什么要 `TORCH_BOX`

![TORCH_BOX 展开后的 boxed 函数：从 StableIValue 栈取出参数、调用真实 kernel、再把结果 from 回 StableIValue 放回栈上](assets/2026%20年怎么写好一个%20PyTorch%20C++%20扩展：稳定%20ABI、算子注册与打包/00822.webp)

原来的函数签名是 `(Tensor, Tensor, float)`，`TORCH_BOX` 把它统一转成 **boxed 形式**，接收三个参数：

1. `StableIValue* stack`：来自 dispatcher 的一个 stable IValue 栈；
2. `num_args`：从注册的 schema 解析出的参数个数；
3. `num_outputs`：同样来自 schema 的输出个数。

函数体做三件事：用 `to<T>` 把 `StableIValue` 转成 schema 里对应的对象类型 → 调用你的 kernel → 用 `from<T>` 把输出转回 `StableIValue` 并放回栈上。

### 5.2 `StableIValue` 到底是什么

这是全篇最需要想清楚的一个概念。**`StableIValue` 是对象的 ABI 稳定表示。**

为什么需要它？因为**你 kernel 的输入和输出其实都在跨越 libtorch 的 ABI 边界**。想象这个场景：

- 你的扩展是在 **torch 2.10** 下编译的，某个对象 A 在 2.10 里有某种内存布局；
- 运行时你实际跑在 **torch 2.11** 上，dispatcher 传进来的参数是 libtorch 2.11 版本、可能是**另一个版本**的对象 A。

`StableIValue` 就是那个**两种版本都认的公共表示**，而 `to` / `from` 就是在两种表示之间做翻译的转换层。**这就是 ABI 稳定在运行时的落点**：不是让 libtorch 不变，而是在边界上放一层翻译。[【跳转到 14:57】](https://www.youtube.com/watch?v=v2LcTzpUOYU&t=897)

## 六、编译：两个 flag 撑起两个维度的稳定

```python
from setuptools import setup, Extension
from torch.utils import cpp_extension

setup(name="extension_cpp_stable",
      ext_modules=[
          cpp_extension.CUDAExtension(
              "extension_cpp_stable",
              ["muladd.cu"],
              extra_compile_args={
                  "cxx": [
                      # 只用 Python 3.9+ 的 stable limited API 子集
                      "-DPy_LIMITED_API=0x03090000",
                  ],
                  "nvcc": [
                      # 只用 torch 2.10+ 的 stable API 子集
                      "-DTORCH_TARGET_VERSION=0x020a000000000000",
                      "-DUSE_CUDA",
                  ],
              },
              py_limited_api=True),   # 一个 wheel 跨多个 Python 版本
      ],
      cmdclass={"build_ext": cpp_extension.BuildExtension},
      options={"bdist_wheel": {"py_limited_api": "cp39"}})
```

![用 torch.utils.cpp_extension 编译：cxx 传 Py_LIMITED_API、nvcc 传 TORCH_TARGET_VERSION，并打开 py_limited_api](assets/2026%20年怎么写好一个%20PyTorch%20C++%20扩展：稳定%20ABI、算子注册与打包/00972.webp)

### 6.1 `TORCH_TARGET_VERSION` 干了两件事

格式是"主版本号 + 次版本号"，比如目标 2.10 就写成 `0x020a000000000000`。它有两个作用：

1. **禁止你的扩展 include 任何 libtorch 不稳定头文件**。比如你不小心用了 `at::cuda::getCurrentCUDAStream` 之类的 API，就会得到一个"又响又愤怒"的编译错误，告诉你别这么干。
2. **指定编译产物能运行的最低 torch 版本**。注意这个版本**不必等于构建时的 torch 版本**：你可以下载 2.12 的 nightly，用 2.10 的 `TORCH_TARGET_VERSION` 构建，编译出的扩展保证能在任何 $\ge$ 2.10 的 nightly 或正式版上运行。

**一个重要的限制**：这个特性不能往回追溯太久。别指望传 2.4 当目标版本还能在 2.4 上跑。[【跳转到 17:02】](https://www.youtube.com/watch?v=v2LcTzpUOYU&t=1022)

### 6.2 版本门控是怎么实现的

按三类头文件分别看：

- **C shim**：每个 API 周围都有 `#if` 宏，只有当你目标版本 $\ge$ 它被引入的版本时才暴露。比如 C shim 里的 `from_blob` 假设是 2.11 引入的，那么目标版本低于 2.11 就看不到它。
- **`torch/csrc/stable` 的高层封装**：它的版本号**总是取它用到的所有 shim 里最大的那个**。上面那个 `from_blob` 封装内部调 C shim 的 `from_blob`，所以同样被 2.11 这道门挡住。
- **`torch/headeronly`**：不依赖 libtorch，所以"构建时能用的对象版本"就是"被编译进你扩展的那个版本"。唯一的例外是：如果那个对象**跨过了 ABI 边界**，会对稳定性有影响——但视频说这种情况不太会发生（他们基本保证冻结 header-only），而且万一发生，`from`/`to` 转换会正确处理。

[【跳转到 18:17】](https://www.youtube.com/watch?v=v2LcTzpUOYU&t=1097)

### 6.3 `Py_LIMITED_API`：第二个维度

ABI 稳定性其实有**两个维度**：libtorch ABI 和 **CPython ABI**。`Py_LIMITED_API` 是 CPython 提供的 flag，传上它就能帮你校验扩展只用了 CPython 的 stable limited API。

两个坑：

- **像 pybind11 这样的头文件不是 CPython ABI 稳定的**。用了它，你的扩展可能就没法做到 CPython 无关。
- **这个 flag 要在三个不同的地方都传**，扩展才能真正做到 Python 无关（视频原话："一个有点怪的地方"）。

![Py_LIMITED_API 的用法：extra_compile_args 里传 -DPy_LIMITED_API、CUDAExtension 打开 py_limited_api、bdist_wheel 里再声明一次，三处齐备才能打出 CPython 无关的 wheel](assets/2026%20年怎么写好一个%20PyTorch%20C++%20扩展：稳定%20ABI、算子注册与打包/00947.webp)

做完这两件事，那张格子图就塌成一格：**一个二进制，跨多个 torch 版本和多个 Python 版本。**[【跳转到 20:22】](https://www.youtube.com/watch?v=v2LcTzpUOYU&t=1222)

## 七、Python 侧：用 `torch.ops.load_library` 加载

```python
# In __init__.py
import torch
from pathlib import Path

so_files = list(Path(__file__).parent.glob("_C*.so"))
assert len(so_files) == 1, f"Expected one _C*.so file, found {len(so_files)}"
torch.ops.load_library(so_files[0])
```

![在 __init__.py 里 glob 出 _C*.so 并用 torch.ops.load_library 加载：全程不碰 CPython API](assets/2026%20年怎么写好一个%20PyTorch%20C++%20扩展：稳定%20ABI、算子注册与打包/01247.webp)

**为什么推荐这种方式？** 因为它**不使用任何 CPython API**——这对 CPython ABI 稳定性有好处。暴露 C++ 算子还有别的方式（比如 pybind11 直接绑定），但为了 CPython ABI 稳定，视频推荐这一种。加载之后，算子就能用 `torch.ops.extension_cpp_stable.mymuladd` 访问。[【跳转到 21:12】](https://www.youtube.com/watch?v=v2LcTzpUOYU&t=1272)

## 八、别忘了两件"组合"的事：`register_fake` 与 `opcheck`

即使 kernel 和注册都写完了，还有两个工具能让它真正"好用"：

- **`torch.library.register_fake`**：从 Python 侧给算子注册 fake（meta）kernel，**让算子能和 `torch.compile` 组合**。原理和上一篇讲的一样：编译器要在没有真实数据的情况下推断输出形状。
- **`torch.library.opcheck`**：检查一些容易写错的地方，比如**你注册的函数 schema 和 kernel 的 schema 是否一致**，或者**你的 fake tensor 实现是否正确**。

但视频特别提醒：**`opcheck` 的测试并不穷尽，自己写测试仍然有必要。**[【跳转到 22:02】](https://www.youtube.com/watch?v=v2LcTzpUOYU&t=1322)

## 九、已经上船的库

视频最后列了一批已经在用 torch stable ABI 的库，这比任何论证都有说服力：

- **FlashAttention 3**
- **xformers** 的 CUDA 部分
- **torchaudio**
- **torchao** CUDA（较近）
- **vLLM** 的 CUDA 部分（推进中）

如果你觉得 `mul-add` 这个例子太简单，视频的建议是：**去看这些真实用例**，它们对你的真实场景来说是更好的例子。[【跳转到 23:17】](https://www.youtube.com/watch?v=v2LcTzpUOYU&t=1397)

## 小结

- **写 C++ 扩展的动机**：针对特定硬件、用自己场景更优的启发式，同时还想继续用 autograd、PT2、`torch.compile`。
- **libtorch 是座"锯齿山"**：ABI 稳定的部分只有三层——C shim、`torch/csrc/stable` 的高层封装、`torch/headeronly`，**其余都别 include**。
- **`TORCH_TARGET_VERSION` 既是门禁也是承诺**：编译期禁止不稳定头文件，同时承诺产物能在 $\ge$ 该版本的 torch 上运行。
- **注册要用 `STABLE_TORCH_LIBRARY` + `TORCH_BOX`**：`TORCH_BOX` 把函数转成 boxed 形式，在 `StableIValue` 与真实对象之间做 `to`/`from` 翻译——这就是 ABI 稳定在运行时的落点。
- **`Py_LIMITED_API` 消掉 Python 维度**，但它要在三个地方都传，且 pybind11 之类不算 CPython ABI 稳定。
- **Python 侧用 `torch.ops.load_library` 加载 `.so`**，避免引入 CPython API。
- **`register_fake` 管组合、`opcheck` 管校验**，但 `opcheck` 不穷尽，测试还得自己写。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| ABI（应用二进制接口） | 已编译代码之间的调用约定与内存布局；ABI 一变，二进制就得重编 |
| ABI stable / stable ABI | 承诺不随版本变化的接口层，让一个二进制跨多个版本可用 |
| C shim | 用 C 写的稳定接口层，把 libtorch 的内部变化挡在外面 |
| `torch::stable::Tensor` | stable 世界里对应 ATen `Tensor` 的类型，语义相似但 ABI 稳定 |
| header-only API | 完全用头文件实现、不依赖 `libtorch.so` 的接口，如 `dtype`、`device type` |
| `TORCH_TARGET_VERSION` | 编译选项，声明目标最低 torch 版本，并禁止 include 不稳定头文件 |
| `Py_LIMITED_API` | CPython 提供的 flag，限定只用 stable limited API，实现 Python 版本无关 |
| `py_limited_api` | setuptools/wheel 侧的开关，配合上面的 flag 打出跨 Python 版本的 wheel |
| `STABLE_TORCH_LIBRARY` / `_IMPL` | stable 版的算子注册宏：前者声明 schema，后者按 dispatch key 挂实现 |
| `TORCH_BOX` | 把普通函数转成 boxed 函数（收发 `StableIValue`）的宏 |
| `StableIValue` | 对象的 ABI 稳定表示，跨版本传参时的"公共语言" |
| dispatch key | 分派键，dispatcher 据此把调用路由到 CPU / CUDA 等实现 |
| `register_fake` | 注册形状推断（meta）实现，让算子能和 `torch.compile` 组合 |
| `opcheck` | PyTorch 提供的算子自检工具，校验 schema 一致性与 fake 实现正确性 |
| `torch.ops.load_library` | 在 Python 里加载 `.so` 并注册其中算子的方式，不依赖 CPython API |