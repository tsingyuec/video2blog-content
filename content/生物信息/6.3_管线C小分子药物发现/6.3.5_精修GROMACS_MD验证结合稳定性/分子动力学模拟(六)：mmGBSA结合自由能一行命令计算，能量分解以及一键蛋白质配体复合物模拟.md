# 分子动力学模拟(六)：mmGBSA结合自由能一行命令计算，能量分解以及一键蛋白质配体复合物模拟

> 视频来源：[B站《分子动力学模拟(六)：mmGBSA结合自由能一行命令计算，能量分解以及一键蛋白质配体复合物模拟》](https://www.bilibili.com/video/BV1MdZGYTEYP)（9:12，UP 主：玄月只有无言）。系列第六集：用开源包 **uni-GBSA**（UP 主同事开发，发表于 Briefings in Bioinformatics）**一行命令**完成 MM-GBSA 结合自由能计算与**逐残基能量分解**，并演示"一键跑复合物 MD"的便捷用法与适用边界。视频字幕为 B 站 AI 字幕（kedou 配额耗尽，经 cookie 降级链抓取 ai-zh 轨道），已逐窗口纠正错拼（"MMGBC/GPSA/GPIC/GBAC"→MM-GBSA、"unit g b c"→uni-GBSA、"自由能围绕"→自由能微扰（FEP）、"legend"→ligand、"MOTO"→mol2、"残疾"→残基、"matt flow live"→matplotlib、"ACPIPE"→ACPYPE、"PDP"→PDB、"DC点CSV"→dec.csv、"RG0210"→残基名误拼 等）；本文基于文稿整理，所有操作可点时间戳回看核对。

## 本讲要解决的核心问题（SCQA）

**背景**：MD 轨迹已经到手（本系列第五集），用 RMSD、氢键等指标可以**定性**判断复合物"散没散架"。

**冲突**：但论文里需要一个**可比的"结合强度"数字**——对接打分太粗（详见 6.3.4），严格自由的 FEP（自由能微扰）又太贵；"看起来稳"和"结合有多强"之间还差一步。

**疑问**：有没有一种方法，精度比对接打分好、成本又远低于 FEP？

**回答（中心思想）**：**MM-GBSA**——构建热力学循环、用"分子力学 + 广义玻恩（GB）隐式溶剂 + 表面积项"估算结合自由能，精度介于两者之间，是科研发表中的常见选择（[【跳转到 00:13】](https://www.bilibili.com/video/BV1MdZGYTEYP/?t=13)）。本集用同事开发的 **uni-GBSA** 包把它变成"一行命令"。

![MM-GBSA：精度介于对接打分与自由能微扰之间](assets/分子动力学模拟%28六%29：mmGBSA结合自由能一行命令计算，能量分解以及一键蛋白质配体复合物模拟/00013.webp)

## 一、安装 uni-GBSA：一个环境、两行命令

uni-GBSA 的 GitHub 地址在视频里给出。安装思路：

1. 一行 conda 命令**同时创建虚拟环境并安装** ACPYPE、OpenMM 等依赖与 mmgbsa 本体——注意它依赖 **GROMACS**，如果你跟着本系列一路学下来应该已经装好（[【跳转到 00:38】](https://www.bilibili.com/video/BV1MdZGYTEYP/?t=38)）；
2. 激活环境后，再安装 uni-gbsa 与配套依赖，软件部分就绪（[【跳转到 01:28】](https://www.bilibili.com/video/BV1MdZGYTEYP/?t=88)）。

UP 主特别提醒：这个包发表在 Briefings in Bioinformatics 上，**使用时记得引用**。

![一行命令创建环境并安装依赖与 mmgbsa](assets/分子动力学模拟%28六%29：mmGBSA结合自由能一行命令计算，能量分解以及一键蛋白质配体复合物模拟/00038.webp)

## 二、快速版：静态结构一行估 ΔG

如果只想对"一个蛋白 + 一个配体"快速估算结合自由能并做能量分解，一条 `--pipeline` 命令搞定：

- `-I` 输入**蛋白 PDB**；`-L` 输入**配体的 SDF 或 mol2**；`-o` 指定输出文件；`--decomposition` 表示要**能量分解**（[【跳转到 01:58】](https://www.bilibili.com/video/BV1MdZGYTEYP/?t=118)）。
- **前提**：蛋白和小分子都必须**已经做完准备**（加氢、质子化状态正确等），否则结果不成立。

UP 主实测：命令跑约 **2 分钟**结束，得到 ΔG ≈ **−52 kcal/mol**（[【跳转到 02:48】](https://www.bilibili.com/video/BV1MdZGYTEYP/?t=168)）。

![--pipeline 一行命令：-I 蛋白、-L 配体、-o 输出、--decomposition](assets/分子动力学模拟%28六%29：mmGBSA结合自由能一行命令计算，能量分解以及一键蛋白质配体复合物模拟/00118.webp)

![约 2 分钟算出 −52 kcal/mol，但绝对值本身意义不大](assets/分子动力学模拟%28六%29：mmGBSA结合自由能一行命令计算，能量分解以及一键蛋白质配体复合物模拟/00168.webp)

## 三、读数纪律：只有"相对值"有意义

这是全片最重要的一段提醒（[【跳转到 02:48】](https://www.bilibili.com/video/BV1MdZGYTEYP/?t=168)、[【跳转到 03:13】](https://www.bilibili.com/video/BV1MdZGYTEYP/?t=193)）：

- **绝对值没有意义**：−52 kcal/mol 不代表"结合能就是 52"；只有**计算多个配体、比较它们的相对大小**才有意义；
- MM-GBSA **比对接打分好不少**，但它与实验值的相关性**也没有好到哪里去**——结论只能当参考；
- 有条件的话，**最后还是要做实验**验证。

## 四、输出文件：总 ΔG + 逐残基能量分解

计算结束后会生成一个**以配体名命名**的文件夹：

- `binding_energy.csv`：整个体系的**总结合自由能**（[【跳转到 03:43】](https://www.bilibili.com/video/BV1MdZGYTEYP/?t=223)）；
- `dec.csv`：**逐残基能量分解**——把结合自由能分配到蛋白的每一个残基上，看每个残基对结合的贡献，并按能量类型（范德华、静电、极性……）分列（[【跳转到 04:05】](https://www.bilibili.com/video/BV1MdZGYTEYP/?t=245)）。

![输出文件：binding_energy.csv 汇总 + dec.csv 分解](assets/分子动力学模拟%28六%29：mmGBSA结合自由能一行命令计算，能量分解以及一键蛋白质配体复合物模拟/00223.webp)

![dec.csv：每个残基的贡献与能量类型分列](assets/分子动力学模拟%28六%29：mmGBSA结合自由能一行命令计算，能量分解以及一键蛋白质配体复合物模拟/00245.webp)

有了这张表就可以画图：装上 **pandas 和 matplotlib**，用 UP 主提供的脚本出图——横轴是**与小分子有相互作用的残基**，纵轴是**结合自由能贡献**（[【跳转到 04:40】](https://www.bilibili.com/video/BV1MdZGYTEYP/?t=280)）。示例体系里贡献最大的残基（字幕误拼为"RG0210"，应为编号 210 附近的精氨酸类残基，以 dec.csv 实际输出为准）一眼可辨——这正是找**热点残基、指导突变/优化**的起点。

![逐残基贡献柱状图：横轴残基、纵轴 ΔG 贡献](assets/分子动力学模拟%28六%29：mmGBSA结合自由能一行命令计算，能量分解以及一键蛋白质配体复合物模拟/00280.webp)

## 五、正式版：基于 MD 轨迹的 MM-GBSA

快速版只算静态结构；**真正的 MM-GBSA 应该对 MD 轨迹逐帧计算再取平均**。步骤（[【跳转到 05:38】](https://www.bilibili.com/video/BV1MdZGYTEYP/?t=338)）：

1. 先用 `gmx make_ndx` 准备 index 文件，把**蛋白和配体分别选出来**建两组：蛋白组命名 **receptor**，小分子组命名 **ligand**。做蛋白-蛋白模拟时同理——把 A 链当 receptor、B 链当 ligand，就能算两条链之间的结合自由能（[【跳转到 06:03】](https://www.bilibili.com/video/BV1MdZGYTEYP/?t=363)）；
2. 用 `uni-gbsa` 的轨迹命令：`-T` 输入轨迹 `md.xtc`，`-I` 输入体系的 `tpr`，`-P` 输入拓扑文件与 index 文件（指明谁是 receptor、谁是 ligand），`-M` 指定方法（GB），逐帧计算 GB 再取平均（[【跳转到 06:33】](https://www.bilibili.com/video/BV1MdZGYTEYP/?t=393)）；
3. 加 `--decomposition` 可做逐残基分解，但**可能会报错**；不加分解项直接跑是稳定的（[【跳转到 06:33】](https://www.bilibili.com/video/BV1MdZGYTEYP/?t=393)）。

![index：蛋白组 receptor、配体组 ligand（蛋白-蛋白体系同理）](assets/分子动力学模拟%28六%29：mmGBSA结合自由能一行命令计算，能量分解以及一键蛋白质配体复合物模拟/00338.webp)

![基于轨迹的 MM-GBSA：-T 轨迹、-I tpr、-P 拓扑+index、-M gb](assets/分子动力学模拟%28六%29：mmGBSA结合自由能一行命令计算，能量分解以及一键蛋白质配体复合物模拟/00393.webp)

## 六、一键 MD：很方便，但初学别用这个"拐棍"

uni-GBSA 还能**直接跑蛋白-配体复合物的 MD**（`-MD` 模式）：`-P` 提供准备好的蛋白 PDB，`-L` 提供准备好的配体文件，`-pf`/`-lf` 分别指定蛋白与配体力场，`-d` 指定盒子大小与离子浓度，再给输出目录和步数，默认步长 2 fs（[【跳转到 07:28】](https://www.bilibili.com/video/BV1MdZGYTEYP/?t=448)）。

![uni-GBSA -MD：一键复合物分子动力学](assets/分子动力学模拟%28六%29：mmGBSA结合自由能一行命令计算，能量分解以及一键蛋白质配体复合物模拟/00448.webp)

但 UP 主的忠告是（[【跳转到 08:18】](https://www.bilibili.com/video/BV1MdZGYTEYP/?t=498)）：**初学时不要用这个拐棍**——老老实实按系列第五集的步骤一步一步手动做，理解每一步在干什么；等你熟悉之后、需要**大批量**处理时，再用一行命令提效。

![忠告：初学别用一键 MD，先手动走通全流程](assets/分子动力学模拟%28六%29：mmGBSA结合自由能一行命令计算，能量分解以及一键蛋白质配体复合物模拟/00498.webp)

## 小结：管线 C 的"精修"闭环至此走完

- **定性**：对接 pose → MD 轨迹 → RMSD/RMSF/氢键/Rg 判断"稳不稳"（见本条目前两篇）；
- **定量**：轨迹 → MM-GBSA → ΔG 排序 + 逐残基分解找热点，衔接后续的先导优化与实验验证；
- **边界**：ΔG 只做相对比较，别把绝对值写进结论；MM-GBSA 与实验的相关性有限，最终裁决靠实验。
