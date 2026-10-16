# TemStaPro ｜ Predicting Protein Thermostability Values ｜ Full Tutorial

> 来源视频：[TemStaPro | Predicting Protein Thermostability Values | Full Tutorial](https://www.youtube.com/watch?v=k3Zcb8HkDtE)（YouTube，4 分 39 秒）。本文基于该视频的「图-字幕」演说稿整理，所有结论均出自视频画面与口播，内容可核查。

## 本讲要解决的核心问题（SCQA）

**背景**：结构导向的蛋白设计流水线里，ProteinMPNN 这类逆折叠模型能对给定骨架一口气生成一批备选序列——比如对 β-内酰胺酶（beta-lactamase）生成的一整批变体。

**冲突**：候选序列多了，谁更耐热就成了新问题——逐条做实验测热稳定性成本太高。

**疑问**：有没有现成工具，能把一批候选序列按不同温度批量打出热稳定性分数？

**回答（中心思想）**：在 Neurosnap 平台上跑 TemStaPro：上传 ProteinMPNN 生成的变体序列 CSV，指定名称列与序列列，约 2 分钟返回每个变体在 40/45/50/55/60/65 °C 下的平均热稳定性分数——分数来自逐残基预测（0–1，可当概率看）再对全分子取平均——配合箱线图看整体分布与中位数，就能从候选库里挑出整体最耐热的变体。

## 一、TemStaPro 是什么，为什么接在 ProteinMPNN 后面

### 1.1 逆折叠生成的序列需要"耐热筛选"

TemStaPro 是 Neurosnap 上的一个模型，用来预测蛋白在多种不同温度下的热稳定性 [【跳转到 00:00】](https://www.youtube.com/watch?v=k3Zcb8HkDtE&t=0)。本教程特意接续之前的一期演示：用 ProteinMPNN 对 β-内酰胺酶做序列设计。ProteinMPNN 是逆折叠（inverse folding）模型——对给定输入结构预测一批备选序列；想深入了解这个概念可以去看那一期 [【跳转到 00:12】](https://www.youtube.com/watch?v=k3Zcb8HkDtE&t=12)、[【跳转到 00:22】](https://www.youtube.com/watch?v=k3Zcb8HkDtE&t=22)。

![TemStaPro 教程开场：在 Neurosnap 上按温度预测蛋白热稳定性](assets/TemStaPro%20%EF%BD%9C%20Predicting%20Protein%20Thermostability%20Values%20%EF%BD%9C%20Full%20Tutorial/00000.webp)

![逆折叠模型讲解时刻：ProteinMPNN 为给定骨架生成备选序列](assets/TemStaPro%20%EF%BD%9C%20Predicting%20Protein%20Thermostability%20Values%20%EF%BD%9C%20Full%20Tutorial/00022.webp)

### 1.2 在 Neurosnap 上提交任务

长话短说：把上次 ProteinMPNN 运行的结果表导出为 CSV，作为 TemStaPro 的输入 [【跳转到 00:40】](https://www.youtube.com/watch?v=k3Zcb8HkDtE&t=40)、[【跳转到 00:45】](https://www.youtube.com/watch?v=k3Zcb8HkDtE&t=45)。上传 CSV 后需要指定两个列名：名称列（这里确认用 Rank）与序列列，点提交后所有变体序列加载完毕 [【跳转到 00:55】](https://www.youtube.com/watch?v=k3Zcb8HkDtE&t=55)、[【跳转到 01:08】](https://www.youtube.com/watch?v=k3Zcb8HkDtE&t=68)。这些就是 ProteinMPNN 生成的一批 β-内酰胺酶变体序列，点击 Finish 运行任务，剩下的交给 Neurosnap [【跳转到 01:08】](https://www.youtube.com/watch?v=k3Zcb8HkDtE&t=68)、[【跳转到 01:18】](https://www.youtube.com/watch?v=k3Zcb8HkDtE&t=78)。

Neurosnap 是一个在线平台，集成大量生信工具与模型：选工具、按需配置、上传必要的文件或数据即可，任务在它的服务器上运行，完成后返回结果 [【跳转到 01:23】](https://www.youtube.com/watch?v=k3Zcb8HkDtE&t=83)。

![上传 ProteinMPNN 结果 CSV 作为 TemStaPro 输入并指定列名](assets/TemStaPro%20%EF%BD%9C%20Predicting%20Protein%20Thermostability%20Values%20%EF%BD%9C%20Full%20Tutorial/00045.webp)

![变体序列加载完毕，点击 Finish 提交运行](assets/TemStaPro%20%EF%BD%9C%20Predicting%20Protein%20Thermostability%20Values%20%EF%BD%9C%20Full%20Tutorial/00068.webp)

## 二、读懂输出：从逐残基概率到全分子平均分

### 2.1 结果表的每一列

任务约 2 分钟完成，速度不错，并且产出了多种可视化 [【跳转到 01:39】](https://www.youtube.com/watch?v=k3Zcb8HkDtE&t=99)、[【跳转到 01:44】](https://www.youtube.com/watch?v=k3Zcb8HkDtE&t=104)。先看第一张表：第一列是蛋白名称——因为输入名称是纯数字，输出带了一串零后缀，可以安全忽略、不影响结果；第二列是蛋白长度（氨基酸个数）；之后就是 **40/45/50/55/60/65 °C 各温度下的平均预测热稳定性分数**列 [【跳转到 01:49】](https://www.youtube.com/watch?v=k3Zcb8HkDtE&t=109)、[【跳转到 02:14】](https://www.youtube.com/watch?v=k3Zcb8HkDtE&t=134)。

![TemStaPro 结果表：名称、长度与各温度平均热稳定性分数](assets/TemStaPro%20%EF%BD%9C%20Predicting%20Protein%20Thermostability%20Values%20%EF%BD%9C%20Full%20Tutorial/00099.webp)

### 2.2 0–1 分数：某温度下"保持折叠"的似然

这个平均分怎么来的？TemStaPro 实际是**对蛋白里每一个氨基酸逐个预测热稳定性**；为了得到全分子的代表值，再对每个温度取平均——因为模型对不同温度给出不同的热稳定性概率 [【跳转到 02:14】](https://www.youtube.com/watch?v=k3Zcb8HkDtE&t=134)、[【跳转到 02:39】](https://www.youtube.com/watch?v=k3Zcb8HkDtE&t=159)。数值一般在 0–1 之间：0 表示在该温度下稳定的可能性低，1 表示很可能稳定——基本可以当概率看 [【跳转到 02:39】](https://www.youtube.com/watch?v=k3Zcb8HkDtE&t=159)。例如表中某一行的位置 11 在 65 °C 下，模型几乎确定该位置相对不稳定；当然要看整体结构，所以要做平均 [【跳转到 03:04】](https://www.youtube.com/watch?v=k3Zcb8HkDtE&t=184)。

### 2.3 箱线图：整体分布与中位数

换一条整体预测热稳定性更高的序列来看最后的箱线图：开头的小区域展示模型预测的热稳定性分数分布形态，箱线图与之对应。这条蛋白的氨基酸分布整体偏向更耐热，而且这种趋势一直延续到较高温度、中位数仍为正——它可能就是整批变体里更耐热的那一个 [【跳转到 03:29】](https://www.youtube.com/watch?v=k3Zcb8HkDtE&t=209)、[【跳转到 03:39】](https://www.youtube.com/watch?v=k3Zcb8HkDtE&t=219)、[【跳转到 04:04】](https://www.youtube.com/watch?v=k3Zcb8HkDtE&t=244)。

![箱线图讲解时刻：热稳定性分数分布与中位数](assets/TemStaPro%20%EF%BD%9C%20Predicting%20Protein%20Thermostability%20Values%20%EF%BD%9C%20Full%20Tutorial/00219.webp)

## 三、用分数挑变体：一条热稳定性优化流水线

整套流程就是"从候选变体数据集中做热稳定性优化"的闭环：ProteinMPNN 从骨架生成一批候选序列 → TemStaPro 按温度逐残基打分 → 平均分 + 箱线图看分布与中位数 → 挑出整体最耐热的变体 [【跳转到 04:13】](https://www.youtube.com/watch?v=k3Zcb8HkDtE&t=253)。视频结尾欢迎观众在评论区提问或对后续内容提建议 [【跳转到 04:23】](https://www.youtube.com/watch?v=k3Zcb8HkDtE&t=263)。

## 小结

- TemStaPro：在 Neurosnap 平台上按温度（40–65 °C 六档）预测蛋白热稳定性的工具，开箱即用、约 2 分钟出结果。
- 输入设计得很顺：ProteinMPNN（逆折叠）生成的变体序列 CSV 可直接喂入，指定名称列与序列列即可。
- 分数语义：逐残基预测的 0–1 概率式分数，对全分子取平均后得到各温度下的平均热稳定性分数。
- 读表顺序：先看各温度平均分列，再用箱线图看整体分布与中位数（中位数仍为正 = 整体更耐热）。
- 用途：从一批候选变体中批量挑出最耐热的序列，构成"设计 → 打分 → 筛选"的闭环。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| TemStaPro | 按温度预测蛋白热稳定性的模型，对每个氨基酸逐个打 0–1 分，Neurosnap 平台可在线使用 |
| Neurosnap | 集成多种生信工具与模型的在线平台：选工具、配置、上传数据即可在服务器上运行 |
| ProteinMPNN | 逆折叠模型：给定蛋白结构，生成多条备选氨基酸序列 |
| 逆折叠（inverse folding） | 与结构预测相反的任务：从骨架结构反推可行的氨基酸序列 |
| 热稳定性分数 | TemStaPro 输出：0–1 的概率式分数，表示某温度下残基保持稳定的可能性 |
| β-内酰胺酶（beta-lactamase） | 本教程示例蛋白：一类水解 β-内酰胺类抗生素的酶 |
