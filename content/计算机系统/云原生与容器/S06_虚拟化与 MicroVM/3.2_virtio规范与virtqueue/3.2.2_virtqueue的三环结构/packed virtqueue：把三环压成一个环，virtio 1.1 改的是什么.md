# packed virtqueue：把三环压成一个环，virtio 1.1 改的是什么

> 视频来源：[Virtio 1.1 What's new in the next version of the Virtio standard](https://www.youtube.com/watch?v=T61JG07XHc0)（YouTube · FOSDEM 2018 · Jens Freimann，Red Hat）｜时长约 25 分钟（后半段是同一会场的另一场演讲，与本主题无关）
> 简要导读：这支演讲是 virtio 1.1 里 packed virtqueue 的提出者自述——为什么要改掉 virtio 1.0 的三环布局、新布局长什么样、实测拿到多少收益，以及 virtio 1.1 顺带推进的几件事（vDPA、vhost-pci / virtio-vhost-user、virtio-bonding）。本文前半讲布局改造，后半把演讲里"其他变化"压缩成一节，方便对照。

## 本讲要解决的核心问题（SCQA）

**背景**：virtio 1.0 的 split virtqueue 把一条请求的信息拆在三块内存里——descriptor table 记缓冲区地址与长度，available ring 记"哪些链可以处理了"，used ring 记"哪些链处理完了"。这套结构在软件里跑了多年，工作得很好。

**冲突**：一条请求的信息散在多个数据结构里，意味着每搬一个缓冲区，host 与 guest 的 CPU 之间要来回同步至少五块内存区域。而 CPU 之间共享内存不是免费的：一方访问另一方改过的内存，会触发缓存一致性协议消息与 cache miss，直接抬高通信延迟。同时，这套布局对硬件实现来说太复杂——演讲者说，等了很多年也没等到硬件支持 virtio，有公司试过又停下了。

**疑问**：能不能把一条请求需要的信息**尽量塞进同一个数据结构**，既减少 cache miss，又让硬件实现变简单？

**回答（中心思想）**：virtio 1.1 的 **packed virtqueue** 直接砍掉 available ring、used ring 和 `next` 字段，只留**一个 descriptor ring**：guest 按顺序把 descriptor 写进环里，翻转 descriptor 里的 **available 位**表示"归你了"；设备处理完，把 **descriptor ID** 写回并翻转 **used 位**表示"还给你"。双方各自维护一个**单比特回绕计数器**，用来在环绕回之后仍能分辨"哪些是新放的"。这就是"三环压成一环"的全部内容。

## 一、先说清 split 的问题：一条请求的信息散在五处

### 1.1 复习：split virtqueue 的三块内存

演讲先用一张图复述了 virtio 1.0 的布局（[【跳转到 07:11】](https://www.youtube.com/watch?v=T61JG07XHc0&t=431)）：

![split virtqueue 的结构：上方 descriptor table 存 addr、len、next，左右两个环分别是 available ring 与 used ring，各自带一个 idx](assets/packed%20virtqueue：把三环压成一个环，virtio%201.1%20改的是什么/00431.webp)

文字版（[【跳转到 04:41】](https://www.youtube.com/watch?v=T61JG07XHc0&t=281)）：

1. 每条请求的数据放在一个缓冲区里，缓冲区在驱动与设备之间共享；
2. 缓冲区的地址与长度写进 16 字节的 descriptor，descriptor 集中放在 descriptor table 里；
3. 缓冲区不连续时，用 descriptor 里的 `next` 字段把多个 descriptor 串成链；
4. 一条请求用**链头下标**（head index，16 位、指向表里第一个 descriptor）来标识；
5. 链头下标放进 available ring，驱动另外维护一个 available idx 告诉设备"哪些项有效"；
6. 设备执行完，把链头下标写进 used ring，同时写回"缓冲区被用了多少字节"，然后递增 used idx，告诉驱动"这条用完了"。

### 1.2 五块内存 = 至少五次 cache miss

演讲把这件事拉低到 CPU 层面（[【跳转到 05:56】](https://www.youtube.com/watch?v=T61JG07XHc0&t=356)）：host 与 guest 本质上是在**用共享内存给两个 CPU 传消息**。当一个 CPU 访问另一个 CPU 改过的内存时，两边要交换缓存一致性协议消息来同步缓存；在某些架构上，这还会造成 cache miss。交换的消息数、miss 的次数，直接决定通信延迟。

于是可以数一下：split virtqueue 由**五个部分**组成，一个缓冲区在 host 与 guest 之间走一趟，这五个部分每个都至少被读一次、写一次。也就是说，**每个缓冲区至少五次 cache miss**——这还是在不考虑批量处理的情况下；做了批量会好一点，但好不了多少（[【跳转到 06:46】](https://www.youtube.com/watch?v=T61JG07XHc0&t=406)）。

结论很直接：**问题的根源不是"环"本身，而是"一条请求的信息被摊在多个数据结构里"**。要降开销，就得把信息打包进一个结构（[【跳转到 07:36】](https://www.youtube.com/watch?v=T61JG07XHc0&t=456)）。

## 二、packed 的设计：一个环、两个位、一对计数器

![packed virtqueue 的两条动机写在标题页上：让 virtio 更容易在硬件里实现，以及通过优化环布局拿到性能收益](assets/packed%20virtqueue：把三环压成一个环，virtio%201.1%20改的是什么/00256.webp)

### 2.1 砍掉两个环和 `next`，只留 descriptor ring

提案的做法是（[【跳转到 08:01】](https://www.youtube.com/watch?v=T61JG07XHc0&t=481)）：

- **完全去掉 available ring、used ring 以及 `next` 结构**；
- 让 guest **按顺序**把 descriptor 一个接一个写进新的 descriptor ring；
- 在每个 descriptor 里**新增三个字段**：`flags`（含 available 与 used 两个位）和 `descriptor ID`。

![packed 的 descriptor ring：驱动把可用 descriptor 按顺序写进环，设备在同一个环里写回已用状态；descriptor 字段是 addr、len、id、avail、used](assets/packed%20virtqueue：把三环压成一个环，virtio%201.1%20改的是什么/00481.webp)

交接协议变成"翻位"：

- 要让缓冲区可用，guest 把 descriptor 写进环，然后**翻转 available 位**——这表示"host 可以消费它了"；
- host 可以**按任意顺序**处理这些 descriptor（不再受环的先后约束）；
- 每个 descriptor 带一个 ID，host 处理完把 **descriptor ID 写回环里**，并**翻转 used 位**——这明确告诉 guest"这一项用过了"，guest 于是可以复用它、或者重新把它置为可用。

### 2.2 为什么还需要"计数器"：环绕回之后怎么分辨新旧

只靠位翻转有个坑：环会绕回。如果某一轮里有些 descriptor 被跳过了没碰，绕回之后光看"位"是分不清它是"上一轮留下的"还是"这一轮新放的"。

演讲的解法是：设备与驱动各自维护一个**内部计数器，只需要一个比特**，从 1 开始，**每绕过环里最后一个 descriptor 就翻转一次**。这个比特就体现在 descriptor 的 available / used 位里（[【跳转到 09:16】](https://www.youtube.com/watch?v=T61JG07XHc0&t=556)）。

![descriptor 状态图：环上方是驱动的 Available wrap counter，下方是设备的 Used wrap counter，每个 descriptor 里记着 avail 与 used 两个位](assets/packed%20virtqueue：把三环压成一个环，virtio%201.1%20改的是什么/00556.webp)

假设环被清零初始化：

- 第一轮遍历环、标记 descriptor 可用时，available 位设为 1；下一轮再标记时设为 0；再下一轮又设 1……依此类推；
- 同理，设备标记"已用"时，第一轮把 used 位设成 1，然后 0、再 1……

这样做的收益是（[【跳转到 10:06】](https://www.youtube.com/watch?v=T61JG07XHc0&t=606)）：**即使环已经绕回，双方仍然能识别出"新出现的可用 descriptor"**，包括那些在上一轮被跳过、这一轮才被放进去的项。换句话说，计数器把"环绕回"这个边界问题，转化成了"位是否等于当前计数器值"的一次比较。

### 2.3 与 split 的对照

| 维度 | split virtqueue（virtio 1.0） | packed virtqueue（virtio 1.1） |
| :--- | :--- | :--- |
| 内存结构 | descriptor table + available ring + used ring | 单个 descriptor ring |
| 请求标识 | 链头下标（head index） | descriptor ID |
| 交接信号 | 两个 `idx` 计数器分别推进 | 每个 descriptor 的 available / used 位翻转 |
| 链式缓冲区 | `next` 字段 + `NEXT` 标志 | 去掉 `next` 结构，按顺序写入 |
| 处理顺序 | 由环的顺序表达 | 设备可任意顺序处理 |
| 绕回处理 | `idx` 自由运行、取模定位槽位 | 单比特回绕计数器 |
| 主要收益 | 结构清晰、生态成熟 | 信息集中，减少 cache miss，便于硬件实现 |

## 三、代价与边界：演讲里能读出的两点

演讲的重点在"为什么改"和"改成什么"，没有专门列代价清单。但从它描述的机制里，可以读出两处结构性代价：

**第一，顺序信息从"环的位置"搬到了"descriptor 的 ID 与位"。** split 布局里，available ring 的先后顺序天然表达了"先放先处理"；packed 布局明确允许 host 按任意顺序处理，于是每一条请求都必须靠 descriptor ID 才能被认回来。驱动侧要自己维护 ID 分配与那个回绕比特，逻辑比"读 idx、取模、拿下标"要重。

**第二，兼容性要靠 feature 协商，且三处实现都要改。** 演讲说得很清楚：这个提案当时还在 virtio 邮件列表上讨论，DPDK 有原型（且是最先做的），QEMU 与 Linux 也在做；现场提问问"QEMU 的改动要多久"，回答是"先把 DPDK 上游化，QEMU 的实现已经开始，需要几个月"（[【跳转到 19:16】](https://www.youtube.com/watch?v=T61JG07XHc0&t=1156)）。新布局不是替换旧布局，而是并存、靠特性位协商。

顺带一提，演讲还给了一条"怎么参与规范"的路径：规范源码在 GitHub 上，改 LaTeX、编译、检查排版，然后订阅 virtio 邮件列表，发一行 patch 预订一个特性位，走一周投票，两周后特性就进规范了（[【跳转到 09:46】](https://www.youtube.com/watch?v=T61JG07XHc0&t=586)）。

## 四、实测：64 字节小包从 18.8 到 22.6 Mpps

演讲者说这是演讲前唯一做完的一次真实测试（[【跳转到 10:56】](https://www.youtube.com/watch?v=T61JG07XHc0&t=656)）：

![性能测试环境：DPDK 的 PVP 参考测试、Xeon E5-2667 v4、host 与 guest 都是 RHEL 7.4、Moongen 打流、可接受丢包 0.05%、DPDK 17.11](assets/packed%20virtqueue：把三环压成一个环，virtio%201.1%20改的是什么/00656.webp)

- 测试环境：DPDK 的 PVP（physical–virtual–physical）参考测试；CPU 为 Intel Xeon E5-2667 v4 @ 3.20GHz；host 与 guest 都是 RHEL 7.4；打流工具 Moongen；可接受丢包 0.05%；DPDK 17.11；补丁在 GitHub 上。
- 结果：**64 字节小包从 18.8 Mpps 提升到 22.6 Mpps**；更大的包在这套环境里直接打到线速，所以看不出差别（演讲者说还在补大包的测试）。

这也解释了为什么 packed 的动机里同时写着两条：**让 virtio 更容易在硬件里实现**，以及**性能收益（优化环布局）**。

## 五、virtio 1.1 顺带推进的另外三件事

演讲后半段（约 13:26 之后）讲了三个与 virtio 相关、但不属于 packed 布局的项目。它们和"队列结构"关系不大，这里只做定位，细节留给对应小节。

### 5.1 vDPA：让硬件直接读写 vring

![vDPA 的结构：控制面仍由 QEMU 模拟（PCI 配置空间、设备寄存器），数据面交给能直接读写 vring 的加速设备](assets/packed%20virtqueue：把三环压成一个环，virtio%201.1%20改的是什么/00806.webp)

vDPA（virtual Datapath Accelerator）由 Intel 在 DPDK 里发起。它保留了 virtio"前后端解耦"的好处——在云环境里方便热迁移——同时把数据面交给一块**能直接读写 vring 格式**的硬件，从而拿到接近 SR-IOV 的数据面性能（[【跳转到 13:26】](https://www.youtube.com/watch?v=T61JG07XHc0&t=806)）。

它的分工是：**控制面仍然模拟**（PCI 配置空间、设备寄存器，性能不敏感），**数据面由混合设备直接写进 vring**；kick 走共享内存，中断走 irqfd，控制面消息由 vhost-user 建立。演讲也点出当时的短板：还没有用虚拟 IOMMU，这是待改进项。

至于"为什么不干脆把整块设备直通给 guest"，演讲给了四条理由：virtio 规范一直在演进，硬件实现跟不上；物理功能带的特性与元数据远多于虚拟功能；直通之后热迁移更难；而 virtio 的前后端解耦让后端可以自由替换。

### 5.2 vhost-pci 与 virtio-vhost-user：让 VM 之间直接通信

这一组解决的是**东西向流量**：一堆虚拟网络功能（防火墙、IDS、路由器）互相转发包时，通常要先绕进宿主里的虚拟交换机，代码路径很长、扩展性一般。能不能让包直接从一台 VM 到另一台 VM，不经过宿主代码路径？（[【跳转到 15:31】](https://www.youtube.com/watch?v=T61JG07XHc0&t=931)）

![vhost-pci 设计：各 VM 里放 virtio 设备驱动，中间一台 VM 里跑 vhost-pci server，彼此通过 Unix socket 讲 vhost-pci 协议](assets/packed%20virtqueue：把三环压成一个环，virtio%201.1%20改的是什么/01156.webp)

做法是：在 VM 里引入一组新的 virtio PCI 设备，把 vhost-user server 放进其中一台 VM 作为中心组件，彼此用 Unix socket 连接、讲现有的 vhost-user 协议。这个方向后来演化成 **virtio-vhost-user**——把 vhost 设备后端**搬进 guest**（[【跳转到 20:56】](https://www.youtube.com/watch?v=T61JG07XHc0&t=1256)）：

![virtio-vhost-user：VM 1 里跑 vhost 设备后端，VM 2 里是普通的 virtio-net 驱动，两者数据面靠共享内存，控制面走 vhost-user socket](assets/packed%20virtqueue：把三环压成一个环，virtio%201.1%20改的是什么/01281.webp)

- VM 2 看到的是一个**普通的 virtio-net 设备**；VM 1 用现有的 vhost-user 能力，就像在对宿主的 vhost-user 后端说话；
- VM 1 的 QEMU 把 vhost-user 协议消息**隧道**到新的 virtio-vhost-user 设备，于是 VM 1 里的软件就成了 VM 2 的 vhost-user 后端；
- 因为协议相同，**现有的 vhost-user 后端软件可以复用**；代价是要新写一个 virtio-vhost-user 的 PCI 驱动；
- 数据面（vhost 设备的环）通过共享内存访问，**不需要交换 vhost-user 消息，也不产生 VM exit**；即使使用中断，也可以走轻量的 ioeventfd，QEMU 不参与。

![virtio-vhost-user 的定位：guest 可以充当 vhost 设备后端，为同一云环境里的其他 guest 提供 virtio 设备，VM 之间走无 exit 的快路径](assets/packed%20virtqueue：把三环压成一个环，virtio%201.1%20改的是什么/01256.webp)

演讲者特别说明：这套东西目前只对网络设备成立，块设备等还不行。

### 5.3 virtio-bonding：迁移时把快路径换成 virtio

一句话的想法：在 guest 里做**透明 bonding**，不需要用户做复杂配置。给 virtio 设备加一个特殊特性位，guest 看到它之后就去寻找能与之绑定的 SR-IOV 设备；平时数据走 SR-IOV 的快路径，**要迁移时把 SR-IOV 的链路 down 掉、切到 virtio 设备**；到了目标机再找新的 SR-IOV 设备接管数据面，找不到就一直用 virtio（[【跳转到 17:11】](https://www.youtube.com/watch?v=T61JG07XHc0&t=1031)）。

演讲的结论是：virtio 1.1 会是一个比较大的版本，改动主要围绕 packed virtqueue，另外还有一些硬件实现需要的东西（[【跳转到 18:26】](https://www.youtube.com/watch?v=T61JG07XHc0&t=1106)）。

## 小结

- split virtqueue 的痛点不是"环"本身，而是**一条请求的信息被摊在五个部分里**：每搬一个缓冲区，host 与 guest 之间至少五次 cache miss。
- packed virtqueue 的改造只有三句话：**去掉 available ring、used ring 与 `next`，只留一个 descriptor ring；每个 descriptor 加 `flags`（available / used 位）与 `descriptor ID`；双方各维护一个单比特回绕计数器。**
- 交接协议从"推进两个 `idx`"变成"翻转两个位"：guest 翻 available 位交付，设备写回 ID 并翻 used 位归还；设备可以按任意顺序处理。
- 回绕计数器解决的是"环绕回之后如何分辨新旧"——比较位与计数器值即可，包括上一轮被跳过的项。
- 代价是顺序信息从"环的位置"转移到"ID 与位"，驱动侧逻辑变重；新旧布局并存，靠特性位协商，DPDK / QEMU / Linux 三处都要改。
- 实测（DPDK PVP、Xeon E5-2667 v4、64 字节包）：18.8 Mpps → 22.6 Mpps；更大的包直接打满线速。
- virtio 1.1 同期还推进了 vDPA（硬件直接读写 vring）、vhost-pci / virtio-vhost-user（VM 之间直连）、virtio-bonding（迁移时切快路径）。

## 关键术语速查

| 术语 | 一句话解释 |
| :--- | :--- |
| split virtqueue | virtio 1.0 的队列布局：descriptor table + available ring + used ring 三块内存 |
| packed virtqueue | virtio 1.1 的队列布局：单个 descriptor ring，用 available / used 位表达交接 |
| descriptor ID | packed 布局里给每个 descriptor 的编号，设备处理完后写回，用来认领请求 |
| available 位 | 驱动翻转它表示"这个 descriptor 归设备了" |
| used 位 | 设备翻转它表示"这个 descriptor 用完了，可以还给你" |
| wrap counter | 单比特回绕计数器，每绕过环尾翻转一次，用来在环绕回后分辨新旧 |
| cache miss | CPU 访问另一个 CPU 改过的缓存行时产生的缺失，是跨 CPU 共享内存通信的主要延迟来源 |
| Mpps | 每秒百万包，网络数据面的吞吐单位 |
| vDPA | 让硬件直接读写 vring 的数据面加速方案，控制面仍模拟 |
| virtio-vhost-user | 把 vhost 设备后端搬进 guest 的 virtio 设备类型，用于 VM 之间直连 |
| virtio-bonding | 在 guest 内把 SR-IOV 快路径与 virtio 设备做透明绑定，迁移时切换 |