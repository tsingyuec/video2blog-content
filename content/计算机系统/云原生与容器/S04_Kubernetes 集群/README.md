# S04 Kubernetes 集群

编号：S04 · 类型：系统专题 · 目录规模：67 个小节（三级叶子节点）。

> 本文件是 `content-new` 的完整目录草案。状态统一为 `[DONE]`，待 Phase 2 映射 video2blog 博客后更新。

## 脉络章程

**知识主线**：从集群组件与声明式 API 出发，沿控制器、调度、CNI、Service、CSI 与准入，理解 Kubernetes 控制面与数据面的职责边界。

**一句话范围**：不重复讲容器底层隔离、镜像与运行时（归 S03），也不展开单机容器网络数据面（归 S04）；聚焦集群编排层。

**学习入口 → 学习出口**：Linux 基础、容器隔离/镜像/运行时与网络（可复用 S03） → 能解释一个 Pod 从提交到运行、从 Service 到后端 Pod 的完整链路，能定位常见调度、网络、存储与准入问题。

**完整问题链**：
1. 集群架构与声明式模型
2. 控制器与工作负载
3. 调度与节点执行
4. Pod 网络与 CNI
5. 服务、入口与现代集群数据面
6. Kubernetes 存储抽象与准入策略

**与相邻脉络的关系**：Linux 基础、容器隔离/镜像/运行时与网络（可复用 S03）

> 博客已从 `content/K8s集群` 迁入对应小节子目录；`5.1.5 kube-proxy IPVS 模式` 已补充手工实现 IPVS 转发的落地博客（IPVS 机制与 kube-proxy 概览见 S03 6.2.4）。

## 目录

<a id="s04-1"></a>
## 1 集群架构与声明式模型

<a id="s04-1-1"></a>
### 1.1 集群组件与职责

- 1.1.1 控制面组件与职责 <a id="s04-1-1-1"></a> [DONE]
- 1.1.2 节点组件与职责 <a id="s04-1-1-2"></a> [DONE]
- 1.1.3 组件间通信与高可用基础 <a id="s04-1-1-3"></a> [DONE]

<a id="s04-1-2"></a>
### 1.2 声明式 API 与资源模型

- 1.2.1 期望状态与声明式 API <a id="s04-1-2-1"></a> [DONE]
- 1.2.2 API 资源、GVK 与命名空间 <a id="s04-1-2-2"></a> [DONE]
- 1.2.3 标签、选择器与 OwnerReference <a id="s04-1-2-3"></a> [DONE]

<a id="s04-1-3"></a>
### 1.3 etcd 与 API Server

- 1.3.1 etcd 与 Raft 共识 <a id="s04-1-3-1"></a> [DONE]
- 1.3.2 watch 机制与事件分发 <a id="s04-1-3-2"></a> [DONE]
- 1.3.3 kube-apiserver 请求流水线 <a id="s04-1-3-3"></a> [DONE]

<a id="s04-2"></a>
## 2 控制器与工作负载

<a id="s04-2-1"></a>
### 2.1 控制器模式

- 2.1.1 Reconcile 循环 <a id="s04-2-1-1"></a> [DONE]
- 2.1.2 Informer 与工作队列 <a id="s04-2-1-2"></a> [DONE]
- 2.1.3 控制器与期望状态收敛 <a id="s04-2-1-3"></a> [DONE]

<a id="s04-2-2"></a>
### 2.2 工作负载控制器

- 2.2.1 Deployment 与 ReplicaSet <a id="s04-2-2-1"></a> [DONE]
- 2.2.2 StatefulSet <a id="s04-2-2-2"></a> [DONE]
- 2.2.3 DaemonSet <a id="s04-2-2-3"></a> [DONE]
- 2.2.4 Job 与 CronJob <a id="s04-2-2-4"></a> [DONE]

<a id="s04-2-3"></a>
### 2.3 扩展控制面

- 2.3.1 CRD 与自定义资源 <a id="s04-2-3-1"></a> [DONE]
- 2.3.2 Operator 模式 <a id="s04-2-3-2"></a> [DONE]
- 2.3.3 控制器与准入控制的协作 <a id="s04-2-3-3"></a> [DONE]

<a id="s04-3"></a>
## 3 调度与节点执行

<a id="s04-3-1"></a>
### 3.1 调度

- 3.1.1 调度框架 <a id="s04-3-1-1"></a> [DONE]
- 3.1.2 过滤与打分 <a id="s04-3-1-2"></a> [DONE]
- 3.1.3 资源请求与节点可分配资源 <a id="s04-3-1-3"></a> [DONE]
- 3.1.4 亲和与反亲和 <a id="s04-3-1-4"></a> [DONE]
- 3.1.5 污点与容忍 <a id="s04-3-1-5"></a> [DONE]
- 3.1.6 拓扑分布约束 <a id="s04-3-1-6"></a> [DONE]
- 3.1.7 优先级与抢占 <a id="s04-3-1-7"></a> [DONE]

<a id="s04-3-2"></a>
### 3.2 节点执行

- 3.2.1 kubelet 职责 <a id="s04-3-2-1"></a> [DONE]
- 3.2.2 Pod 生命周期 <a id="s04-3-2-2"></a> [DONE]
- 3.2.3 探针 <a id="s04-3-2-3"></a> [DONE]
- 3.2.4 CRI、CNI、CSI 的调用关系 <a id="s04-3-2-4"></a> [DONE]
- 3.2.5 Static Pod <a id="s04-3-2-5"></a> [DONE]
- 3.2.6 节点状态与心跳 <a id="s04-3-2-6"></a> [DONE]

<a id="s04-4"></a>
## 4 Pod 网络与 CNI

<a id="s04-4-1"></a>
### 4.1 Pod 网络模型

- 4.1.1 每 Pod 一个 IP 的网络模型 <a id="s04-4-1-1"></a> [DONE]
- 4.1.2 pause 容器与网络命名空间 <a id="s04-4-1-2"></a> [DONE]
- 4.1.3 Pod 内容器通信与共享网络栈 <a id="s04-4-1-3"></a> [DONE]

<a id="s04-4-2"></a>
### 4.2 CNI 与 IPAM

- 4.2.1 CNI 规范与插件调用流程 <a id="s04-4-2-1"></a> [DONE]
- 4.2.2 IPAM 地址分配 <a id="s04-4-2-2"></a> [DONE]
- 4.2.3 网络配置与 Pod sandbox <a id="s04-4-2-3"></a> [DONE]

<a id="s04-4-3"></a>
### 4.3 网络实现模式

- 4.3.1 Underlay 与 Overlay <a id="s04-4-3-1"></a> [DONE]
- 4.3.2 VXLAN 与路由模式 <a id="s04-4-3-2"></a> [DONE]
- 4.3.3 常见 CNI 插件对比 <a id="s04-4-3-3"></a> [DONE]

<a id="s04-5"></a>
## 5 服务、入口与现代集群数据面

<a id="s04-5-1"></a>
### 5.1 Service 与负载均衡

- 5.1.1 Service 模型 <a id="s04-5-1-1"></a> [DONE]
- 5.1.2 ClusterIP、NodePort 与 LoadBalancer <a id="s04-5-1-2"></a> [DONE]
- 5.1.3 Endpoint 与 EndpointSlice <a id="s04-5-1-3"></a> [DONE]
- 5.1.4 kube-proxy iptables 模式 <a id="s04-5-1-4"></a> [DONE]
- 5.1.5 kube-proxy IPVS 模式 <a id="s04-5-1-5"></a> [DONE]
- 5.1.6 eBPF 与 Service 负载均衡 <a id="s04-5-1-6"></a> [DONE]

<a id="s04-5-2"></a>
### 5.2 服务发现与入口

- 5.2.1 CoreDNS 与服务发现 <a id="s04-5-2-1"></a> [DONE]
- 5.2.2 Ingress <a id="s04-5-2-2"></a> [DONE]
- 5.2.3 Gateway API <a id="s04-5-2-3"></a> [DONE]

<a id="s04-5-3"></a>
### 5.3 网络策略与集群数据面

- 5.3.1 NetworkPolicy 模型 <a id="s04-5-3-1"></a> [DONE]
- 5.3.2 默认隔离与规则语义 <a id="s04-5-3-2"></a> [DONE]
- 5.3.3 CNI 对网络策略的实现 <a id="s04-5-3-3"></a> [DONE]
- 5.3.4 eBPF 与集群网络可观测性 <a id="s04-5-3-4"></a> [DONE]

<a id="s04-6"></a>
## 6 Kubernetes 存储抽象与准入策略

<a id="s04-6-1"></a>
### 6.1 存储抽象

- 6.1.1 Volume 类型 <a id="s04-6-1-1"></a> [DONE]
- 6.1.2 PV、PVC 与 StorageClass <a id="s04-6-1-2"></a> [DONE]
- 6.1.3 访问模式与回收策略 <a id="s04-6-1-3"></a> [DONE]
- 6.1.4 拓扑感知与调度约束 <a id="s04-6-1-4"></a> [DONE]

<a id="s04-6-2"></a>
### 6.2 CSI 与存储扩展

- 6.2.1 CSI 架构与组件 <a id="s04-6-2-1"></a> [DONE]
- 6.2.2 动态供给 <a id="s04-6-2-2"></a> [DONE]
- 6.2.3 存储快照与克隆 <a id="s04-6-2-3"></a> [DONE]
- 6.2.4 挂载与卸载流程 <a id="s04-6-2-4"></a> [DONE]

<a id="s04-6-3"></a>
### 6.3 准入与资源策略

- 6.3.1 认证与鉴权 <a id="s04-6-3-1"></a> [DONE]
- 6.3.2 RBAC <a id="s04-6-3-2"></a> [DONE]
- 6.3.3 准入控制 <a id="s04-6-3-3"></a> [DONE]
- 6.3.4 Mutating 与 Validating Webhook <a id="s04-6-3-4"></a> [DONE]
- 6.3.5 ResourceQuota 与 LimitRange <a id="s04-6-3-5"></a> [DONE]

## 学习出口

能解释一个 Pod 从提交到运行、从 Service 到后端 Pod 的完整链路，能定位常见调度、网络、存储与准入问题。

## 导航

[返回分类目录](../README.md) · [知识总目录](../../../README.md)
