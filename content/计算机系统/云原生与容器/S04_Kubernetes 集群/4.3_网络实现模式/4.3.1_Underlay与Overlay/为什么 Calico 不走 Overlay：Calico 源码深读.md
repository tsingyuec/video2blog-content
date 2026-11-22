# 为什么 Calico 不走 Overlay：Calico 源码深读

> 视频来源：[01·Calico 是什么？为什么它偏偏不走 overlay｜Calico 源码深读](https://www.bilibili.com/video/BV1tbhW68Evu/)（Bilibili，11:21）
>
> 这是一支「Calico 源码深读」系列的开篇，它不急着钻进函数，而是先把地图画出来，回答四个问题：Calico 到底解决什么问题、它和 Flannel 最根本的分歧在哪、一台节点上跑了哪些进程、一个数据包从 Pod 到 Pod 经历了什么。字幕来自 B 站 AI 字幕，已逐窗口纠正错拼（如 `开了口`→**Calico**、`CUBBERNIS`→**Kubernetes**、`FLO`→**Flannel**、`tiff`→**Typha**、`KELLY`→**cali**、`nowing cap`→**no-encap**、`EXCE`→**ipset** 等）。

## 本讲要解决的核心问题（SCQA）

**背景**：Kubernetes 的网络模型只提了要求，没给实现——它规定每个 Pod 有自己的 IP、Pod 之间能直接互通且不经过 NAT，但故意不规定"这些 IP 包到底怎么在一个节点到另一个节点之间跑"。

**冲突**：正因为 K8s 不给实现，各家网络方案（CNI）必须自己回答一个绕不过去的问题——**"别的节点上的 Pod 网段，路由是谁告诉这台节点的？"** 同样是让 Pod 互通，Flannel 和 Calico 却选了截然不同的两条路，这两条路的差别远不止性能。

**疑问**：Calico 为什么不走 Overlay（隧道封装），而要把每台主机当成路由器？这条路由到底由谁来写？一支以机制深度著称的 Calico 源码，为什么代码量高达 35 万行？

**回答（中心思想）**：**Flannel 把网络搞成一条条隧道，Calico 把网络搞成一张路由表。** Overlay（打隧道）把 Pod 报文封进 UDP/VXLAN 里发到对端再解开，好处是底层网络完全不用改，代价是每个包多一层封装（12~50 字节）、MTU 变小、故障排查要剥两层；Calico 走 Underlay 路线，用 BGP 把每个节点的 Pod 网段宣告出去，包"进来什么样、出去什么样，一个字节都不多"。这一讲串起三个关键机制：**一个包的六跳旅程**、**节点上的 Felix / confd / BIRD 三个进程**、**"一份策略语义、四套数据面实现"** 带来的复杂度。[【跳转到 00:05】](https://www.bilibili.com/video/BV1tbhW68Evu/?t=5)

![本期要回答的四个问题：Calico 解决什么问题、与 Flannel 的分歧、节点上跑了什么、包的旅程](assets/为什么%20Calico%20不走%20Overlay：Calico%20源码深读/00005.webp)

---

## 一、Kubernetes 网络模型只提要求，不给实现

先把问题的起点摆正：K8s 对网络只提了三条要求，其余全部留给 CNI 去实现。

### 1.1 三条要求，真正的难题藏在第三条

[【跳转到 01:21】](https://www.bilibili.com/video/BV1tbhW68Evu/?t=81)

Kubernetes 的网络模型只提了三件事 [【跳转到 01:21】](https://www.bilibili.com/video/BV1tbhW68Evu/?t=81)：

1. **每个 Pod 有自己的 IP**，且在整个集群内唯一；
2. **任意两个 Pod 之间可以直接通信、不经过 NAT**，而且一个 Pod 不应该知道另一个 Pod 跑在哪台机器上；
3. **节点之间需要知道对方的 Pod 网段在哪里。**

前两条是**结果**，第三条才是**真正要解决的问题**：每台节点原本只知道自己的 Pod 地址，那别的节点上的 Pod 地址路由，是谁告诉它的？

**[【跳转到 01:41】](https://www.bilibili.com/video/BV1tbhW68Evu/?t=101) Kubernetes 故意没有规定手段**——这正是 Calico 和 Flannel 全部分歧的起点。

![K8s 只提要求、没给实现：三条网络要求里，跨节点的 Pod 路由才是真正要解决的问题](assets/为什么%20Calico%20不走%20Overlay：Calico%20源码深读/00081.webp)

---

## 二、同一个问题，两种解法：打隧道，还是走路由

既然 K8s 不管"跨节点 Pod 路由怎么来"，各家 CNI 就要自己选路。Flannel 和 Calico 给出了两种根本不同的答案。

### 2.1 Flannel：把网络变成一条条隧道（Overlay）

[【跳转到 02:01】](https://www.bilibili.com/video/BV1tbhW68Evu/?t=121)

Flannel 的做法是**打隧道**：每台节点上建一个虚拟网卡，把 Pod 包**封装进 UDP 或者 VXLAN** 里，发到对端节点再解开。好处是**底层网络完全不用改**；缺点也很直接：

- 每个包都要**多一层封装**，12~50 字节不等；
- **MTU 要跟着变小**（否则大包会被分片）；
- 出故障时，你看到的只是**隧道地址**，得剥开两层才能看出"是谁在跟谁说话"。

### 2.2 Calico：把每台主机当成一台路由器（Underlay / BGP）

Calico 选了另一条路：**不打隧道，把每台主机当成一台路由器**。每个节点把自己负责的 Pod 网段，通过 **BGP** 这个路由协议**宣告**给集群里其他节点 [【跳转到 02:30】](https://www.bilibili.com/video/BV1tbhW68Evu/?t=150)。于是：

- 包"进来什么样，出去还是什么样"，**一个字节都不多**，MTU 不变；
- `traceroute` 出来的就是**真实路径**；
- 代价是它要求底层网络**允许节点之间直接路由**——不过在同一个数据中心里，这个要求通常不算过分。

**一句话总结：Flannel 把网络搞成一条条隧道，Calico 把网络搞成一张路由表。**

![同一件事、两种解法：Flannel 打隧道（封装 + MTU 变小）与 Calico 走路由（BGP 宣告，不加字节）](assets/为什么%20Calico%20不走%20Overlay：Calico%20源码深读/00121.webp)

---

## 三、一个包的六跳旅程：cali 链、veth、路由表

理解了"两种解法"，再跟着一个包走一遍，就能看清每一跳是谁在做决定。

[【跳转到 02:55】](https://www.bilibili.com/video/BV1tbhW68Evu/?t=175)

假设 A 节点上有个 Pod，要给 B 节点上的 Pod 发包，过程中要经历六跳 [【跳转到 02:55】](https://www.bilibili.com/video/BV1tbhW68Evu/?t=175)：

1. **出项策略检查**：包在离开 Pod 之前，要先经过宿主机上 **cali 链**里的规则（eBPF 模式下，则是挂在网卡上的 eBPF 程序），这一跳决定它**能不能出去**；
2. **进入宿主机**：包通过 **veth pair**（虚拟网线）进入宿主机——Pod 里那块网卡在宿主机上的另一端，名字通常是 **`cali` 加一长串哈希**；
3. **查路由表**：宿主机查自己的路由表，目标 IP 一定落在 B 节点的网段里，所以命中的是一条**指向 B 节点 IP 的路由**——下一跳就是 B 节点；
4. **跨节点传输**：如果是 **no-encap** 模式，包就照原样发给 B 节点；如果是 **IPIP 或 VXLAN**，就在这一跳**封一层**；
5. **B 节点收包**：查自己的路由表，同时检查入项策略；
6. **写进目标 Pod**：包被送进目标 Pod，对端旅程结束。

整条路上**最值得盯住的是第三跳**，因为"给这条路写路由的"，在 Calico 里可能有两个不同的组件。

![一个包的完整旅程：出项策略检查 → veth 进宿主机 → 查路由表 → 跨节点 → 入项策略 → 目标 Pod](assets/为什么%20Calico%20不走%20Overlay：Calico%20源码深读/00175.webp)

---

## 四、节点上到底跑了什么：Felix、confd 与 BIRD

### 4.1 一个 calico-node 容器，三个进程

[【跳转到 04:01】](https://www.bilibili.com/video/BV1tbhW68Evu/?t=241)

每台节点上跑着一个 **calico-node 容器**（以守护进程形式部署），容器里拉起三个进程 [【跳转到 04:01】](https://www.bilibili.com/video/BV1tbhW68Evu/?t=241)：

| 进程 | 职责 | 类比 |
| --- | --- | --- |
| **Felix** | 数据面代理，整个项目最核心的组件：计算策略、生成规则、编程路由，并把节点状态上报 | 节点上的"执行者" |
| **confd** | 把 data store 里的状态**渲染成 BIRD 的配置文件** | 翻译官 |
| **BIRD** | 一个 BGP 守护进程，负责和其他节点**交换路由信息** | 网络里的"信使" |

除了这个容器，节点上还装着 **CNI 插件**（二进制由 kubelet 在创建 Pod 时调用）。再往下就是**宿主机内核里的东西**：一堆 **veth 对**、**`cali` 开头的链**、**ipset 集合**，还有**路由表**。这里有个细节：三个进程看着是三个，其实是**同一个二进制的不同子命令**，统一写成 `calico-component` 加上组件名。

![节点上跑了什么：Calico 的进程与内核对象（Felix / confd / BIRD、CNI 插件、cali 链、ipset、路由表）](assets/为什么%20Calico%20不走%20Overlay：Calico%20源码深读/00241.webp)

### 4.2 一条策略怎么从 API 走到每一台节点

[【跳转到 04:52】](https://www.bilibili.com/video/BV1tbhW68Evu/?t=292)

一条策略的传播链路是四步 [【跳转到 04:52】](https://www.bilibili.com/video/BV1tbhW68Evu/?t=292)：

1. **控制面组件把策略写进 Kubernetes 的自定义资源（CRD）或者 etcd**；
2. **节点上的 Felix 通过 watch 拿到变更**——但这里有个关键设计：在规模稍大的集群里，几百上千个节点不会各自去建 watch 连接，中间隔着一层叫 **Typha** 的代理，它**替所有节点连一次上游**，再把变更广播给所有节点，并且做**增量和缓存**，只发对端真正需要的东西；
3. **Felix 收到变更后不直接写规则**，而是先把它扔进一张**计算图**，重算出这台节点上"最终应该是什么样的期望状态"；
4. **期望状态被转换成 iptables / nftables 规则、ipset 集合或者路由**，原子地写进内核。

![一条策略怎么走到每个节点：CRD/etcd → Typha 代理 → Felix 计算图 → 内核规则](assets/为什么%20Calico%20不走%20Overlay：Calico%20源码深读/00292.webp)

---

## 五、那条路由到底是谁写的：Felix 还是 BIRD

[【跳转到 05:47】](https://www.bilibili.com/video/BV1tbhW68Evu/?t=347)

回到第三跳的疑问，答案是：**取决于这个 IP 池用的是哪种封装模式**，可能是 Felix，也可能是 BIRD [【跳转到 05:47】](https://www.bilibili.com/video/BV1tbhW68Evu/?t=347)：

| IP 池模式 | 谁写路由 | 方式 |
| --- | --- | --- |
| **VXLAN 池** | Felix（confd 和 BIRD 不参与） | 计算图里自己算出来直接写 |
| **IPIP 池** | 默认 Felix，可配给 BIRD | 默认直接写 |
| **no-encap 池**（完全不打隧道） | 默认 confd + BIRD | 靠 BGP 从邻居**学到**路由再写进内核，也可配给 Felix |

两种写法的本质不同：**Felix 是在计算图里自己算出来直接写；BIRD 是从邻居那里学来再写。** 从 **v3.13** 版本开始，默认组合是 **Felix 管 IPIP、BIRD 管 no-encap**，这也是为什么你会在同一台节点上，**既看到一个数据面代理，又看到一个路由进程**。

这里有个坑必须提醒：两边各有一个配置字段，**必须保持互补**。如果配重了，两个组件会同时去写同一条路由，现象是**路由反复翻动**，而且没有任何组件会检测出来并报错。

![集群路由到底谁写：Felix（计算图自算）还是 BIRD（BGP 学来）——由 IP 池的封装模式决定](assets/为什么%20Calico%20不走%20Overlay：Calico%20源码深读/00347.webp)

---

## 六、为什么 Calico 代码这么多：一份语义，四份实现

[【跳转到 06:49】](https://www.bilibili.com/video/BV1tbhW68Evu/?t=409)

### 6.1 数据面有四套，语义只有一套

先看第一层原因：**数据面有四套** [【跳转到 06:49】](https://www.bilibili.com/video/BV1tbhW68Evu/?t=409)：

1. **iptables**（最经典）：靠 `iptables-restore` 一次性写入规则，但规则一多匹配就慢；
2. **nftables**：新一代 netfilter 接口集合，匹配更高效，模式还能**自动跟随 kube-proxy 的选择**，保证两者用的是同一代 netfilter；
3. **eBPF 程序**：挂在网卡和 cgroup 上，直接跳过 iptables 那条长长的链，**性能最好也最复杂**；
4. **Windows**：走 HNS 和 HCN，和 Linux 那套几乎没有任何共用代码。

Felix 同一时刻只会跑其中**一套**，由 `bpfEnabled` 和 `nftablesMode` 两个配置决定。但关键在于：**上面四套数据面要表达的策略语义是同一套**——这就是它代码量大的第一个原因：**一份语义，四份实现**。

![同一套策略、四种落地方式：iptables / nftables / eBPF / Windows，同一份语义四份实现](assets/为什么%20Calico%20不走%20Overlay：Calico%20源码深读/00409.webp)

### 6.2 代码地图：35 万行都在哪

[【跳转到 07:35】](https://www.bilibili.com/video/BV1tbhW68Evu/?t=455)

整个仓库源码 **35.5 万行**（不含测试；加上测试是 72 万行），分布大致是 [【跳转到 07:35】](https://www.bilibili.com/video/BV1tbhW68Evu/?t=455)：

- **Felix 14 万行，占全仓约四成**——节点代理，装着计算图和四套数据面的实现；
- **libcalico-go 5.5 万行**——数据模型、客户端和 CRD 的实现，所有组件都依赖它；
- **kube-controllers 1.8 万行**——负责安装和生命周期；
- 往后还有 apiserver 1.2 万行，以及 cni-plugin、node、Typha 等各在数千到一万余行上下。

本系列前面几期集中在 **Felix、libcalico-go、Typha、node** 这四块，加起来约 21 万行，却覆盖了数据面的全部主干。五个入口文件是：`cmd` 目录下的组件入口（所有组件都是这一个二进制的子命令）、`felix/daemon.go`（Felix 主入口）、`felix/calc_graph.go`（计算图，Felix 的"大脑"）、`dataplane/driver.go`（数据面工厂）、以及 `node` 目录下的启动文件（节点初始化，写 node 资源与 BGP 配置）。

![三十五万五千行怎么分布：Felix 约四成、libcalico-go、kube-controllers、apiserver……](assets/为什么%20Calico%20不走%20Overlay：Calico%20源码深读/00455.webp)

### 6.3 它为什么"必须"这么复杂：六条绕不过去的理由

[【跳转到 09:58】](https://www.bilibili.com/video/BV1tbhW68Evu/?t=598)

Calico 早就不只是一个 CNI 插件，而是一个**网络与安全平台**——而平台的代价就是复杂度 [【跳转到 09:58】](https://www.bilibili.com/video/BV1tbhW68Evu/?t=598)。有六条理由：

1. **四套数据面 × 两种 data store**（K8s CRD 与 etcd），天然是倍数关系；
2. **策略模型比 K8s 原生丰富得多**：有分层策略、全局策略、灰度中的策略，还有主机端点；
3. **规模要求上千个节点不可能各自去 watch etcd**，所以必须有一层代理（Typha）；
4. **集群路由的编程被拆在 Felix 和 confd + BIRD 两边**，还得保证它们不打架；
5. **安全和加密是一等公民**：加密隧道、七层策略、流量日志全都挂在主路径上；
6. **同一份策略语义要同时表达在 Linux 和 Windows 两种内核上**。

![为什么它必须这么复杂：六条绕不过去的理由，看懂就不会觉得它是无谓的复杂](assets/为什么%20Calico%20不走%20Overlay：Calico%20源码深读/00598.webp)

---

## 小结

- **K8s 只提要求、不给实现**：真正要解决的是"跨节点的 Pod 网段路由由谁告诉节点"，这正是各家 CNI 的分歧起点。
- **两条路线**：Flannel 把网络搞成**一条条隧道**（Overlay，封装换通用性，代价是字节开销、MTU 变小、排障变难）；Calico 把网络搞成**一张路由表**（Underlay，用 BGP 宣告 Pod 网段，不加字节、MTU 不变、`traceroute` 即真实路径，代价是底层要允许节点间直接路由）。
- **一个包的六跳**：出项策略检查 → veth 进宿主机 → 查路由表（命中指向对端节点的路由）→ 跨节点（no-encap 原样发 / IPIP·VXLAN 封一层）→ 入项策略 → 目标 Pod。
- **节点上的三进程**：Felix（算策略、编程路由）、confd（渲染 BIRD 配置）、BIRD（换 BGP 路由），本质是同一二进制的不同子命令。
- **控制面靠 Typha 扇出**：上千节点不各自 watch etcd，由 Typha 连一次上游再广播增量。
- **路由归属**：VXLAN 池由 Felix 写、no-encap 池默认由 confd + BIRD 写；v3.13 起默认"Felix 管 IPIP、BIRD 管 no-encap"。
- **复杂度来源**：一份策略语义、四套数据面实现，再叠加丰富策略模型、聚合代理、路由拆分与双内核支持。

---

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| **CNI** | Container Network Interface，容器网络接口规范；负责给 Pod 配上网络 |
| **Overlay** | 叠加网络：把 Pod 报文封装进 UDP/VXLAN 等再跨节点传输（如 Flannel），通用性好但有封装开销 |
| **Underlay** | 底层网络：直接利用物理/三层网络转发，不额外封装（如 Calico 的 BGP 路由模式） |
| **BGP** | 边界网关协议；Calico 用它把各节点的 Pod 网段宣告给集群内其他节点，实现纯三层路由 |
| **IPIP / VXLAN** | 两种隧道封装协议；Calico 中的 IPIP、VXLAN IP 池会在一跳上封一层 |
| **no-encap** | 不封装模式；Calico 中完全不打隧道的 IP 池，靠 BGP 学路由直接转发 |
| **MTU** | 最大传输单元；隧道封装会让可用 MTU 变小，配置不当会引发分片与丢包 |
| **veth pair** | 一对虚拟网卡，像一根虚拟网线，连接 Pod 命名空间与宿主机命名空间 |
| **cali 链** | Calico 在宿主机 iptables 中创建、以 `cali` 开头的规则链 |
| **ipset** | 内核里的 IP 集合，用于高效匹配大量地址/端口 |
| **Felix** | Calico 节点上的数据面代理，计算策略、生成规则、编程路由 |
| **confd** | 把 data store 状态渲染成 BIRD 配置文件的组件 |
| **BIRD** | 一个 BGP 守护进程，负责与其他节点交换路由信息 |
| **Typha** | Calico 的聚合代理：替大量节点连一次上游，再广播增量变更 |
| **libcalico-go** | Calico 的数据模型与客户端库，所有组件都依赖它 |
| **CRD** | Custom Resource Definition，Kubernetes 自定义资源；Calico 用它承载策略等对象 |
