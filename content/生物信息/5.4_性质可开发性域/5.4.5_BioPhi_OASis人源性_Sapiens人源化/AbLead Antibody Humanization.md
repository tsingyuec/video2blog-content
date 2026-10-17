# AbLead Antibody Humanization

> 来源视频：[AbLead Antibody Humanization](https://www.youtube.com/watch?v=8y0Uwwz-Kvg)（YouTube，18 分 05 秒，en-orig 原声字幕）。本文基于该视频的「图-字幕」演说稿整理，所有结论均出自视频画面与口播，内容可核查。字幕为 YouTube 自动生成，专有名词已按上下文纠正：OA sign → OASis、BioFi/BioFile → BioPhi、Honnegar → Honegger、North → Kabat、315 → IGKV3-15。

## 本讲要解决的核心问题（SCQA）

**背景**：治疗性抗体不能"太像鼠"——非人源序列会被人体免疫系统识别并诱导产生抗药抗体。BioPhi 平台把"让抗体像人"标准化为两条能力：用 **Sapiens** 语言模型提出人源化突变，用 **OASis** 依据 OAS（Observed Antibody Space）抗体序列库评估人源性。

**冲突**：真实的人源化远不止"跑一个模型"：哪些位置允许动（CDR？框架？DE loop？）、用哪条人 germline 当模板、改完之后人源性够不够——每一步都有多种做法，缺的是一条可操作的工程流程。

**疑问**：有没有一场完整实操演示，能把"Sapiens 提突变 + OASis 式评估"与经典 germline 模板法放进同一个流程里对照走完？

**回答（中心思想）**：有。Ketchum Biotherapeutics 的抗体分析与工程套件 **AbLead** 的这期人源化演示完整覆盖了这条链路：三种掩蔽策略（Honegger 模板 / CDR / 自定义）、两条人源化路线（germline 模板法与 BioPhi Sapiens 法）、突变组合生成，最后用"类似 BioPhi OASis 方法"的 OAS 位置频率核查揪出 DE loop 隐患——正好对应本目录条目「BioPhi —— OASis 人源性 / Sapiens 人源化」的两个任务面。

## 一、起点：一条鼠源抗体在主表格里被判"离人很远"

演示项目里放了一条鼠源序列 [【跳转到 00:00】](https://www.youtube.com/watch?v=8y0Uwwz-Kvg&t=0)。AbLead 主表格自动判定：轻链、重链都是鼠源，VL/VH 的 germline（胚系基因，指未发生 V(D)J 重排与体细胞超突变的抗体基因"原种"序列）也匹配到鼠源。

翻到人源性判定一栏：这条序列的 **OASis、peptide representation 与 OAS 得分都很低**——鼠源序列"不像人"是必然的 [【跳转到 00:25】](https://www.youtube.com/watch?v=8y0Uwwz-Kvg&t=25)。随后选中该条目、打开编辑菜单，进入 **Humanization（人源化）工具**。

![主表格判定鼠源：OASis/peptide representation/OAS 得分都很低](assets/AbLead%20Antibody%20Humanization/00025.webp)

## 二、人源化工具的设置面板：物种、germline 数量与排序方式

进入工具后，第一组设置决定"往哪个方向人源化" [【跳转到 00:49】](https://www.youtube.com/watch?v=8y0Uwwz-Kvg&t=49)：

- **目标物种**：决定后续用哪套 germline 做模板——比如从鼠改到兔就会换成兔 germline；演示选择 human；
- **展示的 germline 数量**：演示只展示 5 条以压缩界面，实际可展开更多去寻找特定 germline [【跳转到 01:14】](https://www.youtube.com/watch?v=8y0Uwwz-Kvg&t=74)；
- **排序方式**：默认按 **modification identity**（将发生修饰位点上的同一性）排序，也可按 full identity（全长同一性）排序 [【跳转到 01:34】](https://www.youtube.com/watch?v=8y0Uwwz-Kvg&t=94)。建议用前者：不修改的位置本来就和 germline 相同，真正要比的是"会被修改的那些位置"上各条 germline 的同一性。

![人源化工具：目标物种决定 germline 模板的来源](assets/AbLead%20Antibody%20Humanization/00049.webp)

轻、重链都提供 IMGT 线性编号与 CDR/框架区域条带 [【跳转到 01:59】](https://www.youtube.com/watch?v=8y0Uwwz-Kvg&t=119)，且 CDR 定义可在 **Kabat 与 IMGT 之间切换**——同一条序列在两种定义下 CDR 边界不同，后面的掩蔽也会跟着变。

## 三、Honegger 模板：把"不能动"的位点提前锁定

工具内置 **Honegger 模板** [【跳转到 02:24】](https://www.youtube.com/watch?v=8y0Uwwz-Kvg&t=144)：一份"germline 到 germline 转换时应当保持不变"的掩蔽残基清单。它源自 Anne-Marie Honegger 关于抗体核心折叠（core fold）稳定性的系列论文与 Aho 编号体系，同时考虑了**抗原呈递相关位置**与**维持 Ig 核心折叠所必需的位置** [【跳转到 02:49】](https://www.youtube.com/watch?v=8y0Uwwz-Kvg&t=169)。演示者说这套模板在真实项目里用过多次，"非常成功"。

![Honegger 模板：核心折叠稳定性与抗原呈递位点的掩蔽清单](assets/AbLead%20Antibody%20Humanization/00169.webp)

接着是父序列与各条 germline 的叠加显示：工具列出与父序列最接近的 V 区、J 区 germline（轻、重链各有）[【跳转到 03:14】](https://www.youtube.com/watch?v=8y0Uwwz-Kvg&t=194)。颜色语言贯穿全程 [【跳转到 03:39】](https://www.youtube.com/watch?v=8y0Uwwz-Kvg&t=219)：

- **品红（magenta）= M（mask，被掩蔽）**：这些位置不许改；
- **青色（cyan）= 开放修改**：这些位置才是人源化的"工作面"；
- **绿色 = 与父序列相同**：即使开放修改也不会产生突变。

这样横向扫一眼就知道：换一条 germline，哪些位置的结果会变 [【跳转到 04:04】](https://www.youtube.com/watch?v=8y0Uwwz-Kvg&t=244)——比如大多数位置在几条 germline 间完全一致，而 IMGT 13 位会随 germline 选择而不同，工程师可以据此做更精细的模板取舍。

![颜色语言：品红=掩蔽、青色=开放修改、绿色=与父序列相同](assets/AbLead%20Antibody%20Humanization/00244.webp)

## 四、三种掩蔽（exclusions）：Honegger、CDR 与自定义

**Exclusions（排除区）**决定"哪些位置开放修改"，共三个层级 [【跳转到 04:29】](https://www.youtube.com/watch?v=8y0Uwwz-Kvg&t=269)：

1. **Honegger**：品红掩蔽区与 Honegger 模板一致；
2. **CDR**：切到 CDR 掩蔽后，Honegger 的品红区域解除锁定，CDR 位置反而被锁定——即"只改框架、不动 CDR" [【跳转到 04:54】](https://www.youtube.com/watch?v=8y0Uwwz-Kvg&t=294)；
3. **Selected（自选）**：粒度最细，初始不选任何位置则全部开放，随后手动勾选想掩蔽的残基 [【跳转到 05:19】](https://www.youtube.com/watch?v=8y0Uwwz-Kvg&t=319)。

## 五、自定义掩蔽的经验法则：CDR + Vernier 残基 + DE loop

什么时候需要自定义掩蔽？演示者给出一套实战经验 [【跳转到 05:44】](https://www.youtube.com/watch?v=8y0Uwwz-Kvg&t=344)：

- 如果共晶结构能告诉你**哪些残基直接接触抗原**，可以只掩蔽它们——但接触抗原不等于功能所需：**Vernier 残基**（框架中位于 CDR 下方、支撑环构象的"底座"残基）同样决定 CDR 环的取向；
- **DE loop**（D、E β 链之间的环，有时被称为"第四 CDR"）也常常参与抗原呈递 [【跳转到 06:09】](https://www.youtube.com/watch?v=8y0Uwwz-Kvg&t=369)；
- Honegger 模板里维持 Ig 核心折叠的**内部残基，在晶体结构里根本看不到**——只看结构会漏掉它们。

最常见的偷懒做法是"**CDR + Vernier 残基**"一把梭——演示者自嘲这是"大锤（sledgehammer）"，但在缺乏结构信息时往往就是全部可用的信息 [【跳转到 06:34】](https://www.youtube.com/watch?v=8y0Uwwz-Kvg&t=394)；若手里有共晶结构，再把已知的抗原接触残基补进掩蔽集合即可 [【跳转到 06:59】](https://www.youtube.com/watch?v=8y0Uwwz-Kvg&t=419)。这套掩蔽选择同时适用于 germline 模板法与 Sapiens 法 [【跳转到 07:24】](https://www.youtube.com/watch?v=8y0Uwwz-Kvg&t=444)。

## 六、两条人源化路线：germline 模板法与 BioPhi Sapiens 法

### 6.1 BioPhi Sapiens：按掩蔽生成 AI 突变

工具栏里的"魔杖"是单点突变，而 **Suggest Mutations（建议突变）按钮调用的就是 BioPhi 的 Sapiens 方法**——一种 AI 方法，按掩蔽位置生成突变 [【跳转到 07:49】](https://www.youtube.com/watch?v=8y0Uwwz-Kvg&t=469)。口播原话点明：Sapiens 方法**默认用 CDR 做掩蔽**，而 AbLead 允许把任意掩蔽方案喂给它。这是本视频与本目录条目最直接的交点。

![Suggest Mutations 调用 BioPhi Sapiens 方法：按掩蔽生成 AI 突变](assets/AbLead%20Antibody%20Humanization/00469.webp)

### 6.2 germline 模板法：挑最近的人胚系，套用差异

演示先走经典路线 [【跳转到 08:14】](https://www.youtube.com/watch?v=8y0Uwwz-Kvg&t=494)：轻链选定与人父序列最近的 kappa germline **IGKV3-15**，工具列出将修改的位置 **1、3、9、10**，点击应用后右下角弹出绿色确认框 [【跳转到 08:47】](https://www.youtube.com/watch?v=8y0Uwwz-Kvg&t=527)；J 区检查发现仅末端一个残基不同。重链同样选 top germline，J 区五条里只有最后一位丝氨酸不同——TVSA 变 TVSS，"本该如此" [【跳转到 09:33】](https://www.youtube.com/watch?v=8y0Uwwz-Kvg&t=573)。

V、J、V、J 四处修改自动写入 **Engineering（工程）工具**：主表格出现修改标记，注释自动记为 mouse→human 修饰、分组自动挂到所选 germline [【跳转到 09:53】](https://www.youtube.com/watch?v=8y0Uwwz-Kvg&t=593)。演示者建议对同一个亲本做**多套人源化方案**，因此用 **Set（集合）**管理：先把模板法的突变存为 "hum template" 清空默认集，之后还能再存 Sapiens 法的 "hum sapiens" [【跳转到 10:05】](https://www.youtube.com/watch?v=8y0Uwwz-Kvg&t=605)。

![germline 模板法：选定 IGKV3-15 后应用 1/3/9/10 位修改](assets/AbLead%20Antibody%20Humanization/00527.webp)

回到工程工具，Select All 勾选全部修改后可以可视化突变分布：抗原呈递区大体被保留 [【跳转到 11:23】](https://www.youtube.com/watch?v=8y0Uwwz-Kvg&t=683)。随后 **Generate Combinations（生成组合）**，选定一个组合即可导出 FASTA 或直接 Build——新序列回到主表格，自动跑完主表格的所有分析 [【跳转到 12:16】](https://www.youtube.com/watch?v=8y0Uwwz-Kvg&t=736)。

![Select All 可视化突变分布：抗原呈递区大体被保留](assets/AbLead%20Antibody%20Humanization/00683.webp)

## 七、结果判定：OASis 式核查揪出 DE loop

新序列的分析结果很有意思 [【跳转到 12:42】](https://www.youtube.com/watch?v=8y0Uwwz-Kvg&t=762)：**VL 判为 human、最近 germline 也是 human；VH 判为 human，但最近 germline 却是 mouse**——为什么？

![人源化结果：VL 人源化彻底，VH 的最近 germline 仍是鼠源](assets/AbLead%20Antibody%20Humanization/00762.webp)

原因藏在 DE loop：Honegger 掩蔽下，**80、82、85、87** 四个位置从鼠源序列原样保留、未做修改 [【跳转到 13:02】](https://www.youtube.com/watch?v=8y0Uwwz-Kvg&t=782)。打开 AbLead 的 **humanness（人源性）工具**核查：确实是 DE loop 的人源性不足 [【跳转到 13:18】](https://www.youtube.com/watch?v=8y0Uwwz-Kvg&t=798)。这套核查"是在 OAS 上再查九条以上肽段的位置频率，**类似 BioPhi 的 OASis 方法**" [【跳转到 13:27】](https://www.youtube.com/watch?v=8y0Uwwz-Kvg&t=807)：点开详情可见，对最近 germline 的位置频率分析并不认可这四个位置——它们在人 germline 中的代表性很差。

![humanness 核查：DE loop 80/82/85/87 四个位置人源性不足](assets/AbLead%20Antibody%20Humanization/00807.webp)

工具当然支持当场把这四个位置改成"变体设计"，但演示者的建议是**先别动** [【跳转到 14:12】](https://www.youtube.com/watch?v=8y0Uwwz-Kvg&t=852)：DE loop 很可能参与抗原结合，改了可能掉活性——正确做法是保留它们、交给实验验证。

### 换用 Sapiens 法再跑一遍

回到人源化工具，把排除区切到 CDR、点 Suggest Mutations（BioPhi Sapiens），应用为 "hum sapiens" 突变集合 [【跳转到 14:36】](https://www.youtube.com/watch?v=8y0Uwwz-Kvg&t=876)。生成的组合比模板法**修改更少**，而且会动到 DE loop 里的位置 [【跳转到 15:08】](https://www.youtube.com/watch?v=8y0Uwwz-Kvg&t=908)——演示者点评：真实项目里他不会用"纯 CDR 掩蔽"，而会用更精细的掩蔽，这里只是为了评估工具表现。

Build 进主表格后再看 [【跳转到 15:45】](https://www.youtube.com/watch?v=8y0Uwwz-Kvg&t=945)：Sapiens 版本人源化成功，但**两条链的最近 germline 都还是 mouse**。打开 germline 分析、同时显示 human+mouse 各 10 条 [【跳转到 16:21】](https://www.youtube.com/watch?v=8y0Uwwz-Kvg&t=981)：与人最近 germline 的差异其实只有 **1.9 个百分点**——Honegger 掩蔽区加上未动的 DE loop 四个位置，正是这条序列仍被归为鼠源的主要原因 [【跳转到 16:46】](https://www.youtube.com/watch?v=8y0Uwwz-Kvg&t=1006)。

![Sapiens 版本构建完成：人源化成功但最近 germline 仍为鼠源](assets/AbLead%20Antibody%20Humanization/00945.webp)

![germline 分析：与人最近 germline 仅差 1.9 个百分点，DE loop 是主因](assets/AbLead%20Antibody%20Humanization/01006.webp)

## 八、人源化之后：liabilities 分析

收尾给出了标准后续 [【跳转到 17:11】](https://www.youtube.com/watch?v=8y0Uwwz-Kvg&t=1031)：把人源化序列送进 **liabilities（成药性隐患）分析**，修复 PTM（翻译后修饰）位点与整体稳定性问题——就像处理一条"天生人源"的序列一样；动手前要先给序列**建结构模型**，才能在序列与结构两个视图上可视化隐患位置 [【跳转到 17:29】](https://www.youtube.com/watch?v=8y0Uwwz-Kvg&t=1049)。

## 小结

- 人源化的第一个问题不是"怎么改"，而是"**哪里不许改**"：Honegger 模板、CDR、自定义三种掩蔽，粒度逐级变细；
- 经典掩蔽组合是 **CDR + Vernier 残基**，有结构信息时再补抗原接触残基；DE loop 与 Ig 核心折叠的内部残基是最容易漏掉的"暗桩"；
- **BioPhi Sapiens 方法**以掩蔽为约束生成 AI 突变（默认 CDR 掩蔽）；germline 模板法（IGKV3-15，1/3/9/10 位 + J 区 TVSA→TVSS）给出可解释的对照路线——两条路线在同一工程工具里以 Set 并行管理；
- 人源性核查用 **OAS 位置频率**（与 BioPhi OASis 同思路），能精确指出"哪些位置让这条序列仍像鼠"——本例是 DE loop 80/82/85/87；
- 与最近人 germline 只差 1.9 个百分点却仍被判鼠源：**判定阈值与功能保守之间存在权衡**，人源化设计的最后一步往往是"保留疑似功能位点、交给实验"。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| OASis | 基于 OAS（Observed Antibody Space）抗体序列库的位置频率人源性评分；视频中 AbLead 的 humanness 工具"类似 BioPhi OASis 方法" |
| Sapiens | BioPhi 平台的掩码语言模型人源化方法：按掩蔽位置提出"变得更像人"的突变建议 |
| germline | 胚系基因：未发生 V(D)J 重排与体细胞超突变的抗体"原种"序列，人源化的比对基准 |
| CDR | 互补决定区：抗体上直接接触抗原的 6 个环，人源化中默认保守不动 |
| Vernier 残基 | 框架中位于 CDR 下方、支撑 CDR 环构象的"底座"残基 |
| DE loop | D、E β 链之间的环（80–87 位附近），常称"第四 CDR"，可参与抗原接触 |
| Honegger 模板 | 基于 Aho 编号的掩蔽清单：维护 Ig 核心折叠稳定性与抗原呈递相关位置 |
| masking（掩蔽） | 指定"不允许突变"的位置集合；未被掩蔽的位置才开放人源化 |
| liabilities | 成药性隐患（PTM 位点、稳定性等），人源化之后的下一个分析环节 |
