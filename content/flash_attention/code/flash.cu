// flash.cu —— 第08讲《CUDA 算子解析》配套代码（可运行版）
// 说明：本文件基于视频中作者（比飞鸟贵重的多_HKL）重写的版本整理，
//       修正了若干问题、补充了详细注释，并加入了 d=128 时所需的共享内存上限设置。
//
// 相对作者原版修正的地方：
//   1) bid 的压平顺序：改为 blockIdx.x * gridDim.y + blockIdx.y，
//      以匹配张量 [B, nh, N, d] 的布局（原来写成 gridDim.x*blockIdx.y+blockIdx.x，顺序反了）
//   2) L/M 的全局偏移：补上 bid * N（每个 (batch, head) 一段）
//   3) Ss 的计算：K 的行索引用 l（而非 tid），且累加前先清零
//   4) sram_size：按实际共享内存布局 (d*Br + 2*d*Bc + Bc*Br) 计算
//   5) 外层循环末尾补 __syncthreads()，避免下一轮覆盖 Ks/Vs 时的读写竞争
//   6) 动态共享内存 > 48KB 时，用 cudaFuncSetAttribute 抬高上限（否则 d=128 会启动失败）
//
// 注意：这是一个教学用 kernel，假设 N 能被 Bc/Br 整除、且 blockDim == Br == Bc，
//       未做边界处理；生产实现还需考虑边界、任意线程数与访存合并。

#include <torch/types.h>
#include <cuda.h>
#include <cuda_runtime.h>
#include <cmath>
#include <cstdio>

// =====================================================================
// GPU 端：__global__ kernel
// 每个 block 负责一组 (batch, head) 的 attention 计算；
// block 内 Bc 个线程各负责一行 Q，在 shared memory 上完成分块 + online softmax。
// =====================================================================
__global__ void my_forward_kernel(const float* Q, const float* K, const float* V,
                                  const int N, const int d,
                                  const int Tc, const int Tr, const int Bc, const int Br,
                                  const float softmax_scale,
                                  float* L, float* M, float* O)
{
    // ---------- 线程 / 块索引 ----------
    const int thread_num_per_block = blockDim.x * blockDim.y; // 本 block 线程数（= Bc）
    int tid = threadIdx.x;                                    // block 内线程号，对应一行 Q

    // 把二维 grid (x=batch, y=head) 压平为线性 bid，匹配张量 [B, nh, N, d] 的布局：
    // 第 (b, h) 组的数据起始下标 = (b * nh + h) * ...
    int bid = blockIdx.x * gridDim.y + blockIdx.y;            // = batch * nh + head

    // ---------- 每组 (batch, head) 的起始指针 ----------
    // Q/K/V/O 形状均为 [B, nh, N, d]，一组占 N*d 个元素
    const float* Q_start = Q + bid * d * N;
    const float* K_start = K + bid * d * N;
    const float* V_start = V + bid * d * N;
    float*       O_start = O + bid * d * N;
    // L/M 形状为 [B, nh, N]，一组占 N 个元素
    float* L_start = L + bid * N;
    float* M_start = M + bid * N;

    // ---------- 划分动态共享内存（SRAM）----------
    // 布局：Qs[d*Br] | Ks[d*Bc] | Vs[d*Bc] | Ss[Bc*Br]
    extern __shared__ float smem[];
    int offset = 0;
    float* Qs = &smem[offset];  offset += d * Br; // Q 分块：Br 行 × d 列
    float* Ks = &smem[offset];  offset += d * Bc; // K 分块：Bc 行 × d 列
    float* Vs = &smem[offset];  offset += d * Bc; // V 分块：Bc 行 × d 列
    float* Ss = &smem[offset];                    // 分数分块 S = QKᵀ：每线程一行、Bc 列

    // ================== 外层循环：遍历 K、V 分块（慢）==================
    for (int i = 0; i < Tc; i++) {
        // 把第 i 个 K、V 分块从 HBM 搬到 SRAM（d*Bc 个元素，多个线程协作搬运）
        for (int j = 0; j < d * Bc; j += thread_num_per_block) {
            Ks[j + tid] = K_start[i * d * Bc + j + tid];
            Vs[j + tid] = V_start[i * d * Bc + j + tid];
        }
        __syncthreads(); // 等 Ks/Vs 全部就位，之后所有线程都要读它们

        // ================== 内层循环：遍历 Q 分块（快）==================
        for (int j = 0; j < Tr; j++) {
            // 把第 j 个 Q 分块搬到 SRAM（每线程只写/读自己那一行，天然无跨线程冲突）
            for (int k = 0; k < d * Br; k += thread_num_per_block) {
                Qs[k + tid] = Q_start[j * d * Br + k + tid];
            }
            __syncthreads(); // 确保 Qs 写完，再进入下面的计算

            // ---- 计算 S = Q·Kᵀ，并对本线程负责的这一行求最大值 row_m ----
            float row_m = -INFINITY;
            for (int l = 0; l < Bc; l++) {           // 遍历 K 分块的 Bc 个列
                Ss[tid * Bc + l] = 0.0f;             // 必须先清零，才能用 += 累加
                for (int m = 0; m < d; m++) {        // 点积：Q 的第 tid 行 · K 的第 l 行
                    Ss[tid * Bc + l] += Qs[tid * d + m] * Ks[l * d + m];
                }
                Ss[tid * Bc + l] *= softmax_scale;   // 乘 1/√d
                if (Ss[tid * Bc + l] > row_m)
                    row_m = Ss[tid * Bc + l];
            }

            // ---- P = exp(S - row_m)，并求本行的指数和 row_l ----
            float row_l = 0.0f;
            for (int k = 0; k < Bc; k++) {
                Ss[tid * Bc + k] = __expf(Ss[tid * Bc + k] - row_m);
                row_l += Ss[tid * Bc + k];
            }

            // ---- 读取上一轮累积的状态（online softmax 的关键）----
            float row_m_prev = M_start[j * Br + tid]; // 该行此前的最大值 M_{j-1}
            float row_l_prev = L_start[j * Br + tid]; // 该行此前的指数和 L_{j-1}

            // ---- 在线更新最大值与指数和 ----
            // M_j = max(M_{j-1}, m)
            // L_j = L_{j-1} * exp(M_{j-1} - M_j) + exp(m - M_j)
            float row_m_new = max(row_m_prev, row_m);
            float row_l_new = (__expf(row_m_prev - row_m_new) * row_l_prev)
                            + (__expf(row_m - row_m_new) * row_l);

            // ---- 计算 P·V，并按公式更新输出 O（写回 HBM）----
            for (int x = 0; x < d; x++) {            // 输出向量的第 x 个通道
                float pv = 0.0f;                     // (Pij · Vj) 的第 x 个分量
                for (int y = 0; y < Bc; y++) {
                    pv += Ss[tid * Bc + y] * Vs[y * d + x];
                }
                // O_j = O_{j-1} * (L_{j-1}/L_j) * exp(M_{j-1}-M_j)
                //     + (1/L_j) * exp(m - M_j) * (P·V)
                O_start[j * d * Br + tid * d + x] = (1.0f / row_l_new) *
                    ((row_l_prev * __expf(row_m_prev - row_m_new)
                        * O_start[j * d * Br + tid * d + x])       // 旧输出按比例缩放
                     + (__expf(row_m - row_m_new) * pv));          // 加上本块贡献
            }

            // ---- 把新的 L、M 写回 HBM，供下一个 K/V 分块使用 ----
            M_start[j * Br + tid] = row_m_new;
            L_start[j * Br + tid] = row_l_new;
        }

        __syncthreads(); // 避免下一轮覆盖 Ks/Vs 时，仍有线程在读取本轮数据
    }
}

// =====================================================================
// host 端：把 kernel 包装成 LibTorch 算子
// =====================================================================
torch::Tensor my_forward(torch::Tensor Q, torch::Tensor K, torch::Tensor V) {
    // 分块大小（教学用固定 32；一般应由 SRAM 容量和 d 动态推导）
    const int Bc = 32; const int Br = 32;
    const int B  = Q.size(0);   // batch
    const int nh = Q.size(1);   // num heads
    const int N  = Q.size(2);   // seq len
    const int d  = Q.size(3);   // head dim

    // 分块数量与缩放系数
    const int Tc = ceil((float) N / Bc);
    const int Tr = ceil((float) N / Br);
    const float softmax_scale = 1.0f / sqrt((float) d);

    // ---------- 在 HBM 上申请输出与状态量 ----------
    auto O = torch::zeros_like(Q);                  // 输出，形状/设备同 Q（在 GPU）
    auto L = torch::zeros({B, nh, N});              // 每行的指数和
    auto M = torch::full({B, nh, N}, -INFINITY);    // 每行的最大值
    torch::Device device(torch::kCUDA);
    L = L.to(device);                               // zeros/full 默认在 CPU，这里搬到 GPU
    M = M.to(device);

    // ---------- 计算每 block 需要的动态共享内存字节数 ----------
    // 布局：Qs[d*Br] + Ks[d*Bc] + Vs[d*Bc] + Ss[Bc*Br]
    const int sram_size = (d * Br + 2 * d * Bc + Bc * Br) * sizeof(float);
    int max_sram_size;
    cudaDeviceGetAttribute(&max_sram_size, cudaDevAttrMaxSharedMemoryPerBlock, 0);
    printf("Max shared memory: %d, requested shared memory: %d \n", max_sram_size, sram_size);

    // 动态共享内存默认上限 48KB，超过时需显式抬高（本 demo 在 d=128 时约 52KB）
    if (sram_size > 48 * 1024) {
        cudaFuncSetAttribute(my_forward_kernel,
                             cudaFuncAttributeMaxDynamicSharedMemorySize,
                             sram_size);
    }

    // ---------- 执行配置：grid=(batch, num_heads)，block=Bc 个线程 ----------
    dim3 grid_dim(B, nh);   // x=batch, y=head，共 B*nh 个 block，各自独立
    dim3 block_dim(Bc);     // 每个 block Bc 个线程（= 1 个 warp）

    // 三尖括号 = kernel 启动配置：<<<网格, 每块线程数, 每块动态共享内存字节数>>>
    my_forward_kernel<<<grid_dim, block_dim, sram_size>>>(
        Q.data_ptr<float>(), K.data_ptr<float>(), V.data_ptr<float>(),
        N, d, Tc, Tr, Bc, Br, softmax_scale,
        L.data_ptr<float>(), M.data_ptr<float>(), O.data_ptr<float>()
    );

    // 检查 kernel 启动是否出错
    cudaError_t err = cudaGetLastError();
    if (err != cudaSuccess) {
        printf("kernel launch failed: %s\n", cudaGetErrorString(err));
    }
    return O;
}
