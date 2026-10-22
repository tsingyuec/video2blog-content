/* 左侧栏：文件 / 大纲 切换 + 可拖动的分界线
   - 文件：显示 /content 的目录树
   - 大纲：显示当前页的标题大纲（从右侧 md-nav--secondary 克隆而来）
   - 分界线：可左右拖动调整左栏宽度。宽度直接写进 .md-sidebar--primary 的**行内样式**
     （不依赖任何样式表规则，因此一定能生效），并按位移量计算；宽度存 localStorage，
     全站共享、双击复位；窄屏（抽屉）下自动交回 Material 的默认宽度。 */
(function () {
  var KEY = "np-sidebar-w";
  var MIN = 150; /* px */
  var MAX = 560; /* px */
  var DESKTOP = window.matchMedia("(min-width: 76.25em)");

  function primary() {
    return document.querySelector(".md-sidebar--primary");
  }

  /* ---------- 左栏宽度 ---------- */
  function saveWidth(px) {
    try {
      if (px == null) localStorage.removeItem(KEY);
      else localStorage.setItem(KEY, String(px));
    } catch (e) {}
  }

  function savedWidth() {
    var v = NaN;
    try {
      v = parseInt(localStorage.getItem(KEY), 10);
    } catch (e) {}
    return isFinite(v) ? v : null;
  }

  function applyWidth(px, persist) {
    var el = primary();
    if (!el) return null;
    if (px == null || !isFinite(px) || !DESKTOP.matches) {
      el.style.removeProperty("width");
      if (persist) saveWidth(null);
      return null;
    }
    px = Math.round(Math.max(MIN, Math.min(MAX, px)));
    el.style.width = px + "px";
    if (persist) saveWidth(px);
    return px;
  }

  function currentWidth() {
    var el = primary();
    if (!el) return null;
    var w = parseFloat(el.style.width);
    return isFinite(w) ? w : el.getBoundingClientRect().width;
  }

  function restoreWidth() {
    applyWidth(savedWidth(), false);
  }

  /* ---------- 文件 / 大纲 切换 ---------- */
  function currentMode() {
    return document.documentElement.getAttribute("data-np-mode") || "file";
  }

  function setMode(m) {
    document.documentElement.setAttribute("data-np-mode", m);
    var tabs = document.querySelectorAll(".np-toolbar .np-tab");
    for (var i = 0; i < tabs.length; i++) {
      tabs[i].classList.toggle("np-tab--active", tabs[i].getAttribute("data-np") === m);
    }
  }

  /* ---------- 分界线 ---------- */
  function mountSplitter() {
    var content = document.querySelector(".md-content");
    if (!content || !content.parentNode || !primary()) return;

    var prev = content.previousElementSibling;
    if (prev && prev.classList.contains("np-splitter")) return; /* 已挂载 */

    var bar = document.createElement("div");
    bar.className = "np-splitter";
    bar.setAttribute("role", "separator");
    bar.setAttribute("aria-orientation", "vertical");
    bar.setAttribute("aria-label", "拖动调整左侧目录宽度（双击复位）");
    bar.title = "拖动调整左侧目录宽度（双击复位）";
    content.parentNode.insertBefore(bar, content);

    bar.addEventListener("mousedown", function (e) {
      if (e.button !== 0) return;
      var startX = e.clientX;
      var startW = currentWidth();
      if (startW == null) return;
      bar.classList.add("np-splitter--drag");
      document.body.classList.add("np-resizing");
      e.preventDefault();

      function onMove(ev) {
        applyWidth(startW + (ev.clientX - startX), false);
      }
      function onUp() {
        bar.classList.remove("np-splitter--drag");
        document.body.classList.remove("np-resizing");
        document.removeEventListener("mousemove", onMove);
        document.removeEventListener("mouseup", onUp);
        var el = primary();
        var w = el ? parseFloat(el.style.width) : NaN;
        saveWidth(isFinite(w) ? w : null);
      }
      document.addEventListener("mousemove", onMove);
      document.addEventListener("mouseup", onUp);
    });

    bar.addEventListener("dblclick", function () {
      applyWidth(null, true);
    });
  }

  /* ---------- 装配 ---------- */
  function inject() {
    var nav = document.querySelector(".md-sidebar--primary .md-nav--primary");
    if (!nav) return;

    var old = nav.querySelector(".np-toolbar");
    if (old) old.remove();
    var oldOutline = nav.querySelector(".np-outline");
    if (oldOutline) oldOutline.remove();

    var bar = document.createElement("div");
    bar.className = "np-toolbar";
    bar.innerHTML =
      '<span class="np-tab" data-np="file">文件</span>' +
      '<span class="np-tab" data-np="outline">大纲</span>';

    /* 克隆当前页大纲（右侧栏里的 md-nav--secondary） */
    var outline = document.createElement("div");
    outline.className = "np-outline";
    var toc = document.querySelector(".md-sidebar--secondary .md-nav--secondary");
    if (toc) {
      var list = toc.querySelector(".md-nav__list");
      if (list) outline.appendChild(list.cloneNode(true));
    }
    if (!outline.firstChild) {
      outline.innerHTML = '<div class="np-outline__empty">本页无大纲</div>';
    }

    nav.insertBefore(outline, nav.firstChild);
    nav.insertBefore(bar, nav.firstChild);

    bar.addEventListener("click", function (e) {
      var t = e.target.closest ? e.target.closest(".np-tab") : null;
      if (t) setMode(t.getAttribute("data-np"));
    });

    setMode(currentMode());
    mountSplitter();
    restoreWidth();
  }

  function boot() {
    restoreWidth();
    window.addEventListener("resize", restoreWidth);
    if (DESKTOP.addEventListener) DESKTOP.addEventListener("change", restoreWidth);
    if (window.document$ && typeof window.document$.subscribe === "function") {
      window.document$.subscribe(inject);
    } else {
      document.addEventListener("DOMContentLoaded", inject);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();

/* 时间戳就地播放
   正文里指向 YouTube / Bilibili 的时间戳（00:03:25、【跳转到 00:28】）
   左键点击时，在页面右侧打开播放窗口并从该时间开始，不离开当前文章。
   Ctrl / ⌘ / Shift / 中键仍按浏览器默认方式打开链接。同一 YouTube 视频
   再次点击只跳进度；换视频或 Bilibili 分 P 则切换播放地址。 */
(function () {
  var WIDTH_KEY = "np-player-w";
  var WIDTH_DEFAULT = 420;
  var WIDTH_MIN = 280;
  var WIDTH_MAX = 760;
  var DESKTOP = window.matchMedia("(min-width: 76.25em)");

  var player = null;
  var marked = null;
  var current = { key: "", sec: -1, kind: "", raw: "" };

  function parseClock(raw) {
    if (raw == null) return 0;
    var s = String(raw).trim().toLowerCase();
    if (!s) return 0;
    if (/^\d+$/.test(s)) return parseInt(s, 10);
    var hms = s.match(/^(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?$/);
    if (hms && (hms[1] || hms[2] || hms[3])) {
      return (parseInt(hms[1] || "0", 10) * 3600) +
        (parseInt(hms[2] || "0", 10) * 60) +
        parseInt(hms[3] || "0", 10);
    }
    var parts = s.split(":");
    if (parts.length === 2 || parts.length === 3) {
      var nums = [];
      var i;
      for (i = 0; i < parts.length; i++) {
        if (!/^\d+$/.test(parts[i])) return 0;
        nums.push(parseInt(parts[i], 10));
      }
      if (nums.length === 3) return nums[0] * 3600 + nums[1] * 60 + nums[2];
      return nums[0] * 60 + nums[1];
    }
    return 0;
  }

  function formatClock(sec) {
    sec = Math.max(0, parseInt(sec, 10) || 0);
    var h = Math.floor(sec / 3600);
    var m = Math.floor((sec % 3600) / 60);
    var s = sec % 60;
    function z(n) { return (n < 10 ? "0" : "") + n; }
    return z(h) + ":" + z(m) + ":" + z(s);
  }

  function timeOf(url, linkText) {
    var keys = ["t", "start"];
    var i;
    for (i = 0; i < keys.length; i++) {
      if (url.searchParams.has(keys[i])) return parseClock(url.searchParams.get(keys[i]));
    }
    var hm = (url.hash || "").match(/(?:^#|[?&#])t=([^&#]+)/);
    if (hm) return parseClock(decodeURIComponent(hm[1]));
    var tm = String(linkText || "").match(/(\d{1,2}:\d{2}(?::\d{2})?)/);
    if (tm) return parseClock(tm[1]);
    return 0;
  }

  function youtubeId(url) {
    var host = url.hostname.toLowerCase().replace(/^www\./, "");
    if (host === "youtu.be") {
      return (url.pathname.split("/").filter(Boolean)[0] || "").split("?")[0];
    }
    if (host !== "youtube.com" && host !== "youtube-nocookie.com" && host !== "m.youtube.com") {
      return "";
    }
    if (url.pathname === "/watch" || url.pathname === "/watch/") {
      return url.searchParams.get("v") || "";
    }
    var parts = url.pathname.split("/").filter(Boolean);
    if (parts.length >= 2 && (parts[0] === "embed" || parts[0] === "shorts" || parts[0] === "live" || parts[0] === "v")) {
      return parts[1];
    }
    return "";
  }

  function youtubeEmbed(id, sec) {
    var q = [
      "start=" + String(sec || 0),
      "autoplay=1",
      "enablejsapi=1",
      "rel=0"
    ];
    try {
      if (location.protocol === "http:" || location.protocol === "https:") {
        q.push("origin=" + encodeURIComponent(location.origin));
      }
    } catch (err) {}
    return "https://www.youtube.com/embed/" + encodeURIComponent(id) + "?" + q.join("&");
  }

  function bilibiliEmbed(bv, aid, page, sec) {
    var q = [
      "isOutside=true",
      "autoplay=1",
      "high_quality=1",
      "danmaku=0",
      "p=" + String(page || 1),
      "t=" + String(sec || 0)
    ];
    if (bv) q.push("bvid=" + encodeURIComponent(bv));
    if (aid) q.push("aid=" + encodeURIComponent(String(aid)));
    return "https://player.bilibili.com/player.html?" + q.join("&");
  }

  /* 仅拦截「看起来就是时间戳」的视频链接，索引里的整集链接仍走原站。 */
  function isTimestampLink(a) {
    var text = (a.textContent || "").replace(/\s+/g, " ").trim();
    if (/^\d{1,2}:\d{2}(:\d{2})?$/.test(text)) return true;
    if (/跳转[到至]?\s*\d{1,2}:\d{2}(:\d{2})?/.test(text)) return true;
    return false;
  }

  function parseVideoUrl(href, linkText) {
    var url;
    try {
      url = new URL(href, window.location.href);
    } catch (err) {
      return null;
    }
    var sec = timeOf(url, linkText);
    var yid = youtubeId(url);
    if (yid && /^[\w-]{6,}$/.test(yid)) {
      return {
        kind: "youtube",
        key: "yt:" + yid,
        sec: sec,
        rawUrl: href,
        embed: youtubeEmbed(yid, sec)
      };
    }
    var host = url.hostname.toLowerCase().replace(/^www\./, "").replace(/^m\./, "");
    if (host !== "bilibili.com") return null;
    var bv = "";
    var aid = "";
    var bm = url.pathname.match(/\/video\/(BV[0-9A-Za-z]+)/i);
    if (bm) bv = bm[1];
    var am = url.pathname.match(/\/video\/av(\d+)/i);
    if (am) aid = am[1];
    if (!bv && !aid) return null;
    var page = parseInt(url.searchParams.get("p") || url.searchParams.get("page") || "1", 10);
    if (!isFinite(page) || page < 1) page = 1;
    return {
      kind: "bilibili",
      key: "bi:" + (bv || ("av" + aid)) + ":p" + page,
      sec: sec,
      rawUrl: href,
      embed: bilibiliEmbed(bv, aid, page, sec)
    };
  }

  function setPlayerWidth(px, persist) {
    var reset = px == null || !isFinite(px);
    if (reset) px = WIDTH_DEFAULT;
    px = Math.round(Math.max(WIDTH_MIN, Math.min(WIDTH_MAX, px)));
    document.documentElement.style.setProperty("--np-player-w", px + "px");
    if (!persist) return;
    try {
      if (reset) localStorage.removeItem(WIDTH_KEY);
      else localStorage.setItem(WIDTH_KEY, String(px));
    } catch (err) {}
  }

  function restorePlayerWidth() {
    var v = NaN;
    try { v = parseInt(localStorage.getItem(WIDTH_KEY), 10); } catch (err) {}
    setPlayerWidth(isFinite(v) ? v : WIDTH_DEFAULT, false);
  }

  function placeTop() {
    if (!player) return;
    var dock = DESKTOP.matches &&
      document.body.classList.contains("np-player-open") &&
      !document.body.classList.contains("np-player-collapsed");
    if (!dock) {
      player.root.style.top = "";
      return;
    }
    var header = document.querySelector(".md-header");
    var h = header ? Math.round(header.getBoundingClientRect().height) : 48;
    player.root.style.top = (h + 10) + "px";
  }

  function mark(a) {
    if (marked && marked !== a) marked.classList.remove("np-ts-on");
    marked = a || null;
    if (marked) marked.classList.add("np-ts-on");
  }

  function ytCmd(iframe, func, args) {
    if (!iframe || !iframe.contentWindow) return;
    iframe.contentWindow.postMessage(JSON.stringify({
      event: "command",
      func: func,
      args: args || []
    }), "*");
  }

  function setCollapsed(collapsed) {
    document.body.classList.toggle("np-player-collapsed", collapsed);
    player.collapseBtn.textContent = collapsed ? "展开" : "收起";
    player.collapseBtn.title = collapsed ? "展开播放窗口" : "收起播放窗口";
    player.collapseBtn.setAttribute("aria-expanded", collapsed ? "false" : "true");
    placeTop();
  }

  function openRaw() {
    if (!current.raw) return;
    try {
      var u = new URL(current.raw, window.location.href);
      if (u.protocol !== "http:" && u.protocol !== "https:") return;
      window.open(u.href, "_blank", "noopener,noreferrer");
    } catch (err) {}
  }

  function closePlayer() {
    if (!player) return;
    player.iframe.removeAttribute("data-yt-ready");
    player.iframe.setAttribute("data-embed", "");
    player.iframe.src = "about:blank";
    current.key = "";
    current.sec = -1;
    current.kind = "";
    current.raw = "";
    document.body.classList.remove("np-player-open");
    document.body.classList.remove("np-player-collapsed");
    player.root.setAttribute("hidden", "");
    player.root.style.top = "";
    mark(null);
  }

  function ensure() {
    if (player) return player;
    var root = document.createElement("aside");
    root.className = "np-player";
    root.setAttribute("hidden", "");
    root.setAttribute("aria-label", "视频播放");
    root.innerHTML =
      '<div class="np-player__resize" role="separator" aria-orientation="vertical" aria-label="拖动调整播放器宽度，双击复位" title="拖动调整宽度，双击复位"></div>' +
      '<div class="np-player__bar">' +
        '<span class="np-player__time">00:00:00</span>' +
        '<span class="np-player__kind"></span>' +
        '<span class="np-player__gap"></span>' +
        '<button type="button" class="np-player__btn" data-np-act="open" title="在原站打开">原站</button>' +
        '<button type="button" class="np-player__btn" data-np-act="collapse" title="收起播放窗口" aria-expanded="true">收起</button>' +
        '<button type="button" class="np-player__btn" data-np-act="close" title="关闭播放窗口">关闭</button>' +
      "</div>" +
      '<div class="np-player__stage">' +
        '<iframe title="视频播放" allow="autoplay; fullscreen; picture-in-picture; encrypted-media" allowfullscreen referrerpolicy="strict-origin-when-cross-origin"></iframe>' +
      "</div>";
    document.body.appendChild(root);
    player = {
      root: root,
      time: root.querySelector(".np-player__time"),
      kind: root.querySelector(".np-player__kind"),
      collapseBtn: root.querySelector("[data-np-act='collapse']"),
      iframe: root.querySelector("iframe"),
      resize: root.querySelector(".np-player__resize")
    };

    root.addEventListener("click", function (e) {
      var btn = e.target && e.target.closest ? e.target.closest("[data-np-act]") : null;
      if (!btn) return;
      var act = btn.getAttribute("data-np-act");
      if (act === "close") closePlayer();
      else if (act === "collapse") setCollapsed(!document.body.classList.contains("np-player-collapsed"));
      else if (act === "open") openRaw();
    });

    player.iframe.addEventListener("load", function () {
      if (current.kind !== "youtube") return;
      var src = player.iframe.getAttribute("data-embed") || "";
      if (src.indexOf("youtube.com/embed/") === -1) return;
      try {
        player.iframe.contentWindow.postMessage(JSON.stringify({
          event: "listening",
          id: "np-player"
        }), "*");
      } catch (err) {}
    });

    player.resize.addEventListener("mousedown", function (e) {
      if (e.button !== 0 || !DESKTOP.matches) return;
      if (document.body.classList.contains("np-player-collapsed")) return;
      var rightEdge = player.root.getBoundingClientRect().right;
      player.resize.classList.add("np-player__resize--drag");
      document.body.classList.add("np-player-drag");
      e.preventDefault();
      function onMove(ev) {
        var px = rightEdge - ev.clientX;
        var max = Math.min(WIDTH_MAX, window.innerWidth - 240);
        if (px > max) px = max;
        setPlayerWidth(px, false);
      }
      function onUp() {
        player.resize.classList.remove("np-player__resize--drag");
        document.body.classList.remove("np-player-drag");
        document.removeEventListener("mousemove", onMove);
        document.removeEventListener("mouseup", onUp);
        var cur = parseFloat(getComputedStyle(document.documentElement).getPropertyValue("--np-player-w"));
        if (isFinite(cur)) setPlayerWidth(cur, true);
      }
      document.addEventListener("mousemove", onMove);
      document.addEventListener("mouseup", onUp);
    });

    player.resize.addEventListener("dblclick", function () {
      setPlayerWidth(null, true);
    });

    return player;
  }

  function showVideo(info, anchor) {
    var ui = ensure();
    document.body.classList.add("np-player-open");
    ui.root.removeAttribute("hidden");
    setCollapsed(false);
    mark(anchor);
    ui.time.textContent = formatClock(info.sec);
    ui.kind.textContent = info.kind === "youtube" ? "YouTube" : "哔哩哔哩";
    ui.iframe.title = (info.kind === "youtube" ? "YouTube " : "哔哩哔哩 ") + formatClock(info.sec);

    var srcNow = ui.iframe.getAttribute("data-embed") || "";
    var sameVideo = current.key === info.key && srcNow.indexOf("http") === 0;
    if (info.kind === "youtube" && sameVideo && ui.iframe.getAttribute("data-yt-ready") === "1") {
      current.sec = info.sec;
      current.kind = info.kind;
      current.raw = info.rawUrl;
      ytCmd(ui.iframe, "seekTo", [info.sec, true]);
      ytCmd(ui.iframe, "playVideo", []);
      return;
    }
    if (sameVideo && current.sec === info.sec && srcNow === info.embed) {
      current.raw = info.rawUrl;
      return;
    }
    current.key = info.key;
    current.sec = info.sec;
    current.kind = info.kind;
    current.raw = info.rawUrl;
    ui.iframe.removeAttribute("data-yt-ready");
    ui.iframe.setAttribute("data-embed", info.embed);
    ui.iframe.src = info.embed;
  }

  function tagLinks() {
    var root = document.querySelector(".md-content");
    if (!root) return;
    var links = root.querySelectorAll("a[href]");
    var again = null;
    var i;
    for (i = 0; i < links.length; i++) {
      var a = links[i];
      if (!isTimestampLink(a)) continue;
      var info = parseVideoUrl(a.href, a.textContent || "");
      if (!info) continue;
      a.classList.add("np-ts-link");
      a.setAttribute("title", "在页面右侧播放（Ctrl 或 ⌘ 点击则在新标签页打开）");
      if (!again && current.key && info.key === current.key && info.sec === current.sec) again = a;
    }
    if (again) mark(again);
  }

  function onClick(e) {
    if (e.defaultPrevented || e.button !== 0) return;
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    var node = e.target;
    if (!node) return;
    if (node.nodeType === 3) node = node.parentNode;
    if (!node || !node.closest) return;
    var a = node.closest("a[href]");
    if (!a || (a.closest && a.closest(".np-player"))) return;
    if (a.hasAttribute("download")) return;
    if (!isTimestampLink(a)) return;
    var info = parseVideoUrl(a.href, a.textContent || "");
    if (!info) return;
    e.preventDefault();
    e.stopPropagation();
    showVideo(info, a);
  }

  function onKey(e) {
    if (e.key !== "Escape") return;
    if (!document.body.classList.contains("np-player-open")) return;
    var t = e.target;
    if (t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.isContentEditable)) return;
    closePlayer();
  }

  function onMessage(ev) {
    if (!player || !player.iframe.contentWindow) return;
    if (ev.source !== player.iframe.contentWindow) return;
    if (!ev.origin || ev.origin.indexOf("youtube.com") === -1) return;
    var data = ev.data;
    if (typeof data === "string") {
      try { data = JSON.parse(data); } catch (err) { return; }
    }
    if (!data || data.event !== "onReady") return;
    player.iframe.setAttribute("data-yt-ready", "1");
  }

  function boot() {
    restorePlayerWidth();
    document.addEventListener("click", onClick, true);
    document.addEventListener("keydown", onKey);
    window.addEventListener("message", onMessage);
    window.addEventListener("resize", placeTop);
    if (DESKTOP.addEventListener) DESKTOP.addEventListener("change", placeTop);
    tagLinks();
    if (window.document$ && typeof window.document$.subscribe === "function") {
      window.document$.subscribe(tagLinks);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
