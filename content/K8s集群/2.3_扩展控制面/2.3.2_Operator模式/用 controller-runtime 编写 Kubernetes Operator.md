# 用 controller-runtime 从零编写一个 Kubernetes Operator

## 本讲要解决的核心问题（SCQA）

**背景**：要写 Kubernetes Operator，你有现成的脚手架——Operator SDK、Kubebuilder——它们能按你的 CRD 自动生成一大坨代码，跑起来毫不费力。

**冲突**：但用了脚手架，你往往**并不真的知道引擎盖下发生了什么**。哪天生成的代码报错、`Reconcile` 行为诡异，你只能干瞪眼。

**疑问**：如果不用脚手架，一个 Operator 的最小骨架到底长什么样？从 CRD 到控制器，每一步具体在做什么？

**回答（中心思想）**：Operator = **CRD（定义一种新资源）+ Controller（一个永远运行的循环）**，两者都建立在 `controller-runtime` 之上。只要亲手把一个 `StaticPage` Operator 写一遍——CRD、API 类型、Scheme 注册、Manager、Controller Builder、Reconcile——你就会看清 Kubebuilder 生成的代码其实和你手写的一模一样。真正干活的重活，`controller-runtime` 都替你做了。

> 本讲基于 YouTube 视频《How to write your own Kubernetes Operator in Golang (using controller-runtime)》（sF2Z8IDshRA，约 48 分钟）整理。

---

## 一、起手方式：Operator SDK、Kubebuilder 与手写 controller-runtime

写一个 Operator，其实有多种入口（[【跳转到 00:00】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=0)、[【跳转到 00:25】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=25)）：

- **Operator SDK** 或 **Kubebuilder**：它们是库与二进制包，会**为你生成**上手所需的代码。它们内部都使用 **`controller-runtime`**——一个由 Kubernetes 社区维护、用来和集群交互的 Go 项目。
- **手写 controller-runtime**：不使用任何脚手架，自己用 `controller-runtime` 从头写一个控制器。

讲者特意选择**第三种**（手写），因为用它才看得清机制。理由很直接（[【跳转到 00:50】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=50)、[【跳转到 01:00】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=100)）：先用脚手架，你其实「不知道到底发生了什么」；**先理解 `controller-runtime` 如何工作、如何在 Go 程序里实现它**，之后再用 Kubebuilder / Operator SDK，或干脆自己写，都会踏实得多。

![三种起手方式：Operator SDK、Kubebuilder、以及基于 controller-runtime 的自定义 Controller](assets/用%20controller-runtime%20编写%20Kubernetes%20Operator/00025.webp)

为什么不直接写一个「原生」的 Go Kubernetes 客户端、而去用 `controller-runtime`？（[【跳转到 02:25】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=145)）因为 `controller-runtime` **是在客户端之上的抽象**：它把与 API Server 打交道的样板代码都封装好了，你只需提供连接集群的配置，然后写一个「**当 StaticPage 变化时做点什么**」的函数即可。讲者坦言自己也试过手写客户端，但**不好写、文档也不足**，最后放弃——手写还得自己保证 Kubernetes 版本、`client-go` 版本彼此匹配，而 `controller-runtime` 帮你挡掉了这些细节。

顺带一提，Kubernetes 本质就是 **REST API**：你完全可以用一个 Go HTTP 客户端直接对它发请求、拿回 JSON（[【跳转到 03:00】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=180)、[【跳转到 03:25】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=205)）。拿回 JSON 后放进 Go 结构体，再从结构体读出/写回 API Server——这正是所有客户端库在做的事。

---

## 二、Operator 的两个组成部分：CRD 与 Controller（StaticPage 例子）

一个 Operator 由两部分构成（[【跳转到 01:00】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=60)）：

1. **Custom Resource Definition（CRD）**：定义一种自定义资源，你在这里声明要存哪些字段；
2. **Controller**：你自己写的自定义 Go 代码，被部署成一个 Deployment（其实就是一个跑着 Go 代码的 Pod），通过 Kubernetes API 观察并操作对象。

演示用的例子叫 **StaticPage**：当有人创建一个 `StaticPage` 资源时，控制器就启动一个 **nginx Deployment**，并把一段自定义内容注入进去——本质上就是把这段内容当作 nginx 容器的 `index.html`，访问这个容器就会看到这段消息（[【跳转到 01:25】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=85)、[【跳转到 01:50】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=110)）。

控制器的行为很朴素，恰好把 CRUD 三种情形说清楚（[【跳转到 01:50】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=110)、[【跳转到 02:00】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=120)）：

- 出现一个**新的 StaticPage** → 创建一个新的 nginx 容器；
- StaticPage **被更新** → 更新这个容器；
- StaticPage **被删除**（从 API Server 移除）→ 删掉它对应的 Deployment、Pod。

![Operator 的两个组成部分：CRD 定义自定义资源（StaticPage），Controller 把变化翻译成对 nginx Deployment 的操作](assets/用%20controller-runtime%20编写%20Kubernetes%20Operator/00125.webp)

---

## 三、第一步：CRD 与示例对象

项目有三个目录，第一个就是 YAML 定义——`crd.yaml`，kind 为 `CustomResourceDefinition`（[【跳转到 03:45】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=225)、[【跳转到 04:05】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=245)）。CRD 本身可读性一般，先看它定义出来的**示例对象** `example.yaml` 更直观（[【跳转到 04:05】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=245)）：

```yaml
apiVersion: kubernetes.in4it.com/v1
kind: StaticPage
metadata:
  name: testpage
  namespace: default
spec:
  image: nginx:latest       # 用哪个镜像
  contents: "This is a test" # 注入的 index.html 内容
  replicas: 1                # 副本数
```

- `apiVersion` 要取一个**唯一**的组名，这里是 `kubernetes.in4it.com/v1`；
- `metadata` 与任何普通 Kubernetes 对象一样；
- `spec` 里才是**自定义字段**：`image`、`contents`、`replicas`。

要让这个对象真正可被集群接受，就需要 `crd.yaml`——它是你**第一个 apply 到集群的 YAML**（[【跳转到 04:30】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=270)、[【跳转到 04:55】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=295)）。里面给出组名、版本，并在该版本下声明 `spec` 的字段（contents、image、replicas），以及 `namespaced`、`plural`、`singular`、`kind`、`shortName` 等——都很直白。

![crd.yaml：kind 为 CustomResourceDefinition，声明 StaticPage 的组、版本与 spec 字段](assets/用%20controller-runtime%20编写%20Kubernetes%20Operator/00405.webp)

![example.yaml：一个 StaticPage 实例，spec 里是自定义字段 image / contents / replicas](assets/用%20controller-runtime%20编写%20Kubernetes%20Operator/00430.webp)

**但只有 CRD 什么也不会发生**（[【跳转到 04:55】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=295)）——因为还没有一个控制器去监听 StaticPage 的变化。于是进入第二、第三个目录：`cmd/controller` 与程序要用的 API 类型。

---

## 四、第二步：API 类型、DeepCopy 与 Scheme 注册

在写控制器之前，先准备 `api/v1` 下的三类样板代码。

**（1）API 类型 `staticpage.go`**（[【跳转到 05:05】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=305)、[【跳转到 05:30】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=330)）：因为 API Server 返回的是 JSON，得把它翻译成 Go 结构体。于是定义 `StaticPage` 结构体，其中包含从 API Server 返回的 `spec`（contents、image、replicas）。同时用 `metav1.ListMeta` 和 `TypeMeta` 承载 metadata——**每个 Kubernetes 对象都是这么写的**，所以可以直接照抄这段样板。

**（2）`deepcopy.go`**（[【跳转到 05:50】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=350)、[【跳转到 06:05】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=365)）：因为 `controller-runtime` 的接口要求对象实现 **DeepCopy**。你需要一个深拷贝函数：拷贝这个结构体时，连 `spec` 里的内容也一起深拷贝，而不是共享引用。这段代码不会自动生成，但 **Kubebuilder 能帮你生成**——讲者就是跑了一遍 Kubebuilder 对照它生成的版本写的。

**（3）`register.go`**（[【跳转到 06:30】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=390)、[【跳转到 06:55】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=415)）：里面只有组名和组版本。它的作用是——当你使用 `controller-runtime` 内嵌的客户端时，让这个客户端**知道你的新 Schema**（也就是能识别 StaticPage 这个类型）。`register.go` 本身不做事，你只是需要它的 `AddKnownTypes` 以及那几个常量，供 `main.go` 使用。

![staticpage.go：把 API Server 返回的 JSON 映射为 Go 类型 StaticPage（含自定义的 spec）](assets/用%20controller-runtime%20编写%20Kubernetes%20Operator/00530.webp)

![deepcopy.go：实现 controller-runtime 接口要求的深拷贝方法，Kubebuilder 可自动生成](assets/用%20controller-runtime%20编写%20Kubernetes%20Operator/00605.webp)

---

## 五、第三步：main.go —— Scheme、Manager 与 Controller Builder

接下来是控制器本体（[【跳转到 06:55】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=415)）。它要**永远运行**，并在 StaticPage 被创建、修改、删除时收到通知，然后调用一个函数——这个函数就是 `Reconcile`。

**（1）用 `init()` 建立 Scheme**（[【跳转到 07:30】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=450)、[【跳转到 07:55】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=475)）：`scheme = runtime.NewScheme()`（`runtime` 来自 API Machinery）。Scheme 容纳 Kubernetes 里所有资源类型。随后调用 `AddToScheme`，把 `api/v1` 注册进这个 Scheme——`AddToScheme` 内部其实就是 `schemeBuilder.AddToScheme`，而 `schemeBuilder` 由 `NewSchemeBuilder` 结合 `AddKnownTypes` 构造而来。注册后，你的 Scheme 就「认识」StaticPage 了。

**（2）准备 logger 与 reconciler**（[【跳转到 08:30】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=510)、[【跳转到 08:55】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=535)）：用 `controller-runtime` 提供的 logger（讲者直接从 Kubebuilder 抄了 `zap` 日志配置）；再定义一个 `reconciler` 结构体，它拥有一个 `Reconcile` 方法——**每次 StaticPage 变化，这个方法就会被调用**，它才是控制器的业务逻辑所在。

**（3）`main()` 决定「在哪连接集群」**（[【跳转到 09:05】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=545)、[【跳转到 09:30】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=570)）：控制器可以在两种环境下启动——

- **本地**：存在 `~/.kube/config` 时，用 kubeconfig 构建 config（配合 Minikube 本地跑）；
- **集群内**：Pod 里没有 kubeconfig，改用 `rest.InClusterConfig()`，从挂载的 token 连接。

两种路径都得到 config 后，创建 client set、设置 logger，然后进入 `controller-runtime` 的世界（[【跳转到 10:05】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=605)）：

```go
mgr, _ := manager.New(cfg, manager.Options{Scheme: scheme})
ctrl.NewControllerManagedBy(mgr).
    For(&v1.StaticPage{}).            // 关注的被调谐对象类型
    Complete(&reconciler{Client: mgr.GetClient(), Scheme: mgr.GetScheme(), KubeClient: kubeClient})
```

- `For(...)`：声明**被调谐的对象类型**——任何 StaticPage 的变化都会让我知晓；
- `Complete(...)`：把 reconciler 装配进控制器；
- reconciler 里持有两类客户端：`mgr.GetClient()`（面向 StaticPage 的控制器客户端）与前面建的**通用 client set**（用来操作 Deployment、ConfigMap 等标准对象）。讲者特意把两者分开，因为 `controller-runtime` 的默认 client 只认识 StaticPage。

最后 `mgr.Start(...)` 会启动所有注册的控制器并**阻塞直到 context 被取消**，控制器就此永远运行（[【跳转到 12:05】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=725)）。

![main.go 的 main 函数：manager.New 创建 Manager，ControllerManagedBy/For/Complete 装配控制器](assets/用%20controller-runtime%20编写%20Kubernetes%20Operator/01055.webp)

![main.go：导入 client-go/rest 与 clientcmd，实现「本地 kubeconfig / 集群内 in-cluster」两种连接方式](assets/用%20controller-runtime%20编写%20Kubernetes%20Operator/00755.webp)

---

## 六、第四步：Reconcile —— 从 request 到 Deployment 与 ConfigMap

`Reconcile` 收到的是一个 `request`，其 `namespace` 与 `name` 来自对象的 metadata（[【跳转到 12:30】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=750)、[【跳转到 13:20】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=800)）。整个流程如下。

**（1）用 CRD 客户端 Get 主资源**（[【跳转到 13:40】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=820)）：

```go
var sp v1.StaticPage
err := r.Client.Get(ctx, req.NamespacedName, &sp)
```

取到后，`sp.Spec` 里的 contents/image/replicas 就可以用了。

**（2）处理「删除」**（[【跳转到 14:05】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=845)、[【跳转到 14:30】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=870)）：如果 Get 报错且是 **`IsNotFound`**，说明对象已被删除——此时 `Reconcile` 会再次被触发，你应该**清理此前创建的资源**。

**（3）判断「创建还是更新」**（[【跳转到 14:30】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=870)、[【跳转到 14:55】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=895)）：用 Deployment 客户端 Get 一下同名 Deployment：

- **Get 报 not found** → 属于新建：创建 **ConfigMap**（装 `index.html` 内容）与 **Deployment**（nginx 容器）；
- **Get 成功** → 属于更新：此时做更新（演示里只更了 replicas 和 Deployment，没动 ConfigMap）。

其中创建 ConfigMap / Deployment 用了两个辅助函数 `getConfigMapObject` 与 `getDeploymentObject`（[【跳转到 15:05】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=905)、[【跳转到 15:21】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=921)）：它们用 `corev1.ConfigMap` 与 `apps/v1.Deployment` 这两个 **Go 结构体**，把平时写在 YAML 里的 Deployment/ConfigMap 描述出来，并通过 `volumeMount` 把 ConfigMap 挂到 nginx 的 `/usr/share/nginx/html`（[【跳转到 15:46】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=946)）。

![Reconcile 主体：Get 主资源 → 判断 not found（删除）→ create/update Deployment 与 ConfigMap](assets/用%20controller-runtime%20编写%20Kubernetes%20Operator/01255.webp)

![getDeploymentObject：用 Go 结构体构造 apps/v1.Deployment，等价于手写 YAML](assets/用%20controller-runtime%20编写%20Kubernetes%20Operator/01546.webp)

**（4）三种场景串起来**（[【跳转到 16:46】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=1006)）：

- 第一次 apply（not found）→ 走「创建」分支；
- 再改一次 replicas（found）→ 走「更新」分支；
- 删掉 `example.yaml` → `Reconcile` 被触发，Get 时 not found → 走「清理」分支，用 client 的 Delete 把 Deployment、ConfigMap 删掉，把集群清理干净。

这就是一个能和自定义资源变化交互的**最小控制器**。

---

## 七、本地运行与验证

把控制器跑起来（[【跳转到 16:55】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=1015)）：项目里有 Dockerfile（用于集群内运行）和 README；只要本地有 kubeconfig，就能直接在机器上跑。讲者用 Minikube：macOS 上 `brew install minikube`、`minikube start`，然后先 apply CRD、再启动控制器（`go run start.go`）。

一个有意思的调试技巧（[【跳转到 18:45】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=1125)、[【跳转到 19:20】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=1160)）：可以直接用 **curl** 访问 API Server（带上 `--key/--cert`），不加 CA 时它会返回 JSON 并提示 `system:anonymous is forbidden`——借此能直观看到「kubectl 背后其实就是一次 API 调用」。请求 `apis/kubernetes.in4it.com/v1`，API resource list 会列出对该资源可做的 `get/list/create/patch/delete`（[【跳转到 19:45】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=1185)、[【跳转到 20:20】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=1220)）。

验证闭环（[【跳转到 20:45】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=1245)、[【跳转到 21:20】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=1280)）：

- `kubectl apply -f example.yaml` → 日志立刻打印 `Reconciling StaticPage ... created`；
- `kubectl get staticpages` → 能看到 `testpage`；
- `kubectl get deploy` / `kubectl get pod` → 出现了 `staticpage-testpage` 的 Deployment 与 Pod；
- `kubectl exec` 进 nginx 容器，`/usr/share/nginx/html/index.html` 里正是挂载进去的「This is a test」；
- `kubectl delete` 掉 StaticPage → 控制器把 Deployment、Pod、ConfigMap 一并清理。

---

## 八、部署到集群：Docker 镜像与 RBAC

你不希望控制器一直跑在自己机器上，所以要把它部署进集群（[【跳转到 21:55】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=1315)、[【跳转到 22:20】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=1340)）：`docker build -t <name> .` 构建镜像，再 `minikube image load`（或 `minikube build`、`docker image save`）把镜像导进去。（讲者的 Docker 版本太新，和 `minikube image load` 不兼容，于是改用 save/load 组合。）

`deploy-controller.yaml` 把控制器部署成一个 Deployment，并配好**权限**（[【跳转到 17:45】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=1065)、[【跳转到 22:55】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=1375)）：

- 一个 **ServiceAccount**（控制器以它的身份运行）；
- 一个 **Role / RoleBinding**：访问 Deployment、ConfigMap；
- 一个 **ClusterRole / ClusterRoleBinding**：访问 **StaticPage**（自定义资源是集群级资源，需要 cluster 级权限）。

`kubectl apply -f deploy-controller.yaml` 后，Deployment、ServiceAccount、Role(RoleBinding)、ClusterRole(ClusterRoleBinding) 一起被创建，`kubectl get pods` 能看到控制器 Pod；日志里是 `StaticPages up to date`。再删除 StaticPage，可以看到控制器把一切清理干净。

![deploy-controller.yaml：部署含 ServiceAccount 与 RBAC 的控制器](assets/用%20controller-runtime%20编写%20Kubernetes%20Operator/01796.webp)

---

## 九、版本兼容与代码生成器

**`controller-runtime` 帮了大忙**（[【跳转到 24:20】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=1460)）：真正需要手写的代码其实不多，重活都是这个包在做。但**为每个 CRD 字段手写这套 Go 代码仍然很费事**——contents、image、replicas，每加一个字段都要改一遍。

这正是 **Kubebuilder / Operator SDK** 的价值所在（[【跳转到 24:45】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=1485)、[【跳转到 25:20】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=1520)）：每次更新 CRD，它们能**自动生成/重新生成**这些代码。讲者拿 Kubebuilder 生成的项目对照，发现里面的 `manager.Start`、reconciler 装配、`controllerManagedBy/For/Complete` 等**与手写版本如出一辙**——只是多了些自动生成工具，省去你亲手维护的功夫。所以你可以自行取舍：想要完全掌控代码，就手写；图省事，就用生成器。

最后一个高频坑是**版本匹配**（[【跳转到 26:10】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=1570)、[【跳转到 27:20】](https://www.youtube.com/watch?v=sF2Z8IDshRA&t=1640)）：`controller-runtime` 与 `client-go` 的版本要和**集群版本**对得上，否则可能报错或告警。讲者用的 client 版本是 1.30，和 Minikube 版本接近，所以能跑通。`client-go` 的 GitHub 项目里有一张矩阵，说明「哪个 client 版本对应哪个 Kubernetes 版本」；这套版本差异报错在网络 issue 里非常常见（你的 `kubectl` 与 server 版本差异过大时也会报类似错误）。因此维护项目时要同步更新 `go.mod` 里的 Go 与 Kubernetes 版本。

![controller-runtime 承担了大部分重活：真正手写的代码不多；Kubebuilder 则在此基础上自动生成这些代码](assets/用%20controller-runtime%20编写%20Kubernetes%20Operator/02446.webp)

---

## 小结

- **Operator = CRD + Controller**：CRD 定义新资源，Controller 是一个永远运行、监听该资源变化的循环。
- **`controller-runtime` 是核心**：它封装了与 API Server 打交道的样板，你只需配置连接并写一个 `Reconcile` 函数。
- **三类样板代码**：API 类型（JSON↔Go 结构体映射）、`DeepCopy`（接口要求）、`register`（把类型注册进 Scheme）。
- **`main.go` 的三件事**：建立 Scheme、选本地 kubeconfig 或 in-cluster 连接、用 `Manager` + `ControllerManagedBy/For/Complete` 装配并启动控制器。
- **`Reconcile` 的通用骨架**：Get 主资源 → 判断 `IsNotFound`（清理）→ 否则 create/update 子资源（Deployment、ConfigMap）。
- **本地与集群**都可运行：本地用 kubeconfig，集群内用 in-cluster 配置；集群部署需要 ServiceAccount 与 RBAC。
- **版本要对得上**：`controller-runtime` / `client-go` 与集群版本需匹配。
- **脚手架与手写不矛盾**：Kubebuilder / Operator SDK 生成的代码，与手写版本几乎一致；先懂机制，再用生成器。

---

## 关键术语速查

| 术语 | 一句话解释 |
| :--- | :--- |
| Operator SDK / Kubebuilder | 按 CRD 自动生成 Operator 代码的脚手架，底层都用 controller-runtime |
| controller-runtime | Kubernetes 官方控制器开发库，封装与 API Server 的交互并驱动 Reconcile |
| CRD | CustomResourceDefinition，向 API Server 注册一种新的自定义资源类型 |
| StaticPage | 本例的自定义资源：声明 image / contents / replicas，控制器据此创建 nginx |
| api/v1（类型包） | 存放 Go 结构体定义、DeepCopy、register 的包 |
| Scheme | 把 Group/Version/Kind 与 Go 类型关联，让客户端能识别你的自定义类型 |
| DeepCopy | 对象的深拷贝方法，controller-runtime 接口要求实现 |
| Manager | 创建并管理控制器的对象，负责启动、缓存与生命周期 |
| For / Complete | Controller Builder 的两个方法：声明被调谐对象类型、装配 reconciler |
| Reconcile | 控制器核心方法，输入 request(namespace/name)，读主资源并收敛子资源 |
| in-cluster config | Pod 内用挂载的 token 连接 API Server 的方式（本地则用 kubeconfig） |
| RBAC（Role/ClusterRole） | 控制器访问 Deployment/ConfigMap（Role）与自定义资源（ClusterRole）的授权 |
