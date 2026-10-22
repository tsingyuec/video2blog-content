# 从零构建容器文件系统：chroot、rootfs 与命名空间

> 视频来源：YouTube 视频 [Docker Tutorial: Build a Container Filesystem From Scratch (chroot, RootFS & Namespaces)](https://www.youtube.com/watch?v=1r8feBhPn9E)（Techi Nik，约 17 分钟，英文讲解）。本文基于视频演说图文稿整理，时间戳可跳转到原视频对应位置；配图取自视频画面。字幕来自平台自动字幕（英文 ASR），术语与错拼已逐窗口核对纠正。
>
> 配套阅读：想从**安全与排查**视角看一个真实容器的挂载布局（`lsns` / `findmnt` / `nsenter`），见[《容器与挂载命名空间：在主机上直接看穿容器的 rootfs 与挂载布局》](Container%20Security%20Fundamentals%20-%20Linux%20Namespaces%20%28Part%201%29%EF%BC%9A%20The%20Mount%20Namespace.md)；想理解多个层如何高效合成一个视图，见[《从零看懂容器文件系统：OverlayFS 如何用 lower/upper/merged 搭出容器 rootfs》](../3.3.2_OverlayFS结构/Docker%20Storage%20Deep%20Dive%EF%BC%9A%20How%20OverlayFS%20Builds%20Container%20Filesystems.md)。

## 本讲要解决的核心问题（SCQA）

**背景**：上一集我们**用命名空间隔离了进程**——被隔离的进程活在只属于自己的 PID、网络、主机名视图里。

**冲突**：但只隔离进程**还不够**。一个被隔离的进程，**仍然和主机共用同一个文件系统**——它一眼就能看遍整台机器的文件（你的用户文件、配置、系统数据）。**这还不是容器**。真正的容器，必须拥有一套**只属于自己的文件系统**。

**疑问**：容器那套独立的文件系统（**rootfs**）到底**从哪来**？我们能不能**不装 Docker、不下载任何镜像**，只用 Linux 原语**亲手把它造出来**？

**回答（中心思想）**：可以。本讲从理解 **`/`（根目录）** 开始，用 `mkdir`、`cp`、`ldd`、`chroot`、`unshare` 一步步**手工搭出一个 rootfs**、把它变成进程眼里的"整个文件系统"，再把**进程隔离**加上去。走完这条路你会看到：**容器 = 文件系统 + 进程隔离 + 执行**，而 **Docker 做的正是这同一套流程，只不过它自动化了**。[【跳转到 00:00】](https://www.youtube.com/watch?v=1r8feBhPn9E&t=0)

---

## 一、起点是理解 `/`：进程只认斜杠，不认"主机还是容器"

在动任何东西之前，先想清楚一个符号：**`/`（斜杠）**。

敲一条 `ls /`，会列出一堆目录：`bin`、`boot`、`dev`、`etc`、`home`、`lib`、`media`、`mnt`、`opt`、`proc`、`root`、`run`、`sbin`、`srv`、`sys`、`tmp`、`usr`、`var`。[【跳转到 00:30】](https://www.youtube.com/watch?v=1r8feBhPn9E&t=30)

![`ls /` 列出的根目录：bin、dev、etc、home、lib、proc、sys、usr、var 等](assets/Docker%20Tutorial：%20Build%20a%20Container%20Filesystem%20From%20Scratch%20%28chroot%2C%20RootFS%20%26%20Namespaces%29/00049.webp)

**`/` 不是一个普通目录，它是整个文件系统的起点**。Linux 里每一个路径——`/etc/passwd`、`/usr/bin`——都**从 `/` 开始解析**。这意味着一个关键事实：

> **程序访问文件时，并不区分"主机"还是"容器"。它只是沿着一条从 `/` 出发的路径走。所以只要 `/` 变了，这个程序眼里的整个世界就都变了。** [【跳转到 00:49】](https://www.youtube.com/watch?v=1r8feBhPn9E&t=49)

来证明一下。跑一条 `cat /etc/os-release`——它并不"知道"什么特别的事，只是**从 `/etc` 读了一个文件**：这次读出来的是 Red Hat Enterprise Linux。**如果这个 `/etc` 换成别的，输出自然就变了**。这就是"程序不知道自己身在何处，只知道 `/` 展示了什么"的含义。[【跳转到 00:54】](https://www.youtube.com/watch?v=1r8feBhPn9E&t=54)

![`cat /etc/os-release` 只是从 `/etc` 读文件，输出随 `/etc` 的内容而变](assets/Docker%20Tutorial：%20Build%20a%20Container%20Filesystem%20From%20Scratch%20%28chroot%2C%20RootFS%20%26%20Namespaces%29/00069.webp)

再看进程这一侧：`ps aux` 里，**每个进程都在运行一个二进制文件**，而这些路径**同样只从 `/` 解析**。把两件事合起来就是本讲的逻辑基石：

> **进程依赖文件系统，文件系统又依赖 `/`。所以改动 `/`，就等于改动了进程的整个"世界观"。** 而在默认状态下，**所有进程共享同一个根文件系统、彼此之间没有任何边界**——你随便跑一个不可信的程序，它就能看到你的全部。[【跳转到 01:09】](https://www.youtube.com/watch?v=1r8feBhPn9E&t=69)

## 二、给进程一套自己的文件系统：先动手造一个 rootfs

修复办法是：**不再共用 `/`，而是给进程一份属于它自己的文件系统**。注意这里的"窍门"——**我们不创建新内核、也不创建虚拟机**，只是**造一套不同的目录结构**而已。[【跳转到 01:34】](https://www.youtube.com/watch?v=1r8feBhPn9E&t=94)

### 2.1 先搭出目录骨架

```bash
mkdir rootfs-demo
cd rootfs-demo
mkdir -p bin lib64 etc proc usr
```

这几条命令建出来的**不是随便几个文件夹**，而是**一个 Linux 系统的骨架**——**这正是容器镜像里装的东西**。[【跳转到 02:24】](https://www.youtube.com/watch?v=1r8feBhPn9E&t=144)

![`mkdir -p bin lib64 etc proc usr`：搭出一个 Linux 系统的目录骨架](assets/Docker%20Tutorial：%20Build%20a%20Container%20Filesystem%20From%20Scratch%20%28chroot%2C%20RootFS%20%26%20Namespaces%29/00234.webp)

### 2.2 放进第一个程序，并解决"依赖"问题

把 shell 拷进去：

```bash
cp /bin/bash bin/
```

此刻**有了文件，但还谈不上"能用"**。试着在这里跑 bash 会失败，原因是：**二进制文件不是独立的**，它依赖一批**共享库（shared libraries）**。用 `ldd`（list dependencies）查它的依赖：[【跳转到 02:49】](https://www.youtube.com/watch?v=1r8feBhPn9E&t=169)

![`ldd /bin/bash`：逐行列出 bash 依赖的共享库及其路径（如 libtinfo、libc、ld-linux）](assets/Docker%20Tutorial：%20Build%20a%20Container%20Filesystem%20From%20Scratch%20%28chroot%2C%20RootFS%20%26%20Namespaces%29/00284.webp)

输出的**每一行都是一个必需的库**及其位置。也就是说：**二进制文件只是个入口，真正的功能都来自这些库**。[【跳转到 03:39】](https://www.youtube.com/watch?v=1r8feBhPn9E&t=219)

接着把这些库拷进去，用 **`cp -av`**：

```bash
cp -av /lib64/libtinfo.so.* lib64/
```

这里 **`-a` 是关键**：它会**保留符号链接**。为什么重要？**很多库并不是真实文件，而是指向"带版本号文件"的软链**——如果你把链接拷断了，系统也就坏了。所以必须完整保留链接。[【跳转到 03:54】](https://www.youtube.com/watch?v=1r8feBhPn9E&t=234)

![`ls -l lib64`：库文件与指向版本化文件的符号链接都被保留](assets/Docker%20Tutorial：%20Build%20a%20Container%20Filesystem%20From%20Scratch%20%28chroot%2C%20RootFS%20%26%20Namespaces%29/00360.webp)

### 2.3 把重复劳动自动化

一个个手拷太慢，可以**一条命令搞定**：

```bash
ldd /bin/bash /bin/ls | awk '{print $3}' | grep "/" | sort -u | xargs -I'{}' cp -av {} lib64/
```

拆解一下：`ldd` 列出 `bash` 与 `ls` 的依赖 → `awk '{print $3}'` 取出文件路径 → `grep "/"` 过滤出合法路径 → `sort -u` 去重 → `xargs ... cp` **一次性把需要的库全拷进去**。[【跳转到 05:09】](https://www.youtube.com/watch?v=1r8feBhPn9E&t=309)

![用 `ldd | awk | grep | sort -u | xargs cp` 一条管道自动拷贝依赖库](assets/Docker%20Tutorial：%20Build%20a%20Container%20Filesystem%20From%20Scratch%20%28chroot%2C%20RootFS%20%26%20Namespaces%29/00451.webp)

至此，**我们的根文件系统准备好了**。

### 2.4 用 `chroot` 让它成为"根"

现在把它**当作真正的文件系统**来用——工具是 **`chroot`**（change root，切换根目录）：

```bash
chroot rootfs-demo /bin/bash      # 再把 PATH 指到 /bin，然后 exec /bin/bash
```

它做的事：**把进程的根目录切换到 `rootfs-demo`**，在里面启动一个 shell，**让这个进程相信这就是整个文件系统**。注意两个细节——**要记得 `export PATH=/bin`**，否则 shell 不知道去哪找命令；用 **`exec /bin/bash`** 则会让它**替换**当前进程，而不是新建一个子进程。[【跳转到 06:00】](https://www.youtube.com/watch?v=1r8feBhPn9E&t=360)

### 2.5 一个真实的"翻车现场"：文件系统不完整

进到自定义 rootfs 后，**bash 能跑，`ls` 却失败**。这恰好说明一个要点：**文件系统存在，但还不完整**——我们补全了 bash 的依赖，却漏掉了 `ls` 的一部分依赖，比如 `libcap`。**每个二进制都有自己的依赖，哪怕只缺一个，它就跑不起来。** [【跳转到 06:50】](https://www.youtube.com/watch?v=1r8feBhPn9E&t=410)

![在自定义 rootfs 内执行 `ls` 报错 `libcap.so.2: cannot open shared object file`](assets/Docker%20Tutorial：%20Build%20a%20Container%20Filesystem%20From%20Scratch%20%28chroot%2C%20RootFS%20%26%20Namespaces%29/00513.webp)

于是退出来，查出 `ls` 缺的库并补齐：

```bash
ldd /bin/ls | grep libcap           # 找到 libcap.so.2 的路径
cp -av /lib64/libcap.so.* rootfs-demo/lib64/
# 补上后发现还缺 libpcre2-8、libselinux 等，一并拷贝
```

**`ls` 的多重依赖逐一补齐后，它终于能跑了**。这里得到的教训非常直接：**每个二进制都依赖多个库，还常常是放在不同路径的版本化软链——手工或漏拷任何一环，都会报错。这正是"容器镜像"要解决的问题**：它把一切打包在一起，所以你永远不会遇到"缺依赖"。[【跳转到 08:33】](https://www.youtube.com/watch?v=1r8feBhPn9E&t=513)

再验证一次边界：在自定义 rootfs 里 `ls /home` 会**失败**——因为 `/home` 指的是 **`rootfs-demo/home`**，而不是主机的 `/home`。**这个环境里根本没有这个目录。**

### 2.6 但它还不是容器

到这一步**它"看起来"像容器，其实不是**。因为我们**只改变了"文件系统视图"**：**进程依然是共享的，内核依然是共享的**——我们改的是"进程能看到什么"，而**没有**改变"系统如何隔离"。[【跳转到 10:13】](https://www.youtube.com/watch?v=1r8feBhPn9E&t=613)

## 三、把"文件系统隔离"和"进程隔离"合起来

那么问题来了：**能不能像隔离文件系统一样，把进程也隔离掉？** 用 **`unshare`** 一条命令即可：[【跳转到 10:38】](https://www.youtube.com/watch?v=1r8feBhPn9E&t=638)

```bash
unshare --pid --uts --mount --net --fork --mount-proc bash
```

逐个看这些开关：`--pid`（进程号隔离）、`--uts`（主机名隔离）、`--mount`（挂载隔离）、`--net`（网络隔离）、`--fork`（在新命名空间里 fork 出新进程）、**`--mount-proc`（顺手挂一份全新的 `/proc`）**。执行后 `echo $$` 显示为 **1**——**在这个命名空间里，我们自己就是 PID 1**。[【跳转到 11:03】](https://www.youtube.com/watch?v=1r8feBhPn9E&t=663)

![`unshare --pid --uts --mount --net --fork --mount-proc bash` 后 `echo $$` 得到 1](assets/Docker%20Tutorial：%20Build%20a%20Container%20Filesystem%20From%20Scratch%20%28chroot%2C%20RootFS%20%26%20Namespaces%29/00688.webp)

再叠加自定义文件系统：

```bash
exec chroot rootfs-demo /bin/bash
```

`exec` 让它**替换**当前进程（不产生子进程，PID 保持不变），`chroot` 把根切到我们造的 rootfs。**进去之后 `ls` 又报错了**——因为这次**忘了设置 `PATH`**。补上 `export PATH=/bin` 就恢复正常。[【跳转到 11:53】](https://www.youtube.com/watch?v=1r8feBhPn9E&t=713)

![进入自定义 rootfs 后未设 PATH，`ls` 报 `command not found`](assets/Docker%20Tutorial：%20Build%20a%20Container%20Filesystem%20From%20Scratch%20%28chroot%2C%20RootFS%20%26%20Namespaces%29/00873.webp)

这个细节带出一条重要结论：**容器不只需要文件，还需要"环境"**。所以**容器镜像里会定义环境变量**——**Docker 就在 Dockerfile 里自动为容器设好了 `PATH`**。没有它，再完整的文件系统也会"找不到命令"。[【跳转到 12:18】](https://www.youtube.com/watch?v=1r8feBhPn9E&t=738)

至此，我们**同时隔离了文件和进程**，还准备好了运行环境。至于**网络（veth 网卡、IP、主机名的 UTS 设置）**，视频里点到为止（讲者说在上一集已详细演示过）——**要真正联网，还得把 `ip` 等网络工具也拷进 rootfs 才行**。[【跳转到 13:04】](https://www.youtube.com/watch?v=1r8feBhPn9E&t=784)

## 四、Docker 做的事，就是把这套流程自动化

回到主机，敲下 `docker run nginx`。**Docker 在后台其实做了这么几件事**：[【跳转到 13:34】](https://www.youtube.com/watch?v=1r8feBhPn9E&t=814)

1. **准备根文件系统**（从镜像里）；
2. **创建命名空间**；
3. **配置网络**；
4. **启动进程**。

![Docker Engine 作为自动化层：把用户命令翻译成 API 调用并处理交互](assets/Docker%20Tutorial：%20Build%20a%20Container%20Filesystem%20From%20Scratch%20%28chroot%2C%20RootFS%20%26%20Namespaces%29/00832.webp)

**这和我们手动做的每一步完全一样，只是被自动化了**。同样的道理也适用于 Kubernetes：**Kubernetes 不直接跑容器**，它调用 **containerd、runc、docker** 这类**容器运行时**来完成"命名空间搭建 + 文件系统准备 + 进程启动"这些步骤——**Kubernetes 负责编排，Linux 负责干实际活**。[【跳转到 13:52】](https://www.youtube.com/watch?v=1r8feBhPn9E&t=832)

## 五、镜像就是打包好的文件系统：把 nginx 镜像拆开看

那容器的文件系统到底从哪来？答案朴素得让人意外：**镜像就是一份打包的文件系统，没什么魔法**。视频里把 nginx 镜像**拆开**验证了一遍：[【跳转到 14:08】](https://www.youtube.com/watch?v=1r8feBhPn9E&t=848)

```bash
podman pull nginx
podman save nginx -o nginx-image.tar      # 把镜像导出成一个 tar
mkdir nginx-img && tar -xf nginx-image.tar -C nginx-img
cd nginx-img && find . -name layer.tar    # 找出镜像层
```

`find` 的结果，就是一个个 **`layer.tar`**——**每个"层"代表一组文件系统的变更**。也就是说：**容器不会每次都存一整套完整文件系统，而只存"改动了什么"**。[【跳转到 15:28】](https://www.youtube.com/watch?v=1r8feBhPn9E&t=928)

![`find . -name layer.tar`：镜像由一个 json 加若干个 layer.tar 组成](assets/Docker%20Tutorial：%20Build%20a%20Container%20Filesystem%20From%20Scratch%20%28chroot%2C%20RootFS%20%26%20Namespaces%29/00967.webp)

把其中一层解开，会看到一个**完整的 Linux 文件系统**（`/home`、`/lib`、`/lib64` …）——**它和我们刚才手工搭的那一套几乎一模一样，唯一的区别是这次是自动生成的**。[【跳转到 15:56】](https://www.youtube.com/watch?v=1r8feBhPn9E&t=956)

![解开的镜像层：一个完整的 Linux 文件系统目录树](assets/Docker%20Tutorial：%20Build%20a%20Container%20Filesystem%20From%20Scratch%20%28chroot%2C%20RootFS%20%26%20Namespaces%29/00983.webp)

到这里，所有线索串起来了：

> **当你运行一个容器，系统会拿这套文件系统、建立命名空间、在里面启动进程。文件系统 + 进程隔离 + 执行——这就是容器。** [【跳转到 16:23】](https://www.youtube.com/watch?v=1r8feBhPn9E&t=967)

但这又带出一个新问题：**难道每个容器都要复制一整份文件系统吗？** 那样又慢又浪费空间。答案就留给下一集——**rootfs 给容器一套文件系统，而 overlayFS 让它变得可扩展**。[【跳转到 16:32】](https://www.youtube.com/watch?v=1r8feBhPn9E&t=992)

## 小结

- **`/` 是整个文件系统的起点**：进程不区分"主机还是容器"，只沿 `/` 解析路径；所以**换掉 `/`，就换掉了进程的整个世界**。
- **容器需要一个属于自己的 rootfs**。它可以**从零手工搭**：建目录骨架 → 拷二进制 → 用 `ldd` 找依赖 → `cp -av` 连同符号链接一起拷（库多是版本化软链，断了就崩）。
- **`chroot` 把某个目录变成进程的 `/`**；但要记得 **`PATH`**——**容器不只需要文件，还需要环境变量**（Docker 在 Dockerfile 里设 `PATH`）。
- **单靠 `chroot` 只是"文件系统视图"，不是容器**：进程与内核仍共享。**`unshare --pid --uts --mount --net --fork --mount-proc` 才能把进程也隔离**（`--mount-proc` 会挂一份新的 `/proc`）。
- **Docker / Kubernetes 做的就是把上面这套手工步骤自动化**：Docker 直接跑；Kubernetes 交给 containerd / runc 等运行时。
- **镜像 = 打包的文件系统**：拆开是若干 `layer.tar`，**每层只记录"变更"**；解开一层就是一个完整 Linux 文件系统。
- **一句话总结：容器 = 文件系统 + 进程隔离 + 执行**。往下要解决的规模化问题，靠 **overlayFS**。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| rootfs | 容器的根文件系统，即进程看到的 `/` |
| `/`（根目录） | 所有路径的解析起点；换 `/` 即换进程的世界观 |
| `ldd` | 列出某二进制所依赖的共享库及其路径 |
| 共享库 / 符号链接 | 二进制真正功能所在；库往往是版本化软链，拷贝须保链（`cp -a`） |
| `chroot` | 切换进程的根目录，让它把某目录当作 `/` |
| `PATH` | 命令查找路径；缺了它即使文件齐全也会 `command not found` |
| `unshare` | 创建新的命名空间并运行进程；`--mount-proc` 会挂一份新 `/proc` |
| mount-proc | 在隔离环境里挂载一份全新的 `/proc`，形成独立挂载布局 |
| layer.tar | 镜像的"层"，每层记录一组文件系统变更而非全量 |
| containerd / runc | 容器运行时，负责命名空间、文件系统与进程启动 |
