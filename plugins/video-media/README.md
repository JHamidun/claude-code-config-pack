# Video Production

> Generation (Runway), avatars (HeyGen/D-ID), edit, download, export, subtitles, transcripts.

Part of the **[hamidun marketplace](../../README.md)**.

## What's inside

| Skill | What it does |
|-------|--------------|
| `d-id` | D-ID API Skill |
| `did` | D-ID AI avatar videos - talking heads from photo + text/audio. |
| `heygen` | HeyGen AI avatar video — Video Agent (prompt-to-video), precise avatar control (v2 API), AI video gen (VEO/Kling/Sora via Workflow Gateway), Starfish… |
| `runway-api` | Direct Python/MCP client for Runway ML's web API — create generations (Seedance, Gen-4.5, Kling, Multi-Shot), poll, download. |
| `submagic` | SubtitleService AI video captions, B-roll, auto-editing for short-form content |
| `video-downloader` | Download videos from YouTube and other platforms with yt-dlp |
| `video-editor` | Local video editing via FFmpeg. |
| `video-export` | HTML animation → MP4 / GIF via FFmpeg (Playwright record + encode) — social explainers, product demos. |
| `video-generation` | Full-cycle AI video production: Veo 3.1 Fast/Sora generation → ElevenLabs voiceover → music → subtitles → FFmpeg assembly |
| `void-video` | Netflix VOID — remove objects from video with physics-aware handling via a free HuggingFace Spaces API. |
| `youtube-transcript` | Fetch YouTube video transcripts, summaries, and content analysis |

### Agents

- `video-factory`

### Commands

- `/transcribe`
- `/video-factory`
- `/youtube-upload`

## Install

```text
/plugin marketplace add JHamidun/claude-code-config-pack
/plugin install video-media@hamidun
```

Enable it with `/plugin` — the skills then activate automatically when relevant.

## Related plugins

`audio-voice` · `image-gen`

---

MIT © [Zhemal Khamidun](https://github.com/JHamidun)
