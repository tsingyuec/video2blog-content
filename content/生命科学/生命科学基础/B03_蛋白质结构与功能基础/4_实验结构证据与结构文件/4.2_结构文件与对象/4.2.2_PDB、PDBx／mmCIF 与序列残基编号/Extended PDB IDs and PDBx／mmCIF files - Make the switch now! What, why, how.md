# Extended PDB IDs and PDBx/mmCIF files - Make the switch now! What, why, how

> 视频来源：[Extended PDB IDs and PDBx/mmCIF files - Make the switch now! What, why, how](https://www.youtube.com/watch?v=U-MEtWaFNdI)（wwPDB 官方科普，约 5.5 分钟）。本文基于该视频的「图-字幕」演说文稿整理，所有要点均可回看视频核对。

**一句话结论：4 字符的 PDB ID 和 legacy PDB 文件格式正在退出历史舞台，扩展 PDB ID（12 字符）与 PDBx/mmCIF 格式现在就能用——今天就该把你的工作流切换过去。**

## 本讲要解决的核心问题（SCQA）

**背景**：做结构生物信息的人，早就习惯了用 4 字符 PDB ID（如 `4HHB`）下载结构，也习惯了传统的 PDB 文件格式。

**冲突**：这套路子正在失效——4 字符编号池即将用尽；而且旧 PDB 格式列宽固定、信息装不下，一些大而复杂的结构干脆不提供旧格式文件。

**疑问**：编号用完了怎么办？旧格式装不下的信息放哪里？

**回答（中心思想）**：切换到 12 字符的**扩展 PDB ID** 和 **PDBx/mmCIF 文件格式**。旧 ID 可以零成本映射成新 ID，新格式现在就被主流软件支持——这是一场可以平滑完成的迁移，越早切越省事。

![视频开场：一次 PSA，提醒大家避开蛋白质领域的 Y2K 危机](assets/Extended%20PDB%20IDs%20and%20PDBx／mmCIF%20files%20-%20Make%20the%20switch%20now!%20What,%20why,%20how/00000.webp)

## 一、4 字符 ID + 旧格式，为什么撑不下去了

### 1.1 编号池见底：4 字符 ID 快用完了

PDB（Protein Data Bank，蛋白质数据库）是查询蛋白质及其他生物大分子三维结构的首选数据库 [【跳转到 00:00】](https://www.youtube.com/watch?v=U-MEtWaFNdI&t=0)。一直以来，你用一个 **4 字符的 PDB ID** 来访问每条结构记录。但 4 个字符的组合是有限的——官方已经开始发放 **12 字符的扩展 PDB ID（extended PDB ID）**，并希望大家现在就开始切换 [【跳转到 00:18】](https://www.youtube.com/watch?v=U-MEtWaFNdI&t=18)。

### 1.2 旧格式的三重局限

去 PDB 下载文件时你会看到一种 **legacy PDB 格式**（旧版格式）。它有三处硬伤 [【跳转到 00:35】](https://www.youtube.com/watch?v=U-MEtWaFNdI&t=35)：

- **有些结构根本没有旧格式文件**——结构太大、太复杂（原子数太多）时，旧格式根本写不下 [【跳转到 01:00】](https://www.youtube.com/watch?v=U-MEtWaFNdI&t=60)；
- **装不下 mmCIF 里的全部信息**——旧格式承载的信息量更少；
- **格式过严**——列数固定、每列宽度固定 [【跳转到 03:35】](https://www.youtube.com/watch?v=U-MEtWaFNdI&t=215)。这带来两个后果：处理不了特别长、特别复杂的分子，也放不下 map（电子密度图）这类数据——而 mmCIF 都可以。此外，计算机处理 mmCIF 也更顺畅。

![旧版 legacy PDB 格式的局限：列数与列宽固定，精度和信息量都受限](assets/Extended%20PDB%20IDs%20and%20PDBx／mmCIF%20files%20-%20Make%20the%20switch%20now!%20What,%20why,%20how/00215.webp)

## 二、mmCIF 到底是什么

PDBx/mmCIF 的全称是 **Protein Data Bank Exchange Macromolecular Crystallographic Information Framework**（蛋白质数据库交换·大分子晶体学信息框架）[【跳转到 01:36】](https://www.youtube.com/watch?v=U-MEtWaFNdI&t=96)。拆开看：

- **CIF** = Crystallographic Information Framework，晶体学信息框架，是晶体学界通用的文本数据格式；
- **mm** = macromolecular，表示它面向生物大分子；
- **PDBx** = PDB exchange，表示这是 PDB 生态使用的交换版本。

关键的一点：**文件后缀是 `.cif`，不是 `.pdb`**。这种 CIF 文件你现在就可以用，可以说它正在成为标准 [【跳转到 02:01】](https://www.youtube.com/watch?v=U-MEtWaFNdI&t=121)。所以即便某个结构还同时提供 legacy 格式，也请下载 PDBx/mmCIF 版本——旧格式正在被逐步淘汰，以后会不再兼容 [【跳转到 02:06】](https://www.youtube.com/watch?v=U-MEtWaFNdI&t=126)。

![PDBx/mmCIF 的全称拆解：CIF 是晶体学信息框架，mm 表示大分子](assets/Extended%20PDB%20IDs%20and%20PDBx／mmCIF%20files%20-%20Make%20the%20switch%20now!%20What,%20why,%20how/00096.webp)

## 三、扩展 PDB ID：怎么把旧 ID 变成新 ID

扩展 PDB ID 有 12 个字符长。适配规则非常简单 [【跳转到 00:35】](https://www.youtube.com/watch?v=U-MEtWaFNdI&t=35)：

- **旧 4 字符 ID**：在前面加上 `pdb_` 和 4 个 0，再接旧编号。比如旧 ID `9CN3` 对应扩展 ID `pdb_00009CN3`；
- **未来发放的新 ID**：从一开始就是完整的 12 字符，但同样以 `pdb_` 开头 [【跳转到 04:34】](https://www.youtube.com/watch?v=U-MEtWaFNdI&t=274)。

![扩展 PDB ID 的适配规则：旧 4 字符 ID 前面补 pdb_0000](assets/Extended%20PDB%20IDs%20and%20PDBx／mmCIF%20files%20-%20Make%20the%20switch%20now!%20What,%20why,%20how/00274.webp)

时间表也很明确 [【跳转到 05:00】](https://www.youtube.com/watch?v=U-MEtWaFNdI&t=300)：

- 预计 **2029 年左右**，4 字符旧 ID 退场；
- 2029 之后只发放扩展 ID；
- 扩展 ID **现在就已可用**，而且旧 ID 补零扩展后随时可以访问想要的结构——不存在断档。

## 四、现在就能用的操作指南

### 4.1 PyMOL：命令行 fetch 已支持，菜单暂不支持

12 字符扩展 ID 已经可以配合分子查看软件使用 [【跳转到 02:06】](https://www.youtube.com/watch?v=U-MEtWaFNdI&t=126)。以 PyMOL 为例 [【跳转到 02:25】](https://www.youtube.com/watch?v=U-MEtWaFNdI&t=145)：

```text
fetch pdb_00009CN3
```

在命令行执行 `fetch` 加扩展 ID，就能直接加载对应结构。但注意：如果你走"简便途径"——用菜单里的 Get PDB——**目前还不支持长编号**（估计以后会更新支持），这条路现在只认 4 字符编号；不过你可以在命令行输入 `fetch` 来绕过 [【跳转到 02:45】](https://www.youtube.com/watch?v=U-MEtWaFNdI&t=165)。

![在 PyMOL 中用 fetch 命令加载扩展 PDB ID 对应的结构](assets/Extended%20PDB%20IDs%20and%20PDBx／mmCIF%20files%20-%20Make%20the%20switch%20now!%20What,%20why,%20how/00145.webp)

### 4.2 下载到本地再看

另一个选择是直接从 PDB 网站把 CIF 文件下载到本地，然后用 PyMOL 打开：走 `File → Open`，甚至直接把 CIF 文件**拖进**查看器窗口即可 [【跳转到 02:55】](https://www.youtube.com/watch?v=U-MEtWaFNdI&t=175)。

## 五、换编号还有个隐藏好处：避免撞名

4 字符组合是有限的，有些组合恰好是基因或蛋白质名称的缩写 [【跳转到 03:51】](https://www.youtube.com/watch?v=U-MEtWaFNdI&t=231)。最早一批 PDB ID 起名还有含义可循——比如一些血红蛋白相关的编号就叫 `HBB` 之类；但后来的新 ID 基本是随机的，而且 4 字符池也快用完了 [【跳转到 04:04】](https://www.youtube.com/watch?v=U-MEtWaFNdI&t=244)。

换成带 `pdb_` 前缀的 12 字符编号后，这类混淆就大幅减少：旧编号本不该表达含义，却可能在你的代码里撞上某个基因或蛋白的缩写（比如你在搜 gigahertz，却碰上一个叫 `GHz` 的 ID），平添麻烦 [【跳转到 04:09】](https://www.youtube.com/watch?v=U-MEtWaFNdI&t=249)。

## 小结

- PDB 正在从 4 字符 ID 切换到 **12 字符扩展 PDB ID**，预计 2029 年左右旧 ID 全面退场；
- 旧 ID 零成本适配：前面补 `pdb_0000` 即可；新 ID 从一开始就是 12 字符、`pdb_` 开头；
- **PDBx/mmCIF** 是取代 legacy PDB 的现代格式：后缀 `.cif`，信息更全、没有列宽限制、能装下电子密度图，计算机处理也更友好；
- 下载结构时**优先选 mmCIF 文件**，即使旧格式还在——它正在被淘汰；
- PyMOL 的 `fetch` 命令已支持扩展 ID；菜单方式暂时只认 4 字符；也可以下载 CIF 后直接拖入查看器。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| PDB ID | PDB 数据库中每条结构记录的编号，传统为 4 字符（如 `4HHB`） |
| 扩展 PDB ID | 12 字符的新编号（如 `pdb_00009CN3`），旧 ID 补 `pdb_0000` 前缀即得 |
| legacy PDB 格式 | 旧版结构文件格式，列数与列宽固定，信息承载能力有限 |
| PDBx/mmCIF | 现代结构文件格式，后缀 `.cif`，无列宽限制、信息更全 |
| CIF | Crystallographic Information Framework，晶体学信息框架，mmCIF 的基础 |
| map 数据 | 电子密度图等实验数据，旧 PDB 格式放不下，mmCIF 可以 |
