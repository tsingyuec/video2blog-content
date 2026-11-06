# Kubebuilder 准入 Webhook 实战：给你的 Operator 加上默认值与校验

## 本讲要解决的核心问题（SCQA）

**背景**：在上一讲的 Operator 里，你已经写出一个控制器，能把自定义资源（CR）`Ghost` 调谐成 Deployment、Service 等子资源——它已经会「做事」了。

**冲突**：但控制器是**异步**的。用户如果把 CR 写错（比如把副本数写成 1000，或者干脆不写），控制器只会**照单全收**，等资源炸了才知道。你希望在对象被系统接受**之前**就能**补默认值、挡掉非法值**。可一想到手写准入 Webhook 要处理证书、配置、路径……又觉得不值当。

**疑问**：在一个**已经存在**的 Operator 项目里，能不能用 Kubebuilder 最省事地加上「默认值 + 校验」的准入 Webhook？它和原来的控制器怎么共处？

**回答（中心思想）**：可以。`kubebuilder create webhook` 会一次性脚手架生成两块占位逻辑——`defaulting`（变更型 mutating）与 `programmatic validation`（校验型 validating），并复用 **cert-manager** 自动注入证书。关键是理解这套分工：**Webhook 负责让进入系统的 CR 先「合法」（补默认、拒非法），控制器负责把合法 CR 调谐成真实资源**；而且它们**共用同一个 Manager 进程**——一个管「写前」，一个管「事后」，一前一后协作。下面从头走一遍。

> 本讲基于 YouTube 实操教程《Kubernetes Admission Webhooks - Kubebuilder Tutorial》（`bOalXo21fF4`，约 21 分钟）整理。视频承接上一期「幽灵 Operator」项目，属于动手课。

---

## 一、准入控制器与动态准入控制

**准入控制器（Admission Controller）**：它是**拦截 apiserver 请求**的代码——在**认证、鉴权之后**，在对象**写入 etcd 之前**介入（[【跳转到 01:10】](https://www.youtube.com/watch?v=bOalXo21fF4&t=70)）。按能力分三种：**只会变更、只会校验、或两者兼具**。

- **变更准入（mutating）**：请求进来后看字段，**新增字段、改值、追加元素**——例如更新时补上「最后修改时间戳」，再落库；
- **校验准入（validating）**：看对象、决定**是否拒绝**，不改对象。

K8s 自带一批由 **API Machinery** 维护的准入插件；某个集群开了哪些，取决于 apiserver 的 **`--enable-admission-plugins`** 参数（[【跳转到 02:00】](https://www.youtube.com/watch?v=bOalXo21fF4&t=120)）。

在编译进 apiserver 的内置插件之外，还有一套**动态准入控制（Dynamic Admission Control）**：由 `MutatingAdmissionWebhook` 与 `ValidatingAdmissionWebhook` **两个插件**启用，让我们**自己写 Webhook** 接入自定义的变更与校验逻辑（[【跳转到 02:50】](https://www.youtube.com/watch?v=bOalXo21fF4&t=170)）。

它的模型很简单：**你写一个 HTTP 服务**，apiserver 像**回调**一样问它——「你要改这个对象吗？」「这个对象合法吗？」——服务给个答复即可。这个服务**可以跑在集群内，也可以跑在集群外**；若跑在集群内，就能用 **cert-manager** 这类云原生工具**自动注入 SSL 证书**，保证与 apiserver 的通信安全（[【跳转到 03:15】](https://www.youtube.com/watch?v=bOalXo21fF4&t=195)）。

---

## 二、动态准入的调用顺序

动态准入在一次写请求里的**顺序**非常讲究（[【跳转到 04:05】](https://www.youtube.com/watch?v=bOalXo21fF4&t=245)）：

1. 用户 create / update / delete 一个资源 → 请求进入 **kube-apiserver**；
2. **认证、鉴权**；
3. **动态准入控制器先调用「变更 Webhook」**——因为「先改、再验」才合理，不能校验完又去改对象；
4. 双方通过 **`AdmissionReview`** 对象通信：请求是 `AdmissionReview request`，回复是 `AdmissionReview response`，**响应里可带着 patch**（描述如何变更）；
5. 接着做**schema 校验**——即 CRD 的 **OpenAPI schema 校验**（比如「这个字段必须匹配某正则」「最小值为 1」）；
6. 再做**校验 Webhook**（同样是 `AdmissionReview` 请求/响应）；
7. 全部通过后，才把对象**写入 etcd**。

![动态准入顺序：变更 Webhook → schema 校验 → 校验 Webhook → 写入 etcd](assets/Kubebuilder%20准入%20Webhook%20实战/00245.webp)

记住这个顺序：**schema 校验夹在「变更」与「校验」两个 Webhook 之间**——这也解释了为什么 Kubebuilder 的字段约束（marker）能自动变成 CRD 里的 schema 校验。

---

## 三、用 Kubebuilder 给 Operator 生成 Webhook 骨架

准备阶段先装好 `kubebuilder`、`go` 和 `k9s`，然后**克隆上一期的 ghost operator 项目**——也就是说，我们是在**已有的 Operator 项目里加 Webhook**（[【跳转到 03:38】](https://www.youtube.com/watch?v=bOalXo21fF4&t=338)）。

给 Webhook 生成脚手架只需一条命令，关键是把 **GVK（Group-Version-Kind）** 和两个开关告诉它（[【跳转到 06:40】](https://www.youtube.com/watch?v=bOalXo21fF4&t=400)）：

- `--defaulting`：生成**默认值/mutating** Webhook（给 CR 设默认值）；
- `--programmatic-validation`：生成**校验/validating** Webhook（执行你的校验逻辑）。

![kubebuilder create webhook：指定 GVK，并用 --defaulting / --programmatic-validation 决定生成哪种 Webhook](assets/Kubebuilder%20准入%20Webhook%20实战/00400.webp)

命令会顺手执行 `make generate`，在 `api/v1/` 下生成 `ghost_webhook.go` 和对应的测试文件。生成物里已经给我们留好了**占位函数**：默认值逻辑、以及**创建/更新/删除**时的校验逻辑（[【跳转到 07:30】](https://www.youtube.com/watch?v=bOalXo21fF4&t=450)）。

---

## 四、先加一个字段：schema 校验自动生成

为了有东西可校，先给 CR 的 `spec` 加一个字段 **`replicas`**（[【跳转到 08:20】](https://www.youtube.com/watch?v=bOalXo21fF4&t=500)）。加完后跑 `make manifests` 重新生成 CRD——Kubebuilder 的 **marker** 会**自动翻译成 CRD 里的 schema 校验**：`replicas` 必须是整数、且**至少为 1**。

也就是说，「字段类型 / 取值范围」这类**结构性约束**，不用写任何 Webhook 代码，Kubebuilder 会放进 CRD 的 OpenAPI schema 里，由 apiserver 的 schema 校验兜住（[【跳转到 09:10】](https://www.youtube.com/watch?v=bOalXo21fF4&t=550)）。

![make manifests 把 Kubebuilder marker 翻译成 CRD 里的 schema 校验（replicas: integer, minimum 1）](assets/Kubebuilder%20准入%20Webhook%20实战/00550.webp)

---

## 五、控制器也要跟着改：把 replicas 用起来

新增了字段，原来的**控制器逻辑必须跟上**，否则 `replicas` 只是摆设。需要改**两处**（[【跳转到 09:35】](https://www.youtube.com/watch?v=bOalXo21fF4&t=575)）：

1. **生成期望的 Deployment spec 时**：把写死的副本数替换为读 `spec.replicas`；
2. **更新判断条件里**：原来只在**镜像变化**时更新托管 Deployment，现在要改成**镜像变化或 `replicas` 变化**时才更新——否则用户改了副本数，控制器不会动。

改完 `make` 重新编译控制器（首次编译较慢）。这一步点明了一个重要关系：**准入 Webhook 只是让 CR「合法」，真正把 CR 变成资源、并跟随其变化的是控制器**——两者靠同一个 CR 的字段「对接」。

---

## 六、实现 defaulting 与 validating 逻辑

接着把生成的两个占位函数填上逻辑（[【跳转到 11:02】](https://www.youtube.com/watch?v=bOalXo21fF4&t=662)）：

- **defaulting（变更）**：如果 `replicas` 为 0（或空 / null 被转成 0），就**默认设为 2**；
- **validating（校验）**：复用同一个判断函数，如果 `replicas > 5` 就**返回错误**，请求被拒。

Kubebuilder 会**自动把 defaulting 结果生成 JSON Patch**，你不用自己拼 patch（回想上面第 2 步，响应里带的就是 patch）。校验函数返回**警告（warnings）与错误（errors）**：出问题时返回错误信息，用户就能看到被拒原因。

另一个由 marker 负责的细节是 **Webhook 的路径/端点**：变更 Webhook 的路径形如 `mutate.log.example.com/v1/ghost`，校验的形如 `validate...`；跑 `make manifests` 时，这些 marker 会被映射进 YAML，其中**变更在 create 和 update 时触发、校验也在 create 和 update 时触发**（[【跳转到 12:17】](https://www.youtube.com/watch?v=bOalXo21fF4&t=737)）。

![defaulting 设为 2、validating 拒绝大于 5，Kubebuilder 自动生成 JSON Patch](assets/Kubebuilder%20准入%20Webhook%20实战/00687.webp)

![Kubebuilder marker 定义 Webhook 的路径与触发操作，并落到 manifest 里](assets/Kubebuilder%20准入%20Webhook%20实战/00762.webp)

---

## 七、装配：cert-manager 自动注入 caBundle

Webhook 要能被 apiserver 以 HTTPS 调用，就得有证书。这里用 **cert-manager** 自动处理（[【跳转到 13:57】](https://www.youtube.com/watch?v=bOalXo21fF4&t=837)）：

- 生成的清单里有个 **`service`**，它就是 Webhook 的服务入口，**监听 443**，并且由**同一个 Manager** 提供（下面会看到，控制器和 Webhook 是同一个进程）；
- 需要在 `config/default` 和 `config/crd` 的 customization 里，把标注了 **cert-manager** 的段落**取消注释**——这样 cert-manager 才能**注入 CA bundle**；
- 跑 `make manifests` 重新渲染清单，再用 `make install-cert-manager` **安装 cert-manager**（它是第三方组件，Kubebuilder 不自带）。

cert-manager 自己其实也用了 Webhook（挺有意思的「自举」），但我们真正关心的是它的 **ca-injector**：**把 CA bundle 注入我们 Webhook 的配置里**（[【跳转到 15:37】](https://www.youtube.com/watch?v=bOalXo21fF4&t=937)）。

---

## 八、部署与验证

最后：设置镜像 tag、**构建并推送镜像**（视频里用 `ttl.sh` 这个匿名临时镜像仓库图省事），再 `make deploy` 把整个 Operator（含新 Webhook）部署上去（[【跳转到 16:02】](https://www.youtube.com/watch?v=bOalXo21fF4&t=962)）。

验证分三步：

1. **看状态**：用 `k9s` 进入 `operator-tutorial-system` 命名空间，确认 Manager 正在运行；查看集群里的 **mutating / validating webhook configuration** 都已生成。
2. **验默认值**：建一个 `marketing` 命名空间，应用一份**不写 `replicas`** 的 `Ghost` 样例。查托管的 Deployment——**副本数变成了 2**；`kubectl describe` 一下 `Ghost`，它的 `spec.replicas` 也是 **2**。说明 **defaulting Webhook 生效了**（[【跳转到 18:18】](https://www.youtube.com/watch?v=bOalXo21fF4&t=1098)）。
3. **验校验**：把 `replicas` 改成明显非法的值（如大于 5）再 apply，立刻报错 **`denied: ghost replicas cannot be more than five`**——**validating Webhook 生效了**（[【跳转到 19:16】](https://www.youtube.com/watch?v=bOalXo21fF4&t=1156)）。

![默认值验证：样例没写 replicas，Deployment 与 Ghost 的 replicas 都变成了 2](assets/Kubebuilder%20准入%20Webhook%20实战/01123.webp)

![校验验证：replicas 非法时被拒，错误信息为「cannot be more than five」](assets/Kubebuilder%20准入%20Webhook%20实战/01161.webp)

最后回到命名空间看看 **services**：Webhook service 指向的正是 **Manager**——这再次印证了**控制器与 Webhook 是同一个 Manager 进程**：**控制器负责调谐，Webhook 负责把关**，只是触发时机不同（[【跳转到 19:46】](https://www.youtube.com/watch?v=bOalXo21fF4&t=1186)）。

---

## 小结

- **两种 Webhook**：变更（defaulting，改对象、先执行）与校验（validating，只判定）；它们与内置插件同属准入控制器。
- **调用顺序**：变更 Webhook → **schema 校验** → 校验 Webhook → 写入 etcd。
- **两条约束路径**：**结构性约束**（类型、范围）交给 CRD 的 **OpenAPI schema**（Kubebuilder marker 自动生成）；**业务性约束**（如「大于 5 就拒」）写进 **Webhook 逻辑**。
- **脚手架**：`kubebuilder create webhook` 用 `--defaulting` / `--programmatic-validation` 一次生成两块逻辑与空壳。
- **控制器要联动**：新增字段后，控制器要读它、并在字段变化时触发更新——**准入负责「合法」，控制器负责「落地」**。
- **证书**：集群内 Webhook 用 **cert-manager + ca-injector** 自动注入 caBundle，省去手工管理证书。
- **共处一 Manager**：控制器与 Webhook 在**同一个进程**里，Webhook service 指向 Manager——「写前把关」与「事后收敛」由同一个组件承担。
- **验证闭环**：默认值（不写 replicas → 2）与校验（replicas 超限 → 拒绝并给出理由）都要实测。

## 关键术语速查

| 术语 | 一句话解释 |
| :--- | :--- |
| Admission Controller | apiserver 在鉴权后、落库前拦截请求的代码；可变更或校验 |
| Dynamic Admission Control | 由两个 Webhook 插件启用的自定义准入机制 |
| Mutating / Validating Webhook | 变更型 / 校验型自定义准入回调服务 |
| `AdmissionReview` | apiserver 与 Webhook 交换的请求/响应对象，响应可含 patch |
| JSON Patch | 变更型 Webhook 返回改动的方式，由 Kubebuilder 自动生成 |
| OpenAPI schema 校验 | CRD 里基于字段类型/范围的校验，夹在变更与校验 Webhook 之间 |
| Kubebuilder marker | 标注字段约束与 Webhook 端点，`make manifests` 时翻译成 YAML |
| `kubebuilder create webhook` | 生成 defaulting / validating 占位逻辑的脚手架命令 |
| cert-manager / ca-injector | 自动签发证书并把 caBundle 注入 Webhook 配置 |
| Manager | controller-runtime 的进程骨架，同一进程里托管控制器与 Webhook |
| `failurePolicy` | Webhook 不可用时 `Fail`（拒绝）或 `Ignore`（放行） |
