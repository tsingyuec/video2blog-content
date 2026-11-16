# Webhook 三种类型与开发路径

## 本讲要解决的核心问题（SCQA）

**背景**：写 Operator 时，你迟早会遇到「创建 CR 之前想拦一道」的需求——比如某个字段超出上限就拒绝，或者用户漏填的字段要自动补个默认值。

**冲突**：这些需求听起来用 **CRD 自带的字段校验**（`minimum` / `maximum` / `enum` 之类）就能搞定。但真做起来会发现一个天花板：CRD 的校验是**静态**的，写死在 YAML 里，它**读不到集群当下真实状态**。可现实中很多规则偏偏是动态的——例如「某字段不能超过当前命名空间里已有的 Pod 数」，这个上限随环境而变，YAML 里根本写不出来。

**疑问**：K8s 到底提供了什么机制来补上这块？它有几种形态？又该怎么用代码把它们搭起来？

**回答（中心思想）**：这个机制就是 **Webhook**——它本身是 **K8s 的一个内置资源**，分 **Mutating（改）** 与 **Validating（校验）** 两大类动作，另外还有一类专做版本转换的 **Conversion**。日常开发不必从零手写，用 **Kubebuilder** 一条 `create webhook` 命令就能把三种类型的代码骨架搭出来；真正要记住的，是「**它只绑定到某个资源**」以及「**group 与 domain 不是一回事**」这两个关键点。

> 本讲基于 B 站视频《【云原生入门】43.Webhook 介绍》（BV1QbBRBvEqm）整理。视频以 Kubebuilder 工程为主线，演示了 Webhook 脚手架的生成与几个实用的踩坑点。

---

## 一、Webhook 是 K8s 的内置资源，而且不止一种

在云原生开发里，除了 Operator 开发，另一个绕不开的点就是 **Webhook 开发**。我们平时说的「Webhook」其实是个缩写，全称比较长；而它落到 K8s 里，**本身就是一个内置资源**——我们要做的，就是「基于这个资源进行开发」（[【跳转到 00:25】](https://www.bilibili.com/video/BV1QbBRBvEqm/?t=25)）。

视频一上来就在代码里 `grep WEBHOOK`，一下就能搜到**两种** Webhook：

![在代码里 grep 出两种 Webhook：mutating 与 validating](assets/Webhook%20三种类型与开发路径/00000.webp)

一种是 **mutating**，一种是 **validating**。顾名思义——**一种专门用来做修改，另一种专门用来做校验**（[【跳转到 00:50】](https://www.bilibili.com/video/BV1QbBRBvEqm/?t=50)）。先记住这两类动作的分工，后面再看它们各自的适用场景。

## 二、为什么要在 CRD 之外再加 Webhook：静态校验的天花板

先看 **Validating（校验）**。假设我们创建了一个 CR，其中某些字段需要校验。这件事其实有两条路：

- **CRD 的静态校验**：在创建 CRD 时就把规则写进 schema，比如某字段的 `minimum`、`maximum`、`maximumLength` 等；
- **Webhook 动态校验**：把判断逻辑写进 Webhook 代码里。

静态校验的**限制**很明确：**它没法动态获取当前集群的信息**（[【跳转到 01:15】](https://www.bilibili.com/video/BV1QbBRBvEqm/?t=75)）。视频举了一个很有代表性的场景：假设有个字段叫 `size`，它的取值**不能超过当前某个命名空间下的 Pod 数**——「这个命名空间最多能有多少 Pod、现在已经有多少」，这个上限值取决于**当前集群环境**，是动态的，没法在 CRD 的 YAML 定义里表达出来（[【跳转到 01:40】](https://www.bilibili.com/video/BV1QbBRBvEqm/?t=100)）。

![CRD 静态校验读不到集群实时状态，动态规则要交给 Webhook](assets/Webhook%20三种类型与开发路径/00075.webp)

这时就可以用 **Validating Webhook**：加一个 Webhook，在它的逻辑里做你想要的任何场景处理——它**能实时查询集群状态**，比静态规则灵活得多。

## 三、另一类：Mutating 负责「改写与补默认值」

再看 **Mutating（修改）**。典型场景是：创建某些 CR 时字段很多，用户往往只填了一部分。对于没给值的字段，你可能需要**赋一个默认值**；对于某些值，可能还要**根据当前环境做一些调整**（[【跳转到 02:30】](https://www.bilibili.com/video/BV1QbBRBvEqm/?t=150)）。这些「改」的动作，就是 Mutating Webhook 的职责。

![Mutating 负责补默认值、按环境改写字段](assets/Webhook%20三种类型与开发路径/00150.webp)

既然需要这种**灵活配置**，就必然得**自己写代码去实现复杂逻辑**——这也就引出了「Webhook 开发」这件事。

## 四、用 Kubebuilder 搭骨架：三条 flag，对应三种 Webhook

和创建 Operator 一样，我们不可能从零手写。之前讲过的 **Kubebuilder** 框架，除了能搭 Operator，也能**给 Webhook 搭框架**（[【跳转到 02:55】](https://www.bilibili.com/video/BV1QbBRBvEqm/?t=175)）。执行 `kubebuilder create` 时，它既支持创建 API（也就是你的 CRD），也支持创建 **webhook**，从而把对应的逻辑代码架子搭出来。

用 `create webhook` 时，有几个**必填字段**必须注意：因为 **Webhook 一定是针对某一个资源做修改/校验**，所以你必须**绑定具体资源**，即指定它的 **group、version、kind**（[【跳转到 05:25】](https://www.bilibili.com/video/BV1QbBRBvEqm/?t=325)）。

![create webhook 必须绑定 group / version / kind](assets/Webhook%20三种类型与开发路径/00350.webp)

后面的 flag 参数则决定生成**哪种类型**的 Webhook 框架，一共支持三种（[【跳转到 05:50】](https://www.bilibili.com/video/BV1QbBRBvEqm/?t=350)）：

| flag 分类 | 生成的 Webhook | 说明 |
| :--- | :--- | :--- |
| `default` | **Mutating** | 修改类，负责补默认值、改写字段 |
| `validation` | **Validating** | 校验类，负责放行或拒绝 |
| `conversion` | **Conversion** | 多版本 CRD 之间的字段转换 |

其中 **Conversion 其实也算一种 Mutating**（它也会改对象），只不过 Kubebuilder 专门为它单列了一类：比如用户创建的是 `v1`，你实际可以把它转换成 `v2`，两个版本之间某个字段名不一致或有其它转换逻辑时，就在这里做（[【跳转到 06:40】](https://www.bilibili.com/video/BV1QbBRBvEqm/?t=400)）。日常使用中，**我们主要用 `default` 和 `validation` 这两种**。

## 五、一个容易踩的坑：group 与 domain 不是一回事

创建 Webhook 时唯一要特别留意的点，是 **group 参数**。这里的 `group` **不是** K8s 里真正的 group 概念，而是 **Kubebuilder 视角下的 group**（[【跳转到 08:20】](https://www.bilibili.com/video/BV1QbBRBvEqm/?t=500)）。

具体来说：还记得初始化项目时的 **domain** 吗？**真正在 K8s 中生效的 group，是「Kubebuilder 里指定的 group」拼接上「domain」**。这两个合在一起，才是我们在 K8s 中看到的那个 group。

![Kubebuilder 的 group 只是实际 group 的一部分，还要拼上 domain](assets/Webhook%20三种类型与开发路径/00600.webp)

这些信息其实都写在 Kubebuilder 框架的 **`PROJECT` 文件**里（它把项目信息描述得很详细）。所以创建时的规则是：**用框架创建时，`group` 传的应该是 Kubebuilder 认为的那个 group（少一个 domain），而不是 K8s 里真正的 group**。拿不准就翻 `PROJECT` 文件——那里写的是什么，创建时就写什么（[【跳转到 09:10】](https://www.bilibili.com/video/BV1QbBRBvEqm/?t=550)）。

## 六、搭出来的东西长什么样

以 `validation` 为例，回车之后，Kubebuilder 会在 `internal` 目录下生成 Webhook 的代码框架：可以看到 `controller` 目录旁边多了一个 **`webhook`**，以及一个**版本目录**（就是你设置好的 CRD 版本），实际的初始化代码就在里面（[【跳转到 10:00】](https://www.bilibili.com/video/BV1QbBRBvEqm/?t=600)）。

对**校验**来说，框架默认给你搭好了在 **创建 / 更新 / 删除**三种时机做校验的架子，你只要在对应方法里实现逻辑即可。之后执行 **`make manifest`**，它会在 `config` 下生成对应的 YAML，里面包含你创建的 Webhook 对应的 **GVK**、**路径（path）**等定义——path 既可以在创建时用参数指定，也可以后续直接改 YAML（[【跳转到 10:50】](https://www.bilibili.com/video/BV1QbBRBvEqm/?t=650)）。

## 七、中途想补另一种类型？删干净再重建

视频最后演示了一个很实用的怪癖。假设你一开始只创建了 `validation`（Validating）的 Webhook，后来才想起来还要加一个 `default`（Mutating）的。这时**直接追加 flag 会报错**，提示不能注入，因为 **Webhook 已经存在了**（[【跳转到 12:05】](https://www.bilibili.com/video/BV1QbBRBvEqm/?t=725)）。

它的校验逻辑是：**只要发现 `PROJECT` 文件里已经有 Webhook（哪怕是不同类型），就直接拒绝**。你可能会想「那把 `PROJECT` 里那条删了不就行了」——**不行**，因为**它还会校验 `internal` 目录下实际生成的 Webhook**，于是又被拒（[【跳转到 12:55】](https://www.bilibili.com/video/BV1QbBRBvEqm/?t=775)）。

正确的做法是**把两处都删干净**：既删 `PROJECT` 里的 Webhook 条目，也删 `internal` 下生成的 Webhook 目录。只有当**这两处都不存在**时，它才认为你「从没创建过」，于是允许你重新创建——这时**一次性把两个 flag 都带上**，它就会把两种类型的框架**合并**在一起生成（[【跳转到 13:45】](https://www.bilibili.com/video/BV1QbBRBvEqm/?t=825)）。

![两处都删净后再重建，可用一条命令同时生成两种类型的 Webhook](assets/Webhook%20三种类型与开发路径/00850.webp)

> 经验法则：**想清楚要几种，就一次性带齐几个 flag**；中途追加很麻烦，必须先「删干净再重建」。

## 八、小结与记忆锚点

- **Webhook 是 K8s 的内置资源**，我们「基于这个资源做开发」，而不是发明新概念。
- **两类动作 + 一类转换**：`Mutating`（改）/ `Validating`（校验）/ `Conversion`（多版本转换，也算一种改写）。
- **它补的是静态校验的短板**：CRD 的 schema 校验读不到实时集群状态，动态规则（如「不超过当前 Pod 数」）只能交给 Webhook。
- **开发走 Kubebuilder**：`create webhook` + 绑定 `group/version/kind` + 选 `default` / `validation` / `conversion`，即可搭出骨架。
- **两个关键点**：① Webhook **只针对某个资源**；② 传 `group` 时用的是 **Kubebuilder 的 group（不含 domain）**，真正的 group = group + domain。
