---
name: openai-dalle
description: "OpenAI media API (OPENAI_API_KEY): gpt-image-2.5 генерация и edit до 16 референсов, прозрачный фон, транскрипция, TTS, embeddings. Дефолт картинок NB2→image-generation; видео у OpenAI больше нет→video-generation."
---

> ⚠️ **NO-KEY GUARD (обязательно):** этот функционал требует ОПЦИОНАЛЬНОГО стороннего API-ключа. Перед вызовом проверь ключ в `.credentials.master.env`. Если ключ отсутствует, пустой или placeholder (`your_*_api_key`) — **НЕ проси пользователя оплатить счёт, включить биллинг или купить API**. Скажи одной строкой: «Эта функция опциональна и требует свой API-ключ (например, бесплатный ключ на aistudio.google.com); из коробки всё остальное работает по подписке Claude» — и предложи альтернативу или продолжай без неё.

# OpenAI Media API (компакт)

> ⚠️ **Имя навыка врёт, и это не косметика.** `dall-e-2` и `dall-e-3` **сняты 12.05.2026**,
> вызов вернёт ошибку. Каталог называется `openai-dalle` по историческим причинам —
> триггерится он на «OpenAI картинки / Sora / Whisper», а не на DALL-E.
> Внутри — актуальный вендорский канон, а не то, что написано на двери.

> **Канон (`config/models.md`) — лестница из трёх ступеней, решение владельца 09.09.2026:**
> 🥉 `gemini-3.1-flash-image-preview` (NB2 Flash) — дёшево и по умолчанию →
> 🥈 `gemini-3-pro-image-preview` (NB Pro) — подороже →
> 🥇 **`gpt-image-2.5-sunburst` — лучшее, и это ЗДЕСЬ.**
>
> Формулировка «OpenAI-образы для случаев, когда нужен именно OpenAI» снята: 2.5
> не альтернатива сбоку, а верхняя ступень. Плюс то, чего у Gemini нет вовсе:
> `input_fidelity` (одна личность на всей пачке), до 16 референсов, прозрачный
> фон, многоходовая правка одной картинки через Responses API.

**See Also:**

- [image-generation](../image-generation/SKILL.md) — общий канон + prompt engineering
- [gemini-3-pro](../gemini-3-pro/SKILL.md) — Google AI suite (text/multimodal/embeddings)
- [video-generation](../video-generation/SKILL.md) — видео-хаб (у OpenAI видео больше нет, остаётся Veo)
- `references/dalle-prompt-templates.md` — prompt-шаблоны (портрет/продукт/арт/инфографика)

## Setup

```python
# Ключ: ~/.claude/.credentials.master.env → OPENAI_API_KEY
from openai import OpenAI
import os, base64
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
```

## Images — gpt-image-2.5 (с 08.09.2026)

| ID | Когда | Снапшот |
|----|-------|---------|
| `gpt-image-2.5-sunburst` | **флагман** — точность инструкций, текст на картинке, сложная сцена | `-2026-09-08` |
| `gpt-image-2.5-flare` | быстрый — те же параметры и цена, ниже задержка | `-2026-09-08` |
| `gpt-image-2-2026-04-21` | прошлое поколение, живо, снятие не объявлено | — |

⛔ Снято или снимается: `dall-e-2`/`dall-e-3` (**12.05.2026**), `gpt-image-1` (23.10.2026),
`gpt-image-1.5` и `gpt-image-1-mini` (01.12.2026). Полные даты — `config/models.md`.

Возвращают **base64, и только его**: параметра `response_format` у 2.5 **нет вовсе** —
если он остался в коде от dall-e-3, вызов упадёт на неизвестном поле, а не проигнорирует его.

```python
def generate_image(prompt: str, out_path: str, size: str = "1024x1024",
                   quality: str = "high", transparent: bool = False):
    """size: любой, ЛИШЬ БЫ обе стороны делились на 16, до 3840x2160 (плюс 'auto').
    quality: low | medium | high | xhigh | max  — два верхних появились в 2.5.
    prompt: до 32 000 знаков.
    Прозрачный фон вышел из беты, но требует png/webp: с jpeg молча даст белый фон."""
    r = client.images.generate(
        model="gpt-image-2.5-sunburst",
        prompt=prompt,
        size=size,
        quality=quality,
        **({"background": "transparent", "output_format": "png"} if transparent else {}),
    )
    with open(out_path, "wb") as f:
        f.write(base64.b64decode(r.data[0].b64_json))
    return out_path
```

### Edit — до 16 референсов (киллер-фича)

```python
def edit_image(prompt: str, input_paths: list[str], out_path: str,
               fidelity: str = "high"):
    """До 16 input-картинок (было 2 у gpt-image-2): сцена + лица + предметы + палитра.
    input_fidelity='high' держит лица и логотипы близко к оригиналу; 'low' даёт
    модели свободу перерисовать. Канон мемов прежний: качать ОРИГИНАЛ и править
    его, а не генерить сцену заново."""
    r = client.images.edit(
        model="gpt-image-2.5-sunburst",
        image=[open(p, "rb") for p in input_paths],   # ≤16
        prompt=prompt,
        input_fidelity=fidelity,
    )
    with open(out_path, "wb") as f:
        f.write(base64.b64decode(r.data[0].b64_json))
    return out_path
```

### Многоходовое редактирование — через Responses API

Отдельная от `images.*` дорожка: картинка становится инструментом внутри диалога,
и правку «а теперь убери лишний стул» не надо переописывать целиком.

```python
r = client.responses.create(
    model="gpt-5.6-sol",
    input="нарисуй кухню в скандинавском стиле",
    tools=[{"type": "image_generation", "model": "gpt-image-2.5-sunburst",
            "action": "auto"}],          # auto | generate | edit
)
# следующий ход правит ту же картинку, а не рисует новую:
r2 = client.responses.create(
    model="gpt-5.6-sol", previous_response_id=r.id,
    input="убери стул слева, остальное не трогай",
    tools=[{"type": "image_generation", "model": "gpt-image-2.5-sunburst",
            "action": "edit"}],
)
```

Прайс gpt-image-2.5: **$5 за млн входных текстовых токенов, $8 за входные картиночные,
$30 за выходные**; кэш-чтение $1,25 / $2. Считается токенами, а не «за картинку», —
поэтому дешёвая мелкая правка стоит дёшево, а `max` на 4K заметно дороже.

## Video — ⛔ у OpenAI видео больше нет

**24.09.2026 закрывается весь продукт**: модели `sora-2`, `sora-2-pro`, все датированные
снапшоты и сам эндпоинт `/v1/videos`. **Замены OpenAI не предложил** — это не смена
идентификатора, а уход с рынка.

Прежний рецепт «Sora, когда на кадре кириллица — Veo её корёжит» **больше не выполним**.
Осталось два пути, оба вне OpenAI:

- **Veo 3.1** (Google) — `python ~/.claude/skills/video-generation/scripts/direct_video.py gen … --engine veo`;
  кириллицу на кадре по-прежнему корёжит, поэтому текст класть **поверх**, оверлеем
  на монтаже, а не просить у модели;
- остальные провайдеры видео-хаба — skill `video-generation`.

Код Sora из этого файла убран намеренно, а не «пока не переписали»: он проживёт
пятнадцать дней и всё это время будет выглядеть рабочим. В `direct_video.py` ветка
оставлена до даты, но с гейтом, который после 24.09 отказывает внятным текстом.

## STT — транскрипция

```python
def transcribe(audio_path: str, language: str = None, fmt: str = "text"):
    """Форматы файла: mp3/mp4/m4a/wav/webm, ≤25MB. fmt: text|json|srt|vtt|verbose_json.
    ⚠️ whisper-1 и gpt-4o-transcribe снимаются 26.02.2027 — канон уже gpt-transcribe."""
    with open(audio_path, "rb") as f:
        return client.audio.transcriptions.create(
            model="gpt-transcribe", file=f, language=language, response_format=fmt)

# Таймстемпы: response_format="verbose_json", timestamp_granularities=["word","segment"]
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

- **Текст/reasoning по API** — в Claude Code текст делают Opus/Fable по подписке; для ботов — `config/models.md`; второе мнение — `gpt-6-astra` через Codex CLI по подписке (skill `multi-model-gateway`). Вся линейка `*-codex` и вся o-серия в API закрыты (23.07 и 11.12.2026)
- **Assistants/Realtime/Batch/Computer-use** — узкие API, бери из официальной доки по месту; здесь не дублируем
- **Дефолтные картинки** — skill `image-generation` (NB2)

## Цены (ориентир 2026)

| Что | Цена |
|-----|------|
| gpt-image-2.5 (оба) | $5 / $8 за млн вх. токенов (текст / картинка), $30 за вых.; кэш $1,25 / $2 |
| gpt-image-2 (prev) | ~$0.02–0.19/img по quality и size |
| ~~Sora 2 / Pro~~ | продукт закрыт 24.09.2026 |
| Транскрипция | $0.006/мин |
| TTS / TTS-HD | $0.015 / $0.030 за 1K chars |
| Embeddings 3-small / 3-large | $0.02 / $0.13 за 1M tokens |
