# vCPU 的状态清单：VMCS 的 guest 区域里到底要填哪些字段

> 视频来源：[13-填充guest区域MSR和非寄存器状态字段](https://www.bilibili.com/video/BV1X3wbzsEfi/)（Bilibili · UP 主 51HOOK）｜时长约 28 分钟
> 导读：这是一节手写 hypervisor 的实机编码课，讲者对着 Intel 白皮书卷三第 27 章，把 VMCS 的 guest 区域剩下的字段一项项填完。本文把它整理成一份"vCPU 状态清单"：段寄存器与描述符缓存、GDTR/IDTR、几个必填的 MSR，以及四个不对应任何寄存器的非寄存器状态字段。

## 本讲要解决的核心问题（SCQA）

**背景**：想恢复一台 vCPU，得先知道"一台 vCPU 有哪些状态"。这件事其实有官方答案——Intel 白皮书卷三第 27.4 节把 guest 的状态分门别类列了出来，硬件在 VM entry 时读的就是这些字段，VM exit 时写的也是这些字段。

**冲突**：这份清单比想象的长，而且**并不全是寄存器**。段寄存器里存的不只是选择子，还有一份"隐藏"的描述符缓存；MSR 有一大堆，但白皮书只点名了少数几个必须填；最后还有一组字段，它们在任何寄存器里都读不到，只存在于 VMCS 里。

**疑问**：这份清单到底分几组？每组里"必须填"的是哪几个？那些读不出来的状态又是什么？

**回答（中心思想）**：VMCS 的 guest 区域就是硬件视角下的"vCPU 状态清单"，它分成三层——**寄存器状态**（通用寄存器、段寄存器及其描述符缓存、描述符表、控制/调试寄存器、RFLAGS、以及白皮书点名的几个 MSR）、**非寄存器状态**（activity state、interruptibility state、pending debug exceptions、VMCS link pointer），以及**由 VMM 自己保管的那部分**（比如本讲留到下一节的 RSP 与 RIP 的取值来源）。要恢复一台 vCPU，把这三层按原值写回去就够了；写少了，恢复出来的 CPU 行为会和快照那一刻不一致。

![白皮书里段寄存器字段的说明：base、limit、access rights 三部分构成段寄存器的"隐藏"部分，也就是描述符缓存，它们被放进 VMCS 是因为描述符缓存可能与内存中的描述符不一致](assets/vCPU%20的状态清单：VMCS%20的%20guest%20区域里到底要填哪些字段/00040.webp)

## 一、寄存器状态：先填段，再填表

### 1.1 段寄存器不止一个选择子

写代码时我们看到的段寄存器（CS/DS/ES/FS/GS/SS）只有一个 16 位的选择子，但硬件内部还缓存着这个选择子指向的描述符内容：**base、limit、access rights**。白皮书把这部分叫"隐藏"部分（hidden part），也叫描述符缓存（descriptor cache）。[【跳转到 00:40】](https://www.bilibili.com/video/BV1X3wbzsEfi/?t=40)

它被单独放进 VMCS，理由白皮书讲得很直白：**描述符缓存可能与内存里的描述符不一致**——GDT 里的描述符随时可能被改，而 CPU 内部缓存的那份还是旧的。所以恢复一台 vCPU 时，不能只恢复选择子然后让硬件重新去 GDT 里查一遍，必须把缓存的那份原值一起写回去。

access rights 这一栏的位定义也在同一张表里：第 13 位是 L（64 位模式，仅对 CS 有效），第 14 位是 D/B（默认操作数大小），第 15 位是 G（粒度），第 16 位是 unusable（段不可用）。[【跳转到 00:40】](https://www.bilibili.com/video/BV1X3wbzsEfi/?t=40)

代码里的写法就是一组一一对应的赋值：选择子用 `read_cs`、`read_ss` 这类指令读出来，base 则要拿选择子在 GDT 里查——讲者写的辅助函数注释得很清楚：**段描述符地址 = GDT.base + Selector.index × 8**。[【跳转到 01:55】](https://www.bilibili.com/video/BV1X3wbzsEfi/?t=115)

![填充代码：DS/ES/FS/GS/TR/LDT 的 access rights、CR0/CR3/CR4、DR7、RFLAGS，以及计算段 base 的辅助函数（注释写着段描述符地址 = GDT.base + Selector.index * 8）](assets/vCPU%20的状态清单：VMCS%20的%20guest%20区域里到底要填哪些字段/00115.webp)

同一屏里还能看到这一组的其他成员：**CR0、CR3、CR4**（控制寄存器）、**DR7**（调试寄存器）、**RFLAGS**（标志寄存器）。它们都是"读出来直接写进去"的关系，没有额外的解释成本。[【跳转到 01:55】](https://www.bilibili.com/video/BV1X3wbzsEfi/?t=115)

### 1.2 GDTR 和 IDTR：只有 base 和 limit

描述符表寄存器比段寄存器简单得多。白皮书对 GDTR 和 IDTR 只要求两项：**base（64 位）和 limit（32 位）**。注意 limit 在架构上只有 16 位，但 VMCS 里的字段给了 32 位。[【跳转到 00:40】](https://www.bilibili.com/video/BV1X3wbzsEfi/?t=40)

读取用 `sgdt` / `sidt` 两条指令，读进一个伪描述符结构体，再把结构体里的 base 和 limit 分别写进 VMCS 的四个字段（GDTR_BASE、IDTR_BASE、GDTR_LIMIT、IDTR_LIMIT）。[【跳转到 01:05】](https://www.bilibili.com/video/BV1X3wbzsEfi/?t=65)

![填充 guest 段选择子与段 base 的代码：CS/SS/DS/ES/FS/GS/LDTR/TR 逐个写入，base 由 GDT 加选择子索引算出](assets/vCPU%20的状态清单：VMCS%20的%20guest%20区域里到底要填哪些字段/00090.webp)

## 二、MSR：白皮书只点名了几个，其余不用填

### 2.1 五个必填的 MSR

白皮书在 guest 区域里列了一长串 MSR，但讲者明确说：**并不是所有都要填，只挑出必须填的几个，其余不管**。[【跳转到 03:25】](https://www.bilibili.com/video/BV1X3wbzsEfi/?t=205) 他挑出来的是这五个：

| MSR | 作用（按视频里的说法） |
| --- | --- |
| `IA32_DEBUGCTL` | 调试控制，跟调试相关的那个"debug" |
| `IA32_SYSENTER_CS` / `IA32_SYSENTER_ESP` / `IA32_SYSENTER_EIP` | `sysenter` 指令从三环进零环时用的三个寄存器 |
| `IA32_PERF_GLOBAL_CTRL` | 全局的性能监控 MSR |
| `IA32_PAT` | 控制内存页缓存属性的 MSR（Page Attribute Table） |
| `IA32_EFER` | 扩展功能启用寄存器，控制 `syscall` 这类扩展指令是否可用 |

![白皮书列出的 guest 区域 MSR 清单：IA32_DEBUGCTL、IA32_SYSENTER_CS/ESP/EIP、IA32_PERF_GLOBAL_CTRL、IA32_PAT、IA32_EFER，后面还有 BNDCFGS、RTIT_CTL、LBR_CTL、S_CET 等](assets/vCPU%20的状态清单：VMCS%20的%20guest%20区域里到底要填哪些字段/00547.webp)

讲者对 EFER 的解释值得单独记一下：EFER 里的 E 是"扩展"（extend），后面的部分就是"启用"（enable）。比如 64 位下的 `syscall` 指令，从三环进零环时就要用到它，**这个寄存器控制 `syscall` 是否可用**。[【跳转到 05:55】](https://www.bilibili.com/video/BV1X3wbzsEfi/?t=355)

清单后面还有 `IA32_BNDCFGS`、`IA32_RTIT_CTL`、`IA32_LBR_CTL`、`IA32_S_CET` 等，但白皮书对它们都加了"仅当对应的 VM-entry/VM-exit 控制位被置 1 时才支持"这样的条件，本讲直接跳过不填。[【跳转到 06:20】](https://www.bilibili.com/video/BV1X3wbzsEfi/?t=380)

这里有一个对"最小集合"很关键的判断：**MSR 不是越多越好，而是"硬件恢复 guest 时会读的那几个"才必须写**。视频里讲者反复强调，这些 MSR 每一位具体干什么，等真正用到时再讲——现在只需要记住"有哪几个、叫什么"。[【跳转到 04:15】](https://www.bilibili.com/video/BV1X3wbzsEfi/?t=255)

### 2.2 两套编号别搞混

填 MSR 时最容易踩的坑是编号。一行代码里会出现两个编号：

- `vmwrite` 的第一个参数是 **VMCS 字段编号**（encoding），告诉硬件"写到 VMCS 的哪个位置"；
- `read_msr` 的参数是 **MSR 序号**，告诉硬件"读哪个 MSR"。

讲者原话是"这俩东西大家可别搞混了"。[【跳转到 11:47】](https://www.bilibili.com/video/BV1X3wbzsEfi/?t=707)

以 `IA32_DEBUGCTL` 为例：白皮书正文只写了字段名，没给编号；编号要去卷三的附录里查，那里有一张 VMCS encoding 表，分 16 位、64 位、32 位三栏。查到的 `0x2803` 后面标着 "high"，但 64 位下要填的是完整字段，对应编号是 `0x2802`。之所以有 "high" 这一说，是因为 32 位时代一个 64 位字段一次填不进去，只能拆成高低两半分别填。[【跳转到 09:57】](https://www.bilibili.com/video/BV1X3wbzsEfi/?t=597)

![填充代码里 MSR 那一段：vmwrite 写 GUEST_DEBUG_CONTROL，值是 read_msr 读出的 IA32_DEBUGCTL，注释标着 0x2803，往下是 SYSENTER 三个、PERF_GLOBAL_CTRL、PAT、EFER](assets/vCPU%20的状态清单：VMCS%20的%20guest%20区域里到底要填哪些字段/00707.webp)

对应的代码就一行，两个参数分别是 VMCS 字段编号和 MSR 序号：

```c
vmwrite(GUEST_DEBUG_CONTROL, read_msr(IA32_DEBUGCTL));   // 0x2803
```

## 三、非寄存器状态：读不出来的那部分

### 3.1 它们不属于任何寄存器

MSR 填完，白皮书翻到 27.4.2 节：**guest 非寄存器状态**（Guest Non-Register State）。讲者的概括是：前面那些字段都是从某个寄存器读出来再填进去的，**下面这些不一样，它们是 VMCS 自己专属的字段**。[【跳转到 20:10】](https://www.bilibili.com/video/BV1X3wbzsEfi/?t=1210)

这一组一共四项，正好对应"CPU 此刻处于什么状态"这件寄存器表达不了的事。

![白皮书 27.4.2 节：guest 非寄存器状态包括 activity state（0 active / 1 HLT / 2 shutdown / 3 wait-for-SIPI）、interruptibility state、pending debug exceptions](assets/vCPU%20的状态清单：VMCS%20的%20guest%20区域里到底要填哪些字段/01235.webp)

### 3.2 activity state：CPU 现在是"活着"还是"停着"

activity state 用来标识当前逻辑处理器的运行状态，一共四个取值 [【跳转到 20:35】](https://www.bilibili.com/video/BV1X3wbzsEfi/?t=1235)：

- **0 = active**：逻辑处理器正在正常执行指令；
- **1 = HLT**：因为执行了 `hlt` 指令而停止；
- **2 = shutdown**：因为三重故障（triple fault）或其他严重错误而停止；
- **3 = wait-for-SIPI**：在等待 startup IPI。

讲者的提醒是：**初始化时一定要把它设成 0**，因为除了 0 以外都是非正常状态。[【跳转到 21:00】](https://www.bilibili.com/video/BV1X3wbzsEfi/?t=1260)

### 3.3 interruptibility state：中断是开着还是关着

这个字段讲者嫌"中断阻塞状态"这个名字不好懂，建议改叫**开中断/关中断状态**：写代码时为了不被中断干扰会先关中断，写完再开，这个字段记录的就是当前中断是开是关。[【跳转到 22:33】](https://www.bilibili.com/video/BV1X3wbzsEfi/?t=1353)

白皮书里它是一张按位定义的表，四个有效位分别是：被 `STI` 阻塞、被 `MOV SS` 阻塞、被 SMI 阻塞、以及 enclave 中断。[【跳转到 25:50】](https://www.bilibili.com/video/BV1X3wbzsEfi/?t=1550)

![interruptibility state 的位定义表（bit 0 被 STI 阻塞、bit 1 被 MOV SS 阻塞、bit 2 被 SMI 阻塞、bit 4 enclave interruption），以及下面 VMCS link pointer 的说明](assets/vCPU%20的状态清单：VMCS%20的%20guest%20区域里到底要填哪些字段/01575.webp)

### 3.4 pending debug exceptions：异常被"挂起"的那段时间

CPU 触发异常之后，有时候不会立刻投递，而是把异常状态**挂起**（pending），这些待投递的异常就存在这个字段里。[【跳转到 24:14】](https://www.bilibili.com/video/BV1X3wbzsEfi/?t=1454)

这是典型的"只存在于 CPU 内部、任何寄存器都读不出来"的状态。快照如果漏了它，恢复后那个本该被投递的异常就凭空消失了。

### 3.5 VMCS link pointer：没有影子 VMCS 就填全 1

最后一个字段是 VMCS link pointer，白皮书里写的是 shadow VMCS。如果你有影子 VMCS，这个字段要填它的地址；没有的话，白皮书要求软件把它设成全 1，也就是 `0xFFFFFFFF_FFFFFFFF`。[【跳转到 25:50】](https://www.bilibili.com/video/BV1X3wbzsEfi/?t=1550)

讲者的做法是：这是 8 字节 64 位字段，所以直接填一串 F，"说白了就是个 -1"。[【跳转到 26:15】](https://www.bilibili.com/video/BV1X3wbzsEfi/?t=1575)

![填充代码的最后一段：三个非寄存器状态字段都写 0（activity state 注释 Active、interruptibility state 注释 sti、pending debug exceptions）](assets/vCPU%20的状态清单：VMCS%20的%20guest%20区域里到底要填哪些字段/01526.webp)

## 四、这份清单怎么当"快照清单"用

把这一讲填的东西按顺序过一遍，就是一份可以直接抄的状态清单：

```text
寄存器状态
├─ 段寄存器：CS/SS/DS/ES/FS/GS/LDTR/TR
│   ├─ selector（16 位选择子）
│   ├─ base（描述符缓存里的基址）
│   └─ access rights（描述符缓存里的属性位）
├─ 描述符表：GDTR.base/limit、IDTR.base/limit
├─ 控制寄存器：CR0、CR3、CR4
├─ 调试寄存器：DR7
├─ 标志寄存器：RFLAGS
└─ MSR：IA32_DEBUGCTL、IA32_SYSENTER_CS/ESP/EIP、
        IA32_PERF_GLOBAL_CTRL、IA32_PAT、IA32_EFER
非寄存器状态
├─ activity state（0 active / 1 HLT / 2 shutdown / 3 wait-for-SIPI）
├─ interruptibility state（STI / MOV SS / SMI / enclave 中断阻塞位）
├─ pending debug exceptions（挂起待投递的调试异常）
└─ VMCS link pointer（无影子 VMCS 时填全 1）
```

三个判断值得记住：

1. **"隐藏"状态必须显式存**。段寄存器的描述符缓存、pending debug exceptions、interruptibility state，这些东西在普通寄存器里读不到，但它们决定了 CPU 下一步的行为。
2. **MSR 只存白皮书点名的那几个**。清单很长，但带条件的那些（BNDCFGS、RTIT_CTL、LBR_CTL、S_CET）只有在对应的 VM-entry/VM-exit 控制位打开时才需要，默认不填。
3. **有些状态要等"下一节"**。RSP 和 RIP 这一讲没填——不是不重要，而是它们的取值来源（栈和入口地址）要单独讲，这也说明状态清单里的每一项背后都对应一段"从哪儿读"的逻辑。[【跳转到 27:13】](https://www.bilibili.com/video/BV1X3wbzsEfi/?t=1633)

## 小结

- VMCS 的 guest 区域就是硬件视角下的 vCPU 状态清单：VM entry 时硬件读它，VM exit 时硬件写它。
- 段寄存器要存三样：选择子、base、access rights。后两样是描述符缓存，之所以要单独存，是因为它可能与 GDT 里的描述符不一致。
- GDTR/IDTR 只有 base 和 limit 两项，用 `sgdt`/`sidt` 读出来直接填。
- MSR 只填白皮书点名的几个：DEBUGCTL、SYSENTER 三个、PERF_GLOBAL_CTRL、PAT、EFER；带条件的其余 MSR 默认不填。
- 填 MSR 时两套编号要分清：`vmwrite` 用 VMCS 字段编号，`read_msr` 用 MSR 序号；64 位字段用完整 encoding，不用 "high" 那一半。
- 非寄存器状态有四项：activity state、interruptibility state、pending debug exceptions、VMCS link pointer；初始化时前三项填 0，最后一项在无影子 VMCS 时填全 1。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| VMCS | Virtual Machine Control Structure，硬件读写的内存结构，VM entry/exit 时从这里取/存 guest 与 host 状态 |
| guest 区域 | VMCS 里存放 guest（vCPU）状态的那一块，分寄存器状态与非寄存器状态两节 |
| 描述符缓存 | 段寄存器内部缓存的 base/limit/access rights，可能与 GDT 里的描述符不一致，因此要显式保存 |
| access rights | 段属性位：13 位 L、14 位 D/B、15 位 G、16 位 unusable |
| IA32_EFER | 扩展功能启用寄存器，控制 `syscall` 这类扩展指令是否可用 |
| IA32_PAT | Page Attribute Table，控制内存页缓存属性的 MSR |
| activity state | 逻辑处理器当前是 active、HLT、shutdown 还是 wait-for-SIPI |
| interruptibility state | 记录中断是否被 STI / MOV SS / SMI / enclave 中断暂时阻塞 |
| pending debug exceptions | 已识别但尚未投递、被挂起的调试异常 |
| VMCS link pointer | 指向影子 VMCS 的指针；没有影子 VMCS 时软件要把它设成全 1 |