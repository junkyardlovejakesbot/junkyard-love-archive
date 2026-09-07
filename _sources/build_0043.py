#!/usr/bin/env python3
"""Process Junkyard Love episode 0043 — Joseph Crumb (single guest, NEW).
YT≠RSS title (prefer YouTube H1). Inventory has_quotes=yes, has_timestamps=no,
has_guest_links=no, has_hashtags=no.
Guest slug: joseph-crumb (NEW; RSS Stand-Up Comedian Joseph Crumb — display Joseph Crumb).
Archive picks required. Imperfect auto diarization flagged.
No formal bumper — conversation opens on mustache / cancel-culture banter."""
from __future__ import annotations
import json, re, shutil
from pathlib import Path
from html import escape, unescape
from collections import Counter

ROOT = Path('/workspace/junkyard-love-archive')
CONTENT = ROOT / 'content/0043-joseph-crumb-redefining-your-life-and-wait-why-are-you-taking-me-seriously'
SITE = ROOT / 'site'
DEPLOY = Path('/workspace/junkyard-love-archive-deploy')
EP_SLUG = '0043-joseph-crumb-redefining-your-life-and-wait-why-are-you-taking-me-seriously'
GUEST_SLUG = 'joseph-crumb'
TITLE = 'Episode 043 with Joseph Crumb - Redefining your life and - wait why are you taking me seriously?'
RSS_TITLE = 'Episode 043 with Stand-Up Comedian Joseph Crumb - Redefining your life and - wait why are you taking me seriously?'
GUEST = 'Joseph Crumb'
GUEST_SHORT = 'Joseph'
YOUTUBE = 'https://www.youtube.com/watch?v=kbDzFZrle9c'
RSS_URL = 'https://share.transistor.fm/s/d4cdff47'
AUDIO_URL = 'https://2.gum.fm/op3.dev/e/pdcn.co/e/pscrb.fm/rss/p/pdst.fm/e/dts.podtrac.com/redirect.mp3/media.transistor.fm/d4cdff47/582e1207.mp3'
DATE = '2020-05-29'
DURATION_S = 6241  # RSS / inventory
YT_DURATION_S = 6183
EP_NUM = '0043'
EP_INT = 43
SPOTIFY = 'https://open.spotify.com/show/45J7CBdM8j29doqyBp2bFs'
APPLE = 'https://podcasts.apple.com/us/podcast/the-junkyard-love-podcast/id1489118788'
SITE_BASE = 'https://junkyardlovejakesbot.github.io/junkyard-love-archive'
VIDEO_ID = 'kbDzFZrle9c'

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
(CONTENT / 'source-youtube-title.txt').write_text(TITLE + '\n', encoding='utf-8')
(CONTENT / 'source-youtube-raw.txt').write_text(yt_raw if yt_raw.endswith('\n') else yt_raw + '\n', encoding='utf-8')
(CONTENT / 'yt-meta.txt').write_text(
    f'title={TITLE}\nupload_date=20200530\nduration={YT_DURATION_S}\nvideo_id={VIDEO_ID}\n',
    encoding='utf-8',
)

# ---------- ABOUT from YouTube (primary; ~itunes:summary) ----------
yt_body = yt_desc
for marker in ['\nThe Junkyard Love Podcast', '\n\u2605 Episode details', '\n\u2605 Additional episodes']:
    idx = yt_body.find(marker)
    if idx >= 0:
        yt_body = yt_body[:idx]
yt_body = yt_body.strip()

# Strip guest contact / Instagram / Twitter CTA (no guest contact/email on archive)
yt_body = re.sub(
    r'\s*Checkout Comedian Joseph Crumb on instagram\s*@\s*crumb_guzzler.*$',
    '',
    yt_body,
    flags=re.I | re.S,
).strip()
# Also strip leftover recorded/quotes blocks if contact strip missed them
yt_body = re.sub(r'\s*\(Recorded on May 17th\)\s*', '\n', yt_body, flags=re.I).strip()
yt_body = re.sub(
    r'\s*-?\s*Couple quotes from the chat\s*-?\s*.*$',
    '',
    yt_body,
    flags=re.I | re.S,
).strip()
# Safety: strip any remaining @ crumb / twitter contact fragments
yt_body = re.sub(r'\s*(?:instagram|twitter)\s*@\s*crumb[^\n]*', '', yt_body, flags=re.I).strip()

# Published quotes from YT/RSS "Couple quotes from the chat" block (inventory has_quotes=yes)
published_quotes = []
for src in (yt_desc, rss_plain):
    block = src
    m = re.search(r'Couple quotes from the chat\s*-?\s*(.*)', src, re.I | re.S)
    if m:
        block = m.group(1)
    for qm in re.findall(r'[“"]([^”"]+)[”"]', block):
        q = qm.strip()
        # skip incidental short mid-sentence quotes like "available" / band name alone
        if q and q not in published_quotes and len(q) > 20:
            published_quotes.append(q)

about_paras = [x.strip() for x in re.split(r'\n\s*\n', yt_body) if x.strip()]
expanded = []
for block in about_paras:
    parts = [ln.strip() for ln in block.split('\n') if ln.strip()]
    if len(parts) > 1 and all(len(pt) > 40 for pt in parts):
        expanded.extend(parts)
    else:
        expanded.append(block)
about_paras = expanded
# Soft-split the single long About into readable paras at sentence boundaries (verbatim text)
if len(about_paras) == 1 and len(about_paras[0]) > 500:
    text = about_paras[0]
    soft_breaks = [
        'Throughout the episode',
        'We vibe about the flowing tides',
        'He shares some background',
        'We talk about things like seeking validation',
        'Joe talks about his band',
        'He tells me about Open Mic',
        'We talk about our insecurities',
        'Though a lifetime of work',
        'This episode is riddled',
    ]
    chunks = []
    remaining = text
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
    about_paras = [ln.strip() for ln in yt_body.split('\n') if ln.strip()] or [yt_body]

(CONTENT / 'source-description.raw.txt').write_text(yt_body + '\n', encoding='utf-8')

guest_links = []

about_md = '\n\n'.join(about_paras) + '\n'
quotes_md_lines = [f'- "{q}"' for q in published_quotes] if published_quotes else ['(none published in episode notes)']
(CONTENT / 'source-about.md').write_text(about_md, encoding='utf-8')
(CONTENT / 'source-quotes.md').write_text('\n'.join(quotes_md_lines) + '\n', encoding='utf-8')
(CONTENT / 'source-timestamps.md').write_text('(none published in episode notes)\n', encoding='utf-8')
(CONTENT / 'source-hashtags.txt').write_text('(none published in episode notes)\n', encoding='utf-8')
(CONTENT / 'source-links.md').write_text('(none published in episode notes)\n', encoding='utf-8')
(CONTENT / 'source-description.md').write_text(
    about_md + '\n## Quotes\n\n' + '\n'.join(quotes_md_lines) + '\n\n## Guest links\n\n(none published in episode notes)\n',
    encoding='utf-8',
)
(CONTENT / 'guest-share-draft.txt').write_text(
    f'Episode {EP_NUM}: {TITLE}\nGuest: {GUEST}\nDate: {DATE}\nYouTube: {YOUTUBE}\nRSS: {RSS_URL}\n',
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
    if low in ('foreign', 'you') and e.get('tStartMs', 0) > DURATION_S * 1000 - 25000:
        continue
    t0 = e.get('tStartMs', 0)
    if t0 >= DURATION_S * 1000 + 8000:
        continue
    text = re.sub(r'\[\s*__\s*\]', '****', text)
    text = text.replace('\u00a0', ' ').replace('[\u00a0__\u00a0]', '****').replace('[__]', '****')
    text = re.sub(r'\[\s*[_\u00a0]+\s*\]', '****', text)
    text = text.replace('[\xa0__\xa0]', '****').replace('[ __ ]', '****')
    text = re.sub(r'\[\s*(?:__|\xa0__\xa0)\s*\]', '****', text)
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
        r'^(Well,? (?:I|so|yeah|we)|Yeah,? (?:so|I|and|we|dude|man)|So,? (?:I|we|when|in|the|my)|I (?:think|was|love|want|had|grew|got|mean|have|always|feel|work|don.?t|ran|run|can.?t)|We (?:are|were|have|had|just|all|been)|Absolutely|Thank you|Okay|Yes|Right|For me|Um,? (?:I|so|yeah)|Man |Dude |For sure|How does my moustache|I can.?t grow|Stay In Prison|Open [Mm]ic)',
        text.strip(), re.I))
    starts_jacob = bool(re.match(
        r'^(Hello|Welcome|Well,? so|So,? (?:let\'s|what|um|all right|bro)|Junkyard|Thank you|Yeah,? yeah|Wave|Peace out|Knowledge is|Reality is|Listeners|Cool so|What.?s up|Check it out|Drink some|Folks if|All right (?:bro|man)|My friends|Joseph|Joe |Tell listeners|Alright let.?s roll|As a DJ)',
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
        (r'\bjoseph crumb\b', 'Joseph Crumb'),
        (r'\bjoseph chrome\b', 'Joseph Crumb'),
        (r'\bjoseph\b', 'Joseph'),
        (r'\bcrumb guzzler\b', 'crumb_guzzler'),
        (r'\bcrum guzzler\b', 'crumb_guzzler'),
        (r'\bstay in prison\b', 'Stay In Prison'),
        (r'\bjoe rogan\b', 'Joe Rogan'),
        (r'\bandrew schultz\b', 'Andrew Schultz'),
        (r'\bcharlemagne\b', 'Charlemagne'),
        (r'\bjim carrey\b', 'Jim Carrey'),
        (r'\bjason momoa\b', 'Jason Momoa'),
        (r'\bmy chemical romance\b', 'My Chemical Romance'),
        (r'\bmichael locke\b', 'Michael Locke'),
        (r'\btik tok\b', 'TikTok'),
        (r'\btic toc\b', 'TikTok'),
        (r'\bmyspace\b', 'MySpace'),
        (r'\bpsilocybin\b', 'psilocybin'),
        (r'\bdmt\b', 'DMT'),
        (r'\bdimethyltryptamine\b', 'dimethyltryptamine'),
        (r'\bjake rynes\b', 'Jake Rhines'),
        (r'\bjacob rhines\b', 'Jacob Rhines'),
        (r'\bjunkyard love podcast\b', 'Junkyard Love Podcast'),
        (r'\bjunkyard love\b', 'Junkyard Love'),
        (r'\byoutube\b', 'YouTube'),
        (r'\bspotify\b', 'Spotify'),
        (r'\binstagram\b', 'Instagram'),
        (r'\btwitter\b', 'Twitter'),
        (r'\bcovid\b', 'COVID'),
        (r'\bfomo\b', 'FOMO'),
    ]
    for pat, rep in reps:
        text = re.sub(pat, rep, text, flags=re.I)
    return text


def score_jacob(text):
    tlow = text.lower()
    s = 0
    for pat in [
        r'\bjunkyard\b', r'\bwelcome to the (?:junkyard )?podcast\b',
        r'\bdrink (?:some |dat |tons of )?water\b', r'\blove yourself\b', r'\bpeace out\b',
        r'\btake care of yourself\b', r'\blisteners?\b',
        r'\bjacob from the internet\b', r'\bjake rhines\b',
        r'\bget present\b', r'\bknowledge is power\b',
        r'\bfolks if you enjoyed\b', r'\bsee you next\b',
        r'\bmy podcast\b', r'\ball right bro\b', r'\ball right man\b',
        r'\bmy friends i hope you enjoyed\b',
        r'\bi appreciate you coming\b', r'\bgive him all your\b',
        r'\bas a dj\b', r'\bpsychedelic therapy\b',
        r'\bi study a lot of this\b', r'\bbe on the lookout for stay in prison\b',
        r'\byou\'ll be seeing some more joseph\b',
    ]:
        if re.search(pat, tlow):
            s += 4
    if re.search(r'\b(?:you)\b', tlow) and ('?' in text or re.search(r'\byou (?:feel|think|said|mentioned|been)\b', tlow)):
        s += 3
    if '?' in text and len(text.split()) < 90:
        s += 2
    if len(text.split()) <= 12 and re.search(
        r'^(yeah|yes|right|okay|ok|cool|love it|mhm|mm+|exactly|wow|dude|man|perfect|great|beautiful|thanks|you bet|interesting|excellent)\b', tlow):
        s += 2
    if re.search(r'\byou (?:guys|mentioned|said|feel|think|know|been)\b', tlow):
        s += 2
    return s


def score_joseph(text):
    tlow = text.lower()
    s = 0
    for pat in [
        r'\bmoustache\b', r'\bmustache\b', r'\bi can.?t grow a\b',
        r'\bstay in prison\b', r'\bopen mic\b', r'\bcrumb_guzzler\b', r'\bcrumb guzzler\b',
        r'\bjester\b', r'\bstand-?up comedian\b', r'\bi.?m a comedian\b',
        r'\bavatar telling you\b', r'\btake away.?jk\b', r'\bfomo\b',
        r'\bpsilocybin\b', r'\bdmt\b', r'\bdimethyltryptamine\b',
        r'\bmeth heroin\b', r'\beighth grade\b', r'\b8th grade\b',
        r'\bchameleon\b', r'\bcancel(?:led|ed)? culture\b',
        r'\bhow does my moustache\b', r'\bi look like i.?m 15\b',
        r'\bcomedic genius\b', r'\bmy jokes don.?t get treated\b',
        r'\bbox spring\b', r'\bdrinking mouthwash\b',
        r'\bi obtained a certain level\b', r'\bmy social media is\b',
    ]:
        if re.search(pat, tlow):
            s += 5
    if re.search(r'\bi (?:was|had|grew|got|did|started|think|feel|have|went|lived|always|work|don.?t|ran|run|can.?t)\b', tlow) and len(text.split()) > 40:
        s += 1
    return s


turns = []
prev = 'Joseph'  # episode opens on guest mustache bit (no formal bumper)
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
    sg = score_joseph(text)

    if sj > sg + 1:
        sp = 'Jacob'
    elif sg > sj + 1:
        sp = 'Joseph'
    else:
        if sj > sg:
            sp = 'Jacob'
        elif sg > sj:
            sp = 'Joseph'
        else:
            if len(text.split()) <= 8:
                sp = 'Joseph' if prev == 'Jacob' else 'Jacob'
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
    if re.search(r'how does my moustache|i can.?t grow a|stay in prison|open mic|crumb_guzzler|jester|avatar telling you|take away.?jk|psilocybin|dimethyltryptamine|meth heroin|eighth grade|comedic genius|box spring|drinking mouthwash|i obtained a certain level', low):
        sp = 'Joseph'
    if re.search(r'drink (?:some |dat |tons of )?water|see you (?:guys )?next|peace out|get present|listeners|hello and welcome to the junkyard|knowledge is power|folks if you enjoyed|my friends i hope you enjoyed|i appreciate you coming|give him all your|as a dj|be on the lookout for stay in prison|you.?ll be seeing some more joseph', low):
        if re.search(r'peace out|my friends i hope|folks if you|hello and welcome|i appreciate you coming|give him all your|be on the lookout|you.?ll be seeing some more joseph|listener drink|drink some', low) or ms >= DURATION_S * 1000 - 90000:
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
    r'(.*(?:i appreciate you coming on here|appreciate talking to me))\s+(.*(?:give him all your|instagram|crumb).*)',
    'Jacob', 'Jacob', 'noop-keep jacob close promo')
split_on(
    r'(.*(?:stay in prison|punk rock bar in town))\s+(.*(?:listen(?:er|ers)? drink|drink some).*)',
    'Jacob', 'Jacob', 'noop-keep jacob outro water')
split_on(
    r'(.*(?:how does my moustache look))\s+(.*(?:it.?s pretty good|it.?s solid).*)',
    'Joseph', 'Jacob', 'split Joseph mustache / Jacob reply')

rescored = []
for i, (ms, sp, tx) in enumerate(turns):
    low = tx.lower()
    sj = score_jacob(tx)
    sg = score_joseph(tx)
    if re.search(r'junkyard love podcast|get present|hello and welcome|knowledge is power|folks if you enjoyed|see you next|my friends i hope you enjoyed|peace out|i appreciate you coming|give him all your|be on the lookout for stay in prison', low):
        sp = 'Jacob'
    elif re.search(r'how does my moustache|i can.?t grow a|stay in prison our|open mic|avatar telling you|psilocybin|dimethyltryptamine|meth heroin|eighth grade|comedic genius|box spring|drinking mouthwash', low):
        sp = 'Joseph'
    elif sj > sg + 2:
        sp = 'Jacob'
    elif sg > sj + 2:
        sp = 'Joseph'
    if ms >= DURATION_S * 1000 - 90000 and re.search(r'folks if|please share|follow like subscribe|see you next|junkyard|drink some water|listeners|get present|my friends i hope|peace out|five star|give him all your|be on the lookout', low):
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
    ('moustache', 'Joseph'),
    ('mustache', 'Joseph'),
    ('cancel culture', None),
    ('jk', 'Joseph'),
    ('jester', None),
    ('FOMO', None),
    ('avatar', 'Joseph'),
    ('Stay In Prison', 'Joseph'),
    ('open mic', 'Joseph'),
    ('psilocybin', 'Joseph'),
    ('DMT', None),
    ('comedic genius', 'Joseph'),
    ('drink some', 'Jacob'),
    ('crumb_guzzler', None),
    ('eighth grade', None),
    ('validation', None),
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

chapter_needles = [
    (10, 'how does my moustache', 'Opening — mustache check / no formal intro'),
    (104, 'cancel culture', 'Cancel culture / parody / satire'),
    (312, 'take JK away', "JK / what can we say"),
    (498, 'jesters like that', 'Jesters / funny philosopher role'),
    (544, 'TikTok', 'New forms of comedy / TikTok memes'),
    (1002, 'pre-internet brain', 'FOMO / pre-internet brain / phone anxiety'),
    (1081, 'am i delusional', 'Belief in yourself / internet reassurance'),
    (1442, 'smoked weed together', 'Substance history / family / eighth grade'),
    (1990, 'avatar telling you', 'Avatar / Jim Carrey / true self'),
    (2350, 'without psilocybin', 'Psilocybin / DMT / not who I was going to be'),
    (3275, 'called Stay In Prison', 'Stay In Prison band / stumbling into music'),
    (3476, 'do open mics', 'Open mics / putting yourself out there'),
    (3690, 'being a stand-up comedian', 'What stand-up is / reacting to crowds'),
    (3963, 'Andrew Schultz', 'Andrew Schultz / filming sets'),
    (4330, 'comedic genius', 'Believing in yourself / comedic genius'),
    (5233, 'during the quarantine', 'Quarantine / what is next'),
    (5403, 'putting on my own shows', 'Putting on shows / venues / open mic organizers'),
    (None, 'drink some', 'Outro — crumb_guzzler / Stay In Prison / drink water'),
]
chapters = []
used = set()
for target, needle, label in chapter_needles:
    hit = find(needle, None)
    if not hit:
        continue
    s, sp, tx = hit
    if target is None:
        last = None
        for ms, sp2, t2 in turns:
            if needle.lower() in t2.lower():
                last = (ms / 1000.0, sp2, t2)
        if last:
            s, sp, tx = last
    aid = anchor_id_s(s)
    if aid in used:
        continue
    used.add(aid)
    chapters.append((s, label))
chapters.sort(key=lambda x: x[0])

keywords = (
    'Joseph Crumb, Redefining your life and wait why are you taking me seriously, '
    'Junkyard Love Podcast episode 0043, JYLP 0043, stand-up comedy, cancel culture, '
    'jester, FOMO, validation, Stay In Prison, open mic, psychedelics, psilocybin, DMT, '
    'chameleon personality, Jacob Rhines'
)
hashtags = (
    '#JosephCrumb #JYLP0043 #JunkyardLove #StandUpComedy '
    '#CancelCulture #OpenMic #StayInPrison #FOMO #JYLP'
)
guest_bio = (
    'Joseph Crumb (stand-up comedian; RSS title: Stand-Up Comedian Joseph Crumb) appears on '
    'Junkyard Love episode 0043 — Redefining your life and - wait why are you taking me seriously? '
    'Jacob’s published notes describe a conversation on the jester and funny philosopher in society, '
    'cancel culture, parody, jokes and context/timing, FOMO and always-on devices, seeking validation, '
    'habits and mind-altering substances, his band Stay In Prison, open mic nights, performance, '
    'insecurities, chameleon personality, and mental wellness tips. Published RSS/YT quotes include '
    'lines on taking away “jk”, looking through a “what the fuck” lens, and your avatar telling you '
    'who the real you is. Guest slug joseph-crumb is NEW. Inventory has_quotes=yes / has_timestamps=no '
    '/ has_hashtags=no / has_guest_links=no (Instagram/Twitter contact stripped from About).'
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
    "Source: YouTube automatic captions en/en-orig (captions.en.vtt / captions.en.json3; also archived as source-yt.en*); no official/manual track; no >> diarization markers\n"
    f"Video: {YOUTUBE}\n"
    f"Turns: {len(turns)}\n"
    f"Word count: {word_count}\n"
    "Speaker map: pause-gap segmentation + sticky Jacob/Joseph content scoring (named speaker labels not present in captions; auto diarization imperfect); no formal host bumper — conversation opens mid-banter\n"
    "Cleanup: light dedupe of consecutive duplicate words; merged consecutive same-speaker fragments; HTML entities/nbsp unescaped; capitalized turn starts after merge; light caption spacing tidy; light ASR name tidy (Joseph Crumb; Stay In Prison; Joe Rogan; Andrew Schultz; TikTok; FOMO; DMT); outro promo/drink-water forced to Jacob where clear; YouTube swear blanks normalized to ****\n"
    "No sentence rewriting.\n"
    f"Guest name spelling: Joseph Crumb (YT title / display); RSS title uses Stand-Up Comedian Joseph Crumb; slug {GUEST_SLUG} (NEW).\n"
    "Note: automatic diarization is imperfect; remaining short backchannels and some mid-turn blends may still be swapped in places. Episode opens without a formal Junkyard Love bumper.\n"
    f"Issue: YouTube automatic captions (en/en-orig) used; no official/manual track; no >> speaker flips. YT duration {YT_DURATION_S}s vs RSS/inventory {DURATION_S}s (archive meta uses RSS duration). No published chapter timestamps. Title YT≠RSS (H1 uses YouTube). About YT~itunes:summary (YT primary; Instagram/Twitter contact + quotes block stripped from About). Inventory has_quotes=yes / has_timestamps=no / has_hashtags=no / has_guest_links=no. Published quotes from YT/RSS description. Archive picks fills timestamped quotes/chapters/keywords/hashtags/bio. Guest page: {GUEST_SLUG} (NEW).\n"
    f"Speaker balance: Jacob {balance.get('Jacob',0)} turns/{words_by.get('Jacob',0)} words; Joseph {balance.get('Joseph',0)} turns/{words_by.get('Joseph',0)} words.\n"
    f"Heuristic speaker fixes: {len(fixes)}; post-splits: {len(post_fixes)} ({'; '.join(post_fixes)})\n",
    encoding='utf-8',
)

(CONTENT / 'SOURCES.txt').write_text(
    "Description source: YouTube primary per archive rules; About spaced from YT plain description (~itunes:summary). Guest Instagram/Twitter contact stripped. Quotes block moved to Quotes. No guest contact/email.\n"
    f"YouTube chars: {len(yt_desc.strip())}\n"
    f"RSS HTML chars: {len(rss_html.strip())}\n"
    f"Title source: YouTube / exact_public_title ({VIDEO_ID}). YT≠RSS (H1 uses YouTube; RSS adds Stand-Up Comedian).\n"
    f"Title: {TITLE}\n"
    f"RSS title: {RSS_TITLE}\n"
    "Chapters source: none published in episode notes (inventory has_timestamps=no); no YT chapters\n"
    "Guest links: none published on archive page (inventory has_guest_links=no); Instagram/Twitter CTA stripped from About\n"
    f"Quotes: {len(published_quotes)} published quotes from YT/RSS description (inventory has_quotes=yes)\n"
    "Hashtags: none published (inventory has_hashtags=no)\n"
    "About: Jacob published description verbatim as spaced paras from YouTube (contact/quotes stripped)\n"
    f"Guest name spelling: Joseph Crumb; guest slug {GUEST_SLUG} (NEW)\n"
    f"Duration: RSS itunes:duration {DURATION_S}s ({DURATION_HUMAN}); YT info.json duration {YT_DURATION_S}s — using RSS/inventory {DURATION_S}\n"
    "Publish date: RSS/inventory 2020-05-29 (YT upload_date 20200530)\n"
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
    'title_conflict': 'YT≠RSS',
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
if published_quotes:
    quotes_html = '<ul class="quotes">\n' + '\n'.join(f'<li>“{escape(q)}”</li>' for q in published_quotes) + '\n</ul>'
else:
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

ld_keywords = keywords + ', Joseph Crumb, stand-up comedian, Jacob Rhines, Junkyard Love Podcast'
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
<p class="note">From YouTube automatic captions; light cleanup; speaker labels via imperfect auto diarization (Jacob/Joseph may be swapped in places). Episode opens without a formal host bumper.</p>
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

bio_html = about_html

# Guest page NEW
guest_dir = SITE / 'guests' / GUEST_SLUG
guest_dir.mkdir(parents=True, exist_ok=True)

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
<p class="note">Appeared on The Junkyard Love Podcast (1 episode)</p>
<h2>Episodes</h2>
<ul class="list">
  <li><a href="../../episodes/__SLUG__/index.html">__TITLE__</a><br><span class="note">__DATE__ · Episode __EPNUM__</span></li>
</ul>
<h2>From the episode notes</h2>
<p class="note">Copied from published episode descriptions (not a new biography).</p>
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

# Insert after 0044 (descending episode list)
marker_home = (
    '  <li><a href="episodes/0044-spencer-hicks-operating-optimally-should-be-your-goal/index.html">'
    'Episode 044 with Spencer Hicks - Operating Optimally Should Be Your Goal</a>'
    '<br><span class="note">2020-06-10 · Spencer Hicks · 1:28:24</span></li>\n'
)
marker_ep = (
    '  <li><a href="episodes/0044-spencer-hicks-operating-optimally-should-be-your-goal/index.html">'
    'Episode 044 with Spencer Hicks - Operating Optimally Should Be Your Goal</a>'
    '<br><span class="note">Episode 0044 · 2020-06-10 · 1:28:24 · Guest: Spencer Hicks</span></li>\n'
)

home = (SITE / 'index.html').read_text(encoding='utf-8')
if EP_SLUG not in home:
    if marker_home not in home:
        raise SystemExit('home 0044 marker not found')
    home = home.replace(marker_home, marker_home + home_li)
    (SITE / 'index.html').write_text(home, encoding='utf-8')

ep_index = (SITE / 'episodes' / 'index.html').read_text(encoding='utf-8')
if EP_SLUG not in ep_index:
    if marker_ep not in ep_index:
        raise SystemExit('ep index 0044 marker not found')
    ep_index = ep_index.replace(marker_ep, marker_ep + ep_li)
    (SITE / 'episodes' / 'index.html').write_text(ep_index, encoding='utf-8')

# Guest NEW — alphabetically after Jordenelle Tsugawa (before Josh Gebhardt)
guests_index = (SITE / 'guests' / 'index.html').read_text(encoding='utf-8')
if GUEST_SLUG not in guests_index:
    guest_li = f'  <li><a href="guests/{GUEST_SLUG}/index.html">{escape(GUEST)}</a></li>\n'
    for cand in [
        '  <li><a href="guests/jordenelle-tsugawa/index.html">Jordenelle Tsugawa</a></li>\n',
        '  <li><a href="guests/josh-gebhardt/index.html">Josh Gebhardt</a></li>\n',
        '  <li><a href="guests/jerry-fu/index.html">Jerry Fu</a></li>\n',
    ]:
        if cand in guests_index:
            if 'jordenelle-tsugawa' in cand or 'jerry-fu' in cand:
                guests_index = guests_index.replace(cand, cand + guest_li, 1)
            else:
                guests_index = guests_index.replace(cand, guest_li + cand, 1)
            break
    else:
        raise SystemExit('guests index insert marker not found')
    (SITE / 'guests' / 'index.html').write_text(guests_index, encoding='utf-8')

sm = (SITE / 'sitemap.xml').read_text(encoding='utf-8')
if EP_SLUG not in sm:
    insert = (
        f'  <url><loc>{SITE_BASE}/episodes/{EP_SLUG}/</loc></url>\n'
        f'  <url><loc>{SITE_BASE}/episodes/{EP_SLUG}/episode.md</loc></url>\n'
    )
    m44 = f'  <url><loc>{SITE_BASE}/episodes/0044-spencer-hicks-operating-optimally-should-be-your-goal/episode.md</loc></url>\n'
    if m44 not in sm:
        raise SystemExit('sitemap 0044 marker not found')
    sm = sm.replace(m44, m44 + insert)
if GUEST_SLUG not in sm:
    g_insert = f'  <url><loc>{SITE_BASE}/guests/{GUEST_SLUG}/</loc></url>\n'
    g_mark = f'  <url><loc>{SITE_BASE}/guests/jordenelle-tsugawa/</loc></url>\n'
    if g_mark in sm:
        sm = sm.replace(g_mark, g_mark + g_insert)
    else:
        g_mark2 = f'  <url><loc>{SITE_BASE}/guests/josh-gebhardt/</loc></url>\n'
        if g_mark2 in sm:
            sm = sm.replace(g_mark2, g_insert + g_mark2)
        else:
            sm = sm.replace('</urlset>', g_insert + '</urlset>')
(SITE / 'sitemap.xml').write_text(sm, encoding='utf-8')

llms = (SITE / 'llms.txt').read_text(encoding='utf-8')
if EP_SLUG not in llms:
    ep_line = (
        f'- [0043 Joseph Crumb — Redefining your life and - wait why are you taking me seriously?]'
        f'({SITE_BASE}/episodes/{EP_SLUG}/) — {DATE}\n'
    )
    m44_line = (
        f'- [0044 Spencer Hicks — Operating Optimally Should Be Your Goal]'
        f'({SITE_BASE}/episodes/0044-spencer-hicks-operating-optimally-should-be-your-goal/) — 2020-06-10\n'
    )
    if m44_line not in llms:
        raise SystemExit('llms 0044 ep line not found')
    llms = llms.replace(m44_line, m44_line + ep_line)
    md_line = f'- [{SITE_BASE}/episodes/{EP_SLUG}/episode.md]({SITE_BASE}/episodes/{EP_SLUG}/episode.md)\n'
    m44_md = (
        f'- [{SITE_BASE}/episodes/0044-spencer-hicks-operating-optimally-should-be-your-goal/episode.md]'
        f'({SITE_BASE}/episodes/0044-spencer-hicks-operating-optimally-should-be-your-goal/episode.md)\n'
    )
    if m44_md in llms and md_line not in llms:
        llms = llms.replace(m44_md, m44_md + md_line)
if f'/guests/{GUEST_SLUG}/' not in llms:
    g_line = f'- [Joseph Crumb]({SITE_BASE}/guests/{GUEST_SLUG}/)\n'
    for cand in [
        f'- [Jordenelle Tsugawa]({SITE_BASE}/guests/jordenelle-tsugawa/)\n',
        f'- [Josh Gebhardt]({SITE_BASE}/guests/josh-gebhardt/)\n',
        f'- [Jerry Fu]({SITE_BASE}/guests/jerry-fu/)\n',
    ]:
        if cand in llms:
            if 'Josh Gebhardt' in cand:
                llms = llms.replace(cand, g_line + cand, 1)
            else:
                llms = llms.replace(cand, cand + g_line, 1)
            break
(SITE / 'llms.txt').write_text(llms, encoding='utf-8')

readme = (ROOT / 'README.md').read_text(encoding='utf-8')
if EP_SLUG not in readme and '**0043**' not in readme:
    marker = (
        '- **0044** Spencer Hicks — Operating Optimally Should Be Your Goal — '
        '`site/episodes/0044-spencer-hicks-operating-optimally-should-be-your-goal/`\n'
    )
    add = (
        '- **0043** Joseph Crumb — Redefining your life and - wait why are you taking me seriously? — '
        '`site/episodes/0043-joseph-crumb-redefining-your-life-and-wait-why-are-you-taking-me-seriously/`\n'
    )
    if marker not in readme:
        raise SystemExit('README 0044 marker not found')
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
    print('deploy synced (no commit/push)')

print('DONE')
print('slug', EP_SLUG)
print('guest', GUEST_SLUG, 'NEW')
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
print('Around mid:')
for ms, sp, tx in turns:
    if 1900000 <= ms <= 2100000:
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
print('title_conflict YT≠RSS')
print('H1', TITLE)
print('deploy synced', DEPLOY.exists())
