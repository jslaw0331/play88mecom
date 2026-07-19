"""Convert relative sitemap CDATA paths to https://www.play88me.com/..."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://www.play88me.com"
CDATA_PATH = re.compile(r"(<!\[CDATA\[)(/[^]]*?)(\]\])")


def to_absolute(match: re.Match[str]) -> str:
    path = match.group(2)
    if path.startswith("//"):
        return match.group(0)
    return f"{match.group(1)}{SITE}{path}{match.group(3)}"


def main() -> None:
    updated = 0
    for path in sorted(ROOT.glob("*sitemap*.xml")):
        text = path.read_text(encoding="utf-8")
        new_text = CDATA_PATH.sub(to_absolute, text)
        if new_text != text:
            path.write_text(new_text, encoding="utf-8", newline="\n")
            updated += 1
            print(f"  {path.name}")

    print(f"fix-sitemap-urls: updated {updated} files")


if __name__ == "__main__":
    main()
