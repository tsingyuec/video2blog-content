# 强化学习知识体系：从 MDP 到大模型 RL

> 规则：每个章节通过 `/explore <关键词>` 查找对应主题的视频；每个 `- N.M` 条目产出 1~3 篇博客。
> 进度标记 `**【处理中】**` / `**【已完成】**` 与博客链接由 Maka 定时任务维护（每 20 分钟触发、允许多轮并行），规则见同目录 [AGENT_TASK.md](AGENT_TASK.md)。

## 第一篇：强化学习基石 (Foundations)

### 第 1 章 强化学习导论
- 1.1 什么是强化学习：从试错中学习 **【已完成】** 📺 [什么是强化学习：从试错中学习](第1章_强化学习导论/什么是强化学习：从试错中学习.md)
- 1.2 强化学习与监督学习、无监督学习的边界 **【已完成】** 📺 [机器学习类型：监督学习、非监督学习、强化学习](第1章_强化学习导论/1.2_强化学习与监督学习、无监督学习的边界/机器学习类型：监督学习、非监督学习、强化学习.md) · 📺 [有监督学习、无监督学习、半监督学习和强化学习的区别](第1章_强化学习导论/1.2_强化学习与监督学习、无监督学习的边界/有监督学习、无监督学习、半监督学习和强化学习的区别.md)
- 1.3 核心要素：智能体 (Agent)、环境 (Environment)、状态 (State)、动作 (Action)、奖励 (Reward) **【处理中】**
- 1.4 探索 (Exploration) 与利用 (Exploitation) 的权衡
- 1.5 多臂赌博机问题 (Multi-Armed Bandits) 与遗憾界

### 第 2 章 马尔可夫决策过程 (MDP)
- 2.1 马尔可夫性质与马尔可夫链
- 2.2 马尔可夫奖励过程 (MRP) 与回报 (Return)、折扣因子 (Discount Factor)
- 2.3 马尔可夫决策过程 (MDP) 的数学定义
- 2.4 策略 (Policy) 与价值函数 (状态价值 $V$ 与动作价值 $Q$)
- 2.5 贝尔曼期望方程 (Bellman Expectation Equation)
- 2.6 最优策略与贝尔曼最优方程 (Bellman Optimality Equation)

---

## 第二篇：经典表格型方法 (Tabular Methods)

### 第 3 章 动态规划 (Dynamic Programming)
- 3.1 已知环境模型下的规划问题
- 3.2 策略评估 (Policy Evaluation)：迭代求解价值函数
- 3.3 策略改进 (Policy Improvement) 与策略迭代 (Policy Iteration)
- 3.4 价值迭代 (Value Iteration)
- 3.5 广义策略迭代 (GPI) 思想与动态规划的维度灾难

### 第 4 章 蒙特卡洛方法 (Monte Carlo Methods)
- 4.1 免模型 (Model-Free) 学习的基本思想
- 4.2 蒙特卡洛预测：首次访问 (First-Visit) 与每次访问 (Every-Visit)
- 4.3 蒙特卡洛控制：基于探索性起点的策略优化
- 4.4 同轨策略 (On-Policy) 与 $\epsilon$-贪婪策略 ($\epsilon$-Greedy)
- 4.5 离轨策略 (Off-Policy) 与重要性采样 (Importance Sampling)

### 第 5 章 时序差分学习 (Temporal-Difference Learning)
- 5.1 结合动态规划与蒙特卡洛：自举 (Bootstrapping) 与采样
- 5.2 TD(0) 预测算法：TD 目标与 TD 误差
- 5.3 同轨策略控制：SARSA 算法与期望 SARSA
- 5.4 离轨策略控制：Q-Learning 算法与最大化偏差、Double Q-Learning
- 5.5 多步时序差分 ($n$-step TD) 与资格迹 ($\text{TD}(\lambda)$)

---

## 第三篇：函数近似与深度强化学习 (Function Approximation & Deep RL)

### 第 6 章 价值函数近似与 DQN 家族
- 6.1 从表格到参数化函数：连续状态空间的表示
- 6.2 线性函数近似与随机梯度下降
- 6.3 深度 Q 网络 (DQN)：经验回放 (Experience Replay) 与目标网络 (Target Network)
- 6.4 DQN 的核心改进：Double DQN、优先经验回放 (PER)、Dueling DQN
- 6.5 分布式强化学习 (Distributional RL) 与 Rainbow 综合框架

### 第 7 章 策略梯度方法 (Policy Gradient Methods)
- 7.1 基于价值 vs. 基于策略：处理连续动作空间与随机策略
- 7.2 策略目标函数与策略梯度定理 (Policy Gradient Theorem)
- 7.3 蒙特卡洛策略梯度：REINFORCE 算法
- 7.4 减小方差：引入基线 (Baseline) 的 REINFORCE

### 第 8 章 演员-评论家算法 (Actor-Critic Methods)
- 8.1 Actor-Critic 架构原理：结合策略梯度与时序差分
- 8.2 优势函数 (Advantage Function) 与广义优势估计 (GAE)
- 8.3 同步与异步优势演员-评论家：A2C 与 A3C
- 8.4 确定性策略梯度：DDPG 算法
- 8.5 延迟策略更新与目标平滑：TD3 (Twin Delayed DDPG) 算法

### 第 9 章 现代主流深度强化学习算法
- 9.1 策略更新的步长困境与单调改进保证
- 9.2 信赖域策略优化 (TRPO)：KL 散度约束与共轭梯度
- 9.3 近端策略优化 (PPO)：PPO-Penalty 与 PPO-Clip
- 9.4 最大熵强化学习框架：探索与鲁棒性
- 9.5 柔性演员-评论家算法 (SAC, Soft Actor-Critic)

---

## 第四篇：基于模型的强化学习与规划 (Model-Based RL & Planning)

### 第 10 章 环境建模与搜索规划
- 10.1 有模型 (Model-Based) 与免模型 (Model-Free) 的权衡
- 10.2 环境转移模型的学习与复合误差问题 (Compounding Error)
- 10.3 整合学习与规划：Dyna 架构与 Dyna-Q
- 10.4 蒙特卡洛树搜索 (MCTS) 与 UCT 算法
- 10.5 从 AlphaGo、AlphaZero 到 MuZero (隐空间规划)
- 10.6 世界模型 (World Models) 与 MBPO (Model-Based Policy Optimization)

---

## 第五篇：进阶专题与前沿应用 (Advanced Topics & Frontiers)

### 第 11 章 模仿学习与逆强化学习
- 11.1 稀疏奖励困境与专家演示数据
- 11.2 行为克隆 (Behavioral Cloning) 与分布偏移、DAgger 算法
- 11.3 逆强化学习 (IRL)：从行为反推奖励函数
- 11.4 生成对抗模仿学习 (GAIL)

### 第 12 章 离线强化学习 (Offline RL)
- 12.1 离线强化学习的定义与应用场景 (纯静态数据集学习)
- 12.2 核心挑战：分布外 (OOD) 动作与价值高估
- 12.3 策略约束方法 (BCQ, BEAR)
- 12.4 保守价值估计：CQL (Conservative Q-Learning) 与 IQL
- 12.5 序列建模视角：Decision Transformer

### 第 13 章 多智能体强化学习 (MARL)
- 13.1 多智能体系统的博弈论基础：纳什均衡与马尔可夫博弈
- 13.2 关系设定：完全合作、完全竞争与混合场景
- 13.3 集中式训练与分布式执行 (CTDE) 范式
- 13.4 价值分解方法：VDN 与 QMIX
- 13.5 多智能体策略梯度：MADDPG 与 MAPPO

### 第 14 章 大模型时代的强化学习 (RL for LLMs)
- 14.1 语言模型作为策略网络：序列生成的 MDP 建模
- 14.2 人类反馈强化学习 (RLHF) 三阶段流程
- 14.3 奖励模型 (Reward Model) 的训练与 Bradley-Terry 模型
- 14.4 直接偏好优化 (DPO) 及其变体 (IPO, KTO)
- 14.5 面向推理能力的强化学习：过程奖励模型 (PRM) 与 GRPO (Group Relative Policy Optimization)
