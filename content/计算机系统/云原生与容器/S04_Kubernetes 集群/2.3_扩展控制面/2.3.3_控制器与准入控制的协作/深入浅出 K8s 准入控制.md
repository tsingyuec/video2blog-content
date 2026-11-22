# 深入浅出 K8s 准入控制：从内置插件到自研 Webhook

## 本讲要解决的核心问题（SCQA）

**背景**：你在用 Kubernetes 时，一定见过这些「凭空发生」的事——Namespace 一旦进入 `Terminating`，就再也建不进资源；给容器不写 `resources`，`kubectl describe` 里却冒出了 limit/request；只填了 `serviceAccountName`，Pod 里就自动挂上了证书文件。

**冲突**：这些能力不是控制器（controller）在你不知情时「偷偷调谐」出来的，而是在对象被写进 etcd 之前、由 `kube-apiserver` **同步**完成的。想给集群加一条自己的「写前改写 / 写前拦截」规则时，网上的 webhook 例子要么版本过时，要么复杂到看不懂，要么简单到把最关键的坑（TLS、路径、`failurePolicy`）全漏掉。

**疑问**：K8s 的「准入控制」到底是什么机制？它和控制器是什么关系？怎样才能用最少的代码，写出一个属于自己的准入 Webhook？

**回答（中心思想）**：准入控制是 `kube-apiserver` 请求流水线里、**认证鉴权之后、写入 etcd 之前**的一段可插拔阶段，天生分为「变更（mutating）」与「校验（validating）」两类动作。K8s 既内置了一批准入插件，又用 `MutatingAdmissionWebhook` / `ValidatingAdmissionWebhook` 两个插件开放出**回调式扩展点**，让第三方用 HTTP 服务接入自定义逻辑。抓住「配置对象 + 回调服务 + TLS」三件事，用**不到 100 行代码、4 个资源对象**就能落地一个自己的准入 Webhook。

> 本讲基于 B 站视频《【Meetup 分享】深入浅出 K8s 准入控制》（BV13F4m1A75n，约 37 分钟）整理。讲者是 cos（KubeSphere）社区贡献者，分享以「机制 + 现场手写 demo」为主。

---

## 一、先定位：准入控制发生在请求流水线的哪一步

理解准入控制，先要理解 `kube-apiserver` 是**整个控制平面流量的唯一入口**：任何对集群对象的读写都要先经过它。一条「修改对象」的请求（create / update / delete），大致会经过下面这条流水线（[【跳转到 02:05】](https://www.bilibili.com/video/BV13F4m1A75n/?t=125)）：

1. **反序列化**：把请求体的 JSON 解析成对象；
2. **认证（Authentication）**：确认「你是谁」，可插拔、可多个模块；
3. **鉴权（Authorization）**：确认「你能不能做」，例如 RBAC，同样可插拔；
4. **准入控制（Admission）**：本讲主角，在对象落库前做改写与拦截；
5. **写入 etcd**：通过后才真正持久化。

![kube-apiserver 请求流水线：认证、鉴权、准入、落库，多处都可插件化](assets/深入浅出%20K8s%20准入控制/00175.webp)

流水线里**很多阶段都能插件化**——认证、鉴权可以，准入同样可以。准入这一环又细分为两个子阶段：

- **变更准入（mutating admission）**：在创建/更新对象**最开始**执行，可以修改对象字段（改值、加字段）。因为「改完还要再校验」，所以必须**排在前面**；多个变更插件之间还会相互影响，因此需要**串行**。
- **校验准入（validating admission）**：在变更之后执行，只做「通过 / 拒绝」判断。**任意一个校验失败，整个 API 调用就失败**。

![变更准入先于校验准入：先改对象，再决定要不要放行](assets/深入浅出%20K8s%20准入控制/00242.webp)

> 关键区别：**准入是同步的、在 apiserver 内完成的**；而控制器是异步的、在后台不断把现实往期望状态收敛。这正是「控制器与准入控制」分工协作的根源——**准入管「写得对不对」，控制器管「最终像不像」。**

---

## 二、内置准入插件：K8s 把很多「魔法」都放在这里

K8s 原生功能里，有大量行为其实是内置的**准入插件**在幕后实现的（[【跳转到 04:36】](https://www.bilibili.com/video/BV13F4m1A75n/?t=276)）：

| 内置准入插件 | 作用 |
| :--- | :--- |
| `NamespaceLifecycle` | 当 Namespace 处于 `Terminating` 状态时，禁止在其下创建资源 |
| `LimitRanger` | 创建 Pod 时自动注入 `limits` / `requests` 等资源限制 |
| `ServiceAccount` | 只填 `serviceAccountName` 时，自动挂载 token 等文件（在代码里硬编码实现） |
| `PodNodeSelector` / `PodTolerationRestriction` | 结合 Namespace 注解限制 Pod 的调度与容忍 |
| `PodSecurity`（1.24+） | 内建三种 Pod 安全策略，替代旧的 PSP |

这些插件有的**默认开启**，有的需要**手动用 flag 启用**，每个关注点都不一样（可通过 apiserver 的 `--enable-admission-plugins` 查看与开关）。

![K8s 内置了一批准入插件，覆盖命名空间、资源限制、服务账号等原生能力](assets/深入浅出%20K8s%20准入控制/00326.webp)

那么问题来了：K8s 为什么要开放准入给外部？因为内置插件是「写死在代码里、靠 flag 开关」的，社区必然希望开发者能**自己扩展**。于是 K8s 提供了 `MutatingAdmissionWebhook` 与 `ValidatingAdmissionWebhook` 两个插件，作为给第三方对接的**回调式扩展点**：把一段自定义 HTTP 服务「注入」进准入链（[【跳转到 06:16】](https://www.bilibili.com/video/BV13F4m1A75n/?t=376)）。

---

## 三、如何声明一个 Webhook：配置对象与必看字段

K8s 里一切皆声明式，Webhook 也不例外——我们通过 `MutatingWebhookConfiguration` / `ValidatingWebhookConfiguration` 两个**资源对象**来定义它（[【跳转到 07:25】](https://www.bilibili.com/video/BV13F4m1A75n/?t=445)）。核心要关注这些字段：

- **请求体**：apiserver 发给 Webhook 的是一次 `AdmissionReview` 请求；Webhook 回一个 `AdmissionReview` 响应。
- **`clientConfig`**：Webhook 的 service 地址——apiserver 要发到哪个 Service（也可用 URL）。
- **TLS**：内部通信**强制要求 HTTPS**，因此必须配 `caBundle`（CA 证书）。
- **`failurePolicy`**：Webhook 不可用时怎么办——`Fail`（拒绝请求）还是 `Ignore`（放行）。**这是实际开发中最关键的一个字段**（下面单列一节）。
- **`objectSelector` / `namespaceSelector`**：只对「匹配某些 label 的对象 / 某些命名空间」生效。
- **`rules`**：和 RBAC 规则写法类似，用 `apiGroups` / `apiVersions` / `resources` / `operations` 精确指定「哪些资源的哪些操作」要触发这个 Webhook。

![ValidatingWebhookConfiguration 的关键字段：service 地址、caBundle、failurePolicy、selector 与 rules](assets/深入浅出%20K8s%20准入控制/00470.webp)

一个顺带的结论：**不管你用 `CRD` 还是 `Aggregated API Server` 扩展 K8s API**，扩展出来的资源都能被 Webhook 在「创建 / 变更」时校验——这正好把「API 扩展」和「准入控制」两件事串了起来（[【跳转到 08:40】](https://www.bilibili.com/video/BV13F4m1A75n/?t=520)）。

---

## 四、动手：不到 100 行，写出一个准入 Webhook

光讲概念没意义，讲者在现场手撸了一个最简版本（[【跳转到 12:00】](https://www.bilibili.com/video/BV13F4m1A75n/?t=720)）。他的目标很明确：**用最少的代码讲清机制**——因为 Webhook 本身非常简单，apiserver 发起一次 API 调用，请求体 `AdmissionReview` 的结构官方文档写得清清楚楚，即便手撸也很好实现。

**技术选型**：官方常用两条路——Kubebuilder 或手写 + `controller-runtime` SDK。讲者**刻意没用 Kubebuilder**：Kubebuilder 升级时常伴随数据迁移和代码结构变化，心智负担重；而手写版**不到 100 行**，只用 `controller-runtime` 帮我们搭出 admission webhook 框架，更清爽、更好维护。

**部署只需要 4 个对象**（[【跳转到 15:58】](https://www.bilibili.com/video/BV13F4m1A75n/?t=958)）：

1. `Secret`：存证书；
2. Webhook 配置对象：保存 apiserver 要回调的 service 地址；
3. `Service`：把流量引到 Webhook server；
4. `Deployment`：真正跑 Webhook server 的工作负载。

**几个必须注意的小细节**：

- **本地调试用 Telepresence**：把线上环境的某个 Service 流量「接管」到本机，本地就能实时断点 debug，省去来回转发流量、配网络（[【跳转到 10:10】](https://www.bilibili.com/video/BV13F4m1A75n/?t=610)）。
- **证书生成**：调 `openSSL` 手动生成 CA 与站点证书也行，但流程繁琐（要逐个生成、配路径）；开发阶段用 **helm 生成**最轻便，**cert-manager** 则更适合生产（略重）。
- **注册路径要手写**：Webhook 配置里填的 `path`，必须和代码里注册 server 时的路径一致。默认框架会「资源类型 + 固定前缀」拼路径，一个资源有多个 Webhook 时可能冲突，所以**手动指定路径**更可控（[【跳转到 21:48】](https://www.bilibili.com/video/BV13F4m1A75n/?t=1308)）。
- **业务逻辑就两个接口**：`Default`（mutating，改写对象）和 `Validate`（validating，拒绝对象）——对象可以是任意资源类型。demo 里写了一条极简规则：**发现容器用了 `nginx:latest` 镜像就返回 forbidden**，创建即被拒（[【跳转到 18:03】](https://www.bilibili.com/video/BV13F4m1A75n/?t=1083)）。

![开发期用 Telepresence 把线上 Service 接管到本地，实时断点调试自己的准入逻辑](assets/深入浅出%20K8s%20准入控制/01308.webp)

这段 demo 想传达的是：**实际业务里的校验/注入逻辑，真的可以就这么简单**，几个文件就能把自己的 Webhook 组织起来。

---

## 五、开发准入 Webhook 的工程注意事项

讲者把「开发时容易踩的坑」单列成了几点（[【跳转到 21:23】](https://www.bilibili.com/video/BV13F4m1A75n/?t=1283)）：

- **路径配置**：见上——默认框架路径不可控、可能冲突，建议手动指定。
- **手写 vs Kubebuilder**：手写代码往往更高效、更易维护，也更适合「我就想干一件小事」的场景。
- **证书方案**：cert-manager（稳定、生产）/ helm（图简单）/ 用 K8s 的 CSR 签发，按需选。
- **`failurePolicy` 的取舍**：Webhook 一旦「没写好」，可能把所有人的资源创建都 forbid 掉，**影响平台稳定性**。所以强校验用 `Fail`、弱校验用 `Ignore`——**Webhook 挂了要不要连带阻断正常资源创建，是必须权衡的**（[【跳转到 23:25】](https://www.bilibili.com/video/BV13F4m1A75n/?t=1405)）。
- **`objectSelector` / `namespaceSelector`**：只关注自己关心的对象与命名空间。有个很妙的用法：**用 `objectSelector` 绕过「存有问题的旧 Webhook」**——比如 helm 更新时会重放旧 Webhook，若它已处于异常状态，会卡住资源更新，此时用一个 label selector 把「造这个问题的那批资源」排除掉即可（[【跳转到 24:40】](https://www.bilibili.com/video/BV13F4m1A75n/?t=1480)）。

---

## 六、真实世界里的准入控制：从 PodSecurity 到 Gatekeeper

准入 Webhook 在生产里用得非常多，讲者挑了几个典型场景（[【跳转到 26:56】](https://www.bilibili.com/video/BV13F4m1A75n/?t=1616)）：

### 6.1 PodSecurity Standards：K8s 官方收窄后的安全策略

旧的 `PodSecurityPolicy`（PSP）灵活但能力有限，于是 1.24 版本干脆把它**最小化抽象成三种内建安全策略**（Privileged / Baseline / Restricted），只保证这一档基础能力。不满足？就继续在准入 Webhook 之上做扩展。

### 6.2 Gatekeeper 与 Kyverno：基于准入的策略引擎

- **Gatekeeper**：它是**架在准入 Webhook 之上的策略控制（policy controller）**，用声明式方式定义集群安全策略。其策略语言基于 **OPA（Open Policy Agent）的 Rego**——可以把策略当「脚本」来写，动态下发、无需重新编译部署，极大提升效率。它也支持滚动发布、预发布等机制，并可用于 KubeSphere 的权限声明。典型规则：Pod 镜像必须来自可信仓库、必须带版本号而不能用 `latest` 等（[【跳转到 29:26】](https://www.bilibili.com/video/BV13F4m1A75n/?t=1766)）。
- **Kyverno**：同样开源、更贴合 K8s 声明式风格——**无需自己写脚本**，内置了大量开箱即用的社区策略（镜像仓库限制、资源限制、Pod 限制等），编程负担更低（[【跳转到 30:30】](https://www.bilibili.com/video/BV13F4m1A75n/?t=1830)）。

![Gatekeeper 基于 OPA/Rego 编写可编程策略，用于集群安全准入](assets/深入浅出%20K8s%20准入控制/01716.webp)

### 6.3 平台里的「默认注入/改写」场景

很多平台性需求，本质都是准入 Webhook 在做事（[【跳转到 32:18】](https://www.bilibili.com/video/BV13F4m1A75n/?t=1938)）：

- **给特定类型的 Secret 注入默认字段**：当检测到某个 Secret 的 `type` 是自定义类型时，自动补上默认 endpoint、字段，而不必为一点点配置就新建一个 CRD；
- **企业配额管理**：在 validating 阶段检查「这个 Pod 是谁建的、在哪个 namespace / workspace 下、对应配额够不够」，从而把 `ResourceQuota` 从「命名空间级」扩展到「人 / 工作空间级」；
- **注入环境变量**：把平台级公共参数（如某些服务地址）统一注入，业务方无需各自配置；
- **格式化 ConfigMap**：ConfigMap 里存了长配置文件、混入多余换行与空白字符时，`kubectl edit` 会乱成一团；用 Webhook 把这些噪声清掉，`kubectl edit` 就能肉眼可读。

![平台里的默认注入（Secret 默认字段、配额、环境变量、ConfigMap 格式化）几乎都靠准入 Webhook 实现](assets/深入浅出%20K8s%20准入控制/01963.webp)

### 6.4 推荐

讲者最后推荐：**集群安全策略优先考虑 Gatekeeper 与 Kyverno**，它们在 K8s 集群安全相关功能上都非常成熟，KubeSphere 也已通过扩展组件的方式集成了 Gatekeeper（[【跳转到 36:28】](https://www.bilibili.com/video/BV13F4m1A75n/?t=2188)）。

---

## 小结

- **准入定位**：它在 kube-apiserver 流水线的「认证鉴权之后、写入 etcd 之前」，是**同步**的；控制器则是**异步**的——两者分工协作：准入管「写前合规」，控制器管「最终收敛」。
- **两类动作**：`mutating`（改对象，必须在前、串行）与 `validating`（只判定，可并行）；**任一校验失败即整单失败**。
- **两个扩展点**：`MutatingAdmissionWebhook` / `ValidatingAdmissionWebhook` 把自定义逻辑接进入准链。
- **内置插件**：`NamespaceLifecycle`、`LimitRanger`、`ServiceAccount`、`PodNodeSelector` 等，很多「原生魔法」来自这里。
- **落地三件事**：配置对象（`clientConfig` + `rules`）、回调服务、TLS（`caBundle`）；再用 `failurePolicy` / `objectSelector` / `namespaceSelector` 控制风险与范围。
- **最薄实现**：手写 + `controller-runtime`，不到 100 行、4 个对象即可跑通；开发期用 Telepresence 本地调试。
- **生产用策略引擎**：Gatekeeper（OPA/Rego，可编程）与 Kyverno（声明式、开箱策略）。

## 关键术语速查

| 术语 | 一句话解释 |
| :--- | :--- |
| 准入控制（Admission Control） | apiserver 在对象落库前执行的同步阶段，可改写或拦截请求 |
| Mutating Admission | 变更准入，修改对象字段，先于校验、串行执行 |
| Validating Admission | 校验准入，只判定通过/拒绝，可并行 |
| `MutatingAdmissionWebhook` / `ValidatingAdmissionWebhook` | 开放给第三方的回调式准入扩展点 |
| `AdmissionReview` | apiserver 与 Webhook 之间交换的请求/响应对象 |
| `failurePolicy` | Webhook 不可用时 `Fail`（拒绝）还是 `Ignore`（放行） |
| `caBundle` | apiserver 校验 Webhook 服务端证书用的 CA 证书 |
| PodSecurity Standards | 1.24+ 替代 PSP 的内建三档 Pod 安全策略 |
| Gatekeeper / OPA / Rego | 架在准入 Webhook 之上的策略引擎，用 Rego 写策略 |
| Kyverno | 声明式、内置大量策略、无编程负担的准入策略引擎 |
| Telepresence | 把线上 Service 流量接管到本地，便于实时调试 |
| controller-runtime | 构建控制器与 Admission Webhook 的官方 SDK |
