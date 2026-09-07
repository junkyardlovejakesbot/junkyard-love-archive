# Quality pass (c) — full-runtime Archive picks chapters

**Date:** 2026-09-06 (CT)  
**Script:** `_sources/fix_full_runtime_chapters.py` (regenerable)  
**Overrides:** `_sources/chapter_label_overrides.json` (handcrafted priority lists)  
**Word list:** `_sources/words_alpha.txt` (label filter)  
**Scope:** all 120 published numbered episode pages (`*-removed` skipped)  
**No git commit / no push.**

## What changed
- Rebuilt **Archive picks → Chapter-style timestamps** in `source-archive-picks.md` + episode HTML `<ul class="chapters">`.
- Walked each transcript to the **actual end** (including host outro when present).
- Snapped chapter clocks to valid transcript turns (`#t-HH-MM-SS`).
- Kept accurate existing chapter labels; filled truncated / thin coverage; labeled host close as **Outro**.
- Post-cleaned redundant **Close/Closing** chapter immediately before **Outro** (29 eps).
- Jacob published About / Chapters / Quotes blocks unchanged.
- Topic chips preserved; browse-subtitle preserved where it already existed (0037 never had one on the ASR rebuild page).

## Priority truncated (audit list) — before → after

| Ep | Chapters before → after | Last chapter before → after | Coverage |
|---|---|---|---|
| 0003 | 14 → 22 | 00:54:32 → 01:17:46 Outro | 68% → 97.5% |
| 0012 | 17 → 22 | 00:55:49 → 01:04:54 Outro | 83% → 96.6% |
| 0020 | 10 → 19 | 01:38:14 → 02:03:04 Outro | 79% → 98.6% |
| 0027 | 7 → 16 | 01:11:36 → 01:46:41 Outro | 67% → 99.4% |
| 0028 | 26 → 36 | 00:57:47 → 01:40:38 Outro | 57% → 99.4% |
| 0037 | 24 → 27 | 02:20:09 Outro (kept) | 99.6% → 99.6% (+ mid-gap fills) |
| 0056 | 14 → 18 | 01:29:16 → 02:07:54 Outro | 70% → 99.6% |
| 0079 | 13 → 17 | 00:39:27 → 00:46:39 Outro | 82% → 97.2% |
| 0080 | 14 → 19 | 00:35:36 → 00:59:35 Outro | 58% → 97.5% |
| 0085 | 10 → 15 | 00:45:34 → 01:00:03 Outro | 74% → 97.6% |
| 0086 | 12 → 20 | 01:06:26 → 01:51:20 Outro | 59% → 98.5% |
| 0087 | 12 → 18 | 00:55:09 → 01:25:33 Outro | 63% → 98.1% |
| 0095 | 12 → 18 | 00:56:30 → 01:47:03 Outro | 52% → 98.5% |

## Catalog summary
| Metric | Value |
|---|---:|
| Episodes processed | 120 |
| With Outro last chapter | **120** |
| Median last-chapter coverage | ~98.8% of runtime |
| Min coverage after pass | 86.8% (**0103**) |
| Errors | 0 |

## Still thin / notes
- **0109** — last chapter ~94.8% (near threshold; has Outro).
- **0103** — last chapter at **01:34:27** (~87% of inventory **1:48:49**). Transcript has only **35** long turns; caption clocks stop at 01:34:27 even though inventory/YT duration ≈6529s. Outro CTA is inside that final turn. Needs caption/ASR clock repair (separate from chapter labeling) before coverage can reach ~95%+.
- A few long freeform eps still lean on auto-filled mid labels (dictionary-filtered); priority list used handcrafted overrides.
- Density now ≥ ~6 chapters/hour for ≥1h episodes (post-pass check).

## 0037 status
- **Full RSS faster-whisper ASR already on disk** (TRANSCRIPT_SOURCE: MP3 ASR; max turn **02:20:09**; duration ≈8445s).
- **Not held** — lightly extended mid-gap after **01:54:53** and kept **Outro — drink water / get present** at **02:20:09**.
- If another job continues diarization cleanup, **re-run** `_sources/fix_full_runtime_chapters.py --only 0037 --force` (and quote pass b) after that lands.

## How to regenerate
```bash
cd junkyard-love-archive-deploy
python3 _sources/fix_full_runtime_chapters.py \
  --report _sources/reports/QUALITY_PASS_C_CHAPTERS.json
# optional: edit _sources/chapter_label_overrides.json then re-run --only …
```

## Implementation notes
- Most episodes use `<ul class="chapters">`; **0124** uses `<ul class="archive-chapters">` — script now matches both.
- Priority truncated eps use handcrafted lists in `chapter_label_overrides.json`; others auto-extend with dictionary-filtered labels + Outro detection.

## Confirm
- **No git commit / no push.** Branch remains up to date with `origin/main` (local unstaged edits only).
