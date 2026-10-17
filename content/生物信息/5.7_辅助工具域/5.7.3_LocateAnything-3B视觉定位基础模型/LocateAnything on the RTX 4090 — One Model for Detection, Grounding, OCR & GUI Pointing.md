# LocateAnything on the RTX 4090 — One Model for Detection, Grounding, OCR & GUI Pointing

## 本讲要解决的核心问题（SCQA）

**背景**：LocateAnything 是 NVIDIA Eagle 家族的通用视觉定位基础模型，诞生于 H100 数据中心集群，论文参数漂亮：单卡每秒 12.7 个框、ScreenSpot-Pro 60.3 分。

**冲突**：这些数字离消费级用户很远——一张 RTX 4090 能否复现？模型默认配置在 Ada 显卡上根本起不来，大图推理还要爆 40GB 显存。

**疑问**：一张桌面 4090 到底要付出多少工程成本，才能跑出接近数据中心的五种定位任务？

**回答（中心思想）**：能跑——3B 模型 bfloat16 只占约 7GB 显存；但必须手动把注意力后端从 Magi 换成 SDPA、把大图 token 上限压到 6400，再理顺安装顺序；装好后目标检测、短语定位、场景文本、GUI、指点五种任务与 fast/slow/hybrid 三种解码模式全部可用。

> 视频来源：[LocateAnything on the RTX 4090 — One Model for Detection, Grounding, OCR & GUI Pointing](https://www.youtube.com/watch?v=YyMhtCXMfXo)（YouTube，13 分 50 秒）。

![视频开场：一张 3B 模型要在任意图片里"定位任何东西"](assets/LocateAnything%20on%20the%20RTX%204090%20—%20One%20Model%20for%20Detection,%20Grounding,%20OCR%20&%20GUI%20Pointing/00000.webp)

## 一、模型本体：三件套架构与通用定位设计

### 1.1 三件套：编码器、解码器、投影器

LocateAnything 是一个 **generalist（通用型）定位模型**：一个网络胜任多种定位任务。底层三件协同 [【跳转到 0:46】](https://www.youtube.com/watch?v=YyMhtCXMfXo&t=46)：

| 组件 | 角色 |
| --- | --- |
| MoonViT 视觉编码器 | 按**原生分辨率**读图——不把图压成小方块 |
| Qwen2.5 语言解码器 | 理解你用自然语言提出的请求 |
| MLP 投影器 | 小型投影层，桥接视觉与语言两个世界 |

训练数据规模惊人：**1.38 亿条语言查询、7.85 亿个边界框** [【跳转到 1:11】](https://www.youtube.com/watch?v=YyMhtCXMfXo&t=71)。更关键的是体量：只有 **30 亿参数，float16 下约 7GB 显存**，一张游戏显卡就能装下。

![模型三件套：MoonViT + Qwen2.5 + MLP 投影器](assets/LocateAnything%20on%20the%20RTX%204090%20—%20One%20Model%20for%20Detection,%20Grounding,%20OCR%20&%20GUI%20Pointing/00046.webp)

## 二、Parallel Box Decoding：为什么快

### 2.1 从逐 token 到整框原子输出

经典视觉语言模型把边界框当**句子**生成：先 x1、再 y1、再 x2、再 y2，一个 token 接一个 token 地等 [【跳转到 1:36】](https://www.youtube.com/watch?v=YyMhtCXMfXo&t=96)。LocateAnything 的核心主张是：**一个框是一个几何整体**——Parallel Box Decoding（PBD，并行框解码）把整个框、四个坐标作为一个**原子单元**，一次前向并行输出。

两个直接收益 [【跳转到 2:01】](https://www.youtube.com/watch?v=YyMhtCXMfXo&t=121)：

- **保住几何一致性**：四个角点一起预测，不再互相脱节；
- **解锁吞吐**：单张 H100 每秒 **12.7 个框**，约为 Qwen3-VL 同任务的 **10 倍**。

### 2.2 可解析的输出语法

模型的一切输出都在一套极小、可解析的语法里 [【跳转到 2:01】](https://www.youtube.com/watch?v=YyMhtCXMfXo&t=121)：

- 一次检测 = 带标签的 `ref` 标签 + 装着四个整数的 `box` 标签；一个点 = 两个整数；
- 匹配不到任何东西时输出 `box none`——一个**诚实的空答案**，而不是硬编一个框；
- 坐标是 **0~1000 的整数**、按图片归一化：除以 1000、乘以图片尺寸，框就落在原该在的位置——**输出与分辨率无关**，十行 Python 就能得到像素级精确的矩形。

![Parallel Box Decoding：整框一次输出 vs 逐 token 生成](assets/LocateAnything%20on%20the%20RTX%204090%20—%20One%20Model%20for%20Detection,%20Grounding,%20OCR%20&%20GUI%20Pointing/00096.webp)

## 三、三种生成模式：fast / slow / hybrid

模型给了你一个三档旋钮，分清何时用哪一档，决定 demo 是"丝滑"还是"抓狂" [【跳转到 2:57】](https://www.youtube.com/watch?v=YyMhtCXMfXo&t=177)：

- **fast**：纯并行框解码，整框一步输出、吞吐最大，为"每一毫秒都算数"的机器人和实时智能体而生；代价是极密集或含混场景下并行猜测偶尔出错。
- **slow**：经典逐 token 预测，一次一个坐标，最稳定，适合离线标注与基准评测——宁等勿错，但每个框都要付完整的串行延迟。
- **hybrid（默认档，最聪明）**：以 fast 模式运行，同时紧盯自己的输出——一旦看到语法畸形或空间含混的坐标（比如密集人群里两个框糊在一起），就**丢弃出问题的块、回退到最近一个已验证前缀、只用逐 token 方式重新解码该块，然后立刻切回 fast**。既拿到并行速度，又有串行可靠性。

结论：除非有特别理由，请用 hybrid。

![fast / slow / hybrid 三种生成模式的取舍](assets/LocateAnything%20on%20the%20RTX%204090%20—%20One%20Model%20for%20Detection,%20Grounding,%20OCR%20&%20GUI%20Pointing/00177.webp)

## 四、五任务实测：通用性的成绩单

同一组权重、同一套提示格式，胜任五种工作 [【跳转到 4:28】](https://www.youtube.com/watch?v=YyMhtCXMfXo&t=268)。

### 4.1 目标检测：218 个类别一次问完

把类别列表（car、person、traffic light、bus、truck）交给模型，它为每个实例返回一个带标签的框。对繁忙东京路口的实际输出：数十个行人、车辆、信号灯**一次推理全部框出**。类别列表还能扩展——在本机一次查询里验证了 **218 个类别**，模型对每一个都给出回应。

![东京路口目标检测：行人、车辆、信号灯一次全部框出](assets/LocateAnything%20on%20the%20RTX%204090%20—%20One%20Model%20for%20Detection,%20Grounding,%20OCR%20&%20GUI%20Pointing/00268.webp)

### 4.2 短语定位：single 模式的语言理解

multi 模式下要 bus，场景里每辆公交都得到一个框（本例三辆）[【跳转到 5:23】](https://www.youtube.com/watch?v=YyMhtCXMfXo&t=323)。single 模式才是炫技场：要"**离镜头最近的绿色公交**"，模型必须理解颜色、理解深度、比较候选，并恰好交还一个框——属性、空间关系、最高级，都在一次前向里解析完毕。

![短语定位 single 模式：准确框出"离镜头最近的绿色公交"](assets/LocateAnything%20on%20the%20RTX%204090%20—%20One%20Model%20for%20Detection,%20Grounding,%20OCR%20&%20GUI%20Pointing/00323.webp)

### 4.3 场景文本检测：54 个区域，label 即转录

一条固定提示 `detect all the text in box format`，模型扫全图找文字。指向论文架构图，返回 **54 个文本区域**——仔细看标签：每个框的 label 就是转录出的文字本身。所以它不只回答"文字在哪"，还回答"是什么"；文档版面、街牌、界面，同一套玩法 [【跳转到 5:55】](https://www.youtube.com/watch?v=YyMhtCXMfXo&t=355)。

![场景文本检测：54 个文本区域，框标签即转录文字](assets/LocateAnything%20on%20the%20RTX%204090%20—%20One%20Model%20for%20Detection,%20Grounding,%20OCR%20&%20GUI%20Pointing/00355.webp)

### 4.4 指点 pointing：GUI 智能体的基石

有时你不要框，只要一个能点的坐标。把 demo 截图喂给模型，让它指出橙色的 locate 按钮——一个点，正中按钮 [【跳转到 6:26】](https://www.youtube.com/watch?v=YyMhtCXMfXo&t=386)。这正是 GUI 自动化机器人与具身智能体赖以构建的能力：**看到屏幕、理解指令、产出点击目标**。该模型在 ScreenSpot-Pro 上拿到 **60.3 分**，胜过体积大它十倍的 GUI 专用模型。

![指点模式：正中橙色按钮的坐标点](assets/LocateAnything%20on%20the%20RTX%204090%20—%20One%20Model%20for%20Detection,%20Grounding,%20OCR%20&%20GUI%20Pointing/00386.webp)

### 4.5 4090 实测速度

以下是自己硬件上的数字，不是营销页 [【跳转到 6:51】](https://www.youtube.com/watch?v=YyMhtCXMfXo&t=411)：

- fast 模式一次并行推理从该场景拉出 **65 个框**；
- 1920 像素路口的完整 hybrid 检测不到 **10 秒**；
- 单条短语定位查询端到端 **2~3 秒**。

demo 还加了个彩蛋：每个检测结果都能从全分辨率原图自动裁剪、按类型分文件夹存盘——一次点击就得到一份带标注的图片数据集。

## 五、4090 安装配方：可复现环境四步

模型诞生于 H100 集群，作者的目标是让它在 Pop!_OS 的单张消费级 4090 上安家、环境干净可复现 [【跳转到 9:21】](https://www.youtube.com/watch?v=YyMhtCXMfXo&t=561)：

1. **钉住环境**：用 asdf 把 Python 3.12.8 与 uv 0.8.8 写进随仓库的 tool-versions 文件，再用 uv 建项目独立虚拟环境——不用 conda、不碰全局 site-packages、完全可弃。
2. **安装顺序有讲究**：先从 CUDA 12.8 轮子索引装 PyTorch（带完整 GPU 支持），再装仓库本体——它会带进 transformers 4.57、deepspeed 等依赖，关键是**不会降级 torch**。
3. **庆祝前先验证**：一行 Python 必须打印 `CUDA available: true`、`NVIDIA GeForce RTX 4090`。
4. **缓存目录家规**：所有模型下载强制走大硬盘上的专用缓存目录——7GB 权重绝不该误落系统盘。

首个检查点下载 7.2GB，以 bfloat16 装入刚过 7GB 的显存；传入一个关键 override（见下章）后，东京路口的第一次检测：**9.7 秒 97 个框**，nvidia-smi 证实是 GPU 在干活。从空目录到能跑的 SOTA 定位模型约 15 分钟，大头是下载时间 [【跳转到 9:21】](https://www.youtube.com/watch?v=YyMhtCXMfXo&t=561)。

![首次检测：9.7 秒 97 个框，nvidia-smi 证实 GPU 满载](assets/LocateAnything%20on%20the%20RTX%204090%20—%20One%20Model%20for%20Detection,%20Grounding,%20OCR%20&%20GUI%20Pointing/00561.webp)

## 六、三个战例：踩坑与一行修复

通往顺滑 demo 的路上有 10 个问题，视频讲了最有代表性的三个 [【跳转到 10:41】](https://www.youtube.com/watch?v=YyMhtCXMfXo&t=641)。

### 6.1 战例一：Hopper-only 的默认注意力后端

读模型的配置代码（config.json）会发现：`_attn_implementation` 默默默认为 **Magi**——一种极快、但只存在于数据中心 Hopper 和 Blackwell GPU 的注意力内核。4090 是 Ada 一代，用不上 Magi，而加载代码甚至不暴露这个设置。修法：加载模型时把 attention implementation 参数传为 **SDPA**，回退到 PyTorch 内置的缩放点积注意力——一个关键字参数，但你得知道它在那儿。

### 6.2 战例二：大图显存爆炸的完整链条

用户上传大图，GPU 在 24GB 卡上要 **40.6GB**——一个 30 亿参数的模型哪来的胆子？链条如下 [【跳转到 11:06】](https://www.youtube.com/watch?v=YyMhtCXMfXo&t=666)：

1. 视觉编码器按原生分辨率工作，大图最多产生 **25600 个 token**；
2. SDPA 回退要构造稠密注意力掩码，把 PyTorch 打到 math 后端；
3. 完整注意力矩阵以 float32 物化：16 头 × 25600² × 4 字节 ≈ **41GB**——报错数字与算术分毫不差。

修法：把处理器的 token 上限压到 **6400**，超大图先降采样再进编码器。一张 6000 像素的图现在 **2.2 秒**跑完；而且因为输出坐标是归一化的，**框仍精确落在原图上**。

![大图显存爆炸：24GB 卡上要求 40.6GB 的报错现场](assets/LocateAnything%20on%20the%20RTX%204090%20—%20One%20Model%20for%20Detection,%20Grounding,%20OCR%20&%20GUI%20Pointing/00641.webp)

### 6.3 战例三：demo 的依赖打地鼠

仓库不附带本地 UI，作者用 Gradio 搭了一个，然后一头扎进依赖地狱：锁定的 Gradio 是 2023 年版、与现代 Jinja2 一起崩；升级 Gradio 又拖进一个过新的 Hugging Face Hub、弄坏 transformers；把 Hub 钉回去两个问题都解决。模型偶尔输出**角点颠倒的框**，绘图库干脆拒绝渲染——一个 `sorted` 调用修好。每个修复都是一行，**找到那一行才是真功夫**——作者把全部 10 个问题连同精确修法写进了 notes 文件夹。

## 七、demo 成品与资源

最终成果是一个在 4090 上完整运行的本地 demo [【跳转到 12:48】](https://www.youtube.com/watch?v=YyMhtCXMfXo&t=768)：下拉框里五种任务类型、三种生成模式一键切换、面向密集场景的 token 预算滑块、每个能力的一键示例——包括指向它自己的界面。裁剪功能把每个检测从全分辨率原图切出、按类型归档并提供 ZIP 下载。整套东西空闲时只占约 **7GB 显存**。

![最终 demo：五任务、三模式、token 预算滑块与一键示例](assets/LocateAnything%20on%20the%20RTX%204090%20—%20One%20Model%20for%20Detection,%20Grounding,%20OCR%20&%20GUI%20Pointing/00768.webp)

需要的一切都在 NVIDIA 官方仓库 `github.com/NVlabs/Eagle`（Embodied 目录），模型在 Hugging Face 开放：`NVIDIA/LocateAnything-3B`。

## 小结

- LocateAnything = MoonViT（原生分辨率）+ Qwen2.5（语言解码）+ MLP 投影，3B 参数、bfloat16 约 7GB 显存，训练数据 1.38 亿查询 / 7.85 亿框。
- 快的根源是 Parallel Box Decoding：整框原子输出保几何一致性，单张 H100 每秒 12.7 框，约为 Qwen3-VL 的 10 倍；输出是 ref/box 标签语法 + 0~1000 归一化坐标，与分辨率无关。
- 三种生成模式：fast（并行最快）、slow（串行最稳）、hybrid（默认；并行出错时回退已验证前缀、逐 token 重解码该块再切回）。
- 消费级部署三道坎：注意力后端默认 Magi 只支持 Hopper/Blackwell（要手动传 SDPA）；大图触发 math 后端物化 41GB 注意力矩阵（token 上限压到 6400）；Gradio/Jinja2/Hub 依赖冲突与角点颠倒框（sorted 一行修复）。
- 4090 实测：fast 一次并行 65 框、hybrid 全图检测 <10 秒、单查询 2~3 秒、ScreenSpot-Pro 60.3 分。
- 装好后一次点击即可裁剪导出带标注数据集——桌面 GPU 也能干过去要数据中心的活。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| LocateAnything / Eagle 家族 | NVIDIA 的通用视觉定位基础模型，Eagle VLM 系列成员 |
| Parallel Box Decoding（PBD） | 把整个边界框当原子单元、一次前向并行输出的解码方式 |
| fast / slow / hybrid | 并行最快 / 串行最稳 / 默认档：并行出错自动回退重解码 |
| ref / box 标签 | 输出语法：ref 带语义标签，box 装四个整数坐标 |
| box none | 无匹配时的诚实空输出，避免硬编框 |
| 归一化坐标 | 0~1000 整数按图缩放，输出与分辨率无关 |
| Magi 注意力 | 仅 Hopper/Blackwell 数据中心 GPU 的高速注意力内核，Ada 显卡需手动换 SDPA |
| SDPA | PyTorch 内置缩放点积注意力，是 Ada 等消费卡的回退方案 |
| math 后端 | SDPA 遇稠密掩码时的兜底实现，会物化完整注意力矩阵导致显存爆炸 |
| ScreenSpot-Pro | 高分辨率屏幕 GUI 定位基准；LocateAnything 得 60.3 分 |
| asdf / uv | 版本管理器与 Python 包管理器，用于钉住可复现环境 |
