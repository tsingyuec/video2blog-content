# pause 容器：Pod 为什么需要一个「什么都不做」的容器

> 视频源：[深入理解 docker 和 kubernetes(k8s)--19.pause 容器](https://www.bilibili.com/video/BV1hYLvzrEGq/)（Bilibili，19 分 41 秒）。本文基于视频演说图文稿整理，时间戳可跳转到原视频对应位置。

## 本讲要解决的核心问题（SCQA）

**背景**：Kubernetes 里最小的、可被调度的计算单元是 **Pod**。一个 Pod 里可以只跑一个容器，也可以跑多个容器；而同一个 Pod 里的所有容器，**共享同一个网络命名空间（network namespace）**——也就是说，它们的「网络情况」是一样的。[【跳转到 00:15】](https://www.bilibili.com/video/BV1hYLvzrEGq/?t=15)

**冲突**：既然共享同一个网络命名空间，那它到底「用谁的」？如果以容器 A 的命名空间为准，就得让 A 先启动、B 再「加入」进去；反过来也一样。这两种方案都有毛病：一是对**容器的启动顺序**提出了要求；二是那个「被借用」的容器一旦崩溃、被默认策略重启，它重启后拿到的可能是**一个新的命名空间**，于是两个容器就落在不同的命名空间里，网络直接出问题。[【跳转到 01:28】](https://www.bilibili.com/video/BV1hYLvzrEGq/?t=88)

**疑问**：有没有一个「稳定的、不属于任何业务容器」的东西，专门来**持有**这个共享的网络命名空间，让所有业务容器都去加入它？

**回答（中心思想）**：有，它就是 **pause 容器**（也叫 infra 容器、根容器）。Kubernetes 在创建 Pod 时会**先**创建一个几乎不占资源、由 pause 镜像启动的「基础设施容器」，让它持有网络命名空间；随后创建的业务容器，全部**加入** pause 的网络命名空间。这样既不用挑业务容器来「借」命名空间，也不怕业务容器重启，Pod 的网络就有了一个稳定的锚点。[【跳转到 03:10】](https://www.bilibili.com/video/BV1hYLvzrEGq/?t=190)

本讲按「**问题的由来 → pause 的解法 → 动手验证**」三步展开，最后用 containerd + crictl 在真实节点上把 pause 容器「揪」出来。

## 一、问题的由来：共享的网络命名空间该「挂」在谁身上

结论先说：**Pod 内所有容器共享一个网络命名空间，但这个命名空间既不能属于这里的任何一个业务容器**。

### 1.1 先用一个「两容器 Pod」把问题摆出来

视频里沿用了上一讲的那个「两容器」配置文件（`containers` / `two-containers`）：在一个 Pod 里定义了两个容器——一个是 `B1`，镜像用 **busybox**；另一个是 `N1`，镜像用 **nginx**。[【跳转到 00:53】](https://www.bilibili.com/video/BV1hYLvzrEGq/?t=53)

因为这两个容器在同一个 Pod 里，它们的网络是一样的，也就是**共享同一个网络命名空间**。这时问题就来了：这个命名空间到底用的是 `B1` 的，还是 `N1` 的？[【跳转到 01:03】](https://www.bilibili.com/video/BV1hYLvzrEGq/?t=63)

![同一个 Pod 里的两个容器（B1、N1）共享同一个网络命名空间，那这个命名空间该用谁的？](<assets/深入理解docker和kubernetes(k8s)--19.pause容器/00063.webp>)

### 1.2 两种「借命名空间」的方案都站不住脚

如果要用 `B1` 的命名空间，那就意味着 **B1 必须先启动**，然后 `N1` 再加入 B1 的命名空间；如果要用 `N1` 的，那就反过来。仔细想想，这两种方案都不是好方案：[【跳转到 00:88】](https://www.bilibili.com/video/BV1hYLvzrEGq/?t=88)

- **第一个毛病**：对容器的**启动顺序**有了要求——到底谁先谁后，得看「谁贡献命名空间」。
- **第二个毛病**：以某个容器的命名空间为「公用命名空间」时，如果这个容器崩溃退出了，按容器的默认策略**它会被重启**；而它重启之后拿到的命名空间可能**跟以前不一样了**。[【跳转到 01:43】](https://www.bilibili.com/video/BV1hYLvzrEGq/?t=143)

结果就是：重启的容器跑到**新的命名空间**里，另一个容器还留在**旧的命名空间**里，两者的网络命名空间不再一致，Pod 内的网络就崩了。[【跳转到 01:57】](https://www.bilibili.com/video/BV1hYLvzrEGq/?t=157)

![两种「让某个业务容器贡献命名空间」的方案都会因启动顺序与容器重启而失效](<assets/深入理解docker和kubernetes(k8s)--19.pause容器/00113.webp>)

**于是思路浮出水面**：我们用的网络命名空间，**既不用 B1 的、也不用 N1 的**，更不会用任何一个**用户自定义容器**的命名空间——而是用一个专门为此准备的容器的命名空间。[【跳转到 02:45】](https://www.bilibili.com/video/BV1hYLvzrEGq/?t=165)

![解决思路：共享的网络命名空间既不用 B1 的、也不用 N1 的](<assets/深入理解docker和kubernetes(k8s)--19.pause容器/00165.webp>)

## 二、解法：让一个「什么都不做」的 pause 容器来持有命名空间

结论：这个专门用来「持有命名空间」的容器就是 **pause 容器**，它还有一个名字叫 **infra 容器**（infrastructure，基础设施之意）。[【跳转到 03:28】](https://www.bilibili.com/video/BV1hYLvzrEGq/?t=208)

### 2.1 pause 容器的四个特征

- **它由 K8s 自动创建、注入每个 Pod**，而不是用户定义的。**对用户不可见**——你并不知道它存在，但它确确实实存在。[【跳转到 03:28】](https://www.bilibili.com/video/BV1hYLvzrEGq/?t=208)
- **创建顺序上它是「第一个」**：启动 Pod 时，会**优先创建 pause 容器**，等它创建好、有了自己的网络命名空间之后，再去创建用户定义的业务容器；业务容器统统**加入 pause 的命名空间**。这样，一个 Pod 里所有容器就都落在同一个网络命名空间里了。[【跳转到 03:53】](https://www.bilibili.com/video/BV1hYLvzrEGq/?t=233)
- **它极其轻量且稳定**：pause 容器的镜像非常小，**大概只有几百 K**；运行后它其实只执行一个 `pause` 函数——也就是「暂停」，**基本上什么都不做**，消耗的资源非常非常小，而且很稳定。[【跳转到 04:18】](https://www.bilibili.com/video/BV1hYLvzrEGq/?t=258)
- **它是命名空间的 holder（持有者）**：正因为稳定又不占资源，pause 就充当整个 Pod 网络命名空间的「持有者」，为 Pod 内的其他容器提供一个**共同的网络基础环境**。[【跳转到 04:43】](https://www.bilibili.com/video/BV1hYLvzrEGq/?t=283)

![pause 容器（infra 容器）由 K8s 自动创建、对用户不可见，专门充当网络命名空间的持有者](<assets/深入理解docker和kubernetes(k8s)--19.pause容器/00208.webp>)

![pause 镜像只有几百 K，运行后执行一个 pause 函数，几乎不消耗资源、非常稳定](<assets/深入理解docker和kubernetes(k8s)--19.pause容器/00258.webp>)

一句话记住这个设计：**「加一个稳定的中间层」**——不是让某个业务容器来当「房东」，而是让一个几乎「什么都不做」的 pause 容器当「房东」，业务容器都是「租客」。

## 三、动手验证：用 containerd + crictl 把 pause 容器揪出来

结论：**pause 容器虽然对用户不可见，但在运行时层面它是「实打实」存在的一个容器**，用 crictl 能清清楚楚地把它以及它持有的命名空间找出来。

### 3.1 起一个两容器 Pod

我们在 default 命名空间里目前没有任何 Pod，先把它启动起来。启动后可以看到，Pod 被调度到了 **worker2** 这个节点上，并且里面有两个容器。[【跳转到 05:22】](https://www.bilibili.com/video/BV1hYLvzrEGq/?t=322)

![启动一个包含两个容器的 Pod，它被调度到 worker2 节点上](<assets/深入理解docker和kubernetes(k8s)--19.pause容器/00322.webp>)

因为底层用的是 **containerd** 作为容器运行时，所以接下来用 **crictl** 这个命令来操作。

### 3.2 crictl ps：看到的是「进程」，还能看到 pod id

crictl 加 `ps` 看到的其实是**进程**——因为一个容器最终要体现为一个进程。这里能看到 `N1` 和 `B1` 两个进程，也就是两个容器。看它们的相关信息：首先是 **container id**；再往下一行是 **pod id**。`B1` 的 pod id 与 `N1` 的 pod id **肯定是一样的**（它们属于同一个 Pod）。[【跳转到 06:12】](https://www.bilibili.com/video/BV1hYLvzrEGq/?t=372)

![crictl ps 列出 B1、N1 两个容器，并给出各自的 container id 与共用的 pod id](<assets/深入理解docker和kubernetes(k8s)--19.pause容器/00372.webp>)

### 3.3 crictl inspectp：Pod 里赫然有一个 pause:3.6 镜像

把 pod id 复制出来，用 `crictl inspectp`（display status of one or more pods）看 Pod 的信息；`crictl inspect`（不带 p）则是看 container 的。[【跳转到 07:02】](https://www.bilibili.com/video/BV1hYLvzrEGq/?t=422)

在 Pod 的基本信息里，能看到 Pod 的 name、所在的命名空间、id、IP 地址等等。[【跳转到 07:52】](https://www.bilibili.com/video/BV1hYLvzrEGq/?t=472) 一路往下翻，会依次看到：

- `pid`——进程 id 号；
- `image`——这里写着的居然是 **`pause:3.6`**！这说明 pause 容器**确确实实是有的**，只不过对用户而言「好像不存在」而已；
- 还配有 hostname、DNS 相关配置，以及一堆挂载、cgroup 等等。[【跳转到 08:17】](https://www.bilibili.com/video/BV1hYLvzrEGq/?t=497)

![crictl inspectp 查看 Pod 基本信息：名称、命名空间、id、IP 等](<assets/深入理解docker和kubernetes(k8s)--19.pause容器/00447.webp>)

![Pod 的 image 字段赫然是 pause:3.6——pause 容器确实存在，只是对用户不可见](<assets/深入理解docker和kubernetes(k8s)--19.pause容器/00497.webp>)

### 3.4 从进程号找到命名空间

在 inspectp 里拿到的 `pid`（这里是 2011 442），正好能用 `ps -ef` 在节点上对上号——因为容器的本质就是一个进程，这个进程就是 **pause 容器**。[【跳转到 09:45】](https://www.bilibili.com/video/BV1hYLvzrEGq/?t=585)

![用 ps -ef 找到 pause 容器对应的进程（PID 2011 442）](<assets/深入理解docker和kubernetes(k8s)--19.pause容器/00585.webp>)

所有容器都是一个进程，都会在 `/proc` 下有一个以进程号为名的子目录；`cd` 进去再 `cd ns`，就相当于进入了这个 pause 进程，能看到它现在持有的**所有命名空间**。[【跳转到 10:10】](https://www.bilibili.com/video/BV1hYLvzrEGq/?t=610)

![在 /proc/<pid>/ns 下查看 pause 进程持有的各类命名空间](<assets/深入理解docker和kubernetes(k8s)--19.pause容器/00610.webp>)

用同样的办法（`crictl inspect` 拿到 container id → 进程号 → `/proc/<pid>/ns`），把 `N1`、`B1` 的命名空间也一并取出来。

### 3.5 对比三类容器的命名空间：谁共享、谁独立

把 pause、`N1`、`B1` 三者的命名空间摆在一起对比：

- **net（网络）**：pause 是 `4026538208`，`N1` 和它**完全一样**——说明 `N1`、`B1` 实际上**加入的正是 pause 那个网络命名空间**。[【跳转到 13:16】](https://www.bilibili.com/video/BV1hYLvzrEGq/?t=796)
- **mnt（挂载）**：三个容器的编号各不相同（末尾分别是 283 / 286 / 279），**不一样**。因为 mnt 管的是挂载，挂载会影响容器的根目录——所以在不同容器里 `ls /` 看到的东西本来就不一样。[【跳转到 13:41】](https://www.bilibili.com/video/BV1hYLvzrEGq/?t=821)
- **IPC**：是**一样的**。[【跳转到 14:06】](https://www.bilibili.com/video/BV1hYLvzrEGq/?t=846)
- **pid**：三个编号也不一样（282 / 287 / 285）。正因为 pid 命名空间不同，所以在不同容器里 `ps` 看到的结果也不一样。[【跳转到 14:31】](https://www.bilibili.com/video/BV1hYLvzrEGq/?t=871)
- **UTS**：是**一样的**——UTS 决定域名之类的信息，本质上还是跟网络相关，既然大家同一个网络，UTS 一致也就顺理成章。（视频里还观察到 user 命名空间编号也一致。）[【跳转到 14:56】](https://www.bilibili.com/video/BV1hYLvzrEGq/?t=896)

![对比 net 命名空间：N1、B1 都加入了 pause 的 net 命名空间，所以编号相同](<assets/深入理解docker和kubernetes(k8s)--19.pause容器/00796.webp>)

![对比 mnt 命名空间：三个容器各自不同，因为挂载决定了各自的根目录](<assets/深入理解docker和kubernetes(k8s)--19.pause容器/00821.webp>)

### 3.6 进容器实测：网络共享、文件系统独立

进入 `N1`（nginx）和 `B1` 两个容器里做验证：

- 在 nginx 容器里 `ls /`，和 busybox 容器里 `ls /` 看到的**内容不一样**——因为它们的 **mnt 命名空间不同**。
- 但 `cat /etc/hostname` 两边**一样**（都是 `two-containers`），`/etc/resolv.conf`（域名服务器地址）也**一样**——因为它们在**同一个网络命名空间**里。
- 再用 `wget` 访问本机的 80 端口，能**成功拿到 nginx 的 index 主页文件**，这间接证明了这两个容器确实在**同一个网络空间**里。
- 另外，busybox 容器里有 `ps` 命令，而 nginx 容器里**没有**（nginx 主要提供 web 服务，命令少一些）；也正因为 pid 命名空间不同，两个容器里 `ps` 看到的结果本来就不一样。[【跳转到 14:56】](https://www.bilibili.com/video/BV1hYLvzrEGq/?t=896)

![进入容器实测：/etc/hostname 相同、wget localhost 能拿到 nginx 首页，证明两容器共享网络](<assets/深入理解docker和kubernetes(k8s)--19.pause容器/00896.webp>)

## 小结

- **问题**：Pod 内容器共享一个网络命名空间，但把它「挂在」任何一个业务容器上都不行——会引入启动顺序依赖，且该容器重启后命名空间会变，导致网络错乱。
- **解法**：引入一个专门的基础设施容器 **pause 容器（infra 容器）**。它由 K8s 自动创建、对用户不可见，先于业务容器创建，持有网络命名空间；业务容器全部加入它的命名空间。
- **为什么用它**：镜像极小（几百 K）、运行后只执行 `pause` 函数、几乎不占资源且极其稳定，是理想的「命名空间持有者（holder）」。
- **验证（containerd + crictl）**：
  - `crictl ps` 列出容器与它们共用的 pod id；
  - `crictl inspectp <pod-id>` 能看到 Pod 的 `image` 是 **`pause:3.6`**，证明 pause 容器真实存在；
  - 用进程号进入 `/proc/<pid>/ns`，把 pause、N1、B1 的命名空间逐一取出；
  - 对比结果：**network、UTS、IPC 共享**（视频里还观察到 user 也一致），而 **pid、mnt 各自独立**；
  - 进容器实测：`ls /` 不同（mnt 不同）、`/etc/hostname` 相同、`wget localhost` 能拿到 nginx 首页（网络共享）。
- **一句话记忆**：pause 容器是 Pod 网络的「锚」——它什么都不干，只负责把命名空间稳稳地固定在 Pod 的整个生命周期里。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| Pod | Kubernetes 最小的可调度计算单元，一个 Pod 含一个或多个容器，容器间共享网络命名空间 |
| 网络命名空间（network namespace） | Linux 内核提供的网络隔离单元；同一 Pod 内的容器共享它，因此网络视图一致 |
| pause 容器 | 也叫 infra 容器 / 根容器；由 K8s 自动创建、对用户不可见，专门持有 Pod 的网络命名空间 |
| infra 容器 | pause 容器的别名，infrastructure 即「基础设施」 |
| 命名空间 holder | pause 容器的角色：作为一个稳定不变量，持有 Pod 级网络命名空间 |
| containerd | 本讲实验使用的底层容器运行时 |
| crictl | 一个类 docker 的 CRI 命令行工具，用于调试节点上的容器与 Pod |
| `crictl ps` | 列出容器（进程），给出 container id 与 pod id |
| `crictl inspectp` | 查看 Pod（sandbox）信息，如名称、命名空间、id、IP、image 等 |
| `pause:3.6` | inspectp 中 Pod 的 image 字段，暴露了 pause 容器的存在 |
| `/proc/<pid>/ns` | 查看某个进程持有的各类命名空间（net、mnt、pid、IPC、UTS、user 等） |
| mnt 命名空间 | 挂载命名空间，决定容器根目录的挂载视图；Pod 内各容器相互独立 |
| pid 命名空间 | 进程号命名空间，决定容器内能看到的进程；Pod 内各容器相互独立 |
| IPC 命名空间 | 进程间通信命名空间；同一 Pod 的容器共享，便于容器间 IPC |
| UTS 命名空间 | 决定主机名/域名等；同一 Pod 的容器共享 |
