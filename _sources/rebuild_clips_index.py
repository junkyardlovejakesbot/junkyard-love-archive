#!/usr/bin/env python3
"""Rebuild chapter/clip index for all published Junkyard Love episodes.

Treats every Archive-picks chapter as a clip. Across the full catalog:
  - drops produced intro bumper + produced outro (theme / Sam Harris / drink-water)
  - labels Host open (Jacob alone after bumper) with a real topic title
  - splits long one-word blob chapters into tighter beats
  - writes short + long summaries grounded in transcript text for that range
  - emits clips_index.json + updates episodes_index chapters + Archive picks HTML/MD

No git commit / no push.
"""
from __future__ import annotations

import argparse
import html as html_lib
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = Path(__file__).resolve().parent
CONTENT = SOURCES / "content"
EPISODES = ROOT / "episodes"
ASSETS = ROOT / "assets"
REPORTS = SOURCES / "reports"

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
    r"cancel cancel|thumbs up|"
    r"wherever you(?:'re| are) listening|"
    r"subscribe to (?:the )?junkyard|"
    r"find clips from the show"
    r")",
    re.I,
)
OUTRO_STRONG_RE = re.compile(
    r"(?:"
    r"drink (?:some )?water|love yoursel(?:f|ves)|peace out|"
    r"get present|get grounded|put this phone away|five[- ]?star|"
    r"junkyard love (?:podcast )?out|have a good (?:rest of your |rest your )?day|"
    r"wiggle your|focus on your posture|thumbs up|"
    r"wherever you(?:'re| are) listening|subscribe to (?:the )?junkyard"
    r")",
    re.I,
)

BUMPER_TEXT_RE = re.compile(
    r"(?:"
    r"hello and welcome to the junkyard love|"
    r"welcome to the junkyard love podcast|"
    r"sam harris|"
    r"knowledge is power|"
    r"at what age do we learn|"
    r"theme song|produced by|"
    r"today'?s recommendation"
    r")",
    re.I,
)

HOST_RE = re.compile(r"^(jacob|host)\b", re.I)
BLOB_TITLE_RE = re.compile(
    r"^(?:"
    r"breath|chat|practice|intro|opening|outro|conversation|talk|close|closing|"
    r"welcome|wrap|music|story|advice|update|updates|background|journey|"
    r"connection|community|growth|healing|mindfulness|meditation|ego|"
    r"presence|gratitude|father|mother|family|work|life|love|fear|"
    r"body|mind|spirit|sleep|anxiety|depression|trauma|addiction|"
    r"creating|writing|alcohol|topics|open"
    r")(?:\s*/\s*(?:breath|chat|practice|talk|conversation))?$",
    re.I,
)
WEAK_OPEN_RE = re.compile(
    r"^(?:intro|opening|open|welcome(?:\s+back)?)(?:\b.*)?$",
    re.I,
)
OUTRO_LABEL_RE = re.compile(
    r"(?:"
    r"\b(?:outro|closing|end credits|credits|theme|bumper|subscribe to the junkyard)\b|"
    r"host close|"
    r"drink water|"
    r"junkyard love thank you|"
    r"^close\b|^closing\b"
    r")",
    re.I,
)
BUMPER_LABEL_RE = re.compile(
    r"^(?:intro|opening|open|bumper|theme|credits|end credits|"
    r"welcome to the junkyard love(?:\s+podcast)?|"
    r"open\s*[—\-–:]\s*host bumper|"
    r"open\s*[—\-–:].*bumper|"
    r"junkyard love bumper)"
    r"(?:\s*[—\-–:].*)?$",
    re.I,
)

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
    "think", "feel", "say", "said", "says", "going", "get", "got", "getting",
    "go", "went", "make", "made", "making", "take", "took", "want", "wanted",
    "need", "needed", "see", "saw", "look", "looking", "come", "came", "coming",
    "let", "put", "one", "two", "three", "first", "even", "still", "well",
    "much", "many", "way", "ways", "time", "times", "today", "now", "actually",
    "literally", "basically", "probably", "maybe", "kinda", "mean", "means",
    "meant", "talk", "talking", "talked", "podcast", "episode", "junkyard",
    "love", "jacob", "guest", "question", "questions", "answer", "true",
    "good", "great", "cool", "super", "little", "big", "new", "old", "same",
    "different", "whole", "part", "through", "over", "under", "before", "after",
    "again", "around", "always", "never", "ever", "already", "almost", "enough",
    "able", "sure", "fine", "nah", "hey", "hi", "hello", "welcome", "thanks",
    "thank", "appreciate", "absolutely", "totally", "exactly", "definitely",
    "obviously", "honestly", "whatever", "somebody", "everyone", "anybody",
    "doing", "done", "doesn't", "don't", "didn't", "isn't", "wasn't", "weren't",
    "can't", "won't", "i'm", "you're", "we're", "they're", "it's", "that's",
    "there's", "here's", "who's", "what's", "i've", "you've", "we've", "they've",
    "i'll", "you'll", "we'll", "they'll", "i'd", "you'd", "we'd", "they'd",
}

UNNUMBERED = {
    "0118": "sean-blackwell-mania-is-a-message",
    "0120": "david-hulse-path-to-no-path",
    "0121": "tim-fraley-surrendering-the-porsche",
}

REMOVED = {"0001", "0014", "0016", "0029"}

# Hand-grounded title fixes: episode -> {start_seconds: title}
TITLE_OVERRIDES: dict[str, dict[int, str]] = {
    "0002": {0: "EYE Clothing cold open — raves & selling from the trunk"},
    "0012": {0: "Bob Kendall cold open — third-person marketplace intro"},
}

TOPIC_KEYWORDS = {
    "awakening-mystical": [
        "awakening", "kundalini", "mystical", "spiritual emergency", "gnosis",
        "enlightenment", "ascension", "psychedelic",
    ],
    "breath-body-practice": [
        "breath", "breathwork", "exhale", "yoga", "body", "nervous system",
        "meditation", "posture", "stretch", "pilates",
    ],
    "fatherhood-family": [
        "father", "dad", "son", "daughter", "family", "parent", "mother", "kids",
        "childhood",
    ],
    "healing-trauma": [
        "trauma", "healing", "therapy", "ptsd", "abuse", "wound", "pain",
        "grief", "forgiveness",
    ],
    "masculinity-armor": [
        "masculinity", "armor", "vulnerable", "vulnerability", "man", "men",
        "toxic", "costume",
    ],
    "addiction-recovery": [
        "addiction", "alcohol", "sober", "recovery", "drugs", "substance",
        "relapse", "drinking",
    ],
    "science-frequency-integral": [
        "frequency", "quantum", "528", "solfeggio", "schumann", "science",
        "integral", "wilber",
    ],
    "creativity-work": [
        "music", "art", "creative", "brand", "business", "writing", "song",
        "design", "work",
    ],
    "presence-mind": [
        "presence", "ego", "mindfulness", "awareness", "attention", "phone",
        "distraction", "meditation",
    ],
    "relationships-community": [
        "relationship", "community", "friend", "partner", "connection",
        "marriage", "love",
    ],
}


@dataclass
class Turn:
    sec: int
    speaker: str
    text: str

    @property
    def ts(self) -> str:
        return fmt_ts(self.sec)


@dataclass
class Clip:
    sec: int
    title: str
    short_summary: str = ""
    long_summary: str = ""
    topic_tags: list[str] = field(default_factory=list)
    host_open: bool = False
    source: str = "rebuild"

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


def parse_existing_chapters(md: str) -> list[tuple[int, str]]:
    m = CHAP_SEC_RE.search(md)
    if not m:
        return []
    out = []
    for cm in CHAP_MD_RE.finditer(m.group(1)):
        out.append(
            (
                parse_ts_parts(cm.group(1), cm.group(2), cm.group(3)),
                html_lib.unescape(cm.group(4).strip()),
            )
        )
    return out


def nearest_turn_sec(sec: int, turn_secs: list[int], max_delta: int = 90) -> int | None:
    if not turn_secs:
        return None
    best = min(turn_secs, key=lambda t: abs(t - sec))
    if abs(best - sec) <= max_delta:
        return best
    if abs(best - sec) <= 180:
        return best
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


def soft_asr(turns: list[Turn]) -> bool:
    """Heuristic: soft/noisy ASR → shorter summaries, less invention."""
    if not turns:
        return True
    sample = turns[:80]
    texts = [t.text for t in sample if t.text]
    if not texts:
        return True
    avg = sum(len(t.split()) for t in texts) / max(1, len(texts))
    junk = 0
    for t in texts:
        if re.search(r"\b(?:bet though|outie|e son|\*{2,})\b", t, re.I):
            junk += 1
        if len(re.findall(r"[A-Z]{4,}", t)) > 3:
            junk += 1
    return avg < 12 or junk >= max(3, len(texts) // 8)


def detect_bumper_end(turns: list[Turn]) -> int:
    """Return first second of real content after produced Intro bumper."""
    if not turns:
        return 0
    intro_secs = [t.sec for t in turns if t.speaker.lower() == "intro"]
    if intro_secs:
        last_intro = max(intro_secs)
        # content starts at next non-Intro turn after last Intro
        for t in turns:
            if t.sec > last_intro and t.speaker.lower() != "intro":
                return t.sec
        return last_intro
    # No Intro diarization: detect bumper-like early host/system text
    for t in turns[:12]:
        if t.sec > 90:
            break
        if BUMPER_TEXT_RE.search(t.text) and len(t.text) < 500:
            # if next turns still bumper-ish, keep going
            continue
        # first substantial non-bumper
        if t.sec <= 45 and BUMPER_TEXT_RE.search(t.text):
            continue
    # Conservative: if first turn is pure welcome bumper line, skip it
    first = turns[0]
    if first.speaker.lower() == "intro":
        return turns[1].sec if len(turns) > 1 else first.sec
    if first.sec <= 20 and BUMPER_TEXT_RE.search(first.text) and len(first.text) < 400:
        for t in turns[1:]:
            if not BUMPER_TEXT_RE.search(t.text) or len(t.text) > 200:
                return t.sec
    return 0


def detect_outro_start(turns: list[Turn]) -> int | None:
    if not turns:
        return None
    last = turns[-1].sec
    cutoff = max(0, last - max(180, int(last * 0.08)))
    strong: list[Turn] = []
    weak: list[Turn] = []
    for t in turns:
        if t.sec < cutoff:
            continue
        if not HOST_RE.match(t.speaker) and t.speaker.lower() != "outro":
            continue
        if OUTRO_STRONG_RE.search(t.text):
            strong.append(t)
        elif OUTRO_RE.search(t.text):
            weak.append(t)
    pool = strong or weak
    if pool:
        end = pool[-1]
        start = end
        for t in reversed(pool):
            if end.sec - t.sec <= 75:
                start = t
            else:
                break
        return start.sec
    # labeled Outro speaker
    for t in reversed(turns):
        if t.speaker.lower() == "outro":
            return t.sec
    return None


def detect_host_open(
    turns: list[Turn], bumper_end: int, is_solo: bool
) -> tuple[int, int] | None:
    """Return (start, end) of Jacob-alone host open after bumper, if meaningful."""
    if is_solo:
        # Solo: first content stretch after bumper is host open until ~first topic beat
        # Mark first ~2–8 min after bumper as host open window for the first clip only.
        start = bumper_end
        end_candidates = [t.sec for t in turns if t.sec > start + 90]
        if not end_candidates:
            return None
        # End at ~3–8 minutes or first major shift — use 4 min default cap
        end = min(start + 8 * 60, turns[-1].sec)
        # Prefer a natural break near 2–5 min
        for t in turns:
            if start + 120 <= t.sec <= start + 5 * 60:
                if re.search(
                    r"\b(?:so today|this episode|i want to talk|let'?s talk|"
                    r"i'?ve been thinking|the reason)\b",
                    t.text,
                    re.I,
                ):
                    end = t.sec
                    break
        if end - start >= 60:
            return (start, end)
        return None

    jacob_start = None
    first_guest = None
    for t in turns:
        if t.sec < bumper_end:
            continue
        if t.speaker.lower() in ("intro", "outro"):
            continue
        if HOST_RE.match(t.speaker):
            if jacob_start is None:
                jacob_start = t.sec
        else:
            first_guest = t.sec
            break
    if jacob_start is None or first_guest is None:
        return None
    start = max(jacob_start, bumper_end)
    if first_guest - start >= 90:
        return (start, first_guest)
    return None


def window_turns(turns: list[Turn], t0: int, t1: int) -> list[Turn]:
    w = [t for t in turns if t0 <= t.sec < t1]
    if w:
        return w
    return [t for t in turns if t0 - 20 <= t.sec < t1 + 20]


def sentences_from_turns(turns_in: list[Turn], max_chars: int = 4000) -> list[str]:
    blob = " ".join(t.text for t in turns_in)
    blob = re.sub(r"\s+", " ", blob).strip()
    if not blob:
        return []
    # Soft split on punctuation / conjunction pauses
    parts = re.split(r"(?<=[\.\!\?])\s+|(?<=\b)\s+(?=(?:so|and then|but|because)\b)", blob)
    out = []
    total = 0
    for p in parts:
        p = p.strip(" ,;:-")
        if len(p) < 28:
            continue
        # drop pure filler
        if re.fullmatch(r"(?:yeah|right|okay|ok|um+|uh+|mm+)[\.\!]?", p, re.I):
            continue
        out.append(p)
        total += len(p)
        if total >= max_chars:
            break
    return out


def score_sentence(s: str) -> float:
    words = clean_words(s)
    score = min(len(words), 24) * 0.4
    if "?" in s:
        score += 2
    if re.search(
        r"\b(?:because|when i|i realized|i learned|the thing|what happens|"
        r"practice|breath|father|healing|trauma|meditation|ego|presence)\b",
        s,
        re.I,
    ):
        score += 3
    if len(s) > 220:
        score -= 2
    if len(s) < 40:
        score -= 3
    return score


def pick_sentences(sents: list[str], n: int) -> list[str]:
    if not sents:
        return []
    ranked = sorted(enumerate(sents), key=lambda iv: score_sentence(iv[1]), reverse=True)
    chosen_idx = sorted(i for i, _ in ranked[:n])
    return [sents[i] for i in chosen_idx]


def tidy_sentence(s: str) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"^(?:and|but|so|because)\s+", "", s, flags=re.I)
    if s and s[0].islower():
        s = s[0].upper() + s[1:]
    if s and s[-1] not in ".!?":
        s += "."
    # trim length
    if len(s) > 220:
        s = s[:217].rsplit(" ", 1)[0] + "…"
    return s


def label_from_window(
    turns: list[Turn], t0: int, t1: int, about_toks: set[str], guest_name: str = ""
) -> str:
    window = [t for t in turns if t0 <= t.sec < t1 and len(t.text) >= 30]
    if not window:
        window = [t for t in turns if t0 - 20 <= t.sec < t1 + 20 and len(t.text) >= 20]
    if not window:
        return "Conversation continues"

    guest_turns = [t for t in window if not HOST_RE.match(t.speaker) and t.speaker.lower() not in ("intro", "outro")]
    pool = guest_turns if guest_turns else window
    win_low = " ".join(t.text for t in pool).lower()
    win_words = clean_words(win_low)
    freq: dict[str, int] = {}
    for w in win_words:
        if len(w) < 4:
            continue
        if about_toks and w not in about_toks and w not in {
            "breath", "ego", "father", "trauma", "healing", "meditation",
            "yoga", "anxiety", "presence", "gratitude", "surrender",
            "frequency", "breathwork", "masculinity", "vulnerability",
        }:
            # still allow high-frequency local words
            pass
        freq[w] = freq.get(w, 0) + 1

    # Boost about tokens
    for w in list(freq):
        if w in about_toks:
            freq[w] += 2

    top = [w for w, _ in sorted(freq.items(), key=lambda kv: (-kv[1], -len(kv[0]), kv[0]))[:6]]
    # Prefer phrase-like title from top words
    if len(top) >= 3:
        return title_case_label(f"{top[0]}, {top[1]} & {top[2]}")[:72]
    if len(top) == 2:
        return title_case_label(f"{top[0]} / {top[1]}")[:72]
    if len(top) == 1:
        return title_case_label(top[0])[:72]
    return "Conversation continues"


def is_blob_title(title: str) -> bool:
    t = title.strip()
    # strip Host open prefix for blob check on the substance
    t2 = re.sub(r"^host open\s*[—\-–:]\s*", "", t, flags=re.I).strip()
    # "Opening — concrete topic…" with enough substance is NOT a blob
    if re.match(r"^(?:intro|opening|open|welcome)\s*[—\-–:]", t2, re.I):
        rest = re.split(r"[—\-–:]", t2, maxsplit=1)[-1].strip()
        rest_words = re.findall(r"[A-Za-z0-9']+", rest)
        if len(rest_words) >= 3 and not re.search(r"\bbumper\b|theme song", rest, re.I):
            return False
    words = re.findall(r"[A-Za-z0-9']+", t2)
    if len(words) <= 2 and BLOB_TITLE_RE.match(t2):
        return True
    # One-word titles: only treat as blob when generic (Breath/Chat/Practice list)
    if len(words) == 1:
        return bool(BLOB_TITLE_RE.match(t2))
    if WEAK_OPEN_RE.match(t2) and len(words) <= 3:
        return True
    return False


def is_bumper_label(title: str) -> bool:
    t = title.strip()
    if BUMPER_LABEL_RE.match(t):
        # Allow "Opening — specific topic" that isn't bumper-only
        if re.search(r"[—\-–:]", t):
            rest = re.split(r"[—\-–:]", t, maxsplit=1)[-1].strip()
            words = re.findall(r"[A-Za-z0-9']+", rest)
            if len(words) >= 3 and not re.search(r"\bbumper\b|theme song|welcome to the junkyard", rest, re.I):
                return False
        return True
    if re.search(r"welcome to the junkyard love", t, re.I) and len(t) < 70:
        return True
    if re.search(r"\bhost bumper\b|\bjunkyard love bumper\b", t, re.I):
        return True
    return False


def is_outro_label(title: str) -> bool:
    return bool(OUTRO_LABEL_RE.search(title))


def grounded_tokens(content_dir: Path) -> set[str]:
    toks: set[str] = set()
    for name in ("source-about.md", "source-description.md", "source-youtube-title.txt"):
        p = content_dir / name
        if p.exists():
            for w in clean_words(p.read_text(encoding="utf-8", errors="replace")):
                if len(w) >= 4:
                    toks.add(w)
    picks = content_dir / "source-archive-picks.md"
    if picks.exists():
        md = picks.read_text(encoding="utf-8", errors="replace")
        km = re.search(r"^## Keywords\s*\n+(.*?)(?=^## |\Z)", md, re.M | re.S)
        if km:
            for w in clean_words(km.group(1)):
                if len(w) >= 4:
                    toks.add(w)
    return toks


def make_summaries(
    turns: list[Turn],
    t0: int,
    t1: int,
    *,
    guest: str,
    browse_title: str,
    ep_num: str,
    title: str,
    host_open: bool,
    is_solo: bool,
    soft: bool,
) -> tuple[str, str]:
    w = window_turns(turns, t0, t1)
    sents = sentences_from_turns(w, max_chars=3500 if not soft else 1800)
    n_short = 1 if soft else 2
    n_long = 3 if soft else 5
    short_bits = [tidy_sentence(s) for s in pick_sentences(sents, n_short)]
    if not short_bits:
        who = "Jacob" if (host_open or is_solo) else (guest or "the guest")
        short = f"{who} covers {title.lower().rstrip('.')} in this stretch."
    else:
        short = " ".join(short_bits[:2])

    long_bits = [tidy_sentence(s) for s in pick_sentences(sents, n_long)]
    # Frame without hype
    frame = []
    who = "Jacob (solo)" if is_solo else (guest or "the guest")
    ep_ref = f"Episode {ep_num}"
    if browse_title:
        ep_ref += f" — {browse_title}"
    if host_open and is_solo:
        frame.append(
            f"Host open on {ep_ref}: Jacob opens the solocast and sets what he wants to cover."
        )
    elif host_open:
        frame.append(
            f"Host open on {ep_ref}: Jacob talks alone before the guest joins."
        )
    else:
        frame.append(f"This stretch of {ep_ref} with {who} focuses on {title.rstrip('.')}."
        )
    # Add grounded sentences
    for s in long_bits:
        if s.lower() not in short.lower() or soft:
            frame.append(s)
        if len(frame) >= (4 if soft else 6):
            break
    if len(frame) < 3 and short_bits:
        for s in short_bits:
            if s not in frame:
                frame.append(s)
    # why keep listening — grounded, not hype
    speakers = {t.speaker for t in w if t.speaker.lower() not in ("intro", "outro")}
    if host_open and is_solo:
        frame.append(
            "Stay for the setup: Jacob names the commitments and themes he wants to review."
        )
    elif host_open:
        frame.append(
            "Stay for the setup: Jacob names what the episode is circling before the guest joins."
        )
    elif len(speakers) >= 2:
        frame.append(
            f"Keep listening for how {who} and Jacob trade the next beat of the conversation."
        )
    else:
        frame.append("Keep listening as this beat continues from the transcript.")
    long = " ".join(frame[: 4 if soft else 6])
    return short, long


def topic_tags_for(
    ep_topics: list[dict], title: str, short: str, long: str
) -> list[str]:
    tags = []
    for t in ep_topics or []:
        slug = t.get("slug") if isinstance(t, dict) else None
        if slug and slug not in tags:
            tags.append(slug)
    blob = f"{title} {short} {long}".lower()
    for slug, kws in TOPIC_KEYWORDS.items():
        if slug in tags:
            continue
        if any(kw in blob for kw in kws):
            tags.append(slug)
        if len(tags) >= 5:
            break
    return tags[:5]


def find_split_points(
    turns: list[Turn], t0: int, t1: int, max_splits: int = 2
) -> list[int]:
    """Find subject-change beats inside a long blob window."""
    duration = t1 - t0
    if duration < 5 * 60:
        return []
    # Aim for ~4–6 min segments
    target = max(3 * 60, min(6 * 60, duration // (max_splits + 1)))
    candidates = []
    for t in turns:
        if t.sec <= t0 + 90 or t.sec >= t1 - 90:
            continue
        # Jacob questions / topic pivots
        if HOST_RE.match(t.speaker) and (
            "?" in t.text
            or re.search(
                r"\b(?:tell me about|what about|how do you|can you talk|"
                r"let'?s (?:talk|shift|move)|another thing|switching|"
                r"on the topic|speaking of)\b",
                t.text,
                re.I,
            )
        ):
            candidates.append(t.sec)
        elif not HOST_RE.match(t.speaker) and re.search(
            r"\b(?:the other thing|what changed|years later|growing up|"
            r"my practice|the practice|my father|my dad)\b",
            t.text,
            re.I,
        ):
            candidates.append(t.sec)

    if not candidates:
        # Uniform midpoints
        points = []
        cur = t0 + target
        while cur < t1 - 90 and len(points) < max_splits:
            ns = nearest_turn_sec(cur, [t.sec for t in turns], max_delta=120)
            if ns and t0 + 90 < ns < t1 - 90:
                points.append(ns)
            cur += target
        return points[:max_splits]

    # Greedy pick spaced candidates
    picks = []
    for c in candidates:
        if all(abs(c - p) >= target * 0.7 for p in picks):
            picks.append(c)
        if len(picks) >= max_splits:
            break
    return picks


def rebuild_episode_clips(
    turns: list[Turn],
    existing: list[tuple[int, str]],
    *,
    about_toks: set[str],
    guest: str,
    browse_title: str,
    ep_num: str,
    is_solo: bool,
    duration: int,
    ep_topics: list[dict],
) -> list[Clip]:
    if not turns:
        return []
    turn_secs = [t.sec for t in turns]
    last_turn = turns[-1].sec
    runtime = max(duration or 0, last_turn)
    bumper_end = detect_bumper_end(turns)
    outro_start = detect_outro_start(turns)
    content_end = outro_start if outro_start is not None else last_turn
    host_open_range = detect_host_open(turns, bumper_end, is_solo)
    soft = soft_asr(turns)

    # Seed from existing chapters
    seeded: list[tuple[int, str]] = []
    seen: set[int] = set()
    produced_bumper = bumper_end > 0
    for sec, title in existing:
        if is_outro_label(title):
            continue
        if outro_start is not None and sec >= outro_start - 10:
            continue
        # Drop produced bumper chapters only when Intro bumper exists
        if produced_bumper and is_bumper_label(title) and sec <= bumper_end + 30:
            continue
        if produced_bumper and sec < bumper_end - 5 and is_bumper_label(title):
            continue
        ns = nearest_turn_sec(sec, turn_secs, max_delta=120)
        if ns is None:
            continue
        # Snap chapters that sit inside produced bumper forward
        if produced_bumper and ns < bumper_end:
            ns = nearest_turn_sec(bumper_end, turn_secs, max_delta=30) or bumper_end
        if ns in seen:
            continue
        if ns >= content_end:
            continue
        # Bare Intro/Opening with no produced bumper → keep clock, retitle later
        if (not produced_bumper) and is_bumper_label(title) and not re.search(r"[—\-–:]", title):
            title = "Opening"
        seeded.append((ns, title))
        seen.add(ns)

    # Ensure a first content chapter after bumper
    if not seeded or seeded[0][0] > bumper_end + 120:
        start = nearest_turn_sec(bumper_end, turn_secs, max_delta=60) or bumper_end
        if start not in seen and start < content_end:
            seeded.insert(0, (start, "Opening"))
            seen.add(start)
            seeded.sort(key=lambda x: x[0])

    # Host open: ensure chapter at host-open start
    if host_open_range:
        ho_start, ho_end = host_open_range
        ns = nearest_turn_sec(ho_start, turn_secs, max_delta=60) or ho_start
        if ns not in seen and ns < content_end:
            seeded.append((ns, "Host open"))
            seen.add(ns)
            seeded.sort(key=lambda x: x[0])
        # Relabel nearest chapter at/near host open
        for i, (sec, title) in enumerate(seeded):
            if abs(sec - ns) <= 45 or (ho_start <= sec < ho_end and i == 0):
                # build real title from Jacob's open
                topic = label_from_window(turns, sec, min(ho_end, sec + 4 * 60), about_toks, guest)
                if topic.lower() in ("conversation continues", "opening"):
                    topic = label_from_window(turns, ho_start, ho_end, about_toks, guest)
                seeded[i] = (sec, f"Host open — {topic}")
                break

    # Split long blob chapters
    expanded: list[tuple[int, str]] = []
    for i, (sec, title) in enumerate(seeded):
        end = seeded[i + 1][0] if i + 1 < len(seeded) else content_end
        dur = end - sec
        if dur >= 5 * 60 and is_blob_title(title):
            splits = find_split_points(turns, sec, end, max_splits=2 if dur >= 12 * 60 else 1)
            points = [sec] + splits
            for j, p in enumerate(points):
                p_end = points[j + 1] if j + 1 < len(points) else end
                if j == 0 and not is_blob_title(title) and not WEAK_OPEN_RE.match(title):
                    lab = title
                else:
                    lab = label_from_window(turns, p, p_end, about_toks, guest)
                    if title.lower().startswith("host open") and j == 0:
                        lab = title if "—" in title else f"Host open — {lab}"
                if p not in {e[0] for e in expanded}:
                    expanded.append((p, lab))
        else:
            # Improve weak titles even if not long
            lab = title
            words_n = len(re.findall(r"[A-Za-z0-9']+", title))
            # Keep concrete existing titles (incl. "Opening — topic…" with substance)
            has_dash_topic = bool(re.search(r"[—\-–:]", title)) and words_n >= 4
            keep_existing = (not is_blob_title(title)) and (
                has_dash_topic
                or (words_n >= 5 and not WEAK_OPEN_RE.match(title))
                or (words_n >= 4 and not title.lower().startswith(("intro", "opening", "open ", "welcome")))
            )
            if keep_existing:
                lab = title
            elif is_blob_title(title) or WEAK_OPEN_RE.match(title):
                if title.lower().startswith("host open") and "—" in title:
                    lab = title
                else:
                    new_lab = label_from_window(turns, sec, end, about_toks, guest)
                    if title.lower().startswith("host open"):
                        lab = f"Host open — {new_lab}"
                    else:
                        lab = new_lab
            expanded.append((sec, lab))

    expanded.sort(key=lambda x: x[0])
    # Dedupe close clocks
    final_seed: list[tuple[int, str]] = []
    for sec, title in expanded:
        if final_seed and sec - final_seed[-1][0] < 45:
            # keep the more specific title
            if is_blob_title(final_seed[-1][1]) and not is_blob_title(title):
                final_seed[-1] = (final_seed[-1][0], title)
            continue
        final_seed.append((sec, title))

    # Drop any remaining bumper/outro
    cleaned: list[tuple[int, str]] = []
    for sec, title in final_seed:
        if is_outro_label(title):
            continue
        if is_bumper_label(title) and sec <= bumper_end + 45:
            continue
        if outro_start is not None and sec >= outro_start:
            continue
        cleaned.append((sec, title))

    if not cleaned:
        # Fallback: at least one clip from content start
        start = nearest_turn_sec(bumper_end, turn_secs) or bumper_end
        cleaned = [(start, label_from_window(turns, start, min(content_end, start + 300), about_toks, guest))]

    # Build Clip objects with summaries
    clips: list[Clip] = []
    for i, (sec, title) in enumerate(cleaned):
        end = cleaned[i + 1][0] if i + 1 < len(cleaned) else content_end
        if end <= sec:
            end = min(runtime, sec + 120)
        host_open = bool(
            title.lower().startswith("host open")
            or (
                host_open_range
                and host_open_range[0] <= sec < host_open_range[1]
                and i == 0
            )
        )
        # Normalize host open title
        if host_open and not title.lower().startswith("host open"):
            topic = label_from_window(turns, sec, min(end, sec + 240), about_toks, guest)
            title = f"Host open — {topic}"
        short, long = make_summaries(
            turns,
            sec,
            end,
            guest=guest,
            browse_title=browse_title,
            ep_num=ep_num,
            title=title,
            host_open=host_open,
            is_solo=is_solo,
            soft=soft,
        )
        tags = topic_tags_for(ep_topics, title, short, long)
        clips.append(
            Clip(
                sec=sec,
                title=title[:90],
                short_summary=short,
                long_summary=long,
                topic_tags=tags,
                host_open=host_open,
            )
        )
    return clips


def chapters_to_md(clips: list[Clip]) -> str:
    lines = ["## Chapter-style timestamps", ""]
    for c in clips:
        lines.append(f"- [{c.ts}](#{c.anchor}) — {c.title}")
    lines.append("")
    return "\n".join(lines)


def replace_md_chapters(md: str, clips: list[Clip]) -> str:
    block = chapters_to_md(clips)
    if re.search(r"^## Chapter-style timestamps\s*$", md, re.M):
        return re.sub(
            r"^## Chapter-style timestamps\s*\n(?:.*?\n)*?(?=^## |\Z)",
            block + "\n",
            md,
            count=1,
            flags=re.M,
        )
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


def chapters_to_html(clips: list[Clip], use_ts_class: bool) -> str:
    parts = []
    for c in clips:
        label = html_lib.escape(c.title, quote=False)
        if use_ts_class:
            parts.append(
                f'<li><a class="ts" href="#{c.anchor}">[{c.ts}]</a> — {label}</li>'
            )
        else:
            parts.append(f'<li><a href="#{c.anchor}">{c.ts}</a> — {label}</li>')
    return "\n".join(parts)


def replace_html_chapters(html: str, clips: list[Clip]) -> str:
    use_ts = html_has_ts_class(html)
    new_ul_inner = chapters_to_html(clips, use_ts)
    pattern = re.compile(
        r"(<h3>Chapter-style timestamps</h3>\s*<ul class=\"(?:archive-)?chapters\">\s*)(.*?)(\s*</ul>)",
        re.S,
    )
    m = pattern.search(html)
    if m:
        return html[: m.start(2)] + new_ul_inner + html[m.end(2) :]
    ap = html.find("Archive picks")
    if ap >= 0:
        pattern2 = re.compile(r"(<ul class=\"chapters\">\s*)(.*?)(\s*</ul>)", re.S)
        m2 = pattern2.search(html, ap)
        if m2:
            return html[: m2.start(2)] + new_ul_inner + html[m2.end(2) :]
    return html


def ensure_anchors(html: str, clips: list[Clip]) -> str:
    existing = set(re.findall(r'id="(t-\d{2}-\d{2}-\d{2})"', html))
    cue_re = re.compile(r'<p class="cue" id="(t-\d{2}-\d{2}-\d{2})"')
    cue_ids = [(m.start(), m.group(1)) for m in cue_re.finditer(html)]

    def id_to_sec(tid: str) -> int:
        _, h, m, s = tid.split("-")
        return int(h) * 3600 + int(m) * 60 + int(s)

    inserts: list[tuple[int, str]] = []
    for c in clips:
        if c.anchor in existing:
            continue
        if not cue_ids:
            continue
        nearest = min(cue_ids, key=lambda x: abs(id_to_sec(x[1]) - c.sec))
        if abs(id_to_sec(nearest[1]) - c.sec) > 180:
            continue
        span = (
            f'<span id="{c.anchor}" class="t-anchor" hidden '
            f'data-chapter-anchor="1"></span>\n'
        )
        inserts.append((nearest[0], span))
        existing.add(c.anchor)
    if not inserts:
        return html
    inserts.sort(key=lambda x: x[0], reverse=True)
    out = html
    for pos, span in inserts:
        out = out[:pos] + span + out[pos:]
    return out


def write_timestamps(path: Path, clips: list[Clip]) -> None:
    lines = [
        "(Archive picks chapter/clip list — regenerable via rebuild_clips_index.py)",
        "",
    ]
    for c in clips:
        lines.append(f"- [{c.ts}](#{c.anchor}) — {c.title}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


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
    # unnumbered published slugs
    for n, slug in {
        "0118": "what-if-mania-is-a-message-sean-blackwell",
        "0120": "im-not-a-teacher-david-hulse",
        "0121": "surrendering-the-porsche-tim-fraley",
    }.items():
        p = EPISODES / slug
        if p.is_dir() and (p / "index.html").exists():
            out[n] = p
    return out


def load_index() -> dict:
    path = SOURCES / "episodes_index.json"
    return json.loads(path.read_text(encoding="utf-8"))


def process_all(only: set[str] | None = None, dry_run: bool = False) -> dict:
    idx = load_index()
    content_map = map_content_dirs()
    ep_dirs = map_episode_dirs()
    episodes = idx.get("episodes") or []
    by_num = {e["number"]: e for e in episodes}

    all_clips = []
    report_rows = []
    hard_notes = []
    host_open_count = 0
    rebuilt = 0

    nums = sorted(by_num.keys())
    for num in nums:
        if num in REMOVED:
            continue
        if only and num not in only:
            continue
        ep = by_num[num]
        cdir = content_map.get(num)
        edir = ep_dirs.get(num)
        if not cdir or not edir:
            hard_notes.append(f"{num}: missing content or episode dir")
            continue
        tp = cdir / "transcript.md"
        if not tp.exists():
            hard_notes.append(f"{num}: no transcript.md")
            continue
        turns = parse_turns(tp.read_text(encoding="utf-8", errors="replace"))
        if not turns:
            hard_notes.append(f"{num}: empty transcript turns")
            continue

        picks_path = cdir / "source-archive-picks.md"
        md = picks_path.read_text(encoding="utf-8", errors="replace") if picks_path.exists() else ""
        existing = parse_existing_chapters(md)
        # fallback to episodes_index chapters
        if not existing:
            for ch in ep.get("chapters") or []:
                existing.append((int(ch.get("start_seconds") or 0), ch.get("title") or "Chapter"))

        about_toks = grounded_tokens(cdir)
        clips = rebuild_episode_clips(
            turns,
            existing,
            about_toks=about_toks,
            guest=ep.get("guest") or "",
            browse_title=ep.get("browse_title") or "",
            ep_num=num,
            is_solo=bool(ep.get("is_solo")),
            duration=int(ep.get("duration_seconds") or 0),
            ep_topics=ep.get("topics") or [],
        )

        # Apply hand title overrides (nearest clip within 45s)
        ov = TITLE_OVERRIDES.get(num) or {}
        for sec_key, new_title in ov.items():
            best_i = None
            best_d = 46
            for i, c in enumerate(clips):
                d = abs(c.sec - int(sec_key))
                if d < best_d:
                    best_d = d
                    best_i = i
            if best_i is not None:
                clips[best_i].title = new_title[:90]
                # refresh summaries lightly with new title framing
                end = clips[best_i + 1].sec if best_i + 1 < len(clips) else (
                    detect_outro_start(turns) or turns[-1].sec
                )
                s, l = make_summaries(
                    turns,
                    clips[best_i].sec,
                    end,
                    guest=ep.get("guest") or "",
                    browse_title=ep.get("browse_title") or "",
                    ep_num=num,
                    title=clips[best_i].title,
                    host_open=clips[best_i].host_open,
                    is_solo=bool(ep.get("is_solo")),
                    soft=soft_asr(turns),
                )
                clips[best_i].short_summary = s
                clips[best_i].long_summary = l

        soft = soft_asr(turns)
        ho_n = sum(1 for c in clips if c.host_open)
        host_open_count += ho_n
        if soft:
            hard_notes.append(f"{num}: soft ASR — shorter summaries")
        if len(clips) < 5 and (ep.get("duration_seconds") or 0) > 40 * 60:
            hard_notes.append(f"{num}: only {len(clips)} clips for long episode")
        # Known hard clocks / caption gaps
        if num == "0103":
            hard_notes.append(
                "0103: caption clocks stop ~01:34 while inventory duration ~1:48 — coverage capped by ASR"
            )
        if num == "0102":
            hard_notes.append(
                "0102: published note says solo intro skip @11:03 — host-open/bumper handling may vary"
            )
        # Flag weak auto titles for manual review
        weak_auto = [
            c.title for c in clips
            if re.match(r"^(?:[A-Z][a-z]+,\s+[A-Z][a-z]+\s+&\s+[A-Z][a-z]+)$", c.title)
            and c.host_open
        ]
        if len(weak_auto) >= 1 and num in {"0039", "0047", "0048", "0051"}:
            hard_notes.append(f"{num}: host-open title is keyword-auto — consider hand label later")

        if not dry_run:
            if not picks_path.exists():
                md = (
                    "# Archive picks (not from published notes)\n\n"
                    "Extracted from the transcript and published About already on this episode. "
                    "Labeled separately from Jacob’s published About / Chapters / Quotes / Hashtags.\n\n"
                )
            picks_path.write_text(replace_md_chapters(md, clips), encoding="utf-8")
            write_timestamps(cdir / "source-timestamps.md", clips)

            html_path = edir / "index.html"
            html = html_path.read_text(encoding="utf-8", errors="replace")
            html2 = replace_html_chapters(html, clips)
            html2 = ensure_anchors(html2, clips)
            # Preserve UX hooks
            for needle in ("<!-- topic-chips:start -->", 'class="browse-subtitle"'):
                if needle in html and needle not in html2:
                    hard_notes.append(f"{num}: WARNING lost {needle}; skipping HTML write")
                    html2 = html
                    break
            html_path.write_text(html2, encoding="utf-8")

            # Update episode chapters in index object
            ep["chapters"] = [
                {"start": c.ts, "start_seconds": c.sec, "title": c.title} for c in clips
            ]

        for c in clips:
            all_clips.append(
                {
                    "episode_slug": ep["slug"],
                    "episode_number": num,
                    "browse_title": ep.get("browse_title") or "",
                    "guest": ep.get("guest") or "",
                    "start": c.ts,
                    "start_seconds": c.sec,
                    "title": c.title,
                    "short_summary": c.short_summary,
                    "long_summary": c.long_summary,
                    "topic_tags": c.topic_tags,
                    "youtube_id": ep.get("youtube_id") or None,
                    "host_open": c.host_open,
                }
            )

        rebuilt += 1
        report_rows.append(
            {
                "num": num,
                "slug": ep["slug"],
                "clips": len(clips),
                "host_open": ho_n,
                "soft_asr": soft,
                "first": clips[0].title if clips else "",
                "last": clips[-1].title if clips else "",
            }
        )
        print(f"[{rebuilt}] {num} clips={len(clips)} host_open={ho_n} soft={soft}")

    # When --only, merge into existing clips_index instead of wiping the catalog.
    if only and not dry_run:
        existing_path = SOURCES / "clips_index.json"
        if existing_path.exists():
            prev = json.loads(existing_path.read_text(encoding="utf-8"))
            kept = [
                c for c in (prev.get("clips") or [])
                if str(c.get("episode_number")) not in only
            ]
            all_clips = kept + all_clips
            all_clips.sort(key=lambda c: (c.get("episode_number") or "", c.get("start_seconds") or 0))
            host_open_count = sum(1 for c in all_clips if c.get("host_open"))
            rebuilt = len({c.get("episode_number") for c in all_clips})

    clips_doc = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generator": "rebuild_clips_index.py",
        "episode_count": rebuilt if not only else len({c.get("episode_number") for c in all_clips}),
        "clip_count": len(all_clips),
        "host_open_count": host_open_count,
        "removed_skipped": sorted(REMOVED),
        "clips": all_clips,
        "note": (
            "Each Archive-picks chapter is a clip. Produced intro bumper and "
            "produced outro are excluded. Summaries are grounded in transcript "
            "windows; soft ASR episodes use shorter summaries."
        ),
    }

    if not dry_run:
        idx["generated"] = "clip-index-rebuild"
        idx["clip_index"] = "assets/clips_index.json"
        # When --only, idx already has full chapters from load; we updated only selected eps.
        (SOURCES / "episodes_index.json").write_text(
            json.dumps(idx, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        (ASSETS / "episodes_index.json").write_text(
            json.dumps(idx, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        (SOURCES / "clips_index.json").write_text(
            json.dumps(clips_doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        (ASSETS / "clips_index.json").write_text(
            json.dumps(clips_doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )

        REPORTS.mkdir(parents=True, exist_ok=True)
        report_path = REPORTS / "CLIP_INDEX_REBUILD_REPORT.md"
        lines = [
            "# Clip index rebuild report",
            "",
            f"**Date:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} "
            f"(convert −5h for America/Chicago)",
            f"**Script:** `_sources/rebuild_clips_index.py`",
            "**No git commit / no push.**",
            "",
            "## Summary",
            "",
            f"| Metric | Value |",
            f"|---|---:|",
            f"| Episodes rebuilt | **{rebuilt}** |",
            f"| Total clips | **{len(all_clips)}** |",
            f"| Host-open clips | **{host_open_count}** |",
            f"| Removed skipped | {', '.join(sorted(REMOVED))} |",
            "",
            "## Deliverables",
            "",
            "- `_sources/clips_index.json` + `assets/clips_index.json`",
            "- `_sources/episodes_index.json` + `assets/episodes_index.json` (chapters match clips)",
            "- Archive picks chapter lists on every episode page",
            "- `source-archive-picks.md` + `source-timestamps.md` per episode",
            "",
            "## Rules applied",
            "",
            "- Every chapter treated as a clip",
            "- Produced intro bumper + produced outro excluded",
            "- Host open labeled with real topic titles (not “intro”)",
            "- Long one-word blob chapters split into tighter beats",
            "- Short/long summaries paraphrased from transcript windows (no invented quotes)",
            "",
            "## Hard / soft ASR notes",
            "",
        ]
        if hard_notes:
            for n in hard_notes:
                lines.append(f"- {n}")
        else:
            lines.append("- (none)")
        lines.extend(["", "## Per-episode clip counts", "", "| Ep | Clips | Host open | First clip | Last clip |", "|---|---:|---:|---|---|"])
        for r in report_rows:
            lines.append(
                f"| {r['num']} | {r['clips']} | {r['host_open']} | "
                f"{r['first'][:48]} | {r['last'][:48]} |"
            )
        lines.extend(
            [
                "",
                "## How to regenerate",
                "",
                "```bash",
                "cd junkyard-love-archive-deploy",
                "python3 _sources/rebuild_clips_index.py",
                "# optional: python3 _sources/rebuild_clips_index.py --only 0002,0124",
                "```",
                "",
                "## Confirm",
                "",
                "- **No git commit / no push.**",
                "",
            ]
        )
        report_path.write_text("\n".join(lines), encoding="utf-8")

    return {
        "rebuilt": rebuilt,
        "clips": len(all_clips),
        "host_open": host_open_count,
        "hard_notes": hard_notes,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="", help="Comma-separated episode numbers")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    only = {x.strip() for x in args.only.split(",") if x.strip()} or None
    result = process_all(only=only, dry_run=args.dry_run)
    print(json.dumps({k: result[k] for k in ("rebuilt", "clips", "host_open")}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
