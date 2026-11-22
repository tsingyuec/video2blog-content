# 把旋转写成前后半的逐元素乘加：cos、sin 缓存表让 RoPE 只剩四次 mul

> 视频来源：[手撕vLLM系列9-RoPE-50行代码极简实现](https://www.bilibili.com/video/BV1eFe16zEBi/?t=0)（Bilibili · deep_thoughts）
> 本文基于视频演说图文稿整理，配图截自视频。
> 导读：这支约 20 分钟的视频从空文件开始，一行行敲出一个 `RotaryEmbedding` 类——先算频率、再把 cos/sin 存进一张 $[\text{max\_pos},\ \text{rotary\_dim}]$ 的缓存表、前向只做一次按位置取行加四次 `torch.mul`，最后与 HuggingFace 的实现对拍数值和速度。全片没有幻灯片，画面一直是 `v0/models/layer/rotary.py` 这个文件，所以本文按"敲代码的顺序"组织：每一节对应屏幕上新增的那几行。同一算子的另一种写法（预计算复数表 + 广播复数乘）见本小节另一篇博客。

## 本讲要解决的核心问题（SCQA）

**背景**：RoPE 前向要做的事，用一句话就能说完——把每个位置、每个 head 向量按"前后两半"配对，做若干次二维旋转。理论上只需要一组 $\cos(m\theta_i)$ 与 $\sin(m\theta_i)$ 就够了。

**冲突**：真要写代码，麻烦立刻冒出来。$\cos$、$\sin$ 每层都要用、每个 token 都要用，如果每次前向都重算，三角函数会把算子成本吃掉一大截；而如果把表存起来，就要面对三个形状问题：表的两个维度放什么、取出来的行怎么和 $[B,\ S,\ H,\ \text{head\_size}]$ 对齐、旋转到底覆盖 head 的多少维。任何一处错位，数值不会报错，只会静默地算错。

**疑问**：一个推理框架里的位置编码算子，怎样才能既只算一次三角函数，又只做几次内存友好的逐元素运算？

**回答（中心思想）**：**把"角度表"一次性算成 $[\text{max\_pos},\ \text{rotary\_dim}]$ 的缓存张量——前一半存 $\cos$、后一半存 $\sin$；前向按位置 `index_select` 取行、补出一个 head 维走广播，再把 head 向量按前一半 `[:half]` 与后一半 $[\tfrac{d}{2},\ d)$ 切成两段，用四次 `torch.mul` 加一次 `sub_`、一次 `add_` 写出旋转公式。** 复数被彻底绕开，旋转就是一个"乘加"式的 element-wise 算子。

---

## 一、先定接口：四个参数与两条校验

类的骨架是 `class RotaryEmbedding(nn.Module)`，`__init__` 收四个有效参数 [【跳转到 00:20】](https://www.bilibili.com/video/BV1eFe16zEBi/?t=20)：

| 参数 | 类型 | 含义 |
| --- | --- | --- |
| `head_size` | int | 单个注意力头的维度，也就是这个向量总共多长 |
| `rotary_dim` | int | 其中有多少维参与旋转 |
| `max_position_embedding` | int | 预留的最大位置数，表的行数 |
| `base` | float | 频率底数，决定频率阶梯的起点；对拍脚本里取的是 `1e6` |

`head_size` 和 `rotary_dim` 为什么要分开，视频花了将近半分钟解释 [【跳转到 00:40】](https://www.bilibili.com/video/BV1eFe16zEBi/?t=40)：**绝大部分模型里两者相等**，但有些论文会把 `rotary_dim` 设得比 `head_size` 小，只让 head 的前一部分维度参与旋转，剩下的维度原样留着不转——这是训练时的一种取舍。既然真实模型里有这种配置，代码就得留出余地，所以两个参数都收。

接着是两条校验 [【跳转到 01:40】](https://www.bilibili.com/video/BV1eFe16zEBi/?t=100)：

```python
if rotary_dim % 2 != 0:
    raise ValueError("Rotary dim must be even!")
if rotary_dim > head_size:
    raise ValueError("Rotary dim must be smaller than head size!")
```

- **必须是偶数**：旋转要成对做，第 $i$ 维必须有个搭档和它组成一个平面，落单的维度没法转。
- **不能超过 `head_size`**：参与旋转的维度是 head 的一个子集，子集不可能比全集大 [【跳转到 02:00】](https://www.bilibili.com/video/BV1eFe16zEBi/?t=120)。

然后把这些参数存成成员变量，并顺手存一个 `self.half`（取 `rotary_dim` 的一半） [【跳转到 02:20】](https://www.bilibili.com/video/BV1eFe16zEBi/?t=140)。这个 `half` 后面出现得非常频繁：它是"对数"，也是"切一半"的边界，先算好省得每次再除。

---

## 二、`inv_freq`：三行把频率阶梯算出来

![init 前二十行：两条校验、half，以及 inv_freq 与 cache 两行；右侧是 $\theta_i = \text{base}^{-2i/d}$ 的公式卡片](assets/把旋转写成前后半的逐元素乘加：cos、sin%20缓存表让%20RoPE%20只剩四次%20mul/00245.webp)

屏幕上右侧贴着一张小卡片，写着这次要落地的公式：

$$
\theta_i = \text{base}^{-\frac{2i}{d}}
$$

其中 $d$ 是 `rotary_dim`，$i$ 是维度对的序号 [【跳转到 03:00】](https://www.bilibili.com/video/BV1eFe16zEBi/?t=180)。代码是

```python
inv_freq = base ** (-torch.arange(0, rotary_dim, 2, dtype=torch.float32) / rotary_dim)
```

拆开读 [【跳转到 03:05】](https://www.bilibili.com/video/BV1eFe16zEBi/?t=185)：

- `torch.arange` 从 0 到 `rotary_dim`、步长 2，生成 $0, 2, 4, \dots, \text{rotary\_dim}-2$，一共 $\frac{d}{2}$ 个**偶数下标**——每个下标代表"一对维度"的编号；
- 除以 `rotary_dim` 把下标归一化到 $[0, 1)$；
- 前面加负号，变成 $\text{base}$ 的负指数，也就是取倒数。

三个动作连起来，结果正好是 $\frac{d}{2}$ 个**从大到小**的数：第 0 对维度频率最高（分母最小），越往后频率越低。这就是 2.3.3 那篇讲的频率阶梯在代码里的样子——它决定了"哪些维度对小位移敏感、哪些维度负责长距离"。

顺带一个细节：`dtype=torch.float32` 是显式指定的。$2i/d$ 是小数，如果 `arange` 默认生成整数张量，除法会退化成整除，频率全变成 1 或 0。

---

## 三、一张 $[\text{max\_pos},\ \text{rotary\_dim}]$ 的表：前一半 cos，后一半 sin

有了频率，接下来先把空间开出来：

```python
cache = torch.empty(max_position_embedding, rotary_dim, dtype=torch.float32)
```

这是一块形状为 $[\text{max\_pos},\ \text{rotary\_dim}]$、初值任意的 float32 张量 [【跳转到 03:25】](https://www.bilibili.com/video/BV1eFe16zEBi/?t=205)。为什么用 `empty` 而不是 `zeros`：里面的每个位置马上就会被写满，清零是白费的内存带宽。

**这张表的布局是这套实现的核心设计**：每一行对应一个位置，行内前 $\frac{d}{2}$ 列放 $\cos$，后 $\frac{d}{2}$ 列放 $\sin$。这样一次取行就同时拿到了旋转需要的两个系数，不用维护两张表、也不用两次索引 [【跳转到 06:05】](https://www.bilibili.com/video/BV1eFe16zEBi/?t=365)。

视频里反复强调这一步的动机：$\sin$ 和 $\cos$ 提前算好放进 cache，那么后面若干层就不必每层重算一遍，只需要算一次，这是**纯性能优化** [【跳转到 03:45】](https://www.bilibili.com/video/BV1eFe16zEBi/?t=225)。

### 3.1 用一个视图拿到前半段，让 `outer` 直接写进去

```python
angle = cache[:, :self.half]
torch.outer(torch.arange(max_position_embedding, dtype=torch.float32), inv_freq, out=angle)
```

![用视图 angle 指向 cache 的前半段，outer 的 out 参数直接写进这块内存](assets/把旋转写成前后半的逐元素乘加：cos、sin%20缓存表让%20RoPE%20只剩四次%20mul/00385.webp)

`cache[:, :self.half]` 拿到的是前半段的**视图（view）**：它不新建内存，只是给同一块存储换了个"窗口"[【跳转到 04:25】](https://www.bilibili.com/video/BV1eFe16zEBi/?t=265)。视频在这里专门停下来解释 view 的含义——没有真正创建新空间，所以省掉了拷贝开销；后面他还补了一句，如果不这么写而是直接切片复制，就会产生多余的中间拷贝 [【跳转到 08:05】](https://www.bilibili.com/video/BV1eFe16zEBi/?t=485)。

接着是外积：

$$
\text{angle}[m, i] = m \cdot \text{inv\_freq}[i]
$$

也就是"位置 × 频率"的角度矩阵，形状 $[\text{max\_pos},\ \frac{d}{2}]$。关键在于 `out=angle` 这个参数：PyTorch 直接把结果写进刚才那个视图，**连返回值都不需要接** [【跳转到 04:45】](https://www.bilibili.com/video/BV1eFe16zEBi/?t=285)。一条语句省掉了"分配 + 拷贝"两步。

形状刚好对得上不是巧合：`arange` 的长度是 $\text{max\_pos}$，`inv_freq` 长度是 $\frac{d}{2}$，外积正好是 $[\text{max\_pos},\ \frac{d}{2}]$，而 `cache` 前半段也是这个形状 [【跳转到 05:05】](https://www.bilibili.com/video/BV1eFe16zEBi/?t=305)。

### 3.2 把角度复制到后半段，再原地求 cos 与 sin

```python
cache[:, self.half:].copy_(angle)
torch.cos_(angle)
torch.sin_(cache[:, self.half:])
```

现在 `cache` 的前半段是角度。`copy_` 把这个角度矩阵复制到后半段，于是**两半都装着角度** [【跳转到 05:45】](https://www.bilibili.com/video/BV1eFe16zEBi/?t=345)。为什么要先复制：因为接下来要分别在两半上做不同的原地运算，而原地运算会覆盖掉原来的角度值——不复制的话，算完 $\cos$ 就没有角度可以算 $\sin$ 了。

然后两条带下划线的函数：

- `torch.cos_` 把前半段 `angle` **原地**换成 $\cos(m\theta_i)$；
- `torch.sin_` 把后半段 $[\tfrac{d}{2},\ d)$ **原地**换成 $\sin(m\theta_i)$ [【跳转到 06:25】](https://www.bilibili.com/video/BV1eFe16zEBi/?t=385)。

下划线在 PyTorch 里是"原地版"的约定：`torch.cos` 会新建一个张量返回，`torch.cos_` 直接改这块内存。这里全程不产生新张量，也就不用再往 `cache` 里拷一次。

### 3.3 `register_buffer`：让表跟着模型走，但别混进权重

```python
self.register_buffer("cos_sin_cache", cache, persistent=False)
```

![cos_、sin_ 原地算完之后，把 cache 注册成 buffer，persistent 设为 False](assets/把旋转写成前后半的逐元素乘加：cos、sin%20缓存表让%20RoPE%20只剩四次%20mul/00425.webp)

`register_buffer` 注册的张量会跟随模型一起 `.to(device)`，但不是可训练参数，不会出现在优化器的参数组里；它到底该不该进权重文件，由 `persistent` 这个开关决定 [【跳转到 06:45】](https://www.bilibili.com/video/BV1eFe16zEBi/?t=405)。

`persistent=False` 的意思更容易被误解，视频讲得很直白：**它不希望这张表和权重混在一起**——推理时需要的 buffer 值得随模型搬到 GPU，但不该被当成权重存进权重文件里，所以写 `False` [【跳转到 07:05】](https://www.bilibili.com/video/BV1eFe16zEBi/?t=425)。

到这一步 `__init__` 结束。视频末尾自己做了一次小结：先是 `super()`，然后两条判断，然后存初始变量，核心是算 $\theta$ 并把 $\sin$、$\cos$ 一次算出来，中间那些 `view` / `out=` / 下划线操作都是为了**节省中间张量的开销** [【跳转到 07:45】](https://www.bilibili.com/video/BV1eFe16zEBi/?t=465)。

---

## 四、forward：先把位置和表对齐

`forward` 的签名是 `(self, positions, query, key)`，返回两个张量 [【跳转到 08:25】](https://www.bilibili.com/video/BV1eFe16zEBi/?t=505)。**`positions` 是 int 类型的张量，`query` 和 `key` 是浮点张量**——这个类型差别决定了后面各自的操作。函数只对 `key` 做位置注入，`value` 不在此列：位置信息只要进入 $q\cdot k^{\top}$，value 保持原样。

### 4.1 把位置形状拉平

```python
flat = positions.reshape(-1)  # [B, S, D] [B*S, D]
```

为什么可以无脑拉平：不管上游传进来的是 $[B, S]$（二维）还是 $[B\cdot S]$（已经拍平），**我们只关心"每个 token 一个位置"这条信息**，前面那些维度怎么排列无所谓 [【跳转到 09:05】](https://www.bilibili.com/video/BV1eFe16zEBi/?t=545)。拉成一条一维的整数序列，恰好就是"要用 cache 的哪几行"。

### 4.2 `index_select` 取行，并统一 dtype

![forward 开头：位置拉平、按位置取行、把 cos 与 sin 从表的两半里切出来](assets/把旋转写成前后半的逐元素乘加：cos、sin%20缓存表让%20RoPE%20只剩四次%20mul/00625.webp)

```python
cos_sin = self.cos_sin_cache.index_select(0, flat).to(query.dtype)

cos = cos_sin[:, :self.half].unsqueeze(-2)
sin = cos_sin[:, self.half:].unsqueeze(-2)
```

`index_select` 的意思是"在第 0 维上，按 `flat` 里给的编号挑行" [【跳转到 09:45】](https://www.bilibili.com/video/BV1eFe16zEBi/?t=585)。取出来的形状是 $[B\cdot S,\ \text{rotary\_dim}]$：**每个 token 一行，行内前一半是 $\cos$、后一半是 $\sin$**。

`.to(query.dtype)` 紧跟其后：cache 是按 float32 建的，而 query 可能是半精度或者 bfloat16，两者相乘前必须对齐类型。这也解释了为什么表本身存 float32——**用高精度存、按需降精度用**，取行时的那一次转换成本远低于全程用低精度算三角函数。

### 4.3 `unsqueeze(-2)`：补出一个 head 维

现在 `cos` 是 $[B\cdot S,\ \frac{d}{2}]$，而 query 是 $[B\cdot S,\ H,\ \text{head\_size}]$。差的那一维是 head [【跳转到 10:05】](https://www.bilibili.com/video/BV1eFe16zEBi/?t=605)。

`unsqueeze(-2)` 在倒数第二维的位置插入一个长度 1 的维度，形状变成 $[B\cdot S,\ 1,\ \frac{d}{2}]$ [【跳转到 10:44】](https://www.bilibili.com/video/BV1eFe16zEBi/?t=644)。这个 1 不是凑数：**所有 head 共用同一组角度**，所以用长度为 1 的维度走广播，让同一个 $\cos$ 表铺到每个 head 上，而不是真的复制 $H$ 份 [【跳转到 10:51】](https://www.bilibili.com/video/BV1eFe16zEBi/?t=651)。

到这里三个张量的形状已经可以对位了：

| 张量 | 形状 | 说明 |
| --- | --- | --- |
| `x` | $[B\cdot S,\ H,\ \text{head\_size}]$ | 待旋转的 q 或 k |
| `cos` | $[B\cdot S,\ 1,\ \frac{d}{2}]$ | 广播到每个 head |
| `sin` | $[B\cdot S,\ 1,\ \frac{d}{2}]$ | 同上 |

---

## 五、`_apply`：前后半拆分，四次 `mul` 写完旋转

因为 query 和 key 的处理完全一样，视频在 `forward` 里嵌套定义了一个内部函数 `_apply`，最后对 query 和 key 各调一次 [【跳转到 11:31】](https://www.bilibili.com/video/BV1eFe16zEBi/?t=691)。这也是全片最核心的一段。

### 5.1 先存形状，再做视图切分

![_apply 全貌：保存原形状、reshape、四次 mul 加 sub_，右侧是旋转公式卡片](assets/把旋转写成前后半的逐元素乘加：cos、sin%20缓存表让%20RoPE%20只剩四次%20mul/00900.webp)

```python
shape = x.shape
x = x.reshape(flat.numel(), -1, self.head_size)
out = torch.empty_like(x)

x1, x2 = x[..., :self.half], x[..., self.half:self.rotary_dim]
o1, o2 = out[..., :self.half], out[..., self.half:self.rotary_dim]
```

- `shape = x.shape` 先记下原始形状，最后要原样 reshape 回去 [【跳转到 12:40】](https://www.bilibili.com/video/BV1eFe16zEBi/?t=760)；
- `x.reshape` 的三个维度：第一维写成 token 数，中间的 head 数交给 `-1` 自动推断，最后一维钉死 `head_size`；
- `torch.empty_like` 开一块同形状的输出，后面所有结果都往里写；
- `x1` / `x2` 是把 head 维度**按前后两半切开**的视图：`x1` 取 $[0, \frac{d}{2})$，`x2` 取 $[\frac{d}{2}, \text{rotary\_dim})$；`o1` / `o2` 是对应的输出窗口 [【跳转到 13:20】](https://www.bilibili.com/video/BV1eFe16zEBi/?t=800)。

这里就是这套实现与"复数写法"最大的差异：**它不做相邻两维配对，而是把 head 向量拦腰截成前后两段，让第 $i$ 维与第 $i+\frac{d}{2}$ 维组成一个平面**。数学上两者是同一个旋转，只是维度的排布约定不同；换个实现（比如官方 Llama）就要把相邻两维配对。

### 5.2 一次 `temp` + 四次 `mul`

旋转公式在屏幕上一直贴着：

$$
q' = R(\theta)\cdot\begin{pmatrix} x \\ y \end{pmatrix}
= \begin{pmatrix} x\cos\theta - y\sin\theta \\ x\sin\theta + y\cos\theta \end{pmatrix}
$$

代码把它摊成四行乘法：

```python
tmp = torch.empty_like(o1)
torch.mul(x1, cos, out=o1)
torch.mul(x2, sin, out=tmp)
o1.sub_(tmp)

torch.mul(x2, cos, out=o2)
torch.mul(x1, sin, out=tmp)
o2.add_(tmp)
```

逐条对公式 [【跳转到 14:00】](https://www.bilibili.com/video/BV1eFe16zEBi/?t=840)：

1. `torch.mul(x1, cos, out=o1)` 算的是 $x\cos\theta$，直接写进输出的前半段；
2. `torch.mul(x2, sin, out=tmp)` 算的是 $y\sin\theta$，写进临时区。**`tmp` 是这段代码里唯一躲不掉的一次额外分配** [【跳转到 14:20】](https://www.bilibili.com/video/BV1eFe16zEBi/?t=860)——因为 `o1` 里还留着第 1 步的结果，两个乘积没法同时存在输出窗口里；
3. 在 `o1` 上做 `sub_` 减法，前半段的最终值 $x\cos\theta - y\sin\theta$ 落位；
4. 后两行按同样的套路算后半段：`x2` 乘 `cos` 写进 `o2`，`x1` 乘 `sin` 写进 `tmp`，最后 `add_` 回 `o2`，得到 $x\sin\theta + y\cos\theta$。

视频里把四条乘法总结成一句话：**"这四条是 x 和 cos、y 和 sin、x 和 sin、y 和 cos"，前后两组各配一次减法和一次加法，与公式保持一致** [【跳转到 15:00】](https://www.bilibili.com/video/BV1eFe16zEBi/?t=900)。全程都是 `mul` + `sub_` / `add_` 这类原地运算，没有矩阵乘、没有转置、也没有额外的中间大张量。

### 5.3 为什么切片必须写到 `rotary_dim`

第二段的切片是从 `self.half` 切到 `self.rotary_dim`，而不是一直切到结尾。视频专门解释了这条 [【跳转到 15:20】](https://www.bilibili.com/video/BV1eFe16zEBi/?t=920)：**因为 `rotary_dim` 可能小于 `head_size`，`rotary_dim` 之后还有维度**，那些维度不属于旋转范围，切片必须精确停在边界上——这正是第一章里两个参数分开的那笔伏笔 [【跳转到 15:40】](https://www.bilibili.com/video/BV1eFe16zEBi/?t=940)。

最后 `return out.reshape(shape)` 把形状还原成进来时的样子 [【跳转到 16:00】](https://www.bilibili.com/video/BV1eFe16zEBi/?t=960)。**RoPE 是形状不变算子**，这一点与上一节说的“进出形状一致”是同一件事。

---

## 六、和 HuggingFace 对拍：0.03125 的差从哪来

代码写完，视频用一段脚本和 transformers 里现成的实现做对比 [【跳转到 16:20】](https://www.bilibili.com/video/BV1eFe16zEBi/?t=980)：固定随机种子，给出 `head_dim`、最大位置数 $M$、位置数量 $N$、`base = 1e6`（视频的说法是“1 后面跟 6 个 0”）。

第一轮结果并不乐观：**逐元素 `equal` 判等是 `False`，最大差值 0.03125**，但速度上自己写的更快——**16 毫秒对 23 毫秒** [【跳转到 17:46】](https://www.bilibili.com/video/BV1eFe16zEBi/?t=1066)、[【跳转到 17:53】](https://www.bilibili.com/video/BV1eFe16zEBi/?t=1073)。

![对拍脚本的控制台输出：改成 1.0 除以幂之后数值基本一致，性能 1.40 倍](assets/把旋转写成前后半的逐元素乘加：cos、sin%20缓存表让%20RoPE%20只剩四次%20mul/01111.webp)

### 6.1 差异出在"取负号"与"取倒数"

排查之后定位到 `inv_freq` 那一行 [【跳转到 18:11】](https://www.bilibili.com/video/BV1eFe16zEBi/?t=1091)。自己的写法是用负指数：

```python
inv_freq = base ** (-torch.arange(0, rotary_dim, 2, dtype=torch.float32) / rotary_dim)
```

HuggingFace 的写法是**先算正指数，再取倒数**：

```python
inv_freq = 1.0 / (base ** (torch.arange(0, rotary_dim, 2, dtype=torch.float32) / rotary_dim))
```

两式在实数域上完全相等，但在浮点域不是同一条计算路径：一个走 `pow` 的负指数分支，一个走 `pow` 之后接一次 `div`。屏幕上给出的排查结论大意是——这是两条独立的数值路径，在若干个频率值上产生了 $10^{-7}$ 量级的相对误差，而这个误差乘上位置 $m$ 之后再进 $\cos$/$\sin$，就被放大成了 0.03 量级的绝对差 [【跳转到 18:31】](https://www.bilibili.com/video/BV1eFe16zEBi/?t=1111)。

改成 HuggingFace 的写法后，数值"基本上没问题了"，控制台显示性能为 **16.97 ms 对 23.70 ms，约 1.40 倍** [【跳转到 18:51】](https://www.bilibili.com/video/BV1eFe16zEBi/?t=1131)。视频自己的判断是：这个差别在实践中"没什么区别"，误差在 0.0 几的量级，属于可以接受的范围；但**如果你要和某个具体实现做逐位对齐，就得连写法一起对齐**——这也是这段对拍最有价值的地方。

### 6.2 为什么值得手撕一遍

视频在演示过程中自己也踩了坑，而且不藏着：有一次 `torch.mul` 的那一行漏写了、还有一次把 `sin` 打成了 `sim` [【跳转到 17:20】](https://www.bilibili.com/video/BV1eFe16zEBi/?t=1040)。他的结论是：**这类算子看起来只有几十行，但形状、切片、类型、变量名每一处都能出错，所以学习阶段最好自己手敲一遍，而不是复制**。这也解释了为什么这段代码里 `out=`、`_` 后缀、`view` 用得这么密——它们都是为"少一次分配、少一次拷贝"服务的，而这些恰恰是看别人代码时最容易滑过去的部分。

---

## 七、两种写法的取舍：复数乘 vs 逐元素乘加

这个算子至少有两种流行写法，本小节两篇博客各拆了一种。摆在一起看，差别很清楚：

| 维度 | 复数表 + 广播复数乘（官方 Llama） | cos/sin 缓存表 + 前后半乘加（本篇） |
| --- | --- | --- |
| 表的内容 | 每个位置 $\frac{d}{2}$ 个复数 $e^{im\theta}$ | 每个位置前 $\frac{d}{2}$ 个 $\cos$、后 $\frac{d}{2}$ 个 $\sin$ |
| 维度配对方式 | 相邻两维 $(2i,\ 2i+1)$ 配一对 | 前后两半 $(i,\ i+\frac{d}{2})$ 配一对 |
| 前向运算 | 一次复数逐元素乘 | 四次 `mul` 加一次 `sub_`、一次 `add_` |
| 中间张量 | `view_as_complex` / `view_as_real` 两次换解释，无显式 temp | 一次 `empty_like` 的 `tmp` 躲不掉 |
| 后端友好度 | 复数 kernel 在自定义 CUDA/Triton 里支持有限 | 全是实数 element-wise，容易下沉到自定义 kernel |
| 只转部分维度 | 表按 head_dim 生成，不单独区分哪部分要转 | `rotary_dim` 可小于 `head_size`，尾部不转 |

两套代码的数学是同一个：都是把向量按对分组、加上 $m\theta_i$ 的角度偏移，模长不变。区别只在**把旋转安放在哪种运算上**——一个安在复数乘法里，一个摊平成乘加。推理框架多选后者，是因为它更容易融合进一个 kernel：读一次输入、算几次乘加、写一次输出，不需要在实数与复数之间来回换解释。

---

## 小结

- **两个维度参数各管一件事**：`head_size` 是 head 的总维度，`rotary_dim` 是参与旋转的维度，允许更小；必须是偶数，且不超过 `head_size`。
- **频率阶梯就一行**：$\theta_i = \text{base}^{-2i/d}$，用 `arange` 取偶数下标再除以 `rotary_dim` 配负指数实现，指数是阶梯状递减的。
- **缓存表按"行是位置、列分两半"布局**：前一半放 $\cos$、后一半放 $\sin$，一次 `index_select` 同时取到两个系数。
- **`out=` 与下划线把拷贝压到最低**：`torch.outer(..., out=angle)` 写进视图，`torch.cos_` / `torch.sin_` 原地求值，`copy_` 复制角度到后半段。
- **`register_buffer` 的 `persistent=False`**：表跟着模型搬到 GPU，但不写进权重文件。
- **前向三步对齐**：位置 `reshape(-1)`、`index_select` 取行、`unsqueeze(-2)` 补 head 维走广播。
- **旋转摊成四次 `mul`**：$x\cos\theta - y\sin\theta$ 与 $x\sin\theta + y\cos\theta$，中间需要一个 `tmp`；切片必须精确到 `rotary_dim`。
- **与 HF 的 0.03125 差来自写法不同**：`base ** (-x)` 与 `1.0 / base ** x` 是两条浮点路径，要对齐就照抄写法；速度上这一版约快 1.4 倍。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| rotary_dim | 参与旋转的维度数，必须是偶数，可以小于 head_size |
| head_size | 单个注意力头的完整维度，是旋转维度的上界 |
| half | `rotary_dim` 的一半，既是对数也是前后半的分界 |
| inv_freq | 每前进一个位置转过的弧度，随维度对序号递减 |
| cos_sin_cache | 注册为 buffer 的表，行是位置，前一半 cos、后一半 sin |
| register_buffer | 让张量随模型搬设备、进 state_dict，但不是可训练参数 |
| persistent=False | 该 buffer 不写进权重文件，推理时重建即可 |
| index_select | 按给定下标在某一维上挑行，这里用来按位置取表 |
| unsqueeze(-2) | 在倒数第二维插入长度 1 的维度，为广播补出 head 维 |
| 视图 view | 与源张量共享内存的新形状，不产生拷贝 |
| 原地运算 | 带下划线后缀的版本，如 `torch.mul(..., out=)`、`sub_`、`add_` |
| 前后半拆分 | 把 head 维度按前一半与后一半切开，再配对旋转 |
