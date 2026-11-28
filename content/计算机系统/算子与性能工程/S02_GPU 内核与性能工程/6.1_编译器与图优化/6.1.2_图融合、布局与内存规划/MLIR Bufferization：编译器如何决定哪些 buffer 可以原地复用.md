# MLIR Bufferization：编译器怎么决定哪些 buffer 可以原地复用

> 视频来源：[2023 LLVM Dev Mtg - MLIR Bufferization: From Tensors to MemRefs](https://www.youtube.com/watch?v=nLydW5zQoLU)（YouTube · 2023 LLVM Developers' Meeting，讲者 Matthias Springer 与 Martin Erhart，Google Research）｜时长约 50 分钟
> 导读：这是 MLIR 缓冲化（bufferization）的官方教程，讲的是「不可变张量」如何落地成「有地址的 memref」。它正好补上了编译器内存规划最关键的一环：**哪些算子可以原地写、哪些必须复制、复制多了显存峰值就上去了**。本文按「为什么需要 → 原地还是复制 → 冲突怎么判 → 怎么消掉多余分配 → 谁负责释放 → 完整流水线」重排，代码片段只保留能说明判据的部分。

## 本讲要解决的核心问题（SCQA）

**背景**：MLIR 里的 `tensor` 是**不可变**（immutable）的 [【跳转到 03:12】](https://www.youtube.com/watch?v=nLydW5zQoLU&t=192)，它**没有内存地址**——`%t = tensor.insert %v into %t[...]` 描述的是「一个新的张量」，不是「往某块内存里写」。这种表示对做优化极友好（没有副作用、随便重排），但**没法直接执行**：要跑起来，必须先把 tensor IR 降成 memref IR，给每个值分配真正的内存位置。这个降级过程就叫 **bufferization（缓冲化）**。

**冲突**：最朴素的做法是「每个张量结果都分配一块新 buffer」。这样语义绝对正确，但显存会瞬间爆掉：一个 $L$ 层的网络，中间结果全都同时活着，峰值显存随层数线性增长。想省内存就得**原地写**（in-place，把结果写回输入那块 buffer），可原地写是有前提的——**这块 buffer 原来的值后面还有没有人要读？** 判断错了就是静默的数值错误。

**疑问**：编译器凭什么判断一次写能不能原地做？判断不出来的时候它会怎么办？这些决定又如何反映到端到端性能（显存峰值、多余的 copy 内核）上？

**回答（中心思想）**：one-shot bufferize 用一套**冲突检测（conflict detection）**来回答：它在数据流上找「**定义 → 冲突写 → 读**」这个三元组，只要出现这个顺序，就说明原地写会破坏后面还要用的值，于是插入一次 copy。**别名（aliasing）**会被一并考虑（`extract_slice` 产生的子视图算同一块内存）。此外还有两步专门用来消掉多余的内存：**empty tensor elimination**（把「先分配临时 buffer、算完再整体拷到目标」改成「直接算进目标」）和 **buffer deallocation**（用所有权分析决定什么时候能安全释放）。

## 一、起点：一个带「已分配 buffer」的函数

![Running Example：函数参数是 memref（%A、%B、%C），通过 bufferization.to_tensor 进入 tensor IR，最后用 materialize_in_destination 指定结果落在 %C](assets/MLIR%20Bufferization：编译器如何决定哪些%20buffer%20可以原地复用/00035.webp)

教程用一个批量矩阵乘（batched TOSA matmul）当贯穿全文的例子。这个例子里有几个值得注意的构件：

- **函数签名是 memref**：`%A: memref<1x17x19xf32>`、`%B: memref<1x19x29xf32>`、`%C: memref<1x17x29xf32>`。这是编译器里很常见的一种模式——**buffer 已经由运行时（或上一层编译器）预先分配好了**，函数只负责往里写。
- **`bufferization.to_tensor`**：把 memref 转成 tensor，可以理解成一种「还没落实的类型转换」（unrealized conversion cast），它会在缓冲化过程中被逐步消解。
- **`restrict` 属性**：`to_tensor` 上必须标 `restrict`（和 C/C++ 的 `restrict` 关键字同理），意思是「**这块 buffer 只有这一个入口进入 tensor IR，没有别的别名**」。如果违反（比如同一块 buffer 的一个 subview 也从另一个 `to_tensor` 进来），缓冲化会拒绝这段 IR。
- **`bufferization.materialize_in_destination`**：明确要求「算出来的这个张量必须存进 `%C` 这块 buffer」。

IREE 里有对应的自家版本 [【跳转到 02:15】](https://www.youtube.com/watch?v=nLydW5zQoLU&t=135)：`flow.dispatch.tensor.load` / `flow.dispatch.tensor.store`，语义一样，只是边界上的 buffer 类型不同。

## 二、原地还是复制：DPS 是判断的地基

![Destination Passing Style：tied operand/result 对，buffer(%r) = buffer(%t) 或新分配](assets/MLIR%20Bufferization：编译器如何决定哪些%20buffer%20可以原地复用/00367.webp)

缓冲化框架是围绕 **DPS（destination passing style，目的传递风格）** 设计的。 [【跳转到 05:42】](https://www.youtube.com/watch?v=nLydW5zQoLU&t=342)DPS 算子的共同点是：**结果和某个操作数之间有一条「绑定」关系**（tied operand/result pair）。比如 `tensor.insert %f into %t[%idx]`，它的结果 `%r` 绑定在 `%t` 上。

这条绑定关系给了缓冲化一个极强的不变量：

$$
\text{buffer}(\%r) = \text{buffer}(\%t) \quad \text{或} \quad \text{buffer}(\%r) = \text{新分配}
$$

也就是说，结果**要么就写在 `%t` 那块 buffer 里（in-place），要么写在一块全新的 buffer 里（out-of-place）**，绝不会跑到第三块 buffer 上去。这让缓冲化分析变得简单得多——它不需要考虑「哪里有块空闲 buffer 可以塞」。

于是决策就简化成一个二选一：

- **in-place**：不复制，最省内存、最省带宽；
- **out-of-place**：分配一块新 buffer 并复制，代价是**多一份内存占用 + 一次整块拷贝**。

触发 out-of-place 的典型原因有两个 [【跳转到 06:57】](https://www.youtube.com/watch?v=nLydW5zQoLU&t=417)：**原来的值后面还要用**（写进去就读不回来了），或者**这块 buffer 不允许写**（比如标了 `bufferization.writable = false` 的块参数，或者 `restrict` 约束下不确定归属的 buffer）。

教程还强调了一个容易误解的点：**框架本身不保证结果一定落在某块指定 buffer 里**。如果你有这个需求，必须显式用 `materialize_in_destination` 说出来。

顺带一提，`DestinationStyleOpInterface` 不只服务于缓冲化，**tiling（分块）** 等变换也用它——因为「结果写回目的操作数」这个性质在分块后依然成立。

## 三、冲突检测：找「定义 → 冲突写 → 读」这个三元组

真正决定 in-place 与否的，是 one-shot bufferize 的**冲突检测**。 [【跳转到 15:17】](https://www.youtube.com/watch?v=nLydW5zQoLU&t=917)它找的是三个东西，而且**必须按这个顺序出现**：

1. **Definition（定义）**：一个 tensor SSA 值，定义了一份张量的内容；
2. **Conflicting Write（冲突写）**：一个会「覆盖」这份定义某部分的算子；
3. **Read（读）**：一个期望读到这份定义某部分的算子。

![Read-after-Write Conflict Detection：%0 被 from_elements 定义，%1 覆盖写 %0，%r 又读 %0 —— 于是 insert 必须 out-of-place](assets/MLIR%20Bufferization：编译器如何决定哪些%20buffer%20可以原地复用/00967.webp)

幻灯片上的例子非常干净：

```mlir
// Definition
%0 = tensor.from_elements %f0, %f1, %f2 : tensor<3xf32>

// Conflicting Write
%1 = tensor.insert %f3 into %0[%idx] : tensor<3xf32>

// Read
%r = tensor.extract %0[%idx2] : tensor<3xf32>
```

因为 `%0` 在 `%1` 之后还要被 `extract` 读，所以 `insert` **不能**原地写进 `%0` 的 buffer——框架在这里插入一次 copy。这就是那个红色标签 **OUT-OF-PLACE BUFFERIZATION** 的含义。

反过来，**顺序不同的情况不算冲突**：定义 → 读 → 写，是安全的。还有一种常见的安全情况：**写张量的一部分、读另一部分不重叠的切片**，也不算冲突。

但教程很诚实地说明了这个优化的局限：**它只认「`extract_slice` / `insert_slice` 成对出现」这种直观形态**。如果「两块切片不重叠」这件事被**块参数（block argument）**挡住了、看不出来，那还是会保守地插入 copy。

### 3.1 别名必须一起算

冲突检测会把**别名**考虑进去。比如 `tensor.extract_slice` 会产生 `%0` 的一个别名，缓冲化后它变成 `memref.subview`——所以「你是直接用 `%0`，还是用 `%0` 的一个别名」对分析结果没有影响，框架都会正确处理。

### 3.2 循环有一条额外规则

有一条专门针对循环的规则值得记住 [【跳转到 17:22】](https://www.youtube.com/watch?v=nLydW5zQoLU&t=1042)：一般情况下「定义 → 读 → 写」不算冲突，但**如果定义在循环外、而读和写在循环内**，那**仍然算冲突**。原因是：第一次迭代写进 buffer 之后，第二次迭代想读的「原始值」已经被上一轮覆盖掉了。

这也解释了为什么分块（tiling）之后经常突然多出 copy：分块把一次矩阵乘变成循环，循环里又要读又要写同一块 buffer，缓冲化看不出「每一轮操作的是不同片段」，只能保守复制。

## 四、消掉多余分配：empty tensor elimination

很多变换（比如 `tosa-to-linalg`）会先生成一个 `tensor.empty` [【跳转到 29:57】](https://www.youtube.com/watch?v=nLydW5zQoLU&t=1797)（内容未指定的张量），再往里算。

![tensor.empty 会缓冲化成 memref.alloc —— 于是先分配一块临时 buffer](assets/MLIR%20Bufferization：编译器如何决定哪些%20buffer%20可以原地复用/01802.webp)

`tensor.empty` 缓冲化后就是一次 **`memref.alloc`**。于是典型形态变成：

```
alloc 临时 buffer → fill 0 → matmul 写进临时 buffer → 整块 copy 到 %C
```

![tosa-to-linalg 之后：matmul 写进 tensor.empty，再 materialize 到 %C，等于多了一次整块拷贝](assets/MLIR%20Bufferization：编译器如何决定哪些%20buffer%20可以原地复用/01902.webp)

看到这里自然会问：**为什么不直接算进 `%C`？** 这正是 **empty tensor elimination** 做的事：它从 `materialize_in_destination` 往回追，发现「要塞进去的东西」源头是一个 `tensor.empty`，就把这个 `tensor.empty` 替换成对应的目的地（那块 `to_tensor` 背后的 buffer）。于是矩阵乘直接写进 `%C`，剩下的那次拷贝变成 `%C → %C`，被折叠掉。

这条优化的意义在显存上非常直接：**少一次整块分配、少一次整块拷贝**。对一个大矩阵乘来说，这两项都是实打实的带宽和峰值显存。

## 五、谁负责释放：从「老 dealloc」到「所有权分析」

分配讲完了，还得有人释放。 [【跳转到 32:21】](https://www.youtube.com/watch?v=nLydW5zQoLU&t=1941)MLIR 里这块历史上换过一次实现，教程花了不少篇幅讲**为什么换**。

![Old Buffer Deallocation：分支里只有一个分支分配时，老 pass 会在另一个分支插入一次分配 + 拷贝，好让函数末尾能无条件释放](assets/MLIR%20Bufferization：编译器如何决定哪些%20buffer%20可以原地复用/02001.webp)

老 pass 的毛病是它需要「函数末尾能无条件 dealloc」。 [【跳转到 33:46】](https://www.youtube.com/watch?v=nLydW5zQoLU&t=2026)于是当 `scf.if` 的一个分支分配、另一个分支不分配时，它只能在**另一个分支里也插一次分配并把参数内容拷过去**——如果那块 buffer 很大、而这条分支又是更常走的那条，这个代价非常荒唐。此外它还有**内存泄漏**（函数调用、非结构化控制流周围）、并且假设「buffer 的写一定支配（dominate）读」，而 one-shot bufferize **并不保证**这一点。

新方案是**基于所有权的缓冲化释放（ownership-based buffer deallocation）**： [【跳转到 37:06】](https://www.youtube.com/watch?v=nLydW5zQoLU&t=2226)

- **所有权是分配本身的属性**：一个分配的**所有别名共享同一份所有权**，不单独考虑；
- **所有者永远是一个基本块（basic block）**；
- 插入的是**条件释放** `bufferization.dealloc`：给它一串「可能要释放的 memref」、每个对应一个 `i1` 所有权标志、以及一串「**保留（retained）**的 memref」（这些别名后面可能还会被用）；
- 是否真的释放，运行时按「当前基本块是否持有所有权」+「有没有 retained 别名来自同一份分配」+ 活性分析（liveness）来决定，同时避免**重复释放**；
- **函数边界 ABI**：函数参数的 ownership 一律是 `false`（调用者拥有），所以函数里不会去释放外面传进来的 buffer。

代价是 lowering 有复杂度：默认 lowering 的时间复杂度大致是「待释放 memref 数的平方 + 条件释放数 × retained 数」，还需要插入一个**辅助库函数**（所以必须是 module pass）。因此提供了两种优化 lowering：**只有一个 memref 且无 retained** 时直接降成无条件 dealloc；**只有一个 memref 但有任意多个 retained** 时可以做成 function pass。

## 六、完整流水线：内存规划其实是一串 pass

![完整流水线：预处理（改写成 DPS、消 empty tensor）→ one-shot bufferize → buffer 级优化 → 释放](assets/MLIR%20Bufferization：编译器如何决定哪些%20buffer%20可以原地复用/02863.webp)

把前面所有零件拼起来，就是 MLIR 官方推荐的缓冲化流水线： [【跳转到 47:43】](https://www.youtube.com/watch?v=nLydW5zQoLU&t=2863)

| 阶段 | 关键 pass | 作用 |
| --- | --- | --- |
| 预处理 | `-rewrite-in-destination-passing-style`、`-eliminate-empty-tensors` | 把算子改写成 DPS 形态、消掉临时 buffer，让结果能直接写进目的地 |
| 缓冲化 | `-one-shot-bufferize` | 真正的 tensor → memref 改写，并做冲突检测决定 in-place / out-of-place |
| buffer 级优化 | `-buffer-hoisting`、`-buffer-loop-hoisting`、`-buffer-results-to-out-params`、`-drop-equivalent-buffer-results`、`-promote-buffers-to-stack` | 把 buffer 提到循环外、改成输出参数、把能放栈上的放到栈上 |
| 释放 | `-buffer-deallocation-pipeline` | 所有权分析 + 条件释放 + lowering |

还有一个很实用的细节：**缓冲化之后要跑一遍 canonicalize + CSE**。原因是 one-shot bufferize 是**逐算子**处理的，处理到循环终止符（terminator）时，它必须先复制一份，否则可能留下「还没被缓冲化、也没人用」的 tensor IR。这些复制出来的 `memref.copy` 常常是**同一个 subview 拷到同一个 subview**，canonicalize 一跑就全没了。

## 七、踩坑清单：这些坑最后都会变成多余的 copy

![Common Pitfalls：external model 没注册、函数边界没开、getBufferType 没实现、restrict 缺失、忽略 memory space](assets/MLIR%20Bufferization：编译器如何决定哪些%20buffer%20可以原地复用/00917.webp)

教程列出的常见坑，几乎每一条的后果都是「多出一次分配或拷贝」：

1. **`BufferizableOpInterface` 的 external model 没注册** → 那些算子根本没被缓冲化。MLIR 里靠 `initAllDialects.h` 统一注册，自己的编译器应该只注册需要的那些。
2. **想缓冲化函数边界但忘了开 flag** → 函数参数/返回值仍然是 tensor，边界上只能靠 `to_tensor` / `to_memref` 加 copy 过渡。
3. **`getBufferType` 没实现** → 一开始一切正常，**一旦把这个算子放进循环就变成非法 IR**（yield 出来的值类型和循环的 `iter_arg` 类型对不上）。这个函数的作用是「在 IR 还没被改写之前，预测一个结果未来的 buffer 类型」，因为缓冲化是**从外到内**做的：先缓冲化循环本身，再缓冲化循环体。
4. **输入 IR 里有两个 `to_tensor` 却没有 `restrict`** → 别名关系不明，框架只能保守处理。
5. **忽略 memory space** → 只编 CPU 时看不出问题，做 GPU 编译时**共享内存（shared memory）的 memory space 必须标对**，否则会分配错地方。
6. **假设「计算一定会落在某块 buffer 上」** → 没有 `materialize_in_destination` 就没有这个保证。
7. **循环的 yield 顺序和 `iter_arg` 不一致，或 yield 了循环外定义的值** → 当前实现会插入额外 copy。

### 7.1 调试手段：让编译器告诉你为什么插了 copy

教程演示了两个非常好用的开关： [【跳转到 19:40】](https://www.youtube.com/watch?v=nLydW5zQoLU&t=1180)

- `test-analysis-only=true` + `print-conflicts=true`：**只跑分析不改写 IR**，然后打印每个冲突三元组（`c0`、`c1`……），以及每个操作数的 `in-place operand` 标记（`true` 表示原地、`false` 表示这里插了 copy、`none` 表示不是 tensor 操作数）。
- 打印 **alias set**：看哪些值被判定为共享同一块 buffer。

演示里那个例子很典型：原本 `insert` 在 `extract` 之前，冲突检测报 `false`（需要 copy）；把 `extract` 挪到 `insert` 之前，所有标记变成 `true`，copy 消失。**改一行代码顺序，显存占用和带宽就变了**——这就是「内存规划」在源码层面的样子。

## 八、这些机制如何反映到端到端性能

把整场演讲翻译成性能语言，其实就三条：

1. **一次 out-of-place 就是一次额外的显存分配 + 一次整块拷贝**。在访存受限的负载上，这次拷贝直接吃掉带宽；在显存紧张时，它抬高**峰值显存**，可能让本来能跑的 batch size 跑不了。
2. **别名分析越准，能原地写的算子越多**。所以 `restrict`、`writable` 这些标注不是形式主义——它们直接决定编译器敢不敢原地写。
3. **empty tensor elimination 与 dealloc 流水线决定了「临时 buffer」和「泄漏」**。前者消掉整块临时分配，后者保证长跑不涨显存。

换句话说，编译器做内存规划的核心不是「找个聪明的分配算法」，而是**在正确的语义前提下，尽可能多地把写变成原地写**——这需要一套能证明「这么写不会破坏后面还要读的值」的分析，也就是本文第三节那个三元组。

## 小结

- `tensor` 不可变、没有地址；要执行必须 **bufferize 成 memref**，这一步就是编译器分配内存的地方。
- **DPS（目的传递风格）** 给出关键不变量：结果要么写回绑定的操作数，要么写进一块新 buffer，不会跑到第三块去。
- **冲突检测**找「定义 → 冲突写 → 读」三元组；命中就必须 out-of-place（分配 + 拷贝）。别名（`extract_slice` → `subview`）会一起算；写一部分、读另一部分不重叠的切片不算冲突；**定义在循环外、读写在内**则算冲突。
- **empty tensor elimination** 把「分配临时 buffer 再整体拷到目标」改成「直接算进目标」，省一次分配 + 一次拷贝。
- **所有权式 buffer deallocation** 用「所有权属于分配、别名共享、所有者是基本块」来插入条件释放，修掉老 pass 的内存泄漏与「为了无条件释放而多插一次拷贝」。
- 完整流水线是：**改写成 DPS → 消 empty tensor → one-shot bufferize → buffer 级优化 → 缓冲化释放**，之后别忘了 canonicalize + CSE 清掉冗余 `memref.copy`。
- 调试靠 `print-conflicts` 与 alias set 打印：**每一个 `false` 标记都是一次多余的显存往返**。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| bufferization | 把不可变、无地址的 tensor IR 降成有内存地址的 memref IR 的过程 |
| one-shot bufferize | MLIR 的缓冲化主 pass，一次性完成改写与冲突检测 |
| DPS（目的传递风格） | 结果与某个操作数绑定，保证结果写回该操作数或写进新 buffer |
| in-place / out-of-place | 原地写回输入 buffer / 分配新 buffer 再复制 |
| 冲突三元组 | 「定义 → 冲突写 → 读」，出现即说明原地写会破坏后续读取 |
| 别名（aliasing） | 多个值指向同一块内存，如 `extract_slice` 产生的子视图；分析必须一并考虑 |
| `restrict` | 声明「这块 buffer 只有这一个入口进入 tensor IR」，让别名分析能更激进 |
| empty tensor elimination | 把 `tensor.empty` 追到最终目的地，让计算直接写进目标 buffer |
| 所有权（ownership） | 分配本身的属性，别名共享；所有者是基本块，用于决定何时可安全释放 |
| `bufferization.dealloc` | 条件释放算子，按所有权标志与 retained 别名在运行时决定是否释放 |