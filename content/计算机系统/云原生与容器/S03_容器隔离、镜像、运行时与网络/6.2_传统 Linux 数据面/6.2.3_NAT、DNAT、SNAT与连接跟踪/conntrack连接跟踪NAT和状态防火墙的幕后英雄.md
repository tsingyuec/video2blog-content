# 连接跟踪 conntrack：NAT 与状态防火墙共同的幕后英雄

> 本文整理自 B 站视频《conntrack连接跟踪NAT和状态防火墙的幕后英雄》。它把一个「你从来没正眼看过的内核子系统」请到台前，讲透 **状态防火墙、NAT、`state` 状态匹配为什么都建立在同一张哈希表上**，以及 **conntrack 是怎么记住每一条连接的**。

## 本讲要解决的核心问题（SCQA）

**背景**：很多人写过 iptables 里那行 `-m state --state ESTABLISHED,RELATED -j ACCEPT`，也用过 Docker、Kubernetes——这些「有状态」的能力一直在默默工作。

**冲突**：可这些能力到底是由谁提供的？为什么几乎所有云原生网络故障，最后都能追溯到同一个东西？为什么一条 `nf_conntrack: table full, dropping packet` 能让运维做噩梦？

**疑问**：这个叫 conntrack（连接跟踪）的子系统到底是什么？它怎么记住一条连接的状态？NAT 又是怎么「借」它完成地址改写的？

**回答（中心思想）**：**Linux 上所谓的「状态防火墙」、`state` 状态匹配、以及 NAT，全部建立在同一张内核哈希表——conntrack（`nf_conntrack`）之上。** 它给每一条连接建一份「档案」（两个方向各一个 tuple），在 **PREROUTING 登记、POSTROUTING 提交**；NAT 的魔法就藏在它预埋的 **reply tuple** 里——所以只有第一个 SYN 真正跑了 NAT 规则，后面的包全靠查表，这正是 Linux NAT 能抗住几百万 PPS 的根本原因。而这张表一旦写满，新连接就建不起来。

[【跳转到 00:00】](https://www.bilibili.com/video/BV1s29YBBEqT/?t=0)

---

## 一、conntrack 是什么：状态防火墙和 NAT 的共同底座

视频先抛出一个反直觉的事实：**Linux 上所谓的状态防火墙、所谓的 NAT、所谓的 `state` 状态匹配，全部建立在同一张内核哈希表之上。** 这张表只要满了，新连接就建不起来——它就是 **conntrack**。

### 1.1 一个「酒店前台」的类比

想象你开了一家酒店：每来一位客人，前台都要在大本子上记一行——**证件号、房号、入住时间**。之后客人每次进出大堂、点外卖、收快递，前台都要翻这个本子核对身份；客人退房，前台就在那一行画上删除，房间腾给下一位。

**conntrack 干的就是前台这件事**，只不过它登记的不是客人，是**网络连接**。把类比里的角色一一对上号：

| 酒店类比 | conntrack 世界 |
| --- | --- |
| 新客人 | SYN 包 |
| 前台登记 | 建一条 `nf_conntrack` 条目 |
| 每次进出核对身份 | 包到达 **PREROUTING** 时查哈希表 |
| 客人退房 | **FIN** 来了之后销毁条目 |
| 登记本写满 | 内核日志里的 `nf_conntrack: Table full, dropping packet` |

[【跳转到 01:15】](https://www.bilibili.com/video/BV1s29YBBEqT/?t=75)

![conntrack 就像酒店前台，为每一条网络连接登记「档案」](assets/conntrack连接跟踪NAT和状态防火墙的幕后英雄/00075.webp)

### 1.2 挂在 netfilter 上的钩子：五个 hook，两处介入

conntrack **并不是一个独立子系统**，它是挂在 netfilter 框架上的钩子函数。一个数据包从网卡进来到出去，要穿过**五个 hook 点**，conntrack 在其中两个点做关键介入：

- **进门的 PREROUTING**：负责**试着登记**；
- **出门的 POSTROUTING**：负责**真正归档**。

[【跳转到 01:40】](https://www.bilibili.com/video/BV1s29YBBEqT/?t=100)

![conntrack 在 PREROUTING 与 POSTROUTING 两个 hook 点介入](assets/conntrack连接跟踪NAT和状态防火墙的幕后英雄/00100.webp)

**为什么要把「建条目」拆成两步？** 因为包进来之后，**路由可能 drop 它、防火墙也可能 drop 它**；要是先把条目挂到全局哈希表、再被 drop，就脏表了。

所以 conntrack 用了一个非常经典的设计：**Unconfirmed list（未确认列表）**——先在 PREROUTING 预定，到 POSTROUTING 真要发包了再 **confirm**。这和**数据库的两阶段提交是一个味道**。

> 视频顺带致敬了几位把 conntrack 工程化的工程师：当前 netfilter 核心维护者、新一代 nftables 主要作者 **Pablo Neira Ayuso**；2.4 内核时代推动工程化的 **Harald Welte**；以及 2.6 内核大重构的 **Patrick McHardy**——正是他把原来只支持 IPv4 的 `ip_conntrack` 抽象成**协议无关的 `nf_conntrack`**，让 IPv6、bridge、各种 L4 协议能复用同一套连接跟踪逻辑，今天你看到的 `struct nf_conntrack` 就出自他手。

[【跳转到 02:23】](https://www.bilibili.com/video/BV1s29YBBEqT/?t=143)

---

## 二、一条连接长什么样：`struct nf_conntrack` 与「双 tuple」

来看 conntrack 的灵魂——`struct nf_conntrack`。这里最关键的不是它有多少字段，而是这一行：

> **一个 tuple 数组，长度为二——两个 tuple，一个「原始方向」、一个「回程方向」。一条连接的档案，就是它们俩。**

[【跳转到 03:23】](https://www.bilibili.com/video/BV1s29YBBEqT/?t=203)

![一条连接用两个 tuple 记录：原始方向与回程方向](assets/conntrack连接跟踪NAT和状态防火墙的幕后英雄/00203.webp)

重点来了：这两个 tuple（原始方向和回程方向）会被**同时插入同一张全局哈希表**，但**都指向同一个 `nf_conntrack` 节点**。这意味着——**无论去包还是来包，只要哈希命中，就能找到这条连接**。NAT 的所有魔法，全都藏在 **reply tuple** 这一处伏笔里。

### 2.1 查表为什么这么快：三个设计细节

conntrack 的查表核心函数有三个值得记住的细节：

[【跳转到 03:48】](https://www.bilibili.com/video/BV1s29YBBEqT/?t=228)

![conntrack 查表：RCU 无锁、乘法移位代替取模、扩容时重试](assets/conntrack连接跟踪NAT和状态防火墙的幕后英雄/00228.webp)

1. **整个查表路径在 RCU 保护下完全无锁**；
2. **用 reciprocal scale 做「乘法 + 移位」代替取模**，每个包能省下几个 CPU 周期；
3. **扩容时哈希表会换一张新表**，遍历到一半发现 bucket 变了就跳到 begin 重试——这是经典的**读优先系统设计**：查表绝不阻塞写入扩容。

---

## 三、五个状态 + TCP 子状态机

conntrack 给每个包打的标签只有**五个通用状态**：

[【跳转到 04:13】](https://www.bilibili.com/video/BV1s29YBBEqT/?t=253)

![conntrack 的五个状态：NEW / ESTABLISHED / RELATED / INVALID / UNTRACKED](assets/conntrack连接跟踪NAT和状态防火墙的幕后英雄/00253.webp)

| 状态 | 含义 |
| --- | --- |
| **NEW** | 第一次见到的连接 |
| **ESTABLISHED** | 双向都看到包了 |
| **RELATED** | 关联连接，例如 FTP 数据通道、ICMP error |
| **INVALID** | 状态机判定不合法的连接 |
| **UNTRACKED** | 被显式 `NOTRACK` 跳过、不跟踪的连接 |

iptables 那行 `-m state --state ESTABLISHED,RELATED -j ACCEPT`，匹配的就是前面这几个状态。

TCP 比 UDP 复杂得多——conntrack 在 `nf_conntrack_proto_tcp.c` 里维护了一个**完整的子状态机**（常在资料里被概括为 TCP 的十余个子状态）。但这里要特别提醒一句：**这是 conntrack 在路上「看到包之后猜出来」的状态，不是真正端点的 TCP 状态**。conntrack 只是个看客，它的状态机是**包级别的近似**，够用，但**不要拿它替代真正的 TCP 调试**。

[【跳转到 05:03】](https://www.bilibili.com/video/BV1s29YBBEqT/?t=303)

---

## 四、NAT 的魔法，全在 reply tuple 里

现在揭开 NAT 的秘密：**当一条连接被 SNAT 时，conntrack 不光记原始方向，它顺手把 reply tuple 里的目标地址改成了 NAT 后的地址。** 回包到达时，按 NAT 后的地址做哈希，就能命中 reply tuple、找到 `nf_conntrack`，看到 NAT 标志位，conntrack 再顺手把目的地址改回内网 IP。

[【跳转到 05:28】](https://www.bilibili.com/video/BV1s29YBBEqT/?t=328)

> **关键结论**：整个过程**只有第一个 SYN 真正跑了 NAT 规则**，后面的包**全部走查表**——这就是 Linux NAT 能抗住几百万 PPS 的根本原因。

### 4.1 helpers：让 conntrack 看懂应用层的「口子」

有些应用层协议比较「坏」——比如 **FTP、SIP、H.323**，它们的控制连接里会**临时协商出一个新端口**用于数据传输。状态防火墙没法预先放行未知端口，怎么办？

conntrack 给了一个口子叫 **helper（也叫 ALG，应用层网关）**：它会解析控制连接的应用层内容，提前告诉 conntrack——「等会儿有人按这个 tuple 来，你要把它标记成 **RELATED**」。这样防火墙就敢放行了。

[【跳转到 05:53】](https://www.bilibili.com/video/BV1s29YBBEqT/?t=353)

**但是**：helper 解析的是**明文**，对 HTTPS 完全无能为力。

### 4.2 一条连接在 conntrack 眼里的一生

追一条最典型的连接，它在 conntrack 眼里的时间线大致是：

[【跳转到 06:18】](https://www.bilibili.com/video/BV1s29YBBEqT/?t=378)

- 前 **0.5ms**：建立条目 + 做 NAT 决策；
- **20ms**：回包到达，reply tuple 哈希命中，自动反向解 NAT，子状态机推进；
- 然后是 **8 秒**的数据交换；
- 最后是 **FIN** 退出。

---

## 五、conntrack 表满了会怎样：最凶险的「部分故障」

最让人意外的是 `TIME_WAIT` 这一行——**默认要等 120 秒才被 GC（垃圾回收）真正擦掉**。这意味着**每一条短连接在 conntrack 表里至少要占用 2 分钟**。现在你知道为什么这一行会让无数运维做噩梦了。

[【跳转到 06:43】](https://www.bilibili.com/video/BV1s29YBBEqT/?t=403)

![conntrack 表满会导致新连接的 SYN 被丢弃，形成难以排查的部分故障](assets/conntrack连接跟踪NAT和状态防火墙的幕后英雄/00403.webp)

**表满意味着新连接的 SYN 全被 drop。** 于是会出现一种**最难排查的「部分故障」**：业务表面看似「网络不通」，但 **ping 通、SSH 通、已建立的连接还在**——偏偏新连接建不起来。

### 5.1 表满的三种典型成因

[【跳转到 07:08】](https://www.bilibili.com/video/BV1s29YBBEqT/?t=428)

1. **`max` 参数默认基于内存自动算，但不一定够你用**；
2. **某些状态超时长得吓人**，例如 `ESTABLISHED` 默认五天，连接没正常关就一直占着位置；
3. **真的被打了 DDoS、扫描、短连接风暴**。

定位的方法：看 `conntrack -S` 的 drop 和 insert，以及 `/proc/sys/net/netfilter/` 下相关表的 count 与 max 比例。

### 5.2 应对的三招

[【跳转到 07:33】](https://www.bilibili.com/video/BV1s29YBBEqT/?t=453)

![表满的三种成因与三招应对：调大 max/扩容、缩短超时、改长连接](assets/conntrack连接跟踪NAT和状态防火墙的幕后英雄/00453.webp)

1. **调大 `max` 和 buckets**，两者按大约 **4:1** 的比例；
2. **缩短 `ESTABLISHED` 超时**，一小时通常就够了；
3. **业务侧改长连接、用连接池复用**，减少表项膨胀。

其中**第三招是治本**，前两个是治标。

---

## 六、conntrack 在云原生世界的位置

[【跳转到 07:58】](https://www.bilibili.com/video/BV1s29YBBEqT/?t=478)

![conntrack 支撑 kube-proxy iptables 模式，而 Cilium 等倾向用 eBPF 绕开它](assets/conntrack连接跟踪NAT和状态防火墙的幕后英雄/00478.webp)

- **kube-proxy 的 iptables 模式之所以能工作**，就是 **ClusterIP DNAT 之后的反向解地址全靠 conntrack 一手包办**；
- conntrack 还能让**主备防火墙同步连接表**，实现无感切换；
- 而 **Cilium 和现代 sidecar 模式**则倾向**绕开 conntrack，用 eBPF 自己管理连接状态**——因为在某些极致性能场景，conntrack 反而成了瓶颈。

---

## 小结

- **一张表撑起三种能力**：状态防火墙、`state` 状态匹配、NAT，全都建立在 conntrack 这张内核哈希表上。
- **档案 = 双 tuple**：一条连接记录「原始方向 + 回程方向」两个 tuple，都指向同一个 `nf_conntrack` 节点。
- **两阶段登记**：PREROUTING 预定（Unconfirmed list）、POSTROUTING 提交，避免「脏表」，类似数据库两阶段提交。
- **NAT 靠 reply tuple**：SNAT 时预埋回程地址，回包查表即命中；只有第一个 SYN 跑规则，后续全查表——**百万 PPS 的根因**。
- **五个状态**：NEW / ESTABLISHED / RELATED / INVALID / UNTRACKED；TCP 另有**包级别近似**的子状态机（别当真正的 TCP 状态用）。
- **helpers/ALG** 让 conntrack 看懂 FTP 等应用层协议、标记 RELATED，但**解析不了 HTTPS**。
- **表满是隐形杀手**：表现为「ping 通、SSH 通，唯独新连接不通」的部分故障；成因是 max 不足、超时过长、DDoS；应对是调大 max/buckets、缩短超时、改长连接（治本）。
- **云原生位置**：kube-proxy iptables 模式离不开它，Cilium 等则用 eBPF 绕开它。

[【跳转到 08:23】](https://www.bilibili.com/video/BV1s29YBBEqT/?t=503)

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| conntrack（nf_conntrack） | Linux 内核的连接跟踪子系统，为每条连接维护「档案」，是状态防火墙与 NAT 的底座 |
| tuple | 连接的一个方向（五元组信息），一条连接用「原始方向 + 回程方向」两个 tuple 表示 |
| reply tuple | 预埋的「回程方向」记录；NAT 借它记录改写后的地址，回包查表即命中 |
| Unconfirmed list | 未确认列表：PREROUTING 先预定条目，POSTROUTING 确认后才正式入表 |
| PREROUTING / POSTROUTING | conntrack 介入的两个 hook 点：进门登记、出门提交 |
| NEW / ESTABLISHED / RELATED | 连接跟踪的通用状态：新建 / 已建立 / 关联连接 |
| INVALID / UNTRACKED | 状态机判定不合法 / 被显式 NOTRACK 跳过的连接 |
| helper（ALG） | 应用层网关，解析控制连接（如 FTP）内容以放行协商出来的新端口（标为 RELATED） |
| `conntrack -S` | 查看 conntrack 统计（如 drop/insert）的工具命令 |
| RCU | 读-复制-更新机制，让 conntrack 的查表路径完全无锁 |
