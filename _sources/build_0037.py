#!/usr/bin/env python3
"""Process Junkyard Love episode 0037 — Rebecca Wyld of Wyld Wellness (single guest, NEW).
YT=RSS title. Inventory has_quotes=yes, has_timestamps=no, has_guest_links=no, has_hashtags=no.
Guest slug: rebecca-wyld (NEW — distinct from rebecca-wild / episode 0110; do not merge).
Archive picks required. Imperfect auto diarization flagged.
Long pre-roll bumper (~2 min) then conversation; YouTube video shorter than full RSS audio."""
from __future__ import annotations
import json, re, shutil
from pathlib import Path
from html import escape, unescape
from collections import Counter

ROOT = Path('/workspace/junkyard-love-archive')
CONTENT = ROOT / 'content/0037-rebecca-wyld-habit-change-and-happiness-actualization'
SITE = ROOT / 'site'
DEPLOY = Path('/workspace/junkyard-love-archive-deploy')
EP_SLUG = '0037-rebecca-wyld-habit-change-and-happiness-actualization'
GUEST_SLUG = 'rebecca-wyld'
TITLE = 'Episode 037 with Life Coach Rebecca Wyld of Wyld Wellness - Habit Change and Happiness Actualization'
RSS_TITLE = TITLE
GUEST = 'Rebecca Wyld'
GUEST_SHORT = 'Rebecca'
YOUTUBE = 'https://www.youtube.com/watch?v=fIhM0OH2C30'
RSS_URL = 'https://share.transistor.fm/s/370cd41f'
AUDIO_URL = 'https://2.gum.fm/op3.dev/e/pdcn.co/e/pscrb.fm/rss/p/pdst.fm/e/dts.podtrac.com/redirect.mp3/media.transistor.fm/370cd41f/a9541c1f.mp3'
DATE = '2020-04-23'
DURATION_S = 8445  # RSS / inventory
YT_DURATION_S = 7005
EP_NUM = '0037'
EP_INT = 37
SPOTIFY = 'https://open.spotify.com/show/45J7CBdM8j29doqyBp2bFs'
APPLE = 'https://podcasts.apple.com/us/podcast/the-junkyard-love-podcast/id1489118788'
SITE_BASE = 'https://junkyardlovejakesbot.github.io/junkyard-love-archive'
VIDEO_ID = 'fIhM0OH2C30'

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
    f'title={TITLE}\nupload_date=20200424\nduration={YT_DURATION_S}\nvideo_id={VIDEO_ID}\n',
    encoding='utf-8',
)

# ---------- ABOUT from YouTube (primary; ~itunes:summary) ----------
yt_body = yt_desc
for marker in ['\nThe Junkyard Love Podcast', '\n\u2605 Episode details', '\n\u2605 Additional episodes']:
    idx = yt_body.find(marker)
    if idx >= 0:
        yt_body = yt_body[:idx]
yt_body = yt_body.strip()

# Published quotes from YT (inventory has_quotes=yes) — strip from About
published_quotes = []
m = re.search(r'(?:\|\s*)?Some quotes from our chat\s*[-–—|]?\s*(.*)$', yt_body, re.S | re.I)
if m:
    qblock = m.group(1)
    yt_body = yt_body[:m.start()].rstrip()
    # drop trailing lone pipes
    yt_body = re.sub(r'\|+\s*$', '', yt_body).rstrip()
    # Prefer per-quote extraction (YT sometimes puts two quotes on one line)
    for qm in re.findall(r'[“"]([^”"]{8,})[”"]', qblock):
        q = qm.strip()
        if q and q not in published_quotes:
            published_quotes.append(q)
if not published_quotes:
    # fallback from published YT/RSS quote block
    published_quotes = [
        'Your beliefs are there because of your experiences and then those same experiences confirm your beliefs.',
        'Why am I being a jerk to myself, is there another way?',
        "what if what you actually want is just a lil' bushwhack away?",
        'if its your truth, own it!',
        'It took a long time for me to be able to look into the mirror and point out the things I loved instead of the things I hate.',
        'Take me to a place where I feel small',
    ]

about_paras = [x.strip() for x in re.split(r'\n\s*\n', yt_body) if x.strip()]
expanded = []
for block in about_paras:
    parts = [ln.strip() for ln in block.split('\n') if ln.strip()]
    if len(parts) > 1 and all(len(pt) > 40 for pt in parts):
        expanded.extend(parts)
    else:
        expanded.append(block)
about_paras = expanded
# Soft-split long About into readable paras at sentence/topic boundaries (verbatim text)
if len(about_paras) == 1 and len(about_paras[0]) > 200:
    remaining = about_paras[0]
    soft_breaks = [
        'Life Coaching - What is it?',
        'We share hiking stories',
        'She believes in taking one step',
        "There's concurrence between us",
        'We talk breaking family cycles',
        'Rebecca Wyld loves to learn why people',
        'To get ahold of Rebecca',
    ]
    chunks = []
    for br in soft_breaks:
        idx = remaining.find(br)
        if idx > 40:
            chunks.append(remaining[:idx].strip())
            remaining = remaining[idx:].strip()
    if remaining:
        chunks.append(remaining)
    if len(chunks) >= 2:
        about_paras = chunks
elif len(about_paras) >= 2 and any(len(p) > 900 for p in about_paras):
    new_paras = []
    soft_breaks = [
        'Life Coaching - What is it?',
        'We share hiking stories',
        'She believes in taking one step',
        "There's concurrence between us",
        'We talk breaking family cycles',
        'Rebecca Wyld loves to learn why people',
        'To get ahold of Rebecca',
    ]
    for p in about_paras:
        if len(p) <= 900:
            new_paras.append(p)
            continue
        remaining = p
        chunks = []
        for br in soft_breaks:
            idx = remaining.find(br)
            if idx > 40:
                chunks.append(remaining[:idx].strip())
                remaining = remaining[idx:].strip()
        if remaining:
            chunks.append(remaining)
        new_paras.extend(chunks if chunks else [p])
    about_paras = new_paras

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
    if low in ('foreign', 'you') and e.get('tStartMs', 0) > YT_DURATION_S * 1000 - 25000:
        continue
    t0 = e.get('tStartMs', 0)
    # Clip to YouTube end (YT shorter than RSS full audio)
    if t0 >= YT_DURATION_S * 1000 + 8000:
        continue
    text = re.sub(r'\[\s*__\s*\]', '****', text)
    text = text.replace('\u00a0', ' ').replace('[\u00a0__\u00a0]', '****').replace('[__]', '****')
    text = re.sub(r'\[\s*[_\u00a0]+\s*\]', '****', text)
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
        r'^(Well,? (?:I|so|yeah|we)|Yeah,? (?:so|I|and|we|dude|man)|So,? (?:I|we|when|in|the|my)|I (?:think|was|love|want|had|grew|got|mean|have|always|feel|work|don.?t|ran|run|suppose|started|wrote)|We (?:are|were|have|had|just|all|been)|Absolutely|Thank you|Okay|Yes|Right|For me|Um,? (?:I|so|yeah)|Man |Dude |For sure|My husband|As a (?:life )?coach|Life coach|Wyld|Wild Wellness|Cosmetolog)',
        text.strip(), re.I))
    starts_jacob = bool(re.match(
        r'^(Hello|Welcome|hello and welcome|Well,? so|So,? (?:let\'s|what|um|all right|bro)|Junkyard|Thank you|Yeah,? yeah|Wave|Peace out|Knowledge is|Reality is|Listeners|Cool so|What.?s up|Check it out|Drink some|Folks if|All right bro|My friends|Rebecca|Tell listeners|Alright let.?s roll|appreciate you|today\'s episode|today.?s recommendation)',
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
        (r'\brebecca wilde\b', 'Rebecca Wyld'),
        (r'\brebecca wyld\b', 'Rebecca Wyld'),
        (r'\brebecca wild\b', 'Rebecca Wyld'),  # ASR; this episode is Wyld not Wild
        (r'\bwyld wellness\b', 'Wyld Wellness'),
        (r'\bwild wellness\b', 'Wyld Wellness'),
        (r'\bwyld_wellness\b', 'Wyld_Wellness'),
        (r'\bwyldandwell\b', 'wyldandwell'),
        (r'\banthony demaio\b', 'Anthony de Mello'),
        (r'\banthony de maio\b', 'Anthony de Mello'),
        (r'\banthony demello\b', 'Anthony de Mello'),
        (r'\btim ferriss\b', 'Tim Ferriss'),
        (r'\btim ferris\b', 'Tim Ferriss'),
        (r'\bface ?time\b', 'FaceTime'),
        (r'\binstagram\b', 'Instagram'),
        (r'\byoutube\b', 'YouTube'),
        (r'\bspotify\b', 'Spotify'),
        (r'\bcovid\b', 'COVID'),
        (r'\bjake rynes\b', 'Jake Rhines'),
        (r'\bjacob rhines\b', 'Jacob Rhines'),
        (r'\bjunkyard love podcast\b', 'Junkyard Love Podcast'),
        (r'\bjunkyard love\b', 'Junkyard Love'),
        (r'\baudible\b', 'Audible'),
        (r'\bwhole foods\b', 'Whole Foods'),
        (r'\ball trails\b', 'AllTrails'),
    ]
    for pat, rep in reps:
        text = re.sub(pat, rep, text, flags=re.I)
    return text


def score_jacob(text):
    tlow = text.lower()
    s = 0
    for pat in [
        r'\bjunkyard\b', r'\bwelcome to the (?:virtual |remote )?(?:junkyard )?podcast\b',
        r'\bhello and welcome\b', r'\btoday\'?s recommendation\b',
        r'\btoday\'?s episode with rebecca\b', r'\bknowledge is power\b',
        r'\bdrink (?:some |dat |tons of )?water\b', r'\blove yourself\b', r'\bpeace out\b',
        r'\btake care of yourself\b', r'\blisteners?\b',
        r'\bjacob from the internet\b', r'\bjake rhines\b',
        r'\bget present\b',
        r'\bfolks if you enjoyed\b', r'\bsee you next\b',
        r'\bmy podcast\b', r'\ball right bro\b',
        r'\bface ?time your\b', r'\banthony de mello\b',
        r'\btim ferriss\b', r'\bawareness by anthony\b',
        r'\bi\'?ve been able to not have to edit\b',
        r'\bmy first like 10 episodes\b',
        r'\bwhen i make a song\b', r'\bas a dj\b',
        r'\byou as a dj\b',
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


def score_rebecca(text):
    tlow = text.lower()
    s = 0
    for pat in [
        r'\blife coach\b', r'\bwyld wellness\b', r'\bcosmetolog',
        r'\bmy husband\b', r'\bmy rigidity\b',
        r'\bhabit loops?\b', r'\bbushwhack\b',
        r'\bjerk to myself\b', r'\bmirror and point out\b',
        r'\bfeel small\b', r'\bthreshold theory\b',
        r'\bneck pain\b', r'\bcougars?\b', r'\bcoyotes?\b',
        r'\bholistic\b', r'\bself-?love\b',
        r'\bwhole foods\b', r'\binflammation\b',
        r'\bi started writing\b', r'\bown it if it.?s\b',
        r'\bparalysis\b', r'\bcoaching\b',
        r'\bslow down and do those things\b',
        r'\bliterally saved my life\b',
        r'\bgetting people back to the simple\b',
    ]:
        if re.search(pat, tlow):
            s += 5
    if re.search(r'\bi (?:was|had|grew|got|did|started|think|feel|have|went|lived|always|work|don.?t|ran|run|suppose|would say|wrote)\b', tlow) and len(text.split()) > 40:
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
    sg = score_rebecca(text)

    # Opening bumper (~first ~125s) forced to Jacob
    if ms < 130000 and re.search(r'hello|welcome|junkyard|knowledge is|recommendation|anthony|ferriss|face ?time|today.?s episode|rebecca|wilde it.?s quite fantastic|fantastical', text, re.I):
        sp = 'Jacob'
    elif sj > sg + 1:
        sp = 'Jacob'
    elif sg > sj + 1:
        sp = 'Rebecca'
    else:
        if sj > sg:
            sp = 'Jacob'
        elif sg > sj:
            sp = 'Rebecca'
        else:
            if len(text.split()) <= 8:
                sp = 'Rebecca' if prev == 'Jacob' else 'Jacob'
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
    if ms < 130000 and re.search(r'hello|welcome|junkyard|knowledge is|recommendation|anthony|ferriss|face ?time|today.?s episode|rebecca|wilde it.?s quite fantastic|fantastical', low):
        sp = 'Jacob'
    if re.search(r'life coach|wyld wellness|cosmetolog|my husband|habit loops?|bushwhack|jerk to myself|threshold theory|neck pain|cougars?|coyotes?|literally saved my life|i started writing|my favorite thing about that is noticing|if it is your truth then it doesn.?t really matter', low):
        sp = 'Rebecca'
    if re.search(r'drink (?:some |dat |tons of )?water|see you (?:guys )?next|peace out|get present|knowledge is power|folks if you enjoyed|hello and welcome|today.?s recommendation|today.?s episode with rebecca|face ?time your', low):
        if re.search(r'peace out|folks if|hello and welcome|today.?s recommendation|today.?s episode with rebecca|knowledge is|face ?time your|listener', low) or ms < 130000 or ms >= YT_DURATION_S * 1000 - 90000:
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
    r'(.*(?:today.?s episode with Rebecca Wyld|rebecca wilde it.?s quite fantastic).*)\s+(.*(?:mostly i.?ve been able|i.?ve been able to not have to edit).*)',
    'Jacob', 'Jacob', 'split bumper / jacob open chat')
split_on(
    r'(.*(?:you can.?t rewind|conversation that happened|that.?s it.?s a conversation).*)\s+(.*(?:my favorite thing about that|noticing that you are a beginner|are a beginner in something).*)',
    'Jacob', 'Rebecca', 'split Jacob / Rebecca beginner truth')

rescored = []
for i, (ms, sp, tx) in enumerate(turns):
    low = tx.lower()
    sj = score_jacob(tx)
    sg = score_rebecca(tx)
    if ms < 130000 and re.search(r'hello|welcome|junkyard|knowledge is|recommendation|anthony|ferriss|face ?time|today.?s episode|rebecca|wilde it.?s quite fantastic|fantastical', low):
        sp = 'Jacob'
    elif re.search(r'junkyard love|get present|hello and welcome|knowledge is power|folks if you enjoyed|see you next|today.?s recommendation|today.?s episode with rebecca', low):
        sp = 'Jacob'
    elif re.search(r'life coach|wyld wellness|cosmetolog|my husband|habit loops?|bushwhack|jerk to myself|threshold theory|literally saved my life|neck pain|my favorite thing about that is noticing|if it is your truth then it doesn.?t really matter', low):
        sp = 'Rebecca'
    elif sj > sg + 2:
        sp = 'Jacob'
    elif sg > sj + 2:
        sp = 'Rebecca'
    if ms >= YT_DURATION_S * 1000 - 90000 and re.search(r'folks if|please share|follow like subscribe|see you next|junkyard|drink some water|listeners|get present|peace out', low):
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
    ('beliefs are there because of your experiences', 'Rebecca'),
    ('jerk to myself', 'Rebecca'),
    ('bushwhack', 'Rebecca'),
    ('own it', 'Rebecca'),
    ('feel small', 'Rebecca'),
    ('habit loops', 'Rebecca'),
    ('literally saved my life', 'Rebecca'),
    ('inflammation', 'Rebecca'),
    ('Whole Foods', 'Rebecca'),
    ('threshold theory', 'Rebecca'),
    ('neck pain', 'Rebecca'),
    ('cosmetologist', 'Rebecca'),
    ('awareness by Anthony', 'Jacob'),
    ('slow down', 'Rebecca'),
    ('boundaries', 'Rebecca'),
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
    (1, 'hello and welcome', 'Opening bumper — Junkyard Love'),
    (48, 'knowledge is power', 'Knowledge is power'),
    (54, 'today\'s recommendation', 'Book rec — Awareness by Anthony de Mello'),
    (92, 'today\'s episode with Rebecca', 'Introducing Rebecca Wyld'),
    (126, 'I\'ve been able to not have to edit', 'Conversation open — editing / being a beginner'),
    (440, 'self-love', 'Self-love / living well'),
    (480, 'enough water going out into nature', 'Water / nature / what saved her life'),
    (800, 'feel small', 'Take me where I feel small'),
    (918, 'AllTrails', 'Hiking / AllTrails'),
    (1021, 'Cougars', 'Cougars / bears on hikes'),
    (1222, 'coyotes', 'Coyotes'),
    (1302, 'boundaries', 'Boundaries you didn\'t know you had'),
    (1530, 'flexible', 'Flexible vs rigid'),
    (1722, 'coaching', 'Life coaching — what it is'),
    (2153, 'cosmetologist', 'Cosmetologist chats in the chair'),
    (2412, 'neck pain', 'Neck pain path into healing'),
    (2647, 'inflammation', 'Inflammation'),
    (3033, 'Whole Foods', 'Whole Foods / re-learning health'),
    (3089, 'your experiences beliefs', 'Beliefs confirmed by experiences'),
    (3345, 'holistic', 'Holistic wellness'),
    (3434, 'habit loops', 'Habit loops'),
    (3460, 'jerk to myself', 'Why am I being a jerk to myself'),
    (3496, 'bushwhack', 'Lil\' bushwhack away'),
    (4052, 'I started writing', 'Writing is magic'),
    (4487, 'own it', 'If it\'s your truth, own it'),
    (4996, 'ritual', 'Ritual / spiritual practice'),
    (5751, 'threshold theory', 'Threshold theory'),
    (6897, 'social anxiety', 'Social anxiety / depression — YT cut near end'),
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
    'Rebecca Wyld, Wyld Wellness, Habit Change and Happiness Actualization, '
    'Junkyard Love Podcast episode 0037, JYLP 0037, life coach, habit change, '
    'self-love, holistic health, hiking, boundaries, inflammation, mirror work, '
    'beliefs, bushwhack, cosmetologist, Jacob Rhines'
)
hashtags = (
    '#RebeccaWyld #WyldWellness #JYLP0037 #JunkyardLove '
    '#HabitChange #LifeCoach #SelfLove #HolisticHealth #JYLP'
)
guest_bio = (
    'Rebecca Wyld appears on Junkyard Love episode 0037 — Habit Change and Happiness Actualization. '
    'Jacob’s published notes describe her as a life coach, cosmetologist, outdoors advocate, and founder of Wyld Wellness, '
    'oriented toward simple living, habit change, self-love, and holistic health. '
    'Guest slug rebecca-wyld is NEW (distinct from rebecca-wild / episode 0110 — different person/spelling; do not merge). '
    'Inventory has_quotes=yes / has_timestamps=no / has_hashtags=no / has_guest_links=no. Title conflict none (YT=RSS).'
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
    "Speaker map: pause-gap segmentation + sticky Jacob/Rebecca content scoring (named speaker labels not present in captions; auto diarization imperfect); bumper forced to Jacob where clear\n"
    "Cleanup: light dedupe of consecutive duplicate words; merged consecutive same-speaker fragments; HTML entities/nbsp unescaped; capitalized turn starts after merge; light caption spacing tidy; light ASR name tidy (Rebecca Wyld not Wilde/Wild; Anthony de Mello; Tim Ferriss; Wyld Wellness; AllTrails; FaceTime); bumper forced to Jacob where clear; YouTube swear blanks normalized to ****\n"
    "No sentence rewriting.\n"
    f"Guest name spelling: Rebecca Wyld (YT/RSS titles / inventory); slug {GUEST_SLUG} (NEW — distinct from rebecca-wild / 0110).\n"
    "Note: automatic diarization is imperfect; remaining short backchannels and some mid-turn blends may still be swapped in places. Long pre-roll bumper then conversation.\n"
    f"Issue: YouTube automatic captions (en/en-orig) used; no official/manual track; no >> speaker flips. YT duration {YT_DURATION_S}s vs RSS/inventory {DURATION_S}s (archive meta uses RSS duration; transcript clipped to YT — YouTube video ends before full RSS audio). No published chapter timestamps. Title YT=RSS. About YT~itunes:summary (YT primary; Some quotes from our chat stripped into Quotes). Inventory has_quotes=yes / has_timestamps=no / has_hashtags=no / has_guest_links=no. Archive picks fills timestamped quotes/chapters/keywords/hashtags/bio. Guest page: {GUEST_SLUG} (NEW). Do not merge with rebecca-wild.\n"
    f"Speaker balance: Jacob {balance.get('Jacob',0)} turns/{words_by.get('Jacob',0)} words; Rebecca {balance.get('Rebecca',0)} turns/{words_by.get('Rebecca',0)} words.\n"
    f"Heuristic speaker fixes: {len(fixes)}; post-splits: {len(post_fixes)} ({'; '.join(post_fixes)})\n",
    encoding='utf-8',
)

(CONTENT / 'SOURCES.txt').write_text(
    "Description source: YouTube primary per archive rules; About spaced from YT plain description (~itunes:summary). YT footer stripped. Quotes block stripped into Quotes. No guest contact/email invented; published social mention remains in About prose only; Guest links section none (inventory has_guest_links=no).\n"
    f"YouTube chars: {len(yt_desc.strip())}\n"
    f"RSS HTML chars: {len(rss_html.strip())}\n"
    f"Title source: YouTube / exact_public_title ({VIDEO_ID}). YT=RSS.\n"
    f"Title: {TITLE}\n"
    f"RSS title: {RSS_TITLE}\n"
    "Chapters source: none published in episode notes (inventory has_timestamps=no); no YT chapters\n"
    "Guest links: none published as structured links (inventory has_guest_links=no); About may mention Instagram/Facebook/site in prose\n"
    f"Quotes: {len(published_quotes)} published quotes from YT/RSS Some quotes from our chat block (inventory has_quotes=yes)\n"
    "Hashtags: none published (inventory has_hashtags=no)\n"
    "About: Jacob published description verbatim as spaced paras from YouTube\n"
    f"Guest name spelling: Rebecca Wyld; guest slug {GUEST_SLUG} (NEW — not rebecca-wild)\n"
    f"Duration: RSS itunes:duration {DURATION_S}s ({DURATION_HUMAN}); YT info.json duration {YT_DURATION_S}s — using RSS/inventory {DURATION_S}\n"
    "Publish date: RSS/inventory 2020-04-23 (YT upload_date 20200424)\n"
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
    'title_conflict': '',
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

ld_keywords = keywords + ', Rebecca Wyld, Wyld Wellness, habit change, Jacob Rhines, Junkyard Love Podcast'
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
<p class="note">From YouTube automatic captions; light cleanup; speaker labels via imperfect auto diarization (Jacob/Rebecca may be swapped in places). Long pre-roll bumper then conversation. YouTube video ends before full RSS audio length.</p>
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

# Guest page NEW
guest_dir = SITE / 'guests' / GUEST_SLUG
guest_dir.mkdir(parents=True, exist_ok=True)
bio_html = '\n'.join(f'<p>{escape(p)}</p>' for p in about_paras)

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

# Insert after 0038 (descending: 0038 then 0037)
marker_home = (
    '  <li><a href="episodes/0038-spencer-hicks-mental-and-physical-tips-to-maintain-health-at-home/index.html">'
    'Episode 038 with Spencer Hicks   Mental and Physical Tips To Maintain Health At Home</a>'
    '<br><span class="note">2020-04-26 · Spencer Hicks · 1:14:25</span></li>\n'
)
marker_ep = (
    '  <li><a href="episodes/0038-spencer-hicks-mental-and-physical-tips-to-maintain-health-at-home/index.html">'
    'Episode 038 with Spencer Hicks   Mental and Physical Tips To Maintain Health At Home</a>'
    '<br><span class="note">Episode 0038 · 2020-04-26 · 1:14:25 · Guest: Spencer Hicks</span></li>\n'
)

home = (SITE / 'index.html').read_text(encoding='utf-8')
if EP_SLUG not in home:
    if marker_home not in home:
        raise SystemExit('home 0038 marker not found')
    home = home.replace(marker_home, marker_home + home_li)
    (SITE / 'index.html').write_text(home, encoding='utf-8')

ep_index = (SITE / 'episodes' / 'index.html').read_text(encoding='utf-8')
if EP_SLUG not in ep_index:
    if marker_ep not in ep_index:
        raise SystemExit('ep index 0038 marker not found')
    ep_index = ep_index.replace(marker_ep, marker_ep + ep_li)
    (SITE / 'episodes' / 'index.html').write_text(ep_index, encoding='utf-8')

# Guest NEW — alphabetically after rebecca-wild (wyld > wild)
guests_index = (SITE / 'guests' / 'index.html').read_text(encoding='utf-8')
if GUEST_SLUG not in guests_index:
    guest_li = f'  <li><a href="guests/{GUEST_SLUG}/index.html">{escape(GUEST)}</a></li>\n'
    for cand in [
        '  <li><a href="guests/rebecca-wild/index.html">Rebecca Wild</a></li>\n',
        '  <li><a href="guests/ricky-navarrete/index.html">Ricky Navarrete</a></li>\n',
    ]:
        if cand in guests_index:
            if 'ricky-navarrete' in cand:
                guests_index = guests_index.replace(cand, guest_li + cand, 1)
            else:
                guests_index = guests_index.replace(cand, cand + guest_li, 1)
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
    m38 = f'  <url><loc>{SITE_BASE}/episodes/0038-spencer-hicks-mental-and-physical-tips-to-maintain-health-at-home/episode.md</loc></url>\n'
    if m38 not in sm:
        raise SystemExit('sitemap 0038 marker not found')
    sm = sm.replace(m38, m38 + insert)
if f'/guests/{GUEST_SLUG}/' not in sm:
    g_insert = f'  <url><loc>{SITE_BASE}/guests/{GUEST_SLUG}/</loc></url>\n'
    g_mark = f'  <url><loc>{SITE_BASE}/guests/rebecca-wild/</loc></url>\n'
    if g_mark in sm:
        sm = sm.replace(g_mark, g_mark + g_insert)
    else:
        g_mark2 = f'  <url><loc>{SITE_BASE}/guests/ricky-navarrete/</loc></url>\n'
        if g_mark2 in sm:
            sm = sm.replace(g_mark2, g_insert + g_mark2)
        else:
            sm = sm.replace('</urlset>', g_insert + '</urlset>')
(SITE / 'sitemap.xml').write_text(sm, encoding='utf-8')

llms = (SITE / 'llms.txt').read_text(encoding='utf-8')
if EP_SLUG not in llms:
    ep_line = (
        f'- [0037 Rebecca Wyld — Habit Change and Happiness Actualization]'
        f'({SITE_BASE}/episodes/{EP_SLUG}/) — {DATE}\n'
    )
    m38_line = (
        f'- [0038 Spencer Hicks — Mental and Physical Tips To Maintain Health At Home]'
        f'({SITE_BASE}/episodes/0038-spencer-hicks-mental-and-physical-tips-to-maintain-health-at-home/) — 2020-04-26\n'
    )
    if m38_line not in llms:
        raise SystemExit('llms 0038 ep line not found')
    llms = llms.replace(m38_line, m38_line + ep_line)
    md_line = f'- [{SITE_BASE}/episodes/{EP_SLUG}/episode.md]({SITE_BASE}/episodes/{EP_SLUG}/episode.md)\n'
    m38_md = (
        f'- [{SITE_BASE}/episodes/0038-spencer-hicks-mental-and-physical-tips-to-maintain-health-at-home/episode.md]'
        f'({SITE_BASE}/episodes/0038-spencer-hicks-mental-and-physical-tips-to-maintain-health-at-home/episode.md)\n'
    )
    if m38_md in llms and md_line not in llms:
        llms = llms.replace(m38_md, m38_md + md_line)
if f'/guests/{GUEST_SLUG}/' not in llms:
    g_line = f'- [Rebecca Wyld]({SITE_BASE}/guests/{GUEST_SLUG}/)\n'
    for cand in [
        f'- [Rebecca Wild]({SITE_BASE}/guests/rebecca-wild/)\n',
        f'- [Ricky Navarrete]({SITE_BASE}/guests/ricky-navarrete/)\n',
    ]:
        if cand in llms:
            if 'Ricky' in cand:
                llms = llms.replace(cand, g_line + cand, 1)
            else:
                llms = llms.replace(cand, cand + g_line, 1)
            break
(SITE / 'llms.txt').write_text(llms, encoding='utf-8')

readme = (ROOT / 'README.md').read_text(encoding='utf-8')
if EP_SLUG not in readme and '**0037**' not in readme:
    marker = (
        '- **0038** Spencer Hicks — Mental and Physical Tips To Maintain Health At Home — '
        '`site/episodes/0038-spencer-hicks-mental-and-physical-tips-to-maintain-health-at-home/`\n'
    )
    add = (
        '- **0037** Rebecca Wyld — Habit Change and Happiness Actualization — '
        '`site/episodes/0037-rebecca-wyld-habit-change-and-happiness-actualization/`\n'
    )
    if marker not in readme:
        raise SystemExit('README 0038 marker not found')
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
        shutil.copy(ROOT / 'build_0037.py', DEPLOY / '_sources' / 'build_0037.py')
    print('deploy synced (no commit/push)')

print('DONE')
print('slug', EP_SLUG)
print('guest', GUEST_SLUG, 'NEW — distinct from rebecca-wild')
print('turns', len(turns), 'words', word_count)
print('about paras', len(about_paras))
print('published quotes', len(published_quotes))
print('quotes_ap', len(quotes_ap), 'archive_chapters', len(chapters))
print('balance', dict(balance), dict(words_by))
print('title_conflict', repr(meta['title_conflict']))
print('H1', TITLE)
print('About paras:')
for i, para in enumerate(about_paras):
    print(f'  [{i}] {para[:160].replace(chr(10), " / ")}')
print('Published quotes:')
for q in published_quotes:
    print(f'  - {q[:100]}')
print('First 8:')
for ms, sp, tx in turns[:8]:
    print(f'[{ms_to_ts(ms)}] {sp:12s} {len(tx.split()):4d}w | {tx[:100]}')
print('Around conversation open:')
for ms, sp, tx in turns:
    if 100000 <= ms <= 250000:
        print(f'[{ms_to_ts(ms)}] {sp:12s} {len(tx.split()):4d}w | {tx[:100]}')
print('Last 5:')
for ms, sp, tx in turns[-5:]:
    print(f'[{ms_to_ts(ms)}] {sp:12s} {len(tx.split()):4d}w | {tx[:100]}')
