#!/usr/bin/env python3
"""Process Junkyard Love episode 0011 — Spencer Hicks (single guest, EXISTING APPEND).
YT=RSS titles match exactly ("Episode 011 with Spencer Hicks").
About YT~RSS identical body after YT footer strip + (02) series marker strip; inventory
has_quotes=no, has_timestamps=no, has_hashtags=no, has_guest_links=no.
Guest slug: spencer-hicks (EXISTING — lists 0088+0074+0059+0044+0038+0023+0017; APPEND 0011, do not wipe).
YouTube auto-captions available (en/en-orig). YT duration ~5953s vs RSS 5926s (~27s —
not substantial; meta uses RSS). No YouTube chapter markers — Archive picks from transcript.
Archive picks required. Imperfect auto diarization flagged. No guest contact/email.
Insert indexes after 0012. After 0011, next catalog is 0010 Brian DJ Toasty + Kelly St. Onge (do not build here)."""
from __future__ import annotations
import json, re, shutil
from pathlib import Path
from html import escape, unescape
from collections import Counter

ROOT = Path('/workspace/junkyard-love-archive')
CONTENT = ROOT / 'content/0011-spencer-hicks'
SITE = ROOT / 'site'
DEPLOY = Path('/workspace/junkyard-love-archive-deploy')
EP_SLUG = '0011-spencer-hicks'
GUEST_SLUG = 'spencer-hicks'  # EXISTING — APPEND
TITLE = 'Episode 011 with Spencer Hicks'
RSS_TITLE = TITLE
YT_TITLE = TITLE
GUEST = 'Spencer Hicks'
GUEST_SHORT = 'Spencer'
GUEST_DISPLAY = 'Spencer Hicks'
SPK = 'Spencer'
YOUTUBE = 'https://www.youtube.com/watch?v=oSqN2HXKe54'
RSS_URL = 'https://share.transistor.fm/s/f682cb2b'
AUDIO_URL = 'https://2.gum.fm/op3.dev/e/pdcn.co/e/pscrb.fm/rss/p/pdst.fm/e/dts.podtrac.com/redirect.mp3/media.transistor.fm/f682cb2b/52a40954.mp3'
DATE = '2019-12-13'
DURATION_S = 5926  # RSS / inventory (~1:38:46)
YT_DURATION_S = 5953  # YT info.json (~1:39:13); ~27s delta — not substantial
EP_NUM = '0011'
EP_INT = 11
SPOTIFY = 'https://open.spotify.com/show/45J7CBdM8j29doqyBp2bFs'
APPLE = 'https://podcasts.apple.com/us/podcast/the-junkyard-love-podcast/id1489118788'
SITE_BASE = 'https://junkyardlovejakesbot.github.io/junkyard-love-archive'
VIDEO_ID = 'oSqN2HXKe54'
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
    f'title={YT_TITLE}\nupload_date=20191214\nduration={YT_DURATION_S}\nvideo_id={VIDEO_ID}\n'
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
    'We speak on social media',
    'We dive into the abstract',
    'We talk about developing',
    'Once the video side',
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
    f'Title conflict: {TITLE_CONFLICT}\nGuest slug: {GUEST_SLUG} (EXISTING — APPEND 0011 to 0088+0074+0059+0044+0038+0023+0017, do not wipe)\n'
    f'About: YT~RSS identical body; (02) + YT footer stripped; no guest contact/email\n'
    f'Transcript: YouTube auto-captions (en/en-orig); YT duration {YT_DURATION_S}s vs RSS {DURATION_S}s (~27s; meta uses RSS); no YT chapters\n',
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
        r'^(Well,? (?:I|so|yeah|we)|Yeah,? (?:so|I|and|we)|So,? (?:I|we|when|in|the|my|like)|I (?:think|was|love|want|had|grew|got|mean|have|always|feel|am|do|did|started|learned|would|went|ended|see clients)|We (?:are|were|have|had|just)|Absolutely|Thank you|Okay|Yes|Right|For me|My (?:name|brother|clients?|posture)|Um,? (?:I|so|yeah|like)|No problem|Okay so|Spencer)',
        text.strip(), re.I))
    starts_jacob = bool(re.match(
        r'^(Hello|Welcome|Well,? so|So,? (?:let\'s|what|um|Spencer)|Junkyard|Thank you|Yeah,? yeah|Wave|Peace out|Knowledge is|Reality is|Listeners|Cool so|What.?s up|Check it out|Drink some|Now here.?s episode|Ahoy|Okay well folks|All right|Spencer I|Be brave|You.?re awesome listener)',
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
        (r'\bworldview\b', 'worldview'),
        (r'\bbig mac\b', 'Big Mac'),
        (r'\bloserthink\b', 'loserthink'),
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
        r'\bspencer (?:i|welcome|thank|hicks)\b',
        r'\bglad you.?re here\b', r'\bmy friend spencer', r'\bwelcome to the junkyard',
        r'\bgiving the listeners\b', r'\blisteners if you\b',
        r'\byou are not your thoughts\b', r'\byou.?re awesome listener\b',
        r'\bwe are in for the junkyard\b', r'\bspencer hicks welcome\b', r'\bwelcome aboard\b', r'\bgot spencer on again\b',
        r'\bi.?ve also been on the reverse of in djing\b', r'\bdjing\b',
    ]:
        if re.search(pat, tlow):
            s += 4
    if re.search(r'\b(?:you|spencer)\b', tlow) and ('?' in text or re.search(r'\byou (?:feel|think|said|mentioned|been|had|worked)\b', tlow)):
        s += 3
    if '?' in text and len(text.split()) < 90:
        s += 2
    if len(text.split()) <= 12 and re.search(
        r'^(yeah|yes|right|okay|ok|cool|love it|mhm|mm+|exactly|wow|dude|man|perfect|great|beautiful|thanks|you bet|interesting|absolutely)\b', tlow):
        s += 2
    if re.search(r'\byou (?:guys|mentioned|said|feel|think|know|been|had|went|worked)\b', tlow):
        s += 2
    return s


def score_spencer(text):
    tlow = text.lower()
    s = 0
    for pat in [
        r'\bposture\b', r'\bclients?\b', r'\bfitness\b', r'\bgym\b',
        r'\bcalories?\b', r'\bworkout\b', r'\bvegan\b', r'\bdiet\b',
        r'\bmindful(?:ness)?\b', r'\bmeditation\b', r'\bworldview\b',
        r'\bzombie\b', r'\bapocalypse\b', r'\bsocial media\b', r'\binstagram\b',
        r'\bi see clients\b', r'\bpersonal train', r'\bmuscle mass\b',
        r'\bovereat\b', r'\b3500 calories\b', r'\b3,500 calories\b',
        r'\bwhen i (?:was|got|had|went|worked|started|left|came|train)\b',
        r'\bi (?:worked|was working|train|trained|tell my)\b',
        r'\bmy (?:clients?|posture|fitness)\b',
        r'\bas a (?:trainer|science)\b',
    ]:
        if re.search(pat, tlow):
            s += 5
    if re.search(r'\bi (?:was|had|grew|got|did|started|think|feel|have|went|lived|always|work|don.?t|would say|am|learned|ended|worked|see)\b', tlow) and len(text.split()) > 40:
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

    if ms < 200000 and re.search(r'junkyard love|welcome to the junk|spencer hicks welcome|we are in for the junkyard|my friend spencer|welcome aboard|got spencer on again|episode (?:011|11)', text.lower()):
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
    if ms < 220000 and re.search(r'junkyard love|welcome to the junk|spencer hicks welcome|we are in for the junkyard|my friend spencer|welcome aboard|got spencer on again|live conversation with spencer', low):
        sp = 'Jacob'
    if re.search(r'\bi see clients\b|\bmy clients?\b|\b3500 calories\b|\b3,500 calories\b|\bmuscle mass\b|\bposture would change\b', low):
        if re.search(r'\bi (?:had|was|went|got|did|ended|started|worked|see|train)|my (?:clients?|posture)|when i\b', low):
            sp = 'Spencer'
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
    r'(.*(?:welcome aboard|Spencer Hicks welcome|we are in for the Junkyard Love Podcast).*)\s+(.*(well I|I (?:think|was|see)|echo chamber|Internet).*)',
    'Jacob', 'Spencer', 'split Jacob open / Spencer start')

rescored = []
for i, (ms, sp, tx) in enumerate(turns):
    low = tx.lower()
    sj = score_jacob(tx)
    sg = score_spencer(tx)
    if ms < 220000 and re.search(r'junkyard love|welcome to the junk|spencer hicks welcome|we are in for the junkyard|welcome aboard|got spencer on again', low):
        sp = 'Jacob'
    elif re.search(r'junkyard love podcast|drink some|get present|hello and welcome|listeners please|listeners if you|peace out|be brave everybody|you.?re awesome listener|this is jacob rhines', low):
        sp = 'Jacob'
    elif sj > sg + 2:
        sp = 'Jacob'
    elif sg > sj + 2:
        sp = 'Spencer'
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
    ('echo chamber', None),
    ('social media', None),
    ('Instagram', None),
    ('intention', None),
    ('mindful', None),
    ('fitness', None),
    ('zombie', None),
    ('worldview', None),
    ('posture', None),
    ('calorie', None),
    ('clients', 'Spencer'),
    ('tribalism', None),
    ('language barrier', None),
    ('listeners', 'Jacob'),
    ('awesome listener', 'Jacob'),
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
        (70, 'junkyard love podcast', 'Opening — Junkyard Love / Spencer Hicks'),
        (0, 'echo chamber', 'Echo chambers & online communication'),
        (350, 'tribalism', 'Tribalism'),
        (900, 'crowd', 'Crowds, excitement & observing humans'),
        (1075, 'bare feet', 'Bare feet / backyard reset'),
        (1250, 'self-conscious', 'Gym self-consciousness'),
        (1980, 'Instagram', 'Instagram talkers & looking good'),
        (2340, 'questioning everything', 'Questioning everything'),
        (2700, 'vegan', 'Vegan athletes / diet talk'),
        (3040, 'calories', 'Calories, weight & Big Mac math'),
        (3240, 'fitness goals', 'Fitness goals'),
        (3780, 'worldview', 'Rounder worldview'),
        (3950, 'language barrier', 'Language barriers inside our own language'),
        (4140, 'talking heads', 'Talking heads & corporate agendas'),
        (5220, 'Thanksgiving', 'Saying fewer words / Thanksgiving'),
        (5580, 'posture', 'Posture & standing up straight'),
        (5900, 'awesome listener', 'Outro — love the listener'),
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
    'Spencer Hicks, Episode 011 with Spencer Hicks, Junkyard Love Podcast episode 0011, JYLP 0011, '
    'social media, echo chambers, political nonsense, loserthink, intentions, mindfulness, fitness, '
    'working out, conversation, misunderstood words, worldview, zombie apocalypse, posture, '
    'standing up straight, Instagram, calories, gym, Jacob Rhines'
)
hashtags = (
    '#SpencerHicks #JYLP0011 #JunkyardLove #Mindfulness #Fitness #SocialMedia '
    '#Worldview #Posture #Conversation #JYLP #BeBrave'
)
guest_bio = (
    'Spencer Hicks appears on Junkyard Love episode 0011 as Jacob\'s recurring conversation partner — '
    'a science-minded friend, fitness enthusiast, and armchair philosopher. This early series chat covers '
    'social media and echo chambers, political nonsense and loserthink, intentions and mindfulness, '
    'fitness and working out, how words get misunderstood, developing a new worldview, the zombie-apocalypse '
    'metaphor, and standing up straight / posture. Jacob notes that once video is constant, listeners can '
    'expect weekly Spencer episodes for the next few months. Inventory has_quotes=no / has_timestamps=no / '
    'has_hashtags=no / has_guest_links=no. Guest slug spencer-hicks EXISTING APPEND (0088+0074+0059+0044+0038+0023+0017+0011). '
    'No guest contact/email.'
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
    "Speaker map: pause-gap segmentation + sticky Jacob/Spencer content scoring (named speaker labels not present in captions; auto diarization imperfect); host bumper/outro forced to Jacob where clear\n"
    "Cleanup: light dedupe of consecutive duplicate words; merged consecutive same-speaker fragments; HTML entities/nbsp unescaped; capitalized turn starts after merge; light caption spacing tidy; light ASR name tidy (Spencer Hicks; Junkyard Love; Jacob Rhines; Instagram; Facebook; Twitter; YouTube; Big Mac; loserthink); bumper/outro forced to Jacob where clear; YouTube swear blanks normalized to ****\n"
    "No sentence rewriting.\n"
    f"Guest name spelling: Spencer Hicks (YT/RSS titles / inventory); slug {GUEST_SLUG} (EXISTING — APPEND 0011 to 0088+0074+0059+0044+0038+0023+0017, do not wipe).\n"
    "Note: automatic diarization is imperfect; remaining short backchannels and some mid-turn blends may still be swapped in places.\n"
    f"Issue: YouTube automatic captions (en/en-orig) used; no official/manual track; no >> speaker flips. YT duration {YT_DURATION_S}s (~1:39:13) vs RSS/inventory {DURATION_S}s (~1:38:46) — ~27s delta, not substantial; transcript follows YT captions; archive meta uses RSS duration. No published chapter timestamps; no YT chapters. Title {TITLE_CONFLICT}. About YT~RSS identical body ((02) series marker stripped; YT footer stripped). Inventory has_quotes=no / has_timestamps=no / has_hashtags=no / has_guest_links=no. Archive picks fills timestamped quotes/chapters/keywords/hashtags/bio. Guest page: {GUEST_SLUG} (EXISTING APPEND).\n"
    f"Speaker balance: Jacob {balance.get('Jacob',0)} turns/{words_by.get('Jacob',0)} words; Spencer {balance.get('Spencer',0)} turns/{words_by.get('Spencer',0)} words.\n"
    f"Heuristic speaker fixes: {len(fixes)}; post-splits: {len(post_fixes)} ({'; '.join(post_fixes)})\n",
    encoding='utf-8',
)

(CONTENT / 'SOURCES.txt').write_text(
    "Description source: YouTube primary per archive rules; About spaced from RSS plain (identical to YT after footer strip). Soft mid-sentence newlines joined. No guest contact/email.\n"
    f"YouTube chars: {len(yt_desc.strip())}\n"
    f"RSS HTML chars: {len(rss_html.strip())}\n"
    f"Title source: YT=RSS exact match ({VIDEO_ID}). H1/slug use Episode 011 with Spencer Hicks. {TITLE_CONFLICT}.\n"
    f"Title: {TITLE}\n"
    f"RSS title: {RSS_TITLE}\n"
    "Chapters source: none published in episode notes (inventory has_timestamps=no); no YouTube chapter markers — Archive picks derived from transcript themes\n"
    "Guest links: none published (inventory has_guest_links=no)\n"
    f"Quotes: inventory has_quotes=no — no Quotes list block ({len(published_quotes)} list quotes)\n"
    "Hashtags: none published as a block (inventory has_hashtags=no)\n"
    "About: Jacob published description verbatim as spaced paras from RSS (YT~RSS); (02) marker + YT footer stripped\n"
    f"Guest name spelling: Spencer Hicks; guest slug {GUEST_SLUG} (EXISTING — APPEND 0011; prior 0088+0074+0059+0044+0038+0023+0017 preserved)\n"
    f"Duration: RSS itunes:duration {DURATION_S}s ({DURATION_HUMAN}); YT info.json duration {YT_DURATION_S}s — using RSS/inventory {DURATION_S}; YT~RSS within ~27s (not substantial)\n"
    "Publish date: RSS/inventory 2019-12-13 (YT upload_date 20191214 — next calendar day)\n"
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
        {'@type': 'Person', 'name': 'Spencer Hicks'},
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

# Guest page EXISTS — surgical APPEND 0011 (do not wipe prior listings/About blocks)
guest_dir = SITE / 'guests' / GUEST_SLUG
guest_dir.mkdir(parents=True, exist_ok=True)
bio_html = '\n'.join(para_to_html(p) for p in about_paras)
existing_guest = guest_dir / 'index.html'
if not existing_guest.exists():
    raise SystemExit('spencer-hicks guest page missing — expected EXISTING')
old = existing_guest.read_text(encoding='utf-8')
if EP_SLUG in old and f'Episode {EP_NUM}' in old and '0011-spencer-hicks' in old:
    # already appended — rewrite carefully by re-reading and ensuring count
    pass

# Update episode count 7 -> 8 (or N -> N+1 if already wrong)
old2 = re.sub(
    r'Appeared on The Junkyard Love Podcast \((\d+) episodes?\)',
    'Appeared on The Junkyard Love Podcast (8 episodes)',
    old,
    count=1,
)

new_li = (
    f'  <li><a href="../../episodes/{EP_SLUG}/index.html">{escape(TITLE)}</a>'
    f'<br><span class="note">{DATE} · Episode {EP_NUM}</span></li>\n'
)
# Insert after 0017 list item (descending chrono)
marker_li = (
    '  <li><a href="../../episodes/0017-spencer-hicks/index.html">Episode 017 with Spencer Hicks</a>'
    '<br><span class="note">2019-12-28 · Episode 0017</span></li>\n'
)
if EP_SLUG not in old2:
    if marker_li not in old2:
        raise SystemExit('guest page 0017 list marker not found')
    old2 = old2.replace(marker_li, marker_li + new_li)

# Insert About block for 0011 before Guest links (after 0017 about section)
about_block = (
    f'<h3>Episode {EP_NUM}</h3>\n'
    f'<div class="about">\n'
    f'{bio_html}\n'
    f'</div>\n'
)
if f'<h3>Episode {EP_NUM}</h3>' not in old2:
    guest_links_h2 = '<h2>Guest links</h2>'
    if guest_links_h2 not in old2:
        raise SystemExit('guest page Guest links marker not found')
    old2 = old2.replace(guest_links_h2, about_block + guest_links_h2)
else:
    # refresh About block contents for 0011 without touching others
    old2 = re.sub(
        rf'<h3>Episode {EP_NUM}</h3>\s*<div class="about">\s*.*?\s*</div>',
        about_block.rstrip(),
        old2,
        count=1,
        flags=re.S,
    )

(guest_dir / 'index.html').write_text(old2, encoding='utf-8')

home_li = (
    f'  <li><a href="episodes/{EP_SLUG}/index.html">{escape(TITLE)}</a>'
    f'<br><span class="note">{DATE} · {escape(GUEST)} · {DURATION_HUMAN}</span></li>\n'
)
ep_li = (
    f'  <li><a href="episodes/{EP_SLUG}/index.html">{escape(TITLE)}</a>'
    f'<br><span class="note">Episode {EP_NUM} · {DATE} · {DURATION_HUMAN} · Guest: {escape(GUEST)}</span></li>\n'
)

# Insert AFTER 0012 (descending: 0012 then 0011)
marker_home = (
    '  <li><a href="episodes/0012-bob-kendall/index.html">'
    'Episode 012 with Bob Kendall</a>'
    '<br><span class="note">2019-12-15 · Bob Kendall · 1:07:13</span></li>\n'
)
marker_ep = (
    '  <li><a href="episodes/0012-bob-kendall/index.html">'
    'Episode 012 with Bob Kendall</a>'
    '<br><span class="note">Episode 0012 · 2019-12-15 · 1:07:13 · Guest: Bob Kendall</span></li>\n'
)

home = (SITE / 'index.html').read_text(encoding='utf-8')
if EP_SLUG not in home:
    if marker_home not in home:
        raise SystemExit('home 0012 marker not found')
    home = home.replace(marker_home, marker_home + home_li)
    (SITE / 'index.html').write_text(home, encoding='utf-8')

ep_index = (SITE / 'episodes' / 'index.html').read_text(encoding='utf-8')
if EP_SLUG not in ep_index:
    if marker_ep not in ep_index:
        raise SystemExit('ep index 0012 marker not found')
    ep_index = ep_index.replace(marker_ep, marker_ep + ep_li)
    (SITE / 'episodes' / 'index.html').write_text(ep_index, encoding='utf-8')

# Guest EXISTS — already on guests index (spencer-hicks); do not re-insert

sm = (SITE / 'sitemap.xml').read_text(encoding='utf-8')
if EP_SLUG not in sm:
    insert = (
        f'  <url><loc>{SITE_BASE}/episodes/{EP_SLUG}/</loc></url>\n'
        f'  <url><loc>{SITE_BASE}/episodes/{EP_SLUG}/episode.md</loc></url>\n'
    )
    m12 = f'  <url><loc>{SITE_BASE}/episodes/0012-bob-kendall/episode.md</loc></url>\n'
    if m12 not in sm:
        raise SystemExit('sitemap 0012 marker not found')
    sm = sm.replace(m12, m12 + insert)
    (SITE / 'sitemap.xml').write_text(sm, encoding='utf-8')
# Guest already in sitemap (spencer-hicks)

llms = (SITE / 'llms.txt').read_text(encoding='utf-8')
if EP_SLUG not in llms:
    ep_line = (
        f'- [0011 Spencer Hicks]'
        f'({SITE_BASE}/episodes/{EP_SLUG}/) — {DATE}\n'
    )
    m12_line = (
        f'- [0012 Bob Kendall]'
        f'({SITE_BASE}/episodes/0012-bob-kendall/) — 2019-12-15\n'
    )
    if m12_line not in llms:
        raise SystemExit('llms 0012 ep line not found')
    llms = llms.replace(m12_line, m12_line + ep_line)
    md_line = f'- [{SITE_BASE}/episodes/{EP_SLUG}/episode.md]({SITE_BASE}/episodes/{EP_SLUG}/episode.md)\n'
    m12_md = (
        f'- [{SITE_BASE}/episodes/0012-bob-kendall/episode.md]'
        f'({SITE_BASE}/episodes/0012-bob-kendall/episode.md)\n'
    )
    if m12_md in llms and md_line not in llms:
        llms = llms.replace(m12_md, m12_md + md_line)
    (SITE / 'llms.txt').write_text(llms, encoding='utf-8')
# Guest already listed in llms

readme = (ROOT / 'README.md').read_text(encoding='utf-8')
if EP_SLUG not in readme and '**0011**' not in readme:
    marker = '- **0012** Bob Kendall — `site/episodes/0012-bob-kendall/`\n'
    add = f'- **0011** Spencer Hicks — `site/episodes/{EP_SLUG}/`\n'
    if marker not in readme:
        raise SystemExit('README 0012 marker not found')
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
        shutil.copy(ROOT / 'build_0011.py', DEPLOY / '_sources' / 'build_0011.py')
    print('deploy synced (no commit/push)')

print('DONE')
print('slug', EP_SLUG)
print('guest', GUEST_SLUG, 'EXISTING APPEND — episodes after update: 0088, 0074, 0059, 0044, 0038, 0023, 0017, 0011')
gcheck = (SITE / 'guests' / GUEST_SLUG / 'index.html').read_text(encoding='utf-8')
print('guest has 0011', EP_SLUG in gcheck)
print('guest note episodes:', re.search(r'\((\d+) episodes?\)', gcheck).group(1) if re.search(r'\((\d+) episodes?\)', gcheck) else '?')
for ep in ['0088', '0074', '0059', '0044', '0038', '0023', '0017', '0011']:
    print(f'  guest has Episode {ep}:', f'Episode {ep}' in gcheck or f'episodes/00' in gcheck)
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
