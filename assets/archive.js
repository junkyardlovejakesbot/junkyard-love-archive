(function () {
  "use strict";

  var INDEX_URL = "assets/episodes_index.json";
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
    return false;
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
    return loadIndex().then(function (data) {
      var eps = published(data.episodes).filter(function (e) {
        return usableChapters(e).length > 0;
      });
      var ep = pick(eps);
      var el = typeof targetEl === "string" ? document.querySelector(targetEl) : targetEl;
      if (!ep || !el) {
        if (el) el.innerHTML = '<p class="search-empty">No chapters available yet.</p>';
        return;
      }
      var usable = usableChapters(ep);
      var picked = pick(usable);
      var ch = picked.ch;
      var chs = ep.chapters || [];
      var startSec = parseTs(ch.start_seconds != null ? ch.start_seconds : ch.start);
      var endSec = chs[picked.i + 1]
        ? parseTs(
            chs[picked.i + 1].start_seconds != null
              ? chs[picked.i + 1].start_seconds
              : chs[picked.i + 1].start
          )
        : startSec + (picked.dur || 120);
      var quote = nearestQuote(ep, startSec, endSec);
      el.innerHTML = clipCardHtml(ep, ch, quote);
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
    return loadIndex().then(function (data) {
      var el = typeof targetEl === "string" ? document.querySelector(targetEl) : targetEl;
      if (!el) return;
      var matches = [];
      var usedEps = {};
      published(data.episodes).forEach(function (ep) {
        (ep.chapters || []).forEach(function (ch, i) {
          if (isBumper(ch.title)) return;
          if (!phraseMatchesChapter(phrase, ch.title)) return;
          // also match topic titles lightly
          matches.push({ ep: ep, ch: ch, i: i });
        });
        // topic / keyword soft match if chapter miss
      });
      // topic fallback: if phrase matches a topic word and chapter titles contain related words
      if (matches.length < 3) {
        published(data.episodes).forEach(function (ep) {
          var hay = normalize(
            [
              ep.browse_title,
              ep.guest,
              (ep.topics || [])
                .map(function (t) {
                  return t.title || t.slug;
                })
                .join(" "),
              (ep.keywords || []).join(" "),
            ].join(" ")
          );
          if (hay.indexOf(normalize(phrase)) === -1) return;
          usableChapters(ep).forEach(function (u) {
            matches.push({ ep: ep, ch: u.ch, i: u.i });
          });
        });
      }
      // diversify across episodes
      var chosen = [];
      var pool = matches.slice().sort(function () {
        return Math.random() - 0.5;
      });
      for (var i = 0; i < pool.length && chosen.length < limit; i++) {
        var m = pool[i];
        if (usedEps[m.ep.slug]) continue;
        usedEps[m.ep.slug] = 1;
        chosen.push(m);
      }
      // fill if needed allowing same ep
      for (var j = 0; j < pool.length && chosen.length < Math.min(3, limit); j++) {
        var m2 = pool[j];
        var dup = chosen.some(function (c) {
          return c.ep.slug === m2.ep.slug && c.ch.title === m2.ch.title;
        });
        if (dup) continue;
        chosen.push(m2);
      }
      if (!chosen.length) {
        el.innerHTML =
          '<p class="search-empty">No chapters matched “' +
          esc(phrase) +
          '”. Try another phrase.</p>';
        return;
      }
      el.innerHTML =
        "<p class=\"note\">Clips for “" +
        esc(phrase) +
        "”</p>" +
        chosen
          .map(function (m) {
            var chs = m.ep.chapters || [];
            var startSec = parseTs(
              m.ch.start_seconds != null ? m.ch.start_seconds : m.ch.start
            );
            var endSec = chs[m.i + 1]
              ? parseTs(
                  chs[m.i + 1].start_seconds != null
                    ? chs[m.i + 1].start_seconds
                    : chs[m.i + 1].start
                )
              : startSec + 120;
            return clipCardHtml(m.ep, m.ch, nearestQuote(m.ep, startSec, endSec));
          })
          .join("");
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
          el.innerHTML = "";
          return;
        }
        var t = parseTs(item.t_seconds != null ? item.t_seconds : item.timestamp);
        var hash = item.timestamp ? "#t-" + fmtTs(t) : "";
        var text = String(item.text).replace(/^["“]|["”]$/g, "");
        var epUrl = abs("episodes/" + item.episode_slug + "/index.html") + hash;
        el.innerHTML =
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
            el.innerHTML = "";
            return;
          }
          var t = parseTs(item.q.t_seconds != null ? item.q.t_seconds : item.q.t);
          var hash = item.q.t ? "#t-" + fmtTs(t) : "";
          var text = item.q.text.replace(/^["“]|["”]$/g, "");
          el.innerHTML =
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
        });
      });
  }

  function search(query, targetEl) {
    var q = normalize(query);
    var el = typeof targetEl === "string" ? document.querySelector(targetEl) : targetEl;
    if (!el) return Promise.resolve();
    if (!q) {
      el.innerHTML =
        '<p class="search-empty">try a guest name, or a word like breath, father, surrender.</p>';
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
    var el =
      typeof targetEl === "string" ? document.querySelector(targetEl) : targetEl;
    if (!el) return Promise.resolve();
    return Promise.all([loadIndex(), loadMoods()]).then(function (pair) {
      var data = pair[0];
      var moods = pair[1];
      var door = (moods.doors || []).filter(function (d) {
        return d.slug === slug;
      })[0];
      if (!door) {
        el.innerHTML = '<p class="search-empty">Door not found.</p>';
        return;
      }
      var cards = resolveRefs(door.chapters, data);
      if (!cards.length) {
        el.innerHTML = '<p class="search-empty">No chapters for this door yet.</p>';
        return;
      }
      el.innerHTML =
        '<p class="note">' +
        esc(door.label) +
        ' · <a href="' +
        esc(abs("moods/" + door.slug + "/index.html")) +
        '">Open door page</a></p>' +
        cards
          .map(function (m) {
            return clipCardHtml(m.ep, m.ch, m.quote);
          })
          .join("");
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

  function wireRadioSets() {
    var bar = document.querySelector("[data-radio-sets]");
    if (!bar) return;
    bar.addEventListener("click", function (e) {
      var btn = e.target.closest("button[data-radio-set]");
      if (!btn) return;
      var id = btn.getAttribute("data-radio-set");
      bar.querySelectorAll("button[data-radio-set]").forEach(function (b) {
        b.setAttribute("aria-pressed", b === btn ? "true" : "false");
      });
      document.querySelectorAll("[data-radio-playlist]").forEach(function (pl) {
        var match = pl.getAttribute("data-radio-playlist") === id;
        if (match) pl.removeAttribute("hidden");
        else pl.setAttribute("hidden", "");
      });
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
        '<p class="search-empty">try a guest name, or a word like breath, father, surrender.</p>';
  }

  document.addEventListener("DOMContentLoaded", function () {
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
    search: search,
    randomEpisode: randomEpisode,
    shuffleClip: shuffleClip,
    pickClips: pickClips,
    showMood: showMood,
    cardHtml: cardHtml,
    abs: abs,
  };
})();
