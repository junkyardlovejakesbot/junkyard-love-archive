# IndexNow

- key: `522ce9e3faeeaa7c0619b57b0277baa9`
- key file: `/522ce9e3faeeaa7c0619b57b0277baa9.txt` (published at site root)
- keyLocation: `https://junkyardlovejakesbot.github.io/junkyard-love-archive/522ce9e3faeeaa7c0619b57b0277baa9.txt`
- host: `junkyardlovejakesbot.github.io`
- submitted: 129 episode URLs, 100 guest URLs, plus the key file (230 total)
- endpoint: `https://api.indexnow.org/indexnow`

Ping ran after deploy. Response codes:

1. Immediately after the key file went live: **403** `SiteVerificationNotCompleted` (IndexNow asked to wait for verification).
2. 45 seconds later: **200** (empty body). Submission accepted.

Recorded 2026-11-11 08:39 UTC-06:00 (America/Chicago).

## 0126 ping (2026-11-13)

0126 was added in `d7f06b4` after the first IndexNow batch, so those URLs had not been submitted yet.

- submitted: 19 URLs (0126 episode page, episode.md, guest page, chapters JSON; episodes/guests/topics indexes and the three topic pages that list 0126; llms.txt; sitemap.xml; episodes_index.json; chapter_index.json; and the five related episode pages touched in the 0126 commit)
- endpoint: `https://api.indexnow.org/indexnow`
- response: **200** (empty body). Submission accepted.
- recorded 2026-11-13 07:14 America/Chicago.

