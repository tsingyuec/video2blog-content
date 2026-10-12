/* 左侧栏顶部工具条：文件 / 大纲 切换
   - 文件：显示 /content 的目录树
   - 大纲：显示当前页的标题大纲（从右侧 md-nav--secondary 克隆而来） */
(function () {
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

    // 克隆当前页大纲（右侧栏里的 md-nav--secondary）
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
