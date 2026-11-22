# 无根容器入门：Podman 到底保护了什么

> 本博客整理自视频 [Rootless Containers Explained | How Podman Protects Your Host（GoDevOps，Ep.8）](https://www.youtube.com/watch?v=eNzYIgRCYBk)，全部内容来自视频字幕与画面，时间戳链接均指向原视频。

## 本讲要解决的核心问题（SCQA）

**背景**：你已经在用容器了。跑一个容器时，你通常会关心镜像干不干净、镜像里的应用有没有漏洞。

**冲突**：但还有一个同样重要的细节被大多数人忽略——**容器里的进程是以什么身份运行的**。默认情况下，它运行在容器里的 `root`，而更糟的是，这个 `root` 往往就是宿主机上的 `root`。一旦有人攻破应用、从容器里跑出来，他落地就是宿主机的 root。

**疑问**：那么，怎么才能让容器不以 root 运行？「无根容器（rootless container）」到底指什么？它凭什么更安全？要付出什么代价？

**回答（中心思想）**：无根容器把安全边界从「一小段代码」扩展到「两层防线」——第一层是**无根运行时**（没有 root 守护进程，`root` 映射到你的普通用户），第二层是**容器内的非 root 进程**（应用本身不需要 root）。两层相互独立，任一层有缺口，另一层仍能限制损害。而这套能力完全建立在一个 Linux 内核特性上：**用户命名空间（user namespace）** 与它背后的 `subuid`/`subgid` 映射。

---

## 一、先问一个问题：容器里到底是谁在运行？

### 1.1 为什么这个问题对容器比对虚拟机更关键

要理解无根容器的价值，先要看清容器和虚拟机在「出事后」的差别。

- **虚拟机**：每个应用跑在自己的 VM 里，每个 VM 有自己的内核和完整操作系统，隔离是彻底的。攻击者攻破了你的应用，他也只是**在 VM 内部**；要逃到宿主机，他必须找到并利用一个 **hypervisor（虚拟机监视器，负责在宿主与 VM 之间做隔离的那层软件）** 的漏洞——门槛极高，不是不可能，但极其困难。代价是资源：每个 VM 都背着一整套操作系统，**重、启动慢、运行贵**。

![虚拟机的隔离模型：每个应用各自拥有一个内核，逃逸需要打穿 hypervisor](<assets/Rootless Containers Explained：How Podman Protects Your Host/00030.webp>)

- **容器**：完全不同的模型。容器**共享宿主机的内核**，没有「每个容器一套操作系统」这回事，所以启动只要毫秒级、开销几乎为零。但安全边界也随之改变：如果攻击者从容器里逃出来，他和内核之间**没有 hypervisor 那道墙**——内核就在眼前。

![容器共享同一个内核：容器与宿主机之间没有 hypervisor 边界](<assets/Rootless Containers Explained：How Podman Protects Your Host/00090.webp>)

那容器是不是很危险？**不是**。容器非常优秀，这只是意味着「谁在容器里运行」这个问题在容器场景下变得重要得多。**容器内进程的权限越低，出事时的损失就越小。**

[【跳转到 00:30】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=30) · [【跳转到 01:30】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=90)

### 1.2 「rootless」是一个有严格定义的技术术语

「无根」不是随口说说的口号，它由**三个具体条件**构成——三者缺一不可。

![rootless 的第一个条件：容器内进程不能以 UID 0 运行](<assets/Rootless Containers Explained：How Podman Protects Your Host/00138.webp>)

**条件一：容器内的进程不能是 UID 0，也就是不能是 root。**
如果你的 Web 服务、API、数据库客户端在容器里以 root 运行，那么攻破它的人就在容器里拿到了 root，从而对容器内**每一个文件、每一个进程**都有完全访问权。

![rootless 的第二个（也是最重要的）条件：容器内的 root 不能被映射成宿主机的 root](<assets/Rootless Containers Explained：How Podman Protects Your Host/00163.webp>)

**条件二：容器里的 root 用户，不能对应到容器外的 root 用户。** 这是**最重要**的一条。
传统上「里面的 root」就等于「外面的 root」，所以只要以 root 身份逃出容器，就等于拿下了宿主机。而**用户命名空间打破了这种等价关系**——它让容器里的 root 映射成你在宿主机上的普通用户。

![rootless 的第三个条件：运行时自身不能以 root 运行（Docker 的守护进程就是反面例子）](<assets/Rootless Containers Explained：How Podman Protects Your Host/00188.webp>)

**条件三：运行时（runtime）自身也不能以 root 运行。**
以 Docker 为例：Docker 守护进程（daemon）以宿主机 root 身份运行，任何能访问 Docker socket 的用户**实际上就等于有 root**。而 Podman 没有守护进程：你运行一个容器时，Podman 会 fork 出一个由**你的用户**拥有的子进程，整条链路上没有任何 root 进程。因此 **Podman 在设计上同时满足这三个条件**。

[【跳转到 02:18】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=138) · [【跳转到 02:43】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=163) · [【跳转到 03:08】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=188)

---

## 二、守护进程架构的后果：能碰 socket，就等于有 root

这个「有 daemon / 无 daemon」的差别不是细节，它有**实实在在的安全后果**。

![Docker 的 daemon 模型：root 守护进程管理一切，socket 就是后门](<assets/Rootless Containers Explained：How Podman Protects Your Host/00227.webp>)

在 Docker 模型里，是 root 守护进程在管理一切。**只要你能接触到那个 socket，你就能以任意能力运行任意容器**。安全研究者已经证明：这种能力**等价于拥有宿主机的 root**。

Podman 则不同：你执行 `podman run` 时，Podman fork 出一个属于你的子进程，它带着你的权限运行，中间没有任何 root 守护进程。

![daemonless 模型：容器就是你的进程，而不是某个 root 服务替你做事](<assets/Rootless Containers Explained：How Podman Protects Your Host/00249.webp>)

一句话总结这两种模型：**你的容器就是你自己的进程，而不是一个 root 服务在替你干活**。

[【跳转到 03:47】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=227) · [【跳转到 04:09】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=249)

---
## 三、实验一：亲手看清 `uid_map`——里外的 root 不是同一个 root

理论说完，来动手。第一个实验要回答的问题是：**我们一直在用的容器里，到底是谁在运行？**

### 3.1 宿主机的我 vs 容器里的我

先在宿主机上看看自己是谁：

```bash
id          # 宿主机上：uid=1000，一个普通非特权用户
```

再从 Alpine 镜像起一个容器，在里面执行 `id`：

```bash
podman run --rm alpine id   # 容器里：uid=0(root)
```

于是我们看到一个矛盾的现象：**宿主机上我是 UID 1000，容器里的进程却是 UID 0。**

[【跳转到 04:30】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=270) · [【跳转到 04:55】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=295)

### 3.2 揭开映射表：`/proc/self/uid_map` 的三列

答案藏在内核维护的一个文件里。进入容器，查看 `/proc/self/uid_map`：

```bash
podman run --rm alpine cat /proc/self/uid_map
#          0       1000          1
#          ↑        ↑            ↑
#  容器内的UID  宿主机的UID   映射范围(size)
```

这个文件由 **Linux 内核**维护，描述当前进程的 UID 映射关系，共三列：

| 列 | 含义 |
| --- | --- |
| 第 1 列 | 容器内的用户 ID |
| 第 2 列 | 对应的宿主机用户 ID |
| 第 3 列 | 映射范围大小（size） |

这里我们看到 `0 → 1000`，size 为 1。含义是：**容器内的 root，在宿主机上就是 UID 1000 这个普通非特权用户**。内核在背后透明地完成了这件事——**容器进程坚信自己是 root，而宿主机看到的只是 UID 1000**。

[【跳转到 06:10】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=370)

### 3.3 用 `podman top` 同时看两边

想一眼看到映射的两端，可以用 `podman top` 指定列：

```bash
podman run -d --name runtest alpine sleep 1000
podman top runtest huser user
```

`huser` 是宿主机侧的用户，`user` 是容器内的用户。输出里 `root` 与 UID 1000 出现在同一行——**一次就能看到映射的两端**。

### 3.4 反面案例：`--userns=host` 让映射彻底消失

现在做对照实验，加上 `--userns=host`（让容器直接使用宿主机的用户命名空间）：

```bash
podman run --rm --userns=host alpine cat /proc/self/uid_map
#          0          0   4294967295
```

映射彻底变了：**容器内的 0 直接映射到宿主机的 0**，整个约 43 亿（2³²−1）的 ID 区间**一一对应**。也就是说，**里面的 root 就是外面的 root**——攻击者一旦从这里逃出去，落到宿主机上就是货真价实的 root。

这正是无根 Podman 存在的意义，也是**为什么你不该随手使用 `sudo podman`**（除非有明确理由）：`sudo podman` 起出来的容器，映射关系就退化成了上面这种「root 对 root」。

[【跳转到 07:25】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=445) · [【跳转到 07:50】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=470)

---

## 四、用户命名空间的映射规则

### 4.1 原理：内核做了一次「翻译」

**用户命名空间（user namespace）是一个内核特性，它让进程拥有自己的一套用户 ID 视图。**

在容器内部，进程看到的是「完整」的一套用户 ID：root 是 0，某个守护进程用户可能是 1，你的应用用户可能是 1001……**从容器的视角看，一切正常**。

但这些 ID 在与宿主机发生交互之前，内核会把它们**过一遍翻译表**：

| 容器内 | 宿主机上 | 说明 |
| --- | --- | --- |
| 0（root） | 1000 | 就是你的用户 |
| 1 | 100001 | 落在 subuid 区间 |
| 101 | 101001 | 落在 subuid 区间 |

这里的关键是：**那些高于 100000 的 ID，在宿主机上不属于任何真实用户**，所以它们**对任何东西都没有访问权限**。如果攻击者以 root 身份逃出容器，他在宿主机上落地成 UID 1000——**也就是你，而不是真正的 root**。

![用户命名空间的翻译表：容器内 root → 宿主机普通用户，其余 ID 落到无人拥有的高位区间](<assets/Rootless Containers Explained：How Podman Protects Your Host/00545.webp>)

[【跳转到 08:15】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=495) · [【跳转到 09:05】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=545)

### 4.2 规则从哪来：`/etc/subuid` 与 `/etc/subgid`

内核做翻译所依据的规则，来自两个文件：`/etc/subuid` 和 `/etc/subgid`。

![subuid / subgid 的三字段格式与映射公式](<assets/Rootless Containers Explained：How Podman Protects Your Host/00614.webp>)

每行三个字段：

```
用户名:起始宿主机UID:数量
samar:100000:65536
```

含义是：把从 100000 开始的 65536 个 ID 分配给用户 `samar` 使用——**对任何真实应用来说都绰绰有余**。

映射公式也很简单：

```
宿主机 UID = 100000 + 容器内 UID − 1
```

举两个例子：

- 容器内 UID 1 → 宿主机 UID 100000
- 容器内 UID 500 → 宿主机 UID 100499

**唯一的例外永远是 UID 0**：容器内的 root 不落在 subuid 区间里，而是映射到**启动这个容器的那个用户**。这正是我们在第一个实验里看到的：容器里的 root 对应宿主机上的 UID 1000。

[【跳转到 09:49】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=589) · [【跳转到 10:14】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=614) · [【跳转到 10:39】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=639)

---

## 五、实验二：容器内换成非 root 用户，映射会怎么变？

理论讲完，做对照实验：**同一个宿主机、同一套 subuid 配置，只是容器内运行的进程用户不同**，映射会有什么差别？

### 5.1 造一个带非 root 用户的镜像

先写一个 `Containerfile`：基于 Alpine，创建一个专用用户 `appuser`，然后切换到它：

```dockerfile
FROM alpine
RUN adduser -D -u 1500 appuser
USER appuser
CMD ["id"]
```

构建成 `maptest:latest`。[【跳转到 12:01】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=721) · [【跳转到 12:26】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=746)

### 5.2 两个容器，一次对照

```bash
podman run -d --name asroot alpine sleep 1000          # 容器内是 root
podman run -d --name asuser maptest:latest sleep 1000  # 容器内是 appuser

podman top asroot huser user
podman top asuser huser user
```

结果：

- **`asroot`**：`huser` 是 1000（**你自己**），`user` 是 `root`——**容器里的 root，在宿主机上就是你**；
- **`asuser`**：宿主机侧仍是 1000，而容器内的用户是 `appuser`。

[【跳转到 13:16】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=796) · [【跳转到 13:41】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=821)

**这个差别为什么重要？** 因为逃逸后落到哪，完全取决于它：

- 第一个容器逃逸 → 攻击者拿到 **UID 1000**，也就是**你**，连同你的全部权限；
- 第二个容器逃逸 → 攻击者落到宿主机上那个**不属于任何人的高位 ID**（下一节实验三会亲眼验证），**什么都拿不到**。

[【跳转到 14:06】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=846)

---

## 六、把应用改成非 root：Containerfile 的三步模式

在讲第三个实验前，先看一段「为什么会这样」的说明。[【跳转到 15:46】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=946)

**默认是 root，不是因为有人刻意这么选，而是因为没人想过这件事。** 后果是**影响范围（blast radius）极大**：如果你的 Python 服务有漏洞，攻击者就在容器里以 root 落地——他能读**每一个文件**、装工具、甚至顺手翻内核漏洞。整个容器都是他的。**而这一切只需要 Containerfile 里的四行就能避免。**

![`USER` 指令：从这一行往后，所有指令都以该用户运行](<assets/Rootless Containers Explained：How Podman Protects Your Host/01014.webp>)

这个模式分**三步**：

**第一步：用 `useradd` 创建一个专用系统用户。** 没有 home 目录、没有登录 shell——这个用户**只为跑应用而存在**。注意这条 `RUN` 在 `USER` 之前，所以是以 root 执行的，而且这是**故意的**：创建用户本来就需要 root。

**第二步：给应用需要的文件设置属主。** 如果你以 root 复制了文件再切换用户，`appuser` 会读不了它们，所以在这里修好。

**第三步：`USER` 指令。** **从这一行开始**，Containerfile 里后续每一条指令都以 `appuser` 运行；容器运行时，`CMD`/`ENTRYPOINT` 也以 `appuser` 启动。攻击者攻破应用，落地的身份就是 `appuser`：**碰不到系统文件、装不了东西，影响范围被关住了**。

```dockerfile
FROM python:3-alpine
RUN adduser -D -u 1001 appuser
WORKDIR /app
COPY server.py .
RUN chown appuser:appuser /app/server.py
USER appuser
CMD ["python", "server.py"]
```

**关键性质：`USER` 是位置敏感的。** 它在它之前的一切以 root 运行，之后的一切以指定用户运行。因此**构建期的准备工作——装包、建用户、设权限——都必须放在 `USER` 之前**；如果你不小心在 `USER` 之后放了一条需要 root 的 `RUN`，构建就会失败。[【跳转到 17:19】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=1039) · [【跳转到 17:44】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=1064)

心法很简单：**Containerfile 上半段是「准备」，`USER` 之下是「应用」，把两者分开。**[【跳转到 17:49】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=1069)

---

## 七、实验三：同一份代码，两种安全姿态

为了让差别变得完全可触摸，讲者**把同一个 Python 服务构建了两遍**：一遍用不安全默认值，一遍用安全的非 root 版本，然后**同时运行、逐项对比**——谁在运行、怎么映射、应用返回什么。同一份应用，两种完全不同的安全姿态。[【跳转到 18:14】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=1094)

![实验三：同一份代码构建两种镜像，对照运行](<assets/Rootless Containers Explained：How Podman Protects Your Host/01094.webp>)

这个服务会在**每次响应里报告自己的用户 ID 与用户名**，所以只要 curl 一下就立刻知道它**以谁的身份在跑**。[【跳转到 18:50】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=1130)

```bash
# 不安全版：不写 USER
podman build -t demo:insecure .
podman run -d --name insecure -p 8080:8080 demo:insecure

# 安全版：加 USER + chown
podman build -t demo:secure .
podman run -d --name secure -p 8081:8080 demo:secure
```

[【跳转到 19:40】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=1180) · [【跳转到 20:05】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=1205) · [【跳转到 21:20】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=1280) · [【跳转到 21:45】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=1305)

**第一轮：应用自己怎么报？**

| 容器 | 应用报告的 UID | 用户名 |
| --- | --- | --- |
| `insecure` | 0 | `root` |
| `secure` | 1001 | `appuser` |

同样的代码、同样的功能，**权限完全不同**。[【跳转到 22:10】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=1330) · [【跳转到 22:35】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=1355)

**第二轮：从宿主机侧看映射。**

```bash
podman top insecure huser user    # root inside → 宿主机 1000，也就是「你」
podman top secure   huser user    # appuser inside → 宿主机上一个不属于任何人的高位 ID
```

- `insecure` 逃逸 → 攻击者拿到**你的权限**，在宿主机上畅通无阻；
- `secure` 逃逸 → 攻击者落到一个**在系统里属于 nobody 的 ID**——没有 home 目录、没有任何文件、访问不了任何东西，**一无所获**。

[【跳转到 23:00】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=1380) · [【跳转到 23:25】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=1405) · [【跳转到 23:50】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=1430)

**第三轮：功能有受影响吗？** 两个 curl 都能正常返回、都正常服务请求——**这项安全改动对功能零影响**，而且一般来说**没有任何理由不做它**。[【跳转到 24:15】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=1455) · [【跳转到 24:40】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=1480)

**唯一的区别，就是 Containerfile 里为安全版多写的那几行。**

---

## 八、最常见的一次翻车：`subuid` / `subgid` 没配好

到这里为止的一切——用户映射——都依赖一个前提：**`/etc/subuid` 与 `/etc/subgid` 被正确配置**。[【跳转到 25:30】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=1530)

运行时，Podman 会读 `/etc/subuid`，找出可以为命名空间分配哪些宿主机用户 ID。**如果文件不存在，或没有你用户的条目，Podman 会退回到一个最小的单条映射。**[【跳转到 25:42】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=1542)

这对**只用 root 的容器**也许还能跑；但对任何**镜像里有非 root 用户**的情况——比如我们刚建的 UID 1001 的 `appuser`——Podman **无法把这个 ID 映射到宿主机上的任何东西**，于是在试图对容器内的用户执行 `setresuid` 时失败：

```
Invalid argument
```

**这是全新系统上最常见的 Podman 配置错误之一。**[【跳转到 26:05】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=1565)

### 三步修复，顺序不能错

[【跳转到 26:30】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=1590)

**第一步：确认文件存在。** `/etc/subuid` 与 `/etc/subgid` 必须先存在，`usermod` 才能往里写——**有些全新系统上它们根本不存在，而 `usermod` 不会替你创建**。[【跳转到 26:43】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=1603)

**第二步：用 `usermod` 添加映射。** 从 100000 开始的 65536 个 ID，这是给单个用户的标准配额。[【跳转到 27:08】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=1628)

**第三步：`podman system migrate`。** 这是**所有人都会忘**的一步：Podman 会**缓存命名空间配置**，你改了 subuid 文件却不 migrate，Podman 根本不知道。

![最容易忘的一步：改了 subuid 文件后必须 `podman system migrate`](<assets/Rootless Containers Explained：How Podman Protects Your Host/01646.webp>)

讲者把这种场景描述得很形象：你改了文件、跑容器还是失败，你开始加 `sudo` 调试、越来越困惑——**而答案永远是那句：「你跑过 `system migrate` 了吗？」**[【跳转到 27:26】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=1646)

```bash
# 三步，缺一不可，且顺序不能错
sudo touch /etc/subuid /etc/subgid
sudo usermod --add-subuids 100000-165535 --add-subgids 100000-165535 "$USER"
podman system migrate
```

### 实验四：把「全新服务器」复现一遍

讲者说这是整支视频里**最实用**的一个实验：**故意删掉映射**，看错误发生，弄清它为什么失败，再一步步修好。[【跳转到 27:56】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=1676)

1. 先构建一个**需要非 root 用户**的镜像：Alpine + UID 1001 的 `appuser` + `CMD id`，构建成 `apptest:latest`；[【跳转到 29:11】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=1751)
2. 先跑一次确认**现在**是好的（映射在位）；
3. 备份映射，然后**把你用户在两个文件里的条目都删掉**——这就等于一台**没为 rootless Podman 配过的全新 Linux 机器**；
4. 再跑容器 → **报错**：它想在用户命名空间里为 UID 1001 找 subuid 区间却找不到，于是容器运行时在「切到那个用户」时失败。**这就是你在真实世界里会看到的那条报错。**[【跳转到 30:51】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=1851) · [【跳转到 31:16】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=1876)
5. 按三步修回来：**文件存在 → `usermod` 加映射 → `podman system migrate`**；

这里有个很典型的陷阱：[【跳转到 32:56】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=1976) · [【跳转到 33:21】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=2001)

```bash
# 文件改对了，但直接再跑 → 仍然失败！
podman run apptest:latest
# → Podman 缓存了旧的命名空间配置，不会每次运行都重读这两个文件
podman system migrate     # 让它重新加载
podman run apptest:latest # 这次 UID 1001 出现了，完美
```

**三步缺一不可，而且永远不要只做前两步。**[【跳转到 33:46】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=2026) · [【跳转到 34:11】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=2051)

---

## 九、两个必须知道的限制

![限制一：无根容器不能直接绑定 80/443 这类特权端口](<assets/Rootless Containers Explained：How Podman Protects Your Host/02113.webp>)

**限制一：特权端口。** Linux 把 1024 以下的端口保留给 root，所以**无根容器不能直接绑定 80 或 443**。[【跳转到 35:13】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=2113)

解法（第 7 集讲过）：**容器用高位端口，前面放一个反向代理**接管 80 与 443——这样容器留在高位端口上，也保持无根。如果你**确实**需要在 80 端口跑无根容器，可以用 `sysctl net.ipv4.ip_unprivileged_port_start` 降低阈值，但**反向代理几乎总是正确的那套架构**。[【跳转到 35:38】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=2138)

![限制二：raw socket（如 ping）需要 CAP_NET_RAW](<assets/Rootless Containers Explained：How Podman Protects Your Host/02163.webp>)

**限制二：原始套接字（raw socket）。** 最典型的例子是 `ping`——它需要一项叫 `CAP_NET_RAW` 的内核能力来创建原始网络套接字，而**无根容器默认没有它**。可以通过 sysctl 给一个 ping group 范围做系统级授权。[【跳转到 36:03】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=2163)

**这两条都不是死结**：它们有解、有文档、解法也直接。[【跳转到 36:28】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=2188)

---

## 十、把整幅图拼起来：两层防线

![完整图景：第一层是无根运行时，第二层是容器内的非 root 进程](<assets/Rootless Containers Explained：How Podman Protects Your Host/02200.webp>)

- **第一层：无根运行时（rootless runtime）。** 没有 root 守护进程，**容器就是你自己的进程**；用户命名空间保证**即使容器内的 root，也映射成宿主机上的非特权用户**。
- **第二层：容器内的非 root 进程。** 应用进程本身不需要 root——它以一个专用用户运行，**只拿它需要的权限**；攻击者攻破它，落地的身份是 `nobody`。

**这两层是相互独立的：即使其中一层有缺口，另一层依然限制损害。** 这就是**应用到容器上的纵深防御（defense in depth）**——而这两层，都可以用本集的知识做到。[【跳转到 36:40】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=2200) · [【跳转到 37:05】](https://www.youtube.com/watch?v=eNzYIgRCYBk&t=2225)

---

## 小结

- **起点问题**：容器里到底是谁在运行？答案可以用 `id`、`podman top`、`/proc/self/uid_map` 三个工具当场查出来。
- **为什么容器比 VM 更在意这件事**：容器**共享宿主内核**，没有 hypervisor 那道墙，所以**容器内进程的权限直接影响宿主机**。
- **真正无根的三个条件**：① 容器内不是 root；② 容器内的 root ≠ 宿主机的 root；③ 运行时自身不需要 root——**Podman 在设计上三条全满足**。
- **映射实证**：容器内 root 映射到宿主机的普通用户；容器内非 root 用户映射到宿主机上的高位未映射 ID；**这一切由内核透明执行**。
- **同一份应用两种写法**：写与不写 `USER`，功能完全一样，`podman top` 与 curl 的结果却完全不同——**第二种永远是正确选择**。「准备在上、应用在下」，`USER` 之后不会再有 root。
- **踩坑与修复**：搞坏了又修好了 subuid 映射，并记住了**所有人都忘的那一步——`podman system migrate`**（先改文件，再 migrate，顺序不能反）。
- **两个真实限制**：特权端口与 raw socket，都有务实解法（反向代理；`CAP_NET_RAW` / ping group）。
- **最终图景**：无根运行时 + 容器内非 root 进程 = **两层相互独立的防线**。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| rootless container（无根容器） | 以非 root 身份运行、且容器内 root 不映射为宿主机 root 的容器 |
| user namespace（用户命名空间） | 让容器拥有一套自己的用户 ID 视图，内核负责与宿主机之间「翻译」 |
| `uid_map` / `gid_map` | `/proc/<pid>/uid_map` 等文件，记录容器 ID ↔ 宿主机 ID 的映射（三列：容器 ID、宿主机 ID、范围） |
| `subuid` / `subgid` | `/etc/subuid`、`/etc/subgid`，记录分配给某用户的宿主机 ID 区间（如 `samar:100000:65536`） |
| 映射公式 | `宿主机 UID = 100000 + 容器内 UID − 1`；**唯一例外是 UID 0**，它映射到启动容器的那个人 |
| `podman top huser user` | 同时显示宿主机侧用户（huser）与容器内用户（user），一眼看到映射两端 |
| `--userns=host` | 让容器直接用宿主机的用户命名空间，映射退化为 root↔root，等于放弃无根保护 |
| daemonless（无守护进程） | Podman 不像 Docker 那样有 root 守护进程，容器直接是你的进程 |
| Docker socket | 与 root 守护进程通信的接口；**能访问它 ≈ 拥有宿主机 root** |
| `USER` 指令 | Containerfile/Dockerfile 中切换后续指令执行用户的指令，位置敏感（之前 root、之后该用户） |
| blast radius（影响范围） | 一次攻破能波及多大范围；默认 root 会让它大到整个容器 |
| `podman system migrate` | 让 Podman 重新加载（缓存的）命名空间配置——改完 subuid 后必须执行 |
| 特权端口 | 1024 以下、Linux 保留给 root 的端口，无根容器不能直接绑定 |
| CAP_NET_RAW | 创建原始套接字所需的能力，`ping` 依赖它，无根容器默认没有 |
| 纵深防御（defense in depth） | 用多层相互独立的防护叠加；这里指「无根运行时 + 容器内非 root 进程」 |
| VM 逃逸 / hypervisor | 虚拟机有独立内核，逃逸需攻破 hypervisor；容器共享内核，故没有这道边界 |
