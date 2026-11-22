# Protein-Ligand MD Simulation in Gromacs A to Z

> 视频来源：[EP 10 | Protein-Ligand MD Simulation in Gromacs-A to Z | all reusable commands and files provided](https://www.youtube.com/watch?v=EGMoMNttJLc)（约 78 分钟）

## 本讲要解决的核心问题（SCQA）

**背景**：前面剧集里，我们用 UCSF Chimera + AutoDock Vina 把药物利培酮（risperidone）对接进了 D2 多巴胺受体，得到了一个蛋白-配体复合物（`pose1.pdb`）。[【跳转到 00:00】](https://www.youtube.com/watch?v=EGMoMNttJLc&t=0)

**冲突**：对接给的是一个"静止快照"——药物到底在生理环境下结合得稳不稳，得让复合物在水盒子+离子中真实"动"起来看。但 GROMACS 的 MD 流程命令繁多、文件交错，新手很容易在半路迷路。

**疑问**：能不能有一条从对接结果出发、命令可复用的固定流水线，把 MD 模拟从零跑到产出？

**回答（中心思想）**：能。本讲给出一条 **八步流水线**：拆分复合物 → 配体参数化（SwissParam）→ 生成拓扑（pdb2gmx）→ 合并坐标与拓扑 → 装配体系（盒子/水/离子）→ 能量最小化 → NVT/NPT 两段平衡 → production 生产模拟；作者把全部命令与文件放在 GitHub 仓库，只要按约定命名（`rec.pdb`、`li.mol2`），**同一套命令不改一个字就能复用到你自己的体系**。[【跳转到 02:48】](https://www.youtube.com/watch?v=EGMoMNttJLc&t=168)

## 一、开工前的三件事：素材、环境与"可复用命令"约定

### 1.1 素材：分子对接的产物 pose1.pdb

本讲的输入是第一集分子对接得到的复合物文件 `pose1.pdb`：D2 多巴胺受体 + 利培酮，配体在 Chimera 里以绿色高亮显示。[【跳转到 02:34】](https://www.youtube.com/watch?v=EGMoMNttJLc&t=154)

![Chimera 中打开的蛋白-配体复合物](assets/Protein-Ligand%20MD%20Simulation%20in%20Gromacs%20A%20to%20Z/00000.webp)

### 1.2 环境：安装与 source

体系搭建依赖的工具（GROMACS 源码编译版、VMD 等）在 EP8/EP9 已装好。注意：**源码编译的 GROMACS 不会自动进 PATH**，直接敲 `gmx` 会提示 command not found；需要先执行仓库提供的 `source` 脚本激活环境（若是"dirty install"直装版则可跳过），之后 `gmx` 的所有命令才可用。[【跳转到 26:34】](https://www.youtube.com/watch?v=EGMoMNttJLc&t=1594)

![source 激活 GROMACS 环境后 gmx 可用](assets/Protein-Ligand%20MD%20Simulation%20in%20Gromacs%20A%20to%20Z/01594.webp)

### 1.3 "可复用命令"的约定

作者把全部命令整理在工作目录的 `gromacs codes` 文件里，按流程列好了每一步的命令与说明。[【跳转到 06:15】](https://www.youtube.com/watch?v=EGMoMNttJLc&t=375)

![gromacs codes 文件中列出的流程步骤](assets/Protein-Ligand%20MD%20Simulation%20in%20Gromacs%20A%20to%20Z/00375.webp)

可复用的关键在**命名约定**：配体一律存成 `li.mol2`、受体一律存成 `rec.pdb`（大写）。只要名字一致，教程里的每条命令都能原样跑通你自己的蛋白-配体体系。[【跳转到 02:48】](https://www.youtube.com/watch?v=EGMoMNttJLc&t=168)

## 二、第一步：在 Chimera 里把复合物拆成配体与受体

拓扑要分开建：蛋白（受体）与配体的拓扑必须**分别生成**，所以先在 UCSF Chimera 里把 `pose1.pdb` 拆成两个文件。[【跳转到 06:41】](https://www.youtube.com/watch?v=EGMoMNttJLc&t=401)

### 2.1 配体：删蛋白链 → 加氢 → 存成 li.mol2

在 Chimera 中打开 `pose1.pdb`，用 Select 选中**蛋白链**，走 `Actions → Atoms/Bonds → delete` 删掉，屏幕上只剩下配体。[【跳转到 08:20】](https://www.youtube.com/watch?v=EGMoMNttJLc&t=500)

![Chimera 中选中并删除蛋白链，只留配体](assets/Protein-Ligand%20MD%20Simulation%20in%20Gromacs%20A%20to%20Z/00500.webp)

接着给配体补氢：`Tools → Structure Editing → Add Hydrogen`（参数默认即可）。保存时走 `File → Save MOL2`，**务必勾选 MOL2 格式**，文件名用大写的 `li`，存进工作目录。[【跳转到 09:00】](https://www.youtube.com/watch?v=EGMoMNttJLc&t=540)

### 2.2 受体：删配体链 → Dock Prep → 存成 rec.pdb

再开一次 `pose1.pdb`，这次选中**配体链**删掉，只留蛋白。然后走 `Tools → Surface/Binding Analysis → Dock Prep`：[【跳转到 12:12】](https://www.youtube.com/watch?v=EGMoMNttJLc&t=732)

- 第一次先**取消勾选**"incomplete side chains / replace using Dunbrack rotamer library"与"write Mol2 file"两项，其余默认；
- 弹窗里同意 **add hydrogens**（加氢）、**assign charges** 选 **Gasteiger** 电荷方法、净电荷（net charge）保持 **0**；
- 完成后 `File → Save PDB`，文件名大写 `rec`，存进工作目录。

![Dock Prep 对话框的选项设置](assets/Protein-Ligand%20MD%20Simulation%20in%20Gromacs%20A%20to%20Z/00748.webp)

### 2.3 报错预案：组氨酸环不完整

后续 `pdb2gmx` 若报"incomplete ring"（组氨酸残基环不完整）一类错误，处理办法是**回到 Chimera 重做一遍受体**：这次把 Dock Prep 里 Dunbrack rotamer library 那一项**勾上**（程序会花几分钟从 Dunbrack 库检索侧链构象），其余步骤照旧，重新保存 `rec.pdb` 再跑。[【跳转到 28:39】](https://www.youtube.com/watch?v=EGMoMNttJLc&t=1719)

## 三、第二步：给配体补力场参数——SwissParam

蛋白的力场参数 pdb2gmx 自己能生成，但**小分子配体不在蛋白力场里**，需要在线服务补参数。把 `li.mol2` 上传到 SwissParam 网站，服务器返回一个 `li.zip`；解压到工作目录（遇到重名选"不替换"，保留我们自己的原始文件）。解压出的 7 个文件（`lig.itp`、`lig.top`、`lig.pdb` 等）就是 GROMACS 跑配体所需的拓扑与参数文件。[【跳转到 22:14】](https://www.youtube.com/watch?v=EGMoMNttJLc&t=1334)

![从 SwissParam 下载的配体参数包](assets/Protein-Ligand%20MD%20Simulation%20in%20Gromacs%20A%20to%20Z/01334.webp)

此时工作目录里应齐备：GitHub 下载的各阶段 `.mdp` 文件、`rec.pdb`、配体参数文件。[【跳转到 25:00】](https://www.youtube.com/watch?v=EGMoMNttJLc&t=1500)

## 四、第三步：生成蛋白拓扑与配体坐标（pdb2gmx）

### 4.1 蛋白：pdb2gmx 选 CHARMM27 + 水模型

```bash
gmx pdb2gmx -f rec.pdb -o ... -ignh
```

运行后程序让你**选力场**：输入 **8** = CHARMM27 全原子力场（适合蛋白）；再**选水模型**：输入 **1**（推荐项，即 TIP3P 水）。[【跳转到 27:24】](https://www.youtube.com/watch?v=EGMoMNttJLc&t=1644)

![pdb2gmx 交互选择力场与水模型](assets/Protein-Ligand%20MD%20Simulation%20in%20Gromacs%20A%20to%20Z/01644.webp)

成功后生成蛋白拓扑 `topol.top`；同名带 `##` 前后缀的文件可以忽略或删除。[【跳转到 31:39】](https://www.youtube.com/watch?v=EGMoMNttJLc&t=1899)

### 4.2 配体：li.pdb → lig.gro

配体侧用类似命令把 SwissParam 给的 `li.pdb` 转成 `lig.gro`（`-f` 是输入文件、`-o` 是输出文件——这是 GROMACS 命令的通用惯例）。[【跳转到 33:33】](https://www.youtube.com/watch?v=EGMoMNttJLc&t=2013)

### 4.3 怎么判断命令跑成功了

GROMACS 每条命令结束都会**随机打印一句引言彩蛋**（比如"I have a bad case of a purple diarrhea"）——看到引言就代表命令成功执行；若命令半途报错退出则不会有引言。[【跳转到 34:23】](https://www.youtube.com/watch?v=EGMoMNttJLc&t=2063)

## 五、第四步：合并坐标与拓扑

### 5.1 conf.gro + lig.gro：手工合并

蛋白拓扑（坐标文件 `conf.gro`）与配体坐标 `lig.gro` 现在是分开的，要**手工合并**。用 `gedit conf.gro lig.gro` 同时打开两个文件：在 `lig.gro` 里**从第 3 行选中到倒数第 2 行**（跳过标题行、原子数行和最后一行盒子信息），复制；切到 `conf.gro`，在**最后一行（盒子行）之前**新建一空行粘贴。[【跳转到 38:27】](https://www.youtube.com/watch?v=EGMoMNttJLc&t=2307)

![把 lig.gro 内容粘贴进 conf.gro](assets/Protein-Ligand%20MD%20Simulation%20in%20Gromacs%20A%20to%20Z/02307.webp)

### 5.2 原子数 = 总行数 − 3

合并后 `conf.gro` 的第 2 行是**原子总数**，必须手动更新：数一下文件总行数（本例 6931 行），**减去 3**（首两行 + 末行不是原子记录），把差值（6928）写进第 2 行。[【跳转到 39:17】](https://www.youtube.com/watch?v=EGMoMNttJLc&t=2357)

### 5.3 topol.top 两处修改

打开 `topol.top`：

1. 在 `; Include forcefield parameters` 注释下方**追加两行 include**（引入配体拓扑 `lig.itp` 等参数文件）；[【跳转到 44:11】](https://www.youtube.com/watch?v=EGMoMNttJLc&t=2651)
2. 在文件**末尾**、`protein_chain_A` 那一行的正下方**对齐追加** `LIG 1`（把 1 个 LIG 分子加进体系清单）。

![topol.top 中追加 include 与 LIG 1](assets/Protein-Ligand%20MD%20Simulation%20in%20Gromacs%20A%20to%20Z/02651.webp)

### 5.4 检查 lig.itp 的 moleculetype

打开 `lig.itp`，确认 moleculetype 段是 `LIG`、`nrexcl` 为 3——用 Chimera/SwissParam 流程生成时**通常已经正确**，只需检查、一般无需修改。[【跳转到 46:11】](https://www.youtube.com/watch?v=EGMoMNttJLc&t=2771)

### 5.5 用 Chimera 打开 conf.gro 自检

合并是否成功有个"聪明的验法"：直接用 Chimera 打开 `conf.gro`——能正常打开并看到蛋白 + 配体（选中 LIG 残基标红）就说明前面全部做对了；打不开则回头检查合并步骤。[【跳转到 41:32】](https://www.youtube.com/watch?v=EGMoMNttJLc&t=2492)

## 六、第五步：装配模拟体系——盒子、溶剂、离子

最难的部分到此为止，接下来基本是"复制-粘贴"命令。[【跳转到 47:32】](https://www.youtube.com/watch?v=EGMoMNttJLc&t=2852)

### 6.1 editconf：给复合物套上盒子

用 `editconf` 围绕蛋白-配体复合物生成周期性盒子，输出 `box.gro`（看到 GROMACS 引言即成功）。[【跳转到 47:57】](https://www.youtube.com/watch?v=EGMoMNttJLc&t=2877)

### 6.2 solvate：用水填满盒子

`solvate` 把盒子里的空隙填满水分子，输出 `box_sol.gro`。想亲眼看看体系长什么样，可以用 VMD 打开它：中间是蛋白-配体复合物，四周是填满的水分子。[【跳转到 48:34】](https://www.youtube.com/watch?v=EGMoMNttJLc&t=2914)

![VMD 中查看加完水的模拟盒子](assets/Protein-Ligand%20MD%20Simulation%20in%20Gromacs%20A%20to%20Z/02939.webp)

### 6.3 加离子：ions.mdp → genion

先 `grompp` 配合 `ions.mdp`（该文件来自 GitHub 仓库）生成 `ions.tpr`；再用 `genion` 往体系里加离子。程序会让你**选一个组**：本例 SOL 在第 15 位就输 15；如果你的体系里 SOL 排在别的序号，就输对应序号——**认准组名，别死记数字**。执行后程序向体系加入了 Cl⁻（氯离子）以中和体系净电荷。[【跳转到 51:11】](https://www.youtube.com/watch?v=EGMoMNttJLc&t=3071)

![genion 选择 SOL 组加离子](assets/Protein-Ligand%20MD%20Simulation%20in%20Gromacs%20A%20to%20Z/03130.webp)

> 关于 `-maxwarn 1`：命令若因警告报错，可加 `-maxwarn 1` 重试；但优先先跑不带它的原始命令，两者等价时以原始命令为准。[【跳转到 50:44】](https://www.youtube.com/watch?v=EGMoMNttJLc&t=3044)

## 七、第六步：能量最小化（EM）

正式"跑"的第一步是**能量最小化**：`grompp` 配合 `em.mdp` 生成 `em.tpr`，然后 `mdrun` 执行，大约一两分钟跑完。它把加氢、加离子后体系里的局部空间冲突"推"到低能量状态，消除不合理接触，为动力学模拟铺路。[【跳转到 53:07】](https://www.youtube.com/watch?v=EGMoMNttJLc&t=3187)

![能量最小化完成，输出能量汇总](assets/Protein-Ligand%20MD%20Simulation%20in%20Gromacs%20A%20to%20Z/03285.webp)

EM 之后还按教程要求生成了索引文件：先用 `lig.gro` 做 `make_ndx` 得到配体索引（`index_lig.ndx`），选中配体组；后续再做一次面向整个体系的 `make_ndx`（输入 `em.gro`，输出 `index.ndx`），把 1（Protein）和 13（LIG）两组合在一起生成 Protein_LIG 复合物组。[【跳转到 55:00】](https://www.youtube.com/watch?v=EGMoMNttJLc&t=3300)

同时按教程在 `topol.top` 的 `; Include Position restraint file` 注释下方**追加位置限制（position restraints）的 include 段**，注意各行对齐，保存。[【跳转到 57:56】](https://www.youtube.com/watch?v=EGMoMNttJLc&t=3476)

## 八、第七步：两段平衡——NVT 与 NPT

平衡（equilibration）是正式生产模拟前的"热身"，分 NVT、NPT 两段，各 100 ps。这一步是全流程最关键的节点。[【跳转到 61:01】](https://www.youtube.com/watch?v=EGMoMNttJLc&t=3661)

### 8.1 NVT：nvt.mdp（100 ps）

`nvt.mdp` 同样来自 GitHub 仓库，默认平衡 100 ps（100 皮秒）。[【跳转到 61:01】](https://www.youtube.com/watch?v=EGMoMNttJLc&t=3661)

![nvt.mdp 的平衡时长设置](assets/Protein-Ligand%20MD%20Simulation%20in%20Gromacs%20A%20to%20Z/03661.webp)

**时长怎么改**：模拟总时长 = 步数 × 步长（dt，默认 0.002 ps = 2 fs）。仓库默认 500,000 步对应 1000 ps（即 1 ns）；想要 100 ps，就把**三处**相关数字各去掉一个零——`nsteps`、对应的时间注释（ps）与另一处同步字段。改时长必须三处联动，漏一处就会报错。[【跳转到 62:44】](https://www.youtube.com/watch?v=EGMoMNttJLc&t=3764)

然后 `grompp -f nvt.mdp …` 生成 `nvt.tpr`（先尝试不加 `-maxwarn 1`），再 `gmx mdrun` 跑这 100 ps 的 NVT 平衡。跑完终端再次出现引言，还会给出性能统计。[【跳转到 63:34】](https://www.youtube.com/watch?v=EGMoMNttJLc&t=3814)

### 8.2 性能参考：43 ns/day

作者的机器（NVIDIA RTX 2050 显卡）对这个相对较大的蛋白-配体体系跑出 **43 ns/day**——即一天能模拟 43 纳秒的物理时间；蛋白更小（小 30%~40%）可到 100 ns/day 左右。这个数字可以用来估算自己的模拟要跑多久。[【跳转到 65:39】](https://www.youtube.com/watch?v=EGMoMNttJLc&t=3939)

### 8.3 NPT：npt.mdp（同样 100 ps）

NVT 完成后跑 NPT：`npt.mdp` 同样是 100 ps，命令流程与 NVT 相同（`grompp` → `mdrun`）。运行开始时终端若显示 **"one GPU selected for this run"**，说明体系成功用上了 GPU 加速——这是个好迹象。[【跳转到 66:04】](https://www.youtube.com/watch?v=EGMoMNttJLc&t=3964)

## 九、第八步：production MD（md.mdp）

平衡完成后进入正戏——**生产模拟（production run）**。[【跳转到 68:00】](https://www.youtube.com/watch?v=EGMoMNttJLc&t=4080)

### 9.1 时长怎么定

打开 `md.mdp`（仓库默认 10 ns），按需修改时长：本教程演示改跑 2 ns。规则与前面一致——去掉一个零变 1 ns（500,000 步）；把 500,000 翻倍成 1,000,000（把 5 换成 10）就是 2 ns（2000 ps）。[【跳转到 68:09】](https://www.youtube.com/watch?v=EGMoMNttJLc&t=4089)

![md.mdp 中设置生产模拟时长](assets/Protein-Ligand%20MD%20Simulation%20in%20Gromacs%20A%20to%20Z/04089.webp)

**科研建议**：若要发表数据，小体系至少跑 **25 ns**；蛋白较大则建议 50~100 ns。教程里只跑 2 ns 演示流程。[【跳转到 69:11】](https://www.youtube.com/watch?v=EGMoMNttJLc&t=4151)

### 9.2 接续 NPT 的状态起跑

生产模拟的 `grompp` **会把上一段 NPT 平衡的输出当作输入**（从平衡末态出发），生成 `md.tpr`；随后 `mdrun` 正式开跑。跑完这最后一条命令，MD 模拟就大功告成——本例 2 ns 在 42 ns/day 的速度下约需 2 小时。[【跳转到 71:59】](https://www.youtube.com/watch?v=EGMoMNttJLc&t=4319)

## 十、产出：md.tpr / md.xtc 等输出文件

跑完后工作目录里会出现一组 `md.*` 文件，对照"输入→输出"看最清楚：[【跳转到 75:19】](https://www.youtube.com/watch?v=EGMoMNttJLc&t=4519)

- `grompp`：输入 `md.mdp` → 输出 **`md.tpr`**（二进制运行输入）；
- `mdrun`：输出 `md.cpt`（检查点）、`md.edr`（能量）、`md.gro`（末态坐标）、`md.log`（日志）、`md.tpr`、**`md.xtc`**（轨迹）。

其中 **`md.tpr` 与 `md.xtc` 是生产模拟的核心输出**——轨迹文件就是后续一切分析（画 RMSD 图、做模拟动画等）的原材料。[【跳转到 75:49】](https://www.youtube.com/watch?v=EGMoMNttJLc&t=4549)

![生产模拟的输入输出命令一览](assets/Protein-Ligand%20MD%20Simulation%20in%20Gromacs%20A%20to%20Z/04519.webp)

至此"从 A 到 Z"的模拟本体完成；下一集（EP11 起）讲解如何可视化轨迹、用结果做图做视频（post-simulation 评估）。[【跳转到 76:14】](https://www.youtube.com/watch?v=EGMoMNttJLc&t=4574)

## 小结

- 流水线共八步：**拆分（Chimera）→ 配体参数化（SwissParam）→ 拓扑（pdb2gmx：CHARMM27+水模型）→ 合并（conf.gro+lig.gro、原子数=行数−3、topol.top 加 include 与 LIG 1）→ 装配（editconf/solvate/genion）→ 能量最小化（em）→ 平衡（NVT 100 ps → NPT 100 ps）→ 生产（md.mdp 自定时长）**。
- 可复用约定：配体 `li.mol2`、受体 `rec.pdb`（大写），命令不改字直接跑自己的体系。
- 两个救命细节：`pdb2gmx` 报 incomplete ring → 回 Chimera 勾选 Dunbrack rotamer library 重做受体；GROMACS 结束打印引言彩蛋 = 命令成功的标志。
- 时长换算口诀：总时长 = `nsteps` × dt（0.002 ps）；改时长要三处联动，production 接续 NPT 末态起跑。
- 性能量级参考：RTX 2050 上该体系 42~43 ns/day，小体系可达 100 ns/day；发表级模拟至少 25 ns。
- 核心产出：`md.tpr`（运行输入）与 `md.xtc`（轨迹）——后续分析的原材料。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| MOL2 / `.mol2` | 配体保存格式，SwissParam 上传的输入 |
| Dock Prep | Chimera 的受体准备工具：加氢 + Gasteiger 电荷 + 净电荷设定 |
| SwissParam | 在线小分子参数服务：把 MOL2 转成 GROMACS 配体拓扑/参数文件 |
| `pdb2gmx` | 由 PDB 生成蛋白拓扑的命令；交互选择力场与水模型 |
| `-f` / `-o` | GROMACS 命令通用惯例：输入文件 / 输出文件 |
| `.gro` | 坐标文件（如 conf.gro、lig.gro、box_sol.gro） |
| `topol.top` | 体系总拓扑：分子清单 + include 的各组件参数 |
| `grompp` | 预处理器：把 `.mdp` + 拓扑 + 坐标编译成 `.tpr` 运行输入 |
| `genion` | 加离子命令；按**组名**（如 SOL）选替换对象 |
| NVT / NPT | 平衡两阶段：先固定粒子数/体积/温度，再放开体积控压 |
| production run | 生产模拟：平衡后的正式采样，时长按科研需要设定 |
| `md.xtc` | 轨迹文件，生产模拟的核心产出与后续分析的原材料 |
| ns/day | 模拟速度：每天能模拟的物理时间纳秒数 |
