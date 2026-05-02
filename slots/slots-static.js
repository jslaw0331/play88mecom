(function () {
  function init() {
    var grid = document.querySelector(".elementor-widget-loop-grid .elementor-loop-container");
    var asp =
      document.getElementById("ajaxsearchpro1_1") ||
      document.querySelector(".asp_w_container .ajaxsearchpro.asp_main_container");
    if (!grid || !asp) return;

    var aspRoot = asp.closest(".asp_w_container") || asp;
    var searchInput = asp.querySelector('input.orig[type="search"], input.orig');
    var settingsForm = aspRoot.querySelector(".asp_ss form.options, form.asp-fss-flex");
    var providerSelect =
      settingsForm && settingsForm.querySelector('select[name="termset[providers][]"]');

    function readInitialSearchQuery() {
      try {
        var u = new URL(window.location.href);
        return (u.searchParams.get("s") || "").trim();
      } catch (e) {
        return "";
      }
    }

    var initialSearch = readInitialSearchQuery();
    if (initialSearch && searchInput) {
      searchInput.value = initialSearch;
    }

    var stale = document.getElementById("slots-static-search-results");
    if (stale) stale.remove();

    var loopWidget = grid.closest(".elementor-widget-loop-grid");

    function ensureEmptyStateEl() {
      var el = document.getElementById("slots-static-empty-state");
      if (el) return el;
      el = document.createElement("div");
      el.id = "slots-static-empty-state";
      el.className = "slots-static-empty-state";
      el.hidden = true;
      el.setAttribute("role", "status");
      grid.parentNode.insertBefore(el, grid.nextSibling);
      return el;
    }

    function norm(s) {
      return (s || "").toLowerCase().trim();
    }

    function providerLabelToSlug() {
      var map = Object.create(null);
      document.querySelectorAll(".providers-list a[href*='/providers/']").forEach(function (a) {
        var m = a.pathname.match(/\/providers\/([^/]+)\/?/);
        if (!m) return;
        var slug = m[1];
        var span = a.querySelector("span");
        var label = span ? span.textContent : a.textContent;
        if (label) map[norm(label)] = slug;
      });
      return map;
    }

    var labelToSlug = providerLabelToSlug();

    function selectedProviderSlugs() {
      if (!providerSelect) return [];
      var out = [];
      var opts = providerSelect.querySelectorAll("option:checked");
      for (var i = 0; i < opts.length; i++) {
        var txt = norm(opts[i].textContent);
        var slug = labelToSlug[txt] || null;
        if (slug) out.push(slug);
      }
      return out;
    }

    function providerSlugFromPath() {
      var m = location.pathname.match(/\/providers\/([^/]+)(?:\/|$|\?|#)/);
      return m ? m[1] : null;
    }

    function providerSlugFromNav() {
      var cur = document.querySelector('.providers-list li.current-term a[href*="/providers/"]');
      if (!cur) return null;
      var m = cur.pathname.match(/\/providers\/([^/]+)/);
      return m ? m[1] : null;
    }

    function effectiveProviderSlugs() {
      var fromSelect = selectedProviderSlugs();
      if (fromSelect.length) return fromSelect;
      var fromPath = providerSlugFromPath();
      if (fromPath) return [fromPath];
      var fromNav = providerSlugFromNav();
      if (fromNav) return [fromNav];
      return [];
    }

    function getSearchQuery() {
      var inp = asp.querySelector('input.orig[type="search"], input.orig');
      return norm(inp ? inp.value : "");
    }

    function getLoopCards() {
      var out = [];
      var ch = grid.children;
      for (var i = 0; i < ch.length; i++) {
        var el = ch[i];
        if (el.classList && el.classList.contains("e-loop-item")) out.push(el);
      }
      return out;
    }

    function cardProviderSlug(card) {
      var m = card.className.match(/providers-([a-z0-9-]+)/);
      return m ? m[1] : "";
    }

    function applyGridFilter() {
      try {
        var q = getSearchQuery();
        var provs = effectiveProviderSlugs();
        var cards = getLoopCards();
        var emptyEl = ensureEmptyStateEl();
        var pathSlug = providerSlugFromPath();

        var catalogMissingProvider =
          provs.length === 1 &&
          pathSlug &&
          provs[0] === pathSlug &&
          !cards.some(function (c) {
            return cardProviderSlug(c) === provs[0];
          });

        if (catalogMissingProvider) {
          if (loopWidget) loopWidget.classList.add("slots-static-hide-loop");
          emptyEl.hidden = false;
          emptyEl.textContent = "No games found for this provider.";
          for (var h = 0; h < cards.length; h++) {
            cards[h].classList.add("slots-static-hidden");
          }
          return;
        }

        if (loopWidget) loopWidget.classList.remove("slots-static-hide-loop");
        emptyEl.hidden = true;

        for (var i = 0; i < cards.length; i++) {
          var card = cards[i];
          var titleEl = card.querySelector(".elementor-heading-title a, h2 a");
          var title = titleEl ? titleEl.textContent : "";
          var okQ = !q || norm(title).indexOf(q) !== -1;
          var cslug = cardProviderSlug(card);
          var okP = provs.length === 0 || provs.indexOf(cslug) !== -1;
          card.classList.toggle("slots-static-hidden", !(okQ && okP));
        }

        var visible = 0;
        for (var v = 0; v < cards.length; v++) {
          if (!cards[v].classList.contains("slots-static-hidden")) visible++;
        }
        if (visible === 0 && cards.length > 0) {
          var hasActiveFilter = q.length > 0 || provs.length > 0;
          if (!hasActiveFilter) {
            for (var r = 0; r < cards.length; r++) {
              cards[r].classList.remove("slots-static-hidden");
            }
            if (loopWidget) loopWidget.classList.remove("slots-static-hide-loop");
            emptyEl.hidden = true;
          } else {
            if (loopWidget) loopWidget.classList.add("slots-static-hide-loop");
            emptyEl.hidden = false;
            emptyEl.textContent = q
              ? "No games match your search."
              : "No games found.";
          }
        }
      } catch (e) {
        console.warn("slots-static: applyGridFilter", e);
      }
    }

    function refresh() {
      applyGridFilter();
    }

    var debounce;
    function debouncedRefresh() {
      clearTimeout(debounce);
      debounce = setTimeout(refresh, 200);
    }

    asp.addEventListener(
      "input",
      function (e) {
        if (e.target && e.target.classList && e.target.classList.contains("orig")) {
          debouncedRefresh();
        }
      },
      true
    );

    if (searchInput) {
      searchInput.addEventListener("input", debouncedRefresh);
      searchInput.addEventListener(
        "keydown",
        function (e) {
          if (e.key === "Enter") {
            e.preventDefault();
            e.stopPropagation();
            refresh();
          }
        },
        true
      );
    }

    if (providerSelect) {
      providerSelect.addEventListener("change", debouncedRefresh);
    }

    if (typeof jQuery !== "undefined") {
      jQuery(document).on(
        "change",
        'select[name="termset[providers][]"]',
        debouncedRefresh
      );
    }

    var mag = asp.querySelector(".promagnifier");
    if (mag) {
      mag.type = "button";
      mag.addEventListener("click", function (e) {
        e.preventDefault();
        refresh();
      });
    }

    var proboxForm = asp.querySelector(".probox form");
    if (proboxForm) {
      proboxForm.addEventListener(
        "submit",
        function (e) {
          e.preventDefault();
          e.stopImmediatePropagation();
          refresh();
        },
        true
      );
    }

    refresh();
    setTimeout(refresh, 400);
    window.addEventListener("load", function () {
      debouncedRefresh();
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
