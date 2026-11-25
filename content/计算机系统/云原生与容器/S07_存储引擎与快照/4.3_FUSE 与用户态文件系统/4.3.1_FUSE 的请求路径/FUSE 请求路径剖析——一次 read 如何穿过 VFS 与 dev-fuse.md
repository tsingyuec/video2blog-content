# FUSE 请求路径剖析：一次 read 如何穿过 VFS 与 /dev/fuse

> 视频来源：[FUSE 文件系统浅析 - 张老师](https://www.bilibili.com/video/BV1r24y157gm/)（Bilibili · 泰晓科技 RISC-V Linux 内核兴趣小组 · 讲者张老师）｜时长约 75 分钟，技术部分约 57 分钟，其余为问答
>
> 导读：这是一场**贴着内核源码讲**的分享：先给 FUSE 的高层架构图，再从 `mount` 一路读到 `fuse_fill_super`、`fuse_send_init`，然后讲请求结构体、五个请求队列、libfuse 的两级 API，最后用内核文档里那张「rm 命令流程图」把整条链路串起来。本文按本小节的题目重排：**先讲清楚一次请求要穿过哪几个部件，再逐步走完「VFS → 队列 → 守护进程 → 回程」**。JuiceFS 收到请求之后怎么做留给 4.2.2，性能优化手段留给 4.3.2，本文只讲通用机制。

## 本讲要解决的核心问题（SCQA）

**背景**：在 Linux 上，`read(fd, buf, n)` 这类调用由内核的 VFS 统一接收，再分发给具体文件系统的实现。传统文件系统（ext4、XFS）的实现就在内核里，VFS 调一个函数指针就到位了。

**冲突**：FUSE 文件系统的实现**不在内核里**。内核里只有一个「代理」——`fuse.ko`，它注册到 VFS，却什么都不做，把请求打包后丢给用户态的守护进程；守护进程算完再把结果丢回来。可用户看到的仍然只是一个普通的 `read`。

**疑问**：这一次 `read` 到底在哪些函数、哪些结构体、哪些队列之间流转？内核凭什么知道该把请求交给哪个守护进程？守护进程又凭什么知道这个响应对应哪个请求？代价花在哪里？

**回答（中心思想）**：一次 FUSE 请求是**三段接力**——① VFS 把 `read` 翻译成一条 FUSE 协议请求，挂到 `fuse_conn` 的队列上并唤醒守护进程；② 守护进程用 `read(/dev/fuse)` 取走请求，解析 `fuse_in_header` 里的 opcode 和 nodeid，调用自己实现的回调，再用 `write(/dev/fuse)` 写回一个带 `unique` 序号的响应；③ 内核侧 `fuse_dev_do_write` 找到还在 `request_wait_answer` 里睡觉的进程，把数据拷进页缓存并唤醒它。整条链路上**没有任何一方拥有「文件系统」，只有协议**——这正是 FUSE 灵活性和开销的共同来源。

## 一、四个部件，一条请求路径

讲者一上来就给了 FUSE 的组成清单：内核模块 `fuse.ko`、用户库 `libfuse.*`、挂载工具 `fusermount`、用户态守护进程 `fuse daemon` [【跳转到 00:31】](https://www.bilibili.com/video/BV1r24y157gm/?t=31)。

![FUSE 高层架构图：左边是普通内核文件系统的对照，右边是 FUSE 的 request 与 reply 两条流——应用经 VFS 进入 FUSE driver，再经 /dev/fuse 到用户态守护进程](assets/FUSE%20请求路径剖析——一次%20read%20如何穿过%20VFS%20与%20dev-fuse/00106.webp)

这张图是理解全文的锚点，值得逐块看：

- **左边那张小图是「对照组」**：`ls /tmp/fuse` 经 libc 进入 VFS，VFS 下面是 NFS、Ext3 这些**在内核里**的实现。FUSE 只是 VFS 下面多出来的一个分支。
- **右边是 FUSE 的真实结构**：`Application` → `VFS` → `FUSE driver` → `/dev/fuse` → `FUSE file-system daemon`。图上红色三角是 request，黄色方块是 reply，两条流的路径**不对称**：请求从内核流向用户态，响应从用户态流回内核。
- **`Other Kernel subsystems`** 那条线说明守护进程并非只能自己算：它可以把请求再下发给内核的其他子系统（比如底层还是一个 ext4 目录），这就是后面要讲的「可堆叠」。

讲者特别强调 `fuse driver` 的角色：它**在加载注册 FUSE 文件系统时注册到 VFS，但自己不做任何事**，只充当用户态实现的代理，把请求抛给用户态 [【跳转到 03:44】](https://www.bilibili.com/video/BV1r24y157gm/?t=224)。这句话解释了一个常见误解：`fuse.ko` 不是「一个文件系统的实现」，它是「一个把 VFS 调用翻译成 IPC 消息的转发器」。

所以一次操作的数据流是：**用户态 → 内核态 → 用户态 →（算完）→ 内核态 → 用户态**。讲者说这是「涉及大量用户态到内核态的上下文切换」，也正是 FUSE 性能问题的根 [【跳转到 14:17】](https://www.bilibili.com/video/BV1r24y157gm/?t=857)。

### 1.3 为什么业界愿意付这个代价

既然多两次穿越，为什么还用？讲者列了五条理由 [【跳转到 15:57】](https://www.bilibili.com/video/BV1r24y157gm/?t=957)：

1. **可堆叠**。底层还是 ext4，你在上面用用户态守护进程堆叠一层，就能加去重（deduplication）、压缩这类特性，不用改内核。
2. **原型快**。开发文件系统要动内核是很讨厌的事，在用户态可以尽快把原型建起来，成熟了再考虑移进内核。
3. **已有文件系统可以被「搬出来」**。ZFS、NTFS 都已经有用户态实现 [【跳转到 16:47】](https://www.bilibili.com/video/BV1r24y157gm/?t=1007)。
4. **大公司在用**。讲者举了 IBM、Apache HDFS、Google File System、RedHat GlusterFS 等例子。
5. **文件系统越来越复杂**。内核里代码量最大的可能就是文件系统，而内核态实现一旦出问题就会导致内核崩溃 [【跳转到 17:37】](https://www.bilibili.com/video/BV1r24y157gm/?t=1057)。放到用户态，开发和维护压力都小一些。

这五条恰好解释了 FUSE 的定位：**它不是「更快的文件系统」，而是「用可接受的性能损失换开发自由度和崩溃隔离」的框架**。

## 二、挂载：内核怎么把 FUSE 挂进 VFS

在能收发请求之前，得先挂载。挂载这一步决定了后面所有的数据结构：`super_block`、`fuse_conn`、队列、`/dev/fuse` 的关联、以及第一次 `FUSE_INIT` 协商。

### 2.1 mount 的调用链：从系统调用到 fuse_fill_super

讲者把 `mount(2)` 到 `fuse_fill_super` 的调用链整理成了一张图 [【跳转到 26:44】](https://www.bilibili.com/video/BV1r24y157gm/?t=1604)：

![mount 调用链：mount → do_mount → do_new_mount → fs_context_for_mount → vfs_get_tree → legacy_get_tree → fuse_mount → fuse_fill_super，再往下是 fuse_conn_init、fuse_get_root_inode、fuse_iget、fuse_send_init](assets/FUSE%20请求路径剖析——一次%20read%20如何穿过%20VFS%20与%20dev-fuse/01604.webp)

沿着这张图读，有几个关键点：

1. **`do_new_mount` 之后先建 `fs_context`**。现代内核用 `fs_context` 保存挂载参数；FUSE 走的是 legacy 路径，所以 `get_tree` 指针指向 `legacy_get_tree`，再进 `fuse_mount`。
2. **`fuse_mount` 不是「挂一块盘」**。讲者说得很直白：FUSE 挂载点「不是真正意义上的设备」，它是个混杂设备，只用来让守护进程和内核通信，**并不存在真正存放文件系统的介质** [【跳转到 28:49】](https://www.bilibili.com/video/BV1r24y157gm/?t=1729)。所以 `fuse_mount` 干的事是建立连接、拿到 `/dev/fuse` 的 fd，而不是去读超级块。
3. **`fuse_fill_super` 才是真正「建文件系统」的地方**，它下面挂着一串初始化：`super_block`、`fuse_conn_init`、`fuse_dev_alloc`、`fuse_bdi_init`、`fuse_get_root_inode`（内部是 `fuse_iget`）、`fuse_send_init`。

### 2.2 fuse_init：注册文件系统类型、/dev/fuse 与 sysfs

模块初始化 `fuse_init` 做了三件互相独立的事 [【跳转到 40:04】](https://www.bilibili.com/video/BV1r24y157gm/?t=2404)：

![fuse_init 源码：fuse_fs_init 里 register_filesystem(fuse_fs_type)、fuse_dev_init 里 misc_register 注册 /dev/fuse、fuse_sysfs_init 里建立 connections 目录](assets/FUSE%20请求路径剖析——一次%20read%20如何穿过%20VFS%20与%20dev-fuse/02404.webp)

- **`fuse_fs_init`**：`kmem_cache_create` 建 `fuse_inode` 和 `fuse_req` 两个 slab 缓存，`register_filesystem(&fuse_fs_type)` 注册一种新的文件系统类型。这一步之后，`mount -t fuse` 才认识这个名字。
- **`fuse_dev_init`**：`misc_register(&fuse_miscdevice)` 注册 `/dev/fuse`，并把 `fuse_dev_operations` 挂上去。讲者说这里原本也可以设计成块设备，实际实现选的是**混杂设备** [【跳转到 04:09】](https://www.bilibili.com/video/BV1r24y157gm/?t=249)。
- **`fuse_sysfs_init`**：在 sysfs 下建 `connections` 目录。于是每建立一个连接，`/sys/fs/fuse/connections/<id>/` 下就会多一个节点——这是后面观测队列长度的地方 [【跳转到 41:44】](https://www.bilibili.com/video/BV1r24y157gm/?t=2504)。

`/dev/fuse` 上的操作怎么落到具体函数？讲者专门讲了 `replace_fops` 这个机制 [【跳转到 53:06】](https://www.bilibili.com/video/BV1r24y157gm/?t=3186)：

![replace_fops：misc_register 注册的 fuse_dev_operations 是 miscdevice.fops 类型，misc_open 里通过 replace_fops 把它换成 file->f_op，之后 read/write 就走 fuse_dev_read 等函数](assets/FUSE%20请求路径剖析——一次%20read%20如何穿过%20VFS%20与%20dev-fuse/03186.webp)

也就是说：`open("/dev/fuse")` 时，`misc_open` 把 `file->f_op` 替换成 `fuse_dev_operations`；此后守护进程对这个 fd 的每一次 `read`/`write`，都直接进 `fuse_dev_read` / `fuse_dev_write`。这条「换 fops」的细节很重要，因为它是「用户态一个普通的 read 系统调用，怎么就会去取内核队列里的请求」的答案。

### 2.3 fuse_fill_super：一次挂载建了哪些结构

`fuse_fill_super` 是全场信息密度最高的一段，讲者把它的每个子调用都拆开讲了 [【跳转到 43:24】](https://www.bilibili.com/video/BV1r24y157gm/?t=2604)：

![fuse_fill_super 的六个子步骤：super_block 初始化、fuse_conn_init、fuse_dev_alloc、fuse_bdi_init、fuse_get_root_inode、fuse_send_init；右侧是 fuse_conn_init 里对队列与 max_background 的初始化](assets/FUSE%20请求路径剖析——一次%20read%20如何穿过%20VFS%20与%20dev-fuse/02604.webp)

- **`super_block`**：填魔术数 `FUSE_SUPER_MAGIC`、`s_maxbytes`（最大文件大小）、`s_op = &fuse_super_operations`、`s_xattr`、`s_export_op`，还有几个标志位。讲者说「很多基本参数、ops 注册都在这里」。
- **`fuse_conn_init`**：建 `fuse_conn`，这是整条连接的「总控结构」——队列、后台请求计数、拥塞阈值、最大页数都在里面。图上能直接读到 `fc->max_background = FUSE_DEFAULT_MAX_BACKGROUND` 和 `fc->congestion_threshold = FUSE_DEFAULT_CONGESTION_THRESHOLD`。
- **`fuse_dev_alloc`**：分配 `fuse_dev` 和 `fuse_pqueue`。讲者提醒：`processing` 队列**不在** `fuse_iqueue` 里，它在 `fuse_dev_alloc` 里初始化 [【跳转到 43:49】](https://www.bilibili.com/video/BV1r24y157gm/?t=2629)。
- **`fuse_bdi_init`**：挂上 backing device info，让内核的预读机制能对 FUSE 生效。
- **`fuse_get_root_inode` → `fuse_iget`**：把根 inode 建出来，并把 `fuse_file_operations`、`fuse_file_aops` 这些 ops 绑定到 inode 上 [【跳转到 46:44】](https://www.bilibili.com/video/BV1r24y157gm/?t=2804)。

![fuse_iget 与 inode ops 的绑定关系：fuse_init_inode 按 inode 类型选 ops，普通文件拿到 fuse_file_operations 与 fuse_file_aops，目录拿到 fuse_dir_inode_operations](assets/FUSE%20请求路径剖析——一次%20read%20如何穿过%20VFS%20与%20dev-fuse/02804.webp)
- **`fuse_send_init`**：发出第一条请求 `FUSE_INIT`。

`FUSE_INIT` 值得单独看，因为它就是「一条 FUSE 请求长什么样」的样板 [【跳转到 45:54】](https://www.bilibili.com/video/BV1r24y157gm/?t=2754)：

![fuse_send_init 源码：把 major/minor 版本、max_readahead、flags 能力位填进 fuse_init_in，req->in.h.opcode 设为 FUSE_INIT，最后 fuse_request_send_background 发出](assets/FUSE%20请求路径剖析——一次%20read%20如何穿过%20VFS%20与%20dev-fuse/02754.webp)

这段代码把三件事一次演示完了：**请求头里放 opcode**（`req->in.h.opcode = FUSE_INIT`）、**参数放在 in.args 里**（`fuse_init_in` 结构）、**请求通过 `fuse_request_send_background` 入队**。`FUSE_INIT` 要协商的内容，讲者归纳为三项：协议版本、相互支持的能力集、各种参数设置 [【跳转到 10:07】](https://www.bilibili.com/video/BV1r24y157gm/?t=607)。这也解释了为什么 FUSE 的内核模块和 libfuse 必须版本配套——协议是两边谈出来的。

## 三、请求的形状：一个头 + 43 种 opcode

### 3.1 43 种请求类型

内核 driver 和用户态 daemon 通信时，会组织一个 FUSE 请求结构体。讲者说按含义分一共有 **43 种请求类型**，其中大多数可以直接映射到传统 VFS 操作 [【跳转到 09:42】](https://www.bilibili.com/video/BV1r24y157gm/?t=582)：

![请求类型分组表：Special 3 种（INIT、DESTROY、INTERRUPT）、Metadata 14 种、Data 2 种（READ、WRITE）、Attributes、Extended Attributes、Symlinks、Directory 7 种、Locking、Misc](assets/FUSE%20请求路径剖析——一次%20read%20如何穿过%20VFS%20与%20dev-fuse/00582.webp)

这张表值得记住两行：

- **`Data (2)` 只有 `READ` 和 `WRITE`**。也就是说，真正搬文件内容的只有两种请求，其余四十来种都在处理元数据、目录、属性、锁。这解释了为什么 FUSE 的元数据操作特别多、也特别碎。
- **`Special (3)` 里的 `INTERRUPT`**：如果之前发出的请求不再需要了（比如用户按了 Ctrl-C），内核会发一个 `INTERRUPT` 请求，告诉守护进程「这个请求可以放弃了」。

### 3.2 三个字段：opcode、nodeid、unique

一条请求头里有三个字段撑起了整个协议：

![请求头字段说明：node ID 是无符号 64 位整数，在内核和用户空间标识 inode；LOOKUP 实现 path-to-inode 翻译；OPEN 的回复里守护进程可以分配 64 位文件句柄 fh，此后该文件的每次请求都带着它](assets/FUSE%20请求路径剖析——一次%20read%20如何穿过%20VFS%20与%20dev-fuse/00707.webp)

- **`opcode`**：这条请求要干什么。守护进程收到后第一件事就是解析它，然后决定分发到哪个回调。
- **`nodeid`**：标识 inode。讲者强调 inode 是「这个文件系统最重要的一个结构」，`LOOKUP` 请求实现的就是 **path → inode** 的翻译 [【跳转到 10:57】](https://www.bilibili.com/video/BV1r24y157gm/?t=657)。路径是给人看的，nodeid 才是内核和守护进程之间真正传的东西。
- **`unique`（sequence 号）**：每个请求由内核分配一个唯一的 64 位序号。讲者的原话是「发出的请求和回来的响应就能一一对应」——**响应里带着同一个 unique，内核据此知道该唤醒谁**。这是整个异步模型能成立的关键。

另外还有两个生命周期相关的机制：

- **`FORGET` / `BATCH_FORGET`**：新建 inode 时会放进 inode cache；当内核要从 cache 里删掉它时，发 `FORGET` 告诉用户态「这个 nodeid 可以忘了」。批量删就发 `BATCH_FORGET` [【跳转到 11:22】](https://www.bilibili.com/video/BV1r24y157gm/?t=682)。
- **`OPEN` 分配的 `fh`**：打开文件时守护进程可以回一个 64 位文件句柄，此后**该文件的每次请求都带着它**，直到 `RELEASE`。这就是守护进程保存「每个已打开文件的状态」的地方 [【跳转到 11:47】](https://www.bilibili.com/video/BV1r24y157gm/?t=707)。

### 3.3 请求走哪条路：ops 结构图

讲者把 FUSE 驱动注册的所有 ops 画成了一张大图，用来回答「一次 read 到底从哪个函数进来」[【跳转到 51:26】](https://www.bilibili.com/video/BV1r24y157gm/?t=3086)：

![FUSE 驱动主要 ops 结构：fuse_file_operations 里 read = fuse_read、read_iter = fuse_file_read_iter；右侧是 fuse_simple_request 与各 opcode 的对应关系，元数据类操作都汇到 fuse_simple_request](assets/FUSE%20请求路径剖析——一次%20read%20如何穿过%20VFS%20与%20dev-fuse/03086.webp)

这张图给出了两条重要结论：

1. **元数据类操作（lookup、getattr、setattr、create、unlink、mkdir……）最后都汇到 `fuse_simple_request`**。讲者说「这些操作最后都会集中到 `fuse_simple_request` 这个点上」。
2. **读写不走这条路**。讲者明确说：「读写是对文件内容的操作，不会像元数据那么简单，所以它最后虽然也是发 request，但不会走 `fuse_simple_request`，会走另外一条路」[【跳转到 50:47】](https://www.bilibili.com/video/BV1r24y157gm/?t=3047)。原因是读写要处理页、要处理大量数据，需要一套带页描述符的请求路径。

`fuse_simple_request` 本身很短，值得一看，因为它把「发请求 + 等响应」的骨架暴露得很清楚 [【跳转到 49:07】](https://www.bilibili.com/video/BV1r24y157gm/?t=2947)：

![fuse_simple_request 源码：fuse_get_req 取一个请求、填 opcode/nodeid/numargs、memcpy 参数、fuse_request_send 发出、最后 fuse_put_request 归还；下方是 fuse_request_send → fuse_request_send_msg → queue_request 与 request_wait_answer](assets/FUSE%20请求路径剖析——一次%20read%20如何穿过%20VFS%20与%20dev-fuse/02947.webp)

`fuse_request_send` 分叉出的两个函数，正是这条链路的两端：**`queue_request` 负责入队**，**`request_wait_answer` 负责睡等待**。下一节就讲这个队列。

## 四、五个队列，一条优先级规则

请求不是「直接递给守护进程」，而是先进队列。讲者说请求队列是 daemon 和 kernel 通信的数据结构，**按优先级从高到低一共五个**：interrupt、forget、processing、pending、background [【跳转到 04:34】](https://www.bilibili.com/video/BV1r24y157gm/?t=274)。

![基本原理页：fuse driver 注册到 VFS 作为代理；/dev/fuse 作为 daemon 与 kernel 的接口；请求队列分 interrupt、forgets、processing、pending、background 五级](assets/FUSE%20请求路径剖析——一次%20read%20如何穿过%20VFS%20与%20dev-fuse/00274.webp)

这张图上能看出队列之间的层次关系：`pending` 是主入口，`background` 是它的「分级异步队列」，队列头会接到 pending 的尾部；`processing` 里的请求是「已经交给守护进程、还没回响应」的。讲者强调一条不变量：**一个 request 在任何时刻只属于一个队列** [【跳转到 05:59】](https://www.bilibili.com/video/BV1r24y157gm/?t=359)。

守护进程 `read(/dev/fuse)` 时，内核按下面的规则挑一个请求给它 [【跳转到 06:24】](https://www.bilibili.com/video/BV1r24y157gm/?t=384)：

![FUSE queue 页：中断队列优先级最高，因此中断请求最先传输；forget 与 nonforget 公平选择——每 8 个 nonforget 请求传输 16 个 forget 请求；pending 里等待最久的请求送给 daemon 并转入 processing；daemon 写 /dev/fuse 回复后请求移出 processing](assets/FUSE%20请求路径剖析——一次%20read%20如何穿过%20VFS%20与%20dev-fuse/00384.webp)

四条规则，逐条解释：

1. **中断队列优先级最高**。因为 `INTERRUPT` 的语义是「这个请求我不要了」，越早送到越能省掉无用功。
2. **forget 要做公平性限制**。forget 是第二优先级，但不能让它把带宽吃光，所以「每 8 个 nonforget 请求，传输 16 个 forget 请求」——给低优先级请求留出带宽。
3. **pending 里挑等待最久的**，同时把它转到 `processing`。注意这一步是「转移」而不是「复制」：请求从 pending 摘下、挂到 processing，全程只有一个队列持有它。
4. **pending 为空时，守护进程阻塞在 `read` 调用里**。这就是守护进程「平时在睡觉」的准确含义——不是轮询，是阻塞在系统调用上等唤醒。

`background` 队列还有两个可调参数，讲者给得很具体：`max_background` 默认 **12**，即 pending 里驻留的异步请求不超过 12 个；`congestion_threshold` 是它的 **75%**，也就是 **9**，超过就认为队列拥塞，要对发起该文件操作的用户进程限流 [【跳转到 08:02】](https://www.bilibili.com/video/BV1r24y157gm/?t=482) [【跳转到 08:27】](https://www.bilibili.com/video/BV1r24y157gm/?t=507)。他还补了一句使用建议：这些是经验值，应该在自己的场景里跑 benchmark 再调。

顺带一个容易忽略的细节：**写请求一般不在发起时入 background**，而是在脏页回刷（bdflush）时才入队 [【跳转到 07:37】](https://www.bilibili.com/video/BV1r24y157gm/?t=457)。读请求则直接入队——这对理解「读延迟为什么对 FUSE 特别敏感」很有帮助。

## 五、把一次请求走完：官方文档那张流程图

讲者用内核文档里的一张图把前面所有零件串了起来。原图以 `rm /mnt/fuse/file` 为例，左边是用户进程，右边是守护进程，中间是内核 [【跳转到 34:14】](https://www.bilibili.com/video/BV1r24y157gm/?t=2054)：

![内核文档里的 FUSE 请求流程图：左侧 rm 进程走 sys_unlink → fuse_unlink → request_send 入 pending 队列 → request_wait_answer 睡眠；右侧守护进程 sys_read → fuse_dev_read → request_wait 睡眠，被唤醒后取请求、转 processing、执行回调，再 sys_write → fuse_dev_write 唤醒对方](assets/FUSE%20请求路径剖析——一次%20read%20如何穿过%20VFS%20与%20dev-fuse/02054.webp)

这张图信息量很大，逐行读一遍：

**用户进程一侧（左栏）**

1. `sys_unlink()` 进入系统调用，走到 `fuse_unlink()`。
2. `[get request from fc->unused_list]`：从连接的空闲请求池里取一个 `fuse_req`。
3. `request_send()`：`[queue req on fc->pending]` 把请求挂到 pending 队列，`[wake up fc->waitq]` 唤醒睡在这个连接等待队列上的守护进程。
4. `request_wait_answer()`：`[sleep on req->waitq]` 自己睡在**这个请求自己的**等待队列上。注意这里有两个不同的等待队列：连接级的 `fc->waitq` 用来叫醒守护进程，请求级的 `req->waitq` 用来等这一条请求的结果。

**守护进程一侧（右栏）**

5. `sys_read()` → `fuse_dev_read()` → `request_wait()`：`[sleep on fc->waitq]`。守护进程平时就停在这里，不占 CPU。
6. 被唤醒后回到 `request_wait()`：`[remove req from fc->pending]` 摘下来、`[copy req to read buffer]` 拷进读缓冲区、`[add req to fc->processing]` 挂到 processing，然后 `fuse_dev_read` 返回，`sys_read` 把请求头交给用户态。
7. `[perform unlink]`：守护进程解析请求，调用自己实现的回调，把活干完。
8. `sys_write()` → `fuse_dev_write()`：`[look up req in fc->processing]` 按 unique 找到请求、`[remove from fc->processing]` 移出、`[copy write buffer to req]` 把响应内容拷回请求、`[wake up req->waitq]` 唤醒还在睡的进程。

**回到用户进程**：`request_wait_answer()` 醒来，`request_send()` 收尾把请求还回 `fc->unused_list`，`fuse_unlink()` 返回，`sys_unlink()` 返回。

讲者对这个流程有两句点睛的话：一是「**所有通信其实都是通过发送请求、回响应来实现的**」；二是 `perform unlink` 那一步「**就是你要你来设计的**」——框架只负责把请求送到你手上，语义由你实现 [【跳转到 35:04】](https://www.bilibili.com/video/BV1r24y157gm/?t=2104)。

### 5.1 把 unlink 换成 read，哪些地方变、哪些不变

本节要回答的是一次 `read`，而上面这张图是 `unlink`。好消息是**骨架完全一样**，只有三处不同：

| 环节 | unlink | read |
| :--- | :--- | :--- |
| 入口 | `sys_unlink` → `fuse_unlink` | `vfs_read` → `fuse_file_operations.read_iter`（`fuse_file_read_iter`）→ `fuse_read` |
| opcode | `FUSE_UNLINK`，参数是文件名 | `FUSE_READ`，参数是 `fh`、偏移、长度 |
| 回程数据 | 只有一个错误码 | `fuse_out_header` 后面跟着实际的数据页，要 `fuse_copy_pages` 拷进页缓存 |

第一行和第三行都能在讲者的 ops 结构图里找到依据：`fuse_file_operations` 里 `read = fuse_read`、`read_iter = fuse_file_read_iter`；而不管走不走 splice，读写最终都「统一到 `fuse_copy_pages`，也就是做页面拷贝」[【跳转到 33:49】](https://www.bilibili.com/video/BV1r24y157gm/?t=2029)。

第二行里那个 `fh` 来自之前的 `OPEN`：打开文件时守护进程分配一个 64 位句柄，之后该文件的每次请求都带着它。所以一次 `read` 的请求头里，**`nodeid` 告诉你是哪个 inode，`fh` 告诉你是哪一次打开，`unique` 让响应能找回你**——三个字段各管一件事，缺一不可。

### 5.2 数据怎么回到用户缓冲

回程的数据不是「一份」，而是「一页一页」。讲者提到 FUSE 会把多页数据拼成一个请求，read 也一样必须多页 [【跳转到 15:32】](https://www.bilibili.com/video/BV1r24y157gm/?t=932)。这带来两个后果：

- **大 IO 更划算**：请求头、上下文切换这些固定开销被摊到更多页上，平均开销随数据量下降。
- **小 IO 很吃亏**：一次 4 KB 的读也要走完整条链路，固定开销一分不少。这是 FUSE 上「小文件、随机读」性能差的结构性原因。

数据落到哪？讲者说文件系统操作很多时候「实际上还是对内存 page cache 的操作」，涉及 `address_space` 的操作会走到 mm 里的 `filemap.c` [【跳转到 56:51】](https://www.bilibili.com/video/BV1r24y157gm/?t=3411)。也就是说，读回来的页先落进页缓存，VFS 再把页里的内容交给用户缓冲——这也解释了为什么 FUSE 文件系统同样能享受页缓存的加速。

### 5.3 守护进程那一侧：一个循环、一次分发

前面一直在讲内核。回到用户态，守护进程到底在跑什么？讲者用 libfuse 的 hello 例子给了两条调用链 [【跳转到 22:10】](https://www.bilibili.com/video/BV1r24y157gm/?t=1330)：

![HLI 与 LLI 的调用链对比：左边 high-level 走 main → fuse_main → fuse_main_real → fuse_setup 与 fuse_loop_mt → fuse_loop_start_thread → fuse_do_work；右边 low-level 走 main → fuse_mount → fuse_lowlevel_new → fuse_session_loop → fuse_session_receive_buf 与 fuse_session_process_buf](assets/FUSE%20请求路径剖析——一次%20read%20如何穿过%20VFS%20与%20dev-fuse/01330.webp)

两条链的末端是同一对函数，这就是守护进程的「心跳」：

- **`fuse_session_receive_buf`**：内部就是一次 `read(/dev/fuse)`。没请求就阻塞，有请求就把字节读进缓冲区。
- **`fuse_session_process_buf`**：解析缓冲区里的 `fuse_in_header`，**看 opcode**，然后分发到对应的 low-level 回调。

讲者说得很直白：`process_buf` 里「比较重要的一点是要看 opcode」，因为「刚才传进去的、你要做的文件操作，实际上都放在 `in->opcode` 里」[【跳转到 30:29】](https://www.bilibili.com/video/BV1r24y157gm/?t=1829)。分发之后，回调执行完就 `reply`——回程从这里开始。

顺带一个能印证读路径的细节：hello 这个例子**只实现了 `open` 和 `read`，没有实现 `write`**，所以讲者展示分发代码时 write 那一支是灰的 [【跳转到 30:54】](https://www.bilibili.com/video/BV1r24y157gm/?t=1854)。换句话说，一个最小的 FUSE 文件系统只需要实现「打开 + 读」就能跑起来——这也从侧面说明读路径是整条链路上最先必须打通的一段。

## 六、数据面的另一条路：splice 与零拷贝

基本的收发方式很朴素：守护进程从 `/dev/fuse` `read()` 请求，再 `write()` 回响应。讲者指出问题所在：**每次这样的调用都会有一次内核和用户空间之间的内存拷贝**，而 `WRITE` 请求和 `READ` 响应恰恰经常处理大量数据 [【跳转到 14:17】](https://www.bilibili.com/video/BV1r24y157gm/?t=857)。

![Splicing 与 FUSE buffers：基本设置下每次 read/write 都有一次内核与用户空间的内存拷贝；splice 允许在两个 in-kernel memory 之间传数据而不拷到用户空间，FUSE 的 buffer 因此有两种形态](assets/FUSE%20请求路径剖析——一次%20read%20如何穿过%20VFS%20与%20dev-fuse/00857.webp)

splice 的思路是：在**两个内核内的内存**之间搬数据，不经过用户空间。为此 FUSE 的 buffer 要支持两种形态：

- 用户 daemon 地址空间里的普通内存（传统方式）；
- 通过**文件描述符指向的内核空间内存**（splice 方式）。

于是守护进程可以选择用 `write_buf()` 这类接口：FUSE 把来自 `/dev/fuse` 的数据拼好，直接以「fd 指向的内核 buffer」形式交给它，中间不做用户态拷贝。

讲者也给了这条路的**适用边界**：splice 以页为单位操作，如果你的读写是随机小 IO，用它效果可能还不如普通读写；它对大量连续数据才真正有益 [【跳转到 15:07】](https://www.bilibili.com/video/BV1r24y157gm/?t=907)。这跟其他零拷贝机制的取舍是一样的——省的是拷贝，代价是粒度变粗。

## 七、libfuse 的两级 API：你写的那一层在哪

前面一直在讲内核。回到用户态，守护进程通常不直接跟 `/dev/fuse` 打交道，而是基于 libfuse。libfuse 提供**两级 API** [【跳转到 12:37】](https://www.bilibili.com/video/BV1r24y157gm/?t=757)：

![Library and API levels：低级 API 负责接收解析内核请求、发送格式正确的响应、配置挂载、屏蔽 kernel 与 user 间的版本差异；高阶 API 构建在低级 API 之上，没有 inode 与 lookup，用 chmod/chown 代替 setattr](assets/FUSE%20请求路径剖析——一次%20read%20如何穿过%20VFS%20与%20dev-fuse/00757.webp)

- **low-level API**（`fuse_lowlevel_ops`）：直接面对协议。你拿到的是 `fuse_req_t`、`nodeid`、`fuse_ino_t`，要自己管 inode 生命周期、自己回 `fuse_reply_*`。它负责四件事：接收和解析内核请求、发送格式正确的响应、方便地配置和挂载、**屏蔽 kernel 与 user 之间的版本差异**。
- **high-level API**（`fuse_operations`）：构建在 low-level 之上，让你忽略 path-to-inode 映射。所以它**既没有 inode 也没有 lookup**，直接对文件路径操作；也**没有 setattr**，而是用更通用的 `chmod()`、`chown()`。

讲者用 libfuse 自带的 hello 例子做了对照：同一个文件系统有 high-level 和 low-level 两份实现，函数名几乎一一对应（`getattr`、`readdir`、`open`、`read`），差别就在 high-level 少了 `lookup` 和 `setattr` [【跳转到 22:59】](https://www.bilibili.com/video/BV1r24y157gm/?t=1379)。

关键的一点是：**即使你写的是 high-level，运行时也会先落到 low-level**。讲者说「即使我们设计的是 high-level 接口，它其实也会先走 low-level 接口，先走到 low-level 才会调到你 high-level 的那个点」[【跳转到 55:11】](https://www.bilibili.com/video/BV1r24y157gm/?t=3311)。所以读源码时从 `fuse_lowlevel_ops` 入手，能覆盖两种写法。

选哪一级？讲者的结论是「平衡灵活性和开发难易程度」：high-level 上手快、符合上层应用直觉；low-level 能做 inode 级优化、能控制每一个请求。作为设计者，最好把 low-level 那条线也了解一遍。

## 八、代价与观测：这条路径贵在哪

### 8.1 贵在切换和拷贝

把前面几节合起来，一次请求往返的固定成本是：

- **4 次用户态/内核态切换**：请求发出时 2 次（用户进程 → 内核 → 守护进程），响应回来时 2 次（守护进程 → 内核 → 用户进程）。讲者原话是「两次或者四次切换」[【跳转到 03:00】](https://www.bilibili.com/video/BV1r24y157gm/?t=180)。
- **至少 2 次数据拷贝**：请求进读缓冲区一次、响应拷回请求一次；数据面还要再加页拷贝（除非走 splice）。
- **2 个进程的调度**：用户进程睡在 `req->waitq`，守护进程睡在 `fc->waitq`，一次请求就是两次唤醒。

讲者引用了一篇主要讲 FUSE 的论文的测试结果：即使做了优化，性能仍会下降（最高约 83%）；不做优化时开销会扩大到 3 倍 [【跳转到 18:52】](https://www.bilibili.com/video/BV1r24y157gm/?t=1132)。他补了一句限定：换个测试背景结论可能不同，但「性能确实受到了很大影响」。

### 8.2 观测点

讲者点到的几个可观测位置，正好对应前面讲的结构：

| 想看什么 | 看哪里 | 对应结构 |
| :--- | :--- | :--- |
| 有几个连接、各自 id | `/sys/fs/fuse/connections/` | `fuse_sysfs_init` 建的 connections 目录 |
| 队列里积压多少请求 | 同上目录下的计数 | `pending` / `background` 队列长度 |
| 后台请求上限与拥塞阈值 | 同上 | `max_background`（默认 12）、`congestion_threshold`（默认 9） |
| 挂载参数与类型 | `/proc/self/mountinfo` | `mount -t fuse.<name>` 的记录 |
| 想临时掐掉某些请求 | fusectl 控制文件系统 | 讲者提到它可以「临时把一些请求 abort 掉」 |

最后一行是讲者在介绍内核文档时提到的：FUSE 有一个 control 文件系统（fusectl），可以临时把请求 abort 掉，相当于一些小开关 [【跳转到 05:44】](https://www.bilibili.com/video/BV1r24y157gm/?t=344)。

## 小结

- **FUSE 的内核部分只是代理**：`fuse.ko` 注册到 VFS，自己不实现文件系统，只把 VFS 调用翻译成 FUSE 协议请求。
- **挂载决定一切**：`mount` → `do_new_mount` → `vfs_get_tree` → `fuse_mount` → `fuse_fill_super`，在这里建好 `super_block`、`fuse_conn`、队列、根 inode，并发出第一条 `FUSE_INIT` 完成协议协商。
- **请求 = 头 + 参数**：头里有 `opcode`（43 种）、`nodeid`（哪个 inode）、`unique`（哪个请求）；`OPEN` 之后多一个 `fh`（哪一次打开）。
- **五个队列一条规则**：interrupt > forget > processing/pending/background；一个请求任何时刻只在一个队列里；pending 空时守护进程阻塞在 `read` 上。
- **一次 read 的往返**：VFS → `fuse_file_read_iter`/`fuse_read` → 入 pending、唤醒 `fc->waitq` → 守护进程 `read(/dev/fuse)` 取走、转 processing → 执行回调 → `write(/dev/fuse)` → 内核按 `unique` 找回请求、`fuse_copy_pages` 拷数据、唤醒 `req->waitq`。
- **贵在两次切换与两次拷贝**：往返 4 次上下文切换、至少 2 次拷贝；splice 能省掉用户态拷贝，但对随机小 IO 不划算。
- **两级 API 一条路**：high-level 最终也会落到 low-level，读源码从 `fuse_lowlevel_ops` 入手最省力。

## 关键术语速查

| 术语 | 一句话解释 |
| :--- | :--- |
| `fuse.ko` | 内核模块，向 VFS 注册 FUSE 文件系统类型，充当用户态实现的代理 |
| `/dev/fuse` | 混杂设备，内核与守护进程之间唯一的通信接口 |
| `fusermount` | 挂载工具，负责把目标目录挂到 FUSE 文件系统上 |
| `fuse_conn` | 一条挂载连接的总控结构，持有队列、后台请求计数、拥塞阈值、最大页数 |
| `fuse_iqueue` | 输入侧队列集合，含 pending、forget、interrupt |
| `fuse_pqueue` | 处理侧队列，含 processing 与 background |
| `fuse_in_header` | 请求头：至少包含 `opcode`、`unique`、`nodeid` 三个关键字段 |
| `fuse_out_header` | 响应头：带回同一个 `unique`，内核据此定位是哪条请求的响应 |
| `nodeid` | 64 位无符号整数，内核与用户空间用它标识 inode |
| `fh` | 文件句柄，`OPEN` 时由守护进程分配，此后该文件的请求都带着它 |
| `unique` | 内核分配的 64 位请求序号，响应带回同一个值以定位请求 |
| `max_background` | pending 队列里允许驻留的异步请求上限，默认 12 |
| `congestion_threshold` | 拥塞阈值，默认是 `max_background` 的 75%，即 9 |
| `fuse_simple_request` | 元数据类请求的统一入口：取请求、填参数、发送、等待、归还 |
| `request_wait_answer` | 内核侧等待响应的函数，睡在 `req->waitq` 上 |
| `fuse_copy_pages` | 读写路径上统一的页拷贝收口 |
| splice | 在两个内核内存之间搬数据的零拷贝机制，避免拷到用户空间 |
| `fuse_lowlevel_ops` | libfuse 的低级接口，直接面对协议与 inode |
| `fuse_operations` | libfuse 的高级接口，按路径操作，没有 lookup 与 setattr |
