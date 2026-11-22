# 用 AI 蛋白质设计攻克「难对付」的细菌转运蛋白：从设计、过滤到湿实验验证的完整闭环

> 视频来源：[Using AI protein design to design binding proteins to challenging bacterial transporters](https://www.youtube.com/watch?v=3Ad2gUjeSL8)（Australian BioCommons 网研会，约 69 分钟；主讲人 Dr. Rhys Grinter，墨尔本大学；工作已发表于 Nature Communications，实验主要由博士生 Daniel Fox 完成，并与莫纳什大学 Gavin Knott 实验室合作）

## 本讲要解决的核心问题（SCQA）

**背景**：RFdiffusion 生成骨架、ProteinMPNN 配序列、AlphaFold2 回折验证——这套「binder 设计三部曲」在论文里成功率看起来不错，工具也全部开源。

**冲突**：但对第一次上手的人来说，把三个工具串成一个真正能走到湿实验的完整项目并不容易：靶标怎么选、候选怎么过滤、判据定多少、成本多少、哪些坑会让人白忙一场；而且最关键的问题——「设计出来的 binder 凭什么可信」——最终要靠什么来回答？

**疑问**：一个真实的实验室是怎么把 AI 蛋白设计从头走到尾，并证明设计结果与实验事实相符的？

**回答（中心思想）**：本讲用致病性大肠杆菌血红素摄取转运蛋白 ChuA 的真实案例完整演示了这条闭环：先用 AlphaFold 建模搞清「靶标长什么样、该往哪儿设计」，再用 RFdiffusion 生成 20,000 个设计，用 AlphaFold2 按 **iPAE<10、pLDDT>90** 两道阈值过滤到约 400 个、人工精选 96 个合成基因，3 天完成 96 孔表达纯化，表型筛选拿到约 4–5% 的高亲和 binder，最后用 X 射线与冷冻电镜证明**实验结构与设计模型的 RMSD 仅 0.55–0.63 Å**。设计工具给出的模型，和湿实验拍出来的结构几乎一模一样——这就是「回折验证」值得信任的实证。

## 一、背景：为什么盯上 ChuA 这条「血红蛋白铁泵」

### 1.1 革兰氏阴性菌的外膜铁掠夺系统

致病性革兰氏阴性菌要生长，必须掠夺宿主体内稀缺又宝贵的铁。执行这项任务的，是一类叫 **TonB 依赖性转运蛋白**（TonB-dependent transporter）的外膜蛋白 [【跳转到 20:04】](https://www.youtube.com/watch?v=3Ad2gUjeSL8&t=1204)：

![TonB 依赖性转运蛋白：22 股 β 桶加内部 plug 结构域，靠内膜 TonB-ExbB-ExbD 复合物拉开「塞子」](assets/Using%20AI%20protein%20design%20to%20design%20binding%20proteins%20to%20challenging%20bacterial%20transporters/00254.webp)

- 革兰氏阴性菌有外膜和内膜两层，中间是周质空间；这些转运蛋白**插在外膜上**，负责捕获含铁化合物等稀缺底物。
- 它们的结构是 **22 股 β 桶**，中间被一个内部 **plug 结构域**（「塞子」）堵住；底物要进入细胞，plug 必须先被移开。
- 难点在于：外膜本身**没有任何能量来源**。移开塞子的活由内膜上的 **TonB-ExbB-ExbD 复合物**完成——它靠内膜的质子动力势驱动，伸出一根长臂抓住转运蛋白、拉开塞子，底物才能进细胞。

讲者开场所说的 ShuA 与本讲的 ChuA 是同一家族的直系同源蛋白：本案例的模型与设计工作均围绕致病性大肠杆菌的血红素转运蛋白 **ChuA** 展开。

### 1.2 为什么非要设计 binder 抑制它

致病性大肠杆菌是尿路感染的主要病原，每年造成数亿病例、数十万死亡；ChuA 负责摄取血红素（heme）——人体内**最丰富的铁来源**，在系统性感染中是重要的毒力因子。如果设计出高亲和 binder「扣住」ChuA，血红蛋白就送不进铁，细菌就长不动。这就是「用 AI 设计的蛋白质当抗生素」的思路。

### 1.3 研究前提：先造一个「干净」的实验背景

铁对细菌太重要，摄取系统**高度冗余**——即便实验室大肠杆菌也有七八个铁摄取转运蛋白，功能互相备份，单独敲掉一个看不出表型。讲者 2019 年构建了一个敲除**全部**天然铁摄取转运蛋白的大肠杆菌菌株：在加了铁螯合剂（联吡啶）的限制性琼脂上完全不生长 [【跳转到 05:54】](https://www.youtube.com/watch?v=3Ad2gUjeSL8&t=354)。

![铁限制平板实验：敲除菌株不生长，转入 chu 操纵子后恢复生长，再敲掉 ChuA 又不生长](assets/Using%20AI%20protein%20design%20to%20design%20binding%20proteins%20to%20challenging%20bacterial%20transporters/00404.webp)

在此基础上把 **chu 操纵子**（含 ChuA 及其他血红素摄取基因）整合进基因组，菌株就能在血红蛋白/血红素上生长；再单独敲掉 ChuA，生长又消失——用质粒回补可以恢复。这就证明了 ChuA 是从环境获取血红素的关键，也提供了研究它的干净背景。

## 二、设计前的生物学功课：把 ChuA–血红蛋白复合物搞清楚

讲者反复强调一句话：**AI 工具只是流水线的一部分，对靶标生物学与结构背景的理解才是成败关键**。这部分功课占了报告近三分之一的篇幅。

### 2.1 底物偏好：血红蛋白才是生理底物

博士生 Daniel Fox 用琼脂和液体生长实验系统测定了 ChuA 的底物偏好 [【跳转到 07:59】](https://www.youtube.com/watch?v=3Ad2gUjeSL8&t=479)：

![BLI 实验测定 ChuA 与血红蛋白的亲和力：约 80 nM，但结合/解离都很快](assets/Using%20AI%20protein%20design%20to%20design%20binding%20proteins%20to%20challenging%20bacterial%20transporters/00554.webp)

- ChuA 对血红蛋白（成人型 αβ 与胎儿型 αγ）的亲和力**远高于**游离血红素，更高于肌红蛋白；对神经珠蛋白、细胞珠蛋白、铁硫蛋白 ferredoxin 则完全无法摄取。
- **BLI**（生物层干涉术，一种把蛋白「挂」在传感器上测结合的光学方法）测得 Kd 约 **80 nM**，但 on/off 速率都很快—— ChuA 的机制是「快速结合血红蛋白 → 把血红素抽出来 → 立刻解离」，全程**不需要任何外部能量**，在溶液里自发完成。

### 2.2 结构生物学的两次「失败」：只抓到抽完血红素的状态

- 混合 ChuA 与血红蛋白结晶，得到漂亮的粉色晶体，解析出的却是 **ChuA 单独结合血红素**的状态——也就是血红素已经从血红蛋白里被抽出来之后的状态。
- 换冷冻电镜（cryo-EM）再试，分类平均图里依然只有 ChuA 单体。这反过来印证了「快结合、快抽取、快解离」的机制：复合物存在时间太短，实验抓不住。

这正是**结构预测模型登场的理由**——实验抓不到的复合物，可以让 AlphaFold 来「摆」出来。

### 2.3 先搞对「血红蛋白是几聚体」，再建模

直接建模之前还有一个容易被忽略的问题：血红蛋白在红细胞内虽以 α₂β₂ 四聚体为主，但存在**四聚体–二聚体平衡**，随 pH 和血红素氧化态而变。系统实验表明：pH 8 时以四聚体为主，pH 6 时基本变成二聚体；高铁血红蛋白同样如此；再结合血清中运血红蛋白的 haptoglobin 时是二聚体——病原菌遇到的最可能就是**二聚体**。

于是用 AlphaFold 建模 ChuA–血红蛋白复合物：四聚体没有合理解；**αβ 二聚体**给出了漂亮的模型——血红蛋白 β 亚基与 ChuA 的 **loop 7/8** 相互作用，α 亚基悬在溶剂中 [【跳转到 11:19】](https://www.youtube.com/watch?v=3Ad2gUjeSL8&t=679)。

![AlphaFold 模型：血红蛋白 αβ 二聚体的 β 亚基结合在 ChuA 的 loop 7/8 上，αγ 与肌红蛋白的结合模式一致](assets/Using%20AI%20protein%20design%20to%20design%20binding%20proteins%20to%20challenging%20bacterial%20transporters/00679.webp)

三条佐证让这个模型可信：αβ、αγ、肌红蛋白（同样的球蛋白折叠）**结合模式完全一致**；αβ 复合物的 AlphaFold 置信度打分合理；模型里血红素的位置与晶体结构中「抽出后」血红素的配位位置非常接近——构象变化即可把血红素释放、递交给组氨酸。

再用假设驱动的实验交叉验证：与 nanobody 结合的血红蛋白（结合位点远离 ChuA 作用面）喂给细菌，生长刺激不变；而与 haptoglobin 结合的血红蛋白（静态结构叠加出现严重空间冲突）则显著变差——模型预测与表型完全对上。

### 2.4 两个组氨酸：血红素搬运的关键

文献早已指出 ChuA 中 **His420**（晶体结构里正结合着血红素）与 **His86** 对血红素结合与转运很关键。用 **AlphaFold 3**（可以对配体建模）跑 ChuA 加血红素，得到 5 种配位状态：一种与晶体一致（仅 His420 配位），其余都趋向 **His420–His86 双齿配位** [【跳转到 15:04】](https://www.youtube.com/watch?v=3Ad2gUjeSL8&t=904)。

![AlphaFold 3 给出的五种血红素配位状态：从仅 His420 配位到 His420–His86 双齿配位](assets/Using%20AI%20protein%20design%20to%20design%20binding%20proteins%20to%20challenging%20bacterial%20transporters/00904.webp)

光谱实验进一步支持：ChuA 与血红蛋白孵育后出现 413 nm 的血红素吸收峰；单独突变 His420 或 His86 都会让峰位移动（说明两者都参与配位血红素），而突变桶内远端的另一个组氨酸则不移动。

至此，「生物学功课」完成：**血红蛋白二聚体结合在 ChuA 的 loop 7/8 上 → 动态变化把血红素抽出并交给 His420（可能还有 His86）→ TonB-ExbB-ExbD 复合物供能把它运进细胞**。这就是 binder 要去阻断的过程。

## 三、binder 设计战役：RFdiffusion → ProteinMPNN → AlphaFold2 过滤

### 3.1 两件武器是什么

- **RFdiffusion**：Baker 实验室的骨架生成模型（2022 年预印本、2023 年正式发表；相关人物获 2024 年诺贝尔化学奖）。它以 RoseTTAFold 结构预测网络为底座，用去噪算法从高斯噪声加提示出发「去噪」出真实的主链骨架 [【跳转到 17:59】](https://www.youtube.com/watch?v=3Ad2gUjeSL8&t=1079)。注意：它**只输出多聚甘氨酸骨架，不含序列**。
- **ProteinMPNN**：图神经网络，读入骨架坐标，为骨架逐位置配一条能折叠回该骨架的氨基酸序列。

![RFdiffusion 从噪声生成主链骨架，ProteinMPNN 为骨架配序列](assets/Using%20AI%20protein%20design%20to%20design%20binding%20proteins%20to%20challenging%20bacterial%20transporters/01079.webp)

### 3.2 设计策略与三级流水线

策略直接来自生物学功课：**做出结合在 loop 7/8 上的 binder，挡住血红蛋白**，铁摄取自然被切断 [【跳转到 19:14】](https://www.youtube.com/watch?v=3Ad2gUjeSL8&t=1154)。

![设计策略：AlphaFold 模型显示血红蛋白结合在 ChuA 的 loop 7/8，binder 就往这里设计](assets/Using%20AI%20protein%20design%20to%20design%20binding%20proteins%20to%20challenging%20bacterial%20transporters/01154.webp)

具体战役的「弹药清单」[【跳转到 20:04】](https://www.youtube.com/watch?v=3Ad2gUjeSL8&t=1204)：

![设计流水线：RFdiffusion 骨架 → ProteinMPNN 序列 → AlphaFold2 按 iPAE<10、pLDDT>90 过滤，20000→400→96](assets/Using%20AI%20protein%20design%20to%20design%20binding%20proteins%20to%20challenging%20bacterial%20transporters/01204.webp)

1. **RFdiffusion 骨架设计**：以 ChuA 为 target；
2. **ProteinMPNN 序列生成**：每个骨架生成多条候选序列；
3. **AlphaFold2 过滤与验证**：用名为 **DLBinder design** 的精简实现（砍掉了多序列比对等步骤的快速版 AF2），从 **20,000 个 in silico 设计**里筛出 **iPAE（界面 PAE）< 10 且 pLDDT > 90** 的设计——大约 **400 个**；
4. **人工精选到 96 个**：看结合 ΔG、界面面积、折叠样式与折叠多样性等。讲者特别坦承：这些人工标准哪个真正有效并不清楚，从 400 压到 96 更多是合成预算所迫。

设计的 binder 长度在 **70–120 个氨基酸**之间。

### 3.3 从 DNA 到蛋白：3 天拿到 96 个纯化蛋白

- 基因合成交给 **Twist Bioscience**：clonal genes（克隆基因，NGS 验证过的成品质粒），每条约 **70–100 美元**，96 条约 **7,000 美元**；2 月 16 日下单、3 月 7 日到手，直接转化表达菌株。
- 表达：96 孔板中转化 + 抗生素筛选，**免涂板挑克隆**（用 GFP 验证过每孔都正常表达）；转 24 孔自诱导培养基过夜表达；离心收菌、化学裂解；加镍树脂结合 His-tag 蛋白，再用真空多通道装置（Cytiva）并行洗脱。
- 结果：**3 天完成 96 个蛋白的纯化**，加上基因合成时间，从 DNA 到可筛选蛋白**不到 3 周**；表达成功率 80–90%，4 mL 培养能拿到 100–500 μg 蛋白，足够初筛。讲者强调：对疫情响应这类应用，这种「快」本身就是竞争力。

## 四、湿实验筛选：约 4–5% 的命中率，以及「设计=实验」的实证

### 4.1 表型筛选：抑菌圈直接读结果

实验设计很简单粗暴 [【跳转到 25:04】](https://www.youtube.com/watch?v=3Ad2gUjeSL8&t=1504)：铺一块含血红蛋白的琼脂板，上面覆盖一株**携带 TonB 依赖转运蛋白的志贺氏菌**（它能靠血红蛋白长起来），然后把 96 个纯化 binder 分别点上去——如果 binder 亲和力够高，就会跟细菌抢转运蛋白，细菌长不动，板上出现**抑菌圈**。

![表型筛选平板：部分 binder 周围出现清晰的抑菌圈](assets/Using%20AI%20protein%20design%20to%20design%20binding%20proteins%20to%20challenging%20bacterial%20transporters/01504.webp)

周五铺板、忐忑过周末，周一迎来「梦里都见过」的结果：约 **4–5%** 的 binder 有强抑制活性——这个命中率与 BindCraft 论文报道的成功率范围一致。胜出者是 **A10、C8、G7、H3** 四个。

一个耐人寻味的细节：把板里的血红蛋白换成**游离血红素**，binder 就不起作用了——ChuA 照样能摄取游离血红素。为什么？看到最后的机制总结就明白了。

### 4.2 定量表征：亲和力与一个「反例」

![四个胜出 binder 的 AlphaFold 模型：都是 α 螺旋束，但拓扑和序列完全不同](assets/Using%20AI%20protein%20design%20to%20design%20binding%20proteins%20to%20challenging%20bacterial%20transporters/01559.webp)

- 琼脂抑菌可低至 **纳摩尔级**；液体培养 IC50 从低微摩尔到低纳摩尔；BLI 测得 Kd 在**数十至数百纳摩尔**区间。
- **A10 之谜**：A10 的 Kd（155 nM）与 G7、H3 相当，但它只能把生长抑制到约 3 μM，而其他两个能到 50–100 nM。解释藏在 BLI 曲线里：A10 的结合/解离都**太快**——一解离，血红蛋白就趁虚而入完成抽血红素（这个过程本来就极快）。结论：对这种「抢底物」的应用，**慢 on/off 比绝对亲和力数字更重要**。这也是「回折验证指标之外，还要按应用场景选设计」的活教材。

### 4.3 结构验证：设计模型与实验结构几乎重合

**X 射线**：96 个 binder 里照例只长出一个晶体，解析后发现——binder 单独在溶液中的结构与计算设计模型 RMSD 仅 **0.55 Å**，与非对称单元内 8 个分子之间的构象差异相当，也就是说差异完全落在柔性与实验误差范围内。

**冷冻电镜**：解析了 apo ChuA、ChuA+G7、ChuA+H3 三个结构。做 cryo-EM 的好处是拿到 class averages 那一刻就知道有没有结果——转运蛋白头上多了顶「小帽子」，binder 结合上了 [【跳转到 29:19】](https://www.youtube.com/watch?v=3Ad2gUjeSL8&t=1759)。

![冷冻电镜结构：binder 如设计预期结合在 ChuA 的 loop 7/8 位置，密度清晰](assets/Using%20AI%20protein%20design%20to%20design%20binding%20proteins%20to%20challenging%20bacterial%20transporters/01759.webp)

binder 单独对齐的 RMSD 约 **0.63 Å**；整体复合物的少量错位经分析完全由 loop 7/8 自身的柔性摆动驱动，而非 binder 折叠不对。讲者的总结：这套工具不但能做出「能用的」binder，还能做出**与设计原子级吻合**的 binder——这是对整个社区的概念验证。

### 4.4 机制全景：为什么挡得住血红蛋白、挡不住游离血红素

![机制总结图：binder 与血红蛋白界面大面积重叠，但血红素/组氨酸位点未被遮挡](assets/Using%20AI%20protein%20design%20to%20design%20binding%20proteins%20to%20challenging%20bacterial%20transporters/01859.webp)

把 binder 模型叠上血红蛋白复合物模型：两者结合界面**大面积重叠**，血红蛋白被挤出局；但血红素与 His420–His86 的位置**没有被遮挡**，所以游离血红素仍能照常进入。幸运的是，体内细菌遇到的血红素几乎都结合在蛋白上（血红蛋白），所以这条「后门」不影响其作为治疗手段的价值。

下一步计划：致病大肠杆菌还有第二个血红素摄取转运蛋白 **Hma**，正在设计双靶 binder；已提交 NHMRC Ideas Grant，若获资助将在小鼠尿路致病性大肠杆菌感染模型中测试，并积累免疫原性、稳定性等成药性数据。

## 五、给你的实操路线图：Stage 0 / 1 / 2

报告后半段是一份手把手的上手指引，分成三个阶段。

### 5.1 Stage 0：算力

- 建议**持续可用**的 2–8 张 GPU、每张 ≥24 GB 显存；Google Colab 除最简单靶标外大概率不够。
- 预算参考：实验室自购服务器（2×RTX 4090、56 线程、约 1/4 TB 内存）约 **2 万美元**；**消费级显卡完全可用**（更吵更热更费电，但便宜得多）——RFdiffusion 和 ProteinMPNN 24 GB 够用，BindCraft 对大靶标要更多显存。
- 也可用大学 HPC（讲者用墨尔本大学的 Spartan）、Galaxy 平台或云计算；日常设计与试跑用小服务器、大战役用 HPC 是常见分工。

### 5.2 工具选择：只用「发表过且实验验证过」的

- **RFdiffusion**：经典，与 ProteinMPNN、AlphaFold2 组成标准流水线；
- **BindCraft**（Martin Pacesa，Bruno Correia 实验室）：一站式 binder 设计，**实验成功率显著高于 RFdiffusion**，因此需要合成的设施数量更少；开源无商业限制；代价是显存要求更高、体系超过约 400 氨基酸后会变慢；
- 专有工具：DeepMind 的 **AlphaProteo**（未公开、可申请）、**AlphaPulldown**（自称成功率可达 88%、未公开）、**Tri-Discovery**（刚发布，de novo binder 成功率高，de novo 抗体在 50% 靶点上达约 16%）。
- 原则：**别用没经实验检验的新算法**——纸上跑得漂亮不代表现实能成。

### 5.3 安装与心态

- 需要 Linux/Bash/Python/Conda 的基本操作，但**不必是专家**——讲者本人花两个月自学搞定；Lambda Stack 一键装 AI 软件栈、仔细读 GitHub 文档、遇到 bug 找开发者与社区。
- ChatGPT 极有用：既解释工具用法，也直接生成脚本。事实上论文里的全部结果都来自「ChatGPT 生成、拼凑起来的 Python 脚本」。金句：**don't let perfect be the enemy of good**——先跑起来再说。

### 5.4 Stage 1：靶标准备（最容易踩坑的一步）

- 选实验结构：<2.5 Å 分辨率、B-factor 良好；用计算模型则要求目标区域 **pLDDT > 90**。
- 把靶标**裁到能做 binder 的最小范围**：计算成本大致随残基数平方增长；裁小才能在有限算力下拿到足够设计量。
- 但小心 **binder escape**：裁过头把疏水核心暴露出来，设计程序会无视你指定的 hotspot，直接去贴疏水核心「作弊」——分数漂亮、期望拉满、实验全废 [【跳转到 40:33】](https://www.youtube.com/watch?v=3Ad2gUjeSL8&t=2433)。

![binder escape 示意：靶标裁剪不当暴露疏水核心，设计程序绕开热点去贴疏水面](assets/Using%20AI%20protein%20design%20to%20design%20binding%20proteins%20to%20challenging%20bacterial%20transporters/02433.webp)

- 定好 **hotspot 残基**告诉设计程序「贴哪儿」；先做小规模 **scoping runs** 摸参数——有的靶标很容易，有的极难；可以换 hotspot、换模型与参数、换设计策略，甚至联系开发者合作。

### 5.5 Stage 2：规模化、筛选与确认

- 规模经验值：RFdiffusion 路线要拿到 **200–400 个**过筛 binder，通常需要生成 **1,000–30,000 个**模型；BindCraft 只要跑 **50–100 个设计**（它在设计过程中迭代自筛，出手的都是过关的）。GPU 时间从几天到一个月不等，摊到五六张卡上就是几天。
- 精选看：折叠多样性、相互作用界面、结合能量；然后合成——RFdiffusion 路线选 **96 条**、BindCraft 选 **24–48 条**（因为它成功率高）。
- 筛选哲学：**什么 assay 出结果最快就用什么**——生化、生物物理或细胞实验皆可，半定量也够用；讲者最爱 **BLI**（通量与定量的折中）：靶蛋白挂芯片、binder 流过、看响应与解离速率 [【跳转到 46:06】](https://www.youtube.com/watch?v=3Ad2gUjeSL8&t=2766)。细胞实验给不了精确亲和力，但能给出与天然配体对比的相对活性；此外还有 DNA 文库池筛选、胞内表达、无细胞表达偶联酶活等路线，按体系发挥想象。
- 中选 4–5 条 → 毫克级表达 → 严格定量（亲和力、on/off、对靶标功能的调制）→ 结构表征。关于「还要不要花钱做结构验证」，讲者的看法：模型与实验高度一致的证据越来越多，随着信任积累，未来这一步可能可以省。
- 若亲和力不满意：**噬菌体展示**（实验路线，把 AI 设计当起点）或 **partial diffusion**（计算路线，对既有 binder 加部分噪声再去噪，产生变体）都能做亲和力成熟；走向转化还要评估稳定性、哺乳细胞毒性、免疫原性。

### 5.6 工作流全景

![从靶标到药物的完整工作流总结图](assets/Using%20AI%20protein%20design%20to%20design%20binding%20proteins%20to%20challenging%20bacterial%20transporters/02991.webp)

## 六、前沿与挑战：这套技术还缺什么

### 6.1 难啃的靶标与缺失的参数

- **难靶**：膜蛋白的跨膜区很难以「化学上合理」的方式被 binder 接近；极性表面、平坦表面依然难做；有的位点用现有工具几乎做不出能用的 binder——只能换 hotspot、换模型、换策略。
- **翻译后修饰（PTM）**：糖基化、脂化以及小分子配体在预测与生成模型中**尚未被良好参数化**，目前只能避开 PTM 位点做设计；随着配体建模工具（如 AlphaFold 3 这类）成熟，未来可以显式设计与糖基化位点结合的蛋白。

### 6.2 成功率与成本的经济学

本案例今年的实验成功率约为 **4%**（纳摩尔亲和 binder）——意味着必须合成约 96 条基因，DNA 费用不菲。反过来说：若成功率逼近 100%，你只需要合成「你想要多少多样性就合成多少条」，DNA 与筛选成本都将趋近于零——BindCraft 这类高成功率工具正把领域往这个方向推。

### 6.3 人才与 de novo 抗体

- 这套流程需要**复合型人才**：蛋白生化与结构生物学（选靶、选模型、定参数）+ 机器学习与 Python 工程（开发与改进工具）；最理想的是两拨人捏合成一个团队。
- **De novo 抗体仍然很难**。抗体是最容易转化的蛋白药物形式（药企风险偏好高、成药规则清楚），但机器学习至今仍难以准确预测 antibody–antigen 界面。证据：CASP16 竞赛中的 nanobody–hemoglobin 靶标，约 40 支队伍里**只有 1 支**预测成功——而且这是 AlphaFold 3 与 Boltz 都折戟的目标 [【跳转到 53:30】](https://www.youtube.com/watch?v=3Ad2gUjeSL8&t=3210)。

![CASP16 抗原–纳米抗体复合物靶标：绝大多数预测方法失败](assets/Using%20AI%20protein%20design%20to%20design%20binding%20proteins%20to%20challenging%20bacterial%20transporters/03210.webp)

- 刚发布的 **Chai-2**（Chai Discovery，未开源）宣称：在一半「从未被靶向过」的靶点上取得 16% 的 nanobody 成功率、约 68% 的 minibinder 成功率——专有工具在冲锋，开源社区预计会跟上。

### 6.4 递送与成药

- 口服可能性：Baker 实验室 Cell 论文中的 TH17 拮抗剂显示**高度稳定的 de novo 蛋白可能实现口服生物利用度**；
- mRNA 递送适合抗病毒、胞内靶标等场景；吸入或注射在相应场景下可行；
- 稳定性、毒性、免疫原性仍需系统摸底，再把数据反哺进设计参数。
- 一个鼓舞人心的示范：Baker 实验室发表于 Nature 的**蛇毒中和蛋白**——de novo 设计的 binder 在毒素给药前后注射都能保护小鼠，且无副作用。从 in silico 到救命药的路径正在打通。

## 小结

- **AI binder 设计的成败一半在生物学**：先把靶标的底物偏好、 oligomeric 状态、功能机制搞清楚（ChuA 案例：血红蛋白二聚体结合 loop 7/8），才能选对设计位点——这是整条流水线的地基。
- **回折验证是设计闭环的质量闸门**：RFdiffusion 生成 20,000 个设计，AlphaFold2 按 iPAE<10、pLDDT>90 两道闸压到约 400 个——「结构预测器认可这个序列能折叠并贴上靶标」是值得花钱合成的最低门槛。
- **设计模型可以被实验结构验证**：X 射线 RMSD 0.55 Å、冷冻电镜 RMSD 0.63 Å，差异完全落在柔性与实验误差范围内——「设计=实验」有了硬核实证。
- **快速闭环本身就是竞争力**：clonal genes 免克隆 + 96 孔免涂板表达 + 3 天并行纯化，从 DNA 到可筛选蛋白不到 3 周。
- **约 4–5% 的成功率是常态**，且要按应用选设计：A10 的教训是「慢 on/off 比亲和力数字更重要」。
- **上手的门槛正在快速下降**：消费级 GPU、全开源工具链、生成式 AI 辅助编码，让单个实验室也能玩转这套「从头设计蛋白质抗生素」的技术。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| TonB 依赖性转运蛋白 | 革兰氏阴性菌外膜上、由内膜 TonB-ExbB-ExbD 复合物供能的底物摄取通道 |
| ChuA | 致病性大肠杆菌的血红素摄取转运蛋白，本案例的靶标 |
| 血红素 (heme) | 含铁辅基，人体内最丰富的铁来源，ChuA 的底物 |
| plug 结构域 | 堵在 β 桶内侧、可被 TonB 拉开的「塞子」 |
| RFdiffusion | 从高斯噪声去噪生成蛋白主链骨架的扩散模型（Baker 实验室） |
| ProteinMPNN | 读入骨架、逐位置设计氨基酸序列的图神经网络 |
| iPAE（界面 PAE） | AlphaFold 输出的界面位置对齐误差，越小越好；本案例过滤阈值 <10 |
| pLDDT | AlphaFold 逐残基置信度（0–100）；本案例过滤阈值 >90 |
| DLBinder design | 精简加速版的 ProteinMPNN + AlphaFold2 组合实现 |
| BLI | 生物层干涉术：蛋白固定在传感器上实时测结合/解离的光学方法 |
| Kd | 解离常数，数值越小亲和力越强 |
| binder escape | 靶标裁剪过度、暴露疏水核心，导致设计程序绕开指定热点「作弊」的现象 |
| BindCraft | 一站式开源 binder 设计流水线（Correia 实验室），内部迭代过滤 |
| clonal genes | NGS 测序验证过的合成基因克隆，到手即可转化表达 |
| scoping runs | 大规模设计前的小规模试跑，用于摸索能通过 in silico 指标的参数 |
