# AI Models & Services Reference

> Актуальная таблица моделей. Получена через API 30.01.2026.
> Используй ТОЛЬКО эти model ID — они проверены.

---

## ⚠️ Из коробки — только подписка Claude (БЕСПЛАТНО для пользователя)

Свежая установка работает БЕЗ единого стороннего ключа: весь текст/код/reasoning — Opus по подписке Claude. Все таблицы внешних моделей ниже — ОПЦИОНАЛЬНЫЕ платные интеграции.

**Правило NO-KEY:** прежде чем вызывать любой внешний API (Gemini, OpenAI, ElevenLabs…) — проверь ключ в `.credentials.master.env`. Ключ отсутствует/пустой/placeholder (`your_*_api_key`) → НЕ вызывай API и НЕ проси пользователя оплатить или включить биллинг. Ответь: «Эта функция опциональна, нужен свой API-ключ» + как получить (для Gemini: aistudio.google.com, есть бесплатный tier) — и предложи альтернативу.

## Контекст использования

**Claude Code работает на Opus 4.6 через подписку** (не по API).
Opus закрывает ВСЕ текстовые, кодовые и reasoning задачи внутри Claude Code.

Внешние модели по API нужны в двух случаях:
1. **В Claude Code** — только для того, что Opus не может (медиа, поиск, embeddings)
2. **В автономных ботах/агентах** — для любых задач, т.к. они работают вне Claude Code

### Модели для использования в Claude Code (только то, что Opus не может)

| Задача | Модель | Провайдер |
|--------|--------|-----------|
| **Генерация картинок** (опционально, нужен GOOGLE_API_KEY) | `gemini-3.1-flash-image-preview` (default) или `gemini-3-pro-image-preview` (pro) или `gpt-image-1.5` | Google / OpenAI |
| **Генерация видео** | `sora-2-pro` или `veo-3.1-generate-preview` | OpenAI / Google |
| **Видео с аватаром** | HeyGen API (skill `heygen`) | HeyGen |
| **TTS / озвучка** | `eleven_multilingual_v2` или `tts-1-hd` | ElevenLabs / OpenAI |
| **Транскрипция** | `whisper-1` или Deepgram API | OpenAI / Deepgram |
| **Deep Research** | `o3-deep-research` или `deep-research-pro-preview-12-2025` | OpenAI / Google |
| **Online search** | `sonar` (Perplexity) — но WebFetch/WebSearch часто достаточно | Perplexity |
| **Embeddings** | `text-embedding-3-large` или `gemini-embedding-001` | OpenAI / Google |

**НЕ вызывай внешние API для:** текста, кода, reasoning, ревью, рефакторинга — Opus 4.6 через подписку делает это сам.

---

## Модели для автономных ботов и агентов

Когда создаёшь ботов, агентов или автономные системы — выбирай модель по задаче:

### Текст / Чат

| Уровень | Model ID | Провайдер | Env Var |
|---------|----------|-----------|---------|
| Лучший | `gpt-5.2` | OpenAI | OPENAI_API_KEY |
| Быстрый | `gpt-5-mini` | OpenAI | OPENAI_API_KEY |
| Дешёвый | `gpt-5-nano` | OpenAI | OPENAI_API_KEY |
| Лучший (Anthropic) | `claude-opus-4-5-20251101` | Anthropic | ANTHROPIC_API_KEY |
| Быстрый (Anthropic) | `claude-sonnet-4-5-20250929` | Anthropic | ANTHROPIC_API_KEY |
| Дешёвый (Anthropic) | `claude-haiku-4-5-20251001` | Anthropic | ANTHROPIC_API_KEY |
| Лучший (Google) | `gemini-3-pro-preview` | Google | GEMINI_API_KEY |
| Быстрый (Google) | `gemini-3-flash-preview` | Google | GEMINI_API_KEY |
| Альтернатива | `deepseek-chat` | DeepSeek | DEEPSEEK_API_KEY |

### Код (автономные агенты)

| Уровень | Model ID | Провайдер | Env Var |
|---------|----------|-----------|---------|
| Агентный | `gpt-5.2-codex` | OpenAI | OPENAI_API_KEY |
| Макс | `gpt-5.1-codex-max` | OpenAI | OPENAI_API_KEY |
| Быстрый | `codex-mini-latest` | OpenAI | OPENAI_API_KEY |
| Среднее | `gpt-4.1` | OpenAI | OPENAI_API_KEY |

### Reasoning

| Уровень | Model ID | Провайдер | Env Var |
|---------|----------|-----------|---------|
| Максимум | `o3-pro` | OpenAI | OPENAI_API_KEY |
| Быстрый | `o4-mini` | OpenAI | OPENAI_API_KEY |
| Альтернатива | `deepseek-reasoner` | DeepSeek | DEEPSEEK_API_KEY |

### Медиа / Специализированные

| Задача | Model ID | Провайдер | Env Var |
|--------|----------|-----------|---------|
| Картинки | `gpt-image-1.5` | OpenAI | OPENAI_API_KEY |
| Картинки (Gemini default) | `gemini-3.1-flash-image-preview` | Google | GOOGLE_API_KEY |
| Картинки (Gemini pro) | `gemini-3-pro-image-preview` | Google | GOOGLE_API_KEY |
| Картинки (Imagen) | `imagen-4.0-ultra-generate-001` | Google | GEMINI_API_KEY |
| Картинки (Imagen fast) | `imagen-4.0-fast-generate-001` | Google | GEMINI_API_KEY |
| Видео | `sora-2-pro` | OpenAI | OPENAI_API_KEY |
| Видео (Google) | `veo-3.1-generate-preview` | Google | GEMINI_API_KEY |
| Видео (Google fast) | `veo-3.0-fast-generate-001` | Google | GEMINI_API_KEY |
| Видео аватары | HeyGen / D-ID API | HeyGen/D-ID | HEYGEN/DID_API_KEY |
| TTS | `tts-1-hd` | OpenAI | OPENAI_API_KEY |
| TTS (ElevenLabs) | `eleven_multilingual_v2` | ElevenLabs | ELEVENLABS_API_KEY |
| Транскрипция | `whisper-1` | OpenAI | OPENAI_API_KEY |
| Realtime voice | `gpt-realtime` | OpenAI | OPENAI_API_KEY |
| Deep Research | `o3-deep-research` | OpenAI | OPENAI_API_KEY |
| Deep Research (Google) | `deep-research-pro-preview-12-2025` | Google | GEMINI_API_KEY |
| Online search | `sonar` | Perplexity | PERPLEXITY_API_KEY |
| Embeddings | `text-embedding-3-large` | OpenAI | OPENAI_API_KEY |
| Embeddings (Google) | `gemini-embedding-001` | Google | GEMINI_API_KEY |
| 1000+ моделей | Replicate | Replicate | REPLICATE_API_KEY |

---

## Генерация картинок — Nano Banana 2 (default)

```python
from google import genai
from google.genai import types
import os

os.environ.pop('GEMINI_API_KEY', None)  # SDK conflict
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",  # Nano Banana 2 (fast, 4K)
    # model="gemini-3-pro-image-preview",    # Nano Banana Pro (higher quality)
    contents="Generate image: описание картинки...",
    config=types.GenerateContentConfig(response_modalities=['IMAGE', 'TEXT'])
)
# ВАЖНО: модель генерирует JPEG, не PNG!
with open("image.jpg", "wb") as f:
    f.write(response.candidates[0].content.parts[0].inline_data.data)
```

---

## Полный список доступных моделей (из API)

### OpenAI (121 модель) — ключевые

```
gpt-5.2, gpt-5.2-codex, gpt-5.2-pro
gpt-5.1, gpt-5.1-codex, gpt-5.1-codex-max, gpt-5.1-codex-mini
gpt-5, gpt-5-mini, gpt-5-nano, gpt-5-pro, gpt-5-codex
gpt-4.1, gpt-4.1-mini, gpt-4.1-nano
gpt-4o, gpt-4o-mini
o3-pro, o3, o3-mini, o3-deep-research
o4-mini, o4-mini-deep-research
gpt-image-1, gpt-image-1-mini, gpt-image-1.5
dall-e-3, sora-2, sora-2-pro
whisper-1, tts-1-hd
gpt-realtime, gpt-audio
codex-mini-latest
```

### Anthropic (9 моделей)

```
claude-opus-4-5-20251101
claude-opus-4-1-20250805
claude-opus-4-20250514
claude-sonnet-4-5-20250929
claude-sonnet-4-20250514
claude-haiku-4-5-20251001
claude-3-7-sonnet-20250219
claude-3-5-haiku-20241022
claude-3-haiku-20240307
```

### Google Gemini (47 моделей) — ключевые

```
gemini-3.1-pro-preview, gemini-3-pro-image-preview, gemini-3.1-flash-image-preview, gemini-3-flash-preview
gemini-2.5-pro, gemini-2.5-flash, gemini-2.5-flash-image, gemini-2.5-flash-lite
gemini-2.0-flash, gemini-2.0-flash-lite
imagen-4.0-ultra-generate-001, imagen-4.0-generate-001, imagen-4.0-fast-generate-001
veo-3.1-generate-preview, veo-3.1-fast-generate-preview
veo-3.0-generate-001, veo-3.0-fast-generate-001
nano-banana-pro-preview
deep-research-pro-preview-12-2025
```

### DeepSeek (2 модели)

```
deepseek-chat
deepseek-reasoner
```

### Perplexity

```
sonar (Online search + answer)
```

---

## ЗАПРЕЩЕНО

- `gemini-pro-vision` — устаревшая, retired
- `imagen-*` — для генерации через Gemini SDK, не напрямую
- Старый SDK `google.generativeai` — используй `from google import genai`
- Сохранять jpg как .png — всегда проверяй формат
- Любые модели `gemini-1.0-*`, `gemini-1.5-*` — retired, вернут 404

## API ключи

Все ключи: `~/.claude/.credentials.master.env`
