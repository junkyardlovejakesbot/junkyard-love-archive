#!/usr/bin/env python3
"""Quality-pass (b): complete-sentence Archive picks quotes for published episodes.

Updates only Archive picks Memorable quotes (source-archive-picks.md + episode HTML
archive-quote blockquotes). Leaves Jacob published About/Quotes text unchanged.
No git commit/push.
"""
from __future__ import annotations

import argparse
import html as html_lib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = Path(__file__).resolve().parent / "content"
EPISODES = ROOT / "episodes"

SOFT_ASR = {"0020", "0025", "0047", "0037"}
HOST_RE = re.compile(r"^(jacob|host)\b", re.I)
TURN_RE = re.compile(r"^\[(\d{2}):(\d{2}):(\d{2})\]\s+([^:\n]+):\s*(.*)$", re.M)
ARCHIVE_QUOTE_LINE = re.compile(
    r"^- \[(\d{2}):(\d{2}):(\d{2})\]\s+([^:]+):\s+[“\"](.+?)[”\"]\s*$"
)

BAD_END_WORDS = {
    "the", "a", "an", "to", "of", "and", "or", "but", "so", "like", "as",
    "my", "your", "our", "their", "his", "her", "with", "for", "from", "into",
    "onto", "at", "in", "on", "by", "is", "are", "was", "were", "be", "been",
    "being", "that", "this", "these", "those", "which", "who", "whom", "when",
    "what", "how", "if", "than", "then", "just", "also", "very", "really",
    "kind", "sort", "lot", "bit", "gonna", "wanna", "gotta", "um", "uh",
    "i", "you", "we", "they", "he", "she", "it", "me", "us", "them",
    "do", "does", "did", "have", "has", "had", "can", "could", "would",
    "should", "will", "about", "because", "while", "where", "there",
    "getting", "taking", "making", "going", "doing", "having", "wanting",
    "trying", "looking", "saying", "starting", "learning", "creating",
    "becoming", "putting", "giving", "coming", "keeping", "letting",
    "feeling", "thinking", "knowing", "seeing", "hearing", "talking",
    "speaking", "telling", "asking", "working", "living", "growing",
    "changing", "healing", "believing", "realizing", "listening",
    "teaching", "building", "finding", "needing", "helping", "loving",
    "using", "sharing", "bringing", "leaving", "moving", "turned",
    "started", "wanted", "needed", "tried", "taught", "learned", "got",
    "went", "came", "took", "made", "put", "let", "still", "even",
    "something", "anything", "everything", "nothing", "someone", "somebody",
    "around", "through", "over", "under", "between", "without", "within",
    "up", "out", "off", "down", "back", "away", "more", "most", "such",
    "some", "any", "other", "another", "own", "not", "no", "yes", "yeah",
    "brother", "dude", "man", "today", "right", "okay", "ok", "one",
    "stuff", "number", "first", "oh", "he", "did", "it's", "thats",
}

BAD_START_WORDS = {
    "and", "but", "or", "so", "because", "which", "who", "whom", "where",
    "when", "than", "that", "of", "to", "for", "with", "from", "into",
    "mm-hmm", "mm", "uh", "um", "yeah", "yep", "yup", "okay", "ok", "right",
    "exactly", "absolutely", "totally", "much", "well",
    "us", "me", "him", "them", "her", "his", "its", "doing", "hasn't",
    "can't", "don't", "didn't", "isn't", "wasn't", "weren't",
    "get", "got", "bad", "similarly", "just", "lot", "work", "thing",
    "things", "designs", "company",
}

FILLER_RE = re.compile(r"\b(?:uh|um|mm-?hmm|you know|i mean)\b", re.I)
VERB_RE = re.compile(
    r"\b(?:am|is|are|was|were|be|been|being|'m|'s|'re|'ve|'d|'ll|"
    r"do|does|did|doing|have|has|had|having|can|could|will|would|should|may|might|must|"
    r"get|got|getting|go|goes|went|going|make|makes|made|making|"
    r"take|takes|took|taking|want|wants|wanted|need|needs|needed|"
    r"know|knows|knew|think|thinks|thought|feel|feels|felt|"
    r"see|sees|saw|say|says|said|tell|tells|told|"
    r"create|creates|created|learn|learns|learned|"
    r"help|helps|helped|love|loves|loved|try|tries|tried|"
    r"work|works|worked|live|lives|lived|become|becomes|became|"
    r"grow|grows|grew|change|changes|changed|heal|heals|healed|"
    r"believe|believes|believed|realize|realizes|realized|"
    r"listen|listens|listened|hear|hears|heard|"
    r"start|starts|started|stop|stops|stopped|"
    r"put|puts|find|finds|found|give|gives|gave|"
    r"come|comes|came|keep|keeps|kept|let|lets|"
    r"mean|means|meant|choose|chooses|chose|chosen|"
    r"build|builds|built|teach|teaches|taught|"
    r"remember|remembered|forget|forgot|forgive|forgave|"
    r"plant|planted|open|opened|turn|turned|stay|stayed|"
    r"communicate|connect|connected|understand|understood|"
    r"prefer|suffer|suffered|fail|failed|succeed|win|won|lose|lost|"
    r"allow|allows|allowed|own|owns|owned|face|faced|"
    r"deal|dealt|shift|shifted|matter|matters)\b",
    re.I,
)
INSIGHT_RE = re.compile(
    r"\b(?:because|realize|realized|truth|learn|learned|lesson|practice|habit|"
    r"heal|healing|grow|growth|change|mindset|ego|fear|love|kindness|"
    r"listen|listening|compassion|vulnerable|vulnerability|courage|"
    r"discipline|consistency|vision|dream|purpose|meaning|identity|belief|"
    r"meditation|breath|nature|community|connection|forgiveness|gratitude|"
    r"resilience|empathy|create|creator|compound|diamond|garden|"
    r"responsibility|choice|choose|chosen|emergency|benevolence|educator|"
    r"insight|sobriety|trauma|depression|anxiety|relationship|marriage|"
    r"consciousness|spirit|soul|awareness|presence|patience|"
    r"accountability|humility|integrity|boundaries|permission|"
    r"cornerstone|communication|observation|signature|niceness)\b",
    re.I,
)
FLUFF_RE = re.compile(
    r"\b(?:welcome to (?:the )?junkyard|peace out|see you next|"
    r"thanks for (?:coming|being|listening|joining)|like and subscribe)\b",
    re.I,
)
STRONG_START_RE = re.compile(
    r"^(?:I|I'm|I've|I'd|I'll|You|You're|You've|We|We're|We've|"
    r"They|They're|He|She|It|It's|That's|There's|Here's|What's|"
    r"This|That|These|Those|The|A|An|My|Your|Our|Their|"
    r"Whatever|Whenever|Everyone|Everybody|Anyone|Anybody|Nobody|"
    r"Nothing|Something|Someone|People|Life|Love|Fear|Hope|Truth|"
    r"Music|Art|School|Work|Time|Change|Growth|Healing|Kindness|"
    r"Listening|Observation|Vulnerability|Ego|Meditation|Nature|"
    r"Realizing|Stop|Don't|Do|Be|Being|Become|Never|Always|Sometimes|"
    r"If|When|While|After|Before|Once|Maybe|Perhaps|Positive|Clear|"
    r"Operating|Chance|Morality|Laughter|Identify|Will|Can|Could|"
    r"Would|Should|Have|Had|One|Every|Each|All|Most|Many|Some|"
    r"Just|Only|Even|Still|Now|Yes|No|Thank|Thanks|Hello|Welcome|"
    r"Comparing|Am|There|In|On|Going|Own|Take|Taking|Living|"
    r"Planting|Taught|Teaching|Thinking|Keep|Keeping|Hard|It|"
    r"Kindness|Your|Meditation)\b"
)


@dataclass
class Quote:
    sec: int
    ts: str
    speaker: str
    text: str
    source: str
    score: float = 0.0


def fmt_ts(sec: int) -> str:
    return f"{sec // 3600:02d}:{(sec % 3600) // 60:02d}:{sec % 60:02d}"


def anchor_id(sec: int) -> str:
    return "t-" + fmt_ts(sec).replace(":", "-")


def episode_num(slug: str) -> str:
    m = re.match(r"^(\d{4})", slug)
    return m.group(1) if m else ""


def parse_turns(transcript: str) -> list[dict]:
    turns = []
    for m in TURN_RE.finditer(transcript):
        h, mi, s = int(m.group(1)), int(m.group(2)), int(m.group(3))
        turns.append(
            {
                "sec": h * 3600 + mi * 60 + s,
                "ts": f"{h:02d}:{mi:02d}:{s:02d}",
                "speaker": m.group(4).strip(),
                "text": m.group(5).strip(),
            }
        )
    return turns


def strip_attribution(q: str) -> str:
    q = re.sub(r"\s*[—–-]\s*[A-Z][^“”\"]{0,60}$", "", q).strip()
    return q.strip(" \"'“”")


def parse_published_quotes(path: Path) -> list[str]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    if not text or "none published" in text.lower():
        return []
    out = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        line = re.sub(r"^\s*[-*]\s*", "", line)
        q = strip_attribution(line.strip().strip("“”\"'"))
        q = re.sub(r"\s+", " ", q).strip()
        if len(q) >= 8:
            out.append(q)
    return out


def parse_archive_seeds(picks_path: Path) -> list[tuple[int, str, str]]:
    if not picks_path.exists():
        return []
    md = picks_path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"^## Memorable quotes\s*\n(.*?)(?=^## |\Z)", md, re.M | re.S)
    if not m:
        return []
    seeds = []
    for line in m.group(1).splitlines():
        mm = ARCHIVE_QUOTE_LINE.match(line.strip())
        if not mm:
            continue
        h, mi, s = int(mm.group(1)), int(mm.group(2)), int(mm.group(3))
        seeds.append((h * 3600 + mi * 60 + s, mm.group(4).strip(), mm.group(5).strip()))
    return seeds


def normalize_words(s: str) -> list[str]:
    s = s.lower().replace("'", "'").replace("'", "'").replace("'", "'")
    s = re.sub(r"[^a-z0-9'\s]+", " ", s)
    return [w for w in s.split() if w]


def last_word(text: str) -> str:
    words = re.findall(r"[A-Za-z0-9']+", text)
    return words[-1].lower() if words else ""


def first_word(text: str) -> str:
    words = re.findall(r"[A-Za-z0-9']+", text)
    return words[0].lower() if words else ""


def distinctive_words(words: list[str]) -> list[str]:
    stop = {
        "the", "a", "an", "and", "or", "but", "so", "to", "of", "in", "on", "for",
        "with", "at", "by", "from", "as", "is", "are", "was", "were", "be", "been",
        "being", "that", "this", "it", "its", "you", "your", "i", "my", "we", "our",
        "they", "their", "he", "she", "his", "her", "not", "no", "yes", "do", "does",
        "did", "have", "has", "had", "can", "could", "would", "should", "will", "just",
        "like", "really", "very", "about", "into", "what", "when", "where", "who",
        "how", "why", "if", "then", "than", "there", "here", "all", "some", "any",
        "more", "most", "other", "also", "only", "even", "still", "out", "up", "one",
        "get", "got", "go", "going", "know", "think", "thing", "things", "gonna",
    }
    return [w for w in words if len(w) >= 4 and w not in stop]


def looks_complete(text: str) -> bool:
    text = text.strip()
    if not text:
        return False
    words = text.split()
    nw = len(words)
    if nw < 6:
        if 3 <= nw <= 5 and text[0].isupper() and re.search(r"[.!?…]$", text):
            return last_word(text.rstrip(".!?…")) not in BAD_END_WORDS
        return False
    if nw > 55:
        return False
    if text[0].islower():
        return False
    if first_word(text) in BAD_START_WORDS:
        return False
    if last_word(text.rstrip(".!?…")) in BAD_END_WORDS:
        return False
    if not VERB_RE.search(text):
        return False
    if len(FILLER_RE.findall(text)) >= 3:
        return False
    if FLUFF_RE.search(text):
        return False
    # reject "I still." / "what I." style pronoun-heavy stubs
    if re.search(r"\b(?:what|about|as|than|because)\s+I[.!?]?$", text, re.I):
        return False
    lw = last_word(text.rstrip(".!?…"))
    if len(lw) <= 1 and lw not in {"i", "a"}:
        return False
    # reject obvious truncation tails like "yourself l" / "things these"
    if re.search(r"\b(?:these|those|this|that)\s+things?[.!?]?$", text, re.I):
        # allow "these things matter" style only if verb after — already ended
        if not VERB_RE.search(text.split()[-3] if len(text.split())>=3 else ""):
            pass
    # too many filler commas / dashes from ASR mash
    if text.count("“") != text.count("”"):
        return False
    if text.count(" - ") >= 2:
        return False
    if len(re.findall(r"\b(?:okay|ok|right|yeah|you know|i mean|like)\b", text, re.I)) >= 3:
        return False
    return True


def is_complete_published(q: str) -> bool:
    q = strip_attribution(q).strip()
    words = q.split()
    if len(words) < 4:
        return False
    if q[0].islower() and not re.search(r"[.!?…]$", q):
        return False
    lw = last_word(q.rstrip(".!?…,"))
    if lw in BAD_END_WORDS and not re.search(r"[.!?…]$", q):
        return False
    if q.endswith("...") and len(words) < 8:
        return False
    return len(words) <= 60 and (q[0].isupper() or q[0] in "\"“'")


def polish_sentence(text: str) -> str:
    t = re.sub(r"\s+", " ", text).strip(" \"'“”«»")
    for _ in range(5):
        fw = first_word(t)
        if fw in BAD_START_WORDS or fw in {"well", "like", "actually", "basically", "literally", "honestly"}:
            t2 = re.sub(r"^[^\s]+\s+", "", t).strip(" ,;")
            if len(t2.split()) < 6:
                break
            t = t2
        else:
            break
    for _ in range(8):
        core = t.rstrip(".!?…,;:—–- ")
        lw = last_word(core)
        if lw in BAD_END_WORDS:
            parts = core.split()
            if len(parts) < 7:
                break
            t = " ".join(parts[:-1])
        else:
            t = core
            break
    if not t:
        return ""
    chars = list(t)
    for i, ch in enumerate(chars):
        if ch.isalpha():
            chars[i] = ch.upper()
            break
    t = "".join(chars)
    if not re.search(r"[.!?…]$", t):
        t = t.rstrip(",;: ") + "."
    t = re.sub(r"\s+([,.!?])", r"\1", t)
    return re.sub(r"\s+", " ", t).strip()


def extract_spans(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    cands: list[str] = []
    if re.search(r"[.!?]", text):
        for p in re.split(r"(?<=[.!?])\s+", text):
            p = p.strip()
            if 6 <= len(p.split()) <= 45:
                cands.append(p)
    words = text.split()
    n = len(words)
    if n < 6:
        return cands
    start_idxs = []
    for i, w in enumerate(words):
        ww = w.lstrip("\"'“")
        if STRONG_START_RE.match(ww) or (i == 0 and ww[:1].isupper()):
            start_idxs.append(i)
    if not start_idxs:
        start_idxs = [0]
    for i in start_idxs:
        for L in (10, 12, 14, 16, 18, 20, 22, 24, 28):
            if i + L > n:
                continue
            span = " ".join(words[i : i + L])
            if last_word(span) in BAD_END_WORDS:
                continue
            if first_word(span) in BAD_START_WORDS:
                continue
            if not VERB_RE.search(span):
                continue
            if len(FILLER_RE.findall(span)) >= 3:
                continue
            cands.append(span)
    for m in INSIGHT_RE.finditer(text):
        wi = len(text[: m.start()].split())
        for back in (3, 5, 7):
            for forward in (8, 10, 12, 14):
                a = max(0, wi - back)
                b = min(n, wi + forward)
                if b - a < 8:
                    continue
                span = " ".join(words[a:b])
                if last_word(span) in BAD_END_WORDS or first_word(span) in BAD_START_WORDS:
                    continue
                if VERB_RE.search(span):
                    cands.append(span)
    seen = set()
    out = []
    for c in cands:
        key = c.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(c)
    return out


def score_quote(text: str, speaker: str, sec: int, duration: int, source: str) -> float:
    words = text.split()
    nw = len(words)
    score = 0.0
    if 10 <= nw <= 26:
        score += 3.5
    elif 8 <= nw <= 34:
        score += 2.0
    elif 6 <= nw <= 45:
        score += 0.8
    else:
        score -= 2.0
    if VERB_RE.search(text):
        score += 1.2
    if INSIGHT_RE.search(text):
        score += 2.2
    if FLUFF_RE.search(text):
        score -= 4.0
    if re.search(r"[.!?…]$", text):
        score += 0.8
    if text[:1].isupper():
        score += 0.5
    if HOST_RE.match(speaker.strip()):
        score -= 1.0
    else:
        score += 1.4
    if duration > 0:
        frac = sec / duration
        if 0.04 <= frac <= 0.93:
            score += 0.7
        if frac < 0.015 or frac > 0.98:
            score -= 2.0
    if source == "published":
        score += 5.0
    score -= 0.5 * len(FILLER_RE.findall(text))
    return score


def similar(a: str, b: str) -> bool:
    wa, wb = set(normalize_words(a)), set(normalize_words(b))
    if not wa or not wb:
        return False
    inter = len(wa & wb)
    return inter / min(len(wa), len(wb)) >= 0.7 or inter / max(len(wa), len(wb)) >= 0.55


def find_published_in_transcript(q: str, turns: list[dict]) -> Quote | None:
    q_words = normalize_words(q)
    if len(q_words) < 4:
        return None
    needle = q_words[: min(12, len(q_words))]
    dist = distinctive_words(q_words) or [w for w in q_words if len(w) >= 4][:8]
    best = None
    best_score = 0.0
    for t in turns:
        tw = normalize_words(t["text"])
        if len(tw) < 3:
            continue
        tw_set = set(tw)
        idx = 0
        for w in tw:
            if idx < len(needle) and w == needle[idx]:
                idx += 1
        ordered = idx / len(needle)
        bag = len(set(needle) & tw_set) / max(len(set(needle)), 1)
        dhit = len(set(dist) & tw_set) / max(len(set(dist)), 1)
        sc = ordered * 2.0 + bag + dhit * 2.5
        if ordered >= 0.55 or dhit >= 0.45 or (bag >= 0.55 and dhit >= 0.3):
            if sc > best_score:
                best_score = sc
                best = t
    if not best:
        for i, t in enumerate(turns):
            joined: list[str] = []
            for j in range(i, min(i + 6, len(turns))):
                joined.extend(normalize_words(turns[j]["text"]))
            dhit = len(set(dist) & set(joined)) / max(len(set(dist)), 1)
            if dhit >= 0.5:
                best = t
                best_score = dhit
                break
    if not best:
        return None
    text_q = q.strip()
    if not re.search(r"[.!?…]$", text_q):
        text_q = text_q.rstrip(",; ") + "."
    return Quote(
        sec=best["sec"],
        ts=best["ts"],
        speaker=best["speaker"].split()[0],
        text=text_q,
        source="published",
        score=best_score + 5,
    )


def select_quotes(
    turns: list[dict],
    published: list[str],
    soft: bool,
    seeds: list[tuple[int, str, str]] | None = None,
) -> list[Quote]:
    duration = turns[-1]["sec"] if turns else 0
    selected: list[Quote] = []

    for pq in published:
        if not is_complete_published(pq):
            continue
        hit = find_published_in_transcript(pq, turns)
        if not hit:
            continue
        hit.score = score_quote(hit.text, hit.speaker, hit.sec, duration, "published")
        if not any(similar(hit.text, s.text) for s in selected):
            selected.append(hit)
        if len(selected) >= 8:
            break

    # Build seed boost map: sec -> scrap words
    seed_boost: dict[int, set[str]] = {}
    if seeds:
        for sec, _speaker, scrap in seeds:
            seed_boost[sec] = set(normalize_words(scrap))

    cands: list[Quote] = []
    for t in turns:
        # skip pure intro fluff window unless published already filled
        if t["sec"] < 45 and not any(abs(t["sec"] - s.sec) < 5 for s in selected if s.source == "published"):
            # still allow insight lines
            pass
        for span in extract_spans(t["text"]):
            polished = polish_sentence(span)
            if not looks_complete(polished):
                continue
            # reject ASR capital-glitch density (e.g. "Was females")
            caps = len(re.findall(r"\b[A-Z][a-z]+\b", polished))
            # first word capital is fine; many mid-sentence Title Case tokens are ASR artifacts
            mid_caps = caps - (1 if polished[:1].isupper() else 0)
            if mid_caps >= 3 and not soft:
                # allow if looks like normal punctuated prose with names
                if not re.search(r"[.!?]", span):
                    continue
            if soft:
                sw = set(normalize_words(span))
                pw = set(normalize_words(polished))
                if pw and len(pw - sw) / max(len(pw), 1) > 0.15:
                    continue
            sc = score_quote(polished, t["speaker"], t["sec"], duration, "transcript")
            # boost near prior archive-pick timestamps
            for ssec, scrap_w in seed_boost.items():
                if abs(ssec - t["sec"]) <= 35:
                    sc += 1.2
                    if scrap_w:
                        ov = len(scrap_w & set(normalize_words(polished))) / max(len(scrap_w), 1)
                        sc += ov * 2.0
                    break
            # early ASR: require insight cue
            if soft or t["sec"] < 120:
                if not INSIGHT_RE.search(polished) and sc < 6.0:
                    continue
            if not INSIGHT_RE.search(polished) and sc < 4.5:
                continue
            if sc < 3.5:
                continue
            if t["sec"] < 40 and not INSIGHT_RE.search(polished):
                continue
            cands.append(
                Quote(t["sec"], t["ts"], t["speaker"].split()[0], polished, "transcript", sc)
            )
    cands.sort(key=lambda q: q.score, reverse=True)

    def bucket(sec: int) -> int:
        return int((sec / max(duration, 1)) * 8) if duration else 0

    used_b: dict[int, int] = {}
    for c in cands:
        if len(selected) >= 8:
            break
        if any(similar(c.text, s.text) for s in selected):
            continue
        b = bucket(c.sec)
        if used_b.get(b, 0) >= 2 and len(selected) >= 4:
            continue
        selected.append(c)
        used_b[b] = used_b.get(b, 0) + 1

    if len(selected) < 4:
        for c in cands:
            if len(selected) >= 4:
                break
            if any(similar(c.text, s.text) for s in selected):
                continue
            selected.append(c)

    if len(selected) < 4:
        for t in turns:
            if HOST_RE.match(t["speaker"]):
                continue
            for span in extract_spans(t["text"])[:5]:
                polished = polish_sentence(span)
                if looks_complete(polished) and not any(similar(polished, s.text) for s in selected):
                    selected.append(
                        Quote(
                            t["sec"],
                            t["ts"],
                            t["speaker"].split()[0],
                            polished,
                            "transcript",
                            score_quote(polished, t["speaker"], t["sec"], duration, "transcript"),
                        )
                    )
                    break
            if len(selected) >= 4:
                break

    if len(selected) > 8:
        selected.sort(key=lambda q: q.score, reverse=True)
        kept = []
        used_b = {}
        for c in selected:
            if len(kept) >= 8:
                break
            b = bucket(c.sec)
            if used_b.get(b, 0) >= 2 and len(kept) >= 4:
                continue
            kept.append(c)
            used_b[b] = used_b.get(b, 0) + 1
        selected = kept

    # final completeness filter
    selected = [q for q in selected if looks_complete(q.text) or q.source == "published"]
    selected.sort(key=lambda q: q.sec)
    return selected[:8]



def sanitize_quote_text(text: str) -> str:
    """Avoid nested curly doubles that break HTML/MD quote delimiters."""
    # Replace inner curly doubles with singles; keep apostrophes.
    text = text.replace("“", "‘").replace("”", "’")
    return text

def replace_md_quotes(md: str, quotes: list[Quote]) -> str:
    lines = [f'- [{q.ts}] {q.speaker}: “{sanitize_quote_text(q.text)}”' for q in quotes]
    block = "## Memorable quotes\n\n" + "\n".join(lines) + "\n"
    if re.search(r"^## Memorable quotes\s*$", md, re.M):
        return re.sub(
            r"^## Memorable quotes\s*\n(?:.*?\n)*?(?=^## |\Z)",
            block + "\n",
            md,
            count=1,
            flags=re.M,
        )
    if re.search(r"^## Chapter-style timestamps", md, re.M):
        return re.sub(
            r"^## Chapter-style timestamps",
            block + "\n## Chapter-style timestamps",
            md,
            count=1,
            flags=re.M,
        )
    return md.rstrip() + "\n\n" + block


def replace_html_archive_quotes(html: str, quotes: list[Quote]) -> str:
    parts = []
    for q in quotes:
        parts.append(
            f'<blockquote class="archive-quote"><a class="ts" href="#{anchor_id(q.sec)}">[{q.ts}]</a> '
            f'<span class="speaker">{html_lib.escape(q.speaker)}:</span> '
            f"“{html_lib.escape(sanitize_quote_text(q.text))}”</blockquote>"
        )
    new_block = "\n".join(parts)
    pattern = re.compile(r"(<h3>Memorable quotes</h3>\s*)(.*?)(\s*<h3>)", re.S)
    m = pattern.search(html)
    if m:
        return html[: m.start(2)] + new_block + html[m.end(2) :]
    pattern2 = re.compile(r"(<h3>Memorable quotes</h3>\s*)(.*?)(\s*</div>)", re.S)
    m2 = pattern2.search(html)
    if m2:
        return html[: m2.start(2)] + new_block + html[m2.end(2) :]
    return html


def map_content_to_episode() -> dict[str, Path]:
    by_num: dict[str, Path] = {}
    for d in EPISODES.iterdir():
        if not d.is_dir() or "removed" in d.name:
            continue
        n = episode_num(d.name)
        if n and (d / "index.html").exists():
            by_num[n] = d
    return by_num


def process_episode(content_dir: Path, ep_dir: Path, dry_run: bool = False) -> dict:
    num = episode_num(content_dir.name)
    soft = num in SOFT_ASR
    tp = content_dir / "transcript.md"
    if not tp.exists():
        return {"num": num, "status": "skip", "reason": "no transcript"}
    turns = parse_turns(tp.read_text(encoding="utf-8", errors="replace"))
    if not turns:
        return {"num": num, "status": "skip", "reason": "empty turns"}
    published = parse_published_quotes(content_dir / "source-quotes.md")
    seeds = parse_archive_seeds(content_dir / "source-archive-picks.md")
    quotes = select_quotes(turns, published, soft=soft, seeds=seeds)

    result = {
        "num": num,
        "status": "ok",
        "n_quotes": len(quotes),
        "n_published_used": sum(1 for q in quotes if q.source == "published"),
        "soft": soft,
        "samples": [q.text for q in quotes],
    }
    if dry_run:
        return result

    picks_path = content_dir / "source-archive-picks.md"
    html_path = ep_dir / "index.html"
    if picks_path.exists():
        md = picks_path.read_text(encoding="utf-8", errors="replace")
        picks_path.write_text(replace_md_quotes(md, quotes), encoding="utf-8")
    else:
        body = (
            "# Archive picks (not from published notes)\n\n"
            "Extracted from the transcript and published About quotes already on this episode. "
            "Labeled separately from Jacob’s published About / Chapters / Quotes / Hashtags.\n\n"
        )
        picks_path.write_text(replace_md_quotes(body, quotes), encoding="utf-8")

    html = html_path.read_text(encoding="utf-8", errors="replace")
    html2 = replace_html_archive_quotes(html, quotes)
    if "<!-- topic-chips:start -->" in html and "<!-- topic-chips:start -->" not in html2:
        raise RuntimeError(f"{num}: topic chips lost")
    if 'class="browse-subtitle"' in html and 'class="browse-subtitle"' not in html2:
        raise RuntimeError(f"{num}: browse-subtitle lost")
    if "data-theme" in html and "data-theme" not in html2:
        raise RuntimeError(f"{num}: theme hook lost")
    html_path.write_text(html2, encoding="utf-8")
    return result


def count_archive_frags(ep_dir: Path) -> tuple[int, int]:
    html = (ep_dir / "index.html").read_text(encoding="utf-8", errors="replace")
    frag = ok = 0
    for m in re.finditer(r'<blockquote class="archive-quote">.*?</blockquote>', html, re.S):
        qm = re.search(r"[“](.+?)[”]", m.group(0), re.S)
        if not qm:
            continue
        q = html_lib.unescape(qm.group(1)).strip()
        words = q.split()
        has_end = bool(re.search(r"[.!?…]$", q))
        bad = (
            (bool(q) and q[0].islower())
            or (len(words) < 8 and not has_end)
            or (last_word(q.rstrip(".!?")) in BAD_END_WORDS)
            or not has_end
        )
        if bad:
            frag += 1
        else:
            ok += 1
    return frag, ok


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--batch", type=int)
    ap.add_argument("--report", default="")
    args = ap.parse_args()

    ep_map = map_content_to_episode()
    content_dirs = sorted(
        [
            d
            for d in CONTENT.iterdir()
            if d.is_dir() and re.match(r"^\d{4}-", d.name) and "removed" not in d.name
        ],
        key=lambda p: episode_num(p.name),
    )

    results = []
    before_frag = before_ok = after_frag = after_ok = 0

    for cd in content_dirs:
        num = episode_num(cd.name)
        if args.only and num not in args.only:
            continue
        if args.batch is not None and not (args.batch <= int(num) < args.batch + 10):
            continue
        ep = ep_map.get(num)
        if not ep:
            results.append({"num": num, "status": "skip", "reason": "no episode dir"})
            continue
        if not args.dry_run:
            f, o = count_archive_frags(ep)
            before_frag += f
            before_ok += o
        try:
            r = process_episode(cd, ep, dry_run=args.dry_run)
        except Exception as e:
            r = {"num": num, "status": "error", "reason": str(e)}
        results.append(r)
        if not args.dry_run and r.get("status") == "ok":
            f, o = count_archive_frags(ep)
            after_frag += f
            after_ok += o
        samples = r.get("samples") or []
        preview = " | ".join(s[:64] for s in samples[:3])
        print(
            f"{num} {r.get('status')} n={r.get('n_quotes')} pub={r.get('n_published_used')} "
            f"soft={r.get('soft')} :: {preview}",
            flush=True,
        )

    summary = {
        "episodes_processed": sum(1 for r in results if r.get("status") == "ok"),
        "episodes_skipped": sum(1 for r in results if r.get("status") == "skip"),
        "episodes_error": sum(1 for r in results if r.get("status") == "error"),
        "before_frag": before_frag,
        "before_ok": before_ok,
        "after_frag": after_frag,
        "after_ok": after_ok,
        "results": results,
    }
    print("SUMMARY", json.dumps({k: v for k, v in summary.items() if k != "results"}, indent=2))
    if args.report:
        Path(args.report).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return 0 if summary["episodes_error"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
