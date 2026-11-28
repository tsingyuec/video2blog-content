# 二维 grid 与 block 写矩阵加法：行列索引映射与行主序一维化

> 视频来源：[🚀 CUDA Programming Day 2: Grid, Block, and Threads | Parallel Matrix Addition](https://www.youtube.com/watch?v=viTFnXRPnsY)（YouTube · MLWorks）｜时长约 21 分钟
> 导读：这一集把「二维矩阵」完整地映射到「二维 grid/block 的线程」上：先推行列索引公式，再做边界检查，再用行主序把二维压成一维，最后用 `dim3` 配好启动参数跑通。文中代码与画面里实际敲出的版本一致，包括中途出现的一个真实编译警告。

## 本讲要解决的核心问题（SCQA）

**背景**：CUDA 的 block 和 grid 都有 x、y、z 三个维度，`dim3` 可以一次给出二维形状，所以「一个线程对应矩阵的一个格子」看起来是很自然的事。

**冲突**：矩阵是二维的（行、列），可显存里的数组是一维的；线程编号也是「第几个 block、block 里第几个线程」这种分层编号。三套编号之间没有现成的对应关系。

**疑问**：线程怎么算出自己负责矩阵的哪一行、哪一列？二维坐标又怎么变成一维数组下标？`grid` 和 `block` 这两个参数该填多少？

**回答（中心思想）**：二维索引由同一条公式在两个方向上各算一次——`blockIdx.x * blockDim.x + threadIdx.x` 得列、`blockIdx.y * blockDim.y + threadIdx.y` 得行；再用行主序公式 `index = i * size + j` 把二维坐标压成一维下标；`grid` 用向上取整算出来，并配一句边界检查兜住多出来的线程。矩阵之所以必须按行主序存成**连续**内存，是因为只有连续内存才能整块 `cudaMemcpy`。

## 一、把矩阵映射到线程：100 个元素对应 100 个线程

视频的目标很具体：一个 10×10 的矩阵有 100 个元素，那就造 100 个线程，一个线程负责一个格子。因为是二维矩阵，线程的坐标得是 $(i, j)$ 而不是单个数字。

![二维 grid 的 block 布局：Grid 1 里排着 Block(0,0)、Block(0,1)…，每个 block 里又是 Thread(0,0,0) 这样的三维编号](assets/二维%20grid%20与%20block%20写矩阵加法：行列索引映射与行主序一维化/00061.webp)

这一集的核心命题就是「矩阵怎么映射到线程上」：矩阵是二维的，线程是按 block 分层的，两者之间要靠索引公式搭桥。[【跳转到 00:25】](https://www.youtube.com/watch?v=viTFnXRPnsY&t=25)

这张图把三层结构画在一起：一个 grid 里有若干 block，每个 block 里有一组线程，线程的编号自带 x、y、z 三个分量——本集只用 x 和 y。[【跳转到 01:01】](https://www.youtube.com/watch?v=viTFnXRPnsY&t=61)

## 二、kernel 骨架：二维 grid/block 下算出 (i, j)

整个程序从一个 `.cu` 文件开始，`const int N = 10` 定义矩阵维度，然后就是 kernel：

```cpp
#include <iostream>
#include <cmath>

// matrix dimension
const int N = 10;   // 10 x 10

// kernel function
// it uses 2d grid and 2d block
__global__ void matrix_addition(int *A, int *B, int *C, int size)
{
    int i = blockIdx.x * blockDim.x + threadIdx.x;  // column index
    int j = blockIdx.y * blockDim.y + threadIdx.y;  // row index
    ...
}
```

![kernel 骨架：__global__ 限定符、三个 int 指针加一个 size，函数体第一件事是算行列索引](assets/二维%20grid%20与%20block%20写矩阵加法：行列索引映射与行主序一维化/00289.webp)

这两行是整个小节的骨架，值得拆开看。以 `i` 为例：

$$
i = \text{blockIdx.x} \times \text{blockDim.x} + \text{threadIdx.x}
$$

- `blockIdx.x`：当前 block 在 grid 的 x 方向上是第几个；
- `blockDim.x`：一个 block 在 x 方向上有多少线程；
- `threadIdx.x`：当前线程在这个 block 的 x 方向上是第几个。

三者合起来回答一个问题：**在我之前已经排了多少个线程？再加上我在本 block 里的位置，就是我的全局编号。** `j` 只是把 x 换成 y。[【跳转到 04:49】](https://www.youtube.com/watch?v=viTFnXRPnsY&t=289)

![代码里两行索引的注释：i 标为 column index，j 标为 row index](assets/二维%20grid%20与%20block%20写矩阵加法：行列索引映射与行主序一维化/00416.webp)

在进 kernel 之前，视频先把 2×2 的矩阵加法讲清楚：逐元素相加，$a_{11} + b_{11}$ 得到结果的左上角，其余元素同理。矩阵加法之所以适合并行，就是因为 100 个格子之间互不依赖，可以交给 100 个线程同时算。[【跳转到 02:01】](https://www.youtube.com/watch?v=viTFnXRPnsY&t=121)

这里有个细节要留意：视频代码把 `i`（来自 x 方向）注释成**列**、`j`（来自 y 方向）注释成**行**；而后面幻灯片上画矩阵时，`i` 是向下的**行**、`j` 是向右的**列**。两种约定本身都能用，但必须自始至终保持一致——尤其是下面要讲的「哪个方向乘 size」。[【跳转到 06:56】](https://www.youtube.com/watch?v=viTFnXRPnsY&t=416)

## 三、边界检查与行主序一维化

拿到 $(i, j)$ 之后还不能直接访存，先要过两道关。

**第一关：边界检查。** 矩阵只有 100 个元素，但启动时线程数往往多于 100（因为 `blockDim` 是 32、16 这种整齐的数）。越界的线程如果照常访问内存，就会触发越界访问。所以：

```cpp
if (i < N && j < N)
{
    int index = i * size + j;
    C[index] = A[index] + B[index];
}
```

**第二关：二维转一维。** 显存里没有「二维数组」，只有一条连续的内存，所以要用行主序公式把坐标压成下标：

$$
\text{index} = i \times \text{size} + j
$$

其中 `size` 是一行的长度（这里是 N = 10）。直观理解：**跳过前面完整的 i 行（每行 size 个元素），再加上本行的第 j 个**。

![2D 转 1D：3×4 的矩阵按行摊平成 index 0..11，A 变成 [1 2 3 4 5 6 7 8 1 3 2 9]](assets/二维 grid 与 block 写矩阵加法：行列索引映射与行主序一维化/00510.webp)

`size` 这个参数从主机端一路传进 kernel，就是为这一行公式服务的。[【跳转到 05:45】](https://www.youtube.com/watch?v=viTFnXRPnsY&t=345)

这张图把「摊平」过程画得很清楚：矩阵里 (行 1, 列 0) 的元素 `5`，摊平后落在 index 4 = $1 \times 4 + 0$。所有元素都按这条公式换算，之后 kernel 里就只剩一维下标了。[【跳转到 08:30】](https://www.youtube.com/watch?v=viTFnXRPnsY&t=510)

## 四、host 侧：`dim3` 配置与向上取整

kernel 写完之后是主机端流程：声明 `h_a`、`h_b`、`h_c`（`new int[N * N]`），填值（`h_a` 放 1、`h_b` 放 2、`h_c` 置 0），再声明 `d_a`、`d_b`、`d_c` 并用 `cudaMalloc` 分配显存，最后两次 `cudaMemcpy(..., cudaMemcpyHostToDevice)` 把数据搬上去。

![主机端：填值、cudaMalloc 分配三个显存数组、两次 cudaMemcpy 搬到 device](assets/二维%20grid%20与%20block%20写矩阵加法：行列索引映射与行主序一维化/00785.webp)

真正决定「用多少线程」的是这两行：

```cpp
dim3 blockDim(32, 16);
dim3 gridDim((int)ceil((float)N / blockDim.x), (int)ceil((float)N / blockDim.y));  // 10/32, 10/16 = (1, 1)
matrix_addition<<<gridDim, blockDim>>>(d_a, d_b, d_c, N);
```

![启动配置：blockDim 取 (32,16)，gridDim 用 ceil(N/blockDim) 算出 (1,1)](assets/二维%20grid%20与%20block%20写矩阵加法：行列索引映射与行主序一维化/00885.webp)

三个要点：

1. **`blockDim` 是「我选的」**：一个 block 32 列 × 16 行，共 512 个线程；
2. **`gridDim` 是「算出来的」**：$10 / 32 = 0.3125$ 向上取整得 1，$10 / 16 = 0.625$ 向上取整也得 1，所以一个 block 就够；
3. **必须向上取整**：如果直接整除，$10 / 32$ 会得到 0，一个 block 都不启动，kernel 根本不执行。

填值这一步用的是同一套一维下标：`for (int i = 0; i < N * N; i++)` 里直接写 把 `h_a` 的第 i 个元素赋成 1，因为此时矩阵已经是摊平后的连续数组了。[【跳转到 11:00】](https://www.youtube.com/watch?v=viTFnXRPnsY&t=660)

代价是「线程比元素多」：一个 block 有 512 个线程，矩阵只有 100 个元素，多出来的 412 个线程全靠第三节那句 `if (i < N && j < N)` 挡住。[【跳转到 13:05】](https://www.youtube.com/watch?v=viTFnXRPnsY&t=785)

## 五、同步、拷回、编译运行

kernel 是异步启动的，主机端不等它算完就继续往下走。所以拷回结果之前必须加一道同步：

```cpp
matrix_addition<<<gridDim, blockDim>>>(d_a, d_b, d_c, N);
cudaDeviceSynchronize();                                              // 等所有线程算完
cudaMemcpy(h_c, d_c, matrix_size, cudaMemcpyDeviceToHost);            // 结果搬回主机
cudaFree(d_a); cudaFree(d_b); cudaFree(d_c);                          // 释放显存
```

漏掉 `cudaDeviceSynchronize()` 的后果是：可能拷回一份还没算完的数据，结果时对时错。

结果打印同样是一维循环，`h_c` 的第 i 个元素依次输出，中间用空格隔开。[【跳转到 16:25】](https://www.youtube.com/watch?v=viTFnXRPnsY&t=985)

然后 用 nvcc 把 `matrix_addition.cu` 编译成可执行文件 `mathadd` 编译、运行。视频在这里遇到一个真实警告：`main` 函数里传的是 device 内置变量 `blockIdx`，而这里应该传 `blockDim`——因为 `(32, 16)` 这个配置是存在 `blockDim` 里的，`blockIdx` 是 kernel 内部才有效的坐标。改成传 dimension 之后重新编译，输出矩阵全是 3，说明 $1 + 2$ 全部算对了。[【跳转到 18:05】](https://www.youtube.com/watch?v=viTFnXRPnsY&t=1085)

![运行结果：矩阵里全是 3，h_c 从 0 变成 1+2](assets/二维%20grid%20与%20block%20写矩阵加法：行列索引映射与行主序一维化/01135.webp)

这个 bug 挺有代表性：`blockIdx` 和 `blockDim` 只差几个字母，但一个是「第几个 block」，一个是「每个 block 多少线程」，传错方向整条索引公式就崩了。

## 六、为什么矩阵要按行主序存成连续内存

视频最后专门解释了「为什么用一维数组 + 行主序，而不是 `int**` 的二维数组」：

![2D 转 1D 的另一视角：上面是线程网格，下面是摊平后的 index 序列](assets/二维%20grid%20与%20block%20写矩阵加法：行列索引映射与行主序一维化/01196.webp)

视频把这一点称为整个程序里最重要的地方。[【跳转到 19:20】](https://www.youtube.com/watch?v=viTFnXRPnsY&t=1160)

在标准 C++ 里动态分配二维数组时，**每一行是单独分配的一块内存**，三行就是三块分散在不同位置的内存。要把这样的数据搬到 GPU，你得一块一块地迭代拷贝，既慢又麻烦。

而按行主序存成一整块连续内存之后，一次 `cudaMemcpy` 就能把整个矩阵送上去，kernel 里也只需要一条 `index = i * size + j` 的换算。[【跳转到 19:56】](https://www.youtube.com/watch?v=viTFnXRPnsY&t=1196)

这也解释了为什么「索引公式」和「存储顺序」必须成对设计：公式里的 `size` 就是行主序的步长，换一种存储顺序（比如列主序），公式就得跟着改成 `j * size + i`。

## 小结

- 二维映射的核心是**同一条公式在两个方向各算一次**：`i = blockIdx.x * blockDim.x + threadIdx.x`（列），`j = blockIdx.y * blockDim.y + threadIdx.y`（行）。
- 索引公式的语义是「前面有多少个线程 + 我在本 block 里排第几」，所以 `blockIdx` 一定要乘 `blockDim`。
- 访存前必须做**边界检查** `if (i < N && j < N)`，因为线程数通常多于元素数。
- 二维坐标用**行主序**压成一维：`index = i * size + j`；公式里的 `size` 就是存储顺序的步长。
- 启动配置用 `dim3` 给出二维形状：`blockDim` 自己选（本例 32×16），`gridDim` 用 `ceil(N / blockDim)` **向上取整**算出来，否则可能一个 block 都不启动。
- kernel 异步执行，拷回结果前要 `cudaDeviceSynchronize()`；`blockIdx` 与 `blockDim` 别传混。
- 矩阵必须按行主序存成**连续内存**，才能整块 `cudaMemcpy`；`int**` 的二维数组是分散的，搬起来又慢又麻烦。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| 二维 grid / 二维 block | 用 `dim3(x, y)` 指定形状，线程因此拥有 (x, y) 两个方向的坐标 |
| `blockIdx.x` / `blockIdx.y` | 当前 block 在 grid 的列方向 / 行方向上是第几个 |
| `blockDim.x` / `blockDim.y` | 一个 block 在列方向 / 行方向上有多少线程 |
| 全局索引 | `blockIdx * blockDim + threadIdx`，即「之前所有线程数 + 我的位置」 |
| 边界检查 | `if (i < N && j < N)`，挡住比元素多的那批线程 |
| 行主序（row-major） | 二维矩阵按行依次摊平成一维，`index = i * size + j` |
| `dim3` | CUDA 的三维尺寸类型，用来给 `blockDim` / `gridDim` 赋值 |
| `cudaDeviceSynchronize` | 阻塞主机直到 device 上所有任务完成，拷回结果前必须调用 |