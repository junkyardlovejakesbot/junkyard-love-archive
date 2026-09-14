#!/usr/bin/env python3
"""Build honest book library: authored vs mentioned buckets.

Sources:
  - assets/_sources books_index.json (existing mentioned shelf)
  - _sources/books_library_enrichment.json (verified author/bucket/url + additional authored)

Does NOT invent books, co-authors, years, ISBNs, URLs, or LLM blurbs.
Does NOT git commit or push.
"""
from __future__ import annotations

import html as htmlmod
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "_sources"
ASSETS = ROOT / "assets"
SITE_BASE = "https://junkyardlovejakesbot.github.io/junkyard-love-archive"

HEADER = """<header class="site">
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


def seo_head(title: str, description: str, path: str) -> str:
    url = f"{SITE_BASE}/{path.lstrip('/')}"
    if path.endswith("/") and not url.endswith("/"):
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
<link rel="canonical" href="{esc(url)}">
</head>
"""


def ep_link(m: dict) -> str:
    slug = m.get("episode_slug") or ""
    href = f"episodes/{slug}/index.html"
    label = f"Episode {m.get('episode_number') or ''} — {m.get('browse_title') or slug}".strip(" —")
    if m.get("start"):
        parts = str(m["start"]).split(":")
        if len(parts) == 3:
            href += f"#t-{parts[0]}-{parts[1]}-{parts[2]}"
        label += f" · {m['start']}"
    return f'<a href="{esc(href)}">{esc_text(label)}</a>'


def load_enrichment() -> dict:
    return json.loads((SRC / "books_library_enrichment.json").read_text(encoding="utf-8"))


def load_base_books() -> list[dict]:
    path = SRC / "books_index.json"
    if not path.exists():
        path = ASSETS / "books_index.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return list(data.get("books") or [])


def guest_display_name(slug: str) -> str:
    p = ROOT / "guests" / slug / "index.html"
    if p.exists():
        m = re.search(r"<h1>([^<]+)</h1>", p.read_text(encoding="utf-8", errors="ignore"))
        if m:
            return htmlmod.unescape(m.group(1)).strip()
    return slug.replace("-", " ").title()


def enrich_book(b: dict, enrich_by_slug: dict) -> dict:
    slug = b.get("book_slug") or slugify(b.get("title") or "")
    e = enrich_by_slug.get(slug) or {}
    out = dict(b)
    out["book_slug"] = slug
    if e.get("author") is not None:
        out["author"] = e["author"]
    elif "author" not in out:
        out["author"] = None
    if e.get("authors"):
        out["authors"] = e["authors"]
    out["bucket"] = e.get("bucket") or out.get("bucket") or "mentioned"
    if e.get("url"):
        out["url"] = e["url"]
    elif "url" in out and not out["url"]:
        out.pop("url", None)
    if e.get("blurb"):
        out["blurb"] = e["blurb"]
    if e.get("authored_guest_slug"):
        out["authored_guest_slug"] = e["authored_guest_slug"]
    # For authored books that were already on shelf via guest mention, ensure authored_guest_slug
    if out["bucket"] == "authored" and not out.get("authored_guest_slug"):
        # prefer guest_slug from book if present
        if out.get("guest_slug"):
            out["authored_guest_slug"] = out["guest_slug"]
    return out


def build_library() -> tuple[list[dict], dict]:
    enrich = load_enrichment()
    by_slug = enrich.get("by_slug") or {}
    books = [enrich_book(b, by_slug) for b in load_base_books()]
    existing = {b["book_slug"] for b in books}

    for add in enrich.get("additional_authored") or []:
        slug = add.get("book_slug") or slugify(add["title"])
        if slug in existing:
            # merge: keep mentions from existing, take authored fields
            for b in books:
                if b["book_slug"] == slug:
                    b["bucket"] = "authored"
                    b["author"] = add.get("author") or b.get("author")
                    if add.get("authors"):
                        b["authors"] = add["authors"]
                    if add.get("url"):
                        b["url"] = add["url"]
                    b["authored_guest_slug"] = add.get("authored_guest_slug")
                    break
            continue
        row = {
            "title": add["title"],
            "book_slug": slug,
            "author": add.get("author"),
            "bucket": "authored",
            "authored_guest_slug": add.get("authored_guest_slug"),
            "mentions": list(add.get("mentions") or []),
            "mentioned_by": None,
            "guest_slug": add.get("authored_guest_slug"),
            "guest": guest_display_name(add["authored_guest_slug"]) if add.get("authored_guest_slug") else None,
            "episode_slug": None,
            "episode_number": None,
            "start": None,
            "start_seconds": None,
            "browse_title": None,
        }
        if add.get("authors"):
            row["authors"] = add["authors"]
        if add.get("url"):
            row["url"] = add["url"]
        # primary episode fields from first mention if any
        if row["mentions"]:
            m0 = row["mentions"][0]
            row["mentioned_by"] = m0.get("mentioned_by")
            row["guest_slug"] = m0.get("guest_slug") or row["guest_slug"]
            row["guest"] = m0.get("guest") or row["guest"]
            row["episode_slug"] = m0.get("episode_slug")
            row["episode_number"] = m0.get("episode_number")
            row["start"] = m0.get("start")
            row["start_seconds"] = m0.get("start_seconds")
            row["browse_title"] = m0.get("browse_title")
        books.append(row)
        existing.add(slug)

    books.sort(key=lambda b: (b.get("title") or "").lower())
    return books, enrich


def write_index_json(books: list[dict]) -> None:
    authored = sum(1 for b in books if b.get("bucket") == "authored")
    mentioned = sum(1 for b in books if b.get("bucket") != "authored")
    payload = {
        "title": "Books on Junkyard Love — authored and mentioned",
        "count": len(books),
        "authored_count": authored,
        "mentioned_count": mentioned,
        "schema_note": "bucket=authored|mentioned; author=actual book author; mentions=show appearances",
        "books": books,
    }
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    (SRC / "books_index.json").write_text(text, encoding="utf-8")
    (ASSETS / "books_index.json").write_text(text, encoding="utf-8")


def write_book_pages(books: list[dict]) -> None:
    books_dir = ROOT / "books"
    books_dir.mkdir(parents=True, exist_ok=True)
    for child in list(books_dir.iterdir()):
        if child.is_dir():
            for p in child.rglob("*"):
                if p.is_file():
                    p.unlink()
            for p in sorted(child.rglob("*"), reverse=True):
                if p.is_dir():
                    p.rmdir()
            child.rmdir()

    for b in books:
        slug = b["book_slug"]
        d = books_dir / slug
        d.mkdir(parents=True, exist_ok=True)
        title = b["title"]
        bucket = b.get("bucket") or "mentioned"
        author = b.get("author")
        label = "Authored by a Junkyard Love guest" if bucket == "authored" else "Mentioned on Junkyard Love"
        desc = f"{title}"
        if author:
            desc += f" by {author}"
        desc += f" — {label.lower()}. A research trail from real conversations, not a store."

        bits = [f"<h1>{esc_text(title)}</h1>"]
        meta = []
        if author:
            meta.append(f"Author: {esc_text(author)}")
        meta.append(f"Bucket: <strong>{esc_text(bucket)}</strong>")
        bits.append(f'<p class="note">{" · ".join(meta)}. No affiliate links.</p>')
        if bucket == "authored" and b.get("authored_guest_slug"):
            gslug = b["authored_guest_slug"]
            gname = guest_display_name(gslug)
            bits.append(
                f'<p>Guest author: <a href="guests/{esc(gslug)}/index.html">{esc_text(gname)}</a></p>'
            )
        if b.get("url"):
            bits.append(
                f'<p><a href="{esc(b["url"])}" target="_blank" rel="noopener">Book page / publisher link</a></p>'
            )
        if b.get("blurb"):
            bits.append(f"<p>{esc_text(b['blurb'])}</p>")

        mentions = b.get("mentions") or []
        if mentions:
            bits.append("<h2>On the show</h2>")
            bits.append('<ul class="list">')
            for m in mentions:
                who = esc_text(m.get("mentioned_by") or "mentioned")
                if m.get("guest_slug"):
                    who = f'<a href="guests/{esc(m["guest_slug"])}/index.html">{esc_text(m["mentioned_by"])}</a>'
                bits.append(f"<li>{who} · {ep_link(m)}</li>")
            bits.append("</ul>")
        else:
            bits.append(
                '<p class="note">No on-air mention recorded in the books index yet — listed because a guest authored it.</p>'
            )

        bits.append('<p class="note"><a href="books/index.html">All books</a></p>')
        html = (
            seo_head(f"{title} — Books — The Junkyard Love Podcast", desc, f"books/{slug}/")
            + "<body>\n<div class=\"wrap\">\n"
            + HEADER
            + "\n"
            + "\n".join(bits)
            + "\n"
            + FOOTER
            + "\n</div>\n"
            + SCRIPTS
            + "\n</body>\n</html>\n"
        )
        (d / "index.html").write_text(html, encoding="utf-8")


def write_books_index(books: list[dict]) -> None:
    authored = [b for b in books if b.get("bucket") == "authored"]
    mentioned = [b for b in books if b.get("bucket") != "authored"]

    def row(b: dict) -> str:
        author = b.get("author") or "author unknown"
        people = []
        seen = set()
        for m in b.get("mentions") or []:
            n = m.get("mentioned_by")
            if not n or n in seen:
                continue
            seen.add(n)
            if m.get("guest_slug"):
                people.append(f'<a href="guests/{esc(m["guest_slug"])}/index.html">{esc_text(n)}</a>')
            else:
                people.append(esc_text(n))
        show_bits = ""
        if people:
            show_bits = f'<span class="note"> — on show: {" · ".join(people)}</span>'
        elif b.get("bucket") == "authored" and b.get("authored_guest_slug"):
            g = guest_display_name(b["authored_guest_slug"])
            show_bits = (
                f'<span class="note"> — guest author: '
                f'<a href="guests/{esc(b["authored_guest_slug"])}/index.html">{esc_text(g)}</a></span>'
            )
        bucket_label = "authored" if b.get("bucket") == "authored" else "mentioned"
        return (
            '<li class="book-item">'
            f'<strong><a href="books/{esc(b["book_slug"])}/index.html">{esc_text(b["title"])}</a></strong>'
            f'<span class="note"> — {esc_text(author)} · <em>{bucket_label}</em></span>'
            f"{show_bits}"
            "</li>"
        )

    body = f"""<h1>Books</h1>
<p class="note">Honest library: books guests wrote, and books named on the show. No affiliate links. No invented titles.</p>
<p class="note">{len(authored)} authored · {len(mentioned)} mentioned · {len(books)} total</p>
<h2>Authored by guests</h2>
<p class="note">Guest wrote or co-wrote it (said on mic or verified elsewhere).</p>
<ul class="list book-list">
{''.join(row(b) for b in authored) or '<li class="note">(none yet)</li>'}
</ul>
<h2>Mentioned on the show</h2>
<p class="note">Named in conversation; someone else’s book (unless also listed above).</p>
<ul class="list book-list">
{''.join(row(b) for b in mentioned) or '<li class="note">(none yet)</li>'}
</ul>
"""
    desc = "Books guests authored or mentioned on Junkyard Love — a research trail, not a store."
    html = (
        seo_head("Books on Junkyard Love", desc, "books/")
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


def update_guest_pages(books: list[dict]) -> dict:
    """Replace Books on file / Books mentioned with Authored + Mentioned sections."""
    authored_by: dict[str, list] = {}
    mentioned_by: dict[str, list] = {}
    for b in books:
        if b.get("bucket") == "authored" and b.get("authored_guest_slug"):
            authored_by.setdefault(b["authored_guest_slug"], []).append(b)
        for m in b.get("mentions") or []:
            gs = m.get("guest_slug")
            if not gs:
                continue
            # if this guest authored it, don't also list under mentioned
            if b.get("bucket") == "authored" and b.get("authored_guest_slug") == gs:
                continue
            mentioned_by.setdefault(gs, []).append(b)

    # dedupe
    for d in (authored_by, mentioned_by):
        for gs, lst in list(d.items()):
            seen = set()
            uniq = []
            for b in lst:
                if b["book_slug"] in seen:
                    continue
                seen.add(b["book_slug"])
                uniq.append(b)
            d[gs] = uniq

    touched = {"authored": [], "mentioned": [], "cleared": []}
    guests_dir = ROOT / "guests"
    for d in guests_dir.iterdir():
        if not d.is_dir():
            continue
        path = d / "index.html"
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        # strip prior book sections
        text2 = re.sub(
            r"\n?<h2>(?:Books on file|Books mentioned|Authored books)</h2>.*?(?=\n<h2>|\n<footer class=\"site\">)",
            "\n",
            text,
            flags=re.S,
        )
        # may leave multiple; keep looping
        while True:
            text3 = re.sub(
                r"\n?<h2>(?:Books on file|Books mentioned|Authored books)</h2>.*?(?=\n<h2>|\n<footer class=\"site\">)",
                "\n",
                text2,
                count=1,
                flags=re.S,
            )
            if text3 == text2:
                break
            text2 = text3

        a_list = authored_by.get(d.name) or []
        m_list = mentioned_by.get(d.name) or []
        sections = []
        if a_list:
            lines = ['<h2>Authored books</h2>', '<ul class="list book-list">']
            for b in a_list:
                author = b.get("author") or ""
                extra = f' <span class="note">({esc_text(author)})</span>' if author else ""
                lines.append(
                    f'<li class="book-item"><a href="books/{esc(b["book_slug"])}/index.html">'
                    f'<strong>{esc_text(b["title"])}</strong></a>{extra}</li>'
                )
            lines.append("</ul>")
            sections.append("\n".join(lines))
            touched["authored"].append(d.name)
        if m_list:
            lines = ['<h2>Books mentioned</h2>', '<ul class="list book-list">']
            for b in m_list:
                author = b.get("author") or ""
                extra = f' <span class="note">— {esc_text(author)}</span>' if author else ""
                lines.append(
                    f'<li class="book-item"><a href="books/{esc(b["book_slug"])}/index.html">'
                    f'<strong>{esc_text(b["title"])}</strong></a>{extra}</li>'
                )
            lines.append("</ul>")
            sections.append("\n".join(lines))
            touched["mentioned"].append(d.name)
        if not a_list and not m_list:
            # leave no books section (or keep empty note only if previous existed)
            if text2 != text:
                touched["cleared"].append(d.name)
            path.write_text(text2, encoding="utf-8")
            continue

        block = "\n" + "\n".join(sections) + "\n"
        # insert before Watch / archive if present, else before footer
        if "<h2>Watch / archive</h2>" in text2:
            text2 = text2.replace("<h2>Watch / archive</h2>", block + "<h2>Watch / archive</h2>", 1)
        elif '<footer class="site">' in text2:
            text2 = text2.replace('<footer class="site">', block + '<footer class="site">', 1)
        path.write_text(text2, encoding="utf-8")
    return touched


def update_sitemap(books: list[dict]) -> None:
    path = ROOT / "sitemap.xml"
    text = path.read_text(encoding="utf-8")
    text = re.sub(
        r"\s*<url>\s*<loc>[^<]*/books/[^<]*</loc>\s*(?:<lastmod>[^<]*</lastmod>\s*)?</url>",
        "",
        text,
    )
    books_index_loc = f"{SITE_BASE}/books/"
    if books_index_loc not in text:
        # insert before </urlset>
        pass
    # rebuild book urls block
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    urls = [
        f"  <url>\n    <loc>{books_index_loc}</loc>\n    <lastmod>{today}</lastmod>\n  </url>"
    ]
    for b in books:
        loc = f"{SITE_BASE}/books/{b['book_slug']}/"
        urls.append(f"  <url>\n    <loc>{loc}</loc>\n    <lastmod>{today}</lastmod>\n  </url>")
    block = "\n".join(urls) + "\n"
    if "</urlset>" not in text:
        raise SystemExit("sitemap missing </urlset>")
    # ensure old books index removed already; append before close
    text = text.replace("</urlset>", block + "</urlset>")
    path.write_text(text, encoding="utf-8")


def update_llms(books: list[dict]) -> None:
    path = ROOT / "llms.txt"
    text = path.read_text(encoding="utf-8")
    authored = [b for b in books if b.get("bucket") == "authored"]
    mentioned = [b for b in books if b.get("bucket") != "authored"]
    lines = [
        "",
        "## Books",
        f"Honest library ({len(authored)} authored / {len(mentioned)} mentioned). No affiliate links.",
        f"- Index: {SITE_BASE}/books/",
        "",
        "### Authored by guests",
    ]
    for b in authored:
        author = b.get("author") or "?"
        lines.append(f"- [{b['title']}]({SITE_BASE}/books/{b['book_slug']}/) — {author}")
    lines.append("")
    lines.append("### Mentioned on the show")
    for b in mentioned:
        author = b.get("author") or "author unknown"
        lines.append(f"- [{b['title']}]({SITE_BASE}/books/{b['book_slug']}/) — {author}")
    lines.append("")
    section = "\n".join(lines)

    # replace existing ## Books section if present, else append before end
    if re.search(r"^## Books\b", text, re.M):
        text = re.sub(
            r"^## Books\b.*?(?=^## |\Z)",
            section.lstrip("\n") + "\n",
            text,
            count=1,
            flags=re.M | re.S,
        )
    else:
        # update the books_index.json blurb line if present
        text = text.replace(
            "`assets/books_index.json` — books mentioned on-air (guest_slug when known)",
            "`assets/books_index.json` — books library (authored + mentioned; author + bucket fields)",
        )
        text = text.rstrip() + "\n" + section + "\n"
    # also fix blurb if Books section replace path taken
    text = text.replace(
        "`assets/books_index.json` — books mentioned on-air (guest_slug when known)",
        "`assets/books_index.json` — books library (authored + mentioned; author + bucket fields)",
    )
    path.write_text(text, encoding="utf-8")


def guests_with_zero_books(books: list[dict]) -> list[str]:
    linked = set()
    for b in books:
        if b.get("authored_guest_slug"):
            linked.add(b["authored_guest_slug"])
        for m in b.get("mentions") or []:
            if m.get("guest_slug"):
                linked.add(m["guest_slug"])
    index = (ROOT / "guests" / "index.html").read_text(encoding="utf-8")
    all_slugs = re.findall(r'href="guests/([^/]+)/index\.html"', index)
    zero = [s for s in all_slugs if s not in linked]
    return zero


def write_report(books: list[dict], enrich: dict, touched: dict) -> None:
    authored = [b for b in books if b.get("bucket") == "authored"]
    mentioned = [b for b in books if b.get("bucket") != "authored"]
    zero = guests_with_zero_books(books)
    def pick(cands, slugs):
        by = {b["book_slug"]: b for b in cands}
        out = [by[s] for s in slugs if s in by]
        for b in cands:
            if b not in out:
                out.append(b)
            if len(out) >= 2:
                break
        return out[:2]
    a_ex = pick(authored, ["full-voice", "one-journey"])
    m_ex = pick(mentioned, ["atomic-habits", "the-symbolic-species"])
    lines = [
        "# SHIP_BOOKS — honest book library",
        "",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} (display for user as CT)",
        "",
        "## Counts",
        f"- Authored: **{len(authored)}**",
        f"- Mentioned: **{len(mentioned)}**",
        f"- Total: **{len(books)}**",
        "",
        "## Live URL stubs",
        f"- Books index: {SITE_BASE}/books/",
    ]
    for b in a_ex:
        lines.append(f"- Authored example: {SITE_BASE}/books/{b['book_slug']}/ — {b['title']}")
    for b in m_ex:
        lines.append(f"- Mentioned example: {SITE_BASE}/books/{b['book_slug']}/ — {b['title']}")
    lines += [
        "",
        "## Guests checked (writer-ish / notes + web)",
        ", ".join(enrich.get("guests_checked_writerish") or []) or "(none)",
        "",
        f"## Guests with zero books on file ({len(zero)}) — fine",
        ", ".join(zero),
        "",
        "## NEEDS JACOB (unverified — do not treat as catalog truth)",
    ]
    for item in enrich.get("needs_jacob") or []:
        lines.append(
            f"- **{item.get('item')}** ({item.get('guest')}) — UNVERIFIED — {item.get('note')}"
        )
    # also collect needs_jacob flags on books
    for b in books:
        slug = b["book_slug"]
        e = (enrich.get("by_slug") or {}).get(slug) or {}
        if e.get("needs_jacob"):
            lines.append(f"- **{b['title']}** — UNVERIFIED — {e['needs_jacob']}")
    lines += [
        "",
        "## Authored slugs",
        ", ".join(b["book_slug"] for b in authored),
        "",
        "## Guest page updates",
        f"- Authored sections: {len(touched.get('authored') or [])}",
        f"- Mentioned sections: {len(touched.get('mentioned') or [])}",
        f"- Cleared leftover book sections: {len(touched.get('cleared') or [])}",
        "",
        "## Notes",
        "- Prefer regenerable `_sources/build_books_library.py` + `_sources/books_library_enrichment.json`.",
        "- No git push from this ship.",
        "- Blurbs omitted unless grounded; none LLM-written this pass.",
        "",
    ]
    out = SRC / "reports" / "SHIP_BOOKS.md"
    out.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    books, enrich = build_library()
    write_index_json(books)
    write_book_pages(books)
    write_books_index(books)
    touched = update_guest_pages(books)
    update_sitemap(books)
    update_llms(books)
    write_report(books, enrich, touched)
    authored = sum(1 for b in books if b.get("bucket") == "authored")
    mentioned = sum(1 for b in books if b.get("bucket") != "authored")
    print(f"OK books={len(books)} authored={authored} mentioned={mentioned}")
    print(f"guest authored sections={len(touched['authored'])} mentioned={len(touched['mentioned'])}")
    print("Wrote _sources/reports/SHIP_BOOKS.md")


if __name__ == "__main__":
    main()
