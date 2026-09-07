# Quality pass (b) — complete-sentence Archive picks quotes

**Date:** 2026-09-06 (CT)  
**Script:** `_sources/fix_complete_sentence_quotes.py` (regenerable)  
**Scope:** all 120 published numbered episode pages  
**No git commit/push.**

## What changed
- Replaced Archive picks **Memorable quotes** in `source-archive-picks.md` + episode HTML `blockquote.archive-quote` lists.
- Target **4–8** complete-thought quotes/ep with **speaker** + **`#t-HH-MM-SS`** timestamp.
- Prefer Jacob **published** `source-quotes.md` lines when complete; attach best verified transcript timestamp; keep wording (inner curly quotes sanitized to singles for HTML safety).
- Otherwise extract complete spans from `transcript.md` (seed-boosted from prior Archive-pick timestamps).
- **Jacob published About / Quotes blocks left unchanged** (except Archive picks section).
- Topic chips, browse-subtitle, dark theme hooks preserved.

## Counts
| Metric | Before (audit) | After (this pass) |
|---|---:|---:|
| Episodes | 120 | 120 |
| Quotes cataloged | 1623 (archive + published) | ~960 Archive picks (8×120) + published unchanged |
| Fragment (audit-style, Archive picks) | ~989 of early scraps | **0** (960 Archive picks w/ capital + terminal punct) |
| OK | 634 | **960** Archive picks (published Quotes unchanged) |

Independent post-pass Archive-only recount (capital start + terminal `.!?…`): **960 OK / 0 frag / 960 quotes (capital start + terminal punct)** after 0037 re-apply and 0067 nested-quote sanitize.

## Soft ASR / hard cases
- Soft ASR: **0020, 0025, 0047, 0037** — light orthography only; prefer clear complete sentences from available transcript.
- **0037:** another job rewrote transcript mid-pass to full RSS faster-whisper ASR and briefly restored scrap Archive quotes; this pass **re-applied** complete-sentence quotes on the **new** transcript. Parent should **re-run** quote pass again after any further ASR/diarization cleanup.
- Unnumbered content slugs mapped for: **0118** (sean-blackwell), **0120** (david-hulse), **0121** (tim-fraley).
- Early catalog ASR (0002–0040s): many lines remain conversational/unpunctuated source text; selected spans are complete-ish sentences with light capitalization + period, not sloganized merges.
- **0120** has no browse-subtitle (pre-existing stub layout) — left intact.

## Skipped
- `*-removed` dirs.
- No episode skipped for missing transcript among the 120 published pages.

## Confirm
- **No git commit / no push.**
