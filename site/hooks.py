"""MkDocs 构建后置处理（hooks）。

目前只做一件事：**搜索索引改为按需加载**。

Material 的 bundle 在页面初始化时就把 `search/search_index.json` 接上：
`zi = document.forms.namedItem("search") ? ks() : tt` —— `ks()` 返回的 Observable
一经订阅立即发请求，而这个站点的索引是 36 MB（gzip 后约 7.9 MB），手机上一个页面
光等它就得好几秒。这里把该表达式换成「先给一个 Subject，等用户真的要用搜索
（悬停/点按/聚焦搜索框、按 / 或 ⌘K、或 URL 带 ?h= 高亮参数）才真正请求」。

找不到目标片段时不做任何改动，只打印告警——material 升级后需要重新确认。
"""

import glob
import os
import re

# zi = document.forms.namedItem("search") ? ks() : tt
_CALL_SITE = re.compile(
    r'(?P<var>[A-Za-z_$][\w$]*)=document\.forms\.namedItem\("search"\)\?ks\(\):(?P<empty>[A-Za-z_$][\w$]*)'
)

_LAZY = (
    "{var}=(function(){{"
    'if(!document.forms.namedItem("search"))return {empty};'  # 没有搜索框：保持原样
    "var _s=new T,_r=!1,"  # T = RxJS Subject（bundle 同作用域内已有）
    "_g=function(){{if(_r)return;_r=!0,"
    'document.removeEventListener("focusin",_g,!0),'
    'document.removeEventListener("pointerdown",_g,!0),'
    'document.removeEventListener("pointerenter",_g,!0),'
    'document.removeEventListener("keydown",_g,!0),'
    "ks().subscribe(function(v){{_s.next(v)}})"
    "}};"
    "return"
    ' document.addEventListener("focusin",_g,!0),'
    ' document.addEventListener("pointerdown",_g,!0),'
    ' document.addEventListener("pointerenter",_g,!0),'
    ' document.addEventListener("keydown",_g,!0),'
    " /([?&])h=/.test(location.search)&&_g(),"  # 来自搜索结果的高亮参数：立即加载
    "_s"
    "}})()"
)


def _patch_bundle(site_dir: str) -> None:
    paths = glob.glob(os.path.join(site_dir, "assets", "javascripts", "bundle.*.js"))
    paths = [p for p in paths if not p.endswith(".map")]
    if not paths:
        print("[hooks] 未找到 bundle.*.js，跳过搜索索引延迟处理")
        return
    for path in paths:
        with open(path, encoding="utf-8") as fh:
            js = fh.read()
        m = _CALL_SITE.search(js)
        if not m:
            print(f"[hooks] 警告：{os.path.basename(path)} 中未找到搜索索引调用点，未改动")
            continue
        js = js[: m.start()] + _LAZY.format(**m.groupdict()) + js[m.end():]
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(js)
        print(f"[hooks] 搜索索引已改为按需加载：{os.path.basename(path)}")


def on_post_build(config, **kwargs):
    _patch_bundle(config["site_dir"])
