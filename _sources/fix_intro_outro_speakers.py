#!/usr/bin/env python3
"""Quality-pass (d): Intro / Jacob / Guest / Outro transcript speaker labeling.

Relabels produced opens (music, bumper, taped open) to Intro and produced
closes to Outro. Keeps spoken host after bumper as Jacob. Fixes clear
misattribution (bumper crumbs on guest, solocast non-Jacob labels, guest-labeled
produced closes). Soft-ASR episodes (0020, 0025, 0047, 0037): speaker/intro-outro
only — do not rewrite cue text.

Updates:
  - _sources/content/*/transcript.md
  - _sources/content/*/transcript.html
  - episodes/*/index.html  (cue <span class="speaker"> only; About untouched)

Skips *-removed. No git commit/push. Preserves timestamps/clocks, topic chips,
browse-subtitle, dark theme, quotes, chapters.
"""
from __future__ import annotations

import argparse
import html as html_lib
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = Path(__file__).resolve().parent / "content"
EPISODES = ROOT / "episodes"
REPORTS = Path(__file__).resolve().parent / "reports"

SOFT_ASR = {"0020", "0025", "0047", "0037"}

# Audit-seeded high-confidence sets (QUALITY_PASS_AUDIT.md §4)
AUDIT_INTRO = {
    "0021", "0023", "0024", "0025", "0026", "0027", "0028", "0030", "0031", "0032",
    "0034", "0035", "0036", "0037", "0039", "0040", "0041", "0042", "0044", "0045",
    "0046", "0047", "0048", "0049", "0050", "0051", "0052", "0053", "0054", "0055",
    "0056", "0057", "0058", "0059", "0060", "0061", "0062", "0063", "0064", "0065",
    "0067", "0068", "0069", "0070", "0071", "0072", "0073", "0074", "0075", "0087",
    "0090", "0092", "0094", "0095", "0097", "0098", "0099", "0102", "0103", "0104",
    "0105", "0106", "0107", "0108", "0109", "0110", "0111", "0112", "0113", "0116",
    "0117", "0118", "0119", "0124",
}
AUDIT_OUTRO = {
    "0013", "0015", "0021", "0025", "0026", "0032", "0034", "0038", "0044", "0048",
    "0049", "0051", "0052", "0054", "0057", "0058", "0059", "0063", "0064", "0065",
    "0066", "0067", "0068", "0072", "0076", "0078", "0079", "0080", "0081", "0083",
    "0090", "0092", "0096", "0097", "0098", "0101", "0103", "0107", "0115", "0117",
    "0118", "0121", "0123", "0124",
}

# Episodes where audit flagged intro but live guest-greet should stay Jacob
SKIP_INTRO = {"0124"}  # "Well, Sigmar, welcome…" is spoken host greeting

TURN_MD_RE = re.compile(
    r"^\[(\d{2}):(\d{2}):(\d{2})\]\s+([^:\n]+):\s*(.*)$", re.M
)
CUE_RE = re.compile(
    r'(<p class="cue" id="t-(\d{2})-(\d{2})-(\d{2})"><a class="ts" href="#t-\2-\3-\4">'
    r"\[\2:\3:\4\]</a> <span class=\"speaker\">)([^<]+)(:</span>\s*)(.*?)(</p>)",
    re.S,
)

HOST_NAMES = {"jacob", "host", "jacob rhines", "jacobfromtheinternet"}
META_SPEAKERS = {"intro", "outro", "bumper"}

BUMPER_OPEN = re.compile(
    r"(?:"
    r"at what age[, ]+(?:do|should) we learn|"
    r"at what age (?:do|should) we learn|"
    r"hello[,.]?\s+(?:and\s+)?welcome to the junkyard|"
    r"hello\s+(?:all|everyone|beautiful people)\s+welcome to the junkyard|"
    r"hey[, ]+everything'?s going to be all right|"
    r"(?:what you'?re listening to right now is )?just an intro|"
    r"skip that intro|"
    r"hello(?:\s+my)?\s+lovely listeners|"
    r"what'?s up (?:y'?all|party people|guys|bros)[, ]+welcome to the junkyard|"
    r"hey hello how are you welcome to\s+the junkyard|"
    r"welcome to the junkyard love podcast with ourselves|"
    r"omi dudes|"
    r"what is (?:cracking|bracken|gucci) my|"
    r"hello me mates welcome to the junkyard|"
    r"hello my very best to you"
    r")",
    re.I,
)

KIP_RE = re.compile(r"\bknowledge is power\b", re.I)

# Live host open (keep as Jacob): ladies/gentlemen + here-with-guest, no formula bumper
LIVE_HOST_OPEN = re.compile(
    r"ladies and gentlemen.{0,40}(?:welcome|i'?m here with|i have .{0,40} here)",
    re.I,
)

INTRO_CONT = re.compile(
    r"(?:"
    r"today'?s recommendation|"
    r"before (?:we get|said|the podcast)|"
    r"if you would like to skip|"
    r"value your time|"
    r"i just wanted to (?:do an intro|give you|do a summarization)|"
    r"releasing my \d|"
    r"\d0th episode|"
    r"watch our live stream|"
    r"hope you(?:'re| are) (?:well|very well)|"
    r"recommendation (?:before|due|is|of)|"
    r"for more information on serotonin|"  # 0061 bumper continuation
    r"deep code|"  # 0040 rec plug
    r"my mates"  # bumper crumb
    r")",
    re.I,
)

COLD_OPEN = re.compile(
    r"(?:"
    r"today on my podcast|"
    r"is a voice for|"
    r"i sit down with|"
    r"on (?:today'?s|this) episode"
    r")",
    re.I,
)

# Produced close: audience CTA near end (not in-body yoga chat)
PRODUCED_CLOSE = re.compile(
    r"(?:"
    r"junkyard love (?:podcasts? )?out\b|"
    r"\bdrink (?:some |more )?water\b|"
    r"\blisteners?\b.{0,50}(?:drink|stretch|love yoursel|take care|have a good|peace|you know the drill)|"
    r"(?:folks|everybody)\b.{0,40}(?:drink|stretch|love yoursel|share|subscribe)|"
    r"\bstretch\b.{0,40}(?:drink|hydrate|listeners|have a good|love yoursel)|"
    r"have a good (?:rest of your |rest your )?day.{0,80}(?:drink|stretch|listeners|junkyard|love yoursel)|"
    r"\blisteners?\b.{0,40}have a good|"
    r"at what age (?:do|should) we learn|"
    r"please (?:share|follow|like|subscribe)|"
    r"(?:share|follow|like|subscribe).{0,50}(?:wherever|spotify|apple|youtube|instagram)|"
    r"five[- ]?star|"
    r"wherever you(?:'re| are) listening|"
    r"\bahoy\b|"
    r"cancel cancel|"
    r"get present|get grounded|wiggle your|"
    r"focus on your posture|"
    r"be kind to yourself|"
    r"put this phone away|"
    r"i(?:'m| am) going to (?:hit )?end (?:this |on this )?record|"
    r"i will (?:continue to |talk for another couple minutes)|"
    r"you know the drill|"
    r"peace out\b|"
    r"love yourselves?(?:\s+peace|\s+drink|\.|"
    r"$)|"
    r"hope you(?:(?:'ve)| have)? enjoyed the episode|"
    r"don'?t forget to stretch|"
    r"please drink some water|"
    r"if you haven'?t drank|"
    r"\bknowledge is power\b"
    r")",
    re.I,
)

LIVE_GUEST_GREET = re.compile(
    r"welcome to the junkyard love podcast,\s+\w+",
    re.I,
)


def is_bumper_open_text(text: str) -> bool:
    """True for produced open / bumper; excludes live host greets and trailing KIP crumbs."""
    if LIVE_GUEST_GREET.search(text) and not BUMPER_OPEN.search(text):
        return False
    if LIVE_HOST_OPEN.search(text) and not BUMPER_OPEN.search(text) and not (
        KIP_RE.search(text[:120]) or len(text) < 160
    ):
        # live cold open to guest — Jacob, not Intro
        return False
    if BUMPER_OPEN.search(text):
        return True
    if COLD_OPEN.search(text) and len(text) > 80:
        return True
    # Knowledge-is-power: only if slogan-led or short bumper-only turn
    km = KIP_RE.search(text)
    if km:
        if len(text) < 180:
            return True
        if km.start() <= 80:
            return True
        # trailing KIP after long talk — not a whole-turn Intro
        return False
    if re.search(r"^hello and welcome to the junkyard love\.?\s*$", text, re.I):
        return True
    return False


@dataclass
class Turn:
    sec: int
    h: str
    mi: str
    s: str
    speaker: str
    text: str
    new_speaker: str | None = None


@dataclass
class EpisodeResult:
    ep: str
    slug: str
    intro_fixes: int = 0
    outro_fixes: int = 0
    mid_fixes: int = 0
    notes: list[str] = field(default_factory=list)
    uncertain: list[str] = field(default_factory=list)
    changed: bool = False


def ep_num_from_name(name: str) -> str | None:
    m = re.match(r"^(\d{4})\b", name)
    return m.group(1) if m else None


def is_host(name: str) -> bool:
    return name.strip().lower() in HOST_NAMES


def is_meta(name: str) -> bool:
    return name.strip().lower() in META_SPEAKERS


def parse_md_turns(text: str) -> list[Turn]:
    out: list[Turn] = []
    for m in TURN_MD_RE.finditer(text):
        h, mi, s, sp, tx = m.groups()
        out.append(
            Turn(
                sec=int(h) * 3600 + int(mi) * 60 + int(s),
                h=h,
                mi=mi,
                s=s,
                speaker=sp.strip(),
                text=tx.strip(),
            )
        )
    return out


def parse_html_turns(html: str) -> list[Turn]:
    out: list[Turn] = []
    for m in CUE_RE.finditer(html):
        h, mi, s = m.group(2), m.group(3), m.group(4)
        sp = m.group(5).strip()
        tx = html_lib.unescape(re.sub(r"<[^>]+>", "", m.group(7))).strip()
        out.append(
            Turn(
                sec=int(h) * 3600 + int(mi) * 60 + int(s),
                h=h,
                mi=mi,
                s=s,
                speaker=sp,
                text=tx,
            )
        )
    return out


def load_meta(content_dir: Path | None) -> dict:
    if content_dir and (content_dir / "meta.json").exists():
        return json.loads((content_dir / "meta.json").read_text())
    return {}


def guest_first_names(meta: dict, turns: list[Turn]) -> set[str]:
    names: set[str] = set()
    guests = meta.get("guests") or []
    if isinstance(guests, str):
        guests = [guests]
    g = meta.get("guest") or meta.get("guest_name")
    if g:
        guests = list(guests) + [g]
    for g in guests:
        if not g or not isinstance(g, str):
            continue
        # "Brian 'Dj Toasty' Andrews and Kelly..." → split
        parts = re.split(r"\s+(?:and|&)\s+", g)
        for p in parts:
            p = re.sub(r"[\"'].*?[\"']", "", p).strip()
            p = re.sub(r"\s+of\s+.*$", "", p, flags=re.I).strip()
            if not p:
                continue
            names.add(p)
            names.add(p.split()[0])
            # nickname tokens
            for tok in re.findall(r"[A-Za-z][A-Za-z0-9]+", p):
                if len(tok) > 2:
                    names.add(tok)
    # from existing transcript speakers
    for t in turns:
        if not is_host(t.speaker) and not is_meta(t.speaker):
            names.add(t.speaker)
            names.add(t.speaker.split()[0])
    return {n for n in names if n and n.lower() not in HOST_NAMES | META_SPEAKERS}


def find_intro_indices(turns: list[Turn], ep: str) -> list[int]:
    if ep in SKIP_INTRO:
        return []
    idxs: list[int] = []
    for i, t in enumerate(turns[:40]):
        if t.sec > 18 * 60:
            break
        text = t.text
        if LIVE_GUEST_GREET.search(text) and not is_bumper_open_text(text):
            if idxs:
                break
            continue
        hit = is_bumper_open_text(text)
        if i == 0 and hit:
            idxs.append(i)
            continue
        if idxs:
            if hit or INTRO_CONT.search(text):
                idxs.append(i)
                continue
            # bumper crumb on wrong speaker within ~3 min
            if (
                i <= idxs[-1] + 3
                and t.sec <= turns[idxs[0]].sec + 200
                and len(text) < 120
                and re.search(
                    r"junkyard|welcome|mates|ahoy|recommendation|listeners|"
                    r"knowledge|live stream|serotonin|posture",
                    text,
                    re.I,
                )
            ):
                idxs.append(i)
                continue
            if i > idxs[-1] + 1:
                break
        elif i <= 2 and hit and t.sec < 120:
            idxs.append(i)
        elif i >= 2 and not idxs:
            break

    # Long taped intro (e.g. 0102, 0050): extend Jacob intro block before guest
    if idxs and re.search(
        r"intro|50th episode|i just wanted to|summarization|skip that intro|"
        r"what you'?re listening to right now",
        turns[idxs[0]].text,
        re.I,
    ):
        first_guest = next(
            (
                i
                for i, t in enumerate(turns)
                if not is_host(t.speaker) and not is_meta(t.speaker)
            ),
            len(turns),
        )
        for i in range(idxs[-1] + 1, min(first_guest, idxs[0] + 20)):
            t = turns[i]
            if is_host(t.speaker) and t.sec < turns[idxs[0]].sec + 25 * 60:
                if re.search(
                    r"intro|skip|listeners|podcast|episode|grateful|today|"
                    r"recommendation|welcome|jacob",
                    t.text,
                    re.I,
                ):
                    idxs.append(i)
                else:
                    break
            else:
                break
    return idxs


def find_outro_indices(turns: list[Turn], ep: str) -> list[int]:
    """Label produced closes near the end as Outro.

    Only returns turns that themselves look like produced closes (no range-fill).
    Long substance turns with a soft trailing CTA stay Jacob unless a strong
    formula marker is present.
    """
    n = len(turns)
    if not n:
        return []

    def is_produced_close(text: str) -> bool:
        strong_formula = bool(
            re.search(
                r"junkyard love (?:podcasts? )?out\b|"
                r"you know the drill|"
                r"at what age (?:do|should) we learn|"
                r"i(?:'m| am) going to (?:hit )?end (?:this |on this )?record|"
                r"hope you(?:(?:'ve)| have)? enjoyed the episode|"
                r"\bdrink (?:some |more )?water\b|"
                r"if you haven'?t drank|"
                r"don'?t forget to stretch|"
                r"cancel cancel|get present|get grounded|wiggle your|"
                r"focus on your posture|put this phone away|\bahoy\b|"
                r"five[- ]?star|"
                r"wherever you(?:'re| are) listening|"
                r"please (?:share|follow|like|subscribe)",
                text,
                re.I,
            )
        )
        audience_cta = bool(
            re.search(
                r"\blisteners?\b.{0,80}"
                r"(?:drink|stretch|love yoursel|take care|have a good|peace|hydrate|"
                r"you know the drill)",
                text,
                re.I,
            )
        )
        love_close = bool(
            re.search(
                r"love yourselves?(?:\s+(?:drink|peace|take)|\.\s*$)",
                text,
                re.I,
            )
        )
        kip_close = bool(
            KIP_RE.search(text)
            and (
                len(text) < 140
                or re.search(
                    r"knowledge is power\.?\s*(?:reality.{0,40}junkyard.*)?$",
                    text,
                    re.I,
                )
            )
        )
        if kip_close:
            return True
        if strong_formula or audience_cta or love_close:
            if len(text) > 550 and not strong_formula and not (
                audience_cta
                and re.search(
                    r"\bdrink\b|\bstretch\b|you know the drill|junkyard love",
                    text,
                    re.I,
                )
            ):
                return False
            return True
        return False

    hits: list[int] = []
    window = min(6, n)
    for i in range(n - window, n):
        if is_produced_close(turns[i].text):
            hits.append(i)
    if not hits:
        return []
    filtered = []
    for i in hits:
        if i >= n - 4:
            filtered.append(i)
        elif re.search(
            r"junkyard love (?:podcasts? )?out|you know the drill|"
            r"\bdrink (?:some |more )?water\b|at what age|"
            r"knowledge is power",
            turns[i].text,
            re.I,
        ):
            filtered.append(i)
    return sorted(set(filtered))



def apply_mid_fixes(
    turns: list[Turn],
    ep: str,
    meta: dict,
    intro_idxs: set[int],
    outro_idxs: set[int],
) -> list[tuple[int, str, str, str]]:
    """Return list of (idx, old, new, reason) mid-run fixes."""
    fixes: list[tuple[int, str, str, str]] = []
    solo = bool(meta.get("solo")) or (
        meta.get("guest") in (None, "", "None")
        and not meta.get("guests")
        and ep in {"0045", "0060", "0083", "0093"}
    )
    # 0100 is Jacob-on-Brent / co-hosted — not a pure solocast despite meta.solo
    if ep == "0100":
        solo = False

    if solo:
        for i, t in enumerate(turns):
            if i in intro_idxs or i in outro_idxs:
                continue
            if not is_host(t.speaker) and not is_meta(t.speaker):
                fixes.append((i, t.speaker, "Jacob", "solocast non-Jacob → Jacob"))
        return fixes

    # Bumper / produced-open text labeled as guest anywhere in first 8 minutes
    for i, t in enumerate(turns):
        if i in intro_idxs or i in outro_idxs:
            continue
        if is_host(t.speaker) or is_meta(t.speaker):
            continue
        if t.sec <= 8 * 60 and is_bumper_open_text(t.text):
            # 0031-style: guest turn that starts with host welcoming guest — uncertain split
            if re.search(
                rf"^{re.escape(t.speaker.split()[0])}\s+welcome\b", t.text, re.I
            ):
                continue  # leave uncertain
            fixes.append((i, t.speaker, "Intro", "early bumper text on guest → Intro"))

    # Produced close labeled as guest in last 3 minutes
    if turns:
        end = turns[-1].sec
        for i, t in enumerate(turns):
            if i in outro_idxs or i in intro_idxs:
                continue
            if is_host(t.speaker) or is_meta(t.speaker):
                continue
            if t.sec >= end - 180 and re.search(
                r"junkyard love (?:podcasts? )?out|"
                r"(?:\blisteners?\b.{0,40}(?:drink|stretch|love yoursel))|"
                r"\bdrink (?:some |more )?water\b.{0,60}(?:stretch|listeners|love yoursel)|"
                r"at what age (?:do|should) we learn|"
                r"you know the drill|"
                r"hope you(?:(?:'ve)| have)? enjoyed the episode",
                t.text,
                re.I,
            ):
                fixes.append(
                    (i, t.speaker, "Outro", "late produced-close on guest → Outro")
                )
    return fixes


def decide_labels(turns: list[Turn], ep: str, meta: dict) -> EpisodeResult:
    slug = meta.get("slug") or ep
    res = EpisodeResult(ep=ep, slug=slug)
    if not turns:
        res.uncertain.append("no turns")
        return res

    intro_idxs = find_intro_indices(turns, ep)
    outro_idxs = find_outro_indices(turns, ep)

    # If audit said intro but we found none (except SKIP), force first turn when it matches soft open
    if ep in AUDIT_INTRO and ep not in SKIP_INTRO and not intro_idxs:
        t0 = turns[0]
        if re.search(
            r"welcome to the junkyard|hello[,.]?\s+(?:all|everyone|and)?\s*welcome|"
            r"knowledge is power|at what age|just an intro",
            t0.text,
            re.I,
        ):
            intro_idxs = [0]
            res.notes.append("audit-intro soft-match first turn")
        else:
            res.uncertain.append(
                f"audit intro but no auto-match: {t0.speaker}: {t0.text[:70]}"
            )

    if ep in AUDIT_OUTRO and not outro_idxs:
        # force last turn if audit; still require some close-ish signal
        tL = turns[-1]
        if PRODUCED_CLOSE.search(tL.text) or re.search(
            r"listeners|drink|junkyard|stretch|peace|knowledge is power|"
            r"have a good|appreciate you",
            tL.text,
            re.I,
        ):
            outro_idxs = [len(turns) - 1]
            res.notes.append("audit-outro soft-match last turn")
        else:
            res.uncertain.append(
                f"audit outro but no auto-match: {tL.speaker}: {tL.text[:70]}"
            )

    intro_set = set(intro_idxs)
    outro_set = set(outro_idxs)
    # Prefer Outro over Intro if somehow both (shouldn't happen)
    intro_set -= outro_set

    mid = apply_mid_fixes(turns, ep, meta, intro_set, outro_set)

    for i in intro_set:
        old = turns[i].speaker
        if old != "Intro":
            turns[i].new_speaker = "Intro"
            res.intro_fixes += 1
            if not is_host(old) and not is_meta(old):
                res.notes.append(f"intro was {old} @ {turns[i].h}:{turns[i].mi}:{turns[i].s}")

    for i in outro_set:
        old = turns[i].speaker
        if turns[i].new_speaker == "Intro":
            continue
        if old != "Outro":
            turns[i].new_speaker = "Outro"
            res.outro_fixes += 1
            if not is_host(old) and not is_meta(old):
                res.notes.append(f"outro was {old} @ {turns[i].h}:{turns[i].mi}:{turns[i].s}")

    for i, old, new, reason in mid:
        if turns[i].new_speaker:
            continue
        if turns[i].speaker != new:
            turns[i].new_speaker = new
            res.mid_fixes += 1
            res.notes.append(f"mid: {reason} @ {turns[i].h}:{turns[i].mi}:{turns[i].s}")

    # 0040: Brandon "My mates" after short open — ensure Intro
    if ep == "0040" and len(turns) > 1:
        if re.search(r"^my mates\.?$", turns[1].text, re.I):
            if turns[1].new_speaker != "Intro" and turns[1].speaker != "Intro":
                turns[1].new_speaker = "Intro"
                res.intro_fixes += 1
                res.mid_fixes += 0
                res.notes.append("0040 bumper crumb 'My mates' → Intro")

    res.changed = any(t.new_speaker and t.new_speaker != t.speaker for t in turns)

    # Flag possible remaining dual-guest / mid uncertainty lightly
    speakers = Counter(
        (t.new_speaker or t.speaker) for t in turns if not is_meta(t.new_speaker or t.speaker)
    )
    guests = [s for s in speakers if not is_host(s)]
    if len(guests) >= 2 and ep not in {"0010", "0032", "0042", "0053", "0054", "0056", "0063", "0073", "0107"}:
        # known multi-guest ok; others note if unexpected third party
        pass

    if ep in SKIP_INTRO:
        res.uncertain.append("0124 live guest greet kept as Jacob (not Intro)")

    return res


def render_md(turns: list[Turn]) -> str:
    lines = []
    for t in turns:
        sp = t.new_speaker or t.speaker
        lines.append(f"[{t.h}:{t.mi}:{t.s}] {sp}: {t.text}")
    return "\n".join(lines) + "\n"


def render_html(turns: list[Turn]) -> str:
    parts = []
    for t in turns:
        sp = t.new_speaker or t.speaker
        tid = f"t-{t.h}-{t.mi}-{t.s}"
        text = html_lib.escape(t.text, quote=False)
        # preserve apostrophe entity style used elsewhere
        text = text.replace("'", "&#x27;")
        parts.append(
            f'<p class="cue" id="{tid}"><a class="ts" href="#{tid}">[{t.h}:{t.mi}:{t.s}]</a> '
            f'<span class="speaker">{sp}:</span> {text}</p>'
        )
    return "\n".join(parts) + "\n"


def patch_episode_html(html: str, turns: list[Turn]) -> str:
    """Replace speaker labels in cue spans by cue order (safe with duplicate timestamps)."""
    wanted = [(t.new_speaker or t.speaker) for t in turns]
    if not any(t.new_speaker and t.new_speaker != t.speaker for t in turns):
        return html
    cue_re = re.compile(
        r'(<p class="cue"[^>]*>\s*<a class="ts"[^>]*>\[.*?\]</a>\s*<span class="speaker">)'
        r'([^<]+)(:</span>)',
        re.S,
    )
    matches = list(cue_re.finditer(html))
    # Prefer cues inside transcript region when counts differ (quotes also use .speaker)
    # Match by scanning all cues that look like timestamped turns; if count mismatches,
    # try restricting to div.transcript / Full transcript section.
    def region_bounds(h: str) -> tuple[int, int] | None:
        m = re.search(r'<div class="transcript">', h)
        if m:
            start = m.start()
            last = list(re.finditer(r'<p class="cue"', h[start:]))
            if not last:
                return None
            last_pos = start + last[-1].start()
            end_m = re.search(
                r'</div>\s*(?:</div>\s*)?(?:<h2|footer|</main|<section|$)',
                h[last_pos:],
                re.I,
            )
            end = last_pos + (end_m.start() + len('</div>') if end_m else len(h) - last_pos)
            return start, end
        for hpat in (r'<h2>\s*Full transcript\s*</h2>', r'<h2>\s*Transcript\s*</h2>'):
            m = re.search(hpat, h, re.I)
            if not m:
                continue
            end_m = re.search(r'<h2>|footer|</main>', h[m.end():], re.I)
            end = m.end() + (end_m.start() if end_m else len(h) - m.end())
            return m.start(), end
        return None

    bounds = region_bounds(html)
    if bounds:
        start, end = bounds
        block = html[start:end]
        matches = list(cue_re.finditer(block))
        if len(matches) != len(wanted):
            return html  # refuse mismatched surgery
        out = []
        last = 0
        changed = False
        for m, sp in zip(matches, wanted):
            out.append(block[last:m.start()])
            if m.group(2) != sp:
                changed = True
            out.append(m.group(1) + sp + m.group(3))
            last = m.end()
        out.append(block[last:])
        if not changed:
            return html
        return html[:start] + ''.join(out) + html[end:]

    # Fallback: global ordered cues if counts match
    if len(matches) != len(wanted):
        return html
    out = []
    last = 0
    for m, sp in zip(matches, wanted):
        out.append(html[last:m.start()])
        out.append(m.group(1) + sp + m.group(3))
        last = m.end()
    out.append(html[last:])
    return ''.join(out)


def find_content_dir(ep: str) -> Path | None:
    matches = sorted(CONTENT.glob(f"{ep}-*"))
    return matches[0] if matches else None


def find_episode_dir(ep: str) -> Path | None:
    matches = [
        d
        for d in EPISODES.iterdir()
        if d.is_dir() and d.name.startswith(ep) and "removed" not in d.name
    ]
    return sorted(matches)[0] if matches else None


def process_episode(ep: str, dry_run: bool = False) -> EpisodeResult:
    content_dir = find_content_dir(ep)
    ep_dir = find_episode_dir(ep)
    if not ep_dir or not (ep_dir / "index.html").exists():
        return EpisodeResult(ep=ep, slug=ep, uncertain=["missing episode dir"])

    meta = load_meta(content_dir)
    html_path = ep_dir / "index.html"
    html = html_path.read_text(encoding="utf-8")

    if content_dir and (content_dir / "transcript.md").exists():
        md_text = (content_dir / "transcript.md").read_text(encoding="utf-8")
        turns = parse_md_turns(md_text)
        source = "md"
    else:
        turns = parse_html_turns(html)
        source = "html"
        md_text = None

    if not turns:
        return EpisodeResult(ep=ep, slug=meta.get("slug", ep), uncertain=["empty transcript"])

    res = decide_labels(turns, ep, meta)
    res.slug = meta.get("slug") or ep_dir.name
    if source == "html":
        res.notes.append("no _sources/content transcript — patched episode HTML only")

    if not res.changed:
        return res

    if dry_run:
        return res

    # Soft ASR: still allow speaker renames (text unchanged via HTML patch path)
    new_md = render_md(turns)
    new_html_cues = render_html(turns)

    if content_dir:
        (content_dir / "transcript.md").write_text(new_md, encoding="utf-8")
        (content_dir / "transcript.html").write_text(new_html_cues, encoding="utf-8")
        # Surgical speaker-span patch on episode (preserves About/timestamps/theme)
        html2 = patch_episode_html(html, turns)
        if html2 != html:
            html_path.write_text(html2, encoding="utf-8")
        else:
            res.uncertain.append("episode HTML speaker patch produced no diff")
    else:
        html2 = patch_episode_html(html, turns)
        if html2 != html:
            html_path.write_text(html2, encoding="utf-8")
        else:
            res.uncertain.append("episode HTML speaker patch produced no diff")

    return res


def list_episode_nums() -> list[str]:
    nums = []
    for d in EPISODES.iterdir():
        if not d.is_dir() or "removed" in d.name:
            continue
        n = ep_num_from_name(d.name)
        if n:
            nums.append(n)
    return sorted(set(nums))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--ep", action="append", help="Limit to episode number(s)")
    ap.add_argument("--write-report", action="store_true", default=True)
    args = ap.parse_args()

    eps = args.ep or list_episode_nums()
    results: list[EpisodeResult] = []
    for ep in eps:
        results.append(process_episode(ep, dry_run=args.dry_run))

    intro_eps = sum(1 for r in results if r.intro_fixes)
    outro_eps = sum(1 for r in results if r.outro_fixes)
    mid_eps = sum(1 for r in results if r.mid_fixes)
    changed = sum(1 for r in results if r.changed)
    total_intro = sum(r.intro_fixes for r in results)
    total_outro = sum(r.outro_fixes for r in results)
    total_mid = sum(r.mid_fixes for r in results)

    lines = [
        "# Quality-pass (d) — Intro / Jacob / Guest / Outro speaker labeling",
        "",
        f"_Mode: {'dry-run' if args.dry_run else 'applied'}_",
        "",
        "## Counts",
        "",
        f"- Episodes scanned: **{len(results)}**",
        f"- Episodes changed: **{changed}**",
        f"- Episodes with Intro relabel: **{intro_eps}** (turns: {total_intro})",
        f"- Episodes with Outro relabel: **{outro_eps}** (turns: {total_outro})",
        f"- Episodes with mid-run fixes: **{mid_eps}** (turns: {total_mid})",
        "",
        "## Per-episode changes",
        "",
        "| Ep | Intro | Outro | Mid | Notes |",
        "|---:|---:|---:|---:|---|",
    ]
    uncertain_all: list[str] = []
    for r in results:
        if not r.changed and not r.uncertain:
            continue
        note = "; ".join(r.notes[:3])
        if r.uncertain:
            uncertain_all.append(f"{r.ep}: " + "; ".join(r.uncertain))
        if r.changed:
            lines.append(
                f"| {r.ep} | {r.intro_fixes} | {r.outro_fixes} | {r.mid_fixes} | {note} |"
            )

    lines += ["", "## Remaining uncertain", ""]
    if uncertain_all:
        for u in uncertain_all:
            lines.append(f"- {u}")
    else:
        lines.append("- (none flagged)")

    lines += [
        "",
        "## Notes",
        "",
        "- Produced opens → **Intro**; produced closes → **Outro**; host after bumper stays **Jacob**.",
        "- Soft ASR eps 0020/0025/0047/0037: speaker labels only (cue text not rewritten beyond label).",
        "- Jacob published About left untouched.",
        "- No git commit/push.",
        "",
    ]
    report = "\n".join(lines)
    REPORTS.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS / "QUALITY_PASS_D_SPEAKERS_REPORT.md"
    if not args.dry_run or args.write_report:
        report_path.write_text(report, encoding="utf-8")

    print(report)
    print(f"\nReport: {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
