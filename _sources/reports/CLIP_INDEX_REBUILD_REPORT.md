# Clip index rebuild report

**Date:** 2026-09-07 6:58 AM CT (box UTC 11:58)
**Script:** `_sources/rebuild_clips_index.py`
**No git commit / no push.**

## Summary

| Metric | Value |
|---|---:|
| Episodes rebuilt | **120** |
| Total clips | **2422** |
| Host-open clips | **24** |
| Removed skipped | 0001, 0014, 0016, 0029 |

## Deliverables

- `_sources/clips_index.json` + `assets/clips_index.json`
- `_sources/episodes_index.json` + `assets/episodes_index.json` (chapters match clips)
- Archive picks chapter lists on every episode page
- `source-archive-picks.md` + `source-timestamps.md` per episode

## Rules applied

- Every chapter treated as a clip
- Produced intro bumper + produced outro excluded
- Host open labeled with real topic titles (not “intro”)
- Long one-word blob chapters split into tighter beats
- Short/long summaries paraphrased from transcript windows (no invented quotes)

## Hard / soft ASR notes

- 0102: published note says solo intro skip @11:03 — host-open/bumper handling may vary
- 0103: caption clocks stop ~01:34 while inventory duration ~1:48 — coverage capped by ASR
- Early catalog ASR (esp. 0002–0020): some auto titles/summaries stay soft — paraphrased only from transcript, not invented
- Some Host open titles are keyword-auto (e.g. “Yourself, Feeling & Care”) — hand labels welcome later via TITLE_OVERRIDES
- 0066 mid-show ASR labels cleaned from “Opening He’s”; remaining mid labels still auto

## Per-episode clip counts

| Ep | Clips | Host open | First clip | Last clip |
|---|---:|---:|---|---|
| 0002 | 13 | 0 | EYE Clothing cold open — raves & selling from th | Clothing, Permission & Community |
| 0003 | 21 | 0 | Friend, Yourself & Ladies | Today’s a good day to die — presence |
| 0004 | 17 | 0 | Opening — doctors / ADHD / medication stigmas | Sense / May |
| 0005 | 14 | 0 | Opening — growing up / age group / happiness | Allergies / diet / food and cognitive function |
| 0006 | 18 | 0 | Opening — live / Junkyard Love / Ryan intro | One life to live / smiling for joy |
| 0007 | 21 | 0 | Opening — welcome / Jessica Faul | Faul name / German pronunciation |
| 0008 | 18 | 0 | Opening — fist pump with Nate | Survivor mindset |
| 0009 | 18 | 0 | Opening — Junkyard Love / Shaden 'Hvshi' Nugent | Messages for listeners |
| 0010 | 16 | 0 | Opening — Junkyard Love / three DJs | Festivals / Kelly |
| 0011 | 19 | 0 | Echo chambers & online communication | Posture & standing up straight |
| 0012 | 20 | 0 | Bob Kendall cold open — third-person marketplace | Being the best version of yourself |
| 0013 | 18 | 0 | Opening — Kokanee / Sasquatch / Castle Rock | Protecting yourself / new-mom strength |
| 0015 | 15 | 0 | Opening — Junkyard Love / Jordanne Crane | Clean, sober, full of life / survivor story |
| 0017 | 18 | 0 | Spencer, Learn & Touch | Realizing / Thinking |
| 0018 | 17 | 0 | Opening — Nate Tanzman returns | Important / Life |
| 0019 | 21 | 0 | Opening — Kendall Johns / Dead Crown intro | Boy vs man — right time and place |
| 0020 | 18 | 0 | Opening — Megalodon / Megan Elam intro | Sleep, graveyard shifts & morning momentum |
| 0021 | 28 | 0 | Year, Baseball & Rosetan | Community / Friends |
| 0022 | 21 | 0 | Opening — Taya Sanders of Clover+Tribe | What's next / store hours / website |
| 0023 | 17 | 0 | Three kinds of empathy | Sensory deprivation / float tanks |
| 0024 | 16 | 0 | Introduce Maxx V. Payne | Where to find Maxx / close |
| 0025 | 21 | 0 | Chakras, Start & Healing | Conversations / Visualization |
| 0026 | 20 | 0 | Scott on mic | Basketball / Coffee |
| 0027 | 14 | 0 | Opening — Junkyard Love / Mackenzie | Bucket lists / Red Rocks dreams |
| 0028 | 34 | 0 | Beautiful Minds | Relationships without forcing meaning |
| 0030 | 21 | 0 | Touch, Subjects & Perfect | Archimedes / Eureka story |
| 0031 | 14 | 0 | Madi arrives — stoked to be here | Don't Medication Wis |
| 0032 | 16 | 0 | Andre — EYE Clothing as space-company front | Yourself / World |
| 0033 | 20 | 0 | Open — COVID / Mask Off banter | Vangelis / Blade Runner sound design |
| 0034 | 22 | 0 | Introducing Nate / backlog note | New levels / new devils |
| 0035 | 27 | 0 | Haflife, Comes & Place | Where to find Ryan / HAFLife ENT |
| 0036 | 19 | 0 | Journaling and gratitude | Enneagram 4 |
| 0037 | 25 | 0 | Conversation open — editing / being a beginner | Happiness without money stories |
| 0038 | 20 | 0 | Opening — virtual/remote Junkyard Love | Fantasy / Witcher / playground for the mind |
| 0039 | 18 | 1 | Host open — Yourself, Feeling & Care | Important / Outside |
| 0040 | 18 | 0 | Drink some water / hit record | Identity / attachment to jobs / career change |
| 0041 | 19 | 0 | Conversation begins | Corona Virus Lead |
| 0042 | 22 | 1 | Host open — Listening, Jessica & Mackenzie | Glass table talks / friendship |
| 0043 | 20 | 0 | Opening — mustache check / no formal intro | Skating / Joseph |
| 0044 | 19 | 0 | Drink some water / let's roll | Faith in humanity / optimistic close |
| 0045 | 21 | 1 | Host open — Might, Learning & Change | Boundaries / not staying reactive |
| 0046 | 20 | 0 | Episode start — we got JACE / podcast voice | Listening / Better |
| 0047 | 23 | 1 | Host open — Order, Universal & Entire | Everyone you meet knows something |
| 0048 | 21 | 1 | Host open — Contempt, Country & Society | Feeding / Life |
| 0049 | 18 | 0 | Home, School & Work | Give power to the positive |
| 0050 | 18 | 0 | Experience / Themselves | Twin flame / partnerships / frequency |
| 0051 | 21 | 1 | Host open — Grow, Towards & Choice | Balance — girlfriend Rachel / gym life |
| 0052 | 18 | 1 | Host open — Experience, Rikki & Sleep | Aliens Ufos Alternate Realities |
| 0053 | 25 | 1 | Host open — October, Yourself & Sober | Turned Music Driving |
| 0054 | 15 | 0 | Ask — Camp ReEducation origin | Understanding / Learning |
| 0055 | 24 | 0 | Live check / stream delay | Every Song Plays He's |
| 0056 | 15 | 1 | Host open — Year, Money & Water | Years ago / grocery-store stories |
| 0057 | 21 | 0 | Guest intro — Anna Cantwell | Learning / Yourself |
| 0058 | 22 | 0 | Host intro / Joe Dispenza recommendation | Fantastic / People's |
| 0059 | 21 | 1 | Host open — Human, Each & Progress | YouTube as free curiosity school |
| 0060 | 14 | 1 | Host open — Coffee, Caffeine & Days | Invite — next Sober October / stick to your guns |
| 0061 | 19 | 0 | Guest intro — Trevor May | Find that purpose |
| 0062 | 22 | 0 | Guest intro — Abrielle Dunn | Understand yourself / understand others |
| 0063 | 16 | 0 | Into the conversation | Change / World |
| 0064 | 19 | 0 | Social decorum after going digital | Unapologetic patience |
| 0065 | 19 | 0 | What have you been up to | What does the world need more of? |
| 0066 | 19 | 1 | Host open — Song, Background & Trying | What does the world need more of? |
| 0067 | 22 | 1 | Host open — Yourself, Keep & Jaycie | Intuitive / Finding |
| 0068 | 29 | 1 | Host open — Sense, Trying & Conversation | Expose Myself |
| 0069 | 17 | 1 | Host open — Smoking, Cigarette & Though | No one will do it for you — go get it |
| 0070 | 22 | 1 | Host open — Dealing, Beauty & Ryan | Life Goes |
| 0071 | 20 | 0 | What made you want to start this podcast | What the world needs — discipline |
| 0072 | 17 | 0 | Jacob YouTube intro — late start / fasting note | Megan — live events / presence / synchronicities |
| 0073 | 14 | 0 | Guests hello | Pushing All |
| 0074 | 17 | 0 | Into cancel culture — pop vs politics | Alan Watts backwards law / self-help |
| 0075 | 17 | 0 | Jacob welcome & Bradley intro | What the world needs — soft skills / psychology |
| 0076 | 15 | 0 | Opening clip — preventative mental health | Beautiful / Heather |
| 0077 | 18 | 1 | Host open — Cannabis, World & Episodes | What the world needs — more love |
| 0078 | 20 | 0 | Opening clip — leadership training Jerry wished  | Relationships / Leadership |
| 0079 | 15 | 0 | Opening clip — pickleball diversity / accessibil | pickleballfire.com resources |
| 0080 | 17 | 0 | Opening clip — uninterrupted listening / mediati | Leader within / speaking as a leader |
| 0081 | 14 | 0 | Bio ask | Advice — life is short / own path |
| 0082 | 18 | 0 | Einstein, Life & Work | Where to find Sandy / Prosperous podcast |
| 0083 | 18 | 1 | Host open — Depression, Sadness & Record | Depression Minutes May |
| 0084 | 14 | 0 | Mid-life crisis & hairpin curves | Where to find Jeremy / current work |
| 0085 | 13 | 0 | Studying human rights / trafficking sensitivity | Spreading the word / listener responsibility |
| 0086 | 19 | 1 | Host open — Episodes, Life & Conversations | Conversation chemistry over looks |
| 0087 | 17 | 0 | Opening — Zach Beach / yoga & poetry | Natural world / open heart |
| 0088 | 22 | 1 | Host open — Communication, Listening & Every | Company Stagehand |
| 0089 | 14 | 0 | Conversation, Buckminster & Resources | World Game not a world order |
| 0090 | 22 | 1 | Host open — Played, Yoga & Instagram | Work Free Work Live |
| 0091 | 16 | 0 | Nike bio — Legacy Enterprises; Austin from Lagos | Powered by possibility, not caged by fear |
| 0092 | 18 | 0 | Music, Yourself & Ableton | Rising From The Ashes — serpent / kundalini cros |
| 0093 | 21 | 1 | Host open — Health, Mental & Send | Malfunction ≠ identity — change who you are |
| 0094 | 16 | 0 | Jacob intro — delayed episode, Austin check-in | Thoughtful Species Type Thou |
| 0095 | 17 | 0 | Real, Stay & Position | Open mic — all genres welcome |
| 0096 | 17 | 0 | Opening banter — headset, pilots, welcome back | Experience / Speaking |
| 0097 | 19 | 0 | Opening — welcome and brief bio ask | Own truth in Jesus / faith as turning yourself o |
| 0098 | 17 | 0 | Opening — welcome and bio ask | Prison story / companion to yourself / Bhagavad  |
| 0099 | 23 | 0 | Opening — welcome and Loneliness of kundalini | Resources — BATGAP, Adyashanti, Yvonne Kason, Ma |
| 0100 | 25 | 1 | Host open — Spiritual, Against & Whether | Where to find Jacob — Instagram @jacobfromtheint |
| 0101 | 27 | 1 | Host open — Friends, Conversations & Keenan | Life Gets Stable |
| 0102 | 30 | 0 | Solo intro — Jacob’s at-home ketamine / BetterU  | Where to find BetterU — betterucare.com / @bette |
| 0103 | 17 | 0 | Opening — welcome Landon / bio ask | Remembering who you are / placing God outside th |
| 0104 | 20 | 0 | Opening — welcome Julie / “who are you” | Informal practice — peeling potatoes / silence i |
| 0105 | 24 | 0 | Opening — welcome Matt / “who are you” | Connected to the why / mission-driven |
| 0106 | 27 | 0 | Opening — better conversations / better conversa | Floating / traveler community / bridge connectio |
| 0107 | 20 | 0 | Opening — welcome Meredith & Craig | Road of Life Podcast + Instagram @meredithandcra |
| 0108 | 26 | 0 | Opening — better conversations / check-in with A | Escaping old ideas / Einstein: as simple as poss |
| 0109 | 24 | 0 | Opening — Junkyard Love check-in | Nine novels + three business books / A Time for  |
| 0110 | 27 | 0 | Opening — depression tools / welcome newcomers + | Meditation can reach the same place without psyc |
| 0111 | 28 | 0 | Opening — kids changed Nate’s relationship with  | Biggest money month → prayed remove it → lost cl |
| 0112 | 27 | 0 | Opening — welcome David Crayk / high-school thea | Don’t bargain with the inner voice / listen and  |
| 0113 | 29 | 0 | Opening — welcome Wendy / Demystifying the Trans | “Yep, you’re ready” / possibilities / resources |
| 0114 | 25 | 0 | Opening — welcome Ravinder / Mind Training intro | One day at a time / happiness now / problems res |
| 0115 | 28 | 0 | Opening — welcome Nate / voice actor & puppeteer | Megaphone to humanity — Kermit / do what you lov |
| 0116 | 29 | 0 | Opening — welcome Curtis / Junkyard Love | Finish the show / discuss later / move forward |
| 0117 | 29 | 0 | Opening — welcome Blake / Junkyard Love | Hope for humanity / ChatGPT as harm reduction |
| 0118 | 31 | 0 | Opening — Am I Bipolar or Waking Up? / Bipolar A | Untrained supporter does surrogate birth work |
| 0119 | 25 | 0 | Opening — welcome Trey / bone broth morning | Predetermined purpose / amnesia / this too shall |
| 0120 | 19 | 0 | Opening — what is awakening? | Pre-incarnation contracts tease / caterpillar co |
| 0121 | 25 | 0 | Perfect, Clears & Throat | Start and end prayer with gratitude |
| 0122 | 22 | 0 | Opening — unconscious vocal habits / TED spark | Courses, self-directed path, living/dying retrea |
| 0123 | 21 | 0 | Opening — elevator pitch / Junkyard Love framing | Website sign-off / cristinehull.com spelling |
| 0124 | 18 | 0 | Opening — welcome Sigmar Berg | One Journey the book and where to find Lovetuner |

## How to regenerate

```bash
cd junkyard-love-archive-deploy
python3 _sources/rebuild_clips_index.py
# optional: python3 _sources/rebuild_clips_index.py --only 0002,0124
```

## Confirm

- **No git commit / no push.**
- Branch `main` remains aligned with `origin/main` (local unstaged edits only; ahead/behind 0 0).
- `--only` merges into existing `clips_index.json` (does not wipe other episodes).
