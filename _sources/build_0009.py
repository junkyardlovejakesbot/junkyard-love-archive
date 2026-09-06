#!/usr/bin/env python3
"""Process Junkyard Love episode 0009 — Shaden 'Hvshi' Nugent (single guest, NEW).
YT=RSS titles match exactly ("Episode 009 with Shaden 'Hvshi' Nugent").
About YT~RSS identical body after YT footer strip; inventory
has_quotes=no, has_timestamps=no, has_hashtags=no, has_guest_links=no.
Guest slug: shaden-hvshi-nugent (NEW — nickname-in-slug like nate-nastynate pattern).
YouTube auto-captions available (en/en-orig). YT duration ~3882s vs RSS 3854s (~28s —
not substantial; meta uses RSS). No YouTube chapter markers — Archive picks from transcript.
Archive picks required. Imperfect auto diarization flagged. No guest contact/email.
Insert indexes after 0010. After 0009, next catalog is 0008 Nate NastyNate Tanzman (do not build here)."""
from __future__ import annotations
import json, re, shutil
from pathlib import Path
from html import escape, unescape
from collections import Counter

ROOT = Path('/workspace/junkyard-love-archive')
CONTENT = ROOT / 'content/0009-shaden-hvshi-nugent'
SITE = ROOT / 'site'
DEPLOY = Path('/workspace/junkyard-love-archive-deploy')
EP_SLUG = '0009-shaden-hvshi-nugent'
GUEST_SLUG = 'shaden-hvshi-nugent'  # NEW
TITLE = "Episode 009 with Shaden 'Hvshi' Nugent"
RSS_TITLE = TITLE
YT_TITLE = TITLE
GUEST = "Shaden 'Hvshi' Nugent"
GUEST_SHORT = 'Shaden'
GUEST_DISPLAY = "Shaden 'Hvshi' Nugent"
SPK = 'Shaden'
YOUTUBE = 'https://www.youtube.com/watch?v=VijHLQP1MxY'
RSS_URL = 'https://share.transistor.fm/s/f22b63cf'
AUDIO_URL = 'https://2.gum.fm/op3.dev/e/pdcn.co/e/pscrb.fm/rss/p/pdst.fm/e/dts.podtrac.com/redirect.mp3/media.transistor.fm/f22b63cf/29ab26fa.mp3'
DATE = '2019-12-11'
DURATION_S = 3854  # RSS / inventory (~1:04:14)
YT_DURATION_S = 3882  # YT info.json (~1:04:42); ~28s delta — not substantial
EP_NUM = '0009'
EP_INT = 9
SPOTIFY = 'https://open.spotify.com/show/45J7CBdM8j29doqyBp2bFs'
APPLE = 'https://podcasts.apple.com/us/podcast/the-junkyard-love-podcast/id1489118788'
SITE_BASE = 'https://junkyardlovejakesbot.github.io/junkyard-love-archive'
VIDEO_ID = 'VijHLQP1MxY'
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
    f'title={YT_TITLE}\nupload_date=20191212\nduration={YT_DURATION_S}\nvideo_id={VIDEO_ID}\n'
    f'rss_title={RSS_TITLE}\ntitle_conflict={TITLE_CONFLICT}\nh1={TITLE}\n',
    encoding='utf-8',
)

# ---------- ABOUT from YT/RSS (identical body; strip YT footer + (02) marker) ----------
yt_body = yt_desc
for marker in ['\nThe Junkyard Love Podcast', '\n\u2605 Episode details', '\n\u2605 Additional episodes']:
    idx = yt_body.find(marker)
    if idx >= 0:
        yt_body = yt_body[:idx]
yt_body = yt_body.strip()
yt_body = re.sub(r'^\(\d+\)\s*', '', yt_body).strip()
yt_body = re.sub(r'\n(?=[a-z])', ' ', yt_body)
yt_body = re.sub(r'[ \t]+\n', '\n', yt_body)
yt_body = re.sub(r'\n{3,}', '\n\n', yt_body).strip()

rss_body = re.sub(r'^\(\d+\)\s*', '', rss_plain.strip()).strip()
rss_body = re.sub(r'\n(?=[a-z])', ' ', rss_body)
rss_body = re.sub(r'[ \t]+\n', '\n', rss_body)
rss_body = re.sub(r'\n{3,}', '\n\n', rss_body).strip()

if rss_body and abs(len(rss_body) - len(yt_body)) < 80:
    about_src = rss_body
else:
    about_src = yt_body

published_quotes: list[str] = []
# inventory has_quotes=no — no Quotes list block

soft_breaks = [
    'He lays out his last few years',
    'We learn about the man behind',
    'He speaks on his recent healing',
    'We touch a bit on being a fashionable',
    'Shaden has always stood out',
    'As he gets better and understands',
    "There's much more on the horizon",
]
about_paras: list[str] = []
remaining = about_src
for br in soft_breaks:
    idx = remaining.find(br)
    if idx > 40:
        about_paras.append(remaining[:idx].strip())
        remaining = remaining[idx:].strip()
if remaining:
    about_paras.append(remaining)
about_paras = [p for p in about_paras if p]
if len(about_paras) < 2:
    about_paras = [x.strip() for x in re.split(r'\n\s*\n', about_src) if x.strip()]
if len(about_paras) < 1:
    about_paras = [about_src]

(CONTENT / 'source-description.raw.txt').write_text(about_src + '\n', encoding='utf-8')

guest_links: list[str] = []

about_md = '\n\n'.join(about_paras) + '\n'
quotes_md_lines = [
    '(none published — inventory has_quotes=no)'
]
(CONTENT / 'source-about.md').write_text(about_md, encoding='utf-8')
(CONTENT / 'source-quotes.md').write_text('\n'.join(quotes_md_lines) + '\n', encoding='utf-8')
(CONTENT / 'source-timestamps.md').write_text(
    '(none published in episode notes — inventory has_timestamps=no; no YouTube chapter markers — Archive picks derived from transcript)\n',
    encoding='utf-8',
)
(CONTENT / 'source-hashtags.txt').write_text(
    '(none published as a hashtag block — inventory has_hashtags=no)\n',
    encoding='utf-8',
)
(CONTENT / 'source-links.md').write_text('(none published in episode notes)\n', encoding='utf-8')
(CONTENT / 'source-description.md').write_text(
    about_md + '\n## Quotes\n\n' + '\n'.join(quotes_md_lines) + '\n\n## Guest links\n\n(none published in episode notes)\n',
    encoding='utf-8',
)
(CONTENT / 'guest-share-draft.txt').write_text(
    f'Episode {EP_NUM}: {TITLE}\nGuest: {GUEST}\nDate: {DATE}\nYouTube: {YOUTUBE}\nRSS: {RSS_URL}\n'
    f'Title conflict: {TITLE_CONFLICT}\nGuest slug: {GUEST_SLUG} (NEW)\n'
    f'About: YT~RSS identical body; YT footer stripped; no guest contact/email\n'
    f'Transcript: YouTube auto-captions (en/en-orig); YT duration {YT_DURATION_S}s vs RSS {DURATION_S}s (~28s; meta uses RSS); no YT chapters\n',
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
        r'^(Well,? (?:I|so|yeah|we)|Yeah,? (?:so|I|and|we)|So,? (?:I|we|when|in|the|my|like)|I (?:think|was|love|want|had|grew|got|mean|have|always|feel|am|do|did|started|learned|would|went|ended|wrote|was always)|We (?:are|were|have|had|just)|Absolutely|Thank you|Okay|Yes|Right|For me|My (?:name|brother|dad|freedom|fashion)|Um,? (?:I|so|yeah|like)|No problem|Okay so|Hoshi|Hvshi|Shaden)',
        text.strip(), re.I))
    starts_jacob = bool(re.match(
        r'^(Hello|Welcome|Well,? so|So,? (?:let\'s|what|um|Shaden|Hvshi|Hoshi)|Junkyard|Thank you|Yeah,? yeah|Wave|Peace out|Knowledge is|Reality is|Listeners|Cool so|What.?s up|Check it out|Drink some|Now here.?s episode|Ahoy|Okay well folks|All right|Yo listen|Be brave|You.?re awesome listener|give me a little)',
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
        (r'\bshaden \'?hvshi\'? nugent\b', "Shaden 'Hvshi' Nugent"),
        (r'\bshaden nugent\b', 'Shaden Nugent'),
        (r'\bshading\b', 'Shaden'),
        (r'\bshayden\b', 'Shaden'),
        (r'\bshaden\b', 'Shaden'),
        (r'\bhoshi\b', 'Hvshi'),
        (r'\bhashi\b', 'Hvshi'),
        (r'\bhvshi\b', 'Hvshi'),
        (r'\bnugent\b', 'Nugent'),
        (r'\bco so\b', 'Colorado'),
        (r'\bcolorado\b', 'Colorado'),
        (r'\bnative american\b', 'Native American'),
        (r'\bjacob ryan.?s\b', 'Jacob Rhines'),
        (r'\bjake rhines\b', 'Jake Rhines'),
        (r'\bjacob rhines\b', 'Jacob Rhines'),
        (r'\bjunkyard love podcasts?\b', 'Junkyard Love Podcast'),
        (r'\bjunkie? ?i love podcasts?\b', 'Junkyard Love Podcast'),
        (r'\bjunk our love podcast\b', 'Junkyard Love Podcast'),
        (r'\bjunk yard love podcast\b', 'Junkyard Love Podcast'),
        (r'\bjunkyard love\b', 'Junkyard Love'),
        (r'\byoutube\b', 'YouTube'),
        (r'\binstagram\b', 'Instagram'),
        (r'\bfacebook\b', 'Facebook'),
        (r'\btwitter\b', 'Twitter'),
        (r'\bspotify\b', 'Spotify'),
        (r'\bsoundcloud\b', 'SoundCloud'),
        (r'\bhip[- ]?hop\b', 'hip-hop'),
        (r'\bdjing\b', 'DJing'),
        (r'\bdj\b', 'DJ'),
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
        r'\bjacob from the internet\b', r'\bjake rhines\b', r'\bjacob rhines\b',
        r'\bget present\b', r'\bknowledge is power\b',
        r'\bahoy\b', r'\benjoy the episode\b', r'\bhere.?s episode\b',
        r'\bbe brave\b', r'\bi love y.?all\b', r'\bjunkyard love podcast out\b',
        r'\b(?:shaden|hvshi|hoshi) (?:i|welcome|thank|man)\b',
        r'\bglad you.?re here\b', r'\bwelcome to the junkyard',
        r'\bgiving the listeners\b', r'\blisteners if you\b',
        r'\byou are not your thoughts\b', r'\byou.?re awesome listener\b',
        r'\byo listen\b', r'\byou.?re on the junkyard\b',
        r'\bsuper glad to have you\b', r'\bgive me a little bit your story\b',
        r'\bpeople who haven.?t heard of\b', r'\bthis man.?s a rapper\b',
        r'\bany messages for them\b', r'\bi.?m happy to have you\b',
        r'\blet.?s talk about like aliases\b', r'\blet.?s talk mindset\b',
    ]:
        if re.search(pat, tlow):
            s += 4
    if re.search(r'\b(?:you|shaden|hvshi|hoshi)\b', tlow) and ('?' in text or re.search(r'\byou (?:feel|think|said|mentioned|been|had|worked|got)\b', tlow)):
        s += 3
    if '?' in text and len(text.split()) < 90:
        s += 2
    if len(text.split()) <= 12 and re.search(
        r'^(yeah|yes|right|okay|ok|cool|love it|mhm|mm+|exactly|wow|dude|man|perfect|great|beautiful|thanks|you bet|interesting|absolutely)\b', tlow):
        s += 2
    if re.search(r'\byou (?:guys|mentioned|said|feel|think|know|been|had|went|worked)\b', tlow):
        s += 2
    return s


def score_shaden(text):
    tlow = text.lower()
    s = 0
    for pat in [
        r'\bskater\b', r'\bskate\b', r'\bpro skater\b', r'\bskate park\b',
        r'\brapper\b', r'\brap\b', r'\bsongs?\b', r'\bwriting songs\b',
        r'\bfreedom is like my biggest\b', r'\bpunk-ass\b',
        r'\bi grew up\b', r'\bcame from colorado\b', r'\bco so\b',
        r'\bmy (?:dad|brothers?|fashion|lyrics)\b',
        r'\btour(?:ing)?\b', r'\bcontracts?\b',
        r'\balias(?:es)?\b', r'\bmask\b', r'\bbeast\b',
        r'\bbutterfly\b', r'\bnative american\b', r'\bsunshine\b',
        r'\baudio engineering\b', r'\breckless\b',
        r'\bi.?ve been writing\b', r'\bwhen i (?:was|got|had|went|started|left)\b',
        r'\bas a (?:rapper|kid|skater)\b',
    ]:
        if re.search(pat, tlow):
            s += 5
    if re.search(r'\bi (?:was|had|grew|got|did|started|think|feel|have|went|lived|always|work|don.?t|would say|am|learned|ended|wrote|wanted)\b', tlow) and len(text.split()) > 40:
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
    sg = score_shaden(text)

    if ms < 180000 and re.search(r'junkyard love|welcome to the junk|yo listen|you.?re on the junkyard|super glad to have you|episode (?:009|9)|shaden|hvshi|hoshi listen', text.lower()):
        sp = 'Jacob'
    elif sj > sg + 1:
        sp = 'Jacob'
    elif sg > sj + 1:
        sp = 'Shaden'
    else:
        if sj > sg:
            sp = 'Jacob'
        elif sg > sj:
            sp = 'Shaden'
        else:
            if len(text.split()) <= 8:
                sp = 'Shaden' if prev == 'Jacob' else 'Jacob'
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
    if ms < 180000 and re.search(r'junkyard love|welcome to the junk|yo listen|you.?re on the junkyard|super glad to have you|episode (?:009|9)|shaden|hvshi', low):
        sp = 'Jacob'
    if re.search(r'\bi see clients\b|\bmy clients?\b|\b3500 calories\b|\b3,500 calories\b|\bmuscle mass\b|\bposture would change\b', low):
        if re.search(r'\bi (?:had|was|went|got|did|ended|started|worked|see|train)|my (?:clients?|posture)|when i\b', low):
            sp = 'Shaden'
    if re.search(r'drink (?:some )?(?:dang )?water|see you (?:guys )?next|peace out|get present|listeners (?:drink|please|get|if you)|hello and welcome to the junkyard|junkyard love podcast out|be brave everybody|you are not your thoughts|welcome to the junkyard love|you.?re awesome listener|this is jacob rhines|end of junkyard love', low):
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
    r'(.*(?:yo listen|you.?re on the Junkyard Love Podcast|super glad to have you).*)\s+(.*(I grew up|came from|punk-ass skater|writing songs).*)',
    'Jacob', 'Shaden', 'split Jacob open / Shaden start')

rescored = []
for i, (ms, sp, tx) in enumerate(turns):
    low = tx.lower()
    sj = score_jacob(tx)
    sg = score_shaden(tx)
    if ms < 180000 and re.search(r'junkyard love|welcome to the junk|yo listen|you.?re on the junkyard|super glad to have you|episode (?:009|9)', low):
        sp = 'Jacob'
    elif re.search(r'junkyard love podcast|drink some|get present|hello and welcome|listeners please|listeners if you|peace out|be brave everybody|you.?re awesome listener|this is jacob rhines', low):
        sp = 'Jacob'
    elif sj > sg + 2:
        sp = 'Jacob'
    elif sg > sj + 2:
        sp = 'Shaden'
    if ms >= min(DURATION_S, YT_DURATION_S) * 1000 - 150000 and re.search(r'peace out|junkyard|drink|listeners|get present|be brave|awesome listener|jacob rhines', low):
        if re.search(r'listeners|drink|get present|peace out|junkyard|be brave|junkyard love podcast|awesome listener|jacob rhines', low):
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
    ('freedom is like my biggest', 'Shaden'),
    ('writing songs', 'Shaden'),
    ('pro skater', 'Shaden'),
    ('punk-ass skater', 'Shaden'),
    ('contracts', None),
    ('tour', None),
    ('aliases', None),
    ('mask', None),
    ('Native American', None),
    ('sunshine', None),
    ('fashion', 'Shaden'),
    ('butterfly', None),
    ('dark place', None),
    ('management', 'Jacob'),
    ('rapper', 'Jacob'),
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
            label = "Opening — Junkyard Love / Shaden 'Hvshi' Nugent"
        aid = anchor_id_s(s)
        if aid in used:
            continue
        used.add(aid)
        chapters.append((s, label))
else:
    chapter_needles = [
        (0, 'junkyard love podcast', "Opening — Junkyard Love / Shaden 'Hvshi' Nugent"),
        (70, 'rapper', 'Rapper intro / Colorado skater kid origin'),
        (100, 'writing songs', 'Writing songs since age 12'),
        (360, 'brothers', 'Brothers / family'),
        (600, 'skate park', 'Skate park / headphones / weaving'),
        (680, 'pain', 'Recklessness & avoiding pain'),
        (820, 'tour', 'Touring, contracts, music work'),
        (1040, 'healing', 'Healing out loud / brand-new setup'),
        (1150, 'audio', 'Audio engineering / touring job'),
        (1200, 'mindset', 'Mindset / the beast'),
        (1750, 'aliases', 'Aliases & public masks'),
        (2320, 'Native American', "Hvshi — Native American 'sunshine' meaning"),
        (2520, 'fashion', 'Fashionable male in a small town'),
        (3050, 'remixes', 'Remixes / creative process'),
        (3370, 'butterfly', 'Butterfly stage / upcoming chapter'),
        (3420, 'messages', 'Messages for listeners'),
        (3630, 'dark place', 'Dark place / closing'),
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
            if best and best[0] < 400:
                s = best[1]
        aid = anchor_id_s(s)
        if aid in used:
            continue
        used.add(aid)
        chapters.append((s, label))
    chapters.sort(key=lambda x: x[0])

keywords = (
    "Shaden Hvshi Nugent, Episode 009 with Shaden 'Hvshi' Nugent, Junkyard Love Podcast episode 0009, JYLP 0009, "
    'rapper, hip-hop, skater, Colorado, songwriting, touring, contracts, fame, healing, the beast, '
    'fashion, aliases, masks, Native American sunshine meaning, butterfly, EP, short film, storytelling, '
    'audio engineering, Jacob Rhines'
)
hashtags = (
    "#ShadenNugent #Hvshi #JYLP0009 #JunkyardLove #HipHop #Rapper #Songwriting "
    "#Touring #Healing #Fashion #Aliases #Storytelling #JYLP #BeBrave"
)
guest_bio = (
    "Shaden 'Hvshi' Nugent is a creator, rapper, and storyteller who joins Junkyard Love episode 0009 "
    "to unpack success, fame, contracts, touring, turmoil, and reset. He traces the boy behind the artistic "
    "layers — Colorado skater kid turned songwriter — and talks healing from letting the beast protect him "
    "from pain, being a fashionable male in a small town, the music writing process, upcoming EP and short film, "
    "alias masks, and the butterfly of this life stage. Inventory has_quotes=no / has_timestamps=no / "
    "has_hashtags=no / has_guest_links=no. Guest slug shaden-hvshi-nugent NEW. No guest contact/email."
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
    "Speaker map: pause-gap segmentation + sticky Jacob/Shaden content scoring (named speaker labels not present in captions; auto diarization imperfect); host bumper/outro forced to Jacob where clear\n"
    "Cleanup: light dedupe of consecutive duplicate words; merged consecutive same-speaker fragments; HTML entities/nbsp unescaped; capitalized turn starts after merge; light caption spacing tidy; light ASR name tidy (Shaden/Hvshi/Hoshi ASR tidy; Junkyard Love; Jacob Rhines; Instagram; Facebook; Twitter; YouTube; Big Mac; loserthink); bumper/outro forced to Jacob where clear; YouTube swear blanks normalized to ****\n"
    "No sentence rewriting.\n"
    f"Guest name spelling: Shaden 'Hvshi' Nugent (YT/RSS titles / inventory); captions often ASR as Hoshi/Hashi/shading; slug {GUEST_SLUG} (NEW).\n"
    "Note: automatic diarization is imperfect; remaining short backchannels and some mid-turn blends may still be swapped in places.\n"
    f"Issue: YouTube automatic captions (en/en-orig) used; no official/manual track; no >> speaker flips. YT duration {YT_DURATION_S}s (~1:04:42) vs RSS/inventory {DURATION_S}s (~1:04:14) — ~28s delta, not substantial; transcript follows YT captions; archive meta uses RSS duration. No published chapter timestamps; no YT chapters. Title {TITLE_CONFLICT}. About YT~RSS identical body (YT footer stripped). Inventory has_quotes=no / has_timestamps=no / has_hashtags=no / has_guest_links=no. Archive picks fills timestamped quotes/chapters/keywords/hashtags/bio. Guest page: {GUEST_SLUG} (NEW).\n"
    f"Speaker balance: Jacob {balance.get('Jacob',0)} turns/{words_by.get('Jacob',0)} words; Shaden {balance.get('Shaden',0)} turns/{words_by.get('Shaden',0)} words.\n"
    f"Heuristic speaker fixes: {len(fixes)}; post-splits: {len(post_fixes)} ({'; '.join(post_fixes)})\n",
    encoding='utf-8',
)

(CONTENT / 'SOURCES.txt').write_text(
    "Description source: YouTube primary per archive rules; About spaced from RSS plain (identical to YT after footer strip). Soft mid-sentence newlines joined. No guest contact/email.\n"
    f"YouTube chars: {len(yt_desc.strip())}\n"
    f"RSS HTML chars: {len(rss_html.strip())}\n"
    f"Title source: YT=RSS exact match ({VIDEO_ID}). H1/slug use Episode 009 with Shaden 'Hvshi' Nugent. {TITLE_CONFLICT}.\n"
    f"Title: {TITLE}\n"
    f"RSS title: {RSS_TITLE}\n"
    "Chapters source: none published in episode notes (inventory has_timestamps=no); no YouTube chapter markers — Archive picks derived from transcript themes\n"
    "Guest links: none published (inventory has_guest_links=no)\n"
    f"Quotes: inventory has_quotes=no — no Quotes list block ({len(published_quotes)} list quotes)\n"
    "Hashtags: none published as a block (inventory has_hashtags=no)\n"
    "About: Jacob published description verbatim as spaced paras from RSS (YT~RSS); YT footer stripped\n"
    f"Guest name spelling: Shaden 'Hvshi' Nugent; guest slug {GUEST_SLUG} (NEW)\n"
    f"Duration: RSS itunes:duration {DURATION_S}s ({DURATION_HUMAN}); YT info.json duration {YT_DURATION_S}s — using RSS/inventory {DURATION_S}; YT~RSS within ~28s (not substantial)\n"
    "Publish date: RSS/inventory 2019-12-11 (YT upload_date 20191212 — next calendar day)\n"
    "Archive picks: added (timestamped transcript quotes, chapter-style timestamps from transcript, keywords/hashtags, short guest bio) — extracted from YT auto-caption transcript + published About; kept separate from Jacob published About/Chapters/Quotes.\n"
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
quotes_html = (
    '<p class="note">(none published — inventory has_quotes=no)</p>'
)
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

ld_keywords = keywords + ", Shaden 'Hvshi' Nugent, Jacob Rhines, Junkyard Love Podcast"
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
<p class="note">From YouTube automatic captions; light cleanup; speaker labels via imperfect auto diarization (Jacob/Shaden may be swapped in places).</p>
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
guest_meta_html = f'<a href="../../guests/{GUEST_SLUG}/index.html">{escape(GUEST)}</a>'
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

# Guest page NEW — shaden-hvshi-nugent
guest_dir = SITE / 'guests' / GUEST_SLUG
if guest_dir.exists():
    shutil.rmtree(guest_dir)
guest_dir.mkdir(parents=True)
bio_html = '\n'.join(para_to_html(p) for p in about_paras)
guest_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<base href="/junkyard-love-archive/">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(GUEST_DISPLAY)} — The Junkyard Love Podcast</title>
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

<h1>{escape(GUEST_DISPLAY)}</h1>
<p class="note">Appeared on The Junkyard Love Podcast (1 episode)</p>
<h2>Episodes</h2>
<ul class="list">
  <li><a href="../../episodes/{EP_SLUG}/index.html">{escape(TITLE)}</a><br><span class="note">{DATE} · Episode {EP_NUM}</span></li>
</ul>
<h2>From the episode notes</h2>
<p class="note">Copied from published episode descriptions (not a new biography).</p>
<h3>Episode {EP_NUM}</h3>
<div class="about">
{bio_html}
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
(guest_dir / 'index.html').write_text(guest_html, encoding='utf-8')

home_li = (
    f'  <li><a href="episodes/{EP_SLUG}/index.html">{escape(TITLE)}</a>'
    f'<br><span class="note">{DATE} · {escape(GUEST)} · {DURATION_HUMAN}</span></li>\n'
)
ep_li = (
    f'  <li><a href="episodes/{EP_SLUG}/index.html">{escape(TITLE)}</a>'
    f'<br><span class="note">Episode {EP_NUM} · {DATE} · {DURATION_HUMAN} · Guest: {escape(GUEST)}</span></li>\n'
)

# Insert AFTER 0010 (descending: 0010 then 0009)
marker_home = (
    '  <li><a href="episodes/0010-brian-dj-toasty-andrews-and-kelly-k3lls-st-onge/index.html">'
    "Episode 010 with Brian &#x27;Dj Toasty&#x27; Andrews and Kelly &#x27;K3lls&#x27; St. Onge</a>"
    "<br><span class=\"note\">2019-12-13 · Brian &#x27;Dj Toasty&#x27; Andrews and Kelly &#x27;K3lls&#x27; St. Onge · 1:46:43</span></li>\n"
)
marker_ep = (
    '  <li><a href="episodes/0010-brian-dj-toasty-andrews-and-kelly-k3lls-st-onge/index.html">'
    "Episode 010 with Brian &#x27;Dj Toasty&#x27; Andrews and Kelly &#x27;K3lls&#x27; St. Onge</a>"
    "<br><span class=\"note\">Episode 0010 · 2019-12-13 · 1:46:43 · Guests: Brian &#x27;Dj Toasty&#x27; Andrews &amp; Kelly &#x27;K3lls&#x27; St. Onge</span></li>\n"
)

home = (SITE / 'index.html').read_text(encoding='utf-8')
if EP_SLUG not in home:
    if marker_home not in home:
        raise SystemExit('home 0010 marker not found')
    home = home.replace(marker_home, marker_home + home_li)
    (SITE / 'index.html').write_text(home, encoding='utf-8')

ep_index = (SITE / 'episodes' / 'index.html').read_text(encoding='utf-8')
if EP_SLUG not in ep_index:
    if marker_ep not in ep_index:
        raise SystemExit('ep index 0010 marker not found')
    ep_index = ep_index.replace(marker_ep, marker_ep + ep_li)
    (SITE / 'episodes' / 'index.html').write_text(ep_index, encoding='utf-8')

# Guest NEW — insert alphabetically between sean-blackwell and shaye-camp-reeducation
guests_index = (SITE / 'guests' / 'index.html').read_text(encoding='utf-8')
if GUEST_SLUG not in guests_index:
    g_li = f'  <li><a href="guests/{GUEST_SLUG}/index.html">{escape(GUEST_DISPLAY)}</a></li>\n'
    g_marker = '  <li><a href="guests/sean-blackwell/index.html">Sean Blackwell</a></li>\n'
    if g_marker not in guests_index:
        raise SystemExit('guests index sean-blackwell marker not found')
    guests_index = guests_index.replace(g_marker, g_marker + g_li)
    (SITE / 'guests' / 'index.html').write_text(guests_index, encoding='utf-8')


sm = (SITE / 'sitemap.xml').read_text(encoding='utf-8')
if EP_SLUG not in sm:
    insert = (
        f'  <url><loc>{SITE_BASE}/episodes/{EP_SLUG}/</loc></url>\n'
        f'  <url><loc>{SITE_BASE}/episodes/{EP_SLUG}/episode.md</loc></url>\n'
    )
    m10 = f'  <url><loc>{SITE_BASE}/episodes/0010-brian-dj-toasty-andrews-and-kelly-k3lls-st-onge/episode.md</loc></url>\n'
    if m10 not in sm:
        raise SystemExit('sitemap 0010 marker not found')
    sm = sm.replace(m10, m10 + insert)
    (SITE / 'sitemap.xml').write_text(sm, encoding='utf-8')
# Guest NEW in sitemap (alpha near shaye)
if f'/guests/{GUEST_SLUG}/' not in sm:
    g_url = f'  <url><loc>{SITE_BASE}/guests/{GUEST_SLUG}/</loc></url>\n'
    g_mark = f'  <url><loc>{SITE_BASE}/guests/sean-blackwell/</loc></url>\n'
    if g_mark not in sm:
        # fallback after shaye block area — try inserting before shaye if sean marker elsewhere
        g_mark2 = f'  <url><loc>{SITE_BASE}/guests/shaye-camp-reeducation/</loc></url>\n'
        if g_mark2 not in sm:
            raise SystemExit('sitemap guest insert marker not found')
        sm = sm.replace(g_mark2, g_url + g_mark2)
    else:
        sm = sm.replace(g_mark, g_mark + g_url)
    (SITE / 'sitemap.xml').write_text(sm, encoding='utf-8')
elif EP_SLUG in sm:
    (SITE / 'sitemap.xml').write_text(sm, encoding='utf-8')


llms = (SITE / 'llms.txt').read_text(encoding='utf-8')
if EP_SLUG not in llms:
    ep_line = (
        f"- [0009 Shaden 'Hvshi' Nugent]"
        f'({SITE_BASE}/episodes/{EP_SLUG}/) — {DATE}\n'
    )
    m10_line = (
        f"- [0010 Brian 'Dj Toasty' Andrews & Kelly 'K3lls' St. Onge]"
        f'({SITE_BASE}/episodes/0010-brian-dj-toasty-andrews-and-kelly-k3lls-st-onge/) — 2019-12-13\n'
    )
    if m10_line not in llms:
        raise SystemExit('llms 0010 ep line not found')
    llms = llms.replace(m10_line, m10_line + ep_line)
    md_line = f'- [{SITE_BASE}/episodes/{EP_SLUG}/episode.md]({SITE_BASE}/episodes/{EP_SLUG}/episode.md)\n'
    m10_md = (
        f'- [{SITE_BASE}/episodes/0010-brian-dj-toasty-andrews-and-kelly-k3lls-st-onge/episode.md]'
        f'({SITE_BASE}/episodes/0010-brian-dj-toasty-andrews-and-kelly-k3lls-st-onge/episode.md)\n'
    )
    if m10_md in llms and md_line not in llms:
        llms = llms.replace(m10_md, m10_md + md_line)
    g_line = f"- [Shaden 'Hvshi' Nugent]({SITE_BASE}/guests/{GUEST_SLUG}/)\n"
    if f'/guests/{GUEST_SLUG}/' not in llms:
        g_mark = f'- [Sean Blackwell]({SITE_BASE}/guests/sean-blackwell/)\n'
        if g_mark not in llms:
            raise SystemExit('llms guest sean marker not found')
        llms = llms.replace(g_mark, g_mark + g_line)
    (SITE / 'llms.txt').write_text(llms, encoding='utf-8')


readme = (ROOT / 'README.md').read_text(encoding='utf-8')
if EP_SLUG not in readme and '**0009**' not in readme:
    marker = "- **0010** Brian 'Dj Toasty' Andrews & Kelly 'K3lls' St. Onge — `site/episodes/0010-brian-dj-toasty-andrews-and-kelly-k3lls-st-onge/`\n"
    add = f"- **0009** Shaden 'Hvshi' Nugent — `site/episodes/{EP_SLUG}/`\n"
    if marker not in readme:
        raise SystemExit('README 0010 marker not found')
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
        shutil.copy(ROOT / 'build_0009.py', DEPLOY / '_sources' / 'build_0009.py')
    print('deploy synced (no commit/push)')

print('DONE')
print('slug', EP_SLUG)
print('guest', GUEST_SLUG, 'NEW')
gcheck = (SITE / 'guests' / GUEST_SLUG / 'index.html').read_text(encoding='utf-8')
print('guest has 0009', EP_SLUG in gcheck)
print('guest note episodes:', re.search(r'\((\d+) episodes?\)', gcheck).group(1) if re.search(r'\((\d+) episodes?\)', gcheck) else '?')
print('H1', TITLE)
print('title_conflict', TITLE_CONFLICT)
print('turns', len(turns), 'words', word_count)
print('about paras', len(about_paras))
print('published quotes', len(published_quotes))
print('quotes_ap', len(quotes_ap), 'archive_chapters', len(chapters))
print('balance', dict(balance), dict(words_by))
print('About paras:')
for i, para in enumerate(about_paras):
    print(f'  [{i}] {para[:200].replace(chr(10), " / ")}')
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
for s, sp, q in quotes_ap[:12]:
    print(f'  [{fmt_ts_from_s(s)}] {sp}: {q[:80]}')
print('title_conflict', repr(meta['title_conflict']) or '(empty/YT=RSS)')
print('H1', TITLE)
print('deploy synced', DEPLOY.exists())
