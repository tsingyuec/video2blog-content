# thin pool 的容量为什么对不上：一个池里藏着 data、metadata 和 spare 三个卷

> 视频来源：[PVE里最容易看懵的pve-data，到底是个啥？为什么PVE磁盘容量对不上？原来藏着一个特殊卷！thin pool 的构成](https://www.bilibili.com/video/BV1tjVb6wEMd/)（Bilibili · 领略技术的美）｜时长约 6 分钟
> 导读：这支视频从一个很小的困惑出发——装完 PVE 后，各个卷的容量加起来跟总容量对不上。顺着这个差额，它把 thin pool 的内部构成、容量水位的看法、以及"虚拟硬盘为什么天生就是精简的"讲了一遍。本文把口播里的类比换成可复核的命令输出。

## 本讲要解决的核心问题（SCQA）

**背景**：在 PVE（Proxmox VE）里装完系统，你会看到 `root`、`swap`、`data` 三个卷。按直觉，它们的容量加起来应该等于那块盘的总容量。

**冲突**：加起来对不上。少掉的那部分去哪了？更奇怪的是，在 `data` 上新建一块 100 GB 的虚拟硬盘，`data` 的占用率却纹丝不动。

**疑问**：`pve-data` 到底是个什么卷？它凭什么"报 100 GB 却几乎不占空间"？容量水位又该看哪个数字？

**回答（中心思想）**：`pve-data` 不是普通 LV，而是一个 **thin pool（精简池）类型的特殊 LV**——它对外是一个"池"，对内由 `data`（数据）、`tmeta`（元数据）两个隐藏卷加一个 `pmspare`（元数据备用卷）组成。容量对不上的差额就是这些隐藏卷；而池的"真实水位"要看 `%data` 和 `%meta` 两个百分比，不是看卷的 `LSize`。

## 一、`pve-data` 是 LV，但不是普通 LV

### 1.1 先分清：LV 有很多种

视频的结论给得很直接：`pve-data` 跟 `root`、`swap` 一样都是 LV（Logical Volume，逻辑卷），但它**不是普通 LV**。

![此 LV 非彼 LV：LV 是逻辑卷，但逻辑卷分很多类型](assets/thin%20pool容量对不上：data、metadata与spare三个卷/00023.webp)

[【跳转到 00:23】](https://www.bilibili.com/video/BV1tjVb6wEMd/?t=23)

普通 LV 的本质是 linear LV，`root` 和 `swap` 都属于这一类，它们是**厚置备（thick provisioning）**的：要多少给多少，划走了别人就用不了。除此之外还有条带 LV、raid 的 LV、thin LV，以及 **thin 精简池 LV**。

[【跳转到 00:15】](https://www.bilibili.com/video/BV1tjVb6wEMd/?t=15)

`pve-data` 就属于最后一种：它既是 LV，又带着 pool（存储池）的特性——这正是它让人看不懂的原因。

### 1.2 厚置备和精简制备，差在"什么时候真的给"

用视频里的比喻来理解：

- **厚置备**像自家修的水池，从村里的公共水池一次性划走满满一池水。你用不完，别人也用不了。
- **精简制备**像在中间加了一个"按需放水"的中间水池：你家水龙头一直有水，但那不是预先划给你的，是中间水池在你用的时候才放出来的。

这个"中间水池"就是 thin pool。它需要一本账本记录"谁用了多少水"——这本账本就是**元数据（metadata）**。厚置备不需要这么麻烦，一手交钱一手交货就结束了；精简制备必须有账本。

## 二、水位怎么看：`%data` 和 `%meta`

既然 `data` 是精简制备的，那"它实际用了多少"就不能看它报的容量，要看百分比。

![lsblk 里能看到 pve-data 下面挂着 tmeta 和 tdata 两个子卷](assets/thin%20pool容量对不上：data、metadata与spare三个卷/00071.webp)

[【跳转到 01:11】](https://www.bilibili.com/video/BV1tjVb6wEMd/?t=71)

命令行里看 `lvs` 输出的 `Data%` 这一列：

![lvs 输出：data 的 Data% 是 0.00，Meta% 是 1.13](assets/thin%20pool容量对不上：data、metadata与spare三个卷/00033.webp)

[【跳转到 00:51】](https://www.bilibili.com/video/BV1tjVb6wEMd/?t=51)

图形界面里则是"数据中心 → pve → LVM-Thin"这一页：

![PVE 的 LVM-Thin 面板：使用率 6%、元数据使用率 1%，两列并排](assets/thin%20pool容量对不上：data、metadata与spare三个卷/00239.webp)

[【跳转到 03:59】](https://www.bilibili.com/video/BV1tjVb6wEMd/?t=239)

这里有两个数字，注意它们量纲完全不同：

- **使用率 / `Data%`**：池里真正被写过的数据占池容量的比例。这是"还剩多少能写"的主指标。
- **元数据使用率 / `Meta%`**：那本"账本"占了多少。账本很小（示例里只有 1.4 GB 左右），但它一旦写满，池同样会出问题——这也是为什么下面会有一个专门的备用卷。

视频里那张图上，池的 `LSize` 是 140.87 GB，而 `Data%` 只有 0.00、`Meta%` 是 1.13。**一个卷"有多大"和"用了多少"是两件事**，这就是精简配置的全部要点。

## 三、容量对不上的差额：三个带方括号的隐藏卷

回到开头那个困惑。把 `lvs` 加上 `-a`（显示所有卷，包括内部卷），答案就出来了：

![lvs -a 显示出三个带方括号的隐藏卷：data_tdata、data_tmeta、lvol0_pmspare](assets/thin%20pool容量对不上：data、metadata与spare三个卷/00133.webp)

[【跳转到 02:13】](https://www.bilibili.com/video/BV1tjVb6wEMd/?t=133)

- **不带方括号的 LV 是用户可见的**：`data`、`root`、`swap`，你可以直接管理和使用。
- **带方括号的 LV 是内部隐藏的**：[data_tdata]、[data_tmeta]、[lvol0_pmspare]，属于精简池内部管理用，你一般不能直接操作它们。

它们的分工，视频用"面子"和"里子"来概括：

> `data` 是我们平时看到的、操作的那个精简池，它对外提供存储能力；而 `data_tdata` 是底层真正存放数据的地方，属于精简池的内部实现。所以你可以认为 `data` 是面子，`tdata` 是里子。

`tmeta` 则是那本账本。而 `pmspare` 是 `pve-data_tmeta` 的**备用空间**：当池的元数据出问题时，就会启用这个备用卷顶上。

![lsblk 的树状结构：pve-data_tmeta 与 pve-data_tdata 下面都挂着 pve-data](assets/thin%20pool容量对不上：data、metadata与spare三个卷/00157.webp)

[【跳转到 02:37】](https://www.bilibili.com/video/BV1tjVb6wEMd/?t=157)

把 `pmspare` 这份备用空间的容量也加回去，账就对上了。**所以"容量对不上"不是丢了空间，而是有一部分空间被留作元数据的保险。**

## 四、虚拟硬盘本身也是精简卷

### 4.1 新建 100 GB，不代表占掉 100 GB

视频做了一个很直观的对照实验：在 `data` 上新建一块 100 GB 的虚拟硬盘。

![新建虚拟机后，LVM-Thin 面板里 data 的使用率仍然是 0%](assets/thin%20pool容量对不上：data、metadata与spare三个卷/00200.webp)

[【跳转到 03:20】](https://www.bilibili.com/video/BV1tjVb6wEMd/?t=200)

装操作系统之前，`data` 还是 0% 的占用；装完系统之后，也只占了几个 G。

![装完系统后，使用率只涨到 6%，已用 8.59 GB——而不是 100 GB](assets/thin%20pool容量对不上：data、metadata与spare三个卷/00205.webp)

[【跳转到 03:25】](https://www.bilibili.com/video/BV1tjVb6wEMd/?t=205)

结论：**虚拟硬盘本身也是精简制备的**，只有真正写入数据时才占用池的空间。

### 4.2 PVE 不让你选厚/薄，因为底层存储已经决定了

这里有个和 ESXi 的对比：ESXi 在新建虚拟机时，可以手动选择虚拟硬盘是厚置备还是精简制备；PVE 没有这个选项。

原因是：**虚拟硬盘的模式由底层存储的类型决定**。

- 在 `data` 这个精简池上新建硬盘 → 虚拟硬盘就是精简制备的；
- 在 LVM 这种厚置备存储上新建硬盘 → 虚拟硬盘就是厚置备的。

[【跳转到 03:54】](https://www.bilibili.com/video/BV1tjVb6wEMd/?t=234)

### 4.3 从 `lsblk` 里能直接看到那块"虚拟硬盘"

用 `lsblk` 或 `pvs` 再看一眼，会发现在 `data` 上新建虚拟机之后，多出来一个 `vm-100-disk-0`：

![lsblk 与 lvs：vm-100-disk-0 的 LSize 是 100G，但 Data% 只有 8.01](assets/thin%20pool容量对不上：data、metadata与spare三个卷/00259.webp)

[【跳转到 04:19】](https://www.bilibili.com/video/BV1tjVb6wEMd/?t=259)

这一张图把整篇的要点全串起来了：`vm-100-disk-0` 的 `LSize` 是 100.00g（逻辑容量，报给虚拟机看的），`Data%` 是 8.01（它实际在池里占的比例），而池 `data` 自己的 `Data%` 是 5.68——**逻辑容量和物理占用是两个独立的数字，池的水位是它们共同的结果**。

视频作者自己也承认这套结构看着乱："本来好不容易搞清楚一点了，现在又迷糊了。"但也补了一句实用建议：日常用 PVE 时完全不用管这些，你只需要知道该选左侧哪个存储；这些属于专业存储领域的知识，是他碰到问题后顺手查资料整理出来的理解。

## 小结

- **`pve-data` 是 thin pool 类型的特殊 LV**：既有 LV 的特性，又有存储池的特性；`root`/`swap` 则是普通的 linear LV，厚置备。
- **精简制备需要账本**：池按需分配，靠元数据记录"谁用了多少"，所以它比厚置备多一层结构。
- **水位看百分比，不看容量**：`lvs` 的 `Data%`/`Meta%`，或 PVE 的 LVM-Thin 面板上的"使用率/元数据使用率"。
- **容量对不上的差额是隐藏卷**：`lvs -a` 能看到 [data_tdata]、[data_tmeta]、[lvol0_pmspare]，其中 `pmspare` 是元数据的备用空间。
- **虚拟硬盘天生是精简卷**：新建 100 GB 不占 100 GB，装完系统只占几个 G；厚薄由底层存储类型决定，PVE 不给你选。
- **一个卷的 `LSize` 和它的 `Data%` 是两回事**：前者是承诺，后者是实际，池的水位由所有卷的实际占用累加而成。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| LV（Logical Volume） | 逻辑卷，LVM 里对上层呈现的"块设备"，分 linear、thin、thin pool 等多种类型 |
| 厚置备（thick） | 创建时就把物理空间划走，用不完别人也用不了 |
| 精简制备（thin） | 只报逻辑容量，写入时才分配物理块 |
| thin pool | 精简池，多个精简卷共享的物理空间，自带元数据账本 |
| `Data%` / `Meta%` | `lvs` 输出的池数据使用率与元数据使用率，是真正的容量水位 |
| `tdata` / `tmeta` | 精简池内部真正存数据的卷和存元数据的卷，`lvs -a` 里带方括号 |
| `pmspare` | 元数据的备用空间，元数据出问题时顶上 |

> 想继续看"池写满之后会发生什么、怎么把空间要回来"，读同小节的《LVM thin 池写满不报错》。