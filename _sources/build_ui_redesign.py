#!/usr/bin/env python3
"""Generate episodes_index.json and apply quiet long-form archive UI redesign.
No git commit/push — parent deploys.
"""
from __future__ import annotations

import html as htmlmod
import json
import random
import re
import shutil
from collections import Counter, defaultdict
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path("/workspace/junkyard-love-archive-deploy")
MIRROR = Path("/workspace/junkyard-love-archive")
REMOVED = {"0001", "0014", "0016", "0029"}
SHOW = {
    "youtube_channel": "https://www.youtube.com/@TheJunkyardLovePodcast",
    "spotify_show": "https://open.spotify.com/show/45J7CBdM8j29doqyBp2bFs",
    "apple_show": "https://podcasts.apple.com/us/podcast/the-junkyard-love-podcast/id1489118788",
    "instagram": "https://www.instagram.com/jacobfromtheinternet/",
}

HEADER_HTML = """<header class="site">
  <div class="header-row">
    <a class="brand" href="index.html">The Junkyard Love Podcast</a>
    <button type="button" class="theme-toggle" data-theme-toggle aria-label="Toggle light and dark mode">Light</button>
  </div>
  <nav class="nav-main" aria-label="Primary">
    <a href="index.html">Home</a>
    <a href="start-here/index.html">Start here</a>
    <a href="episodes/index.html">Episodes</a>
    <a href="guests/index.html">Guests</a>
    <a href="topics/index.html">Topics</a>
    <a href="radio/index.html">Chapter radio</a>
    <a href="search/index.html">Search</a>
    <a href="listen/index.html">Listen</a>
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


def youtube_id(url: str | None) -> str | None:
    if not url:
        return None
    m = re.search(
        r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/shorts/)([A-Za-z0-9_-]{6,})",
        url,
    )
    return m.group(1) if m else None


def parse_ts_to_seconds(t: str) -> int:
    t = (t or "").strip().strip("[]")
    parts = t.split(":")
    try:
        nums = [int(p) for p in parts]
    except ValueError:
        return 0
    if len(nums) == 3:
        return nums[0] * 3600 + nums[1] * 60 + nums[2]
    if len(nums) == 2:
        return nums[0] * 60 + nums[1]
    if len(nums) == 1:
        return nums[0]
    return 0


def fmt_hash_ts(seconds: int) -> str:
    seconds = max(0, int(seconds))
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}-{m:02d}-{s:02d}"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def map_content_dirs() -> dict[str, Path]:
    """Map episode_number -> content dir path."""
    content_root = ROOT / "_sources" / "content"
    by_num: dict[str, Path] = {}
    # Prefer numbered folders
    for p in content_root.iterdir():
        if not p.is_dir():
            continue
        m = re.match(r"^(\d{4})", p.name)
        if m:
            by_num[m.group(1)] = p
    # Fill gaps via meta episode_number or youtube match later
    for p in content_root.iterdir():
        if not p.is_dir():
            continue
        meta_path = p / "meta.json"
        if not meta_path.exists():
            continue
        meta = load_json(meta_path)
        num = meta.get("episode_number")
        if num and str(num).zfill(4) not in by_num:
            by_num[str(num).zfill(4)] = p
    return by_num


def extract_chapters_from_html(html: str) -> list[dict]:
    chapters = []
    # Prefer published chapters ul
    m = re.search(r'<ul class="chapters">(.*?)</ul>', html, re.S)
    block = m.group(1) if m else ""
    if not block:
        m2 = re.search(r'<ul class="archive-chapters">(.*?)</ul>', html, re.S)
        block = m2.group(1) if m2 else ""
    for li in re.finditer(
        r'<li>\s*<a href="#t-(\d{2})-(\d{2})-(\d{2})"\[?>?\s*([^<]*)</a>\s*—\s*(.*?)</li>',
        block,
        re.S,
    ):
        h, mi, s = int(li.group(1)), int(li.group(2)), int(li.group(3))
        title = re.sub(r"<[^>]+>", "", li.group(5)).strip()
        title = htmlmod.unescape(title)
        start = f"{h:02d}:{mi:02d}:{s:02d}"
        chapters.append(
            {
                "start": start,
                "start_seconds": h * 3600 + mi * 60 + s,
                "title": title,
            }
        )
    if chapters:
        return chapters
    # Fallback looser
    for li in re.finditer(
        r'href="#t-(\d{2})-(\d{2})-(\d{2})"[^>]*>.*?</a>\s*—\s*([^<]+)',
        block or html,
        re.S,
    ):
        h, mi, s = int(li.group(1)), int(li.group(2)), int(li.group(3))
        title = htmlmod.unescape(li.group(4).strip())
        chapters.append(
            {
                "start": f"{h:02d}:{mi:02d}:{s:02d}",
                "start_seconds": h * 3600 + mi * 60 + s,
                "title": title,
            }
        )
    return chapters


def extract_quotes_from_html(html: str) -> list[dict]:
    quotes = []
    for bq in re.finditer(
        r'<blockquote class="archive-quote">(.*?)</blockquote>', html, re.S
    ):
        chunk = bq.group(1)
        tm = re.search(r"#t-(\d{2})-(\d{2})-(\d{2})", chunk)
        sm = re.search(r'<span class="speaker">([^<]+)</span>', chunk)
        # text after speaker or after timestamp link
        text = re.sub(r"<[^>]+>", "", chunk)
        text = htmlmod.unescape(text)
        text = re.sub(r"^\[\d{1,2}:\d{2}(?::\d{2})?\]\s*", "", text)
        if sm:
            speaker = htmlmod.unescape(sm.group(1)).rstrip(":")
            text = re.sub(re.escape(speaker) + r":?\s*", "", text, count=1)
        else:
            speaker = ""
        text = text.strip().strip("“”\"")
        if not text:
            continue
        t_seconds = 0
        t_str = ""
        if tm:
            t_seconds = int(tm.group(1)) * 3600 + int(tm.group(2)) * 60 + int(tm.group(3))
            t_str = f"{int(tm.group(1)):02d}:{int(tm.group(2)):02d}:{int(tm.group(3)):02d}"
        quotes.append(
            {"t": t_str, "t_seconds": t_seconds, "speaker": speaker, "text": text}
        )
    return quotes


def extract_meta_from_episode_html(html: str) -> dict:
    out = {}
    ym = re.search(r"youtube\.com/watch\?v=([A-Za-z0-9_-]+)", html)
    if ym:
        out["youtube_id"] = ym.group(1)
        out["youtube_url"] = f"https://www.youtube.com/watch?v={ym.group(1)}"
    mm = re.search(
        r'class="meta">Episode\s+(\d{4})\s*·\s*([^·]+)\s*·\s*([^·]+)\s*·\s*(?:Guest:\s*)?(.*?)</p>',
        html,
        re.S,
    )
    if mm:
        out["number"] = mm.group(1)
        out["date"] = mm.group(2).strip()
        out["duration"] = mm.group(3).strip()
        guest = re.sub(r"<[^>]+>", "", mm.group(4)).strip()
        out["guest"] = htmlmod.unescape(guest)
    sm = re.search(r'href="(https://open\.spotify\.com/show/[^"]+)"', html)
    if sm:
        out["spotify_show"] = sm.group(1)
    am = re.search(r'href="(https://podcasts\.apple\.com/[^"]+)"', html)
    if am:
        out["apple_show"] = am.group(1)
    rm = re.search(r'href="(https://share\.transistor\.fm/[^"]+)"', html)
    if rm:
        out["rss_url"] = rm.group(1)
    return out


def duration_to_seconds(d: str | int | None) -> int:
    if d is None:
        return 0
    if isinstance(d, int):
        return d
    d = str(d).strip()
    if d.isdigit():
        return int(d)
    parts = d.split(":")
    try:
        nums = [int(p) for p in parts]
    except ValueError:
        return 0
    if len(nums) == 3:
        return nums[0] * 3600 + nums[1] * 60 + nums[2]
    if len(nums) == 2:
        return nums[0] * 60 + nums[1]
    return 0


def build_index() -> dict:
    browse = load_json(ROOT / "_sources" / "browse_titles.json")
    topics = load_json(ROOT / "_sources" / "topics.json")
    content_by_num = map_content_dirs()

    # topic membership by slug
    topic_for_slug: dict[str, list[dict]] = defaultdict(list)
    topic_meta = {}
    for cat in topics.get("categories", []):
        topic_meta[cat["slug"]] = {"slug": cat["slug"], "title": cat["title"], "blurb": cat.get("blurb", "")}
        for ep in cat.get("episodes", []):
            topic_for_slug[ep["slug"]].append(
                {"slug": cat["slug"], "title": cat["title"]}
            )

    solo_slugs = {
        e["slug"]
        for cat in topics.get("categories", [])
        if cat["slug"] == "host-solocasts"
        for e in cat.get("episodes", [])
    }

    # youtube map from inventory
    inv_yt = {}
    inv_path = ROOT / "inventory.csv"
    if inv_path.exists():
        import csv

        with inv_path.open(encoding="utf-8") as f:
            for row in csv.DictReader(f):
                num = (row.get("episode_number") or "").zfill(4)
                inv_yt[num] = row

    # also map unnumbered content by youtube id
    content_by_yt = {}
    for p in (ROOT / "_sources" / "content").iterdir():
        if not p.is_dir():
            continue
        mp = p / "meta.json"
        if not mp.exists():
            continue
        meta = load_json(mp)
        yid = youtube_id(meta.get("youtube_url"))
        if yid:
            content_by_yt[yid] = p

    episodes = []
    for slug, bt in browse.items():
        num = str(bt.get("episode_number") or slug[:4]).zfill(4)
        if num in REMOVED:
            continue
        ep_dir = ROOT / "episodes" / slug
        html_path = ep_dir / "index.html"
        if not html_path.exists():
            continue
        html = html_path.read_text(encoding="utf-8")
        from_html = extract_meta_from_episode_html(html)

        content_dir = content_by_num.get(num)
        meta = {}
        if content_dir and (content_dir / "meta.json").exists():
            meta = load_json(content_dir / "meta.json")
        # try youtube match
        yid = youtube_id(meta.get("youtube_url")) or from_html.get("youtube_id")
        if not content_dir and yid and yid in content_by_yt:
            content_dir = content_by_yt[yid]
            meta = load_json(content_dir / "meta.json")
            yid = youtube_id(meta.get("youtube_url")) or yid

        inv = inv_yt.get(num, {})
        if not yid:
            yid = youtube_id(inv.get("youtube_url"))

        guest = (
            bt.get("guest")
            or meta.get("guest")
            or from_html.get("guest")
            or inv.get("guest_name")
            or ""
        )
        duration = (
            meta.get("duration_human")
            or from_html.get("duration")
            or inv.get("duration")
            or ""
        )
        duration_seconds = (
            meta.get("duration_seconds")
            or duration_to_seconds(inv.get("duration_seconds") or duration)
        )
        date = meta.get("datePublished") or from_html.get("date") or inv.get("publish_date") or ""

        is_solo = slug in solo_slugs or re.search(r"\bsolo\b", guest, re.I) is not None

        keywords = []
        # light keywords from topic titles + chapter words later
        for t in topic_for_slug.get(slug, []):
            keywords.extend(re.findall(r"[A-Za-z]{4,}", t["title"].lower()))

        chapters = extract_chapters_from_html(html)
        quotes = extract_quotes_from_html(html)

        ep = {
            "slug": slug,
            "number": num,
            "browse_title": bt.get("browse_title") or "",
            "canonical_title": bt.get("canonical_title") or meta.get("title") or "",
            "guest": guest,
            "duration": duration,
            "duration_seconds": int(duration_seconds or 0),
            "date": date,
            "youtube_id": yid,
            "youtube_url": meta.get("youtube_url")
            or from_html.get("youtube_url")
            or (f"https://www.youtube.com/watch?v={yid}" if yid else None),
            "spotify_show": meta.get("spotify_show")
            or from_html.get("spotify_show")
            or SHOW["spotify_show"],
            "apple_show": meta.get("apple_show")
            or from_html.get("apple_show")
            or SHOW["apple_show"],
            "rss_url": meta.get("rss_url") or from_html.get("rss_url"),
            "topics": topic_for_slug.get(slug, []),
            "chapters": chapters,
            "quotes": quotes,
            "keywords": sorted(set(keywords))[:40],
            "is_solo": bool(is_solo),
            "url": f"episodes/{slug}/index.html",
            "removed": False,
        }
        episodes.append(ep)

    episodes.sort(key=lambda e: e["number"], reverse=True)

    clip_phrases = build_clip_phrases(episodes, topics)
    index = {
        "show": SHOW,
        "removed": sorted(REMOVED),
        "generated": "ui-redesign",
        "episode_count": len(episodes),
        "episodes": episodes,
        "topics": [topic_meta[c["slug"]] | {"count": len(c.get("episodes", []))} for c in topics.get("categories", [])],
        "clip_phrases": clip_phrases,
    }
    return index


def build_clip_phrases(episodes: list[dict], topics: dict) -> list[str]:
    """Build 24–40 phrases ONLY from chapter titles + existing keywords/topics."""
    # Seed from topic short labels (existing titles, shortened for UI)
    seeds = [
        "breath",
        "father",
        "surrender",
        "healing",
        "masculinity",
        "trauma",
        "meditation",
        "anxiety",
        "sobriety",
        "love",
        "money",
        "music",
        "awakening",
        "body",
        "second chances",
        "nervous system",
        "grief",
        "ego",
        "belonging",
        "prison",
        "creativity",
        "depression",
        "intuition",
        "frequency",
        "relationship",
        "identity",
        "vulnerability",
        "practice",
        "courage",
        "peace",
    ]
    # Extract meaningful bigrams/phrases from chapter titles
    title_words = Counter()
    phrases = []
    stop = {
        "the", "and", "with", "from", "that", "this", "your", "into", "about",
        "what", "when", "how", "for", "are", "you", "our", "his", "her", "their",
        "episode", "junkyard", "love", "podcast", "guest", "welcome", "opening",
        "intro", "outro", "part", "why", "who", "where", "being", "having",
    }
    for ep in episodes:
        for ch in ep.get("chapters") or []:
            title = ch.get("title") or ""
            # keep short chapter-derived phrases (3–6 words) if they look real
            words = re.findall(r"[A-Za-z][A-Za-z'-]{2,}", title)
            for w in words:
                lw = w.lower()
                if lw not in stop and len(lw) > 3:
                    title_words[lw] += 1
            # pull colon / dash clauses
            for piece in re.split(r"[:/—–|-]", title):
                piece = piece.strip()
                wc = piece.split()
                if 2 <= len(wc) <= 5 and not re.match(r"(?i)^(intro|outro|welcome)", piece):
                    if sum(1 for w in wc if w.lower() not in stop) >= 2:
                        phrases.append(piece.lower())

    # topic titles as phrases (shortened)
    for cat in topics.get("categories", []):
        t = cat["title"]
        # take left side before &
        short = re.split(r"[&/]", t)[0].strip()
        if short and len(short) < 40:
            phrases.append(short.lower())

    # rank chapter-derived phrases by frequency
    phrase_counts = Counter(phrases)
    ranked = [p for p, _ in phrase_counts.most_common(80)]

    # Merge seeds that appear in chapter corpus or topics
    corpus = " ".join(
        (ch.get("title") or "") for ep in episodes for ch in (ep.get("chapters") or [])
    ).lower()
    for cat in topics.get("categories", []):
        corpus += " " + cat.get("title", "").lower() + " " + cat.get("blurb", "").lower()

    chosen = []
    seen = set()

    def add(p: str):
        p = re.sub(r"\s+", " ", p.strip().lower())
        if not p or p in seen or len(p) < 3:
            return
        # must appear in chapter titles, topic titles, or be a seed word present in corpus
        if p not in corpus and not any(w in corpus for w in p.split() if len(w) > 3):
            return
        seen.add(p)
        chosen.append(p)

    for s in seeds:
        if s in corpus or any(w in corpus for w in s.split()):
            add(s)
    for p in ranked:
        add(p)
        if len(chosen) >= 40:
            break

    # Prefer 28–36
    if len(chosen) < 24:
        for w, c in title_words.most_common(40):
            add(w)
            if len(chosen) >= 24:
                break

    return chosen[:36]


def card_html(ep: dict) -> str:
    title = ep.get("browse_title") or ep.get("canonical_title") or "Episode"
    guest = ep.get("guest") or "Solo"
    num = ep.get("number") or ""
    dur = ep.get("duration") or ""
    href = ep.get("url") or f"episodes/{ep['slug']}/index.html"
    yid = ep.get("youtube_id")
    if yid:
        media = (
            f'<div class="ep-card-thumb">'
            f'<img src="https://i.ytimg.com/vi/{esc(yid)}/hqdefault.jpg" alt="" loading="lazy" width="480" height="360">'
            f"</div>"
        )
    else:
        media = (
            f'<div class="ep-card-thumb"><div class="ep-card-fallback">'
            f'<span class="num">Episode {esc_text(num)}</span>'
            f'<span class="ftitle">{esc_text(title)}</span>'
            f"</div></div>"
        )
    meta_bits = [b for b in [f"Episode {num}" if num else "", guest, dur] if b]
    return (
        f'<a class="ep-card" href="{esc(href)}">'
        f"{media}"
        f'<div class="ep-card-body">'
        f'<p class="ep-card-title">{esc_text(title)}</p>'
        f'<p class="ep-card-meta">{esc_text(" · ".join(meta_bits))}</p>'
        f"</div></a>"
    )


def replace_header(html: str) -> str:
    # Replace existing header.site block
    new, n = re.subn(
        r"<header class=\"site\">.*?</header>",
        HEADER_HTML,
        html,
        count=1,
        flags=re.S,
    )
    if n:
        return new
    # insert after <div class="wrap">
    return re.sub(
        r'(<div class="wrap">\s*)',
        r"\1" + HEADER_HTML + "\n",
        html,
        count=1,
    )


def ensure_footer_and_scripts(html: str) -> str:
    # Remove llms from any leftover nav (already replaced header)
    # Ensure footer before closing wrap
    if 'class="motto"' not in html:
        # Insert footer before last </div> that closes wrap — heuristic:
        # place before theme.js script or before </body>
        if re.search(r'<footer class="site">', html):
            html = re.sub(
                r"<footer class=\"site\">.*?</footer>",
                FOOTER_HTML,
                html,
                count=1,
                flags=re.S,
            )
        else:
            if "</div>\n<script src=\"assets/theme.js\"" in html:
                html = html.replace(
                    "</div>\n<script src=\"assets/theme.js\"",
                    FOOTER_HTML + "\n</div>\n<script src=\"assets/theme.js\"",
                    1,
                )
            elif re.search(r"</div>\s*<script src=\"assets/theme.js\"", html):
                html = re.sub(
                    r"</div>\s*(<script src=\"assets/theme.js\")",
                    FOOTER_HTML + r"\n</div>\n\1",
                    html,
                    count=1,
                )
            elif "</body>" in html:
                # before </body>, ensure wrap closed
                if html.count("<div") > html.count("</div>"):
                    html = html.replace("</body>", FOOTER_HTML + "\n</div>\n</body>", 1)
                else:
                    # insert before last </div> prior to scripts/body
                    html = re.sub(
                        r"(</div>\s*)(</body>)",
                        FOOTER_HTML + r"\n\1\2",
                        html,
                        count=1,
                    )
            else:
                html += "\n" + FOOTER_HTML

    # Scripts: theme + archive
    if "assets/archive.js" not in html:
        if "assets/theme.js" in html:
            html = html.replace(
                '<script src="assets/theme.js" defer></script>',
                SCRIPTS,
                1,
            )
        elif "</body>" in html:
            html = html.replace("</body>", SCRIPTS + "\n</body>", 1)
        else:
            html += "\n" + SCRIPTS
    elif "assets/theme.js" not in html:
        html = html.replace(
            '<script src="assets/archive.js" defer></script>',
            SCRIPTS,
            1,
        )
    return html


def patch_all_headers_footers():
    count = 0
    for path in ROOT.rglob("*.html"):
        if "_sources" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        orig = text
        text = replace_header(text)
        text = ensure_footer_and_scripts(text)
        # strip any remaining human nav llms links outside header (shouldn't remain)
        if text != orig:
            path.write_text(text, encoding="utf-8")
            count += 1
    return count


def write_page(rel: str, title: str, body: str):
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    html = (
        PAGE_SHELL_HEAD.format(title=esc_text(title), header=HEADER_HTML)
        + body
        + PAGE_SHELL_TAIL.format(footer=FOOTER_HTML, scripts=SCRIPTS)
    )
    path.write_text(html, encoding="utf-8")


def build_homepage(index: dict):
    topics = index["topics"]
    topic_by = {t["slug"]: t for t in topics}
    packs = [
        (
            "Men / armor / fatherhood",
            "men-masculinity-fatherhood",
            "Men’s emotional life, fatherhood, and outgrown costumes.",
        ),
        (
            "Healing without clinic-speak",
            "healing-trauma-therapy",
            "Trauma, therapy, chronic pain, and recovery of the self.",
        ),
        (
            "When the break might be a message",
            "awakening-mystical",
            "Awakening stories, mystical practice, and sense-making at the edge.",
        ),
        (
            "Body first",
            "breath-body-practice",
            "Breath, yoga, fitness, and everyday care of the body.",
        ),
        (
            "Second chances",
            "extreme-lives-second-chances",
            "Prison, combat, near-death, and hard second acts.",
        ),
    ]
    pack_html = '<div class="card-grid">\n'
    for label, slug, blurb in packs:
        t = topic_by.get(slug, {})
        count = t.get("count", "")
        pack_html += (
            f'<a class="start-pack" href="topics/{esc(slug)}/index.html">'
            f'<p class="pack-label">Start here</p>'
            f"<h3>{esc_text(label)}</h3>"
            f"<p>{esc_text(blurb)}"
            + (f" · {count} episodes" if count != "" else "")
            + "</p></a>\n"
        )
    pack_html += "</div>\n"

    topic_cards = '<div class="card-grid cols-3">\n'
    for t in topics:
        topic_cards += (
            f'<a class="topic-card" href="topics/{esc(t["slug"])}/index.html">'
            f'<h3>{esc_text(t["title"])}</h3>'
            f'<span class="count">{t.get("count", 0)} episodes</span>'
            f'<p class="blurb">{esc_text(t.get("blurb", ""))}</p>'
            f"</a>\n"
        )
    topic_cards += "</div>\n"

    thesis = """<div class="about thesis">
<p>&quot;Mining the hearts and minds of unorthodox teachers&quot; For the life-long learner who wants honest, human conversations about how we grow, heal, create, and understand ourselves.</p>
<p>These are longform dialogues with artists, thinkers, authors, meditators, psychologists, musicians, creatives, leaders, philosophers, healers, and everyday people with something real to teach. Each episode offers a perspective, story, or insight that tends to lands exactly when someone needs it most.</p>
<p>Thoughtful, curious, and quietly life-changing, this show exists to help us live a better life by understanding our own inner world more deeply, through the perspectives of one another. The Junkyard Love Podcast - for a better life.</p>
</div>"""

    body = f"""
<h1>The Junkyard Love Podcast</h1>
<p class="note">Conversation archive — published episodes, searchable transcripts.</p>
{thesis}

<h2>Search</h2>
<form class="search-box" data-archive-search role="search" action="search/index.html">
  <label class="sr-only" for="home-q">Search episodes</label>
  <input id="home-q" type="search" name="q" placeholder="Guest, topic, or a word like breath…" autocomplete="off">
  <button type="submit">Search</button>
</form>
<div id="search-results"></div>

<h2>Start here</h2>
<p class="note">Five ways in — pick a door that matches where you are.</p>
{pack_html}
<p class="note"><a href="start-here/index.html">More about starting here</a></p>

<div class="action-row">
  <a class="btn" href="#" data-random-episode>Random episode</a>
  <a class="btn secondary" href="#" data-shuffle-clip>Shuffle a clip</a>
</div>
<div id="shuffle-result"></div>

<h2>Listen by mood</h2>
<p class="note">not a diagnosis. just a door.</p>
<div id="mood-doors" class="mood-doors" data-mood-doors></div>
<div id="mood-results" class="mood-results" data-mood-results></div>

<h2>Pick a clip</h2>
<p class="note">Keyword phrases drawn from chapter titles and topics — click for a few chapter deep-links. <a href="clips/index.html">Open Pick a clip</a></p>
<div class="phrase-cloud" data-phrase-cloud></div>
<div id="clip-results"></div>

<div class="section-head">
  <h2>Latest</h2>
  <a class="more" href="episodes/index.html">All episodes</a>
</div>
<div class="card-grid" data-latest-cards data-count="8"></div>

<h2>Topics</h2>
{topic_cards}

<h2>A quote from the archive</h2>
<div class="quote-spotlight card" data-random-quote></div>
"""
    write_page("index.html", "The Junkyard Love Podcast — Conversation Archive", body)


def build_start_here(index: dict):
    topics = {t["slug"]: t for t in index["topics"]}
    packs = [
        ("Men / armor / fatherhood", "men-masculinity-fatherhood"),
        ("Healing without clinic-speak", "healing-trauma-therapy"),
        ("When the break might be a message", "awakening-mystical"),
        ("Body first", "breath-body-practice"),
        ("Second chances", "extreme-lives-second-chances"),
    ]
    # also mind-mood as related
    cards = '<div class="card-grid">\n'
    for label, slug in packs:
        t = topics.get(slug, {})
        cards += (
            f'<a class="start-pack" href="topics/{esc(slug)}/index.html">'
            f'<p class="pack-label">Topic pack</p>'
            f"<h3>{esc_text(label)}</h3>"
            f'<p>{esc_text(t.get("blurb", ""))} · {t.get("count", 0)} episodes</p>'
            f"</a>\n"
        )
    mm = topics.get("mind-mood-mental-health")
    if mm:
        cards += (
            f'<a class="start-pack" href="topics/mind-mood-mental-health/index.html">'
            f'<p class="pack-label">Also nearby</p>'
            f"<h3>Mind, mood &amp; mental health</h3>"
            f'<p>{esc_text(mm.get("blurb", ""))} · {mm.get("count", 0)} episodes</p>'
            f"</a>\n"
        )
    cards += "</div>\n"
    body = f"""
<h1>Start here</h1>
<p class="lede">If the full catalog feels like too much, begin with one of these doors. Each pack is an existing topic page — same episodes, same transcripts.</p>
{cards}
<p class="note"><a href="search/index.html">Search</a> · <a href="clips/index.html">Pick a clip</a> · <a href="episodes/index.html">All episodes</a></p>
"""
    write_page("start-here/index.html", "Start here — The Junkyard Love Podcast", body)


def build_search_page():
    body = """
<h1>Search</h1>
<p class="note">Search titles, guests, topics, and archive quotes. Everything stays on this site.</p>
<form class="search-box" data-archive-search role="search">
  <label class="sr-only" for="q">Search</label>
  <input id="q" type="search" name="q" placeholder="Guest, topic, or a word like breath…" autocomplete="off">
  <button type="submit">Search</button>
</form>
<div id="search-results"><p class="search-empty">try a guest name, or a word like breath, father, surrender.</p></div>
"""
    write_page("search/index.html", "Search — The Junkyard Love Podcast", body)


def build_listen_page():
    body = f"""
<h1>Listen</h1>
<p class="lede">The show lives on YouTube and the usual podcast apps. Episode pages link to the video when we have it; show feeds cover the full catalog.</p>
<div class="card">
  <h2 style="margin-top:0;border:0;padding:0;">Show feeds</h2>
  <div class="listen-links btn-row" style="margin-top:1rem;">
    <a href="{esc(SHOW['youtube_channel'])}" target="_blank" rel="noopener">YouTube channel</a>
    <a class="secondary" href="{esc(SHOW['spotify_show'])}" target="_blank" rel="noopener">Spotify</a>
    <a class="secondary" href="{esc(SHOW['apple_show'])}" target="_blank" rel="noopener">Apple Podcasts</a>
  </div>
</div>
<p class="note"><a href="episodes/index.html">Browse episodes</a> · <a href="{esc(SHOW['instagram'])}" target="_blank" rel="noopener">Instagram</a></p>
"""
    write_page("listen/index.html", "Listen — The Junkyard Love Podcast", body)


def build_donate_merch_clips():
    write_page(
        "donate/index.html",
        "Donate — The Junkyard Love Podcast",
        """
<h1>Donate</h1>
<p class="lede">Support for the archive and the show.</p>
<div class="card">
  <p>Donation link coming.</p>
  <p class="note">No payment form on this page yet — when a donate URL is ready, it will live here.</p>
</div>
""",
    )
    write_page(
        "merch/index.html",
        "Merch — The Junkyard Love Podcast",
        """
<h1>Merch</h1>
<p class="lede">Soft goods, when they exist.</p>
<div class="card">
  <p>Logo shirts — not for sale yet.</p>
  <p class="note">No cart, no checkout. This page is a placeholder until artwork and stock are real.</p>
</div>
""",
    )
    write_page(
        "clips/index.html",
        "Pick a clip — The Junkyard Love Podcast",
        """
<h1>Pick a clip</h1>
<p class="note">Phrases come from existing chapter titles and topics. Click one to see a few chapter cards across different episodes — open at the chapter, or jump to YouTube at that time. No autoplay.</p>
<div class="action-row">
  <a class="btn secondary" href="#" data-shuffle-clip>Shuffle a clip</a>
  <a class="btn secondary" href="#" data-random-episode>Random episode</a>
</div>
<div id="shuffle-result"></div>
<div class="phrase-cloud" data-phrase-cloud data-clips-page></div>
<div id="clip-results"></div>
""",
    )


def rebuild_episodes_index(index: dict):
    cards = '<div class="card-grid">\n'
    # chronological newest first already
    for ep in index["episodes"]:
        cards += card_html(ep) + "\n"
    # removed placeholders as simple notes (not in random)
    removed_notes = ""
    for num in sorted(REMOVED):
        slug = f"{num}-removed"
        p = ROOT / "episodes" / slug / "index.html"
        if p.exists():
            removed_notes += f'<li><a href="episodes/{esc(slug)}/index.html">Episode {num} (Removed)</a> <span class="note">Catalog gap</span></li>\n'
    body = f"""
<h1>Episodes</h1>
<p class="note">{index['episode_count']} published episodes. Thumbnails from YouTube when available.</p>
<div class="action-row">
  <a class="btn" href="#" data-random-episode>Random episode</a>
  <a class="btn secondary" href="search/index.html">Search</a>
  <a class="btn secondary" href="clips/index.html">Pick a clip</a>
</div>
{cards}
"""
    if removed_notes:
        body += f"<h2>Catalog gaps</h2><ul class=\"list\">{removed_notes}</ul>\n"
    write_page("episodes/index.html", "Episodes — The Junkyard Love Podcast", body)


def rebuild_topics_index(index: dict):
    cards = '<div class="card-grid">\n'
    for t in index["topics"]:
        cards += (
            f'<a class="topic-card" href="topics/{esc(t["slug"])}/index.html">'
            f'<h3>{esc_text(t["title"])}</h3>'
            f'<span class="count">{t.get("count", 0)} episodes</span>'
            f'<p class="blurb">{esc_text(t.get("blurb", ""))}</p>'
            f"</a>\n"
        )
    cards += "</div>\n"
    body = f"""
<h1>Topics</h1>
<p class="note">Browse published episodes by theme. Episodes can appear in more than one topic.</p>
{cards}
"""
    write_page("topics/index.html", "Topics — The Junkyard Love Podcast", body)


def rebuild_topic_pages(index: dict):
    by_slug = {e["slug"]: e for e in index["episodes"]}
    topics_src = load_json(ROOT / "_sources" / "topics.json")
    for cat in topics_src.get("categories", []):
        cards = '<div class="card-grid">\n'
        for item in cat.get("episodes", []):
            ep = by_slug.get(item["slug"])
            if ep:
                cards += card_html(ep) + "\n"
            else:
                # fallback minimal card without inventing
                title = item.get("title") or item["slug"]
                # try browse title from number
                cards += (
                    f'<a class="ep-card" href="episodes/{esc(item["slug"])}/index.html">'
                    f'<div class="ep-card-thumb"><div class="ep-card-fallback">'
                    f'<span class="num">Episode {esc_text(item.get("number", ""))}</span>'
                    f'<span class="ftitle">{esc_text(title)}</span>'
                    f"</div></div>"
                    f'<div class="ep-card-body"><p class="ep-card-title">{esc_text(title)}</p></div></a>\n'
                )
        cards += "</div>\n"
        body = f"""
<h1>{esc_text(cat["title"])}</h1>
<p class="lede">{esc_text(cat.get("blurb", ""))}</p>
<p class="note">{len(cat.get("episodes", []))} episodes · <a href="topics/index.html">All topics</a></p>
{cards}
"""
        write_page(
            f"topics/{cat['slug']}/index.html",
            f"{cat['title']} — The Junkyard Love Podcast",
            body,
        )


def rebuild_guests_index_and_pages(index: dict):
    # Parse existing guest index for names/slugs, then upgrade cards
    guests_dir = ROOT / "guests"
    guest_pages = sorted(
        [p for p in guests_dir.iterdir() if p.is_dir() and (p / "index.html").exists()],
        key=lambda p: p.name,
    )
    # Build guest -> episodes from index by matching guest name loosely + parsing guest pages
    ep_by_slug = {e["slug"]: e for e in index["episodes"]}

    index_items = []
    for gp in guest_pages:
        html = (gp / "index.html").read_text(encoding="utf-8")
        # keep h1 name
        hm = re.search(r"<h1>(.*?)</h1>", html, re.S)
        name = htmlmod.unescape(re.sub(r"<[^>]+>", "", hm.group(1))).strip() if hm else gp.name
        # episode links
        slugs = re.findall(r'href="episodes/([^"/]+)/index\.html"', html)
        eps = [ep_by_slug[s] for s in slugs if s in ep_by_slug]
        index_items.append((gp.name, name, eps, html))

    # guests index
    lis = []
    for slug, name, eps, _ in sorted(index_items, key=lambda x: x[1].lower()):
        lis.append(
            f'<li><a href="guests/{esc(slug)}/index.html">{esc_text(name)}</a>'
            f' <span class="note">({len(eps)})</span></li>'
        )
    body = f"""
<h1>Guests</h1>
<p class="note">{len(index_items)} people who have appeared on the show.</p>
<ul class="list">
{''.join(lis)}
</ul>
"""
    write_page("guests/index.html", "Guests — The Junkyard Love Podcast", body)

    # upgrade each guest page: keep about notes, replace episode list with cards; update header/footer via later pass too
    for slug, name, eps, html in index_items:
        # extract "From the episode notes" section if present
        notes = ""
        nm = re.search(
            r"(<h2>From the episode notes</h2>.*?)(?:<footer|</div>\s*<script|</body>)",
            html,
            re.S,
        )
        if nm:
            notes = nm.group(1).strip()
            # trim trailing footer if captured
            notes = re.sub(r"<footer class=\"site\">.*$", "", notes, flags=re.S).strip()

        cards = '<div class="card-grid">\n' + "\n".join(card_html(e) for e in eps) + "\n</div>\n"
        count = len(eps)
        body = f"""
<h1>{esc_text(name)}</h1>
<p class="note">Appeared on The Junkyard Love Podcast ({count} episode{"s" if count != 1 else ""})</p>
<h2>Episodes</h2>
{cards}
"""
        if notes:
            body += notes + "\n"
        write_page(
            f"guests/{slug}/index.html",
            f"{name} — The Junkyard Love Podcast",
            body,
        )


def patch_episode_heroes(index: dict):
    """Add hero thumb + optional YouTube embed; solocast badge. Do not rewrite About/titles."""
    by_slug = {e["slug"]: e for e in index["episodes"]}
    patched = 0
    for path in (ROOT / "episodes").glob("*/index.html"):
        slug = path.parent.name
        if "removed" in slug:
            # still get header/footer from global pass
            continue
        ep = by_slug.get(slug)
        if not ep:
            continue
        html = path.read_text(encoding="utf-8")
        if 'class="ep-hero"' in html:
            continue

        yid = ep.get("youtube_id")
        title = ep.get("browse_title") or ""
        num = ep.get("number") or ""
        if yid:
            media = (
                f'<div class="ep-hero-media">'
                f'<img src="https://i.ytimg.com/vi/{esc(yid)}/hqdefault.jpg" alt="" width="480" height="360">'
                f"</div>"
            )
        else:
            media = (
                f'<div class="ep-hero-media"><div class="ep-card-fallback">'
                f'<span class="num">Episode {esc_text(num)}</span>'
                f'<span class="ftitle">{esc_text(title)}</span>'
                f"</div></div>"
            )

        badge = ""
        if ep.get("is_solo"):
            badge = '<span class="badge-solo">Solocast</span>\n'

        # Insert hero after <article> or before first h1
        hero_open = f'<div class="ep-hero">\n{media}\n<div class="ep-hero-text">\n{badge}'
        if "<article>" in html:
            html = html.replace("<article>", "<article>\n" + hero_open, 1)
        else:
            html = re.sub(r"(<h1>)", hero_open + r"\1", html, count=1)

        # Close hero after topic-chips or after listen block
        close = "\n</div><!-- /.ep-hero-text --></div><!-- /.ep-hero -->\n"
        if "<!-- topic-chips:end -->" in html:
            html = html.replace(
                "<!-- topic-chips:end -->",
                "<!-- topic-chips:end -->" + close,
                1,
            )
        elif '<div class="listen">' in html:
            html = re.sub(
                r'(<div class="listen">.*?</div>)',
                r"\1" + close,
                html,
                count=1,
                flags=re.S,
            )
        else:
            # after first meta paragraph
            html = re.sub(
                r'(<p class="meta">.*?</p>)',
                r"\1" + close,
                html,
                count=1,
                flags=re.S,
            )

        # YouTube embed (no autoplay) after hero / before About if youtube id
        if yid and 'class="yt-embed"' not in html:
            embed = (
                f'<div class="yt-embed">'
                f'<iframe src="https://www.youtube.com/embed/{esc(yid)}" '
                f'title="YouTube video" loading="lazy" '
                f'allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" '
                f'referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>'
                f"</div>\n"
            )
            if "<h2>About</h2>" in html:
                html = html.replace("<h2>About</h2>", embed + "<h2>About</h2>", 1)
            elif close in html:
                html = html.replace(close, close + embed, 1)

        path.write_text(html, encoding="utf-8")
        patched += 1
    return patched


def write_notes(index: dict):
    yt_count = sum(1 for e in index["episodes"] if e.get("youtube_id"))
    notes = f"""# UI redesign notes

Generated by `_sources/build_ui_redesign.py` (no git push from this pass).

## Missing assets (known)

- **Donate URL** — none in repo → `donate/index.html` placeholder: “Donation link coming.”
- **Logo file** — none in repo → merch page: “Logo shirts — not for sale yet.” No storefront.
- **Bed / theme music file** — none owned in repo → **no music player** shipped.
- **Guest photos** — not used; no fake photos. Cards/hero use YouTube `hqdefault` when `youtube_id` exists, else episode number + title fallback.

## What shipped

- Wider quiet long-form layout (`assets/style.css`), dark default, Light toggle (`assets/theme.js`).
- Nav: Home | Start here | Episodes | Guests | Topics | Search | Listen | Instagram. `llms.txt` remains on disk, removed from human nav.
- Homepage: thesis, search, Start here packs, Random / Shuffle clip, Pick a clip phrases, Latest 8 cards, Topics as cards, one random Archive quote.
- Pages: `start-here/`, `search/`, `listen/`, `donate/`, `merch/`, `clips/`.
- Footer motto exact: `drink some water, stretch, love yourselves.`
- Thumbnails: YouTube `https://i.ytimg.com/vi/<ID>/hqdefault.jpg` on homepage latest (JS), episodes index, topics, guests, episode heroes.
- Client index: `assets/episodes_index.json` (+ `_sources/episodes_index.json` copy) with slug, browse_title, guest, duration, youtube_id, topics, chapters, quotes.
- Search / Random / Shuffle a clip / Pick a clip via `assets/archive.js` (skips removed 0001/0014/0016/0029).
- Episode heroes: thumb/fallback + solocast badge + YouTube embed without autoplay when ID present.
- Base href remains `/junkyard-love-archive/`.

## Counts

- Published episodes in index: {index['episode_count']}
- With YouTube ID: {yt_count}
- Clip phrases: {len(index.get('clip_phrases', []))}
- Topics: {len(index.get('topics', []))}

## Intentionally unchanged

- Content model, canonical titles, Jacob About copy, episode URL paths.
- Transcripts, published chapters/quotes blocks (heroes inserted around them).
- No newsletter popups, no autoplay, no neon/purple-gradient template.
"""
    out = ROOT / "_sources" / "reports" / "UI_REDESIGN_NOTES.md"
    out.write_text(notes, encoding="utf-8")
    mirror = MIRROR / "_sources" / "reports" / "UI_REDESIGN_NOTES.md"
    mirror.parent.mkdir(parents=True, exist_ok=True)
    mirror.write_text(notes, encoding="utf-8")


def mirror_key_assets():
    for rel in [
        "assets/style.css",
        "assets/theme.js",
        "assets/archive.js",
        "assets/episodes_index.json",
        "_sources/episodes_index.json",
        "_sources/build_ui_redesign.py",
    ]:
        src = ROOT / rel
        if not src.exists():
            continue
        dst = MIRROR / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def main():
    print("Building episodes index…")
    index = build_index()
    idx_json = json.dumps(index, ensure_ascii=False, indent=2)
    (ROOT / "_sources" / "episodes_index.json").write_text(idx_json + "\n", encoding="utf-8")
    (ROOT / "assets" / "episodes_index.json").write_text(idx_json + "\n", encoding="utf-8")
    print(f"  episodes={index['episode_count']} phrases={len(index['clip_phrases'])} yt={sum(1 for e in index['episodes'] if e.get('youtube_id'))}")

    print("Writing primary pages…")
    build_homepage(index)
    build_start_here(index)
    build_search_page()
    build_listen_page()
    build_donate_merch_clips()
    rebuild_episodes_index(index)
    rebuild_topics_index(index)
    rebuild_topic_pages(index)
    rebuild_guests_index_and_pages(index)

    print("Patching episode heroes…")
    n_hero = patch_episode_heroes(index)
    print(f"  heroes patched: {n_hero}")

    print("Updating headers/footers on all HTML…")
    n_hdr = patch_all_headers_footers()
    print(f"  files updated: {n_hdr}")

    write_notes(index)
    mirror_key_assets()
    print("Done. No git commit/push.")


if __name__ == "__main__":
    main()
