# VMState 与 CPR：QEMU 怎样把设备状态序列化成文件

> 视频来源：[QEMU Live Update](https://www.youtube.com/watch?v=Qujgm-EPyvY)（YouTube · KVM Forum 2020 · Steven Sistare，Oracle）｜时长约 18 分钟
> 导读：这场 talk 讲的是"把 QEMU 换成新版本、客户机不停机"，但整条链路上最核心的一步恰好就是本节要问的问题——**设备状态怎么从一堆 C 结构体变成磁盘上的一个文件，又怎么装回去**。本文只取这条线：VMState 框架、VFIO 设备状态的三块内容、`cprsave`/`cprload` 的先后顺序，以及"什么时候可以干脆不存设备状态"。

## 本讲要解决的核心问题（SCQA）

**背景**：一台虚拟机的"现场"由三部分组成——vCPU 的寄存器、内存、以及设备。前两部分各有一块连续的东西可以整块搬走（vCPU 状态结构体、一段 RAM），设备却不一样：一块 virtio-net、一块 virtio-blk、一个 VFIO 直通网卡，各自的状态散落在不同的 C 结构体、不同的内核子系统里。

**冲突**：如果每次要保存现场都得为每个设备写一份"存/取"代码，那设备一多就没法维护；而更麻烦的是，有些设备状态根本不在 QEMU 进程里——VFIO 直通设备的 BAR、中断路由、DMA 映射都握在内核手里，QEMU 手上只有一个文件描述符。

**疑问**：那 QEMU 到底把设备的哪些部分写进了快照文件？写不进去的部分又靠什么带过去？这些动作和 vCPU 的暂停是什么先后关系？

**回答（中心思想）**：QEMU 把设备状态分成两类处理——**纯软件的那部分交给 VMState 框架序列化成一个普通文件（不到 1 MB）**；**落在内核里的那部分不复制内容，只把文件描述符和环境变量带过 `exec`，让新进程重新挂上去**。而这两件事都必须发生在 vCPU 已经暂停之后，否则存下来的设备状态和 vCPU 状态对不上。

## 一、设备状态在快照里很小，但它是"对不齐就全废"的那一块

### 1.1 先看这个方案想省掉什么

这场 talk 的出发点是：云厂商要打内核或 QEMU 的补丁，但客户机不能重启。可选的路有三类——把 VM 迁走（live migration）、原地给内核打热补丁、或者原地把组件换掉。作者选的是第三类：让旧 QEMU 进程 `exec` 新 QEMU 二进制，整个过程中客户机只暂停 **约 100 毫秒**，对外连接不断，客户机操作系统不需要配合，也不需要装任何 guest agent [【跳转到 00:06】](https://www.youtube.com/watch?v=Qujgm-EPyvY&t=6)。

![Live Update 的目标：客户机暂停约 100 毫秒、连接不断、支持 SR-IOV 且不需要客户机配合](assets/VMState%20与%20CPR：QEMU%20怎样把设备状态序列化成文件/00056.webp)

为什么不直接用 live migration？作者列了三条账：迁移要同时占住源和目的两台机器，降低集群利用率；要吃掉内存和网络带宽，影响同机其它进程；而且"影响持续多久"是不确定的，取决于拷贝阶段什么时候收敛——如果本地有大块存储要一起搬，代价更是高到不可接受 [【跳转到 00:56】](https://www.youtube.com/watch?v=Qujgm-EPyvY&t=56)。

### 1.2 设计里最容易被忽略的一行

整场 talk 的设计要素只有六条，其中第五条和第六条正是本节的主题：

| 设计要素 | 处理方式 |
| --- | --- |
| 旧 QEMU 进程 exec 新 QEMU 二进制 | 执行环境整体带过去 |
| 客户机内存原地保留 | 留在 RAM 里，DMA 可以继续跑 |
| 外部描述符保持打开 | 串口控制台、QEMU monitor、VNC、pty、vhost 设备 |
| VFIO / SR-IOV 描述符保留 | 设备在内核侧"活着" |
| KVM 描述符**不**保留 | 销毁旧实例，重建 |
| QEMU 设备状态序列化后存文件 | 本节的主角 |

[【跳转到 02:11】](https://www.youtube.com/watch?v=Qujgm-EPyvY&t=131)

![设计要素：设备状态被序列化并保存到文件，而 KVM 实例被销毁重建](assets/VMState%20与%20CPR：QEMU%20怎样把设备状态序列化成文件/00131.webp)

注意这张表的逻辑：**能"带过去"的就不"写下来"**。内存不写（原地保留）、fd 不写（跨 exec 保留）、只有"既不能原地保留、又必须精确复原"的设备内部状态，才需要序列化。这就是为什么设备状态文件可以小到 1 MB 以下——大头（内存、磁盘镜像）都不在里面。

## 二、VMState：把"每个设备要存哪些字段"变成一张可遍历的表

### 2.1 复用 live migration 的那套框架

QEMU 处理"其它设备状态"的办法不是新写一套，而是直接借用 live migration 用的 **VMState 框架**，只做一处改动：让 save/restore 的 handler 可以按操作类型选择——同一次序列化，走 CPR、走内部快照、走 live migration，可以调用不同的 handler [【跳转到 07:36】](https://www.youtube.com/watch?v=Qujgm-EPyvY&t=456)。

![QEMU 设备状态：借用 vmstate 框架，序列化到普通文件，不做块设备快照](assets/VMState%20与%20CPR：QEMU%20怎样把设备状态序列化成文件/00456.webp)

从后面那页"注入 vmsave"的幻灯片可以更清楚地看到这个框架的形状：QEMU 里维护着一串全局链表——**RAM handler 列表、VM state handler 列表**，以及字符设备、vhost 设备等列表。所谓"保存设备状态"，就是遍历 VM state handler 列表，让每个设备按自己注册的规则把字段吐出来；所谓"注册一个新 handler"，就是往这张表里加一项 [【跳转到 13:06】](https://www.youtube.com/watch?v=Qujgm-EPyvY&t=786)。

对初学者可以这样理解：VMState 相当于给每个设备发一张"体检表"，表上写着这个设备有哪些字段要记录、每个字段多宽。保存时按表逐项抄，恢复时按表逐项填回去。设备作者只需要维护自己那张表，不用关心整体文件格式。

### 2.2 三个和"快照"有关的取舍

这页幻灯片上有三个细节，直接决定了这份文件的性质：

1. **序列化到普通文件**，不是 socket（live migration 走的是流），也不是 qcow2 内部快照。这样做的收益是"支持各种镜像格式和引导设备"——存下来的东西和磁盘格式解耦。
2. **不做块设备快照**。因此有一条硬约束：从 save 到 restore 之间，**不能修改块设备**。设备状态和磁盘内容是一对必须同时成立的现场，只存一半就得靠外部保证另一半不变。
3. **文件很小，不到 1 MB**，写文件非常快，对客户机暂停时间的贡献很小 [【跳转到 08:01】](https://www.youtube.com/watch?v=Qujgm-EPyvY&t=481)。

第 3 点值得停一下：一台跑着网卡和磁盘的虚拟机，设备状态不到 1 MB，说明这里存的只是"设备的控制面状态"——寄存器、索引、配置、中断表，而不是缓冲区里的数据。数据在客户机内存里，而内存是原地保留的。

## 三、VFIO 设备状态：能带走的 fd，和必须写进文件的表

直通设备（VFIO）是这条链路上最难的一半：设备真的存在，它的 BAR 映射、中断路由、IOMMU 映射都在内核里。QEMU 的做法是**分类处理**，而不是一股脑序列化。

![VFIO 设备状态：BAR 与 config 重新映射、DMA 靠 IOMMU group fd、中断靠 eventfd 加 MSI-X 表](assets/VMState%20与%20CPR：QEMU%20怎样把设备状态序列化成文件/00356.webp)

### 3.1 BAR 与配置空间：不存内容，重读一次

PCI BAR 和 config region 通过 VFIO 的 device fd 就能访问。所以跨 `exec` 之后，QEMU 不需要"恢复"这些内容，它做的是：**重新 mmap BAR、重新读一遍 config** [【跳转到 05:31】](https://www.youtube.com/watch?v=Qujgm-EPyvY&t=331)。

这是一个很值得记住的思路：**能从硬件读回来的状态就不要存**。存下来反而有风险——万一文件里的值和硬件里的值不一致，谁是权威？重读一次，硬件永远是权威。

### 3.2 DMA 映射：保留 IOMMU group fd

DMA 映射靠保留 **IOMMU group fd**（放在 container fd 里）来维持。只要这个 fd 还在，映射就还在，设备在客户机暂停期间仍可以继续发 DMA，异步内核线程也能安全地做 IOVA → 虚拟地址 → 物理页的翻译 [【跳转到 01:46】](https://www.youtube.com/watch?v=Qujgm-EPyvY&t=106)。

### 3.3 中断状态：eventfd 加 MSI-X 表

中断被拆成两部分：

- **eventfd 部分**：error IRQ、request IRQ、以及每个 vector 一个 MSI-X IRQ，都建好 eventfd 并保留下来；
- **表部分**：**MSI-X table 和 pending bit（PBA）写进 VM state 文件**，恢复时从文件读回来 [【跳转到 05:56】](https://www.youtube.com/watch?v=Qujgm-EPyvY&t=356)。

为什么 MSI-X 表必须写进文件而不是重读？因为它是**软件配置出来的**：guest 在初始化时把每个 vector 的地址和数据写进 MSI-X table，这段内容不在设备硬件里"天然存在"，重读也读不回来。这正是"必须序列化"的那一类状态。

### 3.4 fd 的命名：设备拓扑被编码进了字符串

幻灯片右下角那一小段环境变量很值得看，它把"设备树"这件事暴露得很直白：

```text
setenv QEMU_FD_/dev/vfio/65                       15
setenv QEMU_FD_vfio_container_65                  24
setenv QEMU_FD_0000:3a:10.0                       26
setenv QEMU_FD_0000:3a:10.0_err_0                 27
setenv QEMU_FD_0000:3a:10.0_req_0                 28
setenv QEMU_FD_0000:3a:10.0_interrupt_0           162
setenv QEMU_FD_0000:3a:10.0_kvm_interrupt_0       163
setenv QEMU_FD_0000:3a:10.0_interrupt_1           164
setenv QEMU_FD_0000:3a:10.0_kvm_interrupt_1       165
```

每一行是"名字 + fd 号"。名字里带着 **PCI 地址（`0000:3a:10.0`）**、**中断类型（err / req / interrupt）**、**vector 序号**。作者特意指出，高亮的那条是"设备 `3a:10` 的 vector 0 对应的 KVM IRQ chip notifier，描述符编号 163" [【跳转到 06:21】](https://www.youtube.com/watch?v=Qujgm-EPyvY&t=381)。

换句话说，**恢复时并不需要另外存一份"这台 VM 有哪些设备、各挂在哪条总线、用哪个中断"的清单**——这份拓扑信息就编码在 fd 的名字里，新 QEMU 按名字把 fd 认回来，再用 `KVM_CREATE_DEVICE`、`KVM_SET_GSI_ROUTING`、`KVM_IRQFD`、`KVM_IOEVENTFD` 这些 ioctl 重新挂到新的 KVM 实例上 [【跳转到 06:46】](https://www.youtube.com/watch?v=Qujgm-EPyvY&t=406)。

代码改动小得出人意料：凡是创建 VFIO 描述符的地方，先查一下环境变量，有就直接用那个值，然后走原来的代码路径；同时记住这个 fd 是复用的，跳过那些会重新配置设备的 ioctl。

## 四、`cprsave` / `cprload`：设备状态与 vCPU 状态的先后顺序

### 4.1 保存侧：先停 vCPU，再抄设备

`cprsave <file> <mode>` 的步骤是有严格顺序的：

1. **暂停客户机 vCPU**；
2. **把 QEMU 设备状态写进文件**；
3. 对各个 RAM 段调用 `MADV_DOEXEC`（主内存、显存等）；
4. 保留 VFIO 描述符与状态，保留其它描述符；
5. 销毁 KVM 实例；
6. `exec` 新 QEMU 二进制（可经 `/usr/bin/qemu-exec` 这个站点自定义的跳板）；
7. 新 QEMU 启动：建新 KVM 实例、复用 RAM、复用 VFIO 与其它描述符、把 VFIO fd 挂到新 KVM 上。

[【跳转到 08:26】](https://www.youtube.com/watch?v=Qujgm-EPyvY&t=506)

![cprsave 的步骤：暂停 vCPU、保存设备状态、保留 fd、销毁 KVM 实例、exec 新二进制](assets/VMState%20与%20CPR：QEMU%20怎样把设备状态序列化成文件/00506.webp)

第 1 步和第 2 步的先后关系是整件事的关键。设备状态里包含"设备当前处理到哪了"这类信息（中断挂起位、队列索引等），只有在 vCPU 不再推进、设备也不再被新的 MMIO 写操作驱动之后，抄下来的值才是一个**自洽的瞬间**。如果先抄设备再停 vCPU，中间那段时间客户机可能又改了设备配置，恢复出来的现场就会出现"设备记得的"和"vCPU 记得的"不一致。

### 4.2 恢复侧：先装设备，再放 vCPU

`cprload <file>` 的顺序正好相反：

- 此时 QEMU 处于 **pre-launch 状态**，管理面可以先发 `device-add` 命令，补上命令行没定义的设备——这也是为什么整个流程被拆成 save 和 load 两个阶段；
- 然后 **从文件载入设备状态（包括 VFIO 的 MSI-X 状态）**；
- 最后才 **继续 vCPU**。

[【跳转到 09:41】](https://www.youtube.com/watch?v=Qujgm-EPyvY&t=581)

![cprload：从文件载入设备状态（含 VFIO MSI-X），再继续 vCPU](assets/VMState%20与%20CPR：QEMU%20怎样把设备状态序列化成文件/00581.webp)

同样是为了自洽：vCPU 一旦跑起来，第一条指令就可能去读设备寄存器、发一个 doorbell。设备必须先就位，否则客户机看到的是一个"刚复位"的设备，而不是它暂停前的那个设备。

作者给出的实测暂停时间是 **100 毫秒**，而且是在四年前的 Xeon 上、没有做过任何 profiling 的结果 [【跳转到 10:06】](https://www.youtube.com/watch?v=Qujgm-EPyvY&t=606)。

### 4.3 演示里能看到什么

现场演示用两块终端窗口：左边跑 QEMU 和 `status`，右边用 `yum` 把磁盘上的 QEMU 换成新版本——这一步不影响正在跑的进程；然后左窗发 `cprsave`，状态变成 pre-launch；再发 `cprload`，客户机继续跑 [【跳转到 10:31】](https://www.youtube.com/watch?v=Qujgm-EPyvY&t=631)。

演示里还有一个细节值得注意：客户机里跑着一个计数程序，`suspend` 时数字停住，`resume` 时继续；反复在新旧版本之间来回切换，每次暂停时间都被打印出来，稳定在 100 毫秒左右 [【跳转到 11:48】](https://www.youtube.com/watch?v=Qujgm-EPyvY&t=708)。这说明设备状态的存取是**幂等且可重复**的——每次都是同一张表、同一个文件格式。

![演示现场：HOST 窗口里 QEMU 版本已换成新镜像，GUEST 窗口里的计数程序仍在继续跑](assets/VMState%20与%20CPR：QEMU%20怎样把设备状态序列化成文件/00708.webp)

## 五、反例：什么时候可以"没有设备状态要存"

这场 talk 最有教学价值的一段，是它给出了一个**完全绕开设备状态序列化**的方案。

如果要连宿主内核一起换（`cprsave file reboot` → `kexec boot` → `cprload file`），QEMU 的设备状态照旧存文件，但客户机内存必须放在 `/dev/shm` 里，由 pkram 补丁跨 kexec 保留下来。这时如果 VM 里还有 SR-IOV 直通设备，作者的做法是：**要求客户机装一个 agent（例如 qemu-guest-agent），先做一次 suspend-to-RAM**。

![Kernel Live Update：SR-IOV 场景下让客户机驱动自己把设备复位，于是"没有设备状态要存"](assets/VMState%20与%20CPR：QEMU%20怎样把设备状态序列化成文件/00986.webp)

幻灯片最后一行写得很干脆：**guest drivers flush requests and re-initialize → no device state to save/restore**。客户机驱动把在途请求刷干净、把设备重新初始化到一个复位状态——而这个状态恰好等于"宿主重启之后设备会处于的状态"，于是双方对状态的认知天然一致，QEMU 这边就不用存任何直通设备的状态了 [【跳转到 16:26】](https://www.youtube.com/watch?v=Qujgm-EPyvY&t=986)。

这给出一条判断准则：**如果设备能被驱动复位到一个双方都认可的确定状态，就不必序列化；只有当设备状态无法通过复位重建时，才必须写进快照。** 代价是这条路要客户机配合（装 agent），而且比"让设备一直活着"慢——作者在结尾说，未来想和 Intel 的 VMM fast restart 工作合并，那条路能让 SR-IOV 设备跨重启保持存活和配置，更快，也不需要 guest agent [【跳转到 16:51】](https://www.youtube.com/watch?v=Qujgm-EPyvY&t=1011)。

## 六、这套机制的边界

### 6.1 老版本 QEMU 也能被"注入"保存逻辑

`cprsave` 是新加的 monitor 命令，旧 QEMU 没有。作者的做法是往运行中的进程里注入一个 `vmsave` 共享库：它按符号表找到 QEMU 的全局变量（RAM handler 列表、VM state handler 列表、字符设备与 vhost 设备列表），删掉一些只为 live migration 准备的 handler，再注册一个 VFIO 专用 handler，然后调用 `MADV_DOEXEC`、保存设备状态、exec 新 QEMU [【跳转到 12:41】](https://www.youtube.com/watch?v=Qujgm-EPyvY&t=761)。因为 `vmsave` 对 QEMU 的数据结构有二进制依赖，所以每个旧版本都要单独编译一份，用 GCC build id 索引 [【跳转到 14:21】](https://www.youtube.com/watch?v=Qujgm-EPyvY&t=861)。

这段的隐含结论是：**设备状态的序列化格式是和设备模型代码绑定的**。换一个 QEMU 版本，handler 表就可能变了，所以"快照能不能恢复"从来不只是文件格式问题，而是"恢复端有没有同一套设备模型"。

### 6.2 还没解决的部分

- `MADV_DOEXEC` 这个内核扩展 upstream 评审不接受，作者在考虑改用 `shmat`、`memfd` + `mmap` 之类的标准系统调用重新挂内存 [【跳转到 17:16】](https://www.youtube.com/watch?v=Qujgm-EPyvY&t=1036)。
- 块设备不在快照里，所以"保存到恢复之间不能动盘"这条约束要靠外部保证。
- 100 毫秒的暂停还没有优化过。

## 小结

- 快照里的"设备那一半"通常很小（本例不到 1 MB），因为内存原地保留、磁盘不拍快照，真正要写的只有设备的控制面状态。
- QEMU 用 **VMState 框架**统一处理：每个设备注册自己的 handler，保存时遍历 handler 列表逐个序列化，恢复时逐个填回。
- 状态按"能不能重建"分两类：**能从硬件读回来的（BAR、config）就重读；读不回来的（MSI-X table 与 pending bit）才写进文件**。
- 落在内核里的那部分（DMA 映射、中断 eventfd、VFIO 描述符）靠**跨 exec 保留 fd** 带过去，设备拓扑信息编码在 fd 名字里（PCI 地址 + 中断类型 + vector 号）。
- 顺序不能反：保存时**先停 vCPU 再抄设备**，恢复时**先装设备再放 vCPU**，否则设备状态与 vCPU 状态对不上。
- 如果驱动能把设备复位到双方认可的确定状态（SR-IOV + suspend-to-ram），就**根本不需要序列化设备状态**——这是判断"哪些状态必须存"的一把尺子。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| VMState | QEMU 里"每个设备声明自己哪些字段要保存"的框架，live migration、内部快照、CPR 共用同一套 handler |
| CPR（CheckPoint and Restart） | QEMU 新增的一对 monitor 命令 `cprsave` / `cprload`，把设备状态存成文件、进程 exec 后重新装载 |
| VFIO | 把物理设备直通给虚拟机的框架；设备状态一部分在 QEMU，一部分在内核 |
| MSI-X table / PBA | 中断向量表与挂起位图，由客户机软件写入，硬件里没有"原值"，必须序列化 |
| eventfd | 内核用来向用户态投递中断通知的文件描述符，可跨 exec 保留 |
| IOMMU group fd | 代表一个 IOMMU 组的文件描述符，保留它等于保留设备的 DMA 映射 |
| MADV_DOEXEC | 作者提出的 madvise 扩展，让一段 mmap 内存在 exec 后仍映射在同一虚拟地址 |
| pre-launch 状态 | 新 QEMU 已启动但 vCPU 未运行的状态，此时可补发 `device-add`，然后 `cprload` |
| suspend-to-RAM（客户机侧） | 客户机驱动把在途请求刷干净、把设备复位，使设备状态可由复位重建，从而免去序列化 |