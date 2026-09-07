#!/usr/bin/env python3
"""Process Junkyard Love episode 0045 — Solo with Jacob Rhines (solocast).
YT≠RSS title (triple spaces on YT vs dashes on RSS). Prefer YouTube title for H1.
Inventory has_quotes=no, has_timestamps=no, has_guest_links=no, has_hashtags=no.
Solo: no guest page (mirror 0060). Archive picks required. Imperfect ASR flagged.
About from YT primary (verbatim Jacob; footer stripped; no guest contact/email)."""
from __future__ import annotations
import json, re, shutil
from pathlib import Path
from html import escape, unescape
from collections import Counter

ROOT = Path('/workspace/junkyard-love-archive')
CONTENT = ROOT / 'content/0045-solo-jacob-rhines-how-to-take-care-of-yourself-a-bit'
SITE = ROOT / 'site'
DEPLOY = Path('/workspace/junkyard-love-archive-deploy')
EP_SLUG = '0045-solo-jacob-rhines-how-to-take-care-of-yourself-a-bit'
# Prefer YouTube title for H1 when YT≠RSS (preserve triple spaces)
TITLE = 'Episode 045   Solo with Jacob Rhines   How To Take Care Of Yourself A Bit'
RSS_TITLE = 'Episode 045 - Solo with Jacob Rhines - How To Take Care Of Yourself A Bit'
YOUTUBE = 'https://www.youtube.com/watch?v=oE2Vxdn0U_I'
RSS_URL = 'https://share.transistor.fm/s/ef8ff2e1'
AUDIO_URL = 'https://2.gum.fm/op3.dev/e/pdcn.co/e/pscrb.fm/rss/p/pdst.fm/e/dts.podtrac.com/redirect.mp3/media.transistor.fm/ef8ff2e1/5b2a40b4.mp3'
DATE = '2020-06-18'
DURATION_S = 7828  # RSS / inventory / YT match
YT_DURATION_S = 7828
EP_NUM = '0045'
EP_INT = 45
SPOTIFY = 'https://open.spotify.com/show/45J7CBdM8j29doqyBp2bFs'
APPLE = 'https://podcasts.apple.com/us/podcast/the-junkyard-love-podcast/id1489118788'
SITE_BASE = 'https://junkyardlovejakesbot.github.io/junkyard-love-archive'
VIDEO_ID = 'oE2Vxdn0U_I'

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
    f'title={TITLE}\nupload_date=20200619\nduration={YT_DURATION_S}\nvideo_id={VIDEO_ID}\n',
    encoding='utf-8',
)

# ---------- ABOUT from YouTube (primary) ----------
yt_body = yt_desc
for marker in ['\nThe Junkyard Love Podcast', '\n\u2605 Episode details', '\n\u2605 Additional episodes']:
    idx = yt_body.find(marker)
    if idx >= 0:
        yt_body = yt_body[:idx]
yt_body = yt_body.strip()

# No guest contact/email to strip (solo). Keep Jacob CTA to comment on YT / share.

about_paras = [x.strip() for x in re.split(r'\n\s*\n', yt_body) if x.strip()]
expanded = []
for block in about_paras:
    parts = [ln.strip() for ln in block.split('\n') if ln.strip()]
    if len(parts) > 1 and all(len(pt) > 40 for pt in parts):
        expanded.extend(parts)
    else:
        expanded.append(block)
about_paras = expanded

# Soft-split long single About into readable paras at sentence boundaries (verbatim text)
if len(about_paras) == 1 and len(about_paras[0]) > 500:
    text = about_paras[0]
    soft_breaks = [
        'My intentions here are simply to help.',
        'I wish for all my listeners to feel clear',
        'I share my experiences with stretching',
        'As I tried to not dwell too far into subjects',
        'If you like this episode, please share',
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

published_quotes = []  # inventory has_quotes=no

about_md = '\n\n'.join(about_paras) + '\n'
quotes_md_lines = ['(none published in episode notes)']
(CONTENT / 'source-about.md').write_text(about_md, encoding='utf-8')
(CONTENT / 'source-quotes.md').write_text('\n'.join(quotes_md_lines) + '\n', encoding='utf-8')
(CONTENT / 'source-timestamps.md').write_text('(none published in episode notes)\n', encoding='utf-8')
(CONTENT / 'source-hashtags.txt').write_text('(none published in episode notes)\n', encoding='utf-8')
(CONTENT / 'source-links.md').write_text('(none published — solo)\n', encoding='utf-8')
(CONTENT / 'source-description.md').write_text(
    about_md + '\n## Quotes\n\n' + '\n'.join(quotes_md_lines) + '\n\n## Guest links\n\n(none published — solo)\n',
    encoding='utf-8',
)
(CONTENT / 'guest-share-draft.txt').write_text(
    f'Episode {EP_NUM}: {TITLE}\nSolo / host-only (Jacob Rhines)\nDate: {DATE}\nYouTube: {YOUTUBE}\nRSS: {RSS_URL}\n',
    encoding='utf-8',
)

# ---------- TRANSCRIPT (solo — all turns Jacob) ----------
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
    text = text.replace('[ __ ]', '****').replace('[ __ ]', '****')
    text = re.sub(r'\[\s*(?:__|  __  )\s*\]', '****', text)
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
    if gap >= GAP_HARD or (ended and gap >= GAP_SOFT) or (len(' '.join(parts).split()) > 140 and gap >= 1000):
        flush()
        cur_ms = t
    parts.append(text)
    prev_ms = t
    prev_text = text
flush()
atoms = [(ms, re.sub(r'\s+', ' ', tx).strip()) for ms, tx in atoms if tx]

def light_name_fix(text):
    reps = [
        (r'\bjacob ryan\'?s\b', 'Jacob Rhines'),
        (r'\bjacob rhines\b', 'Jacob Rhines'),
        (r'\bjake rhines\b', 'Jake Rhines'),
        (r'\bjake rynes\b', 'Jake Rhines'),
        (r'\bjacob from the internet\b', 'Jacob from the Internet'),
        (r'\bjunkyard love podcasts?\b', 'Junkyard Love Podcast'),
        (r'\bjunkyard love\b', 'Junkyard Love'),
        (r'\byoutube\b', 'YouTube'),
        (r'\bspotify\b', 'Spotify'),
        (r'\binstagram\b', 'Instagram'),
        (r'\bcovid\b', 'COVID'),
        (r'\badhd\b', 'ADHD'),
        (r'\bnofap\b', 'NoFap'),
        (r'\bpaleolithic\b', 'Paleolithic'),
        (r'\bhomeostasis\b', 'homeostasis'),
    ]
    for pat, rep in reps:
        text = re.sub(pat, rep, text, flags=re.I)
    return text

turns = []
for ms, text in atoms:
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
    turns.append((ms, 'Jacob', text))

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
turns = merge_turns(turns)

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
    ('constantly trying and failing', 'Jacob'),
    ('take care of yourself physically', 'Jacob'),
    ('reactive state', 'Jacob'),
    ('stretch and give them that morning yawn', 'Jacob'),
    ('feet touch the ground', 'Jacob'),
    ('breath work', 'Jacob'),
    ('screen time', 'Jacob'),
    ('great for inflammation', 'Jacob'),
    ('caffeine', 'Jacob'),
    ('pornography', 'Jacob'),
    ('monkey mind', 'Jacob'),
    ('alone time', 'Jacob'),
    ('setting boundaries', 'Jacob'),
    ('practice mindfulness', 'Jacob'),
    ('take care of yourself', 'Jacob'),
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
    (6, 'hello and welcome to the junkyard', 'Open — Junkyard Love bumper / knowledge is power'),
    (75, 'solo episode', 'Solo episode framing — general self-care notes'),
    (343, 'take care of yourself physically', 'Why take care of yourself — body & mind'),
    (540, 'habits had lined up', 'Habits / values / who you became'),
    (748, 'social media', 'Social media / comparison / Instagram'),
    (1138, 'reactive state', 'Reactive state / news & emotional hijack'),
    (1166, 'stretch and give them that morning yawn', 'Stretching / morning yawn / move your body'),
    (1307, 'feet touch the ground', 'Grounding — feet on the earth'),
    (1549, 'being weird', 'Being weird / stretching in public'),
    (1710, 'breathe breathe', 'Breath / breath work / yoga'),
    (1987, 'screen time', 'Screen time before bed / content'),
    (2131, 'grounding', 'Grounding / barefoot tips'),
    (2463, 'inflammation', 'Diet / inflammation / fasting'),
    (3162, 'caffeine', 'Caffeine awareness'),
    (4327, 'pornography', 'Pornography / NoFap / sexual urges'),
    (4617, 'monkey mind', 'Monkey mind / reptilian brain'),
    (6394, 'alone time', 'Alone time / solitude'),
    (6901, 'philosophy', 'Learning philosophy / ideas that change you'),
    (7533, 'setting boundaries', 'Boundaries / not staying reactive'),
    (None, 'practice mindfulness', 'Close — mindfulness / learn on YouTube / take care'),
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
    'Junkyard Love Podcast, JYLP 0045, Jacob Rhines, Jacob from the Internet, solocast, '
    'Solo with Jacob Rhines, How To Take Care Of Yourself A Bit, self-care, monkey mind, '
    'stretching, grounding, barefoot, breath work, yoga, screen time, diet, inflammation, '
    'caffeine, sleep, pornography, NoFap, social media, habits, values, boundaries, '
    'philosophy, mindfulness, alone time, reactive state, long form podcast'
)
hashtags = (
    '#JYLP0045 #JunkyardLove #Solocast #SelfCare #TakeCareOfYourself '
    '#MonkeyMind #Grounding #BreathWork #Mindfulness #Habits #Boundaries '
    '#JYLP #JacobFromTheInternet'
)
episode_framing = (
    'Solo episode (no guest). Jacob sits with scribbled notes for a general self-care solocast — '
    'ways to feel better and get control of monkey minds. Topics span stretching, environment, '
    'hygiene (published spelling hygeine), screens, grounding, being weird, alone time, diet, '
    'inflammation, sleep, recovery, caffeine, porn/NoFap, breathwork, news, social media, habits, '
    'learning to learn, boundaries, values, distraction, content consumption, digital dementia, '
    'philosophy, reactivity, and working out. Matches published About: constantly trying and failing '
    'feels better than accepting failure as an identity; hope this helps; take care of yourselves.'
)

picks_md = [
    '# Archive picks (not from published notes)',
    '',
    'Extracted from the YouTube auto-caption transcript and published About. '
    'Labeled separately from Jacob’s published About / Chapters / Quotes / Hashtags '
    '(none published beyond the solocast description).',
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
    '## Episode framing (solo — not a guest bio)', '', episode_framing, '',
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
    "Speaker map: solo solocast — all turns labeled Jacob (pause-gap segmentation only; no guest diarization)\n"
    "Cleanup: light dedupe of consecutive duplicate words; merged consecutive same-speaker fragments; HTML entities/nbsp unescaped; capitalized turn starts after merge; light caption spacing tidy; light ASR name tidy (Jacob Rhines; Junkyard Love Podcast; NoFap; YouTube); YouTube swear blanks normalized to ****\n"
    "No sentence rewriting.\n"
    "Guest: none (solo / Jacob Rhines). No guest page.\n"
    "Note: automatic ASR is imperfect; timestamps and phrasing may drift. Solo — no speaker swaps, but ASR wording remains rough.\n"
    f"Issue: YouTube automatic captions (en/en-orig) used; no official/manual track. YT duration {YT_DURATION_S}s vs RSS/inventory {DURATION_S}s (archive meta uses RSS duration). No published chapter timestamps. Title YT≠RSS — YT uses triple spaces between title segments; RSS uses dashes. H1/title use YouTube title; four-digit 0045 in slug/meta. About YT~RSS body (YT primary; footer stripped). Inventory has_quotes=no / has_timestamps=no / has_hashtags=no / has_guest_links=no. Archive picks fills timestamped quotes/chapters/keywords/hashtags/solo framing.\n"
    f"Speaker balance: Jacob {balance.get('Jacob',0)} turns/{words_by.get('Jacob',0)} words.\n",
    encoding='utf-8',
)

(CONTENT / 'SOURCES.txt').write_text(
    "Description source: YouTube primary per archive rules; About spaced from YT plain description (verbatim paragraphs). Inventory has_guest_links=no / has_quotes=no / has_timestamps=no / has_hashtags=no.\n"
    f"YouTube chars: {len(yt_desc.strip())}\n"
    f"RSS plain chars: {len(rss_plain.strip())}\n"
    f"Title source: YouTube / exact_public_title ({VIDEO_ID}). YT≠RSS — YT uses triple spaces; RSS uses dashes. H1/title use YouTube title; four-digit 0045 in slug/meta.\n"
    f"Title: {TITLE}\n"
    f"RSS title: {RSS_TITLE}\n"
    "Chapters source: none published (inventory has_timestamps=no; YT info.json chapters=None)\n"
    "Guest links: none (solo)\n"
    "Quotes: none published (inventory has_quotes=no)\n"
    "Hashtags: none published (inventory has_hashtags=no)\n"
    "About: Jacob published description verbatim as spaced paras from YouTube; YT≈RSS body (YT primary). Spelling hygeine / nobodies / breathework kept as published.\n"
    "Guest: none (solo / Jacob Rhines). No guest page.\n"
    f"Duration: RSS itunes:duration {DURATION_S}s ({DURATION_HUMAN}); YT info.json duration {YT_DURATION_S}s — using RSS/inventory {DURATION_S}\n"
    "Publish date: RSS/inventory 2020-06-18 (YT upload_date 20200619)\n"
    "Archive picks: added (timestamped transcript quotes, chapter-style timestamps from transcript beats, keywords/hashtags, solo episode framing) — extracted from YT auto-caption transcript + published About; kept separate from Jacob published About/Chapters/Quotes.\n"
    "Captions: freshly downloaded source-yt.en-orig.* / en.* this run (auto only; en identical to en-orig; no official en track).\n",
    encoding='utf-8',
)

meta = {
    'episode_number': EP_NUM,
    'episodeNumber': EP_INT,
    'title': TITLE,
    'rss_title': RSS_TITLE,
    'guest': None,
    'guest_name': None,
    'solo': True,
    'host': 'Jacob Rhines',
    'host_aka': 'JacobFromTheInternet',
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
    'guest_slug': None,
    'title_conflict': 'YT≠RSS',
}
(CONTENT / 'meta.json').write_text(json.dumps(meta, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

ep_md = [f'# {TITLE}', '',
         f'- Episode: {EP_NUM}',
         f'- Date: {DATE}', f'- Duration: {DURATION_HUMAN}',
         '- Guest: *(solo / host-only — no guest)*',
         '- Host: Jacob Rhines (JacobFromTheInternet)',
         f'- YouTube: {YOUTUBE}', f'- RSS: {RSS_URL}',
         f'- Spotify (show): {SPOTIFY}',
         f'- Apple (show): {APPLE}', '',
         '## About', '', about_md.strip(), '', '## Chapters', '',
         '(none published in episode notes)', '',
         '## Quotes', '', '\n'.join(quotes_md_lines), '',
         '## Guest links', '', '(none published — solo)', '']
# Archive picks section for episode.md (human readable, with episode-relative chapter links)
ap_md_body = [
    'Not from Jacob’s published episode notes — extracted from this episode’s transcript. Published About / Chapters / Quotes blocks above stay unchanged.',
    '',
    '### Memorable quotes',
    '',
]
for s, sp, q in quotes_ap[:12]:
    ap_md_body.append(f'- [{fmt_ts_from_s(s)}] {sp}: “{q}”')
ap_md_body += ['', '### Chapter-style timestamps', '']
for s, label in chapters:
    ap_md_body.append(f'- [{fmt_ts_from_s(s)}](/episodes/{EP_SLUG}/#{anchor_id_s(s)}) — {label}')
ap_md_body += [
    '', '### Keywords', '', keywords, '',
    '### Hashtags', '', hashtags, '',
    '### Episode framing (solo)', '', episode_framing,
]
ep_md += [
    '', '## Archive picks', '', '\n'.join(ap_md_body), '',
    '## Transcript', '',
    f'Source: YouTube automatic captions (en-orig). Light cleanup only (all turns Jacob; timestamps). Solo. Imperfect ASR flagged. Not rewritten. Word count: {word_count}. Turns: {len(turns)}.',
    '', transcript_md,
]
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
links_html = '<p class="note">(none published — solo solocast)</p>'

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
    'Not from Jacob’s published episode notes — extracted from this episode’s transcript. '
    'Published About / Chapters / Quotes blocks above stay unchanged; Archive picks add timestamps, '
    'chapters, keywords/hashtags, and episode framing where published notes lacked them.'
)

ld_keywords = keywords + ', Jacob Rhines, JacobFromTheInternet, Junkyard Love Podcast, solocast'
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
    ],
    'associatedMedia': [
        {'@type': 'VideoObject', 'contentUrl': YOUTUBE, 'name': TITLE},
        {'@type': 'AudioObject', 'contentUrl': AUDIO_URL, 'name': TITLE},
    ],
    'transcript': transcript_md.strip(),
    'keywords': ld_keywords,
    'description': about_md.strip(),
}

guest_meta_html = '<strong>Solo</strong> (host-only — Jacob Rhines / JacobFromTheInternet)'

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
<p class="meta">Episode __EPNUM__ · __DATE__ · __DUR__ · __GUESTMETA__</p>
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
<h3>Episode framing (solo)</h3>
<p>__BIO__</p>
</div>
<h2>Transcript</h2>
<p class="note">Source: YouTube automatic captions (en-orig). Light cleanup only (all turns Jacob; timestamps). Solo solocast. Imperfect ASR flagged. Not rewritten. Word count: __WC__. Turns: __TURNS__.</p>
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
    .replace('__BIO__', escape(episode_framing))
    .replace('__WC__', str(word_count))
    .replace('__TURNS__', str(len(turns)))
    .replace('__TRANS__', transcript_html)
)
(ep_dir / 'index.html').write_text(index_html, encoding='utf-8')

# Indexes — insert AFTER 0046 (base-safe relative hrefs)
home_li = (
    f'  <li><a href="episodes/{EP_SLUG}/index.html">{escape(TITLE)}</a>'
    f'<br><span class="note">{DATE} · Solo · {DURATION_HUMAN}</span></li>\n'
)
ep_li = (
    f'  <li><a href="episodes/{EP_SLUG}/index.html">{escape(TITLE)}</a>'
    f'<br><span class="note">Episode {EP_NUM} · {DATE} · {DURATION_HUMAN} · Solo</span></li>\n'
)

marker_home = (
    '  <li><a href="episodes/0046-rapper-jace-saltzman-killing-the-ego-and-stumbling-onto-the-right-path/index.html">'
    'Episode 046 with Rapper JACE Saltzman - Killing The Ego and Stumbling Onto The Right Path</a>'
    '<br><span class="note">2020-06-21 · JACE Saltzman · 2:07:28</span></li>\n'
)
marker_ep = (
    '  <li><a href="episodes/0046-rapper-jace-saltzman-killing-the-ego-and-stumbling-onto-the-right-path/index.html">'
    'Episode 046 with Rapper JACE Saltzman - Killing The Ego and Stumbling Onto The Right Path</a>'
    '<br><span class="note">Episode 0046 · 2020-06-21 · 2:07:28 · Guest: JACE Saltzman</span></li>\n'
)

home = (SITE / 'index.html').read_text(encoding='utf-8')
if EP_SLUG not in home:
    if marker_home not in home:
        raise SystemExit('home 0046 marker not found')
    home = home.replace(marker_home, marker_home + home_li)
    (SITE / 'index.html').write_text(home, encoding='utf-8')

ep_index = (SITE / 'episodes' / 'index.html').read_text(encoding='utf-8')
if EP_SLUG not in ep_index:
    if marker_ep not in ep_index:
        raise SystemExit('ep index 0046 marker not found')
    ep_index = ep_index.replace(marker_ep, marker_ep + ep_li)
    (SITE / 'episodes' / 'index.html').write_text(ep_index, encoding='utf-8')

# No guest page / no guests index update (solo)

sm = (SITE / 'sitemap.xml').read_text(encoding='utf-8')
if EP_SLUG not in sm:
    insert = (
        f'  <url><loc>{SITE_BASE}/episodes/{EP_SLUG}/</loc></url>\n'
        f'  <url><loc>{SITE_BASE}/episodes/{EP_SLUG}/episode.md</loc></url>\n'
    )
    m46 = f'  <url><loc>{SITE_BASE}/episodes/0046-rapper-jace-saltzman-killing-the-ego-and-stumbling-onto-the-right-path/episode.md</loc></url>\n'
    if m46 not in sm:
        raise SystemExit('sitemap 0046 marker not found')
    sm = sm.replace(m46, m46 + insert)
    (SITE / 'sitemap.xml').write_text(sm, encoding='utf-8')

llms = (SITE / 'llms.txt').read_text(encoding='utf-8')
if EP_SLUG not in llms:
    ep_line = (
        f'- [0045 Solo with Jacob Rhines — How To Take Care Of Yourself A Bit]'
        f'({SITE_BASE}/episodes/{EP_SLUG}/) — {DATE}\n'
    )
    m46_line = (
        f'- [0046 JACE Saltzman — Killing The Ego and Stumbling Onto The Right Path]'
        f'({SITE_BASE}/episodes/0046-rapper-jace-saltzman-killing-the-ego-and-stumbling-onto-the-right-path/) — 2020-06-21\n'
    )
    if m46_line not in llms:
        raise SystemExit('llms 0046 ep line not found')
    llms = llms.replace(m46_line, m46_line + ep_line)
    md_line = f'- [{SITE_BASE}/episodes/{EP_SLUG}/episode.md]({SITE_BASE}/episodes/{EP_SLUG}/episode.md)\n'
    m46_md = (
        f'- [{SITE_BASE}/episodes/0046-rapper-jace-saltzman-killing-the-ego-and-stumbling-onto-the-right-path/episode.md]'
        f'({SITE_BASE}/episodes/0046-rapper-jace-saltzman-killing-the-ego-and-stumbling-onto-the-right-path/episode.md)\n'
    )
    if m46_md in llms and md_line not in llms:
        llms = llms.replace(m46_md, m46_md + md_line)
    (SITE / 'llms.txt').write_text(llms, encoding='utf-8')

readme = (ROOT / 'README.md').read_text(encoding='utf-8')
if EP_SLUG not in readme and '**0045**' not in readme:
    marker = (
        '- **0046** JACE Saltzman (Rapper JACE Saltzman) — Killing The Ego and Stumbling Onto The Right Path — '
        '`site/episodes/0046-rapper-jace-saltzman-killing-the-ego-and-stumbling-onto-the-right-path/`\n'
    )
    add = (
        '- **0045** Solo with Jacob Rhines — How To Take Care Of Yourself A Bit — '
        '`site/episodes/0045-solo-jacob-rhines-how-to-take-care-of-yourself-a-bit/`\n'
    )
    if marker not in readme:
        raise SystemExit('README 0046 marker not found')
    readme = readme.replace(marker, marker + add)
    (ROOT / 'README.md').write_text(readme, encoding='utf-8')

if DEPLOY.exists():
    dep_ep = DEPLOY / 'episodes' / EP_SLUG
    if dep_ep.exists():
        shutil.rmtree(dep_ep)
    shutil.copytree(SITE / 'episodes' / EP_SLUG, dep_ep)
    src_content = DEPLOY / '_sources' / 'content' / EP_SLUG
    if src_content.parent.exists():
        if src_content.exists():
            shutil.rmtree(src_content)
        shutil.copytree(CONTENT, src_content)
    for name in ('index.html', 'llms.txt', 'sitemap.xml'):
        shutil.copy(SITE / name, DEPLOY / name)
    shutil.copy(SITE / 'episodes' / 'index.html', DEPLOY / 'episodes' / 'index.html')
    # guests index unchanged (solo — no guest page)
    if (DEPLOY / 'README.md').exists():
        shutil.copy(ROOT / 'README.md', DEPLOY / 'README.md')
    # copy build script into deploy sources if present
    build_src = ROOT / 'build_0045.py'
    if build_src.exists() and (DEPLOY / '_sources').exists():
        shutil.copy(build_src, DEPLOY / '_sources' / 'build_0045.py')
    print('deploy synced (no commit/push)')

print('DONE')
print('slug', EP_SLUG)
print('guest_handling', 'solo / no guest page (mirror 0060)')
print('turns', len(turns), 'words', word_count)
print('about paras', len(about_paras))
print('published quotes', len(published_quotes))
print('quotes_ap', len(quotes_ap), 'archive_chapters', len(chapters))
print('balance', dict(balance), dict(words_by))
print('About paras:')
for i, para in enumerate(about_paras):
    print(f'  [{i}] {para[:160].replace(chr(10), " / ")}')
print('First 6:')
for ms, sp, tx in turns[:6]:
    print(f'[{ms_to_ts(ms)}] {sp:12s} {len(tx.split()):4d}w | {tx[:100]}')
print('Last 4:')
for ms, sp, tx in turns[-4:]:
    print(f'[{ms_to_ts(ms)}] {sp:12s} {len(tx.split()):4d}w | {tx[:100]}')
print('Archive picks chapters:', len(chapters))
for s, label in chapters:
    print(f'  [{fmt_ts_from_s(s)}] {label}')
print('Archive quotes:', len(quotes_ap))
for s, sp, q in quotes_ap[:12]:
    print(f'  [{fmt_ts_from_s(s)}] {sp}: {q[:80]}')
print('title_conflict YT≠RSS')
print('H1', TITLE)
