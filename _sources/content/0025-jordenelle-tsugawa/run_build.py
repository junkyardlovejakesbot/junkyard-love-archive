#!/workspace/.venv/bin/python3
"""Process Junkyard Love episode 0025 — Jordenelle Tsugawa (single guest, APPEND).
YT=RSS: titles match exactly ("Episode 025 with Jordenelle Tsugawa").
Inventory has_quotes=yes (inline “ok ego…” / YOU ARE ENOUGH; no Quotes list block),
has_timestamps=no, has_guest_links=no, has_hashtags=no.
Guest slug: jordenelle-tsugawa (EXISTS from 0096+0050 — APPEND 0025, do not wipe).
YouTube has NO captions/auto-captions for BRKmGl5XGVA — transcript from faster-whisper
ASR on downloaded audio (tiny/int8), exported as source-yt.en*.vtt/json3; flag imperfect diarization.
Archive picks required. No guest contact/email.
Insert indexes after 0026."""
from __future__ import annotations
import json, re, shutil
from pathlib import Path
from html import escape, unescape
from collections import Counter

ROOT = Path('/workspace/junkyard-love-archive')
CONTENT = ROOT / 'content/0025-jordenelle-tsugawa'
SITE = ROOT / 'site'
DEPLOY = Path('/workspace/junkyard-love-archive-deploy')
EP_SLUG = '0025-jordenelle-tsugawa'
GUEST_SLUG = 'jordenelle-tsugawa'
TITLE = 'Episode 025 with Jordenelle Tsugawa'
RSS_TITLE = TITLE
YT_TITLE = TITLE
TITLE_CONFLICT = 'YT=RSS'
GUEST = 'Jordenelle Tsugawa'
YOUTUBE = 'https://www.youtube.com/watch?v=BRKmGl5XGVA'
RSS_URL = 'https://share.transistor.fm/s/76e14b5a'
AUDIO_URL = 'https://2.gum.fm/op3.dev/e/pdcn.co/e/pscrb.fm/rss/p/pdst.fm/e/dts.podtrac.com/redirect.mp3/media.transistor.fm/76e14b5a/02080033.mp3'
DATE = '2020-02-18'
DURATION_S = 8469  # RSS / inventory
YT_DURATION_S = 8499
EP_NUM = '0025'
EP_INT = 25
SPK = 'Jordenelle'
SPOTIFY = 'https://open.spotify.com/show/45J7CBdM8j29doqyBp2bFs'
APPLE = 'https://podcasts.apple.com/us/podcast/the-junkyard-love-podcast/id1489118788'
SITE_BASE = 'https://junkyardlovejakesbot.github.io/junkyard-love-archive'
VIDEO_ID = 'BRKmGl5XGVA'

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
yt_desc = yt_raw.strip() + '\n'
if not (CONTENT / 'source-rss-description.txt').exists():
    raise SystemExit('missing source-rss-description.txt')
rss_plain = (CONTENT / 'source-rss-description.txt').read_text(encoding='utf-8').strip() + '\n'
rss_html = (CONTENT / 'source-rss-description.html').read_text(encoding='utf-8') if (CONTENT / 'source-rss-description.html').exists() else ''
(CONTENT / 'source-youtube-title.txt').write_text(TITLE + '\n', encoding='utf-8')
(CONTENT / 'source-youtube-raw.txt').write_text(yt_raw if yt_raw.endswith('\n') else yt_raw + '\n', encoding='utf-8')
(CONTENT / 'yt-meta.txt').write_text(
    f'title={YT_TITLE}\nupload_date=20200218\nduration={YT_DURATION_S}\nvideo_id={VIDEO_ID}\n'
    f'rss_title={RSS_TITLE}\ntitle_conflict={TITLE_CONFLICT}\nh1={TITLE}\n',
    encoding='utf-8',
)

# ---------- ABOUT from YT/RSS (identical body; strip YT footer) ----------
yt_body = yt_desc
for marker in ['\nThe Junkyard Love Podcast', '\n\u2605 Episode details', '\n\u2605 Additional episodes']:
    idx = yt_body.find(marker)
    if idx >= 0:
        yt_body = yt_body[:idx]
yt_body = yt_body.strip()
# Prefer RSS plain if lengths match after strip (same Jacob copy)
if rss_plain.strip() and abs(len(rss_plain.strip()) - len(yt_body)) < 5:
    about_src = rss_plain.strip()
else:
    about_src = yt_body

# inventory has_quotes=yes — inline “ok ego…” + YOU ARE ENOUGH kept in About; no Quotes list block
published_quotes: list[str] = []
inline_quote_bits = [
    'YOU ARE ENOUGH - we both agree!',
    '"ok ego, i hear you. but where\'s my soul?" (epic soundbyte!)',
]

# Soft-split single published block into spaced paras (verbatim Jacob copy)
soft_breaks = [
    'We talk all things Energy',
    'We cover growing up in small towns',
    'Jay opens it up with the chakras',
    'We expand on the mental connection',
    'Jay and I talk about self-love',
    'We talk about the gap that the internet',
    'Jay tells us about Forest Bathing',
    'She recently moved into a TINY home',
    'She shares how she actualizes',
    'YOU ARE ENOUGH',
    'We break down words like',
    'We share a few experiences',
    'Soul is love fear is ego',
    'She tells me about her Full Moon Circle',
    'We shed some light on living',
    "I love Jay's way of seeing",
    'I see those of her personality',
    'Her type keeps us connected',
    "Someone who doesn't let us forget",
    'If your life ever leads you',
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
    about_paras = [about_src]

(CONTENT / 'source-description.raw.txt').write_text(about_src + '\n', encoding='utf-8')

# inventory has_guest_links=no
guest_links: list[str] = []

about_md = '\n\n'.join(about_paras) + '\n'
quotes_md_lines = [
    '(none published as a Quotes list block — inventory has_quotes=yes from inline '
    '“YOU ARE ENOUGH” and “ok ego, i hear you. but where\'s my soul?” kept verbatim in About)'
]
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
    f'Title conflict: {TITLE_CONFLICT}\nGuest slug: {GUEST_SLUG} (EXISTS — APPEND 0096+0050)\n'
    f'About: YT~RSS identical body; YT footer stripped; no guest contact/email\n'
    f'Transcript: YouTube has NO captions — faster-whisper ASR fallback\n',
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
        r'^(Well,? (?:I|so|yeah|we)|Yeah,? (?:so|I|and|we)|So,? (?:I|we|when|in|the|my)|I (?:think|was|love|want|had|grew|got|mean|have|always|feel|set|deserve)|We (?:are|were|have|had|just)|Absolutely|Thank you|Okay|Yes|Right|For me|My (?:intention|table|hands)|Um,? (?:I|so|yeah)|No problem|Okay so)',
        text.strip(), re.I))
    starts_jacob = bool(re.match(
        r'^(Hello|Welcome|Well,? so|So,? (?:let\'s|what|um|Jay|Jordenelle)|Junkyard|Thank you|Yeah,? yeah|Wave|Peace out|Knowledge is|Reality is|At what age|Listeners|Cool so|What.?s up|Check it out|Drink some|50 episodes|Now here.?s episode)',
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
        (r'\bjordan now tsugawa\b', 'Jordenelle Tsugawa'),
        (r'\bjordenelle\b', 'Jordenelle'),
        (r'\btsugawa\b', 'Tsugawa'),
        (r'\bforest bathing\b', 'Forest Bathing'),
        (r'\btiny home\b', 'tiny home'),
        (r'\bfull moon circle\b', 'Full Moon Circle'),
        (r'\btsugawa\b', 'Tsugawa'),
        (r'\bjordan l\b', 'Jordenelle'),
        (r'\breiki\b', 'Reiki'),
        (r'\bstarseed\b', 'starseed'),
        (r'\bchakras\b', 'chakras'),
        (r'\bchakra\b', 'chakra'),
        (r'\bmurray hidary\b', 'Murray Hidary'),
        (r'\bmindtravel\b', 'MindTravel'),
        (r'\bmind travel\b', 'MindTravel'),
        (r'\bcelestial_gypsy_witch\b', 'celestial_gypsy_witch'),
        (r'\bcelestial gypsy witch\b', 'celestial gypsy witch'),
        (r'\btwin flames\b', 'twin flames'),
        (r'\btwin flame\b', 'twin flame'),
        (r'\bjake rynes\b', 'Jake Rhines'),
        (r'\bjacob rhines\b', 'Jacob Rhines'),
        (r'\bjunkyard love podcast\b', 'Junkyard Love Podcast'),
        (r'\bjunkyard love\b', 'Junkyard Love'),
        (r'\byoutube\b', 'YouTube'),
        (r'\bspotify\b', 'Spotify'),
        (r'\binstagram\b', 'Instagram'),
        (r'\bcovid\b', 'COVID'),
        (r'\bwikipedia\b', 'Wikipedia'),
    ]
    for pat, rep in reps:
        text = re.sub(pat, rep, text, flags=re.I)
    return text


def score_jacob(text):
    tlow = text.lower()
    s = 0
    for pat in [
        r'\bjunkyard\b', r'\bwelcome to the (?:junkyard )?podcast\b',
        r'\b50 episodes\b', r'\b50th episode\b', r'\bfirst 50\b',
        r'\bdrink (?:some )?(?:dang )?water\b', r'\blove yourself\b', r'\bpeace out\b',
        r'\btake care of yourself\b', r'\blisteners\b',
        r'\bjacob from the internet\b', r'\bjake rhines\b',
        r'\bget present\b', r'\bmy first reiki session\b',
        r'\bhere.?s episode 50\b', r'\bjordenelle tsugawa\b',
        r'\bbelieve in your damn self\b', r'\bhere.?s your permission\b',
        r'\bwhat is art to you jay\b', r'\bthank you jay\b',
    ]:
        if re.search(pat, tlow):
            s += 4
    if re.search(r'\b(?:jay|you)\b', tlow) and ('?' in text or re.search(r'\byou (?:feel|think|said|mentioned|been)\b', tlow)):
        s += 3
    if '?' in text and len(text.split()) < 90:
        s += 2
    if len(text.split()) <= 12 and re.search(
        r'^(yeah|yes|right|okay|ok|cool|love it|mhm|mm+|exactly|wow|dude|man|perfect|great|beautiful|thanks|you bet|interesting)\b', tlow):
        s += 2
    if re.search(r'\byou (?:guys|mentioned|said|feel|think|know|been)\b', tlow):
        s += 2
    return s


def score_jordenelle(text):
    tlow = text.lower()
    s = 0
    for pat in [
        r'\bchakras?\b', r'\bherbal(?:ism|ist)?\b', r'\bforest bath(?:ing)?\b',
        r'\btiny home\b', r'\bgrounding\b', r'\bmeditation\b', r'\bvisualization\b',
        r'\bintuition\b', r'\btrigger\b', r'\bsynchronicity\b', r'\bfull moon\b',
        r'\bego\b', r'\bsoul\b', r'\benergy\b', r'\bheal(?:ing|er|ers)?\b',
        r'\balcohol\b', r'\bmantra\b', r'\baffirmation\b', r'\bempath(?:ic|y)?\b',
        r'\bi (?:moved into|live in|quit|practice)\b',
        r'\bmy (?:tiny home|full moon|circle|intuition)\b',
        r'\byou are enough\b', r'\bok ego\b',
    ]:
        if re.search(pat, tlow):
            s += 5
    if re.search(r'\bi (?:was|had|grew|got|did|started|think|feel|have|went|lived|always|work|don.?t|would say)\b', tlow) and len(text.split()) > 40:
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
    sg = score_jordenelle(text)

    # Host bumper (~first ~90s) forced to Jacob when clear host cues
    if ms < 90000 and re.search(r'junkyard love|hello and welcome|drink some|get present|recommendation|posture|diaphragm', text.lower()):
        sp = 'Jacob'
    elif sj > sg + 1:
        sp = 'Jacob'
    elif sg > sj + 1:
        sp = 'Jordenelle'
    else:
        if sj > sg:
            sp = 'Jacob'
        elif sg > sj:
            sp = 'Jordenelle'
        else:
            if len(text.split()) <= 8:
                sp = 'Jordenelle' if prev == 'Jacob' else 'Jacob'
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
    if ms < 758000:
        sp = 'Jacob'
    if ms < 120000 and re.search(r'junkyard love|hello and welcome|jordenelle|drink some|get present', low):
        sp = 'Jacob'
    if re.search(r'i set up my table|ancient japanese style|universal energy to flow|i.?m teaching you how to heal|starseed|copper water|celestial gypsy|onto whatever i.?m like|putting my energy into|you feel good i feel good|addicting thing for me|i.?m getting it too|twitching in my hands|i literally physically could feel|cut like a part of a flower|hundred hands|thousand hands|i drink copper water|movement is like dancing|especially being a starseed|i deserve to be here|just forgive it', low):
        sp = 'Jordenelle'
    if re.search(r'drink (?:some )?(?:dang )?water|see you (?:guys )?next|peace out|get present|listeners (?:drink|please|get)|hello and welcome to the junkyard|listeners please|knowledge is power', low):
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
    r'(.*(?:explain|what just happened|teach me))\s+(.*(?:i set up my table|basically i set|reiki session|universal energy).*)',
    'Jacob', 'Jordenelle', 'split Jacob ask / Jordenelle Reiki')
split_on(
    r'(.*(?:what is art to you jay|what is art))\s+(.*(?:art is|for me art|i think art|creation).*)',
    'Jacob', 'Jordenelle', 'split Jacob ask / Jordenelle art')

rescored = []
for i, (ms, sp, tx) in enumerate(turns):
    low = tx.lower()
    sj = score_jacob(tx)
    sg = score_jordenelle(tx)
    if ms < 758000:
        sp = 'Jacob'
    elif re.search(r'junkyard love podcast|drink some|get present|hello and welcome|listeners please|peace out|knowledge is power', low):
        sp = 'Jacob'
    elif re.search(r'i set up my table|ancient japanese|universal energy to flow|starseed|copper water|celestial gypsy witch|i deserve to be here|onto whatever i.?m like|putting my energy into|you feel good i feel good|addicting thing for me|twitching in my hands|i drink copper water|movement is like dancing|just forgive it', low):
        sp = 'Jordenelle'
    elif sj > sg + 2:
        sp = 'Jacob'
    elif sg > sj + 2:
        sp = 'Jordenelle'
    if ms >= DURATION_S * 1000 - 120000 and re.search(r'peace out|junkyard|drink some|listeners|get present|enjoy your (?:day|life)|celestial gypsy', low):
        if re.search(r'celestial gypsy|get a hold of jay', low) and not re.search(r'listeners drink|get present', low):
            sp = 'Jordenelle'
        elif re.search(r'listeners|drink some|get present|enjoy your', low):
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
    ('chakra', 'Jordenelle'),
    ('forest bathing', 'Jordenelle'),
    ('tiny home', 'Jordenelle'),
    ('you are enough', None),
    ('ok ego', 'Jordenelle'),
    ("where's my soul", 'Jordenelle'),
    ('intuition', 'Jordenelle'),
    ('trigger', 'Jordenelle'),
    ('herbal', 'Jordenelle'),
    ('grounding', 'Jordenelle'),
    ('meditation', 'Jordenelle'),
    ('visualization', 'Jordenelle'),
    ('full moon', 'Jordenelle'),
    ('alcohol', 'Jordenelle'),
    ('synchronicity', None),
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
            label = 'Opening — Junkyard Love / Jordenelle'
        aid = anchor_id_s(s)
        if aid in used:
            continue
        used.add(aid)
        chapters.append((s, label))
else:
    chapter_needles = [
        (10, 'hello and welcome', 'Opening bumper — Junkyard Love'),
        (90, 'jordenelle', 'Introduce Jordenelle / Jay'),
        (300, 'chakra', 'Chakras / energy body'),
        (900, 'herbal', 'Herbalism / natural healing'),
        (1500, 'grounding', 'Grounding / connection'),
        (2100, 'meditation', 'Meditation / visualization'),
        (2700, 'self love', 'Self-love / becoming truest self'),
        (3300, 'trauma', 'Trauma / generational experiences'),
        (3900, 'forest bathing', 'Forest bathing / nature healing'),
        (4500, 'tiny home', 'Tiny home living'),
        (5100, 'you are enough', 'YOU ARE ENOUGH'),
        (5700, 'intuition', 'Trigger / intuition / gossip'),
        (6300, 'synchronicity', 'Synchronicity / empathic story'),
        (6900, 'ego', 'Soul is love / fear is ego'),
        (7500, 'full moon', 'Full Moon Circle / alcohol'),
        (8000, 'community', 'Community / glass table / close'),
        (None, 'drink some water', 'Outro — drink water / get present'),
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
            if best and best[0] < 240:
                s = best[1]
        else:
            last = None
            for ms, sp2, t2 in turns:
                if needle.lower() in t2.lower():
                    last = (ms / 1000.0, sp2, t2)
            if last:
                s = last[0]
        aid = anchor_id_s(s)
        if aid in used:
            continue
        used.add(aid)
        chapters.append((s, label))
    chapters.sort(key=lambda x: x[0])

keywords = (
    'Jordenelle Tsugawa, Episode 025 with Jordenelle Tsugawa, '
    'Junkyard Love Podcast episode 0025, JYLP 0025, chakras, herbalism, '
    'energy, grounding, meditation, visualization, self-love, forest bathing, '
    'tiny home, intuition, synchronicity, Full Moon Circle, Jacob Rhines, Jay'
)
hashtags = (
    '#JordenelleTsugawa #JYLP0025 #JunkyardLove #Chakras #Herbalism '
    '#SelfLove #ForestBathing #TinyHome #Meditation #JYLP'
)
guest_bio = (
    'Jordenelle Tsugawa (Jay) appears on Junkyard Love episode 0025 as a natural healer and '
    'soon-to-be herbalist — Jacob\'s notes call her a mystical knowledge-base of divine love, '
    'openhearted tiny-home forest-dweller. The conversation covers energy, herbalism, chakras, '
    'grounding, meditation, visualization, self-love and growth; small-town upbringing; alcohol '
    'and family trauma; forest bathing; tiny-home living; planners/mantras/affirmations; '
    '"YOU ARE ENOUGH"; trigger vs intuition; synchronicity; Full Moon Circle; and the soundbite '
    '"ok ego, i hear you. but where\'s my soul?" Inventory has_quotes=yes / has_timestamps=no / '
    'has_hashtags=no / has_guest_links=no. No guest contact/email in published notes for 0025. '
    'Also appeared later on 0050 and 0096 (same guest slug).'
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
    "Speaker map: pause-gap segmentation + sticky Jacob/Jordenelle content scoring (named speaker labels not present in ASR; auto diarization imperfect); host bumper forced to Jacob when clear\n"
    "Cleanup: light dedupe of consecutive duplicate words; merged consecutive same-speaker fragments; HTML entities/nbsp unescaped; capitalized turn starts after merge; light caption spacing tidy; light ASR name tidy (Jordenelle; Tsugawa; Reiki; chakra(s); Murray Hidary; MindTravel; celestial gypsy witch; Jake Rhines); bumper/outro forced to Jacob where clear; YouTube swear blanks normalized to ****\n"
    "No sentence rewriting.\n"
    "Guest name spelling: Jordenelle Tsugawa (YT/RSS titles / inventory); about also uses Jay; slug jordenelle-tsugawa (EXISTS from 0096 — APPEND).\n"
    "Note: automatic diarization is imperfect; remaining short backchannels and some mid-turn blends may still be swapped in places.\n"
    f"Issue: YouTube had NO captions/auto-captions for {VIDEO_ID}; transcript from faster-whisper tiny/int8 ASR on downloaded audio (exported as source-yt.en*.vtt/json3). YT duration {YT_DURATION_S}s vs RSS/inventory {DURATION_S}s (archive meta uses RSS duration). No published chapter timestamps; no YT chapters. Title {TITLE_CONFLICT}. About YT~RSS identical body (footer stripped). Inventory has_quotes=yes (inline YOU ARE ENOUGH / ok-ego soundbite in About; no Quotes list) / has_timestamps=no / has_hashtags=no / has_guest_links=no. Archive picks fills timestamped quotes/chapters/keywords/hashtags/bio. Guest page: jordenelle-tsugawa (APPEND prior 0096+0050).\n"
    f"Speaker balance: Jacob {balance.get('Jacob',0)} turns/{words_by.get('Jacob',0)} words; Jordenelle {balance.get('Jordenelle',0)} turns/{words_by.get('Jordenelle',0)} words.\n"
    f"Heuristic speaker fixes: {len(fixes)}; post-splits: {len(post_fixes)} ({'; '.join(post_fixes)})\n",
    encoding='utf-8',
)

(CONTENT / 'SOURCES.txt').write_text(
    "Description source: YT~RSS identical About body (YT footer stripped). Soft-split into spaced paras; inline quotes kept in About. No guest contact/email.\n"
    f"YouTube chars: {len(yt_desc.strip())}\n"
    f"RSS HTML chars: {len(rss_html.strip())}\n"
    f"Title source: YT=RSS exact match ({VIDEO_ID}). H1/slug use Episode 025 with Jordenelle Tsugawa. {TITLE_CONFLICT}.\n"
    f"Title: {TITLE}\n"
    f"RSS title: {RSS_TITLE}\n"
    "Chapters source: none published in episode notes (inventory has_timestamps=no); no YT chapters\n"
    "Guest links: none published for 0025 (inventory has_guest_links=no); prior appearances keep Instagram handles on guest page\n"
    "Quotes: no dedicated Quotes list block (inventory has_quotes=yes from inline YOU ARE ENOUGH / ok-ego soundbite kept in About)\n"
    "Hashtags: none published (inventory has_hashtags=no)\n"
    "About: Jacob published description verbatim as spaced paras from YouTube (quotes section stripped to Quotes)\n"
    "Guest name spelling: Jordenelle Tsugawa; guest slug jordenelle-tsugawa (EXISTS — APPEND 0096); About also uses Jay\n"
    f"Duration: RSS itunes:duration {DURATION_S}s ({DURATION_HUMAN}); YT info.json duration {YT_DURATION_S}s — using RSS/inventory {DURATION_S}\n"
    "Publish date: RSS/inventory 2020-07-31 (YT upload_date 20200731)\n"
    "Archive picks: added (timestamped transcript quotes, chapter-style timestamps, keywords/hashtags, short guest bio) — extracted from YT auto-caption transcript + published About; kept separate from Jacob published About/Chapters/Quotes.\n"
    "Captions: YouTube none — ASR via faster-whisper tiny/int8 → source-yt.en*.vtt/json3 (also mirrored as en-orig).\n",
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

about_html = '\n'.join(f'<p>{escape(p)}</p>' for p in about_paras)
quotes_html = (
    '<p class="note">(none published as a Quotes list block — inline YOU ARE ENOUGH and ok-ego soundbite kept in About)</p>'
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

ld_keywords = keywords + ', Jordenelle Tsugawa, Jacob Rhines, Junkyard Love Podcast'
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
<p class="note">YouTube had no captions for this upload — transcript from faster-whisper ASR on episode audio; light cleanup; speaker labels via imperfect auto diarization (Jacob/Jordenelle may be swapped in places).</p>
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

bio_html = '\n'.join(f'<p>{escape(p)}</p>' for p in about_paras)

# Guest page EXISTS (0096 + 0050) — APPEND 0025 (do not wipe)
guest_dir = SITE / 'guests' / GUEST_SLUG
guest_dir.mkdir(parents=True, exist_ok=True)
existing_guest = guest_dir / 'index.html'
old = existing_guest.read_text(encoding='utf-8') if existing_guest.exists() else ''

def extract_about_section(html: str, heading: str) -> str:
    m = re.search(
        rf'<h3>{re.escape(heading)}</h3>\s*<div class="about">\s*(.*?)\s*</div>',
        html, re.S)
    return m.group(1).strip() if m else ''

about_0096 = extract_about_section(old, 'Episode 0096')
about_0050 = extract_about_section(old, 'Episode 0050')
if not about_0096:
    raise SystemExit('guest page missing Episode 0096 about — refuse wipe')
if not about_0050:
    raise SystemExit('guest page missing Episode 0050 about — refuse wipe')

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
<p class="note">Appeared on The Junkyard Love Podcast (3 episodes)</p>
<h2>Episodes</h2>
<ul class="list">
  <li><a href="../../episodes/0096-jordenelle-tsugawa-the-forever-umbilical-cord-and-grand-mother-ayahuasca/index.html">The JYLP ep 096 with Jordenelle Tsugawa - The Forever Umbilical Cord, And Grand-Mother Ayahuasca</a><br><span class="note">2023-02-09 · Episode 0096</span></li>
  <li><a href="../../episodes/0050-jordenelle-tsugawa-healing-the-soul-with-hands-and-self-love/index.html">Episode 050 with Starseed and Reiki Worker Jordenelle Tsugawa - Healing The Soul With Hands and S...</a><br><span class="note">2020-07-31 · Episode 0050</span></li>
  <li><a href="../../episodes/__SLUG__/index.html">__TITLE__</a><br><span class="note">__DATE__ · Episode __EPNUM__</span></li>
</ul>
<h2>From the episode notes</h2>
<p class="note">Copied from published episode descriptions (not a new biography).</p>
<h3>Episode 0096</h3>
<div class="about">
__ABOUT0096__
</div>
<h3>Episode 0050</h3>
<div class="about">
__ABOUT0050__
</div>
<h3>Episode __EPNUM__</h3>
<div class="about">
__BIO__
</div>
<h2>Guest links</h2>
<p class="note">From published notes across appearances.</p>
<ul class="links">
<li><a href="https://www.instagram.com/cosmic_merrmaid/">Instagram @cosmic_merrmaid</a> (episode 0096)</li>
<li>Instagram @celestial_gypsy_witch (episode 0050; published inline in About)</li>
</ul>

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
    .replace('__ABOUT0096__', about_0096)
    .replace('__ABOUT0050__', about_0050)
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

marker_home = (
    '  <li><a href="episodes/0026-scott-pisapia-of-roots-basketball-academy/index.html">'
    'Episode 026 with Scott Pisapia of Roots Basketball Academy</a>'
    '<br><span class="note">2020-02-24 · Scott Pisapia of Roots Basketball Academy · 2:28:20</span></li>\n'
)
marker_ep = (
    '  <li><a href="episodes/0026-scott-pisapia-of-roots-basketball-academy/index.html">'
    'Episode 026 with Scott Pisapia of Roots Basketball Academy</a>'
    '<br><span class="note">Episode 0026 · 2020-02-24 · 2:28:20 · Guest: Scott Pisapia of Roots Basketball Academy</span></li>\n'
)

home = (SITE / 'index.html').read_text(encoding='utf-8')
if EP_SLUG not in home:
    if marker_home not in home:
        raise SystemExit('home 0026 marker not found')
    home = home.replace(marker_home, marker_home + home_li)
    (SITE / 'index.html').write_text(home, encoding='utf-8')

ep_index = (SITE / 'episodes' / 'index.html').read_text(encoding='utf-8')
if EP_SLUG not in ep_index:
    if marker_ep not in ep_index:
        raise SystemExit('ep index 0026 marker not found')
    ep_index = ep_index.replace(marker_ep, marker_ep + ep_li)
    (SITE / 'episodes' / 'index.html').write_text(ep_index, encoding='utf-8')

guests_index = (SITE / 'guests' / 'index.html').read_text(encoding='utf-8')
if GUEST_SLUG not in guests_index:
    raise SystemExit('guest jordenelle-tsugawa missing from guests index')

sm = (SITE / 'sitemap.xml').read_text(encoding='utf-8')
if EP_SLUG not in sm:
    insert = (
        f'  <url><loc>{SITE_BASE}/episodes/{EP_SLUG}/</loc></url>\n'
        f'  <url><loc>{SITE_BASE}/episodes/{EP_SLUG}/episode.md</loc></url>\n'
    )
    m26 = f'  <url><loc>{SITE_BASE}/episodes/0026-scott-pisapia-of-roots-basketball-academy/episode.md</loc></url>\n'
    if m26 not in sm:
        raise SystemExit('sitemap 0026 marker not found')
    sm = sm.replace(m26, m26 + insert)
(SITE / 'sitemap.xml').write_text(sm, encoding='utf-8')

llms = (SITE / 'llms.txt').read_text(encoding='utf-8')
if EP_SLUG not in llms:
    ep_line = (
        f'- [0025 Jordenelle Tsugawa]'
        f'({SITE_BASE}/episodes/{EP_SLUG}/) — {DATE}\n'
    )
    m26_line = (
        f'- [0026 Scott Pisapia of Roots Basketball Academy]'
        f'({SITE_BASE}/episodes/0026-scott-pisapia-of-roots-basketball-academy/) — 2020-02-24\n'
    )
    if m26_line not in llms:
        raise SystemExit('llms 0026 ep line not found')
    llms = llms.replace(m26_line, m26_line + ep_line)
    md_line = f'- [{SITE_BASE}/episodes/{EP_SLUG}/episode.md]({SITE_BASE}/episodes/{EP_SLUG}/episode.md)\n'
    m26_md = (
        f'- [{SITE_BASE}/episodes/0026-scott-pisapia-of-roots-basketball-academy/episode.md]'
        f'({SITE_BASE}/episodes/0026-scott-pisapia-of-roots-basketball-academy/episode.md)\n'
    )
    if m26_md in llms and md_line not in llms:
        llms = llms.replace(m26_md, m26_md + md_line)
(SITE / 'llms.txt').write_text(llms, encoding='utf-8')

readme = (ROOT / 'README.md').read_text(encoding='utf-8')
if EP_SLUG not in readme and '**0025**' not in readme:
    marker = '- **0026** Scott Pisapia of Roots Basketball Academy — `site/episodes/0026-scott-pisapia-of-roots-basketball-academy/`\n'
    add = '- **0025** Jordenelle Tsugawa — `site/episodes/0025-jordenelle-tsugawa/`\n'
    if marker not in readme:
        raise SystemExit('README 0026 marker not found')
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
print('guest', GUEST_SLUG)
print('turns', len(turns), 'words', word_count)
print('about paras', len(about_paras))
print('published quotes', len(published_quotes))
print('quotes_ap', len(quotes_ap), 'archive_chapters', len(chapters))
print('balance', dict(balance), dict(words_by))
print('About paras:')
for i, para in enumerate(about_paras):
    print(f'  [{i}] {para[:160]}')
print('Published quotes:')
for q in published_quotes:
    print(f'  - {q[:100]}')
print('First 8:')
for ms, sp, tx in turns[:8]:
    print(f'[{ms_to_ts(ms)}] {sp:12s} {len(tx.split()):4d}w | {tx[:100]}')
print('Around guest entry:')
for ms, sp, tx in turns:
    if 740000 <= ms <= 900000:
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
print('RSS', RSS_TITLE)
