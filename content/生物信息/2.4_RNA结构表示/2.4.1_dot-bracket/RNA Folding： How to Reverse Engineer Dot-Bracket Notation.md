# 读懂 dot-bracket：从一行括号还原 RNA 二级结构

> 视频来源：[RNA Folding: How to Reverse Engineer Dot-Bracket Notation](https://www.youtube.com/watch?v=5S34lgNbRxI&t=0)（YouTube · Nikolay's Genetics Lessons）
> 本文基于视频演说图文稿整理，配图截自视频。

## 本讲要解决的核心问题（SCQA）

**背景**：上一讲（同频道前作）我们学会了把 RNA 二维结构图"翻译"成 dot-bracket 记法——配对写 `(` / `)`，不成对写 `.`。

**冲突**：会写了，但反过来呢？拿到别人给的一行点与括号，怎么把它画回二维结构图？另外，结构图上那些环和茎，正式名称都是什么？

**疑问**：有没有一套通用的"读法"，见字符就能落笔画图？

**回答（中心思想）**：有。先认全六种常见模体的名字（发夹环、内环、凸环、多分支环、茎、假结），再逐位扫描 dot-bracket：**点照抄、`(` 是配对开始、`)` 是配对关闭——看到 `)` 就意味着 RNA 在此处回折**；扫完把配对连上线，二维结构就画出来了。讲者最后强调：dot-bracket 是双向可行的紧凑表示，几乎不占存储空间。 [【跳转到 07:30】](https://www.youtube.com/watch?v=5S34lgNbRxI&t=450)

---

## 一、先认全六种模体的名字 [【跳转到 00:25】](https://www.youtube.com/watch?v=5S34lgNbRxI&t=25)

在开始逆向还原之前，讲者先给图上的各种"形状"起了名字：

- **发夹环（hairpin loop）**：茎的顶端拐回来的环； [【跳转到 00:50】](https://www.youtube.com/watch?v=5S34lgNbRxI&t=50)
- **内环（internal loop）**与**凸环（bulge loop）**：茎中间"鼓开"的地方——内环两侧都不配对，凸环只有一侧多出未配对的碱基； [【跳转到 01:15】](https://www.youtube.com/watch?v=5S34lgNbRxI&t=75)
- **多分支环（multibranched loop）**：汇聚了至少三条分支的环； [【跳转到 01:15】](https://www.youtube.com/watch?v=5S34lgNbRxI&t=75)
- **茎（stem）**：连续配对形成的双链区； [【跳转到 01:40】](https://www.youtube.com/watch?v=5S34lgNbRxI&t=100)
- **假结（pseudoknot）**：两个环通过配对连在一起——讲者特别说明，这种结构不算茎。 [【跳转到 02:05】](https://www.youtube.com/watch?v=5S34lgNbRxI&t=125)

![发夹环：茎的顶端拐回来的环](assets/RNA%20Folding：%20How%20to%20Reverse%20Engineer%20Dot-Bracket%20Notation/00050.webp)

![内环、凸环与多分支环](assets/RNA%20Folding：%20How%20to%20Reverse%20Engineer%20Dot-Bracket%20Notation/00075.webp)

![茎：连续配对形成的双链区](assets/RNA%20Folding：%20How%20to%20Reverse%20Engineer%20Dot-Bracket%20Notation/00100.webp)

![假结：两个环通过配对相连](assets/RNA%20Folding：%20How%20to%20Reverse%20Engineer%20Dot-Bracket%20Notation/00125.webp)

## 二、逆向还原例一：逐位扫描 [【跳转到 02:30】](https://www.youtube.com/watch?v=5S34lgNbRxI&t=150)

图例沿用上一讲：**点 = 不配对，括号 = 配对**。讲者拿两段不同的 dot-bracket 做演示，先看第一段。

它的开头是 5 个不成对的核苷酸（5 个点），随后是 4 个参与配对的核苷酸。 [【跳转到 02:55】](https://www.youtube.com/watch?v=5S34lgNbRxI&t=175)

读法要点（讲者边写边说）：

- 点照抄；括号区就是茎，成对的碱基逐个连起来； [【跳转到 03:20】](https://www.youtube.com/watch?v=5S34lgNbRxI&t=200)
- **看到括号关闭，意味着 RNA 在此处回折、沿反方向折回自身**——这是逆向还原最关键的一步； [【跳转到 03:45】](https://www.youtube.com/watch?v=5S34lgNbRxI&t=225)
- 扫描继续：1 个不成对、4 个成对、2 个不成对……直到结尾； [【跳转到 04:10】](https://www.youtube.com/watch?v=5S34lgNbRxI&t=250)
- 最后把所有配对连上线，不成对的保持"悬空"，结构图就完成了。 [【跳转到 04:35】](https://www.youtube.com/watch?v=5S34lgNbRxI&t=275)

画完之后标注模体：这个结构包含**发夹环、内环，以及两条茎**。 [【跳转到 05:00】](https://www.youtube.com/watch?v=5S34lgNbRxI&t=300)

![例一完成：标注出发夹环、内环与两条茎](assets/RNA%20Folding：%20How%20to%20Reverse%20Engineer%20Dot-Bracket%20Notation/00300.webp)

## 三、逆向还原例二：更密集的括号 [【跳转到 05:25】](https://www.youtube.com/watch?v=5S34lgNbRxI&t=325)

第二行开头就有 10 个参与配对的核苷酸——讲者从 1 数到 10，把它们逐个标出。 [【跳转到 05:25】](https://www.youtube.com/watch?v=5S34lgNbRxI&t=325)

继续扫描：随后 3 个点之后括号关闭，说明又到了一个回折点，RNA 在此折回自身；接下来是 3 个成对、5 个不成对、4 个成对…… [【跳转到 05:50】](https://www.youtube.com/watch?v=5S34lgNbRxI&t=350) [【跳转到 06:15】](https://www.youtube.com/watch?v=5S34lgNbRxI&t=375)

再往后：1 个不成对、3 个成对、1 个不成对，边扫边把配对连上。 [【跳转到 06:40】](https://www.youtube.com/watch?v=5S34lgNbRxI&t=400) [【跳转到 07:05】](https://www.youtube.com/watch?v=5S34lgNbRxI&t=425)

最终标注：**一个发夹环、三条茎，以及两处凸环**。 [【跳转到 07:05】](https://www.youtube.com/watch?v=5S34lgNbRxI&t=425)

![例二完成：一个发夹环、三条茎与两处凸环](assets/RNA%20Folding：%20How%20to%20Reverse%20Engineer%20Dot-Bracket%20Notation/00450.webp)

## 四、双向可行，而且极其紧凑 [【跳转到 07:30】](https://www.youtube.com/watch?v=5S34lgNbRxI&t=450)

讲者总结（也是本讲结论）：

- **正向**：二维结构 → dot-bracket（上一讲演示）；
- **逆向**：dot-bracket → 二维结构（本讲演示）；
- dot-bracket 是一种**紧凑的**存储方式：喂给计算机、存在计算机里都几乎不占存储空间，程序可以轻松读取和再处理。 [【跳转到 07:55】](https://www.youtube.com/watch?v=5S34lgNbRxI&t=475)

## 小结

- 六种模体先认名字：发夹环 / 内环 / 凸环 / 多分支环 / 茎 / 假结；
- 读法口诀：**点照抄，`(` 起茎，`)` 回折**——扫完连线即成图；
- dot-bracket ↔ 二维结构双向互逆，一行文本就能在计算机里完整保存一张结构图。

上一篇（正向：图 → 记法）见 [RNA Folding： How to Use Dot-Bracket Notation](RNA%20Folding：%20How%20to%20Use%20Dot-Bracket%20Notation.md)。
