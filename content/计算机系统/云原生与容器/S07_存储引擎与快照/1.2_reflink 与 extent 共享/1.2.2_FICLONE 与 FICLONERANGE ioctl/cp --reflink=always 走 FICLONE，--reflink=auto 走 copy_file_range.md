# `cp --reflink=always` 走 FICLONE，`--reflink=auto` 走 copy_file_range

> 视频来源：[ZFS Finally Has CoW Reflink Support on Linux!](https://www.youtube.com/watch?v=kzXxCcKj0OU)（YouTube · Tony Tascioglu）｜时长约 7.5 分钟
>
> 导读：这是一条关于 OpenZFS 2.2.0 支持块克隆的更新视频，但真正有价值的是中间那两分钟：讲者把 `cp --reflink=always` 与 `--reflink=auto` 拆成两个完全不同的内核入口——前者是 `FICLONE` ioctl，后者是 `copy_file_range` 系统调用，于是同一个「跨数据集克隆」请求，一个必然失败、一个可能成功。字幕为 YouTube 自动字幕，术语已按上下文订正（Btrfs、OpenZFS、vdev、`duperemove`、`rmlint`）。

## 本讲要解决的核心问题（SCQA）

**背景**：reflink（块克隆）早就不是新东西，XFS 和 Btrfs 用户敲一句 `cp --reflink=always` 就能拿到一份「不占空间、改了才复制」的副本。ZFS 用户看着眼馋——OpenZFS 从 1.0 之前就没这个能力。

**冲突**：ZFS 2.2.0 终于加了块克隆，可很多人一试就发现「跨数据集克隆会失败」，而换成 `--reflink=auto` 又好像能成。同一个文件系统、同一条命令，只是换了个参数，行为为什么不一样？

**疑问**：`cp --reflink=always` 和 `--reflink=auto` 到底各自调用了什么？为什么一个对「源和目标必须同一个文件系统」这么敏感，另一个却无所谓？

**回答（中心思想）**：因为它们是**两个不同的内核接口**。`--reflink=always` 直接下发 `FICLONE` ioctl，语义是「必须真的克隆，做不到就报错」，而内核要求源和目标**共享同一个 superblock**；`--reflink=auto` 走的是 copy_file_range(2)，语义是「把这段数据弄过去就行，怎么弄我不管」，于是它可以在克隆失败时退化成普通复制，也就顺带绕过了跨数据集的限制。

## 一、先把 reflink 放回它该在的位置

讲者用一句话概括了 reflink：

> reflink 让你能用上写时复制：复制文件或目录时不必真的多占磁盘空间，因为它可以先指向原来的块；等你改动的时候才复制，然后完成你的写请求。

它最有价值的场景是**离线去重**。[【跳转到 00:38】](https://www.youtube.com/watch?v=kzXxCcKj0OU&t=38)

ZFS 早就支持在线去重，但代价很高：

- 在线去重非常吃内存，讲者的建议是「除非能省下两到三倍空间，否则别开」；
- 它会给所有写和删除操作拖后腿，因为每次都要去查一张巨大的去重表；
- 好处是「写下去的那一刻就知道是不是重复」，不用定期跑脚本。

[【跳转到 01:01】](https://www.youtube.com/watch?v=kzXxCcKj0OU&t=61)

reflink 走的是另一条路：用 `duperemove`、`rmlint` 这类工具**事后**扫一遍文件系统，找出完全相同的文件或 extent，再把它们重新链接到一起。

> 这比硬链接好得多，因为如果你改了其中一个文件，不会连带改掉所有副本——它会在那一刻复制一份，然后改你想改的地方。

讲者自己也用这个：同一条视频项目会存好几份拷贝，用 reflink 就不占空间，直到他真的动了某个片段，那个文件才被复制出来。

[【跳转到 01:48】](https://www.youtube.com/watch?v=kzXxCcKj0OU&t=108)

顺带一个 Btrfs 的坑：单盘 Btrfs 支持 reflink，但如果上了 **RAID5/RAID6，写时复制并不被保证**，所以那种配置下不能总指望 reflink 可用。

## 二、ZFS 2.2.0 补上了「块表」

[【跳转到 02:13】](https://www.youtube.com/watch?v=kzXxCcKj0OU&t=133)

reflink 在 ZFS 上迟迟没有，是因为缺一张能记录「哪些块被共享」的结构。2.2.0 引入了 **block table**，块克隆才成为可能。

[【跳转到 06:11】](https://www.youtube.com/watch?v=kzXxCcKj0OU&t=371)

讲者还解释了为什么这件事拖了这么久、并且先在 BSD 上能用：

- 初始实现是跟着上游 OpenZFS 走的，但**没有适配 Linux 侧的系统调用**，所以 BSD 上能跑、Linux 上不行；
- 最后合并的那个 PR 补的正是 Linux 这一半；
- 实现本身不轻——它需要一整张新表来缓存克隆结果，而 ZFS 里**目录的存储方式又相当独特**，要把这套功能塞进去并不直观。

## 三、关键的两分钟：`always` 与 `auto` 是两条代码路径

[【跳转到 02:27】](https://www.youtube.com/watch?v=kzXxCcKj0OU&t=147)

这是本文真正要记住的部分。讲者把 `cp` 的两个参数一路追到了内核入口：

| `cp` 参数 | 内核入口 | 语义 | 跨数据集 |
| --- | --- | --- | --- |
| `--reflink=always` | `FICLONE` ioctl | 必须真的克隆，做不到就失败 | 失败 |
| `--reflink=auto` | copy_file_range(2) | 只要数据到位，怎么复制不管 | 可能成功 |

[【跳转到 03:09】](https://www.youtube.com/watch?v=kzXxCcKj0OU&t=189)

具体到讲者的原话：

> 如果你做 `cp --reflink=always`，那会产生一个叫 `FICLONE` 的 ioctl 操作。在 Linux 内核里，这个操作要求你的源和目标拥有**同一个 superblock**。这意味着当你跨数据集做 `cp --reflink=always` 时它会失败。

[【跳转到 03:40】](https://www.youtube.com/watch?v=kzXxCcKj0OU&t=220)

而换一个参数：

> 但如果你做 `cp --reflink=auto`，你拿到的是 `copy_file_range` 系统调用。这种情况下 Linux 并不关心克隆有没有成功、是怎么成功的，只要文件到了就行。

于是出现了一个看起来矛盾、其实完全自洽的现象：

> `--reflink=auto` 和 `--reflink=always` 实际上走的是不同的代码路径，这意味着你用 auto 的时候有时可以跨数据集 reflink，而用 always 就不行。

[【跳转到 02:52】](https://www.youtube.com/watch?v=kzXxCcKj0OU&t=172)

为什么 Btrfs 用户从来没遇到这个限制？因为**Btrfs 的所有子卷共享同一个 superblock**，所以「跨子卷克隆」在 Btrfs 眼里仍然是「同一个文件系统内部」，`FICLONE` 的约束自然满足。ZFS 的 dataset 不是这个结构，限制才显形。

[【跳转到 03:55】](https://www.youtube.com/watch?v=kzXxCcKj0OU&t=235)

讲者也说明了这个「auto 能跨数据集」的结论来源：它来自实现这批 PR 的作者 Rob，讨论和 PR 链接都放在视频描述里——换句话说，这是**实现细节层面的行为**，不是接口承诺。

## 四、其他边界：加密数据集与「同一数据集内」

[【跳转到 05:05】](https://www.youtube.com/watch?v=kzXxCcKj0OU&t=305)

除了 superblock 这条，讲者还点了一个限制：**加密数据集之间不能互相 reflink**。

理由是密钥与数据集内的文件绑在一起：

> 如果你把文件 reflink 到一个用不同密码的数据集，这个块该怎么存？如果你改了其中一个数据集的密钥又怎么办？

结论是：加密数据集**内部**可以 reflink，**跨**加密数据集不行。

[【跳转到 03:00】](https://www.youtube.com/watch?v=kzXxCcKj0OU&t=180)

而在同一个 dataset 内部，讲者的说法很干脆：装上 2.2.0 之后，「reflink 就是能用了」，不用操心这些。

## 五、这条更新对工程实践意味着什么

把上面几条拼起来，可以得到几条能直接用的判断：

- **`--reflink=always` 是「断言」**：它在告诉你「这次必须零拷贝」，所以任何不满足前提的情况（跨文件系统、跨数据集、文件系统不支持）都会变成硬失败。适合你知道自己在同一个文件系统里、并且**需要**确认克隆真的发生了的场合。
- **`--reflink=auto` 是「尽力而为」**：它允许静默退化成普通复制。代价是**成功不等于克隆成功**——你以为省了空间，可能只是拷了一遍。
- **「跨数据集能不能克隆」不是一个稳定契约**：它取决于 `copy_file_range` 在特定文件系统上的实现，ZFS 这里是靠 PR 作者确认的行为。
- **上线前先验证**：ZFS 2.2.0 在讲者录制时还是 release candidate；想试可以从 git 构建后 `modprobe` 加载。

## 小结

- **reflink = 写时复制的副本**：先共享块，改动时才复制；适合离线去重，比硬链接安全。
- **在线去重是另一回事**：吃内存、拖慢写删，除非收益两到三倍否则不建议开。
- **ZFS 2.2.0 靠 block table 补上块克隆**，Linux 侧的适配 PR 比 BSD 晚，因为要补系统调用适配层。
- **`--reflink=always` → `FICLONE` ioctl**：要求源与目标同一 superblock，跨数据集直接失败。
- **`--reflink=auto` → copy_file_range(2)**：不关心怎么复制，可能退化成普通复制，因此有时能跨数据集。
- **Btrfs 子卷共享 superblock**，所以跨子卷克隆天然可行；ZFS 的 dataset 不是这个结构。
- **加密数据集之间不能 reflink**，数据集内部可以。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| reflink（块克隆） | 两个文件共享同一批块，写入时才复制；`FICLONE` 是创建它的接口 |
| `FICLONE` | ioctl，语义是「必须真的克隆」，要求源与目标同一 superblock |
| copy_file_range(2) | 系统调用，语义是「把数据搬过去」，允许退化成普通复制 |
| superblock | 一个文件系统的元数据根；同一个 superblock 才算「同一个文件系统」 |
| dataset | ZFS 的管理单位，可独立设属性、配额、加密；跨 dataset 克隆受限制 |
| subvolume | Btrfs 的子卷，所有子卷共享同一 superblock，所以可跨子卷克隆 |
| block table | ZFS 2.2.0 为块克隆引入的结构，用来缓存克隆结果 |
| `duperemove` / `rmlint` | 事后去重工具，扫描相同 extent 并重新链接 |
| 在线去重 / 离线去重 | 前者写入时即查重（吃内存），后者事后扫描（用 reflink 实现） |
| vdev | ZFS 的虚拟设备，池由 vdev 组成；「扩容 vdev」是另一条独立议题 |