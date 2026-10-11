#!/usr/bin/env python3
"""Discovery v4 (idempotent): meta descriptions from published About, OG/Twitter cards,
PodcastEpisode/Person JSON-LD upgrade, 'Also in this lane' related block.
Data sources: assets/episodes_index.json, assets/books_index.json, page About text only."""
import html, json, re, sys, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://junkyardlovejakesbot.github.io/junkyard-love-archive/"
TODAY = datetime.date.today().isoformat()
BANNED = re.compile(r"\b(NBA|NFL|NHL|MLB|MLS|WNBA)\b|erotic|sexual violence|classmate", re.I)
idx = json.loads((ROOT / "assets/episodes_index.json").read_text())
EPS = [e for e in idx["episodes"] if e["number"] not in set(idx.get("removed", []))]
BY_SLUG = {e["slug"]: e for e in EPS}
changed, skipped, report = set(), [], {"desc": 0, "guest_noimg": []}

def strip_tags(s):
    return html.unescape(re.sub(r"<[^>]+>", " ", s))

def norm(s):
    return re.sub(r"\s+", " ", s).strip()

def about_text(page):
    m = re.search(r'<div class="about">(.*?)</div>', page, re.S)
    if not m:
        return ""
    paras = re.findall(r"<p>(.*?)</p>", m.group(1), re.S) or [m.group(1)]
    out = []
    for p in paras:
        t = norm(strip_tags(p))
        if re.match(r"(check out|find|follow|connect with)", t, re.I) or re.search(r"https?://|:\s*$", t) and len(t) < 80:
            break
        if t.startswith("(") and t.endswith(")"):
            continue
        out.append(t)
    return norm(" ".join(out))

def sentences(t):
    return [s for s in re.split(r"(?<=[.!?])\s+(?=[A-Z\"'“])", t) if s]

def make_desc(about, fallback_tail):
    sents = [s for s in sentences(about) if not BANNED.search(s) and not s.startswith("(")]
    if not sents:
        return None
    out = ""
    for s in sents:
        cand = (out + " " + s).strip()
        if len(cand) <= 160:
            out = cand
            if len(out) >= 140:
                return out
        else:
            # trim this sentence at a word boundary with ellipsis
            room = 159 - (len(out) + 1 if out else 0)
            if True:
                cut = s[:room].rsplit(" ", 1)[0].rstrip(",;:—– -")
                res = (out + " " + cut).strip() + "…"
                if len(res) >= 140:
                    return res
            break
    # still short: add factual tail from the page H1 data
    cand = (out + " " + fallback_tail).strip()
    if 140 <= len(cand) <= 160:
        return cand
    return out if len(out) >= 140 else None

def esc(s):
    return html.escape(s, quote=True)

def set_meta(page, attr, key, val, after_pat=r'<meta name="viewport"[^>]*>\n'):
    tag = f'<meta {attr}="{key}" content="{esc(val)}">'
    pat = re.compile(rf'<meta {attr}="{re.escape(key)}" content="[^"]*">\n?')
    if pat.search(page):
        page = pat.sub(tag + "\n", page, count=1)
        # remove duplicates
        first = page.find(tag)
        rest = pat.sub("", page[first + len(tag):])
        return page[:first + len(tag)] + rest
    m = re.search(r'<link rel="canonical"[^>]*>\n', page) or re.search(after_pat, page)
    i = m.end() if m else page.find("</head>")
    return page[:i] + tag + "\n" + page[i:]

def h1_text(page):
    m = re.search(r"<h1[^>]*>(.*?)</h1>", page, re.S)
    return norm(strip_tags(m.group(1))) if m else None

def apply_cards(page, title, desc, img, typ):
    for k, v in (("og:title", title), ("og:description", desc), ("og:type", typ)):
        if v: page = set_meta(page, "property", k, v)
    if img: page = set_meta(page, "property", "og:image", img)
    page = set_meta(page, "name", "twitter:card", "summary_large_image")
    if title: page = set_meta(page, "name", "twitter:title", title)
    if desc: page = set_meta(page, "name", "twitter:description", desc)
    if img: page = set_meta(page, "name", "twitter:image", img)
    return page

def get_desc(page):
    m = re.search(r'<meta name="description" content="([^"]*)">', page)
    return html.unescape(m.group(1)) if m else None

def iso_dur(sec):
    h, r = divmod(int(sec), 3600); m, s = divmod(r, 60)
    return "PT" + (f"{h}H" if h else "") + (f"{m}M" if m else "") + (f"{s}S" if s or not (h or m) else "")

def upgrade_jsonld(page, typ, fn):
    blocks = list(re.finditer(r'<script type="application/ld\+json">\s*(.*?)\s*</script>\n?', page, re.S))
    hit = [b for b in blocks if json.loads(b.group(1)).get("@type") == typ]
    data = json.loads(hit[0].group(1)) if hit else {"@context": "https://schema.org", "@type": typ}
    data = fn(data)
    new = '<script type="application/ld+json">\n' + json.dumps(data, indent=2, ensure_ascii=False) + "\n</script>\n"
    if hit:
        for b in reversed(hit[1:]):
            page = page[:b.start()] + page[b.end():]
        b = hit[0]
        return page[:b.start()] + new + page[b.end():]
    i = page.find("</head>")
    return page[:i] + new + page[i:]

# ---- related data
book_eps = {}
for b in json.loads((ROOT / "assets/books_index.json").read_text())["books"]:
    slugs = {m["episode_slug"] for m in b.get("mentions") or [] if m.get("episode_slug")}
    if b.get("episode_slug"): slugs.add(b["episode_slug"])
    for s in slugs:
        book_eps.setdefault(s, []).append((b["title"], slugs))

def related(e):
    n = int(e["number"]); cands = {}
    for o in EPS:
        if o["slug"] == e["slug"]: continue
        if o.get("guest") and o.get("guest") == e.get("guest"):
            cands[o["slug"]] = (0, 0, abs(int(o["number"]) - n), "Same guest")
    for title, slugs in book_eps.get(e["slug"], []):
        for s in sorted(slugs):
            if s != e["slug"] and s in BY_SLUG and s not in cands:
                cands[s] = (1, 0, abs(int(BY_SLUG[s]["number"]) - n), f"Also mentions {title}")
    my = {t["slug"]: t["title"] for t in e.get("topics") or []}
    for o in EPS:
        if o["slug"] == e["slug"] or o["slug"] in cands: continue
        shared = [my[t["slug"]] for t in o.get("topics") or [] if t["slug"] in my]
        if shared:
            cands[o["slug"]] = (2, -len(shared), abs(int(o["number"]) - n), "Also in " + " · ".join(shared[:2]))
    picks = sorted(cands.items(), key=lambda kv: kv[1][:3] + (kv[0],))[:4]
    return [(BY_SLUG[s], v[3]) for s, v in picks]

def related_html(items):
    lis = "\n".join(
        f'<li><a href="episodes/{o["slug"]}/index.html"><strong>{o["number"]}</strong> — {esc(o.get("browse_title") or o.get("canonical_title"))}</a>'
        f'<br><span class="note">{esc(o.get("guest") or "")} · {esc(why)}</span></li>' for o, why in items)
    return ('<!-- related:start -->\n<section class="related-lane" aria-label="Also in this lane">\n<h2>Also in this lane</h2>\n'
            f'<ul class="list related-list">\n{lis}\n</ul>\n</section>\n<!-- related:end -->\n')

# ---- episodes
descs = {}
for e in EPS:
    p = ROOT / "episodes" / e["slug"] / "index.html"
    if not p.exists():
        skipped.append((e["number"], "page missing")); continue
    page = orig = p.read_text(encoding="utf-8")
    tail = f"Episode {e['number']} of The Junkyard Love Podcast with {e.get('guest')}." if e.get("guest") else ""
    d = make_desc(about_text(page), tail)
    if d and d in descs.values():
        d = None
    if d:
        descs[e["slug"]] = d
        page = set_meta(page, "name", "description", d); report["desc"] += 1
    else:
        skipped.append((e["number"], "no usable About for a 140-160 char description"))
    canon = SITE + f"episodes/{e['slug']}/"
    yt = e.get("youtube_id"); yurl = f"https://www.youtube.com/watch?v={yt}" if yt else None
    img = f"https://i.ytimg.com/vi/{yt}/hqdefault.jpg" if yt else None
    page = apply_cards(page, h1_text(page), d or get_desc(page), img, "article")
    def fix(j, e=e, canon=canon, yurl=yurl, yt=yt, page=page):
        j["name"] = h1_text(page) or j.get("name"); j["url"] = canon
        if e.get("date"): j["datePublished"] = e["date"]
        if e.get("duration_seconds"): j["duration"] = iso_dur(e["duration_seconds"])
        j.pop("timeRequired", None)
        if e.get("guest"):
            j["actor"] = {"@type": "Person", "name": e["guest"]}
        am = j.get("associatedMedia", [])
        am = am if isinstance(am, list) else [am]
        media = [m for m in am if isinstance(m, dict) and m.get("@type") != "VideoObject"]
        sa0 = j.get("sameAs", [])
        j["sameAs"] = sa0 if isinstance(sa0, list) else [sa0]
        if yurl:
            media.insert(0, {"@type": "VideoObject", "name": j["name"], "contentUrl": yurl,
                             "embedUrl": f"https://www.youtube.com/embed/{yt}", "thumbnailUrl": f"https://i.ytimg.com/vi/{yt}/hqdefault.jpg"})
            sa = [s for s in j.get("sameAs", []) if s != yurl]; j["sameAs"] = [yurl] + sa
        if media: j["associatedMedia"] = media
        j.pop("publisher", None)
        return j
    page = upgrade_jsonld(page, "PodcastEpisode", fix)
    page = re.sub(r"<!-- related:start -->.*?<!-- related:end -->\n?", "", page, flags=re.S)
    items = related(e)
    if items:
        m = re.search(r'<div class="about">.*?</div>\n', page, re.S)
        if m: page = page[:m.end()] + related_html(items) + page[m.end():]
    if page != orig:
        p.write_text(page, encoding="utf-8"); changed.add(f"episodes/{e['slug']}/")

# ---- homepage, guests index, guest pages
latest_by_guest = {}
for e in EPS:
    g = e.get("guest")
    if g and e.get("youtube_id") and (g not in latest_by_guest or int(e["number"]) > int(latest_by_guest[g]["number"])):
        latest_by_guest[g] = e
for rel in ["index.html", "guests/index.html"] + sorted(str(x.relative_to(ROOT)) for x in (ROOT / "guests").glob("*/index.html")):
    p = ROOT / rel; page = orig = p.read_text(encoding="utf-8")
    is_guest = rel.count("/") == 2
    title = h1_text(page) if rel != "index.html" else None  # homepage: keep existing og:title
    if rel == "index.html":
        m = re.search(r'<meta property="og:title" content="([^"]*)">', page); title = html.unescape(m.group(1)) if m else None
    img = None
    if is_guest:
        name = h1_text(page)
        linked = [BY_SLUG[x] for x in re.findall(r'href="episodes/([^/"]+)/index.html"', page) if x in BY_SLUG and BY_SLUG[x].get("youtube_id")]
        e = max(linked, key=lambda x: int(x["number"])) if linked else latest_by_guest.get(name)
        if e: img = f"https://i.ytimg.com/vi/{e['youtube_id']}/hqdefault.jpg"
        else: report["guest_noimg"].append(rel)
        url = SITE + rel.replace("index.html", "")
        def pfix(j, name=name, url=url):
            j["name"] = name; j["url"] = url; return j
        page = upgrade_jsonld(page, "Person", pfix)
    page = apply_cards(page, title, get_desc(page), img, "website")
    if page != orig:
        p.write_text(page, encoding="utf-8"); changed.add(rel.replace("index.html", ""))

# ---- sitemap lastmod for changed pages
sm = ROOT / "sitemap.xml"; s = sm.read_text()
for c in changed:
    loc = SITE + c if c else SITE.rstrip("/")
    for L in {loc, loc.rstrip("/"), loc.rstrip("/") + "/"}:
        s = re.sub(rf"(<loc>{re.escape(L)}</loc>\s*<lastmod>)[^<]*", rf"\g<1>{TODAY}", s)
sm.write_text(s)
print(json.dumps({"desc": report["desc"], "changed": len(changed), "skipped": skipped,
                  "guest_noimg": report["guest_noimg"]}, indent=1))
