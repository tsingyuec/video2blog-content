# Kata Containers 的 agent 与 shim：VM 里谁接指令、谁报告容器死活

> 视频来源：[Kata Containers An introduction and overview](https://www.youtube.com/watch?v=4gmLXyMeYWI)（YouTube · Graham，Intel 开源技术中心，会议演讲）｜时长约 32 分钟（含问答）
> 导读：这是一场偏概览的演讲，讲 Kata 是什么、为什么要在容器外面套一台 VM、以及这台 VM 里外各有哪些组件。本文只抽取与「宿主怎么在 VM 里下指令、怎么判断容器还活着」相关的部分：agent 的职责、vsock 取代 proxy 的通道变化、shim 作为监控翻译官的角色。网络与存储的调优细节只取到「agent 要配置什么」为止。字幕为自动生成，人名与项目名已按上下文订正。

## 本讲要解决的核心问题（SCQA）

**背景**：Kata Containers 的做法是「每个容器（或每个 Pod）一台轻量虚拟机」。容器在里面照常跑，用 namespace、cgroup 隔离，它自己感觉不到外面套了一层硬件虚拟化。

**冲突**：一旦套上 VM，宿主与容器之间就多了一道硬件边界。kubelet 和容器运行时站在边界外面，它们既不能直接 `exec` 进容器，也不能直接读容器进程的 `/proc` 判断它是否还活着。可容器生态里所有的工具——`docker ps`、CRI 的 `ContainerStatus`、监控采集——都默认「我能看到容器进程」。

**疑问**：VM 里那个「接电话的人」是谁？监控和指令怎么穿过这道边界？

**回答（中心思想）**：VM 里有一个 agent，它是宿主在客户机内唯一的执行入口，负责把「挂载点、网络、内存、cgroup」这些配置落到容器上；VM 外面有一个常驻的 shim，负责把容器栈的提问（容器还在吗、给我统计）翻译成穿过边界发给 agent 的请求。**agent 决定「能不能做」，shim 决定「外面怎么问」。**

## 一、Kata 的取舍：用一台小 VM 换一层硬件隔离

[【跳转到 01:33】](https://www.youtube.com/watch?v=4gmLXyMeYWI&t=93) 演讲开头把光谱讲得很清楚：容器这一端启动快、部署简单、工具链成熟，但隔离靠软件（namespace、capability、cgroup）；VM 那一端隔离强，代价是「开机一分钟、几百 MB 内存」。Kata 想做的是把两边接起来——要 VM 的隔离，不要 VM 的笨重。

![Speed vs Security：横轴是速度、纵轴是隔离，Kata 的位置在两者之间，而不是任何一端](assets/Kata%20Containers%20的%20agent%20与%20shim：VM%20里谁接指令、谁报告容器死活/00124.webp)

具体做法是**每个容器一台 VM，每台 VM 有自己的内核**：

![Kata 的隔离模型：每个 VM 里一个进程，各自一套 namespace 与一份独立内核，最底下才是宿主内核](assets/Kata%20Containers%20的%20agent%20与%20shim：VM%20里谁接指令、谁报告容器死活/00374.webp)

[【跳转到 06:16】](https://www.youtube.com/watch?v=4gmLXyMeYWI&t=376) 讲者强调了两点：一是「每个容器拿到自己的内核」，所以可以针对单个 Pod 裁剪内核特性；二是所有编排动作仍然发生在裸金属宿主上——你照常用 Kubernetes 的工具部署，只是容器实际跑在 VM 里，而容器自己不该知道这件事。

这就是问题的起点：**容器不知道自己在 VM 里，但宿主必须知道 VM 里发生了什么。**

## 二、七件套：agent 只是组件清单里的一项

[【跳转到 07:31】](https://www.youtube.com/watch?v=4gmLXyMeYWI&t=451) 演讲给了一张组件清单：

![Kata 的组件：QEMU 包、runtime、内核、rootfs 镜像、agent、shim、proxy](assets/Kata%20Containers%20的%20agent%20与%20shim：VM%20里谁接指令、谁报告容器死活/00524.webp)

按「谁在边界哪一侧」重新归类，会更容易理解它们的分工：

| 组件 | 位置 | 职责 |
| --- | --- | --- |
| runtime（`kata-runtime`） | 宿主 | 实现 OCI 运行时接口，被 containerd/CRI-O 调用；生命周期很短 |
| QEMU 包 | 宿主 | 真正创建 VM 的 VMM |
| 内核 | 客户机 | 每个 Pod 一份，可单独裁剪 |
| rootfs 镜像 | 客户机 | 一个极小的根文件系统，用来把 VM 引导起来 |
| **agent** | 客户机 | VM 内的执行入口：配置挂载、网络、内存、cgroup，执行命令 |
| **shim** | 宿主 | 留在宿主上替容器栈盯着 VM，并把提问翻译成对 agent 的调用 |
| proxy | 宿主 | 早期用于转发到 agent 的组件，正在被 vsock 取代 |

[【跳转到 08:25】](https://www.youtube.com/watch?v=4gmLXyMeYWI&t=505) 为什么客户机里还需要一个 rootfs？讲者的解释很实在：容器镜像里「东西不够多」，没法直接当一台机器的根文件系统用。VM 必须先引导一个极小的 rootfs，再由这个环境把容器搭起来——**这一步的执行者就是 agent**。

## 三、agent 的职责：把 OCI 配置变成 VM 里的现实

[【跳转到 08:43】](https://www.youtube.com/watch?v=4gmLXyMeYWI&t=523) 讲者用一句话定义了 agent 的角色：**「工作最终得在 VM 里发生」**——总得有人去配置挂载点、网络、内存资源和 cgroup。runtime 把要做的事告诉 agent，agent 去执行。他称 agent 为「workhorse（干活的那匹马）」。

更关键的是它的位置：

[【跳转到 09:22】](https://www.youtube.com/watch?v=4gmLXyMeYWI&t=562) **agent 跑在容器的 namespace 之外**。这样它才有权限去操作容器的 namespace、内核参数，以及面向 hypervisor 的那一层。用一句话概括：agent 是「VM 里的 root」，容器是它管的对象。

这也解释了为什么 agent 必须由运行时自己带、而不是复用客户机发行版里的服务：它要理解 OCI 的配置语义，而不只是执行 shell。

agent 要落地的两类资源，演讲各给了一张图：

![Kata 的存储路径：overlay 走 9pfs，device mapper 走块设备直通，镜像文件走 NVDIMM + DAX，远端存储走网络](assets/Kata%20Containers%20的%20agent%20与%20shim：VM%20里谁接指令、谁报告容器死活/01099.webp)

![Kata 的物理网络：容器网络与 VM 网络的模型不一致，需要在宿主侧做端点映射，加速方案（DPDK、SR-IOV）可以直接插进 VM](assets/Kata%20Containers%20的%20agent%20与%20shim：VM%20里谁接指令、谁报告容器死活/00899.webp)

这两张图放在「agent 与就绪探测」的语境下，价值在于说明**「就绪」不只是进程起来了**：存储没挂上、网络没配通，容器即使跑起来也不可用。而这些挂载与网络配置恰恰是 agent 在容器启动前完成的——它既是配置的执行者，也是「配置是否落地」的唯一知情人。

## 四、通道：从 proxy 到 vsock

[【跳转到 09:22】](https://www.youtube.com/watch?v=4gmLXyMeYWI&t=562) 演讲的架构图上有两条通往 VM 的线：一条经 shim，一条经 runtime，都标注为 gRPC，落到 hypervisor 的 **VSOCK socket** 上。

![Kata 基本架构：shim 与 runtime 通过 gRPC 走 hypervisor 的 vsock socket 进入 VM，VM 里从上到下是容器命令、agent、内核、hypervisor](assets/Kata%20Containers%20的%20agent%20与%20shim：VM%20里谁接指令、谁报告容器死活/00574.webp)

讲者特别说明了这张图的一个变化：**proxy 被跳过了**。早期架构里有一个 proxy 组件专门做转发，现在改用 vsock——「一个比较新的内核特性」，proxy 因此在图里变得不那么重要。

这个变化对「就绪探测」有直接影响：通道越短，探测的往返就越可预测。宿主侧的 shim 不再需要经过一个额外的转发进程，直接把请求写进 vsock，客户机里的 agent 收到后执行，再把结果原路送回。**这也意味着探测的延迟与 VM 是否被调度、agent 是否在跑强相关**——通道断了，探针失败的原因可能根本不在业务上。

## 五、shim：宿主侧那个「翻译官」，也是探针的落点

[【跳转到 09:57】](https://www.youtube.com/watch?v=4gmLXyMeYWI&t=597) 这段是全场最贴近「就绪探测」的部分。讲者先讲了一个容易被忽略的事实：**runtime 是瞬态的**。`docker run` 或 kubelet 启动容器时，runtime 把环境搭好就退出了，它不会一直待在那儿。

那谁来回答「容器还在跑吗」？传统方案是直接盯容器进程；但在 Kata 里，「盯容器进程」这件事在宿主上做不到——容器进程在 VM 里。讲者说，默认做法会变成去盯 QEMU 进程，可那也不是你真正想看的：QEMU 活着不代表容器活着。

于是有了 shim：**它留在宿主上，替容器栈盯着这台 VM，并把问题翻译过去**——你问「容器还在吗」，它去问 VM 里的 agent，再把答案翻译回来。讲者的原话是「把 VM 里的信息翻译出来，告诉你其实应该问什么」。

把这条链路完整写出来：

```text
kubelet / docker
   │  容器还在吗？给我统计
   ▼
CRI（containerd / CRI-O）
   │
   ▼
shim（宿主，常驻）
   │  gRPC over vsock
   ▼
agent（客户机，容器 namespace 之外）
   │
   ▼
容器进程 / 业务端口
```

### 5.1 三层判据在 Kata 里分别落在谁身上

把「进程级 / 内核级 / 服务级」这套判据套到 Kata 上，每一级的证据来源都不一样：

| 判据层级 | Kata 里的证据 | 谁提供这个证据 | 测不到什么 |
| --- | --- | --- | --- |
| VM 进程级 | QEMU 进程在、shim 在 | 宿主（进程表） | 客户机可能还卡在引导 |
| 客户机内核级 | agent 能应答一次 gRPC | agent + vsock 通道 | 容器可能还没创建 |
| 容器级 | agent 报告容器已创建、进程在 | agent（容器 namespace 之外） | 业务端口可能还没监听 |
| 服务级 | 探针命令经 agent 在容器里执行成功 | 业务自己暴露的健康端点 | 依赖的下游是否可用 |

这张表最实用的一点是：**前三级都不需要业务配合，只有第四级需要**。所以当你在 Kata 上看到「Pod 一直 not ready」，先按这张表从下往上排，比直接怀疑业务代码要快。

这张链路图解释了一个实践中的常见困惑：**在 Kata 里，探针失败可能发生在四个不同的地方**——业务真的挂了、agent 没起来、vsock 通道不通、shim 卡住。只看 kubelet 的 `Unhealthy` 事件是分不出来的，必须逐层看。

## 六、接进 Kubernetes：按 Pod 选运行时

[【跳转到 12:15】](https://www.youtube.com/watch?v=4gmLXyMeYWI&t=735) Kata 不是 runc 的替代品，而是并排的另一个选择。你可以在同一个集群里，让一部分 Pod 跑 runc、一部分跑 Kata，甚至按 Pod 指定：

![CRI-O 与 Kata：kubelet 经 CRI 到 CRI-O/containerd，再分叉到 runc（普通 Pod）或 kata-runtime（VM 里的 Pod）](assets/Kata%20Containers%20的%20agent%20与%20shim：VM%20里谁接指令、谁报告容器死活/00749.webp)

讲者的建议很务实：轻量、可信的负载直接用 runc 换速度；来源不明、不信任的负载放进 Kata。这也意味着**同一个集群里，探针的语义相同、落地路径不同**：跑在 runc 里的 readinessProbe 是宿主直接进容器执行，跑在 Kata 里的则要多穿 shim 与 agent 两层。

## 七、代价与边界：agent 是能力，也是攻击面

[【跳转到 16:56】](https://www.youtube.com/watch?v=4gmLXyMeYWI&t=1016) 讲者给了两个量化指标：启动「远低于一秒」，每容器内存开销「大约 50 MB 量级」。他还提到一个优化手段：用 NVDIMM 把 rootfs 以 DAX 方式直接映射进 VM 内存，绕过各级缓存，既省启动时间也省内存与缓存占用。

[【跳转到 17:11】](https://www.youtube.com/watch?v=4gmLXyMeYWI&t=1031) 关于安全，演讲给了一个「分层」的视角：安全像洋葱，一层层加，但每一层都有代价（体积、速度）。所以 Kata 通常**只在一边加层**——要么在容器里加 seccomp，要么在宿主上包 QEMU：

![安全分层：容器内加 seccomp；宿主侧加 cgroup 隔离、更多 namespace 隔离、rootless QEMU、SELinux 策略](assets/Kata%20Containers%20的%20agent%20与%20shim：VM%20里谁接指令、谁报告容器死活/01174.webp)

这一页对理解 agent 的定位很重要：**agent 是「宿主可信」假设下的产物**。它给宿主开了一条在 VM 里执行命令的路，所以宿主侧必须跟着收窄权限（rootless QEMU、SELinux 策略），否则这条通道就成了逃逸的捷径。

[【跳转到 27:09】](https://www.youtube.com/watch?v=4gmLXyMeYWI&t=1629) 最后还有一个有意思的边界：如果想让 Kata 跑非 Linux 容器，讲者说「第一步要做的就是把 agent 移植过去」——因为必须有一个 agent 在 VM 里对话。这反过来印证了本文的中心思想：**agent 不是可选项，它是「VM 里有人接电话」这件事本身。**

## 小结

- Kata 用「每容器一台轻量 VM、每 VM 一份内核」换硬件级隔离，容器自己感知不到这层边界。
- 边界一旦存在，宿主就失去了直接操作容器进程的能力，因此 VM 里必须有一个 agent：它在容器 namespace 之外，负责把挂载、网络、内存、cgroup 配置落到容器上。
- 通道从早期的 proxy 转发改为 vsock：shim 与 runtime 通过 gRPC 走 hypervisor 的 vsock socket 进入 VM。
- runtime 是瞬态的（搭好环境就退出），shim 留下来：它替容器栈盯着 VM，并把「容器还在吗」翻译成对 agent 的提问。
- 探针链路是 kubelet → CRI → shim → agent → 容器，任何一层出问题都表现为「探针失败」，必须逐层排查。
- 代价是每容器约 50 MB 内存与一层额外的探测跳数；收益是内核级隔离，以及可以按 Pod 选择 runc 或 Kata。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| Kata Containers | 把每个容器/Pod 放进一台轻量 VM 的容器运行时，兼容 OCI 与 CRI |
| agent | 跑在客户机里、容器 namespace 之外的执行入口，接收 runtime 的指令并落地配置 |
| shim | 宿主上的常驻进程，替容器栈盯着 VM，把提问翻译给 agent |
| proxy | 早期 Kata 架构里转发到 agent 的组件，正被 vsock 取代 |
| vsock | 虚拟机与宿主之间的套接字通道，不经过 IP 网络栈 |
| gRPC | agent 与 shim/runtime 之间的 RPC 协议 |
| 瞬态 runtime | 只负责把环境搭好就退出的运行时进程，因此需要 shim 留下接管监控 |