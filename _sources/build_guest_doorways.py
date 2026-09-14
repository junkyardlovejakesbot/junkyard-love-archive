#!/usr/bin/env python3
"""Rebuild Good Room guest doorway pages + guests/index.html.

Sources of truth (no invented bios / brands / URLs / books / YouTube):
  - guests/index.html display names (canonical labels), with Brandon Cruz override
  - existing guests/*/index.html episode hrefs (multi-guest splits already curated)
  - assets/episodes_index.json, assets/quotes_clean.json, assets/books_index.json
  - _sources/content/*/source-about.md (identity sentence only when clear)
  - _sources/also_made.json (verified Also Made only)
  - assets/portraits/<slug>.{png,webp,jpg} when present

Good Room order:
  1. Name (+ optional portrait) (+ Zak alias line for brandon-cruz)
  2. One published-notes identity sentence (omit host-voice openers)
  3. Episode setlist
  4. Published quotes
  5. Authored books (+ optional Books mentioned if already on file)
  6. ALSO MADE (verified; skip entirely for authors with no non-book entry)
  7. Quiet clip-permission line

Does NOT invent bios, quotes, books, brands, or YouTube IDs.
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
SOURCES = DEPLOY / "_sources"
CONTENT = SOURCES / "content"

def content_dirs_index() -> dict[str, list[Path]]:
    """Map 4-digit episode numbers (and exact folder names) to content dirs."""
    by_num: dict[str, list[Path]] = {}
    by_name: dict[str, Path] = {}
    if not CONTENT.is_dir():
        return {}
    for d in CONTENT.iterdir():
        if not d.is_dir():
            continue
        by_name[d.name] = d
        m = re.match(r"^(\d{4})", d.name)
        if m:
            by_num.setdefault(m.group(1), []).append(d)
    # stash on function for reuse
    content_dirs_index.by_num = by_num  # type: ignore
    content_dirs_index.by_name = by_name  # type: ignore
    return by_num


def resolve_content_dirs(ep_slug: str, guest_slug: str | None = None) -> list[Path]:
    if not hasattr(content_dirs_index, "by_name"):
        content_dirs_index()
    by_name = content_dirs_index.by_name  # type: ignore
    by_num = content_dirs_index.by_num  # type: ignore
    out: list[Path] = []
    if ep_slug in by_name:
        out.append(by_name[ep_slug])
    m = re.match(r"^(\d{4})", ep_slug)
    if m:
        for d in by_num.get(m.group(1), []):
            if d not in out:
                out.append(d)
    # Non-numeric / renamed folders: match guest slug or distinctive ep tokens
    tokens = []
    if guest_slug:
        tokens.append(guest_slug)
        # also first+last if hyphenated
        parts = [x for x in guest_slug.split("-") if x and x not in {"of", "the", "and", "a"}]
        if len(parts) >= 2:
            tokens.append("-".join(parts[:2]))
    # ep slug without leading number
    rest = re.sub(r"^\d{4}-?", "", ep_slug)
    if rest and len(rest) > 8:
        tokens.append(rest[:40])
    for tok in tokens:
        for name, d in by_name.items():
            if tok and tok in name and d not in out:
                out.append(d)
    return out

PORTRAITS = ASSETS / "portraits"
BASE_SITE = "https://junkyardlovejakesbot.github.io/junkyard-love-archive"
MOTTO = "drink some water, stretch, love yourselves."
CLIP_LINE = "You’re welcome to clip this conversation. I won’t copyright you."

# Hard name rules
DISPLAY_OVERRIDES = {
    "brandon-cruz": "Brandon Cruz",
}
ALIAS_LINES = {
    "brandon-cruz": "Also known as Zak Wyld",
}
# Index may note alias in parentheses for findability
INDEX_NAME_OVERRIDES = {
    "brandon-cruz": "Brandon Cruz",
}

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
<link rel="canonical" href="{og_url}">
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
    return html.escape(s or "", quote=False)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def git_show(relpath: str) -> str | None:
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
        r'<li[^>]*>\s*<a href="guests/([^/]+)/index\.html">([^<]+)</a>',
        text,
    )
    names = {slug: html.unescape(name) for slug, name in items}
    for slug, name in DISPLAY_OVERRIDES.items():
        names[slug] = name
    return names


def existing_episode_map() -> dict[str, list[str]]:
    mapping: dict[str, list[str]] = {}
    for p in sorted(GUESTS_DIR.glob("*/index.html")):
        slug = p.parent.name
        src = git_show(f"guests/{slug}/index.html")
        if src is None:
            src = p.read_text(encoding="utf-8")
        # Prefer curated setlist block when present (idempotent across rebuilds)
        block = re.search(
            r'<ul class="list guest-episodes">(.*?)</ul>', src, re.S
        )
        region = block.group(1) if block else src
        # On legacy pages, prefer Episodes heading region before Topics/Watch
        if not block:
            m = re.search(
                r"<h2>Episodes</h2>(.*?)(?:<h2>Topics</h2>|<h2>Published|<h2>Watch|<h2>Books|<h2>Also|</div>\s*<footer)",
                src,
                re.S | re.I,
            )
            if m:
                region = m.group(1)
        eps = re.findall(r'href="episodes/([^/]+)/index\.html"', region)
        seen: set[str] = set()
        uniq: list[str] = []
        for e in eps:
            if e not in seen:
                seen.add(e)
                uniq.append(e)
        mapping[slug] = uniq
    return mapping


def portrait_src(slug: str) -> str | None:
    for ext in (".png", ".webp", ".jpg", ".jpeg"):
        p = PORTRAITS / f"{slug}{ext}"
        if p.is_file():
            return f"assets/portraits/{slug}{ext}"
    return None


def is_host_voice(s: str) -> bool:
    low = s.lower().strip()
    if low.startswith(
        (
            "in this episode",
            "in this conversation",
            "in this chat",
            "in this podcast",
            "today we’re",
            "today we're",
            "today we",
            "here the founder",
            "here he",
            "here she",
            "i find myself",
            "i get to",
            "i'm joined",
            "i am joined",
            "i sit down",
            "i'm sitting",
            "we’re joined",
            "we're joined",
            "this week we're",
            "this week we",
            "joining us",
            "welcome to",
            "welcome back",
            "what if ",
            "this is ",
            "hit follow",
            "to skip",
            "blu and i",
            "andre and rob",
            "the sense-making",
            "at the junkyard",
            "“",
            '"',
            "(",
        )
    ):
        return True
    if re.match(r"^my buddy\b", low):
        return True
    if " and i " in low or low.endswith(" and i"):
        # host co-presence openers
        if not re.match(r"^[A-Z][a-z]+ [A-Z]", s):
            return True
    if "stops by" in low or "leans back" in low or "spills his" in low:
        return True
    if re.match(r"^(rebecca|brandon|nate|matt|sigmar|barbara)\s+and i\b", low):
        return True
    return False


def is_identity_sentence(s: str) -> bool:
    if is_host_voice(s):
        return False
    # Clear "Name … is/are …" identity (allow He/She/They/Hailing)
    if re.match(
        r"^(?:[A-Z][\w'.\-]+(?:\s+(?:[A-Z][\w'.\-]+|of|the|de|da|van|von)){0,6}|He|She|They)\s+(?:is|are|was|has been)\b",
        s,
    ):
        return True
    if re.match(r"^Hailing from\b", s):
        return True
    if re.match(
        r"^Meet [A-Z][\w'.\-]+(?:\s+[A-Z][\w'.\-]+){0,5}\s*[—\-:]",
        s,
    ):
        return True
    return False


def first_identity_from_text(blob: str) -> str | None:
    if not blob or blob.strip().startswith("(none"):
        return None
    # drop markdown noise
    text = re.sub(r"^#+\s.*$", "", blob, flags=re.M)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    for para in paras:
        plain = re.sub(r"[*_`]", "", para)
        plain = re.sub(r"\s+", " ", plain).strip()
        if is_host_voice(plain):
            continue
        # first sentence
        m = re.match(r"^([^.?!]{20,220}[.?!])", plain)
        if not m:
            continue
        cand = m.group(1).strip()
        if len(cand) > 220:
            continue
        if is_identity_sentence(cand):
            return cand
    return None


def extract_identity_bio(slug: str, old_page: str) -> str | None:
    # Prefer published source-about across mapped episodes (caller passes via side channel)
    # Fallback: existing about block on prior page
    about_blocks = re.findall(r'<div class="about">(.*?)</div>', old_page, re.S)
    for block in about_blocks:
        for p in re.findall(r"<p>(.*?)</p>", block, re.S):
            plain = re.sub(r"<[^>]+>", "", p)
            plain = html.unescape(plain).strip()
            if plain and is_identity_sentence(plain.split(".")[0] + "." if "." in plain else plain):
                m = re.match(r"^([^.?!]{20,220}[.?!])", plain)
                if m and is_identity_sentence(m.group(1).strip()):
                    return m.group(1).strip()
    # lede
    m = re.search(r'<p class="lede">(.*?)</p>', old_page, re.S)
    if m:
        plain = html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip()
        if plain and is_identity_sentence(plain):
            return plain
    return None


def identity_from_sources(ep_slugs: list[str], guest_slug: str | None = None) -> str | None:
    content_dirs_index()
    for es in ep_slugs:
        for d in resolve_content_dirs(es, guest_slug=guest_slug):
            about = d / "source-about.md"
            if about.exists():
                bio = first_identity_from_text(about.read_text(encoding="utf-8", errors="replace"))
                if bio:
                    return bio
    for es in ep_slugs:
        for d in resolve_content_dirs(es, guest_slug=guest_slug):
            desc = d / "source-description.md"
            if desc.exists():
                bio = first_identity_from_text(desc.read_text(encoding="utf-8", errors="replace"))
                if bio:
                    return bio
    return None


def person_json_ld(name: str, slug: str, episodes: list[dict], alias: str | None = None) -> str:
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
    data: dict = {
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
    if alias:
        data["alternateName"] = alias.replace("Also known as ", "").strip()
    blob = json.dumps(data, ensure_ascii=False, indent=2)
    return f'<script type="application/ld+json">\n{blob}\n</script>'


def books_for_guest(slug: str, books: list[dict]) -> dict[str, list[dict]]:
    authored: list[dict] = []
    mentioned: list[dict] = []
    seen_a: set[str] = set()
    seen_m: set[str] = set()
    for b in books:
        bslug = b.get("book_slug")
        if not bslug:
            continue
        if b.get("bucket") == "authored" and b.get("authored_guest_slug") == slug:
            if bslug not in seen_a:
                seen_a.add(bslug)
                authored.append(b)
            continue
        hit = False
        for m in b.get("mentions") or []:
            if m.get("guest_slug") == slug:
                hit = True
                break
        if not hit and b.get("guest_slug") == slug and b.get("bucket") != "authored":
            hit = True
        if hit and bslug not in seen_a and bslug not in seen_m:
            seen_m.add(bslug)
            mentioned.append(b)
    return {"authored": authored, "mentioned": mentioned}


def quotes_for_episodes(ep_slugs: set[str], quotes: list[dict]) -> list[dict]:
    out = []
    for q in quotes:
        if q.get("source") != "published":
            continue
        if q.get("episode_slug") in ep_slugs:
            out.append(q)
    return out


def fill_header(**kw) -> str:
    out = HEADER
    for k, v in kw.items():
        out = out.replace("{" + k + "}", v)
    return out


def render_guest_page(
    slug: str,
    display_name: str,
    bio: str | None,
    episodes: list[dict],
    books: dict[str, list[dict]],
    quotes: list[dict],
    also_made: dict | None,
    has_authored: bool,
) -> str:
    desc = f"{display_name} on The Junkyard Love Podcast — episodes, published quotes, and what they made (when verified)."
    og_url = f"{BASE_SITE}/guests/{slug}/"
    alias = ALIAS_LINES.get(slug)
    json_ld = person_json_ld(display_name, slug, episodes, alias)

    parts = [
        fill_header(
            title=esc(f"{display_name} — The Junkyard Love Podcast"),
            description=esc(desc),
            og_title=esc(f"{display_name} — The Junkyard Love Podcast"),
            og_url=esc(og_url),
            json_ld=json_ld,
        ),
        f"<h1>{text_esc(display_name)}</h1>",
    ]

    portrait = portrait_src(slug)
    if portrait:
        parts.append(
            f'<p class="guest-portrait-wrap"><img class="guest-portrait" src="{esc(portrait)}" '
            f'alt="{esc(display_name)}" width="320" height="320" loading="lazy"></p>'
        )

    if alias:
        parts.append(f'<p class="guest-alias note">{text_esc(alias)}</p>')

    if bio:
        parts.append(f'<p class="lede guest-about">{text_esc(bio)}</p>')

    # Episode setlist
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
    authored_books = books.get("authored") or []
    mentioned_books = books.get("mentioned") or []
    if authored_books:
        parts.append("<h2>Authored books</h2>")
        parts.append('<ul class="list book-list">')
        for b in authored_books:
            bslug = b.get("book_slug")
            title = b.get("title") or bslug
            author = b.get("author") or ""
            extra = f' <span class="note">({text_esc(author)})</span>' if author else ""
            if bslug:
                parts.append(
                    f'<li class="book-item"><a href="books/{esc(bslug)}/index.html"><strong>{text_esc(title)}</strong></a>{extra}</li>'
                )
            else:
                parts.append(f"<li>{esc(title)}{extra}</li>")
        parts.append("</ul>")
    if mentioned_books:
        parts.append("<h2>Books mentioned</h2>")
        parts.append('<ul class="list book-list">')
        for b in mentioned_books:
            bslug = b.get("book_slug")
            title = b.get("title") or bslug
            author = b.get("author") or ""
            extra = f' <span class="note">— {text_esc(author)}</span>' if author else ""
            if bslug:
                parts.append(
                    f'<li class="book-item"><a href="books/{esc(bslug)}/index.html"><strong>{text_esc(title)}</strong></a>{extra}</li>'
                )
            else:
                parts.append(f"<li>{esc(title)}{extra}</li>")
        parts.append("</ul>")

    # ALSO MADE
    if also_made:
        parts.append('<h2 class="also-made">Also made</h2>')
        label = also_made.get("label") or "Also made"
        url = also_made.get("url") or ""
        kind = also_made.get("kind") or ""
        kind_bit = f' <span class="note">({text_esc(kind)})</span>' if kind else ""
        if url:
            parts.append(
                f'<p class="also-made-item"><a href="{esc(url)}" target="_blank" rel="noopener">'
                f"{text_esc(label)}</a>{kind_bit}</p>"
            )
        else:
            parts.append(f"<p class=\"also-made-item\">{text_esc(label)}{kind_bit}</p>")
        vurl = also_made.get("video_url")
        if vurl:
            parts.append(
                f'<p class="also-made-video note"><a href="{esc(vurl)}" target="_blank" rel="noopener">'
                f"Video</a></p>"
            )
    elif not has_authored:
        # heading omitted when unverified for non-authors (listed in NEEDS report)
        pass
    # authors without non-book Also Made: skip section entirely

    parts.append(f'<p class="clip-permission note">{text_esc(CLIP_LINE)}</p>')
    parts.append(FOOTER)
    return "\n".join(parts) + "\n"


def render_index(guests: list[dict]) -> str:
    desc = "People who sat down for long conversations on Junkyard Love."
    og_url = f"{BASE_SITE}/guests/"
    rows = []
    for g in guests:
        index_name = g.get("index_name") or g["display_name"]
        alias_note = ""
        filter_name = index_name.lower()
        if g["slug"] == "brandon-cruz":
            alias_note = ' <span class="note">(also Zak Wyld)</span>'
            filter_name = f"{filter_name} zak wyld zack wyld"
        rows.append(
            f'<li data-guest-name="{esc(filter_name)}" '
            f'data-guest-slug="{esc(g["slug"])}">'
            f'<a href="guests/{esc(g["slug"])}/index.html">{text_esc(index_name)}</a>{alias_note}</li>'
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
        '<input id="guest-filter" type="search" placeholder="Type a name…" autocomplete="off" '
        'style="width:min(100%,22rem);padding:0.5rem 0.75rem;border-radius:6px;border:1px solid var(--border, #444);'
        'background:var(--bg-elevated, #1a1a1a);color:inherit;"></p>',
        '<ul class="list" id="guest-list">',
        "".join(rows),
        "</ul>",
        filter_js,
        FOOTER,
    ]
    return "\n".join(body) + "\n"


def ensure_portrait_css() -> None:
    css_path = ASSETS / "style.css"
    if not css_path.exists():
        return
    css = css_path.read_text(encoding="utf-8")
    if "guest-portrait" in css:
        return
    css += """

/* Good Room guest portraits */
.guest-portrait-wrap { margin: 0.75rem 0 1rem; }
img.guest-portrait {
  display: block;
  width: min(100%, 320px);
  height: auto;
  border-radius: 10px;
  border: 1px solid var(--border, #444);
}
.guest-alias { margin-top: -0.35rem; }
.also-made-item { margin: 0.35rem 0 0.75rem; }
.clip-permission { margin-top: 2rem; opacity: 0.85; }
"""
    css_path.write_text(css, encoding="utf-8")


def main() -> None:
    episodes_doc = load_json(ASSETS / "episodes_index.json")
    ep_by_slug = {e["slug"]: e for e in episodes_doc["episodes"]}
    quotes = load_json(ASSETS / "quotes_clean.json")["quotes"]
    books = load_json(ASSETS / "books_index.json")["books"]
    also_made_doc = load_json(SOURCES / "also_made.json") if (SOURCES / "also_made.json").exists() else {}

    authored_slugs = {
        b["authored_guest_slug"]
        for b in books
        if b.get("bucket") == "authored" and b.get("authored_guest_slug")
    }

    index_names = parse_index_names()
    ep_map = existing_episode_map()
    ensure_portrait_css()

    folder_slugs = sorted(p.parent.name for p in GUESTS_DIR.glob("*/index.html"))
    guests_out = []
    bios_kept = []
    also_filled = []
    also_omitted = []
    needs_jacob_also = []
    portraits_wired = []
    needs_jacob = []

    for slug in folder_slugs:
        display = DISPLAY_OVERRIDES.get(slug) or index_names.get(slug)
        if not display:
            page = (GUESTS_DIR / slug / "index.html").read_text(encoding="utf-8")
            m = re.search(r"<h1>([^<]+)</h1>", page)
            display = m.group(1) if m else slug
            needs_jacob.append(f"Guest folder `{slug}` missing from prior index labels — left as `{display}`")

        # Strip old parenthetical Zack from display if still present
        if slug == "brandon-cruz":
            display = "Brandon Cruz"

        old_page = git_show(f"guests/{slug}/index.html") or (
            GUESTS_DIR / slug / "index.html"
        ).read_text(encoding="utf-8")

        ep_slugs = ep_map.get(slug) or []
        bio = identity_from_sources(ep_slugs, guest_slug=slug) or extract_identity_bio(slug, old_page)
        if bio:
            bios_kept.append(slug)

        episodes = []
        for es in ep_slugs:
            ep = ep_by_slug.get(es)
            if ep:
                episodes.append(ep)
            else:
                needs_jacob.append(f"Guest `{slug}` linked episode `{es}` not in episodes_index")

        episodes_sorted = sorted(
            episodes,
            key=lambda e: (e.get("date") or "", e.get("number") or ""),
            reverse=True,
        )
        ep_slug_set = {e["slug"] for e in episodes_sorted}
        g_quotes = quotes_for_episodes(ep_slug_set, quotes)
        g_books = books_for_guest(slug, books)
        has_authored = slug in authored_slugs or bool(g_books["authored"])

        am = also_made_doc.get(slug)
        if am and am.get("url") and am.get("label"):
            also_filled.append(slug)
        else:
            am = None
            if has_authored:
                # skip section — books cover what they made
                pass
            else:
                also_omitted.append(slug)
                needs_jacob_also.append(slug)

        if portrait_src(slug):
            portraits_wired.append(slug)

        html_out = render_guest_page(
            slug,
            display,
            bio,
            episodes_sorted,
            g_books,
            g_quotes,
            am,
            has_authored,
        )
        (GUESTS_DIR / slug / "index.html").write_text(html_out, encoding="utf-8")

        guests_out.append(
            {
                "slug": slug,
                "display_name": display,
                "index_name": INDEX_NAME_OVERRIDES.get(slug, display),
                "episode_count": len(episodes_sorted),
                "sort_key": display.lstrip('"').lower(),
            }
        )

    guests_out.sort(key=lambda g: g["sort_key"])
    (GUESTS_DIR / "index.html").write_text(render_index(guests_out), encoding="utf-8")

    # NEEDS JACOB Also Made report
    reports = SOURCES / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    needs_lines = [
        "# NEEDS JACOB — Also Made",
        "",
        "Guests with **no authored book** on file and **no verified** Also Made entry",
        "(company / band / practice / podcast / product / movement + real URL from published notes).",
        "",
    ]
    for slug in also_omitted:
        name = next((g["display_name"] for g in guests_out if g["slug"] == slug), slug)
        needs_lines.append(f"- `{slug}` — {name}")
    needs_lines.append("")
    (reports / "NEEDS_JACOB_ALSO_MADE.md").write_text("\n".join(needs_lines), encoding="utf-8")

    report = {
        "guest_pages": len(guests_out),
        "bios_kept": bios_kept,
        "also_made_filled": also_filled,
        "also_made_omitted_non_author": also_omitted,
        "portraits_wired": portraits_wired,
        "needs_jacob": needs_jacob,
        "brandon_cruz": next(g for g in guests_out if g["slug"] == "brandon-cruz"),
        "rebecca_wyld": next(g for g in guests_out if g["slug"] == "rebecca-wyld"),
        "rebecca_wild": next(g for g in guests_out if g["slug"] == "rebecca-wild"),
    }
    (reports / "GUEST_DOORWAYS_BUILD.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )

    # SHIP report
    base = BASE_SITE
    ship = [
        "# SHIP — Good Room guest pages + Also Made",
        "",
        f"- Guest pages rebuilt: **{len(guests_out)}**",
        f"- Also Made filled: **{len(also_filled)}** (`{', '.join(also_filled)}`)",
        f"- Also Made omitted (non-authors → NEEDS JACOB): **{len(also_omitted)}**",
        f"- Portraits wired (file present at build): **{len(portraits_wired)}** — {portraits_wired}",
        f"- Identity bios kept: **{len(bios_kept)}**",
        "",
        "## Name notes",
        "",
        "- **Brandon Cruz** single doorway `guests/brandon-cruz/` with alias line "
        "`Also known as Zak Wyld` (episode slug `0004-zack-wyld` unchanged; Zak/Zack treated as one alias).",
        "- **Rebecca Wyld** (`rebecca-wyld`, ep 0037) ≠ **Rebecca Wild** (`rebecca-wild`, ep 0110) — separate folders.",
        "- Portraits: wired for `sigmar-berg`, `barbara-mcafee`, `rebecca-wild`. "
        "Skipped (no trustworthy face): `brandon-cruz`, `rebecca-wyld`.",
        "",
        "## Live URL stubs",
        "",
        f"- Guests index: {base}/guests/",
        f"- Brandon Cruz: {base}/guests/brandon-cruz/",
        f"- Rebecca Wyld: {base}/guests/rebecca-wyld/",
        f"- Rebecca Wild: {base}/guests/rebecca-wild/",
        f"- Author guest (Sigmar Berg): {base}/guests/sigmar-berg/",
        f"- Also-made-only example (Anna Cantwell): {base}/guests/anna-cantwell/",
        f"- Also-made-only example (Scott Pisapia): {base}/guests/scott-pisapia/",
        "",
        "## Example Also Made entries",
        "",
    ]
    for ex in ("sigmar-berg", "anna-cantwell", "scott-pisapia", "brent-spirit", "matt-mcgee"):
        am = also_made_doc.get(ex) or {}
        ship.append(
            f"- `{ex}`: {am.get('label')} → {am.get('url')} ({am.get('kind')})"
        )
    ship.append("")
    ship.append(f"See also: `_sources/reports/NEEDS_JACOB_ALSO_MADE.md` ({len(also_omitted)} guests).")
    ship.append("")
    (reports / "SHIP_GOOD_ROOM.md").write_text("\n".join(ship), encoding="utf-8")

    print(f"Rebuilt {len(guests_out)} Good Room guest pages + index")
    print(f"Also Made filled ({len(also_filled)}): {also_filled}")
    print(f"Also Made omitted / NEEDS JACOB ({len(also_omitted)})")
    print(f"Portraits wired: {portraits_wired}")
    print(f"Bios kept ({len(bios_kept)}): {bios_kept}")


if __name__ == "__main__":
    main()
