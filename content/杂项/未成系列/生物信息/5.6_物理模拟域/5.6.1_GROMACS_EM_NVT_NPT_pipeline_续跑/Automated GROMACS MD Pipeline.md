# Automated GROMACS MD Pipeline

> 视频来源：[Automated GROMACS MD Pipeline | Native Protein & Protein–Ligand Simulations and Analysis](https://www.youtube.com/watch?v=29rOMV1XUZQ)（约 96 分钟，工作坊实录）

## 本讲要解决的核心问题（SCQA）

**背景**：手工跑 GROMACS 分子动力学，就是把几十条命令按顺序复制粘贴——上一集那条"从 A 到 Z"的流水线已经证明了它可行。

**冲突**：但手工流程有三大痛点：命令繁多、一步错全盘乱；配体参数化、拓扑合并这些环节最容易卡住；更难受的是模拟一跑就是几十分钟到几天，**你只能盲等**，不知道还要多久。

**疑问**：能不能把这些固定步骤写进一个脚本，让"检查环境 → 下载结构 → 拆分配体/受体 → 参数化 → 建体系 → EM → NVT/NPT → 生产模拟 → 出分析报告"全程自动化，而且中途出错还能从断点接着跑？

**回答（中心思想）**：能。本讲是作者自研 **Automated GROMACS MD Pipeline** 的实测工作坊（1.81 GB 的打包环境，跑在 WSL 或虚拟机里）：整个 MD 流程被压成"回车-回车-回车"，全流程只剩 **CGenFF 参数化一个手工环节**；内置环境自检、PDB 自动下载与修复、**断点续跑（resume）**、**步数下限保护**、**ETA 预计剩余时间**与**批量排队**。[【跳转到 04:46】](https://www.youtube.com/watch?v=29rOMV1XUZQ&t=286)

## 一、启动与环境自检

### 1.1 拿到并运行 pipeline

打包好的 pipeline 压缩包约 1.81 GB，解压后既可以放进虚拟机，也可以直接在 WSL 里用。进入文件夹，核心入口是 `run_pipeline.sh`：先 `chmod +x run_pipeline.sh` 赋予执行权限，再运行它。[【跳转到 06:13】](https://www.youtube.com/watch?v=29rOMV1XUZQ&t=373)

![pipeline 文件夹：readme、assets、scripts、run_pipeline.sh](assets/Automated%20GROMACS%20MD%20Pipeline/00373.webp)

### 1.2 启动即体检

启动后 pipeline 先要一个**运行名**（同时作为工作目录名，本例 `native`），然后自动做一轮环境体检：检查 GROMACS 是否安装及版本、当前系统信息、自动创建虚拟环境，并检查 Python 3、Perl、Unzip 等依赖——缺什么会**主动询问是否帮你安装**（演示中作者已装好，选了 no 省时间）。[【跳转到 08:23】](https://www.youtube.com/watch?v=29rOMV1XUZQ&t=503)

![启动自检：GROMACS 版本、虚拟环境与依赖检查](assets/Automated%20GROMACS%20MD%20Pipeline/00503.webp)

体检还包括硬件面：CPU 核数、CPU 温度（演示时 63 °C）、CUDA 是否可用、apt/brew/pip 等包管理器在不在——这些都决定了后续模拟的跑法。[【跳转到 09:38】](https://www.youtube.com/watch?v=29rOMV1XUZQ&t=578)

## 二、两条工作流与输入处理

### 2.1 选工作流：native 还是 complex

pipeline 提供两条工作流：**仅天然蛋白（native protein）** 与 **蛋白-配体复合物（protein-ligand complex）**。工作坊先演示复合物流线：输入 PDB 代码 `3HTB`，pipeline 发现本地没有该文件就**自动从 PDB 数据库下载**。[【跳转到 10:53】](https://www.youtube.com/watch?v=29rOMV1XUZQ&t=653)

![输入 3HTB，PDB 自动下载](assets/Automated%20GROMACS%20MD%20Pipeline/00653.webp)

### 2.2 结构完整性检查与自动修复

下载后自动检查 PDB 完整性："PDB structure is passed. No missing residues, no atoms"。如果检出缺失氨基酸，pipeline 会提示运行 **PDB-Fixer** 脚本自动修复结构——这是手工流程里新手最容易栽跟头的预处理。[【跳转到 11:18】](https://www.youtube.com/watch?v=29rOMV1XUZQ&t=678)

### 2.3 异原子基团与配体选择

接着分析文件里挂着的异原子基团（本例检出 β-巯基乙醇、JZ4 配体与磷酸基团），问你要保留哪些（本例全部不保留）；再让你从候选里**选定配体**（选 2 号 JZ4）。随后 `ligand.pdb` 与 `receptor.pdb` **自动拆分生成**——上一集里在 Chimera 手工"删链-加氢-另存"的那一套，这里一步到位。[【跳转到 12:33】](https://www.youtube.com/watch?v=29rOMV1XUZQ&t=753)

![自动拆分生成 ligand.pdb 与 receptor.pdb](assets/Automated%20GROMACS%20MD%20Pipeline/00753.webp)

## 三、拓扑自动化

### 3.1 力场、水模型与末端

拆分完成后依次选择：**力场**（2022 年 7 月版或 2026 版）、**水模型**（TIP3P / TIP4P / SPC，选 1 即 TIP3P）、**蛋白末端**（N 端 NH3⁺ 选 1、C 端 COO⁻ 选 0）。选完自动从 `receptor.pdb` 生成拓扑——`receptor.gro` 与 `topol.top` 直接出现在工作目录（作者把输出开了 verbose，过程全可见）。[【跳转到 13:23】](https://www.youtube.com/watch?v=29rOMV1XUZQ&t=803)

### 3.2 配体侧的自动处理

配体侧同样自动化：`ligand.pdb` 自动转成 MOL2（选 automatic，不用手工开 OpenBabel）；随后"sort bonds"环节用 **Perl 脚本**自动生成修正过的 `ligand_fix` MOL2 文件——这对应手工流程里最琐碎的文件改名与格式修正。[【跳转到 15:03】](https://www.youtube.com/watch?v=29rOMV1XUZQ&t=903)

## 四、唯一的人工步骤：CGenFF 参数化

### 4.1 流程

全流程唯一需要动手的环节：打开 **CGenFF 服务器**（作者临时分享了实习用账号），把 `ligand_fix_cgen.mol2` 拖进去，核对结构与氢原子无误后，依次 **Process Input → Run CGenFF Engine → Include Parameters → 下载结果**（zip 包 + GROMACS 格式结果各一份）。[【跳转到 15:53】](https://www.youtube.com/watch?v=29rOMV1XUZQ&t=953)

![CGenFF 服务器：拖入配体文件](assets/Automated%20GROMACS%20MD%20Pipeline/00953.webp)

### 4.2 按名放回与自动转换

把下载的两个文件**按 pipeline 要求的名字**（`ligand_fix_cgen.zip` 与 `ligand_fix_cgen_gromacs`）放进工作目录——多次下载会导致文件名带后缀，要先改名。pipeline 确认文件齐备后自动完成转换：**自动删掉力场段、内联参数、删水拓扑、改 moleculetype 名**，直接产出配体拓扑 `ligand_gmx.itp`。作者强调：教程里"非常复杂的一串步骤"，在这里被合并成了**一次回车**。[【跳转到 26:47】](https://www.youtube.com/watch?v=29rOMV1XUZQ&t=1607)

![自动生成 ligand_gmx.itp](assets/Automated%20GROMACS%20MD%20Pipeline/01607.webp)

### 4.3 缺文件怎么办：可从断点恢复

如果两个 zip 没放对，pipeline 会**终止**，但不会作废——它会明确告诉你"可以从这一步 **resume**"，重跑 `run_pipeline.sh` 时选择从上次的未完成步骤继续即可。工作坊里作者还现场演示了因为 CGenFF 的 GROMACS 结果没进 zip、手工把文件夹压缩成 zip 再续跑的过程。[【跳转到 19:12】](https://www.youtube.com/watch?v=29rOMV1XUZQ&t=1152)

## 五、复合物构建与位姿检查

### 5.1 专属 Python 环境的要求

复合物构建依赖 **networkx**，而它对 Python 版本挑剔：**必须 Python 3.7**（作者机器上是 3.17 系的版本就不行）。为此 pipeline 提供了 conda 环境文件，`conda create` 建 `simulation` 环境、`conda activate simulation` 后再装 numpy 与 networkx。作者现场踩了这个坑：一直在 base 环境里跑导致 networkx 缺失报错，激活正确环境后恢复。[【跳转到 31:12】](https://www.youtube.com/watch?v=29rOMV1XUZQ&t=1872)

### 5.2 PyMOL 位姿检查：防"配体漂走"

构建完成后 pipeline 自动生成一个 `inspect.pyMol` 文件，用 PyMOL 打开就能**目视检查配体是否真的结合在结合位点**。作者点出这是 MD 新手最常见的翻车点之一：复合物制备时坐标没弄好，模拟一开跑配体就"漂"出口袋——先检查，再开跑。[【跳转到 32:33】](https://www.youtube.com/watch?v=29rOMV1XUZQ&t=1953)

![PyMOL 检查配体结合位姿](assets/Automated%20GROMACS%20MD%20Pipeline/01953.webp)

### 5.3 通用性

pipeline 不挑体系：不必是 JZ4 或 3HTB，**自己的对接结果文件拷进同一文件夹直接跑**就行——拓扑、复杂度各异的蛋白都能走完同一条流水线。[【跳转到 35:00】](https://www.youtube.com/watch?v=29rOMV1XUZQ&t=2100)

## 六、装配与能量最小化

### 6.1 盒子：四种形状任选

溶剂化环节 pipeline 给出四个盒子选项：**cubic（立方，默认）**、triclinic（三斜）、octahedron（八面体）、dodecahedron（十二面体）；再设**最小距离**——默认 1.2 nm，蛋白如果"胳膊"伸得长（柔性大）建议 2 nm；主轴对齐等选项不懂就回车取默认。盒子生成后同样用 PyMOL 打开检查：蛋白与配体稳稳位于水盒中央。[【跳转到 35:50】](https://www.youtube.com/watch?v=29rOMV1XUZQ&t=2150)

![盒子形状与最小距离选项](assets/Automated%20GROMACS%20MD%20Pipeline/02150.webp)

![PyMOL 中查看装好水的盒子](assets/Automated%20GROMACS%20MD%20Pipeline/02213.webp)

### 6.2 加离子：全自动

`ions.mdp` 由 pipeline 自动拷贝进工作目录；步数默认 3000（可改）；静电模型默认 **PME**（也可选 cut-off）；随后**组自动选择**——不需要你手动挑 SOL 组，执行完直接显示"6 个 Cl⁻ 已自动加入"以及加到了哪里，全部细节可视化呈现。[【跳转到 37:47】](https://www.youtube.com/watch?v=29rOMV1XUZQ&t=2267)

### 6.3 能量最小化：收敛即过

EM 同样自动：步数默认 20,000（保留或修改随你），以 CPU 多线程启动，同时生成 log 文件记录势能变化；跑完报告"EM converged successfully"，看到它才放行下一步。[【跳转到 38:51】](https://www.youtube.com/watch?v=29rOMV1XUZQ&t=2331)

![能量最小化步数设置与多线程启动](assets/Automated%20GROMACS%20MD%20Pipeline/02331.webp)

### 6.4 位置限制与索引：组自动合并

EM 之后的组选择是"非常 tricky"的一步——pipeline 自动把蛋白、配体、水、离子分组合并并生成 `index.ndx`，配体的位置限制文件也自动生成，免去手工 make_ndx 逐组点选。[【跳转到 40:06】](https://www.youtube.com/watch?v=29rOMV1XUZQ&t=2406)

## 七、平衡与生产模拟：步数下限与 ETA

### 7.1 NVT/NPT：步数有"安全下限"

NVT 阶段 pipeline 会报三个数：**当前检测值 2000、推荐值 50,000、允许范围 25,000–50,000**。作者想输入 20,000 步被直接拒绝——他给脚本加了**强制下限 25,000 步**（约 50 ps），因为步数太少的平衡会给出不可信的结果。NPT 阶段同理。这是 pipeline 相比手工流程的一个隐性"防呆"设计。[【跳转到 41:05】](https://www.youtube.com/watch?v=29rOMV1XUZQ&t=2465)

![NVT 步数：检测值/推荐值/允许范围](assets/Automated%20GROMACS%20MD%20Pipeline/02465.webp)

### 7.2 ETA：告别盲等

pipeline 内置了进度与**预计剩余时间（ETA）**：模拟开跑 1–2% 后即给出总时长预估。作者对比：以前跟着教程跑，只能盯着屏幕"盲目等待"，不知道还要多久；现在每一步都清楚显示"已跑多少、还剩多少"。NPT 演示跑 3,000 步（约 6 ps）不到一分钟；若 matplotlib 未安装，图会自动降级为 CSV 导出（Excel、GraphPad Prism 都能打开重绘）。[【跳转到 42:20】](https://www.youtube.com/watch?v=29rOMV1XUZQ&t=2540)

![模拟启动后自动给出 ETA](assets/Automated%20GROMACS%20MD%20Pipeline/02540.webp)

### 7.3 生产模拟：最低 25,000 步

MD 生产模拟同样有下限：推荐 50,000 步、**强制至少 25,000 步**（作者试 5,000 被拒）。`md.mdp` 自动创建；被问及 barostat（恒压器）等参数时，**不懂就回车走默认值**——作者在脚本里预置了合理的定制参数。模拟总时长取决于蛋白与水分子的原子数（体系大小）与计算机算力。[【跳转到 57:06】](https://www.youtube.com/watch?v=29rOMV1XUZQ&t=3426)

### 7.4 断点续跑与结果复用

pipeline 的 resume 能力贯穿全程：重跑 `run_pipeline.sh` 时可以**从指定步骤继续**（工作坊演示了直接跳到第 16 步做后分析），也可以**复用既有结果**——NVT/NPT/MD 各步都会问"用已有结果继续，还是重跑"，选 continue 就跳过重算，直接进入下一环节。[【跳转到 60:35】](https://www.youtube.com/watch?v=29rOMV1XUZQ&t=3635)

## 八、README 与工程化细节

作者为 pipeline 写了详尽的 README，覆盖：[【跳转到 68:09】](https://www.youtube.com/watch?v=29rOMV1XUZQ&t=4089)

- **最低系统要求：4 核 CPU、8 GB 内存、50 GB 磁盘**（模拟数据量不小——一次 NVT 演示就产生 6~8 MB，生产模拟数十 MB 起）；
- 自动安装 GROMACS、OpenBabel，检查 Python，依赖含 PDB-Fixer；
- **常见问题排查表**：`GMX not found`（GROMACS 未安装/未 source）、`PDB not found`（代码拼写错误）、index 文件缺失、配体未正确处理、缺残基结构 → autofix；
- **WSL2 专属坑**：内存分配不足、绘图需要图形支持；
- 进阶用法：第 4 步可手动更换力场；**批量处理**——把多个 PDB ID 写进列表，周末挂着让机器自动连跑 4~5 个体系的模拟。

![README 中的最低系统要求](assets/Automated%20GROMACS%20MD%20Pipeline/04129.webp)

![批量处理：多个 PDB ID 排队自动跑](assets/Automated%20GROMACS%20MD%20Pipeline/04279.webp)

pipeline 已在 **Mac、Ubuntu、Windows WSL2**（2024/2025 版）上实测通过；面向蛋白体系优化（DNA 需自行更换力场）；在 GPU 工作站上验证可正常加速。[【跳转到 71:44】](https://www.youtube.com/watch?v=29rOMV1XUZQ&t=4304)

## 九、分析产出自动化

### 9.1 native 蛋白全流程演示

工作坊后半段用 `1AKI` 走了一遍 native 蛋白流程：检出无异原子、无水 → 自动生成 receptor → 力场/水模型/末端各选一次 → 盒子、溶剂、离子、EM（曲线图自动导出）→ NVT（26 秒完成 50%）→ NPT（3,000 步约 50 秒，进度实时显示 16.7%）→ MD 生产模拟（最低 25,000 步）。[【跳转到 77:25】](https://www.youtube.com/watch?v=29rOMV1XUZQ&t=4645)

### 9.2 一份 HTML 报告装下所有分析

生产模拟结束后进入 post-MD 分析：RMSD（骨架）、RMSF（逐残基）、回旋半径、二级结构变化（DSSP）、氢键（蛋白-水、氨基酸间、侧链间、**蛋白-配体间**）、**蛋白-配体最小距离（nm）**、**接触计数**、**关键氨基酸占据分析**与**接触热图**（哪些氨基酸与配体保持接触、保持多久）——以前要在教程里学会选组、认配体原子名才能画出来的图，pipeline **泛化处理**：不必告诉它配体叫 JZ4，自动识别自动选组。全部结果汇成一份 **HTML 分析报告**，图片可直接复制引用，同时附高分辨率图像与 Excel/CSV 原始数据供重绘。[【跳转到 85:45】](https://www.youtube.com/watch?v=29rOMV1XUZQ&t=5145)

![HTML 分析报告：能量、平衡与结构指标全集](assets/Automated%20GROMACS%20MD%20Pipeline/05145.webp)

### 9.3 进阶选项的门槛

- **PCA**（主成分分析）需要至少 **20~50 ns** 的轨迹数据，50 ps 的演示轨迹跑 PCA"is rubbish"（毫无意义）；
- **XTC → movie**：pipeline 支持把轨迹文件自动转成演示用动画；
- **MM/GBSA、MM/PBSA、umbrella sampling** 等结合自由能分析是可选项，但作者建议**先从 native 模拟打基础，再到配体体系，最后才碰自由能方法**。

## 小结

- pipeline 把"从 PDB 代码到分析报告"的完整 MD 流程压缩为交互式问答：**环境自检 → 自动下载/修复 PDB → 自动拆分配体/受体 → 自动拓扑（力场/水模型/末端）→ 自动配体参数化前处理 → 唯一人工步骤 CGenFF → 自动复合物构建与位姿检查 → 自动盒子/溶剂/离子 → EM → NVT/NPT → production → HTML 分析报告**。
- 三大工程化保障：**断点续跑**（指定步骤恢复、复用既有结果）、**步数下限**（平衡/生产模拟强制 ≥25,000 步防"假结果"）、**ETA**（跑 1~2% 即报剩余时间，告别盲等）。
- 可复用性：不挑体系、不挑配体名，自己的对接文件放进文件夹即可跑；批量处理支持多 PDB 排队。
- 运行门槛亲民：4 核 CPU / 8 GB 内存 / 50 GB 磁盘即可起步，Mac/Ubuntu/WSL2/GPU 均实测可用。
- 分析自动化覆盖 RMSD/RMSF/Rg/二级结构/氢键/接触图/关键氨基酸占据，并给出 PCA（≥20–50 ns）与自由能方法的进阶门槛提醒。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| `run_pipeline.sh` | pipeline 入口脚本：`chmod +x` 后运行，交互式推进全流程 |
| PDB-Fixer | 自动补全缺失残基/原子的结构修复脚本 |
| hetero atoms | PDB 中挂载的异原子基团（辅因子、配体等），跑模拟前需决定去留 |
| CGenFF | 生成小分子 CHARMM 力场参数的在线服务器，全流程唯一人工环节 |
| `ligand_gmx.itp` | 配体的 GROMACS 拓扑文件，由 pipeline 从 CGenFF 结果自动转换 |
| networkx | 复合物构建依赖的 Python 库，要求专属 Python 3.7 环境 |
| dodecahedron | 十二面体盒子，与 cubic/triclinic/octahedron 同为可选溶剂盒形状 |
| PME | Particle Mesh Ewald，长程静电的默认求解方法 |
| barostat | 恒压器（控压算法），NPT/生产模拟中的压力控制；不懂选默认即可 |
| ETA | 预计剩余时间：模拟开跑 1~2% 后自动给出 |
| resume | 断点续跑：从指定步骤恢复，或复用既有结果跳过重算 |
| batch processing | 批量处理：多个 PDB ID 排队，机器自动连跑多个体系 |
| DSSP | 二级结构指认算法，分析阶段自动输出二级结构变化图 |
| contact map | 接触热图：展示哪些氨基酸与配体保持接触及持续时间 |
