# 用无根模式加固 Docker 守护进程：把整条栈降到普通用户

> 视频源：[Hardening Docker Daemon with Rootless Mode（Akihiro Suda, NTT）](https://www.youtube.com/watch?v=uWURUtqLiqQ)（YouTube / KubeCon，21 分 30 秒）。本文基于视频演说图文稿整理，时间戳可跳转到原视频对应位置。

## 本讲要解决的核心问题（SCQA）

**背景**：Docker 默认就为安全做了很多设计。它自带命名空间来隔离进程（mount namespace、network namespace 等），用 capabilities 把 root 的权限拆成细粒度能力（`CAP_CHOWN`、`CAP_SETUID`……），用 cgroups 限制设备访问，用 seccomp 限制系统调用，还用 AppArmor 与 SELinux 控制文件访问权限。[【跳转到 02:00】](https://www.youtube.com/watch?v=uWURUtqLiqQ&t=120)

**冲突**：这些特性我们不必太操心——**但最终每个软件都有 bug**。容器里的 root 可以借这些 bug 逃出容器：视频里举了两个真实例子，一个是 runc 的漏洞，允许攻击者覆写 `/proc/self/exe`；一个是 `docker cp` 的漏洞，通过篡改 `docker cp` 的进程把恶意库注入宿主机。还有人干脆把 Docker API 暴露到公网上且不做任何客户端认证——研究者说互联网上有成千上万台这样配错的主机。[【跳转到 03:15】](https://www.youtube.com/watch?v=uWURUtqLiqQ&t=195)

**疑问**：漏洞修不完，配置也总有人配错。那么，能不能改变「出事之后的后果」，让一次逃逸拿不到宿主机真正的 root？

**回答（中心思想）**：这就是 **rootless mode（无根模式）**——**把 Docker 守护进程以非 root 用户运行**，而且要强调：不只是容器，**包括 containerd、dockerd 在内的整条栈**都跑在普通用户下。它**不修漏洞、也不防错配**，但能大幅降低伤害，因为否则攻击者拿到的是宿主机的真 root。本讲讲清它**不是什么**、怎么装、底层靠什么（user namespace）、有哪些工程代价，以及它与 Podman 的分工。[【跳转到 01:35】](https://www.youtube.com/watch?v=uWURUtqLiqQ&t=95)

---

## 一、先分清：无根模式是什么，以及它不是什么

### 1.1 关键在「整条栈」

无根模式指**以宿主机上的普通用户身份运行 Docker 守护进程**。它不只是「让容器以非 root 跑」——在这个模式下，**整个栈**（containerd、Docker 守护进程等等）都以非 root 用户运行。

因此它保护的不只是容器，而是**整个系统**：当漏洞或错误配置出在守护进程本身时，受害范围也被限制住了。[【跳转到 02:00】](https://www.youtube.com/watch?v=uWURUtqLiqQ&t=120)

### 1.2 Docker 默认已经很安全，但所有软件都有 bug

Docker 自带的安全能力可以列成一张清单：

![Docker 自带的默认安全特性：命名空间、capabilities、cgroups、seccomp、AppArmor/SELinux](<assets/Hardening Docker Daemon with Rootless Mode/00145.webp>)

- **命名空间**：mount namespace、network namespace 等，隔离进程能看到什么；
- **capabilities**：如 `CAP_CHOWN`、`CAP_SETUID`，把 root 的权限拆细；
- **cgroups**：限制设备访问；
- **seccomp**：限制系统调用；
- **AppArmor / SELinux**：控制文件访问权限。

这些特性「不需要我们太操心」，但**每个软件最终都有 bug**，容器里的 root 可以借 bug 逃逸。视频给出的两类典型问题：

- **runc 漏洞**：允许攻击者覆写 `/proc/self/exe`；
- **`docker cp` 漏洞**：通过篡改 `docker cp` 的进程，把恶意库注入宿主机；
- **错误配置**：把 Docker API 暴露到公网、不做客户端认证——研究者说这类主机在互联网上有成千上万台。

[【跳转到 02:50】](https://www.youtube.com/watch?v=uWURUtqLiqQ&t=170)

### 1.3 无根模式不修漏洞，只降低伤害

无根模式**本身不是这些漏洞与错误配置的解药**，但它能减轻攻击造成的损害——因为它拦住的正是最坏的结果：攻击者拿到宿主机真正的 root。[【跳转到 03:40】](https://www.youtube.com/watch?v=uWURUtqLiqQ&t=220)

当守护进程以无根模式运行时，攻击者**仍可能**借漏洞在容器里取得访问权，但此时：

- 他**读不到任何属于其他用户的文件**；
- 他**改不了容器文件，也改不了任何系统文件**；
- 他**不能做网络欺骗**。

[【跳转到 04:05】](https://www.youtube.com/watch?v=uWURUtqLiqQ&t=245)

### 1.4 它也不是这四样东西

有几件事听起来很像无根模式，但完全不同：

![第一件不是无根模式的事：`sudo docker`](<assets/Hardening Docker Daemon with Rootless Mode/00270.webp>)

- **不是 `sudo docker`**：这个当然完全不同——你还是在用 root 跑。
- **不是把用户加进 `docker` 用户组**：这样用户只是能访问 Docker socket，守护进程依然是 root，用户照样能以 root 权限对宿主机为所欲为。
- **不是 `docker run --userns=...`**：它让容器以非 root 用户跑，但**守护进程仍是 root**。
- **不是 Docker 的 userns-remap 模式**：守护进程仍是 root，用户只要跑一句 `docker run -v /:/host` 或 `docker run --privileged`，就能拿到整机 root。

[【跳转到 04:30】](https://www.youtube.com/watch?v=uWURUtqLiqQ&t=270) · [【跳转到 05:20】](https://www.youtube.com/watch?v=uWURUtqLiqQ&t=320) · [【跳转到 06:10】](https://www.youtube.com/watch?v=uWURUtqLiqQ&t=370)

---

## 二、一次演示：容器里是 root，宿主机上不是

演示环境里，讲者的用户名是 `user`，用户 ID 非零；他**以这个非 root 用户同时运行 Docker 守护进程和容器**。

在容器里，他拿到了 UID 0——也就是 root。但：

```bash
cat /etc/shadow        # permission denied（容器里是 root，但不是宿主机 root）
apt install <应用>      # 正常
# 起一个 nginx HTTP 服务 → 正常
```

结果显示：容器内是 root，却**看不到宿主机的任何文件**——`cat /etc/shadow` 直接 "permission denied"；反过来，在容器里装应用、起 nginx 都工作正常。[【跳转到 07:26】](https://www.youtube.com/watch?v=uWURUtqLiqQ&t=446) · [【跳转到 07:51】](https://www.youtube.com/watch?v=uWURUtqLiqQ&t=471)

这就是无根模式的日常形态：**容器内的 root 只是「容器内够用」的 root**。

---

## 三、怎么开始用：一个脚本 + 一个环境变量

上手非常简单：

1. 从 `get.docker.com/rootless` 下载安装脚本并执行；
2. 设置一个环境变量 `DOCKER_HOST`。

就这两步。[【跳转到 08:44】](https://www.youtube.com/watch?v=uWURUtqLiqQ&t=524)

![安装脚本把一切装在你的 home 目录下，不需要 root](<assets/Hardening Docker Daemon with Rootless Mode/00547.webp>)

关键点：**安装过程不需要 root 权限**。所有东西都装在你的 home 目录下，所以既不需要 root，也不需要自己去创建系统用户或编辑 `/etc/subuid`、`/etc/subgid`。[【跳转到 09:07】](https://www.youtube.com/watch?v=uWURUtqLiqQ&t=547)

**前置条件因发行版而异**：

- 需要为你的用户账号配好 `subuid` 与 `subgid`——不过通常这两个文件默认就配好了；
- 如果用的是 Debian 或 CentOS 7，还需要设置一些 `sysctl` 值；不满足前置条件时，**安装脚本会给出提示信息**。

[【跳转到 09:32】](https://www.youtube.com/watch?v=uWURUtqLiqQ&t=572)

另外有一个名为 **Katacoda scenario** 的无根模式教程，可以在上面直接试：[【跳转到 10:12】](https://www.youtube.com/watch?v=uWURUtqLiqQ&t=612)

```bash
# 添加一个用户账号 → 切换到该账号 → 运行 rootless Docker，跑通即可
```

---

## 四、底层原理：user namespace 与 `unshare`

无根模式是靠 **user namespace（用户命名空间）** 实现的。

先在终端里看一眼最小演示：当前用户名是 `user`（不是 root），执行：

```bash
unshare --user --map-root-user
```

![`unshare --user --map-root-user`：只是命名空间内的 root](<assets/Hardening Docker Daemon with Rootless Mode/00700.webp>)

用户名就变成了 `root`——但**它只是在命名空间内获得了类似 root 的能力**。立刻验证一下：

```bash
touch /test        # permission denied
```

在根目录下创建文件会失败。[【跳转到 11:54】](https://www.youtube.com/watch?v=uWURUtqLiqQ&t=714)

**在 user namespace 里，可以继续创建其它命名空间**——mount、network、UTS、IPC——并做一些平时需要 root 的操作，比如改主机名、挂载别的文件系统：[【跳转到 12:07】](https://www.youtube.com/watch?v=uWURUtqLiqQ&t=727)

```bash
unshare --user --map-root-user --uts
hostname myname    # 改主机名
```

![在 user namespace 内再建 UTS namespace，改主机名只影响这个命名空间](<assets/Hardening Docker Daemon with Rootless Mode/00727.webp>)

这个改动**只发生在该命名空间内部，完全不影响宿主机**。[【跳转到 12:42】](https://www.youtube.com/watch?v=uWURUtqLiqQ&t=762)

> 一句话理解：user namespace 让普通用户先在「自己的小世界」里自封为 root，再用这份命名空间内的权限去搭建容器需要的其它隔离。

---

## 五、三个工程上的坑：overlayfs、网络、cgroups

无根模式早期被诟病，主要就是因为下面三处支持不足。

### 5.1 overlayfs：得换个实现

无根 Docker 要用 overlayfs，才能从镜像创建容器而**不复制数据**。但它**基本上对非特权用户不可用**，因为受内核限制：

- 用 **Ubuntu 或 Debian**：内核编译时开启了非特权 overlayfs，可以直接用；
- 用**其它发行版**：只能用 **VFS 驱动**——性能最差的一种。

好消息是：**从 Docker 20.10 起**，无根模式借助 **fuse-overlayfs**，让**任何 4.18 或更新版本的内核**都能用上 overlayfs。[【跳转到 13:07】](https://www.youtube.com/watch?v=uWURUtqLiqQ&t=787) · [【跳转到 13:12】](https://www.youtube.com/watch?v=uWURUtqLiqQ&t=792)

![overlayfs 与 fuse-overlayfs：Docker 20.10 起任何 4.18+ 内核都能用](<assets/Hardening Docker Daemon with Rootless Mode/00792.webp>)

### 5.2 网络：改用用户态 TCP/IP 栈

有 user namespace，我们可以无 root 创建 network namespace，**但仍然不能创建虚拟以太网接口（veth）**，所以改用**用户态 TCP/IP 栈**，而不是网桥接口：[【跳转到 14:02】](https://www.youtube.com/watch?v=uWURUtqLiqQ&t=842)

- **首选 `slirp4netns`**：来自 QEMU 项目，Docker Desktop for Mac 与 Windows 也在用；
- **最后的兜底**是一个叫 `vpnkit` 的 setuid 程序，可以拿到「真正的」网络，但它**仍是实验性的、且牺牲了安全性**，所以还是推荐 `slirp4netns`。

[【跳转到 14:27】](https://www.youtube.com/watch?v=uWURUtqLiqQ&t=867) · [【跳转到 14:52】](https://www.youtube.com/watch?v=uWURUtqLiqQ&t=892)

### 5.3 cgroups：从几乎没有，到完整支持

以前无根模式对 cgroup 支持极少，**不能指定 `--cpus`、`--memory` 这类资源限制**。**从 Docker 20.10 起 cgroups 已完整支持**。[【跳转到 15:17】](https://www.youtube.com/watch?v=uWURUtqLiqQ&t=917)

![cgroups 完整支持的前提：systemd cgroup driver + systemd.unified_cgroup_hierarchy=1](<assets/Hardening Docker Daemon with Rootless Mode/00942.webp>)

但它有前提：需要 **systemd cgroup driver**，且内核参数 `systemd.unified_cgroup_hierarchy=1`。Fedora 默认开启；其它发行版需要改内核命令行。[【跳转到 15:42】](https://www.youtube.com/watch?v=uWURUtqLiqQ&t=942)

### 5.4 仍然不支持的少数特性

无根模式仍不支持：指定 AppArmor profile、`docker checkpoint`、`docker run --net=host`、暴露特权端口（< 1024），以及一些网络特性。[【跳转到 16:07】](https://www.youtube.com/watch?v=uWURUtqLiqQ&t=967)

讲者的判断很直接：**99% 的用例用不到这些**，所以基本不必在意。

---

## 六、常见问答

![FAQ 环节：是否生产可用、是不是万能药、端口、与 Podman 的比较](<assets/Hardening Docker Daemon with Rootless Mode/00992.webp>)

**Q1：无根模式还是实验特性吗？能上生产吗？**
Docker 19.03 里它确实是实验特性，但下一个版本 **Docker 20.10 就会转正**（视频发布时该版本尚未发布，但 release notes 已经写好）。[【跳转到 16:52】](https://www.youtube.com/watch?v=uWURUtqLiqQ&t=1012)

**Q2：它是解决一切问题的万能药吗？**
**不是银弹。** 即使开了无根模式，攻击者仍可能拿容器去**挖矿**（比如比特币），或把宿主机当作**跳板**去攻击互联网上其它主机（用来隐藏自己的 IP）。此外，它对针对**内核、VM 或硬件**的攻击无效。[【跳转到 17:17】](https://www.youtube.com/watch?v=uWURUtqLiqQ&t=1037)

**Q3：还能用 `docker run -p` 暴露端口吗？**
可以，但要知道 **1024 以下的特权端口对无根用户不可用**，所以基本上要用 8080 这样的高位端口：

```bash
docker run -p 8080:80      # 想跑 HTTP 服务，这样写
```

![`docker run -p` 在无根模式下的端口限制与变通办法](<assets/Hardening Docker Daemon with Rootless Mode/01087.webp>)

如果你**确实**需要暴露特权端口，可以通过调整 sysctl `net.ipv4.ip_unprivileged_port_start`，或给二进制加上 `CAP_NET_BIND_SERVICE` capability。但讲者说这「有点 hack」，**最好还是指定 8080 这类高位端口**。[【跳转到 18:07】](https://www.youtube.com/watch?v=uWURUtqLiqQ&t=1087) · [【跳转到 18:32】](https://www.youtube.com/watch?v=uWURUtqLiqQ&t=1112)

**Q4：无根 Docker 与 Podman 怎么选？**
Rootless Podman 是 Red Hat 做的另一个实现，目标是同一件事。**Docker 与 Podman 在这方面的协作很多，功能与性能几乎一致**，差别很小：[【跳转到 18:57】](https://www.youtube.com/watch?v=uWURUtqLiqQ&t=1137)

| 维度 | 无根 Docker | Rootless Podman |
| --- | --- | --- |
| 功能 / 性能 | 几乎相同 | 几乎相同 |
| 自定义网络 | 不支持 `docker run --net=host` 等 | 支持 `podman network create`，网络支持更好 |
| 无根模式整体成熟度 | 讲者认为更好 | — |

结论：**如果确实需要 `--net=host`，Podman 可能是更好的选择**；否则两者差别不大。[【跳转到 19:47】](https://www.youtube.com/watch?v=uWURUtqLiqQ&t=1187) · [【跳转到 20:12】](https://www.youtube.com/watch?v=uWURUtqLiqQ&t=1212)

---

## 七、收尾：一句话记住它

![收尾：无根模式把宿主用户从守护进程的漏洞与错误配置中保护起来](<assets/Hardening Docker Daemon with Rootless Mode/01260.webp>)

讲者用一段话做了总结：[【跳转到 20:30】](https://www.youtube.com/watch?v=uWURUtqLiqQ&t=1230)

- 无根模式**保护宿主机用户**，使其免受 Docker 守护进程漏洞与错误配置的伤害；
- 它原来是实验特性、且缺少 cgroups 支持，**从 Docker 20.10 起转正**，并带来 cgroups 完整支持——现在可以用 `--cpus`、`--memory` 等资源限制；
- 安装只需跑 `get.docker.com/rootless` 的脚本，非常简单。

---

## 小结

- **无根模式 = 把整条栈（containerd、dockerd、容器）都以非 root 用户运行**，保护的是整个系统，不只是容器。
- 它**不修漏洞、不防错配**，只是把「逃逸后拿到宿主机真 root」这个最坏结果，变成「读不到别人的文件、改不了系统文件、不能做网络欺骗」。
- 它**不是** `sudo docker`、**不是** 加入 docker 组、**不是** `--userns=`、**也不是** userns-remap——后两者守护进程仍是 root，一句 `-v /:/host` 或 `--privileged` 就能拿下整机。
- **安装两件事**：跑 `get.docker.com/rootless`，设 `DOCKER_HOST`；装在你的 home 下，不需要 root；前置条件是 `subuid`/`subgid`（通常默认已配）。
- **底层是 user namespace**：`unshare --user --map-root-user` 让人在命名空间内成为 root，再在其内创建 mount/network/UTS/IPC 命名空间。
- **三个代价**：overlayfs 需要 fuse-overlayfs（Docker 20.10 + 内核 4.18+）、网络改用 `slirp4netns`、cgroups 需要 systemd unified hierarchy。
- **不支持**：AppArmor profile、`docker checkpoint`、`--net=host`、特权端口等，但 99% 的场景用不到。
- **它不是银弹**：仍可被挖矿、被当跳板，对内核/VM/硬件层攻击无效。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| rootless mode（无根模式） | 把 Docker 守护进程（含 containerd 等整条栈）以非 root 用户运行的模式 |
| 守护进程（daemon） | 后台常驻、替客户端执行容器操作的进程；Docker 默认以 root 运行 |
| Docker socket | 客户端与守护进程通信的接口；能访问它几乎等价于拥有 root |
| user namespace（用户命名空间） | 让普通用户在自己的命名空间内拥有「root」，同时把这份 root 与宿主机 root 隔开 |
| `unshare` | 创建新命名空间并运行程序的工具，`--map-root-user` 把自己映射成命名空间内的 root |
| capabilities | 把 root 权限拆成的一项项细粒度能力，如 `CAP_CHOWN`、`CAP_NET_BIND_SERVICE` |
| seccomp | 限制进程可使用的系统调用的内核机制 |
| AppArmor / SELinux | 控制文件与资源访问权限的强制访问控制（MAC）机制 |
| overlayfs / fuse-overlayfs | 联合文件系统；非特权用户在内核不支持时靠 fuse-overlayfs 使用 |
| VFS 驱动 | 最保守的存储驱动，不做联合挂载，性能最差 |
| slirp4netns | 用户态 TCP/IP 栈，让无根容器拥有网络（来自 QEMU 项目） |
| vpnkit | setuid 的网络兜底方案，实验性且牺牲安全性 |
| subuid / subgid | 分配给某个用户使用的宿主机 ID 区间，是 UID 映射的前提 |
| systemd.unified_cgroup_hierarchy | 内核参数，设为 1 启用 cgroup v2 统一层级，是无根模式 cgroups 支持的前提 |
| `net.ipv4.ip_unprivileged_port_start` | 控制「多大端口以上非特权用户可绑定」的 sysctl，可用来降低特权端口门槛 |
| userns-remap | Docker 的一种用户映射模式，但守护进程仍是 root，故不等同于无根模式 |
| Podman | Red Hat 的无守护进程容器工具，rootless 是默认行为，网络支持更好（如 `--net=host`） |
