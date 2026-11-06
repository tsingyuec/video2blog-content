# Kubernetes Operator 的运行模型：一条对象变化如何变成一次可靠调谐

## 本讲要解决的核心问题（SCQA）

**背景**：你已经会写 CRD、会写控制器代码，知道「监听 CR、然后创建 Deployment、Service」这套套路。照着教程跑一遍，通常都能成功。

**冲突**：可这套写法一旦上线就会露馅——事件会重复投递，watch 会断线，进程会在执行到一半时重启，用户会手工改掉子资源，外部 API 还可能超时。一个「事件一响就按顺序做事」的脚本，根本扛不住这些现实。

**疑问**：那一个能在生产里活下来的 Operator，到底是怎么运转的？一条对象变化，是怎样被一步步变成一次「可靠」的调谐的？

**回答（中心思想）**：成熟的 Operator 保存的不是「事件」，而是**声明式意图**，再通过一个持续运行的 `Reconcile` 循环不断把现实推向期望状态。围绕这个循环，controller-runtime 提供了一整套基础设施：`Manager` 管生命周期、`Scheme` 管类型映射、`Cache` 提供本地视图、`Watch` 把变化映射成调谐键、`WorkQueue` 负责去重与限速、`Client` 划清读写边界、`OwnerReference`/`Finalizer` 表达资源关系，而可观测性与选主让 Operator 本身变得可运营。下面我们把这台机器一层层拆开。

> 本讲基于 B 站视频《Kubernetes 进阶 15｜Operator 的运行模型》（BV14LKV6wEpR，约 8 分钟）整理。

---

## 一、Operator 不是事件触发脚本

很多人第一次写 Operator，会把它理解成一个「事件触发脚本」：监听到 CR 创建事件，就按顺序创建 Deployment 和 Service；监听到删除事件，就依次删掉它们。这个版本**能演示，却扛不住生产**（[【跳转到 00:00】](https://www.bilibili.com/video/BV14LKV6wEpR/?t=0)）：

- 事件会**重复**投递；
- `watch` 会**断线**，漏掉变化；
- 进程会在执行到一半时**重启**，留下半成品状态；
- 用户会**手工修改**子资源，让现实偏离；
- 外部 API 也可能**超时**。

关键区别在于「保存的是什么」：

| 维度 | 一次性脚本 | Operator |
| :--- | :--- | :--- |
| 输入 | 事件 = 命令 | CR = 期望状态 |
| 中断后 | 执行到一半难恢复 | 每次重读当前事实 |
| 重复执行 | 容易产生副作用 | 幂等地持续修正 |
| 触发来源 | 只靠单次事件 | 事件 + 周期重同步 |

Operator 保存的是**声明式意图**，并靠**持续 reconcile** 修正偏差。所以它不依赖「某一次事件不丢」，而是接受「信号可能重复、丢失、乱序」，仍然把系统推向期望状态。（见下图：左侧是"事件=命令"的脚本思维，右侧是"CR=期望状态"的 Operator 思维。）

![Operator 与一次性脚本的对比：脚本把事件当命令，Operator 把 CR 当期望状态](assets/Operator%20的运行模型/00025.webp)

---

## 二、进程骨架：Manager 统一管理共同生命周期

`Manager` 是控制器进程的**总装配层**。它读取集群配置，创建共享的 cache 和 client，注册一个或多个 controller、Webhook、健康检查和指标服务，并统一处理：启动、leader election 与优雅退出（[【跳转到 00:25】](https://www.bilibili.com/video/BV14LKV6wEpR/?t=25)、[【跳转到 00:50】](https://www.bilibili.com/video/BV14LKV6wEpR/?t=50)）。

一个容易被忽略的细节：**Manager 的 cache 没有完成初次同步之前，不应该让依赖缓存的 worker 开始处理**，否则第一次 `reconcile` 可能建立在不完整的视图上。

请注意，Manager **不包含具体业务调谐逻辑**——它解决的是「多个控制器重复需要的基础设施与生命周期」：配置、缓存、客户端、Webhook、健康检查、选主，全都共享统一的启动与停止边界。所以同一份 cache 可以被 Controller A、Controller B 共用，进程退出时也能一起干净地停下来。

![Manager 是控制器进程的总装配层：配置、缓存、客户端、Webhook、健康检查与选主共享统一的启动停止边界](assets/Operator%20的运行模型/00050.webp)

---

## 三、类型系统：Scheme 让 Go 对象对应 API 资源

`Scheme` 常被忽略，但它决定「进程能不能理解对象类型」（[【跳转到 01:15】](https://www.bilibili.com/video/BV14LKV6wEpR/?t=75)、[【跳转到 01:40】](https://www.bilibili.com/video/BV14LKV6wEpR/?t=100)）。

原因在于：Kubernetes API 在网络上传输的是带 `apiVersion` 和 `kind` 的 **JSON**，而你的控制器代码处理的是 **Go 结构体**。Scheme 保存的就是 `Group / Version / Kind` 与 Go 类型之间的映射，它同时让 client 知道「该请求哪个资源路径、怎样编码与解码」。

- **内置资源**（如 `apps/v1` 的 `Deployment{}`）和**自定义资源**（如 `platform.example.io/v1beta1` 的你的 CR）都要加入同一个 Scheme；
- 一旦**漏注册**，控制器甚至还没进入业务逻辑，就会因为「无法识别类型」而失败；
- **版本转换**（同一 Kind 的多个 Version 之间互转）同样依赖清晰的类型边界。

![Scheme 维护 Group/Version/Kind 与 Go 类型之间的映射，是序列化与客户端工作的基础](assets/Operator%20的运行模型/00100.webp)

---

## 四、本地视图：Cache 用 List/Watch 建立可查询镜像

控制器不会因为「每次调谐」就把所有读取都压到 API Server 上（[【跳转到 02:05】](https://www.bilibili.com/video/BV14LKV6wEpR/?t=125)）。`Cache` 的做法是：

1. 启动时先 **List** 建立一份对象快照；
2. 再用 **Watch** 持续接收变化，把快照更新到最新；
3. 通过 **Indexer** 支持按命名空间、名称或字段查询。

这样大多数 `Get`/`List` 都读本地缓存，换来吞吐与解耦。多个控制器还可以**共享同一份缓存**。但代价是：**它不是实时数据库**。写入 API 成功后，新对象可能还没回流到 cache，生产逻辑必须**允许短暂陈旧**，不能假设「刚创建的子资源，下一次缓存读取就一定可见」；只有在少数要求强一致的场景，才直接使用 API reader 绕过缓存。

![Cache 用 List/Watch 建立可查询的本地镜像：以吞吐与解耦换取对短暂陈旧的容忍](assets/Operator%20的运行模型/00150.webp)

---

## 五、触发关系：Watch 把对象变化映射成调谐键

`Watch` 的职责**不是执行操作，而是把变化映射成一条「调谐请求」**（[【跳转到 02:30】](https://www.bilibili.com/video/BV14LKV6wEpR/?t=150)、[【跳转到 02:55】](https://www.bilibili.com/video/BV14LKV6wEpR/?t=175)）。控制器关注的**不只是主资源**，还包括它拥有或依赖的对象：

- **主资源**（比如 AppRelease）变化时，通常直接入队它自己的 `namespace/name`；
- **子资源**（Deployment、Service）变化时，可以通过 `ownerReference` 找回「拥有它的主资源」，再把主资源入队；
- **外部配置或跨命名空间依赖**，则需要显式地写 `map function` 或建立索引关系。

`Predicate` 可以过滤掉无意义的更新（比如只改了 `status` 的更新不再触发调谐），但**过滤过度会让真实偏差失去触发**。因此即便没有事件，Operator 还应保留**周期性 requeue 或重新同步**，作为兜底的恢复机会。

![Watch 把主资源、子资源与外部依赖的变化统一映射为 reconcile request（namespace/name 键）](assets/Operator%20的运行模型/00175.webp)

---

## 六、可靠调度：WorkQueue 合并、限速并重试对象键

`WorkQueue` 位于「事件」和「worker」之间（[【跳转到 03:20】](https://www.bilibili.com/video/BV14LKV6wEpR/?t=200)、[【跳转到 03:45】](https://www.bilibili.com/video/BV14LKV6wEpR/?t=225)）。它传递的是「**需要检查谁**」，而不是「**必须执行什么**」——这是一个关键心态差别。

- 短时间内同一个对象产生多次变化时，队列会**去重与合并**，避免每个边沿事件都触发一次完整工作；
- worker 取出 `reconcile request`，执行结束后根据结果决定：**forget**（不再重试）、**立即 requeue**，还是**延迟重试**；
- 出错通常进入**指数退避**，防止外部依赖故障时形成「热循环」。

因此，**队列深度、处理时延和重试次数是 Operator 的核心运行指标**。如果代码「永远返回 error 却没有上限或告警」，就等于把失败隐藏成无休止的重试。

![WorkQueue 在事件与 worker 之间做去重、限速与重试：成功 Forget、错误 RateLimit、等待 Requeue](assets/Operator%20的运行模型/00225.webp)

---

## 七、核心合同：Reconcile 每次都从当前状态开始

`Reconcile` 是业务核心，但它的输入通常**只有 `namespace` 和 `name`**（[【跳转到 04:10】](https://www.bilibili.com/video/BV14LKV6wEpR/?t=250)、[【跳转到 04:35】](https://www.bilibili.com/video/BV14LKV6wEpR/?t=275)）。它是 **level-based**（基于水平）而非 edge-based（基于边沿）的：每一次都从「当前事实」重新出发，而不管上一次是怎么走到这里的。标准动作是：

1. **重新 Get 主资源**：`not found` 往往表示对象已被删除，可以直接结束；
2. **检查 `deletionTimestamp` 和 `finalizer`**，决定是否进入删除清理流程；
3. **构造期望对象**（Deployment、Service 等），与实际比较；
4. 用 **create / patch / update** 修正差异；
5. 所有步骤都应**可重入**：已经存在就更新，已经删除就不重复删除；操作外部资源要使用**稳定的幂等键**；
6. 最后更新 **status 和 conditions**，让用户知道「本次处理的是哪个 generation、失败在哪里」。

![Reconcile 是 level-based 的：Get 主资源 → 处理删除 → 构造期望 → 比较差异 → 幂等写入 → 更新状态](assets/Operator%20的运行模型/00275.webp)

---

## 八、读写边界：Client 写 API，状态与对象分开更新

controller-runtime 的默认 `Client` 通常是「**从 cache 读、直接向 API Server 写**」（[【跳转到 05:00】](https://www.bilibili.com/video/BV14LKV6wEpR/?t=300)、[【跳转到 05:25】](https://www.bilibili.com/video/BV14LKV6wEpR/?t=325)）。这带来几条必须显式处理的边界：

- 创建子资源后要设置 `ownerReference`，既表达归属，也让垃圾回收与 watch 映射生效；
- 修改**共享对象**时应优先用 `patch`，缩小字段冲突面；用 `update` 遇到 `resourceVersion` 已变化会返回 **409**，需要重新读取再计算；
- **status 使用独立子资源更新**，避免业务状态写入时覆盖用户的 `spec`；
- **不要在同一个 reconcile 中假设所有写入组成一个事务**：任何一条成功、下一条失败，下一轮都必须能从中间状态恢复。

![Client 的读写边界：读取走 Shared Cache（可能短暂陈旧），写入直连 API Server，冲突需显式处理](assets/Operator%20的运行模型/00325.webp)

---

## 九、资源关系：OwnerReference 与 Finalizer 的边界

`ownerReference` **让子资源指向控制器拥有的主资源**，于是垃圾回收器可以在主资源删除后级联清理，controller watch 也能把子资源变化映射回主资源（[【跳转到 05:50】](https://www.bilibili.com/video/BV14LKV6wEpR/?t=350)、[【跳转到 06:15】](https://www.bilibili.com/video/BV14LKV6wEpR/?t=375)）。

但它有**明确边界**：

- 命名空间对象**不能**拥有集群级对象，也**不能**跨命名空间建立非法所有权；
- 外部资源——DNS 记录、数据库账号、云资源——**不在 Kubernetes 垃圾回收范围内**，它们必须由 **`finalizer`** 驱动**显式清理**，并记录外部资源标识；
- 删除流程要允许重试，但也要防止「永久 finalizer」把对象永久卡死。

一句话：**所有权适合表达 Kubernetes 对象的生命周期，不适合替代跨系统事务。**

![OwnerReference 负责集群内父子关系的级联删除；外部资源必须交给 Finalizer 显式清理](assets/Operator%20的运行模型/00375.webp)

---

## 十、可运营性：Operator 自己也必须可观测、可升级

一个「能创建资源」的控制器，还**不等于**一个「可运营」的 Operator（[【跳转到 06:15】](https://www.bilibili.com/video/BV14LKV6wEpR/?t=375)、[【跳转到 06:40】](https://www.bilibili.com/video/BV14LKV6wEpR/?t=400)）。业务资源 `Ready` 还不够，你还要能证明**控制循环本身是健康的**：

- **Conditions**：给用户可解释的持久状态；
- **Metrics**：reconcile 次数、错误率、队列深度、处理时延、外部 API 延迟；
- **Logs / Events**：只记录用户需要看到的离散变化，作为单次调谐的证据；
- **Leader 状态**：让多副本部署可被诊断。

升级控制器时，还要**验证旧版本的 status 和进行中的 finalizer**；若新版本无法理解旧状态，滚动升级期间两个版本交替接管，就可能产生**行为震荡**——这正是「API 兼容」必须与「控制器升级」一起设计的原因。

![Operator 自身的可观测性：Conditions（用户可解释状态）、Metrics（队列与调谐健康）、Logs/Events（单次证据）、Leader 状态](assets/Operator%20的运行模型/00400.webp)

---

## 十一、完整闭环：多副本靠选主提升可用性

部署多个 Operator 副本时，**Leader Election** 通常保证「同一组控制器只有一个活跃实例」，其余实例等待租约，在进程或节点故障后接管（[【跳转到 06:50】](https://www.bilibili.com/video/BV14LKV6wEpR/?t=410)、[【跳转到 07:30】](https://www.bilibili.com/video/BV14LKV6wEpR/?t=450)）。

它**提高的是进程可用性，而不是单键并发能力**——同一个对象不会被更多 worker 安全地并发处理。**水平扩展的收益取决于对象数量、队列分片和外部依赖**，而不是简单加副本。

至此，完整闭环浮现出来：**API 对象变化 → 进入 cache → watch 映射出对象键 → WorkQueue 去重限速 → worker 调用 reconcile → 写回子资源和 status → 新的变化再次触发。**

![完整闭环：一条变化从 API 到缓存、队列、调谐，再回到 API；多副本靠选主提升可用性，不提升单键并发](assets/Operator%20的运行模型/00450.webp)

---

## 小结

- **Operator 不是事件脚本**：它保存声明式意图，靠持续 reconcile 修正偏差，从而容忍事件重复、丢失、重启与并发。
- **Manager** 负责把 cache、client、多个 controller、Webhook、健康检查、选主统一装配，并管理共同的启动/停止生命周期。
- **Scheme** 把 Go 类型与 API 资源（Group/Version/Kind）互相映射，漏注册就进不了业务逻辑。
- **Cache** 用 List/Watch 建立可查询的本地镜像，用吞吐换解耦，代价是允许短暂陈旧。
- **Watch** 的职责是把变化映射成调谐键，主/子资源和外部依赖都要想办法映射回主资源。
- **WorkQueue** 在事件与 worker 之间去重、限速、重试；队列深度与重试次数是核心运行指标。
- **Reconcile** 是 level-based 的核心合同，每次都从当前事实重来，且必须幂等可重入。
- **Client** 划定读写边界：缓存读、直连写；冲突、status 子资源、非事务性写入都要显式处理。
- **OwnerReference** 表达集群内生命周期，**Finalizer** 负责外部资源的显式清理，两者边界分明。
- **可观测性与选主**让 Operator 自身可运营、可升级；选主提升可用性而非单键并发。

---

## 关键术语速查

| 术语 | 一句话解释 |
| :--- | :--- |
| Operator | 用「CRD + 控制器」把运维知识编码进集群、并持续把系统推向期望状态的一种模式 |
| CRD | CustomResourceDefinition，给 API Server 动态增加一种自定义资源类型 |
| controller-runtime | Kubernetes 官方的控制器开发库，提供 Manager、Client、Cache 等基础设施 |
| Manager | 控制器进程的总装配层，管理 cache/client/controller 等组件的共同生命周期 |
| Scheme | Group/Version/Kind 与 Go 类型之间的注册表，决定序列化与客户端行为 |
| Cache | 基于 List/Watch 建立的本地对象镜像，多数读取走它，允许短暂陈旧 |
| Watch | 把对象变化映射成「调谐请求」（namespace/name 键）的机制 |
| Predicate | 在入队前过滤无意义事件（如仅 status 变化）的钩子 |
| WorkQueue | 事件与 worker 之间的队列，负责去重、合并、限速与退避重试 |
| Reconcile | 控制器核心函数，level-based，输入只有 namespace/name，须幂等可重入 |
| OwnerReference | 表达子资源归属主资源，驱动级联垃圾回收与 watch 映射 |
| Finalizer | 删除前必须完成的钩子，用于显式清理外部资源并允许重试 |
| Leader Election | 多副本选主，保证同一组控制器只有一个活跃实例 |
