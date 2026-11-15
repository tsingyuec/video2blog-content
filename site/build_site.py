#!/usr/bin/env python3
"""装配 MkDocs 文档树。

把仓库里的 `content/` 内容整理成 `build/docs/`，供 MkDocs 构建成网站：

- 根 README.md            -> build/docs/index.md（站点首页）
- content/<...>/README.md -> build/docs/<...>/index.md（各系列/分组索引）
- content/<...>/**/*.md    -> 原样拷贝（不要求有 blog/ 层）
- content/<...>/**/*.{webp,png,jpg,…} -> 原样拷贝（博客配图）
- 发布范围 = 所有 .md + 图片等非文本资源（隐藏文件/隐藏目录除外），不认目录名

同时把文内链接重写为构建后的站点 URL：
- `content/x/README.md` / `../x/README.md` / `blog/x.md` 等 -> 正确的站点相对链接
- 指向「不会被发布的内容」（非 .md / 非图片 / 隐藏文件）或压根不存在的目标的链接
  -> 降级为纯文本，避免死链；缺失的目标会统计出来，便于发现笔误

用法：
    python site/build_site.py            # 生成 build/docs
    python site/build_site.py --check    # 只做链接统计，不写文件
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

# 静态资源来源（拷贝到 build/docs/_static/ 供 mkdocs 引用）
ASSETS = os.path.join(ROOT, "site", "assets")
VENDOR = os.path.join(ROOT, "vendor")
STATIC_FILES = ("extra.css", "extra.js", "katex.js")

# 发布规则（与目录结构无关，新增系列/新目录无需改这里，也不认任何目录名/文件名）：
#   1) 所有 *.md 都发布；
#   2) 图片等非文本资源按扩展名发布（ASSET_EXTS），源码/锁文件/配置等一律不发；
#   3) 隐藏文件与隐藏目录（以 . 开头，如 .venv/、.DS_Store）不是内容，不发。
# 想「留在仓库里但不上站」的东西，按上面第 2/3 条办即可（改名成 .xxx 或非 ASSET_EXTS 后缀）。
ASSET_EXTS = {
    ".webp", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".avif", ".bmp", ".ico", ".pdf",
}

# 侧栏 = /content 的真实目录树；同级按自然序（第2讲 排在 第10讲 前）


def _natural_key(s: str):
    """自然排序：让 Lecture 2 排在 Lecture 10 之前。"""
    return [int(p) if p.isdigit() else p.lower() for p in re.split(r"(\d+)", s)]

# 链接目标可能含空格（未做 URL 编码）与成对括号（文件名如 `xxx（volume, tmpfs）.md`），
# 故允许一层括号，且用非贪婪匹配到右括号
LINK_RE = re.compile(
    r"(!?)\[([^\]]*)\]\(\s*(<[^>]*>|(?:[^()\n]|\([^()\n]*\))*?)((?:\s+\"[^\"]*\")?)\s*\)"
)

# 给正文图片补上 loading="lazy"（浏览器只加载可视区附近的图）与 decoding="async"。
# 一篇文章动辄十几张抽帧截图，不懒加载时首屏要等全部图下完。
# 已有 { ... } 属性块的图片不重复追加。
IMG_RE = re.compile(r"(!\[[^\]]*\]\((?:<[^>]*>|[^)\n])*\))(?!\s*\{)")


def rel_repo(path: str) -> str:
    return os.path.relpath(path, ROOT).replace("\\", "/")


def rel_content(path: str) -> str:
    return os.path.relpath(path, CONTENT).replace("\\", "/")


def is_hidden(sub: str) -> bool:
    """任一以 . 开头的路径段：.venv/、.git/、.DS_Store 等，都不是内容。"""
    return any(seg.startswith(".") for seg in sub.split("/"))


def is_publishable(sub: str) -> bool:
    """所有 .md + 图片等非文本资源（隐藏文件/目录除外）。"""
    if is_hidden(sub):
        return False
    ext = posixpath.splitext(sub)[1].lower()
    return ext == ".md" or ext in ASSET_EXTS


def docs_rel(sub: str) -> str:
    if sub.endswith("README.md"):
        return sub[: -len("README.md")] + "index.md"
    return sub


def nmatch(s: str) -> str:
    """Unicode NFC 归一化，用于文件名匹配。"""
    return unicodedata.normalize("NFC", s)


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
            if not is_publishable(sub):
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


def _link_candidates(pdir_repo: str, target: str) -> list[tuple[str, str]]:
    """把链接目标拆成 (仓库相对路径, #fragment) 候选。

    先按 # 当锚点切（常规写法），再把整串当路径试一次（文件名本身带 # 的情况，
    如 `Docker Crash Course #8 - Layer Caching.md`）。
    """
    candidates: list[tuple[str, str]] = []
    specs = []
    path_part, frag = _split(target)
    specs.append((unquote(path_part), frag))
    if frag:
        specs.append((unquote(target), ""))
    for path, f in specs:
        for cand in (
            posixpath.normpath(posixpath.join(pdir_repo, path)),
            posixpath.normpath(path),
        ):
            if (cand, f) not in candidates:
                candidates.append((cand, f))
    return candidates


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

        cands = _link_candidates(pdir_repo, target)

        for cand, frag in cands:
            key = nmatch(cand)
            if key in urls:
                dest = urls[key]
                rel = posixpath.relpath(dest, page_dir)
                new = quote(rel, safe="/") + frag
                if new != raw:
                    stats["rewritten"] += 1
                return f"{bang}[{label}]({new}{title})"

        # 其余一律降级为纯文本（站内不留死链），但分两档记账：
        #   unpublished：目标在仓库里存在，但按发布规则不上站（源码/配置/隐藏文件等）
        #   missing    ：目标根本不在仓库里——多半是视频演说图文稿这类被 .gitignore
        #                掉的中间产物（正常），也可能是笔误/漏提交（要报出来）
        if any(nmatch(c) in present for c, _ in cands):
            stats["unpublished"] += 1
        else:
            stats["missing"] += 1
            orphan = not any(
                os.path.isdir(os.path.join(ROOT, posixpath.dirname(c))) for c, _ in cands
            )
            stats.setdefault("missing_orphan" if orphan else "missing_file", []).append(
                f"{page_repo_rel} -> {target}"
            )
        return label

    out = []
    for i, part in enumerate(parts):
        if i % 2 == 1:  # 代码块
            out.append(part)
        else:
            part = LINK_RE.sub(handle, part)
            part = IMG_RE.sub(r'\1{ loading="lazy" decoding="async" }', part)
            out.append(part)
    return "".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只统计，不写文件")
    args = ap.parse_args()

    files, urls, present = build_plan()
    print(f"计划发布文件：{len(files)}（其中 .md：{sum(1 for d in files.values() if d.endswith('.md'))}）")

    stats = {"rewritten": 0, "unpublished": 0, "missing": 0}

    if not args.check:
        if os.path.exists(DOCS):
            shutil.rmtree(DOCS)
        os.makedirs(DOCS, exist_ok=True)
        # 生成中文导航
        nav_path = write_nav(files)
        print(f"已生成导航：{nav_path}")
        # 拷贝自定义样式 / 脚本 / 字体 / KaTeX，供 mkdocs 引用
        static_dir = os.path.join(DOCS, "_static")
        for name in STATIC_FILES:
            src = os.path.join(ASSETS, name)
            if os.path.exists(src):
                os.makedirs(static_dir, exist_ok=True)
                shutil.copy2(src, os.path.join(static_dir, name))
        katex_src = os.path.join(VENDOR, "katex")
        if os.path.isdir(katex_src):
            os.makedirs(static_dir, exist_ok=True)
            shutil.copytree(katex_src, os.path.join(static_dir, "katex"), dirs_exist_ok=True)
        fonts_src = os.path.join(ASSETS, "fonts")
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
        f"链接处理：重写 {stats['rewritten']}，降级 {stats['unpublished'] + stats['missing']}"
        f"（目标未发布 {stats['unpublished']}，目标缺失 {stats['missing']}）"
    )
    # 缺失且父目录也不存在：多半是 transcripts/ 这类被 .gitignore 掉的中间产物，正常；
    # 父目录存在却没这个文件：多半是笔误或漏提交的配图，需要人看。
    orphans = stats.get("missing_orphan", [])
    broken = stats.get("missing_file", [])
    if orphans:
        print(f"缺失目标（父目录也不存在，正常，{len(orphans)} 条）：")
        for line in orphans[:3]:
            print("  ", line)
    if broken:
        print(f"缺失目标（父目录在、文件不在，请核，{len(broken)} 条，前 20）：")
        for line in broken[:20]:
            print("  ", line)
    if not args.check:
        print(f"已生成：{DOCS}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
