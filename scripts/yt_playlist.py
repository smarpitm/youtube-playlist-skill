#!/usr/bin/env python3
"""yt_playlist.py — find YouTube videos by topic and build real playlists.

Zero external dependencies (Python 3.8+ standard library only).

Commands:
  search  API-key only. Run queries, return candidates as JSON with real
          durations/views. (Agent or human curates from this.)
  create  OAuth. Create a playlist in the user's account and insert videos.

Setup:
  1. Google Cloud Console -> enable "YouTube Data API v3"
  2. Credentials -> Create credentials -> API key           (for search)
  3. Credentials -> Create credentials -> OAuth client ID -> Desktop app
     -> download client_secret_*.json                        (for create/full)

Quota: search=100 units, videos.list=1, playlists.insert=50,
playlistItems.insert=50. Default 10,000/day.
"""

import argparse
import json
import os
import re
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

API = "https://www.googleapis.com/youtube/v3"
OAUTH_AUTH = "https://accounts.google.com/o/oauth2/v2/auth"
OAUTH_TOKEN = "https://oauth2.googleapis.com/token"
SCOPE = "https://www.googleapis.com/auth/youtube.force-ssl"
TOKEN_FILE = os.path.join(os.path.expanduser("~"), ".yt_playlist_tokens.json")
REDIRECT_PORT = 8765


# ---------------------------------------------------------------- http helpers

def _request(method, url, params=None, body=None, headers=None):
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Accept", "application/json")
    if data:
        req.add_header("Content-Type", "application/json")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            detail = json.loads(e.read().decode())
            reason = detail.get("error", {}).get("message", "")
            errors = detail.get("error", {}).get("errors", [])
            if errors:
                reason = "%s: %s" % (errors[0].get("reason", ""), reason)
        except Exception:
            reason = str(e)
        sys.stderr.write("HTTP %s from %s -> %s\n" % (e.code, url.split("?")[0], reason))
        raise SystemExit(2)


def api_get(path, key, **params):
    params["key"] = key
    return _request("GET", API + path, params=params)


def api_post(path, token, body):
    return _request("POST", API + path, body=body,
                    headers={"Authorization": "Bearer " + token})


# ------------------------------------------------------------------- duration

_DUR_RE = re.compile(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?")


def iso8601_to_seconds(d):
    if not d:
        return 0
    m = _DUR_RE.match(d)
    if not m:
        return 0
    h, mi, s = (int(x) if x else 0 for x in m.groups())
    return h * 3600 + mi * 60 + s


# --------------------------------------------------------------------- OAuth

class _CodeCatcher(BaseHTTPRequestHandler):
    code = None

    def do_GET(self):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        _CodeCatcher.code = (q.get("code") or [None])[0]
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(b"<h2 style='font-family:sans-serif'>Playlist authorized."
                         b"You can close this tab.</h2>")

    def log_message(self, *a):  # silence
        pass


def load_client_secrets(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    for key in ("installed", "web"):
        if key in data:
            return data[key]
    if "client_id" in data:  # already flattened
        return data
    raise SystemExit("client secret file missing 'installed'/'web' section")


def _token_store():
    try:
        with open(TOKEN_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_token_store(store):
    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        json.dump(store, f)


def get_access_token(client_id, client_secret, fresh=False, headless=False):
    """Return a valid access token, using cached refresh token when possible."""
    store = _token_store()
    entry = store.get(client_id, {})
    if not fresh and entry.get("refresh_token"):
        r = _request("POST", OAUTH_TOKEN, body={
            "client_id": client_id, "client_secret": client_secret,
            "refresh_token": entry["refresh_token"],
            "grant_type": "refresh_token",
        })
        if r.get("access_token"):
            entry["access_token"] = r["access_token"]
            store[client_id] = entry
            _save_token_store(store)
            return r["access_token"]

    redirect = "http://localhost:%d" % REDIRECT_PORT
    params = {
        "client_id": client_id, "redirect_uri": redirect,
        "response_type": "code", "scope": SCOPE,
        "access_type": "offline", "prompt": "consent",
    }
    url = OAUTH_AUTH + "?" + urllib.parse.urlencode(params)

    if headless:
        print("Open this URL in a browser, approve access, then copy the URL you\n"
              "are redirected to (it starts with %s) and paste it here:\n%s"
              % (redirect, url), file=sys.stderr)
        pasted = input("redirect URL: ").strip()
        _CodeCatcher.code = urllib.parse.parse_qs(
            urllib.parse.urlparse(pasted).query).get("code", [None])[0]
    else:
        server = HTTPServer(("localhost", REDIRECT_PORT), _CodeCatcher)
        t = threading.Thread(target=server.handle_request, daemon=True)
        t.start()
        print("Opening browser for Google sign-in…", file=sys.stderr)
        webbrowser.open(url)
        t.join(timeout=300)
        server.server_close()
        if not _CodeCatcher.code:
            raise SystemExit("No OAuth code received within 5 minutes. "
                             "Re-run with --fresh or use YT_OAUTH_NO_BROWSER=1.")
    if not _CodeCatcher.code:
        raise SystemExit("No OAuth code captured.")

    r = _request("POST", OAUTH_TOKEN, body={
        "client_id": client_id, "client_secret": client_secret,
        "code": _CodeCatcher.code, "grant_type": "authorization_code",
        "redirect_uri": redirect,
    })
    if not r.get("access_token"):
        raise SystemExit("Token exchange failed: %s" % r)
    store[client_id] = r
    _save_token_store(store)
    return r["access_token"]

# -------------------------------------------------------------- API commands

def search_videos(key, queries, per_query=6):
    """Run each query through search.list, return candidates."""
    candidates, seen = [], set()
    for q in queries:
        q = q.strip()
        if not q:
            continue
        data = api_get("/search", key, part="snippet", type="video",
                       maxResults=max(1, min(50, per_query)), q=q)
        for item in data.get("items", []):
            vid = item["id"].get("videoId")
            if not vid or vid in seen:
                continue
            seen.add(vid)
            sn = item["snippet"]
            candidates.append({
                "videoId": vid,
                "title": sn["title"],
                "channel": sn["channelTitle"],
                "query": q,
                "publishedAt": sn["publishedAt"][:10],
                "url": "https://www.youtube.com/watch?v=" + vid,
            })
    # enrich with real duration + views (videos.list = 1 unit per 50 ids)
    ids = [c["videoId"] for c in candidates]
    details = {}
    for i in range(0, len(ids), 50):
        d = api_get("/videos", key, part="contentDetails,statistics",
                    id=",".join(ids[i:i + 50]))
        for it in d.get("items", []):
            details[it["id"]] = it
    for c in candidates:
        it = details.get(c["videoId"], {})
        c["durationSeconds"] = iso8601_to_seconds(
            it.get("contentDetails", {}).get("duration", ""))
        c["views"] = int(it.get("statistics", {}).get("viewCount", 0))
    return candidates


def create_playlist(key, client_id, client_secret, title, description,
                    video_ids, privacy, fresh=False):
    token = get_access_token(client_id, client_secret, fresh=fresh,
                             headless=bool(os.environ.get("YT_OAUTH_NO_BROWSER")))
    pl = api_post("/playlists", token, {
        "snippet": {"title": title, "description": description},
        "status": {"privacyStatus": privacy},
    })
    pid = pl["id"]
    added, failed = 0, []
    for vid in video_ids:
        try:
            api_post("/playlistItems", token, {
                "snippet": {"playlistId": pid, "resourceId": {
                    "kind": "youtube#video", "videoId": vid}}})
            added += 1
        except SystemExit:
            sys.stderr.write("Skipping %s (not found / private)\n" % vid)
            failed.append(vid)
    print(json.dumps({
        "playlistId": pid,
        "url": "https://www.youtube.com/playlist?list=" + pid,
        "privacy": privacy, "requested": len(video_ids),
        "added": added, "failed": failed,
    }, indent=2))

# ----------------------------------------------------------------------- CLI

def _client_creds(args):
    if getattr(args, "client_secret", None):
        s = load_client_secrets(args.client_secret)
        return s["client_id"], s["client_secret"]
    cid, csec = getattr(args, "client_id", None), getattr(args, "client_key", None)
    if cid and csec:
        return cid, csec
    raise SystemExit("Provide --client-secret FILE or --client-id/--client-key.")


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    ps = sub.add_parser("search", help="search videos (API key only)")
    ps.add_argument("--api-key", required=True)
    ps.add_argument("--queries", required=True, help="semicolon-separated queries")
    ps.add_argument("--per-query", type=int, default=6)

    pc = sub.add_parser("create", help="create playlist + insert videos (OAuth)")
    pc.add_argument("--api-key", required=True)
    pc.add_argument("--client-secret", help="client_secret_*.json path")
    pc.add_argument("--client-id"); pc.add_argument("--client-key")
    pc.add_argument("--title", required=True)
    pc.add_argument("--description", default="")
    pc.add_argument("--privacy", choices=["public", "unlisted", "private"],
                    default="public")
    pc.add_argument("--video-ids", nargs="+", required=True)
    pc.add_argument("--fresh", action="store_true", help="ignore cached tokens")

    a = p.parse_args()

    if a.cmd == "search":
        print(json.dumps(search_videos(a.api_key, a.queries.split(";"),
                                       per_query=a.per_query), indent=2))

    elif a.cmd == "create":
        cid, csec = _client_creds(a)
        create_playlist(a.api_key, cid, csec, a.title, a.description,
                        a.video_ids, a.privacy, fresh=a.fresh)


if __name__ == "__main__":
    main()




