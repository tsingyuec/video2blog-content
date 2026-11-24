# VT-x 的特权级真相：从 ring 0 到根模式与非根模式

> 视频来源：[13.1 Hardware Virtualization: VMX Root vs Non-Root | CPU Rings, Intel VT-x, and the KVM Subsystem](https://www.youtube.com/watch?v=b6i7R7Jipqs)（YouTube · Adsorp AI）｜时长约 24 分钟
> 导读：这支视频出自一个系统安全课程的第 13 章，专门讲「CPU 特权模型怎么被硬件虚拟化改写」。本文聚焦 1.1.2 的边界——ring 0-3 为什么不够用、ring -1 这个说法错在哪、根模式与非根模式怎么切换；三种虚拟化路径的分类对比留给相邻小节。

## 本讲要解决的核心问题（SCQA）

**背景**：x86 处理器从 80386 起就有四个特权级 ring 0 到 ring 3。操作系统内核跑在 ring 0，普通应用跑在 ring 3，应用想碰硬件就得通过系统调用陷入内核。这套「一个内核 + 一堆应用」的模型统治了 PC 三十多年。

**冲突**：虚拟化要求同一台物理机上同时跑多个操作系统，每个客户机内核都以为自己是 ring 0 的主人。可 ring 0 只有一个，宿主机自己的内核（以及 hypervisor）已经占着它了。更麻烦的是，x86 指令集里有一批「敏感指令」在低特权级下不会陷入，客户机内核执行它们时会静默失败或读到假数据——这就是著名的 x86 虚拟化漏洞。

**疑问**：既然 ring 0 已经被占用，CPU 的特权级要如何再腾出一层给 hypervisor？是不是像很多人说的那样，加了一个「ring -1」？

**回答（中心思想）**：Intel VT-x 与 AMD-V 并没有在 ring 0 下面再加第五个环，而是增加了一个**与特权级正交的新维度**——VMX 根模式（root operation，跑 hypervisor）与非根模式（non-root operation，跑客户机）。每个模式内部都保留完整的 ring 0-3，所以客户机内核拿到的是**真正的 ring 0**，只是这个 ring 0 被限制在非根模式这个「沙箱维度」里。所谓 ring -1 只是口头上的近似说法，它掩盖了这套二维结构。

## 一、ring 0-3 装不下 hypervisor 的根源

### 1.1 特权指令与敏感指令不是一回事

要理解硬件为什么要改特权模型，先要区分两类指令（[【跳转到 02:10】](https://www.youtube.com/watch?v=b6i7R7Jipqs&t=130)）：

- **特权指令（privileged instruction）**：只有在最高特权级 ring 0 才能执行。ring 1/2/3 的程序一旦执行，CPU 立刻陷入并抛出通用保护异常 #GP。典型例子是 `LLDT`（加载局部描述符表）和 `CLI`（关中断）。
- **敏感指令（sensitive instruction）**：会读取或改写硬件配置与关键系统资源的指令。它又分两小类：**控制敏感**（改系统配置，比如关中断、切换 MMU、改页表）和**行为敏感**（执行结果取决于当前特权级，比如读取当前特权级的指令）。

![特权指令与敏感指令的差别，以及敏感指令为什么必须由 hypervisor 代为执行](assets/VT-x%20的特权级真相：从%20ring%200%20到根模式与非根模式/00130.webp)

### 1.2 Popek-Goldberg 定理：可虚拟化的判据

1974 年 Gerald Popek 与 Robert Goldberg 在论文《Formal Requirements for Virtualizable Third Generation Architectures》里给出一条判据（[【跳转到 03:00】](https://www.youtube.com/watch?v=b6i7R7Jipqs&t=180)）：

$$
\text{架构可虚拟化} \iff \text{敏感指令集合} \subseteq \text{特权指令集合}
$$

翻译成人话：只要客户机做了任何「敏感」的事，硬件都必须先陷入到 hypervisor，让 hypervisor 决定是放行、伪造还是拒绝。满足这条规则的架构，虚拟化就很直接：hypervisor 跑在 ring 0，客户机内核跑在 ring 1 或 ring 3，每次客户机碰敏感指令就陷入，hypervisor 在软件里模拟出它期望的结果，再把指令指针往前推一格继续跑。这套做法叫 **trap and emulate（陷入-模拟）**（[【跳转到 03:50】](https://www.youtube.com/watch?v=b6i7R7Jipqs&t=230)）。

### 1.3 x86 的洞：17 条不设防的敏感指令

问题在于原始 x86 违反了这条定理。Intel 设计 80386 时想的是单租户的桌面与服务器，压根没考虑 hypervisor，于是指令集里留下了 **17 条「敏感但不特权」的指令**：它们在 ring 1/3 执行时不会陷入，而是静默失败、返回误导性数据，或者悄悄改掉状态却不通知 hypervisor（[【跳转到 04:15】](https://www.youtube.com/watch?v=b6i7R7Jipqs&t=255)）。

视频举了三个最典型的例子（[【跳转到 04:40】](https://www.youtube.com/watch?v=b6i7R7Jipqs&t=280)）：

| 指令 | 本意 | 在低特权级下的实际行为 | 后果 |
| --- | --- | --- | --- |
| `POPF` | 从栈上弹出并写入 EFLAGS，其中包括中断标志 IF | 不陷入，只更新算术标志位，对 IF 的修改被静默忽略 | 客户机以为关掉了中断，宿主的物理中断其实还开着 |
| `PUSHF` | 把 EFLAGS 压栈，其中含 IOPL 字段 | 不陷入，客户机内核能读到自己的 CPL 是 01B 而不是 00B | 客户机发现自己没有真正的硬件权限，即「ring aliasing」，内核直接 panic |
| `SMSW` | 把 CR0 低 16 位存到通用寄存器或内存 | 在 ring 3 也能完整执行，不产生异常 | 客户机能直接窥探宿主是否开了保护模式与分页 |

![POPF、PUSHF、SMSW 三条指令各自的漏洞表现](assets/VT-x%20的特权级真相：从%20ring%200%20到根模式与非根模式/00380.webp)

这条「漏洞」的形状可以画成两个嵌套的圈：外圈是特权指令（ring > 0 就陷入），内圈是敏感指令；夹在两者之间、既敏感又不特权的部分，就是 x86 虚拟化漏洞（[【跳转到 06:20】](https://www.youtube.com/watch?v=b6i7R7Jipqs&t=380)）。

在硬件出手之前，业界只能靠两种代价高昂的软件办法绕过去（[【跳转到 06:56】](https://www.youtube.com/watch?v=b6i7R7Jipqs&t=416)）：一是 VMware 首创的**动态二进制翻译（DBT）**，在客户机代码执行前扫描基本块，把 `POPF` 这类指令就地改写成陷入调用，工程复杂度与内存开销都极大；二是**半虚拟化**，直接改客户机内核源码，把敏感指令换成对 hypervisor 的 hypercall，快是快，但拿不到源码的操作系统就跑不了。两条路都说明：软件层已经无解，必须改硬件。

## 二、ring -1 是个方便但不准确的说法

2005 与 2006 年，Intel 的 VT-x（代号 Vanderpool）和 AMD 的 AMD-V（代号 Pacifica）相继落地。它们不是往指令集里加了几条指令那么简单，而是**重新设计了处理器的特权模型**（[【跳转到 08:29】](https://www.youtube.com/watch?v=b6i7R7Jipqs&t=509)）。

这里就是本讲最关键的纠偏。很多工程师第一次接触硬件辅助虚拟化时会说：「哦，Intel 在 ring 0 下面加了一个新环，叫 ring -1 嘛。」视频明确反对这种描述（[【跳转到 08:54】](https://www.youtube.com/watch?v=b6i7R7Jipqs&t=534)）：

> 把 hypervisor 那一层口语化地叫作 ring -1，会掩盖 Intel 与 AMD 真正造出来的东西。芯片架构师**没有**在 ring 0 下面加第五个同心环，而是引入了一个全新的、正交的执行维度。

![纠正 ring -1 的误解：VT-x 增加的是正交的执行维度，而不是更低的一个环](assets/VT-x%20的特权级真相：从%20ring%200%20到根模式与非根模式/00534.webp)

为什么这个区别重要？因为「加一个环」意味着特权级是一条一维的阶梯，越往下权限越大；而「正交维度」意味着特权级变成了一张二维表，同一个 ring 号在不同模式下含义不同。前者无法解释「客户机内核为什么能真的以 ring 0 运行」，后者可以。

## 三、根模式与非根模式：特权级的二维矩阵

### 3.1 两种操作模式

启用 VT-x 后，物理 CPU 只可能处于两种硬件模式之一（[【跳转到 09:19】](https://www.youtube.com/watch?v=b6i7R7Jipqs&t=559)）：

- **VMX 根模式（root operation）**，也叫 host 模式或 hypervisor 模式。这是物理 CPU 的常规执行环境，开机时就处于这个模式。此时处理器表现得和没有虚拟化扩展的普通 x86 一模一样，唯一的区别是它多了一组 VMX 指令（`VMXON`、`VMXOFF`、`VMLAUNCH`、`VMRESUME` 等），可以用来配置、启动和管辖虚拟机。宿主内核与 KVM 这样的 hypervisor 就跑在这里。
- **VMX 非根模式（non-root operation）**，也叫 guest 模式。这是被沙箱化的执行环境。CPU 在非根模式下执行代码时，硬件行为被根本性改写：某些操作、内存访问和敏感指令会被处理器直接拦截，不再静默失败或放任执行，而是强制挂起客户机、切回根模式。这次硬件切换就叫 **VM exit**。

### 3.2 每个模式内部都有完整的四个环

正交设计的核心结论是：非根模式里有自己完整的一套 ring 0-3（[【跳转到 10:28】](https://www.youtube.com/watch?v=b6i7R7Jipqs&t=628)）。把两个维度摊开，就得到一张二维矩阵：

![特权级的二维矩阵：根模式与非根模式各自拥有完整的 ring 0-3，两个维度之间靠 VM exit 与 VM entry 跨越](assets/VT-x%20的特权级真相：从%20ring%200%20到根模式与非根模式/00653.webp)

| 特权级 | VMX 根模式（宿主物理机） | VMX 非根模式（客户虚拟机） |
| --- | --- | --- |
| ring 3（最低） | 宿主用户态工具，如 Firecracker VMM、QEMU、hypervisor 命令行 | 客户机用户态程序，如 Python、Bash、agent 工具、Git |
| ring 2 | 现代操作系统不使用 | 现代操作系统不使用 |
| ring 1 | 现代操作系统不使用 | 现代操作系统不使用 |
| ring 0（最高） | 宿主 hypervisor 内核，如 KVM 内核模块或裸金属 Linux 内核 | 客户机操作系统内核，如 vmlinux 或沙箱化的 guest kernel |

这张表解释了一个反直觉的事实：**客户机内核在非根模式里跑的是货真价实的 ring 0**。它的 CPL（当前特权级）真的是二进制的 00，客户机内核去读 CS 寄存器、去执行 `PUSHF`，处理器如实报告「你在 ring 0」。前面那个让无数客户机内核崩溃的 ring aliasing 问题，就此彻底消失（[【跳转到 11:00】](https://www.youtube.com/watch?v=b6i7R7Jipqs&t=660)）。

### 3.3 由此带来的性能收益

客户机内核既然真的在 ring 0，它就能自己配置页表、自己处理系统调用、自己管理虚拟设备驱动、自己响应线程中断，全程不惊动宿主 hypervisor（[【跳转到 11:30】](https://www.youtube.com/watch?v=b6i7R7Jipqs&t=690)）。

最典型的例子是系统调用。客户机 ring 3 的应用发起 `syscall` 时，物理 CPU 直接跳到非根模式 ring 0 里的客户机系统调用分发器，**不产生任何 VM exit**。这次从 guest 用户态到 guest 内核态的切换完全发生在客户机执行域内部，直接跑在裸金属硅片上，通常不到 50 纳秒（[【跳转到 12:18】](https://www.youtube.com/watch?v=b6i7R7Jipqs&t=738)）。对比之下，用户态内核（如 gVisor）的每次系统调用都要经过宿主陷入、seccomp 过滤或 systrap stub，代价是微秒级的进程上下文切换。这就是硬件虚拟化在系统调用延迟上能接近容器的根本原因。

## 四、切换是怎么发生的：VMXON、VM entry 与 VM exit

### 4.1 硬件拦截的两种形态

非根模式怎么解决那 17 条指令？答案是：处理器进入非根模式后不再盲目执行敏感指令，而是把它们分成两类（[【跳转到 13:00】](https://www.youtube.com/watch?v=b6i7R7Jipqs&t=780)）：

- **无条件 VM exit**：无论 hypervisor 怎么配置，执行就必然退出到根模式。例如 `CPUID`——客户机不许直接读取真实硬件能力，必须退出让 hypervisor 伪造一份 CPU 特性表；又如 `INVD`/`WBINVD` 这类缓存失效指令，防止客户机破坏物理缓存一致性；再如 `VMXON`、`VMLAUNCH`、`VMRESUME` 这些虚拟化管理指令，除非显式开启嵌套虚拟化，客户机不许执行。
- **有条件 VM exit**：可以全速直接执行，也可以按 hypervisor 在内存里设置的位图触发退出。例如写控制寄存器 `MOV CR3`（hypervisor 可以让客户机自己改页表基址，也可以在需要检查页表分配时强制退出）、`IN`/`OUT` 端口 IO（可以放行特定端口，也可以全部陷入去模拟传统外设）、以及 `CLI`/`STI`/`POPF` 的中断开关（处理器可以维护一个虚拟中断标志，让客户机关掉自己的虚拟中断而不影响宿主的物理中断）。

![无条件退出与有条件退出的分工：前者是硬件强制的，后者由 hypervisor 的位图配置决定](assets/VT-x%20的特权级真相：从%20ring%200%20到根模式与非根模式/00772.webp)

### 4.2 用 POPF 收尾：漏洞是被逻辑门堵上的

回到老朋友 `POPF`。在 VT-x 下，非根模式 ring 0 的客户机内核执行 `POPF` 时，物理 CPU 不再静默忽略中断标志，而是去查 hypervisor 配置的虚拟化执行设置：如果配置过，处理器改的是**由硬件维护的、客户机专属的虚拟中断状态**（[【跳转到 14:37】](https://www.youtube.com/watch?v=b6i7R7Jipqs&t=877)）。

结果是客户机内核得到了它期望的语义（在它的虚拟环境里中断确实被屏蔽了），而物理 CPU 的真实中断控制器照常工作，不被打断。视频的总结很到位：这个洞不是靠复杂的动态二进制翻译补上的，而是靠 CPU 自己的物理逻辑门补上的。

![POPF 在非根模式下改写的是硬件维护的虚拟中断标志，宿主中断不受影响](assets/VT-x%20的特权级真相：从%20ring%200%20到根模式与非根模式/00877.webp)

### 4.3 一条完整的 vCPU 生命周期

把指令串起来，就得到一条确定的循环（[【跳转到 15:02】](https://www.youtube.com/watch?v=b6i7R7Jipqs&t=902)）：

1. 宿主 Linux 内核在根模式 ring 0 启动，执行 `VMXON` 打开硬件虚拟化。
2. hypervisor（例如 KVM）初始化虚拟机，分配 VMCS 这类控制结构，并设置初始的 guest 寄存器（RSP、CR0、CR3）。
3. hypervisor 执行 `VMLAUNCH`（首次进入）或 `VMRESUME`（从上次退出处恢复），触发硬件转换 **VM entry**。
4. 客户机在非根模式运行：guest ring 0 跑客户机内核的系统调用分发，guest ring 3 跑应用。
5. 出现敏感事件（未处理的 MMIO、端口 IO、`HLT` 等），硬件触发 **VM exit**。
6. hypervisor 在根模式 ring 0 拿回控制权，读取退出原因，处理虚拟设备 IO 或时钟，推进 guest 的 RIP。
7. 再执行 `VMRESUME` 回到第 4 步。

![进入沙箱的三步：CPUID 检查、CR4 置 VMXE 位、执行 VMXON 指向 4KB 的 VMXON 区域](assets/VT-x%20的特权级真相：从%20ring%200%20到根模式与非根模式/00977.webp)

其中「打开开关」这一步值得单独记（[【跳转到 16:01】](https://www.youtube.com/watch?v=b6i7R7Jipqs&t=961)）：物理机加电时硬件虚拟化扩展默认是关闭的。宿主内核先用 `CPUID` 确认 CPU 支持，再把 CR4 的第 13 位（VMXE）置 1 打开虚拟化逻辑，最后执行 `VMXON` 并把一块 4KB 内存区域的物理地址传给它，这块区域叫 VMXON region。`VMXON` 成功后，物理处理器才正式进入 VMX 根模式操作，具备启动和管理客户机的能力。

至于 VM entry 与 VM exit 期间寄存器状态存在哪里、哪些指令允许执行、哪些会触发陷入——那由 VMCS（虚拟机控制结构）决定，是下一讲的主题，也是本小节第二篇博客的内容。

![VM exit 的四个动作：硬件冻结客户机、把退出原因记入 VMCS、切回根模式、把控制权交给 KVM 的分发逻辑](assets/VT-x%20的特权级真相：从%20ring%200%20到根模式与非根模式/01077.webp)

## 五、这套特权模型的安全含义

视频后半段把硬件机制拉回到它真正关心的问题：不可信代码的隔离。它对比了三种隔离架构在「客户机内核被攻破」时的表现（[【跳转到 18:52】](https://www.youtube.com/watch?v=b6i7R7Jipqs&t=1132)）：

- **普通容器（runc）**：应用直接共享宿主内核。一旦利用内核漏洞提权成功，攻击者拿到的 ring 0 就是**宿主的** ring 0，游戏结束。
- **用户态内核（gVisor）**：应用只跟用户态的 Sentry 打交道，内核漏洞利用往往打不中，但系统调用模拟带来严重延迟。
- **硬件 microVM（VT-x）**：客户机内核被攻破后，攻击者拿到的 ring 0 只在非根模式内有效。它能随意改写客户机自己的内存与页表，但一旦试图访问宿主物理内存或改动物理硬件控制寄存器，硅片就会拦截并触发 VM exit，把控制权交回根模式的宿主 hypervisor。

![三种隔离架构的横向对比：只有 microVM 给客户机「真正的 ring 0」，同时用硬件边界把它关在非根模式里](assets/VT-x%20的特权级真相：从%20ring%200%20到根模式与非根模式/01352.webp)

这就是「非根模式 ring 0」这个设计的价值所在：它同时给了客户机**近乎原生的性能**（系统调用不陷入）和**硬件强制的边界**（越界必然 VM exit）。两者在软件方案里是互斥的。

## 小结

- x86 的 ring 0-3 是一维特权阶梯，hypervisor 需要比客户机内核更高的权限，但 ring 0 已经被占，一维模型装不下这一层。
- 原始 x86 有 17 条「敏感但不特权」的指令，违反 Popek-Goldberg 判据，导致 trap and emulate 失效，只能靠二进制翻译或半虚拟化硬扛。
- VT-x / AMD-V 没有加第五个环，而是加了**正交维度**：VMX 根模式（跑 hypervisor）与非根模式（跑客户机），每个模式内部都有完整的 ring 0-3。
- 客户机内核在非根模式里是**真正的 ring 0**（CPL 为 0），ring aliasing 消失，客户机系统调用不产生 VM exit，延迟可低至几十纳秒。
- 跨越两个维度的动作只有两个：VM entry（`VMLAUNCH` 首次进入 / `VMRESUME` 恢复）与 VM exit（敏感事件触发，硬件切回根模式）。
- 非根模式下的敏感指令分两类：无条件退出（`CPUID`、`INVD`、VMX 指令本身）与有条件退出（`MOV CR3`、`IN`/`OUT`、`CLI`/`STI`/`POPF`，由 hypervisor 的位图决定）。
- ring -1 只是口头近似；准确说法是「hypervisor 运行在根模式，客户机运行在非根模式」，特权级因此从一条线变成一张二维表。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| 特权指令 | 只有 ring 0 能执行、否则抛 #GP 的指令，如 `LLDT`、`CLI` |
| 敏感指令 | 会读写硬件配置或关键系统资源的指令，分控制敏感与行为敏感两类 |
| Popek-Goldberg 判据 | 架构可虚拟化当且仅当所有敏感指令都是特权指令 |
| trap and emulate | 客户机执行敏感指令时陷入 hypervisor，由软件模拟结果后继续 |
| ring aliasing | 客户机内核在低环运行，一读 CPL 就露馅，导致内核崩溃 |
| VMX 根模式 | hypervisor 所在的执行环境，可使用 VMX 指令管理虚拟机 |
| VMX 非根模式 | 客户机所在的沙箱执行环境，敏感操作被硬件拦截 |
| VM entry | 从根模式切入非根模式，由 `VMLAUNCH` 或 `VMRESUME` 触发 |
| VM exit | 从非根模式退回根模式，由敏感事件触发，原因记录在 VMCS |
| VMXON | 打开 VMX 操作的指令，需传入一块 4KB 的 VMXON 区域物理地址 |
| CPL | 当前特权级，非根模式下的客户机内核 CPL 为 0 |