#!/usr/bin/env python3
"""Add Listen by mood + Chapter radio to the archive deploy tree.
No git commit/push — parent deploys.
Uses only existing chapters/quotes from episodes_index.
"""
from __future__ import annotations

import html as htmlmod
import json
import re
import shutil
from pathlib import Path

ROOT = Path("/workspace/junkyard-love-archive-deploy")
SRC = ROOT / "_sources"
REMOVED = {"0001", "0014", "0016", "0029"}

HEADER_HTML = """<header class="site">
  <div class="header-row">
    <a class="brand" href="index.html">The Junkyard Love Podcast</a>
    <button type="button" class="theme-toggle" data-theme-toggle aria-label="Toggle light and dark mode">Light</button>
  </div>
    <nav class="nav-main" aria-label="Primary">
    <a href="index.html">Home</a>
    <a href="radio/index.html">Chapter radio</a>
    <a href="topics/index.html">Topics</a>
    <a href="guests/index.html">Guests</a>
    <a href="episodes/index.html">Episodes</a>
    <a href="books/index.html">Books</a>
    <a href="moods/index.html">Moods</a>
    <a href="search/index.html">Search</a>
    <a href="listen/index.html">Listen</a>
    <a href="donate/index.html">Donate</a>
    <a href="https://www.instagram.com/jacobfromtheinternet/" target="_blank" rel="noopener">Instagram</a>
  </nav>
</header>"""

FOOTER_HTML = """<footer class="site">
  <p class="motto">drink some water, stretch, love yourselves.</p>
  <p class="footer-links">
    <a href="donate/index.html">Donate</a>
    ·
    <a href="merch/index.html">Merch</a>
    ·
    <a href="https://www.instagram.com/jacobfromtheinternet/" target="_blank" rel="noopener">Instagram</a>
  </p>
</footer>"""

SCRIPTS = """<script src="assets/theme.js" defer></script>
<script src="assets/archive.js" defer></script>"""

PAGE_SHELL_HEAD = """<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<base href="/junkyard-love-archive/">
<script>(function(){{try{{var t=localStorage.getItem("jylp-theme");if(t==="light"||t==="dark")document.documentElement.setAttribute("data-theme",t);}}catch(e){{}}}})();</script>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="stylesheet" href="assets/style.css">
<link rel="canonical" href="{canonical}">
</head>
<body>
<div class="wrap">
{header}
"""

PAGE_SHELL_TAIL = """
{footer}
</div>
{scripts}
</body>
</html>
"""


def esc(s: str) -> str:
    return htmlmod.escape(s or "", quote=True)


def esc_text(s: str) -> str:
    return htmlmod.escape(s or "", quote=False)


def parse_ts(t: str | int | float | None) -> int:
    if t is None:
        return 0
    if isinstance(t, (int, float)):
        return int(t)
    t = str(t).strip().strip("[]")
    parts = [int(x) for x in t.split(":")]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    return parts[0] if parts else 0


def fmt_human(sec: int) -> str:
    sec = max(0, int(sec))
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def fmt_hash(sec: int) -> str:
    sec = max(0, int(sec))
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"#t-{h:02d}-{m:02d}-{s:02d}"


def is_bumper(title: str) -> bool:
    t = (title or "").lower().strip()
    if not t:
        return True
    if re.match(r"^(intro|outro|opening|closing|end credits|credits|theme|bumper)\b", t):
        return True
    if "welcome to the junkyard love" in t and len(t) < 55:
        return True
    return False


def load_index() -> dict:
    return json.loads((SRC / "episodes_index.json").read_text(encoding="utf-8"))


def load_moods() -> dict:
    return json.loads((SRC / "mood_doors.json").read_text(encoding="utf-8"))


def load_radio() -> dict:
    return json.loads((SRC / "radio_sets.json").read_text(encoding="utf-8"))


def ep_by_slug(index: dict) -> dict:
    return {e["slug"]: e for e in index["episodes"] if e.get("slug")}


def resolve_chapter(ep: dict, chapter_time: str, chapter_title: str | None = None):
    want = parse_ts(chapter_time)
    chs = ep.get("chapters") or []
    for i, ch in enumerate(chs):
        start = parse_ts(ch.get("start_seconds", ch.get("start")))
        if start == want:
            if chapter_title and ch.get("title") != chapter_title:
                # time wins; title should already be synced
                pass
            return ch, i
    if chapter_title:
        for i, ch in enumerate(chs):
            if ch.get("title") == chapter_title:
                return ch, i
    return None, -1


def nearest_quote(ep: dict, start_sec: int, end_sec: int):
    best = None
    best_dist = 10**9
    for q in ep.get("quotes") or []:
        t = parse_ts(q.get("t_seconds", q.get("t")))
        if start_sec <= t < end_sec:
            return q
        dist = abs(t - start_sec)
        if dist < best_dist and (start_sec - 30) <= t <= (end_sec + 30):
            best_dist = dist
            best = q
    return best


def chapter_end(ep: dict, idx: int, start_sec: int) -> int:
    chs = ep.get("chapters") or []
    if 0 <= idx < len(chs) - 1:
        return parse_ts(chs[idx + 1].get("start_seconds", chs[idx + 1].get("start")))
    dur = ep.get("duration_seconds")
    if dur:
        return int(dur)
    return start_sec + 120


def clip_card_html(ep: dict, ch: dict, idx: int, *, show_duration: bool = False) -> str:
    start = parse_ts(ch.get("start_seconds", ch.get("start")))
    end = chapter_end(ep, idx, start)
    dur = max(0, end - start)
    quote = nearest_quote(ep, start, end)
    guest = "Solo" if ep.get("is_solo") else (ep.get("guest") or "Guest")
    title = ep.get("browse_title") or ep.get("canonical_title") or ""
    ep_url = ep.get("url") or f"episodes/{ep['slug']}/index.html"
    hash_ = fmt_hash(start)
    yt = None
    if ep.get("youtube_id"):
        yt = f"https://www.youtube.com/watch?v={ep['youtube_id']}&t={start}s"

    meta = f"{esc_text(title)} · Episode {esc_text(ep.get('number', ''))} · {esc_text(guest)} · starts {esc_text(fmt_human(start))}"
    if show_duration and dur >= 45:
        meta += f" · {esc_text(fmt_human(dur))}"

    html = (
        f'<div class="clip-card">'
        f"<h3>{esc_text(ch.get('title', ''))}</h3>"
        f'<p class="clip-ep">{meta}</p>'
    )
    if quote and quote.get("text"):
        text = re.sub(r'^["“]|["”]$', "", quote["text"])
        sp = quote.get("speaker") or ""
        html += (
            f'<p class="clip-quote">'
            + (f"{esc_text(sp)}: " if sp else "")
            + f"“{esc_text(text)}”</p>"
        )
    html += '<div class="btn-row">'
    html += f'<a href="{esc(ep_url + hash_)}">Open at this chapter</a>'
    html += f'<a class="secondary" href="{esc(ep_url)}">Full episode</a>'
    if yt:
        html += (
            f'<a class="secondary" href="{esc(yt)}" target="_blank" rel="noopener">'
            f"YouTube at time</a>"
        )
    html += "</div></div>"
    return html


def write_page(rel: str, title: str, body: str):
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    # Absolute canonical (slash form)
    if rel == "index.html":
        canon = "https://junkyardlovejakesbot.github.io/junkyard-love-archive/"
    elif rel.endswith("/index.html"):
        folder = rel[: -len("/index.html")]
        canon = f"https://junkyardlovejakesbot.github.io/junkyard-love-archive/{folder}/"
    else:
        canon = f"https://junkyardlovejakesbot.github.io/junkyard-love-archive/{rel}"
    html = (
        PAGE_SHELL_HEAD.format(title=esc_text(title), header=HEADER_HTML, canonical=canon)
        + body
        + PAGE_SHELL_TAIL.format(footer=FOOTER_HTML, scripts=SCRIPTS)
    )
    path.write_text(html, encoding="utf-8")


def copy_assets_json():
    for name in ("mood_doors.json", "radio_sets.json"):
        shutil.copy2(SRC / name, ROOT / "assets" / name)


def patch_nav_sitewide():
    """Ensure Chapter radio link exists in every page header."""
    count = 0
    for path in ROOT.rglob("*.html"):
        if "_sources" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        orig = text
        # Replace whole header block with updated HEADER_HTML
        text2, n = re.subn(
            r"<header class=\"site\">.*?</header>",
            HEADER_HTML,
            text,
            count=1,
            flags=re.S,
        )
        if n:
            text = text2
        elif "radio/index.html" not in text and 'class="nav-main"' in text:
            text = text.replace(
                '<a href="topics/index.html">Topics</a>',
                '<a href="topics/index.html">Topics</a>\n    <a href="radio/index.html">Chapter radio</a>',
                1,
            )
        if text != orig:
            path.write_text(text, encoding="utf-8")
            count += 1
    return count


def patch_homepage(moods: dict):
    path = ROOT / "index.html"
    text = path.read_text(encoding="utf-8")

    mood_section = """
<h2>Listen by mood</h2>
<p class="note">not a diagnosis. just a door.</p>
<div id="mood-doors" class="mood-doors" data-mood-doors>
"""
    for door in moods["doors"]:
        mood_section += (
            f'  <a class="mood-chip" href="moods/{esc(door["slug"])}/index.html" '
            f'data-mood="{esc(door["slug"])}">{esc_text(door["label"])}</a>\n'
        )
    mood_section += """</div>
<div id="mood-results" class="mood-results" data-mood-results></div>

"""

    # Restructure: Random+Shuffle only in action-row; mood before Pick a clip
    # Current pattern has Pick a clip button in action-row — move section after mood.
    new_action = """<div class="action-row">
  <a class="btn" href="#" data-random-episode>Random episode</a>
  <a class="btn secondary" href="#" data-shuffle-clip>Shuffle a clip</a>
</div>
<div id="shuffle-result"></div>
"""

    # Replace action-row through Pick a clip header
    pattern = re.compile(
        r'<div class="action-row">.*?</div>\s*<div id="shuffle-result"></div>\s*'
        r'(?:<h2>Pick a clip</h2>.*?<div id="clip-results"></div>)?',
        re.S,
    )
    pick_block = """<h2>Pick a clip</h2>
<p class="note">Keyword phrases drawn from chapter titles and topics — click for a few chapter deep-links. <a href="clips/index.html">Open Pick a clip</a></p>
<div class="phrase-cloud" data-phrase-cloud></div>
<div id="clip-results"></div>"""

    replacement = new_action + "\n" + mood_section + pick_block
    text2, n = pattern.subn(replacement, text, count=1)
    if not n:
        # fallback: insert mood before Pick a clip h2
        if "Listen by mood" not in text:
            text2 = text.replace(
                "<h2>Pick a clip</h2>",
                mood_section + "<h2>Pick a clip</h2>",
                1,
            )
        else:
            text2 = text
    # If mood already present from prior run, rewrite mood block
    if "Listen by mood" in text2 and "data-mood-doors" in text2:
        text2 = re.sub(
            r"<h2>Listen by mood</h2>.*?<div id=\"mood-results\"[^>]*>.*?</div>",
            mood_section.strip(),
            text2,
            count=1,
            flags=re.S,
        )
    path.write_text(text2, encoding="utf-8")


def build_mood_pages(index: dict, moods: dict):
    by = ep_by_slug(index)
    for door in moods["doors"]:
        cards = []
        for ref in door["chapters"][:3]:
            ep = by.get(ref["slug"])
            if not ep or ep.get("number") in REMOVED or ep.get("removed"):
                continue
            ch, idx = resolve_chapter(ep, ref["chapter_time"], ref.get("chapter_title"))
            if not ch:
                continue
            cards.append(clip_card_html(ep, ch, idx))
        body = f"""
<h1>{esc_text(door["label"])}</h1>
<p class="note">not a diagnosis. just a door. · <a href="index.html#mood-doors">All mood doors</a></p>
<div class="mood-results">
{"".join(cards) if cards else '<p class="search-empty">No chapters mapped yet.</p>'}
</div>
<p class="note"><a href="radio/index.html">Chapter radio</a> · <a href="clips/index.html">Pick a clip</a></p>
"""
        write_page(
            f"moods/{door['slug']}/index.html",
            f"{door['label']} — Listen by mood — The Junkyard Love Podcast",
            body,
        )


def usable_chapters(ep: dict):
    chs = ep.get("chapters") or []
    out = []
    for i, ch in enumerate(chs):
        if is_bumper(ch.get("title") or ""):
            continue
        title = (ch.get("title") or "").strip()
        if not title or re.match(r"^chapter\s*\d+$", title, re.I):
            continue
        start = parse_ts(ch.get("start_seconds", ch.get("start")))
        end = chapter_end(ep, i, start)
        dur = end - start
        if dur < 45 and i < len(chs) - 1:
            continue
        out.append((ch, i, dur))
    return out


def radio_row_html(ep: dict, ch: dict, idx: int, dur: int) -> str:
    start = parse_ts(ch.get("start_seconds", ch.get("start")))
    guest = "Solo" if ep.get("is_solo") else (ep.get("guest") or "Guest")
    title = ep.get("browse_title") or ep.get("canonical_title") or ""
    ep_url = ep.get("url") or f"episodes/{ep['slug']}/index.html"
    hash_ = fmt_hash(start)
    yt = None
    if ep.get("youtube_id"):
        yt = f"https://www.youtube.com/watch?v={ep['youtube_id']}&t={start}s"
    dur_bit = f" · {esc_text(fmt_human(dur))}" if dur >= 45 else ""
    html = (
        f'<div class="clip-card radio-row" data-radio-row '
        f'data-slug="{esc(ep["slug"])}" data-time="{esc(fmt_human(start).replace(":", "-") if False else ch.get("start", ""))}">'
        f"<h3>{esc_text(ch.get('title', ''))}</h3>"
        f'<p class="clip-ep">{esc_text(title)} · Episode {esc_text(ep.get("number", ""))} · '
        f'{esc_text(guest)} · starts {esc_text(fmt_human(start))}{dur_bit}</p>'
        f'<div class="btn-row">'
        f'<a href="{esc(ep_url + hash_)}">Open at this chapter</a>'
        f'<a class="secondary" href="{esc(ep_url)}">Full episode</a>'
    )
    if yt:
        html += (
            f'<a class="secondary" href="{esc(yt)}" target="_blank" rel="noopener">'
            f"YouTube at time</a>"
        )
    html += "</div></div>"
    return html


def build_radio_page(index: dict, radio: dict):
    by = ep_by_slug(index)
    # Set chips
    chips = '<div class="mood-doors radio-sets" data-radio-sets>\n'
    chips += '  <button type="button" class="mood-chip" data-radio-set="all" aria-pressed="true">All chapters</button>\n'
    for s in radio["sets"]:
        chips += (
            f'  <button type="button" class="mood-chip" data-radio-set="{esc(s["slug"])}">'
            f'{esc_text(s["label"])}</button>\n'
        )
    chips += "</div>\n"

    # Pre-rendered set playlists (hidden; JS shows one)
    set_blocks = ""
    for s in radio["sets"]:
        rows = []
        for ref in s["chapters"]:
            ep = by.get(ref["slug"])
            if not ep or ep.get("number") in REMOVED or ep.get("removed"):
                continue
            ch, idx = resolve_chapter(ep, ref["chapter_time"], ref.get("chapter_title"))
            if not ch:
                continue
            start = parse_ts(ch.get("start_seconds", ch.get("start")))
            dur = chapter_end(ep, idx, start) - start
            rows.append(radio_row_html(ep, ch, idx, dur))
        set_blocks += (
            f'<div class="radio-playlist" data-radio-playlist="{esc(s["slug"])}" hidden>\n'
            + "".join(rows)
            + "</div>\n"
        )

    # Full scrolling playlist from shuffle pool
    all_rows = []
    for ep in index["episodes"]:
        if ep.get("number") in REMOVED or ep.get("removed"):
            continue
        for ch, idx, dur in usable_chapters(ep):
            all_rows.append(radio_row_html(ep, ch, idx, dur))

    body = f"""
<h1>Chapter radio</h1>
<p class="note">named chapters from the long conversations. not a highlight reel we invented.</p>
<p class="note">Guided index only — open a chapter when you want. No autoplay chain.</p>
{chips}
<div class="radio-playlist" data-radio-playlist="all">
{"".join(all_rows)}
</div>
{set_blocks}
<p class="note"><a href="index.html">Home</a> · <a href="clips/index.html">Pick a clip</a></p>
"""
    write_page("radio/index.html", "Chapter radio — The Junkyard Love Podcast", body)
    return len(all_rows), {s["slug"]: len(s["chapters"]) for s in radio["sets"]}


def update_sitemap(moods: dict):
    path = ROOT / "sitemap.xml"
    text = path.read_text(encoding="utf-8")
    base = "https://junkyardlovejakesbot.github.io/junkyard-love-archive"
    urls = [f"{base}/radio/"] + [f"{base}/moods/{d['slug']}/" for d in moods["doors"]]
    for u in urls:
        if u not in text:
            text = text.replace(
                "</urlset>",
                f"  <url><loc>{u}</loc></url>\n</urlset>",
                1,
            )
    path.write_text(text, encoding="utf-8")


def patch_build_ui_redesign_header():
    """Keep future redesign rebuilds in sync with Chapter radio nav + mood slot."""
    path = SRC / "build_ui_redesign.py"
    text = path.read_text(encoding="utf-8")
    if "radio/index.html" not in text:
        text = text.replace(
            '    <a href="topics/index.html">Topics</a>\n'
            '    <a href="search/index.html">Search</a>',
            '    <a href="topics/index.html">Topics</a>\n'
            '    <a href="radio/index.html">Chapter radio</a>\n'
            '    <a href="search/index.html">Search</a>',
        )
        path.write_text(text, encoding="utf-8")

    # Also patch homepage builder action-row / mood insertion point if present
    text = path.read_text(encoding="utf-8")
    old_action = '''<div class="action-row">
  <a class="btn" href="#" data-random-episode>Random episode</a>
  <a class="btn secondary" href="#" data-shuffle-clip>Shuffle a clip</a>
  <a class="btn secondary" href="clips/index.html">Pick a clip</a>
</div>
<div id="shuffle-result"></div>

<h2>Pick a clip</h2>
<p class="note">Keyword phrases drawn from chapter titles and topics — click for a few chapter deep-links.</p>
<div class="phrase-cloud" data-phrase-cloud></div>
<div id="clip-results"></div>'''
    new_action = '''<div class="action-row">
  <a class="btn" href="#" data-random-episode>Random episode</a>
  <a class="btn secondary" href="#" data-shuffle-clip>Shuffle a clip</a>
</div>
<div id="shuffle-result"></div>

<h2>Listen by mood</h2>
<p class="note">not a diagnosis. just a door.</p>
<div class="mood-doors" data-mood-doors></div>
<div id="mood-results" class="mood-results" data-mood-results></div>

<h2>Pick a clip</h2>
<p class="note">Keyword phrases drawn from chapter titles and topics — click for a few chapter deep-links. <a href="clips/index.html">Open Pick a clip</a></p>
<div class="phrase-cloud" data-phrase-cloud></div>
<div id="clip-results"></div>'''
    if old_action in text:
        path.write_text(text.replace(old_action, new_action), encoding="utf-8")


def write_notes(mood_counts: dict, radio_sizes: dict, playlist_n: int, nav_n: int):
    notes = SRC / "reports" / "MOOD_RADIO_NOTES.md"
    lines = [
        "# Mood doors + Chapter radio",
        "",
        "Generated by `_sources/build_mood_radio.py` (no git commit/push — parent deploys).",
        "",
        "## Features",
        "",
        "- **Listen by mood** on homepage (after Random / Shuffle, before Pick a clip).",
        "- Subline exact: `not a diagnosis. just a door.`",
        "- Six mood doors → up to 3 existing chapter cards each; mappings in `_sources/mood_doors.json` / `assets/mood_doors.json`.",
        "- Mood pages: `moods/<slug>/index.html`.",
        "- **Chapter radio** at `radio/index.html` — scrolling named-chapter playlist (same pool as Shuffle a clip: skip Intro/Outro, prefer ≥~45s).",
        "- Optional starter sets in `_sources/radio_sets.json` / `assets/radio_sets.json`: Body, Armor down, Opened, Second chances.",
        "- Nav: **Chapter radio** next to Topics site-wide.",
        "- Deep-links: episode `#t-HH-MM-SS` + YouTube `&t=` seconds when youtube_id exists. No autoplay.",
        "- Footer motto unchanged. Dark mode default. Base href `/junkyard-love-archive/`.",
        "",
        "## Mood door chapter counts",
        "",
    ]
    for slug, n in mood_counts.items():
        lines.append(f"- `{slug}`: {n}")
    lines += ["", "## Radio sets", ""]
    for slug, n in radio_sizes.items():
        lines.append(f"- `{slug}`: {n}")
    lines += [
        "",
        f"- Full chapter playlist rows: {playlist_n}",
        f"- HTML pages with nav patched this run: {nav_n}",
        "",
        "## Guardrails",
        "",
        "- No invented moods, summaries, medical claims, or clip titles.",
        "- No “recommended for depression” / disorder / treatment language.",
        "- Skips Removed placeholders 0001/0014/0016/0029.",
        "- Quotes on cards only when already in-range in episodes_index.",
        "",
    ]
    notes.write_text("\n".join(lines), encoding="utf-8")

    # Short append to UI redesign notes
    ui = SRC / "reports" / "UI_REDESIGN_NOTES.md"
    if ui.exists():
        t = ui.read_text(encoding="utf-8")
        marker = "## Mood doors + Chapter radio"
        add = (
            f"{marker}\n\n"
            "See `MOOD_RADIO_NOTES.md`. Homepage gains Listen by mood; `radio/` + `moods/` pages; "
            "Chapter radio in nav. Curated from existing chapters only.\n"
        )
        if marker not in t:
            t = t.rstrip() + "\n\n" + add
            ui.write_text(t, encoding="utf-8")


def main():
    index = load_index()
    moods = load_moods()
    radio = load_radio()

    # Validate mappings resolve
    by = ep_by_slug(index)
    mood_counts = {}
    for door in moods["doors"]:
        n = 0
        for ref in door["chapters"]:
            ep = by.get(ref["slug"])
            assert ep, f"missing ep {ref['slug']}"
            ch, _ = resolve_chapter(ep, ref["chapter_time"], ref.get("chapter_title"))
            assert ch, f"missing chapter {ref}"
            n += 1
        mood_counts[door["slug"]] = n

    copy_assets_json()
    patch_build_ui_redesign_header()
    build_mood_pages(index, moods)
    playlist_n, radio_sizes = build_radio_page(index, radio)
    patch_homepage(moods)
    nav_n = patch_nav_sitewide()
    update_sitemap(moods)
    write_notes(mood_counts, radio_sizes, playlist_n, nav_n)

    print("mood_counts", mood_counts)
    print("radio_sizes", radio_sizes)
    print("playlist_rows", playlist_n)
    print("nav_patched", nav_n)


if __name__ == "__main__":
    main()
