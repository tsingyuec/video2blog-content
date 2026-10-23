# 查准 ontology term 的关键是限定物种、读定义并核对层级

> 视频：[Searching for an Ontology Term using Ontology Lookup Service](https://www.youtube.com/watch?v=I8m3oCyDyiQ)（Zebrafish Toxicology Phenotype Atlas Project，5:06，2026）

## 本讲要解决的核心问题（SCQA）

**背景**：做实验、写论文、提交补充表时，经常需要给一个生物概念附上稳定的 **ontology term ID**，让别人能准确知道你指的是什么。

**冲突**：同一个概念往往有多种叫法；直接搜一个词，可能没有 exact match（完全匹配），只得到一堆候选；不同物种、不同模型又各自有专门的本体，搜错本体就会拿到错误的 ID。

**疑问**：在 OLS4 里，怎样从几个关键词走到一个可以放心引用的 term ID？

**回答（中心思想）**：**加上物种/模型限定 → 看搜索结果预览和定义 → 进术语页核对同义词与层级 → 复制 ID**；如果找不到合适的术语，或者发现术语需要修改，就去本体主页找 maintainer 的 GitHub issue tracker。

![OLS4 首页：输入关键词，建议同时带上物种或模型](assets/Searching%20for%20an%20Ontology%20Term%20using%20Ontology%20Lookup%20Service/00027.webp)

## 一、为什么用一个 ID，而不是一个词？

在论文里写“jaw”看起来很清楚，但对数据库来说，`jaw` 可能对应多个物种、多个解剖结构，甚至同一结构的不同发育阶段。用一个稳定的 term ID 有三个好处：

1. **跨数据集可对齐**：别人拿到你的 ID，就知道你指的是哪个本体里的哪个概念；
2. **可复现**：审稿人、读者可以顺着 ID 回到原始定义，而不是猜你的用词；
3. **可进入补充表**：很多期刊要求把 ontology ID 写进正文或 supplementary table，方便索引和复用。

所以目标不是“搜到一个看起来对的词”，而是“找到一个 ID，并确认它确实对应我要表达的概念”。

## 二、搜索：关键词 + 物种/模型限定

演示从 OLS4 首页开始 [【跳转到 00:27】](https://www.youtube.com/watch?v=I8m3oCyDyiQ&t=27)。讲者输入的关键词是 **zebrafish jaws**（斑马鱼的颌）。

这里有一个很实用的建议：**尽量把物种或模型写进关键词**。原因是同一个解剖结构在不同物种里有不同的本体，例如：

- 斑马鱼有 Zebrafish Anatomy Ontology（ZFA）；
- 人类、小鼠等也各有自己的解剖学本体；
- 如果不限定物种，搜索结果会把多个本体的术语混在一起。

输入后，页面会给出一个**搜索结果预览** [【跳转到 00:52】](https://www.youtube.com/watch?v=I8m3oCyDyiQ&t=52)。预览里可能没有 exact match，但会列出若干匹配术语。每条结果旁边有一个绿色图标，表示它来自哪个本体（这里是 ZFA），后面跟着 term ID。

![搜索 zebrafish jaws 的预览：没有 exact match，但给出候选术语、本体 ID 和 term ID](assets/Searching%20for%20an%20Ontology%20Term%20using%20Ontology%20Lookup%20Service/00052.webp)

此时有两条路：

- 如果预览里已经看到明显匹配的术语，直接点进去；
- 如果候选太多，点 **search OLS4** 进入完整结果页，逐个看定义再筛选。

预览里每个术语下面都会带定义。讲者强调：**不要只看词名，要看定义**。同一个词在不同本体里可能指不同东西，定义是区分它们的关键。

## 三、术语页：定义、同义词、层级

讲者点进了 **mandibular arch skeleton**（下颌弓骨骼）这个术语 [【跳转到 01:17】](https://www.youtube.com/watch?v=I8m3oCyDyiQ&t=77)。术语页从上到下提供了几层信息。

### 3.1 ID 与定义

页面顶部给出 term ID 和定义。这个 ID 就是之后要写进论文或补充表的东西。

![术语页顶部：ID、定义，以及同义词列表](assets/Searching%20for%20an%20Ontology%20Term%20using%20Ontology%20Lookup%20Service/00077.webp)

### 3.2 同义词：确认“同一个概念的另一种叫法”

往下滚动会看到 **synonyms（同义词）** 列表 [【跳转到 01:57】](https://www.youtube.com/watch?v=I8m3oCyDyiQ&t=117)。这个例子里，`jaw` 和 `jaws` 被标为 **exact synonyms**（完全同义词）。

这意味着：`jaw`、`jaws` 和 `mandibular arch skeleton` 是同一个概念的不同叫法，指向**同一个 ID**。对使用者来说，这解决了一个常见困惑：

> 我搜的是 “jaw”，为什么结果叫 “mandibular arch skeleton”？

因为它们是 exact synonyms；用哪个词搜索都应该能落到同一个术语上。

![jaw / jaws 被标为 exact synonyms，说明它们和 mandibular arch skeleton 指向同一个概念](assets/Searching%20for%20an%20Ontology%20Term%20using%20Ontology%20Lookup%20Service/00117.webp)

### 3.3 层级树：确认它是不是我要的那个“层级”

继续往下是 **hierarchical tree（层级树）** [【跳转到 02:33】](https://www.youtube.com/watch?v=I8m3oCyDyiQ&t=153)。这个例子里：

- `mandibular arch skeleton` 被归类在 **splanchnocranium**（脏颅）下面；
- 所以它是 splanchnocranium 的 **child term**（子术语），表示更具体的概念；
- 反过来，splanchnocranium 是它的 **parent term**（父术语），表示更宽泛的概念；
- 点开父术语旁边的箭头，还能看到和它并列的其他术语，这些叫 **sibling terms**（兄弟术语）。

![层级树：mandibular arch skeleton 是 splanchnocranium 的子类，同级还有兄弟术语](assets/Searching%20for%20an%20Ontology%20Term%20using%20Ontology%20Lookup%20Service/00153.webp)

这一步很关键：**同义词只能告诉你“叫法”，层级才能告诉你“位置”**。如果你要的是“整个颌部”而不是“颌骨”，就要在树里往上或往下确认，避免选到过窄或过宽的概念。

### 3.4 复制 ID

确认术语后，点击页面上的 **copy** 按钮 [【跳转到 03:31】](https://www.youtube.com/watch?v=I8m3oCyDyiQ&t=211)，就能把 term ID 复制到剪贴板。之后可以：

- 写进论文正文；
- 写进 supplementary table；
- 贴到实验记录或数据库提交表单里。

![复制按钮把 term ID 复制到剪贴板，方便写进论文或补充表](assets/Searching%20for%20an%20Ontology%20Term%20using%20Ontology%20Lookup%20Service/00211.webp)

## 四、找不到或需要修改：找 maintainer

实际使用中还有两种情况：

1. 搜不到合适的 term；
2. 找到了 term，但发现定义、同义词或层级有错误。

这时不要自己“造一个 ID”，也不要随便套一个相近的术语。正确做法是联系本体的维护者。

OLS 里的多数本体都通过 **GitHub issue tracker** 接收社区反馈 [【跳转到 03:56】](https://www.youtube.com/watch?v=I8m3oCyDyiQ&t=236)。操作路径是：

1. 在术语页点击绿色的本体主页按钮；
2. 本体主页上有 **homepage** 和 **issue tracker** 两个入口；
3. 点 issue tracker，会跳到该本体的 GitHub 仓库（这里是 ZFA）[【跳转到 04:21】](https://www.youtube.com/watch?v=I8m3oCyDyiQ&t=261)；
4. 在仓库里新建 issue，说明你要请求新增术语、修改定义，还是报告错误。

![本体主页提供 homepage 与 issue tracker 入口](assets/Searching%20for%20an%20Ontology%20Term%20using%20Ontology%20Lookup%20Service/00236.webp)

![通过 GitHub issue 向本体维护者报告错误或请求修改](assets/Searching%20for%20an%20Ontology%20Term%20using%20Ontology%20Lookup%20Service/00261.webp)

讲者还提醒：如果还不熟悉 GitHub，可以看视频说明里 note 8 附的 GitHub 教程链接，先学会怎么建 issue。

## 五、把流程串起来

一次可靠的 OLS4 查词，可以固化成下面五步：

1. **写清概念 + 物种/模型**：例如 `zebrafish jaws`，不要只写 `jaws`；
2. **看预览，不急着点第一条**：确认候选来自正确的本体（绿色图标 + 本体名）；
3. **读定义**：确保它描述的就是你要表达的概念；
4. **核对同义词和层级**：确认叫法一致，且粒度（父/子）合适；
5. **复制 ID 并记录来源**：在论文/补充表里同时保留 ID 和本体名，方便别人复查。

如果第 2–4 步有任何一步对不上，就回到搜索结果换一个候选，或者去 issue tracker 请求维护者补充。

## 小结

- **OLS4 查词的目标不是“搜到词”，而是“拿到一个可引用的 term ID”**。
- **搜索时带上物种/模型**，能显著减少跨本体混淆；预览里没有 exact match 是正常的，重点看候选和定义。
- **术语页要三看**：看定义确认含义，看同义词确认叫法，看层级确认粒度。
- **exact synonym 表示同一概念的不同叫法**，例如 jaw / jaws / mandibular arch skeleton 指向同一个 ID。
- **层级树里的 parent / child / sibling** 帮你判断术语是太宽还是太窄。
- **找不到或发现错误时，走本体主页 → issue tracker → GitHub issue**，不要自己造 ID。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| ontology term | 本体里的一个概念节点，例如 mandibular arch skeleton |
| term ID | 术语的稳定标识符，写论文/补充表时引用 |
| exact match | 搜索词与术语 label 完全一致；没有 exact match 不代表没有合适术语 |
| exact synonym | 与术语完全等价的另一种叫法，例如 jaw / jaws |
| parent term | 更宽泛的父术语，例如 splanchnocranium |
| child term | 更具体的子术语，例如 mandibular arch skeleton |
| sibling term | 同一个父术语下的并列术语 |
| ontology browser | 浏览、搜索本体的工具，OLS4 就是其中之一 |
| issue tracker | 本体维护者接收新增/修改/错误报告的入口，通常是 GitHub Issues |
