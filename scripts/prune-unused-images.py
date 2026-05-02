"""
Find image files never referenced by static site assets and delete them.

By default only files under wp-content/uploads/ are candidates. Plugin/theme
images are skipped: they often load only from wp-admin or via JS we do not
model, so deleting them would risk breaking the export.

Scans: *.html, *.css, *.js, *.json, *.xml, *.xsl, *.txt, *.webmanifest, *.php
Extracts: absolute /paths…, wp-content|wp-includes paths, and resolves CSS url(...).

Run: python scripts/prune-unused-images.py --dry-run
      python scripts/prune-unused-images.py --apply
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]

# Only media library by default (safe for static hosting).
DEFAULT_DELETE_PREFIX = "wp-content/uploads"

IMAGE_EXT = frozenset(
    {
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".webp",
        ".svg",
        ".ico",
        ".avif",
        ".bmp",
    }
)

SCAN_SUFFIXES = frozenset(
    {
        ".html",
        ".htm",
        ".css",
        ".js",
        ".mjs",
        ".json",
        ".xml",
        ".xsl",
        ".txt",
        ".webmanifest",
        ".php",
    }
)

# Greedy + allows digits-only filenames (e.g. /2025/11/157.jpg)
ABS_IMG_RE = re.compile(
    r"(?i)(?<![\w/])(/[\w./+\-%]+\.(?:jpe?g|png|gif|webp|svg|ico|avif|bmp))"
    r"(?:\?[^\s\"'<>)\]]*)?",
)

# Unrooted wp-* paths (some JSON/JS)
REL_WP_RE = re.compile(
    r"(?i)(?<![\w/])((?:wp-content|wp-includes)/[\w./+\-%]+"
    r"\.(?:jpe?g|png|gif|webp|svg|ico|avif|bmp))(?:\?[^\s\"'<>)\]]*)?",
)

URL_CALL_RE = re.compile(r"url\(\s*[\"']?([^)\"']+?)[\"']?\s*\)", re.I)


def _normalize_ref(ref: str) -> str:
    ref = ref.strip().strip("\"'")
    ref = ref.split("#", 1)[0]
    ref = ref.split("?", 1)[0]
    ref = unquote(ref)
    ref = ref.lstrip("/").replace("\\", "/")
    return ref


def _safe_resolve_css_url(css_file: Path, raw_url: str) -> str | None:
    raw = raw_url.strip()
    if not raw or raw.startswith("data:"):
        return None
    if "#" in raw:
        raw = raw.split("#", 1)[0]
    path_only = raw.split("?", 1)[0].strip().strip("\"'")
    if Path(path_only).suffix.lower() not in IMAGE_EXT:
        return None
    if path_only.startswith(("http://", "https://", "//")):
        # Keep path-only if it looks like our site path in URL
        if "://" in path_only:
            try:
                from urllib.parse import urlparse

                u = urlparse(path_only)
                path_only = unquote(u.path or "")
            except Exception:
                return None
        if not path_only or path_only[0] != "/":
            return None
        return _normalize_ref(path_only)
    if path_only.startswith("/"):
        return _normalize_ref(path_only)
    base = css_file.resolve().parent
    try:
        target = (base / path_only).resolve()
    except (OSError, ValueError):
        return None
    try:
        rel = target.relative_to(ROOT.resolve())
    except ValueError:
        return None
    return rel.as_posix()


def collect_referenced_paths() -> set[str]:
    refs: set[str] = set()

    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in SCAN_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        # JSON-LD and some inline script use \/ for /
        norm = text.replace("\\/", "/")

        for m in ABS_IMG_RE.finditer(norm):
            refs.add(_normalize_ref(m.group(1)))

        for m in REL_WP_RE.finditer(norm):
            refs.add(_normalize_ref(m.group(1)))

        if path.suffix.lower() == ".css":
            for m in URL_CALL_RE.finditer(text):
                resolved = _safe_resolve_css_url(path, m.group(1))
                if resolved:
                    refs.add(resolved)

    return refs


def iter_image_files(delete_prefix: str | None = None):
    want = delete_prefix.strip("/ ").replace("\\", "/") if delete_prefix else None
    parts_need = want.split("/") if want else None
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in IMAGE_EXT:
            continue
        if ".git" in path.parts:
            continue
        rel = path.relative_to(ROOT)
        if parts_need is not None and len(rel.parts) < len(parts_need):
            continue
        if parts_need is not None and rel.parts[0 : len(parts_need)] != tuple(parts_need):
            continue
        yield path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List unused files and total size; do not delete",
    )
    parser.add_argument(
        "--prefix",
        default=DEFAULT_DELETE_PREFIX,
        metavar="PATH",
        help=(
            "Only consider deleting images under this repo-relative path "
            "(default: %s). Use \"\" with --include-all." % DEFAULT_DELETE_PREFIX
        ),
    )
    parser.add_argument(
        "--include-all",
        action="store_true",
        help="Consider every image under the repo (not recommended).",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually delete files (without this, only stats are printed)",
    )
    args = parser.parse_args()

    delete_prefix: str | None
    if args.include_all:
        delete_prefix = None
    else:
        delete_prefix = (args.prefix or "").strip("/ ").replace("\\", "/") or None

    print("Collecting references from text assets…", file=sys.stderr)
    refs = collect_referenced_paths()
    print("Unique referenced paths: %d" % len(refs), file=sys.stderr)

    refs_lower = {r.lower() for r in refs}

    # Stats: all images (no prefix) vs deletable bucket
    all_unused: list[Path] = []
    unused_in_bucket: list[Path] = []
    used_all = 0
    for img in iter_image_files(delete_prefix=None):
        key_lower = img.relative_to(ROOT).as_posix().lower()
        if key_lower in refs_lower:
            used_all += 1
            continue
        all_unused.append(img)
        if delete_prefix is None:
            unused_in_bucket.append(img)
        else:
            parts = delete_prefix.split("/")
            rel = img.relative_to(ROOT)
            if len(rel.parts) >= len(parts) and rel.parts[0 : len(parts)] == tuple(
                parts
            ):
                unused_in_bucket.append(img)

    bucket_bytes = sum(p.stat().st_size for p in unused_in_bucket)
    print(
        "Images referenced: %d | unused (whole tree): %d"
        % (used_all, len(all_unused)),
        file=sys.stderr,
    )
    if delete_prefix:
        print(
            "Delete bucket %r: unused %d (%.2f MB)"
            % (delete_prefix, len(unused_in_bucket), bucket_bytes / (1024 * 1024)),
            file=sys.stderr,
        )
    else:
        print(
            "Delete bucket (entire tree): unused %d (%.2f MB)"
            % (len(unused_in_bucket), bucket_bytes / (1024 * 1024)),
            file=sys.stderr,
        )

    if args.dry_run:
        for p in sorted(unused_in_bucket, key=lambda x: str(x).lower())[:200]:
            print(p.relative_to(ROOT).as_posix())
        if len(unused_in_bucket) > 200:
            print("… and %d more" % (len(unused_in_bucket) - 200))
        return 0

    if not args.apply:
        print(
            "No files deleted (pass --apply to delete). "
            "Use --dry-run to list paths.",
            file=sys.stderr,
        )
        return 0

    removed = 0
    for p in unused_in_bucket:
        try:
            p.unlink()
            removed += 1
        except OSError as e:
            print("Failed %s: %s" % (p, e), file=sys.stderr)
    print("Deleted %d files" % removed, file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
