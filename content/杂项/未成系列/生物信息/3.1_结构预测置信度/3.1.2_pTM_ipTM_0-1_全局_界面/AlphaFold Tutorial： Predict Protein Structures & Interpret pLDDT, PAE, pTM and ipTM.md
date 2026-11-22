# 从提交序列到读懂分数：AlphaFold Server 实操与四大置信度指标

> 来源视频：[AlphaFold Tutorial: Predict Protein Structures & Interpret pLDDT, PAE, pTM and ipTM](https://www.youtube.com/watch?v=cEJca3gMhbw) · 时长 6:24
> 本篇基于视频 AI 字幕与画面整理，时间戳可跳转回原视频对应位置。

## 本讲要解决的核心问题（SCQA）

**背景**：AlphaFold 能从氨基酸序列直接预测蛋白质的三维结构。与同源建模、折叠识别这类传统方法相比，它更快、也更准；网页版（AlphaFold Server）甚至不需要安装任何软件。

**冲突**：但"拿到模型"不等于"拿到可信的模型"。屏幕上转着的彩色结构不会自己告诉你哪一段是高置信的、哪一段是模型在"猜"；单链蛋白和多链复合物的"可信"又是两码事。

**疑问**：有没有一套统一的数字，能告诉我们"这个预测的每个位置可不可信、整体可不可信、链与链之间可不可信"？

**回答（中心思想）**：AlphaFold 结果页给了**四把尺子**——**pLDDT（逐残基，0–100）、PAE（残基对相对位置，热图）、pTM（整体折叠，0–1）、ipTM（链间界面，0–1，仅多链复合物）**。看单个位置用 pLDDT，看两两关系用 PAE，看整体折叠用 pTM，看链间界面用 ipTM。

---

## 一、五步拿到模型：AlphaFold Server 从输入到提交

AlphaFold 可以通过一个自动化服务器使用：它自动搜索模板并预测结构，**只需要一次点击**就能启动 [【跳转到 00:00】](https://www.youtube.com/watch?v=cEJca3gMhbw&t=0)。

### 1.1 输入：一条 FASTA 序列就够了

在搜索引擎里找到 AlphaFold 官网，唯一的必填输入就是**目标蛋白的氨基酸序列，且要用 FASTA 格式**（一种以 `>` 标识行开头、下面跟序列字母的纯文本格式，几乎所有预测工具的通用输入）[【跳转到 00:25】](https://www.youtube.com/watch?v=cEJca3gMhbw&t=25)：

![在 AlphaFold Server 输入框粘贴 FASTA 序列](assets/AlphaFold%20Tutorial： Predict%20Protein%20Structures%20%26%20Interpret%20pLDDT,%20PAE,%20pTM%20and%20ipTM/00025.webp)

两个容易忽略的点 [【跳转到 00:50】](https://www.youtube.com/watch?v=cEJca3gMhbw&t=50)：

- 下拉菜单里要**选择 protein**（分子类型）；
- 如果蛋白带**翻译后修饰（PTM, post-translational modification）**——比如磷酸化、糖基化这类蛋白合成之后才加上去的化学修饰——可以在这里一并指定。

### 1.2 seed：控制随机性的"骰子起点"

提交前还有一个 **seed** 参数 [【跳转到 01:14】](https://www.youtube.com/watch?v=cEJca3gMhbw&t=74)。seed 是一个起始数字，控制预测中的随机部分：换一个 seed，就换一次"掷骰子"，可能得到略有不同的模型——**差异通常出现在柔性大、本身不确定的区域**。

![seed 参数的作用：不同种子在柔性区可能给出不同模型](assets/AlphaFold%20Tutorial： Predict%20Protein%20Structures%20%26%20Interpret%20pLDDT,%20PAE,%20pTM%20and%20ipTM/00074.webp)

如果对模型不满意、或置信度分数偏低，可以启用 seed 选项让 AlphaFold 自动用不同 seed 多生成几个模型，可能得到更好的预测 [【跳转到 01:39】](https://www.youtube.com/watch?v=cEJca3gMhbw&t=99)。

### 1.3 提交、等待与查看

确认并提交任务后等几分钟 [【跳转到 01:50】](https://www.youtube.com/watch?v=cEJca3gMhbw&t=110)，模型就生成在界面里了。查看操作很直观：右键、左键、滚轮分别对应不同的旋转、平移、缩放 [【跳转到 02:05】](https://www.youtube.com/watch?v=cEJca3gMhbw&t=125)；要复制或下载结果，点下载按钮即可 [【跳转到 02:10】](https://www.youtube.com/watch?v=cEJca3gMhbw&t=130)。

显示选项（display options）还能自定义结构的呈现方式 [【跳转到 02:22】](https://www.youtube.com/watch?v=cEJca3gMhbw&t=142)——不过比"怎么好看"更重要的是接下来的问题：**这个模型到底可不可信？**

---

## 二、读结果先认识四把尺子

视频给出的答案：用**四个置信度指标**评估模型质量——pLDDT、ipTM、pTM、PAE [【跳转到 02:22】](https://www.youtube.com/watch?v=cEJca3gMhbw&t=142)。

| 指标 | 管什么 | 范围 | 好坏直觉 |
| --- | --- | --- | --- |
| **pLDDT** | 逐残基的位置置信度 | 0–100 | 越高越好，>90 高置信，<50 常为无序/柔性区 |
| **PAE** | 残基对之间的相对位置误差 | 热图（Å） | 深绿好，黄/红差 |
| **pTM** | 整体折叠的全局置信度 | 0–1 | 越接近 1 越好，>0.8 高置信 |
| **ipTM** | 链间界面的置信度（仅多链） | 0–1 | >0.8 界面高置信；单链没有这个数 |

下面逐个展开，先从最重要的 pLDDT 说起。

---

## 三、pLDDT：每个残基一个分（0–100）

**pLDDT 是最重要的置信度分数**，它衡量 AlphaFold 对**每个氨基酸残基预测位置**的把握 [【跳转到 02:52】](https://www.youtube.com/watch?v=cEJca3gMhbw&t=172)：

![pLDDT 定义幻灯片：逐残基置信度，0–100](assets/AlphaFold%20Tutorial： Predict%20Protein%20Structures%20%26%20Interpret%20pLDDT,%20PAE,%20pTM%20and%20ipTM/00172.webp)

阈值读法 [【跳转到 03:17】](https://www.youtube.com/watch?v=cEJca3gMhbw&t=197)：

- **> 90**：对该残基预测位置**非常有信心**；
- **< 50**：置信度低，**可能意味着固有无序区或高度柔性区域**——这些区域本来就没有唯一稳定的构象。

结构会按 pLDDT 着色：示例模型中大多数残基 pLDDT > 90，显示为蓝色（颜色标尺即每个残基的置信度）[【跳转到 03:35】](https://www.youtube.com/watch?v=cEJca3gMhbw&t=215)。

![pLDDT 颜色标尺：蓝色代表高置信残基](assets/AlphaFold%20Tutorial： Predict%20Protein%20Structures%20%26%20Interpret%20pLDDT,%20PAE,%20pTM%20and%20ipTM/00215.webp)

> pLDDT 只回答"每个残基本身摆得对不对"；残基与残基**之间**的相对位置对不对，要看下一个指标。

---

## 四、PAE：残基与残基之间的相对位置

**PAE（predicted aligned error，预测对齐误差）**衡量的不是单个残基，而是**蛋白不同部分之间的相对位置**有多可信 [【跳转到 03:52】](https://www.youtube.com/watch?v=cEJca3gMhbw&t=232)。

PAE 图的读法：

- **深绿色区域**：预测误差低，这些区域之间的相对位置**高置信**；
- **浅绿、黄、红区域**：预测误差更高、置信度更低。示例模型里没有黄色或红色区域，说明整体相对位置可信 [【跳转到 04:07】](https://www.youtube.com/watch?v=cEJca3gMhbw&t=247)。

![PAE 热图：颜色越深绿，两个残基间的相对位置越可信](assets/AlphaFold%20Tutorial： Predict%20Protein%20Structures%20%26%20Interpret%20pLDDT,%20PAE,%20pTM%20and%20ipTM/00232.webp)

坐标轴含义：**x 轴是被打分的残基，y 轴是作为对齐参考的残基** [【跳转到 04:32】](https://www.youtube.com/watch?v=cEJca3gMhbw&t=272)。

PAE 最有价值的用法是抓出这种"陷阱"：**两个结构域各自的 pLDDT 都 > 90，但 PAE 图显示它们之间低置信**——这说明每个域自身的结构预测得很好，**但两个域的相对朝向不确定** [【跳转到 04:32】](https://www.youtube.com/watch?v=cEJca3gMhbw&t=272)。

![两个域各自高置信、相对朝向却不确定的 PAE 示意](assets/AlphaFold%20Tutorial： Predict%20Protein%20Structures%20%26%20Interpret%20pLDDT,%20PAE,%20pTM%20and%20ipTM/00272.webp)

> pLDDT 和 PAE 都是"局部/成对"视角。想用一个数字概括**整体**结构可不可信，就该看 pTM 了。

---

## 五、pTM：整体折叠的全局置信度（0–1）

**pTM（predicted TM score，预测 TM 分数）**衡量 AlphaFold 对**预测蛋白整体结构**的置信度 [【跳转到 04:57】](https://www.youtube.com/watch?v=cEJca3gMhbw&t=297)：

![pTM 定义幻灯片：衡量整体结构的置信度](assets/AlphaFold%20Tutorial： Predict%20Protein%20Structures%20%26%20Interpret%20pLDDT,%20PAE,%20pTM%20and%20ipTM/00302.webp)

- 分数范围 **0 到 1**，越接近 1 越好；
- **> 0.8**：对整体折叠（overall fold）**高置信**；
- **0.6 – 0.8**：中等置信；
- **< 0.6**：整体结构需**谨慎解读** [【跳转到 05:02】](https://www.youtube.com/watch?v=cEJca3gMhbw&t=302)。

示例模型的 pTM 为 **0.98**，属于高置信 [【跳转到 05:27】](https://www.youtube.com/watch?v=cEJca3gMhbw&t=327)。

![本例模型 pTM = 0.98，整体折叠高置信](assets/AlphaFold%20Tutorial： Predict%20Protein%20Structures%20%26%20Interpret%20pLDDT,%20PAE,%20pTM%20and%20ipTM/00327.webp)

---

## 六、ipTM：链间界面的置信度（0–1，仅多链）

最后一个指标专为复合物而生：**ipTM（interface predicted TM score，界面预测 TM 分数）****只用于多链蛋白复合物**，衡量 AlphaFold 对**不同蛋白链之间预测界面**的置信度 [【跳转到 05:38】](https://www.youtube.com/watch?v=cEJca3gMhbw&t=338)：

![ipTM 定义幻灯片：多链复合物的界面置信度](assets/AlphaFold%20Tutorial： Predict%20Protein%20Structures%20%26%20Interpret%20pLDDT,%20PAE,%20pTM%20and%20ipTM/00347.webp)

- **> 0.8**：对预测界面**高置信** [【跳转到 05:47】](https://www.youtube.com/watch?v=cEJca3gMhbw&t=347)；
- 如果模型**只有一条链**，就没有 ipTM 这个分数——示例是单链模型，所以结果显示 ipTM 不可用 [【跳转到 06:09】](https://www.youtube.com/watch?v=cEJca3gMhbw&t=369)。

一句话记住它与 pTM 的分工：**pTM 管"各链整体摆得对不对"（全局），ipTM 管"链与链搭得牢不牢"（界面）**。

---

## 小结

- AlphaFold Server 用一条 FASTA 序列、一次点击即可完成预测；PTM 可指定，seed 控制随机性，不满意可换 seed 重跑。
- 四个置信度指标各管一层：**pLDDT 看残基（0–100，>90 高、<50 常为无序区），PAE 看残基对相对位置（深绿可信），pTM 看整体折叠（0–1，>0.8 高置信、<0.6 谨慎），ipTM 看链间界面（0–1，>0.8 高置信，仅多链）**。
- 最经典的"陷阱"是两域各自 pLDDT > 90 但 PAE 显示相对朝向低置信——**局部都对，拼起来未必对**。
- pTM 与 ipTM 都是 0–1 的 TM 分数家族：前者是全局视角，后者把同样的思想用在界面上；只有多链复合物才有 ipTM。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| FASTA | 以 `>` 开头、后跟序列字母的纯文本序列格式，预测工具的通用输入 |
| PTM（翻译后修饰） | 蛋白合成后加上去的化学修饰（如磷酸化），可在提交时指定 |
| seed | 控制预测随机性的起始数字；不同 seed 在柔性区可能给出略不同的模型 |
| pLDDT | 逐残基位置置信度，0–100；>90 高置信，<50 常提示无序/柔性区 |
| PAE | 残基对相对位置的预测误差热图；深绿可信，黄红差 |
| pTM | 整体折叠的全局置信度，0–1；>0.8 高置信，<0.6 需谨慎 |
| ipTM | 链间界面置信度，0–1；>0.8 高置信，仅多链复合物可用 |
| 固有无序区（IDR） | 本身没有唯一稳定构象的蛋白区段，预测分数天然偏低 |
