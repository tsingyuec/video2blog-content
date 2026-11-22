# 三大 CNI 路线之争：Flannel、Calico、Cilium 到底怎么选

> 本文整理自 B 站视频《[Flannel、Calico、Cilium 到底怎么选？三大 CNI 的底层路线之争](https://www.bilibili.com/video/BV1kVJ56bEpR/)》（K8s 网络系列课程第二篇，时长约 24 分钟）。文中概念、字段、表格与结论均来自该视频的图文稿，可核对。

## 本讲要解决的核心问题（SCQA）

**背景（S）**：装 CNI 看起来很简单——用 kubeadm、k3s 或者云厂商托管集群，一条命令就能装上任何一家的 CNI，Pod 起来、网络就通，业务跑得挺欢。

**冲突（C）**：但当集群上了规模、上了生产、有了安全合规要求之后，想换 CNI 基本等同于重建集群。视频里提到一个 200 节点的集群，从 Flannel 换 Calico，花了整整一个周末的停机窗口，中间还踩了三个坑。

**疑问（Q）**：Flannel、Calico、Cilium 到底有什么区别？面对自己的场景，该怎么选？

**回答（中心思想 A）**：这三个不是「同一辆车的三个品牌」，而是三条不同的底层路线——**Flannel 走 Overlay（封装）**、**Calico 走 BGP 路由（Underlay）**、**Cilium 用 eBPF 在内核里重写网络栈**。选型的核心不是谁性能最好，而是你的集群规模、团队能力和业务需求，跟哪种**设计哲学**最匹配；而且**一开始就要选对**，因为迁移是高危的停机操作。

[【跳转到 00:00】](https://www.bilibili.com/video/BV1kVJ56bEpR/?t=0)

---

## 一、一张矩阵看清三大派系

要理解三家为什么长得不一样，先画一张「定位图」。**跨节点流量**只有两种走法：

- **Overlay（覆盖网络）**：也就是**封装**，比如 VXLAN、IPIP。物理网络**不需要知道**你的 Pod 网段，只要节点之间三层可达就能用——适合公有云、跨机房这种**你对底层网络没有控制权**的场景。
- **Underlay**：也就是**纯路由、不封装**。性能最好、接近物理网络，但**物理网络必须知道怎么路由到你的 Pod IP**。

把这条「封装与否」当**横轴**，再把「主机侧数据面架构」当**纵轴**（从下往上：**L2 网桥 → 纯 L3 路由 → eBPF**），整个 CNI 世界就落到了一张矩阵里：

| 派系 | 代表 | 主机侧数据面 |
| :--- | :--- | :--- |
| L2 网桥 | **Flannel** | 每个节点一座网桥，Pod 网卡挂上去，同节点走二层广播域 |
| 纯 L3 路由 | **Calico** | 不要网桥，给每个 Pod 网卡直接配一条**主机路由** |
| eBPF | **Cilium** | 跳过 iptables 和 netfilter，在 TC / cgroup 层用 eBPF 处理包 |

![底层路线图：一张图看清三大派系（横轴 Overlay/Underlay × 纵轴网桥/路由/eBPF）](assets/Flannel、Calico、Cilium%20到底怎么选？三大%20CNI%20的底层路线之争/00150.webp)

[【跳转到 02:30】](https://www.bilibili.com/video/BV1kVJ56bEpR/?t=150)

**真正的差距在纵轴**：从 Flannel 到 Calico，是「**去网桥**」的过程；从 Calico 到 Cilium，是「**去 iptables**」的过程。每一层都是为了把更多决策从 Linux 网络栈的**传统慢路径**上裁下来。

要注意：三家**都同时支持 Overlay 和 Underlay 模式**，只是各自擅长和推荐的路线不同——Flannel 主打 VXLAN overlay，Calico 主打 BGP underlay，Cilium 主打 eBPF 加 native routing。

![两条核心分歧：横向「封装与否」，纵向「主机侧数据面架构」](assets/Flannel、Calico、Cilium%20到底怎么选？三大%20CNI%20的底层路线之争/00300.webp)

[【跳转到 05:00】](https://www.bilibili.com/video/BV1kVJ56bEpR/?t=300)

---

## 二、Flannel：够用就好的 Overlay 派

Flannel 是最早的主流 CNI 之一，由 **CoreOS** 开发，设计哲学只有四个字——**够用就好**。它给集群画一个较大的 Pod CIDR（比如 `10.244.0.0/16`），再给每个节点分一个 `/24` 子网；**同节点的 Pod 走 `cni0` 网桥二层互通**，本身不做复杂的跨节点机制。

Flannel 提供几种后端（backends）：

| 后端 | 做法 | 特点 |
| :--- | :--- | :--- |
| **VXLAN**（默认） | 用 UDP 封装，节点间建 VXLAN 隧道 | 有封装/解封装开销，但常规业务没感觉 |
| **host-gw** | 直接修改节点路由表，把对端 Pod 网段指向对端节点 | 性能接近物理网络，**但要求节点在同一 VPC、同一子网、二层互通** |
| AWS VPC | 借助云厂商的原生路由 | 只在特定云环境可用 |

视频特别强调：**host-gw 其实很能打**——它的数据面性能跟 Calico 的 BGP 模式**几乎没有差别**（都是纯路由不封装），而运维复杂度比 Calico **低一个数量级**，因为它没有 BIRD、也没有 BGP 邻居关系。如果你的规模只有几十个节点、不需要 NetworkPolicy，节点又是同子网二层互通，host-gw 是性价比很高的选择。

![Flannel 介绍：设计哲学「四字——够用就好」与三种后端](assets/Flannel、Calico、Cilium%20到底怎么选？三大%20CNI%20的底层路线之争/00350.webp)

[【跳转到 05:50】](https://www.bilibili.com/video/BV1kVJ56bEpR/?t=350)

**但 Flannel 有三个硬伤：**

1. **不支持 NetworkPolicy**。K8s 本身支持 NetworkPolicy，但 Flannel 不做，只能搭配 Calico 之类的组件去兜底；而且它自己也不再迭代了。
2. **功能仅停留在「能通」**：没有 eBPF、没有七层策略、没有可观测性。
3. **社区活跃度低**：CoreOS 被红帽收购后，Flannel 的迭代明显放缓。

所以 Flannel 的适用场景是：**测试环境、学习阶段、小规模集群**，对网络功能没有要求；或者裸金属同子网用 host-gw。**生产环境一般不再选它**——因为同样的位置，Calico 也可以，而且能力更强。18 年以前很多生产环境用 Flannel，只是因为那时 Calico 还不够成熟、Cilium 还没火起来。

![Flannel 的硬伤与适用场景：三个硬伤 + 什么时候用 Flannel](assets/Flannel、Calico、Cilium%20到底怎么选？三大%20CNI%20的底层路线之争/00425.webp)

[【跳转到 07:05】](https://www.bilibili.com/video/BV1kVJ56bEpR/?t=425)

---

## 三、Calico：把每个节点变成路由器的 BGP 派

Calico 的思路跟 Flannel **完全相反**：它**不封装，直接做路由**，核心理念是**把每个节点都变成一个路由器**。

Calico 在每个节点会跑两个关键组件：

- **Felix**：Agent，负责在节点上配置路由和策略；
- **BIRD**：BGP 守护进程。

节点之间通过 **BGP 协议**交换「我身上有哪些 Pod 网段」，于是**每个节点都维护一张完整的全集群路由表**。

![Calico：BGP 让 K8s 网络变成数据中心网络——节点、Felix、BIRD 与路由交换](assets/Flannel、Calico、Cilium%20到底怎么选？三大%20CNI%20的底层路线之争/00525.webp)

[【跳转到 08:45】](https://www.bilibili.com/video/BV1kVJ56bEpR/?t=525)

**一个关键细节**：Calico 的路由掩码是 **`/32`（单个 IP）**，不是 Flannel 那种 `/24` 的网段级别。原因是 Calico 的 **IPAM 是全局的**——Pod 可以在任何节点分配到任何 IP，路由表存放在 etcd 里，所有节点读的都是这张表。这让 IP 的利用率和灵活性大大提升，**代价是每个节点上的表会比较大**：

- 路由条目 ≈ **节点数 × 每节点 Pod 数**；
- 100 节点 × 30 Pod = 3000 条，完全没问题；
- 500 节点 × 50 Pod = **2.5 万条**，BIRD 内存就上来了；
- 再大（如 80 节点 × 2000 Pod ≈ 16 万条），BGP 收敛会明显变慢，BIRD 内存能吃掉几个 G。

**应对策略是 Route Reflector（RR）**：用它代替 full mesh 做聚合路由，限制每个节点的 peer 数量。规模再大，视频的建议是**直接换 Cilium**。

### BGP 模式的流量走向

以 Pod A 在 Node1、Pod B 在 Node3 为例：

1. Pod A 发包，Node1 查路由，发现目的 `10.244.3.12` 要到 Node3；
2. **不封装**，直接按原始 IP 发出去；
3. 物理网络把包发给 Node3，Node3 再查本节点路由，发现该 IP 是自己的 Pod，直接送进 Pod B 的网卡。

**注意第 2 步的前提：物理网络必须知道怎么路由这个 Pod IP。** 有两种实现方式：小规模（<100 节点）节点间直接做 BGP 对等；规模大了就上 Route Reflector——指定几个核心节点当 RR，其他节点只和 RR 建邻居。更彻底的部署，是**和数据中心的物理交换机建立 BGP 会话**，这样 Pod IP 在整个机房都可路由，真正做到「K8s 网络就是数据中心网络的一部分」。

![Calico BGP 流量走向：物理网络必须能路由到 Pod IP，这是 BGP 模式的前提](assets/Flannel、Calico、Cilium%20到底怎么选？三大%20CNI%20的底层路线之争/00725.webp)

[【跳转到 12:05】](https://www.bilibili.com/video/BV1kVJ56bEpR/?t=725)

### 跨子网怎么办：IPIP 与 CrossSubnet

公有云上你常常要跨可用区、跨 VPC，物理网络**根本不让你随便路由 Pod IP**。所以 Calico 提供了 **IPIP 模式**作为兜底：**同子网时还是纯路由，跨子网时做 IPIP 封装**。这个模式叫 **CrossSubnet**，兼顾了性能和通用性，是**公有云上 Calico 的默认推荐**。

![Calico BGP 模式：同子网纯路由，跨子网走 IPIP 封装（CrossSubnet）](assets/Flannel、Calico、Cilium%20到底怎么选？三大%20CNI%20的底层路线之争/00775.webp)

[【跳转到 12:55】](https://www.bilibili.com/video/BV1kVJ56bEpR/?t=775)

### 核心卖点：NetworkPolicy

这是 Flannel 没有的。除了 K8s 原生的 NetworkPolicy，Calico 还提供自己的扩展 **GlobalNetworkPolicy**——**集群级**策略，不受 namespace 限制，有更丰富的匹配条件和更细粒度的动作。

Calico 从 **3.13** 起就支持 **eBPF 数据面**，可以绕开 iptables 和 kube-proxy，直接在网卡上用 eBPF 处理包，性能跟 Cilium 相当。但这个特性在生产上的普及度不如 Cilium，主要原因是 **Calico 的 eBPF 是「锦上添花」**——BGP 加 iptables 已经够用了；而 Cilium 是**为 eBPF 而生**，设计得更彻底。

![Calico 的核心卖点 NetworkPolicy：K8s 原生策略 + 集群级 GlobalNetworkPolicy](assets/Flannel、Calico、Cilium%20到底怎么选？三大%20CNI%20的底层路线之争/00800.webp)

[【跳转到 13:20】](https://www.bilibili.com/video/BV1kVJ56bEpR/?t=800)

---

## 四、Cilium：用 eBPF 重写网络栈

如果说 Calico 是在**现有 Linux 技术栈上**把每个节点做成路由器，那么 Cilium 就是**绕开现有网络栈**，用 **eBPF 在内核里自己写一个**。

**eBPF 是什么？** 它是 Linux 内核的一项技术，允许你在内核的各种 hook 上挂载**沙盒化**的程序——**不需要改内核代码，也不需要加载内核模块**，就能在包处理、系统调用等关键路径上插入自定义逻辑。

对比一下两条路径：

| | 传统 K8s 网络栈 | Cilium |
| :--- | :--- | :--- |
| 包的处理 | Pod 发包 → veth → 宿主机网络栈 → iptables 的 prerouting → forward → postrouting → 网卡 | 在 veth 的 TC hook 上用 eBPF 程序直接做**路由决策、NAT、策略检查** |
| 规则形态 | 规则链，逐条匹配 | 查表 / 哈希 |
| 是否经过 iptables | 每一步都在内核里走一遍规则链 | **绕开 iptables**，快不止一个数量级 |

![Cilium：用 eBPF 重写整个网络栈——传统 iptables 路径 vs eBPF 路径](assets/Flannel、Calico、Cilium%20到底怎么选？三大%20CNI%20的底层路线之争/00900.webp)

[【跳转到 15:00】](https://www.bilibili.com/video/BV1kVJ56bEpR/?t=900)

### Cilium 的七大核心能力

1. **native routing**：跟 Calico 的 BGP 模式类似，节点间走直接路由，但底层由 eBPF 转换；
2. **替代 kube-proxy**：用 eBPF 实现 Service 负载均衡，性能远超 iptables 和 IPVS；
3. **七层 NetworkPolicy**：能在 HTTP / gRPC 层做策略，比如只允许某用户访问 API 的 `v1/user` 路径，其余拒绝——这是三、四层做不到的；
4. **Hubble 可观测**：基于 eBPF 的可观测平台，能看到每条流量端到端的路径、过去 10 分钟哪些请求被策略拒绝、服务的 P99 延迟，比 Istio 轻量得多；
5. **Cluster Mesh**：多集群联邦，Pod 可跨集群直接通信；
6. **透明加密**：用 IPsec 或 WireGuard 对 Pod 之间的流量加密；
7. **支持 VXLAN / Geneve 封装**：对底层网络没有控制权的场景也能用。

![Cilium 核心能力：native routing、替代 kube-proxy、七层策略、Hubble、Cluster Mesh、加密与封装](assets/Flannel、Calico、Cilium%20到底怎么选？三大%20CNI%20的底层路线之争/00975.webp)

[【跳转到 16:15】](https://www.bilibili.com/video/BV1kVJ56bEpR/?t=975)

### Cilium 的代价

1. **学习曲线陡峭**：得懂 eBPF、BGP、VXLAN 等一堆东西，出问题排障难度比 Calico 高很多；
2. **内核版本要求高**：能用哪些特性跟内核强相关（如 CentOS 7 默认的 3.10 内核基本用不了），要吃透全部能力建议上 **5.10** 以上；
3. **资源开销**：eBPF 的 map 吃内存，大集群下 cilium-agent 的内存可能达到**几百兆**；
4. **生态不如 Calico 成熟**。

---

## 五、横向对比表

把三家拉齐到同一张表上，差异一目了然：

| 维度 | Flannel | Calico | Cilium |
| :--- | :--- | :--- | :--- |
| **数据面** | VXLAN overlay | BGP 路由 + IPIP | eBPF + native routing |
| **性能** | 中等（host-gw 接近物理网络） | 高 | 最高 |
| **NetworkPolicy** | ❌ 不支持 | ✅ L3/L4 + 扩展 | ✅ L3/L4/L7 |
| **可观测性** | 基本没有 | 基础 | Hubble，非常强大 |
| **替代 kube-proxy** | ❌ | eBPF 数据面可完全替代 | ✅ |
| **内核要求** | 3.10+ | 3.10 或 5.4 | 建议 5.10+ |
| **运维复杂度 / 排障难度** | 最低 | 中 | 最高 |

![一张横向对比表：数据面、性能、NetworkPolicy、可观测性、kube-proxy 替代、内核要求、运维复杂度](assets/Flannel、Calico、Cilium%20到底怎么选？三大%20CNI%20的底层路线之争/01164.webp)

[【跳转到 19:24】](https://www.bilibili.com/video/BV1kVJ56bEpR/?t=1164)

---

## 六、按场景选型

讲完差异，到底怎么选？视频给出的场景化建议：

- **学习 / 测试环境、小集群** → **Flannel** 的 VXLAN 模式：配置简单、问题少、遇到网络问题好排查；
- **中小规模（50–300 节点）** → **Calico** 的 **CrossSubnet IPIP** 模式：稳定成熟、NetworkPolicy 够用、生态好、踩坑资料多；
- **500 节点以上、多租户或强安全合规** → **Calico 的 BGP 模式 + Route Reflector**，或 **Cilium**：Calico 经过很多大厂验证，最成熟；Cilium 更现代；
- **极致性能（高频交易、AI 训练、大规模微服务）** → **Cilium 的 native routing + 替代 kube-proxy**：eBPF 的性能优势要在**高负载**下才真正显现；
- **需要七层防护策略或服务网格**（替代 Istio）→ **Cilium**：比 Istio 轻量得多，七层能力覆盖大部分需求；
- **公有云托管 K8s** → 用它**默认的**就好；
- **单集群跨机房** → **Calico** 和物理交换机做 **BGP Peering**，这是 Calico 最经典的卖点之一；
- **多集群联邦** → 首选 **Cilium Cluster Mesh**，备选 Submariner。

![按场景的选型建议：从学习环境到多集群联邦，每类场景对应推荐方案](assets/Flannel、Calico、Cilium%20到底怎么选？三大%20CNI%20的底层路线之争/01208.webp)

[【跳转到 20:08】](https://www.bilibili.com/video/BV1kVJ56bEpR/?t=1208)

---

## 小结

- **三条路线**：Flannel = Overlay（L2 网桥），Calico = BGP 路由（L3），Cilium = eBPF（内核可编程）。**矩阵的纵轴才是真正的差距**。
- **Flannel** 是「够用就好」的 VXLAN 时代产物，适合学习与小集群；硬伤是不支持 NetworkPolicy、只停留在「能通」、社区迭代放缓。
- **Calico** 把每个节点变成路由器，用 BGP 让 Pod 网络与物理网络对齐，是**目前生产最稳定**的选择；核心卖点是 NetworkPolicy / GlobalNetworkPolicy，跨子网用 CrossSubnet（IPIP）兜底。
- **Cilium** 用 eBPF 重写内核网络栈，是**面向未来**的选择：native routing、替代 kube-proxy、七层策略、Hubble 可观测一应俱全；代价是门槛高、内核要求高、生态仍在追赶。
- **选型的核心不是谁性能最好**，而是看集群规模、团队能力、业务需求与 CNI 设计哲学是否匹配。
- **最重要的是「一开始就选对」**：从 Flannel 迁到 Calico，或从 Calico 迁到 Cilium，都是很高危的停机操作。

![本章小结：Flannel（够用就好）、Calico（生产最稳定）、Cilium（面向未来）](assets/Flannel、Calico、Cilium%20到底怎么选？三大%20CNI%20的底层路线之争/01333.webp)

[【跳转到 22:13】](https://www.bilibili.com/video/BV1kVJ56bEpR/?t=1333)
