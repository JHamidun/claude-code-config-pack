# Video Production

> Generation (Runway), avatars (HeyGen/D-ID), edit, download, export, subtitles, transcripts.

Part of the **[hamidun marketplace](../../README.md)**.

## What's inside

| Skill | What it does |
|-------|--------------|
| `did` | D-ID AI avatar videos - talking heads from photo + text/audio. |
| `heygen` | HeyGen API — AI avatar video, v3 primary (54 endpoints). |
| `submagic` | your subtitle API — AI captions, Magic Brolls/Zooms/Hook, music, silence removal, audio cleanup, AI-edit templates, Magic Clips (YouTube → multi-clip), social publishing. |
| `video-downloader` | Download videos from YouTube and other platforms with yt-dlp |
| `video-editor` | Локальный видеомонтаж на FFmpeg+Python: вырезка тишины/дублей, виральные субтитры, переходы, цветокор/LUT, авто-рефрейм 16:9→9:16, overlay-рил talking-head + AI b-roll. |
| `video-export` | HTML animation → MP4 / GIF via FFmpeg (Playwright record + encode) — social explainers, product demos. |
| `video-generation` | Полный пайплайн AI-видео: Veo, Sora, Seedance, Runway (Kling/Pika), voiceover, музыка, субтитры, сборка ffmpeg; включает движок Higgsfield… |
| `video-montage` | Full 9:16 reels production — Whisper subtitles, TTS voiceover, word-accurate sync, pop-up cards, lip-sync, safe zones. |
| `video-shotcraft` | Кинематографичные промо-ролики продукта на Remotion: 153 карточки-рецепта кадров, 2.5D-проходы по страницам, кадрирование под бит, звуковой дизайн… |
| `void-video` | Netflix VOID — remove objects from video with physics-aware handling via a free HuggingFace Spaces API. |
| `watch-video` | Let the agent actually watch a video — timestamped frames plus transcript, so it can answer about what is on screen. |
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
