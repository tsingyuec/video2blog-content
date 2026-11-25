# VM 退出时谁在存状态：硬件只存一半，另一半由 KVM 的汇编搬

> 视频来源：[Learn KVM 1.2.2 虚拟机切入和退出及相关的上下文保存](https://www.bilibili.com/video/BV1n71jYvEci/)（Bilibili · UP 主 绝对是泽文啦）｜时长约 14 分钟
> 导读：这篇逐行读 `arch/x86/kvm/vmx/vmx.c` 里那段内联汇编。它回答一个很具体的问题：从 host 切到 guest、再从 guest 退回来，**哪些状态是 CPU 自己搬的，哪些必须 KVM 用指令搬**。读完你会知道为什么 VMCS 里没有通用寄存器，为什么 RCX 被单独挑出来，以及为什么 host 的 RSP 可以"懒更新"。

## 本讲要解决的核心问题（SCQA）

**背景**：上一篇把 VMCS 的 guest 区域逐字段填了一遍——段寄存器、描述符表、MSR、非寄存器状态，都在里面。

**冲突**：但那份清单里**没有通用寄存器**。CPU 从 host 模式切到 guest 模式时，并不会自动保存一部分寄存器，典型的就是通用寄存器。也就是说，"vCPU 的状态"并不全在 VMCS 里，还有一半散落在别处，由软件负责搬。

**疑问**：这"另一半"具体是哪些？KVM 用什么办法搬？搬的时候为什么还要讲究"能不写就不写"？

**回答（中心思想）**：VM 切入/切出的状态搬运是**分工**的——硬件通过 VMCS 自动换掉段寄存器、控制寄存器、MSR 这些"有字段"的状态，而**通用寄存器、CR2、host 的 RSP** 这些 VMCS 没有或不便自动处理的状态，由 KVM 在内联汇编里手动存取。并且凡是"没变就不用写"的状态（host RSP、guest 的 RSP/RIP），KVM 都会先比较再决定要不要写 VMCS——因为每一次写 VMCS 都是一次访存。

![vmx.c 里的切入代码：先按 dirty 位决定要不要写 GUEST_RSP / GUEST_RIP，然后 push rdx/rbp/rcx，比较 host_rsp，按需重载 CR2，最后加载 guest 通用寄存器](assets/VM%20退出时谁在存状态：硬件只存一半，另一半由%20KVM%20的汇编搬/00037.webp)

## 一、硬件不管的那一半：通用寄存器

### 1.1 只手动压两个，其余交给 GCC

进入 guest 前，代码里第一件事是保存宿主机的通用寄存器。但仔细看，它只写了两个：

```c
"push %%" R "dx; push %%" R "bp;"
"push %%" R "cx \n\t"
```

为什么只压 RDX 和 RBP？讲者给了两条理由：**RDX 是 GCC 保留的寄存器**，GCC 不会主动处理它；**RBP 在 x86 里一般用作寻址的基地址寄存器**，GCC 也不会主动处理它。所以这两个必须手动保存。[【跳转到 01:52】](https://www.bilibili.com/video/BV1n71jYvEci/?t=112)

那其他通用寄存器呢？它们**在后面实现**——靠内联汇编的 clobber list。把可能被影响的寄存器列在约束列表里，GCC 在把内联汇编和 C 代码一起展开编译时，就会把这一部分也压进栈。[【跳转到 01:27】](https://www.bilibili.com/video/BV1n71jYvEci/?t=87)

![内联汇编的约束列表：每个通用寄存器都对应 vcpu_vmx 里 arch.regs 数组的一个偏移，最后是 clobber 列表（cc、memory、Rax、Rbx、Rdi、Rsi……）](assets/VM%20退出时谁在存状态：硬件只存一半，另一半由%20KVM%20的汇编搬/00262.webp)

这段约束列表值得单独看一眼：每一项都是 `offsetof` 取 `vcpu_vmx` 里 `arch.regs` 数组某个下标的偏移，从 RAX 一路排到 R15，说明**每个通用寄存器在 `vcpu_vmx` 结构体里都有一个固定的槽位**。汇编里直接写 `mov c[rax](%0), %%rax` 这种形式，就是"从结构体偏移处取 guest 的值装进物理寄存器"。[【跳转到 06:52】](https://www.bilibili.com/video/BV1n71jYvEci/?t=412)

### 1.2 RCX 的第二个用途：把 vmx 指针带过边界

除了 RDX 和 RBP，代码还多压了一个 RCX。讲者说这个寄存器"有特殊的使命"。

guest 退出到 host 以后，CPU 不会自动保存 guest 的通用寄存器，KVM 是手动把状态存到 `vcpu_vmx` 这个结构体的子结构体里。**而要写这个结构体，首先得拿到它的地址**——这个地址就是靠 RCX 带过去的。[【跳转到 02:42】](https://www.bilibili.com/video/BV1n71jYvEci/?t=162)

具体做法：约束里把 `vmx` 绑定到 RCX（32 位下就是 ECX），所以 `push rcx` 实际上就是把 vmx 的地址压到栈顶。guest 退出、回到这段栈的时候，第一时间把 RCX 弹出来，就拿到了 vmx 实例。[【跳转到 03:57】](https://www.bilibili.com/video/BV1n71jYvEci/?t=237)

这里有个前提条件：guest 退出时，CPU 会自动把 VMCS 里 **host 的 RSP** 恢复到物理 CPU，所以这个时候我们访问的正是 vCPU 线程在 host 状态下的栈。[【跳转到 05:12】](https://www.bilibili.com/video/BV1n71jYvEci/?t=312)

## 二、退出后的第一件事：把 vmx 换回来

guest 退出后的第一行代码是 `xchg`，把栈顶的值和第 0 号变量交换。[【跳转到 05:37】](https://www.bilibili.com/video/BV1n71jYvEci/?t=337)

为什么是交换而不是弹出？因为刚从 guest 模式切换出来时，**通用寄存器里存的仍然是 guest 的值**，RCX 里是 guest 的 RCX，不是 vmx。一条 `xchg` 同时办了两件事 [【跳转到 06:27】](https://www.bilibili.com/video/BV1n71jYvEci/?t=387)：

1. 把进入之前压入的 vmx 实例换出来；
2. 把 guest 的 RCX 值放回栈里。

拿到 vmx 之后，接下来那一堆 `mov` 就是把 guest 的各个通用寄存器存进 `vcpu_vmx` 对应的槽位。[【跳转到 06:52】](https://www.bilibili.com/video/BV1n71jYvEci/?t=412)

![退出路径：xchg 换回 vmx，pop 把 guest 的 RCX 存进结构体，其余寄存器逐个 mov 回去，最后用 RDI 中转保存 guest 的 CR2](assets/VM%20退出时谁在存状态：硬件只存一半，另一半由%20KVM%20的汇编搬/00337.webp)

反方向（进入 guest 前）就是镜像操作：把 `vcpu_vmx` 里存的 guest 寄存器值逐个装进物理寄存器，然后判断是首次进入还是恢复执行，分别走 `vmlaunch` 和 `vmresume`。[【跳转到 07:17】](https://www.bilibili.com/video/BV1n71jYvEci/?t=437)

![进入 guest 前的最后一段：从结构体偏移处把 guest 的通用寄存器装回物理寄存器，然后 vmlaunch / vmresume 进入 guest 模式](assets/VM%20退出时谁在存状态：硬件只存一半，另一半由%20KVM%20的汇编搬/00487.webp)

## 三、能少写就少写：host RSP 的懒更新

### 3.1 栈没变，就不用写 VMCS

host 的 RSP 也在 VMCS 里，但 KVM 并不会每次都更新它。讲者的推理是：只要 host 的栈不生长也不缩小，RSP 就没变，那就不需要每次都更新；**只有当 RSP 发生变化时，才需要更新 VMCS 里 host 的 RSP 字段**。[【跳转到 08:07】](https://www.bilibili.com/video/BV1n71jYvEci/?t=487)

原因很直接：**每一次写 VMCS 都要访存，访存就代表性能开销**。[【跳转到 08:07】](https://www.bilibili.com/video/BV1n71jYvEci/?t=487)

所以 KVM 在 vcpu 里记录了一份 host 的 RSP 值，每次比较是否变化，没变就跳过：

```c
"cmp %%" R "sp, %c[host_rsp](%0) \n\t"
"je 1f \n\t"
"mov %%" R "sp, %c[host_rsp](%0) \n\t"
__ex(ASM_VMX_VMWRITE_RSP_RDX) "\n\t"
"1: \n\t"
```

这段代码就在上面第一张图里，`cmp` 之后 `je` 直接跳过写 VMCS 的那条指令。[【跳转到 08:55】](https://www.bilibili.com/video/BV1n71jYvEci/?t=535)

### 3.2 guest 的 RSP/RIP 同理

同样的思路也用在 guest 侧：代码里先用 `test_bit` 检查 `VCPU_REGS_RSP` / `VCPU_REGS_RIP` 是否在 `regs_dirty` 位图里被置位，只有脏了才把值写进 VMCS 对应的字段。[【跳转到 00:37】](https://www.bilibili.com/video/BV1n71jYvEci/?t=37)

![汇编段之后的 C 代码：约束列表收尾、regs_avail 与 regs_dirty 的初始化，再从 VMCS 读出退出原因](assets/VM%20退出时谁在存状态：硬件只存一半，另一半由%20KVM%20的汇编搬/00012.webp)

这条经验对做快照很有参考价值：**"状态"和"需要写回去的状态"不是一回事**。运行中的 vCPU 大量状态其实没变，VMM 用 dirty 位图把它们过滤掉；快照要存的是全量，但恢复时可以只写回脏的那部分。

## 四、CR2：硬件明确不管，KVM 自己比

### 4.1 VMX 没有定义 CPU 自动保存 CR2

CR2 是缺页异常发生时记录异常地址的寄存器。讲者指出：**VMX 没有定义 CPU 自动保存 CR2**，因为事实上 host 也可能改变 CR2 的值。[【跳转到 09:31】](https://www.bilibili.com/video/BV1n71jYvEci/?t=571)

于是 KVM 在切入 guest 之前要做一次比较：检测物理 CPU 的 CR2 与 vCPU 中保存的 guest CR2 是否相同，不同就用 guest 的 CR2 更新物理 CPU 的 CR2。[【跳转到 09:56】](https://www.bilibili.com/video/BV1n71jYvEci/?t=596)

代码里就是图里那段 `/* Reload cr2 if changed */`：先把结构体里的值取到 RAX，把物理 CR2 取到 RDX，比较，不同才写回。

![讲者的幻灯片：VMX 没有定义 CPU 自动保存 CR2，但 host 可能改变 CR2 的值，所以切入前要比较、按需重载](assets/VM%20退出时谁在存状态：硬件只存一半，另一半由%20KVM%20的汇编搬/00596.webp)

### 4.2 退出方向：MMIO 缺页也要存回来

反方向也有对应操作。有些 guest 退出是由缺页异常引起的，比如通过 MMIO 方式访问外设 IO；缺页异常会把异常地址记录在 CR2 里，所以 guest 退出以后 KVM 需要保存 guest 的 CR2。[【跳转到 10:12】](https://www.bilibili.com/video/BV1n71jYvEci/?t=612)

这里有一个指令层面的限制：**`mov` 指令不支持控制寄存器到内存地址的直接复制**，所以中间用 RDI 做了一次中转。[【跳转到 10:37】](https://www.bilibili.com/video/BV1n71jYvEci/?t=637)

## 五、从 XCHG 到预留栈位：一次为性能的重写

讲者最后讲了一段"历史"：`xchg` 是一条原子交换指令，**它会锁住地址总线**，为了提高效率，后来 KVM 摒弃了这条指令，设计了一个新方案。[【跳转到 11:27】](https://www.bilibili.com/video/BV1n71jYvEci/?t=687)

新方案的做法是：进入 guest 之前，先在栈上为 guest 的 RCX 预留一个位置（栈顶的下一个位置），也就是只把栈顶指针挪一下；guest 退出时，先把 guest 的 RCX 存进这个预留位置，再 `pop` 出 vmx。[【跳转到 11:59】](https://www.bilibili.com/video/BV1n71jYvEci/?t=719)

代码变成这样：

```c
"mov %0, %c[wordsize](%%" R "sp) \n\t"
"pop %0 \n\t"
```

先把 vmx 写到栈上预留的那个字，再弹出来——等价于一次交换，但没有原子指令的总线锁。[【跳转到 12:49】](https://www.bilibili.com/video/BV1n71jYvEci/?t=769)

![重写后的退出路径：`mov %0, c[wordsize](%Rsp)` 加 `pop %0` 取代了 xchg，随后照旧把 guest 寄存器逐个存回结构体](assets/VM%20退出时谁在存状态：硬件只存一半，另一半由%20KVM%20的汇编搬/00719.webp)

![同一段代码的尾部：加载 guest 寄存器、进入 guest 模式（vmlaunch / vmresume），以及退出后从栈上把 vmx 弹回 RCX](assets/VM%20退出时谁在存状态：硬件只存一半，另一半由%20KVM%20的汇编搬/00794.webp)

## 六、这对"vCPU 状态清单"意味着什么

把这篇和上一篇合起来看，一台 vCPU 的状态其实分成三类，恢复时三类的处理方式完全不同：

| 类别 | 例子 | 谁来存 | 恢复时怎么处理 |
| --- | --- | --- | --- |
| 硬件自动换的状态 | 段寄存器、控制寄存器、MSR、非寄存器状态 | CPU 通过 VMCS 自动存取 | 把 VMCS 字段写回原值 |
| 软件手动搬的状态 | 通用寄存器、CR2 | KVM 的内联汇编 | 写回 `vcpu_vmx` 里的槽位，切入时由汇编装回物理寄存器 |
| 可以不写的状态 | host RSP、未变脏的 guest RSP/RIP | 靠比较 / dirty 位图过滤 | 运行时能省则省；做快照时仍要存全量 |

这也解释了为什么"最小状态集合"这个词要小心用：**对运行时来说最小**（只写变了的）和**对快照来说最小**（只存不存就恢复不出来的）是两个不同的集合。前者靠 dirty 位图，后者靠的是"这个状态能不能从别处重建"。

## 小结

- CPU 从 host 切到 guest 时不会自动保存通用寄存器，这部分由 KVM 的内联汇编负责。
- 只手动 `push` RDX 和 RBP（GCC 保留、不主动处理），其余通用寄存器靠 clobber list 交给 GCC 保存。
- RCX 被单独挑出来携带 `vmx` 指针：进入前压栈，退出后第一时间取回，才能访问 `vcpu_vmx` 里的寄存器槽位。
- 退出后的第一行 `xchg` 一举两得：换出 vmx、把 guest 的 RCX 存回栈里。
- host RSP 采用懒更新：先 `cmp` 再决定要不要写 VMCS，因为写 VMCS 就是访存；guest 的 RSP/RIP 则用 dirty 位图过滤。
- CR2 硬件不自动保存，切入前要比较并按需重载，退出时要把 MMIO 缺页的地址存回来；`mov` 不能直接从控制寄存器写到内存，要用 RDI 中转。
- 后来 KVM 用"预留栈位 + pop"替掉了 `xchg`，因为原子交换会锁地址总线。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| VMCS | 硬件读写的内存结构，保存 guest/host 状态与退出原因 |
| host 状态区域 | VMCS 里存 host（宿主）CPU 状态的那一块，VM exit 时由硬件装回 |
| `vcpu_vmx` | KVM 里描述一个 VMX vCPU 的结构体，`arch.regs[]` 是各通用寄存器的槽位 |
| clobber list | 内联汇编的约束列表，告诉 GCC 哪些寄存器会被改动，由 GCC 负责保存恢复 |
| `regs_dirty` | 位图，标记哪些寄存器被改过，只有脏了才需要写回 VMCS |
| CR2 | 缺页异常时记录出错地址的控制寄存器，VMX 不自动保存 |
| `xchg` | 原子交换指令，会锁地址总线，后来被"预留栈位 + pop"取代 |