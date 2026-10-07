# 系列：40 天 Kubernetes 挑战 / CKA 全课程

- **平台**：YouTube
- **作者**：Tech Tutorials with Piyush（Piyush Sachdeva）
- **来源**：[Day 0/40 - FREE Kubernetes Full Course (CKA) + 路线图](https://www.youtube.com/watch?v=6_gMoe7Ik8k)（频道 [Tech Tutorials with Piyush](https://www.youtube.com/@TechTutorialswithPiyush)）
- **视频数**：40+（本目录持续整理中，当前收录 Day 0–Day 10）
- **主题**：以 2024/2025 版 CKA 考纲为线索，从容器与 Docker 基础讲起，逐步覆盖 Kubernetes 架构、集群搭建、Pod 与工作负载、调度、网络、存储、权限与排障等，配大量动手演示（hands-on demo）与「#40daysofkubernetes」挑战任务。

## 视频索引

| 视频键 | 讲次 · 标题 | 时长 | 博客 | 原视频 |
| --- | --- | ---: | --- | --- |
| 6_gMoe7Ik8k | Day 0 · 课程介绍与路线图 | 12:12 | [博客](blog/Day00_课程介绍与路线图.md) | [YouTube](https://www.youtube.com/watch?v=6_gMoe7Ik8k) |
| ul96dslvVwY | Day 1 · Docker 基础 | 25:21 | [博客](blog/Day01_Docker基础.md) | [YouTube](https://www.youtube.com/watch?v=ul96dslvVwY) |
| nfRsPiRGx74 | Day 2 · Docker 化项目 | 34:52 | [博客](blog/Day02_Docker化项目.md) | [YouTube](https://www.youtube.com/watch?v=nfRsPiRGx74) |
| ajetvJmBvFo | Day 3 · Docker 多阶段构建 | 19:00 | [博客](blog/Day03_Docker多阶段构建.md) | [YouTube](https://www.youtube.com/watch?v=ajetvJmBvFo) |
| lXs1VCWqIH4 | Day 4 · 为什么需要 Kubernetes | 08:30 | [博客](blog/Day04_为什么需要Kubernetes.md) | [YouTube](https://www.youtube.com/watch?v=lXs1VCWqIH4) |
| SGGkUCctL4I | Day 5 · 什么是 Kubernetes 与架构 | 25:15 | [博客](blog/Day05_什么是Kubernetes与架构.md) | [YouTube](https://www.youtube.com/watch?v=SGGkUCctL4I) |
| RORhczcOrWs | Day 6 · 用 Kind 搭建多节点集群 | 27:08 | [博客](blog/Day06_用Kind搭建多节点集群.md) | [YouTube](https://www.youtube.com/watch?v=RORhczcOrWs) |
| _f9ql2Y5Xcc | Day 7 · Pod 与命令式/声明式 | 33:20 | [博客](blog/Day07_Pod与命令式声明式.md) | [YouTube](https://www.youtube.com/watch?v=_f9ql2Y5Xcc) |
| oe2zjRb51F0 | Day 8 · Deployment、RC 与 ReplicaSet | 35:06 | [博客](blog/Day08_Deployment与ReplicaSet.md) | [YouTube](https://www.youtube.com/watch?v=oe2zjRb51F0) |
| tHAQWLKMTB0 | Day 9 · Service（ClusterIP/NodePort/LB/ExternalName） | 46:46 | [博客](blog/Day09_Service网络服务.md) | [YouTube](https://www.youtube.com/watch?v=tHAQWLKMTB0) |
| yVLXIydlU_0 | Day 10 · Namespace 命名空间 | 27:55 | [博客](blog/Day10_Namespace命名空间.md) | [YouTube](https://www.youtube.com/watch?v=yVLXIydlU_0) |

## 内容速览

- **Day 0**：课程介绍、Discord 社区、每周直播答疑、#40daysofkubernetes 挑战规则与 40 讲路线图。
- **Day 1**：容器与 Docker 基础——容器解决了什么问题、与虚拟机的区别、Docker 架构与工作流、常用命令。
- **Day 2**：把一个示例应用 Docker 化——写 Dockerfile、build/tag/push/pull/run、进入容器排障。
- **Day 3**：多阶段构建——`installer` + `deployer` 两阶段，只复制构建产物，把镜像从 200MB 瘦下来；排障三板斧。
- **Day 4**：为什么需要 Kubernetes——手动运维容器的痛点，以及「Kubernetes 不是万能的」这一反面提醒。
- **Day 5**：Kubernetes 架构——控制平面（API Server / etcd / Scheduler / Controller Manager）与工作节点（kubelet / kube-proxy），并串起一次请求的完整旅程。
- **Day 6**：用 Kind 搭本地集群——单节点、`--config` 多节点、`kubectl config use-context` 切换，以及 CKA 查文档技巧。
- **Day 7**：Pod 与两种创建方式——命令式 vs 声明式、YAML 基础、四个顶层字段、`--dry-run=client -o yaml`、`ImagePullBackOff` 排障。
- **Day 8**：Deployment 与 ReplicaSet——控制器自动愈合与保副本；RC→RS→Deployment 三者关系（Deployment 管 RS，RS 管 Pod）；`replicas` 期望状态；扩缩容三法（apply / edit / scale）；滚动更新与 `rollout history`/`undo`。
- **Day 9**：Service 网络抽象——为会变化的 Pod IP 提供稳定入口与负载均衡；四种类型（ClusterIP / NodePort / LoadBalancer / ExternalName）；NodePort 三端口（nodePort/port/targetPort）；Endpoints；Kind 的 `extraPortMappings`。
- **Day 10**：Namespace——集群内的逻辑隔离与权限/环境隔离；默认 `default`、系统 `kube-system`；`-n` 指定与同名共存；跨命名空间需用 FQDN（`<服务名>.<命名空间>.svc.cluster.local`），同命名空间才可用短主机名。

## 核心结论

- **先容器、后编排**：Day 1–3 打牢 Docker 基础，Day 4 起再进入 Kubernetes，学习路径循序渐进。
- **架构一句话**：集群 = 控制平面（发号施令）+ 工作节点（真正干活）；**所有组件都只与 API Server 交互**，也只有 API Server 能读写 etcd。
- **环境**：整个系列不使用云托管服务，用 **Kind** 在本机搭可反复练习、可排障的集群；context 切换是 CKA 每道题的第一步。
- **创建资源两条路都要会**：命令式（`kubectl run`）适合排障与临时操作；声明式（YAML + `apply`）适合生产、CI/CD 与 GitOps。
- **工作负载靠控制器托管**：Pod 必须由 ReplicaSet/Deployment 等控制器管理；Deployment 负责滚动更新与回滚，ReplicaSet 负责保副本与按标签纳管 Pod。
- **网络用 Service 解耦**：Pod IP 会变，Service 提供固定入口与负载均衡；对外用 NodePort/负载均衡器，对内用 ClusterIP。
- **隔离用 Namespace，跨空间名字用 FQDN**：同命名空间用短主机名，跨命名空间必须写完整域名。

> 说明：本系列中间结果（视频、抽帧、字幕、图文稿）位于 `_work/kubernetes_cursor/`；`content/kubernetes_cursor/` 只收录博客与配图。
