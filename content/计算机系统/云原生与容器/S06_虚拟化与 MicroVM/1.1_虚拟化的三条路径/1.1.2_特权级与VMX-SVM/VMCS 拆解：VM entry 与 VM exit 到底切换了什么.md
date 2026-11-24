# VMCS 拆解：VM entry 与 VM exit 到底切换了什么

> 视频来源：[13.2 VMCS Lifecycle & Handling VM Exits | CPU Rings, Intel VT-x, and the KVM Subsystem](https://www.youtube.com/watch?v=LQ6dQN6rGqg)（YouTube · Adsorp AI）｜时长约 26 分钟
> 导读：这是上一讲的直接续篇。上一讲说明 VT-x 用根模式/非根模式这个正交维度替代了「ring -1」；这一讲打开两个模式之间的那本「账本」——VMCS，看一次 VM entry 与 VM exit 究竟由硬件自动搬运了哪些状态、哪些必须由软件自己保存。

## 本讲要解决的核心问题（SCQA）

**背景**：上一讲已经确认，Intel VT-x 用根模式与非根模式把 hypervisor 和客户机分到两个维度，每个维度内部都有完整的 ring 0-3，两者之间靠 VM entry 与 VM exit 切换。

**冲突**：切换意味着 CPU 要从「跑客户机内核」瞬间变成「跑宿主 hypervisor」，寄存器、控制位、段描述符全都要换一套。这些状态存在哪里？CPU 又怎么知道客户机执行 `CPUID` 该退出、执行 `MOV CR3` 该不该退出？如果每次切换都把 16 个通用寄存器刷进内存，延迟会高到无法接受。

**疑问**：是什么数据结构在管理这两个维度之间的每一次跨越？它长什么样、由谁读写、切换时哪些字段自动生效、哪些字段必须软件补上？

**回答（中心思想）**：这个结构叫 **VMCS（Virtual Machine Control Structure，虚拟机控制结构）**，是每个 vCPU 一块 4KB 的物理内存页，软件只能通过 `VMREAD`/`VMWRITE` 这类专用指令访问。它被划分为六个功能区：guest 状态区、host 状态区、VM 执行控制、VM 退出控制、VM 进入控制、VM 退出信息。VM entry 时硬件按 guest 状态区装载客户机上下文，VM exit 时硬件把客户机状态存回 guest 状态区、按 host 状态区恢复宿主上下文，并把退出原因写进退出信息区。**通用寄存器不在自动搬运之列**——这是刻意的性能取舍，由 hypervisor 的汇编例程自己保存。

## 一、VMCS 是一块 4KB 的不透明内存页

### 1.1 它是什么

VMCS 是驻留在宿主物理内存里的一个 4KB 页，每个分配给虚拟机的 vCPU 都有自己独立的一块（[【跳转到 01:13】](https://www.youtube.com/watch?v=LQ6dQN6rGqg&t=73)）。如果 VMX 模式定义了沙箱的硅片边界，VMCS 就是这条边界上每一次跨越的**配置状态与飞行记录仪**。

关键限制是：**不能把它当成普通 C 结构体用**。你不能 malloc 一块内存、拿一个结构体指针直接给「guest 指令指针」字段赋值。原因是 VMCS 的内部布局是 Intel 私有的、与微架构相关的、对软件不透明的（[【跳转到 01:30】](https://www.youtube.com/watch?v=LQ6dQN6rGqg&t=90)）。

![VMCS 的物理布局：前 4 字节是修订标识符，4 到 7 字节是 VMX 中止指示器，8 到 4095 字节是只能通过 VMREAD 与 VMWRITE 访问的不透明存储区](assets/VMCS%20拆解：VM%20entry%20与%20VM%20exit%20到底切换了什么/00130.webp)

页内布局大致是：

- **偏移 0-3 字节**：31 位的 VMCS 修订标识符，从 `IA32_VMX_BASIC` 这个 MSR 读出后由软件写入。
- **偏移 4-7 字节**：VMX 中止指示器，由硅片在发生灾难性硬件故障时写入。
- **偏移 8-4095 字节**：不透明的硬件数据区，CPU 微码管理，软件只能通过 `VMREAD` 读、通过 `VMWRITE` 写。

视频强调了两点工程后果：一是字段偏移会随处理器代际变化（Skylake、Ice Lake、Sapphire Rapids 各不相同），所以软件绝不能硬编码偏移；二是现代 CPU 会把当前活跃的 VMCS 的一部分缓存在片内 SRAM 里，避免每次上下文切换都去访问外部 DRAM。

### 1.2 分配与激活：一条严格的握手流程

要让一块 VMCS 生效，hypervisor 必须按固定顺序走完（[【跳转到 02:28】](https://www.youtube.com/watch?v=LQ6dQN6rGqg&t=148)）：

1. **查硬件参数**：读 `IA32_VMX_BASIC`（MSR 0x480），拿到本 CPU 支持的 31 位修订标识符、所需内存大小（现代 x86-64 上固定 4096 字节）以及应使用的内存缓存类型。
2. **分配对齐的物理内存**：申请一块 4KB 物理连续、按 4K 页边界对齐的内存。
3. **写入修订标识符**：把 31 位修订号写进这块页的前 4 个字节，第 31 位清零；若虚拟化过程中发生灾难性硬件故障，CPU 会把这一位置 1 作为中止指示。
4. **执行 `VMCLEAR`**：传入这块页的 64 位物理地址，让 CPU 把与该 VMCS 相关的内部缓存刷回内存，并把该 VMCS 标记为 clear 且 inactive 状态。
5. **执行 `VMPTRLD`**：把这个物理地址加载为当前物理核上的活跃 VMCS（[【跳转到 03:31】](https://www.youtube.com/watch?v=LQ6dQN6rGqg&t=211)）。

### 1.3 读写字段：VMREAD 与 VMWRITE

VMCS 激活后，软件用两条专用汇编指令访问其中的字段（[【跳转到 03:58】](https://www.youtube.com/watch?v=LQ6dQN6rGqg&t=238)）：`VMREAD` 与 `VMWRITE`。它们不用字节偏移，而是用 Intel 为每个可配置属性分配的**32 位字段编码**。例如 guest 指令指针的编码是 `0x0000681E`，主处理器执行控制字段的编码是 `0x00004002`。

如果读写了非法字段编码，或者在没有活跃 VMCS 时执行 `VMREAD`/`VMWRITE`，CPU 会把进位标志 CF 置 1 或零标志 ZF 置 1，让 hypervisor 在真正启动客户机之前就抓到配置错误。

## 二、六个功能区：一本账分成六栏

概念上，这块不透明的 4KB 被切成六个逻辑区，合起来构成「客户机沙箱环境 + 宿主恢复现场」的完整规格（[【跳转到 05:02】](https://www.youtube.com/watch?v=LQ6dQN6rGqg&t=302)）：

![VMCS 的六个功能区：guest 状态、host 状态、VM 执行控制、VM 退出控制、VM 进入控制、VM 退出信息](assets/VMCS%20拆解：VM%20entry%20与%20VM%20exit%20到底切换了什么/00327.webp)

| 功能区 | 装什么 | 谁写、何时生效 |
| --- | --- | --- |
| guest 状态区 | RIP、RSP、RFLAGS、CR0/3/4、各段寄存器、MSR、活动状态 | hypervisor 用 VMWRITE 初始化；VM entry 时由硬件装载，VM exit 时由硬件存回 |
| host 状态区 | RIP、RSP、CR0/3/4、CR3（宿主页表）、段选择子 | hypervisor 初始化时静态写入；VM exit 时由硬件原子恢复 |
| VM 执行控制 | pin 级、处理器级、次级控制、CR 影子 | hypervisor 用 VMWRITE 配置沙箱策略 |
| VM 退出控制 | 64 位宿主模式、MSR 保存/加载列表、抢占定时器 | 决定退出瞬间 CPU 的行为 |
| VM 进入控制 | 事件注入（中断/异常）、MSR 加载列表 | 决定进入客户机前要注入什么事件 |
| VM 退出信息 | 退出原因、退出资格、guest 线性地址 | 只读，由 CPU 微码在退出时写入 |

### 2.1 guest 状态区与 host 状态区

guest 状态区保存的是「VM entry 时要装进物理核的那套执行上下文」（[【跳转到 06:40】](https://www.youtube.com/watch?v=LQ6dQN6rGqg&t=400)）：控制与调试寄存器（CR0、CR3 页表基址、CR4、DR7）、指令与栈指针（RIP、RSP）、RFLAGS、段寄存器（CS、DS、ES、FS、GS、TR、LDTR）、描述符表寄存器（GDTR、IDTR 的基址与限长）、MSR（IA32_SYSENTER 系列、IA32_EFER、IA32_PAT），以及活动状态（运行中、HLT 停机、三重故障关机、等待 SIPI）和中断性状态（比如刚执行完 `STI` 或 `MOV SS` 之后，硬件要延迟一条指令才允许中断）。

有个细节值得注意：对每个段寄存器，VMCS 不只存 16 位选择子，还**缓存了基址、限长与访问权限**。这样 CPU 执行段检查时不必每次都去遍历客户机的描述符表，省掉了大量内存访问。

host 状态区则是 hypervisor 的「返场剧本」：宿主 CR0/CR3/CR4、host RIP（hypervisor 的 VM exit 处理例程入口）、host RSP（hypervisor 私有的内核栈）、宿主段选择子、GDTR/IDTR 基址、以及若干宿主 MSR。这些字段在 vCPU 初始化时写一次，之后在每次 VM exit 时被硬件原子地装回。

![guest 状态区与 host 状态区的分工：一个负责进入时装载，一个负责退出时恢复](assets/VMCS%20拆解：VM%20entry%20与%20VM%20exit%20到底切换了什么/00432.webp)

### 2.2 一个反直觉的缺口：通用寄存器不在里面

视频在这里点出了最容易被忽略的工程细节（[【跳转到 07:55】](https://www.youtube.com/watch?v=LQ6dQN6rGqg&t=475)）：**guest 状态区和 host 状态区里都没有通用寄存器**。硬件不会自动保存或恢复 RAX、RBX、RCX、RSI、RDI，以及 R8 到 R15。

原因是性能：如果每次切换都把 16 个通用寄存器刷进内存，进入和退出虚拟化的延迟会直线上升。硅片只负责恢复 RSP 和 RIP，其余通用寄存器由 hypervisor 软件在进入前压栈、在退出后立刻保存。

这带来一个实践上的后果：VM exit 处理例程通常用汇编写，第一件事就是把客户机的通用寄存器存进每 vCPU 的内存缓冲区，最后再把它们恢复回去，然后才执行 `VMRESUME`。漏掉这一步，客户机恢复后读到的就是被 hypervisor 弄脏的值。

### 2.3 VM 执行控制：沙箱策略写在这里

执行控制区是「沙箱的配置引擎」，决定客户机哪些操作可以自主执行、哪些必须陷入（[【跳转到 08:27】](https://www.youtube.com/watch?v=LQ6dQN6rGqg&t=507)）。它分三组位图：

- **pin 级执行控制**：管外部异步硬件信号。比如「外部中断退出」置 1 时，本该送给宿主的中断会立刻触发 VM exit，而不是投递给客户机；「NMI 退出」控制不可屏蔽中断是否陷入宿主。
- **处理器级执行控制（主/次级）**：管客户机执行的同步指令。关键位包括 `HLT exiting`（客户机执行 `HLT` 就陷入，宿主可以把线程挂起、让出 CPU）、`CR3 load/store exiting`（客户机一碰顶层页表寄存器就退出）、`Use I/O bitmaps`（用两张 4KB 位图分别覆盖 0x0000-0x7FFF 与 0x8000-0xFFFF 端口，位为 1 的端口访问触发退出，为 0 则零开销直通）、`Unrestricted guest`（让客户机在实模式或未分页的保护模式下也能跑，加速启动）、`Enable EPT` 与 `Enable VPID`（开启嵌套分页与带标签的 TLB）。
- **CR0/CR4 的 guest/host mask 与 read shadow**：这是「骗客户机」的机制。如果 hypervisor 在 mask 里把某位置 1，客户机任何写这一位的尝试都会陷入；而客户机读 CR0 时，硅片不返回真实硬件寄存器，而是返回 read shadow 字段里的值。客户机以为自己关掉了某个控制位，底层物理硬件其实仍然强制开启。

### 2.4 退出控制、进入控制与退出信息

**VM 退出控制**决定退出瞬间 CPU 的行为（[【跳转到 10:20】](https://www.youtube.com/watch?v=LQ6dQN6rGqg&t=620)）：最重要的是第 9 位「host address-space size」，置 1 时处理器退出后直接进入 64 位长模式，置 0 则退回 32 位宿主状态；此外还有 MSR 保存/加载列表指针，以及 `Save VMX-preemption timer`（用硬件抢占定时器强制打断跑飞的客户机任务）。

**VM 进入控制**负责把事件注入客户机（[【跳转到 10:52】](https://www.youtube.com/watch?v=LQ6dQN6rGqg&t=652)）：VM entry 中断信息字段允许 hypervisor 在 `VMRESUME` 的同时注入硬件中断、NMI 或软件异常（如 #GP、#PF），在客户机看来这个事件就像由原生 CPU 执行单元直接产生的一样。MSR 加载列表则指定在客户机开始执行前必须原子写入的 MSR。

**VM 退出信息**区是只读的诊断栏，由 CPU 微码在退出时写入（[【跳转到 11:23】](https://www.youtube.com/watch?v=LQ6dQN6rGqg&t=683)）：16 位的**基本退出原因**（例如 `0x0000000A` 表示 `CPUID`，`0x0000001C` 表示控制寄存器访问，`0x00000030` 表示 `IN`/`OUT` 指令）、64 位的**退出资格（exit qualification）**（对控制寄存器访问来说，它编码了是哪个寄存器、是读还是写、用哪个通用寄存器做源或目的）、以及 **guest 线性地址（GLA）**（内存缺页类退出涉及到的虚拟地址）。

![六个功能区的字段归属与交互流程：hypervisor 配置边界与宿主状态，CPU 微码在退出时更新 guest 状态并写诊断信息](assets/VMCS%20拆解：VM%20entry%20与%20VM%20exit%20到底切换了什么/00732.webp)

![四类控制与信息区的分工：执行控制管拦截策略、退出控制管退出行为、进入控制管事件注入、退出信息管诊断](assets/VMCS%20拆解：VM%20entry%20与%20VM%20exit%20到底切换了什么/00632.webp)

## 三、一次完整的 VMX 转换循环

把字段串起来，vCPU 的生命周期是一条确定的六步循环（[【跳转到 13:22】](https://www.youtube.com/watch?v=LQ6dQN6rGqg&t=802)）：

1. 在根模式 ring 0：`VMCLEAR` → `VMPTRLD` → `VMWRITE` 写入 guest/host 状态与执行控制。
2. 把宿主通用寄存器压栈，执行 `VMLAUNCH`，触发硬件 VM entry。
3. 在非根模式：客户机原生执行，ring 3 跑应用、ring 0 跑客户机内核，全速运行。
4. 出现被拦截的操作（`CPUID`、`CLT`、写 CR3 等），触发硬件 VM exit。
5. 回到根模式：hypervisor 入口点触发，保存客户机通用寄存器，`VMREAD` 读退出原因，分发到模拟逻辑，推进 guest RIP。
6. 恢复客户机通用寄存器，执行 `VMRESUME`，硬件走快速路径校验后重新装载客户机状态，回到第 3 步。

### 3.1 阶段一：校验与首次启动（VMLAUNCH）

在 vCPU 执行第一条指令之前，hypervisor 用 `VMWRITE` 写入初始参数（[【跳转到 14:57】](https://www.youtube.com/watch?v=LQ6dQN6rGqg&t=897)）：把 guest RIP 指向客户机固件或内核入口，guest RSP 指向引导栈，guest CR3 装入客户机初始页目录的物理地址，并把通用寄存器清零。然后把自己的寄存器上下文压到私有栈上，执行 `VMLAUNCH`。

`VMLAUNCH` 触发时，处理器微码会做一轮**VMCS 一致性检查**：guest CR0 的配置与当前操作模式兼容吗？CR4 的保留位都清零了吗？host RIP 指向的是规范的 64 位地址吗？段属性与限长自洽吗？任何一项不通过，CPU 立刻中止启动，物理寄存器保持原样，把 CF 置 1，然后从 `VMLAUNCH` 的下一条指令继续执行宿主代码。全部通过，CPU 才原子地换入客户机状态、把内部模式切到非根模式，从 guest RIP 开始取指。

![VMLAUNCH 之前的三件事：用 VMWRITE 配置 guest 入口状态、保存宿主寄存器、由微码做 VMCS 一致性校验](assets/VMCS%20拆解：VM%20entry%20与%20VM%20exit%20到底切换了什么/00943.webp)

### 3.2 阶段二：客户机原生执行

进入非根模式后，处理器以原生硅片时钟频率直接执行指令（[【跳转到 16:07】](https://www.youtube.com/watch?v=LQ6dQN6rGqg&t=967)）。客户机用户态进程发起 `syscall` 时，硬件查客户机内核配置的 `IA32_LSTAR`，直接把执行流导向非根模式 ring 0 的客户机系统调用分发器——**不产生 VM exit**。客户机内核管理内存分配、处理算术运算、调度内部线程，全程原生速度。

### 3.3 阶段三：拦截与 VM exit

客户机迟早会做一件 VMCS 配置了拦截的事。以 `CPUID` 为例（[【跳转到 16:35】](https://www.youtube.com/watch?v=LQ6dQN6rGqg&t=995)）：客户机内核不允许知道真实的物理硬件拓扑与特性，所以 `CPUID` 是无条件退出。硬件在指令退休前停下，微码依次做五件事：

1. 把当前 RIP（正指向这条 `CPUID`）、RSP、RFLAGS 与段状态存进 VMCS 的 guest 状态区；
2. 把整数 10（`CPUID` 的架构退出原因码）写进退出原因字段；
3. 把 CPU 内部状态切回根模式；
4. 把宿主页表基址装入 CR3，从 host RSP 恢复宿主栈指针，从 host RIP 装入指令指针；
5. 执行流无缝落到宿主内核空间的 hypervisor 退出处理例程。

### 3.4 阶段四：hypervisor 分诊与 VMRESUME

退出处理例程通常用汇编写，第一件事是把客户机通用寄存器（RAX、RBX、RCX 等）存进每 vCPU 的内存缓冲区（[【跳转到 17:32】](https://www.youtube.com/watch?v=LQ6dQN6rGqg&t=1052)）。接着 `VMREAD` 读退出原因字段，拿到 10，跳到 `CPUID` 模拟逻辑：从保存的寄存器里读出客户机请求的 leaf 号，伪造一份合成结果（隐藏 AVX-512 之类的宿主特性、隐藏物理核数），把结果写回缓冲区里的 RAX/RBX/RCX/RDX。

关键一步是**推进 RIP**：hypervisor 读 VMCS 里的「退出指令长度」字段，得知 `CPUID` 是 2 字节，于是用 `VMWRITE` 给 guest RIP 加 2，保证恢复后客户机从下一条指令继续，而不是原地死循环重执行 `CPUID`。最后恢复通用寄存器，执行 `VMRESUME`。

`VMRESUME` 是 `VMLAUNCH` 的快速路径兄弟（[【跳转到 18:31】](https://www.youtube.com/watch?v=LQ6dQN6rGqg&t=1111)）：因为 VMCS 已经通过过一致性检查，它跳过繁重的结构校验，几百个时钟周期内就重新进入非根模式，从上次离开的地方继续跑。

![阶段四：hypervisor 的退出处理例程在根模式保存寄存器、模拟被拦截的指令、调整指令指针，然后 VMRESUME 返回](assets/VMCS%20拆解：VM%20entry%20与%20VM%20exit%20到底切换了什么/01053.webp)

## 四、这套机制为什么能关住被攻破的客户机内核

视频最后把 VMCS 接到它真正关心的场景：不可信的自动化代码（比如一个会下载、编译、运行第三方库的 AI 编码代理）。假设第三方库里有针对客户机 Linux 内核的零日漏洞，代理成功提权，拿到了客户机 ring 0（[【跳转到 19:38】](https://www.youtube.com/watch?v=LQ6dQN6rGqg&t=1178)）。

在共享内核的容器里，这就是灾难：ring 0 就是宿主的 ring 0。但在由正确配置的 VMCS 管辖的 microVM 里，攻击者拿到的 ring 0 只在非根模式内有效。视频给了两条具体的拦截线。

### 4.1 第一条线：CR3 load exiting

要逃出虚拟化的牢笼，被攻破的客户机内核必须重写页表，把宿主物理内存映射进自己的地址空间。它大概会执行一段把未授权的物理地址装进页表基址寄存器的汇编（[【跳转到 20:47】](https://www.youtube.com/watch?v=LQ6dQN6rGqg&t=1247)）。

在裸金属内核上，这条指令瞬间生效。但在 microVM 里，hypervisor 早就把 VMCS 处理器级执行控制中的 `CR3 load exiting` 置 1。物理 CPU 在执行单元碰到真实 CR3 之前就解码出陷阱条件，把指令扣在中途，往退出原因里写 28（控制寄存器访问），往退出资格里写清细节。**这条指令从未执行**。客户机内核想让 MMU 指向任何地方，都必须经过宿主 hypervisor 的明确知情与仲裁。

### 4.2 第二条线：CR0/CR4 的 mask 与 shadow

第二条线针对的是攻击者想关掉 CPU 安全缓解措施。内核漏洞利用经常尝试清掉 CR0 第 16 位的 WP（写保护）以便覆写只读内核代码段，或者清掉 CR4 第 20 位的 SMEP（管理模式执行保护）以便从 ring 0 执行用户态 shellcode（[【跳转到 21:46】](https://www.youtube.com/watch?v=LQ6dQN6rGqg&t=1306)）。

hypervisor 的应对是：在 VMCS 的 `CR0 guest/host mask` 与 `CR4 guest/host mask` 里，把 WP、SMEP 这些位对应的位置 1；同时把 `CR0 read shadow`、`CR4 read shadow` 设成客户机期望看到的值。于是：

- 攻击者执行写 CR0 清 WP 的指令时，物理 CPU 立刻触发 VM exit；
- 如果 hypervisor 选择「模拟」这次操作，它只更新 read shadow，让客户机**以为**这一位被关掉了；
- 底层物理硬件的写保护位依然牢牢开着，客户机随后去写只读内存时会触发真正的缺页异常，payload 当场崩溃。

视频的结论是：VMCS 把物理 CPU 变成了一个不眨眼的硬件仲裁者。自动化代理可以在客户机里拿到任意代码执行、可以改坏客户机内核的所有数据结构、可以完全控制 guest ring 0，但它始终被 VMCS 的执行控制字段关在边界之内。

![攻击场景：客户机提权成功后试图改写 CR3 指向宿主内存，被 CR3 load exiting 拦下并触发确定性的 VM exit](assets/VMCS%20拆解：VM%20entry%20与%20VM%20exit%20到底切换了什么/01203.webp)

## 五、小结与下一步

![VMCS 的心智模型：一块不透明的 4KB 硅片配置、六个功能区、通用寄存器需软件保存、一条确定的 VMX 转换循环](assets/VMCS%20拆解：VM%20entry%20与%20VM%20exit%20到底切换了什么/01420.webp)

- VMCS 是每个 vCPU 一块 4KB 的物理内存页，布局私有且随微架构变化，只能用 `VMCLEAR`、`VMPTRLD`、`VMREAD`、`VMWRITE` 操作。
- 它分成六个功能区：guest 状态区（entry 时装载、exit 时存回）、host 状态区（exit 时原子恢复）、VM 执行控制（拦截策略）、VM 退出控制（退出行为）、VM 进入控制（事件注入）、VM 退出信息（退出诊断）。
- **通用寄存器不由硬件自动保存**，这是为了压低切换延迟的刻意取舍，由 hypervisor 的汇编例程负责保存与恢复。
- 转换循环是确定的：`VMCLEAR`/`VMPTRLD` 初始化 → `VMLAUNCH` 首次进入 → 客户机原生执行 → 被拦截操作触发 VM exit → hypervisor 读退出原因、模拟、推进 RIP → `VMRESUME` 快速恢复。
- `VMLAUNCH` 会做完整的 VMCS 一致性校验，失败则 CF 置 1 并原地返回；`VMRESUME` 跳过重校验，因此快得多。
- 安全上，`CR3 load exiting` 与 CR0/CR4 的 mask + shadow 组合，使被完全攻破的客户机内核也无法改写关键控制位或访问宿主内存而不触发 VM exit。

视频结尾留了一个明显的缺口：客户机内核既然能在非根模式里自己建页表，什么阻止它把虚拟地址直接映射到宿主物理内存？答案是下一节的 EPT/NPT（扩展页表与嵌套页表），也就是本系列 2.1 与 2.2 的内容。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| VMCS | 每 vCPU 一块 4KB 的硬件控制结构，保存 guest/host 状态与控制策略 |
| VMREAD / VMWRITE | 按 32 位字段编码读写 VMCS 字段的专用指令 |
| VMCLEAR / VMPTRLD | 把 VMCS 标记为 clear/inactive 与设为当前活跃 VMCS 的指令 |
| guest 状态区 | VM entry 时装载进物理核的客户机上下文 |
| host 状态区 | VM exit 时原子恢复的宿主 hypervisor 上下文 |
| VM 执行控制 | 决定哪些指令与中断触发 VM exit 的位图策略 |
| 退出原因 | 16 位编码，说明这次 VM exit 由什么引起，如 10 是 `CPUID` |
| 退出资格 | 64 位细节字段，如控制寄存器访问是哪一号寄存器、读还是写 |
| CR0/CR4 mask 与 shadow | 让客户机读到假的控制位、同时底层硬件保持强制的机制 |
| VMLAUNCH / VMRESUME | 首次进入客户机与从退出处恢复客户机的两条 VM entry 指令 |
| VMX-preemption timer | 硬件抢占定时器，用于强制打断跑飞的客户机任务 |