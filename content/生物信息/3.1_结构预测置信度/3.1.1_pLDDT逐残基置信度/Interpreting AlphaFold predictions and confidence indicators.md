# 解读 AlphaFold 预测结果：pLDDT 等置信度指标怎么看

> 来源视频：[Interpreting AlphaFold predictions and confidence indicators（the bumbling biochemist）](https://www.youtube.com/watch?v=i_aou7FRySw) · 时长 6:24
> 本篇基于视频 AI 字幕与画面整理，时间戳可跳转回原视频对应位置。

## 本讲要解决的核心问题（SCQA）

**背景**：AlphaFold 能用人工智能预测蛋白质（及蛋白质复合物）的三维结构，屏幕上转着的模型看上去"就像真的"。

**冲突**：但它终究只是**预测**。模型不会告诉你"我这里其实没把握"——如果不看置信度，你可能把一段模型自己都没信心的无序区当成真实结构拿去做下游分析。

**疑问**：有没有一套量化的办法，告诉我"结构的哪些部分可信、整体可不可信、两个残基的相对位置可不可信"？

**回答（中心思想）**：AlphaFold 在给出结构的同时给出三份"自信报告"——**pLDDT（逐残基，0–100）、pTM / ipTM（整体，0–1）、PAE（残基对相对位置，单位 Å）**。三个层面各管一件事：残基看 pLDDT，整体看 pTM/ipTM，两两关系看 PAE。

---

## 一、预测之外的三份"自信报告"

AlphaFold 的结果里，置信度按**三个层级**给出 [【跳转到 00:00】](https://www.youtube.com/watch?v=i_aou7FRySw&t=0)：

- **逐残基层级**：每个氨基酸（或核酸）残基一个分数；
- **整体层级**：整个结构一个分数；
- **残基对层级**：每两个残基之间的相对位置关系一个分数——它告诉你分子的堆积（packing）和复合物中各亚基的相对取向有多可信。

这三层分别对应三个数值 [【跳转到 00:39】](https://www.youtube.com/watch?v=i_aou7FRySw&t=39)：

| 指标 | 管什么 | 直觉读法 |
| --- | --- | --- |
| **pLDDT** | 逐残基置信度 | 结构着色的依据：深蓝好，橙差 |
| **PAE**（predicted aligned error） | 残基对之间的相对位置 | 热图：深绿好，浅绿差 |
| **pTM / ipTM** | 整个结构（/界面）的置信度 | 显示在图上方，越接近 1 越好 |

![AlphaFold 结果页三大指标：pLDDT 着色的结构、PAE 热图、上方的 pTM/ipTM 数值](assets/Interpreting%20AlphaFold%20predictions%20and%20confidence%20indicators/00039.webp)

下面逐个展开。

---

## 二、pLDDT：逐残基置信度（0–100）

### 2.1 它是什么、怎么看

pLDDT 是**残基层级**的置信度分数，也是结构默认的着色依据 [【跳转到 01:14】](https://www.youtube.com/watch?v=i_aou7FRySw&t=74)：

![结构按 pLDDT 着色：高置信区呈深蓝，低置信区呈橙色](assets/Interpreting%20AlphaFold%20predictions%20and%20confidence%20indicators/00079.webp)

- **高置信 → 深蓝**；
- **低置信 → 橙色**。

橙色（低置信）区域经常对应两类东西：**loop 区**（环区），或者**内在无序区（intrinsically disordered regions, IDR）**——本来就没有唯一稳定构象的区段 [【跳转到 01:19】](https://www.youtube.com/watch?v=i_aou7FRySw&t=79)。

一个非常常见的现象：即便一个结构大部分区域都是高置信的深蓝，**末端（N 端 / C 端）也常常是橙色**——末端残基的预测置信度天然偏低。

### 2.2 pLDDT 存在文件的 B-factor 字段里

这些逐残基数值会被保存在结构文件的 **B-factor 字段** [【跳转到 01:44】](https://www.youtube.com/watch?v=i_aou7FRySw&t=104)。所以在 PyMOL 里打开 AlphaFold 的结构文件后，**按 B-factor 着色，就等于按 pLDDT 着色**。

> 这也解释了 [B-factor 那一讲](../../2.2_结构类格式/2.2.3_链ID_auth_asym_id_残基编号_B-factor/What%20Are%20B-Factors？%20Understanding%20Protein%20Flexibility%20in%20X-Ray%20Crystallography.md)提到的现象：实验结构里 B-factor 反映晶体学柔性，而 AlphaFold 预测结构里 B-factor 列装的就是 pLDDT。

一个小坑：在 PyMOL 命令行里要输入 `spectrum b, red_blue` 才能得到和网页一致的配色——因为 PyMOL 里 B-factor 的**标尺方向是反的**（默认红高蓝低，而 pLDDT 习惯蓝高红低）[【跳转到 01:44】](https://www.youtube.com/watch?v=i_aou7FRySw&t=104)。

![pLDDT 保存在 B-factor 字段，PyMOL 中按 B 因子着色即可复现配色](assets/Interpreting%20AlphaFold%20predictions%20and%20confidence%20indicators/00104.webp)

---

## 三、pTM / ipTM：整体（与界面）置信度

看完了残基层级，再看**整体**。一个直观判断：整体更"蓝"的结构，整体置信度更高 [【跳转到 02:09】](https://www.youtube.com/watch?v=i_aou7FRySw&t=129)。

![两个结构对比：整体更蓝的那个整体置信度更高](assets/Interpreting%20AlphaFold%20predictions%20and%20confidence%20indicators/00129.webp)

这个整体置信度就落在 **ipTM 和 pTM** 两个数上 [【跳转到 02:22】](https://www.youtube.com/watch?v=i_aou7FRySw&t=142)：

- **pTM**（predicted template modeling score）：对**整个结构**的置信度度量；
- **ipTM**（interface pTM）：**界面版** pTM，度量复合物中**链与链之间**的相对位置的置信度。

读法一句话：**越接近 1 越好**。

![pTM 与 ipTM 数值：越接近 1 越可信](assets/Interpreting%20AlphaFold%20predictions%20and%20confidence%20indicators/00142.webp)

视频给出的经验分界线 [【跳转到 02:22】](https://www.youtube.com/watch?v=i_aou7FRySw&t=142)：

| pTM / ipTM 范围 | 怎么对待 |
| --- | --- |
| > 0.8 | 很好，可信 |
| 0.6 – 0.8 | **谨慎使用**（use with caution） |
| < 0.6 | 基本可以当作失败 |
| 短序列 | 例外：序列很短时分数天然偏低，不适用上述判据 |

视频中示例结构的分数非常接近 1，属于"整体高置信"的结构——但仍要记住那句 caveat：橙色区域（低置信部分）另当别论 [【跳转到 02:47】](https://www.youtube.com/watch?v=i_aou7FRySw&t=167)。

---

## 四、PAE：残基对之间"相对位置"的置信度

### 4.1 它回答什么问题

pLDDT 说的是"**这个残基本身**预测得准不准"，但它不回答"**两个残基之间**的相对摆放准不准"——这就是 PAE（predicted aligned error）的职责 [【跳转到 03:07】](https://www.youtube.com/watch?v=i_aou7FRySw&t=187)：

![PAE 热图：深绿代表相对位置可信，浅绿代表存疑](assets/Interpreting%20AlphaFold%20predictions%20and%20confidence%20indicators/00187.webp)

- PAE 度量**两个残基相对位置**的置信度，是"结构域的堆积与相对摆放是否准确"的指标；
- **深绿 = 好**，**浅绿 = 不好**。

### 4.2 怎么读这张图

PAE 图是**交互式**的：X、Y 两个轴都是残基编号 [【跳转到 03:32】](https://www.youtube.com/watch?v=i_aou7FRySw&t=212)。

![PAE 图的 X/Y 轴是残基编号，可交互查询任意两个残基](assets/Interpreting%20AlphaFold%20predictions%20and%20confidence%20indicators/00212.webp)

- 选中"位置 A × 位置 B"这个格子：若落在白色/浅绿区域，说明**模型对这两个位置的相对关系没把握**。视频里演示了比较相距很远的两个位置（第 222 位与第 333 位），它们交叉的格子颜色很浅——不太可信 [【跳转到 03:32】](https://www.youtube.com/watch?v=i_aou7FRySw&t=212)；
- 反过来，**越靠近轴的位置对**（编号相近、挨得近的残基），格子越深绿——它们之间的相对关系更可信 [【跳转到 03:57】](https://www.youtube.com/watch?v=i_aou7FRySw&t=237)；
- **对角线永远是深的**：对角线是残基和自己比，误差自然接近 0 [【跳转到 04:22】](https://www.youtube.com/watch?v=i_aou7FRySw&t=262)。

即便是一个整体预测得很差的结构，对角线也照样是深色——读图时要排除对角线本身。

### 4.3 不止看链内，还能看链间

PAE 能看出两件事 [【跳转到 04:22】](https://www.youtube.com/watch?v=i_aou7FRySw&t=262)：

1. **一条链内部**各结构域之间的相对摆位是否可信；
2. **复合物中不同亚基之间**的相对摆位是否可信。打开 **Display Chain Borders**（显示链边界）后，可以在图上区分 RNA 链与蛋白质链，然后做同样的两两比较——结构越可信的区对，格子越深绿。

![打开链边界显示后，可区分 RNA 与蛋白质链并比较亚基间相对位置](assets/Interpreting%20AlphaFold%20predictions%20and%20confidence%20indicators/00262.webp)

### 4.4 数值单位：Å（埃）

PAE 的数值单位是**埃（angstrom, Å）**，1 Å = 0.1 纳米 [【跳转到 04:47】](https://www.youtube.com/watch?v=i_aou7FRySw&t=287)。它的含义是：**预测结构与理论"真实"结构之间的误差**——

- 数值越小越好，颜色也越深绿；
- 浅绿区域意味着相对位置可能有不确定性 [【跳转到 05:12】](https://www.youtube.com/watch?v=i_aou7FRySw&t=312)。

浅绿不一定是"模型烂"，常见原因有三类 [【跳转到 05:12】](https://www.youtube.com/watch?v=i_aou7FRySw&t=312)：

1. 模型本身不够好、数据不足；
2. 或者——这个区域**本来就柔性大、动态强**，压根**不存在唯一的"正确结构"**（quote-unquote "right structure"）。软件总得给你一个答案，于是它给你的只是一个代表构象 [【跳转到 05:37】](https://www.youtube.com/watch?v=i_aou7FRySw&t=337)。

---

## 五、结果包里的 5 个模型：0 号最优

AlphaFold Server 的预测结果下载下来是一个 **zip 压缩包**，里面通常给出**五个不同的结构** [【跳转到 05:46】](https://www.youtube.com/watch?v=i_aou7FRySw&t=346)：

![AlphaFold Server 下载包：.cif 是结构文件，编号 0–4，0 号置信度最高](assets/Interpreting%20AlphaFold%20predictions%20and%20confidence%20indicators/00346.webp)

- 文件里真正装着结构的是那几个 **`.cif` 文件**；
- 文件名末尾的编号 **0 1 2 3 4**：**0 号置信度最高，4 号最低**；
- 想要更多构象可以**反复运行**，多次结果应当收敛到最可能正确的那一个结构 [【跳转到 06:11】](https://www.youtube.com/watch?v=i_aou7FRySw&t=371)。

> 顺带一提：[AF3 结果解读那篇](Alphafold3输出的结果文件数据解读及复合体预测流程.md)讲的"AlphaFold3 生成 5 个构象、model_0 是最佳构象"，对应的正是同一件事。

---

## 小结

- AlphaFold 的置信度分三层：**逐残基 pLDDT、整体 pTM/ipTM、残基对 PAE**——各管一件事，读结果时三个都看。
- **pLDDT（0–100）**是结构着色依据：深蓝高置信、橙色低置信；橙色常是 loop 或内在无序区，末端几乎总是偏低。
- pLDDT 存在**B-factor 字段**里；PyMOL 里用 `spectrum b, red_blue` 按 B 因子着色即可复现（注意刻度方向与网页相反）。
- **pTM / ipTM 越接近 1 越好**：>0.8 很好，0.6–0.8 谨慎，<0.6 基本算失败（短序列例外）。
- **PAE** 单位是 Å，衡量两个残基相对位置的误差；对角线恒深绿，浅绿块提示域间/亚基间相对摆位不可信——可能因数据不足，也可能因该区域本身无唯一构象。
- 结果包有 **5 个模型**：`.cif` 是结构，**0 号置信度最高**，多次运行会收敛。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| pLDDT | 逐残基置信度分数（0–100），结构着色依据；存储于 B-factor 字段 |
| pTM | predicted template modeling score，整体结构置信度（0–1，越接近 1 越好） |
| ipTM | interface pTM，复合物界面的 pTM，衡量链间相对位置置信度 |
| PAE | predicted aligned error，残基对相对位置误差（Å），热图深绿好、浅绿差 |
| IDR | intrinsically disordered region，内在无序区，pLDDT 低分的常见原因 |
| B-factor | 结构文件中的温度因子列；在 AF 预测结构里装载的是 pLDDT |
| Å（埃） | 长度单位，1 Å = 0.1 nm，PAE 数值的单位 |
