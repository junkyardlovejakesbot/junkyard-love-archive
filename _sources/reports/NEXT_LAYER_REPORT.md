# NEXT LAYER report

Generated under `/workspace/junkyard-love-archive-deploy/`. **No git commit/push.** Parent deploys.

## A) Feeling-level SEO

Touched surfaces (title + `meta description` + `og:title` / `og:description` / `og:type` / `og:url`):

| Surface | Path |
|---------|------|
| Homepage | `index.html` |
| Six ways in | `six-ways-in/index.html` |
| Chapter radio | `radio/index.html` |
| Pick a clip | `clips/index.html` |
| Books index | `books/index.html` |
| Book detail pages | `books/<book-slug>/index.html` (37) |
| Guests index | `guests/index.html` |
| Guest pages (light) | `guests/*/index.html` (98) |
| Topics index | `topics/index.html` |
| Topic pages (feeling copy on six-ways doors + light on others) | `topics/*/index.html` (13) |
| Mood pages | `moods/*/index.html` (11) |
| Listen / Search / Start here / Donate / Merch | matching `*/index.html` |
| Episode pages | 123 published — **canonical titles kept**; description from About first paragraph (or prior meta / short fallback). No invented summaries. |

Tone: feeling / seeking language (“Long conversations when you can’t sleep.” / “Talks for men taking the armor off.”). No clinic-speak or treatment claims.

Also:

- `robots.txt` present (`Allow: /` + Sitemap URL)
- `sitemap.xml` updated with book detail URLs
- Script: `_sources/apply_feeling_seo.py`

## B) Chapter radio = on-page listen path

**Behavior**

1. **Play a random clip** (or subject chip → Play): shows card with title, `short_summary`, guest, episode, start; expand → `long_summary`.
2. If `youtube_id` exists: loads YouTube IFrame API (fallback: `youtube-nocookie` embed) **starting at `start_seconds`**, only after the Play/Next gesture. **No autoplay on page load.**
3. If no `youtube_id` (e.g. 0047): card + “Open episode at chapter” `#t-` link — no fake player.
4. **Next**: another random clip (same subject if active); swaps embed to the new video/start.
5. Subject chips kept. Leftover set UI not present.
6. Does not host/cut audio files.

**Choice documented:** YouTube end does **not** auto-advance. User must hit **Next** (safer default).

Files: `assets/archive.js`, `radio/index.html`, `assets/style.css`.

## C) Books as guest research

| Metric | Value |
|--------|-------|
| Before (ASR scraps / duplicates) | **53** |
| After (canonical titled works) | **37** |
| Source scraps (regenerable) | `_sources/books_index_scraps.json` |
| Rebuild script | `_sources/rebuild_books_index.py` |
| Outputs | `_sources/books_index.json`, `assets/books_index.json`, `books/index.html`, `books/<slug>/index.html` |

Cleanup: dropped mid-sentence ASR, merged fuzzy duplicates (e.g. Body Keeps the Score variants, Awake…, Full Voice, Be Here Now), resolved `mentioned_by` to **Jacob** or guest real name (else “mentioned on episode”), added `book_slug` + `guest_slug` when mappable.

**Guest pages with “Books mentioned”** (guest mentioned ≥1 cleaned book):

anne-riley, barbara-mcafee, brandon-cruz, brent-spirit, cristine-hull, heather-hutchison, jeremy-sherman, jerry-fu, juli-geske-peer, julie-hoyle, mack-t, marty-strong, nike-anani, ravinder-taylor, rebecca-wild, rebecca-wyld, ryan-baker, ryan-reed, sigmar-berg, spencer-hicks, swami-nityananda, trevor-may, will-andes, zach-beach

Rebecca **Wyld** ≠ Rebecca **Wild** preserved (separate guests, separate books).

Books index: one row per canonical title, all mention episodes listed, guest names as research doorways, optional **Browse by guest**.

No affiliate links.

## Live paths (relative to site base `/junkyard-love-archive/`)

- `/` — homepage
- `/six-ways-in/` — six doors
- `/radio/` — chapter radio (on-page listen)
- `/clips/` — pick a clip
- `/books/` — books index
- `/books/<book-slug>/` — book detail (e.g. `/books/the-body-keeps-the-score/`)
- `/guests/<slug>/` — guest + Books mentioned when applicable
- `/moods/<slug>/` — mood doors
- `/topics/<slug>/` — topics
- `/robots.txt`, `/sitemap.xml`

## Confirm

- **No git commit**
- **No git push**
- Parent deploys

## Success check

- Radio: Play embeds YT at chapter time after click; Next works; no load autoplay
- Books: 37 << 53; guest↔book links both directions
- SEO: view-source on home / radio / a mood / a book shows description + og tags
