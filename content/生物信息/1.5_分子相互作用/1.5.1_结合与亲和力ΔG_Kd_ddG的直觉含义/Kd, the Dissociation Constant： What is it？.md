# Kd，解离常数：它到底是什么？

> 视频来源：[Kd, the Dissociation Constant: What is it?](https://www.youtube.com/watch?v=3UHJ9gnpqB0)（YouTube，约 8 分钟，播放 12.5 万+）。本文基于该视频的演说图文稿整理而成，关键结论均可在对应时间戳核对。

## 本讲要解决的核心问题（SCQA）

**背景**：蛋白质的功能几乎都离不开"结合"——药物要结合靶点蛋白、信号分子要结合受体、抗体要结合抗原。描述这类结合，生化里写成一个平衡反应：蛋白 P 与配体 L 结合成复合物 PL。

**冲突**：衡量结合强弱的平衡常数有两个，Ka（结合常数）和 Kd（解离常数），而且 Kd 越小代表结合越强——数值大小和"强/弱"的方向是反的，初学者极易混淆；两个常数还互为倒数，符号 Ka 又和酸碱平衡里的酸解离常数撞名。

**疑问**：Kd 到底是什么？它为什么带"浓度"单位？为什么蛋白质研究里几乎都用 Kd 而不是 Ka？

**回答（中心思想）**：Kd 是解离常数，Kd = [P]·[L]/[PL]，单位是浓度（M）。它的直觉含义是：**当游离配体（或蛋白）浓度等于 Kd 时，恰有一半的靶分子被结合**。Kd 越小结合越强，且 Kd = 1/Ka。因为"浓度"单位比"1/浓度"直观得多，生化与药物研究默认使用 Kd。

![视频标题页：Kd, the Dissociation Constant — 解离常数](assets/Kd,%20the%20Dissociation%20Constant：%20What%20is%20it？/00000.webp)

## 一、先说"结合"：蛋白 P 与配体 L 写成一个平衡反应

### 1.1 P 是蛋白，L 是配体

在结合类问题里，记号约定很固定：**P 代表蛋白（protein）**，**L 代表配体（ligand）**。蛋白你已经熟悉——氨基酸连成的链，执行各种生物功能；配体是更关键的新概念：**凡是能被蛋白结合的分子，都叫配体**（药物分子、信号分子、底物……）。

### 1.2 一个"抓铅笔"的类比

讲师给了一个贯穿全片的类比：把你的手想成蛋白，铅笔想成配体。起初两者互不相干；你伸手一抓，铅笔就被"结合"到了手上——这时就形成了**复合物（complex）**，正如蛋白结合配体后形成 PL 复合体。[【跳转到 00:50】](https://www.youtube.com/watch?v=3UHJ9gnpqB0&t=50)

### 1.3 平衡反应：不是全结合，也不是全不结合

蛋白-配体的相互作用写成平衡反应：

$$P + L \rightleftharpoons PL$$

关键直觉是：**反应达到平衡时，不是所有配体都结合在蛋白上**——总是一部分处于结合态（PL），一部分处于游离态（P 和 L）。[【跳转到 01:15】](https://www.youtube.com/watch?v=3UHJ9gnpqB0&t=75) 用类比说：没拿铅笔的手是"游离蛋白"，握着铅笔的手就是"复合物"。[【跳转到 01:40】](https://www.youtube.com/watch?v=3UHJ9gnpqB0&t=100)

![P + L ⇌ PL 平衡反应：部分游离、部分结合](assets/Kd,%20the%20Dissociation%20Constant：%20What%20is%20it？/00075.webp)

![手握铅笔 = 蛋白-配体复合物](assets/Kd,%20the%20Dissociation%20Constant：%20What%20is%20it？/00100.webp)

这和普通化学里的平衡反应没有本质区别，同样可以用平衡常数描述——只是名字换成了生化专属的 Ka 和 Kd。[【跳转到 02:05】](https://www.youtube.com/watch?v=3UHJ9gnpqB0&t=125)

## 二、顺着反应写：结合常数 Ka

### 2.1 Ka 的表达式

写平衡常数永远**从左往右读**反应：产物（分子）之积作分子，反应物之积作分母。对 P + L ⇌ PL 来说：

$$K_a = \frac{[PL]}{[P]\,[L]}$$

因为从左往右读时，蛋白正在"结合（associate）"配体，所以这个常数叫**结合常数（association constant）Ka**。[【跳转到 02:30】](https://www.youtube.com/watch?v=3UHJ9gnpqB0&t=150)

![从左往右读反应：Ka = [PL]/([P][L])](assets/Kd,%20the%20Dissociation%20Constant：%20What%20is%20it？/00150.webp)

![手"结合"铅笔的过程，对应 association](assets/Kd,%20the%20Dissociation%20Constant：%20What%20is%20it？/00175.webp)

### 2.2 一个符号陷阱：Ka 有两种

Ka 这个符号容易撞车：酸碱平衡里 Ka 是**酸解离常数**。但在蛋白功能语境下，**Ka 默认指结合常数（association constant）**——注意区分。[【跳转到 03:20】](https://www.youtube.com/watch?v=3UHJ9gnpqB0&t=200)

## 三、把反应倒过来写：解离常数 Kd

把同一个平衡反应反过来写：PL ⇌ P + L。这次从左往右读，是复合物正在"解离"：就像你写久了字手酸了，松开铅笔让它落回桌面——从"握着铅笔"回到"手、铅笔分离"。[【跳转到 03:44】](https://www.youtube.com/watch?v=3UHJ9gnpqB0&t=224)

![逆反应：复合物解离为 P 与 L](assets/Kd,%20the%20Dissociation%20Constant：%20What%20is%20it？/00224.webp)

按同样的"产物/反应物"规则写这个方向：

$$K_d = \frac{[P]\,[L]}{[PL]}$$

**D 就是 dissociation（解离）的首字母**。[【跳转到 04:34】](https://www.youtube.com/watch?v=3UHJ9gnpqB0&t=274)

![Kd = [P][L]/[PL]，D = dissociation](assets/Kd,%20the%20Dissociation%20Constant：%20What%20is%20it？/00274.webp)

讲师强调：在蛋白功能的语境里，Ka 与 Kd 中**最重要的、用得最多的是 Kd**。为什么？答案藏在单位里。

## 四、单位推导：Kd 的单位是浓度

### 4.1 约分看单位

假设三个浓度都用 mol/L（M）：Kd = [P]·[L]/[PL] 的单位是

$$\frac{M \times M}{M} = M$$

![三个浓度约分，Kd 剩下单位 M](assets/Kd,%20the%20Dissociation%20Constant：%20What%20is%20it？/00306.webp)

### 4.2 严格来说：平衡常数其实无量纲

严格按物理化学的定义，所有平衡常数都是**无量纲**的——因为每个浓度本应除以标准浓度再代入。但生化学家习惯"偷懒"，不除标准浓度、直接把浓度代进去，于是 Kd 在实践中就带上了摩尔（M）这个单位。[【跳转到 05:31】](https://www.youtube.com/watch?v=3UHJ9gnpqB0&t=331)

![严格无量纲 vs 生化习惯的"单位 M"](assets/Kd,%20the%20Dissociation%20Constant：%20What%20is%20it？/00331.webp)

而 Ka 呢？它的单位是 (M·M)/M 的倒数——**1/M（逆摩尔）**。[【跳转到 05:56】](https://www.youtube.com/watch?v=3UHJ9gnpqB0&t=356)

![Ka 的单位是 1/M](assets/Kd,%20the%20Dissociation%20Constant：%20What%20is%20it？/00356.webp)

"1/M"这种逆浓度单位用起来很不顺手——这也是大家偏爱 Kd 的直接原因：**Kd 的单位就是浓度**。[【跳转到 06:21】](https://www.youtube.com/watch?v=3UHJ9gnpqB0&t=381)

## 五、Kd 与 Ka 互为倒数

因为两个常数来自同一个反应的正反两个写法，表达式互为倒数：

$$K_d = \frac{1}{K_a}, \qquad K_a = \frac{1}{K_d}$$

这带来一个实用技巧：很多场合你可以先（比如用图形法）求出 Kd，再取倒数得到 Ka；反之亦然。[【跳转到 06:47】](https://www.youtube.com/watch?v=3UHJ9gnpqB0&t=407)

![Kd 与 Ka 互为倒数](assets/Kd,%20the%20Dissociation%20Constant：%20What%20is%20it？/00407.webp)

虽然通常讨论结合时把反应按"P + L 结合"的方向写（顶部那行），但**真正常用、更有信息量的是 Kd**。[【跳转到 07:12】](https://www.youtube.com/watch?v=3UHJ9gnpqB0&t=432)

![蛋白功能研究里最常用 Kd](assets/Kd,%20the%20Dissociation%20Constant：%20What%20is%20it？/00432.webp)

## 小结

- 蛋白-配体结合写成一个平衡反应 P + L ⇌ PL；平衡态下游离与结合两种形式共存。
- 顺着写（结合方向）得到结合常数 Ka = [PL]/([P][L])；反着写（解离方向）得到解离常数 Kd = [P][L]/[PL]。
- Kd 的单位是浓度（M），Ka 的单位是 1/M；严格说平衡常数无量纲，是生化习惯"不除标准浓度"赋予了单位。
- Kd 与 Ka 互为倒数：Kd = 1/Ka。
- Kd 越小、结合越强；因为"浓度"单位直观，蛋白质研究默认使用 Kd。
- （本讲后续系列）Kd 还可以由结合曲线图形法求出：一半结合处对应的浓度就是 Kd。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| 配体（ligand，L） | 能被蛋白结合的分子（药物、信号分子、底物等）的通称 |
| 复合物（complex，PL） | 蛋白与配体结合后形成的整体 |
| Ka（association constant） | 结合常数，[PL]/([P][L])，单位 1/M，越大结合越强 |
| Kd（dissociation constant） | 解离常数，[P][L]/[PL]，单位 M，越小结合越强 |
| Kd = 1/Ka | 同一平衡正反两种写法的互倒关系 |
