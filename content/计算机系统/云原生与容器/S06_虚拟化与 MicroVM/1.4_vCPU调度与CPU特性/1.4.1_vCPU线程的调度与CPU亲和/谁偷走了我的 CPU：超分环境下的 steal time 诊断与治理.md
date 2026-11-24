# 谁偷走了我的 CPU：超分环境下的 steal time 诊断与治理

> 视频来源：[Who stole my CPU? Steal time mitigation at DigitalOcean](https://www.youtube.com/watch?v=FruPyQ0DRWc)（YouTube · Linux Plumbers Conference 2018 · DigitalOcean 系统工程团队）｜时长约 30 分钟
> 导读：这是一份来自公有云一线的实战复盘。DigitalOcean 的团队发现：宿主明明还有空闲资源，客户机却在 `top` 里顶着 20% 的 `st`（steal time）。他们顺着这条线索查下去，挖出了三层原因——NUMA balancing、per-VM cgroup 的份额分配、以及 autogroup，最后用一个用户态守护进程 Octopus 统一治理。本文按他们的排查顺序展开，正好把「vCPU 被 CFS 调度」这件事的后果讲透。文中命令与数字均来自讲者口述与幻灯片。

## 本讲要解决的核心问题（SCQA）

**背景**：vCPU 在宿主上就是一个普通 OS 任务，由 Linux 的 CFS 调度。客户机里的 `top` 会有一列 `st`，表示「我想跑但没轮到我」的时间。

**冲突**：按直觉，`st` 高应该意味着宿主 CPU 不够用。但 DigitalOcean 在一部分机器上看到的现象相反：**宿主整体只有 81% 的利用率，却有一批客户机顶着 20%~30% 的 steal**。更奇怪的是，**越大的 VM 被偷得越多，小 VM 反而把大 VM 饿着**。

**疑问**：在资源并不紧张的宿主上，steal 是从哪来的？它是怎么被算出来的？该由谁来负责消除？

**回答（中心思想）**：这类 steal 不是「核不够」，而是**调度器的分组策略与 NUMA 自动均衡在消耗 vCPU 的时间**。治理路径有三层：先关掉 NUMA balancing 并把 VM 绑到 NUMA 节点，再把 cgroup 的份额模型从「per-VM 平分」改成「per-host 共享」，最后用一个用户态守护进程（Octopus）承担绑核、NUMA 分区与跨 socket 迁移。核心结论是：**steal 是客户机唯一能观测到宿主争抢的窗口，但它只告诉你「被抢了」，不告诉你「谁抢的」——后者必须在宿主侧查。**

## 一、steal time 是什么：客户机唯一能看见的争抢

### 1.1 定义与三个性质

打开 `top`，CPU 时间被分成几类：`us`（用户态）、`sy`（内核态）、`wa`（iowait）……其中一类就是 **steal time**：**你的 vCPU 等着被分配到一颗物理 CPU 上运行所花的时间**，本质上是它**在运行队列里排队**的时间。[【跳转到 01:45】](https://www.youtube.com/watch?v=FruPyQ0DRWc&t=105)

讲者给了它四条性质，每一条都值得记住 [【跳转到 03:00】](https://www.youtube.com/watch?v=FruPyQ0DRWc&t=180)：

- **vCPU 只是宿主的另一个任务**，所以它完全可能丢掉 CPU；
- **从客户机的角度看，时间就停住了**——墙上时钟在走，vCPU 一条指令也没执行；
- **steal 只存在于虚拟机内部**：在物理机上看，steal 永远是 0；
- **它是由 hypervisor 上报的**。

最后一条最关键：客户机**没有能力自己做这笔账**。抢占发生在宿主侧，客户机连"谁抢了我"都看不见，只能被动接收 KVM 喂给它的计数器。

![steal 的四条性质：vCPU 只是宿主任务、客户机时间里时间停止、只存在于 VM 内、由 hypervisor 上报](assets/谁偷走了我的%20CPU：超分环境下的%20steal%20time%20诊断与治理/00180.webp)

### 1.2 两个视角：VM 视角看「有没有受伤」，宿主视角看「能不能救」

同一个指标，要从两个方向读 [【跳转到 05:30】](https://www.youtube.com/watch?v=FruPyQ0DRWc&t=330)：

| 视角 | 看什么 | 回答什么问题 |
| --- | --- | --- |
| 单台 VM | 这台机器自己的 steal | 它有没有真的受损 |
| 宿主 / 机群 | steal 在各 VM 间的分布、均值、离群点 | 该用哪种治理手段 |

![steal 分析的两种视角：VM 内视角判断是否受损，hypervisor 视角判断该采取什么治理手段](assets/谁偷走了我的%20CPU：超分环境下的%20steal%20time%20诊断与治理/00330.webp)

讲者还强调了一句容易忽略的话：**hypervisor 自己从不经历 steal**。我们说的「宿主的 steal」其实是「这台宿主上所有 VM 的 steal 之和」，是一个聚合量。

### 1.3 判断「是否真的受损」：utilization + steal 是否接近 100

这是本讲最实用的一个判据 [【跳转到 05:55】](https://www.youtube.com/watch?v=FruPyQ0DRWc&t=355)：

- 对单台 VM，看 **利用率与 steal 之和**。如果这个和接近 100%，说明这台机器**确实**有性能问题——如果没有 steal，那部分时间本来会被它用掉。
- 如果这台机器本来就比较闲，那 steal 大概率不构成问题。

换句话说，`st` 高不等于「慢」；`st` 高且 `us + st ≈ 100` 才是「慢」。

### 1.4 宿主视角：有没有空闲资源，决定「能不能救」

从宿主看，问题被简化成一个二分判断 [【跳转到 06:20】](https://www.youtube.com/watch?v=FruPyQ0DRWc&t=380)：

- **没有空闲资源**：什么也做不了，唯一办法是把一些 VM 迁到别的宿主，降低超分比；
- **有空闲资源却仍有 steal**：这是**宿主配置问题**，可以修。

本讲后面全部内容，都是在处理第二种情况。

## 二、现象：宿主只用了 81%，客户机却在丢 30% 的 CPU

讲者给了一个合成实验：一台宿主上跑十台 VM，全部执行 `top`。[【跳转到 07:10】](https://www.youtube.com/watch?v=FruPyQ0DRWc&t=430)

结果有三个特征：

1. **宿主整体利用率只有 81%**——没有超分；
2. **多台 VM 的 steal 高达 20%~30%**；
3. **越大的 VM steal 越高，小 VM 反而把大 VM 饿死**。

![合成实验的 top 输出：宿主整体仅 81% 利用率，但多台 VM 的 steal 达到 20% 到 30%](assets/谁偷走了我的%20CPU：超分环境下的%20steal%20time%20诊断与治理/00430.webp)

第 3 条是破案的关键线索：如果只是「核不够」，大 VM 和小 VM 应该按比例一起挨饿；出现「小的饿死大的」，说明问题出在**分组与份额分配**上，而不是总算力。

## 三、第一层原因：NUMA balancing 把 vCPU 的时间花在搬家上

排查的第一步，团队发现**迁移线程在飙高**——系统里一直在做某种迁移。[【跳转到 08:24】](https://www.youtube.com/watch?v=FruPyQ0DRWc&t=504)

原因是两个默认行为的叠加：

- **默认情况下，一台 VM 会横跨宿主上所有的 NUMA 节点**；
- Linux 有一个 **automatic NUMA balancing**（自动 NUMA 均衡）特性，试图让「任务」和「它的内存」靠得更近。

这个均衡有两种工作模式：

1. **memory follows CPU**：把内存迁到任务正在运行的节点；
2. **CPU follows memory**：把任务迁到持有它大部分内存的那个节点。

问题在于，**做这两件事要消耗系统 CPU 时间**——而这些时间本来可以给 VM 用，现在变成了 steal。[【跳转到 08:49】](https://www.youtube.com/watch?v=FruPyQ0DRWc&t=529)

### 3.1 第一版修复：绑 NUMA 节点 + 关掉 NUMA balancing

修复很直接 [【跳转到 09:14】](https://www.youtube.com/watch?v=FruPyQ0DRWc&t=554)：**把 VM 绑到指定的 NUMA 节点，把 hypervisor 里所有内存区域也绑到同一个节点，并关闭 NUMA balancing**。没有迁移了，理论上 steal 应该降下来。

![NUMA balancing 的治理：把 VM 与它的内存都钉在同一个 NUMA 节点上，并关闭自动均衡](assets/谁偷走了我的%20CPU：超分环境下的%20steal%20time%20诊断与治理/00554.webp)

效果确实有：大 VM 的 steal **从 20% 降到 4%**。但**还有 4%**。

## 四、第二层原因：per-VM cgroup 让大 VM 吃亏

剩下的 4% 引出了 **process grouping（进程分组）** 这个话题。[【跳转到 09:39】](https://www.youtube.com/watch?v=FruPyQ0DRWc&t=579)

Linux 会把相关进程分组来分配资源，其中一种机制就是 **cpu cgroup**。而 libvirt 的默认行为是：**每台 VM 一个 cpu cgroup，所有 cgroup 的 shares 平分**。

### 4.1 一个 8 核宿主上的算术题

讲者用一个小例子把问题算清楚了 [【跳转到 10:15】](https://www.youtube.com/watch?v=FruPyQ0DRWc&t=615)：

- 宿主 8 个 CPU，即 **800% 的 CPU 时间**；
- 三台 VM：一台大 VM 有 **4 个 vCPU**，两台小 VM 各有 **2 个 vCPU**；
- libvirt 建了 3 个 cgroup，shares 平分，**每台 VM 拿到 800/3 ≈ 266%**。

于是：

- 小 VM：266% 分给 2 个 vCPU，**每个 vCPU 拿到 100%**，理论上没有 steal；
- 大 VM：266% 分给 4 个 vCPU，**每个 vCPU 只有 66%**，剩下的 **34% 就是 steal**。

![per-VM cgroup 的份额分配：三台 VM 各得 266%，大 VM 的 4 个 vCPU 每个只有 66%，其余变成 steal](assets/谁偷走了我的%20CPU：超分环境下的%20steal%20time%20诊断与治理/00640.webp)

这就是「小 VM 饿死大 VM」的机制：**cgroup 的份额是按 VM 分的，不是按 vCPU 分的**。VM 越大，每个 vCPU 分到的份额越少。

### 4.2 两次失败的修复

**尝试一：按 VM 大小分配 shares。** 大 VM 给大 share，小 VM 给小 share。理论上应该对，但在他们的机群上**没有生效**——因为 **libvirt 默认会建出很深的 cgroup 层级，进程数一多就不 scale**，看不到预期效果。[【跳转到 11:30】](https://www.youtube.com/watch?v=FruPyQ0DRWc&t=690)

**尝试二：整体关掉 cgroup。** 关掉之后调度器把每个任务视为平等，份额自然均分，理论上也对。但有两个副作用 [【跳转到 12:20】](https://www.youtube.com/watch?v=FruPyQ0DRWc&t=740)：

1. **失去了控制单台 VM CPU 利用率的能力**。他们的控制面本来提供「限制某台 VM 的 CPU」这个功能，请求发给 libvirt，libvirt 用 cpu cgroup 来落实；关掉 cgroup 这条链路就断了。
2. **autogroup 趁虚而入**。autogroup 是另一个隐式特性，会按进程属性（启动用户、session ID 等）自动分组。关掉 cgroup 后 autogroup 接管，把一台 VM 的所有任务塞进同一个组——**又回到原点，大 VM 继续被惩罚**。

![关掉 cgroup 的两个副作用：失去单 VM CPU 限制能力，且 autogroup 接管后问题复现](assets/谁偷走了我的%20CPU：超分环境下的%20steal%20time%20诊断与治理/00790.webp)

**尝试三：再关掉 autogroup。** 还是不行——因为**关掉 autogroup 只影响新进程**，已经在跑的 VM 仍然留在原来的 autogroup 里。[【跳转到 13:10】](https://www.youtube.com/watch?v=FruPyQ0DRWc&t=790)

### 4.3 生效的方案：per-host cgroup

最终方案叫 **per-host cgroup** [【跳转到 13:10】](https://www.youtube.com/watch?v=FruPyQ0DRWc&t=790)：

- libvirt 默认建 per-VM cgroup，他们**改成在系统里只留一个 cgroup**，把这台宿主上所有 VM 的所有任务都放进去；
- 为此修改了 libvirt，让它创建 per-host cgroup 并把所有 VM 移进去。

回到刚才那道算术题：8 核宿主、800% CPU 时间、**一个 cgroup**，那么总份额被**所有 vCPU 平分**——每个 vCPU 拿 1/8，也就是 **100%**，理论上没有 steal。[【跳转到 14:25】](https://www.youtube.com/watch?v=FruPyQ0DRWc&t=865)

![per-host cgroup 的效果：同一个例子下，每个 vCPU 都能拿到 100%，大 VM 不再被惩罚](assets/谁偷走了我的%20CPU：超分环境下的%20steal%20time%20诊断与治理/00865.webp)

但这样一来，「单独控制某台 VM 的 CPU」的能力还是丢了。他们的补救办法很巧妙：**当控制面发来控制请求时，修改过的 libvirt 把被控 VM 透明地从大 cgroup 里移出来，放进一个小 cgroup 并设置参数；请求撤销时再透明地移回去**。[【跳转到 14:50】](https://www.youtube.com/watch?v=FruPyQ0DRWc&t=890)

同一份合成负载加上这些修复后，steal 显著下降，大 VM 的 steal 变得很小，各 VM 之间也基本拉平。

## 五、剩下的 steal：不是所有 steal 都值得治

修完之后 steal 仍不为零，但讲者解释了它的来源：这部分来自**跑在很忙的宿主上的两台空闲 VM**。[【跳转到 15:15】](https://www.youtube.com/watch?v=FruPyQ0DRWc&t=915)

按他们第 1.3 节的判据，这**不构成性能问题**——因为 CFS 本来就会在有其它工作可做时**降低空闲任务的优先级**。既然不影响性能，他们就在这里停止了追查。[【跳转到 15:40】](https://www.youtube.com/watch?v=FruPyQ0DRWc&t=940)

这条经验值得单独拎出来：**steal 的治理目标是「消除影响」，不是「把数字清零」**。空闲任务的 steal 是调度器正常工作的副产品。

## 六、落地：为什么把这件事放在用户态守护进程里做

### 6.1 逻辑上该在内核，实际上放在用户态

讲者说得很坦白：这套逻辑**理论上应该实现在 OS 任务调度器里**，但那样很难；而他们可以接受一个简单得多的方案。[【跳转到 16:05】](https://www.youtube.com/watch?v=FruPyQ0DRWc&t=965)

方案是一个跑在宿主上的**用户态守护进程 Octopus**，负责把虚拟资源映射到物理资源：管理 vCPU 线程与 QEMU 线程，把它们钉到具体的 CPU 和 NUMA 节点上。[【跳转到 16:55】](https://www.youtube.com/watch?v=FruPyQ0DRWc&t=1015)

为什么用户态够用？因为**他们不需要细粒度**：决策的时间尺度是「VM 创建/销毁」或「分钟级」，他们看的是工作负载而不是单个任务，所以用户态实现完全够。[【跳转到 17:20】](https://www.youtube.com/watch?v=FruPyQ0DRWc&t=1040)

![Octopus 的定位：用户态 VM 放置守护进程，负责绑核、NUMA 分区、利用率跟踪与 CPU 到 vCPU 的映射](assets/谁偷走了我的%20CPU：超分环境下的%20steal%20time%20诊断与治理/01090.webp)

### 6.2 Octopus 的三件事

1. **NUMA 分区**：把宿主上所有 VM 分成大致相等的两堆，每堆只落在一个 CPU socket 及其对应的 NUMA 节点上。
2. **跨 socket 迁移**：做了 NUMA 分区，就**失去了 Linux 调度器的负载均衡能力**——一个 socket 忙、另一个闲着。这时由 Octopus 在 socket 之间迁移 VM。[【跳转到 18:10】](https://www.youtube.com/watch?v=FruPyQ0DRWc&t=1090)
3. **CPU 优化型套餐**：承诺「100% 的 CPU 时间」，实现方式是**把 vCPU 一对一钉到 CPU 上**。[【跳转到 19:00】](https://www.youtube.com/watch?v=FruPyQ0DRWc&t=1140)

第 3 条正好印证了绑核与超分的互斥关系：一旦承诺独占，就不能再把这颗核卖第二次。

### 6.3 迁移时的两个坑

**坑一：目标节点可能被撑爆。** 迁移过程中，目标 NUMA 节点可能过载。他们的做法是：**迁移前打开 swap，迁移后 swapoff**，把溢出的内存排回物理内存。[【跳转到 19:25】](https://www.youtube.com/watch?v=FruPyQ0DRWc&t=1165)

这听起来像 hack，但他们利用了一个特性：**swapoff 不是一次性的**——如果从 node 0 迁到 node 1 而空间不够，swapoff 时溢出的内存可能又落回源节点 node 0；下一轮迭代会搬更多，**过程是收敛的**。[【跳转到 20:15】](https://www.youtube.com/watch?v=FruPyQ0DRWc&t=1215)

**坑二：迁移期间被 OOM kill。** 极端情况下，目标节点上有另一台 VM 在猛烈申请内存，swap 来不及，VM 会被 OOM 杀掉。更糟的是 **swapoff 本身效率不高**——最极端的情况下他们见过 swapoff 跑几个小时，而这段时间里新的迁移可能已经开始。[【跳转到 21:55】](https://www.youtube.com/watch?v=FruPyQ0DRWc&t=1315)

因此他们的方向是：**不再依赖 swap**，复活一个多年前提交的补丁（希望现在效率高得多），并让 **NUMA 迁移能够优雅失败**而不是 OOM——后者仍在开发中。

### 6.4 工具链：从 top 到 perf

Q&A 里有人问他们用什么工具定位。回答是：**从 `top` 开始，然后转到 `perf`**。[【跳转到 24:52】](https://www.youtube.com/watch?v=FruPyQ0DRWc&t=1492)

`perf` 的价值在于能看到**上下文切换、VM exit**，以及**一个 VM 线程变成 runnable 之后、真正开始运行之前，中间还发生了什么**。对 NUMA 部分他们没用什么调试技巧，因为现象本身（迁移线程飙高）已经足够明显。

关于「为什么 NUMA balancing 会这么折腾」的追问，讲者的解释是：宿主上的负载非常动态——中间件会起来、会批量拉起 VM、负载会尖峰，内存因此很不均衡，NUMA balancing 就一直在搬。[【跳转到 25:47】](https://www.youtube.com/watch?v=FruPyQ0DRWc&t=1547) 有人建议「把 NUMA balancing 调得不那么激进是不是就够了」，讲者的回答是：不够，因为**VM 的负载本身会漂移**——固定成两个 NUMA 节点后，某个节点的 CPU 利用率仍可能被打满而另一个闲着，所以还需要**持续监控节点是否过载并据此再平衡**。[【跳转到 27:32】](https://www.youtube.com/watch?v=FruPyQ0DRWc&t=1652)

## 小结

把这条排查链压成一张图：

1. **steal 的定义**：vCPU 在宿主运行队列里排队的时间，由 hypervisor 上报，客户机无法自己记账。
2. **判据**：`利用率 + steal ≈ 100%` 才算真的受损；宿主有空闲却仍有 steal，说明是配置问题。
3. **第一层原因**：默认 VM 横跨所有 NUMA 节点，automatic NUMA balancing 不断搬内存/搬任务，消耗的时间变成了 steal。治理：绑 NUMA 节点 + 关掉 NUMA balancing。
4. **第二层原因**：libvirt 默认 per-VM cgroup 且份额平分，导致 vCPU 越多每个 vCPU 分得越少。治理：改成 per-host 单一 cgroup，让份额按 vCPU 平分；需要限速的 VM 再单独拎出去。
5. **第三层原因**（残余）：空闲任务被 CFS 降优先级产生的 steal，不影响性能，不必治。
6. **工程落地**：把绑核、NUMA 分区、跨 socket 迁移放进用户态守护进程 Octopus，因为决策粒度是分钟级；代价是失去内核调度器的自动均衡，需要自己做迁移，而迁移会带来 swap 与 OOM 的坑。

一句话收束：**vCPU 被 CFS 调度这件事，把「性能问题」的定位权从客户机手里拿走了**。客户机只能看到 `st` 这个数字，真正的因果链——NUMA balancing、cgroup 份额、autogroup——全在宿主侧。所以调优的第一步永远是把视角切到宿主，第二步才是动旋钮。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| steal time（`st`） | vCPU 等待物理 CPU 的时间，由 hypervisor 上报给客户机 |
| automatic NUMA balancing | 内核自动在 NUMA 节点间迁移内存或任务，使二者靠近，代价是 CPU 时间 |
| cpu cgroup shares | 按组分配 CPU 权重的机制，libvirt 默认每台 VM 一个组、份额平分 |
| autogroup | 内核隐式按进程属性（用户、session）分组的特性，关掉 cgroup 后会接管 |
| per-host cgroup | DigitalOcean 的改法：整台宿主只留一个 cgroup，让份额按 vCPU 平分 |
| Octopus | 他们的用户态 VM 放置守护进程，负责绑核、NUMA 分区与跨 socket 迁移 |
| CPU 优化型套餐 | 承诺 100% CPU 的产品形态，实现方式是 vCPU 与物理 CPU 一对一绑定 |
| swapoff 收敛 | 迁移后 swapoff 让溢出内存逐步回到物理内存，多轮迭代后收敛 |