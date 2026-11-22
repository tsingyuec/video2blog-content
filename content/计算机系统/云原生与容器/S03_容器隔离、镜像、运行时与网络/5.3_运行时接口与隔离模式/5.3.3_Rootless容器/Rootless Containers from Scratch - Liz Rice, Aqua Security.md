# 从零手写一个无根容器：33 分钟看懂用户命名空间

> 视频源：[Rootless Containers from Scratch - Liz Rice, Aqua Security](https://www.youtube.com/watch?v=jeTKgAEyhsA)（YouTube / KubeCon，33 分 31 秒）。本文基于视频演说图文稿整理，时间戳可跳转到原视频对应位置。

## 本讲要解决的核心问题（SCQA）

**背景**：默认情况下，容器里的进程是以 **root** 运行的——你去用 Docker 或 Kubernetes，只要没显式指定用户，跑的就是 root。而且这不只是「容器里的 root」：**它和宿主机上的 root 是同一个 root**。[【跳转到 00:30】](https://www.youtube.com/watch?v=jeTKgAEyhsA&t=30)

**冲突**：讲者一直在谈「以 root 权限运行容器很危险」，但大多数人只听到结论，看不到原因，更不知道**怎么才能不 root**。危险在于：能跑容器就等于有 root，这在多用户机器上是真问题——比如一台大学共享机器，很多学生通过 SSH 连上来，管理员根本不会允许学生跑 Docker，因为他们可以轻松拿到整机的 root。[【跳转到 04:08】](https://www.youtube.com/watch?v=jeTKgAEyhsA&t=248)

**疑问**：那么，一个**不依赖 root 的容器**到底需要哪些零件？如果从零开始写，最小实现是什么？

**回答（中心思想）**：讲者用**约 60 行 Go 代码**，一步一步加内核特性，最终以 **UID 1000 的普通用户**身份跑出一个「看起来像 Alpine、只看得见自己进程」的容器。整条路径是：**UTS 命名空间 → 用户命名空间 → UID 映射 → mount/PID 命名空间 → chroot → 挂载 `/proc`**。其中**用户命名空间是那颗定盘星**——它让非特权进程先在「自己的世界」里变成 root，再用这份权限去创建其它命名空间。[【跳转到 01:18】](https://www.youtube.com/watch?v=jeTKgAEyhsA&t=78)

---

## 一、为什么默认的容器是危险的：里面的 root 就是外面的 root

### 1.1 一个两窗口实验

讲者在一台虚拟机上开了两个窗口。启动一个 Alpine 容器，在里面查看自己的身份：

```bash
docker run -it alpine sh
id          # uid=0(root) gid=0(root)
```

![容器里 `id` 显示 root——但故事还没结束](<assets/Rootless Containers from Scratch - Liz Rice, Aqua Security/00100.webp>)

你可能会想：这是**容器里面**，有什么要紧？那就从**宿主机**的角度再看一次。在容器里起一个长睡眠进程，然后在宿主机上找它：

```bash
# 容器内
sleep 1000
# 宿主机上
ps -ef | grep sleep
```

结果很关键：这个 sleep 进程**在宿主机视角下也是 root 运行的**——不是「容器内的 root」，两者**完全等同**。[【跳转到 02:28】](https://www.youtube.com/watch?v=jeTKgAEyhsA&t=148)

当然，你可以用 `-u` 指定用户，或是在 Dockerfile 里用 `USER` 指令——但**默认就是 root**。补充一点：这并不适用于所有容器运行时，比如 Red Hat 的 Podman 默认就不以 root 运行。[【跳转到 02:53】](https://www.youtube.com/watch?v=jeTKgAEyhsA&t=173) · [【跳转到 03:18】](https://www.youtube.com/watch?v=jeTKgAEyhsA&t=198)

### 1.2 「能用 docker」约等于「有 root」

另一个窗口里，讲者是以用户名 `vagrant`、用户 ID 1000 运行的**非 root 用户**，却能直接执行 `docker` 命令。

Docker 文档里其实有一条警告：你之所以能跑 Docker，是因为你被加进了 **docker 组**。而**只要你能运行容器，容器默认就以 root 运行，且这个 root 就是宿主机的 root**。也就是说：**身为 docker 组成员，你实际上拥有 root 权限**。[【跳转到 03:43】](https://www.youtube.com/watch?v=jeTKgAEyhsA&t=223)

![「能跑 docker」的真实含义：docker 组 ≈ root 权限](<assets/Rootless Containers from Scratch - Liz Rice, Aqua Security/00273.webp>)

这在**多用户环境**里是实打实的问题。视频举的例子是大学共享机器：管理员不会让学生用 Docker，因为学生可以借此轻易拿到整个系统的 root。

**这正是无根容器出现的首要原因**——让人能以普通用户身份运行容器。[【跳转到 04:33】](https://www.youtube.com/watch?v=jeTKgAEyhsA&t=273)

---

## 二、无根容器其实是两件事

很多人把「无根」当成一件事，其实是**两个层面**：

![无根容器的两个层面：能作为普通用户运行容器 + 容器里的 root 不等于宿主机的 root](<assets/Rootless Containers from Scratch - Liz Rice, Aqua Security/00323.webp>)

1. **能以普通用户身份运行容器**。Docker 通过 **rootless mode** 支持了这一点（讲者视频录制时它还是实验特性）；
2. **能让容器里的进程「以为」自己是 root，而这个 root 并不等于宿主机的 root**。

[【跳转到 04:58】](https://www.youtube.com/watch?v=jeTKgAEyhsA&t=298) · [【跳转到 05:23】](https://www.youtube.com/watch?v=jeTKgAEyhsA&t=323)

在动手写之前，还需要先补一块地基。

---

## 三、先补地基：命名空间

**命名空间（namespace）限制的是一个进程能「看见」什么。** 视频用两个例子解释：

- **PID 命名空间**：如果给容器一个自己的 PID 命名空间，它就**只能看见自己的进程**，看不到系统里其余进程与 ID；
- **UTS 命名空间**（Unix Time Sharing）：可以给容器一个**独立的主机名**，与宿主机名互不影响。

而这一堆命名空间里有一个叫 **user ID namespace（用户命名空间）** 的——**它就是用来创建无根容器的那个**。[【跳转到 06:13】](https://www.youtube.com/watch?v=jeTKgAEyhsA&t=373) · [【跳转到 06:38】](https://www.youtube.com/watch?v=jeTKgAEyhsA&t=398)

![命名空间家族中的一个特殊成员：用户命名空间](<assets/Rootless Containers from Scratch - Liz Rice, Aqua Security/00398.webp>)

讲者的讲法是：先用最简单的 UTS 命名空间做出一个「有点像容器」的东西，再一步步加上去。

---

## 四、从零开始：一个能执行任意命令的程序

讲者写了一个 Go 程序，它的行为刻意模仿 `docker`：

```bash
go run main.go run <命令> [参数...]
```

- 整体相当于一个 `docker` 可执行文件；
- 第一个参数是子命令，比如 `run`（`docker run image cmd args...` 的简化版）；
- 用户可以从第二个参数开始，传入任意想执行的命令与参数。

第一版程序只做两件事：**打印它被调用时收到的参数**，以及**打印自己的有效用户 ID（euid）与进程 ID**。

```bash
go run main.go run echo hello
# 打印参数；显示运行在 user ID 1000（vagrant）；进程 ID 很大
```

接着让它**真的执行**任意命令：构造 `exec.Cmd` 结构描述要跑的命令，把 **stdin、stdout、stderr 都接上**，然后 `Run()`——这会创建一个新进程去执行我们传进来的命令。[【跳转到 10:12】](https://www.youtube.com/watch?v=jeTKgAEyhsA&t=612) · [【跳转到 11:27】](https://www.youtube.com/watch?v=jeTKgAEyhsA&t=687)

```bash
go run main.go run echo hello
# 我们看到 hello 被打印出来
```

此时**完全没有任何容器化**，只是一个「能执行任意命令」的程序——地基打好了。

---

## 五、加第一个命名空间：UTS，然后撞墙

在 Go 里给**子进程**创建命名空间，靠的是 `SysProcAttr` 的 `Cloneflags` 字段：告诉它在 clone 新进程时使用哪些标志。第一站是 **UTS 命名空间**（可以独立改主机名）。[【跳转到 12:17】](https://www.youtube.com/watch?v=jeTKgAEyhsA&t=737)

```go
cmd.SysProcAttr = &syscall.SysProcAttr{
    Cloneflags: syscall.CLONE_NEWUTS,
}
```

以普通用户运行——**失败了**：

```
operation not permitted
```

因为**没有相应权限，就不被允许创建 UTS 命名空间**。用 `sudo` 变成 root 再跑，一切正常：能起 shell、能改主机名。在容器里把主机名改成 `container`，宿主机上仍然是 `host`——**这是迈向容器化的第一步**，但代价是**只能用 root 做**。[【跳转到 12:42】](https://www.youtube.com/watch?v=jeTKgAEyhsA&t=762) · [【跳转到 13:57】](https://www.youtube.com/watch?v=jeTKgAEyhsA&t=837) · [【跳转到 14:22】](https://www.youtube.com/watch?v=jeTKgAEyhsA&t=862)

---

## 六、用户命名空间：非特权进程的「自封 root」

救命的东西来了：查用户命名空间的说明会发现，**非特权进程可以创建用户命名空间**——不需要是 root。[【跳转到 14:52】](https://www.youtube.com/watch?v=jeTKgAEyhsA&t=892) · [【跳转到 14:57】](https://www.youtube.com/watch?v=jeTKgAEyhsA&t=897)

机制是：在**新的用户命名空间里**创建一个子进程，这个子进程就获得**完整的一套 capabilities**，**可以在该用户命名空间里扮演 root**。

**创建顺序极其关键**：

![顺序很重要：先建用户命名空间，之后才能创建其它命名空间](<assets/Rootless Containers from Scratch - Liz Rice, Aqua Security/00922.webp>)

```go
Cloneflags: syscall.CLONE_NEWUTS | syscall.CLONE_NEWUSER,
```

- 之前程序失败，是因为「没有权限创建 UTS 命名空间」；
- 现在**先创建用户命名空间**，之后进程就**可以在新命名空间里创建任意其它命名空间**；
- 于是**用普通用户身份就跑通了**。

[【跳转到 15:22】](https://www.youtube.com/watch?v=jeTKgAEyhsA&t=922) · [【跳转到 15:47】](https://www.youtube.com/watch?v=jeTKgAEyhsA&t=947) · [【跳转到 16:12】](https://www.youtube.com/watch?v=jeTKgAEyhsA&t=972)

但新问题出现了：虽然是以 1000 运行的，进容器后 `id` 显示的是——

```
nobody
```

[【跳转到 16:50】](https://www.youtube.com/watch?v=jeTKgAEyhsA&t=1010)

原因在于创建用户命名空间时发生的 **ID 映射**。

---

## 七、UID 映射：把宿主机的 1000 映射成容器里的 0

![用户命名空间的 ID 映射示意：把宿主机的 1000 映射到新命名空间里的 0](<assets/Rootless Containers from Scratch - Liz Rice, Aqua Security/01053.webp>)

创建新用户命名空间时，我们可以**在宿主机与新命名空间之间映射用户 ID**。如果我想在新空间里当 root，就需要为宿主机上的用户配置映射：**从 1000（vagrant 这个用户）开始，取一段长度**。[【跳转到 17:15】](https://www.youtube.com/watch?v=jeTKgAEyhsA&t=1035) · [【跳转到 17:33】](https://www.youtube.com/watch?v=jeTKgAEyhsA&t=1053)

`SysProcAttr` 正好提供了一个方便的字段来配置这些映射（就是 runtime spec 里的 UID 映射列表）：

```go
cmd.SysProcAttr = &syscall.SysProcAttr{
    Cloneflags: syscall.CLONE_NEWUTS | syscall.CLONE_NEWUSER,
    UidMappings: []syscall.SysProcIDMap{
        {ContainerID: 0, HostID: 1000, Size: 1},   // 容器内 root ← 宿主机 1000
    },
    GidMappings: /* 同样拷贝一份、改一个字符 */ []syscall.SysProcIDMap{
        {ContainerID: 0, HostID: 1000, Size: 1},
    },
}
```

要点：**容器内要 root（0），宿主机侧从 1000 来，只需要映射一个 ID，所以 size = 1**。组 ID 映射同理，照着复制一份、改一个字符即可。[【跳转到 18:11】](https://www.youtube.com/watch?v=jeTKgAEyhsA&t=1091) · [【跳转到 18:36】](https://www.youtube.com/watch?v=jeTKgAEyhsA&t=1116) · [【跳转到 19:01】](https://www.youtube.com/watch?v=jeTKgAEyhsA&t=1141)

结果：

```bash
id            # uid=0(root)  ← 宿主机上的 1000 变成了容器里的 0
hostname container   # 不再报错，且不影响宿主机
```

**一个非特权用户（UID 1000），造出了一个有自己的隔离主机名、并且看起来以 root 运行的容器。** 改主机名成功，宿主机不受影响。[【跳转到 19:26】](https://www.youtube.com/watch?v=jeTKgAEyhsA&t=1166) · [【跳转到 19:51】](https://www.youtube.com/watch?v=jeTKgAEyhsA&t=1191)

不过讲者提醒：**这还不算一个完整容器**——第一，它还能看见宿主机文件系统上的所有东西；第二，它还能看见宿主机上所有进程。[【跳转到 20:16】](https://www.youtube.com/watch?v=jeTKgAEyhsA&t=1216)

---

## 八、离「真容器」还差什么：文件系统与进程视图

继续加两个命名空间：**mount 命名空间**与**PID 命名空间**。[【跳转到 21:06】](https://www.youtube.com/watch?v=jeTKgAEyhsA&t=1266)

```bash
# 加了 mount + PID 命名空间之后
ps      # 结果看起来和之前一模一样：还是能看到宿主机所有进程
```

为什么？因为 **`ps` 其实是在读 `/proc` 这个伪目录**：机器上每个运行中的进程都在 `/proc` 下有一个目录，用户 ID 等信息也写在那里。[【跳转到 21:31】](https://www.youtube.com/watch?v=jeTKgAEyhsA&t=1291)

顺着 `/proc` 还能亲眼看到映射：

```bash
# 找到容器内某个进程的 PID，比如 3995
cat /proc/3995/uid_map
#   0       1000        1
```

- 容器内的 0 映射到宿主机的 1000，长度为 1；
- **创建一个用户命名空间时，只有一次机会把这些 ID 映射写进这个文件**——我们的 Go 代码里已经替我们设好了。[【跳转到 22:21】](https://www.youtube.com/watch?v=jeTKgAEyhsA&t=1341) · [【跳转到 22:46】](https://www.youtube.com/watch?v=jeTKgAEyhsA&t=1366)

要让容器里的 `ps` **只看见容器自己的进程**，就得给它**自己的 `/proc`**——而这就意味着要给它**自己的根文件系统**。[【跳转到 23:11】](https://www.youtube.com/watch?v=jeTKgAEyhsA&t=1391) · [【跳转到 23:36】](https://www.youtube.com/watch?v=jeTKgAEyhsA&t=1416)

---

## 九、chroot 与「自我重启」小技巧

讲者手上正好有一份 **Alpine 文件系统**的副本（在 `/home/vagrant/alpine/fs`）。把容器的根切到那里，它就**只能看见那套目录里的文件**——像一份解包好的镜像文件系统。[【跳转到 24:01】](https://www.youtube.com/watch?v=jeTKgAEyhsA&t=1441) · [【跳转到 24:26】](https://www.youtube.com/watch?v=jeTKgAEyhsA&t=1466)

**坑点**：不能直接在当前进程里 `chroot`——那会改掉当前进程的根目录，而我们**只想影响子进程**。讲者的做法是一个小技巧：[【跳转到 24:51】](https://www.youtube.com/watch?v=jeTKgAEyhsA&t=1491) · [【跳转到 25:16】](https://www.youtube.com/watch?v=jeTKgAEyhsA&t=1516)

1. `run` 函数创建一个子进程；
2. 子进程**用 `/proc/self/exe` 重新调用自己**（即当前这个可执行文件），但传入的关键字不是 `run`，而是 **`child`**；
3. 顶层逻辑看关键字分发：`run` → 走 `run`，`child` → 走 `child`。

```go
// run：建命名空间、做 ID 映射、然后跑 child
// child：先 chroot 到 alpine 根，再 chdir("/")，最后执行用户的任意命令
```

在 `child` 里，先 `chroot` 到 Alpine 目录，并且**显式改变当前目录到根**——因为按 chroot 的正确用法，改变根目录后当前目录会处于未定义状态，所以值得显式 `cd` 到根。

跑起来的结果：[【跳转到 28:11】](https://www.youtube.com/watch?v=jeTKgAEyhsA&t=1716) · [【跳转到 28:36】](https://www.youtube.com/watch?v=jeTKgAEyhsA&t=1716) · [【跳转到 29:01】](https://www.youtube.com/watch?v=jeTKgAEyhsA&t=1741)

- **以 root 运行，进程 ID 是 1**——因为我们有自己的进程命名空间，编号从头开始；
- `ls` 来自 `/bin`，而且它其实是 **BusyBox 的符号链接**（Alpine 的典型特征）；
- 根目录内容正好对应 `/home/vagrant/alpine/fs`——**chroot 成功**。

---

## 十、挂上 `/proc`，收工

最后差一步：容器里的 `ps` 还不太好使。只需告诉内核：**把容器里的 `/proc` 当作 proc 类型文件系统挂进来**——内核会把进程信息写进去。[【跳转到 30:16】](https://www.youtube.com/watch?v=jeTKgAEyhsA&t=1816)

```bash
mount -t proc proc /proc
ps          # 现在只看见容器里应有的进程
umount /proc   # 用完卸载清理
```

结果是——[【跳转到 31:06】](https://www.youtube.com/watch?v=jeTKgAEyhsA&t=1866) · [【跳转到 31:31】](https://www.youtube.com/watch?v=jeTKgAEyhsA&t=1891)

**我们以 root 身份运行在一个看起来像 Alpine 文件系统的容器里；在容器里跑 `ps`，只看见容器内该看见的进程。而且这一切是用 UID 1000 这个非特权用户做到的——这就是无根容器。**

---

## 十一、这套东西什么时候能用上

![好消息：Docker 20.10 将让 rootless 模式脱离实验状态](<assets/Rootless Containers from Scratch - Liz Rice, Aqua Security/01925.webp>)

- **Docker**：讲者录制视频时（2020 年 10 月），**Docker engine 20.10 尚未发布**，但 release notes 已经写好——**无根模式预计将脱离实验状态**。等你看的时候，它大概率已经可用了。[【跳转到 32:10】](https://www.youtube.com/watch?v=jeTKgAEyhsA&t=1930)
- **Kubernetes**：社区正在积极推进一项**改进用户命名空间支持**的提案。[【跳转到 32:35】](https://www.youtube.com/watch?v=jeTKgAEyhsA&t=1955)

![延伸资源：rootless-containers 仓库与 containers-from-scratch](<assets/Rootless Containers from Scratch - Liz Rice, Aqua Security/01980.webp>)

想继续深入，讲者给了两个方向：GitHub 上的 **rootless-containers 仓库**（要感谢做了大量工作的 Akihiro Suda），以及讲者自己在 GitHub 上的 **containers from scratch** 系列——那场演讲讲的是「如何创建一个容器」的更多细节。[【跳转到 33:00】](https://www.youtube.com/watch?v=jeTKgAEyhsA&t=1980) · [【跳转到 33:06】](https://www.youtube.com/watch?v=jeTKgAEyhsA&t=1986)

---

## 小结

- **默认容器跑在 root 上，而且就是宿主机的 root**：在容器里起的 `sleep`，在宿主机看来同样是 root。
- **能跑 Docker ≈ 有 root**：Docker 文档会告诉你，这是因为你在 docker 组里；在多用户机器（如大学共享机）上，这就是无根容器出现的首要原因。
- **无根容器是两件事**：① 能以普通用户运行容器；② 容器里的 root 不等于宿主机的 root。
- **地基是命名空间**：它限制进程能看见什么（PID 只管自己的进程，UTS 可以有自己的主机名），而**用户命名空间**是关键的那一个。
- **从零写的顺序**：能执行任意命令的 Go 程序 → 加 UTS 命名空间（普通用户 `operation not permitted`）→ 加**用户命名空间**（非特权进程可创建，且**必须先建它**，之后才能建其它命名空间）→ 配 **UID 映射**（容器 0 ← 宿主机 1000，size 1，靠 `SysProcAttr` 的 UidMappings）→ 加 mount/PID 命名空间 → `chroot` 到 Alpine 根 → 用 `/proc/self/exe` + `child` 关键字重新执行自己 → 挂载 `/proc`。
- **过程中的两个易错点**：不能直接在当前进程 `chroot`（会改掉自己的根，要用子进程 + 重新执行自己）；`/proc` 不换，`ps` 就永远看得见宿主机全部进程。
- **最终成果**：以 **UID 1000** 跑出容器内 PID 为 1、只看得见自己进程与 Alpine 文件系统的容器——**无根容器**。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| rootless container（无根容器） | 不依赖 root 就能创建并运行的容器；容器内的 root 与宿主机 root 不是同一个 |
| namespace（命名空间） | 限制进程能看见什么的内核机制（PID、UTS、mount、network、IPC、user……） |
| UTS namespace | 让进程拥有独立主机名的命名空间 |
| user namespace（用户命名空间） | 让非特权进程在自己内部拥有「root」的命名空间，是无根容器的核心机制 |
| UID 映射（uid_map） | 建立「容器内 ID ↔ 宿主机 ID」的对应表；`/proc/<pid>/uid_map` 可查看，且只能写一次 |
| `SysProcAttr.Cloneflags` | Go 中创建子进程时用来指定创建哪些命名空间的字段 |
| `SysProcAttr.UidMappings` / `GidMappings` | Go 中配置用户/组 ID 映射的字段（对应 runtime spec 的 ID 映射列表） |
| docker 组 | 被加入该组的用户可访问 Docker socket，因而**在效果上拥有 root** |
| rootless mode（Docker） | Docker 官方的无根模式，Docker 20.10 起脱离实验状态 |
| PID namespace | 让容器只看见自己的进程，且进程编号从头开始（容器内常见 PID 1） |
| mount namespace | 让容器拥有独立的挂载视图 |
| `chroot` | 改变进程看到的根目录；正确用法还需显式把当前目录切到新根 |
| `/proc/self/exe` | 指向当前可执行文件的符号链接，用来让程序「重新执行自己」 |
| `/proc`（procfs） | 内核暴露进程信息的伪文件系统；`ps` 的数据来源，容器要单独挂载才会只看见自己 |
| BusyBox | 把大量常用命令塞进单个可执行文件的工具集，Alpine 中 `/bin` 下多为它的链接 |
