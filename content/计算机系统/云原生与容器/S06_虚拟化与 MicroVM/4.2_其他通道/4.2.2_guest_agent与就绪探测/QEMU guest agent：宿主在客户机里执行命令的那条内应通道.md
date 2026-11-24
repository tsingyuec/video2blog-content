# QEMU guest agent：宿主想在客户机里执行命令，为什么必须先在里面安一个「内应」

> 视频来源：[Qemu Guest Agent in Proxmox, what it does and how to enable it](https://www.youtube.com/watch?v=wp4kCUM6dik)（YouTube · Brandon Lee / Proxmox 实践）｜时长约 19 分钟
> 导读：这支视频以 Proxmox 为例，把 guest agent 从「装在哪、怎么开」一路讲到「宿主能对它下哪些命令」。本文按「为什么需要 → 通道长什么样 → 怎么判断客户机就绪 → 能做什么 → 代价」重排，并把视频里的操作对应到「进程级 / 内核级 / 服务级」三层就绪判据上。视频里没有展开客户机侧的 virtio-serial 端口，本文在该处做了标注。

## 本讲要解决的核心问题（SCQA）

**背景**：hypervisor 能对一台虚拟机做很多物理主板做不到的事——在线迁移、快照、备份、暂停。这些操作在宿主侧都只是「操作一个进程」。

**冲突**：但客户机内部对宿主是个黑盒。宿主看得见「VM 进程在跑」，看不见「客户机里的服务在监听」；它不知道客户机的 IP，不知道内核版本，也没法让客户机先把缓存刷盘再拍快照。视频里最直观的一幕是：同一台 VM，装了 agent 的摘要页会列出 IP，没装的只显示一行 `No Guest Agent configured`。

**疑问**：宿主到底靠什么在客户机里执行命令、查询状态、做一致性快照？

**回答（中心思想）**：靠客户机里一个主动配合的进程——guest agent。宿主与它之间有一条专用控制通道（Proxmox 里是 `/var/run/qemu-server/<vmid>.qga` 这个 Unix socket），宿主把命令写成协议报文塞进去，agent 在客户机里执行完再把 JSON 结果送回来。**没有这个内应，宿主对客户机就只有「开机 / 关机 / 看进程」三种能力。**

## 一、宿主与客户机之间缺的不是带宽，而是「语义」

[【跳转到 00:00】](https://www.youtube.com/watch?v=wp4kCUM6dik&t=0) 视频开头给了一个很好的类比：物理主板上，操作系统能拿到的只有电源键、时钟、串口这些信号；而 hypervisor 能做到在线迁移、快照、备份，这些是物理主板给不了的。

问题是，这些能力要落地，光有 hypervisor 不够。以快照为例：宿主可以让 vCPU 停下来，但它不知道客户机文件系统里还有多少脏数据没落盘；以关机为例：宿主可以给客户机发一个 ACPI 电源键事件，但客户机完全可以配置成「按电源键什么也不做」——服务器操作系统常这么配，就是为了防止误触。

于是需要一个**在客户机里运行、听得懂宿主指令**的进程。视频把它讲得很直白：guest agent 提供的正是「超出物理主板能力」的那部分额外通信，让迁移、快照、备份这些操作能以最好的方式完成，顺便还能收集一批管理用的信息。

## 二、通道的两端：宿主一个 socket 文件，客户机一个系统服务

[【跳转到 03:34】](https://www.youtube.com/watch?v=wp4kCUM6dik&t=214) Proxmox 官方 wiki 写得很清楚：与 guest agent 的通信发生在 `/var/run/qemu-server/<my_vmid>.qga` 这个 Unix socket 上，验证方式是：

```bash
qm agent <vmid> ping
```

如果客户机里的 `qemu-guest-agent` 正常运行，这条命令**不输出任何东西**，直接返回提示符；如果不正常，它会明确告诉你 agent 没在跑。

![Proxmox wiki 的验证方式：宿主侧是一条 /var/run/qemu-server/<vmid>.qga 的 Unix socket，用 qm agent <vmid> ping 探活](assets/QEMU%20guest%20agent：宿主在客户机里执行命令的那条内应通道/00230.webp)

[【跳转到 01:09】](https://www.youtube.com/watch?v=wp4kCUM6dik&t=69) 要让这条链路通，**两端都得开**，缺一不可：

| 位置 | 要做什么 | 视频里的操作 |
| --- | --- | --- |
| 宿主（hypervisor） | 为这台 VM 启用 guest agent 通道 | VM → Options → `QEMU Guest Agent` 设为 Enabled |
| 客户机（Linux） | 安装并启动 `qemu-guest-agent` 服务 | `apt install qemu-guest-agent`，`systemctl status qemu-guest-agent` |
| 客户机（Windows） | 装 virtio 驱动包，其中包含 agent | 运行 virtio guest tools 安装器，服务名 `qemu-guest-agent` |

![宿主侧只有一个开关：Options 里的 QEMU Guest Agent 设为 Enabled，通道才会被创建出来](assets/QEMU%20guest%20agent：宿主在客户机里执行命令的那条内应通道/00238.webp)

[【跳转到 02:55】](https://www.youtube.com/watch?v=wp4kCUM6dik&t=175) 视频里 Debian 12 是预装好的，其它发行版按包管理器装同名包即可。注意它在客户机里**是一个常驻服务**（systemd unit 或 Windows 服务），不是一个命令行工具——这一点决定了后面「就绪探测」怎么设计。

> 补充（视频未展开）：在 QEMU 里，这条通道在客户机一侧表现为一个 **virtio-serial** 端口，agent 就是在这个端口上收发报文。宿主侧看到的是 socket 文件，客户机侧看到的是串口设备，中间由 VMM 转接。记住这个「宿主 socket ↔ 客户机串口」的对应关系，后面讲 Kata 的 vsock 时就能直接类比。

## 三、就绪的三级判据：进程活着、内核起来了、服务在监听

这是本小节最该带走的一张表。视频里出现的每一条命令，其实都落在不同层级上：

| 层级 | 判据 | 视频里的证据 | 它证明了什么 | 它证明不了什么 |
| --- | --- | --- | --- | --- |
| 进程级 | VM 进程在跑、vCPU 在 `KVM_RUN` | Proxmox 摘要页 `Status: running` | hypervisor 已经把这台机器「开起来了」 | 客户机内核可能还卡在引导 |
| 内核级 | 客户机内核启动完成 | `qm guest cmd <vmid> get-osinfo` 返回 `kernel-release` | 内核起来了，用户态也有了 | 业务进程可能还没监听端口 |
| agent 级 | agent 服务在应答 | `qm guest cmd <vmid> ping` 无输出 | 客户机的 init 已经把 agent 拉起来，通道双向可用 | 业务容器/服务是否就绪 |
| 服务级 | 应用真的在监听 | `qm guest exec <vmid> ...` 拿到 `exitcode: 0`（近似） | 能在客户机里跑命令并拿到结果 | 端口是否 accept、依赖是否就绪 |

![同一台没装 agent 的 VM，摘要页的 IPs 一栏只能显示 No Guest Agent configured——宿主连客户机的地址都看不到](assets/QEMU%20guest%20agent：宿主在客户机里执行命令的那条内应通道/00250.webp)

![装上 agent 之后，摘要页自动列出 IPv6 与 IPv4 地址：这条信息是宿主通过 agent 问出来的，不是从网络里探到的](assets/QEMU%20guest%20agent：宿主在客户机里执行命令的那条内应通道/00243.webp)

这两张图放在一起看，就是「进程级就绪」与「agent 级就绪」的差别：两台 VM 的 `Status` 都是 running，但只有一台能被宿主问到内部状态。

**为什么这个区分重要**：MicroVM 宣传的「100 ms 启动」说的是第一级——VM 进程起来了；而「服务可用 100 ms」说的是第四级——应用已经在监听。中间隔着内核引导、init 拉起服务、agent 启动、应用初始化，秒级到十秒级的时间差是常态。把这两件事混为一谈，就会出现「启动耗时指标很漂亮，但请求一直 502」的情况。

## 四、agent 能做的四类事：查、执行、一致性、生命周期

[【跳转到 09:59】](https://www.youtube.com/watch?v=wp4kCUM6dik&t=599) 视频从 Proxmox 网页界面切到命令行，用 `qm guest` 展开全部能力。命令列表不用背，但要知道它分成四类。

### 4.1 查：把客户机内部状态变成宿主可读的 JSON

先看命令全集。视频里用了一个巧办法：随便传一个不存在的子命令，QEMU 会把枚举值全部回显出来：

```text
fsfreeze-freeze, fsfreeze-status, fsfreeze-thaw, fstrim, get-fsinfo,
get-host-name, get-memory-block-info, get-memory-blocks, get-osinfo,
get-time, get-timezone, get-users, get-vcpus, info, network-get-interfaces,
ping, shutdown, suspend-disk, suspend-hybrid, suspend-ram
```

![完整命令清单：freeze/trim 类、get-* 查询类、ping 探活、shutdown 与 suspend 生命周期类，一次回显全部枚举值](assets/QEMU%20guest%20agent：宿主在客户机里执行命令的那条内应通道/00720.webp)

![命令枚举与探活：传错子命令会回显全部可用命令；ping 在没装 agent 的 VM 上直接返回 QEMU guest agent is not running](assets/QEMU%20guest%20agent：宿主在客户机里执行命令的那条内应通道/00702.webp)

![get-users 与 get-osinfo 的返回：登录用户、内核版本、发行版、机器架构，全部是结构化 JSON，可直接喂给脚本](assets/QEMU%20guest%20agent：宿主在客户机里执行命令的那条内应通道/00760.webp)

![network-get-interfaces 的返回：每块网卡的 IPv4/IPv6 地址、前缀长度、收发统计，网页界面里的 IP 就是从这份数据里取的](assets/QEMU%20guest%20agent：宿主在客户机里执行命令的那条内应通道/00800.webp)

[【跳转到 12:58】](https://www.youtube.com/watch?v=wp4kCUM6dik&t=778) 视频特别点出：这些输出都是 JSON，方便塞进自己的脚本做批量处理。这也解释了为什么「查 IP」这件事在虚拟化平台里普遍依赖 agent——从外部扫网段既慢又不可靠，直接问客户机最快。

### 4.2 执行：在客户机里跑一条命令

[【跳转到 16:23】](https://www.youtube.com/watch?v=wp4kCUM6dik&t=983) `qm guest exec <vmid> <命令>` 可以在客户机里执行任意命令，Linux 与 Windows 都支持。视频演示了 `ls /`，返回结构里包含 `exitcode`、`exited` 和 `out-data`：

![qm guest exec 的返回：exitcode 0 表示命令执行成功，out-data 里是标准输出（换行被转义成 \n）](assets/QEMU%20guest%20agent：宿主在客户机里执行命令的那条内应通道/01007.webp)

这一条是「服务级探针」的雏形：如果宿主能在客户机里跑 `curl localhost:8080/healthz` 并拿到 0，那就是真正的服务级判据；而 `ping` 只能证明 agent 活着。视频也提醒，跑的是客户机里的最高权限用户（演示中是 root），所以这条通道的能力边界等于「客户机 root」。

### 4.3 一致性：拍快照前先把缓存刷下去

[【跳转到 06:10】](https://www.youtube.com/watch?v=wp4kCUM6dik&t=370) 这是 agent 最不可替代的用途。视频用「拔 U 盘」做类比：现代文件系统是日志式的，突然断电通常也能恢复，但正在写的文件可能出问题；正确做法是先 eject，把内存里待写的数据刷到盘上。

`fsfreeze` 做的就是这件事，分三步：

1. `fsfreeze-freeze`：同步所有在途写入，然后**暂停写操作**（视频说最长 10 秒）；
2. 宿主在这个窗口里拍快照 / 做备份；
3. `fsfreeze-thaw`：恢复写入。

![fsfreeze 的三个动作：freeze 返回 1，thaw 返回 1，status 显示 thawed；紧接着可以安全地 shutdown](assets/QEMU%20guest%20agent：宿主在客户机里执行命令的那条内应通道/00900.webp)

[【跳转到 07:33】](https://www.youtube.com/watch?v=wp4kCUM6dik&t=453) 视频给的时间账很实用：整机停机再做快照要几分钟，而 freeze 窗口只有几十毫秒量级，对文件系统完整性却是「花小钱办大事」。他也诚实地说，自己做过很多不 freeze 的备份也恢复成功了，但最近修改过的文件风险更高。对延迟敏感的业务，需要自己压测确认这几十毫秒能不能接受。

同一类里还有 `fstrim`：把「哪些块已经不用了」告诉宿主，帮虚拟磁盘瘦身、缩短备份时间。视频实测 XFS、BTRFS 可用，ZFS 不行。

![fstrim 的返回：path 与 trimmed 字节数；它等价于在客户机里跑一次 TRIM](assets/QEMU%20guest%20agent：宿主在客户机里执行命令的那条内应通道/00860.webp)

### 4.4 生命周期：关机、挂起、改密码

[【跳转到 14:57】](https://www.youtube.com/watch?v=wp4kCUM6dik&t=897) 没有 agent 时，「关机」只是给客户机发一个电源键事件，客户机可以不理会；有 agent 时，`shutdown` 是让客户机里的 agent 执行真正的关机流程，视频说它「总是能关掉」。[【跳转到 15:32】](https://www.youtube.com/watch?v=wp4kCUM6dik&t=932) `qm guest passwd` 则能在宿主侧重置客户机用户密码，适合批量运维或防止把自己锁在门外。

## 五、探针放在哪一层，就决定了它测的是什么

把上面四类能力放回「就绪探测」的语境，可以得到一张对照表。这张表也是与 S03 容器探针的分界线：**S03 讲 liveness/readiness/startup 的配置语义，这里讲这些探针在 VM 运行时里靠什么通道落地。**

| 探针位置 | 典型实现 | 测到的是 | 代价 |
| --- | --- | --- | --- |
| VMM 进程 / vCPU | 宿主看进程状态、`KVM_RUN` 是否在跑 | 机器起来了 | 几乎为零，但信息量也最少 |
| 客户机内核 | 串口日志匹配 `login:`、`multi-user.target` | 内核与 init 完成 | 要解析日志，格式随发行版变 |
| guest agent | `ping`、vsock 心跳 | 客户机用户态可用、通道双向通 | 需要客户机配合装 agent |
| 应用 | `guest-exec` 跑健康检查、K8s readinessProbe | 服务真的能应答 | 需要业务暴露健康端点 |

视频里那条 `ping` 命令值得单独说一句：它**不返回任何内容**才算成功。这种「静默即成功」的约定在探活里很常见，但也容易误判——脚本必须把「命令非零退出」和「输出为空」分开处理，否则会把失败当成功。

再往下走一步，如果客户机里跑的是 Kata 这样的容器运行时，探针还要再穿两层：kubelet 发起探测 → CRI → shim → VM 里的 agent → 容器。这条链路在本小节另一篇《Kata Containers 的 agent 与 shim》里展开。

## 六、代价与风险：为什么不是「无脑全开」

[【跳转到 17:34】](https://www.youtube.com/watch?v=wp4kCUM6dik&t=1054) 视频作者的态度是「大多数 VM 都建议开」，但列了三类要留神的地方：

1. **功能本身可能出问题**：freeze 会让客户机短暂无法写盘，对延迟敏感负载要实测；某些文件系统（如 ZFS）不支持 fstrim。
2. **安全面变大**：agent 通道等于给宿主开了一条在客户机里以 root 执行命令的路。视频提到历史上确实有涉及 guest agent 的 CVE，多数是 Windows 侧的提权问题。
3. **信任模型要想清楚**：作者的观点是，你本来就得信任 hypervisor——它能直接改磁盘镜像、能改进出 VM 的数据，已经拥有完全控制权。所以 agent 并没有引入一个新的信任方，只是把已有能力做成了接口。

这段讨论对做沙箱的人尤其重要：**guest agent 是「宿主可信、客户机不可信」模型下的产物**。如果客户机里跑的是不可信代码，agent 就是攻击面的一部分，必须跟着 VMM 一起做最小权限（seccomp、最小设备集），这也是 MicroVM 运行时普遍把 agent 通道收窄到「只做必要的配置注入」的原因。

## 小结

- 宿主对客户机是黑盒：能开机关机看进程，但看不到 IP、内核版本、文件系统状态，也无法优雅关机。guest agent 就是补上这块的「内应」。
- 通道两端都要开：宿主侧启用通道（Proxmox 里是 `Options → QEMU Guest Agent`），客户机侧跑常驻服务（`qemu-guest-agent`）。宿主侧表现为 `/var/run/qemu-server/<vmid>.qga` 这个 Unix socket。
- 就绪至少分三层：VM 进程在跑（进程级）、客户机内核与 init 完成（内核级）、应用在监听（服务级）。`ping` 落在 agent 级，`get-osinfo` 落在内核级，`guest-exec` 才勉强够到服务级。
- agent 的四类能力：查状态（JSON）、执行命令、保证一致性（freeze/trim）、管生命周期（关机/挂起/改密码）。
- 一致性快照是 agent 最不可替代的用途：freeze 把写操作暂停几十毫秒，换来可恢复的磁盘镜像。
- 代价是攻击面与短暂停顿；在不可信客户机场景里，agent 必须和 VMM 一起做最小权限。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| guest agent | 跑在客户机里的常驻服务，替宿主执行命令、汇报状态 |
| QGA（QEMU Guest Agent） | QEMU 定义的 agent 与宿主之间的命令协议，命令如 `ping`、`get-osinfo`、`fsfreeze-freeze` |
| virtio-serial | 客户机侧看到的虚拟串口设备，agent 通道就架在它上面 |
| `qm agent` / `qm guest` | Proxmox 宿主侧的命令行入口，前者是别名，后者是完整命令 |
| fsfreeze | 暂停客户机文件系统写入并刷盘，用于拍一致性快照 |
| fstrim | 告诉宿主哪些块已不再使用，用于瘦身虚拟磁盘 |
| 进程级 / 内核级 / 服务级就绪 | 三层判据：VM 进程在跑、客户机内核启动完成、应用已在监听 |