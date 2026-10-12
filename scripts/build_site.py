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

# 侧栏排序优先级（同级之间），未列出的按字母序排在后面
PRIORITY = [
    "cs336", "gpu", "minimind",
    "vllm_group", "vllm", "vllm_class", "vllm_meetup",
    "aiinfra", "aiinfra_learning", "flash_attention",
    "protein_group", "protein_design", "alphafold", "protein_interaction", "protein_ml_bootcamp",
    "biomodel", "highfold",
    "kubernetes", "kubernetes_cursor", "drug_design", "ai4s_tasks",
    "agent", "biodata",
]

# 没有索引页的目录，手工指定侧栏名称
DIR_LABELS = {
    "vllm_group": "vLLM 系列",
    "protein_group": "蛋白质系列",
}

# 顶部标签分组（OI Wiki 风格）：把顶层系列归类成若干短标签，
# 标签下再列出各系列与文章。改这里即可调整顶部导航。
CATEGORY = {
    "cs336": "大语言模型",
    "minimind": "大语言模型",
    "vllm_group": "大语言模型",
    "aiinfra": "大语言模型",
    "aiinfra_learning": "大语言模型",
    "flash_attention": "大语言模型",
    "protein_group": "生物计算",
    "biomodel": "生物计算",
    "biodata": "生物计算",
    "drug_design": "生物计算",
    "ai4s_tasks": "生物计算",
    "gpu": "系统与基础设施",
    "kubernetes": "系统与基础设施",
    "kubernetes_cursor": "系统与基础设施",
    "agent": "其他",
}
CATEGORY_ORDER = ["大语言模型", "生物计算", "系统与基础设施", "其他"]

# 标题截断标记：索引页 / 博文页用不同规则，避免侧栏标题过长或丢失中文名
_CUT_INDEX = ["（", "(", "|", "｜", "·"]
_CUT_PAGE = ["——", "（", "(", "|", "｜", "·"]

# 这些目录在侧栏里"透明"（拉平），不额外产生一层分组
TRANSPARENT_DIRS = {"blog"}


def _natural_key(s: str):
    """自然排序：让 Lecture 2 排在 Lecture 10 之前。"""
    return [int(p) if p.isdigit() else p.lower() for p in re.split(r"(\d+)", s)]

# 只发布：README.md（索引） 与 blog/ 目录下的所有文件（博文 + 配图）
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
    return "/blog/" in "/" + sub


def docs_rel(sub: str) -> str:
    if sub.endswith("README.md"):
        return sub[: -len("README.md")] + "index.md"
    return sub


def nmatch(s: str) -> str:
    """Unicode NFC 归一化，用于文件名匹配。"""
    return unicodedata.normalize("NFC", s)


def has_excluded_segment(path: str) -> bool:
    return any(seg in EXCLUDE_DIRS for seg in path.split("/"))


_h1_cache: dict[str, str] = {}


def first_h1(repo_rel: str) -> str:
    """读取 Markdown 源文件的第一个一级标题。"""
    if repo_rel in _h1_cache:
        return _h1_cache[repo_rel]
    title = ""
    try:
        with open(os.path.join(ROOT, repo_rel), encoding="utf-8") as fh:
            for i, line in enumerate(fh):
                if i > 80:
                    break
                if line.startswith("# "):
                    title = line[2:].strip()
                    break
    except OSError:
        pass
    _h1_cache[repo_rel] = title
    return title


def short_title(text: str, marks) -> str:
    """把过长的标题截短，作为侧栏标签。"""
    t = text.strip()
    if not t:
        return t
    t = re.sub(r"^(系列|分组)[：:]\s*", "", t)
    cuts = [i for i in (t.find(m) for m in marks) if i > 0]
    if cuts:
        t = t[: min(cuts)]
    t = re.sub(r"\s+", " ", t).strip()
    if len(t) > 48:
        t = t[:47].rstrip() + "…"
    return t


def title_for_index(repo_rel: str) -> str:
    h1 = first_h1(repo_rel)
    # 索引页里的「——」多用于连接中英文名，替换为空格而非截断
    h1 = h1.replace("——", " ")
    return short_title(h1, _CUT_INDEX)


def title_for_page(repo_rel: str) -> str:
    return short_title(first_h1(repo_rel), _CUT_PAGE)


def humanize(name: str) -> str:
    return name.replace("_", " ").replace("-", " ").strip().title()


def _order_key(name: str):
    return (PRIORITY.index(name) if name in PRIORITY else len(PRIORITY), name)


def build_nav(files: dict[str, str]):
    """根据发布文件生成带中文标题的 nav 结构。"""
    rev = {dr: rr for rr, dr in files.items()}
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
        return sorted(kids, key=lambda x: _order_key(posixpath.basename(x)))

    def label_dir(d: str) -> str:
        if d in index_of:
            t = title_for_index(rev[index_of[d]])
            if t:
                return t
        base = posixpath.basename(d)
        return DIR_LABELS.get(base, humanize(base))

    def label_page(p: str) -> str:
        t = title_for_page(rev[p])
        return t or humanize(posixpath.splitext(posixpath.basename(p))[0])

    def disambiguate(pairs):
        """同一层出现重名标题时，用文件名加以区分。"""
        counts = defaultdict(int)
        for lab, _ in pairs:
            counts[lab] += 1
        out = []
        for lab, p in pairs:
            if counts[lab] > 1:
                stem = humanize(posixpath.splitext(posixpath.basename(p))[0])
                m = re.search(r"\d+\D*$", stem)
                suffix = (m.group(0) if m else stem).strip(" _-")
                suffix = re.sub(r"\s+", " ", suffix)
                lab = f"{lab}（{suffix}）" if suffix and suffix != lab else lab
            out.append({lab: p})
        return out

    def node(d: str):
        entries = []
        if d in index_of:
            entries.append(index_of[d])
        for sub in child_dirs(d):
            if posixpath.basename(sub) not in TRANSPARENT_DIRS:
                entries.append({label_dir(sub): node(sub)})
        pages = []
        for sub in child_dirs(d):
            if posixpath.basename(sub) in TRANSPARENT_DIRS:
                if sub in index_of:
                    entries.append(index_of[sub])
                pages.extend(pages_of.get(sub, []))
        pages.extend(pages_of.get(d, []))
        pages = sorted(pages, key=lambda x: _natural_key(posixpath.basename(x)))
        entries.extend(disambiguate([(label_page(p), p) for p in pages]))
        return entries

    tops = child_dirs("")
    grouped: dict[str, list[str]] = defaultdict(list)
    for t in tops:
        grouped[CATEGORY.get(posixpath.basename(t), "其他")].append(t)

    nav = []
    if "" in index_of:
        nav.append({title_for_index(rev[index_of[""]]) or "首页": index_of[""]})
    order = [c for c in CATEGORY_ORDER if c in grouped]
    order += [c for c in grouped if c not in CATEGORY_ORDER]
    for cat in order:
        nav.append({cat: [{label_dir(t): node(t)} for t in grouped[cat]]})
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
