#!/usr/bin/env python3
"""Rebuild guest doorway pages + guests/index.html from catalog data only.

Sources of truth:
  - guests/index.html display names (canonical labels)
  - existing guests/*/index.html episode hrefs (multi-guest splits already curated)
  - assets/episodes_index.json (titles, dates, topics, youtube)
  - assets/quotes_clean.json (published quotes only)
  - assets/books_index.json (books naming this guest via guest_slug / mentions)

Does NOT invent bios, quotes, books, or YouTube IDs.
Does NOT git commit or push.
"""
from __future__ import annotations

import html
import json
import re
import subprocess
from pathlib import Path

DEPLOY = Path(__file__).resolve().parents[1]
GUESTS_DIR = DEPLOY / "guests"
ASSETS = DEPLOY / "assets"
BASE_SITE = "https://junkyardlovejakesbot.github.io/junkyard-love-archive"
MOTTO = "drink some water, stretch, love yourselves."

HEADER = """<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<base href="/junkyard-love-archive/">
<script>(function(){try{var t=localStorage.getItem("jylp-theme");if(t==="light"||t==="dark")document.documentElement.setAttribute("data-theme",t);}catch(e){}})();</script>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<meta property="og:title" content="{og_title}">
<meta property="og:description" content="{description}">
<meta property="og:type" content="website">
<meta property="og:url" content="{og_url}">
<link rel="stylesheet" href="assets/style.css">
{json_ld}
</head>
<body>
<div class="wrap">
<header class="site">
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
</header>
"""

FOOTER = f"""
<footer class="site">
  <p class="motto">{MOTTO}</p>
  <p class="footer-links">
    <a href="donate/index.html">Donate</a>
    ·
    <a href="merch/index.html">Merch</a>
    ·
    <a href="https://www.instagram.com/jacobfromtheinternet/" target="_blank" rel="noopener">Instagram</a>
  </p>
</footer>
</div>
<script src="assets/theme.js" defer></script>
<script src="assets/archive.js" defer></script>
</body>
</html>
"""


def esc(s: str) -> str:
    return html.escape(s or "", quote=True)


def text_esc(s: str) -> str:
    """Escape for HTML text nodes (keep apostrophes/quotes readable)."""
    return html.escape(s or "", quote=False)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def git_show(relpath: str) -> str | None:
    """Read a file from HEAD so rebuilds stay idempotent against prior site copy."""
    try:
        r = subprocess.run(
            ["git", "show", f"HEAD:{relpath}"],
            cwd=DEPLOY,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    if r.returncode != 0:
        return None
    return r.stdout


def parse_index_names() -> dict[str, str]:
    text = git_show("guests/index.html")
    if text is None:
        text = (GUESTS_DIR / "index.html").read_text(encoding="utf-8")
    items = re.findall(
        r'<li><a href="guests/([^/]+)/index\.html">([^<]+)</a>',
        text,
    )
    return {slug: html.unescape(name) for slug, name in items}


def existing_episode_map() -> dict[str, list[str]]:
    mapping: dict[str, list[str]] = {}
    for p in sorted(GUESTS_DIR.glob("*/index.html")):
        slug = p.parent.name
        # Prefer HEAD mapping (pre-rebuild) so multi-guest splits stay curated
        src = git_show(f"guests/{slug}/index.html")
        if src is None:
            src = p.read_text(encoding="utf-8")
        eps = re.findall(r'href="episodes/([^/]+)/index\.html"', src)
        seen = set()
        uniq = []
        for e in eps:
            if e not in seen:
                seen.add(e)
                uniq.append(e)
        mapping[slug] = uniq
    return mapping


def extract_one_line_bio(page_text: str) -> str | None:
    """Keep at most one short existing identity bio; never invent."""
    about_blocks = re.findall(r'<div class="about">(.*?)</div>', page_text, re.S)
    paras: list[str] = []
    for block in about_blocks:
        for p in re.findall(r"<p>(.*?)</p>", block, re.S):
            plain = re.sub(r"<[^>]+>", "", p)
            plain = html.unescape(plain).strip()
            if plain:
                paras.append(plain)
    if not paras:
        return None

    def is_identity(s: str) -> bool:
        low = s.lower().strip()
        # Reject episode-note openers / host voice
        if low.startswith(
            (
                "in this episode",
                "in this conversation",
                "in this chat",
                "i find myself",
                "i get to",
                "i'm joined",
                "i am joined",
                "what if ",
                "this is ",
                "“",
                '"',
            )
        ):
            return False
        if "stops by" in low or "leans back" in low or "spills his" in low:
            return False
        # Identity cues
        if re.match(
            r"^(?:[A-Z][\w'.\-]+(?:\s+[A-Z][\w'.\-]+){0,4}|He|She|They)\s+(?:is|are|'s)\b",
            s,
        ):
            return True
        if re.match(r"^Hailing from\b", s):
            return True
        return False

    # One sentence max, identity only
    first = paras[0]
    m = re.match(r"^([^.?!]{20,140}[.?!])", first)
    if not m:
        return None
    cand = m.group(1).strip()
    if len(cand) > 140:
        return None
    if is_identity(cand):
        return cand
    return None


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


def person_json_ld(name: str, slug: str, episodes: list[dict]) -> str:
    url = f"{BASE_SITE}/guests/{slug}/"
    items = []
    for i, ep in enumerate(episodes, 1):
        items.append(
            {
                "@type": "ListItem",
                "position": i,
                "url": f"{BASE_SITE}/episodes/{ep['slug']}/",
                "name": ep.get("browse_title") or ep.get("canonical_title") or ep["slug"],
            }
        )
    data = {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": name,
        "url": url,
        "subjectOf": {
            "@type": "ItemList",
            "name": f"Junkyard Love episodes with {name}",
            "numberOfItems": len(items),
            "itemListElement": items,
        },
    }
    blob = json.dumps(data, ensure_ascii=False, indent=2)
    return f'<script type="application/ld+json">\n{blob}\n</script>'


def books_for_guest(slug: str, books: list[dict]) -> list[dict]:
    out = []
    seen = set()
    for b in books:
        hit = b.get("guest_slug") == slug
        if not hit:
            for m in b.get("mentions") or []:
                if m.get("guest_slug") == slug:
                    hit = True
                    break
        if hit and b.get("book_slug") not in seen:
            seen.add(b.get("book_slug"))
            out.append(b)
    return out


def quotes_for_episodes(ep_slugs: set[str], quotes: list[dict]) -> list[dict]:
    out = []
    for q in quotes:
        if q.get("source") != "published":
            continue
        if q.get("episode_slug") in ep_slugs:
            out.append(q)
    return out


def render_guest_page(
    slug: str,
    display_name: str,
    bio: str | None,
    episodes: list[dict],
    books: list[dict],
    quotes: list[dict],
) -> str:
    ep_count = len(episodes)
    desc = f"Doorway for {display_name} on The Junkyard Love Podcast — episodes, topics, published quotes, and books already on file."
    og_url = f"{BASE_SITE}/guests/{slug}/"
    json_ld = person_json_ld(display_name, slug, episodes)

    def fill_header(**kw):
        out = HEADER
        for k, v in kw.items():
            out = out.replace("{" + k + "}", v)
        return out

    parts = [
        fill_header(
            title=esc(f"{display_name} — The Junkyard Love Podcast"),
            description=esc(desc),
            og_title=esc(f"{display_name} — The Junkyard Love Podcast"),
            og_url=esc(og_url),
            json_ld=json_ld,
        ),
        f"<h1>{text_esc(display_name)}</h1>",
        f'<p class="note">Appeared on The Junkyard Love Podcast ({ep_count} episode{"s" if ep_count != 1 else ""})</p>',
    ]
    if bio:
        parts.append(f'<p class="lede">{text_esc(bio)}</p>')

    # Episodes
    parts.append("<h2>Episodes</h2>")
    if not episodes:
        parts.append('<p class="note">(no episodes on file)</p>')
    else:
        parts.append('<ul class="list guest-episodes">')
        for ep in episodes:
            title = ep.get("browse_title") or ep.get("canonical_title") or ep["slug"]
            num = ep.get("number") or ""
            date = ep.get("date") or ""
            dur = ep.get("duration") or ""
            meta_bits = [f"Episode {num}" if num else None, date or None, dur or None]
            meta = " · ".join(b for b in meta_bits if b)
            href = f"episodes/{ep['slug']}/index.html"
            parts.append(
                f'<li><a href="{esc(href)}"><strong>{text_esc(num)}</strong> — {text_esc(title)}</a>'
                f'<br><span class="note">{text_esc(meta)}</span></li>'
            )
        parts.append("</ul>")

    # Topic shelves
    topic_map: dict[str, str] = {}
    for ep in episodes:
        for t in ep.get("topics") or []:
            if isinstance(t, dict) and t.get("slug"):
                topic_map[t["slug"]] = t.get("title") or t["slug"]
    parts.append("<h2>Topics</h2>")
    if not topic_map:
        parts.append('<p class="note">(no topic shelves on file for these episodes)</p>')
    else:
        parts.append('<ul class="list guest-topics">')
        for tslug, ttitle in sorted(topic_map.items(), key=lambda x: x[1].lower()):
            parts.append(
                f'<li><a href="topics/{esc(tslug)}/index.html">{text_esc(ttitle)}</a></li>'
            )
        parts.append("</ul>")

    # Published quotes
    parts.append("<h2>Published quotes</h2>")
    if not quotes:
        parts.append('<p class="note">(none published for these episodes)</p>')
    else:
        for q in quotes:
            text = (q.get("text") or "").strip()
            if not text:
                continue
            ep_num = q.get("episode_number") or ""
            ep_slug = q.get("episode_slug") or ""
            cite = f"Episode {ep_num}" if ep_num else ep_slug
            parts.append("<blockquote>")
            parts.append(f"<p>{text_esc(text)}</p>")
            if ep_slug:
                parts.append(
                    f'<p class="note"><a href="episodes/{esc(ep_slug)}/index.html">{esc(cite)}</a></p>'
                )
            parts.append("</blockquote>")

    # Books
    parts.append("<h2>Books on file</h2>")
    if not books:
        parts.append('<p class="note">(none in the books index for this guest)</p>')
    else:
        parts.append('<ul class="list book-list">')
        for b in books:
            bslug = b.get("book_slug")
            title = b.get("title") or bslug
            if bslug:
                parts.append(
                    f'<li class="book-item"><a href="books/{esc(bslug)}/index.html"><strong>{text_esc(title)}</strong></a></li>'
                )
            else:
                parts.append(f"<li>{esc(title)}</li>")
        parts.append("</ul>")

    # YouTube / archive links from episodes
    parts.append("<h2>Watch / archive</h2>")
    parts.append('<ul class="list guest-watch">')
    for ep in episodes:
        title = ep.get("browse_title") or ep.get("canonical_title") or ep["slug"]
        num = ep.get("number") or ""
        archive = f"episodes/{ep['slug']}/index.html"
        yid = ep.get("youtube_id")
        yurl = ep.get("youtube_url")
        if yid and not yurl:
            yurl = f"https://www.youtube.com/watch?v={yid}"
        line = f'<li><strong>{esc(num)}</strong> — {esc(title)} · <a href="{esc(archive)}">archive</a>'
        if yurl:
            line += f' · <a href="{esc(yurl)}" target="_blank" rel="noopener">YouTube</a>'
        line += "</li>"
        parts.append(line)
    parts.append("</ul>")

    parts.append(FOOTER)
    return "\n".join(parts) + "\n"


def render_index(guests: list[dict]) -> str:
    desc = "People who sat down for long conversations on Junkyard Love."
    og_url = f"{BASE_SITE}/guests/"
    rows = []
    for g in guests:
        count = g["episode_count"]
        count_html = f' <span class="note">({count})</span>'
        rows.append(
            f'<li data-guest-name="{esc(g["display_name"].lower())}" data-guest-slug="{esc(g["slug"])}">'
            f'<a href="guests/{esc(g["slug"])}/index.html">{text_esc(g["display_name"])}</a>{count_html}</li>'
        )
    filter_js = """
<script>
(function () {
  var input = document.getElementById("guest-filter");
  var list = document.getElementById("guest-list");
  if (!input || !list) return;
  input.addEventListener("input", function () {
    var q = (input.value || "").toLowerCase().trim();
    var items = list.querySelectorAll("li");
    for (var i = 0; i < items.length; i++) {
      var name = items[i].getAttribute("data-guest-name") || "";
      var slug = items[i].getAttribute("data-guest-slug") || "";
      var show = !q || name.indexOf(q) !== -1 || slug.indexOf(q) !== -1;
      items[i].style.display = show ? "" : "none";
    }
  });
})();
</script>
"""
    def fill_header(**kw):
        out = HEADER
        for k, v in kw.items():
            out = out.replace("{" + k + "}", v)
        return out

    body = [
        fill_header(
            title=esc("Guests — The Junkyard Love Podcast"),
            description=esc(desc),
            og_title=esc("Guests — The Junkyard Love Podcast"),
            og_url=esc(og_url),
            json_ld="",
        ),
        "<h1>Guests</h1>",
        '<p class="note">Everyone who sat down for a conversation. Filter by name, or scan A–Z.</p>',
        '<p><label class="note" for="guest-filter">Filter guests</label><br>',
        '<input id="guest-filter" type="search" placeholder="Type a name…" autocomplete="off" style="width:min(100%,22rem);padding:0.5rem 0.75rem;border-radius:6px;border:1px solid var(--border, #444);background:var(--bg-elevated, #1a1a1a);color:inherit;"></p>',
        '<ul class="list" id="guest-list">',
        "".join(rows),
        "</ul>",
        filter_js,
        FOOTER,
    ]
    return "\n".join(body) + "\n"


def main() -> None:
    episodes_doc = load_json(ASSETS / "episodes_index.json")
    ep_by_slug = {e["slug"]: e for e in episodes_doc["episodes"]}
    quotes = load_json(ASSETS / "quotes_clean.json")["quotes"]
    books = load_json(ASSETS / "books_index.json")["books"]

    index_names = parse_index_names()
    ep_map = existing_episode_map()

    # Ensure every guest folder is covered
    folder_slugs = sorted(p.parent.name for p in GUESTS_DIR.glob("*/index.html"))
    guests_out = []
    bios_kept = []
    needs_jacob = []

    for slug in folder_slugs:
        display = index_names.get(slug)
        if not display:
            # fall back to existing h1
            page = (GUESTS_DIR / slug / "index.html").read_text(encoding="utf-8")
            m = re.search(r"<h1>([^<]+)</h1>", page)
            display = m.group(1) if m else slug
            needs_jacob.append(f"Guest folder `{slug}` missing from prior index labels — left as `{display}`")

        old_page = git_show(f"guests/{slug}/index.html") or (GUESTS_DIR / slug / "index.html").read_text(encoding="utf-8")
        bio = extract_one_line_bio(old_page)
        if bio:
            bios_kept.append(slug)

        ep_slugs = ep_map.get(slug) or []
        episodes = []
        for es in ep_slugs:
            ep = ep_by_slug.get(es)
            if ep:
                episodes.append(ep)
            else:
                needs_jacob.append(f"Guest `{slug}` linked episode `{es}` not in episodes_index")

        # newest first for doorway
        episodes_sorted = sorted(
            episodes,
            key=lambda e: (e.get("date") or "", e.get("number") or ""),
            reverse=True,
        )
        ep_slug_set = {e["slug"] for e in episodes_sorted}
        g_quotes = quotes_for_episodes(ep_slug_set, quotes)
        g_books = books_for_guest(slug, books)

        html_out = render_guest_page(
            slug, display, bio, episodes_sorted, g_books, g_quotes
        )
        (GUESTS_DIR / slug / "index.html").write_text(html_out, encoding="utf-8")

        guests_out.append(
            {
                "slug": slug,
                "display_name": display,
                "episode_count": len(episodes_sorted),
                "sort_key": display.lstrip('"').lower(),
            }
        )

    guests_out.sort(key=lambda g: g["sort_key"])
    (GUESTS_DIR / "index.html").write_text(render_index(guests_out), encoding="utf-8")

    report = {
        "guest_pages": len(guests_out),
        "bios_kept": bios_kept,
        "needs_jacob": needs_jacob,
        "wyld_wild_separate": {
            "rebecca-wyld": next(g for g in guests_out if g["slug"] == "rebecca-wyld"),
            "rebecca-wild": next(g for g in guests_out if g["slug"] == "rebecca-wild"),
        },
    }
    out = DEPLOY / "_sources" / "reports" / "GUEST_DOORWAYS_BUILD.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Rebuilt {len(guests_out)} guest pages + index")
    print(f"Bios kept ({len(bios_kept)}): {bios_kept}")
    if needs_jacob:
        print("NEEDS JACOB:")
        for line in needs_jacob:
            print(" -", line)


if __name__ == "__main__":
    main()
