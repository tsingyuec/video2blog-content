# scripts/check — 内容公式检查

只处理这个内容仓库的公式渲染链：Markdown 源文件与 MkDocs 构建产物。它们依赖 `vendor/katex/`，不属于通用的 `video2blog` skill。

## 脚本

| 脚本 | 检查什么 |
| --- | --- |
| `check_md_math.mjs` | 源文件中的 `$...$` / `$$...$$` 能否被 KaTeX 渲染、落单 `$`、代码样式公式嫌疑 |
| `check_katex.mjs` | 构建后 HTML 里的公式能否被 KaTeX 渲染、页面残留的 `$` |
| `katex.mjs` | 定位 KaTeX 的加载器，供上面两个脚本复用 |

## 用法

从仓库根目录运行：

```bash
node scripts/check/check_md_math.mjs content/<系列>/X.Y_<节>/X.Y.Z_<小节>
node scripts/check/check_katex.mjs build/site/<系列> --recursive
```

默认从当前目录向上查找 `vendor/katex/katex.mjs`；也可用 `KATEX_PATH` 指定其他 KaTeX 发行包。

退出码：0 通过，1 有问题，2 用法/依赖错误。
