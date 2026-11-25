# Llama-2 模型文件构成：safetensors 分片命名、index 索引与 pickle 的安全问题

> 视频来源：[04 深入浅出模型文件构成 - Llama-2 模型文件详解](https://www.bilibili.com/video/BV1MN411h7Jh/)（Bilibili · 五里墩茶社）｜时长约 14 分钟
> 导读：用一段真实的 `from_pretrained` 下载日志，把 Llama-2 仓库里的十几个文件逐个认一遍：哪些是配置、哪些是权重、分片为什么叫 `model-00001-of-00002`、`index.json` 里记了什么、safetensors 与 pickle 的 `.bin` 差在哪、`use_safetensors` 参数怎么切换。本文按"下载日志 → 文件清单 → 分片命名 → 索引内容 → 格式安全 → 加载参数 → 分词器"整理；权重名如何对应模型结构另有专文。

## 本讲要解决的核心问题（SCQA）

**背景**：用 `AutoModel.from_pretrained()` 或 `pipeline()` 加载模型时，transformers 会自动把需要的文件下载到本地缓存。多数人到此为止——模型能跑就行。

**冲突**：但下载下来的东西并不只是一个"模型文件"，而是十几个文件名各异的文件：`config.json`、`generation_config.json`、`model-00001-of-00002.safetensors`、`model.safetensors.index.json`、`pytorch_model-00001-of-00002.bin`、`tokenizer.model`……其中 safetensors 与 `.bin` 两套权重**内容几乎一样大**，却同时存在；不搞清楚谁是谁，遇到"加载慢""缺文件""想换格式"就只能猜。

**疑问**：这些文件分别负责什么？分片文件名里的 `00001-of-00002` 是什么含义？索引文件里到底记了哪些信息？既然两套权重都在，默认加载的是哪一套、能不能指定另一套？

**回答（中心思想）**：一个 HF 模型仓库可以按"配置 / 权重 / 分词器"三组来读。**权重被切成多个分片（shard），分片命名自带序号与总数，`*.index.json` 记录每个切片的元数据与重组方式；同一份权重通常提供 safetensors 与 pickle 两套格式，safetensors 因为不执行任意代码而更安全，`use_safetensors` 默认取 True**。理解这三组文件的职责，就能自己判断"少下了什么、加载的是哪一套"。[【跳转到 09:31】](https://www.bilibili.com/video/BV1MN411h7Jh/?t=571)

---

## 一、先看一段真实的下载日志

### 1.1 加载代码只有一行

视频用一个 Colab notebook 演示，模型选的是 `meta-llama/Llama-2-7b-chat-hf`：

```python
from transformers import AutoModel

model = AutoModel.from_pretrained(
    "meta-llama/Llama-2-7b-chat-hf",
    trust_remote_code=True,
    token="hf_...",
)
```

![演示 notebook：标题是"小白入门 Hugging Face / 04 看懂模型文件"，第一格安装依赖，第二格执行 from_pretrained，下面就是下载进度条](assets/Llama-2%20模型文件构成：safetensors%20分片命名、index%20索引与%20pickle%20的安全问题/00096.webp)

Llama-2 是受限模型，第一次打开仓库会看到申请表单，提交申请拿到访问权限后才能看到文件、才能用 `AutoModel` 加载；此外还需要一个 Hugging Face 的 access token（在个人设置里创建），代码里通过 `token=` 传入。[【跳转到 02:01】](https://www.bilibili.com/video/BV1MN411h7Jh/?t=121)

### 1.2 下载日志暴露了加载顺序

执行 `from_pretrained` 时，终端里依次出现这些行 [【跳转到 03:16】](https://www.bilibili.com/video/BV1MN411h7Jh/?t=196)：

```
Downloading (...)/config.json: 100%          614/614        [00:00<00:00, 20.1kB/s]
Downloading (...)/safetensors.index.json: 100%  26.8k/26.8k  [00:00<00:00, 1.10MB/s]
Downloading shards: 0%                          0/2 [00:22<?, ?it/s]
Downloading (...)-00002.safetensors: 32%        3.21G/9.98G  [00:33<02:15, 49.8MB/s]
```

![下载日志：先 config.json（614 字节），再 safetensors.index.json（26.8 kB），然后才开始下分片，进度条显示 "Downloading shards: 0/2"](assets/Llama-2%20模型文件构成：safetensors%20分片命名、index%20索引与%20pickle%20的安全问题/00221.webp)

这段日志的顺序很说明问题：**先拿配置，再拿索引，最后才拿权重分片**。因为只有读到 `config.json` 才知道该建多大的模型，只有读到索引文件才知道要下几个分片、每个分片叫什么名字。日志里的 `0/2` 就是分片总数——这个 7B 模型被切成 2 片，单片 9.98 GB。

### 1.3 换一个参数，下载的文件就变了

第二次调用同样用 `from_pretrained`、加载同一个模型，唯一区别是把 `use_safetensors` 设为 `False`。这次日志里出现的是 `00002-of-00002.bin` 的下载。[【跳转到 04:06】](https://www.bilibili.com/video/BV1MN411h7Jh/?t=246)

也就是说，**同一个仓库里躺着两套体积几乎一样的权重：一套 `.safetensors`，一套 `.bin`**。默认用哪一套、怎么切到另一套，是后面第五节的主题。

---

## 二、把 12 个文件逐个认一遍

视频用一张表格把 Files and versions 里的清单逐条解释了一遍。[【跳转到 05:21】](https://www.bilibili.com/video/BV1MN411h7Jh/?t=321)

![notebook 里的"模型文件详解"表格：12 个文件按 配置 / safetensors 三件套 / bin 三件套 / 分词器四件套 排列，每条都写了用途](assets/Llama-2%20模型文件构成：safetensors%20分片命名、index%20索引与%20pickle%20的安全问题/00321.webp)

按职责归组，这张表其实是三组：

**第一组：配置（2 个）**

| 文件 | 作用 |
| --- | --- |
| `config.json` | 模型架构的主要配置，如模型设置、预测头部、训练参数等 |
| `generation_config.json` | 文本生成相关的模型配置 |

两个都是 JSON，点开就能看，内容包括模型名称、路径、架构，以及 bos/eos 这些序列起始与结束的 token id 等。[【跳转到 05:46】](https://www.bilibili.com/video/BV1MN411h7Jh/?t=346)

**第二组：权重（6 个，两套格式各 3 个）**

| 文件 | 作用 |
| --- | --- |
| `model-00001-of-00002.safetensors` | safetensors 格式的权重参数分块 1 |
| `model-00002-of-00002.safetensors` | safetensors 格式的权重参数分块 2 |
| `model.safetensors.index.json` | safetensors 模型参数文件的索引，描述模型切片的 JSON |
| `pytorch_model-00001-of-00002.bin` | pickle 序列化的 PyTorch 权重参数分块 1 |
| `pytorch_model-00002-of-00002.bin` | pickle 序列化的 PyTorch 权重参数分块 2 |
| `pytorch_model.bin.index.json` | pickle 序列化的索引，描述模型切片的 JSON |

**第三组：分词器（4 个）**

| 文件 | 作用 |
| --- | --- |
| `special_tokens_map.json` | 分词器中特殊标记符（special tokens）到对应数字 id 的映射 |
| `tokenizer.json` | 分词器的配置信息，如字典大小、tokenize 的策略等 |
| `tokenizer.model` | 分词器的具体模型参数，是训练得到的二进制文件，不可读 |
| `tokenizer_config.json` | 使用该 tokenizer 时的一些配置，如最大序列长度等 |

视频的读法是"三个一组"：safetensors 的两个分片 + 一个索引是一组，`.bin` 的两个分片 + 一个索引是另一组，分词器的 `tokenizer.json` / `tokenizer.model` / `tokenizer_config.json` 又是一组。[【跳转到 06:36】](https://www.bilibili.com/video/BV1MN411h7Jh/?t=396)

---

## 三、分片命名：`model-00001-of-00002` 怎么读

一个完整的大型模型通常会被切成多个碎片（shards），并以 `model-00001-of-00002.safetensors` 这种命名方式保存。[【跳转到 09:06】](https://www.bilibili.com/video/BV1MN411h7Jh/?t=546)

名字可以拆成三段：

- `model`：这是"模型权重"的固定前缀（对比 `pytorch_model`，后者表示 pickle 格式）；
- `00001`：**这是第几片**，从 1 开始编号，补零到 5 位，保证按字符串排序时顺序正确；
- `of-00002`：**一共几片**。有了这个数字，下载器可以校验是否下全，也可以直接开 N 个线程并行下载。

为什么必须切？因为单个文件太大既不利于下载断点续传，也不利于多进程并行加载。切分之后，"哪个张量在哪一片"就不再能从文件名推断，必须靠索引文件回答。

---

## 四、index.json 里记了什么

视频把索引文件的内容归纳成四条 [【跳转到 09:06】](https://www.bilibili.com/video/BV1MN411h7Jh/?t=546)：

1. **模型切片的总数**；
2. **每个切片的元数据**，如名称、偏移地址、文件大小等；
3. **切片如何组合起来重新组成完整模型的说明**；
4. **一些额外的模型信息**，如模型名称、框架版本等元数据。

![notebook 里对 index 文件与 special_tokens_map 的说明：index 包含切片总数、每个切片的元数据（名称、偏移地址、文件大小）、重组说明与额外元数据；special_tokens_map 则列出 unk/sep/pad/cls/mask 五类特殊标记](assets/Llama-2%20模型文件构成：safetensors%20分片命名、index%20索引与%20pickle%20的安全问题/00421.webp)

第二点是理解权重文件的入口：**偏移地址（offset）**。索引里记的不只是"这个张量在哪一片"，还包括它在那一片字节流里的起始位置和长度，所以加载器可以拿着"名字 → 分片 → 偏移"这条链直接定位目标张量，而不必把整片文件当成一个整体去解析。视频没有展开 safetensors 的二进制布局，但"偏移地址"这个字段的存在，已经说明了它为什么能做到"快速加载"。

---

## 五、safetensors 与 pickle：同一个模型，两种存法

### 5.1 safetensors 是什么

视频给的定义很简洁：**safetensors 是一种安全、快速存储和加载 tensors 的文件格式**。[【跳转到 09:31】](https://www.bilibili.com/video/BV1MN411h7Jh/?t=571)

它出现的背景是：通常情况下，PyTorch 模型的权重参数会用 Python 的 pickle 工具序列化，写进 `.bin` 文件；**但是 pickle 并不安全，pickle 文件可能包含可以执行的恶意代码**。因此推出了 safetensors 这种机制，作为 pickle 的一个更安全的替代方案，用来帮助模型共享权重参数。

![notebook 里"safetensors 文件"一节的原文：safetensors 是安全快速的张量存储格式；pickle 不安全、可能包含可执行的恶意代码，safetensors 是它的安全替代方案](assets/Llama-2%20模型文件构成：safetensors%20分片命名、index%20索引与%20pickle%20的安全问题/00571.webp)

用一句话对比两者的差别：

| 维度 | pickle 的 `.bin` | safetensors |
| --- | --- | --- |
| 本质 | 一段可以被"执行"的序列化程序 | 一段被"读取"的字节流 + 元数据 |
| 安全 | 反序列化时可能执行恶意代码 | 只读数据，不执行代码 |
| 加载 | 需要反序列化，通常要整体读入 | 按名字与偏移定位，可直接映射 |
| 命名 | `pytorch_model-0000x-of-0000y.bin` | `model-0000x-of-0000y.safetensors` |

视频没有展开 safetensors 的二进制布局，只把读者引向 Hugging Face 的 "Load safetensors" 文档——那里讲得更细，包括如何使用 safetensors 以及为什么要用它。[【跳转到 09:56】](https://www.bilibili.com/video/BV1MN411h7Jh/?t=596)

### 5.2 `use_safetensors` 参数：默认取哪一套

回到代码层面：**在默认情况下，当我们没有指定 `use_safetensors` 参数时，`AutoModel` 加载的是 safetensors 文件**——也就是更安全、更快速的那一种。[【跳转到 10:31】](https://www.bilibili.com/video/BV1MN411h7Jh/?t=631)

如果想加载 pickle 序列化的 `.bin` 文件，就把参数显式设为 `False`：

```python
model = AutoModel.from_pretrained(
    "meta-llama/Llama-2-7b-chat-hf",
    use_safetensors=False,   # 明确要求加载 pytorch_model-*.bin
)
```

![use_safetensors=False 时的下载日志：这次出现的是 00002-of-00002.bin，而不再是 .safetensors 分片](assets/Llama-2%20模型文件构成：safetensors%20分片命名、index%20索引与%20pickle%20的安全问题/00656.webp)

这个参数的默认值从日志里就能反推：第一次调用没有传它，下载的是 safetensors，所以默认是 `True`。[【跳转到 04:56】](https://www.bilibili.com/video/BV1MN411h7Jh/?t=296)

---

## 六、分词器的四个文件

分词器负责把文本变成 token id，反向再把 id 变回文本。[【跳转到 08:16】](https://www.bilibili.com/video/BV1MN411h7Jh/?t=496)

- `tokenizer.json`：分词器的配置信息——字典大小、tokenize 的策略等；
- `tokenizer.model`：分词器的具体模型参数，是训练得到的二进制文件，**不可读**（Llama 系列用的是 SentencePiece 模型）；
- `tokenizer_config.json`：使用该 tokenizer 时的一些配置，如最大序列长度；
- `special_tokens_map.json`：特殊标记符到数字 id 的映射。

视频列出了五类常见特殊标记：

1. `unk_token`：未登录词（out-of-vocabulary words）的标记 id；
2. `sep_token`：句子分隔的标记 id；
3. `pad_token`：填充序列到相等长度时使用的填充标记 id；
4. `cls_token`：分类任务中使用的分类标记 id；
5. `mask_token`：掩码语言模型任务中使用的掩码标记 id。

这五类标记的 id 会直接影响输入张量的内容——比如 `pad_token` 的 id 决定了 padding 位置填什么数，而 attention mask 正是靠这个值来屏蔽填充位的。

---

## 七、不是每个模型都提供 safetensors

视频最后提醒了一句很重要的话：**这并不是唯一的模型文件组成形式**。[【跳转到 11:46】](https://www.bilibili.com/video/BV1MN411h7Jh/?t=706)

点开 PyTorch 或 text-generation 标签下的其他模型，会看到各种不同的文件组合。有的模型同时提供 safetensors 与 `.bin`，有的**只有 `.bin`**——数据就以 pickle 序列化的形式存储。

![反例：togethercomputer/LLaMA-2-7B-32K 仓库里只有 pytorch_model-00001/00002-of-00002.bin 与 pytorch_model.bin.index.json，没有任何 safetensors 文件，还多了一个 modeling_flash_llama.py](assets/Llama-2%20模型文件构成：safetensors%20分片命名、index%20索引与%20pickle%20的安全问题/00706.webp)

这张截图里有三个值得注意的细节：

1. 权重只有 `.bin` 一套，索引文件叫 `pytorch_model.bin.index.json`；
2. 文件列表里有 `modeling_flash_llama.py`——**模型自带代码**，这类仓库通常需要 `trust_remote_code=True`；
3. `added_tokens.json` 这类文件也可能出现，用于记录额外添加的 token。

所以判断"这个模型能不能用 safetensors 加载"，不能靠猜，要去看仓库的文件列表；有些模型还会在 README 里说明推荐用哪一套。

---

## 小结

- **一个 HF 仓库按三组读**：配置（`config.json`、`generation_config.json`）、权重（分片 + 索引）、分词器（`tokenizer.json`、`tokenizer.model`、`tokenizer_config.json`、`special_tokens_map.json`）。
- **下载顺序是"配置 → 索引 → 分片"**：先读 `config.json` 建模型，再读索引知道要下几片，最后才下权重。
- **分片命名自带序号与总数**：`model-00001-of-00002.safetensors` 中 `00001` 是第几片、`00002` 是总片数，便于并行下载与校验完整性。
- **索引文件记录四类信息**：切片总数、每个切片的元数据（名称、偏移地址、文件大小）、切片如何重组、额外的模型与框架元数据。
- **safetensors 的核心优势是安全**：pickle 反序列化可能执行恶意代码，safetensors 只读数据；同时按偏移定位让加载更快。
- **`use_safetensors` 默认 True**：不写参数就加载 safetensors；写 `False` 才去加载 `pytorch_model-*.bin`。
- **并非所有模型都有 safetensors**：只有 `.bin` 的仓库很常见，判断依据是仓库文件列表而不是习惯。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| safetensors | 安全、快速的张量存储格式，只存数据不执行代码，是 pickle 的替代方案 |
| pickle | Python 的序列化工具，反序列化时可执行任意代码，因此 `.bin` 权重存在安全风险 |
| shard（分片） | 把大权重按体积切成多个文件，命名形如 `model-00001-of-00002.safetensors` |
| `model.safetensors.index.json` | safetensors 权重分片的索引，记录切片总数、每个切片的名称与偏移地址、重组方式 |
| `pytorch_model.bin.index.json` | pickle 格式权重分片的索引，作用同上 |
| `use_safetensors` | `from_pretrained` 的参数，默认 `True` 加载 safetensors，`False` 则加载 `.bin` |
| `config.json` | 模型架构的主要配置，决定网络结构与预测头部 |
| `generation_config.json` | 文本生成相关配置，如采样策略与特殊 token id |
| `special_tokens_map.json` | 特殊标记符（unk/sep/pad/cls/mask）到数字 id 的映射 |
| `tokenizer.model` | 分词器的具体模型参数，训练得到的二进制文件，不可直接阅读 |
| `trust_remote_code` | 允许执行仓库自带建模代码（如 `modeling_flash_llama.py`）的开关 |