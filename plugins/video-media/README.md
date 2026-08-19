# Video Production

> 8-role production pipeline (brief to QC), generation (Runway), avatars (HeyGen/D-ID), edit, download, export, subtitles, transcripts.

Part of the **[hamidun marketplace](../../README.md)**.

## What's inside

| Skill | What it does |
|-------|--------------|
| `did` | D-ID talking head from a photo plus text or audio. |
| `heygen` | HeyGen API v3: AI avatar video, digital twin, lip-sync translation, voice clone. |
| `submagic` | your subtitle API (v1 REST): AI captions, Magic Brolls/Zooms, Magic Clips (YouTube to multi-clip), silence removal, social publishing. |
| `video-downloader` | Download videos from YouTube and other platforms with yt-dlp |
| `video-editor` | Видеомонтаж FFmpeg+Python: тишина, субтитры, рефрейм 9:16. |
| `video-export` | HTML animation → MP4 / GIF via FFmpeg (Playwright record + encode) — social explainers, product demos. |
| `video-generation` | AI-видео хаб: Veo, Sora, Seedance, Runway, Higgsfield. |
| `video-montage` | Full 9:16 reels production — Whisper subtitles, TTS voiceover, word-accurate sync, pop-up cards, lip-sync, safe zones. |
| `video-shotcraft` | Промо-ролики продукта на Remotion: 153 рецепта кадров, 2.5D-проходы, шаблон Ink Press. |
| `void-video` | Netflix VOID — remove objects from video with physics-aware handling via a free HuggingFace Spaces API. |
| `watch-video` | Let the agent actually watch a video — timestamped frames plus transcript, so it can answer about what is on screen. |
| `youtube-transcript` | Fetch YouTube video transcripts, summaries, and content analysis |

### Agents

- `vf-brief`
- `vf-editor`
- `vf-operator`
- `vf-prompter`
- `vf-qc`
- `vf-screenwriter`
- `vf-sound`
- `vf-storyboard`
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
