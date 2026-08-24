---
name: gemini-3-pro
description: "Google AI API (GOOGLE_API_KEY): Gemini text 2M контекст, embeddings, TTS, grounding. Триггеры: «gemini api», «спроси gemini». НЕ картинки→image-generation."
---

> ⚠️ **NO-KEY GUARD (обязательно):** этот функционал требует ОПЦИОНАЛЬНОГО стороннего API-ключа. Перед вызовом проверь ключ в `.credentials.master.env`. Если ключ отсутствует, пустой или placeholder (`your_*_api_key`) — **НЕ проси пользователя оплатить счёт, включить биллинг или купить API**. Скажи одной строкой: «Эта функция опциональна и требует свой API-ключ (например, бесплатный ключ на aistudio.google.com); из коробки всё остальное работает по подписке Claude» — и предложи альтернативу или продолжай без неё.

# Gemini API Skill (Full Suite)

> **See Also:**
> - **[image-generation](../image-generation/SKILL.md)** — генерация картинок (канон NB2/Lite/Pro)
> - **[nano-banana-pro](../nano-banana-pro/SKILL.md)** — prompt engineering для Gemini image
> - **[video-generation](../video-generation/SKILL.md)** — генерация видео (Veo/Sora/Seedance)
> - **[openai-dalle](../openai-dalle/SKILL.md)** — OpenAI suite: gpt-image-2, Sora, Whisper, TTS
> - **[autonomous-agent-creator](../autonomous-agent-creator/references/gemini-api-models.md)** — живой каталог моделей + discovery curl + OpenAI-shim для ботов

## Overview

Скилл для Google AI (Gemini) API — то, что Opus/Fable не делают сами:

- **Text по API** — для автономных ботов/агентов вне Claude Code (2M контекст у Pro)
- **Multimodal understanding** — анализ изображений, видео (вкл. YouTube URL), аудио, PDF
- **Embeddings** — `gemini-embedding-001`
- **Tools** — Google Search grounding, code execution, URL context, function calling
- **TTS / Live API** — озвучка и realtime аудио-диалог
- **Structured output** — JSON по схеме

⚠️ **НЕ здесь**: генерация картинок и видео. Канон — `config/models.md`:
картинки → skill `image-generation` (NB2 `gemini-3.1-flash-image-preview` default / NB2 Lite / NB Pro),
видео → skill `video-generation` (`veo-3.1-generate-preview`, `sora-2-pro`).
Запрещённые модели (gemini-2.0-flash*, gemini-2.5-flash-image, gemini-pro-vision, gemini-1.x) — `rules/dont-do.md`.

## API Key

```python
# Ключи: ~/.claude/.credentials.master.env
# Канон: GOOGLE_API_KEY (GEMINI_API_KEY конфликтует с SDK при image-генерации)
import os
os.environ.pop('GEMINI_API_KEY', None)   # снять конфликт SDK
api_key = os.getenv('GOOGLE_API_KEY')
```

## SDK

```bash
pip install google-genai
```

```python
from google import genai
from google.genai import types

client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))
```

⛔ Старый SDK `google.generativeai` (`import google.generativeai as genai`, `genai.configure(...)`, `GenerativeModel`) **ЗАПРЕЩЁН** (`rules/dont-do.md` п.9). Только `from google import genai`.

## Актуальные модели (сверка июль 2026)

| Модель | Контекст | Роль |
|--------|----------|------|
| `gemini-3.1-pro-preview` | ~2M | Лучший reasoning / длинные документы |
| `gemini-3.5-flash` | ~1M | **Рекомендованный primary для ботов** (быстрый, дешёвый) |
| `gemini-3.1-flash-lite` | ~1M | Самый дешёвый, простые Q&A/классификация |
| `gemini-3-flash-preview` | ~1M | Beta, местами ограничен |
| `gemini-2.5-pro` / `gemini-2.5-flash` | 1M | Стабильные fallback |
| `gemini-embedding-001` | — | Embeddings |
| `gemini-3.1-flash-tts-preview` | — | TTS |

Каталог дрейфует между ключами и релизами — **перед хардкодом модели в конфиг прогони discovery**:

```bash
curl -s "https://generativelanguage.googleapis.com/v1beta/models?key=${GOOGLE_API_KEY}" | python -m json.tool
```

Полная таблица (latency/лимиты/прайс/gotchas) — `autonomous-agent-creator/references/gemini-api-models.md`.

## Text Generation

```python
def gemini_chat(prompt: str, system: str | None = None,
                model: str = "gemini-3.5-flash") -> str:
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(system_instruction=system),
    )
    return response.text

result = gemini_chat("Explain quantum computing",
                     model="gemini-3.1-pro-preview")  # когда нужно качество/2M
```

> В Claude Code текст/код/reasoning делают Opus/Fable по подписке — Gemini-текст нужен для автономных ботов, кросс-валидации (skill `multi-model-gateway`) и 2M-контекста.

## Multimodal Understanding

### Изображения

```python
from PIL import Image

def analyze_image(image_path: str, prompt: str) -> str:
    img = Image.open(image_path)
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=[prompt, img],           # можно несколько картинок списком
    )
    return response.text
```

### Видео / аудио / PDF (Files API)

```python
import time

def analyze_file(file_path: str, prompt: str,
                 model: str = "gemini-3.1-pro-preview") -> str:
    """Видео, аудио, PDF, большие документы (2M контекст)."""
    f = client.files.upload(file=file_path)
    while f.state == "PROCESSING":
        time.sleep(2)
        f = client.files.get(name=f.name)
    response = client.models.generate_content(model=model, contents=[prompt, f])
    return response.text

def transcribe_audio(audio_path: str) -> str:
    return analyze_file(audio_path,
        "Transcribe this audio accurately. Include speaker labels.")
```

### YouTube URL

```python
def analyze_youtube(url: str, prompt: str) -> str:
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=types.Content(parts=[
            types.Part(file_data=types.FileData(file_uri=url)),
            types.Part(text=prompt),
        ]),
    )
    return response.text
```

## Structured Output (JSON)

```python
import json

def structured_output(prompt: str, schema: dict) -> dict:
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=schema,       # или Pydantic-модель
        ),
    )
    return json.loads(response.text)
```

## Streaming и Chat

```python
# Streaming
for chunk in client.models.generate_content_stream(
        model="gemini-3.5-flash", contents=prompt):
    print(chunk.text, end="")

# Multi-turn chat
chat = client.chats.create(
    model="gemini-3.5-flash",
    config=types.GenerateContentConfig(system_instruction="You are a coding assistant."),
)
r1 = chat.send_message("Write a Python function to sort a list")
r2 = chat.send_message("Now add type hints")
```

## Built-in Tools

### Google Search grounding

```python
def grounded(query: str):
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=query,
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
        ),
    )
    return {
        "text": response.text,
        "grounding": response.candidates[0].grounding_metadata,
    }
```

### Code execution (sandbox)

```python
def execute_code(prompt: str) -> str:
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[types.Tool(code_execution=types.ToolCodeExecution())],
        ),
    )
    for part in response.candidates[0].content.parts:
        if getattr(part, "executable_code", None):
            print("CODE:", part.executable_code.code)
        if getattr(part, "code_execution_result", None):
            print("RESULT:", part.code_execution_result.output)
    return response.text
```

### URL context

```python
response = client.models.generate_content(
    model="gemini-3.5-flash",
    contents=f"Summarize: https://example.com/article",
    config=types.GenerateContentConfig(
        tools=[types.Tool(url_context=types.UrlContext())],
    ),
)
```

### Function calling

```python
def get_weather(city: str) -> str:
    """Get current weather for a city."""
    ...

response = client.models.generate_content(
    model="gemini-3.5-flash",
    contents="Погода в город?",
    config=types.GenerateContentConfig(tools=[get_weather]),  # SDK сам строит схему из сигнатуры
)
```

## Embeddings

```python
def get_embeddings(texts: list[str],
                   task: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
    """task: RETRIEVAL_DOCUMENT | RETRIEVAL_QUERY | SEMANTIC_SIMILARITY |
             CLASSIFICATION | CLUSTERING"""
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=texts,
        config=types.EmbedContentConfig(task_type=task),
    )
    return [e.values for e in result.embeddings]
```

Альтернатива (основной стек brain/RAG) — OpenAI `text-embedding-3-large`, см. `config/models.md`.

## TTS

```python
def tts(text: str, out_path: str, voice: str = "Kore"):
    """Голоса: Puck, Charon, Kore, Fenrir, Aoede и др."""
    response = client.models.generate_content(
        model="gemini-3.1-flash-tts-preview",
        contents=text,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice))),
        ),
    )
    with open(out_path, "wb") as f:   # PCM 24kHz — при необходимости завернуть в WAV
        f.write(response.candidates[0].content.parts[0].inline_data.data)
```

Для продакшн-озвучки основной канон — ElevenLabs (skill `elevenlabs`) / `tts-1-hd`.

## Live API (realtime аудио/STT)

```python
async def live_session(audio_bytes: bytes):
    """Realtime диалог: аудио на вход, аудио/текст на выход, tools внутри сессии.
    Live-модель бери из discovery (live-эндпоинты дрейфуют чаще остальных)."""
    config = {"response_modalities": ["AUDIO"]}
    async with client.aio.live.connect(model=LIVE_MODEL, config=config) as session:
        await session.send_realtime_input(
            audio=types.Blob(data=audio_bytes, mime_type="audio/pcm;rate=16000"))
        async for msg in session.receive():
            if msg.data:
                yield msg.data
```

Для батч-транскрипции используй Files API (`transcribe_audio` выше) или Deepgram/Whisper (skill `deepgram`).

## Для ботов: OpenAI-compat shim

Hermes/боты ходят в Gemini через OpenAI-совместимый эндпоинт:

```
base_url: https://generativelanguage.googleapis.com/v1beta/openai
model:    gemini-3.5-flash        # bare name, без "models/"
```

404 → неправильный base_url или модели нет на ключе (прогони discovery). Детали, rate limits (free tier ~1500 req/day), пустой `message {}` при выжранном reasoning-бюджете — в `autonomous-agent-creator/references/gemini-api-models.md`.

## Генерация картинок/видео — указатели (канон)

Здесь НЕ реализуется. Канон-модели из `config/models.md`:

| Задача | Модель | Где |
|--------|--------|-----|
| Картинки (default) | `gemini-3.1-flash-image-preview` (NB2) | skill `image-generation` |
| Картинки (обложки news) | `gemini-3.1-flash-lite-image` (NB2 Lite) | skill `image-generation` |
| Картинки (флагман) | `gemini-3-pro-image-preview` (NB Pro) | skill `nano-banana-pro` |
| Видео | `veo-3.1-generate-preview` / `sora-2-pro` | skill `video-generation` |

Ключ для image — `GOOGLE_API_KEY` + `os.environ.pop('GEMINI_API_KEY', None)`; модель отдаёт **JPEG, не PNG**.

## Прайс (ориентир, июнь-июль 2026, USD/1M токенов)

| Модель | Input | Output |
|--------|-------|--------|
| gemini-3.5-flash | ~$0.10 | ~$0.40 |
| gemini-3.1-flash-lite | ~$0.04 | ~$0.20 |
| gemini-3.1-pro-preview | ~$1.25 | ~$10 |

Gemini Flash ~30× дешевле Sonnet на бот-нагрузках. Актуализация — в reference-файле.

## Quick Reference

| Задача | Код |
|--------|-----|
| Текст | `client.models.generate_content(model=..., contents=prompt)` |
| Стриминг | `client.models.generate_content_stream(...)` |
| Чат | `client.chats.create(model=...)` → `chat.send_message(...)` |
| Картинка/видео/PDF на вход | `client.files.upload(file=path)` → в `contents` |
| JSON по схеме | `response_mime_type="application/json"` + `response_schema` |
| Grounding | `tools=[types.Tool(google_search=types.GoogleSearch())]` |
| Code exec | `tools=[types.Tool(code_execution=types.ToolCodeExecution())]` |
| Embeddings | `client.models.embed_content(model="gemini-embedding-001", ...)` |
| Live | `client.aio.live.connect(model=..., config=...)` |

## Tips

1. **Discovery перед хардкодом** — модели дрейфуют, `gemini-3-flash` уже один раз молча умер в 404.
2. **2M контекст** (`gemini-3.1-pro-preview`) — целые кодбазы/книги одним запросом.
3. **Для ботов** — `gemini-3.5-flash` primary, `gemini-2.5-flash` known-good fallback.
4. **В Claude Code** — Gemini только для того, что Opus не может: multimodal-анализ, 2M, grounding, embeddings.
5. **Старый SDK запрещён** — только `from google import genai`.
6. **Image/video — НЕ здесь** — skill `image-generation` / `video-generation`, канон `config/models.md`.
