# PlaylistForge — topic in, playlist out

A single-file website that turns any topic into a **real YouTube playlist saved to
your own channel** (public, unlisted, or private). No server, no build step —
everything runs in your browser against the official YouTube Data API v3.

## Quick start

1. **Serve the file over http** (Google sign-in won't work from `file://`):

   ```
   cd youtube-playlist-generator
   python -m http.server 8000
   ```

   Open http://localhost:8000

2. **Get your keys** (one-time, ~5 minutes, free):
   - Go to https://console.cloud.google.com/ → create a project (any name).
   - **APIs & Services → Library** → enable **YouTube Data API v3**.
   - **APIs & Services → Credentials**:
     - *Create credentials → API key* → paste into the site's "API key" field.
     - *Create credentials → OAuth client ID → Web application* → under
       **Authorized JavaScript origins** add `http://localhost:8000` → copy the
       client ID into the site.
   - **OAuth consent screen**: choose External, fill the required fields, add
     **your own Google account as a test user**, scope not needed to be pre-added.
     (Your app stays in "Testing" mode — fine for personal use.)

3. Type a topic, pick a count / length window / privacy, hit **Forge playlist**,
   sign in with Google, and your playlist appears in your YouTube library.

## How the curation works

- Your topic is expanded into a query plan (topic + "full course", "explained",
  "tutorial for beginners", …) plus optional focus/lo-fi study-music queries.
- Every candidate is checked for **real duration and view count**; anything
  outside your length window, plus Shorts/live re-uploads, is dropped.
- The final mix round-robins across queries (so you don't get five videos from
  one channel) and caps music tracks at ~25% of the list.

## Quota

Each build uses roughly `searches × 100 + ~50` units of the free **10,000/day**
quota. A typical 8-query build ≈ 900 units → ~10 builds/day.

## Privacy

Your API key and client ID are stored in `localStorage` in your browser only,
and requests go directly from your browser to Google. Nothing else sees them.

## Also included

A CLI version lives in the companion skill:
`~/.cline/skills/youtube-playlist/scripts/yt_playlist.py` (zero dependencies) —
useful if you want an AI coding agent to curate the picks for you instead of
the site's automatic ranking.
