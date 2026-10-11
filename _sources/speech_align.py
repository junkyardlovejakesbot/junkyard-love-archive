"""Speech-aligned play starts (archive standard).

play_start(folder, published_seconds) -> (seconds:int, kind:str, detail:str)

Sources, in order: YouTube json3 (word-level), YouTube vtt, Transistor/other
SRT, transcript.md [HH:MM:SS] Name: turns. Rules:
  * prefer the latest speaker-turn start in [published-30s, published]
    ('>>' in YouTube captions, 'Name:' in SRT / transcript.md)
    if that turn began within 10s; inside a longer monologue use the latest
    sentence start (still never before the turn)
  * a mark that falls just before an answer (turn within 1.5s after) whose
    preceding turn ends in '?' starts at that question turn
  * else the latest sentence start (word after . ? !) in that window
  * else the start of the caption line containing the published time
  * a turn that starts within 1.5s AFTER the published time counts as "on time":
    keep published (never move later)
  * never later than published, never earlier than 30s, floor to whole seconds
  * no captions -> keep published
"""
import json, math, re, glob
from functools import lru_cache
from pathlib import Path

LOOKBACK = 30
TURN_NEAR = 10  # a mid-monologue mark further than this from the turn start snaps to the sentence start
HERE = Path(__file__).resolve().parent
CONTENT = HERE / "content"
END_P = re.compile(r"[.?!][\"')\]]*$")


def _json3_words(path):
    d = json.loads(Path(path).read_text())
    words, prev_end = [], False
    for ev in d.get("events", []):
        t0 = ev.get("tStartMs", 0)
        for s in ev.get("segs") or []:
            w = s.get("utf8", "")
            if not w.strip():
                continue
            t = (t0 + (s.get("tOffsetMs") or 0)) / 1000
            turn = ">>" in w
            words.append((t, w.replace(">>", "").strip(), turn, turn or prev_end or not words, s.get("tOffsetMs") is None))
            prev_end = bool(END_P.search(w.strip()))
    return words


def _ts(h, m, s, frac="0"):
    return int(h) * 3600 + int(m) * 60 + int(s) + float("0." + frac)


def _cue_file(path):
    txt = Path(path).read_text(errors="ignore")
    out, spk, prev_end = [], None, True
    for m in re.finditer(r"(\d+):(\d\d):(\d\d)[.,](\d+) -->[^\n]*\n(.+?)(?:\n\s*\n|\Z)", txt, re.S):
        h, mi, s, fr, body = m.groups()
        body = re.sub(r"<[^>]+>", "", body).strip()
        if not body:
            continue
        t = _ts(h, mi, s, fr)
        nm = re.match(r"^([A-Z][\w.' -]{0,30}):\s", body)
        turn = body.startswith(">>") or bool(nm and nm.group(1) != spk)
        if nm:
            spk = nm.group(1)
        out.append((t, body, turn, turn or prev_end, True))
        prev_end = bool(END_P.search(body))
    return out


def _md_turns(path):
    out, spk = [], None
    for m in re.finditer(r"^\[(\d\d):(\d\d):(\d\d)\]\s*([^:\n]{1,40}):\s*(.*)$", Path(path).read_text(errors="ignore"), re.M):
        nm = m.group(4).strip()
        out.append((_ts(*m.groups()[:3]), nm + ": " + m.group(5), nm != spk, True, True))
        spk = nm
    return out


@lru_cache(maxsize=None)
def source(folder):
    """-> (kind, tokens) tokens: (t, text, is_turn, is_sentence_start)"""
    f = Path(folder)
    if not f.is_absolute():
        f = CONTENT / folder
    best = None
    for j in sorted(f.rglob("*.json3")):
        try:
            w = _json3_words(j)
        except Exception:
            continue
        if w and (best is None or (sum(x[2] for x in w), len(w)) > (sum(x[2] for x in best), len(best))):
            best = w
    if best:
        # auto captions without punctuation: a pause (>=1.2s between word
        # starts) marks a phrase start. transcript.md turns are NOT used here:
        # on older episodes they are heuristic splits, often mid-sentence.
        if sum(1 for x in best if END_P.search(x[1])) < len(best) / 200:
            best = [(t, w, turn, ss or (i > 0 and t - best[i - 1][0] >= 1.2), ln)
                    for i, (t, w, turn, ss, ln) in enumerate(best)]
        return "yt-json3", tuple(best)
    for v in sorted(f.rglob("*.vtt")):
        c = _cue_file(v)
        if c:
            return "yt-vtt", tuple(c)
    for s in sorted(f.rglob("*.srt")):
        c = _cue_file(s)
        if c:
            return "srt", tuple(c)
    md = f / "transcript.md"
    if md.exists():
        c = _md_turns(md)
        if c:
            return "transcript-md", tuple(c)
    return "none", ()


def play_start(folder, published, lookback=LOOKBACK):
    published = float(published)
    kind, tok = source(folder)
    if not tok:
        return int(published), "none", "no captions; kept published"
    lo = published - lookback
    # on time: a turn begins within 1.5s after the mark
    nxt = [i for i, x in enumerate(tok) if published <= x[0] <= published + 1.5 and x[2]]
    if nxt:
        i = nxt[0]
        prevturns = [j for j in range(i) if tok[j][2] and tok[j][0] >= lo]
        last = tok[i - 1][1].strip() if i else ""
        if prevturns and last.endswith("?"):
            t = tok[prevturns[-1]][0]
            return max(int(math.floor(t)), 0), "question", f"{kind} answer at mark; question turn at {t:.2f}s"
        return int(math.floor(published)), "on-time", "turn starts at mark"
    if any(published <= x[0] < published + 1.0 and x[3] for x in tok):
        return int(math.floor(published)), "on-time", "sentence starts at mark"
    turns = [t for t, _, turn, *_ in tok if lo <= t <= published and turn]
    sents = [t for t, _, _, ss, *_ in tok if lo <= t <= published and ss]
    if turns and (max(turns) >= published - TURN_NEAR or not sents or max(sents) <= max(turns)):
        t = max(turns); why = "turn"
    elif sents:
        t = max(sents); why = "sentence"
    else:
        prior = [x[0] for x in tok if lo <= x[0] <= published and x[4]] or [x[0] for x in tok if lo <= x[0] <= published]
        if not prior:
            return int(math.floor(published)), "kept", "no token in window"
        t = max(prior); why = "line"
    s = max(int(math.floor(t)), int(math.ceil(lo)) if lo > 0 else 0)
    s = min(s, int(math.floor(published)))
    return s, why, f"{kind} {why} at {t:.2f}s"


def words_at(folder, seconds, n=12):
    kind, tok = source(folder)
    ws = [x for x in tok if x[0] >= seconds][:n]
    return " ".join(("‖" if x[2] else "") + x[1] for x in ws)


def folder_for(slug):
    p = CONTENT / slug
    if p.exists():
        return p
    num = slug[:4]
    g = sorted(CONTENT.glob(num + "-*"))
    if g:
        return g[0]
    # un-numbered content folders (e.g. sean-blackwell-mania-is-a-message):
    # require the guest-name tokens (first two words of the folder) in the slug
    toks = set(slug.split("-"))
    for d in sorted(CONTENT.iterdir()):
        if d.is_dir() and not d.name[:4].isdigit():
            name = d.name.split("-")[:2]
            if all(n in toks for n in name):
                return d
    return None


def published_chapters(repo, slug):
    """Published chapter clock from the episode page chapter list -> {title: seconds}."""
    import html as H
    p = Path(repo) / "episodes" / slug / "index.html"
    if not p.exists():
        return {}
    out = {}
    for m in re.finditer(r'<a href="#t-[\d-]+">(\d\d):(\d\d):(\d\d)</a> — (.*?)</li>', p.read_text()):
        out.setdefault(H.unescape(m.group(4)).strip(), _ts(*m.groups()[:3]))
    return out


def anchors(repo, slug):
    p = Path(repo) / "episodes" / slug / "index.html"
    if not p.exists():
        return []
    return sorted({_ts(*a.split("-")) for a in re.findall(r'id="t-(\d\d-\d\d-\d\d)"', p.read_text())})


def hms(s):
    s = int(s); return f"{s//3600:02d}:{s%3600//60:02d}:{s%60:02d}"
