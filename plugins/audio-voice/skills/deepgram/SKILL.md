---
name: deepgram
description: "Deepgram speech-to-text: transcribe audio/video, SRT subtitles, speaker diarization. Triggers: «transcribe», «subtitles from audio»."
---

# Deepgram API Skill

## Overview

Expert skill for audio transcription and speech-to-text using Deepgram - fast, accurate, real-time capable.

## API Key

```bash
# API ключи: ~/.claude/.credentials.master.env
# Переменная: DEEPGRAM_API_KEY
DEEPGRAM_API_KEY=os.getenv('DEEPGRAM_API_KEY')
```

## When to Use Deepgram

**Best for:**
- Audio/video transcription
- Real-time speech-to-text
- Meeting transcription
- Podcast processing
- Voice commands
- Call center analytics

**Advantages:**
- Very fast transcription
- High accuracy
- Real-time streaming
- Speaker diarization
- Multiple languages
- Punctuation & formatting

## Dependencies

```bash
pip install deepgram-sdk
```

## ⚠️ SDK 6.x сломал старый API — надёжный путь REST (читать первым)

В **deepgram-sdk 6.0.1+** УБРАЛИ `PrerecordedOptions`/`FileSource` (`from deepgram import PrerecordedOptions` → ImportError). Примеры ниже по тексту — для SDK ≤3.x. Чтобы не зависеть от версии SDK, для prerecorded-транскрипции с диаризацией используй **сырой REST** (работает всегда):

```python
import requests, os
key = os.getenv('DEEPGRAM_API_KEY')
# сначала ужать: ffmpeg -i in.mp4 -vn -ac 1 -ar 16000 -b:a 64k meeting.mp3  (3ч ≈ 86 МБ)
audio = open('meeting.mp3', 'rb').read()
r = requests.post('https://api.deepgram.com/v1/listen',
    params={'model': 'nova-3', 'language': 'ru', 'diarize': 'true', 'punctuate': 'true',
            'smart_format': 'true', 'utterances': 'true', 'paragraphs': 'true'},
    headers={'Authorization': f'Token {key}', 'Content-Type': 'audio/mpeg'},
    data=audio, timeout=1800)
utts = r.json()['results']['utterances']   # [{speaker, start, end, transcript}, ...]
```

**Разбивка записи по докладчикам/докладам:** группируй `utterances` по полю `speaker`; граница доклада = где доминирующий спикер меняется на длинном отрезке (модератор объявляет следующего). `start`/`end` (секунды) → таймкоды для нарезки видео ffmpeg-ом. Модель **`nova-3`** (не `nova-2`) заметно точнее на русском. Этого абзаца хватает, чтобы собрать кейс «запись → пакет по спикерам» самому: диаризация здесь, нарезка — ffmpeg по таймкодам.

## Basic Usage

### Setup Client

```python
from deepgram import DeepgramClient, PrerecordedOptions, LiveOptions
import os

client = DeepgramClient(os.getenv('DEEPGRAM_API_KEY'))
```

### Transcribe Audio File

```python
def transcribe_file(audio_path: str, language: str = "en"):
    """
    Transcribe audio file.

    Supported formats: mp3, wav, flac, m4a, ogg, webm
    """
    with open(audio_path, "rb") as audio:
        source = {"buffer": audio.read()}

    options = PrerecordedOptions(
        model="nova-2",  # Best model
        language=language,
        smart_format=True,  # Punctuation, formatting
        punctuate=True,
        diarize=True,  # Speaker separation
        paragraphs=True,
        utterances=True
    )

    response = client.listen.prerecorded.v("1").transcribe_file(source, options)

    return response.results.channels[0].alternatives[0].transcript

# Simple usage
transcript = transcribe_file("meeting.mp3")
print(transcript)
```

### Transcribe from URL

```python
def transcribe_url(audio_url: str, language: str = "en"):
    """Transcribe audio from URL."""

    source = {"url": audio_url}

    options = PrerecordedOptions(
        model="nova-2",
        language=language,
        smart_format=True,
        punctuate=True
    )

    response = client.listen.prerecorded.v("1").transcribe_url(source, options)

    return response.results.channels[0].alternatives[0].transcript
```

### Get Detailed Results

```python
def transcribe_detailed(audio_path: str):
    """Get detailed transcription with timestamps and speakers."""

    with open(audio_path, "rb") as audio:
        source = {"buffer": audio.read()}

    options = PrerecordedOptions(
        model="nova-2",
        smart_format=True,
        diarize=True,
        utterances=True
    )

    response = client.listen.prerecorded.v("1").transcribe_file(source, options)

    results = []
    for utterance in response.results.utterances:
        results.append({
            "speaker": utterance.speaker,
            "start": utterance.start,
            "end": utterance.end,
            "text": utterance.transcript,
            "confidence": utterance.confidence
        })

    return {
        "transcript": response.results.channels[0].alternatives[0].transcript,
        "utterances": results,
        "duration": response.metadata.duration
    }
```

### Real-time Streaming

```python
import asyncio

async def transcribe_stream(audio_stream):
    """Real-time streaming transcription."""

    options = LiveOptions(
        model="nova-2",
        language="en",
        smart_format=True,
        interim_results=True
    )

    connection = client.listen.live.v("1").options(options)

    async def on_message(result):
        transcript = result.channel.alternatives[0].transcript
        if transcript:
            print(f"Transcript: {transcript}")

    connection.on("transcript", on_message)

    await connection.start()

    # Send audio chunks
    for chunk in audio_stream:
        await connection.send(chunk)

    await connection.finish()
```

### Transcribe Video

```python
def transcribe_video(video_path: str):
    """
    Extract and transcribe audio from video.

    Supports: mp4, mov, avi, mkv, webm
    """
    # Deepgram can process video files directly
    with open(video_path, "rb") as video:
        source = {"buffer": video.read()}

    options = PrerecordedOptions(
        model="nova-2",
        smart_format=True,
        diarize=True,
        paragraphs=True
    )

    response = client.listen.prerecorded.v("1").transcribe_file(source, options)

    return response.results.channels[0].alternatives[0].transcript
```

### Meeting Transcription

```python
def transcribe_meeting(audio_path: str):
    """
    Transcribe meeting with speaker labels.

    Returns formatted transcript with speaker changes.
    """
    result = transcribe_detailed(audio_path)

    # Format as meeting transcript
    transcript_lines = []
    current_speaker = None

    for utterance in result["utterances"]:
        speaker = f"Speaker {utterance['speaker']}"
        if speaker != current_speaker:
            current_speaker = speaker
            transcript_lines.append(f"\n**{speaker}:**")
        transcript_lines.append(utterance["text"])

    return {
        "formatted": "\n".join(transcript_lines),
        "duration_minutes": result["duration"] / 60,
        "speaker_count": len(set(u["speaker"] for u in result["utterances"]))
    }
```

### Multi-language Support

```python
SUPPORTED_LANGUAGES = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "nl": "Dutch",
    "ja": "Japanese",
    "ko": "Korean",
    "zh": "Chinese",
    "ru": "Russian",
    "uk": "Ukrainian",
    "pl": "Polish",
    "tr": "Turkish",
    "ar": "Arabic",
    "hi": "Hindi"
}

def transcribe_multilingual(audio_path: str):
    """Auto-detect language and transcribe."""

    with open(audio_path, "rb") as audio:
        source = {"buffer": audio.read()}

    options = PrerecordedOptions(
        model="nova-2",
        detect_language=True,  # Auto-detect
        smart_format=True
    )

    response = client.listen.prerecorded.v("1").transcribe_file(source, options)

    return {
        "transcript": response.results.channels[0].alternatives[0].transcript,
        "language": response.results.channels[0].detected_language
    }
```

### Generate Subtitles (SRT/VTT)

```python
def generate_subtitles(audio_path: str, format: str = "srt"):
    """Generate subtitle file from audio."""

    result = transcribe_detailed(audio_path)

    if format == "srt":
        return generate_srt(result["utterances"])
    elif format == "vtt":
        return generate_vtt(result["utterances"])

def generate_srt(utterances: list) -> str:
    """Generate SRT format subtitles."""

    srt_lines = []
    for i, utt in enumerate(utterances, 1):
        start = format_timestamp_srt(utt["start"])
        end = format_timestamp_srt(utt["end"])
        srt_lines.append(f"{i}")
        srt_lines.append(f"{start} --> {end}")
        srt_lines.append(utt["text"])
        srt_lines.append("")

    return "\n".join(srt_lines)

def format_timestamp_srt(seconds: float) -> str:
    """Format seconds to SRT timestamp."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
```

### Summarize Audio

```python
def transcribe_and_summarize(audio_path: str):
    """Transcribe audio and generate summary."""

    # First transcribe
    transcript = transcribe_file(audio_path)

    # Then summarize with Gemini/GPT
    from openai import OpenAI
    client = OpenAI()

    response = client.chat.completions.create(
        model="gpt-5.1",
        messages=[
            {"role": "system", "content": "Summarize this transcript concisely."},
            {"role": "user", "content": transcript}
        ]
    )

    return {
        "transcript": transcript,
        "summary": response.choices[0].message.content
    }
```

## Models

| Model | Description | Best For |
|-------|-------------|----------|
| nova-2 | Latest, most accurate | General use |
| nova | Fast and accurate | Real-time |
| enhanced | Better accuracy | Important content |
| base | Fastest | High volume |
| whisper | OpenAI Whisper | Comparison |

## API Pricing

| Model | Price |
|-------|-------|
| nova-2 | $0.0043/min |
| nova | $0.0036/min |
| enhanced | $0.0145/min |
| base | $0.0125/min |

## Quick Reference

| Task | Code |
|------|------|
| Transcribe file | `transcribe_file(path)` |
| Transcribe URL | `transcribe_url(url)` |
| With timestamps | `transcribe_detailed(path)` |
| Real-time | Use LiveOptions + streaming |
| Auto language | `detect_language=True` |
| Speaker labels | `diarize=True` |
| Subtitles | `generate_subtitles(path, "srt")` |

## Tips

1. **nova-2** - лучшее качество для большинства задач
2. **diarize=True** - разделяет спикеров автоматически
3. **smart_format=True** - добавляет пунктуацию и форматирование
4. **Streaming** - для real-time приложений
5. **detect_language** - автоопределение языка
6. Поддерживает видео файлы напрямую
