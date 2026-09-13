#!/usr/bin/env python3
"""Build chapter-level transcript search indexes for Ask the Junkyard.

Emits:
  assets/chapter_index.json (+ _sources copy) — lean machine index
  assets/chapter_search.json (+ _sources) or sharded assets/chapter_search/
  _sources/reports/SEARCH_GAPS.md
"""
from __future__ import annotations

import json
import re
import shutil
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "_sources"
ASSETS = ROOT / "assets"
CONTENT = SRC / "content"
REPORTS = SRC / "reports"
WORDS_ALPHA = SRC / "words_alpha.txt"

REMOVED = {"0001", "0014", "0016", "0029"}
BASE_URL = "https://junkyardlovejakesbot.github.io/junkyard-love-archive"
SHARD_SOFT_LIMIT = 7_500_000  # shard before ~8MB

# Content folder aliases when slug on disk differs from episode_slug
SLUG_ALIASES = {
    "0118-what-if-mania-is-a-message-sean-blackwell": "sean-blackwell-mania-is-a-message",
    "0120-im-not-a-teacher-david-hulse": "david-hulse-path-to-no-path",
    "0121-surrendering-the-porsche-tim-fraley": "tim-fraley-surrendering-the-porsche",
    "0122-laughing-like-a-hairy-oaf-barbara-mcafee": "0122-barbara-mcafee",
    "0123-endorphins-love-quantum-medicine-four-bodies": "0123-cristine-hull",
    "0124-sigmar-berg-conscious-breathing-break": "0124-sigmar-berg",
}

CUE_RE = re.compile(
    r"^\[(\d{1,2}):(\d{2}):(\d{2})\]\s*([^:\n]+):\s*(.*)$"
)
TS_ONLY_RE = re.compile(r"^\[(\d{1,2}):(\d{2}):(\d{2})\]")


def parse_ts(t) -> int:
    if isinstance(t, (int, float)):
        return int(t)
    if not t:
        return 0
    s = str(t).strip().strip("[]")
    parts = s.split(":")
    try:
        nums = [int(p) for p in parts]
    except ValueError:
        return 0
    if len(nums) == 3:
        return nums[0] * 3600 + nums[1] * 60 + nums[2]
    if len(nums) == 2:
        return nums[0] * 60 + nums[1]
    return nums[0] if nums else 0


def fmt_hms(sec: int) -> str:
    sec = max(0, int(sec))
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def fmt_hash(sec: int) -> str:
    sec = max(0, int(sec))
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}-{m:02d}-{s:02d}"


def is_bumper(title: str) -> bool:
    t = (title or "").lower().strip()
    if not t:
        return True
    if re.match(r"^(intro|outro|opening|closing|end credits|credits|theme|bumper)\b", t):
        return True
    if "welcome to the junkyard love" in t and len(t) < 55:
        return True
    if "drink some water" in t:
        return True
    if re.search(r"let'?s roll", t) and re.search(r"drink|water|hit record", t):
        return True
    if "hit record" in t and len(t) < 40:
        return True
    return False


def resolve_transcript_path(episode_slug: str, episode_number: str | None) -> Path | None:
    candidates = []
    if episode_slug in SLUG_ALIASES:
        candidates.append(CONTENT / SLUG_ALIASES[episode_slug] / "transcript.md")
    candidates.append(CONTENT / episode_slug / "transcript.md")
    if episode_number:
        for p in CONTENT.iterdir():
            if p.is_dir() and (
                p.name.startswith(f"{episode_number}-") or p.name == episode_number
            ):
                candidates.append(p / "transcript.md")
    seen = set()
    for path in candidates:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        if path.is_file():
            return path
    return None


def load_transcript_cues(path: Path) -> list[dict]:
    cues = []
    text = path.read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        m = CUE_RE.match(line)
        if m:
            h, mi, s, speaker, body = m.groups()
            sec = int(h) * 3600 + int(mi) * 60 + int(s)
            cues.append(
                {
                    "sec": sec,
                    "speaker": speaker.strip(),
                    "text": body.strip(),
                    "raw": line,
                }
            )
            continue
        # Continuation lines without timestamp — append to previous cue if any
        if cues and not TS_ONLY_RE.match(line) and not line.startswith("#"):
            cues[-1]["text"] = (cues[-1]["text"] + " " + line).strip()
            cues[-1]["raw"] = (cues[-1]["raw"] + " " + line).strip()
    return cues


def normalize_ws(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def load_wordlist() -> set[str]:
    if not WORDS_ALPHA.is_file():
        return set()
    words = set()
    with WORDS_ALPHA.open(encoding="utf-8", errors="ignore") as f:
        for line in f:
            w = line.strip().lower()
            if w:
                words.add(w)
    return words


WORD_RE = re.compile(r"[a-zA-Z']+")


def garbage_reason(text: str, wordlist: set[str]) -> str | None:
    """Return reason string if window looks like ASR garbage / empty."""
    t = normalize_ws(text)
    if not t:
        return "empty window"
    letters = sum(1 for ch in t if ch.isalpha())
    if letters < 40:
        return "too few letters"
    words = WORD_RE.findall(t.lower())
    if len(words) < 12:
        return "extremely short"
    # Excessive repeated tokens
    if words:
        counts = Counter(words)
        top_token, top_n = counts.most_common(1)[0]
        if top_n >= max(8, int(len(words) * 0.35)) and len(top_token) > 1:
            return "excessive repeated tokens"
    # Mostly non-words (skip if no wordlist)
    if wordlist and len(words) >= 12:
        alpha_words = [w for w in words if any(c.isalpha() for c in w)]
        if alpha_words:
            known = sum(1 for w in alpha_words if w in wordlist or len(w) <= 2)
            ratio = known / len(alpha_words)
            if ratio < 0.45:
                return "mostly non-words"
    return None


def extract_excerpt(text: str, min_words: int = 80, max_words: int = 160) -> str:
    """Trim to ~80–160 words of complete sentences near the start. No rewrite."""
    t = normalize_ws(text)
    if not t:
        return ""
    # Split into sentence-ish chunks on . ! ? while keeping delimiter
    parts = re.split(r"(?<=[.!?])\s+", t)
    sentences = [p.strip() for p in parts if p.strip()]
    if not sentences:
        words = t.split()
        return " ".join(words[:max_words])

    chosen: list[str] = []
    word_count = 0
    for sent in sentences:
        sw = sent.split()
        if not sw:
            continue
        # If first sentence alone exceeds max, trim at word boundary but prefer complete if possible
        if not chosen and len(sw) > max_words:
            # try to end at a later punctuation inside — otherwise take max_words
            return " ".join(sw[:max_words])
        if word_count + len(sw) > max_words and word_count >= min_words:
            break
        chosen.append(sent)
        word_count += len(sw)
        if word_count >= max_words:
            break
    if word_count < min_words and len(chosen) < len(sentences):
        # keep adding until min or out of sentences (may exceed max slightly to finish sentence)
        for sent in sentences[len(chosen) :]:
            sw = sent.split()
            chosen.append(sent)
            word_count += len(sw)
            if word_count >= min_words:
                break
    excerpt = " ".join(chosen).strip()
    # If still tiny, fall back to word trim
    if len(excerpt.split()) < 20:
        excerpt = " ".join(t.split()[:max_words])
    return excerpt


def youtube_url(youtube_id: str | None, start_seconds: int) -> str | None:
    if not youtube_id:
        return None
    t = max(0, int(start_seconds))
    return f"https://www.youtube.com/watch?v={youtube_id}&t={t}s"


def transcript_url(episode_slug: str, start_seconds: int) -> str:
    return f"episodes/{episode_slug}/index.html#t-{fmt_hash(start_seconds)}"


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    clips_data = json.loads((ASSETS / "clips_index.json").read_text(encoding="utf-8"))
    eps_data = json.loads((ASSETS / "episodes_index.json").read_text(encoding="utf-8"))
    clips = clips_data.get("clips") or []
    episodes = {e["slug"]: e for e in eps_data.get("episodes") or [] if e.get("slug")}
    duration_by_slug = {
        slug: int(ep.get("duration_seconds") or 0) for slug, ep in episodes.items()
    }

    # Group all clips by episode for end boundaries (include host_open for boundaries)
    by_ep: dict[str, list] = defaultdict(list)
    for c in clips:
        by_ep[c["episode_slug"]].append(c)
    for slug in by_ep:
        by_ep[slug].sort(key=lambda c: parse_ts(c.get("start_seconds", c.get("start"))))

    wordlist = load_wordlist()
    print(f"wordlist size: {len(wordlist)}")

    # Cache transcripts per episode
    cue_cache: dict[str, list | None] = {}
    transcript_path_cache: dict[str, Path | None] = {}
    gaps: list[dict] = []
    lean_entries: list[dict] = []
    search_entries: list[dict] = []

    indexed = 0
    skipped = 0

    # Candidates: non-host_open, non-bumper, not removed
    candidates = []
    for c in clips:
        if not c.get("title"):
            continue
        if c.get("episode_number") in REMOVED:
            continue
        if c.get("host_open"):
            continue
        if is_bumper(c.get("title") or ""):
            continue
        candidates.append(c)

    print(f"candidate chapters: {len(candidates)}")

    for c in candidates:
        slug = c["episode_slug"]
        start_sec = parse_ts(c.get("start_seconds", c.get("start")))
        # end = next chapter start in same episode
        ep_clips = by_ep[slug]
        end_sec = None
        for other in ep_clips:
            os_ = parse_ts(other.get("start_seconds", other.get("start")))
            if os_ > start_sec:
                end_sec = os_
                break
        if end_sec is None:
            end_sec = duration_by_slug.get(slug) or 0

        # Load transcript
        if slug not in cue_cache:
            path = resolve_transcript_path(slug, c.get("episode_number"))
            transcript_path_cache[slug] = path
            if path is None:
                cue_cache[slug] = None
            else:
                cue_cache[slug] = load_transcript_cues(path)

        cues = cue_cache[slug]
        if cues is None:
            gaps.append(
                {
                    "episode_slug": slug,
                    "episode_number": c.get("episode_number"),
                    "chapter_title": c.get("title"),
                    "start": fmt_hms(start_sec),
                    "reason": "missing transcript",
                }
            )
            skipped += 1
            continue

        if end_sec <= start_sec:
            # last chapter with unknown duration — use last cue + small pad or +600
            last_cue = cues[-1]["sec"] if cues else start_sec
            end_sec = max(last_cue + 1, start_sec + 1)

        window_cues = [q for q in cues if start_sec <= q["sec"] < end_sec]
        # If no cues in window but transcript exists, try expanding to include cue at start
        if not window_cues:
            # sometimes chapter start falls between cues — include last cue before start through end
            before = [q for q in cues if q["sec"] < start_sec]
            if before:
                # only if the previous cue is close (within 30s)
                if start_sec - before[-1]["sec"] <= 30:
                    window_cues = [before[-1]] + [
                        q for q in cues if start_sec < q["sec"] < end_sec
                    ]

        if not window_cues:
            gaps.append(
                {
                    "episode_slug": slug,
                    "episode_number": c.get("episode_number"),
                    "chapter_title": c.get("title"),
                    "start": fmt_hms(start_sec),
                    "end": fmt_hms(end_sec),
                    "reason": "empty window",
                }
            )
            skipped += 1
            continue

        # Verbatim text: speaker lines joined
        lines = []
        for q in window_cues:
            piece = q["text"]
            if q.get("speaker"):
                piece = f"{q['speaker']}: {piece}"
            lines.append(piece)
        full_text = normalize_ws(" ".join(lines))

        reason = garbage_reason(full_text, wordlist)
        if reason:
            gaps.append(
                {
                    "episode_slug": slug,
                    "episode_number": c.get("episode_number"),
                    "chapter_title": c.get("title"),
                    "start": fmt_hms(start_sec),
                    "end": fmt_hms(end_sec),
                    "reason": reason,
                }
            )
            skipped += 1
            continue

        # If duration still unknown for last chapter, set end from last cue in window
        if not duration_by_slug.get(slug) or end_sec <= start_sec:
            end_sec = max(window_cues[-1]["sec"] + 1, start_sec + 1)
        # Prefer episode duration when this is last chapter and duration known
        ep_dur = duration_by_slug.get(slug) or 0
        next_exists = any(
            parse_ts(o.get("start_seconds", o.get("start"))) > start_sec for o in ep_clips
        )
        if not next_exists and ep_dur > start_sec:
            end_sec = ep_dur
        elif not next_exists:
            end_sec = max(window_cues[-1]["sec"] + 30, start_sec + 60)

        excerpt = extract_excerpt(full_text)
        yt_id = c.get("youtube_id") or (episodes.get(slug) or {}).get("youtube_id")
        yt = youtube_url(yt_id, start_sec)

        lean = {
            "episode_number": c.get("episode_number"),
            "guest": c.get("guest") or "Solo",
            "chapter_title": c.get("title"),
            "start": fmt_hms(start_sec),
            "start_seconds": start_sec,
            "end": fmt_hms(end_sec),
            "end_seconds": end_sec,
            "episode_slug": slug,
            "transcript_url": transcript_url(slug, start_sec),
        }
        if yt:
            lean["youtube_url"] = yt
            lean["youtube_id"] = yt_id

        search_rec = dict(lean)
        search_rec["excerpt"] = excerpt
        search_rec["text"] = full_text

        lean_entries.append(lean)
        search_entries.append(search_rec)
        indexed += 1

    generated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lean_doc = {
        "generated": generated,
        "generator": "build_ask_junkyard.py",
        "base_url": BASE_URL,
        "chapter_count": len(lean_entries),
        "skipped_count": skipped,
        "candidate_count": len(candidates),
        "note": "Lean chapter windows for machines. Verbatim transcript search is in chapter_search.json (or shards). No invented summaries.",
        "chapters": lean_entries,
    }

    # Write lean index both places
    lean_json = json.dumps(lean_doc, ensure_ascii=False, indent=2)
    (ASSETS / "chapter_index.json").write_text(lean_json + "\n", encoding="utf-8")
    (SRC / "chapter_index.json").write_text(lean_json + "\n", encoding="utf-8")

    search_doc = {
        "generated": generated,
        "generator": "build_ask_junkyard.py",
        "chapter_count": len(search_entries),
        "skipped_count": skipped,
        "note": "Browser search corpus: verbatim chapter windows + excerpts. No LLM rewrite.",
        "chapters": search_entries,
    }
    search_json = json.dumps(search_doc, ensure_ascii=False, separators=(",", ":"))
    search_bytes = len(search_json.encode("utf-8"))
    print(f"search json ~{search_bytes} bytes; indexed={indexed} skipped={skipped}")

    # Clean prior shard dir / single file
    shard_dir = ASSETS / "chapter_search"
    src_shard_dir = SRC / "chapter_search"
    single_asset = ASSETS / "chapter_search.json"
    single_src = SRC / "chapter_search.json"

    if search_bytes <= SHARD_SOFT_LIMIT:
        single_asset.write_text(search_json + "\n", encoding="utf-8")
        single_src.write_text(search_json + "\n", encoding="utf-8")
        if shard_dir.exists():
            shutil.rmtree(shard_dir)
        if src_shard_dir.exists():
            shutil.rmtree(src_shard_dir)
        shard_mode = False
        shard_count = 0
    else:
        if single_asset.exists():
            single_asset.unlink()
        if single_src.exists():
            single_src.unlink()
        shard_dir.mkdir(parents=True, exist_ok=True)
        src_shard_dir.mkdir(parents=True, exist_ok=True)
        # Pack chapters into shards under soft limit
        shards = []
        current: list[dict] = []
        current_size = 200  # header overhead approx

        def chapter_size(rec: dict) -> int:
            return len(json.dumps(rec, ensure_ascii=False, separators=(",", ":")).encode())

        for rec in search_entries:
            sz = chapter_size(rec) + 1
            if current and current_size + sz > SHARD_SOFT_LIMIT:
                shards.append(current)
                current = []
                current_size = 200
            current.append(rec)
            current_size += sz
        if current:
            shards.append(current)

        manifest = {
            "generated": generated,
            "generator": "build_ask_junkyard.py",
            "chapter_count": len(search_entries),
            "shard_count": len(shards),
            "shards": [],
        }
        for i, chunk in enumerate(shards):
            name = f"shard-{i:02d}.json"
            body = {
                "generated": generated,
                "shard": i,
                "chapter_count": len(chunk),
                "chapters": chunk,
            }
            payload = json.dumps(body, ensure_ascii=False, separators=(",", ":")) + "\n"
            (shard_dir / name).write_text(payload, encoding="utf-8")
            (src_shard_dir / name).write_text(payload, encoding="utf-8")
            manifest["shards"].append({"file": name, "chapter_count": len(chunk)})

        man_json = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
        (shard_dir / "manifest.json").write_text(man_json, encoding="utf-8")
        (src_shard_dir / "manifest.json").write_text(man_json, encoding="utf-8")
        shard_mode = True
        shard_count = len(shards)

    # SEARCH_GAPS.md
    reason_counts = Counter(g["reason"] for g in gaps)
    lines = [
        "# Search gaps — Ask the Junkyard",
        "",
        f"Generated: {generated}",
        "",
        f"- Candidate chapters (non-host_open, non-bumper): **{len(candidates)}**",
        f"- Indexed: **{indexed}**",
        f"- Skipped: **{skipped}**",
        f"- Search emit: **{'sharded ×' + str(shard_count) if shard_mode else 'single chapter_search.json'}**",
        "",
        "## Skip reasons",
        "",
    ]
    for reason, n in reason_counts.most_common():
        lines.append(f"- `{reason}`: {n}")
    lines.extend(["", "## Skipped windows", ""])
    if not gaps:
        lines.append("_None._")
    else:
        lines.append("| episode | start | chapter | reason |")
        lines.append("|---|---|---|---|")
        for g in gaps:
            title = (g.get("chapter_title") or "").replace("|", "/")
            lines.append(
                f"| {g.get('episode_number') or ''} `{g.get('episode_slug')}` | {g.get('start')} | {title} | {g.get('reason')} |"
            )
    (REPORTS / "SEARCH_GAPS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Small stats sidecar for ship report
    stats = {
        "generated": generated,
        "indexed": indexed,
        "skipped": skipped,
        "candidates": len(candidates),
        "shard_mode": shard_mode,
        "shard_count": shard_count,
        "search_bytes": search_bytes,
        "reason_counts": dict(reason_counts),
    }
    (REPORTS / "ASK_JUNKYARD_STATS.json").write_text(
        json.dumps(stats, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
