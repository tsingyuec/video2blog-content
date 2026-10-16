# Using Boltz-2 NIM： A Short Tutorial

> 视频来源：[Using Boltz-2 NIM: A Short Tutorial](https://www.youtube.com/watch?v=Ej_iKFcNEfA)（MIT Jameel Clinic，2025-07，4 分 07 秒）
> 主讲人：Tally Portnoi（Boltz-2 论文共同作者、MIT Regina Barzilay 实验室博士生，[【跳转到 00:00】](https://www.youtube.com/watch?v=Ej_iKFcNEfA&t=0)）

## 本讲要解决的核心问题（SCQA）

**背景**：Boltz-2 是 MIT 推出的最先进生物分子结构预测模型，能对涉及蛋白质、DNA、RNA 和小分子的复合物做快速、高精度的结构预测，还特别擅长预测结合亲和力（[【跳转到 00:05】](https://www.youtube.com/watch?v=Ej_iKFcNEfA&t=5)）。但想在本地跑它，得装环境、下权重。

**冲突**：大多数时候我们只想快速验证一个体系——最好打开网页、贴上序列就能出结构，而不是先折腾半天的部署。

**疑问**：不装任何环境，能不能几分钟内完成一次带共价键、口袋约束的复合物预测？

**回答**：可以。NVIDIA 把 Boltz-2 封装成了 **NIM** 网页服务：添加组件 →（可选）加口袋约束 → 点 Run 就出结构；同一个服务还能用 Python、shell、node 脚本调用（[【跳转到 03:55】](https://www.youtube.com/watch?v=Ej_iKFcNEfA&t=235)）。

## 一、Boltz-2 NIM：网页里就能用的复合物预测服务

### 1.1 Boltz-2 是什么

Boltz-2 是一种**最先进的生物分子结构预测模型**，可对涉及蛋白质、DNA、RNA 和小分子的复合物进行快速、高精度的结构预测（[【跳转到 00:10】](https://www.youtube.com/watch?v=Ej_iKFcNEfA&t=10)）。它特别擅长**预测结合亲和力**——也就是配体与蛋白结合得有多紧。不过主讲人说明：由于 NVIDIA 网站目前尚未提供亲和力功能，本教程将专注于结构预测。

![Boltz-2 定位介绍画面](assets/Using%20Boltz-2%20NIM：%20A%20Short%20Tutorial/00010.webp)

### 1.2 NIM 把模型变成开箱即用的服务

打开入口 **build.nvidia.com/mit/boltz2**，就能看到操作 Boltz-2 模型的网页界面（[【跳转到 00:27】](https://www.youtube.com/watch?v=Ej_iKFcNEfA&t=27)）。

> **NIM 是什么**：NVIDIA Inference Microservice（推理微服务）——把大模型打包成标准化的网页/API 服务，使用者不需要关心底层环境。本系列 5.1.2 的 OpenFold3 同样提供 NIM 入口。

![build.nvidia.com 上 Boltz-2 的网页界面](assets/Using%20Boltz-2%20NIM：%20A%20Short%20Tutorial/00027.webp)

界面里点 **View Examples** 可以看到预置的不同生物分子复合物示例（[【跳转到 00:37】](https://www.youtube.com/watch?v=Ej_iKFcNEfA&t=37)）。网页之外，页面上还提供了用 **Python 脚本、shell 和 node** 调用 NVIDIA 服务来使用 Boltz-2 的示例（[【跳转到 03:55】](https://www.youtube.com/watch?v=Ej_iKFcNEfA&t=235)）——同一套能力，既能点鼠标用，也能写脚本用。

## 二、读懂官方示例：激酶 + 共价配体的三组件输入

我们先讲预置的「**人源激酶蛋白 + 共价配体**」例子，再演示如何输入自己的体系（[【跳转到 00:42】](https://www.youtube.com/watch?v=Ej_iKFcNEfA&t=42)）。

![View Examples 中的预置复合物示例列表](assets/Using%20Boltz-2%20NIM：%20A%20Short%20Tutorial/00042.webp)

这个复合物由**三个组成部分**构成（[【跳转到 00:57】](https://www.youtube.com/watch?v=Ej_iKFcNEfA&t=57)）：

1. **蛋白质链 A**：激酶蛋白的氨基酸序列；
2. **配体组分**：由 **CCD 代码** U4U 指定（[【跳转到 01:04】](https://www.youtube.com/watch?v=Ej_iKFcNEfA&t=64)）。CCD（Chemical Component Dictionary，化学组分字典）是 PDB 的标准配体命名体系——ATP、ZN 这类小分子都有统一的三字母代号，模型按代号查到分子的原子结构；
3. **一条共价键**：规定**残基 12 的硫原子与配体上的碳原子成键**（[【跳转到 01:04】](https://www.youtube.com/watch?v=Ej_iKFcNEfA&t=64)、[【跳转到 01:23】](https://www.youtube.com/watch?v=Ej_iKFcNEfA&t=83)）。这是「共价配体」场景：药物与蛋白不是靠弱相互作用贴合，而是形成了真实的化学键，建模时必须显式声明。

![复合物的三个组成部分：蛋白链、配体、共价键](assets/Using%20Boltz-2%20NIM：%20A%20Short%20Tutorial/00057.webp)

![配体由 CCD 代码 U4U 指定，并声明共价键](assets/Using%20Boltz-2%20NIM：%20A%20Short%20Tutorial/00064.webp)

![共价键：残基 12 的硫原子连到配体碳原子上](assets/Using%20Boltz-2%20NIM：%20A%20Short%20Tutorial/00083.webp)

这样的输入会得到右边的输出结构（[【跳转到 01:23】](https://www.youtube.com/watch?v=Ej_iKFcNEfA&t=83)）。

## 三、手动搭建带口袋约束的预测

点 **Clear All** 清空所有组件（[【跳转到 01:30】](https://www.youtube.com/watch?v=Ej_iKFcNEfA&t=90)），然后以**口袋（pocket）约束**为例手动搭建一个体系：

**第 1 步：添加蛋白。** 把蛋白序列复制粘贴进来；如果自己有 **MSA**（多序列比对，给模型提供同源序列的共进化信号）也可以在这里提供，本例没有提供，照样能跑（[【跳转到 01:37】](https://www.youtube.com/watch?v=Ej_iKFcNEfA&t=97)）。

![手动添加蛋白序列，MSA 为可选项](assets/Using%20Boltz-2%20NIM：%20A%20Short%20Tutorial/00097.webp)

**第 2 步：添加配体（ligand）。** 这次不用 CCD 代码，而是用 **SMILES 字符串**指定（[【跳转到 02:02】](https://www.youtube.com/watch?v=Ej_iKFcNEfA&t=122)）——SMILES 是把分子结构写成一行文本的规范，适合描述字典里没有的新分子。从下拉菜单选择 ligand、点下新增按钮、把 SMILES 粘贴进来即可。本例的配体是 **ATP**。

**第 3 步：添加口袋约束。** 也就是告诉 Boltz-2：我期望这个配体结合到蛋白的哪个位置（[【跳转到 02:27】](https://www.youtube.com/watch?v=Ej_iKFcNEfA&t=147)）。具体声明为：**配体 ATP 与蛋白 A 链结合，并接触第 12、15 和 18 位残基**（[【跳转到 02:27】](https://www.youtube.com/watch?v=Ej_iKFcNEfA&t=147)、[【跳转到 02:52】](https://www.youtube.com/watch?v=Ej_iKFcNEfA&t=172)）。口袋约束相当于把结合位点"钉住"，让模型在这个区域内摆放配体。

![用 SMILES 添加配体，并准备添加 pocket 约束](assets/Using%20Boltz-2%20NIM：%20A%20Short%20Tutorial/00122.webp)

![声明 ATP 与蛋白 A 链结合、接触第 12/15/18 位残基](assets/Using%20Boltz-2%20NIM：%20A%20Short%20Tutorial/00147.webp)

全部输入完成后点击运行，稍等片刻就得到结构图，可以直接在界面里查看（[【跳转到 02:52】](https://www.youtube.com/watch?v=Ej_iKFcNEfA&t=172)）。

![口袋约束示例的预测结果结构](assets/Using%20Boltz-2%20NIM：%20A%20Short%20Tutorial/00172.webp)

## 四、免疫场景：MHC 蛋白与多肽一起折叠

主讲人再演示一个例子：把 **MHC 蛋白和多肽放在一起折叠**（[【跳转到 02:52】](https://www.youtube.com/watch?v=Ej_iKFcNEfA&t=172)、[【跳转到 03:17】](https://www.youtube.com/watch?v=Ej_iKFcNEfA&t=197)）。

操作依旧两步（[【跳转到 03:22】](https://www.youtube.com/watch?v=Ej_iKFcNEfA&t=202)）：

1. 添加一种蛋白：输入 **HLA-A02**（HLA 是人类 MHC 的名字，负责向免疫系统呈递肽段）；
2. 再点一次蛋白，加入**多肽序列**，然后点击运行。

现在就得到了 **MHC 蛋白与多肽在一起的复合物**——这正是免疫识别场景里最常见的预测需求（[【跳转到 03:44】](https://www.youtube.com/watch?v=Ej_iKFcNEfA&t=224)）。

![添加 HLA-A02 蛋白与多肽序列](assets/Using%20Boltz-2%20NIM：%20A%20Short%20Tutorial/00202.webp)

![MHC 蛋白与多肽复合物的预测结果](assets/Using%20Boltz-2%20NIM：%20A%20Short%20Tutorial/00224.webp)

## 小结

- Boltz-2 是 MIT 的开源 AF3 类模型：蛋白/DNA/RNA/小分子复合物的快速高精度结构预测，亲和力预测是它的强项（视频时点 NVIDIA 网页端尚未上线该功能）。
- **NIM** 把 Boltz-2 变成开箱即用的网页服务（build.nvidia.com/mit/boltz2），并提供 Python / shell / node 三种脚本调用方式。
- 输入体系的三类要素：**蛋白**（贴序列，MSA 可选）、**配体**（CCD 代码或 SMILES）、**关系约束**（共价键、口袋）。
- 官方示例覆盖三类典型场景：共价配体（激酶 + U4U）、口袋约束（ATP 接触指定残基）、免疫复合物（HLA-A02 + 肽）。
- 对本系列而言，这正是 5.1「结构预测域」中 Boltz-2 的 **NIM 入口**用法；输入 JSON 细节见 2.5.3，模型架构见 4.3.3。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| Boltz-2 | MIT 开源的 AF3 类生物分子结构预测模型，可预测蛋白/DNA/RNA/小分子复合物结构，兼长亲和力预测 |
| NIM | NVIDIA Inference Microservice，把模型封装成网页/API 服务，免部署直接调用 |
| CCD 代码 | PDB 化学组分字典的配体代号（如 U4U、ATP），模型按代号取原子结构 |
| SMILES | 把分子结构写成一行文本的线性表示法，适合描述任意新分子 |
| 共价键约束 | 显式声明配体与蛋白某残基成键（如残基 12 硫原子—配体碳原子） |
| pocket（口袋） | 指定配体应结合的位置：声明配体接触哪些残基（如 12/15/18） |
| MSA | 多序列比对，为结构预测提供同源序列的共进化信息，可选项 |
| MHC / HLA | 向免疫系统呈递肽段的蛋白；HLA 是人类的 MHC |
