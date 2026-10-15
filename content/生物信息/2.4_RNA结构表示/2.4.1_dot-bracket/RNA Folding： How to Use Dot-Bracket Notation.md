# dot-bracket 记法：把 RNA 二级结构写成一行 `((((....))))`

> 视频来源：[RNA Folding: How to Use Dot-Bracket Notation](https://www.youtube.com/watch?v=cmUXCvuTwyY&t=0)（YouTube · Nikolay's Genetics Lessons）
> 本文基于视频演说图文稿整理，配图截自视频。

## 本讲要解决的核心问题（SCQA）

**背景**：RNA 链会折叠出二级结构——哪些碱基互相配对、哪些悬空，画出来是一张带茎和环的二维图。人看图很直观。

**冲突**：计算机没法直接"看图"。讲者指出：虽然如今的计算机也能处理图片，但在生物信息学起步的年代，科学家必须把这张图转成计算机能理解的东西，才能存储和计算。 [【跳转到 02:05】](https://www.youtube.com/watch?v=cmUXCvuTwyY&t=125)

**疑问**：只靠一行字符，怎么可能完整描述"谁和谁配了对"？

**回答（中心思想）**：dot-bracket（点-括号）记法。规则只有两条：**配对的碱基 = 一对互相匹配的 `(` 与 `)`；未配对的碱基 = `.`**。一行字符串就能完整记录 RNA 的二维折叠，计算机据此可以重建二维结构，进而走向三维结构预测。 [【跳转到 04:10】](https://www.youtube.com/watch?v=cmUXCvuTwyY&t=250)

---

## 一、第一步：把二维图"拉直"成序列

每个 RNA 分子都有 5' 端和 3' 端。要把二维结构变成线性形式，就从 5' 端开始，把图上的碱基逐个抄下来。 [【跳转到 00:25】](https://www.youtube.com/watch?v=cmUXCvuTwyY&t=25)

本例抄出的序列是（共 15 个核苷酸）： [【跳转到 00:50】](https://www.youtube.com/watch?v=cmUXCvuTwyY&t=50)

```
5'- A C U G A U C G U A G U C A C -3'
```

![原始的 RNA 二维结构图：带茎与环](assets/RNA%20Folding：%20How%20to%20Use%20Dot-Bracket%20Notation/00000.webp)

## 二、第二步：数位置，找出"谁和谁配对"

有了线性序列，每个碱基就有了位置编号。讲者逐对确认，并在图上把配对的两者"桥接"起来：

- 第 1 位的 A 与第 12 位的 U 配对——他现场从 1 数到 12 来确认位置； [【跳转到 01:15】](https://www.youtube.com/watch?v=cmUXCvuTwyY&t=75)
- 第 2 位的 C 配第 11 位的 G；第 3 位的 U 配第 10 位的 A； [【跳转到 01:40】](https://www.youtube.com/watch?v=cmUXCvuTwyY&t=100)
- 第 4 位的 G 配第 9 位的 U——最后一对。 [【跳转到 02:05】](https://www.youtube.com/watch?v=cmUXCvuTwyY&t=125)

剩下第 5–8 位（A、U、C、G）找不到任何伙伴——它们就是茎顶端拐出来的那个环。

![数位置找配对：把第 1 位 A 与第 12 位 U 桥接起来](assets/RNA%20Folding：%20How%20to%20Use%20Dot-Bracket%20Notation/00075.webp)

## 三、第三步：逐位写下点与括号

从 5' 端开始逐位扫描，边看配对边写：

1. **配对的开始 → `(`**。第 1 位的 A 在记法里就像一个开括号（讲者用绿色高亮标出）；第 2、3、4 位同样，共 4 个 `(`。 [【跳转到 02:30】](https://www.youtube.com/watch?v=cmUXCvuTwyY&t=150)
2. **没有伙伴 → `.`**。环上的 A、U、C、G 写成 4 个点。 [【跳转到 02:55】](https://www.youtube.com/watch?v=cmUXCvuTwyY&t=175)
3. **配对的结束 → `)`**。与开括号呼应，写下 4 个闭括号。 [【跳转到 03:20】](https://www.youtube.com/watch?v=cmUXCvuTwyY&t=200)
4. **3' 端尾巴 → `.`**。末尾的 C、A、C 也不配对，写成 3 个点；讲者顺手用它标出 3' 端。 [【跳转到 03:45】](https://www.youtube.com/watch?v=cmUXCvuTwyY&t=225)

![dot-bracket 从第 1 个开括号写起（绿色高亮处）](assets/RNA%20Folding：%20How%20to%20Use%20Dot-Bracket%20Notation/00150.webp)

![环区的 A U C G 写成 4 个点](assets/RNA%20Folding：%20How%20to%20Use%20Dot-Bracket%20Notation/00175.webp)

![3' 端尾巴写成 3 个点](assets/RNA%20Folding：%20How%20to%20Use%20Dot-Bracket%20Notation/00225.webp)

最终得到：

```
((((....))))...
```

4 个 `(` + 4 个 `.` + 4 个 `)` + 3 个 `.` = 15 个字符，与 15 个核苷酸一一对应。 [【跳转到 04:10】](https://www.youtube.com/watch?v=cmUXCvuTwyY&t=250)

![最终的 dot-bracket 字符串：配对用匹配括号、未配对用点](assets/RNA%20Folding：%20How%20to%20Use%20Dot-Bracket%20Notation/00250.webp)

## 四、这一行字符为什么有价值

规则再总结一遍：**碱基配对可以编码为一对匹配的开括号与闭括号；未配对的核苷酸用点表示**。 [【跳转到 04:10】](https://www.youtube.com/watch?v=cmUXCvuTwyY&t=250)

有了这个格式，计算机就能拿它继续工作：先重建出二维结构，再进一步得到三维结构。本讲的例子很简单，讲者预告后续视频会换更复杂的 RNA 结构来练习这套记法。 [【跳转到 04:35】](https://www.youtube.com/watch?v=cmUXCvuTwyY&t=275) [【跳转到 00:00】](https://www.youtube.com/watch?v=cmUXCvuTwyY&t=0)

## 小结

- dot-bracket 把"图"翻译成了"字"：`(` 与 `)` 一一对应表示配对，`.` 表示不成对；
- 三步流程：**拉直成序列 → 数位置找配对 → 逐位写点与括号**；
- 它是 RNA 序列与结构计算之间的桥梁：计算机读取这行字符，即可重建二维、进而预测三维结构。

下一篇（同频道续集）走相反方向：拿到一行 dot-bracket，如何把它还原成二维结构图，以及各种环与茎的正式名称——见 [RNA Folding： How to Reverse Engineer Dot-Bracket Notation](RNA%20Folding：%20How%20to%20Reverse%20Engineer%20Dot-Bracket%20Notation.md)。
