# S03 容器隔离、镜像、运行时与网络

编号：S03 · 类型：系统专题 · 目录规模：105 个小节（三级叶子节点）。

> 博客已从 `content/容器技术` 迁入对应小节子目录，状态更新为 `[DONE]`。

## 脉络章程

**知识主线**：从 Linux 进程、文件系统、权限与网络栈出发，经过 namespace/cgroup/capability、镜像规范、构建、写时复制与存储，到容器运行时（OCI/containerd/CRI），最后进入容器网络数据面（netns/veth、bridge/iptables、eBPF），理解容器“看起来像一台机器”的完整生命周期。

**一句话范围**：不展开网络排障（归杂项）；聚焦隔离、限制、镜像、存储、运行时与网络数据面。

**学习入口 → 学习出口**：Linux 命令行、进程与文件系统基础 → 能解释容器与虚拟机的差别，能读懂镜像层、挂载、cgroup 限制、常见存储问题、运行时链路与单机容器网络数据面。

**完整问题链**：
1. Linux 系统基础
2. 隔离、限制与行为约束
3. 镜像、文件系统与供应链
4. 容器存储基础
5. 容器运行时
6. 容器网络数据面

**与相邻脉络的关系**：Linux 命令行、进程与文件系统基础；网络排障见杂项；集群 CNI/Service 见 S04。

## 目录

<a id="s03-1"></a>
## 1 Linux 系统基础

<a id="s03-1-1"></a>
### 1.1 进程与执行模型

- 1.1.1 fork/exec 与进程创建 <a id="s03-1-1-1"></a> [DONE]
- 1.1.2 PID 1、init 进程与进程树 <a id="s03-1-1-2"></a> [DONE]
- 1.1.3 孤儿进程、僵尸进程与回收 <a id="s03-1-1-3"></a> [DONE]
- 1.1.4 系统调用与内核态/用户态边界 <a id="s03-1-1-4"></a> [DONE]

<a id="s03-1-2"></a>
### 1.2 文件系统与挂载

- 1.2.1 文件系统、inode 与文件描述符 <a id="s03-1-2-1"></a> [DONE]
- 1.2.2 mount 与挂载命名空间 <a id="s03-1-2-2"></a> [DONE]
- 1.2.3 pivot_root 与 chroot <a id="s03-1-2-3"></a> [DONE]
- 1.2.4 /proc、/sys 与内核暴露接口 <a id="s03-1-2-4"></a> [DONE]

<a id="s03-1-3"></a>
### 1.3 用户与权限

- 1.3.1 UID/GID 与进程凭证 <a id="s03-1-3-1"></a> [DONE]
- 1.3.2 setuid/setgid 与权限提升 <a id="s03-1-3-2"></a> [DONE]
- 1.3.3 文件 capability <a id="s03-1-3-3"></a> [DONE]

<a id="s03-1-4"></a>
### 1.4 网络栈基础

- 1.4.1 网卡、网桥与链路层 <a id="s03-1-4-1"></a> [DONE]
- 1.4.2 路由表与 ARP <a id="s03-1-4-2"></a> [DONE]
- 1.4.3 netfilter 钩子与包处理路径 <a id="s03-1-4-3"></a> [DONE]
- 1.4.4 socket、连接与连接跟踪基础 <a id="s03-1-4-4"></a> [DONE]
- 1.4.5 网络命名空间与网络设备的关系 <a id="s03-1-4-5"></a> [DONE]

<a id="s03-1-5"></a>
### 1.5 资源限制与系统服务

- 1.5.1 rlimit/ulimit 与进程级资源限制 <a id="s03-1-5-1"></a> [DONE]
- 1.5.2 systemd 对 cgroup 的管理 <a id="s03-1-5-2"></a> [DONE]
- 1.5.3 根 cgroup 与容器管理器的边界 <a id="s03-1-5-3"></a> [DONE]
- 1.5.4 日志与 journald 基础 <a id="s03-1-5-4"></a> [DONE]

<a id="s03-2"></a>
## 2 隔离、限制与行为约束

<a id="s03-2-1"></a>
### 2.1 命名空间

- 2.1.1 命名空间的概念与作用 <a id="s03-2-1-1"></a> [DONE]
- 2.1.2 PID 命名空间 <a id="s03-2-1-2"></a> [DONE]
- 2.1.3 网络命名空间 <a id="s03-2-1-3"></a> [DONE]
- 2.1.4 挂载命名空间 <a id="s03-2-1-4"></a> [DONE]
- 2.1.5 UTS 与 IPC 命名空间 <a id="s03-2-1-5"></a> [DONE]
- 2.1.6 用户命名空间 <a id="s03-2-1-6"></a> [DONE]
- 2.1.7 Cgroup 命名空间 <a id="s03-2-1-7"></a> [DONE]
- 2.1.8 时间命名空间 <a id="s03-2-1-8"></a> [DONE]
- 2.1.9 namespace 系统调用接口：clone/unshare/setns <a id="s03-2-1-9"></a> [DONE]

<a id="s03-2-2"></a>
### 2.2 控制组

- 2.2.1 cgroup 的职责：限制与记帐 <a id="s03-2-2-1"></a> [DONE]
- 2.2.2 cgroup v1 与 v2 的架构差异 <a id="s03-2-2-2"></a> [DONE]
- 2.2.3 CPU 子系统 <a id="s03-2-2-3"></a> [DONE]
- 2.2.4 内存子系统 <a id="s03-2-2-4"></a> [DONE]
- 2.2.5 IO 子系统 <a id="s03-2-2-5"></a> [DONE]
- 2.2.6 PIDs 子系统 <a id="s03-2-2-6"></a> [DONE]
- 2.2.7 cgroup 与容器资源限制的映射 <a id="s03-2-2-7"></a> [DONE]
- 2.2.8 cgroup 文件系统接口与 systemd 委托 <a id="s03-2-2-8"></a> [DONE]

<a id="s03-2-3"></a>
### 2.3 权限与行为约束

- 2.3.1 Linux Capabilities <a id="s03-2-3-1"></a> [DONE]
- 2.3.2 Seccomp 系统调用过滤 <a id="s03-2-3-2"></a> [DONE]
- 2.3.3 AppArmor <a id="s03-2-3-3"></a> [DONE]
- 2.3.4 SELinux <a id="s03-2-3-4"></a> [DONE]
- 2.3.5 no_new_privs 与权限提升约束 <a id="s03-2-3-5"></a> [DONE]
- 2.3.6 容器进程模型 <a id="s03-2-3-6"></a> [DONE]
- 2.3.7 隔离、限制与约束三者的关系 <a id="s03-2-3-7"></a> [DONE]

<a id="s03-3"></a>
## 3 镜像、文件系统与供应链

<a id="s03-3-1"></a>
### 3.1 镜像规范与结构

- 3.1.1 OCI 镜像规范 <a id="s03-3-1-1"></a> [DONE]
- 3.1.2 镜像分层模型 <a id="s03-3-1-2"></a> [DONE]
- 3.1.3 manifest、config 与 layer <a id="s03-3-1-3"></a> [DONE]
- 3.1.4 tag 与 digest <a id="s03-3-1-4"></a> [DONE]
- 3.1.5 镜像仓库与分发基础 <a id="s03-3-1-5"></a> [DONE]

<a id="s03-3-2"></a>
### 3.2 镜像构建

- 3.2.1 Dockerfile 与构建上下文 <a id="s03-3-2-1"></a> [DONE]
- 3.2.2 镜像构建与分层缓存 <a id="s03-3-2-2"></a> [DONE]
- 3.2.3 多阶段构建 <a id="s03-3-2-3"></a> [DONE]
- 3.2.4 BuildKit 与 Buildx <a id="s03-3-2-4"></a> [DONE]

<a id="s03-3-3"></a>
### 3.3 文件系统与写时复制

- 3.3.1 联合文件系统 <a id="s03-3-3-1"></a> [DONE]
- 3.3.2 OverlayFS 结构 <a id="s03-3-3-2"></a> [DONE]
- 3.3.3 写时复制机制 <a id="s03-3-3-3"></a> [DONE]
- 3.3.4 存储驱动 <a id="s03-3-3-4"></a> [DONE]
- 3.3.5 容器可写层 <a id="s03-3-3-5"></a> [DONE]
- 3.3.6 容器 rootfs 与挂载布局 <a id="s03-3-3-6"></a> [DONE]

<a id="s03-3-4"></a>
### 3.4 镜像供应链

- 3.4.1 SBOM <a id="s03-3-4-1"></a> [DONE]
- 3.4.2 构建来源证明 <a id="s03-3-4-2"></a> [DONE]
- 3.4.3 镜像签名与验证 <a id="s03-3-4-3"></a> [DONE]
- 3.4.4 镜像扫描 <a id="s03-3-4-4"></a> [DONE]

<a id="s03-4"></a>
## 4 容器存储基础

<a id="s03-4-1"></a>
### 4.1 容器卷

- 4.1.1 卷的模型与生命周期 <a id="s03-4-1-1"></a> [DONE]
- 4.1.2 匿名卷与命名卷 <a id="s03-4-1-2"></a> [DONE]
- 4.1.3 卷驱动基础 <a id="s03-4-1-3"></a> [DONE]

<a id="s03-4-2"></a>
### 4.2 绑定挂载

- 4.2.1 绑定挂载模型 <a id="s03-4-2-1"></a> [DONE]
- 4.2.2 挂载传播 <a id="s03-4-2-2"></a> [DONE]
- 4.2.3 只读挂载与权限 <a id="s03-4-2-3"></a> [DONE]

<a id="s03-4-3"></a>
### 4.3 容器可写层与数据生命周期

- 4.3.1 可写层与容器生命周期 <a id="s03-4-3-1"></a> [DONE]
- 4.3.2 临时文件系统 tmpfs <a id="s03-4-3-2"></a> [DONE]
- 4.3.3 数据持久化边界 <a id="s03-4-3-3"></a> [DONE]
- 4.3.4 数据备份与迁移基础 <a id="s03-4-3-4"></a> [DONE]

<a id="s03-4-4"></a>
### 4.4 容器存储排障基础

- 4.4.1 挂载与权限排查 <a id="s03-4-4-1"></a> [DONE]
- 4.4.2 卷生命周期排查 <a id="s03-4-4-2"></a> [DONE]
- 4.4.3 常见存储故障模式 <a id="s03-4-4-3"></a> [DONE]

<a id="s03-5"></a>
## 5 容器运行时

<a id="s03-5-1"></a>
### 5.1 运行时规范

- 5.1.1 OCI Runtime Spec <a id="s03-5-1-1"></a> [DONE]
- 5.1.2 容器生命周期 <a id="s03-5-1-2"></a> [DONE]
- 5.1.3 runc <a id="s03-5-1-3"></a> [DONE]
- 5.1.4 runc 创建容器的内核调用流程 <a id="s03-5-1-4"></a> [DONE]

<a id="s03-5-2"></a>
### 5.2 运行时架构

- 5.2.1 Docker 架构 <a id="s03-5-2-1"></a> [DONE]
- 5.2.2 containerd 架构 <a id="s03-5-2-2"></a> [DONE]
- 5.2.3 containerd-shim <a id="s03-5-2-3"></a> [DONE]
- 5.2.4 snapshotter 与镜像解包 <a id="s03-5-2-4"></a> [DONE]
- 5.2.5 容器日志与标准流基础 <a id="s03-5-2-5"></a> [DONE]

<a id="s03-5-3"></a>
### 5.3 运行时接口与隔离模式

- 5.3.1 CRI 容器运行时接口基础 <a id="s03-5-3-1"></a> [DONE]
- 5.3.2 Pod sandbox 概念 <a id="s03-5-3-2"></a> [DONE]
- 5.3.3 Rootless 容器 <a id="s03-5-3-3"></a> [DONE]
- 5.3.4 用户命名空间与运行时隔离 <a id="s03-5-3-4"></a> [DONE]

<a id="s03-6"></a>
## 6 单机容器网络与 Linux 数据面

<a id="s03-6-1"></a>
### 6.1 单机容器网络

- 6.1.1 网络命名空间与 veth pair <a id="s03-6-1-1"></a> [DONE]
  - 学习目标：说明 netns 与 veth pair 如何把容器接到宿主机，画出两端接口。
- 6.1.2 网桥与 docker0 <a id="s03-6-1-2"></a> [DONE]
  - 学习目标：说明 docker0 网桥的转发与地址分配。
- 6.1.3 Docker 网络模式：bridge、host、none、container <a id="s03-6-1-3"></a> [DONE]
  - 学习目标：比较 bridge/host/none/container 四种网络模式的隔离与连通性。
- 6.1.4 端口映射与 NAT <a id="s03-6-1-4"></a> [DONE]
  - 学习目标：解释端口映射的 DNAT 规则与访问路径。
- 6.1.5 容器 DNS、/etc/hosts 与 resolv.conf <a id="s03-6-1-5"></a> [DONE]
  - 学习目标：说明容器 DNS 解析顺序与 /etc/hosts、resolv.conf 的来源。
- 6.1.6 veth 与 netns 的创建、销毁和生命周期 <a id="s03-6-1-6"></a> [DONE]
  - 学习目标：描述 veth/netns 的创建、销毁与生命周期。

<a id="s03-6-2"></a>
### 6.2 传统 Linux 数据面

- 6.2.1 iptables 表链结构与规则语义 <a id="s03-6-2-1"></a> [DONE]
  - 学习目标：说明 iptables 表/链/规则的匹配顺序。
- 6.2.2 nftables 与 iptables 的关系 <a id="s03-6-2-2"></a> [DONE]
  - 学习目标：说明 nftables 与 iptables 的关系及迁移差异。
- 6.2.3 NAT、DNAT、SNAT 与连接跟踪 <a id="s03-6-2-3"></a> [DONE]
  - 学习目标：区分 NAT/DNAT/SNAT，说明 conntrack 如何记录连接。
- 6.2.4 IPVS <a id="s03-6-2-4"></a> [DONE]
  - 学习目标：说明 IPVS 的负载均衡模式与容器场景。
- 6.2.5 路由、ARP、MTU 与分片 <a id="s03-6-2-5"></a> [DONE]
  - 学习目标：说明路由、ARP、MTU 与分片在包路径中的作用。

<a id="s03-6-3"></a>
### 6.3 eBPF 与现代单机数据面

- 6.3.1 eBPF 基础：程序类型、验证器、map <a id="s03-6-3-1"></a> [DONE]
  - 学习目标：说明 eBPF 程序类型、验证器与 map 的作用。
- 6.3.2 XDP 与 tc <a id="s03-6-3-2"></a> [DONE]
  - 学习目标：区分 XDP 与 tc 的挂载点和适用场景。
- 6.3.3 cgroup eBPF 与容器资源/网络约束 <a id="s03-6-3-3"></a> [DONE]
  - 学习目标：说明 cgroup eBPF 如何约束容器资源与网络。
- 6.3.4 eBPF 与容器网络、安全、可观测性的关系 <a id="s03-6-3-4"></a> [DONE]
  - 学习目标：说明 eBPF 在容器网络、安全、可观测性中的角色。
- 6.3.5 eBPF 与传统 iptables/IPVS 数据面的对比 <a id="s03-6-3-5"></a> [DONE]
  - 学习目标：比较 eBPF 与 iptables/IPVS 数据面的优劣。

<a id="s03-6-4"></a>

## 学习出口

能解释容器与虚拟机的差别，能读懂镜像层、挂载、cgroup 限制、常见存储问题、OCI/containerd/CRI 的运行时链路，以及 netns/veth、bridge/iptables、eBPF 的单机网络数据面。

## 导航

[返回分类目录](../README.md) · [知识总目录](../../../README.md)
