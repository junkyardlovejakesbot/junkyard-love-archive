# Junkyard Love — Quality Pass Catalog Audit

_Generated 2026-09-06 08:05 PM CT. Audit only — no episode page edits, no git commit/push._

**Scope:** published numbered episode dirs under `junkyard-love-archive-deploy/episodes/` with `index.html`.
Skipped: `0001/0014/0016/0029-removed` and unnumbered redirect stubs
(`surrendering-the-porsche-tim-fraley`, `what-if-mania-is-a-message-sean-blackwell`, `im-not-a-teacher-david-hulse`).

**Note on 0037:** may be mid ASR re-transcript (full RSS). This audit reflects **current on-disk files** only.

---

## Summary counts

| Metric | Count |
|---|---:|
| Episodes audited | 120 |
| `needs_browse_title` | 27 |
| `title_already_good` | 93 |
| Needs browse_title but no grounded candidate | 0 |
| Truncated chapter lists (<85% runtime / first-hour of 2h+) | 13 |
| Episodes with ≥1 fragment quote | 118 |
| Quotes total / fragment / OK | 1623 / 989 / 634 |
| Likely need Intro relabel (first turns) | 74 |
| Likely need Outro relabel (last turns) | 44 |
| Likely need Intro **and** Outro | 29 |
| Likely need Intro **or** Outro | 89 |

---

## 1. Browse titles (missing / needed)

Flagged when H1 is essentially **number + guest only** (or show-prefix + number + guest),
vs already carrying a real title phrase (e.g. *Surrendering The Porsche*, *Healing The Soul With Hands and Self Love*, *Same Room, Different Angles*).

Candidate `browse_title` proposed **only** when grounded in that page’s About first line / existing subtitle / Archive-picks chapter phrase (aim 4–10 words).
If published title is already real → `browse_title` = that title phrase.

### needs_browse_title (27)

| Ep | Current H1 | Candidate browse_title | Source |
|---:|---|---|---|
| 0002 | Episode 002 with Rob Gonzalez of EYE Clothing | Growth hard work vision and raves | about (verified) |
| 0003 | Episode 003 with Spencer Hicks | Ego mindfulness and consciousness | about |
| 0004 | Episode 004 with Zack Wyld of Wyld Productions | Community technology positive use | archive_chapters |
| 0005 | Episode 005 with Jaycie Randall | Goals presence meditation and plateaus | about+chapters (verified) |
| 0006 | Episode 006 with Ryan 'Tos' Santos | Always smiling friendship and shared history | about |
| 0007 | Episode 007 with Jessica Faul | Past pains laughs and future plans | about |
| 0008 | Episode 008 with Nate 'NastyNate' Tanzman | Ego as a beast | archive_chapters |
| 0009 | Episode 009 with Shaden 'Hvshi' Nugent | Colorado skater kid to rapper | archive_chapters (verified) |
| 0010 | Episode 010 with Brian 'Dj Toasty' Andrews and Kelly 'K3lls' St. Onge | DJ discipline assessing the next moves | about |
| 0011 | Episode 011 with Spencer Hicks | Echo chambers & online communication | archive_chapters |
| 0012 | Episode 012 with Bob Kendall | Being passionate about the product | archive_chapters |
| 0013 | Episode 013 with Nona Southard | Motherhood courage and reconnecting with yourself | about |
| 0015 | Episode 015 with Jordanne Crane | C-Diff survival storytelling and gratitude | about |
| 0017 | Episode 017 with Spencer Hicks | Free talk with Spencer again | archive_chapters (verified) |
| 0018 | Episode 018 with Nate 'NastyNate' Tanzman | Change room to breathe | archive_chapters |
| 0019 | Episode 019 with Kendall Johns of Dead Crown | Metalcore genre Dead Crown sound | archive_chapters |
| 0020 | Episode 020 with Megan Elam | Speech pathology career and belonging | about+chapters |
| 0021 | Episode 021 with "rosetan" the band | How the band got started | archive_chapters |
| 0022 | Episode 022 with Taya Sanders of Clover+Tribe | Herniated discs and handmade kids clothes | about+chapters (verified) |
| 0023 | Episode 023 with Spencer Hicks | Three kinds of empathy | archive_chapters |
| 0024 | Episode 024 with Maxx V. Payne | Rap music background & inspiration | archive_chapters |
| 0025 | Episode 025 with Jordenelle Tsugawa | Natural healer and mystical knowledge | about (verified) |
| 0026 | Episode 026 with Scott Pisapia of Roots Basketball Academy | Clear Eyes Full Hearts Can't Lose | about_lead_quote (verified) |
| 0027 | Episode 027 with Mackenzie Thornquist | DJ sets live music and nightlife | about+chapters (verified) |
| 0028 | Episode 028 with Yanis 'Kanideis' Pisarchuk | The importance of music | archive_chapters |
| 0031 | Episode 031 with Madi Allis of Vail Denim | Growth and allowing room to change | archive_chapters (verified) |
| 0033 | The Junkyard Love Podcast Episode 033 with Andy of Team Banzai | Team Banzai at Black Diamond Studio | archive_chapters (verified) |

### title_already_good (93) — browse_title = existing title phrase

<details><summary>Expand full list</summary>

| Ep | browse_title (from H1) | Full H1 (trimmed) |
|---:|---|---|
| 0030 | Mathematics, Science, Quantum Physics and Unlocking The Universe | Episode 030 with Kelly St. Onge - Mathematics, Science, Quantum Physics  |
| 0032 | The dreamers mindset, building a real foundation, enjoying the j | Episode 032 with Andre Gilbert and Roberto Gonzalez - The dreamers minds |
| 0034 | Healing Toxic Masculinity, Male Vulnerability, Believing In Your | Episode 034 with Nate 'NastyNate' Tanzman - Healing Toxic Masculinity, M |
| 0035 | Hope, Ambition, Fortitude, Unlimited Beliefs, Putting Yourself O | Episode 035 with Ryan Reed - Hope, Ambition, Fortitude, Unlimited Belief |
| 0036 | Sharpening Your Emotional Toolkit Through Writing, Grit, Gratitu | Episode 036 with Mika Woodruff - Sharpening Your Emotional Toolkit Throu |
| 0037 | Habit Change and Happiness Actualization | Episode 037 with Life Coach Rebecca Wyld of Wyld Wellness - Habit Change |
| 0038 | Mental and Physical Tips To Maintain Health At Home | Episode 038 with Spencer Hicks   Mental and Physical Tips To Maintain He |
| 0039 | A Small Town Sound With Heart | Episode 039 with Erik Nordin of Rosetan - A Small Town Sound With Heart |
| 0040 | Formulating Perspective From Behind The Lens, Cognitive Change W | Episode 040 with Brandon Cruz - Formulating Perspective From Behind The  |
| 0041 | Views From Consciousness and The Great Neural Net of Humanity | Episode 041 with Brandon Cruz - Views From Consciousness and The Great N |
| 0042 | The Last Saturday: Small Town Minds Evolving and An Attitude | Episode 042 with Mack T and J Faul - The Last Saturday: Small Town Minds |
| 0043 | wait why are you taking me seriously? | Episode 043 with Joseph Crumb - Redefining your life and - wait why are  |
| 0044 | Operating Optimally Should Be Your Goal | Episode 044 with Spencer Hicks - Operating Optimally Should Be Your Goal |
| 0045 | How To Take Care Of Yourself A Bit | Episode 045   Solo with Jacob Rhines   How To Take Care Of Yourself A Bi |
| 0046 | Killing The Ego and Stumbling Onto The Right Path | Episode 046 with Rapper JACE Saltzman - Killing The Ego and Stumbling On |
| 0047 | Searching For Fluidity, Learning From Detail, and Laughing With  | Episode 047 with Trenten Kesler - Searching For Fluidity, Learning From  |
| 0048 | Being Kind, Flipping Perspective and Drinkin' Water | Episode 048 with Devon Sims - Being Kind, Flipping Perspective and Drink |
| 0049 | The Ever Evolving Chameleon, Vibe Surfing, Weird A | Episode 049 with Airik Makaio Hokulani Mobbs - The Ever Evolving Chamele |
| 0050 | Healing The Soul With Hands and S | Episode 050 with Starseed and Reiki Worker Jordenelle Tsugawa - Healing  |
| 0051 | Hard Work and Heavy We | Episode 051 with Electrician and Competitive Powerlifter Ricky Navarrete |
| 0052 | Chest Pressure, Intrusive Thoughts, and Space Aliens | Episode 052 with Rikki Hall - Chest Pressure, Intrusive Thoughts, and Sp |
| 0053 | How To Build Confidence And Create Your Own Luck | Episode 053 with Matt Young and Nate Tanzman - How To Build Confidence A |
| 0054 | You Don't Know What You Think You Already Know | Episode 054 with Ian and Shaye of Camp ReEducation - You Don't Know What |
| 0055 | Life Has No Sync Button | Episode 055 with Brian 'DJ Toasty' Andrew - Life Has No Sync Button |
| 0056 | Get With The Picture, Grow Through It, And Laugh | Episode 056 with Trevir Petitt & Jasmine Heagy - Get With The Picture, G |
| 0057 | A Teacher Of The Human Spirit | Episode 057 with Soul Coach and Mindfulness Expert Anna Cantwell - A Tea |
| 0058 | People Are Portals To Yourself | Episode 058 with Conner Anshutz - People Are Portals To Yourself |
| 0059 | The Sense Making Sickness | Episode 059 - The Sense Making Sickness - with Spencer Hicks - Series Pa |
| 0060 | Sober October - A Personal Mental Review | Episode 060 - Solo with Jacob Rhines - Sober October - A Personal Mental |
| 0061 | Finding The Feel | Episode 061 with MLB Player/Twitch Streamer Trevor May - Finding The Fee |
| 0062 | 062 with Abrielle Dunn - Aspiring Towards Inspiration, Creating  | 062 with Abrielle Dunn - Aspiring Towards Inspiration, Creating Connecti |
| 0063 | Life, Loss, and Dogs | Episode 063 with Shiloh Rister & Georgia Peach - Life, Loss, and Dogs |
| 0064 | Bumping Elbows With Leaders, Censorship and New Norms | The JYLP Episode 064 with Tyler Milliken - Bumping Elbows With Leaders,  |
| 0065 | It's Open Mic Night For Being Yourself | The JYLP Episode 065 with Josh Gebhardt - It's Open Mic Night For Being  |
| 0066 | Writin' Songs, Lentin' Booze and Upgradin' Society | The JYLP Episode 066 with Tim Fraley - Writin' Songs, Lentin' Booze and  |
| 0067 | A Path From The Past | The JYLP Episode 067 with Intuitive Healer Jaycie Randall - A Path From  |
| 0068 | Wait Why Are We LARPing | The JYLP Episode 068 with Abrielle Dunn - The Sense Making-Sickness Seri |
| 0069 | Trimming Off What No Longer Serves You | The JYLP Episode 069 with Crystal Nyman - Trimming Off What No Longer Se |
| 0070 | The Wiring Within The Walls | The JYLP Episode 070 with Ryan 'Tos' Santos - The Wiring Within The Wall |
| 0071 | Forward Is The Only Way | The JYLP Episode 071 with Ryan Baker - Forward Is The Only Way |
| 0072 | Social Creatures Having An Internet Experience | The JYLP Episode 072 with Megan Robinson - Social Creatures Having An In |
| 0073 | Sex, Pleasure, Relationship-Blueprints, and Orgasms | The JYLP episode 073 with Alicia & Erwan Davon - Sex, Pleasure, Relation |
| 0074 | Ep 074 with Spencer Hicks - Dialectics and Communication Breakdo | Ep 074 w/ Spencer Hicks - Dialectics and Communication Breakdown - A Met |
| 0075 | Being Most People Is Bad For Your Health | The JYLP Episode 075 with Bradley Roth - Being Most People Is Bad For Yo |
| 0076 | Seeing More Clearly | The JYLP Episode 076 with Singer/Songwriter & Blind Author Heather Hutch |
| 0077 | A Friendly Conversation About Weed | JYLP Episode 077 w/ Cannabis Industry Consultant Devin Mullins - A Frien |
| 0078 | Be Free From The Fear Of Conflict | The JYLP Episode 078 with Conflict Resolution Coach Jerry Fu - Be Free F |
| 0079 | EP079 with Guest Lynn Cherry of Pickleball Fire - "Here, | The JYLP EP079 W/ Guest Lynn Cherry of Pickleball Fire - "Here, Use My P |
| 0080 | 080 with Relationship Practitioner, Mediator, and Author Juli Ge | The JYLP 080 with Relationship Practitioner, Mediator, and Author Juli G |
| 0081 | EP081 with philosophical contemplator John Lee - Pondering The B | The JYLP EP081 with philosophical contemplator John Lee - Pondering The  |
| 0082 | 082 with Yogi & Meditation Teacher Sandy Vo - Towards | 082 with Yogi & Meditation Teacher Sandy Vo - Towards A Path Of Peace |
| 0083 | 083 - a solocast - Making Sense Of My Depression | 083 - a solocast - Making Sense Of My Depression & Anxiety pt. 1 |
| 0084 | 084 with Science Researcher, Writer, and Biosemiotician Jeremy S | The JYLP 084 with Science Researcher, Writer, and Biosemiotician Jeremy  |
| 0085 | 085 with Bachelor of Science/Masters In Human Rights Cetvies Cet | 085 w Bachelor of Science/Masters In Human Rights Cetvies Cetvies - Cens |
| 0086 | - 086 with Mika Woodruff - The Individuals Innate Desire | The JYLP - 086 with Mika Woodruff - The Individuals Innate Desire For Be |
| 0087 | 087 Yogi, Author, Poet, Love Coach & Masters in East/West | 087 Yogi, Author, Poet, Love Coach & Masters in East/West Psychology Zac |
| 0088 | ep. 088 with Bachelor In Arts Of Strategic Communication Spencer | The JYLP ep. 088 with Bachelor In Arts Of Strategic Communication Spence |
| 0089 | 089 with Social Impact Investor and Organizational Strategist Da | 089 with Social Impact Investor and Organizational Strategist Daniel T.  |
| 0090 | Ep 090 with B.S. in Psychology Will Andes - Being | The JYLP Ep 090 with B.S. in Psychology Will Andes - Being Boys, Becomin |
| 0091 | 091 with Speaker, Author, and Family Business Consultant Nike An | 091 with Speaker, Author, and Family Business Consultant Nike Anani |
| 0092 | A Complicated Historical Paradigm | The JYLP Episode 092 with Roman Merrell of 'RFTA Podcast' - A Complicate |
| 0093 | I Know Great Men Stuck In Costumes Of Sadness | The JYLP Episode 093 - I Know Great Men Stuck In Costumes Of Sadness |
| 0094 | Acid, Intellect, Money, and Morality | The JYLP Episode 094 with 1/3 Billionaire John Lefebvre - Acid, Intellec |
| 0095 | ep 095 with Rapper & CEO Bobby Barrz - The | The JYLP ep 095 with Rapper & CEO Bobby Barrz - The Only Real Game In To |
| 0096 | ep 096 with Jordenelle Tsugawa - The Forever Umbilical Cord, | The JYLP ep 096 with Jordenelle Tsugawa - The Forever Umbilical Cord, An |
| 0097 | Fighting For Sobriety | The JYLP Episode 097 with Kevin Foreman - Fighting For Sobriety |
| 0098 | 098 with Swami Nityananda - Be Still, As The Universe | 098 with Swami Nityananda - Be Still, As The Universe Plays Through You |
| 0099 | A Kundalini Awakening Story | The Junkyard Love Podcast Episode 099 with Brent Spirit - A Kundalini Aw |
| 0100 | 0100 JacobFromTheInternet - Mystical Experience And Spiritual Pr | 0100 JacobFromTheInternet - Mystical Experience And Spiritual Practice T |
| 0101 | 0101 with Keenan 'Hurricane' Harvey - Taking Care Of What | The JYLP 0101 with Keenan 'Hurricane' Harvey - Taking Care Of What You C |
| 0102 | 0102 with Megan Hawkins From 'BetterU' Psychedelic Therapy - Ket | 0102 with Megan Hawkins From 'BetterU' Psychedelic Therapy - Ketamine To |
| 0103 | 0103 with Landon 'Dirtyzen' Smith - Breaking Into The Abyss | 0103 with Landon 'Dirtyzen' Smith - Breaking Into The Abyss |
| 0104 | Awakening From The Lucid Dream | The JYLP Episode 0104 with Author and Spiritual Coach Julie Hoyle - 'Awa |
| 0105 | 0105 with Tutor and Educational Consultant Matt McGee - How | The JYLP 0105 w Tutor and Educational Consultant Matt McGee - How To Sta |
| 0106 | Ep 0106 with Connector and Operations Manager Cameron 'Cam' Reid | The JYLP Ep 0106 with Connector and Operations Manager Cameron 'Cam' Rei |
| 0107 | - 0107 with Marriage Coaches Meredith and Craig Bennett - | The JYLP - 0107 with Marriage Coaches Meredith and Craig Bennett - Marri |
| 0108 | Always Evolution Occurs | The JYLP Episode 0108 - with Author of 'The Human Idea' Anne Riley - 'Al |
| 0109 | 0109 Retired Navy SEAL combat veteran, Author, CEO - Marty | JYLP 0109 Retired Navy SEAL combat veteran, Author, CEO - Marty Strong - |
| 0110 | Turning The Lights On | The JYLP Episode 0110 with Rebecca Wild - Turning The Lights On |
| 0111 | - 0111 with Nate Tanzman - Father | The JYLP - 0111 with Nate Tanzman - Father |
| 0112 | 0112 with David Crayk - 'True Teachings' - Interviewing My | The JYLP 0112 with David Crayk - 'True Teachings' - Interviewing My High |
| 0113 | 'Later Bloom' | 'Later Bloom' - a conversation with Transition Mentor Wendy Cole - The J |
| 0114 | From Chronic Pain To Inner Power | From Chronic Pain To Inner Power - with Psychotherapist, Hypnotherapist, |
| 0115 | 0115 with Voice Actor, Puppeteer, Storyteller, and Sound Produce | 0115 with Voice Actor, Puppeteer, Storyteller, and Sound Producer Nate B |
| 0116 | Same Room, Different Angles | The Junkyard Love Podcast Episode 0116 w Curtis L. Harnagel - Same Room, |
| 0117 | E 0117 with Blake Hull - Good morning, Blakey Boy | The Junkyard Love Podcast E 0117 with Blake Hull - Good morning, Blakey  |
| 0118 | What If Mania Is a Message? / Sean Blackwell on | What If Mania Is a Message? / Sean Blackwell on Bipolar, Trauma & Awaken |
| 0119 | The Story Of Trey Jones – From Prison Overdose to | The Story Of Trey Jones – From Prison Overdose to Witness State - The Ju |
| 0120 | "I'm Not A Teacher, I'm A Reminder" David Hulse and | "I'm Not A Teacher, I'm A Reminder" David Hulse and The Path To No Path |
| 0121 | Surrendering The Porsche | Surrendering The Porsche - A Conversation on Masculine Drive, Spiritual  |
| 0122 | Laughing Like a Hairy Oaf - Simple and playful ways | Laughing Like a Hairy Oaf - Simple and playful ways to free your real vo |
| 0123 | Endorphins, Love, Quantum Medicine, & the Four Bodies Model with | Episode 0123: Endorphins, Love, Quantum Medicine, & the Four Bodies Mode |
| 0124 | Adding 'A Conscious Breathing Break' To Your Daily Vocabulary | Adding 'A Conscious Breathing Break' To Your Daily Vocabulary - Episode  |

</details>

**needs_browse_title episode numbers:** 0002, 0003, 0004, 0005, 0006, 0007, 0008, 0009, 0010, 0011, 0012, 0013, 0015, 0017, 0018, 0019, 0020, 0021, 0022, 0023, 0024, 0025, 0026, 0027, 0028, 0031, 0033

---

## 2. Truncated chapter lists

Compared last Archive-picks / Chapters timestamp to page/inventory duration.
Flagged when last chapter is well before ~85% of runtime, or only covers the first hour of a 2h+ show.

| Ep | Duration | Chapters | Last chapter | Last title (trim) | Issue |
|---:|---|---:|---|---|---|
| 0003 | 1:19:46 | 14 | 00:54:32 (68%) | ADHD | last chapter at 68% of runtime (<85%) |
| 0012 | 1:07:13 | 17 | 00:55:49 (83%) | How to love your job | last chapter at 83% of runtime (<85%) |
| 0020 | 2:04:52 | 10 | 01:38:14 (79%) | [01:38:14] — Saying no / implementing change  | last chapter at 79% of runtime (<85%) |
| 0027 | 1:47:19 | 7 | 01:11:36 (67%) | What's the Difference between a Regular Set a | last chapter at 67% of runtime (<85%) |
| 0028 | 1:41:15 | 26 | 00:57:47 (57%) | Communicate with yourself | last chapter at 57% of runtime (<85%) |
| 0037 | 2:20:45 | 24 | 01:54:56 (82%) | Social anxiety / depression — YT cut near end | last chapter at 82% of runtime (<85%) |
| 0056 | 2:08:25 | 14 | 01:29:16 (70%) | America / melting pot / racism | last chapter at 70% of runtime (<85%) |
| 0079 | 48:00 | 13 | 00:39:27 (82%) | Juniors Leagues | last chapter at 82% of runtime (<85%) |
| 0080 | 1:01:08 | 14 | 00:35:36 (58%) | Common ground | last chapter at 58% of runtime (<85%) |
| 0085 | 1:01:32 | 10 | 00:45:34 (74%) | Role of journalists amid fake news & conflict | last chapter at 74% of runtime (<85%) |
| 0086 | 1:53:05 | 12 | 01:06:26 (59%) | Crying, suppression & emotional honesty | last chapter at 59% of runtime (<85%) |
| 0087 | 1:27:14 | 12 | 00:55:09 (63%) | Yoga etymology — science & spirituality | last chapter at 63% of runtime (<85%) |
| 0095 | 1:48:41 | 12 | 00:56:30 (52%) | Answer the call — prepare so opportunity does | last chapter at 52% of runtime (<85%) |

**Episode numbers:** 0003, 0012, 0020, 0027, 0028, 0037, 0056, 0079, 0080, 0085, 0086, 0087, 0095

---

## 3. Fragment quotes

Archive picks Quotes (and published Quotes when present): mid-clause scraps
(no terminal punctuation, starts lowercase mid-thought, obvious truncation, or <~8 words without being a proverb).

**Catalog-wide:** 989 fragment / 634 OK of 1623 quotes across 120 episodes.
**Episodes with any fragment:** 118/120.

Early-catalog Archive picks are almost entirely ASR slice scraps; later episodes improve somewhat but many still lack terminal punctuation.

### Worst offenders (highest fragment count)

| Ep | Frag / Total | Sample worst scraps |
|---:|---|---|
| 0108 | 18/20 | “identify your values live them that's it” · “you get to be the expert on you” · “morality is a human construct nature doesn't have” |
| 0109 | 17/20 | “Chance favors the prepared mind” · “thank you for your service now what” · “we train much harder … for combat than combat tends to be” |
| 0107 | 15/17 | “don't settle don't settle” · “vulnerability is actually a superpower in your relationship” · “so it sounds like marriages like plants need sunlight and water” |
| 0008 | 12/12 | “exactly it would feed my ego” · “single thing that I value was gone now Who am I so happy where is yeah…” · “obviously like a pretty in shape do bar you are you a coach - are you …” |
| 0028 | 12/12 | “who maybe still are punching walls what do” · “Absolutely and yeah it's communicate with yourself man tell yourself m…” · “Your storytelling and I think that storytelling is important I think s…” |
| 0036 | 12/12 | “Positive feelings of self-worth and your” · “I'm kind of having a depression day and” · “thinking it as like a plan B or a plan Z” |
| 0038 | 12/12 | “like to definitely remember to breathe as well but yeah I would say fo…” · “irritable like I flipped my sleep schedule back around I feel a lot be…” · “when you were I love fantasy I love fantasy like me personally but as …” |
| 0046 | 12/12 | “Possibility of opportunity right you” · “have a problem i'm about a solution that's how i am” · “after i showed you the BIG MAD because the BIG MAD it's like we out” |
| 0053 | 12/12 | “thinking differently better mind better lifestyle” · “now i feel like the cost of entry” · “me grounded a lot is i'm just a baker that found bread” |
| 0106 | 12/15 | “laughter is not for yourself like laughter is for connection” · “you meet up with someone you realize you're living about six miles dee…” · “we're all sitting in the living room watching The Simpsons … but I als…” |
| 0110 | 12/20 | “will you do the healing for me no” · “you can absolutely get to the same place with it” · “will you turn the light on and I did and I stayed” |
| 0050 | 11/11 | “did that and to just forgive it don't hold it” · “especially being a starseed i'm not from here so it is uncomfortable” · “that i grew i drink copper water um i like i try to” |
| 0004 | 11/12 | “it first but um the bromance so” · “for a true sense of community and” · “around this room with my camera one day and show you how cool it is” |
| 0005 | 11/12 | “changing people are growing up have you” · “there's not a lot of present people mm-hmm you” · “group like we're just trying to make something different happen a diff…” |
| 0009 | 11/12 | “the money my man that dark place that you're in right now that's just …” · “up just has a little punk-ass skater kid I was always pretty smart and…” · “scheming and I've been writing songs since I was like 12 but I mean th…” |
| 0018 | 11/12 | “but consistency and accountability so” · “got that yes and then patience being patient with” · “the deepest depths of depression and what it is to” |
| 0019 | 11/12 | “talk about the lyric writing process because for me like you” · “We're like we're metalcore band okay yes like metalcore I guess is lik…” · “future of things yeah 401k and retirement all that crap oh dude I was …” |
| 0020 | 11/12 | “you recently moved to Portland” · “undergad is working at Starbucks” · “development was the Spartan Race” |
| 0022 | 11/12 | “s of Clover+Tribe” · “students that were at risk for” · “Inspirational it's not Mike Wazowski yes” |
| 0024 | 11/12 | “did a cipher a whole HAFLife Ent Cipher where it” · “when I used to go to church you know there's c i remember there's like…” · “that was the first benefit concert that we ever put on war oh well if …” |
| 0026 | 11/12 | “was on a team that coach but I” · “believe it's called agoraphobia maybe where you're in like a public si…” · “like hey there was a zombie apocalypse where would you go just so I ha…” |
| 0027 | 11/12 | “yeah I remember before Odesza was even like a” · “different tours you can do scuba diving one of my favorite places that…” · “Meaning they had enough flight attendants in those bases for the amoun…” |
| 0031 | 11/12 | “more than this like ADHD threat” · “he has the power to influence many lives and I” · “angry and really short patience is that a word patience no well I” |
| 0037 | 11/12 | “going out into nature literally saved my life these things” · “that's a big one yeah own it you have to own it if it's your truth own…” · “of my the back of my neck pain was my eyes and in like so I would star…” |
| 0039 | 11/12 | “this you know being quarantine is a” · “just want people to be safe want people to be well” · “four B's are be safe be caring be responsible and be productive” |

### Episodes with relatively cleaner quotes (more OK than fragment, ≥5 quotes)

0057, 0058, 0060, 0062, 0079, 0082, 0087, 0091, 0093, 0094, 0095, 0096, 0100, 0102, 0104, 0111, 0112, 0113, 0114, 0115, 0116, 0117, 0118, 0119, 0120, 0121, 0122, 0123, 0124

<details><summary>Per-episode fragment vs OK counts</summary>

| Ep | Frag | OK | Total |
|---:|---:|---:|---:|
| 0002 | 9 | 1 | 10 |
| 0003 | 10 | 0 | 10 |
| 0004 | 11 | 1 | 12 |
| 0005 | 11 | 1 | 12 |
| 0006 | 9 | 2 | 11 |
| 0007 | 9 | 3 | 12 |
| 0008 | 12 | 0 | 12 |
| 0009 | 11 | 1 | 12 |
| 0010 | 0 | 0 | 0 |
| 0011 | 10 | 2 | 12 |
| 0012 | 10 | 1 | 11 |
| 0013 | 10 | 2 | 12 |
| 0015 | 8 | 4 | 12 |
| 0017 | 10 | 2 | 12 |
| 0018 | 11 | 1 | 12 |
| 0019 | 11 | 1 | 12 |
| 0020 | 11 | 1 | 12 |
| 0021 | 9 | 1 | 10 |
| 0022 | 11 | 1 | 12 |
| 0023 | 10 | 2 | 12 |
| 0024 | 11 | 1 | 12 |
| 0025 | 9 | 3 | 12 |
| 0026 | 11 | 1 | 12 |
| 0027 | 11 | 1 | 12 |
| 0028 | 12 | 0 | 12 |
| 0030 | 10 | 2 | 12 |
| 0031 | 11 | 1 | 12 |
| 0032 | 8 | 4 | 12 |
| 0033 | 10 | 2 | 12 |
| 0034 | 10 | 2 | 12 |
| 0035 | 9 | 3 | 12 |
| 0036 | 12 | 0 | 12 |
| 0037 | 11 | 1 | 12 |
| 0038 | 12 | 0 | 12 |
| 0039 | 11 | 1 | 12 |
| 0040 | 11 | 1 | 12 |
| 0041 | 11 | 1 | 12 |
| 0042 | 11 | 1 | 12 |
| 0043 | 10 | 2 | 12 |
| 0044 | 10 | 2 | 12 |
| 0045 | 11 | 1 | 12 |
| 0046 | 12 | 0 | 12 |
| 0047 | 10 | 2 | 12 |
| 0048 | 10 | 2 | 12 |
| 0049 | 10 | 1 | 11 |
| 0050 | 11 | 0 | 11 |
| 0051 | 9 | 3 | 12 |
| 0052 | 11 | 1 | 12 |
| 0053 | 12 | 0 | 12 |
| 0054 | 9 | 1 | 10 |
| 0055 | 10 | 0 | 10 |
| 0056 | 8 | 2 | 10 |
| 0057 | 9 | 13 | 22 |
| 0058 | 7 | 11 | 18 |
| 0059 | 8 | 2 | 10 |
| 0060 | 3 | 7 | 10 |
| 0061 | 9 | 1 | 10 |
| 0062 | 9 | 10 | 19 |
| 0063 | 7 | 3 | 10 |
| 0064 | 8 | 2 | 10 |
| 0065 | 9 | 4 | 13 |
| 0066 | 5 | 4 | 9 |
| 0067 | 9 | 9 | 18 |
| 0068 | 9 | 1 | 10 |
| 0069 | 10 | 1 | 11 |
| 0070 | 8 | 2 | 10 |
| 0071 | 8 | 8 | 16 |
| 0072 | 9 | 1 | 10 |
| 0073 | 9 | 1 | 10 |
| 0074 | 9 | 1 | 10 |
| 0075 | 7 | 5 | 12 |
| 0076 | 7 | 3 | 10 |
| 0077 | 10 | 0 | 10 |
| 0078 | 7 | 5 | 12 |
| 0079 | 4 | 6 | 10 |
| 0080 | 8 | 2 | 10 |
| 0081 | 9 | 1 | 10 |
| 0082 | 6 | 12 | 18 |
| 0083 | 9 | 1 | 10 |
| 0084 | 9 | 1 | 10 |
| 0085 | 7 | 1 | 8 |
| 0086 | 5 | 3 | 8 |
| 0087 | 1 | 7 | 8 |
| 0088 | 6 | 4 | 10 |
| 0089 | 7 | 1 | 8 |
| 0090 | 7 | 1 | 8 |
| 0091 | 2 | 8 | 10 |
| 0092 | 6 | 5 | 11 |
| 0093 | 3 | 5 | 8 |
| 0094 | 6 | 10 | 16 |
| 0095 | 2 | 6 | 8 |
| 0096 | 3 | 5 | 8 |
| 0097 | 6 | 4 | 10 |
| 0098 | 8 | 5 | 13 |
| 0099 | 5 | 5 | 10 |
| 0100 | 2 | 10 | 12 |
| 0101 | 7 | 3 | 10 |
| 0102 | 6 | 11 | 17 |
| 0103 | 6 | 4 | 10 |
| 0104 | 6 | 8 | 14 |
| 0105 | 9 | 3 | 12 |
| 0106 | 12 | 3 | 15 |
| 0107 | 15 | 2 | 17 |
| 0108 | 18 | 2 | 20 |
| 0109 | 17 | 3 | 20 |
| 0110 | 12 | 8 | 20 |
| 0111 | 7 | 24 | 31 |
| 0112 | 4 | 18 | 22 |
| 0113 | 4 | 22 | 26 |
| 0114 | 1 | 24 | 25 |
| 0115 | 8 | 19 | 27 |
| 0116 | 4 | 25 | 29 |
| 0117 | 4 | 30 | 34 |
| 0118 | 5 | 25 | 30 |
| 0119 | 4 | 30 | 34 |
| 0120 | 3 | 26 | 29 |
| 0121 | 8 | 16 | 24 |
| 0122 | 4 | 23 | 27 |
| 0123 | 1 | 23 | 24 |
| 0124 | 0 | 16 | 16 |

</details>

---

## 4. Intro/outro mislabeled as speakers

Sampled first 2 and last 2 transcript turns per episode. Flagged when turns are labeled Jacob/Guest
but read like produced open (welcome bumper / formula cold-open) or produced close
(outro CTA / “Junkyard Love out” / drink-water / subscribe close).

- **Likely Intro relabel:** 74 episodes
- **Likely Outro relabel:** 44 episodes
- **Either:** 89 · **Both:** 29

Early episodes that start mid-conversation (no bumper) are generally **not** flagged for Intro.

### Intro candidates

0021, 0023, 0024, 0025, 0026, 0027, 0028, 0030, 0031, 0032, 0034, 0035, 0036, 0037, 0039, 0040, 0041, 0042, 0044, 0045, 0046, 0047, 0048, 0049, 0050, 0051, 0052, 0053, 0054, 0055, 0056, 0057, 0058, 0059, 0060, 0061, 0062, 0063, 0064, 0065, 0067, 0068, 0069, 0070, 0071, 0072, 0073, 0074, 0075, 0087, 0090, 0092, 0094, 0095, 0097, 0098, 0099, 0102, 0103, 0104, 0105, 0106, 0107, 0108, 0109, 0110, 0111, 0112, 0113, 0116, 0117, 0118, 0119, 0124

### Outro candidates

0013, 0015, 0021, 0025, 0026, 0032, 0034, 0038, 0044, 0048, 0049, 0051, 0052, 0054, 0057, 0058, 0059, 0063, 0064, 0065, 0066, 0067, 0068, 0072, 0076, 0078, 0079, 0080, 0081, 0083, 0090, 0092, 0096, 0097, 0098, 0101, 0103, 0107, 0115, 0117, 0118, 0121, 0123, 0124

### Sample first/last turns (representative)

#### 0002 — intro_flag=False outro_flag=False

**First 2:**
- `Jacob`: Roberto Rob bet though that Gonzalez I'm a man of many names a man of many names man the owner of EYE Clothing I'm finally I'm pumped to fin
- `Rob`: Company out of your trunk of your outie so when I had like four designs - yeah right well did everybody was happy to rep you because everybo

**Last 2:**
- `Rob`: Using an app YouTube Spotify whatever
- `Jacob`: That autoplay is to the next thing just be conscious of your day today if you don't have all day to be spending on your phone or listening t

#### 0005 — intro_flag=False outro_flag=False

**First 2:**
- `Jacob`: You know what is that like it seems like a lot of our age group people are changing people are growing up have you
- `Jaycie`: Noticed that ya know it's super I don't know so much is changing but I feel like so for so long like generations prior I've just kind of lik

**Last 2:**
- `Jacob`: Yeah I appreciate you coming well thank you so much all right guys have a good
- `Jaycie`: Rest your day

#### 0023 — intro_flag=True outro_flag=False

**First 2:**
- `Jacob`: Hello and welcome to the junkyard knowledge is power ahoy that is the new intro if you haven't heard it yet I'm gonna leave it a minute long
- `Spencer`: Should stop obsessing over sounds fine this is what it was before yeah this one hey this sounds good I had to dive deep and make sure that a

**Last 2:**
- `Jacob`: Good thing for I don't know everything yes be kind to yourself the kind yourself take care of yourself I hope you guys benefit from the advi
- `Spencer`: My

#### 0037 — intro_flag=True outro_flag=False

**First 2:**
- `Jacob`: Hello and welcome to the junkyard knowledge is power what's up guys welcome to the junk hair love podcast today's recommendation is in the f
- `Jacob`: Reach out to the ones who are you know not dealing so well with being at home you know look out for each other take care yourself let's get 

**Last 2:**
- `Rebecca`: Like the I'm gonna I'm gonna take you through this journey of like my inner being through music but it's going to
- `Jacob`: Point out things in your inner being you know and I think that like there's so much power in that when it comes to music like music because 

#### 0050 — intro_flag=True outro_flag=False

**First 2:**
- `Jacob`: Hello and welcome to the Junkyard Love podcast with ourselves 50 episodes today i'm releasing my 50th episode of the Junkyard Love Podcast a
- `Jacob`: Get to experience each other from another level we really get to learn about each other on another level i mean that's been the biggest thin

**Last 2:**
- `Jordenelle`: Casual that's perfect that's how we make community yeah let's message each other so listener if you want to experience this if you want to k
- `Jacob`: Yeah thank you so much this was so great yeah thank you i feel like lighter as well so it's like it's like i feel like counseling it's like 

#### 0080 — intro_flag=False outro_flag=True

**First 2:**
- `Juli`: One will be the one to tell their story Using their own words however they want to tell and the other is invited to listen carefully and rea
- `Jacob`: Ladies and gentlemen hello i hope you're well I have Juli here with me today um Juli you want to go ahead and give me Let's start out with k

**Last 2:**
- `Jacob`: Think we all have a light inside of us and find that light inside of yourself and that light is meant to shine positive energy on others rig
- `Jacob`: Drink some water stretch and uh check out Juli's book have a good rest your day thank you Junkyard Love Podcast At what age do we learn how 

#### 0102 — intro_flag=True outro_flag=False

**First 2:**
- `Jacob`: What you're listening to right now is just an intro with me if you would like to skip that intro feel free man value your time go ahead and 
- `Jacob`: We'll assume going into the podcast that I've basically given you like a Partial introduction but I think I'll probably spend you know 5-10 

**Last 2:**
- `Megan`: Www.betterucare.com uh you can schedule An intro call with somebody from our team where like I said briefly before they'll walk you through 
- `Jacob`: This was you know even better than I could have expected so I'm so again grateful for your time grateful for everybody over at BetterU um yo

#### 0121 — intro_flag=False outro_flag=True

**First 2:**
- `Tim`: Good morning, brother. It's
- `Jacob`: [laughter] It's uh It's wonderful to have you on here again, man. Uh if anybody who is listening remembers Tim from before, you can go check

**Last 2:**
- `Tim`: Totally open.
- `Jacob`: Yeah, sure. Yeah. All right, Tim Fraley. I appreciate you, brother. Have a good rest of your day. Listeners, you know the drill. If you are 

<details><summary>All flagged intro/outro snippets</summary>

**0013**
- OUTRO [Jacob] (produced_close): Be nice all right Junkyard Love Podcast out

**0015**
- OUTRO [Jacob] (produced_close): Absolutely all right well be brave everybody have a good rest your day Junkyard Love Podcast out

**0021**
- INTRO [Jacob] (produced_open): Hello my lovely listeners happy whatever day of the week it is that you're listening to this I just wanted to give you a
- OUTRO [Jacob] (produced_close): Roastin do good do good and be good Junkyard Love podcasts out

**0023**
- INTRO [Jacob] (produced_open): Hello and welcome to the junkyard knowledge is power ahoy that is the new intro if you haven't heard it yet I'm gonna le

**0024**
- INTRO [Jacob] (produced_open): Hello and welcome to the Junkyard Love podcast at what age do we learn how to have better conversations at what age do w

**0025**
- INTRO [Jacob] (produced_open): Hello and welcome to the Junkyard Love Podcast. Hello and welcome aliens and alienates and humans and primates and zombi
- OUTRO [Jacob] (produced_close): Thank you. Have a good rest of your day listeners. Drink some water, take care of yourself.

**0026**
- INTRO [Jacob] (produced_open): Hello and welcome to the Junkyard Love what's up party people this is Jacob from the internet today's recommendation as 
- OUTRO [Jacob] (produced_close): Junkyard Love podcasts out Ethos DiGiorno's Caressa daimyo Shibui Scott

**0027**
- INTRO [Jacob] (produced_open): Hello and welcome to the junkyard what is Bracken my bros welcome to the podcast right before we get going you know I'd 

**0028**
- INTRO [Jacob] (produced_open): Hello and welcome to the Junkyard Love my friends today's recommendation before the podcast gets going is in the form of

**0030**
- INTRO [Jacob] (produced_open): Hello and welcome to the Junkyard Love what's up guys welcome to the junkyard love podcast today's recommendation due to

**0031**
- INTRO [Jacob] (produced_open): Hello and welcome to the junkyard hello my very best to you and yours Junkyard Love Podcast recommendation before we get

**0032**
- INTRO [Jacob] (produced_open): Hello welcome to the Junkyard Love OMI dudes in my dudettes welcome to the Junkyard Love pot yes where before we get goi
- OUTRO [Jacob] (produced_close): Care of yourself listeners have a good rest of your day don't care of

**0034**
- INTRO [Jacob] (produced_open): Hello and welcome to the junkyard hello me mates welcome to the junkyard of podcast today's recommendation is in the for
- OUTRO [Jacob] (produced_close): Yeah I'm gonna call it yeah hey guys hope you enjoyed the episode just want to quickly touch by and ask of course if you

**0035**
- INTRO [Jacob] (produced_open): Hello and welcome to the Junkyard Love what is cracking my brows welcome to the Junkyard Love Podcast this is Jacob Rhin

**0036**
- INTRO [Jacob] (produced_open): Hello and welcome to the junkyard boy hello welcome to the Junkyard Love podcast today's recommendations before we get k

**0037**
- INTRO [Jacob] (produced_open): Hello and welcome to the junkyard knowledge is power what's up guys welcome to the junk hair love podcast today's recomm

**0038**
- OUTRO [Jacob] (produced_close): Listeners have a good rest of your day please focus on your posture and all these other things that we mentioned and Spe

**0039**
- INTRO [Jacob] (produced_open): Hello and welcome to the junkyard guys hello welcome I hope you are well I hope you are well today's recommendation as I

**0040**
- INTRO [Jacob] (produced_open): Hello and welcome to the Junkyard Love

**0041**
- INTRO [Jacob] (produced_open): Hello and welcome to the junkyard hello welcome to the Junkyard Love Podcast I hope y'all are very well I hope you takin

**0042**
- INTRO [Jacob] (produced_open): Hello and welcome to the Junkyard Love no I like to do self-improvement type stuff I like to learn I like to shove knowl
- INTRO [Jacob] (produced_open): Something definitely worth pointing out in taking a look at and kind of listening to if you're listening to anything tha

**0044**
- INTRO [Jacob] (produced_open): Hello and welcome to the junkyard hello hello welcome to the Junkyard Love podcast today's recommendation before said po
- OUTRO [Jacob] (produced_close): Listener drink some water and if you have a stretch today man what it like what's wrong with you what are you doing you 

**0045**
- INTRO [Jacob] (produced_open): Hello and welcome to the junkyard knowledge is power let's get loose you got to do yellow welcome to the Junkyard Love P

**0046**
- INTRO [Jacob] (produced_open): Hello and welcome to the Junkyard Love podcast at what age do we learn how to have better conversations at what age do w

**0047**
- INTRO [Jacob] (produced_open): Hello, and welcome to the Junkyard Love Podcast. Oh, what is Gucci, my dude skis? This is the Junkyard Love Podcast. Tod

**0048**
- INTRO [Jacob] (produced_open): Hello and welcome to the junkyard hey guys I hope you're doing well Shaylee and I are just in the car now we're heading 
- OUTRO [Jacob] (produced_close): All right thank you bro appreciate that listeners drink some water bring some water drink more water don't eat till 2 o'

**0049**
- INTRO [Jacob] (produced_open): Hello and welcome to the Junkyard Love podcast with ourselves my friends it's me and it's you and we're listening to the
- OUTRO [Jacob] (produced_close): Love you too folks if you enjoyed the Episode please share just follow like subscribe Any of those things whatever's rel

**0050**
- INTRO [Jacob] (produced_open): Hello and welcome to the Junkyard Love podcast with ourselves 50 episodes today i'm releasing my 50th episode of the Jun

**0051**
- INTRO [Jacob] (produced_open): Hello and welcome to the Junkyard Love podcast at what age do we learn how to have better conversations at what age do w
- OUTRO [Jacob] (produced_close): No problem man thanks for having me yeah you bet man we'll have to do this again sometime heck yeah listeners get in tha

**0052**
- INTRO [Jacob] (produced_open): Hello and welcome to the Junkyard Love podcast at what age do we learn how to have better conversations at what age do w
- OUTRO [Jacob] (produced_close): Drink some water do some pilates do some yoga do something take care of yourselves have a good day ahoy guys i hope you 

**0053**
- INTRO [Jacob] (produced_open): Hello and welcome to the Junkyard Love podcast at what age do we learn how to have better conversations at what age do w

**0054**
- INTRO [Jacob] (produced_open): Hello and welcome to the Junkyard Love podcast at what age do we learn how to have better conversations at what age shou
- OUTRO [Shaye] (produced_close): Yeah i edit how Ian however Ian however smart Ian sounds that's how i edit him to sound all right all right fellas well 

**0055**
- INTRO [Jacob] (produced_open): Hello and welcome to the Junkyard Love Podcast At what age do we learn how to have Better conversations At what age do w
- INTRO [Brian] (produced_open): Watch our live stream on saturday if you're listening to this beforehand we would love to have you hope you have a good 

**0056**
- INTRO [Jacob] (produced_open): Hello and welcome to the Junkyard Love podcast at what age do we learn how to have better conversations at what age do w

**0057**
- INTRO [Jacob] (produced_open): Hello and welcome to the Junkyard Love Podcast At what age do we learn how to have Better conversations At what age do w
- OUTRO [Jacob] (produced_close): Well listeners take care of yourself uh I'm gonna end this recording but and i will talk for another couple minutes but 

**0058**
- INTRO [Jacob] (produced_open): Hello and welcome to the Junkyard Love Podcast At what age do we learn how to Have better conversations at what age shou
- OUTRO [Jacob] (produced_close): If you haven't drank any water today what are you doing drink some water take care of yourself stay hydrated stay high h

**0059**
- INTRO [Jacob] (produced_open): Hello and welcome to the Junkyard Love
- OUTRO [Jacob] (produced_close): It's free so is youtube so that goes pretty well you just gotta engage in it yeah so check out some things literally typ

**0060**
- INTRO [Jacob] (produced_open): Hello and welcome to the Junkyard Love Podcast at what age do we learn how to have better conversations at what age do w

**0061**
- INTRO [Jacob] (produced_open): Hello and welcome to the Junkyard Love Podcast At what age do we learn how to have Better conversations At what age do w

**0062**
- INTRO [Jacob] (produced_open): Hello and welcome to the Junkyard Love Podcast At what age do we learn how to have Better conversations At what age do w

**0063**
- INTRO [Jacob] (produced_open): Hello and welcome to the Junkyard Love Podcast At what age do we learn how to have Better conversations At what age do w
- OUTRO [Jacob] (produced_close): Yeah you betcha we will uh we'll catch up soon i'll send you a text a little bit later today okay Listeners have a good 

**0064**
- INTRO [Jacob] (produced_open): Hello and welcome to the Junkyard Love Podcast At what age do we learn how to have Better conversations At what age do w
- OUTRO [Jacob] (produced_close): All right tyler have a good rest of your day Listeners drink some water Stretch and love yourself be a little more patie

**0065**
- INTRO [Jacob] (produced_open): Hello and welcome to the Junkyard Love Podcast At what age do we learn how to have Better conversations At what age do w
- OUTRO [Jacob] (produced_close): All right have a good day buddy all right talk to you soon bye right Hey guys i hope you enjoyed the episode If you coul

**0066**
- OUTRO [Jacob] (produced_close): Listeners take care of yourself drink some water do some stretches um hug your friends next time you see them how about 

**0067**
- INTRO [Jacob] (produced_open): Hello and welcome to the Junkyard Love Podcast At what age do we learn how to have Better conversations At what age do w
- OUTRO [Jacob] (produced_close): You need to get some all right we got to end this podcast because you need to go drink some water my friend you're corre

**0068**
- INTRO [Jacob] (produced_open): Hello all welcome to the Junkyard Love Podcast It's me your host Jacob Rhines i'm happy you are here this is episode num
- OUTRO [Jacob] (produced_close): Man i appreciate it Listeners take care of yourself drink some water love yourself practice gratitude practice compassio

**0069**
- INTRO [Jacob] (produced_open): Hello and welcome to the Junkyard Love Podcast At what age do we learn how to have Better conversations At what age do w

**0070**
- INTRO [Jacob] (produced_open): Hey hello how are you welcome to The Junkyard Love Podcast it's me your host Dwayne the Rock Johnson's stunt double I'm 

**0071**
- INTRO [Jacob] (produced_open): Hello and welcome to the Junkyard Love Podcast With ourselves No Knowledge is power Well we're good to go Ryan Baker hel

**0072**
- INTRO [Jacob] (produced_open): What's up y'all welcome to the Junkyard Love Podcast i'm happy you're here if you're joining me on YouTube and you're wa
- OUTRO [Jacob] (produced_close): Good rest today Listeners take care of yourselves drink some water do a little stretching Uh you know look at the back o

**0073**
- INTRO [Jacob] (produced_open): Hello and welcome to the junkyard love podcast at what age do we learn how to have better conversations at what age do w

**0074**
- INTRO [Jacob] (produced_open): Hello and welcome to the Junkyard Love

**0075**
- INTRO [Jacob] (produced_open): Hello and welcome to the Junkyard Love Podcast
- INTRO [Jacob] (produced_open): At what age do we learn how to have better conversations At what age do we learn to have better conversations with ourse

**0076**
- OUTRO [Jacob] (produced_close): We'll be in touch I'll send you some emails and keep you posted when this has come out you have a good rest your day hea

**0078**
- OUTRO [Jerry] (produced_close): Please uh continue the dialogue even after the podcast is over yeah definitely man we'll have to stay in touch um so yea

**0079**
- OUTRO [Jacob] (produced_close): Love yourselves drink some water stretch Take care of yourselves go explore the community check it out have a have a smi

**0080**
- OUTRO [Jacob] (produced_close): Drink some water stretch and uh check out Juli's book have a good rest your day thank you Junkyard Love Podcast At what 

**0081**
- OUTRO [Jacob] (produced_close): Yeah sounds good man we'll uh We'll be in touch via email and whatnot and we'll uh we'll get together again okay sounds 

**0083**
- OUTRO [Jacob] (produced_close): There's a video about depression and anxiety i hope my ramblings help somebody uh i will continue to will continue to do

**0087**
- INTRO [Jacob] (produced_open): Knowledge is power Welcome to the Junkyard Love Podcast Ladies and gentlemen I'm here with Zach Beach welcome Zach

**0090**
- INTRO [Jacob] (produced_open): Hello beautiful people welcome to the Junkyard Love Podcast it is I Andrew Tate's great grandmother I'm happy you're her
- OUTRO [Jacob] (produced_close): Everybody love yourself drink some water stretch um and yeah just uh you know love your family be a little more present 

**0092**
- INTRO [Jacob] (produced_open): Hello and welcome to the Junkyard Love podcast at what age should we learn to have better conversations with ourselves k
- OUTRO [Roman] (produced_close): Man I'll talk to you soon buddy it's so much love I hope you have a good rest of your day buddy you brother thanks thank

**0094**
- INTRO [Jacob] (produced_open): Hello everyone welcome to the Junkyard Love Podcast it's me your host Jacob I'm happy that you are here this is an Episo

**0095**
- INTRO [Jacob] (produced_open): Hello and welcome to the Junkyard Love Podcast s learn to have better conversations with ourselves knowledge is power br

**0096**
- OUTRO [Jacob] (produced_close): Please follow Jay on Instagram she's a wonderful follow she Posts great things every day and she also has a Linktree wit

**0097**
- INTRO [Jacob] (produced_open): Hello and welcome to the junkyard love podcast at what age do we learn to have better conversations with ourselves knowl
- OUTRO [Jacob] (produced_close): Listeners love yourselves peace out

**0098**
- INTRO [Jacob] (produced_open): At what age do we learn how to have better conversations at what age should we learn to have better conversations with o
- OUTRO [Jacob] (produced_close): Have a good rest of your day listeners have a good rest of your day as well love yourself drink some water and uh see th

**0099**
- INTRO [Jacob] (produced_open): At what age do we learn how to have better conversations at what age do we learn to have better conversations with ourse

**0101**
- OUTRO [Jacob] (produced_close): A good conversation as always but I really appreciate the opportunity yeah excellent cool um all right listeners you kno

**0102**
- INTRO [Jacob] (produced_open): What you're listening to right now is just an intro with me if you would like to skip that intro feel free man value you

**0103**
- INTRO [Jacob] (produced_open): Hello and welcome to the junkyard love podcast Landon it's such a pleasure to meet you uh you know in Zoom person and uh
- OUTRO [Jacob] (produced_close): Cool all right well listeners love yourselves take care of yourselves if you drank no water today you're crazy drink som

**0104**
- INTRO [Jacob] (produced_open): Hello and welcome to the junkyard love podcast what age do we learn how to have better conversations at what age do we l

**0105**
- INTRO [Jacob] (produced_open): Hello and welcome to the junkyard love podcast listeners welcome to the junkyard love podcast today I'm here with Matt M

**0106**
- INTRO [Jacob] (produced_open): Junkard love podcast at what age do we learn how to have better conversations at what age do we learn to have better con

**0107**
- INTRO [Jacob] (produced_open): Love podcast at what age do we learn how To have better conversations the recording is in progress learn hello Meredith 
- OUTRO [Jacob] (produced_close): Yeah listeners love yourself drink Some water if you haven't drank any water set a date day up with your husband or your

**0108**
- INTRO [Jacob] (produced_open): Junkyard love podcast at what age do we learn how to have better conversations at what age do we learn to have better co

**0109**
- INTRO [Jacob] (produced_open): Junkyard love podcast at what age do we learn how to have better convers a real junkard love podcast

**0110**
- INTRO [Jacob] (produced_open): Hello and welcome to the junkyard love podcast I listen to this morning um you had an episode on your podcast I forgive 

**0111**
- INTRO [Jacob] (produced_open): Hello and welcome to the Junkyard Love Podcast. Well, I kind of interrupted you by hitting record. My apologies there, m

**0112**
- INTRO [Jacob] (produced_open): Junkyard Love podcast. At what age do we learn how to have better comprehensive Junkyard Love podcast? David Crayk, welc

**0113**
- INTRO [Jacob] (produced_open): Junkyard Love Podcast. At what age do we learn how to be a better ... conversation? Junkyard Love Podcast. So, what I wo

**0115**
- OUTRO [Jacob] (produced_close): Cool. All right. Well, everybody, uh, I'm going to hit end on this record here. Drink some water. Stretch. Hydrate. Do y

**0116**
- INTRO [Jacob] (produced_open): Hello and welcome to the Junkyard Love.

**0117**
- INTRO [Jacob] (produced_open): Hello and welcome to the Junkyard Love. Hey, everything's going to be all right. It's all good. It's all good. The Junky
- OUTRO [Jacob] (produced_close): Yeah. Start meditating. Uh listener, drink some water. If you have drank no water today, I don't care what time it is. T

**0118**
- INTRO [Jacob] (produced_open): Hello and welcome to the Junkyard Love. Hey, everything's going to be all right. It's all good. It's all good. The Junky
- OUTRO [Jacob] (produced_close): All right, man. Well, hey, I'm wishing you the best. Thank you again so much for your time. I hope you have a good rest 

**0119**
- INTRO [Jacob] (produced_open): Hello and welcome to the Junkyard Love. Hey, everything's going to be all right. It's all good. It's all good. The Junky

**0121**
- OUTRO [Jacob] (produced_close): Yeah, sure. Yeah. All right, Tim Fraley. I appreciate you, brother. Have a good rest of your day. Listeners, you know th

**0123**
- OUTRO [Jacob] (produced_close): Cool, love it. Well, thanks one more time. Everybody, listen to more Cristine, check out more of her stuff, read more of

**0124**
- INTRO [Jacob] (produced_open): Well, Sigmar, welcome to the Junkyard Love podcast, man. Thank you one more time for your time. I appreciate you.
- OUTRO [Jacob] (produced_close): Okay. That one's already out. Okay. So it's already out. They can get it now. Cool. Yeah. All right, brother, I'm going 

</details>

---

## Priority order recommendation

1. **Browse titles for thin early H1s** (0002, 0003, 0004, 0005, 0006, 0007, 0008, 0009, 0010, 0011, 0012, 0013, 0015, 0017, 0018, 0019, 0020, 0021, 0022, 0023, 0024, 0025, 0026, 0027, 0028, 0031, 0033) — highest listing/UX win; use grounded candidates; manually title none (all thin eps now have grounded candidates).
2. **Fragment quote rewrite pass** — start with worst offenders (highest frag/total, especially early Archive-picks ASR scraps); replace with complete sentences from transcript or drop; short proverb-like lines OK.
3. **Truncated chapters** — extend coverage for: 0003, 0012, 0020, 0027, 0028, 0037, 0056, 0079, 0080, 0085, 0086, 0087, 0095. Prefer through ~outro; **0037 may wait** until ASR re-transcript settles.
4. **Intro/Outro speaker relabel** — batch-relabel produced opens/closes to `Intro`/`Outro` (~74 intros, ~44 outros). Lower risk mechanically; do after title/quote copy so spot-checks stay clean.
5. **0037 special** — re-audit chapters/quotes/transcript labels after full RSS ASR lands.

---

## Method notes

- Titles: H1 with show-prefix/`w/` normalize; `Episode N with Guest` without thematic phrase → `needs_browse_title`.
- Chapters: `ul.chapters` under Archive picks preferred; else published Chapters.
- Duration: page `p.meta` first, else `inventory.csv` `duration_seconds`.
- Quotes: Archive `blockquote.archive-quote` + published Quotes blockquotes.
- Transcript: first/last two `p.cue` speaker labels + text.

_Audited 120 episodes from `/workspace/junkyard-love-archive-deploy/episodes`._
