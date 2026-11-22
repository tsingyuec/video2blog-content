# EP 12 ｜ Post MD simulation assessment of Protein Ligand Complex in Gromacs ｜ RMSD, RMSF, H-bonds, Rg

> 视频来源：[YouTube《EP 12 | Post MD simulation assessment of Protein Ligand Complex in Gromacs | RMSD, RMSF, H-bonds, Rg》](https://www.youtube.com/watch?v=thxwcKRolM4)（24:27，频道：Learn-at-ease）。作者系列前几集已完整跑完蛋白-配体复合物的 GROMACS 动力学，本集是收官一讲：**跑完 MD 之后怎么"读"轨迹**——重新居中/去包裹轨迹，再依次算 RMSD（配体拟蛋白）、RMSF、蛋白-配体氢键、回旋半径（Rg）与能量项，全部用 `gmx` 命令 + xmgrace 出图。命令文件可从作者 GitHub 仓库下载（视频简介有链接）。视频字幕为 YouTube en-orig 自动字幕（yt-dlp 直拉），已逐窗口纠正错拼（"grow Max/gromex/Romex"→GROMACS、"liquid fit protein"→Lig fit Prot、"xvd/svg"→.xvg、"grades/Grays/great"→Grace、"guy rate/guide at one"→gyrate、"tons/Tu and S"→-tu ns、"least square bit/feet"→least squares fit 等）；本文基于文稿整理，所有操作可点时间戳回看核对。

## 本讲要解决的核心问题（SCQA）

**背景**：上一环节已经把蛋白-配体复合物在 GROMACS 里跑出了成品轨迹（工作目录 `gromacs_protein_ligand_main` 里躺着全部输出文件，[【跳转到 00:30】](https://www.youtube.com/watch?v=thxwcKRolM4&t=30)）。

**冲突**：轨迹文件里只有一帧帧坐标——"这个配体结合得稳不稳"光靠肉眼看动画是说不清的，论文里需要一张张**可量化、可比较**的图。

**疑问**：跑完 MD 到底应该算哪些量？每个量回答什么问题？

**回答（中心思想）**：后评估"五件套"——**RMSD**（结构漂没漂）、**RMSF**（哪里在动）、**氢键**（接触还在不在）、**Rg**（整体紧不紧）、**能量项**（模拟健不健康），再配 xmgrace 出图（[【跳转到 01:08】](https://www.youtube.com/watch?v=thxwcKRolM4&t=68)）。

![本集主题：MD 轨迹的后评估](assets/EP%2012%20｜%20Post%20MD%20simulation%20assessment%20of%20Protein%20Ligand%20Complex%20in%20Gromacs%20｜%20RMSD%2C%20RMSF%2C%20H-bonds%2C%20Rg/00000.webp)

## 一、第零步：终端就位 + 轨迹重新居中

在**工作目录**里右键"Open in Terminal"，确认终端指向当前目录；如果 GROMACS 是自己编译安装的，先 `source` 安装包路径让终端认识 `gmx` 命令，再 `gmx --version` 验证（作者的环境显示 GPU support 已启用，[【跳转到 02:17】](https://www.youtube.com/watch?v=thxwcKRolM4&t=137)、[【跳转到 03:07】](https://www.youtube.com/watch?v=thxwcKRolM4&t=187)）。

跑分析之前有一个容易忽略的步骤：**重新居中与去包裹（re-centering and re-wrapping）**。模拟盒子是周期性边界，跑着跑着分子可能"出盒子"或整体漂移，直接算 RMSD 会被这些假象污染。用 `gmx trjconv` 处理：**居中组选 Protein（1），输出组选 System（0）**，得到 `md_center.xtc`，后续所有分析都用这份干净轨迹（[【跳转到 05:27】](https://www.youtube.com/watch?v=thxwcKRolM4&t=327)）。命令文件里另有一条导出 PDB 帧的额外命令，本集用不到，直接跳过（[【跳转到 07:12】](https://www.youtube.com/watch?v=thxwcKRolM4&t=432)）。

GROMACS 命令执行成功的标志是界面弹出**青色括号的选择提示**并正常生成输出文件（[【跳转到 06:17】](https://www.youtube.com/watch?v=thxwcKRolM4&t=377)）。

![trjconv：居中选 Protein、输出选 System，得到 md_center.xtc](assets/EP%2012%20｜%20Post%20MD%20simulation%20assessment%20of%20Protein%20Ligand%20Complex%20in%20Gromacs%20｜%20RMSD%2C%20RMSF%2C%20H-bonds%2C%20Rg/00302.webp)

## 二、RMSD：配体在口袋里有没有"跑偏"

用 `gmx rms` 算 RMSD，两次选择分别是：**least squares fit（最小二乘拟合）选 Protein（1）**，**输出组选 Lig（13）**，得到 `rmsd.xvg`（[【跳转到 08:20】](https://www.youtube.com/watch?v=thxwcKRolM4&t=500)）。这就是"**配体拟蛋白**"的 RMSD：先把每帧蛋白叠合到参考构象上，再看配体相对口袋漂了多少——它直接回答"**配体还老老实实待在结合位点里吗**"。

用 `xmgrace rmsd.xvg` 出图（需安装 Grace，作者另有安装教程，[【跳转到 09:16】](https://www.youtube.com/watch?v=thxwcKRolM4&t=556)）。默认横轴是**皮秒**，想换成纳秒就在命令后加 **`-tu ns`**（[【跳转到 09:46】](https://www.youtube.com/watch?v=thxwcKRolM4&t=586)）。小知识：重复输出同名文件时，GROMACS 会把旧文件改名为 `#文件名.1#` 留底，认准不带 `#` 的新文件即可（[【跳转到 11:15】](https://www.youtube.com/watch?v=thxwcKRolM4&t=675)）。

![gmx rms：拟合组 Protein、输出组 Lig](assets/EP%2012%20｜%20Post%20MD%20simulation%20assessment%20of%20Protein%20Ligand%20Complex%20in%20Gromacs%20｜%20RMSD%2C%20RMSF%2C%20H-bonds%2C%20Rg/00475.webp)

![配体拟蛋白的 RMSD 曲线](assets/EP%2012%20｜%20Post%20MD%20simulation%20assessment%20of%20Protein%20Ligand%20Complex%20in%20Gromacs%20｜%20RMSD%2C%20RMSF%2C%20H-bonds%2C%20Rg/00581.webp)

![加 -tu ns 后横轴变为纳秒；旧文件被 # 包裹备份](assets/EP%2012%20｜%20Post%20MD%20simulation%20assessment%20of%20Protein%20Ligand%20Complex%20in%20Gromacs%20｜%20RMSD%2C%20RMSF%2C%20H-bonds%2C%20Rg/00666.webp)

再算一条**骨架 RMSD** 做对照：同样的命令，输出文件改名 `rmsd1.xvg`，拟合组仍选 Protein（1），输出组选 **Backbone（4）**（[【跳转到 12:57】](https://www.youtube.com/watch?v=thxwcKRolM4&t=777)）。之后 `xmgrace rmsd.xvg rmsd1.xvg` 把两条曲线**画在同一张图里**——骨架 RMSD 平稳、配体 RMSD 也平稳，才是"复合物稳定结合"的完整证据（[【跳转到 13:56】](https://www.youtube.com/watch?v=thxwcKRolM4&t=836)）；作者提醒这样的图截图就能放进论文。

![骨架 RMSD：拟合 Protein、输出 Backbone](assets/EP%2012%20｜%20Post%20MD%20simulation%20assessment%20of%20Protein%20Ligand%20Complex%20in%20Gromacs%20｜%20RMSD%2C%20RMSF%2C%20H-bonds%2C%20Rg/00777.webp)

![两条 RMSD 同图对比，可截图入论文](assets/EP%2012%20｜%20Post%20MD%20simulation%20assessment%20of%20Protein%20Ligand%20Complex%20in%20Gromacs%20｜%20RMSD%2C%20RMSF%2C%20H-bonds%2C%20Rg/00836.webp)

## 三、RMSF：哪里在动

`gmx rmsf` 算**逐原子/逐残基涨落**：想看骨架就选 Backbone（4），想看配体就选 Lig（13），输出 `rmsf.xvg`（[【跳转到 14:53】](https://www.youtube.com/watch?v=thxwcKRolM4&t=893)）。图里横轴是原子编号，峰越高代表这个位置在模拟全程里动得越凶——配体上如果只有两端"尾巴"在晃、核心骨架平稳，结合姿态就值得信任（[【跳转到 16:02】](https://www.youtube.com/watch?v=thxwcKRolM4&t=962)）。

![配体的 RMSF：逐原子涨落](assets/EP%2012%20｜%20Post%20MD%20simulation%20assessment%20of%20Protein%20Ligand%20Complex%20in%20Gromacs%20｜%20RMSD%2C%20RMSF%2C%20H-bonds%2C%20Rg/00918.webp)

## 四、氢键：蛋白-配体的接触还在不在

`gmx hbond`（新版 GROMACS 为 `gmx hbond`）算**两组之间的氢键数随时间的变化**：选择组 **1（Protein）** 和 **13（Lig）**，输出 `hb.xvg`（[【跳转到 17:02】](https://www.youtube.com/watch?v=thxwcKRolM4&t=1022)）。如果对接时预测的关键氢键在整个模拟里**时断时续却始终存在**，这个姿态的相互作用网络就是"活"的；如果氢键数长期归零，配体大概率已经漂走（[【跳转到 18:03】](https://www.youtube.com/watch?v=thxwcKRolM4&t=1083)）。

![gmx hbond：组 1（蛋白）与组 13（配体）](assets/EP%2012%20｜%20Post%20MD%20simulation%20assessment%20of%20Protein%20Ligand%20Complex%20in%20Gromacs%20｜%20RMSD%2C%20RMSF%2C%20H-bonds%2C%20Rg/01022.webp)

![蛋白-配体氢键数随时间变化](assets/EP%2012%20｜%20Post%20MD%20simulation%20assessment%20of%20Protein%20Ligand%20Complex%20in%20Gromacs%20｜%20RMSD%2C%20RMSF%2C%20H-bonds%2C%20Rg/01078.webp)

## 五、Rg：整体紧致度

`gmx gyrate` 算**回旋半径**——分子"摊开"程度的量度：选 Protein（1），输出 `gyrate.xvg`（[【跳转到 18:58】](https://www.youtube.com/watch?v=thxwcKRolM4&t=1138)）。Rg 平稳说明蛋白整体没有明显伸展/坍塌（变性前兆）。小插曲：作者试图给这条命令加 `-tu ns` 时遇到报错（不同版本对该命令的支持有差异），不影响主流程（[【跳转到 20:07】](https://www.youtube.com/watch?v=thxwcKRolM4&t=1207)）。

![gmx gyrate：蛋白的回旋半径](assets/EP%2012%20｜%20Post%20MD%20simulation%20assessment%20of%20Protein%20Ligand%20Complex%20in%20Gromacs%20｜%20RMSD%2C%20RMSF%2C%20H-bonds%2C%20Rg/01138.webp)

## 六、能量项：给模拟做"体检"

`gmx energy -f md.edr` 会列出**几十个能量项**供交互选择：作者先选了蛋白-配体组的**温度项**（列表里编号 48）看平均值（[【跳转到 20:57】](https://www.youtube.com/watch?v=thxwcKRolM4&t=1257)），又试了另一项（编号 50），随后演示 **LJ-SR（短程 Lennard-Jones，编号 9）** 看复合物的短程相互作用能（[【跳转到 22:37】](https://www.youtube.com/watch?v=thxwcKRolM4&t=1357)）。

![gmx energy：交互选择能量项](assets/EP%2012%20｜%20Post%20MD%20simulation%20assessment%20of%20Protein%20Ligand%20Complex%20in%20Gromacs%20｜%20RMSD%2C%20RMSF%2C%20H-bonds%2C%20Rg/01257.webp)

![LJ-SR 项的输出曲线](assets/EP%2012%20｜%20Post%20MD%20simulation%20assessment%20of%20Protein%20Ligand%20Complex%20in%20Gromacs%20｜%20RMSD%2C%20RMSF%2C%20H-bonds%2C%20Rg/01357.webp)

这些曲线多数是一条**平稳直线**——平稳本身就是模拟健康的信号（温度守恒、能量不漂移）。作者建议读者把动能、势能、键能等项逐个"do your own homework"，弄清每一项在告诉你什么（[【跳转到 22:22】](https://www.youtube.com/watch?v=thxwcKRolM4&t=1342)）。

## 小结

- **五个指标、五张图**：RMSD（配体拟蛋白 + 骨架对照）、RMSF（哪里在动）、氢键（接触持续性）、Rg（整体紧致度）、能量项（模拟健康度）——它们共同回答"MD 验证结合稳定性"的定性一半；
- **读数有陷阱**：RMSD 平稳 ≠ 结合正确。结构上"摆得进去"不等于特异性结合（参见 5.3.3 的结构置信度≠结合判别结论）， 所以还需要亲和力的**定量**证据——下一支视频的 MM-GBSA 接棒：[MM-GBSA 结合自由能与逐残基分解](分子动力学模拟%28六%29：mmGBSA结合自由能一行命令计算，能量分解以及一键蛋白质配体复合物模拟.md)。
