"""Fix static slots listing: pagination URLs, slots-index.json, script tag injection."""

from __future__ import annotations

import json
import re
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SLOTS = ROOT / "slots"
PROVIDERS = ROOT / "providers"
SCRIPT_TAG = '<script src="/slots/slots-static.js" defer></script>'
SCRIPT_MARKER = "slots-static.js"
STYLESHEET_MARKER = "slots-static.css"
STYLESHEET_TAG = '\t<link rel="stylesheet" href="/slots/slots-static.css">\n'
ASP_ID = 'id="ajaxsearchpro1_1"'
HEADER_SEARCH_ID = 'id="header-search"'
HEADER_SCRIPT_MARKER = "header-search.js"
HEADER_SCRIPT_TAG = (
    '\t<script src="/wp-content/themes/astra-child/header-search.js" defer></script>\n'
)


def fix_urls(text: str) -> str:
    def repl_href(m: re.Match[str]) -> str:
        n = int(m.group(1))
        if n <= 1:
            return 'href="/slots/"'
        return f'href="/slots/page/{n}/"'

    def repl_data(m: re.Match[str]) -> str:
        n = int(m.group(1))
        max_page = 0
        max_m = re.search(r'data-max-page="(\d+)"', text)
        if max_m:
            max_page = int(max_m.group(1))
        if n <= 1:
            return 'data-next-page="/slots/"'
        if max_page and n > max_page:
            return f'data-next-page="/slots/page/{max_page}/"'
        return f'data-next-page="/slots/page/{n}/"'

    text = re.sub(r'href="/slots/\?e-page-6174417e=(\d+)"', repl_href, text)
    text = re.sub(r'data-next-page="/slots/\?e-page-6174417e=(\d+)"', repl_data, text)
    return text


def extract_items(text: str) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    parts = text.split('data-elementor-type="loop-item"')
    for part in parts[1:]:
        pr = re.search(r"providers-([a-z0-9-]+)", part)
        prov = pr.group(1) if pr else ""
        m = re.search(
            r'<h2 class="elementor-heading-title[^"]*"[^>]*>\s*<a href="([^"]+)"[^>]*>([^<]+)</a>',
            part,
        )
        if not m:
            continue
        url, title = m.group(1), m.group(2).strip()
        items.append({"title": title, "url": url, "provider": prov})
    return items


def ensure_script_tag(text: str) -> str:
    if SCRIPT_MARKER in text:
        return text
    body_close = text.rfind("</body>")
    if body_close == -1:
        return text
    return text[:body_close] + "\t" + SCRIPT_TAG + "\n" + text[body_close:]


def ensure_stylesheet_link(text: str) -> str:
    if STYLESHEET_MARKER in text:
        return text
    head_close = text.lower().find("</head>")
    if head_close == -1:
        return text
    return text[:head_close] + STYLESHEET_TAG + text[head_close:]


def ensure_header_search_script(text: str) -> str:
    if HEADER_SCRIPT_MARKER in text or HEADER_SEARCH_ID not in text:
        return text
    body_close = text.rfind("</body>")
    if body_close == -1:
        return text
    return text[:body_close] + HEADER_SCRIPT_TAG + text[body_close:]


def main() -> None:
    listing_paths = [SLOTS / "index.html"] + sorted(SLOTS.glob("page/*/index.html"))
    all_items: list[dict[str, str]] = []
    seen: set[str] = set()

    for path in listing_paths:
        if not path.exists():
            continue
        t = path.read_text(encoding="utf-8")
        for it in extract_items(t):
            if it["url"] in seen:
                continue
            seen.add(it["url"])
            all_items.append(it)

    all_items.sort(key=lambda x: x["title"].lower())
    (SLOTS / "slots-index.json").write_text(
        json.dumps(all_items, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("slots-index.json:", len(all_items), "items")

    updated = 0
    for path in listing_paths:
        if not path.exists():
            continue
        t = path.read_text(encoding="utf-8")
        nt = fix_urls(t)
        nt = ensure_stylesheet_link(nt)
        nt = ensure_script_tag(nt)
        if nt != t:
            path.write_text(nt, encoding="utf-8")
            updated += 1
    print("updated", updated, "slots listing html files")

    prov_updated = 0
    for path in sorted(PROVIDERS.glob("*/index.html")):
        if not path.is_file():
            continue
        t = path.read_text(encoding="utf-8")
        if ASP_ID not in t:
            continue
        nt = ensure_stylesheet_link(t)
        nt = ensure_script_tag(nt)
        if nt != t:
            path.write_text(nt, encoding="utf-8")
            prov_updated += 1
    print("updated", prov_updated, "provider archive html files")

    header_updated = 0
    for path in sorted(ROOT.rglob("index.html")):
        if not path.is_file() or "node_modules" in path.parts:
            continue
        t = path.read_text(encoding="utf-8")
        nt = ensure_header_search_script(t)
        if nt != t:
            path.write_text(nt, encoding="utf-8")
            header_updated += 1
    print("updated", header_updated, "html files (header search script)")

    import importlib.util

    ensure_path = pathlib.Path(__file__).resolve().parent / "ensure-missing-provider-pages.py"
    spec = importlib.util.spec_from_file_location("ensure_missing_provider_pages", ensure_path)
    if spec and spec.loader:
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.main()


if __name__ == "__main__":
    main()
