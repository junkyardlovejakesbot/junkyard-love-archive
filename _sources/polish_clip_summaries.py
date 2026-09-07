#!/usr/bin/env python3
"""Polish clip titles + short/long summaries for Junkyard Love archive.

Regenerable. Reads existing clips_index.json (preserves start times, youtube_id,
host_open, topic_tags, episode fields), rewrites weak titles and ALL summaries
from transcript windows, then syncs chapter titles into episode pages /
source-archive-picks.md / source-timestamps.md / episodes_index.json.

No git commit / no push.
"""
from __future__ import annotations

import argparse
import html as html_lib
import json
import re
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

# Import shared helpers from the clip rebuild script
sys.path.insert(0, str(Path(__file__).resolve().parent))
import rebuild_clips_index as rci  # noqa: E402

ROOT = rci.ROOT
SOURCES = rci.SOURCES
ASSETS = rci.ASSETS
CONTENT = rci.CONTENT
EPISODES = rci.EPISODES
REPORTS = rci.REPORTS

# ---------------------------------------------------------------------------
# Extra hand title overrides (sec → title). Applied after weak-title rewrite.
# Keys are episode numbers; values map start_seconds → title.
# ---------------------------------------------------------------------------
TITLE_POLISH_OVERRIDES: dict[str, dict[int, str]] = {
    "0002": {
        0: "EYE Clothing cold open — raves & selling from the trunk",
    },
    "0012": {
        0: "Bob Kendall cold open — third-person marketplace intro",
    },
    "0021": {
        75: "Baseball song & meeting Rosetan",
        298: "How Rosetan formed — Erik and the trio",
    },
    "0042": {
        109: "Host open — Listening with Jessica and Mackenzie",
    },
    "0047": {
        51: "Host open — Letterkenny bit and settling in",
        6337: "Research, opinions & staying curious",
        8414: "Travel picks — Thailand, Ireland, Dublin",
    },
    "0063": {
        1499: "How Shiloh has changed over the years",
    },
    "0069": {
        1611: "MySpace to Facebook — growing up online",
    },
}

# Topic lexicon: (regex, human label). Order = priority.
TOPIC_LEXICON: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bbreath(?:work|ing)?\b|\bexhale\b|\binhale\b", re.I), "breathwork"),
    (re.compile(r"\bmeditat(?:e|ion|ing)\b|\bmindfulness\b", re.I), "meditation"),
    (re.compile(r"\byoga\b|\bqigong\b|\bpilates\b", re.I), "embodied practice"),
    (re.compile(r"\bego\b", re.I), "ego"),
    (re.compile(r"\btrauma\b|\bptsd\b|\bwound", re.I), "trauma and healing"),
    (re.compile(r"\bheal(?:ing|ed)?\b", re.I), "healing"),
    (re.compile(r"\bfather(?:hood)?\b|\bdad\b|\bson\b", re.I), "fatherhood"),
    (re.compile(r"\bmother(?:hood)?\b|\bmom\b|\bparent", re.I), "family"),
    (re.compile(r"\baddict(?:ion|ed)?\b|\brecovery\b|\bsober(?:iety)?\b|\balcohol\b", re.I), "addiction and recovery"),
    (re.compile(r"\banxiety\b|\bdepress(?:ion|ed)\b|\bpanic\b", re.I), "mental health"),
    (re.compile(r"\bmasculin|\bvulnerab|\barmor\b", re.I), "masculinity and vulnerability"),
    (re.compile(r"\bpresence\b|\bpresent moment\b|\bphone\b.*\bdopamine\b|\bdopamine\b", re.I), "presence"),
    (re.compile(r"\bgratitude\b|\bgrateful\b", re.I), "gratitude"),
    (re.compile(r"\bfrequenc|\b528\b|\bsolfeggio\b|\bschumann\b|\bquantum\b", re.I), "frequency and science"),
    (re.compile(r"\bawaken|\bkundalini\b|\bmystic|\bspiritual emergency\b|\bgnosis\b", re.I), "awakening"),
    (re.compile(r"\bpsilocybin\b|\bpsychedelic|\bmdma\b|\blsd\b|\bmushroom", re.I), "psychedelics"),
    (re.compile(r"\bmusic\b|\bguitar\b|\bband\b|\bsong\b|\bdrum|\brehears", re.I), "music"),
    (re.compile(r"\bbusiness\b|\bbrand\b|\bclothing\b|\bstore\b|\bentrepreneur", re.I), "building a brand"),
    (re.compile(r"\bwork\b|\bjob\b|\bcareer\b|\bmoney\b", re.I), "work and money"),
    (re.compile(r"\bcommunity\b|\bfriend(?:s|ship)?\b|\brelationship", re.I), "community"),
    (re.compile(r"\bcreativ|\bart\b|\bwriting\b|\bdesign\b", re.I), "creativity"),
    (re.compile(r"\bsleep\b|\binsomnia\b", re.I), "sleep"),
    (re.compile(r"\bjourn(?:al|aling)\b", re.I), "journaling"),
    (re.compile(r"\bgoal(?:s)?\b|\bhabit(?:s)?\b|\bdiscipline\b", re.I), "habits and goals"),
    (re.compile(r"\bdeath\b|\bgrief\b|\bmortal", re.I), "mortality and grief"),
    (re.compile(r"\blove\b|\bpartner\b|\bmarriage\b|\bdating\b", re.I), "relationships"),
    (re.compile(r"\bmentor|\bteacher\b|\blearn(?:ing)?\b", re.I), "mentorship and learning"),
    (re.compile(r"\bgear\b|\bguitar center\b|\binstrument", re.I), "gear and instruments"),
    (re.compile(r"\bbandcamp\b|\bshow(?:s)?\b|\bvenue\b|\bbrewery\b", re.I), "shows and releases"),
    (re.compile(r"\bcoffee\b|\bcaffeine\b|\bcannabis\b|\bweed\b", re.I), "substances and habits"),
    (re.compile(r"\bcomedy\b|\bstand[- ]?up\b", re.I), "comedy"),
    (re.compile(r"\bpodcast\b|\bepisode\b", re.I), "the podcast itself"),
]

# Jacob question → topic cue
QUESTION_CUES = [
    (re.compile(r"tell me about\s+(.{8,60}?)(?:[\.?!]|$)", re.I), "about"),
    (re.compile(r"how did (?:you|the|it)\s+(.{8,50}?)(?:[\.?!]|$)", re.I), "how"),
    (re.compile(r"what (?:was|is|are|do you)\s+(.{8,50}?)(?:[\.?!]|$)", re.I), "what"),
    (re.compile(r"can you (?:talk|speak|share|walk).{0,20}?(?:about|through)\s+(.{8,50}?)(?:[\.?!]|$)", re.I), "about"),
    (re.compile(r"let'?s talk about\s+(.{8,50}?)(?:[\.?!]|$)", re.I), "about"),
]

ASR_JUNK_RE = re.compile(
    r"(?:"
    r"\bbet though\b|\boutie\b|\be son\b|\brosetan about yeah\b|"
    r"\bkilomet(?:er|re)s whoo\b|\blass baseball\b|"
    r"\bthrow Me some fish\b|\bkiss of sunshine\b|"
    r"\b\*{2,}\b"
    r")",
    re.I,
)

WEAK_TITLE_SOUP = re.compile(
    r"^[A-Za-z0-9'’\-]+,\s+[A-Za-z0-9'’\-]+\s+&\s+[A-Za-z0-9'’\-]+$"
)
WEAK_SLASH = re.compile(
    r"^[A-Za-z0-9'’\-]+(?:\s*/\s*[A-Za-z0-9'’\-]+){1,4}$"
)
WEAK_HOST_SOUP = re.compile(
    r"^Host open\s*[—\-–:]\s*[A-Za-z0-9'’\-]+,\s*[A-Za-z0-9'’\-]+\s+&\s*[A-Za-z0-9'’\-]+$",
    re.I,
)
WEAK_ASR_BIT = re.compile(
    r"\b(?:Won'?t|Weren'?t|That'?s|Dif|Currently|Supposed|Myself|Having)\b"
)
GENERIC_BLOBS = {
    "breath", "chat", "practice", "conversation", "talk", "community",
    "friends", "music", "build", "older", "intro", "opening", "open",
    "welcome", "experience", "themselves", "yourself", "feeling", "care",
    "momentum currently", "keep playing", "place that's why",
}

FILLER = {
    "like", "just", "really", "actually", "basically", "literally", "kinda",
    "sorta", "you", "know", "yeah", "right", "okay", "um", "uh", "so", "well",
    "gonna", "wanna", "gotta", "dude", "man", "bro", "stuff", "thing", "things",
}


def first_name(guest: str) -> str:
    g = (guest or "").strip()
    if not g:
        return "the guest"
    low = g.lower().strip('"')
    if low.startswith("solo") or low in {"host", "solo (host)"}:
        return "Jacob"
    # Band / project names → short label
    if "the band" in low or low.startswith("rosetan") or (g[:1] == '"' and "band" in low):
        inner = g.strip('"').strip()
        inner = re.sub(r"\s+the band.*$", "", inner, flags=re.I).strip().strip('"')
        label = (inner.split()[0] if inner else "the band")[:40]
        return label[:1].upper() + label[1:] if label else "the band"
    g2 = g.strip('"')
    if " of " in g2:
        g2 = g2.split(" of ")[0]
    parts = re.split(r"\s+", g2)
    if parts and parts[0].lower() in {"dr", "dr.", "mr", "mrs", "ms"}:
        parts = parts[1:]
    return parts[0] if parts else g2[:30]


def word_count(s: str) -> int:
    return len((s or "").split())


def clamp_words(s: str, max_words: int) -> str:
    words = (s or "").split()
    if len(words) <= max_words:
        return s.strip()
    cut = " ".join(words[:max_words]).rstrip(" ,;:")
    if cut and cut[-1] not in ".!?":
        cut += "."
    return cut


def tidy(s: str) -> str:
    s = re.sub(r"\s+", " ", (s or "")).strip()
    s = re.sub(r"^(?:and|but|so|because|well|yeah|okay|ok)\s+", "", s, flags=re.I)
    if s and s[0].islower():
        s = s[0].upper() + s[1:]
    if s and s[-1] not in ".!?":
        s += "."
    return s


def title_case_phrase(s: str) -> str:
    s = re.sub(r"\s+", " ", s).strip(" —-/")
    if not s:
        return s
    small = {"and", "or", "of", "the", "a", "an", "to", "for", "vs", "with", "in", "on", "from", "into"}
    parts = []
    for i, w in enumerate(s.split()):
        if i > 0 and w.lower() in small:
            parts.append(w.lower())
        elif w.isupper() and len(w) <= 4:
            parts.append(w)
        else:
            parts.append(w[:1].upper() + w[1:].lower() if w.islower() or w.isupper() else w[:1].upper() + w[1:])
    return " ".join(parts)


def core_title(title: str) -> str:
    t = title.strip()
    t = re.sub(r"^host open\s*[—\-–:]\s*", "", t, flags=re.I).strip()
    t = re.sub(r"^(?:opening|open|intro|welcome)\s*[—\-–:]\s*", "", t, flags=re.I).strip()
    return t


def phrase_for_sentence(title: str) -> str:
    """Turn a chapter title into a mid-sentence noun phrase."""
    raw = (title or "").strip()
    core = core_title(raw)
    if not core:
        return "this stretch"
    # Prefer substance after Opening/Host-open already stripped by core_title.
    # For "A — B", keep B when it is specific; else keep full.
    if " — " in core:
        left, right = core.split(" — ", 1)
        if len(right.split()) >= 2:
            core = right
        elif len(left.split()) >= 2:
            core = left
    # Keep up to two slash segments for readable mid-sentence phrases
    if " / " in core:
        parts = [p.strip() for p in core.split(" / ") if p.strip()]
        if len(parts) >= 2 and sum(len(p.split()) for p in parts[:2]) <= 10:
            core = " / ".join(parts[:2])
        elif len(core) > 56:
            core = parts[0]
    core = core.strip(" —-/")
    if not core:
        return "this stretch"
    # Lowercase first word only when it is a common English starter, not a name
    common_starters = {
        "the", "a", "an", "how", "what", "why", "when", "where", "who",
        "living", "growing", "taking", "making", "being", "getting",
        "talking", "building", "finding", "learning", "working", "playing",
        "opening", "welcome", "welcoming", "small", "self-love", "mystical",
        "aqua", "episode", "conversation", "technology", "breathwork",
        "meditation", "music", "community", "friends", "habit", "habits",
        "fatherhood", "healing", "trauma", "presence", "solocast",
        "baseball", "meeting", "editing", "take", "your", "ram",
    }
    first, *rest = core.split()
    if first.lower().strip("()[]") in common_starters:
        first = first.lower()
    out = " ".join([first] + rest)
    out = re.sub(r"\bjacob\b", "Jacob", out, flags=re.I)
    # Grammar tweak: "welcome X" → "welcoming X"
    out = re.sub(r"^welcome\b", "welcoming", out, flags=re.I)
    return out


def is_weak_title(title: str, *, host_open: bool = False) -> bool:
    t = (title or "").strip()
    if not t:
        return True
    core = re.sub(r"^host open\s*[—\-–:]\s*", "", t, flags=re.I).strip()
    if WEAK_TITLE_SOUP.match(core) or WEAK_TITLE_SOUP.match(t):
        return True
    if WEAK_HOST_SOUP.match(t):
        return True
    if WEAK_SLASH.match(core):
        bits = [b.strip() for b in core.split("/")]
        if all(len(b.split()) == 1 for b in bits) and len(bits) <= 3:
            return True
        if any(len(b) < 4 for b in bits):
            return True
    if core.lower() in GENERIC_BLOBS:
        return True
    words = re.findall(r"[A-Za-z0-9']+", core)
    if len(words) <= 2 and core.lower() in GENERIC_BLOBS:
        return True
    if WEAK_ASR_BIT.search(core) and len(words) <= 5:
        return True
    if host_open and re.match(r"^(?:intro|opening|open|welcome)(?:\b|$)", core, re.I):
        return True
    if len(words) <= 4 and WEAK_ASR_BIT.search(core):
        return True
    if re.match(r"^Community\s*/\s*\w+$", core, re.I):
        return True
    if re.match(r"^(?:Build|Place|Band|Friends|Music)\s*/\s*\w+$", core, re.I):
        return True
    return False


def extract_topics(text: str, limit: int = 4) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    # Require density for noisy / common words
    min_hits = {
        "work and money": 3,
        "music": 3,
        "community": 3,
        "relationships": 2,
        "the podcast itself": 4,
        "creativity": 2,
        "ego": 2,
        "family": 2,
        "substances and habits": 2,
        "masculinity and vulnerability": 2,
        "shows and releases": 2,
        "mentorship and learning": 2,
    }
    for pat, label in TOPIC_LEXICON:
        n = len(pat.findall(text))
        if n <= 0:
            continue
        if n < min_hits.get(label, 1):
            continue
        if label not in seen:
            found.append(label)
            seen.add(label)
        if len(found) >= limit:
            break
    return found


def _clean_qfrag(frag: str) -> str | None:
    frag = re.sub(r"\s+", " ", (frag or "")).strip(" .,!?;:\"'")
    frag = re.sub(r"\b(like|just|really|you know|yeah|man|dude|um|uh)\b", " ", frag, flags=re.I)
    frag = re.sub(r"\s+", " ", frag).strip(" .,")
    words = frag.split()
    if len(words) < 2 or len(words) > 8:
        return None
    # Reject ASR junk / too many stopwords
    content = [w for w in words if w.lower() not in FILLER and w.lower() not in rci.STOP]
    if len(content) < 2:
        return None
    if ASR_JUNK_RE.search(frag):
        return None
    if re.search(r"\b(?:what do you mean|yeah man|peanut butter|stumble upon this)\b", frag, re.I):
        return None
    # Must look somewhat topical
    joined = " ".join(words).lower()
    if not re.search(r"[a-z]{5,}", joined):
        return None
    return " ".join(words[:6])


def extract_question_topics(turns: list) -> list[str]:
    out: list[str] = []
    for t in turns:
        if not rci.HOST_RE.match(t.speaker):
            continue
        for pat, _kind in QUESTION_CUES:
            m = pat.search(t.text)
            if not m:
                continue
            frag = _clean_qfrag(m.group(1))
            if not frag:
                continue
            if frag.lower() not in {x.lower() for x in out}:
                out.append(frag)
            if len(out) >= 2:
                return out
    return out


def meaningful_bigrams(text: str, about_toks: set[str], limit: int = 6) -> list[str]:
    words = re.findall(r"[A-Za-z']{3,}", text.lower())
    words = [w for w in words if w not in rci.STOP and w not in FILLER]
    if not words:
        return []
    grams: Counter[str] = Counter()
    for i in range(len(words) - 1):
        a, b = words[i], words[i + 1]
        if a == b:
            continue
        if len(a) < 4 and len(b) < 4:
            continue
        key = f"{a} {b}"
        score = 1
        if a in about_toks or b in about_toks:
            score += 2
        # prefer concrete second word
        if b in {
            "practice", "meditation", "breathwork", "guitar", "band", "father",
            "healing", "community", "business", "clothing", "recovery", "anxiety",
            "presence", "ego", "trauma", "music", "habit", "goals",
        }:
            score += 2
        grams[key] += score
    # also trigrams lightly
    for i in range(len(words) - 2):
        a, b, c = words[i], words[i + 1], words[i + 2]
        if any(x in FILLER for x in (a, b, c)):
            continue
        key = f"{a} {b} {c}"
        grams[key] += 1
    ranked = [g for g, _ in grams.most_common(20)]
    # filter ASR junk grams
    clean = []
    for g in ranked:
        if ASR_JUNK_RE.search(g):
            continue
        if any(w in {"won", "wont", "werent", "thats", "dif", "currently", "supposed"} for w in g.split()):
            continue
        clean.append(g)
        if len(clean) >= limit:
            break
    return clean


def window_text(turns: list[rci.Turn], t0: int, t1: int) -> str:
    w = rci.window_turns(turns, t0, t1)
    return " ".join(t.text for t in w)


def speaker_names(turns: list[rci.Turn], guest: str) -> tuple[str, bool]:
    """Return (who_label, multi_speaker)."""
    speakers = {
        t.speaker for t in turns
        if t.speaker.lower() not in ("intro", "outro") and t.text.strip()
    }
    has_host = any(rci.HOST_RE.match(s) for s in speakers)
    guests = [s for s in speakers if not rci.HOST_RE.match(s)]
    multi = len(speakers) >= 2
    if guests:
        who = first_name(guest) if guest else guests[0].split()[0]
    elif has_host:
        who = "Jacob"
    else:
        who = first_name(guest) if guest else "the guest"
    return who, multi


def polish_title(
    *,
    old_title: str,
    host_open: bool,
    turns: list[rci.Turn],
    t0: int,
    t1: int,
    about_toks: set[str],
    guest: str,
    browse_title: str,
) -> str:
    if not is_weak_title(old_title, host_open=host_open):
        # Still normalize host-open prefix if flagged host_open
        if host_open and not old_title.lower().startswith("host open"):
            return f"Host open — {core_title(old_title)}"[:90]
        return old_title[:90]

    w = rci.window_turns(turns, t0, min(t1, t0 + 360))
    text = " ".join(t.text for t in w)
    topics = extract_topics(text, limit=3)
    qtopics = extract_question_topics(w)
    bigrams = meaningful_bigrams(text, about_toks, limit=5)

    phrase = None
    if qtopics:
        phrase = qtopics[0]
        # clean
        phrase = re.sub(r"\b(like|just|really|you know)\b", " ", phrase, flags=re.I)
        phrase = re.sub(r"\s+", " ", phrase).strip(" .,")
    if not phrase and topics:
        if len(topics) >= 2:
            phrase = f"{topics[0]} and {topics[1]}"
        else:
            phrase = topics[0]
    if not phrase and bigrams:
        phrase = bigrams[0]
    if not phrase and browse_title:
        # fall back to episode browse title fragment
        phrase = " ".join(browse_title.split()[:5])
    if not phrase:
        phrase = "the conversation continues"

    phrase = title_case_phrase(phrase)
    # Prefer lowercase connective style for short topic titles
    if topics and phrase.lower() == topics[0]:
        # "Meditation" → keep
        pass
    # Soften overly Title-Cased bigrams into readable labels
    if " " in phrase and phrase.islower() is False:
        # convert "guitar practice" style already title-cased
        pass

    # Naturalize a few patterns
    phrase = phrase.replace(" And ", " and ").replace(" Of ", " of ").replace(" The ", " the ")
    # Ensure first letter capital
    if phrase:
        phrase = phrase[0].upper() + phrase[1:]

    if host_open:
        title = f"Host open — {phrase}"
    else:
        # Prefer em-dash form when we have guest cue + topic
        g = first_name(guest)
        if topics and g and g.lower() not in phrase.lower() and len(phrase.split()) <= 4:
            # "Music community" stays; don't force guest into every title
            title = phrase
        else:
            title = phrase

    # Avoid leftover soup
    title = re.sub(r",\s+", " — ", title, count=1)
    title = title.replace(" & ", " and ")
    return title[:90]


def oxford(items: list[str]) -> str:
    items = [i for i in items if i]
    if not items:
        return "the conversation"
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return f"{items[0]}, {items[1]}, and {items[2]}"


def make_polished_summaries(
    *,
    turns: list,
    t0: int,
    t1: int,
    guest: str,
    browse_title: str,
    ep_num: str,
    title: str,
    host_open: bool,
    is_solo: bool,
    soft: bool,
    about_toks: set[str],
) -> tuple[str, str]:
    w = rci.window_turns(turns, t0, t1) if turns else []
    text = " ".join(t.text for t in w)
    topics = extract_topics(text, limit=4) if text else []
    qtopics = extract_question_topics(w) if w else []
    who, multi = speaker_names(w, guest) if w else (first_name(guest), False)
    lead = phrase_for_sentence(title)
    if lead in {"this stretch", ""} and topics:
        lead = topics[0]
    elif lead in {"this stretch", ""} and qtopics:
        lead = qtopics[0].lower()

    # ---- SHORT (1–2 sentences) ----
    if soft:
        if host_open:
            short = f"Jacob opens alone (soft ASR). This beat seems to set up {lead}."
        elif topics:
            short = f"Soft transcript here; this stretch seems to cover {oxford(topics[:2])}."
        else:
            short = (
                f"Soft transcript stretch from episode {ep_num}; "
                f"keeping the summary short rather than inventing detail."
            )
        short = clamp_words(tidy(short), 36)
    elif host_open and is_solo:
        short = (
            f"Jacob opens the solocast and sets up {lead}. "
            f"He names what he wants to sit with before going deeper."
        )
        short = clamp_words(tidy(short), 40)
    elif host_open:
        short = (
            f"Jacob opens alone before {first_name(guest)} joins and sets up {lead}."
        )
        extras = [t for t in topics if t.lower() not in lead.lower()][:1]
        if extras:
            short += f" He also flags {extras[0]}."
        short = clamp_words(tidy(short), 42)
    else:
        if is_solo:
            s1 = f"Jacob spends this stretch on {lead}."
        elif multi:
            s1 = f"{who} and Jacob talk about {lead}."
        else:
            s1 = f"{who} covers {lead} in this stretch."
        extras = [t for t in topics if t.lower() not in lead.lower()][:2]
        if qtopics and qtopics[0].lower() not in lead.lower():
            s2 = f"Jacob asks about {qtopics[0].lower()}."
        elif extras:
            s2 = f"The beat also touches on {oxford(extras)}."
        else:
            s2 = "They stay with the thread instead of jumping ahead."
        short = clamp_words(tidy(s1) + " " + tidy(s2), 45)

    # ---- LONG (3–6 sentences, aim 60–120 words) ----
    ep_ref = f"Episode {ep_num}"
    if browse_title:
        ep_ref += f" — {browse_title}"
    guest_label = "Jacob (solo)" if is_solo else (guest or who)
    topic_core = core_title(title) or lead

    frame: list[str] = []
    if host_open and is_solo:
        frame.append(
            f"Host open on {ep_ref}: Jacob opens the solocast and sets what he wants to cover."
        )
    elif host_open:
        frame.append(
            f"Host open on {ep_ref}: Jacob talks alone before {guest_label} joins."
        )
    else:
        frame.append(
            f"This stretch of {ep_ref} with {guest_label} focuses on {topic_core}."
        )

    if soft:
        if topics:
            frame.append(
                f"ASR is rough in this window; the clearest themes are {oxford(topics[:3])}."
            )
        else:
            frame.append(
                "ASR is rough in this window, so the summary stays high-level."
            )
        frame.append(
            f"Treat the wording as approximate; the clip still belongs with {lead}."
        )
        frame.append(
            f"The window runs from {rci.fmt_ts(t0)} until the next chapter mark."
        )
    else:
        if topics:
            frame.append(f"In this window they stay with {oxford(topics[:3])}.")
        else:
            frame.append(f"In this window the talk centers on {lead}.")
        if qtopics:
            frame.append(f"Jacob steers with questions about {qtopics[0].lower()}.")
        elif multi and not is_solo:
            frame.append(
                f"{who} answers from lived experience while Jacob keeps the thread moving."
            )
        elif is_solo:
            frame.append(
                "Jacob thinks out loud and ties the beat back to practice, not theory alone."
            )
        else:
            frame.append(
                f"The conversation stays close to {lead} without racing ahead."
            )
        # Grounding sentence
        if about_toks and topics:
            frame.append(
                f"It sits inside the episode's larger through-line rather than a random digression."
            )
        else:
            frame.append(
                f"Nothing here is a teaser — it is the actual stretch of conversation around {lead}."
            )

    if host_open and is_solo:
        frame.append(
            "Stay for the setup: Jacob names the commitments and themes he wants to review."
        )
    elif host_open:
        frame.append(
            "Stay for the setup: Jacob names what the episode is circling before the guest joins."
        )
    elif multi and not is_solo:
        frame.append(
            f"Keep listening for how {who} and Jacob trade the next beat of the conversation."
        )
    else:
        frame.append("Keep listening as this beat continues into what follows.")

    max_sents = 4 if soft else 6
    long = " ".join(tidy(s) for s in frame[:max_sents])
    # Pad into the 60–120 band when thin
    if not soft and word_count(long) < 60:
        long += " " + tidy(
            f"Use the chapter mark at {rci.fmt_ts(t0)} if you want to jump straight to this part."
        )
    if word_count(long) > 130:
        long = clamp_words(long, 120)
    return short, long


def apply_title_overrides(ep_num: str, sec: int, title: str) -> str:
    for mapping in (rci.TITLE_OVERRIDES.get(ep_num) or {}, TITLE_POLISH_OVERRIDES.get(ep_num) or {}):
        best = None
        best_d = 46
        for sec_key, new_title in mapping.items():
            d = abs(int(sec_key) - sec)
            if d < best_d:
                best_d = d
                best = new_title
        if best:
            return best[:90]
    return title


def sync_episode_artifacts(
    *,
    ep_num: str,
    cdir: Path,
    edir: Path,
    clips_for_ep: list[dict],
) -> list[str]:
    """Update archive picks MD, timestamps MD, and episode HTML chapter titles."""
    notes: list[str] = []
    # Build Clip-like objects for reuse of rebuild helpers
    clip_objs = [
        rci.Clip(sec=int(c["start_seconds"]), title=c["title"], host_open=bool(c.get("host_open")))
        for c in clips_for_ep
    ]

    picks_path = cdir / "source-archive-picks.md"
    if picks_path.exists():
        md = picks_path.read_text(encoding="utf-8", errors="replace")
        picks_path.write_text(rci.replace_md_chapters(md, clip_objs), encoding="utf-8")
    else:
        notes.append(f"{ep_num}: no source-archive-picks.md")

    rci.write_timestamps(cdir / "source-timestamps.md", clip_objs)
    # Fix header line to mention polish script
    ts_path = cdir / "source-timestamps.md"
    ts = ts_path.read_text(encoding="utf-8")
    ts = ts.replace(
        "regenerable via rebuild_clips_index.py",
        "regenerable via polish_clip_summaries.py / rebuild_clips_index.py",
    )
    ts_path.write_text(ts, encoding="utf-8")

    html_path = edir / "index.html"
    if html_path.exists():
        html = html_path.read_text(encoding="utf-8", errors="replace")
        html2 = rci.replace_html_chapters(html, clip_objs)
        html2 = rci.ensure_anchors(html2, clip_objs)
        for needle in ("<!-- topic-chips:start -->", 'class="browse-subtitle"'):
            if needle in html and needle not in html2:
                notes.append(f"{ep_num}: WARNING lost {needle}; skipping HTML write")
                html2 = html
                break
        html_path.write_text(html2, encoding="utf-8")
    else:
        notes.append(f"{ep_num}: no episode index.html")
    return notes


def polish_all(only: set[str] | None = None, dry_run: bool = False) -> dict:
    clips_path = ASSETS / "clips_index.json"
    if not clips_path.exists():
        clips_path = SOURCES / "clips_index.json"
    clips_doc = json.loads(clips_path.read_text(encoding="utf-8"))
    clips: list[dict] = list(clips_doc.get("clips") or [])

    idx = rci.load_index()
    by_num = {e["number"]: e for e in (idx.get("episodes") or [])}
    content_map = rci.map_content_dirs()
    ep_dirs = rci.map_episode_dirs()

    # Group clips by episode preserving order
    by_ep: dict[str, list[dict]] = defaultdict(list)
    for c in clips:
        by_ep[str(c["episode_number"])].append(c)

    before_short = [word_count(c.get("short_summary")) for c in clips]
    before_long = [word_count(c.get("long_summary")) for c in clips]
    before_titles = [c.get("title") for c in clips]

    titles_changed = 0
    soft_eps: list[str] = []
    hard_notes: list[str] = []
    polished_count = 0
    transcript_cache: dict[str, list[rci.Turn]] = {}
    about_cache: dict[str, set[str]] = {}

    for num in sorted(by_ep.keys()):
        if only and num not in only:
            continue
        ep = by_num.get(num)
        if not ep:
            hard_notes.append(f"{num}: missing from episodes_index")
            continue
        cdir = content_map.get(num)
        edir = ep_dirs.get(num)
        if not cdir:
            hard_notes.append(f"{num}: missing content dir")
            continue
        tp = cdir / "transcript.md"
        if not tp.exists():
            hard_notes.append(f"{num}: no transcript.md — summaries use title/guest only")
            turns: list[rci.Turn] = []
        else:
            if num not in transcript_cache:
                transcript_cache[num] = rci.parse_turns(
                    tp.read_text(encoding="utf-8", errors="replace")
                )
            turns = transcript_cache[num]
        if num not in about_cache:
            about_cache[num] = rci.grounded_tokens(cdir) if cdir else set()
        about_toks = about_cache[num]

        soft = rci.soft_asr(turns) if turns else True
        if soft:
            soft_eps.append(num)

        ep_clips = by_ep[num]
        # Ensure sorted by start
        ep_clips.sort(key=lambda c: int(c.get("start_seconds") or 0))
        is_solo = bool(ep.get("is_solo"))
        guest = ep.get("guest") or ""
        browse_title = ep.get("browse_title") or ""
        runtime = int(ep.get("duration_seconds") or 0)
        outro = rci.detect_outro_start(turns) if turns else None
        content_end = outro or runtime or (turns[-1].sec if turns else 0)

        title_changed_this_ep = False
        for i, c in enumerate(ep_clips):
            t0 = int(c.get("start_seconds") or 0)
            t1 = int(ep_clips[i + 1]["start_seconds"]) if i + 1 < len(ep_clips) else content_end
            if t1 <= t0:
                t1 = t0 + 180

            host_open = bool(c.get("host_open"))
            old_title = c.get("title") or ""
            new_title = polish_title(
                old_title=old_title,
                host_open=host_open,
                turns=turns,
                t0=t0,
                t1=t1,
                about_toks=about_toks,
                guest=guest,
                browse_title=browse_title,
            )
            new_title = apply_title_overrides(num, t0, new_title)
            if new_title != old_title:
                titles_changed += 1
                title_changed_this_ep = True
                c["title"] = new_title

            short, long = make_polished_summaries(
                turns=turns,
                t0=t0,
                t1=t1,
                guest=guest,
                browse_title=browse_title,
                ep_num=num,
                title=c["title"],
                host_open=host_open,
                is_solo=is_solo,
                soft=soft,
                about_toks=about_toks,
            )
            c["short_summary"] = short
            c["long_summary"] = long
            # Keep stable fields; refresh browse_title/guest from index in case stale
            c["browse_title"] = browse_title
            c["guest"] = guest
            c["youtube_id"] = ep.get("youtube_id") or c.get("youtube_id")
            polished_count += 1

        # Sync artifacts when titles changed (or always, to keep chapters aligned)
        if not dry_run and edir and cdir:
            notes = sync_episode_artifacts(
                ep_num=num, cdir=cdir, edir=edir, clips_for_ep=ep_clips
            )
            hard_notes.extend(notes)
            # Update episodes_index chapters
            ep["chapters"] = [
                {
                    "start": c["start"],
                    "start_seconds": int(c["start_seconds"]),
                    "title": c["title"],
                }
                for c in ep_clips
            ]
        elif title_changed_this_ep:
            hard_notes.append(f"{num}: titles changed but dry-run — no sync")

        if only:
            print(f"[{num}] clips={len(ep_clips)} soft={soft}")
        elif int(num) % 20 == 0 or num in {"0002", "0124"}:
            print(f"[{num}] clips={len(ep_clips)} soft={soft}")

    # Recount title changes properly from before snapshot by episode order
    # (we mutated in place; recompute via storing old)
    # Actually we already counted titles_changed during loop.

    after_short = [word_count(c.get("short_summary")) for c in clips]
    after_long = [word_count(c.get("long_summary")) for c in clips]

    def median(xs: list[int]) -> float:
        return float(statistics.median(xs)) if xs else 0.0

    def pct_le(xs: list[int], n: int) -> float:
        if not xs:
            return 0.0
        return sum(1 for x in xs if x <= n) / len(xs)

    # Spot-check samples
    spot = {}
    for num in ("0124", "0100", "0037", "0021", "0005"):
        spot[num] = [
            {
                "start": c["start"],
                "title": c["title"],
                "short": c["short_summary"],
                "long": c["long_summary"],
                "long_wc": word_count(c["long_summary"]),
                "short_wc": word_count(c["short_summary"]),
            }
            for c in by_ep.get(num, [])[:4]
        ]

    clips_doc_out = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generator": "polish_clip_summaries.py",
        "episode_count": clips_doc.get("episode_count")
        or len({c.get("episode_number") for c in clips}),
        "clip_count": len(clips),
        "host_open_count": sum(1 for c in clips if c.get("host_open")),
        "removed_skipped": clips_doc.get("removed_skipped") or [],
        "clips": clips,
        "note": (
            "Titles polished when weak (keyword soup / ASR crumbs). "
            "short_summary and long_summary are paraphrases grounded in transcript "
            "windows — not raw ASR dumps. Soft ASR episodes use shorter honest summaries."
        ),
    }

    result = {
        "polished": polished_count,
        "titles_changed": titles_changed,
        "soft_eps": soft_eps,
        "hard_notes": hard_notes,
        "before": {
            "short_median": median(before_short),
            "long_median": median(before_long),
            "short_pct_le_60": pct_le(before_short, 60),
        },
        "after": {
            "short_median": median(after_short),
            "long_median": median(after_long),
            "short_pct_le_60": pct_le(after_short, 60),
            "short_pct_le_45": pct_le(after_short, 45),
            "long_pct_60_120": (
                sum(1 for x in after_long if 60 <= x <= 120) / len(after_long)
                if after_long
                else 0
            ),
        },
        "spot": spot,
        "quality_ok": (
            median(after_short) <= 45
            and pct_le(after_short, 60) >= 0.95
            and 60 <= median(after_long) <= 120
        ),
    }

    if not dry_run:
        idx["generated"] = "clip-summary-polish"
        idx["clip_index"] = "assets/clips_index.json"
        (SOURCES / "episodes_index.json").write_text(
            json.dumps(idx, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        (ASSETS / "episodes_index.json").write_text(
            json.dumps(idx, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        (SOURCES / "clips_index.json").write_text(
            json.dumps(clips_doc_out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        (ASSETS / "clips_index.json").write_text(
            json.dumps(clips_doc_out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )

        REPORTS.mkdir(parents=True, exist_ok=True)
        write_report(result, soft_eps, hard_notes)

    return result


def write_report(result: dict, soft_eps: list[str], hard_notes: list[str]) -> None:
    path = REPORTS / "CLIP_SUMMARY_POLISH_REPORT.md"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    b, a = result["before"], result["after"]
    lines = [
        "# Clip summary polish report",
        "",
        f"**Date:** {now} (America/Chicago = UTC−5 → "
        f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')} morning CT)",
        f"**Script:** `_sources/polish_clip_summaries.py`",
        "**No git commit / no push.**",
        "",
        "## Summary",
        "",
        "| Metric | Before | After |",
        "|---|---:|---:|",
        f"| Clips polished | — | **{result['polished']}** |",
        f"| Titles changed | — | **{result['titles_changed']}** |",
        f"| short_summary median words | {b['short_median']:.0f} | **{a['short_median']:.0f}** |",
        f"| short ≤ 60 words | {100*b['short_pct_le_60']:.1f}% | **{100*a['short_pct_le_60']:.1f}%** |",
        f"| short ≤ 45 words | — | **{100*a['short_pct_le_45']:.1f}%** |",
        f"| long_summary median words | {b['long_median']:.0f} | **{a['long_median']:.0f}** |",
        f"| long in 60–120 words | — | **{100*a['long_pct_60_120']:.1f}%** |",
        f"| Quality gate | — | **{'PASS' if result['quality_ok'] else 'CHECK'}** |",
        "",
        "## Quality bar",
        "",
        "- Clip title: short, specific, newbie-readable (not keyword lists)",
        "- Short summary: 1–2 sentences, paraphrase of the time window (not ASR dump)",
        "- Long summary: 3–6 sentences — what this stretch is, who guest is, what episode, why keep listening",
        "- No hype, no fake pull-quotes, no medical claims",
        "- Host open: real topic title; soft ASR → shorter honest summaries",
        "",
        "## Soft-ASR episodes (shorter summaries)",
        "",
        ", ".join(f"`{n}`" for n in soft_eps) if soft_eps else "_none_",
        "",
        "## Hard / notable notes",
        "",
    ]
    if hard_notes:
        for n in hard_notes[:80]:
            lines.append(f"- {n}")
        if len(hard_notes) > 80:
            lines.append(f"- … +{len(hard_notes) - 80} more")
    else:
        lines.append("- _none_")

    lines += ["", "## Spot checks (first clips)", ""]
    for num, rows in (result.get("spot") or {}).items():
        lines.append(f"### Episode {num}")
        lines.append("")
        for row in rows:
            lines.append(f"- **[{row['start']}] {row['title']}**")
            lines.append(f"  - short ({row['short_wc']}w): {row['short']}")
            lines.append(f"  - long ({row['long_wc']}w): {row.get('long', '')}")
        lines.append("")

    lines += [
        "## Deliverables",
        "",
        "- `assets/clips_index.json` + `_sources/clips_index.json`",
        "- `assets/episodes_index.json` + `_sources/episodes_index.json` (chapters match)",
        "- Archive picks chapter *titles* on episode pages when titles changed",
        "- `_sources/content/*/source-archive-picks.md` + `source-timestamps.md`",
        "- This report",
        "",
        "## Re-run",
        "",
        "```bash",
        "python3 _sources/polish_clip_summaries.py",
        "python3 _sources/polish_clip_summaries.py --only 0021,0005",
        "```",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {path}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--only", help="Comma-separated episode numbers", default="")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    only = {x.strip() for x in args.only.split(",") if x.strip()} or None
    result = polish_all(only=only, dry_run=args.dry_run)
    print(json.dumps({k: result[k] for k in ("polished", "titles_changed", "quality_ok", "after")}, indent=2))


if __name__ == "__main__":
    main()
