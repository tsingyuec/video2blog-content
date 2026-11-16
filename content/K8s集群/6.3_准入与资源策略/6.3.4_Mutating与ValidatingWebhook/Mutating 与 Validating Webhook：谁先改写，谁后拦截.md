# Mutating 与 Validating Webhook：谁先改写，谁后拦截

## 本讲要解决的核心问题（SCQA）

**背景**：你给集群提交一个 YAML，偶尔会遇到「莫名其妙」的结果——明明没写 `type: 1` 这类字段，对象却被人补上了默认值；或者反过来，只是想建一个 CronJob，却被 API Server 直接拒绝，报一段你根本没写过的错误。

**冲突**：做这些事的既不是 `kubectl` 客户端，也不是后台的控制器（controller）。控制器是**异步**的：对象早就落库了，它才慢慢把现实往期望状态收敛。可上面这些「写之前就被改写 / 写之前就被拦下」的行为是**同步**发生的——请求还没返回，结果就已经定了。

**疑问**：到底是谁在对象进入集群之前动了它？「改写」和「拦截」又是怎么分工的？为什么有的 Webhook 先跑、有的后跑？

**回答（中心思想）**：答案是 **Admission Webhook（准入 Webhook）**，它是 `kube-apiserver` 在写入 etcd **之前**发起的一次「阻塞式 HTTP 回调」。准入 Webhook 分两类动作、严格分先后：**Mutating（变更）先跑，负责改写对象、注入默认值；Validating（校验）后跑，负责判断放行还是拒绝**。只有两类都通过，对象才会真正进入集群，随后才轮到控制器去做调和（reconcile）。

> 本讲基于 B 站视频《webhook 在 k8s 中原来是这个作用！》（BV1or421x7b2，约 12 分钟）整理。视频以官方文档为主线，配一段「创建非法资源被拒」的现场演示。

---

## 一、先把 Webhook 说清楚：一次等回应的 HTTP 请求

官方文档对 Webhook 的定义是：**以阻塞（blocking）方式发送的信息请求**——能处理 Webhook 的 Web 应用会收到一个 HTTP 请求，从而从其它应用那里获得信息（[【跳转到 00:25】](https://www.bilibili.com/video/BV1or421x7b2/?t=25)）。

这句话里最关键的是 **blocking（阻塞）**。它的含义是：**调用方发完请求后不会自顾自往下走，而是停下来等对方回话**。放到 K8s 里就是——当某个「值得关注的事件」发生时，系统会主动向另一个应用发出请求，并且**等它返回结果后才继续**。

用一个更好懂的说法：Webhook 就是「一件事走到最后一步时，顺手去调用另一个接口、问一句、拿回结果」（[【跳转到 01:45】](https://www.bilibili.com/video/BV1or421x7b2/?t=105)）。它不是「通知完就走」的火并 forget，而是**必须等到回应**的同步交互。

## 二、K8s 里其实有三种 Webhook

很多人以为「Webhook = 准入 Webhook」，其实官方文档明确列出 K8s 里有**三种** Webhook（[【跳转到 01:15】](https://www.bilibili.com/video/BV1or421x7b2/?t=75)）：

| Webhook 类型 | 管什么 |
| :--- | :--- |
| **Admission Webhook（准入）** | 对象写入集群**之前**介入，做改写或拦截 |
| **Authorization Webhook（鉴权）** | 把「你能不能做这个操作」的判断交给外部服务 |
| **CRD Conversion Webhook（转换）** | 在同一个 CRD 的不同版本之间做字段转换 |

![Kubernetes 官方文档列出的三种 Webhook 类型](assets/Mutating%20与%20Validating%20Webhook：谁先改写，谁后拦截/00075.webp)

视频里提到，在 `controller-runtime` 这个常用开发库里，日常至少会接触到**准入 Webhook** 和 **CRD 转换 Webhook**——前者用于「写前改写/拦截」，后者用于「多版本 CRD 的兼容」。本讲聚焦前者。

## 三、准入 Webhook 在「动态准入控制」里，是一段 HTTP 回调

准入 Webhook 属于 K8s 的**动态准入控制（dynamic admission control）**这一块（[【跳转到 01:40】](https://www.bilibili.com/video/BV1or421x7b2/?t=100)）。它的本质是**一个 HTTP 回调**：API Server 收到准入请求（`AdmissionReview` request），把它发给你的 Webhook 服务，做完处理后，你的服务把结果（`AdmissionReview` response）返回给 API Server。

所谓「回调」，就是「我做一件事时，在关键节点去调用另一个接口、跟它交互、拿回结果」。准入 Webhook 完全符合这个模式：**它接收一次准入请求，做某些处理，再回传结论**（[【跳转到 01:45】](https://www.bilibili.com/video/BV1or421x7b2/?t=105)）。

> 记住三个关键词：**回调服务**、**`AdmissionReview` 报文体**、**同步等待**。它们是后面「配置对象怎么指向 Webhook」的基础。

## 四、两类准入 Webhook，严格控制先后顺序

准入 Webhook 有两种类型（[【跳转到 02:35】](https://www.bilibili.com/video/BV1or421x7b2/?t=155)）：

### 1. MutatingAdmissionWebhook —— 先跑，负责改写

**Mutating 会被最先调用**。它可以**修改（mutate）**准备发给 API Server 的对象，用来强制执行我们自定义的默认值、补全字段。通俗说，就是「你漏填的、需要按环境调整的字段，在这里被自动补上」。

![Mutating 先跑：改写对象、执行自定义默认值](assets/Mutating%20与%20Validating%20Webhook：谁先改写，谁后拦截/00130.webp)

Mutating 只能有一轮「群体改写」的机会，所以它必须排在**最前面**——因为「改完之后还要再校验」，如果把校验放到前面、改写放到后面，改写后的对象就没人再检查了。

### 2. ValidatingAdmissionWebhook —— 后跑，负责拦截

**等所有对象的修改都完成之后**，对象才会交给 API Server 去做校验，这时 **Validating Admission Webhook 被调用**（[【跳转到 03:00】](https://www.bilibili.com/video/BV1or421x7b2/?t=180)）。它只做一件事：**判断通过还是拒绝**，从而执行我们自定义的策略。

![Validating 后跑：所有改写完成后才校验，可以拒绝请求](assets/Mutating%20与%20Validating%20Webhook：谁先改写，谁后拦截/00180.webp)

一句话记住分工与顺序：**先 Mutating「改」，后 Validating「判」；改完才能判，判不过就被拦下。**

## 五、Validating 可以被「多个」匹配，并且是并行执行的

一个 Validating Webhook 会被**任何一个匹配到该请求的 validating webhook 调用**；也就是说，我们可以定义**多个** Validating Webhook，只要某个请求能匹配上，对应的 Webhook 就会被触发（[【跳转到 03:51】](https://www.bilibili.com/video/BV1or421x7b2/?t=231)）。

关键细节：**匹配到的多个 Validating Webhook 是「平行（并行）」调用的**。它们各自独立判断，**任意一个失败都可以拒绝请求**。这与 Mutating 的「串行改写」形成对照——因为「校验」之间互不影响，谁也不用基于谁的输出，所以可以并行。

![多个匹配的 Validating Webhook 并行调用，任一失败即可拒绝](assets/Mutating%20与%20Validating%20Webhook：谁先改写，谁后拦截/00256.webp)

> 顺带一个容易踩的坑：视频提到，如果你**禁用了** `ValidatingAdmissionWebhook` 这个内置插件，**也必须把对应的 `ValidatingWebhookConfiguration` 配置对象一并禁用**，否则配置指向的 Webhook 就失去了意义。

## 六、校验发生在控制器之前：这决定了整条链的定位

为什么说准入控制是「写前」的关卡？因为**只有合法的资源被交给 K8s 之后，控制器（controller）才会去做调和（reconcile）**，把当前状态推进到期望状态（[【跳转到 05:06】](https://www.bilibili.com/video/BV1or421x7b2/?t=306)）。

![准入发生在控制器之前：先决定资源能不能进来，再谈怎么收敛](assets/Mutating%20与%20Validating%20Webhook：谁先改写，谁后拦截/00306.webp)

所以 **Admission 这一步其实发生在控制器之前**。它管的是「这个对象**能不能、以什么样子**进入集群」；控制器管的是「进来之后，现实**像不像**期望状态」。把这两件事分开，就能理解为什么准入是同步的、而控制器是异步的——一个是「写前的门禁」，一个是「写后的纠偏」。

顺便一提，校验与 **group/version** 密切相关：比如某个资源你只声明了 `v1`，对方却发来 `v2`，那就是不合法的，直接拒绝——不允许它被交付到集群里（[【跳转到 04:41】](https://www.bilibili.com/video/BV1or421x7b2/?t=281)）。

## 七、用配置对象声明 Webhook：靠 rules 决定「谁来触发」

K8s 里一切皆声明式，Webhook 也不例外。在我们的项目目录里会看到两种配置对象（[【跳转到 07:04】](https://www.bilibili.com/video/BV1or421x7b2/?t=424)）：

- **`MutatingWebhookConfiguration`**：对应「改写类」Webhook；
- **`ValidatingWebhookConfiguration`**：对应「校验类」Webhook。

配置里会定义**一个路径（path）**，并用一组 **rules** 描述触发条件。视频里演示的规则大致是：**当 API 组、版本是 `v1`，操作是 `create` 或 `update`，且资源类型是 `CronJob` 时**，这些条件互相匹配，请求就会走 Mutating Webhook 这条路（[【跳转到 07:54】](https://www.bilibili.com/video/BV1or421x7b2/?t=474)）。

![Webhook 配置里用 rules 精确描述「哪些资源的哪些操作」触发回调](assets/Mutating%20与%20Validating%20Webhook：谁先改写，谁后拦截/00474.webp)

这里也解释了「为什么多个 Webhook 是平行的」：比如同时存在 `v1`、`v2` 两套配置，它们**彼此不会互相影响**——匹配谁的规则，就走谁那条路（[【跳转到 08:19】](https://www.bilibili.com/video/BV1or421x7b2/?t=499)）。

## 八、现场演示：一次「非法创建」是怎么被拦下的

理论讲完，视频里做了一次实测：先 `make deploy` 把 Webhook 部署起来，然后**故意创建一个非法对象**（比如某字段的正确取值是 `1`，却传了别的值）（[【跳转到 09:09】](https://www.bilibili.com/video/BV1or421x7b2/?t=549)）。

结果是：**客户端发起创建后直接报错**。而在这个错误返回给我们之前，请求其实经历了两个阶段——先经过 **Validating 和 Mutating** 这两个 Webhook，去确认「这个资源类型 K8s 是否已知（CRD 是否已注册）」，如果是已知的，再继续校验「这些字段是否合法」（[【跳转到 10:24】](https://www.bilibili.com/video/BV1or421x7b2/?t=624)）。

把值改回 `1` 再创建，就**正常匹配、成功创建**了；而如果版本对不上（比如声明的是 `v1`、却发 `v2`），就会「找不到」（[【跳转到 11:14】](https://www.bilibili.com/video/BV1or421x7b2/?t=674)）。

整条链路可以概括为（[【跳转到 11:39】](https://www.bilibili.com/video/BV1or421x7b2/?t=699)）：

> 你创建资源时，K8s 会**向 Webhook 的某个路径发送 HTTP 请求**，把这个对象发给它，问它「到底认不认识这个对象、允不允许创建」。**允许就直接创建；不允许，就把报错返回给你。**

## 九、小结与记忆锚点

- **Webhook 的本质**：一次**阻塞式**的 HTTP 回调——调用方要等回应。
- **三种 Webhook**：准入（Admission）、鉴权（Authorization）、CRD 转换（Conversion）；本讲聚焦准入。
- **两类准入动作，严格分先后**：
  - **Mutating 先跑**，改写对象、注入默认值，**串行**；
  - **Validating 后跑**，只判通过/拒绝，多个匹配时**并行**，任一失败即可拒绝。
- **定位**：准入发生在**控制器 reconcile 之前**，是「写前的门禁」；控制器是「写后的纠偏」。
- **落地方式**：用 `MutatingWebhookConfiguration` / `ValidatingWebhookConfiguration` 声明，靠 **path + rules**（apiGroups / versions / resources / operations）决定谁被触发。
