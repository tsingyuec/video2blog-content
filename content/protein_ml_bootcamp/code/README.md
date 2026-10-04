# 配套代码：PyMOL 环境（第 02 讲：PyMol and VS Code）

这是系列 `protein_ml_bootcamp` 第 02 讲的配套 [uv](https://docs.astral.sh/uv/) 项目，
用于在本机运行 / 查看 **PyMOL（Open-Source 3.2）** 的图形界面。

## 快速开始

```bash
uv sync                       # 创建 .venv 并安装依赖
uv run pymol                  # 打开 PyMOL 图形界面（独立桌面窗口）
uv run pymol demo.pml         # 打开界面并自动加载示例结构 1AO7
```

在 PyMOL 窗口底部命令行可输入：`fetch 1ao7`、`show cartoon`、`color cyan`、`ray`、`png out.png` 等。

## 目录内容

| 文件 | 说明 |
| --- | --- |
| `pyproject.toml` | uv 项目定义；依赖 `pymol` |
| `uv.lock` | 锁定版本，保证 `uv sync` 可复现 |
| `demo.pml` | 示例脚本：加载 1AO7 并卡通显示 |

## 为什么依赖指向 cgohlke 的 wheel

PyPI 上的 `pymol-open-source` 的 **Windows 轮子没有打包依赖 DLL**（freetype / glew / libpng / libnetcdf 等），
安装后 `import pymol` 会报 `DLL load failed while importing _cmd`。
因此这里改用 [cgohlke/pymol-open-source-wheels](https://github.com/cgohlke/pymol-open-source-wheels)
提供的完整 Windows wheel（自带全部依赖）：

```toml
[tool.uv.sources]
pymol = { url = "https://github.com/cgohlke/pymol-open-source-wheels/releases/download/v2026.4.5/pymol-3.2.0a0-cp312-cp312-win_amd64.whl" }
```

> 该 URL 对应 **Python 3.12 / Windows x64**。换 Python 版本或平台时，去 releases 页面选对应的
> `cpXY` / `win_amd64` 文件即可。

## 编码注意

PyMOL 读取 `.pml` 脚本时使用**系统编码**（简体中文 Windows 为 GBK），
所以脚本里**不要写中文注释**，否则会 `UnicodeDecodeError`。
确实需要中文时，用 UTF-8 模式运行：

```bash
PYTHONUTF8=1 uv run pymol xxx.pml
```

`.py` 文件默认按 UTF-8 读取，不受影响。

## 界面说明

- PyMOL 开源版使用 **GLUT / Tk** 界面（没有 Qt 界面），启动日志里的
  `Qt not available`、`freeglut ... CreateDC failed` 均为无害提示，可忽略。
- 窗口是**独立桌面窗口**，不会嵌入 VS Code；需在**本机（有桌面 / 显卡）**运行。
  WSL / SSH / 远程容器下看不到界面，只能无界面出图。

## 环境

- Python 3.12
- pymol 3.2.0a0（cgohlke Windows wheel）
