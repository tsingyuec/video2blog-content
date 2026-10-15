# CLS 池化 vs 均值池化：用 recall@K 实测，为检索任务选出更合适的句子向量

> 来源：YouTube 视频《CLS Pooling vs Mean Pooling in Python: Compare Semantic Search Recall》（Professor Py: AI Foundations，[DiTUHmqS2WI](https://www.youtube.com/watch?v=DiTUHmqS2WI)，时长 06:52）。
> 本文基于视频字幕与画面逐窗口整理而成，配图取自视频截图，时间戳可跳回原视频对应位置核对。
> 系列定位：上一节讲了 SBERT 用 Mean Pooling 或 [CLS] 把逐词向量变成句子向量；本视频用一段可复现的 Python 实验，演示**怎么在具体任务上判断两种池化谁更好**。它也正好回应了 `return_per_token` 这类参数背后的取舍：逐 token 向量是模型的原生输出，但检索这类序列级任务必须先池化再比。

## 本讲要解决的核心问题（SCQA）

**背景**：Transformer 编码器会把一句话变成**几百个 token 向量**（每个 token 一个），模型的原生输出就是这个粒度。

**冲突**：语义检索（比如帮助中心搜索：把一个短问题匹配到正确的帮助文章）需要的是**每句一个紧凑向量**——逐 token 向量没法直接两两比较。

**疑问**：把 token 向量压缩成句子向量时，取第一个特殊标记（CLS 池化）好，还是对句中所有有效 token 取平均（均值池化）好？

**回答（中心思想）**：没有普适答案——正确做法是**实测**：用同一个编码器（all-MiniLM-L6-v2）构造两种句子向量，在一个带标注的小检索集上用 **recall@K**（召回率@K）实测哪种池化能找回更多相关文档，选召回更高的那种。一般经验：为句子嵌入训练过的模型，均值池化常是强默认；若模型被训练成把句义放进第一个 token，CLS 可能更好。**不要假设任何一种规则处处赢**。

[![视频开篇：CLS vs Mean——transformer 返回几百个 token 向量，而检索需要每句一个向量](assets/CLS%20Pooling%20vs%20Mean%20Pooling%20in%20Python：%20Compare%20Semantic%20Search%20Recall/00005.webp)](https://www.youtube.com/watch?v=DiTUHmqS2WI&t=5)

## 一、实验设置：一个带标注的小检索集

[【跳转到 00:15】](https://www.youtube.com/watch?v=DiTUHmqS2WI&t=15)

场景是帮助中心搜索工具：把一个短问题匹配到正确的文章。实验构造了 3 篇文档（`docs`）、3 个查询（`queries`），并给出 `gold` 标注——每个查询对应哪篇文档是「已知正确答案」。这样比较两种池化时，靠的是**标注的标准答案**，而不是「某个邻居看起来好像合理」。

[![实验数据：3 篇文档、3 个查询、gold 标注，以及统一走 PoolingRecall_Pipeline 的对比流程](assets/CLS%20Pooling%20vs%20Mean%20Pooling%20in%20Python：%20Compare%20Semantic%20Search%20Recall/00015.webp)](https://www.youtube.com/watch?v=DiTUHmqS2WI&t=15)

编码器用 **all-MiniLM-L6-v2** 检查点，两种池化实验**共享同一个 token 编码器**——这是公平对比的关键：唯一的变量是池化规则，而不是模型。文档加查询共 9 条文本，规模虽小但结构完整，足以支撑一次受控对比（真实场景中它可以代表帮助中心的查询与文章）。

[![加载 all-MiniLM-L6-v2 作为两种池化实验共享的 token 编码器](assets/CLS%20Pooling%20vs%20Mean%20Pooling%20in%20Python：%20Compare%20Semantic%20Search%20Recall/00085.webp)](https://www.youtube.com/watch?v=DiTUHmqS2WI&t=85)

> 视频作者提醒：这段代码的目的是把核心思想讲清楚，库版本与本地环境可能不同，实际运行遇到差异请查官方文档。

## 二、先拿到逐 token 向量：encoder 输出与 attention mask

[【跳转到 01:50】](https://www.youtube.com/watch?v=DiTUHmqS2WI&t=110)

文本就绪后，先看编码器给了什么：

```python
features = encoder(encoder.preprocess(texts))
tokens = features["token_embeddings"]
mask   = features["attention_mask"]
```

`encoder.preprocess` 负责构建模型输入，编码器则产出 **token embeddings** 和 **attention mask**，一并存放在 `features` 里。此时**每个（填充后的）token 位置都有一个向量**——这是三维的张量（批次 × token × 维度），语义检索没法把它当作「每句一个向量」来直接比较，所以**还差一步池化**。

[![编码器输出 token_embeddings 与 attention_mask：掩码区分真实 token 与填充位置](assets/CLS%20Pooling%20vs%20Mean%20Pooling%20in%20Python：%20Compare%20Semantic%20Search%20Recall/00130.webp)](https://www.youtube.com/watch?v=DiTUHmqS2WI&t=130)

两个细节值得注意：

- **attention mask** 区分真实 token 与填充（padding）——句子长短不一时，这决定了哪些向量该参与池化；
- `torch.no_grad()` 让这次纯推理过程不记录梯度。

输出显示批次、token、向量三个维度，以及第一个文本的 **7 个有效位置**（真实 token 数）。

## 三、两种池化：CLS 取第一个，均值池化取平均

[【跳转到 02:57】](https://www.youtube.com/watch?v=DiTUHmqS2WI&t=177)

同一份 token 输出，用两种方式压缩：

```python
dim = encoder.get_embedding_dimension()
cls_pool  = Pooling(dim, pooling_mode="cls")
mean_pool = Pooling(dim, pooling_mode="mean")
cls_out  = cls_pool(dict(features))["sentence_embedding"]
mean_out = mean_pool(dict(features))["sentence_embedding"]
```

- **CLS pool**：直接取**第一个 token 的表示**（特殊标记 [CLS] 的向量）；
- **mean pool**：用存在 `features` 里的 attention mask，**组合所有有效 token 的表示**（取平均）。

代码里给每种池化传**独立的字典副本**，防止一次池化调用改写掉另一个的结果；再用 `util.normalize` 把两种句子向量都归一化成**单位长度**，余弦相似度比较就很直接了。两种策略都把每句压成 **384 维**，但取值所强调的信息可能不同。

[![同一份 token 输出分别做 CLS 池化与均值池化：pooling_mode="cls" 与 "mean" 的关键代码](assets/CLS%20Pooling%20vs%20Mean%20Pooling%20in%20Python：%20Compare%20Semantic%20Search%20Recall/00182.webp)](https://www.youtube.com/watch?v=DiTUHmqS2WI&t=182)

## 四、检索：同一个查询，两种排序

[【跳转到 04:00】](https://www.youtube.com/watch?v=DiTUHmqS2WI&t=240)

现在有了**两个嵌入空间**（CLS 版和 mean 版）。检索步骤把池化后的张量切片分回文档向量与查询向量（**不需要重新编码文本**），然后分别用 `util.semantic_search` 排序——它默认使用余弦相似度，为每个查询返回语料库中 top-2 的索引。

只看第一个查询就能发现：**即使两种池化给出的结果都相关，邻居的排序也可能不同**——池化方式确实改变了检索行为。调 `top_k` 也讲究：调大能覆盖更多相关文档，但返回列表更长；调小则测试更严格。不过，**邻居顺序只能用肉眼看个大概，真正能下结论的是带标注的检索质量**。

[![用 util.semantic_search 分别在 CLS 与 mean 两个嵌入空间里检索，比较邻居排序](assets/CLS%20Pooling%20vs%20Mean%20Pooling%20in%20Python：%20Compare%20Semantic%20Search%20Recall/00245.webp)](https://www.youtube.com/watch?v=DiTUHmqS2WI&t=245)

## 五、用 recall@K 裁决

[【跳转到 04:51】](https://www.youtube.com/watch?v=DiTUHmqS2WI&t=291)

这段代码衡量的是：哪种池化规则**检回了更多带标注的相关文档**。

**recall@K 的算法**：把 `util.semantic_search` 每行结果里的 `corpus_id` 集合，与 `gold` 标注求交集，再除以标注数；最后对所有查询**取平均的找回比例**。

```python
def recall_at_k(hits):
    scores = []
    for row, want in zip(hits, gold):
        got = {hit["corpus_id"] for hit in row}
        scores.append(len(got & want) / len(want))
    return sum(scores) / len(scores)
```

作者强调：这比「因为 CLS 排第一所以选它」或「因为 mean 常用所以选它」**更有依据**。`scores` 把两种测量放在一起，`winner` 报告更高的那个结果，同时保留诚实的平局可能。更大的评估集会让结论更可靠，但评估流程不变。当团队有几千篇支持文章时，同样的对比就更重要了。

[![recall_at_k 函数：检索结果与 gold 标注求交集，按查询平均找回比例](assets/CLS%20Pooling%20vs%20Mean%20Pooling%20in%20Python：%20Compare%20Semantic%20Search%20Recall/00296.webp)](https://www.youtube.com/watch?v=DiTUHmqS2WI&t=296)

## 六、结论：均值池化常是强默认，但不要照搬

[【跳转到 05:46】](https://www.youtube.com/watch?v=DiTUHmqS2WI&t=346)

- **均值池化**：对为句子嵌入而训练的模型，通常是一个强默认选项；
- **CLS 池化**：当模型被训练成「把句子的意义放进第一个 token」时，可能更好；
- **不要假设任何一种规则处处赢**——编码器、语料、查询、评估标签，都要与真实的搜索体验保持一致。

这个小实验展示的核心思想是：**token 嵌入还不是句子嵌入，池化决定了语义检索能召回什么**。recall 衡量的是结果是否包含「你的标注认为重要」的文档。试着改变检索条数 K：更大的 K 可能找回更多相关文档，但也让用户面对更长的结果列表。

[![小结画面：token 嵌入还不是句子嵌入，池化决定语义检索能召回什么](assets/CLS%20Pooling%20vs%20Mean%20Pooling%20in%20Python：%20Compare%20Semantic%20Search%20Recall/00346.webp)](https://www.youtube.com/watch?v=DiTUHmqS2WI&t=346)

视频结尾还给了两个进阶方向：重排序（re-ranking）相似度分数，或构造更好的评估集。

## 小结

- 编码器的原生输出是**逐 token 向量**，检索需要**每句一个向量**——中间必须做池化（这正是 `return_per_token` 类参数两种取值各自服务的场景）；
- **CLS 池化**取第一个特殊标记的向量，**均值池化**按 attention mask 对所有有效 token 取平均；两者都把句子压成同一维度（384 维）的向量，但强调的信息不同；
- 对比实验的控制变量：**同一个编码器**（all-MiniLM-L6-v2）、同一批文本、只有池化规则不同；
- 裁决标准用 **recall@K**：检回的文档与 gold 标注求交集、按查询平均——比「凭习惯选池化」更有依据；
- 经验法则：为句子嵌入训练的模型**均值池化常是强默认**；模型若被训练成把句义放进第一个 token，**CLS 可能更好**；别假设任何一种处处赢；
- 归一化（unit length）+ 余弦相似度是句子向量比较的标准姿势。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| token embedding（逐 token 嵌入） | 编码器给每个 token 位置输出的向量，模型的原生输出粒度 |
| 池化（pooling） | 把多个 token 向量压缩成一个句子级向量的操作 |
| CLS 池化（CLS pooling） | 直接取第一个特殊标记 [CLS] 的向量作为句子表示 |
| 均值池化（mean pooling） | 按 attention mask 对所有有效 token 向量取平均作为句子表示 |
| attention mask | 标记哪些位置是真实 token、哪些是填充，池化时只组合有效位置 |
| recall@K（召回率@K） | 检回的前 K 条结果中，命中标注相关文档的比例，按查询平均 |
| `util.semantic_search` | sentence-transformers 的检索函数，默认余弦相似度，返回 top-k |
| `util.normalize` | 把向量归一化成单位长度，使余弦相似度等价于点积 |
