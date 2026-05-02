"""Create providers/{slug}/index.html for slugs linked in HTML but missing folders (static export gap)."""

from __future__ import annotations

import html
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SLOTS_INDEX = ROOT / "slots" / "index.html"
PROVIDERS = ROOT / "providers"


def linked_slugs() -> set[str]:
    slugs: set[str] = set()
    for p in ROOT.rglob("*.html"):
        if "wp-content" in p.parts:
            continue
        try:
            t = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for m in re.finditer(r'href="/providers/([a-z0-9-]+)/"', t):
            slugs.add(m.group(1))
    return slugs


def display_name(page_html: str, slug: str) -> str:
    m = re.search(
        rf'<a href="/providers/{re.escape(slug)}/"[^>]*>.*?<span>([^<]+)</span>',
        page_html,
        re.DOTALL,
    )
    if m:
        return m.group(1).strip()
    return slug.replace("-", " ").title()


def patch_list_current_term(page_html: str, slug: str) -> str:
    m = re.search(r'(<ul class="providers-list">)(.*?)(</ul>)', page_html, re.DOTALL)
    if not m:
        return page_html
    inner = m.group(2)
    inner = re.sub(r'<li class="current-term"', "<li", inner)
    inner2, n = re.subn(
        rf'(<li)(><a href="/providers/{re.escape(slug)}/")',
        r'\1 class="current-term"\2',
        inner,
        count=1,
    )
    if n != 1:
        return page_html
    return page_html.replace(m.group(0), m.group(1) + inner2 + m.group(3), 1)


def patch_head(page_html: str, slug: str, label: str) -> str:
    safe = html.escape(label)
    page_title = f"{safe} - Slot Games | Play88"
    base = f"/providers/{slug}/"
    t = page_html.replace(
        "<title>All Slot Games - Play88 Official Site</title>",
        f"<title>{page_title}</title>",
        1,
    )
    t = re.sub(
        r'<link rel="canonical" href="/slots/">',
        f'<link rel="canonical" href="{base}">',
        t,
        count=1,
    )
    t = t.replace(
        '<meta property="og:title" content="All Slot Games - Play88 Official Site">',
        f'<meta property="og:title" content="{page_title}">',
        1,
    )
    t = re.sub(
        r'<meta property="og:url" content="/slots/">',
        f'<meta property="og:url" content="{base}">',
        t,
        count=1,
    )
    t = t.replace(
        '<meta name="twitter:title" content="All Slot Games - Play88 Official Site">',
        f'<meta name="twitter:title" content="{page_title}">',
        1,
    )
    return t


def main() -> None:
    if not SLOTS_INDEX.is_file():
        print("ensure-missing-provider-pages: slots/index.html missing, skip")
        return
    template = SLOTS_INDEX.read_text(encoding="utf-8")
    have = {d.name for d in PROVIDERS.iterdir() if d.is_dir()}
    missing = sorted(linked_slugs() - have)
    if not missing:
        print("ensure-missing-provider-pages: no missing provider folders")
        return
    for slug in missing:
        label = display_name(template, slug)
        patched = patch_head(template, slug, label)
        patched = patch_list_current_term(patched, slug)
        out_dir = PROVIDERS / slug
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "index.html").write_text(patched, encoding="utf-8")
        print("ensure-missing-provider-pages:", out_dir / "index.html")
    print("ensure-missing-provider-pages: generated", len(missing), "archives")


if __name__ == "__main__":
    main()
