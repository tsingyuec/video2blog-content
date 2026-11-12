/* 把 pymdownx.arithmatex（generic）产出的 \( \) / \[ \] 交给 KaTeX。
   navigation.instant 换页后 document$ 会再触发，需要重新排版。

   KaTeX 本体（katex.min.js 约 76 KB + auto-render 与字体）不再随每页无条件加载：
   本页没有公式就不下，有公式才按需注入脚本再排版。 */
(function () {
  var self = document.currentScript ||
    document.querySelector('script[src$="_static/katex.js"]');
  var base = self && self.src ? self.src.replace(/[^/]*$/, "") : "";
  var KATEX = base + "katex/katex.min.js";
  var AUTORENDER = base + "katex/contrib/auto-render.min.js";

  var loading = false;
  var ready = false;
  var pending = [];

  function load(cb) {
    if (ready) return cb();
    pending.push(cb);
    if (loading) return;
    loading = true;
    var s1 = document.createElement("script");
    s1.src = KATEX;
    s1.onload = function () {
      var s2 = document.createElement("script");
      s2.src = AUTORENDER;
      s2.onload = function () {
        ready = true;
        var queue = pending;
        pending = [];
        for (var i = 0; i < queue.length; i++) queue[i]();
      };
      s2.onerror = function () { loading = false; };
      document.head.appendChild(s2);
    };
    s1.onerror = function () { loading = false; };
    document.head.appendChild(s1);
  }

  function typeset(ctx) {
    var root = (ctx && ctx.body) || document.body;
    if (!root || !root.querySelector(".arithmatex")) return;
    load(function () {
      if (typeof renderMathInElement !== "function") return;
      renderMathInElement(root, {
        delimiters: [
          { left: "\\(", right: "\\)", display: false },
          { left: "\\[", right: "\\]", display: true }
        ],
        throwOnError: false,
        ignoredTags: ["script", "noscript", "style", "textarea", "pre", "code"]
      });
    });
  }

  if (window.document$ && typeof window.document$.subscribe === "function") {
    window.document$.subscribe(typeset);
  } else if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () { typeset(); });
  } else {
    typeset();
  }
})();
