# 系列：Minimind —— 从零手敲大模型

- **平台**：Bilibili
- **UP 主**：木乔_Mokio
- **来源**：[BV1T2k6BaEeC](https://www.bilibili.com/video/BV1T2k6BaEeC/)
- **原标题**：【2025/Minimind】Only三小时！Pytorch从零手敲大模型，架构到训练全教程
- **已整理**：25 / 26 集（约 3 小时 13 分）

> ⚠️ 第 26 集《Eval：完结！》的在线字幕服务（kedou）持续返回「抽取失败」，无法获得可信字幕，
> 为避免编造内容，本集已**弃置**（未生成文稿与博客）。

## 建议学习路线

| 阶段 | 讲次 | 内容 |
| --- | --- | --- |
| 绪论与准备 | 1–6 | 开篇、前言、前置知识、架构图解读、初始化项目 |
| 模型组件 | 7–16 | RMSNorm、RoPE&YaRN、GQA、FFN（理论 + 代码） |
| 组装与封装 | 17–20 | Block、Model、CausalLM、回顾与纠错补充 |
| 数据与训练 | 21–25 | 重制 Dataset / Pretrain、启动训练 |

## 分 P 索引

| 讲次 | 标题 | 时长 | 视频演说图文稿 | 博客 | 配图 | 原视频 |
| ---: | --- | ---: | --- | --- | ---: | --- |
| 1 | 开篇 | 02:50 | [文稿](transcripts/第01讲_开篇.md) | [博客](blog/第01讲_开篇.md) | 8 | [B站](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=1) |
| 2 | 前言 | 04:28 | [文稿](transcripts/第02讲_前言.md) | [博客](blog/第02讲_前言.md) | 13 | [B站](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=2) |
| 3 | 必看：前言补充 | 02:03 | [文稿](transcripts/第03讲_必看：前言补充.md) | [博客](blog/第03讲_必看：前言补充.md) | 10 | [B站](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=3) |
| 4 | 前置知识 | 07:17 | [文稿](transcripts/第04讲_前置知识.md) | [博客](blog/第04讲_前置知识.md) | 11 | [B站](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=4) |
| 5 | 架构图解读 | 05:46 | [文稿](transcripts/第05讲_架构图解读.md) | [博客](blog/第05讲_架构图解读.md) | 12 | [B站](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=5) |
| 6 | 初始化项目 | 03:47 | [文稿](transcripts/第06讲_初始化项目.md) | [博客](blog/第06讲_初始化项目.md) | 9 | [B站](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=6) |
| 7 | 理论：RMSNorm | 04:06 | [文稿](transcripts/第07讲_理论：RMSNorm.md) | [博客](blog/第07讲_理论：RMSNorm.md) | 8 | [B站](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=7) |
| 8 | 代码：RMSNorm | 06:25 | [文稿](transcripts/第08讲_代码：RMSNorm.md) | [博客](blog/第08讲_代码：RMSNorm.md) | 12 | [B站](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=8) |
| 9 | 理论：RoPE&YaRN | 13:51 | [文稿](transcripts/第09讲_理论：RoPE&YaRN.md) | [博客](blog/第09讲_理论：RoPE&YaRN.md) | 14 | [B站](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=9) |
| 10 | 代码：RoPE&YaRN | 17:20 | [文稿](transcripts/第10讲_代码：RoPE&YaRN.md) | [博客](blog/第10讲_代码：RoPE&YaRN.md) | 15 | [B站](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=10) |
| 11 | 理论：GQA | 03:50 | [文稿](transcripts/第11讲_理论：GQA.md) | [博客](blog/第11讲_理论：GQA.md) | 10 | [B站](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=11) |
| 12 | 代码：GQA 上 | 13:08 | [文稿](transcripts/第12讲_代码：GQA 上.md) | [博客](blog/第12讲_代码：GQA 上.md) | 14 | [B站](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=12) |
| 13 | 代码：GQA 下 | 19:22 | [文稿](transcripts/第13讲_代码：GQA 下.md) | [博客](blog/第13讲_代码：GQA 下.md) | 14 | [B站](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13) |
| 14 | 理论：FFN | 06:16 | [文稿](transcripts/第14讲_理论：FFN.md) | [博客](blog/第14讲_理论：FFN.md) | 12 | [B站](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=14) |
| 15 | 代码：FFN | 05:39 | [文稿](transcripts/第15讲_代码：FFN.md) | [博客](blog/第15讲_代码：FFN.md) | 11 | [B站](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=15) |
| 16 | 拼接：Block | 05:47 | [文稿](transcripts/第16讲_拼接：Block.md) | [博客](blog/第16讲_拼接：Block.md) | 14 | [B站](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=16) |
| 17 | 组装：Model | 11:43 | [文稿](transcripts/第17讲_组装：Model.md) | [博客](blog/第17讲_组装：Model.md) | 15 | [B站](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=17) |
| 18 | 封装：CausalLM | 10:00 | [文稿](transcripts/第18讲_封装：CausalLM.md) | [博客](blog/第18讲_封装：CausalLM.md) | 16 | [B站](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=18) |
| 19 | 回顾与知识检验 | 07:15 | [文稿](transcripts/第19讲_回顾与知识检验.md) | [博客](blog/第19讲_回顾与知识检验.md) | 9 | [B站](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=19) |
| 20 | 必看：纠错补充 | 07:55 | [文稿](transcripts/第20讲_必看：纠错补充.md) | [博客](blog/第20讲_必看：纠错补充.md) | 14 | [B站](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=20) |
| 21 | 重制Dataset：理论 | 05:32 | [文稿](transcripts/第21讲_重制Dataset：理论.md) | [博客](blog/第21讲_重制Dataset：理论.md) | 13 | [B站](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=21) |
| 22 | 重制Dataset：代码 | 08:04 | [文稿](transcripts/第22讲_重制Dataset：代码.md) | [博客](blog/第22讲_重制Dataset：代码.md) | 13 | [B站](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=22) |
| 23 | 重制Pretrain：理论 | 05:44 | [文稿](transcripts/第23讲_重制Pretrain：理论.md) | [博客](blog/第23讲_重制Pretrain：理论.md) | 10 | [B站](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=23) |
| 24 | 重制Pretrain：代码 | 09:40 | [文稿](transcripts/第24讲_重制Pretrain：代码.md) | [博客](blog/第24讲_重制Pretrain：代码.md) | 16 | [B站](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=24) |
| 25 | 训练，启动！ | 05:43 | [文稿](transcripts/第25讲_训练，启动！.md) | [博客](blog/第25讲_训练，启动！.md) | 14 | [B站](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=25) |
| ~~26~~ | ~~Eval：完结！~~（已弃置） | 08:17 | — | — | — | [B站](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=26) |

## 相关资源（来自视频简介）

- minimind 仓库：https://github.com/jingyaogong/minimind
- 视频 GitHub 仓库：https://github.com/Wood-Q/MokioMind
- 视频 Notion 笔记：https://mirage-thought-d06.notion.site/minimind-3-29c747825dae80bda611dd4dfe4f0e7b
