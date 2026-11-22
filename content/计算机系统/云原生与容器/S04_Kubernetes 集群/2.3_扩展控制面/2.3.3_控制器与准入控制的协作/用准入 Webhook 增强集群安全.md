# 用准入 Webhook 增强集群安全：从内置 Admission Controller 到 OPA

## 本讲要解决的核心问题（SCQA）

**背景**：你已经熟悉 Kubernetes 的认证、鉴权与 RBAC，知道怎么给「谁能在哪个命名空间做什么」立规矩。

**冲突**：但 RBAC 管不住**对象内容**——它拦不住你拉一个来源不明的镜像，也没法给一批动态创建的命名空间统一注入 `nodeSelector`，更没法强制某个字段必须符合格式。这类「看完对象内容再决定放不放行、要不要改」的活，得交给**准入控制器（Admission Controller）**。

**疑问**：准入控制器到底是什么？它和控制器是不是一回事？内置的这么多该怎么挑？什么时候该自己写 Webhook？最关键的——**写了自己的 Webhook 之后，策略一旦中途变严，集群里已经存在的那些旧对象怎么办？**

**回答（中心思想）**：准入控制器是 apiserver 在**认证鉴权之后、写入 etcd 之前**对请求做「变更或校验」的一段代码，优先用**内置插件**解决常见诉求；内置不够时再自研 Webhook，或用 **OPA** 把策略与代码分离。但一定要记住：**准入 Webhook 只在你「写的那一刻」把关，它不会回头检查存量对象**——策略变更后要让旧对象重新符合新规，必须再配一个**控制器**去周期性收敛。这道「准入管写前、控制器管事后」的分工，正是二者协作的边界。

> 本讲基于 KubeCon 分享《Kubernetes Track: Using Admission Webhooks to enhance security》（YouTube `c6Y35av2BUE`，约 37 分钟）整理。讲者 Jan Waś 以「概念 + 幻灯片代码」为主，无现场 demo。

---

## 一、准入控制器在请求流水线中的位置

**准入控制器是一段拦截 apiserver 请求的代码**：它在请求被认证、鉴权之后，对象被写进 etcd 之前介入（[【跳转到 01:20】](https://www.youtube.com/watch?v=c6Y35av2BUE&t=80)）。它只作用于**修改对象的请求**（create / update / delete），**读取（get/list）不经过它**。

一条请求的完整流程是（[【跳转到 02:15】](https://www.youtube.com/watch?v=c6Y35av2BUE&t=135)）：

1. **认证（Authentication）**：以「模块」形式做，可能有多个；**任一模块成功**即可继续；
2. **鉴权（Authorization）**：同样是模块化的，例如 RBAC；**任一模块放行**即可继续；
3. **准入控制器（Admission Controllers）**：规则**反了过来**——**所有**被配置的准入控制器都**必须**通过，请求才能继续；
4. **写入 etcd**：全部通过后，修改才被持久化。

![请求流水线：认证/鉴权「任一通过即可」，而准入控制器「必须全部通过」](assets/用准入%20Webhook%20增强集群安全/00185.webp)

这个「任一放行 vs 全部放行」的差别很关键：认证鉴权是**叠加式**的（多个身份来源、多条授权路径），而准入是**把关式**的（每个插件都是一票否决）。

---

## 二、两条分支：变更准入 vs 校验准入

准入控制器分两类（[【跳转到 03:30】](https://www.youtube.com/watch?v=c6Y35av2BUE&t=210)）：

- **变更准入（Mutating）**：可以修改对象——改字段值、加新字段、往数组里追加元素。例如更新时补上 `lastUpdateTimestamp`。**它必须排在前面、串行执行**，因为一个插件改了对象，会影响后面插件看到的输入，也会影响校验结果。
- **校验准入（Validating）**：只看对象、决定要不要拒绝，**不改对象**；因此**可以并行**执行以提速。

顺序不能颠倒：**绝不能在「校验通过」之后再去改对象**，否则校验就失去意义了。所以永远是「先把所有变更做完，再做校验」。

---

## 三、优先用内置：以 PodNodeSelector 为例

讲者的第一个例子很实际：**把开发环境的工作负载和生产环境隔离开，调度到不同节点上**——比如开发环境会跑没测过的代码、可能忘记设 limit 把整个节点拖垮，隔离能降低风险（[【跳转到 04:27】](https://www.youtube.com/watch?v=c6Y35av2BUE&t=267)）。

那该挑哪个准入控制器？思路是「在名字里找关键词」：需要按**节点标签**选择节点，正好有一个 `PodNodeSelector`（名字里带 pod / node / selector），而且**默认开启**（[【跳转到 05:47】](https://www.youtube.com/watch?v=c6Y35av2BUE&t=347)）。

用法有两种：

- **最简单**：给命名空间加一条固定 key 的注解，值是一个节点标签选择器；此后**该命名空间里所有 Pod** 都会被调度到匹配的节点上。
- **更通用**：若想给「所有命名空间」设一个默认选择器（例如 GitLab 会为每个 feature branch 动态创建命名空间），就得改 apiserver 的启动参数、指定一个配置文件——文件里列出各命名空间的选择器，并可定义一个兜底默认值（[【跳转到 07:27】](https://www.youtube.com/watch?v=c6Y35av2BUE&t=447)）。

![内置准入插件的完整列表——讲者建议先在这里找现成的，别急着自研](assets/用准入%20Webhook%20增强集群安全/00347.webp)

**别忘了一个副作用**：你得真的**给节点打上标签**，动态加入集群的新节点也要补标签，否则规则不生效。好在一批**默认标签**（zone / region / 实例类型等，具体取决于云厂商）可以直接拿来用（[【跳转到 09:07】](https://www.youtube.com/watch?v=c6Y35av2BUE&t=547)）。

`PodNodeSelector` 的**工作方式**正是「变更准入」的典型：它给 Pod 加上 `nodeSelector` 字段，进而影响调度（[【跳转到 09:57】](https://www.youtube.com/watch?v=c6Y35av2BUE&t=597)）。

它的**局限**也要清楚：需要额外配置；只支持**简单**的标签匹配与组合；想做更复杂的亲和，只能自己写在 Pod 上——因为**目前没有针对亲和性的内置准入控制器**（[【跳转到 10:47】](https://www.youtube.com/watch?v=c6Y35av2BUE&t=647)）。

---

## 四、模仿内置插件：它们都在干什么

如果确实没有现成插件满足需求，就该自己动手了。但动手前，先「把内置的看一圈」，学它们的用法与边界（[【跳转到 11:04】](https://www.youtube.com/watch?v=c6Y35av2BUE&t=664)）：

| 内置准入控制器 | 类型 | 作用 |
| :--- | :--- | :--- |
| `NamespaceExists` | 校验 | 确保要在其中创建对象的命名空间确实存在 |
| `NamespaceLifecycle` | 校验 | 命名空间删除过程中，禁止再往里创建对象；命名空间也在更复杂地拆除 |
| `NodeRestriction` | 校验 | 限制 kubelet 只能修改**与自己节点关联**的 Node 对象，不能碰别的节点 |
| `OwnerReferencesPermissionEnforcement` | 校验 | 修改 `ownerReferences` 需要额外权限（配合 RBAC 使用） |
| `PodNodeSelector` / `PodTolerationRestriction` | 变更 | 结合命名空间给 Pod 注入节点选择器 / 容忍 |
| `AlwaysPullImages` | 变更 | 强制镜像拉取策略为 `Always`，避免凭证过期后仍能用缓存镜像 |
| `DefaultStorageClass` | 变更 | 用户没写 `storageClassName` 时补上默认值 |
| `LimitRanger` | 变更 | Pod 没写 limit 时，套用命名空间里的默认 limit |

讲者总结出的规律：**变更类插件主要用来「设默认值」**，而且**不该做太出乎意料的事**——因为「乱改对象可能破坏其它控制器的生命周期」，这正是内置插件都克制地只设默认的原因（[【跳转到 15:03】](https://www.youtube.com/watch?v=c6Y35av2BUE&t=903)）。另外注意：**这两个 Webhook 到讲时（该版本）仍标记为 beta**，可通过 apiserver flag 启用或禁用非默认插件。

---

## 五、自己写一个 Webhook：配置对象与回调服务

要自研准入控制器，第一步是创建 **Webhook 配置对象**（`ValidatingWebhookConfiguration` / `MutatingWebhookConfiguration`），它告诉 K8s **如何找到并调用**你的 Webhook（[【跳转到 15:53】](https://www.youtube.com/watch?v=c6Y35av2BUE&t=953)）：

- **`rules`**：列出你关心哪些资源、哪些操作——apiserver **只把命中的请求**转发给你，不必也不能处理全部；
- **`clientConfig`**：`URL` 或 `service`（服务名 + 命名空间）。讲者用 AWS Lambda 的 URL 做例子，因为「不用自己搭 HTTP 服务」最省事；若服务在集群内，就填 `service`，此时它**必须监听 443**；
- **HTTPS**：**必须**是 HTTPS，apiserver **完全不接受** HTTP；URL 里也**不能带 basic auth**；因此要提供 `caBundle`；
- **`namespaceSelector`**：把生效范围限定在某些命名空间；
- **`failurePolicy`**：`Fail` 还是 `Ignore`——**Webhook 调不通时怎么办**（临时宕机、或新版本把它改坏了）；
- **`timeout`**：这是**外部调用**，必须设超时。

![Webhook 配置对象：rules 决定「哪些请求转发」、clientConfig 决定「往哪发」](assets/用准入%20Webhook%20增强集群安全/00978.webp)

关于 `failurePolicy` 的取舍：这取决于你要的是「软限制」还是「硬限制」。**软限制**下 Webhook 挂了就放行，可能放进一些不该放的工作负载，但至少集群还能用；**硬限制**下则宁可拒绝所有请求。如果确实需要双向认证，还得额外写一份 kubeconfig 格式的配置文件传给 apiserver（[【跳转到 18:23】](https://www.youtube.com/watch?v=c6Y35av2BUE&t=1103)）。

### 5.1 回调服务长什么样

讲者用一段极简的 Lambda handler 演示**校验型 Webhook**：检查所有容器是否只用**私有仓库**的镜像（[【跳转到 20:03】](https://www.youtube.com/watch?v=c6Y35av2BUE&t=1203)）。要点：

- 把收到的请求读进来，构造响应时**必须把 `uid` 原样拷回**——apiserver 靠它确认「这个响应是对应那次请求的」；
- 只设置 `allowed` 字段（true / false），根据「每个容器镜像是否以指定前缀开头」来判定；
- 它会遍历 `object.spec.containers`——**请求里带着完整对象**，你想查任何字段都行；
- 校验型 Webhook **不改对象**。

一个常被忽略的点：这段代码**连「为什么拒绝」都没说**，导致用户只看到「被拒了」却一头雾水。响应结构里其实有个 `result` 字段可以写明原因——**强烈建议始终填写理由**，让用你集群的人知道发生了什么、该怎么做（[【跳转到 25:03】](https://www.youtube.com/watch?v=c6Y35av2BUE&t=1503)）。

![校验 Webhook 的 handler：拷回 uid、设置 allowed、遍历容器校验镜像](assets/用准入%20Webhook%20增强集群安全/01203.webp)

- **变更型 Webhook** 则用 **`patch`** 字段返回改动，**只支持 JSON Patch**，且 `patchType` 只能取一个固定值；不需要自己手搓 patch——拿「原对象」和「改后的副本」调用现成库即可生成。此外变更还会带上 **warning / audit 注解**，同样是提示用户「集群里刚刚发生了什么」的手段。
- 另外一个坑：**Webhook 是按「对象」触发的**。你用 Deployment 建 Pod，Deployment 本身可能通过校验，但它创建的**每个 Pod 都会被单独再校验一次**——所以自研 Webhook 必须**足够快**。

### 5.2 改成集群内服务

把 `URL` 换成 `service` 就变成调用集群内服务，apiserver 通过 HTTPS 访问它（[【跳转到 27:08】](https://www.youtube.com/watch?v=c6Y35av2BUE&t=1628)）。配置里还能声明这个 Webhook **是否有副作用（side effects）**——如果有副作用（比如顺手改了对象或外部资源，或维护了「创建了多少对象」的计数器），就应加以保护，并且可能要求它返回的改动**再走一遍所有 Webhook** 重新校验；而保护它需要改两个 apiserver flag（[【跳转到 22:33】](https://www.youtube.com/watch?v=c6Y35av2BUE&t=1353)）。

![把 URL 换成 service，并用一份 kubeconfig 格式的外部配置支持 mTLS / 相互认证](assets/用准入%20Webhook%20增强集群安全/01303.webp)

---

## 六、为什么「自己写」可能并不划算

写 Webhook 的**真实成本**远不止一个 handler（[【跳转到 27:58】](https://www.youtube.com/watch?v=c6Y35av2BUE&t=1678)）：

- 得处理 HTTP、认证鉴权；
- 得打成镜像、管理 TLS 证书（放进 Secret，还要考虑**轮换**，长期不换不安全）；
- 得写一整套部署清单，还要让它**高可用、可靠**；
- 高级校验可能还要去**查询集群里其它对象**（要和 API 打交道，配置变复杂）；
- 还得有**日志、指标、链路追踪**，以及**文档**——说清策略在哪、以后怎么改。

讲者的话很直接：如果你是一个成熟的微服务团队，这些本来就是标配，写一个「X 微服务」不难；但如果只是为了加一条策略就要背负这一切，那**太重了**。

---

## 七、OPA：把策略与代码分离

不想自己写，又想扩展集群，可以用 **OPA（Open Policy Agent）**：它自带一个**实现了这些 Webhook 的 server**，能直接和 apiserver 对话（[【跳转到 29:50】](https://www.youtube.com/watch?v=c6Y35av2BUE&t=1790)）。它收到请求后，用**自己的语言 Rego** 把请求和策略比对，返回决策。

- **缺点**：要**再学一门语言** Rego。
- **优点**：同一套策略可以**复用到很多地方**——比如用它校验节点的 SSH 登录、在业务逻辑里做访问控制，甚至编译成 SQL 用于**数据库访问控制**；而且**策略与代码分离**，可以单独评审、放进版本控制，让不太懂技术的人也能参与评审。

![OPA 不只用于准入：同一套策略可复用到 SSH、业务逻辑甚至数据库访问控制](assets/用准入%20Webhook%20增强集群安全/01826.webp)

讲者展示了一段和前面「镜像前缀校验」**等价**的 Rego 策略：先断言对象是 Pod，取出镜像名赋给变量，判断是否以指定前缀开头，不满足则给出**失败原因**——思路和写代码几乎一样（[【跳转到 32:31】](https://www.youtube.com/watch?v=c6Y35av2BUE&t=1951)）。还有更进阶的例子：用命名空间的注解维护一份 **Ingress 主机白名单**，从而校验某些命名空间下的 Ingress 配置是否合法。

![用 Rego 写策略：等价于镜像前缀校验，但策略可独立于代码管理](assets/用准入%20Webhook%20增强集群安全/01951.webp)

---

## 八、协作边界：准入管「写前」，控制器管「事后」

演讲最后的 Q&A，恰好点破了本讲最该记住的一层关系（[【跳转到 35:51】](https://www.youtube.com/watch?v=c6Y35av2BUE&t=2151)）：

> **提问**：如果策略在白天中途变得更严格了，怎么保证集群里**已经存在的**存量对象也符合新策略？
>
> **回答**：这种情况**你就该用控制器（controller）**。你需要**另一个控制器去定期调谐（reconcile）这些对象**——Webhook 负责「写的那一刻」，而「让存量对象重新对齐新策略」是**控制器**的职责。

换句话说：

- **准入 Webhook 是「门卫」**：只在对象被创建/更新的瞬间检查一次，**不会回头复查**；
- **控制器是「巡检员」**：持续观察现实、把偏差收敛回期望状态。

两者**同属「扩展控制面」的手段，但关注的时间点完全不同**。真正成熟的方案往往是**二者配套**：Webhook 做写前约束与默认注入，控制器做持续校正（OPA/Gatekeeper 正是「Webhook + 定期 reconcile」的组合）。此外，当 Webhook 自己坏掉、导致「连 Pod 都建不出来」时，**回到 `failurePolicy` 的取舍**——想清楚哪种行为对你的集群更合适（[【跳转到 36:16】](https://www.youtube.com/watch?v=c6Y35av2BUE&t=2176)）。

---

## 小结

- **定位**：准入控制器在 apiserver **认证鉴权之后、写入 etcd 之前**拦截「修改对象」的请求；读取不经过它；规则是「**所有**准入控制器都通过才放行」。
- **两支**：**变更准入**（改对象、先执行、串行）与**校验准入**（只判定、可并行）；先后顺序不可颠倒。
- **优先内置**：如 `PodNodeSelector`、`AlwaysPullImages`、`DefaultStorageClass`、`LimitRanger`——大多用来**设默认值**，且刻意克制，以免破坏其它控制器。
- **自研 Webhook**：靠配置对象（`rules` / `clientConfig` / `caBundle` / `namespaceSelector` / `failurePolicy` / `timeout`）+ 一个 HTTPS 回调服务；务必**回填 `uid`**、**写明拒绝理由**、变更用 **JSON Patch**。
- **成本**：自研要背 HTTPS、TLS 轮换、部署、可观测性、文档——团队不成熟时并不划算。
- **OPA**：用 Rego 写策略、**策略与代码分离**、可跨场景复用，代价是学一门语言。
- **协作边界**：**准入管「写前」、控制器管「事后」**；策略中途变严时，存量对象必须靠**控制器**定期调谐。

## 关键术语速查

| 术语 | 一句话解释 |
| :--- | :--- |
| Admission Controller | apiserver 在鉴权后、落库前拦截请求的代码，可变更或校验对象 |
| Mutating / Validating | 变更准入（改对象，先、串行）/ 校验准入（只判定，可并行） |
| `ValidatingWebhookConfiguration` / `MutatingWebhookConfiguration` | 告诉 K8s 如何找到并调用你 Webhook 的配置对象 |
| `clientConfig` | 指定 Webhook 地址：`URL` 或集群内 `service`（须监听 443） |
| `caBundle` | apiserver 校验 Webhook 证书用的 CA；通信强制 HTTPS |
| `failurePolicy` | Webhook 不可用时 `Fail`（拒绝）或 `Ignore`（放行） |
| `AdmissionReview.uid` | 请求/响应的关联标识，响应必须原样回填 |
| JSON Patch | 变更型 Webhook 唯一支持的 patch 格式 |
| `result.reason` | 拒绝原因，供用户排查；自研时务必填写 |
| side effects | Webhook 除改对象外是否还改了外部资源，影响调用保护策略 |
| OPA / Rego | 策略引擎及其策略语言，可让策略与代码分离、跨场景复用 |
| `PodNodeSelector` | 内置变更插件，按命名空间给 Pod 注入 nodeSelector |
