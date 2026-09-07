# Quote rebuild — stand-alone complete quotes

**Date:** 2026-09-07 (CT)  
**Deploy:** `/workspace/junkyard-love-archive-deploy/`  
**Script:** `_sources/rebuild_quotes_clean.py` (+ surgical cleanup pass)  
**No git commit/push.**

## Rules applied
- Quote allowed only if: complete grammatical thought; zero episode context; not ASR garbage / mid-clause / filler; has speaker + episode; ideally claim / story beat / practice.
- Prefer 3–8 strong quotes/ep; quality over volume (fewer OK when thin).
- Do not invent quotes; do not rewrite Jacob published About (published `source-quotes.md` lines kept when complete, with verified timestamps when possible).
- Soft ASR **0020, 0025, 0037, 0047**: published-complete only (no unpunctuated ASR mining).
- Skip removed 0001/0014/0016/0029.

## Counts
| Metric | Before | After |
|---|---:|---:|
| Archive / index quotes | **963** | **442** |
| Dropped (fragments / weak) | — | **521** |
| `quotes_clean.json` rotator pool | — | **442** |

## Worst offenders cleaned
- **0021 Rosetan** — removed ASR scraps including **“I get see that really good to like I even just in practice like when I'm.”** and other mid-clause lines. Kept 4 stand-alone-ish transcript lines (band origin / vision / practice).
- Early catalog scraps ending in `because man/people`, `and I feel.`, `I love.`, `by the time.` — dropped in cleanup pass (24 additional).
- Soft ASR **0020 / 0025**: no complete published Quotes list → **0** archive quotes retained (thin OK).
- Soft ASR **0037**: kept 3 complete published About quotes.
- Soft ASR **0047**: kept 1 complete published quote (Maya Angelou line already on episode).

## Artifacts updated
- `episodes/*/index.html` — Memorable quotes / `blockquote.archive-quote`
- `_sources/content/*/source-archive-picks.md` (+ work mirror under `/workspace/junkyard-love-archive/content/` where present)
- `_sources/quotes_clean.json` + `assets/quotes_clean.json`
- `assets/episodes_index.json` + `_sources/episodes_index.json` quote fields
- `assets/archive.js` — homepage `data-random-quote` rotator prefers `assets/quotes_clean.json`

## Confirm
- **No git commit / no push.**
- Parent can run chapters next.
