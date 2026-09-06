import json
from pathlib import Path
j=json.loads(Path('/workspace/junkyard-love-archive/content/0033-andy-of-team-banzai/source-yt.en.json3').read_text())
raw=[]
for e in j['events']:
    segs=e.get('segs')
    if not segs: continue
    text=''.join(s.get('utf8','') for s in segs)
    if '<c>' in text: continue
    text=text.replace('\n',' ').strip()
    if not text: continue
    raw.append((e.get('tStartMs',0), text))
for needle in ['japan','team banzai','black diamond','ADHD','modular','tutorial','vibe','sound design','producer','LimeWire','Elton John','wash your hands','appreciate it','reel','middle school','house part','foreigner','explicit','Portland','synth','plugin','sampling','tattoo','festival','Burning Man',' DJ','engineer','mentor','mask']:
    hits=[]
    for t,tx in raw:
        if needle.lower() in tx.lower():
            hits.append((t,tx))
            if len(hits)>=2: break
    print('==', needle, '==')
    for t,tx in hits:
        print(f'  {t/1000:.0f}s {tx[:110]}')
