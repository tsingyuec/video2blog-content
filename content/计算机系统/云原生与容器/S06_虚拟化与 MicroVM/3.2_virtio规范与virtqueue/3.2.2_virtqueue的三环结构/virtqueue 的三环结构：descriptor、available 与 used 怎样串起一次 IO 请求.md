# virtqueue 的三环结构：descriptor、available 与 used 怎样串起一次 I/O 请求

> 视频来源：[15.1 Paravirtualization Mechanics: VirtIO Ring | VirtIO & the Firecracker Jailer Architecture](https://www.youtube.com/watch?v=2wkpXkGiflw)（YouTube · Adsorp AI）｜时长约 19 分钟
> 简要导读：这支视频从"microVM 里没有磁盘控制器，却读到了磁盘"这个矛盾切入，把 split virtqueue 的三块内存结构、16 字节 descriptor 的字段、一次请求的 14 步流转，以及"客户机内核被攻破后能否伪造 descriptor"这条安全线一次讲完。本文按"为什么需要 → 结构长什么样 → 一次请求怎么走 → 边界在哪"重排；packed virtqueue 的结构差异另有一篇（见文末）。

## 本讲要解决的核心问题（SCQA）

**背景**：一台 MicroVM 被砍到只剩最小设备——没有模拟的 Intel 主板、没有 PCI 总线层级、没有 IDE 控制器、没有物理 SATA 线。可它照样启动、照样从宿主机文件系统里的一个磁盘镜像里读扇区、执行二进制程序。

**冲突**：传统做法是"全模拟"——hypervisor 假装自己是一块 1990 年代的网卡或 IDE 控制器。客户机每碰一次设备寄存器，CPU 就得停下来、退出到宿主机、用软件把那块硬件的行为演一遍，再回到客户机。一次搬运一个字节就要几千个 CPU 周期。

**疑问**：既然不能靠"模拟寄存器"，那 guest 和 host 到底靠什么结构把数据搬过去？

**回答（中心思想）**：virtio 把"设备寄存器"换成了**一块双方都映射的共享内存里的三个环**——descriptor table 记录缓冲区在哪、available ring 由驱动发布"这些缓冲区归你了"、used ring 由设备回执"这些我用完了"。驱动与设备各自只写属于自己的那一环（单写者原则），靠一个 16 位单调递增的 `idx` 计数器判断"有没有新东西"，再用门铃（kick）和虚拟中断把对方叫醒。一次块读请求，就是"填 3 个 descriptor → 发布 → kick → 设备处理 → 写 used → 中断 → 回收"这一条流水线。

## 一、从"骗客户机"到"跟客户机合作"

### 1.1 全模拟设备的六步代价

视频先把"全模拟"的成本拆成六步（[【跳转到 00:55】](https://www.youtube.com/watch?v=2wkpXkGiflw&t=55)）：

1. 客户机执行一条 `outb` 之类的指令，写一个传统 I/O 端口（例如 0x300），撞上硬件陷阱；
2. CPU 触发一次 VM exit，保存 vCPU 寄存器、冲刷流水线、恢复宿主控制寄存器；
3. hypervisor 解码这条指令，算出它想访问的是哪个设备地址（比如 QEMU 进程里的一块模拟寄存器）；
4. 用软件模拟那颗芯片的物理逻辑，更新内部状态机，完成这次字节搬运；
5. 硬件 resume；
6. CPU 执行 VM entry，重新装载 vCPU 状态，客户机从下一条指令继续。

代价是"**搬一个字节要几千个周期**"（[【跳转到 01:05】](https://www.youtube.com/watch?v=2wkpXkGiflw&t=65)）。在跑多租户 AI 沙箱、处理高吞吐数据流时，每秒几千次 VM exit 的 CPU 税是不可接受的。

### 1.2 半虚拟化：把寄存器换成共享内存里的环

半虚拟化换了个思路：不再骗客户机"你是真机"，而是直接告诉它"你在虚拟机里"。既然客户机知道自己是虚拟的，它就不需要一块模拟的 IDE 或 PCI 芯片，双方约定一套干净的软件接口即可——这就是 OASIS 维护的开放规范 **virtio**（[【跳转到 02:40】](https://www.youtube.com/watch?v=2wkpXkGiflw&t=160)）。

virtio 的核心，是用"**建立在共享内存里的高速、异步、无锁环形队列**"取代寄存器模拟。这里的"环形队列"就是 **virtqueue**（虚拟队列）：它是一套**内存缓冲区所有权转移**的机制——缓冲区原本归客户机内核里的驱动所有，驱动把它"交给"宿主机进程里的设备模型，设备用完再"还回来"。

![三环各司其职：descriptor table 编目缓冲区，available ring 由驱动写，used ring 由设备写](assets/virtqueue%20的三环结构：descriptor、available%20与%20used%20怎样串起一次%20IO%20请求/00235.webp)

## 二、三环的内存布局：一块共享内存，三种角色

virtio 并没有分配一整块大共享堆，而是把队列切成**三块各自连续的内存区域**（[【跳转到 03:05】](https://www.youtube.com/watch?v=2wkpXkGiflw&t=185)）：

| 区域 | 别名 | 谁写 | 谁读 | 作用 |
| :--- | :--- | :--- | :--- | :--- |
| descriptor table | descriptor area | 驱动 | 设备 | 缓冲区目录：地址、长度、访问标志 |
| available ring | driver area | 驱动 | 设备 | 待办清单：哪些 descriptor 链可以处理了 |
| used ring | device area | 设备 | 驱动 | 完成回执：哪条链用完了、写了多少字节 |

### 2.1 descriptor table：16 字节的"缓冲区目录"

descriptor 是 virtio 内存表示的基本单位，每个 16 字节，字段来自 Linux 头文件 `linux/virtio_ring.h` 里的 struct vring_desc（[【跳转到 05:35】](https://www.youtube.com/watch?v=2wkpXkGiflw&t=335)）：

| 字段 | 宽度 | 含义 |
| :--- | :--- | :--- |
| `addr` | 64 位 | 缓冲区的**客户机物理地址**（GPA），既不是客户机用户态虚拟指针，也不是宿主虚拟指针 |
| `len` | 32 位 | 设备被允许读或写的精确字节数 |
| `flags` | 16 位 | 设备必须遵守的访问方式（见第三节） |
| `next` | 16 位 | 当 `NEXT` 置位时，链中下一个 descriptor 的下标 |

注意 `addr` 存的是 **GPA**。这一点在第七节会变成安全边界的关键：设备模型拿到这个地址后不能直接当指针用。

### 2.2 available ring：驱动写给设备的待办清单

驱动把一条 descriptor 链拼好后，怎么告诉设备"这条可以处理了"？答案是把**链头 descriptor 的下标**放进 available ring（[【跳转到 08:05】](https://www.youtube.com/watch?v=2wkpXkGiflw&t=485)）。它的 C 结构是：

![available ring：驱动把链头 descriptor 的下标写进这个环，等于向宿主提交工作](assets/virtqueue%20的三环结构：descriptor、available%20与%20used%20怎样串起一次%20IO%20请求/00510.webp)

```c
struct vring_avail {
    __virtio16 flags;        /* bit 0: VIRTQ_AVAIL_F_NO_INTERRUPT */
    __virtio16 idx;          /* 单调递增的计数器 */
    __virtio16 ring[QUEUE_SIZE];  /* 链头下标数组 */
    __virtio16 used_event;   /* 可选：中断抑制用的事件阈值 */
};
```

### 2.3 used ring：设备写给驱动的完成回执

设备处理完一条链，要把缓冲区还回去，并报告"我写了多少字节"。它写的是 used ring（[【跳转到 09:20】](https://www.youtube.com/watch?v=2wkpXkGiflw&t=560)）：

```c
struct vring_used_elem {
    __virtio32 id;    /* 被处理完的链头 descriptor 下标 */
    __virtio32 len;   /* 设备实际写入的字节数 */
};

struct vring_used {
    __virtio16 flags;             /* bit 0: VIRTQ_USED_F_NO_NOTIFY */
    __virtio16 idx;               /* 单调递增的完成计数器 */
    struct vring_used_elem ring[QUEUE_SIZE];
    __virtio16 avail_event;
};
```

### 2.4 为什么必须分成三块：单写者原则

三块区域合起来的语义非常清楚：**每一块都只有一个写者**。descriptor table 与 available ring 由驱动写、设备读；used ring 由设备写、驱动读。视频给了一张完整的内存拓扑示意（[【跳转到 04:20】](https://www.youtube.com/watch?v=2wkpXkGiflw&t=260)）：

![split virtqueue 的内存拓扑：descriptor table 在上，available ring 与 used ring 在下，中间靠 head index 与 descriptor id 互相引用](assets/virtqueue%20的三环结构：descriptor、available%20与%20used%20怎样串起一次%20IO%20请求/00260.webp)

图里的具体内容值得逐行读一遍：

- descriptor 0：`addr=0x104000`、`len=16`、`flags=NEXT`、`next=1`——一段 16 字节的请求头；
- descriptor 1：`addr=0x1000`、`len=512`、`flags=NEXT|WRITE`、`next=2`——512 字节的数据缓冲区，设备可写；
- descriptor 2：`addr=0x106000`、`len=1`、`flags=WRITE`、`next=0`——1 字节状态字段；
- available ring：`flags=0`、`idx=42`、`ring=[0, 5, 8, ...]`；
- used ring：`flags=0`、`idx=41`、ring=[{id 0, len 513}, …]。

单写者原则带来的好处是：**双方都不需要对整块结构加锁**。驱动只关心"我写到哪了"，设备只关心"我读到哪了"，两个计数器之间的差值就是"还有多少活没干"。

这三块区域都是**客户机内核驱动在设备初始化时从客户机物理内存里分配**的，驱动把三块区域的基址通过配置接口交给 hypervisor。之后双方各自映射这块内存，**每一次数据传输都不需要系统调用、也不需要硬件陷阱**——这正是 virtio 相对全模拟省下来的那笔钱（[【跳转到 05:10】](https://www.youtube.com/watch?v=2wkpXkGiflw&t=310)）。

## 三、descriptor chain：一次块请求为什么需要三个 descriptor

### 3.1 三个 flag 的语义

`flags` 里最关键的三个位（[【跳转到 06:25】](https://www.youtube.com/watch?v=2wkpXkGiflw&t=385)）：

- **`VIRTQ_DESC_F_NEXT`（bit 0）**：这个 descriptor 后面还链着另一个。virtio 用这种方式实现 scatter-gather I/O——把不连续的几段内存拼成一次请求。
- **`VIRTQ_DESC_F_WRITE`（bit 1）**：**注意，它不表示"客户机正在写"，而是"这块缓冲区设备可写"**。置位时，设备会把数据写进这块客户机内存（比如完成一次磁盘读、收到一个网络包）；清零时，缓冲区是"设备只读"的，说明内容由客户机填好、设备只能读（比如执行一次磁盘写、发一个网络包）。这个方向约定反了，数据就会写错地方。
- **`VIRTQ_DESC_F_INDIRECT`（bit 2）**：这个 descriptor 不直接指向数据，而是指向另一张**动态分配的 descriptor 表**。好处是大批 scatter-gather 请求只占用主队列里的一个槽位。

`next` 字段只在 `NEXT` 置位时有意义，它存的是链中下一个 descriptor 的下标。

### 3.2 一个块读请求的三段链

现实中的 I/O 很少能塞进一块连续内存。一次块设备读至少需要三段（[【跳转到 07:15】](https://www.youtube.com/watch?v=2wkpXkGiflw&t=435)）：

1. 一小段**请求头**（扇区号、读命令），由客户机填、设备只读；
2. 真正接收数据的**目标缓冲区**，设备可写；
3. 末尾**1 字节状态字段**，设备写回成功或 I/O 错误。

用 descriptor chaining，驱动把三个 descriptor 串起来：

```text
[ Descriptor 0 ] (Flags: NEXT)          -> 请求头（设备只读）
        v next = 1
[ Descriptor 1 ] (Flags: NEXT | WRITE)  -> 目标数据缓冲区（设备可写）
        v next = 2
[ Descriptor 2 ] (Flags: WRITE)         -> 1 字节状态字段（设备可写）
```

![descriptor 链：第 0 个指向请求头，第 1 个指向数据缓冲区，第 2 个指向 1 字节状态字段](assets/virtqueue%20的三环结构：descriptor、available%20与%20used%20怎样串起一次%20IO%20请求/00460.webp)

设备照着链走：从 descriptor 0 读出请求头，从宿主存储读出原始数据，直接写进 descriptor 1 指向的客户机内存，再把 0（成功）写进 descriptor 2 指定的那个字节。整条链在 available ring 里只占**一个**槽位——记的是链头下标 0。

## 四、`idx` 为什么是单调递增的计数器

### 4.1 自由计数器 + 取模

available ring 的 `idx` 是一个**自由运行的 16 位计数器**，它**不会在队列大小处回绕**，而是 0、1、2 …… 65535、再回到 0（[【跳转到 08:30】](https://www.youtube.com/watch?v=2wkpXkGiflw&t=510)）。

要找到它在环里的实际槽位，双方都算一次取模：

$$
offset = idx \bmod QUEUE\_SIZE
$$

而 virtio 规定 queue size 必须是 2 的幂（128、256、1024 之类），于是取模退化成一次按位与：

$$
offset = idx \ \& \ (QUEUE\_SIZE - 1)
$$

![自由运行的 idx 与 2 的幂取模：offset = idx mod QUEUE_SIZE，实现上就是一次按位与](assets/virtqueue%20的三环结构：descriptor、available%20与%20used%20怎样串起一次%20IO%20请求/00560.webp)

为什么不用"当前下标"而要一个会绕圈的计数器？因为**双方各自维护一个内部计数器**，靠"两个计数器的差值"判断有多少条待处理请求。如果 `idx` 是"当前下标"，一旦环写满绕回 0，双方就无法区分"空"和"满"；单调递增的 16 位计数器把"绕回"这件事变成一个可以比较的差值问题，同时避免了生产者与消费者之间的模偏差和边界情形。

### 4.2 `ring[]` 的大小为什么等于 queue size

`avail->ring[]` 与 `used->ring[]` 的数组长度都是 `QUEUE_SIZE`，不是"队列大小减一"。原因是这两个数组各自记录的是**环上每个槽位的元信息**：available 侧记"这个槽位里放的链头下标是多少"，used 侧记"这个槽位对应的完成记录（id、len）"。环上有多少槽位，就需要多少条记录。真正限制"最多能挂多少条未完成请求"的，是 descriptor table 的项数（同样是 `QUEUE_SIZE`），因为每条请求至少要占一个 descriptor。

### 4.3 发布顺序：先写内容，再动计数器

驱动把新的链头写进 `ring[offset]` 之后，**不能立刻**加 `idx`。它要先发一个写内存屏障（write memory barrier），确保 descriptor 的内容真的落到内存里，然后才 `avail->idx++`（[【跳转到 08:45】](https://www.youtube.com/watch?v=2wkpXkGiflw&t=525)）。

顺序反了会怎样？设备看到 `idx` 变了，跑去读 descriptor，读到的却可能是还没写全的旧内容——这就是典型的发布顺序错误。所以这里的规则是：**内容先可见，计数器后可见**。设备侧对称地遵循同样的规则：先写 `used->ring[used->idx & (size-1)]` 的 `id` 与 `len`，再 `used->idx++`。

## 五、一次请求的完整生命周期

### 5.1 同步的两难

驱动跑在硬件虚拟化容器里的虚拟 CPU 上，设备线程是宿主 Linux 上的一个普通 POSIX 线程。两者怎么知道对方有新动作？（[【跳转到 10:10】](https://www.youtube.com/watch?v=2wkpXkGiflw&t=610)）

- 设备**死循环轮询** `avail->idx`？那会白白烧掉一个物理核。
- 客户机每发一个包就做一次**系统调用**？那就退回到全模拟的性能陷阱里了。

virtio 的答案是**异步信号**：门铃（kick）与半虚拟化中断。

![同步两难：轮询烧核、每次提交都陷入又太贵，virtio 用门铃与虚拟中断解耦执行](assets/virtqueue%20的三环结构：descriptor、available%20与%20used%20怎样串起一次%20IO%20请求/00660.webp)

### 5.2 十四步流水线

视频把整条链路画成 14 步（[【跳转到 11:00】](https://www.youtube.com/watch?v=2wkpXkGiflw&t=660)），可以按"客户机侧 → 硬件边界 → 宿主侧 → 硬件边界 → 客户机侧"来读：

![virtio 异步信号流水线的 14 个步骤：客户机发布 → MMIO 门铃 → KVM eventfd → 设备处理 → irqfd → 虚拟中断 → 驱动回收](assets/virtqueue%20的三环结构：descriptor、available%20与%20used%20怎样串起一次%20IO%20请求/00710.webp)

客户机侧（guest OS space）：

1. 驱动在 descriptor table 里拼好 descriptor 链；
2. 驱动把链头下标写进 vring_avail.ring[idx & mask]；
3. 驱动 vring_avail.idx++；
4. 驱动检查标志位：设备需要通知吗？需要，就把队列号写进 MMIO 门铃寄存器（例如偏移 0x050）。

硬件边界：

5. 物理 CPU 捕获这次 MMIO 访问，通过 VM exit（EPT violation）陷入宿主 KVM。

宿主侧（host KVM / user space）：

6. KVM 认出这是已注册的 virtio MMIO 区域；
7. KVM 向与该 virtqueue 绑定的内部 Linux eventfd 发信号；
8. hypervisor 的事件循环（epoll）从 eventfd 上解除阻塞；
9. 设备模型直接从客户机 RAM 里读 descriptor 链；
10. 设备模型把结果写进 used ring 并 `used->idx++`；
11. 设备模型写 irqfd（宿主侧 eventfd）。

硬件边界：

12. KVM 捕获 irqfd 信号，向客户机的 Local APIC 注入一个虚拟中断。

客户机侧：

13. 客户机 Local APIC 触发中断向量；
14. 客户机 virtio 驱动的中断服务程序（ISR）醒来，读 used ring，回收缓冲区。

### 5.3 kick：一次 MMIO 写换来一次 VM exit

现代 virtio-over-MMIO 模型（Firecracker 只用这一种）里，kick 就是**一条 32 位写指令**，目标是 `QueueNotify` 寄存器（[【跳转到 12:15】](https://www.youtube.com/watch?v=2wkpXkGiflw&t=735)）：

![kick 的四步：入队 → 写 QueueNotify（偏移 0x050）→ 因 MMIO 无 RAM 背书触发 EPT violation → KVM 派发到队列绑定的 eventfd](assets/virtqueue%20的三环结构：descriptor、available%20与%20used%20怎样串起一次%20IO%20请求/00760.webp)

关键在于：这段 MMIO 地址**故意不被客户机 RAM 背书**，所以 CPU 一定撞上 EPT violation，触发一次轻量 VM exit。KVM 截住它，认出已注册的 MMIO 地址，立刻向该队列对应的 Linux eventfd 发信号；宿主上的事件循环（epoll）解除阻塞，读 descriptor、做真正的 I/O、重置 eventfd。整个过程**不需要客户机发复杂的 hypercall**。

### 5.4 完成通知：irqfd 与虚拟中断

设备做完 I/O，填好 used ring、`used->idx++`，接下来要叫醒客户机。它**不做**昂贵的用户态到内核态切换，而是往预先配置好的 **irqfd** 写一个 8 字节整数（[【跳转到 12:40】](https://www.youtube.com/watch?v=2wkpXkGiflw&t=760)）。irqfd 是 Linux 内核的一个机制，把一个 eventfd 直接绑到 KVM 的虚拟中断线上；宿主内核收到写入后，立即向客户机的虚拟 Local APIC 注入中断。客户机 CPU 拦下这个中断，挂起 VM 内正在跑的用户态进程，直接跳到 virtio 驱动的 ISR。

![完成通知的四步：写 used ring 并推进 used->idx → 写 irqfd → 宿主内核注入虚拟中断到 Local APIC → ISR 读 used ring 回收](assets/virtqueue%20的三环结构：descriptor、available%20与%20used%20怎样串起一次%20IO%20请求/00810.webp)

![used ring 的结构：vring_used_elem 只有 id 与 len 两个字段，设备按 used->idx & (QUEUE_SIZE-1) 定位槽位](assets/virtqueue%20的三环结构：descriptor、available%20与%20used%20怎样串起一次%20IO%20请求/00610.webp)

### 5.5 回收：驱动侧的最后一步

ISR 读 used ring，发现 `id=0` 那条链完成了，就把对应的 I/O 请求标记为完成，把三个 descriptor 归还到空闲池，然后返回客户机用户态。至此一次请求走完：**descriptor 被填 → available 被发布 → 门铃 → 设备处理 → used 回执 → 中断 → 回收**。

### 5.6 顺带一提：事件抑制

如果每次提交都 kick、每次完成都中断，高吞吐场景仍然吃不消。virtio 因此留了两个抑制位（[【跳转到 13:30】](https://www.youtube.com/watch?v=2wkpXkGiflw&t=810)）：

- **`VIRTQ_USED_F_NO_NOTIFY`**：设备在 `vring_used.flags` 里置位，意思是"我已经醒着在排空队列，你加新缓冲区时别再写 MMIO 门铃"；
- **`VIRTQ_AVAIL_F_NO_INTERRUPT`**：驱动在 `vring_avail.flags` 里置位，意思是"你做完别中断我，我下一轮自己来轮询 used ring"。

这两个位的取舍（低负载用中断省电、高负载用轮询/批量换吞吐）是下一小节的主题，这里只点出它们在结构里的位置。

## 六、split 与 packed：三环能不能压成一环

视频明确提到：现代 virtio 规范定义了好几种队列变体，**包括 packed virtqueue**，但"高性能 MicroVM 虚拟化的地基是 split virtqueue"（[【跳转到 03:10】](https://www.youtube.com/watch?v=2wkpXkGiflw&t=190)）。

这句话点出了本节的结构定位：三环（descriptor table + available ring + used ring）是 split 布局，也是理解一切 virtio 性能讨论的基线。packed 布局正是针对"一条请求的信息被拆散在三块内存里"这一点做的改造——它把三个环压成一个 descriptor ring，用每个 descriptor 里的 available/used 标志位代替两个独立的环，用一对回绕计数器代替两个 `idx`。具体结构与代价，见本节的另一篇：[packed virtqueue：把三环压成一个环，virtio 1.1 改的是什么](packed%20virtqueue：把三环压成一个环，virtio%201.1%20改的是什么.md)。

## 七、安全边界：被攻破的客户机内核能伪造 descriptor 吗

### 7.1 威胁模型

设想一个跑不受信任代码的 AI 沙箱：攻击者拿到客户机内核的 ring 0 权限，于是**完全控制 virtio 驱动**——可以随意构造 descriptor、随意改 struct vring_desc、随意敲 MMIO 门铃（[【跳转到 14:45】](https://www.youtube.com/watch?v=2wkpXkGiflw&t=885)）。

![威胁模型：一旦客户机内核被攻破，攻击者掌握 virtio 驱动，可以构造任意 descriptor 与洪水般敲门铃](assets/virtqueue%20的三环结构：descriptor、available%20与%20used%20怎样串起一次%20IO%20请求/00910.webp)

问题随之而来：**被攻破的客户机内核，能不能伪造一个 descriptor，骗宿主 hypervisor 去读或覆盖任意的宿主物理内存？** 答案是明确的"不能"，原因有两层。

### 7.2 第一层：GPA 必须经过地址翻译与边界检查

descriptor 里的 `addr` 是**客户机物理地址（GPA）**。客户机内核从来见不到宿主虚拟地址（HVA）或宿主物理地址（HPA）。所以 hypervisor 处理 descriptor 时**不能**把 `addr` 当裸指针解引用——那样轻则 SIGSEGV，重则读到宿主内存（[【跳转到 15:35】](https://www.youtube.com/watch?v=2wkpXkGiflw&t=935)）。

正确做法是查 KVM 在启动前登记的内存槽（struct kvm_userspace_memory_region），先做**严格边界检查**：区间 $[GPA, GPA+len]$ 必须完整落在某个已注册的客户机内存槽内。通过后再算宿主虚拟地址：

$$
HVA = slot\rightarrow userspace\_addr + (GPA - slot\rightarrow guest\_phys\_addr)
$$

![地址翻译与边界完整性：攻击者伪造 addr 与 len，先查内存槽，越界就丢弃 descriptor 或直接终止 MicroVM](assets/virtqueue%20的三环结构：descriptor、available%20与%20used%20怎样串起一次%20IO%20请求/00960.webp)

如果攻击者把 `addr` 设成 0x7fff_dead_beef 这种越界值，或者把 `len` 设成 0xffffffff 制造整数溢出回绕，内存子系统会算出"这个区间落在已分配的客户机物理地址空间之外"。在 Firecracker 这类加固过的 hypervisor 里，结果是立即的设备错误：非法缓冲区被拒绝，设备进入损坏状态，或者宿主进程直接把整台 MicroVM 终止。

### 7.3 第二层：EPT/NPT 在硅片上兜底

即使设备模型有 bug、真的替客户机发了一次越界访问，硬件虚拟化扩展仍然会拦下：Intel 的 EPT、AMD 的 NPT 在硅片级别把客户机物理页翻译成宿主物理页，**硬件保证**客户机容器里的代码读不到、也写不到分配给它的槽位之外（[【跳转到 17:15】](https://www.youtube.com/watch?v=2wkpXkGiflw&t=1035)）。

所以三环这套设计的意义不只是快：它让 virtio 拿到接近原生的直接内存 I/O 性能，同时**没有在 hypervisor 的安全边界上开口子**。

## 小结

- 全模拟设备靠"每次寄存器访问都 VM exit"工作，一次字节搬运要几千个周期；virtio 把寄存器换成共享内存里的环形队列，把每次传输的成本降到几次内存写。
- split virtqueue 是三块各连续的内存：descriptor table（16 字节一项，`addr`/`len`/`flags`/`next`）、available ring（`flags`/`idx`/`ring[]`）、used ring（`flags`/`idx`/`ring[]`，每项 `id`/`len`）。
- 三块区域各自只有一个写者：驱动写 descriptor table 与 available ring，设备写 used ring。单写者原则让整个协议无需加锁。
- `VIRTQ_DESC_F_NEXT` 串链、`VIRTQ_DESC_F_WRITE` 表示"设备可写"、`VIRTQ_DESC_F_INDIRECT` 指向一张间接表；一次块读用三个 descriptor 拼出"请求头 + 数据缓冲区 + 1 字节状态"。
- `idx` 是自由运行的 16 位计数器，不是"当前下标"；槽位靠 idx & (QUEUE_SIZE - 1) 算出，因为 queue size 必须是 2 的幂。
- 发布顺序是"先写内容，再写计数器"，中间要一道写内存屏障。
- 一次请求 14 步：填链 → 写 `ring[]` 与 `idx` → MMIO 门铃触发 VM exit → KVM 发 eventfd → 设备读链、做 I/O、写 used ring → 写 irqfd → 注入虚拟中断 → ISR 回收。
- 安全上，descriptor 里的 GPA 必须经过内存槽边界检查再翻译成 HVA，越界即拒绝；EPT/NPT 在硬件层再兜一层。

## 关键术语速查

| 术语 | 一句话解释 |
| :--- | :--- |
| virtio | OASIS 维护的半虚拟化 I/O 规范，用共享内存环形队列取代设备寄存器模拟 |
| virtqueue | 驱动与设备之间转移缓冲区所有权的环形队列，split 布局下由三块内存组成 |
| descriptor | 16 字节的缓冲区描述项：客户机物理地址、长度、标志、下一个 descriptor 下标 |
| descriptor chain | 用 `NEXT` 把多个 descriptor 串成一条请求，实现 scatter-gather |
| available ring | 驱动写、设备读的环，登记"哪些链头可以处理了" |
| used ring | 设备写、驱动读的环，登记"哪条链完成了、写了多少字节" |
| `idx` | 自由运行的 16 位计数器，双方靠差值判断待处理数量 |
| kick（门铃） | 驱动写 MMIO `QueueNotify` 寄存器通知设备，触发一次 VM exit |
| irqfd | 把 eventfd 绑到 KVM 虚拟中断线的机制，设备用它注入虚拟中断 |
| GPA / HVA | 客户机物理地址 / 宿主虚拟地址；descriptor 里存的是前者，必须经内存槽翻译 |
| packed virtqueue | virtio 1.1 引入的队列布局，把三环压成一个 descriptor ring |