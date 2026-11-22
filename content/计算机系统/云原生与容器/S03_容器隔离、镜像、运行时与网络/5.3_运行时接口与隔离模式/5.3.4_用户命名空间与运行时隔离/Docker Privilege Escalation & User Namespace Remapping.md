# Docker 提权攻防实测：从「docker 组等于 root」到用户命名空间重映射（userns-remap）

> 视频源：[Docker Privilege Escalation & User Namespace Remapping](https://www.youtube.com/watch?v=UdVMdok6TYY)（YouTube，约 20 分钟）。本文基于视频演说图文稿整理，时间戳可跳转到原视频对应位置。

## 本讲要解决的核心问题（SCQA）

**背景**：只要你用过 Docker，多半就把自己的用户加进过 **docker 组**——不加的话，跑 `docker` 命令就得 `sudo`，太麻烦，于是教程都教你「把用户加进 docker 组」。

**冲突**：可这就等于**把 root 权限直接发给了这个用户**。视频开头有句话很扎心：**「我这辈子没见过一个用 Docker 又不会中 Docker 提权的人。」** 只要你在 docker 组里，一条命令就能拿到系统的 root。[【跳转到 00:00】](https://www.youtube.com/watch?v=UdVMdok6TYY&t=0)

**疑问**：docker 提权到底是怎么发生的？官方文档说用 **用户命名空间重映射（userns-remap）** 就能防住——它真的防住了吗？如果防不住，正确的解法又是什么？

**回答（中心思想）**：docker 组的成员之所以等于 root，是因为他能用 `docker run -v /:/mnt` **把宿主机的整个文件系统挂进容器**、并以容器里的 root 身份随意读写。**userns-remap 能挡住「容器内 → 逃逸到宿主机」，但挡不住「宿主机上已经能敲 docker 命令的人」**——因为那人可以再用 `--userns=host` 把保护绕过去。所以真正的解法不是加个开关，而是**别把用户加进 docker 组**；更彻底地说，**「Docker 安全始于主机安全」**。[【跳转到 17:10】](https://www.youtube.com/watch?v=UdVMdok6TYY&t=1030)

---

## 一、前提与设定：一个「已经拿到普通账号」的攻击者

先立好假设（这也是真实渗透的典型处境）：[【跳转到 00:25】](https://www.youtube.com/watch?v=UdVMdok6TYY&t=25)

1. 攻击者**已经拿到初始立足点**——比如一个 `www-data` 之类的普通用户；
2. 攻击者**不知道这个用户的密码**。因为如果知道密码，直接 `sudo bash` 就行了，**根本用不着 docker**。

也就是说：攻击者手上只有一个**低权限账户**，而这个账户**恰好属于 docker 组**。接下来看它能干出什么。

---

## 二、攻击面演示 1：一条命令挂载整个宿主机

只要在 docker 组里，就能直接 `docker run`。攻击的核心是**用 `-v` 把宿主机根目录挂进容器**：

```bash
docker run -it --rm -v /:/mnt alpine sh
```

这里用了 `alpine` 镜像——它**默认以 root 运行**。进入容器后，`/mnt` 里就是**宿主机的整个文件系统**。[【跳转到 00:50】](https://www.youtube.com/watch?v=UdVMdok6TYY&t=50)

![把宿主机根目录挂进容器的 /mnt，容器里的 root 就能读写整个主机](<assets/Docker Privilege Escalation & User Namespace Remapping/00050.webp>)

容器里现在是 **root**，于是：

- 进 `/mnt/root` 直接读走 `flag.txt`；
- 改写 **`/etc/shadow`**、**`/etc/passwd`**，**新建一个 admin 用户**来**植入持久化后门**。

**一次挂载，就拿到了整台机器的控制权。**[【跳转到 01:40】](https://www.youtube.com/watch?v=UdVMdok6TYY&t=100)

![容器内 root 视角：挂载进来的宿主机文件系统任你读写](<assets/Docker Privilege Escalation & User Namespace Remapping/00075.webp>)

**注意**：挂载卷时**不要用「默认以非 root 运行」的镜像**。像 Alpine 这种默认 root 的镜像最省事；如果碰上默认非 root 的镜像，攻击者还有后手（见下）.[【跳转到 02:05】](https://www.youtube.com/watch?v=UdVMdok6TYY&t=125)

---

## 三、攻击面演示 2：镜像默认非 root 时，用 `-u root` 翻盘

换个**默认以非 root 运行**的镜像再来一遍。挂载依旧：

```bash
docker run -it --rm -v /:/mnt <镜像> sh
whoami      # 非 root（提示符是 $ 而不是 #）
```

这次进 `/mnt/root` 会**权限被拒绝**——因为挂进来的文件都归 root 所有，而当前是非 root 用户。又因为用的是 **Alpine 这种精简镜像**，它不带 `sudo` / `su`（需要 SUID 才行），所以没法就地提权。[【跳转到 03:20】](https://www.youtube.com/watch?v=UdVMdok6TYY&t=200)

![默认非 root 的镜像里，普通用户进不了归 root 所有的 /mnt/root](<assets/Docker Privilege Escalation & User Namespace Remapping/00200.webp>)

**解法极其简单**：在命令行里**直接把容器用户指定成 root**：

```bash
docker run -it --rm -u root -v /:/mnt <镜像> sh
whoami      # root（提示符变 #）
```

进了 `/mnt/root`、读到 `input.txt`——整个系统又到手了。视频强调：**这招不是每次都灵，但大多数时候都灵**。你也可以指定别的用户（比如 `nobody`）来观察效果，但它没有任何特权。[【跳转到 04:21】](https://www.youtube.com/watch?v=UdVMdok6TYY&t=261)

![用 -u root 覆盖镜像默认用户，容器内又是 root](<assets/Docker Privilege Escalation & User Namespace Remapping/00236.webp>)

**小结这一段**：只要你在 docker 组里，就能——挂载整个文件系统、访问敏感文件、修改文件、改 `/etc/shadow`+`/etc/passwd` 建新用户；若镜像默认非 root，就 `-u root` 拿回 root shell。[【跳转到 05:35】](https://www.youtube.com/watch?v=UdVMdok6TYY&t=335)

---

## 四、官方推荐的解法：用户命名空间重映射（userns-remap）

那怎么防？视频提醒：这类「解法」里**有些是错的、有些是被误解的**，得看清楚。

先补概念。**Linux 命名空间为进程提供隔离**，限制它们访问系统资源，而进程本身对此无感。**Docker 不过是命名空间和 cgroup 的一层「花哨包装」**（它们都是 Linux 内核的一部分）——命名空间在**你的容器和整个系统之间竖起一道屏障**。[【跳转到 07:21】](https://www.youtube.com/watch?v=UdVMdok6TYY&t=441)

Docker 官方文档的说法是：**防止容器内提权的最佳方式，是让应用的进程以非特权用户运行**；**对于那些必须以 root 运行的进程，可以把它在宿主机上重映射成一个低权限用户**。这个被重映射的用户会被分配一段 **UID 范围**，这些 UID **在命名空间内和普通 UID 一样工作，但在宿主机上毫无特权**。[【跳转到 07:46】](https://www.youtube.com/watch?v=UdVMdok6TYY&t=466)

一句话：**在「另一个命名空间」里新建一个用户，它在那个命名空间里是 root，但在宿主机上只是个毫无力量的低权限用户。**

![用户命名空间重映射：命名空间内的 root，在宿主机上只是低权限用户](<assets/Docker Privilege Escalation & User Namespace Remapping/00466.webp>)

---

## 五、动手配置 userns-remap

按文档配置（视频做了「复制粘贴」演示）：[【跳转到 08:36】](https://www.youtube.com/watch?v=UdVMdok6TYY&t=516)

1. **建一个组**（如 `dockremap`），并**建一个不分配登录 shell 的用户**；
2. 在 **`/etc/subuid` 和 `/etc/subgid`** 里，为它指定一段 UID/GID 范围——这就是「命名空间内最不特权的那些 ID」所对应的范围；
3. 在 Docker 的 **`daemon.json`** 里开启重映射（如 `"userns-remap": "default"`）；
4. **重启 Docker**（`systemctl restart docker`）。

![在 daemon.json 中启用 userns-remap](<assets/Docker Privilege Escalation & User Namespace Remapping/00570.webp>)

### 5.1 生效后的效果：主机文件都归 `nobody`

配好后再来试同样的挂载招式。此时**挂进来的宿主机文件系统全都归 `nobody` 所有**——容器里的 root **再也进不去** `/mnt/root`，因为他在宿主机上**没有相应权限**。[【跳转到 10:33】](https://www.youtube.com/watch?v=UdVMdok6TYY&t=633)

![开启 userns-remap 后，挂进来的文件归 nobody 所有，容器内 root 也读不了](<assets/Docker Privilege Escalation & User Namespace Remapping/00633.webp>)

看起来成功了？——**先别急。**

---

## 六、保护的真实边界：它只防「逃逸」，不防「宿主机上敲命令的人」

视频点破关键：**这个机制是用来防「容器逃逸」的**。

**场景**：你的容器跑着一个有漏洞的 MySQL；攻击者借漏洞进了容器。此时**他读不到宿主机**——这正是防逃逸的意义。[【跳转到 11:20】](https://www.youtube.com/watch?v=UdVMdok6TYY&t=680)

**但它挡不住另一种人**：**已经能访问宿主机的人**。他可以**指定不同的命名空间**，把保护直接绕过去：

```bash
docker run -it --rm --userns=host -v /:/mnt alpine sh
```

这样一来，重映射就被**覆盖**了——`--userns=host` 让容器回到宿主机的用户命名空间，于是**又能读到 `/mnt/root/flag.txt`**。[【跳转到 11:58】](https://www.youtube.com/watch?v=UdVMdok6TYY&t=718)

![用 `--userns=host` 在运行时覆盖，就能绕过 userns-remap](<assets/Docker Privilege Escalation & User Namespace Remapping/00718.webp>)

换句话说：**docker 命令本身的权限，比你容器里的权限更大**。默认你是被重映射的用户，**但没人拦得住你把它覆盖成 `host`**。若攻击者已经拿到 `www-data` 账户，**他在运行时改一改配置**，这些保护就形同虚设。

**结论**：**userns-remap 保护「从容器内部向宿主机逃逸」，但不保护「在宿主机上运行命令的人」**——只要你能控制 docker 命令，这层保护就不起作用。[【跳转到 13:28】](https://www.youtube.com/watch?v=UdVMdok6TYY&t=808)

---

## 七、真正的解法：别把用户加进 docker 组

既然重映射会被绕过，最简单有效的办法是：**不要给任何人（任何用户）加入 docker 组。**

这样，攻击者就算拿到 `www-data`，**也得先知道 `sudo` 密码才能执行 docker**——而正是「不知道密码」这个前提，让他动弹不得。[【跳转到 13:53】](https://www.youtube.com/watch?v=UdVMdok6TYY&t=833)

![最简单的解法：别把用户加进 docker 组，提权就需要密码](<assets/Docker Privilege Escalation & User Namespace Remapping/00833.webp>)

**为什么要有密码就有用？** 因为 **`sudo docker …` 等价于「把人加进 docker 组」**，区别只在于：加进组**不需要密码**，而 `sudo` **需要密码**。[【跳转到 14:34】](https://www.youtube.com/watch?v=UdVMdok6TYY&t=874)

### 7.1 但在公司里会变复杂

现实里有个绕不开的角色：**运维 / DevOps 工程师**，他的职责就是管 Kubernetes 集群或 Docker 容器。**他必然知道 `sudo` 密码**。

于是你只有两种选择：加进 docker 组（视频不推荐），或给他 `sudo` 权限。有人会说：那就**在 `sudoers` 里限定他只能执行 `sudo docker`**。但视频提醒——**你其实间接把「管理员访问」交出去了**：能给 root 用户开的口子，最终都是 root。（公司里越往后越复杂，往往还得叠加 **seccomp 限制系统调用、加认证**等手段，**没有轻松的捷径**。）[【跳转到 16:14】](https://www.youtube.com/watch?v=UdVMdok6TYY&t=974)

![用 sudo 密码挡住提权——但公司里知道密码的人本就是风险来源](<assets/Docker Privilege Escalation & User Namespace Remapping/00874.webp>)

---

## 八、更高一层：Docker 安全始于主机安全

视频反复强调一句话：**「Docker 安全始于主机安全」（Docker security starts from host security）**——**先保护好你的主机，再谈 Docker 安全**。他推荐了一本不错的安全电子书，并留了个小测验：**为什么我们要用 `chroot /mnt`？** 提示是去看 **GTFOBins**（上面收录了大量「被允许执行的程序如何反手变成提权工具」的案例）。[【跳转到 17:10】](https://www.youtube.com/watch?v=UdVMdok6TYY&t=1030)

核心结论：**只要你身处 docker 组（或用 sudo 能跑 docker、或存在 SUID 程序），就极难避开 Docker 提权**——因为**能用 Docker，本质上就约等于拥有 root**。[【跳转到 17:35】](https://www.youtube.com/watch?v=UdVMdok6TYY&t=1055)

**收口的一句话**：

- **单机/个人用户**：别把任何用户加进 docker 组，提权就绕不开密码；
- **组织环境**：得叠加更多措施（受限 sudo、seccomp、认证等）。

---

## 九、userns-remap 的代价：挂载会变麻烦

最后视频补了一个**使用限制**：一旦开启 Docker 重映射，**你甚至无法正常挂载文件系统**。而挂载卷在 Docker 里是再常见不过的操作。开启重映射后，想让容器能读某个宿主机目录，往往得**把那个目录设成「world readable（全局可读/可执行）」**——视频说得很直白：**这也不是个好主意，但这就是你必须忍受的代价**。[【跳转到 18:50】](https://www.youtube.com/watch?v=UdVMdok6TYY&t=1130)

![开启 userns-remap 后，挂载宿主机目录会受限，得把目录设成全局可读](<assets/Docker Privilege Escalation & User Namespace Remapping/01105.webp>)

---

## 小结

- **docker 组 ≈ root**：能用 docker 的账户，可以 `docker run -v /:/mnt` **把宿主机整个文件系统挂进容器**，并以容器内 root 身份读敏感文件、改 `/etc/shadow`、**建后门用户**。
- **非 root 镜像也拦不住**：一句 `-u root` 就能把容器用户覆盖成 root。
- **userns-remap 的作用与边界**：把容器内 root **映射**成宿主机上的低权限用户，**能防「容器内逃逸到宿主机」**；但**挡不住「宿主机上能敲 docker 命令的人」**——他可以用 **`--userns=host`** 绕过。
- **最有效的一招**：**别把用户加进 docker 组**；`sudo docker` 与「加进组」等价，只是**多了密码这道门槛**。
- **组织环境更复杂**：受限 sudo 仍等于间接给管理员权限，往往还要叠加 seccomp、认证等。
- **总原则**：**Docker 安全始于主机安全**；userns-remap 的代价是**挂载宿主机目录会受限**（常需设成 world-readable）。

---

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| docker 组 | 加入后即可无需密码运行 docker，效果约等于拿到 root |
| `docker run -v /:/mnt` | 把宿主机根目录挂进容器；提权演示的核心命令 |
| `-u root` | 覆盖镜像默认用户，让容器内进程以 root 运行 |
| 命名空间 | 内核提供的隔离机制；Docker 是它的「包装层」 |
| userns-remap | 用户命名空间重映射：把容器内 UID/root 映射成宿主机低权限用户 |
| `--userns=host` | 运行时覆盖，让容器回到宿主机用户命名空间，绕过重映射 |
| `/etc/subuid`·`/etc/subgid` | 为重映射用户指定可用的 UID/GID 范围 |
| `daemon.json` | Docker 守护进程配置；`"userns-remap"` 在此开启 |
| 容器逃逸 | 从容器内部跳出到宿主机；userns-remap 主要防的就是它 |
| GTFOBins | 收录「被允许的程序如何反手提权」的清单，渗透常用 |
| seccomp | 限制进程可调用的系统调用，用于收紧容器行为 |
