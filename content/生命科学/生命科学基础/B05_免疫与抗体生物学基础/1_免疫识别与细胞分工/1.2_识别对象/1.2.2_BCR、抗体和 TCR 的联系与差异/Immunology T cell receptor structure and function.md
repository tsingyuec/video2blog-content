# T 细胞受体（TCR）：与抗体同源的另一种抗原受体，信号机器更精细

> 视频来源：[Immunology: T cell receptor structure and function](https://www.youtube.com/watch?v=uq9p26JAnCs&t=0)（YouTube · 免疫学课堂讲座），时长约 10 分钟。
> 本文基于视频演说图文稿整理，配图截自视频。

## 本讲要解决的核心问题（SCQA）

**背景**：适应性免疫有两大类抗原受体。读完抗体相关内容我们已经知道：抗体/BCR 由重链 + 轻链组成，有 V/C 区、靠 V(D)J 重组等机制产生多样性。TCR 看起来很像"膜结合版的抗体"——同样有抗原结合位点、可变区，同样带着糖基修饰。

**冲突**：但 TCR 毕竟不是抗体：它的基因座组成、多样性的规模、信号传递方式都与抗体不同；而且 TCR 自身的胞内段很短，识别抗原之后，激活信号要靠一整组辅助分子接力才能传进细胞核。

**疑问**：TCR 与抗体究竟哪里同源、哪里不同？识别抗原后信号如何传入胞内？

**回答（中心思想）**：TCR 是 α/β 异二聚体——**β 链同源重链、α 链同源轻链**；V(D)J 重组、连接多样性等机制照常运作，唯独没有体细胞超突变，且可选基因片段更多，**总多样性比抗体高约 5 个数量级**；识别后由 CD3（ε/γ/δ）与 ζ 等亚基组成 **TCR-CD3 复合体**接力传信号——比 BCR 只用一对 Igα/Igβ 更复杂，因而调节更精细。

## 一、TCR 与抗体：高度同源的"表亲"

讲者开篇就把 TCR 和 BCR/抗体放在一起对比：两者在**结构和功能上都高度同源**——都有抗原结合位点、都结合抗原；区别只是一个可溶（抗体）、一个锚在膜上（受体）；都有可变区，也都带着糖基 [【跳转到 00:08】](https://www.youtube.com/watch?v=uq9p26JAnCs&t=8)。

![TCR 与抗体/BCR 的同源对比：都有抗原结合位点与可变区](assets/Immunology%20T%20cell%20receptor%20structure%20and%20function/00008.webp)

链的对应关系看这张配色示意图最直观 [【跳转到 00:33】](https://www.youtube.com/watch?v=uq9p26JAnCs&t=33)：

- **β 链 ≈ 抗体的重链**（基因上同源）；
- **α 链 ≈ 抗体的轻链**。

![颜色配对图：β 链同源重链、α 链同源轻链](assets/Immunology%20T%20cell%20receptor%20structure%20and%20function/00033.webp)

## 二、多样性：机制相同、可选片段更多，总多样性高约 5 个数量级

BCR 那套多样性产生机制**几乎全部适用于 T 细胞**，唯一例外是**体细胞超突变（somatic hypermutation）在 T 细胞中不发生**；连接多样性、体细胞重组、剪接机制都照常运作 [【跳转到 01:03】](https://www.youtube.com/watch?v=uq9p26JAnCs&t=63)。

基因座的差别也能从同源关系推出来 [【跳转到 01:28】](https://www.youtube.com/watch?v=uq9p26JAnCs&t=88)：

- **β 链**（同源重链）有 **V、D、J** 三种基因片段；
- **α 链**（同源轻链）只有 **V、J** 两种片段。

![α 链与 β 链基因座：β 有 V/D/J，α 只有 V/J](assets/Immunology%20T%20cell%20receptor%20structure%20and%20function/00088.webp)

把 TCR 与免疫球蛋白放在一起逐项对比 [【跳转到 01:59】](https://www.youtube.com/watch?v=uq9p26JAnCs&t=119)：

- **V 片段**：α、β TCR 的可变片段都比免疫球蛋白多得多；
- **D 片段**：重链的 D 片段比 β 链略多；α 链没有（同源轻链）；
- **J 片段**：TCR 有 **61 个** J 片段，而 κ/λ 轻链只有 4～5 个（平均约 4.5 个）；连接处还会插入 N/P 核苷酸，进一步增加连接多样性 [【跳转到 02:24】](https://www.youtube.com/watch?v=uq9p26JAnCs&t=144)；
- **D 片段三读框阅读**：在 TCR 中很少见，讲者留到 B 细胞重链部分再讲。

![TCR 与免疫球蛋白的基因片段数量对比](assets/Immunology%20T%20cell%20receptor%20structure%20and%20function/00119.webp)

把这些乘在一起：抗体的总多样性本已很大（讲者强调这些都是近似数字），而 **TCR 的总多样性比抗体还要高出约 5 个数量级** [【跳转到 02:49】](https://www.youtube.com/watch?v=uq9p26JAnCs&t=169)。

![总多样性对比：TCR 约为免疫球蛋白的 10^5 倍](assets/Immunology%20T%20cell%20receptor%20structure%20and%20function/00169.webp)

## 三、逐链拆解：V/C 区与 3 个高变环

先看整体：TCR 上有**抗原识别/结合位点**，由 α、β 两条链组成；免疫球蛋白旁有 Igα/Igβ 辅助信号，TCR 旁对应的是 **CD3 分子**，功能类似 [【跳转到 03:19】](https://www.youtube.com/watch?v=uq9p26JAnCs&t=199)。

![TCR 整体结构：抗原结合位点 + α/β 链 + 旁侧 CD3](assets/Immunology%20T%20cell%20receptor%20structure%20and%20function/00199.webp)

接着按链拆解 [【跳转到 06:01】](https://www.youtube.com/watch?v=uq9p26JAnCs&t=361)。每条链分两段：**C 末端**与 **N 末端**。讲者用"三个 C"记 C 末端：**C**arboxyl（羧基端）、**C**onstant（恒定）、**C**onserved（保守）——这就是恒定结构域，而且 TCR 的恒定区**只有 2 个 C 基因**可选 [【跳转到 06:31】](https://www.youtube.com/watch?v=uq9p26JAnCs&t=391)。

重链（对应 β 链）的 V、J、D 片段都参与重组、造就各种结构；TCR 各链的基因组规模比 B 细胞更大——可选基因多，变异自然更多 [【跳转到 06:56】](https://www.youtube.com/watch?v=uq9p26JAnCs&t=416)。

N 末端一侧则贡献**可变结构域**：可变结构域携带抗原结合位点，而抗原结合位点下方，与抗体一样是**同样的 3 个高变环（hypervariable loops）** [【跳转到 07:21】](https://www.youtube.com/watch?v=uq9p26JAnCs&t=441)。这套规律**对 β 链和 α 链都成立**——每条链都有自己的可变结构域和 3 个高变环 [【跳转到 07:46】](https://www.youtube.com/watch?v=uq9p26JAnCs&t=466)。

![可变结构域下的 3 个高变环：与抗体 CDR 一一对应](assets/Immunology%20T%20cell%20receptor%20structure%20and%20function/00441.webp)

## 四、TCR-CD3 复合体：比 BCR 更精细的信号机器

前面说过，TCR 旁的 CD3 相当于免疫球蛋白旁的 Igα/Igβ。但两者复杂度不同：BCR 只挂着**一对** Igα/Igβ 分子；TCR 侧则是**整个 CD3-TCR 复合体** [【跳转到 03:44】](https://www.youtube.com/watch?v=uq9p26JAnCs&t=224)。

抗原从结合位点结合后引起**构象变化**，不仅作用于 CD3，也作用于 **ζ（zeta）亚基** [【跳转到 03:44】](https://www.youtube.com/watch?v=uq9p26JAnCs&t=224)。

![抗原结合引起构象变化，作用于 CD3 与 ζ 亚基](assets/Immunology%20T%20cell%20receptor%20structure%20and%20function/00224.webp)

为什么要在信号通路上堆这么多分子？讲者给了一个直觉类比：从"受体被结合"到"细胞核激活"之间**环节越多，调节就越精确、越可微调**——就像轴越长、刻度越细 [【跳转到 04:09】](https://www.youtube.com/watch?v=uq9p26JAnCs&t=249)。讲者还给了一个记忆口诀（按字母表顺序 E、D 排在 G 之前，所以这些链在"α/β 一侧"），但随即强调：**具体哪条链在哪一侧不重要，理解各成员的功能才是关键** [【跳转到 04:34】](https://www.youtube.com/watch?v=uq9p26JAnCs&t=274)。这一整套组装起来，就是 **CD3 T 细胞复合体** [【跳转到 04:59】](https://www.youtube.com/watch?v=uq9p26JAnCs&t=299)。

落到具体成员：CD3 复合体包括 ε、γ、δ 以及另一个 ε（讲者边画边数，对应两对异源二聚体）[【跳转到 08:36】](https://www.youtube.com/watch?v=uq9p26JAnCs&t=516)；此外还有一条链——讲者凭记忆把它称作"kappa 链"，自嘲希腊字母可能写得不标准——它**同样参与信号与转运**，并且与 B 细胞一侧的 **Igα、Igβ 同源** [【跳转到 09:01】](https://www.youtube.com/watch?v=uq9p26JAnCs&t=541)。这里"信号"指信号转导通路，"转运"指把 TCR 定向运送到细胞膜、嵌入成有功能的受体 [【跳转到 09:26】](https://www.youtube.com/watch?v=uq9p26JAnCs&t=566)。

![TCR-CD3 复合体：CD3 成员与信号链齐聚受体旁](assets/Immunology%20T%20cell%20receptor%20structure%20and%20function/00516.webp)

![信号链与 B 细胞的 Igα/Igβ 同源——同源性的由来](assets/Immunology%20T%20cell%20receptor%20structure%20and%20function/00591.webp)

> 编者注：结合本系列上一篇（【陈巍翻译】T 细胞受体（TCR）和 CD3），TCR 复合体中经二硫键相连、专职传递信号的这一对链就是 **ζ 链**；讲者口中的"kappa 链"应为口误。

## 五、γδ T 细胞：另一类 TCR

有一群 T 细胞表达的是**另一类 TCR——由 γ 链和 δ 链组成**。它们的功能至今没有被完全理解；这类受体比 α/β TCR **更保守、变异性更小** [【跳转到 05:11】](https://www.youtube.com/watch?v=uq9p26JAnCs&t=311)。

分布上，γδ T 细胞**富集在组织间隙，尤其是皮肤**；而在血液循环和淋巴导管里循环的，更多是 α/β T 细胞 [【跳转到 05:36】](https://www.youtube.com/watch?v=uq9p26JAnCs&t=336)。讲者推测：它们变异性小，可能与其所处环境（组织间隙，相对更"严酷"）有关。

![γδ TCR：更保守，富集于皮肤等组织](assets/Immunology%20T%20cell%20receptor%20structure%20and%20function/00311.webp)

![α/β 主导血液与淋巴循环，γδ 驻留组织](assets/Immunology%20T%20cell%20receptor%20structure%20and%20function/00336.webp)

## 小结

- TCR 与抗体/BCR 高度同源：**β 链 ≈ 重链、α 链 ≈ 轻链**；都有可变区、抗原结合位点和 3 个高变环；
- 多样性机制照常（体细胞重组、连接多样性、N/P 核苷酸），**唯独没有体细胞超突变**；
- 基因座更大、片段更多（61 个 J 片段 vs κ/λ 的 4～5 个），**总多样性比抗体高约 5 个数量级**；
- 结构上：β 链 = V-D-J，α 链 = V-J；恒定区只有 2 个 C 基因（"三个 C"：carboxyl/constant/conserved）；
- 信号上：CD3（ε/γ/δ）+ ζ 等亚基组成 **TCR-CD3 复合体**，比 BCR 的一对 Igα/Igβ 更复杂 → 信号更精确、可微调；这些信号链与 Igα/Igβ 同源，既管信号转导、也管受体转运到膜；
- 另有一类 **γδ TCR**：更保守、富集于皮肤等组织，功能尚未完全明确。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| TCR | T 细胞受体：α/β 异二聚体膜结合抗原受体，β 链同源重链、α 链同源轻链 |
| 体细胞超突变 | 仅发生在 BCR/抗体的多样化机制，TCR 中不存在 |
| 高变环 | 可变区中直接接触抗原的 3 个环，α、β 链各有 3 个 |
| CD3 | TCR 旁的信号分子集合（ε、γ、δ 等两对异源二聚体） |
| ζ 亚基 | TCR-CD3 复合体中的信号链，抗原结合后随之发生构象响应 |
| Igα / Igβ | BCR 的信号辅助分子，与 CD3/ζ 功能同源 |
| γδ TCR | 由 γ/δ 链组成的另一类 TCR：更保守，富集于皮肤等组织 |
