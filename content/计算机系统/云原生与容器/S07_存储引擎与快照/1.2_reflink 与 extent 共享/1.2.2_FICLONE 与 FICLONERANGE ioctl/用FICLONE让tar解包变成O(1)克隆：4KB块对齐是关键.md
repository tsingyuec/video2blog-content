# 用 FICLONE ioctl 让 tar 解包变成 O(1) 克隆：4KB 对齐是关键

> 视频来源：[Making a magic deduplicating tar using the FICLONE ioctl](https://www.youtube.com/watch?v=5Z0isb-BCck)（YouTube · All Systems Go! 2023 · Wicher Minnaard）｜时长约 24 分钟
>
> 导读：这是一支「先讲清接口、再讲清它为什么用不上」的实战分享。讲者想把 tar 里的文件直接变成文件系统里的 reflink，结果被 4 KB 块对齐挡住，于是回头去改 tar 格式。本文按这条线展开：`read`/`write` 为什么必然复制、`FICLONE` 这个 ioctl 在哪里出现、对齐为什么是硬门槛、以及怎么用 PAX 头把文件「推」到块边界上。字幕为 YouTube 自动字幕，术语已按上下文订正（Btrfs、XFS、PAX、`FICLONE`、`bees`、`duperemove`、`zipalign`）。

## 本讲要解决的核心问题（SCQA）

**背景**：tar 是最古老的归档格式之一，容器镜像层到今天还是 tar。打包一个文件最自然的写法是 `read()` 从源文件读、`write()` 写进归档，字节一个不差。

**冲突**：讲者跑的是 Btrfs，他很清楚同一份数据在文件系统里只需要存一次，其余的都该是 reflink。可只要走 `read`/`write` 这条路，文件系统就一定会为归档里的那份数据**新分配空间**——于是同一张 768 字节的猫图在磁盘上出现了两三份。

**疑问**：能不能让内核知道「归档里这段字节和原文件是同一份数据」，直接做一次 reflink 克隆？如果能，为什么大家不这么干？

**回答（中心思想）**：能，入口就是 `FICLONE` 这个 ioctl——Btrfs 和 XFS 都支持它，成功之后归档里的那段内容与原文件**共享同一批 extent**，写归档几乎是瞬时的。但它有一个硬门槛：**源数据在文件里的偏移必须落在文件系统块边界上（Linux 上通常 4 KB）**，而 tar 的文件内容紧跟在 512 字节对齐的头之后，天然不对齐。于是整场分享的后半段，变成了「怎么在不破坏 tar 兼容性的前提下，把文件挪到 4 KB 边界」。

## 一、朴素的 tar 打包：内核不知道字节从哪来

讲者的测试素材是一张 768 字节的猫图 `kitties.jpg`。打包流程本身很朴素：

1. 用 `stat()` / `statx()` 拿到文件名、权限、大小；
2. 写一个 tar 头（Unix V7 头固定 257 字节，然后补齐到 512 字节的记录边界）；
3. 用 `read()` 读出文件内容，再用 `write()` 原样写进 `archive.tar`；
4. 内容之后继续补零到 512 的倍数，再写下一个文件的头。

[【跳转到 04:33】](https://www.youtube.com/watch?v=5Z0isb-BCck&t=273)

![白板上的三层示意：最上面是 kitties.jpg 的两个 512 字节块，中间是 archive.tar 的头部、PADDING、文件内容、PADDING 和下一个头，最下面是解包目标目录里的 kitties.jpg；红色虚线标出 stat 与 read/write 的路径](assets/用FICLONE让tar解包变成O(1)克隆：4KB块对齐是关键/00200.webp)

关键在颜色。讲者在白板上把原文件里的字节画成**蓝色**，把归档里那份画成**红色**：

[【跳转到 05:17】](https://www.youtube.com/watch?v=5Z0isb-BCck&t=317)

![同一张示意图，kitties.jpg 的两个块被高亮成蓝色：这些字节是「原始数据」](assets/用FICLONE让tar解包变成O(1)克隆：4KB块对齐是关键/00317.webp)

为什么同样的字节会变成「新位置」？讲者的解释是整场分享的支点：

> 我们只是从某处读、再用另一个系统调用写到另一处，内核完全不知道这些字节是从哪来的。所以文件系统别无选择，只能给它找一块新空间。

这就是 `read`/`write` 的语义边界：**它搬运的是字节，不是「这段数据属于谁」这个事实**。文件系统看到的是「一次全新的写」，于是老老实实分配新块。想让两份数据共享，必须换一个**能表达「这段内容请指向那份数据」的系统调用**——也就是 ioctl。

## 二、`FICLONE` 的硬门槛：源偏移必须落在块边界上

讲者提到的正是这个接口：创建 reflink 用的是 ioctl，Btrfs 支持，**XFS 也支持同一个 ioctl**。

[【跳转到 19:25】](https://www.youtube.com/watch?v=5Z0isb-BCck&t=1165)

> 如果你跑 Btrfs，或者 XFS——XFS 也能做这件事，同一个 ioctl——你就可以。

但它不是「有就能用」。讲者的原话是：

> 那个系统调用能工作，前提是你的数据在文件系统块大小上对齐，而在 Linux 世界里大多数情况是 4 KB。

[【跳转到 08:54】](https://www.youtube.com/watch?v=5Z0isb-BCck&t=534)

写成式子就是（$B$ 为文件系统块大小，Linux 上通常 4096 字节）：

$$
\mathrm{offset}_{\text{src}} \bmod B = 0, \qquad B = 4096
$$

这条约束直接解释了「为什么现成的去重工具救不了他」。Btrfs 有 `bees` 这类用户态去重工具，做法是把数据按**比文件系统块更大的块**做哈希（因为不可能给每个块存一个哈希，数据库会爆），发现哈希相同就把它们 reflink 到一起。但 `bees` 对不上 tar 里的那份：

[【跳转到 08:18】](https://www.youtube.com/watch?v=5Z0isb-BCck&t=498)

> 它没法在 tar 里的文件和 tar 外的文件之间去重。为什么？因为对齐。

原因很具体：`kitties.jpg` 在文件系统里从偏移 0 开始，而它在 `archive.tar` 里从第 512 字节之后开始——**起始偏移差了 512 字节，块边界对不上**，两边能共享的 extent 边界就永远对不齐。去重工具再聪明，也只能处理「边界一致」的数据。

麻烦在于 tar 的步长是 512，而块是 4096：512 能整除 4096，所以 tar 里的偏移**总是** 512 的倍数，却**很少**是 4096 的倍数。

$$
\mathrm{record} = 512, \qquad B = 4096, \qquad 4096 \bmod 512 = 0
$$

这就是本讲的核心矛盾：**接口（`FICLONE`）要求块对齐，格式（tar）给的是 512 字节对齐**。

## 三、对齐之后能拿到什么：翻指针，而不是搬数据

一旦对齐成立，收益是数量级上的：

[【跳转到 09:12】](https://www.youtube.com/watch?v=5Z0isb-BCck&t=552)

> 那我就能把它们放到下一个块边界上，然后就能去重了。实际上我在写入的时候就在去重，所以写文件的存储速度基本上接近无限，因为从文件系统的角度看，这只是翻一个指针，或者几个指针。

注意这句话里的两个方向：

- **写归档**：不再是「复制 768 字节」，而是「建立一段映射」，代价与数据量无关；
- **解包**：只要数据已经在磁盘上的 tar 里、而且是对齐的，解包几乎瞬时完成——「打个响指，所有文件就出现在你的文件系统里」。

[【跳转到 09:37】](https://www.youtube.com/watch?v=5Z0isb-BCck&t=577)

![同一张白板图，这次高亮的是 archive.tar 里两个猫图块：讲者说只要这些块落在 4 KB 边界上，解包就只是把指针指过去](assets/用FICLONE让tar解包变成O(1)克隆：4KB块对齐是关键/00552.webp)

讲者顺手点了一句这跟容器有关：Docker 镜像层就是 tar，如果解包能变成「翻指针」，镜像拉取后的落地时间就不再由数据量决定。这句在后面的 Q&A 里又被观众捡了起来。

## 四、改造 tar：用 PAX 头把文件「推」到 4 KB 边界

既然差的是偏移，那就把 tar 里的文件往后推。问题是 tar 的老格式没有留白的地方。

讲者把三代 tar 头并排画了出来：

[【跳转到 11:03】](https://www.youtube.com/watch?v=5Z0isb-BCck&t=663)

![白板对比三代 tar 头：Unix V7 是固定 257 字节头加 PADDING；POSIX 1988（ustar）多了 version 和额外字段；POSIX 2001 的 PAX 用 type=x 的伪文件承载任意长度的 key=value，因此可以塞任意多填充](assets/用FICLONE让tar解包变成O(1)克隆：4KB块对齐是关键/00663.webp)

- **Unix V7**：257 字节定长头，之后补到 512 字节边界。定长意味着**没有可伸缩的填充空间**，文件该落在哪就落在哪。
- **POSIX 1988（ustar）**：加了 version 和几个额外字段，但长度同样是固定的，还是挤不出空间。
- **POSIX 2001（PAX）**：允许一个 `type = x` 的「扩展头」伪文件跟在后面，内容是任意长度的 `key=value` 对，而且**这个伪文件本身可以任意长**。

于是填充点找到了：在真正的文件头之前塞一个超长的 PAX 扩展头，把真实文件推到下一个 4 KB 边界。代价是格式上的丑陋——PAX 伪文件之后还得再写一遍 Unix V7 头和 ustar 头，这是 tar 格式本身的怪癖。

实际做出来是这样的：工具往 tar 里写一个 `comment` 之类的未知关键字，长度刚好把文件顶到边界上，GNU tar 读的时候会礼貌地忽略它：

[【跳转到 14:10】](https://www.youtube.com/watch?v=5Z0isb-BCck&t=850)

![终端里 GNU tar 输出 "tar: Ignoring unknown extended header keyword 'LOLOLOLOLOLOLOL'"，紧接着正常列出文件：PAX 扩展头里的未知关键字被忽略，正好可以拿来当填充](assets/用FICLONE让tar解包变成O(1)克隆：4KB块对齐是关键/00872.webp)

讲者说他最初用的就是这种「假 PAX 头」，后来才发现 PAX 里本来就有 `comment` 关键字——「你可以直接写一条很长的注释」，更名正言顺。另一个考虑过的方案是用**精度极高的 mtime**（小数点后很多位）来占位，赌大多数实现会丢弃多余精度。

## 五、代价与边界：填充不是免费的

这套做法不是没有成本，讲者在 Q&A 里被直接问到了：

[【跳转到 21:23】](https://www.youtube.com/watch?v=5Z0isb-BCck&t=1283)

- **小文件不划算**：为了对齐塞进去的填充可能比省下来的还多，所以工具遇到小文件会直接放弃去重；
- **压缩会毁掉对齐**：tar 一旦过 `gzip`/`bzip2`/`xz`，字节流全变了，reflink 无从谈起；
- **但文件系统级压缩不冲突**：Btrfs 的透明压缩发生在另一层，去重照样成立，「那你就不用压缩 tar 了，它已经是压缩的」。

作为对照，zip 天生更适合这件事：它**按条目单独压缩**，条目之间还能对齐，Android 生态里的 `zipalign` 就是干这个的。

[【跳转到 17:45】](https://www.youtube.com/watch?v=5Z0isb-BCck&t=1065)

![幻灯片 "How about ZIP? How about compression?"：ZIP 同样古老，同样可以被对齐操纵，事实上 zipalign 就存在](assets/用FICLONE让tar解包变成O(1)克隆：4KB块对齐是关键/01090.webp)

顺着这个思路，观众提了一个更实用的方案：**混合**——图片这类压不动的走对齐 + reflink，文本这类能压的照常压缩。讲者的回答是这其实就是 zip 的思路；对 tar 也能做，办法是自定义一个 PAX 头，声明「下一个文件是 gzip 或 XZ 压缩的」，因为已经对齐了，压缩块之间也能互相去重。

## 六、彩蛋与结论：一个「两天」而不是「零天」的技巧

讲者留了一个和安全无关、纯粹好玩的副产物：既然 PAX 扩展头能塞任意字节，那就能塞**终端控制码**。他用反斜杠加 b（退格符）把 GNU tar 的告警信息「擦」掉，再进一步用清屏控制码，最后发现终端还支持图片格式的控制码——于是 tar 变成了「世界上最差的视频播放器」。

[【跳转到 15:47】](https://www.youtube.com/watch?v=5Z0isb-BCck&t=947)

![终端里执行 clear | xxd，输出 1b5b 481b 5b32 4a：清屏不过是往标准输出写几个控制码，而控制码可以藏在 tar 的扩展头里](assets/用FICLONE让tar解包变成O(1)克隆：4KB块对齐是关键/01022.webp)

收尾时讲者给了三条「贡献」，也给了边界：

[【跳转到 20:18】](https://www.youtube.com/watch?v=5Z0isb-BCck&t=1218)

![幻灯片 "BUT... Align all the things already!"：希望主流 tar 实现和标准库都懂这些填充技巧，紧接着一行红字 "AND THIS MAY BE A TERRIBLE IDEA"，脚注指向 man 2 copy_file_range 与 Aleksa Sarai 2019 年那篇《The Road to OCIv2 Images》](assets/用FICLONE让tar解包变成O(1)克隆：4KB块对齐是关键/01241.webp)

- 工具已经放出来了（`de-duptar`），但**这只是个两天的技巧，不是零日漏洞**：他联系了 tar 的维护者，对方两天内就修了，所以「两年之后你在 Debian 上就做不了这件事了」；
- 真正有价值的是那句「为什么我们需要文件系统块对齐，以及怎么给 tar 做到」；
- 而这件事**不需要任何人同意**——你可以在自己的归档格式里先对齐、先 dedup。

[【跳转到 20:57】](https://www.youtube.com/watch?v=5Z0isb-BCck&t=1257)

![幻灯片 "Where to from here"：Contributions 三条——已经有 de-duptar、对块对齐的认知多了一点、以及这件事不需要征求任何人同意](assets/用FICLONE让tar解包变成O(1)克隆：4KB块对齐是关键/01190.webp)

顺带一提，那张幻灯片脚注里的 man 2 copy_file_range 不是随手写的：copy_file_range(2) 是另一条「让内核知道这段数据来自哪里」的路径，和 `FICLONE` 的关系见同小节的另一篇《cp --reflink=always 走 FICLONE，--reflink=auto 走 copy_file_range》。

## 小结

- **`read`/`write` 必然复制**：内核只看到「一次新的写」，不知道字节来自哪，文件系统只能分配新块。
- **reflink 要靠 ioctl 表达**：`FICLONE` 让目标文件的内容指向源文件的 extent，Btrfs 与 XFS 都实现了同一个 ioctl。
- **对齐是硬门槛**：源数据在文件里的偏移必须落在文件系统块边界（Linux 常见 4 KB）上，否则克隆无法建立。
- **对齐换来 O(1)**：写归档与解包都退化成「改指针」，代价与数据量无关；这正是容器镜像层想要的。
- **tar 的填充点是 PAX 扩展头**：`type = x` 的伪文件长度任意，可以拿 `comment` 或超长 mtime 把真实文件顶到 4 KB 边界；代价是格式更丑、小文件不划算。
- **压缩与对齐互斥，但分层不互斥**：tar 过 gzip 会毁掉对齐；文件系统级压缩（Btrfs）在另一层，不影响去重。
- **这是「两天」技巧**：GNU tar 已修，别指望长期可用；可迁移的是「块对齐」这个认知。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| `FICLONE` | 一个 ioctl：让目标文件的内容整体指向源文件的 extent，不复制数据 |
| reflink | 两个文件共享同一批 extent，写入时才分裂；`FICLONE` 是创建它的接口 |
| extent | 文件系统分配数据的基本单位，一段连续的块；reflink 共享的粒度就是它 |
| 块对齐 | 数据的文件内偏移是文件系统块大小的整数倍；不对齐就无法建立共享 |
| tar 记录 | tar 的最小单位是 512 字节，头部与内容都按 512 补齐 |
| ustar | POSIX 1988 的 tar 头格式，字段定长，没有可伸缩的填充空间 |
| PAX 扩展头 | POSIX 2001 引入的 `type = x` 伪文件，承载任意长度的 `key=value`，可用来填充 |
| `bees` | Btrfs 的用户态去重工具，按大于块大小的单位做哈希再 reflink |
| `duperemove` | 事后去重工具，扫描相同 extent 并重新链接（见 1.2.1） |
| `zipalign` | Android 工具，把 zip 条目对齐到边界，与本文的 tar 填充是同一类技巧 |
| copy_file_range(2) | 另一个「内核可自行决定怎么复制」的接口，可能退化为 reflink，见下一篇 |