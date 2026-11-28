# 在 vLLM 里接入一个自定义算子：从 DeepSeek V4 的 PR 看推理后端的算子落地

> 视频来源：[Adding Deepseek v4 support in vLLM](https://www.youtube.com/watch?v=Em1Qm84FZmI)（YouTube · 4 分钟）｜时长约 4 分钟
> 导读：这是一支很短的高层概览，但它给出了一个很有用的**清单**：要让一个新模型在 vLLM 里跑起来，一个 PR 里到底要改哪几类东西——依赖、API、自定义算子、层、模型、attention backend、KV cache。本文把它和本小节前两篇的"注册路径"对上，说明**推理后端的接入是同一套算子机制在具体框架里的落地**。字幕为 YouTube 自动字幕，术语按上下文订正。

## 本讲要解决的核心问题（SCQA）

**背景**：你已经知道在 PyTorch 里怎么把自定义 kernel 注册成算子（`torch.library.custom_op` 或 `TORCH_LIBRARY`），也知道要补 schema、fake kernel、autograd。

**冲突**：但推理框架不是 PyTorch 本身。vLLM 这样的引擎有自己的目录结构、自己的 C++ 扩展、自己的 Triton 工具层、自己的 attention backend 抽象。一个"新模型支持"的 PR 动辄 150 个文件、上万行改动——**算子注册只是其中一小块，但它决定了这个模型能不能真的跑快**。

**疑问**：在一个真实的推理后端里，一个自定义算子从"写"到"被前向调用"要经过哪些位置？一个模型支持 PR 的改动可以怎么分类？

**回答（中心思想）**：视频把 DeepSeek V4 的 PR（vllm-project/vllm #40860）拆成**七类改动**，按"从下往上"的顺序是：**依赖 → API → 自定义算子 → 层 → 模型 → attention backend → KV cache**。其中"自定义算子"这一类就是本小节讲的接入路径在 vLLM 里的具体形态：**在 C++ 头文件里声明、在 `.cu` 文件里实现、在 `torch_bindings.cpp` 里绑定；纯 Triton 的算子则直接放在 `vllm/.../ops/` 下用 `@triton.jit` 写。**

## 一、先看这个 PR 有多大

![vLLM PR #40860 [Feat] DeepSeek V4 Rebased：150 个文件、+16,313 −717，左侧能看到 csrc/cpu、csrc/moe、vllm/ 等目录结构](assets/在%20vLLM%20里接入一个自定义算子：从%20DeepSeek%20V4%20的%20PR%20看推理后端的算子落地/00000.webp)

这张图先给一个体感：**150 个文件、+16,313 行、−717 行**。视频说得很清楚，这期只讲"高层"，具体 kernel 和 layer 留到后面几期。

从左侧文件树就能看出 vLLM 的分层：[【跳转到 00:00】](https://www.youtube.com/watch?v=Em1Qm84FZmI&t=0)

- `csrc/`：C++/CUDA 扩展源码，按功能分子目录（`cpu/`、`moe/`、`quantization/`……）；
- `vllm/`：Python 侧，`attention/backends/`、`model_executor/models/`、`layers/`、`v1/` 等；
- `cmake/external_projects/`：第三方依赖的构建脚本（deepgemm、flashmla 等）。

## 二、七类改动：一张"模型支持"的检查清单

视频按顺序过了一遍，这个顺序本身就是一条合理的接入路径。

### 2.1 依赖更新

第一类是**更新依赖**：比如 DeepGEMM、FlashMLA 这些第三方内核库。

![PR 里对 cmake/external_projects/deepgemm.cmake 的改动：更新 GIT_TAG、调整 submodule 与安装规则](assets/在%20vLLM%20里接入一个自定义算子：从%20DeepSeek%20V4%20的%20PR%20看推理后端的算子落地/00025.webp)

注意这里改的是 `GIT_TAG` 和安装路径——**推理框架的内核能力有很大一部分来自外部库**，新模型往往先要求"把某个库升到某个 commit"。[【跳转到 00:25】](https://www.youtube.com/watch?v=Em1Qm84FZmI&t=25)

### 2.2 API 更新

第二类是**更新自己的 API**。视频举的例子是 rotary embedding：要支持 DeepSeek V4 需要的 `inverse` 和 `rope dim offset` 参数。

这类改动的特点是：**算子本身没变，但签名要变**。[【跳转到 00:50】](https://www.youtube.com/watch?v=Em1Qm84FZmI&t=50)它对应本小节反复强调的那件事——**schema 就是接口**，模型需要新的语义，就得先把 schema 扩出来。

### 2.3 引入自定义算子（本小节的核心）

第三类才是真正"新写 kernel"。视频举的例子是 **top-k + softplus + 开根号** 这个组合：

> "比如这个 top-k、softplus、开根号的组合，我们在一个头文件里声明，然后给它一个 CUDA 实现。"

在 PR 的文件树里，对应的就是：

- `csrc/moe/topk_softplus_sqrt_kernels.cu`：CUDA 实现；
- `csrc/moe/ops.h`：声明；
- `csrc/moe/torch_bindings.cpp`：绑定到 Python。

**这三件套就是"接入"的全部**：声明（schema）→ 实现（kernel）→ 绑定（注册）。[【跳转到 01:15】](https://www.youtube.com/watch?v=Em1Qm84FZmI&t=75)和上一篇讲的 `TORCH_LIBRARY` 是同一件事，只是 vLLM 把它组织成了 `ops.h` + `_kernels.cu` + `torch_bindings.cpp` 的固定结构。

### 2.4 顺手修 bug：精度问题

第四类改动很有意思，也是实战里最常见的"意外收获"：

> "我们改一个 layer norm，因为接入 DeepSeek V4 才发现这里有个 bug——我们实际在用比预期更低的精度做计算，于是顺手修掉，保证按正确的精度算。"

![PR 里 layer_norm_kernels.cu 的改动：把中间计算提升到 float 精度，并修正 fused_add_rms_norm_kernel 的累加方式](assets/在%20vLLM%20里接入一个自定义算子：从%20DeepSeek%20V4%20的%20PR%20看推理后端的算子落地/00075.webp)

看 diff 就能明白：中间量被显式转成 `float` 再参与乘加，最后才转回原本的标量类型——**把累加和缩放提到 float 做**。新模型对数值更敏感，旧 kernel 里那些"为了快而降低精度"的写法就暴露出来了。[【跳转到 01:40】](https://www.youtube.com/watch?v=Em1Qm84FZmI&t=100)

### 2.5 配置项

第五类是**加配置**：比如"indexer cache 要不要用 FP4"、"hash block size 设多少"。

这类改动容易被忽略，但它是**接入的最后一公里**：新模型往往带来新的取舍（精度 vs 显存），框架必须把这些取舍暴露成开关，用户才能在自己的硬件上选。

### 2.6 层（layers）

第六类是**加层**：

- DeepSeek V4 的 **MLA attention**；
- DeepSeek V4 的 **fused MoE** 实现；
- **compressor**；
- 之前视频里讲过的 **multiple hyper connection** 实现。

**层是算子的组合**。这一层的代码通常不写 CUDA，而是"把哪些算子按什么顺序拼起来"。[【跳转到 02:00】](https://www.youtube.com/watch?v=Em1Qm84FZmI&t=120)

### 2.7 模型（models）

第七类是**模型本身**。模型由一系列层组成，定义在 `DeepSeekV4Model` 这个类里。

视频对 forward 的描述很朴素：先 embedding，然后过很多 transformer 层，再过 head，然后做一次 norm；再往后是 tokenizer、tool parser 之类比较外围的东西。

![PR 里新增 vllm/model_executor/models/deepseek_v4.py，文件树里能看到 layers/attention、layers/fused_moe、layers/quantization、layers/rotary_embedding 等分层](assets/在%20vLLM%20里接入一个自定义算子：从%20DeepSeek%20V4%20的%20PR%20看推理后端的算子落地/00120.webp)

## 三、attention backend：元数据也是"接入"的一部分

除了上面七类，视频还单独讲了 **attention backend** 里的改动。它的定位很值得注意：

> "概念上可以这样理解这些改动：它在做 attention 的**全部元数据计算**，比如该从 KV cache 的哪个位置读、往哪里写。这些元数据就是上一个视频里讲过的、在 context manager 里设置的那些。"

这句话点出了一个容易被忽视的事实：**推理后端的"算子接入"不只是写计算 kernel，还包括写"告诉 kernel 去哪读数据"的索引 kernel**。[【跳转到 02:25】](https://www.youtube.com/watch?v=Em1Qm84FZmI&t=145)在 paged attention 的世界里，后者往往和前者一样重要。

### 3.1 例子：一个 Triton 写的索引 kernel

![vllm/v1/attention/backends/mla/compressor_utils.py 里新增的 @triton.jit _compressed_slot_mapping_kernel：输入全是索引类张量（slot_mapping_ptr、query_start_loc_ptr、seq_lens_ptr、block_table_ptr）](assets/在%20vLLM%20里接入一个自定义算子：从%20DeepSeek%20V4%20的%20PR%20看推理后端的算子落地/00170.webp)

看这个 kernel 的签名就明白什么叫"元数据 kernel"：

```python
@triton.jit
def _compressed_slot_mapping_kernel(
        slot_mapping_ptr,        # [num_tokens]
        query_start_loc_ptr,     # [num_reqs + 1]
        seq_lens_ptr,            # [num_reqs]
        block_table_ptr,         # [num_reqs, max_num_blocks]
        block_table_stride,
        block_size,
        COMPRESS_RATIO: tl.constexpr,
        PAD_ID: tl.constexpr,
        TRITON_BLOCK_SIZE: tl.constexpr,
):
    ...
```

它不碰 hidden states，只算"每个 token 该落到哪个 slot"。**这正是 DeepSeek V4 的 hash-based routing 带来的新需求**：位置信息要能写进 KV cache。

### 3.2 例子：Triton 写的融合算子

![vllm/attention/deepseek_v4_ops/ 下新增的 fused_compress_quant_cache.py、fused_indexer_q.py、fused_inv_rope_fp8_quant.py，全部用 @triton.jit 写](assets/在%20vLLM%20里接入一个自定义算子：从%20DeepSeek%20V4%20的%20PR%20看推理后端的算子落地/00195.webp)

这里能看出 vLLM 的一个工程选择：**能融合的算子用 Triton 写，放在 `vllm/.../ops/` 下**。文件名的信息量很大：

- `fused_compress_quant_cache.py`：压缩 + 量化 KV cache 融合；
- `fused_indexer_q.py`：indexer 的 query 侧融合；
- `fused_inv_rope_fp8_quant.py`：逆 RoPE + FP8 量化融合。

每个文件名都是"**几个小算子合成一个 kernel**"的产物——这就是本系列前面讲的算子融合，在推理后端里的落地形态。[【跳转到 02:50】](https://www.youtube.com/watch?v=Em1Qm84FZmI&t=170)

## 四、KV cache 的改动

最后一类是 **KV cache**。视频给了两条具体需求：

1. **hash-based routing 需要把位置信息写进 KV cache**；
2. **KV cache 要支持 DeepSeek V4 新增的 block compression**。

为什么 KV cache 的改动要和算子放在一起讲？因为**KV cache 的布局直接决定 kernel 怎么访存**。block compression 一进来，"一个 token 对应几个 slot、按什么比例压缩"就成了 kernel 必须知道的编译期常量——上面那个 `COMPRESS_RATIO` 就是证据。[【跳转到 03:15】](https://www.youtube.com/watch?v=Em1Qm84FZmI&t=195)

## 五、把这条路径和"注册"对上

把视频的清单和本小节前两篇的内容叠在一起，就得到一张完整的"接入路径"图：

| 层次 | 你要做的事 | 对应本小节的知识点 |
| --- | --- | --- |
| 依赖 | 把第三方内核库升到需要的版本 | — |
| API | 扩 schema（如 RoPE 的 `inverse`、`dim offset`） | schema 就是接口 |
| 算子（C++/CUDA） | `ops.h` 声明 + `_kernels.cu` 实现 + `torch_bindings.cpp` 绑定 | `TORCH_LIBRARY` / `STABLE_TORCH_LIBRARY` |
| 算子（Triton） | 在 `vllm/.../ops/` 下用 `@triton.jit` 写，直接调用 | Triton kernel 开箱即可与 `torch.compile` 组合 |
| 层 | 把算子按顺序拼起来 | 算子组合 |
| 模型 | 定义 forward：embedding → layers → head → norm | — |
| attention backend | 元数据 kernel：算"从 KV cache 哪里读、往哪里写" | 索引 kernel 也是 kernel |
| KV cache | 布局与压缩策略 | 布局决定访存 |

一个值得记住的对照：**在 PyTorch 里你操心的是"能不能被 `torch.compile` 组合"，在 vLLM 里你操心的是"能不能被 paged attention 的元数据正确索引"**。两者都是"胶水"问题，只是胶水粘的对象不同。[【跳转到 03:40】](https://www.youtube.com/watch?v=Em1Qm84FZmI&t=220)

## 小结

- **一个"新模型支持"的 PR 可以拆成七类改动**：依赖、API、自定义算子、配置、层、模型，外加 attention backend 与 KV cache。
- **vLLM 的自定义算子是"三件套"**：`ops.h` 声明、`_kernels.cu` 实现、`torch_bindings.cpp` 绑定——和 `TORCH_LIBRARY` 是同一套机制。
- **接入新模型常常顺手暴露旧 kernel 的精度 bug**：layer norm 的中间计算要提到 float。
- **元数据 kernel 和计算 kernel 一样重要**：paged attention 里"每个 token 落到哪个 slot"本身就是个 kernel。
- **能融合就融合**：`fused_` 开头的文件名就是算子融合在推理后端里的落地。
- **KV cache 布局决定 kernel 访存**：block compression 一进来，压缩比就成了 kernel 的编译期常量。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| vLLM | 面向 LLM 推理的服务引擎，核心是 paged attention 与 KV cache 管理 |
| PR（pull request） | 代码合并请求；这里指 vllm-project/vllm #40860 这个模型支持 PR |
| `csrc/` | vLLM 的 C++/CUDA 扩展源码目录，按功能分子目录 |
| `torch_bindings.cpp` | 把 C++ 算子绑定/注册到 Python 侧的文件 |
| `ops.h` | 算子声明（schema）集中放的头文件 |
| custom op（自定义算子） | 框架里注册过的、可被图或调度器识别的计算单元 |
| MLA（Multi-head Latent Attention） | DeepSeek 系列用的低秩压缩注意力，KV cache 占用更小 |
| fused MoE | 把专家路由与专家计算融合进少数几个 kernel 的 MoE 实现 |
| Triton `@triton.jit` | 用 Python DSL 写 GPU kernel 的装饰器，编译成 CUDA kernel |
| KV cache | 推理时缓存历史 key/value，避免重复计算 |
| block compression | 对 KV cache 按块压缩的机制，DeepSeek V4 引入 |
| hash-based routing | 用哈希决定路由的机制，需要把位置信息写入 KV cache |
| slot mapping | 逻辑 token 位置到物理 KV cache 槽位的映射，paged attention 的核心元数据 |
| dispatch / 绑定 | 把算子名与具体实现关联起来，使框架能按名字调用 |