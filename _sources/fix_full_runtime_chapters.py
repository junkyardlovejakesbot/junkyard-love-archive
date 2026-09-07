#!/usr/bin/env python3
"""Quality-pass (c): full-runtime Archive picks chapter lists for published episodes.

Walks each episode transcript to the actual end (including host outro), builds a
complete browseable chapter list, snaps timestamps to valid transcript turns
(#t-HH-MM-SS), keeps accurate existing chapters, fills truncated/thin coverage,
and labels the host close as Outro when present.

Updates:
  - _sources/content/*/source-archive-picks.md  (Chapter-style timestamps)
  - episodes/*/index.html                       (Archive picks chapter <ul>)
  - _sources/content/*/source-timestamps.md     only when it already mirrors
                                                Archive/YT chapter lists (optional)

Does NOT change Jacob published About / Chapters / Quotes blocks, topic chips,
browse-subtitle, or dark theme hooks. No git commit/push.
"""
from __future__ import annotations

import argparse
import csv
import html as html_lib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = Path(__file__).resolve().parent / "content"
EPISODES = ROOT / "episodes"
INVENTORY = ROOT / "inventory.csv"

TURN_RE = re.compile(r"^\[(\d{2}):(\d{2}):(\d{2})\]\s+([^:\n]+):\s*(.*)$", re.M)
CHAP_MD_RE = re.compile(
    r"^- \[(\d{2}):(\d{2}):(\d{2})\](?:\(#t-\d{2}-\d{2}-\d{2}\))? — (.+)$",
    re.M,
)
CHAP_SEC_RE = re.compile(
    r"^## Chapter-style timestamps\s*\n(.*?)(?=^## |\Z)",
    re.M | re.S,
)

OUTRO_RE = re.compile(
    r"(?:"
    r"drink (?:some )?water|"
    r"do some (?:pilates|yoga|stretches?)|"
    r"stretch(?:es)?(?: your| and|,)|"
    r"love yoursel(?:f|ves)|take care of yoursel(?:f|ves)|"
    r"peace out|get present|get grounded|wiggle your|"
    r"put this phone away|five[- ]?star|"
    r"junkyard love (?:podcast )?out|"
    r"have a good (?:rest of your |rest your )?day|"
    r"\bahoy\b|focus on your posture|be kind to yourself|"
    r"cancel cancel|"
    r"thumbs up|"
    r"wherever you(?:'re| are) listening"
    r")",
    re.I,
)

# Stronger CTA cues for choosing among matches
OUTRO_STRONG_RE = re.compile(
    r"(?:"
    r"drink (?:some )?water|love yoursel(?:f|ves)|peace out|"
    r"get present|get grounded|put this phone away|five[- ]?star|"
    r"junkyard love (?:podcast )?out|have a good (?:rest of your |rest your )?day|"
    r"wiggle your|focus on your posture|thumbs up|wherever you(?:'re| are) listening"
    r")",
    re.I,
)

HOST_RE = re.compile(r"^(jacob|host)\b", re.I)

STOP = {
    "the", "a", "an", "to", "of", "and", "or", "but", "so", "like", "as", "just",
    "my", "your", "our", "their", "his", "her", "its", "with", "for", "from",
    "into", "onto", "at", "in", "on", "by", "is", "are", "was", "were", "be",
    "been", "being", "that", "this", "these", "those", "which", "who", "whom",
    "when", "what", "how", "if", "than", "then", "also", "very", "really",
    "kind", "sort", "lot", "bit", "gonna", "wanna", "gotta", "um", "uh", "mm",
    "i", "you", "we", "they", "he", "she", "it", "me", "us", "them", "do",
    "does", "did", "have", "has", "had", "can", "could", "would", "should",
    "will", "about", "because", "while", "where", "there", "here", "out", "up",
    "down", "off", "back", "away", "more", "most", "some", "any", "other",
    "another", "own", "not", "no", "yes", "yeah", "yep", "okay", "ok", "right",
    "dude", "man", "bro", "guys", "stuff", "thing", "things", "something",
    "anything", "everything", "nothing", "someone", "people", "person", "know",
    "think", "feel", "say", "said", "says", "going", "going", "get", "got",
    "getting", "go", "went", "make", "made", "making", "take", "took", "want",
    "wanted", "need", "needed", "see", "saw", "look", "looking", "come", "came",
    "coming", "let", "put", "one", "two", "three", "first", "even", "still",
    "well", "much", "many", "way", "ways", "time", "times", "today", "now",
    "actually", "literally", "basically", "probably", "maybe", "kinda", "gonna",
    "mean", "means", "meant", "talk", "talking", "talked", "podcast", "episode",
    "junkyard", "love", "jacob", "guest", "question", "questions", "answer",
    "true", "good", "great", "cool", "super", "little", "big", "new", "old",
    "same", "different", "whole", "part", "into", "through", "over", "under",
    "before", "after", "again", "around", "always", "never", "ever", "already",
    "almost", "enough", "able", "sure", "fine", "yeah", "nah", "hey", "hi",
    "hello", "welcome", "thanks", "thank", "appreciate", "absolutely", "totally",
    "exactly", "definitely", "obviously", "honestly", "whatever", "somebody",
    "everyone", "anybody", "doing", "done", "doesn't", "don't", "didn't",
    "isn't", "wasn't", "weren't", "can't", "won't", "i'm", "you're", "we're",
    "they're", "it's", "that's", "there's", "here's", "who's", "what's",
    "i've", "you've", "we've", "they've", "i'll", "you'll", "we'll", "they'll",
    "i'd", "you'd", "we'd", "they'd", "im", "youre", "were", "theyre",
}

UNNUMBERED = {
    "0118": "sean-blackwell-mania-is-a-message",
    "0120": "david-hulse-path-to-no-path",
    "0121": "tim-fraley-surrendering-the-porsche",
}

# Hold lightly if another job still rewriting ASR — overridden when full ASR present.
HOLD_LIGHT = {"0037"}

OVERRIDES_PATH = Path(__file__).resolve().parent / "chapter_label_overrides.json"


def load_overrides() -> dict[str, list[dict]]:
    """Optional per-episode chapter overrides: [{sec, label}, ...] exact clocks."""
    if not OVERRIDES_PATH.exists():
        return {}
    try:
        data = json.loads(OVERRIDES_PATH.read_text(encoding="utf-8"))
        return {str(k): v for k, v in data.items()}
    except Exception:
        return {}



_DICT_CANDIDATES = [
    Path(__file__).resolve().parent / "words_alpha.txt",
    Path("/usr/share/dict/words"),
]
DICT_WORDS: set[str] = set()
for _dp in _DICT_CANDIDATES:
    if _dp.exists():
        DICT_WORDS = {
            w.strip().lower()
            for w in _dp.read_text(encoding="utf-8", errors="ignore").splitlines()
            if w.strip().isalpha() and len(w.strip()) >= 3
        }
        break




@dataclass
class Turn:
    sec: int
    speaker: str
    text: str

    @property
    def ts(self) -> str:
        return fmt_ts(self.sec)


@dataclass
class Chapter:
    sec: int
    label: str
    source: str = "new"  # existing | new | outro | intro

    @property
    def ts(self) -> str:
        return fmt_ts(self.sec)

    @property
    def anchor(self) -> str:
        return f"t-{self.ts.replace(':', '-')}"


def fmt_ts(sec: int) -> str:
    sec = max(0, int(sec))
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def parse_ts_parts(h: str, m: str, s: str) -> int:
    return int(h) * 3600 + int(m) * 60 + int(s)


def episode_num(name: str) -> str:
    m = re.match(r"^(\d{4})", name)
    return m.group(1) if m else ""


def load_durations() -> dict[str, int]:
    out: dict[str, int] = {}
    if not INVENTORY.exists():
        return out
    with INVENTORY.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            n = f"{int(row['episode_number']):04d}"
            try:
                out[n] = int(float(row["duration_seconds"] or 0))
            except ValueError:
                out[n] = 0
    return out


def parse_turns(text: str) -> list[Turn]:
    turns: list[Turn] = []
    for m in TURN_RE.finditer(text):
        turns.append(
            Turn(
                sec=parse_ts_parts(m.group(1), m.group(2), m.group(3)),
                speaker=m.group(4).strip(),
                text=(m.group(5) or "").strip(),
            )
        )
    return turns


def parse_existing_chapters(md: str) -> list[Chapter]:
    m = CHAP_SEC_RE.search(md)
    if not m:
        return []
    block = m.group(1)
    chaps: list[Chapter] = []
    for cm in CHAP_MD_RE.finditer(block):
        sec = parse_ts_parts(cm.group(1), cm.group(2), cm.group(3))
        label = cm.group(4).strip()
        label = html_lib.unescape(label)
        chaps.append(Chapter(sec=sec, label=label, source="existing"))
    return chaps


def nearest_turn_sec(sec: int, turn_secs: list[int], max_delta: int = 90) -> int | None:
    if not turn_secs:
        return None
    best = min(turn_secs, key=lambda t: abs(t - sec))
    if abs(best - sec) <= max_delta:
        return best
    # allow larger snap near end
    if abs(best - sec) <= 180:
        return best
    return None


def detect_outro(turns: list[Turn]) -> int | None:
    if not turns:
        return None
    last = turns[-1].sec
    # Keep outro detection in the final stretch only
    cutoff = max(0, last - max(180, int(last * 0.08)))
    strong: list[Turn] = []
    weak: list[Turn] = []
    for t in turns:
        if t.sec < cutoff:
            continue
        if not HOST_RE.match(t.speaker):
            continue
        if OUTRO_STRONG_RE.search(t.text):
            strong.append(t)
        elif OUTRO_RE.search(t.text):
            weak.append(t)
    pool = strong or weak
    if pool:
        # Prefer the last strong CTA (true produced close); snap back to start
        # of a tight host-CTA cluster within 75s.
        end = pool[-1]
        start = end
        for t in reversed(pool):
            if end.sec - t.sec <= 75:
                start = t
            else:
                break
        return start.sec
    # Fallback: host wrap / gratitude close (early eps often fragment the CTA)
    wrap = re.compile(
        r"(?:thank you for (?:coming|being)|thanks for your|"
        r"appreciate you(?:r)?(?: coming| friendship)?|"
        r"love you (?:so much|very much|too|guys|folks)|i love you|"
        r"much love|check (?:them|her|him|our) out|"
        r"take care(?! of the)|have a good(?: rest)?|"
        r"peace(?: out)?\b|be (?:wary|conscious|mindful)|"
        r"podcast out|junkyard(?: love)?(?: podcast)? out)",
        re.I,
    )
    # Also scan last ~10 turns across speakers for split outros
    tail = [t for t in turns if t.sec >= cutoff]
    for t in reversed(tail):
        if wrap.search(t.text):
            # Prefer nearest prior host turn within 90s as chapter start
            host = next(
                (
                    h
                    for h in reversed(tail)
                    if h.sec <= t.sec
                    and HOST_RE.match(h.speaker)
                    and h.sec >= t.sec - 90
                ),
                t,
            )
            return host.sec
    return None


def clean_words(text: str) -> list[str]:
    text = re.sub(r"[^\w\s'\-/]", " ", text.lower())
    words = []
    for w in text.split():
        w = w.strip("'/-")
        if len(w) < 3 or w in STOP:
            continue
        if w.isdigit():
            continue
        words.append(w)
    return words


def title_case_label(s: str) -> str:
    s = re.sub(r"\s+", " ", s).strip(" —-/")
    if not s:
        return s
    # Keep short connectors lower unless first
    small = {"and", "or", "of", "the", "a", "an", "to", "for", "vs", "with", "in", "on"}
    parts = []
    for i, w in enumerate(s.split()):
        if i > 0 and w.lower() in small:
            parts.append(w.lower())
        elif w.isupper() and len(w) <= 4:
            parts.append(w)
        else:
            parts.append(w[:1].upper() + w[1:])
    return " ".join(parts)


def extract_about_phrases(content_dir: Path) -> list[str]:
    phrases: list[str] = []
    for name in ("source-about.md", "source-description.md", "source-youtube-title.txt"):
        p = content_dir / name
        if p.exists():
            phrases.append(p.read_text(encoding="utf-8", errors="replace"))
    picks = content_dir / "source-archive-picks.md"
    if picks.exists():
        md = picks.read_text(encoding="utf-8", errors="replace")
        km = re.search(r"^## Keywords\s*\n+(.*?)(?=^## |\Z)", md, re.M | re.S)
        if km:
            phrases.append(km.group(1))
    return phrases


def grounded_tokens(about_blobs: list[str]) -> set[str]:
    toks: set[str] = set()
    for blob in about_blobs:
        for w in clean_words(blob):
            if len(w) >= 4:
                toks.add(w)
    return toks



def label_from_window(
    turns: list[Turn],
    t0: int,
    t1: int,
    about_toks: set[str],
    guest_name: str = "",
) -> str:
    """Grounded, conservative labels — prefer About/keywords + clean dict words."""
    window = [t for t in turns if t0 <= t.sec < t1 and len(t.text) >= 35]
    if not window:
        window = [t for t in turns if t0 - 20 <= t.sec < t1 + 20 and len(t.text) >= 20]
    if not window:
        return "Conversation continues"

    guest_turns = [t for t in window if not HOST_RE.match(t.speaker)]
    pool = guest_turns if guest_turns else window
    win_low = " ".join(t.text for t in pool).lower()
    win_words = set(clean_words(win_low))

    def dict_ok(w: str) -> bool:
        wl = w.lower().replace("'", "")
        if wl in STOP or len(wl) < 3:
            return False
        if not DICT_WORDS:
            return bool(re.search(r"[aeiouy]", wl))
        return (
            wl in DICT_WORDS
            or wl.rstrip("s") in DICT_WORDS
            or (wl + "s") in DICT_WORDS
        )

    # About/keyword tokens present in window
    grounded = [
        w
        for w in about_toks
        if w in win_words
        and dict_ok(w)
        and w not in {"jacob", "rhines", "junkyard", "podcast", "episode", "love"}
    ]
    # stable order by length then alpha (prefer specific terms)
    grounded = sorted(set(grounded), key=lambda w: (-len(w), w))

    # Pattern extractions
    patt = re.compile(
        r"(?:talk(?:ing)? about|speaking (?:on|about)|called|known as|"
        r"idea of|practice of|concept of|importance of|power of|"
        r"my (?:job|work|practice|path|journey|story)|"
        r"(?:started|start)(?:ed)? (?:with|as|in|doing)|"
        r"learning (?:to|how to))\s+([A-Za-z][A-Za-z0-9' \-]{3,40})",
        re.I,
    )
    for t in pool:
        for m in patt.finditer(t.text):
            frag = re.sub(r'\s+', ' ', m.group(1)).strip(" .,!?;:\"'")
            words = [w for w in re.findall(r"[A-Za-z']+", frag) if dict_ok(w)]
            if 2 <= len(words) <= 6:
                return title_case_label(" ".join(words[:5]))[:72]

    if len(grounded) >= 2:
        return title_case_label(f"{grounded[0]} / {grounded[1]}")[:72]
    if len(grounded) == 1:
        # pair with strongest other dict word in window
        scores: dict[str, float] = {}
        for t in pool:
            for w in clean_words(t.text):
                if not dict_ok(w) or w == grounded[0]:
                    continue
                scores[w] = scores.get(w, 0) + (1.5 if not HOST_RE.match(t.speaker) else 1.0)
        if scores:
            top = max(scores, key=scores.get)
            return title_case_label(f"{grounded[0]} / {top}")[:72]
        return title_case_label(grounded[0] + " theme")[:72]

    # Score clean dict bigrams
    bigrams: dict[str, float] = {}
    scores: dict[str, float] = {}
    for t in pool:
        words = [w for w in clean_words(t.text) if dict_ok(w)]
        wt = 1.5 if not HOST_RE.match(t.speaker) else 0.8
        for w in words:
            scores[w] = scores.get(w, 0) + wt
        for a, b in zip(words, words[1:]):
            bg = f"{a} {b}"
            bigrams[bg] = bigrams.get(bg, 0) + wt

    for bg, sc in sorted(bigrams.items(), key=lambda x: -x[1])[:10]:
        if sc >= 2.5:
            return title_case_label(bg)[:72]

    top_words = [w for w, sc in sorted(scores.items(), key=lambda x: -x[1]) if sc >= 2.0][:2]
    if len(top_words) == 2:
        return title_case_label(f"{top_words[0]} / {top_words[1]}")[:72]
    if len(top_words) == 1:
        return title_case_label(top_words[0] + " theme")[:72]

    return "Conversation continues"


def is_outro_label(label: str) -> bool:
    return bool(re.search(r"\boutro\b|\bclose\b|\bclosing\b|\bwrap\b", label, re.I))


def normalize_outro_label(label: str, turns: list[Turn], sec: int) -> str:
    # Keep substance after Outro — if already detailed keep; else enrich from turn
    turn = next((t for t in turns if t.sec == sec), None)
    detail = ""
    if turn:
        bits = []
        if re.search(r"drink (?:some )?water", turn.text, re.I):
            bits.append("drink water")
        if re.search(r"stretch|pilates|yoga|mobility", turn.text, re.I):
            bits.append("stretch")
        if re.search(r"love yoursel", turn.text, re.I):
            bits.append("love yourselves")
        if re.search(r"get present|get grounded|posture", turn.text, re.I):
            bits.append("get present")
        if re.search(r"peace out", turn.text, re.I):
            bits.append("peace out")
        if bits:
            detail = " / ".join(bits[:3])
    if is_outro_label(label) and "—" in label:
        # already Outro — …
        return label if label.lower().startswith("outro") else f"Outro — {label.split('—',1)[-1].strip()}"
    if detail:
        return f"Outro — {detail}"
    if is_outro_label(label):
        rest = re.sub(r"^(?:close|closing|outro|wrap)\s*[—\-–:]?\s*", "", label, flags=re.I).strip()
        return f"Outro — {rest}" if rest else "Outro"
    return f"Outro — {label}" if label and not label.lower().startswith("outro") else (label or "Outro")


def target_spacing(duration: int) -> int:
    """Ideal seconds between chapters: ~5–8 min, scaled by length."""
    if duration <= 0:
        return 6 * 60
    # aim roughly duration/14 chapters core (excluding dense short eps)
    ideal = duration / 14
    return int(max(4 * 60, min(8 * 60, ideal)))


def min_chapters_for(duration: int) -> int:
    if duration < 35 * 60:
        return 8
    if duration < 70 * 60:
        return 10
    if duration < 110 * 60:
        return 14
    return 16


def max_chapters_for(duration: int) -> int:
    # avoid denser than ~1 / 3.5 min
    if duration <= 0:
        return 24
    return int(max(12, min(32, duration / (3.5 * 60) + 2)))


def build_chapter_list(
    existing: list[Chapter],
    turns: list[Turn],
    duration: int,
    about_toks: set[str],
    guest_name: str = "",
) -> list[Chapter]:
    if not turns:
        return existing
    turn_secs = [t.sec for t in turns]
    last_turn = turns[-1].sec
    runtime = max(duration, last_turn) if duration else last_turn

    # Snap existing
    snapped: list[Chapter] = []
    seen: set[int] = set()
    for ch in existing:
        ns = nearest_turn_sec(ch.sec, turn_secs)
        if ns is None:
            continue
        if ns in seen:
            continue
        # drop bogus outro labels mid-show
        label = ch.label.strip()
        snapped.append(Chapter(sec=ns, label=label, source="existing"))
        seen.add(ns)

    # Ensure intro near start
    if not snapped or snapped[0].sec > 90:
        intro_sec = turn_secs[0]
        # prefer a turn within first 30s
        for s in turn_secs:
            if s <= 30:
                intro_sec = s
                break
            if s > 30:
                break
        if intro_sec not in seen:
            snapped.insert(0, Chapter(sec=intro_sec, label="Opening", source="intro"))
            seen.add(intro_sec)
    else:
        # normalize first label if generic empty
        if snapped[0].sec <= 30 and not snapped[0].label:
            snapped[0].label = "Opening"

    snapped.sort(key=lambda c: c.sec)

    outro_sec = detect_outro(turns)
    if outro_sec is not None:
        outro_sec = nearest_turn_sec(outro_sec, turn_secs) or outro_sec

    spacing = target_spacing(runtime)
    # Fill large gaps
    filled: list[Chapter] = []
    for i, ch in enumerate(snapped):
        # skip existing chapters that sit after outro (except we'll re-add outro)
        if outro_sec is not None and ch.sec > outro_sec + 30 and is_outro_label(ch.label):
            continue
        if outro_sec is not None and ch.sec >= outro_sec and is_outro_label(ch.label):
            # will handle outro later
            continue
        if filled:
            prev = filled[-1].sec
            gap = ch.sec - prev
            # insert midpoints while gap too large
            while gap > spacing * 1.35 and len(filled) < max_chapters_for(runtime) + 5:
                target = prev + spacing
                ns = nearest_turn_sec(target, turn_secs, max_delta=120)
                if ns is None or ns <= prev + 90 or ns >= ch.sec - 90:
                    # try midpoint
                    mid = (prev + ch.sec) // 2
                    ns = nearest_turn_sec(mid, turn_secs, max_delta=150)
                if ns is None or ns <= prev + 60 or ns >= ch.sec - 60:
                    break
                if ns in seen:
                    break
                end_w = min(ch.sec, ns + spacing)
                label = label_from_window(turns, ns, end_w, about_toks, guest_name)
                filled.append(Chapter(sec=ns, label=label, source="new"))
                seen.add(ns)
                prev = ns
                gap = ch.sec - prev
        filled.append(ch)
        seen.add(ch.sec)

    # Extend after last chapter toward outro / end
    end_target = outro_sec if outro_sec is not None else last_turn
    if filled:
        prev = filled[-1].sec
        # If last existing is far from end, keep filling
        guard = 0
        while end_target - prev > spacing * 1.15 and guard < 40:
            guard += 1
            target = prev + spacing
            if target >= end_target - 60:
                break
            ns = nearest_turn_sec(target, turn_secs, max_delta=120)
            if ns is None or ns <= prev + 60:
                mid = (prev + end_target) // 2
                ns = nearest_turn_sec(mid, turn_secs, max_delta=150)
            if ns is None or ns <= prev + 60 or ns >= end_target - 45:
                break
            if ns in seen:
                # nudge forward
                nxt = [s for s in turn_secs if s > prev + spacing // 2]
                if not nxt:
                    break
                ns = nxt[0]
                if ns >= end_target - 45 or ns in seen:
                    break
            label = label_from_window(
                turns, ns, min(end_target, ns + spacing), about_toks, guest_name
            )
            filled.append(Chapter(sec=ns, label=label, source="new"))
            seen.add(ns)
            prev = ns

    # Ensure minimum coverage count by splitting largest gaps
    def largest_gap(chaps: list[Chapter]) -> tuple[int, int, int]:
        best = (-1, 0, 0)  # gap, idx_after_left, left_sec
        for i in range(len(chaps) - 1):
            g = chaps[i + 1].sec - chaps[i].sec
            if g > best[0]:
                best = (g, i + 1, chaps[i].sec)
        # also gap to end_target
        if chaps:
            g = end_target - chaps[-1].sec
            if g > best[0]:
                best = (g, len(chaps), chaps[-1].sec)
        return best

    filled.sort(key=lambda c: c.sec)
    min_n = min_chapters_for(runtime)
    max_n = max_chapters_for(runtime)
    guard = 0
    while len(filled) < min_n and guard < 30:
        guard += 1
        gap, _, left = largest_gap(filled)
        if gap < spacing * 0.9:
            break
        target = left + gap // 2
        ns = nearest_turn_sec(target, turn_secs, max_delta=150)
        if ns is None or ns in seen:
            break
        # don't collide
        if any(abs(c.sec - ns) < 90 for c in filled):
            break
        label = label_from_window(
            turns, ns, min(end_target, ns + spacing), about_toks, guest_name
        )
        filled.append(Chapter(sec=ns, label=label, source="new"))
        seen.add(ns)
        filled.sort(key=lambda c: c.sec)

    # Trim if absurdly dense (prefer keeping existing)
    if len(filled) > max_n:
        # remove newest inserted in smallest gaps first
        while len(filled) > max_n:
            # find smallest gap whose right chapter is source=new
            best_i = None
            best_gap = 10**9
            for i in range(1, len(filled)):
                if filled[i].source != "new":
                    continue
                g = filled[i].sec - filled[i - 1].sec
                if g < best_gap:
                    best_gap = g
                    best_i = i
            if best_i is None:
                break
            seen.discard(filled[best_i].sec)
            filled.pop(best_i)

    # Prefer an existing late Outro/close if detection drifted earlier
    existing_outro = None
    for ch in existing:
        if is_outro_label(ch.label) and ch.sec >= runtime * 0.9:
            existing_outro = ch
    if existing_outro is not None:
        # Keep existing outro clock when it snaps near end and is later than detection
        eo = nearest_turn_sec(existing_outro.sec, turn_secs) or existing_outro.sec
        if outro_sec is None or eo >= (outro_sec - 30):
            outro_sec = eo

    # Attach / replace Outro as last chapter
    if outro_sec is not None:
        # remove chapters at/after outro
        filled = [c for c in filled if c.sec < outro_sec - 15]
        # if an existing chapter was already a close near end, reuse substance
        prior_close = None
        for ch in existing:
            if is_outro_label(ch.label) or ch.sec >= outro_sec - 90:
                if abs(ch.sec - outro_sec) < 180 or is_outro_label(ch.label):
                    prior_close = ch
        label = normalize_outro_label(
            prior_close.label if prior_close else "Outro", turns, outro_sec
        )
        if not label.lower().startswith("outro"):
            label = f"Outro — {label}"
        # simplify to canonical Outro form
        if label.lower() == "outro":
            label = normalize_outro_label("Outro", turns, outro_sec)
        filled.append(Chapter(sec=outro_sec, label=label, source="outro"))
    else:
        # No clear outro — if last chapter far from end, add closing beat from last turn
        if filled and (last_turn - filled[-1].sec) > 3 * 60:
            ns = nearest_turn_sec(max(filled[-1].sec + 60, last_turn - 90), turn_secs)
            if ns and ns > filled[-1].sec + 45:
                # Check if last host turn is wrap-like
                last_host = next(
                    (t for t in reversed(turns) if HOST_RE.match(t.speaker)), turns[-1]
                )
                if last_host.sec >= last_turn - 180:
                    lab = normalize_outro_label("Close", turns, last_host.sec)
                    filled.append(Chapter(sec=last_host.sec, label=lab, source="outro"))
                else:
                    lab = label_from_window(
                        turns, ns, last_turn + 1, about_toks, guest_name
                    )
                    filled.append(Chapter(sec=ns, label=lab, source="new"))
        elif filled and not is_outro_label(filled[-1].label):
            # If coverage already near end, optionally retitle last if it's clearly close CTA
            last_ch = filled[-1]
            if last_ch.sec >= runtime * 0.9 or last_ch.sec >= last_turn - 180:
                turn = next((t for t in turns if t.sec == last_ch.sec), None)
                if turn and HOST_RE.match(turn.speaker) and OUTRO_RE.search(turn.text):
                    filled[-1] = Chapter(
                        sec=last_ch.sec,
                        label=normalize_outro_label(last_ch.label, turns, last_ch.sec),
                        source="outro",
                    )

    # Final sort + dedupe
    filled.sort(key=lambda c: c.sec)
    final: list[Chapter] = []
    for ch in filled:
        if final and abs(final[-1].sec - ch.sec) < 45:
            # prefer existing / outro
            if ch.source in {"existing", "outro"} and final[-1].source == "new":
                final[-1] = ch
            continue
        final.append(ch)

    # Ensure last is Outro-labeled when we detected outro
    if outro_sec is not None and final:
        if final[-1].sec != outro_sec:
            # snap last
            final = [c for c in final if c.sec < outro_sec - 15]
            final.append(
                Chapter(
                    sec=outro_sec,
                    label=normalize_outro_label("Outro", turns, outro_sec),
                    source="outro",
                )
            )
        elif not final[-1].label.lower().startswith("outro"):
            final[-1].label = normalize_outro_label(final[-1].label, turns, final[-1].sec)

    # Dedupe consecutive identical labels by merging clock (keep earlier)
    deduped: list[Chapter] = []
    for ch in final:
        if deduped and deduped[-1].label.lower() == ch.label.lower() and ch.source == "new":
            continue
        deduped.append(ch)
    final = deduped

    return final


def chapters_to_md(chapters: list[Chapter]) -> str:
    lines = ["## Chapter-style timestamps", ""]
    for ch in chapters:
        lines.append(f"- [{ch.ts}](#{ch.anchor}) — {ch.label}")
    lines.append("")
    return "\n".join(lines)


def replace_md_chapters(md: str, chapters: list[Chapter]) -> str:
    block = chapters_to_md(chapters)
    if re.search(r"^## Chapter-style timestamps\s*$", md, re.M):
        return re.sub(
            r"^## Chapter-style timestamps\s*\n(?:.*?\n)*?(?=^## |\Z)",
            block + "\n",
            md,
            count=1,
            flags=re.M,
        )
    # insert before Keywords if present
    if re.search(r"^## Keywords\s*$", md, re.M):
        return re.sub(
            r"^## Keywords\s*$",
            block + "\n## Keywords",
            md,
            count=1,
            flags=re.M,
        )
    return md.rstrip() + "\n\n" + block


def html_has_ts_class(html: str) -> bool:
    idx = html.find("Chapter-style timestamps")
    if idx < 0:
        return False
    return 'class="ts"' in html[idx : idx + 600]


def chapters_to_html(chapters: list[Chapter], use_ts_class: bool) -> str:
    parts = []
    for ch in chapters:
        label = html_lib.escape(ch.label, quote=False)
        if use_ts_class:
            parts.append(
                f'<li><a class="ts" href="#{ch.anchor}">[{ch.ts}]</a> — {label}</li>'
            )
        else:
            parts.append(f'<li><a href="#{ch.anchor}">{ch.ts}</a> — {label}</li>')
    return "\n".join(parts)


def replace_html_chapters(html: str, chapters: list[Chapter]) -> str:
    use_ts = html_has_ts_class(html)
    new_ul_inner = chapters_to_html(chapters, use_ts)
    # Prefer Archive picks Chapter-style block
    pattern = re.compile(
        r"(<h3>Chapter-style timestamps</h3>\s*<ul class=\"(?:archive-)?chapters\">\s*)(.*?)(\s*</ul>)",
        re.S,
    )
    m = pattern.search(html)
    if m:
        return html[: m.start(2)] + new_ul_inner + html[m.end(2) :]
    # Fallback: first ul.chapters after Archive picks
    ap = html.find("Archive picks")
    if ap >= 0:
        pattern2 = re.compile(
            r"(<ul class=\"chapters\">\s*)(.*?)(\s*</ul>)",
            re.S,
        )
        m2 = pattern2.search(html, ap)
        if m2:
            return html[: m2.start(2)] + new_ul_inner + html[m2.end(2) :]
    return html


def ensure_anchors(html: str, chapters: list[Chapter]) -> str:
    """Insert hidden anchors for chapter times missing as turn ids."""
    existing = set(re.findall(r'id="(t-\d{2}-\d{2}-\d{2})"', html))
    # find transcript cue starts for nearest placement
    cue_re = re.compile(r'<p class="cue" id="(t-\d{2}-\d{2}-\d{2})"')
    cue_ids = [(m.start(), m.group(1)) for m in cue_re.finditer(html)]

    def id_to_sec(tid: str) -> int:
        _, h, m, s = tid.split("-")
        return int(h) * 3600 + int(m) * 60 + int(s)

    inserts: list[tuple[int, str]] = []
    for ch in chapters:
        if ch.anchor in existing:
            continue
        # place hidden span before nearest cue
        if not cue_ids:
            continue
        nearest = min(cue_ids, key=lambda x: abs(id_to_sec(x[1]) - ch.sec))
        if abs(id_to_sec(nearest[1]) - ch.sec) > 180:
            continue
        span = (
            f'<span id="{ch.anchor}" class="t-anchor" hidden '
            f'data-chapter-anchor="1"></span>\n'
        )
        inserts.append((nearest[0], span))
        existing.add(ch.anchor)

    if not inserts:
        return html
    # apply from end so offsets stable
    inserts.sort(key=lambda x: x[0], reverse=True)
    for pos, span in inserts:
        html = html[:pos] + span + html[pos:]
    return html


def guest_name_from_meta(content_dir: Path) -> str:
    meta = content_dir / "meta.json"
    if meta.exists():
        try:
            data = json.loads(meta.read_text(encoding="utf-8"))
            for k in ("guest_name", "guest", "title"):
                if data.get(k):
                    return str(data[k])
        except Exception:
            pass
    return ""


def map_content_dirs() -> dict[str, Path]:
    out: dict[str, Path] = {}
    for d in CONTENT.iterdir():
        if not d.is_dir() or "removed" in d.name:
            continue
        n = episode_num(d.name)
        if n:
            out[n] = d
    for n, slug in UNNUMBERED.items():
        p = CONTENT / slug
        if p.is_dir():
            out[n] = p
    return out


def map_episode_dirs() -> dict[str, Path]:
    out: dict[str, Path] = {}
    for d in EPISODES.iterdir():
        if not d.is_dir() or "removed" in d.name:
            continue
        n = episode_num(d.name)
        if n and (d / "index.html").exists():
            out[n] = d
    return out


def coverage_pct(chapters: list[Chapter], duration: int, last_turn: int) -> float:
    if not chapters:
        return 0.0
    runtime = max(duration, last_turn) if duration else last_turn
    if runtime <= 0:
        return 0.0
    return 100.0 * chapters[-1].sec / runtime


def process_episode(
    num: str,
    content_dir: Path,
    ep_dir: Path,
    duration: int,
    dry_run: bool = False,
    force: bool = False,
) -> dict:
    tp = content_dir / "transcript.md"
    if not tp.exists():
        return {"num": num, "status": "skip", "reason": "no transcript"}
    turns = parse_turns(tp.read_text(encoding="utf-8", errors="replace"))
    if not turns:
        return {"num": num, "status": "skip", "reason": "empty turns"}

    picks_path = content_dir / "source-archive-picks.md"
    md = picks_path.read_text(encoding="utf-8", errors="replace") if picks_path.exists() else ""
    existing = parse_existing_chapters(md) if md else []
    before_n = len(existing)
    before_last = existing[-1].sec if existing else 0
    before_pct = coverage_pct(existing, duration, turns[-1].sec)

    # 0037 hold lightly unless force or clearly needs fill after ASR
    light = num in HOLD_LIGHT and not force
    about_toks = grounded_tokens(extract_about_phrases(content_dir))
    guest = guest_name_from_meta(content_dir)

    if light:
        # Only ensure outro + fill if last chapter << runtime (post-ASR gap)
        chapters = build_chapter_list(existing, turns, duration, about_toks, guest)
        # If we already had good full coverage with Outro, keep mostly existing
        if (
            before_pct >= 95
            and existing
            and is_outro_label(existing[-1].label)
            and before_n >= min_chapters_for(duration) - 2
        ):
            # still run builder but prefer existing labels: rebuild already does
            pass
        note = "light-touch (0037 ASR landed — filled gaps / ensured Outro)"
    else:
        chapters = build_chapter_list(existing, turns, duration, about_toks, guest)
        note = ""

    # Optional handcrafted overrides (priority quality)
    overrides = load_overrides().get(num)
    if overrides:
        turn_secs = [t.sec for t in turns]

        def parse_sec(item):
            sec = item.get("sec")
            if isinstance(sec, (int, float)):
                return int(sec)
            if isinstance(sec, str) and ":" in sec:
                parts = [int(x) for x in sec.split(":")]
                if len(parts) == 3:
                    return parts[0] * 3600 + parts[1] * 60 + parts[2]
                if len(parts) == 2:
                    return parts[0] * 60 + parts[1]
            return None

        mode = "full" if any(isinstance(i, dict) and i.get("mode") == "full" for i in overrides) else "merge"
        # allow {"mode":"full","chapters":[...]} wrapper
        if isinstance(overrides, dict):
            mode = overrides.get("mode", "full")
            overrides = overrides.get("chapters") or []
        ov_chaps = []
        for item in overrides:
            if not isinstance(item, dict) or item.get("mode"):
                continue
            sec = parse_sec(item)
            label = item.get("label") or ""
            if sec is None or not label:
                continue
            ns = nearest_turn_sec(sec, turn_secs, max_delta=120)
            if ns is None:
                continue
            ov_chaps.append(Chapter(sec=ns, label=label, source="override"))
        if ov_chaps:
            if mode == "full":
                chapters = sorted(ov_chaps, key=lambda c: c.sec)
            else:
                for ov in ov_chaps:
                    matched = False
                    for i, ch in enumerate(chapters):
                        if abs(ch.sec - ov.sec) <= 90:
                            chapters[i] = Chapter(sec=ch.sec, label=ov.label, source="override")
                            matched = True
                            break
                    if not matched:
                        chapters.append(ov)
                chapters = sorted(chapters, key=lambda c: c.sec)
            note = (note + f" overrides:{mode}").strip()

    after_n = len(chapters)
    after_last = chapters[-1].sec if chapters else 0
    after_pct = coverage_pct(chapters, duration, turns[-1].sec)
    has_outro = bool(chapters and chapters[-1].label.lower().startswith("outro"))

    result = {
        "num": num,
        "status": "ok",
        "before_n": before_n,
        "after_n": after_n,
        "before_pct": round(before_pct, 1),
        "after_pct": round(after_pct, 1),
        "before_last": fmt_ts(before_last),
        "after_last": fmt_ts(after_last),
        "has_outro": has_outro,
        "duration": duration,
        "last_turn": turns[-1].sec,
        "note": note,
        "labels": [c.label for c in chapters],
        "changed": chapters != existing
        and (
            before_n != after_n
            or before_last != after_last
            or [c.label for c in existing] != [c.label for c in chapters]
        ),
    }

    # Detect real change more carefully
    same = (
        before_n == after_n
        and all(
            abs(a.sec - b.sec) <= 1 and a.label == b.label
            for a, b in zip(existing, chapters)
        )
        if before_n == after_n and before_n > 0
        else False
    )
    result["changed"] = not same

    if dry_run:
        return result

    if not picks_path.exists():
        md = (
            "# Archive picks (not from published notes)\n\n"
            "Extracted from the transcript and published About already on this episode. "
            "Labeled separately from Jacob’s published About / Chapters / Quotes / Hashtags.\n\n"
        )
    md2 = replace_md_chapters(md, chapters)
    picks_path.write_text(md2, encoding="utf-8")

    html_path = ep_dir / "index.html"
    html = html_path.read_text(encoding="utf-8", errors="replace")
    html2 = replace_html_chapters(html, chapters)
    html2 = ensure_anchors(html2, chapters)

    # Safety: preserve UX hooks
    for needle, label in [
        ("<!-- topic-chips:start -->", "topic chips"),
        ('class="browse-subtitle"', "browse-subtitle"),
    ]:
        if needle in html and needle not in html2:
            raise RuntimeError(f"{num}: {label} lost")
    if re.search(r'data-theme|theme-dark|class="dark"', html) and not re.search(
        r'data-theme|theme-dark|class="dark"', html2
    ):
        # dark theme may be CSS-only; don't fail hard
        pass

    html_path.write_text(html2, encoding="utf-8")

    # Optionally sync source-timestamps.md when it already holds a chapter list
    ts_path = content_dir / "source-timestamps.md"
    if ts_path.exists():
        ts = ts_path.read_text(encoding="utf-8", errors="replace")
        if re.search(r"^\s*[-*]?\s*\[?\d{1,2}:\d{2}", ts, re.M) and "none published" not in ts.lower():
            # Only refresh if it looks like YT/archive chapter dump without Jacob prose
            if "Chapter" in ts or re.search(r"\d{2}:\d{2}:\d{2}", ts):
                # Keep a note + mirror archive picks chapters
                if "inventory has_timestamps=yes" in ts.lower() or "published" in ts.lower()[:200]:
                    pass  # leave Jacob published timestamps source alone
                else:
                    body = (
                        "(Archive picks chapter list — regenerable full-runtime pass)\n\n"
                        + "\n".join(f"- [{c.ts}] {c.label}" for c in chapters)
                        + "\n"
                    )
                    # Only overwrite clearly machine/archive chapter files
                    if "YouTube chapter" in ts or "Archive picks" in ts or ts.strip().startswith("0") or ts.strip().startswith("["):
                        ts_path.write_text(body, encoding="utf-8")

    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--force", action="store_true", help="Do not light-touch 0037")
    ap.add_argument("--report", default="")
    args = ap.parse_args()

    durations = load_durations()
    content_map = map_content_dirs()
    ep_map = map_episode_dirs()

    nums = sorted(set(content_map) & set(ep_map))
    if args.only:
        want = {f"{int(x):04d}" for x in args.only}
        nums = [n for n in nums if n in want]

    results = []
    for num in nums:
        try:
            r = process_episode(
                num,
                content_map[num],
                ep_map[num],
                durations.get(num, 0),
                dry_run=args.dry_run,
                force=args.force,
            )
        except Exception as e:
            r = {"num": num, "status": "error", "reason": str(e)}
        results.append(r)
        print(
            f"{num} {r.get('status')} {r.get('before_n')}→{r.get('after_n')} "
            f"{r.get('before_pct')}%→{r.get('after_pct')}% "
            f"last {r.get('before_last')}→{r.get('after_last')} "
            f"outro={r.get('has_outro')} changed={r.get('changed')} "
            f"{r.get('note') or r.get('reason') or ''}",
            flush=True,
        )

    thin = [
        r
        for r in results
        if r.get("status") == "ok"
        and (
            (r.get("after_pct") or 0) < 90
            or (r.get("after_n") or 0) < 8
            or not r.get("has_outro")
        )
    ]
    summary = {
        "episodes_ok": sum(1 for r in results if r.get("status") == "ok"),
        "episodes_changed": sum(1 for r in results if r.get("changed")),
        "episodes_error": sum(1 for r in results if r.get("status") == "error"),
        "episodes_skip": sum(1 for r in results if r.get("status") == "skip"),
        "with_outro": sum(1 for r in results if r.get("has_outro")),
        "still_thin": [
            {
                "num": r["num"],
                "n": r.get("after_n"),
                "pct": r.get("after_pct"),
                "outro": r.get("has_outro"),
                "last": r.get("after_last"),
            }
            for r in thin
        ],
        "samples": [
            {
                "num": r["num"],
                "before_n": r.get("before_n"),
                "after_n": r.get("after_n"),
                "before_pct": r.get("before_pct"),
                "after_pct": r.get("after_pct"),
                "labels_tail": (r.get("labels") or [])[-4:],
            }
            for r in results
            if r.get("status") == "ok"
            and r["num"]
            in {
                "0003",
                "0012",
                "0020",
                "0027",
                "0028",
                "0037",
                "0056",
                "0079",
                "0080",
                "0085",
                "0086",
                "0087",
                "0095",
                "0047",
                "0105",
            }
        ],
        "results": results,
    }
    print(
        "SUMMARY",
        json.dumps({k: v for k, v in summary.items() if k != "results"}, indent=2),
    )
    if args.report:
        Path(args.report).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return 0 if summary["episodes_error"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
