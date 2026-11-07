# Kubernetes 准入控制器分类之旅：四象限、请求生命周期与内置插件

## 本讲要解决的核心问题（SCQA）

**背景**：你在写 YAML、`kubectl apply` 的时候，已经默认了一个前提——集群里有一个 API Server，它负责把对象写进 etcd。你对「鉴权（谁能做这个操作）」也多少有些概念，RBAC 就是干这个的。

**冲突**：但真正上手后你会发现，光有「鉴权」远远不够。很多你想表达的规则，根本不在「谁能做什么」的层面：比如「每张 Pod 都得自动带上一个默认的 CPU 限额」「私有镜像不允许被别的租户白嫖」「CRD 得自动补默认值」。这些规则要**钻进对象内部**看字段才能判断，鉴权做不了。更麻烦的是，Kubernetes 里这类「准入控制」相关的插件**将近 20 个**，名字、触发时机、能改不能改各不相同，一上来很容易被绕晕。

**疑问**：这一堆「准入控制器」（admission controller）到底是什么？它们按什么标准分类？一次请求进来，它们又是在**哪一步**被调用、谁先谁后？

**回答（中心思想）**：准入控制器是 API Server 在把对象**写入 etcd 之前**插入的一批「拦截/改写插件」。它们可以沿两个维度看成一张**四象限表**——**「编译进 API Server 的内置插件 vs 外部 Webhook」×「变更型（mutating）vs 校验型（validating）」**；一次请求会先经过**变更阶段**（内置变更插件 + 变更 Webhook，串行改写对象），再做 schema 校验，最后经过**校验阶段**（内置校验插件 + 校验 Webhook），全部通过才落库。内置插件存在的意义是三件事——**安全、治理、配置**。

> 本讲基于 KubeCon/CNCF 视频《A Journey Through Kubernetes Admission Controller Taxonomy》（Morgan Bauer & Srinivas Brahmaroutu，IBM，约 32 分钟，[原视频](https://www.youtube.com/watch?v=rPLH1aTeJ5Q)）整理。视频按「历史 → 高层理解 → 代码 → 演示」四步展开，并带了一段基于 `agnhost` 镜像的 Webhook 现场演示。

---

## 一、准入控制器是什么：在对象落库之前拦截它

视频给出的第一句定义非常朴素：**准入控制器是一种在对象「进入」时、被持久化（persist）到数据库之前，对它做校验或修改的机制**（[【跳转到 00:55】](https://www.youtube.com/watch?v=rPLH1aTeJ5Q&t=55)）。

这句话里最关键的是「**持久化之前**」和「**数据库 = etcd**」。也就是说，准入控制器拦的是对象**写入 etcd 之前的最后一程**——请求还没真正落库，它就有机会改写或拦下。

![准入控制器的抽象定义与两种实现形式的区别](assets/Kubernetes%20准入控制器分类之旅/00055.webp)

从**技术实现**上看，两类准入控制器走的是两条不同的路：

- **编译进 API Server 的内置插件**（compiled-in）——直接实现 Go 语言里的 **validation interface（校验接口）**或 **mutation interface（变更接口）**，是和 API Server 编在一起的本地代码；
- **Webhook**——吃进一个 **`AdmissionReview`** 报文对象，读取其中的 **`AdmissionRequest`**，最后输出一个 **`AdmissionResponse`**。它是一个外部的 HTTP 回调。

### 它和普通控制器不是一回事

这一点最容易被初学的人混淆。视频特意做了对照（[【跳转到 05:05】](https://www.youtube.com/watch?v=rPLH1aTeJ5Q&t=305)）：

| | 控制器（controller） | 准入控制器（admission controller） |
| :--- | :--- | :--- |
| 本质 | 一个**控制循环**，持续 watch 集群状态 | 一次**同步的拦截**，作用在「进来的 API 调用」上 |
| 目标 | 把集群的**实际状态**收敛到**期望状态** | **治理、约束**「集群被怎么用」 |
| 时机 | 对象**早已落库**，之后再慢慢协调 | 对象**落库之前**就介入 |

一句话：普通控制器是「事后异步地纠偏」，准入控制器是「事前同步地改写或拦截」。

![准入控制器是 API Server 调用链上的拦截器，而非 watcher 型控制器](assets/Kubernetes%20准入控制器分类之旅/00305.webp)

视频还强调了一个细节：`MutatingAdmissionWebhook` 和 `ValidatingAdmissionWebhook` 本身就是**两个被编译进 API Server 的特殊控制器**。它们能响应创建、删除、修改等请求，但**不支持读请求（read）**——因为「读」根本不需要在落库前被拦截。

> 小结论：准入控制器只对「写」类操作（create / delete / modify / connect）生效，对「读」不生效。

## 二、从历史看分类：两个维度、四个象限

视频先讲历史，因为「分类」其实是从演化中长出来的（[【跳转到 01:45】](https://www.youtube.com/watch?v=rPLH1aTeJ5Q&t=105)）：

- **v0.9**：把对象校验**抽出来做成可插拔（pluggable）接口**，也为将来接入别的插件留了口子——这是准入控制器最早的样子；
- **v1.4**：第一批 **Webhook** 出现，但只能针对**特定的 API 类型**回调到特定的服务，远没有现在这么通用、可配置；
- **v1.9**：**通用 Webhook 与「变更（mutation）」被分离开**，从此配置可以作用于**任意对象**，也能正式地「修改进来的对象」；
- **v1.16 起**：今天的一切都收敛到 **`v1`** 这个稳定版本（不再是 alpha 或 v1beta），覆盖了当前大多数仍受支持的版本。

历史理清后，真正好记的是那个「**Punnett square（旁氏表 / 四象限）**」式的分类法（[【跳转到 03:50】](https://www.youtube.com/watch?v=rPLH1aTeJ5Q&t=230)）。它有**两条轴**：

- 轴一：**它是编译进 API Server 的内置插件，还是外部 Webhook？**
- 轴二：**它是校验型（validating），还是变更型（mutating）？**

两条轴一交叉，就是四类：

![两个维度交叉出的四类准入控制器](assets/Kubernetes%20准入控制器分类之旅/00230.webp)

| | **校验型（Validating）** | **变更型（Mutating）** |
| :--- | :--- | :--- |
| **内置（Built-in）** | 最早的一批校验插件 | 内置变更插件 |
| **Webhook** | 最早用于「校验允许的镜像」 | 对 **CRD** 最有用 |

四个象限里各有值得记的代表：

- **内置校验**：是最早、最成熟的一类；
- **内置变更**：典型是 **PodPresets**——它让用户写一份配置，就能在 Pod 进来时批量修改它（后文第六节展开）；
- **校验 Webhook**：最早的一批用来**校验「允许使用的镜像」**；
- **变更 Webhook**：视频认为这是「最有意思」的一类，因为**对于 CRD，它是唯一能同时做校验和默认值（defaulting）的手段**。也正因为如此，Kubernetes 自身并不内置针对 CRD 的变更插件，只能靠 Webhook——官方连示例都没直接提供，而是在集成测试里用了一个叫 **`agnhost`** 的测试镜像来演示（后文第九节）。

> 记忆锚点：**「内置 vs Webhook」看它住在哪，「变更 vs 校验」看它动不动手改对象。**

## 三、请求生命周期：准入控制发生在哪一步

把四类放回「一次请求的旅程」里，位置就很清楚了（[【跳转到 06:20】](https://www.youtube.com/watch?v=rPLH1aTeJ5Q&t=380)）：

![一次 API 请求的完整准入流水线](assets/Kubernetes%20准入控制器分类之旅/00380.webp)

1. **认证 + 鉴权**：请求进来，先做 authn（你是谁）和 authz（你能不能做这个操作）；
2. **变更阶段（mutating phase）**：所有**内置变更插件 + 变更 Webhook 串行执行**，它们会直接**修改进来的对象的 spec**；
3. **对象 schema 校验**：对改写后的对象做一次 schema 校验；
4. **校验阶段（validating phase）**：一批**内置校验插件 + 校验 Webhook** 逐字段校验；
5. **持久化**：全部通过，对象才被写入 etcd；**任意一环失败，整个请求被拒绝**。

这里有一个「配置方式」的演进值得单独记：早期用 `--admission-control` 这个参数，它要求你把所有 Webhook **按固定顺序**排好，而且 `MutatingAdmissionWebhook` 与 `ValidatingAdmissionWebhook` 必须放在最后两个。这个参数在 **1.10** 左右被废弃，换成了新的 `--enable-admission-plugins` / `--disable-admission-plugins`——**不再需要你操心顺序**，每个 API Server（以及各家云厂商）按自己的需要开启一组插件即可（[【跳转到 08:00】](https://www.youtube.com/watch?v=rPLH1aTeJ5Q&t=480)）。

> 实践提醒：正因为各厂商默认开启的插件集合不同，排查「为什么同一个 YAML 在这家云上被拒、换一家却通过」时，第一步就是去查**对方文档里到底开了哪些准入插件**。

## 四、内置准入插件为什么存在：安全、治理与配置

视频用一页专门回答「为什么需要准入控制器」（[【跳转到 08:47】](https://www.youtube.com/watch?v=rPLH1aTeJ5Q&t=527)）。内置插件的主要职责，就三件事：**安全（Security）、治理（Governance）、配置管理（Configuration Management）**。

![内置准入插件的职责与代表性名单](assets/Kubernetes%20准入控制器分类之旅/00527.webp)

挑几个最典型的举例：

- **DefaultStorageClass**：如果传入的存储请求**没有指定 StorageClass**，就给它补上一个**默认的**——省得用户每次都要写一遍；
- **LimitRanger**：在某个 namespace 内，如果 Pod **没写 CPU / 内存限额**，就把它**设成默认限额**；
- **AlwaysPullImages**：在多租户环境里保护你的**私有镜像**——强制**每个其他用户**都必须提供正确的认证（凭证）才能拉取你的镜像。视频称这是个「有意思」的插件，因为它解决的是「镜像被共享后失去隔离」的安全问题。

### 内置插件住哪儿、长什么样

内置的、编译进去的准入控制器，其代码位于 **`k8s.io/kubernetes/pkg/kubeapiserver/admission`** 目录下，默认启用的那批则由 **`pkg/kubeapiserver/options/plugins.go`** 定义（[【跳转到 15:08】](https://www.youtube.com/watch?v=rPLH1aTeJ5Q&t=908)）。

![内置准入插件在源码中的位置](assets/Kubernetes%20准入控制器分类之旅/00908.webp)

以 **AlwaysPullImages** 为例，它的 `admission.go` 里**同时实现了两个接口**——这也正好印证了前面「一条轴管动手、一条轴管喊停」的说法（[【跳转到 16:12】](https://www.youtube.com/watch?v=rPLH1aTeJ5Q&t=972)）：

- 实现 **mutation interface**：对应一个 `Admit` 函数，作用是**把 `imagePullPolicy` 设成 `Always`**；
- 实现 **validation interface**：对应一个 `Validate` 函数，作用是**确认这个值确实被设置上了**。

而执行的先后顺序，正是第三节里的那句话：**变更在前，校验在后**。

> 对比一句：**Validating 只会说「是 / 否」**——放行或不放行；**Mutating 则会真的改动对象**。这也是两者接口不同的根本原因。

## 五、两类 Webhook 的行为差异：校验并行、变更串行

内置插件讲完，就轮到外部 Webhook。两类 Webhook 最实质的差别在**执行方式**与**响应内容**上。

### 5.1 Validating Webhook：匹配到的并行执行，一个失败全拒

对校验型 Webhook（[【跳转到 09:08】](https://www.youtube.com/watch?v=rPLH1aTeJ5Q&t=548)）：

- **找到所有匹配该请求的 Webhook，并行（parallelly）执行**；
- **只要有任意一个失败，整个请求就被拒绝**；
- 因为它处在**最后、最终的阶段**，所以此刻**不会再发生任何变更**。

它的规则可以用几个维度去匹配：**操作（operations）**、**作用域（scope，Cluster 或 Namespaced）**，例如「v1 版本上、针对 pod 的 CREATE 操作、限定在某 namespace」。此外还可以用 **`objectSelector`**——当对象的**标签匹配**时**跳过**对这个 Webhook 的调用。

![Validating Webhook：并行执行、任一失败即拒绝](assets/Kubernetes%20准入控制器分类之旅/00548.webp)

### 5.2 Mutating Webhook：串行执行，用 JSON Patch 描述「怎么改」

对变更型 Webhook（[【跳转到 09:53】](https://www.youtube.com/watch?v=rPLH1aTeJ5Q&t=593)）：**它们是串行（serially）调用的**。请求/响应契约如下：

- 吃进一个 `AdmissionReview`，里面装着一个 **UID** 和**需要被变更或校验的资源对象**；
- 返回的响应里必须**带上同一个 UID**（原样回填），以及一个 **`allowed` 标志**，表示**接受还是拒绝**；
- 变更型 Webhook 还要额外返回一段 **patch**。

![Mutating Webhook 的要点清单：串行、幂等、匹配、超时等](assets/Kubernetes%20准入控制器分类之旅/00593.webp)

关于 patch，视频给了一个非常具体的例子（[【跳转到 11:08】](https://www.youtube.com/watch?v=rPLH1aTeJ5Q&t=668)）：**patchType 永远是 JSON**，patch 本体是**序列化后的 JSON 字节数组**。假设进来的是一张 Deployment，你想在它**没写 replicas 时补成 3**，就回一段：

```json
{ "op": "add", "path": "/spec/replicas", "value": 3 }
```

意思是「在 `/spec/replicas` 这个路径上**新增**一个值 3」。

### 5.3 五个容易踩坑的字段

视频把 Mutating Webhook 的若干注意事项列成了一页清单（[【跳转到 11:33】](https://www.youtube.com/watch?v=rPLH1aTeJ5Q&t=693)），挑最关键的几条：

- **幂等（Idempotence）**：因为**一个 Webhook 可能被调用不止一次**——当一段 patch 被多个 Webhook 相继改写时，你的 Webhook 就**可能被调用两次甚至更多**；而且**所有变更型 Webhook 之间的顺序并不保证**，任何 Webhook 都可能以任意顺序被调用。所以你的逻辑必须是**幂等**的。
- **匹配模式（matching）**：`Exact` 还是 `Equivalent`，**优先用 `Equivalent`**。原因还是那个 Deployment 例子——API Server 允许用不同版本创建/修改 Deployment，`apps/v1` 和 `apps/v1beta1` **应当有同样的效果**，用 `Equivalent` 才能让「补 replicas」对两种版本都生效。
- **超时（timeout）**：Webhook 的延迟会**累加到 API 延迟**上，所以要把超时设在 **0～30 秒**之间，别让一个慢 Webhook 拖垮整个 API。
- **`sideEffects`**：可取值如 `None`、`NoneOnDryRun` 等。如果你在做 **dry run（试运行）**，或请求**中途失败**，你必须保证 Webhook 能**回收它已经对集群做过的改动**。
- **`namespaceSelector`**：**必须设置**，用来避免 Webhook 在**系统 namespace** 里被触发——那可能给集群带来意料之外的行为。
- **`reinvocationPolicy`**：取值 `Never` 或 `IfNeeded`，用来控制一个 Webhook **是否会被多次调用**。

最后一句是最容易被忽视的原则：**变更型与校验型 Webhook 应当「配合工作」**——变更型先改某些字段，校验型再对这些字段做校验。

### 5.4 内置的变更插件也能「直接改对象」——指针语义

Webhook 用 JSON Patch 描述改动，而**内置变更插件**则更直接。视频专门讲了这背后的**指针（pointer）语义**（[【跳转到 17:42】](https://www.youtube.com/watch?v=rPLH1aTeJ5Q&t=1062)）：

- 传给内置插件函数的，**永远是这个对象的一个指针**；
- 你必须**直接在上面改**，因为这个对象**就是随后会被存储层（也就是 etcd）持久化的那个**；
- 这**和普通控制器很不一样**：普通控制器里常常有一层**缓存（cache）**，你**不能**去改缓存里的对象——因为缓存层并不知道你改了它、也不会把你写的值回写，最后就会「把自己炸掉」。

![内置变更 vs 校验：你可以拿到指向同一对象的指针，改动会进入存储层](assets/Kubernetes%20准入控制器分类之旅/01062.webp)

## 六、用 Webhook 时，请求/响应长这样

把视角切到 Webhook 一侧（[【跳转到 19:30】](https://www.youtube.com/watch?v=rPLH1aTeJ5Q&t=1170)）：Webhook 本质是**一个 REST API**，两类 Webhook 都会收到一个 `AdmissionReview`，里面是一个 `AdmissionRequest`；处理完逻辑后，把 `AdmissionReview` / `AdmissionResponse` 写回，并**把请求里的 UID 复制过去**、把 `allowed` 置为 `true`。

- **Validating**：`AdmissionResponse` 里带上 **`allowed` 字段**即可；
- **Mutating**：`AdmissionResponse` 里还要带上**一段 JSONPatch**，用来**描述期望的改动**。

![Webhook 的请求/响应里，校验型只回 allowed、变更型还要回 JSONPatch](assets/Kubernetes%20准入控制器分类之旅/01170.webp)

落到结构体上：`AdmissionReview` 里有 `AdmissionRequest` 与 `AdmissionResponse`；`AdmissionRequest` 里有 UID 和**对象（需要你反序列化成真正的对象再操作）**；决定好怎么改之后，写出 patch、复制 UID、置 `allowed=true`（[【跳转到 20:47】](https://www.youtube.com/watch?v=rPLH1aTeJ5Q&t=1247)）。

> 出错时怎么办？视频提醒：Webhook **应当返回一个规范的 HTTP 错误**，并带一条**对用户友好**的消息——比如「你的某个注解里缺少签名」。**缺什么就说清楚什么**。

## 七、PodPresets：内置变更插件的典型用法

前面说到内置变更插件的代表是 **PodPresets**（[【跳转到 13:48】](https://www.youtube.com/watch?v=rPLH1aTeJ5Q&t=828)）。它的作用是：**在 Pod 被创建的那一刻，往里面注入信息**，典型的有 **secrets、volumes、volumeMounts、环境变量**等。

![PodPresets 的结构：metadata 与要注入的 env/volumeMounts/volumes](assets/Kubernetes%20准入控制器分类之旅/00828.webp)

它的触发方式是**靠 Pod 上的标签匹配**。视频举的例子是：一张**带着 `front-end` 标签**的 Pod 进来，就会命中一条 PodPreset，于是被注入一个**环境变量**和若干 **volume mount**。

几个要点：

- **合并失败也不影响启动**：如果一个 PodPreset **merge 失败**，Pod **仍然会照常启动**（不会因为这个预设把 Pod 卡死）；
- **可以有任意多条（N 条）PodPreset 同时作用于一张 Pod**；
- 一条 PodPreset 可以影响**多类 Pod 请求**——被合并影响的可能是**所有容器**，甚至**整个 Pod spec**；
- 可以用一个**开关（flag）把它整体关掉**。

> 记住「默认值/注入」这类需求，往往就是内置变更插件或变更 Webhook 的用武之地——它让用户「少写也能跑对」。

## 八、落地建议与常见坑

视频最后用一页「Pitfalls and Idiomatic（坑与惯用法）」做了收尾（[【跳转到 25:10】](https://www.youtube.com/watch?v=rPLH1aTeJ5Q&t=1510)）。

![收尾清单：副作用、失败场景、安全、多语言、顺序不保证、维护](assets/Kubernetes%20准入控制器分类之旅/01510.webp)

### 8.1 尽量避免副作用（side effects）

这是整页里最重要的一条：**不要写入「除了传进来的那个对象之外」的其它对象**（[【跳转到 24:45】](https://www.youtube.com/watch?v=rPLH1aTeJ5Q&t=1485)）。原因是你要**避免维护状态**——大多数这类插件都应当是**近乎无状态**的：**即使被打断、重启，它们也能重新达成目标**。一旦引入状态，重启后的行为就难以预测了。

### 8.2 失败场景、安全与部署

- **失败场景（Failure scenarios）**：要理解 **failurePolicy** 的不同后果——如果设成 **`Ignore`**，你可能**悄悄跳过了一条企业强制要求**的策略，所以必须清楚自己在放行什么；
- **安全（Security aspects）**：**TLS 之外还有很多**要关心的——Webhook **并不是沙箱**；
- **部署位置**：Webhook 可以跑在**集群内**，也可以跑在**集群外**（它只是一个 REST 端点，**只要能访问到就行**）；建议把它放在**单独的 namespace**，并用 **RBAC** 约束谁能改它的配置对象。

### 8.3 语言、顺序与维护

- **多语言（Multi-language）**：因为 Webhook 只是一个独立 Web 服务，你**可以用任意语言**实现，**只要满足那套 REST API**（`AdmissionReview` 里装 request 和 response）即可；
- **顺序不保证（Chaining does not guarantee order）**：链式调用下顺序不确定，所以要**保持幂等**；
- **维护（Maintenance）**：Webhook 是你要长期运维的一份服务，别当成一次性脚本。

### 8.4 dry run 与「怎么上手写一个」

问答环节聊了两个初学者最关心的问题（[【跳转到 27:35】](https://www.youtube.com/watch?v=rPLH1aTeJ5Q&t=1655)）：

- **有没有好用的代码生成器 / 脚手架？** 视频的回答偏克制：`kubebuilder` 那套东西**不一定**是**专门**为准入控制器准备的；更好的参考是 **`agnhost` 镜像**——它里面塞了 **15 个不同的准入控制器**，虽然**有点过于复杂**，但**几乎覆盖了大部分特性**，而且**都被 Kubernetes 的集成测试跑过**，非常值得对照阅读。
- **dry run 的「回收（reconcile）」是怎么回事？** dry run 的目的是：**让你「看一眼某个对象会怎样」，但并不真的创建、持久化它**（[【跳转到 29:15】](https://www.youtube.com/watch?v=rPLH1aTeJ5Q&t=1755)）。实现上给进来的对象打一个 **dry run 标记**；这就再次解释了为什么**要避免副作用**——如果你在 Webhook 里**创建了别的对象**，dry run 时这些「副产物」就得被回收干净。所以正确的做法是：**让代码走完请求的完整生命周期，但最终不真正创建任何对象**。

### 8.5 现场演示：用 agnhost 跑两个 Webhook

视频末尾有一段演示（[【跳转到 22:34】](https://www.youtube.com/watch?v=rPLH1aTeJ5Q&t=1354)）：在一个两台节点的集群里，起一个提供 **TLS** 的服务，里面放**两个 Webhook 实现**——一个 **`always deny`**（直接把 `AdmissionResponse` 置为 `false`，并**带一条消息**），一个 **`add-label`**（给被创建的资源**加一个标签**）。先用 `kubectl get` 确认**没有任何 Webhook 配置**，再创建 Webhook 配置、跑一张 Pod，就能看到**预期生效**了。它也说明了一点：**一个服务里可以塞多个 Webhook 实现**——因为它本质就是一台服务器。

## 小结

- **准入控制器** = API Server 在**写入 etcd 之前**，对传入对象做**校验或修改**的一批插件；它是**同步拦截**，不是像普通控制器那样**异步收敛**。
- 分类就是一张**四象限表**：**内置 vs Webhook** × **校验型 vs 变更型**；其中**变更 Webhook 是给 CRD 做默认值的唯一手段**。
- 一次请求的顺序是：**认证鉴权 → 变更阶段（串行改写）→ schema 校验 → 校验阶段（Webhook 并行）→ 落库**；**任一环失败即拒绝**。
- 内置插件的职责是**安全、治理、配置**，代表有 `DefaultStorageClass`、`LimitRanger`、`AlwaysPullImages`；**变更先于校验**，你把内置变更插件拿到的是一个**指向待持久化对象的指针**，可以直接改。
- 两类 Webhook 的行为差：**Validating 并行、任一失败全拒**；**Mutating 串行、用 JSON Patch 描述改动**。
- 写 Webhook 的几条硬约束：**幂等**（可能被多次调用）、**匹配优先用 Equivalent**、**超时 0～30s**、**设 `namespaceSelector`**、**避免副作用**、**理解 `failurePolicy`**。
- 想找参考实现，看 **`agnhost`**（15 个准入控制器 + 被集成测试覆盖）。

## 关键术语速查

| 术语 | 一句话解释 |
| :--- | :--- |
| 准入控制器（Admission Controller） | 对象写入 etcd **之前**拦截它，做校验或修改的插件；只对写类操作用效。 |
| Validating（校验型） | 只回答「是 / 否」——放行或拒绝，**不修改**对象。 |
| Mutating（变更型） | 会**真的改动**对象（补默认值、注入字段等）。 |
| 内置编译插件（Built-in） | 与 API Server 编译在一起的准入插件，位于 `pkg/kubeapiserver/admission`。 |
| Admission Webhook | 外部 HTTP 回调形式的准入控制器，不跟 API Server 编在一起。 |
| `AdmissionReview` | Webhook 收发用的报文对象，内含 `AdmissionRequest` 与 `AdmissionResponse`。 |
| JSON Patch | 变更 Webhook 用 `{op, path, value}` 描述「怎么改」的补丁。 |
| `Equivalent` 匹配 | 让不同 API 版本（如 `apps/v1` 与 `apps/v1beta1`）都命中同一 Webhook。 |
| `failurePolicy` | Webhook 调用失败时的策略：`Fail` 拒绝、`Ignore` 放行（可能悄悄跳过强制策略）。 |
| PodPresets | 内置变更插件，按标签在 Pod 创建时注入 env / volume / secret 等。 |
| `agnhost` | 官方测试镜像，内含 15 个准入控制器，是学习/参考 Webhook 实现的好素材。 |
