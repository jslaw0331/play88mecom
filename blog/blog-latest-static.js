(function () {
  function esc(s) {
    return String(s || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function parseFilterIds(raw) {
    if (!raw || raw.indexOf(",") !== -1) {
      return "all";
    }
    return String(raw).trim();
  }

  function postMatches(filterKey, termIds) {
    if (filterKey === "all") {
      return true;
    }
    var ids = termIds || [];
    for (var i = 0; i < ids.length; i++) {
      if (ids[i] === filterKey) {
        return true;
      }
    }
    return false;
  }

  function formatDate(iso) {
    if (!iso) {
      return "";
    }
    try {
      var d = new Date(iso);
      if (isNaN(d.getTime())) {
        return iso.slice(0, 10);
      }
      return d.toLocaleDateString(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
      });
    } catch (e) {
      return iso.slice(0, 10);
    }
  }

  function termBadgeLabel(termIds) {
    var ids = termIds || [];
    if (ids.indexOf("18") !== -1) {
      return "SLOTS";
    }
    if (ids.indexOf("17") !== -1) {
      return "CASINO";
    }
    if (ids.indexOf("19") !== -1) {
      return "SPORTS";
    }
    return "BLOG";
  }

  function renderCard(p) {
    var title = esc(p.title);
    var url = esc(p.url);
    var rawImg = (p.image || "").trim();
    var badge = esc(termBadgeLabel(p.termIds));
    var dateStr = formatDate(p.date);
    var excerpt = esc(p.excerpt || "");
    var media =
      '<a class="blog-static-post__media" href="' +
      url +
      '">' +
      (rawImg
        ? '<img class="blog-static-post__img" src="' +
          esc(rawImg) +
          '" alt="" loading="lazy" decoding="async" width="320" height="180" />'
        : '<span class="blog-static-post__img blog-static-post__img--placeholder"></span>') +
      "</a>";
    return (
      '<article class="blog-static-post">' +
      media +
      '<div class="blog-static-post__body">' +
      '<span class="blog-static-post__tag">' +
      badge +
      "</span>" +
      '<h2 class="blog-static-post__title"><a href="' +
      url +
      '">' +
      title +
      "</a></h2>" +
      (dateStr
        ? '<p class="blog-static-post__date">' + esc(dateStr) + "</p>"
        : "") +
      (excerpt ? '<p class="blog-static-post__excerpt">' + excerpt + "</p>" : "") +
      '<a class="blog-static-post__readmore" href="' +
      url +
      '">Read More</a>' +
      "</div>" +
      "</article>"
    );
  }

  function setStatus(el, n, loadingErr) {
    if (!el) {
      return;
    }
    el.classList.remove("active");
    if (loadingErr) {
      el.textContent = "Posts found: —";
      return;
    }
    el.textContent = "Posts found: " + n;
  }

  function run(container, state, data) {
    var per = parseInt(container.getAttribute("data-per-page"), 10) || data.perPage || 4;
    var filterRaw = container.getAttribute("data-terms") || "17,18,19";
    var filterKey = parseFilterIds(filterRaw);

    var list = [];
    for (var i = 0; i < data.posts.length; i++) {
      if (postMatches(filterKey, data.posts[i].termIds)) {
        list.push(data.posts[i]);
      }
    }
    var slice = list.slice(0, per);

    var row = container.querySelector("#manage-ajax-response .content");
    var statusEl = container.querySelector("#manage-ajax-response .status");
    if (!row) {
      return;
    }
    row.innerHTML =
      '<div class="blog-static-post-list" id="blog-static-post-row" role="list">' +
      slice.map(renderCard).join("") +
      "</div>";
    setStatus(statusEl, list.length, false);
  }

  function bindFilters(container, state, data) {
    var ul = container.querySelector(".caf-filter-container");
    if (!ul) {
      return;
    }
    ul.addEventListener(
      "click",
      function (e) {
        var a = e.target.closest("a[data-main-id=flt]");
        if (!a || !container.contains(a)) {
          return;
        }
        e.preventDefault();
        var id = a.getAttribute("data-id");
        if (!id) {
          return;
        }
        container.setAttribute("data-terms", id);
        ul.querySelectorAll("a[data-main-id=flt]").forEach(function (x) {
          x.classList.remove("active");
        });
        a.classList.add("active");
        run(container, state, data);
      },
      true
    );
  }

  function init() {
    var container = document.getElementById("caf-post-layout-container");
    if (!container || container.getAttribute("data-blog-static") === "1") {
      return;
    }
    container.setAttribute("data-blog-static", "1");

    var statusEl = container.querySelector("#manage-ajax-response .status");
    setStatus(statusEl, 0, false);
    if (statusEl) {
      statusEl.textContent = "Loading…";
    }

    var state = {};
    fetch("/blog/blog-latest-data.json", { credentials: "same-origin" })
      .then(function (r) {
        if (!r.ok) {
          throw new Error("fetch");
        }
        return r.json();
      })
      .then(function (data) {
        if (!data || !Array.isArray(data.posts)) {
          throw new Error("bad json");
        }
        run(container, state, data);
        bindFilters(container, state, data);
      })
      .catch(function () {
        setStatus(statusEl, 0, true);
        var row = container.querySelector("#manage-ajax-response .content");
        if (row) {
          row.innerHTML =
            '<p class="error-caf">Could not load posts. Please refresh the page.</p>';
        }
      });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
