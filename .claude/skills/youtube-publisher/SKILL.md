---
name: youtube-publisher
description: "YouTube upload automation -- OAuth 2.0, resumable upload, metadata optimization, SRT captions, thumbnail, scheduling. Triggers: upload youtube, youtube upload."
---

# YouTube Publisher

Upload videos to YouTube with full metadata, captions, thumbnails, and scheduling support. Handles OAuth 2.0 auth, resumable uploads, and quota management.

## When to Use

- User wants to upload a video to YouTube
- User says "upload youtube", "youtube upload"
- Post-production step after video generation or Shorts production pipelines
- Batch upload of multiple videos with metadata

## Prerequisites

```bash
pip install google-auth-oauthlib google-api-python-client
```

Google Cloud Console setup (one-time):
1. Go to https://console.cloud.google.com
2. Create a project (or use existing)
3. Enable **YouTube Data API v3**
4. APIs & Services -> Credentials -> Create Credentials -> OAuth 2.0 Client ID -> Desktop app
5. Download `client_secret.json`
6. Save it to `~/.claude/.youtube-client-secrets.json` (or set `YOUTUBE_CLIENT_SECRETS` env var)

## OAuth Setup (One-Time)

```bash
python ~/.claude/skills/youtube-publisher/scripts/yt_oauth_setup.py
```

This opens a browser for Google sign-in and saves the token to `~/.claude/.youtube-oauth-token.json` with 0600 permissions.

Token auto-refreshes on each upload. If refresh fails, re-run the setup script.

## Upload Workflow

### 1. Basic Upload (Private by Default)

```bash
python ~/.claude/skills/youtube-publisher/scripts/yt_upload.py upload video.mp4 \
  --title "My Video Title" \
  --description "Video description here" \
  --tags "ai,tech,tutorial"
```

### 2. Full Upload with All Options

```bash
python ~/.claude/skills/youtube-publisher/scripts/yt_upload.py upload video.mp4 \
  --title "AI Revolution 2026" \
  --description "Deep dive into latest AI developments" \
  --tags "ai,machine learning,2026" \
  --category 28 \
  --thumbnail thumb.png \
  --srt captions.srt \
  --privacy private \
  --playlist PLxxxxxxxxxxxxxxxx \
  --schedule "2026-04-01T15:00:00Z"
```

### 3. Check Processing Status

```bash
python ~/.claude/skills/youtube-publisher/scripts/yt_upload.py status VIDEO_ID
```

## CLI Reference

### `upload` Subcommand

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `video` | positional | required | Path to video file (mp4, mov, avi, mkv, webm) |
| `--title` | string | filename | Video title (max 100 chars) |
| `--description` | string | "" | Video description (max 5000 chars) |
| `--tags` | string | "" | Comma-separated tags |
| `--category` | int | 28 | YouTube category ID (28=Science & Tech) |
| `--thumbnail` | path | none | PNG or JPG thumbnail image |
| `--srt` | path | none | SRT file for closed captions |
| `--privacy` | choice | private | private / unlisted / public |
| `--playlist` | string | none | Playlist ID to add video to |
| `--schedule` | string | none | ISO 8601 datetime for scheduled publish |
| `--lang` | string | en | Default language and audio language |

### `status` Subcommand

| Argument | Type | Description |
|----------|------|-------------|
| `video_id` | positional | YouTube video ID to check |

Returns: upload status, processing status, privacy status, and video URL.

## Category IDs (Common)

| ID | Category |
|----|----------|
| 1 | Film & Animation |
| 10 | Music |
| 15 | Pets & Animals |
| 17 | Sports |
| 20 | Gaming |
| 22 | People & Blogs |
| 24 | Entertainment |
| 25 | News & Politics |
| 26 | Howto & Style |
| 27 | Education |
| 28 | Science & Technology |

## Metadata Optimization

### Title Formulas (from Shorts analytics)

- **Hook + Topic**: "This Changes Everything About [Topic]"
- **Number + Benefit**: "3 AI Tools That Replace [Expensive Thing]"
- **Curiosity Gap**: "[Topic] Just Changed Forever"
- Keep 71-100 characters for Shorts (channel's proven sweet spot)
- For long-form: front-load keywords, max 100 chars

### Description Best Practices

- First 2 lines visible without "Show More" -- make them count
- Include 3-5 relevant hashtags at the end
- Add timestamps for long-form (>5 min)
- Link to related content

### Tags Strategy

- 5-15 tags total
- Mix broad ("ai") + specific ("claude code tutorial")
- Include variations and synonyms

## Shorts vs Long-Form Auto-Detection

The upload script does NOT auto-detect Shorts format. YouTube determines this server-side based on:
- Duration < 60 seconds
- Aspect ratio 9:16 (vertical)
- `#Shorts` in title or description (recommended)

For Shorts: add `#Shorts` to tags or description. The script handles metadata identically for both formats.

## Scheduling

When `--schedule` is provided:
- Video is uploaded as **private**
- `publishAt` is set to the specified ISO 8601 datetime
- YouTube automatically publishes at the scheduled time
- Privacy status must be "private" for scheduling to work

Use optimal publish times from your channel analytics (YouTube Studio) to set the schedule parameter.

```bash
# Example: schedule for next Monday at 3 PM UTC
python ~/.claude/skills/youtube-publisher/scripts/yt_upload.py upload video.mp4 \
  --title "Weekly AI Update" \
  --schedule "2026-04-06T15:00:00Z"
```

## Quota Information

YouTube Data API v3 quota: **10,000 units/day** (per project).

| Operation | Cost (units) |
|-----------|-------------|
| videos.insert (upload) | 1,600 |
| thumbnails.set | 50 |
| captions.insert | 400 |
| videos.list (status check) | 1 |
| playlistItems.insert | 50 |

**Effective limit: ~6 full uploads per day** (with thumbnail + captions).

If you hit quota limits:
- Wait until midnight Pacific Time (quota resets)
- Use a different Google Cloud project
- Apply for quota increase in Google Cloud Console

## Safety

- **Always upload as Private first** -- the default privacy is `private`
- Verify title, description, and thumbnail before changing to public
- Use `status` subcommand to confirm processing is complete
- Schedule public release using `--schedule` flag

## Token & Credential Paths

| What | Path | Source |
|------|------|--------|
| OAuth token | `~/.claude/.youtube-oauth-token.json` | Generated by yt_oauth_setup.py |
| Client secrets | `~/.claude/.youtube-client-secrets.json` | Downloaded from Google Cloud Console |
| Client secrets (override) | `$YOUTUBE_CLIENT_SECRETS` env var | Alternative path |

All credential files use 0600 permissions (owner read/write only).

## Integration with Other Skills

| Skill | How It Connects |
|-------|----------------|
| `video-editor` | Post-production editing before upload |
| `video-generation` | AI video generation -> upload |
| `youtube-transcript` | Download transcripts from uploaded videos |

## Typical Workflow (Claude Code)

```
1. User: "upload my-video.mp4 to YouTube with title 'AI Update'"
2. Claude: runs yt_upload.py upload with metadata
3. Script: authenticates, uploads (resumable), sets thumbnail/captions
4. Output: https://youtu.be/VIDEO_ID (private)
5. User: reviews and schedules/publishes
```

## Troubleshooting

| Error | Solution |
|-------|----------|
| Token not found | Run `yt_oauth_setup.py` |
| Token expired, no refresh | Re-run `yt_oauth_setup.py` |
| Quota exceeded | Wait for reset or use different project |
| Upload timeout | Script retries automatically (exponential backoff) |
| "forbidden" on upload | Check YouTube channel is verified for uploads |
| Thumbnail rejected | Must be PNG/JPG, < 2MB, 1280x720 recommended |
| Captions failed | SRT format must be valid; video must be processed first |

## Files

| File | Description |
|------|-------------|
| `SKILL.md` | This documentation |
| `scripts/yt_upload.py` | Main CLI for upload and status check |
| `scripts/yt_oauth_setup.py` | One-time OAuth setup script |
