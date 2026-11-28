# 参数化 CUDA Graph：不重录图也能换输入指针

> 视频来源：[Parameterized CUDA Graph Launch in PyTorch: CUDA Graphs Without the Pain - Daniel Galvez, NVIDIA](https://www.youtube.com/watch?v=37w9hQb5gME)（YouTube · PyTorch Foundation，PyTorch Conference Europe 2026）｜时长约 26 分钟
> 导读：这是一场「讲坑」的演讲。作者是 PyTorch 里改 CUDA API 的工程师，他把 CUDA Graph 难用的四个问题摊开，再讲参数化图启动怎么用「每次启动前重写指针参数」把它们缓解掉。本文覆盖原片的全部技术主线，包括他没能合入代码的两个真实障碍。

## 本讲要解决的核心问题（SCQA）

**背景**：CUDA Graph 能消掉全部 CPU 启动开销，MLPerf 上有些负载快 3 倍，512 卡的训练不开图会被老板骂。

**冲突**：但一个完全合法的 PyTorch 程序，用上图之后可能就跑不对了。输入必须拷进静态缓冲区、输出地址永远被覆盖、显存被放大、图的输入输出根本没法内省——这四条几乎把「好用」这件事堵死。

**疑问**：既然内核参数在捕获时就被冻结，能不能在每次重放之前，**把指针参数改掉**，从而不必再拷贝输入、也不必独占一块私有显存池？

**回答（中心思想）**：能。参数化图启动（parameterized CUDA Graph launch）的思路是「每次启动前把每个内核节点的指针参数重写一遍」，于是图可以直接借用默认内存池的内存，显存占用大幅下降，静态输入拷贝也可以省掉。但它在实现上有两个硬骨头：CUDA 只给内核节点一个不透明的参数缓冲区（不知道哪个 8 字节是指针），以及重放时的内存对齐必须与捕获时一致。作者用「捕获两张图做交叉验证」解决了前者，后者至今没有干净解法。

## 一、先算清楚：图买到的是什么

### 1.1 收益只有一条——性能

CUDA Graph 本质上是一张 DAG：节点是内核、内存拷贝、memset（九成情况下是内核），边声明先后依赖。

![传统执行与图执行的对比：上图 CPU 逐内核 Launch 造成 GPU 气泡，下图一次 Graph Launch 让内核背靠背执行](assets/参数化%20CUDA%20Graph：不重录图也能换输入指针/00191.webp)

作者把收益讲得很直白：**好处就是性能，仅此而已**。在 Blackwell、Hopper 这一代，一个 CUDA 内核跑 5 微秒并不罕见，而 CPU 发下一个内核可能要花超过 5 微秒。于是出现 GPU 气泡；更糟的是，**你越优化 GPU 代码，气泡越大**——因为缝是 CPU 填的。

他也顺手拆了「CPU 为什么慢」：CUDA 驱动、Python、PyTorch 的 dispatcher，粗略地说各占三分之一。想加速 CPU 侧，三条腿得一起动；而图的做法是「把这些统统干掉」。

[【跳转到 03:11】](https://www.youtube.com/watch?v=37w9hQb5gME&t=191)

### 1.2 什么负载需要图

- **高度分布式负载**：不希望被尾部效应打中（某个 CPU 核慢、GC、调度器抽风）。
- **工作量很小的负载**：模型越小，越容易被 CPU 开销支配，也就越适合图。

[【跳转到 06:06】](https://www.youtube.com/watch?v=37w9hQb5gME&t=366)

## 二、今天大家怎么用图：预热、捕获、静态缓冲区

### 2.1 PyTorch 的标准写法

原片给了一段完整可读的代码，这是理解后面所有问题的基准：

![PyTorch 里传统的 CUDA Graph 用法：先 eager 预热，再 with torch.cuda.graph(g) 捕获，之后每次先 copy_ 到静态缓冲区再 g.replay()](assets/参数化%20CUDA%20Graph：不重录图也能换输入指针/00391.webp)

```python
model = torch.nn.Linear(16, 4).cuda()
criterion = torch.nn.MSELoss()
data_loader = DataLoader(RandomDataset(32, 64), batch_size=32,
                         shuffle=False, pin_memory=True, num_workers=1)

def train(X, y):
    model.zero_grad(set_to_none=True)
    y_pred = model(X)
    loss = criterion(y_pred, y)
    loss.backward()
    with torch.no_grad():
        for param in model.parameters():
            param.sub_(lr * param.grad)
    lr.mul_(0.9)
    return loss

for i, (X, y) in enumerate(data_loader):
    if i == 0:
        loss = train(X.cuda(), y.cuda())     # 预热：先按 eager 跑一次
        print(loss.item())
        continue
    if i == 1:
        X_static = torch.empty_like(X, device="cuda")
        y_static = torch.empty_like(y, device="cuda")
        g = torch.cuda.CUDAGraph()
        with torch.cuda.graph(g):            # 捕获
            loss_static = train(X_static, y_static)
        continue
    X_static.copy_(X, non_blocking=True)     # 每次重放前的手工拷贝
    y_static.copy_(y, non_blocking=True)
    g.replay()                               # 重放
    print(loss_static.item())
```

三个要点：

1. **预热**：第一次迭代必须按 eager 方式跑一遍（原因演讲者没时间展开，但对分配器与 lazy 初始化都必要）。
2. **捕获**：`with torch.cuda.graph(g)` 会新建一条流、把它设为捕获模式，你在里面提交的工作被录进图 `g`。
3. **静态缓冲区**：捕获时用的张量（`X_static`、`y_static`）是固定的；输出也是固定的——所以叫 `loss_static`。每次重放前，你必须自己把新数据 `copy_` 进去。

[【跳转到 07:21】](https://www.youtube.com/watch?v=37w9hQb5gME&t=441)

### 2.2 参数化写法长什么样

注释掉的那段就是参数化版本：指定动态输入 `X`、`y` 的新值，直接拿到一个「动态的 loss」。

```python
# 参数化图启动（示意）
dynamic_loss = g.replay_dynamic(dynamic_inputs={"X": X, "y": y})
```

区别在于 `loss_static` 每次重放都是同一个张量、同一个底层地址；而「动态 loss」**每次重放都在不同地址上**（除非缓存分配器碰巧又分到同一个地址）。这个差别正是后面所有讨论的源头。

[【跳转到 09:01】](https://www.youtube.com/watch?v=37w9hQb5gME&t=541)

## 三、四个问题：为什么「合法程序」会跑不对

原片用一张冰山图概括了「图能拒绝你的方式」，水面之上只有四条：

![为什么 CUDA Graph 难用：四个主要问题（静态输入拷贝、输出地址复用、显存放大、无法内省）与水面下的冰山](assets/参数化%20CUDA%20Graph：不重录图也能换输入指针/00601.webp)

| # | 问题 | 具体表现 |
| --- | --- | --- |
| 1 | 必须把输入拷进「静态输入地址」 | 分段式图（图与非图混用）时极难保证不漏拷 |
| 2 | 重放的图总是写到同一地址 | 两次重放的输出其实是同一块内存，前一个被静默覆盖 |
| 3 | 图会放大显存占用 | 每张图独占私有池，作者认为这才是最严重的一条 |
| 4 | 无法内省图的输入输出 | 只能靠用户自己记账 |

第 2 条值得多说一句：假设同一张图重放两次得到 `out1` 和 `out2`，第二次重放结束后 `out1` 的值会和 `out2` 一样——因为它们其实是同一块内存。在大规模代码库里，这会是**静默错误**：你用了某张图的输出地址，但后面又重放了一次，那个值就被覆盖了。作者的原话是「这种 bug 你绝对不想碰，那是高级忍者领域」。

[【跳转到 10:01】](https://www.youtube.com/watch?v=37w9hQb5gME&t=601)

## 四、参数化图启动：机制其实很朴素

### 4.1 概念：把「张量 → 缓冲区」的关联重写一遍

看 `torch.add`：内部算子最终会跑一个 CUDA 内核，形如 `add_arrays(const float* a, const float* b, float* out, int n)`。

![参数化图启动的原理：torch.add 的输入输出分别对应内核的 float* a、float* b、float* out，重放前把这些指针参数换掉即可](assets/参数化%20CUDA%20Graph：不重录图也能换输入指针/00796.webp)

要更新一张图的参数，机制上就是更新图里**每一个内核**的参数。假设我们有一张只含 `add_arrays` 的图：输入对应 `float* a`，另一个输入对应 `float* b`，输出落在 `float* out` 里。于是所谓参数化，就是每次启动前重新建立「张量 ↔ 显存缓冲区」的关联。

实现上最好用的 API 是 `cudaGraphKernelNodeSetParams`（PyTorch 侧对应 `cudaGraphKernelNodeUpdatesApply`）。**注意：非指针参数改不了**——原因没时间细说，但总之只关心更新指针参数。如果你真想改非指针参数，那基本没戏。

[【跳转到 14:06】](https://www.youtube.com/watch?v=37w9hQb5gME&t=846)

### 4.2 收益：从默认池「借」内存

![参数化图启动带来的好处：图不再需要私有内存池，显存占用大幅下降；不必拷贝输入；不会覆盖上次输出；还能做图快速重启](assets/参数化%20CUDA%20Graph：不重录图也能换输入指针/00896.webp)

- **不再需要私有内存池**：内存从 PyTorch 的默认内存池分配，然后替换进图里——相当于「借」内存，从而减少私有池带来的外部碎片。作者说这是**最重要的一条**。
- **不必拷贝输入**：省掉设备端拷贝，也允许输入被原地修改。
- **不会覆盖上次重放的输出**：每次输出地址不同。
- **理论上可以做图快速重启**：重启整个训练进程很慢，这对 VLM 之类很吸引人。

为什么第一条最重要？因为今天 VLM、SGLang、很多 Megatron 相关工作都不得不做「部分 CUDA Graph」：一部分负载能用图，一部分用不了。而采用图时你可能会发现**显存不够了**——这直接让你根本没法上图，如果上图本来能带来 3 倍性能提升，那就很要命。

[【跳转到 15:21】](https://www.youtube.com/watch?v=37w9hQb5gME&t=921)

## 五、实现难点一：参数缓冲区是不透明的

### 5.1 图根本不知道自己在跑什么代码

概念上说「输入张量变成 `float* a`」很简单，麻烦在于 CUDA 看到的东西非常「笨」：

![为什么打补丁很难：CUDA 只给内核节点一个 void** kernelParams 的不透明缓冲区，节点并不知道自己跑的是什么代码](assets/参数化%20CUDA%20Graph：不重录图也能换输入指针/01096.webp)

```c
struct __device_builtin__ cudaKernelNodeParams {
    void* func;                  // 内核函数指针
    dim3 gridDim;                // grid 维度
    dim3 blockDim;               // block 维度
    unsigned int sharedMemBytes; // 动态共享内存
    void** kernelParams;         // 参数数组（不透明！）
    void** extra;
};
```

每个内核节点拿到的就是一堆 `void*`。所以「我只要找到输入输出的地址，然后在参数缓冲区的那些偏移上替换掉」这个想法并不成立——至少不是开箱即用。

[【跳转到 18:16】](https://www.youtube.com/watch?v=37w9hQb5gME&t=1096)

### 5.2 检测算法：捕获两张图，做交叉验证

原片给了一个很巧的算法（作者把功劳给了 Zach DeVito）：

![检测参数缓冲区里指针偏移的算法：在两张私有池不同的图上同时命中，才判定为需要更新的动态指针](assets/参数化%20CUDA%20Graph：不重录图也能换输入指针/01196.webp)

1. **朴素做法**：检查参数缓冲区里每一个 8 字节值，看它是否落在该图私有内存池的范围内；是的话，就认为它是指针。这是 Medusa 那篇 VLM 论文里描述的做法。
2. **问题**：会误报。一旦你把某个「假指针」覆盖成别的指针值，就会得到完全错误的结果。
3. **解法**：**捕获两张图**，两张图的私有内存池不同（只分配虚拟显存、不落物理页），同样的检查做两遍；只有两张图里都命中的 8 字节值，才判定为需要更新的动态指针。用反证法可以证明这样永远不会误报。

算法还要求两张图的拓扑完全一致，然后对每一对内核节点，遍历参数缓冲区里每个 8 字节对齐的值，判断它是否落在对应图私有池的地址区间内（从 `buffer_data_ptr` 到 `buffer_data_ptr + buffer_nbytes`）。

[【跳转到 19:56】](https://www.youtube.com/watch?v=37w9hQb5gME&t=1196)

## 六、实现难点二：两个至今没有干净解法的障碍

### 6.1 分布式通信要求地址固定

算法里有一个隐含假设：**指针的值本身不变**。但对分布式计算它确实会变——NCCL、NVSHMEM、PyTorch symmetric memory 都受影响。

对称内存与注册内存假定自己待在固定地址上，这样能拿到延迟上的好处；但这恰好和参数化图启动要做的事相反（我们想改地址，它只在地址固定时才成立）。问题在于，今天 NCCL 或 PyTorch symmetric memory **没有办法告诉参数化图启动这套基础设施**：「这是静态地址，你不能改。」

[【跳转到 20:21】](https://www.youtube.com/watch?v=37w9hQb5gME&t=1221)

### 6.2 对齐：捕获时选的内核，重放时可能不合法

第二个问题更隐蔽。`torch.compile` 有 guard，会 guard 设备、dtype 之类，但它**不 guard 输入张量的对齐（alignment）**。而 PyTorch 在捕获时会根据当时的对齐情况选择不同的 CUDA 内核：

![检测算法的失效情形之三：捕获时按对齐选到 vectorized_elementwise_kernel<8>，重放时若对齐降级，就会变成非法访存或静默错误](assets/参数化%20CUDA%20Graph：不重录图也能换输入指针/01296.webp)

```cpp
case 8:  vectorized_elementwise_kernel<8, ...><<<grid, num_threads(), 0, stream>>>(N, f, data); break;
case 4:  vectorized_elementwise_kernel<4, ...><<<grid, num_threads(), 0, stream>>>(N, f, data); break;
case 2:  vectorized_elementwise_kernel<2, ...><<<grid, num_threads(), 0, stream>>>(N, f, data); break;
```

具体说：如果我向分配器要一个 4 字节对齐的指针，它很可能给出一个 8 字节对齐的指针；于是我知道它至少 4 字节对齐，但 PyTorch 可能很乐观地在捕获时选了只支持 8 字节对齐的版本。到了重放时如果对齐降级，就会变成非法访存或静默错误。

作者的回应是「重放时要求对齐与捕获时一致」——这是对的，但**没有任何 API 能表达这个约束**，所以他也不知道怎么处理。这也是这个特性卡在「单卡 TorchBench 全通、通用化受阻」的原因。

[【跳转到 21:36】](https://www.youtube.com/watch?v=37w9hQb5gME&t=1296)

### 6.3 另一条路：虚拟内存别名

演讲最后给了一个完全不同的思路：**你并不一定需要更新指针参数**。

![虚拟内存别名方案：让 CUDA Graph 拥有虚拟页，应用拥有虚拟页与物理页，重放前把图的虚拟页映射到应用的物理页上](assets/参数化%20CUDA%20Graph：不重录图也能换输入指针/01371.webp)

- 每张图用一块私有的虚拟地址范围捕获；
- 重放之前，把图的私有虚拟页**映射到应用提供的、有物理页支撑的虚拟内存**上；
- 于是不必定位并更新每个内核的参数，地址天然就对得上。

它的代价也很清楚：应用张量与图张量必须按 2 MiB 对齐；**只有 CPU 能做内存映射**，而这是特权 OS 操作、很慢，会造出一个 GPU 气泡。作者提到 OpenXLA 正在做原型（jax/XLA 的 PR），并且这也许能顺带解决 NCCL 注册内存的问题，但他问过做 NCCL 的同事，对方说「有点悬」。

[【跳转到 22:51】](https://www.youtube.com/watch?v=37w9hQb5gME&t=1371)

## 七、结论与路线

![结论：单卡 TorchBench 上已经全部跑通，但注册/对称内存与输入对齐两个边界情况挡住了通用化；预计先落地「只改输出参数」的弱化版](assets/参数化%20CUDA%20Graph：不重录图也能换输入指针/01471.webp)

- 参数化图启动**今天在每个单卡 TorchBench 负载上都工作**，但边界情况让它还不能通用。
- 两个已知问题：① NCCL、NVSHMEM、torch symmetric memory 这类注册与对称内存不配合；② 捕获与重放之间的输入对齐不一致。
- 对用户来说**最大的好处是显存在「部分 CUDA Graph」场景下大幅下降**。
- 作者预计几周到几个月后会出现一个「弱化版」：每次启动**只改输出参数、不改输入参数**，输入仍然要拷进静态缓冲区。这样依然能借到输出内存，从而省掉那部分显存增长；它大概会通过 `torch.compile` 加 CUDA Graph Trees 暴露成一个可选的布尔开关。

## 小结

- CUDA Graph 的收益只有一条：消掉 CPU 侧启动开销；而 CPU 侧开销大致由驱动、Python、dispatcher 各占三分之一。
- 传统用法是「预热 → 捕获 → 每次 `copy_` 到静态缓冲区 → 重放」，代价是静态输入拷贝、输出地址复用、显存放大、无法内省四个问题。
- 参数化图启动的机制很朴素：每次启动前用 `cudaGraphKernelNodeSetParams` 重写每个内核节点的**指针参数**（非指针参数改不了）。
- 它最大的价值是**让图借用默认内存池**，从而在「部分 CUDA Graph」场景下大幅降低显存占用；顺带省掉输入拷贝、避免输出覆盖。
- 实现难点一是参数缓冲区不透明：用「捕获两张图、交叉验证」的算法检测指针偏移，可避免误报。
- 实现难点二是分布式注册内存要求地址固定、以及捕获/重放的对齐必须一致——后者目前没有 API 能表达。
- 另一条路是虚拟内存别名：不做参数更新，直接把图的虚拟页映射到应用的物理页，代价是 2 MiB 对齐与 CPU 侧映射的延迟。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| 参数化图启动 | 每次重放前重写图内各内核节点的指针参数，从而复用同一张可执行图 |
| 静态输入缓冲区 | 捕获时使用的固定地址张量，传统用法要求每次把新数据拷进去 |
| `cudaGraphKernelNodeSetParams` | 修改某个内核节点启动参数的 API，只能改指针类参数 |
| `cudaKernelNodeParams` | 内核节点的参数结构体，其中 `kernelParams` 是 `void**` 的不透明缓冲区 |
| 私有内存池（private pool） | 图在捕获时独占的显存池，是显存放大的主因 |
| 部分 CUDA Graph | 负载中一部分用图、一部分保持 eager 的混合模式 |
| 虚拟内存别名 | 用虚拟页到物理页的映射代替参数改写，让图的地址自动对上应用的内存 |
| CUDA Graph Trees | PyTorch 里把多张图按调用关系组织起来、避免重复捕获的机制 |