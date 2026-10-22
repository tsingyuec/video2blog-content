#!/usr/bin/env python3
"""装配 MkDocs 文档树。

把仓库里的 `content/` 内容整理成 `build/docs/`，供 MkDocs 构建成网站：

- 根 README.md            -> build/docs/index.md（站点首页）
- content/<...>/README.md -> build/docs/<...>/index.md（各系列/分组索引）
- content/<...>/blog/**   -> 原样拷贝（博文与配图）
- 排除 transcripts/ 与 code/（体积巨大，且非博客正文）

同时把文内链接重写为构建后的站点 URL：
- `content/x/README.md` / `../x/README.md` / `blog/x.md` 等 -> 正确的站点相对链接
- 指向被排除内容（transcripts/code）的链接 -> 降级为纯文本，避免死链

用法：
    python scripts/build_site.py            # 生成 build/docs
    python scripts/build_site.py --check    # 只做链接统计，不写文件
"""

from __future__ import annotations

import argparse
import os
import posixpath
import re
import shutil
import sys
import unicodedata
from collections import defaultdict
from urllib.parse import quote, unquote

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT = os.path.join(ROOT, "content")
DOCS = os.path.join(ROOT, "build", "docs")

# 这些目录（content/ 下的任意层级）不发布
EXCLUDE_DIRS = {"transcripts", "code"}

# 「扁平」结构的分组根目录：如 content/biomodel/<模型>/*.md、content/biodata/<站点>/*.md、
# content/biobasic/*.md —— 这些目录下不再有 README.md 与 blog/，博客与配图直接落在子目录里
# 生物信息：Maka 定时任务产出的章节目录（章节/条目/配图，同样无 blog/ 层）
# 容器技术：同结构新知识树（层级为 第N章 → X.Y 小节 → X.Y.Z 条目）
FLAT_ROOT_DIRS = ("biomodel", "biodata", "biobasic", "生物信息", "容器技术")

# 侧栏 = /content 的真实目录树；同级按自然序（第2讲 排在 第10讲 前）


def _natural_key(s: str):
    """自然排序：让 Lecture 2 排在 Lecture 10 之前。"""
    return [int(p) if p.isdigit() else p.lower() for p in re.split(r"(\d+)", s)]

# 发布范围：README.md（索引）、blog/ 目录下的所有文件（博文 + 配图），
# 以及 FLAT_ROOT_DIRS 扁平分组下的所有文件。
# 链接目标可能含空格（未做 URL 编码），故用非贪婪匹配到右括号
LINK_RE = re.compile(r"(!?)\[([^\]]*)\]\(\s*(<[^>]*>|[^)\n]*?)((?:\s+\"[^\"]*\")?)\s*\)")


def rel_repo(path: str) -> str:
    return os.path.relpath(path, ROOT).replace("\\", "/")


def rel_content(path: str) -> str:
    return os.path.relpath(path, CONTENT).replace("\\", "/")


def is_excluded(sub: str) -> bool:
    return any(seg in EXCLUDE_DIRS for seg in sub.split("/"))


def is_included(sub: str) -> bool:
    base = posixpath.basename(sub)
    if base == "README.md":
        return True
    if "/blog/" in "/" + sub:
        return True
    # 扁平分组（biomodel / biodata / biobasic）：目录下的 .md 与配图一并发布
    return sub.split("/", 1)[0] in FLAT_ROOT_DIRS


def docs_rel(sub: str) -> str:
    if sub.endswith("README.md"):
        return sub[: -len("README.md")] + "index.md"
    return sub


def nmatch(s: str) -> str:
    """Unicode NFC 归一化，用于文件名匹配。"""
    return unicodedata.normalize("NFC", s)


def has_excluded_segment(path: str) -> bool:
    return any(seg in EXCLUDE_DIRS for seg in path.split("/"))


def build_nav(files: dict[str, str]):
    """按 /content 的真实目录结构生成 nav：目录名 / 文件名原样保留，
    保留 blog 层级，不显示图片（assets）等非 .md 目录。"""
    index_of: dict[str, str] = {}
    pages_of: dict[str, list[str]] = defaultdict(list)
    all_dirs: set[str] = set()

    for rr, dr in files.items():
        if not dr.endswith(".md"):
            continue
        d = posixpath.dirname(dr)
        all_dirs.add(d)
        if d:
            parts = d.split("/")
            for i in range(1, len(parts) + 1):
                all_dirs.add("/".join(parts[:i]))
        if posixpath.basename(dr) == "index.md":
            index_of[d] = dr
        else:
            pages_of[d].append(dr)

    def child_dirs(parent: str):
        kids = [x for x in all_dirs if x != parent and posixpath.dirname(x) == parent]
        return sorted(kids, key=lambda x: _natural_key(posixpath.basename(x)))

    def node(d: str):
        entries = []
        for sub in child_dirs(d):                      # 目录在前
            entries.append({posixpath.basename(sub): node(sub)})
        files_here = list(pages_of.get(d, []))         # 文件在后
        if d in index_of:
            files_here.append(index_of[d])
        for p in sorted(files_here, key=lambda x: _natural_key(posixpath.basename(x))):
            base = posixpath.basename(p)
            label = "README.md" if base == "index.md" else base
            entries.append({label: p})
        return entries

    nav = []
    if "" in index_of:
        nav.append({"首页": index_of[""]})
    for top in child_dirs(""):
        nav.append({posixpath.basename(top): node(top)})
    return nav


def write_nav(files: dict[str, str]) -> str:
    nav = build_nav(files)
    path = os.path.join(ROOT, "build", "nav.yml")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(
            yaml.safe_dump(
                {"nav": nav},
                allow_unicode=True,
                sort_keys=False,
                default_flow_style=False,
                width=1000,
            )
        )
    return path


def build_plan():
    files: dict[str, str] = {}   # repo_rel -> docs_rel
    urls: dict[str, str] = {}    # NFC(repo_rel) -> docs_rel（页面/资源在 docs 里的真实路径）
    present: set[str] = set()    # 所有存在的仓库文件（含被排除的）

    # 根 README
    root_readme = os.path.join(ROOT, "README.md")
    if os.path.exists(root_readme):
        files["README.md"] = "index.md"
        urls[nmatch("README.md")] = "index.md"

    # 根 AGENTS.md（README 中有链接指向它）
    root_agents = os.path.join(ROOT, "AGENTS.md")
    if os.path.exists(root_agents):
        files["AGENTS.md"] = "AGENTS.md"
        urls[nmatch("AGENTS.md")] = "AGENTS.md"

    for dirpath, dirnames, filenames in os.walk(CONTENT):
        for fn in filenames:
            src = os.path.join(dirpath, fn)
            rr = rel_repo(src)
            present.add(nmatch(rr))
            sub = rel_content(src)
            if is_excluded(sub) or not is_included(sub):
                continue
            dr = docs_rel(sub)
            files[rr] = dr
            urls[nmatch(rr)] = dr

    return files, urls, present


def _split(url: str) -> tuple[str, str]:
    if "#" in url:
        p, f = url.split("#", 1)
        return p, "#" + f
    return url, ""


def _is_external(t: str) -> bool:
    return (
        not t
        or t.startswith("#")
        or t.startswith("//")
        or t.startswith("/")
        or re.match(r"^[a-zA-Z][a-zA-Z0-9+.\-]*:", t) is not None
    )


def rewrite_text(text, page_repo_rel, page_docs, urls, present, stats):
    page_dir = posixpath.dirname(page_docs) or "."
    pdir_repo = posixpath.dirname(page_repo_rel)

    # 跳过围栏代码块
    parts = re.split(r"(```.*?```)", text, flags=re.S)

    def handle(m: re.Match) -> str:
        bang, label, target, title = m.groups()
        raw = target
        target = target.strip()
        if target.startswith("<") and target.endswith(">"):
            target = target[1:-1]
        if _is_external(target):
            return m.group(0)

        path_part, frag = _split(target)
        decoded = unquote(path_part)

        cands = [
            posixpath.normpath(posixpath.join(pdir_repo, decoded)),
            posixpath.normpath(decoded),
        ]
        for cand in cands:
            key = nmatch(cand)
            if key in urls:
                dest = urls[key]
                rel = posixpath.relpath(dest, page_dir)
                new = quote(rel, safe="/") + frag
                if new != raw:
                    stats["rewritten"] += 1
                return f"{bang}[{label}]({new}{title})"

        # 指向被排除/未发布的内容：降级为纯文本（含仓库里本就缺失的 transcripts 链接）
        for cand in cands:
            if nmatch(cand) in present or has_excluded_segment(cand):
                stats["neutralized"] += 1
                return label

        # 无法解析：原样保留
        stats["unresolved"] += 1
        if decoded.endswith(".md"):
            stats.setdefault("unresolved_md", [])
            stats["unresolved_md"].append(f"{page_repo_rel} -> {target}")
        return m.group(0)

    out = []
    for i, part in enumerate(parts):
        if i % 2 == 1:  # 代码块
            out.append(part)
        else:
            out.append(LINK_RE.sub(handle, part))
    return "".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只统计，不写文件")
    args = ap.parse_args()

    files, urls, present = build_plan()
    print(f"计划发布文件：{len(files)}（其中 .md：{sum(1 for d in files.values() if d.endswith('.md'))}）")

    stats = {"rewritten": 0, "neutralized": 0, "unresolved": 0}

    if not args.check:
        if os.path.exists(DOCS):
            shutil.rmtree(DOCS)
        os.makedirs(DOCS, exist_ok=True)
        # 生成中文导航
        nav_path = write_nav(files)
        print(f"已生成导航：{nav_path}")
        # 拷贝自定义样式 / 脚本 / 字体，供 mkdocs 引用
        static_dir = os.path.join(DOCS, "_static")
        for name in ("extra.css", "extra.js"):
            src = os.path.join(ROOT, "scripts", name)
            if os.path.exists(src):
                os.makedirs(static_dir, exist_ok=True)
                shutil.copy2(src, os.path.join(static_dir, name))
        fonts_src = os.path.join(ROOT, "scripts", "fonts")
        if os.path.isdir(fonts_src):
            shutil.copytree(fonts_src, os.path.join(static_dir, "fonts"), dirs_exist_ok=True)

    for rr, dr in files.items():
        src = os.path.join(ROOT, rr)
        dst = os.path.join(DOCS, dr)
        if args.check:
            if dr.endswith(".md"):
                text = open(src, encoding="utf-8").read()
                rewrite_text(text, rr, urls[nmatch(rr)], urls, present, stats)
            continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if dr.endswith(".md"):
            text = open(src, encoding="utf-8").read()
            text = rewrite_text(text, rr, urls[nmatch(rr)], urls, present, stats)
            with open(dst, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
        else:
            shutil.copy2(src, dst)

    print(
        f"链接处理：重写 {stats['rewritten']}，降级 {stats['neutralized']}，未解析 {stats['unresolved']}"
    )
    bad = stats.get("unresolved_md", [])
    if bad:
        print(f"未解析的 .md 链接（{len(bad)} 条，前 20）：")
        for line in bad[:20]:
            print("  ", line)
    if not args.check:
        print(f"已生成：{DOCS}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
