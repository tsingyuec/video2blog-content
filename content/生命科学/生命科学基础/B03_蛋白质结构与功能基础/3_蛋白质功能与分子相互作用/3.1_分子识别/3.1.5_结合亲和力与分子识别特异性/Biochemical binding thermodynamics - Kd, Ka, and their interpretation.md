# 结合热力学：读懂 Kd、Ka 与 ΔG

> 视频来源：[Biochemical binding thermodynamics - Kd, Ka, and their interpretation](https://www.youtube.com/watch?v=aErpulsqG1g)（YouTube，约 49 分钟）。本文基于该视频的演说图文稿整理而成，关键结论均可在对应时间戳核对。

## 本讲要解决的核心问题（SCQA）

**背景**：分子结合是生化世界的常态——酶与底物、抗体与抗原、药物与靶点。衡量结合强弱的通用标尺是解离常数 Kd；结合曲线、亲和力成熟、药物设计全都绕不开它。

**冲突**：Kd 有三层"反直觉"：数值越小结合越强；它明明叫"常数"却带着浓度单位；而且"两个分子能结合"和"两个分子真的会结合"是两回事——结合还取决于浓度与热力学环境。

**疑问**：Kd 到底怎么读？怎么测？它由什么决定？ΔG 又在其中扮演什么角色？

**回答（中心思想）**：**Kd 是 koff 与 kon 之比，单位是浓度，直觉含义是"让一半靶分子被结合所需的配体浓度"**；它由结合反应的热力学（ΔG = ΔH − TΔS）决定，并随盐浓度、pH 等环境条件改变；实验上用系列稀释测结合曲线，在半最大结合处读出 Kd。

![本讲主题：Kd 是生化里最重要的常数之一](assets/Biochemical%20binding%20thermodynamics%20-%20Kd,%20Ka,%20and%20their%20interpretation/00000.webp)

## 一、Kd 的直觉：做一次"分子普查"

### 1.1 一半结合所需的浓度

讲师开篇给出全片的中心：Kd（结合解离常数）衡量结合强度，但它是结合亲和力 Ka 的**倒数**。它最实用的读法是：

> **Kd = 当游离配体浓度达到这个值时，恰好一半的靶蛋白被结合。**

所以 **Kd 越小 → 只需要更少的配体就能让一半蛋白"上钩" → 亲和力越强**；反过来 Kd 越大，就需要更多的"另一半"围着，才能维持一半的结合。[【跳转到 00:44】](https://www.youtube.com/watch?v=aErpulsqG1g&t=44)

![Kd 的直觉：一半结合所需的浓度；低 Kd = 高亲和力](assets/Biochemical%20binding%20thermodynamics%20-%20Kd,%20Ka,%20and%20their%20interpretation/00044.webp)

### 1.2 分子普查：谁"结婚"了，谁还"单身"

把两个结合伙伴叫 A 和 B，混在一起，让它们"结婚"（结合）或"离婚"（解离）。然后对体系做一次"分子普查（molecular census）"：数一数有多少是"已婚"（AB 复合物），多少是"单身"（游离的 A 与 B）。[【跳转到 01:34】](https://www.youtube.com/watch?v=aErpulsqG1g&t=94) Kd 告诉我们的正是：**要有多少 B 摆在周围，才能让一半的 A 结婚**。[【跳转到 08:39】](https://www.youtube.com/watch?v=aErpulsqG1g&t=519)

![分子普查：数一数"已婚"（结合）与"单身"（游离）](assets/Biochemical%20binding%20thermodynamics%20-%20Kd,%20Ka,%20and%20their%20interpretation/00094.webp)

术语备忘：**L（ligand，配体）**是结合伙伴的通称——抗体的配体叫抗原，受体的配体叫信号分子；**R（receptor，受体）**常是膜上蛋白，识别信号分子并传递信号。[【跳转到 02:28】](https://www.youtube.com/watch?v=aErpulsqG1g&t=148)

### 1.3 结婚概率与离婚概率：kon 与 koff

A 撞上 B 时结成 AB 的"概率"，是**结合速率常数 kon**——像"一见钟情"的概率；已结合的 AB 散伙的概率，是**解离速率常数 koff**——像婚后的"离婚率"。[【跳转到 03:39】](https://www.youtube.com/watch?v=aErpulsqG1g&t=219) 两者都会随环境（盐浓度、pH 等）而变。

注意符号的"大小写规则"：**小写 k 指速率常数（kon、koff），大写 K 指平衡常数（Ka、Kd）**——教材里就是这个约定。[【跳转到 03:09】](https://www.youtube.com/watch?v=aErpulsqG1g&t=189)

体系最终到达**动态平衡**：结合与解离仍在不断发生，只是速率相等、比例不再变化。而平衡时的比例正由 kon 与 koff 共同决定：

$$K_d = \frac{k_{\text{off}}}{k_{\text{on}}}$$

![结婚概率 kon 与离婚概率 koff 共同决定平衡](assets/Biochemical%20binding%20thermodynamics%20-%20Kd,%20Ka,%20and%20their%20interpretation/00239.webp)

### 1.4 平衡测量分不出 kon 和 koff

只测平衡态的浓度，**只能得到 Kd 这个"比值"，分不出 kon 和 koff 各自的贡献**——kon 大或 koff 小都可能造成低 Kd。要拆开它们得用动力学方法（如表面等离子共振等），本讲只关注平衡。[【跳转到 16:29】](https://www.youtube.com/watch?v=aErpulsqG1g&t=989)

浓度变化也一样：提高浓度让 A、B 更容易"相遇"，平衡时结合的比例会变，但**Kd 本身不变**——它只由 kon/koff 决定。[【跳转到 06:54】](https://www.youtube.com/watch?v=aErpulsqG1g&t=414)

## 二、Kd 的单位从哪来：质量作用定律

### 2.1 先写结合方向：Ka 的单位别扭

对 A + B ⇌ AB，按"产物/反应物"写平衡常数（质量作用定律）：

$$K_a = \frac{[AB]}{[A]\,[B]}$$

这是**结合常数 Ka**。若各浓度以 M 计，单位是 M/M² = **1/M**——"逆浓度"单位，用起来别扭。[【跳转到 11:34】](https://www.youtube.com/watch?v=aErpulsqG1g&t=694)

![Ka = [AB]/([A][B])：结合方向的平衡常数](assets/Biochemical%20binding%20thermodynamics%20-%20Kd,%20Ka,%20and%20their%20interpretation/00694.webp)

### 2.2 把反应倒过来写：得到 Kd

把平衡式倒写成 AB ⇌ A + B（解离方向），平衡常数就变成：

$$K_d = \frac{[A]\,[B]}{[AB]}$$

单位是 M²/M = **浓度**——这正是生化研究偏爱 Kd 的原因：它的单位就是浓度，读起来直观。[【跳转到 13:39】](https://www.youtube.com/watch?v=aErpulsqG1g&t=819)

![解离方向的平衡常数 Kd：单位是浓度](assets/Biochemical%20binding%20thermodynamics%20-%20Kd,%20Ka,%20and%20their%20interpretation/00819.webp)

（严格说所有平衡常数都是无量纲的——各浓度本应除以 1 M 标准态；生化习惯省略这一步，Kd 便"带上"了浓度单位。）

### 2.3 小结这一段

- **浓度不影响 Kd**：改浓度改变的是"结合的量"，不是"结合的强度"。
- **Kd = koff/kon**：结合强度由两个速率常数的比决定。
- 正因为 Kd = [A][B]/[AB]，我们才能用"测不同浓度下的结合量"反推出 Kd。

## 三、Kd 的典型数量级：从 10⁻¹⁵ M 到毫摩尔

生化里的非共价结合，Kd 跨越约 12 个数量级：

- **生物素–亲和素（biotin–avidin）**：约 10⁻¹⁵ M（飞摩尔级），已知最强的非共价相互作用之一；[【跳转到 17:29】](https://www.youtube.com/watch?v=aErpulsqG1g&t=1049)
- **毫摩尔（10⁻³ M）**：低亲和力；
- **微摩尔（10⁻⁶ M）**：许多酶-配体相互作用的典型范围；
- **纳摩尔（10⁻⁹ M）**：常见的高亲和力结合；
- **抗体–抗原**：强的可达皮摩尔（10⁻¹²）到纳摩尔级。

![典型 Kd 数值表：biotin-avidin 最强，毫摩尔最弱](assets/Biochemical%20binding%20thermodynamics%20-%20Kd,%20Ka,%20and%20their%20interpretation/01049.webp)

数量级越小、结合越紧。药物设计的语境里，人们希望先导化合物的 Kd（或 Ki、IC50）越低越好——**药量少、药效强，患者不用一天吞 50 颗大药片**。[【跳转到 26:45】](https://www.youtube.com/watch?v=aErpulsqG1g&t=1605)

## 四、怎么测 Kd：结合曲线

### 4.1 系列稀释 + 分子普查

标准做法：把一个结合伙伴（如 A）做**系列稀释（serial dilution）**——每次按相同倍数稀释，覆盖很宽的浓度范围；另一个伙伴（B）保持恒定的低浓度。混合、等平衡，然后"普查"：B 有多少被结合（比例记作 θB）。[【跳转到 19:14】](https://www.youtube.com/watch?v=aErpulsqG1g&t=1154)

- A = 0 时，B 全部游离；
- A 增多，B 的结合比例上升；
- A 大过量时，B 全部被占据（饱和，平台期）。

中间就是一条**双曲线（hyperbolic）**：纵轴是结合比例，横轴是 A 的浓度。**曲线到达半最大结合（½Bmax）处对应的 A 浓度，就是 Kd**。[【跳转到 21:19】](https://www.youtube.com/watch?v=aErpulsqG1g&t=1279)

![双曲线型结合曲线：半最大结合处读出 Kd](assets/Biochemical%20binding%20thermodynamics%20-%20Kd,%20Ka,%20and%20their%20interpretation/01279.webp)

### 4.2 半对数坐标：S 形曲线与"先看横轴"

实验中更常用**半对数图**：横轴取 log（如 log₁₀），纵轴仍是线性。浓度跨几个数量级时，点不再挤在原点附近，S 形曲线铺满全图，读 Kd 更方便。[【跳转到 22:09】](https://www.youtube.com/watch?v=aErpulsqG1g&t=1329)

![半对数坐标下的 S 形结合曲线](assets/Biochemical%20binding%20thermodynamics%20-%20Kd,%20Ka,%20and%20their%20interpretation/01329.webp)

一个重要提醒（讲师用自己读博时的数据举例）：**读图前先看横轴是线性还是对数**。线性坐标 + 多个结合位点 + 协同性（如血红蛋白结合氧）也会出现 S 形；而单纯一个位点、log 坐标下本来就是 S 形。别把坐标选择误读成"协同性"。[【跳转到 23:24】](https://www.youtube.com/watch?v=aErpulsqG1g&t=1404)

### 4.3 实战判读：一篇转录因子论文

讲师现场演示判读一篇论文的图：转录因子（蛋白）与多条 RNA / DNA 序列结合，log 横轴、S 形曲线。判读规则：

- **最强结合 = 曲线最靠左**（Kd 最小）；
- **最弱结合 = 曲线最靠右**（Kd 最大）；
- 在 ½Bmax 处向下读浓度，即得各自的 Kd；
- **最高 Ka 对应最低 Kd**（互为倒数）。[【跳转到 28:07】](https://www.youtube.com/watch?v=aErpulsqG1g&t=1687)

细节：实测的 Bmax 有时小于 1——可能部分"你以为在"的分子其实失活，不参与结合。[【跳转到 29:47】](https://www.youtube.com/watch?v=aErpulsqG1g&t=1787)

### 4.4 测量实践小贴士

- **[A] ≫ [B] 近似**：当 A 大过量时，被结合消耗掉的 A 可以忽略，"游离 A ≈ 总 A"，公式大幅简化；若 B 与 Kd 相当，就必须扣掉被消耗的部分。[【跳转到 37:30】](https://www.youtube.com/watch?v=aErpulsqG1g&t=2250)
- 理想上稀释范围覆盖 Kd 上下约 **100 倍**，曲线才完整。
- 结合太强（Kd 太低）时浓度低到难以检测——测核酸结合常用**放射性标记**（如 ³²P 标记的磷酸骨架）。[【跳转到 39:10】](https://www.youtube.com/watch?v=aErpulsqG1g&t=2350)

## 五、为什么"一半"恰好是 Kd：三行推导

设 θB 为 B 的结合比例：θB = [AB]/([A] + [AB])，而 Kd = [A][B]/[AB]。两式联立消去 [AB]，得：

$$\theta_B = \frac{[A]}{K_d + [A]}$$

把 [A] = Kd 代入：θB = Kd/(Kd+Kd) = **1/2**——这就是"Kd 是一半结合所需的浓度"的数学出处。[【跳转到 33:12】](https://www.youtube.com/watch?v=aErpulsqG1g&t=1992)

![θB = [A]/(Kd+[A])：[A] = Kd 时恰好一半结合](assets/Biochemical%20binding%20thermodynamics%20-%20Kd,%20Ka,%20and%20their%20interpretation/01992.webp)

这个公式还能回答"到底会结合多少"：

- **[A] = 10×Kd**：θB = 10/11 ≈ **91%** 结合；
- **[A] = 0.1×Kd**：θB = 0.1/1.1 ≈ **9%** 结合。[【跳转到 34:02】](https://www.youtube.com/watch?v=aErpulsqG1g&t=2042)

由此得到全片最重要的一句提醒：**"能结合"不等于"会结合"**。理论上算得出亲和力，但如果生理环境中对方浓度远低于 Kd，实际结合微乎其微——反之，体内丰度很低的分子必须亲和力极高才有可能真正结合。[【跳转到 34:39】](https://www.youtube.com/watch?v=aErpulsqG1g&t=2079)

对称地，θA = [B]/(Kd + [B])——用谁做"恒定量"都能推出同样形式。[【跳转到 35:54】](https://www.youtube.com/watch?v=aErpulsqG1g&t=2154)

## 六、Kd 从哪来：热力学（ΔG）

Kd 为什么是那个值？讲师提示：注意那张典型 Kd 数值表的脚注——**蛋白-配体相互作用的 Kd 会随溶液盐浓度、pH 等条件改变，有时变好几个数量级**。[【跳转到 39:45】](https://www.youtube.com/watch?v=aErpulsqG1g&t=2385) 往下挖，就到了热力学。

![Kd 随盐浓度、pH 等条件改变——线索在表格脚注里](assets/Biochemical%20binding%20thermodynamics%20-%20Kd,%20Ka,%20and%20their%20interpretation/02380.webp)

### 6.1 ΔG：负值才自发

平衡常数的本质是吉布斯自由能变：

$$\Delta G = \Delta H - T\,\Delta S$$

**ΔG < 0：有利（自发）**；ΔG > 0：不利。ΔG 由焓变 ΔH 与熵变 ΔS 共同决定。非共价结合不涉及共价键的断裂与生成，账要算在非共价相互作用上。[【跳转到 40:32】](https://www.youtube.com/watch?v=aErpulsqG1g&t=2432)

![ΔG < 0 自发；ΔG = ΔH − TΔS](assets/Biochemical%20binding%20thermodynamics%20-%20Kd,%20Ka,%20and%20their%20interpretation/02432.webp)

### 6.2 焓：一切的静电（广义）

焓项来自"**相反电荷相吸、相同电荷相斥**"——而且对部分电荷同样成立：永久偶极-偶极、诱导偶极、瞬时偶极（London 色散力）、范德华力，全都可以归结为广义的静电相互作用。结合态若比游离态形成更多有利的这类相互作用，ΔH 就对结合有利。[【跳转到 41:25】](https://www.youtube.com/watch?v=aErpulsqG1g&t=2485)

### 6.3 熵：疏水效应是被低估的主力

熵看"无序度"。结合把两个分子"锁"在一起，本身降低熵——但别只盯着这两个分子，还要看**它们置换出了什么**：疏水结合位点周围的水原本被"困"在有序的笼状排布里，无处躲藏；一旦配体结合、占据位点，这些水被释放回溶液，**水的熵大幅增加**，足以驱动结合。这就是**疏水效应（hydrophobic effect）**——它是结合能量的重要来源。[【跳转到 42:14】](https://www.youtube.com/watch?v=aErpulsqG1g&t=2534)

![疏水效应：结合释放被"困"的水，水的熵增驱动结合](assets/Biochemical%20binding%20thermodynamics%20-%20Kd,%20Ka,%20and%20their%20interpretation/02534.webp)

### 6.4 环境：盐会"分心"

把静电相互作用想成"男女相吸"：溶液里盐越多，越多其他离子在"抢戏"（屏蔽电荷、提供干扰），蛋白与配体更难找到彼此——**高盐通常使 Kd 升高（结合变弱）**；低盐则相反。[【跳转到 44:35】](https://www.youtube.com/watch?v=aErpulsqG1g&t=2675)

这就是"Kd 依赖条件"的原因，也带来一个实验技巧：想检验某个结合是否真的牢固，用**高盐洗脱**——洗得掉的都不是强结合。[【跳转到 45:50】](https://www.youtube.com/watch?v=aErpulsqG1g&t=2725)

## 七、收尾回顾：一张"Kd 全景图"

视频最后把全片串成一遍：[【跳转到 45:50】](https://www.youtube.com/watch?v=aErpulsqG1g&t=2750)

- Kd 衡量结合强度，但它是亲和力常数 Ka 的**倒数**：**Kd 越小 = 相互作用越强**；
- Kd = koff/kon；条件不变时它是常数，**浓度改变不影响 Kd**，只影响结合的量；
- Kd = [A][B]/[AB] = **一半结合所需的浓度**（θ = [A]/(Kd+[A)] 的直接推论）；
- 典型范围：纳摩尔～微摩尔（药物设计追求更低）；
- 亲和力既可以来自"结合更快"（kon 大），也可以来自"脱落更慢"（koff 小），或两者组合——**只测平衡态分不出这两者**。

![收尾全景：Kd = koff/kon，低 Kd = 强结合](assets/Biochemical%20binding%20thermodynamics%20-%20Kd,%20Ka,%20and%20their%20interpretation/02760.webp)

## 小结

- **Kd 的直觉**：一半靶分子被结合所需的配体浓度；Kd 越小亲和力越强。
- **Kd 的身世**：Kd = koff/kon = [A][B]/[AB]，单位浓度（Ka 是它的倒数，单位 1/M）。
- **Kd 的数量级**：biotin–avidin ~10⁻¹⁵ M 最强；毫摩尔最弱；酶常在 μM；抗体-抗原可到 pM~nM。
- **怎么测**：系列稀释 + 恒量另一伙伴 → 饱和曲线；半对数坐标更常用；½Bmax 处读 Kd；先看横轴是线性还是 log。
- **一半的出处**：θ = [A]/(Kd+[A)]；[A]=Kd → 50%；10×Kd → 91%；0.1×Kd → 9%。
- **能结合 ≠ 会结合**：实际结合比例取决于浓度与 Kd 的相对大小。
- **Kd 的根源**：ΔG = ΔH − TΔS；静电（广义）贡献焓，疏水效应（释放水）贡献熵；盐浓度、pH 等环境条件通过热力学改变 Kd。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| Kd（解离常数） | [A][B]/[AB]，单位浓度；一半结合所需浓度；越小越强 |
| Ka（结合常数） | [AB]/([A][B])，单位 1/M；Kd 的倒数；越大越强 |
| kon / koff | 结合/解离速率常数（小写 k）；决定 Kd = koff/kon |
| θB（结合比例） | B 被结合的比例，θB = [A]/(Kd+[A]) |
| Bmax | 最大结合比例（可 <1，提示部分分子失活） |
| ΔG = ΔH − TΔS | 吉布斯自由能变；负值自发的结合 |
| 疏水效应 | 结合释放被"困"的水，水熵增驱动结合 |
| 分子普查 | 平衡时数"已婚/单身"比例的思考方式 |
