---
description: Full video production pipeline — from trends to YouTube in one command
argument-hint: "topic or 'auto' for trend-based selection"
---

Launch the Video Factory agent to produce a complete video.

**Usage:**
- `/video-factory DeepSeek V4 release` — make a video about a specific topic
- `/video-factory auto` — auto-detect best trending topic
- `/video-factory auto --format short` — YouTube Short (15-25s)
- `/video-factory auto --format medium` — Medium video (60-90s)
- `/video-factory "тема" --no-avatar` — AI video only, no HeyGen avatar
- `/video-factory "тема" --no-upload` — produce video but don't upload to YouTube

**What happens:**
1. Trend Discovery (if auto) — finds viral topics across Reddit, X, TikTok, YouTube
2. Script Generation — hook-value-abrupt formula, optimized for retention
3. Visual Production — HeyGen avatar + Veo 3.1 b-roll (parallel)
4. Audio Production — ElevenLabs voiceover + music with ducking
5. Post-Production — assembly, subtitles, thumbnail
6. YouTube Upload — as Private first, then you review and approve

Topic: $ARGUMENTS

Read the Agent `video-factory` definition and execute the full pipeline for the specified topic.
