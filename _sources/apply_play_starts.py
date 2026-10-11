"""Add speech-aligned play starts to every clip/chapter index (run after any rebuild).

For each entry with episode slug + start_seconds this adds
  play_start_seconds  - start of speech per _sources/speech_align.py (<= published, >= published-30)
  play_start          - HH:MM:SS of the above
  play_anchor         - nearest existing transcript #t- anchor at or before play_start_seconds
and points youtube_url (&t=) and transcript_url/url (#t-) at the play start.
Published labels (start, start_seconds, chapter titles) are never changed, except
0125 where the index drifted from the published chapter clock on the episode page:
those start/start_seconds are reset to the published clock (by exact title) first.
0125 promo zone (1:22:03 -> end) is never given a play start inside it.
"""
import json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import speech_align as A

REPO = A.HERE.parent
FILES = ["clips_index.json", "chapter_index.json", "mood_doors.json", "episodes_index.json"]
DRIFT_FIX = "all"  # any episode: unique title on page + unique in the index file -> published clock
INTRO_RE = __import__("re").compile(r"^(intro|bumper|countdown|music)\b|intro music|countdown", __import__("re").I)
_DUP = set()
PROMO = {"0125": 4923}
_pub, _anc, _fold = {}, {}, {}


def slug_of(d):
    return d.get("episode_slug") or (d.get("slug") if re.match(r"^\d{4}-", str(d.get("slug", ""))) else None)


def ctx(slug):
    if slug not in _pub:
        _pub[slug] = A.published_chapters(REPO, slug)
        _anc[slug] = A.anchors(REPO, slug)
        _fold[slug] = A.folder_for(slug)
    return _pub[slug], _anc[slug], _fold[slug]


_pc, _fs = {}, {}


def _pagecount(slug):
    if slug not in _pc:
        import html as H
        p = REPO / "episodes" / slug / "index.html"
        cnt = {}
        if p.exists():
            for m in re.finditer(r'<a href="#t-[\d-]+">\d\d:\d\d:\d\d</a> — (.*?)</li>', A.chapters_section(p.read_text())):
                t = H.unescape(m.group(1)).strip(); cnt[t] = cnt.get(t, 0) + 1
        _pc[slug] = cnt
    return _pc[slug]


def first_speech(slug):
    """Earliest published chapter mark that is not an intro/music bumper."""
    if slug not in _fs:
        # first speaker turn in the episode transcript (intro music / countdown /
        # bumper is not transcribed as a turn); fallback: first non-intro chapter
        pub, _, folder = ctx(slug)
        md = (folder / "transcript.md") if folder else None
        first = None
        if md and md.exists():
            m = re.search(r"^\[(\d\d):(\d\d):(\d\d)\]\s*[^:\n]{1,40}:", md.read_text(errors="ignore"), re.M)
            if m:
                first = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3))
                if first > 180:
                    first = None
        if first is None:
            ts = [int(v) for k, v in pub.items() if not INTRO_RE.search(k)]
            first = min(ts) if ts else None
        _fs[slug] = first
    return _fs[slug]


def fix_entry(d, stats):
    slug = slug_of(d)
    if not slug or d.get("start_seconds") is None:
        return
    pub, anc, folder = ctx(slug)
    num = slug[:4]
    title = d.get("title") or d.get("chapter_title")
    page_titles = _pagecount(slug)
    if (DRIFT_FIX == "all" or num in DRIFT_FIX) and title in pub and page_titles.get(title) == 1 \
            and (slug, title) not in _DUP and int(pub[title]) != int(d["start_seconds"]):
        old = int(d["start_seconds"]); new = int(pub[title])
        d["start_seconds"] = new
        for k in ("start", "chapter_time"):
            if k in d:
                d[k] = A.hms(new)
        stats["drift_fixed"].append((num, title, old, new))
    p = int(d["start_seconds"])
    if folder is None:
        s, kind = p, "none"
    else:
        s, kind, _ = A.play_start(folder, p)
    if num in PROMO and p < PROMO[num] <= s:
        s = p
    # never start inside intro music: no earlier than the first speech chapter
    floor = first_speech(slug)
    if floor is not None and s < floor <= p:
        s = floor
    d["play_start_seconds"] = s
    d["play_start"] = A.hms(s)
    a = max([x for x in anc if x <= s], default=None)
    if a is not None:
        d["play_anchor"] = "t-" + A.hms(a).replace(":", "-")
    for k in ("transcript_url", "url"):
        if isinstance(d.get(k), str) and "#t-" in d[k] and a is not None:
            d[k] = re.sub(r"#t-[\d-]+", "#" + d["play_anchor"], d[k])
    if isinstance(d.get("youtube_url"), str) and "t=" in d["youtube_url"]:
        d["youtube_url"] = re.sub(r"([?&]t=)\d+s?", lambda m: f"{m.group(1)}{s}s", d["youtube_url"])
    if d.get("_drift_noted") is None and stats["drift_fixed"] and stats["drift_fixed"][-1][0] == num:
        pass
    stats["n"] += 1
    stats["kinds"][kind] = stats["kinds"].get(kind, 0) + 1
    if p - s >= 1:
        stats["shifts"].append(p - s)
    if kind == "none":
        stats["nocap"].add(num)


def walk(o, stats):
    if isinstance(o, dict):
        fix_entry(o, stats)
        for v in o.values():
            walk(v, stats)
    elif isinstance(o, list):
        for v in o:
            walk(v, stats)


def new_stats():
    return {"n": 0, "kinds": {}, "shifts": [], "nocap": set(), "drift_fixed": []}


def process(path, stats):
    raw = path.read_text(encoding="utf-8")
    doc = json.loads(raw)
    _DUP.clear()
    seen = {}
    def scan(o):
        if isinstance(o, dict):
            sl = slug_of(o); t = o.get("title") or o.get("chapter_title")
            if sl and t and o.get("start_seconds") is not None:
                seen[(sl, t)] = seen.get((sl, t), 0) + 1
            for v in o.values(): scan(v)
        elif isinstance(o, list):
            for v in o: scan(v)
    scan(doc)
    _DUP.update(k for k, n in seen.items() if n > 1)
    if path.name == "episodes_index.json":
        for ep in doc.get("episodes", []):
            for ch in ep.get("chapters") or []:
                ch["episode_slug"] = ep["slug"]
                fix_entry(ch, stats)
                ch.pop("episode_slug", None)
    else:
        walk(doc, stats)
    compact = "\n" not in raw.strip()[:200]
    out = json.dumps(doc, ensure_ascii=False, separators=(",", ":")) if compact else json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
    if out != raw:
        path.write_text(out, encoding="utf-8")
        return True
    return False


def fix_mood_pages():
    """Point mood page YouTube t= links / embeds at play starts (labels untouched)."""
    doors = json.loads((REPO / "assets/mood_doors.json").read_text())
    changed = []
    for door in doors.get("doors", []):
        page = REPO / "moods" / door["slug"] / "index.html"
        if not page.exists():
            continue
        h = page.read_text(encoding="utf-8"); h0 = h
        for ch in door.get("chapters", []):
            if ch.get("youtube_id") and ch.get("play_start_seconds") is not None:
                vid, p, s = ch["youtube_id"], ch.get("_pub", ch["start_seconds"]), ch["play_start_seconds"]
                h = h.replace(f"v={vid}&amp;t={p}s", f"v={vid}&amp;t={s}s").replace(f"embed/{vid}?start={p}&", f"embed/{vid}?start={s}&")
        if h != h0:
            page.write_text(h, encoding="utf-8"); changed.append(page)
    return changed


def main():
    stats = new_stats()
    changed = []
    for base in (REPO / "assets", A.HERE):
        for f in FILES:
            if (base / f).exists() and process(base / f, stats):
                changed.append(base / f)
        for sh in sorted((base / "chapter_search").glob("*.json")) if (base / "chapter_search").exists() else []:
            if process(sh, stats):
                changed.append(sh)
        if (base / "chapter_search.json").exists() and process(base / "chapter_search.json", stats):
            changed.append(base / "chapter_search.json")
    changed += fix_mood_pages()
    sh = sorted(stats["shifts"])
    print(json.dumps({"entries": stats["n"], "kinds": stats["kinds"], "shifted": len(sh),
                      "median_shift": sh[len(sh)//2] if sh else 0, "max_shift": sh[-1] if sh else 0,
                      "no_captions": sorted(stats["nocap"]), "drift_fixed": len(stats["drift_fixed"]), "drift_eps": sorted({x[0] for x in stats["drift_fixed"]}), "drift_detail": sorted({x for x in stats["drift_fixed"]}),
                      "changed": [str(c.relative_to(REPO)) for c in changed]}, indent=1))
    return stats


if __name__ == "__main__":
    main()
