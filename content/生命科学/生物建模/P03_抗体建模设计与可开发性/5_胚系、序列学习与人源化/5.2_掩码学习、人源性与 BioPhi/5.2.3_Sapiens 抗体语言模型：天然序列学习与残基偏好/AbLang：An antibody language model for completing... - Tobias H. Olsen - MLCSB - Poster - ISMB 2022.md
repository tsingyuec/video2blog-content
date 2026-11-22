# AbLang：为抗体专训的语言模型，把缺失的抗体序列「补」回来

> 来源：YouTube 视频《AbLang: An antibody language model for completing... - Tobias H. Olsen - MLCSB - Poster - ISMB 2022》（官方频道：ISCB 国际计算生物学会，[MTbKfGM3aYM](https://www.youtube.com/watch?v=MTbKfGM3aYM)，时长 07:08，2023-01-27 发布；ISMB 2022 会议海报报告）。
> 本文基于视频字幕与画面逐窗口整理而成，配图取自视频截图，时间戳可跳回原视频对应位置核对。
> 导读：讲者是 AbLang 一作 Tobias H. Olsen（牛津蛋白质信息学组 OPIG，受 Charlotte Deane 指导，GSK 方合作者 Iain Moal）——这是 ABDP 平台底座模型 AbLang 的作者亲讲。本篇回答三个问题：抗体为什么值得一个专属语言模型？AbLang 怎么训练、怎么用？它最实用的能力——补全缺失残基——效果如何？

## 本讲要解决的核心问题（SCQA）

**背景**：抗体是 Y 形蛋白质，由两条重链和两条轻链组成；顶端的可变区里藏着结合位点。可变区多样性极高，因此抗体几乎能结合任何类型的病原——这让抗体成为极其重要的一类治疗药物。

**冲突**：极端多样性反过来成了工程难题——很难搞清哪一支抗体真正结合你的特定靶标，于是产生了大量计算工具来预测抗体性质。可这些工具所依赖的 OAS（Observed Antibody Space）数据库里，**大多数序列缺失 N 端一整段，约 1% 的序列还带有模糊残基**。常规补救办法要么直接丢弃这些数据，要么用种系（germline）序列回填——但种系不一定已知，预测种系又可能出问题。

**疑问**：能不能专门为抗体训练一个语言模型，既帮我们理解抗体的「语义」，又顺手把缺失的残基补全？

**回答（中心思想）**：AbLang 证明可以。它在 OAS 数百万条无标注抗体序列上做 BERT 式掩码预训练；补全缺失残基时，成绩与种系法相当、随机缺失场景下更好，明显优于通用蛋白质语言模型 ESM-1B；面对「不知道缺多长」的问题，它还能用首位残基的预测似然推断抗体序列全长。抗体特有问题，就该用抗体专属语言模型。

## 一、为什么抗体要一个专属语言模型

[【跳转到 00:22】](https://www.youtube.com/watch?v=MTbKfGM3aYM&t=22)

先看对象本身：抗体由两条重链和两条轻链组成（图中红色为轻链），顶端可变区携带结合位点。可变区的极度多样性让抗体能广谱结合病原，也因此成为重要的治疗药物。

![报告开场讲解抗体结构时的画面](assets/AbLang：An%20antibody%20language%20model%20for%20completing...%20-%20Tobias%20H.%20Olsen%20-%20MLCSB%20-%20Poster%20-%20ISMB%202022/00022.webp)

[【跳转到 00:47】](https://www.youtube.com/watch?v=MTbKfGM3aYM&t=47)

但多样性也带来困难：很难确定哪支抗体结合你的靶标。为此学界造了大量计算工具来预测抗体的各种性质。AbLang 的定位就是支撑这类工具——一个**抗体专属**的语言模型，帮助我们理解抗体的「语义」。

## 二、AbLang 怎么训练、怎么用

### 2.1 训练：BERT 式掩码预训练 + OAS 海量数据

[【跳转到 01:12】](https://www.youtube.com/watch?v=MTbKfGM3aYM&t=72)

AbLang 是一个 **BERT 启发**的语言模型，训练数据来自 Observed Antibody Space（OAS）的庞大数据量。预训练（pre-training）的做法：在数百万条**无标注**抗体序列上，随机遮住整条序列中的一组残基，让模型预测这些被遮的残基——模型由此学会「根据序列其余部分预测每个位置」，进而掌握抗体的「语义」（掩码预训练的一般原理见本系列 4.2.1）。

![讲解 OAS 数据与掩码预训练时的画面](assets/AbLang：An%20antibody%20language%20model%20for%20completing...%20-%20Tobias%20H.%20Olsen%20-%20MLCSB%20-%20Poster%20-%20ISMB%202022/00097.webp)

### 2.2 三种用法：残基级、序列级、氨基酸似然

[【跳转到 02:02】](https://www.youtube.com/watch?v=MTbKfGM3aYM&t=122)

预训练学到的信息编码在模型末端的隐空间——**残基编码（residue encodings）**里。报告给出三种用法：

1. **逐残基预测**：直接取每个残基的编码，做残基级别的任务；
2. **序列级预测**：把残基编码取平均（average pooling），得到整条序列的表示；
3. **氨基酸似然**：保留输出头，用输出似然做「某个位置最可能是哪个氨基酸」的预测。

## 三、用例：补全缺失残基

### 3.1 问题：OAS 里的序列天生「缺角」

[【跳转到 02:57】](https://www.youtube.com/watch?v=MTbKfGM3aYM&t=177)

翻看 OAS 里的每条序列可以发现：**大多数序列缺失 N 端一大段**，还有约 1% 的序列在中间带至少一个模糊残基。常规处理：要么丢弃数据，要么用种系（germline）序列恢复。种系法的麻烦在于：你要么得知道对应的种系（不总是知道），要么得先预测种系（可能出问题）。

![讲解 OAS 序列缺失 N 端问题时的画面](assets/AbLang：An%20antibody%20language%20model%20for%20completing...%20-%20Tobias%20H.%20Olsen%20-%20MLCSB%20-%20Poster%20-%20ISMB%202022/00177.webp)

### 3.2 AbLang 的做法：取似然最高的氨基酸填补

[【跳转到 03:47】](https://www.youtube.com/watch?v=MTbKfGM3aYM&t=227)

换用语言模型（如 AbLang）：把带缺失残基的序列直接喂进去，看缺失位置上各氨基酸的似然，**取似然最高的那个氨基酸填补**。报告称这一思路效果相当好。

![讲解用 AbLang 填补缺失残基时的画面](assets/AbLang：An%20antibody%20language%20model%20for%20completing...%20-%20Tobias%20H.%20Olsen%20-%20MLCSB%20-%20Poster%20-%20ISMB%202022/00227.webp)

## 四、效果：与种系法、ESM-1B 同台比较

[【跳转到 04:03】](https://www.youtube.com/watch?v=MTbKfGM3aYM&t=243)

对比对象：种系法，以及当时最先进的**通用**蛋白质语言模型 ESM-1B。

- **补 N 端最多 30 个缺失残基**：通用模型表现挣扎很多（视频说这也符合预期），AbLang 与种系法相当；
- **随机缺失 1–10 个残基**：AbLang 更胜一筹。

![AbLang 与种系法、ESM-1B 补全效果对比的图表](assets/AbLang：An%20antibody%20language%20model%20for%20completing...%20-%20Tobias%20H.%20Olsen%20-%20MLCSB%20-%20Poster%20-%20ISMB%202022/00243.webp)

## 五、缺多长不知道？让似然告诉你

### 5.1 首位残基似然 → 序列全长

[【跳转到 04:53】](https://www.youtube.com/watch?v=MTbKfGM3aYM&t=293)

补 N 端有个隐含假设：三种方法都默认「知道缺了几个残基」，可现实中并不知道。AbLang 的解法：**用首个残基的预测似然来确定抗体序列的全长**——先推断该补多长，再补。

### 5.2 与标准编号方法对比

[【跳转到 05:18】](https://www.youtube.com/watch?v=MTbKfGM3aYM&t=318)

在「正确预测该补多少个残基」这件事上，与标准做法（ANARCI 这类抗体序列编号方法）相比，AbLang 相当或更好。

![AbLang 预测缺失长度与编号方法对比的图表](assets/AbLang：An%20antibody%20language%20model%20for%20completing...%20-%20Tobias%20H.%20Olsen%20-%20MLCSB%20-%20Poster%20-%20ISMB%202022/00318.webp)

### 5.3 迭代恢复：ANARCI → AbLang → AbLang

[【跳转到 05:43】](https://www.youtube.com/watch?v=MTbKfGM3aYM&t=343)

一个进阶技巧：先用 ANARCI 恢复一次、再用 AbLang 恢复，然后用 AbLang **再恢复第二次**——性能反而进一步提升。这种改善在重链较长的缺失区域尤其明显。

## 六、结论

[【跳转到 06:14】](https://www.youtube.com/watch?v=MTbKfGM3aYM&t=374)

报告收尾三点：

1. OAS 的海量数据让**训练抗体专属语言模型**成为可能；
2. AbLang 补全残基胜过种系基线与通用蛋白质语言模型；
3. 这证明了：抗体特异的问题，用抗体专属的语言模型是合理路线。

![报告结论页](assets/AbLang：An%20antibody%20language%20model%20for%20completing...%20-%20Tobias%20H.%20Olsen%20-%20MLCSB%20-%20Poster%20-%20ISMB%202022/00374.webp)

## 小结

- 抗体的价值与难点同源：可变区极度多样 → 广谱结合 → 难以定向，于是需要计算工具。
- AbLang = BERT 式掩码预训练 + OAS 数百万无标注抗体序列；编码可分别支持残基级、序列级、氨基酸似然三类任务。
- OAS 序列普遍缺 N 端、约 1% 带模糊残基；种系法依赖「已知或可预测的种系」，AbLang 直接按位置似然填补。
- 补全成绩：N 端长段缺失与种系法相当，随机 1–10 个缺失比种系法更好，明显强于通用模型 ESM-1B。
- 缺失长度未知时，用首位残基似然推断全长；ANARCI → AbLang → AbLang 的迭代恢复在重链长缺失区收益最大。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| AbLang | 在 OAS 上掩码预训练的抗体专属语言模型 |
| OAS（Observed Antibody Space） | 海量抗体序列数据库，AbLang 的训练数据来源 |
| 掩码预训练 | 随机遮残基、预测被遮残基的自监督训练 |
| 残基编码 | 模型末端隐空间里每个残基的向量表示 |
| germline（种系） | 未经历体细胞超突变的胚系抗体基因序列 |
| ESM-1B | 通用蛋白质语言模型（对比基线，非抗体专属） |
| ANARCI | 抗体序列编号工具，用于规范比对与编号 |
| N 端 | 序列开头一端，OAS 序列最常缺失的部位 |
