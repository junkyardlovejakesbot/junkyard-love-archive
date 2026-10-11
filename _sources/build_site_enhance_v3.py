#!/usr/bin/env python3
"""Site enhancement v3 (idempotent): plain mood labels + door paragraphs,
homepage 'Start with a clip' hero, topics/keyword cloud below the fold.
Run after build_mood_radio.py / homepage builders, then pass2_crawler_survivability.py."""
import html, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "_sources"

NEW_LABELS = {
    "cant-sleep": "Can't sleep",
    "tired-of-holding-it-together": "Feeling overwhelmed",
    "something-big-shifted": "Life just changed",
    "need-to-come-back-to-my-body": "Not in my body",
    "having-a-really-hard-time": "Having a hard time",
    "just-want-a-real-conversation": "Want a real conversation",
    "armors-on": "Feeling guarded",
    "need-my-body-back": "Body feels off",
    "on-the-floor": "At a low point",
    "something-opened": "Something made sense",
    "want-a-friend-talking": "Need company",
}
OLD_LABELS = {
    "cant-sleep": ["Can't sleep", "Can’t sleep"],
    "tired-of-holding-it-together": ["Tired of holding it together"],
    "something-big-shifted": ["Something big shifted"],
    "need-to-come-back-to-my-body": ["Need to come back to my body"],
    "having-a-really-hard-time": ["Having a really hard time"],
    "just-want-a-real-conversation": ["Just want a real conversation"],
    "armors-on": ["Armor's on", "Armor’s on", "Armor&#39;s on"],
    "need-my-body-back": ["Need my body back"],
    "on-the-floor": ["On the floor"],
    "something-opened": ["Something opened"],
    "want-a-friend-talking": ["Want a friend talking"],
}

# Start clip: real chapter from assets/clips_index.json (published clock).
START_CLIP = {"episode_number": "0125", "title": "Why don't you hate men?", "start_seconds": 370}  # published chapter 6:10

e = lambda s: html.escape(str(s), quote=True)


def fmt_human(sec):
    h, r = divmod(int(sec), 3600); m, s = divmod(r, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def fmt_hash(sec):
    h, r = divmod(int(sec), 3600); m, s = divmod(r, 60)
    return f"#t-{h:02d}-{m:02d}-{s:02d}"


def clip_card_embed_html(c, card_id="start-clip"):
    """Same markup as archive.js clipFromIndexCard(c, {embed:true})."""
    sec = int(c["start_seconds"])
    ep_url = f"episodes/{c['episode_slug']}/index.html"
    guest = c.get("guest") or "Solo"
    out = f'<div class="clip-card clip-card-embed" id="{card_id}">'
    out += f"<h3>{e(c['title'])}</h3>"
    out += f'<p class="clip-ep">{e(guest)} · Episode {e(c["episode_number"])} · starts {fmt_human(sec)}</p>'
    if c.get("youtube_id"):
        yid = c["youtube_id"]
        out += ('<div class="clip-embed"><iframe src="https://www.youtube-nocookie.com/embed/'
                f'{e(yid)}?start={sec}&amp;rel=0" title="{e(c["title"])} — {e(guest)}" '
                'loading="lazy" frameborder="0" allow="encrypted-media; picture-in-picture" '
                'allowfullscreen></iframe></div>')
    else:
        out += '<p class="note">No video is available for this one. Use the episode page below.</p>'
    out += '<div class="btn-row">'
    if c.get("youtube_id"):
        out += (f'<a class="secondary" href="https://www.youtube.com/watch?v={e(c["youtube_id"])}&amp;t={sec}s" '
                'target="_blank" rel="noopener">YouTube</a>')
    out += f'<a class="secondary" href="{ep_url}{fmt_hash(sec)}">Transcript at this moment</a>'
    out += f'<a class="secondary" href="{ep_url}">Full episode</a>'
    out += "</div></div>"
    return out


def update_mood_json():
    for p in (SRC / "mood_doors.json", ROOT / "assets" / "mood_doors.json"):
        d = json.loads(p.read_text(encoding="utf-8"))
        for door in d["doors"]:
            if door["slug"] in NEW_LABELS:
                door["label"] = NEW_LABELS[door["slug"]]
        p.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def door_paragraph(titles):
    titles = [t for t in titles if t][:3]
    if not titles:
        return ""
    if len(titles) == 1:
        joined = titles[0]
    else:
        joined = ", ".join(titles[:-1]) + (", and " if len(titles) > 2 else " and ") + titles[-1]
    return f"Chapters here include {joined}."


def patch_mood_pages():
    report = {}
    for slug, label in NEW_LABELS.items():
        p = ROOT / "moods" / slug / "index.html"
        if not p.exists():
            report[slug] = "MISSING"; continue
        t = p.read_text(encoding="utf-8")
        for old in OLD_LABELS[slug]:
            for variant in (old, e(old)):
                t = t.replace(f"<title>{variant} — ", f"<title>{e(label)} — ")
                t = t.replace(f'content="{variant} — ', f'content="{e(label)} — ')
        t = re.sub(r"<h1>.*?</h1>", f"<h1>{e(label)}</h1>", t, count=1, flags=re.S)
        t = re.sub(r'\s*<p class="door-for">.*?</p>', "", t, flags=re.S)
        if 'http-equiv="refresh"' in t:
            report[slug] = "redirect page (no chapters listed; label only)"
        else:
            titles = [html.unescape(x) for x in re.findall(r'<div class="clip-card"><h3>(.*?)</h3>', t)]
            para = door_paragraph(titles)
            words = len(para.split())
            assert words <= 40, (slug, words)
            if para:
                t = t.replace(f"<h1>{e(label)}</h1>", f'<h1>{e(label)}</h1>\n<p class="door-for">{e(para)}</p>', 1)
            report[slug] = f"ok ({words} words)"
        p.write_text(t, encoding="utf-8")
    # moods index
    p = ROOT / "moods" / "index.html"
    t = p.read_text(encoding="utf-8")
    for slug, label in NEW_LABELS.items():
        t = re.sub(rf'(href="moods/{slug}/index.html"><h3>).*?(</h3>)', rf"\g<1>{e(label)}\g<2>", t)
    p.write_text(t, encoding="utf-8")
    return report


def patch_homepage():
    p = ROOT / "index.html"
    t = p.read_text(encoding="utf-8")
    for slug, label in NEW_LABELS.items():
        t = re.sub(rf'(data-mood="{slug}">).*?(</a>)', rf"\g<1>{e(label)}\g<2>", t)
    clips = json.loads((ROOT / "assets" / "clips_index.json").read_text(encoding="utf-8"))["clips"]
    c = dict(next(x for x in clips if x["episode_number"] == START_CLIP["episode_number"]
             and x["title"] == START_CLIP["title"]))
    c["start_seconds"] = START_CLIP["start_seconds"]
    c["start"] = "00:06:10"
    hero = (
        '<!-- hero-v3:start -->\n<section class="home-hero" id="start">\n'
        '<p class="hero-line">Mining the hearts and minds of unorthodox teachers.</p>\n'
        '<p class="hero-sub">Long conversations with people who learned something the hard way.</p>\n'
        '<h2>Start with a clip</h2>\n'
        + clip_card_embed_html(c) + "\n"
        '<nav class="hero-doors" aria-label="Ways in">\n'
        '  <a class="btn" href="clips/index.html" data-shuffle-clip data-shuffle-target="#start-clip">Shuffle another clip</a>\n'
        '  <a class="btn secondary" href="moods/index.html">Listen by mood</a>\n'
        '  <a class="btn secondary" href="#latest">Latest episodes</a>\n'
        '</nav>\n</section>\n<!-- hero-v3:end -->\n'
    )
    t = re.sub(r"<!-- hero-v3:start -->.*?<!-- hero-v3:end -->\n", "", t, flags=re.S)
    t = t.replace("</header>\n", "</header>\n" + hero, 1)
    # Move Topics grid and Pick a clip (keyword cloud) below Latest
    below = re.compile(r'<!-- below-fold-v3:start -->.*?<!-- below-fold-v3:end -->\n', re.S)
    m = below.search(t)
    if m:
        block = m.group(0); t = t.replace(block, "")
    else:
        topics = re.search(r'<h2>Topics</h2>\n<div class="card-grid cols-3">.*?\n</div>\n\n', t, re.S).group(0)
        t = t.replace(topics, "")
        pick = re.search(r'<h2>Pick a clip</h2>.*?<div id="clip-results"></div>\n\n', t, re.S).group(0)
        t = t.replace(pick, "")
        block = "<!-- below-fold-v3:start -->\n" + topics + pick + "<!-- below-fold-v3:end -->\n"
    t = t.replace('<div class="section-head">\n  <h2>Latest</h2>', '<div class="section-head" id="latest">\n  <h2>Latest</h2>', 1)
    t = re.sub(r'(<div class="card-grid" data-latest-cards[^>]*></div>\n)', lambda mm: mm.group(1) + "\n" + block, t, count=1)
    p.write_text(t, encoding="utf-8")
    return c


def main():
    update_mood_json()
    rep = patch_mood_pages()
    c = patch_homepage()
    print(json.dumps(rep, indent=1))
    print("start clip:", c["guest"], c["episode_number"], c["title"], c["start"], c["youtube_id"])


if __name__ == "__main__":
    main()
