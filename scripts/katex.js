/* 把 pymdownx.arithmatex（generic）产出的 \( \) / \[ \] 交给 KaTeX。
   navigation.instant 换页后 document$ 会再触发，需要重新排版。 */
(function () {
  function typeset(ctx) {
    if (typeof renderMathInElement !== "function") return;
    var root = document.body;
    if (ctx && ctx.body) root = ctx.body;
    renderMathInElement(root, {
      delimiters: [
        { left: "\\(", right: "\\)", display: false },
        { left: "\\[", right: "\\]", display: true }
      ],
      throwOnError: false,
      ignoredTags: ["script", "noscript", "style", "textarea", "pre", "code"]
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
