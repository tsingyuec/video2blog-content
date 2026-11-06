# Kubernetes 集群架构与数据面

> 规则：每个章节通过 `/explore <关键词>` 查找对应主题的视频；每个 `- X.Y.Z` 条目产出 1~3 篇博客。
> 进度标记 `**【处理中】**` / `**【已完成】**` 与博客链接由 Maka 定时任务维护，规则见同目录 [AGENT_TASK.md](AGENT_TASK.md)。

## 第 1 章 集群架构与声明式模型

### 1.1 集群组件与职责
- 1.1.1 控制面组件与职责 **【已完成】** 📺 [k8s 数据流核心逻辑](1.1_集群组件与职责/1.1.1_控制面组件与职责/B站讲解k8s数据流核心底层逻辑.md) · 📺 [控制面四大组件详解](1.1_集群组件与职责/1.1.1_控制面组件与职责/Kubernetes Control Plane Components Explained.md)
- 1.1.2 节点组件与职责 **【已完成】** 📺 [工作节点三件套：kubelet、容器运行时与 kube-proxy](1.1_集群组件与职责/1.1.2_节点组件与职责/Kubernetes Worker Node Components Explained.md) · 📺 [kubelet 是节点上的宰相](1.1_集群组件与职责/1.1.2_节点组件与职责/Kubelet这样讲你应该能听懂了吧.md)
- 1.1.3 组件间通信与高可用基础 **【已完成】** 📺 [Kubernetes list-watch机制原理](1.1_集群组件与职责/1.1.3_组件间通信与高可用基础/Kubernetes list-watch机制原理.md) · 📺 [Kubernetes Leader Election 选举机制](1.1_集群组件与职责/1.1.3_组件间通信与高可用基础/Kubernetes Leader Election 选举机制.md)

### 1.2 声明式 API 与资源模型
- 1.2.1 期望状态与声明式 API **【已完成】** 📺 [K8S架构原则与对象设计：声明式系统](1.2_声明式 API 与资源模型/1.2.1_期望状态与声明式API/K8S架构原则与对象设计：声明式系统.md) · 📺 [别只会操作K8s：从声明式与控制器底层读懂分布式软件设计](1.2_声明式 API 与资源模型/1.2.1_期望状态与声明式API/别只会操作K8s：从声明式与控制器底层读懂分布式软件设计.md) · 📺 [什么是声明式：声明式vs命令式与k8s的选择](1.2_声明式 API 与资源模型/1.2.1_期望状态与声明式API/什么是声明式：声明式vs命令式与k8s的选择.md)
- 1.2.2 API 资源、GVK 与命名空间 **【已完成】** 📺 [Kubernetes API 中概念探究：Resource、Kind、Object 与 CRD](1.2_声明式 API 与资源模型/1.2.2_API资源GVK与命名空间/Kubernetes API 中概念探究：Resource、Kind、Object 与 CRD.md) · 📺 [API 组、版本、生命周期与弃用策略](1.2_声明式 API 与资源模型/1.2.2_API资源GVK与命名空间/Kubernetes API Fundamentals You Must Know.md)
- 1.2.3 标签、选择器与 OwnerReference **【已完成】** 📺 [深入理解 K8s 的标签与标签选择器](1.2_声明式 API 与资源模型/1.2.3_标签选择器与OwnerReference/深入理解K8s的标签.md) · 📺 [Finalizer 与 OwnerReference：安全有序删除](1.2_声明式 API 与资源模型/1.2.3_标签选择器与OwnerReference/K8s EP15 Finalizers and Owner References.md)

### 1.3 etcd 与 API Server
- 1.3.1 etcd 与 Raft 共识 **【已完成】** 📺 [解读共识算法Raft（合集）](1.3_etcd 与 API Server/1.3.1_etcd与Raft共识/解读共识算法Raft（合集）.md) · 📺 [Deep Dive： etcd - Jingyi Hu, Google](1.3_etcd 与 API Server/1.3.1_etcd与Raft共识/Deep Dive： etcd - Jingyi Hu, Google.md)
- 1.3.2 watch 机制与事件分发 **【已完成】** 📺 [etcd Watch 机制源码剖析](1.3_etcd 与 API Server/1.3.2_watch机制与事件分发/etcd Watch 机制源码剖析.md) · 📺 [client-go Informer 源码剖析：FIFO 队列](1.3_etcd 与 API Server/1.3.2_watch机制与事件分发/client-go Informer 源码剖析：FIFO 队列.md)
- 1.3.3 kube-apiserver 请求流水线 **【已完成】** 📺 [kube-apiserver 请求处理流水线](1.3_etcd 与 API Server/1.3.3_kube-apiserver请求流水线/kube-apiserver 请求处理流水线.md) · 📺 [kube-apiserver 中的策略模式与装饰器模式](1.3_etcd 与 API Server/1.3.3_kube-apiserver请求流水线/kube-apiserver 中的策略模式与装饰器模式.md)

---

## 第 2 章 控制器与工作负载

### 2.1 控制器模式
- 2.1.1 Reconcile 循环 **【已完成】** 📺 [Kubernetes 控制器深潜：控制循环与事件协调](2.1_控制器模式/2.1.1_Reconcile循环/Kubernetes 控制器深潜：控制循环与事件协调.md) · 📺 [Reconcile 循环解剖：edge-driven 与 level-driven](2.1_控制器模式/2.1.1_Reconcile循环/Reconcile 循环解剖：edge-driven 与 level-driven.md)
- 2.1.2 Informer 与工作队列 **【已完成】** 📺 [Informer 机制：为什么控制器不直接访问 API Server](2.1_控制器模式/2.1.2_Informer与工作队列/Informer 机制：为什么控制器不直接访问 API Server.md) · 📺 [Informer 原理与使用：Indexer 与 SharedInformerFactory](2.1_控制器模式/2.1.2_Informer与工作队列/Informer 原理与使用：Indexer 与 SharedInformerFactory.md) · 📺 [WorkQueue 的实现：限流重试、去重与两阶段出队](2.1_控制器模式/2.1.2_Informer与工作队列/WorkQueue 的实现：限流重试、去重与两阶段出队.md)
- 2.1.3 控制器与期望状态收敛 **【已完成】** 📺 [Kubernetes 自愈能力的设计原理](2.1_控制器模式/2.1.3_控制器与期望状态收敛/The Magic of Kubernetes Self-Healing Capabilities.md) · 📺 [Kubernetes 究竟如何工作：从愿望到收敛](2.1_控制器模式/2.1.3_控制器与期望状态收敛/How Kubernetes Actually Works（Desired State, Reconciled）.md)

### 2.2 工作负载控制器
- 2.2.1 Deployment 与 ReplicaSet **【已完成】** 📺 [K8S-Deployment的设计与实现](2.2_工作负载控制器/2.2.1_Deployment与ReplicaSet/K8S-Deployment的设计与实现.md) · 📺 [K8S-ReplicaSet实现详解](2.2_工作负载控制器/2.2.1_Deployment与ReplicaSet/K8S-ReplicaSet实现详解.md)
- 2.2.2 StatefulSet **【已完成】** 📺 [StatefulSet 运行机制详解](2.2_工作负载控制器/2.2.2_StatefulSet/StatefulSet运行机制详解.md) · 📺 [Pod 控制器：StatefulSet 与无头服务](2.2_工作负载控制器/2.2.2_StatefulSet/Pod控制器StatefulSet与无头服务.md)
- 2.2.3 DaemonSet **【已完成】** 📺 [K8s原生技术之DaemonSet控制器详解](2.2_工作负载控制器/2.2.3_DaemonSet/K8s原生技术之DaemonSet控制器详解.md) · 📺 [Pod控制器-DaemonSet](2.2_工作负载控制器/2.2.3_DaemonSet/Pod控制器-DaemonSet.md)
- 2.2.4 Job 与 CronJob **【已完成】** 📺 [B站最清晰讲解：掌握 k8s - Job 控制器](2.2_工作负载控制器/2.2.4_Job与CronJob/B站最清晰讲解,掌握k8s（kubernetes）-Job控制器.md) · 📺 [Kubernetes 原生技术之 CronJob 控制器详解](2.2_工作负载控制器/2.2.4_Job与CronJob/Kubernetes原生技术之CronJob控制器详解.md)

### 2.3 扩展控制面
- 2.3.1 CRD 与自定义资源 **【已完成】** 📺 [深度解析 K8s API 扩展：从 CRD 到独立 API Server](2.3_扩展控制面/2.3.1_CRD与自定义资源/深度解析K8s API扩展：从CRD到独立API Server.md) · 📺 [Kubernetes CRD Design for the Long Haul](2.3_扩展控制面/2.3.1_CRD与自定义资源/Kubernetes CRD Design for the Long Haul.md)
- 2.3.2 Operator 模式 **【已完成】** 📺 [Operator 的运行模型](2.3_扩展控制面/2.3.2_Operator模式/Operator 的运行模型.md) · 📺 [用 controller-runtime 编写 Kubernetes Operator](2.3_扩展控制面/2.3.2_Operator模式/用 controller-runtime 编写 Kubernetes Operator.md)
- 2.3.3 控制器与准入控制的协作 **【已完成】** 📺 [深入浅出 K8s 准入控制](2.3_扩展控制面/2.3.3_控制器与准入控制的协作/深入浅出 K8s 准入控制.md) · 📺 [用准入 Webhook 增强集群安全](2.3_扩展控制面/2.3.3_控制器与准入控制的协作/用准入 Webhook 增强集群安全.md) · 📺 [Kubebuilder 准入 Webhook 实战](2.3_扩展控制面/2.3.3_控制器与准入控制的协作/Kubebuilder 准入 Webhook 实战.md)

---

## 第 3 章 调度与节点执行

### 3.1 调度
- 3.1.1 调度框架 **【处理中】**
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
