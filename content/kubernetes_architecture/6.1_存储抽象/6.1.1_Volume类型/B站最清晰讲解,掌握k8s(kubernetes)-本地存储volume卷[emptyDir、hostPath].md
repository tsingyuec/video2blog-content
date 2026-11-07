# 本地存储卷 emptyDir 与 hostPath：数据到底存在哪、什么时候会被删

> 本文整理自 B 站视频《[B站最清晰讲解,掌握k8s(kubernetes)-本地存储volume卷[emptyDir、hostPath]](https://www.bilibili.com/video/BV1HZY5z1Ecv/)》。文中的机制、命令与实验结论均来自该视频的「图-字幕」图文稿，可逐句核对。存储卷的完整类型清单（配置卷、元数据卷、网络卷等）另见同目录的 [《K8S 存储卷的类型与来源》](<5.简单懂点K8S的存储(Volume／PV／PVC／StorageClass).md>)。

## 本讲要解决的核心问题（SCQA）

**背景（S）**：容器是从镜像启动的，写进容器文件系统的数据，会随着容器的消亡而消亡，无法持久化。所以 Kubernetes 提供 **volume（数据卷）** 来解决数据的存放问题——它的作用和 Docker 里的 volume 是一样的。[【跳转到 00:05】](https://www.bilibili.com/video/BV1HZY5z1Ecv/?t=5)

**冲突（C）**：但 volume 有很多类型。最基础的**宿主机存储卷（本地存储）**就有两种——`emptyDir` 和 `hostPath`。它们看起来都是「把宿主机上的一个目录挂进容器」，那它们到底把数据放在宿主机上的哪个位置？Pod 被删掉以后，数据还在不在？

**疑问（Q）**：`emptyDir` 和 `hostPath` 的**目录结构、生命周期和用法**分别是什么样的？

**回答（中心思想 A）**：两者的区别全在**生命周期**上。`emptyDir` 是 kubelet 在宿主机上**临时创建**的目录，**和 Pod 同生共死**——Pod 一删，目录连同数据一起消失；`hostPath` 则是直接复用宿主机上的一个**既有路径**，**比 Pod 活得久**——Pod 删了，宿主机上的数据还在。理解这两点，本讲的实验都会变得顺理成章。

## 一、为什么需要 Volume：容器数据会「随容器消亡」

先看问题本身。容器启动后，对文件系统的改动都发生在镜像之上的可读写层；一旦容器重启或销毁，这一层就被丢掉，容器会以「干净」的状态重新开始，之前写的文件就没了[【跳转到 00:10】](https://www.bilibili.com/video/BV1HZY5z1Ecv/?t=10)。

而 volume 在 Kubernetes 里，本质上就**对应磁盘上的一个目录**：把这个目录挂进容器，容器对它的读写就落在了宿主机的存储上，从而能跨容器重启保留数据[【跳转到 00:10】](https://www.bilibili.com/video/BV1HZY5z1Ecv/?t=10)。

视频把它要解决的场景归纳成三类[【跳转到 00:35】](https://www.bilibili.com/video/BV1HZY5z1Ecv/?t=35)：

- **同一个 Pod 内多个容器要共享数据**。例如一个项目：由 `initContainer`（初始化容器）先 `git clone` 拉取源码、切到目标分支，之后主容器（main container）再读取这份源码去运行。代码不能存在 init 容器自己身上（它执行完就没了），必须存到一个双方都能访问的位置。
- **Pod 要访问宿主机上的目录**。例如采集类 Pod 需要读取宿主机的内核信息、网络信息、文件信息。
- **多个 Pod 之间要共享文件/目录**。例如一个 Web 服务接受用户上传，文件要存到某个共享位置，后续负载均衡访问也不受影响。

![K8S 中 volume 的定位：宿主机存储卷分为 emptyDir 与 hostPath 两类](assets/B站最清晰讲解,掌握k8s(kubernetes)-本地存储volume卷[emptyDir、hostPath]/00010.webp)

## 二、Volume 按生命周期怎么分类

视频给了一个很有用的分类视角：volume 可以按不同应用场景分成多种类型[【跳转到 01:50】](https://www.bilibili.com/video/BV1HZY5z1Ecv/?t=110)：

- **临时的存储**：存储卷与 Pod 是**生命周期绑定**的关系——Pod 消亡，卷里的内容也被销毁；
- **跟随数据集本身**：数据卷跟着底层数据集走，只要数据集文件还在，下次挂载就没问题；
- **远程存储**：通过远程存储方式实现。

本讲只聚焦第一类的两个代表——**宿主机存储卷（本地存储）**：`emptyDir` 和 `hostPath`[【跳转到 02:15】](https://www.bilibili.com/video/BV1HZY5z1Ecv/?t=135)。

## 三、emptyDir：随 Pod 一起生、一起死的临时目录

### 3.1 它在宿主机上的位置

`emptyDir` 的机理是：Pod 所在的那台宿主机（节点）上，会创建一个**临时目录**作为这个卷的存储介质，路径规则大致是[【跳转到 02:40】](https://www.bilibili.com/video/BV1HZY5z1Ecv/?t=160)：

```
/var/lib/kubelet/pods/<Pod 的 ID>/volumes/kubernetes.io~empty-dir/<volume 的名字>
```

拆开看：先是最外层 `kubelet` 管理 Pod 的目录，接着是该 Pod 的 ID，再往下是固定的 `volumes` 路径，然后是类型目录（`kubernetes.io~empty-dir`），最后是我们自己给这个卷起的名字。创建好这个临时目录后，Kubernetes 再把它挂载到 Pod 里对应的容器中。

### 3.2 生命周期特点与应用场景

`emptyDir` 最大的特点就是**生命周期与 Pod 相同**：整个 Pod 被销毁后，这个临时目录也会被删除[【跳转到 03:05】](https://www.bilibili.com/video/BV1HZY5z1Ecv/?t=185)。它适合「临时性存储、不在意长期持久化、丢了也不敏感」的场景，例如前面说的拉取 Git 源码、做临时数据操作[【跳转到 03:30】](https://www.bilibili.com/video/BV1HZY5z1Ecv/?t=210)。

![emptyDir 的说明与典型用途：与 Pod 生命周期一致的临时存储](assets/B站最清晰讲解,掌握k8s(kubernetes)-本地存储volume卷[emptyDir、hostPath]/00085.webp)

![emptyDir 的两个要点：临时存储、容量可限制（如 128Mi）](assets/B站最清晰讲解,掌握k8s(kubernetes)-本地存储volume卷[emptyDir、hostPath]/00110.webp)

### 3.3 动手：init 容器写文件，主容器读文件

视频用一份 Deployment 演示。它下面有两个容器：一个 **init 容器**（用 busybox 镜像，起名 `b1`）和一个**主容器**（用 nginx 镜像），两者共享同一个 `emptyDir`[【跳转到 03:55】](https://www.bilibili.com/video/BV1HZY5z1Ecv/?t=235)。关键写法有两处：

- **`volumeMounts`**：指定「挂到容器里的哪个路径」和「引用哪个卷」。挂载目标路径（`mountPath`）很容易理解——把卷挂到容器里的哪个目录；这里把它挂到了 nginx 的 `html` 目录，方便直接用 `curl` 访问 Pod 提供的 nginx 服务、看到文件内容[【跳转到 04:20】](https://www.bilibili.com/video/BV1HZY5z1Ecv/?t=260)。`name` 则填「引用的卷名」。
- **`volumes`**：和容器同级的一个数组，声明卷本身：给卷取个名字（视频里叫 `code-tempdir`），并声明它的介质类型是 `emptyDir`；`emptyDir` 下还能设属性，比如这个临时目录**容量上限**（视频里设成了 `128Mi`）[【跳转到 05:10】](https://www.bilibili.com/video/BV1HZY5z1Ecv/?t=310)。

然后是行为：init 容器执行时，往挂载目标路径下写一个 `index.php`，内容是一行 `echo hello world`；主容器也挂载同一个卷、挂到相同的 nginx `html` 路径[【跳转到 06:00】](https://www.bilibili.com/video/BV1HZY5z1Ecv/?t=360)。于是整条链路是：

```
init 容器写入 → 存进 emptyDir 临时目录 → 主容器把同一目录挂到 html → 访问 Pod:80 看到内容
```

访问 Pod 的 80 端口打开这个文件，就显示出了 `hello world`——这模拟了部署项目时「init 容器 clone 源码 → 存到临时目录 → 主容器读同一份源码运行」的过程[【跳转到 06:50】](https://www.bilibili.com/video/BV1HZY5z1Ecv/?t=410)。

![实验效果：init 容器写入 emptyDir 的文件，被主容器通过 nginx 提供出来](assets/B站最清晰讲解,掌握k8s(kubernetes)-本地存储volume卷[emptyDir、hostPath]/00730.webp)

### 3.4 验证一：到宿主机上找到这个目录、并验证「同一份数据」

光看不练不算数。要确认文件确实落在宿主机上，可以这样做[【跳转到 03:30】](https://www.bilibili.com/video/BV1HZY5z1Ecv/?t=210)：先 `kubectl get pods -o wide` 拿到 Pod 所在节点，再登到那台节点上，用 `find` 去找那个文件：

```bash
find / -name index.php
```

结果会看到它正躺在前面讲的路径里：`/var/lib/kubelet/pods/<pod-id>/volumes/kubernetes.io~empty-dir/code-tempdir/index.php`[【跳转到 14:08】](https://www.bilibili.com/video/BV1HZY5z1Ecv/?t=848)。而路径里的 `<pod-id>`，正是该 Pod 在 etcd 里存储的 UID——两边能对上。

![在宿主机上顺着 Pod 的 UID 找到了 emptyDir 的临时目录与其中的文件](assets/B站最清晰讲解,掌握k8s(kubernetes)-本地存储volume卷[emptyDir、hostPath]/00848.webp)

接着做一个「反证」：直接在宿主机的这个目录里修改文件（例如给内容补上几个字符），再访问 Pod，页面内容也随之改变[【跳转到 16:23】](https://www.bilibili.com/video/BV1HZY5z1Ecv/?t=983)。这说明宿主机上的目录和容器里看到的是**同一份数据**——容器读的就是宿主机上这个临时目录。

![在宿主机上改动文件后，访问 Pod 得到的内容同步变化，证明二者是同一份数据](assets/B站最清晰讲解,掌握k8s(kubernetes)-本地存储volume卷[emptyDir、hostPath]/00983.webp)

### 3.5 验证二：删掉 Deployment，临时目录随之消失

最后验证生命周期。注意**不能直接删 Pod**——Deployment 发现副本为 0 会把 Pod 重新拉起来；要删就删 Deployment[【跳转到 17:13】](https://www.bilibili.com/video/BV1HZY5z1Ecv/?t=1033)：

```bash
kubectl delete deployment <name>
```

再回到节点上看刚才那个路径——**目录已经不存在了**[【跳转到 17:38】](https://www.bilibili.com/video/BV1HZY5z1Ecv/?t=1058)。这就实证了 `emptyDir` 的特征：生命周期与 Pod 紧密相关，Pod 删了，连同它在宿主机上创建的临时目录一起没了。

![删除 Deployment 后，回到节点看 emptyDir 的目录已不存在](assets/B站最清晰讲解,掌握k8s(kubernetes)-本地存储volume卷[emptyDir、hostPath]/01033.webp)

## 四、hostPath：直接复用宿主机路径，能「活」过 Pod

### 4.1 特点：与 emptyDir 的核心区别在哪

`hostPath` 是另一种宿主机存储卷：它以 Pod 所在宿主机上的**某个路径**作为卷的存储介质，挂到容器里[【跳转到 08:05】](https://www.bilibili.com/video/BV1HZY5z1Ecv/?t=485)。它有几个要点：

- **数据的持久性取决于宿主机**：文件在不在、磁盘健不健康，取决于这台主机；磁盘正常，挂载就没问题；
- **Kubernetes 感知不到它的容量**：`hostPath` 不像 `emptyDir` 那样能限制大小；
- **Pod 被销毁后，`hostPath` 的卷不会被销毁**——这是它和 `emptyDir` 最关键的差别[【跳转到 08:30】](https://www.bilibili.com/video/BV1HZY5z1Ecv/?t=510)。它更像 Docker Compose 里直接用绝对路径挂载的方式。

它的典型场景是**与宿主机本身属性相关的采集/监控**：把宿主机上的 `/proc`、`/sys` 之类路径以只读方式挂进容器，让容器读取宿主机的文件与指标，从而上报采集信息[【跳转到 08:55】](https://www.bilibili.com/video/BV1HZY5z1Ecv/?t=535)。

![hostPath 的特点：以宿主机路径为介质、K8S 无法感知容量、不随 Pod 删除而销毁](assets/B站最清晰讲解,掌握k8s(kubernetes)-本地存储volume卷[emptyDir、hostPath]/00510.webp)

![hostPath 的典型场景：以只读方式挂载宿主机路径，采集/监控宿主机自身指标](assets/B站最清晰讲解,掌握k8s(kubernetes)-本地存储volume卷[emptyDir、hostPath]/00535.webp)

### 4.2 动手：只读（readOnly）挂载实验

资源清单和前面类似，只把卷的类型从 `emptyDir` 换成 `hostPath`，并指明「用宿主机上的哪个绝对路径」——视频里写的是 `/k8s/data`[【跳转到 10:10】](https://www.bilibili.com/video/BV1HZY5z1Ecv/?t=610)。`hostPath` 的**默认模式**是：如果这个目录不存在，就帮你创建出来。容器这边则把这个宿主机的 `/k8s/data` 挂到 nginx 的 `html` 目录，并加上 **`readOnly: true`**，即**只读挂载**[【跳转到 18:45】](https://www.bilibili.com/video/BV1HZY5z1Ecv/?t=1125)。

实验里出现了两个值得讲的现象：

- **访问返回 403**：因为 `html` 目录被一个**空的**宿主机目录覆盖了，里面没有 `index.html`，自然访问不到[【跳转到 20:17】](https://www.bilibili.com/video/BV1HZY5z1Ecv/?t=1217)。
- **容器内写入被拒**：进容器往该目录写文件/创建目录都失败，提示「只读文件系统」——因为前面加了只读挂载[【跳转到 21:07】](https://www.bilibili.com/video/BV1HZY5z1Ecv/?t=1267)。

![空目录覆盖了 nginx 默认首页，访问得到 403](assets/B站最清晰讲解,掌握k8s(kubernetes)-本地存储volume卷[emptyDir、hostPath]/01192.webp)

这里有个**极易混淆的坑**，视频特意强调[【跳转到 21:42】](https://www.bilibili.com/video/BV1HZY5z1Ecv/?t=1302)：`readOnly` **只约束容器内对挂载点的操作**，并不影响宿主机上的读写规则。也就是说——**容器里写不了，不等于宿主机上写不了**。宿主机上仍然可以用 root 账号往 `/k8s/data` 里写文件（登录宿主机用的账号权限和容器内的只读限制是两码事）[【跳转到 22:32】](https://www.bilibili.com/video/BV1HZY5z1Ecv/?t=1352)。所以在宿主机上写入 `index.html` 后，容器/页面马上就能读到它（显示 `hello hostPath`）。

### 4.3 验证：删掉 Pod，宿主机的数据仍在

`hostPath` 与 `emptyDir` 的差别就在这里验收：把 Pod 删掉，宿主机上 `/k8s/data` 里的数据**依然存在**；重新 `apply` 拉起 Pod、再挂载进去，之前写的内容照样能访问到[【跳转到 24:03】](https://www.bilibili.com/video/BV1HZY5z1Ecv/?t=1443)。这说明它的数据不会随 Pod 的销毁而销毁。

但反过来想也很「危险」：如果只是挂载宿主机的路径来采集目标信息，Pod 哪天被删了数据却还在，说明这份数据其实并不属于 Pod——所以它的定位就是「和宿主机本身相关」的那类存储。

![hostPath 总结：与宿主机绑定、不随 Pod 生命周期销毁](assets/B站最清晰讲解,掌握k8s(kubernetes)-本地存储volume卷[emptyDir、hostPath]/01501.webp)

## 五、emptyDir 与 hostPath 对照

| 维度 | emptyDir | hostPath |
| --- | --- | --- |
| 存储位置 | kubelet 在宿主机上**临时创建**的目录 | 宿主机上**既有的某个路径** |
| 生命周期 | 与 Pod 相同，Pod 删除即销毁 | 不随 Pod 删除而销毁，数据保留 |
| 容量感知 | 可设上限（如 `sizeLimit: 128Mi`） | Kubernetes **无法感知**容量 |
| 数据留在哪 | 由 kubelet 管理的 Pod 专属目录 | 由宿主机自身决定 |
| 典型用途 | 临时数据、init 容器与主容器共享中间产物 | 采集/监控宿主机自身（常配 `readOnly`） |
| 主要风险 | Pod 一删数据就没了 | Pod 漂移后「找不到」原来节点的数据 |

## 小结

- **volume 本质是宿主机上的一个目录**，把它挂进容器，数据就能跨容器重启保留。
- **`emptyDir`**：kubelet 在宿主机上创建临时目录（`/var/lib/kubelet/pods/<pod-id>/volumes/kubernetes.io~empty-dir/<卷名>`），**生命周期与 Pod 相同**，Pod 删了目录就没；适合临时存储和数据丢失不敏感的场景，可限制容量。
- **`hostPath`**：直接用宿主机上的路径作卷，**比 Pod 活得久**，Kubernetes 无法感知容量；适合采集/监控宿主机，通常配只读挂载。
- **只读挂载**只限制容器内的写入，不影响宿主机上的读写——这是最容易踩的坑。
- **两者的根本区别就是一个字：生命周期**。选哪个，取决于你要的数据是「随 Pod 走」还是「留在宿主机上」。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| Volume（数据卷） | 宿主机上的一个目录，挂进容器供其读写，以保留数据 |
| emptyDir | 随 Pod 创建/销毁的临时卷，kubelet 在宿主机上创建对应目录 |
| `kubernetes.io~empty-dir` | emptyDir 在宿主机上目录名里的类型标识 |
| sizeLimit | 限制 emptyDir 可用容量的字段 |
| hostPath | 直接复用宿主机既有路径的卷，不随 Pod 销毁 |
| readOnly | 只读挂载，仅限制容器内对挂载点的写入 |
| initContainer | 在主容器之前运行的初始化容器，常用来准备数据 |
| volumeMounts | 容器侧声明「把哪个卷挂到容器哪个路径」 |
| 生命周期 | 卷的数据从创建到销毁所跟随的对象（Pod 或宿主机） |
