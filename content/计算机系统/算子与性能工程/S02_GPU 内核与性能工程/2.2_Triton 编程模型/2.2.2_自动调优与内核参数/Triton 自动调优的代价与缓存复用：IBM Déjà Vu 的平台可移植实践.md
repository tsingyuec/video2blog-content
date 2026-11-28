# Triton 自动调优的代价与缓存复用：IBM Déjà Vu 的平台可移植实践

> 视频来源：[How IBM Research Achieved vLLM Platform Portability with Triton Autotuning](https://www.youtube.com/watch?v=GG1qi82J8Hg)（YouTube · Ray Summit 2024，讲者 Benedikt Ringlein，IBM Research）｜时长约 31 分钟
> 导读：上一篇讲「怎么用 `@triton.autotune` 挑参数」，这一篇讲「autotune 在生产环境里为什么用不起、怎么把它变成可缓存的东西」。核心是一组真实数字：Llama-7B 用原生 autotune 冷启动要 62304 秒（约 17 小时），用缓存复用只要 26 秒。本文按「为什么需要 → 效果如何 → 代价多大 → 怎么解决 → 是否安全 → 实测结果」展开。

## 本讲要解决的核心问题（SCQA）

**背景**：Triton 的卖点之一是「一份代码，多平台可比性能」。而性能的关键旋钮是 block size——它决定 tile 怎么切、映射到多少共享内存与缓存。

**冲突**：同一个 kernel，为 A100 调好的 block size 搬到 H100 上就不再最优；换成 AMD、Intel 的卡更不用说。Triton 提供了 `@triton.autotune` 来自动选配置，但**原生 autotune 会把所有候选配置顺序跑一遍**——在 vLLM 这种「几十个 kernel × 十几种 batch size × 上百组配置」的场景里，冷启动时间会膨胀到以「天」为单位。

**疑问**：既然 autotune 结果对「同一块 GPU + 同一份 kernel + 同一个形状」是确定可复现的，那能不能**只调一次、把结果存下来、之后直接复用**？复用又怎么保证不会拿错配置？

**回答（中心思想）**：可以。IBM Research 的做法（Triton Déjà Vu）是把 autotune 从「运行时行为」搬到「构建时行为」：在 CI/CD 阶段针对**声明好的使用场景**做一次调优，把结果写成 `cache.json` 打进容器；运行时用一组哈希（CUDA/PyTorch/Triton 版本、GPU 型号、kernel 代码哈希、key 列表哈希、配置列表哈希、调优参数哈希）判断缓存是否仍然适用。**自动调优负责「选得对」，缓存负责「用得起」，哈希负责「不会用错」。**

---

[【跳转到 01:32】](https://www.youtube.com/watch?v=GG1qi82J8Hg&t=92)

## 一、性能旋钮就是 block size：tile 编程模型的软肋与强项

### 1.1 Triton 的编程模型：你切范围，编译器切线程

Triton 遵循 SPMD，但以 **blocked program** 为单位：一个 program 处理一块 tile，你只写「范围」，编译器负责把范围拆到每个线程、每段共享内存。

```python
thread_i = tl.program_id(axis=1)
i = thread_i * BLOCK_SIZE + tl.arange(0, BLOCK_SIZE)
```

对比 CUDA 里那种 `for (int i = threadIdx.x; i < n; i += blockDim.x)` 的逐线程循环，差别看起来只是「循环 vs 范围」，但演讲者强调这个差别带来了三件好处：**更简单的 liveness 分析**（因此更好的内存/缓存管理）、**更容易自动切分 tile**（不必依赖多面体编译）、**更容易做静态调度**。

![Triton 的 tile 编程模型：CUDA 逐线程映射 vs Triton 范围映射，block 的切法「可以由 autotuner 决定」](assets/Triton%20自动调优的代价与缓存复用：IBM%20Déjà%20Vu%20的平台可移植实践/00414.webp)

[【跳转到 04:40】](https://www.youtube.com/watch?v=GG1qi82J8Hg&t=280)

### 1.2 但性能取决于「怎么切」

演讲者引用了 Triton 文档里那句著名的话——「结果系统工作得惊人地好」——然后补了一句关键的脚注：**性能主要取决于你把这些范围切成多大的 block**。因为 block 大小直接决定它怎么映射到缓存和共享内存。

而 Triton 是 JIT 编译器，block size 就是一个可以在运行时决定的变量。于是问题变成：**对不同模型、不同 GPU，我们需要不同的 block size 配置**。这就是「Triton kernel 的 configuration」这个词的含义。

---

## 二、性能可移植性：同一份 Triton 代码，换卡就掉

[【跳转到 06:29】](https://www.youtube.com/watch?v=GG1qi82J8Hg&t=389)

### 2.1 什么是 performance portability

演讲给的定义是：**程序在不同平台上都能有效运行的能力**。他特别强调：这不只是「Nvidia vs AMD vs Intel」的跨厂商问题，**同一厂商的不同代际之间也一样**——Hopper 相对 Ampere 的架构变化很大，为旧卡调好的参数在新卡上可能明显变慢。

[【跳转到 07:24】](https://www.youtube.com/watch?v=GG1qi82J8Hg&t=444)

### 2.2 vLLM 的现状：几乎没有 kernel 用 autotuner

vLLM 里已经有不少 Triton kernel，但演讲者的观察是：**它们基本都不用 autotuner**，而是用硬编码的 block size、非常简单的 heuristics，或者自定义的 JSON 配置列表。这些配置是开发者在 A100/H100 上调出来的，于是 kernel 在这些卡上表现良好，**换一块卡就不行**。

[【跳转到 08:19】](https://www.youtube.com/watch?v=GG1qi82J8Hg&t=499)

### 2.3 一个具体例子：reshape_and_cache

`reshape_and_cache` 是准备 KV cache 的 kernel。图上横轴是数组元素个数（batch size × head size 等），纵轴是延迟（越低越好）：

- 绿色是 vLLM 的 CUDA 实现；
- 紫色是演讲者用 Triton 重写的实现，**开启了 autotuning**。

在 A100 上紫色已经普遍更快；换到 H100 上，绿色曲线几乎没变——**CUDA kernel 吃不到 Hopper 架构的红利**——而紫色继续下探。原因正是 autotuning：block size 与代码对新架构的适配是自动完成的。

![reshape_and_cache 在 A100 与 H100 上的对比：CUDA 实现在 H100 上没有变快，Triton + autotune 则继续下降](assets/Triton%20自动调优的代价与缓存复用：IBM%20Déjà%20Vu%20的平台可移植实践/00564.webp)

---

[【跳转到 09:56】](https://www.youtube.com/watch?v=GG1qi82J8Hg&t=596)

## 三、autotune 到底在做什么：为每个 shape 选它自己的最优配置

为了讲清 autotune 的作用，演讲者做了一个对照实验：**关掉 autotune，手动写死 block size**，于是得到两条 Triton 曲线——一条大 block（浅紫），一条小 block（深紫）。

结果符合直觉但值得记住：

- **小数组**：小 block 更快（tile 小、边界浪费少、并发高）；
- **大数组**：到某个点之后，大 block 反超（单次搬运的数据多、复用更好）。

![关掉 autotune 后的两条曲线：triton-fp16-tb32 与 triton-fp16-tb2048，交叉点清晰可见](assets/Triton%20自动调优的代价与缓存复用：IBM%20Déjà%20Vu%20的平台可移植实践/00621.webp)

**打开 autotune 后，两条曲线被「合并」成一条包络线**：autotuner 为每个数组尺寸（token 数 × batch size × head 数……）挑出当时最优的那份配置。这就是为什么在这个 kernel 上 Triton 版本总是更快。

这里有一个非常实用的认知：**autotune 的收益来自「按 shape 分段选择」，而不是来自某个万能配置**。这也解释了 `key` 为什么要包含形状信息——如果 key 太粗，autotune 只能给所有形状同一份配置，包络线就退化回单条曲线。

---

## 四、代价：为什么 autotune 在生产环境里「用不起」

[【跳转到 10:46】](https://www.youtube.com/watch?v=GG1qi82J8Hg&t=646)

### 4.1 顺序评估 + 巨大搜索空间

Triton 原生 autotuner 的实现方式是**顺序评估所有候选配置**。耗时取决于两件事：kernel 本身，以及搜索空间的大小。演讲者给出的判断很直接：**在极端情况下可能要几天**。

对一个推理服务来说这是致命的——「启动一个新服务要 3 天到 8 天才能接请求」，显然不可能放进生产系统。

于是矛盾成型：**要跨硬件的最优性能就必须 autotune；但 autotune 在生产环境里成本高到不可接受。**

### 4.2 把成本算清楚

用一个粗略的模型表达这个成本：

$$
T_{\text{autotune}} \approx N_{\text{kernel}} \times N_{\text{shape}} \times N_{\text{config}} \times t_{\text{bench}}
$$

其中 $N_{\text{kernel}}$ 是参与调优的 kernel 数，$N_{\text{shape}}$ 是每种 kernel 需要覆盖的形状数，$N_{\text{config}}$ 是候选配置数，$t_{\text{bench}}$ 是单次测速耗时。

代入演讲后面给出的 Llama-7B 设定（5 个 Triton kernel、10 种 batch size、每种平均 200 组配置），总共是 $5 \times 10 \times 200 = 10000$ 次测速；实测总耗时 62304.3 秒，折算下来**平均每次测速约 6.2 秒**。这个数量级说明：autotune 的成本不是「稍微慢一点」，而是「配置数乘出来就爆炸」。

---

## 五、Déjà Vu：把 autotune 结果变成可交付的缓存

[【跳转到 11:36】](https://www.youtube.com/watch?v=GG1qi82J8Hg&t=696)

### 5.1 核心观察

演讲者的观察是：**对给定的平台（给定 GPU）和给定的 kernel 配置，autotuner 的决定是可以预测的**。同一个矩阵乘在 A100 上跑，最优配置永远是那一个。既然如此，为什么要每次启动都重新搜一遍？

于是他们做了 **Triton Déjà Vu**：给 Triton 加一个「既视感」机制——**记住它之前做过什么**。

[【跳转到 12:40】](https://www.youtube.com/watch?v=GG1qi82J8Hg&t=760)

### 5.2 流程：多了一步「声明使用场景」

原来的流程是「写 kernel → 给一组候选配置 → 运行时调优」。Déjà Vu 在前面插入了**第二份清单：使用场景定义**（哪些模型、哪些 batch size、哪些形状）。因为调优决策依赖数组形状，不声明场景就没法预调优。

之后的链路是：

1. **Cache preparation**（缓存准备）：对所有声明的场景 × 所有目标硬件，选出最优配置；
2. 写成一个简单的 **`cache.json`**；
3. **Container build**：把 JSON 打进容器镜像；
4. 部署后**直接可用**，运行时不再调优。

整条链路可以完全自动化，并且**带变更门控**：如果 Triton kernel 代码没变，重建容器时不需要重跑 cache preparation。

![Déjà Vu 的流程：kernel 开发 → 配置清单 + 使用场景清单 → CI/CD 中的缓存准备 → cache.json → 容器构建 → 快速部署](assets/Triton%20自动调优的代价与缓存复用：IBM%20Déjà%20Vu%20的平台可移植实践/00760.webp)

[【跳转到 15:16】](https://www.youtube.com/watch?v=GG1qi82J8Hg&t=916)

### 5.3 配置不是「二三十个」，而是「几百个」

一个反直觉的发现：他们原以为每个 kernel 准备 20～30 组配置就够，实际发现**要做到最好需要上百组**。而配置一多，Triton 那种「列表式」遍历就不够用了，需要按**配置空间**（configuration space）来组织，而不是平铺的列表。此外还要保留一套 **heuristics 兜底**，用于生产中出现没优化过的边角情况。

[【跳转到 21:45】](https://www.youtube.com/watch?v=GG1qi82J8Hg&t=1305)

### 5.4 缓存长什么样

在演示环节，他打开了一个真实的缓存文件，前几行是元信息：

```
"signature": "JITFunction(vllm.attention.ops.rocm_flash_attn.attn_fwd)",
"total_bench_time_s": 18332.4,
"evaluated_configs": 72,
"cache": {
  "0": {"0": {"0": {"0": "16384", "32": "1", "0": "16384", "32": "1",
     ... "BLOCK_M": 64, "BLOCK_N": 64, "PRE_LOAD_V": true,
     "num_warps": 4, "num_ctas": 1, "num_stages": 8, "maxnreg": null}}}
}
```

这里有三个信息值得注意：

- **`signature`** 是人类可读的标签，方便排查「这个缓存文件是给哪个 kernel 的」；
- **`evaluated_configs` 与 `total_bench_time_s`** 记录了这次调优花了多少代价，本身就是审计信息；
- **最终存下来的是完整的 `triton.Config` 内容**：除了 `BLOCK_M/BLOCK_N`，还有 `num_warps`、`num_stages`、`num_ctas`、`PRE_LOAD_V` 这些参数——**一次 autotune 调的不只是 block size，而是一整组内核参数**。

![缓存文件的内容：signature、调优耗时、评估过的配置数，以及每个 case 对应的最优配置（含 num_warps、num_stages）](assets/Triton%20自动调优的代价与缓存复用：IBM%20Déjà%20Vu%20的平台可移植实践/01327.webp)

[【跳转到 14:01】](https://www.youtube.com/watch?v=GG1qi82J8Hg&t=841)

## 六、复用的安全性：一组哈希决定「能不能用」

缓存复用最大的风险是「拿错配置」——环境变了，旧结果不再成立。演讲者列出的判据是一份很值得抄的清单：

| 判据 | 例子 |
| --- | --- |
| CUDA runtime 版本 | `12.4` |
| PyTorch 版本 | torch 2.4.0（cu121 构建） |
| Triton 版本 | `3.0.0`（未来会用 git commit hash） |
| GPU 型号 | `NVIDIA_H100_80GB_HBM3` |
| JIT 函数代码哈希 | `JITFunction.fn.hash` |
| autotuner key 列表的哈希 | 决定「按什么维度分组」 |
| 候选配置列表的哈希 | 配置变了，结果就不可比 |
| autotuner 可选参数的哈希 | 例如 benchmark 时长 |
| triton-dejavu 自身次版本号 | 框架行为变化 |
| 函数签名（可选） | 人类可读标签，如 `flash_attn` |

两条设计原则藏在里面：

1. **只对「会影响调优结果」的东西做哈希**。他们特意说明：不需要对依赖库做哈希，因为那与部署无关——哈希太粗会导致缓存永远失效，太细又会导致误用。
2. **key 列表本身也要进哈希**。因为 key 决定了「按什么粒度分组调优」，key 变了，缓存里的分组结构就不再对应。

![复用判据清单：CUDA/PyTorch/Triton 版本、GPU 型号、JIT 函数哈希、key 列表哈希、配置哈希、调优参数哈希](assets/Triton%20自动调优的代价与缓存复用：IBM%20Déjà%20Vu%20的平台可移植实践/00841.webp)

---

## 七、实测：跨厂商、端到端与启动时间

[【跳转到 16:00】](https://www.youtube.com/watch?v=GG1qi82J8Hg&t=960)

### 7.1 跨厂商：同一份 Triton 代码在 AMD 与 Nvidia 上

他们直接拿 AMD ROCm 团队写的 Flash Attention Triton kernel，在 Nvidia A100 上跑，和 PyTorch 的 `flash_attn` 包对比（`float16`，A100-40GB）：

- 用**匹配的配置**（autotune 过）：小 token 数上 Triton 版本约快 1.1 倍，大 token 数上约 0.85 倍，差距不大；
- 用**AMD 的配置**跑在 Nvidia 上：只能拿到约 70% 的性能；
- **完全关掉 autotune**：性能掉到约 15%，也就是 6～7 倍的减速。

![同一份 Triton Flash Attention 代码在 A100 上的表现：配置不匹配会掉到 70%，关掉 autotune 会掉到 15%](assets/Triton%20自动调优的代价与缓存复用：IBM%20Déjà%20Vu%20的平台可移植实践/01010.webp)

结论很干脆：**跨平台可移植性是可以做到的，但前提是你真的在用 autotuning。**

[【跳转到 17:40】](https://www.youtube.com/watch?v=GG1qi82J8Hg&t=1060)

### 7.2 端到端：Llama-7B 的 TTF vs 吞吐

把 vLLM 里的自定义 CUDA kernel 全部换成 Triton（`silu_and_mul`、`reshape_and_cache`、`RMSNorm`、AMD 版 `flash_attention`），在 A100 上测首 token 时间（TTFT）与吞吐：

- 纯 Triton + autotune：大 batch 下只比上游 vLLM 0.6 慢约 8%，**小用户数下反而更快**；
- 纯 Triton 但**不开 autotune**：与上游相差约 30%。

![Llama-7B 端到端：纯 Triton + autotune 贴近上游 vLLM，关掉 autotune 则出现明显差距](assets/Triton%20自动调优的代价与缓存复用：IBM%20Déjà%20Vu%20的平台可移植实践/01085.webp)

[【跳转到 19:20】](https://www.youtube.com/watch?v=GG1qi82J8Hg&t=1160)

### 7.3 启动时间：从 17 小时到 26 秒

| 模型 | 调优规模 | 原生 autotune | Déjà Vu |
| --- | --- | --- | --- |
| Llama-7B | 5 个 Triton kernel，10 种 batch size，每种约 200 组配置 | 62304.3 s（1×A100，约 17 小时） | 26.23 s |
| Mixtral-8x7B | 1 个 Triton kernel（fused MoE），18 种 batch size，每种约 100 组配置 | 497380 s（4×L40S）/ 716646 s（2×H100，约 8 天） | 77 s / 56 s |

演讲者自己也说，这个「五个数量级」的对比有点夸张——现实中没人会真的在生产环境里跑 8 天的 autotune。但数字说明的问题是真实的：**原生 autotune 的冷启动成本与「可部署」之间差着好几个数量级**。

![启动时间对比：Llama-7B 62304.3 s → 26.23 s；Mixtral-8x7B 716646 s → 56 s](assets/Triton%20自动调优的代价与缓存复用：IBM%20Déjà%20Vu%20的平台可移植实践/01210.webp)

演示部分也印证了这一点：启动 Docker 容器、加载 Déjà Vu 缓存、起 OpenAI 兼容服务，大约 30 秒后就能发请求，而且**请求本身没有额外的调优延迟**。

[【跳转到 21:14】](https://www.youtube.com/watch?v=GG1qi82J8Hg&t=1274)

## 八、讨论与局限：演讲者自己承认的三件事

问答环节里有几个诚实的补充，对工程判断很有价值：

1. **大多数生产用户其实没在用 autotune**。他们通常有非常同构的硬件，于是手工调一次 kernel，固定一个默认配置一直用。这也是为什么这个特性至今没进 Triton 的优先级列表。
2. **「凭直觉调参」会输**。演讲者说自己做过很多计算机体系结构的工作，一度认为能靠直觉找到最优配置——「但我一直被自己的算法打败」。所以他的建议是：即使你觉得自己知道最优配置，也应该用 autotuning。
3. **缓存要能增量复用**。如果之后想扩大配置空间，缓存机制会按哈希清单判断哪些结果还能复用、哪些必须重算，「能复用就尽量复用，因为算力最终是贵的」。另外，一个 kernel 一份 JSON：多个 kernel 就是多个文件，同一个 kernel 的不同场景则共用一份缓存。

---

## 小结

- **block size 是 Triton 的性能主旋钮**：tile 怎么切，决定它怎么映射到共享内存与缓存；不同模型、不同 GPU 需要不同配置。
- **autotune 的收益来自「按 shape 分段选择」**：小数组适合小 block，大数组适合大 block，autotune 把两条曲线合成一条包络线。
- **原生 autotune 的成本是乘出来的**：$N_{\text{kernel}} \times N_{\text{shape}} \times N_{\text{config}} \times t_{\text{bench}}$，Llama-7B 的实测是 62304 秒。
- **解法是把调优搬到构建时**：声明使用场景 → CI/CD 里预调优 → 写 `cache.json` → 打进容器 → 运行时零调优。
- **缓存必须配一套判据**：版本、GPU 型号、kernel 代码哈希、key 列表哈希、配置哈希、调优参数哈希，缺一项就可能用错配置。
- **配置数量比想象的多**：20～30 组不够，上百组才够；要用配置空间组织，并保留 heuristics 兜底。
- **可移植性有代价也有回报**：同一份 Triton 代码跨 AMD/Nvidia 可行，但配置不匹配会掉到 70%，关掉 autotune 会掉到 15%。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| performance portability | 同一份程序在不同硬件上都能有效运行的能力，同厂商不同代际也算 |
| tile / block size | 一个 program 处理的数据块大小，直接决定缓存与共享内存的映射方式 |
| autotuner | Triton 的自动配置选择器：编译所有候选配置、逐个测速、选最快的 |
| autotuner key | 决定「按什么维度分组调优并缓存」的键，通常是形状参数 |
| configuration space | 把候选配置按维度组织成的空间，比平铺列表更适合上百组配置 |
| cache preparation | 在 CI/CD 阶段预先跑完 autotune、生成 `cache.json` 的环节 |
| `cache.json` | 记录「场景 → 最优配置」的缓存文件，随容器一起分发 |
| JIT 函数哈希 | kernel 源码的指纹，代码一变缓存即失效 |
| heuristics 兜底 | 遇到未预调优的边角形状时的保守回退策略 |
| TTF / TTFT | Time To First Token，首 token 延迟，推理服务的关键指标 |
| KV cache | 推理时缓存历史 token 的 K/V，`reshape_and_cache` 负责整理它 |