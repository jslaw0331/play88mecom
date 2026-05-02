"""
Remove Google gtag block for G-WB625TE9FD and strip &_gl= linker params from hrefs
(e.g. _ga_KML0Y8RMDT) from exported HTML.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = (ROOT / "slots" / "page" / "2" / "index.html").read_text(encoding="utf-8")

a = SAMPLE.index("\t<!-- Google tag (gtag.js) -->")
b = SAMPLE.index("\t<!-- Google Tag Manager -->", a)
GTAG_BLOCK = SAMPLE[a:b]
GTAG_BLOCK_CRLF = GTAG_BLOCK.replace("\n", "\r\n")

_GL_IN_HREF = re.compile(r"&amp;_gl=[^\"]*")


def main() -> None:
    gtag_files = 0
    gl_subs = 0
    missing_gtag = []

    for path in ROOT.rglob("*.html"):
        text = path.read_text(encoding="utf-8")
        orig = text

        if "G-WB625TE9FD" in text:
            if GTAG_BLOCK in text:
                text = text.replace(GTAG_BLOCK, "", 1)
                gtag_files += 1
            elif GTAG_BLOCK_CRLF in text:
                text = text.replace(GTAG_BLOCK_CRLF, "", 1)
                gtag_files += 1
            else:
                missing_gtag.append(path)

        n_gl = len(_GL_IN_HREF.findall(text))
        if n_gl:
            gl_subs += n_gl
            text = _GL_IN_HREF.sub("", text)

        if text != orig:
            path.write_text(text, encoding="utf-8", newline="")

    print("Removed G-WB625TE9FD gtag block from %d files" % gtag_files)
    print("Stripped &amp;_gl= from %d occurrences" % gl_subs)
    if missing_gtag:
        print("Could not find gtag block (manual fix needed): %d" % len(missing_gtag))
        for p in missing_gtag[:25]:
            print(" ", p.relative_to(ROOT))


if __name__ == "__main__":
    main()
