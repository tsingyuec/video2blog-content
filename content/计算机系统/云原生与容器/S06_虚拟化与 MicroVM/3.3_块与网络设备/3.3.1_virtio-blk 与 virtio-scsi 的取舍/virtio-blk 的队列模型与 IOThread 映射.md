# virtio-blk 的队列模型：每 vCPU 一条 virtqueue，瓶颈却在宿主的单个线程

> 视频来源：[IOThread Virtqueue Mapping: Improving virtio-blk SMP scalability in QEMU](https://www.youtube.com/watch?v=tVIRDdf79-0)（YouTube · KVM Forum 2024，讲者 Stefan Hajnoczi，Red Hat）｜时长约 28 分钟
> 导读：这支演讲回答一个很具体的问题——virtio-blk 早就是多队列设备了，为什么多 vCPU 的虚拟机跑并发 I/O 仍然要付 20%~30% 的虚拟化开销？答案是 QEMU 侧的处理线程，以及它在 QEMU 9.0 里的解法（IOThread Virtqueue Mapping）。本文讲的是 virtio-blk 这条**队列模型**的来龙去脉；virtio-scsi 为什么存在、它在功能与队列上和 virtio-blk 怎么分工，见同节另一篇《virtio-scsi 与 virtio-blk 的设计取舍》。

## 本讲要解决的核心问题（SCQA）

**背景**：virtio-blk 是 KVM 上最常用的高性能块设备。它天生是多队列（multi-queue）设备：一个 virtio-blk 设备可以有多条 virtqueue，每条 virtqueue 对应一个 vCPU，客户机里的驱动提交 I/O 时不需要跨 CPU 抢锁，完成中断也能直接回到提交请求的那个 vCPU。[【跳转到 01:09】](https://www.youtube.com/watch?v=tVIRDdf79-0&t=69)

**冲突**：既然客户机侧的队列已经分开了，为什么把虚拟机做大——比如 16 个 vCPU、几十个线程同时压 I/O——虚拟化开销反而涨到 20%~30%？演讲者一开始就承认，过去 virtio-blk 的优化几乎都盯着"单 vCPU 拼命压 I/O"这个场景，多 vCPU 并发提交的场景是被忽略的。[【跳转到 00:19】](https://www.youtube.com/watch?v=tVIRDdf79-0&t=19)

**疑问**：队列都在客户机里分好了，堵塞点到底在哪一层？

**回答（中心思想）**：堵塞点在**宿主侧**。在 QEMU 里，一个 virtio-blk 设备的所有 virtqueue 由**同一个 QEMU 线程**模拟，客户机分出多少条队列，最终都漏斗到这一个线程上。QEMU 9.0 的做法是把这个漏斗拆开：让不同的 virtqueue 绑定到不同的宿主 IOThread（IOThread Virtqueue Mapping）。在本地 NVMe 上，4 个 IOThread 能让 4K 随机读的 IOPS 翻倍——但演讲者反复强调，这**不是一项"降低开销"的优化，而是一项"给虚拟机分配更多资源"的功能**：宿主没有空闲 CPU、磁盘已经饱和时，它一点忙也帮不上。

## 一、多队列只解决了客户机侧的竞争

### 1.1 每条 virtqueue 归一个 vCPU，提交与完成都不跨核

virtio 的基本模型是一个共享内存环形队列（virtqueue）：客户机驱动把请求描述符放进环里，敲一下"门铃"（doorbell，一次 MMIO/PIO 写），宿主侧取走请求、做完 I/O，再把结果放回环里并发一个中断。这套三环结构在 3.2 节已经拆过，这里只看它的**多队列**形态。

virtio-blk 的多队列设计非常直接：**每个 vCPU 有自己的 virtqueue**。这样做换来两个好处[【跳转到 01:34】](https://www.youtube.com/watch?v=tVIRDdf79-0&t=94)：

- **提交无竞争**：客户机驱动提交或完成 I/O 时，不需要为了共用一条队列而加锁、不需要和别的 CPU 通信，每条队列独立并发地跑。
- **完成中断落到提交者**：完成中断可以直接投递到提交这条 I/O 的那个 vCPU——也就是应用线程正在跑、缓存最热的那颗核。如果没有这个能力，中断只能随便挑一颗 CPU 投递，再由它去通知真正干活的那颗，白白多出一段延迟。

![virtio-blk 多队列：vCPU0、vCPU1 各有一条 virtqueue 直连 virtio-blk 设备，幻灯片上写着"提交无竞争、完成中断回到提交者"](assets/virtio-blk%20的队列模型与%20IOThread%20映射/00119.webp)

这不是什么新奇设计。演讲者特意指出，网卡早就是这么干的，NVMe 的 PCI 接口也是同样的多队列模型。而且 QEMU **默认就开着**：你启动一台 16 vCPU 的虚拟机，什么都不用写，它的 virtio-blk 设备自动就有 16 条 virtqueue。

### 1.2 队列分开之后，SMP 开销依然是 20%~30%

问题就出在这里：设计是对的，默认也是开的，可大虚拟机的扩展性还是不行。演讲者给出的量级是，多 vCPU 并发提交 I/O 时，虚拟化开销大约 20%，甚至 30%；而单 vCPU 压 I/O 的场景下这个数字要好看得多。[【跳转到 00:44】](https://www.youtube.com/watch?v=tVIRDdf79-0&t=44)

用一句定义把"开销"说清楚：

$$
\text{overhead} = \frac{T_{\text{virt}} - T_{\text{bare}}}{T_{\text{bare}}}
$$

其中 $T_{\text{bare}}$ 是同样的负载直接跑在裸机上完成所需的时间，$T_{\text{virt}}$ 是在虚拟机里完成所需的时间。这个比值在单 vCPU 场景下很小，在多 vCPU 并发 I/O 场景下就涨到了 20%~30%——对把虚拟机当主力生产环境的人来说，这个数字太大了。

![virtio-blk 在 QEMU 里的性能挑战：多 vCPU 提交 I/O 时开销很高，而"虚拟机有很多 vCPU"如今是常态而非特例](assets/virtio-blk%20的队列模型与%20IOThread%20映射/00019.webp)

## 二、真正的漏斗在宿主的一个线程

### 2.1 一个 virtio-blk 设备的所有 virtqueue 由同一个 QEMU 线程模拟

答案在 QEMU 的实现里：**一个 virtio-blk 设备由一个 QEMU 线程模拟，它的所有 virtqueue 都在那一个线程里处理**。客户机里有 4 个 vCPU、4 条队列同时灌 I/O，宿主侧却只有一个线程在替它们干活——这就是漏斗的形状。[【跳转到 03:14】](https://www.youtube.com/watch?v=tVIRDdf79-0&t=194)

![漏斗图：4 个 vCPU 的请求全部汇入"QEMU with 1 IOThread"，一个线程处理一个设备的所有 virtqueue](assets/virtio-blk%20的队列模型与%20IOThread%20映射/00244.webp)

这个线程干的活并不轻。一条 I/O 在宿主侧要走完[【跳转到 04:04】](https://www.youtube.com/watch?v=tVIRDdf79-0&t=244)：

1. 解析 virtqueue 里的请求描述符；
2. 经过 QEMU 块层（block layer）——镜像格式（比如 qcow2）、各种块层特性都在这一层；
3. 块层决定"缓冲区在哪、逻辑块地址是多少"，然后发起一次系统调用，可能是 Linux AIO，也可能是 io_uring；
4. 宿主内核再走一遍：解析 AIO/io_uring 请求，穿过 VFS 和内核块层，交给真正的磁盘驱动（比如 NVMe 驱动）；
5. 反向再爬回来：QEMU 组装 virtqueue 响应，向客户机注入完成中断。

路径很长，每一段都要烧 CPU 周期。单 vCPU 时这条路径也许还能跑满盘；一旦 4 个 vCPU 同时压过来，一个线程就撑不住了。

### 2.2 先做实验：如果每条队列都有自己的线程会怎样

在动手改 QEMU 之前，演讲者先做了一个"作弊"的模拟实验：在客户机里创建**多个 virtio-blk 设备**，让它们指向同一个镜像文件，并给每个设备配一个专属的 IOThread。这样等价于"每条 virtqueue 都有自己的线程"，只是靠多设备凑出来的。镜像上没有文件系统，只做块设备级压测，所以多设备共享同一份数据不会写坏。[【跳转到 05:19】](https://www.youtube.com/watch?v=tVIRDdf79-0&t=319)

结果很明确：4 个设备（4 个 IOThread）时，4K 随机读的 IOPS 大约是单设备的 2 倍，能把盘压满。[【跳转到 05:44】](https://www.youtube.com/watch?v=tVIRDdf79-0&t=344)

![模拟实验：客户机里放多个 virtio-blk 设备、各配一个 IOThread 访问同一块盘，4 个设备带来约 2 倍 IOPS](assets/virtio-blk%20的队列模型与%20IOThread%20映射/00344.webp)

## 三、QEMU 9.0 的 IOThread Virtqueue Mapping

### 3.1 前提：QEMU 块层先要变成多线程

真正实现这件事，难点不在 virtio，而在 QEMU 自己。QEMU 的块层历史上是单线程的，要做到"多条 virtqueue 并行处理"，先得让块层支持多线程的请求处理。这项基础设施在 **QEMU 9.0** 落地，是 Kevin Wolf、Emanuele Esposito、Paolo Bonzini 和演讲者四个人多年工作的结果。[【跳转到 07:04】](https://www.youtube.com/watch?v=tVIRDdf79-0&t=424)

![QEMU 9.0 的块层获得了多线程请求处理能力，这是 IOThread Virtqueue Mapping 的地基](assets/virtio-blk%20的队列模型与%20IOThread%20映射/00449.webp)

有了地基，virtio-blk 的 IOThread Virtqueue Mapping 才成为可能：它让**客户机侧的多队列在宿主侧也真的并行**——把不同的 virtqueue 分配给不同的宿主 IOThread。

### 3.2 怎么配：libvirt 一行标签，QEMU 一个数组

libvirt 侧的写法（libvirt 10.0 起，由 Peter Krempa 实现）是给磁盘加一组 `<iothread>` 引用，virtqueue 会**轮转（round-robin）**分配给这些 IOThread[【跳转到 08:05】](https://www.youtube.com/watch?v=tVIRDdf79-0&t=485)：

```xml
<domain>
  ...
  <vcpu>4</vcpu>
  <iothreads>2</iothreads>
  ...
  <devices>
    <disk ...>
      <driver name='qemu' cache='none' io='native' .../>
      <iothreads>
        <iothread id='1'/>
        <iothread id='2'/>
      </iothreads>
    </disk>
  </devices>
</domain>
```

4 条 virtqueue、2 个 IOThread 时，分配结果是：vq0→IOThread1、vq1→IOThread2、vq2→IOThread1、vq3→IOThread2。

![libvirt 语法：`<iothreads>` 里列出 IOThread id，virtqueue 按轮转分配；幻灯片注明这个特性是为 `cache='none' io='native'` 设计的](assets/virtio-blk%20的队列模型与%20IOThread%20映射/00485.webp)

想精确控制哪条队列落到哪个线程，就得用 QEMU 的 JSON 语法，直接给 `iothread-vq-mapping` 一个数组，里面写明 IOThread 和它负责的 virtqueue 编号[【跳转到 09:45】](https://www.youtube.com/watch?v=tVIRDdf79-0&t=585)：

```text
$ qemu-system-x86_64 ...
    -smp 4
    -object iothread,id=iothread0
    -object iothread,id=iothread1
    ...
    -device '{"driver": "virtio-blk-pci",
              "iothread-vq-mapping": [
                 {"iothread": "iothread0", "vqs": [0, 3]},
                 {"iothread": "iothread1", "vqs": [1, 2]}]}'
```

![QEMU 语法：`iothread-vq-mapping` 数组可以按 virtqueue 编号精确分配，这个参数只能用 JSON 形式写](assets/virtio-blk%20的队列模型与%20IOThread%20映射/00585.webp)

为什么只能写 JSON？因为 QEMU 传统的命令行解析器处理不了这种嵌套结构。演讲者顺带给了个实用技巧：先用 libvirt 配好，再让 libvirt 把生成的 QEMU 命令行 dump 出来，照抄进自己的脚本。

### 3.3 为什么是"映射"而不是"共享"：vring 是单消费者结构

一个容易犯的直觉错误是：既然有多个 IOThread，为什么不让它们一起处理同一条 virtqueue，谁空谁上？

因为 virtqueue 背后的共享内存结构 vring 是**单消费者（single consumer）**的。一条 virtqueue 只能交给一个 IOThread 处理，正因为如此，IOThread 里才完全不需要加锁。[【跳转到 09:20】](https://www.youtube.com/watch?v=tVIRDdf79-0&t=560)

这条约束解释了这个特性的形状：它做的是**把队列分给线程**（mapping），而不是**让线程共享队列**（sharing）。想并行，就得先有多条队列——这也是为什么它天然依赖客户机侧的多队列。

### 3.4 别和 `io='threads'` 搞混

libvirt 里还有另一个叫 `io='threads'` 的东西，两者完全不同[【跳转到 10:10】](https://www.youtube.com/watch?v=tVIRDdf79-0&t=610)：

| 名字 | 它是什么 | 干什么 |
| --- | --- | --- |
| IOThread（本节的特性） | QEMU 里的**设备模拟线程** | 解析 virtqueue、跑块层、发起系统调用、注入中断 |
| `io='threads'` | 用户态**线程池**，一种异步 I/O 引擎 | 替代 Linux AIO / io_uring 去执行 I/O 请求 |

两者不但不是一回事，而且**配合不好**：用 `io='threads'` 时，IOThread 做完设备模拟后还要把请求丢给另一个线程池线程，多一次交接。在 Linux 上演讲者直接建议用 `cache='none'` 加 `io='native'`（即 Linux AIO）。

![IOTHreads 与 io="threads" 是两件事：前者做设备模拟，后者是用户态线程池；IOThread Virtqueue Mapping 不是为配合 io="threads" 设计的](assets/virtio-blk%20的队列模型与%20IOThread%20映射/00635.webp)
## 四、参数怎么选：线程数、共享与绑核

### 4.1 IOThread 太少压不满盘，太多抢应用的 CPU

线程数不是越多越好，两头都有代价[【跳转到 12:15】](https://www.youtube.com/watch?v=tVIRDdf79-0&t=735)：

- **太少**：退回到"一个线程压一块盘"的老局面，拿不到磁盘能给的 IOPS。
- **太多**：那些 CPU 本来可以留给虚拟机里的应用，现在被设备模拟吃掉，还可能在宿主上互相争抢。

演讲者在本地 NVMe 上的测试结果是 **4~8 个**比较合适；具体数字取决于存储类型（本地闪存、网络存储、盘的快慢都不一样），所以最终还是要自己在目标机器上测。

![选择 IOThread 数量：太少压不满盘，太多则没有 CPU 留给应用；本地 NVMe 上的经验值是 4~8 个](assets/virtio-blk%20的队列模型与%20IOThread%20映射/00735.webp)

### 4.2 多个设备可以共享同一组 IOThread

IOThread 不必一个设备独占。典型场景是一台虚拟机既有系统盘（启动盘）又有数据盘，绝大部分 I/O 都落在数据盘上，启动盘利用率很低——那就没必要给启动盘配专属线程，让它和数据盘共享即可，几乎不影响性能。[【跳转到 13:05】](https://www.youtube.com/watch?v=tVIRDdf79-0&t=785)

原则只有一条：**如果你了解自己的负载，就别让某一个 IOThread 被压爆**。

### 4.3 绑核能减少噪声，但要挑对 NUMA 节点

默认情况下，宿主 Linux 调度器会把 IOThread 放到它认为合适的地方。用 `<iothreadpin>` 把它们钉在指定 CPU 上，等于告诉调度器"这些核只跑这些线程"，别的负载不会挤进来。幻灯片给出的结论是：绑核**减少噪声**，并且性能更早到达满值。[【跳转到 13:55】](https://www.youtube.com/watch?v=tVIRDdf79-0&t=835)

![绑核前后对比：横轴是 iodepth，纵轴是 IOPS；`pin-*` 系列比 `nopin-*` 更早接近满值，幻灯片总结为"绑核降低噪声"](assets/virtio-blk%20的队列模型与%20IOThread%20映射/00835.webp)

绑哪里也有讲究：**绑在与客户机内存、存储控制器 PCI 适配器同一个 NUMA 节点上的宿主 CPU**。因为某些 PCI 插槽属于特定 NUMA 节点，跨节点访问内存和设备的代价会吃掉绑核的收益。

还有一条容易被忽略的限制：**热迁移场景下绑核需要管理/编排工具支持**。你把 IOThread 钉在 8 号 CPU 上，迁移到目的宿主后，8 号 CPU 上可能已经跑着别的东西，钉了也等于没钉。没有这种工具支持时，演讲者的建议是干脆别绑——性能没那么稳，但至少不会错。

## 五、收益边界：它是"分配资源"，不是"降低开销"

### 5.1 微基准：4K 随机读翻倍

标准测试用 fio 打：4K 随机读、`--direct=1`、8 个 job、`cache=none io=native`，目标是一块 Intel Optane P4800X，直接打裸设备（没有文件系统）。结果是 **4 个 IOThread 把 IOPS 翻了一倍**，把盘压到了上限。[【跳转到 16:25】](https://www.youtube.com/watch?v=tVIRDdf79-0&t=985)

![fio 4K 随机读：1 / 2 / 4 个 IOThread 的 IOPS 对比，4 个线程时性能翻倍](assets/virtio-blk%20的队列模型与%20IOThread%20映射/00985.webp)

### 5.2 大块 I/O 收益很小

如果应用发的是 64KB 甚至更大的请求，情况就变了：**大块 I/O 用很少的请求数就能把盘压满**，QEMU 里花的 CPU 周期本来就少，此时瓶颈在盘而不在线程数——一个 IOThread 可能就够了。所以这个特性只对小块、混合块大小的负载有意义。[【跳转到 17:15】](https://www.youtube.com/watch?v=tVIRDdf79-0&t=1035)

![大块 I/O 受益更少：64KB 以上的块大小，一个 IOThread 往往就能压满盘](assets/virtio-blk%20的队列模型与%20IOThread%20映射/01035.webp)

### 5.3 真实数据库：提升 10%~23%，但会随负载下降

微基准好看不等于生产环境好看。Red Hat 性能团队的 Sanjay Rao 在 Oracle 和 MS SQL Server 上跑 HammerDB，用一台 192 vCPU、800G 内存的大虚拟机（4 个 IOThread、96 条队列的数据卷）[【跳转到 18:05】](https://www.youtube.com/watch?v=tVIRDdf79-0&t=1085)：

| 并发用户数 | 无 IOThread（事务/分） | 4 个 IOThread（事务/分） | 差异 |
| --- | --- | --- | --- |
| 10 | 502275 | 660906 | +22.86% |
| 20 | 874371 | 1137540 | +22.37% |
| 40 | 1453838 | 1759600 | +17.53% |
| 80 | 2313728 | 2550453 | +12.33% |

![HammerDB 在 Oracle 上的结果：低并发时提升 22%，用户数上去以后回落到 12% 左右](assets/virtio-blk%20的队列模型与%20IOThread%20映射/01085.webp)

规律很清楚：**一开始提升明显，负载越重提升越小**。因为用户数上去以后，宿主 CPU 和存储系统本身已经接近饱和，没有余量可以"多分配"了。

### 5.4 宿主挤满虚拟机时，收益归零

更极端的一步：在同一台宿主上跑 8 个同样的 Oracle 虚拟机，把机器塞满。此时加不加 IOThread 几乎没有区别，差异落在 -1.16% 到 +3.08% 之间，也就是噪声。[【跳转到 18:55】](https://www.youtube.com/watch?v=tVIRDdf79-0&t=1135)

![8 个虚拟机挤满宿主后，有无 IOThread 的差异在 ±3% 以内，属于噪声](assets/virtio-blk%20的队列模型与%20IOThread%20映射/01135.webp)

这就是演讲者反复强调的那句话的含义：**IOThread Virtqueue Mapping 不是一项优化，而是让你能给虚拟机分配更多资源的功能**。宿主有富余的 CPU 和磁盘带宽，它才有效；资源本来就紧张，它不会凭空变快。

## 六、未来方向与边界

演讲最后列了三条后续工作[【跳转到 19:45】](https://www.youtube.com/watch?v=tVIRDdf79-0&t=1185)：

1. **virtio-scsi 也支持**。目前只做了 virtio-blk，因为 SCSI 层还是单线程的，所有 I/O 处理必须在一个线程里完成，要先把那层重构成多线程。
2. **其他 virtio 设备复用这套基础设施**。`iothread-vq-mapping` 的语法和线程建立代码可以给别的多队列 virtio 设备用。
3. **继续优化 QEMU 的 I/O 代码路径**，降低每单位 I/O 的 CPU 开销——这才是真正的"优化"，和"分配资源"是两件事。

![未来方向：virtio-scsi 支持、其他 virtio 设备复用 iothread-vq-mapping 基础设施、继续优化 QEMU I/O 代码路径](assets/virtio-blk%20的队列模型与%20IOThread%20映射/01185.webp)

问答环节还澄清了两个边界：

- **网络设备用不上它**。网卡现在基本都走 vhost-net 或 vhost-user，数据面绕过了 QEMU 的设备模拟，而这套东西恰恰实现在 QEMU 的设备模拟里。[【跳转到 26:06】](https://www.youtube.com/watch?v=tVIRDdf79-0&t=1566)
- **`qemu-storage-daemon` 是更彻底的形态**。把块层放到独立进程里，所有虚拟机的磁盘 I/O 由一个守护进程统一处理，IOThread 就能跨虚拟机共享、统一绑核；但它的导出（比如 `vhost-user-blk`）目前只接受一个 IOThread 参数，还不支持 virtqueue 映射。[【跳转到 21:50】](https://www.youtube.com/watch?v=tVIRDdf79-0&t=1310)

## 小结

- virtio-blk 的队列模型是**每 vCPU 一条 virtqueue**：提交无锁竞争，完成中断回到提交者。QEMU 默认就按 vCPU 数建队列。
- 但 QEMU 里**一个 virtio-blk 设备的所有 virtqueue 由同一个线程模拟**，多 vCPU 并发 I/O 时这就是漏斗，虚拟化开销可达 20%~30%。
- QEMU 9.0 先把块层改成多线程，才让 IOThread Virtqueue Mapping 成为可能：把不同 virtqueue 绑到不同宿主 IOThread。
- 因为 vring 是**单消费者**结构，一条 virtqueue 只能归一个线程，所以是"映射"而非"共享"，线程里因此不需要加锁。
- 配置上 libvirt 用 `<iothreads>` 轮转分配，QEMU 用 JSON 的 `iothread-vq-mapping` 精确指定；别和 `io='threads'`（用户态线程池）混为一谈。
- 线程数本地 NVMe 建议 4~8；多设备可共享 IOThread；绑核要绑在与客户机内存、存储控制器同 NUMA 节点的 CPU 上，热迁移场景需要编排工具支持。
- 收益有边界：4K 随机读能翻倍，64KB 以上的大块 I/O 收益很小，真实数据库提升 10%~23% 且随负载下降，宿主挤满虚拟机后收益归零。
- 它的定位是**把富余资源分配给虚拟机**，不是降低虚拟化开销；virtio-scsi 的同类支持还在路上（要先解决 SCSI 层单线程的问题）。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| virtqueue | virtio 的请求队列，客户机与宿主共享的一段环形缓冲区，一条队列对应一个方向的数据面 |
| 多队列（multi-queue） | 一个设备拥有多条 virtqueue，通常每 vCPU 一条，避免客户机侧提交时的跨核竞争 |
| vring | virtqueue 在共享内存里的三段式结构（描述符表、可用环、已用环），是**单消费者**结构 |
| IOThread | QEMU 里负责设备模拟的线程，解析 virtqueue、跑块层、发起系统调用、注入完成中断 |
| IOThread Virtqueue Mapping | QEMU 9.0 的特性，把不同的 virtqueue 分配给不同的 IOThread，让宿主侧也真正并行 |
| `iothread-vq-mapping` | QEMU 的 JSON 命令行参数，按 virtqueue 编号精确指定它归哪个 IOThread |
| `<iothreads>` / `<iothreadpin>` | libvirt 里给磁盘列出 IOThread（轮转分配）、以及把 IOThread 绑定到宿主 CPU 的标签 |
| `io='threads'` | libvirt 的用户态异步 I/O 线程池，和 IOThread 是两套东西，且与 virtqueue 映射配合不好 |
| `cache='none'` + `io='native'` | 绕过宿主页缓存、使用 Linux AIO 的组合，是这套特性推荐搭配的磁盘配置 |
| 单消费者（single consumer） | vring 的一条队列只能由一个线程取用，因此无需加锁，也限制了并行方式 |
