#!/usr/bin/env python3
"""Build browse_titles.json and apply browse titles + dark-mode theme site-wide.

Idempotent. Primary target: deploy tree (repo root containing episodes/, assets/).
Skip Removed placeholders. Does not commit or push.
"""
from __future__ import annotations

import html as html_lib
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
DEPLOY = SCRIPT_DIR.parent  # junkyard-love-archive-deploy/
MIRROR = Path("/workspace/junkyard-love-archive")
EPISODES_DIR = DEPLOY / "episodes"
ASSETS = DEPLOY / "assets"
BROWSE_JSON = SCRIPT_DIR / "browse_titles.json"

# Grounded candidates from QUALITY_PASS_AUDIT.md — needs_browse_title (27)
NEEDS_BROWSE: dict[str, str] = {
    "0002": "Growth hard work vision and raves",
    "0003": "Ego mindfulness and consciousness",
    "0004": "Community technology positive use",
    "0005": "Goals presence meditation and plateaus",
    "0006": "Always smiling friendship and shared history",
    "0007": "Past pains laughs and future plans",
    "0008": "Ego as a beast",
    "0009": "Colorado skater kid to rapper",
    "0010": "DJ discipline assessing the next moves",
    "0011": "Echo chambers & online communication",
    "0012": "Being passionate about the product",
    "0013": "Motherhood courage and reconnecting with yourself",
    "0015": "C-Diff survival storytelling and gratitude",
    "0017": "Free talk with Spencer again",
    "0018": "Change room to breathe",
    "0019": "Metalcore genre Dead Crown sound",
    "0020": "Speech pathology career and belonging",
    "0021": "How the band got started",
    "0022": "Herniated discs and handmade kids clothes",
    "0023": "Three kinds of empathy",
    "0024": "Rap music background & inspiration",
    "0025": "Natural healer and mystical knowledge",
    "0026": "Clear Eyes Full Hearts Can't Lose",
    "0027": "DJ sets live music and nightlife",
    "0028": "The importance of music",
    "0031": "Growth and allowing room to change",
    "0033": "Team Banzai at Black Diamond Studio",
}

HEADER_RE = re.compile(
    r"<header class=\"site\">.*?</header>",
    re.DOTALL,
)

# Canonical header with theme toggle (base-safe hrefs)
NEW_HEADER = """<header class="site">
  <div class="header-row">
    <a class="brand" href="index.html">The Junkyard Love Podcast</a>
    <button type="button" class="theme-toggle" data-theme-toggle aria-label="Toggle light and dark mode">Light</button>
  </div>
  <nav>
    <a href="episodes/index.html">Episodes</a>
    <a href="guests/index.html">Guests</a>
    <a href="topics/index.html">Topics</a>
    <a href="llms.txt">llms.txt</a>
  </nav>
</header>"""

EARLY_THEME_SCRIPT = (
    '<script>(function(){try{var t=localStorage.getItem("jylp-theme");'
    'if(t==="light"||t==="dark")document.documentElement.setAttribute("data-theme",t);'
    '}catch(e){}})();</script>\n'
)

THEME_JS_TAG = '<script src="assets/theme.js" defer></script>'


def unescape(s: str) -> str:
    return html_lib.unescape(s)


def escape(s: str) -> str:
    return (
        html_lib.escape(s, quote=True)
        .replace("&#x27;", "&#x27;")  # keep consistent
    )


def strip_tags(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s)


def ep_num_from_slug(slug: str) -> str | None:
    m = re.match(r"^(\d{4})-", slug)
    return m.group(1) if m else None


def is_removed(slug: str) -> bool:
    return "removed" in slug.lower()


def list_episode_dirs() -> list[Path]:
    dirs = []
    for d in sorted(EPISODES_DIR.iterdir()):
        if not d.is_dir():
            continue
        if not re.match(r"^\d{4}-", d.name):
            continue  # skip alias redirect dirs
        if is_removed(d.name):
            continue
        if not (d / "index.html").exists():
            continue
        dirs.append(d)
    return dirs


def read_h1_and_guest(html: str) -> tuple[str, str]:
    m = re.search(r"<article>\s*<h1>(.*?)</h1>", html, re.DOTALL)
    if not m:
        m = re.search(r"<h1>(.*?)</h1>", html, re.DOTALL)
    h1 = unescape(strip_tags(m.group(1))).strip() if m else ""
    guest = ""
    mg = re.search(
        r'<p class="meta">.*?(?:Guest|Guests):\s*(.*?)</p>',
        html,
        re.DOTALL | re.IGNORECASE,
    )
    if mg:
        guest = unescape(strip_tags(mg.group(1))).strip()
        # drop trailing role noise already in text
    if not guest:
        ms = re.search(r"Solo[^<]*", html)
        if ms and "meta" in html[max(0, html.find("class=\"meta\"")) : html.find("class=\"meta\"") + 200]:
            guest = "Solo (host)"
    return h1, guest


def title_case_slug_phrase(slug: str, guest_slug_hint: str = "") -> str | None:
    """When H1 is truncated with ..., recover phrase from slug remainder."""
    # strip leading NNN-
    rest = re.sub(r"^\d{4}-", "", slug)
    # try to drop guest-name-ish prefix by finding common thematic words
    # Convert hyphens to spaces and title-case lightly
    words = rest.split("-")
    # Heuristic: drop leading name tokens until we hit "the","a","an" or long thematic run
    # Better: use known patterns from slug after guest portion — keep full hyphen phrase
    # and title-case: this is a fallback only for truncated H1s.
    phrase = " ".join(words)
    # Title-case small words carefully
    small = {"a", "an", "the", "and", "or", "of", "to", "for", "in", "on", "with", "from"}
    out = []
    for i, w in enumerate(phrase.split()):
        lw = w.lower()
        if i > 0 and lw in small:
            out.append(lw)
        else:
            out.append(lw.capitalize() if lw.islower() or lw == w.lower() else w)
    return " ".join(out)


def extract_browse_from_h1(h1: str, slug: str, ep: str) -> str:
    """Extract thematic browse_title from a good H1 (title_already_good)."""
    raw = h1.strip()
    truncated = raw.endswith("...")
    if truncated:
        recovered = recover_from_slug(slug, ep)
        if recovered:
            return recovered
        raw = raw[:-3].rstrip()

    # Quoted short title first: 'Later Bloom' - ...
    m = re.match(r"^('[^']+'|\"[^\"]+\")\s+-\s+", raw)
    if m:
        return clean_phrase(m.group(1))

    # Leading thematic titles (title first, episode/guest after)
    lead_patterns = [
        r'^(.+?)\s+-\s+Episode\s+\d+',
        r'^(.+?)\s+-\s+The Junkyard Love Podcast',
        r'^(.+?)\s+-\s+with\s+',
        r'^(.+?)\s+\|\s+',
    ]
    for pat in lead_patterns:
        m = re.match(pat, raw, re.IGNORECASE)
        if m:
            phrase = m.group(1).strip(" -|")
            if is_wrapper_part(phrase) or re.match(
                r"^(?:Episode|Ep\.?<PLACE>|EP|E|JYLP)\b", phrase, re.IGNORECASE
            ):
                continue  # later Episode-NNN handlers
            if " - " in phrase:
                first = phrase.split(" - ", 1)[0].strip()
                if (
                    2 <= len(first.split()) <= 8
                    and not is_wrapper_part(first)
                    and not re.match(
                        r"^(?:Episode|Ep\.?<PLACE>|EP|E|JYLP)\b", first, re.IGNORECASE
                    )
                ):
                    phrase = first
            quoted = phrase[:1] in ("'", '"')
            if len(phrase.split()) >= 2 or (quoted and len(phrase) > 3):
                return clean_phrase(phrase)


    # Punchy lead + long descriptive subtitle (no show wrapper)
    if not re.match(r'^(?:The\s+)?(?:JYLP|Junkyard|Episode|Ep\b|\d{3})', raw, re.IGNORECASE):
        m = re.match(r'^([^-]+?)\s+-\s+(.+)$', raw)
        if m:
            first, rest = m.group(1).strip(), m.group(2).strip()
            rest_l = rest.lower()
            if 2 <= len(first.split()) <= 7 and (
                rest_l.startswith("a conversation")
                or rest_l.startswith("simple and")
                or len(rest.split()) >= 8
            ):
                return clean_phrase(first)

    # Episode 0123: Title with Guest
    m = re.match(r"^Episode\s+\d+:\s*(.+?)(?:\s+with\s+.+)?$", raw, re.IGNORECASE)
    if m:
        phrase = re.sub(r"\s+with\s+.+$", "", m.group(1).strip(), flags=re.IGNORECASE).strip()
        if phrase:
            return clean_phrase(phrase)

    # Episode/JYLP NNN - ... forms
    m = re.match(
        r"^(?:The\s+)?(?:Junkyard Love Podcast\s+)?(?:The\s+)?(?:JYLP\s+)?"
        r"(?:Episode|Ep\.?|EP|E)\s*\d+\s*[-–—:]\s*(.+)$",
        raw,
        re.IGNORECASE,
    )
    if m:
        rest = m.group(1).strip()
        # "... - with Author ... - 'Always Evolution Occurs'"
        if re.match(r'^(?:with|w/)\s+', rest, re.IGNORECASE):
            parts = re.split(r"\s+-\s+", rest)
            last = parts[-1].strip().strip("'\"")
            if last and not re.match(r'^(?:with|w/)', last, re.IGNORECASE):
                return clean_phrase(last)
        parts = re.split(r"\s+-\s+with\s+", rest, maxsplit=1, flags=re.IGNORECASE)
        phrase = parts[0]
        phrase = re.sub(r"\s+-\s+Series Part.*$", "", phrase, flags=re.IGNORECASE)
        phrase = re.sub(r"\s+\(video\)\s*$", "", phrase, flags=re.IGNORECASE)
        m2 = re.match(r"^Solo with .+?\s*[-–—]\s*(.+)$", phrase, re.IGNORECASE)
        if m2:
            phrase = m2.group(1)
        phrase = re.sub(
            r'^(?:Episode|Ep\.?|EP|E)\s*\d+\s*[-–—:]\s*',
            '',
            phrase,
            flags=re.IGNORECASE,
        )
        if phrase and not re.match(r"^(with|w/)\s", phrase, re.IGNORECASE):
            return clean_phrase(phrase)

    # "083 - a solocast - Making Sense..."
    m = re.match(r'^\d{3,4}\s+-\s+(?:a\s+)?solocast\s+-\s+(.+)$', raw, re.IGNORECASE)
    if m:
        return clean_phrase(m.group(1))

    # Classic dash split
    if re.search(r'\s[-–—]\s', raw):
        parts = re.split(r"\s+[-–—]\s+", raw)
        thematic = []
        for p in parts:
            if is_wrapper_part(p):
                continue
            if re.match(r'^(?:with|w/)\s+', p, re.IGNORECASE):
                continue
            thematic.append(p)
        if thematic:
            if len(thematic) == 1:
                return clean_phrase(thematic[0].strip("'\""))
            last = thematic[-1].strip().strip("'\"")
            first = thematic[0]
            if looks_like_role_fluff(first) or re.match(
                r'^[A-Z][a-z]+(?:\s+[A-Z][a-z.\']+)+$', first
            ):
                if len(last.split()) <= 10:
                    return clean_phrase(last)
            if len(thematic) >= 2 and all(len(t.split()) <= 10 for t in thematic[-2:]):
                if looks_like_role_fluff(first):
                    return clean_phrase(last)
                return clean_phrase(" - ".join(thematic))
            if len(last.split()) <= 12:
                return clean_phrase(last)
            return clean_phrase(" - ".join(thematic))

    # Multi-space separator (0038, 0045)
    m = re.match(
        r"^(?:Episode|Ep\.?)\s*\d+\s+(?:with\s+.+?|Solo with .+?)\s{2,}(.+)$",
        raw,
        re.IGNORECASE,
    )
    if m:
        return clean_phrase(m.group(1))
    m = re.search(r"\s{2,}(.+)$", raw)
    if m and re.match(r"^(?:Episode|The JYLP|JYLP)", raw, re.IGNORECASE):
        return clean_phrase(m.group(1))

    # Fallback: strip wrappers
    stripped = raw
    stripped = re.sub(
        r"^(?:The\s+)?(?:Junkyard Love Podcast\s+)?(?:The\s+)?(?:JYLP\s+)?",
        "",
        stripped,
        flags=re.IGNORECASE,
    )
    stripped = re.sub(
        r"^(?:Episode|Ep\.?|EP|E)\s*\.?\s*\d+\s*(?:w/?\s*|with\s+)?",
        "",
        stripped,
        flags=re.IGNORECASE,
    )
    stripped = re.sub(r"^\d{3,4}\s*(?:with\s+|w\s+)?", "", stripped, flags=re.IGNORECASE)
    stripped = stripped.strip(" -–—|")
    if stripped and stripped != raw and len(stripped) > 8:
        if " - " in stripped:
            parts = [
                p
                for p in re.split(r"\s+-\s+", stripped)
                if not is_wrapper_part(p)
                and not re.match(r'^(?:with|w/)', p, re.IGNORECASE)
            ]
            if parts:
                cand = parts[-1] if len(parts[-1].split()) <= 14 else " - ".join(parts)
                return clean_phrase(cand.strip("'\""))
        return clean_phrase(stripped)

    return clean_phrase(raw)



def is_wrapper_part(p: str) -> bool:
    p = p.strip()
    if re.match(
        r"^(?:The\s+)?(?:Junkyard Love Podcast|JYLP)\b",
        p,
        re.IGNORECASE,
    ):
        return True
    if re.match(r"^(?:Episode|Ep\.?|EP|E)\s*\d+\b", p, re.IGNORECASE):
        return True
    if re.match(r"^\d{3,4}\b", p):
        return True
    return False


def looks_like_role_fluff(p: str) -> bool:
    fluff = (
        "author", "coach", "retired", "navy", "seal", "ceo", "rapper",
        "yogi", "poet", "tutor", "consultant", "bachelor", "masters",
        "science", "researcher", "writer", "investor", "strategist",
        "practitioner", "mediator", "singer", "songwriter", "blind",
        "relationship", "philosophical", "contemplator", "social impact",
        "voice actor", "puppeteer", "storyteller", "sound producer",
        "connector", "operations", "marriage coaches", "psychotherapist",
        "hypnotherapist", "transition mentor", "family business",
        "speaker", "electrician", "competitive", "powerlifter",
        "starseed", "reiki", "mlb", "twitch", "cannabis", "industry",
    )
    low = p.lower()
    hits = sum(1 for f in fluff if f in low)
    return hits >= 2 or (hits >= 1 and len(p.split()) >= 6)


def clean_phrase(s: str) -> str:
    s = s.strip().strip(" -–—|")
    s = re.sub(r"\s+", " ", s)
    s = s.strip(".")
    # unwrap quotes only if whole phrase quoted oddly — keep inner quotes
    return s.strip()


def recover_from_slug(slug: str, ep: str) -> str | None:
    """Recover thematic title from slug when H1 ends with ..."""
    # Known full recoveries for truncated public titles
    KNOWN = {
        "0049": "The Ever Evolving Chameleon, Vibe Surfing, Weird America and Giving Power to the Positive",
        "0050": "Healing The Soul With Hands and Self Love",
        "0051": "Hard Work and Heavy Weight",
        "0056": "Get With The Picture, Grow Through It, And Laugh",
    }
    if ep in KNOWN:
        return KNOWN[ep]
    # Generic: take slug after dropping NNN and a guess at guest tokens — title-case
    rest = re.sub(r"^\d{4}-", "", slug)
    # These truncated ones have guest then thematic; use known list primarily
    return None


def build_browse_map() -> dict[str, dict]:
    out: dict[str, dict] = {}
    n_new = 0
    n_existing = 0
    for d in list_episode_dirs():
        slug = d.name
        ep = ep_num_from_slug(slug)
        if not ep:
            continue
        html = (d / "index.html").read_text(encoding="utf-8", errors="replace")
        h1, guest = read_h1_and_guest(html)
        if ep in NEEDS_BROWSE:
            browse = NEEDS_BROWSE[ep]
            source = "needs_browse_title"
            n_new += 1
        else:
            browse = extract_browse_from_h1(h1, slug, ep)
            source = "title_already_good"
            n_existing += 1
        out[slug] = {
            "episode_number": ep,
            "canonical_title": h1,
            "browse_title": browse,
            "guest": guest,
            "source": source,
        }
    return out


# ---------------------------------------------------------------------------
# Apply browse titles to HTML
# ---------------------------------------------------------------------------

LIST_ITEM_RE = re.compile(
    r'(<li>\s*<a href="(episodes/(\d{4}-[^"/]+)/index\.html)">(.*?)</a>)'
    r'(\s*<br\s*/?>\s*<span class="note">)(.*?)(</span>\s*</li>)',
    re.DOTALL,
)


def format_list_link_text(browse: str, ep: str, guest: str) -> str:
    """Link text: browse_title (escaped). Note carries ep + guest."""
    return html_lib.escape(browse)


def note_with_browse_meta(old_note: str, ep: str, guest: str) -> str:
    """Rebuild note to lead with Episode NNN · guest, keep date/duration when present."""
    note = unescape(strip_tags(old_note)).strip()
    # Extract date YYYY-MM-DD and duration-like token if present
    date_m = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", note)
    dur_m = re.search(r"\b(\d{1,2}:\d{2}(?::\d{2})?)\b", note)
    parts = [f"Episode {ep}"]
    if date_m:
        parts.append(date_m.group(1))
    if dur_m:
        parts.append(dur_m.group(1))
    if guest:
        # Avoid duplicating "Guest:" if guest already short
        g = guest
        g = re.sub(r"^Guests?:\s*", "", g, flags=re.IGNORECASE)
        parts.append(g)
    return " · ".join(parts)


def apply_browse_to_list_html(html: str, browse_map: dict[str, dict]) -> str:
    """Rewrite episode list items to use browse_title."""

    def repl(m: re.Match) -> str:
        href = m.group(2)
        slug = m.group(3)
        old_note = m.group(6)
        info = browse_map.get(slug)
        if not info:
            return m.group(0)
        browse = info["browse_title"]
        ep = info["episode_number"]
        guest = info.get("guest") or ""
        link = format_list_link_text(browse, ep, guest)
        note = html_lib.escape(note_with_browse_meta(old_note, ep, guest))
        return (
            f'<li><a href="{href}">{link}</a>'
            f'<br><span class="note">{note}</span></li>'
        )

    return LIST_ITEM_RE.sub(repl, html)


def apply_browse_to_episode_page(html: str, info: dict) -> str:
    """Keep canonical H1; add browse subtitle when it differs."""
    browse = info["browse_title"]
    canonical = info["canonical_title"]
    # Remove prior browse subtitle if re-running
    html = re.sub(
        r'\s*<p class="browse-subtitle">.*?</p>',
        "",
        html,
        count=1,
        flags=re.DOTALL,
    )
    if browse.strip().lower() == canonical.strip().lower():
        return html
    # Also skip if browse is essentially the whole H1
    if browse.strip().lower() in canonical.strip().lower() and len(browse) > 40:
        # still show if it's the distinctive phrase and H1 is wrapper+phrase
        pass

    sub = f'\n<p class="browse-subtitle">{html_lib.escape(browse)}</p>'
    html2, n = re.subn(
        r"(<article>\s*<h1>.*?</h1>)",
        r"\1" + sub,
        html,
        count=1,
        flags=re.DOTALL,
    )
    if n:
        return html2
    # fallback: after first h1
    html2, n = re.subn(
        r"(<h1>.*?</h1>)",
        r"\1" + sub,
        html,
        count=1,
        flags=re.DOTALL,
    )
    return html2


def apply_browse_to_guest_page(html: str, browse_map: dict[str, dict]) -> str:
    return apply_browse_to_list_html(html, browse_map)


# ---------------------------------------------------------------------------
# Dark mode / theme
# ---------------------------------------------------------------------------

STYLE_CSS = r'''/* Junkyard Love Podcast archive — minimal readable, dark default */
:root,
html[data-theme="light"] {
  --bg: #f7f4ef;
  --fg: #1a1a1a;
  --muted: #5a5a5a;
  --accent: #8b3a2b;
  --card: #fffdf9;
  --border: #e0d8cc;
  --link: #6b2d22;
  --quote: #2a2a2a;
  --chip-hover-bg: #fff;
  --btn-fg: #fff;
  --toggle-bg: transparent;
  --toggle-fg: var(--fg);
  --toggle-border: var(--border);
}
html[data-theme="dark"] {
  --bg: #141210;
  --fg: #eae6de;
  --muted: #a8a297;
  --accent: #c48778;
  --card: #1c1916;
  --border: #3a342e;
  --link: #d4a99a;
  --quote: #d2cdc4;
  --chip-hover-bg: #2a2622;
  --btn-fg: #1a1412;
  --toggle-bg: #2a2622;
  --toggle-fg: #eae6de;
  --toggle-border: #4a433c;
}
html { color-scheme: light dark; }
html[data-theme="dark"] { color-scheme: dark; }
html[data-theme="light"] { color-scheme: light; }

* { box-sizing: border-box; }
html { font-size: 18px; scroll-behavior: smooth; }
body {
  margin: 0;
  font-family: Georgia, "Times New Roman", serif;
  line-height: 1.65;
  color: var(--fg);
  background: var(--bg);
}
a { color: var(--link); }
a:hover { text-decoration: underline; }
.wrap { max-width: 42rem; margin: 0 auto; padding: 1.5rem 1.25rem 3rem; }
header.site {
  border-bottom: 1px solid var(--border);
  background: var(--card);
  margin-bottom: 2rem;
}
header.site .wrap { padding-top: 1rem; padding-bottom: 1rem; }
header.site h1 { font-size: 1.15rem; margin: 0 0 0.35rem; font-weight: 700; }
.header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 0.35rem;
}
.brand {
  font-family: system-ui, -apple-system, sans-serif;
  font-weight: 700;
  font-size: 1.05rem;
  color: var(--fg);
  text-decoration: none;
}
.brand:hover { text-decoration: underline; color: var(--link); }
nav a { margin-right: 1rem; font-size: 0.95rem; text-decoration: none; }
nav a:hover { text-decoration: underline; }
.theme-toggle {
  font-family: system-ui, -apple-system, sans-serif;
  font-size: 0.82rem;
  padding: 0.28rem 0.65rem;
  border-radius: 4px;
  border: 1px solid var(--toggle-border);
  background: var(--toggle-bg);
  color: var(--toggle-fg);
  cursor: pointer;
  line-height: 1.2;
  flex-shrink: 0;
}
.theme-toggle:hover { border-color: var(--accent); }
.theme-toggle:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}
h1, h2, h3 { line-height: 1.25; font-family: system-ui, -apple-system, sans-serif; }
h1 { font-size: 1.75rem; }
h2 { font-size: 1.25rem; margin-top: 2rem; border-bottom: 1px solid var(--border); padding-bottom: 0.35rem; }
.meta, .note {
  color: var(--muted);
  font-size: 0.95rem;
  font-family: system-ui, sans-serif;
}
.browse-subtitle {
  margin: -0.35rem 0 0.85rem;
  font-size: 1.15rem;
  font-family: system-ui, -apple-system, sans-serif;
  font-weight: 600;
  color: var(--muted);
  line-height: 1.35;
}
.card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 1rem 1.15rem;
  margin: 1rem 0;
}
.btn-row a {
  display: inline-block;
  margin: 0.25rem 0.5rem 0.25rem 0;
  padding: 0.4rem 0.75rem;
  background: var(--accent);
  color: var(--btn-fg);
  text-decoration: none;
  border-radius: 4px;
  font-family: system-ui, sans-serif;
  font-size: 0.9rem;
}
.btn-row a.secondary { background: transparent; color: var(--link); border: 1px solid var(--border); }
ul.plain, ul.list { padding-left: 1.2rem; }
ul.list li { margin: 0.65rem 0; }
blockquote {
  margin: 0.75rem 0;
  padding: 0.5rem 0 0.5rem 1rem;
  border-left: 3px solid var(--accent);
  font-style: italic;
  color: var(--quote);
}
.transcript p, .transcript .turn {
  margin: 0.85rem 0;
}
.transcript .speaker {
  font-weight: 700;
  font-family: system-ui, sans-serif;
  font-size: 0.9rem;
  color: var(--accent);
}
.transcript time, .transcript .ts {
  font-family: ui-monospace, monospace;
  font-size: 0.85rem;
  color: var(--muted);
  text-decoration: none;
}
footer.site {
  margin-top: 3rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border);
  color: var(--muted);
  font-size: 0.9rem;
  font-family: system-ui, sans-serif;
}
.chapters li { margin: 0.25rem 0; }
.about { white-space: normal; }
.about p { margin: 0 0 1rem; line-height: 1.65; }
.about p:last-child { margin-bottom: 0; }
.listen a {
  display: inline-block;
  margin: 0.25rem 0.75rem 0.25rem 0;
  font-family: system-ui, sans-serif;
  font-size: 0.9rem;
}

/* Archive picks (transcript-derived; separate from published notes) */
.archive-picks h3 {
  font-size: 1.05rem;
  margin: 1.25rem 0 0.5rem;
  border: 0;
  padding: 0;
}
.archive-picks h3:first-child { margin-top: 0.25rem; }
.archive-picks .archive-quote {
  margin: 0.65rem 0;
  font-size: 0.98rem;
}
.archive-picks .archive-quote .speaker {
  font-style: normal;
  font-weight: 700;
  font-family: system-ui, -apple-system, sans-serif;
  font-size: 0.9rem;
  color: var(--accent);
}

/* Topic chips on episode pages */
.topic-chips {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.4rem 0.5rem;
  margin: 0.85rem 0 1.1rem;
  font-family: system-ui, -apple-system, sans-serif;
  font-size: 0.88rem;
}
.topic-chips-label {
  color: var(--muted);
  margin-right: 0.15rem;
  font-weight: 600;
}
.topic-chip {
  display: inline-block;
  padding: 0.2rem 0.65rem;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: var(--card);
  color: var(--link);
  text-decoration: none;
  line-height: 1.4;
}
.topic-chip:hover {
  border-color: var(--accent);
  text-decoration: none;
  background: var(--chip-hover-bg);
}
'''

THEME_JS = r'''(function () {
  var KEY = "jylp-theme";
  var root = document.documentElement;

  function current() {
    var t = root.getAttribute("data-theme");
    return t === "light" ? "light" : "dark";
  }

  function apply(theme) {
    root.setAttribute("data-theme", theme);
    var label = theme === "dark" ? "Light" : "Dark";
    document.querySelectorAll("[data-theme-toggle]").forEach(function (btn) {
      btn.textContent = label;
      btn.setAttribute("aria-pressed", theme === "dark" ? "true" : "false");
      btn.setAttribute(
        "aria-label",
        theme === "dark" ? "Switch to light mode" : "Switch to dark mode"
      );
    });
  }

  function stored() {
    try {
      var t = localStorage.getItem(KEY);
      if (t === "light" || t === "dark") return t;
    } catch (e) {}
    return null;
  }

  apply(stored() || "dark");

  document.addEventListener("click", function (e) {
    var btn = e.target.closest && e.target.closest("[data-theme-toggle]");
    if (!btn) return;
    var next = current() === "dark" ? "light" : "dark";
    try {
      localStorage.setItem(KEY, next);
    } catch (err) {}
    apply(next);
  });
})();
'''


def patch_html_theme(html: str) -> str:
    """Add data-theme default, early script, theme.js, and unified header."""
    # html tag
    if re.search(r"<html\b[^>]*\bdata-theme=", html):
        html = re.sub(
            r'(<html\b[^>]*\bdata-theme=")[^"]*(")',
            r'\1dark\2',
            html,
            count=1,
        )
    else:
        html = re.sub(r"<html\b([^>]*)>", r'<html\1 data-theme="dark">', html, count=1)
        html = html.replace('<html data-theme="dark" lang="en">', '<html lang="en" data-theme="dark">')
        # normalize if lang came after
        html = re.sub(
            r'<html(\s+data-theme="dark")(\s+lang="en")>',
            r'<html\2\1>',
            html,
        )

    # early theme script after <head> or after charset/base
    if "jylp-theme" not in html or "localStorage.getItem(\"jylp-theme\")" not in html:
        # remove old early script if partial
        html = re.sub(
            r'<script>\(function\(\)\{try\{var t=localStorage\.getItem\("jylp-theme"\);.*?</script>\n?',
            "",
            html,
            count=1,
            flags=re.DOTALL,
        )
        if "<base href=" in html:
            html = html.replace(
                '<base href="/junkyard-love-archive/">\n',
                '<base href="/junkyard-love-archive/">\n' + EARLY_THEME_SCRIPT,
                1,
            )
        elif "<head>" in html:
            html = html.replace("<head>", "<head>\n" + EARLY_THEME_SCRIPT, 1)

    # theme.js before </body>
    if 'src="assets/theme.js"' not in html:
        if "</body>" in html:
            html = html.replace("</body>", THEME_JS_TAG + "\n</body>", 1)
        else:
            html += "\n" + THEME_JS_TAG + "\n"

    # header
    if HEADER_RE.search(html):
        html = HEADER_RE.sub(NEW_HEADER, html, count=1)
    return html


def write_assets() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    (ASSETS / "style.css").write_text(STYLE_CSS, encoding="utf-8")
    (ASSETS / "theme.js").write_text(THEME_JS, encoding="utf-8")


def all_html_files() -> list[Path]:
    files = []
    for p in DEPLOY.rglob("*.html"):
        if "/.git/" in str(p):
            continue
        # skip source blobs / tooling (not published pages)
        if "_sources" in p.parts:
            continue
        # skip removed episode pages
        if "removed" in p.parts:
            continue
        files.append(p)
    return sorted(files)


def mirror_useful(browse_map: dict) -> None:
    """Copy useful sources/assets into work mirror when practical."""
    try:
        m_src = MIRROR / "_sources"
        m_src.mkdir(parents=True, exist_ok=True)
        (m_src / "browse_titles.json").write_text(
            json.dumps(browse_map, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        # copy build script
        src = SCRIPT_DIR / "build_browse_titles.py"
        if src.exists():
            (m_src / "build_browse_titles.py").write_text(
                src.read_text(encoding="utf-8"), encoding="utf-8"
            )
        m_assets = MIRROR / "assets"
        m_assets.mkdir(parents=True, exist_ok=True)
        (m_assets / "style.css").write_text(STYLE_CSS, encoding="utf-8")
        (m_assets / "theme.js").write_text(THEME_JS, encoding="utf-8")
        # also site/assets if present
        site_assets = MIRROR / "site" / "assets"
        if site_assets.parent.exists():
            site_assets.mkdir(parents=True, exist_ok=True)
            (site_assets / "style.css").write_text(STYLE_CSS, encoding="utf-8")
            (site_assets / "theme.js").write_text(THEME_JS, encoding="utf-8")
        # audit already on disk in both trees
    except Exception as e:
        print(f"mirror warning: {e}", file=sys.stderr)


def main() -> int:
    write_assets()
    browse_map = build_browse_map()
    BROWSE_JSON.write_text(
        json.dumps(browse_map, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    n_new = sum(1 for v in browse_map.values() if v["source"] == "needs_browse_title")
    n_good = sum(1 for v in browse_map.values() if v["source"] == "title_already_good")
    print(f"browse_titles.json: {len(browse_map)} episodes ({n_new} new, {n_good} from existing)")

    # Episode pages
    ep_patched = 0
    for d in list_episode_dirs():
        info = browse_map[d.name]
        path = d / "index.html"
        html = path.read_text(encoding="utf-8", errors="replace")
        html = apply_browse_to_episode_page(html, info)
        html = patch_html_theme(html)
        path.write_text(html, encoding="utf-8")
        ep_patched += 1

    # Index pages with episode lists
    list_pages = [
        DEPLOY / "index.html",
        DEPLOY / "episodes" / "index.html",
        DEPLOY / "topics" / "index.html",
        DEPLOY / "guests" / "index.html",
    ]
    for topic_dir in sorted((DEPLOY / "topics").glob("*/index.html")):
        list_pages.append(topic_dir)
    for guest_dir in sorted((DEPLOY / "guests").glob("*/index.html")):
        list_pages.append(guest_dir)

    list_patched = 0
    for path in list_pages:
        if not path.exists():
            continue
        html = path.read_text(encoding="utf-8", errors="replace")
        if "episodes/" in html and "<li>" in html:
            html = apply_browse_to_list_html(html, browse_map)
        html = patch_html_theme(html)
        path.write_text(html, encoding="utf-8")
        list_patched += 1

    # Any remaining HTML (alias redirects etc.) — theme only
    themed = 0
    for path in all_html_files():
        html = path.read_text(encoding="utf-8", errors="replace")
        if 'data-theme-toggle' in html and 'assets/theme.js' in html:
            continue
        html2 = patch_html_theme(html)
        if html2 != html:
            path.write_text(html2, encoding="utf-8")
            themed += 1

    mirror_useful(browse_map)

    # Sample
    samples = []
    for ep in ("0002", "0008", "0121", "0116", "0026"):
        for slug, info in browse_map.items():
            if info["episode_number"] == ep:
                samples.append(f"  {ep}: {info['browse_title']!r} ({info['source']})")
                break

    print(f"episode pages patched: {ep_patched}")
    print(f"list/index pages patched: {list_patched}")
    print(f"extra theme-only patches: {themed}")
    print("samples:")
    print("\n".join(samples))
    print("no git commit/push")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
