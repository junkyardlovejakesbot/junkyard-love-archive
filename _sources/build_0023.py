#!/usr/bin/env python3
"""Process Junkyard Love episode 0023 — Spencer Hicks (single guest).
YT=RSS titles match exactly ("Episode 023 with Spencer Hicks").
Inventory has_quotes=no, has_timestamps=no, has_guest_links=no, has_hashtags=no.
Guest slug: spencer-hicks (EXISTING — lists 0088 + 0074 + 0059 + 0044 + 0038; APPEND 0023, do not wipe).
Archive picks required. Imperfect auto diarization flagged.
YouTube auto-captions en/en-orig available. Insert indexes after 0024."""
from __future__ import annotations
import json, re, shutil
from pathlib import Path
from html import escape, unescape
from collections import Counter

ROOT = Path('/workspace/junkyard-love-archive')
CONTENT = ROOT / 'content/0023-spencer-hicks'
SITE = ROOT / 'site'
DEPLOY = Path('/workspace/junkyard-love-archive-deploy')
EP_SLUG = '0023-spencer-hicks'
GUEST_SLUG = 'spencer-hicks'  # EXISTING — APPEND
TITLE = 'Episode 023 with Spencer Hicks'
RSS_TITLE = TITLE
YT_TITLE = TITLE
GUEST = 'Spencer Hicks'
GUEST_SHORT = 'Spencer'
GUEST_DISPLAY = 'Spencer Hicks'
SPK = 'Spencer'
YOUTUBE = 'https://www.youtube.com/watch?v=W_9LsPkj3wo'
RSS_URL = 'https://share.transistor.fm/s/0519bcf9'
AUDIO_URL = 'https://2.gum.fm/op3.dev/e/pdcn.co/e/pscrb.fm/rss/p/pdst.fm/e/dts.podtrac.com/redirect.mp3/media.transistor.fm/0519bcf9/dd5b80d6.mp3'
DATE = '2020-02-02'
DURATION_S = 4776  # RSS / inventory
YT_DURATION_S = 4803
EP_NUM = '0023'
EP_INT = 23
SPOTIFY = 'https://open.spotify.com/show/45J7CBdM8j29doqyBp2bFs'
APPLE = 'https://podcasts.apple.com/us/podcast/the-junkyard-love-podcast/id1489118788'
SITE_BASE = 'https://junkyardlovejakesbot.github.io/junkyard-love-archive'
VIDEO_ID = 'W_9LsPkj3wo'
TITLE_CONFLICT = 'YT=RSS'

CONTENT.mkdir(parents=True, exist_ok=True)
(CONTENT / 'captions').mkdir(exist_ok=True)

# Caption copies
for src_name, dsts in [
    ('source-yt.en.vtt', ['captions.en.vtt', 'captions/captions.en.vtt', 'captions/auto.en.vtt', 'captions/source-yt.en.vtt']),
    ('source-yt.en-orig.vtt', ['captions.en-orig.vtt', 'captions/captions.en-orig.vtt', 'captions/source-yt.en-orig.vtt']),
    ('source-yt.en.json3', ['captions.en.json3', 'captions/captions.en.json3', 'captions/auto.en.json3', 'captions/source-yt.en.json3']),
    ('source-yt.en-orig.json3', ['captions.en-orig.json3', 'captions/captions.en-orig.json3', 'captions/source-yt.en-orig.json3']),
]:
    src = CONTENT / src_name
    if not src.exists() and 'json3' in src_name:
        alt = CONTENT / src_name.replace('source-yt.', 'source-yt-j3.')
        if alt.exists():
            shutil.copy(alt, src)
    if not src.exists():
        raise SystemExit(f'missing caption source: {src}')
    for d in dsts:
        shutil.copy(src, CONTENT / d)

yt_raw = (CONTENT / 'source-yt.description').read_text(encoding='utf-8')
yt_desc = yt_raw.replace('\r\n', '\n').replace('\r', '\n').strip() + '\n'
if not (CONTENT / 'source-rss-description.txt').exists():
    raise SystemExit('missing source-rss-description.txt')
rss_plain = (CONTENT / 'source-rss-description.txt').read_text(encoding='utf-8').strip() + '\n'
rss_html = (CONTENT / 'source-rss-description.html').read_text(encoding='utf-8') if (CONTENT / 'source-rss-description.html').exists() else ''
(CONTENT / 'source-youtube-title.txt').write_text(YT_TITLE + '\n', encoding='utf-8')
(CONTENT / 'source-youtube-raw.txt').write_text(yt_raw if yt_raw.endswith('\n') else yt_raw + '\n', encoding='utf-8')
(CONTENT / 'yt-meta.txt').write_text(
    f'title={YT_TITLE}\nupload_date=20200202\nduration={YT_DURATION_S}\nvideo_id={VIDEO_ID}\n'
    f'rss_title={RSS_TITLE}\ntitle_conflict={TITLE_CONFLICT}\nh1={TITLE}\n',
    encoding='utf-8',
)

# ---------- ABOUT from YouTube (primary; ~itunes:summary) ----------
yt_body = yt_desc
for marker in ['\nThe Junkyard Love Podcast', '\n\u2605 Episode details', '\n\u2605 Additional episodes']:
    idx = yt_body.find(marker)
    if idx >= 0:
        yt_body = yt_body[:idx]
yt_body = yt_body.strip()
# strip leading (4) episode-series marker if present (match 0038 pattern)
yt_body = re.sub(r'^\(\d+\)\s*', '', yt_body).strip()

# Prefer RSS body if nearly identical after strip
rss_body = re.sub(r'^\(\d+\)\s*', '', rss_plain.strip()).strip()
if rss_body and abs(len(rss_body) - len(yt_body)) < 10:
    about_src = rss_body
else:
    about_src = yt_body

published_quotes: list[str] = []

about_paras = [x.strip() for x in re.split(r'\n\s*\n', about_src) if x.strip()]
expanded = []
for block in about_paras:
    parts = [ln.strip() for ln in block.split('\n') if ln.strip()]
    if len(parts) > 1 and all(len(pt) > 40 for pt in parts):
        expanded.extend(parts)
    else:
        expanded.append(block)
about_paras = expanded

# Soft-split long paragraphs at natural Jacob sentence starts (verbatim)
soft_breaks = [
    'We learn about cognitive empathy',
    "We chat about the strange situation",
    "We expand on the 'alllowing'",
    'We talk about the parasympathetic state',
    'We talk about what the body-mind does',
    'Spencer gives some great tips on sleep',
]
chunks = []
remaining = ' '.join(about_paras) if len(about_paras) == 1 else None
if remaining is None:
    # already multi-para: soft-split each long one
    new_paras = []
    for para in about_paras:
        rem = para
        local = []
        for br in soft_breaks:
            idx = rem.find(br)
            if idx > 40:
                local.append(rem[:idx].strip())
                rem = rem[idx:].strip()
        if rem:
            local.append(rem)
        new_paras.extend(local if local else [para])
    about_paras = [p for p in new_paras if p]
else:
    for br in soft_breaks:
        idx = remaining.find(br)
        if idx > 40:
            chunks.append(remaining[:idx].strip())
            remaining = remaining[idx:].strip()
    if remaining:
        chunks.append(remaining)
    if len(chunks) >= 2:
        about_paras = chunks

if len(about_paras) < 1:
    about_paras = [about_src]

(CONTENT / 'source-description.raw.txt').write_text(about_src + '\n', encoding='utf-8')

guest_links: list[str] = []

about_md = '\n\n'.join(about_paras) + '\n'
quotes_md_lines = ['(none published in episode notes)']
(CONTENT / 'source-about.md').write_text(about_md, encoding='utf-8')
(CONTENT / 'source-quotes.md').write_text('\n'.join(quotes_md_lines) + '\n', encoding='utf-8')
(CONTENT / 'source-timestamps.md').write_text(
    '(none published in episode notes — inventory has_timestamps=no; no YouTube chapter markers; Archive picks uses transcript-derived chapter-style timestamps)\n',
    encoding='utf-8',
)
(CONTENT / 'source-hashtags.txt').write_text('(none published in episode notes)\n', encoding='utf-8')
(CONTENT / 'source-links.md').write_text('(none published in episode notes)\n', encoding='utf-8')
(CONTENT / 'source-description.md').write_text(
    about_md + '\n## Quotes\n\n' + '\n'.join(quotes_md_lines) + '\n\n## Guest links\n\n(none published in episode notes)\n',
    encoding='utf-8',
)
(CONTENT / 'guest-share-draft.txt').write_text(
    f'Episode {EP_NUM}: {TITLE}\nGuest: {GUEST}\nDate: {DATE}\nYouTube: {YOUTUBE}\nRSS: {RSS_URL}\n'
    f'Title conflict: {TITLE_CONFLICT}\nGuest slug: {GUEST_SLUG} (EXISTING — APPEND 0023 to 0088+0074+0059+0044+0038, do not wipe)\n'
    f'About: YT~RSS identical body; (4) series marker stripped; YT footer stripped; no guest contact/email\n'
    f'Transcript: YouTube auto-captions (en/en-orig)\n',
    encoding='utf-8',
)

# ---------- TRANSCRIPT ----------
j = json.loads((CONTENT / 'captions' / 'captions.en.json3').read_text(encoding='utf-8'))
raw = []
for e in j['events']:
    segs = e.get('segs')
    if not segs:
        continue
    text = ''.join(s.get('utf8', '') for s in segs)
    if '<c>' in text:
        continue
    text = text.replace('\n', ' ').strip()
    if not text:
        continue
    low = text.lower().strip()
    if low in ('[music]',) or low.startswith('[music]'):
        continue
    if low in ('foreign', 'you') and e.get('tStartMs', 0) > YT_DURATION_S * 1000 - 25000:
        continue
    t0 = e.get('tStartMs', 0)
    if t0 >= YT_DURATION_S * 1000 + 8000:
        continue
    text = re.sub(r'\[\s*__\s*\]', '****', text)
    text = text.replace('\u00a0', ' ').replace('[\u00a0__\u00a0]', '****').replace('[__]', '****')
    text = re.sub(r'\[\s*[_\u00a0]+\s*\]', '****', text)
    text = re.sub(r'\[\s*[^\]]*__[^\]]*\]', '****', text)
    raw.append((t0, e.get('dDurationMs', 0) or 0, text))

GAP_HARD = 2500
GAP_SOFT = 1800
atoms = []
cur_ms = None
parts = []
prev_ms = None
prev_text = ''

def flush():
    global parts, cur_ms
    if parts:
        atoms.append((cur_ms, ' '.join(parts)))
        parts = []
        cur_ms = None

for t, dur, text in raw:
    if cur_ms is None:
        cur_ms = t
        parts = [text]
        prev_ms, prev_text = t, text
        continue
    gap = t - prev_ms
    ended = bool(re.search(r'[.!?]"?$', prev_text.strip()))
    starts_guest = bool(re.match(
        r'^(Well,? (?:I|so|yeah|we)|Yeah,? (?:so|I|and|we)|So,? (?:I|we|when|in|the|my)|I (?:think|was|love|want|had|grew|got|mean|have|always|feel|am|do|did|started)|We (?:are|were|have|had|just)|Absolutely|Thank you|Okay|Yes|Right|For me|My (?:name|brother|team)|Um,? (?:I|so|yeah)|No problem|Okay so|Spencer)',
        text.strip(), re.I))
    starts_jacob = bool(re.match(
        r'^(Hello|Welcome|Well,? so|So,? (?:let\'s|what|um|Spencer)|Junkyard|Thank you|Yeah,? yeah|Wave|Peace out|Knowledge is|Reality is|Listeners|Cool so|What.?s up|Check it out|Drink some|Now here.?s episode|Ahoy)',
        text.strip(), re.I))
    if gap >= GAP_HARD or (ended and gap >= GAP_SOFT) or (gap >= 900 and (starts_guest or starts_jacob)) or (len(' '.join(parts).split()) > 160 and gap >= 1200):
        flush()
        cur_ms = t
    parts.append(text)
    prev_ms = t
    prev_text = text
flush()
atoms = [(ms, re.sub(r'\s+', ' ', tx).strip()) for ms, tx in atoms if tx]

def light_name_fix(text):
    reps = [
        (r'\bspencer hicks\b', 'Spencer Hicks'),
        (r'\bspencer\b', 'Spencer'),
        (r'\bmax strom\b', 'Max Strom'),
        (r'\bbreathe to heal\b', 'Breathe to Heal'),
        (r'\bparasympathetic\b', 'parasympathetic'),
        (r'\bsympathetic\b', 'sympathetic'),
        (r'\bcortisol\b', 'cortisol'),
        (r'\badrenaline\b', 'adrenaline'),
        (r'\bsensory deprivation\b', 'sensory deprivation'),
        (r'\bfloat tank\b', 'float tank'),
        (r'\bted talk\b', 'TED Talk'),
        (r'\byoutube\b', 'YouTube'),
        (r'\bspotify\b', 'Spotify'),
        (r'\binstagram\b', 'Instagram'),
        (r'\bfacebook\b', 'Facebook'),
        (r'\bjake rhines\b', 'Jake Rhines'),
        (r'\bjacob rhines\b', 'Jacob Rhines'),
        (r'\bjunkyard love podcast\b', 'Junkyard Love Podcast'),
        (r'\bjunkyard love\b', 'Junkyard Love'),
    ]
    for pat, rep in reps:
        text = re.sub(pat, rep, text, flags=re.I)
    return text


def score_jacob(text):
    tlow = text.lower()
    s = 0
    for pat in [
        r'\bjunkyard\b', r'\bwelcome to the (?:junkyard )?podcast\b',
        r'\bdrink (?:some )?(?:dang )?water\b', r'\blove yourself\b', r'\bpeace out\b',
        r'\btake care of yourself\b', r'\blisteners?\b',
        r'\bjacob from the internet\b', r'\bjake rhines\b',
        r'\bget present\b', r'\bknowledge is power\b',
        r'\bahoy\b', r'\bTED Talk\b', r'\bbreathe to heal\b', r'\bmax strom\b',
        r'\brecommendation today\b', r'\bhere.?s episode\b',
        r'\bmy dealings with social anxiety\b', r'\benjoy the episode\b',
        r'\bwieners\b', r'\bsocial anxiety\b',
    ]:
        if re.search(pat, tlow):
            s += 4
    if re.search(r'\b(?:you|spencer)\b', tlow) and ('?' in text or re.search(r'\byou (?:feel|think|said|mentioned|been)\b', tlow)):
        s += 3
    if '?' in text and len(text.split()) < 90:
        s += 2
    if len(text.split()) <= 12 and re.search(
        r'^(yeah|yes|right|okay|ok|cool|love it|mhm|mm+|exactly|wow|dude|man|perfect|great|beautiful|thanks|you bet|interesting)\b', tlow):
        s += 2
    if re.search(r'\byou (?:guys|mentioned|said|feel|think|know|been)\b', tlow):
        s += 2
    return s


def score_spencer(text):
    tlow = text.lower()
    s = 0
    for pat in [
        r'\bcognitive empathy\b', r'\bemotional empathy\b', r'\bcompassionate empathy\b',
        r'\bparasympathetic\b', r'\bsympathetic nervous\b', r'\bcortisol\b',
        r'\badrenaline\b', r'\bfight or flight\b', r'\bfighter flight\b',
        r'\bcold shower\b', r'\bcaffeine\b', r'\bsensory deprivation\b',
        r'\bfloat tank\b', r'\bdeprivation tank\b',
        r'\bsleep hygiene\b', r'\bbreathwork\b', r'\bbreath work\b',
        r'\bi (?:am a|was a|started|recommend|would say)\b',
        r'\bas a (?:trainer|science)\b', r'\bscience[- ]?boy\b',
        r'\bmotivational\b', r'\bfitness\b',
    ]:
        if re.search(pat, tlow):
            s += 5
    if re.search(r'\bi (?:was|had|grew|got|did|started|think|feel|have|went|lived|always|work|don.?t|would say|am)\b', tlow) and len(text.split()) > 40:
        s += 1
    return s


turns = []
prev = 'Jacob'
for i, (ms, text) in enumerate(atoms):
    text = unescape(text.replace('\xa0', ' '))
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r"\b([\w']+)(?:\s+\1\b)+", r'\1', text, flags=re.I)
    text = re.sub(r'([,.;:!?])([A-Za-z])', r'\1 \2', text)
    text = re.sub(r'\band and\b', 'and', text, flags=re.I)
    text = re.sub(r'\bi i\b', 'I', text, flags=re.I)
    text = re.sub(r'\bthe the\b', 'the', text, flags=re.I)
    text = re.sub(r'\bto to\b', 'to', text, flags=re.I)
    text = re.sub(r'\byou you\b', 'you', text, flags=re.I)
    text = re.sub(r'\bwe we\b', 'we', text, flags=re.I)
    text = light_name_fix(text)

    sj = score_jacob(text)
    sg = score_spencer(text)

    if ms < 120000 and re.search(r'junkyard love|hello and welcome|ahoy|knowledge is power|breathe to heal|max strom|TED Talk|recommendation|enjoy the episode', text.lower()):
        sp = 'Jacob'
    elif sj > sg + 1:
        sp = 'Jacob'
    elif sg > sj + 1:
        sp = 'Spencer'
    else:
        if sj > sg:
            sp = 'Jacob'
        elif sg > sj:
            sp = 'Spencer'
        else:
            if len(text.split()) <= 8:
                sp = 'Spencer' if prev == 'Jacob' else 'Jacob'
            else:
                sp = prev

    turns.append((ms, sp, text))
    prev = sp

def merge_turns(seq, cap=220):
    merged = []
    for ms, sp, text in seq:
        if not text:
            continue
        if merged and merged[-1][1] == sp:
            pms, psp, ptx = merged[-1]
            if len(ptx.split()) + len(text.split()) <= cap or ms - pms < 8000:
                merged[-1] = (pms, psp, (ptx + ' ' + text).strip())
            else:
                merged.append((ms, sp, text))
        else:
            merged.append((ms, sp, text))
    return merged

turns = merge_turns(turns)

def cap_start(text):
    if not text:
        return text
    return text[0].upper() + text[1:] if text[0].islower() else text

turns = [(ms, sp, cap_start(tx)) for ms, sp, tx in turns]

fixes = []
new_turns = []
for ms, sp, tx in turns:
    low = tx.lower()
    orig = sp
    if ms < 130000 and re.search(r'junkyard love|hello and welcome|ahoy|knowledge is power|breathe to heal|max strom|TED Talk|recommendation|enjoy the episode', low):
        sp = 'Jacob'
    if re.search(r'cognitive empathy|compassionate empathy|emotional empathy|parasympathetic|sympathetic nervous|cortisol|cold shower|sensory deprivation|deprivation tank|float tank', low):
        # could be either; lean Spencer for technical health tips
        if re.search(r'\bi (?:do|did|recommend|would|always)|my (?:advice|tip|routine)|when i\b', low):
            sp = 'Spencer'
    if re.search(r'drink (?:some )?(?:dang )?water|see you (?:guys )?next|peace out|get present|listeners (?:drink|please|get)|hello and welcome to the junkyard|knowledge is power|ahoy', low):
        sp = 'Jacob'
    if sp != orig:
        fixes.append(f'{orig}->{sp} @ {ms}: {tx[:70]}')
    new_turns.append((ms, sp, tx))
turns = merge_turns(new_turns)

post_fixes = []
def split_on(pattern, before_sp, after_sp, label):
    global turns, post_fixes
    out = []
    for ms, sp, tx in turns:
        m = re.search(pattern, tx, re.I | re.S)
        if m:
            before = m.group(1).strip()
            after = m.group(2).strip()
            if before and after and len(before.split()) > 2 and len(after.split()) > 2:
                out.append((ms, before_sp, cap_start(before)))
                out.append((ms + 500, after_sp, cap_start(after)))
                post_fixes.append(label)
                continue
        out.append((ms, sp, tx))
    turns = merge_turns(out)

split_on(
    r'(.*(?:enjoy the episode|wieners|does this sound better))\s+(.*(?:three kinds of empathy|cognitive empathy).*)',
    'Jacob', 'Spencer', 'split Jacob open / Spencer empathy')

rescored = []
for i, (ms, sp, tx) in enumerate(turns):
    low = tx.lower()
    sj = score_jacob(tx)
    sg = score_spencer(tx)
    if ms < 120000 and re.search(r'junkyard love|hello and welcome|ahoy|knowledge is power|breathe to heal|max strom|recommendation|enjoy the episode', low):
        sp = 'Jacob'
    elif re.search(r'junkyard love podcast|drink some|get present|hello and welcome|listeners please|peace out|knowledge is power|ahoy', low):
        sp = 'Jacob'
    elif sj > sg + 2:
        sp = 'Jacob'
    elif sg > sj + 2:
        sp = 'Spencer'
    if ms >= DURATION_S * 1000 - 120000 and re.search(r'peace out|junkyard|drink some|listeners|get present|enjoy your (?:day|life)|instagram|facebook|love yourself', low):
        if re.search(r'listeners|drink some|get present|enjoy your|peace out|junkyard', low):
            sp = 'Jacob'
    if sp != turns[i][1]:
        fixes.append(f'rescore {turns[i][1]}->{sp} @ {ms}')
    rescored.append((ms, sp, tx))
turns = merge_turns(rescored)

word_count = sum(len(t.split()) for _, _, t in turns)

def ms_to_ts(ms):
    s = int(ms // 1000)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f'{h:02d}:{m:02d}:{sec:02d}'

def ts_to_anchor(ts):
    return 't-' + ts.replace(':', '-')

def fmt_ts_from_s(s):
    s = int(s)
    return f'{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}'

def anchor_id_s(s):
    return 't-' + fmt_ts_from_s(s).replace(':', '-')

def duration_iso(seconds):
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f'PT{h}H{m}M{s}S' if h else f'PT{m}M{s}S'

def sec_to_hms(s):
    h, rem = divmod(int(s), 3600)
    m, sec = divmod(rem, 60)
    return f'{h}:{m:02d}:{sec:02d}' if h else f'{m}:{sec:02d}'

DURATION_HUMAN = sec_to_hms(DURATION_S)
DURATION_ISO = duration_iso(DURATION_S)

def find(substr, speaker=None):
    for ms, sp, t in turns:
        if speaker and sp != speaker:
            continue
        if substr.lower() in t.lower():
            return ms / 1000.0, sp, t
    return None

def extract_quote_from_turn(t, needle, max_words=28):
    idx = t.lower().find(needle.lower())
    if idx < 0:
        return None
    start = max(0, idx - 20)
    while start > 0 and t[start] not in ' .!?':
        start -= 1
    chunk = t[start:].strip(' .,\n')
    words = chunk.split()
    return ' '.join(words[:max_words]).strip(' ,;')

quote_needles = [
    ('cognitive empathy', None),
    ('compassionate empathy', None),
    ('parasympathetic', None),
    ('sympathetic', None),
    ('breathwork', None),
    ('breath work', None),
    ('cold shower', None),
    ('caffeine', None),
    ('sensory deprivation', None),
    ('deprivation tank', None),
    ('cortisol', None),
    ('awkward', None),
    ('social anxiety', None),
    ('sleep', 'Spencer'),
    ('breathe to heal', 'Jacob'),
    ('Max Strom', 'Jacob'),
    ('drink some', 'Jacob'),
    ('get present', 'Jacob'),
    ('junkyard love', 'Jacob'),
]

quotes_ap = []
seen_q = set()
for needle, spk in quote_needles:
    hit = find(needle, spk) if spk else find(needle, None)
    if not hit and spk:
        hit = find(needle, None)
    if not hit:
        continue
    s, sp, tx = hit
    q = extract_quote_from_turn(tx, needle)
    if not q or len(q.split()) < 5:
        idx = tx.lower().find(needle.lower())
        q = tx[max(0, idx - 5): idx + 140].strip()
        q = re.sub(r'^(and|but|so|um|,|\s)+', '', q, flags=re.I)
    key = (fmt_ts_from_s(s), sp)
    if key in seen_q:
        continue
    qkey = q[:50].lower()
    if any(abs(s - ss) < 3 and qkey[:30] in qq.lower() for ss, _, qq in quotes_ap):
        continue
    seen_q.add(key)
    quotes_ap.append((s, sp, q))
    if len(quotes_ap) >= 12:
        break

yt_info = json.loads((CONTENT / 'source-yt.info.json').read_text(encoding='utf-8'))
yt_chapters = yt_info.get('chapters') or []
chapters = []
used = set()
if yt_chapters:
    for ch in yt_chapters:
        s = float(ch.get('start_time') or 0)
        label = (ch.get('title') or '').strip() or 'Chapter'
        if label.startswith('<Untitled'):
            label = 'Opening — Junkyard Love / Spencer Hicks'
        aid = anchor_id_s(s)
        if aid in used:
            continue
        used.add(aid)
        chapters.append((s, label))
else:
    chapter_needles = [
        (10, 'hello and welcome', 'Opening bumper — Junkyard Love / knowledge is power'),
        (70, 'ahoy', 'New intro / Ahoy'),
        (100, 'breathe to heal', 'Recommendation — Max Strom Breathe to Heal TED Talk'),
        (130, 'cognitive empathy', 'Three kinds of empathy'),
        (260, 'sympathy', 'Sympathy vs empathy / social norms'),
        (700, 'suffering', 'Suffering / reducing total suffering'),
        (1000, 'parasympathetic', 'Parasympathetic vs sympathetic state'),
        (1650, 'awkward', 'Allowing awkwardness / meeting people from the internet'),
        (1680, 'anxiety', 'Social anxiety / real-life conversations'),
        (2470, 'stress', 'Stress / fight-or-flight / body-mind'),
        (2810, 'nervous system', 'Sympathetic nervous system / cortisol / adrenaline'),
        (3145, 'stretch', 'Breathwork / stretching / anxiety & depression'),
        (3370, 'caffeine', 'Caffeine cutoff / sleep tips'),
        (3560, 'cold shower', 'Cold showers'),
        (3900, 'phone in the bedroom', 'Phone in the bedroom / shutting down the mind'),
        (4200, 'phone', 'Phone control / sleep environment'),
        (4660, 'sensory deprivation', 'Sensory deprivation / float tanks'),
        (4730, 'be kind to yourself', 'Close — be kind / take care of yourself'),
        (None, 'take care of yourself', 'Outro — take care of yourself'),
    ]
    for target, needle, label in chapter_needles:
        hit = find(needle, None)
        if not hit:
            continue
        s, sp, tx = hit
        if target is not None:
            best = None
            for ms, sp2, t2 in turns:
                if needle.lower() in t2.lower():
                    dist = abs(ms / 1000.0 - target)
                    if best is None or dist < best[0]:
                        best = (dist, ms / 1000.0, sp2, t2)
            if best and best[0] < 300:
                s = best[1]
        else:
            last = None
            for ms, sp2, t2 in turns:
                if needle.lower() in t2.lower():
                    last = (ms / 1000.0, sp2, t2)
            if last:
                s = last[0]
            else:
                continue
        aid = anchor_id_s(s)
        if aid in used:
            continue
        used.add(aid)
        chapters.append((s, label))
    chapters.sort(key=lambda x: x[0])

keywords = (
    'Spencer Hicks, Episode 023 with Spencer Hicks, '
    'Junkyard Love Podcast episode 0023, JYLP 0023, cognitive empathy, '
    'parasympathetic, sympathetic, breathwork, stress, sleep, cold showers, '
    'caffeine, phone control, sensory deprivation, float tank, social anxiety, '
    'Max Strom, Breathe to Heal, Jacob Rhines'
)
hashtags = (
    '#SpencerHicks #JYLP0023 #JunkyardLove #Breathwork #Empathy '
    '#Parasympathetic #SleepTips #ColdShower #FloatTank #JYLP'
)
guest_bio = (
    'Spencer Hicks appears on Junkyard Love episode 0023 as a science-boy, armchair '
    'philosopher, fitness enthusiast, and motivational speaker. Jacob and Spencer discuss '
    'matters of mind, body, and spirit — cognitive/emotional/compassionate empathy, sympathy, '
    'suffering, social norms, and Jacob’s social anxiety; meeting people known from the internet '
    'and allowing awkwardness in real-life conversation; parasympathetic vs sympathetic states; '
    'stress, breathwork, and tips for poor breathing habits; what the body-mind does under stress; '
    'sleep tips; and touch-and-go topics including cold showers, caffeine intake, phone control, '
    'and sensory deprivation tanks. Inventory has_quotes=no / has_timestamps=no / has_hashtags=no / '
    'has_guest_links=no. Guest slug spencer-hicks is EXISTING (0088 + 0074 + 0059 + 0044 + 0038); '
    'this episode is appended. No guest contact/email.'
)

picks_md = [
    '# Archive picks (not from published notes)',
    '',
    'Extracted from the YouTube auto-caption transcript and published About already on this episode. '
    'Labeled separately from Jacob’s published About / Chapters / Quotes / Hashtags.',
    '',
    '## Memorable quotes',
    '',
]
for s, sp, q in quotes_ap[:12]:
    picks_md.append(f'- [{fmt_ts_from_s(s)}] {sp}: “{q}”')
picks_md += ['', '## Chapter-style timestamps', '']
for s, label in chapters:
    picks_md.append(f'- [{fmt_ts_from_s(s)}](#{anchor_id_s(s)}) — {label}')
picks_md += [
    '', '## Keywords', '', keywords, '', '## Hashtags', '', hashtags, '',
    '## Short guest bio (from episode speech + published About/links)', '', guest_bio, '',
]
(CONTENT / 'source-archive-picks.md').write_text('\n'.join(picks_md), encoding='utf-8')

md_lines = []
html_parts = []
for ms, sp, text in turns:
    ts = ms_to_ts(ms)
    md_lines.append(f'[{ts}] {sp}: {text}')
    md_lines.append('')
    html_parts.append(
        f'<p class="cue" id="{ts_to_anchor(ts)}"><a class="ts" href="#{ts_to_anchor(ts)}">[{ts}]</a> '
        f'<span class="speaker">{escape(sp)}:</span> {escape(text)}</p>'
    )

transcript_md = '\n'.join(md_lines).rstrip() + '\n'
transcript_html = '\n'.join(html_parts) + '\n'
(CONTENT / 'transcript.md').write_text(transcript_md, encoding='utf-8')
(CONTENT / 'transcript.html').write_text(transcript_html, encoding='utf-8')

balance = Counter()
words_by = Counter()
for _, sp, t in turns:
    balance[sp] += 1
    words_by[sp] += len(t.split())

(CONTENT / 'TRANSCRIPT_SOURCE.txt').write_text(
    f"Source: YouTube automatic captions en/en-orig (captions.en.vtt / captions.en.json3; also archived as source-yt.en*); no official/manual track; no >> diarization markers\n"
    f"Video: {YOUTUBE}\n"
    f"Turns: {len(turns)}\n"
    f"Word count: {word_count}\n"
    "Speaker map: pause-gap segmentation + sticky Jacob/Spencer content scoring (named speaker labels not present in captions; auto diarization imperfect); host bumper forced to Jacob where clear\n"
    "Cleanup: light dedupe of consecutive duplicate words; merged consecutive same-speaker fragments; HTML entities/nbsp unescaped; capitalized turn starts after merge; light caption spacing tidy; light ASR name tidy (Spencer Hicks; Max Strom; Breathe to Heal; TED Talk; Junkyard Love); bumper/outro forced to Jacob where clear; YouTube swear blanks normalized to ****\n"
    "No sentence rewriting.\n"
    f"Guest name spelling: Spencer Hicks (YT/RSS titles / inventory); slug {GUEST_SLUG} (EXISTING — APPEND 0023 to 0088+0074+0059+0044+0038, do not wipe).\n"
    "Note: automatic diarization is imperfect; remaining short backchannels and some mid-turn blends may still be swapped in places.\n"
    f"Issue: YouTube automatic captions (en/en-orig) used; no official/manual track; no >> speaker flips. YT duration {YT_DURATION_S}s vs RSS/inventory {DURATION_S}s (archive meta uses RSS duration). No published chapter timestamps; no YT chapters. Title {TITLE_CONFLICT}. About YT~RSS identical body ((4) series marker stripped; YT footer stripped). Inventory has_quotes=no / has_timestamps=no / has_hashtags=no / has_guest_links=no. Archive picks fills timestamped quotes/chapters/keywords/hashtags/bio. Guest page: {GUEST_SLUG} (EXISTING APPEND).\n"
    f"Speaker balance: Jacob {balance.get('Jacob',0)} turns/{words_by.get('Jacob',0)} words; Spencer {balance.get('Spencer',0)} turns/{words_by.get('Spencer',0)} words.\n"
    f"Heuristic speaker fixes: {len(fixes)}; post-splits: {len(post_fixes)} ({'; '.join(post_fixes)})\n",
    encoding='utf-8',
)

(CONTENT / 'SOURCES.txt').write_text(
    "Description source: YouTube primary per archive rules; About spaced from YT/RSS plain description (~itunes:summary). (4) series marker stripped. YT footer stripped. No guest contact/email.\n"
    f"YouTube chars: {len(yt_desc.strip())}\n"
    f"RSS HTML chars: {len(rss_html.strip())}\n"
    f"Title source: YT=RSS exact match ({VIDEO_ID}). H1/slug use Episode 023 with Spencer Hicks. {TITLE_CONFLICT}.\n"
    f"Title: {TITLE}\n"
    f"RSS title: {RSS_TITLE}\n"
    "Chapters source: none published in episode notes (inventory has_timestamps=no); no YT chapters\n"
    "Guest links: none published (inventory has_guest_links=no)\n"
    f"Quotes: {len(published_quotes)} published quotes (inventory has_quotes=no)\n"
    "Hashtags: none published (inventory has_hashtags=no)\n"
    "About: Jacob published description verbatim as spaced paras from YouTube/RSS\n"
    f"Guest name spelling: Spencer Hicks; guest slug {GUEST_SLUG} (EXISTING — APPEND 0023; prior 0088+0074+0059+0044+0038 preserved)\n"
    f"Duration: RSS itunes:duration {DURATION_S}s ({DURATION_HUMAN}); YT info.json duration {YT_DURATION_S}s — using RSS/inventory {DURATION_S}\n"
    "Publish date: RSS/inventory 2020-02-02 (YT upload_date 20200202)\n"
    "Archive picks: added (timestamped transcript quotes, chapter-style timestamps, keywords/hashtags, short guest bio) — extracted from YT auto-caption transcript + published About; kept separate from Jacob published About/Chapters/Quotes.\n"
    "Captions: freshly downloaded source-yt.en-orig.* / en.* this run (auto only; en identical to en-orig; no official en track).\n",
    encoding='utf-8',
)

meta = {
    'episode_number': EP_NUM,
    'episodeNumber': EP_INT,
    'title': TITLE,
    'rss_title': RSS_TITLE,
    'guest': GUEST,
    'datePublished': DATE,
    'duration_seconds': DURATION_S,
    'duration_iso': DURATION_ISO,
    'duration_human': DURATION_HUMAN,
    'youtube_url': YOUTUBE,
    'rss_url': RSS_URL,
    'audio_url': AUDIO_URL,
    'spotify_show': SPOTIFY,
    'apple_show': APPLE,
    'slug': EP_SLUG,
    'guest_slug': GUEST_SLUG,
    'title_conflict': TITLE_CONFLICT,
}
(CONTENT / 'meta.json').write_text(json.dumps(meta, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

guest_md_link = f'[{GUEST}](/guests/{GUEST_SLUG}/)'
ep_md = [f'# {TITLE}', '',
         f'- Episode: {EP_NUM}',
         f'- Date: {DATE}', f'- Duration: {DURATION_HUMAN} ({DURATION_S}s)',
         f'- Guest: {guest_md_link}', f'- YouTube: {YOUTUBE}', f'- RSS: {RSS_URL}',
         f'- Audio: {AUDIO_URL}', '',
         '## About', '', about_md.strip(), '', '## Chapters', '',
         '(none published in episode notes)', '',
         '## Quotes', '', '\n'.join(quotes_md_lines), '',
         '## Guest links', '', '(none published in episode notes)', '']
ep_md += ['', '## Archive picks', '', '\n'.join(picks_md), '', '## Transcript', '', transcript_md]
(CONTENT / 'episode.md').write_text('\n'.join(ep_md), encoding='utf-8')

ep_dir = SITE / 'episodes' / EP_SLUG
ep_dir.mkdir(parents=True, exist_ok=True)
shutil.copy(CONTENT / 'episode.md', ep_dir / 'episode.md')
shutil.copy(CONTENT / 'TRANSCRIPT_SOURCE.txt', ep_dir / 'TRANSCRIPT_SOURCE.txt')

def para_to_html(p: str) -> str:
    if '\n' in p:
        lines = [escape(ln.strip()) for ln in p.split('\n') if ln.strip()]
        return '<p>' + '<br>\n'.join(lines) + '</p>'
    return f'<p>{escape(p)}</p>'

about_html = '\n'.join(para_to_html(p) for p in about_paras)
quotes_html = '<p class="note">(none published in episode notes)</p>'
links_html = '<p class="note">(none published in episode notes)</p>'

archive_quotes_html = '\n'.join(
    f'<blockquote class="archive-quote"><a class="ts" href="#{anchor_id_s(s)}">[{fmt_ts_from_s(s)}]</a> '
    f'<span class="speaker">{escape(sp)}:</span> “{escape(q)}”</blockquote>'
    for s, sp, q in quotes_ap[:12]
)
archive_chapters_html = '\n'.join(
    f'<li><a href="#{anchor_id_s(s)}">{fmt_ts_from_s(s)}</a> — {escape(label)}</li>'
    for s, label in chapters
)
archive_note = (
    'Not from Jacob’s published episode notes — extracted from this episode’s transcript '
    '(and the published About already above). Published About / Chapters / Quotes / Guest links blocks above stay unchanged; '
    'Archive picks add timestamps, chapters, keywords/hashtags, and a short bio where published notes lacked them or need enrichment.'
)

ld_keywords = keywords + ', Spencer Hicks, Jacob Rhines, Junkyard Love Podcast'
ld = {
    '@context': 'https://schema.org',
    '@type': 'PodcastEpisode',
    'name': TITLE,
    'datePublished': DATE,
    'duration': DURATION_ISO,
    'episodeNumber': EP_INT,
    'url': f'{SITE_BASE}/episodes/{EP_SLUG}/',
    'partOfSeries': {
        '@type': 'PodcastSeries',
        'name': 'The Junkyard Love Podcast',
        'url': 'https://www.youtube.com/@TheJunkyardLovePodcast',
    },
    'author': {'@type': 'Person', 'name': 'Jacob Rhines'},
    'contributor': [
        {'@type': 'Person', 'name': 'Jacob Rhines'},
        {'@type': 'Person', 'name': GUEST},
    ],
    'associatedMedia': [
        {'@type': 'VideoObject', 'contentUrl': YOUTUBE, 'name': TITLE},
        {'@type': 'AudioObject', 'contentUrl': AUDIO_URL, 'name': TITLE},
    ],
    'transcript': transcript_md.strip(),
    'keywords': ld_keywords,
    'description': about_md.strip(),
}

guest_meta_html = f'<a href="../../guests/{GUEST_SLUG}/index.html">{escape(GUEST)}</a>'

index_html = """<!DOCTYPE html>
<html lang="en">
<head>
<base href="/junkyard-love-archive/">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<link rel="stylesheet" href="../../assets/style.css">
</head>
<body>
<div class="wrap">
<header class="site">
  <a class="brand" href="../../index.html">The Junkyard Love Podcast</a>
  <nav>
    <a href="../../episodes/index.html">Episodes</a>
    <a href="../../guests/index.html">Guests</a>
    <a href="../../llms.txt">llms.txt</a>
  </nav>
</header>

<script type="application/ld+json">
__LD__
</script>
<article>
<h1>__TITLE__</h1>
<p class="meta">Episode __EPNUM__ · __DATE__ · __DUR__ · Guest: __GUESTMETA__</p>
<div class="listen">
  <a href="__YT__">YouTube</a>
  <a href="__SPOTIFY__">Spotify (show)</a>
  <a href="__APPLE__">Apple (show)</a>
  <a href="__RSS__">RSS episode</a>
</div>
<h2>About</h2>
<div class="about">
__ABOUT__
</div>
<h2>Chapters</h2>
<p class="note">(none published in episode notes)</p>
<h2>Quotes</h2>
__QUOTES__
<h2>Guest links</h2>
__LINKS__
<h2>Archive picks</h2>
<p class="note">__ARCHNOTE__</p>
<div class="card archive-picks">
<h3>Memorable quotes</h3>
__ARCHQ__
<h3>Chapter-style timestamps</h3>
<ul class="chapters">
__ARCHC__
</ul>
<h3>Keywords</h3>
<p>__KW__</p>
<h3>Hashtags</h3>
<p>__HT__</p>
<h3>Short guest bio</h3>
<p>__BIO__</p>
</div>
<h2>Transcript</h2>
<p class="note">From YouTube automatic captions; light cleanup; speaker labels via imperfect auto diarization (Jacob/Spencer may be swapped in places).</p>
<div class="transcript">
__TRANS__</div>
</article>

<footer>
  <p>The Junkyard Love Podcast — Jacob Rhines · <a href="../../guests/index.html">Guest index</a></p>
</footer>
</div>
</body>
</html>
"""
index_html = (index_html
    .replace('__TITLE__', escape(TITLE))
    .replace('__LD__', json.dumps(ld, ensure_ascii=False, indent=2))
    .replace('__EPNUM__', EP_NUM)
    .replace('__DATE__', DATE)
    .replace('__DUR__', DURATION_HUMAN)
    .replace('__GUESTMETA__', guest_meta_html)
    .replace('__YT__', YOUTUBE)
    .replace('__SPOTIFY__', SPOTIFY)
    .replace('__APPLE__', APPLE)
    .replace('__RSS__', RSS_URL)
    .replace('__ABOUT__', about_html)
    .replace('__QUOTES__', quotes_html)
    .replace('__LINKS__', links_html)
    .replace('__ARCHNOTE__', escape(archive_note))
    .replace('__ARCHQ__', archive_quotes_html)
    .replace('__ARCHC__', archive_chapters_html)
    .replace('__KW__', escape(keywords))
    .replace('__HT__', escape(hashtags))
    .replace('__BIO__', escape(guest_bio))
    .replace('__TRANS__', transcript_html)
)
(ep_dir / 'index.html').write_text(index_html, encoding='utf-8')

# Guest page EXISTS (0088 + 0074 + 0059 + 0044 + 0038) — APPEND 0023 (do not wipe)
guest_dir = SITE / 'guests' / GUEST_SLUG
guest_dir.mkdir(parents=True, exist_ok=True)
bio_html = '\n'.join(f'<p>{escape(p)}</p>' for p in about_paras)

about_0088 = '<p>&quot;Spencer Hicks, Bachelor in arts of strategic communication; studies semiotics, enjoyed Hegelian dialectics and eats from the trash can of ideology.&quot;</p>'
about_0074 = '<p>Spencer is an armchair philosopher with focus in metaphysics, political philanthropy, ethics, and epistemology.</p>'
about_0059 = '<p>An important series introduction is presented in the form of a short audio essay that exists in the first ten minutes of this episode. I encourage you to listen for a better understanding of what to expect.</p>'
about_0044 = (
    '<p>I am joined by my friend Spencer Hicks, personal trainer, and we discuss varying self-development and health topics - including inflammation, obesity, self-sovereignty, exploring varying world-views and the shoes that fit them, questioning our own ideas, improving our knowledge and emotional database, enhancing conversations, becoming aware of our thoughts and deflecting discomfort.</p>\n'
    '<p>We tip the iceberg of a much larger conversation on the art of rhetoric and the current protests amidst the overarching world situation - fueled by the misleading media propaganda machine.</p>\n'
    '<p>We talk about conspiracy theories, humanities classes, government corruption, some thought experiments and personal observations for the future of humanity, some ways to navigate difficult conversations, Neuralink, wealth gaps, and remaining faithful and optimistic for the future of civilization.</p>\n'
    '<p>A hopeful contribution to the bigger conversation and larger view - enjoy episode 044.</p>'
)
about_0038 = (
    '<p>Spencer and I video chat about some at-home practices and techniques to better suit each of us amidst the current covid retreat.</p>\n'
    '<p>We include some recommendations for walking, stretching, at-home workouts, mindfulness, awareness and general at-home health.</p>\n'
    '<p>Spencer and I discuss concepts that hopefully aide and assist any listeners during this stay-at-home order.</p>\n'
    '<p>The audio is subpar in comparison to our normal episodes here but it&#x27;s easy to get used to in a minute or two.</p>\n'
    '<p>For more info on Spencer, check out our older conversations and episode descriptions.</p>'
)
existing_guest = guest_dir / 'index.html'
if existing_guest.exists():
    old = existing_guest.read_text(encoding='utf-8')
    for ep_label, key, varname in [
        ('0088', 'Bachelor in arts', '0088'),
        ('0074', 'armchair philosopher', '0074'),
        ('0059', 'series introduction', '0059'),
        ('0044', 'personal trainer', '0044'),
        ('0038', 'at-home practices', '0038'),
    ]:
        m = re.search(
            rf'<h3>Episode {ep_label}</h3>\s*<div class="about">\s*(.*?)\s*</div>',
            old, re.S,
        )
        if m and key.split()[0].lower() in m.group(1).lower():
            snippet = m.group(1).strip()
            if varname == '0088':
                about_0088 = snippet
            elif varname == '0074':
                about_0074 = snippet
            elif varname == '0059':
                about_0059 = snippet
            elif varname == '0044':
                about_0044 = snippet
            else:
                about_0038 = snippet

guest_html = """<!DOCTYPE html>
<html lang="en">
<head>
<base href="/junkyard-love-archive/">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__NAME__ — The Junkyard Love Podcast</title>
<link rel="stylesheet" href="../../assets/style.css">
</head>
<body>
<div class="wrap">
<header class="site">
  <a class="brand" href="../../index.html">The Junkyard Love Podcast</a>
  <nav>
    <a href="../../episodes/index.html">Episodes</a>
    <a href="../../guests/index.html">Guests</a>
    <a href="../../llms.txt">llms.txt</a>
  </nav>
</header>

<h1>__NAME__</h1>
<p class="note">Appeared on The Junkyard Love Podcast (6 episodes)</p>
<h2>Episodes</h2>
<ul class="list">
  <li><a href="../../episodes/0088-spencer-hicks-break-the-hammer/index.html">The JYLP ep. 088 with Bachelor In Arts Of Strategic Communication Spencer Hicks - Break The Hammer</a><br><span class="note">2022-08-02 · Episode 0088</span></li>
  <li><a href="../../episodes/0074-spencer-hicks-dialectics-and-communication-breakdown/index.html">Ep 074 w/ Spencer Hicks - Dialectics and Communication Breakdown - A Meta-Analysis of Cancel Culture</a><br><span class="note">2021-07-15 · Episode 0074</span></li>
  <li><a href="../../episodes/0059-spencer-hicks-the-sense-making-sickness-series-part-1/index.html">Episode 059 - The Sense Making Sickness - with Spencer Hicks - Series Part 1</a><br><span class="note">2020-10-20 · Episode 0059</span></li>
  <li><a href="../../episodes/0044-spencer-hicks-operating-optimally-should-be-your-goal/index.html">Episode 044 with Spencer Hicks - Operating Optimally Should Be Your Goal</a><br><span class="note">2020-06-10 · Episode 0044</span></li>
  <li><a href="../../episodes/0038-spencer-hicks-mental-and-physical-tips-to-maintain-health-at-home/index.html">Episode 038 with Spencer Hicks   Mental and Physical Tips To Maintain Health At Home</a><br><span class="note">2020-04-26 · Episode 0038</span></li>
  <li><a href="../../episodes/__SLUG__/index.html">__TITLE__</a><br><span class="note">__DATE__ · Episode __EPNUM__</span></li>
</ul>
<h2>From the episode notes</h2>
<p class="note">Copied from published episode descriptions (not a new biography).</p>
<h3>Episode 0088</h3>
<div class="about">
__ABOUT0088__
</div>
<h3>Episode 0074</h3>
<div class="about">
__ABOUT0074__
</div>
<h3>Episode 0059</h3>
<div class="about">
__ABOUT0059__
</div>
<h3>Episode 0044</h3>
<div class="about">
__ABOUT0044__
</div>
<h3>Episode 0038</h3>
<div class="about">
__ABOUT0038__
</div>
<h3>Episode __EPNUM__</h3>
<div class="about">
__BIO__
</div>
<h2>Guest links</h2>
<p class="note">(none published in episode notes)</p>

<footer>
  <p>The Junkyard Love Podcast — Jacob Rhines · <a href="../../guests/index.html">Guest index</a></p>
</footer>
</div>
</body>
</html>
"""
guest_html = (guest_html
    .replace('__NAME__', escape(GUEST))
    .replace('__EPNUM__', EP_NUM)
    .replace('__SLUG__', EP_SLUG)
    .replace('__TITLE__', escape(TITLE))
    .replace('__DATE__', DATE)
    .replace('__ABOUT0088__', about_0088)
    .replace('__ABOUT0074__', about_0074)
    .replace('__ABOUT0059__', about_0059)
    .replace('__ABOUT0044__', about_0044)
    .replace('__ABOUT0038__', about_0038)
    .replace('__BIO__', bio_html)
)
(guest_dir / 'index.html').write_text(guest_html, encoding='utf-8')

home_li = (
    f'  <li><a href="episodes/{EP_SLUG}/index.html">{escape(TITLE)}</a>'
    f'<br><span class="note">{DATE} · {escape(GUEST)} · {DURATION_HUMAN}</span></li>\n'
)
ep_li = (
    f'  <li><a href="episodes/{EP_SLUG}/index.html">{escape(TITLE)}</a>'
    f'<br><span class="note">Episode {EP_NUM} · {DATE} · {DURATION_HUMAN} · Guest: {escape(GUEST)}</span></li>\n'
)

# Insert AFTER 0024 (descending: 0024 then 0023)
marker_home = (
    '  <li><a href="episodes/0024-maxx-v-payne/index.html">'
    'Episode 024 with Maxx V. Payne</a>'
    '<br><span class="note">2020-02-10 · Maxx V. Payne · 1:49:32</span></li>\n'
)
marker_ep = (
    '  <li><a href="episodes/0024-maxx-v-payne/index.html">'
    'Episode 024 with Maxx V. Payne</a>'
    '<br><span class="note">Episode 0024 · 2020-02-10 · 1:49:32 · Guest: Maxx V. Payne</span></li>\n'
)

home = (SITE / 'index.html').read_text(encoding='utf-8')
if EP_SLUG not in home:
    if marker_home not in home:
        raise SystemExit('home 0024 marker not found')
    home = home.replace(marker_home, marker_home + home_li)
    (SITE / 'index.html').write_text(home, encoding='utf-8')

ep_index = (SITE / 'episodes' / 'index.html').read_text(encoding='utf-8')
if EP_SLUG not in ep_index:
    if marker_ep not in ep_index:
        raise SystemExit('ep index 0024 marker not found')
    ep_index = ep_index.replace(marker_ep, marker_ep + ep_li)
    (SITE / 'episodes' / 'index.html').write_text(ep_index, encoding='utf-8')

# Guest EXISTS — already on guests index (spencer-hicks); do not re-insert

sm = (SITE / 'sitemap.xml').read_text(encoding='utf-8')
if EP_SLUG not in sm:
    insert = (
        f'  <url><loc>{SITE_BASE}/episodes/{EP_SLUG}/</loc></url>\n'
        f'  <url><loc>{SITE_BASE}/episodes/{EP_SLUG}/episode.md</loc></url>\n'
    )
    m24 = f'  <url><loc>{SITE_BASE}/episodes/0024-maxx-v-payne/episode.md</loc></url>\n'
    if m24 not in sm:
        raise SystemExit('sitemap 0024 marker not found')
    sm = sm.replace(m24, m24 + insert)
    (SITE / 'sitemap.xml').write_text(sm, encoding='utf-8')
# Guest already in sitemap (spencer-hicks)

llms = (SITE / 'llms.txt').read_text(encoding='utf-8')
if EP_SLUG not in llms:
    ep_line = (
        f'- [0023 Spencer Hicks]'
        f'({SITE_BASE}/episodes/{EP_SLUG}/) — {DATE}\n'
    )
    m24_line = (
        f'- [0024 Maxx V. Payne]'
        f'({SITE_BASE}/episodes/0024-maxx-v-payne/) — 2020-02-10\n'
    )
    if m24_line not in llms:
        raise SystemExit('llms 0024 ep line not found')
    llms = llms.replace(m24_line, m24_line + ep_line)
    md_line = f'- [{SITE_BASE}/episodes/{EP_SLUG}/episode.md]({SITE_BASE}/episodes/{EP_SLUG}/episode.md)\n'
    m24_md = (
        f'- [{SITE_BASE}/episodes/0024-maxx-v-payne/episode.md]'
        f'({SITE_BASE}/episodes/0024-maxx-v-payne/episode.md)\n'
    )
    if m24_md in llms and md_line not in llms:
        llms = llms.replace(m24_md, m24_md + md_line)
    (SITE / 'llms.txt').write_text(llms, encoding='utf-8')
# Guest already listed in llms

readme = (ROOT / 'README.md').read_text(encoding='utf-8')
if EP_SLUG not in readme and '**0023**' not in readme:
    marker = '- **0024** Maxx V. Payne — `site/episodes/0024-maxx-v-payne/`\n'
    add = '- **0023** Spencer Hicks — `site/episodes/0023-spencer-hicks/`\n'
    if marker not in readme:
        raise SystemExit('README 0024 marker not found')
    readme = readme.replace(marker, marker + add)
    (ROOT / 'README.md').write_text(readme, encoding='utf-8')

if DEPLOY.exists():
    dep_ep = DEPLOY / 'episodes' / EP_SLUG
    if dep_ep.exists():
        shutil.rmtree(dep_ep)
    shutil.copytree(SITE / 'episodes' / EP_SLUG, dep_ep)
    dep_g = DEPLOY / 'guests' / GUEST_SLUG
    if dep_g.exists():
        shutil.rmtree(dep_g)
    shutil.copytree(SITE / 'guests' / GUEST_SLUG, dep_g)
    src_content = DEPLOY / '_sources' / 'content' / EP_SLUG
    if src_content.parent.exists():
        if src_content.exists():
            shutil.rmtree(src_content)
        shutil.copytree(CONTENT, src_content)
    for name in ('index.html', 'llms.txt', 'sitemap.xml'):
        shutil.copy(SITE / name, DEPLOY / name)
    shutil.copy(SITE / 'episodes' / 'index.html', DEPLOY / 'episodes' / 'index.html')
    shutil.copy(SITE / 'guests' / 'index.html', DEPLOY / 'guests' / 'index.html')
    if (DEPLOY / 'README.md').exists():
        shutil.copy(ROOT / 'README.md', DEPLOY / 'README.md')
    if (DEPLOY / '_sources').exists():
        shutil.copy(ROOT / 'build_0023.py', DEPLOY / '_sources' / 'build_0023.py')
    print('deploy synced (no commit/push)')

print('DONE')
print('slug', EP_SLUG)
print('guest', GUEST_SLUG, 'EXISTING APPEND — episodes after update: 0088, 0074, 0059, 0044, 0038, 0023')
print('H1', TITLE)
print('title_conflict', TITLE_CONFLICT)
print('turns', len(turns), 'words', word_count)
print('about paras', len(about_paras))
print('published quotes', len(published_quotes))
print('quotes_ap', len(quotes_ap), 'archive_chapters', len(chapters))
print('balance', dict(balance), dict(words_by))
print('About paras:')
for i, para in enumerate(about_paras):
    print(f'  [{i}] {para[:160].replace(chr(10), " / ")}')
print('First 8:')
for ms, sp, tx in turns[:8]:
    print(f'[{ms_to_ts(ms)}] {sp:12s} {len(tx.split()):4d}w | {tx[:100]}')
print('Last 5:')
for ms, sp, tx in turns[-5:]:
    print(f'[{ms_to_ts(ms)}] {sp:12s} {len(tx.split()):4d}w | {tx[:100]}')
print('Archive picks chapters:')
for s, label in chapters:
    print(f'  [{fmt_ts_from_s(s)}] {label}')
print('Archive quotes:')
for s, sp, q in quotes_ap:
    print(f'  [{fmt_ts_from_s(s)}] {sp}: {q[:80]}')
