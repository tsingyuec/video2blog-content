# 第02讲：用 PyMOL 看结构、用 VS Code 连集群——蛋白质建模的两把必备工具

## 本讲要解决的核心问题（SCQA）

**背景**：做蛋白质的机器学习（protein ML），你每天都会产出、下载大量三维结构文件（PDB 文件）；而真正吃算力的训练和绘图任务，通常跑在远程计算集群上，而不是你的笔记本上。

**冲突**：结构不能只靠阅读文本来理解，集群又隔着一层 SSH（安全远程登录）。PyMOL 的界面和一大堆命令让人望而生畏，VS Code 的远程玩法也没系统学过，于是"看得见结构"和"写得动代码"成了两道坎。

**疑问**：有没有一套顺手的工具组合，既能可视化蛋白质结构，又能远程连上集群写代码、看结果？

**回答（中心思想）**：有。本讲用一次完整的实操演示走通两件事——用 **PyMOL** 看结构（界面、常用命令、上色、比对、高亮、出图），用 **VS Code + 扩展** 远程登录计算集群（SSH、Jupyter notebook、tmux、Protein Viewer）。这一讲不讲深理论，只求把这两个"最常用工具"的骨架摸熟，剩下的深度留给你们自己动手练习。

主讲人是 Johns Hopkins University 的 Fatima Hitawala，时长约 29 分钟，属于系列里的"迷你实操课"（Mini-session）。

## 一、PyMOL 是什么：一个内置 Python 的分子可视化软件

PyMOL 和 Visual Studio Code 被主讲人称为这个领域里"最常用的两种工具"，而且"深不见底"（a glacier's worth of depth），[【跳转到 00:11】](https://www.youtube.com/watch?v=7fh90mdg2pI&t=11)。所以本讲只做非常基础的概览，目的是让你先熟悉界面，之后通过小练习找手感。

![PyMOL 主界面：左侧是对象/选择面板，中间是 3D 视图，底部是命令行](assets/第02讲_PyMol and VS Code (Mini-session)/00123.webp)

### 1.1 它到底是什么

PyMOL 是一个**分子可视化软件（molecular visualization software）**，而且**内部带有 Python**，[【跳转到 00:46】](https://www.youtube.com/watch?v=7fh90mdg2pI&t=46)。

- 平时我们把它当**图形用户界面（GUI）**来用，点点鼠标就能操作；
- 你也可以用 **Conda** 安装它，[【跳转到 00:51】](https://www.youtube.com/watch?v=7fh90mdg2pI&t=51)，然后写 **Python 脚本**，以一种更舒服的编程方式调用它的全部能力；
- 它还有一个内置的小接口，可以让你**把代码直接写进 GUI**，让操作更省事，[【跳转到 01:01】](https://www.youtube.com/watch?v=7fh90mdg2pI&t=61)。

> 术语：**PDB 文件**是蛋白质结构的标准文本格式，记录了每个原子的坐标；**GUI** 就是能用鼠标点击操作的图形界面。

### 1.2 我们拿它做什么

从 AI 的角度想：假设你训练好了一个模型、生成了一堆结构，想看看输出到底长什么样——把它丢进 PyMOL，它就能根据"化学键有没有断、结构看起来怪不怪"给出不同的形状和视图，[【跳转到 01:10】](https://www.youtube.com/watch?v=7fh90mdg2pI&t=70)。你还可以：

- 按某种属性给它上色，突出某个功能区域；
- 随意缩放，只盯着你关心的部分；
- 在实验场景里查看**氢键网络**、**极性接触（polar contacts）**；
- 做**突变（mutate）**、做 **sculpting（结构塑形）**等（主讲人自己用得不多，但值得了解），[【跳转到 01:35】](https://www.youtube.com/watch?v=7fh90mdg2pI&t=95)。

## 二、PyMOL 界面总览：命令行、选择模式与序列面板

打开 PyMOL 后（主讲人用的是 **PyMOL 3.0**，旧版本界面会略有不同，[【跳转到 02:08】](https://www.youtube.com/watch?v=7fh90mdg2pI&t=128)），界面可以分成几块来看。

### 2.1 命令行：PyMOL 的 Python 入口

界面底部是命令行，也是前面说的 Python 接口，[【跳转到 02:13】](https://www.youtube.com/watch?v=7fh90mdg2pI&t=133)。绝大多数操作都能在这里用一行命令完成，这是 PyMOL 最强大的地方。

### 2.2 选择模式切换：按残基还是按链

在对象面板上方有一个**选择模式（selection toggle）**下拉菜单，[【跳转到 03:13】](https://www.youtube.com/watch?v=7fh90mdg2pI&t=193)。它可以让你按不同粒度选择：

- **residue（残基）**：适合做非常精细的操作；
- **chain（链）**：适合整体删除某条链这类粗操作，非常有用；
- **molecule（分子）**；
- 也可以只看 **Cα**（蛋白质骨架上的α碳原子）。

![选择模式下拉菜单：可以按残基、链、分子等不同粒度来选中结构](assets/第02讲_PyMol and VS Code (Mini-session)/00193.webp)

### 2.3 序列面板：用序列来选结构

界面里还有一块**序列（sequence）**显示区，[【跳转到 03:48】](https://www.youtube.com/watch?v=7fh90mdg2pI&t=228)。它的两个用途特别实用：

1. **按序列选结构**：如果你知道某段序列、但不知道它在三维结构上的位置，直接在序列上选中这一段，结构里对应的部分就会被选中；
2. **同时显示两组序列**：当你有两组非常相似的结构时，它会同时展示两条序列，让你一边做**序列比对（sequence alignment）**、一边做**结构比对（structural alignment）**，[【跳转到 04:13】](https://www.youtube.com/watch?v=7fh90mdg2pI&t=253)。

### 2.4 缩放的两档用法

PyMOL 顶部有 **Zoom** 菜单。一个很实用的技巧是：

- 先用点击的方式把不需要的部分**隐藏**掉；
- 点 **Zoom Visible**，镜头就跳到当前可见的部分；
- 如果选中了特定的片段，用 **Zoom to active selection**，它会带你聚焦过去，并把其他结构**遮暗**，方便你只看重点，[【跳转到 05:03】](https://www.youtube.com/watch?v=7fh90mdg2pI&t=303)。

![Zoom 菜单的选项：All / Visible / Active Selection 等](assets/第02讲_PyMol and VS Code (Mini-session)/00303.webp)

## 三、从 fetch 到清理：最常用的 PyMOL 命令

命令多到数不清，但入门只需要记住几条。

### 3.1 获取一个结构：fetch

最常见的命令之一就是取一个 PDB 结构，格式是：

```
fetch <PDB的ID>
```

比如输入 `fetch 1ao7`，PyMOL 就会把 1AO7 这个结构下载并显示出来，[【跳转到 02:18】](https://www.youtube.com/watch?v=7fh90mdg2pI&t=138)。

### 3.2 清理结构：去掉水分子和非蛋白原子

下载下来的 PDB 往往含有大量"杂物"。主讲人常用的清理方式：

- `remove hetatm`：移除**非蛋白原子**（hetatm），只留下有机的部分。按主讲人的理解，就是"所有不属于蛋白质部分的东西"——比如金属离子，以及漂浮在周围的水分子，[【跳转到 02:43】](https://www.youtube.com/watch?v=7fh90mdg2pI&t=163)；
- `remove water`：专门去掉水分子（也可以从右侧菜单点 *remove waters* 完成）。

### 3.3 测量距离：Wizards 向导

PyMOL 还有 **Wizards（向导）**，其中 **Measurement（测量）**专门用来量：

- **距离（Distances）**；
- **角度（Angles）**、**二面角（Dihedrals）**；
- **极性邻居（Polar neighbors）**等，[【跳转到 05:28】](https://www.youtube.com/watch?v=7fh90mdg2pI&t=328)。

操作很直观：依次点两个原子，PyMOL 就报出它们之间的距离。演示中两个原子之间是 **3.9 埃（angstrom）**，[【跳转到 05:45】](https://www.youtube.com/watch?v=7fh90mdg2pI&t=345)。

> 术语：**埃（Å）**是原子尺度的长度单位，1 Å = 0.1 纳米，原子间成键距离通常在 1–2 Å 量级。

![用 Measurement 向导测量两个原子之间的距离，结果为 3.9 埃](assets/第02讲_PyMol and VS Code (Mini-session)/00345.webp)

## 四、A / S / H：控制"显示什么"的核心三键

演示里以**抗体（antibody）**为例。对象面板里每一行左侧有 A、S、H、L、C 五个字母按钮，代表最核心的一批命令，[【跳转到 06:05】](https://www.youtube.com/watch?v=7fh90mdg2pI&t=365)。

![抗体结构 + Action 菜单：可以查找极性接触、氢键、碰撞等](assets/第02讲_PyMol and VS Code (Mini-session)/00365.webp)

### 4.1 A = Action（通用操作）

A 代表 action，是最通用的命令入口：

- `remove waters`（去水）、`zoom`（缩放）、`find`（查找）；
- 查找 **full contacts**、所有**极性相互作用（polar interactions）**、**碰撞（clashes）**等。

### 4.2 S = Show（怎么显示）

S 代表 show，决定你以什么方式看到蛋白、离子或任何对象。用抗体演示：

- 默认是 **cartoon（卡通）视图**，能看到 **β 折叠（beta strands）**、**loop 环**、**α 螺旋（alpha helices）**；
- 切到 **ribbon**，结构会变成**一条穿过所有 Cα 的线**；
- 切到 **lines** 效果差不多；
- **mesh / dot spheres / surface**：显示**范德华半径**等表面，非常适合观察结构表面的"斑块（patch）"、有没有孔洞，从而大致判断 **pockets（口袋）**位置、**packing（堆积）**好不好、核心堆得紧不紧，[【跳转到 07:20】](https://www.youtube.com/watch?v=7fh90mdg2pI&t=440)。

![切换到表面/mesh 表示：便于观察堆积、口袋和孔洞](assets/第02讲_PyMol and VS Code (Mini-session)/00440.webp)

### 4.3 H = Hide（隐藏）

H 代表 hide，`hide everything` 会把所有对象一次性隐藏，再 `show cartoon` 就能回到干净的卡通视图。

## 五、上色的威力：element、SS、B Factor 与按链上色

上色（color）是 PyMOL 里最有用的功能之一，[【跳转到 07:45】](https://www.youtube.com/watch?v=7fh90mdg2pI&t=465)。

### 5.1 几种常用上色方式

- **by element（按元素）**：蛋白质里非氢原子大多是 C/N/O，按元素上色能让你大致看懂结构组成；
- **by SS（按二级结构）**：SS = **secondary structure（二级结构）**，会把 β 折叠、α 螺旋、loop 环染成不同颜色；
- **Spectrum（光谱/彩虹）**：按某种连续属性做渐变上色。

### 5.2 B Factor：一眼看出模型"哪里没把握"

**B Factor** 是 PDB 文件末尾的一列，可以存"温度信息"，[【跳转到 08:10】](https://www.youtube.com/watch?v=7fh90mdg2pI&t=490)：

- 在实验结构里，温度因子反映某一部分**有多灵活**；
- 在 **AlphaFold** 等预测模型的输出里，B Factor 存的其实是**模型对预测的置信度（confidence）**。

所以，只要把预测结构丢进 PyMOL 并按 B Factor 上色，你就能**一眼看出模型对哪些区域非常有信心、哪些区域是"问题地带"**，[【跳转到 08:35】](https://www.youtube.com/watch?v=7fh90mdg2pI&t=515)。

> 术语：**AlphaFold** 是 DeepMind 的蛋白质结构预测模型；它输出的 PDB 里，每个残基的置信度就藏在 B Factor 列里（通常叫 pLDDT）。

### 5.3 按链上色：快速定位重链/轻链

**color by chain（按链上色）**对找到目标非常方便。抗体有**抗原链（antigen chain）**、**重链（heavy chain）**、**轻链（light chain）**，按链上色后一眼就能区分，[【跳转到 09:00】](https://www.youtube.com/watch?v=7fh90mdg2pI&t=540)。你还可以按任意选项上色，甚至自定义配色方案。

![按链/光谱上色后的结构，不同颜色对应不同链或不同数值区间](assets/第02讲_PyMol and VS Code (Mini-session)/00540.webp)

## 六、对齐与选区：把结构叠合、把 CDR 存成对象

### 6.1 把选区存成对象（object）

当你在序列上双击选中某一段，或在上一步做好了选择后，这段选择会存成一个 **object（对象）**。你可以通过 **Actions → rename selections** 给它重命名，比如命名为 **CDR**，[【跳转到 09:25】](https://www.youtube.com/watch?v=7fh90mdg2pI&t=565)。这有点像 Python 里的**面向对象编程**——你可以选中一块东西、给它命名、到处移动。

> 术语：**CDR**（Complementarity-Determining Region，互补决定区）是抗体上与抗原结合的关键环区，常按 CDR1/2/3 编号；在抗体设计中经常单独拿出来研究。

### 6.2 结构比对：Align

PyMOL 另一个非常好用的功能是 **alignments（比对）**。有两种入口：命令行，或 **Actions → align** 菜单，[【跳转到 09:50】](https://www.youtube.com/watch?v=7fh90mdg2pI&t=590)。

以两个抗体为例，选择 **all to this**，PyMOL 会把当前对象（演示中是 **6XLB**）作为参照，**把所有其他完整结构对齐到它上面**（注意是完整结构，不是子对象，一次对齐一个对象），[【跳转到 10:15】](https://www.youtube.com/watch?v=7fh90mdg2pI&t=615)。

![Actions → align 菜单：把多个结构对齐到参考对象上](assets/第02讲_PyMol and VS Code (Mini-session)/00615.webp)

### 6.3 视图里读懂比对结果

对齐完成后：

- 它**同时做了结构比对和序列比对**（按最接近的部分配序列）；
- 按链上色后可以看清楚：**重链对重链、轻链对轻链**；
- 底部窗口会给出比对的信息；
- 你可能注意到有**多轮（multiple rounds）**——PyMOL 在不断尝试，让序列比对和结构比对达到最佳拟合，[【跳转到 11:03】](https://www.youtube.com/watch?v=7fh90mdg2pI&t=663)；
- 它基于**所有原子**计算，所以你家工具得到的数字可能和它不一样——别的工具可能只算每个残基的主碳原子，或只看**骨架原子（backbone atoms，不含氢）**，[【跳转到 11:33】](https://www.youtube.com/watch?v=7fh90mdg2pI&t=693)。

## 七、Cartoon transparency 与出图：把重点"提"出来

做这类工作时，最常想做的就是**强调蛋白的某一部分**。没有人光看整个蛋白就能明白你的意思，你必须聚焦并指出"这就是我要你看的地方"，[【跳转到 12:50】](https://www.youtube.com/watch?v=7fh90mdg2pI&t=770)。

### 7.1 两种"突出重点"的办法

1. **用颜色**：把其他部分都上成灰色，只给重点部分一个**超级亮的颜色**；
2. **用卡通透明度（cartoon transparency）**：把所有部分的透明度设为 0（或 1，即全透明），再把你关心的那部分设为**不透明**。

### 7.2 命令怎么写

演示里，主讲人现场输入了这条命令，[【跳转到 14:49】](https://www.youtube.com/watch?v=7fh90mdg2pI&t=889)：

```
set cartoon_transparency, <数值>, <对象名>
```

要点：

- 第一个参数是**属性名**：`cartoon_transparency`；
- PyMOL 命令里**所有参数用逗号分隔**；
- 第二个参数是**透明度数值**（0 = 完全不透明，1 = 完全透明）；
- 最后是**对象名**。

例如，把要强调的 CDR 区域的透明度设为 0，其余全部设为 **0.05**。这样做的效果是：原来所有卡通结构都带一点点描边/颜色，设置透明度会**去掉描边、并让结构本身变得略透明**；0.05 会移除描边但其他地方仍清晰可见，[【跳转到 15:14】](https://www.youtube.com/watch?v=7fh90mdg2pI&t=914)。

![设置 cartoon transparency 后，灰色部分变淡、绿色高亮区域"跳"出来](assets/第02讲_PyMol and VS Code (Mini-session)/00914.webp)

### 7.3 出图与配色脚本

画好图后，最后一步是**出图**，[【跳转到 15:39】](https://www.youtube.com/watch?v=7fh90mdg2pI&t=939)：

- **draw fast**：基本就是给你一张截图，快；
- **ray slow**（光线追踪）：生成那种**可用于发表的精美图片**，需要一点时间，进度会显示在上方；
- 然后 **save image to file** 保存。

如果你想要和 **RFdiffusion** 论文一样的图美观度，可以去看 **Notion 页面**：在幻灯片链接正下方有一个小文本文件，里面有 Python 脚本，包含 **preset aesthetic functions（预设美观函数）**，拿来就能复现那种风格，[【跳转到 12:00】](https://www.youtube.com/watch?v=7fh90mdg2pI&t=720)。

![打开 `pymol_rfdiffusion_aesthetic` 脚本，里头是预设的配色/出图函数](assets/第02讲_PyMol and VS Code (Mini-session)/00720.webp)

最后，PyMOL 的所有命令语法、例子都在 **PyMOLWiki** 上，可以直接复制粘贴，是巨大的资源库，强烈推荐，[【跳转到 16:35】](https://www.youtube.com/watch?v=7fh90mdg2pI&t=995)。

## 八、VS Code 与扩展：最流行的 IDE 长什么样

讲完 PyMOL，切换到 **Visual Studio Code**（简称 VS Code）。现场调查发现大多数同学用过 VS Code、也有人用过它的 SSH 远程功能，[【跳转到 17:01】](https://www.youtube.com/watch?v=7fh90mdg2pI&t=1021)。

![幻灯片刻画 VS Code 的定位：最流行的 IDE 之一、靠扩展增强、界面可个性化](assets/第02讲_PyMol and VS Code (Mini-session)/00995.webp)

### 8.1 为什么用它

VS Code 是**最流行的 IDE（集成开发环境）之一**，[【跳转到 17:12】](https://www.youtube.com/watch?v=7fh90mdg2pI&t=1032)。它的优点：

- **扩展（extensions）生态**带来海量功能；
- **可简可繁**：想简单就简单，想复杂就复杂；
- 界面非常友好、可个性化。

### 8.2 界面速览

- 上方是**中央命令区（Command Palette）**和一堆按钮，用来决定哪个面板弹出；面板可以**随意拖动、摆放**，实现个性化，[【跳转到 17:29】](https://www.youtube.com/watch?v=7fh90mdg2pI&t=1049)；
- 上方还有**终端（terminal）**，下方是**调试控制台（debug console）**。终端可以开**任意多个**，像浏览器标签页一样来回切换、随时删除，[【跳转到 17:54】](https://www.youtube.com/watch?v=7fh90mdg2pI&t=1074)；
- 左侧是 **Explorer（资源管理器）**：放入文件系统后可在文件间切换、在文档里搜索，还内置 **GitHub 控制**功能；再下面是 **Extensions（扩展）**、**Remote Explorer（远程资源管理器）**和 **Account（账户）**，[【跳转到 18:19】](https://www.youtube.com/watch?v=7fh90mdg2pI&t=1099)。

## 九、用 VS Code SSH 远程登录计算集群

接下来是本讲的重头戏：**用 SSH 远程登录集群**。

### 9.1 先装 Remote-SSH 扩展

如果还没装 SSH 客户端，去 **Extensions** 面板搜索并安装微软出品的 **Remote-SSH** 扩展，来自 **Microsoft**，安装只需两秒钟，[【跳转到 19:09】](https://www.youtube.com/watch?v=7fh90mdg2pI&t=1149)。这些扩展通常自带写得非常好的文档，遇到问题随时回去刷新查看，[【跳转到 19:31】](https://www.youtube.com/watch?v=7fh90mdg2pI&t=1171)。

![Remote-SSH 扩展页面：微软出品，用 SSH 打开远程机器上的任意文件夹](assets/第02讲_PyMol and VS Code (Mini-session)/01149.webp)

### 9.2 点击按钮、输入登录信息

装好之后，左下角会出现一个小按钮（不同的主题下位置可能略有差异），[【跳转到 19:41】](https://www.youtube.com/watch?v=7fh90mdg2pI&t=1181)。点击它，窗口正上方中央会弹出一个提示，要求你输入 **SSH 登录信息**，格式通常是：

```
你的邮箱ID@主机名
```

输入回车后，它会告诉你还需要哪些额外扩展（比如 **Python**），并**一步步引导你安装**，[【跳转到 19:52】](https://www.youtube.com/watch?v=7fh90mdg2pI&t=1192)。

### 9.3 实际效果

主讲人现场演示：点 SSH 后会得到一堆选项，可以进 **GitHub**、也可以连**远程仓库**，[【跳转到 20:39】](https://www.youtube.com/watch?v=7fh90mdg2pI&t=1239)。连上以后，左下角状态栏会显示当前连接，例如 `SSH: login.rockfish.jhu.edu`，说明你已经进到远程服务器了，[【跳转到 21:00】](https://www.youtube.com/watch?v=7fh90mdg2pI&t=1260)。

把文件放进 VS Code 界面，最简单的办法是在终端输入：

```
code <文件名>
```

也可以在界面里直接打开。

![成功 SSH 连接后，左下角显示远程主机名，终端可以直接操作集群](assets/第02讲_PyMol and VS Code (Mini-session)/01285.webp)

## 十、Jupyter、tmux 与 Protein Viewer：远程科研三件套

### 10.1 Jupyter notebook：在集群上边跑边画

连上集群后，可以打开 **Jupyter notebook**。演示里上方有完整的**文件路径面包屑**，方便在不同 Python 文件之间切换；接上 Git 仓库后，文件也会在这里列出来，[【跳转到 21:50】](https://www.youtube.com/watch?v=7fh90mdg2pI&t=1310)。

Jupyter notebook 最擅长两件事：**草稿（scratch）和绘图**，[【跳转到 22:15】](https://www.youtube.com/watch?v=7fh90mdg2pI&t=1335)。关键原因在于：

- 当你在**计算集群**上处理 AI 的超大数据集时，需要为很大的数据出图，但**不想把数据全部搬到本地桌面**（那会把本地撑爆）；
- Jupyter 让你用熟悉的 Python 绘图包**在集群上就地画图**，速度很快；
- 还可以用**交互式节点（interactive nodes）**把整个流程优化到极致，[【跳转到 22:40】](https://www.youtube.com/watch?v=7fh90mdg2pI&t=1360)。

![VS Code 里的 Jupyter notebook：顶部有文件路径，单元格里写 Python 导入与数据加载](assets/第02讲_PyMol and VS Code (Mini-session)/01310.webp)

**用 markdown 单元格做大纲**是另一个"救命"功能：[【跳转到 23:05】](https://www.youtube.com/watch?v=7fh90mdg2pI&t=1385)

- markdown 单元格就是放文字的地方，在文字前加 `#` 会变成类似 HTML 标题的效果（`#` 越多、级别越低），于是可以做出标题/副标题/小标题，并**快速跳转**；
- 好处有两个：一是**组织性极强**，二是**促使你去写注释、保证代码可读**。

主讲人推荐的工作流是：**先在自己的 notebook 里写草稿，等代码跑通之后，把它们全部注释掉，复制粘贴到一个 `.py` 文件里，并记录这段代码现在在哪个文件、该怎么运行**——这样你就对自己所有代码的位置一清二楚，最后再进 GitHub 保持整洁，[【跳转到 23:30】](https://www.youtube.com/watch?v=7fh90mdg2pI&t=1410)。

另外，打开装满**类和函数**的文件时，通常能调出一个**函数列表**并点击跳转，和 GitHub 网站上的体验类似，[【跳转到 24:20】](https://www.youtube.com/watch?v=7fh90mdg2pI&t=1460)。

### 10.2 tmux：让任务在后台一直跑

**tmux** 超级有用，[【跳转到 24:45】](https://www.youtube.com/watch?v=7fh90mdg2pI&t=1485)。它解决的问题是：

- 你在终端/VS Code 里跑任务时，一关笔记本就什么都丢了；
- 而 **tmux 让你把终端里的后台进程"脱开"（disengage）并保持运行**：你可以关掉笔记本、做任何事，再从**另一个客户端 SSH 回来，它还在跑**，完全不用担心中途被关掉，[【跳转到 25:10】](https://www.youtube.com/watch?v=7fh90mdg2pI&t=1510)。

### 10.3 Protein Viewer：不搬数据也能看蛋白

集群上会有大量 PDB 文件（它们很占空间），每次下载到本地都很麻烦。**Protein Viewer** 正是为此而生：它其实是 **PDB 网站上做结构查看器时用的同一个后台**，命令基本一致，但你可以**远程打开**它，[【跳转到 25:49】](https://www.youtube.com/watch?v=7fh90mdg2pI&t=1549)。

用法：

1. 在扩展市场安装 **Protein Viewer**（作者 **Arian Jamash**），[【跳转到 26:14】](https://www.youtube.com/watch?v=7fh90mdg2pI&t=1574)；
2. 如果你用 Jupyter notebook，还需要在 SSH 客户端上装好对应支持；
3. 通过 **show and run commands → protein viewer** 打开面板；
4. 在 **Explorer** 里定位到存放 PDB 的文件夹。**直接点** PDB 文件只会把它当文本打开（看到一堆行列）；**右键 → view in protein viewer**，就会在新标签页里打开三维视图，[【跳转到 28:23】](https://www.youtube.com/watch?v=7fh90mdg2pI&t=1703)。

![Protein Viewer 扩展：在编辑器里直接可视化蛋白质结构](assets/第02讲_PyMol and VS Code (Mini-session)/01460.webp)

打开后可以**摆弄三维表示、应用各种操作**：做透明度、按不同属性上色，甚至能按**残基属性**上色——比如**二级结构、残基名、疏水性（hydrophobicity）**，[【跳转到 27:13】](https://www.youtube.com/watch?v=7fh90mdg2pI&t=1633)。你还可以 **start protein here** 并输入 PDB ID；只要文件夹里有本地 PDB，也能直接抓取查看，[【跳转到 27:43】](https://www.youtube.com/watch?v=7fh90mdg2pI&t=1663)。总之，**不用把蛋白搬来搬去，全部远程完成**。

![在 VS Code 的新标签页里远程查看 1TQN 结构，左侧是状态树，右侧是结构工具](assets/第02讲_PyMol and VS Code (Mini-session)/01595.webp)

## 小结

- **工具定位**：PyMOL 负责"**看结构**"（内置 Python 的分子可视化软件），VS Code 负责"**写代码 / 连集群**"（最流行的 IDE 之一，靠扩展增强）。两者都是领域内最常用的工具，但都深不见底，先用基础功能上手即可，[00:11](https://www.youtube.com/watch?v=7fh90mdg2pI&t=11)。
- **PyMOL 核心命令**：`fetch` 取结构、`remove hetatm/water` 清理、`A/S/H` 控制通用操作/显示/隐藏、`color` 按 element/SS/B Factor/chain 上色、`align` 做结构与序列比对、`set cartoon_transparency, 数值, 对象` 做重点高亮、`ray`+`save image` 出发表级图片。
- **B Factor 是预测模型的"信心条"**：AlphaFold 等输出里，它表示模型对每个预测区域的置信度，按它上色能一眼看出可靠区与问题区。
- **VS Code 远程开发的完整链条**：装 **Remote-SSH** 扩展 → 点左下角 SSH 按钮 → 输入 `邮箱ID@主机名` → 按提示补装 Python 等扩展 → 用 `code <文件>` 或界面打开文件。
- **远程科研三件套**：**Jupyter notebook**（集群上就地绘图、markdown 做大纲）、**tmux**（后台任务不因关电脑而中断）、**Protein Viewer**（远程直接看 PDB，不用搬数据）。
- **工作流建议**：草稿写在 notebook → 跑通后注释并整理进 `.py` 文件 → 记录代码位置 → 进 GitHub 保持整洁。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| PyMOL | 内置 Python 的分子可视化软件，既可用 GUI 也可用脚本/命令操作结构 |
| PDB | 蛋白质结构的标准文本格式，记录每个原子的坐标；`fetch <ID>` 可下载 |
| GUI | 图形用户界面，能用鼠标点击操作 |
| **A / S / H** | PyMOL 对象面板的 Action / Show / Hide 三组核心命令 |
| cartoon / ribbon / lines / surface / mesh | PyMOL 的几种结构表示方式，分别强调二级结构、骨架线、表面与堆积 |
| SS（secondary structure） | 二级结构，如 α 螺旋、β 折叠、loop 环 |
| B Factor | PDB 末尾一列；实验结构中表示温度/柔性，预测模型（如 AlphaFold）中表示预测置信度 |
| CDR | 抗体上决定抗原结合的关键环区，常单独选中、命名、研究 |
| align | PyMOL 的结构+序列比对功能，把多个结构叠合到参考对象上 |
| cartoon transparency | 卡通透明度命令，用来淡化其他部分、突出目标区域 |
| ray / draw | PyMOL 出图命令：draw 快（截图），ray 慢（光线追踪，发表级） |
| PyMOLWiki | PyMOL 官方 wiki，命令语法与示例的资源库 |
| IDE | 集成开发环境，VS Code 是最流行的之一 |
| Extension（扩展） | VS Code 的可下载功能模块，如 Remote-SSH、Jupyter、Protein Viewer |
| Remote-SSH | 微软出品的 VS Code 扩展，用 SSH 打开远程机器上的文件夹 |
| SSH | 安全远程登录协议，用 `邮箱ID@主机名` 连接计算集群 |
| Jupyter notebook | 交互式笔记本，适合草稿与在集群上就地绘图；用 markdown 单元格做大纲 |
| tmux | 终端复用器，让后台任务在你断开/关电脑后继续运行 |
| Protein Viewer | VS Code 扩展，远程可视化 PDB 结构，后台与 PDB 网站一致 |
| hydrophobicity | 疏水性，可按其给残基上色，帮助判断蛋白表面性质 |
