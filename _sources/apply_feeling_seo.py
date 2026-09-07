#!/usr/bin/env python3
"""Feeling-level SEO: title/description/OG across key surfaces + episode meta from About.

No therapy/clinic claims. No invented episode summaries.
No git commit/push.
"""
from __future__ import annotations

import html as htmlmod
import json
import re
from pathlib import Path

ROOT = Path("/workspace/junkyard-love-archive-deploy")
SITE = "https://junkyardlovejakesbot.github.io/junkyard-love-archive"
REMOVED = {"0001", "0014", "0016", "0029"}

# path relative to site root (for og:url) → (title, description)
# Six topic doors used by six-ways-in get light feeling copy too.
PAGES = {
    "index.html": (
        "The Junkyard Love Podcast — long conversations worth keeping",
        "Long conversations when you can’t sleep. Real talks about healing, becoming, breath, and taking the armor off.",
        "",
    ),
    "six-ways-in/index.html": (
        "Six ways in — The Junkyard Love Podcast",
        "Six doors into the catalog when the full list feels like too much — same episodes, plain labels.",
        "six-ways-in/",
    ),
    "radio/index.html": None,  # already done
    "clips/index.html": (
        "Pick a clip — The Junkyard Love Podcast",
        "Pick a chapter from a real conversation and jump straight to it.",
        "clips/",
    ),
    "books/index.html": None,  # rebuilt with SEO
    "guests/index.html": (
        "Guests — The Junkyard Love Podcast",
        "People who sat down for long conversations on Junkyard Love.",
        "guests/",
    ),
    "topics/index.html": (
        "Topics — The Junkyard Love Podcast",
        "Browse the archive by what the conversations are actually about.",
        "topics/",
    ),
    "listen/index.html": (
        "Listen — The Junkyard Love Podcast",
        "Ways to listen to Junkyard Love — episodes, clips, and chapter radio.",
        "listen/",
    ),
    "search/index.html": (
        "Search — The Junkyard Love Podcast",
        "Search guests, topics, and words from real conversations.",
        "search/",
    ),
    "start-here/index.html": (
        "Start here — The Junkyard Love Podcast",
        "A soft place to begin when the full archive feels like a lot.",
        "start-here/",
    ),
    "donate/index.html": (
        "Donate — The Junkyard Love Podcast",
        "Support the archive if these conversations have meant something to you.",
        "donate/",
    ),
    "merch/index.html": (
        "Merch — The Junkyard Love Podcast",
        "Junkyard Love merch — drink some water, stretch, love yourselves.",
        "merch/",
    ),
}

MOOD_SEO = {
    "cant-sleep": (
        "Can’t sleep — Listen by mood",
        "Long conversations when you can’t sleep.",
    ),
    "tired-of-holding-it-together": (
        "Tired of holding it together — Listen by mood",
        "Talks for when you’re tired of holding it together.",
    ),
    "something-big-shifted": (
        "Something big shifted — Listen by mood",
        "Conversations for after something big shifted and you’re still catching up.",
    ),
    "need-to-come-back-to-my-body": (
        "Need to come back to my body — Listen by mood",
        "Breath, body, and coming back to yourself.",
    ),
    "having-a-really-hard-time": (
        "Having a really hard time — Listen by mood",
        "Company for a really hard time — no clinic-speak.",
    ),
    "just-want-a-real-conversation": (
        "Just want a real conversation — Listen by mood",
        "When you just want a real conversation.",
    ),
    "armors-on": (
        "Armor’s on — Listen by mood",
        "Talks for men taking the armor off.",
    ),
    "need-my-body-back": (
        "Need my body back — Listen by mood",
        "Conversations for getting back into your body.",
    ),
    "on-the-floor": (
        "On the floor — Listen by mood",
        "For nights when you’re on the floor and need a human voice.",
    ),
    "something-opened": (
        "Something opened — Listen by mood",
        "When something opened and you need someone who’s been there.",
    ),
    "want-a-friend-talking": (
        "Want a friend talking — Listen by mood",
        "When you want a friend talking in the room with you.",
    ),
}

TOPIC_FEELING = {
    "men-masculinity-fatherhood": (
        "Talks for men — Topics",
        "Talks for men taking the armor off — fatherhood, pressure, softness.",
    ),
    "healing-trauma-therapy": (
        "Getting through the hard thing — Topics",
        "Conversations about getting through the hard thing — trauma, pain, healing, without clinic-speak.",
    ),
    "awakening-mystical": (
        "When your life cracks open — Topics",
        "When your life cracks open — awakening stories, kundalini, visions, was that a breakdown?",
    ),
    "breath-body-practice": (
        "Breath, body, daily practice — Topics",
        "Breath, body, and daily practice — nervous system, yoga, voice, water, stretch.",
    ),
    "extreme-lives-second-chances": (
        "Starting over — Topics",
        "Starting over — prison, collapse, second chances.",
    ),
    "mind-mood-mental-health": (
        "Mind, mood, making sense — Topics",
        "Mind, mood, making sense — anxiety, depression, mania, intrusive thoughts, sense-making.",
    ),
    "love-sex-relationships": (
        "Love, sex & relationships — Topics",
        "Intimacy, partnership, belonging, and relationship practice — real conversations.",
    ),
    "music-creative-practice": (
        "Music & creative practice — Topics",
        "Music, voice, art, and making as a way of life.",
    ),
    "work-money-building": (
        "Work, money & building — Topics",
        "Work, money, and building something real.",
    ),
    "sobriety-substances": (
        "Sobriety & substances — Topics",
        "Sobriety, cannabis, plant medicine, and substance questions — honest talk.",
    ),
    "science-frequency-integral": (
        "Science, frequency & integral bridges — Topics",
        "Quantum talk, frequency, and bridges between science and spirit.",
    ),
    "host-solocasts": (
        "Host solocasts — Topics",
        "Solo episodes with Jacob — self-care, sobriety experiment, mood, masculinity, mystical practice.",
    ),
    "identity-becoming": (
        "Identity & becoming — Topics",
        "Transition, outgrown identities, and becoming who you are.",
    ),
}


def esc_attr(s: str) -> str:
    return htmlmod.escape(s or "", quote=True)


def strip_tags(s: str) -> str:
    s = re.sub(r"<[^>]+>", "", s or "")
    return htmlmod.unescape(s)
    # fallthrough


def truncate(s: str, n: int = 160) -> str:
    s = re.sub(r"\s+", " ", (s or "").strip())
    if len(s) <= n:
        return s
    cut = s[: n - 1]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut.rstrip(".,;:") + "…"


def upsert_seo(html: str, title: str, description: str, og_url: str) -> str:
    """Replace or insert title + meta description + basic OG tags in <head>."""
    # title
    if re.search(r"<title>.*?</title>", html, re.S):
        html = re.sub(r"<title>.*?</title>", f"<title>{esc_attr(title).replace('&quot;', '\"')}</title>", html, count=1, flags=re.S)
        # title should not use attr escape for quotes the same way — use text escape
        html = re.sub(
            r"<title>.*?</title>",
            f"<title>{htmlmod.escape(title, quote=False)}</title>",
            html,
            count=1,
            flags=re.S,
        )
    else:
        html = html.replace(
            '<meta charset="utf-8">',
            f'<meta charset="utf-8">\n<title>{htmlmod.escape(title, quote=False)}</title>',
            1,
        )

    desc_tag = f'<meta name="description" content="{esc_attr(description)}">'
    if re.search(r'<meta\s+name="description"\s+content="[^"]*"\s*/?>', html):
        html = re.sub(
            r'<meta\s+name="description"\s+content="[^"]*"\s*/?>',
            desc_tag,
            html,
            count=1,
        )
    else:
        html = re.sub(
            r"(</title>)",
            r"\1\n" + desc_tag,
            html,
            count=1,
        )

    og_block = "\n".join(
        [
            f'<meta property="og:title" content="{esc_attr(title)}">',
            f'<meta property="og:description" content="{esc_attr(description)}">',
            '<meta property="og:type" content="website">',
            f'<meta property="og:url" content="{esc_attr(og_url)}">',
        ]
    )
    # remove existing og tags we manage
    html = re.sub(r'\n?<meta\s+property="og:(?:title|description|type|url)"\s+content="[^"]*"\s*/?>', "", html)
    html = re.sub(
        r'(<meta\s+name="description"\s+content="[^"]*"\s*/?>)',
        r"\1\n" + og_block,
        html,
        count=1,
    )
    return html


def patch_file(rel: str, title: str, description: str, url_path: str) -> bool:
    path = ROOT / rel
    if not path.exists():
        return False
    html = path.read_text(encoding="utf-8")
    og_url = f"{SITE}/{url_path}" if url_path else f"{SITE}/"
    new = upsert_seo(html, title, description, og_url)
    if new != html:
        path.write_text(new, encoding="utf-8")
        return True
    return False


def about_first_para(html: str) -> str | None:
    m = re.search(r"<h2[^>]*>About</h2>\s*(.*?)(?=<h2\b)", html, re.S | re.I)
    if not m:
        return None
    block = m.group(1)
    pm = re.search(r"<p\b[^>]*>(.*?)</p>", block, re.S | re.I)
    if not pm:
        return None
    text = strip_tags(pm.group(1))
    text = re.sub(r"\s+", " ", text).strip()
    return text or None


def patch_episodes() -> tuple[int, int]:
    touched = 0
    kept_title = 0
    eps = ROOT / "episodes"
    for d in sorted(eps.iterdir()):
        if not d.is_dir():
            continue
        num = d.name.split("-")[0]
        if num in REMOVED:
            continue
        path = d / "index.html"
        if not path.exists():
            continue
        html = path.read_text(encoding="utf-8", errors="ignore")
        tm = re.search(r"<title>(.*?)</title>", html, re.S)
        title = strip_tags(tm.group(1)).strip() if tm else d.name
        kept_title += 1
        about = about_first_para(html)
        if not about:
            # fall back to existing description or short thesis-ish note
            dm = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', html)
            if dm and dm.group(1).strip():
                about = dm.group(1).strip()
            else:
                about = f"A Junkyard Love conversation — {title}"
        desc = truncate(about, 165)
        og_url = f"{SITE}/episodes/{d.name}/"
        new = upsert_seo(html, title, desc, og_url)
        # ensure dark theme if missing? don't change episode chrome beyond SEO
        if new != html:
            path.write_text(new, encoding="utf-8")
            touched += 1
    return touched, kept_title


def patch_guest_light() -> int:
    n = 0
    for d in sorted((ROOT / "guests").iterdir()):
        if not d.is_dir():
            continue
        path = d / "index.html"
        if not path.exists():
            continue
        html = path.read_text(encoding="utf-8", errors="ignore")
        hm = re.search(r"<h1>([^<]+)</h1>", html)
        name = htmlmod.unescape(hm.group(1)).strip() if hm else d.name
        title = f"{name} — The Junkyard Love Podcast"
        desc = f"Long conversations with {name} on Junkyard Love."
        # Rebecca distinction stays via correct name in H1
        new = upsert_seo(html, title, desc, f"{SITE}/guests/{d.name}/")
        if new != html:
            path.write_text(new, encoding="utf-8")
            n += 1
    return n


def ensure_robots() -> None:
    path = ROOT / "robots.txt"
    if path.exists() and "Sitemap:" in path.read_text(encoding="utf-8"):
        return
    path.write_text(
        "User-agent: *\nAllow: /\nSitemap: https://junkyardlovejakesbot.github.io/junkyard-love-archive/sitemap.xml\n",
        encoding="utf-8",
    )


def main() -> None:
    ensure_robots()
    touched = []
    for rel, meta in PAGES.items():
        if meta is None:
            continue
        title, desc, url_path = meta
        if patch_file(rel, title, desc, url_path):
            touched.append(rel)

    for slug, (title, desc) in MOOD_SEO.items():
        rel = f"moods/{slug}/index.html"
        if patch_file(rel, f"{title} — The Junkyard Love Podcast", desc, f"moods/{slug}/"):
            touched.append(rel)

    for slug, (title, desc) in TOPIC_FEELING.items():
        rel = f"topics/{slug}/index.html"
        if patch_file(rel, f"{title} — The Junkyard Love Podcast", desc, f"topics/{slug}/"):
            touched.append(rel)

    # book detail pages already have SEO from rebuild; refresh index if needed
    books_idx = ROOT / "books" / "index.html"
    if books_idx.exists() and 'name="description"' not in books_idx.read_text(encoding="utf-8"):
        patch_file(
            "books/index.html",
            "Books mentioned on Junkyard Love",
            "Books guests mentioned on Junkyard Love — a research trail through real conversations, not a store.",
            "books/",
        )
        touched.append("books/index.html")

    ep_n, ep_total = patch_episodes()
    guest_n = patch_guest_light()

    # radio already patched; confirm
    radio = (ROOT / "radio" / "index.html").read_text(encoding="utf-8")
    radio_ok = 'name="description"' in radio and "og:title" in radio

    report = {
        "pages_touched": touched,
        "episodes_meta_updated": ep_n,
        "episodes_total": ep_total,
        "guest_pages_seo": guest_n,
        "radio_seo_ok": radio_ok,
        "robots_ok": (ROOT / "robots.txt").exists(),
    }
    (ROOT / "_sources" / "reports" / "FEELING_SEO_STATS.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
