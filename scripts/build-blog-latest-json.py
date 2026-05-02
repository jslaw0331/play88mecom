"""Build blog/blog-latest-data.json for static LATEST POST grid (replaces CAF AJAX)."""

from __future__ import annotations

import json
import re
import pathlib
from datetime import datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
BLOG = ROOT / "blog"
OUT = BLOG / "blog-latest-data.json"

# When HTML has no tag-* class, map slug -> WP tag ids used in caf filters (17=casino, 18=slots, 19=sports)
SLUG_TERMS: dict[str, list[str]] = {
    "top-5-myths-about-online-casinos-debunked": ["17"],
    "slot-malaysia-play-slot-games-at-trusted-online-casinos": ["18"],
    "play88beila": ["17", "18"],
    "pickleball-betting-malaysia": ["19"],
    "monkey-king-slot-game-review-2024-play-now-on-play88": ["18"],
    "mega888-game-list-highest-win-rate-mega888-casino-games": ["18"],
    "how-to-spot-a-safe-and-secure-online-casino-key-features-to-look-for": ["17"],
    "how-to-manage-your-bankroll-when-playing-at-online-casinos": ["17"],
    "god-of-wealth-slot-review-play-free-earn-real-money-on-play88": ["18"],
    "crown-slot-review-2024-play-free-demo-on-play88": ["18"],
    "cleopatras-gold-a-slots-game-fit-for-a-pharaoh-available-on-918kiss": ["18"],
    "cleopatra-riches-mega888": ["18"],
    "fairy-garden-918kiss-review-and-how-to-play": ["18"],
}


def _tag_ids_from_classes(html: str) -> list[str]:
    out: list[str] = []
    if re.search(r"\btag-casino\b", html):
        out.append("17")
    if re.search(r"\btag-slots\b", html):
        out.append("18")
    if re.search(r"\btag-sports\b", html):
        out.append("19")
    return sorted(set(out))


def _blogposting_from_ld(html: str) -> dict[str, str | None]:
    m = re.search(
        r'<script type="application/ld\+json"[^>]*class="aioseo-schema"[^>]*>\s*(\{.*?\})\s*</script>',
        html,
        re.DOTALL,
    )
    if not m:
        return {"headline": None, "date": None, "image": None, "section": None}
    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError:
        return {"headline": None, "date": None, "image": None, "section": None}
    graph = data.get("@graph")
    if not isinstance(graph, list):
        return {"headline": None, "date": None, "image": None, "section": None}
    for node in graph:
        if isinstance(node, dict) and node.get("@type") == "BlogPosting":
            headline = node.get("headline") or node.get("name")
            date = node.get("datePublished")
            img = node.get("image")
            image_url = None
            if isinstance(img, dict):
                image_url = img.get("url")
            elif isinstance(img, str):
                image_url = img
            section = node.get("articleSection")
            return {
                "headline": headline if isinstance(headline, str) else None,
                "date": date if isinstance(date, str) else None,
                "image": image_url,
                "section": section if isinstance(section, str) else None,
            }
    return {"headline": None, "date": None, "image": None, "section": None}


def _canonical(html: str) -> str | None:
    m = re.search(r'<link rel="canonical" href="([^"]+)"', html)
    return m.group(1).strip() if m else None


def _meta_description(html: str) -> str:
    m = re.search(
        r'<meta name="description" content="([^"]*)"', html, re.IGNORECASE
    )
    return m.group(1).strip() if m else ""


def _infer_terms(slug: str, title: str, section: str | None) -> list[str]:
    if slug in SLUG_TERMS:
        return SLUG_TERMS[slug]
    blob = f"{slug} {title}".lower()
    terms: set[str] = set()
    if section:
        for part in section.lower().split(","):
            p = part.strip()
            if p == "slots":
                terms.add("18")
            elif p == "casino":
                terms.add("17")
            elif p == "sports":
                terms.add("19")
    if not terms:
        if "pickleball" in blob or "sportsbook" in blob:
            terms.add("19")
        if "slot" in blob or "mega888" in blob or "918kiss" in blob or "jili" in blob:
            terms.add("18")
        if "casino" in blob or "blackjack" in blob or "bankroll" in blob or "baccarat" in blob:
            terms.add("17")
    return sorted(terms)


def _parse_date(iso: str | None) -> float:
    if not iso:
        return 0.0
    try:
        if iso.endswith("Z"):
            iso = iso[:-1] + "+00:00"
        return datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return 0.0


def main() -> None:
    posts: list[dict] = []
    for path in sorted(BLOG.glob("*/index.html")):
        html = path.read_text(encoding="utf-8")
        url = _canonical(html)
        if not url:
            url = "/" + path.parent.relative_to(BLOG).as_posix().rstrip("/") + "/"
        ld = _blogposting_from_ld(html)
        title = ld["headline"]
        if not title:
            tm = re.search(
                r'<h1 class="elementor-heading-title[^"]*"[^>]*>([^<]+)</h1>',
                html,
            )
            title = tm.group(1).strip() if tm else path.parent.name.replace("-", " ").title()
        slug = path.parent.name
        term_ids = _tag_ids_from_classes(html)
        if not term_ids:
            term_ids = _infer_terms(slug, title, ld.get("section") if ld else None)
        if not term_ids:
            term_ids = ["17", "18"]

        image = ld["image"]
        if not image:
            im = re.search(
                r'<meta property="og:image" content="([^"]+)"',
                html,
                re.I,
            )
            image = im.group(1) if im else ""

        posts.append(
            {
                "url": url,
                "title": title.strip(),
                "image": image or "",
                "date": ld["date"] or "",
                "excerpt": _meta_description(html)[:280],
                "termIds": term_ids,
            }
        )

    posts.sort(key=lambda p: _parse_date(p["date"]), reverse=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps({"perPage": 4, "posts": posts}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("wrote", OUT.relative_to(ROOT), len(posts), "posts")


if __name__ == "__main__":
    main()
