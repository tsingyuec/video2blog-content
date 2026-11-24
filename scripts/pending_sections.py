#!/usr/bin/env python3
"""列出 / 认领 / 改状态：系列 README 里的小节。

用法：
    # 列出待处理小节（默认只看 WAITING），带博客目录与 _work 目录
    python3 scripts/pending_sections.py "content/<域>/<分类>/<系列>"

    # 看别的状态
    python3 scripts/pending_sections.py "content/<域>/<分类>/<系列>" --status PROCESSING

    # 认领 N 条：把行尾 [WAITING] 改成 [PROCESSING]
    python3 scripts/pending_sections.py "content/<域>/<分类>/<系列>" --claim 2

    # 改状态：DONE / WAITING / PROCESSING / REUSE / ABORT
    # --id 就是小节行里 <a id="..."> 的值（全库唯一）
    python3 scripts/pending_sections.py "content/<域>/<分类>/<系列>" --set DONE --id s07-1-2-2
    python3 scripts/pending_sections.py "content/<域>/<分类>/<系列>" --set REUSE --id s07-1-2-2 --link "../../x/README.md#y"

路径参数可以是系列 README、系列目录，或任意上级目录（递归找出下面所有系列索引）。
"""

from __future__ import annotations

import argparse
import fcntl
import os
import re
import sys

STATUSES = ("WAITING", "PROCESSING", "DONE", "REUSE", "ABORT")
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SUB_RE = re.compile(
    r"^-\s+(?P<num>\d+(?:\.\d+)+)\s+(?P<title>.+?)\s*"
    r'(?:<a\s+id="(?P<anchor>[^"]*)"></a>)?\s*'
    r"\[(?P<status>" + "|".join(STATUSES) + r")\]\s*"
    r"(?:\((?P<link>[^)]*)\))?\s*$"
)
SEC_RE = re.compile(r"^###\s+(?P<num>\d+(?:\.\d+)+)\s+(?P<title>\S.*?)\s*$")
GOAL_RE = re.compile(r"^\s+-\s+学习目标[：:]\s*(?P<goal>.+?)\s*$")


def dirname(num: str, title: str) -> str:
    """README 标题 -> 目录名：去反引号，斜杠换全角（与库内既有约定一致）。"""
    t = re.sub(r"\s+", " ", title.replace("`", "").replace("/", "／")).strip()
    return f"{num}_{t}"


def parse(path: str) -> list[dict]:
    """把 README 解析成 [{num, title, subs:[{num,title,status,goal,link,anchor,raw}]}]。"""
    sections: list[dict] = []
    sec = sub = None
    for raw in open(path, encoding="utf-8"):
        line = raw.rstrip("\n")
        m = SUB_RE.match(line)
        if m:
            sub = {k: m.group(k) or "" for k in ("num", "title", "status", "anchor", "link")}
            sub.update(goal="", raw=line)
            if sec is None:  # 小节出现在任何 ### 之前，兜底
                sec = {"num": m.group("num").rsplit(".", 1)[0], "title": "", "subs": []}
                sections.append(sec)
            sec["subs"].append(sub)
            continue
        m = SEC_RE.match(line)
        if m:
            sec = {"num": m.group("num"), "title": m.group("title"), "subs": []}
            sections.append(sec)
            sub = None
            continue
        if sub is not None:
            g = GOAL_RE.match(line)
            if g:
                sub["goal"] = g.group("goal")
                sub = None
    return sections


def find_readmes(root: str) -> list[str]:
    """root 可以是 README.md、系列目录、或上层目录。"""
    if os.path.isfile(root):
        return [root]
    out = []
    for dirpath, _dirs, files in os.walk(root):
        p = os.path.join(dirpath, "README.md")
        if "README.md" in files and _has_subs(p):
            out.append(p)
    return sorted(out)


def _has_subs(path: str) -> bool:
    try:
        return any(SUB_RE.match(l) for l in open(path, encoding="utf-8"))
    except OSError:
        return False


def locate(series_dir: str, sec: dict, sub: dict) -> tuple[str, str, bool]:
    """返回 (节目录, 小节目录, 是否已存在)。磁盘上已有的优先，否则用 README 推导名。"""
    sec_dir = _pick(series_dir, sec["num"], sec["title"])
    sub_dir = _pick(os.path.join(series_dir, sec_dir), sub["num"], sub["title"])
    return sec_dir, sub_dir, os.path.isdir(os.path.join(series_dir, sec_dir, sub_dir))


def _pick(parent: str, num: str, title: str) -> str:
    """在 parent 下找 `num_` 开头的目录；找不到就用 README 推导名。"""
    try:
        for name in sorted(os.listdir(parent)):
            if name.startswith(f"{num}_") and os.path.isdir(os.path.join(parent, name)):
                return name
    except OSError:
        pass
    return dirname(num, title)


def collect(paths: list[str], statuses: set[str]) -> list[dict]:
    out = []
    seen = set()
    for root in paths:
        for readme in find_readmes(root):
            if readme in seen:
                continue
            seen.add(readme)
            series_dir = os.path.dirname(os.path.abspath(readme))
            for sec in parse(readme):
                for sub in sec["subs"]:
                    if statuses and sub["status"] not in statuses:
                        continue
                    sec_dir, sub_dir, exists = locate(series_dir, sec, sub)
                    out.append({
                        "readme": readme,
                        "series": os.path.basename(series_dir),
                        "sec_num": sec["num"],
                        "sec_title": sec["title"],
                        "path": os.path.join(series_dir, sec_dir, sub_dir),
                        "work": work_path(series_dir, sub_dir),
                        "exists": exists,
                        **sub,
                    })
    return out


def work_path(series_dir: str, sub_dir: str) -> str:
    """content/<域>/<分类>/<系列> -> _work/<域>/<分类>/<系列>/<小节>。"""
    rel = os.path.relpath(series_dir, os.path.join(REPO_ROOT, "content"))
    if rel.startswith(".."):
        rel = os.path.basename(series_dir)
    return os.path.join("_work", rel, sub_dir)


def rewrite(row: dict, status: str, link: str | None, require: str | None = None) -> bool:
    """把这一行的状态改成 status（必要时换 REUSE 链接）。带锁、只改这一行、写完重读校验。

    require 指定时，当前状态必须等于它才动手——认领靠这个避免两个进程抢同一条。
    """
    with open(row["readme"], "r+", encoding="utf-8") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            lines = fh.readlines()
            idx = next(
                (i for i, l in enumerate(lines)
                 if SUB_RE.match(l.rstrip("\n"))
                 and (f'id="{row["anchor"]}"' in l if row["anchor"] else l.rstrip("\n") == row["raw"])),
                None,
            )
            if idx is None:
                return False
            if require is not None:
                cur = SUB_RE.match(lines[idx].rstrip("\n"))
                if not cur or cur.group("status") != require:
                    return False  # 已被别人改过
            body = lines[idx].rstrip("\n")
            new = re.sub(r"\[(?:" + "|".join(STATUSES) + r")\]", f"[{status}]", body, count=1)
            if status == "REUSE" and link is not None:
                new = re.sub(r"\s*\([^)]*\)\s*$", "", new) + f" ({link})"
            elif status != "REUSE":
                new = re.sub(r"\s*\([^)]*\)\s*$", "", new)  # 非 REUSE 不带复用链接
            if new != body:
                lines[idx] = new + "\n"
                fh.seek(0)
                fh.writelines(lines)
                fh.truncate()
                fh.flush()
                os.fsync(fh.fileno())
            fh.seek(0)
            return f"[{status}]" in fh.readlines()[idx]
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)


def claim(paths: list[str], n: int) -> list[dict]:
    """按 README 顺序认领 n 条 WAITING；被抢先的跳过，继续下一个候选。"""
    got = []
    for row in collect(paths, {"WAITING"}):
        if len(got) >= n:
            break
        if rewrite(row, "PROCESSING", None, require="WAITING"):
            row["status"] = "PROCESSING"
            got.append(row)
    return got


def set_status(paths: list[str], ids: list[str], status: str, link: str | None):
    """按 <a id> 改状态。返回 (成功, 失败[(id, 原因)])。"""
    all_rows = collect(paths, set())
    ok, bad = [], []
    for wanted in ids:
        cands = [r for r in all_rows if r["anchor"] == wanted]
        if not cands:
            bad.append((wanted, "找不到这个 id"))
        elif len(cands) > 1:
            bad.append((wanted, f"有 {len(cands)} 个小节用了同一个 id"))
        elif rewrite(cands[0], status, link):
            cands[0]["status"] = status
            ok.append(cands[0])
        else:
            bad.append((wanted, "写入失败"))
    return ok, bad


def show(rows: list[dict]) -> None:
    series = sec = None
    for r in rows:
        if r["series"] != series:
            series, sec = r["series"], None
            print(f"\n■ {series}")
        if r["sec_num"] != sec:
            sec = r["sec_num"]
            print(f"\n  {r['sec_num']} {r['sec_title']}")
        notes = [r["anchor"]] if r["anchor"] else []
        if not r["exists"] and r["status"] not in ("REUSE", "ABORT"):
            notes.append("目录待建")
        suffix = f"  ({', '.join(notes)})" if notes else ""
        print(f"    [{r['status']}] {r['num']} {r['title']}{suffix}")
        if r["goal"]:
            print(f"        学习目标：{r['goal']}")
        if r["status"] == "REUSE":
            print(f"        复用：{r['link'] or '（README 未给链接）'}")
        elif r["status"] != "ABORT":
            print(f"        博客：{r['path']}")
            print(f"        工作：{r['work']}")
    print(f"\n合计：{len(rows)} 条")


def main() -> int:
    ap = argparse.ArgumentParser(description="列出 / 认领 / 改状态：系列 README 里的小节。")
    ap.add_argument("paths", nargs="+", help="系列 README / 系列目录 / 上层目录")
    ap.add_argument("--status", default="WAITING", help="状态过滤，默认 WAITING；all 表示不过滤")
    ap.add_argument("--claim", type=int, metavar="N", help="认领 N 条 WAITING")
    ap.add_argument("--set", metavar="STATUS", help="把 --id 指定的小节改成该状态")
    ap.add_argument("--id", default="", help="--set 的目标 <a id>，逗号分隔")
    ap.add_argument("--link", help="--set REUSE 时附带的复用链接")
    args = ap.parse_args()

    if args.set:
        status = args.set.strip().upper()
        if status not in STATUSES:
            print(f"未知状态：{status}；可选 {list(STATUSES)}", file=sys.stderr)
            return 2
        ids = [i.strip().lstrip("#") for i in args.id.split(",") if i.strip()]
        if not ids:
            print("--set 需要配合 --id，例如 --set DONE --id s07-1-2-2", file=sys.stderr)
            return 2
        ok, bad = set_status(args.paths, ids, status, args.link)
        for r in ok:
            print(f"[{status}] {r['num']} {r['title']}  ({r['anchor']})")
            print(f"    {r['readme']}")
        for num, why in bad:
            print(f"[失败] {num}：{why}", file=sys.stderr)
        print(f"\n成功 {len(ok)} 条，失败 {len(bad)} 条")
        return 1 if bad else 0

    if args.claim:
        got = claim(args.paths, args.claim)
        if not got:
            print("没有可认领的小节（候选都已被抢先，或本来就没有 WAITING）。")
            return 0
        show(got)
        return 0

    want = set() if args.status.lower() == "all" else {
        s.strip().upper() for s in args.status.split(",") if s.strip()
    }
    if want - set(STATUSES):
        print(f"未知状态：{sorted(want - set(STATUSES))}", file=sys.stderr)
        return 2
    found = collect(args.paths, want)
    if not found:
        print("没有匹配的小节。")
        return 0
    show(found)
    return 0


if __name__ == "__main__":
    sys.exit(main())