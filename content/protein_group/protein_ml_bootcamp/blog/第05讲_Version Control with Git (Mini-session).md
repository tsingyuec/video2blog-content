# 第05讲：用 Git 做版本控制——从「为什么」到「亲手跑一遍 init、add、commit、branch、merge」

> 视频来源：[Version Control with Git (Mini-session)](https://www.youtube.com/watch?v=uieL4B09SK8)（Rosetta Commons ML Bootcamp：Machine Learning Methods for Protein Modeling and Design，主讲 Nick Randolph，UNC Chapel Hill，时长 11:31）
>
> 这是一节插在正课之间的小课（Mini-session），由助教 Amrita Nallathambi 现场演示。

## 本讲要解决的核心问题（SCQA）

**背景**：在蛋白质设计的后续课程里，大家要写很多代码——跑 AlphaFold、改脚本、和同伴共享工程。只要不是一个人闭门造车，就一定会遇到"我改了这段、你改了那段，最后怎么合到一起"的问题。

**冲突**：如果只会用"复制一份文件夹、改个名字、加个日期"的方式来管理代码，那么文件很容易被覆盖、也很容易忘记自己把东西放在哪儿了；几个人同时改同一个文件时更是灾难。

**疑问**：有没有一种工具，能让你和别人修改同一份代码而不互相覆盖，还能随时查看、回退历史版本？它是怎么运作的？又该怎么上手？

**回答（中心思想）**：**请务必使用 Git 做版本控制**。Git 用"仓库 + 分支 + 合并"的模型，把多人协作从"互相覆盖"变成"各自开发、最后汇聚"。要理解它，只需抓住两件事：一是 Git 仓库内部由**工作区、暂存区、仓库**三个区域组成，日常操作就是让文件在这三个区域之间流动；二是它用**分支（branch）**让你隔离地开发、再用**合并（merge）**把成果收拢回来。[【跳转到 00:11】](https://www.youtube.com/watch?v=uieL4B09SK8&t=11)

---

## 一、为什么需要 Git：多人协同时不要互相覆盖

你可以想象，很多人维护代码的方式，就是**每做一次改动就新建一个不同的目录**，如果比较聪明的话，还会给目录加上时间戳（比如 `project_2024_10_21`）。但这样做的后果是：**文件很容易被覆盖，也很容易忘记自己把东西放在哪里了**。于是程序员们发明了 Git 这样一个好用的工具，它既能帮你管理代码，也能和别人分享、协作。[【跳转到 00:29】](https://www.youtube.com/watch?v=uieL4B09SK8&t=29)

一个你会想用 Git 的典型场景是：**你和一群人一起写代码，大家都在差不多同一时间修改它**。Git 让你从一个**共享仓库（shared repository）**出发，你可以修改它、别人也可以修改它，最后大家能**汇聚到一起，把各自的功能合并（merge）起来**，而不是互相覆盖，也不是留下一堆不同的版本要处理。[【跳转到 00:51】](https://www.youtube.com/watch?v=uieL4B09SK8&t=51)

![「为什么要用 Git？」——多个开发者围绕一个共享仓库（shared repository）各自拉取与提交，而不是各自复制一堆目录](assets/第05讲_Version Control with Git (Mini-session)/00029.webp)

创建你自己分支的方式，就是从主仓库**分出一个分支（branch）**，做你的修改，然后再**合并（merge）**回代码库。[【跳转到 01:22】](https://www.youtube.com/watch?v=uieL4B09SK8&t=82)

![Git 分支模型：从主干（Master）分出「你的工作（Your Work）」，同时别人也有自己的分支，最后各自 `git merge` 回主干](assets/第05讲_Version Control with Git (Mini-session)/00100.webp)

---

## 二、Git 的三个区域：工作区、暂存区、仓库

一个 Git 仓库的主要部分由**三个区域**组成，理解它们就理解了 Git 的日常操作。[【跳转到 01:40】](https://www.youtube.com/watch?v=uieL4B09SK8&t=100)

- **工作目录（Working Directory）**：你实际写代码、改文件的地方。
- **暂存区（Staging Area）**：当你觉得某组改动"已经准备好提交"时，就把文件放进来——相当于说"好，我把这些放到一起了"。
- **`.git` 目录（仓库 / Repository）**：提交（commit）最终把暂存的改动存成一份**带时间戳的代码版本**。

文件在这三个区域之间流动，大致是：你在**工作目录**里修改 → `git add` 把它们**放入暂存区** → `git commit` 把它们**提交进仓库**；反过来 `git checkout` 可以把仓库里的版本拉回工作目录。[【跳转到 01:46】](https://www.youtube.com/watch?v=uieL4B09SK8&t=106) 提交可以反复做，如果你改动代码很多，还可以**跳回到之前某个提交**——比如你加了点东西结果把代码搞坏了，就可以退回去。这让追踪代码变得非常容易，也能确保你不会把事情搞砸。[【跳转到 02:11】](https://www.youtube.com/watch?v=uieL4B09SK8&t=131)

![Git 仓库的三个区域：工作目录（Working Directory）、暂存区（Staging Area）、`.git` 仓库，以及 `git add`/`git commit`/`git checkout` 的方向](assets/第05讲_Version Control with Git (Mini-session)/00106.webp)

> 讲者推荐把一张 **Git 速查表（Git cheat sheet）** 打印出来贴在桌子旁边，并提供了一个"Learn Git Branching"的交互式网站，用可视化的方式展示这些阶段长什么样。[【跳转到 02:36】](https://www.youtube.com/watch?v=uieL4B09SK8&t=156)

---

## 三、动手教程：init → status → add → commit

接下来讲者现场演示了一整套基本操作。整个过程如下。[【跳转到 03:29】](https://www.youtube.com/watch?v=uieL4B09SK8&t=209)

1. **创建并初始化仓库**：先创建一个目录（如 `git_tutorial`），进入目录后运行 `git init`。它会告诉你"已初始化一个空的 Git 仓库"，意思是现在你开始用 Git 追踪这个仓库了。[【跳转到 03:29】](https://www.youtube.com/watch?v=uieL4B09SK8&t=209)
2. **查看状态**：`git status` 会显示前面说的那三个区域现在各是什么情况。[【跳转到 03:54】](https://www.youtube.com/watch?v=uieL4B09SK8&t=234)
3. **添加文件**：假设你新建了一个 `test.txt`，它此时还在工作区、**没有被暂存**，`git status` 会把它显示为 **untracked（未追踪）**——也就是你还没告诉 Git 要追踪它。执行 `git add` 把它放进暂存区后，它会**从红色变成绿色**，基本意味着 Git 开始追踪这个文件了。[【跳转到 04:19】](https://www.youtube.com/watch?v=uieL4B09SK8&t=259)
4. **提交**：现在可以 `git commit` 了，等于在代码库里创建一个永久的时间点。讲者喜欢用 `-m` 参数直接附上提交信息（如 `git commit -m "first commit"`）；如果只输入 `git commit`，它会带你去一个新页面填写提交信息。[【跳转到 04:44】](https://www.youtube.com/watch?v=uieL4B09SK8&t=284)

几个容易被忽略的细节：

- 修改过已经提交过的文件后，需要**重新 `git add`** 才能让 Git 追踪这次的修改（否则 `git status` 会显示 "Changes not staged for commit"）。
- 讲者习惯直接写 `git add *`（或用 `git add .`）把改过的所有文件一次性加入，也可以逐个文件单独 add。[【跳转到 06:49】](https://www.youtube.com/watch?v=uieL4B09SK8&t=409)

---

## 四、分支与合并：branch / checkout / merge，以及冲突处理

在别人写的代码上工作时，你会想**分出一个分支**，先做自己的修改，然后再推送或合并回去。命令很简单：`git branch <分支名>`（例如 `git branch dev`）。此时用 `git branch` 就能看到有两个分支了。要切换到另一个分支，用 `git checkout dev`。[【跳转到 05:34】](https://www.youtube.com/watch?v=uieL4B09SK8&t=334)

在分支上做的修改，同样要走"修改 → `git add` → `git commit`"的流程。一旦提交，分支上就多出一个新的提交节点。如果你切回 main 分支再修改、再提交，两条分支就**开始分岔**了：main 和 dev 各自往前走，各自的文件内容可能产生冲突。[【跳转到 08:47】](https://www.youtube.com/watch?v=uieL4B09SK8&t=527)

**怎么把两条分支合起来？** 讲者的习惯是**留在 main 分支上**，然后把其他分支拉进来合并：在当前位于 main 的情况下执行 `git merge dev`。[【跳转到 09:12】](https://www.youtube.com/watch?v=uieL4B09SK8&t=552)

如果两边改了同一处，Git 会说存在**冲突（conflict）**，没法自动把两个文件合到一起，于是它会**要求你手动解决冲突**，并展示不同分支各自的改动，让你逐一把这些改动处理好、把两边的改动都保留下来，然后就能搞定。[【跳转到 09:37】](https://www.youtube.com/watch?v=uieL4B09SK8&t=577) 处理完冲突后再提交一次，两条分支就**又变回同一条分支**了。[【跳转到 10:27】](https://www.youtube.com/watch?v=uieL4B09SK8&t=627)

这就是 Git 最基础的核心内容了。Git 里还有很多东西，讲者建议跟着她提供的教程和"第一个链接"做一遍，就能把上面这套流程真正变成肌肉记忆。[【跳转到 10:52】](https://www.youtube.com/watch?v=uieL4B09SK8&t=652)

---

## 小结

- **为什么要用 Git**：多人同时改同一份代码时，Git 用"共享仓库 + 分支 + 合并"替代"复制目录/互相覆盖"，并能随时查看、回退历史版本。[【跳转到 00:29】](https://www.youtube.com/watch?v=uieL4B09SK8&t=29)
- **三个区域**：工作目录 →（`git add`）→ 暂存区 →（`git commit`）→ `.git` 仓库；`git checkout` 可以把仓库版本拉回工作目录。[【跳转到 01:40】](https://www.youtube.com/watch?v=uieL4B09SK8&t=100)
- **最小工作流**：`git init` 初始化 → `git status` 查看状态 → `git add` 暂存 → `git commit -m "..."` 提交。[【跳转到 03:29】](https://www.youtube.com/watch?v=uieL4B09SK8&t=209)
- **untracked → staged**：新文件先是未追踪（红色），`git add` 后进入暂存区并转为追踪（绿色）；改过已提交的文件要重新 add。[【跳转到 04:19】](https://www.youtube.com/watch?v=uieL4B09SK8&t=259)
- **分支与合并**：`git branch <名>` 建分支、`git checkout <名>` 切换；留在 main 上 `git merge <名>` 把他人的分支合进来。[【跳转到 05:34】](https://www.youtube.com/watch?v=uieL4B09SK8&t=334)
- **冲突**：两边改了同一处时合并无法自动完成，需要人工逐一处理，把双方改动都保留下来，再提交。[【跳转到 09:12】](https://www.youtube.com/watch?v=uieL4B09SK8&t=552)

## 关键术语速查

| 术语 | 一句话解释 |
| --- | --- |
| 版本控制（version control） | 记录代码历史、支持协作与回退的机制 |
| Git | 最流行的分布式版本控制工具 |
| 仓库（repository） | 存放项目代码及其完整历史的 `.git` 目录 |
| 共享仓库（shared repository） | 多个开发者共同拉取、提交的中心仓库 |
| 工作目录（working directory） | 你实际编辑文件的当前目录 |
| 暂存区（staging area） | 提交前暂存本次改动的地方 |
| `git init` | 把当前目录初始化成一个 Git 仓库 |
| `git status` | 查看三个区域当前状态、文件是否被追踪 |
| untracked / staged | 未被追踪（红） / 已放入暂存区待提交（绿） |
| `git add` | 把改动加入暂存区 |
| `git commit` | 把暂存区内容提交成一份带时间戳的版本（`-m` 加提交信息） |
| 分支（branch） | 从主线上分出、可独立开发的一条线 |
| `git branch` | 列出 / 创建分支 |
| `git checkout` | 切换分支（或把仓库版本检出到工作目录） |
| 合并（merge） | 把一条分支的改动汇入当前分支 |
| 冲突（conflict） | 两边改了同一处、无法自动合并，需要人工处理 |
| 速查表（cheat sheet） | 汇总常用 Git 命令的参考卡片 |
