# Type 1 与 Type 2 hypervisor：谁直接跑在硬件上

> 视频来源：[Hypervisors Explained: Type 1 vs Type 2 | Cloud Fundamentals Tutorial](https://www.youtube.com/watch?v=PpfAP6Q3pIs)（YouTube · CodeLucky）｜时长约 4.5 分钟
> 导读：这是一节云基础课里的小讲，用「硬件 → 谁 → 虚拟机」这条层次链把两类 hypervisor 讲清楚，并各给四个特征和四款代表产品。本文按这条链条组织，最后给出一个可复用的判断方法。姊妹篇《KVM 为什么算 Type 1》专门处理 KVM 的归类争议。

## 本讲要解决的核心问题（SCQA）

**背景**：你已经知道虚拟机（virtual machine，VM）是"用软件模拟出来的一台计算机"，一台物理服务器上可以同时跑很多台。让它们不打架的那个中间层，叫 hypervisor。

**冲突**：但 hypervisor 被分成 Type 1 和 Type 2 两类，名字听起来像版本号，实际却不是新旧关系——VirtualBox（Type 2）和 ESXi（Type 1）可以同一年发布、同样流行，却根本不在一个位置上。更麻烦的是，KVM 这种"藏在 Linux 内核里"的东西，看上去既不像 ESXi 那样独占一台机器，又不像 VirtualBox 那样是个普通应用。

**疑问**：Type 1 和 Type 2 的分界线到底画在哪里？凭什么一条线就能决定性能、成本和使用场景？

**回答（中心思想）**：分界线只有一条——**hypervisor 和物理硬件之间，还隔不隔着一个宿主操作系统**。不隔，硬件直接交给 hypervisor，这是 Type 1（裸金属型）；隔着一层宿主 OS，hypervisor 只是那个 OS 上的一个普通应用，这是 Type 2（宿主型）。多出来的这一层 OS，就是 Type 2 性能劣势的全部来源，也是它易用、便宜的全部来源。

![本讲的标题页：Hypervisors，Type 1 vs Type 2](assets/Type%201%20与%20Type%202%20hypervisor：谁直接跑在硬件上/00000.webp)

## 一、hypervisor 是什么：夹在硬件和虚拟机之间的一层软件

hypervisor 是位于**物理硬件和虚拟机之间的一层软件**。它的主要职责是把底层的物理硬件资源抽象出来，在此基础上创建并管理虚拟机。[【跳转到 00:22】](https://www.youtube.com/watch?v=PpfAP6Q3pIs&t=22)

![hypervisor 的定义：对物理硬件资源做抽象，从而创建和管理虚拟机](assets/Type%201%20与%20Type%202%20hypervisor：谁直接跑在硬件上/00022.webp)

一个容易上手的类比是**交通调度员**：同一台物理服务器上同时跑着好几台虚拟机，CPU、内存、存储、网络这些资源是有限的，谁先走、谁走多少、怎么保证互不撞车，由这个调度员来分配。虚拟机自己并不知道"我在和别人抢 CPU"，它以为自己独占一台机器——这正是"抽象"的含义。

这里先记住一个词：**宿主操作系统（host OS）**。它指的是直接装在物理硬件上、你日常开机看到的那个操作系统，比如你笔记本上的 Windows 或 macOS。后面 Type 1 与 Type 2 的全部分歧，都围绕"hypervisor 和它之间是什么关系"展开。

## 二、Type 1：硬件直接交给 hypervisor，中间没有别人

Type 1 hypervisor 也叫**裸金属（bare metal）hypervisor**。它的关键特征是：**直接运行在物理硬件上，下面不需要一个宿主操作系统**。架构是硬件直接到 hypervisor，再到上面的虚拟机。[【跳转到 00:47】](https://www.youtube.com/watch?v=PpfAP6Q3pIs&t=47) [【跳转到 00:52】](https://www.youtube.com/watch?v=PpfAP6Q3pIs&t=52)

![Type 1 的层次链：Hardware → Hypervisor → VMs，中间没有宿主操作系统](assets/Type%201%20与%20Type%202%20hypervisor：谁直接跑在硬件上/00052.webp)

这条链只有三节：**硬件 → hypervisor → 虚拟机**。

"裸金属"这个词容易误解。它不是说"没有软件"，而是说 hypervisor **站到了操作系统原本站的那个位置上**——一台装了 ESXi 的服务器，你开机之后看到的不是 Windows 桌面，而是 ESXi 自己的管理界面；hypervisor 自己承担了"管理这台机器硬件"的职责。所以它既是虚拟化层，也在某种意义上充当了这台机器的操作系统。

正因为中间没有别人，虚拟机对硬件的访问路径最短、额外开销最小，这是 Type 1 性能优势的物理来源。

## 三、Type 1 的四个特征：高性能与企业级，代价是钱和门槛

视频把 Type 1 的特征归纳成四条，两好两坏。[【跳转到 01:15】](https://www.youtube.com/watch?v=PpfAP6Q3pIs&t=75) [【跳转到 01:40】](https://www.youtube.com/watch?v=PpfAP6Q3pIs&t=100)

![Type 1 的四个特征：高性能、企业级、成本更高、部署复杂](assets/Type%201%20与%20Type%202%20hypervisor：谁直接跑在硬件上/00100.webp)

| 特征 | 含义 | 为什么 |
| --- | --- | --- |
| 高性能（High Performance） | 直接访问硬件，额外开销极小 | 层次链里没有宿主 OS 这一跳 |
| 企业级（Enterprise Grade） | 专为数据中心和生产环境设计，可靠性优先 | 目标场景就是"不能停"的服务器 |
| 成本更高（Higher Cost） | 需要专用硬件，往往还有不便宜的授权费 | 一台机器被 hypervisor 独占，不能兼作他用 |
| 部署复杂（Complex Setup） | 需要专业知识才能正确配置和维护 | 装完就没有桌面环境了，排障靠另一套工具 |

这四条不是并列的四个优点，而是**两组因果**：前两条来自"少一层"，后两条也来自"少一层"。少了宿主 OS，性能上去了；但也正因为少了宿主 OS，这台机器不能再当普通电脑用，你得为它专门准备硬件、专门学一套管理方式，厂商也就可以收授权费。**Type 1 的所有好处和所有代价，都是同一个架构决定的。**

## 四、Type 1 的代表产品，以及 KVM 为什么出现在这张名单里

视频列了四款常见的 Type 1 hypervisor。[【跳转到 01:50】](https://www.youtube.com/watch?v=PpfAP6Q3pIs&t=110) [【跳转到 01:55】](https://www.youtube.com/watch?v=PpfAP6Q3pIs&t=115)

![四款常见 Type 1 hypervisor：VMware ESXi、Microsoft Hyper-V、Citrix Hypervisor、KVM](assets/Type%201%20与%20Type%202%20hypervisor：谁直接跑在硬件上/00140.webp)

- **VMware ESXi**（VMware）：使用最广的企业级 hypervisor 之一。
- **Microsoft Hyper-V**（Microsoft）：微软的裸金属方案，常见于 Windows 环境。
- **Citrix Hypervisor**（Citrix，原名 XenServer）：另一个企业级选项。
- **KVM**（Linux Kernel）：全称 kernel-based virtual machine，一个**内建于 Linux 内核**的开源 hypervisor，在云平台上被广泛使用。

前三个都好理解：它们是独立产品，装上去就占据了硬件。**KVM 是这张名单里唯一一个"看起来不像独立产品"的**——它没有独立的安装介质，它就是 Linux 内核的一部分。它凭什么和 ESXi 并列？

答案还是那条分界线：判断标准不是"hypervisor 是不是一个独立产品"，而是"hypervisor 和硬件之间有没有隔着一个宿主 OS"。KVM 的代码跑在**内核态**，它直接操作 CPU 的虚拟化能力和内存，中间并没有"另一个操作系统"挡着——Linux 内核自己就是那个直接管硬件的层，只是它顺便学会了当 hypervisor。所以它被归入 Type 1，通常被称为 Type 1 的"内核内嵌"变体。

这条线索值得单独展开，本文不在这里下结论，见姊妹篇《KVM 为什么算 Type 1：内核自身变成 hypervisor》。

## 五、Type 2：多出来的那一层宿主操作系统

Type 2 hypervisor 走的是另一条路。它们被称为**宿主型（hosted）hypervisor**，因为它们**运行在一个已有的操作系统之上，就像任何一个普通应用一样**。架构多了一层：硬件，然后是宿主操作系统，然后是 hypervisor，最后是虚拟机。[【跳转到 02:27】](https://www.youtube.com/watch?v=PpfAP6Q3pIs&t=147)

![Type 2 的层次链：Hardware → Host OS → Hypervisor → VMs，比 Type 1 多出宿主 OS 这一层](assets/Type%201%20与%20Type%202%20hypervisor：谁直接跑在硬件上/00147.webp)

这条链有四节：**硬件 → 宿主 OS → hypervisor → 虚拟机**。

和 Type 1 对比着看，差别一目了然：

```text
Type 1（裸金属）        Type 2（宿主型）
┌──────────────┐        ┌──────────────┐
│    虚拟机     │        │    虚拟机     │
├──────────────┤        ├──────────────┤
│  hypervisor  │        │  hypervisor  │   ← 这里只是一个普通进程
├──────────────┤        ├──────────────┤
│              │        │   宿主 OS     │   ← Type 1 没有这一层
│    硬件       │        ├──────────────┤
│              │        │    硬件       │
└──────────────┘        └──────────────┘
```

关键在于：多出来的这一层意味着 **Type 2 hypervisor 没有 Type 1 那样直接的硬件访问能力**。虚拟机的一次磁盘读写，在 Type 1 里是"hypervisor 直接处理"，在 Type 2 里则要穿过 hypervisor、穿过宿主 OS 的文件系统、再由宿主 OS 的驱动落到硬件上。每一跳都是开销。

## 六、Type 2 的四个特征：易用与便宜，代价是性能

Type 2 的特征同样是四条，也同样是两好两坏，但方向和 Type 1 正好相反。[【跳转到 02:52】](https://www.youtube.com/watch?v=PpfAP6Q3pIs&t=172) [【跳转到 02:57】](https://www.youtube.com/watch?v=PpfAP6Q3pIs&t=177) [【跳转到 03:22】](https://www.youtube.com/watch?v=PpfAP6Q3pIs&t=202)

![Type 2 的四个特征：易用、适合开发、性能较低、成本友好](assets/Type%201%20与%20Type%202%20hypervisor：谁直接跑在硬件上/00202.webp)

| 特征 | 含义 | 为什么 |
| --- | --- | --- |
| 易用（User Friendly） | 在桌面系统上安装配置简单，不需要专门培训 | 它就是一个普通应用，双击安装即可 |
| 适合开发（Development Use） | 适合测试环境和个人项目，能快速起虚拟机 | 你的笔记本本来就是工作机，不用另买服务器 |
| 性能较低（Lower Performance） | 多出的操作系统层增加开销、降低效率 | 每一次硬件访问都要多穿一层 |
| 成本友好（Cost Effective） | 有大量优秀的免费选项，个人甚至部分商业可用 | 不需要专用硬件，也不用独占一台机器 |

把两张表并排放，会发现它们几乎是**镜像关系**：

- Type 1 用"专用硬件 + 授权费 + 学习成本"换"性能和可靠性"；
- Type 2 用"性能"换"零门槛和零成本"。

这不是巧合，而是同一个架构差异在四个维度上的投影。所以选型时不该问"哪个更好"，而该问"我这台机器是拿来当服务器的，还是拿来当工作机的"。

## 七、Type 2 的代表产品：桌面上的那几款

视频列了四款最常见的 Type 2 hypervisor。[【跳转到 03:32】](https://www.youtube.com/watch?v=PpfAP6Q3pIs&t=212) [【跳转到 03:37】](https://www.youtube.com/watch?v=PpfAP6Q3pIs&t=217)

![四款常见 Type 2 hypervisor：VMware Workstation、Oracle VirtualBox、Parallels Desktop、VMware Fusion](assets/Type%201%20与%20Type%202%20hypervisor：谁直接跑在硬件上/00242.webp)

- **VMware Workstation**（VMware）：面向 Windows 和 Linux 的专业级宿主型 hypervisor。
- **Oracle VirtualBox**（Oracle）：免费开源，在开发者和学生中极受欢迎。
- **Parallels Desktop**（Parallels）：专门为在 Mac 上运行 Windows 而设计。
- **VMware Fusion**（VMware）：给需要在 macOS 旁边跑其他操作系统的 Mac 用户的方案。

这四款有一个共同点：**它们都假设你已经有一台能正常使用的电脑**。你不需要为它们准备一台空机器，装完照常用你的桌面、浏览器、编辑器，虚拟机只是多开的一个窗口。这正是"宿主型"三个字的日常含义。

也正因为如此，这些工具让任何有一台普通电脑的人都能用上虚拟化 [【跳转到 04:02】](https://www.youtube.com/watch?v=PpfAP6Q3pIs&t=242)——学习者第一次接触虚拟化，几乎都是从 VirtualBox 或 Workstation 开始的。

## 八、一个可复用的判断方法：问 hypervisor 站在哪一节

学完两类之后，遇到一个没见过的 hypervisor，怎么判断它属于哪一类？视频给出的层次链其实就是一个判定流程：

1. **找到 hypervisor 在层次链里的位置**。它下面是"硬件"还是"某个操作系统"？
2. **如果它下面直接是硬件**，它就是 Type 1。此时它自己承担了管理硬件的职责，装完之后这台机器不再有日常意义上的桌面操作系统。
3. **如果它下面是一个完整操作系统**，它就是 Type 2。此时它是一个普通应用，可以被安装、卸载、和浏览器同时运行。
4. **如果它既在操作系统"里面"、又直接管硬件**，说明遇到了 KVM 这类内核内嵌形态——它站在内核里，所以按"与硬件之间没有隔着宿主 OS"这一条归入 Type 1。

第 4 条是这条分界线上唯一的模糊地带，也是下一篇文章的全部内容。

## 小结

- **分界线只有一条**：hypervisor 与物理硬件之间，还隔不隔着一个宿主操作系统。不隔是 Type 1（裸金属），隔着是 Type 2（宿主型）。
- **两条层次链**：Type 1 是 `硬件 → hypervisor → 虚拟机`；Type 2 是 `硬件 → 宿主 OS → hypervisor → 虚拟机`。
- **Type 1 的四特征**：高性能、企业级（优点）；成本高、部署复杂（代价）。四条都由"少一层"推出。
- **Type 2 的四特征**：易用、适合开发（优点）；性能较低、成本友好（一坏一好）。四条都由"多一层"推出。
- **两类是镜像关系**：Type 1 用专用硬件和授权费换性能与可靠性，Type 2 用性能换零门槛和零成本。
- **代表产品**：Type 1 有 ESXi、Hyper-V、Citrix Hypervisor、KVM；Type 2 有 Workstation、VirtualBox、Parallels Desktop、Fusion。
- **判断方法**：看 hypervisor 站在层次链的哪一节——它下面直接是硬件还是宿主 OS。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| hypervisor | 位于物理硬件与虚拟机之间的软件层，负责抽象硬件资源、创建并管理虚拟机 |
| 虚拟机（VM） | 由 hypervisor 模拟出来的一台"计算机"，有自己的 CPU、内存、磁盘和操作系统 |
| 宿主操作系统（host OS） | 直接装在物理硬件上、用户日常使用的那个操作系统，如 Windows、macOS |
| Type 1 / 裸金属型 | 直接运行在物理硬件上、下面没有宿主操作系统的 hypervisor |
| Type 2 / 宿主型 | 作为普通应用运行在已有操作系统之上的 hypervisor |
| Bare metal | "裸金属"，指 hypervisor 直接占据硬件、取代了原本操作系统的位置 |
| 客户操作系统（guest OS） | 跑在虚拟机内部的那个操作系统，与宿主 OS 相互独立 |
| 开销（overhead） | 虚拟化层为了模拟硬件而额外消耗的性能，层次越多开销越大 |