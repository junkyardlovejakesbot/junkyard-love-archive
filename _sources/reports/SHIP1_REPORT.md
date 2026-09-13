# SHIP 1 report

**Date:** 2026-09-13 (America/Chicago)  
**Commit:** 0de0c7a  
**Scope:** Ship 1 only — counts, chrome, empty labels, Trenten spelling check, publish dates, newbie above-fold. Ships 2–6 not started.

## Live URLs (after Pages catch-up)

- https://junkyardlovejakesbot.github.io/junkyard-love-archive/
- https://junkyardlovejakesbot.github.io/junkyard-love-archive/topics/
- https://junkyardlovejakesbot.github.io/junkyard-love-archive/episodes/0047-trenten-kesler-searching-for-fluidity-learning-from-detail-and-laughing-with-everyone/
- https://junkyardlovejakesbot.github.io/junkyard-love-archive/listen/

## DONE

1. **Homepage Topics counts** — all 13 topic cards show real counts (no `<span class="count">0 episodes</span>`). Root cause was stale homepage HTML; topic pages were already correct.
2. **Homepage hierarchy** — tagline first (“Mining the hearts…”), show name once smaller under it, search in header top-right, wider `wrap-wide`, tooltips on nav/topic/start packs/moods.
3. **Quote rotator** — “another quote” button preserved/recreated by `renderQuoteCard` + `wireAnotherQuote` in `assets/archive.js`.
4. **Search hint rotation** — `wireSearchHints` shuffles placeholders from real guests/chapter words on load/focus.
5. **What we talk about** — button label: “What do we talk about on the Junkyard Love Podcast?” (wired to existing subject shuffle).
6. **Newbie above-fold copy** — Jacob-approved short intro on home; longer directory copy on `/listen`.
7. **Episode publish dates** — `Published YYYY-MM-DD · year` near title on numbered episode pages (120). Legacy slug paths are redirects to numbered URLs (no separate date needed).
8. **Empty labels** — 0010/0013 already link “Quotes are in Archive picks below” when published Quotes block is empty but Archive picks exist.
9. **Trenten Kesler** — episode slug/title use **Kesler** (not Kessler). Kessler hits remaining only in ASR/transcript text (0036 mention + 0047 whisper JSON) — left as spoken/ASR, not a path bug.

## BLOCKED

- None for Ship 1 core.

## NEEDS JACOB

- None required to ship Ship 1.
- Optional later: if any guest social URL still appears as pasted plain text in an About block, send the preferred label + URL (Ship 1 did not invent replacements). Full About raw-URL linkification pass can wait for a later ship if you want it exhaustive.

## Not in this ship

Ships 2–6 (clip gems, names/video targets, books library, quotes, renames/donate/host) — not started per session order.
