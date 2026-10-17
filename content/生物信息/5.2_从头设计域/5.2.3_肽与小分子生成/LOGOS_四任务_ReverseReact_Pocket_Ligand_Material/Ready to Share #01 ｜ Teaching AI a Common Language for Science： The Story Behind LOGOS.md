# 科学的「GPT 时刻」如何到来：LOGOS 作者亲述统一科学语法的诞生之路

> 视频来源：[Ready to Share #01 ｜ Teaching AI a Common Language for Science： The Story Behind LOGOS](https://www.youtube.com/watch?v=_0ns1oz3qhM)（阿里巴巴通义实验室官方播客「Ready to Share」第 1 期，约 34 分钟；主持人 Roxan，嘉宾为 LOGOS 论文团队成员）。字幕为 YouTube 英文自动识别轨，术语已按上下文纠正（如 AFO science→AI for science、Q1→Qwen、skiing law→scaling law、ritual sensic→retrosynthesis、soda→SOTA）。本博客基于视频字幕与画面整理，数据与结论均以节目内容为准。

## 本讲要解决的核心问题（SCQA）

**背景**：通义实验室三年前起做了一批**领域专用**科学模型：覆盖小分子与蛋白质的生物分子基座模型（用于药物发现、高通量筛选）、蛋白质与 DNA 的 LUCA 系列序列模型（衍生出病毒、农业等下游专用模型）、以及一个基因序列生成式基础模型。

**冲突**：AI4S 的工程范式与 LLM 脱节——大语言模型用**一个模型、一条流水线**解决所有任务；AI4S 却是"一个任务一个模型、一套数据"，做下游还要微调。团队试过把科学数据直接混进 LLM 的常规训练流程，换了多个模型都不理想。

**疑问**：能不能像 GPT 统一 NLP 那样，用一个基座模型 + 一条统一流水线，解决所有科学任务？

**回答（中心思想）**：团队把科学数据当作**一门自洽的语言**，用三类语法 token（实体、位置、相互作用）改写全部数据，再完全沿用 LLM 的训练流水线预训练出 **LOGOS**。作者称之为"科学的 GPT 时刻"：在口袋→配体生成、口袋识别、MOF 材料生成、ReverseReact 逆合成等任务上，一个模型追平或超越领域专用工具；消融实验还带来三个意外——从 Qwen 初始化比从头训练更好、0.6B→8B 规模律同样成立、六七个域共训明显优于单域。

![视频题图：通义实验室播客第一期，作者分享 LOGOS 背后的故事](assets/Ready%20to%20Share%20%2301%20｜%20Teaching%20AI%20a%20Common%20Language%20for%20Science：%20The%20Story%20Behind%20LOGOS/00000.webp)

## 一、起点：三年「专用模型」积攒的问题意识

[【跳转到 01:37】](https://www.youtube.com/watch?v=_0ns1oz3qhM&t=97)

嘉宾回顾：从 AlphaFold2 展示出解决生物学、化学问题的强大能力开始，AI 研究者与生物研究者都相信 AI 能帮人类解决科学问题。通义团队也在三年前跟进主流范式，做了一批**领域专用模型**：

- **生物分子基座模型**：同时覆盖小分子与大分子（蛋白质），已被用于药物发现和高通量筛选；
- **LUCA 系列序列模型**：同时覆盖蛋白质与 DNA，并衍生出病毒、农业等下游任务专用模型；
- **基因序列生成式基础模型**（节目称 generator）。

![回顾团队三年间开发的领域专用模型时的幻灯片](assets/Ready%20to%20Share%20%2301%20｜%20Teaching%20AI%20a%20Common%20Language%20for%20Science：%20The%20Story%20Behind%20LOGOS/00163.webp)

做这批模型时他们意识到一个"代差"：[【跳转到 04:23】](https://www.youtube.com/watch?v=_0ns1oz3qhM&t=263) 大语言模型用同一套流水线解决所有任务；AI4S 却要为每个领域单独训练模型、单独准备数据，解决下游任务还要微调——可以说 **AI4S 模型落后于 LLM 的工程范式**。于是团队想弥合这个差距。

## 二、两个灵感：GPT 时刻与数学/代码的自洽性

[【跳转到 05:21】](https://www.youtube.com/watch?v=_0ns1oz3qhM&t=321)

第一个灵感来自 **GPT 时刻**：GPT 把 NLP 的所有任务合并起来，用 next-token 预测框架训练所有数据，构建单一模型解决不同任务。

第二个灵感来自**数学与编码**：[【跳转到 05:46】](https://www.youtube.com/watch?v=_0ns1oz3qhM&t=346) 在 LLM 推理模型中，数学和编码能力能显著增强模型——团队认为这是因为**它们是自洽领域（self-consistent domains）**：数学的逻辑与 token 在领域内自洽，自然语言只是辅助 token；编码更明显，写代码时并不需要大量自然语言。

由此产生关键假设：如果让科学数据也变得像数学、代码一样**自洽**，或许就能复制 GPT 时刻。

## 三、两条路线的试错：直接混数据败下阵来

[【跳转到 07:01】](https://www.youtube.com/watch?v=_0ns1oz3qhM&t=421)

想用一个模型解决所有科学问题，有两条路：

1. **简单路线**：直接把科学训练数据塞进 LLM 的常规训练流程——只是"多了一些训练数据"。团队试了多个模型，效果都不好。
2. **语法路线**：把 AI4S 数据当作一门特定语言，让它更自洽，再引入训练集去训练基座模型、增强其科学能力。

![对比两条技术路线时的幻灯片](assets/Ready%20to%20Share%20%2301%20｜%20Teaching%20AI%20a%20Common%20Language%20for%20Science：%20The%20Story%20Behind%20LOGOS/00446.webp)

团队选了第二条路，造出了 LOGOS。[【跳转到 07:51】](https://www.youtube.com/watch?v=_0ns1oz3qhM&t=471) 作者认为他们做的最有价值的事，就是**给科学领域引入一套简单语法**：训练数据里完全不用自然语言，只用科学序列本身，配合一系列特殊 token 使其自洽，然后沿用大型语言模型的训练流水线。

## 四、语法长什么样：实体、位置、相互作用三类 token

[【跳转到 08:16】](https://www.youtube.com/watch?v=_0ns1oz3qhM&t=496)

语法的构成在节目里讲得很直白，就是三类特殊 token：

- **实体 token**：标示科学对象的类别与起止，如蛋白质、抗体、分子、材料的起始/结束指示符；
- **位置 token**：标示不同对象在序列中的位置；
- **相互作用 token**：在科学序列内部标示对象之间在哪里发生相互作用。

![讲解三类语法 token 时的幻灯片](assets/Ready%20to%20Share%20%2301%20｜%20Teaching%20AI%20a%20Common%20Language%20for%20Science：%20The%20Story%20Behind%20LOGOS/00496.webp)

引入这些 token 后，数据变得更自洽，可以只用这些科学数据作为训练样本；[【跳转到 10:34】](https://www.youtube.com/watch?v=_0ns1oz3qhM&t=634) 作者强调语法设计"非常简单"——只加了起始/结束指示符和序列内部的相互作用位置标记，就能把不同数据集、不同科学领域的数据统一到一起，然后**完全按照 LLM 的训练流水线**训练 LOGOS 模型。

![讲解语法设计与数据统一时的幻灯片](assets/Ready%20to%20Share%20%2301%20｜%20Teaching%20AI%20a%20Common%20Language%20for%20Science：%20The%20Story%20Behind%20LOGOS/00634.webp)

目前的语料主要覆盖**分子相关**的科学领域（用分子和原子桥接各子领域）——因为这是研究组自己的数据领域；未来要纳入更多科学领域，还需要领域专家帮助设计各自的语法和专用 token。

## 五、成绩单：「科学的 GPT 时刻」

[【跳转到 12:03】](https://www.youtube.com/watch?v=_0ns1oz3qhM&t=723)

训练完成后，团队在多个任务上测试模型的科学能力。让他们惊讶的是：**所有任务上，模型表现要么最好，要么与领域内最佳专用工具相当**——作者称之为"科学的 GPT 时刻"。

### 5.1 口袋 → 配体生成（Ligand）

[【跳转到 12:58】](https://www.youtube.com/watch?v=_0ns1oz3qhM&t=778)

给定一个蛋白质口袋作为输入，模型能输出一个可以与该口袋结合的小分子；对比所有 SOTA 工具与模型，LOGOS 表现最好。

![讲解口袋条件分子生成任务结果时的幻灯片](assets/Ready%20to%20Share%20%2301%20｜%20Teaching%20AI%20a%20Common%20Language%20for%20Science：%20The%20Story%20Behind%20LOGOS/00778.webp)

### 5.2 口袋识别（Pocket）

[【跳转到 13:34】](https://www.youtube.com/watch?v=_0ns1oz3qhM&t=814)

输入一个蛋白质，模型输出它预测的结合口袋：在已有口袋上，表现优于各类专用工具。更有意思的是，模型还能找出一些**从未被实验验证过**的真实口袋——团队正在寻找合作者，通过湿实验（wet-lab）来验证。

![讲解口袋识别任务与未验证口袋发现时的幻灯片](assets/Ready%20to%20Share%20%2301%20｜%20Teaching%20AI%20a%20Common%20Language%20for%20Science：%20The%20Story%20Behind%20LOGOS/00814.webp)

### 5.3 材料生成（Material：MOF）

[【跳转到 14:29】](https://www.youtube.com/watch?v=_0ns1oz3qhM&t=869)

纯无条件生成任务：在 MOF（金属有机框架）材料上，模型在所有 SOTA 方法中表现最好。

### 5.4 ReverseReact 逆合成

[【跳转到 14:52】](https://www.youtube.com/watch?v=_0ns1oz3qhM&t=892)

LOGOS 还能做化学的 ReverseReact——即逆合成（retrosynthesis）任务，表现同样很好。

![讲解 MOF 材料生成与逆合成任务时的幻灯片](assets/Ready%20to%20Share%20%2301%20｜%20Teaching%20AI%20a%20Common%20Language%20for%20Science：%20The%20Story%20Behind%20LOGOS/00869.webp)

## 六、三个意外发现（消融实验）

[【跳转到 15:14】](https://www.youtube.com/watch?v=_0ns1oz3qhM&t=914)

### 6.1 用 Qwen 初始化，比从头训练更好

设置两组对照：一组随机初始化、从零训练；另一组用 **Qwen 模型**做初始参数，先连续预训练再做 SFT。结果从 Qwen 基座出发的最终模型表现**明显更好**。作者也直呼意外：过去几年做科学专用模型，都是只用科学数据从头训练；现在看到从大语言基座模型出发反而更好。被问及最意外的发现时，作者再次点名这个消融——在他们的领域专用模型时代，同类 transformer 用 Qwen 初始化并没有这种效果，而 LOGOS 有，这暗示**可以用 LLM 作起点，把科学能力嵌入大语言模型**。

![讲解初始化方式消融（随机 vs Qwen）时的幻灯片](assets/Ready%20to%20Share%20%2301%20｜%20Teaching%20AI%20a%20Common%20Language%20for%20Science：%20The%20Story%20Behind%20LOGOS/00914.webp)

### 6.2 规模律在科学领域同样成立

[【跳转到 16:29】](https://www.youtube.com/watch?v=_0ns1oz3qhM&t=989)

团队训练了从 0.6B 到 8B 的多档模型规模：规模越大，性能越好——与 LLM 领域的规律一致（各档具体规模以论文为准）。

### 6.3 多域共训显著优于单域

[【跳转到 17:19】](https://www.youtube.com/watch?v=_0ns1oz3qhM&t=1039)

对比"只用单一领域数据训练"与"六七个领域数据一起训练"基座模型：多域联合训练的最终结果明显更好。这说明**跨域协同有助于训练更强的模型**，也让团队有信心用更多数据、更大的模型去验证科学领域的 scaling law（规模律）。

![讲解多域共训消融时的幻灯片](assets/Ready%20to%20Share%20%2301%20｜%20Teaching%20AI%20a%20Common%20Language%20for%20Science：%20The%20Story%20Behind%20LOGOS/01039.webp)

## 七、未解的权衡与未来计划

### 7.1 自然语言与科学语言的此消彼长

[【跳转到 25:24】](https://www.youtube.com/watch?v=_0ns1oz3qhM&t=1524)

这是作者坦承**尚未解决**的挑战：训练中增加自然语言数据，科学能力反而下降。原因尚不明确，团队猜测是数据量还不够、模型规模还太小——留给未来扩大规模与数据去解决。

### 7.2 走了哪些弯路

[【跳转到 22:54】](https://www.youtube.com/watch?v=_0ns1oz3qhM&t=1374)

作者复盘了多年的试错：直接合并所有数据用 next-token 训练、用 SFT 微调基座模型、尝试图神经网络与各类 transformer 变体，效果都不达预期；曾想把所有训练数据重构成"提示词 + 答案"格式，但很难为不同类型的科学问题找到统一的答案引入方式。最终回到**从科学领域本身出发**：引入专用 token、把所有数据转成序列、用 next-token 预测训练——调试完训练代码的 bug 后，一开始只在一两个任务上见效，随着任务越加越多，惊喜地发现**所有任务都能 work**。

### 7.3 现实影响与下一步

[【跳转到 28:56】](https://www.youtube.com/watch?v=_0ns1oz3qhM&t=1736)

作者认为 LOGOS 的部分任务已经非常实用：**筛选（screening）与口袋发现（pocket finding）对制药业很有价值，材料生成对材料业很实用**。但这仍是一条早期路线，要推向更大数据集与更大模型规模。未来计划有二：一是验证**科学模型的 scaling law**；二是纳入更多科学领域——这需要为每个新领域设计特定语法与专用 token，需要领域专家帮忙把科学语言转成序列。此外还有一个反向方向（science for AI）：用更多科学数据训练 LLM，验证科学数据能否提升模型的通用智能。

## 八、一句话带走

[【跳转到 32:41】](https://www.youtube.com/watch?v=_0ns1oz3qhM&t=1961)

如果观众只记住一件事，作者希望是：**LOGOS 不是又一个多领域/多模态基础模型——他们真正想做的，是把科学信息嵌入大语言模型**。

## 小结

- 团队三年专用模型的积累，暴露了 AI4S"一任务一模型 + 下游微调"范式与 LLM 的代差。
- 两个灵感：GPT 用 next-token 统一 NLP；数学与代码因"自洽"而增强推理——科学数据也可以被改造成自洽语言。
- 直接混数据的路线失败；语法路线胜出：只用科学序列 + 实体/位置/相互作用三类 token，完全沿用 LLM 训练流水线。
- 成绩单：口袋→配体生成、口袋识别（含从未验证口袋）、MOF 材料生成、ReverseReact 逆合成，全部追平或超越 SOTA 专用工具。
- 三个消融意外：Qwen 初始化优于从头训练；0.6B→8B 规模律成立；六七域共训显著优于单域。
- 未解权衡：自然语言数据加多，科学能力反而下降；未来靠更大规模与更多数据解决。
- 作者的一句话定位：LOGOS 的目标是把科学信息嵌入 LLM，而不是再造一个多模态基座。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| LOGOS | 通义实验室提出的统一科学语法多域生成基础模型（论文 *Speaking the Language of Science*） |
| 统一科学语法 | 用三类特殊 token（实体/位置/相互作用）把科学数据改写成自洽的"语言" |
| 自洽领域（self-consistent domain） | 数学、代码这类不依赖自然语言即可自表达的领域，是其能增强 LLM 推理的原因 |
| next-token 预测 | 自回归训练目标：给定前文预测下一个 token，LOGOS 完全沿用 LLM 的训练流水线 |
| ReverseReact | 逆合成任务：从目标产物反推反应物 |
| Pocket identification | 口袋识别：输入蛋白质，输出其潜在结合口袋 |
| MOF | 金属有机框架材料，本节目材料生成任务的代表 |
| Qwen 初始化 | 用通义千问模型参数作为 LOGOS 训练起点（连续预训练 + SFT），消融显示优于随机初始化 |
| scaling law（规模律） | 模型规模/数据增大带来性能提升的规律，团队计划在科学领域验证 |
| 湿实验（wet-lab） | 实验室实际生化验证；团队正为模型预测的未验证口袋寻找湿实验合作 |
| science for AI | 反向方向：用科学数据反哺 LLM，验证能否提升通用智能 |

> 延伸阅读：论文的系统性拆解（三范式局限、七模态语料 448.7 亿 token 的构建细节）见姊妹篇 [首个统一「科学语法」多领域生成基础模型！通用科学AI大一统的新方向 【AI for Science】](首个统一「科学语法」多领域生成基础模型！通用科学AI大一统的新方向%20【AI%20for%20Science】.md)。
