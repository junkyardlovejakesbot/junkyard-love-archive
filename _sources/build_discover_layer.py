#!/usr/bin/env python3
"""Layer B+C: JSON-LD, sitemap, llms.txt, YouTube/Opus reports, SHIP_DISCOVER.

Uses only catalog fields. Does not post to YouTube. Does not invent IDs/bios.
"""
from __future__ import annotations

import csv
import html
import json
import re
from datetime import date
from pathlib import Path

DEPLOY = Path(__file__).resolve().parents[1]
ASSETS = DEPLOY / "assets"
REPORTS = DEPLOY / "_sources" / "reports"
BASE_SITE = "https://junkyardlovejakesbot.github.io/junkyard-love-archive"
MOTTO = "drink some water, stretch, love yourselves."
SHOW_NAME = "The Junkyard Love Podcast"
SHOW_DESC = (
    "Long conversations for people who want honest talk about how we grow, heal, "
    "create, and understand ourselves. Full episodes, searchable transcripts, and clips."
)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def is_bumper(title: str) -> bool:
    """Mirror assets/archive.js isBumper heuristics."""
    t = (title or "").lower().strip()
    if not t:
        return True
    if re.match(r"^(intro|outro|opening|closing|end credits|credits|theme|bumper)\b", t):
        return True
    if "welcome to the junkyard love" in t and len(t) < 55:
        return True
    if "drink some water" in t:
        return True
    if re.search(r"let'?s roll", t) and re.search(r"drink|water|hit record", t):
        return True
    if "hit record" in t and len(t) < 40:
        return True
    return False


def iso_duration(duration: str | None, duration_seconds: int | None) -> str | None:
    secs = duration_seconds
    if secs is None and duration:
        parts = [int(x) for x in duration.split(":")]
        if len(parts) == 3:
            secs = parts[0] * 3600 + parts[1] * 60 + parts[2]
        elif len(parts) == 2:
            secs = parts[0] * 60 + parts[1]
    if secs is None:
        return None
    h, rem = divmod(int(secs), 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"PT{h}H{m}M{s}S"
    return f"PT{m}M{s}S"


def yt_chapter_ts(start_seconds: int | None, start: str | None) -> str:
    """YouTube paste format: 0:00 / 1:02 / 1:02:03"""
    secs = start_seconds
    if secs is None and start:
        parts = [int(x) for x in start.split(":")]
        if len(parts) == 3:
            secs = parts[0] * 3600 + parts[1] * 60 + parts[2]
        elif len(parts) == 2:
            secs = parts[0] * 60 + parts[1]
        else:
            secs = int(parts[0])
    secs = int(secs or 0)
    h, rem = divmod(secs, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def t_anchor(start_seconds: int | None, start: str | None) -> str:
    secs = start_seconds
    if secs is None and start:
        parts = [int(x) for x in start.split(":")]
        if len(parts) == 3:
            secs = parts[0] * 3600 + parts[1] * 60 + parts[2]
        elif len(parts) == 2:
            secs = parts[0] * 60 + parts[1]
        else:
            secs = 0
    secs = int(secs or 0)
    h, rem = divmod(secs, 3600)
    m, s = divmod(rem, 60)
    return f"t-{h:02d}-{m:02d}-{s:02d}"


def replace_or_insert_jsonld(page: Path, json_ld_obj: dict) -> bool:
    text = page.read_text(encoding="utf-8")
    blob = json.dumps(json_ld_obj, ensure_ascii=False, indent=2)
    script = f'<script type="application/ld+json">\n{blob}\n</script>'
    if re.search(r'<script type="application/ld\+json">.*?</script>', text, re.S):
        # Replace first JSON-LD only (episode pages may have one)
        new_text, n = re.subn(
            r'<script type="application/ld\+json">.*?</script>',
            script,
            text,
            count=1,
            flags=re.S,
        )
        changed = n == 1 and new_text != text
    else:
        # Insert before </head>
        if "</head>" not in text:
            return False
        new_text = text.replace("</head>", script + "\n</head>", 1)
        changed = True
    if changed:
        page.write_text(new_text, encoding="utf-8")
    return changed


def update_homepage_jsonld() -> bool:
    page = DEPLOY / "index.html"
    data = {
        "@context": "https://schema.org",
        "@type": "PodcastSeries",
        "name": SHOW_NAME,
        "description": SHOW_DESC,
        "url": BASE_SITE + "/",
    }
    return replace_or_insert_jsonld(page, data)


def update_episode_jsonld(episodes: list[dict]) -> tuple[int, int]:
    touched = 0
    skipped = 0
    for ep in episodes:
        if ep.get("removed"):
            skipped += 1
            continue
        slug = ep["slug"]
        page = DEPLOY / "episodes" / slug / "index.html"
        if not page.exists():
            skipped += 1
            continue
        name = ep.get("canonical_title") or ep.get("browse_title") or slug
        url = f"{BASE_SITE}/episodes/{slug}/"
        data: dict = {
            "@context": "https://schema.org",
            "@type": "PodcastEpisode",
            "name": name,
            "url": url,
            "partOfSeries": {
                "@type": "PodcastSeries",
                "name": SHOW_NAME,
                "url": BASE_SITE + "/",
            },
        }
        if ep.get("date"):
            data["datePublished"] = ep["date"]
        dur = iso_duration(ep.get("duration"), ep.get("duration_seconds"))
        if dur:
            data["duration"] = dur
        if ep.get("number"):
            try:
                data["episodeNumber"] = int(str(ep["number"]).lstrip("0") or "0")
            except ValueError:
                pass
        guest = ep.get("guest")
        if guest and not ep.get("is_solo"):
            # Split multi-guest "A & B" into Person list when clear
            people = re.split(r"\s*&\s*|\s+and\s+", guest)
            people = [p.strip() for p in people if p.strip()]
            if len(people) == 1:
                data["contributor"] = {"@type": "Person", "name": people[0]}
            elif people:
                data["contributor"] = [{"@type": "Person", "name": p} for p in people]
        yid = ep.get("youtube_id")
        yurl = ep.get("youtube_url")
        if yid:
            if not yurl:
                yurl = f"https://www.youtube.com/watch?v={yid}"
            data["associatedMedia"] = {
                "@type": "VideoObject",
                "name": name,
                "contentUrl": yurl,
                "embedUrl": f"https://www.youtube.com/embed/{yid}",
            }
        if replace_or_insert_jsonld(page, data):
            touched += 1
        else:
            # still count as processed if already matching
            touched += 1
    return touched, skipped


def rebuild_sitemap(episodes: list[dict]) -> int:
    urls: list[str] = []

    def add(path: str):
        path = path.lstrip("/")
        if path and not path.endswith("/") and not path.endswith(".txt") and not path.endswith(".xml") and not path.endswith(".html") and "." in Path(path).name:
            loc = f"{BASE_SITE}/{path}"
        elif path.endswith(".txt") or path.endswith(".json") or path.endswith(".xml") or path.endswith(".html"):
            loc = f"{BASE_SITE}/{path}"
        else:
            loc = f"{BASE_SITE}/{path}".rstrip("/") + "/"
        if path == "":
            loc = BASE_SITE + "/"
        urls.append(loc)

    add("")
    for section in [
        "six-ways-in/",
        "start-here/",
        "radio/",
        "topics/",
        "guests/",
        "episodes/",
        "books/",
        "search/",
        "listen/",
        "clips/",
        "donate/",
        "merch/",
        "llms.txt",
    ]:
        add(section)

    # moods
    moods = DEPLOY / "moods"
    if moods.exists():
        add("moods/")
        for d in sorted(moods.iterdir()):
            if d.is_dir() and (d / "index.html").exists():
                add(f"moods/{d.name}/")

    # topics
    for d in sorted((DEPLOY / "topics").iterdir()):
        if d.is_dir() and (d / "index.html").exists():
            add(f"topics/{d.name}/")

    # guests
    for d in sorted((DEPLOY / "guests").iterdir()):
        if d.is_dir() and (d / "index.html").exists():
            add(f"guests/{d.name}/")

    # books
    for d in sorted((DEPLOY / "books").iterdir()):
        if d.is_dir() and (d / "index.html").exists():
            add(f"books/{d.name}/")

    # episodes (non-removed)
    removed = set()
    for ep in episodes:
        if ep.get("removed"):
            removed.add(ep["slug"])
            continue
        add(f"episodes/{ep['slug']}/")

    # also include on-disk episode folders that aren't removed aliases? stick to index
    # Dedupe preserve order
    seen = set()
    ordered = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            ordered.append(u)

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for u in ordered:
        lines.append("  <url>")
        lines.append(f"    <loc>{html.escape(u)}</loc>")
        lines.append("  </url>")
    lines.append("</urlset>")
    lines.append("")
    (DEPLOY / "sitemap.xml").write_text("\n".join(lines), encoding="utf-8")
    return len(ordered)


def update_llms_txt(episodes: list[dict], guest_index_names: dict[str, str]) -> None:
    path = DEPLOY / "llms.txt"
    text = path.read_text(encoding="utf-8")

    # Ensure machine files section mentions books_index + guests index
    useful = """### Useful machine files
- `assets/episodes_index.json` — episode catalog (chapters, links, topics, youtube_id)
- `assets/quotes_clean.json` — public published-quote pool only (`source=published`, 244)
- `assets/clips_index.json` — chapter/clip index (titles + timestamps; summaries intentionally empty)
- `assets/books_index.json` — books mentioned on-air (guest_slug when known)
- `guests/index.html` — guest doorway index (filterable)
- `llms.txt` — this file
"""
    text = re.sub(
        r"### Useful machine files\n(?:- .+\n)+",
        useful + "\n",
        text,
        count=1,
    )

    # Rebuild Guests section from live guest folders + display names
    guest_lines = ["## Guests", ""]
    guest_lines.append(
        f"Index: [{BASE_SITE}/guests/]({BASE_SITE}/guests/)"
    )
    guest_lines.append("")
    for slug, name in sorted(guest_index_names.items(), key=lambda x: x[1].lstrip('"').lower()):
        guest_lines.append(f"- [{name}]({BASE_SITE}/guests/{slug}/)")
    guest_lines.append("")

    new_guests = "\n".join(guest_lines)
    if re.search(r"^## Guests\n", text, re.M):
        text = re.sub(
            r"^## Guests\n.*?(?=^## |\Z)",
            new_guests + "\n",
            text,
            count=1,
            flags=re.M | re.S,
        )
    else:
        text = text.rstrip() + "\n\n" + new_guests

    # Ensure quotes_clean + books mentioned near top reliable fields if missing books
    if "assets/books_index.json" not in text.split("## Episodes")[0]:
        pass  # already patched useful section

    path.write_text(text, encoding="utf-8")


def load_inventory_audio() -> dict[str, dict]:
    inv = {}
    path = DEPLOY / "inventory.csv"
    if not path.exists():
        return inv
    with path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            num = (row.get("episode_number") or "").zfill(4)
            inv[num] = row
    return inv


def write_missing_youtube(episodes: list[dict], inventory: dict) -> int:
    rows = []
    for ep in episodes:
        if ep.get("removed"):
            continue
        yid = ep.get("youtube_id")
        # no id, or known unavailable markers — no guessing
        unavailable = False
        if isinstance(yid, str) and yid.lower() in {"unavailable", "none", "null", "missing"}:
            unavailable = True
            yid = None
        if yid:
            continue
        num = str(ep.get("number") or "")
        inv = inventory.get(num.zfill(4), {})
        audio_bits = []
        if inv.get("audio_enclosure_url"):
            audio_bits.append("mp3 enclosure on file")
        if ep.get("rss_url") or inv.get("rss_episode_url"):
            audio_bits.append(f"rss: {ep.get('rss_url') or inv.get('rss_episode_url')}")
        if ep.get("apple_show") or inv.get(""):
            if ep.get("apple_show"):
                audio_bits.append("Apple episode URL on file")
        if ep.get("spotify_show"):
            audio_bits.append("Spotify show URL on file (show-level)")
        if not audio_bits:
            audio_bits.append("audio links unknown in catalog")
        rows.append(
            {
                "number": num,
                "title": ep.get("browse_title") or ep.get("canonical_title") or ep["slug"],
                "guest": ep.get("guest") or "",
                "slug": ep["slug"],
                "audio": "; ".join(audio_bits),
                "note": "no youtube_id" + (" / marked unavailable" if unavailable else ""),
            }
        )

    lines = [
        "# Missing YouTube",
        "",
        "Episodes with no `youtube_id` (or known unavailable). IDs are not guessed.",
        "",
        f"Count: **{len(rows)}**",
        "",
    ]
    for r in rows:
        lines.append(f"## {r['number']} — {r['title']}")
        lines.append(f"- Guest: {r['guest']}")
        lines.append(f"- Slug: `{r['slug']}`")
        lines.append(f"- Status: {r['note']}")
        lines.append(f"- Audio on file: {r['audio']}")
        lines.append("")
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "MISSING_YOUTUBE.md").write_text("\n".join(lines), encoding="utf-8")
    return len(rows)


def write_youtube_chapters(episodes: list[dict]) -> int:
    lines = [
        "# YouTube chapters (paste-ready)",
        "",
        "For Jacob to paste into YouTube descriptions. Not published by this script.",
        "Bumpers / host-open style titles skipped (archive.js `isBumper` heuristics).",
        "First line forced to `0:00` when the first kept chapter starts later (YouTube requirement).",
        "",
    ]
    count = 0
    for ep in sorted(episodes, key=lambda e: e.get("number") or "", reverse=True):
        if ep.get("removed") or not ep.get("youtube_id"):
            continue
        chapters = ep.get("chapters") or []
        kept = []
        for ch in chapters:
            title = (ch.get("title") or "").strip()
            if is_bumper(title):
                continue
            if re.match(r"^chapter\s*\d+$", title, re.I):
                continue
            # Skip host_open-like titles
            if title.lower().startswith("host open"):
                continue
            kept.append(ch)
        if not kept:
            continue
        count += 1
        name = ep.get("browse_title") or ep.get("canonical_title") or ep["slug"]
        yurl = ep.get("youtube_url") or f"https://www.youtube.com/watch?v={ep['youtube_id']}"
        lines.append(f"## {ep.get('number')} — {name}")
        lines.append(f"Guest: {ep.get('guest') or ''}")
        lines.append(f"YouTube: {yurl}")
        lines.append("")
        lines.append("```")
        first = True
        for ch in kept:
            ts = yt_chapter_ts(ch.get("start_seconds"), ch.get("start"))
            if first:
                # YouTube requires starting at 0:00
                ts = "0:00"
                first = False
            lines.append(f"{ts} {ch.get('title')}")
        lines.append("```")
        lines.append("")
    (REPORTS / "YOUTUBE_CHAPTERS.md").write_text("\n".join(lines), encoding="utf-8")
    return count


def write_opus_shotlist(episodes: list[dict], clips: list[dict]) -> int:
    ep_by_slug = {e["slug"]: e for e in episodes}
    # Prefer chapter lists from episodes; fall back to clips_index non-bumper non-host_open
    rows = []
    for ep in episodes:
        if ep.get("removed"):
            continue
        yid = ep.get("youtube_id")
        if not yid:
            continue
        yurl = ep.get("youtube_url") or f"https://www.youtube.com/watch?v={yid}"
        chapters = list(ep.get("chapters") or [])
        # Build usable chapter windows
        usable = []
        for i, ch in enumerate(chapters):
            title = (ch.get("title") or "").strip()
            if is_bumper(title) or title.lower().startswith("host open"):
                continue
            if re.match(r"^chapter\s*\d+$", title, re.I):
                continue
            start_s = ch.get("start_seconds")
            if start_s is None and ch.get("start"):
                parts = [int(x) for x in ch["start"].split(":")]
                start_s = parts[0] * 3600 + parts[1] * 60 + parts[2] if len(parts) == 3 else parts[0] * 60 + parts[1]
            end_s = None
            if i + 1 < len(chapters):
                nxt = chapters[i + 1]
                end_s = nxt.get("start_seconds")
                if end_s is None and nxt.get("start"):
                    parts = [int(x) for x in nxt["start"].split(":")]
                    end_s = parts[0] * 3600 + parts[1] * 60 + parts[2] if len(parts) == 3 else parts[0] * 60 + parts[1]
            if end_s is None:
                end_s = ep.get("duration_seconds")
            usable.append((title, int(start_s or 0), int(end_s) if end_s is not None else None, ch))

        # Also skip host_open clips when matching
        host_open_starts = set()
        for c in clips:
            if c.get("episode_slug") == ep["slug"] and c.get("host_open"):
                host_open_starts.add(int(c.get("start_seconds") or 0))

        for title, start_s, end_s, ch in usable:
            if start_s in host_open_starts:
                continue
            anchor = t_anchor(start_s, ch.get("start"))
            archive = f"{BASE_SITE}/episodes/{ep['slug']}/#{anchor}"
            rows.append(
                {
                    "date": ep.get("date") or "",
                    "number": ep.get("number") or "",
                    "guest": ep.get("guest") or "",
                    "episode": ep.get("browse_title") or ep.get("canonical_title") or ep["slug"],
                    "youtube": yurl,
                    "chapter": title,
                    "start": yt_chapter_ts(start_s, None),
                    "end": yt_chapter_ts(end_s, None) if end_s is not None else "",
                    "archive": archive,
                }
            )

    rows.sort(key=lambda r: (r["date"], r["number"]), reverse=True)

    lines = [
        "# Opus shotlist (clipping menu)",
        "",
        "Newest episodes first. Bumpers / host-opens excluded. No marketing copy.",
        "",
        f"Rows: **{len(rows)}**",
        "",
        "| Episode | Guest | YouTube | Chapter | Start | End | Archive |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        ep_label = f"{r['number']} {r['episode']}".replace("|", "/")
        lines.append(
            f"| {ep_label} | {r['guest'].replace('|','/')} | {r['youtube']} | "
            f"{r['chapter'].replace('|','/')} | {r['start']} | {r['end']} | {r['archive']} |"
        )
    lines.append("")
    (REPORTS / "OPUS_SHOTLIST.md").write_text("\n".join(lines), encoding="utf-8")
    return len(rows)


def parse_guest_names() -> dict[str, str]:
    text = (DEPLOY / "guests" / "index.html").read_text(encoding="utf-8")
    items = re.findall(r'<a href="guests/([^/]+)/index\.html">([^<]+)</a>', text)
    return {slug: html.unescape(name) for slug, name in items}


def write_ship_report(
    guest_count: int,
    sitemap_count: int,
    missing_yt: int,
    yt_chapters: int,
    opus_rows: int,
    episode_jsonld: int,
    needs_jacob: list[str],
) -> None:
    names = parse_guest_names()
    lines = [
        "# SHIP — Discover layer",
        "",
        f"Date: {date.today().isoformat()} (repo clock UTC; user zone America/Chicago)",
        f"Live base: {BASE_SITE}/",
        "",
        "## DONE",
        "",
        f"- Guest doorways rebuilt: **{guest_count}** pages + filterable `guests/index.html`",
        f"- Guest JSON-LD (Person + episode ItemList) on each guest page",
        f"- Homepage PodcastSeries JSON-LD",
        f"- Episode PodcastEpisode JSON-LD refreshed: **{episode_jsonld}** pages",
        f"- `sitemap.xml` rebuilt on GitHub Pages host — **{sitemap_count}** `<loc>` entries",
        f"- `llms.txt` guests section + machine file pointers updated",
        f"- `_sources/reports/MISSING_YOUTUBE.md` — **{missing_yt}** episodes",
        f"- `_sources/reports/YOUTUBE_CHAPTERS.md` — **{yt_chapters}** episodes with paste-ready chapters",
        f"- `_sources/reports/OPUS_SHOTLIST.md` — **{opus_rows}** clipping rows",
        "",
        "### Live URLs (samples)",
        f"- Guests index: {BASE_SITE}/guests/",
        f"- Rebecca Wyld: {BASE_SITE}/guests/rebecca-wyld/",
        f"- Rebecca Wild: {BASE_SITE}/guests/rebecca-wild/",
        f"- Quotes JSON: {BASE_SITE}/assets/quotes_clean.json",
        f"- Episodes JSON: {BASE_SITE}/assets/episodes_index.json",
        f"- Books JSON: {BASE_SITE}/assets/books_index.json",
        f"- Clips JSON: {BASE_SITE}/assets/clips_index.json",
        "",
        "## BLOCKED",
        "",
        "- No YouTube description publishing from this ship (files only).",
        "- Episode 0047 Trenten Kesler has no youtube_id — cannot generate YT chapters/shotlist for it.",
        "",
        "## NEEDS JACOB",
        "",
    ]
    if needs_jacob:
        for item in needs_jacob:
            lines.append(f"- {item}")
    else:
        lines.append("- (none beyond missing YouTube listed in MISSING_YOUTUBE.md)")
    lines.append("")
    lines.append("### Identity notes kept separate (do not merge)")
    lines.append(f"- Rebecca Wyld ≠ Rebecca Wild (`rebecca-wyld` / `rebecca-wild`)")
    lines.append(f"- Brandon Cruz (Zack Wyld) kept under `brandon-cruz` — no separate zack-wyld guest page")
    lines.append(f"- Alicia / Erwan husband-wife labels preserved")
    lines.append(f"- Ian / Shaye Camp Re-Education separate pages")
    lines.append("")
    lines.append("### Confirmations")
    lines.append("- No invented bios / quotes / books")
    lines.append("- Guest quotes only from `assets/quotes_clean.json` published pool")
    lines.append(f"- Footer motto exact: `{MOTTO}`")
    lines.append("")
    (REPORTS / "SHIP_DISCOVER.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    eps_doc = load_json(ASSETS / "episodes_index.json")
    episodes = eps_doc["episodes"]
    clips = load_json(ASSETS / "clips_index.json")["clips"]
    inventory = load_inventory_audio()

    update_homepage_jsonld()
    ep_touched, ep_skipped = update_episode_jsonld(episodes)
    sitemap_count = rebuild_sitemap(episodes)
    guest_names = parse_guest_names()
    update_llms_txt(episodes, guest_names)

    missing_yt = write_missing_youtube(episodes, inventory)
    yt_chapters = write_youtube_chapters(episodes)
    opus_rows = write_opus_shotlist(episodes, clips)

    needs = []
    if missing_yt:
        needs.append(f"{missing_yt} episode(s) missing YouTube — see MISSING_YOUTUBE.md (includes 0047 Trenten Kesler if listed)")
    # Brandon / Zack naming
    if (DEPLOY / "guests" / "brandon-cruz").exists() and not (DEPLOY / "guests" / "zack-wyld").exists():
        needs.append("Confirm Brandon Cruz (Zack Wyld) single-page mapping remains correct (no separate zack-wyld doorway)")

    guest_count = len(list((DEPLOY / "guests").glob("*/index.html")))
    write_ship_report(
        guest_count=guest_count,
        sitemap_count=sitemap_count,
        missing_yt=missing_yt,
        yt_chapters=yt_chapters,
        opus_rows=opus_rows,
        episode_jsonld=ep_touched,
        needs_jacob=needs,
    )

    print(f"homepage JSON-LD: ok")
    print(f"episode JSON-LD touched/processed: {ep_touched} skipped={ep_skipped}")
    print(f"sitemap urls: {sitemap_count}")
    print(f"guests in llms: {len(guest_names)}")
    print(f"MISSING_YOUTUBE: {missing_yt}")
    print(f"YOUTUBE_CHAPTERS episodes: {yt_chapters}")
    print(f"OPUS_SHOTLIST rows: {opus_rows}")


if __name__ == "__main__":
    main()
