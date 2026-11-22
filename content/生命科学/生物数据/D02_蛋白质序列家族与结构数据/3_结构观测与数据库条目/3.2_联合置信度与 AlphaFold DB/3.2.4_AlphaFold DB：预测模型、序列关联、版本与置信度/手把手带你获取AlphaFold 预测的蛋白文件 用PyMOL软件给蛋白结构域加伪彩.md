# 预测结构也能当靶标：获取 AlphaFold 预测蛋白文件并用 PyMOL 按结构域上色

> 视频来源：[手把手带你获取AlphaFold 预测的蛋白文件 用PyMOL软件给蛋白结构域加伪彩](https://www.bilibili.com/video/BV1ER4y1N7xi/)（B 站，8 分钟）

## 本讲要解决的核心问题（SCQA）

**背景**：很多蛋白（尤其是新靶点）没有实验解析结构，AlphaFold 数据库几乎覆盖了整个蛋白质组的预测结构，随时可下载。

**冲突**：预测结构不能拿来就用——先要判断哪些区域可信（置信度颜色），而且数据库网页不能编辑；做图时还常想把蛋白的不同结构域（domain）用不同颜色标出来，网页上做不到。

**疑问**：怎么把 AlphaFold 预测文件拿到手、看懂它的置信度，并按 domain 上色出图？

**回答（中心思想）**：从 NCBI 定位蛋白并选对 isoform → 到 UniProt 拿官方 AlphaFold 链接和 domain 注释（记下氨基酸区间）→ 从 AlphaFold DB 下载 PDB 文件 → 在 PyMOL 里按区间选区、逐个 domain 上色、透明背景导出。视频以人类驱动蛋白 **KIF3A**（UniProt [Q9Y496](https://www.uniprot.org/uniprot/Q9Y496)）为例完整走了一遍。

## 一、置信度颜色：预测结构的「使用说明书」

AlphaFold 对预测结构的每个残基都给了置信度分数 **pLDDT**（0～100），并以颜色标在结构上：

| 颜色 | 含义 |
| --- | --- |
| 深蓝 | Very high（pLDDT > 90），可信度最高 |
| 浅蓝 | Confident（70 < pLDDT < 90） |
| 黄 | Low（50 < pLDDT < 70） |
| 橘红 | Very low（pLDDT < 50），预测可信度最低 |

这种颜色标示本身就很有用；但有时我们更想展示「这个蛋白有哪几个 domain（结构域）」，用不同颜色区分它们——这就需要把文件下载下来自己编辑。

![pLDDT 置信度颜色图例](assets/手把手带你获取AlphaFold%20预测的蛋白文件%20用PyMOL软件给蛋白结构域加伪彩/00025.webp)

## 二、NCBI → UniProt：把 isoform 与 domain 摸清

### 2.1 从 NCBI 进，选对 isoform

在 [NCBI](https://www.ncbi.nlm.nih.gov) 里直接输入关注的蛋白名称（视频搜 **kif3a**）。从科研角度建议从 NCBI 搜起，因为它列出了蛋白的不同 **isoform（转录本异构体）**——到底选哪一个 isoform，要从这里选定才能一路走通。

![NCBI 中搜索 kif3a](assets/手把手带你获取AlphaFold%20预测的蛋白文件%20用PyMOL软件给蛋白结构域加伪彩/00108.webp)

选人类的蛋白，并在几条 isoform 里选**代表最长转录本、对应这个蛋白**的那一条，然后进入 UniProt。

![RefSeq 转录本列表](assets/手把手带你获取AlphaFold%20预测的蛋白文件%20用PyMOL软件给蛋白结构域加伪彩/00138.webp)

### 2.2 UniProt：官方 AlphaFold 链接 + domain 注释

进入 UniProt 条目（[Q9Y496](https://www.uniprot.org/uniprot/Q9Y496)）后，页面里就有官方推荐的 **AlphaFold 链接**，点进去就能看到预测结构、拿到结构文件。

![UniProt 的 KIF3A 条目](assets/手把手带你获取AlphaFold%20预测的蛋白文件%20用PyMOL软件给蛋白结构域加伪彩/00173.webp)

为什么不直接去 AlphaFold 数据库？因为 UniProt 本身还对 **domain 做了注释预测**：比如 KIF3A 注释了多个结构域。先把每个 domain 的**氨基酸位次**记下来（比如 motor 结构域在 14～345），后面上色就照着这段区间来。

![UniProt Structure 栏的 domain 注释](assets/手把手带你获取AlphaFold%20预测的蛋白文件%20用PyMOL软件给蛋白结构域加伪彩/00199.webp)

## 三、下载与 PyMOL 编辑

### 3.1 从 AlphaFold DB 下载 PDB 文件

点进 AlphaFold 数据库条目（[Q9Y496](https://alphafold.ebi.ac.uk/entry/Q9Y496)）就能看到预测的蛋白结构。但**网页不能编辑**，所以要把结构文件（PDB 格式）下载到本地，例如存到桌面。

![AlphaFold DB 的 KIF3A 预测结构页](assets/手把手带你获取AlphaFold%20预测的蛋白文件%20用PyMOL软件给蛋白结构域加伪彩/00249.webp)

### 3.2 PyMOL：显示序列与整体着色

提前安装好 [PyMOL](https://pymol.org)，直接打开下载的文件。点 **Sequence**（S 图标）会显示氨基酸序列；显示方式选 **show as cartoon**（卡通模式）。先整体统一上色——比如全部改成浅蓝色，作为「底色」。

![PyMOL 打开结构并显示序列](assets/手把手带你获取AlphaFold%20预测的蛋白文件%20用PyMOL软件给蛋白结构域加伪彩/00280.webp)

### 3.3 按 domain 区间选区上色

给特定 domain 换颜色：在序列上从第 14 位选到第 345 位（这就是 motor/马达结构域），选中后先给选区重命名方便管理，再用 Color 把它改成红色。其他区域（如 372～481 及其余注释区间）同样方法分别赋不同颜色，就得到了「每个 domain 一种颜色」的效果。

![按 14–345 选区着色](assets/手把手带你获取AlphaFold%20预测的蛋白文件%20用PyMOL软件给蛋白结构域加伪彩/00330.webp)

![不同 domain 不同颜色的效果](assets/手把手带你获取AlphaFold%20预测的蛋白文件%20用PyMOL软件给蛋白结构域加伪彩/00422.webp)

### 3.4 背景透明与导出

最后把背景从白色改成透明，就可以按需要导出不同角度的图片了。

![调整背景并导出](assets/手把手带你获取AlphaFold%20预测的蛋白文件%20用PyMOL软件给蛋白结构域加伪彩/00453.webp)

## 小结

- AlphaFold 预测结构自带 pLDDT 置信度颜色：深蓝最可信、橘红最不可信，用之前先看颜色。
- 推荐路径：NCBI（选 isoform）→ UniProt（拿 AlphaFold 链接 + domain 注释）→ AlphaFold DB（下载 PDB 文件）。
- UniProt 的 domain 注释给出了每个结构域的氨基酸区间，是后续上色的「坐标表」。
- PyMOL 里四步出图：show as cartoon → 整体底色 → 按 domain 区间选区逐一上色 → 背景透明导出。
- 当靶蛋白没有实验结构时，这条「预测结构 + 置信度检查」的路线就是获取靶标结构的现实选择。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| pLDDT | AlphaFold 的逐残基置信度分数（0–100），以颜色标在结构上 |
| isoform | 同一基因经可变剪接产生的不同转录本/蛋白异构体 |
| domain（结构域） | 蛋白中相对独立的结构/功能单元，如 KIF3A 的 motor 结构域 |
| UniProt | 蛋白序列与注释数据库，提供官方 AlphaFold 链接和 domain 区间 |
| AlphaFold DB | EMBL-EBI 的预测结构数据库，按 UniProt 登录号提供 PDB/CIF 文件 |
| PyMOL | 常用分子可视化软件，支持选区、着色与高质量出图 |
