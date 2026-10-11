"""Snap a clip start to the real start of speech so embeds never cut words.

Rule (archive standard): the embed starts at the beginning of the speaker turn
that the chapter opens on, read from the episode's own YouTube captions
(json3 or vtt in _sources/content/<folder>/). Look back up to 30s from the
published chapter time for a speaker change (">>"); if none, use the start of
the caption line containing the chapter time. Floor to whole seconds (YouTube
start= is integer), so playback begins slightly before the first word.

Usage: python3 _sources/snap_clip_start.py <content-folder> <published_seconds>
"""
import json, math, re, sys
from pathlib import Path

def events(folder):
    f = Path(folder)
    for j in sorted(f.rglob("*.json3")):
        d = json.loads(j.read_text())
        out = []
        for ev in d.get("events", []):
            w = "".join(s.get("utf8", "") for s in ev.get("segs", []) or [])
            if w.strip():
                out.append((ev.get("tStartMs", 0) / 1000, w))
        if out:
            return out
    for v in sorted(f.rglob("*.vtt")):
        out = []
        for m in re.finditer(r"(\d+):(\d\d):(\d\d)\.(\d+) -->.*?\n(.+?)(?:\n\n|\Z)", v.read_text(), re.S):
            h, mi, s, ms, txt = m.groups()
            out.append((int(h) * 3600 + int(mi) * 60 + int(s) + int(ms) / 1000, re.sub(r"<[^>]+>", "", txt)))
        if out:
            return out
    return []

def snap(folder, published, lookback=30):
    ev = events(folder)
    if not ev:
        return int(published), "no captions; kept published time"
    turns = [t for t, w in ev if published - lookback <= t <= published and ">>" in w]
    if turns:
        t = max(turns)
        return math.floor(t), f"speaker turn at {t:.2f}s"
    prior = [t for t, w in ev if t <= published + 0.5]
    t = max(prior) if prior else published
    return math.floor(t), f"caption line at {t:.2f}s"

if __name__ == "__main__":
    s, why = snap(sys.argv[1], float(sys.argv[2]))
    print(s, why)
