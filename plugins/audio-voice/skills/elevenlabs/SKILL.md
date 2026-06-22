---
name: elevenlabs
description: "ElevenLabs text-to-speech, voice cloning, sound effects generation. Use when asked to voice text, clone voice, generate audio, or create sound effects."
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

## Voices

Use a prebuilt ElevenLabs voice, or set `ELEVENLABS_VOICE_ID` to your own (cloned) voice ID. List available voices via the `/v2/voices` endpoint.

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
