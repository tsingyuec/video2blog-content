# 容器网络排障

> 本页收录不适合单独成脉络的容器网络排障材料，不设状态机，不计入脉络小节数；可作为 S03 容器网络数据面的延伸阅读。

## 1 单机网络排障基础

- 1.1 网络命名空间与 veth 排查 <a id="misc-net-1-1"></a>
  - 学习目标：用 netns/veth 命令定位容器网络断点。
- 1.2 路由、NAT 与连接跟踪排查 <a id="misc-net-1-2"></a>
  - 学习目标：用路由/NAT/conntrack 命令定位转发问题。
- 1.3 抓包与包路径分析 <a id="misc-net-1-3"></a>
  - 学习目标：用 tcpdump 抓包并还原包路径。
- 1.4 常见单机容器网络故障模式 <a id="misc-net-1-4"></a>
  - 学习目标：列举常见单机容器网络故障模式与排查顺序。

<a id="misc-net-2"></a>
## 2 MTU、MSS 与 PMTUD

<a id="misc-net-2-1"></a>
### 2.1 MTU、MSS 与分片

- 2.1.1 MTU、MSS 与 1500/1460 的关系 <a id="misc-net-2-1-1"></a>
  - 学习目标：解释 MTU/MSS 与 1500/1460 的关系。
- 2.1.2 IPv4 分片与 DF 标志 <a id="misc-net-2-1-2"></a>
  - 学习目标：说明 IPv4 分片与 DF 标志的行为。
- 2.1.3 IPv6 与 PMTUD <a id="misc-net-2-1-3"></a>
  - 学习目标：说明 IPv6 下 PMTUD 的工作方式。

<a id="misc-net-2-2"></a>
### 2.2 隧道封装与 PMTUD 黑洞

- 2.2.1 IPsec 封装与 MTU 挤占 <a id="misc-net-2-2-1"></a>
  - 学习目标：说明 IPsec 封装如何挤占 MTU。
- 2.2.2 ICMP 过滤与 PMTU 黑洞 <a id="misc-net-2-2-2"></a>
  - 学习目标：解释 ICMP 过滤如何造成 PMTU 黑洞。
- 2.2.3 MSS Clamping 与隧道 MTU <a id="misc-net-2-2-3"></a>
  - 学习目标：说明 MSS Clamping 与隧道 MTU 的配置。

<a id="misc-net-2-3"></a>
### 2.3 案例与抓包验证

- 2.3.1 RouterOS IPsec MTU/MSS 案例 <a id="misc-net-2-3-1"></a>
  - 学习目标：复盘 RouterOS IPsec MTU/MSS 案例。
- 2.3.2 逐跳 MTU 收敛与抓包 <a id="misc-net-2-3-2"></a>
  - 学习目标：用逐跳 MTU 收敛与抓包定位问题。
- 2.3.3 IP ID 反查被丢的包 <a id="misc-net-2-3-3"></a>
  - 学习目标：用 IP ID 反查被丢弃的包。

## 导航

[返回工具与排障](../README.md) · [知识总目录](../../../README.md)
