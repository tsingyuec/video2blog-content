# 从零手写一个 CNI 插件：用 bash 实证 kubelet 如何调用 CNI

> 本文整理自 KubeCon + CloudNativeCon EU 2018 演讲《[Kubernetes Networking: How to Write a CNI Plugin From Scratch](https://www.youtube.com/watch?v=zmYxdtFzK6s)》（讲者 Eran Yanay，Twistlock）。文中结构图、清单、命令与结论均来自该视频的图文稿，可核对。讲者用 bash + 常见 Linux 工具，从零写出一支能跑的 CNI 插件，并现场演示了 Pod 打通网络的完整过程。

## 本讲要解决的核心问题（SCQA）

**背景（S）**：前面讲过，kubelet 会在 Pod 启动时调用「CNI 插件」，让插件把容器的网络配好。但「调用」和「配置」之间到底发生了什么，很多人只有模糊印象。

**冲突（C）**：把 CNI 说得再清楚，不如亲手写一支看看。可是插件从哪拿参数？它拿什么去配网卡和路由？为什么把代码写完、Pod 也起来了，**同节点 Pod 之间、跨节点 Pod 之间、访问公网**却还是不通？

**疑问（Q）**：**一支 CNI 插件到底由什么组成、被 kubelet 如何调用、内部要完成哪些动作？把网络真正打通，还差哪几片拼图？**

**回答（中心思想 A）**：一支 CNI 插件 = **一份配置 JSON + 一个可执行二进制**。二进制只做一件事——**在 Pod 的网络命名空间里，把网卡、IP、路由配出来**：建网桥、拉 veth pair、把一头塞进 Pod、分配 IP、设置默认路由。而「集群级」的连通性（同/跨节点转发、出公网做 NAT）**本不属于 CNI 二进制的职责**，通常由一个**常驻 Daemon** 完成——这正是「只写插件」时网络不通、而真实 CNI 供应商还要附带一个 Daemon 的原因。

[【跳转到 00:35】](https://www.youtube.com/watch?v=zmYxdtFzK6s&t=35)

![开场：Kubernetes Networking——How to Write a CNI Plugin From Scratch（KubeCon + CloudNativeCon EU 2018，讲者 Eran Yanay, Twistlock）](assets/Kubernetes%20Networking：%20How%20to%20Write%20a%20CNI%20Plugin%20From%20Scratch/00000.webp)

---

## 一、CNI 是什么：运行时与网络实现之间的接口

**CNI = Container Networking Interface（容器网络接口）**。它是**容器运行时（本例中是 Kubernetes）与网络实现之间的接口**。当 CNI 插件运行时，它负责**配置网络接口，也可能配置路由**。有一点必须牢记：**插件只关心 Pod 的网络连通性**——它不管存储、不管调度，只负责「让这个 Pod 能上网、能被访问」。[【跳转到 01:00】](https://www.youtube.com/watch?v=zmYxdtFzK6s&t=60)

![What is CNI?——CNI 是容器运行时与网络实现之间的接口：配置网络接口与路由，且只关心 Pod 的网络连通性](assets/Kubernetes%20Networking：%20How%20to%20Write%20a%20CNI%20Plugin%20From%20Scratch/00085.webp)

一支完整的 CNI 方案通常由**两个组件**构成：

![How CNI plugin works (in k8s)——① CNI 二进制：被 kubelet 执行，负责配置网络接口、搭建 Pod 连通性；② Daemon：在每个节点常驻，负责整个集群的可达性（每个 Pod 都能被每个节点访问）](assets/Kubernetes%20Networking：%20How%20to%20Write%20a%20CNI%20Plugin%20From%20Scratch/00185.webp)

| 组件 | 运行位置 | 职责 |
| :--- | :--- | :--- |
| **① CNI 二进制（插件本体）** | 被 kubelet 按需执行 | 配置网络接口，搭好**单个 Pod 的连通性**。 |
| **② Daemon（常驻守护进程）** | 每个节点一个 | 管理**集群级可达性**——让每个 Pod 都能被任意节点访问。 |

讲者特别说明：本次演讲**只聚焦第一部分（CNI 二进制本身）**——因为「集群可达性」在真实场景里由 Daemon 负责，而我们要亲手看清的是插件本体的调用与实现。

---

## 二、一支 CNI 插件由什么组成：配置文件 + 二进制

![What a CNI plugin is made of?——左边是配置文件（JSON），右边是可执行二进制；二进制需实现 CNI 规范定义的命令](assets/Kubernetes%20Networking：%20How%20to%20Write%20a%20CNI%20Plugin%20From%20Scratch/00310.webp)

**左半边——配置文件（一个 JSON 文件）**，包含若干必填字段：

- **`cniVersion`**：插件所遵循的规范版本。
- **`name`**：插件（网络）的名字。
- **`type`**：**要在 CNI 的二进制目录里查找的二进制文件名**。这是「配置 → 二进制」的对应关系所在。

此外还可以有可选字段和**自定义字段**——讲者在配置里放了一个自定义字段 `subnet`，稍后演示时就会用它。

**右半边——可执行二进制**，它必须实现 CNI 规范定义的**命令集**。核心是：

| 命令 | 何时被调用 | 做什么 |
| :--- | :--- | :--- |
| **ADD** | 新容器需要配置网络时 | 给新容器配置网络接口（本讲重点）。 |
| **DEL** | 容器被删除时 | 做清理，比如释放 IP 等。 |
| **CHECK** | 校验时 | 验证网络是否按配置搭好（0.4 规范后调整）。 |
| **VERSION** | 查询时 | 返回插件版本（很简单）。 |

[【跳转到 04:45】](https://www.youtube.com/watch?v=zmYxdtFzK6s&t=285)

**一个值得注意的部署细节**：讲者用一份 YAML（`kubectl apply` 一个下载下来的文件）来安装插件，而这个 Pod 跑在 **`hostNetwork: true`（主机网络）** 下。为什么要用主机网络？两个原因：

1. 这样就能**在 CNI 插件还没配好时先部署它本身**——它不需要别人给它分配 IP，因此在任何节点上都能跑起来。
2. 插件**要操作主机的网络栈**（改 iptables、加路由），所以必须能看到并修改主机的网络。

同时，这个 Pod 会**把磁盘上的特定路径挂进来**——也就是 CNI 二进制和配置**应当被放置的位置**。它的启动脚本会做几件事：确认 **CNI 二进制目录**存在、创建 **CNI 配置目录**（`/etc/cni/net.d`），最后把文件和配置**部署到正确的位置**。[【跳转到 07:48】](https://www.youtube.com/watch?v=zmYxdtFzK6s&t=468)

---

## 三、kubelet 是如何调用 CNI 的：从调度到 Pod 就绪

把「插件是什么」讲清楚后，看它在 Kubernetes 里被怎么用。一个完整的调用链是这样的：

![How a CNI plugin is being used in K8s?——API Server 告知 kubelet → kubelet 先建好 Pod 的网络命名空间（仅含 loopback）→ kubelet 调用 CNI 插件配置接口与 IP → Pod 就绪](assets/Kubernetes%20Networking：%20How%20to%20Write%20a%20CNI%20Plugin%20From%20Scratch/00568.webp)

1. **新 Pod 被调度**，API Server 把 Pod 的信息告知 **kubelet**，让它把这个 Pod 跑起来。
2. **kubelet 先建立 Pod 的网络命名空间**：它会先起 **`pause` 容器（沙箱容器）**——`pause` 容器的作用之一是**持有这个 Pod 的网络命名空间**，让 Pod 内所有容器共享它，从而彼此通信。此时，这个命名空间里**只有一块 `loopback` 网卡**。
3. **kubelet 调用 CNI 插件**，告诉它「这里有个新 Pod 要配网络」。
4. **插件开始干活**：**创建网络接口、分配 IP、可能定义路由**，完成其他网络操作。
5. **完成**：Pod 网络就绪，Pod 内的容器可以正常使用网络。

[【跳转到 08:13】](https://www.youtube.com/watch?v=zmYxdtFzK6s&t=493)

**那么插件被调用时，具体收到了哪些信息？** 答案是**两种形式**：

![How a CNI plugin is executed?——① 容器信息通过环境变量传入（CNI_COMMAND、容器 ID、netNS 路径、接口名）；② 网络配置则通过标准输入传入](assets/Kubernetes%20Networking：%20How%20to%20Write%20a%20CNI%20Plugin%20From%20Scratch/00668.webp)

- **① 容器信息（通过环境变量）**：包含命令（这里是 `ADD`）、**容器 ID**、**`netNS`**（容器网络命名空间在 proc 文件系统里的磁盘路径）、以及**要分配给它的接口名**。
- **② 网络配置（通过标准输入）**：本质上就是**那份 CNI 配置文件的全部内容**——你在里面写下的所有字段。

信息给全之后，插件就按配置去搭接口，并把**结果输出到标准输出**，告诉 kubelet 自己做了什么：**创建的接口列表、MAC 地址、接口名、默认网关、分配的 IP** 等等。[【跳转到 11:08】](https://www.youtube.com/watch?v=zmYxdtFzK6s&t=668)

---

## 四、Pod 网络的解剖：网桥 + veth pair

插件内部到底怎么把 Pod 接进主机网络？核心是两样东西：**网桥（bridge）**和 **veth pair**。

![Anatomy of pod networking——每个 Pod 有独立的网络命名空间；把 Pod 接到主机的简单办法是建一个网桥（bridge），再通过 veth pair 把 Pod 的一头连进网桥](assets/Kubernetes%20Networking：%20How%20to%20Write%20a%20CNI%20Plugin%20From%20Scratch/00793.webp)

- **网桥（bridge）**：你可以把它想成一台**物理交换机**——把「一根线」插到交换机的某个端口上，就接进了这台交换机的网络。
- **veth pair（虚拟以太网对）**：它由**一对互相连通的虚拟设备**组成——**从一端发出的每一个包，会立刻从另一端收到**。这在 Linux 容器场景里正好合适：**把一头放进容器（Pod）的网络命名空间，另一头留在主机命名空间**。

于是整个连接过程就是：**取 veth pair 的一端连到 Pod，另一端留在主机并接到网桥上**。此刻开始，**任何从 Pod 发出的包，都会立刻在主机这一侧的网桥上被收到**。[【跳转到 11:33】](https://www.youtube.com/watch?v=zmYxdtFzK6s&t=693)

> **一句话记忆**：**网桥负责「汇集」，veth pair 负责「穿孔」**——一个把主机各 Pod 连成一张二层网络，一个把 Pod 的命名空间和主机连通。

之后，**每有一个 Pod 被调度到本节点，CNI 插件就被调用一次**，它会：**建好 veth、接入网桥、给设备配 IP**，再用常见 Linux 工具（`ip`、`iptables` 等）**加上合适的路由**，让流量能在 Pod 与 Pod、Pod 与集群其余部分之间流动。[【跳转到 13:13】](https://www.youtube.com/watch?v=zmYxdtFzK6s&t=793)

---

## 五、动手写：ADD 的每一步都在做什么

讲者的演示环境是**两个节点**（node1、node2），它们通过各自的网卡互联；创建集群时，**每个节点分到一段专属的 Pod 网段**（例如 node1 分到 `10.244.0.0/24`）。而**配置文件里会写明本节点的 Pod 网段**——所以每个节点的配置都不同，插件据此知道自己该用哪段地址。[【跳转到 14:03】](https://www.youtube.com/watch?v=zmYxdtFzK6s&t=843)

下面聚焦 **ADD** 命令，看插件一步步做了什么（每一步都对应一段 bash + Linux 命令）：

![bridge 插件的 ADD 实现：读配置取网段 → 建网桥 → 建 veth pair → 把容器端移入 Pod 命名空间 → 分配 IP → 在 Pod 内配 IP 与默认路由](assets/Kubernetes%20Networking：%20How%20to%20Write%20a%20CNI%20Plugin%20From%20Scratch/00893.webp)

1. **读取配置、取出本节点网段**：从**标准输入**读取配置 JSON，用 **`jq`** 取出 `subnet` 字段。
2. **算出网关地址**：网关就是**网桥的地址**（通常是该网段的第一个可用地址）。
3. **创建网桥并启用**：用 **`ip`（iproute2 的 `bridge` 工具）创建一张名为 `cni0` 的网桥**，把它**启用（up）**，并**把网关 IP 设到它上面**——于是这台主机上的网桥就持有本节点 Pod 网段的网关地址。
4. **创建 veth pair**：为主机这一端**算一个随机名字**（因为要唯一），用 `ip link` 创建一对 veth——一端叫 **`CNI_IFNAME`**（kubelet 指定的容器内接口名），另一端是刚算出的主机端名字，然后都启用。
5. **把容器端移进 Pod 的网络命名空间**：这里有个关键细节——Linux 的网络命名空间有**两种形态**：一种是**绑定在进程上**的（`/proc/<PID>/ns/net`，进程一死就没了）；另一种是 **`/var/run/netns` 下的「命名」命名空间**（长期存在、不绑定进程，可以用 **`ip netns`** 直接操作）。插件**先在 `/var/run/netns/` 下建一个以容器 ID 命名的链接**，把 Pod 的 netns「接」进来，然后 `ip link set <接口> netns CNI_<容器ID>`——**这一下，接口就从主机命名空间搬进了 Pod 命名空间**。
6. **分配 IP**：IPAM 有很多做法（DHCP、`host-local` 等）；讲者为了简单，**用一个文件记住「上一个分出去的 IP」，每次加一**。
7. **在 Pod 命名空间里完成收尾**：进入命名空间**把接口拉起**、**把 IP 配到 `eth0` 上**、**把默认路由指向网关（即网桥 IP）**。

**到这一步，插件就干完了**——**Pod 已经连上网桥，包可以流动了**。[【跳转到 19:28】](https://www.youtube.com/watch?v=zmYxdtFzK6s&t=1168)

---

## 六、现场演示：为什么「配完了」还是不通

演示里部署了 3 个 Pod，分布在两个节点上（node1 上 alpine 与 nginx，node2 上 nginx）。因为插件已执行，**Pod 都拿到了同一网段里递增的 IP**。结果发现：

- **主机 → Pod**：**通**（因为已经连上网桥）。
- **同节点 Pod → Pod**：**不通**。
- **跨节点 Pod → Pod**：**不通**。
- **Pod → 公网**：**不通**。

讲者逐一「补」上缺失的拼图，正好展示了 **CNI 二进制之外、本应由 Daemon 做的事**：

**① 同节点 Pod 互通——需要 iptables 的 FORWARD 放行。**
每个 Pod 处在**不同的网络命名空间**里，从主机角度看，**Pod 之间的流量属于「外部流量」**（就像一台路由器下挂着多个用户，默认不允许它们互通）。要让包流过，需要 **`filter` 表的 `FORWARD` 链**放行：**追加一条规则，允许源地址、目的地址属于本集群 Pod 网段的流量被 `ACCEPT`**。加上之后，同节点 Pod 互通了。[【跳转到 22:56】](https://www.youtube.com/watch?v=zmYxdtFzK6s&t=1376)

**② 跨节点 Pod 互通——需要路由。**
每个节点的 Pod 网段**只有它自己知道**，别的节点不知道「对方的 Pod 网段在哪」。于是要在**内核路由表**里告诉它：**发往对方 Pod 网段的包，经由对方节点的 IP 转发**（在 node1 上加一条指向 node2 Pod 网段的路由，反之亦然）。两条路由都加好后，跨节点也通了。[【跳转到 24:36】](https://www.youtube.com/watch?v=zmYxdtFzK6s&t=1476)

**③ 访问公网——需要源地址伪装（masquerade）。**
Pod 发出的包带着**容器的私有 IP**，公网根本不知道如何回包。常见解法是 **source NAT（源地址转换）**：在 **`nat` 表的 `POSTROUTING` 链**上加一条规则，让**从本节点 Pod 网段发出、且不是发往 CNI 网段**的包**做 masquerade**——包离开主机时把源 IP 换成主机 IP，回包时再换回来。加上之后，Pod 就能出公网了。[【跳转到 27:06】](https://www.youtube.com/watch?v=zmYxdtFzK6s&t=1626)

> **本节的中心结论**：这些**手工补上的 iptables 规则、路由、NAT**，在真实集群里正是**由每个节点上的 Daemon（或 Deployment/Agent）自动完成**的。这也解释了 CNI 供应商为什么都「二进制 + Daemon」成对出现。[【跳转到 28:46】](https://www.youtube.com/watch?v=zmYxdtFzK6s&t=1726)

---

## 七、问答：并发、Calico 与 Service

讲者在结尾回答了几个有代表性的问题：

- **「多个 Pod 在同节点并发启动，会不会有问题？」** 在这个演示里，因为用「文件记上一个 IP」的简单做法，两次并发执行**有可能拿到同一个 IP**。不过最终会「自愈」——因为**插件失败时，Kubernetes 会重建这个 Pod**。另外，他直接改的主机 iptables 会被机器上其它工具影响，由于**没有用独立的 chain**，这些规则过一会儿可能被清掉。[【跳转到 30:11】](https://www.youtube.com/watch?v=zmYxdtFzK6s&t=1811)
- **「这跟 Calico 是不是很像？」** 是的，**Calico 用的是类似的方式**（也借助路由等机制）；**所有 CNI 的底层细节，本质上都大同小异**。[【跳转到 31:31】](https://www.youtube.com/watch?v=zmYxdtFzK6s&t=1891)
- **「Service 的服务发现也要靠 iptables 魔法吗？」** 当把 Pod 通过 **Service 暴露**出来时，Service 会把流量转发到后端（Endpoints）。这类「Service → Pod」的转发由集群组件处理（如 kube-proxy），**并非 CNI 二进制的职责范围**。[【跳转到 32:00】](https://www.youtube.com/watch?v=zmYxdtFzK6s&t=1920)

---

## 小结

用 bash 从零写一支 CNI 插件，把 Kubernetes 网络这条链彻底「点亮」了。回看三点：

1. **插件 = 配置 JSON + 一个二进制**。二进制只实现 CNI 命令集（ADD/DEL/CHECK/VERSION），**只关心 Pod 的网络连通性**。
2. **ADD 的核心动作是「在 Pod 命名空间里配网卡」**：建网桥 → 拉 veth pair → 把一端移入 Pod → 分配 IP → 设默认路由。kubelet 通过**环境变量**告诉插件「做什么」、通过**标准输入**告诉它「怎么配」。
3. **CNI 二进制 ≠ 全部网络**：同/跨节点转发、出公网 NAT 这些**集群级连通性**，由**每节点上的 Daemon** 负责——这也是为什么「只写插件」时网络不通，而真实 CNI 供应商都配套一个 Daemon。

## 关键术语速查

| 术语 | 一句话解释 |
| :--- | :--- |
| **CNI** | Container Networking Interface，容器运行时与网络实现之间的接口。 |
| **CNI 二进制** | 被 kubelet 调用的可执行插件本体，负责配置单个 Pod 的网络接口。 |
| **Daemon** | 每节点常驻进程，负责集群级可达性（CNI 二进制之外的网络工作）。 |
| **bridge（网桥）** | 可类比物理交换机，把主机上多个 Pod 的二层网络汇集起来。 |
| **veth pair** | 一对互相连通的虚拟网卡：一端进 Pod 命名空间、一端留主机接入网桥。 |
| **pause 容器** | 持有 Pod 网络命名空间的沙箱容器，让 Pod 内所有容器共享网络。 |
| **CNI_COMMAND / netNS / CNI_IFNAME** | kubelet 通过环境变量传入的命令、容器命名空间路径与接口名。 |
| **masquerade（源地址伪装）** | 出公网时把源 IP 换成主机 IP 的 NAT，让 Pod 能访问外部网络。 |
| **FORWARD 链** | iptables 中决定「是否放行转发流量」的链，需放行 Pod 网段以实现同节点互通。 |
