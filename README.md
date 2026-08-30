# youtube-playlist — agent skill + single-file website

Turn a topic into a **real YouTube playlist saved to your own channel**
(public/unlisted/private). Two parts, same engine (official YouTube Data API v3):

- **`SKILL.md` + `scripts/yt_playlist.py`** — a skill for AI coding agents
  (Cline, Claude Code, any harness that reads `SKILL.md`). Zero-dependency
  Python 3.8+ CLI: the agent generates search queries, curates the picks from
  real durations/views, then OAuths in and saves the playlist.
- **`docs/index.html`** — a single-file site that does the whole flow in the
  browser: type a topic → auto query plan → filter/rank → sign in with Google →
  playlist created. No server, no build step. **Live: https://smarpitm.github.io/youtube-playlist-skill/**

## Install (skill)

```
git clone https://github.com/smarpitm/youtube-playlist-skill
# Cline:
cp -r youtube-playlist-skill ~/.cline/skills/youtube-playlist
# Claude Code:
cp -r youtube-playlist-skill ~/.claude/skills/youtube-playlist
```

Then just ask your agent: *"make me a study playlist on organic chemistry,
12 videos, public"*.

## Run (website)

Already live: **https://smarpitm.github.io/youtube-playlist-skill/**

Or locally:

```
cd docs
python -m http.server 8000
# open http://localhost:8000
```

## One-time setup (both paths)

1. Google Cloud Console → enable **YouTube Data API v3**
2. **API key** (search) + **OAuth client** — Desktop app for the CLI, Web
   application (origin `http://localhost:8000`) for the website
3. Add your Google account as a **test user** on the OAuth consent screen

Full walkthrough: `SKILL.md` and `docs/README.md`.

## Quota

Free tier: 10,000 units/day. `search.list` = 100 units, writes = 50 each —
a typical build costs < 1,000 units.

## License

MIT
