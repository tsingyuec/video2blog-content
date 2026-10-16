# RFDiffusion3 蛋白 binder 设计上机讲解（MPNN 部分）：从 80 个骨架到 480 条序列

> 视频来源：[RFDiffusion3 AI蛋白设计 binder设计 上机操作 及 讲解 MPNN部分](https://www.bilibili.com/video/BV1uDbW6tE3c/)（约 7 分钟，命令行批量实操）。本视频是 RFdiffusion3 binder 设计教程的**续篇**——上一节（见 5.2.1(a)）用 RFdiffusion3 生成了骨架，本节做下一步：MPNN 序列优化。

## 本讲要解决的核心问题（SCQA）

**背景**：上一讲已经用 RFdiffusion3（RF3）为靶蛋白生成了 **80 个 binder 骨架文件**——这是 binder 设计三部曲的第 (a) 步产物。

**冲突**：RFdiffusion 只负责骨架形状，附带的序列并不保证「好用」——可能表达量低、容易聚集沉淀，这样的 binder 到了湿实验环节就很难产出蛋白。

**疑问**：怎么把这 80 个骨架**批量**变成「好表达、不易聚集」的氨基酸序列？

**回答（中心思想）**：用 MPNN 脚本批量逆折叠：80 个骨架 × 每个优化 3 条 × run 2 轮 = **480 条候选序列**；下一步再用 Rosetta 对全部序列打分，选出 top5 或 top10 进入湿实验验证。这正是 binder 设计三部曲中「骨架 → 序列」的第 (b) 步 [【跳转到 00:00】](https://www.bilibili.com/video/BV1uDbW6tE3c/?t=0)。

## 一、脚本怎么写：输入、输出与批量参数

### 1.1 从 RF3 骨架文件出发

作者写了一个 MPNN 批量脚本：输入文件是 RF3 刚生成的 80 个 binder 的 **PDB 文件**，输出文件夹设为 `mpnn_out` [【跳转到 00:25】](https://www.bilibili.com/video/BV1uDbW6tE3c/?t=25)。

![MPNN 批量脚本：输入 80 个 PDB，输出 mpnn_out](assets/RFDiffusion3%20AI蛋白设计%20binder设计%20上机操作%20及%20讲解%20MPNN部分/00000.webp)

![脚本参数：输入输出路径与生成条数](assets/RFDiffusion3%20AI蛋白设计%20binder设计%20上机操作%20及%20讲解%20MPNN部分/00025.webp)

### 1.2 每个骨架优化几条、跑几轮

两个关键的批量参数：

- **每个骨架生成几条**：本次设为 3 条（也可以写得更高，比如 10 条）；为了实操演示先写 3。
- **跑几轮（batch/run）**：可以 run 1 轮或 run 2 轮，都可以 [【跳转到 00:50】](https://www.bilibili.com/video/BV1uDbW6tE3c/?t=50)。

### 1.3 conda 环境里运行

保存脚本后，还要用之前准备好的 **conda 环境**：直接用 Python 运行 MPNN 脚本即可。程序跑起来后输出 `parsing 80 backbone structures to design sequence for`，这一步时间其实比较快 [【跳转到 01:10】](https://www.bilibili.com/video/BV1uDbW6tE3c/?t=70)。

![conda 环境运行，parsing 80 backbones](assets/RFDiffusion3%20AI蛋白设计%20binder设计%20上机操作%20及%20讲解%20MPNN部分/00070.webp)

运行后可以立即看到 `mpnn_out` 文件夹已经创建（最初还是空的，稍等片刻就有结果写入）。

## 二、数量账：80 → 240 → 480

这一步的数量关系值得算清楚 [【跳转到 01:45】](https://www.bilibili.com/video/BV1uDbW6tE3c/?t=105)：

- RF3 原来给出 **80 个 binder**；
- 每个骨架生成 3 条优化序列：3 × 80 = **240 条**；
- 如果 run 两轮，就是 **480 条**。

![80 骨架 × 3 条 × 2 轮 = 480 条序列](assets/RFDiffusion3%20AI蛋白设计%20binder设计%20上机操作%20及%20讲解%20MPNN部分/00105.webp)

在实际的科研操作中，这个数字可能会更大——可能几千条、要跑上几天。生成过程中可以看到 `mpnn_out` 里的文件快速增长，很快就跑完了 [【跳转到 02:10】](https://www.bilibili.com/video/BV1uDbW6tE3c/?t=130)。

![生成完成，下一步 Rosetta 打分](assets/RFDiffusion3%20AI蛋白设计%20binder设计%20上机操作%20及%20讲解%20MPNN部分/00130.webp)

## 三、结果对比：序列被改了哪里

### 3.1 原始骨架 vs MPNN 优化序列

打开 binder_0 的 model_0 PDB：最上面是原始的、用 RFdiffusion3 生成的骨架；下面是 MPNN 优化的 model_0——每个骨架生成了六条（2 轮 × 3 条）。视频中加载结构时遇到了一点显示小插曲（生成的 MPNN 文件在 Python 里显示有些问题，修复后凑合着看），不影响结论 [【跳转到 02:56】](https://www.bilibili.com/video/BV1uDbW6tE3c/?t=176)。

![对比原始 binder_0 与 MPNN 优化结果](assets/RFDiffusion3%20AI蛋白设计%20binder设计%20上机操作%20及%20讲解%20MPNN部分/00176.webp)

### 3.2 逐残基看替换：R→K、Q→E、D→A

对比原始序列和优化序列，能看到具体的氨基酸替换 [【跳转到 04:46】](https://www.bilibili.com/video/BV1uDbW6tE3c/?t=286)：

- 原来是 **R**（精氨酸）的位置，优化后变成了 **K**（赖氨酸）；
- 原来是 **Q**（谷氨酰胺）的位置，变成了 **E**（谷氨酸）；
- 逐位检查还有 **D → A** 等替换；
- 也有很多位置保持不变（比如某个 E、某个 K 原样保留），比如第二位变成了 L。

![R→K、Q→E：MPNN 对序列的逐残基优化](assets/RFDiffusion3%20AI蛋白设计%20binder设计%20上机操作%20及%20讲解%20MPNN部分/00286.webp)

整体看，很多残基仍然相似——MPNN 并不是把序列推倒重来，而是在保持骨架的前提下**对氨基酸序列重新进行优化**。

### 3.3 为什么这样改：表达量与聚集

MPNN 优化序列的逻辑是：它按**自然界的天然氨基酸序列**的统计规律来打分，所以优化后的序列 [【跳转到 05:11】](https://www.bilibili.com/video/BV1uDbW6tE3c/?t=311)：

- **更容易表达**，表达量比较高；
- **不容易聚集**；
- 做纯化的时候，收率也会比较高。

![MPNN 按天然序列规律优化：好表达、不易聚集](assets/RFDiffusion3%20AI蛋白设计%20binder设计%20上机操作%20及%20讲解%20MPNN部分/00311.webp)

![序列差异对比与纯化收率](assets/RFDiffusion3%20AI蛋白设计%20binder设计%20上机操作%20及%20讲解%20MPNN部分/00336.webp)

这正是 RFdiffusion 输出序列「能折叠但不一定好表达」问题的对症解法——也是为什么 binder 设计三部曲里，骨架生成之后必须接一步 MPNN。

## 四、下一步：Rosetta 打分与湿实验验证

本节最终生成了 **480 条**候选序列。下一步的操作已经预告 [【跳转到 06:49】](https://www.bilibili.com/video/BV1uDbW6tE3c/?t=409)：

1. 使用 **Rosetta** 对这 480 条序列进行打分；
2. 选出 top——比如 top5 或 top10 的分子；
3. 如果这些分子的各项指标足够完美，就可以开展**湿实验**对它进行验证。

![480 条序列 → Rosetta 打分 → top5/10 → 湿实验](assets/RFDiffusion3%20AI蛋白设计%20binder设计%20上机操作%20及%20讲解%20MPNN部分/00409.webp)

至此，「RFdiffusion3 生成骨架 → MPNN 配序列」两步闭环完成，三部曲的第三步（Protenix/OpenFold3 回折验证）与 Rosetta 打分一起构成完整的筛选流水线。

## 小结

- 本视频是 RFdiffusion3 binder 设计教程的续篇：对上一步生成的 **80 个 binder 骨架**做 MPNN 序列优化。
- 脚本三要素：输入 PDB 骨架、输出 `mpnn_out`、每骨架 3 条 × 可跑多轮。
- 数量账：80 × 3 = 240；run 2 轮 = **480 条**；实际项目几千条、跑几天很正常。
- 运行依赖之前建好的 conda 环境，Python 一键启动，80 个骨架解析很快。
- 对比结果：R→K、Q→E、D→A 等逐残基替换，整体与原序列保持相似——重优化而非重设计。
- 优化逻辑：MPNN 按自然界天然序列的统计规律打分，使序列更好表达、不易聚集、纯化收率高。
- 下游流程：480 条 → Rosetta 打分 → top5/top10 → 指标完美才进湿实验。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| binder | 能结合靶蛋白的（设计）蛋白，本流程的设计目标 |
| RFdiffusion3（RF3） | Baker 实验室全原子扩散骨架生成模型，三部曲第 (a) 步 |
| MPNN | ProteinMPNN 逆折叠模型，给骨架配序列，三部曲第 (b) 步 |
| mpnn_out | 脚本的输出文件夹，存放每条优化序列 |
| run 轮数 | 批量参数：跑几轮决定每骨架产出的序列倍数 |
| conda 环境 | 隔离的 Python 运行环境，复用之前配置好的依赖 |
| Rosetta | 经典打分/建模工具，下一步用于给 480 条序列排序 |
| top5 / top10 | 打分筛选后保留的头部候选，进入湿实验验证 |
| 湿实验 | 试管/细胞层面的真实实验，验证计算设计的最终关卡 |
