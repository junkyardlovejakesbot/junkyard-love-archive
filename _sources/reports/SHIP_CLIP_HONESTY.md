# SHIP_CLIP_HONESTY

**Date:** 2026-09-13 (America/Chicago)  
**Scope:** Part A only — hide fake clip blurbs, tighten pools, filter weak rotator quotes. No LLM rewrite of 2422 descriptions. No Ship 1 reopen. Part B (chapter search) deferred unless credits remain after live A.

## Live URLs (after Pages)

- https://junkyardlovejakesbot.github.io/junkyard-love-archive/
- https://junkyardlovejakesbot.github.io/junkyard-love-archive/radio/
- https://junkyardlovejakesbot.github.io/junkyard-love-archive/clips/
- Example episode: https://junkyardlovejakesbot.github.io/junkyard-love-archive/episodes/0124-sigmar-berg-conscious-breathing-break/
- Search: https://junkyardlovejakesbot.github.io/junkyard-love-archive/search/

## DONE

1. **Cards (radio / shuffle / pick-a-clip / mood)** show only: chapter title, episode number, guest, start time, Play / open-at-chapter / transcript / full episode. `short_summary` and `long_summary` are **not rendered** (fields left in JSON).
2. **Pools** exclude `host_open`, drink-water / hit-record bumpers, and other `isBumper` titles via `isPoolClip()` in `assets/archive.js`.
3. **Thin radio subjects** no longer fall back to stuffing the whole catalog — show an honest empty message instead.
4. **Quotes filter** on `assets/quotes_clean.json` (+ `_sources/`): **442 → 438** (4 dropped). See `QUOTE_FILTER.md`.

## BLOCKED

- None for Part A.

## NEEDS JACOB

- If any radio subject door stays empty after exclusions, hand-curate preferred chapter titles for that subject (do not invent).
- Part B (chapter-window transcript search) not started this report — only after A is confirmed live and credits remain.

## Not done (by design)

- No rewrite of 2422 clip descriptions.
- No books / Six ways rename / donate / host / beds / auto-advance.
