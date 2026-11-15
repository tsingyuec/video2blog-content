# scripts/ — 工具入口

这里**只放可执行工具**。站点样式/字体/第三方库不在这里（见下），内容也不在这里。

| 命令 | 作用 | 何时跑 |
| --- | --- | --- |
| `python site/build_site.py` | 装配 `content/` → `build/docs`，重写文内链接，生成 `build/nav.yml` | 每次构建前（CI 已自动跑） |
| `python site/build_site.py --check` | 同上但不写文件，只统计链接（重写/降级/未解析） | 改目录结构后核对死链 |
| `mkdocs build` | 由 `build/docs` 生成 `build/site` | 构建 |
| `node scripts/checks/check_md_math.mjs <md 或目录>` | 校验**源文件**里的公式能否被 KaTeX 渲染（失败/落单 $/残留代码样式三项须为 0） | 写完博客自检 |
| `node scripts/checks/check_images.mjs <md 或目录> [--quiet]` | 校验图片引用：文件是否存在、扩展名与文件头是否一致（`.png` 实为 WEBP 之类）、0 字节/目录、扩展名是否在发布白名单；传**目录**时额外列出「存着但没被任何文章引用」的孤儿图（可删除或挪走） | 写完博客自检、定期清理配图 |
| `node scripts/checks/check_katex.mjs build/site/<系列> --recursive` | 校验**构建产物**里的公式；能抓到源文件检查漏掉的制表符转义 | 全量构建后验收 |
| `python scripts/checks/convert_math_inline.py --dry-run <md...>` | 一次性迁移工具：把「代码样式公式」批量转成 KaTeX（历史遗留，现已无人调用） | 一般不需要 |

## 本目录之外的相关文件

| 路径 | 作用 |
| --- | --- |
| `site/build_site.py` | 站点装配脚本（上面命令表第一行） |
| `site/hooks.py` | MkDocs 构建后置 hook：把 36 MB 搜索索引改成按需加载；`mkdocs.yml` 的 `hooks:` 指向它 |
| `site/assets/` | `extra.css`（newsprint 主题）、`extra.js`（左栏文件/大纲）、`katex.js`（按需加载 KaTeX）、`fonts/`（PT Serif） |
| `vendor/katex/` | KaTeX 发行包；`build_site.py` 会把整包拷进 `build/docs/_static/katex/`，两个校验脚本也 `import` 它的 `katex.mjs` |
| `mkdocs.yml` | 站点配置；`extra_css`/`extra_javascript` 指向产物里的 `_static/*`（源文件在 `site/assets/`） |

产物路径固定：`site/assets/` → `build/docs/_static/`、`vendor/katex/` → `build/docs/_static/katex/`。
改这些路径需同时改 `site/build_site.py` 的 `ASSETS` / `VENDOR` 常量与 `mkdocs.yml`。
