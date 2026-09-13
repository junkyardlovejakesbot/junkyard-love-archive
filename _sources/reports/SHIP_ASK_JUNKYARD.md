# Ship — Ask the Junkyard + Chapter radio subjects

Generated: 2026-09-13 (America/Chicago)

## A — Chapter radio subjects

Kept existing 8 subjects (terms unchanged). Added 8 new subjects with honest pools after host_open / bumper exclusion. Body / Voice / Faith & doubt use **chapter-title-only** matching so `breath-body-practice` tag pollution and episode browse-title “Beliefs” do not flood the pool. Mind & mood uses `tag_terms` + `title_terms` hybrid.

### Subjects shipped (16) — honest pool / with YouTube

| Subject | slug | pool | with YouTube |
|---|---|---:|---:|
| Breath | breath | 2315 | 2293 |
| Men & fatherhood | men-fatherhood | 2012 | 1998 |
| Awakening | awakening | 443 | 442 |
| Healing | healing | 608 | 604 |
| Starting over | starting-over | 30 | 30 |
| Music | music | 552 | 530 |
| Meditation | meditation | 2316 | 2294 |
| Work & money | work-money | 1537 | 1515 |
| Love & relationships | love-relationships | 545 | 544 |
| Sobriety | sobriety | 281 | 259 |
| Body | body | 65 | 64 |
| Voice | voice | 15 | 15 |
| Mind & mood | mind-mood | 514 | 513 |
| Science & frequency | science-frequency | 262 | 262 |
| Faith & doubt | faith-doubt | 33 | 33 |
| Creativity | creativity | 1428 | 1406 |

### Refused subjects

_None._ All eight proposed subjects cleared the “real YouTube chapters, not empty/nearly empty” bar (Voice ships at 15 ≈ the ~19 guidance).

### Radio UI

- `radio/index.html`: chips for all 16 subjects
- Quiet use line (not a banner): “Leave this on while you wash dishes, walk, work out, stretch, drive, or wake up.”
- Play / auto-advance / subject-lock behavior unchanged in `assets/archive.js`
- Source of truth: `_sources/radio_sets.json` (copied to `assets/radio_sets.json`)
- `filterClipsByTerms` extended for `match: "title"`, `title_terms`, `tag_terms`

## B1 — Human search (Ask the Junkyard)

- Script: `_sources/build_ask_junkyard.py`
- Candidate chapters (non-host_open, non-bumper, not removed): **2349**
- Indexed chapter windows: **2349**
- Skipped: **0** (see `_sources/reports/SEARCH_GAPS.md` — empty skip table; six content-folder slug aliases resolved)
- Machine lean index: `assets/chapter_index.json` (+ `_sources/chapter_index.json`)
- Browser corpus sharded (~15MB): `assets/chapter_search/manifest.json` + `shard-00.json` / `shard-01.json` (mirrored under `_sources/chapter_search/`)
- `assets/archive.js` `search()` loads shards, ranks **chapter hits first** (verbatim excerpt), then episode-level matches
- `search/index.html` note: searches conversation transcripts by chapter
- No invented summaries / clip blurbs; excerpts are trim-only complete sentences (~80–160 words)

## B2 — Machine index

- `llms.txt` points at `assets/chapter_index.json`
- `sitemap.xml` includes `https://junkyardlovejakesbot.github.io/junkyard-love-archive/assets/chapter_index.json`

## Live URL stubs

- Radio: https://junkyardlovejakesbot.github.io/junkyard-love-archive/radio/
- Search: https://junkyardlovejakesbot.github.io/junkyard-love-archive/search/
- Chapter index: https://junkyardlovejakesbot.github.io/junkyard-love-archive/assets/chapter_index.json
- Chapter search manifest: https://junkyardlovejakesbot.github.io/junkyard-love-archive/assets/chapter_search/manifest.json

## Guardrails

- Books shelf untouched
- Guest pages untouched
- No ambient beds
- No invented quotes or clip blurbs
