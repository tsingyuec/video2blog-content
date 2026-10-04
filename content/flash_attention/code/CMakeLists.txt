# CMakeLists.txt —— 第08讲《CUDA 算子解析》my_flash 工程
#
# 依赖：LibTorch（PyTorch C++ 发行版）+ CUDA Toolkit
# 用法：
#   mkdir build && cd build
#   cmake -DCMAKE_PREFIX_PATH=/path/to/libtorch ..
#   cmake --build . --config Release
#   ./my_flash
#
# 说明：LibTorch 的下载与 CMAKE_PREFIX_PATH 设置见第03讲（p=3）。

cmake_minimum_required(VERSION 3.18 FATAL_ERROR)

# 同时启用 C++ 与 CUDA（.cu 需要单独用 nvcc 编译）
project(my_flash LANGUAGES CXX CUDA)

# 目标 GPU 架构（按自己的显卡修改；89 = RTX 40 系 / Ada，86 = RTX 30 系，等）
if(NOT DEFINED CMAKE_CUDA_ARCHITECTURES)
    set(CMAKE_CUDA_ARCHITECTURES 89)
endif()

# 找到 LibTorch。若未自动找到，请用 -DCMAKE_PREFIX_PATH=/path/to/libtorch 指定
find_package(Torch REQUIRED)

# 统一 C++ / CUDA 标准（LibTorch 要求 C++17）
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CUDA_STANDARD 17)
set(CMAKE_CUDA_STANDARD_REQUIRED ON)

# 可执行文件：main.cpp + flash.cu
add_executable(my_flash
    main.cpp
    flash.cu
)

# 链接 LibTorch（会一并带上它的头文件目录与库）
target_link_libraries(my_flash PRIVATE "${TORCH_LIBRARIES}")

# LibTorch 的编译选项（含 ABI 宏，如 _GLIBCXX_USE_CXX11_ABI），
# 必须同时用于 C++ 与 CUDA 源文件，否则会链接不上
target_compile_options(my_flash PRIVATE
    $<$<COMPILE_LANGUAGE:CXX>:${TORCH_CXX_FLAGS}>
    $<$<COMPILE_LANGUAGE:CUDA>:${TORCH_CXX_FLAGS}>
)
