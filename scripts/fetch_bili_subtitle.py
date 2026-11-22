#!/usr/bin/env python3
"""用 B 站官方字幕接口抓取字幕，产出 ``subs/<BV>.srt``。

**为什么需要这个脚本**：video2blog skill 的 ``subtitle_fetch.py`` 里 B 站走的是
kedou.life 第三方服务，该服务有每日次数上限（超限返回
``code:500 您今日的使用次数已达上限``），且**不读 cookie**，额度耗尽后无法绕过。
本脚本改走 B 站官方接口，凭登录态 cookie 取字幕轨（含 ``ai-zh`` AI 字幕），
没有第三方额度限制，是 kedou 的等价替代。

字幕轨来源：``/x/player/wbi/v2`` 返回的 ``data.subtitle.subtitles``。注意：

- **必须带登录态 cookie**，否则该数组恒为空（未登录看不到字幕轨）。
- 视频本身没有字幕轨时数组也为空——这与「接口失败」是两件事，脚本会分别报错。
- 多 P 视频默认取第 1 P，可用 ``--p`` 指定。

用法::

    python3 scripts/fetch_bili_subtitle.py \
        --workdir "_work/<系列>/<小节>" --bv BV1xxxxxxxxx \
        --cookies .agents/bili-subtitle/cookies.txt

产出::

    <workdir>/subs/<BV>.srt          # 标准 SRT，供 build_transcript.py 直接消费
    <workdir>/subs/bili_<BV>.json    # 原始接口响应，备查

退出码：0 = 成功；1 = 失败（无字幕轨 / 接口异常 / 无 cookie）。
"""

from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import sys
import urllib.error
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
VIEW_API = "https://api.bilibili.com/x/web-interface/view?bvid={bv}"
PLAYER_API = "https://api.bilibili.com/x/player/wbi/v2?aid={aid}&cid={cid}"
VIDEO_PAGE = "https://www.bilibili.com/video/{bv}/"

# 语言偏好：越靠前越优先。B 站目前常见 zh-CN / zh-Hans / ai-zh（AI 生成）。
LANG_PRIORITY = ("zh-Hans", "zh-CN", "zh-Hant", "ai-zh")


def load_cookies(path: str) -> str:
    """读取 Netscape cookies.txt，返回可直接放进 Cookie 头的字符串。"""
    if not path or not os.path.isfile(os.path.expanduser(path)):
        raise SystemExit(f"cookie 文件不存在: {path}")
    jar = http.cookiejar.MozillaCookieJar(os.path.expanduser(path))
    jar.load(ignore_discard=True, ignore_expires=True)
    pairs = [f"{c.name}={c.value}" for c in jar if "bilibili" in c.domain]
    if not any(p.startswith("SESSDATA=") for p in pairs):
        raise SystemExit("cookie 里没有 SESSDATA，未登录态无法取字幕轨")
    return "; ".join(pairs)


def get_json(url: str, cookie_header: str, referer: str) -> dict:
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Referer": referer,
        "Cookie": cookie_header,
        "Accept": "application/json, text/plain, */*",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def pick_track(tracks: list[dict], want_lang: str) -> dict | None:
    """按语言偏好挑一条字幕轨；``want_lang`` 为空时按默认优先级。"""
    if not tracks:
        return None
    want = (want_lang or "").strip()
    if want:
        exact = [t for t in tracks if t.get("lan") == want]
        if exact:
            return exact[0]
        # zh-Hans / zh-CN / ai-zh 视为同一族，按前缀放宽
        prefix = want.split("-")[0]
        same_family = [t for t in tracks if (t.get("lan") or "").startswith(prefix)]
        if same_family:
            return same_family[0]
    for lang in LANG_PRIORITY:
        hit = [t for t in tracks if t.get("lan") == lang]
        if hit:
            return hit[0]
    return tracks[0]


def to_srt(items: list[dict]) -> str:
    """把 B 站字幕 JSON 的 body 转成标准 SRT。"""
    def stamp(sec: float) -> str:
        ms = int(round(sec * 1000))
        h, ms = divmod(ms, 3_600_000)
        m, ms = divmod(ms, 60_000)
        s, ms = divmod(ms, 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    blocks = []
    for i, it in enumerate(items, 1):
        text = (it.get("content") or "").strip()
        if not text:
            continue
        blocks.append(f"{i}\n{stamp(float(it['from']))} --> "
                      f"{stamp(float(it['to']))}\n{text}\n")
    return "\n".join(blocks)


def main() -> int:
    ap = argparse.ArgumentParser(description="用 B 站官方接口抓取字幕（kedou 的替代路径）")
    ap.add_argument("--workdir", required=True, help="工作目录，字幕写入 <workdir>/subs/")
    ap.add_argument("--bv", required=True, help="视频 BV 号，如 BV1xxxxxxxxx")
    ap.add_argument("--cookies", required=True, help="Netscape 格式 cookies.txt")
    ap.add_argument("--lang", default="", help="目标语言，如 zh-Hans / ai-zh；留空按默认优先级")
    ap.add_argument("--p", type=int, default=1, help="第几个分P（默认 1）")
    args = ap.parse_args()

    bv = args.bv.strip()
    referer = VIDEO_PAGE.format(bv=bv)
    cookie_header = load_cookies(args.cookies)

    try:
        view = get_json(VIEW_API.format(bv=bv), cookie_header, referer)
        if view.get("code") != 0:
            print(f"取视频信息失败: code={view.get('code')} {view.get('message')}")
            return 1
        data = view["data"]
        pages = data.get("pages") or []
        if not pages:
            print("该视频没有分P信息")
            return 1
        idx = min(max(args.p, 1), len(pages)) - 1
        aid = data["aid"]
        cid = pages[idx]["cid"]
        title = data.get("title", "")
        part = pages[idx].get("part", "")
        print(f"视频: {title}" + (f" / P{idx + 1} {part}" if len(pages) > 1 else ""))

        player = get_json(PLAYER_API.format(aid=aid, cid=cid), cookie_header, referer)
        if player.get("code") != 0:
            print(f"取播放信息失败: code={player.get('code')} {player.get('message')}")
            return 1
        tracks = ((player.get("data") or {}).get("subtitle") or {}).get("subtitles") or []
        if not tracks:
            print("该视频没有任何字幕轨（含 AI 字幕）。"
                  "这不是接口故障——B 站侧确实为空，请换候选视频。")
            return 1
        print("可用字幕轨: " + ", ".join(
            f"{t.get('lan')}({t.get('lan_doc')})" for t in tracks))

        track = pick_track(tracks, args.lang)
        url = track.get("subtitle_url") or ""
        if not url:
            print(f"选中的字幕轨没有 subtitle_url: {track.get('lan')}")
            return 1
        if url.startswith("//"):
            url = "https:" + url

        body = get_json(url, cookie_header, referer)
        items = body.get("body") or []
        if not items:
            print("字幕内容为空")
            return 1

        srt = to_srt(items)
        subs_dir = os.path.join(args.workdir, "subs")
        os.makedirs(subs_dir, exist_ok=True)
        srt_path = os.path.join(subs_dir, f"{bv}.srt")
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(srt)
        with open(os.path.join(subs_dir, f"bili_{bv}.json"), "w", encoding="utf-8") as f:
            json.dump({"track": track, "body": items}, f, ensure_ascii=False, indent=1)

        print(f"字幕轨: {track.get('lan')} | {len(items)} 条 | "
              f"{len(srt)} 字节 -> {srt_path}")
        return 0
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.reason}")
        return 1
    except urllib.error.URLError as e:
        print(f"网络错误: {e.reason}")
        return 1


if __name__ == "__main__":
    sys.exit(main())