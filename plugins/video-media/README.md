# Video Production

> 8-role production pipeline (brief to QC), generation (Runway), avatars (HeyGen/D-ID), edit, download, export, subtitles, transcripts.

Part of the **[hamidun marketplace](../../README.md)**.

## What's inside

| Skill | What it does |
|-------|--------------|
| `did` | D-ID: говорящая голова из фото + текст или аудио. |
| `heygen` | HeyGen API v3: AI-аватар видео, digital-twin, lip-sync перевод, Voice Clone. |
| `submagic` | Submagic API: ИИ-субтитры, Magic Brolls/Zooms, Magic Clips (YouTube в нарезку). |
| `video-downloader` | Скачивание видео с YouTube и других площадок через yt-dlp. |
| `video-editor` | Видеомонтаж FFmpeg+Python: тишина, субтитры, рефрейм 9:16. |
| `video-export` | HTML animation → MP4 / GIF via FFmpeg (Playwright record + encode) — social explainers, product demos. |
| `video-generation` | AI-видео хаб: Veo, Sora, Seedance, Runway. |
| `video-montage` | Full 9:16 reels production — Whisper subtitles, TTS voiceover, word-accurate sync, pop-up cards, lip-sync, safe zones. |
| `video-shotcraft` | Промо-ролики продукта на Remotion: 153 рецепта кадров, 2.5D-проходы, шаблон Ink Press. |
| `void-video` | Netflix VOID — remove objects from video with physics-aware handling via a free HuggingFace Spaces API. |
| `watch-video` | Let the agent actually watch a video — timestamped frames plus transcript, so it can answer about what is on screen. |
| `youtube-transcript` | Транскрипты роликов YouTube, саммари и разбор содержимого. |

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
