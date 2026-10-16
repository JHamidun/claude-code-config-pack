# Video Production

> 8-role production pipeline (brief to QC), generation (Runway), avatars (HeyGen/D-ID), edit, download, export, subtitles, transcripts.

Part of the **[hamidun marketplace](../../README.md)**.

## What's inside

| Skill | What it does |
|-------|--------------|
| `code-cartoon` | Мультик кодом в MP4 с героем, голосом и звуком: цветной карандаш, глянцевое 3D с рисованным героем, мел, стекло, растр, коллаж, частицы, акварель. |
| `did` | D-ID: говорящая голова из фото + текст или аудио. |
| `heygen` | HeyGen API v3: AI-аватар видео, digital-twin, lip-sync перевод, Voice Clone. |
| `hyperframes` | Видео из HTML/GSAP (HyperFrames): титры, моушн, слайды, порт из Remotion. |
| `sketch-course-video` | Урок или сторис из записи спикера со скетч-анимацией на Remotion: рисунок по контурам, караоке, кружок лица, CTA. |
| `submagic` | Submagic API: ИИ-субтитры, Magic Brolls/Zooms, Magic Clips (YouTube в нарезку). |
| `video-downloader` | Скачивание видео с YouTube и других площадок через yt-dlp. |
| `video-editor` | Видеомонтаж FFmpeg+Python: тишина, субтитры, рефрейм 9:16. |
| `video-export` | Покадровый рендер готовой HTML-анимации в MP4 или GIF (Playwright + ffmpeg). |
| `video-generation` | AI-видео хаб: Veo, Seedance 2.5, Runway, Kling. |
| `video-montage` | Конвейер ролика ролями: бриф→сценарий→музыка→раскадровка→монтаж; reels 9:16. |
| `video-shotcraft` | Промо-ролики продукта на Remotion: 152 рецепта кадров, Ink Press. |
| `void-video` | Netflix VOID: удаление объектов из видео с физикой взаимодействий, HuggingFace Spaces бесплатно. |
| `watch-video` | Агент «смотрит» видео: кадры с таймкодами + транскрипт. |
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
