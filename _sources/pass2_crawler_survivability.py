#!/usr/bin/env python3
"""Pass 2: crawler survivability — canonicals, transcript.md links, listen RSS,
homepage/episode schema, sitemap lastmods, search noscript, llms crawl contract.

Does NOT invent quotes/books/guests. Does NOT rename folders. Does NOT convert hrefs.
Idempotent-ish: safe to re-run.
"""
from __future__ import annotations

import csv
import html as htmlmod
import json
import re
import subprocess
from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://junkyardlovejakesbot.github.io/junkyard-love-archive"
TODAY = date.today().isoformat()
RSS = "https://feeds.transistor.fm/the-junkyard-love-podcast"
YT_CH = "https://www.youtube.com/@TheJunkyardLovePodcast"
SPOTIFY = "https://open.spotify.com/show/45J7CBdM8j29doqyBp2bFs"
APPLE = "https://podcasts.apple.com/us/podcast/the-junkyard-love-podcast/id1489118788"
IG = "https://www.instagram.com/jacobfromtheinternet/"


def esc(s: str) -> str:
    return htmlmod.escape(s or "", quote=True)


def load_inventory() -> dict[str, dict]:
    path = ROOT / "inventory.csv"
    by_num: dict[str, dict] = {}
    with path.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            num = (row.get("episode_number") or "").strip().zfill(4)
            if num:
                by_num[num] = row
    return by_num


def git_date(rel: Path) -> str:
    try:
        r = subprocess.run(
            ["git", "log", "-1", "--format=%cs", "--", str(rel)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except OSError:
        pass
    return TODAY


def ensure_canonical(html: str, canonical: str) -> str:
    tag = f'<link rel="canonical" href="{esc(canonical)}">'
    if re.search(r'rel=["\']canonical["\']', html, re.I):
        return re.sub(
            r'<link\s+rel=["\']canonical["\'][^>]*>',
            tag,
            html,
            count=1,
            flags=re.I,
        )
    if re.search(r'<link rel="stylesheet"', html):
        return re.sub(
            r'(<link rel="stylesheet"[^>]*>)',
            r"\1\n" + tag,
            html,
            count=1,
        )
    return html.replace("</head>", tag + "\n</head>", 1)


def patch_homepage_jsonld(html: str) -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "PodcastSeries",
        "name": "The Junkyard Love Podcast",
        "description": "Long conversations for people who want honest talk about how we grow, heal, create, and understand ourselves. Full episodes, searchable transcripts, and clips.",
        "url": ORIGIN + "/",
        "webFeed": RSS,
        "sameAs": [YT_CH, SPOTIFY, APPLE, IG],
        "author": {
            "@type": "Person",
            "name": "Jacob Rhines",
            "alternateName": "JacobFromTheInternet",
        },
    }
    blob = json.dumps(data, ensure_ascii=False, indent=2)
    script = f'<script type="application/ld+json">\n{blob}\n</script>'
    if "application/ld+json" in html:
        return re.sub(
            r'<script type="application/ld\+json">\s*\{.*?\}\s*</script>',
            script,
            html,
            count=1,
            flags=re.S,
        )
    return html.replace("</head>", script + "\n</head>", 1)


def patch_episode_jsonld(html: str, slug: str, inv: dict | None) -> str:
    m = re.search(
        r'<script type="application/ld\+json">\s*(\{.*?\})\s*</script>',
        html,
        flags=re.S,
    )
    if not m:
        return html
    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError:
        return html
    if data.get("@type") != "PodcastEpisode":
        return html
    ep_url = ORIGIN + f"/episodes/{slug}/"
    data["url"] = ep_url
    series = data.get("partOfSeries") or {
        "@type": "PodcastSeries",
        "name": "The Junkyard Love Podcast",
    }
    series["@type"] = "PodcastSeries"
    series["url"] = ORIGIN + "/"
    series["webFeed"] = RSS
    data["partOfSeries"] = series

    same_as: list[str] = []
    media: list[dict] = []
    am = data.get("associatedMedia")
    if isinstance(am, dict):
        media.append(am)
    elif isinstance(am, list):
        media.extend([x for x in am if isinstance(x, dict)])

    yt = (inv or {}).get("youtube_url", "").strip() or None
    audio = (inv or {}).get("audio_enclosure_url", "").strip() or None
    share = (inv or {}).get("rss_episode_url", "").strip() or None
    if not yt:
        ym = re.search(r"https://www\.youtube\.com/watch\?v=[\w-]+", html)
        if ym:
            yt = ym.group(0)
    if not share:
        sm = re.search(r"https://share\.transistor\.fm/s/[\w-]+", html)
        if sm:
            share = sm.group(0)

    if yt:
        same_as.append(yt)
        if not any(x.get("@type") == "VideoObject" for x in media):
            media.append(
                {
                    "@type": "VideoObject",
                    "name": data.get("name"),
                    "contentUrl": yt,
                    "embedUrl": yt.replace("watch?v=", "embed/")
                    if "watch?v=" in yt
                    else yt,
                }
            )
    if share:
        same_as.append(share)
    if audio and not any(x.get("@type") == "AudioObject" for x in media):
        media.append({"@type": "AudioObject", "contentUrl": audio})
    if same_as:
        data["sameAs"] = list(dict.fromkeys(same_as))
    if media:
        data["associatedMedia"] = media if len(media) > 1 else media[0]

    data["transcript"] = {
        "@type": "CreativeWork",
        "url": ORIGIN + f"/episodes/{slug}/episode.md",
        "encodingFormat": "text/markdown",
    }

    blob = json.dumps(data, ensure_ascii=False, indent=2)
    script = f'<script type="application/ld+json">\n{blob}\n</script>'
    return html[: m.start()] + script + html[m.end() :]


def transcript_links_html(ep_dir: Path, slug: str) -> str:
    links = []
    if (ep_dir / "episode.md").exists():
        links.append(
            f'<a href="episodes/{esc(slug)}/episode.md">Transcript (markdown)</a>'
        )
    found = []
    for p in sorted(ep_dir.iterdir()):
        if p.is_file() and p.name.lower().endswith((".vtt", ".srt", ".json3")):
            found.append(p.name)
    capdir = ep_dir / "captions"
    if capdir.is_dir():
        for p in sorted(capdir.iterdir()):
            if p.is_file() and p.name.lower().endswith((".vtt", ".srt")):
                found.append(f"captions/{p.name}")
    preferred = [f for f in found if f.lower().endswith((".vtt", ".srt"))]
    use = preferred[:3] or [f for f in found if f.lower().endswith(".json3")][:1]
    for name in use:
        label = (
            "Captions"
            if name.lower().endswith((".vtt", ".srt"))
            else "Captions (json3)"
        )
        links.append(
            f'<a href="episodes/{esc(slug)}/{esc(name)}">{label} ({esc(Path(name).name)})</a>'
        )
    if not links:
        return ""
    return '<p class="note transcript-files">' + " · ".join(links) + "</p>"


def ensure_transcript_link(html: str, block: str) -> str:
    if not block:
        return html
    if "transcript-files" in html or "Transcript (markdown)" in html:
        html2, n = re.subn(
            r'<p class="note transcript-files">.*?</p>',
            block,
            html,
            count=1,
            flags=re.S,
        )
        if n:
            return html2
        return html
    if re.search(r"<h2>About</h2>", html):
        return re.sub(r"(<h2>About</h2>\s*)", r"\1" + block + "\n", html, count=1)
    if re.search(r"<h2>Full transcript</h2>", html):
        return re.sub(
            r"(<h2>Full transcript</h2>)", block + "\n" + r"\1", html, count=1
        )
    if re.search(r"<h2>Chapters</h2>", html):
        return re.sub(r"(<h2>Chapters</h2>)", block + "\n" + r"\1", html, count=1)
    if "</article>" in html:
        return html.replace("</article>", block + "\n</article>", 1)
    return html + block


def update_llms() -> None:
    path = ROOT / "llms.txt"
    text = path.read_text(encoding="utf-8")
    crawl = f"""## How to crawl this site

- Public origin: {ORIGIN}/ — all relative HTML hrefs resolve from `<base href="/junkyard-love-archive/">`, **not** from the current folder.
- Do **not** request `/topics/topics/...` or `/episodes/episodes/...` (those 404s mean the crawler ignored `<base>`).
- Do **not** invent slugs. Use [`sitemap.xml`]({ORIGIN}/sitemap.xml) or [`assets/episodes_index.json`]({ORIGIN}/assets/episodes_index.json).
- Early episodes use short slugs (example: `/episodes/0003-spencer-hicks/`). Later episodes use long title slugs (example: `/episodes/0124-sigmar-berg-conscious-breathing-break/`). `/episodes/0124-sigmar-berg/` is **not** a page.
- Removed catalog numbers **0001, 0014, 0016, 0029** are intentional placeholder pages, not missing episodes.
- Full transcripts live in each episode folder as `episode.md` and in the episode HTML. Deep links use `#t-HH-MM-SS`.
- Published quotes only: [`assets/quotes_clean.json`]({ORIGIN}/assets/quotes_clean.json) where `source=published`. Ignore Archive-picks / mined lines.
- Clip `short_summary` / `long_summary` are intentionally empty.
- Section indexes: `topics/`, `guests/`, `episodes/`, `books/`, `moods/`, `listen/`, `search/`, `clips/`, `radio/`, `start-here/`, `where-to-begin/`
- Machine files (absolute):
  - {ORIGIN}/sitemap.xml
  - {ORIGIN}/inventory.csv
  - {ORIGIN}/assets/episodes_index.json
  - {ORIGIN}/assets/chapter_index.json
  - {ORIGIN}/assets/clips_index.json
  - {ORIGIN}/assets/quotes_clean.json
  - {ORIGIN}/assets/books_index.json
- Official listen destinations: YouTube channel ({YT_CH}), Spotify show ({SPOTIFY}), Apple show ({APPLE}), RSS [{RSS}]({RSS})
- This archive is the **canonical public website** for the show. Linktree is not the catalog.

"""
    if "## How to crawl this site" in text:
        text = re.sub(
            r"## How to crawl this site\n.*?(?=\n## For bots)",
            crawl.rstrip() + "\n\n",
            text,
            count=1,
            flags=re.S,
        )
    else:
        text = re.sub(
            r"(Site: https://junkyardlovejakesbot\.github\.io/junkyard-love-archive/\n\n)",
            r"\1" + crawl,
            text,
            count=1,
        )
    head = text.split("## Episodes")[0]
    if "inventory.csv" not in head:
        text = text.replace(
            "- `llms.txt` — this file",
            f"- `inventory.csv` — episode catalog fields (youtube_url, audio_enclosure_url, rss_episode_url, …). Absolute: {ORIGIN}/inventory.csv\n"
            f"- Show RSS (audio catalog): {RSS}\n"
            "- `llms.txt` — this file",
            1,
        )
    path.write_text(text, encoding="utf-8")


def update_listen() -> None:
    p = ROOT / "listen" / "index.html"
    t = p.read_text(encoding="utf-8")
    if RSS not in t:
        t = t.replace(
            """    <a class="secondary" href="https://podcasts.apple.com/us/podcast/the-junkyard-love-podcast/id1489118788" target="_blank" rel="noopener">Apple Podcasts</a>
  </div>
</div>""",
            f"""    <a class="secondary" href="https://podcasts.apple.com/us/podcast/the-junkyard-love-podcast/id1489118788" target="_blank" rel="noopener">Apple Podcasts</a>
  </div>
  <p class="note" style="margin-top:1rem;">Show RSS: <a href="{RSS}">{RSS}</a></p>
  <p class="note">Episode pages link YouTube when we have a video; this RSS is the full audio catalog.</p>
  <p class="note">Archive catalog: <a href="episodes/index.html">/episodes/</a> — this site is the canonical website for the show.</p>
</div>""",
        )
    p.write_text(t, encoding="utf-8")


def update_search() -> None:
    p = ROOT / "search" / "index.html"
    t = p.read_text(encoding="utf-8")
    if "<noscript>" in t and "assets/chapter_index.json" in t:
        return
    note = f"""<p class="note">Searches stay on this site. If you are a bot or have JavaScript off: read transcripts on each episode page, or use <a href="llms.txt">llms.txt</a>, <a href="assets/chapter_index.json">assets/chapter_index.json</a>, and <a href="assets/episodes_index.json">assets/episodes_index.json</a>.</p>
<noscript>
<p class="note">JavaScript is off. Searches stay on this site when JS works. Meanwhile: read transcripts on each episode page, or use
<a href="{ORIGIN}/llms.txt">{ORIGIN}/llms.txt</a>,
<a href="{ORIGIN}/assets/chapter_index.json">{ORIGIN}/assets/chapter_index.json</a>,
<a href="{ORIGIN}/assets/episodes_index.json">{ORIGIN}/assets/episodes_index.json</a>.</p>
</noscript>
"""
    if 'id="search-results"' in t:
        t = t.replace('<div id="search-results">', note + '<div id="search-results">', 1)
    else:
        t = t.replace("</form>", "</form>\n" + note, 1)
    p.write_text(t, encoding="utf-8")


def update_readme() -> None:
    p = ROOT / "README.md"
    t = p.read_text(encoding="utf-8")
    blurb = f"""
## For indexers

- Crawl rules: [`llms.txt`]({ORIGIN}/llms.txt) (read **How to crawl this site** first)
- Sitemap: [`sitemap.xml`]({ORIGIN}/sitemap.xml)
- Inventory CSV: [`inventory.csv`]({ORIGIN}/inventory.csv)
- Show RSS (audio): {RSS}
- GitHub Pages publishes from the **repository root**. Relative links need `<base href="/junkyard-love-archive/">` — do not invent `/topics/topics/` or short episode slugs.

"""
    if "## For indexers" in t:
        t = re.sub(
            r"## For indexers\n.*?(?=\n## )",
            blurb.lstrip(),
            t,
            count=1,
            flags=re.S,
        )
    elif "## Episodes processed" in t:
        t = t.replace("## Episodes processed", blurb + "## Episodes processed", 1)
    else:
        t = t.rstrip() + "\n" + blurb
    p.write_text(t, encoding="utf-8")


def rebuild_sitemap(pages: list[tuple[str, str]]) -> None:
    required = [
        "/",
        "/moods/",
        "/listen/",
        "/search/",
        "/llms.txt",
        "/inventory.csv",
        "/assets/chapter_index.json",
        "/sitemap.xml",
    ]
    seen: set[str] = set()
    entries: list[tuple[str, str]] = []
    for path, lastmod in pages:
        if not path.startswith("/"):
            path = "/" + path
        if path in seen or "transistor.fm" in path:
            continue
        seen.add(path)
        entries.append((path, lastmod))
    for path in required:
        if path not in seen:
            entries.append((path, TODAY))
            seen.add(path)
    entries.sort(key=lambda x: (x[0] != "/", x[0]))
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for path, lastmod in entries:
        loc = ORIGIN + ("" if path == "/" else path)
        lines.append("  <url>")
        lines.append(f"    <loc>{xml_escape(loc)}</loc>")
        lines.append(f"    <lastmod>{lastmod}</lastmod>")
        lines.append("  </url>")
    lines.append("</urlset>")
    lines.append("")
    (ROOT / "sitemap.xml").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    inv_by_num = load_inventory()
    update_llms()
    update_listen()
    update_search()
    update_readme()

    sitemap_pages: list[tuple[str, str]] = []
    html_files = [p for p in ROOT.rglob("*.html") if ".git" not in p.parts]
    for p in sorted(html_files):
        rel = p.relative_to(ROOT).as_posix()
        if rel == "index.html":
            canon = ORIGIN + "/"
            sitemap_path = "/"
        elif rel.endswith("/index.html"):
            folder = rel[: -len("/index.html")]
            if folder == "six-ways-in":
                canon = ORIGIN + "/where-to-begin/"
            else:
                canon = ORIGIN + "/" + folder + "/"
            sitemap_path = "/" + folder + "/"
        else:
            canon = ORIGIN + "/" + rel
            sitemap_path = "/" + rel

        text = p.read_text(encoding="utf-8")
        text = ensure_canonical(text, canon)

        if rel == "index.html":
            text = patch_homepage_jsonld(text)

        m = re.match(r"episodes/([^/]+)/index\.html$", rel)
        if m:
            slug = m.group(1)
            if not slug.endswith("-removed"):
                num = slug.split("-")[0]
                inv = inv_by_num.get(num)
                text = patch_episode_jsonld(text, slug, inv)
                block = transcript_links_html(p.parent, slug)
                text = ensure_transcript_link(text, block)

        p.write_text(text, encoding="utf-8")
        sitemap_pages.append((sitemap_path, git_date(p)))

    for rel in (
        "llms.txt",
        "inventory.csv",
        "assets/chapter_index.json",
        "assets/episodes_index.json",
        "assets/clips_index.json",
        "assets/quotes_clean.json",
        "assets/books_index.json",
        "robots.txt",
    ):
        fp = ROOT / rel
        if fp.exists():
            sitemap_pages.append(("/" + rel, git_date(fp)))

    rebuild_sitemap(sitemap_pages)
    print(
        f"Pass 2 complete. HTML={len(html_files)} sitemap_paths={len(sitemap_pages)}"
    )


if __name__ == "__main__":
    main()
