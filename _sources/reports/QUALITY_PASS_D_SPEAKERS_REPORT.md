# Quality-pass (d) — Intro / Jacob / Guest / Outro speaker labeling

_Mode: applied_

## Counts

- Episodes scanned: **120**
- Episodes with ≥1 Intro label now: **84** (turns: 114)
- Episodes with ≥1 Outro label now: **93** (turns: 112)
- Audit intro coverage: **73/73** (0124 live guest-greet intentionally kept as Jacob)
- Audit outro coverage: **44/44**
- Additional clear produced opens/closes beyond audit also labeled (formula bumper / audience CTA)
- Mid-run misattrs fixed via Intro/Outro path (bumper crumbs / guest-labeled closes), e.g. 0040 Brandon “My mates”, 0055 Brian live-stream bumper, 0114/0116 guest-held closes, 0065/0078 guest outros

## Method

- Regenerable: `_sources/fix_intro_outro_speakers.py`
- Updates `_sources/content/*/transcript.md` + `transcript.html` and matching `episodes/*/index.html` cue speakers
- Episodes without content dirs (0118/0120/0121): episode HTML only
- Ordered cue-speaker sync (handles duplicate timestamps)
- Timestamps/clocks preserved; cue text not rewritten (soft ASR 0020/0025/0047/0037: speakers only)
- Jacob published About untouched; topic chips / browse-subtitle / dark theme / quotes / chapters preserved
- **No git commit/push**

## Remaining uncertain

- **0124**: first turn is live “Well, Sigmar, welcome…” — kept as **Jacob** (not Intro), despite audit flag
- **0010**: uses legacy `<span class="spk">` transcript markup (no `class="cue"`); no Intro/Outro change this pass (live host open, no formula bumper)
- Dual-guest mid-run swaps without bumper/CTA text: not aggressively reassigned (would need audio) — leave ASR diarization as-is
- Soft-ASR eps (0020/0025/0047/0037): speaker/intro-outro focus only; wording left soft
- Some long final turns mix goodbye + produced close in one cue — whole cue labeled **Outro** when CTA/formula present

## Sample mid-run / misattr fixes

- 0040: Brandon “My mates” bumper crumb → Intro
- 0055: Brian “Watch our live stream…” bumper continuation → Intro
- 0116: Curtis bumper line → Intro
- 0065/0078/0114: guest-held produced closes → Outro
- 0120: trailing formula bumper lines → Outro

