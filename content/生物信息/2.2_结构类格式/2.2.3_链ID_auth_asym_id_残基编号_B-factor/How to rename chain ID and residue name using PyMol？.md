# How to rename chain ID and residue name using PyMol?

> 视频来源：[How to rename chain ID and residue name using PyMol?](https://www.youtube.com/watch?v=b9FjwGgrTNU)（约 11 分钟英文实操教程）。本文基于该视频的「图-字幕」演说文稿整理，所有要点均可回看视频核对。

**一句话结论：改 PDB 结构里的残基名与链 ID，用 PyMOL 两条 `alter` 命令最直接——`alter (sele), resn=ASP` 改残基名、`alter (sele), chain=B` 改链 ID，再 `sort` 一下，最后 Export Molecule 另存为新 PDB 即可；先弄清"为什么改"（非标准残基 → 标准氨基酸；独立实体 → 独立链），再动手。**

## 本讲要解决的核心问题（SCQA）

**背景**：这是 VMD / Chimera 系列教程的后续。前几集处理了 AspRS（天冬酰-tRNA 合成酶）与配体的复合物结构：在 VMD 里从原始 PDB 的两条亚基中只保留一条，然后在 Chimera 里把配体 AMO 化学编辑成 L-天冬氨酸，又把手性翻转为 D-天冬氨酸 [【跳转到 00:00】](https://www.youtube.com/watch?v=b9FjwGgrTNU&t=0)。

**冲突**：化学身份改了，PDB 里的"身份证"却没变——这个残基还叫 **AMO**（非标准残基名），而且还挂在受体所在的 **A 链**里。结构文件与真实化学对不上了 [【跳转到 00:25】](https://www.youtube.com/watch?v=b9FjwGgrTNU&t=25)。

**疑问**：为什么必须改残基名和链 ID？用什么工具改最省事？

**回答（中心思想）**：残基名必须改成标准三字母 **ASP**（它已是氨基酸、属于蛋白域）；链 ID 必须给独立的 **B**（它只是非共价结合在受体口袋里，是独立实体）。VMD / Chimera 都能改但绕，**PyMOL 的 `alter` 命令最直接**。

![视频开场：本讲承接 VMD/Chimera 教程，处理 AspRS–配体复合物的残基名与链 ID 问题](assets/How%20to%20rename%20chain%20ID%20and%20residue%20name%20using%20PyMol？/00000.webp)

## 一、为什么改：残基名与链 ID 各有各的理由

### 1.1 残基名：非标准残基 → 标准氨基酸

当前这个残基的 ID 是 **AMO**——一个**非标准残基**（non-standard residue），不是蛋白残基。但编辑后的 L-天冬氨酸是真正的氨基酸，**属于蛋白域（protein domain）**，所以名字必须改成 **ASP**——天冬氨酸作为蛋白氨基酸的标准三字母码 [【跳转到 00:50】](https://www.youtube.com/watch?v=b9FjwGgrTNU&t=50)。

![残基名为什么改：AMO 是非标准残基，编辑后的 L-天冬氨酸应使用标准三字母码 ASP](assets/How%20to%20rename%20chain%20ID%20and%20residue%20name%20using%20PyMol？/00050.webp)

### 1.2 链 ID：独立实体要有独立编号

L-ASP 将成为一个**独立实体**：它与受体之间没有共价键，只在 AspRS 的结合口袋里发生非共价相互作用，所以需要独立的 ID。如果受体的链 ID 是 **A**，那么配体的链 ID 就应改成 **B** [【跳转到 01:15】](https://www.youtube.com/watch?v=b9FjwGgrTNU&t=75)。

![链 ID 为什么改：配体与受体非共价结合、是独立实体，应从 A 链分出为 B 链](assets/How%20to%20rename%20chain%20ID%20and%20residue%20name%20using%20PyMol？/00075.webp)

## 二、准备工作：用评估版 PyMOL 载入结构

- 用 VMD 和 Chimera 也能重命名链与残基，但都要绕些弯路；所以这里改用 **PyMOL**——非常强大、操作又简单。双击桌面快捷方式启动（Windows 下）[【跳转到 01:39】](https://www.youtube.com/watch?v=b9FjwGgrTNU&t=99)。

![工具选择：PyMOL 比在 VMD/Chimera 里绕路更直接](assets/How%20to%20rename%20chain%20ID%20and%20residue%20name%20using%20PyMol？/00099.webp)

- 启动后会提示购买付费版，**不需要**：评估版（evaluation version）就够用，功能已经很多；直接跳过激活 [【跳转到 02:04】](https://www.youtube.com/watch?v=b9FjwGgrTNU&t=124)。
- **File → Open** 载入上一集 Chimera 保存的结构（workspace one 目录），选择 **L-ASP bound to AspRS**；同一目录里还有手性翻转得到的 D-ASP 版本 [【跳转到 02:22】](https://www.youtube.com/watch?v=b9FjwGgrTNU&t=142)。

![File → Open 载入上次 Chimera 保存的 L-ASP–AspRS 结构](assets/How%20to%20rename%20chain%20ID%20and%20residue%20name%20using%20PyMol？/00142.webp)

- 结构加载后默认就是 new-cartoon / ribbon 表示，配体虽然名义上叫 AMO、实际已是 L-ASP，以 licorice（棍棒）方式显示——**表示方式无需任何调整** [【跳转到 02:46】](https://www.youtube.com/watch?v=b9FjwGgrTNU&t=166)。

![加载完成：ribbon 表示的 AspRS，配体以 licorice 显示，无需调整表示](assets/How%20to%20rename%20chain%20ID%20and%20residue%20name%20using%20PyMol？/00166.webp)

## 三、显示序列：先"看见"要改的残基

本讲的目标很明确：把残基 **AMO** 改名为 **ASP**，并把它的链 ID 从 A 改成 B [【跳转到 03:09】](https://www.youtube.com/watch?v=b9FjwGgrTNU&t=189)。

第一步是**显示序列**（Display → Sequence）：沿着序列走、选中特定残基会容易得多 [【跳转到 03:34】](https://www.youtube.com/watch?v=b9FjwGgrTNU&t=214)。

序列显示出来后能立刻看到一个细节 [【跳转到 03:59】](https://www.youtube.com/watch?v=b9FjwGgrTNU&t=239)：

- 蛋白残基全部用**单字母码**显示（G、N、A……）；
- 唯独末尾的 **AMO 用三字母码**——因为它是非标准残基，没有单字母码、不被当作蛋白残基识别。

![序列面板：蛋白残基是单字母码，AMO 因非标准而以三字母显示](assets/How%20to%20rename%20chain%20ID%20and%20residue%20name%20using%20PyMol？/00239.webp)

接着把序列显示模式切换为 **residue names**（残基三字母码；也可以选原子名），并注意序列面板上的**链标识列：包括配体在内全都是 A**——这正是要改的地方 [【跳转到 04:24】](https://www.youtube.com/watch?v=b9FjwGgrTNU&t=264)。

![切换为 residue names 模式：链标识列显示 A——配体也挂在 A 链上，需要拆出](assets/How%20to%20rename%20chain%20ID%20and%20residue%20name%20using%20PyMol？/00264.webp)

选中操作：**在序列或视口中单击一次**即可选中并高亮该残基。顺带两个视图技巧：PyMOL 里缩放是**按住鼠标右键拖动**——往下拖是缩小（拉远），朝自己方向拖是放大 [【跳转到 04:49】](https://www.youtube.com/watch?v=b9FjwGgrTNU&t=289)。

## 四、两条 alter 命令完成改名

### 4.1 命令行是主力

PyMOL 自带**命令行接口**，和 VMD 的脚本语言、Chimera 的命令行类似 [【跳转到 05:14】](https://www.youtube.com/watch?v=b9FjwGgrTNU&t=314)。命令输入区就在 GUI 下方；**按 Tab 可以列出可用命令**，用这套 PyMOL 语言能做很多事（视频幻灯片里附了可跟随的官方链接）[【跳转到 05:34】](https://www.youtube.com/watch?v=b9FjwGgrTNU&t=334)。

改残基名 / 链 ID 的命令是 **`alter`**。语法要点 [【跳转到 05:59】](https://www.youtube.com/watch?v=b9FjwGgrTNU&t=359)：

- `(sele)`：**选择的简称**，指代刚才点选的原子集；
- `resn`：**residue name（残基名）**属性的短名。

### 4.2 改残基名：`alter (sele), resn=ASP`

输入 `alter (sele), resn=ASP` 后回车，立竿见影：**序列里的 AMO 当场变成 ASP** [【跳转到 06:24】](https://www.youtube.com/watch?v=b9FjwGgrTNU&t=384)。

![alter (sele), resn=ASP 执行后：序列中的 AMO 当场变成 ASP](assets/How%20to%20rename%20chain%20ID%20and%20residue%20name%20using%20PyMol？/00384.webp)

### 4.3 改链 ID：`alter (sele), chain=B`

同一个命令换个属性即可：`alter (sele), chain=B`（B 要带引号），回车后**链 ID 立即变成 B** [【跳转到 06:49】](https://www.youtube.com/watch?v=b9FjwGgrTNU&t=409)。

![alter (sele), chain=B 执行后：配体的链 ID 由 A 变为 B](assets/How%20to%20rename%20chain%20ID%20and%20residue%20name%20using%20PyMol？/00409.webp)

### 4.4 收尾：`sort` 让改动归位

为确保修改生效，再敲一条 **`sort`** 并回车：链会被重新排序——**受体链 A 排在前面，配体（现已是 ASP、链 B）排在最后**。之后在分子外侧点击即可取消选择 [【跳转到 07:14】](https://www.youtube.com/watch?v=b9FjwGgrTNU&t=434)。

## 五、导出保存：Export Molecule 的选项逐个看

改完残基名与链 ID，接下来把结构**另存为独立的 PDB**：**File → Export Molecule** [【跳转到 07:39】](https://www.youtube.com/watch?v=b9FjwGgrTNU&t=459)。导出对话框里的选项值得逐个认识 [【跳转到 07:54】](https://www.youtube.com/watch?v=b9FjwGgrTNU&t=474)：

- **Original atom order**：勾选后保留初始加载 PDB 中的原子顺序；
- **Write CONNECT records**：把原子间找到的**共价键**写成记录——内容是按**原子序号的索引**；
- **Retain atom IDs**：保留原子 ID。这一项在**后续跑模拟时很重要**：拿到复合物结构后若要用 **GROMACS** 这类 MD 引擎做模拟，它需要能识别特定的原子 ID / 原子类型——本演示先不勾选 [【跳转到 08:19】](https://www.youtube.com/watch?v=b9FjwGgrTNU&t=499)；
- **Segment identifier**：PDB 文件**最后一列**的片段标识，有时查看它很有用 [【跳转到 08:44】](https://www.youtube.com/watch?v=b9FjwGgrTNU&t=524)；
- **Header information**：与从 Protein Data Bank 下载的原始 PDB 一样，文件开头有结构描述、实验方法等**文件头信息**；不需要也可以不勾 [【跳转到 08:44】](https://www.youtube.com/watch?v=b9FjwGgrTNU&t=524)。

确认好原子坐标区域后，保存到同一目录（workspace one），**换一个新文件名**——不要覆盖之前已写出的 L-ASP/AspRS 文件。命名建议带上 **`_mod`** 后缀，标记这是"改过的 PDB" [【跳转到 09:26】](https://www.youtube.com/watch?v=b9FjwGgrTNU&t=566)。

![导出对话框：新文件名带 _mod 后缀，避免覆盖原文件](assets/How%20to%20rename%20chain%20ID%20and%20residue%20name%20using%20PyMol？/00566.webp)

关于格式选项：对话框里有 **PDBx/mmCIF**（CIF）一项。CIF 文件一般对应**晶体结构**——X 射线晶体学解出的结构常用 CIF 格式；但现在我们要的是简单 PDB，所以选择普通 PDB 格式并使用 **`.pdb`** 扩展名，点击保存 [【跳转到 09:51】](https://www.youtube.com/watch?v=b9FjwGgrTNU&t=591)。

![格式选择：PDBx/mmCIF 常见于晶体学，此处选简单 PDB 并用 .pdb 扩展名](assets/How%20to%20rename%20chain%20ID%20and%20residue%20name%20using%20PyMol？/00591.webp)

## 六、文本验证：改没改成功，打开文件就知道

想确认结果，就**以文本方式查看**：关闭 PyMOL，用你喜欢的文本编辑器打开刚保存的 `_mod.pdb` [【跳转到 10:21】](https://www.youtube.com/watch?v=b9FjwGgrTNU&t=621)。

验证结果非常清楚 [【跳转到 10:26】](https://www.youtube.com/watch?v=b9FjwGgrTNU&t=626)：

- **蛋白部分的链 ID 依然是 A**——没有被动过；
- 一路滚到**文件末尾配体所在处**：链 ID 已是 **B**，残基名也已是 **ASP** [【跳转到 10:51】](https://www.youtube.com/watch?v=b9FjwGgrTNU&t=651)。

残基名与链 ID 的重命名**成功完成**。

![文本验证：蛋白链保持 A，文件末尾的配体已是链 B、残基名 ASP](assets/How%20to%20rename%20chain%20ID%20and%20residue%20name%20using%20PyMol？/00651.webp)

## 小结

- **先想清楚为什么改**：非标准残基（AMO）改成了标准氨基酸就该用标准三字母码（ASP）；非共价结合的独立实体就该有独立链 ID（A → B）。
- **PyMOL 三步法**：点选残基得到 `(sele)` → `alter (sele), resn=ASP` 与 `alter (sele), chain=B` → `sort` 归位。
- **序列面板是导航**：Display → Sequence；非标准残基只能以三字母显示，链标识列能一眼看出配体挂在哪条链。
- **Export Molecule 选项有讲究**：原子顺序、CONNECT records（共价键索引）、retain atom IDs（跑 GROMACS 等 MD 前尤其重要）、segment identifier、header information。
- **另存不覆盖**：新文件名带 `_mod` 后缀；需要 PDBx/mmCIF 还是简单 PDB 视用途而定。
- **文本验证收尾**：蛋白链仍是 A，末尾配体已是 B 链 + ASP——重命名成功。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| AspRS | 天冬酰-tRNA 合成酶，本教程系列的受体蛋白 |
| AMO | 编辑前的非标准残基（配体）名，无单字母码 |
| ASP / L-ASP / D-ASP | 天冬氨酸标准三字母码 / 其 L 型与 D 型（手性翻转） |
| `(sele)` | PyMOL 中"当前选择"的简称，alter 命令的操作对象 |
| `alter` | PyMOL 修改原子属性的命令，如 `resn`（残基名）、`chain`（链 ID） |
| `sort` | 让链/原子重新排序、使修改归位的命令 |
| CONNECT records | PDB 中以原子序号索引记录的共价键信息 |
| Segment identifier | PDB 每行最后一列的片段标识 |
| PDBx/mmCIF | 晶体学常用的现代结构格式；与简单 PDB 格式在导出时可二选一 |
