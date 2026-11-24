# virtio 的通知不是免费的：kick、中断与 event idx 三个开关

> 视频来源：[虚拟化os virtio数据传输原理](https://www.bilibili.com/video/BV1wx3NzcEUh/)（B 站 · 机七西-）｜时长约 6 分钟
> 导读：这支视频逐字段拆开 Linux 的 `vring_virtqueue`，再顺着"驱动提交、设备处理、驱动回收"走一遍数据流。本文只抓其中与**通知**有关的那条线：`notify` 函数指针、`flags` 开关与 `event idx` 阈值；virtqueue 三环的字段细节请配合本节的 3.2.2 一起读。

## 本讲要解决的核心问题（SCQA）

**背景**：virtio 用一块共享内存（vring）让客户机驱动和宿主后端交换数据。共享内存的好处是双方都能直接读写，不需要谁替谁搬数据。

**冲突**：共享内存只解决了"数据放哪儿"，没解决"对方怎么知道有新数据"。驱动往环里放了一项，设备不会自动醒来；设备处理完，驱动也不会自动知道。于是双方必须互相"敲一下"——驱动敲设备叫 kick，设备敲驱动叫中断。而每一次敲打，都要跨过客户机与宿主之间那道边界。

**疑问**：这两次敲打具体是怎么实现的？既然贵，能不能少敲几次？少敲会不会误事？

**回答（中心思想）**：virtio 把"要不要敲"做成了两个可协商的开关——环里的 `flags` 位（粗暴地整体关掉）和 `event idx`（精确到"处理到第几项才敲"）。驱动的 `notify` 函数指针负责敲设备，设备更新 `used.idx` 后发中断敲驱动。理解这三个东西，就理解了 virtio 通知路径上的全部取舍。

## 一、virtqueue 只是接口，通知藏在 vring_virtqueue 里

先分清两个结构体，这是理解后面所有字段的前提。

驱动写代码时看到的是 `virtqueue`——可以把它理解成**对外的一个接口**：提交请求、取回结果，都通过它。但真正干活的结构体是 `vring_virtqueue`，`virtqueue` 机制的实现依赖于它，vring 的具体实现也被它藏在下面 [【跳转到 00:14】](https://www.bilibili.com/video/BV1wx3NzcEUh/?t=14)。

![vring_virtqueue 的完整字段，其中 event 表示是否开启 event 通知机制](assets/virtio%20的通知不是免费的：kick、中断与%20event%20idx%20三个开关/00014.webp)

![左边是实现体 vring_virtqueue，右边是对外接口 virtqueue，两者一一对应](assets/virtio%20的通知不是免费的：kick、中断与%20event%20idx%20三个开关/00119.webp)

一个 virtio 设备可以拥有一个或多个 virtqueue，每个 virtqueue 独立完成数据收发；队列数量的多少由设备需求决定，比如网卡通常有两个——一个收、一个发 [【跳转到 01:19】](https://www.bilibili.com/video/BV1wx3NzcEUh/?t=79)。这一点很关键：**通知是按队列算的**，不是按设备算的，所以后面所有的抑制开关也都是队列级的。

### 1.1 跟通知有关的五个成员

`vring_virtqueue` 字段不少，和通知直接相关的有五个：

| 成员 | 视频里的解释 | 在通知路径上的角色 |
| --- | --- | --- |
| `event` | 是否开启 event 通知机制 | 决定用不用 event idx 那套精确阈值 |
| `num_added` | 上一次通知 host 之前，guest 添加了多少个 buffer | 攒批计数器：每添加一个 +1，每 kick 一次被清空 |
| `avail_idx_shadow` | guest 视角的可用索引 | 驱动侧的影子索引，用来判断"设备消费到哪了" |
| `last_used_idx` | 驱动侧记录设备已用到的位置 | 决定要不要处理 used ring 里的新项 |
| `notify` | virtqueue 通知后端的具体实现，初始化队列时注册 | **就是 kick 本身** |

![num_added 是"上次通知之后攒了几个 buffer"，每 kick 一次 host 就把它清空](assets/virtio%20的通知不是免费的：kick、中断与%20event%20idx%20三个开关/00034.webp)

`num_added` 这个名字值得停一下。它记录的不是"环里一共有多少项"，而是"**自从上次通知之后又加了几项**"。换句话说，内核在结构体里天生就为"攒一批再通知"留了计数器——这正是后面所有批量化、抑制手段的落脚点。

## 二、kick：驱动写完 avail.idx 后按下门铃

### 2.1 一次发送的完整动作

先看驱动这一侧做了什么。前端驱动通过 `virtqueue_add` 把 buffer 添加到 `vring_desc` 中，并把多个 `vring_desc` 组合成描述符链；接着把本次可以使用的 buffer 在 `vring_desc` 中的索引更新到 `vring_avail` 的 `ring` 数组里，并同步更新 `idx` [【跳转到 03:52】](https://www.bilibili.com/video/BV1wx3NzcEUh/?t=232)。

![virtqueue_add 把 buffer 挂进描述符表，描述符链指向真正的数据 buffer](assets/virtio%20的通知不是免费的：kick、中断与%20event%20idx%20三个开关/00232.webp)

视频给的例子很具体：客户机填充 `desc[0]` 和 `desc[1]`，分别写入数据 A 和 B，把索引 0 和 1 依次放入 `vring_avail.ring` 数组，并把 `vring_avail.idx` 更新为 2 [【跳转到 04:12】](https://www.bilibili.com/video/BV1wx3NzcEUh/?t=252)。

![desc0 与 desc1 分别写入 A、B，索引 0 和 1 进 avail.ring，这是 kick 之前的最后一步](assets/virtio%20的通知不是免费的：kick、中断与%20event%20idx%20三个开关/00252.webp)

注意顺序：**先写 ring 数组，再写 idx**。`idx` 是那个"提交完成"的信号量，设备看到 `idx` 前进了，才知道 ring 数组里新增的项是有效的。写 `idx` 之后紧接着的那次通知，就是 kick。

### 2.2 notify 是一个注册进来的函数指针

kick 在代码里不是一个写死的动作，而是 `vring_virtqueue` 里的一个函数指针 `notify`，在初始化队列的时候注册。对于基于 PCI 总线的 virtio 队列，对应的实现是 `vp_notify` [【跳转到 01:14】](https://www.bilibili.com/video/BV1wx3NzcEUh/?t=74)。

![notify 成员被圈出来：它是初始化时注册的函数指针，PCI 队列上落到 vp_notify](assets/virtio%20的通知不是免费的：kick、中断与%20event%20idx%20三个开关/00074.webp)

这个设计的意义在于**传输层可替换**：同一套 virtqueue 逻辑，跑在 PCI 上就写 PCI 的通知寄存器，跑在 MMIO 上就写 MMIO 的 `QueueNotify`，换成别的传输方式只要换掉 `notify` 的实现。对驱动作者来说，"kick"永远是调用同一个函数指针。

### 2.3 影子索引：为什么驱动要自己记一份

`avail_idx_shadow` 表示 guest 视角的可用索引：每添加一次 buffer 加一，每删除一次 buffer 减一 [【跳转到 00:54】](https://www.bilibili.com/video/BV1wx3NzcEUh/?t=54)。设备侧则维护 `last_avail_idx`，前端驱动更新头指针 `idx`，后端设备更新尾指针，头尾指针"你追我赶" [【跳转到 03:23】](https://www.bilibili.com/video/BV1wx3NzcEUh/?t=203)。

![avail_idx_shadow 与 notify 两个字段：一个是影子索引，一个是通知实现](assets/virtio%20的通知不是免费的：kick、中断与%20event%20idx%20三个开关/00054.webp)

影子索引存在的理由很朴素：共享内存里的 `idx` 是双方共写的，读一次就是一次跨边界的内存访问，还可能被设备随时改动。驱动在本地留一份影子，绝大多数判断在本地完成，只在真正需要时才对共享内存做一次读或写。**少碰共享内存，和少发通知，是同一个优化思路的两个侧面。**

## 三、interrupt：设备写完 used.idx 再叫醒驱动

设备这一侧的动作是驱动侧的镜像。设备先从 `vring_avail` 的 `ring` 数组中取出索引，再从 desc table 中取出数据并处理；处理完成后更新 `vring_used` 的 `ring` 数组和 `idx`，并发送中断通知 guest [【跳转到 04:52】](https://www.bilibili.com/video/BV1wx3NzcEUh/?t=292)。

![设备从 vring_avail 取索引、读 desc 处理，这是"读请求"的一半](assets/virtio%20的通知不是免费的：kick、中断与%20event%20idx%20三个开关/00292.webp)

接着看例子：设备读取 vring_avail 的 ring 数组第 0 项和第 1 项，得到索引 0 和 1，处理 desc 表第 0 项的数据 A 和第 1 项的数据 B，把索引 0 和 1 放入 vring_used 的 ring 数组，更新 `vring_used.idx` 等于 2 [【跳转到 05:12】](https://www.bilibili.com/video/BV1wx3NzcEUh/?t=312)。

![设备把处理完的索引写回 vring_used.ring，并推进 used.idx](assets/virtio%20的通知不是免费的：kick、中断与%20event%20idx%20三个开关/00312.webp)

最后是 guest 回收资源：客户机发现 `vring_used.idx` 等于 2，就知道 `desc[0]` 和 `desc[1]` 已被处理，于是重新填充它们写入新数据 C 和 D，索引 0 和 1 再次放入 `vring_avail.ring`，`vring_avail.idx` 更新为 4 [【跳转到 05:32】](https://www.bilibili.com/video/BV1wx3NzcEUh/?t=332)。

![回收后重新提交：同一批 desc 被复用，avail.idx 从 2 推进到 4](assets/virtio%20的通知不是免费的：kick、中断与%20event%20idx%20三个开关/00332.webp)

把这一圈连起来看，一次请求生命周里恰好有**两次通知**：

```
驱动: 写 desc → 写 avail.ring → 写 avail.idx → [kick] ─┐
                                                        ↓
设备: 读 avail → 读 desc → 处理 → 写 used.ring → 写 used.idx → [中断] ─┐
                                                        ↑              │
驱动: 发现 used.idx 前进 → 回收 desc → 重新提交 ────────┴──────────────┘
```

图里的 `notify by int` 就是设备回敲驱动的那一次中断。两条路径方向相反、机制对称：一条从驱动到设备，一条从设备到驱动。

## 四、第一个开关：ring 里的 flags

视频明确说，guest 添加完 buffer 之后**是否通知 host 有两种机制**：一是判断 ring 中的 `flags`，二是 `event idx` [【跳转到 04:12】](https://www.bilibili.com/video/BV1wx3NzcEUh/?t=252)。

![vring_avail 与 vring_used 都自带 flags 字段，这是最原始的通知开关](assets/virtio%20的通知不是免费的：kick、中断与%20event%20idx%20三个开关/00152.webp)

回看结构体定义可以看到，`vring_avail` 和 `vring_used` 各自都带一个 `flags` 字段，后面才是 `idx` 和 `ring[]`。这个 `flags` 就是最早的抑制手段：规范里对应 `VIRTQ_AVAIL_F_NO_INTERRUPT` 这一位，一方把它置上，等于告诉对方"我暂时不想收通知，别敲我"。

它的优点是**实现极简**：一次位操作，不需要任何额外状态，也不需要双方协商。缺点是**粒度太粗**：它只表达"要"或"不要"，不表达"什么时候要"。一旦置上，对方就完全不知道你什么时候会重新打开——只能靠轮询或者别的机制兜底。所以它是一种"宁可漏、不可多"的开关，适合明确知道自己要连续处理一大批数据的场景。

## 五、第二个开关：event idx

`event idx` 是更聪明的做法。视频把它的核心原则压缩成了一句话：**如果 host 能够很快处理 virtqueue 上的数据，就通知；如果 host 处理得慢，就不通知** [【跳转到 04:32】](https://www.bilibili.com/video/BV1wx3NzcEUh/?t=272)。

![同一张图上标注的"或者 Event idx"：阈值取代了开关](assets/virtio%20的通知不是免费的：kick、中断与%20event%20idx%20三个开关/00272.webp)

这句话值得展开，因为它把"要不要通知"从**布尔判断**变成了**位置判断**：

- 开关式（`flags`）问的是"现在要不要通知"；
- 阈值式（`event idx`）问的是"**你处理到第几项的时候才需要通知我**"。

于是双方各自在环里留一个"到第几项叫我"的位置：驱动告诉设备"你处理到第 N 项时再中断我"，设备告诉驱动"你提交到第 M 项时再 kick 我"。只要对方的进度还没到那个位置，通知就省掉；一旦跨过，通知照发。

这就自然带出了取舍：如果设备处理得比驱动提交还快，环里长期是空的，那么"处理到第 N 项"这个条件几乎每次都会被满足，通知一次也省不掉；反过来，如果设备是瓶颈、环里一直堆着活，驱动就没必要每加一项都敲一次门——设备反正还在忙，等它处理到约定的位置再叫它就行。

这也解释了为什么 `event` 这个布尔成员要和 `event idx` 配套存在：`event` 表示"是否开启 event 通知机制"，它决定走不走这套阈值逻辑；不开的时候退回 `flags` 那套粗粒度开关。

## 六、取舍：什么时候该关通知

把视频里的两条原则放在一起，可以得到一张判断表。注意这里的"通知"既包括驱动的 kick，也包括设备的中断：

| 场景特征 | 该怎么做 | 省下了什么 | 赔上了什么 |
| --- | --- | --- | --- |
| 环里长期有积压（设备是瓶颈） | 关通知，用阈值或攒批 | 每次提交一次跨边界写 | 设备空闲时可能多等一会儿才被叫醒 |
| 环里长期是空的（驱动提交慢、设备快） | 保持通知 | 最低延迟 | 每次提交都要付一次通知成本 |
| 明确要连续处理一大批 | 置 `flags` 整体关掉 | 一批只付一次 | 重新打开前的通知全丢，需要自己兜底 |
| 负载忽快忽慢、无法预判 | `event idx` 阈值 | 忙时自动省、闲时自动开 | 多维护两个阈值位置，逻辑更复杂 |

一句话总结这张表：**通知越少，吞吐越高、延迟越大；通知越多，延迟越低、CPU 越忙。** 抑制的本质不是"消灭通知"，而是把通知从"每项一次"改成"按需一次"。

## 小结

- virtio 的数据面是共享内存，但**共享内存不会自己通知对方**；一次请求生命周期里恰好有两次跨边界通知：驱动的 kick 与设备的中断。
- `virtqueue` 是对外接口，`vring_virtqueue` 才是实现；通知相关的字段是 `event`、`num_added`、`avail_idx_shadow`、`last_used_idx` 和 `notify`。
- **kick 就是 `notify` 函数指针**，初始化队列时注册，PCI 队列上落到 `vp_notify`；传输层换了，换的是这个指针。
- 驱动侧先写 `avail.ring` 再写 `avail.idx`，`idx` 是"提交完成"的信号；设备侧先写 `used.ring` 再写 `used.idx`，然后发中断。
- 抑制通知有两个开关：`flags` 是布尔开关，简单但粗暴；`event idx` 是位置阈值，精确但要多维护两个位置。
- 判断规则只有一条：**看环里是积压还是空闲**。积压就少通知，空闲就保持通知。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| kick | 驱动通知设备"有新请求"的动作，实现上就是调用注册好的 `notify` 函数指针 |
| 中断 | 设备通知驱动"你的请求处理完了"的动作，靠推进 `used.idx` 加一次中断注入 |
| `notify` | `vring_virtqueue` 里的函数指针，初始化队列时注册；PCI 队列上是 `vp_notify` |
| `num_added` | 上次通知之后又添加了几个 buffer，每 kick 一次被清空，天然适合做攒批计数 |
| `avail_idx_shadow` | 驱动本地保存的影子索引，避免每次都去读共享内存里的 `idx` |
| `flags` 抑制 | 环结构里的一位开关，置上就表示"暂时别通知我"，粒度粗 |
| `event idx` | 用"处理到第几项"的位置阈值代替布尔开关，忙时自动省通知、闲时自动恢复 |
| 通知成本 | 每一次 kick 或中断都要跨过客户机与宿主的边界，本篇只讲机制，成本链条见同小节的另一篇 |