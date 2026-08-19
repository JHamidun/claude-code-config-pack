---
description: "Транскрибация аудио и видео через Deepgram: файл или URL, SRT-субтитры, диаризация. Триггеры: «транскрибируй», «расшифруй запись», «субтитры из аудио»."
argument-hint: "<file_path|url> [--srt] [--speakers] [--lang ru]"
---

# Transcribe

/transcribe - Audio/video transcription via Deepgram

## Usage
```
/transcribe <file_path>              - Transcribe audio/video file
/transcribe <url>                    - Transcribe from URL
/transcribe <file_path> --srt        - Generate SRT subtitles
/transcribe <file_path> --speakers   - With speaker diarization
/transcribe <file_path> --lang ru    - Specify language
```

## Instructions for Claude

Uses Deepgram API (nova-2 model). Full reference: `~/.claude/skills/deepgram/SKILL.md`

### Quick transcribe

```python
from deepgram import DeepgramClient, PrerecordedOptions
import os
from dotenv import load_dotenv

load_dotenv('${HOME}/.claude/.credentials.master.env')
client = DeepgramClient(os.getenv('DEEPGRAM_API_KEY'))

# From file
with open("audio.mp3", "rb") as f:
    source = {"buffer": f.read()}

options = PrerecordedOptions(
    model="nova-2",
    language="ru",         # or "en", auto-detect with detect_language=True
    smart_format=True,
    punctuate=True,
    diarize=True,          # speaker separation
    paragraphs=True,
    utterances=True
)

response = client.listen.prerecorded.v("1").transcribe_file(source, options)
print(response.results.channels[0].alternatives[0].transcript)
```

### From URL

```python
source = {"url": "https://example.com/audio.mp3"}
response = client.listen.prerecorded.v("1").transcribe_url(source, options)
```

### With speaker labels

```python
for utterance in response.results.utterances:
    print(f"Speaker {utterance.speaker}: {utterance.transcript}")
```

### Generate SRT subtitles

```python
srt_lines = []
for i, utt in enumerate(response.results.utterances, 1):
    start = format_srt_time(utt.start)
    end = format_srt_time(utt.end)
    srt_lines.append(f"{i}\n{start} --> {end}\n{utt.transcript}\n")

def format_srt_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
```

## Supported formats

Audio: mp3, wav, flac, m4a, ogg, webm
Video: mp4, mov, avi, mkv, webm (extracts audio automatically)

## Languages

Auto-detect or specify: en, ru, uk, de, fr, es, it, pt, nl, ja, ko, zh, ar, hi, pl, tr

## Important

- DEEPGRAM_API_KEY from `~/.claude/.credentials.master.env`
- Model `nova-2` is best quality for most tasks
- Cost: ~$0.0043/min
- `smart_format=True` adds punctuation automatically
