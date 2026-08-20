# AI Image Generation

> Nano Banana, DALL-E, Replicate, enhancement, OCR, stickers, generative art.

Part of the **[hamidun marketplace](../../README.md)**.

## What's inside

| Skill | What it does |
|-------|--------------|
| `algorithmic-art` | Генеративное искусство на p5.js: seeded randomness, flow fields, частицы. |
| `edit-banana` | Диаграмма PNG/JPG → редактируемый DrawIO XML (локально ~/Edit-Banana). |
| `image-enhancer` | Улучшение картинок: апскейл, denoise, оптимизация (Pillow/OpenCV). |
| `image-generation` | Промпт-инжиниринг генерации картинок (DALL-E, Midjourney, SD, Gemini) + сюрреализм-пресет Крестинина. |
| `nano-banana-pro` | Prompt engineering Nano Banana Pro (Gemini Image): реставрация фото, VK-креативы без VPN. |
| `ocr-restore` | Восстановление битого OCR по ступеням с оценкой качества: склейки, мусорные символы. |
| `openai-dalle` | OpenAI media API (OPENAI_API_KEY): gpt-image-2 face-swap/edit, Sora 2 video, Whisper STT, TTS, embeddings. |
| `replicate` | Replicate: запуск 1000+ AI-моделей по API (FLUX, SDXL, Whisper), если модели нет нативно. |
| `slack-gif-creator` | Анимированные GIF под лимиты Slack (emoji 64KB): валидаторы и анимационные примитивы. |
| `sticker-pack-generator` | Стикерпаки Telegram: static WEBP, WebM VP9-alpha, кастом-эмодзи; Telethon upload через @Stickers. |

### Agents

- `image-generator`

## Install

```text
/plugin marketplace add JHamidun/claude-code-config-pack
/plugin install image-gen@hamidun
```

Enable it with `/plugin` — the skills then activate automatically when relevant.

## Related plugins

`video-media` · `audio-voice`

---

MIT © [Zhemal Khamidun](https://github.com/JHamidun)
