# virtio-scsi 与 virtio-blk 的设计取舍：什么时候该把"块设备"换成"SCSI 卡"

> 视频来源：[Virtio SCSI: An alternative virtualized storage stack for KVM](https://www.youtube.com/watch?v=7-rnyxuY-xc)（YouTube · KVM Forum 2011，讲者 Paolo Bonzini 与 Stefan Hajnoczi，Red Hat）｜时长约 30 分钟
> 导读：这是 virtio-scsi 的"出生演讲"——两位作者讲清 virtio-blk 的四个结构性限制、virtio-scsi 为什么要把队列拆成控制/事件/请求三类、以及后端 target 的两种选择。**说明**：这场 2011 年的录像只拍了演讲者，幻灯片没有进画面，所以本文配图只有演讲现场照，图表信息全部以文字与表格呈现；文中"当时"指 2011 年，今天的实现已经补齐了其中不少缺口。virtio-blk 的队列模型细节见同节另一篇《virtio-blk 的队列模型与 IOThread 映射》。

## 本讲要解决的核心问题（SCQA）

**背景**：virtio-blk 是 KVM 上高性能块设备的标准答案。它是半虚拟化设备，不用 SCSI 命令集也不用 ATA 命令集，只用一小把命令——读、写、刷缓存——配上 virtio 的环形队列，性能很好，Linux 和 Windows 客户机都支持。[【跳转到 02:52】](https://www.youtube.com/watch?v=7-rnyxuY-xc&t=172)

**冲突**：简单是有代价的，而且代价都长在"扩展"和"兼容"上。想给 virtio-blk 加一个 `trim`/`discard` 命令，得先改规范、再改 QEMU 的设备模拟、最后改**每一个**客户机驱动（Linux、Windows，还有 Solaris）；一个 PCI 适配器只能挂一个块设备，磁盘一多就把 PCI 总线塞满；进到客户机里它叫 `/dev/vda` 而不是 `/dev/sda`，那些按 SCSI 设备去找盘的应用会看不见它；持久预留、多路径这些 SCSI 高级特性根本没有。

**疑问**：能不能既保住 virtio 的性能，又拿到一整套 SCSI 的能力？

**回答（中心思想）**：virtio-scsi 的做法是**把"传输"和"命令集"拆开**。传输仍然用 virtio：环形队列、请求与环元素一一对应，性能几乎白送；命令换成标准的 SCSI CDB，于是持久预留、多路径、LUN 热插拔、`/dev/sda` 命名这些能力全部回来了。功能集不再由 virtio 规范写死，而是**由后端的 SCSI target 决定**。代价是队列模型变复杂了——一个 virtio-scsi 设备不再是一条队列，而是"控制队列 + 事件队列 + 一条或多条请求队列"。

## 一、virtio-blk 的设计：用极小的命令集换性能

### 1.1 环形队列加批量提交，性能是白送的

virtio-blk 的数据面就是 virtio 的通用模型：客户机驱动把命令放进环里，宿主把命令取走、替客户机做 I/O，做完把完成信息放回环里，客户机被唤醒后发现"我的 I/O 完成了"。关键在于它**可以一次塞进一大批命令**——客户机里如果有很多线程在做 I/O，把它们攒起来一起提交，比一条一条等着做要快得多。这是 virtio-blk 性能好的重要原因。[【跳转到 03:37】](https://www.youtube.com/watch?v=7-rnyxuY-xc&t=217)

它也能当 CD-ROM 用：把设备设成只读、挂一个 ISO 文件，就得到一个只读块设备——不过这已经接近它的能力边界了。

![演讲者 Stefan Hajnoczi 在 KVM Forum 2011 现场介绍 virtio-blk 的现状与限制](assets/virtio-scsi%20与%20virtio-blk%20的设计取舍/00177.webp)

### 1.2 命令集小到只有读、写、刷缓存

virtio-blk 的命令集就是"基本 I/O"那几条。这带来一个连锁反应：**每加一个新特性，都要同时改三处**。[【跳转到 04:32】](https://www.youtube.com/watch?v=7-rnyxuY-xc&t=272)

以 `trim`/`discard` 为例（当时精简置备正变得重要）：

1. 先改 virtio-blk 规范，把新命令写进文档；
2. 再改 QEMU 的设备模拟，把新命令实现出来；
3. 然后改**每一个**客户机驱动——Linux、Windows，还有 Solaris，都得加一遍。

一处需求，三处改动，而且第三处你永远改不完。既然命令集这么小，未来必然还要加好几次，这种"改一次全栈"的模式显然不可持续。

### 1.3 SCSI 直通命令存在，但不能通用

virtio-blk 其实带了一个 SCSI 直通（pass-through）命令，但它**不能通用**：它给出的东西和真机上"一块 SCSI 主机总线适配器（HBA）"能给出的完全不是一回事。所以想跑那些依赖真实 SCSI 设备的应用，光靠这个直通口是不够的。[【跳转到 06:04】](https://www.youtube.com/watch?v=7-rnyxuY-xc&t=364)

## 二、virtio-blk 的四个结构性限制

### 2.1 一个 PCI 适配器只能挂一个块设备

在 x86 的 KVM 上，virtio 设备是通过 PCI 呈现给客户机的。你在虚拟机里加一块盘，客户机里就多出一个 virtio-blk 的 PCI 适配器。于是就有了**PCI 适配器与块设备的一对一映射**：一个适配器一个盘。[【跳转到 06:48】](https://www.youtube.com/watch?v=7-rnyxuY-xc&t=408)

磁盘一多，PCI 总线就被塞满了。当时人们试过一些绕法：

- 用**多功能 PCI 设备**，把多个块设备塞进一个 PCI 槽位——但这样单个设备的热插拔就不正常了；
- 让 QEMU 的 PCI 拓扑扩出更多桥，把总线"拓宽"——能凑合，但显然不是可扩展的做法。

真正的解法应该像 SCSI HBA 那样：**一块适配器，后面挂一堆设备**。

### 2.2 设备名从 `/dev/sda` 变成 `/dev/vda`，应用就坏了

这一条是演讲者自己说"这是我最大的动机之一"的。在物理机上，磁盘叫 `/dev/sda`；搬到 KVM 上，它叫 `/dev/vda`。P2V（物理机迁虚拟机）或 V2V（虚拟机迁虚拟机）时，设备名一变，应用就崩，或者配置文件得改。[【跳转到 08:28】](https://www.youtube.com/watch?v=7-rnyxuY-xc&t=508)

理想情况下这不是问题——大家都该用 UUID 而不是设备名。但现实里就是有很多"固定栈"的用户，他们以为把系统丢进 KVM 就能跑，结果发现得加一堆 `if 在 KVM 里 then 找 /dev/vda` 的条件判断。

问题还不止名字。virtio-blk 设备是个"外来物种"：它就是一块块设备，**不是 SCSI 设备**。所以那些进 `/sys` 里找 SCSI 设备、或者要发 SCSI 命令的底层应用，即使 virtio-blk 提供了直通口，也未必满意——它们期待的是一个真正的 SCSI 设备。

### 2.3 没有高级 SCSI 特性：持久预留与多路径

Paolo 接着列了功能层面的缺口：virtio-blk 不支持**持久预留**（persistent reservation，集群文件系统用来做并发控制的机制），也不支持**多路径**（multipathing，把多条路径映射到同一个设备）。[【跳转到 10:33】](https://www.youtube.com/watch?v=7-rnyxuY-xc&t=633)

### 2.4 把整块 HBA 直通给客户机也不是答案

有人会说：那就把整块 HBA 直通给客户机好了。这条路的问题更多：

- **不能迁移**：直通的设备没法热迁移；
- **槽位有限**：一台刀片可能跑 20 个客户机，却只有 5 个 HBA 插槽；
- **暴露了宿主 fabric**：客户机没理由知道自己是跑在光纤通道上还是别的什么上；
- **独占**：直通后客户机独占这块盘，没法让两台客户机访问同一块盘；
- **语义错位**：两台客户机碰巧在同一台宿主上、通过持久预留去抢同一块盘的独占权时，target 会认为它们来自同一个 initiator，冲突检测就失效了。

所以 virtio-scsi 的目标被定义成四条：**保住 virtio 的高性能、拿到完整的 SCSI 特性、可扩展性不受限、对物理盘是可直接替换的（P2V/V2V 友好）**。[【跳转到 12:37】](https://www.youtube.com/watch?v=7-rnyxuY-xc&t=757)

## 三、virtio-scsi 的设计：传输不变，命令集换成 SCSI

### 3.1 性能靠 virtio，功能靠 target

virtio-scsi 的设计可以一句话概括：**性能来自 virtio，功能来自 SCSI target**。

- 性能：还是 virtio 的环形队列，请求与环元素**一一对应**（1:1），这部分几乎白送；
- 功能：特性集取决于后端 target。virtio-scsi 本身只实现 SCSI 规范里已有的东西，不发明新命令；
- 多路径：天然支持，因为**一个 virtio-scsi 设备在客户机里就是一块 SCSI 主机**；
- SCSI 直通：可以用 `sg` 那套通用接口，也可以走后面要讲的内核 target；
- 可扩展性：基本没有上限，一个 PCI 设备后面可以挂几千块盘，每个 target 的 LUN 编号能到 16000 左右；
- 命名：又变回 `/dev/sda`。

![Paolo Bonzini 讲解 virtio-scsi 的设计目标与队列结构](assets/virtio-scsi%20与%20virtio-blk%20的设计取舍/01076.webp)

这里有个概念上的关键点：**SCSI 不是"一种线"，而是一组 RPC 服务**。它最早绑在并行 SCSI 适配器上，如今已经演变成 target 暴露的一组服务，上面可以跑不同的传输协议——并行 SCSI、SAS、光纤通道、iSCSI、SRP。virtio-scsi 就是给这组服务又加了一种传输：virtio。演讲者提到，virtio-scsi 的设计与 IBM p 系列的 vSCSI 有很好的重合，他经常拿 p 系列的 target 来调试 QEMU 的 SCSI target。

### 3.2 队列模型：控制队列、事件队列、请求队列

这是 virtio-scsi 与 virtio-blk 在结构上最大的差别。virtio-scsi 设备有**三类 virtqueue**[【跳转到 15:59】](https://www.youtube.com/watch?v=7-rnyxuY-xc&t=959)：

| 队列 | 装什么 | 作用 |
| --- | --- | --- |
| 控制队列（control queue） | 除 SCSI 命令之外的一切 | 任务管理类操作，比如中止任务、设备复位 |
| 事件队列（event queue） | 宿主主动发来的异步事件 | unit attention：复位、热插拔、介质更换 |
| 请求队列（request queue） | SCSI CDB | 真正的读写命令，可以有一条或多条 |

当时的实现建议是**请求队列先只做一条**：多条请求队列确实可以做多队列，但 SCSI 对多队列的**顺序保证**语义还没理清，容易踩坑。控制队列和事件队列则各一条。

为什么要有事件队列？因为 SCSI 原生的"热插拔通知"很笨：一个 target 上插了新 LUN，客户机**不会自动知道**，必须等到它去读写同一个 target 上的某个 LUN 时才会发现。virtio-scsi 用一条专门的事件队列把这个通知提前送过去，客户机可以立刻感知。万一事件丢了也不要紧——协议会告诉客户机"你漏了一个事件"，它就退回去把整个 target 扫一遍。[【跳转到 16:43】](https://www.youtube.com/watch?v=7-rnyxuY-xc&t=1003)

### 3.3 命令如何变成请求：SCSI CDB 进环

请求队列里的每个环元素对应一条 SCSI CDB，和 virtio-blk 的"请求与环元素 1:1"是同一个思路。区别在于**命令的语义由 SCSI 规范定义**，而不是由 virtio 规范定义——这正是"加特性不用改客户机驱动"的根源。

## 四、后端 target：QEMU 还是内核

virtio-scsi 只是"传输"，真正干活的是 target。演讲里给了两条路。

### 4.1 QEMU 的 SCSI target：灵活但当时很弱

QEMU 里的 SCSI target 是用户态的，好处是灵活（能配各种镜像格式），但 2011 年时的状态很差[【跳转到 18:21】](https://www.youtube.com/watch?v=7-rnyxuY-xc&t=1101)：

- 只支持磁盘，CD-ROM 勉强支持，实现和规范差得远；
- 支持通过 `sg` 通用设备做直通；
- **一个 target 只能有一个 LUN**；
- 只实现了 SCSI 规范的一小部分；
- 不支持迁移（它是为并行 SCSI 设计的）；
- 没有 autosense——一条命令失败时，同时还有别的命令在飞，你可能只知道"失败了"，不知道为什么；
- 热插拔能力有限：一个 target 一个 LUN，客户机根本没途径知道你在新 target 上插了东西。

Paolo 为此做了一轮现代化改造，其中不少补丁是别人早年写好但没人关心的。改造的核心思路是**把通用的 SCSI 语义上提到 target 层**，而不是每个设备各实现一份：无效命令的处理、无效 LUN 的访问、`REPORT LUNS`、`REQUEST SENSE` 这些，本来就该由 target 统一负责。上提之后直接换来几个能力：

- **热插拔**：target 可以汇报"LUN 清单变了"，客户机自动重新 `REPORT LUNS`；
- **一个 target 多个 LUN**：因为 `REPORT LUNS` 本来就在 target 层处理，target 知道它下面所有 LUN；
- **迁移**：迁移时把在飞的请求丢掉，直接给客户机报一次"设备复位"，客户机自己重发；
- **scatter-gather 免 bounce buffer**：I/O 直接从宿主设备进客户机内存，不再经中转缓冲区（这个实现是通用的，Megasas 之类的非半虚拟化设备也能用）。

### 4.2 内核 target（LIO）与 vhost-scsi：把 QEMU 也省掉

第二条路是把 virtio-scsi 直接接到 Linux 内核里的 SCSI target（LIO，2.6.3x 起进主线）。它是一个多协议的 target 引擎：可以插 iSCSI、SRP、光纤通道 target 模式的适配器，下面可以接各种 backstore——一个文件、一块块设备，或者 SCSI 直通（磁带机、光驱）。[【跳转到 24:33】](https://www.youtube.com/watch?v=7-rnyxuY-xc&t=1473)

再往前一步就是 **vhost-scsi**：借用 vhost 的内核态 virtio 实现，把客户机的 virtio-scsi 设备**直接接到内核 target**，连 QEMU 都不用过。代码量不大——无非是把客户机给的 SCSI 命令抓过来，交给 target 去做。管理上也很细：target 支持 ACL，每台客户机看到的是自己的 target，LUN 映射可以按需配。

代价是**镜像格式**：内核 target 能直通文件、能直通块设备（比如 LVM 卷），但**不支持 qcow2 这类镜像格式**——这是当时没有解决的问题。另外文件后端是同步 I/O，块后端才是常用的选择。

![演讲者 Stefan Hajnoczi 讲解 vhost-scsi：把客户机的 virtio-scsi 直接接到内核 SCSI target](assets/virtio-scsi%20与%20virtio-blk%20的设计取舍/01524.webp)

演讲结束时，virtio-scsi 还处于**原型阶段**：规范还在邮件列表上讨论，客户机驱动只有 Linux 一份，QEMU 的 target 改造刚合入一部分，vhost-scsi 是能跑的 demo。

## 五、两者的取舍

| 维度 | virtio-blk | virtio-scsi |
| --- | --- | --- |
| 命令集 | 极小（读、写、刷缓存），由 virtio 规范定义 | 标准 SCSI CDB，由 SCSI 规范定义 |
| 加新特性要改哪里 | 规范 + QEMU + 每个客户机驱动 | 只改 target（客户机驱动不用动） |
| 设备粒度 | 一个 PCI 适配器 = 一块盘 | 一个 PCI 适配器 = 一块 SCSI HBA，后面挂很多 LUN |
| 队列结构 | 一组请求队列，请求与环元素 1:1 | 控制队列 + 事件队列 + 请求队列，CDB 与环元素 1:1 |
| 热插拔感知 | 由设备本身支持 | 事件队列主动通知，比 SCSI 轮询快 |
| 高级特性 | 无持久预留、无多路径 | 持久预留、多路径、`sg` 直通 |
| 客户机里的名字 | `/dev/vda` | `/dev/sda` |
| 对应用透明性 | 底层 SCSI 应用可能不认 | 和真机 SCSI 盘一致 |
| 性能 | 极简路径，通常更好 | 多一层 SCSI 语义，换来功能 |

所以选择规则可以概括成一句话：**只要一块盘、要极致简单和性能，用 virtio-blk；要很多盘、要 SCSI 语义、要 P2V/V2V 平滑迁移、要接真实存储阵列的能力，用 virtio-scsi。**

## 小结

- virtio-blk 用"极小的命令集 + virtio 环形队列"换来了好性能，代价是每加一个特性都要改规范、改 QEMU、改所有客户机驱动。
- 它的四个结构性限制：一个 PCI 适配器只能挂一块盘、设备名变成 `/dev/vda`、没有持久预留与多路径、HBA 直通又带来迁移与独占问题。
- virtio-scsi 的解法是**传输与命令集分离**：传输仍是 virtio（请求与环元素 1:1），命令换成 SCSI CDB，功能集由后端 target 决定。
- 队列模型因此从"一组请求队列"变成"控制队列 + 事件队列 + 请求队列"；事件队列让热插拔通知不必等客户机去轮询。
- 一个 virtio-scsi 设备在客户机里就是一块 SCSI 主机，所以多路径天然成立，LUN 数量与磁盘数量都不再受 PCI 槽位限制。
- 后端有两条路：QEMU 的用户态 target（灵活、支持镜像格式，但当年功能很弱，需要把通用 SCSI 语义上提到 target 层）和内核 target LIO + vhost-scsi（快、可直通块设备，但不支持 qcow2）。
- 到 2011 年演讲时，virtio-scsi 还在原型阶段；它后来的演进（多队列请求队列、与 vhost 的配合）走的正是这里定下的框架。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| virtio-blk | 半虚拟化块设备，命令集只有读、写、刷缓存等几条，性能好但功能有限 |
| virtio-scsi | 半虚拟化的 SCSI 主机适配器，传输用 virtio，命令用 SCSI CDB |
| CDB | Command Descriptor Block，SCSI 命令的定长描述块，一条命令一个 CDB |
| HBA | Host Bus Adapter，主机总线适配器，真机上挂 SCSI 设备的那块卡 |
| LUN | Logical Unit Number，一个 SCSI target 下的逻辑单元编号，可以理解为"第几块盘" |
| unit attention | SCSI 的异步状态通知，用于复位、热插拔、介质更换等事件 |
| `REPORT LUNS` | SCSI 命令，让 target 汇报它下面有哪些 LUN |
| autosense | 命令失败时自动带回 sense data（失败原因），没有它就只能知道"失败了" |
| 持久预留 | persistent reservation，集群文件系统用来做跨节点并发控制的 SCSI 机制 |
| 多路径 | multipathing，同一个设备有多条路径，一条断了还能走另一条 |
| LIO | Linux 内核里的 SCSI target 引擎，支持多种 fabric 与多种 backstore |
| vhost-scsi | 把客户机的 virtio-scsi 直接接到内核 SCSI target，绕过 QEMU 的设备模拟 |
| bounce buffer | 中转缓冲区；scatter-gather 支持后 I/O 可直接在宿主设备与客户机内存之间搬 |
| P2V / V2V | 物理机迁虚拟机 / 虚拟机迁虚拟机，设备名变化会直接影响这类迁移 |