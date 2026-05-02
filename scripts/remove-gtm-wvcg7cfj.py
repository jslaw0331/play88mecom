"""Remove GTM container GTM-WVCG7CFJ (inline script + noscript) from exported HTML."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = (ROOT / "slots" / "page" / "2" / "index.html").read_text(encoding="utf-8")

i = SAMPLE.index("GTM-WVCG7CFJ")
HEAD = SAMPLE[
    SAMPLE.rfind("\t<!-- Google Tag Manager -->", 0, i) : SAMPLE.index(
        "<!-- End Google Tag Manager -->", i
    )
    + len("<!-- End Google Tag Manager -->")
]
ib = SAMPLE.index("<body")
i2 = SAMPLE.index("GTM-WVCG7CFJ", ib)
NS = SAMPLE[
    SAMPLE.rfind("\t<!-- Google Tag Manager (noscript) -->", 0, i2) : SAMPLE.index(
        "<!-- End Google Tag Manager (noscript) -->", i2
    )
    + len("<!-- End Google Tag Manager (noscript) -->")
]

HEAD_CRLF = HEAD.replace("\n", "\r\n")
NS_CRLF = NS.replace("\n", "\r\n")


def main() -> None:
    updated = 0
    missing = []

    for path in ROOT.rglob("*.html"):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if "GTM-WVCG7CFJ" not in text:
            continue
        orig = text
        if HEAD in text:
            text = text.replace(HEAD, "", 1)
        elif HEAD_CRLF in text:
            text = text.replace(HEAD_CRLF, "", 1)
        else:
            missing.append((path, "head"))
            continue
        if NS in text:
            text = text.replace(NS, "", 1)
        elif NS_CRLF in text:
            text = text.replace(NS_CRLF, "", 1)
        else:
            missing.append((path, "noscript"))
            continue
        if text != orig:
            path.write_text(text, encoding="utf-8", newline="")
            updated += 1

    print(f"Updated {updated} files")
    if missing:
        print(f"Missing pattern: {len(missing)}")
        for p, kind in missing[:30]:
            print(f"  {kind}: {p.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
