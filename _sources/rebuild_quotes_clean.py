#!/usr/bin/env python3
"""QUOTE REBUILD — stand-alone complete quotes for all published episodes.

Updates:
  - _sources/content/*/source-archive-picks.md Memorable quotes
  - episodes/*/index.html archive-quote blockquotes
  - _sources/quotes_clean.json + assets/quotes_clean.json (homepage rotator pool)
  - assets/episodes_index.json + _sources/episodes_index.json quote fields

Rules (Jacob):
  - Complete grammatical thought with clear beginning and end
  - Makes sense with zero episode context
  - Not ASR garbage / mid-clause / filler
  - Has speaker + episode
  - Prefer claim / story beat / practice
  - Prefer 3–8 strong quotes/ep; quality over volume
  - Do NOT invent quotes; do NOT rewrite published About
  - Soft ASR (0020, 0025, 0037, 0047): only clearly complete thoughts
  - Skip removed 0001/0014/0016/0029
  - No git commit/push
"""
from __future__ import annotations

import argparse
import html as html_lib
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = Path(__file__).resolve().parent / "content"
EPISODES = ROOT / "episodes"
ASSETS = ROOT / "assets"
SOURCES = Path(__file__).resolve().parent
WORK_MIRROR_CONTENT = Path("/workspace/junkyard-love-archive/content")

SOFT_ASR = {"0020", "0025", "0037", "0047"}
REMOVED = {"0001", "0014", "0016", "0029"}

# Content dirs without leading episode number
SPECIAL_CONTENT = {
    "0118": "sean-blackwell-mania-is-a-message",
    "0120": "david-hulse-path-to-no-path",
    "0121": "tim-fraley-surrendering-the-porsche",
}

HOST_RE = re.compile(r"^(jacob|host|intro|outro)\b", re.I)
TURN_RE = re.compile(r"^\[(\d{2}):(\d{2}):(\d{2})\]\s+([^:\n]+):\s*(.*)$", re.M)
ARCHIVE_QUOTE_LINE = re.compile(
    r"^- \[(\d{2}):(\d{2}):(\d{2})\]\s+([^:]+):\s+[“\"](.+?)[”\"]\s*$"
)

BAD_END = {
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
    "stuff", "number", "first", "oh", "it's", "thats", "i'm", "you're",
    "we're", "they're", "he's", "she's", "there's", "that's", "what's",
    "here's", "who's", "ain't", "can't", "don't", "didn't", "isn't",
    "wasn't", "weren't", "won't", "wouldn't", "shouldn't", "couldn't",
    "matter", "same", "behind", "compound", "ask", "call", "called",
    "go", "create", "learn", "practice", "better", "guitar", "song",
    "band", "things", "thing", "way", "ways", "part", "parts", "kind",
    "sorts", "into", "onto", "toward", "towards", "across", "along",
    "during", "before", "after", "until", "unless", "although", "though",
    "whether", "either", "neither", "nor", "both", "each", "every",
    "few", "many", "much", "several", "all", "half", "least", "less",
    "enough", "too", "also", "only", "almost", "already", "always",
    "never", "often", "sometimes", "usually", "probably", "maybe",
    "perhaps", "actually", "basically", "literally", "honestly",
    "exactly", "absolutely", "totally", "pretty", "super", "kinda",
    "sorta", "cause", "'cause", "cuz", "cos", "well", "now", "then",
    "here", "there", "again", "once", "twice", "next", "last",
    "know", "think", "mean", "says", "said", "tell", "told", "see",
    "saw", "look", "looks", "feel", "feels", "want", "wants", "need",
    "needs", "try", "tries", "start", "starts", "begin", "begins",
    "stop", "stops", "keep", "keeps", "give", "gives", "take", "takes",
    "make", "makes", "get", "gets", "come", "comes", "bring", "brings",
    "find", "finds", "use", "uses", "show", "shows", "help", "helps",
    "allow", "allows", "become", "becomes", "seem", "seems", "happen",
    "happens", "include", "includes", "provide", "provides",
}

# Ending words that CAN close a complete thought (override BAD_END when scored high)
OK_END_OVERRIDE = {
    "love", "life", "truth", "fear", "hope", "peace", "heart", "soul",
    "mind", "body", "breath", "home", "work", "art", "music", "path",
    "practice", "habit", "choice", "choices", "freedom", "courage",
    "kindness", "compassion", "gratitude", "presence", "awareness",
    "consciousness", "healing", "growth", "change", "identity", "purpose",
    "meaning", "vision", "dream", "community", "connection", "relationship",
    "relationships", "friendship", "family", "father", "mother", "child",
    "children", "people", "world", "universe", "god", "spirit", "self",
    "yourself", "myself", "ourselves", "themselves", "everyone", "anybody",
    "nobody", "someone", "everyone", "wholeness", "authenticity", "integrity",
    "humility", "accountability", "responsibility", "boundaries", "permission",
    "meditation", "nature", "silence", "stillness", "surrender", "acceptance",
    "forgiveness", "resilience", "empathy", "vulnerability", "discipline",
    "consistency", "patience", "listening", "observation", "communication",
    "friend", "exhale", "inhale", "day", "night", "moment", "time",
    "pain", "joy", "grief", "anger", "shame", "trauma", "addiction",
    "sobriety", "recovery", "depression", "anxiety", "ego", "shadow",
    "light", "darkness", "mirror", "teacher", "student", "mentor",
    "lesson", "gift", "tool", "practice", "ritual", "prayer",
    "water", "fire", "earth", "air", "space", "energy", "frequency",
    "tone", "key", "wholeness", "whole", "enough", "human", "humans",
    "adults", "narcissism", "muscle", "intuition", "channel", "divine",
    "serious", "yourself", "heart", "head", "intellect", "meditation",
    "feel", "felt", "work", "need", "needs", "change", "stronger", "control",
    "passion", "passions", "calling", "amnesia", "itself", "muscle",
    "enough", "soul", "ego", "worthy", "heavy", "vessel", "artist",
    "creations", "shine", "grounded", "reality", "nature", "peace",
    "excellence", "boss", "together", "music", "vision", "guitar",
    "rehearsal", "song", "time", "myself", "listening",
    "humanity", "excellence", "vision", "designs", "meaning", "seed", "mind",
    "mates", "together", "words", "outsider", "fame", "reality", "platform",
    "generations", "instruments", "followers", "brewery", "bandcamp",
    "encouraging", "responsibility", "patience", "honest", "honesty",
    "steel", "producers", "engineers", "feeling", "space", "charming",
    "library", "album", "presence", "torch", "self-worth", "worth",
    "friends", "friendship", "leader", "man", "men", "women", "artists",
    "musicians", "musician", "song", "songs", "shows", "show", "stage",
    "rehearsal", "rehearsals", "practice", "practices", "guitar", "piano",
    "mentor", "mentors", "teachers", "teacher", "lessons", "lesson",
    "tabs", "tablature", "chords", "scales", "chord", "scale",
    "future", "past", "present", "mirror", "beliefs", "belief",
    "experiences", "experience", "bushwhack", "truth", "jerk",
    "small", "loved", "hate", "hated", "depression", "anxiety",
    "meditation", "fasting", "body", "past", "machine", "clean",
    "neuroscience", "psychology", "question", "questions", "answer",
    "science", "idea", "ideas", "disorder", "illness", "awakening",
    "delusions", "delusion", "storm", "whispers", "buried",
}

BAD_START = {
    "and", "but", "or", "so", "because", "which", "who", "whom", "where",
    "when", "than", "that", "of", "to", "for", "with", "from", "into",
    "mm-hmm", "mm", "uh", "um", "yeah", "yep", "yup", "okay", "ok", "right",
    "exactly", "absolutely", "totally", "much", "well", "us", "me", "him",
    "them", "her", "his", "its", "doing", "hasn't", "can't", "don't",
    "didn't", "isn't", "wasn't", "weren't", "get", "got", "bad", "similarly",
    "just", "lot", "work", "thing", "things", "designs", "company",
    "necessary", "trying", "part", "up", "out", "off", "down", "back",
    "even", "also", "actually", "basically", "literally", "honestly",
    "say", "said", "like", "cause", "'cause", "cuz",
    "surrendered", "started", "wanted", "needed", "tried", "learned",
    "planting", "meaning", "comparing", "operating", "taught", "teaching",
    "thinking", "keeping", "living", "taking", "going", "being", "becoming",
    "putting", "giving", "coming", "letting", "feeling", "knowing", "seeing",
    "hearing", "talking", "speaking", "telling", "asking", "working",
    "growing", "changing", "healing", "believing", "realizing", "listening",
    "building", "finding", "helping", "loving", "using", "sharing",
    "bringing", "leaving", "moving", "surrounded", "consistent",
}

FILLER_RE = re.compile(
    r"\b(?:uh+|um+|mm-?hmm|you know|i mean|kind of|sort of|kinda|sorta)\b",
    re.I,
)
LIKE_RE = re.compile(r"\blike\b", re.I)
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
    r"deal|dealt|shift|shifted|matter|matters|"
    r"trigger|triggers|triggered|separate|separates|separated|"
    r"slow|slows|slowed|set|sets|setting|trust|trusts|trusted|"
    r"exercise|exercises|exercised|create|creates|"
    r"refuse|refuses|refused|whisper|whispers|whispered|"
    r"surround|surrounds|surrounded|ignore|ignores|ignored|"
    r"encourage|encourages|encouraged|deserve|deserves|deserved|"
    r"enjoy|enjoys|enjoyed|hang|hangs|hung|play|plays|played|"
    r"write|writes|wrote|written|read|reads|speak|speaks|spoke|"
    r"break|breaks|broke|broken|release|releases|released|"
    r"awaken|awakens|awakened|dream|dreams|dreamed|"
    r"surrender|surrenders|surrendered|accept|accepts|accepted|"
    r"practice|practices|practiced|breathe|breathes|breathed)\b",
    re.I,
)
INSIGHT_RE = re.compile(
    r"\b(?:because|realize|realized|truth|learn|learned|lesson|practice|habit|"
    r"heal|healing|grow|growth|change|mindset|ego|fear|love|kindness|"
    r"listen|listening|compassion|vulnerable|vulnerability|courage|"
    r"discipline|consistency|vision|dream|purpose|meaning|identity|belief|"
    r"meditation|breath|breathe|nature|community|connection|forgiveness|gratitude|"
    r"resilience|empathy|create|creator|compound|diamond|garden|"
    r"responsibility|choice|choose|chosen|benevolence|educator|"
    r"insight|sobriety|trauma|depression|anxiety|relationship|marriage|"
    r"consciousness|spirit|soul|awareness|presence|patience|"
    r"accountability|humility|integrity|boundaries|permission|"
    r"cornerstone|communication|observation|authenticity|wholeness|"
    r"surrender|intuition|narcissism|willpower|empathy|standards|"
    r"mentor|teacher|musician|music|band|guitar|encourage|encouraging|"
    r"frequency|exhale|inhale|heart|intellect|divine|channel)\b",
    re.I,
)
FLUFF_RE = re.compile(
    r"\b(?:welcome to (?:the )?junkyard|peace out|see you next|"
    r"thanks for (?:coming|being|listening|joining)|like and subscribe|"
    r"follow us on|smash that|don't forget to)\b",
    re.I,
)
ASR_SALAD_RE = re.compile(
    r"\b(?:i get see|learn about things that like learn|things these|"
    r"would ignore my guitar for a few hours and bike okay|"
    r"necessary things how a mentor|"
    r"you can call[.!?]?$|"
    r"first thing we ask[.!?]?$|"
    r"the reason i chose to go[.!?]?$|"
    r"earning your excellence is the compound[.!?]?$)\b",
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
    r"Just|Only|Even|Still|Now|Yes|No|Thank|Thanks|"
    r"Comparing|Am|There|In|On|Going|Own|Take|Taking|Living|"
    r"Planting|Taught|Teaching|Thinking|Keep|Keeping|Hard|"
    r"Breath|Authenticity|Victim|Empathy|Your|Pray|Don't|He|"
    r"Hearts|Breakdowns|The|People)\b"
)

# Patterns that indicate mid-clause / incomplete despite terminal punct
INCOMPLETE_TAIL_RE = re.compile(
    r"(?:"
    r"\b(?:to|for|with|from|into|onto|about|because|than|that|which|who|when|where|if|and|or|but|so|like)\s*$|"
    r"\b(?:i'm|you're|we're|they're|it's|that's|there's|what's)\s*$|"
    r"\b(?:the|a|an)\s+\w+\s*$|"  # weak: "the compound" alone may be ok if insight — handled elsewhere
    r"\bso (?:the|a|an|i|you|we|they|he|she)\b.*$"  # often truncated second clause started with so
    r")",
    re.I,
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


def normalize_words(s: str) -> list[str]:
    s = s.lower().replace("'", "'").replace("'", "'").replace("'", "'")
    s = re.sub(r"[^a-z0-9'\s]+", " ", s)
    return [w for w in s.split() if w]


def _ascii_apos(s: str) -> str:
    return s.replace("'", "'").replace("'", "'").replace("'", "'").replace("'", "'")


def last_word(text: str) -> str:
    text = _ascii_apos(text)
    words = re.findall(r"[A-Za-z0-9']+", text)
    return words[-1].lower() if words else ""


def first_word(text: str) -> str:
    text = _ascii_apos(text)
    words = re.findall(r"[A-Za-z0-9']+", text)
    return words[0].lower() if words else ""


def strip_attribution(q: str) -> str:
    q = re.sub(r"\s*[—–-]\s*[A-Z][^“”\"]{0,60}$", "", q).strip()
    return q.strip(" \"'“”")


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


def parse_published_quotes(path: Path) -> list[str]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    if not text or "none published" in text.lower():
        return []
    # Skip inventory-note-only files without real quote lines
    out = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("(") and "inventory" in line.lower():
            continue
        line = re.sub(r"^\s*[-*]\s*", "", line)
        q = strip_attribution(line.strip().strip("“”\"'"))
        q = re.sub(r"\s+", " ", q).strip()
        # skip meta notes
        if "inventory has_quotes" in q.lower():
            continue
        if len(q) >= 12 and not q.lower().startswith("(none"):
            out.append(q)
    return out


def is_complete_thought(text: str, *, published: bool = False, soft: bool = False) -> bool:
    """Strict: must stand alone with zero episode context."""
    text = text.strip()
    if not text:
        return False
    # normalize fancy punct
    text = text.replace("…", "...")
    words = text.split()
    nw = len(words)
    if nw < 6:
        # allow short published aphorisms that clearly end
        if published and 4 <= nw <= 5 and re.search(r"[.!?]$", text) and text[0].isupper():
            lw = last_word(text.rstrip(".!?"))
            if lw not in BAD_END or lw in OK_END_OVERRIDE:
                return True
        return False
    if nw > 48:
        return False
    if not text[0].isupper() and text[0] not in "\"“'":
        return False
    fw = first_word(text)
    if fw in BAD_START:
        return False
    core = text.rstrip(".!?…,;:—–- ")
    lw = last_word(core)
    if lw in BAD_END and lw not in OK_END_OVERRIDE:
        # allow published copula closers: "the stronger it is."
        if not (published and lw in {"is", "are", "was", "were", "be"} and len(text.split()) >= 8):
            return False
    verb_hits = VERB_RE.findall(text)
    if not verb_hits:
        return False
    # noun-phrase only (e.g. "the language of love") — sole hit is love/work/need at end
    if not published and len(verb_hits) == 1 and verb_hits[0].lower() in {
        "love", "work", "need", "needs", "change", "dream", "dreams", "face", "matter", "matters"
    }:
        if last_word(text.rstrip(".!?")) == verb_hits[0].lower():
            return False
    if FLUFF_RE.search(text):
        return False
    if ASR_SALAD_RE.search(text):
        return False
    # filler / like density
    like_n = len(LIKE_RE.findall(text))
    filler_n = len(FILLER_RE.findall(text))
    if like_n >= 2:
        return False
    if filler_n >= 2:
        return False
    if soft and (like_n >= 1 and filler_n >= 1):
        return False
    if soft and like_n >= 1 and nw < 14:
        return False
    # must have sentence-final punct for rotator-grade (published may already)
    if not re.search(r"[.!?…]$", text):
        return False
    # reject dangling contractions as last token
    if re.search(r"\b(?:i'm|you're|we're|they're|it's|that's|there's|what's|here's)\.?$", text, re.I):
        return False
    # reject ending on hanging infinitive "to X." where X is verb without object and short
    if re.search(r"\bto (?:go|do|be|get|make|take|put|see|say|try|start|call|ask)\.?$", text, re.I):
        return False
    # reject "so [clause start]..." incomplete second half when so is late
    if re.search(r"\bso (?:the reason|i|you|we|they|he|she|it)\b", text, re.I):
        # allow if second clause has its own verb completion beyond 4 words after so
        m = re.search(r"\bso\b(.+)$", text, re.I)
        if m and len(m.group(1).split()) < 6:
            return False
    # reject obvious ASR capital glitch density without real punctuation in source sense
    mid_caps = len(re.findall(r"(?<![.!?]\s)\b[A-Z][a-z]{2,}\b", text))
    if mid_caps >= 4 and not published:
        return False
    # reject questions that are clearly mid-host prompts without answer value unless insightful
    if text.endswith("?") and HOST_RE.match(text.split()[0] if False else ""):
        pass
    # standalone: avoid unresolved "how a mentor ... teach you some things" salad
    if re.search(r"\bhow a \w+ or a \w+ \w+ you\b", text, re.I):
        return False
    # too many commas without structure often = ASR mash
    if text.count(",") >= 4 and not published:
        return False
    # pronoun stub endings
    if re.search(r"\b(?:what|about|as|than|because)\s+I[.!?]?$", text, re.I):
        return False
    # "no matter." hanging
    if re.search(r"\bno matter[.!?]?$", text, re.I):
        return False
    # "the same." often truncated contrast
    if re.search(r"\bthe same[.!?]?$", text, re.I) and "same as" not in text.lower():
        if "do the same" in text.lower() or "would i do the same" in text.lower():
            return False
    # mid-sentence lowercase standalone i (ASR)
    if re.search(r"(?<![A-Za-z])i(?![A-Za-z'])", text[1:]):
        return False
    # host agreement crumbs
    if re.search(r"\bright exactly\b", text, re.I):
        return False
    if re.search(r"\bthis is i(?:'m| am)\b", text, re.I):
        return False
    if re.search(r"\b(?:in|on|at|for|with)\s+\w+\s+is\s+\w+ing\b", text, re.I):
        return False
    # incomplete "hide the fact that..." without resolution beyond 8 words after that
    if re.match(r"^Hide the fact\b", text) and "because" not in text.lower():
        return False
    # abrupt mid-clause capital And/But without prior sentence end
    if re.search(r"(?<![.!?])\s+(?:And|But|Or|So|Because)\s+", text) and not published:
        return False
    # trailing weak noun fragments often cut off
    if re.search(r"\b(?:senior|junior|compound|matter|same|behind|bike)\.?$", text, re.I):
        return False
    # must start with pronoun/determiner/nouny strong start — reject bare past participle clauses
    if re.match(r"^[A-Z][a-z]+ed\b", text) and not re.match(
        r"^(?:I|I'm|I've|I'd|I'll|You|We|They|He|She|It|This|That|There|Here|What|When|If|My|Your|Our|Their|The|A|An|People|Life|Love|Fear|Breath|Authenticity|Victim|Empathy|Hearts|Breakdowns|Don't|Never|Always|Sometimes|Maybe|Perhaps)\b",
        text,
    ):
        # allow "Taught by..." etc only if published
        if not published:
            return False
    return True


def polish_sentence(text: str, *, allow_force_period: bool = True) -> str:
    t = re.sub(r"\s+", " ", text).strip(" \"'“”«»")
    # strip leading filler once
    for _ in range(3):
        fw = first_word(t)
        if fw in BAD_START or fw in {"well", "like", "actually", "basically", "literally", "honestly"}:
            t2 = re.sub(r"^[^\s]+\s+", "", t).strip(" ,;")
            if len(t2.split()) < 6:
                break
            t = t2
        else:
            break
    # do NOT strip ending words aggressively — that creates false completions
    if not t:
        return ""
    chars = list(t)
    for i, ch in enumerate(chars):
        if ch.isalpha():
            chars[i] = ch.upper()
            break
    t = "".join(chars)
    if allow_force_period and not re.search(r"[.!?…]$", t):
        t = t.rstrip(",;: ") + "."
    t = re.sub(r"\s+([,.!?])", r"\1", t)
    return re.sub(r"\s+", " ", t).strip()


def extract_punctuated_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text or not re.search(r"[.!?]", text):
        return []
    out = []
    for p in re.split(r"(?<=[.!?])\s+", text):
        p = p.strip()
        if 6 <= len(p.split()) <= 40:
            out.append(p)
    return out


def extract_unpunctuated_spans(text: str, soft: bool) -> list[str]:
    """Only emit spans that already look complete BEFORE forcing a period.

    Soft mode: return nothing (caller should use punctuated/published only).
    Non-soft: require insight cue AND ending word in OK_END_OVERRIDE.
    """
    if soft:
        return []
    text = re.sub(r"\s+", " ", text).strip()
    words = text.split()
    n = len(words)
    if n < 8:
        return []
    start_idxs = []
    for i, w in enumerate(words):
        ww = w.lstrip("\"'“")
        if STRONG_START_RE.match(ww):
            start_idxs.append(i)
    if not start_idxs:
        return []
    cands = []
    for i in start_idxs:
        for L in range(8, 29):
            if i + L > n:
                break
            span_words = words[i : i + L]
            lw = re.findall(r"[A-Za-z0-9']+", span_words[-1])
            lw = lw[-1].lower() if lw else ""
            if lw not in OK_END_OVERRIDE:
                continue
            if first_word(span_words[0]) in BAD_START:
                continue
            span = " ".join(span_words)
            if not VERB_RE.search(span):
                continue
            if not INSIGHT_RE.search(span):
                continue
            if len(LIKE_RE.findall(span)) >= 1:
                continue
            if len(FILLER_RE.findall(span)) >= 2:
                continue
            if ASR_SALAD_RE.search(span):
                continue
            # reject mashed second subject pronoun without conjunction
            if re.search(r"\bI\b.{8,40}?\bI\b", span) and not re.search(
                r"\b(?:and|but|because|when|if|while|as|that)\s+I\b", span, re.I
            ):
                continue
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
    if 8 <= nw <= 24:
        score += 3.5
    elif 6 <= nw <= 34:
        score += 2.0
    else:
        score -= 1.5
    if VERB_RE.search(text):
        score += 1.2
    if INSIGHT_RE.search(text):
        score += 2.5
    if FLUFF_RE.search(text):
        score -= 5.0
    if re.search(r"[.!?…]$", text):
        score += 0.8
    if text[:1].isupper():
        score += 0.5
    if HOST_RE.match(speaker.strip()):
        score -= 0.8
    else:
        score += 1.5
    if duration > 0:
        frac = sec / duration
        if 0.04 <= frac <= 0.93:
            score += 0.7
        if frac < 0.02 or frac > 0.97:
            score -= 2.5
    if source == "published":
        score += 6.0
    score -= 1.2 * len(LIKE_RE.findall(text))
    score -= 0.8 * len(FILLER_RE.findall(text))
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
    dist = [w for w in q_words if len(w) >= 4][:10]
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
        # keep published with timestamp 0 fallback only if complete — use mid-episode later
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


def speaker_label(raw: str) -> str:
    raw = raw.strip()
    if not raw:
        return "Guest"
    # keep Intro/Jacob/Guest/Outro / first token of guest name
    first = raw.split()[0]
    return first.rstrip(":")



def is_rotator_grade(text: str, *, published: bool = False) -> bool:
    """Final homepage/archive gate — stricter than extract completeness."""
    if not is_complete_thought(text, published=published, soft=False):
        return False
    words = text.split()
    if len(words) < 6:
        return False
    if re.search(r"\bIII+\b", text):
        return False
    if re.search(r"\bI think I think\b", text, re.I):
        return False
    if re.search(r"\byeah\b|\babsolutely\b|\bexactly\b", text, re.I) and not published:
        return False
    if re.search(r"\b(?:pheenoh|rot year|well III)\b", text, re.I):
        return False
    if re.search(r"there(?:'s| is) she(?:'s| is)\b", text, re.I):
        return False
    if re.search(r"\bdr\.?$", text, re.I):
        return False
    # Title-Case caption artifacts after the first token
    mid_caps = 0
    for w in words[1:]:
        core = re.sub(r"[^A-Za-z0-9']+", '', w)
        if len(core) >= 2 and core[0].isupper() and core[1:].islower():
            mid_caps += 1
    if mid_caps >= 1 and not published:
        return False
    if re.search(r"\bdo you Is\b|\bCan I tell you a secret\?", text):
        return False
    if text.count("?") >= 1 and not published:
        return False
    if re.search(r"\band that (?:vision|meaning|community)\.?$", text, re.I):
        return False
    if re.search(r"\bfun listen\b", text, re.I):
        return False
    if re.search(r"\bwho (?:don|'don)t play \w+\.?$", text, re.I):
        return False
    if re.search(r"\btrue nature\.?$", text, re.I) and not re.search(r"true nature of\b", text, re.I):
        return False
    if re.search(r"\bexactly or\b", text, re.I):
        return False
    if re.search(r"\bIt so many\b", text):
        return False
    if re.search(r"(?<!^)(?<!\. )\bi'm\b", text):
        return False
    # fragment published lines
    fw = first_word(text)
    if fw in {"isn't", "aren't", "wasn't", "weren't", "don't", "doesn't", "didn't", "can't", "won't", "reminding", "see", "hide", "loves", "now"}:
        return False
    # gerund openers only ok when published and clearly predicative
    if fw in {"staying", "healing", "being", "becoming", "living", "growing"} and not published:
        return False
    # "I said and I still" mash
    if re.search(r"\bI said and I\b", text, re.I):
        return False
    # "I knew had to" missing subject
    if re.search(r"\bI knew had\b", text, re.I):
        return False
    # "diamond is because" mash
    if re.search(r"\bis because\b", text, re.I) and not re.search(r"\b(?:that|this|which|why)\s+is because\b", text, re.I):
        if "reason" not in text.lower() and "the reason" not in text.lower():
            # allow "X is because Y" only with clear subject noun before is
            if not re.search(r"\b(?:reason|truth|point|idea|thing)\s+is because\b", text, re.I):
                return False
    # "I listen to podcasts absolutely"
    if re.search(r"\bI (?:listen|know|think|said)\b.*\b(?:absolutely|that's why I can)\b", text, re.I) and not published:
        return False
    # crazy thinking host crumbs
    if re.search(r"\bcrazy thinking\b|\bLet's realize\b", text, re.I):
        return False
    # "whatever the equivalent of your body"
    if re.search(r"\bwhatever the equivalent\b", text, re.I):
        return False
    # "See the same reoccurring"
    if re.match(r"^See the same\b", text):
        return False
    if re.search(r"\band I (?:felt|feel)\.?$", text, re.I):
        return False
    if re.search(r"\band I (?:felt|feel) (?:really|so|very)?\.?$", text, re.I):
        return False
    # "Life-changing experience I do remember"
    if re.match(r"^Life-changing experience\b", text, re.I):
        return False
    # "In case people can't see from here down"
    if re.match(r"^In case people\b", text, re.I):
        return False
    # "Love myself today and then you go"
    if re.match(r"^Love myself\b", text, re.I):
        return False
    # "This is grounded in science neuroscience" missing commas / caps
    if mid_caps >= 1 and re.search(r"\bscience\s+\w+\s+[A-Z]", text):
        return False
    return True


def select_quotes(turns: list[dict], published: list[str], soft: bool) -> list[Quote]:
    duration = turns[-1]["sec"] if turns else 0
    punct_ratio = (
        sum(1 for t in turns if re.search(r"[.!?]", t["text"])) / max(len(turns), 1)
    )
    # explicit soft ASR: published + punctuated only
    # sparse punctuation (early catalog): allow strict unpunctuated insight-noun ends
    sparse = punct_ratio < 0.12
    selected: list[Quote] = []

    for pq in published:
        # keep wording; only normalize leading capital + terminal punct (no rewrite)
        polished = pq.strip()
        if polished and polished[0].islower():
            polished = polished[0].upper() + polished[1:]
        if not re.search(r"[.!?…]$", polished):
            polished = polished.rstrip(",; ") + "."
        if not is_complete_thought(polished, published=True, soft=soft):
            continue
        if not is_rotator_grade(polished, published=True):
            continue
        hit = find_published_in_transcript(pq, turns)
        if hit:
            speaker = speaker_label(hit.speaker)
            sec, ts = hit.sec, hit.ts
            if HOST_RE.match(speaker) or re.match(r"^(intro|outro)$", speaker, re.I):
                for turn in turns:
                    if not HOST_RE.match(turn["speaker"]) and not re.match(r"^(intro|outro)\b", turn["speaker"], re.I):
                        speaker = speaker_label(turn["speaker"])
                        break
        else:
            # verified timestamp not found — keep published quote with mid-episode anchor
            speaker = "Guest"
            for turn in turns:
                sp = turn["speaker"]
                if HOST_RE.match(sp) or re.match(r"^(intro|outro)\b", sp, re.I):
                    continue
                speaker = speaker_label(sp)
                break
            sec = duration // 3 if duration else 0
            ts = fmt_ts(sec)
        q = Quote(
            sec=sec,
            ts=ts,
            speaker=speaker,
            text=polished,
            source="published",
            score=score_quote(polished, speaker, sec, duration, "published"),
        )
        if not any(similar(q.text, s.text) for s in selected):
            selected.append(q)
        if len(selected) >= 8:
            break

    cands: list[Quote] = []
    for turn in turns:
        if soft:
            continue  # soft ASR: published quotes only
        spans = extract_punctuated_sentences(turn["text"])
        spans += extract_unpunctuated_spans(turn["text"], soft=False)
        for span in spans:
            has_punct = bool(re.search(r"[.!?…]$", span.strip()))
            polished = polish_sentence(span, allow_force_period=True)
            if not is_complete_thought(polished, published=False, soft=(soft or sparse)):
                continue
            # reject broken copula mash: "depression is living"
            if re.search(r"\b(?:in|on|at|for|with)\s+\w+\s+is\s+\w+ing\b", polished, re.I):
                continue
            if re.search(r"\bthis is i(?:'m| am)\b", polished, re.I):
                continue
            if soft or sparse:
                if not INSIGHT_RE.search(polished):
                    continue
                if LIKE_RE.search(polished):
                    continue
                if len(FILLER_RE.findall(polished)) >= 1:
                    continue
            sc = score_quote(polished, turn["speaker"], turn["sec"], duration, "transcript")
            if soft and sc < 7.0:
                continue
            if sparse and sc < 7.5:
                continue
            if not INSIGHT_RE.search(polished) and sc < 6.5:
                continue
            if sc < 5.5:
                continue
            if turn["sec"] < 50 and not INSIGHT_RE.search(polished):
                continue
            if not is_rotator_grade(polished, published=False):
                continue
            cands.append(
                Quote(
                    turn["sec"],
                    turn["ts"],
                    speaker_label(turn["speaker"]),
                    polished,
                    "transcript",
                    sc,
                )
            )

    cands.sort(key=lambda q: q.score, reverse=True)

    def bucket(sec: int) -> int:
        return int((sec / max(duration, 1)) * 8) if duration else 0

    used_b: dict[int, int] = {}
    target_max = 5 if soft else (4 if sparse else 7)
    target_min = 0 if soft else (1 if sparse else 3)

    for c in cands:
        if len(selected) >= target_max:
            break
        if any(similar(c.text, s.text) for s in selected):
            continue
        b = bucket(c.sec)
        if used_b.get(b, 0) >= 2 and len(selected) >= target_min:
            continue
        selected.append(c)
        used_b[b] = used_b.get(b, 0) + 1

    # do NOT pad with weaker quotes — quality over volume

    # final filter
    selected = [
        q
        for q in selected
        if is_complete_thought(q.text, published=(q.source == "published"), soft=soft)
        and is_rotator_grade(q.text, published=(q.source == "published"))
    ]
    selected.sort(key=lambda q: q.sec)
    # prefer 3–8; allow fewer if thin
    if len(selected) > target_max:
        selected = sorted(selected, key=lambda q: q.score, reverse=True)[:target_max]
        selected.sort(key=lambda q: q.sec)
    return selected


def sanitize_quote_text(text: str) -> str:
    return text.replace("“", "‘").replace("”", "’")


def replace_md_quotes(md: str, quotes: list[Quote]) -> str:
    if quotes:
        lines = [f'- [{q.ts}] {q.speaker}: “{sanitize_quote_text(q.text)}”' for q in quotes]
        block = "## Memorable quotes\n\n" + "\n".join(lines) + "\n"
    else:
        block = "## Memorable quotes\n\n_(no stand-alone complete quotes retained for this episode)_\n"
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
    if quotes:
        parts = []
        for q in quotes:
            parts.append(
                f'<blockquote class="archive-quote"><a class="ts" href="#{anchor_id(q.sec)}">[{q.ts}]</a> '
                f'<span class="speaker">{html_lib.escape(q.speaker)}:</span> '
                f"“{html_lib.escape(sanitize_quote_text(q.text))}”</blockquote>"
            )
        new_block = "\n".join(parts)
    else:
        new_block = '<p class="note">No stand-alone complete archive quotes retained for this episode.</p>'
    pattern = re.compile(r"(<h3>Memorable quotes</h3>\s*)(.*?)(\s*<h3>)", re.S)
    m = pattern.search(html)
    if m:
        return html[: m.start(2)] + new_block + html[m.end(2) :]
    pattern2 = re.compile(r"(<h3>Memorable quotes</h3>\s*)(.*?)(\s*</div>)", re.S)
    m2 = pattern2.search(html)
    if m2:
        return html[: m2.start(2)] + new_block + html[m2.end(2) :]
    return html


def map_episodes_by_num() -> dict[str, Path]:
    by_num: dict[str, Path] = {}
    for d in EPISODES.iterdir():
        if not d.is_dir() or "removed" in d.name:
            continue
        n = episode_num(d.name)
        if n and n not in REMOVED and (d / "index.html").exists():
            by_num[n] = d
    return by_num


def map_content_dirs() -> dict[str, Path]:
    """Map episode number -> content dir."""
    by_num: dict[str, Path] = {}
    for d in CONTENT.iterdir():
        if not d.is_dir():
            continue
        n = episode_num(d.name)
        if n and n not in REMOVED:
            by_num[n] = d
    for n, name in SPECIAL_CONTENT.items():
        p = CONTENT / name
        if p.is_dir():
            by_num[n] = p
    return by_num


def process_episode(content_dir: Path, ep_dir: Path, dry_run: bool = False) -> dict:
    num = episode_num(ep_dir.name) or episode_num(content_dir.name)
    for k, v in SPECIAL_CONTENT.items():
        if content_dir.name == v:
            num = k
            break
    soft = num in SOFT_ASR
    tp = content_dir / "transcript.md"
    if not tp.exists():
        return {"num": num, "slug": ep_dir.name, "status": "skip", "reason": "no transcript", "quotes": []}
    turns = parse_turns(tp.read_text(encoding="utf-8", errors="replace"))
    if not turns:
        return {"num": num, "slug": ep_dir.name, "status": "skip", "reason": "empty turns", "quotes": []}
    published = parse_published_quotes(content_dir / "source-quotes.md")
    quotes = select_quotes(turns, published, soft=soft)
    result = {
        "num": num,
        "slug": ep_dir.name,
        "status": "ok",
        "n_quotes": len(quotes),
        "n_published_used": sum(1 for q in quotes if q.source == "published"),
        "soft": soft,
        "samples": [q.text for q in quotes],
        "quotes": quotes,
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
    for marker in ("<!-- topic-chips:start -->", 'class="browse-subtitle"', "data-theme"):
        if marker in html and marker not in html2:
            raise RuntimeError(f"{num}: lost marker {marker}")
    html_path.write_text(html2, encoding="utf-8")

    # sync work mirror archive picks if present
    if WORK_MIRROR_CONTENT.exists():
        mirror = None
        if (WORK_MIRROR_CONTENT / content_dir.name).is_dir():
            mirror = WORK_MIRROR_CONTENT / content_dir.name / "source-archive-picks.md"
        else:
            # try by number prefix
            for d in WORK_MIRROR_CONTENT.iterdir():
                if d.is_dir() and d.name.startswith(num):
                    mirror = d / "source-archive-picks.md"
                    break
        if mirror is not None and picks_path.exists():
            mirror.parent.mkdir(parents=True, exist_ok=True)
            mirror.write_text(picks_path.read_text(encoding="utf-8"), encoding="utf-8")

    return result


def load_browse_meta() -> dict[str, dict]:
    idx_path = ASSETS / "episodes_index.json"
    if not idx_path.exists():
        return {}
    data = json.loads(idx_path.read_text(encoding="utf-8"))
    return {e["slug"]: e for e in data.get("episodes", [])}


def build_quotes_clean(results: list[dict], ep_meta: dict[str, dict]) -> list[dict]:
    pool = []
    for r in results:
        if r.get("status") != "ok":
            continue
        slug = r["slug"]
        meta = ep_meta.get(slug, {})
        browse = meta.get("browse_title") or meta.get("canonical_title") or slug
        for q in r.get("quotes") or []:
            if not is_complete_thought(q.text, published=(q.source == "published"), soft=r.get("soft", False)):
                continue
            pool.append(
                {
                    "speaker": q.speaker,
                    "episode_slug": slug,
                    "episode_number": r["num"],
                    "browse_title": browse,
                    "timestamp": q.ts,
                    "t_seconds": q.sec,
                    "text": q.text,
                    "source": q.source,
                }
            )
    return pool


def update_episodes_index_quotes(results: list[dict]) -> None:
    for path in (ASSETS / "episodes_index.json", SOURCES / "episodes_index.json"):
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        by_slug = {r["slug"]: r for r in results if r.get("status") == "ok"}
        for ep in data.get("episodes", []):
            r = by_slug.get(ep["slug"])
            if not r:
                continue
            ep["quotes"] = [
                {
                    "t": q.ts,
                    "t_seconds": q.sec,
                    "speaker": q.speaker,
                    "text": q.text,
                }
                for q in r.get("quotes") or []
            ]
        data["generated"] = "quotes-clean-rebuild"
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def patch_archive_js_rotator() -> bool:
    """Point homepage randomQuote at quotes_clean.json when available."""
    js_path = ASSETS / "archive.js"
    js = js_path.read_text(encoding="utf-8")
    if "quotes_clean.json" in js:
        return False
    old = """  function randomQuote(targetEl) {
    return loadIndex().then(function (data) {
      var el = typeof targetEl === "string" ? document.querySelector(targetEl) : targetEl;
      if (!el) return;
      var pool = [];
      published(data.episodes).forEach(function (ep) {
        (ep.quotes || []).forEach(function (q) {
          if (q && q.text && q.text.length > 20) pool.push({ ep: ep, q: q });
        });
      });
      var item = pick(pool);
      if (!item) {
        el.innerHTML = "";
        return;
      }
      var t = parseTs(item.q.t_seconds != null ? item.q.t_seconds : item.q.t);
      var hash = item.q.t ? "#t-" + fmtTs(t) : "";
      var text = item.q.text.replace(/^["“]|["”]$/g, "");
      el.innerHTML =
        '<blockquote class="pull-quote">“' +
        esc(text) +
        '”</blockquote>' +
        '<p class="note">' +
        (item.q.speaker ? esc(item.q.speaker) + " · " : "") +
        '<a href="' +
        esc(episodeUrl(item.ep, hash)) +
        '">' +
        esc(item.ep.browse_title || item.ep.canonical_title) +
        " · Episode " +
        esc(item.ep.number) +
        "</a></p>";
    });
  }"""
    new = """  function randomQuote(targetEl) {
    var el = typeof targetEl === "string" ? document.querySelector(targetEl) : targetEl;
    if (!el) return Promise.resolve();
    var cleanUrl = abs("assets/quotes_clean.json");
    return fetch(cleanUrl, { credentials: "same-origin" })
      .then(function (r) {
        if (!r.ok) throw new Error("no quotes_clean");
        return r.json();
      })
      .then(function (payload) {
        var list = payload.quotes || payload || [];
        var pool = list.filter(function (q) {
          return q && q.text && q.text.length > 20 && q.episode_slug;
        });
        var item = pick(pool);
        if (!item) {
          el.innerHTML = "";
          return;
        }
        var t = parseTs(item.t_seconds != null ? item.t_seconds : item.timestamp);
        var hash = item.timestamp ? "#t-" + fmtTs(t) : "";
        var text = String(item.text).replace(/^["“]|["”]$/g, "");
        var epUrl = abs("episodes/" + item.episode_slug + "/index.html") + hash;
        el.innerHTML =
          '<blockquote class="pull-quote">“' +
          esc(text) +
          '”</blockquote>' +
          '<p class="note">' +
          (item.speaker ? esc(item.speaker) + " · " : "") +
          '<a href="' +
          esc(epUrl) +
          '">' +
          esc(item.browse_title || item.episode_slug) +
          " · Episode " +
          esc(item.episode_number || "") +
          "</a></p>";
      })
      .catch(function () {
        return loadIndex().then(function (data) {
          var pool = [];
          published(data.episodes).forEach(function (ep) {
            (ep.quotes || []).forEach(function (q) {
              if (q && q.text && q.text.length > 20) pool.push({ ep: ep, q: q });
            });
          });
          var item = pick(pool);
          if (!item) {
            el.innerHTML = "";
            return;
          }
          var t = parseTs(item.q.t_seconds != null ? item.q.t_seconds : item.q.t);
          var hash = item.q.t ? "#t-" + fmtTs(t) : "";
          var text = item.q.text.replace(/^["“]|["”]$/g, "");
          el.innerHTML =
            '<blockquote class="pull-quote">“' +
            esc(text) +
            '”</blockquote>' +
            '<p class="note">' +
            (item.q.speaker ? esc(item.q.speaker) + " · " : "") +
            '<a href="' +
            esc(episodeUrl(item.ep, hash)) +
            '">' +
            esc(item.ep.browse_title || item.ep.canonical_title) +
            " · Episode " +
            esc(item.ep.number) +
            "</a></p>";
        });
      });
  }"""
    if old not in js:
        print("WARN: archive.js randomQuote block not found exactly; skipping JS patch", flush=True)
        return False
    js_path.write_text(js.replace(old, new, 1), encoding="utf-8")
    return True


def count_before_from_snapshot() -> int:
    snap = SOURCES / "reports" / "quotes_before_snapshot.json"
    if snap.exists():
        return len(json.loads(snap.read_text(encoding="utf-8")))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", nargs="*")
    args = ap.parse_args()

    ep_map = map_episodes_by_num()
    content_map = map_content_dirs()
    nums = sorted(set(ep_map) & set(content_map))
    if args.only:
        nums = [n for n in nums if n in args.only]

    before_n = count_before_from_snapshot()
    results = []
    for num in nums:
        cd = content_map[num]
        ep = ep_map[num]
        try:
            r = process_episode(cd, ep, dry_run=args.dry_run)
        except Exception as e:
            r = {"num": num, "slug": ep.name, "status": "error", "reason": str(e), "quotes": []}
        results.append(r)
        samples = r.get("samples") or []
        preview = " | ".join(s[:70] for s in samples[:2])
        print(
            f"{num} {r.get('status')} n={r.get('n_quotes')} pub={r.get('n_published_used')} "
            f"soft={r.get('soft')} :: {preview}",
            flush=True,
        )

    after_n = sum(r.get("n_quotes") or 0 for r in results if r.get("status") == "ok")
    thin = [r["num"] for r in results if r.get("status") == "ok" and (r.get("n_quotes") or 0) < 3]
    zero = [r["num"] for r in results if r.get("status") == "ok" and (r.get("n_quotes") or 0) == 0]

    if not args.dry_run:
        ep_meta = load_browse_meta()
        pool = build_quotes_clean(results, ep_meta)
        payload = {
            "generated": "quotes-clean-rebuild",
            "count": len(pool),
            "quotes": pool,
        }
        for path in (SOURCES / "quotes_clean.json", ASSETS / "quotes_clean.json"):
            path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        update_episodes_index_quotes(results)
        patched = patch_archive_js_rotator()
        print(f"quotes_clean.json count={len(pool)}; archive.js patched={patched}", flush=True)

    summary = {
        "episodes_processed": sum(1 for r in results if r.get("status") == "ok"),
        "episodes_error": sum(1 for r in results if r.get("status") == "error"),
        "episodes_skip": sum(1 for r in results if r.get("status") == "skip"),
        "quotes_before": before_n,
        "quotes_after": after_n,
        "quotes_dropped": before_n - after_n if before_n else None,
        "thin_episodes": thin,
        "zero_quote_episodes": zero,
        "soft_asr": sorted(SOFT_ASR),
    }
    print("SUMMARY", json.dumps(summary, indent=2))
    report = SOURCES / "reports" / "QUOTE_REBUILD_REPORT.json"
    report.write_text(
        json.dumps(
            {
                **summary,
                "results": [
                    {
                        "num": r.get("num"),
                        "slug": r.get("slug"),
                        "status": r.get("status"),
                        "n_quotes": r.get("n_quotes"),
                        "n_published_used": r.get("n_published_used"),
                        "soft": r.get("soft"),
                        "samples": r.get("samples"),
                        "reason": r.get("reason"),
                    }
                    for r in results
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return 0 if summary["episodes_error"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
