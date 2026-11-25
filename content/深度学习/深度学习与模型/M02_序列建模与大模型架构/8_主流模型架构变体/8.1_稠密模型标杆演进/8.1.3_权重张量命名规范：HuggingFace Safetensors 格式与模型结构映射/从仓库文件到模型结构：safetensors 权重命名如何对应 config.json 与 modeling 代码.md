# 从仓库文件到模型结构：safetensors 权重命名如何对应 config.json 与 modeling 代码

> 视频来源：[【LLM】10分钟带你看懂一个大模型的完整文件结构](https://www.bilibili.com/video/BV1SK4CzHEus/)（Bilibili · 认真工作的JIA）｜时长约 10 分钟
> 导读：以 DeepSeek-V3.1 的 Hugging Face 仓库为样本，从 Files 选项卡一路走到 `modeling_deepseek.py`：权重被切成 163 个 safetensors 分片，`model.safetensors.index.json` 负责"名字→文件"的映射，`config.json` 提供数字，代码里的属性名提供名字。本文按"文件分类 → 索引文件 → 配置类 → 类嵌套 → 数字来源 → 一次完整加载"整理；权重绑定（tied weights）的取舍另有专文，这里只在代码里点到为止。

## 本讲要解决的核心问题（SCQA）

**背景**：我们经常听到"某个大模型开源了"。下载下来一看，是一个几百 GB 的仓库：一堆 `model-000xx-of-000163.safetensors`、几个 JSON、一两个 `.py` 文件。用 `AutoModel.from_pretrained()` 一行代码就能把它跑起来。

**冲突**：这行代码背后，框架必须回答一个很具体的问题——**哪个张量该装进哪个位置**。仓库里的权重文件是扁平的（一个文件里成千上万个张量），模型代码是嵌套的（类里套类、层里套层）。如果名字对不上，加载就会报 missing keys / unexpected keys；如果形状对不上，就会报 size mismatch。而这两类错误恰恰是改模型、做增量预训练、手写推理时最常撞上的墙。

**疑问**：一个 safetensors 文件里的张量叫什么名字？这些名字是谁定的？名字里的层级和数字，跟 `config.json`、跟 `modeling_*.py` 里的类，到底是怎么一一对应的？

**回答（中心思想）**：Hugging Face 的权重命名不是另造的一套规范，而是**由 PyTorch 模块树的属性路径直接决定的**：你在 `__init__` 里写 `self.self_attn = ...`，这个子模块下的权重就叫 `...self_attn.<张量名>`。于是"名字"由代码给出，"数字"（层数、维度、词表大小）由 `config.json` 给出，而"哪个名字在哪个文件里"由 `model.safetensors.index.json` 的 `weight_map` 给出。三者对齐，模型才装得起来。[【跳转到 06:12】](https://www.bilibili.com/video/BV1SK4CzHEus/?t=372)

---

## 一、模型 = 结构 + 权重，所以仓库里必然有两类文件

### 1.1 先回到"模型是什么"

视频在打开仓库之前先做了一次最小回顾：大模型本质上还是一个由大量神经元组成的神经网络，网络中每个圆圈代表一个神经元，连接神经元的线代表一个权重参数；**神经元的排列方式决定了模型的结构**——有多少层、每层有多少单元。[【跳转到 01:02】](https://www.bilibili.com/video/BV1SK4CzHEus/?t=62)

这句话可以直接翻译成一句工程结论：一个模型可以拆成两部分，

- **结构**：层的种类、层与层的连接顺序、每一层的维度；
- **权重**：这些层里那些具体的浮点数。

结构是"骨架"，权重是"肉"。骨架可以用代码描述（几百行就够），肉只能用二进制存（几百 GB）。所以一个 HF 仓库里，文件天然分成这两族。

### 1.2 Files 选项卡里的四类文件

以 `deepseek-ai/DeepSeek-V3.1` 为例，模型卡页面只展示介绍信息，真正的核心内容在 **Files** 选项卡里 [【跳转到 00:34】](https://www.bilibili.com/video/BV1SK4CzHEus/?t=34)。往下翻，文件可以归成四类 [【跳转到 00:44】](https://www.bilibili.com/video/BV1SK4CzHEus/?t=44)：

1. **配置相关文件**：`config.json`、`generation_config.json`；
2. **权重文件**：大量 `*.safetensors`，"数量最多也最大"；
3. **模型结构定义**：`modeling_deepseek.py`、`configuration_deepseek.py`；
4. **分词器**：`tokenizer.json`、`tokenizer_config.json`。

![DeepSeek-V3.1 的模型卡页面：右侧信息栏标注 Safetensors 格式、685B 参数、张量类型 BF16/F8_E4M3/F32，这些元信息是仓库的"门面"，真正的文件在 Files 里](assets/从仓库文件到模型结构：safetensors%20权重命名如何对应%20config.json%20与%20modeling%20代码/00034.webp)

![Files 选项卡：config.json、configuration_deepseek.py、generation_config.json 等小文件排在前面，下面才是成片的 safetensors 分片](assets/从仓库文件到模型结构：safetensors%20权重命名如何对应%20config.json%20与%20modeling%20代码/00044.webp)

注意一个直观的对比：`config.json` 只有 1.69 kB，`generation_config.json` 只有 171 Bytes，而 `modeling_deepseek.py` 是 75.7 kB——**描述结构的这几个文件加起来不到 90 kB，而描述权重的分片有 163 个、合计 689 GB**。开源一个模型，绝大部分体积都在权重里。

![Files 选项卡上半部分：config.json（1.69 kB）、configuration_deepseek.py（9.9 kB）、generation_config.json（171 Bytes）——三个小文件决定了整个 685B 模型的形状](assets/从仓库文件到模型结构：safetensors%20权重命名如何对应%20config.json%20与%20modeling%20代码/00136.webp)

这里有个容易忽略的细节：**safetensors 文件的数量最多、体积最大**，一个 685B 参数的模型被切成 163 个分片，每片 4.3 GB 左右（最后几片 5.23 GB、6.58 GB）。为什么必须切？视频给的理由很直接：切成多片**便于并行加载**。[【跳转到 01:37】](https://www.bilibili.com/video/BV1SK4CzHEus/?t=97)

---

## 二、163 个分片怎么找回自己的位置：index.json 是"名字→文件"的映射表

### 2.1 分片文件名的含义

分片统一命名成 `model-00001-of-000163.safetensors` 这种形式。`00001` 是**序号**，`000163` 是**总数**——只看文件名就知道"一共有几片、这是第几片"，下载器可以据此判断是否下全、能否并行。

但文件名只回答了"这一片是第几片"，没有回答"这一片里有哪些张量"。一个 4.3 GB 的文件里可能塞了几十个张量，也可能只塞了一个巨大的专家矩阵。**模型怎么知道某个位置的权重具体在哪个文件里？** 这就由 `model.safetensors.index.json` 负责。[【跳转到 01:37】](https://www.bilibili.com/video/BV1SK4CzHEus/?t=97)

![分片列表的尾部：model-00157 到 model-00163，紧跟着 model.safetensors.index.json（8.9 MB）与 modeling_deepseek.py（75.7 kB）——索引文件比任何一个分片都小得多，因为它只存名字和偏移](assets/从仓库文件到模型结构：safetensors%20权重命名如何对应%20config.json%20与%20modeling%20代码/00097.webp)

### 2.2 打开 index.json：weight_map 的键就是权重全名

这个索引文件只有两个顶层字段：`metadata` 和 `weight_map`。[【跳转到 01:56】](https://www.bilibili.com/video/BV1SK4CzHEus/?t=116)

- `metadata.total_size` 记录所有张量的总字节数（截图里是 1369062772000，约 1.37 TB）——注意这个数字和仓库页面标注的 689 GB 并不是一回事，前者是索引里声明的张量字节总量，后者是仓库的实际体积；
- `weight_map` 是一个巨大的字典，**键是权重张量的全名，值是它所在的分片文件名**。

![model.safetensors.index.json 的内容：weight_map 里每一行都是 "张量全名 → 分片文件名"，例如 model.layers.0.self_attn.q_a_proj.weight 指向 model-00001-of-000163.safetensors](assets/从仓库文件到模型结构：safetensors%20权重命名如何对应%20config.json%20与%20modeling%20代码/00116.webp)

截图里能直接读出命名的语法：

```
model.embed_tokens.weight
model.layers.0.self_attn.q_a_proj.weight
model.layers.0.self_attn.q_b_proj.weight
model.layers.0.self_attn.kv_a_proj_with_mqa.weight
model.layers.0.self_attn.o_proj.weight
model.layers.0.mlp.gate_proj.weight
model.layers.0.mlp.up_proj.weight
model.layers.0.mlp.down_proj.weight
model.layers.0.input_layernorm.weight
model.layers.0.post_attention_layernorm.weight
```

规律非常整齐，可以拆成四段：

| 段落 | 例子 | 含义 |
| --- | --- | --- |
| 顶层前缀 | `model.` | 顶层因果语言模型类里那个叫 `model` 的子模块 |
| 层索引 | `layers.0.` | `ModuleList` 的第 0 个元素，即第 0 个解码器层 |
| 子模块名 | `self_attn.` / `mlp.` | 解码器层里的注意力子层、前馈子层 |
| 张量名 | `q_a_proj.weight` | 该子层内部那个 `nn.Linear` 的权重 |

视频里举的例子更极端：`layer 61` 中的 `input_layernorm` 层，它的权重就在 `00163` 这个文件里 [【跳转到 01:56】](https://www.bilibili.com/video/BV1SK4CzHEus/?t=116)。也就是说，**同一个逻辑层的不同张量，可能被切到不同的分片里**——分片是按体积切的，不是按层切的。这也是为什么必须有索引文件：靠文件名猜不出来。

> 一句话记住：`index.json` 是"电话号码簿"，不是"电话机"。它只告诉你谁在哪，不存任何浮点数。

---

## 三、config.json 是数据，configuration_*.py 是解释数据的逻辑层

### 3.1 config.json 里有什么

`config.json` 定义了模型的结构参数 [【跳转到 02:16】](https://www.bilibili.com/video/BV1SK4CzHEus/?t=136)：

- `model_type`：告诉 transformers 框架"这是一个 DeepSeek 模型"，用于在 `AutoConfig` 里选注册的配置类；
- `hidden_size` 和 `num_hidden_layers`：网络的维度和层数；
- `vocab_size`：词表长度；
- 因为 DeepSeek-V3.1 是混合专家（MoE）模型，这里还会配置**路由专家数量**和**共享专家数量**；
- 开头的 `architectures` 字段指向模型类名 `DeepseekV3ForCausalLM`。

![config.json 与左侧结构树并排：hidden_size 7168、intermediate_size 18432、kv_lora_rank 512、architectures 为 DeepseekV3ForCausalLM，auto_map 把 AutoConfig / AutoModel / AutoModelForCausalLM 指到具体的模块和类名](assets/从仓库文件到模型结构：safetensors%20权重命名如何对应%20config.json%20与%20modeling%20代码/00400.webp)

### 3.2 参数怎么变成 Python 对象

JSON 只是文本，模型构造函数需要的是一个带属性的对象。这中间的翻译由 `configuration_deepseek.py` 完成：它定义了一个 Python 类 `DeepseekV3Config`，**继承自 `PretrainedConfig`**，在模型加载时读取 `config.json`，把参数解析成 Python 对象，再传给模型构造函数。[【跳转到 02:41】](https://www.bilibili.com/video/BV1SK4CzHEus/?t=161)

视频用一句话总结了这个分工：**`config.json` 是数据，`configuration_deepseek.py` 是解释数据的逻辑层**。[【跳转到 03:06】](https://www.bilibili.com/video/BV1SK4CzHEus/?t=186)

这句话解释了 `auto_map` 字段为什么存在。截图里 `auto_map` 长这样：

```json
"auto_map": {
  "AutoConfig": "configuration_deepseek.DeepseekV3Config",
  "AutoModel": "modeling_deepseek.DeepseekV3Model",
  "AutoModelForCausalLM": "modeling_deepseek.DeepseekV3ForCausalLM"
}
```

当模型的结构没有并进 transformers 主库（`trust_remote_code=True` 的那种模型），`AutoConfig` / `AutoModel` 就靠这张表找到"用哪个文件里的哪个类"。这是"模型自带代码"的接线方式。

---

## 四、modeling_*.py 的类嵌套，决定了权重名字的层级

### 4.1 顶层入口：ForCausalLM 里套一个 Model

`modeling_deepseek.py` 是真正定义模型结构和计算逻辑的地方。加载模型时，框架根据 `architectures` 字段创建对应的类 `DeepseekV3ForCausalLM`。[【跳转到 03:31】](https://www.bilibili.com/video/BV1SK4CzHEus/?t=211)

这个类是顶层入口，负责语言建模任务；其中实现 Transformer 架构的部分在 `self.model` 里，而 `self.model` 来自 `DeepseekV3Model` 类。[【跳转到 03:31】](https://www.bilibili.com/video/BV1SK4CzHEus/?t=211)

注意这里已经出现了一个关键事实：**`self.model` 这个属性名，就是权重名里的第一段 `model.`**。命名不是设计出来的，是写代码时顺手写下的属性名。

`DeepseekV3ForCausalLM.forward` 的后半段把这件事讲得很清楚 [【跳转到 03:56】](https://www.bilibili.com/video/BV1SK4CzHEus/?t=236)：

```python
outputs = self.model(input_ids=input_ids, attention_mask=attention_mask, ...)
hidden_states = outputs[0]
logits = self.lm_head(hidden_states)
```

`self.model` 产出隐状态，`self.lm_head` 把隐状态映射成词表上的 logits。对应到权重文件，就是两个名字：`model.*` 那一大族，和单独一个 `lm_head.weight`。

![modeling_deepseek.py 的 forward 片段：self.model(...) 之后取输出的第 0 项作为 hidden_states，再交给 self.lm_head 得到 logits，训练时用交叉熵与 shift 过的 labels 对齐](assets/从仓库文件到模型结构：safetensors%20权重命名如何对应%20config.json%20与%20modeling%20代码/00236.webp)
### 4.2 解码器层：属性名就是权重名的下一段

`DeepseekV3Model` 由多个 `DeepseekV3DecoderLayer` 堆叠组成，每一层包含注意力机制、前馈网络等模块。这些结构都继承自 PyTorch 的 `nn.Module`，而 PyTorch 的核心机制只有两个函数：`__init__` 定义模块需要的层（比如注意力层、线性层），`forward` 定义数据从输入到输出的计算路径。[【跳转到 04:21】](https://www.bilibili.com/video/BV1SK4CzHEus/?t=261)

正因为"层是在 `__init__` 里用 `self.xxx = ...` 挂上去的"，**PyTorch 天然给每个参数生成了一条属性路径**。`nn.Module` 的 `state_dict()` 用的就是这条路径当键。所以：

```python
class DeepseekV3DecoderLayer(nn.Module):
    def __init__(self, config, layer_idx):
        super().__init__()
        self.self_attn = ATTENTION_CLASSES[config._attn_implementation](config, layer_idx)
        self.mlp = ...
        self.input_layernorm = DeepseekV3RMSNorm(config.hidden_size, eps=config.rms_norm_eps)
        self.post_attention_layernorm = DeepseekV3RMSNorm(config.hidden_size, eps=config.rms_norm_eps)
```

这四行 `self.xxx` 直接决定了四个名字段：`self_attn`、`mlp`、`input_layernorm`、`post_attention_layernorm`。再往下，`self_attn` 里的 `q_a_proj`、`o_proj`，`mlp` 里的 `gate_proj`、`up_proj`、`down_proj`，继续拼在后面；最后加上 `nn.Linear` 自己的 `.weight`（有 bias 时再加 `.bias`）。

![DeepseekV3DecoderLayer 的 __init__ 与左侧结构树并排：self.self_attn、self.mlp、self.input_layernorm、self.post_attention_layernorm 四个属性，正好对应树上的四个分支](assets/从仓库文件到模型结构：safetensors%20权重命名如何对应%20config.json%20与%20modeling%20代码/00372.webp)

于是 `model.layers.0.self_attn.q_a_proj.weight` 这条名字可以被逐段"读"出来：

| 名字片段 | 来自哪里 |
| --- | --- |
| `model` | `DeepseekV3ForCausalLM.__init__` 里的 `self.model = DeepseekV3Model(config)` |
| `layers.0` | `DeepseekV3Model` 里那个 `nn.ModuleList` 属性 `layers` 的第 0 个元素 |
| `self_attn` | `DeepseekV3DecoderLayer.__init__` 里的 `self.self_attn` |
| `q_a_proj` | 注意力模块内部的 `self.q_a_proj = nn.Linear(...)` |
| `weight` | `nn.Linear` 自带的参数名 |

**这就是"权重张量命名规范"的全部秘密**：没有额外的命名表，只有一条从根模块到叶子参数的属性路径。换一个模型（Llama、Qwen、Mistral），规则不变，只是中间那几段的名字不同——Llama 用 `q_proj/k_proj/v_proj/o_proj`，DeepSeek 因为用了低秩压缩，拆成 `q_a_proj/q_b_proj`、`kv_a_proj_with_mqa/kv_b_proj`。

### 4.3 从名字反查文件：三步定位一个张量

视频把整个流程压缩成一句话：**现在我们有了 `model`、`layers`、`input_layernorm` 这三个变量名字，就能在权重的索引文件中找到对应的 safetensors 文件**；这样我们就有了"一个具体层级的结构"和"它对应的权重"，以类似的方式可以组建起整个模型。[【跳转到 06:12】](https://www.bilibili.com/video/BV1SK4CzHEus/?t=372)

把它写成可操作的清单：

1. 在 `modeling_*.py` 里顺着 `self.xxx` 找到目标张量，写出全名（如 `model.layers.0.input_layernorm.weight`）；
2. 在 `model.safetensors.index.json` 的 `weight_map` 里查这个名字，拿到分片文件名；
3. 用 `safetensors` 库按名字读那一片里的这个张量，核对形状。

第 3 步是排查形状错误最快的手段——名字对、文件对、形状不对，问题一定在 `config.json` 或代码里的维度计算上。

---

## 五、名字里的数字从哪来：7168 与 18432 的出处

### 5.1 input_layernorm 后面的 7168

结构树里每个模块后面都标了维度，比如 `DeepseekV3RMSNorm (input_layernorm) 7168`。视频特意让观众注意这个数字：**7168 就是来源于之前 `config.json` 中的数据，代表了隐藏层的维度**。[【跳转到 06:28】](https://www.bilibili.com/video/BV1SK4CzHEus/?t=388) [【跳转到 06:40】](https://www.bilibili.com/video/BV1SK4CzHEus/?t=400)

对照 `config.json` 就能验证：`hidden_size` 的值正是 7168。归一化层是逐元素缩放的，权重是一个长度为 `hidden_size` 的向量，所以它的形状里只有这一个数字。

### 5.2 线性层的形状：注意 PyTorch 是"先输出后输入"

结构树上还标了每个 `nn.Linear` 的形状。这里有个初学者最容易读反的约定：**PyTorch 的 `nn.Linear` 权重形状是 `[out_features, in_features]`**，也就是"左边是输出维，右边是输入维"。把它和 `config.json` 对齐：

| 张量（结构图标注） | 形状 | 与 config 的对应 |
| --- | --- | --- |
| `Embedding (embed_tokens)` | 128280 × 7168 | 词表大小 × `hidden_size` |
| `Linear (q_a_proj)` | 1536 × 7168 | 输入维 = `hidden_size` 7168 |
| `Linear (q_b_proj)` | 24576 × 1536 | 输入维 = 上一层的压缩维 1536 |
| `Linear (kv_a_proj_with_mqa)` | 576 × 7168 | 输入维 = `hidden_size` |
| `Linear (kv_b_proj)` | 32768 × 512 | 输入维 = `kv_lora_rank` 512 |
| `Linear (o_proj)` | 7168 × 16384 | 输出维 = `hidden_size` |
| `Linear (gate_proj)` / `(up_proj)` | 18432 × 7168 | 输出维 = `intermediate_size` 18432 |
| `Linear (down_proj)` | 7168 × 18432 | 输入维 = `intermediate_size` |
| `RMSNorm (input_layernorm)` | 7168 | `hidden_size` |

读这张表的正确姿势是：**先在 config 里找字段，再到结构图上找同名数字**。`hidden_size` 7168、`intermediate_size` 18432、`kv_lora_rank` 512 都在截图里的 `config.json` 中出现了，而结构图上的形状恰好由这几个数拼出来。下次遇到 `size mismatch`，第一件事就是把两边的数字这样对一遍。

### 5.3 层数与专家数：MoE 让名字变长

结构树里 `DeepseekV3DecoderLayer` 出现了两次：先是 `x 3`，再是 `x 58`，合计 61 层。这与 config 里的 `first_k_dense_replace: 3`、`moe_layer_freq: 1` 对应——前 3 层是稠密层，后面的层每隔 1 层就是一个 MoE 层。

MoE 层的 `mlp` 不再是单个 `DeepseekV3MLP`，而是 `DeepseekV3MoE`，里面又套了三样东西：

- `ModuleList (experts)`：256 个 `DeepseekV3MLP`，每个的 `gate_proj`/`up_proj` 是 2048 × 7168，`down_proj` 是 7168 × 2048（对应 `moe_intermediate_size: 2048`）；
- `MoEGate (gate)`：256 × 7168，负责给每个 token 选专家；
- `DeepseekV3MLP (shared_experts)`：所有 token 共用的一份前馈。

这些子模块在权重名里表现为**更长的路径**：`model.layers.<i>.mlp.` 之后不再是 `gate_proj`，而是先经过 `experts.<专家编号>` 或 `gate` 或 `shared_experts`，再落到具体的投影矩阵。**结构嵌套多深，名字就有多长**——这是排查 MoE 模型权重时最直观的线索。

---

## 六、lm_head、bias 与"可绑定"名单

顶层类的 `__init__` 只有三行，却解释了三个命名现象 [【跳转到 03:56】](https://www.bilibili.com/video/BV1SK4CzHEus/?t=236)：

```python
class DeepseekV3ForCausalLM(DeepseekV3PreTrainedModel):
    _tied_weights_keys = ["lm_head.weight"]

    def __init__(self, config):
        super().__init__(config)
        self.model = DeepseekV3Model(config)
        self.vocab_size = config.vocab_size
        self.lm_head = nn.Linear(config.hidden_size, config.vocab_size, bias=False)
```

![结构树与 lm_head 的定义并排：lm_head 是 nn.Linear(hidden_size, vocab_size, bias=False)，所以它只有一个 .weight；类属性 _tied_weights_keys 把 lm_head.weight 列入"可绑定"名单](assets/从仓库文件到模型结构：safetensors%20权重命名如何对应%20config.json%20与%20modeling%20代码/00347.webp)

三个现象分别是：

1. **`lm_head.weight` 是唯一不在 `model.` 前缀下的权重**。因为 `lm_head` 挂在 `DeepseekV3ForCausalLM` 上，和 `self.model` 平级，所以它的名字只有两段。
2. **它没有 `.bias`**。`bias=False` 意味着这个线性层只注册一个参数，名字里自然也就没有 `.bias` 这一项。反过来，如果某个模型开了 `attention_bias`，你就会在权重名里看到 `q_proj.bias` 这样的键。
3. **`_tied_weights_keys` 是一份"可绑定"名单**。它声明 `lm_head.weight` 属于可以被绑定（tie）的那类张量——绑定之后，输出层和输入嵌入共享同一块参数，权重文件里就少一个张量。是否真的绑定、绑定哪些，取决于模型的设计取舍；Qwen 与 Mistral 在这一项上的不同选择见 [8.1.2 Qwen 与 Mistral 系列的局部微调](../8.1.2_Qwen%20与%20Mistral%20系列的局部微调：QKV%20Bias%20取舍、Embedding%20权重绑定（Tied%20Weights）/第18讲_封装：CausalLM.md)。

顺带一提，`lm_head` 的形状是 `[vocab_size, hidden_size]`，即 128280 × 7168，和 `embed_tokens` 完全同形——这也是"能绑定"的前提：形状不同就没法共享。

---

## 七、把文件串起来：一次 `from_pretrained` 到底读了几次盘

视频最后跑了一段真实代码。为了在有限资源上演示，up 主先做了 4 bit 量化以减少计算和内存占用（会损失精度，但不影响理解源码），并把模型换成更小的 DeepSeek-V2 版本。[【跳转到 07:37】](https://www.bilibili.com/video/BV1SK4CzHEus/?t=457)

![演示用的加载代码：AutoTokenizer.from_pretrained 与 AutoModelForCausalLM.from_pretrained 两行，后面接 apply_chat_template、generate、decode，右边标注了这两行分别读哪些文件](assets/从仓库文件到模型结构：safetensors%20权重命名如何对应%20config.json%20与%20modeling%20代码/00512.webp)

### 7.1 `tokenizer` 那一行：读两个 JSON

执行 `AutoTokenizer.from_pretrained(...)` 时，模型会读取 `tokenizer.json` 获取词表和分词规则，同时读取 `tokenizer_config.json` 确认分词参数。[【跳转到 08:32】](https://www.bilibili.com/video/BV1SK4CzHEus/?t=512)

![tokenizer_config.json 的内容：add_bos_token、bos_token/eos_token/pad_token 的具体字符串（如 <|begin_of_sentence|>）、model_max_length 131072](assets/从仓库文件到模型结构：safetensors%20权重命名如何对应%20config.json%20与%20modeling%20代码/00443.webp)

分词器的作用可以一句话概括：**把一句话拆成模型能理解的 token id 序列**；反向编码时再把输出的 token 还原成人类可读的文字。[【跳转到 07:23】](https://www.bilibili.com/video/BV1SK4CzHEus/?t=443)

### 7.2 `model` 那一行：四步装配

这是最核心的一行，它按顺序做了四件事 [【跳转到 08:57】](https://www.bilibili.com/video/BV1SK4CzHEus/?t=537)：

1. 从 `config.json` 读取模型结构参数；
2. 通过 `configuration_deepseek.py` 把 JSON 解析成 Python 对象 `DeepseekV3Config`；
3. 根据 `architectures` 里的类名 `DeepseekV3ForCausalLM` 构建模型层级（此时每个 `nn.Module` 已经把自己的参数名注册好了）；
4. 从 safetensors 文件中加载权重矩阵，**`model.safetensors.index.json` 负责权重与模型层之间的映射**。

注意第 3 步和第 4 步的先后关系：**先有名字，后有数据**。模型代码先把"我需要哪些名字、每个名字多大"列成一张清单（`state_dict` 的键与形状），加载器再拿着这张清单去 index 文件里查每个名字在哪个分片、读出来填进去。名字对不上就是 missing/unexpected keys，形状对不上就是 size mismatch。

### 7.3 剩下的三行：模板、生成、解码

- `inputs` 那一行用 chat template 把用户的多轮对话组装成 prompt 格式，再把整个 prompt token 化，生成最终输入的张量 `input_ids`——把 "Who are you" 变成模型能理解的 token id 序列 [【跳转到 08:57】](https://www.bilibili.com/video/BV1SK4CzHEus/?t=537)；
- `model.generate` 最为核心：它会调用模型的 `forward`，从入口类 `DeepseekV3ForCausalLM` 开始一层层向下执行；生成逻辑受 `generation_config.json` 里的策略控制（`temperature`、`top_p`、`max_new_tokens` 等），每一步预测下一个 token 的概率、采样出最有可能的下一个词，循环生成直到结束 [【跳转到 09:22】](https://www.bilibili.com/video/BV1SK4CzHEus/?t=562)；
- 最后 `tokenizer.decode` 做反向查表，把 token id 序列转换回人类可读文本，于是得到了模型的回答 [【跳转到 09:47】](https://www.bilibili.com/video/BV1SK4CzHEus/?t=587)。

到这里，"一个文件 → 一个类 → 一个张量 → 一句话"的链路就闭合了。视频的收尾说得很直白：看清了这些结构，也就真正理解了大模型开源究竟开源的是什么。[【跳转到 10:19】](https://www.bilibili.com/video/BV1SK4CzHEus/?t=619)

---

## 小结

- **一个 HF 仓库只有两族文件**：描述结构的（`config.json` + `configuration_*.py` + `modeling_*.py`）和存放权重的（`*.safetensors` 分片 + `*.index.json`），外加分词器。
- **分片按体积切，不按层切**：685B 参数的 DeepSeek-V3.1 被切成 163 片，每片 4.3 GB 左右；同一层的不同张量可能落在不同分片里。
- **`model.safetensors.index.json` 只做一件事**：`weight_map` 把"张量全名"映射到"分片文件名"，外加 `metadata.total_size`。
- **权重名的语法是 PyTorch 的属性路径**：`model.layers.<i>.<子模块>.<张量>.weight`，每一段都对应 `__init__` 里的一行 `self.xxx = ...`。
- **名字里的数字来自 `config.json`**：`hidden_size` 7168 决定归一化层长度，`intermediate_size` 18432 决定 `gate_proj`/`up_proj` 的输出维，`kv_lora_rank` 512 决定 `kv_b_proj` 的输入维。
- **有没有 `.bias` 由 `bias=` 决定**：`lm_head` 写了 `bias=False`，所以只有一个 `lm_head.weight`；`_tied_weights_keys` 则声明哪些张量属于可绑定名单。
- **加载顺序是"先名字后数据"**：代码先注册出完整的参数名与形状清单，加载器再按 index 文件去分片里取数。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| safetensors | Hugging Face 主推的权重存储格式，一个文件里成千上万个张量按名字索引，加载时不需要执行任意代码 |
| 分片（shard） | 把巨大权重按体积切成多个文件，命名形如 `model-00001-of-000163.safetensors`，便于并行下载与加载 |
| `model.safetensors.index.json` | 索引文件，`weight_map` 记录每个张量全名所在的分片，`metadata.total_size` 记录总字节数 |
| `config.json` | 模型结构参数的纯数据描述：层数、隐藏维度、词表大小、MoE 专家数等 |
| `configuration_*.py` | 解释 `config.json` 的逻辑层，把 JSON 解析成继承 `PretrainedConfig` 的 Python 对象 |
| `modeling_*.py` | 定义模型结构与 `forward` 计算路径的代码，`nn.Module` 的属性名决定了权重名 |
| `architectures` | `config.json` 字段，指向要实例化的模型类名，如 `DeepseekV3ForCausalLM` |
| `auto_map` | 把 `AutoConfig`/`AutoModel` 映射到仓库自带模块与类名的接线表，配合 `trust_remote_code` 使用 |
| `state_dict` | PyTorch 的参数字典，键是属性路径、值是张量；safetensors 文件存的就是它 |
| `_tied_weights_keys` | 类属性，声明哪些权重键属于"可绑定"名单，绑定后输入嵌入与输出层共享参数 |
| `input_layernorm` / `post_attention_layernorm` | 解码器层里两处归一化的属性名，也是权重名里的固定两段 |
| `q_a_proj` / `q_b_proj` | DeepSeek 用低秩分解实现的 Q 投影，拆成两段，因此权重名比 Llama 的 `q_proj` 更长 |
