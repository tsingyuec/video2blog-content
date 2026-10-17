# LocARNA：把一组 RNA 的序列和结构放在一起比对，共识结构直接画出来

> 视频来源：[YouTube《LocARNA (english)》](https://www.youtube.com/watch?v=H_ohb1IHgQ4)（约 4 分 38 秒，LocARNA 开发者出品的官方网页工具教程）
> 本文基于视频演说图文稿撰写，观点与数据均可回看视频核对。

## 本讲要解决的核心问题（SCQA）

**背景**：管线 E 的两条路线（热力学折叠、深度学习接触图）各自给出 RNA 二级结构后，最后一步要做"交叉验证"——把不同来源的结构放到一起，定量比较它们像不像、哪里像、哪里不像。

**冲突**：比较 RNA 不像比较序列那么直接。序列比对只需要照顾"字母对字母"，而 RNA 的结构比较有一个额外难题：**每条序列都有许多潜在结构，你永远不确定分子此刻折叠成的到底是哪一个**（[01:15](https://www.youtube.com/watch?v=H_ohb1IHgQ4&t=75)）。若只盯着"自由能最低的那一个结构"去比（比如 RNAdistance 对两条 dot-bracket 算距离），就丢掉了其他可能性。

**疑问**：有没有工具能在比对一组 RNA 时，同时考虑序列相似性和"所有潜在结构"的不确定性，并给出一个共同结构？

**回答（中心思想）**：LocARNA。它内置一个概率模型，按各自的概率**同时考虑所有潜在结构**，从中找出对整组序列都最合适的结构；在 Freiburg RNA Tools 网页服务器上贴入 FASTA、点一下按钮，就能得到"多序列结构比对 + 共识（consensus）结构 + 结构保守区着色"的完整结果（[00:00](https://www.youtube.com/watch?v=H_ohb1IHgQ4&t=0)）。

## 一、为什么 RNA 的结构比较难

视频开场动画一句话点题：LocARNA 算的是一个**比对（alignment）**，它比较的是**一组** RNA 分子，而且"比较的不只是序列，还有结构"（[00:00](https://www.youtube.com/watch?v=H_ohb1IHgQ4&t=0)）。

难在哪？每条 RNA 序列都可能折叠出**许多**潜在结构（[00:25](https://www.youtube.com/watch?v=H_ohb1IHgQ4&t=25)）——热力学路线的 RNAfold 会给 MFE 结构，也可能有一堆次优结构；深度学习路线给出的接触图同样可以读出多种配对方案。如果你不知道分子"真正"折成哪一个，两两比较就无从下手。

LocARNA 的做法是：把所有潜在结构都纳入考虑，按概率加权，找出**对整组被比较序列都最合适的那一个结构**（[00:25](https://www.youtube.com/watch?v=H_ohb1IHgQ4&t=25)）。这样一来，序列之间的相似点、差异点（比如某条 RNA 缺了一段）都会在比对里显形（[00:50](https://www.youtube.com/watch?v=H_ohb1IHgQ4&t=50)）。

> 小知识：这个"按概率同时考虑所有结构"的思路，和逐对比较两个确定结构（如 RNAdistance 的 Hamming 距离 / 树编辑距离）是两种互补的问法——前者问"这组同源 RNA 一起看，结构保守区在哪"，后者问"这两条预测结构差多远"。

![LocARNA 开场：比较一组 RNA 的序列与结构](assets/LocARNA%20%28english%29/00000.webp)

![每条序列有许多潜在结构，是结构比较的核心难点](assets/LocARNA%20%28english%29/00025.webp)

![概率模型：按概率同时考虑所有潜在结构](assets/LocARNA%20%28english%29/00080.webp)

## 二、网页实操：贴入序列，一键比对

教程的主体是 Freiburg RNA Tools 在线服务器的完整演示：

1. 打开服务器 `rna.informatik.uni-freiburg.de`，里面可以直接在线试用 LocARNA（[01:45](https://www.youtube.com/watch?v=H_ohb1IHgQ4&t=105)）；
2. 演示者准备了一个文本文件，里面是 6 条 RNA 序列——还特意说明"最后两条正是开场动画里的那两条"（[02:05](https://www.youtube.com/watch?v=H_ohb1IHgQ4&t=125)）；
3. 全选复制（Ctrl+C），粘贴进输入框（[02:19](https://www.youtube.com/watch?v=H_ohb1IHgQ4&t=139)）。

![Freiburg RNA Tools 在线服务器入口](assets/LocARNA%20%28english%29/00110.webp)

![粘贴一组 FASTA 序列到输入框](assets/LocARNA%20%28english%29/00139.webp)

提交前只有一个关键选择：**全局（global）还是局部（local）比对**（[02:29](https://www.youtube.com/watch?v=H_ohb1IHgQ4&t=149)）：

- **local**：预期序列整体可能很不一样，但存在局部相似的片段，只找出这些相同/相似的部分；
- **global**：比较**整条**序列——本例六条 RNA 全长相似，所以选 global。

还有若干影响比对打分的高级选项，教程里没有展开，直接点 **Go** 提交（[02:54](https://www.youtube.com/watch?v=H_ohb1IHgQ4&t=174)）。

> 小知识：这个选择和序列比对里 Needleman-Wunsch（全局）/ Smith-Waterman（局部）的分工一致——只是 LocARNA 在此之上多比了一层"结构"。

![global 与 local 对齐的选择](assets/LocARNA%20%28english%29/00149.webp)

## 三、读懂结果：比对图 + 共识结构 + 保守区着色

结果页稍作处理后即可查看（[03:19](https://www.youtube.com/watch?v=H_ohb1IHgQ4&t=199)）：

- **比对图**：六条 RNA 的多序列结构比对整图（[03:25](https://www.youtube.com/watch?v=H_ohb1IHgQ4&t=205)）；
- **共识结构（consensus structure）**：比对图下方就是它——"如果这六条 RNA 形状相似，它们最可能共同折叠成的形状就是这一个"（[03:30](https://www.youtube.com/watch?v=H_ohb1IHgQ4&t=210)）；
- **结构保守区着色**：比对图里不同颜色的区域就是"结构上保守的区域"，一眼可见哪些片段连结构都保住了（[03:48](https://www.youtube.com/watch?v=H_ohb1IHgQ4&t=228)）；
- 页面最底部还有**文本形式的比对**，可以直接复制粘贴（[03:59](https://www.youtube.com/watch?v=H_ohb1IHgQ4&t=239)）；比对结果和共识结构也都能**下载**保存（[04:04](https://www.youtube.com/watch?v=H_ohb1IHgQ4&t=244)）。

![六条 RNA 的多序列结构比对图](assets/LocARNA%20%28english%29/00205.webp)

![共识结构：六条 RNA 最可能共同折叠成的形状](assets/LocARNA%20%28english%29/00210.webp)

![颜色编码标出结构保守区](assets/LocARNA%20%28english%29/00228.webp)

## 四、它在管线 E 里的位置

对照本系列"双路线互验"的最后一步，LocARNA 和 RNAdistance 的分工可以这样理解：

- **RNAdistance**：拿两条 dot-bracket 结构算**距离**（Hamming / 树编辑距离等），回答"热力学路线和深度学习路线的两条预测差多远"，快而直接；
- **LocARNA**：拿**一组同源 RNA** 做序列+结构联合比对，回答"这组序列的结构保守区在哪、共识结构长什么样"。它给出的保守区，正是"用进化证据交叉验证预测结构"的比对基础——本系列下一篇（Elena Rivas 的报告）会把这个思路推到极致：共变分析。

一句话：**RNAdistance 量"两条预测像不像"，LocARNA 找"一组同源 RNA 保不保守"**——一个盯两条结果的差异，一个盯进化留下的结构签名。

## 延伸阅读

- 本系列上一篇：[RNA 二级结构的预测（mFold 实操）](../6.5.1_热力学路线RNAfold→RNAsubopt→RNAalifold→RNAinverse/RNA二级结构的预测.md)
- 下一篇：[Elena Rivas：RNA 结构的进化保守性](Elena%20Rivas-RNA结构的进化保守性.md)（共变分析如何交叉验证结构）
