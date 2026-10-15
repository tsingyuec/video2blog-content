# 荧光热位移实验（DSF）：把蛋白质的热稳定性变成一个数字 Tm

> 视频来源：[Fluorescence thermal shift (FTS) aka Differential Scanning Fluorimetry (DFS) aka Thermal Melt basics](https://www.youtube.com/watch?v=n4g1ENKkAVw)
> 对应知识体系条目：3.4.1 pI（等电点）、Tm（熔解温度 °C）——ABDP

## 本讲要解决的核心问题（SCQA）

**背景**：在 ABDP 这类抗体可开发性平台上，Tm（熔解温度，单位 °C）和 pI 一样是回归模型要预测的蛋白质属性（见知识体系 5.4.2「ABDP Tm Prediction」）。Tm 越高，通常意味着抗体越"皮实"——越耐热、越好储存运输。

**冲突**："这个蛋白稳不稳"只是一句定性描述——热稳定性看不见摸不着，怎么把它变成一个能比较、能优化、能写进报告的数字？

**疑问**：Tm 是怎么测出来的？荧光曲线为什么先升后降？哪些因素会让 Tm 变高或变低？

**回答（中心思想）**：用荧光热位移实验（DSF，又名 thermal shift / thermal melt）：给蛋白加热，用 SYPRO Orange 染料把"蛋白解开了多少"翻译成荧光信号；荧光爬到最大值一半处的温度就是 Tm——Tm 越高，蛋白结合得越牢固。

## 一、热是什么：蛋白为什么会"散架"

- 所谓"热"，本质是分子抖动（wiggle）的能量。蛋白被"绑"得越结实，氨基酸们能承受的抖动越多，蛋白越不容易散架。[【跳转到 00:00】](https://www.youtube.com/watch?v=n4g1ENKkAVw&t=0)
- 把蛋白聚在一起的作用力很多是**疏水相互作用**：水排斥蛋白的疏水部分，把肽链"挤"成折叠好的球；一旦蛋白解折叠（unfold），这些疏水部分就暴露在水里了。[【跳转到 00:30】](https://www.youtube.com/watch?v=n4g1ENKkAVw&t=30)

![水排斥疏水部分，把蛋白"挤"成折叠态；解折叠则暴露疏水区](assets/Fluorescence thermal shift (FTS) aka DSF aka Thermal Melt basics/00030.webp)

## 二、SYPRO Orange：疏水区的荧光探针

- 染料 **SYPRO Orange** 恰好"喜欢"疏水部分：蛋白解折叠、疏水区暴露时，染料结合上去并发荧光（fluoresce）。[【跳转到 00:50】](https://www.youtube.com/watch?v=n4g1ENKkAVw&t=50)
- 游离在水里的染料不发光——水会把它的荧光"偷走"（**淬灭**，quench）。
- 所以：**荧光亮 = 有疏水区暴露、且被染料占住了**。

![SYPRO Orange 结合暴露的疏水区并发出荧光](assets/Fluorescence thermal shift (FTS) aka DSF aka Thermal Melt basics/00050.webp)

## 三、加热看曲线：荧光先升后降

把蛋白和染料混在一起、放进 qPCR 仪做温度梯度，慢慢加热，会看到四个阶段：

1. **低温段**：蛋白结实，只是抖动、不散架——染料没地方结合，荧光很低；
2. **解折叠段**：温度升高，蛋白开始 unfold，疏水区暴露，染料大量结合，荧光快速上升；
3. **峰值**：荧光到达最高点——注意这不一定严格是"解折叠最多"的时刻，而是荧光最高的时刻；
4. **下降段**：解折叠的蛋白太多、染料不够分，蛋白之间互相粘住——发生**聚集（aggregation）**。染料被挤出来回到水里，重新被淬灭，荧光随之下滑。[【跳转到 01:15】](https://www.youtube.com/watch?v=n4g1ENKkAVw&t=75)

![用 qPCR 仪做温度梯度：边升温边读荧光](assets/Fluorescence thermal shift (FTS) aka DSF aka Thermal Melt basics/00115.webp)

![加热过程中：折叠→抖动→解折叠→染料结合](assets/Fluorescence thermal shift (FTS) aka DSF aka Thermal Melt basics/00075.webp)

![蛋白聚集后染料被挤出、信号被水淬灭，荧光下降](assets/Fluorescence thermal shift (FTS) aka DSF aka Thermal Melt basics/00100.webp)

## 四、Tm 的定义：荧光半高处的温度

> **Tm（melting temperature，熔解温度）= 荧光爬到最大值一半时的温度**——也可以理解为"一半蛋白已经解折叠"时的温度。[【跳转到 02:20】](https://www.youtube.com/watch?v=n4g1ENKkAVw&t=140)

![熔解曲线：荧光半高处的温度即 Tm](assets/Fluorescence thermal shift (FTS) aka DSF aka Thermal Melt basics/00140.webp)

- 蛋白越结实 → 半高温度越靠后 → **Tm 越高**；
- 蛋白绑得越松 → 越容易散架 → **Tm 越低**。

## 五、什么会改变 Tm：突变、pH、配体

DSF 最大的用处是**比较**——同样的实验换个条件再做一遍，Tm 的升降立刻告诉你结论：

- **突变**：突变让蛋白更容易展开 → Tm 降低（稳定性变差）；让蛋白更稳定 → Tm 升高。[【跳转到 02:40】](https://www.youtube.com/watch?v=n4g1ENKkAVw&t=160)
- **pH**：同一个蛋白在不同 pH 下稳定性不同。扫一遍 pH 梯度，就能看出哪个 pH 下这个蛋白最稳。
- **配体结合**：小分子配体结合上去，相当于给蛋白加了额外的"扣子"——蛋白除了自身各部分互相拉住，还多拉住了这个分子，通常绑得更紧、Tm 升高；反过来，Tm 位移也常被用来**检测结合是否发生**。[【跳转到 03:05】](https://www.youtube.com/watch?v=n4g1ENKkAVw&t=185)

![突变对 Tm 的影响：更易展开→Tm 低，更稳定→Tm 高](assets/Fluorescence thermal shift (FTS) aka DSF aka Thermal Melt basics/00165.webp)

![配体结合引入额外相互作用，蛋白绑得更紧、Tm 升高](assets/Fluorescence thermal shift (FTS) aka DSF aka Thermal Melt basics/00185.webp)

## 六、怎么从曲线读出 Tm：求导取峰

荧光曲线是先升后降的钟形，肉眼找"半高点"有误差。更省事的办法是**对曲线求导（取斜率）**：

- 上升段斜率先变大再变小，随后转负——导数曲线出现一个**峰**；
- **导数峰位就是 Tm**；画出来一目了然，软件会自动算好。[【跳转到 03:25】](https://www.youtube.com/watch?v=n4g1ENKkAVw&t=205)

![对熔解曲线求导，导数峰位即 Tm](assets/Fluorescence thermal shift (FTS) aka DSF aka Thermal Melt basics/00210.webp)

## 七、实验操作要点

- 染料 SYPRO Orange 出厂是超浓母液，用前先稀释；
- 仪器就是普通的 **qPCR 仪**，只是切换到 FRET（Förster resonance energy transfer）读荧光的设置；
- 用**白色管 + 透明光学盖**：白管利于测荧光、光不会漏进别的孔；透明盖让仪器能"拍照"读数；
- 运行时程序梯度升温、边升边读图；结束后导出数据、画曲线、求导即可。[【跳转到 04:30】](https://www.youtube.com/watch?v=n4g1ENKkAVw&t=270)

![白色管 + 透明光学盖：信号好、不串孔、仪器可读数](assets/Fluorescence thermal shift (FTS) aka DSF aka Thermal Melt basics/00275.webp)

## 八、回到 ABDP：Tm 为什么是回归值

Tm 是抗体可开发性的核心指标之一：Tm 高意味着抗体耐热、耐储运、不易聚集。ABDP 用回归模型从序列预测 Tm（见知识体系 5.4.2），在湿实验之前就把候选分子的热稳定性排出优先级；而 DSF 正是实验端验证这些预测值的标准手段之一——模型预测 + DSF 验证，构成"计算—实验"闭环。

## 小结

- 热稳定性可以变成数字：DSF 荧光热位移实验 = 加热 + SYPRO Orange 染料 + 荧光读数。
- 原理链：疏水区暴露 → 染料结合发光；蛋白聚集 → 染料被挤出 → 信号被水淬灭。
- **Tm = 荧光半高处的温度 ≈ 一半蛋白解折叠的温度**；Tm 越高，蛋白越"结实"。
- 突变、pH、配体都会改变 Tm；Tm 位移可用于筛选稳定突变、找最优 pH、检测结合。
- 曲线求导取峰位即 Tm，软件自动完成。
- ABDP 用回归模型预测 Tm，DSF 是实验端的标准验证手段。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| DSF / thermal shift / thermal melt | 同一实验的不同名字：荧光热位移 / 差示扫描荧光法 / 热熔解实验 |
| SYPRO Orange | 结合疏水区后发荧光的染料；游离时被水淬灭 |
| 解折叠（unfold） | 蛋白失去折叠结构，疏水区暴露 |
| 聚集（aggregation） | 大量解折叠蛋白互相粘连，把染料挤出去 |
| Tm（熔解温度） | 荧光达到最大值一半时的温度（°C）；越高越稳定 |
| 淬灭（quench） | 水分子"偷走"游离染料的荧光能量 |
| FRET | Förster 共振能量转移，qPCR 仪上读荧光的设置名 |
