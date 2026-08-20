---
name: elevenlabs
description: "ElevenLabs: TTS, клонирование голоса, звуковые эффекты; свой клонированный голос. Триггеры: «озвучь», «наговори текст». НЕ расшифровка речи→deepgram; говорящее фото→did."
---

# ElevenLabs API Skill

## Overview

Expert skill for text-to-speech, voice cloning, sound effects, and audio AI using ElevenLabs - the most advanced voice AI platform.

## API Key

```bash
# API ключи: ~/.claude/.credentials.master.env
# Переменная: ELEVENLABS_API_KEY
ELEVENLABS_API_KEY=os.getenv('ELEVENLABS_API_KEY')
```

## Свой голос (клон)

Идентификатор своего голоса держится в окружении, а не в тексте навыка: он привязан
к конкретному аккаунту и в чужой установке всё равно не сработает.

```bash
ELEVENLABS_VOICE_ID_RU=<идентификатор своего клона>   # в ~/.claude/.credentials.master.env
```

Список доступных голосов аккаунта — `GET /v1/voices`; клонированные помечены
категорией `cloned`. Как подготовить материал для клонирования — `scripts/voice_dataset.py`.

> **Локальная альтернатива (экономия кредитов):** для массовой/черновой RU-озвучки, длинных аудиокниг, dictation и офлайн — см. `references/local-voicebox-eval.md` (Voicebox / Chatterbox / Qwen3-TTS на видеокарте с 16 ГБ памяти, без обращений к API). ElevenLabs остаётся каноном для флагманской озвучки, звуковых эффектов и музыки.

## When to Use ElevenLabs

**Best for:**
- Text-to-speech (TTS) generation
- Voice cloning (instant & professional)
- Sound effects generation
- Speech-to-speech voice conversion
- Dubbing & localization
- Real-time voice agents

**Advantages:**
- Most natural-sounding voices
- 70+ languages support
- Ultra-low latency (75ms with Flash)
- Voice cloning from 1 minute of audio
- Emotional expression control

## Dependencies

```bash
pip install elevenlabs
```

## Models

| Model | ID | Latency | Best For |
|-------|-----|---------|----------|
| Eleven v3 | eleven_v3 | Higher | Highest quality, emotions |
| Multilingual v2 | eleven_multilingual_v2 | Medium | 29 languages, expressive |
| Flash v2.5 | eleven_flash_v2_5 | ~75ms | Real-time apps |
| Turbo v2.5 | eleven_turbo_v2_5 | ~250ms | Balance quality/speed |

## Basic Usage

### Setup Client

```python
from elevenlabs import ElevenLabs
import os

client = ElevenLabs(api_key=os.getenv('ELEVENLABS_API_KEY'))
```

### Text-to-Speech

```python
def text_to_speech(text: str, voice_id: str = "JBFqnCBsd6RMkjVDRZzb",
                   model: str = "eleven_multilingual_v2"):
    """Generate speech from text."""

    audio = client.text_to_speech.convert(
        text=text,
        voice_id=voice_id,
        model_id=model,
        output_format="mp3_44100_128",
        voice_settings={
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0,
            "use_speaker_boost": True
        }
    )

    # Save to file
    with open("output.mp3", "wb") as f:
        for chunk in audio:
            f.write(chunk)

    return "output.mp3"
```

### Streaming TTS (Real-time)

```python
def stream_speech(text: str, voice_id: str):
    """Stream speech for real-time playback."""

    audio_stream = client.text_to_speech.stream(
        text=text,
        voice_id=voice_id,
        model_id="eleven_flash_v2_5",  # Best for streaming
        output_format="mp3_44100_128"
    )

    # Play directly
    from elevenlabs.play import play
    play(audio_stream)
```

## Music Generation (`client.music.compose`)

ENDPOINT: `client.music.compose(prompt, music_length_ms, force_instrumental, model_id)` — добавлено 2026-05-31, params исправлены 2026-06-06 (production-used).

### Quickstart

```python
from elevenlabs import ElevenLabs
import os

client = ElevenLabs(api_key=os.environ['ELEVENLABS_API_KEY'])

result = client.music.compose(
    prompt='Tense underscore, sub-bass pulse, sparse percussion, no vocals',
    music_length_ms=30000,     # ← НЕ length_ms! (см. ниже)
    force_instrumental=True,    # инструментал без вокала
    model_id='music_v1',
)

with open('bgm.mp3', 'wb') as f:
    for chunk in result:
        f.write(chunk)
```

### Hard limits + param names

- **CRITICAL — имя параметра длины = `music_length_ms`, НЕ `length_ms`.** `length_ms=...` → `TypeError: MusicClient.compose() got an unexpected keyword argument 'length_ms'` (проверено в проде, июнь 2026).
- Инструментал — через `force_instrumental=True` (надёжнее, чем «no vocals» в тексте промпта).
- `model_id='music_v1'`.
- **~30 seconds на одну генерацию** (длиннее режь на сегменты с narrative handoff, см. video-generation `skills/video-generation/references/audio.md`).
- Output: MP3 stream. Generation time: 10-30 sec wall-clock.

### CRITICAL: Named-artist policy

Любой prompt со ссылкой на named artist → `content_policy_violation`. Это **всегда** падает:

- `'in the style of [Named Artist]'`
- `'[Artist]-style vocal'`
- `'sounds like [Track] by [Artist]'`
- `'[Composer] cinematic'`

**Workaround = ТОЛЬКО descriptor substitution.** Никаких имён.

| Запрещено | Заменить на дескрипторы |
|---|---|
| `Hans Zimmer cinematic` | `Massive orchestral underscore, sub-bass pulse, brass swells, heroic` |
| `in the style of Vangelis` | `Synthesized 80s sci-fi, analog warm pads, slow arpeggios` |
| `Lo-fi hip-hop like Nujabes` | `Jazzy lo-fi, soft vinyl crackle, lazy drum samples, mellow piano` |
| `Sounds like Lord of the Rings score` | `Celtic strings, choir swells, epic fantasy underscore, heroic horn motif` |
| `John Williams adventure` | `Sweeping orchestral adventure, brass fanfare, rolling strings` |

### Длинные треки (>30s)

Генерируй 2 сегмента по 30s с narrative handoff в prompt'е, концатенируй **БЕЗ crossfade** (jarring на музыке):

```python
seg1 = client.music.compose(prompt='Dark mystery cinematic underscore, low strings, builds slowly', music_length_ms=30000, force_instrumental=True, model_id='music_v1')
seg2 = client.music.compose(prompt='Continues from dark mystery, transitions into battle, percussion enters, brass swells', music_length_ms=30000, force_instrumental=True, model_id='music_v1')
# ffmpeg -i seg1.mp3 -i seg2.mp3 -filter_complex "[0:a][1:a]concat=n=2:v=0:a=1[out]" -map "[out]" full.mp3
```

### Когда что использовать

| Задача | Решение |
|---|---|
| Quick BGM под шортс | **ElevenLabs Music** — быстрее, не нужен service account |
| Commercial-safe license для коммерческого ролика | **Lyria 2** (Vertex AI, см. `video-generation/references/audio.md`) |
| Кинематографический score для книжного трейлера | **Lyria 2** 2×30s + acrossfade |

## Production voice IDs

### Свой клонированный голос — рабочие настройки

```python
audio = client.text_to_speech.convert(
    voice_id=os.getenv('ELEVENLABS_VOICE_ID_RU'),   # свой голос — из окружения
    text='Сегодня разберём, как…',
    model_id='eleven_multilingual_v2',
    voice_settings={
        'stability': 0.55,
        'similarity_boost': 0.80,
        'style': 0.15,
        'use_speaker_boost': True,
    },
)
```

**Отклонения от этих параметров → voice cracks, потеря тембра, over-acting.** Не править без причины.

### EN voices on RU — эмпирически лучше native RU

Английские voice IDs через `eleven_multilingual_v2` на русском тексте дают тембр заметно лучше native RU voices. Подтверждено на коротких вертикальных роликах.

| Voice | voice_id | Use |
|---|---|---|
| Matthew Villain | `bwCXcoVxWNYMlC6Esa8u` | mystical / character / book trailer narrator (RU и EN) |
| Brian | (см. ElevenLabs catalog) | confident male, корпоративные шортсы |

### Voice settings ranges (общие)

| Параметр | Range | Эффект |
|---|---|---|
| `stability` | 0.20–0.35 | expressive, актёрская подача |
| `stability` | >0.60 | robotic, монотонный |
| `similarity_boost` | 0.80–0.90 | character lock, держит тембр |
| `style` | 0.2 | intimate, разговорный |
| `style` | 0.8 | dramatic, театральный |
| `use_speaker_boost` | True | всегда True для production |

Тестируй 5-10 voice IDs с identical text прежде чем commit к final.

### Instant Voice Cloning

```python
from io import BytesIO

def clone_voice(name: str, audio_files: list):
    """
    Clone voice from audio samples.

    Requirements:
        - Minimum 1 minute of clean audio
        - Best results with 2-3 minutes
    """
    files = [BytesIO(open(f, "rb").read()) for f in audio_files]

    voice = client.voices.ivc.create(
        name=name,
        files=files,
        remove_background_noise=True
    )

    return voice.voice_id
```

### Sound Effects Generation

```python
def generate_sound_effect(description: str, duration: int = 10):
    """
    Generate sound effect from text description.

    Max duration: 22 seconds
    """
    audio = client.text_to_sound_effects.convert(
        text=description,
        duration_seconds=duration,
        prompt_influence=0.5
    )

    with open("effect.mp3", "wb") as f:
        for chunk in audio:
            f.write(chunk)

    return "effect.mp3"

# Examples:
# "Cinematic braam for movie trailer"
# "Forest ambience with birds chirping"
# "Spaceship engine humming"
```

### Speech-to-Speech (Voice Changer)

```python
def change_voice(audio_path: str, target_voice_id: str):
    """Convert voice in audio to target voice."""

    with open(audio_path, "rb") as audio_file:
        result = client.speech_to_speech.convert(
            voice_id=target_voice_id,
            audio=audio_file,
            model_id="eleven_multilingual_sts_v2",
            remove_background_noise=True
        )

    with open("voice_changed.mp3", "wb") as f:
        for chunk in result:
            f.write(chunk)

    return "voice_changed.mp3"
```

### List Available Voices

```python
def get_voices():
    """Get all available voices."""

    voices = client.voices.search(page_size=100)

    for voice in voices.voices:
        print(f"{voice.name}: {voice.voice_id}")

    return voices.voices
```

## Voice Settings

| Parameter | Range | Description |
|-----------|-------|-------------|
| stability | 0-1 | Voice consistency (0.5 recommended) |
| similarity_boost | 0-1 | Voice matching (0.75 recommended) |
| style | 0-1 | Style exaggeration (0 recommended) |
| use_speaker_boost | bool | Enhance voice similarity |

## Output Formats

- `mp3_22050_32` - Low quality
- `mp3_44100_128` - Standard (default)
- `mp3_44100_192` - High quality (Creator+)
- `pcm_16000`, `pcm_44100` - Raw PCM
- `opus_48000_64` - Opus codec

## API Pricing

| Plan | Cost | Credits |
|------|------|---------|
| Free | $0/mo | 10,000 chars |
| Starter | $5/mo | 30,000 chars |
| Creator | $22/mo | 100,000 chars |
| Pro | $99/mo | 500,000 chars |

## Quick Reference

| Task | Code |
|------|------|
| TTS | `client.text_to_speech.convert(text, voice_id)` |
| Stream | `client.text_to_speech.stream(text, voice_id)` |
| Clone voice | `client.voices.ivc.create(name, files)` |
| Sound effects | `client.text_to_sound_effects.convert(text)` |
| Voice change | `client.speech_to_speech.convert(voice_id, audio)` |

## Tips

1. **eleven_flash_v2_5** - лучший для real-time (75ms latency)
2. **eleven_multilingual_v2** - лучшее качество для записей
3. Для voice cloning нужно минимум 1 минута чистого аудио
4. `stability=0.5` - оптимальный баланс эмоций
5. Sound effects до 22 секунд максимум
6. Поддержка 70+ языков
