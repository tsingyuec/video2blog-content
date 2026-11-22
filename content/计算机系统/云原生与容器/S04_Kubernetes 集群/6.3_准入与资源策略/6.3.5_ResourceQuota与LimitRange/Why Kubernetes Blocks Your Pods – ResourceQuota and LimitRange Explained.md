# Why Kubernetes Blocks Your Pods – ResourceQuota and LimitRange Explained

> 视频标题为英文，本文用中文整理。原片来自 YouTube 频道 TechOps tutorial，约 28 分钟，属于管理员（admin）级别的"集群治理"内容。

## 本讲要解决的核心问题（SCQA）

**背景**：我们已经学过两件事——命名空间（namespace）负责把集群里的资源**组织与隔开**；而 `requests` 与 `limits` 则在**容器级别**定义每个容器能用多少 CPU 和内存。到这里，我们控制的都还是"单个容器"。

**冲突**：可真正的难题是——当**多个团队共享同一个集群**时，谁来管"每个团队总共能用多少资源"？默认情况下，K8s **根本不控制一个团队（命名空间）能用的资源总量**。于是只要有一个团队部署应用时忘了写 limit，它就会疯狂占用 CPU 和内存、慢慢吃掉整个集群，把别人的应用拖垮——这就是所谓的**噪声邻居（noisy neighbor）问题**。

**疑问**：谁能控制每个团队能用多少资源？资源被用超了又会发生什么？

**回答（中心思想）**：K8s 提供了两组管理员级工具来把"容器级控制"升级为"团队级控制"：**ResourceQuota** 给命名空间设一道**总量预算**，**LimitRange** 给容器设**默认值与上下边界**，另外还能用**对象数量配额**限制一个团队能创建多少个 Pod、Service、LoadBalancer、PV。它们一旦生效，**超出范围的请求会在 API 层被直接拒绝**（`Forbidden`），Pod 连创建的机会都没有。

---

## 一、从"管容器"到"管团队"

视频先把前面的知识串起来（[【跳转到 00:50】](https://www.youtube.com/watch?v=fhYWxlbyNaA&t=50)）：

- **Namespaces**：帮助我们组织和隔离集群里的资源；
- **Requests & Limits**：定义**单个容器**能使用多少 CPU 和内存。

也就是说，到现在为止，我们控制的粒度是"**容器级**"。而当多个团队共用一个集群时，就必须把粒度提升到"**团队级**"——这正是本讲要补上的能力。

![从容器到团队：Namespaces → Requests & Limits → Team Control](assets/Why%20Kubernetes%20Blocks%20Your%20Pods%20–%20ResourceQuota%20and%20LimitRange%20Explained/00055.webp)

## 二、噪声邻居问题：为什么必须治理

先看问题是怎么发生的：一个共享集群里，某天某个团队部署应用时**没设任何 limit**。这个应用便大量占用 CPU 和内存，并分散到多个节点，**慢慢吃掉集群的大部分资源**（[【跳转到 02:07】](https://www.youtube.com/watch?v=fhYWxlbyNaA&t=127)）。

后果就是"**噪声邻居问题**"：**别人的应用跟着变慢、重要工作负载甚至起不来**，最糟的情况还会因为内存不足而**崩溃**。

![噪声邻居问题：一个不设 limits 的工作负载把整个集群拖下水](assets/Why%20Kubernetes%20Blocks%20Your%20Pods%20–%20ResourceQuota%20and%20LimitRange%20Explained/00102.webp)

为什么默认会这样？K8s 的开箱行为有三条（[【跳转到 02:41】](https://www.youtube.com/watch?v=fhYWxlbyNaA&t=161)）：

1. **命名空间只负责组织**——它把资源隔开，却**不限制**一个团队能用多少 CPU / 内存；
2. **命名空间层面没有总量控制**——一个团队可以一直创建负载，用掉集群的一大块；
3. **先来先得（First Come, First Consume）**——谁先建负载谁先拿到资源，于是一个应用可能占满节点容量，另一个应用就拿不到足够资源。

一句话总结：**K8s 不会自动拦住这些行为，想要控制就得自己配置。**

![K8s 默认行为：无命名空间限制、无总量控制、先来先得](assets/Why%20Kubernetes%20Blocks%20Your%20Pods%20–%20ResourceQuota%20and%20LimitRange%20Explained/00161.webp)

## 三、两件治理工具：ResourceQuota 与 LimitRange

要控制跨团队的资源使用，K8s 给出两件工具（[【跳转到 03:31】](https://www.youtube.com/watch?v=fhYWxlbyNaA&t=211)）：

- **ResourceQuota**：可以理解为一个命名空间的**预算**，设定**总的 CPU 与内存上限**；即便再创建更多负载，也不能突破这条线；
- **LimitRange**：工作在**命名空间内部**，为 CPU、内存设定**默认值**，并定义**最小值与最大值**；开发者忘记声明资源时，K8s 会**自动补上默认值**。

![两件治理工具：ResourceQuota 管团队总量，LimitRange 管单个容器配置](assets/Why%20Kubernetes%20Blocks%20Your%20Pods%20–%20ResourceQuota%20and%20LimitRange%20Explained/00236.webp)

### 3.1 ResourceQuota = 命名空间的预算

命名空间本不该无限制地使用 CPU 或内存，于是我们用 ResourceQuota 给它设一条线。它有两方面作用：一是**限制该命名空间能消耗多少 CPU / 内存**；二是**阻止某个团队把资源全占光、影响别人**（[【跳转到 05:10】](https://www.youtube.com/watch?v=fhYWxlbyNaA&t=310)）。

视频举的例子是命名空间 `team-alpha`：CPU 上限 2 核、内存上限 4GB；此刻已用 1.5 核、约 1.8GB。**如果它再创建超过这条线的 Pod，K8s 会直接拒绝，Pod 压根不会启动**——这是命名空间级的**硬性控制**。

![ResourceQuota 像一份命名空间预算：team-alpha 上限 2 核 / 4GB，超出即拒绝](assets/Why%20Kubernetes%20Blocks%20Your%20Pods%20–%20ResourceQuota%20and%20LimitRange%20Explained/00310.webp)

### 3.2 LimitRange = 默认值与边界

ResourceQuota 工作在**命名空间级**，而 LimitRange 工作在 **Pod / 容器级**，管的是**每个容器能用多少 CPU 和内存**（[【跳转到 06:25】](https://www.youtube.com/watch?v=fhYWxlbyNaA&t=385)）。它最大的好处是：**开发者忘写 requests / limits 时，自动补上默认值**，从而没有容器会"裸奔"；同时它还设定**最小 / 最大值**，避免出现"小得离谱"或"大得离谱"的配置。

规则会在**Pod 创建时**生效：K8s 检查请求量，必要时按规则调整，让一切落在**容器级的安全区间**内。

![LimitRange 为每个容器定义最小 / 默认 / 最大三个值，创建 Pod 时按规则套用](assets/Why%20Kubernetes%20Blocks%20Your%20Pods%20–%20ResourceQuota%20and%20LimitRange%20Explained/00360.webp)

## 四、不止 CPU 与内存：对象数量配额

需要控制的不只是 CPU 和内存，还包括**一个命名空间能创建多少"资源对象"**：例如 Pod 数量、Service 数量、LoadBalancer 数量、存储卷数量（[【跳转到 07:17】](https://www.youtube.com/watch?v=fhYWxlbyNaA&t=437)）。

为什么这很重要？因为像 **LoadBalancer** 这类资源会让云账单**飞快上涨**。与其只限制 CPU / 内存，不如顺手把"能创建多少个对象"也限住。

视频给的例子是：一个命名空间最多 **50 个 Pod、10 个 Service、1 个 LoadBalancer、5 个持久卷**；一旦有人想越线，K8s 就会拦截，从而**避免意外的云账单**。

![对象数量配额：限制 Pod、Service、LoadBalancer、PV 的数量，防止账单失控](assets/Why%20Kubernetes%20Blocks%20Your%20Pods%20–%20ResourceQuota%20and%20LimitRange%20Explained/00407.webp)

## 五、Requests/Limits 与 Quota/LimitRange 的区别

这是本讲最容易混淆、也最关键的一组对照（[【跳转到 08:06】](https://www.youtube.com/watch?v=fhYWxlbyNaA&t=486)）：

| 维度 | Requests & Limits | Quota & LimitRange |
| :--- | :--- | :--- |
| **作用范围** | 容器级 | 命名空间 / 团队级 |
| **谁来管** | 通常由**开发者**设置 | 通常由**集群管理员**设置 |
| **关注点** | 应用**怎么运行**（可能被杀、可能一直 Pending） | 跨团队的**整体资源控制** |
| **越界后果** | 影响运行行为 | **请求被彻底阻止**，Pod 根本不会被创建 |

用一句话记：**requests / limits 管"应用怎么跑"，quota / LimitRange 管"资源怎么在团队间分"。**

![行为 vs 治理：Requests/Limits 面向运行行为，Quota/LimitRange 面向团队治理](assets/Why%20Kubernetes%20Blocks%20Your%20Pods%20–%20ResourceQuota%20and%20LimitRange%20Explained/00461.webp)

## 六、实测：三个真实场景

视频在终端里演示三种场景（[【跳转到 08:56】](https://www.youtube.com/watch?v=fhYWxlbyNaA&t=536)）：

1. **ResourceQuota**：给命名空间设严格限制，再尝试部署需要更多资源的负载 → 被立即拦下；
2. **LimitRange**：设好默认值后，创建一个不写 CPU / 内存的 Pod → K8s 自动补上默认值；
3. **对象配额**：把 LoadBalancer 数量限制为 1，再尝试创建第二个 → 被拦下。

![演示总览：三种场景分别在真实 Kubernetes 里被实时拦截](assets/Why%20Kubernetes%20Blocks%20Your%20Pods%20–%20ResourceQuota%20and%20LimitRange%20Explained/00511.webp)

### 6.1 场景一：ResourceQuota 的硬限制

先创建命名空间 `team-alpha`，再 apply 一份 `resource-quota.yaml`（CPU 2 核、内存 4GB），describe 一下可以看到配额与当前用量（[【跳转到 10:18】](https://www.youtube.com/watch?v=fhYWxlbyNaA&t=618)）：

```bash
kubectl create namespace team-alpha
kubectl apply -f resource-quota.yaml
kubectl describe quota -n team-alpha
```

![describe quota：CPU=2、内存=4GB，当前用量为 0](assets/Why%20Kubernetes%20Blocks%20Your%20Pods%20–%20ResourceQuota%20and%20LimitRange%20Explained/00618.webp)

接着部署一个在配额内的应用（`small-app`），两个 Pod 正常运行。但视频特意演示了**最关键的一幕**：把 `replicas` 改成 5 ——**K8s 不会一次性全部失败**，而是"**能建几个就建几个，配额一到就拦住剩下的**"（[【跳转到 12:24】](https://www.youtube.com/watch?v=fhYWxlbyNaA&t=744)）。

查看 Deployment 会发现 **replica failure**，原因是 `failed create`；继续看 ReplicaSet，错误信息是 **`forbidden: exceeded quota`**——这就是真正的**执行点**：ReplicaSet 想创建 Pod，但 K8s 在 **API 层面**因为配额已用尽而拒绝（[【跳转到 14:12】](https://www.youtube.com/watch?v=fhYWxlbyNaA&t=852)）。

![describe rs：创建 Pod 被 API 层拒绝，forbidden / exceeded quota](assets/Why%20Kubernetes%20Blocks%20Your%20Pods%20–%20ResourceQuota%20and%20LimitRange%20Explained/00844.webp)

为了验证"配额满了就全拦"，视频先把配额填满（把 `small-app` 扩到 4 个副本，使 `request.cpu` 用满 2 核），然后再部署 `big-app`。结果**一个新 Pod 都起不来**，`kubectl get events` 里清清楚楚地写着 **`forbidden: exceeded quota`**（[【跳转到 17:31】](https://www.youtube.com/watch?v=fhYWxlbyNaA&t=1051)）。

![get events：新 Pod 创建被拒，forbidden / exceeded quota](assets/Why%20Kubernetes%20Blocks%20Your%20Pods%20–%20ResourceQuota%20and%20LimitRange%20Explained/01089.webp)

### 6.2 场景二：LimitRange 自动补默认值

新建命名空间 `team-beta`，apply 一份 `limitrange.yaml`（定义默认 request 与默认 limit）（[【跳转到 20:25】](https://www.youtube.com/watch?v=fhYWxlbyNaA&t=1225)）。然后创建一个**完全不写 `resources` 段**的 Pod：

```bash
kubectl apply -f no-resource.yaml
kubectl get pods no-resource-pod -n team-beta -o yaml
```

Pod 正常 Running。用 `-o yaml` 查看时会发现：Pod 上多了一条注解 **`kubernetes.io/limit-ranger`**，说明 **LimitRange 修改了这个 Pod**；而 `resources` 段里**自动出现了 request 和 limit**——尽管我们的 YAML 里从没写过它们（[【跳转到 22:17】](https://www.youtube.com/watch?v=fhYWxlbyNaA&t=1337)）。

![Pod 被 LimitRange 注入默认值：limit-ranger 注解 + 自动补上的 request/limit](assets/Why%20Kubernetes%20Blocks%20Your%20Pods%20–%20ResourceQuota%20and%20LimitRange%20Explained/01300.webp)

### 6.3 场景三：对象数量配额

最后把重点从 CPU / 内存挪到"**能创建多少资源**"。apply 一份 `object-quota.yaml`（限制 `service loadbalancer` 为 1）后，describe 可以看到 `service.loadbalancer` 上限为 1、当前用量为 0（[【跳转到 24:05】](https://www.youtube.com/watch?v=fhYWxlbyNaA&t=1445)）：

![describe 对象配额：service.loadbalancer 上限 1 / 用量 0](assets/Why%20Kubernetes%20Blocks%20Your%20Pods%20–%20ResourceQuota%20and%20LimitRange%20Explained/01420.webp)

随后：

- 先创建 `nginx` 部署并 `expose --type loadbalancer` → **成功**（在限额内）；
- 再创建 `nginx-2` 并 expose 为 LoadBalancer → 报错 **`Forbidden: exceeded quota`**（[【跳转到 25:45】](https://www.youtube.com/watch?v=fhYWxlbyNaA&t=1545)）。

describe quota 显示 `service.loadbalancer` 已用 1、上限 1。视频强调：**这跟性能无关，而是"控制与成本"**——正因为设了严格限制，K8s 才不再放行更多对象（[【跳转到 26:35】](https://www.youtube.com/watch?v=fhYWxlbyNaA&t=1595)）。

![对象配额生效：service.loadbalancer 已用 1 / 上限 1，第二个 LoadBalancer 被拒](assets/Why%20Kubernetes%20Blocks%20Your%20Pods%20–%20ResourceQuota%20and%20LimitRange%20Explained/01570.webp)

演示结束后，视频删除了 `team-alpha`、`team-beta` 两个命名空间完成清理（这些步骤是可选的）。

---

## 小结

- **问题**：多团队共享集群时，K8s 默认**不控制团队总量**，会出现**噪声邻居**——一个不设 limits 的工作负载拖垮所有人。
- **两件工具、两种粒度**：
  - **ResourceQuota** 管命名空间级的**总预算**（如 team-alpha 2 核 / 4GB），超出即拒绝创建；
  - **LimitRange** 管容器级的**默认值与边界**，忘写 `resources` 时自动补默认值。
- **还有对象数量配额**：限制 Pod、Service、LoadBalancer、PV 的数量，防止云账单失控。
- **执行点**：越界发生在 **API 层**——由 ReplicaSet / Deployment 发起的创建请求直接返回 `forbidden: exceeded quota`。
- **一组对照**：`requests/limits` 是**容器级、开发者设、影响运行行为**；`quota/LimitRange` 是**命名空间/团队级、管理员设、越界直接阻止创建**。
- **要点**：即便共享集群，也没有哪个团队能把资源全占光，而且"忘记配置"这类错误可以被自动兜底。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| Cluster Governance | 集群治理：在资源共享的前提下，用规则约束各团队能用多少资源 |
| Noisy Neighbor（噪声邻居） | 一个不设限的工作负载抢占资源，导致同集群其它应用变慢、起不来甚至崩溃 |
| ResourceQuota | 作用在命名空间的"预算"，限制其可用的 CPU / 内存总量（及对象数量） |
| LimitRange | 作用在容器 / Pod 的默认值与最小 / 最大值，为未声明资源的对象自动补默认值 |
| requests / limits | 容器级资源声明：启动预留量 / 运行时上限 |
| Object Quota（对象数量配额） | 限制命名空间能创建的 Pod、Service、LoadBalancer、PV 等对象个数 |
| `kubernetes.io/limit-ranger` | LimitRange 注入默认值时，写在 Pod 上的注解，表明该 Pod 被其修改过 |
| `forbidden: exceeded quota` | 配额被突破时 API Server 返回的拒绝错误，Pod 不会被创建 |
| First Come, First Consume | K8s 默认的"先来先得"资源分配逻辑 |
