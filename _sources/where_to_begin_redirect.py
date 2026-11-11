#!/usr/bin/env python3
"""Write /start-here/ and /six-ways-in/ as a single-hop redirect to /where-to-begin/."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANON = "https://junkyardlovejakesbot.github.io/junkyard-love-archive/where-to-begin/"
TARGET = "/junkyard-love-archive/where-to-begin/"

HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<base href="/junkyard-love-archive/">
<title>Where to begin — The Junkyard Love Podcast</title>
<link rel="canonical" href="{CANON}">
<meta http-equiv="refresh" content="0;url={TARGET}">
<script>location.replace("{TARGET}");</script>
</head>
<body>
<p><a href="{TARGET}">Where to begin</a></p>
</body>
</html>
"""


def write_aliases(root: Path | None = None) -> None:
    base = root or ROOT
    for folder in ("start-here", "six-ways-in"):
        dest = base / folder / "index.html"
        dest.parent.mkdir(exist_ok=True)
        dest.write_text(HTML, encoding="utf-8")


if __name__ == "__main__":
    write_aliases()
