# AGENTS — 面向 Agent 的项目规则

本文件收录 Agent 在本仓库工作（整理视频、生成博客、维护内容）时必须遵守的规则。项目背景与系列索引见根 `README.md`。

## 项目概览

把 Bilibili / YouTube 视频整理成「**视频演说图文稿** + **初学者也能看懂的博客**」的合集。
内容按**主题系列**分目录，每个系列一个 `README.md`，用于索引该系列下的视频。处理过程中的文稿与其它中间结果放在 `_work/`，最终博客放在 `content/`。

## 目录结构

```
_work/                          # 处理中间结果（体积大、可再生，不进版本库）
└─ <系列>/
   ├─ videos/<视频ID>.mp4        # 下载的视频（仅视频流）
   ├─ frames/<视频ID>/           # 1fps 抽帧
   ├─ subs/<视频ID>.srt          # 字幕
   └─ transcripts/<名称>.md      # 视频演说图文稿（图-字幕对照）

content/                        # 最终产物
└─ <系列>/                       # 也可再套一层分组目录，如 content/protein_group/<系列>/
   ├─ README.md                  # 该系列的视频索引
   └─ blog/
      ├─ <名称>.md               # 博客
      └─ assets/<名称>/          # 博客配图
```

- **处理约定**：处理视频时，所有**中间结果**——下载的视频、1fps 抽帧、字幕，以及「图-字幕」**视频演说图文稿（文稿）**——统一放在 `_work/` 目录下；最终生成的**博客**放在 `content/` 目录下。也就是说，`content/` 只收录博客、配图与系列索引，**不包含文稿**。
- **`<名称>`**：博客按视频名称命名——多 P 系列为 `第NN讲_<分P标题>`（如 `第07讲_理论：RMSNorm`），单视频为视频名称。
- **分组目录**：相关系列可再套一层分组目录，如 `content/vllm_group/`、`content/protein_group/`；分组目录下同样放一个 `README.md` 作为该分组的索引。
- **版本控制**：仓库只收录各系列的 `README.md`、`blog/`（含配图）与 `code/`。中间结果（`_work/` 下的视频、抽帧、字幕、文稿）体积大且可再生，均由 `.gitignore` 排除。
- **生物内容的二层结构**：`content/biomodel/`（按**模型**）、`content/biodata/`（按**数据站点**）、`content/biobasic/`（**公共生物学**）采用「分组 / 主题」两层结构——主题子目录内**直接放**博客 `.md` 与配图 `assets/`，**不再有** `README.md` 与 `blog/`；每个分组各有自己的 `README.md` 作索引。

## 安装 video2blog skill

本项目的内容由 [`video2blog`](https://github.com/tsingyuec/video2blog-skill) skill 生成。

**方式一：交给 Agent 安装（推荐）**

```
Use the skills in "https://github.com/tsingyuec/video2blog-skill" that are relevant to the current task. Run `npx skills add "https://github.com/tsingyuec/video2blog-skill"` and select the relevant skills, then follow their instructions.
```

**方式二：命令行安装**

```bash
npx skills add tsingyuec/video2blog-skill       # 安装到 Agent 技能目录（本机为 ~/.agents/skills/video2blog/）
```

**安装 Python 依赖**（抽帧、图像处理、视频下载）：

```bash
pip install -r ~/.agents/skills/video2blog/requirements.txt   # opencv-python、numpy、pillow、yt-dlp
# 无桌面环境可将 opencv-python 换成 opencv-python-headless
```

- 依赖：Python 3 + `opencv-python` / `numpy`（抽帧）、`pillow`（图像处理）、`yt-dlp`（下载）；字幕抓取为纯标准库实现，无需额外依赖，但需能访问 `kedou.life`。

## 处理流程

基于 `video2blog` skill：**下载 → 抽帧 → 抓取字幕 → 生成「图-字幕」视频演说图文稿 → 通顺化 → 写博客**。

- 多 P 视频按 `?p=N` 逐集下载，时间戳跳转链接为 `?p=N&t=<秒>`；文稿与博客按 `第NN讲_<分P标题>` 命名。
- **产物落位**：下载的视频、抽帧、字幕与文稿都落在 `_work/<系列>/`；最终博客落在 `content/<系列>/blog/`。
- 博客严格基于视频演说图文稿撰写，内容可核查；字幕来自 B 站 AI 字幕，已逐窗口纠正错拼。

## 视频整理任务的调度

单个条目的执行规则见根 [`SUBAGENTS.md`](SUBAGENTS.md)，本节不重复其内容。

### 运行模型

两种驱动方式，执行规则相同：

- **单条模式**：一次运行处理一个条目，完成即结束。
- **批量驱动模式**：按批派生子智能体，见下方「批量驱动」。

无论哪种模式，**进度只存在于系列 `<README>` 的行尾标记里**，运行之间没有记忆，每次都必须重读 README 定位。

### 认领

1. 重读 `<README>`，按出现顺序列出待处理条目（行尾无任何标记的行）。一条都没有就结束本次运行。
2. 从第一个候选开始尝试认领：在该行行尾追加 `**【处理中】**`。
   - 写入**只能精确替换这一行**：`python3` 读全文 → 按内容匹配唯一行 → 只替换该行 → 写回；或 `grep -n` 定位行号后 `sed -i "<行号>s/$/ **【处理中】**/"`。**严禁整体重写覆盖文件**。
   - 写完**立即重读该行**确认：仍以 `**【处理中】**` 结尾，且没被别的运行改成 `【已完成】`。
   - 若该行已被抢先标记，或自己的写入被覆盖丢失，**换下一个候选**。
3. 所有候选都在处理中 → 结束本次运行（不等待、不重试、不排队）。
4. **先标记后干活**，认领成功再开工。

### 回收 `**【处理中】**` 残留（只回收，不做限流）

| 情形 | 处理 |
|---|---|
| 该条目博客已落位 | 只是没来得及写完成标记：**补写完成标记**后结束 |
| 博客未落位，`<temp>/<条目名>/` **近 60 分钟内仍有文件变动** | 别人正在做，**跳过** |
| 博客未落位，且 temp 目录不存在或**已超 60 分钟无变动** | 中断残留：清理 temp、把该行标记回滚为空，之后可作为候选重新认领 |

只回收「明显已死」的残留（超 60 分钟无动静），**不要**因为「感觉慢」去抢别人的条目。

### 批量驱动

```
循环：
  1. 从 <README> 认领 2 个待处理条目（标 【处理中】）
     └─ 不足 2 个就认领剩下的；0 个则退出循环
  2. 派生 2 个子智能体，各处理 1 个条目，并行运行
  3. 等待这 2 个子智能体全部结束（不提前认领下一批）
  4. 检查结果：成功 → 保留 【已完成】；失败 → 回滚该行为待处理
  5. 回到 1
```

**关键约束**：

- **一批只有 2 个**。不要一次派生 3 个以上——读图、下载、抽帧都是重资源，并发过高会互相拖慢并放大超时。
- **必须等本批全部结束再认领下一批**。提前认领会让「处理中」的条目堆积，且失败回滚时容易误伤别人正在做的条目。
- 每个子智能体**只处理自己那一个条目**：不改别人的行、不认领、不调度。
- 两个子智能体的 `<temp>` 与 `<content>` 目录天然不同（不同条目名），互不干扰；若两个条目归到同一小节，注意博客文件名不要撞车。
- **同批两条容易撞车**：若两条主题相邻，先判断它们会不会选中同一支视频。会的话在 prompt 里明确分工（各讲哪一段），或直接把已用视频列入禁选。

### 派生 prompt 必须交代的三件事

不要让它自己去猜：

1. **规则文件**：`SUBAGENTS.md` 的绝对路径（以及系列级参数表的位置）。
2. **本次条目**：README 里那一行的完整文本（不含行尾标记）。
3. **前置说明**：条目已预先认领，行尾已有 `**【处理中】**`，**不要重新认领**。

另需转达的硬性要求（`SUBAGENTS.md` 第 7 节有完整清单，prompt 里至少重复这几条）：读图一次 1 张每轮最多 3 张；公式用 KaTeX 且表格内不用裸 `|`；配图必须真正看过再写图注；录屏必须裁到纯内容区并回看确认公式完整；严禁整体重写 README。

### 失败处理

| 情形 | 处理 |
|---|---|
| 子智能体正常结束 | 保留 `【已完成】`，继续下一批 |
| 子智能体超时 / 异常退出 | 检查该条目博客是否已落位：已落位则补写完成标记；未落位则把 `**【处理中】**` 去掉回滚为待处理 |
| 本批 2 个都失败 | 不要立刻重试同一批（大概率是同一原因），记录原因后继续下一批或停止 |

### 验收

子智能体报告完成后仍需自己核一遍，不要只信它的自检：

1. **图片引用数 == 文件数**（无孤立、无缺失）。
2. `node scripts/check_md_math.mjs <目录>` 三项全 0。
3. `<README>` 只有它自己那一行变更。
4. 全量构建后跑 `node scripts/check_katex.mjs build/site/<系列> --recursive`——**源文件检查会漏掉制表符转义这类问题，构建产物检查才是最终防线**。

### 参考实现

`scripts/rl_auto_process.sh` 是这套调度的现成实现（`BATCH=2`、`ENTRY_TIMEOUT` 单条超时、`flock` 单实例、失败自动回滚），换系列时改 `SPEC`、`PY` 与日志目录即可复用。

## 交互约定

- 当用户输入 `explore:<关键词>` 时，表示要从 Bilibili / YouTube 中探索与关键词相关的视频，步骤如下：
  1. **筛选**：先根据视频标题、简介等介绍信息做大致排序，剔除与关键词不相关或相关度很低的视频。
  2. **精排**：对剩下可能高质量的视频抓取字幕，据此判断其介绍内容的**详细程度**，做更合理的排序。
  3. **展示**：按最终排序将视频展示给用户。

## Maka 定时任务管理

Maka 无公共 CLI；正规通道是用其内置的 Runtime Host 客户端 RPC（Electron 运行中即可连，无需重启）：

```js
// 存为 .mjs 后执行：ELECTRON_RUN_AS_NODE=1 /opt/Maka/maka <脚本>.mjs
import { createRequire } from 'node:module';
const require = createRequire('/opt/Maka/resources/app.asar/');
const { connectExistingRuntimeHost } = require('@maka/runtime-host/client');
const c = await connectExistingRuntimeHost({
  rootPath: '/home/zn102/.config/Maka/workspaces/default',
  protocol: { min: 0, max: 0 }, compositionId: 'maka.interactive',
});
const r = await c.connection.request('scheduled-task.mutate', { /* 输入见下 */ }, 15000);
await c.connection.close();
```

- **创建**：`{ kind: 'create', input: { title, intentBody, schedule, effect } }`；调度 `schedule` 三选一：
  `{kind:'once', runAt}` / `{kind:'interval', everySeconds, startAt}` / `{kind:'cron', expression}`（时间用 epoch 毫秒）；
  效果 `effect` 三选一：`{kind:'notify', channel:'local'}`（仅提醒）/
  `{kind:'session_resume', sessionId}`（续原对话）/
  `{kind:'agent_run', execution:{cwd, llmConnectionId, llmConnectionSlug, model, permissionMode, collaborationMode, orchestrationMode}}`（独立运行；`permissionMode` 取 `explore|ask|bypass`，无人值守用 `bypass`；连接 ID/模型见 `~/.config/Maka/workspaces/default/connection-catalog.json`）。
- **查询/暂停/恢复/删除/立即触发**：`{kind:'query'}` 走 `scheduled-task.query`（`{kind:'list'}` 或 `{kind:'get', taskId}`）；
  变更均发 `scheduled-task.mutate`：`{kind:'pause'|'resume'|'delete'|'trigger_now', taskId}`。
- 也可以在 Maka 应用内对话中直接说「创建/暂停定时任务…」，Agent 会调用内置 ScheduledTask 工具，效果相同。
