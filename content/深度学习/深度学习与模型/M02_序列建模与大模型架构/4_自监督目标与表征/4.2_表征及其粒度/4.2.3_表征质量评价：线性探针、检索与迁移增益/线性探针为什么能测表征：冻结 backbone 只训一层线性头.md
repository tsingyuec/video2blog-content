# 线性探针为什么能测表征：冻结 backbone、只训一层线性头

> 视频来源：[【3】自监督预训练模型的评估："分类" 下游任务 之 线性评估](https://www.bilibili.com/video/BV1LP41157uA/)（Bilibili · OpenMMLab）｜时长约 13 分钟
> 导读：这是一支代码教程，用 MMSelfSup 把"线性评估（linear evaluation / linear probe）"从概念一路做到跑出日志。本文按"为什么这样设计 → 权重从哪来 → 配置里哪几行决定它是线性探针 → 怎么启动与读结果 → 这个数字能说明什么"整理，重点在协议本身，命令细节只保留能复现的部分。

## 本讲要解决的核心问题（SCQA）

**背景**：自监督预训练不产生任何标签，训练完只得到一个 backbone。要判断这个 backbone 学到的图片特征好不好，就得拿它去做下游任务。

**冲突**：如果下游任务允许随便改模型——可以加层、可以解冻、可以调很久——那最后跑出来的分数里，既有 backbone 的功劳，也有你新加的那些层和调参的功劳。两个自监督方法比高低时，你无法判断差距来自表征，还是来自各自的训练配方。

**疑问**：能不能设计一个下游任务，把"表征本身好不好"和"后面那套分类器有多强"分开？如果只训练一层线性分类器，这个分数到底在测什么？

**回答（中心思想）**：线性评估把 backbone 的权重**固定住**，只在它后面接**一层新的线性分类层**，用下游任务的训练集只训练这一层。因为可训练参数被压缩到极小、模型容量被钉死，分类器能做的只有"在已有特征空间里划一刀"。所以分数高低主要反映**冻结表征是否线性可分**，而不是分类器有多聪明。 [【跳转到 00:50】](https://www.bilibili.com/video/BV1LP41157uA/?t=50)

---

## 一、先把"评估哪些任务"摆清楚

视频开篇先列出 MMSelfSup 在"分类"这条下游任务线上已经实现的几种评估方式 [【跳转到 00:00】](https://www.bilibili.com/video/BV1LP41157uA/?t=0)：

- **VOC SVM / Low-shot SVM**：在 VOC 数据集上做 SVM 评估；
- **线性评估（linear evaluation）**：也就是本讲要讲的 linear probe；
- **ImageNet 半监督分类**；
- **ImageNet 最近邻分类**。

这四种方式的共同点是：它们都**不训练（或几乎不训练）backbone**，只用 backbone 吐出来的特征去完成一个简单任务。区别在于"简单任务"由谁来做——是 SVM、是一层线性层、是用少量标签的半监督，还是干脆不算参数、直接找最近邻。

![MMSelfSup 教程的任务介绍页：列出 VOC SVM、线性评估、ImageNet 半监督分类与最近邻分类四种分类下游任务，并给出线性评估的两步基本流程](assets/线性探针为什么能测表征：冻结%20backbone%20只训一层线性头/00050.webp)

### 1.1 一条硬约束：backbone 必须对得上

教程里用加粗标出了一条容易被忽略的前提 [【跳转到 00:25】](https://www.bilibili.com/video/BV1LP41157uA/?t=25)：

> 下游任务的 backbone 必须和自监督预训练模型的 backbone 保持一致，才能进行自监督预训练权重的迁移。

这句话的含义是：线性探针测的是**某一个特定 backbone 在某一层输出的特征**。如果你把 ResNet50 预训练出来的权重硬塞进一个结构不同的网络，权重根本对不上，测出来的东西也不再是那个表征。所以"换 backbone 结构"和"换预训练方法"是两件不能混在一起比较的事。

### 1.2 线性评估的两步流程

流程本身短到可以写两行 [【跳转到 00:50】](https://www.bilibili.com/video/BV1LP41157uA/?t=50)：

1. 在自监督预训练模型的 backbone 后面，接上一层**新的线性分类层**；
2. **固定住 backbone 部分的权重**，用下游任务（分类）的数据集，只对这层新的线性分类层进行训练。

目的是"以此验证自监督预训练模型提取图片特征的效果"。

这两步里，第 2 步的"固定"是整个协议的支点。一旦 backbone 参与更新，它就会朝着下游任务去变形，测到的就不再是"预训练结束时那个表征"，而是"以它为初始化、再训练一轮之后的模型"。线性探针要的恰恰是前者。

---

## 二、探针训练数据与被评估表征的关系

初学者最容易在这里混淆：既然是"评估"，为什么还要**训练**？答案是这个训练只发生在探针上，而且它训练用的数据和被评估的表征是两套东西。

把参与方列清楚：

| 参与方 | 来源 | 在线性评估中是否更新 |
| --- | --- | --- |
| backbone（特征提取器） | 自监督预训练得到，权重从 checkpoint 载入 | 否，冻结 |
| 线性分类层（探针） | 下游任务类别数决定，随机初始化 | 是，唯一被训练的部分 |
| 训练数据 | 下游任务（这里是 Tiny ImageNet）的训练集与标注 | 只用于训练探针 |

由此可以读出三件事：

1. **探针必须用带标签的数据训练**。自监督预训练没有标签，但线性探针有：它拿下游任务的 `train.txt` 里的图片和标号，去学"这 512 维（或 2048 维）特征该判成哪一类"。所以线性评估不是"零样本"，它是"零 backbone 训练、但有标签的分类头训练"。
2. **探针的容量被协议钉死了**。只有一层线性层，意味着它只能在特征空间里做一个线性划分。如果表征本身把不同类别混在一起，再好的线性层也切不开；反之，如果表征已经把类别摊开成线性可分的簇，一层线性层就够了。这就是"分数反映表征"的机制。
3. **探针的数据量和训练轮数是被控制住的**。视频里这份配置只跑 5 个 epoch [【跳转到 08:33】](https://www.bilibili.com/video/BV1LP41157uA/?t=513)。轮数少、模型小，探针本身没有能力"记住"训练集，也就没法靠过拟合把分数刷上去——它只能去逼近这个特征空间里线性可分的那条边界。

反过来说，如果换了协议——比如允许多层 MLP 当探针、或者允许训练很久——那分数里就掺进了探针的容量。这时候"探针分数高"不再等价于"表征好"，可能只是探针更强。**读线性探针的数字，前提是知道探针有多弱。**

---

## 三、权重从哪来：checkpoint 与 backbone 权重

线性评估要的只是 backbone 那一段权重，但自监督训练保存下来的文件往往是一个完整模型（可能还带着投影头、动量编码器等训练期组件）。教程把情况分成两种 [【跳转到 03:20】](https://www.bilibili.com/video/BV1LP41157uA/?t=200)：

- **自监督训练过程中直接保存的 checkpoint**（例如 `epoch_1.pth`）：需要用工具先提取它 backbone 部分的权重；
- **MMSelfSup 模型库里的模型文件**：这些文件已经是提取过 backbone 权重的，下载下来直接用。

提取用的是 `tools/model_converters/extract_backbone_weight.py`，两个参数 [【跳转到 05:00】](https://www.bilibili.com/video/BV1LP41157uA/?t=300)：

- `checkpoint`：自监督预训练过程中保存下来的模型文件路径（这里是 `epoch_1.pth`）；
- `model_file`：输出的 backbone 权重文件保存路径（这里命名成 `backbone.pth`）。

```bash
python tools/model_converters/extract_backbone_weight.py \
    work_dirs/selfsup/simclr/simclr_resnet50_1xb32-coslr-le_tinyin200/epoch_1.pth \
    work_dirs/selfsup/simclr/simclr_resnet50_1xb32-coslr-le_tinyin200/backbone.pth
```

跑完刷新目录，会多出一个 `backbone.pth`。这一步看着琐碎，但它保证了一件事：**接下来被冻结、被评估的，确实是预训练的那个特征提取器，而不是夹带了训练期辅助模块的整包权重**。

![教程第 3.1 节：把 SimCLR 预训练保存的 epoch_1.pth 下载到 work_dirs 下与预训练配置同名的文件夹，供下一步提取 backbone 权重](assets/线性探针为什么能测表征：冻结%20backbone%20只训一层线性头/00300.webp)

---

## 四、配置文件里，哪几行决定了"这是线性探针"

教程的做法是新建一个配置文件，继承已有的线性评估配置，再改参数。继承哪个文件？先到模型库找到对应算法（这里是 SimCLR），点进去能看到线性评估的结果 [【跳转到 07:13】](https://www.bilibili.com/video/BV1LP41157uA/?t=433)：feature1 到 feature5 用的是一个配置，而"对 average pooling 的特征做线性评估"用的是另一个配置。这份配置里有四条关键信息 [【跳转到 07:43】](https://www.bilibili.com/video/BV1LP41157uA/?t=463)：

```python
_base_ = [
    '../_base_/models/resnet50.py',
    '../_base_/datasets/imagenet.py',
    '../_base_/schedules/lars_coslr-90e.py',
    '../_base_/default_runtime.py',
]

model = dict(backbone=dict(frozen_stages=4))   # 冻结 backbone
data = dict(samples_per_gpu=512, workers_per_gpu=8)
```

![线性评估配置文件的骨架：继承四大组件，其中 model 里写 frozen_stages=4、data 里 samples_per_gpu=512，注释说明这是 SimSiam 论文的线性评估设置](assets/线性探针为什么能测表征：冻结%20backbone%20只训一层线性头/00463.webp)

逐条读：

- **`frozen_stages=4`**：把 backbone 的四个 stage 全部冻结。这一行就是"线性探针"与"微调"的分界线——同样是接一个分类头，冻结与否决定了你测的是表征还是模型。
- **`samples_per_gpu=512`**：单卡 batch size。教程里改成单卡训练时，配置名也跟着写成 `resnet50_linear-1xb512`。
- **数据集继承自 `imagenet.py`**：因为用的是 Tiny ImageNet，必须把数据集目录和标注文件路径改到 `data/tiny-imagenet-200`，训练集标注用 `train.txt`，验证集路径与标注同样要改（视频里还把规模缩小为原来的 1/8）。
- **训练轮数**：`max_epochs=5`。

还有一个容易被忽略的细节：**学习率要跟着 batch size 一起改**。配置里能看到按比例缩放的写法：

```python
optimizer = dict(lr=1.6 * ((512 * 1) / (512 * 8)))
```

原来是 8 卡 × 512，现在 1 卡 × 512，总 batch 变成原来的 1/8，学习率也按 1/8 缩。线性探针虽然只训一层，但它依然是一个正常的优化问题，batch 变了学习率不跟着变，5 个 epoch 内的收敛行为就会不一样——而这会直接污染你读到的那个精度数字。

![教程第 4.1 节列出写配置的五个步骤：继承配置、改 samples_per_gpu 与 workers_per_gpu、改数据集与标注路径、按 batch size 调整学习率、改总 epoch 数](assets/线性探针为什么能测表征：冻结%20backbone%20只训一层线性头/00513.webp)

---

## 五、启动与读结果

启动用 `tools/benchmarks/classification/dist_train_linear.sh`，前面加环境变量指定卡数，后面跟两个路径 [【跳转到 10:38】](https://www.bilibili.com/video/BV1LP41157uA/?t=638)：

```bash
GPUS=1 bash tools/benchmarks/classification/dist_train_linear.sh \
    configs/benchmarks/classification/imagenet/resnet50_linear-1xb512-coslr-5e_tinyin200.py \
    checkpoints/simclr_resnet50_8xb32-coslr-200e_in1k_20220428-46ef6bb9.pth
```

- `GPUS`：默认是 8，只有一张卡时必须显式设成 1；
- `CONFIG`：线性评估的配置文件路径；
- `PRETRAIN`：自监督预训练模型的 backbone 权重文件路径。

![线性评估的启动命令与三个参数说明：GPUS 环境变量、CONFIG 配置文件、PRETRAIN 预训练 backbone 权重](assets/线性探针为什么能测表征：冻结%20backbone%20只训一层线性头/00663.webp)

跑起来之后，从日志里能确认配置真的生效了 [【跳转到 11:28】](https://www.bilibili.com/video/BV1LP41157uA/?t=688)：训练集和验证集的数据集、标注文件路径都被改了过来，runner 也被设置为只跑 5 个 epoch。5 个 epoch 之后，loss 不断下降、正确率不断提升，最新 checkpoint 落在 `work_dirs` 下 benchmark 的 classification/imagenet 目录里 [【跳转到 12:43】](https://www.bilibili.com/video/BV1LP41157uA/?t=763)。

![训练日志：每轮 196 个 iter，5 个 epoch 跑完，学习率按 cosine 从 1.8e-01 衰减到 1.9e-02，最后保存第 5 个 epoch 的 checkpoint](assets/线性探针为什么能测表征：冻结%20backbone%20只训一层线性头/00763.webp)

日志里的 `lr` 从 1.809e-01 一路 cosine 衰减到 1.910e-02，这就是前面那条按 batch 缩放过的学习率在跑。**这个精度数字，就是这份配置交给你的"表征质量读数"。**

---

## 六、这个数字能说明什么、不能说明什么

把协议拆完之后，可以给线性探针的读数划出边界：

**能说明的**

- 在这份下游数据上，这个冻结表征**线性可分到什么程度**。分数高，说明特征空间里类别已经分得比较开，一层线性层就能切开。
- **同一份配置下**，不同自监督方法（SimCLR、MoCo v2、BYOL、SwAV……）的横向比较。模型库那张表里，每种算法后面都跟着自己的线性评估 config 与结果 [【跳转到 07:13】](https://www.bilibili.com/video/BV1LP41157uA/?t=433)，比分的前提就是大家用的是同一套探针协议。

![MMSelfSup 模型库表格：每种自监督算法对应一行 config 与 model/log 下载链接，线性评估结果就是按这些配置逐行跑出来的](assets/线性探针为什么能测表征：冻结%20backbone%20只训一层线性头/00438.webp)

**不能说明的**

- **不能跨数据集直接比**。换成 Tiny ImageNet 200 类、或换成 ImageNet 1000 类，类别数、训练样本数都变了，探针难度也变了。所以配置里数据集路径、标注文件、类别数必须一起改，改完的数字只在这个数据集内部有意义。
- **不能把"探针分数"当成"表征的全部能力"**。线性探针只问"线性可分吗"，它不问"用非线性头能不能更好"、"拿去做检索能不能召回"、"迁移到别的任务上能不能涨点"。教程里另外三种评估方式（SVM、半监督、最近邻）就是在换问法：SVM 换了一个更强的分类器，最近邻干脆不算参数、只比距离。同一个 backbone 在这几种评估下的排名不一定一致，因为它们测的是表征的不同侧面。
- **不能忽略探针自身的设定**。5 个 epoch、单层线性、学习率随 batch 缩放——这些是协议的一部分。改掉其中任何一项，数字就会变，而表征一点没变。

一句话总结这一节：**线性探针是一个受控实验，它的价值来自"控制"，不来自那个百分数本身。** 报告这个数字时，必须同时报告探针是什么、在哪个数据集上、训了多久。

---

## 小结

- 线性评估（linear probe）的两步：在 backbone 后接一层新的线性分类层；**冻结 backbone**，只用下游训练集训练这一层。
- 它测的是**冻结表征的线性可分性**，不是模型的全部能力；探针容量被钉死，才使得分数差异能归因到表征。
- 探针需要**带标签的下游数据**训练，但 backbone 不更新；探针的数据量、轮数、学习率都是协议的一部分，改了数字就不可比。
- 下游 backbone 必须与预训练 backbone 结构一致，否则权重对不上，评估无效。
- 工程上三件事不能漏：从 checkpoint 提取 `backbone.pth`、配置里写 `frozen_stages`、学习率按 batch size 缩放。
- 同一个 backbone 换评估方式（SVM、半监督、最近邻、检索、迁移）会得到不同读数，它们各自回答不同的问题。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| 线性评估 / 线性探针（linear evaluation / linear probe） | 冻结预训练 backbone，只在其特征上训练一层线性分类器，用该分类器的精度衡量表征质量 |
| 冻结（freeze） | 把某些层的权重固定，反向传播不更新它们；配置里体现为 `frozen_stages` 或学习率置 0 |
| backbone | 特征提取主干网络；线性评估中被冻结、被评估的那一段 |
| 探针（probe） | 接在冻结特征后面的小分类器；线性探针只有一层线性层 |
| average pooling 特征 | 把 backbone 输出的空间特征按通道取平均得到的全局向量，是线性评估的一种输入形式 |
| 线性可分 | 存在一个线性划分能把不同类别的特征分开；线性探针的精度就是它的一个代理指标 |
| Tiny ImageNet | ImageNet 的缩小版（200 类），教程用它做线性评估以降低算力开销 |
| 迁移（transfer） | 把一个任务上学到的权重用到另一个任务；线性评估是迁移能力最弱、也最干净的一种用法 |