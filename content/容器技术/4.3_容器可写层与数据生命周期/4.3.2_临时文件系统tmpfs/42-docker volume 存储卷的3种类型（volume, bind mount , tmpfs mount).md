# Docker 存储的三种落点：bind 挂宿主目录、volume 落 /var/lib/docker、tmpfs 进内存

> 本文整理自 B 站视频《42-docker volume 存储卷的3种类型（volume, bind mount , tmpfs mount)》（UP 主：白眉大叔89），依据视频演说图文稿逐窗口核对、纠正自动字幕错拼后整理。
> 字幕来自 B 站 AI 字幕，已纠正 `/var/lib/docker`、bind mount、`docker inspect`、`--mount type=tmpfs` 等识别错误，术语按标准写法呈现。
> 视频地址：[BV1w3xCe1ENY](https://www.bilibili.com/video/BV1w3xCe1ENY/)

## 本讲要解决的核心问题（SCQA）

**背景**：用 Docker 跑容器时，数据"放哪里"取决于你用的挂载方式。平时我们最熟的是 `-v`，但 `-v` 后面跟的东西不同，数据落的地方其实是三个完全不同的区域。

**冲突**：三种存储类型分别落在**宿主机目录**、**Docker 数据目录 `/var/lib/docker`** 和**内存**里；可光看命令很难一下子分清到底挂到了哪，而且"想把数据放进内存"这一步，还必须换一个参数才做得到。

**疑问**：Docker 到底有哪三种存储类型、各自落在哪？怎么用 `docker inspect` 分辨它们？`-v` 的两种写法怎么区分？放内存又该怎么写？

**回答（中心思想）**：Docker 存储分三种，**对应三个落点**——**bind** 挂到宿主机的某个目录，**volume** 落在 Docker 的数据目录 `/var/lib/docker/volumes` 下，**tmpfs** 直接放进宿主机的内存。用 `docker inspect` 看 `Mounts` 的 `Type` 字段即可分辨（`bind` / `volume` / `tmpfs`）。写法上的规律是：**`-v <绝对路径>:...` 即 bind，`-v <卷名>:...`（含匿名卷、具名卷）即 volume**；而**要挂到内存，必须改用 `--mount type=tmpfs`**。

## 一、Docker 的三种存储类型，对应三个"落点"

课程开篇就点明：Docker 存储分三种类型——**一个是针对宿主机的，一个是针对内存的，还有一部分在 Docker 这个区域里**。后者就是我们平时看得比较多的 `/var/lib/docker` 目录，它其实也属于文件系统的一部分；这些存储主要都是用来**让宿主机和容器共享数据**的。[【跳转到 00:13】](https://www.bilibili.com/video/BV1w3xCe1ENY/?t=13)

![Docker 存储的三种类型：分别面向宿主机目录、内存与 /var/lib/docker](assets/42-docker volume 存储卷的3种类型（volume, bind mount , tmpfs mount)/00013.webp)

在宿主机上执行 `df -h`，就能看到整个文件系统下有一个 `/var/lib/docker`——这一部分就属于 Docker 区域，**存储卷的数据也放在这里边**。[【跳转到 00:43】](https://www.bilibili.com/video/BV1w3xCe1ENY/?t=43)

![df -h 中可见 /var/lib/docker，存储卷的数据就在这个区域里](assets/42-docker volume 存储卷的3种类型（volume, bind mount , tmpfs mount)/00043.webp)

用一句话概括三者的分工：

| 类型 | 数据落在哪 | 对应命令 |
| --- | --- | --- |
| **bind mount** | 宿主机的某个目录 | `-v <宿主绝对路径>:<容器路径>` |
| **volume** | `/var/lib/docker/volumes` | `-v <卷名>:<容器路径>` |
| **tmpfs** | 宿主机的**内存** | `--mount type=tmpfs,...` |

![三种挂载方式：bind 挂宿主目录、volume 落 /var/lib/docker、tmpfs 进内存](assets/42-docker volume 存储卷的3种类型（volume, bind mount , tmpfs mount)/00063.webp)

## 二、用 docker inspect 分辨 bind 与 volume

`docker -v` 的通用形式是 `宿主机目录:容器内目录`——冒号前是挂载源，冒号后是容器内的目标路径。**如果冒号前是宿主机的根路径再加路径，这就是 bind 方式**。视频用一个容器（名叫 `ng4`）来演示。[【跳转到 01:03】](https://www.bilibili.com/video/BV1w3xCe1ENY/?t=103)

### 2.1 bind 方式：挂载源是宿主目录

启动容器后，执行 `docker inspect <容器名>`，在输出的 `Mounts` 段里看 `Type` 字段——**它的类型是 `bind`**，`Source` 就是我们指定的宿主机目录，目标（`Destination`）是容器内的目录。[【跳转到 02:06】](https://www.bilibili.com/video/BV1w3xCe1ENY/?t=126)

![docker inspect 中 Mounts 的 Type 为 bind，Source 指向宿主机目录](assets/42-docker volume 存储卷的3种类型（volume, bind mount , tmpfs mount)/00126.webp)

```bash
docker run ... -v /宿主目录:/容器内目录 --name ng4 <镜像>
docker inspect ng4          # Mounts.Type = bind
```

![bind 方式的 inspect 结果：Source 是宿主机目录、Destination 是容器目录](assets/42-docker volume 存储卷的3种类型（volume, bind mount , tmpfs mount)/00149.webp)

### 2.2 volume 方式：挂载源是卷名

接着跑第三种方式：**`-v` 前面改成一个存储卷的名称**（例如 `ng3` 用的卷）。同样用 `docker inspect` 看 `Mounts`，这次 **`Type` 变成了 `volume`**——也就是说它以**存储卷**的形式来绑定。[【跳转到 03:04】](https://www.bilibili.com/video/BV1w3xCe1ENY/?t=184)

关键是看 `Source`：它**指向 `/var/lib/docker/volumes` 下面的一个路径**。由此可以总结出一条判据——**只要挂载源落在这个路径下，它就是 volume 类型**。[【跳转到 03:04】](https://www.bilibili.com/video/BV1w3xCe1ENY/?t=184)

![volume 方式：Mounts.Type = volume，Source 落在 /var/lib/docker/volumes 下](assets/42-docker volume 存储卷的3种类型（volume, bind mount , tmpfs mount)/00184.webp)

```bash
docker run ... -v 卷名:/容器内目录 --name ng3 <镜像>
docker inspect ng3          # Mounts.Type = volume，Source 在 /var/lib/docker/volumes 下
```

### 2.3 小结：`-v` 的两种写法

把上面两种方式合起来总结，就是一条很好记的规律：[【跳转到 03:29】](https://www.bilibili.com/video/BV1w3xCe1ENY/?t=209)

- **`-v` 后跟以 `/` 开头的绝对路径 → bind 方式**；
- **`-v` 后跟其它写法（卷名，包括匿名卷或具名卷）→ volume 方式**。

![小结：-v 以 / 开头是 bind，其余（匿名/具名卷）是 volume](assets/42-docker volume 存储卷的3种类型（volume, bind mount , tmpfs mount)/00209.webp)

## 三、把数据放到内存：必须用 `--mount type=tmpfs`

前两种方式把数据落在磁盘上，那**第三种、也就是放进内存**该怎么做？这里必须换一个关键词——**`--mount`**。[【跳转到 03:56】](https://www.bilibili.com/video/BV1w3xCe1ENY/?t=236)

老师特别强调：**`-v` 其实就是 `--volume`，但 `--mount` 和 `-v` 是有区别的**（区别留到下一节课讲）。而**要挂载到内存，就必须用 `--mount` 这种写法**，并且后面**必须指定 `type=tmpfs`**。[【跳转到 04:06】](https://www.bilibili.com/video/BV1w3xCe1ENY/?t=246)

```bash
docker run -itd --name ng5 \
  --mount type=tmpfs,destination=/app \
  <镜像>
```

![挂到内存必须用 --mount 并指定 type=tmpfs](assets/42-docker volume 存储卷的3种类型（volume, bind mount , tmpfs mount)/00246.webp)

容器（`ng5`）起来后，照样用 `docker inspect` 看 `Mounts`：这次 **`Type` 是 `tmpfs`**。它的含义就是——**把容器里 `/app` 的数据，直接加载到宿主机的内存中**。[【跳转到 04:56】](https://www.bilibili.com/video/BV1w3xCe1ENY/?t=296)

![docker inspect 中 Mounts.Type = tmpfs，数据落在宿主机内存而非磁盘](assets/42-docker volume 存储卷的3种类型（volume, bind mount , tmpfs mount)/00296.webp)

## 小结

- Docker 存储有**三种类型，对应三个落点**：**bind**（宿主机目录）、**volume**（`/var/lib/docker/volumes`）、**tmpfs**（宿主机内存）。
- 用 **`docker inspect <容器>` 看 `Mounts.Type`** 即可分辨：`bind` / `volume` / `tmpfs`。
- `-v` 的两条规律：**以 `/` 开头 = bind**；**其余（匿名卷/具名卷）= volume**（看 `Source` 是否落在 `/var/lib/docker/volumes` 下）。
- **要挂到内存，必须用 `--mount type=tmpfs`**；`-v` 与 `--mount` 有区别。

![总结：三种挂载方式分别对应宿主机目录、/var/lib/docker 与内存](assets/42-docker volume 存储卷的3种类型（volume, bind mount , tmpfs mount)/00319.webp)

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| bind mount | 把宿主机的某个目录直接挂进容器，双向共享 |
| volume | 由 Docker 管理的存储卷，数据落在 `/var/lib/docker/volumes` |
| tmpfs mount | 把数据放进宿主机内存的挂载，容器停止/重启后数据消失 |
| `-v` / `--volume` | 挂载参数的简写与全写，形式为 `源:目标` |
| `--mount` | 另一种挂载写法，挂 tmpfs 时必须用它并指定 `type=tmpfs` |
| `docker inspect` | 查看容器详情，`Mounts` 段可见挂载的 `Type`、`Source`、`Destination` |
| `/var/lib/docker` | Docker 的数据目录，存储卷数据所在区域 |
