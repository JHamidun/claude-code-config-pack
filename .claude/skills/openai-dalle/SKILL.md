---
name: openai-dalle
description: "OpenAI media API (OPENAI_API_KEY): gpt-image-2 (флагман, face-swap/multi-input edit), Sora 2 video, Whisper STT, TTS (6 голосов), embeddings, moderation. Триггеры: «dall-e», «gpt-image», «openai image», «sora», «whisper api», «openai tts», «openai embeddings». Канон image-моделей — rules/dont-do + config/models.md (дефолт NB2, не DALL-E/gpt-image — этот скилл когда нужен именно OpenAI)."
---

# OpenAI Media API (компакт)

> **Канон (`config/models.md`): дефолт генерации картинок = NB2** (`gemini-3.1-flash-image-preview`, skill `image-generation`).
> OpenAI-образы — для случаев, когда нужен именно OpenAI: **face-swap / edit с несколькими input-картинками (gpt-image-2), Sora-видео, Whisper, TTS**.
> DALL-E 3 — legacy (в API ещё жив, но флагман — gpt-image-2).

**See Also:**

- [image-generation](../image-generation/SKILL.md) — общий канон + prompt engineering
- [gemini-3-pro](../gemini-3-pro/SKILL.md) — Google AI suite (text/multimodal/embeddings)
- [video-generation](../video-generation/SKILL.md) — видео-хаб (Veo/Sora/Seedance роутинг)
- `references/dalle-prompt-templates.md` — prompt-шаблоны (портрет/продукт/арт/инфографика + Sora tips)

## Setup

```python
# Ключ: ~/.claude/.credentials.master.env → OPENAI_API_KEY
from openai import OpenAI
import os, base64
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
```

## Images — gpt-image-2

Актуальные ID: `gpt-image-2-2026-04-21` (флагман), `gpt-image-1.5` (prev). Возвращают **base64**, не URL.

```python
def generate_image(prompt: str, out_path: str, size: str = "1024x1024"):
    """size: 1024x1024 | 1536x1024 | 1024x1536 | auto. quality: low|medium|high|auto."""
    r = client.images.generate(
        model="gpt-image-2-2026-04-21",
        prompt=prompt,
        size=size,
        quality="high",
    )
    with open(out_path, "wb") as f:
        f.write(base64.b64decode(r.data[0].b64_json))
    return out_path
```

### Edit / face-swap (multi-input — киллер-фича)

```python
def edit_image(prompt: str, input_paths: list[str], out_path: str):
    """До нескольких input-картинок: face-swap = [оригинал_сцены, лицо].
    Канон мемов: качать ОРИГИНАЛ + face-swap 2 input, НЕ генерить сцену заново."""
    r = client.images.edit(
        model="gpt-image-2-2026-04-21",
        image=[open(p, "rb") for p in input_paths],
        prompt=prompt,
    )
    with open(out_path, "wb") as f:
        f.write(base64.b64decode(r.data[0].b64_json))
    return out_path
```

Прайс-ориентир: gpt-image-2 ~$0.02-0.19/картинка по quality/size (DALL-E 3 legacy: $0.04-0.08).

## Video — Sora 2

| Model | Цена/сек | Качество |
|-------|----------|----------|
| `sora-2` | $0.10 | Standard |
| `sora-2-pro` | $0.30 | Highest (канон models.md для видео) |

Видео с синхронным аудио, 5-60 сек, `1280x720` / `720x1280`.

```python
import time

def generate_video(prompt: str, seconds: int = 10, pro: bool = True,
                   resolution: str = "1280x720", image=None):
    v = client.videos.generate(
        model="sora-2-pro" if pro else "sora-2",
        prompt=prompt, duration=seconds, resolution=resolution,
        **({"image": image} if image else {}),   # стартовый кадр (image-to-video)
    )
    return v.id

def wait_for_video(video_id: str, timeout: int = 600) -> str:
    start = time.time()
    while time.time() - start < timeout:
        v = client.videos.retrieve(video_id)
        if v.status == "completed":
            return v.url
        if v.status == "failed":
            raise RuntimeError(f"Sora failed: {v.error}")
        time.sleep(10)
    raise TimeoutError("Sora generation timed out")
```

Prompt tips (движение камеры, действие, свет) — `references/dalle-prompt-templates.md`.

## STT — Whisper

```python
def transcribe(audio_path: str, language: str = None, fmt: str = "text"):
    """Форматы файла: mp3/mp4/m4a/wav/webm, ≤25MB. fmt: text|json|srt|vtt|verbose_json."""
    with open(audio_path, "rb") as f:
        return client.audio.transcriptions.create(
            model="whisper-1", file=f, language=language, response_format=fmt)

# Таймстемпы: response_format="verbose_json", timestamp_granularities=["word","segment"]
# Перевод на EN: client.audio.translations.create(model="whisper-1", file=f)
# SRT-субтитры: fmt="srt" → записать в .srt
```

Для больших объёмов/диаризации — skill `deepgram`.

## TTS

Голоса: `alloy` (нейтр.), `echo` (тёплый), `fable` (британский), `onyx` (низкий), `nova` (бодрый), `shimmer` (мягкий).

```python
def tts(text: str, out_path: str, voice: str = "alloy", model: str = "tts-1-hd"):
    """text ≤4096 chars; model: tts-1 (быстрее) | tts-1-hd (качество).
    Выход: .mp3/.opus/.aac/.flac/.wav/.pcm"""
    r = client.audio.speech.create(model=model, voice=voice, input=text)
    r.stream_to_file(out_path)
    return out_path
```

Для продакшн-озвучки RU — skill `elevenlabs` (`eleven_multilingual_v2`).

## Embeddings

```python
def embed(texts: list[str], model: str = "text-embedding-3-large"):
    """3-small: 1536 dims, дешевле; 3-large: 3072 dims (канон brain/RAG).
    ⚠️ pgvector-гоча: фиксируй dimensions= в вызове, иначе silent dim mismatch."""
    r = client.embeddings.create(model=model, input=texts)
    return [d.embedding for d in r.data]
```

## Moderation

```python
r = client.moderations.create(input=text)
flagged = r.results[0].flagged   # + categories / category_scores
```

## Что здесь НЕ живёт

- **Текст/reasoning по API** (gpt-5.2, o3...) — в Claude Code текст делают Opus/Fable по подписке; для ботов — `config/models.md`; второе мнение gpt-5.6 — Codex CLI по подписке (skill `multi-model-gateway`)
- **Assistants/Realtime/Batch/Computer-use** — узкие API, бери из официальной доки по месту; здесь не дублируем
- **Дефолтные картинки** — skill `image-generation` (NB2)

## Цены (ориентир 2026)

| Что | Цена |
|-----|------|
| gpt-image-2 | ~$0.02-0.19/img |
| Sora 2 / Pro | $0.10 / $0.30 за сек |
| Whisper | $0.006/мин |
| TTS / TTS-HD | $0.015 / $0.030 за 1K chars |
| Embeddings 3-small / 3-large | $0.02 / $0.13 за 1M tokens |
