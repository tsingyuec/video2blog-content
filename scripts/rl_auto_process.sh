#!/usr/bin/env bash
# 强化学习 README 条目自动处理驱动
#
# 每批认领 N 个待处理条目（默认 2），启动一个 pi 会话派生 N 个并行子智能体，
# 各自完成「探索→下载→抽帧→字幕→图文稿→博客→配图视觉核对→回写标记」。
# 一批结束后再认领下一批，直到没有待处理条目。
#
# 用法：
#   scripts/rl_auto_process.sh            # 常驻循环，直到全部完成
#   scripts/rl_auto_process.sh --once     # 只跑一批
#   scripts/rl_auto_process.sh --stop     # 停止常驻循环
#   scripts/rl_auto_process.sh --status   # 查看状态
#
# 环境变量：
#   BATCH=2            每批条目数
#   BATCH_GAP=120      批间隔秒数
#   ENTRY_TIMEOUT=10800 单条超时秒数（默认 3 小时）

set -uo pipefail

ROOT="/workspace/working/video2blog-content"
cd "$ROOT" || exit 1

BATCH="${BATCH:-2}"
BATCH_GAP="${BATCH_GAP:-120}"
ENTRY_TIMEOUT="${ENTRY_TIMEOUT:-10800}"
LOG_DIR="$ROOT/temp/rl_auto"
LOCK="$LOG_DIR/driver.lock"
PIDFILE="$LOG_DIR/driver.pid"
STOPFILE="$LOG_DIR/STOP"
mkdir -p "$LOG_DIR"

PY="$ROOT/scripts/rl_pending.py"
SPEC="$ROOT/content/reinforcement_learning/AGENT_TASK.md"

log() { printf '[%s] %s\n' "$(date '+%F %T')" "$*"; }

status() {
  local n
  n=$(python3 "$PY" count)
  log "待处理条目: $n"
  if [[ -f "$PIDFILE" ]] && kill -0 "$(cat "$PIDFILE" 2>/dev/null)" 2>/dev/null; then
    log "驱动运行中 (pid $(cat "$PIDFILE"))"
  else
    log "驱动未运行"
  fi
  [[ -f "$STOPFILE" ]] && log "存在 STOP 标记：下一批后退出"
  return 0
}

build_prompt() {
  # $1 = 条目文本（不含行尾标记）
  cat <<EOF
你是强化学习知识体系自动整理任务的执行者。本次只处理一个条目，条目已由驱动脚本预先认领（README 行尾已有 【处理中】），不要重新认领、不要改动其它条目。

工作目录：$ROOT

请先完整阅读：
1. $ROOT/AGENTS.md
2. $SPEC

本次条目：$1

按 AGENT_TASK.md 第 2~6 节从零做到最终博客（第 7 节为驱动模式差异）：探索视频 → 精排 → 下载 → 抽帧 → 抓字幕 → 生成图文稿 → 通顺化 → 视觉核对配图 → 写博客 → 只改自己那一行 README 标记为 【已完成】。

硬性要求：
- 读图时一次只读 1 张，每轮最多 3 张，绝不超过 3 张。
- 博客不得使用 LaTeX 数学定界符（\$...\$、\$\$...\$\$）与 LaTeX 命令；行内公式用代码样式或 Unicode，成块推导用围栏代码块。
- 配图必须真正看过再写图注。
- 严禁整体重写 README，只精确替换自己那一行。
- 失败时把自己那行的 【处理中】 去掉并在结束消息说明原因。
EOF
}

run_batch() {
  local claimed
  claimed=$(python3 "$PY" claim "$BATCH")
  local n
  n=$(printf '%s' "$claimed" | python3 -c 'import json,sys; print(len(json.load(sys.stdin)))')

  if [[ "$n" -eq 0 ]]; then
    log "没有待处理条目"
    return 1
  fi

  log "本批认领 $n 个条目"

  local tmpdir
  tmpdir=$(mktemp -d "$LOG_DIR/batch.XXXXXX")
  printf '%s' "$claimed" > "$tmpdir/claimed.json"

  local i=0
  local pids=()
  local texts=()
  while IFS= read -r text; do
    i=$((i + 1))
    local pf="$tmpdir/entry-$i.prompt"
    build_prompt "$text" > "$pf"
    log "启动子智能体 #$i: $text"
    timeout "$ENTRY_TIMEOUT" pi -p --approve --name "RL-auto-$(printf '%s' "$text" | cut -c3-24)" \
      "$(cat "$pf")" > "$tmpdir/entry-$i.log" 2>&1 &
    pids+=($!)
    texts+=("$text")
  done < <(printf '%s' "$claimed" | python3 -c 'import json,sys; [print(x["text"]) for x in json.load(sys.stdin)]')

  log "等待本批 $n 个子智能体完成..."
  local k=0
  for pid in "${pids[@]}"; do
    k=$((k + 1))
    if wait "$pid"; then
      log "子智能体 #$k 正常结束: ${texts[$((k-1))]}"
    else
      local rc=$?
      log "子智能体 #$k 退出码 $rc: ${texts[$((k-1))]}（日志 $tmpdir/entry-$k.log）"
      # 超时或异常：若仍是【处理中】且没有博客，回滚为待处理
      python3 "$PY" release "${texts[$((k-1))]}" >/dev/null 2>&1 || true
    fi
  done

  log "本批完成，日志目录 $tmpdir"
  return 0
}

case "${1:-}" in
  --status)
    status
    exit 0
    ;;
  --stop)
    touch "$STOPFILE"
    log "已写入 STOP 标记，当前批次结束后退出"
    exit 0
    ;;
  --once)
    run_batch
    exit $?
    ;;
esac

# 常驻模式：单实例
exec 9>"$LOCK"
if ! flock -n 9; then
  log "已有驱动实例在运行，退出"
  exit 0
fi
echo $$ > "$PIDFILE"
trap 'rm -f "$PIDFILE"' EXIT

log "驱动启动 (batch=$BATCH gap=${BATCH_GAP}s timeout=${ENTRY_TIMEOUT}s)"

while true; do
  if [[ -f "$STOPFILE" ]]; then
    log "检测到 STOP 标记，退出"
    rm -f "$STOPFILE"
    break
  fi

  if [[ "$(python3 "$PY" count)" -eq 0 ]]; then
    log "全部条目已处理完毕，退出"
    break
  fi

  if ! run_batch; then
    log "没有可认领条目，退出"
    break
  fi

  log "批间隔 ${BATCH_GAP}s"
  sleep "$BATCH_GAP"
done

log "驱动结束"