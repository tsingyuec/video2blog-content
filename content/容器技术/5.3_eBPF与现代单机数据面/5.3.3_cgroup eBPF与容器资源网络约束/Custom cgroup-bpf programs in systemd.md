# Custom cgroup-bpf programs in systemd

> 本文整理自 All Systems Go! 2019 大会上 Julia Kartseva（Facebook 容器团队，负责网络方向）的演讲《Custom cgroup-bpf programs in systemd》。它讲明白了一件很具体的事：**systemd 里现在也用 BPF 做防火墙和设备的访问控制，但写这些程序只能手写 BPF 微汇编、还得靠「照抄」内核代码**；演讲给出了用 libbpf 把它改造成「用户可自定义、可加载、可编译」的目标与里程碑路线。

![演讲标题页：Custom cgroup-BPF programs in systemd（Julia Kartseva，All Systems Go! 2019，柏林）](<assets/Custom cgroup-bpf programs in systemd/00005.webp>)

## 本讲要解决的核心问题（SCQA）

**背景**：BPF 是一种让用户态能安全地修改内核行为的技术，在网络和追踪领域大放异彩。systemd 也早已把 BPF 用了起来，用来实现 **BPF firewall**（按 IP 放行/拉黑）和 **device control**（限制进程能访问哪些设备）。

**冲突**：systemd 里的 BPF 基础设施几乎是「凝固」的——它只服务于最初那两个用例，代码是**从内核 UAPI 和 libbpf 辅助函数里照抄一份**之后就再没动过；而且写这些 BPF 程序时，**只能用 BPF 微汇编手写**，既难维护、也难读。

**疑问**：能不能让**用户自己定义、加载并挂载自定义的 cgroup BPF 程序**，把它挂到各种 hook 点上，而 systemd 的开发者又**不必为了维护这套 BPF 基础设施、去硬啃 BPF 指令集**？

**回答（中心思想）**：能，路线是**引入 libbpf 作为用户态封装**：用一条 **Meson 构建规则**把受限 C 程序编译成**字节码缓冲区**，运行时由 libbpf 直接从缓冲区加载。这样既摆脱了手写微汇编、又能做到**「一次编译、到处运行」且没有 LLVM 运行时依赖**——生产机器上可以直接发已编译好的二进制，不必装 LLVM。

[【跳转到 00:00】](https://www.youtube.com/watch?v=_U37CMiDFVs&t=0)

> 演讲人开场先做了两次举手调研：了解「BPF 是什么」的人不少，但了解「BPF 与 systemd 结合」的只有大约三成。演讲也因此分成两部分：先简要介绍 BPF，再重点讲 systemd 里的 BPF。
>
> [【跳转到 00:18】](https://www.youtube.com/watch?v=_U37CMiDFVs&t=18) / [【跳转到 00:43】](https://www.youtube.com/watch?v=_U37CMiDFVs&t=43)

![演讲 Agenda：1) BPF 简介 2) systemd 中 BPF 的现状 3) 本工作的目标与里程碑 4) libbpf：动机与限制](<assets/Custom cgroup-bpf programs in systemd/00018.webp>)

---

## 一、BPF 是什么：一套受约束的「内核内虚拟机」

[【跳转到 01:33】](https://www.youtube.com/watch?v=_U37CMiDFVs&t=93)

**一句话结论：BPF 是一种类似虚拟机的技术，目的是让用户态能够安全地修改内核行为。**

它的三个关键是：

1. **结合两种思路**：把内核态与用户态两种做法结合了起来；
2. **「安全」有明确含义**：用户注入内核的代码，**有保证不会让内核崩溃、卡死，也不会去访问一些非法（越界）的内存地址**；
3. **主要应用方向**：网络（networking）与追踪（tracing）。

[【跳转到 01:38】](https://www.youtube.com/watch?v=_U37CMiDFVs&t=98)

![BPF overview 幻灯片：一种用来从用户态安全地修改内核行为的技术](<assets/Custom cgroup-bpf programs in systemd/00098.webp>)

### 1.1 一个 BPF 程序的「生命周期」

[【跳转到 02:28】](https://www.youtube.com/watch?v=_U37CMiDFVs&t=148)

要让程序真正跑起来，需要按顺序做这几件事：

1. **编译**（compile）；
2. **加载进内核**（load to kernel）；
3. **挂到某个 hook 点**（attach to a hook point）；
4. 不需要时**卸载**（detach）；
5. 一旦**没有任何地方再引用**这个程序，内核就会把它卸载。

**所以「引用计数（refcount）」是一切的要害：只要还有引用，程序就一直是活的。**

![BPF 程序生命周期：0. 编译 → 1. 加载进内核（refcount=1）→ 2. 挂到 hook 点 → …](<assets/Custom cgroup-bpf programs in systemd/00173.webp>)

### 1.2 用户态 ↔ 内核态：字节码是怎么进去的

[【跳转到 03:18】](https://www.youtube.com/watch?v=_U37CMiDFVs&t=198)

假设你有一个 C 程序想加载进内核，步骤如下：

1. **编译成 BPF 指令集**。这是一种类似汇编的语言，它**借鉴了几种不同架构的指令集**；这一步要用 **Clang / LLVM** 完成。
2. **把字节码加载进内核**。而就在这里，「整个 BPF 系统里最精妙的部分」登场了——
3. **验证器（verifier）**：你的程序需要经过校验，确认它确实可以安全地加载。
4. **JIT 编译器**：校验器完成工作后，JIT 会**针对当前平台**把程序翻译成机器码；如果平台不被支持也没关系，还有**解释器**可以运行程序。
5. 程序加载后会被**分配一个文件描述符**，并且**引用计数大于零**——呼应前面那句：只要有引用，程序就处于加载状态。

![BPF 程序加载流程：用户态用 clang/LLVM 生成指令，进入内核后经 verifier 校验、JIT 编译](<assets/Custom cgroup-bpf programs in systemd/00223.webp>)

---

## 二、systemd 里 BPF 的现状：只有两个用例，而且「凝固」了

[【跳转到 05:23】](https://www.youtube.com/watch?v=_U37CMiDFVs&t=323)

systemd 里目前有**两个子系统**在用 BPF：

| 子系统 | 能做什么 |
| --- | --- |
| **BPF firewall** | 把一些 IP 地址加入白名单/黑名单（想全加进去也行） |
| **device control** | 指定允许哪些设备访问，例如把设备设成只读、定义各种策略等 |

[【跳转到 05:29】](https://www.youtube.com/watch?v=_U37CMiDFVs&t=329)

### 2.1 问题在哪：为两个用例量身定制，然后「冻」住了

[【跳转到 05:54】](https://www.youtube.com/watch?v=_U37CMiDFVs&t=354)

现有的这套基础设施，是专门为上面两个用例打造的，**基本上就停在那个时间点没再动过**。原因很直白：**这段代码当初是从内核的 UAPI 和 libbpf 的辅助函数里搬过来的，照抄了一份之后就一直在那儿没变。**

### 2.2 唯一的写法：手写 BPF 微汇编

[【跳转到 06:19】](https://www.youtube.com/watch?v=_U37CMiDFVs&t=379)

在 systemd 里，目前**很不幸只能用 BPF 微汇编写 BPF 程序**。不过这倒是个了解 BPF 技术的好途径，比如你会学到：

- **BPF 指令集有十一个寄存器**；
- 但这样写**既不好维护、也不好读**——演讲人坦言，自己第一次看这段代码时，**特别感谢那位留下注释的人**（注释解释了那些寄存器其实是在当计数器用）。

![systemd 中 BPF 程序的现状：一段手写的 BPF 微汇编（bpf_insn 指令序列）](<assets/Custom cgroup-bpf programs in systemd/00329.webp>)

### 2.3 已经有的少量自定义支持，以及它的天花板

[【跳转到 07:59】](https://www.youtube.com/watch?v=_U37CMiDFVs&t=479)

现在已经有了一些自定义 BPF 支持（是为某个用例加的）：**你可以指定一个路径，把程序 pin 到 BPF 文件系统（bpffs）上**。所谓 pinned，意思就是它**已经加载、并且有合法的文件描述符**。

但天花板也很明显：

- **只支持一种 BPF 程序类型**；
- **只能挂到 egress 或 ingress 这两类 hook 上**。

[【跳转到 08:24】](https://www.youtube.com/watch?v=_U37CMiDFVs&t=504)

systemd 里 BPF 的另一个重要部分是 **flows（流）**：现在这套方案对多流的支持还有个**「全有或全无」（all or none）的锁**。另外，能**覆盖（override）BPF 程序**也是一件很酷的事。

---

## 三、目标与里程碑：从「能挂载」走到「能编译」

[【跳转到 09:00】](https://www.youtube.com/watch?v=_U37CMiDFVs&t=540)

### 3.1 三个目标

1. **让用户能定义、加载并挂载自定义的 cgroup BPF 程序**，并把这些程序挂到**各种不同的 hook 点**上；
2. **过程要简单、方便**（从用户侧看）；
3. **systemd 开发者不必为维护 BPF 基础设施头疼**——你不用真的深入去啃 BPF 指令集才能搞懂到底发生了什么。同时还要记住那段**照抄来的代码**，希望**新特性开箱即用**。

![systemd 中 BPF 的目标：改善用户体验、让自定义 BPF 程序易于引入与维护](<assets/Custom cgroup-bpf programs in systemd/00540.webp>)

### 3.2 里程碑：用「生命周期」当刻度

[【跳转到 09:59】](https://www.youtube.com/watch?v=_U37CMiDFVs&t=599)

还记得那张讲生命周期的幻灯片吧——**编译、加载、挂载**。用这三个动作当刻度：

- **目前处于里程碑 #1：能挂载（attach）程序**；
- **一个正在等 review 的 pull request** 把 BPF firewall 扩展到其它 BPF 挂载类型和 flows 上，它会**完成里程碑 #3**。

![里程碑幻灯片：Milestone #0（过去）已有 BPF 指令与有限的 BPF 程序支持，后续里程碑逐步推进](<assets/Custom cgroup-bpf programs in systemd/00599.webp>)

[【跳转到 10:49】](https://www.youtube.com/watch?v=_U37CMiDFVs&t=649)

但我们想要的不止这些：**不只要程序能被挂载，还要它既能被加载、也能被编译**。要做到这一点，就得让 systemd 能接收**对象文件、字节码，或者用受限 C 语言写的程序**。

**这是个崇高的目标，但没那么简单**：还记得那个「照抄」的问题吧——它可能会拖累**后面整整三个里程碑**。所以这里需要 **libbpf** 的帮助。

---

## 四、libbpf：动机、限制与进一步工作

### 4.1 为什么要 libbpf

[【跳转到 11:14】](https://www.youtube.com/watch?v=_U37CMiDFVs&t=674)

**libbpf 是一个用户态库，可以把它理解成对内核 BPF 系统调用的一层封装**——它替你把这些「脏活累活」都干了。演讲人特别感兴趣的是它的几个 **wrapper（包装接口）**，比如：

- 从**缓冲区**加载字节码；
- 或从**路径**加载字节码。

[【跳转到 12:01】](https://www.youtube.com/watch?v=_U37CMiDFVs&t=721)

另一个背景是 **BPF 在内核里是热门话题**，比如有个叫 **CO-RE** 的倡议，目标是 **「compile once, run everywhere（一次编译、到处运行）」**。你要做的是在**你自己平台上编译程序**，libbpf 会提供一定保证，让你的程序也能**加载到其它内核上**；而这个倡议的**基石就是 BTF**。

![libbpf 的动机：以统一的方式、带着前置检查与错误处理来执行系统调用](<assets/Custom cgroup-bpf programs in systemd/00696.webp>)

[【跳转到 12:51】](https://www.youtube.com/watch?v=_U37CMiDFVs&t=771)

> **名词解释**：**BTF = BPF Type Format（BPF 类型格式）**，它是「一次编译、到处运行」得以实现的关键——有了类型信息，程序在其它内核上重定位字段偏移才有依据。

### 4.2 为什么现在还没用上它：两大限制

[【跳转到 13:16】](https://www.youtube.com/watch?v=_U37CMiDFVs&t=796)

**限制一：缺少打包。** 目前 libbpf 的打包工作正在进行中，**第一次尝试是以 git submodule 的形式做的**。所以本质上只有两个选择：

- **照抄一份**（copy-paste），或者
- **用 submodule**（更好一些）。

但 **systemd 有一套相当复杂的测试**，submodule 方案**行不通**——因为我们**不得不去改测试**。那只是个权宜之计、周期太长，所以**用打好的包才是更好的做法**。

![libbpf 当前的限制：git submodule（PR12151）暴露出可测试性方面的担忧](<assets/Custom cgroup-bpf programs in systemd/00796.webp>)

[【跳转到 14:06】](https://www.youtube.com/watch?v=_U37CMiDFVs&t=846)

**限制二：libbpf 本身测试得不够充分。** 至少这个 submodule 方案暴露了问题：那个 pull request 做的第一件事就是**在某些测试上崩了**——他们做了一些 **sanitizer 测试**，我们需要**上游补丁**来修，这证明**确实存在问题**。

### 4.3 怎么解决「可测试性」：QEMU + 移植内核自测 + 镜像源打包

[【跳转到 14:31】](https://www.youtube.com/watch?v=_U37CMiDFVs&t=871)

要保证可测试，就得验证 **libbpf 与不同内核的兼容性**，**向后兼容是重中之重**。因为内核开发者发布一个新特性时，只会在**对应内核**上跑自测，这还不够——它**未必能兼容所有内核**。

对策有三条：

1. **用 QEMU**（一种虚拟化设施）针对**多个内核**测试 libbpf；
2. 把一些**内核自测移植**进 systemd 自己的测试基础设施；
3. **打包改为从镜像源**：目前至少 Debian 和 Fedora 都有包，但它们是**直接从内核源码构建**的；如果要做测试，希望它们**从镜像源构建**。

![libbpf 进一步工作：用 QEMU 测试与旧内核的向后兼容性，并移植内核自测](<assets/Custom cgroup-bpf programs in systemd/00896.webp>)

---

## 五、字节码 vs 受限 C：如何做到「无运行时依赖」

[【跳转到 16:11】](https://www.youtube.com/watch?v=_U37CMiDFVs&t=971)

**这一节回应的是 pull request 里有人提出的担忧**：我们不想要一个 **LLVM 的运行时依赖**。于是有人主张：**干脆不要编译 C 程序，只存字节码好了。**

**先给结论：字节码确实比「把 BPF 程序挂到 bpffs 上」要好，但它带来一个新的麻烦——你得存三份东西而不是一份。**

- 你既要存 **C 程序本身**，又要存**字节码**，而且**大端、小端都要存**；
- 还得让它们**保持同步**。

**关键是：你根本不需要这么做。** 因为这里**没有编译时依赖问题、也没有运行时依赖**——**只有编译时依赖**（跟上游走即可）。而在 **CO-RE「一次编译、到处运行」** 的倡议下，会有一定保证：**你编译出来的代码能在其它内核上运行**。

[【跳转到 17:51】](https://www.youtube.com/watch?v=_U37CMiDFVs&t=1071)

另外两个好消息：**BPF 支持最近刚被加入 GCC**（非常棒）；虽然不是说马上就能上手，LLVM 那边可能还要再放一阵子，但值得记在心里。

![bytecode vs restricted C source：字节码需手工由 C 程序构建、并在仓库中同时存大端与小端](<assets/Custom cgroup-bpf programs in systemd/00971.webp>)

### 5.1 实现细节：一条 Meson 规则搞定

[【跳转到 18:16】](https://www.youtube.com/watch?v=_U37CMiDFVs&t=1096)

实现上非常简单：

- 写一条 **Meson 构建规则**，这条规则把 **C 代码编译进一个 C 字符串缓冲区**；
- 再用 **libbpf 直接从缓冲区里读出字节码**。

这就是**第四个里程碑**：**systemd 里能存放 libbpf 程序**。

### 5.2 现场问答：受限编译器、表 vs 生成代码、重写计划

[【跳转到 19:26】](https://www.youtube.com/watch?v=_U37CMiDFVs&t=1166)

**问题一：政府客户不希望系统上有任何类型的编译器，我们离「受限 C 编译器」有多近？**

回答：**你不需要在运行时编译，只需要编译一次**。编译一次之后，程序会被翻译成 LLVM……你的 **Meson 构建规则把 Clang 的输出转储成一个流**，之后就能**直接从那个流里加载程序**。

[【跳转到 20:09】](https://www.youtube.com/watch?v=_U37CMiDFVs&t=1209)

也就是说：**只需要一条构建规则，就可以把已有的二进制文件发到生产机器上，而那些机器上不用装 LLVM——所以没有运行时依赖。**

当然，**如果你要做 tracing，那确实需要运行时依赖**；但对**主要是网络的 systemd 用例**来说就不需要。不过这仍然需要 **libbpf 的支持**，所以要等那些 pull request 先被批准。

[【跳转到 21:03】](https://www.youtube.com/watch?v=_U37CMiDFVs&t=1263)

**问题二：现有两个 BPF 程序中，firewall 把 IP 存表里所以好预编译；但 devices 那部分是把策略直接生成进代码，怎么办？**

- 提问者的观察：firewall 的所有实际 IP 地址都存在 BPF 表里，所以**用它来配 LLVM 构建会很容易**——BPF 代码到处都一样，可以预编译；
- 但 **devices 那部分目前的实现是「生成结构体」**：它是针对**实际要执行的策略**而定制的——它查设备节点的 **major/minor 号**时**不是查外部表，而是直接生成到代码里**。

回答的**策略是：用 BPF maps**——**凡是需要从用户态提供的数据，都用 map（比如哈希表）**。

[【跳转到 22:25】](https://www.youtube.com/watch?v=_U37CMiDFVs&t=1345)

**问题三：那你会做这项工作吗？**

回答：**会**。没有严格的截止日期，但目标是**摆脱 BPF 微汇编**，**重写 firewall 和 devices** 那两部分。（现场回应：「那太好了，很期待。」）

![参考资料：BPF 对象生命周期与 BPF/XDP 参考指南等](<assets/Custom cgroup-bpf programs in systemd/01156.webp>)

---

## 小结

- **BPF 是什么**：一种类似虚拟机的技术，让用户态能**安全地修改内核行为**——「安全」意味着注入的代码不会让内核崩溃/卡死，也不会越界访存；主战场是网络与追踪。
- **程序的生命周期**：编译 → 加载进内核 → 挂到 hook 点 → 卸载；**引用计数（refcount）决定程序存活**。
- **加载链路**：C → Clang/LLVM 编成 BPF 指令集 → verifier 校验 → JIT 编译（否则走解释器）→ 分配 fd。
- **systemd 的现状**：只有 **BPF firewall** 与 **device control** 两个用例，且代码是**从内核 UAPI / libbpf 辅助函数照抄来的**、之后没再动；写程序**只能手写 BPF 微汇编**（11 个寄存器，难读难维护）。
- **目标**：让用户能**定义/加载/挂载自定义 cgroup BPF 程序**并挂到各种 hook 上，同时对用户足够简单、对 systemd 开发者免于维护之苦。
- **里程碑**：以「编译/加载/挂载」为刻度——**当前在「能挂载」**，一个 PR 将补齐挂载类型与 flows。
- **libbpf 的两大拦路虎**：**缺打包**（git submodule 方案因 systemd 的复杂测试而失败）与**测试不足**（PR 在 sanitizer 测试上崩了）；对策是 **QEMU 多内核兼容测试 + 移植内核自测 + 镜像源打包**。
- **字节码 vs 受限 C**：存字节码也不见得省事（要同时存 C 程序与大小端字节码并保持同步）；真正的答案是**只保留编译时依赖、没有运行时依赖**，靠 **CO-RE + BTF** 保证一次编译到处运行。
- **落地方案**：一条 **Meson 规则**把 C 编进字符串缓冲区，libbpf 从缓冲区加载 → **里程碑 #4**；生产机器上**不必装 LLVM**（tracing 场景除外）。
- **后续方向**：用 **BPF maps** 取代「把策略生成进代码」的做法，并**重写 firewall 与 devices**、彻底告别微汇编。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| BPF / eBPF | 一种可让用户态安全修改内核行为的「内核内虚拟机」技术 |
| 引用计数（refcount） | 决定 BPF 对象是否存活；只要有引用，程序就不会被卸载 |
| verifier（验证器） | 加载前对 BPF 程序做静态校验，保证不会崩溃/卡死/越界访存 |
| JIT | 把 BPF 字节码即时翻译成当前平台的原生机器码（不支持时回退解释器） |
| BPF 微汇编 | 直接手写 `bpf_insn` 指令序列的方式，systemd 目前唯一可用的写法 |
| bpffs / pin | BPF 文件系统与「钉住」机制，把程序固定在文件系统上的文件里以保持常驻 |
| flows | systemd BPF 里处理「流」的部分；现方案对多流是「全有或全无」的锁 |
| libbpf | 用户态库，封装 BPF 系统调用（含从缓冲区/路径加载字节码的 wrapper） |
| CO-RE | 「一次编译、到处运行」倡议，让同一份 BPF 程序能跑在多个内核上 |
| BTF | BPF Type Format，CO-RE 的基石，提供内核类型信息用于重定位 |
| restricted C | 受限 C 语言，作为 BPF 程序的输入形态之一（对象文件/字节码之外的一条路） |
| Meson | 构建系统；演讲用它的一条构建规则把 C 编译进字符串缓冲区 |
| BPF map | 内核里的键值数据结构，用于用户态与 BPF 程序共享数据（如 IP 表、设备表） |
