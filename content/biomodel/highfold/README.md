# 系列：HighFold 与环肽 / 二硫键结构预测

- **平台**：YouTube
- **来源**：SDxy5E8fvXY、T4b9YuMhchg
- **视频数**：2
- **主题**：围绕「环肽与二硫键的结构预测与设计」这一主线，收录两篇 ML for Protein Engineering / Institute for Protein Design 的研讨会报告。第 1 篇《环肽结构预测与设计》讲：为什么现成 AlphaFold 用不了环肽（只见过线性、L 型蛋白），以及如何只用一改动——把位置编码里的首尾相对位置改成「环」（**循环偏移 cyclic offset**）——就让预训练模型零样本预测环肽；进而用 **AFdesign**（梯度反传进序列）与 **hallucination**（无目标地大量采样高置信骨架）规模化从头设计环肽，并经外消旋结晶拿到 0.3 Å 级别的实验验证，最后在 MDM2 靶点上做出约 350 nM 的环肽抑制剂。第 2 篇《富二硫键微型蛋白的从头设计》讲：面向难成药的 **B 类 GPCR**，把天然激素配体「拆成激动 N 端 + 结合 C 端」，用 **SEWAnything** 骨架设计、**Hemlock** 引入 C 端二硫键、分层的 Rosetta 序列设计，做出可表达、可纯化、具激动活性的 PTH1R 微型蛋白（Walter 24），并规划了转为拮抗剂的路径。两篇共同展示了「以二硫键/环化约束驱动结构预测与设计」的现代深度学习实践。

## 视频索引

| 视频键 | 标题 | 时长 | 视频演说图文稿 | 博客 | 配图 | 原视频 |
| --- | --- | ---: | --- | --- | ---: | --- |
| SDxy5E8fvXY | 环肽结构预测与设计：用 AlphaFold 攻克「环」的难题（ML for Protein Engineering） | 1:07:20 | [文稿](transcripts/环肽结构预测与设计_基于AlphaFold.md) | [博客](blog/环肽结构预测与设计_基于AlphaFold.md) | 15 | [YouTube](https://www.youtube.com/watch?v=SDxy5E8fvXY) |
| T4b9YuMhchg | 富二硫键微型蛋白的从头设计：靶向 B 类 GPCR 的激动剂与拮抗剂（IPD） | 51:20 | [文稿](transcripts/富二硫键微型蛋白的从头设计_靶向B类GPCR.md) | [博客](blog/富二硫键微型蛋白的从头设计_靶向B类GPCR.md) | 15 | [YouTube](https://www.youtube.com/watch?v=T4b9YuMhchg) |

## 博客结构速览

**环肽结构预测与设计——用 AlphaFold 攻克「环」的难题**

- 一、为什么要做环肽：抗体与小分子之间的治疗空间、环孢素、GKC/FastDesign 旧流程、膜渗透与靶向设计
- 二、现成 AlphaFold 为什么用不了：只见过线性（L 型）蛋白，位置关系是喂进去的输入
- 三、核心创新一：循环偏移（cyclic offset）——首尾相对位置设为 −1，零样本泛化；80 个天然环肽验证 50/80 准确
- 四、核心创新二：AFdesign——梯度反传进序列做 backbone design，换置信度损失即 hallucination
- 五、实验验证：从能量漏斗到 0.3 Å 外消旋晶体结构
- 六、规模化从头设计：5 万骨架/档、pLDDT>0.9 筛选、约 2 万骨架库、8 个晶体验证
- 七、走向药物：MDM2 靶点嫁接 + ProteinMPNN + AlphaFold 复合物预测，命中约 350 nM
- 八、问答精选（更长序列、对抗样本、D 型/非天然氨基酸、构象系综、低分挽救、指标选择）

**富二硫键微型蛋白的从头设计——靶向 B 类 GPCR**

- 一、B 类 GPCR：难打成药的靶点、PTH1R、激动剂/拮抗剂、固有无序与两步结合、微型蛋白载体优势
- 二、设计流程总览：需求驱动的三步走
- 三、第一步：SEWAnything 骨架设计（用天然片段嵌合延展三螺旋束）
- 四、第二步：Hemlock 引入 C 端二硫键
- 五、第三步：Rosetta 序列设计——分层（surface/boundary/core）+ 设计限制
- 六、用计算指标筛选：结合能/界面面积/形状互补性 + 核心吸引能，筛出 48 个 Walter
- 七、实验验证：哺乳动物表达、赋形剂辅助纯化、cAMP GloSensor 活性——Walter 24 作激动剂起效
- 八、小结与下一步（亲和力成熟、改进协议、转为拮抗剂、其余 9 个靶点）
- 九、问答精选（结合态设计、多样性饱和、坏设计归因、SEWAnything 对比、核心不放芳香族）

## 核心知识点速览

- **环肽（cyclic peptide）**：首尾相连（或其他环化方式）形成环状骨架的短肽，兼具抗体级亲和力与小分子级穿膜性；代表药物环孢素（约 1202 Da）能穿膜、可口服，先结合亲环蛋白 A 再生成新界面结合钙调磷酸酶。
- **为什么 AlphaFold 直接用不了环肽**：训练数据只有线性、L 型蛋白，且没见过这么短的肽；但位置关系是**作为输入喂进去的**，因此可以改输入。
- **循环偏移（cyclic offset）**：把位置编码中第一与最后一个残基的相对位置设为 −1，使 AlphaFold 认识「环」拓扑；仅此一改即可零样本泛化（80 个天然环肽中 50 个 pLDDT>0.7 且 RMSD<1.5 Å，且"自信通常即正确"）。
- **AFdesign**：把梯度反传穿过预训练 AlphaFold，但更新的是**输入序列**（非权重）；用 distogram 损失做 backbone design，用 pLDDT/PAE/接触数等置信度损失即得到 **hallucination**，可凭空生成新骨架。
- **规模化设计**：7–13 残基每档 hallucinate 5 万个，扭转角聚类去重，pLDDT>0.9 严格筛选，积累约 2 万高置信骨架库；外消旋结晶验证 8 个，Cα RMSD 可达 0.3 Å。
- **B 类 GPCR**：带大胞外域、由激素多肽调控的小家族（14 个），激动剂仅 3 个获批、无拮抗剂获批；天然配体固有无序、结合时才折叠成 α 螺旋。
- **设计蓝图**：稳定天然配体的 C 端（结合部分）做成激动剂，再去掉 N 端（激动部分）得到竞争性拮抗剂。
- **SEWAnything / SEWING**：用 PDB 天然 helix-loop-helix 片段库与输入螺旋对齐嵌合、逐步延展成三螺旋束；SEWAnything 更模块化，可在流程中插入筛选。
- **Hemlock**：引入 C 端二硫键（SEWAnything 找长 loop + Rosetta disulfide mover + 修剪多余 loop）。
- **分层序列设计**：按 surface/boundary/core 分层规定可用氨基酸（核心仅疏水、边界最宽容、表面偏亲水），核心与界面允许更多芳香族/稀有 rotamer；排除色氨酸与甲硫氨酸以防氧化。
- **筛选与验证**：结合能（dG_separated）、结合界面面积（dSASA）、形状互补性、核心残基全原子吸引能（fa_atr）联合筛选；哺乳动物表达（Siderocalin 分泌标签）、赋形剂（精氨酸/谷氨酸 XCP 缓冲液）辅助纯化、cAMP GloSensor 测活性——Walter 24 呈螺旋并作为 PTH1R 激动剂起效。
