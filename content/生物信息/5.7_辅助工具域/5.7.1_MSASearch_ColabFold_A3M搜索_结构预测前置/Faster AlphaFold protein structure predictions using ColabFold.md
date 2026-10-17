# Faster AlphaFold protein structure predictions using ColabFold

> 视频来源：[Faster AlphaFold protein structure predictions using ColabFold](https://www.youtube.com/watch?v=gIbCAcMDM7E)（YouTube，Eric Pettersen / UCSF RBVI，2022 年 7 月，约 10 分钟）。本文基于该视频的图文稿整理，所有内容均可回溯到视频对应时间点。

## 本篇要解决的核心问题（SCQA）

**背景**：蛋白质结构预测已经成了结构生物学家的日常工具，但官方 AlphaFold2 流程并不轻快——它要先做多序列比对（MSA）搜索、再跑预测，一个蛋白往往要等上几个小时。

**冲突**： UCSF 的 ChimeraX 团队把 [ColabFold](https://www.youtube.com/watch?v=Rfw7thgGTwI)（Baker 实验室与 Sergey Ovchinnikov 等人开发的快速版 AlphaFold）接进了 ChimeraX：同样的蛋白，预测时间从几小时缩短到十几分钟——速度差了一个数量级。

**疑问**：它到底快在哪里？普通使用者又要怎么读懂它给出的结果？

**回答（中心思想）**：ColabFold 的提速来自一个**专门的序列比对服务器**（即 MSA Search：用极快的搜索算法在序列数据库中找同源序列、生成 MSA），加上对 AlphaFold 代码本身的优化；而预测结果是否可信，可以通过它给出的**序列覆盖图（coverage plot）**等输出快速判断——高覆盖、高一致性、同物种配对序列多，预测就越值得信任。

![ChimeraX 中展示的目标蛋白：一个细菌二聚体注射复合物](assets/Faster%20AlphaFold%20protein%20structure%20predictions%20using%20ColabFold/00042.webp)

## 一、快在哪里：一个专门的 MSA 搜索服务器

视频开头就点明：作者自己"没干什么重活"，真正的功劳属于 ColabFold 的作者们。ColabFold 从两方面给 AlphaFold 提速 [【跳转到 00:21】](https://www.youtube.com/watch?v=gIbCAcMDM7E&t=21)：

1. **做了一个非常快的序列比对服务器**——也就是 AlphaFold 预测流水线的前置步骤"MSA 搜索"：拿你的输入序列去序列数据库里搜同源序列，把它们比对排列成多序列比对（MSA）。官方流程里这一步用 HMMER 一类的工具要跑很久，ColabFold 换成了更快的搜索方案；
2. **优化了 AlphaFold 代码本身**——让模型推断部分也更快。

ChimeraX 只是把这两样成果接了进来。**对初学者来说，记住一件事就够了：AlphaFold 类模型的第一步永远是"搜同源序列、拼 MSA"，这一步以前最慢，ColabFold 把它变成了几十秒到几分钟的事。**（这一点与本系列 [2.3.2 A3M 格式](../../2.3_比对类格式/2.3.2_A3M格式/ColabFold%20-%20Making%20protein%20folding%20accessible%20to%20all%20via%20Google%20Colab!.md)中 ColabFold 作者报告的内容互相印证。）

![ChimeraX 的 AlphaFold 面板：粘贴序列的地方](assets/Faster%20AlphaFold%20protein%20structure%20predictions%20using%20ColabFold/00067.webp)

## 二、实操：从两条序列到一个复合物模型

视频里的例子是一个参与"向真核宿主细胞注射蛋白"的细菌二聚体复合物，两条链加起来约 200 个氨基酸——特意选个小蛋白，方便快速演示 [【跳转到 00:42】](https://www.youtube.com/watch?v=gIbCAcMDM7E&t=42)。

操作流程一目了然：

1. 菜单 `Tools → Structure Prediction → AlphaFold`，打开预测面板；
2. 把两条链的序列**用逗号分隔**贴进输入框（逗号是 ColabFold 的多链写法之一）；
3. 点 `Options` 可以选择：是否使用 PDB 数据库里的**模板结构**、是否对结果做**能量最小化**。作者用了默认值（不用模板、不做最小化）——这是最快的配置 [【跳转到 00:59】](https://www.youtube.com/watch?v=gIbCAcMDM7E&t=59)；
4. 点 `Predict`，任务提交到 Google Colab 服务器执行。

![预测选项：模板与能量最小化开关](assets/Faster%20AlphaFold%20protein%20structure%20predictions%20using%20ColabFold/00099.webp)

运行期间有个小插曲值得记住：首次在 Colab 运行会弹窗警告"代码不是 Google 官方的"，点 `Run Anyway` 即可 [【跳转到 01:39】](https://www.youtube.com/watch?v=gIbCAcMDM7E&t=99)。

大约 **5 分钟**后，5 个模型全部返回；而"以前的方式跑同样的计算要花几个小时" [【跳转到 02:47】](https://www.youtube.com/watch?v=gIbCAcMDM7E&t=167)。最好的那个模型会自动加载进 ChimeraX，用经典的置信度配色：**蓝色=高置信，黄/红=低置信** [【跳转到 04:04】](https://www.youtube.com/watch?v=gIbCAcMDM7E&t=244)。

![任务在 Google Colab 服务器上运行，约 5 分钟返回 5 个模型](assets/Faster%20AlphaFold%20protein%20structure%20predictions%20using%20ColabFold/00167.webp)

![预测完成：最优模型自动载入 ChimeraX，按置信度着色](assets/Faster%20AlphaFold%20protein%20structure%20predictions%20using%20ColabFold/00244.webp)

## 三、读懂 MSA 搜索结果：序列覆盖图

这才是本视频最有教学价值的部分。ColabFold 运行时会在日志里生成几张图，第一张就是**序列覆盖图**——它把你看不到的"MSA 搜索 + 比对"过程可视化了出来 [【跳转到 04:47】](https://www.youtube.com/watch?v=gIbCAcMDM7E&t=287)。

![序列覆盖图顶部：黑色曲线是每个位点上搜到的序列数](assets/Faster%20AlphaFold%20protein%20structure%20predictions%20using%20ColabFold/00287.webp)

这个例子中，搜索找到了约 **300 条**与输入匹配的序列。图上有四层信息，逐层看 [【跳转到 05:12】](https://www.youtube.com/watch?v=gIbCAcMDM7E&t=312)：

![覆盖图主体：黑线=各位点被多少条序列覆盖，横线=每条序列的覆盖范围](assets/Faster%20AlphaFold%20protein%20structure%20predictions%20using%20ColabFold/00312.webp)

1. **横轴**是拼接后的输入序列（两条链拼在一起，中间一条黑色竖线隔开：左边约 120 个残基是蛋白 1，右边是蛋白 2）；
2. **黑色曲线**是"每个残基位置上有多少条序列覆盖到了它"。本例中约 250 条序列覆盖了蛋白 1 的 C 端，N 端略少；蛋白 2 只有约 100 条覆盖；
3. **每条横线**代表一条搜到的序列，横线的长度就是它的覆盖范围。比如底部那些红线只覆盖蛋白 1 的后半段（C 端）[【跳转到 05:37】](https://www.youtube.com/watch?v=gIbCAcMDM7E&t=337)；
4. **颜色**代表序列一致性：红=低，绿/蓝=高。右侧有图例，且序列按一致性从高到低排列，所以越靠上颜色越"暖"不到、越蓝 [【跳转到 06:02】](https://www.youtube.com/watch?v=gIbCAcMDM7E&t=362)。

![覆盖图颜色图例：按序列一致性排序，红低蓝高](assets/Faster%20AlphaFold%20protein%20structure%20predictions%20using%20ColabFold/00362.webp)

![靠近顶部的区域：蛋白 1 与蛋白 2 同时出现绿色——来自同一物种的配对序列](assets/Faster%20AlphaFold%20protein%20structure%20predictions%20using%20ColabFold/00387.webp)

再看两个特殊区域 [【跳转到 06:27】](https://www.youtube.com/watch?v=gIbCAcMDM7E&t=387)：

- **顶部同时出现蛋白 1 和蛋白 2 的绿色条带**：说明搜索把同一物种里两条蛋白的同源序列**配对（paired）**到了一起；
- **大片白色区域**：某一侧是白色的行，代表该物种只有其中一条蛋白的同源序列、另一条没有 [【跳转到 06:52】](https://www.youtube.com/watch?v=gIbCAcMDM7E&t=412)。

![大片白色：该物种只搜到其中一条蛋白的同源序列](assets/Faster%20AlphaFold%20protein%20structure%20predictions%20using%20ColabFold/00412.webp)

## 四、怎么判断预测可不可信

作者给了三条目视判据 [【跳转到 06:52】](https://www.youtube.com/watch?v=gIbCAcMDM7E&t=412)：

- **覆盖高**（黑曲线整体不塌）；
- **一致性高**（蓝/绿多、红少）；
- **同物种配对序列多**——这一点对复合物预测尤其关键，因为"同一物种的两条序列来自同一个基因组，它们在一起工作"，模型才能据此把**两条链的相互作用界面**摆对 [【跳转到 07:17】](https://www.youtube.com/watch?v=gIbCAcMDM7E&t=437)。

换句话说：序列覆盖图本质上是"MSA 搜索质量报告"。搜到的同源序列又多又像、还成对出现，预测才值得信；反过来，如果覆盖图上一片红、大片白，就要对结果多留个心眼。

## 五、五个模型与输出文件

比对决合成了之后，ColabFold 用**五个训练略有差异的神经网络**各预测一个结构，得到五个略有不同的模型 [【跳转到 07:25】](https://www.youtube.com/watch?v=gIbCAcMDM7E&t=445)。日志里每个模型配有：

- 置信度着色的结构图；
- **PAE 图**（Predicted Aligned Error，预测对齐误差）：它是判断"两个链的相对摆放可不可信"的关键指标，本系列 [1.5.3](../../1.5_分子相互作用/1.5.3_抗体-抗原界面ipTM与界面几何评分/【公开课】基于AI预测蛋白质复合体的三维空间结构---AlphaFold-Multimer原理及使用.md) 有专门展开 [【跳转到 07:38】](https://www.youtube.com/watch?v=gIbCAcMDM7E&t=458)；
- 逐链着色的结构图，方便看两条链怎么" packing "在一起。

![日志中的模型图像：PAE 图与逐链着色图](assets/Faster%20AlphaFold%20protein%20structure%20predictions%20using%20ColabFold/00458.webp)

所有结果（结构 + 图像）自动下载到本地，位置在 `Downloads/ChimeraX/AlphaFold/prediction_*/`（作者已经攒了 42 个 prediction 文件夹）；其中 `coverage.png` 就是前面那张覆盖图，可以直接放进组会 PPT [【跳转到 08:25】](https://www.youtube.com/watch?v=gIbCAcMDM7E&t=505)。

![输出目录中的 coverage.png 等图像文件](assets/Faster%20AlphaFold%20protein%20structure%20predictions%20using%20ColabFold/00530.webp)

在 ChimeraX 里还可以继续做后续分析：改显示风格、查看原子、点 AlphaFold 面板右侧的 error plot 按钮调出 PAE 图 [【跳转到 09:12】](https://www.youtube.com/watch?v=gIbCAcMDM7E&t=552)。最后是版本提醒：ChimeraX 1.3（一年前）只能预测单链，**复合物预测请用 1.4 及以上或 daily build** [【跳转到 09:37】](https://www.youtube.com/watch?v=gIbCAcMDM7E&t=577)。

## 小结

- ColabFold 的提速来自两处：**极快的 MSA 搜索服务器** + 优化过的 AlphaFold 代码；ChimeraX 把它做成了 `Tools → Structure Prediction → AlphaFold` 的一键体验；
- 结构预测的前置步骤是 **MSA 搜索**：拿输入序列去数据库找同源序列、拼成多序列比对（本系列术语上对应 A3M 格式，见 2.3.2）；
- **序列覆盖图是 MSA 搜索质量的"体检报告"**：黑曲线看覆盖、颜色看一致性、绿色成对条带看同物种配对——三者兼备，预测才可信；
- 复合物预测时，**同物种配对序列**是界面摆对的前提；
- 五个模型 + PAE 图是标准输出；PAE 图看链间相对位置可信度，pLDDT 着色看局部置信度。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| MSA（多序列比对） | 把输入序列与一堆同源序列按列对齐排成的矩阵，AlphaFold 的核心输入 |
| MSA Search | 预测流水线的第一步：在序列数据库中搜同源序列并生成比对；ColabFold 用专门服务器把它做得极快 |
| 序列覆盖图（coverage plot） | 可视化 MSA 搜索结果：黑线=各位点覆盖数，横线=每条序列的覆盖范围，颜色=序列一致性 |
| 配对序列（paired sequences） | 来自同一物种、分别对应复合物中两条链的同源序列；对界面预测至关重要 |
| 序列一致性（sequence identity） | 两条序列相同残基的比例；覆盖图里用颜色表示（红低蓝高） |
| PAE（Predicted Aligned Error） | 预测对齐误差：模型对"两个残基间相对摆放"误差的估计，看复合物界面可不可信 |
| pLDDT | 逐残基置信度（0-100），结构图上蓝=高、红=低 |
| ChimeraX | UCSF 的分子可视化软件，1.4 起内置 ColabFold 一键预测 |
