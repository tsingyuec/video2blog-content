# AMPFormer：把"生成 AMP"与"预测 MIC"装进同一个基础模型（Helmholtz AI 报告）

> 视频来源：YouTube《AMPFormer：A Peptide Foundation Model for Antimicrobial Discovery — P. Gawade》（Helmholtz AI 会议报告），讲者 Pankaj Gawade（Helmholtz 慕尼黑 / TUM 博士生），时长 12 分钟。
> 本篇是「管线 D：抗菌肽开发」**活性筛选步**（6.4.2）的配套视频，承担"新一代基础模型"面：同目录另两篇分别覆盖 APEX 本体与大规模挖掘（de la Fuente 讲座）与经典 ML 预测方法（Raghava 讲座）；本篇回答的是更前沿的问题——**能不能让一个模型既生成候选、又预测活性，还能随每轮湿实验自我改进**。

## 本讲要解决的核心问题（SCQA）

**背景**：若不采取行动，2050 年耐药感染每年将致约 1000 万人死亡；抗菌肽（AMP，通常 <50 aa）是希望的替代路线——对哺乳细胞毒性低、且因作用机制特殊，细菌更难产生耐药。[【跳转到 00:24】](https://www.youtube.com/watch?v=H0zLf_LyL0U&t=24)

**冲突**：肽序列空间约 **10^65**。传统 AI 管线两条路——要么在 AMP 数据库上训生成模型采样新肽，要么从大序列库里分箱出候选肽再过 AMP/非 AMP 分类器——都有三大毛病：**可控性有限、样本效率低、数据稀缺时不可靠**，结果就是昂贵的湿实验验证与低实验命中率。[【跳转到 01:43】](https://www.youtube.com/watch?v=H0zLf_LyL0U&t=103)

**疑问**：能不能把"生成"与"性质/活性预测"合进同一个骨干，并用主动学习循环让每一轮湿实验反哺模型？

**回答（中心思想）**：能。AMPFormer 用约 **370 万条肽序列**做联合预训练——交替注意力 + 任务专属头：**2 个生成头**（下一 token 生成 + 重建）与 **39 个性质预测头**（电荷、疏水性、芳香性等）**共享同一骨干权重**；再在"菌株 + 实测 MIC 值"数据上微调，配合**自改进主动学习循环 + 联合测试时推理（随机束搜索）**；四个设计目标实验中，广谱杀菌在湿实验拿到 **25/25 全命中**（其中 1 条对全部 17 株有活性）。[【跳转到 02:08】](https://www.youtube.com/watch?v=H0zLf_LyL0U&t=128)

![AMPFormer 联合预训练：2 个生成头 + 39 个性质预测头共享骨干](assets/AMPFormer：A%20Peptide%20Foundation%20Model%20for%20Antimicrobial%20Discovery%20—%20P.%20Gawade/00128.webp)

## 一、架构：一个骨干，两种任务

AMPFormer 的核心是把**预测式**与**生成式**两条传统管线合并：

- **生成头 ×2**：下一 token 生成（自回归造新序列）与重建（保序列合法性）；
- **性质预测头 ×39**：电荷、疏水性、芳香性等理化性质——模型不仅"懂序列"，还"懂描述符"；
- 同一骨干、共享权重，论文依据是分子领域已证明联合生成+性质预测的协同收益。[【跳转到 02:58】](https://www.youtube.com/watch?v=H0zLf_LyL0U&t=178)

微调数据正是活性筛选的标准形态：**不同菌株及其实测 MIC 值**——微调后模型即可针对给定细菌输出性质/活性预测。

## 二、自改进主动学习循环 + 测试时推理

这是本报告最有"管线味"的部分，直接对应 6.4.2 的"筛选—验证—迭代"闭环：

1. 微调后的 AMPFormer **生成序列**并**预测目标菌株的性质**；
2. 按预测性质计算分数（score RX）；
3. **随机束搜索**（stochastic beam search）做联合测试时推理：从根节点出发采样多条候选肽（每个叶节点是一条肽），按分数选最优，**回溯**到上层节点再跑一轮束搜索；[【跳转到 03:48】](https://www.youtube.com/watch?v=H0zLf_LyL0U&t=228)
4. 最优候选送去**湿实验**，实验结果回到第 1 步——循环自我改进。

![随机束搜索：采样-打分-回溯的测试时推理](assets/AMPFormer：A%20Peptide%20Foundation%20Model%20for%20Antimicrobial%20Discovery%20—%20P.%20Gawade/00228.webp)

## 三、四个设计目标实验

动手前先做**健全性检查**：与多个模型基准对比，AMPFormer 在"生物学合理性"与所有外部分类器的预测活性上全面领先。[【跳转到 05:28】](https://www.youtube.com/watch?v=H0zLf_LyL0U&t=328)

| 目标 | 验证方式 | 结果 |
|---|---|---|
| ① 广谱杀菌 | **湿实验**（in vitro） | **25/25 全部杀死多重耐药菌**；1 条肽对全部 17 株有活性；在"x=MIC 阈值，y=成功率"图上，AMPFormer 在低至 **MIC 16** 阈值下仍保持高成功率，大幅甩开其他模型 [【跳转到 06:18】](https://www.youtube.com/watch?v=H0zLf_LyL0U&t=378) |
| ② 杀 G⁻ 不杀 G⁺ | in silico | PMIC 越高越有效；主动学习迭代 1→4，两群分离度持续拉大 [【跳转到 07:08】](https://www.youtube.com/watch?v=H0zLf_LyL0U&t=428) |
| ③ 杀 G⁺ 不杀 G⁻ | in silico | 最难：初始信号低，且生物学上"杀 G⁺"往往连带杀 G⁻；但到迭代 4 仍取得有意义的分离 [【跳转到 07:58】](https://www.youtube.com/watch?v=H0zLf_LyL0U&t=478) |
| ④ 广谱杀菌但不伤共生菌 | in silico | 共生菌是"好细菌"；迭代从 1 到 4 差距逐步增大 [【跳转到 08:23】](https://www.youtube.com/watch?v=H0zLf_LyL0U&t=503) |

一个重要的实操细节：候选**不只从最终迭代选**，而是**每一轮迭代的最优候选都送去实验验证**——用湿实验为整条优化轨迹标定，而非只看终点。

![MIC 阈值-成功率图：AMPFormer 在 MIC 16 阈值下 25/25 全命中](assets/AMPFormer：A%20Peptide%20Foundation%20Model%20for%20Antimicrobial%20Discovery%20—%20P.%20Gawade/00378.webp)

![PMIC 迭代分离：主动学习 1→4 轮，目标群与非目标群逐渐分开](assets/AMPFormer：A%20Peptide%20Foundation%20Model%20for%20Antimicrobial%20Discovery%20—%20P.%20Gawade/00428.webp)

## 四、结论与 Q&A

**结论**：向社区提供一个可用于**性质预测、序列生成与优化**的肽基础模型；自改进主动学习循环 + 测试时推理支持"按目标菌株定制"的生成与预测；实验②③④的体外验证仍在进行（作者明言"stay tuned"）——讲中唯一的全湿实验结论是实验①的 25/25。[【跳转到 08:48】](https://www.youtube.com/watch?v=H0zLf_LyL0U&t=528)

**Q&A 两个亮点**：

- **新颖性**：生物合作者回信说，这些肽"**不可能成为传统抗生素**——它们看起来不像任何传统 AMP，但对测试的全部 25 条都 active"。这提示基础模型可以走出"已知 AMP 分布"的舒适区（也呼应 de la Fuente 讲座里"涌现机制"的主题）。[【跳转到 10:23】](https://www.youtube.com/watch?v=H0zLf_LyL0U&t=623)
- **毒性**：基础模型可在**实验验证的毒性数据集**上微调出分类器，预先滤掉可能有毒的序列——与 Raghava 讲座的 ToxinPred 理念一脉相承。[【跳转到 10:48】](https://www.youtube.com/watch?v=H0zLf_LyL0U&t=648)

![Q&A：合作者确认 25 条新肽"不像传统 AMP"但全部有活性](assets/AMPFormer：A%20Peptide%20Foundation%20Model%20for%20Antimicrobial%20Discovery%20—%20P.%20Gawade/00623.webp)

## 小结

AMPFormer 给 6.4.2 的"活性筛选"提供了最新的形态：**筛选不再是一次性打分，而是"生成→预测→束搜索选优→湿实验→回灌模型"的自改进循环**。三点可迁移的启示：①生成与预测共享骨干，让候选在"合法性"与"活性"两端同时受检；②微调数据与平台 APEX 同构（菌株 + 实测 MIC）；③每轮迭代都留样验证，把湿实验预算花在整条优化轨迹上。
