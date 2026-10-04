// main.cpp —— 第08讲《CUDA 算子解析》配套：驱动 my_flash.cu 的测试入口
//
// 功能：
//   1) 构造随机 Q / K / V（形状 [B, nh, N, d]，放在 GPU 上）
//   2) 调用我们实现的 my_forward（FlashAttention 分块 + online softmax）
//   3) 与 PyTorch 参考实现（matmul → softmax → matmul）对比，打印最大误差与是否通过
//
// 编译运行见同目录 CMakeLists.txt。

#include <torch/torch.h>
#include <cuda_runtime.h>

#include <cmath>
#include <cstdio>

// 由 my_flash.cu 提供的 host 端算子
torch::Tensor my_forward(torch::Tensor Q, torch::Tensor K, torch::Tensor V);

// PyTorch 参考实现：Attention(Q,K,V) = softmax(Q·Kᵀ / √d) · V
torch::Tensor manual_attention(torch::Tensor Q, torch::Tensor K, torch::Tensor V) {
    auto d = Q.size(-1);
    auto att = torch::matmul(Q, K.transpose(-2, -1)) / std::sqrt((double) d);
    att = torch::softmax(att, /*dim=*/-1);
    return torch::matmul(att, V);
}

int main() {
    // 与视频演示一致的小模型参数
    const int B = 2, H = 8, N = 256, D = 128;

    // 固定随机种子，保证可复现
    torch::manual_seed(0);
    auto opts = torch::TensorOptions().dtype(torch::kFloat32).device(torch::kCUDA);

    auto Q = torch::rand({B, H, N, D}, opts);
    auto K = torch::rand({B, H, N, D}, opts);
    auto V = torch::rand({B, H, N, D}, opts);

    std::printf("Q/K/V shape = [%d, %d, %d, %d]\n", B, H, N, D);

    // 参考结果
    auto ref = manual_attention(Q, K, V);

    // 我们的实现
    auto out = my_forward(Q, K, V);

    // 等待 GPU 执行完毕，捕获可能的错误
    cudaError_t err = cudaDeviceSynchronize();
    if (err != cudaSuccess) {
        std::printf("CUDA error: %s\n", cudaGetErrorString(err));
        return 2;
    }

    // 对比数值
    auto diff = (out - ref).abs().max().item<float>();
    bool ok = torch::allclose(out, ref, /*rtol=*/1e-2, /*atol=*/1e-2);

    std::printf("max abs diff = %e\n", diff);
    std::printf("allclose(rtol=1e-2, atol=1e-2): %s\n", ok ? "PASS" : "FAIL");

    return ok ? 0 : 1;
}
