# How to stop, continue and extend simulation with gmx convert-tpr

> 视频来源：[How to stop/continue/extend simulation with gmx convert-tpr - GROMACS 2025.2](https://www.youtube.com/watch?v=ad-C64mnIkE)（4 分 05 秒）

## 本讲要解决的核心问题（SCQA）

**背景**：分子动力学（MD）模拟动辄跑数天甚至数周。你把 `mdrun` 挂在服务器上，人却不可能一直守着它：可能要临时关机、集群到时被杀任务，也可能跑完 100 ns 后发现还想再跑 50 ns。

**冲突**：直觉上，中断后的模拟只能"从头再来"；想延长时间就得改参数重新准备输入文件，之前跑的结果全部作废。

**疑问**：有没有办法让模拟**从断点原地继续**，甚至**在旧结果的基础上延长**？

**回答（中心思想）**：有。GROMACS 的 **checkpoint（检查点）机制**负责"续跑"，**`gmx convert-tpr` 工具**负责"延长"——掌握这两个工具，长模拟就可以随时停下、随时接着跑、随时加时长。

---

## 一、优雅停止：Ctrl + C 不会浪费已有结果

### 1.1 按下 Ctrl + C 之后发生了什么

模拟运行中（终端正在刷帧步进度），直接按 **Ctrl + C**。[【跳转到 00:16】](https://www.youtube.com/watch?v=ad-C64mnIkE&t=16)

关键在于：`mdrun` 收到中断信号后**不会立刻硬终止**，而是在接下来约 100 步内完成收尾——把继续运行所需的全部文件写盘（state.cpt、日志等），然后干净退出。[【跳转到 00:21】](https://www.youtube.com/watch?v=ad-C64mnIkE&t=21)

![按下 Ctrl+C 后 mdrun 的收尾输出](assets/How%20to%20stop%2C%20continue%20and%20extend%20simulation%20with%20gmx%20convert-tpr/00016.webp)

> 这就是"优雅停止"：已跑出的轨迹不会损坏，而且系统已经为"下一次接着跑"准备好了材料。

### 1.2 续跑需要哪些文件

要接着跑，工作目录里必须凑齐这些文件：[【跳转到 00:32】](https://www.youtube.com/watch?v=ad-C64mnIkE&t=32)

| 文件 | 角色 |
| --- | --- |
| `.tpr` | 运行输入（二进制，grompp 生成） |
| 轨迹文件（如 `.trr` / `.xtc`） | 已跑出的坐标历史 |
| `.edr` | 能量数据 |
| `.log` | 运行日志 |
| **`.cpt`（checkpoint）** | **续跑的钥匙** |

![续跑所需的文件清单](assets/How%20to%20stop%2C%20continue%20and%20extend%20simulation%20with%20gmx%20convert-tpr/00032.webp)

其中 **checkpoint 文件是真正允许你"接着跑"的那个文件**——它记录了停止时刻所有原子的坐标、速度和随机数状态等，等于给模拟拍了张"快照"。[【跳转到 00:57】](https://www.youtube.com/watch?v=ad-C64mnIkE&t=57)

## 二、断点续跑：mdrun 指定 checkpoint 即可原地起跑

文件齐全后，续跑只需要一条命令：照常运行 `mdrun`，**用 `-cpi` 指定 checkpoint 输入文件**。[【跳转到 01:02】](https://www.youtube.com/watch?v=ad-C64mnIkE&t=62)

```bash
gmx mdrun -s topol.tpr -cpi state.cpt
```

![用 -cpi 指定 checkpoint 续跑](assets/How%20to%20stop%2C%20continue%20and%20extend%20simulation%20with%20gmx%20convert-tpr/00062.webp)

`mdrun` 会从 checkpoint 记录的时刻无缝继续，前面的轨迹与统计量全部保留——就像模拟从未中断过一样。

## 三、延长模拟时长：两条路，convert-tpr 是正路

想给模拟"加时长"有两种做法，视频对二者给出了明确的高下判断。[【跳转到 01:33】](https://www.youtube.com/watch?v=ad-C64mnIkE&t=93)

### 3.1 迂回做法：改 mdp → 重新 grompp

第一条路**绕且复杂**：手动修改 `.mdp` 文件里的模拟总时长，再用 `grompp` 重新生成二进制输入文件（`.tpr`），然后重新 `mdrun`。[【跳转到 01:38】](https://www.youtube.com/watch?v=ad-C64mnIkE&t=98)

![两种延长方式的引入](assets/How%20to%20stop%2C%20continue%20and%20extend%20simulation%20with%20gmx%20convert-tpr/00098.webp)

这条路的问题在于：`.tpr` 是从 `.mdp` 全量重新编译的，参数一旦改动就有引入不一致的风险，流程也长。

### 3.2 推荐做法：gmx convert-tpr -extend

正确且省事的方式是用 **GROMACS 套件自带的 `convert-tpr` 工具**：它直接修改二进制输入文件（`.tpr`），**完全不必碰 `.mdp`**，也不用重走 `grompp` 流程。[【跳转到 02:03】](https://www.youtube.com/watch?v=ad-C64mnIkE&t=123)

![convert-tpr 直接修改 tpr](assets/How%20to%20stop%2C%20continue%20and%20extend%20simulation%20with%20gmx%20convert-tpr/00123.webp)

用法是带上 **`-extend` 旗标**，后面接想要延长的时长（皮秒，ps）：[【跳转到 02:12】](https://www.youtube.com/watch?v=ad-C64mnIkE&t=132)

```bash
gmx convert-tpr -s topol.tpr -extend 1000 -o next.tpr   # 在原结束时刻上延长 1000 ps
gmx mdrun -s next.tpr -cpi state.cpt                     # 从 checkpoint 接着跑
```

![用 -extend 指定延长时长](assets/How%20to%20stop%2C%20continue%20and%20extend%20simulation%20with%20gmx%20convert-tpr/00132.webp)

## 小结

- **停止**：运行中按 **Ctrl + C**，`mdrun` 约在 100 步内优雅收尾，写全续跑所需文件，不损坏已有轨迹。
- **续跑**：`.tpr` + 轨迹 + `.edr` + `.log` + **`.cpt`** 齐备后，`mdrun -cpi state.cpt` 原地接着跑；**checkpoint 是续跑的钥匙**。
- **延长**：两条路——改 `.mdp` 再 `grompp`（绕、易错）vs **`gmx convert-tpr -extend`**（直接改二进制输入、推荐）；延长后同样配合 `-cpi` 续跑。
- 这套"停止 → 续跑 → 延长"组合，正是长时 MD 模拟日常运维的完整闭环。

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| checkpoint（`.cpt`） | 模拟状态的"快照"文件，记录坐标/速度等，是断点续跑的依据 |
| `.tpr` | 运行输入二进制文件，由 `grompp` 从 `.mdp` + 拓扑编译而来 |
| `mdrun -cpi` | 指定 checkpoint 输入，从快照时刻继续模拟 |
| `gmx convert-tpr -extend` | 直接修改 `.tpr` 的结束时刻来延长模拟，无需改动 `.mdp` |
| `.edr` | 能量数据文件，随模拟逐步写入 |
