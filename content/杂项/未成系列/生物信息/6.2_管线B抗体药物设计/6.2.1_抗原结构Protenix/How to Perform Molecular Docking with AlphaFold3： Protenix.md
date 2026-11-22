# How to Perform Molecular Docking with AlphaFold3： Protenix

> 视频来源：YouTube《How to Perform Molecular Docking with AlphaFold3: Protenix》（Ashak Ahmed 频道，约 21.6 分钟）。讲者 Ashak Ahmed 从事结构生物学与生物信息学，这是其「AlphaFold 3 建模」系列的第二讲——上一讲用 AF3 官方 Server 做生物分子建模（频道播放量最高的一期），本讲改用 AF3 的开源复现 **Protenix**，演示「蛋白 + 任意有机分子」的完整对接流程。对应系列条目 **6.2.1 抗原结构（Protenix）**：管线 B（抗体药物设计）的第一步是拿到抗原三维结构——PDB 里没有现成结构时，就用 Protenix 预测。

## 本讲要解决的核心问题（SCQA）

**背景**：做抗体药物设计，先要有靶标抗原的三维结构。PDB 里有现成结构最好（见 6.1.1）；没有的时候，就得靠「序列 → 结构」的 AI 预测工具。

**冲突**：AlphaFold 3 官方 Server 虽强，但限制不少：网页版只给 5 次预测、能加的配体和离子数量有限、代码不开放，商业化用途也不免费。

**疑问**：有没有一个「AF3 级精度 + 配体离子不受限 + 开源可自部署」的工具，能把任意抗原连同配体、离子一起预测出来，还能和实验结构对得上？

**回答（中心思想）**：有——**Protenix**，AlphaFold 3 的开源复现。本讲跟做一遍完整闭环：配置任务（MSA / iptm / 邮箱）→ 粘贴序列（NDM-1）→ 按 CCD 码加两个锌离子 → 从 PubChem 贴布洛芬 SMILES → 提交等 10~15 分钟 → 邮箱收结果、下载 CIF → PyMOL 里与晶体结构 4EXS 对齐验收。结论：主链对齐近乎完美、锌离子位置正确，预测的布洛芬甚至占据了晶体配体卡托普利的口袋、氧原子朝向锌——「任意配体对接」这条路走通了。

## 一、Protenix：补上 AF3 短板的开源复现

### 1.1 它和 AF3 的关系

Protenix 由另一个实验室开发，本质上是对 AF3 的复现，使用了同样先进的 AI 架构，蛋白结构预测精度甚至更高（[【跳转到 01:16】](https://www.youtube.com/watch?v=bfEtvtWJEGg&t=76)）。它对商业与非商业用途都免费，既可以在线用（本讲的用法），也可以下载到本地部署（[【跳转到 04:48】](https://www.youtube.com/watch?v=bfEtvtWJEGg&t=288)）。

### 1.2 它解决了 AF3 的什么限制

AF3 原本只能对接有限数量的离子和有机分子；Protenix 则可以把**各类分子**都整合进蛋白体系——配体、离子、DNA、RNA，甚至共价修饰等蛋白修饰（[【跳转到 01:41】](https://www.youtube.com/watch?v=bfEtvtWJEGg&t=101)）。换句话说：对抗原结构预测这件事，Protenix 几乎不设限——这对「配体/金属离子参与结合功能」的抗原尤其重要。

## 二、服务器实操（一）：任务配置

视频录制时 Protenix 还没有独立域名，讲者通过 IP 地址访问服务器（链接放在视频描述区，[【跳转到 03:48】](https://www.youtube.com/watch?v=bfEtvtWJEGg&t=228)）。进入后的关键设置：

- **Job ID**：任务名，随意改；
- **use MSA**：多序列比对（MSA，把同源序列对齐以提供进化信息）。开启会更慢但更准，建议开启；
- **iptm confidence**：界面置信度计算，同理「开了更慢、结果更可信」，选 true；
- **email**：必填——目前没有专用服务器，结果不做网页展示，直接发到你邮箱（[【跳转到 06:08】](https://www.youtube.com/watch?v=bfEtvtWJEGg&t=368)）。

![Protenix 服务器任务配置页：任务 ID、MSA 与 iptm confidence 开关、邮箱必填](assets/How%20to%20Perform%20Molecular%20Docking%20with%20AlphaFold3： Protenix/00318.webp)

**序列与拷贝数**：序列步骤可以增删序列。讲者用他最常用的 NDM-1（新德里金属 β-内酰胺酶-1，一个含锌的水解酶，PDB 里有多个结构）做演示，从页面复制粘贴即可（[【跳转到 07:14】](https://www.youtube.com/watch?v=bfEtvtWJEGg&t=434)）。旁边的 **copies（拷贝数）** 用于模拟寡聚：想建二聚体、三聚体、四聚体就调到 2、3、4；本例只做单链，保持 1（[【跳转到 07:52】](https://www.youtube.com/watch?v=bfEtvtWJEGg&t=472)）。

## 三、服务器实操（二）：把「配角」加进体系

### 3.1 离子：按 CCD 编码写，别写英文名

NDM-1 的活性口袋里结合**两个锌离子**——这是讲者「了解这个蛋白」带来的领域知识（PDB 4EXS 等多个结构可查）。于是在序列 2 处选择 ions、数量填 2（[【跳转到 08:42】](https://www.youtube.com/watch?v=bfEtvtWJEGg&t=522)）。

![在序列 2 处选择 ions 并指定数量：NDM-1 的口袋里有 2 个锌离子](assets/How%20to%20Perform%20Molecular%20Docking%20with%20AlphaFold3： Protenix/00497.webp)

离子的**名字要按 CCD 编码**（Chemical Component Dictionary，结构生物学标准的化学组分字典）书写：直接写 `zinc` 会报错，锌要写 `ZN`；同理镁 `MG`、钙 `CA`（[【跳转到 09:07】](https://www.youtube.com/watch?v=bfEtvtWJEGg&t=547)）。

![离子名称按 CCD 编码书写：锌是 ZN，镁是 MG，钙是 CA](assets/How%20to%20Perform%20Molecular%20Docking%20with%20AlphaFold3： Protenix/00572.webp)

### 3.2 配体：PubChem 的 isomeric SMILES 原样粘贴

配体是「最重要的一步」（[【跳转到 09:32】](https://www.youtube.com/watch?v=bfEtvtWJEGg&t=572)）。输入方式有 **Ligand SMILES** 与 **Ligand CCD** 两种，本讲用前者。SMILES 是分子的线性文本表示（见 1.3.1）。讲者打开 PubChem，随手挑了**布洛芬（ibuprofen）**做演示——各国商品名不同（如 Brufen），但化学名一致。在 PubChem 页面找到 **isomeric SMILES**（带立体化学的同分异构 SMILES），**原样复制**（[【跳转到 10:42】](https://www.youtube.com/watch?v=bfEtvtWJEGg&t=642)）。

![在 PubChem 中找到布洛芬的 isomeric SMILES 并原样复制](assets/How%20to%20Perform%20Molecular%20Docking%20with%20AlphaFold3： Protenix/00656.webp)

**常见坑**：直接拖选复制容易把空格带进 SMILES，提交时就报错——用退格键删掉空格即可修复（[【跳转到 11:27】](https://www.youtube.com/watch?v=bfEtvtWJEGg&t=687)）。另一个值得注意的差异：Protenix **不需要** AutoDock 类软件的 grid box（对接盒子）——它自己更「智能」，会自动寻找结合位置（[【跳转到 11:51】](https://www.youtube.com/watch?v=bfEtvtWJEGg&t=711)）。如需共价修饰/共价键，也有专门入口可指定成键原子，本讲未用。

## 四、提交、等待与取结果

### 4.1 提交与确认

点 Submit。没填邮箱会提示 verification failed；填好邮箱再提交，确认配置（序列、锌离子 ×2、配体 ×1、MSA=true、原子置信度=true、共价键=0）后点 Confirm 即可（[【跳转到 13:06】](https://www.youtube.com/watch?v=bfEtvtWJEGg&t=786)）。讲者特意先不在演示中点 Confirm，避免给服务器添额外负担——他的任务早已跑完。

### 4.2 等多久？

**10~15 分钟起**，也可能更久，取决于任务规模与设置（[【跳转到 14:26】](https://www.youtube.com/watch?v=bfEtvtWJEGg&t=866)）。专用网页服务器已在开发中，未来体验会更好。

### 4.3 下载与解压

结果邮件里给 output URL / log URL；点开 output URL → visit link → 下载压缩包，解压到本地（[【跳转到 15:54】](https://www.youtube.com/watch?v=bfEtvtWJEGg&t=954)）。

![从 output URL 进入、下载并解压 Protenix 的结果包](assets/How%20to%20Perform%20Molecular%20Docking%20with%20AlphaFold3： Protenix/00954.webp)

结果目录里有三个 JSON 文件和三个子目录；进入 `protenix 任务 → seed → predictions`，会看到若干 JSON 与 CIF 文件。**你真正关心的是 CIF 文件**（结构坐标，见 2.2.2）；理想情况下**第一个就是排名最高的模型**；分数等指标在 JSON_0 里可查（[【跳转到 17:26】](https://www.youtube.com/watch?v=bfEtvtWJEGg&t=1046)）。

![predictions 目录中的 CIF 文件：第一个通常是排名最高的模型](assets/How%20to%20Perform%20Molecular%20Docking%20with%20AlphaFold3： Protenix/01046.webp)

## 五、验收：PyMOL 里与晶体结构对齐

### 5.1 与 PDB 4EXS 对齐

讲者在 PyMOL 中打开预测的 CIF，再载入真实的 **PDB 4EXS**（NDM-1 与卡托普利 L-cap 的共晶结构），把两者对齐（[【跳转到 18:46】](https://www.youtube.com/watch?v=bfEtvtWJEGg&t=1126)）。青灰色是实验结构，蓝色是 Protenix 预测：**主链近乎完美对齐**。一个细节：晶体结构从约 34/42 位开始（N 端缺失），而预测从第 1 位的甲硫氨酸开始——对齐时预测会多出这段 N 端（[【跳转到 19:23】](https://www.youtube.com/watch?v=bfEtvtWJEGg&t=1163)）。

![预测结构（蓝）与晶体 4EXS（青灰）对齐：主链近乎重合，预测多出晶体缺失的 N 端](assets/How%20to%20Perform%20Molecular%20Docking%20with%20AlphaFold3： Protenix/01126.webp)

**锌离子位置**也相当准确（[【跳转到 19:49】](https://www.youtube.com/watch?v=bfEtvtWJEGg&t=1189)）。

### 5.2 配体口袋：布洛芬 vs 卡托普利

最有意思的一幕：绿色是预测的布洛芬，青色是晶体里的卡托普利——**布洛芬占据了卡托普利所在的那个口袋**，而且它的两个氧原子伸向锌离子（[【跳转到 20:19】](https://www.youtube.com/watch?v=bfEtvtWJEGg&t=1219)）。这意味着「全盲对接」确实找到了金属酶的活性位点，含锌口袋的化学被模型「读懂」了。

![绿色布洛芬（预测）落入青色卡托普利（晶体配体）的同一口袋，氧原子朝向锌离子](assets/How%20to%20Perform%20Molecular%20Docking%20with%20AlphaFold3： Protenix/01219.webp)

## 六、对管线 B 的意义

- **抗原结构获取的双路线**就此合拢：PDB 有实验/同源结构就优先用（6.1.1），没有就用 Protenix 预测——本讲给出了从任务配置到结构验收的完整操作路径；
- 抗原预测出来后，还可以把它与抗体放进同一个任务，预测**抗原-抗体复合物**（Protenix 同样支持多链）——但「预测出来的界面能不能信」是另一个问题，见姊妹篇《AlphaFold 3 Accuracy on Antibody Binding and Protein Interactions》与《Bioexcel webinar #85》；
- 记住三个操作细节：离子写 CCD 码、SMILES 别带空格、结果认准 predictions 目录里的 CIF。

## 小结

- Protenix 是 AF3 的开源复现：免费（含商用）、可本地部署，配体/离子/DNA/RNA/共价修饰不受限；
- 离子与配体都按标准编码书写（CCD 码；SMILES 从 PubChem 原样复制，小心空格）；
- 提交后 10~15 分钟出结果，答案在邮箱；结构文件认 predictions 目录的 CIF，第一个是 top ranked；
- 验收三步：与晶体/同源结构对齐看主链 RMSD、检查金属离子位置、检查配体口袋与朝向；
- 本例中主链近乎完美对齐、锌位正确、布洛芬占据卡托普利口袋且氧朝锌——「任意配体对接」成立。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| Protenix | AlphaFold 3 的开源复现；支持任意配体/离子/DNA/RNA/共价修饰的复合物预测 |
| MSA | 多序列比对；提供进化信息，开启更准但更慢 |
| iptm confidence | 界面（ipTM）置信度计算选项；开启更慢、结果更可信 |
| CCD 码 | 化学组分字典编码；离子/配体按此书写（锌 ZN、镁 MG、钙 CA） |
| isomeric SMILES | 带立体化学的分子线性文本表示；PubChem 分子页可直接复制 |
| grid box | 传统对接软件需要人工划定的「对接盒子」；Protenix 不需要 |
| CIF | mmCIF 结构文件格式；Protenix 输出的结构坐标（见 2.2.2） |
| 4EXS | NDM-1 与卡托普利（L-cap）共晶结构的 PDB 编号，本讲用作真值 |
