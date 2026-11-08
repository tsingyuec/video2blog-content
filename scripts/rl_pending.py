#!/usr/bin/env python3
"""强化学习 README 条目状态工具。

用法：
  rl_pending.py list            列出待处理条目（JSON）
  rl_pending.py claim N         认领前 N 个待处理条目（行尾加 【处理中】），输出 JSON
  rl_pending.py release "文本"  把某条目行尾的 【处理中】 去掉
  rl_pending.py count           待处理条目数量
"""
import json
import re
import sys
from pathlib import Path

README = Path(__file__).resolve().parent.parent / "content/reinforcement_learning/README.md"
DONE = "【已完成】"
BUSY = "【处理中】"
ENTRY_RE = re.compile(r"^- ")


def read_lines():
    return README.read_text(encoding="utf-8").splitlines(keepends=True)


def write_lines(lines):
    README.write_text("".join(lines), encoding="utf-8")


def is_entry(line: str) -> bool:
    return bool(ENTRY_RE.match(line))


def pending(lines):
    out = []
    for i, line in enumerate(lines):
        if is_entry(line) and DONE not in line and BUSY not in line:
            out.append((i, line.rstrip("\n")))
    return out


def cmd_list():
    lines = read_lines()
    items = [{"line": i + 1, "text": t} for i, t in pending(lines)]
    print(json.dumps(items, ensure_ascii=False))


def cmd_count():
    print(len(pending(read_lines())))


def cmd_claim(n):
    n = int(n)
    lines = read_lines()
    cands = pending(lines)[:n]
    claimed = []
    for idx, text in cands:
        # 重新读一次，避免与并发写入冲突
        lines = read_lines()
        cur = lines[idx].rstrip("\n")
        if cur != text:
            # 行内容变了，重新定位
            for j, line in enumerate(lines):
                if line.rstrip("\n") == text:
                    idx = j
                    break
            else:
                continue
        if DONE in lines[idx] or BUSY in lines[idx]:
            continue
        lines[idx] = lines[idx].rstrip("\n") + f" {BUSY}\n"
        write_lines(lines)
        claimed.append({"line": idx + 1, "text": text})
    print(json.dumps(claimed, ensure_ascii=False))


def cmd_release(text):
    lines = read_lines()
    target = text.rstrip("\n")
    for i, line in enumerate(lines):
        cur = line.rstrip("\n")
        if BUSY not in cur:
            continue
        if cur == target or cur == target + f" {BUSY}":
            lines[i] = cur.replace(f" {BUSY}", "") + "\n"
            write_lines(lines)
            print("released")
            return
    print("not-found")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "count"
    if cmd == "list":
        cmd_list()
    elif cmd == "count":
        cmd_count()
    elif cmd == "claim":
        cmd_claim(sys.argv[2])
    elif cmd == "release":
        cmd_release(sys.argv[2])
    else:
        sys.exit(f"unknown command: {cmd}")