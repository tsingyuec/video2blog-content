# JuiceFS 客户端：一次 read 与 write 如何翻译成元数据操作和对象读写

> 视频来源：[JuiceFS 常见性能问题排查&调优方法 - OfficeHours0912](https://www.bilibili.com/video/BV12DtNeHEAL/)（Bilibili · JuiceFS 官方，讲者执剑，负责社区版开发）｜时长约 70 分钟
> 导读：这是一场「把 JuiceFS 客户端这个黑盒拆开」的分享。讲者先用两张流程图讲清一次 write / read 在内核 FUSE 与用户态客户端之间怎么被切分、攒批、上传，再逐层演示 `juicefs stats` / `profile` / `bench` / `objbench` 各自的指标含义，最后把挂载参数（`--buffer-size`、`--max-uploads`、`--attr-cache`、`--open-cache`、`--prefetch`、`--writeback`）一个个对应回客户端的某个具体环节。本篇只讲客户端这一侧：内核 VFS → `/dev/fuse` 的通用机制留给 4.3.1，元数据引擎与对象存储的组合留给 4.2.1。字幕里的 `奔起/奔驰`→bench、`states`→stats、`原数据`→元数据、`分20/flash`→flush、`巴布赛/阿布赛`→buffer-size、`respect/REBACK`→writeback、`图放/度放`→读放大 等已订正。

## 本讲要解决的核心问题（SCQA）

**背景**：JuiceFS 挂载好之后，`cp`、`cat`、`ls` 这些命令照常能用，和本地盘没区别。既然没区别，用户自然认为「它就是一个盘」，性能不好时也只能说一句「JuiceFS 慢」[【跳转到 01:30】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=90)。

**冲突**：但在 `read()` 和真正的数据之间，隔着内核的 128K 切分、用户态客户端的内存缓冲区、4 兆的 block 上传、一次元数据引擎查询、若干级缓存。任何一环卡住，用户看到的都只是「慢」；而每一环对应的调优参数完全不同，猜错方向就白调 [【跳转到 04:16】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=256)。

**疑问**：一次 `read()` / `write()` 到底被翻译成了哪些元数据操作和哪些对象存储请求？这些环节各自能用什么指标看见？看见之后又该动哪个挂载参数？

**回答（中心思想）**：JuiceFS 客户端是一台**两级翻译机**——第一级把内核交下来的 128K FUSE 请求攒成 4 兆的 block，第二级把 block 变成对象存储的 PUT/GET，中间所有「文件在哪、这块属于哪个 slice」的问题都去问元数据引擎。因此客户端的性能永远由**两个外部组件（元数据引擎、对象存储）的延迟 × 客户端自身的并发度**决定；调优的本质，是先用 `stats` 判断瓶颈落在哪一级，再去动那一级对应的参数，而不是把 `--buffer-size` 一律调大。

## 一、客户端是一台两级翻译机

讲者一上来就把「黑盒」拆成四个竖列：Application、Kernel FUSE、JuiceFS Client、Object Storage。这四列之间的两条虚线，就是两次翻译的边界。

![一次 1 MiB 顺序写的完整翻译：应用发出 1 MiB，内核 FUSE 切成 8 个 128K，客户端攒成 4 兆 block 并打上 slice 归属，压缩加密后成为对象存储里的 4 兆 object](assets/JuiceFS%20客户端：一次%20read%20与%20write%20如何翻译成元数据操作和对象读写/00115.webp)

### 1.1 第一级翻译：内核把大 IO 切成 128K

正常用户发起一个写入请求，从应用程序发出之后先经过内核，然后被拆分成一个个 128K 的请求；这时 FUSE 还在内核态，它再把这些请求转发到用户态 [【跳转到 01:55】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=115)。

这个 128K 不是 JuiceFS 定的，是 FUSE 层请求的默认最大值。讲者在后面用 `profile` 的数字把这笔账算得很清楚：一次 1 MiB 的应用 IO，会被拆成 8 个 FUSE 请求 [【跳转到 22:47】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=1367)。

所以站在客户端门口看到的，**永远不是应用以为的那个大 IO，而是一串 128K 的小请求**。这一点决定了后面所有缓冲区设计：客户端必须自己把它们重新攒回去。

### 1.2 第二级翻译：客户端把 128K 攒成 4 兆 block

用户态这边是 JuiceFS 文件系统，相当于一个内部库在监听请求。请求经过 JuiceFS 的处理——写入、读取——按正常逻辑处理完之后再返回给 FUSE，FUSE 再返回给用户态的应用程序 [【跳转到 02:20】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=140)。

在客户端内部，这串 128K 请求会被重新组织：

- **攒批**：多个 128K 落进同一段连续区间，就合并成一个 4 兆的 block；
- **归属**：每个 block 属于某一次写入产生的 slice，slice 又属于某个 64 兆的 chunk；
- **加工**：block 在离开客户端之前做压缩和加密，然后才变成对象存储里的一个 4 兆 object。

读方向是同一套结构的镜像（上图下半部分）：客户端按 readahead window 从对象存储取 4 兆 object，解密、解压，再拆回 128K 交给内核 FUSE。图右下角那个 Background Jobs 框很关键——碎片合并、回收站过期删除这些后台任务，**都发生在客户端进程里**，而不是在某个服务端 [【跳转到 03:33】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=213)。

### 1.3 客户端内部的分层：两把缓存、两个外部组件

把视角再抬高一层，官方架构图把客户端内部画成了这样：应用通过 POSIX / SMB/CIFS / NFS 进来，落到 FUSE 这一层；FUSE 下面才是 JuiceFS 本体，本体两侧各挂一把本地缓存——Local Metadata Cache 和 Local Data Cache；再往下通过 TLS 连元数据引擎、通过 HTTPS 连对象存储。

![官方架构图：FUSE / Java SDK / CSI Driver / S3 Gateway 四种接入方式之下是同一个 JuiceFS 本体，本体两侧分别是本地元数据缓存与本地数据缓存，再往下才是元数据引擎与对象存储](assets/JuiceFS%20客户端：一次%20read%20与%20write%20如何翻译成元数据操作和对象读写/00183.webp)

这张图解释了为什么「客户端」这个词在 JuiceFS 里格外重要：**所有文件读写、碎片合并、回收站过期删除等后台任务，均在客户端中发生；客户端需要同时与对象存储和元数据引擎打交道** [【跳转到 03:03】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=183)。

按这张图自上而下读，客户端内部可以看成六段流水线（后文所有 `stats` 指标都能对回其中某一段）：

| 段 | 职责 | 对外表现 |
| :--- | :--- | :--- |
| FUSE 层 | 接 128K 请求，填 `struct stat`、返回目录项 | `stats` 的 fuse 段 |
| VFS 适配层 | 把 POSIX 语义（权限、时间戳、文件锁）落成 JuiceFS 的操作 | `profile` 里的 lookup / getattr / open |
| chunk / slice 管理层 | 64 兆 chunk、4 兆 block 的切分与归属 | 读放大、碎片合并 |
| 元数据客户端 | 查 inode、查 chunk/slice 列表、提交写入 | `stats` 的 meta 段 |
| 对象存储客户端 | 4 兆 block 的 PUT / GET | `stats` 的 object 段 |
| 本地缓存 | 元数据缓存 + 数据缓存（内存 + 磁盘） | `stats` 的 blockcache 段 |

这六段里，只有中间四段是 JuiceFS 自己能控制的；两头——内核 FUSE 的行为、元数据引擎与对象存储的延迟——都只能适应。这也解释了讲者反复强调的那句话：**元数据引擎与对象存储这两部分是外部组件，通信都是 TCP，请求一般都需要耗时，所以是两个重要的环节** [【跳转到 03:03】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=183)。
## 二、用 `juicefs stats` 把六段流水线摆在同一屏上

知道了有哪六段，接下来的问题就是：怎么知道这一次慢在哪一段？讲者的答案是 `juicefs stats`——一个实时统计工具，显示 JuiceFS 当前正在跑的性能状态，也就是耗时发生在哪个环节 [【跳转到 14:26】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=866)。

用法很朴素：在一个终端上跑负载（比如 `juicefs bench`），另一个终端跑 `juicefs stats /mnt/jfs -l 1`，就能看到一秒一行的实时数据 [【跳转到 14:56】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=896)。

![juicefs stats 的列定义：usage（cpu/mem/buf/cache）、fuse（ops/lat/read/write）、meta（ops/lat/txn/retry）、blockcache（read/write）、object（get/put/del 及各自延迟）——正好对应客户端的六段流水线](assets/JuiceFS%20客户端：一次%20read%20与%20write%20如何翻译成元数据操作和对象读写/01228.webp)

### 2.1 五组指标，各管一段

| 组 | 指标 | 含义 |
| :--- | :--- | :--- |
| usage | cpu / mem / buf / cache | 进程 CPU、物理内存、**已用的读写缓冲区大小**、内部指标 |
| fuse | ops / lat / read / write | 通过 FUSE 接口处理的每秒请求数与平均时延（毫秒）、读写带宽 |
| meta | ops / lat / txn / retry | 元数据请求数与平均时延；只读请求如 `getattr` 只计 ops 不计 txn |
| blockcache | read / write | 客户端本地数据缓存的每秒读写流量 |
| object | get / put / del 及各自延迟 | 对象存储的每秒请求数与每个操作的延迟 |

这里有两个容易被忽略的细节。

第一，`buf` 是**整个调优里最重要的一个数**。它代表进程已用的读写缓冲区大小，如果这个值逼近甚至超过客户端设置的 `--buffer-size`，说明读写缓冲区空间不足，需要视情况扩大，或者降低应用读写负载 [【跳转到 58:28】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=3508)。

第二，`meta` 的 ops/lat 里**不包含在缓存中直接处理的元数据请求**，这样统计出来的才是「客户端与元数据引擎真实交互」的耗时 [【跳转到 58:28】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=3508)。换句话说，`meta` 那一列低，可能只是缓存命中率高，不代表元数据引擎快。

### 2.2 瓶颈判定：ops × lat 就是这一段的耗时

讲者给了一个非常好用的判据：**每秒操作数乘以每个操作的耗时，就是这一段占用的总时间**。把各段加起来，应该接近或小于 FUSE 段的总耗时；哪个最耗时，瓶颈大概率就在它身上 [【跳转到 31:36】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=1896)。

他在本地演示里把这个判据走了一遍：把 Redis 放在本机，`meta` 延迟是 0.83 毫秒；如果元数据引擎部署在远端、走公网（比如在阿里云买一台 Redis，本地去连），延迟能达到 50 毫秒，那 bench 就跑不动了，性能会特别差 [【跳转到 29:56】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=1796)。

反过来也一样：如果 `meta` 处理得很快（本地 Redis），而你拿一个走公网的 JuiceFS，上传一个 4 兆要花 100 毫秒，那大部分时间都耗费在上传对象存储上，性能自然也有问题，这时候要想办法提高对象存储的性能 [【跳转到 32:26】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=1946)。

这也是为什么讲者说：**如果对象存储本身就比较慢、有问题，那去调 JuiceFS 这边的参数，除非调缓存，其他基本没什么效果**——因为对象存储的带宽以及它的延迟，决定了 JuiceFS 这边的性能表现 [【跳转到 13:39】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=819)。

## 三、`profile` 与 `accesslog`：数清每一个 POSIX 操作

`stats` 告诉你哪一段慢，`profile` 告诉你**哪一类系统调用慢**。它读取的是挂载点下的一个虚拟文件 `.accesslog`：这个文件是持续增长的，只有你打开它的时候才会产生日志，关闭之后就不再产生了；`profile` 实时读取它，就能分析出各个操作的次数、平均延迟、总耗时和耗时占比 [【跳转到 24:06】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=1446)。

![juicefs profile 的输出：flush 808 次、平均 19315 微秒、耗时占比 88.8%；read 与 write 各 33168 次；下面还有 lookup、create、getattr、unlink、open、release、readdir、statfs、mkdir、rmdir、opendir、releasedir](assets/JuiceFS%20客户端：一次%20read%20与%20write%20如何翻译成元数据操作和对象读写/01367.webp)

这张图信息量极大，值得逐行读。

### 3.1 一次 bench 到底打了多少个系统调用

讲者带着大家把 bench 的流程对上号：这次测试一共创建了 `(1 + 100) * 4 = 404` 个文件，每个文件都经历了「创建 → 写入 → 关闭 → 打开 → 读取 → 关闭 → 删除」的过程，因此一共有：

- **404 次** `create`、`open` 和 `unlink`；
- **808 次** `flush`——每当文件关闭时会自动调用一次 flush；
- **33168 次** `write` / `read`——每个大文件写入了 1024 个 1 MiB IO，而 FUSE 层请求的默认最大值为 128 KiB，也就是说每个应用 IO 会被拆分成 8 个 FUSE 请求，因此一共有 `(1024 * 8 + 100) * 4 = 33168` 个请求 [【跳转到 22:47】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=1367)。

这段算术把第一节讲的两级翻译彻底钉死了：**应用眼里的 1 MiB，在客户端眼里是 8 个 128 KiB**。所以当你看到 `write` 的次数远大于应用自己以为的写次数时，那不是 bug，是翻译的必然结果。

### 3.2 flush 占 88.8% 是正常的

最慢的一项是 `flush`，耗时占比 88.8%。讲者特意强调这**符合预期**：因为我们是先写入读写缓冲区，最终调用 flush，flush 才是真正写入对象存储的阶段，所以这 88% 的时间其实耗在对象存储那边 [【跳转到 22:47】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=1367)。

其他前面这些则是与内部流程以及元数据引擎的交互。元数据引擎交互其实就是过去查一下，没有大量的数据传输；而 flush 可能要传输几百兆数据 [【跳转到 23:12】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=1392)。

这条经验很实用：**看到 flush 占比高，不该去优化客户端，而该去看对象存储的带宽和延迟**；反过来，如果 `lookup` / `getattr` 占比高，才轮到元数据缓存和 `--attr-cache` 出场。

### 3.3 accesslog 还能看出读写模式

`.accesslog` 每行是一个系统调用的参数和耗时，量非常大。讲者说它最大的用处之一是**判断应用程序到底是顺序读还是随机读** [【跳转到 33:34】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=2014)。

`read` 请求后面有三个参数：`inode`（哪个文件）、`size`（其实就 128K，内核那边 128K 的一个读请求）、`offset`（从哪开始读）。如果第一个请求的 offset 在很靠前的位置，第二个请求直接跳到很远的地方，那就是跳跃式读 [【跳转到 45:19】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=2719)。

这个判断直接决定了 `--prefetch` 该开还是该关，下面第四节会讲。另外，你也可以把 accesslog 在短时间内 `cat` 到一个文件里，跑完负载之后把这段日志再喂给 `profile` 做回放——线上你只能跑一次、观察一次，结果就消失了，而离线回放可以反复分析 [【跳转到 24:47】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=1487)。

## 四、`bench` 与 `objbench`：先把外部组件的上限测出来

在调客户端参数之前，得先知道外部组件的天花板在哪里。讲者给了两个工具，一个从挂载点测、一个绕过挂载点测。

`juicefs bench` 跑在挂载点上，把整个环节都走一遍，相当于模拟你的应用程序直接读的时候能达到什么样的性能 [【跳转到 05:53】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=353)。

![juicefs bench 的结果表：Write big file 600.85 MiB/s、Read big file 729.80 MiB/s、Write small file 40.97 ms/file、Read small file 2.24 ms/file、Stat file 0.33 ms/file，以及 FUSE operation、Update meta、Put object、Get object、Write into cache、Read from cache 各自的 ops 与单次耗时](assets/JuiceFS%20客户端：一次%20read%20与%20write%20如何翻译成元数据操作和对象读写/00413.webp)

这张表最值得看的是最后几行：`Put object` 99.05 毫秒、`Get object` 56.00 毫秒、`Update meta` 1.46 毫秒、`Read from cache` 0.05 毫秒。它们正好是客户端六段流水线里「外部组件」和「本地缓存」两端的实测值——**对象存储的一次 PUT 是 99 毫秒，本地缓存的一次读是 0.05 毫秒，差 2000 倍**，这就是为什么客户端要拼命做缓存和攒批。

`juicefs objbench` 则绕过挂载点，直接指定一个对象存储去测它的纯处理性能 [【跳转到 10:17】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=617)。假如对象存储的吞吐只能达到 200 兆，那 JuiceFS 的上限也就在这里，无法突破对象存储的限制 [【跳转到 10:42】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=642)。

它还会先跑功能性测试：`basic` 这一类是基本能力要求，不满足相当于某些功能会受限；`sync` 这一类是给 `juicefs sync` 同步工具用的，不满足相当于 sync 工具用不了。某些对象存储确实有这种情况——实现不太符合 S3 要求，导致 sync 用不了，但基本的 mount 是 OK 的，所以看到这些 fail 可以忽略 [【跳转到 12:07】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=727)。

## 五、挂载参数：每一个都对应客户端里的一小段行为

讲者把挂载参数分成三组讲：元数据缓存、数据缓存、读写缓冲区。这个分法本身就是结论——**参数不是按「调大调小」分的，而是按「它影响客户端六段流水线里的哪一段」分的**。

### 5.1 元数据缓存分两层：内核一层，客户端一层

**内核元数据缓存**由三个参数控制，默认值都是 1 秒，通过 FUSE 传给内核 [【跳转到 58:28】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=3508)：

- `--attr-cache=1`：文件属性（attribute，含文件名、大小、权限、修改时间）的缓存时间，提升 `getattr` 性能；
- `--entry-cache=1`：文件项（entry 和 direntry，用来区分文件和目录的类型）的缓存时间，提升 `lookup` 性能；
- `--dir-entry-cache=1`：目录类型文件的缓存时间，提升目录的 `lookup` 性能。

![官方文档里的三个内核元数据缓存参数：--attr-cache、--entry-cache、--dir-entry-cache，默认都是 1 秒](assets/JuiceFS%20客户端：一次%20read%20与%20write%20如何翻译成元数据操作和对象读写/03508.webp)

这里有两个坑，讲者专门点了出来。

第一，**`entry` 缓存不是一份完整列表**。它是随着文件访问逐渐建立起来的，因此不能被 `readdir` 调用或者 `ls` 命令使用，只对 `lookup` 调用有加速效果。`dir-entry` 的含义也不等同于「目录项」的概念，它并不用来描述「一个目录下包含哪些文件」，而是和 `entry` 一样都是文件，只不过对文件是否目录类型做了区分 [【跳转到 58:28】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=3508)。

第二，在真实场景中很少需要对 `--entry-cache` 和 `--dir-entry-cache` 进行区分设置。如果确实要精细化调优，在**目录极少变动、而文件频繁变动**的场景，可以令 `--dir-entry-cache` 大于 `--entry-cache` [【跳转到 58:28】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=3508)。

**客户端内存元数据缓存**则是另一回事。JuiceFS 客户端在 `open` 操作打开一个文件时，其文件属性会被自动缓存在客户端内存中；这里的属性缓存不仅包含内核元数据中的文件属性（大小、修改时间），还包含 JuiceFS 特有的属性，如文件和 chunk、slice 的对应关系 [【跳转到 60:58】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=3658)。

要利用这层缓存，需要设置 `--open-cache` 指定缓存的有效时长。在缓存有效期间执行的 `getattr` 和 `open` 操作会从内存缓存中立即返回 slice 信息，省去每次打开文件都重新访问元数据服务的开销。

![--open-cache 的代价：设置之后文件系统不再满足 close-to-open 一致性，别的客户端改了文件，本客户端只能等缓存自然过期](assets/JuiceFS%20客户端：一次%20read%20与%20write%20如何翻译成元数据操作和对象读写/03658.webp)

但它有代价，而且代价写得很直白：**使用 `--open-cache` 选项设置了缓存时间以后，文件系统就不再满足 close-to-open 一致性**。不过与内核元数据缓存类似，发起修改的客户端同样能享受到客户端内存元数据缓存主动失效，其他客户端就只能等待缓存自然过期。因此为了保证文件系统语义，`--open-cache` 默认关闭；如果文件很少发生修改，或者只读场景下（例如 AI 模型训练），则推荐根据情况设置 `--open-cache`，进一步提高读性能 [【跳转到 60:58】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=3658)。

这条取舍值得记住：**默认的 1 秒内核缓存 + 关闭的 open-cache，换来的是「关闭再打开就能看到最新数据」这个承诺**。一旦你为了读性能打开 open-cache，等于把「最新数据」换成了「最多旧 N 秒的数据」。

### 5.2 数据缓存：一次 read 会穿过六层

数据缓存比元数据缓存复杂得多，但讲者用一张图把它串成了一条线。

![数据缓存的分层：Kernel Space 里的 Page Cache 与 Local Disk，User Space 里 JuiceFS 的 Read Buffer、Chunk Cache、Block Cache Index，Remote 侧的元数据引擎与对象存储](assets/JuiceFS%20客户端：一次%20read%20与%20write%20如何翻译成元数据操作和对象读写/03783.webp)

一次 `read` 从头到尾会这样走 [【跳转到 62:33】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=3753)：

1. **内核 page cache**。你要读某个文件的某一段，这一段上一秒刚刚读过，page cache 里已经记住了，内核发现你在读就直接反馈——这是最快的一层。注意这一层**不是 JuiceFS 控制的**。
2. **客户端的 read buffer**。page cache 没命中，请求经 FUSE 转发给 JuiceFS，客户端先查自己的 read buffer，有就直接返回，不用去问对象存储。
3. **元数据缓存 → 元数据引擎**。read buffer 也没命中，就得去查这段数据在元数据引擎里到底存不存在、存在哪里。这一步先走元数据缓存，命中就不查了。
4. **算出位置后取数据**。拿到 chunk/slice 信息，算出数据在对象存储中的位置，再去拿。如果对象存储那边还有内存缓存，内存中有就直接返回。
5. **本地缓存盘**。内存也没有，就读缓存盘上磁盘的那个位置。读磁盘又是一个请求，又发生到操作系统，所以**又回到 page cache**——命中就直接返回，没命中才真正读盘。
6. **对象存储**。本地磁盘也没有，那是最差的情况，读对象存储，然后一步一步返回出去。

讲者的总结是：**中间有很多级缓存，有一些是我们控制的，有些不是我们控制的** [【跳转到 63:58】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=3838)。这句话是理解所有缓存参数的前提——`--cache-dir`、`--cache-size` 只管第 5 层，`--prefetch` 管第 4 层的取数粒度，而第 1 层的内核 page cache 你只能通过 `-o direct-io` 之类的方式绕开，不能「调大」。

### 5.3 预读与预取：两种完全不同的猜法

读路径上有两个容易混淆的机制，讲者把它们分得很清楚。

**预读（readahead）针对顺序读**。内核自己有 readahead，但比较小，只有一点；JuiceFS 也有自己的预读行为：根据读写模式判断你正在顺序读，就开一个**变动的预读窗口**，动态判断接下来要读多少——读个 4 兆、8 兆等等。当你读到前面这一块的时候，就把你后面、猜测你要读的那部分从对象存储中拉下来 [【跳转到 40:44】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=2444)。

**预取（prefetch）针对随机读**。它的假设是：你正在读这个文件的第一小段，而对象存储那边一个数据块可能是 4 兆，我们假设它是完整的；你现在正在读第一兆，那我猜测你会把接下来三兆读完，就把剩下三兆给读完 [【跳转到 41:59】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=2519)。

`--prefetch` 的取值有一个常见误解要澄清：**它的值不是「拿几个块」，而是「后台有几个线程去做这件事」**。默认值是 1，就是一个线程在后台异步去拿；等于 2 就是两个线程。因为你读的时候不可能只读一个文件，可能有成百上千个文件一起读，每一个都会有 prefetch 的行为，用几个线程去做由这个参数控制 [【跳转到 43:14】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=2594)。

什么时候该关掉它？如果你的应用就是大文件随机读——读了第一块，接下来直接去读第 100 块，第一块永远不会再读到——那 prefetch 拉下来的那块数据基本不会被用到，纯属读放大。这时把 `--prefetch=0`，就不会造成读放大，可以把带宽留给真正需要的请求 [【跳转到 44:29】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=2669)。

讲者也补了一句公道话：**如果你的带宽本来就是闲置的，prefetch 的提升也一般**，因为读放大时你的读带宽没有达到上限，多读那些并不会造成很大的性能影响 [【跳转到 46:34】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=2794)。

### 5.4 读写缓冲区：读和写抢同一块内存

`--buffer-size` 是讲者反复强调「非常重要」的那个参数。实际上它在进程当中就是一块内存，里面放的东西分两部分，读和写**都占用同一块**，两者还会互相影响，造成性能上的波动 [【跳转到 39:29】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=2369)。

写的一侧比较好理解：write 请求要写到一个地方，暂时放在内存里，这一块就占用了 buffer-size，它会向这个池子申请，分给它一块 [【跳转到 39:04】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=2344)。

读的一侧则容易被忽略：读的时候有一些附带行为（就是上面说的 readahead 和 prefetch），这些行为也会占用 buffer-size。也就是说读和写都会占用，两者还会互相影响 [【跳转到 39:29】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=2369)。

讲者还给了一个具体的观察方法：**buffer-size 给读的配额上限是一半**。所以如果你是大文件顺序读，发现 `buf` 已经接近 buffer-size 的一半，说明读的配额已经占满，这时候加并发其实没用，要加大 buffer-size，这样才能让它有内存分配给读 [【跳转到 53:34】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=3214)。

至于取值，他的建议是：正常可以按机器内存除以 4，不要超过这个上限；但生产上一般机器都比较大，默认的 300 比较小，可以直接先调成 1G 试试，同时把跑业务的程序的并发拉个 10、16，根据 CPU 核数来。**一般 buffer-size 调大之后会有比较明显的性能提升** [【跳转到 54:24】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=3264)。

但「越大越好」是错的。因为对象存储的带宽是有限的，buffer-size 调得再大，那边刷入比较慢的话，反而会造成超时错误 [【跳转到 48:29】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=2909)。

### 5.5 `--max-uploads`：和 buffer-size 绑定的另一个旋钮

缓冲区越大，越需要更大的并发来进行预读和并发上传，提高缓冲区大小本身就有增加并发的作用。不过并发不可能无限增长，因此 JuiceFS 客户端提供 `--max-uploads` 和 `--max-downloads` 参数来控制并发极限 [【跳转到 49:19】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=2959)。

![讲者的幻灯片：--max-uploads 默认 20，若 4M 的对象块 PUT 延迟是 50ms，一秒内最高可上传 1000/50*20=1600M，这已经是极高的吞吐](assets/JuiceFS%20客户端：一次%20read%20与%20write%20如何翻译成元数据操作和对象读写/02959.webp)

这张幻灯片把「为什么默认值够用」算了一遍：`--max-uploads` 默认 20，假设 4M 大小的对象存储块 PUT 延迟是 50ms，那么一秒内最高可上传 `1000/50*20 = 1600M`，这已经是极高的吞吐，也正因为如此，上传并发通常无需进一步提高。**真正需要更高上传并发度的情况只有大量并发小写，或者高频创建小文件** [【跳转到 49:19】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=2959)。

所以这两个参数是有关联的：调 buffer-size 的同时要把 max-uploads 调大，要不然大家都堵在写对象存储那一块 [【跳转到 49:44】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=2984)。

### 5.6 缓存盘放在哪

缓存目录的默认位置取决于操作系统：Linux 是 `/var/jfsCache`，macOS 是 `$HOME/.juicefs/cache`，Windows 是 `%USERPROFILE%\.juicefs\cache`。Linux 下默认路径要求管理员权限，普通用户需要有使用权用 `sudo` 才能设置成功；也可以用 `--cache-dir` 指定到当前系统可以访问的任意存储路径上 [【跳转到 65:58】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=3958)。

![--cache-dir 的用法与缓存目录默认位置，以及一条提示：缓存目录尽量使用独立的高性能盘，不要用系统盘，也不要和其它应用共用](assets/JuiceFS%20客户端：一次%20read%20与%20write%20如何翻译成元数据操作和对象读写/03958.webp)

文档里有一条提示值得抄下来：**建议缓存目录尽量使用独立的高性能盘，不要用系统盘，也不要和其它应用共用**。共用不仅会相互影响性能，还可能导致其它应用出错。

讲者在最后还专门讲了一种反例：有的用户拿网络盘当缓存盘，结果网络盘比对象存储还慢，那你再读缓存盘是没有意义的，反而会拖慢整体性能。所以缓存盘要找一个比较快的，否则就是拖慢 [【跳转到 68:43】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=4123)。排查时如果发现「虽然走了缓存，但数据更差了、跑得更慢了」，就看从缓存盘读取这个操作的耗时，如果它耗时很高，就证明缓存盘有问题 [【跳转到 69:08】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=4148)。

## 六、两个「快但不安全」的开关

### 6.1 `--writeback`：把 flush 变成异步

正常情况下，数据应该写到对象存储再返回；开启 writeback 之后，客户端先写到本地磁盘就返回，然后后台异步上传到对象存储。这可以大幅提高小文件随机写的性能——小文件写每个可能只有 4K，但你要发一次请求上传到对象存储，性能非常差；而写到本地就很快，写到本地立刻就返回 [【跳转到 66:38】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=3998)。

代价有两个，讲者讲得很直白：

- **数据可能丢**。应用程序以为数据已经写完、上传已经完成，其实这时数据还在后台慢慢传。如果这时候机器或者盘挂了，数据就真的丢了 [【跳转到 67:13】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=4033)。
- **别的挂载点可能读不到**。比如 A 机器开启 writeback 写入 100 兆数据，可能一秒就完成了，但事实上它带宽只有 1 兆，后面需要 10 分钟才能传完。这时 B 机器一看「已经完成了」，去读一下，结果报 EIO——这是正常的，因为数据还没有传完，要等那台机器传完之后才能读到 [【跳转到 67:38】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=4058)。

开启之后，待上传的数据放在 `/var/jfsCache/<UUID>/rawstaging/` 目录下，也可以通过 `cat .stats | grep staging` 查看上传进度，会看到 `juicefs_staging_block_bytes`（待上传的数据块大小）、`juicefs_staging_block_delay_seconds`、`juicefs_staging_blocks`（待上传的数据块数量）三个指标 [【跳转到 65:58】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=3958)。

### 6.2 内核回写模式：`-o writeback_cache`

这是另一个容易和 `--writeback` 混淆的开关。从 Linux 内核 3.15 开始，FUSE 支持内核回写（writeback-cache）模式，内核会把高频随机小 IO（例如 10–100 字节）的写请求合并起来，显著提升随机写入的性能。但其副作用是**会将顺序写变为随机写，严重降低顺序写的性能**，开启前请考虑使用场景是否匹配 [【跳转到 64:58】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=3898)。

![内核回写模式（-o writeback_cache）与客户端读缓存、--prefetch 的说明：前者是内核中的实现，后者发生在 JuiceFS 客户端，二者适用场景也不一样](assets/JuiceFS%20客户端：一次%20read%20与%20write%20如何翻译成元数据操作和对象读写/03908.webp)

讲者特意强调了这两个 writeback 的区别：**内核回写是内核中的实现，客户端写缓存则发生在 JuiceFS 客户端，二者适用场景也不一样** [【跳转到 64:58】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=3898)。

### 6.3 低带宽下的一组「反向操作」

如果对象存储网络真的不好，讲者给的不是「调大」，而是一串「调小」 [【跳转到 50:09】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=3009)：

- **降低上传并发**，比如 `--max-uploads=1`，避免上传超时；
- **降低读写缓冲区大小**，比如 `--buffer-size=64` 或更小。当带宽充裕时，增大读写缓冲区能提升并发性能；但在低带宽场景下使用过大的读写缓冲区，flush 的上传时间会很长，因此容易超时；
- **增大 `--get-timeout` 以及 `--put-timeout`**。默认 GET/PUT 请求超时时间为 60 秒，增大它可以改善读写超时的情况。

![官方文档「读写慢与读写失败」一节：低带宽下的三条建议，以及 writeback 导致其他节点读文件报 EIO 的日志样例，最后推荐加 --no-bgjob](assets/JuiceFS%20客户端：一次%20read%20与%20write%20如何翻译成元数据操作和对象读写/03114.webp)

此外，低带宽环境下需要慎用客户端写缓存。文档里解释了原因：每个 JuiceFS 客户端默认都启用后台任务，后台任务中会执行碎片合并（compaction）、异步删除等工作，而如果节点网络状况太差，则会降低系统整体性能；更糟的是如果该节点还启用了客户端写缓存，则容易出现碎片合并后上传缓慢，导致其他节点无法读取该文件的危险情况 [【跳转到 50:09】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=3009)。

为了避免这类问题，官方推荐在低带宽节点上禁用后台任务，也就是为挂载命令添加 `--no-bgjob` 参数 [【跳转到 51:54】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=3114)。

## 七、客户端再快，也要应用肯并发

最后一个案例讲者讲得很生动：一个解压包的命令，在 JuiceFS 上性能比较一般，为什么？**因为它是个单线程** [【跳转到 54:44】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=3284)。

他的判断方法就是前面说的 `ops × lat`：看 stats 每一行是一秒，FUSE 的 ops 是 477、latency 是 2 毫秒，乘一下接近 1000；第二秒是 600 和 1.44，算出来也差不多。**每一行算出来都差不多，就说明只有一个线程在做这件事**。如果是多个线程，ops 乘以延迟会大于一秒 [【跳转到 55:04】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=3304)。

![stats 实时输出：fuse 段的 ops 与 lat 相乘始终不超过 1 秒，说明应用只有一个线程在读；meta 段延迟 3 毫秒，是这一段里比较明显的瓶颈](assets/JuiceFS%20客户端：一次%20read%20与%20write%20如何翻译成元数据操作和对象读写/03329.webp)

这个案例的价值在于它划出了责任边界：**JuiceFS 的性能在那里，但应用程序并没有并发去读，没有用合适的方法同时利用好这个性能** [【跳转到 57:09】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=3429)。讲者自己的演示也是同一个道理：默认 `-p 1` 跑 bench 只有 700 兆，把并发度拉到 4 就跑出大概 4 个 G [【跳转到 56:44】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=3404)。

所以排查顺序应该是：先用 `objbench` 确认对象存储的天花板，再用 `stats` 确认瓶颈落在 fuse / meta / blockcache / object 哪一段，用 `profile` 确认是哪一类系统调用，最后才动参数。讲者的总结是：这些工具主要是帮助我们分析延迟在哪里，以及分析这些流程里的使用情况——内存的使用、buffer 的使用、缓存的使用；通过这些使用情况能判断它现在走的路径是不是合理的，是不是达到了上限 [【跳转到 34:31】](https://www.bilibili.com/video/BV12DtNeHEAL/?t=2071)。

## 小结

- **客户端是一台两级翻译机**：内核把应用 IO 切成 128K 的 FUSE 请求，客户端再把它们攒成 4 兆的 block、打上 slice 归属、压缩加密后 PUT 到对象存储。一次 1 MiB 的应用 IO 在客户端眼里是 8 个 128K 请求——`(1024 * 8 + 100) * 4 = 33168` 这个数字就是它的直接证据。
- **性能由两个外部组件决定**：元数据引擎与对象存储都是外部组件，通信都是 TCP，请求一般都需要耗时。对象存储的上限在哪里，JuiceFS 的上限就在哪里；对象存储本身有问题时，调客户端参数基本没效果。
- **`stats` 的五组指标就是六段流水线**：usage（cpu/mem/buf/cache）、fuse（ops/lat/read/write）、meta（ops/lat/txn/retry）、blockcache（read/write）、object（get/put/del）。瓶颈判据是 `ops × lat` 占了多少秒。
- **`profile` 数清每个 POSIX 操作**：flush 占 88.8% 是正常的，因为 flush 才是真正写对象存储的阶段；如果 `lookup` / `getattr` 占比高，才轮到元数据缓存出场。
- **元数据缓存分两层**：内核层由 `--attr-cache` / `--entry-cache` / `--dir-entry-cache` 控制，默认都是 1 秒；客户端内存层由 `--open-cache` 控制，默认关闭，因为打开就不满足 close-to-open 一致性。
- **一次 read 要穿过六层缓存**：内核 page cache → 客户端 read buffer → 元数据缓存/元数据引擎 → 对象存储内存缓存 → 本地缓存盘 → 对象存储。只有中间几层是 JuiceFS 能调的。
- **`--prefetch` 的值是后台线程数，不是块数**；大文件随机读时应设为 0 以避免读放大。
- **`--buffer-size` 是读写共用的**，读的配额上限是一半；调大它的同时要把 `--max-uploads` 调大，否则大家都堵在写对象存储那一块。
- **两个「快但不安全」的开关**：`--writeback` 把 flush 变成异步，盘挂了数据就丢、别的挂载点可能读到 EIO；`-o writeback_cache` 是内核回写模式，提升随机写但严重降低顺序写。
- **低带宽下要反向调**：降 `--max-uploads`、降 `--buffer-size`、增大 `--get-timeout` / `--put-timeout`、加 `--no-bgjob`、别开 writeback。
- **缓存盘要比对象存储快**，否则走缓存反而更慢；用网络盘当缓存盘是典型反例。

## 关键术语速查

| 术语 | 一句话解释 |
| :--- | :--- |
| FUSE | 用户态文件系统框架，内核把 VFS 请求经 `/dev/fuse` 转给用户态进程；单次请求默认最大 128 KiB |
| 128K 切分 | 内核 FUSE 把应用的大 IO 拆成 128 KiB 的请求，是客户端看到的最小读写单位 |
| block | 对象存储里的最小数据单元，默认 4 MiB；客户端攒够一个 block 才上传 |
| chunk | 文件的逻辑分区，固定 64 MiB，用来快速定位要访问的那部分数据 |
| slice | 一次连续写入产生的记录，携带数据和它在文件中的位置；写入是增量的，不改已有数据 |
| readahead | 顺序读预读：判断你在顺序读，就动态开一个窗口，提前把后面的数据从对象存储拉下来 |
| prefetch | 随机读预取：读到某个 block 的一小段，就把整个 4 MiB block 拉下来；参数值是后台线程数 |
| 读放大 | 实际从对象存储读取的数据量大于应用请求的量，prefetch 与 readahead 都会造成 |
| `--buffer-size` | 客户端进程内读写缓冲区的大小上限，默认 300 MiB，读和写共用 |
| `--max-uploads` | 对象存储上传并发上限，默认 20；与 buffer-size 需要联动调整 |
| `--attr-cache` / `--entry-cache` | 内核元数据缓存时间（属性 / 文件项），默认 1 秒，分别加速 `getattr` 与 `lookup` |
| `--open-cache` | 客户端内存元数据缓存的有效时长，默认关闭，打开后不再满足 close-to-open 一致性 |
| `--writeback` | 客户端写缓存：先写本地磁盘就返回，后台异步上传；盘挂则丢数据，其他挂载点可能读到 EIO |
| `-o writeback_cache` | 内核回写模式（Linux 3.15+），合并高频随机小 IO，提升随机写但严重降低顺序写 |
| `--no-bgjob` | 禁用客户端后台任务（碎片合并、异步删除等），低带宽节点推荐开启 |
| `juicefs stats` | 实时统计客户端各段指标，类似 `dstat` |
| `juicefs profile` | 基于 `.accesslog` 统计各系统调用的次数、延迟与耗时占比 |
| `juicefs bench` / `objbench` | 前者测挂载点整体性能，后者绕过挂载点直测对象存储 |
