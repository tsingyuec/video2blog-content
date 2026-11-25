# Sentence-BERT 的三种池化：mean、max 与 CLS 如何决定句向量

> 视频来源：[101-句子相似度判断（Sentence-BERT）-自然语言处理-深度学习-pytorch](https://www.bilibili.com/video/BV1ud4y1o7km/)（Bilibili · 凯文）｜时长约 12 分钟
> 导读：这是一支偏实操的短课，用 Sentence-Transformers 的代码把"句子怎么变成一个向量"这件事走了一遍：为什么不能拿两个句子直接喂 BERT、孪生结构怎么搭、池化层的三个开关（mean / max / CLS）分别是什么、训练用什么损失、训完效果差多少。本文按"动机 → 结构 → 池化三选一 → 训练 → 结果"重排，字幕中的错拼（如 bt → BERT、pulling → pooling）已订正。

## 本讲要解决的核心问题（SCQA）

**背景**：BERT 和 RoBERTa 在文本相似度上已经达到了 SOTA（state of the art，即该任务当前最先进的结果）[【跳转到 00:25】](https://www.bilibili.com/video/BV1ud4y1o7km/?t=25)。最自然的用法是把两句话拼起来喂进 BERT，让它输出一个匹配判断。

**冲突**：这样做代价太大。每比较一对句子就要完整跑一次 BERT，如果库里有一万条候选、每次查询都要比一万次，计算成本无法接受 [【跳转到 00:50】](https://www.bilibili.com/video/BV1ud4y1o7km/?t=50)。

**疑问**：能不能先给每个句子算好一个向量存起来，查询时只做向量之间的余弦相似度？如果可以，一个变长的句子该怎么压成一个定长向量？

**回答（中心思想）**：Sentence-BERT 的做法是**孪生结构 + 池化**：两个句子各自过同一个 BERT，各自经过池化层压成一个句向量，再比较两个向量。池化有三种可选方式——**mean（对 token 输出取平均）、max（取各维最大值）、CLS（直接取 `[CLS]` 位置）**，视频里选的是 mean [【跳转到 08:20】](https://www.bilibili.com/video/BV1ud4y1o7km/?t=500)。这样句子可以离线编码、预先建库，查询时只算向量距离，从而"大幅缩短时间成本"，同时保持精确度的稳定性 [【跳转到 01:40】](https://www.bilibili.com/video/BV1ud4y1o7km/?t=100)。

---

## 一、为什么需要"句向量"这一层

### 1.1 两种结构的代价差异

视频用一张图把两种做法并排放 [【跳转到 02:30】](https://www.bilibili.com/video/BV1ud4y1o7km/?t=150)：

- **经典 BERT**：`[CLS] 句子1 [SEP] 句子2 [SEP]` 拼成一条序列，一次前向得到一个判断。两句话在编码器内部**逐 token 交互**，精度高，但每换一个候选就要重跑一次。
- **Sentence-BERT**：句子 A 和句子 B 分别过 BERT，各自池化出向量 $u$、$v$，再对 $(u, v, \lvert u-v \rvert)$ 接分类器，或者直接算 $\cos(u,v)$。

![左边是经典 BERT 把两句话拼进同一序列、只在 CLS 上判断；右边是 Sentence-BERT 让两句话各自过 BERT、各自池化出向量 u 和 v 再比较](assets/Sentence-BERT%20的三种池化：mean、max%20与%20CLS%20如何决定句向量/00150.webp)

这张图就是本小节的要害：**左边保留了 token 级的交互，右边把每句话压成了一个向量**。压成向量之后才能离线算，代价是交互信息没了。

### 1.2 孪生结构不是 Sentence-BERT 独有的

视频特意指出，这种"左右两边共用一套参数"的孪生网络有很多应用 [【跳转到 02:55】](https://www.bilibili.com/video/BV1ud4y1o7km/?t=175)：

- **图片搜索**：输入一张照片转成向量，和库里的图逐一算相似度，取最近的；
- **问答**：把用户问题转成向量，在候选答案库里找距离最近的；
- 以及相似度对比、聚类、语义检索这些任务 [【跳转到 02:05】](https://www.bilibili.com/video/BV1ud4y1o7km/?t=125)。

共同点是：**先把对象编码成向量，再在向量空间里比距离**。所以"怎么编码"（池化）直接决定了后面所有检索的质量。

---

## 二、池化层：三种把变长压成定长的办法

### 2.1 三种方式的定义

视频把池化讲得很直白 [【跳转到 08:20】](https://www.bilibili.com/video/BV1ud4y1o7km/?t=500)：BERT 输出的是每个 token 一个向量，池化就是"把你的 token 输出变成一个向量"：

$$
\mathbf{e}_{\text{mean}} = \frac{1}{L}\sum_{i=1}^{L}\mathbf{h}_i,
\qquad
\mathbf{e}_{\text{max}} = \max_{i=1..L}\mathbf{h}_i \ \text{(逐维)},
\qquad
\mathbf{e}_{\text{cls}} = \mathbf{h}_{\text{CLS}}
$$

- **mean**：把所有 token 向量的平均值当作句子向量 [【跳转到 08:45】](https://www.bilibili.com/video/BV1ud4y1o7km/?t=525)；
- **max**：每个维度取所有 token 上的最大值；
- **CLS**：直接用 `[CLS]` 这个位置输出的向量代表整句。

三种方式的差别，本质是**"哪些 token 的信息被保留"**：

| 池化 | 保留了什么 | 丢掉了什么 |
| :--- | :--- | :--- |
| mean | 全部 token 的平均贡献，长度归一 | 语序、组合结构；稀有 token 被稀释 |
| max | 每个维度上最"强"的激活 | 有多少 token 支持这个特征；平均强度 |
| CLS | 一个专门位置的聚合结果 | 所有具体 token 的贡献，且依赖该位置被训练成摘要 |

### 2.2 代码里就是三个开关

在 Sentence-Transformers 里，池化不是自己写的，而是 `Pooling` 模块的三个布尔开关 [【跳转到 07:55】](https://www.bilibili.com/video/BV1ud4y1o7km/?t=475)：

```python
word_embedding_model = models.Transformer(model_name)
pooling_model = models.Pooling(
    word_embedding_model.get_word_embedding_dimension(),
    pooling_mode_mean_tokens=True,
    pooling_mode_cls_token=False,
    pooling_mode_max_tokens=False,
)
model = SentenceTransformer(modules=[word_embedding_model, pooling_model])
```

![代码中通过 pooling_mode_mean_tokens / pooling_mode_cls_token / pooling_mode_max_tokens 三个开关选择池化方式，本例只开启 mean](assets/Sentence-BERT%20的三种池化：mean、max%20与%20CLS%20如何决定句向量/00475.webp)

三个开关可以同时开——同时开就会把几种池化的结果拼接起来，维度翻倍。视频里只开了 mean，这也是 Sentence-BERT 论文与后续大多数模型默认的选择。

### 2.3 为什么默认选 mean

视频没有展开论证，但从池化的定义可以直接看出理由：mean 对**所有 token 一视同仁**，不依赖某个特殊位置是否被训练好，也不会像 max 那样只留下最强的激活。代价是它把句子压成了"加权词袋"——平均之后语序信息基本消失，这也是为什么"我喜欢这家餐厅"和"我不喜欢这家餐厅"的句向量会非常接近。

---

## 三、训练：孪生结构 + 余弦相似度损失

### 3.1 数据长什么样

训练数据是成对的句子加一个相似度标签：`sentence1`、`sentence2`、`label`，从 csv 读进来后包装成 `InputExample` [【跳转到 09:35】](https://www.bilibili.com/video/BV1ud4y1o7km/?t=575)。

### 3.2 损失与训练循环

视频用的损失是 `CosineSimilarityLoss`：它把两个句向量的余弦相似度去拟合标签值 [【跳转到 10:00】](https://www.bilibili.com/video/BV1ud4y1o7km/?t=600)。训练时还会挂一个 `EmbeddingSimilarityEvaluator` 在验证集上算相关性，用来挑模型 [【跳转到 07:30】](https://www.bilibili.com/video/BV1ud4y1o7km/?t=450)。

```python
train_dataloader = DataLoader(train_samples, shuffle=True, batch_size=train_batch_size)
train_loss = losses.CosineSimilarityLoss(model=model)
evaluator = EmbeddingSimilarityEvaluator.from_input_examples(dev_samples, name='sts-dev')
warmup_steps = math.ceil(len(train_dataloader) * num_epochs * 0.1)  # 10% 数据做 warmup
model.fit(train_objectives=[(train_dataloader, train_loss)],
          evaluator=evaluator, epochs=num_epochs,
          evaluation_steps=1000, warmup_steps=warmup_steps,
          output_path=model_save_path)
```

注意这里有一个隐含前提：**训练时两个句子是分别编码的**（孪生），所以同一套池化参数在两侧共享。池化的选择一旦定下，训练就是在教"池化之后的向量该长什么样"。

### 3.3 效果：21% → 71%

视频给出的结果是：直接用预训练模型，测试正确率 21%；用 10 万个例子训练、4 个 epoch 之后，正确率能到 71% [【跳转到 10:50】](https://www.bilibili.com/video/BV1ud4y1o7km/?t=650)。

![训练前后对比：直接使用预训练模型正确率 21%，训练 10 万个例子、4 个 epoch 后达到 71%](assets/Sentence-BERT%20的三种池化：mean、max%20与%20CLS%20如何决定句向量/00650.webp)

这个差距说明：**池化本身不产生语义，它只是把 token 级表示搬运到句级**。未经训练时，池化后的向量方向是各向异性的、不适合直接算余弦；训练（用相似度标签做监督）做的事情，是把这个"池化 + 编码"的组合调整到余弦相似度真的对应语义相似。

---

## 四、用起来：编码、建库、检索

训练好之后，整个流程只有三步 [【跳转到 05:00】](https://www.bilibili.com/video/BV1ud4y1o7km/?t=300)：

```python
from sentence_transformers import SentenceTransformer
import scipy.spatial

embedder = SentenceTransformer('bert-base-chinese')
corpus = ['这是一段话', '关节置换术', '中国首都是哪里']
corpus_embeddings = embedder.encode(corpus)      # 离线：每句一个向量
query_embeddings = embedder.encode(['心脏手术', '中国的首都在哪里'])

for query, query_embedding in zip(queries, query_embeddings):
    distances = scipy.spatial.distance.cdist([query_embedding], corpus_embeddings, "cosine")[0]
    results = zip(range(len(distances)), distances)
    for idx, distance in sorted(results, key=lambda x: x[1]):
        print(corpus[idx].strip(), "(Score: %.4f)" % (1 - distance))
```

![用 encode 把语料和查询各自编码成向量，再用 scipy 的余弦距离排序取 Top-K，这就是"离线编码 + 在线比对"的检索流程](assets/Sentence-BERT%20的三种池化：mean、max%20与%20CLS%20如何决定句向量/00350.webp)

视频里举的例子很直观："心脏手术"应该和"关节置换术"相似度更高，"中国首都在哪里"应该和"天安门"更近，和"铅笔"没什么相似度 [【跳转到 05:50】](https://www.bilibili.com/video/BV1ud4y1o7km/?t=350)。注意 `encode` 只跑一次前向，之后所有比较都是向量运算——这就是把粒度从 token 级压到句级换来的收益。

---

## 小结

- 句向量存在的理由是**离线编码**：两句话拼进一个 BERT 每对都要重跑，成本无法接受；各自编码成向量后，比较退化成一次余弦计算。
- 池化是把 token 级 `[B, L, H]` 压成 `[B, H]` 的那一步，Sentence-BERT 提供 mean、max、CLS 三种，代码里就是三个布尔开关。
- 三者的差别在于保留了什么：mean 保留全部 token 的平均贡献但抹平语序；max 只留每维最强激活；CLS 依赖单个位置。
- 池化本身不产生语义，训练才是让"池化后的向量"与语义相似度对齐的环节：同一份代码，21% → 71%。
- 池化的代价是组合信息：平均之后句子接近加权词袋，否定、语序这类信息很难保留。要保住它们，就得回到 token 级或片段级去做交互。

## 关键术语速查

| 术语 | 一句话解释 |
| :--- | :--- |
| SOTA | state of the art，该任务当前最先进的结果 |
| 孪生网络 | 左右两个分支共享同一套参数的编码结构，用于把两个输入映射到同一空间 |
| 池化（pooling） | 把变长的 token 向量序列压成一个定长向量的操作 |
| mean pooling | 对全部 token 向量取平均，最常用的句向量取法 |
| max pooling | 逐维取所有 token 上的最大值 |
| CLS pooling | 直接取 `[CLS]` 位置的输出作为句子向量 |
| 表示型模型 | 先各自编码成向量、再比较向量距离的结构，可离线计算 |
| 交互型模型 | 两个输入进同一编码器做 token 级交互的结构，精度高但必须在线计算 |
| CosineSimilarityLoss | 让两个句向量的余弦相似度去拟合标签值的训练损失 |