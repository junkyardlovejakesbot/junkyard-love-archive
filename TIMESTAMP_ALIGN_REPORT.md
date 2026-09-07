# Junkyard Love — Timestamp / Anchor Alignment Report

_Generated: 2026-09-06 evening (America/Chicago). Pass: format normalize + pick-target repair. No mass re-ASR. No git commit/push._

## Goals

Align transcript / Archive-picks `#t-` anchors to real audio clocks so search and clip deep-links land correctly. Prefer canonical `#t-HH-MM-SS` (zero-padded) matching displayed `[HH:MM:SS]`.

## Audit summary (120 published episodes; `*-removed` skipped)

| Metric | Count |
|---|---:|
| Published numbered episode dirs | 120 |
| Canonical `#t-HH-MM-SS` scheme (after fix) | **120** |
| Compact `#tM-SS` / `#tH-MM-SS` remaining | **0** (was 1: **0010**) |
| Episodes with unresolved Archive-picks / chapter `#t-` hrefs (after fix) | **0** (was 9) |
| Display time vs `id` mismatches on `.ts` links | 0 |
| Max turn clock ≫ inventory duration (>115%) | 0 |
| Healthy after this pass (canonical + resolves + no long-skew / mismatch) | **120** / 120 |

### Pre-fix snapshot

- **119** episodes already used canonical `#t-HH-MM-SS`.
- **1** episode (**0010**) used compact `#t0-00` / `#t1-27-29` style ids and hrefs (clock values themselves matched displayed `M:SS` / `H:MM:SS`).
- **9** episodes had Archive picks “Chapter-style timestamps” linking to `#t-…` ids that did not exist on any transcript turn (off by ~1–45s from nearest turn).

## Fixes applied

### 1. Episode **0010** — compact → canonical (high value)

Clock values **unchanged**; only id/href/display formatting normalized.

| Before | After |
|---|---|
| `id="t0-00"` / `href="#t1-27-29"` | `id="t-00-00-00"` / `href="#t-01-27-29"` |
| Display `0:00`, `1:27:29` | Display `[00:00:00]`, `[01:27:29]` |

**Files updated:**

- `junkyard-love-archive-deploy/episodes/0010-…/index.html`
- `junkyard-love-archive/site/episodes/0010-…/index.html` (mirror)
- `junkyard-love-archive/content/0010-…/transcript.html`, `transcript.md`, `source-archive-picks.md`
- `junkyard-love-archive-deploy/_sources/content/0010-…/` (same three sources)

Verify: 384 turn ids, all pick/chapter hrefs resolve, max clock `01:46:04` vs duration `01:46:43` (ratio 0.994).

### 2. Nine episodes — missing chapter/pick targets

Inserted hidden `<span id="t-HH-MM-SS" class="t-anchor" …>` **before** the nearest transcript turn (≤90s) so chapter hrefs resolve and land near the spoken moment. **Pick clock labels unchanged.**

| Ep | Anchors added | Notes |
|---|---:|---|
| 0002 | 11 | Chapter-style list vs turn grid |
| 0003 | 14 | same |
| 0012 | 14 | same |
| 0027 | 7 | same |
| 0028 | 24 | same |
| 0057 | 1 | `t-02-06-59` ≈ turn `t-02-07-26` (Δ27s) |
| 0079 | 10 | same |
| 0081 | 1 | `t-00-30-40` ≈ turn `t-00-29-55` (Δ45s) |
| 0082 | 14 | one chapter Δ31s from nearest turn |

Deploy HTML updated; work `site/episodes/` copies synced for the same slugs.


### 3. Builder guard — `build_0010.py`

Updated `ms_to_ts` / `ts_to_anchor` / `fmt_ts_from_s` / `anchor_id_s` / `sec_to_hms` so a future rebuild of 0010 emits canonical `#t-HH-MM-SS` + `[HH:MM:SS]` (prevents compact regression). Work tree only; not committed.

## Priority ASR episodes (already audio-clock aligned)

These were **not** rewritten in this pass; confirmed healthy canonical anchors:

| Ep | Source | Max turn | Inventory duration | Ratio |
|---|---|---|---|---:|
| **0020** | faster-whisper small/int8 on full RSS MP3 | 02:04:02 | 02:04:52 | 0.993 |
| **0025** | faster-whisper small/int8 (YT had no captions) | 02:21:06 | 02:21:09 | 1.000 |
| **0047** | faster-whisper small/int8 on published MP3 | 02:35:17 | 02:35:47 | 0.997 |

## Remaining hard issues (need re-ASR or human check — not fixed here)

1. **0037 (Rebecca Wyld)** — YT auto-caption transcript ends ~`01:56:05` and matches **YouTube** duration (~7005s / ~1:56:45), but RSS/inventory duration is **02:20:45** (8445s). Same class of problem as pre-ASR **0020**: truncated video vs full audio. **Needs full-length ASR from RSS enclosure** if the published MP3 is longer than YT.
2. **0020 / 0025 / 0047** — already on audio-clock ASR (`small/int8`). Optional future upgrade to a larger Whisper model for quality; **not** a timestamp-scheme problem.
3. **Chapter Δ vs turns** — the nine repaired episodes still have chapter labels that are YT/editorial times, not exact turn starts. Hidden anchors land on the nearest turn; a future pass could snap chapter labels to exact turn clocks if desired.
4. **YT auto-caption clock fidelity** — most of the catalog still uses YouTube auto captions. Those clocks usually track the uploaded video; if RSS audio ever diverges (extra intro, alternate master), only per-episode ASR (as with 0020/0047) will fully realign. Out of scope for this pass (no mass re-ASR).

## Out of scope (honored)

- Full Whisper re-transcription of 100+ episodes
- About / Jacob verbatim note edits
- Topic chips
- Git commit / push

## Paths

- Work report: `junkyard-love-archive/TIMESTAMP_ALIGN_REPORT.md`
- Deploy mirror: `junkyard-love-archive-deploy/TIMESTAMP_ALIGN_REPORT.md`
- Audit JSON (internal): `junkyard-love-archive/_timestamp_audit_after.json`

## Success checklist

- [x] Audit all 120 published episodes
- [x] Normalize **0010** compact anchors → `#t-HH-MM-SS` without changing clock values
- [x] Repair unresolved Archive-picks chapter targets (9 eps)
- [x] Apply fixes to deploy episode HTML (+ 0010 content sources)
- [x] Write this report
- [x] **No git commit/push**
