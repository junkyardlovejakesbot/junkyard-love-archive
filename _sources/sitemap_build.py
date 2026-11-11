#!/usr/bin/env python3
"""Build the public sitemap: indexable HTML pages only.

Excludes _sources/, GitHub verification files, inventory.csv, robots.txt,
the sitemap itself, and the start-here / six-ways-in redirects (canonical
is /where-to-begin/). Homepage loc always has a trailing slash.
"""
from __future__ import annotations

import subprocess
from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://junkyardlovejakesbot.github.io/junkyard-love-archive"
TODAY = date.today().isoformat()

SKIP_DIR_NAMES = {".git", "_sources", "start-here", "six-ways-in"}
SKIP_FILES = {
    "googleeb8959305cba963b.html",
    "BingSiteAuth.xml",
    "inventory.csv",
    "robots.txt",
    "sitemap.xml",
}


def git_date(path: Path) -> str:
    try:
        r = subprocess.run(
            ["git", "log", "-1", "--format=%cs", "--", str(path)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        committed = r.stdout.strip() if r.returncode == 0 else ""
    except OSError:
        committed = ""
    try:
        st = subprocess.run(
            ["git", "status", "--porcelain", "--", str(path)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        dirty = bool(st.stdout.strip())
    except OSError:
        dirty = not committed
    if dirty or not committed:
        return TODAY
    return committed


def public_index_pages() -> list[tuple[str, Path]]:
    """Return (url_path, file) pairs. url_path is '' for homepage, else 'folder/'."""
    out: list[tuple[str, Path]] = []
    for p in sorted(ROOT.rglob("index.html")):
        if any(part in SKIP_DIR_NAMES for part in p.parts):
            continue
        rel = p.relative_to(ROOT).as_posix()
        if rel == "index.html":
            out.append(("", p))
        elif rel.endswith("/index.html"):
            folder = rel[: -len("/index.html")]
            out.append((folder + "/", p))
    return out


def loc_for(url_path: str) -> str:
    if url_path == "":
        return ORIGIN + "/"
    return ORIGIN + "/" + url_path.lstrip("/")


def rebuild_sitemap() -> int:
    entries = []
    seen: set[str] = set()
    for url_path, path in public_index_pages():
        loc = loc_for(url_path)
        if loc in seen:
            continue
        seen.add(loc)
        entries.append((loc, git_date(path)))
    entries.sort(key=lambda x: (x[0] != ORIGIN + "/", x[0]))
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for loc, lastmod in entries:
        lines.append("  <url>")
        lines.append(f"    <loc>{xml_escape(loc)}</loc>")
        lines.append(f"    <lastmod>{lastmod}</lastmod>")
        lines.append("  </url>")
    lines.append("</urlset>")
    lines.append("")
    (ROOT / "sitemap.xml").write_text("\n".join(lines), encoding="utf-8")
    return len(entries)


def main() -> None:
    n = rebuild_sitemap()
    print(f"sitemap.xml: {n} URLs")


if __name__ == "__main__":
    main()
