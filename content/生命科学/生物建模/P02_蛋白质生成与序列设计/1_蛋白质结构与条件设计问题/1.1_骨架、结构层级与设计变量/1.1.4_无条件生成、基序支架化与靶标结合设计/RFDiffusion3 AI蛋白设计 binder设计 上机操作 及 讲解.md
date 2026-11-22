# RFDiffusion3 AI蛋白设计 binder设计 上机操作 及 讲解

> 视频来源：Bilibili [RFDiffusion3 AI蛋白设计 binder设计 上机操作 及 讲解](https://www.bilibili.com/video/BV1ohbH6aETT/)（AI药物研发X资深玩家，约 4 分 55 秒）。
> 本篇对应「蛋白 Binder 设计三部曲」的第一步——**(a) RFdiffusion 骨架生成**的全原子版本 RFdiffusion3：视频结尾明确指出，骨架生成后的下一步是 MPNN 序列优化（三部曲第二步）。

## 本讲要解决的核心问题（SCQA）

**背景**：经典 RFdiffusion 用 bash 脚本 + `contigs` 字符串描述 binder 设计任务（见同目录《RFdiffusion系列教程（5）：结合蛋白设计》）；RFdiffusion3 升级为全原子模型，配置方式也随之改变。

**冲突**：全原子版本改用 **JSON 配置文件**，写法与经典版完全不同；初学者容易不知道 JSON 里该填哪几项、热点要写到什么精度。

**疑问**：如何用 RFdiffusion3 为靶蛋白 PDL1 配置并生成一批 binder 骨架？

**回答（中心思想）**：写一份 binder JSON，填四项关键信息——靶蛋白链、binder 长度区间 50~120、靶链残基编号范围 18~132、热点 A56/A66（全原子模型建议精确到原子）；激活 conda 环境后用 `RFdiffusion design` 命令运行 10 个 batch（每批默认 8 个，共约 80 个骨架），把输出的 cif 拖进查看器确认 binder 贴在 PDL1 上，骨架完成后交给 MPNN 优化序列。

## 一、JSON 配置：四项关键信息

### 1.1 靶蛋白与 binder 长度

视频开篇（[【跳转到 00:00】](https://www.bilibili.com/video/BV1ohbH6aETT/?t=0)）作者展示了自己写好的 binder JSON 文件。第一项信息是**靶蛋白**：本例设为 **PDL1**（程序性死亡配体 1，肿瘤免疫中的知名靶点）。

第二项是**要设计的 binder（小蛋白）的氨基酸长度**（[【跳转到 00:25】](https://www.bilibili.com/video/BV1ohbH6aETT/?t=25)）：这里设置为 **50~120 个氨基酸**的区间——与经典版的 `70-100` 长度写法同一个思路，给扩散过程一个落点范围。

![binder JSON 配置文件：靶蛋白与长度设置](assets/RFDiffusion3%20AI蛋白设计%20binder设计%20上机操作%20及%20讲解/00000.webp)

![binder 长度 50~120，18~132 是 PDL1 的 PDB 残基编号范围](assets/RFDiffusion3%20AI蛋白设计%20binder设计%20上机操作%20及%20讲解/00025.webp)

### 1.2 靶链残基编号范围

JSON 里的 `18~132` 指的是 **PDL1 这条 PDB 链的氨基酸编号**：从第 18 位开始、到第 132 位结束（[【跳转到 00:25】](https://www.bilibili.com/video/BV1ohbH6aETT/?t=25)）。也就是说，只在这段残基上做文章，其余部分不参与 binder 结合位点的圈定。

### 1.3 hotspot：全原子模型可以精确到原子

第三项是 **hotspot（热点）**，即 binder 与靶蛋白结合的位置（[【跳转到 00:50】](https://www.bilibili.com/video/BV1ohbH6aETT/?t=50)）。作者随机选了两个残基 **A56 和 A66**。

重点来了：因为 **RFdiffusion3 是全原子模型**，热点配置可以**精确选择到具体的原子**；当然只写到残基层面（`A56, A66`）也可以运行，但作者**建议直接写到原子层面**（[【跳转到 01:15】](https://www.bilibili.com/video/BV1ohbH6aETT/?t=75)）——控制粒度更细，binder 贴合的位置更可控。

![hotspot A56/A66：全原子模型建议写到原子层面](assets/RFDiffusion3%20AI蛋白设计%20binder设计%20上机操作%20及%20讲解/00050.webp)

## 二、运行：conda 环境 + 一条命令

JSON 写好后，先**激活 conda 环境**（[【跳转到 01:15】](https://www.bilibili.com/video/BV1ohbH6aETT/?t=75)），然后使用运行命令——作者提前准备好，直接复制即可（[【跳转到 01:40】](https://www.bilibili.com/video/BV1ohbH6aETT/?t=100)）。

命令的关键参数（[【跳转到 02:05】](https://www.bilibili.com/video/BV1ohbH6aETT/?t=125)）：

- `RFdiffusion design`：设计模式；
- 输出文件名设为 `bb`；
- `input` 指向 **binder JSON**（注意这里用的是 JSON，**不带 PDB**——靶蛋白信息都写在 JSON 里了）；
- **每个 batch 生成 10 个**。

确认能正常运行后即可放手让它跑（[【跳转到 02:30】](https://www.bilibili.com/video/BV1ohbH6aETT/?t=150)）。

![RFdiffusion design 命令：输入 binder JSON，每 batch 十个](assets/RFDiffusion3%20AI蛋白设计%20binder设计%20上机操作%20及%20讲解/00125.webp)

## 三、查看结果：80 个 binder 骨架

等运行暂停后回看（[【跳转到 03:06】](https://www.bilibili.com/video/BV1ohbH6aETT/?t=186)）：按**默认设置每批生成 8 个**，本例设置了 **10 个批次**，所以一共生成 **80 个 binder** 骨架。

![默认每批 8 个 × 10 批 = 80 个 binder](assets/RFDiffusion3%20AI蛋白设计%20binder设计%20上机操作%20及%20讲解/00186.webp)

查看方式很直接（[【跳转到 03:35】](https://www.bilibili.com/video/BV1ohbH6aETT/?t=215)）：把生成的 **cif 文件直接拖进查看器**。放大后可以辨认（[【跳转到 03:49】](https://www.bilibili.com/video/BV1ohbH6aETT/?t=229)）：

- **下方蓝色的**：PDL1 蛋白；
- **上方新长出来的**：新生成的 binder。

![蓝色为 PDL1，上方为新生成的 binder](assets/RFDiffusion3%20AI蛋白设计%20binder设计%20上机操作%20及%20讲解/00229.webp)

多拖几个 cif 对比，每个 binder 的形状都**不太一样**——这正是生成的多样性（[【跳转到 04:10】](https://www.bilibili.com/video/BV1ohbH6aETT/?t=250)）。但要记住：**现在生成的其实只是骨架**——氨基酸序列还没定。

![不同 cif 形状各异；当前产物只是骨架](assets/RFDiffusion3%20AI蛋白设计%20binder设计%20上机操作%20及%20讲解/00250.webp)

## 四、下一步：MPNN 序列优化

视频收尾（[【跳转到 04:35】](https://www.bilibili.com/video/BV1ohbH6aETT/?t=275)）点明接续关系：**下一步基于这个骨架，用 MPNN 的方法对序列进行优化**，作者留到下个视频讲解（[【跳转到 04:40】](https://www.bilibili.com/video/BV1ohbH6aETT/?t=280)）。

这正好对应三部曲的接力：**(a) RFdiffusion/RFdiffusion3 出骨架 → (b) ProteinMPNN 补序列 → (c) 结构预测模型回折验证**。骨架阶段无论用经典版（contigs 字符串）还是全原子版（JSON 配置），交出去的都是同一类东西——只有主链走向的 PDB/cif。

![下一步：基于骨架用 MPNN 优化序列](assets/RFDiffusion3%20AI蛋白设计%20binder设计%20上机操作%20及%20讲解/00280.webp)

## 小结

- RFdiffusion3 的 binder 设计从 bash+contigs 换成了 **JSON 配置**：靶蛋白（PDL1）、binder 长度区间（50~120）、靶链残基编号范围（18~132）、hotspot（A56/A66）四项填齐即可。
- **全原子模型的红利**：hotspot 可以精确到原子层面，作者建议尽量写到原子而非只写残基。
- 运行三要素：conda 环境、`RFdiffusion design` 命令、`input` 指向 binder JSON（不带 PDB）；本例 10 batch × 默认每批 8 个 ≈ **80 个骨架**。
- 结果检查：cif 拖进查看器，蓝色 PDL1 之上长出的就是 binder；多个样品形状各异体现生成多样性。
- 产物是**纯骨架**：序列交给下一步的 MPNN——三部曲第一棒到第二棒的交接点。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| PDL1 | 程序性死亡配体 1，本例的靶蛋白 |
| binder JSON | RFdiffusion3 的任务配置文件：靶蛋白、binder 长度、残基编号范围、hotspot 都写在这里 |
| 残基编号范围（18~132） | PDB 链上允许 binder 结合设计的氨基酸区段 |
| hotspot | 引导 binder 结合位置的关键位点；RFdiffusion3 全原子模型下可写到具体原子 |
| batch | 一批生成任务；默认每批 8 个骨架，批次越多产出越多 |
| cif 文件 | 结构文件格式（现代 PDB 标准），RFdiffusion3 的输出载体 |
| MPNN / ProteinMPNN | 拿骨架补序列的逆折叠工具，三部曲第二步 |
