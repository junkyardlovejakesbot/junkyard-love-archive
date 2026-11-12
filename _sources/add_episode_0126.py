#!/usr/bin/env python3
"""Add episode 0126 (Jess Soto) from published sources only (RSS + YouTube + Transistor SRT).
Targeted injection (same approach as 0125): page, episode.md, guest page, list pages, indexes.
Downstream: build_ask_junkyard.py -> pass2_crawler_survivability.py (discovery_v4, play starts, chapters json, sitemap).
No Archive picks. Published quotes only. Clip summaries empty. No promo zone (no sponsor/ad read)."""
import json, re, csv, io, shutil, html as H
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "_sources"
WORK = Path("/tmp/e126")
ORIGIN = "https://junkyardlovejakesbot.github.io/junkyard-love-archive"
esc = lambda s: H.escape(s, quote=True)

NUM = "0126"; SLUG = "0126-jess-soto-a-great-love-story"; GUEST = "Jess Soto"; GSLUG = "jess-soto"
FOLDER = SRC / "content" / "0126-jess-soto"
RSS_TITLE = "A Great Love Story - 30 Ayahuasca Ceremonies, a Sister's Betrayal, Pregnant at 15 - with Jess Soto - Ep. 0126"
YT_TITLE = "A Great Love Story: 30 Ayahuasca Ceremonies, a Sister's Betrayal, Pregnant at 15 - with Jess Soto"
TITLE = "A Great Love Story - 30 Ayahuasca Ceremonies, a Sister's Betrayal, Pregnant at 15 - Episode 0126 with Jess Soto"
BROWSE = "A Great Love Story"
DATE = "2026-11-11"; DUR_S = 5102; DUR = "1:25:02"; DUR_ISO = "PT1H25M2S"
YT = "T6KpYZSV5GA"; YT_URL = f"https://www.youtube.com/watch?v={YT}"
RSS_EP = "https://share.transistor.fm/s/4eec7b74"
AUDIO = "https://claritaspod.com/measure/2.gum.fm/op3.dev/e/pscrb.fm/rss/p/pdst.fm/e/dts.podtrac.com/redirect.mp3/prfx.byspotify.com/e/media.transistor.fm/4eec7b74/eb797641.mp3"
GUID = "c9283846-33f9-4cf6-8f1b-da2ddcfb87bf"
SPOTIFY = "https://open.spotify.com/show/45J7CBdM8j29doqyBp2bFs"
APPLE = "https://podcasts.apple.com/us/podcast/the-junkyard-love-podcast/id1489118788"
THUMB = f"https://i.ytimg.com/vi/{YT}/hqdefault.jpg"
EP_URL = f"{ORIGIN}/episodes/{SLUG}/"

# Jacob's published About (RSS + YouTube description, identical; stray trailing '**' markdown marker dropped)
ABOUT = [
 "Jess Soto is the #1 international bestselling author of Becoming HER: A Journey of Remembering, founder of Beacon of Hope, a keynote speaker, certified life coach, QHHT practitioner and Theta Healer, and host of the Jess Flow podcast.",
 "Jess became a mom at 15. She was raised by her grandmother while both parents battled addiction, went through foster care with her son, survived two men who tried to kill her, and walked away for good the morning after Easter Sunday. Years later, standing in her kitchen on autopilot, one question stopped her cold: are you happy?",
 "More than 30 ayahuasca ceremonies. A text message revealing that her sister and her ex-husband had been together behind her back for three years. And a choice to call the whole thing a great love story. We talk about breaking the cycle, forgiving without pretending it didn't hurt, why the real ceremony is life, sensual bachata as a moving meditation, and why she's still human enough to lose it with her teenage daughter.",
]
CONTENT_NOTE = "Content note: this episode includes domestic violence, drug use and strong language."  # YouTube description
QUOTES = [
 "The narrative that I'm going to give this is that this is a great love story. They gave me an opportunity to choose love in the face of betrayal.",
 "There was something in me like I knew I had a choice to make.",
 "I needed to end that cycle.",
 "If you're not happy, what is it all for?",
 "Forgiveness is not a one and done. It's a continual choice.",
 "I allowed myself to feel it, but I didn't stay there.",
 "The real ceremony is life.",
 "How do I respond when life shows its teeth?",
 "Earth is a school, right?",
 "Everyone is in their own dance.",
 "The love that you're seeking is within you.",
 "You can turn your pain into purpose.",
 "You are not broken. You are not too far gone.",
]
CH_RAW = """00:00|Welcome
01:31|Mom at 15
02:08|Raised by Her Grandmother
03:23|"I Knew I Had a Choice"
04:18|Chaos, Couch Surfing & Foster Care
06:29|Abusive Relationships
08:01|Easter Sunday & Choosing Herself
10:52|The Manager Who Gave Her Courage
11:48|Ending the Cycle
14:41|Spiritual Awakening at 35
16:59|Changing What You Consume
19:31|Tony Robbins & Priming
21:46|Grief Stored in the Body
24:14|"Who Am I?" and "Are You Happy?"
28:00|The Body Knew: A Stab in the Back
29:16|Ayahuasca, Colombia & the Text Message
34:33|Choose Love: A Great Love Story
36:24|Feel It, But Don't Stay There
41:20|Breath Work, Yoga & Sensual Bachata
49:42|What Is Ayahuasca, Really?
52:20|30+ Ceremonies & Writing the Book
54:58|The Real Ceremony Is Life
57:35|Still Human: Triggers & Her Daughter
1:06:30|What Projection Really Means
1:09:06|Intuition & Muscle Testing
1:13:26|Time Is an Illusion
1:18:10|For Anyone Still in an Abusive Relationship
1:23:10|You Are Not Broken + Where to Find Jess"""
def secs(t):
    p = [int(x) for x in t.split(":")]
    return p[0]*3600+p[1]*60+p[2] if len(p) == 3 else p[0]*60+p[1]
def hms(s): s = int(s); return f"{s//3600:02d}:{s%3600//60:02d}:{s%60:02d}"
def anc(s): return "t-" + hms(s).replace(":", "-")
CHAPTERS = [(secs(a), b) for a, b in (l.split("|", 1) for l in CH_RAW.splitlines())]
GUEST_LINKS = [
 ("Instagram", "https://www.instagram.com/jess_flow444/", "instagram.com/jess_flow444"),
 ("Website (courses, coaching, free 30-day guide)", "https://beaconofhope.world", "beaconofhope.world"),
 ("Book, Becoming HER: A Journey of Remembering (also on Audible, read by Jess)", "https://www.amazon.com/Becoming-HER-Remembering-Jess-Soto/dp/1971359955", "amazon.com/Becoming-HER-Remembering-Jess-Soto/dp/1971359955"),
 ("Companion journal, Becoming HER Journal: 30 Day Journey of Remembering", "https://us.amazon.com/Becoming-HER-Journal-Journey-Remembering/dp/B0GWCPKD6H", "us.amazon.com/Becoming-HER-Journal-Journey-Remembering/dp/B0GWCPKD6H"),
]
MENTIONED = "Abraham Hicks · The School of Greatness (Lewis Howes) · Tony Robbins' priming exercise · Dolores Cannon & QHHT · Theta Healing · Pema Chödrön · Alan Watts"
SUPPORT = "If you or someone you love needs help, the National Domestic Violence Hotline (US) is 1-800-799-7233."
KEYWORDS = "jess soto, becoming her a journey of remembering, beacon of hope, jess flow podcast, a great love story, 30 ayahuasca ceremonies, ayahuasca integration, sister betrayal, affair with ex husband, choosing love, forgiveness after betrayal, mom at 15, teen mom story, foster care survivor, domestic violence survivor, leaving an abusive relationship, breaking generational cycles, spiritual awakening at 35, the real ceremony is life, sensual bachata, dance as moving meditation, somatic healing, emotions stored in the body, theta healing, muscle testing, qhht, projection, intuition, who am i, are you happy, junkyard love podcast, jacob from the internet"
TOPICS = [("healing-trauma-therapy", "Healing, Trauma & Therapy"), ("awakening-mystical", "Awakening & Mystical Experience"), ("love-sex-relationships", "Love, Sex & Relationships")]

def content_folder():
    (FOLDER / "captions").mkdir(parents=True, exist_ok=True)
    shutil.copy(WORK / "transistor.srt", FOLDER / "captions" / "transistor.srt")
    shutil.copy(WORK / "cap.en-US.json3", FOLDER / "captions" / "youtube-manual.en-US.json3")
    shutil.copy(WORK / "transcript.md", FOLDER / "transcript.md")
    shutil.copy(WORK / "desc.html", FOLDER / "source-rss-description.html")
    yt = json.load(open(WORK / "yt.json"))
    (FOLDER / "source-description.raw.txt").write_text(yt["description"] + "\n")
    (FOLDER / "source-youtube-title.txt").write_text(yt["title"] + "\n")
    (FOLDER / "source-about.md").write_text("\n\n".join(ABOUT) + "\n")
    (FOLDER / "source-quotes.md").write_text("\n\n".join(f'"{q}"' for q in QUOTES) + "\n")
    (FOLDER / "source-timestamps.md").write_text("(Published chapters — RSS/YouTube description)\n\n" + "\n".join(f"- [{hms(s)}](#{anc(s)}) — {t}" for s, t in CHAPTERS) + "\n")
    (FOLDER / "source-links.md").write_text("\n".join(f"- {a}: {u}" for a, _, u in GUEST_LINKS) + "\n- Jess Flow podcast (wherever you listen)\n")
    (FOLDER / "source-hashtags.txt").write_text("")
    meta = {"episode_number": NUM, "episodeNumber": 126, "title": TITLE, "title_rss": RSS_TITLE, "title_youtube": YT_TITLE,
            "guest": GUEST, "datePublished": DATE, "duration_seconds": DUR_S, "duration_iso": DUR_ISO, "duration_human": DUR,
            "youtube_url": YT_URL, "rss_url": RSS_EP, "audio_url": AUDIO, "spotify_show": SPOTIFY, "apple_show": APPLE,
            "guid": GUID, "explicit": True}
    (FOLDER / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n")
    turns = json.load(open(WORK / "turns.json"))
    words = sum(len(t["text"].split()) for t in turns)
    (FOLDER / "TRANSCRIPT_SOURCE.txt").write_text(
        f"Source: Transistor published SRT (share.transistor.fm/s/4eec7b74/transcript.srt); identical text to YouTube manual captions en-US.\n"
        f"Video: {YT_URL}\nTurns: {len(turns)}\nWord count: {words}\n"
        "Speaker map: captions carry no speaker labels; Jacob / Jess assigned by reading the conversation (question/answer, names, content) at caption-cue level.\n"
        "Cleanup: [Intro music]/[Outro music] cues dropped; consecutive same-speaker cues merged. No sentence rewriting.\nPublished clock (YouTube chapters = RSS chapters).\n")
    (FOLDER / "SOURCES.txt").write_text(f"Description source: Jacob About copy (RSS item + YouTube description, identical)\nYouTube: {YT} (chapters valid)\nRSS guid: {GUID}\nNo Archive picks. No promo zone (no sponsor/ad read in transcript).\n")
    return turns, words

def paragraphs(turns):
    """Split turns at published chapter marks so chapter links land on the right paragraph."""
    marks = [s for s, _ in CHAPTERS]
    paras = []
    for t in turns:
        cur = None
        for st, txt in t["pieces"]:
            split = cur is None or any(cur["start"] < m - 1 and st >= m - 1 for m in marks)
            if split:
                cur = {"spk": t["spk"], "start": (t["start"] if not paras or cur is None and not t.get("_used") else st), "text": ""}
                if t.get("_used"): cur["start"] = st
                t["_used"] = True
                paras.append(cur)
            cur["text"] += (" " if cur["text"] else "") + txt
    # dedupe anchor ids
    seen = set()
    for p in paras:
        s = int(p["start"])
        while anc(s) in seen: s += 1
        p["id"] = anc(s); seen.add(p["id"]); p["s"] = s
    return paras

HEAD_NAV = None
def page_shell():
    ref = (ROOT / "episodes/0125-fran-frye-shame-sex-mens-mental-health/index.html").read_text()
    head_top = ref.split("<title>")[0]
    m = re.search(r'</head>\n<body>\n(<div class="wrap">.*?</header>\n)', ref, re.S)
    foot = ref[ref.index("</article>"):]
    return head_top, m.group(1), foot

def episode_page(paras, words):
    head_top, header, foot = page_shell()
    desc = ABOUT[0][:157].rsplit(" ", 1)[0] + "…"
    jsonld = {"@context": "https://schema.org", "@type": "PodcastEpisode", "name": TITLE, "url": EP_URL,
              "partOfSeries": {"@type": "PodcastSeries", "name": "The Junkyard Love Podcast", "url": ORIGIN + "/", "webFeed": "https://feeds.transistor.fm/the-junkyard-love-podcast"},
              "datePublished": DATE, "duration": DUR_ISO, "episodeNumber": 126, "contributor": {"@type": "Person", "name": GUEST},
              "sameAs": [YT_URL, RSS_EP],
              "associatedMedia": [{"@type": "VideoObject", "name": TITLE, "contentUrl": YT_URL, "embedUrl": f"https://www.youtube.com/embed/{YT}", "thumbnailUrl": THUMB},
                                  {"@type": "AudioObject", "contentUrl": AUDIO}],
              "transcript": {"@type": "CreativeWork", "url": EP_URL + "episode.md", "encodingFormat": "text/markdown"},
              "actor": {"@type": "Person", "name": GUEST}}
    o = [head_top + f"<title>{esc(TITLE)}</title>",
         f'<meta name="description" content="{esc(desc)}">',
         f'<meta property="og:title" content="{esc(TITLE)}">', f'<meta property="og:description" content="{esc(desc)}">',
         '<meta property="og:type" content="article">', f'<meta property="og:url" content="{EP_URL}">',
         '<link rel="stylesheet" href="assets/style.css">', f'<link rel="canonical" href="{EP_URL}">',
         f'<meta name="twitter:image" content="{THUMB}">', f'<meta name="twitter:description" content="{esc(desc)}">',
         f'<meta name="twitter:title" content="{esc(TITLE)}">', '<meta name="twitter:card" content="summary_large_image">',
         f'<meta property="og:image" content="{THUMB}">', "</head>", "<body>", header,
         '<script type="application/ld+json">\n' + json.dumps(jsonld, indent=2, ensure_ascii=False) + "\n</script>",
         "<article>", '<div class="ep-hero">', f'<div class="ep-hero-media"><img src="{THUMB}" alt="" width="480" height="360"></div>', '<div class="ep-hero-text">', "",
         f"<h1>{esc(TITLE)}</h1>", f'<p class="browse-subtitle">{esc(BROWSE)}</p>',
         f'<p class="meta">Episode {NUM} · Published {DATE} · 2026 · {DUR} · Guest: <a href="guests/{GSLUG}/index.html">{esc(GUEST)}</a></p>',
         '<div class="listen">', f'  <a href="{YT_URL}">YouTube</a>', f'  <a href="{SPOTIFY}">Spotify (show)</a>', f'  <a href="{APPLE}">Apple (show)</a>', f'  <a href="{RSS_EP}">RSS episode</a>', "</div>",
         "<!-- topic-chips:start -->", '<p class="topic-chips"><span class="topic-chips-label">Topics</span>']
    o += [f'  <a class="topic-chip" href="topics/{s}/index.html">{esc(t).replace("&#x27;", chr(39))}</a>' for s, t in TOPICS]
    o += ["</p>", "<!-- topic-chips:end -->", "</div><!-- /.ep-hero-text --></div><!-- /.ep-hero -->", "",
          f'<div class="yt-embed"><iframe src="https://www.youtube.com/embed/{YT}" title="YouTube video" loading="lazy" allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe></div>',
          "<h2>About</h2>", f'<p class="note transcript-files"><a href="episodes/{SLUG}/episode.md">Transcript (markdown)</a></p>', '<div class="about">']
    o += [f"<p>{esc(p)}</p>" for p in ABOUT]
    o += [f'<p class="note">{esc(CONTENT_NOTE)}</p>', f"<p><strong>Mentioned in this episode:</strong> {esc(MENTIONED)}</p>", f"<p><strong>Support:</strong> {esc(SUPPORT)}</p>", "</div>",
          "<h2>Chapters</h2>", '<ul class="chapters">']
    o += [f'<li><a href="#{anc(s)}">{hms(s)}</a> — {esc(t)}</li>' for s, t in CHAPTERS]
    o += ["</ul>", "<h2>Quotes</h2>", f'<p class="note">From the published episode notes (Jess).</p>', '<div class="quotes">']
    o += [f"<blockquote>“{esc(q)}”</blockquote>" for q in QUOTES]
    o += ["</div>", "<h2>Guest</h2>", f'<p><a href="guests/{GSLUG}/index.html">{esc(GUEST)}</a></p>', '<ul class="guest-links">']
    o += [f'<li><a href="{u}">{esc(a)}</a></li>' for a, u, _ in GUEST_LINKS] + ["<li>Jess Flow podcast (wherever you listen)</li>", "</ul>",
          "<h2>Tags / keywords</h2>", f'<p class="tags">{esc(KEYWORDS)}</p>',
          "<h2>Full transcript</h2>", f'<p class="note">Source: Transistor published SRT (same text as the YouTube captions). Speaker labels added by reading the conversation; text not rewritten. Word count: {words}.</p>', '<div class="transcript">']
    before = {}
    for c, _ in CHAPTERS:
        idx = max([i for i, p in enumerate(paras) if p["s"] <= c + 2] or [0])
        before.setdefault(idx, []).append(c)
    for i, p in enumerate(paras):
        for c in before.get(i, []):
            if anc(c) != p["id"]:
                o.append(f'<span id="{anc(c)}" class="chapter-anchor"></span>')
        o.append(f'<p class="cue" id="{p["id"]}"><a class="ts" href="#{p["id"]}">[{hms(p["s"])}]</a> <span class="speaker">{p["spk"]}:</span> {esc(p["text"])}</p>')
    o.append("</div>")
    html = "\n".join(o) + "\n" + foot
    d = ROOT / "episodes" / SLUG; d.mkdir(parents=True, exist_ok=True)
    (d / "index.html").write_text(html)
    md = [f"# {TITLE}", "", f"- Episode: {NUM}", f"- Date: {DATE}", f"- Duration: {DUR}", f"- Guest: [{GUEST}](/guests/{GSLUG}/)",
          f"- YouTube: {YT_URL}", f"- RSS: {RSS_EP}", f"- Spotify (show): {SPOTIFY}", f"- Apple (show): {APPLE}", "", "## About", ""]
    md += [x for p in ABOUT for x in (p, "")] + [CONTENT_NOTE, "", f"Mentioned in this episode: {MENTIONED}", "", f"Support: {SUPPORT}", "", "## Chapters", ""]
    md += [f"- [{hms(s)}](#{anc(s)}) — {t}" for s, t in CHAPTERS] + ["", "## Quotes", ""] + [f"- “{q}”" for q in QUOTES]
    md += ["", "## Guest links (from published notes)", ""] + [f"- {a}: {u}" for a, u, _ in GUEST_LINKS] + ["- Jess Flow podcast (wherever you listen)", "", "## Tags / keywords", "", KEYWORDS, "", "## Transcript", ""]
    md += [f"[{hms(p['s'])}] {p['spk']}: {p['text']}\n" for p in paras]
    (d / "episode.md").write_text("\n".join(md) + "\n")

def card(title):
    return (f'<a class="ep-card" href="episodes/{SLUG}/index.html"><div class="ep-card-thumb"><img src="{THUMB}" alt="" loading="lazy" width="480" height="360"></div>'
            f'<div class="ep-card-body"><p class="ep-card-title">{title}</p><p class="ep-card-meta">Episode {NUM} · {GUEST} · {DUR}</p></div></a>')

def list_pages():
    p = ROOT / "episodes/index.html"; s = p.read_text()
    if SLUG not in s:
        ref = '<a class="ep-card" href="episodes/0125-fran-frye'
        s = s.replace(ref, card(esc(BROWSE)) + "\n" + ref, 1); p.write_text(s)
    for slug, _ in TOPICS:
        p = ROOT / "topics" / slug / "index.html"; s = p.read_text()
        if SLUG in s: continue
        m = re.search(r'<div class="card-grid">\n', s)
        s = s[:m.end()] + card(BROWSE) + "\n" + s[m.end():]; p.write_text(s)
    # guests index (alphabetical by data-guest-name)
    p = ROOT / "guests/index.html"; s = p.read_text()
    if f'data-guest-slug="{GSLUG}"' not in s:
        li = f'<li data-guest-name="jess soto" data-guest-slug="{GSLUG}"><a href="guests/{GSLUG}/index.html">{GUEST}</a></li>'
        items = list(re.finditer(r'<li data-guest-name="([^"]*)" data-guest-slug="[^"]*">.*?</li>', s))
        after = [m for m in items if m.group(1) > "jess soto"]
        pos = after[0].start() if after else items[-1].end()
        s = s[:pos] + li + s[pos:]; p.write_text(s)

def guest_page():
    ref = (ROOT / "guests/fran-frye/index.html").read_text()
    head_top = ref.split("<title>")[0]
    header = re.search(r'(<div class="wrap">.*?</header>\n)', ref, re.S).group(1)
    foot = ref[ref.index("<footer class=\"site\">"):]
    gurl = f"{ORIGIN}/guests/{GSLUG}/"
    d = "Jess Soto on The Junkyard Love Podcast — episodes, published quotes, and what they made (when verified)."
    o = [head_top + f"<title>{GUEST} — The Junkyard Love Podcast</title>", f'<meta name="description" content="{d}">',
         f'<meta property="og:title" content="{GUEST}">', f'<meta property="og:description" content="{d}">', '<meta property="og:type" content="website">',
         f'<meta property="og:url" content="{gurl}">', '<link rel="stylesheet" href="assets/style.css">', f'<link rel="canonical" href="{gurl}">',
         f'<meta name="twitter:image" content="{THUMB}">', f'<meta name="twitter:description" content="{d}">', f'<meta name="twitter:title" content="{GUEST}">',
         '<meta name="twitter:card" content="summary_large_image">', f'<meta property="og:image" content="{THUMB}">', "</head>", "<body>", header,
         f"<h1>{GUEST}</h1>", f'<p class="lede guest-about">{esc(ABOUT[0]).replace("&#x27;", chr(39))}</p>', "<h2>Episodes</h2>", '<ul class="list guest-episodes">',
         f'<li><a href="episodes/{SLUG}/index.html"><strong>{NUM}</strong> — {BROWSE}</a><br><span class="note">Episode {NUM} · {DATE} · {DUR}</span></li>', "</ul>", "<h2>Published quotes</h2>"]
    for q in QUOTES:
        o += ["<blockquote>", f"<p>{esc(q).replace('&#x27;', chr(39))}</p>", f'<p class="note"><a href="episodes/{SLUG}/index.html">Episode {NUM}</a></p>', "</blockquote>"]
    o += ['<h2 class="also-made">Also made</h2>',
          '<p class="also-made-item"><a href="https://www.amazon.com/Becoming-HER-Remembering-Jess-Soto/dp/1971359955" target="_blank" rel="noopener">Becoming HER: A Journey of Remembering</a> <span class="note">(book)</span></p>',
          '<p class="also-made-item"><a href="https://beaconofhope.world" target="_blank" rel="noopener">Beacon of Hope</a> <span class="note">(website)</span></p>',
          '<p class="clip-permission note">You’re welcome to clip this conversation. I won’t copyright you.</p>', ""]
    dd = ROOT / "guests" / GSLUG; dd.mkdir(parents=True, exist_ok=True)
    (dd / "index.html").write_text("\n".join(o) + "\n" + foot)

def indexes():
    pub = {}
    p = SRC / "episodes_index.json"  # assets/ is a mirror of _sources/
    for path in (SRC / "episodes_index.json", ROOT / "assets/episodes_index.json"):
        e = json.load(open(path))
        e["episodes"] = [x for x in e["episodes"] if x["number"] != NUM]
        e["episodes"].append({"slug": SLUG, "number": NUM, "browse_title": BROWSE, "canonical_title": TITLE, "guest": GUEST,
            "duration": DUR, "duration_seconds": DUR_S, "date": DATE, "youtube_id": YT, "youtube_url": YT_URL,
            "spotify_show": SPOTIFY, "apple_show": APPLE, "rss_url": RSS_EP,
            "topics": [{"slug": s, "title": t} for s, t in TOPICS],
            "chapters": [{"start": hms(s), "start_seconds": s, "title": t} for s, t in CHAPTERS],
            "quotes": [{"text": q, "source": "published"} for q in QUOTES]})
        e["episode_count"] = len(e["episodes"])
        for t in e.get("topics", []):
            if t["slug"] in dict(TOPICS):
                t["count"] = sum(1 for x in e["episodes"] if any(tt["slug"] == t["slug"] for tt in x.get("topics", [])))
        path.write_text(json.dumps(e, ensure_ascii=False, indent=2) + "\n")
    for path in (SRC / "clips_index.json", ROOT / "assets/clips_index.json"):
        c = json.load(open(path))
        c["clips"] = [x for x in c["clips"] if x.get("episode_number") != NUM]
        for s, t in CHAPTERS:
            c["clips"].append({"episode_slug": SLUG, "episode_number": NUM, "browse_title": BROWSE, "guest": GUEST,
                "start": hms(s), "start_seconds": s, "title": t, "short_summary": "", "long_summary": "",
                "topic_tags": [x for x, _ in TOPICS], "youtube_id": YT, "host_open": False})
        c["clip_count"] = len(c["clips"]); c["episode_count"] = len({x["episode_slug"] for x in c["clips"]})
        path.write_text(json.dumps(c, ensure_ascii=False, indent=2) + "\n")
    for path in (SRC / "quotes_clean.json", ROOT / "assets/quotes_clean.json"):
        q = json.load(open(path))
        q["quotes"] = [x for x in q["quotes"] if x.get("episode_number") != NUM]
        q["quotes"] += [{"speaker": GUEST, "episode_slug": SLUG, "episode_number": NUM, "browse_title": BROWSE, "text": t, "source": "published"} for t in QUOTES]
        q["count"] = len(q["quotes"])
        path.write_text(json.dumps(q, ensure_ascii=True, indent=2) + "\n")

def inventory_llms():
    p = ROOT / "inventory.csv"; rows = list(csv.reader(io.StringIO(p.read_text(), newline="")))
    hdr = rows[0]; rows = [r for r in rows if r[0] != NUM]
    row = dict(episode_number=NUM, exact_public_title=TITLE, title_rss=RSS_TITLE, title_youtube=YT_TITLE, title_conflict="", publish_date=DATE,
               duration=DUR, duration_seconds=str(DUR_S), guest_name=GUEST, youtube_url=YT_URL, audio_enclosure_url=AUDIO, rss_episode_url=RSS_EP,
               youtube_match_method="episode_number", youtube_captions_exist="yes", listen_notes_transcript="no/unknown",
               has_timestamps="yes", has_quotes="yes", has_hashtags="no", has_guest_links="yes", description_chars=str(len(open(WORK / "desc.html").read())))
    rows.insert(1, [row.get(h, "") for h in hdr])
    out = io.StringIO(); csv.writer(out, lineterminator="\r\n").writerows(rows); p.write_text(out.getvalue())
    p = ROOT / "llms.txt"; s = p.read_text()
    if SLUG not in s:
        s = s.replace("## Episodes (processed)\n", f"## Episodes (processed)\n- [{NUM} {GUEST} — {BROWSE}]({EP_URL}) — {DATE}\n", 1)
        u = EP_URL + "episode.md"
        s = s.replace("## Episode markdown mirrors\n", f"## Episode markdown mirrors\n- [{u}]({u})\n", 1)
        p.write_text(s)

if __name__ == "__main__":
    turns, words = content_folder()
    paras = paragraphs(turns)
    (FOLDER / "transcript.md").write_text("".join(f"[{hms(p['s'])}] {p['spk']}: {p['text']}\n\n" for p in paras))
    episode_page(paras, words)
    guest_page(); list_pages(); indexes(); inventory_llms()
    print("paras", len(paras), "words", words)
