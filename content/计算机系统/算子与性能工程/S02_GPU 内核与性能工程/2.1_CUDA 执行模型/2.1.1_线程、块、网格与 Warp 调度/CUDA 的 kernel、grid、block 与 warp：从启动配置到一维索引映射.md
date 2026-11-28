# CUDA 的 kernel、grid、block 与 warp：从启动配置到一维索引映射

> 视频来源：[CUDA: Kernels, Blocks, Grids, Threads and Warps](https://www.youtube.com/watch?v=OwJp5GudZ6o)（YouTube · Clarence Lee）｜时长约 24 分钟
> 导读：这支视频把「写一个 CUDA kernel」拆成四件事——kernel 是什么、grid/block/thread 三级层级怎么定义、`gridDim`/`blockDim` 与 `blockIdx`/`threadIdx` 怎么读、以及一个把数组元素翻倍的完整可运行程序。本文按同样顺序复述，代码以画面里实际敲出的版本为准。

## 本讲要解决的核心问题（SCQA）

**背景**：CUDA 程序里启动一个 kernel 只要一行 `kernel<<<grid, block>>>(...)`，括号里两个数字分别表示「多少个 block」和「每个 block 多少个线程」。

**冲突**：这一行代码凭空造出成百上千个线程，可代码里既没有循环也没有「谁处理哪个元素」的说明；更奇怪的是，从没在代码里出现过的「warp」却决定了硬件怎么执行。

**疑问**：kernel 到底怎么定义？`grid` 和 `block` 这两个数字该怎么填？每个线程又怎么算出自己该处理的数据下标？

**回答（中心思想）**：CUDA 用**三级逻辑层级**（grid → block → thread）描述线程，用**四个内置变量**让每个线程算出自己的唯一坐标——`gridDim`/`blockDim` 描述形状，`blockIdx`/`threadIdx` 给出坐标；硬件再把 block 拆成 **32 线程的 warp** 交给 SM 执行，所以 block 大小取 32 的倍数最划算。一维情形下，全局下标就是 `blockIdx.x * blockDim.x + threadIdx.x`。

## 一、kernel 就是「加了 `__global__` 的 C 函数」

在 CUDA 的语境里，**host** 指 CPU 及其内存，**device** 指 GPU 及其显存。两者分工不同：CPU 擅长有先后依赖的操作序列（分支预测、投机执行），GPU 擅长同时执行大量逻辑不复杂但数量极大的操作——画面里的对比图显示，GPU 把多得多的晶体管放在数据处理上。[【跳转到 00:48】](https://www.youtube.com/watch?v=OwJp5GudZ6o&t=48)

**kernel** 就是在 GPU 上执行的函数。定义方式和普通 C 函数几乎一样，唯一的差别是前面多一个 `__global__` 限定符：

```cpp
// Kernel definition
__global__ void VecAdd(float* A, float* B, float* C)
{
    int i = threadIdx.x;
    C[i] = A[i] + B[i];
}
```

![kernel 的定义：加上 __global__ 限定符，函数体里用 threadIdx.x 取自己的编号](assets/CUDA%20的%20kernel、grid、block%20与%20warp：从启动配置到一维索引映射/00085.webp)

这段代码值得多看两眼：函数体里没有循环，`i` 直接取自 `threadIdx.x`——每个线程用自己的编号去索引数组，这就是「同一段代码、不同数据」的最朴素形态。[【跳转到 01:25】](https://www.youtube.com/watch?v=OwJp5GudZ6o&t=85)

## 二、三级逻辑层级 + 一级硬件分组

CUDA 用五个词描述「线程在哪里」，视频把它们一次列全：

![SM、warp、grid、block、thread 的定义：前两个是硬件概念，后三个是逻辑层级](assets/CUDA%20的%20kernel、grid、block%20与%20warp：从启动配置到一维索引映射/00110.webp)

| 概念 | 定义 | 性质 |
| --- | --- | --- |
| Streaming Multiprocessor（SM） | GPU 的执行单元，执行的是 warp | 硬件 |
| Warp | 一组 32 个线程 | 硬件分组 |
| Grid | block 的集合，一个 grid 能放多少 block 取决于设备（T4 上可达 $10^{18}$ 量级） | 逻辑 |
| Block | 一组在 GPU 上执行的线程 | 逻辑 |
| Thread | CUDA 中最小的执行单位，执行同一段代码但处理不同数据 | 逻辑 |

硬件上，一个 SM 内部有寄存器文件、共享内存等存储单元，有负责执行 warp 的 CUDA core，还有负责调度的 warp scheduler。[【跳转到 01:50】](https://www.youtube.com/watch?v=OwJp5GudZ6o&t=110)

**warp 是这个模型里唯一「代码里看不见、但决定性能」的概念**，视频给了三条硬性事实：

1. 一个 warp 是 block 内 32 个线程的集合，**warp 内所有线程执行同一条指令**；
2. warp 内线程**保证同步**——一部分线程先做完、另一部分还没做完时，整个 warp 必须等所有线程都完成；
3. 一个 warp **只能由一个 CUDA core 处理**。

![warp 的三条性质：同一条指令、保证同步、只能由一个 CUDA core 处理](assets/CUDA%20的%20kernel、grid、block%20与%20warp：从启动配置到一维索引映射/00161.webp)

第 2 条是初学者最容易忽略的：warp 是一个「绑定在一起」的最小调度单位，线程数不是 32 的整数倍时，多出来的位置只能空转。[【跳转到 02:41】](https://www.youtube.com/watch?v=OwJp5GudZ6o&t=161)

## 三、启动配置：`gridDim`/`blockDim` 描述形状，`blockIdx`/`threadIdx` 给出坐标

程序员写好 kernel 之后，还得告诉 GPU「用多少线程去跑」。视频把这件事拆成两组变量：

![gridDim 是 grid 里每个轴的 block 数，blockDim 是 block 里每个轴的线程数](assets/CUDA%20的%20kernel、grid、block%20与%20warp：从启动配置到一维索引映射/00211.webp)

- **`gridDim`**：grid 在 x、y、z 三个轴上各有多少个 **block**；
- **`blockDim`**：block 在 x、y、z 三个轴上各有多少个 **线程**；
- **`blockIdx`**：当前 block 在 grid 里的坐标（x, y, z）；
- **`threadIdx`**：当前线程在 block 里的坐标（x, y, z）。

注意这四个变量都是**三维**的，即使你只写一维程序，`.x` 之外还有 `.y`、`.z` 可用（默认为 1）。视频用一个 3×3×3 的 grid 演示了坐标怎么读：

![3×3×3 的 grid、blockDim 为 (4,1,4)，紫色 block 的 blockIdx 是 (0,0,2)，高亮线程的 threadIdx 是 (0,0,3)](assets/CUDA%20的%20kernel、grid、block%20与%20warp：从启动配置到一维索引映射/00236.webp)

画面左下角把这组数值写全了：

```text
gridDim.x = 3, gridDim.y = 3, gridDim.z = 3
blockDim.x = 4, blockDim.y = 1, blockDim.z = 4
blockIdx.x = 0, blockIdx.y = 0, blockIdx.z = 2
threadIdx.x = 0, threadIdx.y = 0, threadIdx.z = 3
```

这里有个容易踩的坑：**`blockDim.z = 4` 意味着 z 方向一个 block 里有 4 个线程，但 `blockIdx.z = 2` 指的是 grid 里第 3 个 block**——`Dim` 描述「有多少」，`Idx` 描述「第几个」。把两者混起来，索引立刻算错。[【跳转到 03:31】](https://www.youtube.com/watch?v=OwJp5GudZ6o&t=211)

由此得到最常用的两条映射公式。一维（只关心 x）：

$$
\text{idx} = \text{blockIdx.x} \times \text{blockDim.x} + \text{threadIdx.x}
$$

二维（矩阵的行列）：

$$
\text{col} = \text{blockIdx.x} \times \text{blockDim.x} + \text{threadIdx.x},\qquad
\text{row} = \text{blockIdx.y} \times \text{blockDim.y} + \text{threadIdx.y}
$$

读法很直白：**先数「前面有多少个 block」，每个 block 有 `blockDim` 个线程，再加上「我在本 block 里排第几」**，就是全局编号。

## 四、硬件接手：block 分给 SM，block 再拆成 warp

逻辑层级只是给程序员的抽象，硬件侧的动作是另一套：

![GPU 把 block 分配给各个 SM，SM 再执行 warp](assets/CUDA%20的%20kernel、grid、block%20与%20warp：从启动配置到一维索引映射/00261.webp)

1. GPU 把 grid 里的 block **分配给各个 SM**；
2. SM 并不直接处理 block，而是先把 block **划分成 warp**，每个 warp 32 个线程；
3. 每个 warp 交给一个 CUDA core 执行。

这就解释了视频里那句实用建议：**block 大小最好取 32 的倍数**。因为划分是按 32 一刀切下去的，`blockDim = 100` 会被切成 3 个满 warp 加 1 个只有 4 个线程的残 warp，最后那个 warp 里 28 个位置全程空转，浪费的是实实在在的算力。[【跳转到 04:46】](https://www.youtube.com/watch?v=OwJp5GudZ6o&t=286)

顺带一提，不同 GPU 的规格（每 block 最大线程数、grid 尺寸上限、SM 数量）并不相同，写死参数前应当先查。[【跳转到 05:11】](https://www.youtube.com/watch?v=OwJp5GudZ6o&t=311)

## 五、动手：把数组每个元素翻倍

视频用一个最小例子把上面所有概念串起来：CPU 内存里有一个数组 `[1, 2, 3, 4, 5]`，要在 GPU 上把每个元素乘 2。

### 5.1 先看清 host 与 device 的内存不共享

CUDA 编程里 host 和 device 的内存是两块互不相通的空间，所以「搬数据」是固定动作，四个 API 组成一条流水线：

![cudaMalloc 分配显存、cudaMemcpy 双向搬运、cudaFree 释放](assets/CUDA%20的%20kernel、grid、block%20与%20warp：从启动配置到一维索引映射/00366.webp)

```cpp
cudaMalloc(&d_arr, size * sizeof(int));                                   // 在显存上开空间
cudaMemcpy(d_arr, h_arr, size * sizeof(int), cudaMemcpyHostToDevice);     // host -> device
// ... 调用 kernel ...
cudaMemcpy(h_arr, d_arr, size * sizeof(int), cudaMemcpyDeviceToHost);     // device -> host
cudaFree(d_arr);                                                          // 释放显存
```

顺序不能乱：**先分配、再拷入、再算、再拷回、最后释放**。如果漏掉最后那次 `cudaMemcpy`，CPU 侧看到的还是旧数据——kernel 的修改只发生在显存里。[【跳转到 06:06】](https://www.youtube.com/watch?v=OwJp5GudZ6o&t=366)

### 5.2 kernel：一行算出全局下标，一行做边界检查

真正干活的 kernel 只有三行有效代码：

```cpp
__global__ void doubleArrayKernel(int* arr, int size)
{
    int idx = blockDim.x * blockIdx.x + threadIdx.x;
    if (idx < size)
    {
        arr[idx] *= 2;
    }
}
```

![kernel 里用 blockDim.x * blockIdx.x + threadIdx.x 算出全局下标](assets/CUDA%20的%20kernel、grid、block%20与%20warp：从启动配置到一维索引映射/00984.webp)

`if (idx < size)` 这一句不是可选项。原因是 kernel 以 block 为单位启动，**block 大小往往大于数组长度**：数组只有 50 个元素，而 block 有 128 个线程，那 50 号以后的线程照样会被启动。没有这个判断，它们就会去读写数组之外的内存。[【跳转到 16:49】](https://www.youtube.com/watch?v=OwJp5GudZ6o&t=1009)

![带边界检查的完整 kernel 与主机端函数：cudaMalloc、两次 cudaMemcpy](assets/CUDA%20的%20kernel、grid、block%20与%20warp：从启动配置到一维索引映射/01134.webp)

### 5.3 启动配置：block 大小自己定，block 数量算出来

主机端调用 kernel 时要填两个数字。视频的选择是「线程数取整、block 数向上取整」：

```cpp
int threadsPerBlock = 128;
int numBlocks = (size + threadsPerBlock - 1) / threadsPerBlock;
doubleArrayKernel<<<numBlocks, threadsPerBlock>>>(d_arr, size);
```

![启动配置：先定每个 block 的线程数，再用 (size + threadsPerBlock - 1) / threadsPerBlock 算 block 数](assets/CUDA%20的%20kernel、grid、block%20与%20warp：从启动配置到一维索引映射/01159.webp)

`(size + threadsPerBlock - 1) / threadsPerBlock` 是整数除法下的**向上取整**技巧：`size = 50`、`threadsPerBlock = 128` 时得到 1 个 block；`size = 200` 时得到 2 个 block。它保证「至少覆盖所有元素」，代价是最后可能多出一批越界线程——正好由 5.2 的边界检查兜住。这两个设计是配套的：**向上取整 + 边界检查**才是完整的一套。[【跳转到 19:19】](https://www.youtube.com/watch?v=OwJp5GudZ6o&t=1159)

### 5.4 先写一份 CPU 版本做对照

视频特意先写了一个纯 CPU 的 `main.cpp`：分配 `new int[SIZE]`、填值、循环乘 2、打印。这样做的好处是有一个可信的参照物——GPU 版本跑完之后，把两个数组打印出来一比，就知道对不对。[【跳转到 12:39】](https://www.youtube.com/watch?v=OwJp5GudZ6o&t=759)

最终把 CUDA 版本跑通时，数组元素全部翻倍，与 CPU 版本一致。[【跳转到 23:29】](https://www.youtube.com/watch?v=OwJp5GudZ6o&t=1409)

## 六、查设备规格：`cudaDeviceProp`

写启动配置前，最好先知道手里这块卡的上限。视频用四行代码取设备属性：

![取设备属性的四行代码：cudaGetDevice 拿编号，cudaGetDeviceProperties 拿属性](assets/CUDA%20的%20kernel、grid、block%20与%20warp：从启动配置到一维索引映射/00311.webp)

```cpp
int deviceId;
cudaGetDevice(&deviceId);
cudaDeviceProp deviceProp;
cudaGetDeviceProperties(&deviceProp, deviceId);
```

拿到 `deviceProp` 之后可以读出一串关键字段：

- `deviceProp.name`：设备名；
- `deviceProp.maxThreadsPerBlock`：一个 block 最多多少线程（决定 `blockDim` 的上限）；
- `deviceProp.multiProcessorCount`：SM 数量。视频在 T4 上跑出 40 个 SM。

![完整程序：打印设备名、每 block 最大线程数和 SM 数量，运行后显示设备名是 Tesla T4](assets/CUDA%20的%20kernel、grid、block%20与%20warp：从启动配置到一维索引映射/00684.webp)

知道 SM 数量有什么用？它决定了「同时能装下多少 block」，也就决定了你的 grid 是「一次就铺满」还是「要分好几轮」。视频在 T4 上查到 40 个 SM，正是后面讨论占用率的基础数字。[【跳转到 10:59】](https://www.youtube.com/watch?v=OwJp5GudZ6o&t=659)

## 小结

- **kernel = 加了 `__global__` 的普通函数**，它在 GPU 上执行，每个线程跑同一段代码、处理不同数据。
- 线程有**三级逻辑层级**：grid → block → thread；硬件侧多一层分组：block 被拆成 **32 线程的 warp**，warp 才是被调度的单位。
- 四个内置变量分工明确：`gridDim`/`blockDim` 说「有多少」，`blockIdx`/`threadIdx` 说「第几个」；一维全局下标是 `blockIdx.x * blockDim.x + threadIdx.x`。
- 硬件流程是：block 分给 SM → block 拆成 warp → warp 交给 CUDA core。因此 **block 大小取 32 的倍数**能避免残 warp 空转。
- 启动配置的标准写法是「线程数取整、block 数向上取整」：`numBlocks = (size + threads - 1) / threads`，并**必须**在 kernel 里配一句 `if (idx < size)` 的边界检查。
- host 与 device 内存不共享，固定流水线是 `cudaMalloc → cudaMemcpy(H2D) → kernel → cudaMemcpy(D2H) → cudaFree`。
- 写死参数之前，用 `cudaGetDeviceProperties` 查一下 `maxThreadsPerBlock` 和 `multiProcessorCount`。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| host / device | host 是 CPU 及其内存，device 是 GPU 及其显存，两者内存不共享 |
| kernel | 在 GPU 上执行的函数，用 `__global__` 限定符定义 |
| grid | block 的集合，一次 kernel 启动对应一个 grid |
| block | 一组线程，是分配给 SM 的单位 |
| thread | CUDA 最小执行单位，执行同一段代码但处理不同数据 |
| warp | 32 个线程一组，同一条指令、保证同步，只能由一个 CUDA core 处理 |
| gridDim / blockDim | grid 每个轴的 block 数 / block 每个轴的线程数 |
| blockIdx / threadIdx | 当前 block 在 grid 中的坐标 / 当前线程在 block 中的坐标 |
| `cudaMalloc` / `cudaMemcpy` / `cudaFree` | 分配显存 / 在 host 与 device 间搬运数据 / 释放显存 |
| `cudaDeviceProp` | 设备属性结构体，可读 SM 数量、每 block 最大线程数等 |