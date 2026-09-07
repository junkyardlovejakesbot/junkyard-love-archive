#!/workspace/.venv/bin/python3
"""Transcribe 0037 full RSS MP3 with faster-whisper small/int8; emit VTT + json3 + segments."""
from __future__ import annotations
import json, sys, time
from pathlib import Path

ROOT = Path('/workspace/junkyard-love-archive/content/0037-rebecca-wyld-habit-change-and-happiness-actualization')
AUDIO = ROOT / 'source-audio.mp3'
OUT_JSON = ROOT / 'whisper-segments.json'
OUT_VTT = ROOT / 'captions.en.vtt'
OUT_JSON3 = ROOT / 'captions.en.json3'
LOG = ROOT / 'whisper.log'
MODEL_NAME = 'small'
COMPUTE = 'int8'

def ms(t: float) -> int:
    return int(round(t * 1000))

def fmt_vtt(t: float) -> str:
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    return f'{h:02d}:{m:02d}:{s:06.3f}'

def main():
    from faster_whisper import WhisperModel
    t0 = time.time()
    with LOG.open('w') as log:
        def say(msg):
            print(msg, flush=True)
            log.write(msg + '\n'); log.flush()
        say(f'loading {MODEL_NAME}/{COMPUTE}… audio={AUDIO} size={AUDIO.stat().st_size}')
        model = WhisperModel(MODEL_NAME, device='cpu', compute_type=COMPUTE)
        say('transcribing…')
        segments, info = model.transcribe(
            str(AUDIO),
            language='en',
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
            word_timestamps=False,
            beam_size=5,
            best_of=5,
        )
        say(f'lang={info.language} prob={info.language_probability} duration={info.duration}')
        segs = []
        events = []
        vtt_lines = ['WEBVTT', '']
        n = 0
        for seg in segments:
            n += 1
            text = (seg.text or '').strip()
            if not text:
                continue
            start, end = float(seg.start), float(seg.end)
            segs.append({'start': start, 'end': end, 'text': text})
            events.append({
                'tStartMs': ms(start),
                'dDurationMs': max(ms(end - start), 1),
                'segs': [{'utf8': text + '\n'}],
            })
            vtt_lines.append(str(n))
            vtt_lines.append(f'{fmt_vtt(start)} --> {fmt_vtt(end)}')
            vtt_lines.append(text)
            vtt_lines.append('')
            if n % 50 == 0:
                say(f'… {n} segments @ {start:.1f}s elapsed={time.time()-t0:.0f}s')
        OUT_JSON.write_text(json.dumps({'duration': info.duration, 'model': MODEL_NAME, 'compute_type': COMPUTE, 'segments': segs}, ensure_ascii=False, indent=2))
        OUT_JSON3.write_text(json.dumps({'wireMagic': 'pb3', 'events': events}, ensure_ascii=False))
        OUT_VTT.write_text('\n'.join(vtt_lines) + '\n', encoding='utf-8')
        for name in ('captions.en-orig.vtt', 'source-audio.en.vtt'):
            (ROOT / name).write_text(OUT_VTT.read_text(encoding='utf-8'), encoding='utf-8')
        for name in ('captions.en-orig.json3', 'source-audio.en.json3'):
            (ROOT / name).write_text(OUT_JSON3.read_text(encoding='utf-8'), encoding='utf-8')
        caps = ROOT / 'captions'
        caps.mkdir(exist_ok=True)
        (caps / 'captions.en.vtt').write_text(OUT_VTT.read_text(encoding='utf-8'), encoding='utf-8')
        (caps / 'captions.en.json3').write_text(OUT_JSON3.read_text(encoding='utf-8'), encoding='utf-8')
        (caps / 'captions.en-orig.vtt').write_text(OUT_VTT.read_text(encoding='utf-8'), encoding='utf-8')
        (caps / 'captions.en-orig.json3').write_text(OUT_JSON3.read_text(encoding='utf-8'), encoding='utf-8')
        say(f'DONE model={MODEL_NAME}/{COMPUTE} segments={n} words≈{sum(len(s["text"].split()) for s in segs)} duration={info.duration:.2f}s elapsed={time.time()-t0:.0f}s')

if __name__ == '__main__':
    main()
