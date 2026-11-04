# MTU、MSS 与 PMTUD 网络黑洞

本系列整理四个 Bilibili / YouTube 视频，从基础概念、隧道封装到故障定位与抓包验证，理解为什么“小包能通，大包却卡住”。每个视频单独保留一篇中文博客，并附原画面与时间戳。

## 阅读路线

1. **基础概念**：先区分 TCP 分段与 IP 分片，理解 MTU、MSS、1500 与 1460 的关系。
2. **隧道机制**：再理解 IPsec 封装为什么挤占可用空间，以及 ICMP 反馈丢失如何形成 PMTUD 黑洞。
3. **案例排障**：跟随 RouterOS 案例，用临时调整与 MSS 规则验证实际故障。
4. **抓包实验**：观察不同链路 MTU 下的 ICMP 报错，以及发送方随后缩小的数据包。

## 视频与博客

| # | 视频 | 作者 | 时长 | 平台 | 博客 |
| --- | --- | --- | ---: | --- | --- |
| 1 | IPv4分片问题 \| MTU和MSS的核心区别 | 技术蛋老师 | 10:36 | Bilibili | [博客](blog/IPv4分片问题%20｜%20MTU和MSS的核心区别.md) |
| 2 | 别再查带宽了！VPN连上却卡死的真相：MTU／MSS深度避坑指南 | staylightblow | 16:09 | Bilibili | [博客](blog/别再查带宽了！VPN连上却卡死的真相：MTU／MSS深度避坑指南.md) |
| 3 | 72. 解决RouterOS上的IPSec MTU/MSS问题，你的IPSec能ping不能上网吗？ | ZacGuo | 20:07 | Bilibili | [博客](blog/72.%20解决RouterOS上的IPSec%20MTU_MSS问题，你的IPSec能ping不能上网吗？.md) |
| 4 | PROOF OF CONCEPT \| PMTUD \| PATH MTU DISCOVERY | The Networking Baseline | 25:22 | YouTube | [博客](blog/PROOF%20OF%20CONCEPT%20｜%20PMTUD%20｜%20PATH%20MTU%20DISCOVERY.md) |

原视频：

1. [BV14GyGY8ENw](https://www.bilibili.com/video/BV14GyGY8ENw/)
2. [BV1dz61B9Ed2](https://www.bilibili.com/video/BV1dz61B9Ed2/)
3. [BV1F34y1C7b7](https://www.bilibili.com/video/BV1F34y1C7b7/)
4. [youtube.com/watch?v=wleh0q5sc4I](https://www.youtube.com/watch?v=wleh0q5sc4I)

## 内容速览

- **① 基础概念**：MTU 是接口上限、MSS 是 TCP 负载上限，1500 − 20 − 20 = 1460；分片字段（标识/片偏移/MF）、MSS Clamping、DF 与 PMTUD、IPv6 不允许中间分片。
- **② 隧道机制**：MTU（接口视角）/ PMTU（路径视角）/ MSS（TCP 视角）；NAT-T + ESP 让 1500 的内层包涨到 1570~1600；ICMP 被过滤 → PMTU 黑洞；MSS Clamping + 隧道 MTU + 放行 ICMP；策略型 vs 路由型 IPsec。
- **③ 案例排障**：RouterOS 上 SA active、ping 通但网页打不开；`action=none` policy 摘出 ICMP（对作者环境无效）；`firewall mangle` forward 链改 MSS=1300 解决；性能代价与数值取舍。
- **④ 抓包实验**：三路由器链路上 1500 → 1300 → 1100 的逐跳收敛；帧长 1514 → 1314 → 1114；两条来自不同路由器的 ICMP；用 IP ID 反查被丢的包。

## 核心结论

- **症状指纹**：能连上、ping 通，但网页/下载/SSH 输出卡——「小包通、大包不通」就是 MTU 类问题的第一嫌疑。
- **根因**：封装让包变大 → 超过路径 MTU → 被丢弃；而 ICMP 反馈被过滤 → 发送方不知道要变小 → PMTU 黑洞。
- **解法优先级**：从源头把包变小（MSS Clamping、隧道接口 MTU）> 放行必要 ICMP 让 PMTUD 工作 > 依赖中间设备临场分片（代价最高，NAT 尤其不友好）。
- **工程选择**：优先路由型 IPsec（有可见隧道接口，MTU/MSS/抓包/计数器集中管理），而非策略型。
- **验证手段**：主机侧临时改 MTU 做对照、抓包看帧长与 ICMP、用 IP ID 把 ICMP 与被丢的包对应。

## 产物与来源

- 博客依据各自的视频演说图文稿整理，原视频链接与关键时间点见各篇文章。
- 英文实验整理为中文；字幕中的术语与数字结合画面校正，无法确认的细节保留说明。
- 视频、1fps 抽帧、原始字幕与逐窗口校正的图文稿位于 `_work/network_mtu/`，不进入版本库。
- `content/network_mtu/` 仅收录系列索引、最终博客和配图。
