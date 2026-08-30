---
name: youtube-playlist
description: Build custom YouTube playlists from a topic or prompt. Use when the user asks to create, curate, or automate a YouTube playlist (e.g., "make me a study playlist on X", "find videos about Y and save them as a playlist", "build a learning path playlist"). Uses the YouTube Data API v3 (search + OAuth) via the bundled zero-dependency Python CLI, or the included single-file website. Requires the user's YouTube Data API key and OAuth client (setup instructions inside).
---

# YouTube Playlist Builder

Turn a topic into a **real, saved YouTube playlist** (public/unlisted/private) in the
user's own YouTube account. Two delivery paths:

- **CLI (`scripts/yt_playlist.py`)** — zero dependencies, Python 3.8+. The agent (you)
  supplies the intelligence (query generation + curation); the script does the API work.
- **Website (`website/index.html` in this skill's repo / standalone)** — single HTML file
  the user can open locally; does search + OAuth + playlist creation fully client-side.

## Setup (do this first, with the user)

Both paths need a Google Cloud project with:

1. **YouTube Data API v3 enabled** — https://console.cloud.google.com/apis/library/youtube.googleapis.com
2. **API key** — https://console.cloud.google.com/apis/credentials → *Create credentials → API key*. (Searches use this.)
3. **OAuth client** — same page → *Create credentials → OAuth client ID*:
   - For the **CLI**: choose **Desktop app**. Download the `client_secret_*.json`.
   - For the **website**: choose **Web application**, add the page's origin
     (e.g. `http://localhost:8000`) under *Authorized JavaScript origins*.
4. First OAuth run requires the user to be an Owner/Editor of the project OR added as a
   test user on the OAuth consent screen (unpublished apps only allow test users).
   Google may show an "unverified app" warning → *Advanced → Go to app (unsafe)*.

Quota defaults: 10,000 units/day. Costs: `search.list` = 100, `videos.list` = 1,
`playlists.insert` = 50, `playlistItems.insert` = 50. A 15-video playlist ≈ 200+15*50 = ~950 units.

## Agent workflow (CLI path)

You are the curator. Do it in two rounds so the user gets genuinely good curation:

### Round 1 — plan queries, then search

1. From the user's topic, write 3–6 **specific search queries** (vary phrasing:
   "X full course", "X explained in 10 minutes", "best lofi for studying", "X playlist 2025").
2. Run the search (API key only, no OAuth needed):

```
python scripts/yt_playlist.py search --api-key KEY --queries "query one;query two;query three" --per-query 6
```

3. Output is JSON: `videoId, title, channel, duration (seconds), views, url, query`.
   The script already enriches with real duration/views; you filter and pick
   yourself (e.g. ignore < 4 min or > 2 h for a study session).

### Round 2 — curate, then create the playlist

4. Pick the best N videos yourself (fit the user's intent: level, length, variety, recency,
   avoid duplicates/shorts/low-quality rips). Then pass explicit IDs:

```
python scripts/yt_playlist.py create --api-key KEY --client-secret client_secret.json \
  --title "Deep Focus: Machine Learning Crash Course" \
  --description "Curated intro-to-ML path. Updated 2026." \
  --privacy public --video-ids ID1 ID2 ID3
```

   OAuth: the script opens a browser on the user's machine, runs a loopback server on
   `http://localhost:8765`, and caches tokens in `~/.yt_playlist_tokens.json` for reuse
   (auto-refreshes). On a headless machine, set `YT_OAUTH_NO_BROWSER=1` to print the URL
   and paste the redirect URL back, or provide `--access-token`.

5. No auto-pick mode on purpose: the agent's curation IS the feature. If the user
   wants zero-effort auto-ranking, point them at the website instead.

### Curating well (what makes results feel "AI-made")

- Ask the user about: video length tolerance, difficulty level, language, whether they
  want music/focus tracks mixed in with the topical videos.
- Prefer: recent uploads, channels with authority in the niche, videos whose titles
  actually match the topic, durations that fit a study session (20–90 min blocks).
- Vary sources — don't take 5 videos from one channel.
- Always confirm privacy preference (public by default when the user asked for "public").

## Error handling cheat-sheet

- `quotaExceeded` (403): daily quota gone; nothing you can do until reset (midnight PT).
- `keyInvalid` (400): wrong API key or YouTube Data API not enabled.
- `access_denied` at OAuth: user not a test user on the consent screen, or wrong client type.
- `playlistItems.insert` 404 `videoNotFound`: video is private/deleted/region-blocked — skip it.
- `forbidden` on insert: token missing `youtube.force-ssl` scope — re-auth with `--fresh`.

## Website path

If the user prefers a no-terminal experience, point them at `website/index.html` in this
skill (or the standalone copy in the generator repo). Serve it over http (not file://),
e.g. `python -m http.server 8000`, open http://localhost:8000, paste their API key +
Web-type client ID, type a topic, click Build. The site handles search → filter → rank →
OAuth (Google Identity Services) → playlist creation entirely in the browser.
