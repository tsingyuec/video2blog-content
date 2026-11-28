# `__syncthreads()` 到底同步了什么：从竞争条件到隐式屏障

> 视频来源：[Intro to CUDA (part 6): Synchronization](https://www.youtube.com/watch?v=PJCISyoGpug)（YouTube · Josh Holloway）｜时长约 7.6 分钟
> 导读：这是「CUDA 入门」系列第六集，也是这套基础课里唯一专门讲同步的一集。讲者用一张数组左移的幻灯片把「为什么需要屏障」「屏障放在哪两行之间」讲透，最后把话题从块内屏障延伸到核与核之间的隐式屏障。本文按视频顺序复述，代码以幻灯片上实际出现的版本为准。

## 本讲要解决的核心问题（SCQA）

**背景**：CUDA 的卖点是「一个 kernel 被成千上万个线程同时执行」。既然线程是并行的，写代码时我们很自然地假设「我这一行执行完，别人就能看到结果」。

**冲突**：这个假设是错的。线程之间没有天然的先后顺序，一个线程可能在你写入之前就把旧值读走了，也可能在你读取之前就把新值写进去了——同一段代码，不同次运行可能给出不同答案。这类问题叫**竞争条件（race condition）**。

**疑问**：既然线程之间不能假设顺序，那怎样才能在代码里强制出一个「大家先都读完，然后才能开始写」的顺序？

**回答（中心思想）**：用一个**屏障（barrier）**——`__syncthreads()`——把 block 内所有线程拦在同一个点上，全部到齐才一起放行。屏障只能解决**块内**的顺序问题；块与块之间、kernel 与 kernel 之间靠的是另一套机制（核间隐式屏障 + `cudaDeviceSynchronize()`）。

## 一、竞争条件的两种形态：读早了，或者写早了

视频开头先把问题定义清楚。竞争条件最常见的两种形态是：

1. **读早于写**：某个线程从一个内存位置读取，而「正确的数据」还没被写进去。
2. **写早于读**：某个线程把自己的结果写进某个内存位置，而另一个线程还没把这个位置原来的数据读走。

![竞争条件的第一种形态：线程可能在另一个线程写入之前就读到了这个地址的内容](assets/__syncthreads%20到底同步了什么：从竞争条件到隐式屏障/00040.webp)

注意这两种形态都不是「代码写错了」，而是**同一段正确的代码在并行执行下产生了不确定的结果**。要避免它们，我们需要一种让线程「同步」的手段，本质上是在并行的设备代码里**强行插入一段串行**。[【跳转到 00:20】](https://www.youtube.com/watch?v=PJCISyoGpug&t=20)

## 二、屏障的语义：块内全部到齐，才一起放行

**是什么**：屏障是 kernel 里的一个点，block 内所有正在执行这个 kernel 的线程走到这里都会**停下**，等所有人到齐。

**为什么需要**：因为只有「所有人都停在屏障之前」这一状态，才能保证「屏障之前的读操作全部完成」或「屏障之前的写操作全部完成」。

**怎么做**：在 CUDA 里用 `__syncthreads()` 显式插入屏障。[【跳转到 01:00】](https://www.youtube.com/watch?v=PJCISyoGpug&t=60)

视频用四根彩色波浪线代表一个 block 里的四个线程：

![屏障的第一层含义：四条线程走到横线处全部停下，等其他人](assets/__syncthreads%20到底同步了什么：从竞争条件到隐式屏障/00080.webp)

![屏障的第二层含义：全部到齐后才一起继续往下执行](assets/__syncthreads%20到底同步了什么：从竞争条件到隐式屏障/00100.webp)

这两张图把屏障的两个阶段画得很清楚：**先停，再一起走**。它不保证「谁先谁后」，只保证「屏障之前的都做完了，屏障之后的才开始」。[【跳转到 01:20】](https://www.youtube.com/watch?v=PJCISyoGpug&t=80)

## 三、一个真实的错误用法：数组左移

视频用一个极小的例子说明屏障该放在哪。任务：把数组 `a` 的内容整体向左移一位，`a` 的长度是 4。

![朴素版本的 kernel：每个线程算自己的下标，然后把后一个元素赋给当前元素](assets/__syncthreads%20到底同步了什么：从竞争条件到隐式屏障/00189.webp)

```cuda
// Kernel Definition
__global__ void kernel( int* a )
{
    int i = threadIdx.x + blockIdx.x * blockDim.x;
    if( i < 3 )
    {
        a[i] = a[i+1];
    }
}
```

下标映射是前面几讲的老朋友：`threadIdx.x + blockIdx.x * blockDim.x`。`if (i < 3)` 是边界保护，防止线程 3 去读 `a[4]` 越界。[【跳转到 01:49】](https://www.youtube.com/watch?v=PJCISyoGpug&t=109)

**这段代码是错的**，原因就在 `a[i] = a[i+1]` 这一行：它同时是一次**读**和一次**写**。线程 0 把 `a[1]` 读出来写进 `a[0]` 的同时，线程 1 可能已经把 `a[2]` 写进了 `a[1]`——于是线程 0 读到的 `a[1]` 到底是原值还是被改过的值，完全取决于调度顺序。

修法分两步，第一步是**把读和写拆开**：[【跳转到 03:09】](https://www.youtube.com/watch?v=PJCISyoGpug&t=189)

```cuda
int temp = a[i+1];   // 先读进寄存器
```

`temp` 是每个线程私有的局部变量，实际落在寄存器里（如果数组特别大、寄存器不够，会被溢出到 local memory）。这样一来，「读」这个动作就与「写」这个动作在时间上解耦了。

第二步，在两个动作之间插一道屏障：[【跳转到 03:29】](https://www.youtube.com/watch?v=PJCISyoGpug&t=209)

![完整版本：先读进 temp，再 __syncthreads()，最后写回当前元素](assets/__syncthreads%20到底同步了什么：从竞争条件到隐式屏障/00269.webp)

```cuda
__global__ void kernel( int* a )
{
    int i = threadIdx.x + blockIdx.x * blockDim.x;
    if( i < 3 )
    {
        int temp = a[i+1];
        __syncthreads();
        a[i] = temp;
    }
}
```

现在屏障保证了：**所有线程都把 `a[i+1]` 读进自己的寄存器之后，才允许任何线程往 `a[i]` 里写**。[【跳转到 04:29】](https://www.youtube.com/watch?v=PJCISyoGpug&t=269)

讲者还提到，写完之后**再加一道屏障**更稳妥——保证所有写操作都完成之后，才允许任何线程再去读这个数组。在这个只有一次读写的例子里第二道屏障用不上，但如果后面还要接着读这块数据，它就是必需的。[【跳转到 04:49】](https://www.youtube.com/watch?v=PJCISyoGpug&t=289)

> 这里可以顺手总结出 `__syncthreads()` 的代价：它是**块级的全停等**。屏障之前最快的那批线程必须等最慢的那个线程，等待时间就是整个 block 的「短板」。所以屏障不能滥用——它换来的是正确性，付出的是并行度。

## 四、屏障不止块内一种：核与核之间的隐式屏障

讲到这里，视频把视角从「block 内部」拉到「主机与设备之间」。

**背景**：host（CPU 端代码）启动 kernel 之后**不会等它跑完**，而是立刻继续往下执行自己的流程——这就是 CUDA 的异步执行模型。[【跳转到 05:24】](https://www.youtube.com/watch?v=PJCISyoGpug&t=324)

**冲突**：如果 host 紧接着就要把 device 上的结果拷回主机，那它必须确保 kernel 已经跑完了。

**做法**：用 `cudaDeviceSynchronize()`。host 会在这个点停下来，直到之前启动的 kernel 执行完毕。[【跳转到 05:44】](https://www.youtube.com/watch?v=PJCISyoGpug&t=344)

![主机与设备的时间线：host 一路往下走，kernel 在 device 上并行跑，cudaDeviceSynchronize() 处才对齐](assets/__syncthreads%20到底同步了什么：从竞争条件到隐式屏障/00344.webp)

但视频强调了一个容易被忽略的事实：**连续的两次 kernel 启动之间，本身就是同步的**。第二个 kernel 的 grid 不会被调度到设备上，直到第一个 kernel 全部执行完毕。这可以看作 kernel 之间的一道**隐式屏障**——你不需要写任何代码，它就存在。[【跳转到 06:24】](https://www.youtube.com/watch?v=PJCISyoGpug&t=384)

![连续两次 kernel 启动之间是隐式同步：Grid 0 跑完，第二个 grid 才会被调度](assets/__syncthreads%20到底同步了什么：从竞争条件到隐式屏障/00393.webp)

把这一节的三种「同步」放在一起对比，就不会混淆了：

| 机制 | 作用范围 | 谁被拦住 | 是否需要手写 |
| --- | --- | --- | --- |
| `__syncthreads()` | 一个 block 内的所有线程 | 线程 | 需要 |
| kernel 之间的隐式屏障 | 前一个 kernel 的所有 block | 后一个 kernel 的 grid | 不需要，天然存在 |
| `cudaDeviceSynchronize()` | host 线程 | host 代码 | 需要 |

关键区别是**被拦住的对象不同**：前两个拦的是设备端的执行单元，第三个拦的是主机端的代码流。

## 五、回到 CUDA 的三个核心抽象

视频最后引用了 CUDA Programming Guide 的说法：CUDA 的核心抽象只有三样——

1. **计算的层级**：thread → block → grid；
2. **与之对应的存储层级**：register / shared memory → global memory；
3. **屏障同步原语**：`__syncthreads()` 这一族。

![CUDA in a nutshell：计算层级、存储层级、屏障原语，三件套](assets/__syncthreads%20到底同步了什么：从竞争条件到隐式屏障/00410.webp)

这也解释了为什么这门课把同步放在「基础部分」的最后一讲：前面几讲讲清了前两个抽象，讲完屏障，CUDA 的「基础语法」就齐了。讲者说，后续课程才会进入「如何优化 CUDA 程序、把 GPU 的所有资源用满」。[【跳转到 06:50】](https://www.youtube.com/watch?v=PJCISyoGpug&t=410)

## 小结

- **竞争条件的本质**是「读」和「写」在并行执行下失去了顺序保证，两种形态分别是读早于写、写早于读。
- **屏障 = 块内全停等**：所有线程到齐才放行。它给出的是「屏障之前全做完」这个保证，不给出任何先后顺序。
- **`__syncthreads()` 只能同步同一个 block 内的线程**，跨 block 无效。
- 一个典型的错误用法是「读-改-写」写在一条语句里（如 `a[i] = a[i+1]`）；正确做法是**先读进寄存器，屏障，再写回**。
- 屏障的代价是**并行度**：最快的线程要等最慢的线程，等待时间由 block 的短板决定。
- kernel 之间有**隐式屏障**（第二个 grid 等第一个跑完），host 与 device 之间靠 `cudaDeviceSynchronize()` 对齐。
- CUDA 的三个核心抽象是：计算层级、存储层级、屏障原语。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| 竞争条件（race condition） | 多个线程无顺序地读写同一内存位置，结果取决于调度，因而不可预测 |
| 屏障（barrier） | kernel 里的一个点，block 内所有线程必须全部到达才能继续 |
| `__syncthreads()` | CUDA 中显式插入块内屏障的内建函数 |
| 隐式屏障 | 连续两次 kernel 启动之间天然存在的同步关系 |
| `cudaDeviceSynchronize()` | 让 host 阻塞，直到此前启动的所有设备工作完成 |
| local memory | 寄存器不够时局部变量被溢出到的存储，物理上仍在显存里 |