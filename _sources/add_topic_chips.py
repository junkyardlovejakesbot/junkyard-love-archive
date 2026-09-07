#!/usr/bin/env python3
"""Add Topics chips to published episode pages from topics.json.

Idempotent: re-running replaces any existing .topic-chips block.
Skips *-removed dirs and non-numbered redirect stubs.
Links are base-safe: topics/<slug>/index.html (pages already have <base>).
"""
from __future__ import annotations

import html
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

DEPLOY = Path(__file__).resolve().parent.parent
SOURCES = DEPLOY / "_sources"
EPISODES = DEPLOY / "episodes"
TOPICS_JSON = SOURCES / "topics.json"

# Marker block: entire section between these comments is owned by this script.
START = "<!-- topic-chips:start -->"
END = "<!-- topic-chips:end -->"

CHIP_BLOCK_RE = re.compile(
    re.escape(START) + r".*?" + re.escape(END) + r"\n?",
    re.DOTALL,
)

# Insert before About heading (canonical placement).
ABOUT_RE = re.compile(r"<h2>\s*About\s*</h2>", re.IGNORECASE)


def load_episode_topics() -> dict[str, list[tuple[str, str]]]:
    data = json.loads(TOPICS_JSON.read_text(encoding="utf-8"))
    mapping: dict[str, list[tuple[str, str]]] = defaultdict(list)
    seen: dict[str, set[str]] = defaultdict(set)
    for cat in data["categories"]:
        cslug = cat["slug"]
        ctitle = cat["title"]
        for ep in cat["episodes"]:
            eslug = ep["slug"]
            if cslug in seen[eslug]:
                continue
            seen[eslug].add(cslug)
            mapping[eslug].append((cslug, ctitle))
    return mapping


def render_chips(topics: list[tuple[str, str]]) -> str:
    # Stable order: keep category order from topics.json (already insertion order).
    chips = []
    for cslug, ctitle in topics:
        href = f"topics/{cslug}/index.html"
        chips.append(
            f'<a class="topic-chip" href="{html.escape(href, quote=True)}">'
            f"{html.escape(ctitle)}</a>"
        )
    inner = "\n  ".join(chips)
    return (
        f"{START}\n"
        f'<p class="topic-chips"><span class="topic-chips-label">Topics</span>\n'
        f"  {inner}\n"
        f"</p>\n"
        f"{END}\n"
    )


def is_published_episode_dir(name: str) -> bool:
    if name.endswith("-removed"):
        return False
    # Numbered episode dirs only (skip redirect stubs / index.html).
    return bool(re.match(r"^\d{4}-", name))


def patch_episode(path: Path, topics: list[tuple[str, str]]) -> str:
    """Return 'patched' | 'updated' | 'skipped' | 'missing-about'."""
    text = path.read_text(encoding="utf-8")
    block = render_chips(topics)

    if CHIP_BLOCK_RE.search(text):
        new_text = CHIP_BLOCK_RE.sub(block, text, count=1)
        if new_text == text:
            return "unchanged"
        path.write_text(new_text, encoding="utf-8")
        return "updated"

    m = ABOUT_RE.search(text)
    if not m:
        return "missing-about"

    new_text = text[: m.start()] + block + text[m.start() :]
    path.write_text(new_text, encoding="utf-8")
    return "patched"


def main() -> int:
    mapping = load_episode_topics()
    dirs = sorted(
        p for p in EPISODES.iterdir() if p.is_dir() and is_published_episode_dir(p.name)
    )

    stats = defaultdict(int)
    samples: list[tuple[str, list[str]]] = []
    missing_from_topics: list[str] = []

    for d in dirs:
        html_path = d / "index.html"
        if not html_path.is_file():
            stats["no-html"] += 1
            continue
        topics = mapping.get(d.name)
        if not topics:
            missing_from_topics.append(d.name)
            stats["missing-topics"] += 1
            continue
        status = patch_episode(html_path, topics)
        stats[status] += 1
        if status in ("patched", "updated") and len(samples) < 3:
            samples.append((d.name, [t for _, t in topics]))

    # Prefer interesting multi-topic samples if we only got singles early
    if len(samples) < 3:
        samples = []
        for d in dirs:
            topics = mapping.get(d.name) or []
            if len(topics) >= 2:
                samples.append((d.name, [t for _, t in topics]))
            if len(samples) >= 3:
                break

    printed = stats["patched"] + stats["updated"] + stats.get("unchanged", 0)
    print(f"Published episode dirs considered: {len(dirs)}")
    print(f"Pages with chips (patched+updated+unchanged): {printed}")
    print(f"  patched (new): {stats['patched']}")
    print(f"  updated (replaced): {stats['updated']}")
    print(f"  unchanged: {stats.get('unchanged', 0)}")
    print(f"  missing-about: {stats['missing-about']}")
    print(f"  missing from topics.json: {len(missing_from_topics)}")
    if missing_from_topics:
        for s in missing_from_topics:
            print(f"    - {s}")
    print("Samples:")
    for slug, titles in samples[:3]:
        print(f"  {slug}")
        for t in titles:
            print(f"    · {t}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
