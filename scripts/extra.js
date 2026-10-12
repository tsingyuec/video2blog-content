/* 左侧栏顶部工具条：搜索 / 深浅色 / 文件·大纲 切换 */
(function () {
  var SEARCH_SVG =
    '<svg viewBox="0 0 24 24" width="15" height="15" aria-hidden="true">' +
    '<path fill="currentColor" d="M15.5 14h-.79l-.28-.27a6.5 6.5 0 1 0-.7.7l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0A4.5 4.5 0 1 1 14 9.5 4.5 4.5 0 0 1 9.5 14z"/></svg>';
  var THEME_SVG =
    '<svg viewBox="0 0 24 24" width="15" height="15" aria-hidden="true">' +
    '<path fill="currentColor" d="M12 3a9 9 0 1 0 9 9 7 7 0 0 1-9-9z"/></svg>';

  function mode() {
    return document.documentElement.getAttribute("data-np-mode") || "file";
  }

  function setMode(m) {
    document.documentElement.setAttribute("data-np-mode", m);
    var tabs = document.querySelectorAll(".np-toolbar .np-tab");
    for (var i = 0; i < tabs.length; i++) {
      tabs[i].classList.toggle("np-tab--active", tabs[i].getAttribute("data-np") === m);
    }
  }

  function inject() {
    var nav = document.querySelector(".md-sidebar--primary .md-nav--primary");
    if (!nav) return;

    // 每次导航都重建，避免残留旧的克隆大纲
    var old = nav.querySelector(".np-toolbar");
    if (old) old.remove();
    var oldOutline = nav.querySelector(".np-outline");
    if (oldOutline) oldOutline.remove();

    var bar = document.createElement("div");
    bar.className = "np-toolbar";
    bar.innerHTML =
      '<label class="np-btn" for="__search" title="搜索">' + SEARCH_SVG + "</label>" +
      '<label class="np-btn" for="__palette_1" title="切换深浅色">' + THEME_SVG + "</label>" +
      '<span class="np-spacer"></span>' +
      '<span class="np-tab" data-np="file">文件</span>' +
      '<span class="np-tab" data-np="outline">大纲</span>';

    // 把「大纲」（md-nav--secondary）克隆一份，独立放在工具条下方
    var outline = document.createElement("div");
    outline.className = "np-outline";
    var toc = nav.querySelector(".md-nav--secondary");
    if (toc) {
      var list = toc.querySelector(".md-nav__list");
      if (list) outline.appendChild(list.cloneNode(true));
    } else {
      outline.innerHTML = '<div class="np-outline__empty">本页无大纲</div>';
    }

    nav.insertBefore(outline, nav.firstChild);
    nav.insertBefore(bar, nav.firstChild);

    bar.addEventListener("click", function (e) {
      var t = e.target.closest ? e.target.closest(".np-tab") : null;
      if (t) setMode(t.getAttribute("data-np"));
    });

    setMode(mode());
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
