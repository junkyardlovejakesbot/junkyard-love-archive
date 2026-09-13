(function () {
  "use strict";

  var INDEX_URL = "assets/episodes_index.json";
  var CLIPS_URL = "assets/clips_index.json";
  var clipsCache = null;
  var REMOVED = { "0001": 1, "0014": 1, "0016": 1, "0029": 1 };
  var cache = null;

  function baseHref() {
    var b = document.querySelector("base");
    return b ? b.getAttribute("href") || "" : "";
  }

  function abs(path) {
    if (!path) return path;
    if (/^https?:\/\//i.test(path) || path.charAt(0) === "#") return path;
    return baseHref() + path.replace(/^\//, "");
  }


  function loadClips() {
    if (clipsCache) return Promise.resolve(clipsCache);
    return fetch(abs(CLIPS_URL))
      .then(function (r) {
        if (!r.ok) throw new Error("clips " + r.status);
        return r.json();
      })
      .then(function (data) {
        var list = (data.clips || data || []).filter(isPoolClip);
        clipsCache = { raw: data, clips: list };
        return clipsCache;
      });
  }

  function clipFromIndexCard(c, opts) {
    opts = opts || {};
    var startSec = parseTs(c.start_seconds != null ? c.start_seconds : c.start);
    var hash = "#t-" + fmtTs(startSec);
    var epUrl = abs("episodes/" + c.episode_slug + "/index.html");
    var guest = c.guest || "Solo";
    var yt = c.youtube_id
      ? "https://www.youtube.com/watch?v=" + c.youtube_id + "&t=" + Math.floor(startSec) + "s"
      : null;
    var html = '<div class="clip-card"><h3>' + esc(c.title) + "</h3>";
    html +=
      '<p class="clip-ep">' +
      "Episode " +
      esc(c.episode_number || "") +
      " · " +
      esc(guest) +
      " · starts " +
      esc(fmtHuman(startSec)) +
      "</p>";
    // short_summary / long_summary intentionally hidden until a later extract pass
    html += '<div class="btn-row">';
    if (yt) {
      html +=
        '<a class="btn" href="' +
        esc(yt) +
        '" target="_blank" rel="noopener">Play this clip on YouTube</a>';
    } else {
      html += '<a class="btn" href="' + esc(epUrl + hash) + '">Open at this chapter</a>';
    }
    html +=
      '<a class="secondary" href="' +
      esc(epUrl + hash) +
      '">Read this moment in the transcript</a>';
    html += '<a class="secondary" href="' + esc(epUrl) + '">Full episode</a>';
    html += "</div></div>";
    return html;
  }

  function filterClipsByTerms(clips, terms) {
    terms = (terms || []).map(function (t) { return String(t).toLowerCase(); });
    if (!terms.length) return clips.slice();
    return clips.filter(function (c) {
      var hay = ((c.title || "") + " " + ((c.topic_tags || []).join(" ")) + " " + (c.browse_title || "") + " " + (c.guest || "")).toLowerCase();
      for (var i = 0; i < terms.length; i++) {
        if (hay.indexOf(terms[i]) !== -1) return true;
      }
      return false;
    });
  }

  function diversifyClips(pool, limit) {
    limit = limit || 5;
    var shuffled = pool.slice().sort(function () { return Math.random() - 0.5; });
    var chosen = [];
    var used = {};
    for (var i = 0; i < shuffled.length && chosen.length < limit; i++) {
      var c = shuffled[i];
      if (used[c.episode_slug]) continue;
      used[c.episode_slug] = 1;
      chosen.push(c);
    }
    for (var j = 0; j < shuffled.length && chosen.length < Math.min(3, limit); j++) {
      var c2 = shuffled[j];
      var dup = chosen.some(function (x) {
        return x.episode_slug === c2.episode_slug && x.title === c2.title;
      });
      if (dup) continue;
      chosen.push(c2);
    }
    return chosen;
  }


  function loadIndex() {
    if (cache) return Promise.resolve(cache);
    return fetch(abs(INDEX_URL))
      .then(function (r) {
        if (!r.ok) throw new Error("index " + r.status);
        return r.json();
      })
      .then(function (data) {
        cache = data;
        return data;
      });
  }

  function published(eps) {
    return (eps || []).filter(function (e) {
      return e && e.number && !REMOVED[e.number] && !e.removed;
    });
  }

  function ytThumb(id) {
    if (!id) return null;
    return "https://i.ytimg.com/vi/" + id + "/hqdefault.jpg";
  }

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function cardHtml(ep, opts) {
    opts = opts || {};
    var title = ep.browse_title || ep.canonical_title || ep.title || "Episode";
    var guest = ep.guest || "Solo";
    var num = ep.number || "";
    var dur = ep.duration || "";
    var href = abs(ep.url || ("episodes/" + ep.slug + "/index.html"));
    var thumb = ytThumb(ep.youtube_id);
    var media;
    if (thumb) {
      media =
        '<div class="ep-card-thumb"><img src="' +
        esc(thumb) +
        '" alt="" loading="lazy" width="480" height="360" onerror="this.parentNode.innerHTML=this.parentNode.getAttribute(\'data-fallback\')" data-fallback=""></div>';
    } else {
      media =
        '<div class="ep-card-thumb"><div class="ep-card-fallback"><span class="num">Episode ' +
        esc(num) +
        '</span><span class="ftitle">' +
        esc(title) +
        "</span></div></div>";
    }
    // fix onerror fallback via separate approach
    if (thumb) {
      media =
        '<div class="ep-card-thumb">' +
        '<img src="' +
        esc(thumb) +
        '" alt="" loading="lazy" width="480" height="360">' +
        "</div>";
    }
    var metaBits = [];
    if (num) metaBits.push("Episode " + num);
    if (guest) metaBits.push(guest);
    if (dur) metaBits.push(dur);
    return (
      '<a class="ep-card" href="' +
      esc(href) +
      '">' +
      media +
      '<div class="ep-card-body">' +
      '<p class="ep-card-title">' +
      esc(title) +
      "</p>" +
      '<p class="ep-card-meta">' +
      esc(metaBits.join(" · ")) +
      "</p>" +
      "</div></a>"
    );
  }

  function parseTs(t) {
    if (typeof t === "number") return t;
    if (!t) return 0;
    var parts = String(t).replace(/^\[|\]$/g, "").split(":").map(Number);
    if (parts.some(isNaN)) return 0;
    if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2];
    if (parts.length === 2) return parts[0] * 60 + parts[1];
    return parts[0] || 0;
  }

  function fmtTs(sec) {
    sec = Math.max(0, Math.floor(sec));
    var h = Math.floor(sec / 3600);
    var m = Math.floor((sec % 3600) / 60);
    var s = sec % 60;
    function z(n) {
      return n < 10 ? "0" + n : String(n);
    }
    return z(h) + "-" + z(m) + "-" + z(s);
  }

  function fmtHuman(sec) {
    sec = Math.max(0, Math.floor(sec));
    var h = Math.floor(sec / 3600);
    var m = Math.floor((sec % 3600) / 60);
    var s = sec % 60;
    function z(n) {
      return n < 10 ? "0" + n : String(n);
    }
    if (h) return h + ":" + z(m) + ":" + z(s);
    return m + ":" + z(s);
  }

  function isBumper(title) {
    var t = (title || "").toLowerCase().trim();
    if (!t) return true;
    if (/^(intro|outro|opening|closing|end credits|credits|theme|bumper)\b/.test(t))
      return true;
    if (/welcome to the junkyard love/.test(t) && t.length < 55) return true;
    if (/drink some water/.test(t)) return true;
    if (/let'?s roll/.test(t) && /drink|water|hit record/.test(t)) return true;
    if (/hit record/.test(t) && t.length < 40) return true;
    return false;
  }

  /** Clips allowed in radio / shuffle / pick / mood pools (not host-open, not bumpers). */
  function isPoolClip(c) {
    if (!c || !c.title) return false;
    if (REMOVED[c.episode_number]) return false;
    if (c.host_open) return false;
    if (isBumper(c.title)) return false;
    return true;
  }

  function chapterDuration(ch, next, epDur) {
    var start = parseTs(ch.start_seconds != null ? ch.start_seconds : ch.start);
    var end = next
      ? parseTs(next.start_seconds != null ? next.start_seconds : next.start)
      : epDur || start + 120;
    return Math.max(0, end - start);
  }

  function usableChapters(ep) {
    var chs = ep.chapters || [];
    var out = [];
    for (var i = 0; i < chs.length; i++) {
      var ch = chs[i];
      if (isBumper(ch.title)) continue;
      var dur = chapterDuration(ch, chs[i + 1], ep.duration_seconds);
      if (dur < 45 && i < chs.length - 1) continue;
      // prefer real names (not empty / generic)
      var title = (ch.title || "").trim();
      if (!title || /^chapter\s*\d+$/i.test(title)) continue;
      out.push({ ch: ch, i: i, dur: dur });
    }
    return out;
  }

  function nearestQuote(ep, startSec, endSec) {
    var quotes = ep.quotes || [];
    var best = null;
    var bestDist = Infinity;
    for (var i = 0; i < quotes.length; i++) {
      var q = quotes[i];
      var t = parseTs(q.t_seconds != null ? q.t_seconds : q.t);
      if (t >= startSec && t < endSec) return q;
      var dist = Math.abs(t - startSec);
      if (dist < bestDist && t >= startSec - 30 && t <= endSec + 30) {
        bestDist = dist;
        best = q;
      }
    }
    return best;
  }

  function pick(arr) {
    if (!arr || !arr.length) return null;
    return arr[Math.floor(Math.random() * arr.length)];
  }

  function episodeUrl(ep, hash) {
    var u = abs(ep.url || ("episodes/" + ep.slug + "/index.html"));
    return hash ? u + hash : u;
  }

  function ytUrl(ep, seconds) {
    if (!ep.youtube_id) return null;
    var u = "https://www.youtube.com/watch?v=" + ep.youtube_id;
    if (seconds != null && seconds > 0) u += "&t=" + Math.floor(seconds) + "s";
    return u;
  }

  function clipCardHtml(ep, ch, quote) {
    var startSec = parseTs(ch.start_seconds != null ? ch.start_seconds : ch.start);
    var hash = "#t-" + fmtTs(startSec);
    var guest = ep.is_solo ? "Solo" : ep.guest || "Guest";
    var title = ep.browse_title || ep.canonical_title || "";
    var yt = ytUrl(ep, startSec);
    var html =
      '<div class="clip-card">' +
      "<h3>" +
      esc(ch.title) +
      "</h3>" +
      '<p class="clip-ep">' +
      esc(title) +
      " · Episode " +
      esc(ep.number) +
      " · " +
      esc(guest) +
      " · starts " +
      esc(fmtHuman(startSec)) +
      "</p>";
    if (quote && quote.text) {
      html +=
        '<p class="clip-quote">' +
        (quote.speaker ? esc(quote.speaker) + ": " : "") +
        "“" +
        esc(quote.text.replace(/^["“]|["”]$/g, "")) +
        "”</p>";
    }
    html += '<div class="btn-row">';
    html +=
      '<a href="' +
      esc(episodeUrl(ep, hash)) +
      '">Open at this chapter</a>';
    html +=
      '<a class="secondary" href="' +
      esc(episodeUrl(ep)) +
      '">Full episode</a>';
    if (yt) {
      html +=
        '<a class="secondary" href="' +
        esc(yt) +
        '" target="_blank" rel="noopener">YouTube at time</a>';
    }
    html += "</div></div>";
    return html;
  }

  function randomEpisode() {
    return loadIndex().then(function (data) {
      var ep = pick(published(data.episodes));
      if (!ep) return;
      window.location.href = episodeUrl(ep);
    });
  }


  function shuffleClip(targetEl) {
    return loadClips().then(function (data) {
      var el = typeof targetEl === "string" ? document.querySelector(targetEl) : targetEl;
      var clip = pick(data.clips);
      if (!clip || !el) {
        if (el) el.innerHTML = '<p class="search-empty">No chapters available yet.</p>';
        return;
      }
      el.innerHTML = clipFromIndexCard(clip, {});
    });
  }


  function normalize(s) {
    return String(s || "")
      .toLowerCase()
      .replace(/[^a-z0-9\s]/g, " ")
      .replace(/\s+/g, " ")
      .trim();
  }

  function phraseMatchesChapter(phrase, chTitle) {
    var p = normalize(phrase);
    var t = normalize(chTitle);
    if (!p || !t) return false;
    if (t.indexOf(p) !== -1) return true;
    var words = p.split(" ").filter(function (w) {
      return w.length > 2;
    });
    if (!words.length) return false;
    var hit = 0;
    for (var i = 0; i < words.length; i++) {
      if (t.indexOf(words[i]) !== -1) hit++;
    }
    return hit >= Math.min(2, words.length) || (words.length === 1 && hit === 1);
  }


  function pickClips(phrase, targetEl, limit) {
    limit = limit || 5;
    return loadClips().then(function (data) {
      var el = typeof targetEl === "string" ? document.querySelector(targetEl) : targetEl;
      if (!el) return;
      var p = normalize(phrase);
      var matches = data.clips.filter(function (c) {
        var hay = normalize((c.title || "") + " " + ((c.topic_tags || []).join(" ")) + " " + (c.guest || ""));
        if (hay.indexOf(p) !== -1) return true;
        return phraseMatchesChapter(phrase, c.title || "");
      });
      var chosen = diversifyClips(matches, limit);
      if (!chosen.length) {
        el.innerHTML = '<p class="search-empty">No chapters matched “' + esc(phrase) + '”. Try another phrase.</p>';
        return;
      }
      el.innerHTML =
        '<p class="note">Clips for “' + esc(phrase) + '”</p>' +
        chosen.map(function (c) { return clipFromIndexCard(c); }).join("");
    });
  }


  function renderPhraseCloud(container, phrases) {
    var el =
      typeof container === "string" ? document.querySelector(container) : container;
    if (!el) return;
    el.innerHTML = phrases
      .map(function (p) {
        return (
          '<button type="button" data-phrase="' + esc(p) + '">' + esc(p) + "</button>"
        );
      })
      .join("");
    el.addEventListener("click", function (e) {
      var btn = e.target.closest("button[data-phrase]");
      if (!btn) return;
      el.querySelectorAll("button").forEach(function (b) {
        b.setAttribute("aria-pressed", "false");
      });
      btn.setAttribute("aria-pressed", "true");
      var target = document.querySelector("#clip-results") || el.nextElementSibling;
      pickClips(btn.getAttribute("data-phrase"), target);
    });
  }

  function randomQuote(targetEl) {
    var el = typeof targetEl === "string" ? document.querySelector(targetEl) : targetEl;
    if (!el) return Promise.resolve();
    var cleanUrl = abs("assets/quotes_clean.json");
    return fetch(cleanUrl, { credentials: "same-origin" })
      .then(function (r) {
        if (!r.ok) throw new Error("no quotes_clean");
        return r.json();
      })
      .then(function (payload) {
        var list = payload.quotes || payload || [];
        var pool = list.filter(function (q) {
          return q && q.text && q.text.length > 20 && q.episode_slug;
        });
        var item = pick(pool);
        if (!item) {
          renderQuoteCard(el, "");
          return;
        }
        var t = parseTs(item.t_seconds != null ? item.t_seconds : item.timestamp);
        var hash = item.timestamp ? "#t-" + fmtTs(t) : "";
        var text = String(item.text).replace(/^["“]|["”]$/g, "");
        var epUrl = abs("episodes/" + item.episode_slug + "/index.html") + hash;
        var body =
          '<blockquote class="pull-quote">“' +
          esc(text) +
          '”</blockquote>' +
          '<p class="note">' +
          (item.speaker ? esc(item.speaker) + " · " : "") +
          '<a href="' +
          esc(epUrl) +
          '">' +
          esc(item.browse_title || item.episode_slug) +
          " · Episode " +
          esc(item.episode_number || "") +
          "</a></p>";
        renderQuoteCard(el, body);
      })
      .catch(function () {
        return loadIndex().then(function (data) {
          var pool = [];
          published(data.episodes).forEach(function (ep) {
            (ep.quotes || []).forEach(function (q) {
              if (q && q.text && q.text.length > 20) pool.push({ ep: ep, q: q });
            });
          });
          var item = pick(pool);
          if (!item) {
            renderQuoteCard(el, "");
            return;
          }
          var t = parseTs(item.q.t_seconds != null ? item.q.t_seconds : item.q.t);
          var hash = item.q.t ? "#t-" + fmtTs(t) : "";
          var text = item.q.text.replace(/^["“]|["”]$/g, "");
          var body =
            '<blockquote class="pull-quote">“' +
            esc(text) +
            '”</blockquote>' +
            '<p class="note">' +
            (item.q.speaker ? esc(item.q.speaker) + " · " : "") +
            '<a href="' +
            esc(episodeUrl(item.ep, hash)) +
            '">' +
            esc(item.ep.browse_title || item.ep.canonical_title) +
            " · Episode " +
            esc(item.ep.number) +
            "</a></p>";
          renderQuoteCard(el, body);
        });
      });
  }

  function renderQuoteCard(el, bodyHtml) {
    if (!el) return;
    var actions = el.querySelector(".quote-actions");
    if (!actions) {
      actions = document.createElement("div");
      actions.className = "quote-actions";
      actions.innerHTML =
        '<button type="button" class="btn secondary btn-small" data-another-quote title="Show another quote">another quote</button>';
    } else {
      actions = actions.cloneNode(true);
    }
    var body = document.createElement("div");
    body.className = "quote-body";
    body.innerHTML = bodyHtml || "";
    el.innerHTML = "";
    el.appendChild(body);
    el.appendChild(actions);
  }

  function wireAnotherQuote() {
    document.addEventListener("click", function (e) {
      var btn = e.target.closest("[data-another-quote]");
      if (!btn) return;
      e.preventDefault();
      var card = btn.closest("[data-random-quote]") || document.querySelector("[data-random-quote]");
      if (card) randomQuote(card);
    });
  }

  function wireSearchHints() {
    var inputs = document.querySelectorAll("input[data-search-hint], input#home-q");
    if (!inputs.length) return;
    var fallback = [
      "try a guest name, or a word like breath, father, surrender.",
      "try a guest name, or a word like sleep, prayer, music.",
      "try a guest name, or a word like awakening, grief, work.",
      "try a guest name, or a word like voice, meditation, money.",
    ];
    function applyHints(hints) {
      inputs.forEach(function (input) {
        function setHint() {
          var h = hints[Math.floor(Math.random() * hints.length)];
          input.setAttribute("placeholder", h);
        }
        setHint();
        input.addEventListener("focus", setHint);
      });
    }
    loadClips()
      .then(function (payload) {
        var clips = payload.clips || payload || [];
        var words = {};
        var guests = {};
        clips.forEach(function (c) {
          if (c.guest) {
            var g = String(c.guest).split(/[,&/]/)[0].trim().split(/\s+/)[0];
            if (g && g.length > 2 && g[0] === g[0].toUpperCase()) guests[g] = true;
          }
          String(c.title || "")
            .toLowerCase()
            .split(/[^a-z]+/)
            .forEach(function (w) {
              if (
                w.length >= 4 &&
                [
                  "with",
                  "from",
                  "that",
                  "this",
                  "your",
                  "about",
                  "into",
                  "have",
                  "what",
                  "when",
                  "open",
                  "host",
                  "episode",
                  "intro",
                  "outro",
                ].indexOf(w) < 0
              )
                words[w] = (words[w] || 0) + 1;
            });
        });
        var topWords = Object.keys(words)
          .sort(function (a, b) {
            return words[b] - words[a];
          })
          .slice(0, 24);
        var guestNames = Object.keys(guests).slice(0, 20);
        var hints = [];
        for (var i = 0; i < 12; i++) {
          var g = guestNames[i % Math.max(guestNames.length, 1)] || "Spencer";
          var w1 = topWords[(i * 2) % Math.max(topWords.length, 1)] || "breath";
          var w2 = topWords[(i * 2 + 1) % Math.max(topWords.length, 1)] || "father";
          var w3 = topWords[(i * 3 + 2) % Math.max(topWords.length, 1)] || "surrender";
          hints.push(
            "try a guest name, or a word like " + w1 + ", " + w2 + ", " + w3 + "."
          );
          if (g) hints.push("try " + g + ", or a word like " + w1 + ", " + w2 + ".");
        }
        applyHints(hints.length ? hints : fallback);
      })
      .catch(function () {
        applyHints(fallback);
      });
  }

  function search(query, targetEl) {
    var q = normalize(query);
    var el = typeof targetEl === "string" ? document.querySelector(targetEl) : targetEl;
    if (!el) return Promise.resolve();
    if (!q) {
      el.innerHTML =
        '<p class="search-empty">Type a guest or a topic, then search.</p>';
      return Promise.resolve();
    }
    return loadIndex().then(function (data) {
      var scored = [];
      published(data.episodes).forEach(function (ep) {
        var hay = normalize(
          [
            ep.browse_title,
            ep.canonical_title,
            ep.guest,
            ep.number,
            (ep.topics || [])
              .map(function (t) {
                return (t.title || "") + " " + (t.slug || "");
              })
              .join(" "),
            (ep.quotes || [])
              .map(function (qq) {
                return qq.text || "";
              })
              .join(" "),
            (ep.chapters || [])
              .map(function (c) {
                return c.title || "";
              })
              .join(" "),
            (ep.keywords || []).join(" "),
          ].join(" ")
        );
        if (hay.indexOf(q) === -1) {
          // all words
          var words = q.split(" ");
          var ok = words.every(function (w) {
            return hay.indexOf(w) !== -1;
          });
          if (!ok) return;
        }
        var score = 0;
        if (normalize(ep.guest).indexOf(q) !== -1) score += 50;
        if (normalize(ep.browse_title).indexOf(q) !== -1) score += 40;
        if (normalize(ep.canonical_title).indexOf(q) !== -1) score += 20;
        score += (ep.number || "").indexOf(q) !== -1 ? 30 : 0;
        scored.push({ ep: ep, score: score });
      });
      scored.sort(function (a, b) {
        return b.score - a.score || String(b.ep.number).localeCompare(String(a.ep.number));
      });
      if (!scored.length) {
        el.innerHTML =
          '<p class="search-empty">No matches. try a guest name, or a word like breath, father, surrender.</p>';
        return;
      }
      el.innerHTML =
        '<div class="card-grid">' +
        scored
          .slice(0, 40)
          .map(function (s) {
            return cardHtml(s.ep);
          })
          .join("") +
        "</div>";
    });
  }


  var moodsCache = null;
  var radioSetsCache = null;

  function loadMoods() {
    if (moodsCache) return Promise.resolve(moodsCache);
    return fetch(abs("assets/mood_doors.json"))
      .then(function (r) {
        if (!r.ok) throw new Error("moods " + r.status);
        return r.json();
      })
      .then(function (data) {
        moodsCache = data;
        return data;
      });
  }

  function loadRadioSets() {
    if (radioSetsCache) return Promise.resolve(radioSetsCache);
    return fetch(abs("assets/radio_sets.json"))
      .then(function (r) {
        if (!r.ok) throw new Error("radio " + r.status);
        return r.json();
      })
      .then(function (data) {
        radioSetsCache = data;
        return data;
      });
  }

  function findChapter(ep, chapterTime, chapterTitle) {
    var want = parseTs(chapterTime);
    var chs = ep.chapters || [];
    for (var i = 0; i < chs.length; i++) {
      var ch = chs[i];
      var start = parseTs(ch.start_seconds != null ? ch.start_seconds : ch.start);
      if (start === want) return { ch: ch, i: i };
    }
    if (chapterTitle) {
      for (var j = 0; j < chs.length; j++) {
        if (chs[j].title === chapterTitle) return { ch: chs[j], i: j };
      }
    }
    return null;
  }

  function resolveRefs(refs, data) {
    var bySlug = {};
    published(data.episodes).forEach(function (ep) {
      bySlug[ep.slug] = ep;
    });
    var out = [];
    (refs || []).forEach(function (ref) {
      var ep = bySlug[ref.slug];
      if (!ep) return;
      var found = findChapter(ep, ref.chapter_time, ref.chapter_title);
      if (!found) return;
      var chs = ep.chapters || [];
      var startSec = parseTs(
        found.ch.start_seconds != null ? found.ch.start_seconds : found.ch.start
      );
      var endSec = chs[found.i + 1]
        ? parseTs(
            chs[found.i + 1].start_seconds != null
              ? chs[found.i + 1].start_seconds
              : chs[found.i + 1].start
          )
        : startSec + 120;
      out.push({
        ep: ep,
        ch: found.ch,
        quote: nearestQuote(ep, startSec, endSec),
      });
    });
    return out;
  }


  function showMood(slug, targetEl) {
    var el = typeof targetEl === "string" ? document.querySelector(targetEl) : targetEl;
    if (!el) return Promise.resolve();
    return Promise.all([loadMoods(), loadClips()]).then(function (pair) {
      var moods = pair[0];
      var clipsData = pair[1];
      var door = (moods.doors || []).filter(function (d) { return d.slug === slug; })[0];
      if (!door) {
        el.innerHTML = '<p class="search-empty">Door not found.</p>';
        return;
      }
      var cards = [];
      (door.chapters || []).forEach(function (ref) {
        var found = null;
        for (var i = 0; i < clipsData.clips.length; i++) {
          var c = clipsData.clips[i];
          if (c.episode_slug !== ref.slug) continue;
          if (ref.chapter_title && c.title === ref.chapter_title) { found = c; break; }
          if (ref.start_seconds != null && c.start_seconds === ref.start_seconds) { found = c; break; }
          if (ref.chapter_time && parseTs(c.start) === parseTs(ref.chapter_time)) { found = c; break; }
        }
        if (found && isPoolClip(found)) cards.push(found);
        else if (ref.chapter_title && !isBumper(ref.chapter_title)) {
          var synth = {
            title: ref.chapter_title,
            episode_slug: ref.slug,
            episode_number: ref.episode_number || "",
            browse_title: ref.browse_title || "",
            guest: ref.guest || "",
            start: ref.chapter_time,
            start_seconds: ref.start_seconds != null ? ref.start_seconds : parseTs(ref.chapter_time),
            youtube_id: ref.youtube_id || "",
            host_open: false,
          };
          if (isPoolClip(synth)) cards.push(synth);
        }
      });
      if (!cards.length) {
        el.innerHTML = '<p class="search-empty">No honest chapters for this door after removing intros/host-opens. NEEDS JACOB if this door should stay.</p>';
        return;
      }
      el.innerHTML =
        '<p class="note">' + esc(door.label) + ' · <a href="' + esc(abs("moods/" + door.slug + "/index.html")) + '">Open door page</a></p>' +
        cards.map(function (c) { return clipFromIndexCard(c); }).join("");
    });
  }


  function wireMoodDoors() {
    var cloud = document.querySelector("[data-mood-doors]");
    if (!cloud) return;
    // If empty shell from redesign template, populate chips
    if (!cloud.children.length) {
      loadMoods().then(function (moods) {
        cloud.innerHTML = (moods.doors || [])
          .map(function (d) {
            return (
              '<a class="mood-chip" href="' +
              esc(abs("moods/" + d.slug + "/index.html")) +
              '" data-mood="' +
              esc(d.slug) +
              '">' +
              esc(d.label) +
              "</a>"
            );
          })
          .join("");
      });
    }
    cloud.addEventListener("click", function (e) {
      var chip = e.target.closest("[data-mood]");
      if (!chip) return;
      var results = document.querySelector("[data-mood-results], #mood-results");
      if (!results) return;
      // Keep navigation for middle-click / modified clicks
      if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button === 1) return;
      e.preventDefault();
      cloud.querySelectorAll("[data-mood]").forEach(function (c) {
        c.setAttribute("aria-current", "false");
      });
      chip.setAttribute("aria-current", "true");
      showMood(chip.getAttribute("data-mood"), results);
    });
  }


  // Chapter radio: on-page listen path.
  // Choice: no YouTube-end auto-advance — user must hit Next (safer default).
  // Embeds load only after Play/Next gesture; never on page load.
  var radioState = {
    subject: null,
    last: null,
    subjects: null,
    hasPlayed: false,
    ytApiReady: false,
    ytApiLoading: false,
    player: null,
  };

  function loadRadioSubjects() {
    if (radioState.subjects) return Promise.resolve(radioState.subjects);
    return fetch(abs("assets/radio_sets.json"))
      .then(function (r) { if (!r.ok) return []; return r.json(); })
      .then(function (data) { radioState.subjects = data.subjects || []; return radioState.subjects; })
      .catch(function () { radioState.subjects = []; return radioState.subjects; });
  }

  function ensureYtApi() {
    if (radioState.ytApiReady) return Promise.resolve();
    if (window.YT && window.YT.Player) {
      radioState.ytApiReady = true;
      return Promise.resolve();
    }
    return new Promise(function (resolve) {
      var prev = window.onYouTubeIframeAPIReady;
      window.onYouTubeIframeAPIReady = function () {
        radioState.ytApiReady = true;
        if (typeof prev === "function") prev();
        resolve();
      };
      if (!radioState.ytApiLoading) {
        radioState.ytApiLoading = true;
        var tag = document.createElement("script");
        tag.src = "https://www.youtube.com/iframe_api";
        tag.async = true;
        document.head.appendChild(tag);
      }
      // Fallback if API already mid-load
      var n = 0;
      var timer = setInterval(function () {
        if (window.YT && window.YT.Player) {
          clearInterval(timer);
          radioState.ytApiReady = true;
          resolve();
        } else if (++n > 80) {
          clearInterval(timer);
          resolve();
        }
      }, 100);
    });
  }

  function destroyRadioPlayer() {
    try {
      if (radioState.player && radioState.player.destroy) radioState.player.destroy();
    } catch (e) {}
    radioState.player = null;
  }

  function radioCardHtml(c) {
    var startSec = parseTs(c.start_seconds != null ? c.start_seconds : c.start);
    var hash = "#t-" + fmtTs(startSec);
    var epUrl = abs("episodes/" + c.episode_slug + "/index.html");
    var guest = c.guest || "Solo";
    var html = '<div class="clip-card radio-now-playing"><h3>' + esc(c.title) + "</h3>";
    html +=
      '<p class="clip-ep">' +
      "Episode " +
      esc(c.episode_number || "") +
      " · " +
      esc(guest) +
      " · starts " +
      esc(fmtHuman(startSec)) +
      "</p>";
    // short_summary / long_summary hidden until extract pass
    if (c.youtube_id) {
      html +=
        '<div class="yt-embed radio-embed" data-radio-embed>' +
        '<div id="radio-yt-player"></div>' +
        "</div>";
    } else {
      html +=
        '<p class="note">No YouTube ID for this episode — open the transcript chapter instead.</p>';
    }
    html += '<div class="btn-row">';
    html +=
      '<a href="' +
      esc(epUrl + hash) +
      '">' +
      (c.youtube_id ? "Open episode at chapter" : "Open episode at chapter") +
      "</a>";
    html += '<a class="secondary" href="' + esc(epUrl) + '">Full episode</a>';
    html += "</div></div>";
    return html;
  }

  function mountRadioEmbed(clip) {
    if (!clip || !clip.youtube_id) return Promise.resolve();
    var startSec = Math.floor(parseTs(clip.start_seconds != null ? clip.start_seconds : clip.start));
    var mount = document.getElementById("radio-yt-player");
    if (!mount) return Promise.resolve();
    destroyRadioPlayer();
    // Prefer IFrame API when available; fall back to nocookie iframe.
    return ensureYtApi().then(function () {
      mount = document.getElementById("radio-yt-player");
      if (!mount) return;
      if (window.YT && window.YT.Player) {
        radioState.player = new window.YT.Player("radio-yt-player", {
          videoId: clip.youtube_id,
          playerVars: {
            start: startSec,
            autoplay: 1,
            rel: 0,
            modestbranding: 1,
            playsinline: 1,
            origin: window.location.origin,
          },
          events: {
            // Safer default: do not auto-advance on end — user hits Next.
            onStateChange: function () {},
          },
        });
      } else {
        var src =
          "https://www.youtube-nocookie.com/embed/" +
          encodeURIComponent(clip.youtube_id) +
          "?start=" +
          startSec +
          "&autoplay=1&rel=0&modestbranding=1&playsinline=1";
        mount.outerHTML =
          '<iframe src="' +
          esc(src) +
          '" title="Chapter video" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen loading="lazy"></iframe>';
      }
    });
  }

  function radioPlay(next) {
    return Promise.all([loadClips(), loadRadioSubjects()]).then(function (pair) {
      var clips = pair[0].clips;
      var subjects = pair[1];
      var pool = clips;
      var thinSubject = false;
      if (radioState.subject) {
        var sub = subjects.filter(function (s) { return s.slug === radioState.subject; })[0];
        if (sub && sub.terms) {
          pool = filterClipsByTerms(clips, sub.terms);
          if (!pool.length) thinSubject = true;
        }
      }
      var el = document.querySelector("[data-radio-card], #radio-card");
      if (!el) return;
      if (thinSubject) {
        destroyRadioPlayer();
        el.innerHTML =
          '<p class="search-empty">No honest chapters left in this subject after removing intros/host-opens. Try another subject, or NEEDS JACOB to hand-curate this door.</p>';
        return;
      }
      var clip = pick(pool);
      if (next && radioState.last && pool.length > 1) {
        var guard = 0;
        while (
          clip &&
          radioState.last &&
          clip.episode_slug === radioState.last.episode_slug &&
          clip.title === radioState.last.title &&
          guard < 8
        ) {
          clip = pick(pool);
          guard++;
        }
      }
      radioState.last = clip;
      radioState.hasPlayed = true;
      if (!clip) return;
      destroyRadioPlayer();
      el.innerHTML = radioCardHtml(clip);
      var nextBtn = document.querySelector("[data-radio-next]");
      if (nextBtn) nextBtn.removeAttribute("hidden");
      return mountRadioEmbed(clip);
    });
  }

  function wireRadioSets() {
    wireChapterRadio();
  }

  function wireChapterRadio() {
    var play = document.querySelector("[data-radio-play]");
    var next = document.querySelector("[data-radio-next]");
    var bar = document.querySelector("[data-radio-subjects]");
    if (!play && !bar) return;
    if (bar) {
      bar.addEventListener("click", function (e) {
        var btn = e.target.closest("button[data-radio-subject]");
        if (!btn) return;
        var slug = btn.getAttribute("data-radio-subject");
        if (radioState.subject === slug) {
          radioState.subject = null;
          btn.setAttribute("aria-pressed", "false");
        } else {
          radioState.subject = slug;
          bar.querySelectorAll("button[data-radio-subject]").forEach(function (b) {
            b.setAttribute("aria-pressed", b === btn ? "true" : "false");
          });
        }
      });
    }
    if (play) play.addEventListener("click", function () { radioPlay(false); });
    if (next) next.addEventListener("click", function () { radioPlay(true); });
  }

  function wireWhatWeTalk() {
    var btn = document.querySelector("[data-what-we-talk]");
    var out = document.querySelector("#what-we-talk-result");
    if (!btn || !out) return;
    var cache = null;
    btn.addEventListener("click", function () {
      var go = function (data) {
        var entries = data.entries || [];
        var item = pick(entries);
        if (!item) {
          out.innerHTML = '<p class="search-empty">No subjects yet.</p>';
          return;
        }
        var links = (item.links || [])
          .map(function (l) {
            return (
              '<li><a href="' + esc(abs(l.url)) + '">' + esc(l.title) + "</a> · Episode " +
              esc(l.episode_number || "") + (l.guest ? " · " + esc(l.guest) : "") + "</li>"
            );
          })
          .join("");
        out.innerHTML = "<h3>" + esc(item.subject) + "</h3><p>" + esc(item.blurb) + '</p><ul class="list">' + links + "</ul>";
      };
      if (cache) return go(cache);
      fetch(abs("assets/what_we_talk_about.json"))
        .then(function (r) { return r.json(); })
        .then(function (data) { cache = data; go(data); })
        .catch(function () { out.innerHTML = '<p class="search-empty">Could not load subjects.</p>'; });
    });
  }


  function wireHome() {
    var randomBtn = document.querySelector("[data-random-episode]");
    if (randomBtn) {
      randomBtn.addEventListener("click", function (e) {
        e.preventDefault();
        randomEpisode();
      });
    }
    var shuffleBtn = document.querySelector("[data-shuffle-clip]");
    if (shuffleBtn) {
      shuffleBtn.addEventListener("click", function (e) {
        e.preventDefault();
        shuffleClip("#shuffle-result");
      });
    }
    var searchForm = document.querySelector("[data-archive-search]");
    if (searchForm) {
      searchForm.addEventListener("submit", function (e) {
        e.preventDefault();
        var input = searchForm.querySelector('input[type="search"], input[name="q"]');
        var q = input ? input.value : "";
        var results = document.querySelector("#search-results");
        if (results) {
          search(q, results);
        } else {
          window.location.href = abs("search/index.html") + "?q=" + encodeURIComponent(q);
        }
      });
    }
    loadIndex().then(function (data) {
      var phrases = data.clip_phrases || [];
      var cloud = document.querySelector("[data-phrase-cloud]");
      if (cloud && phrases.length) renderPhraseCloud(cloud, phrases);
      var quoteEl = document.querySelector("[data-random-quote]");
      if (quoteEl) randomQuote(quoteEl);
      var latest = document.querySelector("[data-latest-cards]");
      if (latest) {
        var n = parseInt(latest.getAttribute("data-count") || "8", 10);
        var eps = published(data.episodes)
          .slice()
          .sort(function (a, b) {
            return String(b.number).localeCompare(String(a.number));
          })
          .slice(0, n);
        latest.innerHTML = eps.map(function (ep) {
          return cardHtml(ep);
        }).join("");
      }
    });
  }

  function wireSearchPage() {
    var form = document.querySelector("[data-archive-search]");
    var results = document.querySelector("#search-results");
    if (!form || !results) return;
    var params = new URLSearchParams(window.location.search);
    var initial = params.get("q") || "";
    var input = form.querySelector('input[type="search"], input[name="q"]');
    if (input && initial) input.value = initial;
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var q = input ? input.value : "";
      var url = new URL(window.location.href);
      url.searchParams.set("q", q);
      history.replaceState(null, "", url.toString());
      search(q, results);
    });
    if (initial) search(initial, results);
    else
      results.innerHTML =
        '<p class="search-empty">Type a guest or a topic, then search.</p>';
  }

  document.addEventListener("DOMContentLoaded", function () {
    wireAnotherQuote();
    wireSearchHints();
    wireHome();
    wireMoodDoors();
    wireRadioSets();
    wireSearchPage();
    var clipsCloud = document.querySelector("[data-phrase-cloud][data-clips-page]");
    if (clipsCloud) {
      loadIndex().then(function (data) {
        renderPhraseCloud(clipsCloud, data.clip_phrases || []);
      });
    }
  });

  window.JYLArchive = {
    loadIndex: loadIndex,
    loadClips: loadClips,
    search: search,
    randomEpisode: randomEpisode,
    shuffleClip: shuffleClip,
    pickClips: pickClips,
    showMood: showMood,
    cardHtml: cardHtml,
    abs: abs,
  };
})();
