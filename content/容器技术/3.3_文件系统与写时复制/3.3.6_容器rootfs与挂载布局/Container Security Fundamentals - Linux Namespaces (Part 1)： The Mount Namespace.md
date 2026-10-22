# 容器与挂载命名空间：在主机上直接看穿容器的 rootfs 与挂载布局

> 视频来源：YouTube 视频 [Container Security Fundamentals - Linux Namespaces (Part 1): The Mount Namespace](https://www.youtube.com/watch?v=BwI89OnYm-4)（Datadog Security Labs，主讲 Rory McCune，约 8 分 30 秒，英文讲解）。本文基于视频演说图文稿整理，时间戳可跳转到原视频对应位置；配图取自视频画面。字幕来自平台自动字幕（英文 ASR），术语与错拼已逐窗口核对纠正。
>
> 配套阅读：想先理解"容器 rootfs 是怎么从零手工搭出来的"，见[《从零构建容器文件系统：chroot、rootfs 与命名空间》](Docker%20Tutorial：%20Build%20a%20Container%20Filesystem%20From%20Scratch%20%28chroot%2C%20RootFS%20%26%20Namespaces%29.md)；想理解容器可写层与镜像层如何合成一个视图，见[《从零看懂容器文件系统：OverlayFS 如何用 lower/upper/merged 搭出容器 rootfs》](../3.3.2_OverlayFS结构/Docker%20Storage%20Deep%20Dive：%20How%20OverlayFS%20Builds%20Container%20Filesystems.md)。

## 本讲要解决的核心问题（SCQA）

**背景**：上一集我们讲清了一个事实——**容器本质上就是一组被隔离的普通进程**。把它们和主机、和其他容器隔开的，是一整套 Linux 内核机制。

**冲突**：可是在容器里敲一条 `ls /`，我们看到的是一个**完整、独立、属于自己的 Linux 文件系统**（有 `/bin`、`/etc`、`/home` …）。而事实上这台机器上**所有容器共用一个内核、一块磁盘**——那进程凭什么"看到"一套**只属于自己的文件系统与挂载点**？

**疑问**：容器的根文件系统（**rootfs**）到底**挂在哪里、由什么挂起来**？不借助 `docker` 命令，我们能不能**直接用 Linux 自带工具**把它看穿？

**回答（中心思想）**：靠 **mount namespace（挂载命名空间）**。它让每个容器拥有**独立的一套挂载表**，容器的 rootfs 默认就是一块来自 `/var/lib/docker/overlay2` 的 **overlay 挂载**。而用 `lsns`、`findmnt -N <pid>`、`/proc/<pid>/mountinfo`、`nsenter --mount` 这几个标准工具，我们**完全可以在主机上直接查看一个容器的挂载布局**，连 Docker 工具都不需要。[【跳转到 00:11】](https://www.youtube.com/watch?v=BwI89OnYm-4&t=11)

---

## 一、先认识"容器隔离全家桶"：命名空间只是其中一层

容器不是靠单一机制实现隔离的，而是一组内核能力**叠加**起来的结果。这张图把它们列在一起：[【跳转到 00:41】](https://www.youtube.com/watch?v=BwI89OnYm-4&t=41)

![容器隔离的层层机制：SECCOMP、AppArmor/SELinux、CGROUPS、CAPABILITIES、NAMESPACES、PROCESS](assets/Container%20Security%20Fundamentals%20-%20Linux%20Namespaces%20%28Part%201%29：%20The%20Mount%20Namespace/00041.webp)

从下往上看，一个进程被一路"层层设卡"：

- **PROCESS**：最底层——容器就是进程；
- **NAMESPACES（命名空间）**：决定进程**能看到哪些资源**（本讲重点）；
- **CAPABILITIES（能力）**：把 root 的超级权限拆成细粒度的小权限；
- **CGROUPS**：限制进程能用多少 CPU、内存等资源；
- **AppArmor / SELinux**：强制访问控制；
- **SECCOMP**：过滤进程能发起哪些系统调用。

本讲聚焦其中的**命名空间**。一句话概括它的作用：**命名空间为进程提供一份"隔离的资源视图"**——同一台主机上的资源，在不同的命名空间里，"看起来"是不同的。

## 二、Linux 一共 8 种命名空间，Docker 默认启用其中 6 种

所谓"隔离的资源视图"，是**按资源类别**分开做的，所以命名空间有**多种类型**。到了本讲的版本，Linux 一共有 **8 种**命名空间：[【跳转到 00:41】](https://www.youtube.com/watch?v=BwI89OnYm-4&t=41)

![Linux 命名空间类型：mnt、pid、net、uts、ipc、cgroup、user、time](assets/Container%20Security%20Fundamentals%20-%20Linux%20Namespaces%20%28Part%201%29：%20The%20Mount%20Namespace/00066.webp)

它们各自"隔离"的对象，以及 Docker 是否默认开启，可以整理成下表：

| 命名空间 | 隔离的对象 | Docker 默认 |
| --- | --- | --- |
| **mnt**（mount） | 文件系统挂载点 / 挂载表（本讲主角） | ✅ 启用 |
| **pid** | 进程号（PID），让容器内看到自己的 PID 1 | ✅ 启用 |
| **net** | 网络接口、路由表、端口 | ✅ 启用 |
| **ipc** | 进程间通信（共享内存、信号量） | ✅ 启用 |
| **uts** | 主机名与域名 | ✅ 启用 |
| **cgroup** | cgroup 视图 | ✅ 启用 |
| **user** | 用户与 UID/GID 映射 | ❌ 可启用但默认不启用 |
| **time** | 系统时钟（`/proc/uptime` 等） | ❌ 最新，容器内**尚不可用** |

要点有两个：**Docker 默认开启 mnt、net、pid、ipc、uts、cgroup 这 6 种**；**user** 命名空间需要手动启用、默认是关的；**time** 是最新加入的一种，目前容器里还用不上。[【跳转到 01:06】](https://www.youtube.com/watch?v=BwI89OnYm-4&t=66)

## 三、用 `lsns` 观察：命名空间并不是容器的"专利"

要在主机上看命名空间，最直接的工具是 **`lsns`**——它把机器上的所有命名空间列成一张表：[【跳转到 01:31】](https://www.youtube.com/watch?v=BwI89OnYm-4&t=91)

![sudo lsns 输出：NS 号、类型、NPROCS（使用该命名空间的进程数）、PID、USER、COMMAND](assets/Container%20Security%20Fundamentals%20-%20Linux%20Namespaces%20%28Part%201%29：%20The%20Mount%20Namespace/00141.webp)

在**还没跑任何容器**的情况下，这张表就透露了两件事：

- **绝大多数进程共享同一套命名空间**（看 `NPROCS` 列——它是"有多少个进程正在使用这一组命名空间"，主机的编号一般是几百）。这符合预期：一台普通主机上的进程，默认并不需要隔离。
- **但确实有些进程已经在用命名空间了**：可以看到部分**系统守护进程（systemd daemons）**给**自己**隔离出了 **mnt** 和 **uts** 命名空间。

这说明一个关键认知：**命名空间不是 docker 专属、也不是容器专属的技术**。容器只是**大量、系统性地**把这套内核能力用到了极致——它本质上是在"借"内核早就提供的公开能力，而不是发明了什么黑魔法。[【跳转到 02:46】](https://www.youtube.com/watch?v=BwI89OnYm-4&t=166)

## 四、跑起一个容器，再对照一次 `lsns`

现在启动一个普通的 nginx 容器，然后**重新执行 `lsns`**：[【跳转到 03:11】](https://www.youtube.com/watch?v=BwI89OnYm-4&t=191)

![启动容器后 lsns 的新变化：底部多出一组属于该容器的命名空间](assets/Container%20Security%20Fundamentals%20-%20Linux%20Namespaces%20%28Part%201%29：%20The%20Mount%20Namespace/00201.webp)

对比上一张图，最明显的变化是**列表底部多出了一组全新的命名空间**——它们就是刚刚为这个 Docker 容器创建的。

Docker 是在**后台悄悄**完成这件事的：它把这批 nginx 进程塞进一组**它们自己的命名空间**里，于是这些进程只能看到一份**被隔离的资源视图**。底部这一组命名空间的类型正是前面说的默认六件套：**mnt、uts、ipc、pid、net、cgroup**；而 **user 与 time 没有出现**——因为它们默认不启用，这也和第二节的表对上了。[【跳转到 03:21】](https://www.youtube.com/watch?v=BwI89OnYm-4&t=201)

## 五、深入 mount namespace：容器的 rootfs 到底挂在哪

接下来专门看 **mount 命名空间**——也就是决定容器"能看到哪些挂载点"的那一层。要看它，得先拿到**容器进程的 PID**：

```bash
docker inspect web-server        # 找出该容器的 Pid，例如 2607
```

> 这个 PID 会随着你机器上运行的进程数量而变，视频里是 2607，你机器上可能不同。[【跳转到 04:09】](https://www.youtube.com/watch?v=BwI89OnYm-4&t=249)

拿到 PID 后，用 **`findmnt -N <pid>`** 读取**该进程所在命名空间的挂载表**（`-N/--task` 的作用就是"改用 `/proc/<tid>/mountinfo`"）：[【跳转到 04:34】](https://www.youtube.com/watch?v=BwI89OnYm-4&t=274)

![findmnt -N 2607 输出：根挂载是一块 overlay，来自 /var/lib/docker/overlay2/l/…](assets/Container%20Security%20Fundamentals%20-%20Linux%20Namespaces%20%28Part%201%29：%20The%20Mount%20Namespace/00322.webp)

一眼能看到的结果：**容器的根文件系统（`/`）是一块 `overlay` 挂载**，来源写着 `lowerdir=/var/lib/docker/overlay2/l/…`。也就是说，**容器的 rootfs 是被 overlay 驱动"拼"出来后挂到容器命名空间的根上的**。（overlay 是如何拼出这套目录的，见文首配套的 OverlayFS 一篇。）

这里还引出一个**安全要点**：`/var/lib/docker` 目录**默认存放了所有 Docker 容器与镜像的全部文件**。所以**控制、审计对它的访问权限非常重要**——它能被改动，就等于所有容器与镜像都能被改动。不同实现下具体路径可能略有不同，用 `findmnt` 就能确认它到底在哪；本例用的就是默认位置 `/var/lib/docker`。[【跳转到 05:22】](https://www.youtube.com/watch?v=BwI89OnYm-4&t=322)

同样的信息还有另一种读法——直接读 **`/proc/<pid>/mountinfo`**：

```bash
sudo cat /proc/2607/mountinfo
```

它和 `findmnt` 给的是**同一份内容，只是格式不同、细节更多**。从中更容易看清：**组成这个容器根挂载的一堆目录，全部落在 `/var/lib/docker/overlay2` 里**。[【跳转到 06:08】](https://www.youtube.com/watch?v=BwI89OnYm-4&t=368)

![/proc/2607/mountinfo：/proc、/dev(/dev/pts)、/sys 等条目与它们的挂载选项](assets/Container%20Security%20Fundamentals%20-%20Linux%20Namespaces%20%28Part%201%29：%20The%20Mount%20Namespace/00383.webp)

这张图里还能读到几个**典型的容器挂载点**——`/proc`、`/dev`、`/dev/pts`、`/sys` 等都有各自的挂载项与选项（比如 `ro`、`nosuid`、`nodev`、`noexec`）。前面提过的"**`proc` 被挂进了容器**"就是在这里体现的：这些都不是新内核造出来的，而是 **Docker 在容器命名空间内**替我们挂好的。[【跳转到 05:47】](https://www.youtube.com/watch?v=BwI89OnYm-4&t=347)

## 六、用 `nsenter` 直接"钻进"容器的挂载命名空间

最后再介绍一个能和命名空间交互的利器：**`nsenter`**。它的作用是**进入某个进程所属的命名空间去执行命令**。想进容器的 mount 命名空间，这样写：[【跳转到 06:50】](https://www.youtube.com/watch?v=BwI89OnYm-4&t=410)

```bash
sudo nsenter --target 2607 --mount ls /
```

- `--target 2607`：以进程 2607 为"入口"；
- `--mount`：进入它的 **mount 命名空间**；
- `ls /`：进去以后要执行的命令。

执行结果，就是**容器自己的根文件系统**：[【跳转到 07:20】](https://www.youtube.com/watch?v=BwI89OnYm-4&t=440)

![nsenter --target 2607 --mount ls / 输出：容器 rootfs 的目录（bin、dev、docker-entrypoint.sh、home、lib、media、mnt、opt、proc、root、run、sbin、srv、sys、tmp、usr、var 等）](assets/Container%20Security%20Fundamentals%20-%20Linux%20Namespaces%20%28Part%201%29：%20The%20Mount%20Namespace/00465.webp)

可以看到里面是**容器镜像自带的那套目录树**（例如 nginx 镜像特有的 `docker-entrypoint.sh`、`docker-entrypoint.d`）。这条路径的意义在于：**要检查一台机器上的某个容器，你不一定非得用 Docker 工具**——`nsenter` 这类标准 Linux 工具就能直接进去看。凡是使用命名空间的东西，都能用同样的手法访问。[【跳转到 07:20】](https://www.youtube.com/watch?v=BwI89OnYm-4&t=440)

## 小结

- 容器隔离是**一组内核机制叠加**的结果：进程之上依次是命名空间、能力（capabilities）、cgroups、AppArmor/SELinux、seccomp，命名空间只是其中一层。
- **命名空间 = 给进程一份隔离的资源视图**，按资源类别分型；Linux 共 **8 种**，Docker **默认启用 6 种**（mnt、net、pid、ipc、uts、cgroup），**user 需手动开启**，**time 最新且容器内尚不可用**。
- 用 **`lsns`** 可以看到：命名空间**不是容器的专利**，系统守护进程早就在用了；启动容器后，列表底部会**多出一组属于该容器的命名空间**。
- **mount 命名空间**决定容器能看到哪些挂载点。容器的 **rootfs 默认是一块来自 `/var/lib/docker/overlay2` 的 overlay 挂载**；`/var/lib/docker` 存放所有容器与镜像数据，**其访问控制与审计是安全重点**。
- 查看容器挂载布局的三种工具：**`findmnt -N <pid>`**、**`cat /proc/<pid>/mountinfo`**、**`nsenter --target <pid> --mount`**——**不依赖 Docker 命令**即可在主机上检查容器。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| namespace（命名空间） | 内核给进程的"隔离资源视图"，按资源类别分型 |
| mount namespace（mnt） | 隔离挂载表，让容器拥有独立的文件系统挂载布局 |
| rootfs | 容器的根文件系统，容器进程看到的 `/` |
| `lsns` | 列出主机上所有命名空间及其使用进程数的工具 |
| `findmnt -N <pid>` | 按进程读取其命名空间的挂载表（读 `/proc/<pid>/mountinfo`） |
| `/proc/<pid>/mountinfo` | 某进程可见的所有挂载的内核原始清单 |
| `nsenter --target <pid> --mount` | 进入某进程的挂载命名空间执行命令 |
| `/var/lib/docker` | Docker 默认存放所有镜像与容器数据的目录 |
| overlay2 | Docker 默认存储驱动，负责拼出容器 rootfs 的目录视图 |
