---
description: Upload a video to YouTube with metadata
argument-hint: "path/to/video.mp4 --title 'Title' [--private]"
---

Quick upload a video to YouTube.

**Usage:**
- `/youtube-upload final.mp4 --title "DeepSeek обошёл GPT-5" --private`
- `/youtube-upload video.mp4 --title "Title" --tags "ai,tech" --thumbnail thumb.png`

**Prerequisites:**
1. Run `python ~/.claude/skills/youtube-publisher/scripts/yt_oauth_setup.py` once for OAuth
2. Need `~/.claude/.youtube-client-secrets.json` from Google Cloud Console

**CLI Reference:**
```bash
python ~/.claude/skills/youtube-publisher/scripts/yt_upload.py upload $ARGUMENTS
```

Read skill `youtube-publisher` for full documentation.
