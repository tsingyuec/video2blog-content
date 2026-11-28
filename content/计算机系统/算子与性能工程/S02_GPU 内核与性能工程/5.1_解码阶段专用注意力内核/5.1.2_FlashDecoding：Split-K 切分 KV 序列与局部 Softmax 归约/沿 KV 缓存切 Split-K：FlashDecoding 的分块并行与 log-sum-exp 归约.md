# 沿 KV 缓存切 Split-K：FlashDecoding 的分块并行与 log-sum-exp 归约

> 视频来源：[Why Long Prompts Leave Your GPU Idle (Flash-Decoding)](https://www.youtube.com/watch?v=wUR2E46EWeA)（YouTube · The Agentic Enterprise，讲者 Manik Hanuja）｜时长约 12.5 分钟
> 导读：一支围绕 PyTorch Flash-Decoding 微基准展开的精讲。它先把「decode 时任务数只剩 batch × heads」算清楚，再逐帧讲 Split-K 的三步——切缓存、并行算局部注意力、用第二个内核按 log-sum-exp 归约，最后落到「切分数怎么定、和 GQA 怎么配合、归约本身要付什么代价」。本文按「问题 → 切分 → 局部结果 → 归约 → 收益 → 工程细节」组织。

## 本讲要解决的核心问题（SCQA）

**背景**：FlashAttention 把注意力拆成能塞进片上 SRAM 的小块，为每一行维护一个运行最大值和一个运行和，因此 softmax 仍然精确，同时从不把完整的分数矩阵写回 HBM。它的并行方式是「每块 query 行 × 每个 head × batch 里每条序列」各派一个任务。

**冲突**：decode 时新 token 只有一行 query，于是「每块 query 行」这个维度塌缩成 1，任务数只剩 batch × head 数。一条 64K 的长 prompt、batch 为 1、16 个 query head，就只有 16 个任务，而 A100 有 108 个 SM——大部分 SM 无事可做，耗时比同样缓存量的短 prompt 批处理慢了近六倍。

**疑问**：既然 query 没法切，请求里还有什么维度可以切？切开之后 softmax 还能算对吗？切多少块、什么时候值得切？

**回答（中心思想）**：decode 时请求里真正大的不是 query 而是 KV 缓存，所以 FlashDecoding（Split-K）沿**缓存序列维**切块：每个块独立算一份局部注意力，除了局部输出还多写一个 $\mathrm{LSE}$（log-sum-exp）标量；再由第二个内核用这些 $\mathrm{LSE}$ 把各块的局部答案缩放后相加。这不是近似——softmax 本来就可以分块算，FlashAttention 在块内用的就是同一套技巧，FlashDecoding 只是把它再用到块间一层。代价是每个 split 要多写一份临时结果、多一次归约内核，所以切多少块要按「公平份额」定，短请求根本不切。

## 一、先把账算清：decode 时任务数只剩 batch × heads

### 1.1 decode 的输入形状决定了并行维度

decode 是逐 token 写出答案的阶段：此前每个 token 的 key 和 value 已经存进显存中的 KV cache，每个新 token 只计算自己的 key 和 value，然后拿自己这一行 query 去和缓存里的全部内容打分。[【跳转到 01:30】](https://www.youtube.com/watch?v=wUR2E46EWeA&t=90)

FlashAttention 的工作方式是把注意力拆成小块、放进芯片上的快速内存（SRAM）里算，并为每一行维护运行最大值与运行和，所以 softmax 是精确的，而且完整的分数矩阵从不落回 GPU 主存。[【跳转到 02:09】](https://www.youtube.com/watch?v=wUR2E46EWeA&t=129)

![FlashAttention 把分数矩阵切成小块放进片上 SRAM，完整分数矩阵不落 HBM](assets/沿%20KV%20缓存切%20Split-K：FlashDecoding%20的分块并行与%20log-sum-exp%20归约/00129.webp)

问题出在任务划分上。FlashAttention 2 为「每一块 query 行 × 每个 head × batch 里每条序列」各派一个任务；到了 decode，一行 query 就是一个块，于是任务只能来自 batch 和 head：

$$
\text{jobs} = \text{batch} \times \text{heads}
$$

FlashAttention 2 的论文明确写过，这种调度在任务数达到 80 个左右时才高效；而 A100 有 108 个 SM，每个任务占一个 SM。[【跳转到 02:41】](https://www.youtube.com/watch?v=wUR2E46EWeA&t=161)

![jobs = batch × heads：FA2 论文说任务数要到 80 个左右才能用满 108 个 SM](assets/沿%20KV%20缓存切%20Split-K：FlashDecoding%20的分块并行与%20log-sum-exp%20归约/00178.webp)

### 1.2 基准数据：同样多的缓存 token，长 prompt 慢近六倍

视频引用的基准来自 PyTorch 博客的 Flash-Decoding 微基准（Dao、Haziza、Massa、Sizov，2023 年 10 月）：A100、FP16、16 个 query head（每个宽 128），它们共享 2 个 key/value head。[【跳转到 00:27】](https://www.youtube.com/watch?v=wUR2E46EWeA&t=27)

基准的每一行缓存 token 总数都是 64K，只是 batch 与每条长度的组合不同：

| batch × 每条 token 数 | 缓存 token 总数 | FlashAttention 2 耗时 |
| --- | --- | --- |
| 256 × 256 | 64K | 约 350–400 µs |
| 16 × 4,096 | 64K | 约 350–400 µs |
| 2 × 32,768 | 64K | 约 1,150 µs |
| 1 × 65,536 | 64K | 约 2,300 µs |

![同样的 64K 缓存 token：batch 从 256 降到 1，FlashAttention 2 的耗时从 350–400 µs 爬到 2,300 µs](assets/沿%20KV%20缓存切%20Split-K：FlashDecoding%20的分块并行与%20log-sum-exp%20归约/00225.webp)

视频对这张表的解读很克制：最后两步里 batch 每减半、每条长度每翻倍，耗时大约就翻倍；但表格同时改了两个变量，所以它不能证明任务数是唯一原因，只是与「可分的任务变少」吻合。[【跳转到 03:49】](https://www.youtube.com/watch?v=wUR2E46EWeA&t=229) 长上下文还会让情况更糟：上下文越长每个请求占的显存越多，于是被迫把 batch 压小，任务数进一步减少。[【跳转到 04:08】](https://www.youtube.com/watch?v=wUR2E46EWeA&t=248)

## 二、切分：把 KV 缓存切成块，切本身不花 GPU 算力

### 2.1 切的是缓存，不是 query

batch 为 1、query 只有一行，但请求里仍有一样东西非常大——64K token 的缓存。于是 FlashDecoding 沿缓存切分工作：把缓存切成若干块（chunk），对每一块并行跑 FlashAttention，再把各块的答案合并成一个。[【跳转到 04:26】](https://www.youtube.com/watch?v=wUR2E46EWeA&t=266)

![把 64K token 的 keys/values 沿序列维切成四块，每块各自处理](assets/沿%20KV%20缓存切%20Split-K：FlashDecoding%20的分块并行与%20log-sum-exp%20归约/00294.webp)

一个容易被忽略的细节：**切分本身不消耗 GPU 算力**。这些块只是对已有缓存的内存视图，论文里说这一步并不在 GPU 上执行任何运算。[【跳转到 04:57】](https://www.youtube.com/watch?v=wUR2E46EWeA&t=297) 换句话说，Split-K 的第一刀是「改索引」，不是「搬数据」。

### 2.2 每块独立算一份局部注意力

切完之后，注意力对每个块分别并行计算：每个块拿自己那一段 key 给这一行 query 打分，用自己的那一段 value 拼出一个局部答案，并为每一行额外记下一个数，叫做 log-sum-exp。[【跳转到 05:03】](https://www.youtube.com/watch?v=wUR2E46EWeA&t=303)

![每个块用自己那段 keys/values 算出自己的 scores 和局部答案，四块完全并行](assets/沿%20KV%20缓存切%20Split-K：FlashDecoding%20的分块并行与%20log-sum-exp%20归约/00315.webp)

用公式写出来更清楚。设第 $i$ 个块覆盖的位置集合为 $S_i$，这一行 query 是 $q$，缩放因子为 $\sqrt{d}$，那么块内先算分数，再算三个量：

$$
s_{ij} = \frac{q \cdot k_j}{\sqrt{d}},\quad
m_i = \max_{j \in S_i} s_{ij},\quad
\ell_i = \sum_{j \in S_i} e^{s_{ij} - m_i}
$$

$$
o_i = \sum_{j \in S_i} e^{s_{ij} - m_i}\, v_j,\qquad
\text{局部答案} = \frac{o_i}{\ell_i}
$$

这里的 $m_i$ 是块内最大值，作用是让指数不超过 1、不溢出；$\ell_i$ 是块内的指数和；$o_i$ 是块内按指数加权的 value 之和。视频里说的那个「额外记下的数」就是

$$
\mathrm{LSE}_i = m_i + \log \ell_i
$$

它记录的是这一块的分数总共带了多少权重。[【跳转到 05:19】](https://www.youtube.com/watch?v=wUR2E46EWeA&t=319)

## 三、归约：用 log-sum-exp 把局部答案缩放后相加

### 3.1 第二个内核负责合并

局部结果不能直接相加：每个块的 $\ell_i$ 只统计了自己那一段，分母不一样；而且各块的 $m_i$ 也不同，指数基准不一致。FlashDecoding 的做法是让**第二个内核**做合并：它用每个块的 log-sum-exp 作为指数去缩放该块的局部答案，再把它们加起来。[【跳转到 05:24】](https://www.youtube.com/watch?v=wUR2E46EWeA&t=324)

![第二个内核做 merge：每个局部答案先按自己那块块的 LSE 缩放，再相加](assets/沿%20KV%20缓存切%20Split-K：FlashDecoding%20的分块并行与%20log-sum-exp%20归约/00336.webp)

写成公式，就是 online softmax 的合并规则：先取全局最大值，再把各块的指数和搬到同一基准下相加，最后按各自的权重份额重缩放局部答案。

$$
m = \max_i m_i,\qquad
\ell = \sum_i \ell_i\, e^{m_i - m}
$$

$$
o = \sum_i \left(\frac{o_i}{\ell_i}\right)\cdot \frac{\ell_i\, e^{m_i - m}}{\ell}
$$

第二个公式里，$\ell_i e^{m_i-m}/\ell$ 就是第 $i$ 块在全局 softmax 里占的份额——它既修正了「分母只统计了一段」的问题，也修正了「指数基准不同」的问题。

### 3.2 这不是近似：softmax 可以一块一块地算

视频专门用一页幻灯片回答这个疑问：**这是近似吗？不是。** softmax 本来就可以分块算出来，FlashAttention 合并自己的分块时用的就是同一套办法；FlashDecoding 只是把这个技巧用在了两层——块内一层、块间一层。数学上得到的结果与一次性算完全一样。[【跳转到 05:40】](https://www.youtube.com/watch?v=wUR2E46EWeA&t=340)

![两层归约：块内按 tile 合并，块间按 LSE 合并，结果与一次算完完全相同](assets/沿%20KV%20缓存切%20Split-K：FlashDecoding%20的分块并行与%20log-sum-exp%20归约/00355.webp)

视频还提到一个实用性质：这个合并**与顺序无关**，所以各块可以按任意顺序合并。[【跳转到 06:01】](https://www.youtube.com/watch?v=wUR2E46EWeA&t=361) 这一点直接决定了后面调度器可以自由地按「谁空给谁」派活。

## 四、收益：从「随长度线性变慢」到「几乎恒定」

回到同一张基准表，加上 FlashDecoding 的柱子：一直到 64K token 的每一行，它的耗时都在约 56 到 78 微秒之间，从 batch 为 256 的短 prompt 一路到那条单条长 prompt，论文称之为「到 64K 几乎恒定」。[【跳转到 06:09】](https://www.youtube.com/watch?v=wUR2E46EWeA&t=369)

![FlashDecoding 在每一行都压到 56–78 µs，而 FlashAttention 2 随 batch 缩小、长度变长而上升](assets/沿%20KV%20缓存切%20Split-K：FlashDecoding%20的分块并行与%20log-sum-exp%20归约/00385.webp)

具体数字：

- 64K 时约 64 µs，对比 FlashAttention 2 的 2,300 µs，约 **36 倍**；
- 128K 时约 107 µs，对比约 4,600 µs；
- 端到端在 CodeLlama 34B、batch 为 1 时，论文报告在很长序列上生成速度最高快 **8 倍**，测试范围从 512 token 到 64K。

视频在这里给了一句很重要的提醒：任务数能解释全部差距吗？这张表回答不了——FlashDecoding 在表格最上面一行也更快，而那里 FlashAttention 2 本来就有 4,096 个任务，论文并没有拆解这部分差距。作者愿意保留的结论是这个**形状**：FlashAttention 2 的耗时随 batch 缩小、每条变长而上升，而 FlashDecoding 到 64K 几乎不动。至于那些微秒数，它们属于那块 A100，用在自己的 GPU 上之前应当自己测。[【跳转到 06:46】](https://www.youtube.com/watch?v=wUR2E46EWeA&t=406)

## 五、切分数怎么定：公平份额调度

切分不是免费的：每个 split 都要把局部答案写进一块临时缓冲区，最后还要一次合并。所以真正的问题是「切几块、切谁」。[【跳转到 07:42】](https://www.youtube.com/watch?v=wUR2E46EWeA&t=462)

![每个 split 写一份临时结果到 scratch buffer，再由 merge 步骤合成最终输出](assets/沿%20KV%20缓存切%20Split-K：FlashDecoding%20的分块并行与%20log-sum-exp%20归约/00470.webp)

FlashDecoding 论文的调度器给出了一个很简洁的规则：

1. **算一份公平份额**：把整个 batch 的缓存长度加起来，除以即将在 decode 阶段运行的线程块数量，得到每个线程块应分到的工作量；
2. **长的切开、短的整条跑**：比一份份额更长的请求被切成不超过一份的块；比一份还短的请求整条一起跑，答案直接写进输出，根本不做合并；
3. **长的先派**：把各块按从长到短分发，每块交给当前累计工作量最小的线程块，目的是让 SM 不空转；
4. **不用原子加合并**：这样相同的长度每次都会得到相同的合并顺序，结果可复现。

[【跳转到 07:56】](https://www.youtube.com/watch?v=wUR2E46EWeA&t=476)

这套规则同时回答了「切分数怎么选」和「何时不值得切」：切分数由「缓存总长 ÷ 线程块数」决定，而不是拍一个固定值；比公平份额还短的请求压根不进入切分路径。

## 六、与 GQA 的配合：一次加载服务八个 query head

基准里的模型用的是分组查询注意力（GQA）：多个 query head 共享一个 key head 和一个 value head，这里是 16 个 query head 共享 2 个 key/value head，也就是每组 8 个。

如果给每个 query head 各分一个线程块，那么八个块会各自把同一份 key 和 value 加载一遍——同样的数据从 HBM 读八次。FlashInfer 的做法是把一组里的 8 个 query head 叠成行，并把 key/value head 映射到不同的线程块，这样一次把缓存载入共享内存，就服务了组里全部 8 个 query head；于是在 decode 时，你的一行 query 变成了八行。[【跳转到 08:38】](https://www.youtube.com/watch?v=wUR2E46EWeA&t=518)

![FlashInfer 把同组 8 个 query head 叠成行，一次加载的 KV 服务 8 个 head](assets/沿%20KV%20缓存切%20Split-K：FlashDecoding%20的分块并行与%20log-sum-exp%20归约/00540.webp)

视频补充说，FlashInfer 论文在 query 长度较短时更偏好这种做法，并提到 TensorRT-LLM 的 XQA 内核探索了类似的思路。[【跳转到 09:22】](https://www.youtube.com/watch?v=wUR2E46EWeA&t=562) 对 Split-K 来说，这一条的意义是：**切分维度（缓存）与共享维度（KV head）可以叠加**——先把同一份缓存摊给多个 query head，再沿缓存切块，两个层次的并行度一起用。

## 七、归约本身的代价：等待最大值

Split-K 的归约有一个隐藏成本。注意力的每一块在取指数之前都会先减去一个运行最大值，这样不会溢出；而一旦出现更大的最大值，你就得回头把先前那些局部结果更新到一致。FlashDecoding++ 论文实测这次同步更新占注意力时间的 **18.8%**（Llama 2 7B、A100、输入 1024 token）。[【跳转到 09:30】](https://www.youtube.com/watch?v=wUR2E46EWeA&t=570)

![局部结果要跟着全局最大值回填，FlashDecoding++ 实测这次同步更新占注意力时间 18.8%](assets/沿%20KV%20缓存切%20Split-K：FlashDecoding%20的分块并行与%20log-sum-exp%20归约/00590.webp)

但 softmax 有一个性质：只要指数不溢出也不缩到零，减去哪个数得到的概率都一样。于是 FlashDecoding++ 干脆提前选一个**固定的数**，依据是该模型实际产生的分数分布：对 Llama 2 7B，超过 99.99% 的分数落在 $-16.8$ 到 $6.5$ 之间，于是注意力的每一块都用这同一个固定值，没有哪一块需要等别人的最大值；如果某个分数落到安全范围之外，那一行就按常规方式重算。[【跳转到 10:08】](https://www.youtube.com/watch?v=wUR2E46EWeA&t=608)

![固定最大值的思路：从模型实际分数分布里选一个安全区间，块间就不必互相等待](assets/沿%20KV%20缓存切%20Split-K：FlashDecoding%20的分块并行与%20log-sum-exp%20归约/00620.webp)

视频对这个技巧的态度同样克制：它依赖模型——对 OPT 6.7B，99.99% 的分数分布在约 $-497$ 到 $363$ 之间，论文在那里就没有用这个技巧；而且它的加速是在整个引擎层面测的，引擎里还有别的改动，所以不该把加速比单独归给这一个技巧。[【跳转到 10:45】](https://www.youtube.com/watch?v=wUR2E46EWeA&t=645)

![Llama 2 7B 的分数集中在 -16.8 到 6.5，OPT 6.7B 却横跨 -497 到 363：固定最大值不是通用技巧](assets/沿%20KV%20缓存切%20Split-K：FlashDecoding%20的分块并行与%20log-sum-exp%20归约/00660.webp)

## 八、工程落地：先查内核，再谈加速

视频最后给了一份可操作的清单：

- 如果你的流量是「小 batch 的长 prompt」，先查你的服务栈在 decode 时跑的是哪个注意力内核、它是否沿缓存切分；
- FlashDecoding 从 FlashAttention 包 **2.2** 版起就已包含，xformers 从 **0.0.22** 版起也有；在支持的情况下，调度器会按问题规模在 FlashDecoding 和普通 FlashAttention 之间挑选；
- 别指望切分在任何地方都有用：比公平份额还短的请求不需要切分，调度器会整条跑，而切分意味着临时缓冲区里放多份答案、最后再做一次合并。

[【跳转到 11:06】](https://www.youtube.com/watch?v=wUR2E46EWeA&t=666)

视频用一句话收尾：在 decode 阶段，去找你请求里**真正大的那一部分**，并行的工作就在那里。[【跳转到 12:19】](https://www.youtube.com/watch?v=wUR2E46EWeA&t=739)

## 小结

- decode 的并行度来自 $\text{batch}\times\text{heads}$；一行 query 让「query 块」这个维度消失，16 个任务对 108 个 SM 就是大部分空转。
- Split-K 沿 **KV 缓存序列维**切块，切分只是内存视图，不在 GPU 上执行运算。
- 每个块独立算局部注意力，除局部输出外多写一个 $\mathrm{LSE}_i = m_i + \log \ell_i$。
- 第二个内核按 online softmax 的 rescale 规则合并：$m=\max_i m_i$、$\ell=\sum_i \ell_i e^{m_i-m}$、$o=\sum_i (o_i/\ell_i)\cdot \ell_i e^{m_i-m}/\ell$，结果精确、与合并顺序无关。
- 收益是「到 64K 几乎恒定」：64K 约 64 µs 对 2,300 µs（约 36 倍），128K 约 107 µs 对 4,600 µs。
- 切分数由「缓存总长 ÷ 线程块数」的公平份额决定；比一份份额短的请求整条跑、不合并，长的先派给最空的线程块，且不用原子加以保证顺序确定。
- 与 GQA 叠加时，把同组 8 个 query head 叠成行、一次加载服务 8 个 head（FlashInfer 的做法），query 行数从 1 变 8。
- 归约要付「等待最大值」的代价（实测 18.8%）；FlashDecoding++ 用固定最大值绕开它，但依赖模型的分数分布，不是通用手段。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| Split-K / FlashDecoding | 沿 KV 缓存序列维把一次注意力拆成多个 split 并行算，再归约合并 |
| chunk（块） | 切分后的一段 KV 缓存，是已有缓存的内存视图，不复制数据 |
| 局部最大值 $m_i$ | 第 $i$ 块内分数的最大值，用来把指数压到 1 以下防溢出 |
| 局部指数和 $\ell_i$ | 第 $i$ 块内 $\sum_j e^{s_{ij}-m_i}$，即该块的总权重 |
| 局部输出 $o_i$ | 第 $i$ 块内按指数加权的 value 之和，$\ell_i$ 是其分母 |
| log-sum-exp（LSE） | $m_i + \log \ell_i$，把「最大值 + 指数和」压成一个数，供归约时缩放用 |
| 归约内核（merge kernel） | 第二个内核，按 LSE 把各块局部答案重缩放后相加 |
| 公平份额（fair share） | 缓存总长除以线程块数，决定哪些请求要切、切多大 |
| GQA | 分组查询注意力，多个 query head 共享一个 KV head，可把同组 head 叠成行共用一次加载 |
| 运行最大值 | FlashAttention 块内维护的最大值，出现更大值时需回填更新局部结果 |