#!/usr/bin/env python3
"""Publish Podcasting 2.0 chapters JSON from published chapter clocks.

startTime is the published chapter start (start_seconds), never play_start_seconds.
Writes chapters/<slug>.json and _sources/reports/CHAPTERS_FOR_TRANSISTOR.md.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://junkyardlovejakesbot.github.io/junkyard-love-archive"
OUT_DIR = ROOT / "chapters"
REPORT = ROOT / "_sources" / "reports" / "CHAPTERS_FOR_TRANSISTOR.md"


def chapters_payload(ep: dict) -> dict | None:
    rows = ep.get("chapters") or []
    if not rows:
        return None
    chapters = []
    for ch in rows:
        if ch.get("start_seconds") is None:
            continue
        title = (ch.get("title") or "").strip()
        if not title:
            continue
        chapters.append({"startTime": int(ch["start_seconds"]), "title": title})
    if not chapters:
        return None
    return {"version": "1.2.0", "chapters": chapters}


def main() -> None:
    idx = json.loads((ROOT / "assets" / "episodes_index.json").read_text(encoding="utf-8"))
    removed = set(idx.get("removed") or [])
    eps = [e for e in idx["episodes"] if e.get("number") not in removed]
    OUT_DIR.mkdir(exist_ok=True)
    written = []
    skipped = []
    for ep in eps:
        payload = chapters_payload(ep)
        if not payload:
            skipped.append(ep.get("number") or ep.get("slug"))
            continue
        slug = ep["slug"]
        dest = OUT_DIR / f"{slug}.json"
        dest.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        url = f"{ORIGIN}/chapters/{slug}.json"
        written.append((ep["number"], ep.get("guest") or "", ep.get("browse_title") or ep.get("canonical_title") or slug, url, len(payload["chapters"])))

    lines = [
        "# Chapters URLs for Transistor",
        "",
        "Paste the chapters URL into each episode in Transistor so the feed can emit a `podcast:chapters` tag (type `application/json+chapters`).",
        "",
        "Each file is Podcasting 2.0 chapters JSON version 1.2.0. `startTime` is the published chapter clock from the archive, not the speech-aligned play start.",
        "",
        f"Generated {date.today().isoformat()}. {len(written)} episode files.",
        "",
        "| Episode | Guest | Title | Chapters | URL |",
        "|---|---|---|---:|---|",
    ]
    for number, guest, title, url, n in written:
        title_cell = title.replace("|", "/")
        guest_cell = guest.replace("|", "/")
        lines.append(f"| {number} | {guest_cell} | {title_cell} | {n} | {url} |")
    lines.append("")
    if skipped:
        lines.append("Skipped (no published chapters): " + ", ".join(skipped))
        lines.append("")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"chapters json: {len(written)} written, {len(skipped)} skipped")
    print(f"report: {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
