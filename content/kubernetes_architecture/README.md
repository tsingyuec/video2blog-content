# Kubernetes 集群架构与数据面

> 规则：每个章节通过 `/explore <关键词>` 查找对应主题的视频；每个 `- X.Y.Z` 条目产出 1~3 篇博客。
> 进度标记 `**【处理中】**` / `**【已完成】**` 与博客链接由 Maka 定时任务维护，规则见同目录 [AGENT_TASK.md](AGENT_TASK.md)。

## 第 1 章 集群架构与声明式模型

### 1.1 集群组件与职责
- 1.1.1 控制面组件与职责
- 1.1.2 节点组件与职责
- 1.1.3 组件间通信与高可用基础

### 1.2 声明式 API 与资源模型
- 1.2.1 期望状态与声明式 API
- 1.2.2 API 资源、GVK 与命名空间
- 1.2.3 标签、选择器与 OwnerReference

### 1.3 etcd 与 API Server
- 1.3.1 etcd 与 Raft 共识
- 1.3.2 watch 机制与事件分发
- 1.3.3 kube-apiserver 请求流水线

---

## 第 2 章 控制器与工作负载

### 2.1 控制器模式
- 2.1.1 Reconcile 循环
- 2.1.2 Informer 与工作队列
- 2.1.3 控制器与期望状态收敛

### 2.2 工作负载控制器
- 2.2.1 Deployment 与 ReplicaSet
- 2.2.2 StatefulSet
- 2.2.3 DaemonSet
- 2.2.4 Job 与 CronJob

### 2.3 扩展控制面
- 2.3.1 CRD 与自定义资源
- 2.3.2 Operator 模式
- 2.3.3 控制器与准入控制的协作

---

## 第 3 章 调度与节点执行

### 3.1 调度
- 3.1.1 调度框架
- 3.1.2 过滤与打分
- 3.1.3 资源请求与节点可分配资源
- 3.1.4 亲和与反亲和
- 3.1.5 污点与容忍
- 3.1.6 拓扑分布约束
- 3.1.7 优先级与抢占

### 3.2 节点执行
- 3.2.1 kubelet 职责
- 3.2.2 Pod 生命周期
- 3.2.3 探针
- 3.2.4 CRI、CNI、CSI 的调用关系
- 3.2.5 Static Pod
- 3.2.6 节点状态与心跳

---

## 第 4 章 Pod 网络与 CNI

### 4.1 Pod 网络模型
- 4.1.1 每 Pod 一个 IP 的网络模型
- 4.1.2 pause 容器与网络命名空间
- 4.1.3 Pod 内容器通信与共享网络栈

### 4.2 CNI 与 IPAM
- 4.2.1 CNI 规范与插件调用流程
- 4.2.2 IPAM 地址分配
- 4.2.3 网络配置与 Pod sandbox

### 4.3 网络实现模式
- 4.3.1 Underlay 与 Overlay
- 4.3.2 VXLAN 与路由模式
- 4.3.3 常见 CNI 插件对比

---

## 第 5 章 服务、入口与现代集群数据面

### 5.1 Service 与负载均衡
- 5.1.1 Service 模型
- 5.1.2 ClusterIP、NodePort 与 LoadBalancer
- 5.1.3 Endpoint 与 EndpointSlice
- 5.1.4 kube-proxy iptables 模式
- 5.1.5 kube-proxy IPVS 模式
- 5.1.6 eBPF 与 Service 负载均衡

### 5.2 服务发现与入口
- 5.2.1 CoreDNS 与服务发现
- 5.2.2 Ingress
- 5.2.3 Gateway API

### 5.3 网络策略与集群数据面
- 5.3.1 NetworkPolicy 模型
- 5.3.2 默认隔离与规则语义
- 5.3.3 CNI 对网络策略的实现
- 5.3.4 eBPF 与集群网络可观测性

---

## 第 6 章 Kubernetes 存储抽象与准入策略

### 6.1 存储抽象
- 6.1.1 Volume 类型
- 6.1.2 PV、PVC 与 StorageClass
- 6.1.3 访问模式与回收策略
- 6.1.4 拓扑感知与调度约束

### 6.2 CSI 与存储扩展
- 6.2.1 CSI 架构与组件
- 6.2.2 动态供给
- 6.2.3 存储快照与克隆
- 6.2.4 挂载与卸载流程

### 6.3 准入与资源策略
- 6.3.1 认证与鉴权
- 6.3.2 RBAC
- 6.3.3 准入控制
- 6.3.4 Mutating 与 Validating Webhook
- 6.3.5 ResourceQuota 与 LimitRange
