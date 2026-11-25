# CephFS 的 caps：客户端缓存权的授予与归还

> 视频来源：[What are "caps"? (And Why Won't my Client Drop Them?) - Gregory Farnum, Red Hat](https://www.youtube.com/watch?v=VgNI5RQJGp0)（YouTube · Cephalocon）｜时长约 34 分钟
> 导读：这是 CephFS 前 tech lead 讲「为什么客户端缓存了元数据还能保持 POSIX 一致」的一手材料：caps 不是锁，而是 MDS 发给客户端的**可撤销缓存授权**。本文按「为什么需要锁 → cap 有哪些位 → 怎么撤销 → 代价与告警」重组；JuiceFS 的架构细节属于本系列 4.2，本文不涉及。

## 本讲要解决的核心问题（SCQA）

**背景**：CephFS 对外宣称自己是 POSIX 文件系统。POSIX 有一条底线：一个 `write` 返回之后，紧接着的 `read` 必须读到刚写的数据。单机上这条靠共享 page cache 免费获得。

**冲突**：CephFS 是多客户端共享同一棵树，客户端 A 写、客户端 B 读，中间隔着网络和一个元数据服务。如果每次 `stat` 都要问 MDS，性能无法接受；如果让客户端随便缓存，B 就会读到旧数据。

**疑问**：谁来决定一个客户端「可以缓存什么」？又由谁、在什么时候把它收回来？

**回答（中心思想）**：CephFS 用 **caps（inode capabilities，inode 能力）**把「缓存权」做成了一份**可撤销的授权**。MDS 是元数据的唯一权威，它按 inode 的每一类元数据发 cap（shared 或 exclusive）；客户端拿到 cap 就能本地应答系统调用，一旦别人要改，MDS 发 revoke，**客户端必须停用并确认（ack）之后授权才真正收回**。所以一致性边界既不在时间上，也不在 open/close 上，而在**MDS 的锁状态机 + 客户端的主动归还**这条链上。

## 一、为什么必须有锁：POSIX 的一致性要求一个单一权威

讲者的开场很直接：CephFS 是**一致的（coherent）**，因为文件系统必须一致，否则不配叫 POSIX 文件系统 [【跳转到 02:17】](https://www.youtube.com/watch?v=VgNI5RQJGp0&t=137)。

![CephFS is Coherent：一致性是 POSIX 文件系统的入场券](assets/CephFS%20的%20caps：客户端缓存权的授予与归还/00137.webp)

具体到规则：客户端 A 对文件 foo 的 `write` 完成之后，客户端 B 读 foo 必须读到同样的数据。分布式这个事实**不允许**你打破它 [【跳转到 02:42】](https://www.youtube.com/watch?v=VgNI5RQJGp0&t=162)。

要做到这一点，就必须有一个地方把所有操作**串行化或线性化**——也就是需要锁。在 CephFS 里，这个权威是 MDS：它持有元数据的锁，并在单个 MDS 内部和整个 MDS 集群之间维护分布式锁，锁描述的是「这份状态能以什么方式被访问或修改」 [【跳转到 03:07】](https://www.youtube.com/watch?v=VgNI5RQJGp0&t=187)。

![文件在不同客户端上看起来一样，就意味着需要一个单一权威来裁决访问和修改](assets/CephFS%20的%20caps：客户端缓存权的授予与归还/00187.webp)

但只有锁是不够的：如果每个 `stat` 都要去 MDS 排队拿锁，性能就回到「每次都走网络」。所以 MDS 把一部分权威**下放**出去——这就是 cap。

![MDS 对元数据是权威，分布式锁描述允许的状态，再把 capabilities 发给客户端以允许缓存](assets/CephFS%20的%20caps：客户端缓存权的授予与归还/00212.webp)

讲者举了个很具体的收益：一个客户端 `lookup` 并 `stat` 之后，可以把结果缓存下来，接下来同一个进程哪怕一秒内问一万次，也不用再发一次网络往返 [【跳转到 03:32】](https://www.youtube.com/watch?v=VgNI5RQJGp0&t=212)。

### 1.1 先澄清命名：这里的 caps 不是 keyring 的 caps

Ceph 里 `caps` 这个词被用了两次：创建客户端 keyring 时写的权限字符串也叫 caps。讲者自己吐槽「我们起名很糟糕」——本文讲的是 **CephFS 客户端与 MDS 协议里的 inode capabilities** [【跳转到 04:22】](https://www.youtube.com/watch?v=VgNI5RQJGp0&t=262)。

### 1.2 先看数据放哪：元数据与数据是两套对象

要理解 cap 只管什么，得先看 CephFS 的存储布局。目录和 dentry 与 inode 一起存在**目录 RADOS 对象**里，作为 omap 键值存储；文件数据则按 inode 号存成**另一系列 RADOS 对象** [【跳转到 01:42】](https://www.youtube.com/watch?v=VgNI5RQJGp0&t=102)。

![CephFS 元数据存储：目录对象里是 dentry 到 inode 的映射与文件大小](assets/CephFS%20的%20caps：客户端缓存权的授予与归还/00102.webp)

这个布局决定了 cap 的边界：**caps 管的是元数据缓存**，数据缓存在协议里另有 cache/buffer 两个位（见第三节）。同时它也解释了数据流：客户端把元数据请求发给 MDS，把数据请求直接发给 OSD [【跳转到 01:27】](https://www.youtube.com/watch?v=VgNI5RQJGp0&t=87)。

![CephFS 数据流：元数据走 MDS，数据直连 OSD](assets/CephFS%20的%20caps：客户端缓存权的授予与归还/00087.webp)

## 二、cap 的种类：五类元数据，六种权限位

一个客户端能拿到的 cap 有五类，每类对应 inode 上的一块状态 [【跳转到 04:47】](https://www.youtube.com/watch?v=VgNI5RQJGp0&t=287)：

| cap | 记法 | 覆盖的状态 |
| :--- | :--- | :--- |
| pin | `p` | inode 存在这件事本身 |
| auth | `A` | 认证相关元数据：mode、UID、GID |
| link | `L` | 链接计数（多少 dentry 指向这个 inode） |
| xattr | `X` | 扩展属性的存在与内容 |
| file | `F` | 文件数据、时间戳、文件大小 |

而每个 cap 上还可以带不同的**权限位** [【跳转到 05:37】](https://www.youtube.com/watch?v=VgNI5RQJGp0&t=337)：

- `s`（shared）：这份状态有很多客户端共享，你只是其中之一；
- `x`（exclusive）：只有你有这份状态，别人完全不知道它现在长什么样；
- `r`（read）/ `w`（write）：能读 / 能写这份状态；
- `c`（cache）/ `b`（buffer）：能缓存读 / 能缓冲写。

![CephFS cap 的权限位：shared、exclusive、read、write、cache、buffer](assets/CephFS%20的%20caps：客户端缓存权的授予与归还/00337.webp)

### 2.1 组合起来才有意义

并非每个 cap 都会用到所有位。讲者给了一张组合表 [【跳转到 07:42】](https://www.youtube.com/watch?v=VgNI5RQJGp0&t=462)：

![cap 组合：pin 是二值的；auth、link、xattr 只有 shared 或 exclusive；带 s 可本地缓存，带 x 可本地修改](assets/CephFS%20的%20caps：客户端缓存权的授予与归还/00462.webp)

- **pin** 是二值的：有或没有。它叫 pin 是因为——只要客户端记住了「这个 inode 存在」，MDS 就必须把这个 inode **钉在**自己的内存 inode 缓存里，不能扔 [【跳转到 06:52】](https://www.youtube.com/watch?v=VgNI5RQJGp0&t=412)；
- **auth / link / xattr** 只有 shared 或 exclusive 两种：`[ALX]s` 可以把状态存本地并引用（权限检查在客户端完成）；`[ALX]x` 表示「这份状态归我了」，可以**先在本地改，之后再告诉 MDS**。

`[ALX]x` 这一条是理解 cap 价值的关键：`chmod` 这类操作在客户端内存里改完就可以返回，不必等一次网络往返。

### 2.2 file cap：为什么数据和时间戳被绑在一起

file cap 比其他的都复杂，因为它同时覆盖**文件数据**和**mtime、size** [【跳转到 08:32】](https://www.youtube.com/watch?v=VgNI5RQJGp0&t=512)：

![file cap 的组合：Fs 缓存 mtime/size，Fx 本地改 mtime/size，Fr 同步读 OSD，Fc 缓存数据，Fw 同步写 OSD，Fb 缓冲写](assets/CephFS%20的%20caps：客户端缓存权的授予与归还/00512.webp)

绑在一起的理由很实在：**只要写，就必然要改 mtime**；而读写都需要知道文件大小（否则没法判断「这个偏移超出文件末尾了」）。所以它们被塞进同一个 cap，不能拆开授权。

### 2.3 最容易被误解的一对：read 不等于 cache

`Fr`（read）和 `Fc`（cache）是分开的，讲者专门强调这一点 [【跳转到 09:22】](https://www.youtube.com/watch?v=VgNI5RQJGp0&t=562)：

- `Fr`：允许你向 OSD 发请求**读**数据，但**不允许缓存**；
- `Fc`：允许你把读到的数据缓存在本地。

分开的原因是：可能有别的客户端正在写。只有当你确认没有别人写时，缓存才是安全的。同理 `Fw`（同步写 OSD）与 `Fb`（缓冲写、后台刷）也是两个位——缓冲写的前提是「没有别人在读或写」。

## 三、cap 怎么变：授予容易，收回要确认

cap 会变，通常是因为**别的客户端有动作**。MDS 通过给客户端发消息来授予或撤销 cap [【跳转到 12:55】](https://www.youtube.com/watch?v=VgNI5RQJGp0&t=775)。

![cap 如何变化：MDS 授予或撤销；撤销时客户端必须停用并回 MClientCaps 确认](assets/CephFS%20的%20caps：客户端缓存权的授予与归还/00806.webp)

撤销流程有两个要点：

1. **停用是客户端的责任**。MDS 不会假设「消息发出去了就等于生效」；
2. **必须回一条 `MClientCaps` 确认**。否则 MDS 无法知道客户端是否收到了撤销——如果客户端还在用旧状态本地应答读请求，一致性就破了。

「停用」的难度差别极大：

- 如果只是 `Fs`（缓存的 mtime/size）或者 shared 读，忘掉就行，下次用到再问 MDS；
- 如果是 `Fb`（缓冲写），客户端可能攒了**上百 MB 甚至上 GB 的脏数据**，必须先刷到 OSD 才能交还 [【跳转到 13:51】](https://www.youtube.com/watch?v=VgNI5RQJGp0&t=831)。

### 3.1 一次改 mode 的完整往返

讲者用「三个客户端共享一个文件、其中一个要 `chmod`」演示了整条链 [【跳转到 14:41】](https://www.youtube.com/watch?v=VgNI5RQJGp0&t=881)：

![示例：三个客户端共享同一文件的 auth cap，其中一个要改 mode](assets/CephFS%20的%20caps：客户端缓存权的授予与归还/00881.webp)

1. 三个客户端都持有 `As`（shared auth）和同一个 mode；
2. 客户端 1 想改 mode，**主动先丢掉自己的 shared cap**，把新 mode 发给 MDS；
3. MDS 发现还有别人持有 `As`，于是发出 **revoke all shared**；
4. 另外两个客户端在本地清掉 auth shared 位和它们记的 mode，回一条「已丢弃（顺便，等下能还给我吗）」；
5. MDS 在本地完成 mode 修改，再把新的 shared cap 连同新 mode 发回去；
6. 客户端收到后更新缓存，继续原来的工作。

代价很清楚：**每个客户端一次往返，加上最初客户端到 MDS 的一次**。如果涉及 `Fb`，还要额外加上刷脏数据到 OSD 的往返 [【跳转到 15:31】](https://www.youtube.com/watch?v=VgNI5RQJGp0&t=931)。

### 3.2 客户端刷数据时，MDS 并不知道它在忙

问答环节有人问：客户端正在刷脏数据、迟迟不还 cap，会不会先给 MDS 报个「我在忙，别踢我」？

答案是不会：**MDS 收不到任何「客户端正在干活」的更新**，它只是坐在那里等 cap 回来 [【跳转到 16:50】](https://www.youtube.com/watch?v=VgNI5RQJGp0&t=1010)。这个设计选择直接导致了第六节的两个健康告警。

## 四、代价：MDS 的缓存必须比所有客户端加起来还大

cap 架构有三个直接后果 [【跳转到 17:10】](https://www.youtube.com/watch?v=VgNI5RQJGp0&t=1030)：

![cap 架构的后果：MDS 必须记住客户端 pin 的一切；MDS 缓存要大于客户端缓存；caps 是协作式的](assets/CephFS%20的%20caps：客户端缓存权的授予与归还/01030.webp)

1. **MDS 必须记住客户端 pin 过的所有东西**。客户端 A pin 了一个 inode，客户端 B 把它 `unlink` 到链接计数为 0，MDS 可以把 inode 排队删除，但**不能真的删**——因为 POSIX 允许你继续读一个已 unlink 的文件，直到最后一个句柄关闭；
2. **MDS 的缓存必须大于客户端缓存的并集**。讲者给了一个很扎心的例子：客户端有 256 GB 内存、很乐意攒脏元数据，而 MDS 只配了 4 GB 缓存——这不会工作得好 [【跳转到 17:35】](https://www.youtube.com/watch?v=VgNI5RQJGp0&t=1055)；
3. **caps 是协作式的**。客户端必须主动确认，否则**别人的访问会被一直阻塞**，直到系统外部发生什么改变（超时、断连）。

第 3 条是理解所有 cap 故障的钥匙：一致性靠的是客户端「守规矩」。

## 五、客户端代码里，cap 长什么样

讲者贴了 `client/Client.cc` 里 `_write` 的一段（截掉了前半部分）[【跳转到 22:15】](https://www.youtube.com/watch?v=VgNI5RQJGp0&t=1335)：

![客户端写路径：get_caps 申请需要的 cap，拿 cap ref 标记正在使用，再决定走 objectcacher 还是直写 OSD](assets/CephFS%20的%20caps：客户端缓存权的授予与归还/01335.webp)

流程可以概括成四步：

1. **`get_caps`**：告诉它这次要操作哪个 inode，以及需要哪些 cap——要写所以必须 `Fw`；要做权限检查所以需要 `As`；能拿到 `Fb` 最好 [【跳转到 22:40】](https://www.youtube.com/watch?v=VgNI5RQJGp0&t=1360)。如果没有，就发消息向 MDS 申请并**睡眠等待**；
2. **拿 cap reference**：标记「这个 cap 正被某段代码使用」，此时不能丢；
3. **分岔**：有 `Fb` 且 objectcacher 开着，就写进本地缓冲（异步、非阻塞）；否则走 filer 直写 OSD，然后睡到写完；
4. **释放 ref**：写完之后把 buffer cap 的引用还掉。

这段代码也解释了为什么「撤销」有时会很慢：客户端里到处是「检查 cap → 没有就申请 → 睡眠等待」的循环，`Fb` 的引用可能被一段正在刷盘的代码长期持有。

## 六、两个健康告警：客户端不肯还 cap 时会发生什么

cap 系统目前最常见、也最容易让人困惑的两个告警，讲者各用一页讲清了。

### 6.1 failing to respond to capability release

MDS 发了 revoke，客户端却没把 cap 还回来 [【跳转到 18:25】](https://www.youtube.com/watch?v=VgNI5RQJGp0&t=1105)。

![告警一：客户端未能响应 cap 释放，默认 60 秒后触发](assets/CephFS%20的%20caps：客户端缓存权的授予与归还/01105.webp)

可能的原因包括：

- 网络或 OSD 太忙，客户端正在刷脏数据，实在腾不出手；
- MDS 一次撤销了**两百万个 inode 的 cap**，客户端在时间窗内根本刷不完；
- 软件 bug，客户端真的坏了；
- 恶意客户端（讲者说目前还没见过）；
- 其他原因导致变慢，比如连接短暂断开。

默认 60 秒后进健康告警系统。有一个**默认关闭**的选项 `mds_cap_revoke_eviction_timeout`，可以强制断开不响应的客户端——这是对付 bug 和恶意客户端的办法，但默认不开，因为客户端可能持有脏状态，踢掉就丢数据 [【跳转到 19:40】](https://www.youtube.com/watch?v=VgNI5RQJGp0&t=1180)。

### 6.2 failing to respond to cache pressure

MDS 的内存快满了，于是要求所有客户端交还一部分 pin cap（比如 10%），但客户端没交够 [【跳转到 20:30】](https://www.youtube.com/watch?v=VgNI5RQJGp0&t=1230)。

![告警二：客户端未能响应缓存压力，MDS 要求交还 pin cap 但客户端交不够](assets/CephFS%20的%20caps：客户端缓存权的授予与归还/01230.webp)

这个告警的关键在于：**它可能不是故障，而是配置问题**。如果应用打开了 100 万个文件，而 MDS 的内存目标只按 80 万算，客户端就是「交不出来」——没人能替你解决，只能改配置 [【跳转到 21:20】](https://www.youtube.com/watch?v=VgNI5RQJGp0&t=1280)。讲者提醒这个计数器是「奇怪的衰减计数器」，所以出现时间不好预测，但一旦看到就该去查。

## 七、跨协议：把 NFS delegation 架在 CephFS 之上

讲者最后介绍了一个较新的接口：CephFS 用户态库里的 delegation API，用来给 NFS-Ganesha 这类**再导出（re-export）**服务做缓存一致性 [【跳转到 25:30】](https://www.youtube.com/watch?v=VgNI5RQJGp0&t=1530)。

![再导出文件服务器的接口：CEPH_DELEGATION_RD/WR 与 cap 回调](assets/CephFS%20的%20caps：客户端缓存权的授予与归还/01530.webp)

思路是：NFS 本身有 delegation 概念（把本地读写的权限委派给客户端），但粒度比 cap 粗——基本是整个文件的读或写。要让 NFS 客户端和原生 CephFS 客户端共存且保持一致，需要做一次映射：

1. NFS 客户端打开文件 → Ganesha 向 CephFS 申请一个 delegation（`CEPH_DELEGATION_RD` 或 `WR`）；
2. CephFS 尝试拿到对应的 cap 集合：拿到就成立，拿不到就放弃；
3. 一旦 CephFS 收到会破坏 delegation 的 cap revoke，就通过注册的 **callback** 通知 Ganesha：「你得让 NFS 客户端交回 delegation」；
4. Ganesha 处理完再回话，CephFS 才真正丢掉 cap [【跳转到 27:10】](https://www.youtube.com/watch?v=VgNI5RQJGp0&t=1630)。

讲者希望这套接口以后能扩展到 Samba oplock 和其他文件系统——本质上它是「**用一层薄适配，把 cap 的撤销语义翻译成别的协议的撤销语义**」。

## 八、几个容易被追问的边界

问答部分补了几条重要的语义边界：

- **多客户端同时写同一个文件是支持的**，写本身很容易；但如果有人要读，就得来回交换 cap 以维持顺序 [【跳转到 28:42】](https://www.youtube.com/watch?v=VgNI5RQJGp0&t=1722)；
- **跨 RADOS 对象边界的写不是原子的**。POSIX 要求块级原子更新，而一个跨越对象边界的写可能被拆开——严格说违规，但极罕见，目前基本被忽略 [【跳转到 29:21】](https://www.youtube.com/watch?v=VgNI5RQJGp0&t=1761)；
- **客户端崩溃后，cap 要等 MDS 判定它死了才能收回**。TCP 会话断开有超时，但必须等——因为直接驱逐会丢脏状态 [【跳转到 30:26】](https://www.youtube.com/watch?v=VgNI5RQJGp0&t=1826)；
- **cap 不支持按范围授权**。`Fr`/`Fw` 作用于整个文件，不能只给某个字节区间（那是 fcntl 文件区间锁的领域）；这是多年前讨论过的扩展，但社区优先级不在那里 [【跳转到 31:11】](https://www.youtube.com/watch?v=VgNI5RQJGp0&t=1871)；
- **关掉 blacklist 会留下安全缺口**。客户端被 MDS 驱逐、丢了 cap，但它还有到 OSD 的直连数据通道，会拿着旧权限继续读写；OSD 不会逐请求回查 MDS [【跳转到 32:14】](https://www.youtube.com/watch?v=VgNI5RQJGp0&t=1934)；
- **空闲客户端会不会主动还 cap**？取决于版本：老客户端几乎不还，Mimic/Nautilus 之后开始更积极地裁剪 [【跳转到 33:32】](https://www.youtube.com/watch?v=VgNI5RQJGp0&t=2012)。

## 小结

- CephFS 的一致性来自「单一权威 + 分布式锁」：MDS 对元数据有最终裁决权，再通过 cap 把一部分权威下放给客户端。
- cap 不是锁，而是**可撤销的缓存授权**：五类 cap（pin/auth/link/xattr/file）覆盖不同元数据，六种权限位（s/x/r/w/c/b）决定能读、能写、能缓存还是能缓冲。
- `Fr` 与 `Fc`、`Fw` 与 `Fb` 必须分开：能读不等于能缓存，能写不等于能缓冲——后者都要求「确认没有别人」。
- 撤销是**协作式**的：MDS 发 revoke，客户端停用并回 `MClientCaps` 确认，授权才真正收回；`Fb` 的撤销要先把脏数据刷到 OSD，可能很慢。
- 代价是 MDS 内存：它必须记住客户端 pin 的一切，所以 MDS 缓存要大于客户端缓存之和；两个健康告警（cap 释放无响应、缓存压力无响应）都源于此。
- 缓存一致性的边界可以跨协议复用：NFS delegation / Samba oplock 都能通过一层 callback 适配，映射到 cap 的撤销语义上。

## 关键术语速查

| 术语 | 一句话解释 |
| :--- | :--- |
| caps（inode capabilities） | MDS 发给客户端的元数据缓存授权，可授予也可撤销 |
| pin cap | 只表示「这个 inode 存在」，客户端记住它，MDS 就必须把 inode 留在内存 |
| shared / exclusive | 前者是「很多客户端共享这份状态」，后者是「只有你有，可以本地改」 |
| cache / buffer 位 | 允许缓存读 / 允许缓冲写；两者都要求确认没有其他读写者 |
| revoke 与 ack | MDS 撤销 cap 后，客户端必须停用并回 MClientCaps 确认，否则授权不算收回 |
| MDS 缓存压力 | MDS 内存吃紧时要求客户端交还 pin cap；交不够就触发健康告警 |
| delegation | NFS 的粗粒度委派（整文件读或写），CephFS 通过 callback 与之对接 |
| blacklist | OSD map 里的黑名单，阻止被驱逐的客户端继续直连 OSD 读写 |