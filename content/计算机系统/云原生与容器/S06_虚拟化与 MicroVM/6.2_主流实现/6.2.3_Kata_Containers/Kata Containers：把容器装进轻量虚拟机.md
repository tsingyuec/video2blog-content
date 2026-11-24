# Kata Containers：把容器装进轻量虚拟机

> 视频来源：[Kata Containers An introduction and overview](https://www.youtube.com/watch?v=4gmLXyMeYWI)（YouTube · OpenInfra Foundation，讲者 Graham Whaley，Intel 开源技术中心）｜时长约 32 分钟
> 导读：这是一场 2018 年 Kata 1.3 时期的项目综述，讲者按"是什么 → 为什么 → 架构 → 网络与存储 → 代价 → 路线图"的顺序讲完，正好覆盖"容器接口 + 虚拟机隔离"这条路的全貌。文中的版本号、组件名与数字都来自讲者当时的说法。

## 本讲要解决的核心问题（SCQA）

**背景**：容器用起来很顺手——镜像分层、部署简单、工具链齐全，Kubernetes 和 Docker 那套东西拿来就用。它的隔离靠的是宿主机内核上的 namespace、cgroup 和 capability 这些软件机制。

**冲突**：软件隔离"很好，但没有什么是完美的"。讲者说得很直白：确实发生过从容器里逃出来的事，一旦有人逃出来，他就能碰到同一台机器上的其他容器，甚至打进宿主内核。

**疑问**：那能不能给容器套一层虚拟机的硬件边界，同时又不要传统虚拟机那份臃肿和启动时间？

**回答（中心思想）**：Kata Containers 的做法是**把每个容器（或每个 Pod）装进一台轻量虚拟机里**，对外仍然是一个 OCI 兼容、能被 CRI 调用的运行时。容器自己不知道它在一台虚拟机里；代价则落在几处具体的地方：每个容器一份客户机内核、约 50MB 的内存占用、接近一秒的启动时间，以及网络与存储必须额外做一层"虚拟机适配"。

![速度与安全之间的权衡：虚拟机器在左上方（隔离强、速度慢），容器在右下方（速度快、隔离弱），Kata 想落在两者之间](assets/Kata%20Containers：把容器装进轻量虚拟机/00099.webp)

[【跳转到 01:39】](https://www.youtube.com/watch?v=4gmLXyMeYWI&t=99)

## 一、Kata 的目标：容器接口不变，隔离边界换成虚拟机

### 1.1 传统容器与 Kata 的差别只在"内核归谁"

讲者用两张手绘图把区别讲清楚了。传统容器是这样：三个进程各自待在自己的 namespace 里，下面**共用同一个 Linux 内核**，再往下是 CPU、内存、网络、存储这些被切分共享的硬件资源。

![传统容器：多个进程各有 namespace，但共用宿主机上的同一个 Linux 内核，硬件资源被切分共享](assets/Kata%20Containers：把容器装进轻量虚拟机/00324.webp)

[【跳转到 05:24】](https://www.youtube.com/watch?v=4gmLXyMeYWI&t=324)

Kata 则把每个进程（严格说是每个容器或 Pod）放进一台独立的虚拟机：每台虚拟机里都有自己的 namespace、**自己的客户机内核**，再通过硬件虚拟化落到宿主机的 Linux 内核上。

![Kata Containers：每个容器一台虚拟机，各自带一份客户机内核，靠硬件虚拟化与宿主机隔开](assets/Kata%20Containers：把容器装进轻量虚拟机/00374.webp)

[【跳转到 06:14】](https://www.youtube.com/watch?v=4gmLXyMeYWI&t=374)

这一步带来的直接后果是：**逃逸的收益变了**。在共享内核的模型里，攻破容器边界约等于摸到了宿主内核，也就摸到了同机所有容器；在 Kata 里，攻击者先得攻破一台虚拟机，而虚拟机的边界由硬件虚拟化支撑。讲者反复强调"我们是虚拟机，所以总会有虚拟化损耗，除非耍点小技巧，这份损耗大概永远不会消失"——收益和代价是绑在一起的。

### 1.2 对外它就是一个 OCI 运行时，可以和 runc 并排装

这是 Kata 最容易被误解的地方：它不是"另一套容器平台"，而是**把 runc 那个位置换掉**。讲者的原话是，从使用者角度看它"看起来就像 runc"：OCI 兼容，你甚至可以把 runc 换掉、改个名字插进栈里它也能跑（他补了一句"那样有点野"）。

![Kata 的集成方式：OCI、Kubernetes/CRI、Docker、OpenStack 都能驱动它，定位是"OCI 兼容的 VM 运行时"](assets/Kata%20Containers：把容器装进轻量虚拟机/00174.webp)

[【跳转到 02:54】](https://www.youtube.com/watch?v=4gmLXyMeYWI&t=174)

关键在于**并存**而不是替代：

- 同一个集群里，一部分 Pod 用 runc（信任、要速度），另一部分用 Kata（不信任、要隔离）；
- 可以按 Pod、按容器在配置文件里指定，也可以直接把默认运行时设成 Kata；
- 上层工具不变——滚动发布、监控这些 Kubernetes 和 Docker 的既有工具照旧用。

### 1.3 它是两个项目的合并产物

讲者顺带讲了历史：Kata 之前有 Clear Containers，Hyper 那边有 runV，两边在同一个会议上发现"我们讲的其实是同一件事"，一年后合并进 OpenStack 基金会。版本节奏是 v1.0（2018 年 5 月 22 日）、v1.3.1（2018 年 10 月 22 日），当时正在推 1.4。

![项目历史：OpenStack 基金会托管，由 2015 年起步的 Hyper.sh runV 与 Intel Clear Containers 合并而来，v1.0 于 2018 年 5 月发布](assets/Kata%20Containers：把容器装进轻量虚拟机/00299.webp)

[【跳转到 04:09】](https://www.youtube.com/watch?v=4gmLXyMeYWI&t=249)

## 二、一次容器启动，多出了哪些部件

### 2.1 组件清单：从 QEMU 到 agent

讲者列出的基本组件是七项：QEMU 包、runtime、kernel、rootfs image、agent、shim、proxy。

![Kata 的基本组件：QEMU 包、runtime、kernel、rootfs image、agent、shim、proxy](assets/Kata%20Containers：把容器装进轻量虚拟机/00499.webp)

[【跳转到 08:19】](https://www.youtube.com/watch?v=4gmLXyMeYWI&t=499)

逐项对应到职责：

| 组件 | 讲者的说法 | 为什么需要它 |
| --- | --- | --- |
| QEMU 包 | 开箱即用，用 QEMU 作为虚拟机栈 | 真正去创建和运行那台虚拟机 |
| runtime（kata-runtime） | 相当于 Docker 下面的 runc，名字可以改 | 接收 OCI 命令与 spec，把容器"建"出来 |
| kernel | 每台虚拟机一份，可以按 Pod 裁剪 | 客户机要能启动，且可以按需选内核特性 |
| rootfs image | 一个很小的根文件系统 | 虚拟机总得先启动点什么，容器里的东西不够启动一台机器 |
| agent | 真正干活的那个 | 在虚拟机内部配挂载点、网络、内存、cgroup |
| shim | 在虚拟机那一侧做 I/O，并对外翻译状态 | 上层要监控"容器还在不在"，但不能直接看虚拟机里的进程 |
| proxy | 正在被淘汰 | 早期用来做宿主与客户机之间的转发，现在被 vsock 取代 |

### 2.2 架构图：一条 gRPC 越过 vsock 进到客户机

这张图是全篇的核心。左边是 Docker、Kubernetes、CRI 这些上层；它们分两路走：**I/O 那一路连到 shim**，**OCI 命令与 spec 那一路连到 runtime**。runtime 通过 gRPC 穿过 vsock，进到虚拟机里的 agent；agent 再往下操作客户机内核，最终在虚拟机里跑出容器进程。

![Kata 基本架构：上层经 shim（I/O）与 runtime（OCI 命令/spec）两路进入，runtime 用 gRPC over vsock 与虚拟机内的 agent 通信](assets/Kata%20Containers：把容器装进轻量虚拟机/00574.webp)

[【跳转到 09:34】](https://www.youtube.com/watch?v=4gmLXyMeYWI&t=574)

几个容易忽略的细节：

- **agent 在容器的 namespace 之外**。它必须站在容器外面，才能去配置这个容器。
- **runtime 是短暂进程**。`docker run` 或 Kubernetes 拉起容器时，运行时负责把东西建好就退出，不常驻——这一点和 runc 一样。
- **shim 是那个常驻的"替身"**。上层（比如 Docker）需要盯一个进程来判断容器是否还活着、要统计信息。传统做法是盯容器进程本身，但 Kata 做不到；默认退化成盯 QEMU 也不对（"哦，我只有一个 QEMU"拿不到想要的信息）。所以 shim 站在虚拟机那一侧做 I/O，把虚拟机里的信息翻译出来——你问一个问题，它告诉你你其实该问什么。
- **proxy 已经让位给 vsock**。vsock 是相对较新的内核特性，有了它，宿主和客户机之间的通道不再需要 proxy 这个中间角色。

## 三、接入 Kubernetes：Kubelet 之下多了一条 kata-runtime 分支

讲者给的接入图非常直白：Kubelet 调 CRI，CRI 之下是 CRI-O 或 containerd，再往下分叉——一路是 runc，直接起 Pod；另一路是 kata-runtime，起的是**一台虚拟机，虚拟机里才是 Pod**。

![CRI-O 与 Kata：Kubelet → CRI → CRI-O/containerd 之后分成 runc 与 kata-runtime 两条路，后者把 Pod 放进 VM](assets/Kata%20Containers：把容器装进轻量虚拟机/00724.webp)

[【跳转到 12:04】](https://www.youtube.com/watch?v=4gmLXyMeYWI&t=724)

这条路并不是天然通的。讲者说，容器刚出现时根本没有"VM 容器"这个概念，规范和实现里到处是对 VM 不友好、甚至反 VM 的假设——"就像在代码库中间硬写死了 runc"。所以项目花了大量时间和 OCI、CRI 社区一起改，确保后来的实现能容纳虚拟机。这也解释了为什么 Kata 强调"我们是 OCI 兼容的"：兼容性不是宣传语，而是它能不能被 CRI 调起来的入场券。

## 四、网络：容器在 L3，虚拟机在 L2，中间要搭一座桥

### 4.1 默认路径：veth → MACVTAP → TAP → 虚拟机

容器网络基本跑在 L3，虚拟机网络传统上跑在 L2，所以**不能把容器网络直接插进虚拟机**。Kata 的默认做法是在中间加一层转换：

![Kata 的基础网络路径：K8s overlay 网络经 veth pair 接到 MACVTAP，再由 TAP 设备进入虚拟机](assets/Kata%20Containers：把容器装进轻量虚拟机/00824.webp)

[【跳转到 13:44】](https://www.youtube.com/watch?v=4gmLXyMeYWI&t=824)

讲者的经验值是：开箱即用的情况下，90% 的场景这样就能工作——"你把它插进去，网络就出现了，魔法发生，容器里就有了网络"。

后来他们把默认实现换成了 **TC mirroring**（用 tc 做流量镜像/重定向）：兼容性更好，性能代价很小。这类改动都留了开关——Kata 有一个很大的 TOML 配置文件，默认用新路径，但你可以退回去。

![网络相关的改动清单：TC Mirroring、优化默认路径、Docker Swarm DNS、enlightened CNI 插件](assets/Kata%20Containers：把容器装进轻量虚拟机/01274.webp)

[【跳转到 21:14】](https://www.youtube.com/watch?v=4gmLXyMeYWI&t=1274)

### 4.2 高性能路径：把加速栈直接插进虚拟机

如果默认路径不够快，Kata 允许把加速网络栈直接接到虚拟机上。讲者举的例子是 DPDK，图上画的是 DPDK、VPP、OVS 这些用户态网络组件通过 **vhost-user socket** 直接连进虚拟机，从而绕开 TAP 那一层和额外的二三层转换。

![Kata 的 vhost-user 网络：DPDK、VPP、OVS 等用户态交换组件通过 vhost-user socket 直接接入虚拟机，绕开 TAP](assets/Kata%20Containers：把容器装进轻量虚拟机/00874.webp)

[【跳转到 14:34】](https://www.youtube.com/watch?v=4gmLXyMeYWI&t=874)

再往上一档是硬件：Kata 支持网卡直通，可以把整块物理网卡，或者虚拟化出来的 SR-IOV 网卡，直接分配给虚拟机。讲者的定位很清楚——这些是"中高端容器用户"才会用的路径。

### 4.3 生态适配的两个坑

- **CNI 拿不到虚拟机上下文**。写 CNI 插件的人知道对面是虚拟机的网络栈、知道有个优化该做，但默认没有通道把信息传给 Kata。后来加了"enlightened CNI plugins"：可以在 CNI 配置里写提示或属性，一路传到 Kata，由它调整。讲者补了一句很实在的话——插件不支持这些参数时系统仍然能用，只是不够优。
- **Docker Swarm 的 DNS**。Swarm 会建自己的 DNS 控制器，这在 Kata 的网络侧造成过问题，当时"觉得已经有解法了"。

## 五、存储：rootfs 怎么进客户机，决定了启动有多快

### 5.1 四种后端，四条进虚拟机的路

这张表把"宿主侧用什么存储后端"和"用什么方式送进虚拟机"对应了起来：

![Kata 的存储路径：overlay 走 9pfs，device mapper 走块设备直通，镜像文件走 NVDIMM/DAX，Ceph/Gluster 走网络](assets/Kata%20Containers：把容器装进轻量虚拟机/00924.webp)

[【跳转到 15:24】](https://www.youtube.com/watch?v=4gmLXyMeYWI&t=924)

| 宿主侧后端 | 进虚拟机的方式 | 讲者的评价 |
| --- | --- | --- |
| overlay | 9pfs | 简单、插上就能用，但**不是完整的 POSIX 文件系统**，偶发小异常 |
| device mapper | 块设备直接映射进虚拟机再挂载 | "快得多"，是他偏好的方式，因为不走网络 |
| 镜像文件 | NVDIMM + DAX 直接映射 | 省启动时间，也省内存与缓存占用 |
| Ceph、Gluster 等 | 网络存储 | 按预期工作，配进容器即可 |

9p 的问题是语义层面的：它"大体能用"，但偶尔某个容器做某件奇怪的事就是不行，追下去发现是 9p 的问题。块设备则绕开了这层：找到呈现给宿主的块设备，直接映射进虚拟机挂载，既有完整文件系统，又不走网络连接。

### 5.2 DAX：把 rootfs 一对一映射进客户机内存

讲者特别讲了 NVDIMM 这条路：Kata 用一个模拟的非易失内存设备，通过 DAX 把 rootfs **一对一映射进虚拟机内存**，绕过所有缓存。收益有两块——启动更快，内存和缓存占用更小。同样的能力也能给用户用（把固定镜像映射进容器），只是当时还没见到客户真这么用。

### 5.3 virtio-fs：9p 的接替者

讲者明确说 9p 不是理想方案，他们看过 NFS over vsock（能用，可能比 9p 稍好，但有它自己的坑），而真正期待的是另一个小组在做的东西：**virtio-fs**——基础是在 vsock 上跑一个 FUSE 文件系统，能给出兼容性好得多的文件系统、更干净更快的传输。他的判断是：如果它像看起来那样能成，默认方案会从 9pfs 换过去。

![文件系统（卷）方向：Virtio-FS（vsock/FUSE）、NFS-vsock、缓存开关](assets/Kata%20Containers：把容器装进轻量虚拟机/01424.webp)

[【跳转到 23:19】](https://www.youtube.com/watch?v=4gmLXyMeYWI&t=1399)

### 5.4 缓存变成了两层，这是虚拟化带来的新麻烦

讲者说他有大量时间花在跑指标、找热点上，然后发现一个虚拟机特有的问题：客户机里有 page cache，这些页又通过 QEMU 映射到宿主，宿主那边有时也开了缓存。两种结果：

- **好的一面**：宿主上多个容器共享同一份缓存，同时各自还有本地一份，命中率很高；
- **坏的一面**：只是在重复数据——多穿一层所以稍慢，数据存两份所以稍大。

所以配置里要加开关，让你说清楚在哪一层做文件系统缓存，而不是两边都做。

## 六、代价落在哪里：启动、内存、设备与安全层

### 6.1 启动与内存：低于一秒、每容器约 50MB

这是全篇最具体的两个数字：

- **启动**：可以启动进 QEMU，"远低于一秒"，而 runc 也没比这快多少；
- **内存**：每容器大约 50MB。作为对比，传统 KVM/QEMU"随便就能堆出更大的占用"。

讲者把 50MB 这个量级归功于几处优化，其中最显眼的就是上面说的 DAX 直接映射 rootfs——省下的不只是内存，还有缓存占用。

### 6.2 设备与特权：privileged 模式基本无解

Docker 的 `--privileged` 意思是"把整台宿主都给我"，而 Kata 是在一台虚拟机里跑——讲者的反问是"你觉得这怎么可能工作呢"。他们确实支持其中一部分能力（比如设备直通），但明确说 privileged 模式在 Kata 里可能永远不会完全可用。这是一个结构性限制：隔离边界换来的，就是这类"要摸到真硬件"的需求会打折。

### 6.3 安全层只能选一边，不能两边都堆

Kata 里有个反复出现的争论：seccomp 到底套在虚拟机里的容器上，还是套在宿主上的 QEMU 外面？讲者的原则是**选一边**，而不是两边都做一层。理由是"安全像洋葱，是一层一层的"，每层都有内存和速度的代价。

![安全与隔离的分层：容器内做 seccomp；宿主侧做 cgroup 隔离、更多 namespace 隔离、rootless QEMU、SELinux 策略](assets/Kata%20Containers：把容器装进轻量虚拟机/01124.webp)

[【跳转到 18:44】](https://www.youtube.com/watch?v=4gmLXyMeYWI&t=1124)

当时的进展是：容器里加了 seccomp（希望当周合并）；虚拟机里用的还是和 runc 相同的库，所以虚拟机内部依然是一个 runc 风格的容器；宿主侧则加 cgroup 隔离、更多 namespace 隔离，并计划把运行时放进网络 namespace 以实现 rootless QEMU，以及给宿主上的 QEMU 写 SELinux 策略。

### 6.4 运维与扩展性上的代价

- **热升级**：发布节奏激进，但不能让用户"全部关掉重装"，所以热升级是关键特性。
- **更多 hypervisor**：默认是 QEMU，项目想支持更多。Kata 里有一个专门做这层抽象的库叫 **virtcontainers**，设计上就是让你能插进几乎任何东西，尤其是 hypervisor。这也解释了为什么"换 VMM 后端"在 Kata 里是配置问题而不是重写问题。
- **非 Linux 负载**：立刻的答案是"现在还不行"，但"应该不会太难"——第一步只需把 agent 移植到目标操作系统，因为 agent 是宿主与客户机之间唯一必须存在的对话方。而这恰恰是 Kata 相对软件容器的一大优势：**有独立内核，理论上可以跑不同操作系统的容器，还能混跑**。

![路线图：热升级、更多设备映射、更多 hypervisor、非 Linux 负载，以及始终在权衡的体积与速度](assets/Kata%20Containers：把容器装进轻量虚拟机/01574.webp)

[【跳转到 25:49】](https://www.youtube.com/watch?v=4gmLXyMeYWI&t=1549)

## 七、什么时候该选 Kata

把讲者的说法收拢成一张判断表：

| 你的情况 | 更适合的选择 | 原因 |
| --- | --- | --- |
| 多租户、跑不可信代码 | Kata | 每租户一台虚拟机，不必靠"把 Pod 分散到不同节点"来隔离 |
| 需要按容器定制内核 | Kata | 每台虚拟机可以有自己的内核，按 Pod 裁剪 |
| 追求极致密度、单机塞尽可能多的容器 | runc | 每容器一份客户机内核与约 50MB 固定开销 |
| 需要 `--privileged` 或大量设备直通 | runc 或专门的直通方案 | privileged 在 Kata 里可能永远无法完全可用 |
| 已有 Kubernetes/Docker 栈，只想换隔离层 | Kata | OCI/CRI 兼容，可与 runc 按 Pod 并存 |

讲者还提到多租户这个动机：传统容器栈里，你经常要靠"每客户一台虚拟机"来避免吵闹邻居；Kata 把这个"每客户一台虚拟机"直接做进了运行时本身，所以你不必先管一台虚拟机、再管虚拟机里的容器栈。

## 小结

- Kata 的定位是"**OCI 兼容的 VM 运行时**"：把 runc 那个位置换掉，容器接口不变，隔离边界从 namespace 换成虚拟机。
- 一个容器 = 一台轻量虚拟机，虚拟机里有自己的内核、自己的 rootfs、一个跑在容器 namespace 之外的 agent。
- 数据面靠两条通道：runtime 用 gRPC over vsock 指挥 agent；shim 常驻在虚拟机一侧做 I/O 并翻译监控信息。proxy 已被 vsock 取代。
- 网络要跨越"容器 L3 / 虚拟机 L2"的落差：默认 veth → MACVTAP → TAP，后来改成 TC mirroring；高性能场景用 vhost-user 直连 DPDK/VPP/OVS，或 SR-IOV 直通。
- 存储按宿主后端分四条路：overlay 走 9pfs、device mapper 走块设备直通、镜像文件走 NVDIMM/DAX、Ceph 走网络；9p 不是完整 POSIX，virtio-fs 是接替者。
- 代价是可量化的：启动远低于一秒、每容器约 50MB、privileged 模式基本不可用、安全层只能选一边堆。
- 换 VMM 后端是配置问题：virtcontainers 这层抽象让 QEMU 之外的选择可以插进来。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| Kata Containers | 把每个容器/Pod 放进一台轻量虚拟机的容器运行时，对外 OCI/CRI 兼容 |
| kata-runtime | Kata 的运行时进程，位置相当于 Docker 下的 runc，接收 OCI 命令与 spec |
| kata-agent | 跑在客户机里、容器 namespace 之外的进程，负责在虚拟机内部配挂载、网络、cgroup |
| shim | 常驻在虚拟机一侧的进程，做 I/O 并把虚拟机内部状态翻译给上层监控 |
| vsock | 虚拟机与宿主之间的套接字通道，Kata 用它承载 runtime 到 agent 的 gRPC |
| 9pfs | Plan 9 的网络文件系统，简单易用但非完整 POSIX，Kata 早期的默认共享方式 |
| DAX / NVDIMM | 把宿主内存一对一映射进客户机、绕过缓存的机制，Kata 用它映射 rootfs |
| virtio-fs | 基于 vsock 上跑 FUSE 的共享文件系统，兼容性与传输效率优于 9p |
| TC mirroring | 用 tc 做流量重定向的默认网络实现，兼容性更好、性能代价很小 |
| vhost-user | 用户态网络组件（DPDK/VPP/OVS）通过套接字直接接入虚拟机的机制 |
| virtcontainers | Kata 内部做虚拟机/ hypervisor 抽象的库，让不同 VMM 后端可以插进来 |
| CRI | Kubernetes 的容器运行时接口，Kubelet 通过它在 runc 与 kata-runtime 之间选择 |