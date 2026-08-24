---
name: d-id
description: "D-ID API Skill"
---

# D-ID API Skill

## Overview

Expert skill for creating AI avatar videos, talking heads, and interactive agents using D-ID API.

## API Key

```bash
# ~/.claude/.credentials.master.env — впиши САМ КЛЮЧ, не код на Python
DID_API_KEY=ВСТАВЬ_СЮДА_СВОЙ_КЛЮЧ   # https://studio.d-id.com/account-settings
DID_API_URL=https://api.d-id.com
```

> Строка `DID_API_KEY=os.getenv('DID_API_KEY')` ключ НЕ настраивает: это непустое
> значение, любая проверка `if not key` сочтёт ключ заданным, запрос уйдёт с этим
> текстом и вернётся `401` без объяснения. В коде читай ключ через
> `os.getenv('DID_API_KEY')`, а в файле должен лежать сам ключ. Файл не подгружается
> сам: `load_dotenv(Path.home()/'.claude'/'.credentials.master.env')`.

## When to Use D-ID

**Best for:**
- Talking head videos from photos
- AI avatar video generation
- Video localization/dubbing
- Interactive AI agents
- Personalized video content
- Digital presenters

**Advantages:**
- Photo to video in seconds
- 100+ FPS (4x faster than real-time)
- High quality lip-sync
- 100+ languages
- Express avatars (no training)
- Real-time streaming

## Products

| Product | Description |
|---------|-------------|
| Speaking Portrait (Talks) | Photo-based avatar videos |
| Premium Avatar (Clips) | Full-HD from video avatars |
| Express Avatar | Instant avatars from short clips |
| Video Translate | Localization with voice cloning |
| Agents | Interactive real-time avatars |

## Authentication

```python
import requests
import base64
import os

API_KEY = os.getenv('DID_API_KEY')
BASE_URL = "https://api.d-id.com"

headers = {
    "Authorization": f"Basic {API_KEY}",
    "Content-Type": "application/json"
}
```

## Basic Usage

### Create Talking Head Video (Talks)

```python
def create_talk(image_url: str, text: str, voice_id: str = None):
    """
    Create talking head video from image and text.

    Args:
        image_url: URL of source image
        text: Script for the avatar to speak
        voice_id: Voice ID (use list_voices() to get options)
    """
    payload = {
        "source_url": image_url,
        "script": {
            "type": "text",
            "input": text,
            "provider": {
                "type": "microsoft",
                "voice_id": voice_id or "en-US-JennyNeural"
            }
        }
    }

    response = requests.post(
        f"{BASE_URL}/talks",
        headers=headers,
        json=payload
    )

    return response.json()["id"]

# Usage
talk_id = create_talk(
    "https://example.com/photo.jpg",
    "Hello! Welcome to our presentation.",
    "en-US-GuyNeural"
)
```

### Create Talk with Audio

```python
def create_talk_with_audio(image_url: str, audio_url: str):
    """Create talking head with custom audio."""

    payload = {
        "source_url": image_url,
        "script": {
            "type": "audio",
            "audio_url": audio_url
        }
    }

    response = requests.post(
        f"{BASE_URL}/talks",
        headers=headers,
        json=payload
    )

    return response.json()["id"]
```

### Check Video Status

```python
def get_talk_status(talk_id: str):
    """Check status and get result URL."""

    response = requests.get(
        f"{BASE_URL}/talks/{talk_id}",
        headers=headers
    )

    data = response.json()

    return {
        "status": data["status"],  # created, started, done, error
        "result_url": data.get("result_url"),
        "error": data.get("error")
    }
```

### Wait for Completion

```python
import time

def wait_for_video(talk_id: str, timeout: int = 300):
    """Wait for video to complete and return URL."""

    start = time.time()

    while time.time() - start < timeout:
        status = get_talk_status(talk_id)

        if status["status"] == "done":
            return status["result_url"]
        elif status["status"] == "error":
            raise Exception(f"Video failed: {status['error']}")

        time.sleep(5)

    raise TimeoutError("Video generation timed out")
```

### Full Workflow Example

```python
def generate_avatar_video(image_url: str, text: str, output_path: str):
    """Complete workflow: create, wait, download."""

    # Create talk
    talk_id = create_talk(image_url, text)
    print(f"Created talk: {talk_id}")

    # Wait for completion
    video_url = wait_for_video(talk_id)
    print(f"Video ready: {video_url}")

    # Download video
    video_response = requests.get(video_url)
    with open(output_path, "wb") as f:
        f.write(video_response.content)

    return output_path
```

### List Available Voices

```python
def list_voices():
    """Get available TTS voices."""

    response = requests.get(
        f"{BASE_URL}/tts/voices",
        headers=headers
    )

    voices = response.json()

    for voice in voices:
        print(f"{voice['id']}: {voice['name']} ({voice['language']})")

    return voices
```

### Create Premium Clip

```python
def create_clip(presenter_id: str, text: str, voice_id: str):
    """
    Create premium HD video with video-based avatar.

    Requires HQ Presenter (avatar trained on video).
    """
    payload = {
        "presenter_id": presenter_id,
        "script": {
            "type": "text",
            "input": text,
            "provider": {
                "type": "microsoft",
                "voice_id": voice_id
            }
        }
    }

    response = requests.post(
        f"{BASE_URL}/clips",
        headers=headers,
        json=payload
    )

    return response.json()["id"]
```

### Create Express Avatar

```python
def create_express_avatar(video_url: str, name: str):
    """
    Create instant avatar from short video clip.

    No training required - works immediately.
    """
    payload = {
        "name": name,
        "source_url": video_url
    }

    response = requests.post(
        f"{BASE_URL}/express-avatars",
        headers=headers,
        json=payload
    )

    return response.json()["id"]
```

### Video Translation

```python
def translate_video(video_url: str, target_language: str):
    """
    Translate video to another language.

    Includes voice cloning for natural dubbing.
    """
    payload = {
        "source_url": video_url,
        "target_language": target_language  # e.g., "es", "fr", "de"
    }

    response = requests.post(
        f"{BASE_URL}/video-translate",
        headers=headers,
        json=payload
    )

    return response.json()["id"]
```

### Real-time Streaming (Agents)

```python
def create_stream_session(source_url: str):
    """Create real-time streaming session."""

    payload = {
        "source_url": source_url
    }

    response = requests.post(
        f"{BASE_URL}/streams",
        headers=headers,
        json=payload
    )

    return response.json()

def send_stream_text(session_id: str, text: str):
    """Send text to active stream."""

    payload = {
        "script": {
            "type": "text",
            "input": text
        }
    }

    response = requests.post(
        f"{BASE_URL}/streams/{session_id}",
        headers=headers,
        json=payload
    )

    return response.json()

def close_stream(session_id: str):
    """Close streaming session."""

    response = requests.delete(
        f"{BASE_URL}/streams/{session_id}",
        headers=headers
    )

    return response.status_code == 200
```

### Check Credits

```python
def get_credits():
    """Get remaining credits."""

    response = requests.get(
        f"{BASE_URL}/credits",
        headers=headers
    )

    return response.json()
```

### Upload Image

```python
def upload_image(image_path: str):
    """Upload image to D-ID for use in talks."""

    with open(image_path, "rb") as f:
        files = {"image": f}
        response = requests.post(
            f"{BASE_URL}/images",
            headers={"Authorization": f"Basic {API_KEY}"},
            files=files
        )

    return response.json()["url"]
```

## Voice Providers

| Provider | Description |
|----------|-------------|
| microsoft | Azure TTS (100+ voices) |
| amazon | Amazon Polly |
| elevenlabs | ElevenLabs voices |
| custom | Your uploaded audio |

## Script Types

| Type | Description |
|------|-------------|
| text | Text-to-speech |
| audio | Custom audio file |
| ssml | SSML markup for control |

## API Pricing

| Product | Price |
|---------|-------|
| Talks | ~$0.03/second |
| Clips | ~$0.05/second |
| Streams | Per-minute pricing |
| Video Translate | Per-minute pricing |

## Quick Reference

| Task | Code |
|------|------|
| Create talk | `POST /talks` |
| Get talk status | `GET /talks/{id}` |
| Create clip | `POST /clips` |
| List voices | `GET /tts/voices` |
| Upload image | `POST /images` |
| Create stream | `POST /streams` |
| Translate video | `POST /video-translate` |

## Tips

1. **Image quality** - используй фронтальные фото с четким лицом
2. **Text length** - разбивай длинные скрипты на части
3. **Voice matching** - выбирай голос соответствующий контенту
4. **Express avatars** - быстрее чем обучение полного аватара
5. **Streaming** - для интерактивных приложений
6. **Batch processing** - создавай несколько talks параллельно
7. **Credits** - проверяй баланс перед большими задачами
