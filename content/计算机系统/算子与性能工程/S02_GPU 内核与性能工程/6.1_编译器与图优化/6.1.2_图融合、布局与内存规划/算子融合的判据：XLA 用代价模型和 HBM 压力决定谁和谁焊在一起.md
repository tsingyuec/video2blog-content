# 算子融合的判据：XLA 用代价模型和 HBM 压力决定谁和谁焊在一起

> 视频来源：[JAX/OpenXLA DevLab 2025 - Operator Fusion](https://www.youtube.com/watch?v=yydJ6ZGCiVQ)（YouTube · OpenXLA DevLab，讲者 Kai（Google GPU 编译器团队负责人）与 Karthik（TPU 编译器））｜时长约 51 分钟
> 导读：这是 OpenXLA 开发者大会的「算子融合」专场，前半段讲 GPU 侧怎么用代价模型加自动调优挑融合，后半段用大量 HLO 截图讲 TPU 侧的融合判据——广播为什么必融、多消费者算子为什么犹豫、异步集合通信融合为什么会把显存撑爆。本文按「为什么融 → 融是什么 → 凭什么判 → 怎么验证 → 有哪些机制 → 怎么手动干预」重排，最后落到布局与内存这笔总账上。

## 本讲要解决的核心问题（SCQA）

**背景**：今天的加速器上，绝大多数热门负载是**访存受限**（memory bound）的——算力有富余，带宽不够用。所以编译器最值钱的一项优化就是**算子融合**（operator fusion）：把几个算子合成一个内核，让中间结果留在片上，不要往显存（HBM，High Bandwidth Memory，显卡/加速器上那块大容量高带宽内存）里写一遍再读回来。 [【跳转到 03:15】](https://www.youtube.com/watch?v=yydJ6ZGCiVQ&t=195)

**冲突**：但融合不是「越多越好」。把两个算子焊在一起，往往意味着前一个算子的结果要**多活一段时间**（live range 变长），这段更长的时间里它得占着显存；把异步的集合通信（all-reduce / all-gather）提前发起再延后收尾，省下的是等待时间，付出的是显存压力。更麻烦的是，融合还会改变编译器给每个融合块挑的 **tile 大小**——一个本来能跑满矩阵单元的卷积，可能因为旁边塞进来的向量运算抢了片上内存（VMEM）而被迫缩小 tile，反而变慢。

**疑问**：那么编译器到底凭什么判断「这两个算子该不该焊在一起」？它怎么知道自己猜对了？

**回答（中心思想）**：XLA 的融合是一套**三层结构**——**表示**（用 `kOutput` / `kLoop` / `kCustom` 三种 kind 描述「这个融合块由谁主导迭代空间」）、**策略**（优先队列 + 周期级代价模型 + 少量硬启发式，在 NP-hard 的搜索空间里做近似）、**机制**（compute-with-compute、compute-with-collectives、continuation 等具体融合手法）。判据的核心不是「能融就融」，而是**算总账**：省下的 HBM 往返与暴露的延迟，是否大于增加的显存压力与被拖累的 tile 选择。当显存成为瓶颈时，连「广播必融」这种硬规则都要让路。

## 一、先把账算清楚：融合省的是 HBM 往返，赚的是关键路径

讲者用一张 TPU 结构图开场，把「为什么要融合」讲得很直白。

![TPU TensorCore 结构：HBM 在最下面，向量内存（VMEM）在中间，矩阵乘法单元（MXU）与向量单元（VPU）在上层](assets/算子融合的判据：XLA%20用代价模型和%20HBM%20压力决定谁和谁焊在一起/00705.webp)

图里几个部件的关系值得记住：

- **HBM**（慢速大容量）对应 GPU 的 global memory；
- **Vector Memory / VMEM**（快速小容量）大致对应 GPU 上跨 SM 共享的 L2；
- **MXU**（Matrix Multiply Unit，矩阵乘法单元）一次处理 128×128 的块，是 TPU 的性能主力；
- **VPU**（Vector Processing Unit）做逐元素、转置、置换这类向量活。

讲者给的目标只有一句话：**让关键路径上塞满 MXU 操作**。因为一旦关键路径上出现「等 HBM 数据」或者「等 VPU 算完」，MXU 就饿着了。幻灯片上那句 "Do not allow MXUs to go hungry!"（别让 MXU 饿着）就是整个融合策略的出发点。

融合能带来三种收益，后面所有判据都围绕它们展开：

1. **减少 HBM 往返与总线占用**——中间结果不落显存；
2. **让不同协处理器并行**——VPU 的活藏到 MXU 的活后面；
3. **缩小 HBM 占用（footprint）**——这一点常被忽略 [【跳转到 12:59】](https://www.youtube.com/watch?v=yydJ6ZGCiVQ&t=779)，但对 Transformer 是刚需：softmax 的输出是 $N\times N$（$N$ 是序列长度），显存只有 6GB / 8GB / 32GB，序列一长根本放不下，所以必须把 softmax 融进后面「乘 $V$」的那一步。另一条路是把张量切到多张卡上，但「下片永远比留在片上差」，所以融合才是首选。

## 二、融合是什么：合并迭代空间，且不许反转依赖方向

讲者给了一个形式化但好懂的定义：融合是把两个算子各自的**迭代空间** $I_1$、$I_2$ 合成一个联合迭代空间 $I$，在 $I$ 上同时完成两个算子的工作；如果两者是生产者—消费者关系，还要保证**前一个算子产出的值立刻被后一个算子消费**。约束是：**不能反转依赖方向向量**（don't invert the dependence direction vectors）——换句话说，融合后的执行顺序不能要求「先用后算」。

![Compiler 101：add → conv → add 的链条，若不融合，conv 的输出要写回内存再被读出来](assets/算子融合的判据：XLA%20用代价模型和%20HBM%20压力决定谁和谁焊在一起/00844.webp)

幻灯片上的例子是 `add → conv → add`：

- 两个 `add` 都是 $O(n)$ 的逐元素操作，用 VPU；
- 中间的 `conv`（讲者简化成 dot）是 $O(n^3)$，用 MXU。

不融合的调度是：算完第一个 `add` → 写 HBM → 读回来给 `conv` → 在 MXU 上算 → 写出去 → 再读回来给第二个 `add`。关键路径上全是 HBM 往返。

融合后的做法是：把三个算子装进一个融合块，**让 `conv` 当 lead operation（主导算子）**——由 `conv` 的迭代空间决定整个融合块怎么循环；每一轮迭代里，`conv` 决定「该让第一个 `add` 产出哪一块、第二个 `add` 消费哪一块」。再配合软件流水（software pipelining），`add` 的工作就被藏到 `conv` 的 MXU 工作背后，关键路径上只剩 MXU。

在 HLO（XLA 的高层 IR）里，这个融合块写成一个 `fusion` 原语 [【跳转到 14:29】](https://www.youtube.com/watch?v=yydJ6ZGCiVQ&t=869)：它带输入、带一个 `kind` 字段、内部是一个 `called computation`（被调用的计算）来描述融合了哪些算子。

## 三、表示层：三种 kind 决定「谁主导迭代空间」

![Fusion in XLA-TPU：Representation / Policy / Mechanism 三栏，以及周期级代价模型的四个计数](assets/算子融合的判据：XLA%20用代价模型和%20HBM%20压力决定谁和谁焊在一起/01115.webp)

讲者把融合基础设施拆成三件套：**表示（Representation）、策略（Policy）、机制（Mechanism）**。 [【跳转到 18:35】](https://www.youtube.com/watch?v=yydJ6ZGCiVQ&t=1115)表示层的关键就是 `kind` 字段，只有三种：

| kind | 含义 | 谁主导迭代空间 |
| --- | --- | --- |
| `kLoop` | 只由向量算子组成的融合（"a single loop harness can be used to lower all the operations"） | 一个统一的循环骨架 |
| `kOutput` | 组合里含卷积/矩阵乘的融合 | 卷积（或 dot）当 lead op，决定整个融合块的迭代域 |
| `kCustom` | 手工内核（Pallas kernel）与 loop/output 融合混在一起 | 由 lowering 阶段在 `kOutput` 与 Pallas kernel 之间选一个当 lead |

讲者自嘲「编译器工程师起名很糟」，`kOutput` 这个名字其实是在说「一看到这个 kind，你就知道里面有卷积，卷积是 lead」。而 `kCustom` 里谁是 lead 就不那么一目了然了，得等 lowering 去挑。

为什么 lead op 这么重要？因为**lead op 决定 tile/window 的规格**，而 tile 规格又决定这个融合块能不能塞进 VMEM、能不能把 MXU 喂满。

## 四、策略层：优先队列 + 周期级代价模型 + 三条硬启发式

策略层的做法是：把「候选的融合决定」放进一个**优先队列** [【跳转到 20:23】](https://www.youtube.com/watch?v=yydJ6ZGCiVQ&t=1223)，编译器一个个取出来执行，直到再融下去不划算为止。每个决定值不值得做，交给**代价模型**打分。

### 4.1 代价模型长什么样

TPU 侧用的是**周期级（cycle-aware）代价模型**：给定一个算子，估它需要多少 MXU 周期、多少 VPU 周期、多少 permute 周期、多少 load/store 周期；然后**构造一个伪融合节点**，再问一遍「这个融合节点要多少周期」，两相比较，判断这次融合是好是坏。

幻灯片上给了一个真实的计数例子：MXU 16384 周期、Permute 0、VPU 0、LD/ST 18432 周期。可以看到这个算子里 load/store 的周期数和矩阵乘是一个量级的——这正是「访存受限」在代价模型里的样子。

因为编译器知道 tile 大小（tile 由它自己定），它就能**预估这次融合带来的片上内存开销**；但它对「每个算子映射到哪个单元」只能做粗略近似。讲者反复强调：这是个 **NP-complete** 问题，不可能穷举所有融合决定再挑最优，所以代价模型只是「够用的启发式」。

### 4.2 GPU 侧：代价模型之外还要自动调优

![GPU: HLO Fusion Algorithm —— 优先融合 + 多个（不精确的）代价模型 + 自动调优挑候选](assets/算子融合的判据：XLA%20用代价模型和%20HBM%20压力决定谁和谁焊在一起/00304.webp)

GPU 侧的策略在 2024 年改成「从 hero ops（主角算子）出发，一直往上融到不划算为止」，同样靠多个代价模型。但 GPU 有个额外麻烦：**性能不确定、不完全可预测**。所以 XLA 在 GPU 上会**在编译期真的测**——把候选融合、tile 参数、split-k 等组合拿去跑，挑最快的那个。自动调优很贵，所以先用各种手段把搜索空间收窄。

这也带来一个工程后果：**GPU 上的编译结果是不确定的**（受温度、功耗影响）。讲者在问答里说，如果客户需要可复现，可以关掉自动调优、强制使用调优缓存里的结果。

### 4.3 三条硬启发式（以及它们的例外）

代价模型之外，策略里还有几条「一眼就能判断」的规则：

**规则一：广播（broadcast）永远该融。** [【跳转到 21:43】](https://www.youtube.com/watch?v=yydJ6ZGCiVQ&t=1303) 原因是账太好算——广播不物化任何新东西，只是把数据复制出去，而且**广播的输出严格大于输入**。如果不融，这份更大的输出必然被搬到 HBM，还落在关键路径上。所以广播作为生产者，必须融进它的消费者。

**规则二：被多个消费者使用的生产者 [【跳转到 22:28】](https://www.youtube.com/watch?v=yydJ6ZGCiVQ&t=1348)（比如一个 dot 被好几个算子消费），不要融进每一个消费者。** 因为那等于把同一份计算重复做多遍，白白抬高计算量。

**规则三（例外条款）：当省显存比省计算更重要时，可以违反上面两条。** 讲者举的例子正是注意力：`QK` 融进 softmax 之后，要不要再把它融进后面的输出投影？按规则二不该融，但如果显存吃紧，就该融——因为这样能省下一份要落 HBM 的中间结果。

这条例外条款其实是整场演讲的题眼：**融合的判据不是局部的算术，而是全局的瓶颈在哪**。

## 五、怎么验证一次融合到底好不好：bundle 分析

代价模型只是预测，真要判断得看生成的代码。 [【跳转到 23:40】](https://www.youtube.com/watch?v=yydJ6ZGCiVQ&t=1420)TPU 编译器会把生成的指令打成 **VLIW bundle**，然后画一张「bundle × 各协处理器占用率」的图。

![Analysis of the Generated VLIW Bundles：红线是 MXU 占用，蓝线是 ALU/VPU 占用，理想状态是红线全程顶格](assets/算子融合的判据：XLA%20用代价模型和%20HBM%20压力决定谁和谁焊在一起/01420.webp)

读图方法：

- 横轴是**指令 bundle 序列**（可以理解成时间）；
- 纵轴是**各协处理器的占用率**；
- **红线 = MXU 占用**，**蓝线 = ALU/VPU 占用**。

「好」的形态是：红线**从头到尾顶格**（MXU 一刻不停），同时蓝线在红线下方并行起伏（VPU 的活被藏进去了），没有「只有 MXU 在跑」或「只有 VPU 在跑」的整段空窗。

幻灯片右下角把好利用率的条件列成了五条，值得抄下来当检查表：

1. MXU 与 ALU 并行；
2. lead operation（这里是卷积）决定 window/tile 规格；
3. loop 融合把输出写进一个 buffer，随后被卷积消费；
4. **融合块必须塞得进 VMEM**；
5. 遍历多个 window 大小去挑最好的（穷举但有效）。

第 4 条是很多「融了反而慢」的根源：塞不进 VMEM，就得反复溢出。

## 六、机制层：五种把算子焊在一起的手法

![Fusion Mechanisms：从「重叠 HBM-VMEM 传输与计算」到「把与数据无关的 HLO 算子融进 lead op」](assets/算子融合的判据：XLA%20用代价模型和%20HBM%20压力决定谁和谁焊在一起/01601.webp)

机制层是 TPU 相对 GPU 走得更远的地方——因为 TPU 编译器对**调度和内存放置**有完全显式的控制权（GPU 上这些交给 CUDA runtime 和硬件，编译器只能猜）。讲者把机制按「浅融合 → 深融合」排成一个谱：

- **浅融合（shallow fusion）**：融的是**互相独立**的算子； [【跳转到 27:31】](https://www.youtube.com/watch?v=yydJ6ZGCiVQ&t=1651)
- **深融合（deep fusion）**：融的是**生产者—消费者**这种有依赖的算子。

具体到手法：

### 6.1 compute-with-compute：把并行的向量活挪到另一个卷积旁边

![Parallel Fusion 的 HLO 全图：把原本挂在卷积后面的 VPU 算子，挪到另一个与之无数据依赖的卷积旁边](assets/算子融合的判据：XLA%20用代价模型和%20HBM%20压力决定谁和谁焊在一起/02183.webp)

这是讲者说自己「最喜欢」的一个技巧。场景是：图里有两个互相独立的卷积融合块 [【跳转到 35:26】](https://www.youtube.com/watch?v=yydJ6ZGCiVQ&t=2126)（白框和粉框），各自后面挂着一串 VPU 算子。单独看每个融合块都「挺好」，还能更好吗？

做法是：**把卡在卷积 A 后面的那串 VPU 算子，挪到与之无数据依赖的卷积 B 旁边**。

![Analysis Step 1：卷积融合（红线 MXU 顶格）、纯 loop 融合（只有蓝线）、以及并行融合后的形态](assets/算子融合的判据：XLA%20用代价模型和%20HBM%20压力决定谁和谁焊在一起/02238.webp)

效果用 bundle 分析一读就明白：

- 左边（卷积 A）红线不变，蓝线略微抬高——因为那串 VPU 算子本来就没把 VPU 打满，也不是访存受限，它需要的 HBM 传输和 VPU 周期**完全被卷积的 MXU 工作遮住了**，执行时间不变；
- 右边（卷积 B）**甩掉了这串 VPU 算子**，于是不再有 VMEM 竞争，可以挑一个**更好的 tile 大小**，MXU 占用变成全程顶格（图里的黄线）。

最终在某个 TPU 平台上拿到 **4.4% 的端到端提升**。 [【跳转到 37:43】](https://www.youtube.com/watch?v=yydJ6ZGCiVQ&t=2263)这个例子很能说明「融合的收益不总是来自少搬几次数据」——这里的收益来自**释放了另一个融合块的 tile 选择自由度**。

### 6.2 compute-with-collectives：把集合通信做成 continuation

![Example Fusion and Controlling Flags：卷积与 all-reduce 交错执行，右侧是 collective 子计算](assets/算子融合的判据：XLA%20用代价模型和%20HBM%20压力决定谁和谁焊在一起/01814.webp)

集合通信（all-reduce / all-gather）在多卡上很常见，它的大部分时间在等网络。**浅融合**的做法是：主计算照常跑，每隔一段时间去「看一眼」通信进行到哪了——数据到了就推进一步，没到就继续算主计算。

这就引出 **continuation（续延）** 的概念：融合进来的算子**不保证在这个融合块里执行完**，它维护一份 continuation 状态（几个标量），被「接」到后续的融合块里继续，直到完成。在 HLO 里看，这个 all-reduce 长得还是 all-reduce，只是多出几个标量变量从输入直接穿到输出，后端配置里指明去哪查这份状态。

控制它的开关是这几个 flag：

```
--xla_tpu_enable_async_collective_fusion_fuse_all_gather
--xla_tpu_enable_async_collective_fusion_fuse_all_reduce
--xla_tpu_enable_async_collective_fusion_with_mosaic_custom_call
```

**为什么需要开关？** 讲者的解释是全场最实用的一段 [【跳转到 31:29】](https://www.youtube.com/watch?v=yydJ6ZGCiVQ&t=1889)：异步集合通信意味着这个操作**被提前很远发起、又被推后完成**，于是它消费和产出的那些张量的 **live range 被拉长**，显存压力陡增。所以有时候你得去「推编译器一把」，告诉它：**别只想着性能，我现在要的是模型塞得下**。默认值是 **all-gather 开、all-reduce 关**——因为 all-reduce 的 live range 代价更大。

还有一个更细的副作用：融进来的 VPU 活要占片上内存（VMEM），于是**主计算的 tile 和它抢同一块 VMEM**，主计算可能被迫用更差的 tile。

### 6.3 dot-dot 融合：用生产者的矩阵乘去填消费者的空洞

即使 MXU 已经满负荷，仍然会有**缝隙** [【跳转到 39:51】](https://www.youtube.com/watch?v=yydJ6ZGCiVQ&t=2391)——等 VPU 算完、等通信完成、序列长度不合适等等。dot-dot 融合的思路是：把**生产者的 dot** 提前塞进消费者 dot 的这些缝隙里。相关 flag 是 `dot_dot_fusion` 和多层版本，可以叠不止两层。

代价同样是 live range 与显存压力。讲者还坦白了一个模型上的裂缝：**融合时的代价模型和真正生成底层代码时的 tile 模型不是同一个**，所以融合决定会「受制于」tile 方案——如果缝隙没算准，可能反而更慢。

### 6.4 softmax 融合就是 FlashAttention

![Technique 5: Softmax Fusion (Deep Fusion)：左边是朴素实现，右边是把 softmax 融进乘 V 的深融合](assets/算子融合的判据：XLA%20用代价模型和%20HBM%20压力决定谁和谁焊在一起/02609.webp)

讲者直接点名：文献里说的 **FlashAttention** [【跳转到 43:29】](https://www.youtube.com/watch?v=yydJ6ZGCiVQ&t=2609)，在 XLA 里就是默认开启的 softmax 深融合。幻灯片上还引了两篇工作：Rabe & Staats 的 "Self-attention does not need O(n²) memory" 和 Dao 等人的 "FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness"。

控制开关是 `xla_tpu_prefuse_self_attention` 和 `xla_tpu_rwb_fusion`。

## 七、把控制权还给用户：`must_fuse`

![MUST_FUSE JAX API：给一段算子打上同一个 fusion_region_id，编译器必须把它们融在一起](assets/算子融合的判据：XLA%20用代价模型和%20HBM%20压力决定谁和谁焊在一起/02639.webp)

前面所有判据都是编译器自己拿主意。 [【跳转到 43:54】](https://www.youtube.com/watch?v=yydJ6ZGCiVQ&t=2634)但用户有时比编译器更清楚某几个算子必须在一起。JAX 层面提供的接口是 `must_fuse`：

```python
with must_fuse(fusion_region_id):
    # 这里的算子
```

语义很硬：**同一 region id 的算子必须融进同一个融合块，编译器不考虑性能**；如果它无法安全地做到，就**报错**而不是悄悄放弃。讲者提醒这个特性当时还没进公开版本的 JAX。

另一条路是 `jax.custom_call`：编译器可以内联自定义调用，把它当成若干个普通算子，再按自己的代价模型决定融不融——但如果你想「必须融成一个」，还是得用 `must_fuse`。

## 八、布局、内存与融合是同一本账

问答环节有人问布局（layout）优化。讲者的回答很适合作为本文的收尾： [【跳转到 50:36】](https://www.youtube.com/watch?v=yydJ6ZGCiVQ&t=3036)

> 做最后 10% 性能的人，都是把**布局、融合、调度**放在一个大池子里一起调的。

他举了权重布局的例子：给权重挑一个**最优布局**，能让你从稠密矩阵乘里拿到**最好的 tile 大小**；但布局不只在单卡上算账——你还要考虑这份布局**怎么切分（sharding）到多张卡**上，因为推理负载也不是一张卡跑完的；再往下还有**能不能预取（prefetch）**：如果 VMEM 够大，下一层的权重可以在上一层还在算的时候就预取进来，省掉取第一块数据的开场开销。最后，一旦上了量化，很多问题会变小：footprint 缩小，tile 与布局的自由度都变大。

把这一节和前面的判据合起来看，XLA 的融合决策其实一直在回答同一个问题：**这次融合之后，HBM 上少搬了多少、VMEM 里多占了多少、tile 还能不能挑到最好的那个？** 三个数一起算，才是端到端性能。

## 小结

- 融合的目标是让**关键路径上只剩矩阵乘**：省 HBM 往返、让 VPU 与 MXU 并行、压低 HBM footprint。
- 融合的形式化定义是**合并迭代空间且不反转依赖方向**；融合块由 **lead operation** 决定 tile 规格。
- 表示层只有三种 kind：`kLoop`（纯向量）、`kOutput`（含卷积/矩阵乘）、`kCustom`（Pallas 内核混合）。
- 策略层 = **优先队列 + 周期级代价模型 + 硬启发式**；这是 NP-complete 问题，只能近似。GPU 侧还会**在编译期实测**候选融合，因此结果不确定，可用调优缓存固定。
- 硬启发式：**广播必融**（输出更大，不融就得落 HBM）；**多消费者生产者慎融**（会重复计算）；**但显存吃紧时可以违反**。
- 验证手段是 **bundle 分析**：看 MXU（红线）是否全程顶格、VPU（蓝线）是否被藏进去、融合块是否塞得进 VMEM。
- 机制上分浅融合（独立算子）与深融合（生产者—消费者）：compute-with-compute（并行融合，实测 4.4%）、compute-with-collectives（continuation 式异步通信）、dot-dot 融合（填 MXU 空洞）、softmax 深融合（即 FlashAttention）。
- **显存是融合的硬约束**：continuation 拉长 live range、VPU 活抢 VMEM 都会反噬；所以有 `fuse_all_reduce` 这类「别想性能，先想内存」的开关。
- 用户侧可用 `must_fuse` + `fusion_region_id` 强制融合；布局、融合、调度要一起调。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| HBM | 加速器上的大容量高带宽显存，对应 GPU 的 global memory；融合主要就是在省它的往返 |
| VMEM | TPU 的片上向量内存，容量小、带宽高，大致相当于 GPU 的 L2；融合块必须塞得进去 |
| MXU | 矩阵乘法单元，一次算 128×128 的块，是 TPU 的性能主力 |
| VPU / ALU | 向量/算术单元，负责逐元素、转置、置换等操作 |
| lead operation | 融合块里主导迭代空间与 tile 规格的那个算子（通常是卷积或 dot） |
| `kOutput` / `kLoop` / `kCustom` | XLA 融合块的三种 kind，分别表示「含卷积」「纯向量」「含手工内核」 |
| continuation | 融合进来的算子不保证在本块内完成，用状态量接到后续融合块继续执行 |
| bundle 分析 | 把生成的 VLIW 指令按 bundle 画占用率曲线，用来看 MXU 是否被喂满 |
| hero op | GPU 融合的起点算子，通常是最值得优化的矩阵乘或卷积 |
| live range | 一个张量从产生到最后一次被使用的时间跨度；跨度越长，占显存越久 |