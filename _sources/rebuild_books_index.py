#!/usr/bin/env python3
"""Rebuild a clean books index + book detail pages + guest Books mentioned sections.

No git commit/push — parent deploys.
"""
from __future__ import annotations

import html as htmlmod
import json
import re
from pathlib import Path

ROOT = Path("/workspace/junkyard-love-archive-deploy")
SRC = ROOT / "_sources"
REMOVED = {"0001", "0014", "0016", "0029"}

SITE_BASE = "https://junkyardlovejakesbot.github.io/junkyard-love-archive"

HEADER = """<header class="site">
  <div class="header-row">
    <a class="brand" href="index.html">The Junkyard Love Podcast</a>
    <button type="button" class="theme-toggle" data-theme-toggle aria-label="Toggle light and dark mode">Light</button>
  </div>
  <nav class="nav-main" aria-label="Primary">
    <a href="index.html">Home</a>
    <a href="six-ways-in/index.html">Six ways in</a>
    <a href="radio/index.html">Chapter radio</a>
    <a href="topics/index.html">Topics</a>
    <a href="guests/index.html">Guests</a>
    <a href="episodes/index.html">Episodes</a>
    <a href="books/index.html">Books</a>
    <a href="search/index.html">Search</a>
    <a href="listen/index.html">Listen</a>
    <a href="https://www.instagram.com/jacobfromtheinternet/" target="_blank" rel="noopener">Instagram</a>
  </nav>
</header>"""

FOOTER = """<footer class="site">
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


def esc(s: str) -> str:
    return htmlmod.escape(s or "", quote=True)


def esc_text(s: str) -> str:
    return htmlmod.escape(s or "", quote=False)


def slugify(title: str) -> str:
    s = title.lower().strip()
    s = s.replace("&", " and ")
    s = re.sub(r"[''`]", "", s)
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")[:80]


def norm_key(title: str) -> str:
    s = title.lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    # common article strip for fuzzy match
    for a in ("the ", "a ", "an "):
        if s.startswith(a):
            s = s[len(a) :]
    return s


def looks_like_scrap(title: str) -> bool:
    t = (title or "").strip()
    if not t or len(t) < 3:
        return True
    if len(t) > 70 and (" " in t) and t[:1].islower():
        return True
    # mid-sentence ASR markers
    scrap_markers = [
        " and they talk",
        " and i'm",
        " and it ",
        " that says",
        " it's like",
        " it's about",
        " you hold on",
        " have you ever",
        " and that's",
        " i think",
        " i'm like",
        " uh ",
        " um ",
        " my sister gave",
        " when i was",
        " and two poetry",
        " nine published",
        " the book ",
        " / awake awareness",
        "' here",
    ]
    low = " " + t.lower() + " "
    if any(m in low for m in scrap_markers):
        # allow short proper titles that accidentally match
        if len(t) > 40 or t[:1].islower() or t.lower().startswith(("uh ", "um ", "the book ")):
            return True
        if " and they talk" in low or " nine published" in low:
            return True
    if t.lower() in {"love 2", "pcal", "uh dark psychology"}:
        return True
    # must look title-case-ish or known short title
    words = t.split()
    if len(words) >= 4 and sum(1 for w in words if w[:1].islower()) > len(words) // 2:
        return True
    return False


# ASR / variant → canonical title
CANON_MAP = {
    "atomic habits": "Atomic Habits",
    "awake the yoga of pure awareness": "Awake: The Yoga of Pure Awareness",
    "awake the yoga of pure awareness awake awareness": "Awake: The Yoga of Pure Awareness",
    "be here now": "Be Here Now",
    "be nimble": "Be Nimble",
    "be visionary": "Be Visionary",
    "building resilient family enterprises": "Building Resilient Family Enterprises",
    "decisive": "Decisive",
    "decisive by chip and dan heath": "Decisive",
    "educated": "Educated",
    "educated by tara westover": "Educated",
    "five senses for success": "Five Senses For Success",
    "full voice": "Full Voice",
    "full voice and vocal intelligence": "Full Voice",
    "holding on by letting go a memoir": "Holding On by Letting Go: A Memoir",
    "mans search for meaning": "Man's Search for Meaning",
    "mind gym": "Mind Gym",
    "mind training science of self empowerment": "Mind Training - Science of Self-Empowerment",
    "neither ghost nor machine": "Neither Ghost Nor Machine",
    "next level human": "Next Level Human",
    "one journey": "One Journey",
    "potatoes not prozac": "Potatoes Not Prozac",
    "psycho cybernetics": "Psycho-Cybernetics",
    "tattooing the world pacific designs in print and skin": "Tattooing the World: Pacific Designs in Print and Skin",
    "10x rule": "The 10X Rule",
    "the 10x rule": "The 10X Rule",
    "10x rule by grant cardone": "The 10X Rule",
    "body keeps a score": "The Body Keeps the Score",
    "body keeps the score": "The Body Keeps the Score",
    "the body keeps the score": "The Body Keeps the Score",
    "celestine prophecies": "The Celestine Prophecy",
    "the celestine prophecy": "The Celestine Prophecy",
    "celestine prophecy": "The Celestine Prophecy",
    "end of your world": "The End of Your World",
    "the end of your world": "The End of Your World",
    "far side of the mountain": "Far Side of the Mountain",
    "the far side of the mountain": "Far Side of the Mountain",
    "human idea": "The Human Idea",
    "the human idea": "The Human Idea",
    "power of now": "The Power of Now",
    "the power of now": "The Power of Now",
    "road less traveled": "The Road Less Traveled",
    "the road less traveled": "The Road Less Traveled",
    "seven lessons of love": "The Seven Lessons of Love",
    "the seven lessons of love": "The Seven Lessons of Love",
    "spiritual awakening guide": "The Spiritual Awakening Guide",
    "the spiritual awakening guide": "The Spiritual Awakening Guide",
    "symbolic species": "The Symbolic Species",
    "the symbolic species": "The Symbolic Species",
    "symbolic species the co evolution of language and brain": "The Symbolic Species",
    "war of art": "The War of Art",
    "the war of art": "The War of Art",
    "will to live project": "The Will To Live Project",
    "the will to live project": "The Will To Live Project",
    "wisdom of insecurity": "The Wisdom of Insecurity",
    "the wisdom of insecurity": "The Wisdom of Insecurity",
    "protestant ethic": "The Protestant Ethic and the Spirit of Capitalism",
    "capitalism in the protestant ethic": "The Protestant Ethic and the Spirit of Capitalism",
    "light eaters": "The Light Eaters",
    "the light eaters": "The Light Eaters",
    "who s afraid of ai": "Who's Afraid of AI?",
    "whos afraid of ai": "Who's Afraid of AI?",
}


def resolve_canonical(raw_title: str) -> str | None:
    t = (raw_title or "").strip()
    if not t:
        return None
    key = norm_key(t)
    # direct map
    if key in CANON_MAP:
        return CANON_MAP[key]
    # prefix / contains known keys (longest first)
    for k in sorted(CANON_MAP.keys(), key=len, reverse=True):
        if key.startswith(k) or k in key[: max(len(k) + 10, 40)]:
            # avoid over-matching short keys inside unrelated scraps
            if len(k) >= 8 or key == k or key.startswith(k + " "):
                return CANON_MAP[k]
    # keep clear titled works that aren't scraps
    if looks_like_scrap(t):
        return None
    # title-case proper name heuristic
    if t[0].isupper() and len(t) <= 70:
        return t
    return None


def load_guest_map() -> dict[str, str]:
    """Map lowercased guest display name → guest slug."""
    out: dict[str, str] = {}
    guests_dir = ROOT / "guests"
    for d in guests_dir.iterdir():
        if not d.is_dir():
            continue
        p = d / "index.html"
        if not p.exists():
            continue
        m = re.search(r"<h1>([^<]+)</h1>", p.read_text(encoding="utf-8", errors="ignore"))
        if not m:
            continue
        name = htmlmod.unescape(m.group(1)).strip()
        out[name.lower()] = d.name
        # also first+last only
        parts = name.split()
        if len(parts) >= 2:
            out[" ".join(parts[:2]).lower()] = d.name
    # aliases
    aliases = {
        "dr. cristine hull": "cristine-hull",
        "cristine hull": "cristine-hull",
        "barbara mcafee": "barbara-mcafee",
        "juli geske-peer": "juli-geske-peer",
        "juli geske peer": "juli-geske-peer",
        "maxx v. payne": "maxx-v-payne",
        "maxx v payne": "maxx-v-payne",
        "brandon cruz (zack wyld)": "brandon-cruz",
        "brandon cruz": "brandon-cruz",
        "mack t & j faul": "mack-t",
        "mack t": "mack-t",
        "solo (host)": None,
        "solo": None,
        "jacob": None,
        "jacob rhines": None,
    }
    for k, v in aliases.items():
        if v:
            out[k] = v
        elif k in out:
            del out[k]
    return out


def load_episodes() -> dict[str, dict]:
    data = json.loads((ROOT / "assets" / "episodes_index.json").read_text(encoding="utf-8"))
    by_slug = {}
    by_num = {}
    for ep in data.get("episodes") or []:
        if not ep or ep.get("removed") or ep.get("number") in REMOVED:
            continue
        by_slug[ep["slug"]] = ep
        by_num[ep["number"]] = ep
    return {"by_slug": by_slug, "by_num": by_num}


def resolve_mentioned_by(raw: str, guest: str, is_solo: bool) -> str:
    mb = (raw or "").strip()
    g = (guest or "").strip()
    if mb.lower() in {"guest", "discussed", ""}:
        if is_solo or g.lower().startswith("solo"):
            return "Jacob"
        if mb.lower() == "discussed":
            # host-led mention; still name the guest room when known
            return "Jacob" if not g or g.lower().startswith("solo") else "Jacob"
        if g and not g.lower().startswith("solo"):
            # strip parenthetical noise for display
            g = re.sub(r"\s*\([^)]*\)\s*", " ", g).strip()
            g = re.sub(r"\s+", " ", g)
            return g
        return "mentioned on episode"
    # "Rebecca Wyld / discussed" → Rebecca Wyld
    if "/" in mb:
        mb = mb.split("/")[0].strip()
    if mb.lower() in {"guest", "discussed"}:
        return resolve_mentioned_by("Guest", guest, is_solo)
    return mb


def guest_slug_for(name: str, guest_map: dict[str, str]) -> str | None:
    if not name:
        return None
    n = name.lower().strip()
    if n in {"jacob", "mentioned on episode"}:
        return None
    if n in guest_map:
        return guest_map[n]
    # try without honorifics
    n2 = re.sub(r"^(dr\.|swami)\s+", "", n).strip()
    if n2 in guest_map:
        return guest_map[n2]
    # fuzzy: any guest name contained
    for k, slug in guest_map.items():
        if k in n or n in k:
            return slug
    return None


def fix_episode_slug(slug: str, number: str, eps: dict) -> str:
    if slug in eps["by_slug"]:
        return slug
    if number in eps["by_num"]:
        return eps["by_num"][number]["slug"]
    # barbara bad slug
    if slug.startswith("0122-barbara"):
        return "0122-laughing-like-a-hairy-oaf-barbara-mcafee"
    if slug.startswith("0123-cristine"):
        return eps["by_num"].get("0123", {}).get("slug") or slug
    return slug


def extract_canonical_from_scrap(title: str) -> str | None:
    """Pull known book names out of ASR scraps that resolve_canonical might miss."""
    low = title.lower()
    patterns = [
        (r"decisive", "Decisive"),
        (r"educated", "Educated"),
        (r"mind gym", "Mind Gym"),
        (r"next level human", "Next Level Human"),
        (r"10x rule", "The 10X Rule"),
        (r"body keeps (a|the) score", "The Body Keeps the Score"),
        (r"celestine prophec", "The Celestine Prophecy"),
        (r"end of your world", "The End of Your World"),
        (r"far side of the mountain", "Far Side of the Mountain"),
        (r"spiritual awakening guide", "The Spiritual Awakening Guide"),
        (r"symbolic species", "The Symbolic Species"),
        (r"be here now|b here now", "Be Here Now"),
        (r"protestant ethic", "The Protestant Ethic and the Spirit of Capitalism"),
        (r"light eaters", "The Light Eaters"),
        (r"who.?s afraid of ai", "Who's Afraid of AI?"),
        (r"psycho[- ]?cybernetics", "Psycho-Cybernetics"),
        (r"potatoes not prozac", "Potatoes Not Prozac"),
        (r"tattooing the world", "Tattooing the World: Pacific Designs in Print and Skin"),
        (r"awake:? the yoga of pure awareness", "Awake: The Yoga of Pure Awareness"),
        (r"will to live project", "The Will To Live Project"),
        (r"seven lessons of love", "The Seven Lessons of Love"),
        (r"full voice", "Full Voice"),
    ]
    for pat, canon in patterns:
        if re.search(pat, low):
            return canon
    return None


def clean_books(raw_books: list[dict], eps: dict, guest_map: dict[str, str]) -> list[dict]:
    # canonical_title → aggregated book
    buckets: dict[str, dict] = {}

    for b in raw_books:
        raw_title = (b.get("title") or "").strip()
        canon = resolve_canonical(raw_title)
        if not canon:
            canon = extract_canonical_from_scrap(raw_title)
        if not canon:
            continue
        # drop non-book noise that slipped through
        if canon.lower() in {"love 2", "pcal"}:
            continue

        num = b.get("episode_number") or ""
        if num in REMOVED:
            continue
        slug = fix_episode_slug(b.get("episode_slug") or "", num, eps)
        ep = eps["by_slug"].get(slug) or eps["by_num"].get(num)
        guest = b.get("guest") or (ep.get("guest") if ep else "") or ""
        is_solo = bool(ep and ep.get("is_solo")) or str(guest).lower().startswith("solo")
        mentioned = resolve_mentioned_by(b.get("mentioned_by") or "", guest, is_solo)
        # guest_slug only when the mentioner maps to a guest page (not Jacob)
        gslug = guest_slug_for(mentioned, guest_map)

        browse = b.get("browse_title") or (ep.get("browse_title") if ep else "") or ""
        start = b.get("start")
        start_seconds = b.get("start_seconds")

        book_slug = slugify(canon)
        if book_slug not in buckets:
            buckets[book_slug] = {
                "title": canon,
                "book_slug": book_slug,
                "mentions": [],
            }
        # dedupe mention by episode+start
        key = (slug, start or "", mentioned)
        existing = {
            (m["episode_slug"], m.get("start") or "", m["mentioned_by"])
            for m in buckets[book_slug]["mentions"]
        }
        if key in existing:
            # prefer keeping timestamped version: if new has start and old doesn't, replace
            continue
        # if we already have same episode without start, and this has start, upgrade
        upgraded = False
        for m in buckets[book_slug]["mentions"]:
            if m["episode_slug"] == slug and not m.get("start") and start:
                m["start"] = start
                m["start_seconds"] = start_seconds
                if mentioned and m["mentioned_by"] in {"Jacob", "mentioned on episode"} and mentioned not in {
                    "Jacob",
                    "mentioned on episode",
                }:
                    m["mentioned_by"] = mentioned
                    m["guest_slug"] = gslug
                upgraded = True
                break
        if upgraded:
            continue
        # if duplicate episode with start already, skip scrap without start
        if any(m["episode_slug"] == slug and m.get("start") for m in buckets[book_slug]["mentions"]) and not start:
            continue
        buckets[book_slug]["mentions"].append(
            {
                "mentioned_by": mentioned,
                "guest_slug": gslug,
                "guest": guest if not str(guest).lower().startswith("solo") else "Jacob",
                "episode_slug": slug,
                "episode_number": num or (ep.get("number") if ep else ""),
                "start": start,
                "start_seconds": start_seconds,
                "browse_title": browse,
            }
        )

    # flatten for index: one row per book with mentions list
    books = []
    for book_slug, data in sorted(buckets.items(), key=lambda x: x[1]["title"].lower()):
        mentions = data["mentions"]
        # prefer guest names over Jacob for primary mentioned_by display
        names = []
        for m in mentions:
            n = m["mentioned_by"]
            if n and n not in names:
                names.append(n)
        primary_guest_slug = None
        for m in mentions:
            if m.get("guest_slug"):
                primary_guest_slug = m["guest_slug"]
                break
        books.append(
            {
                "title": data["title"],
                "book_slug": book_slug,
                "mentioned_by": ", ".join(names) if names else "mentioned on episode",
                "guest_slug": primary_guest_slug,
                "mentions": mentions,
                # back-compat single-episode fields (first mention)
                "episode_slug": mentions[0]["episode_slug"] if mentions else None,
                "episode_number": mentions[0]["episode_number"] if mentions else None,
                "start": mentions[0].get("start") if mentions else None,
                "start_seconds": mentions[0].get("start_seconds") if mentions else None,
                "browse_title": mentions[0].get("browse_title") if mentions else None,
                "guest": mentions[0].get("guest") if mentions else None,
            }
        )
    return books


def seo_head(title: str, description: str, path: str) -> str:
    url = f"{SITE_BASE}/{path.lstrip('/')}"
    if not url.endswith("/") and path.endswith("/"):
        url += "/"
    return f"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<base href="/junkyard-love-archive/">
<script>(function(){{try{{var t=localStorage.getItem("jylp-theme");if(t==="light"||t==="dark")document.documentElement.setAttribute("data-theme",t);}}catch(e){{}}}})();</script>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc_text(title)}</title>
<meta name="description" content="{esc(description)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{esc(url)}">
<link rel="stylesheet" href="assets/style.css">
</head>
"""


def ep_link(m: dict) -> str:
    slug = m["episode_slug"]
    href = f"episodes/{slug}/index.html"
    label = f"Episode {m.get('episode_number') or ''} — {m.get('browse_title') or slug}".strip(" —")
    if m.get("start"):
        # #t-HH-MM-SS
        parts = str(m["start"]).split(":")
        if len(parts) == 3:
            href += f"#t-{parts[0]}-{parts[1]}-{parts[2]}"
        label += f" · {m['start']}"
    return f'<a href="{esc(href)}">{esc_text(label)}</a>'


def write_book_pages(books: list[dict]) -> None:
    books_dir = ROOT / "books"
    # remove old book slug dirs (keep index.html)
    for child in list(books_dir.iterdir()):
        if child.is_dir():
            for p in child.rglob("*"):
                if p.is_file():
                    p.unlink()
            # remove empty dirs bottom-up
            for p in sorted(child.rglob("*"), reverse=True):
                if p.is_dir():
                    p.rmdir()
            child.rmdir()

    for b in books:
        slug = b["book_slug"]
        d = books_dir / slug
        d.mkdir(parents=True, exist_ok=True)
        title = b["title"]
        desc = f"{title} — mentioned on Junkyard Love. A research trail from real conversations, not a store."
        people = []
        for m in b["mentions"]:
            n = m["mentioned_by"]
            if n and n not in people:
                people.append(n)
        body_bits = [
            f"<h1>{esc_text(title)}</h1>",
            '<p class="note">Mentioned on Junkyard Love. No affiliate links.</p>',
            "<h2>Who mentioned it</h2>",
            "<ul class=\"list\">",
        ]
        for m in b["mentions"]:
            who = esc_text(m["mentioned_by"])
            if m.get("guest_slug"):
                who = f'<a href="guests/{esc(m["guest_slug"])}/index.html">{esc_text(m["mentioned_by"])}</a>'
            body_bits.append(f"<li>{who} · {ep_link(m)}</li>")
        body_bits.append("</ul>")
        body_bits.append('<p class="note"><a href="books/index.html">All books</a></p>')
        html = (
            seo_head(f"{title} — Books — The Junkyard Love Podcast", desc, f"books/{slug}/")
            + "<body>\n<div class=\"wrap\">\n"
            + HEADER
            + "\n"
            + "\n".join(body_bits)
            + "\n"
            + FOOTER
            + "\n</div>\n"
            + SCRIPTS
            + "\n</body>\n</html>\n"
        )
        (d / "index.html").write_text(html, encoding="utf-8")


def write_books_index(books: list[dict], guest_map: dict[str, str]) -> None:
    desc = "Books guests mentioned on Junkyard Love — a research trail through real conversations, not a store."
    # browse by guest
    by_guest: dict[str, list] = {}
    for b in books:
        for m in b["mentions"]:
            gs = m.get("guest_slug")
            if not gs:
                continue
            by_guest.setdefault(gs, [])
            if b not in by_guest[gs]:
                by_guest[gs].append(b)

    # reverse map slug→name
    slug_to_name = {}
    for name, slug in guest_map.items():
        if slug and slug not in slug_to_name:
            # prefer longer/display names
            slug_to_name[slug] = name.title() if name.islower() else name
    # fix from guest pages
    for slug in by_guest:
        p = ROOT / "guests" / slug / "index.html"
        if p.exists():
            m = re.search(r"<h1>([^<]+)</h1>", p.read_text(encoding="utf-8", errors="ignore"))
            if m:
                slug_to_name[slug] = htmlmod.unescape(m.group(1)).strip()

    rows = []
    for b in books:
        people_bits = []
        seen = set()
        for m in b["mentions"]:
            n = m["mentioned_by"]
            if n in seen:
                continue
            seen.add(n)
            if m.get("guest_slug"):
                people_bits.append(
                    f'<a href="guests/{esc(m["guest_slug"])}/index.html">{esc_text(n)}</a>'
                )
            else:
                people_bits.append(esc_text(n))
        ep_bits = [ep_link(m) for m in b["mentions"]]
        rows.append(
            "<li class=\"book-item\">"
            f'<strong><a href="books/{esc(b["book_slug"])}/index.html">{esc_text(b["title"])}</a></strong>'
            f'<span class="note"> — mentioned by {" · ".join(people_bits)}</span><br>'
            + "<br>".join(ep_bits)
            + "</li>"
        )

    guest_browse = ""
    if by_guest:
        links = []
        for slug in sorted(by_guest.keys(), key=lambda s: slug_to_name.get(s, s).lower()):
            name = slug_to_name.get(slug, slug)
            n = len(by_guest[slug])
            links.append(
                f'<a class="mood-chip" href="guests/{esc(slug)}/index.html">{esc_text(name)} ({n})</a>'
            )
        guest_browse = (
            "<h2>Browse by guest</h2>\n"
            '<p class="note">Guests who mentioned at least one book — a doorway into their episodes.</p>\n'
            f'<div class="mood-doors">{"".join(links)}</div>\n'
        )

    body = f"""<h1>Books</h1>
<p class="note">Named books mentioned on the show. One row per book. No affiliate links.</p>
{guest_browse}<ul class="list book-list">
{''.join(rows)}
</ul>
"""
    html = (
        seo_head("Books mentioned on Junkyard Love", desc, "books/")
        + "<body>\n<div class=\"wrap\">\n"
        + HEADER
        + "\n"
        + body
        + FOOTER
        + "\n</div>\n"
        + SCRIPTS
        + "\n</body>\n</html>\n"
    )
    (ROOT / "books" / "index.html").write_text(html, encoding="utf-8")


def update_guest_pages(books: list[dict]) -> list[str]:
    """Add/replace Books mentioned section on guest pages. Returns guest slugs touched."""
    by_guest: dict[str, list] = {}
    for b in books:
        for m in b["mentions"]:
            gs = m.get("guest_slug")
            if not gs:
                continue
            by_guest.setdefault(gs, []).append((b, m))

    # dedupe books per guest
    for gs in list(by_guest.keys()):
        seen = set()
        uniq = []
        for b, m in by_guest[gs]:
            if b["book_slug"] in seen:
                continue
            seen.add(b["book_slug"])
            uniq.append((b, m))
        by_guest[gs] = uniq

    touched = []
    guests_dir = ROOT / "guests"
    for d in guests_dir.iterdir():
        if not d.is_dir():
            continue
        path = d / "index.html"
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        # strip existing Books mentioned section if present
        text2 = re.sub(
            r"\n?<h2>Books mentioned</h2>.*?(?=\n<footer class=\"site\">)",
            "\n",
            text,
            count=1,
            flags=re.S,
        )
        items = by_guest.get(d.name) or []
        if not items:
            if text2 != text:
                path.write_text(text2, encoding="utf-8")
                touched.append(d.name + " (cleared)")
            continue
        lines = ['<h2>Books mentioned</h2>', '<ul class="list book-list">']
        for b, m in items:
            # find best mention for this guest
            best = m
            for mm in b["mentions"]:
                if mm.get("guest_slug") == d.name and mm.get("start"):
                    best = mm
                    break
            lines.append(
                "<li class=\"book-item\">"
                f'<a href="books/{esc(b["book_slug"])}/index.html"><strong>{esc_text(b["title"])}</strong></a>'
                f" · {ep_link(best)}"
                "</li>"
            )
        lines.append("</ul>")
        section = "\n".join(lines) + "\n"
        if '<footer class="site">' not in text2:
            continue
        text2 = text2.replace('<footer class="site">', section + '<footer class="site">', 1)
        path.write_text(text2, encoding="utf-8")
        touched.append(d.name)
    return touched


def update_sitemap(books: list[dict]) -> None:
    path = ROOT / "sitemap.xml"
    text = path.read_text(encoding="utf-8")
    # remove existing book detail URLs
    text = re.sub(
        r"\s*<url>\s*<loc>[^<]*/books/[^/<]+/</loc>\s*</url>",
        "",
        text,
    )
    # ensure books index present
    books_index_loc = f"{SITE_BASE}/books/"
    alt_books = "https://jacobfromtheinternet.com/junkyard-love-archive/books/"
    block_lines = []
    for b in books:
        loc = f"{SITE_BASE}/books/{b['book_slug']}/"
        if loc not in text:
            block_lines.append(f"  <url>\n    <loc>{loc}</loc>\n  </url>")
    if block_lines:
        block = "\n".join(block_lines) + "\n"
        if "</urlset>" in text:
            text = text.replace("</urlset>", block + "</urlset>")
        else:
            text = text.rstrip() + "\n" + block
    path.write_text(text, encoding="utf-8")


def main() -> None:
    scraps = SRC / "books_index_scraps.json"
    src_path = scraps if scraps.exists() else (SRC / "books_index.json")
    raw = json.loads(src_path.read_text(encoding="utf-8"))
    before = len(raw.get("books") or [])
    eps = load_episodes()
    guest_map = load_guest_map()
    books = clean_books(raw.get("books") or [], eps, guest_map)
    out = {
        "title": "Books mentioned on Junkyard Love",
        "count": len(books),
        "before_count": before,
        "books": books,
    }
    payload = json.dumps(out, indent=2, ensure_ascii=False) + "\n"
    (SRC / "books_index.json").write_text(payload, encoding="utf-8")
    (ROOT / "assets" / "books_index.json").write_text(payload, encoding="utf-8")
    write_book_pages(books)
    write_books_index(books, guest_map)
    touched = update_guest_pages(books)
    update_sitemap(books)
    report = {
        "before": before,
        "after": len(books),
        "titles": [b["title"] for b in books],
        "guest_pages_with_books": [t for t in touched if not t.endswith("(cleared)")],
    }
    (SRC / "reports" / "BOOKS_CLEAN_STATS.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(f"books before={before} after={len(books)}")
    print("titles:", ", ".join(report["titles"]))
    print("guest pages:", ", ".join(report["guest_pages_with_books"]))


if __name__ == "__main__":
    main()
