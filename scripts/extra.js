/* 左侧栏：文件 / 大纲 切换 + 可拖动的分界线
   - 文件：显示 /content 的目录树
   - 大纲：显示当前页的标题大纲（从右侧 md-nav--secondary 克隆而来）
   - 分界线：可左右拖动调整左栏宽度，宽度写入 localStorage，全站共享、双击复位 */
(function () {
  var KEY = "np-sidebar-w";
  var MIN = 150; /* px */
  var MAX = 560; /* px */

  function doc() {
    return document.documentElement;
  }

  /* ---------- 左栏宽度 ---------- */
  function applyWidth(px) {
    if (px == null || !isFinite(px)) {
      doc().style.removeProperty("--np-sidebar-w");
      return null;
    }
    px = Math.round(Math.max(MIN, Math.min(MAX, px)));
    doc().style.setProperty("--np-sidebar-w", px + "px");
    return px;
  }

  function restoreWidth() {
    var v = NaN;
    try {
      v = parseInt(localStorage.getItem(KEY), 10);
    } catch (e) {}
    if (isFinite(v)) applyWidth(v);
  }

  function saveWidth(px) {
    try {
      if (px == null) localStorage.removeItem(KEY);
      else localStorage.setItem(KEY, String(px));
    } catch (e) {}
  }

  function resetWidth() {
    applyWidth(null);
    saveWidth(null);
  }

  /* ---------- 文件 / 大纲 切换 ---------- */
  function currentMode() {
    return doc().getAttribute("data-np-mode") || "file";
  }

  function setMode(m) {
    doc().setAttribute("data-np-mode", m);
    var tabs = document.querySelectorAll(".np-toolbar .np-tab");
    for (var i = 0; i < tabs.length; i++) {
      tabs[i].classList.toggle("np-tab--active", tabs[i].getAttribute("data-np") === m);
    }
  }

  /* ---------- 分界线 ---------- */
  function mountSplitter() {
    var primary = document.querySelector(".md-sidebar--primary");
    var content = document.querySelector(".md-content");
    if (!primary || !content || !content.parentNode) return;

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
      var sidebar = document.querySelector(".md-sidebar--primary");
      if (!sidebar) return;
      var left = sidebar.getBoundingClientRect().left;
      var last = null;
      bar.classList.add("np-splitter--drag");
      document.body.classList.add("np-resizing");
      e.preventDefault();

      function onMove(ev) {
        last = applyWidth(ev.clientX - left);
      }
      function onUp() {
        bar.classList.remove("np-splitter--drag");
        document.body.classList.remove("np-resizing");
        document.removeEventListener("mousemove", onMove);
        document.removeEventListener("mouseup", onUp);
        if (last != null) saveWidth(last);
      }
      document.addEventListener("mousemove", onMove);
      document.addEventListener("mouseup", onUp);
    });

    bar.addEventListener("dblclick", resetWidth);
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
