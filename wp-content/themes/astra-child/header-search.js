(function () {
  function norm(s) {
    return (s || "").trim();
  }

  function pathKey() {
    var p = location.pathname || "/";
    if (p.length > 1 && p.charAt(p.length - 1) === "/") {
      p = p.slice(0, -1);
    }
    return p || "/";
  }

  function onSlotsOrProviderListing() {
    var p = pathKey();
    if (p === "/slots") return true;
    if (/^\/slots\/page\/\d+$/.test(p)) return true;
    if (/^\/providers\/[^/]+$/.test(p)) return true;
    return false;
  }

  function init() {
    var form = document.querySelector("#header-search form.hfe-search-button-wrapper");
    if (!form || form.getAttribute("data-static-header-search") === "1") return;
    form.setAttribute("data-static-header-search", "1");

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var inp = form.querySelector('input[name="s"]');
      var q = norm(inp ? inp.value : "");

      var grid = document.querySelector(
        ".elementor-widget-loop-grid .elementor-loop-container"
      );
      var aspInp =
        document.querySelector('#ajaxsearchpro1_1 input.orig[type="search"]') ||
        document.querySelector("#ajaxsearchpro1_1 input.orig") ||
        document.querySelector(".asp_w_container .ajaxsearchpro.asp_main_container input.orig");

      if (grid && aspInp && onSlotsOrProviderListing()) {
        aspInp.value = q;
        aspInp.dispatchEvent(new Event("input", { bubbles: true }));
        try {
          var u = new URL(location.href);
          if (q) {
            u.searchParams.set("s", q);
          } else {
            u.searchParams.delete("s");
          }
          history.replaceState({}, "", u.pathname + u.search + u.hash);
        } catch (err) {
          /* ignore */
        }
        return;
      }

      var dest = "/slots/";
      if (q) {
        dest += "?s=" + encodeURIComponent(q);
      }
      window.location.assign(dest);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
