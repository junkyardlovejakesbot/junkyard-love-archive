#!/usr/bin/env python3
"""Process Junkyard Love episode 0038 — Spencer Hicks (single guest).
YT≠RSS title (prefer YouTube H1; keep YT spacing). Inventory has_quotes=no, has_timestamps=no, has_guest_links=no, has_hashtags=no.
Guest slug: spencer-hicks (EXISTING — lists 0088 + 0074 + 0059 + 0044; APPEND 0038, do not wipe).
Archive picks required. Imperfect auto diarization flagged.
Remote/video COVID at-home chat from the open — no long pre-roll bumper."""
from __future__ import annotations
import json, re, shutil
from pathlib import Path
from html import escape, unescape
from collections import Counter

ROOT = Path('/workspace/junkyard-love-archive')
CONTENT = ROOT / 'content/0038-spencer-hicks-mental-and-physical-tips-to-maintain-health-at-home'
SITE = ROOT / 'site'
DEPLOY = Path('/workspace/junkyard-love-archive-deploy')
EP_SLUG = '0038-spencer-hicks-mental-and-physical-tips-to-maintain-health-at-home'
GUEST_SLUG = 'spencer-hicks'
# Prefer YouTube title for H1 (YT≠RSS); keep published YT spacing (triple spaces)
TITLE = 'Episode 038 with Spencer Hicks   Mental and Physical Tips To Maintain Health At Home'
RSS_TITLE = 'Episode 038 with Spencer Hicks - Mental and Physical Tips To Maintain Health At Home'
GUEST = 'Spencer Hicks'
GUEST_SHORT = 'Spencer'
YOUTUBE = 'https://www.youtube.com/watch?v=pc0JcBfGisc'
RSS_URL = 'https://share.transistor.fm/s/aa1ebedd'
AUDIO_URL = 'https://2.gum.fm/op3.dev/e/pdcn.co/e/pscrb.fm/rss/p/pdst.fm/e/dts.podtrac.com/redirect.mp3/media.transistor.fm/aa1ebedd/0e27aa05.mp3'
DATE = '2020-04-26'
DURATION_S = 4465  # RSS / inventory
YT_DURATION_S = 4378
EP_NUM = '0038'
EP_INT = 38
SPOTIFY = 'https://open.spotify.com/show/45J7CBdM8j29doqyBp2bFs'
APPLE = 'https://podcasts.apple.com/us/podcast/the-junkyard-love-podcast/id1489118788'
SITE_BASE = 'https://junkyardlovejakesbot.github.io/junkyard-love-archive'
VIDEO_ID = 'pc0JcBfGisc'

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
    f'title={TITLE}\nupload_date=20200427\nduration={YT_DURATION_S}\nvideo_id={VIDEO_ID}\n',
    encoding='utf-8',
)

# ---------- ABOUT from YouTube (primary; ~itunes:summary) ----------
yt_body = yt_desc
for marker in ['\nThe Junkyard Love Podcast', '\n\u2605 Episode details', '\n\u2605 Additional episodes']:
    idx = yt_body.find(marker)
    if idx >= 0:
        yt_body = yt_body[:idx]
yt_body = yt_body.strip()
# strip leading (5) episode-series marker if present
yt_body = re.sub(r'^\(\d+\)\s*', '', yt_body).strip()

# Inventory has_quotes=no
published_quotes = []

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
if len(about_paras) == 1 and len(about_paras[0]) > 200:
    text = about_paras[0]
    # Normalize the published triple-space break into a soft paragraph boundary without dropping text
    text = re.sub(r'\s{2,}', '  ', text)  # keep at least double-space marker region intact as spaces in join
    soft_breaks = [
        'We include some recommendations',
        'Spencer and I discuss concepts',
        'The audio is subpar',
        'For more info on Spencer',
    ]
    chunks = []
    remaining = about_paras[0]
    for br in soft_breaks:
        idx = remaining.find(br)
        if idx > 20:
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
    # YT ends ~4378s; keep a little past RSS if caption exists, but clip far past YT end
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
        r'^(Well,? (?:I|so|yeah|we)|Yeah,? (?:so|I|and|we|dude|man)|So,? (?:I|we|when|in|the|my)|I (?:think|was|love|want|had|grew|got|mean|have|always|feel|work|don.?t|ran|run|suppose)|We (?:are|were|have|had|just|all|been)|Absolutely|Thank you|Okay|Yes|Right|For me|Um,? (?:I|so|yeah)|Man |Dude |For sure|I\'m a personal|Personal trainer|Stretch is|Wim Hof|bodyweight)',
        text.strip(), re.I))
    starts_jacob = bool(re.match(
        r'^(Hello|Welcome|man hello|Well,? so|So,? (?:let\'s|what|um|all right|bro)|Junkyard|Thank you|Yeah,? yeah|Wave|Peace out|Knowledge is|Reality is|Listeners|Cool so|What.?s up|Check it out|Drink some|Folks if|All right bro|My friends|Spencer|Tell listeners|Alright let.?s roll|appreciate you)',
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
        (r'\bjordan hall\b', 'Jordan Hall'),
        (r'\bwim hof\b', 'Wim Hof'),
        (r'\bwim HOF\b', 'Wim Hof'),
        (r'\bthe witcher\b', 'The Witcher'),
        (r'\bwitcher\b', 'Witcher'),
        (r'\bface ?time\b', 'FaceTime'),
        (r'\bxbox\b', 'Xbox'),
        (r'\binstagram\b', 'Instagram'),
        (r'\byoutube\b', 'YouTube'),
        (r'\bspotify\b', 'Spotify'),
        (r'\bcovid\b', 'COVID'),
        (r'\bcoronavirus\b', 'coronavirus'),
        (r'\bjake rynes\b', 'Jake Rhines'),
        (r'\bjacob rhines\b', 'Jacob Rhines'),
        (r'\bjunkyard love podcast\b', 'Junkyard Love Podcast'),
        (r'\bjunkyard love\b', 'Junkyard Love'),
        (r'\baudible\b', 'Audible'),
        (r'\bbuddhism\b', 'Buddhism'),
        (r'\bstoicism\b', 'Stoicism'),
        (r'\bamazon\b', 'Amazon'),
    ]
    for pat, rep in reps:
        text = re.sub(pat, rep, text, flags=re.I)
    return text


def score_jacob(text):
    tlow = text.lower()
    s = 0
    for pat in [
        r'\bjunkyard\b', r'\bwelcome to the (?:virtual |remote )?(?:junkyard )?podcast\b',
        r'\bwelcome to the virtual\b', r'\bremote version of the junkyard\b',
        r'\bdrink (?:some |dat |tons of )?water\b', r'\blove yourself\b', r'\bpeace out\b',
        r'\btake care of yourself\b', r'\blisteners?\b',
        r'\bjacob from the internet\b', r'\bjake rhines\b',
        r'\bget present\b', r'\bknowledge is power\b',
        r'\bfolks if you enjoyed\b', r'\bsee you next\b',
        r'\bmy podcast\b', r'\ball right bro\b',
        r'\bhello spencer\b', r'\bman hello spencer\b',
        r'\bappreciate you spencer\b', r'\bwrap this up\b',
        r'\bfocus on your posture\b', r'\bplease focus on your posture\b',
        r'\bwhat would you recommend\b', r'\blet.?s talk about those people\b',
        r'\byour advice or your maybe recommendations\b',
        r'\bnever heard any of our previous podcast\b',
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


def score_spencer(text):
    tlow = text.lower()
    s = 0
    for pat in [
        r'\bpersonal trainer\b', r'\bbodyweight squats?\b', r'\bstretch(?:ing)?\b',
        r'\bwim hof\b', r'\bbands with different strength\b',
        r'\bwater jugs\b', r'\binternal clock\b', r'\bsleep schedule\b',
        r'\bsweat everyday\b', r'\bbody in motion\b',
        r'\btissue in between your muscle\b', r'\bintensifying technique\b',
        r'\bmarriage to heavy weight\b', r'\bsloth-like\b',
        r'\bi can only speak to my own personal journey\b',
        r'\bpurely analyzing who you are\b',
        r'\bi do wim hof\b', r'\bbad posture\b',
        r'\bi spent the first couple weeks just playing xbox\b',
        r'\bi have a cat\b', r'\bdisclaimer i have a cat\b',
    ]:
        if re.search(pat, tlow):
            s += 5
    if re.search(r'\bi (?:was|had|grew|got|did|started|think|feel|have|went|lived|always|work|don.?t|ran|run|suppose|would say)\b', tlow) and len(text.split()) > 40:
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

    # Opening host greeting (~first few seconds) then conversation
    if ms < 8000 and re.search(r'hello spencer|welcome to the virtual|junkyard love', text, re.I):
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
    if ms < 8000 and re.search(r'hello spencer|welcome to the virtual|junkyard', low):
        sp = 'Jacob'
    if re.search(r'personal trainer|bodyweight squats?|wim hof|water jugs|internal clock|tissue in between your muscle|intensifying technique|marriage to heavy weight|i have a cat|disclaimer i have a cat|i spent the first couple weeks just playing xbox|bands with different strength', low):
        sp = 'Spencer'
    if re.search(r'drink (?:some |dat |tons of )?water|see you (?:guys )?next|peace out|get present|listeners|hello spencer|welcome to the virtual|knowledge is power|folks if you enjoyed|appreciate you spencer|wrap this up|please focus on your posture|never heard any of our previous podcast', low):
        if re.search(r'peace out|folks if you|hello spencer|welcome to the virtual|appreciate you spencer|wrap this up|please focus on your posture|listener|never heard any of our previous', low) or ms < 8000 or ms >= YT_DURATION_S * 1000 - 60000:
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
    r'(.*(?:appreciate you spencer|thanks for having me on my boy|cool sounds good))\s+(.*(?:listeners have a good|please focus on your posture).*)',
    'Jacob', 'Jacob', 'noop-keep jacob close')
split_on(
    r'(.*(?:thanks for having me))\s+(.*(?:listeners have a good|please focus on your posture).*)',
    'Spencer', 'Jacob', 'split Spencer thanks / Jacob outro')
split_on(
    r'(.*(?:man hello spencer welcome to the virtual remote version of the junkyard love))\s+(.*(?:disclaimer i have a cat|i have a cat).*)',
    'Jacob', 'Spencer', 'split Jacob open / Spencer cat disclaimer')

rescored = []
for i, (ms, sp, tx) in enumerate(turns):
    low = tx.lower()
    sj = score_jacob(tx)
    sg = score_spencer(tx)
    if ms < 8000 and re.search(r'hello spencer|welcome to the virtual|junkyard', low):
        sp = 'Jacob'
    elif re.search(r'junkyard love|get present|hello spencer|welcome to the virtual|knowledge is power|folks if you enjoyed|see you next|appreciate you spencer|wrap this up|please focus on your posture|listeners have a good', low):
        sp = 'Jacob'
    elif re.search(r'personal trainer|bodyweight squats?|wim hof|water jugs|internal clock|tissue in between your muscle|intensifying technique|disclaimer i have a cat|i have a cat he likes', low):
        sp = 'Spencer'
    elif sj > sg + 2:
        sp = 'Jacob'
    elif sg > sj + 2:
        sp = 'Spencer'
    if ms >= YT_DURATION_S * 1000 - 60000 and re.search(r'folks if|please share|follow like subscribe|see you next|junkyard|drink some water|listeners|get present|appreciate you spencer|focus on your posture|wrap this up', low):
        sp = 'Jacob'
    if sp != turns[i][1]:
        fixes.append(f'rescore {turns[i][1]}->{sp} @ {ms}')
    rescored.append((ms, sp, tx))
turns = merge_turns(rescored)

# Force clear outro lines to Jacob
_out = []
for ms, sp, tx in turns:
    low = tx.lower()
    if re.search(r'spencer and i will be back|listeners have a good rest|please focus on your posture|appreciate you spencer|wrap this up', low):
        if sp != 'Jacob':
            fixes.append(f'outro-force {sp}->Jacob @ {ms}')
        sp = 'Jacob'
    _out.append((ms, sp, tx))
turns = merge_turns(_out)

# Split Jacob wrap that absorbed Spencer's thanks
split_on(
    r'(.*(?:appreciate you spencer|let.?s do it again))\s+(.*(?:thanks for having me).*)',
    'Jacob', 'Spencer', 'split Jacob appreciate / Spencer thanks')
split_on(
    r'(.*(?:thanks for having me(?: on my boy)?(?: yeah my friend)?(?: cool sounds good)?))\s+(.*(?:listeners have a good|please focus on your posture|spencer and i will be back).*)',
    'Spencer', 'Jacob', 'split Spencer thanks / Jacob listeners outro')

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
    ('bodyweight squats', 'Spencer'),
    ('internal clock', 'Spencer'),
    ('stretching', 'Spencer'),
    ('Wim Hof', 'Spencer'),
    ('water jugs', None),
    ('awareness', 'Jacob'),
    ('before being mindful', 'Jacob'),
    ('body in motion', 'Spencer'),
    ('sleep schedule', 'Spencer'),
    ('posture', 'Spencer'),
    ('playing Xbox', 'Spencer'),
    ('fantasy', 'Spencer'),
    ('focus on your posture', 'Jacob'),
    ('welcome to the virtual', 'Jacob'),
    ('remember to breathe', 'Spencer'),
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
    (1, 'hello Spencer welcome to the virtual', 'Opening — virtual/remote Junkyard Love'),
    (23, 'coronavirus', 'Coronavirus / making do remotely'),
    (33, 'I have a cat', 'Spencer cat disclaimer'),
    (112, 'playing Xbox', 'Xbox / irritability / sleep schedule'),
    (270, 'routine', 'Getting back into a routine'),
    (356, 'never heard any of our previous podcast', 'Ask Spencer — at-home wellness recommendations'),
    (421, 'internal clock', 'Internal clock / consistent sleep'),
    (454, 'try to sweat', 'Sweat every day / body in motion'),
    (505, 'bodyweight squats', 'Bodyweight squats / great equalizer for fitness'),
    (525, 'stretching super important', 'Stretching as a starting place'),
    (588, 'remember to breathe', 'Remember to breathe / stick to basics'),
    (618, 'water jugs', 'At-home workout — bands / water jugs / bodyweight'),
    (800, 'five minutes the morning', 'Morning practice / less irritable'),
    (850, 'that is awareness', 'Awareness before mindfulness'),
    (1003, 'mindfulness', 'Where to start with mindfulness'),
    (1380, 'breath work and meditation', 'Breath work / meditation / planning'),
    (2186, 'Wim Hof breathing', 'Wim Hof breathing'),
    (2629, 'posture', 'Breathing and posture'),
    (4200, 'fantasy', 'Fantasy / Witcher / playground for the mind'),
    (4319, 'wrap this up', 'Wrap-up — thanks Spencer'),
    (None, 'focus on your posture', 'Outro — posture / listeners close'),
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
    'Spencer Hicks, Mental and Physical Tips To Maintain Health At Home, '
    'Junkyard Love Podcast episode 0038, JYLP 0038, COVID at-home, quarantine wellness, '
    'stretching, bodyweight workouts, sleep schedule, mindfulness, awareness, breath work, '
    'Wim Hof, posture, remote conversation, Jacob Rhines'
)
hashtags = (
    '#SpencerHicks #JYLP0038 #JunkyardLove #HealthAtHome '
    '#Mindfulness #BreathWork #WimHof #Posture #JYLP'
)
guest_bio = (
    'Spencer Hicks appears on Junkyard Love episode 0038 — Mental and Physical Tips To Maintain Health At Home. '
    'Jacob’s published notes describe a remote video chat about at-home practices during the COVID stay-at-home period: '
    'walking, stretching, at-home workouts, mindfulness, awareness, and general at-home health, with a note that audio '
    'is subpar versus normal episodes. Guest slug spencer-hicks is EXISTING (0088 + 0074 + 0059 + 0044); this episode is appended. '
    'Inventory has_quotes=no / has_timestamps=no / has_hashtags=no / has_guest_links=no. Title conflict YT≠RSS (YouTube H1 preferred).'
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
    "Speaker map: pause-gap segmentation + sticky Jacob/Spencer content scoring (named speaker labels not present in captions; auto diarization imperfect); remote/video open forced to Jacob where clear\n"
    "Cleanup: light dedupe of consecutive duplicate words; merged consecutive same-speaker fragments; HTML entities/nbsp unescaped; capitalized turn starts after merge; light caption spacing tidy; light ASR name tidy (Spencer Hicks; Wim Hof; Jordan Hall; FaceTime; Xbox; The Witcher); bumper/outro forced to Jacob where clear; YouTube swear blanks normalized to ****\n"
    "No sentence rewriting.\n"
    f"Guest name spelling: Spencer Hicks (YT/RSS titles / inventory); slug {GUEST_SLUG} (EXISTING — APPEND 0038 to 0088+0074+0059+0044, do not wipe).\n"
    "Note: automatic diarization is imperfect; remaining short backchannels and some mid-turn blends may still be swapped in places. Remote COVID video chat from the open.\n"
    f"Issue: YouTube automatic captions (en/en-orig) used; no official/manual track; no >> speaker flips. YT duration {YT_DURATION_S}s vs RSS/inventory {DURATION_S}s (archive meta uses RSS duration). No published chapter timestamps. Title YT≠RSS (YouTube H1 preferred; keep YT spacing). About YT~itunes:summary (YT primary; (5) series marker stripped). Inventory has_quotes=no / has_timestamps=no / has_hashtags=no / has_guest_links=no. Archive picks fills timestamped quotes/chapters/keywords/hashtags/bio. Guest page: {GUEST_SLUG} (EXISTING APPEND).\n"
    f"Speaker balance: Jacob {balance.get('Jacob',0)} turns/{words_by.get('Jacob',0)} words; Spencer {balance.get('Spencer',0)} turns/{words_by.get('Spencer',0)} words.\n"
    f"Heuristic speaker fixes: {len(fixes)}; post-splits: {len(post_fixes)} ({'; '.join(post_fixes)})\n",
    encoding='utf-8',
)

(CONTENT / 'SOURCES.txt').write_text(
    "Description source: YouTube primary per archive rules; About spaced from YT plain description (~itunes:summary). YT footer stripped. No guest contact/email.\n"
    f"YouTube chars: {len(yt_desc.strip())}\n"
    f"RSS HTML chars: {len(rss_html.strip())}\n"
    f"Title source: YouTube / exact_public_title ({VIDEO_ID}). YT≠RSS — prefer YouTube H1; keep YT spacing.\n"
    f"Title: {TITLE}\n"
    f"RSS title: {RSS_TITLE}\n"
    "Chapters source: none published in episode notes (inventory has_timestamps=no); no YT chapters\n"
    "Guest links: none published (inventory has_guest_links=no)\n"
    f"Quotes: {len(published_quotes)} published quotes (inventory has_quotes=no)\n"
    "Hashtags: none published (inventory has_hashtags=no)\n"
    "About: Jacob published description verbatim as spaced paras from YouTube\n"
    f"Guest name spelling: Spencer Hicks; guest slug {GUEST_SLUG} (EXISTING — APPEND 0038; prior 0088+0074+0059+0044 preserved)\n"
    f"Duration: RSS itunes:duration {DURATION_S}s ({DURATION_HUMAN}); YT info.json duration {YT_DURATION_S}s — using RSS/inventory {DURATION_S}\n"
    "Publish date: RSS/inventory 2020-04-26 (YT upload_date 20200427)\n"
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

ld_keywords = keywords + ', Spencer Hicks, at-home health, Jacob Rhines, Junkyard Love Podcast'
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
<p class="note">From YouTube automatic captions; light cleanup; speaker labels via imperfect auto diarization (Jacob/Spencer may be swapped in places). Remote COVID video chat from the open.</p>
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

# Guest page EXISTS (0088 + 0074 + 0059 + 0044) — APPEND 0038 (do not wipe)
guest_dir = SITE / 'guests' / GUEST_SLUG
guest_dir.mkdir(parents=True, exist_ok=True)
bio_html = '\n'.join(f'<p>{escape(p)}</p>' for p in about_paras)

# Preserve prior episode about snippets from existing page when present
about_0088 = '<p>&quot;Spencer Hicks, Bachelor in arts of strategic communication; studies semiotics, enjoyed Hegelian dialectics and eats from the trash can of ideology.&quot;</p>'
about_0074 = '<p>Spencer is an armchair philosopher with focus in metaphysics, political philanthropy, ethics, and epistemology.</p>'
about_0059 = '<p>An important series introduction is presented in the form of a short audio essay that exists in the first ten minutes of this episode. I encourage you to listen for a better understanding of what to expect.</p>'
about_0044 = (
    '<p>I am joined by my friend Spencer Hicks, personal trainer, and we discuss varying self-development and health topics - including inflammation, obesity, self-sovereignty, exploring varying world-views and the shoes that fit them, questioning our own ideas, improving our knowledge and emotional database, enhancing conversations, becoming aware of our thoughts and deflecting discomfort.</p>\n'
    '<p>We tip the iceberg of a much larger conversation on the art of rhetoric and the current protests amidst the overarching world situation - fueled by the misleading media propaganda machine.</p>\n'
    '<p>We talk about conspiracy theories, humanities classes, government corruption, some thought experiments and personal observations for the future of humanity, some ways to navigate difficult conversations, Neuralink, wealth gaps, and remaining faithful and optimistic for the future of civilization.</p>\n'
    '<p>A hopeful contribution to the bigger conversation and larger view - enjoy episode 044.</p>'
)
existing_guest = guest_dir / 'index.html'
if existing_guest.exists():
    old = existing_guest.read_text(encoding='utf-8')
    for ep_label, key in [
        ('0088', 'Bachelor in arts'),
        ('0074', 'armchair philosopher'),
        ('0059', 'series introduction'),
        ('0044', 'personal trainer'),
    ]:
        m = re.search(
            rf'<h3>Episode {ep_label}</h3>\s*<div class="about">\s*(.*?)\s*</div>',
            old, re.S,
        )
        if m and key.split()[0].lower() in m.group(1).lower():
            snippet = m.group(1).strip()
            if ep_label == '0088':
                about_0088 = snippet
            elif ep_label == '0074':
                about_0074 = snippet
            elif ep_label == '0059':
                about_0059 = snippet
            else:
                about_0044 = snippet

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
<p class="note">Appeared on The Junkyard Love Podcast (5 episodes)</p>
<h2>Episodes</h2>
<ul class="list">
  <li><a href="../../episodes/0088-spencer-hicks-break-the-hammer/index.html">The JYLP ep. 088 with Bachelor In Arts Of Strategic Communication Spencer Hicks - Break The Hammer</a><br><span class="note">2022-08-02 · Episode 0088</span></li>
  <li><a href="../../episodes/0074-spencer-hicks-dialectics-and-communication-breakdown/index.html">Ep 074 w/ Spencer Hicks - Dialectics and Communication Breakdown - A Meta-Analysis of Cancel Culture</a><br><span class="note">2021-07-15 · Episode 0074</span></li>
  <li><a href="../../episodes/0059-spencer-hicks-the-sense-making-sickness-series-part-1/index.html">Episode 059 - The Sense Making Sickness - with Spencer Hicks - Series Part 1</a><br><span class="note">2020-10-20 · Episode 0059</span></li>
  <li><a href="../../episodes/0044-spencer-hicks-operating-optimally-should-be-your-goal/index.html">Episode 044 with Spencer Hicks - Operating Optimally Should Be Your Goal</a><br><span class="note">2020-06-10 · Episode 0044</span></li>
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

# Insert after 0039 (descending: 0039 then 0038)
marker_home = (
    '  <li><a href="episodes/0039-erik-nordin-of-rosetan-a-small-town-sound-with-heart/index.html">'
    'Episode 039 with Erik Nordin of Rosetan - A Small Town Sound With Heart</a>'
    '<br><span class="note">2020-05-10 · Erik Nordin · 1:18:21</span></li>\n'
)
marker_ep = (
    '  <li><a href="episodes/0039-erik-nordin-of-rosetan-a-small-town-sound-with-heart/index.html">'
    'Episode 039 with Erik Nordin of Rosetan - A Small Town Sound With Heart</a>'
    '<br><span class="note">Episode 0039 · 2020-05-10 · 1:18:21 · Guest: Erik Nordin</span></li>\n'
)

home = (SITE / 'index.html').read_text(encoding='utf-8')
if EP_SLUG not in home:
    if marker_home not in home:
        raise SystemExit('home 0039 marker not found')
    home = home.replace(marker_home, marker_home + home_li)
    (SITE / 'index.html').write_text(home, encoding='utf-8')

ep_index = (SITE / 'episodes' / 'index.html').read_text(encoding='utf-8')
if EP_SLUG not in ep_index:
    if marker_ep not in ep_index:
        raise SystemExit('ep index 0039 marker not found')
    ep_index = ep_index.replace(marker_ep, marker_ep + ep_li)
    (SITE / 'episodes' / 'index.html').write_text(ep_index, encoding='utf-8')

# Guest EXISTS — already on guests index (spencer-hicks); do not re-insert

sm = (SITE / 'sitemap.xml').read_text(encoding='utf-8')
if EP_SLUG not in sm:
    insert = (
        f'  <url><loc>{SITE_BASE}/episodes/{EP_SLUG}/</loc></url>\n'
        f'  <url><loc>{SITE_BASE}/episodes/{EP_SLUG}/episode.md</loc></url>\n'
    )
    m39 = f'  <url><loc>{SITE_BASE}/episodes/0039-erik-nordin-of-rosetan-a-small-town-sound-with-heart/episode.md</loc></url>\n'
    if m39 not in sm:
        raise SystemExit('sitemap 0039 marker not found')
    sm = sm.replace(m39, m39 + insert)
    (SITE / 'sitemap.xml').write_text(sm, encoding='utf-8')
# Guest already in sitemap (spencer-hicks)

llms = (SITE / 'llms.txt').read_text(encoding='utf-8')
if EP_SLUG not in llms:
    ep_line = (
        f'- [0038 Spencer Hicks — Mental and Physical Tips To Maintain Health At Home]'
        f'({SITE_BASE}/episodes/{EP_SLUG}/) — {DATE}\n'
    )
    m39_line = (
        f'- [0039 Erik Nordin — A Small Town Sound With Heart]'
        f'({SITE_BASE}/episodes/0039-erik-nordin-of-rosetan-a-small-town-sound-with-heart/) — 2020-05-10\n'
    )
    if m39_line not in llms:
        raise SystemExit('llms 0039 ep line not found')
    llms = llms.replace(m39_line, m39_line + ep_line)
    md_line = f'- [{SITE_BASE}/episodes/{EP_SLUG}/episode.md]({SITE_BASE}/episodes/{EP_SLUG}/episode.md)\n'
    m39_md = (
        f'- [{SITE_BASE}/episodes/0039-erik-nordin-of-rosetan-a-small-town-sound-with-heart/episode.md]'
        f'({SITE_BASE}/episodes/0039-erik-nordin-of-rosetan-a-small-town-sound-with-heart/episode.md)\n'
    )
    if m39_md in llms and md_line not in llms:
        llms = llms.replace(m39_md, m39_md + md_line)
    (SITE / 'llms.txt').write_text(llms, encoding='utf-8')
# Guest already listed in llms

readme = (ROOT / 'README.md').read_text(encoding='utf-8')
if EP_SLUG not in readme and '**0038**' not in readme:
    marker = (
        '- **0039** Erik Nordin — A Small Town Sound With Heart — '
        '`site/episodes/0039-erik-nordin-of-rosetan-a-small-town-sound-with-heart/`\n'
    )
    add = (
        '- **0038** Spencer Hicks — Mental and Physical Tips To Maintain Health At Home — '
        '`site/episodes/0038-spencer-hicks-mental-and-physical-tips-to-maintain-health-at-home/`\n'
    )
    if marker not in readme:
        raise SystemExit('README 0039 marker not found')
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
    # also sync build script into deploy _sources if that pattern exists
    if (DEPLOY / '_sources').exists():
        shutil.copy(ROOT / 'build_0038.py', DEPLOY / '_sources' / 'build_0038.py')
    print('deploy synced (no commit/push)')

print('DONE')
print('slug', EP_SLUG)
print('guest', GUEST_SLUG, 'EXISTING APPEND — episodes after update: 0088, 0074, 0059, 0044, 0038')
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
print('Around early conversation:')
for ms, sp, tx in turns:
    if 0 <= ms <= 200000:
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
