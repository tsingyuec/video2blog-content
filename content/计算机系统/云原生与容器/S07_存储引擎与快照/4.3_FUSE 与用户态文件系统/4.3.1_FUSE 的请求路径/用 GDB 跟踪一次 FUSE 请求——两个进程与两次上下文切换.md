# 用 GDB 跟踪一次 FUSE 请求：两个进程与两次上下文切换

> 视频来源：[用 fuse 读写文件的底层视角](https://www.bilibili.com/video/BV1sj411w7s8/)（Bilibili · 萌萌哒hds · CS 讨论班第二期）｜时长约 37 分钟
>
> 导读：这是一次**动手型**分享。讲者先花十分钟把 FUSE 的三个部件、内核模块、libfuse 回调表讲清楚，然后跑一个 hello world 让你看见「挂载之后两个目录变成一样」，最后开 QEMU + GDB，在一个真实内核里下三个断点，用**两个进程、两个 CPU** 把一次请求的睡眠与唤醒全程走一遍。本文按本小节的题目重排：**跟着断点走，看清一次请求从 VFS 到守护进程再回来的每一步**。想看内核源码层面的剖析，见同小节另一篇《FUSE 请求路径剖析——一次 read 如何穿过 VFS 与 dev-fuse》。

## 本讲要解决的核心问题（SCQA）

**背景**：文件系统向来是内核的活。`open`、`read`、`write`、`unlink` 这些回调由 VFS 分发，实现写在 `fuse.ko` 这种模块里，或者干脆编进内核。

**冲突**：FUSE 把这些回调**搬到了用户态**。于是同一个 `rm` 命令，一半动作发生在 `rm` 进程的内核栈里，另一半动作发生在另一个进程（守护进程）里。只看源码很容易懂，但「到底是谁在等谁、什么时候切换、为什么一个命令会牵扯两个进程」很难靠读代码建立直觉。

**疑问**：一次 `rm`（或一次 `read`）在内核里究竟停在哪一行？谁把谁唤醒？两个进程是不是同时在跑？守护进程凭什么能替用户进程操作那个文件？

**回答（中心思想）**：一次 FUSE 请求是**两个进程的接力**——用户进程在内核里构造请求、挂进队列、然后**睡在自己的请求上**；守护进程平时**睡在 `/dev/fuse` 的 `read` 上**，被唤醒后取走请求、在用户态执行回调、再 `write` 回去；内核按请求号找回等待者并唤醒它。整条链路上有**两次用户态/内核态穿越（往返共四次）**，而两个进程是**并行**跑在不同 CPU 上的。

## 一、三个部件，一句总结

讲者把 FUSE 拆成三部分 [【跳转到 03:00】](https://www.bilibili.com/video/BV1sj411w7s8/?t=180)：

- **内核态**：`fuse.ko`，向用户态暴露的设备文件 `/dev/fuse`；
- **用户态**：`libfuse`，守护进程基于它构建；
- **挂载工具**：`fusermount`，负责把目录挂上去。

![FUSE 简介页：左边是架构三件套（fuse.ko、libfuse、fusermount）与「效率低但灵活」的结论，右边是标准 IO 调用经内核 FUSE 模块转发到 FUSE 文件系统实现的示意图](assets/用%20GDB%20跟踪一次%20FUSE%20请求——两个进程与两次上下文切换/00180.webp)

右上那张小图值得多看两眼：`read/write` 从用户态发出，被内核的 FUSE 模块**打包成请求**，再送到右边的「FUSE 文件系统实现」；实现算完，结果沿原路返回。讲者用一句话概括这条路的性质：**效率低，但灵活**。

### 1.1 「效率低」低在哪

讲者数了切换次数：一个文件系统请求从用户态发出，切换一次进内核，经内核 fs 转发，再到用户态的 daemon，这是两次用户态与内核态的切换；回来时又要经过对称的两次 [【跳转到 03:25】](https://www.bilibili.com/video/BV1sj411w7s8/?t=205)。所以一次请求往返是**四次切换**。

他还放了一个动图来演示：IO 请求从 `read` 系统调用发出 → 内核 → 转发给用户态的 fuse daemon 进程 → daemon 执行完 → 返回内核 fs 模块 → 返回给 `read` 的进程 [【跳转到 03:55】](https://www.bilibili.com/video/BV1sj411w7s8/?t=235)。这条「一去一回」的折线，就是后面 GDB 里要验证的东西。

### 1.2 「灵活」灵在哪

灵活来自**回调**。文件系统有很多自成体系的回调：`open` 一个文件、`read`/`write` 读写、`getattr` 取 metadata……FUSE 框架把这些回调的骨架都实现好了，你只要填 callback 里的具体逻辑 [【跳转到 02:10】](https://www.bilibili.com/video/BV1sj411w7s8/?t=130)。换句话说，FUSE 提供的是**协议 + 脚手架**，语义留给你。

## 二、内核模块与那份被忽略的文档

`fuse.ko` 是一个普通的内核模块：它既可以和内核一起编译（打包在一起，不用单独 `insmod`），也可以编成 `.ko`，这样模块代码更新时可以先卸载再热替换 [【跳转到 04:14】](https://www.bilibili.com/video/BV1sj411w7s8/?t=254)。

讲者花了一点时间推荐**内核文档**，这是本节很实用的一个提示：FUSE 的文档就在内核源码树的 `Documentation/filesystems/fuse.rst` 里，写得非常详细——它是什么、分几个类型、挂载参数、还有一个 control 文件系统（`fusectl`）可以临时把请求 abort 掉 [【跳转到 05:19】](https://www.bilibili.com/video/BV1sj411w7s8/?t=319)。

![内核文档 fuse.rst 页面：Kernel - userspace interface 一节给出的流程图，左边是 rm 进程的 sys_unlink 路径，右边是 fuse daemon 的 sys_read 路径，中间用 sleep on 与 woken up 标注等待与唤醒](assets/用%20GDB%20跟踪一次%20FUSE%20请求——两个进程与两次上下文切换/00697.webp)

这份文档里最值钱的就是这张「一次 unlink 的完整流程」图。讲者说文档里给了一个文件系统操作的例子——通过 `rm` 指令下发删除，然后这个指令如何通过 fuse daemon 流转、最后完成删除——他后面会拿它当剧本，一条一条在 GDB 里对上 [【跳转到 06:09】](https://www.bilibili.com/video/BV1sj411w7s8/?t=369)。

## 三、用户态库：回调表就是协议的另一半

用户态最典型的库是 libfuse，C 实现，讲时版本已经到 3.14；此外还有 Go 的 fuse 库，也能实现运行在用户态的 fuse daemon [【跳转到 06:53】](https://www.bilibili.com/video/BV1sj411w7s8/?t=413)。

![FUSE 用户态库页：libfuse 的 GitHub 仓库与 About 说明（内核模块 + 用户态库两个组成部分、high-level 与 low-level 两套 API），右侧是请求类型分组表](assets/用%20GDB%20跟踪一次%20FUSE%20请求——两个进程与两次上下文切换/00470.webp)

这些用户态库的共同特点，讲者总结为一句：**基于 `/dev/fuse` 这个内核 fuse 模块暴露的设备接口，去封装文件系统的操作**，再提供给上层实现各种回调，以 `open`、`read`、`write`、`unlink` 为代表 [【跳转到 07:50】](https://www.bilibili.com/video/BV1sj411w7s8/?t=470)。

右边的表把回调按请求类型分了组，值得记的是这几组：

- **Data (2)**：只有 `READ`、`WRITE`——真正搬数据的就这两个；
- **Metadata (14)**：`LOOKUP`、`FORGET`、`BATCH_FORGET`、`CREATE`、`UNLINK`、`LINK`、`RENAME`、`OPEN`、`RELEASE`、`STATFS`、`FSYNC`、`FLUSH`、`ACCESS`——名字几乎和 POSIX 一一对应；
- **Directory (7)**：`MKDIR`、`RMDIR`、`OPENDIR`、`READDIR`、`READDIRPLUS`、`FSYNCDIR` 等；
- **Special (3)**：`INIT`、`DESTROY`、`INTERRUPT`。

这张表同时解释了「为什么 FUSE 的元数据操作特别多」：14 种元数据请求对 2 种数据请求，一个 `ls -l` 就要发一大串。

## 四、先跑起来：hello world 的两次实验

讲者用的例子是 libfuse 自带的 `passthrough_hp`（high performance passthrough）。选它的理由是「比较好理解」：比如 `unlink` 这个回调，在代码里组织成一个 `sfs_unlink` 函数，里面有 debug 日志，最后调用真正的文件系统 `unlink`——而这个 `sfs_unlink` 正是留给用户自己实现的 [【跳转到 09:01】](https://www.bilibili.com/video/BV1sj411w7s8/?t=541)。

### 4.1 实验一：挂载

准备两个目录：`mnt`（原始目录，里面有 `a.txt`）和 `temp`（待挂载 FUSE 的空目录）。执行 `passthrough_hp ./mnt ./temp` 之后再看，`temp` 里出现了 `a.txt` [【跳转到 10:30】](https://www.bilibili.com/video/BV1sj411w7s8/?t=630)。

![hello world 实验一：挂载前 mnt 下有 a.txt、temp 为空；执行 passthrough_hp ./mnt ./temp 后，temp 下也出现了 a.txt](assets/用%20GDB%20跟踪一次%20FUSE%20请求——两个进程与两次上下文切换/00630.webp)

这一步对应流程图里的**第一步**，讲者强调 FUSE 的流程是**有顺序的**：在用户下发文件系统命令之前，**fuse daemon 必须先就位** [【跳转到 11:06】](https://www.bilibili.com/video/BV1sj411w7s8/?t=666)。

「就位」的具体动作是：daemon 去 `read(/dev/fuse)`，然后**在那里休眠**，直到有文件系统请求下来；请求到了，它就从请求链表上一个一个把请求捞出来执行，执行完把结果通知回去 [【跳转到 11:37】](https://www.bilibili.com/video/BV1sj411w7s8/?t=697)。这句话是后面所有 GDB 断点的解释基础——**daemon 平时不是「在跑」，而是「在睡」**。

### 4.2 实验二：写文件，看回调落到哪

接着往 `temp` 里写一个文件：`echo "abc" > ./temp/b.txt`。结果不光 `temp` 里有 `b.txt`，**`mnt` 里也出现了 `b.txt`** [【跳转到 12:19】](https://www.bilibili.com/video/BV1sj411w7s8/?t=739)。

![hello world 实验二：往 temp 目录写入 b.txt 后，mnt 目录里也出现了 b.txt，说明 passthrough 的回调把写操作落到了原始目录](assets/用%20GDB%20跟踪一次%20FUSE%20请求——两个进程与两次上下文切换/00764.webp)

这就是 passthrough 类实现的语义：**回调的内容就是「往挂载前的那个目录再写一次」**。讲者用这个实验说明回调的落点——你写的是 `temp`，但真正干活的代码操作的是 `mnt` [【跳转到 13:09】](https://www.bilibili.com/video/BV1sj411w7s8/?t=789)。对理解 FUSE 很有用：**挂载点只是一个入口，语义完全由回调决定**。

## 五、动手跟踪：一次 rm 的两个进程

### 5.1 实验环境与三个断点

讲者用 QEMU 起一个带简单 root 文件系统的 Linux 内核，用 GDB 连上去，在实验目录里挂载一个加了大量 debug 日志、**单线程模式**的 FUSE 文件系统（单线程是为了看得更清楚）[【跳转到 17:00】](https://www.bilibili.com/video/BV1sj411w7s8/?t=1020)。

这些 debug 日志是后面读图的钥匙：daemon 每处理一条请求就打一行，里面有 `unique` 号和 `opcode`。从日志里能直接看到 `FUSE_INIT`、`FUSE_GETATTR`、`FUSE_LOOKUP`、`FUSE_RELEASE` 这类请求依次流过，`LOOKUP` 那几行还带着 `name=a.txt`、`parent=1` 这样的参数 [【跳转到 18:12】](https://www.bilibili.com/video/BV1sj411w7s8/?t=1092)。

![VS Code 左侧是 fuse 内核源码，下方是 daemon 打印的请求日志：每行一个 unique 号与 opcode，依次出现 FUSE_INIT、GETATTR、LOOKUP、RELEASE；右侧终端里是挂载前后的目录对比](assets/用%20GDB%20跟踪一次%20FUSE%20请求——两个进程与两次上下文切换/01092.webp)

跟踪的对象是 `rm temp/a.txt`。讲者先给出**核心思想**：这条链路上有**两个进程**——
- **rm 进程**：用户敲命令的那个进程，对应流程图**左半部分**，是所有用户进程会发生的调用流程；
- **fuse daemon 进程**：对应流程图**右半部分**。

![QEMU + GDB 调试 FUSE 内核驱动：以 rm 操作为例，核心思想是两个进程——rm 进程与 FUSE daemon 进程，右侧是内核文档给出的完整流程图](assets/用%20GDB%20跟踪一次%20FUSE%20请求——两个进程与两次上下文切换/00844.webp)

他还提了一个很容易被忽略的细节：观察 daemon 里 **fd 的变化**可以看到，用户在打开那个文件的时候，**daemon 在它继承的内存地址空间里还重复打开了一下这个文件**，从而完成对用户想操作的那个文件的「接管」[【跳转到 14:29】](https://www.bilibili.com/video/BV1sj411w7s8/?t=869)。也就是说，两个进程操作的是同一个底层文件，靠的是 fd 的继承与重开。

### 5.2 断点一：vfs_unlink

第一个断点下在 `vfs_unlink`。断住之后看调用栈：`fuse_unlink` 被 `vfs_unlink` 调用 [【跳转到 20:16】](https://www.bilibili.com/video/BV1sj411w7s8/?t=1216)。

![GDB 断在 fuse_unlink，调用栈显示 fuse_unlink 由 vfs_unlink 调用；左侧是 VS Code 里的 fuse 内核源码，下方是 daemon 打印的 opcode 日志](assets/用%20GDB%20跟踪一次%20FUSE%20请求——两个进程与两次上下文切换/01216.webp)

这一步验证了架构图里那条线：**用户进程的 `unlink` 被 VFS 层转发给 FUSE 内核模块** [【跳转到 18:37】](https://www.bilibili.com/video/BV1sj411w7s8/?t=1117)。讲者还顺带解释了断点前那些 attribute 操作：为了找到这个文件，内核先生成了它的大小、所在目录等属性 [【跳转到 18:37】](https://www.bilibili.com/video/BV1sj411w7s8/?t=1117)。

此时观察两个进程的状态：右上角是 rm 进程，它的调用栈停在 `unlink` 的内核断点上，说明**它是活跃的**；左下角是 fuse daemon，**当前是休眠状态** [【跳转到 19:51】](https://www.bilibili.com/video/BV1sj411w7s8/?t=1191)。

### 5.3 断点二：request_wait_answer 里的睡眠

继续走，会停在 `request_wait_answer`。讲者说看代码很容易对上：`fuse_lib_unlink` 里调 `fuse_simple_request`，再走到 `request_wait_answer` [【跳转到 20:41】](https://www.bilibili.com/video/BV1sj411w7s8/?t=1241)。

![GDB 断在 request_wait_answer，下方调用栈依次是 request_wait_answer、fuse_simple_request、fuse_unlink；左侧源码停在 fuse_request_send 之后的等待处](assets/用%20GDB%20跟踪一次%20FUSE%20请求——两个进程与两次上下文切换/01387.webp)

`request_wait_answer` 里做的事情就是**休眠**。讲者用了一个很好的类比：用户态进程相当于把 rm 这个操作**像快递一样转发给 daemon** 去做，而 rm 进程此时无事可做，就休眠着等待；等 daemon 把 rm 的回调执行完成之后，再回来唤醒它 [【跳转到 21:05】](https://www.bilibili.com/video/BV1sj411w7s8/?t=1265)。

这段是本小节的核心画面：**用户进程并没有「阻塞在磁盘 IO」上，它阻塞在「等另一个进程回话」上**。FUSE 的延迟之所以对调度敏感，根子就在这里。

### 5.4 断点三：fuse_dev_write，以及另一个 CPU

把前两个断点取消，让 daemon 从 `read(/dev/fuse)` 的休眠里回来——讲者说这里能看到它「从读取 `/dev/fuse` 这个驱动的流程里回来」[【跳转到 21:57】](https://www.bilibili.com/video/BV1sj411w7s8/?t=1317)。随后在 `fuse_dev_write` 加断点，因为 daemon 做完用户态的操作之后，要回到用户态去通知 rm 进程 [【跳转到 22:38】](https://www.bilibili.com/video/BV1sj411w7s8/?t=1358)。

断住之后，用户态的 debug 日志会打出这次请求的 opcode：`unlink`；而 `fuse_dev_write` 是从 VFS 层过来的（讲者说有些断点解析不出来，可能是 debug 符号的 bug）[【跳转到 23:07】](https://www.bilibili.com/video/BV1sj411w7s8/?t=1387)。

最有意思的一幕在 `put_request`：讲者先注意到刚才是在 **0 号 CPU** 上执行的，而现在 `put_request` 已经跑到 **2 号 CPU** 上；再 `info threads` 一看，`fuse_dev_do_write` 的 `put_request` 和另一个线程**同时在跑** [【跳转到 25:12】](https://www.bilibili.com/video/BV1sj411w7s8/?t=1512)。

![GDB 的 info threads：1 号线程停在 fuse_put_request，2 号线程停在 fuse_dev_do_write，说明 daemon 的写回与请求回收在不同 CPU 上并行推进](assets/用%20GDB%20跟踪一次%20FUSE%20请求——两个进程与两次上下文切换/01512.webp)

这就把「两个进程」从概念变成了可观测的事实：**rm 进程和 daemon 进程是并行跑在不同 CPU 上的**，不是串行接力。

### 5.5 收尾：谁唤醒谁

把图对上：右侧 daemon 的内核流程把 rm 进程唤醒之后，它接着回去 `write`，`write` 完又回到上面那个 `read` 系统调用，进入循环，在那里 sleep 等下一个请求；左侧的 rm 用户进程接收到「rm 做完」的结果，就自己退出了 [【跳转到 25:26】](https://www.bilibili.com/video/BV1sj411w7s8/?t=1526)。

最后观察到的现象是：`rm temp/a.txt` 这个进程已经回来、可以自由操作，daemon 的 debug 日志也不再打了——说明整个流程正常跑完 [【跳转到 26:04】](https://www.bilibili.com/video/BV1sj411w7s8/?t=1564)。

把这一节压成一张时序表（左栏用户进程、右栏 daemon，与内核文档那张图一一对应）：

| 步骤 | rm 进程 | fuse daemon 进程 |
| :--- | :--- | :--- |
| 1 | — | `read(/dev/fuse)`，无请求则睡眠 |
| 2 | `sys_unlink` → `vfs_unlink` → `fuse_unlink` | 睡 |
| 3 | 构造请求、挂进 pending 队列、唤醒 daemon | 被唤醒 |
| 4 | 睡在 `request_wait_answer` | 取走请求、转入 processing、返回用户态 |
| 5 | 睡 | 执行 `unlink` 回调（真正干活） |
| 6 | 睡 | `write(/dev/fuse)` 写回响应 |
| 7 | 被唤醒，`request_wait_answer` 返回 | 回到 `read` 循环，继续睡 |
| 8 | `sys_unlink` 返回，进程退出 | 睡 |

## 六、问答里的三个实用结论

### 6.1 版本必须配套，因为结构体要对齐

有人问 libfuse 对内核/发行版版本有没有要求。讲者的回答分两层 [【跳转到 26:45】](https://www.bilibili.com/video/BV1sj411w7s8/?t=1605)：

- **内核态**：`fuse.ko` 的代码和内核代码库放在一起，随内核迭代。`fuse.h` 里有一个 FUSE 版本号，一路升到 **7.38**；不同内核版本会改结构体，**成员偏移一变，新版本的内核模块就不能在旧内核里用** [【跳转到 27:31】](https://www.bilibili.com/video/BV1sj411w7s8/?t=1651)。
- **用户态**：libfuse 的接口相对稳定，但它编译时依赖 `include/uapi` 里给用户态用的 API——因为**有些结构体是内核态和用户态共享的，必须保证一致**，整套流程才能正常 work [【跳转到 28:43】](https://www.bilibili.com/video/BV1sj411w7s8/?t=1723)。

![GDB 里看 FUSE 请求日志：forget 请求把 inode 的引用计数从 451 减到 5，随后 GETATTR、LOOKUP 继续；这些结构体字段的偏移就是版本配套要保证的东西](assets/用%20GDB%20跟踪一次%20FUSE%20请求——两个进程与两次上下文切换/01651.webp)

结论很实际：**用 FUSE 就要固定内核版本**，然后基于某个稳定内核去衍生开发下游的内核模块和 libfuse。

### 6.2 谁在用 FUSE

讲者列了几类典型应用 [【跳转到 32:25】](https://www.bilibili.com/video/BV1sj411w7s8/?t=1945)：

- **lxcfs**（Linux container filesystem）：容器场景、云端场景的文件系统，纯软件，不依赖硬件版本；
- **分布式文件系统**：如 JuiceFS，还有 CephFS 之类，云计算场景用得比较多。

它们的共同点是：**纯软件、跑在 Linux 上、需要灵活性**——正好落在 FUSE 的甜区里。

### 6.3 性能到底差多少

有人问「效率低」具体低在哪。讲者的回答很直接：做写入和读取性能测试时会显著降低读写性能——**没有这层 FUSE 转发时读写能到 100 MB/s，有了这层转发只有 50 MB/s** [【跳转到 33:40】](https://www.bilibili.com/video/BV1sj411w7s8/?t=2020)。

但换来的是两件事：

- **崩溃隔离**：内核态文件系统一不小心崩了会导致整个内核崩溃；用户态文件系统的崩溃只会让 daemon 进程挂掉，不影响其他业务 [【跳转到 34:30】](https://www.bilibili.com/video/BV1sj411w7s8/?t=2070)。
- **可以做「不是文件」的文件**：读写回调里可以放网络操作，把文件内容直接发给远端机器，不用写到磁盘上 [【跳转到 35:45】](https://www.bilibili.com/video/BV1sj411w7s8/?t=2145)。

讲者还补了一句关于缓存的观察：读文件可以用 cache 加速，所以很多用户并不特别在意高频读写的效率，低频场景差不太多就行 [【跳转到 35:20】](https://www.bilibili.com/video/BV1sj411w7s8/?t=2120)。

## 小结

- **FUSE = 内核模块 + 用户态库 + 挂载工具**，一句话概括它的取舍：效率低，但灵活。
- **顺序不能反**：必须先挂载、让 daemon 就位并阻塞在 `read(/dev/fuse)` 上，用户才能对这个目录下命令。
- **一次请求牵扯两个进程**：用户进程构造请求后睡在 `request_wait_answer`，daemon 睡在 `read` 上；两者靠队列和等待队列互相唤醒。
- **两个进程是并行的**：GDB 里能看到 `fuse_dev_do_write` 与 `put_request` 跑在不同 CPU 上。
- **往返四次上下文切换**：去程两次、回程两次，这是「效率低」的结构性来源。
- **版本要配套**：`fuse.h` 的版本号（讲到 7.38）与 `include/uapi` 里共享的结构体必须一致，否则内核模块和 libfuse 对不上。
- **性能量级**：讲者的实测是 100 MB/s 降到 50 MB/s，换来的是崩溃隔离和「回调里可以做任何事」的灵活性。

## 关键术语速查

| 术语 | 一句话解释 |
| :--- | :--- |
| `fuse.ko` | 内核模块，向用户态暴露 `/dev/fuse`，把 VFS 调用转发出去 |
| `/dev/fuse` | 守护进程与内核之间唯一的通信设备，daemon 在它上面 `read` 请求、`write` 响应 |
| `libfuse` | 用户态库，封装 `/dev/fuse` 的协议细节，提供 high-level 与 low-level 两套 API |
| `fusermount` | 挂载工具，把目标目录挂到 FUSE 文件系统上 |
| `passthrough_hp` | libfuse 自带的示例文件系统，把操作透传给底层目录，讲者用它做实验 |
| `sfs_unlink` | 该示例里的 unlink 回调，留给用户实现具体语义 |
| `vfs_unlink` | VFS 层的 unlink 入口，FUSE 文件系统在这里被转发到 `fuse_unlink` |
| `fuse_simple_request` | 构造并发送一条元数据请求的函数，之后进入 `request_wait_answer` |
| `request_wait_answer` | 用户进程等待响应的位置，请求发出后睡在这里 |
| `fuse_dev_write` | 守护进程写回响应的入口，内核据此唤醒等待的进程 |
| `put_request` | 请求回收，GDB 里能看到它与写回在不同 CPU 上并行 |
| `fusectl` | FUSE 的 control 文件系统，可以临时 abort 请求 |
| `include/uapi` | 内核与用户态共享的结构体定义，决定 libfuse 与内核能否对上 |