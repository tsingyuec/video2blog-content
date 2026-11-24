# virtio 设备状态怎么存：vDPA 迁移与 Shadow Virtqueue 的队列交接

> 视频来源：[vDPA-net live migration with Shadow Virtqueue](https://www.youtube.com/watch?v=x9ARoNVzS04)（YouTube · KVM Forum · Eugenio Pérez（Red Hat）、Gautam（AMD/Xilinx））｜时长约 25 分钟
> 导读：这场 talk 表面上在讲"怎么让直通网卡也能热迁移"，实际上把 virtio 设备的"状态"拆得最清楚：哪些字段属于设备状态、它们平时藏在谁手里、迁移时怎么被读出来再写回去。本文按"状态在哪 → 为什么看不见 → 怎么让它可见 → 索引怎么存 → 恢复怎么放回去"的顺序整理。

## 本讲要解决的核心问题（SCQA）

**背景**：virtio 设备的状态分两层。数据面是 vring——一块客户机和设备共享的环形缓冲区，双方各自推进自己的索引；控制面是 feature 协商、配置空间、以及一条专门用来传控制命令的 virtqueue（CVQ）。

**冲突**：当设备以 vDPA（或 SR-IOV 直通）方式工作时，数据面和控制面都绕过 QEMU，直接落在内核框架和硬件里。QEMU 手里只剩一个"设备模型"的壳，它**看不到 vring 的读写位置，也看不到客户机刚刚下发的配置命令**。而迁移要求"设备处理到哪了"必须精确交接到目的端。

**疑问**：QEMU 看不见队列，那队列状态（索引、配置）到底怎么被读出来、写进迁移流、再装回目的端？

**回答（中心思想）**：让 QEMU 重新"站在中间"——用一条**影子 virtqueue（Shadow Virtqueue，SVQ）**把控制队列截下来，于是设备状态重新变成 QEMU 能读能写的普通字段，可以复用模拟设备那套现成的状态传输代码；数据面则通过影子 vring 转发 descriptor，顺带把设备写过的内存页记进 dirty bitmap，保证内存和队列索引一起迁走。

## 一、先把 virtio 设备的"状态"拆开

### 1.1 vring 是数据面，不是全部

virtio 规范定义了虚拟设备、虚拟驱动以及两者如何交互，也定义了客户机与宿主之间控制面和数据面怎么建立。数据面由"缓冲区 + 环形布局"组成，负责搬运真正的数据（报文）；而要让数据面能建立起来，需要控制面先做几件事：feature 协商、virtqueue 的配置等等 [【跳转到 03:53】](https://www.youtube.com/watch?v=x9ARoNVzS04&t=233)。

![virtio 的数据面：vring 是一个环，读位置与写位置各自推进](assets/virtio%20设备状态怎么存：vDPA%20迁移与%20Shadow%20Virtqueue%20的队列交接/00258.webp)

讲者特意提醒：为了好理解，幻灯片把 virtqueue 画成一个"环形缓冲区"，但真实的数据结构字段远不止这些 [【跳转到 04:18】](https://www.youtube.com/watch?v=x9ARoNVzS04&t=258)。这句话是后面所有麻烦的根源——**索引、地址、标志位都是独立字段，迁移时一个都不能丢**。

### 1.2 一块 virtio-net 卡到底有哪些"设备状态"

讲者在解释"为什么要让 QEMU 看见控制队列"时，给了一句很关键的定义：设备状态由 **virtio status、MAC 地址、virtio VLAN 配置**等组成，QEMU 必须能跟踪这个设备，才能把它发到目的端 [【跳转到 12:43】](https://www.youtube.com/watch?v=x9ARoNVzS04&t=763)。

![CVQ 绕过 QEMU 时，设备状态（mac、#vqps）只存在于设备和内核驱动里](assets/virtio%20设备状态怎么存：vDPA%20迁移与%20Shadow%20Virtqueue%20的队列交接/00763.webp)

幻灯片右侧那张小表就是一份浓缩的"设备状态清单"：`mac = 00:11:22:33:44:55`、`#vqps = 3`（队列对数）。这类字段的共同点是——**它们不是硬件天生的，而是客户机通过控制队列配出来的**。也正因为如此，它们没法"从硬件读回来"，只能被谁看见、由谁记录。

## 二、问题：vDPA 把控制面搬进内核，QEMU 就"看不见"了

### 2.1 vDPA 的设计取舍

vDPA（vritio Data Path Acceleration）的目标是两头都要：数据面像 SR-IOV 直通一样绕过宿主内核，性能拉满；控制面则交给内核里的 vDPA 框架加厂商专用驱动来处理。于是原本在客户机里的"厂商专用驱动"被搬到了 hypervisor 里 [【跳转到 05:13】](https://www.youtube.com/watch?v=x9ARoNVzS04&t=313)。

![vDPA 架构：数据面直通，控制面经 vDPA 框架与厂商驱动](assets/virtio%20设备状态怎么存：vDPA%20迁移与%20Shadow%20Virtqueue%20的队列交接/00313.webp)

这个结构解决了 SR-IOV 直通的老问题：过去客户机里装的是**厂商专用驱动**，从 A 厂商的网卡迁到 B 厂商的网卡，客户机里没有 B 的驱动，数据面就起不来；换成 vDPA 后，客户机里只有通用的 virtio-net 驱动，厂商差异被关在 hypervisor 里 [【跳转到 07:10】](https://www.youtube.com/watch?v=x9ARoNVzS04&t=430)。

### 2.2 代价：QEMU 拿不到设备状态

但代价随之而来。控制队列（CVQ）的命令由客户机直接发到内核里的 vDPA 驱动，**绕过了 QEMU**。讲者给了一个很具体的故障场景：

1. 客户机执行 `ifconfig eth0 hw ether <新 MAC>`；
2. 命令被厂商专用 vDPA 驱动翻译成硬件命令（例如 Xilinx SN1000 的 `MC command set MAC`），设备上的 MAC 改了；
3. **QEMU 完全不知道这件事**；
4. 迁移时 QEMU 按自己记忆里的旧配置往目的端发；
5. 客户机恢复后突然发现自己的 MAC 变回去了。

[【跳转到 06:12】](https://www.youtube.com/watch?v=x9ARoNVzS04&t=372) [【跳转到 13:08】](https://www.youtube.com/watch?v=x9ARoNVzS04&t=788)

这就是"设备状态必须由 VMM 掌握"的最直白理由：**谁负责序列化，谁就必须先看得见**。

## 三、解法：影子队列让 QEMU 重新站在中间

### 3.1 影子 CVQ：客户机跟 QEMU 谈，QEMU 跟设备谈

解法是加一层交互：从此客户机不再直接跟设备谈控制命令，而是跟 QEMU 谈；QEMU 记录下这些变化，再通过一条**影子 virtqueue** 转给设备。注意范围——这只针对控制队列，数据面依旧直通，性能不受影响 [【跳转到 13:33】](https://www.youtube.com/watch?v=x9ARoNVzS04&t=813)。

![影子 CVQ：客户机与 QEMU 各有一条 vring，QEMU 负责把控制命令转给设备](assets/virtio%20设备状态怎么存：vDPA%20迁移与%20Shadow%20Virtqueue%20的队列交接/00813.webp)

于是又出现了那次 MAC 修改，但这次路径变成：客户机 → QEMU（QEMU 记下新 MAC）→ 设备读 QEMU 的 vring（**这是影子队列，不是客户机那条**）→ 设备确认 → 配置一致地更新 [【跳转到 13:58】](https://www.youtube.com/watch?v=x9ARoNVzS04&t=838)。

### 3.2 状态传输本身不用写新代码

一旦 QEMU 能看见这些字段，**"把状态发到目的端"这件事就免费了**：所有模拟设备本来就要传输这些状态，那套代码完全可复用 [【跳转到 14:22】](https://www.youtube.com/watch?v=x9ARoNVzS04&t=862)。这正是本节最值得记住的一句——**virtio 设备状态的序列化并不是为直通设备新写的格式，而是复用模拟设备的 VMState 路径**；直通设备只是需要先把状态"变回"QEMU 能看见的形态。

### 3.3 恢复端：只开控制队列，不开数据面

到了目的端怎么把这些状态写回设备？讲者的做法很巧：目的设备本来就懂怎么处理这些控制命令，所以**只使能控制 virtqueue、先不使能数据面**，然后把控制命令重放一遍。这样设备不会往无效队列里写数据，也不会把有效报文过滤掉；等所有配置都更新完，再打开数据面，客户机继续跑 [【跳转到 14:47】](https://www.youtube.com/watch?v=x9ARoNVzS04&t=887)。

整个过程对设备透明、对客户机透明——设备不知道自己面对的是 QEMU 的影子队列，客户机也不知道自己的配置命令被"过了一遍手"。

## 四、队列索引怎么被存下来

### 4.1 五步：分配、暂停、读索引、复位、换地址

这是全场最接近"virtio 队列状态如何被序列化"的一段。要让设备从"直接读客户机的 vring"切换到"读影子 vring"，顺序是固定的：

1. 先**分配**影子 virtqueue；
2. **暂停设备**，并把设备状态（例如各个索引）**保存下来**——这样才知道怎么把影子队列"呈现"给客户机；
3. **完全复位设备**；
4. 在影子内存里**配置新的 ring 地址**（客户机对这些新 vring 没有任何访问权限）；
5. 设备照常运行，它并不知道自己写的是影子 vring 还是客户机 vring。

[【跳转到 16:27】](https://www.youtube.com/watch?v=x9ARoNVzS04&t=987)

![影子队列的常规工作方式：设备写影子 vring，QEMU 负责转发](assets/virtio%20设备状态怎么存：vDPA%20迁移与%20Shadow%20Virtqueue%20的队列交接/00987.webp)

第 2 步是本节的核心动作：**索引必须在设备停下来之后读**。索引是"设备处理到第几个 descriptor"的游标，设备在跑的时候它会一直变；只有在暂停之后读到的值，才和"设备当前不再消耗缓冲区"这个事实一致。这和上一节"先停 vCPU 再抄设备状态"是同一条原则的两个侧面。

### 4.2 descriptor 转发与 dirty bitmap

设备写影子 vring 之后，QEMU 负责把 **descriptor** 转发到客户机的 vring 里——注意它**不复制缓冲区内容**，数据本身是直接写进客户机内存的，QEMU 只搬 descriptor，所以讲者说这是"某种意义上的串行拷贝" [【跳转到 17:17】](https://www.youtube.com/watch?v=x9ARoNVzS04&t=1037)。

这个"顺手转发"带来一个额外好处：QEMU 既然在处理 descriptor，就能顺便知道自己碰过哪些内存，于是把 **dirty bitmap** 填上。

![影子队列填 dirty bitmap：QEMU 转发 descriptor 时记下被设备写过的页](assets/virtio%20设备状态怎么存：vDPA%20迁移与%20Shadow%20Virtqueue%20的队列交接/01037.webp)

为什么要这个？因为设备是直通的，它往客户机内存里写数据这件事 QEMU 看不见。如果不记录，迁移时那些页就不会被重发，目的端的客户机会看到不一致的内存视图 [【跳转到 15:37】](https://www.youtube.com/watch?v=x9ARoNVzS04&t=937)。而且这部分代码是"白捡的"——它本来就存在于模拟设备的实现里，实现影子队列之前就有，两边共用同一套优化 [【跳转到 16:02】](https://www.youtube.com/watch?v=x9ARoNVzS04&t=962)。

### 4.3 三件事可以分开取舍

讲者在 recap 时把整件事归纳成三个可独立开关的能力：**跟踪设备状态、跟踪 dirty memory、在目的端重启设备状态**。设备侧不需要任何改动；将来厂商可以只对其中某一项做硬件实现（例如自己上报 dirty memory，性能更好），另外两项继续复用软件路径 [【跳转到 17:42】](https://www.youtube.com/watch?v=x9ARoNVzS04&t=1062) [【跳转到 18:07】](https://www.youtube.com/watch?v=x9ARoNVzS04&t=1087)。

QEMU 侧的改动也很小：对每个新的 virtio feature，要做的只是把命令经 QEMU 转一次到控制 virtqueue，模式都一样。

## 五、现场：跨厂商迁移跑起来是什么样

演示环境是两台 Dell 750：源端是 AMD/Xilinx SN1000（vDPA 设备出现在 port 3），目的端是 Mellanox ConnectX-6（vDPA 设备出现在 port 17），两边用同一个 VLAN ID 接到交换机上，客户机里跑 iperf [【跳转到 08:00】](https://www.youtube.com/watch?v=x9ARoNVzS04&t=480)。

![跨厂商迁移：客户机只看到 virtio-net，厂商差异关在 hypervisor 里](assets/virtio%20设备状态怎么存：vDPA%20迁移与%20Shadow%20Virtqueue%20的队列交接/00480.webp)

启动命令里有一个细节值得初学者注意：源端 QEMU 的命令行很长，因为要**把源端和设备的特性取交集**，连 `VQ size` 都设成两边的最小值 256 [【跳转到 10:30】](https://www.youtube.com/watch?v=x9ARoNVzS04&t=630)。这提醒我们：迁移能不能成，前提是**两端对"这台设备长什么样"有完全一致的认识**——feature 协商结果、队列大小、队列数量都属于这份"设备契约"。

目的端 QEMU 的命令行与源端完全相同，只多一个 `incoming` 参数，告诉它不要启动虚拟机、等着另一台 QEMU 把虚拟机送过来 [【跳转到 11:14】](https://www.youtube.com/watch?v=x9ARoNVzS04&t=674)。迁移过程中实测到 **45 Gbps** 的流量，讲者强调这个数字没做任何优化（没有 CPU 绑定，用的还是效率不高的 split virtqueue），只是为了证明"能迁、迁完还能跑" [【跳转到 11:39】](https://www.youtube.com/watch?v=x9ARoNVzS04&t=699)。

发迁移命令之后，设备被挂起，QEMU 切换到一种能跟踪"设备正在写哪些内存"的模式，于是源端知道哪些页因为设备写入而变脏、需要重发；过一会儿目的端客户机就看到一致的内存视图，迁移完成、性能恢复 [【跳转到 12:04】](https://www.youtube.com/watch?v=x9ARoNVzS04&t=724)。

## 六、边界与遗留问题

- **队列实现在设备里，不在驱动里**。提问环节有人问"hypervisor 里的厂商 vDPA 驱动是否也用 virtqueue"，回答是：virtqueue 由设备实现，厂商驱动只实现一组 config 操作（见 `vdpa.h`），例如 `set vring address`——对 split virtqueue 要传三个地址，配到设备上，设备才能直接往客户机内存里写 [【跳转到 23:00】](https://www.youtube.com/watch?v=x9ARoNVzS04&t=1380)。这也解释了为什么"队列状态"最终要落到设备寄存器/硬件状态里。
- **硬件自迁移还没有数据**。有人问"有没有设备不需要影子队列、自己能迁移"，回答是目前没有性能数字，而且这条路要求厂商实现多得多的东西；vDPA 框架的定位就是让厂商只实现数据面那一小块 [【跳转到 23:50】](https://www.youtube.com/watch?v=x9ARoNVzS04&t=1430)。
- **机密计算场景存疑**。有人问安全 I/O（内存加密）下这套方案是否可行，讲者认为设备通过 IOMMU 访问内存这一环与机密内存的信任模型还没对上，需要另找扩展 [【跳转到 21:31】](https://www.youtube.com/watch?v=x9ARoNVzS04&t=1291)。
- **影子队列本身有成本**：descriptor 要串行转发，数据面在迁移窗口内会退化；这也是为什么讲者反复强调"只对控制队列做影子，数据面保持直通"。

## 小结

- virtio 设备的状态 = **控制面字段（virtio status、MAC、VLAN、队列对数）+ 队列索引 + 队列地址**，它们不是硬件原生的，而是客户机配出来的，所以必须由 VMM 记录。
- 直通/vDPA 让控制面绕过 QEMU，QEMU 就失去了记录能力——这是"设备状态无法序列化"的真正原因，而不是格式问题。
- **影子 virtqueue** 把控制队列重新拉回 QEMU 视野，于是设备状态变回普通字段，可以直接复用模拟设备的 VMState 传输路径。
- 队列索引的保存顺序是：**分配影子队列 → 暂停设备 → 读索引 → 复位设备 → 配置新 ring 地址**；索引必须在设备停下后读。
- 转发 descriptor 时顺手填 dirty bitmap，解决"设备直通写内存、QEMU 看不见"的问题，保证内存与队列状态一起迁移。
- 恢复端先只开控制队列、重放配置命令，再打开数据面——**先设备、后数据**。
- 迁移的前提是两端对设备契约（feature 交集、VQ size、队列数）达成一致。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| vring / virtqueue | 客户机与设备共享的环形队列，读位置和写位置各自推进 |
| CVQ（control virtqueue） | virtio-net 里专门传控制命令（改 MAC、VLAN、队列数）的那条队列 |
| vDPA | virtio 数据面加速：数据面直通硬件，控制面由内核 vDPA 框架加厂商驱动处理 |
| SR-IOV VF 直通 | 把物理设备的虚拟功能直接给虚拟机，客户机需要厂商专用驱动 |
| Shadow Virtqueue（SVQ） | QEMU 在中间放一条影子队列，替代客户机队列与设备交互，从而看见并记录状态 |
| descriptor | vring 里描述"一块缓冲区在哪、多长"的条目；SVQ 只转发 descriptor，不复制数据 |
| dirty bitmap | 记录哪些内存页被写过，迁移时只重发这些页 |
| feature 协商 | 客户机与设备在初始化时确定共同支持的 virtio 特性集合，迁移两端必须一致 |
| `set vring address` | vDPA 驱动把队列地址配置到设备上的操作；split virtqueue 需要三个地址 |