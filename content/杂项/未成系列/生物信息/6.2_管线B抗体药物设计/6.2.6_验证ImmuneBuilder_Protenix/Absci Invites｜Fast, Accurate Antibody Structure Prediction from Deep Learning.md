# 一分钟、CPU 就够：IgFold 把抗体结构预测做到"可扫库"——还自带"哪里不可信"标签

> 视频来源：[YouTube《Absci Invites｜Fast, Accurate Antibody Structure Prediction from Deep Learning》](https://www.youtube.com/watch?v=j2n9j0VRJL0)（约 46 分钟）
> 本文基于视频演说图文稿撰写，观点与数据均可回看视频核对。

## 这支视频要解决的核心问题（SCQA）

**背景**：抗体药物设计管线的验证步，需要给设计出来的抗体序列快速预测结构、并判断预测可不可信。约翰霍普金斯大学 Jeffrey J. Gray 实验室的 Jeffrey Ruffolo 做客 Absci 线上研讨会，介绍他们的两代工作：抗体语言模型 AntiBERTy 与结构预测模型 IgFold（[【跳转到 00:39】](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=39)）。

**冲突**：传统 grafting（模板嫁接）法对 CDR-H3 无能为力——这个环的序列与长度都高度多样，结构库里经常找不到模板；AlphaFold 虽准，但一条序列要 30 分钟到 2 小时，扛不住抗体发现早期动辄成千上万条的序列库。

**疑问**：能不能又快（CPU 上 1 分钟以内）、又准（追平 AlphaFold-Multimer）、还自带"哪个环不可信"的提示？

**回答（中心思想）**：IgFold = AntiBERTy 抗体语言模型的嵌入与注意力 + 图 transformer/三角更新 + 不变点注意力（IPA）端到端预测主链，再交给 Rosetta 补侧链：CPU 上不到 1 分钟；配对抗体精度与 AlphaFold-Multimer 相当；模型自报逐环误差；已有部分结构可作模板注入；训练数据靠 AlphaFold 造出 4.4 万个合成结构，把非冗余抗体结构空间扩大了 40 倍。

![两款模型总览：AntiBERTy 做表征学习，IgFold 用它的嵌入预测结构](assets/Absci%20Invites｜Fast,%20Accurate%20Antibody%20Structure%20Prediction%20from%20Deep%20Learning/00060.webp)

## 一、问题背景：CDR-H3 为什么是老大难

抗体是两条重链加两条轻链的复合物，结构预测真正关心的是与抗原接触的 **Fv 区**（[01:39](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=99)）。Fv 的结合由 **6 个 CDR 环**介导：其中 5 个环采用"典型折叠"（canonical fold），看序列基本就能猜出形状；唯独重链第三个环 **CDR-H3** 序列多样、长度多样，结构琢磨不定——而它又恰恰是结合抗原的主力，所以 H3 建模准不准，直接决定抗体工程的上限（[02:04](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=124)）。

![Fv 区与 6 个 CDR 环：红色为 CDR，H3 是最多样的一条](assets/Absci%20Invites｜Fast,%20Accurate%20Antibody%20Structure%20Prediction%20from%20Deep%20Learning/00124.webp)

传统做法叫 **grafting（嫁接）**：把序列切成结构域，拿 CDR 去结构库 SAbDab 里搜模板，再拼装成完整结构（[02:44](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=164)）。典型环好办，H3 经常搜不到模板，精度也就上不去。Gray 实验室更早的深度学习尝试是把结构当"图"：预测残基两两之间的距离与朝向，再丢给 Rosetta 生成坐标——把 H3 预测精度平均推进了约 0.5 Å，但仍有提升空间（[03:40](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=220)、[04:05](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=245)）。

![嫁接流程：切结构域 → 搜 SAbDab → 拼装；H3 难找模板](assets/Absci%20Invites｜Fast,%20Accurate%20Antibody%20Structure%20Prediction%20from%20Deep%20Learning/00164.webp)

随后 AlphaFold 用"多序列比对里的共进化信息 → 结构"刷新了整个领域（[04:24](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=264)）。但抗体恰恰吃不到这个红利：体内亲和力成熟让 CDR 突变极多，共进化信号几乎不存在。IgFold 的目标因此定为三条（[04:49](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=289)）：**快**（服务大规模抗体库）、**能吃模板**（已有部分结构就别浪费）、**自报误差**（告诉你哪个预测别信）。

![从 AlphaFold 的共进化范式到 IgFold 的端到端抗体预测](assets/Absci%20Invites｜Fast,%20Accurate%20Antibody%20Structure%20Prediction%20from%20Deep%20Learning/00264.webp)

## 二、数据从哪来：10 亿条序列，却没有结构

实验解析的抗体结构只有几千条，但免疫组库测序攒下了海量序列——牛津大学 Deane 实验室把它们汇成 **OAS（Observed Antibody Space）**：约 **10 亿条非配对**抗体序列、约 **12 万条配对**（重轻链成对）序列（[05:20](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=320)、[05:45](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=345)）。序列有、结构没有，怎么榨出信息？答案是**掩码语言建模**：随机遮住一些残基让模型猜，猜得准就意味着模型学会了β折叠的氨基酸偏好、学会了二硫键里半胱氨酸该出现在哪——这些都是三维排列的间接信号（[06:10](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=370)、[06:35](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=395)）。

训练出的模型 AntiBERTy 输出每个序列的"最终隐藏表示"，即嵌入向量。这些嵌入真的学到了东西：

- **免疫组学层面**：对 4 位流感疫苗接种者的抗体库做 UMAP 降维，聚类结构完美复刻 VDJ 重组规则——主簇对应 V 基因，亚簇对应 J 基因，再往下还有 D 基因的微簇（[07:33](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=453)）；
- **结构层面**：对 SAbDab 配对抗体的 CDR 环表示做 t-SNE，CDR-H1、H2 按典型折叠聚类，H3 没有典型折叠就按环长组织——说明预训练确实摸到了结构规律（[08:23](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=503)）。

![流感疫苗接种者抗体库的 UMAP：嵌入聚类复刻 VDJ 重组规则](assets/Absci%20Invites｜Fast,%20Accurate%20Antibody%20Structure%20Prediction%20from%20Deep%20Learning/00453.webp)

## 三、IgFold 架构：嵌入 + 图网络 + IPA，Rosetta 收尾

IgFold 的流水线是：抗体序列 → AntiBERTy 编码，取出嵌入与各层**注意力矩阵**（模型在序列空间学到的"哪些残基该挨着"可以直接给结构预测热身）→ 图 transformer 与**三角乘性更新**层更新节点和边 → 用源自 AlphaFold 的**不变点注意力（IPA）**并入模板（模板坐标固定、只让模型读取信息）→ 再用一组 IPA 层把从原点出发的坐标系推到最终结构 → 最后一组 IPA 固定预测结构、输出**逐原子偏差**的误差估计（[09:13](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=553)、[10:08](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=608)、[10:33](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=633)、[10:58](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=658)、[11:23](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=683)）。拿到主链后再交给 Rosetta 加侧链、修碰撞与非理想键角。

![IgFold 端到端：AntiBERTy 编码 → 图网络 → 主链预测](assets/Absci%20Invites｜Fast,%20Accurate%20Antibody%20Structure%20Prediction%20from%20Deep%20Learning/00553.webp)

![模板注入：IPA 坐标固定，只读取已知结构信息](assets/Absci%20Invites｜Fast,%20Accurate%20Antibody%20Structure%20Prediction%20from%20Deep%20Learning/00633.webp)

## 四、训练数据：让 AlphaFold 造 4.4 万个"合成结构"

SAbDab 只有几千个结构，怎么喂饱深度模型？思路是**借 AlphaFold 造数据**：OAS 约 12 万条配对序列聚类到 1.6 万个，用 AlphaFold 预测成结构；再从 10 亿条非配对序列按 40% 序列一致性聚类出 2.3 万个也预测成结构。两边合计，非冗余抗体结构约是只用晶体结构的 **10 倍**；非配对数据还专门帮了纳米抗体——只见过"配对场景"的旧模型（如 DeepAb）碰上没有轻链的纳米抗体就抓瞎（[11:57](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=717)、[12:22](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=742)）。

![训练数据三来源：SAbDab + OAS 配对合成结构 + OAS 非配对合成结构](assets/Absci%20Invites｜Fast,%20Accurate%20Antibody%20Structure%20Prediction%20from%20Deep%20Learning/00717.webp)

训练时三个数据集均匀采样；一半的样本还附带"模板"——做法是把已知结构随机删掉 1~6 段各 20 个残基（相当于随机挖掉一条 CDR 环），让模型学着在残缺模板下补全（[14:28](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=868)）。损失函数三项：框架残基对齐后的坐标 MSE + 键长损失 + 主链原子与 Cβ 偏差的 L1（[14:53](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=893)）。模型拼装结构的过程也很有意思：第一步先在"紧凑态"摆对残基的相对位置，第二步撑开到真实尺度，第三步微调键长键角，让产物像个正常抗体（[15:25](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=925)）。

![IPA 三步拼装：相对位置 → 撑开尺度 → 修正键长键角](assets/Absci%20Invites｜Fast,%20Accurate%20Antibody%20Structure%20Prediction%20from%20Deep%20Learning/00925.webp)

## 五、成绩单（一）：配对抗体——精度追平 AF-Multimer，速度差两个数量级

评测把结构切成各 CDR 环，对齐框架后量环上重原子 RMSD。grafting 类方法框架与典型环都不错、H3 偏弱；抗体专用的 DeepAb、ABlooper 在 H3 上有进步；AlphaFold-Multimer 虽是通用模型、H3 也不错；IgFold 与 AlphaFold-Multimer 基本打平——毕竟它大量训练在 AF 预测上，真正的差别在**速度**（[18:42](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=1122)、[19:07](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=1147)、[19:32](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=1172)）：

| 方法 | 单条耗时 |
| --- | --- |
| grafting | 几秒~1 分钟内（精度换速度） |
| ABlooper | 约 1 分钟 |
| DeepAb | 最多 10 分钟 |
| AlphaFold-Multimer | 30 分钟~2 小时 |
| **IgFold** | **CPU 上 < 1 分钟** |

![方法对比：IgFold 精度与 AF-Multimer 相当，速度快得多](assets/Absci%20Invites｜Fast,%20Accurate%20Antibody%20Structure%20Prediction%20from%20Deep%20Learning/01172.webp)

逐对比较 IgFold 与 AlphaFold 会发现：两者平均成绩接近，但**常常给出完全不同的构象**——散点图上大量点远离对角线，这侧 IgFold 差 7 Å 而 AlphaFold 差 1 Å，另一侧又反过来（[20:22](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=1222)、[20:47](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=1247)）。这时误差估计就派上用场：预测 RMSD 与真实 RMSD 强相关；长 H3 环中间嵌着β折叠结构域时，模型会摆出"张开"的错误构象，同时**自报高误差**——说明它不是在学"环越长误差越大"的回归，而是真的在判断数据对预测的支持程度（[21:12](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=1272)、[22:02](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=1322)）。唯一失灵的是 CDR-L2：本来就都预测到亚埃级，仅一个离群点骗过了它（[22:27](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=1347)）。

![IgFold vs AlphaFold 的 H3 RMSD 散点：大量非对角点=构象分歧](assets/Absci%20Invites｜Fast,%20Accurate%20Antibody%20Structure%20Prediction%20from%20Deep%20Learning/01247.webp)

## 六、成绩单（二）：纳米抗体——胜过 DeepAb，仍略逊 AlphaFold

纳米抗体没有轻链，CDR-H3 还可以特别长。grafting 法因模板更少而 H1/H2 都会掉分；DeepAb 只在配对数据上训练过，H3 反而显著变差——它总把纳米抗体折成"有轻链时才有的样子"（[22:52](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=1372)、[23:42](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=1422)）。AlphaFold 在纳米抗体上表现出色，H3 显著好于 grafting 与 DeepAb；IgFold 的 H1/H2 不错，但 H3 相比 AlphaFold 有差距（[24:07](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=1447)、[24:32](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=1472)）。具体看构象：IgFold 有时能摆对 AlphaFold 摆不出的 stretched/twist 构象；但**CDR 环里出现二级结构**（比如 H3 中段一小段α螺旋）时它就吃力——AlphaFold 见多识广能折出螺旋，IgFold 只给一团无结构（[24:57](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=1497)）。误差估计在纳米抗体上依然可靠，且它不会像 DeepAb 那样把所有纳米抗体都折成"配对脸"（[25:47](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=1547)）。

![纳米抗体 H3 中嵌α螺旋的失败案例：IgFold 给出无结构折叠](assets/Absci%20Invites｜Fast,%20Accurate%20Antibody%20Structure%20Prediction%20from%20Deep%20Learning/01497.webp)

## 七、模板注入：已有结构别浪费，还能"腌"进嵌入

把测试集抗体的 H3 环删掉、其余坐标当模板喂给模型，有三种玩法：标准 IgFold（不给结构）、只给 H3 以外的全部、连 H3 一起给（[26:45](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=1605)）。给了结构就有额外收益：给了 H3 能到亚埃级；只给框架和其余 CDR 时，虽然总体均值变化不大，但有一批案例的 H3 明显变准（不过嵌着有序β折叠结构域的环依然费劲）——比起 grafting 那样手工嫁接，IgFold 把这些信息"免费"吸收进预测（[27:10](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=1630)、[27:35](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=1655)）。纳米抗体上也有类似案例：给了框架，H3 的 C 端对齐更好，精度从约 2 Å 提到约 1 Å（[28:25](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=1705)）。把整条 Fv 都喂进去虽然对"预测"本身没意义（都有结构了还预测什么），但得到的嵌入携带了结构信息——这种"结构 infused 嵌入"给下游的性质预测、人源化建模当特征更值钱（[28:50](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=1730)）。

![模板三策略：不给 / 给 H3 以外 / 给整条 Fv](assets/Absci%20Invites｜Fast,%20Accurate%20Antibody%20Structure%20Prediction%20from%20Deep%20Learning/01605.webp)

## 八、规模化：一个 10.5 万条序列的结构库

回到 OAS 的 12 万条配对序列，按 95% 一致性去冗余到约 10.5 万条，全部用 IgFold 预测——直方图显示大多数预测自报高置信（[29:26](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=1766)）。这套"合成结构库"在相同序列冗余度下比 SAbDab **扩了 40 倍**，总开销约 **2500 CPU 小时**；生产端每条结构只用 2 个 CPU 核、约 1 分钟，用的还是 2020 年的老集群（[30:41](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=1841)、[34:55](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=2095)）。

![10.5 万条配对序列的预测置信度直方图：多数自报高置信](assets/Absci%20Invites｜Fast,%20Accurate%20Antibody%20Structure%20Prediction%20from%20Deep%20Learning/01766.webp)

## 九、Q&A 精华

- **为什么用 IPA 而不是 EGNN/SE(3)-Transformer？** 同等精度下 IPA 效率高得多：一周的训练量压到两三天，参数还更少；做坐标更新也更顺手（[13:24](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=804)）。
- **损失怎么选？** 误差估计的目标直接用抗体社区的习惯指标——框架对齐后 CDR 环重原子 RMSD；不加键长损失时，模型会在 H3 上"抄近路"：空间距离贴近天然但骨架形状不真实；坐标损失试过 RoseTTAFold 的 RMSD 和 AlphaFold 的损失（算不起），MSE 是效果与效率的折中（[16:14](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=974)、[16:39](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=999)、[17:04](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=1024)）。
- **语言模型贡献多大？** DeepAb 时代加个 LSTM 编码器就带来约 0.25 Å 提升；现在正在试把 BERT 换成 CNN——结构数据多了，也许不需要语言模型加持；上 ESM-1b 这类通用蛋白语言模型会把 2500 万参数的模型撑到 6.5 亿，算力吃不消（[35:20](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=2120)）。
- **训练成本？** AntiBERTy：4 张 A100 训一周，5.5 亿条序列过约 10 遍；IgFold：4.4 万结构训约 70 小时、200 万步（[36:35](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=2195)）。
- **拿 AF 预测当训练数据靠谱吗？** 把 SAbDab 拿掉，每条 H3 会额外差 0.5~1 Å——真实结构依然关键；AF 的价值是把 SAbDab 那个又窄又偏的分布扩成 4 万多个更接近真实抗体的样本（DeepAb 只有 1700 个结构，很容易被"惊到"）（[37:35](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=2255)、[38:00](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=2280)）。
- **容量怎么调？** 第一组 transformer 层加到 4 层就饱和；**模板 IPA 的注意力头数是命门**——8 头是底线，砍到 4 头模型就无视模板；结构 IPA 2 层与 3 层差别不大。结论是"容量刚好就行"，提升要靠数据与任务设计（[42:10](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=2530)、[42:15](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=2535)、[43:05](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=2585)）。
- **下一步？** 一是抗体-抗原复合物预测——难点在数据：AlphaFold 帮不上抗体-抗原复合物的合成数据（[33:40](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=2020)）；二是构象多样性——与其一对一输出，不如让模型输出可采样的构象集合（[34:05](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=2045)）。免疫原性方面，用与 BERT 同源数据训练的生成模型产出的序列，经 T 细胞肽结合与 humanness 评分检验都不像免疫原；可开发性则苦于公开数据太少，也许可以先用 SAP 打分造合成数据自举一把——IgFold 的结构化嵌入应该比纯 BERT 嵌入更有优势（[40:05](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=2405)、[40:55](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=2455)）。
- **结构能打开什么门？** Deane 实验室曾拿已知新冠抗体去抗体库里搜"类旁位"（paratope）——序列差异很大但结合面相似；这类问题没有结构根本没法问（[38:50](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=2330)）。

## 小结

- **快**：抗体序列进、结构出，CPU 上不到 1 分钟，不需要 GPU（[31:47](https://www.youtube.com/watch?v=j2n9j0VRJL0&t=1907)）。
- **准**：配对抗体与 AlphaFold-Multimer 同档（SOTA）；纳米抗体略逊 AlphaFold 但远好于只见过配对数据的旧模型。
- **自知**：逐环误差估计与真实 RMSD 强相关，能告诉你 CDR-H3 这条预测能不能信。
- **开放**：代码在 GitHub，也可从 PyPI 安装。
- 对管线 B 的验证步而言，IgFold 这类工具的角色正是"先快速过一遍结构合理性 + 用误差标记风险区"，把昂贵的复合物预测（AF3/Protenix）留给最值得的候选。

![总结页：快、准、带误差估计、代码开放](assets/Absci%20Invites｜Fast,%20Accurate%20Antibody%20Structure%20Prediction%20from%20Deep%20Learning/01907.webp)

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| CDR / CDR-H3 | 抗体上 6 个决定结合的环区；H3 序列与长度最多样、最难预测也最关键 |
| grafting（嫁接） | 从结构库搜 CDR 模板再拼装的传统建模法；快但 H3 常无模板可用 |
| OAS | Observed Antibody Space，牛津 Deane 组汇总的免疫组库序列库：约 10 亿非配对 + 12 万配对 |
| 掩码语言建模 | 遮住部分残基让模型猜，从而从"只有序列、没有结构"的数据里学到结构规律 |
| IPA（不变点注意力） | 源自 AlphaFold 的注意力模块；IgFold 用它读模板、摆坐标、报误差 |
| 误差自估计 | 模型预测每个骨架原子相对天然结构的偏差（对齐框架后的 CDR 环 RMSD） |
| 纳米抗体（VHH） | 只有重链的单域抗体；只见过配对场景的模型容易把它折错 |
| 结构 infused 嵌入 | 把已知结构喂给模型后取出的表示，携带结构信息，适合下游建模 |
