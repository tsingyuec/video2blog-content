# 用 Python 上手 ESM-2：提取蛋白质嵌入，再微调成酶最佳 pH 预测器

> 来源视频：[Using ESM-2 in Python: Protein Embeddings & Fine-Tuning](https://www.youtube.com/watch?v=i2kz72NIpNs) · 时长 11:01 · ProteinVision
> 本篇基于视频英文 AI 字幕与画面整理（中译），时间戳可跳转回原视频对应位置。
> 知识树定位：4.2 序列语言模型（PLM）→ 4.2.3 ESM2 的下篇（上篇讲架构与训练）。演示代码来自视频配套的 Jupyter Notebook，加载的正是最小的 ESM2-8M——也是本系列 5.2.3 节抗菌肽生成模型 AMP-Diffusion 的底座。

## 本讲要解决的核心问题（SCQA）

**背景**：上篇讲清了 ESM2 的内部构造——Transformer 编码器、RoPE 旋转位置编码、掩码语言建模预训练，以及「均值池化 / cls 词元」两种蛋白质表示。

**冲突**：但「知道原理」和「用起来」之间隔着工程鸿沟：序列怎么喂进模型？表示藏在输出张量的哪个位置、形状是什么？想让它预测一条性质（比如酶的最佳 pH），又该怎么在预训练模型上加自己的预测头？

**疑问**：能不能用一小段代码，从「跑通推理」一路走到「微调成自己的回归器」？

**回答（中心思想）**：可以，路线是三步——①加载预训练的 8M 模型，用 `batch_converter` 把序列变词元、`repr_layers` 取最后一层表示、元素均值池化得到整条蛋白嵌入；②准备酶最佳 pH 数据集（7124 训练 / 760 验证 / 1971 测试）；③给 ESM2 加一个两层 MLP 预测头 `ESM_FFN`，用 MSE 损失 + Adam 优化器微调 3 个周期，验证 R² 从 0.375 提升到 0.380 [【跳转到 00:00】](https://www.youtube.com/watch?v=i2kz72NIpNs&t=0)。

## 一、加载预训练模型：8M 参数的 esm2_t6_8M_UR50D

先加载 `torch` 和 `esm` 包，选定设备（有 CUDA GPU 用 GPU，否则 CPU；演示是在笔记本 CPU 上跑的），然后两行代码拿到模型和词表工具 [【跳转到 01:41】](https://www.youtube.com/watch?v=i2kz72NIpNs&t=101)：

```python
import torch, esm
device = "cuda" if torch.cuda.is_available() else "cpu"
model, alphabet = esm.pretrained.esm2_t6_8M_UR50D()  # esm.pretrained.esm2_t33_650M_UR50D()
last_layer = len(model.layers)          # 6
batch_converter = alphabet.get_batch_converter()
model.eval()
```

模型名 `esm2_t6_8M_UR50D` 的含义：**t6 = 6 个 Transformer 层，8M = 800 万参数**；注释掉的 `esm2_t33_650M_UR50D` 就是上篇讲的主力 650M 版本（33 层、隐藏维度 1280）。首次加载会从网上下载权重、需要几分钟，之后就走缓存了。选最小模型是因为演示在笔记本上运行。

![加载 8M 模型：t6=6 层、8M 参数，注释行是 650M 主力版本](assets/Using%20ESM-2%20in%20Python：%20Protein%20Embeddings%20%26%20Fine-Tuning/00101.webp)

顺便可以打印词表，它就是一个字符串 → 词元 ID 的字典：`'<cls>':0, '<pad>':1, '<eos>':2, '<unk>':3, 'L':4, 'A':5, 'G':6, ...`——分类词元是 0 号，序列结束词元是 2 号，每个氨基酸各占一个 ID。

## 二、序列 → 词元 ID：batch_converter

模型要吃词元 ID 序列。用 `batch_converter` 一步完成：输入是一个列表，每个元素是 `(蛋白质标识符, 氨基酸序列)` 的元组 [【跳转到 02:31】](https://www.youtube.com/watch?v=i2kz72NIpNs&t=151)：

```python
sequence = "MKTGK"
batch = [("Protein 1", sequence)]
batch_labels, batch_strs, batch_tokens = batch_converter(batch)
# batch_tokens: tensor([[0, 20, 15, 11, 6, 15, 2]])
```

对照词表读这串 ID：开头 `0` 是分类词元，结尾 `2` 是序列结束词元，中间 `20,15,11,6,15` 正是 M、K、T、G、K 五个氨基酸。往后看还有多条序列同批的例子——比如 `("Protein 1","KMKMKMKA")` 与 `("Protein 2","MALK")`，短序列会在结束词元后用 `<pad>`（ID 1）补齐，方便同批张量化。

![MKTGK 的词元化结果与模型前向调用](assets/Using%20ESM-2%20in%20Python：%20Protein%20Embeddings%20%26%20Fine-Tuning/00151.webp)

## 三、运行模型：logits 与最后一层表示

推理模式（`torch.no_grad()`）下把批次送进模型，请求最后一层的表示 [【跳转到 04:11】](https://www.youtube.com/watch?v=i2kz72NIpNs&t=251)：

```python
batch_tokens = batch_tokens.to(device)
with torch.no_grad():
    results = model(batch_tokens, repr_layers=[last_layer], return_contacts=False)
```

输出里有两样东西：

- `results["logits"]`：对序列每个位置的氨基酸预测分数——这是掩码语言建模训练目标的产物；
- `results["representations"][6]`：**最后一层（第 6 层）的表示**，这才是我们真正想要的。

表示张量的形状是 **1×7×320**：1 是批次大小，7 是序列长度（2 个特殊词元 + 5 个氨基酸词元），320 是氨基酸表示的隐藏维度——8M 模型是 320；如果换成 650M 模型，这一维就是 1280。

![模型输出：logits 与第 6 层表示张量](assets/Using%20ESM-2%20in%20Python：%20Protein%20Embeddings%20%26%20Fine-Tuning/00251.webp)

## 四、整条蛋白的嵌入：元素均值池化

很多下游任务希望「一条蛋白质 = 一个向量」。上篇讲过做法：**对所有氨基酸嵌入逐元素取平均**。这里排除位置 0 的分类词元和末尾的结束词元，只对中间 5 个氨基酸的嵌入求均值，得到一个 **320 维**的向量。视频把「序列 → 词元 → 前向 → 池化」合并成一个函数：输入序列、模型和批量转换器，直接返回这条序列的 ESM2 蛋白质嵌入 [【跳转到 05:01】](https://www.youtube.com/watch?v=i2kz72NIpNs&t=301)。

## 五、微调任务：预测酶的最佳 pH

接下来把预训练模型改造成回归器：输入氨基酸序列，输出酶的**最佳 pH**——即酶催化速率最高时的 pH 值。

### 5.1 数据集

数据来自 Gado、Knotts、Shaw 等人 2025 年发表在 *Nature Machine Intelligence* 的论文《Machine learning prediction of enzyme optimum pH》（CC BY 4.0 许可，Zenodo 提供下载）。笔记本读入三份 Excel：训练集 **7124** 条、验证集 **760** 条、测试集 **1971** 条，每行是「最佳 pH + 序列」（比如 `MAKFVIRPATAADCSDILRLIKELAKYEYMEEQVILTEKDLLEDGF...`）[【跳转到 06:16】](https://www.youtube.com/watch?v=i2kz72NIpNs&t=376)。

![最佳 pH 数据集：7124/760/1971 三份划分与论文引用](assets/Using%20ESM-2%20in%20Python：%20Protein%20Embeddings%20%26%20Fine-Tuning/00376.webp)

预处理只有一件事：把所有目标 pH **归一化**到近似均值 0、标准差 1 的高斯分布——这对神经网络训练更友好。还定义了一个计算**决定系数 R²** 的函数（1 − MSE/方差），用来监控回归质量。

### 5.2 自定义 Dataset 与 DataLoader

批次大小设为 **4**（可按设备内存与性能调整），再写一个标准的 PyTorch `Dataset`：返回每个数据点的 `(序列, 最佳pH)`。训练集 `shuffle=True` 打乱，验证/测试集不打乱 [【跳转到 06:52】](https://www.youtube.com/watch?v=i2kz72NIpNs&t=412)。

![ESM2Dataset 与三个 DataLoader](assets/Using%20ESM-2%20in%20Python：%20Protein%20Embeddings%20%26%20Fine-Tuning/00412.webp)

## 六、预测头：ESM_FFN

微调部分重新加载 8M 模型，这次切到**训练模式**（`model.train()`），并取出几个关键量：层数、嵌入维度（`model.embed_dim` = 320）、MLP 隐藏维度 **128**、学习率 **1e-5**、训练 **3 个周期（epoch）** [【跳转到 07:42】](https://www.youtube.com/watch?v=i2kz72NIpNs&t=462)。

![微调准备：重新加载 8M 模型并设定超参数](assets/Using%20ESM-2%20in%20Python：%20Protein%20Embeddings%20%26%20Fine-Tuning/00462.webp)

预测头是一个叫 `ESM_FFN` 的类：外层是 ESM2 模型，里面用 `torch.nn.Sequential` 搭一个两层 MLP——`Linear(320, 128)` → `ReLU` → `Linear(128, 1)`，输出单一数值（预测的最佳 pH）[【跳转到 08:07】](https://www.youtube.com/watch?v=i2kz72NIpNs&t=487)。

```python
class ESM_FFN(torch.nn.Module):
    def __init__(self, esm2_model, emb_dim, hidden_dim, last_layer):
        super().__init__()
        self.esm2_model = esm2_model
        self.MLP = torch.nn.Sequential(
            torch.nn.Linear(emb_dim, hidden_dim),
            torch.nn.ReLU(),
            torch.nn.Linear(hidden_dim, 1),
        )
    def forward(self, batch_tokens):
        results = self.esm2_model(batch_tokens, repr_layers=[self.last_layer], return_contacts=False)
        cls_repr = results["representations"][self.last_layer][:, 0, :]   # 位置 0 的分类词元
        return self.MLP(cls_repr)
```

前向传播里先从 ESM2 拿最后一层表示，再**提取位置 0 的分类词元**作为整条蛋白的表示（上篇讲过的 cls 路线）；讲解里也说明，用**元素均值池化**代替 cls 通常得到非常接近的结果。类里还有一个可选的 `extract_representation` 方法：微调完成后，可以用它取回「更新过」的 cls 表示，作为特定任务的蛋白质嵌入。

![ESM_FFN 类定义：ESM2 表示 → cls 词元 → 两层 MLP → 单值](assets/Using%20ESM-2%20in%20Python：%20Protein%20Embeddings%20%26%20Fine-Tuning/00487.webp)

## 七、训练循环：MSE 损失 + Adam 优化器

训练配置只有两行核心：损失用**均方误差 MSE**，优化器用 **Adam**（学习率 1e-5，作用于 ESM2 和预测头的全部参数）。每个周期的循环是标准五步：转批次（每批现过 `batch_converter`）→ `optimizer.zero_grad()` → 前向 → `loss.backward()` → `optimizer.step()`，用 tqdm 显示进度并记录训练损失；周期结束后跑验证循环（eval + no_grad），计算并打印平均平方误差与 R² [【跳转到 09:22】](https://www.youtube.com/watch?v=i2kz72NIpNs&t=562)。

![MSE 损失、Adam 优化器与训练/验证双循环](assets/Using%20ESM-2%20in%20Python：%20Protein%20Embeddings%20%26%20Fine-Tuning/00562.webp)

## 八、结果与解读

在笔记本 CPU 上，每个周期约 **41 分钟**（1781 个批次，恰好 7124÷4）。训练日志清晰可见进步 [【跳转到 10:12】](https://www.youtube.com/watch?v=i2kz72NIpNs&t=612)：

| 周期 | 训练损失 | 验证损失 | 验证 R² |
| --- | --- | --- | --- |
| Epoch 1 | 0.615135 | 0.665324 | 0.374745 |
| Epoch 2 | 0.481702 | 0.659893 | 0.379849 |

![训练日志：损失下降、验证 R² 缓慢提升](assets/Using%20ESM-2%20in%20Python：%20Protein%20Embeddings%20%26%20Fine-Tuning/00612.webp)

损失在下降、性能在提升，继续训练还有提升空间。测试集表现比验证集更好——原因不是运气：**验证集特意选取与训练集差异很大的序列**，本来就比测试集更难预测。

## 小结

- 推理三件套：`esm2_t6_8M_UR50D()` 加载 8M 模型，`batch_converter` 把 `(名称, 序列)` 列表变词元 ID（cls=0、eos=2、pad=1），`repr_layers=[6]` 取最后一层表示，形状 `批次×长度×320`。
- 整条蛋白嵌入 = 排除 cls 与 eos 后对氨基酸嵌入**逐元素取均值**，得到 320 维向量（650M 则是 1280 维）。
- 微调配方：`ESM_FFN`（Linear 320→128 → ReLU → Linear 128→1）接在 cls 表示上，**MSE + Adam(1e-5)**，batch_size=4，3 个周期。
- 结果：每周期约 41 分钟（CPU），训练损失 0.615→0.482，验证 R² 0.375→0.380；测试集比特意选难的验证集更容易。
- 这套「预训练底座 + 小预测头」的模式，正是本系列后续模型（如 ABDP 的 pI/Tm 回归）的通用形态。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| batch_converter | 把 `(名称, 序列)` 列表转成词元 ID 张量，自动加 cls/eos、补 pad |
| repr_layers | 指定取哪一层的表示；`representations[last_layer]` 即最后一层输出 |
| 元素均值池化 | 对所有氨基酸嵌入逐元素平均，得到整条蛋白的单一向量 |
| 预测头（MLP） | 接在 ESM2 表示后的小网络；本例为 Linear(320,128)→ReLU→Linear(128,1) |
| MSE / R² | 回归损失与决定系数；R² 越接近 1 拟合越好 |
| 最佳 pH | 酶催化速率最高时的 pH，本篇微调任务的回归目标 |
