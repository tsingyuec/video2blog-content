# Computational Challenges and Opportunities in RNA Secondary Structure Prediction

> 视频来源：[YouTube《Computational Challenges and Opportunities in RNA Secondary Structure Prediction》](https://www.youtube.com/watch?v=WGe9OcFOiIw)（61:02），主讲人 **Anne Condon**（英属哥伦比亚大学 UBC 教授，ACM 博士论文奖得主，长期研究算法复杂度与生物分子计算）。这是该系列特邀讲座：前半场用"效率—通用性—准确率"三条轴梳理 RNA 二级结构预测的计算版图（peeling/chopping 递归、banana-split、参数学习 10.6% 提升），后半场展望分子编程——DNA 瓦片自组装与 DNA 行走者。视频字幕为英文自动生成，本文基于文稿整理翻译；文中数字与结论均出自视频内容，可点击时间戳回看核对。

## 本讲要解决的核心问题（SCQA）

**背景**：1994 年 Len Adleman 用 DNA 分子做计算的文章点燃了"分子编程"的想象——Anne Condon 从此转入这个领域：既能**设计**分子去实现新功能，也要能**预测**分子天然会折叠成什么结构（[【跳转到 02:00】](https://www.youtube.com/watch?v=WGe9OcFOiIw&t=120)）。

**冲突**：一条含足量 A/C/G/U 的长序列，可能折叠方式的数量是指数级的。想在其中找到"真实"结构，计算上有多难？预测准确率又有多高？

**疑问**：预测算法在**效率、通用性、准确率**三条轴上分别走到了哪里？瓶颈在哪？机会在哪？

**回答（中心思想）**：假结无关结构有优雅的 O(n³) 动态规划（peeling/chopping）；一般假结是 NP-hard，受限子类做到 O(n⁵)/O(n⁶)；准确率瓶颈不在算法而在能量模型——用机器学习重新拟合参数可把 F 值提升 **10.6%**；而分子编程（自组装瓦片、DNA 行走者）正在把"预测"与"设计"连成闭环。

## 一、背景：从双螺旋到自折叠的单链

[【跳转到 03:00】](https://www.youtube.com/watch?v=WGe9OcFOiIw&t=180)

DNA 双螺旋源于互补碱基对（A-T、G-C）；把一条 DNA 单链单独放进溶液，它没有互补链可配，只能**和自己**配——这就是 RNA 二级结构问题的原型。碱基互相寻找、结合，形成分支结构：一条外层 stem 加几条分支，形似树；这种结构在生物 RNA 里非常常见，tRNA 的三叶草就是代表（[【跳转到 05:30】](https://www.youtube.com/watch?v=WGe9OcFOiIw&t=330)）。

![tRNA 三叶草：分支结构是生物 RNA 的常见形态](assets/Computational%20Challenges%20and%20Opportunities%20in%20RNA%20Secondary%20Structure%20Prediction/00388.webp)

主讲人特别提醒：二级结构图只是"**谁和谁配对**"的清单，对真实三维结构的刻画极其粗糙——三叶草图上的两个环在 3D 里可能完全贴在一起（[【跳转到 06:00】](https://www.youtube.com/watch?v=WGe9OcFOiIw&t=360)）。两个环末端的互补序列还可以互相配对，把结构"折"成假结——但螺旋有扭转，两环之间能形成的配对数受几何约束，所以这类结构相对少见（[【跳转到 06:30】](https://www.youtube.com/watch?v=WGe9OcFOiIw&t=390)）。

### 1.1 一个多分子设计案例与 toehold 级联

[【跳转到 07:00】](https://www.youtube.com/watch?v=WGe9OcFOiIw&t=420)

人工设计的例子刻意选了**多分子**编成的刚性结构——四条链各出一角，末端留有可编程的"抓手"，刚性正是它的应用价值（[【跳转到 07:30】](https://www.youtube.com/watch?v=WGe9OcFOiIw&t=450)）。

更精彩的是**结构路径**而非静态结构：两条各带长 stem 与顶部发夹的链处于亚稳态；引入第三条"引发链"，它通过 **toehold**（一段单链突出）挂上第一条链，逐步"拉开"整条 stem；解放出来的顶端又成为下一条链的 toehold……如此级联下去，一管子里可以拉出极长的双链产物。应用是**分子检测**：样品里只要有一点点引发分子，级联就会被触发，产物长度还能反映引发分子的数量（[【跳转到 09:00】](https://www.youtube.com/watch?v=WGe9OcFOiIw&t=540)）。

![toehold 级联：引发链拉开亚稳态发夹，触发链式反应](assets/Computational%20Challenges%20and%20Opportunities%20in%20RNA%20Secondary%20Structure%20Prediction/00566.webp)

## 二、两个问题与一个"沙发土豆"模型

[【跳转到 10:30】](https://www.youtube.com/watch?v=WGe9OcFOiIw&t=630)

由此引出本讲关心的两个问题：

1. **预测**：给定（一条或多条）序列，预测折叠成的结构、或折叠经过的结构路径；
2. **设计**：设计序列，使其形成特定结构/走特定路径——比如上面的分子检测（[【跳转到 10:30】](https://www.youtube.com/watch?v=WGe9OcFOiIw&t=630)）。

预测的思路是概率过程、由热力学驱动：分子像个"沙发土豆"，懒，只想待在低能量态；配对释放能量，所以它喜欢多配对（[【跳转到 12:00】](https://www.youtube.com/watch?v=WGe9OcFOiIw&t=720)）。真实试管里配对不断形成又断开，"真结构"其实是**最可能观察到的状态**。于是有两个可计算的目标：找最低能量构型（MFE），或算**配分函数**得到每个配对出现的概率（[【跳转到 13:00】](https://www.youtube.com/watch?v=WGe9OcFOiIw&t=780)）。

![两个问题：预测结构与设计序列；MFE 与配分函数](assets/Computational%20Challenges%20and%20Opportunities%20in%20RNA%20Secondary%20Structure%20Prediction/00656.webp)

## 三、能量模型与三条轴

### 3.1 环式（loop-based）能量模型

[【跳转到 13:30】](https://www.youtube.com/watch?v=WGe9OcFOiIw&t=810)

最简单的模型是给每个碱基对打分再求和，但实践用的是**环式模型**：能量挂在"环"上——茎末端的发夹环、连续配对形成的堆积对（stacked pair）、带多个分支的多环（multiloop）。生物化学家（如 Rochester 的 Turner 实验室）为每种环精心测定了能量参数，实践中"求和即总能量"（[【跳转到 14:00】](https://www.youtube.com/watch?v=WGe9OcFOiIw&t=840)）。

![环式能量模型：能量挂在发夹环、堆积对、多环上](assets/Computational%20Challenges%20and%20Opportunities%20in%20RNA%20Secondary%20Structure%20Prediction/00869.webp)

### 3.2 NP-hard 与三条轴

[【跳转到 16:00】](https://www.youtube.com/watch?v=WGe9OcFOiIw&t=960)

坏消息先说：在一般情形（loop 模型 + 任意结构）下，找最低能量二级结构是 **NP-hard**。但实践里这不太致命——真实关心的结构很少踩到最坏情况。评价算法可以沿三条轴：

- **效率**：真算 MFE 的动态规划（非启发式）复杂度几何？
- **通用性**：能处理哪类结构？假结无关（树形分支）、H 型假结、kissing hairpin……
- **准确率**：预测与真实结构差多远？

### 3.3 弧线图表示

[【跳转到 17:30】](https://www.youtube.com/watch?v=WGe9OcFOiIw&t=1050)

接下来换一种画法：序列沿底边排开，配对画成弧。三叶草画出来没有交叉弧；kissing hairpin 立刻显出交叉弧；H 型假结则是一条发夹加一条绕过去配对的弧（[【跳转到 18:30】](https://www.youtube.com/watch?v=WGe9OcFOiIw&t=1110)）。

![弧线图：无交叉=假结无关；交叉弧=假结](assets/Computational%20Challenges%20and%20Opportunities%20in%20RNA%20Secondary%20Structure%20Prediction/01080.webp)

## 四、算法复杂度地图

### 4.1 Peeling 与 Chopping：O(n³) 的优雅世界

[【跳转到 19:00】](https://www.youtube.com/watch?v=WGe9OcFOiIw&t=1140)

假结无关结构有一个"剥皮与砍剁"的直觉：任何这类结构，要么从外向内**剥**掉最外侧配对，要么从某处**剁**成两个独立部分——递归地剥/剁下去，总能归约到空。围绕它构建动态规划：为序列的所有子区间保留 MFE 值，每个子区间的答案由"所有剥法/剁法"取最小（[【跳转到 19:30】](https://www.youtube.com/watch?v=WGe9OcFOiIw&t=1170)）。

![peeling/chopping：子区间上取所有分解的最小值](assets/Computational%20Challenges%20and%20Opportunities%20in%20RNA%20Secondary%20Structure%20Prediction/01170.webp)

### 4.2 Banana Split：假结的代价

[【跳转到 21:00】](https://www.youtube.com/watch?v=WGe9OcFOiIw&t=1260)

交叉弧一来，"剁"和"剥"都失效了。需要的额外操作是把结构切成两根"香蕉"——这就是 **banana split**。代价：子问题要由四个端点定义（原先是两个），空间 O(n⁴)；而递归怎么继续又不清楚（[【跳转到 21:30】](https://www.youtube.com/watch?v=WGe9OcFOiIw&t=1290)）。允许两段交叉 + 剥皮可得 O(n⁵) 时间/O(n⁴) 空间的算法；三段交叉（kissing hairpin 是生物学里真实存在的基序）最早由 **Rivas & Eddy** 的 O(n⁶) 算法覆盖；Condon 团队（学生 Hosna Jabbari、博士后 Ho-Lin Chen）把剥皮方向灵活化（外侧剥、内侧剥、四个端点任选方向交替），把 kissing hairpin 级结构做到 **O(n⁵)**（[【跳转到 23:00】](https://www.youtube.com/watch?v=WGe9OcFOiIw&t=1380)）。

![banana split：交叉弧结构需四端点定义子问题](assets/Computational%20Challenges%20and%20Opportunities%20in%20RNA%20Secondary%20Structure%20Prediction/01270.webp)

### 4.3 复杂度总结与实践规模

[【跳转到 24:00】](https://www.youtube.com/watch?v=WGe9OcFOiIw&t=1440)

从假结无关的 O(n³) 到极通用结构的 O(n⁶)，一张表看完（[【跳转到 24:30】](https://www.youtube.com/watch?v=WGe9OcFOiIw&t=1470)）。n 是序列长度。实践中生物学家关心几十到几千核苷酸：几千核苷酸的假结无关折叠毫无压力；假结结构几百核苷酸还能在桌面机上跑，再长就开始吃力（[【跳转到 25:00】](https://www.youtube.com/watch?v=WGe9OcFOiIw&t=1500)）。

![复杂度地图：O(n³) 假结无关 → O(n⁵) kissing hairpin → O(n⁶) 通用](assets/Computational%20Challenges%20and%20Opportunities%20in%20RNA%20Secondary%20Structure%20Prediction/01470.webp)

## 五、准确率：真正的瓶颈与 10.6% 的跃升

### 5.1 怎么衡量准确率

[【跳转到 26:30】](https://www.youtube.com/watch?v=WGe9OcFOiIw&t=1590)

算法保证找到的确实是（所选模型下的）最低能量结构——不准只能怪能量模型。衡量用 **F 值**：灵敏度（真实配对中预测对了多少）与阳性预测值（预测出的配对中对了多少）的调和平均——逼你在"漏报"与"误报"之间找平衡（[【跳转到 27:00】](https://www.youtube.com/watch?v=WGe9OcFOiIw&t=1620)）。用标准算法 + Turner 能量模型，在学生 Mirela Andronescu 收集的大结构库上平均约 **60%**——比蛋白质预测好得多，但提升空间巨大（[【跳转到 28:00】](https://www.youtube.com/watch?v=WGe9OcFOiIw&t=1680)）。

![F 值：灵敏度与 PPV 的调和平均；Turner 模型平均约 60%](assets/Computational%20Challenges%20and%20Opportunities%20in%20RNA%20Secondary%20Structure%20Prediction/01619.webp)

### 5.2 参数学习：Boltzmann 似然与约束生成

[【跳转到 29:00】](https://www.youtube.com/watch?v=WGe9OcFOiIw&t=1740)

Turner 模型约 **350 个特征**（每种堆积对、每种发夹各是一个特征），部分由湿实验（紫外熔解）测定，其余靠拟合已知结构——拟合的部分不可靠。学生 Andronescu 想做的是：**固定模型形式，用数据重新学参数**。路线一（Chuong Do 等斯坦福先行）：最大化结构数据的 **Boltzmann 似然**；Andronescu 的扩展是同时逼近热力学数据里测得的能量、再加正则项防过拟合——为此实现了梯度计算，工程量巨大且运行慢（[【跳转到 31:30】](https://www.youtube.com/watch?v=WGe9OcFOiIw&t=1890)）。

![Boltzmann 似然：最大化已知结构在参数下的概率](assets/Computational%20Challenges%20and%20Opportunities%20in%20RNA%20Secondary%20Structure%20Prediction/01901.webp)

路线二（**约束生成**，constraint generation）：真结构能量应低于一切错误结构、且逼近测量能量——这是指数多条约束；技巧是**边跑边生成**：用当前参数造一批低能错误结构，要求真结构能量更低，解出改进参数，再迭代，直到参数稳定。不用梯度、实现快，虽然不像严格的概率式机器学习那么"正宗"，但简单有效（[【跳转到 33:30】](https://www.youtube.com/watch?v=WGe9OcFOiIw&t=2010)）。

![约束生成：边跑边生成"真结构必须更低能"的约束](assets/Computational%20Challenges%20and%20Opportunities%20in%20RNA%20Secondary%20Structure%20Prediction/02070.webp)

两条路线都带来显著提升；配合她重建的高质量数据集，在大测试集上准确率提升 **10.6%**——而过去一二十年论文间的提升通常只有 1–3%，这是一次大跳（[【跳转到 37:30】](https://www.youtube.com/watch?v=WGe9OcFOiIw&t=2250)）。

## 六、开放问题

[【跳转到 38:00】](https://www.youtube.com/watch?v=WGe9OcFOiIw&t=2280)

- **"缠绕发夹"（entwined hairpins）**：比 kissing hairpin 缠得更深，目前需 O(n⁶)，能否 O(n⁵)？
- **多条相同链**：对称性校正项让 MFE 算法失效，而 Dirk Dirks 发现算配分函数时这些项奇迹般相消、可借群论结果处理——MFE 版本至今是悬案（[【跳转到 39:00】](https://www.youtube.com/watch?v=WGe9OcFOiIw&t=2340)）；
- **折叠路径**：本讲全是静态结构，路径预测同样机会很多；
- **多环特征太糙**：生物学家知道该建不对称性，但改进特征意味着动态规划从 n³ 变 n⁴、参数机器整个重跑——让学生干 6–12 个月然后可能发现白干，"实在不好玩"（[【跳转到 41:30】](https://www.youtube.com/watch?v=WGe9OcFOiIw&t=2490)）；
- **启发式替代 MFE 做参数探索**：启发式把能量模型当黑盒，换模型只需 20 分钟改打分函数；先在启发式里调好参数，再喂回 MFE 算法——快速探索海量模型变型的通道（[【跳转到 43:00】](https://www.youtube.com/watch?v=WGe9OcFOiIw&t=2580)）。

还有一个大前提值得记住：**"分子折叠到 MFE"本身没有证明**，对部分分子成立、部分不成立——路径视角（卡在局部极小）可能才是对的（[【跳转到 44:00】](https://www.youtube.com/watch?v=WGe9OcFOiIw&t=2640)）。

## 七、编程分子：从预测到设计

[【跳转到 44:30】](https://www.youtube.com/watch?v=WGe9OcFOiIw&t=2700)

讲座后半场切换到"编程"视角：DNA 是一种**全数字、可编程的纳米材料**——想要什么序列就能合成什么序列，还能预测其行为，于是可以在纳米尺度上"造东西"（[【跳转到 45:30】](https://www.youtube.com/watch?v=WGe9OcFOiIw&t=2730)）。

### 7.1 自组装：瓦片与 Sierpinski 三角

[【跳转到 46:30】](https://www.youtube.com/watch?v=WGe9OcFOiIw&t=2790)

自组装是自然界的根本过程（微管、鞭毛皆如此）；抽象地看，瓦片在"胶水"强度足够时黏上生长中的组装体——算法人一眼就能认出 Wang 瓦片。Eric Winfree 的团队用 DNA 做出物理瓦片，测试用例是**Sierpinski 三角**：四类瓦片（两种 1、两种 0）就能自然生长出分形图案；原子力显微镜图像显示长出来的确实近似 Sierpinski 三角，当然错误不少（[【跳转到 48:00】](https://www.youtube.com/watch?v=WGe9OcFOiIw&t=2880)）。

![DNA 瓦片自组装的 Sierpinski 三角（原子力显微镜）](assets/Computational%20Challenges%20and%20Opportunities%20in%20RNA%20Secondary%20Structure%20Prediction/02880.webp)

由此回到理论：怎么建模与控制错误？拼出特定形状最少要几种瓦片？Winfree 的学生发现**瓦片复杂度与 Kolmogorov 复杂度**之间有迷人联系（[【跳转到 49:00】](https://www.youtube.com/watch?v=WGe9OcFOiIw&t=2940)）。

### 7.2 DNA 行走者

[【跳转到 49:30】](https://www.youtube.com/watch?v=WGe9OcFOiIw&t=2970)

第二个例子编程的是**路径**：一段"行走者"（两段连体的 DNA）沿轨道行走，燃料发夹先通过 toehold 释放行走者的一条"脚"，脚再挂上下一个 toehold、拉开轨道上的发夹……循环前进。与级联检测一样，原理都是**亚稳态发夹 + 引入触发物释放**；应用包括在纳米空间搬运货物（[【跳转到 50:30】](https://www.youtube.com/watch?v=WGe9OcFOiIw&t=3030)）。

![DNA 行走者：燃料发夹释放脚，toehold 驱动沿轨行走](assets/Computational%20Challenges%20and%20Opportunities%20in%20RNA%20Secondary%20Structure%20Prediction/02994.webp)

Caltech 的 Niles Pierce 正在把这类系统推向"抽象建模→编译成真实 DNA 系统"的更高层抽象。主讲人的结语：预测侧有大量改进空间（路径、准确率、三级结构是一片未开垦地），编程侧的计算思维同样大有可为（[【跳转到 51:30】](https://www.youtube.com/watch?v=WGe9OcFOiIw&t=3090)）。

## 八、Q&A 精选

[【跳转到 53:00】](https://www.youtube.com/watch?v=WGe9OcFOiIw&t=3180)

- **行走者怎么验证真的在走？** 给"脚"和轨道发夹分别挂荧光基团与淬灭基团，只有走到位才有荧光信号；用两种颜色还能确认发光顺序正确（[【跳转到 53:30】](https://www.youtube.com/watch?v=WGe9OcFOiIw&t=3210)）。
- **行走者能倒着走吗？** 理论可行：把燃料设计成既能拆又能装，反向燃料可让系统回退——要是做成，燃料还能回收再用。欢迎带着这类点子去 DNA Computing 会议，或者干脆进湿实验室试试（[【跳转到 55:00】](https://www.youtube.com/watch?v=WGe9OcFOiIw&t=3300)）。
- **训练后预测能量与实验能量对得上吗？** 对热力学数据集（一千多个短结构，平均 17 个配对）做了均方根比较：与 Turner 原版相当（均方根误差 1 点几 kcal/mol），明显好于不用热力学数据的 Do 等方法（[【跳转到 57:30】](https://www.youtube.com/watch?v=WGe9OcFOiIw&t=3450)）。

## 写在最后

这场讲座的价值在于把 RNA 二级结构预测放进了一张**三维地图**：效率轴上 O(n³)→O(n⁶) 的阶梯清晰可爬；通用性轴上假结子类各有归属；准确率轴上 60% 的现状与 10.6% 的参数学习跃升指明了"瓶颈在模型不在算法"。而 Sierpinski 三角与 DNA 行走者则提醒我们：预测与设计本是一体两面——算得准，才造得出。
