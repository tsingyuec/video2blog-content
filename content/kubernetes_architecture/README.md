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
- 3.1.1 调度框架 **【已完成】** 📺 [kubernetes源码刨析专题-scheduler](3.1_调度/kubernetes源码刨析专题-scheduler.md)
- 3.1.2 过滤与打分 **【已完成】** 📺 [调度器过滤与打分全流程](3.1_调度/3.1.2_过滤与打分/How Does the Kubernetes Scheduler Pick a Node.md) · 📺 [谓词与优先级](3.1_调度/3.1.2_过滤与打分/How the Kubernetes scheduler works.md)
- 3.1.3 资源请求与节点可分配资源 **【已完成】** 📺 [Kubernetes resource requests and limits：CPU throttling、OOMKilled 与 QoS 类](3.1_调度/3.1.3_资源请求与节点可分配资源/Kubernetes resource requests and limits：CPU throttling、OOMKilled 与 QoS 类.md) · 📺 [Kubernetes 节点预留资源 system-reserved 详解](3.1_调度/3.1.3_资源请求与节点可分配资源/Kubernetes 节点预留资源 system-reserved 详解.md) · 📺 [k8s resources requests 和 limits及其在 cgroup 中的配置](3.1_调度/3.1.3_资源请求与节点可分配资源/k8s resources requests 和 limits及其在 cgroup 中的配置.md)
- 3.1.4 亲和与反亲和 **【已完成】** 📺 [Pod 亲和与反亲和调度实战](3.1_调度/3.1.4_亲和与反亲和/Pod亲和性与反亲和性调度实战详解.md) · 📺 [节点选择器 vs 节点亲和 vs Pod 亲和](3.1_调度/3.1.4_亲和与反亲和/Kubernetes Node Selector vs Node Affinity vs Pod Affinity vs Taints & Tolerations.md)
- 3.1.5 污点与容忍 **【已完成】** 📺 [K8s 的污点与容忍](3.1_调度/3.1.5_污点与容忍/K8s的污点和容忍.md) · 📺 [容忍写法与 tolerationSeconds 实测](3.1_调度/3.1.5_污点与容忍/10-3 Taint&Toleration补充.md)
- 3.1.6 拓扑分布约束 **【已完成】** 📺 [Pod Topology Spread Constraints in Kubernetes](3.1_调度/3.1.6_拓扑分布约束/Pod Topology Spread Constraints in Kubernetes.md) · 📺 [Kubernetes Scheduling - Topology Spread Constraints](3.1_调度/3.1.6_拓扑分布约束/Kubernetes Scheduling - Topology Spread Constraints.md)
- 3.1.7 优先级与抢占 **【已完成】** 📺 [Kubernetes Priority Classes - The Secret to Efficient Resource Management](3.1_调度/3.1.7_优先级与抢占/Kubernetes Priority Classes - The Secret to Efficient Resource Management.md) · 📺 [Day 46 - Pod Priority And Preemption In Kubernetes](3.1_调度/3.1.7_优先级与抢占/Day 46 - Pod Priority And Preemption In Kubernetes.md)

### 3.2 节点执行
- 3.2.1 kubelet 职责 **【已完成】** 📺 [深度解析Kubernetes集群的核心组件Kubelet](3.2_节点执行/3.2.1_kubelet职责/深度解析Kubernetes集群的核心组件Kubelet.md) · 📺 [kubelet源码启动分析](3.2_节点执行/3.2.1_kubelet职责/kubelet源码启动分析.md)
- 3.2.2 Pod 生命周期 **【已完成】** 📺 [Pod 生命周期：从创建到流量接入的 12 个阶段](3.2_节点执行/3.2.2_Pod生命周期/Pod 生命周期：从创建到流量接入的 12 个阶段.md) · 📺 [Pod 的阶段、Init 容器与 Sidecar 容器](3.2_节点执行/3.2.2_Pod生命周期/Pod 的阶段、Init 容器与 Sidecar 容器.md)
- 3.2.3 探针 **【已完成】** 📺 [Kubernetes 三种探针实战：启动、就绪与存活的联动验证](3.2_节点执行/Kubernetes 三种探针实战：启动、就绪与存活的联动验证.md) · 📺 [Kubernetes 探针详解：存活、就绪与启动探针的契约](3.2_节点执行/Kubernetes 探针详解：存活、就绪与启动探针的契约.md)
- 3.2.4 CRI、CNI、CSI 的调用关系 **【已完成】** 📺 [Who's Running My Pods：CRI 深潜与 containerd 实战](3.2_节点执行/3.2.4_CRI、CNI、CSI的调用关系/Who's Running My Pods：CRI 深潜与 containerd 实战.md) · 📺 [OCI、CRI、CNI、CSI 与 runc 是什么](3.2_节点执行/3.2.4_CRI、CNI、CSI的调用关系/OCI、CRI、CNI、CSI 与 runc 是什么.md)
- 3.2.5 Static Pod **【已完成】** 📺 [静态Pod：kubelet直接管理的特殊Pod](3.2_节点执行/3.2.5_StaticPod/静态Pod：kubelet直接管理的特殊Pod.md) · 📺 [静态Pod深潜：侧门、镜像Pod与DaemonSet之争](3.2_节点执行/3.2.5_StaticPod/静态Pod深潜：侧门、镜像Pod与DaemonSet之争.md)
- 3.2.6 节点状态与心跳 **【已完成】** 📺 [kubelet 心跳为什么分成两套](3.2_节点执行/3.2.6_节点状态与心跳/Five Minutes to Evict：Inside the kubelet 18.md) · 📺 [Lease API 与节点心跳](3.2_节点执行/3.2.6_节点状态与心跳/Lease API ｜ Kubernetes.md) · 📺 [实测：停掉 kubelet 后多久 NotReady](3.2_节点执行/3.2.6_节点状态与心跳/Node NotReady Explained：Kubernetes Node Failure Simulation and Troubleshooting.md)

---

## 第 4 章 Pod 网络与 CNI

### 4.1 Pod 网络模型
- 4.1.1 每 Pod 一个 IP 的网络模型 **【已完成】** 📺 [Pod 之间为什么能直接通信？揭开 K8s 网络模型的底层](4.1_Pod 网络模型/Pod 之间为什么能直接通信？揭开 K8s 网络模型的底层.md)
- 4.1.2 pause 容器与网络命名空间 **【已完成】** 📺 [深入理解 docker 与 kubernetes（k8s）：Pause 容器](4.1_Pod 网络模型/4.1.2_pause容器与网络命名空间/深入理解docker和kubernetes（k8s）--19.pause容器.md) · 📺 [Linux 网络命名空间核心](4.1_Pod 网络模型/4.1.2_pause容器与网络命名空间/Linux网络命名空间核心 ｜ 虚拟网线、虚拟交换机、虚拟路由器.md)
- 4.1.3 Pod 内容器通信与共享网络栈 **【已完成】** 📺 [Pod 内容器通信与共享网络栈](4.1_Pod 网络模型/4.1.3_Pod内容器通信与共享网络栈/Pod 内容器通信与共享网络栈.md) · 📺 [Pod 中的容器是如何通信的](4.1_Pod 网络模型/4.1.3_Pod内容器通信与共享网络栈/Pod 中的容器是如何通信的.md)

### 4.2 CNI 与 IPAM
- 4.2.1 CNI 规范与插件调用流程 **【已完成】** 📺 [容器是怎么连上网的？CNI 原理一次讲透](4.2_CNI 与 IPAM/4.2.1_CNI规范与插件调用流程/容器是怎么连上网的？CNI 原理一次讲透.md) · 📺 [一条 ADD 命令，容器怎么就被接进网络了？CNI 调用链一次讲透](4.2_CNI 与 IPAM/4.2.1_CNI规范与插件调用流程/一条 ADD 命令，容器怎么就被接进网络了？CNI 调用链一次讲透.md) · 📺 [从零手写一个 CNI 插件](4.2_CNI 与 IPAM/4.2.1_CNI规范与插件调用流程/Kubernetes Networking： How to Write a CNI Plugin From Scratch.md)
- 4.2.2 IPAM 地址分配 **【已完成】** 📺 [一个 Pod 的 IP 到底是谁发的：CNI 与 host-local IPAM 全链路拆解](4.2_CNI 与 IPAM/4.2.2_IPAM地址分配/How Kubernetes Networking Actually Works： CNI & IPAM Explained.md) · 📺 [Calico 是怎么给 Pod 发 IP 的：IP 池、IP 块与 Block Affinity 实操](4.2_CNI 与 IPAM/4.2.2_IPAM地址分配/01. Calico IP Address Management (IPAM) for Kubernetes.md) · 📺 [Kubernetes 的 IP 都在哪：地址规划、IPv4 耗尽与应对策略](4.2_CNI 与 IPAM/4.2.2_IPAM地址分配/Kubernetes IP Management： From Core Concepts To Strategic Solutions.md)
- 4.2.3 网络配置与 Pod sandbox **【已完成】** 📺 [Pod的IP从哪来的CNI插件的秘密](4.2_CNI 与 IPAM/4.2.3_网络配置与Podsandbox/Pod的IP从哪来的CNI插件的秘密.md) · 📺 [kubernetes cni剖析](4.2_CNI 与 IPAM/4.2.3_网络配置与Podsandbox/kubernetes cni剖析.md)

### 4.3 网络实现模式
- 4.3.1 Underlay 与 Overlay **【已完成】** 📺 [为什么 Calico 不走 Overlay：Calico 源码深读](4.3_网络实现模式/4.3.1_Underlay与Overlay/为什么 Calico 不走 Overlay：Calico 源码深读.md) · 📺 [BGP 原生还是隧道封装：Calico 底层架构解密](4.3_网络实现模式/4.3.1_Underlay与Overlay/BGP 原生还是隧道封装：Calico 底层架构解密.md)
- 4.3.2 VXLAN 与路由模式 **【已完成】** 📺 [VXLAN 怎么把包套进 UDP：overlay 原理彻底讲透](4.3_网络实现模式/4.3.2_VXLAN与路由模式/VXLAN 怎么把包套进 UDP：overlay 原理彻底讲透.md) · 📺 [CNI 原理与 Calico VXLAN、BGP 双模式对比](4.3_网络实现模式/4.3.2_VXLAN与路由模式/CNI 原理与 Calico VXLAN、BGP 双模式对比.md)
- 4.3.3 常见 CNI 插件对比 **【已完成】** 📺 [Flannel、Calico、Cilium 到底怎么选？三大 CNI 的底层路线之争](4.3_网络实现模式/4.3.3_常见CNI插件对比/Flannel、Calico、Cilium 到底怎么选？三大 CNI 的底层路线之争.md) · 📺 [01·Cilium 是什么？把网络、安全与可观测全塞进 eBPF（Cilium 源码深读）](4.3_网络实现模式/4.3.3_常见CNI插件对比/01·Cilium 是什么？把网络、安全与可观测全塞进 eBPF（Cilium 源码深读）.md)

---

## 第 5 章 服务、入口与现代集群数据面

### 5.1 Service 与负载均衡
- 5.1.1 Service 模型 **【已完成】** 📺 [Service的含义和基本工作原理](5.1_Service 与负载均衡/Service的含义和基本工作原理.md)
- 5.1.2 ClusterIP、NodePort 与 LoadBalancer **【已完成】** 📺 [ClusterIP和NodePort类型的Service](5.1_Service 与负载均衡/5.1.2_ClusterIP、NodePort与LoadBalancer/ClusterIP和NodePort类型的Service.md) · 📺 [ExternalName和LoadBalancer类型的Service](5.1_Service 与负载均衡/5.1.2_ClusterIP、NodePort与LoadBalancer/ExternalName和LoadBalancer类型的Service.md) · 📺 [KubernetesService的ClusterIP是个假IP真相在这里](5.1_Service 与负载均衡/5.1.2_ClusterIP、NodePort与LoadBalancer/KubernetesService的ClusterIP是个假IP真相在这里.md)
- 5.1.3 Endpoint 与 EndpointSlice **【已完成】** 📺 [Endpoints 自动关联体系](5.1_Service 与负载均衡/5.1.3_Endpoint与EndpointSlice/66 Endpoints 自动关联体系.md) · 📺 [Endpoints 手动关联体系](5.1_Service 与负载均衡/5.1.3_Endpoint与EndpointSlice/67 Endpoints 手动关联体系.md) · 📺 [EndpointSlice：Service 如何扩展到数千个 Pod](5.1_Service 与负载均衡/5.1.3_Endpoint与EndpointSlice/EndpointSlices — how Kubernetes Services scale to thousands of pods without falling over.md)
- 5.1.4 kube-proxy iptables 模式 **【已完成】** 📺 [kube-proxy iptables 模式深度解析](5.1_Service 与负载均衡/kube-proxy iptables 模式深度解析.md)
- 5.1.5 kube-proxy IPVS 模式 **【已完成】** 📺 [揭秘IPVS：一张连接表凭什么扛住四层负载均衡](5.1_Service 与负载均衡/5.1.5_kube-proxy IPVS模式/揭秘IPVS：一张连接表凭什么扛住四层负载均衡.md) · 📺 [手工实现kubernetes下ipvs模式的转发](5.1_Service 与负载均衡/5.1.5_kube-proxy IPVS模式/手工实现kubernetes下ipvs模式的转发.md)
- 5.1.6 eBPF 与 Service 负载均衡 **【已完成】** 📺 [eBPF services：把 kube-proxy 换掉](5.1_Service 与负载均衡/5.1.6_eBPF与Service负载均衡/eBPF services：把 kube-proxy 换掉.md) · 📺 [为什么能干掉 kube-proxy：服务负载均衡的全局设计](5.1_Service 与负载均衡/5.1.6_eBPF与Service负载均衡/为什么能干掉 kube-proxy：服务负载均衡的全局设计.md)

### 5.2 服务发现与入口
- 5.2.1 CoreDNS 与服务发现 **【已完成】** 📺 [CoreDNS 深潜：插件链与 Kubernetes 插件](5.2_服务发现与入口/5.2.1_CoreDNS与服务发现/CoreDNS 深潜：插件链与 Kubernetes 插件.md) · 📺 [Kubernetes DNS 深潜：解析、缓存与服务发现](5.2_服务发现与入口/5.2.1_CoreDNS与服务发现/Kubernetes DNS 深潜：解析、缓存与服务发现.md)
- 5.2.2 Ingress **【已完成】** 📺 [K8s网关生态标准Ingress](5.2_服务发现与入口/5.2.2_Ingress/K8s网关生态标准Ingress.md) · 📺 [Kubernetes Ingress Explained Completely For Beginners](5.2_服务发现与入口/5.2.2_Ingress/Kubernetes Ingress Explained Completely For Beginners.md)
- 5.2.3 Gateway API **【已完成】** 📺 [K8s 退役 Ingress NGINX：Gateway API 用三层接手流量路由](5.2_服务发现与入口/5.2.3_Gateway API/K8s正式退役Ingress NGINX——Gateway API接管流量路由的3层设计.md) · 📺 [谐云课堂：Gateway API 全面解析（Envoy/NGINX/Traefik 实战）](5.2_服务发现与入口/5.2.3_Gateway API/【谐云课堂第二十三期】Gateway API全面解析.md) · 📺 [Gateway API 原理与实操：从 Ingress 的两个硬伤讲起](5.2_服务发现与入口/5.2.3_Gateway API/You will never forget Kubernetes Gateway API after watching this.md)

### 5.3 网络策略与集群数据面
- 5.3.1 NetworkPolicy 模型 **【已完成】** 📺 [NetworkPolicy 模型：默认全通的四层身份网络](5.3_网络策略与集群数据面/5.3.1_NetworkPolicy模型/NetworkPolicy 模型：默认全通的四层身份网络.md) · 📺 [NetworkPolicy 基本介绍：pod 间通信与对象结构](5.3_网络策略与集群数据面/5.3.1_NetworkPolicy模型/NetworkPolicy 基本介绍：pod 间通信与对象结构.md)
- 5.3.2 默认隔离与规则语义 **【已完成】** 📺 [NetworkPolicy 的四条基础规则](5.3_网络策略与集群数据面/5.3.2_默认隔离与规则语义/NetworkPolicy 的四条基础规则.md) · 📺 [NetworkPolicy 对象详解：podSelector 与 policyTypes](5.3_网络策略与集群数据面/5.3.2_默认隔离与规则语义/NetworkPolicy 对象详解：podSelector 与 policyTypes.md)
- 5.3.3 CNI 对网络策略的实现 **【已完成】** 📺 [Calico 策略引擎：一条 NetworkPolicy 怎么被算出来](5.3_网络策略与集群数据面/5.3.3_CNI对网络策略的实现/Calico 策略引擎：一条 NetworkPolicy 怎么被算出来.md) · 📺 [Cilium 的 L4 NetworkPolicy 实现原理](5.3_网络策略与集群数据面/5.3.3_CNI对网络策略的实现/Cilium 的 L4 NetworkPolicy 实现原理.md)
- 5.3.4 eBPF 与集群网络可观测性 **【已完成】** 📺 [29·Hubble parser：把字节变成 Flow｜Cilium 源码深读（第五季）](5.3_网络策略与集群数据面/5.3.4_eBPF与集群网络可观测性/29·Hubble parser：把字节变成 Flow｜Cilium 源码深读（第五季）.md) · 📺 [30·Hubble Relay：多节点怎么拼成一张图｜Cilium 源码深读（第五季）](5.3_网络策略与集群数据面/5.3.4_eBPF与集群网络可观测性/30·Hubble Relay：多节点怎么拼成一张图｜Cilium 源码深读（第五季）.md)

---

## 第 6 章 Kubernetes 存储抽象与准入策略

### 6.1 存储抽象
- 6.1.1 Volume 类型 **【已完成】** 📺 [K8S 存储卷的类型与来源](<6.1_存储抽象/6.1.1_Volume类型/5.简单懂点K8S的存储(Volume／PV／PVC／StorageClass).md>) · 📺 [本地存储卷 emptyDir 与 hostPath](<6.1_存储抽象/6.1.1_Volume类型/B站最清晰讲解,掌握k8s(kubernetes)-本地存储volume卷[emptyDir、hostPath].md>)
- 6.1.2 PV、PVC 与 StorageClass **【已完成】** 📺 [持久卷Pv和Pvc](6.1_存储抽象/6.1.2_PV、PVC与StorageClass/持久卷Pv和Pvc.md) · 📺 [存储类-StorageClass](6.1_存储抽象/6.1.2_PV、PVC与StorageClass/存储类-StorageClass.md)
- 6.1.3 访问模式与回收策略 **【已完成】** 📺 [访问模式与回收策略：PV 的两组关键参数](6.1_存储抽象/6.1.3_访问模式与回收策略/访问模式与回收策略：PV 的两组关键参数.md) · 📺 [持久化存储实战：ReadWriteOnce 与回收策略](6.1_存储抽象/6.1.3_访问模式与回收策略/持久化存储实战：ReadWriteOnce 与回收策略.md)
- 6.1.4 拓扑感知与调度约束 **【已完成】** 📺 [本地持久卷：延迟绑定与拓扑感知](6.1_存储抽象/6.1.4_拓扑感知与调度约束/本地持久卷：延迟绑定与拓扑感知.md) · 📺 [存储分布调度：WaitForFirstConsumer 与拓扑分布约束](6.1_存储抽象/6.1.4_拓扑感知与调度约束/存储分布调度：WaitForFirstConsumer 与拓扑分布约束.md)

### 6.2 CSI 与存储扩展
- 6.2.1 CSI 架构与组件 **【已完成】** 📺 [kubernetes csi 剖析](<6.2_CSI 与存储扩展/6.2.1_CSI架构与组件/kubernetes csi剖析.md>) · 📺 [容器存储插件 CSI（上）](<6.2_CSI 与存储扩展/6.2.1_CSI架构与组件/容器存储插件CSI（上）.md>)
- 6.2.2 动态供给 **【已完成】** 📺 [动态存储类 StorageClass 动态供给实战](<6.2_CSI 与存储扩展/6.2.2_动态供给/动态存储类 StorageClass 动态供给实战.md>) · 📺 [Kubernetes StorageClass 动态卷供给详解](<6.2_CSI 与存储扩展/6.2.2_动态供给/Kubernetes StorageClass 动态卷供给详解.md>)
- 6.2.3 存储快照与克隆 **【已完成】** 📺 [Kubernetes Volume Snapshots Explained：Dynamic vs Pre-Provisioned Snapshots](<6.2_CSI 与存储扩展/6.2.3_存储快照与克隆/Kubernetes Volume Snapshots Explained：Dynamic vs Pre-Provisioned Snapshots.md>) · 📺 [Kubernetes CSI Volume Cloning Explained：Clone PVCs Without Starting From Scratch](<6.2_CSI 与存储扩展/6.2.3_存储快照与克隆/Kubernetes CSI Volume Cloning Explained：Clone PVCs Without Starting From Scratch.md>)
- 6.2.4 挂载与卸载流程 **【已完成】** 📺 [CSI 卷的挂载与卸载：从 CreateVolume 到 NodeUnpublishVolume](6.2_CSI 与存储扩展/6.2.4_挂载与卸载流程/CSI 卷的挂载与卸载：从 CreateVolume 到 NodeUnpublishVolume.md) · 📺 [卷是如何挂进容器的：挂载分层、传播与只读安全](6.2_CSI 与存储扩展/6.2.4_挂载与卸载流程/卷是如何挂进容器的：挂载分层、传播与只读安全.md)

### 6.3 准入与资源策略
- 6.3.1 认证与鉴权 **【已完成】** 📺 [Kubernetes 认证机制：X509 客户端证书、ServiceAccount 与 kubeconfig](<6.3_准入与资源策略/6.3.1_认证与鉴权/Kubernetes 认证机制：X509 客户端证书、ServiceAccount 与 kubeconfig.md>) · 📺 [Kubernetes 授权模式：Node、RBAC、ABAC 与 Webhook 的串联](<6.3_准入与资源策略/6.3.1_认证与鉴权/Kubernetes 授权模式：Node、RBAC、ABAC 与 Webhook 的串联.md>)
- 6.3.2 RBAC **【已完成】** 📺 [Kubernetes RBAC 权限控制详解](../kubernetes/blog/Kubernetes RBAC 权限控制详解.md)（复用已有博客）
- 6.3.3 准入控制 **【已完成】** 📺 [Kubernetes 准入控制器分类之旅](<6.3_准入与资源策略/6.3.3_准入控制/Kubernetes 准入控制器分类之旅.md>) · 📺 [准入控制器：API 请求链上的改写与校验](<6.3_准入与资源策略/6.3.3_准入控制/准入控制器：API 请求链上的改写与校验.md>)
- 6.3.4 Mutating 与 Validating Webhook **【已完成】** 📺 [准入链上的改写与拦截](<6.3_准入与资源策略/6.3.4_Mutating与ValidatingWebhook/Mutating 与 Validating Webhook：谁先改写，谁后拦截.md>) · 📺 [Webhook 三种类型与开发路径](<6.3_准入与资源策略/6.3.4_Mutating与ValidatingWebhook/Webhook 三种类型与开发路径.md>)
- 6.3.5 ResourceQuota 与 LimitRange **【已完成】** 📺 [K8s的资源配额与限制](6.3_准入与资源策略/6.3.5_ResourceQuota与LimitRange/K8s的资源配额与限制.md) · 📺 [Why Kubernetes Blocks Your Pods – ResourceQuota and LimitRange Explained](<6.3_准入与资源策略/6.3.5_ResourceQuota与LimitRange/Why Kubernetes Blocks Your Pods – ResourceQuota and LimitRange Explained.md>)
