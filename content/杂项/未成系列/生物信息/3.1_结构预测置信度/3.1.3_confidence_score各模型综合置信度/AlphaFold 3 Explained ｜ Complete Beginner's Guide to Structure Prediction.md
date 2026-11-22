# AlphaFold 3 上手指南：从预测胰岛素到读懂 pLDDT、PAE 与 ipTM

> 来源视频：[AlphaFold 3 Explained | Complete Beginner's Guide to Structure Prediction](https://www.youtube.com/watch?v=NKJ11gOzQcM) · 时长 14:09
> 本篇基于视频 AI 字幕与画面整理（Biotecnika 出品），时间戳可跳转回原视频对应位置。

## 本讲要解决的核心问题（SCQA）

**背景**：AlphaFold Server 让结构预测变成了"网页上点几下"的事——不用装软件、不用写代码，粘贴序列就能拿到三维模型。

**冲突**：跑完预测，模型被涂上深蓝、浅蓝、黄、橙各种颜色，旁边还有一张 PAE 热图和 pTM / ipTM 分数。不知道这些数字和颜色各代表什么，模型再漂亮也不敢用。

**疑问**：这些颜色和分数分别衡量什么？阈值是多少？什么时候看哪个？

**回答（中心思想）**：**颜色就是逐残基的 pLDDT 置信度（0–100），PAE 矩阵是残基对之间相对位置的误差图，pTM / ipTM 是全局 / 界面的综合置信度（0–1）**。记住三条判读线——深蓝 >90 可用于对接与活性位点分析；PAE 矩阵亮区 = 模型自己也不确定；ipTM >0.8 相互作用质量高、<0.5 则不佳。

![AlphaFold 3：面向初学者的结构预测完全指南](assets/AlphaFold%203%20Explained%20｜%20Complete%20Beginner's%20Guide%20to%20Structure%20Prediction/00000.webp)

---

## 一、AlphaFold 3 是什么，比 AlphaFold 2 强在哪

AlphaFold 3 是谷歌 DeepMind 推出的最新突破性模型，用于预测生物结构，可以理解为 AlphaFold 2 的高级版本 [【跳转到 00:00】](https://www.youtube.com/watch?v=NKJ11gOzQcM&t=0)。它是一个能预测**完整生物分子复合物**的系统，准确度极高 [【跳转到 00:25】](https://www.youtube.com/watch?v=NKJ11gOzQcM&t=25)。

区别在哪里？AlphaFold 2 只能根据氨基酸序列预测**蛋白质**的三维结构；而 AlphaFold 3 能预测各种生物分子的结构 [【跳转到 00:50】](https://www.youtube.com/watch?v=NKJ11gOzQcM&t=50)：

![AlphaFold 3 的预测范围：从蛋白到各类复合物](assets/AlphaFold%203%20Explained%20｜%20Complete%20Beginner's%20Guide%20to%20Structure%20Prediction/00050.webp)

- DNA、RNA、小分子**配体**（ligand，与蛋白结合的小分子）；
- 带**翻译后修饰**（PTM）的蛋白质；
- **蛋白-蛋白相互作用**、**抗原-抗体**；
- **蛋白-核酸相互作用**复合物等。

---

## 二、AlphaFold Server 上手七步（人胰岛素演示）

### 2.1 打开页面并登录

谷歌搜索 "AlphaFold 3"，打开官方页面，点击"**使用 Google 继续**"用谷歌账号登录，页面即可正常打开 [【跳转到 01:15】](https://www.youtube.com/watch?v=NKJ11gOzQcM&t=75)。

### 2.2 添加实体与副本数

进入 AlphaFold 3 页面后，可以添加各类**实体**（entity）——蛋白质、DNA、RNA、配体、离子等，还可以设置该结构需要预测的**副本数量**（copies）[【跳转到 01:54】](https://www.youtube.com/watch?v=NKJ11gOzQcM&t=114)。

![AlphaFold Server：添加蛋白、DNA、RNA、配体、离子等实体](assets/AlphaFold%203%20Explained%20｜%20Complete%20Beginner's%20Guide%20to%20Structure%20Prediction/00114.webp)

### 2.3 输入序列：去 Uniprot 找

页面上的参数是 AlphaFold 已设置好的默认值，一般不用动。输入蛋白质序列有两条路：去 **Uniprot** 数据库找——蛋白序列都在那里；也可以用 **PDB** 数据库——但注意 PDB 文件里已经有实验解析的 3D 结构了 [【跳转到 02:19】](https://www.youtube.com/watch?v=NKJ11gOzQcM&t=139)。

本视频的演示目标是**人胰岛素**（human insulin）：它的序列已经确定，我们想预测其三维结构 [【跳转到 02:44】](https://www.youtube.com/watch?v=NKJ11gOzQcM&t=164)。

### 2.4 粘贴序列并提交作业

把人胰岛素的氨基酸序列复制粘贴进来，点"**继续预览作业**"，再确认提交 [【跳转到 03:09】](https://www.youtube.com/watch?v=NKJ11gOzQcM&t=189)。作业会进入队列，排在前面的可能还有其它任务，服务器按情况运行——**服务器空闲时作业很快执行**；一般来说等待 10 到 15 分钟比较常见，有时则很快出结果 [【跳转到 03:38】](https://www.youtube.com/watch?v=NKJ11gOzQcM&t=218)。

### 2.5 查看预测结果

作业结束后，AlphaFold 就为我们输入的氨基酸序列创建了 3D 结构，在页面右侧清晰可见——这就是人胰岛素蛋白的 3D 结构模型 [【跳转到 04:24】](https://www.youtube.com/watch?v=NKJ11gOzQcM&t=264)。

![预测完成：右侧给出人胰岛素的 3D 模型](assets/AlphaFold%203%20Explained%20｜%20Complete%20Beginner's%20Guide%20to%20Structure%20Prediction/00264.webp)

---

## 三、读懂颜色：pLDDT 四档置信度

模型上为什么有深蓝、浅蓝、黄、橙各种颜色 [【跳转到 04:47】](https://www.youtube.com/watch?v=NKJ11gOzQcM&t=287)？放大细看，可以看到图例列出了**四个置信度等级**：非常高（very high）、置信（confident）、低（low）、非常低（very low）的 pLDDT 评分 [【跳转到 05:24】](https://www.youtube.com/watch?v=NKJ11gOzQcM&t=324)。

**pLDDT**（predicted local distance difference test，预测局部距离差异检验）衡量的是：AlphaFold 对**每个原子位置及其直接相邻残基**有多大信心，分数范围 **0–100** [【跳转到 05:49】](https://www.youtube.com/watch?v=NKJ11gOzQcM&t=349)。

![pLDDT 四档颜色图例](assets/AlphaFold%203%20Explained%20｜%20Complete%20Beginner's%20Guide%20to%20Structure%20Prediction/00324.webp)

四档颜色怎么用 [【跳转到 06:14】](https://www.youtube.com/watch?v=NKJ11gOzQcM&t=374)：

- **深蓝色（>90，非常高）**：原子几乎肯定处在预期位置。这样的区域可用于**药物对接（docking）和活性位点分析**——蓝色区域通常就当作活性位点区域来用 [【跳转到 06:39】](https://www.youtube.com/watch?v=NKJ11gOzQcM&t=399)；
- **浅蓝色（70–90，置信）**：对骨架形状的预测基本可靠 [【跳转到 07:04】](https://www.youtube.com/watch?v=NKJ11gOzQcM&t=424)；
- **黄色（50–70，低）与橙色（<50，非常低）**：置信度不足 [【跳转到 07:29】](https://www.youtube.com/watch?v=NKJ11gOzQcM&t=449)。

![黄/橙区域：低置信，常对应天然无序的柔性区](assets/AlphaFold%203%20Explained%20｜%20Complete%20Beginner's%20Guide%20to%20Structure%20Prediction/00449.webp)

![深蓝区域：高置信，可用于对接与活性位点分析](assets/AlphaFold%203%20Explained%20｜%20Complete%20Beginner's%20Guide%20to%20Structure%20Prediction/00374.webp)

特别要注意：**黄橙色区域不是错误**——我们并不认为模型预测错了。它通常表示蛋白质的这一部分在真实世界中**天然无序**（intrinsically disordered），就像一段柔性的环（loop）——这正是这些区域 pLDDT 分数很低的原因 [【跳转到 07:54】](https://www.youtube.com/watch?v=NKJ11gOzQcM&t=474)。

## 四、读懂 PAE 矩阵：残基对之间的误差图

模型的旁边还有一张白绿相间的图——**PAE 矩阵**（predicted aligned error，预测对齐误差）。对于蛋白-配体、蛋白-DNA 这样的复合物，它同样适用 [【跳转到 08:41】](https://www.youtube.com/watch?v=NKJ11gOzQcM&t=521)。

![PAE 矩阵：白绿热图，x 轴 y 轴都是残基](assets/AlphaFold%203%20Explained%20｜%20Complete%20Beginner's%20Guide%20to%20Structure%20Prediction/00521.webp)

它本质上是一张**二维热图**：x 轴和 y 轴都以**残基**表示，对应分子（蛋白质或 DNA 等）的序列位置——无论是蛋白质还是 DNA，读法相同 [【跳转到 09:06】](https://www.youtube.com/watch?v=NKJ11gOzQcM&t=546)。两条判读要点 [【跳转到 09:31】](https://www.youtube.com/watch?v=NKJ11gOzQcM&t=571)：

- **对角线颜色总是很深**：每个残基与自身对齐的误差为零，颜色越深表示误差越小；
- **较亮的区域 = 高误差**：模型不知道这些部分之间有什么关联——它们可能是柔性的，或互不相关 [【跳转到 09:56】](https://www.youtube.com/watch?v=NKJ11gOzQcM&t=596)。

## 五、pTM 与 ipTM：整体与界面的综合分数

输出里还能看到一个叫做 **ipTM** 的东西，以及 **pTM** [【跳转到 10:21】](https://www.youtube.com/watch?v=NKJ11gOzQcM&t=621)。二者的分工：

- 如果预测的是**单独一条链**（只有结构本身、没有相互作用对象），显示的是正常的 **pTM**；
- 如果预测的是**复合物**，分数就会显示为 **ipTM** [【跳转到 10:46】](https://www.youtube.com/watch?v=NKJ11gOzQcM&t=646)。

![输出中的 pTM 与 ipTM 分数区](assets/AlphaFold%203%20Explained%20｜%20Complete%20Beginner's%20Guide%20to%20Structure%20Prediction/00621.webp)

ipTM 基本上就是"预测的模板建模得分"（predicted TM score）的**界面（interface）版本**：一个从 **0 到 1** 的分数，衡量蛋白质之间——以及配体、蛋白质与 DNA 之间——**界面的预测准确性** [【跳转到 10:46】](https://www.youtube.com/watch?v=NKJ11gOzQcM&t=646)。

判读阈值 [【跳转到 11:11】](https://www.youtube.com/watch?v=NKJ11gOzQcM&t=671)：

- **ipTM > 0.8**：相互作用的质量很高；
- **ipTM < 0.5**：相互作用的预测质量不佳。

## 六、进阶：蛋白-配体复合物预测（胰岛素 + ATP）

### 6.1 下载结果

结果页有下载选项，可以下载 **PDB 文件和设置文件**，转换后可在 **PyMOL** 等分子可视化软件中打开查看 [【跳转到 11:24】](https://www.youtube.com/watch?v=NKJ11gOzQcM&t=684)。这就是 AlphaFold 3 预测蛋白结构的完整流程 [【跳转到 11:47】](https://www.youtube.com/watch?v=NKJ11gOzQcM&t=707)。

### 6.2 复合物演示：还是胰岛素，但加上 ATP

在刚才人胰岛素的基础上添加一种**配体**——**ATP**：蛋白质和配体将如何相互作用、如何结合？选择 ATP 作为配体后提交，预测结果的展示方式与之前讲解的完全一致 [【跳转到 12:04】](https://www.youtube.com/watch?v=NKJ11gOzQcM&t=724)。

![蛋白-配体演示：胰岛素 + ATP](assets/AlphaFold%203%20Explained%20｜%20Complete%20Beginner's%20Guide%20to%20Structure%20Prediction/00724.webp)

我刚才只解释了蛋白质部分；对于复合物中的蛋白质-配体，其工作方式也相同——**PAE 矩阵同样以相同方式运作**，背后的理论不变 [【跳转到 12:29】](https://www.youtube.com/watch?v=NKJ11gOzQcM&t=749)。唯一的区别是图例中同时包含蛋白质和配体；正如前面所提醒的，**配体连接到蛋白质时，我们得到的就是 ipTM 分数** [【跳转到 12:43】](https://www.youtube.com/watch?v=NKJ11gOzQcM&t=763)。

![复合物输出：图例含蛋白与配体，显示 ipTM](assets/AlphaFold%203%20Explained%20｜%20Complete%20Beginner's%20Guide%20to%20Structure%20Prediction/00763.webp)

### 6.3 再提交一次：实体自由组合

回到 AlphaFold 页面，再次输入胰岛素序列，选择"添加实体"——可以是蛋白质，也可以选择 DNA 或**配体（ligand）**，有多种实体可以与蛋白质搭配，再走一遍"继续预览 → 确认提交"，等作业结束即可得到输出 [【跳转到 13:04】](https://www.youtube.com/watch?v=NKJ11gOzQcM&t=784)。

---

## 小结

- **AlphaFold 3 = AlphaFold 2 的高级版**：从"只能预测蛋白"扩展到 DNA、RNA、配体、翻译后修饰、蛋白-蛋白、抗原-抗体与蛋白-核酸复合物。
- **Server 七步**：谷歌搜 AlphaFold 3 → Google 登录 → 添加实体与副本数 → 从 Uniprot 取序列粘贴 → 继续预览 → 确认提交 → 等队列出结果（常见 10–15 分钟，空闲时更快）。
- **颜色 = pLDDT（0–100，逐原子位置信心）**：深蓝 >90 可用于对接与活性位点分析；浅蓝 70–90 骨架基本可靠；黄 50–70、橙 <50 置信不足——但**不是错误**，往往是天然无序/柔性环。
- **PAE 矩阵**：对角线深是正常现象（残基与自身对齐零误差）；亮区 = 高误差 = 模型对这两段的相对摆放没把握。
- **pTM / ipTM（0–1）**：单链看 pTM；复合物（含配体）看 ipTM——**>0.8 高质量，<0.5 不佳**。
- 结果可下载 PDB/设置文件，用 PyMOL 查看与后续分析。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| pLDDT | 预测局部距离差异检验：对每个原子位置及其相邻残基的信心，0–100；深蓝>90、浅蓝70–90、黄50–70、橙<50 |
| PAE | 预测对齐误差矩阵：残基对之间的相对位置误差；亮区=高误差=模型不确定 |
| pTM | 预测模板建模得分：单链全局置信度，0–1 |
| ipTM | 界面版 pTM：复合物/含配体时链间界面的置信度，0–1；>0.8 高、<0.5 差 |
| 实体（entity） | Server 中添加的预测对象：蛋白质、DNA、RNA、配体、离子 |
| 副本（copies） | 需要预测的结构副本数量 |
| Uniprot | 蛋白质序列数据库，取输入序列的常用来源 |
| PyMOL | 常用分子可视化软件，可打开下载的 PDB 文件 |

