# 🎬 YouTube Playlist Skill — Complete Setup & Recovery Guide

A step-by-step guide to set up, authenticate, and use the **YouTube Playlist AI Skill** (or standalone Python CLI) to automatically curate and build real YouTube playlists directly on your Google Account.

---

## 📋 Table of Contents
1. [Prerequisites](#1-prerequisites)
2. [Phase 1: Google Cloud Console Setup (One-Time)](#2-phase-1-google-cloud-console-setup-one-time)
   - [Step 1: Create a Google Cloud Project](#step-1-create-a-google-cloud-project)
   - [Step 2: Enable the YouTube Data API v3](#step-2-enable-the-youtube-data-api-v3)
   - [Step 3: Generate an API Key (for Searching)](#step-3-generate-an-api-key-for-searching)
   - [Step 4: Configure OAuth Consent Screen](#step-4-configure-oauth-consent-screen-critical)
   - [Step 5: Create OAuth Desktop Client (for Writing Playlists)](#step-5-create-oauth-desktop-client-id)
3. [Phase 2: Project Setup & Running](#3-phase-2-project-setup--running)
   - [File Layout](#file-layout)
   - [Running Searches (API Key Only)](#1-searching-videos-api-key-only)
   - [Creating the Playlist (OAuth)](#2-creating--populating-the-playlist-oauth)
4. [Phase 3: Troubleshooting & Recovery (The Cheat Sheet)](#4-phase-3-troubleshooting--recovery-the-cheat-sheet)
   - [Fix: `invalid_grant` / Expired Refresh Token (7-Day Expiry)](#1-invalid_grant-error-400-most-common)
   - [Fix: `access_denied` / User Not Authorized](#2-access_denied-403-during-browser-login)
   - [Fix: "Google hasn't verified this app" Screen](#3-google-hasnt-verified-this-app-warning)
   - [Fix: `quotaExceeded` (403)](#4-quotaexceeded-403)
5. [Using with AI Agents (Antigravity / Claude Code / Cline)](#5-using-with-ai-agents)

---

## 1. Prerequisites
- **Python 3.8+** installed (`python --version`).
- **Zero dependencies**: Uses Python’s standard library only (no `pip install` required).
- A **Google Account** with an active YouTube channel.

---

## 2. Phase 1: Google Cloud Console Setup (One-Time)

### Step 1: Create a Google Cloud Project
1. Open the [Google Cloud Project Creation Page](https://console.cloud.google.com/projectcreate).
2. Enter a **Project Name** (e.g. `YouTube Playlist Automation`).
3. Click **Create** and wait ~15 seconds for the project to provision.
4. Ensure your new project is selected in the top navigation bar.

---

### Step 2: Enable the YouTube Data API v3
1. Open the [YouTube Data API v3 Library Page](https://console.cloud.google.com/apis/library/youtube.googleapis.com).
2. Verify your project name is selected in the top bar.
3. Click the blue **Enable** button.

---

### Step 3: Generate an API Key (for Searching)
1. Navigate to the [Google Cloud Credentials Page](https://console.cloud.google.com/apis/credentials).
2. Click **+ CREATE CREDENTIALS** (at the top) → Select **API key**.
3. A dialog will show your new API key (starts with `AIzaSy...`).
4. Copy and save it safely in a text file (e.g. `youtube_api_key.txt`).

---

### Step 4: Configure OAuth Consent Screen *(CRITICAL)*
> [!IMPORTANT]
> If you skip adding yourself as a **Test User**, Google will block login with an `access_denied` error.

1. Go to the [OAuth Consent Screen Config Page](https://console.cloud.google.com/apis/credentials/consent).
2. Under **User Type**, choose **External** → Click **Create**.
3. **App Information**:
   - **App name**: `YouTube Playlist Builder`
   - **User support email**: Select your own Gmail address.
   - **Developer contact information**: Enter your own Gmail address.
   - Click **Save and Continue**.
4. **Scopes**:
   - Click **Save and Continue** (skip this page; scopes are requested dynamically at runtime).
5. **Test Users**:
   - Click **+ ADD USERS**.
   - Enter your **exact Gmail address** (the one that owns your YouTube channel).
   - Click **Add**, then click **Save and Continue**.
6. Review summary and click **Back to Dashboard**.

---

### Step 5: Create OAuth Desktop Client ID
1. Go back to the [Google Cloud Credentials Page](https://console.cloud.google.com/apis/credentials).
2. Click **+ CREATE CREDENTIALS** → Select **OAuth client ID**.
3. Fill in:
   - **Application type**: Choose **Desktop app** *(do NOT choose Web application)*.
   - **Name**: `yt-playlist-client`.
4. Click **Create**.
5. On the popup window, click **Download JSON**.
6. Rename this downloaded file to `client_secret.json`.

---

## 3. Phase 2: Project Setup & Running

### File Layout
Place your script and credentials in a project directory like this:
```text
my-playlist-tool/
├── client_secret.json            <-- Downloaded in Step 5
├── youtube_api_key.txt           <-- API key from Step 3
└── scripts/
    └── yt_playlist.py            <-- The skill CLI script
```

---

### 1. Searching Videos (API Key Only)
Run queries across topics to get enriched video candidates with view counts and exact durations in seconds:

```bash
python scripts/yt_playlist.py search \
  --api-key "YOUR_YOUTUBE_API_KEY" \
  --queries "python flask tutorial;flask get post request;matplotlib crash course" \
  --per-query 5
```
*Output: JSON list containing video IDs, titles, channels, view counts, and duration.*

---

### 2. Creating & Populating the Playlist (OAuth)
Once you've selected the video IDs you want, create and populate the playlist:

```bash
python scripts/yt_playlist.py create \
  --api-key "YOUR_YOUTUBE_API_KEY" \
  --client-secret client_secret.json \
  --title "Unit 5: Python Web Dev & Data Visualization" \
  --description "Curated Flask & Matplotlib study playlist." \
  --privacy unlisted \
  --video-ids dTCiUa-s2YE 0HXg9_r_7MM 2KY5AaFvWtE
```

#### What happens on first run:
1. The script launches a temporary local server on `http://localhost:8765`.
2. A browser window opens automatically asking you to log into Google.
3. Select your Google account and grant permissions.
4. Tokens are cached locally in `~/.yt_playlist_tokens.json` for future runs.
5. The playlist is created in your account and videos are inserted one by one!

---

## 4. Phase 3: Troubleshooting & Recovery (The Cheat Sheet)

### 1. `invalid_grant` / Error 400 *(Most Common)*
- **Why it happens**: For Google Cloud projects in "Testing" mode (unpublished), refresh tokens expire automatically every **7 days**.
- **How to recover**: Run the `create` command with the `--fresh` flag:
  ```bash
  python scripts/yt_playlist.py create --fresh ...
  ```
  This ignores the stale token cache and immediately triggers a fresh browser sign-in.

---

### 2. `access_denied` (403) During Browser Login
- **Why it happens**: The Google account you logged in with was not added to the **Test Users** list on Google Cloud.
- **How to recover**:
  1. Open [OAuth Consent Screen](https://console.cloud.google.com/apis/credentials/consent).
  2. Click **Test Users** → **+ ADD USERS**.
  3. Enter your Gmail address and click **Save**.
  4. Re-run your `create` command with `--fresh`.

---

### 3. "Google hasn't verified this app" Warning
- **Why it happens**: The OAuth app is personal and not publicly verified by Google.
- **How to proceed**:
  1. Click **Advanced** (in small text on the warning screen).
  2. Click **Go to YouTube Playlist Builder (unsafe)**.
  3. Click **Continue / Allow**.

---

### 4. `quotaExceeded` (403)
- **Why it happens**: YouTube gives 10,000 free quota units per day.
  - `search.list` = 100 units
  - `videos.list` = 1 unit per 50 videos
  - `playlists.insert` = 50 units
  - `playlistItems.insert` = 50 units per video
  *(A 15-video playlist typically uses ~900–1,000 units).*
- **How to recover**: Free quota resets every day at **midnight Pacific Time (PT)**. Wait for the reset or switch to a new Google Cloud project.

---

### 5. Running on a Headless Machine / Remote Server (No Browser)
If you are running the script on a remote server with no GUI browser:
```bash
set YT_OAUTH_NO_BROWSER=1
python scripts/yt_playlist.py create ...
```
The script will print an authorization URL. Open it on your phone/laptop, log in, copy the final URL you are redirected to (starts with `http://localhost:8765`), and paste it back into your terminal.

---

## 5. Using with AI Agents

If using an AI coding assistant (like Antigravity, Claude Code, or Cline):
1. Place the `youtube-playlist` folder inside your agent's skills directory (`~/.gemini/config/skills/` or `~/.cline/skills/`).
2. Make sure your `youtube_api_key.txt` and `client_secret.json` exist.
3. Prompt your agent naturally:
   > *"Find the best videos for Verilog modeling styles and build an unlisted playlist on my YouTube channel."*
   The AI will generate query variations, filter out bloated/poor-quality videos, select the highest-rated picks, and run the CLI for you!

