# 从 mfold 到 RNAfold：同一条 mRNA 的 MFE 怎么读——ΔG 越负越稳定，但别跨工具硬比数字

> 来源视频：[Secondary structure prediction using mFOLD and Forna | mRNA structure forecast tools](https://www.youtube.com/watch?v=Ue2N0_Vud_w) · 时长 08:21
> 本篇基于视频 AI 字幕与画面整理，时间戳可跳转回原视频对应位置。

## 本讲要解决的核心问题（SCQA）

**背景**：手上有了一段 mRNA 序列（本视频用 NCBI 上铜绿假单胞菌的丙酮酸激酶基因，约 1.4 kb），想预测它的二级结构。老牌工具 **mfold** 与 **ViennaRNA 套件的 RNAfold web server** 都能做"最小自由能（MFE）折叠"，视频把两个服务器并排跑同一条序列。

**冲突**：两个工具干的是"同一份工作"，给出的数字却不一样——mfold 报 Structure 1 ΔG = **-664.30 kcal/mol**，RNAfold 报 MFE = **-645.70 kcal/mol**；而且 mfold 一次给出一整份按 ΔG 排序的**结构榜单**，RNAfold 给的是"MFE 结构 + 系综四个数"两种读法。初学者容易懵：到底该信哪个数？

**疑问**：mfold 的 ΔG 榜单怎么读？"越负越稳定"在这里怎么体现？两个工具的差异是什么、日常该怎么选？

**回答（中心思想）**：把 ΔG 当**稳定性标尺**读——榜单从上往下 ΔG 递增（-664.30 → -648.30），最顶上（最负）的就是最可能自发形成、最稳定的结构；mfold 与 RNAfold 的热力学参数与算法实现不同，**数值出现差异是正常现象，跨工具硬比数字没有意义**，真正要比较时应在同一工具内比较；日常用 RNAfold（图清晰、可按配对概率/位置熵着色），想看动态结构再上 **Forna**。

![任务起点：在 NCBI 检索铜绿假单胞菌的丙酮酸激酶基因](assets/Secondary%20structure%20prediction%20using%20mFOLD%20and%20Forna｜mRNA%20structure%20forecast%20tools/00026.webp)

---

## 一、任务起点：从 NCBI 拿一条 mRNA 序列

视频从获取序列讲起 [【跳转到 00:00】](https://www.youtube.com/watch?v=Ue2N0_Vud_w&t=0)：

1. 打开 **NCBI**（ncbi.nlm.nih.gov），搜索 *pyruvate kinase*（丙酮酸激酶）+ 物种 *Pseudomonas aeruginosa*（铜绿假单胞菌），并把数据库切换为 **Gene** [【跳转到 00:26】](https://www.youtube.com/watch?v=Ue2N0_Vud_w&t=26)；
2. 结果里第一条是**蛋白序列**，忽略；下一条才是**基因记录**（基因 ID、名称），点进去 [【跳转到 01:01】](https://www.youtube.com/watch?v=Ue2N0_Vud_w&t=61)；
3. 下载格式选 **FASTA 或 GenBank** 都可以（信息相同），在 FASTA 格式下复制**全部核苷酸序列**备用 [【跳转到 01:08】](https://www.youtube.com/watch?v=Ue2N0_Vud_w&t=68)。

![NCBI Gene 记录页：丙酮酸激酶基因与其功能注释](assets/Secondary%20structure%20prediction%20using%20mFOLD%20and%20Forna｜mRNA%20structure%20forecast%20tools/00061.webp)

## 二、mfold：从 1995 年运行至今的老牌 MFE 服务器

另一个标签页打开 **mfold**，网址是 **unafold.rna.albany.edu**（The mfold Web Server，现托管于 UNAFold）[【跳转到 01:43】](https://www.youtube.com/watch?v=Ue2N0_Vud_w&t=103)：

![mfold Web Server 首页：RNA/DNA 折叠表单与结构展示、自由能测定](assets/Secondary%20structure%20prediction%20using%20mFOLD%20and%20Forna｜mRNA%20structure%20forecast%20tools/00108.webp)

页面上能看到它的资历：**自 1995 年秋上线**（最初在华盛顿大学医学院），2000–2010 年间运行于伦斯勒理工学院（RPI），之后迁至 RNA 研究所网站；描述它的论文（2003 年 NAR web server 专刊）被引近三千次；页脚署名 **Michael Zuker & Nick Markham, 1995–2019**。应用列表里有：

- **RNA Folding Form**（RNA 折叠表单，本视频用这个）；
- **DNA Folding Form**（DNA 折叠表单）；
- **Structure Display and Free Energy Determination**（结构展示与自由能测定）。

操作三步 [【跳转到 02:12】](https://www.youtube.com/watch?v=Ue2N0_Vud_w&t=132)：填序列名（"pyruvate kinase of Pseudomonas aeruginosa"）→ 粘贴序列 → **Format Sequence** 格式化 → **Fold RNA** 提交折叠。

![RNA Folding Form：填序列名、粘贴序列后格式化提交](assets/Secondary%20structure%20prediction%20using%20mFOLD%20and%20Forna｜mRNA%20structure%20forecast%20tools/00146.webp)

视频同时并排打开了 **RNAfold web server**（rna.tbi.univie.ac.at，ViennaRNA 套件），把同一条 FASTA 序列粘进去点 Proceed——**两个服务器做的是同一份工作**：RNA 二级结构折叠预测、按自由能找最稳定结构 [【跳转到 02:38】](https://www.youtube.com/watch?v=Ue2N0_Vud_w&t=158)。

## 三、读 mfold 的结果：一份按 ΔG 排序的"结构榜单"

mfold 的结果页不是单一答案，而是一份**榜单** [【跳转到 03:20】](https://www.youtube.com/watch?v=Ue2N0_Vud_w&t=200)：

![mfold 结果页：按初始 ΔG 排序的结构榜单，Structure 1 为 -664.30 kcal/mol](assets/Secondary%20structure%20prediction%20using%20mFOLD%20and%20Forna｜mRNA%20structure%20forecast%20tools/00215.webp)

- **Structure 1: Initial ΔG = -664.30 kcal/mol** ← 最小吉布斯自由能
- Structure 2: -664.10 → Structure 3: -663.80 → ……一路递增
- **Structure 39: Initial ΔG = -648.30 kcal/mol**（视频翻到的靠后条目）[【跳转到 03:30】](https://www.youtube.com/watch?v=Ue2N0_Vud_w&t=210)

为什么"最负的"就是答案？视频用热力学概念点题 [【跳转到 03:35】](https://www.youtube.com/watch?v=Ue2N0_Vud_w&t=215)：**吉布斯自由能直接关系到过程能否自发进行——也就是稳定性**。折叠这一步，ΔG 越负越能自发发生、结构越稳定；所以 ΔG 最低的 Structure 1 就是最稳定的 mRNA 二级结构。榜单后面的条目 ΔG 逐渐升高，是"次稳定"的备选折叠（suboptimal structures）——这正是长序列 reality：稳定构象不止一个，mfold 把它们排给你看。

![榜单后段：Structure 39 的 ΔG 已升至 -648.30 kcal/mol](assets/Secondary%20structure%20prediction%20using%20mFOLD%20and%20Forna｜mRNA%20structure%20forecast%20tools/00210.webp)

结果可以按 **PNG、ct 文件**等格式打开查看 [【跳转到 04:00】](https://www.youtube.com/watch?v=Ue2N0_Vud_w&t=240)，页面还提供排序 ct、h-num/Q-num、log 等附加文件。

## 四、同一序列换 RNAfold：数字对得上吗？

RNAfold 对同一条序列给出的 MFE 结果 [【跳转到 04:54】](https://www.youtube.com/watch?v=Ue2N0_Vud_w&t=294)：

![RNAfold 结果页：MFE -645.70 kcal/mol；系综自由能 -665.10；频率 0.00%；多样性 390.13](assets/Secondary%20structure%20prediction%20using%20mFOLD%20and%20Forna｜mRNA%20structure%20forecast%20tools/00294.webp)

| 读数 | mfold | RNAfold |
| --- | --- | --- |
| 最优/MFE 结构 ΔG | -664.30 kcal/mol | **-645.70 kcal/mol** |
| 系综自由能 | —（榜单形式） | -665.10 kcal/mol |
| MFE 结构在系综中的频率 | — | **0.00%** |
| 系综多样性 | — | 390.13 |

三个观察值得记住：

1. **数值不完全一致**（-664.30 vs -645.70，相差约 19 kcal/mol）。两个工具的热力学参数与搜索实现并不完全相同，数值有差异是正常现象——**跨工具硬比 ΔG 没有意义，比较稳定性应在同一工具内进行**。
2. **长序列的系综读法变了**：约 1.4 kb 的序列，MFE 结构频率只有 **0.00%**、系综多样性高达 **390**——构象空间太大，最稳定结构也只占系综里微不足道的一角。（对比：姊妹篇里 74 nt 短序列的 MFE 结构频率是 17.57%。）
3. RNAfold 还给出**系综自由能 -665.10 kcal/mol**，比 MFE 更负——因为它汇总的是整个系综，不是单个结构。

## 五、怎么选：图的可读性决定日常工具

视频给出的日常经验很直白 [【跳转到 04:24】](https://www.youtube.com/watch?v=Ue2N0_Vud_w&t=264)：

- mfold 的结构图基本由**茎环（stem-loop）**构成，能看到发卡环、开口环等，但**清晰度欠佳**——"这就是我们平时不太用 mfold、而更多用 RNAfold web server 的原因"。

![mfold 的结构图：茎环结构可见但清晰度欠佳](assets/Secondary%20structure%20prediction%20using%20mFOLD%20and%20Forna｜mRNA%20structure%20forecast%20tools/00264.webp)

- RNAfold 的结果可以**按碱基配对概率着色**或**按位置熵着色**（随你选择），还能在交互图里切换 Plain Sequence / No Sequence [【跳转到 05:21】](https://www.youtube.com/watch?v=Ue2N0_Vud_w&t=321)；

![RNAfold 的交互式结构图与显示/着色选项](assets/Secondary%20structure%20prediction%20using%20mFOLD%20and%20Forna｜mRNA%20structure%20forecast%20tools/00346.webp)

- 两个工具预测的**结构本身也不完全相同**：视频对比发现 RNAfold 这版结构里环（loop）明显更多。讲者的解读是环多、配对多，与 mRNA 稳定性直接相关 [【跳转到 05:46】](https://www.youtube.com/watch?v=Ue2N0_Vud_w&t=346)。这正好说明：**结构预测是"模型 + 参数"的输出，不是唯一真理**——重要结论要交叉验证（这也正是这套笔记里"双路线互验"管线的动机）。
- 演示者最后还提到两个工具在**碱基配对规则**上的差异（此处自动字幕含混，细节存疑）。

另外一点实操提示：用**其它数据库**拿到的同一序列，也能得到同样的结构与结果——工具链相当灵活 [【跳转到 07:26】](https://www.youtube.com/watch?v=Ue2N0_Vud_w&t=446)。

## 六、Forna：让二级结构动起来

最后一个工具是 **Forna**（rna.tbi.univie.ac.at/forna）：它直接吃 RNAfold 的 MFE 结构文件，在网页里把二级结构画成**可以实时缩放、自动布局的动态图** [【跳转到 06:11】](https://www.youtube.com/watch?v=Ue2N0_Vud_w&t=371)。

![Forna：把 RNAfold 的 MFE 结构加载为可交互的动态图](assets/Secondary%20structure%20prediction%20using%20mFOLD%20and%20Forna｜mRNA%20structure%20forecast%20tools/00421.webp)

- 页面上有 **AddMolecule / Clear** 等控件，可加载或清空分子；
- 结构会"动"起来（力导向布局），放大缩小细看茎环——讲者称之"这就是 Forna 的魔力" [【跳转到 07:01】](https://www.youtube.com/watch?v=Ue2N0_Vud_w&t=421)；
- 顺带一提：RNAfold 结果页的图形输出里就有 **VIEW IN FORNA** 入口，两个工具是同一家族（ViennaRNA/TBI）的配套。

## 七、别忘了：ΔG 会随序列长度水涨船高

把两个视频放在一起看，还有一个容易踩的坑：

- 74 nt 的短示例序列：MFE ≈ **-28.90 kcal/mol**（姊妹篇的 RNAfold 实操）；
- 约 1.4 kb 的丙酮酸激酶基因：MFE ≈ **-645.70 kcal/mol**（本视频）。

**序列越长，可配对的位置越多，ΔG 总量自然越负**——所以"谁的 ΔG 更负"不能直接推出"谁的折叠更稳定"，跨序列比较要看单位长度的能量或专门的归一化指标。ΔG 的"越负越稳定"，只有在**同一条序列**的不同构象之间比较时才是严格成立的标尺（这正是 mfold 榜单的用法）。

---

## 小结

- 流程三步走：**NCBI 拿 FASTA 序列 → 提交 mfold / RNAfold → 读 ΔG**。
- mfold 给**按 ΔG 排序的结构榜单**：Structure 1 的 -664.30 kcal/mol 最负、最稳定；往下 ΔG 递增是次稳定备选。
- "**越负越稳定**"的热力学含义：吉布斯自由能越低，折叠越能自发发生——ΔG 是稳定性标尺。
- mfold 与 RNAfold 数值不同（-664.30 vs -645.70）属正常：**别跨工具比数字**，重要结论在同工具内比较或交叉验证。
- 长序列（约 1.4 kb）的 RNAfold 系综：MFE 结构频率 **0.00%**、多样性 **390**——构象爆炸，MFE 结构只是代表之一。
- 日常首选 RNAfold（图清晰、配对概率/位置熵着色）；想动态浏览结构用 **Forna**（直接加载 RNAfold 的 MFE 文件）。
- **ΔG 随序列长度变负**：跨序列比较稳定性不能只看 ΔG 总量。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| mfold / UNAFold | 1995 年上线的老牌 MFE 折叠服务器（unafold.rna.albany.edu），作者 Zuker & Markham |
| MFE（minimum free energy） | 最小自由能结构：热力学上最稳定的折叠，工具搜索的目标 |
| ΔG（kcal/mol） | 吉布斯自由能变化；对折叠而言**越负越稳定、越能自发形成** |
| 结构榜单（suboptimal structures） | mfold 把 ΔG 递增的多个备选折叠列成清单，Structure 1 最稳定 |
| 系综自由能 | 整个构象系综的自由能，不是单个结构的能量，可比 MFE 更负 |
| MFE 结构频率 | MFE 结构在系综中的占比；长序列可低至 0.00% |
| 系综多样性 | 系综内结构间的平均差异；本例 390，构象极其多样 |
| 碱基配对概率 / 位置熵 | RNAfold 的两种着色方案：配对把握 / 配对不确定性 |
| Forna | ViennaRNA/TBI 家族的动态结构可视化工具，力导向布局 |
| ct 文件 | 记录碱基配对的表格格式，mfold/RNAfold 都支持导出 |
| NCBI Gene | 基因数据库：检索基因记录并下载 FASTA/GenBank 序列 |
