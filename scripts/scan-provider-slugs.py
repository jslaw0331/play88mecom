"""List /providers/{slug}/ links in HTML vs existing provider folders."""
from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent


def main() -> None:
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
    have = {d.name for d in (ROOT / "providers").iterdir() if d.is_dir()}
    missing = sorted(slugs - have)
    print("linked slugs:", len(slugs))
    print("provider dirs:", len(have))
    print("missing dirs:", len(missing))
    for s in missing:
        print(s)


if __name__ == "__main__":
    main()
