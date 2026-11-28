# chunk 预算是 TTFT 与 ITL 之间的汇率：压小保住流式输出，放大换回首字速度

> 视频来源：[30. Chunked Prefill Explained: Smooth Streaming Under Load](https://www.youtube.com/watch?v=IyeWdVMTSY4)（YouTube · Hitesh C.）｜时长约 3 分 23 秒
> 简要导读：一支不到三分半的短片，只讲**一个旋钮**——每步的 token 预算（vLLM 里的 `max_num_batched_tokens`）——却把它讲成了本节最典型的「按场景取值」案例：预算压小保护正在看流式输出的用户，预算放大保护正在等首字的用户，两者不可能同时最优。本文按它的叙事展开，并把其中的算例（2,048 预算 / 64 个解码请求 / 32K prompt 需要 17 步）逐项核对了一遍。chunked prefill 的调度机制细节属于第 3 章，本文只把它当作「预算可切分」这个前提；TTFT 与 ITL 的测量口径见 2.1.1 与 2.1.2。

## 本讲要解决的核心问题（SCQA）

**背景**：连续批处理把 prefill 和 decode 放在同一批里算，于是 GPU 的算力被两种工作共享：prefill 一次算完整个 prompt，decode 一次只算一个 token。

**冲突**：这两种工作的**步长差了几个数量级**。一个 32,000 token 的 prompt 如果整段 prefill，那一步要比普通解码步长得多；而**所有正在跑的请求都要共享这一步**，它们的下一个 token 只能等这一步算完。用户看到的现象是：流式输出打到一半突然卡住，然后才恢复。

**疑问**：能不能既让长 prompt 进来、又不让正在看流式输出的人被冻住？如果能，代价是什么？这个代价该由谁承担？

**回答（中心思想）**：**chunked prefill 把长 prompt 切成预算大小的块，一步算一块，于是长 prompt 不再独占一整步。** 而「一块多大」由每步的 token 预算决定，这个预算就是一个**汇率**：压小 → 每步短 → 正在解码的人 ITL 好，但长 prompt 要更多步才轮到自己 → 它的 TTFT 差；放大 → 长 prompt 更快算完 → TTFT 好、吞吐高，但每步变长 → 所有正在解码的流变慢。**没有中间值能同时最优，只能按你的场景选一边。**

---

## 一、一个长 prompt 就能冻住所有人的流式输出

视频开场把问题摆得很直接：

![一个 32,000 token 的长 prompt 与 64 个正在解码的请求同时在场](assets/chunk%20预算是%20TTFT%20与%20ITL%20之间的汇率：压小保住流式输出，放大换回首字速度/00025.webp)

[【跳转到 00:25】](https://www.youtube.com/watch?v=IyeWdVMTSY4&t=25)

**「在一台繁忙的 LLM 服务器上，一个长 prompt 就能冻住其他所有用户的流式输出。」**

原因不是调度器写得差，而是连续批处理的结构决定的：

- 每一步都是**对整批做一次前向**；
- 一个解码步，对某个请求来说只处理 **1 个 token**；
- 一个 prefill 步，对某个请求来说要处理 **prompt 的全部 token**。

所以当一个 32,000 token 的 prompt 到达时，**算它的那一步比普通解码步长得多**，而所有正在跑的请求都共享这一步——它们的下一个 token 只能等。视频把这个现象命名为 **generation stall（生成停滞）**：用户看到的是流式输出中间出现一段停顿，**ITL 先尖峰、再恢复**。

这个描述值得停一下：它不是「变慢」，而是「卡一下」。对交互场景来说，卡一下比均匀地慢更难接受——因为用户会以为连接断了。

---

## 二、chunked prefill：一步算一块，而不是一口气算完

解法很朴素：

![chunked prefill：把 prompt 切成块，每步只算一块](assets/chunk%20预算是%20TTFT%20与%20ITL%20之间的汇率：压小保住流式输出，放大换回首字速度/00050.webp)

[【跳转到 00:50】](https://www.youtube.com/watch?v=IyeWdVMTSY4&t=50)

**把长 prompt 切成 token 块，每步只 prefill 一块。** 于是每一步都变成「所有正在解码的请求 + 尽可能多的待处理 prefill」，步长被压回可控范围。

这里的关键词是「尽可能多」——**能塞多少，由每步的 token 预算决定**。在 vLLM 里，这个预算就是 `max_num_batched_tokens`。

---

## 三、vLLM 的三步排法：先解码、再填 prefill、装不下就切

视频把 vLLM 的调度规则写成了三条，值得原样抄下来：

![vLLM 每步的排法：1 所有待解码请求各占 1 个 token；2 用剩余预算排 prefill；3 prefill 太大就切一块装得下的](assets/chunk%20预算是%20TTFT%20与%20ITL%20之间的汇率：压小保住流式输出，放大换回首字速度/00075.webp)

[【跳转到 01:15】](https://www.youtube.com/watch?v=IyeWdVMTSY4&t=75)

```
1 · every pending decode, 1 token each
2 · prefills with the leftover budget
3 · too big? cut a chunk that fits
```

顺序不能换：**先给每个待解码请求留 1 个 token**，剩下的预算才归 prefill。这就是「decode 优先」的含义——它保证了无论来多长的 prompt，正在解码的请求每步都能往前走一格。

接着视频给了一个可以手算的例子：

- 预算 = **2,048** token；
- 正在解码的请求 = **64** 个，各占 1 token；
- 剩余给 prefill 的预算 = $2048 - 64 = 1984$；
- 一个 32,000 token 的 prompt 需要多少步？

$$
\left\lceil \frac{32000}{1984} \right\rceil = 17
$$

**17 步。** 而在这 17 步里的**每一步**，那 64 个解码请求都在往前走。视频的原话是：**「the decodes keep moving in every one of them.」**

这个算例把「汇率」的两端同时量化了：

| | 预算 2,048 | 预算 8,192 以上 |
| --- | --- | --- |
| 32K prompt 需要的步数 | 17 步 | 约 4 步 |
| 长 prompt 的 TTFT | 差（要等 17 步） | 好 |
| 每步步长 | 短 | 长 |
| 正在解码者的 ITL | 好 | 差 |

---

## 四、切块不损失精确性

一个自然的疑问是：把一个 prefill 拆成 17 次算，结果和一次算完一样吗？

视频的回答是**完全一样**，理由一句话：

> **「Each chunk attends to the KV cache written by earlier chunks, so it matches a single prefill.」**

每一块在计算时都会去读前面几块写下的 KV Cache，所以第 $k$ 块看到的上下文，和「一次性算完前 $k$ 块」时看到的完全相同。注意力机制本来就是对着全部历史 token 算的，把历史分几次写进去，结果不变。

这一点很重要：**chunked prefill 是纯粹的调度优化，不是近似。** 它换的是时间分布，不是精度。

---

## 五、第二个收益：计算受限与访存受限挤进同一步

视频还点了第二个好处，这个好处跟延迟无关，跟利用率有关：

![prefill 块是计算受限的，decode 是访存受限的，混在同一步里两种资源都被用上](assets/chunk%20预算是%20TTFT%20与%20ITL%20之间的汇率：压小保住流式输出，放大换回首字速度/00100.webp)

[【跳转到 01:40】](https://www.youtube.com/watch?v=IyeWdVMTSY4&t=100)

**prefill 是计算受限（compute-bound）的，decode 是访存受限（memory-bound）的**，把两者放进同一个 batch，等于让 Tensor Core 和显存带宽同时忙起来——谁都不会闲着等对方。

视频在这里引了出处：**chunked prefill 与 stall-free scheduling 来自 Sarathi-Serve 这篇工作**，论文报告在 Mistral 7B 上、以 ITL 的 P99 为约束时，服务容量提升到 **2.6 倍**。

> 混合批次（hybrid batching / piggybacking）的机制细节属于 3.2，本文只把它当作「chunked prefill 的附带收益」。

---

## 六、预算就是汇率：小预算保 ITL，大预算保 TTFT

这是全片的核心一段，视频把两个方向各说了一遍：

![小预算：步长短，ITL 低](assets/chunk%20预算是%20TTFT%20与%20ITL%20之间的汇率：压小保住流式输出，放大换回首字速度/00125.webp)

[【跳转到 02:05】](https://www.youtube.com/watch?v=IyeWdVMTSY4&t=125)

- **小预算（如 2,048）**：每步短，**ITL 保持低**；但一个长 prompt 需要更多步，**它自己的 TTFT 上升**。
- **大预算（8,192 以上）**：prefill 更快算完，**TTFT 改善、吞吐提高**；代价是步长变长，**正在跑的 decode 流变慢**。

把这两句翻译成本节的语言，就是一张「按场景取值」的对照表：

| 场景 | 该往哪边走 | 为什么 |
| --- | --- | --- |
| 实时交互（人在看流式输出） | 预算压小 | 用户对「卡一下」极敏感，ITL 的 P99 是硬指标；长 prompt 的 TTFT 可以由准入策略（限制 prompt 长度）单独兜 |
| 离线批处理（没人在看） | 预算放大 | 没有流式输出要保护，长 prompt 越早算完越好；吞吐是唯一目标 |

注意这里有个反直觉的地方：**「保护 ITL」和「保护 TTFT」在同一个旋钮上是互斥的。** 很多人会想「我把预算调到一个中间值，两边都不差」——但视频的说法是「这个预算把两个延迟互相交换（trades two latencies against each other）」，它是一条**权衡线**，不是一个**最优点**。线上取哪一点，取决于你的 SLO 卡在哪一边。

---

## 七、它默认是开的，而最大的陷阱是只盯一个指标

![在 vLLM V1 引擎里，chunked prefill 默认开启](assets/chunk%20预算是%20TTFT%20与%20ITL%20之间的汇率：压小保住流式输出，放大换回首字速度/00150.webp)

[【跳转到 02:30】](https://www.youtube.com/watch?v=IyeWdVMTSY4&t=150)

视频明确说：**在 vLLM 的 V1 引擎里，chunked prefill 在所有能启用的地方都是默认开启的。** 也就是说，你不需要「开启」它，你只会**调它的预算**。

而调预算时最容易犯的错，视频用一句话点破：

> **「The common pitfall: tuning the budget against only one metric.」**

具体表现是两种对称的翻车：

- 为了修流式输出的卡顿，把预算压小 → **长 prompt 的 TTFT 爆掉**；
- 为了提吞吐，把预算放大 → **卡顿又回来了**。

所以视频给的验收方法不是「看一个数」，而是三个条件一起看：

![一起测：P99 的 ITL、TTFT、以及你自己的真实 prompt 长度](assets/chunk%20预算是%20TTFT%20与%20ITL%20之间的汇率：压小保住流式输出，放大换回首字速度/00175.webp)

[【跳转到 02:55】](https://www.youtube.com/watch?v=IyeWdVMTSY4&t=175)

1. **P99 的 inter-token latency**（不是均值——卡顿恰恰发生在尾部）；
2. **TTFT**；
3. **用你自己的真实 prompt 长度分布压测**（不是一串等长的合成请求）。

第三条最容易被忽略。预算的收益与代价都跟 prompt 长度强相关：**用短 prompt 压测，你根本测不出这个旋钮的差别。**

---

## 八、什么时候这个旋钮根本不重要

视频结尾给了一个诚实的限定条件：

> **「Chunked prefill matters most with mixed traffic.」**

- **混合流量**（长文档、检索上下文与大量流式用户同时在场）：chunked prefill 价值最大，预算怎么取也最需要斟酌；
- **只有短 prompt**：每次 prefill 本来就不大，切不切块差别很小。

这条限定其实也解释了为什么「按场景选参数」不能照抄别人的配置：**同一个参数在你的流量形态下可能根本不敏感。** 先量清楚自己的 prompt 长度分布，再决定要不要在这个旋钮上花时间。

![短片的总结页：长 prefill 会卡住同批的解码；把它切成预算大小的块；解码优先、prefill 用剩余预算；预算在 TTFT 与 ITL 之间做交换](assets/chunk%20预算是%20TTFT%20与%20ITL%20之间的汇率：压小保住流式输出，放大换回首字速度/00200.webp)

[【跳转到 03:20】](https://www.youtube.com/watch?v=IyeWdVMTSY4&t=200)

---

## 小结

- **一个长 prompt 能冻住所有人的流式输出**，因为连续批处理让所有请求共享同一步，而 prefill 步比解码步长几个数量级。
- **chunked prefill 一步算一块**，每块读前面块写下的 KV Cache，所以**结果与一次算完完全相同**，是纯调度优化。
- **排法固定三步**：先给每个待解码请求 1 个 token，剩余预算排 prefill，装不下就切一块装得下的。2,048 预算 + 64 个解码 → 剩 1,984 → 32K prompt 需要 17 步，而 17 步里解码一直在走。
- **附带收益是利用率**：prefill 计算受限、decode 访存受限，同批混跑两种资源都不闲；Sarathi-Serve 报告在 ITL 的 P99 约束下容量提升 2.6 倍。
- **预算是汇率不是最优点**：压小保 ITL、放大保 TTFT 与吞吐，两者互斥；取哪一边取决于 SLO 卡在哪一侧。
- **V1 默认开启**，你能调的只有预算；最大的陷阱是只盯一个指标调，必须把 P99 ITL、TTFT 与真实 prompt 长度分布放在一起测。
- **只有短 prompt 时这个旋钮不重要**——先量清自己的流量形态，再决定要不要调。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| chunked prefill | 把长 prompt 切成 token 块，每步只 prefill 一块，与解码同批 |
| token 预算（budget） | 每步允许处理的 token 总数，vLLM 里是 `max_num_batched_tokens` |
| generation stall | 长 prefill 独占一步导致所有解码请求停顿，表现为流式输出卡一下 |
| ITL / inter-token latency | 相邻两个输出 token 之间的间隔；决定流式输出顺不顺 |
| TTFT | 从发请求到第一个 token 出现的时间；决定「反应快不快」 |
| decode 优先调度 | 每步先给所有待解码请求各 1 个 token，剩余预算才给 prefill |
| stall-free scheduling | Sarathi-Serve 提出的调度方式，用 chunked prefill 消除 prefill 造成的停顿 |
| compute-bound / memory-bound | 受算力限制 / 受显存带宽限制；prefill 与 decode 各占一边 |
| 混合流量（mixed traffic） | 长 prompt（文档、检索上下文）与大量短请求流式输出同时到达的负载形态 |