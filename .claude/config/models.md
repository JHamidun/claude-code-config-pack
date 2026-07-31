# AI Models & Services — ЕДИНЫЙ КАНОН

> Канон моделей: Claude Code (подписка Max), image/медиа, внешние API.
> Обновлён 2026-07-18 (свод из rules/models.md + rules/dont-do.md image-канона + API-списка от 30.01.2026).
> Используй ТОЛЬКО эти model ID — они проверены.

---

## Claude Code — подписка Max (актуальные алиасы)

С подпиской Claude Code Max доступны ВСЕ модели без ограничений. Аутентификация — подписка, не API.

| Алиас | Model ID | Название | Роль |
|-------|----------|----------|------|
| `model: "opus"` | `claude-opus-4-8` | Claude Opus 4.8 | **Дефолт оркестратора / основной сессии** |
| `model: "fable"` | `claude-fable-5` | Fable 5 | **Дефолт ВСЕХ text-субагентов** (см. правило ниже) |
| `model: "sonnet"` | `claude-sonnet-4-5-20250929` | Claude Sonnet 4.5 | Доступен, но для text-субагентов НЕ дефолт |
| `model: "haiku"` | `claude-haiku-4-5-20251001` | Claude Haiku 4.5 | Быстрые/простые операции, классификация |

### ⚠️ Правило субагентов (канон из памяти, ОБЯЗАТЕЛЬНОЕ)

- **ВСЕ text-субагенты — ТОЛЬКО Fable 5** (`model: "fable"`), **≤5 одновременно** (комфортный параллелизм 3-4 в поток, при rate-limit снижай).
- Fable упал на лимите → подхватить **Opus** (resume + смена model).
- Паттерн оркестрации: **Opus — оркестратор, Fable — воркеры** в изолированном контексте; Fable промптить намерениями (цель, не пошагово).
- Старые дефолты «sonnet для субагентов / haiku для поиска» из rules/model-selection.md — это ФОЛБЭК-логика выбора уровня, но рантайм-дефолт text-воркеров = Fable 5.

```python
# Fable 5 — дефолт text-субагентов
Task(subagent_type="general-purpose", model="fable", prompt="...")
# Haiku — быстрая модель для простых задач
Task(subagent_type="general-purpose", model="haiku", prompt="...")
# Opus — оркестратор / максимальная сложность
Task(subagent_type="general-purpose", model="opus", prompt="...")
```

### Предыдущие версии Claude (доступны через API)

| Model ID | Название |
|----------|----------|
| `claude-opus-4-6` | Claude Opus 4.6 (04.02.2026; был дефолтом до Opus 4.8) |
| `claude-opus-4-5-20251101` | Claude Opus 4.5 |
| `claude-opus-4-1-20250805` | Claude Opus 4.1 |
| `claude-opus-4-20250514` | Claude Opus 4 |
| `claude-sonnet-4-20250514` | Claude Sonnet 4 |
| `claude-3-7-sonnet-20250219` | Claude Sonnet 3.7 |
| `claude-3-5-haiku-20241022` | Claude Haiku 3.5 |
| `claude-3-haiku-20240307` | Claude Haiku 3 |

---

## Контекст использования

**Claude Code работает на Opus 4.8 через подписку** (не по API).
Opus закрывает ВСЕ текстовые, кодовые и reasoning задачи внутри Claude Code; text-субагенты — Fable 5.

Внешние модели по API нужны в двух случаях:
1. **В Claude Code** — только для того, что Opus не может (медиа, поиск, embeddings)
2. **В автономных ботах/агентах** — для любых задач, т.к. они работают вне Claude Code

### Модели для использования в Claude Code (только то, что Opus не может)

| Задача | Модель | Провайдер |
|--------|--------|-----------|
| **Генерация картинок** | `gemini-3.1-flash-image-preview` (NB2, default) / `gemini-3.1-flash-lite-image` (NB2 Lite — обложки news) / `gemini-3-pro-image-preview` (NB Pro) / `gpt-image-2-2026-04-21` (OpenAI flagship) | Google / OpenAI |
| **Генерация видео** | `sora-2-pro` или `veo-3.1-generate-preview` | OpenAI / Google |
| **Видео с аватаром** | HeyGen API (skill `heygen`) | HeyGen |
| **TTS / озвучка** | `eleven_multilingual_v2` или `tts-1-hd` | ElevenLabs / OpenAI |
| **Транскрипция** | `whisper-1` или Deepgram API | OpenAI / Deepgram |
| **Deep Research** | `o3-deep-research` или `deep-research-pro-preview-12-2025` | OpenAI / Google |
| **Online search** | `sonar` (Perplexity) — но WebFetch/WebSearch часто достаточно | Perplexity |
| **Embeddings** | `text-embedding-3-large` или `gemini-embedding-001` | OpenAI / Google |

**НЕ вызывай внешние API для:** текста, кода, reasoning, ревью, рефакторинга — Opus/Fable через подписку делают это сами.

---

## Image-модели — канон Nano Banana (Gemini)

| Модель | Model ID | Роль |
|--------|----------|------|
| **Nano Banana 2 (NB2)** | `gemini-3.1-flash-image-preview` / `gemini-3.1-flash-image` | **Дефолт генерации картинок** (fast, 4K) |
| **NB2 Lite** | `gemini-3.1-flash-lite-image` | Дешевле/быстрее ×2, качество держит. **ДЕФОЛТ новостных обложек ваших контент-проектов (news/wealth)** |
| **Nano Banana Pro** | `gemini-3-pro-image-preview` / `nano-banana-pro-preview` | Флагманское качество |
| OpenAI flagship | `gpt-image-2-2026-04-21` (prev: `gpt-image-1.5`) | Альтернатива (face-swap, 2 input) |

Правила (полный список запретов — HIGH-канон в `rules/dont-do.md`, там же остаётся):

- **КЛЮЧ: `GOOGLE_API_KEY`** (НЕ GEMINI_API_KEY — конфликт SDK). Перед вызовом: `os.environ.pop('GEMINI_API_KEY', None)`.
- SDK: `from google import genai` + `types.GenerateContentConfig(response_modalities=['IMAGE', 'TEXT'])`. Старый SDK `google.generativeai` запрещён.
- Запрещённые image-модели (см. rules/dont-do.md): `gemini-2.0-flash-exp-image-generation`, `gemini-2.0-flash-exp`, `gemini-2.0-flash`, `gemini-2.5-flash-image` (NB1 устарела), `gemini-pro-vision`; `imagen-*` напрямую в Claude Code нельзя (в автономных ботах через Gemini SDK — ОК).
- Модель генерирует **JPEG, не PNG** — проверяй формат перед сохранением.

```python
from google import genai
from google.genai import types
import os

os.environ.pop('GEMINI_API_KEY', None)  # SDK conflict
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",   # Nano Banana 2 (default, fast, 4K)
    # model="gemini-3.1-flash-lite-image",    # NB2 Lite (×2 дешевле/быстрее; дефолт обложек ваших контент-проектов (news/wealth))
    # model="gemini-3-pro-image-preview",     # Nano Banana Pro (флагманское качество)
    contents="Generate image: описание картинки...",
    config=types.GenerateContentConfig(response_modalities=['IMAGE', 'TEXT'])
)
# ВАЖНО: модель генерирует JPEG, не PNG!
with open("image.jpg", "wb") as f:
    f.write(response.candidates[0].content.parts[0].inline_data.data)
```

---

## Внешние модели (кратко)

| Модель | Когда |
|--------|-------|
| `gpt-5.6` (вкл. `-sol`/`-ultra` тиры через Codex CLI по подписке) | Актуальный флагман OpenAI: кросс-валидация, ревью вторым мнением. Гайд промптинга — memory `gpt56-prompting-guide` |
| `gemini-3.1-pro-preview` | 2M контекст, multimodal, Google-экосистема |
| `o4-mini` / `o3-pro` | Математика, структурный reasoning |
| Kimi K2 | Алгоритмы, глубокий reasoning |
| `deep-research-pro-preview-12-2025` / `o3-deep-research` | Multi-step research с цитатами |

Таблицы ниже (боты/агенты) — проверенный API-список от 30.01.2026; для OpenAI-текста сверху появился `gpt-5.6` (в списке ещё нет).

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
| Картинки (OpenAI flagship) | `gpt-image-2-2026-04-21` | OpenAI | OPENAI_API_KEY |
| Картинки (OpenAI prev) | `gpt-image-1.5` | OpenAI | OPENAI_API_KEY |
| Картинки (Gemini default, NB2) | `gemini-3.1-flash-image-preview` | Google | GOOGLE_API_KEY |
| Картинки (NB2 Lite — обложки news/wealth) | `gemini-3.1-flash-lite-image` | Google | GOOGLE_API_KEY |
| Картинки (Gemini pro, NB Pro) | `gemini-3-pro-image-preview` | Google | GOOGLE_API_KEY |
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

## Полный список доступных моделей (из API)

> Снимок от 30.01.2026 — до релизов Opus 4.6 (04.02.2026), Opus 4.8 и Fable 5; актуальные Claude-алиасы — в таблице подписки Max выше.

### OpenAI (121 модель) — ключевые

```
gpt-5.2, gpt-5.2-codex, gpt-5.2-pro
gpt-5.1, gpt-5.1-codex, gpt-5.1-codex-max, gpt-5.1-codex-mini
gpt-5, gpt-5-mini, gpt-5-nano, gpt-5-pro, gpt-5-codex
gpt-4.1, gpt-4.1-mini, gpt-4.1-nano
gpt-4o, gpt-4o-mini
o3-pro, o3, o3-mini, o3-deep-research
o4-mini, o4-mini-deep-research
gpt-image-2, gpt-image-2-2026-04-21, gpt-image-1.5, gpt-image-1, gpt-image-1-mini
chatgpt-image-latest
dall-e-3, sora-2, sora-2-pro
whisper-1, tts-1-hd
gpt-realtime, gpt-audio
codex-mini-latest
```

### Anthropic (9 моделей в API-снимке)

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

+ после снимка вышли: `claude-opus-4-6`, `claude-opus-4-8`, `claude-fable-5` (подписка Max, см. выше).

### Google Gemini (47 моделей) — ключевые

```
gemini-3.1-pro-preview, gemini-3-pro-image-preview, gemini-3.1-flash-image-preview, gemini-3.1-flash-lite-image, gemini-3-flash-preview
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

> HIGH-канон запретов живёт в `rules/dont-do.md` (авто-load) — здесь дубль для полноты справочника.

- `gemini-pro-vision` — устаревшая, retired
- `imagen-*` — для генерации через Gemini SDK, не напрямую
- Старый SDK `google.generativeai` — используй `from google import genai`
- Сохранять jpg как .png — всегда проверяй формат
- Любые модели `gemini-1.0-*`, `gemini-1.5-*` — retired, вернут 404
- Image: `gemini-2.0-flash-exp-image-generation`, `gemini-2.0-flash-exp`, `gemini-2.0-flash`, `gemini-2.5-flash-image` (NB1 — есть NB2)

## API ключи

Все ключи: `~/.claude/.credentials.master.env`
