# 全模拟设备的性能上限：一次门铃写换一次 VM exit

> 视频来源：[NVMe Emulation Performance Optimization](https://www.youtube.com/watch?v=y9FLKkBmww0)（YouTube · KVM Forum，Jinhao Fan，中国科学院计算技术研究所 / GSoC 实习生）｜时长约 21 分钟
> 导读：这是一份"给全模拟设备算账"的实测报告。讲者拿 QEMU 里完全模拟的 NVMe 控制器做样本，先量出它和 virtio-blk 的差距（最高 30K IOPS 对 260K IOPS），再逐项拆掉造成差距的 VM exit，最后把性能拉回同一水平。本文只讲**全模拟这条路线**的代价模型与适用性；exit 的分类与 MMIO 往返路径已在 1.3.2、1.3.3 讲过，这里不重复。

## 本讲要解决的核心问题（SCQA）

**背景**：VMM 想让客户机里的原生驱动"以为自己在操作真硬件"，就必须在用户态把设备的每一个寄存器、每一次状态变化都模拟出来。客户机访问这些寄存器时，硬件会拦住这次访问，把控制权交给 VMM——这就是 trap and emulate（陷入—模拟）。

**冲突**：设备寄存器往往落在 IO 热路径上。以 NVMe 为例，驱动每提交一条命令都要"按一次门铃"，也就是写一次设备上的 MMIO 寄存器；而对延迟敏感的应用会每条命令都按。于是**每一次 IO 都附带一次 VM exit**：客户机被挂起，VMM 在用户态解析地址、改设备状态，再恢复客户机。

**疑问**：这条"每次访问都陷入"的路线，性能上限到底由什么决定？把 VMM 里的代码优化得再快，能追上半虚拟化的 virtio 吗？

**回答（中心思想）**：全模拟设备的性能上限**被 exit 的频率锁死**，而不是被某段模拟代码的效率锁死。实测中，未优化的 QEMU NVMe 无论队列深度多大都停在 30K IOPS 左右，而 virtio-blk 能到 260K——差近一个数量级。要缩小差距，只能从"减少 exit 次数"和"让每次 exit 更便宜"两头下手：shadow doorbell buffer、ioeventfd、iothread、polling 四层优化叠加后，峰值 IOPS 提升 11 倍，才与 virtio-blk 持平。这也解释了全模拟设备为什么至今仍存在，却通常只出现在启动阶段、冷门设备和"要跑未修改系统"的场合。

## 一、全模拟设备：客户机看到真硬件，VMM 里是一段代码

### 1.1 三条路线的定位

设备虚拟化有三条路线，区别只在"客户机看到什么、谁来干活"：

| 路线 | 客户机看到 | 谁处理 IO | 是否需要改驱动 |
| :--- | :--- | :--- | :--- |
| 全模拟（full emulation） | 一块真实的 Intel e1000 网卡、IDE/SATA 控制器、NVMe SSD | VMM 用户态逐寄存器模拟 | 不需要，原生驱动即可 |
| 半虚拟化（virtio） | 一个"明说是虚拟"的设备 | 前后端按共享队列协作 | 需要 virtio 驱动 |
| 设备直通（VFIO） | 一块真实的物理设备 | 设备自己 DMA，VMM 只做映射 | 不需要，但一台设备只能给一台虚拟机 |

全模拟的特别之处在于：设备完全由软件凭空造出来。客户机里跑的是原厂驱动，它写寄存器、读状态、等中断，全都按真实硬件的规矩来；VMM 在另一侧把这些动作翻译成对宿主资源的操作，而宿主上并不需要真的插着一块这样的设备。

### 1.2 样本：QEMU 的模拟 NVMe 控制器

讲者选的样本是 QEMU 里的 `hw/nvme`：一个基于 PCIe 的 NVMe 控制器，支持 NVMe 1.4 的全部强制特性 [【跳转到 01:12】](https://www.youtube.com/watch?v=y9FLKkBmww0&t=72)。它的定位很典型——**开发者和研究者用它来验证新的 NVMe 特性、试验驱动、搭建与 NVMe 设备交互的系统** [【跳转到 01:12】](https://www.youtube.com/watch?v=y9FLKkBmww0&t=72)。

![QEMU NVMe 的现状：被开发者用来试验新特性，但性能低得惊人——最高只有 30K IOPS，与 virtio-blk 差距巨大](assets/全模拟设备的性能上限：一次门铃写换一次VM%20exit/00090.webp)

这张幻灯片上的基线数据值得记住（FIO 4KB 随机读，宿主是 96 核 Xeon Gold 6248R、256GB 内存、Linux 5.15）：

| 队列深度 QD | 1 | 4 | 16 | 64 |
| :--- | ---: | ---: | ---: | ---: |
| 模拟 NVMe（KIOPS） | 31 | 30 | 30 | 30 |
| virtio-blk（KIOPS） | 59 | 185 | 260 | 256 |

注意模拟 NVMe 那一行：**队列深度从 1 加到 64，IOPS 一点没涨**。这不是"设备不够快"，而是"每次提交都要停下来等 VMM"——加队列深度本来是为了让设备并行处理更多请求，但在这条路径上，请求再多也得一个一个穿过 exit 这道门。

### 1.3 为什么每次访问都必须陷入

关键在于设备寄存器的地址性质。客户机访问普通内存时，CPU 直接读写，不会打扰 VMM；但设备的寄存器被映射成 **MMIO**（memory-mapped I/O，内存映射 IO）——地址看起来在内存空间里，实际背后没有 RAM，只有一段"没有映射"的空洞。客户机一碰这个地址，硬件就触发异常，KVM 把这次访问打包成一次 VM exit 交给用户态 VMM。

所以"全模拟"的代价不是"模拟得慢"，而是**结构性的**：客户机每碰一次设备寄存器，就要完整走一遍"停客户机 → 存状态 → 进 VMM → 查设备模型 → 改状态 → 回客户机"。1.3.3 里实测过这条路径的分段耗时（vfio-user 场景）：陷入本身约 2.5 微秒，而用户态处理要 50 微秒量级。设备寄存器访问越频繁，这笔钱就付得越多。

## 二、门铃：把 exit 频率放大到 IO 频率

### 2.1 NVMe 的队列与门铃

NVMe 用一对对环形队列来传命令：提交队列（SQ）放命令，完成队列（CQ）放结果。队列由两个指针描述——生产者推进 tail，消费者推进 head。队列本身放在客户机内存里，设备可以直接读，**不需要陷入** [【跳转到 03:03】](https://www.youtube.com/watch?v=y9FLKkBmww0&t=183)。

![NVMe 的基本模型：环形无锁队列 + head/tail 指针，主机通过"按门铃"告诉设备队列里有新条目；门铃是一个只写的 MMIO 寄存器](assets/全模拟设备的性能上限：一次门铃写换一次VM%20exit/00183.webp)

问题出在"通知"这一步。设备怎么知道主机往队列里放了新命令？靠主机写一个特殊寄存器——**doorbell（门铃）**。它是设备上的一个只写 MMIO 寄存器，写它就是在"按门铃" [【跳转到 03:53】](https://www.youtube.com/watch?v=y9FLKkBmww0&t=233)。

在协议层面这一步没有替代品：队列在内存里，设备不会自己盯着看；主机必须通过一次寄存器写来"踢"它。而寄存器写 = MMIO = VM exit。（后来讲者用轮询绕开了这一步，见 4.4。）

### 2.2 一条命令两次门铃

更糟的是次数。一条 NVMe 命令要按两次门铃：一次写提交队列的 tail（告诉设备"有新命令"），一次写完成队列的 head（告诉设备"这个完成项我取走了"）[【跳转到 04:14】](https://www.youtube.com/watch?v=y9FLKkBmww0&t=254)。

理论上可以攒：主机可以连续放好几条命令再按一次门铃，也可以攒几个完成项再写完成门铃。但**设备对此没有控制权**，攒不攒完全取决于驱动或应用。对延迟敏感的应用不愿意等，就会每提交一条命令按一次门铃 [【跳转到 04:39】](https://www.youtube.com/watch?v=y9FLKkBmww0&t=279)。

![把 MMIO 放回图里：一条命令两次门铃写，应用为降延迟会频繁按铃，于是每次 IO 都背上 trap-emulate 的开销](assets/全模拟设备的性能上限：一次门铃写换一次VM%20exit/00329.webp)

讲者的原话很直接：这些 MMIO 写在虚拟化下都很贵，因为模拟设备用的是传统的 trap-and-emulate 机制——内存访问引发 VM exit，MMIO 处理函数执行期间客户机被挂起 [【跳转到 05:04】](https://www.youtube.com/watch?v=y9FLKkBmww0&t=304)、[【跳转到 05:29】](https://www.youtube.com/watch?v=y9FLKkBmww0&t=329)。设备还会把命令处理推迟到主循环线程，好尽快从 MMIO 处理函数里退出来——**连 VMM 自己都在躲这笔开销**。

### 2.3 代价模型：频率乘以单次行程

把上面的观察写成式子，全模拟设备在 IO 路径上的开销可以近似成：

$$
T_{\text{device}} \approx N_{\text{doorbell}} \times \left( t_{\text{exit}} + t_{\text{emulate}} \right)
$$

其中 $N_{\text{doorbell}}$ 是门铃次数（约等于 IO 次数乘以每条命令的门铃数），$t_{\text{exit}}$ 是陷入与恢复的固定成本，$t_{\text{emulate}}$ 是 VMM 里解析地址、更新设备状态的成本。

这个式子的含义是：**优化 $t_{\text{emulate}}$ 只能线性地改善，而减少 $N_{\text{doorbell}}$ 才能改变量级**。而且当所有设备共用一个主循环线程时，$t_{\text{emulate}}$ 还会被其他设备排队放大——这就是后文 iothread 要解决的问题。

## 三、上限为什么是 30K IOPS

回到基线表格：QD 从 1 涨到 64，模拟 NVMe 始终 30K IOPS 左右，而 virtio-blk 从 59K 涨到 260K。差异的来源可以拆成两条：

1. **每次提交都要 exit**：队列深度再大，每条命令的门铃写仍要单独陷入一次，客户机在陷入期间是停住的；
2. **处理被串行化**：所有设备的 MMIO 处理都在 QEMU 主循环线程里排队，设备越多，单次 exit 的实际等待越长。

于是这条路线有一个硬上限：**IOPS 不可能超过"单位时间内能完成多少次 exit"**。这也解释了为什么讲者把 VM exit 称为"性能低下的头号嫌疑" [【跳转到 05:54】](https://www.youtube.com/watch?v=y9FLKkBmww0&t=354)——不是设备模型写得不好，而是每次 IO 都被强制插入了一次跨越客户机与宿主的长途旅行。

对全模拟路线来说，这个结论是通用的：e1000 网卡的收发包、IDE 控制器的逐扇区读写、VGA 的每次寄存器访问，都遵循同一个模型：寄存器被访问得越频繁、每次操作搬运的数据越少，exit 频率就越高，性能也越差。**全模拟的性能上限由设备的寄存器访问频率决定，而不是由宿主 CPU 的速度决定。**

## 四、四层优化：把 exit 变少、变便宜

讲者的优化清单在项目里早就写好了，一共四项，正好对应上一节式子的两个因子 [【跳转到 02:00】](https://www.youtube.com/watch?v=y9FLKkBmww0&t=120)：

![优化清单：用 shadow doorbell buffer 减少 MMIO、用 ioeventfd 让剩下的 MMIO 更轻、用 iothread 给设备独立线程、用 polling 压延迟](assets/全模拟设备的性能上限：一次门铃写换一次VM%20exit/00120.webp)

### 4.1 第一层：把门铃搬到普通内存（shadow doorbell buffer）

NVMe 1.3 引入了一对虚拟化特性 **shadow doorbell buffer**，思路和 virtio 的 `VIRTIO_F_EVENT_IDX` 非常相似：主机注册两个缓冲区，一个叫 doorbell buffer（由主机更新），一个叫 event index buffer（由控制器更新），两者分别镜像"主机认为的门铃值"和"控制器已经处理到哪" [【跳转到 06:02】](https://www.youtube.com/watch?v=y9FLKkBmww0&t=362)、[【跳转到 06:22】](https://www.youtube.com/watch?v=y9FLKkBmww0&t=382)。

![shadow doorbell buffer 的两个缓冲区：doorbell buffer 由主机写，event index buffer 由控制器写，都是普通内存，写它们不会引发 VM exit](assets/全模拟设备的性能上限：一次门铃写换一次VM%20exit/00382.webp)

关键点在于：**这两个缓冲区是普通内存，写它们不引发 VM exit** [【跳转到 06:47】](https://www.youtube.com/watch?v=y9FLKkBmww0&t=407)。于是绝大多数"我放了新命令"的通知，从一次陷入变成了一次普通的内存写。

只有一种情况还得按真门铃：当 shadow doorbell 的值超过 event index，说明设备正空闲、没在消费队列，主机必须踢它一下把它唤醒 [【跳转到 07:19】](https://www.youtube.com/watch?v=y9FLKkBmww0&t=439)。也就是说，**忙的时候不陷入，闲的时候才陷入**——这正好把 exit 频率从"IO 频率"降到了"唤醒频率"。

### 4.2 第二层：让剩下的 MMIO 只写一个 eventfd（ioeventfd）

剩下那些"唤醒"用的 MMIO 还是贵。QEMU 的 **ioeventfd** 机制把处理函数压缩到极致：MMIO 处理函数只是往一个 eventfd 里写一下，然后立刻恢复客户机运行，不必把控制权交回 QEMU 主循环 [【跳转到 07:44】](https://www.youtube.com/watch?v=y9FLKkBmww0&t=464)、[【跳转到 08:09】](https://www.youtube.com/watch?v=y9FLKkBmww0&t=489)。

![ioeventfd 的适用条件：即使有 shadow doorbell，设备空闲时仍需一次 MMIO；ioeventfd 让这次 MMIO 只写 eventfd 就返回，不回到 QEMU 主循环](assets/全模拟设备的性能上限：一次门铃写换一次VM%20exit/00464.webp)

但 ioeventfd 不能普遍替代门铃写：它只告诉你"某个内存位置被写了"，不告诉你写进去的值是什么 [【跳转到 08:24】](https://www.youtube.com/watch?v=y9FLKkBmww0&t=504)。巧的是，用了 shadow doorbell 之后，MMIO 处理函数本来也不需要这个值——值已经在 shadow doorbell 缓冲区里了，处理函数直接去读缓冲区即可 [【跳转到 08:49】](https://www.youtube.com/watch?v=y9FLKkBmww0&t=529)。

两项叠加的效果：讲者说做到这一步"已经接近 virtio-blk 了" [【跳转到 09:11】](https://www.youtube.com/watch?v=y9FLKkBmww0&t=551)。

### 4.3 第三层：给每个设备一个线程（iothread）

前两层解决的是"次数"和"单次成本"，第三层解决的是"排队"。在原来的架构里，所有设备都在 QEMU 的主循环线程里模拟，主循环因此成了瓶颈——多台设备同时有 IO 时，它们要排同一个线程 [【跳转到 09:39】](https://www.youtube.com/watch?v=y9FLKkBmww0&t=579)。

![原架构的瓶颈：四个客户机 IO 进程的请求全部涌向同一个主循环线程，NVMe0 到 NVMe3 互相排队](assets/全模拟设备的性能上限：一次门铃写换一次VM%20exit/00579.webp)

QEMU 的 **iothread** 特性允许每个设备用一个独立线程，设备之间互不干扰。但把模拟搬到独立线程，先得解决线程安全：QEMU 默认的中断注入不是线程安全的——所有设备都在主循环线程时这不成问题，换成 iothread 就不行了 [【跳转到 10:09】](https://www.youtube.com/watch?v=y9FLKkBmww0&t=609)。

解决办法有两条，都基于 eventfd：一是 KVM 的 **irqfd**，把 MSI-X 中断断言直接绑到 eventfd 上，绕过 QEMU 的中断模拟；二是在 irqfd 不可用时注册普通 event notifier，把中断断言的工作交回主循环线程 [【跳转到 10:34】](https://www.youtube.com/watch?v=y9FLKkBmww0&t=634)、[【跳转到 10:59】](https://www.youtube.com/watch?v=y9FLKkBmww0&t=659)。

有意思的是，irqfd 并没有带来明显的性能提升（Stefan 也说过它不一定更快），它真正的价值是**解决线程安全** [【跳转到 11:32】](https://www.youtube.com/watch?v=y9FLKkBmww0&t=692)。另外，admin 命令（建队列、配 doorbell buffer）涉及读内存事务、要拿 QEMU 大锁，所以 admin 队列仍留在主循环线程——它不在快路径上，挪过去也没收益 [【跳转到 11:56】](https://www.youtube.com/watch?v=y9FLKkBmww0&t=716)。

### 4.4 第四层：干脆不按门铃（polling）

最后一层是轮询：设备端主动去看提交队列有没有新条目，命令一到就开始处理，不用等门铃 [【跳转到 13:18】](https://www.youtube.com/watch?v=y9FLKkBmww0&t=798)。

![polling 的完整路径：客户机不再为 IO 队列按门铃，vCPU 线程里的 KVM 仍会因唤醒写触发 eventfd，iothread 主动轮询 IO 队列，admin 队列仍走主循环](assets/全模拟设备的性能上限：一次门铃写换一次VM%20exit/00798.webp)

理论上，轮询可以**完全消掉 MMIO**：既然设备一直在主动检查 doorbell 的值，主机就不必再写寄存器通知它。实现上，QEMU 的 AIO context 已经提供了轮询框架，NVMe 只需要提供自己的轮询函数——去读提交队列的 tail 和 shadow doorbell 寄存器，检查有没有新条目 [【跳转到 13:43】](https://www.youtube.com/watch?v=y9FLKkBmww0&t=823)。

### 4.5 结果：11 倍，追平 virtio-blk

四项优化加起来约 700 行代码，峰值 IOPS 提升 11 倍 [【跳转到 14:29】](https://www.youtube.com/watch?v=y9FLKkBmww0&t=869)：

| 队列深度 QD | 1 | 4 | 16 | 64 |
| :--- | ---: | ---: | ---: | ---: |
| 模拟 NVMe（KIOPS） | 53 | 155 | 245 | 309 |
| virtio-blk（KIOPS） | 59 | 185 | 260 | 256 |
| 模拟 NVMe + polling（KIOPS） | 123 | 165 | 189 | 191 |
| virtio-blk + polling（KIOPS） | 88 | 212 | 210 | 213 |

![优化后的对比：非轮询配置下模拟 NVMe 已与 virtio-blk 持平，QD 64 时甚至更高；轮询在高队列深度下反而更差，讲者仍在排查](assets/全模拟设备的性能上限：一次门铃写换一次VM%20exit/00844.webp)

两个细节值得注意：

- 非轮询配置下，模拟 NVMe 在 QD 64 时反超 virtio-blk（309 对 256）。讲者猜测原因是**内核里的 NVMe 驱动比 virtio-blk 驱动优化得更好**，而两边用的机制已经很相似 [【跳转到 14:04】](https://www.youtube.com/watch?v=y9FLKkBmww0&t=844)。
- 轮询在低队列深度下收益巨大（QD 1 时 123 对 53），但在高队列深度下反而更差，讲者也没查出原因，还在征集解释 [【跳转到 14:29】](https://www.youtube.com/watch?v=y9FLKkBmww0&t=869)。

这组数据正好印证了前面的代价模型：**全模拟路线的性能不是"优化代码"能救的，而是"减少 exit"才能救的**。四项优化里，前三项都在减少或绕开 exit，第四项干脆把通知机制整个删掉。

## 五、这条路线的边界：能跑未修改的系统，但代价与功能都有限

### 5.1 它为什么还存在

讲者对这个设备的定位说得很清楚：它主要被开发者和研究者用来**验证新的 NVMe 特性、试验驱动和系统** [【跳转到 01:12】](https://www.youtube.com/watch?v=y9FLKkBmww0&t=72)。这正是全模拟路线不可替代的价值：

- **不需要改客户机**。客户机里跑的是原厂 NVMe 驱动，VMM 不需要 virtio 驱动、不需要客户机内核配合，任何未修改的操作系统都能直接启动；
- **能提供"真设备"的语义**。研究新特性、复现真实硬件行为、给驱动做兼容性测试时，必须有一个"看起来就是真硬件"的设备，virtio 给不了；
- **是兜底路径**。当 virtio 驱动不可用（老系统、特殊 OS、启动早期的固件阶段）时，全模拟是让客户机把 IO 跑起来最直接的方式。

代价则是性能：即使做到极致，也只是"追平 virtio-blk"，而不是超过它。这也解释了现代 VMM 的普遍做法——**全模拟设备通常只用于启动阶段和冷门设备，热路径交给 virtio 或直通**。本系列后面两节会分别讲半虚拟化和直通，这里只需要记住定位：全模拟是"兼容性优先"的那条路。

### 5.2 一个规范违规暴露的脆弱性

优化过程中还撞上一个值得所有写设备模型的人记住的坑。NVMe 规范要求 doorbell buffer 用在**所有队列**上，包括 admin 队列；但现有的所有驱动（Linux 内核、SPDK）和模拟设备（SPDK 的 vfio-user target）**没有一个在 admin 队列上用 shadow doorbell** [【跳转到 17:14】](https://www.youtube.com/watch?v=y9FLKkBmww0&t=1034)。

![规范与现实的冲突：规范要求所有队列都用 doorbell buffer，但没有任何现存驱动在 admin 队列上这么做，而且这个行为没法在驱动里修](assets/全模拟设备的性能上限：一次门铃写换一次VM%20exit/01034.webp)

后果是两难：如果设备严格按规范等驱动更新 shadow doorbell，不合规的驱动就永远不发那次 MMIO 写，设备收不到命令；如果设备迁就不合规驱动，又破坏了按规范实现的驱动。而且驱动侧没法修——没有办法判断设备是否合规 [【跳转到 17:39】](https://www.youtube.com/watch?v=y9FLKkBmww0&t=1059)。

最终的解法是 QEMU NVMe 维护者 Keith 提出的一个"hack"：在 MMIO 处理函数里，用门铃寄存器的值覆盖 shadow doorbell 缓冲区的值 [【跳转到 18:28】](https://www.youtube.com/watch?v=y9FLKkBmww0&t=1108)。

![折中方案：在 doorbell 的 MMIO 处理函数里用寄存器值覆盖 shadow doorbell 缓冲区；因为处在 VM exit 上下文里，这样做是安全的，合规与不合规驱动都能工作](assets/全模拟设备的性能上限：一次门铃写换一次VM%20exit/01108.webp)

这个补丁之所以安全，恰恰是因为它跑在 **VM exit 上下文**里——客户机已被挂起，VMM 独占设备状态，不存在并发写。这个小例子说明：全模拟设备的"兼容性优势"不是免费的，它意味着设备模型要同时容纳规范、现实驱动和各种历史包袱。

### 5.3 要上云还缺什么

讲者明确说，这些优化让模拟 NVMe 有潜力成为云上 virtio-blk 的替代品，但**这个设备最初的目标是开发和测试**，要支持云端用例还差几件事 [【跳转到 19:18】](https://www.youtube.com/watch?v=y9FLKkBmww0&t=1158)：

![未来工作：要成为云上可用的 virtio-blk 替代品，还缺热迁移支持、去掉"假特性"的精简版本和安全审计](assets/全模拟设备的性能上限：一次门铃写换一次VM%20exit/01158.webp)

- **热迁移（live migration）**：设备状态要能序列化、能在另一台机器上恢复；
- **精简版本**：把 Simple Copy、Zoned Namespace 模拟等"只为测试而存在"的特性拆掉，减少攻击面；
- **安全审计**：讲者明确说，要在规模化部署前做一次彻底的安全审计；
- **更细的 iothread**：目前一个控制器一个线程，模拟高端 SSD 不够用，未来可能要按 namespace 甚至按提交队列分线程——但提交队列并不绑定到某个 namespace 和底层块设备，做起来并不简单 [【跳转到 20:08】](https://www.youtube.com/watch?v=y9FLKkBmww0&t=1208)。

代码的落地情况：shadow doorbell 和 ioeventfd 支持已进入 QEMU 7.1，irqfd、iothread 和轮询还在评审中 [【跳转到 20:33】](https://www.youtube.com/watch?v=y9FLKkBmww0&t=1233)。

## 六、把这条路线放回三条路线的坐标里

用一句话概括三条路线的取舍：

- **全模拟**：客户机零改动，兼容性最好，但每次寄存器访问都要 exit，性能上限被 exit 频率锁死；
- **半虚拟化（virtio）**：客户机装一个"明说是虚拟"的驱动，把"每次操作一次寄存器"换成"批量描述符 + 一次通知"，exit 次数显著下降；
- **设备直通（VFIO）**：设备直接 DMA 访问客户机内存，VMM 基本退出数据路径，性能接近裸机，但一台设备只能给一台虚拟机。

本节讲的这个案例，正好是全模拟路线的"极限实验"：把能想到的优化全加上，也只是追平 virtio-blk（个别配置略高）。这就是为什么现代 VMM 把全模拟留给启动和冷门设备，而把热路径交给后两条路线。

## 小结

- 全模拟设备让客户机里的原生驱动以为自己在操作真硬件，代价是**每次寄存器访问都要陷入用户态 VMM**。
- 设备寄存器是 MMIO，客户机一碰就触发 VM exit；NVMe 一条命令要按两次门铃，延迟敏感的应用会每条命令都按。
- 开销可以写成"门铃次数 × 单次陷入与模拟成本"；减少次数比优化单次成本更能改变量级。
- 未优化的模拟 NVMe 无论队列深度多大都停在 30K IOPS，virtio-blk 能到 260K——**上限由 exit 频率锁死**。
- 四层优化（shadow doorbell、ioeventfd、iothread、polling）把峰值 IOPS 提升 11 倍，才追平 virtio-blk；前三层都在减少或绕开 exit。
- 全模拟仍然存在的理由是兼容性：不改客户机、能跑任何未修改的系统、能提供真设备语义、是 virtio 不可用时的兜底；代价是性能与功能（缺热迁移、需安全审计）。
- 现代 VMM 的普遍做法：全模拟用于启动阶段与冷门设备，热路径交给 virtio 或直通。

## 关键术语速查

| 术语 | 一句话解释 |
| :--- | :--- |
| 全模拟（full emulation） | VMM 在用户态逐寄存器模拟一个真实设备，客户机用原生驱动即可 |
| trap and emulate | 客户机访问敏感资源时被硬件拦住，控制权交给 VMM 模拟，再返回客户机 |
| MMIO | 内存映射 IO，设备寄存器被映射到地址空间，访问它会触发陷入而非读写 RAM |
| doorbell（门铃） | 设备上的只写 MMIO 寄存器，主机写它来通知设备"队列里有新条目" |
| VM exit | 客户机因敏感操作被暂停、控制权交回 VMM 的那次切换 |
| shadow doorbell buffer | NVMe 1.3 的虚拟化特性，用两块普通内存缓冲区镜像门铃，写它们不触发 exit |
| ioeventfd | QEMU/KVM 机制，MMIO 处理函数只写一个 eventfd 就返回，不必回到主循环 |
| iothread | QEMU 里给单个设备用的独立模拟线程，避免所有设备挤在主循环线程 |
| irqfd | KVM 机制，把中断断言直接绑到 eventfd，绕开 QEMU 的中断模拟并解决线程安全 |
| polling（轮询） | 设备端主动检查队列，不等门铃通知，理论上可完全消掉 MMIO |
| virtio-blk | 半虚拟化块设备，客户机装专门驱动，用共享队列批量提交请求 |
| QD（队列深度） | 同时在途的 IO 请求数，用来压测设备并行处理能力 |