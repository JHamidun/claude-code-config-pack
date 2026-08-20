---
name: did
description: "D-ID: говорящая голова из фото + текст или аудио. Триггеры: «озвучь фото», «видео-презентер из фотографии». НЕ свой аватар → heygen."
---

# D-ID API Skill

## Overview

AI avatar video generation. Create talking head videos from a photo and text/audio input.

## API Key

```python
import os
DID_API_KEY = os.getenv('DID_API_KEY')
# Key from ~/.claude/.credentials.master.env
```

## Base URL

`https://api.d-id.com`

## Create Talking Head Video

```python
import requests, os

headers = {
    "Authorization": f"Basic {os.getenv('DID_API_KEY')}",
    "Content-Type": "application/json"
}

# From text (TTS)
response = requests.post(
    "https://api.d-id.com/talks",
    headers=headers,
    json={
        "source_url": "https://example.com/photo.jpg",
        "script": {
            "type": "text",
            "input": "Hello, this is a demo.",
            "provider": {
                "type": "microsoft",
                "voice_id": "en-US-JennyNeural"
            }
        },
        "config": {"stitch": True}
    }
)
talk_id = response.json()["id"]

# Check status
status = requests.get(
    f"https://api.d-id.com/talks/{talk_id}",
    headers=headers
).json()
video_url = status.get("result_url")
```

## From Audio File

```python
with open("audio.mp3", "rb") as f:
    upload = requests.post(
        "https://api.d-id.com/audios",
        headers={"Authorization": f"Basic {os.getenv('DID_API_KEY')}"},
        files={"audio": f}
    )
audio_url = upload.json()["url"]

response = requests.post(
    "https://api.d-id.com/talks",
    headers=headers,
    json={
        "source_url": "photo.jpg",
        "script": {"type": "audio", "audio_url": audio_url}
    }
)
```

## Clips (Built-in Presenters)

```python
response = requests.post(
    "https://api.d-id.com/clips",
    headers=headers,
    json={
        "presenter_id": "amy-jcwCkr1grs",
        "script": {"type": "text", "input": "Welcome!"},
        "background": {"color": "#FFFFFF"}
    }
)
```

## Tips

1. Use high-quality front-facing photos
2. `stitch: true` improves quality
3. Videos ready in 30-60 seconds
4. Download result_url before expiry
