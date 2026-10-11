# Clip / chapter timing (archive standard)

- `start_seconds` / `start` = the **published** chapter clock (the "Chapters" list on the episode page). Never edited by timing code except to correct index drift back to that published clock (unique titles only).
- `play_start_seconds` / `play_start` / `play_anchor` = **speech-aligned** start used for embeds, YouTube `t=`, and transcript `#t-` links. Computed by `speech_align.py` from the episode's own captions (YouTube json3 > vtt > SRT > transcript.md):
  - latest speaker turn within 10s before the mark; else latest sentence start (pause on unpunctuated auto captions); else caption-line start
  - a mark sitting just before an answer to a question starts at the question
  - never later than published, never more than 30s earlier, never before the episode's first speech (no intro music), never inside the 0125 promo zone
- `apply_play_starts.py` writes these into clips_index, chapter_index, chapter_search shards, mood_doors, episodes_index chapters (assets/ and _sources/) and mood page YouTube links.
- It runs automatically at the end of `rebuild_clips_index.py`, `build_ask_junkyard.py`, `build_mood_radio.py`, `polish_clip_summaries.py`, `build_discover_layer.py`, `pass2_crawler_survivability.py`.
- **Adding an episode:** after the episode page + clips are built, run `rebuild_clips_index.py` then `build_ask_junkyard.py` (both apply timing). Or run `python3 _sources/apply_play_starts.py` directly. Homepage start clip uses `speech_align.play_start` in `build_site_enhance_v3.py`.
- Check one start: `python3 _sources/snap_clip_start.py _sources/content/<folder> <published_seconds>`.
