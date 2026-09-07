#!/usr/bin/env python3
"""Generate BATGAP-inspired Topics browse for Junkyard Love Podcast archive.

Writes:
  - _sources/topics.json
  - topics/index.html
  - topics/<slug>/index.html
  - patches site-wide nav (Episodes|Guests|llms.txt → + Topics)
  - updates sitemap.xml with topic URLs

Run from deploy root or with DEPLOY_ROOT set.
Does NOT git commit or push.
"""
from __future__ import annotations

import csv
import html
import json
import re
from collections import defaultdict
from pathlib import Path

DEPLOY = Path(__file__).resolve().parents[1]
ARCHIVE = Path("/workspace/junkyard-love-archive")
CONTENT = DEPLOY / "_sources" / "content"
if not CONTENT.exists():
    CONTENT = ARCHIVE / "content"
INVENTORY = DEPLOY / "inventory.csv"
EPISODES_DIR = DEPLOY / "episodes"
TOPICS_DIR = DEPLOY / "topics"
SOURCES = DEPLOY / "_sources"
SITEMAP = DEPLOY / "sitemap.xml"
BASE_SITE = "https://junkyardlovejakesbot.github.io/junkyard-love-archive"

REMOVED = {"0001", "0014", "0016", "0029"}

CATEGORIES = [
    {
        "slug": "awakening-mystical",
        "title": "Awakening & Mystical Experience",
        "blurb": "Kundalini, mystical practice, spiritual emergency, and awakening stories.",
    },
    {
        "slug": "healing-trauma-therapy",
        "title": "Healing, Trauma & Therapy",
        "blurb": "Trauma work, therapy, chronic pain, and recovery of the self.",
    },
    {
        "slug": "breath-body-practice",
        "title": "Breath, Body & Daily Practice",
        "blurb": "Breath, yoga, fitness, and everyday care of the body.",
    },
    {
        "slug": "men-masculinity-fatherhood",
        "title": "Men, Masculinity & Fatherhood",
        "blurb": "Men’s emotional life, fatherhood, and outgrown masculine costumes.",
    },
    {
        "slug": "love-sex-relationships",
        "title": "Love, Sex & Relationships",
        "blurb": "Intimacy, partnership, belonging, and relationship practice.",
    },
    {
        "slug": "music-creative-practice",
        "title": "Music & Creative Practice",
        "blurb": "Music, voice, art, and making as a way of life.",
    },
    {
        "slug": "work-money-building",
        "title": "Work, Money & Building",
        "blurb": "Entrepreneurship, craft of work, money, and building something real.",
    },
    {
        "slug": "sobriety-substances",
        "title": "Sobriety & Substances",
        "blurb": "Sobriety, cannabis, plant medicine, and substance questions.",
    },
    {
        "slug": "mind-mood-mental-health",
        "title": "Mind, Mood & Mental Health",
        "blurb": "Depression, anxiety, mania, intrusive thoughts, and sense-making.",
    },
    {
        "slug": "science-frequency-integral",
        "title": "Science, Frequency & Integral Bridges",
        "blurb": "Quantum talk, frequency, and bridges between science and spirit.",
    },
    {
        "slug": "extreme-lives-second-chances",
        "title": "Extreme Lives / Second Chances",
        "blurb": "Prison, combat, near-death, and hard second acts.",
    },
    {
        "slug": "friends-origin-stories",
        "title": "Friends & Origin Stories (JYLP Roots)",
        "blurb": "Early peers, local friends, and the show’s origin circle.",
    },
    {
        "slug": "host-solocasts",
        "title": "Host Solocasts",
        "blurb": "Solo episodes with Jacob — self-care, sobriety experiment, mood, masculinity, mystical practice.",
    },
    {
        "slug": "identity-becoming",
        "title": "Identity & Becoming",
        "blurb": "Transition, outgrown identities, and becoming who you are.",
    },
]

# Exact host solocasts (primary set)
SOLOCASTS = {"0045", "0060", "0083", "0093", "0100"}

# Curated multi-label seeds (episode numbers). Prefer evidence over weak fits.
SEEDS: dict[str, set[str]] = {
    "awakening-mystical": {
        "0025", "0041", "0050", "0081", "0082", "0087", "0096", "0098", "0099",
        "0100", "0103", "0104", "0118", "0120",
    },
    "healing-trauma-therapy": {
        "0025", "0037", "0050", "0057", "0067", "0075", "0080", "0102", "0110",
        "0114", "0118", "0123",
    },
    "breath-body-practice": {
        "0011", "0017", "0023", "0026", "0038", "0044", "0045", "0051", "0060",
        "0061", "0079", "0082", "0124",
    },
    "men-masculinity-fatherhood": {
        "0034", "0090", "0093", "0111", "0121",
    },
    "love-sex-relationships": {
        "0036", "0058", "0072", "0073", "0078", "0080", "0086", "0087", "0107",
    },
    "music-creative-practice": {
        "0004", "0009", "0010", "0019", "0021", "0024", "0028", "0035", "0039",
        "0040", "0046", "0055", "0065", "0066", "0076", "0095", "0103", "0115",
        "0122",
    },
    "work-money-building": {
        "0002", "0006", "0012", "0022", "0031", "0032", "0051", "0064", "0070",
        "0071", "0089", "0091", "0094", "0095", "0105", "0106", "0109",
    },
    "sobriety-substances": {
        "0060", "0066", "0077", "0094", "0096", "0097", "0102", "0119",
    },
    "mind-mood-mental-health": {
        "0052", "0059", "0060", "0068", "0075", "0083", "0088", "0093", "0102",
        "0110", "0118",
    },
    "science-frequency-integral": {
        "0003", "0025", "0030", "0041", "0050", "0084", "0123", "0124",
    },
    "extreme-lives-second-chances": {
        "0085", "0097", "0102", "0109", "0118", "0119",
    },
    "friends-origin-stories": {
        "0002", "0003", "0004", "0005", "0006", "0007", "0008", "0009",
        "0010", "0011", "0012", "0013", "0015", "0017", "0018", "0019",
        "0020", "0021", "0022", "0023", "0024", "0025", "0026", "0027",
        "0028", "0031", "0032", "0033", "0036", "0038", "0039", "0042",
        "0044", "0048", "0049", "0053", "0056", "0059", "0062", "0070",
        "0074", "0088", "0034", "0111", "0112",
    },
    "host-solocasts": set(SOLOCASTS),
    "identity-becoming": {
        "0034", "0043", "0046", "0049", "0054", "0067", "0069", "0071", "0086",
        "0090", "0093", "0108", "0111", "0113",
    },
}

# Keyword# Keyword patterns scored against title + about + guest (lowercase).
# Thresholds keep weak transcript noise out.
# Specific patterns only. Keyword expansion requires min_hits distinct matches
# (see KEYWORD_MIN_HITS) so casual About mentions do not inflate lists.
KEYWORD_RULES: list[tuple[str, list[str]]] = [
    ("awakening-mystical", [
        r"kundalini", r"mystical experience", r"ayahuasca",
        r"spiritual emergency", r"\bswami\b", r"starseed", r"lucid dream",
        r"witness state", r"path to no path", r"awakening from the lucid",
        r"a kundalini awakening", r"grand-?mother ayahuasca",
        r"be still, as the universe", r"spiritual practice to radically",
    ]),
    ("healing-trauma-therapy", [
        r"\btrauma\b", r"psychotherap", r"hypnotherap", r"chronic pain",
        r"healing the soul", r"soul coach", r"ketamine to heal", r"\breiki\b",
        r"intuitive healer", r"inner power", r"habit change and happiness",
    ]),
    ("breath-body-practice", [
        r"conscious breathing", r"528\s*hz", r"powerlift", r"operating optimally",
        r"maintain health", r"sober october", r"pickleball", r"yoga & meditation",
        r"yogi & meditation", r"nervous system", r"gallon of water",
        r"mental and physical tips", r"finding the feel",
    ]),
    ("men-masculinity-fatherhood", [
        r"toxic masculin", r"healing toxic", r"being boys",
        r"becoming men", r"costumes of sadness", r"male vulnerability",
        r"masculine drive", r"-father$", r" nate tanzman - father",
        r"\bfather\b",  # only used on title_blob (see classify)
    ]),
    ("love-sex-relationships", [
        r"\borgasm", r"relationship-?blueprints", r"\bmarriage\b", r"path of love",
        r"love coach", r"innate desire for belonging", r"sex, pleasure",
        r"conflict resolution coach", r"relationship practitioner",
    ]),
    ("music-creative-practice", [
        r"\brapper\b", r"hip-?hop", r"disc jockey", r"\bdj\b", r"\brosetan\b",
        r"songwrit", r"dead crown", r"open mic", r"\bpuppet", r"free your real voice",
        r"writin.? songs", r"singer/songwriter", r"wyld productions",
        r"behind the lens", r"producing music",
    ]),
    ("work-money-building", [
        r"\bceo\b", r"billionaire", r"eye clothing", r"betting on yourself",
        r"college admissions", r"operations manager", r"family business",
        r"social impact investor", r"building a real foundation", r"vail denim",
        r"cleaning the floors",
    ]),
    ("sobriety-substances", [
        r"\bsobriety\b", r"sober october", r"conversation about weed", r"\bcannabis\b",
        r"ayahuasca", r"ketamine", r"lentin.? booze", r"\boverdose\b",
        r"acid, intellect", r"psychedelic therapy",
    ]),
    ("mind-mood-mental-health", [
        r"\bbipolar\b", r"mania is a message", r"intrusive thoughts",
        r"sense.?making sickness", r"mental review", r"chest pressure",
        r"costumes of sadness", r"depression & anxiety", r"depression and anxiety",
        r"ketamine to heal anxiety", r"making sense of my depression",
    ]),
    ("science-frequency-integral", [
        r"\bquantum\b", r"528\s*hz", r"\bschumann\b", r"biosemiot",
        r"mathematics, science", r"four bodies", r"neural net", r"science researcher",
    ]),
    ("extreme-lives-second-chances", [
        r"\bprison\b", r"navy seal", r"combat veteran", r"\boverdose\b",
        r"trafficking humans", r"fighting for sobriety", r"shot at 19",
        r"betteru",
    ]),
    ("identity-becoming", [
        r"outgrown identities", r"later bloom", r"transition mentor",
        r"redefining your life", r"killing the ego", r"trimming off what no longer",
        r"ever evolving chameleon", r"always evolution occurs",
        r"forward is the only way", r"being boys, becoming men",
    ]),
]

KEYWORD_MIN_HITS = 1  # patterns are already specific; 1 strong hit is enough


def load_inventory() -> dict[str, dict]:
    rows = {}
    with INVENTORY.open(newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            num = r["episode_number"].zfill(4)
            if num in REMOVED:
                continue
            rows[num] = r
    return rows


def episode_dirs() -> dict[str, str]:
    """Map episode number -> folder slug (prefer numbered dirs)."""
    mapping = {}
    for p in EPISODES_DIR.iterdir():
        if not p.is_dir():
            continue
        if p.name.endswith("-removed"):
            continue
        m = re.match(r"^(\d{4})-", p.name)
        if m:
            mapping[m.group(1)] = p.name
    return mapping


def read_about(slug: str) -> str:
    for base in (CONTENT, ARCHIVE / "content"):
        p = base / slug / "source-about.md"
        if p.exists():
            return p.read_text(encoding="utf-8", errors="replace")
        p2 = base / slug / "episode.md"
        if p2.exists():
            return p2.read_text(encoding="utf-8", errors="replace")
    # fallback: scrape about from HTML
    html_path = EPISODES_DIR / slug / "index.html"
    if html_path.exists():
        t = html_path.read_text(encoding="utf-8", errors="replace")
        m = re.search(r'<div class="about">(.*?)</div>', t, re.S)
        if m:
            return re.sub(r"<[^>]+>", " ", m.group(1))
    return ""



def read_episode_title(slug: str, fallback: str = "") -> str:
    """Prefer full H1 from episode page when inventory title is truncated."""
    html_path = EPISODES_DIR / slug / "index.html"
    if html_path.exists():
        raw = html_path.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"<h1>(.*?)</h1>", raw, re.S)
        if m:
            title = re.sub(r"<[^>]+>", "", m.group(1))
            title = html.unescape(title)
            title = re.sub(r"\s+", " ", title).strip()
            if title:
                return title
    if fallback and not fallback.rstrip().endswith("..."):
        return fallback
    # last resort: humanize slug without number
    return fallback or slug


def score_keywords(text: str) -> dict[str, float]:
    scores: dict[str, float] = defaultdict(float)
    for slug, patterns in KEYWORD_RULES:
        hits = 0
        for pat in patterns:
            if re.search(pat, text, re.I):
                hits += 1
        if hits >= KEYWORD_MIN_HITS:
            scores[slug] += float(hits)
    return scores


def classify(inv: dict[str, dict], dirs: dict[str, str]) -> dict[str, list[dict]]:
    """Return topics.json structure: slug -> list of {slug, title, number}."""
    assignments: dict[str, set[str]] = {c["slug"]: set() for c in CATEGORIES}

    # Apply seeds
    for topic, nums in SEEDS.items():
        for n in nums:
            if n in dirs and n not in REMOVED:
                assignments[topic].add(n)

    # Keyword expansion from title + guest + slug only (About is too chatty).
    for num, slug in dirs.items():
        if num in REMOVED:
            continue
        r = inv.get(num, {})
        title_blob = " ".join([
            r.get("exact_public_title") or "",
            r.get("guest_name") or "",
            slug.replace("-", " "),
        ]).lower()
        scores = score_keywords(title_blob)
        for topic, sc in scores.items():
            if topic in ("friends-origin-stories", "host-solocasts"):
                continue  # curated only
            if sc >= KEYWORD_MIN_HITS:
                assignments[topic].add(num)

    # Ensure solocasts exact set only (may also appear elsewhere)
    assignments["host-solocasts"] = set(SOLOCASTS) & set(dirs)

    # Coverage pass: every published ep in ≥1 topic
    covered = set()
    for nums in assignments.values():
        covered |= nums
    uncovered = [n for n in sorted(dirs) if n not in covered and n not in REMOVED]
    for num in uncovered:
        slug = dirs[num]
        r = inv.get(num, {})
        title_blob = " ".join([
            r.get("exact_public_title") or "",
            r.get("guest_name") or "",
            slug.replace("-", " "),
        ]).lower()
        scores = score_keywords(title_blob)
        scores.pop("friends-origin-stories", None)
        scores.pop("host-solocasts", None)
        if scores:
            best = max(scores.items(), key=lambda x: x[1])[0]
            assignments[best].add(num)
            continue
        # Soft heuristics from title words for remaining gaps
        t = title_blob
        if any(k in t for k in ("music", "rapper", "dj ", "song", "band", "voice", "puppet")):
            assignments["music-creative-practice"].add(num)
        elif any(k in t for k in ("heal", "therap", "trauma", "pain", "reiki")):
            assignments["healing-trauma-therapy"].add(num)
        elif any(k in t for k in ("business", "ceo", "founder", "money", "entrepreneur", "ops", "clothing")):
            assignments["work-money-building"].add(num)
        elif int(num) <= 55:
            assignments["friends-origin-stories"].add(num)
        else:
            assignments["identity-becoming"].add(num)

    # Build ordered episode lists (newest first)
    out: dict[str, list[dict]] = {}
    for cat in CATEGORIES:
        items = []
        for num in sorted(assignments[cat["slug"]], reverse=True):
            slug = dirs[num]
            r = inv.get(num, {})
            inv_title = r.get("exact_public_title") or ""
            items.append({
                "number": num,
                "slug": slug,
                "title": read_episode_title(slug, inv_title),
                "guest": r.get("guest_name") or "",
                "date": r.get("publish_date") or "",
                "duration": r.get("duration") or "",
            })
        out[cat["slug"]] = items
    return out


NAV_OLD = """  <nav>
    <a href="episodes/index.html">Episodes</a>
    <a href="guests/index.html">Guests</a>
    <a href="llms.txt">llms.txt</a>
  </nav>"""

NAV_NEW = """  <nav>
    <a href="episodes/index.html">Episodes</a>
    <a href="guests/index.html">Guests</a>
    <a href="topics/index.html">Topics</a>
    <a href="llms.txt">llms.txt</a>
  </nav>"""

# Already-patched variant (idempotent)
NAV_ALREADY = 'href="topics/index.html">Topics</a>'


def patch_nav() -> int:
    count = 0
    for path in DEPLOY.rglob("*.html"):
        text = path.read_text(encoding="utf-8", errors="replace")
        if NAV_ALREADY in text:
            continue
        if NAV_OLD not in text:
            # try flexible whitespace
            m = re.search(
                r"<nav>\s*<a href=\"episodes/index\.html\">Episodes</a>\s*"
                r"<a href=\"guests/index\.html\">Guests</a>\s*"
                r"<a href=\"llms\.txt\">llms\.txt</a>\s*</nav>",
                text,
            )
            if not m:
                continue
            text = text[: m.start()] + NAV_NEW + text[m.end() :]
        else:
            text = text.replace(NAV_OLD, NAV_NEW, 1)
        path.write_text(text, encoding="utf-8")
        count += 1
    return count


def esc(s: str) -> str:
    return html.escape(s or "", quote=True)


def page_shell(title: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<base href="/junkyard-love-archive/">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<div class="wrap">
<header class="site">
  <a class="brand" href="index.html">The Junkyard Love Podcast</a>
{NAV_NEW}
</header>
{body}
</div>
</body>
</html>
"""


def format_meta(ep: dict) -> str:
    parts = []
    if ep.get("date"):
        parts.append(ep["date"])
    guest = (ep.get("guest") or "").strip()
    if guest and not re.search(r"solo", guest, re.I):
        parts.append(guest)
    elif guest:
        parts.append(guest)
    if ep.get("duration"):
        parts.append(ep["duration"])
    return " · ".join(parts)


def write_topic_pages(topics: dict[str, list[dict]]) -> None:
    TOPICS_DIR.mkdir(parents=True, exist_ok=True)

    # Index
    items_html = []
    for cat in CATEGORIES:
        n = len(topics[cat["slug"]])
        items_html.append(
            f'  <li><a href="topics/{cat["slug"]}/index.html">{esc(cat["title"])}</a>'
            f' <span class="note">({n})</span><br>'
            f'<span class="note">{esc(cat["blurb"])}</span></li>'
        )
    body = (
        "<h1>Topics</h1>\n"
        '<p class="note">Browse published episodes by theme. Episodes can appear in more than one topic.</p>\n'
        '<ul class="list">\n' + "\n".join(items_html) + "\n</ul>\n"
        '<p class="note"><a href="episodes/index.html">All episodes</a> · '
        '<a href="guests/index.html">Guests</a> · <a href="index.html">Home</a></p>\n'
    )
    (TOPICS_DIR / "index.html").write_text(
        page_shell("Topics — The Junkyard Love Podcast", body), encoding="utf-8"
    )

    for cat in CATEGORIES:
        slug = cat["slug"]
        tdir = TOPICS_DIR / slug
        tdir.mkdir(parents=True, exist_ok=True)
        eps = topics[slug]
        lis = []
        for ep in eps:
            meta = format_meta(ep)
            lis.append(
                f'  <li><a href="episodes/{esc(ep["slug"])}/index.html">{esc(ep["title"])}</a>'
                f'<br><span class="note">{esc(meta)}</span></li>'
            )
        body = (
            f'<p class="note"><a href="topics/index.html">← Topics</a></p>\n'
            f'<h1>{esc(cat["title"])}</h1>\n'
            f'<p class="note">{esc(cat["blurb"])} · {len(eps)} episode{"s" if len(eps)!=1 else ""}</p>\n'
            '<ul class="list">\n' + ("\n".join(lis) if lis else "  <li class=\"note\">No episodes yet.</li>") + "\n</ul>\n"
        )
        (tdir / "index.html").write_text(
            page_shell(f'{cat["title"]} — Topics — The Junkyard Love Podcast', body),
            encoding="utf-8",
        )


def write_topics_json(topics: dict[str, list[dict]]) -> Path:
    # Compact mapping: slug -> list of episode slugs (+ titles)
    payload = {
        "categories": [
            {
                "slug": c["slug"],
                "title": c["title"],
                "blurb": c["blurb"],
                "episodes": [
                    {"slug": e["slug"], "number": e["number"], "title": e["title"]}
                    for e in topics[c["slug"]]
                ],
            }
            for c in CATEGORIES
        ]
    }
    path = SOURCES / "topics.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def update_sitemap() -> None:
    text = SITEMAP.read_text(encoding="utf-8")
    # Remove prior topic urls if regenerating
    text = re.sub(
        r"\s*<url><loc>" + re.escape(BASE_SITE) + r"/topics/[^<]*</loc></url>",
        "",
        text,
    )
    urls = [f"  <url><loc>{BASE_SITE}/topics/</loc></url>"]
    for cat in CATEGORIES:
        urls.append(f"  <url><loc>{BASE_SITE}/topics/{cat['slug']}/</loc></url>")
    block = "\n".join(urls)
    # Insert after guests url if present, else after opening urlset
    if f"{BASE_SITE}/guests/</loc>" in text:
        text = text.replace(
            f"  <url><loc>{BASE_SITE}/guests/</loc></url>",
            f"  <url><loc>{BASE_SITE}/guests/</loc></url>\n{block}",
            1,
        )
    else:
        text = text.replace(
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + block,
            1,
        )
    SITEMAP.write_text(text, encoding="utf-8")


def update_readme() -> None:
    for readme in (DEPLOY / "README.md", ARCHIVE / "README.md"):
        if not readme.exists():
            continue
        text = readme.read_text(encoding="utf-8")
        note = (
            "## Topics browse\n\n"
            "Static theme index under `topics/` (BATGAP-inspired). "
            "Mapping lives in `_sources/topics.json`; regenerate with "
            "`_sources/build_topics.py`. Episodes may appear in multiple topics; "
            "`*-removed` placeholders are excluded.\n"
        )
        if "## Topics browse" in text:
            text = re.sub(
                r"## Topics browse\n\n.*?(?=\n## |\Z)",
                note + "\n",
                text,
                count=1,
                flags=re.S,
            )
        else:
            text = text.rstrip() + "\n\n" + note
        readme.write_text(text, encoding="utf-8")


def mirror_to_archive(topics_json: Path) -> None:
    dest_sources = ARCHIVE / "_sources"
    dest_sources.mkdir(parents=True, exist_ok=True)
    (dest_sources / "topics.json").write_text(topics_json.read_text(encoding="utf-8"), encoding="utf-8")
    (dest_sources / "build_topics.py").write_text(
        (SOURCES / "build_topics.py").read_text(encoding="utf-8"), encoding="utf-8"
    )


def main() -> None:
    inv = load_inventory()
    dirs = episode_dirs()
    # Prefer inventory intersection
    dirs = {n: s for n, s in dirs.items() if n in inv or n not in REMOVED}
    # Keep only published numbered dirs present on disk & not removed
    dirs = {n: s for n, s in dirs.items() if n not in REMOVED and (EPISODES_DIR / s).is_dir()}

    topics = classify(inv, dirs)
    topics_json = write_topics_json(topics)
    write_topic_pages(topics)
    nav_count = patch_nav()
    update_sitemap()
    update_readme()
    mirror_to_archive(topics_json)

    # Report
    all_eps = set(dirs)
    covered = set()
    for items in topics.values():
        for e in items:
            covered.add(e["number"])
    uncovered = sorted(all_eps - covered)

    print("DEPLOY", DEPLOY)
    print("published_episodes", len(all_eps))
    print("topics_json", topics_json)
    print("topics_index", TOPICS_DIR / "index.html")
    for cat in CATEGORIES:
        print(f"count\t{cat['slug']}\t{len(topics[cat['slug']])}")
    print("nav_patched", nav_count)
    print("uncategorized", uncovered if uncovered else "none")
    print("git_commit_push", "skipped (by design)")


if __name__ == "__main__":
    main()
