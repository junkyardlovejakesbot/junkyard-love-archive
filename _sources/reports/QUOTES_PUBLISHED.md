# QUOTES_PUBLISHED

**Date:** 2026-09-13 (America/Chicago)

**Deploy:** `/workspace/junkyard-love-archive-deploy`

**No git push. No invented quotes. Published description quotes only.**

## Counts

- Public quotes now (`quotes_clean.json`): **244**
- Old `quotes_clean` count (git HEAD): **442**
- Mined quotes archived to `_sources/quotes_mined_archive.json`: **319**
- Mined removed from public view (old − new): **198**
- Episode HTML `archive-quote` removed: **317** (kept matching published: **125**)
- Episodes with ZERO published quotes (NEEDS JACOB): **72**

## NEEDS JACOB — episode numbers with zero published quotes

0002, 0003, 0004, 0005, 0006, 0007, 0008, 0009, 0010, 0011, 0012, 0013, 0015, 0017, 0018, 0019, 0020, 0021, 0022, 0023, 0024, 0025, 0026, 0027, 0028, 0030, 0031, 0032, 0033, 0038, 0041, 0042, 0045, 0048, 0051, 0055, 0059, 0060, 0061, 0063, 0064, 0066, 0068, 0070, 0072, 0073, 0074, 0076, 0077, 0079, 0080, 0081, 0083, 0084, 0085, 0086, 0087, 0089, 0090, 0093, 0095, 0096, 0097, 0099, 0101, 0103, 0105, 0106, 0107, 0108, 0109, 0110

### First 30

0002, 0003, 0004, 0005, 0006, 0007, 0008, 0009, 0010, 0011, 0012, 0013, 0015, 0017, 0018, 0019, 0020, 0021, 0022, 0023, 0024, 0025, 0026, 0027, 0028, 0030, 0031, 0032, 0033, 0038

## Notes

- Source of truth: `_sources/content/*/source-quotes.md` quote lines (not `(none published…)` stubs) plus plain `<blockquote>` under episode Quotes sections.
- Inline About phrase scraps noted in none-published stubs were **not** promoted to public quotes.
- `source` field set to `published`. Timestamps omitted (not in published notes).
- Speaker set only when named in published attribution (gloss after the name is discarded).
- Fake blurb phrases cleared from `assets/mood_doors.json`, `_sources/mood_doors.json`, and `moods/*/index.html` clip-summary fields (visitor leftover: none).
- Clip `short_summary`/`long_summary` remain empty (2422). `assets/archive.js` does not render them (intentionally hidden).
- `llms.txt` updated with bot guidance for real fields; empty clip summaries called out as correct.
