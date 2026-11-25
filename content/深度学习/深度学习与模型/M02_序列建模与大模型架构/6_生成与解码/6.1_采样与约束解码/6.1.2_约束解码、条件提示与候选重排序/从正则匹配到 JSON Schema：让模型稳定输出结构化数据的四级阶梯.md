# 从正则匹配到 JSON Schema：让模型稳定输出结构化数据的四级阶梯

> 视频来源：[让 AI 回传可靠的 JSON｜Structured Output 教学｜JSON Schema](https://www.bilibili.com/video/BV1nKHe6XEXL/)（Bilibili · CodingStartup起码课）｜时长约 8 分钟
> 导读：这支视频不先讲原理，而是拿一个「茶餐厅点单」的小网页做实验台，从最脆弱的「用正则解析模型说的话」一路升级到「用 JSON Schema + strict 约束解码」，每一级都给出真实的失败次数。本文按这四级阶梯整理，最后落在视频反复强调的一句话上：schema 保证的是形状，不是内容。

## 本讲要解决的核心问题（SCQA）

**背景**：我们让语言模型把一句自然语言（「两杯冻柠茶少甜，一个菠萝油加牛油，外卖」）整理成点菜纸。程序看不懂一句话，它要的是**数据**：一个 `items` 清单，每项有名称、数量和备注，再加一个 `true` / `false` 表示是否外卖 [【跳转到 00:05】](https://www.bilibili.com/video/BV1nKHe6XEXL/?t=5)。

**冲突**：模型回给我们的是一段**自由文本**，而自由文本的形状每次都不一样。你可以为昨天的写法写一个正则表达式，但明天模型把备注挪到乘号前面，正则就静默地匹配不到那一行——不报错，只是单错了 [【跳转到 01:47】](https://www.bilibili.com/video/BV1nKHe6XEXL/?t=107)。就算让它输出 JSON，key 叫什么、分几层，仍然由模型自己决定。

**疑问**：从「解析模型说的话」到「让模型只能说出合法的话」，中间要跨过哪几级台阶？每一级的可靠性到底差多少？

**回答（中心思想）**：视频给出的四级阶梯是——**解析纯文本 → 叫它用 JSON → 给它看一个例子 → 用 JSON Schema 规定形状**。前三级都是在「请求」模型配合，只有第四级把约束下沉到**解码阶段**：API 只允许模型挑选那些能让回覆保持合格的 token，所以形状才有保证。但即使到了第四级，**schema 保证的是形状，不是内容**，业务值仍然要自己校验 [【跳转到 07:13】](https://www.bilibili.com/video/BV1nKHe6XEXL/?t=433)。

![程序要的不是一句话而是一份数据：items 清单（name/qty/note）加 takeaway 布尔值，右边是最终渲染出的点菜纸](assets/从正则匹配到%20JSON%20Schema：让模型稳定输出结构化数据的四级阶梯/00030.webp)

---

## 一、第一级：用正则去解析模型说的话

最初的实现最朴素：在 JavaScript 里用 `fetch` 呼叫 API，system message 只写「整理客人的点单」，模型回一段纯文字——先写外卖，然后每项一行，一个 dash、名称、一个乘号、再加数量 [【跳转到 01:02】](https://www.bilibili.com/video/BV1nKHe6XEXL/?t=62)。人看很容易明白，但程序要的是分开的名称和数字。

于是写一个正则：一个 dash、任意文字、一个乘号、再加数字；每 match 到一行就变成一个 item [【跳转到 01:27】](https://www.bilibili.com/video/BV1nKHe6XEXL/?t=87)。

![正则解析器：把「- 凍檸茶 × 2（少甜）」这样的行拆成 name 与 qty，再用 includes 判断是否外卖](assets/从正则匹配到%20JSON%20Schema：让模型稳定输出结构化数据的四级阶梯/00107.webp)

执行一次，单看起来完全正确：两杯冻柠茶、一个菠萝油、外卖。但再按一次按钮，同一张单、同一段程序，这次模型把备注写在了乘号前面，pattern 就 match 不到那一行，两杯冻柠茶无声无息地消失了——**没有 error，只是单错了**。

视频作者连跑 6 次，结果是：2 张单完整，2 张少了冻柠茶，还有 2 张完全空白 [【跳转到 02:08】](https://www.bilibili.com/video/BV1nKHe6XEXL/?t=128)。原因很直接：大模型是有随机性的，同一个问题每次的写法都可能不同，而每一种新写法都可能破坏你为旧写法写的 pattern [【跳转到 02:13】](https://www.bilibili.com/video/BV1nKHe6XEXL/?t=133)。

这就是第一级台阶的本质：**你在为一种具体的文本写法写解析器，而模型每次都在换写法**。

## 二、第二级：「请用 JSON 回覆」只是把解析变简单，没有把形状定下来

既然文本形状不稳定，那就让模型直接给结构化数据。在 system message 加一句「用 JSON 回覆」，整个 parser 就变成一行 `JSON.parse` [【跳转到 02:32】](https://www.bilibili.com/video/BV1nKHe6XEXL/?t=152)。

`JSON.parse` 本身没问题，问题在 key 上。模型把单分成了「饮品」和「食物」，还用中文 key，根本没有 `items` 这个 key，所以在 `items` 上呼叫 `map` 就出现 `TypeError: Cannot read properties of undefined`。更隐蔽的是：badge 写着堂食，但客人明明说了外卖——模型把这条信息写在它自己改的 key 里，程序读 `takeaway` 得到 `undefined`，而 `undefined` 就被当作 `false` [【跳转到 02:46】](https://www.bilibili.com/video/BV1nKHe6XEXL/?t=166)。

![同样是合法 JSON，但 key 是模型自己起的：饮品/食物、品项/数量/甜度，程序读 items 与 takeaway 全部落空](assets/从正则匹配到%20JSON%20Schema：让模型稳定输出结构化数据的四级阶梯/00166.webp)

连跑 8 次的结果：清单出现了 4 个不同的名称，数量有 2 个，`takeaway` 一次都没有出现过，5 次 `TypeError`，另外 3 次数量显示 `undefined` [【跳转到 03:11】](https://www.bilibili.com/video/BV1nKHe6XEXL/?t=191)。

视频在这里给了一句很关键的判断：**其实 model 很懂 JSON，它只是不知道我们要什么 key，因为我们从来没有告诉它** [【跳转到 03:16】](https://www.bilibili.com/video/BV1nKHe6XEXL/?t=196)。JSON 语法只是「格式」，字段名和层级是「约定」，而约定必须由调用方给出。

## 三、第三级：给一个例子，把「请求」变成「看得见的规范」

那就告诉它。system message 里加一个例子，正正是我们要的形状：`items`，每一项有 `name`、`qty` 和 `note`，再加 `takeaway` 的 `true` / `false` [【跳转到 03:38】](https://www.bilibili.com/video/BV1nKHe6XEXL/?t=218)。

![system message 里直接写「只用 JSON 回覆，例如：」并给出一段真实填充的样例](assets/从正则匹配到%20JSON%20Schema：让模型稳定输出结构化数据的四级阶梯/00231.webp)

这次换一位新客人（一杯热奶茶，顺便问有没有素食），用真实 API 请求试了 12 次，**每一次都能 parse** [【跳转到 03:51】](https://www.bilibili.com/video/BV1nKHe6XEXL/?t=231)。

所以写得好的 prompt 大部分时间都可行。但它始终只是一个**请求**：照不照做是 model 自己选择，回覆到达 `JSON.parse` 之前，没有任何人帮你检查 [【跳转到 04:00】](https://www.bilibili.com/video/BV1nKHe6XEXL/?t=240)。12 次全对说明概率很高，不说明**一定**对——这正是提示（prompting）与约束（constraining）的分界线：前者提高成功率，后者改变可能性空间。

## 四、第四级：用 JSON Schema 描述形状，用 strict 把约束放进解码

要保证一个形状，首先要**准确地描述**它。视频用 JSON Schema 来描述（也就是上一集描述工具参数的那种写法）[【跳转到 04:18】](https://www.bilibili.com/video/BV1nKHe6XEXL/?t=258)：

- 最外层 `type` 是 `object`；
- 有一个 property 叫 `items`，`type` 是 `array`，数组里每一项都是 `object`；
- 每一项里 `name` 是字符串，数量叫 `qty` 是整数，`note` 也是字符串；
- `required` 列出必须有的栏位；
- `additionalProperties` 设为 `false`，就是不准有其他 key；
- 最后 `takeaway` 的 `type` 是 `boolean`，即只可以是 `true` 或 `false`。

外面一层也是同样两条规则，整份合约 22 行就写完 [【跳转到 04:43】](https://www.bilibili.com/video/BV1nKHe6XEXL/?t=283)。

![JSON Schema 逐层描述形状：object → items 数组 → 每项 object（name/qty/note）→ required 与 additionalProperties](assets/从正则匹配到%20JSON%20Schema：让模型稳定输出结构化数据的四级阶梯/00283.webp)

然后把它送出去：system message 变回简单的一行，request body 加一个新栏位 `response_format`，`type` 是 `json_schema`，有一个名称，`strict` 设为 `true`，再带上我们的 schema [【跳转到 05:09】](https://www.bilibili.com/video/BV1nKHe6XEXL/?t=309)。

![请求体里的 response_format：type 为 json_schema，name 为 order，strict 为 true，schema 直接引用前面定义的常量](assets/从正则匹配到%20JSON%20Schema：让模型稳定输出结构化数据的四级阶梯/00312.webp)

### 4.1 strict 到底改了什么

差别在解码。model 是一个一个 token 写出回覆的：平时，下一个 token 可以是任何东西；但有了 strict schema，API **只会让它选令回覆保持合格的 token** [【跳转到 05:22】](https://www.bilibili.com/video/BV1nKHe6XEXL/?t=322)。所以它不能用一句客套话开头，不能用文字写数量，也不能自己编一个 key 出来。

![模型逐个 token 写回覆的示意：平时候选可以是「好的！」「以下是」「```」「{」，加了 strict 之后这些分支被排除](assets/从正则匹配到%20JSON%20Schema：让模型稳定输出结构化数据的四级阶梯/00330.webp)

这就是**约束解码（constrained decoding）**在 API 层面的样子：约束不是写在 prompt 里的一句嘱咐，而是在每一步把不合法的候选从可选集合里剔出去。用式子写，就是给第 $t$ 步的 logits 加一个掩码 $m_t$：

$$
\text{logits}'_t = \text{logits}_t + m_t,\qquad m_t[i] = \begin{cases} 0, & i \in \mathcal{A}(s_t) \\ -\infty, & i \notin \mathcal{A}(s_t) \end{cases}
$$

其中 $s_t$ 是「已经生成的前缀」在 schema 对应的状态机里所处的状态，$\mathcal{A}(s_t)$ 是该状态下合法的 token 集合。softmax 之后非法项的概率是 $e^{-\infty}=0$，永远不会被采样到。效果立刻可见——同一张单执行 3 次，3 个回覆一模一样，`items` 有 `name`、`qty` 和 `note`，`takeaway` 是 `true`，每一次单都正确；换一张单（一个餐蛋面、一杯热奶茶走甜），形状还是一样 [【跳转到 05:44】](https://www.bilibili.com/video/BV1nKHe6XEXL/?t=344)。

### 4.2 strict mode 的硬性要求：每个字段都必须出现在 required 里

视频特别提醒一个很常见的错误：在 strict mode 里，**每一个 property 都必须放入 `required`**。如果漏了 `note`，API 会拒绝整个 request，返回 `Error 400, missing note`。所以每个栏位都放入 `required`，没有备注就用空字符串 [【跳转到 06:06】](https://www.bilibili.com/video/BV1nKHe6XEXL/?t=366)。

![strict mode 下的 schema 片段：required 必须列全 name/qty/note，additionalProperties 设为 false](assets/从正则匹配到%20JSON%20Schema：让模型稳定输出结构化数据的四级阶梯/00366.webp)

这条限制看起来繁琐，其实正是「形状被锁死」的代价：`required` 全列 + `additionalProperties: false`，等于把对象允许出现的 key 集合完全确定下来，解码器才能据此算出每一步的合法 token 集合。

## 五、schema 保证的是形状，不是内容

第四级台阶也有它管不到的地方。视频用两张单说明：同一张餐蛋面单，有一次回覆是「热奶茶 / 备注：走甜」，另一次是「奶茶 / 备注：热、走甜」——**两个都合格，但只有一个对得上你的餐牌** [【跳转到 06:25】](https://www.bilibili.com/video/BV1nKHe6XEXL/?t=385)。

![两张单都「符合 schema」，但左边 name 是「熱奶茶」、右边是「奶茶」：形状合格不等于语义正确](assets/从正则匹配到%20JSON%20Schema：让模型稳定输出结构化数据的四级阶梯/00397.webp)

第二个例子更能说明约束的边界：客人问「有没有素食」，但 schema 根本没有位置放一条问题。有一次这条信息直接消失了，另外两次被塞进了 `note` [【跳转到 06:43】](https://www.bilibili.com/video/BV1nKHe6XEXL/?t=403)。

由此得到两条工程结论：

1. **程序依赖的值都要检查**，例如名称对不对得上餐牌——这属于业务校验，schema 管不了；
2. **需要什么数据，就在 schema 加一个栏位**——约束只能保住「你描述过的形状」，你没想到的字段，模型只能塞到别处或者丢掉。

另外，使用前记得确认你的 model 支持 structured outputs [【跳转到 07:08】](https://www.bilibili.com/video/BV1nKHe6XEXL/?t=428)。

## 六、四级阶梯放在一起看

| 级别 | 做法 | 谁在保证 | 视频里的实测 | 失效方式 |
| --- | --- | --- | --- | --- |
| 1 | 正则解析自由文本 | 无，靠 pattern 覆盖 | 6 次里 2 次完整 | 写法一变就静默漏行 |
| 2 | 提示「用 JSON 回覆」 | 模型的指令遵循 | 8 次里 5 次 TypeError | key 名与层级由模型自定 |
| 3 | 提示 + 一个填充范例 | 模型的指令遵循（更强） | 12 次全部可 parse | 仍是请求，无强制力 |
| 4 | JSON Schema + strict | 解码器逐步过滤候选 | 3 次回覆完全一致 | 形状对、内容可能错 |

这张表也解释了为什么「提示」和「约束」不能互相替代：提示便宜、通用、能表达语义偏好（比如「备注要写甜度」），但它只提高概率；约束昂贵、只认形式语言能描述的东西（类型、必填、枚举、嵌套），但它把概率变成 0 或 1。真实系统里两者是叠加使用的——**用提示说清要什么，用 schema 锁死长什么样，用业务校验兜住内容对不对**。

## 小结

- 解析自由文本注定失败：模型每次换写法，你的正则就静默漏数据，而且不报错。
- 「请用 JSON」只解决了语法，没解决约定：key 叫什么、分几层，模型会自己发明。
- 给一个真实填充的范例能显著提高成功率（视频里 12/12），但本质仍是请求，不是保证。
- JSON Schema 把形状写成机器可读的合约：类型、必填、禁止额外 key，22 行就能锁死一个对象。
- `response_format: {type: "json_schema", strict: true}` 把这份合约送进解码阶段，模型只能在保持合格的 token 里选，因此形状稳定。
- strict mode 要求每个 property 都进 `required`，缺字段会直接 400；没有值就用空字符串。
- schema 保证形状不保证内容：名称对不对、客人额外提的问题放哪，仍然要靠业务校验与 schema 设计。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| JSON Schema | 用 JSON 写的一份「数据形状合约」：字段名、类型、必填、是否允许额外 key |
| `response_format` | 聊天接口里声明输出格式的栏位，`type: "json_schema"` 表示按给定 schema 输出 |
| `strict: true` | 让服务端在解码阶段强制遵守 schema，而不是只在提示里请求 |
| `additionalProperties: false` | 禁止出现 schema 未声明的 key，把对象的键集合完全定死 |
| 约束解码 | 在每一步生成时只保留合法 token，把非法候选排除出采样空间 |
| structured outputs | 厂商对「按 schema 输出」这一能力的叫法，底层即约束解码 |
| 静默失败 | 解析器没报错但结果错了，例如漏掉一行菜，比抛异常更危险 |