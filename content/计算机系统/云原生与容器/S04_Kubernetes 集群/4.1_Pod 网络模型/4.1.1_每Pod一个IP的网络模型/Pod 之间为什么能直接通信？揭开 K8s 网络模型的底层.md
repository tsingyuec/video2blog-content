# Pod 之间为什么能直接通信？——K8s 网络模型与它的三条铁律

> 本文整理自 B 站视频《[Pod 之间为什么能直接通信？揭开 K8s 网络模型的底层](https://www.bilibili.com/video/BV1a2EA6VEaD/)》（时长约 22 分钟，K8s 网络系列第一篇）。文中的机制描述、命令与结论均来自该视频的图文稿，可核对。

## 本讲要解决的核心问题（SCQA）

**背景（S）**：在 K8s 集群里，你用 `kubectl run` 起两个 Pod，一个在 node1、一个在 node17。你 `kubectl exec` 进第一个 Pod，`curl` 第二个 Pod 的 IP，它秒回。在日常运维里，这几乎是"理所当然"的。

**冲突（C）**：可这两个 Pod 的 IP 并不在任何一块物理网卡的网段里；节点之间只有一张普通千兆口，没有静态路由，你也没做端口映射、NAT、iptables 规则。数据包却真真切切地从一台机器穿到了另一台机器——中间经过了数次封装、路由与规则匹配。

**疑问（Q）**：K8s 网络模型到底定义了什么，才让这种"理所当然"成立？CNI 插件又到底在 Pod 启动的那一瞬间做了什么？

**回答（中心思想 A）**：K8s 把集群网络抽象成**一个扁平的、统一的三层网络**——每个 Pod 拥有一个独立 IP，Pod 之间、节点与 Pod 之间都能直接互通、**无需 NAT**。这个抽象由**三条铁律**定义；而支撑它的实现代价，全部压在了 **CNI 插件**身上。理解了这一层，后面所有的 CNI 选型、网络排障、网络配置才有抓手。

[【跳转到 00:00】](https://www.bilibili.com/video/BV1a2EA6VEaD/?t=0) · [【跳转到 01:15】](https://www.bilibili.com/video/BV1a2EA6VEaD/?t=75)

![全片路线图：网络模型三条铁律 → Pod 启动时网络如何配好 → CNI 是什么 → ADD 调用详解 → Overlay/Underlay 对比 → IPAM → 排查命令](assets/Pod%20之间为什么能直接通信？揭开%20K8s%20网络模型的底层/00100.webp)

---

## 一、K8s 网络模型的骨架：三条铁律

K8s 并没有发明一套复杂的网络协议，而是先定下三条"铁律"，再让 CNI 插件去满足它们。这三条铁律是理解一切 K8s 网络现象的起点。[【跳转到 02:05】](https://www.bilibili.com/video/BV1a2EA6VEaD/?t=125)

### 1.1 铁律一：同一 Pod 内的所有容器共享同一个网络命名空间

**网络命名空间（network namespace）是什么？** 它是 Linux 内核提供的一层隔离：每个命名空间里有自己独立的网卡、IP、端口、路由表。默认情况下，两个进程如果不在同一个命名空间，就像身处两台互不相识的机器。

一个 Pod 里可能有多个容器（一个主容器 + 若干 sidecar/边车容器）。它们**共享同一个 network namespace**——也就是同一个 IP、同一组端口、同一张网卡。这正是为什么 sidecar 可以只用 `localhost` 访问主容器：在 Linux 内核眼里，它们本来就是"同一台机器"。[【跳转到 02:30】](https://www.bilibili.com/video/BV1a2EA6VEaD/?t=150)

这种共享是靠一个叫 **pause 容器（也叫"沙箱"容器）** 的东西实现的：Pod 启动时，第一个被创建的容器就是它。它持有 network namespace，其他业务容器通过加入这个 namespace 来"共用一张网卡"。pause 容器本身几乎不干活，只是守着这个 namespace 不被回收。

![铁律一示意：Pod 内的主容器与 sidecar 容器都加入同一个共享的 network namespace，里面只有一张网卡 eth0，IP 是 10.24.0.7——即"一个 Pod 一个 IP"](assets/Pod%20之间为什么能直接通信？揭开%20K8s%20网络模型的底层/00175.webp)

> **一句话记忆**：容器共享网络命名空间 ⇒ 一个 Pod 只有一个 IP。这就是本条目"每 Pod 一个 IP 的网络模型"的字面含义。

### 1.2 铁律二：Pod 之间直接通信，无需 NAT

这一点与传统 Docker **完全相反**。Docker 默认是 NAT 模型：容器想对外暴露要写端口映射（`-p 8080:80`），容器之间通信用的是宿主机网桥 `docker0`，跨主机还要靠虚拟 IP 做 DNAT。

K8s 不一样。Pod A 的 IP 是 `10.244.1.7`，Pod B 的 IP 是 `10.244.3.12`，它们**直接通信，中间不做任何地址转换**：两个 Pod 看到对方的 IP，就是对方真实的 Pod IP。[【跳转到 03:45】](https://www.bilibili.com/video/BV1a2EA6VEaD/?t=225)

这就是 K8s 选择"扁平网络"的核心理由——**让应用无感知**：一个 Pod 不需要知道自己是跑在 node1 还是 node17，也不需要操心自己的对外端口是什么；它看到自己的 IP 是什么，别人看到的就是什么。

![铁律二示意：Docker 是 NAT + 端口映射 + docker0 网桥；K8s 是 Pod IP 对 Pod IP 直连，无 NAT](assets/Pod%20之间为什么能直接通信？揭开%20K8s%20网络模型的底层/00225.webp)

### 1.3 铁律三：节点能直接访问任意 Pod

铁律二是"Pod 之间"，铁律三把它延伸到"节点与 Pod 之间"：所有节点都能直接访问所有 Pod，同样**无需 NAT**。

单独拎出来说，是因为它解决了一个具体问题——**kubelet 怎么做健康检查**。kubelet 跑在节点上，要定期探测本节点上 Pod 的存活探针和就绪探针；如果"节点访问 Pod"还需要 NAT，那 kubelet 就得逐一知道每个 Pod 的外部地址，这不现实。铁律三要求：无论 Pod 在本机还是远端，节点都能直接访问到它的 Pod IP。[【跳转到 04:35】](https://www.bilibili.com/video/BV1a2EA6VEaD/?t=275)

![铁律三示意：Node 可直接访问本机与远端所有 Pod 的 IP，kubelet 得以直接探测探针](assets/Pod%20之间为什么能直接通信？揭开%20K8s%20网络模型的底层/00300.webp)

### 1.4 三条铁律的合力：一张扁平的大三层网络

把三条铁律放在一起，就推导出一个结论：**K8s 的网络是一个扁平的、统一的三层（L3）网络**——所有 Pod 处在同一个大二层/三层平面内，就像在同一个局域网里一样。[【跳转到 05:00】](https://www.bilibili.com/video/BV1a2EA6VEaD/?t=300)

这个抽象对应用开发者太友好了：写代码时不用关心 Pod 会被调度到哪，服务发现只需要知道"对方的 IP + 端口"。但**抽象的代价，就落到了 CNI 插件身上**——它必须想尽一切办法，把 Pod 之间的流量跨节点打通。这就是 CNI 插件的核心使命。

![三条铁律的合力：Pod 内共享 network namespace + Pod 之间免 NAT + node 直通 Pod ⇒ 扁平的大三层网络](assets/Pod%20之间为什么能直接通信？揭开%20K8s%20网络模型的底层/00375.webp)

---

## 二、一个 Pod 的网络是怎么被"配"出来的

既然抽象的代价落在一个插件上，那这个插件是在什么时候被"叫起来"干活的？看一遍 Pod 的启动流程就清楚了：一个 Pod 从"没有"到"可以 ping 通其他 Pod"，中间经历了这些步骤。[【跳转到 06:15】](https://www.bilibili.com/video/BV1a2EA6VEaD/?t=375)

1. 你提交一个 Pod（`kubectl apply`）；
2. API Server 把它写入 etcd；
3. Scheduler 挑一个节点，把选择结果写进 Pod 的 `nodeName`；
4. 目标节点上的 **kubelet** 监听到"有 Pod 绑定到自己"；
5. kubelet 调用 **CRI（容器运行时接口）**，先起一个 **pause 容器**，创建好 network namespace；
6. **CRI 调用 CNI 插件**，把网络配置写进去；
7. 再拉起业务容器，让它加入 pause 容器的 network namespace；
8. Pod 就 run 起来了。

![Pod 启动时网络如何配好：最关键的一步是 CRI 调用 CNI 插件配置网络](assets/Pod%20之间为什么能直接通信？揭开%20K8s%20网络模型的底层/00450.webp)

这里最能体现 K8s 的**分层解耦**：kubelet 自己**不碰**网络配置，它把这件事完全委托给 CRI，CRI 再委托给 CNI。于是各层职责清晰——kubelet 管"让 Pod 跑起来"，CRI 管"调用容器运行时"，CNI 管"把网络配通"。[【跳转到 07:55】](https://www.bilibili.com/video/BV1a2EA6VEaD/?t=475)

---

## 三、CNI：把网络配置"外包"出去的标准接口

**CNI 全称 Container Network Interface**，是 CNCF 定义的一套容器网络配置规范。它的设计哲学非常极简：**你给我一个空的 network namespace，我负责把它配成一个能上网的网络环境**。[【跳转到 08:20】](https://www.bilibili.com/video/BV1a2EA6VEaD/?t=500)

在整个规范里，插件必须实现的操作其实只有两个：

| 操作 | 触发时机 | 负责的事 |
| --- | --- | --- |
| **ADD** | Pod 创建时 | 分配 IP、创建虚拟网卡、配路由、配 iptables |
| **DEL** | Pod 删除时 | 回收 IP、清理虚拟网卡、清理路由 |

此外还有几个辅助操作（`CHECK`、`VERSION`、`GC`），但抓住 ADD 与 DEL 就够了。

一个常被误解的点：**CNI 插件并不是一个常驻进程**。它是放在 `/opt/cni/bin` 下的一个**可执行文件**；CRI 在需要时 `fork` 出这个二进制，通过环境变量和标准输入输出把参数传进去、再从标准输出把结果拿回来。这种"fork + 标准输入输出"的方式，好处是**无状态、无依赖**——CRI 不需要和任何常驻服务打交道，插件升级也只需替换这个二进制文件。[【跳转到 09:10】](https://www.bilibili.com/video/BV1a2EA6VEaD/?t=550)

![CNI 是什么：Container Network Interface 是 CNCF 的规范，插件必须实现 ADD 与 DEL 两个操作](assets/Pod%20之间为什么能直接通信？揭开%20K8s%20网络模型的底层/00550.webp)

集群里到底装了哪些插件？`ls /opt/cni/bin` 会看到两类：

- **reference 插件**：如 `bridge`、`ptp` 等基础插件；
- **CNI 方案插件**：成熟的整套方案，如 Calico、Cilium、Flannel 等。

想知道集群实际用的是哪个插件，就看 `/etc/cni/net.d` 里的配置文件，看 `plugins` 字段是不是一个**数组**。现在支持**插件链**：一次 ADD 操作会按顺序调用数组里的每个插件，**前一个插件的输出作为后一个的输入**——这正是 portmap 这类"横切能力"能以独立插件形式叠加的原因。[【跳转到 10:25】](https://www.bilibili.com/video/BV1a2EA6VEaD/?t=625)

![集群里的 CNI 插件：reference 插件（bridge 等）与 CNI 方案插件（Calico、Cilium、Flannel 等），并用插件链组合](assets/Pod%20之间为什么能直接通信？揭开%20K8s%20网络模型的底层/00650.webp)

---

## 四、一次 ADD 调用：bridge 插件到底做了什么

以最简单的 `bridge` 插件为例，看它如何把一个"空的 network namespace"变得能上网。整个过程可以拆成五步：[【跳转到 11:40】](https://www.bilibili.com/video/BV1a2EA6VEaD/?t=700)

1. **创建 veth pair（虚拟以太网设备对，也叫"双头网卡"）**：在宿主机上创建一对相连的虚拟网卡，一头叫 X、一头叫 Y；
2. **把 Y 塞进 Pod 的 namespace**，并改名为 `eth0`。于是宿主机上有一个虚拟网卡 X，Pod 里有一个 `eth0`，两者连通；
3. **调用 IPAM 插件**（如 host-local 或 Calico IPAM）拿到一个空闲 IP，比如 `10.244.1.7`；
4. **在 Pod 的 network namespace 里配网络**：给 `eth0` 加上 IP、把网卡"提起来"、加一条默认路由；
5. **在宿主机上把 X 挂到网桥**（如 `cni0`）上，必要时再加上 iptables 规则；最后把 JSON 结果返回给 CRI。

这一套下来，Pod 就有了 IP、有了网卡、有了默认路由。于是：**同节点的 Pod 通过 `cni0` 网桥二层互通**；**跨节点的流量则走封装或路由出去**。[【跳转到 12:55】](https://www.bilibili.com/video/BV1a2EA6VEaD/?t=775)

![一次 ADD 调用的五步：建 veth pair → 塞 Y 进 Pod 并改名 eth0 → 调 IPAM 拿 IP → 配 IP/路由 → 把 X 挂到网桥并配 iptables](assets/Pod%20之间为什么能直接通信？揭开%20K8s%20网络模型的底层/00750.webp)

> **veth pair 是什么？** 你可以把它想成"一根网线两头"：一头插在宿主机、一头插在 Pod 的命名空间里。数据从一头进，就从另一头出。这就是"两台机器"之间被"连起来"的物理直觉。

---

## 五、跨节点流量：Overlay 与 Underlay 两条路

同节点好办（网桥二层直达），难的是**跨节点**。主流思路只有两条：[【跳转到 13:20】](https://www.bilibili.com/video/BV1a2EA6VEaD/?t=800)

**（1）Overlay：隧道封装。** Pod A 在 node1 发包，目标是远端的 Pod 网段，于是把整个 IP 包**塞进一个 UDP 或 VXLAN 包**里，包头写上"源是 node1、目标是 node17"，让物理网络把它送到 node17；node17 收到后**解封装**，取出原始包交给 Pod B。

- **好处**：物理网络**不需要知道** Pod 网段，只要节点之间三层可达就行；适合公有云、跨机房这种"对底层网络没有控制权"的场景。
- **代价**：封装/解封装有额外开销——这也是为什么这类方案的 **MTU 要减 50**。
- **代表方案**：Flannel 的 VXLAN 模式、Calico 的 IPIP 模式。[【跳转到 14:10】](https://www.bilibili.com/video/BV1a2EA6VEaD/?t=850)

**（2）Underlay：路由直达。** 如 Calico 的 BGP 模式、Cilium 的 native routing。Pod A 发包，node1 查路由表，发现"去 `10.244.30.0` 要走 node17"，就**按原始包直接发出**（不封装）；物理路由器/交换机把包送到 node17，node17 再查路由表，发现这个 IP 是本机的，就交给 Pod B。

- **好处**：不需要封装/解封装，性能非常快——直接走路由表到目标宿主机。
- **代价**：物理网络**必须知道怎么路由到 Pod 的 IP**——要么手动配静态路由，要么用 BGP 协议让节点和交换机自动交换路由信息。[【跳转到 15:25】](https://www.bilibili.com/video/BV1a2EA6VEaD/?t=925)

![跨节点流量两条路：Overlay 靠隧道封装（VXLAN/IPIP），Underlay 靠路由（BGP/直接路由）——这是 CNI 插件最核心的分水岭](assets/Pod%20之间为什么能直接通信？揭开%20K8s%20网络模型的底层/00875.webp)

**所以，跨节点通信"靠封装还是靠路由"，是 CNI 插件最核心的分水岭。**

---

## 六、IPAM：Pod 的 IP 从哪里来、怎么不冲突

**IPAM（IP Address Management）的职责**：给每一个 Pod 分配一个不冲突的 IP，并在 Pod 删除时回收它。听起来简单，但在分布式环境下，"**分配不能冲突、回收不能泄露**"并不好办。[【跳转到 16:15】](https://www.bilibili.com/video/BV1a2EA6VEaD/?t=975)

常见的三种 IPAM 方案：

| 方案 | 思路 | 代表 |
| --- | --- | --- |
| **host-local** | 每个节点预分一个 CIDR 段，各节点**本地**管自己的段 | Flannel、早期的 Calico |
| **Calico IPAM（全局 IPAM）** | 按节点需要**按需下发 block**，支持跨节点迁移 | Calico |
| **Cilium IPAM** | 多种模式，支持云厂商**原生地址** | Cilium |

host-local 有一个**经典坑**：节点重启以后，本地记录的"IP 已分配"信息还在，但实际的 Pod 早已不存在了，这些 IP 就出现**泄漏**，严重时会**耗光节点的 CIDR 段**，导致新 Pod 起不来。[【跳转到 17:05】](https://www.bilibili.com/video/BV1a2EA6VEaD/?t=1025)

Calico 的 IPAM 则把**状态存到 etcd 或 K8s API** 里：各节点不再各管一份，而是都到一个统一的"池子"里取信息。这样一来，某个节点宕机，别的节点也能从统一状态里知道哪些 IP 是"活的"——IP 泄漏问题就不存在了。这也就是为什么**大规模集群更倾向于 Calico**。[【跳转到 17:55】](https://www.bilibili.com/video/BV1a2EA6VEaD/?t=1075)

![IPAM 的三种方案对比，以及 host-local 的 IP 泄漏问题：把状态集中存到 etcd/API 即可解决](assets/Pod%20之间为什么能直接通信？揭开%20K8s%20网络模型的底层/01000.webp)

---

## 七、排查命令：把整条链路"串"起来

网络不通时，把下面这几步按顺序走一遍，就能"串起"整条链路，进而判断 CNI 到底在哪一步出了问题——这也是一张常用的**故障排查表**：[【跳转到 18:20】](https://www.bilibili.com/video/BV1a2EA6VEaD/?t=1100)

1. 在 **Pod 里**看网卡与 IP（`ip addr`）；
2. 找到该 Pod 所在**节点**，看 Pod 详细信息（`kubectl describe pod`）与路由表（`ip route`）；
3. 看**宿主机**上的虚拟网卡（veth）；
4. 看 **iptables 规则**；
5. 看 **BGP 状态**；
6. 看 **CNI 日志**（如 Calico 的 CNI 日志）。

把这些信息串起来，你就能还原出：Pod 里的 `eth0` → 宿主机上的虚拟网卡 → 挂在 CNI 网桥（`cni0`）上 → IP 是从 host-local 分配的。每一个环节都能对上，就说明 CNI 正常工作；对不上，问题就出在那一段。[【跳转到 19:35】](https://www.bilibili.com/video/BV1a2EA6VEaD/?t=1175)

![调试与排查命令清单：从 Pod 内网卡/IP，到节点路由、宿主机 veth、iptables、BGP 状态、CNI 日志](assets/Pod%20之间为什么能直接通信？揭开%20K8s%20网络模型的底层/01150.webp)

![Pod 网络排查流程图：把每个环节的信息串起来，即可覆盖绝大部分 Pod 网络不通的问题](assets/Pod%20之间为什么能直接通信？揭开%20K8s%20网络模型的底层/01200.webp)

---

## 小结

- **K8s 网络模型的三条铁律**：① 同一 Pod 内所有容器共享 network namespace ⇒ 一个 Pod 一个 IP；② 所有 Pod 之间可直接通信、无需 NAT；③ 所有节点能直接访问任意 Pod、无需 NAT。
- 三条铁律合起来，构成**一张扁平的大三层网络**——应用无需感知底层拓扑；代价则被 CNI 插件承担。[【跳转到 20:00】](https://www.bilibili.com/video/BV1a2EA6VEaD/?t=1200)
- **CNI** 是 CNCF 的容器网络规范，核心只有 **ADD** 与 **DEL** 两个操作；插件本质是 `/opt/cni/bin` 下的一个**二进制文件**，靠 fork + 标准输入输出与 CRI 通信，无状态、无依赖。
- 一次 **ADD 调用**（以 bridge 插件为例）= 建 veth pair → 塞进 Pod 改名 `eth0` → 调 IPAM 拿 IP → 配 IP/路由 → 挂到网桥并配 iptables。
- **跨节点流量** 两条路：**Overlay**（VXLAN/IPIP 隧道封装）与 **Underlay**（BGP/直接路由），"靠封装还是靠路由"是 CNI 的分水岭。
- **IPAM** 负责 IP 的分配与回收；host-local 易 IP 泄漏，全局 IPAM（如 Calico）把状态集中存到 etcd/API 更稳。
- 掌握 **`ip addr` / `ip route` / `iptables` / BGP 状态 / CNI 日志** 这套排查基本功，就能把 Pod 网络"串"起来。

---

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| **network namespace** | Linux 内核的隔离单位，拥有独立的网卡/IP/端口/路由表；同一 Pod 内所有容器共享它。 |
| **pause 容器** | Pod 里第一个被创建的"沙箱"容器，持有 network namespace，让其他容器共享同一网络栈。 |
| **veth pair** | 一对相连的虚拟网卡（像一根网线两头），一头在宿主机、一头在 Pod，负责"连起来"。 |
| **CNI** | Container Network Interface，CNCF 的容器网络配置规范；插件实现 ADD/DEL 两个操作。 |
| **CRI** | Container Runtime Interface，kubelet 调用的容器运行时接口；由它再去调用 CNI。 |
| **ADD / DEL** | CNI 的两个核心操作：ADD 在 Pod 创建时配网络，DEL 在 Pod 删除时清理网络。 |
| **Overlay** | 隧道封装方案（VXLAN/IPIP）：把 Pod 包再包一层，物理网络无需知道 Pod 网段。 |
| **Underlay** | 路由直达方案（BGP/native routing）：物理网络直接知道到 Pod IP 的路由。 |
| **IPAM** | IP Address Management，负责给 Pod 分配/回收不冲突的 IP。 |
| **host-local** | 每节点预分 CIDR 段、各管各的 IPAM；简单但节点重启后易 IP 泄漏。 |
| **扁平网络** | 所有 Pod 处在同一逻辑平面、可直连、无需 NAT 的抽象，即大三层网络。 |
| **cni0** | bridge 插件默认创建的网桥，同节点 Pod 通过它二层互通。 |
