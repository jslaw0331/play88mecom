"""Convert relative canonical and og:url tags to https://www.play88me.com/..."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://www.play88me.com"
SKIP_PARTS = {"wp-content", "wp-includes", "wp-admin"}

CANONICAL = re.compile(
    r'(<link rel="canonical" href=")(/[^"]*)(">)',
    re.IGNORECASE,
)
OG_URL = re.compile(
    r'(<meta property="og:url" content=")(/[^"]*)(">)',
    re.IGNORECASE,
)


def to_absolute(path: str) -> str:
    if path == "/":
        return f"{SITE}/"
    return f"{SITE}{path}"


def main() -> None:
    updated = 0
    for path in ROOT.rglob("*.html"):
        if any(part in SKIP_PARTS for part in path.parts):
            continue

        text = path.read_text(encoding="utf-8")
        new_text = CANONICAL.sub(
            lambda m: f"{m.group(1)}{to_absolute(m.group(2))}{m.group(3)}",
            text,
        )
        new_text = OG_URL.sub(
            lambda m: f"{m.group(1)}{to_absolute(m.group(2))}{m.group(3)}",
            new_text,
        )

        if new_text != text:
            path.write_text(new_text, encoding="utf-8", newline="")
            updated += 1

    print(f"fix-canonical-urls: updated {updated} files")


if __name__ == "__main__":
    main()
