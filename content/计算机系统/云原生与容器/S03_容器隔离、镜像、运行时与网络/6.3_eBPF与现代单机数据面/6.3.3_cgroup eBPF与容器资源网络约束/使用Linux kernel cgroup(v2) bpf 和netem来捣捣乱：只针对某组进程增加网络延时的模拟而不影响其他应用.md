# 使用 Linux kernel cgroup(v2) bpf 和 netem 来捣捣乱：只针对某组进程增加网络延时的模拟而不影响其他应用

> 本文整理自 B 站视频《使用 Linux kernel cgroup(v2) bpf 和 netem 来捣捣乱：只针对某组进程增加网络延时的模拟而不影响其他应用》。它不满足于上一期的「针对某个 IP 加延时」，而是更进一步——**只让某一组应用（某个 cgroup 里的进程）的网络访问变慢，同一台机器上其它应用完全不受影响**。全文沿「为什么能针对一组应用 → 关键机制 priority 与 classid 的暗号 → cgroup BPF 程序怎么写 → 怎么搭 qdisc 树验证」展开。

## 本讲要解决的核心问题（SCQA）

**背景**：上一期视频已经演示过，在一张网卡上挂一棵 qdisc 树，再用 BPF 写的 filter 按包的 IP 分流，就能把「某个 IP 的包」导进 netem，人为地制造模拟网络延时。

**冲突**：按 IP 分类实在太粗了——同一台机器上不同应用的包，出口 IP 常常是一样的；而真实测试里更常见的需求恰恰是「按应用区分」。难道只能把应用塞进容器、再单独给它一个 IP 吗？那样既麻烦、又要求应用能被容器化。

**疑问**：能不能**不改应用、也不给它单独的 IP**，就直接让「某一个 cgroup 里的所有进程」发出的网络包统统变慢，而其它进程毫发无损？

**回答（中心思想）**：能，核心就一句话——**cgroup 的 BPF hook 允许在进程调用 `socket()` 建立套接字时改写这个 socket 的 `priority` 字段；而 tc 默认 filter 会把 `priority` 当作 `classid` 来给包分类**。于是只要「BPF 把 priority 写成 `1:ffff`」＋「qdisc 树里恰好有一个 classid 为 `1:ffff` 的 class 挂着 netem」两个值对上暗号，这个 cgroup 里所有 socket 发出的包就会自动拐进延时 class；其它包继续走默认路径，感知不到任何变化。

[【跳转到 00:00】](https://www.bilibili.com/video/BV1C14y187Wx/?t=0)

---

## 一、先回顾：上一期是怎么按 IP 制造延时的

[【跳转到 00:05】](https://www.bilibili.com/video/BV1C14y187Wx/?t=5)

上一期讨论了 Linux 网络里「网络包调度」的一些模块和用法，做法是在某张网卡上挂一个 qdisc（排队规则），再挂一个用 BPF 写成的 filter：

- 这段 BPF 程序做的事情很简单：**分析包的 IP**；
- 如果这个 IP 正是我想针对的，就让它往「特殊分支」走；
- 如果不是，就走正常路径。

[【跳转到 00:30】](https://www.bilibili.com/video/BV1C14y187Wx/?t=30)

那个「特殊分支」里用到的延时模块，就是内核里的 **netem**——它是网络包调度管理的一个功能模块，本身实现挺复杂。所以想加延时的时候，与其自己从头实现一个，不如直接复用 netem：你只要把包导到它这儿，它就替你产生延时、丢包之类的现象。

![qdisc 树的基本结构：根节点下挂着 class，其中产生延时的那一支再挂 netem，最终连到网卡驱动](<assets/使用Linux kernel cgroup(v2) bpf 和netem来捣捣乱：只针对某组进程增加网络延时的模拟而不影响其他应用/00055.webp>)

---

## 二、把「针对一个 IP」升级成「针对一组应用」

[【跳转到 00:55】](https://www.bilibili.com/video/BV1C14y187Wx/?t=55)

**先给结论：按 IP 分类非常简单，简单到甚至不需要 BPF**——tc 里默认就有一堆 filter 就能干这件事。所以这一期不再针对某个 IP，而是想针对**某一个应用**：希望某一组应用在进行网络访问时产生延时，但别的应用完全不受影响。

[【跳转到 01:20】](https://www.bilibili.com/video/BV1C14y187Wx/?t=80)

要产生延时，仍然得靠 netem，所以还是要在这张网卡上挂一棵树：

- 树上分几个 **class（分类）**；
- 其中某一个 class 负责「制造 delay」。

[【跳转到 01:45】](https://www.bilibili.com/video/BV1C14y187Wx/?t=105)

那「怎么把话说到某一组应用头上」呢？视频里给了两条路：

1. **容器方案**：用容器把这组应用管理起来，给容器一个独立的出口 IP，然后沿用「按 IP 过滤」的老办法。可行，但你必须把应用封装成一个 container、并让它有自己出口的虚拟 IP。
2. **eBPF cgroup hook 方案（本期主角）**：利用 eBPF 在 cgroup 上的 hook，**针对某一个 cgroup 里的所有应用**做处理——这个 cgroup 里的应用做网络操作时，我给它的包打上一些标志；这样这个 cgroup 里发出的包就都带上这个标志。

[【跳转到 02:10】](https://www.bilibili.com/video/BV1C14y187Wx/?t=130)

一旦「这个 cgroup 里发出的包都带上标志」，这些包在到达网卡之前就可能先去走一下那棵 qdisc 树；这个标志如果被识别出来，就让它往延时分支走，从而实现「这一类包统统产生 delay」；其余没有这个标志的包，照常走正常路径。

这样，就能针对某一组应用做这件事了。举个实际场景：**想测某个应用在特定网络环境下的反应**，就没必要给整台机器的网络都加延时，只针对这一组应用即可。

[【跳转到 03:00】](https://www.bilibili.com/video/BV1C14y187Wx/?t=180)

---

## 三、关键机制：`priority` 与 `classid` 的一次「暗号对接」

[【跳转到 02:35】](https://www.bilibili.com/video/BV1C14y187Wx/?t=155)

**这一节是全文的原理核心，看懂它，后面所有命令都只是搬运工。** 视频作者查资料后确认：这件事其实非常简单，因为它踩在两条现成的机制上。

### 3.1 两个已有的「接口」

- **默认 filter 的分类逻辑**：tc 的默认 filter 会读取包里的一个值，把它当作 **classid** 来决定这个包分到哪个 class。当这个值是 0 时，包走**默认分类**。
- **socket 的 `priority` 成员变量**：每个应用创建的 socket 都有一个叫 `priority`（优先级）的成员，默认值是 0；而 **socket 发出的所有包，都会带上这个 priority 的值**。

### 3.2 于是「暗号」就成立了

把这两条拼起来：

1. 应用创建 socket → socket 的 `priority` 默认是 0；
2. socket 发包 → 包带上 priority=0；
3. 默认 filter 读到这个 0 → 走默认分类。

假设我现在来自某个 cgroup 的所有包，其 priority 都被改成 `ffff` 这种样子的值，那它发过来的包就不是 0 了，filter 就不会把它分到默认分类，而是分到我们指定的那个 class 上去。

[【跳转到 05:30】](https://www.bilibili.com/video/BV1C14y187Wx/?t=330)

对应的 classid 形如 `1:ffff`（主 id 是 `1`，后面是 `ffff`）。所以思路就清晰了：**只要想办法让这个应用所有进程发出的包都带上 `1:ffff` 这样一个 priority，也就等于让它们都带上这个 classid**，剩下的交给 tc 就行——我要做的，只是把这个 class 的 classid 固定成同一个值。

[【跳转到 05:55】](https://www.bilibili.com/video/BV1C14y187Wx/?t=355)

![改动后的示意：socket destroy/socket create 一侧写入 1:ffff，包一路向下进入 classid 为 1:ffff 的延时 class](<assets/使用Linux kernel cgroup(v2) bpf 和netem来捣捣乱：只针对某组进程增加网络延时的模拟而不影响其他应用/00305.webp>)

---

## 四、cgroup BPF 程序：在 `socket_create` 时把 priority 改成 `1:ffff`

[【跳转到 06:04】](https://www.bilibili.com/video/BV1C14y187Wx/?t=364)

视频里这是个简单的 demo，重心放在 **cgroup 对 `socket_create`（socket 创建）这个函数的 hook** 上。逻辑是：

- 我指定的某个 cgroup 里的应用，在调用 `socket_create` 时，都会去调用我这段 BPF 程序；
- 而这段 BPF 程序做的事情也很简单：**修改这个 socket 的 priority，设成 `1:ffff`**，也就是设成我想要的那个 filter 的 classid。

[【跳转到 06:29】](https://www.bilibili.com/video/BV1C14y187Wx/?t=389)

这样一来，socket 创建好之后，它里面发出的所有包都会带上这个 priority，然后一路传下去就会产生 delay。

要点是**两端的值必须是我自己固定好的**：这边创建一个能产生 delay 的 netem qdisc，它的 classid 就是 `1:ffff`；BPF 程序那边把 priority 也写成 `1:ffff`，程序最后 `return 1` 就行。

[【跳转到 06:51】](https://www.bilibili.com/video/BV1C14y187Wx/?t=411)

> **返回值的小细节**：`return 1` 表示这个操作成功，`return 0` 好像是表示拒绝。（对 `cgroup/sock_create` 这类程序而言，返回值决定放行还是拒绝。）

![cgroup BPF 程序源码：挂在 socket_create 上，修改 socket 的 priority](<assets/使用Linux kernel cgroup(v2) bpf 和netem来捣捣乱：只针对某组进程增加网络延时的模拟而不影响其他应用/00406.webp>)

---

## 五、为什么用 cgroup v2，以及 BPF 程序怎么「留住」

[【跳转到 07:09】](https://www.bilibili.com/video/BV1C14y187Wx/?t=429)

这是一个 **cgroup 类型的 BPF 程序**。作者特别说明：目前测试用的 cgroup 都是 **cgroup v2**，看到的那些 cgroup hook 最好在 **cgroup v2 下使用**；cgroup v1 上可能也能用，但操作会比较麻烦。

虽然从 v1 迁到 v2 会花一定时间，但 v2 是趋势，所以这个 demo 也只演示 cgroup v2 的操作——**底层的逻辑是一样的**。

[【跳转到 07:34】](https://www.bilibili.com/video/BV1C14y187Wx/?t=454)

把 BPF 程序编好、编成目标文件，上传到测试机之后，操作流程是：

1. **加载并 pin**：先把 BPF 程序加载挂到内核里，并把它 **pin 到一个位置**，从而保证程序保留在内核中；
2. **pin 的本质**：它其实是 link 到内核文件系统（bpffs）上的一个文件——**只要这个文件在，这段 BPF 程序就可以一直保留在内核里；如果这个文件被 unlink，程序就会从内核里释放出去**；
3. **建 cgroup**：创建自己的 cgroup，例如 `my_test`；
4. **挂程序**：把这个 BPF 程序挂到 `my_test` 这个 cgroup 上。

[【跳转到 08:49】](https://www.bilibili.com/video/BV1C14y187Wx/?t=529)

挂好之后，这个 cgroup 里就常驻了我的 BPF 程序：**任何在这个 cgroup 内的应用，创建 socket 时都会调用我的程序，从而把 priority 改成一个固定的值**（测试嘛，就写死一个固定值）。

![用 tc 脚本加载 BPF 程序、pin 到文件系统、创建 cgroup 并把程序挂上去的过程](<assets/使用Linux kernel cgroup(v2) bpf 和netem来捣捣乱：只针对某组进程增加网络延时的模拟而不影响其他应用/00664.webp>)

---

## 六、动手实验：把「一组应用」真的拖慢

[【跳转到 09:14】](https://www.bilibili.com/video/BV1C14y187Wx/?t=554)

### 6.1 准备：三个应用，起初一样快

测试场景里准备了几个应用，它们都想访问某个 server/daemon（例如启动三个 server）。最开始它们**都能 ping 通，而且延迟都很小**——这是后面做对照的基线。

[【跳转到 09:39】](https://www.bilibili.com/video/BV1C14y187Wx/?t=579)

### 6.2 只把「目标应用」的进程号放进 cgroup

想针对某个应用（它里面执行的所有进程都要加 delay），只需要**把这个进程的 id 加到 `my_test` 这个 cgroup 里**。

此时的状态是：

- 一边是「正常应用」，不受 cgroup 控制；
- 另一边是「已在 cgroup 控制下的应用」。

而这时**还没有加 netem**，所以其实两边都还能正常访问——说明「控制」本身不产生延时，真正的延时来自 netem 那一支。

[【跳转到 10:04】](https://www.bilibili.com/video/BV1C14y187Wx/?t=604)

### 6.3 搭树：一个默认 class + 一个延时 class

[【跳转到 10:26】](https://www.bilibili.com/video/BV1C14y187Wx/?t=626)

接下来按上一期的做法把这棵树建起来：**先创建根节点下面的 qdisc，然后做两个 class**——一个 class 负责正常操作，另一个 class 负责产生 delay。

[【跳转到 10:39】](https://www.bilibili.com/video/BV1C14y187Wx/?t=639)

关键细节：**产生 delay 的那个 class，它的 classid 要设置成 `1:ffff`**，跟 socket_create 里写的值保持一致；然后再往这个 class 里挂上 netem（它负责帮你产生 delay、丢包之类的模拟现象）。这样，这棵树就构建起来了。

![最终完整拓扑：根 qdisc 下分出「延时 class（classid = 1:ffff）」与「正常 class」，延时 class 上挂 netem，最终接到 NIC Driver](<assets/使用Linux kernel cgroup(v2) bpf 和netem来捣捣乱：只针对某组进程增加网络延时的模拟而不影响其他应用/00887.webp>)

### 6.4 验证：cgroup 内变慢，cgroup 外不变

[【跳转到 11:41】](https://www.bilibili.com/video/BV1C14y187Wx/?t=701)

整个系统配合起来就能工作了：**socket 带着 `1:ffff` 这个标识，标识过来以后，默认 filter 就会把它送到延时 class 里的 netem 模块**。现象是：

- 在 cgroup 外的正常应用里 ping —— 正常、很快；
- 在 cgroup 内的应用里 ping —— **产生了明显的 delay**。

[【跳转到 11:56】](https://www.bilibili.com/video/BV1C14y187Wx/?t=716)

这样就实现了「针对某个应用产生 delay」：这个 cgroup 里所有应用只要走这张网卡，就都会产生这类 delay。

![ping 对照：cgroup 外的应用正常，cgroup 内的应用出现明显延时](<assets/使用Linux kernel cgroup(v2) bpf 和netem来捣捣乱：只针对某组进程增加网络延时的模拟而不影响其他应用/00796.webp>)

### 6.5 一个必须记住的限制：延时挂在「网卡」上

[【跳转到 12:21】](https://www.bilibili.com/video/BV1C14y187Wx/?t=741)

这里要特别说明：这棵树是挂在**某一张网卡**上的。如果你希望「这个 cgroup 里 PID 对应的应用，不管走哪张网卡都会产生 delay」，**就需要把 netem 挂到所有的网卡上，每一张都要挂一遍**。

### 6.6 不止 ping：HTTP 应用同样受影响

[【跳转到 12:41】](https://www.bilibili.com/video/BV1C14y187Wx/?t=761)

作者也做了性能测试：用 `curl` 访问上千次。在**不受控制的网卡路径**上，`curl` 是很快的；而**被 cgroup 控制的那个环境里就有点特殊**——它不管跑什么应用都需要 delay，不光是 ping：

- 例如在其中跑一个 HTTP 应用需要访问那张网卡，网卡就会给它模拟一个延时出来，于是会花很长很长时间；
- 这就意味着，你可以借此观察「某个应用在这种网络环境下会有什么行为」，把它隔离出来单独测试。

[【跳转到 13:49】](https://www.bilibili.com/video/BV1C14y187Wx/?t=829)

最后要留意一点：**只影响了这一个 cgroup 里的所有应用，其它应用依然走正常路径，并没有产生 delay**；不过它们可能会有**一点点额外的消耗**，因为本来其实不需要走这棵树，现在稍微走了一下这棵树，会有一点开销。

![两个 bash 跑同样的事、只是分属不同 cgroup，分别用 curl 访问时延时表现完全不同](<assets/使用Linux kernel cgroup(v2) bpf 和netem来捣捣乱：只针对某组进程增加网络延时的模拟而不影响其他应用/00921.webp>)

---

## 小结

- **一句话方法**：cgroup 的 BPF hook（`socket_create`）+ netem 就实现了「只针对某一组应用增加模拟网络延时」。
- **原理是「暗号对接」**：BPF 把 socket 的 `priority` 写成 `1:ffff`；tc 默认 filter 把包的 `priority` 当 `classid` 用——两个 `1:ffff` 对上，包就进了延时 class。
- **两端值必须一致**：netem class 的 classid 与 BPF 程序写入的 priority 必须相同，否则包进不了延时分支。
- **用 cgroup v2**：cgroup hook 最好在 cgroup v2 下用，v1 虽然可能可用但更麻烦。
- **BPF 程序靠 pin 常驻**：pin 到 bpffs 上的文件在，程序就在；文件被 unlink，程序即被释放。
- **限制在网卡**：延时树挂在单张网卡上；要多网卡生效得每张网卡都挂一遍。
- **效果范围**：只有目标 cgroup 内的应用会变慢，其它应用照常走，只有极小的额外开销。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| qdisc | 排队规则，Linux 流量控制里挂在网卡上的「树的根」，决定包怎么排队、怎么分发 |
| class | qdisc 树上的分类节点，一个 class 可以承接特定的包（如「产生延时的那一支」） |
| filter | 分类器，决定一个包应该落到哪棵树的哪个 class |
| netem | 内核里的网络模拟模块，能制造延时、丢包等网络异常现象 |
| cgroup BPF | 挂在 cgroup 上的 BPF 程序，能在 cgroup 内进程做特定操作（如创建 socket）时被调用 |
| `socket_create` hook | cgroup BPF 的一个挂载点，进程调用 socket 创建时触发 |
| `priority` | socket 的优先级成员变量，默认 0，其值会被发出包携带 |
| `classid` | 包的分类标识，tc 默认 filter 用它决定包属于哪个 class |
| bpffs / pin | BPF 文件系统与「钉住」机制：把程序钉在文件系统上的文件里以保持常驻 |
| cgroup v2 | 新一代 cgroup 统一层级，cgroup BPF hook 主要在其上使用 |
