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
