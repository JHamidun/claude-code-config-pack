---
name: gemini-3-pro
description: "Gemini API Skill (Full Suite)"
---

# Gemini API Skill (Full Suite)

> **See Also:**
> - **[image-generation](image-generation.md)** - General prompt engineering for all image generators
> - **[nano-banana-pro](nano-banana-pro.md)** - Photorealistic portrait templates (Gemini-specific)
> - **[openai-dalle](openai-dalle.md)** - OpenAI suite: DALL-E 3, Sora 2, Whisper, GPT-4o

## Overview

Expert skill for Google AI Suite - полный набор возможностей:
- **Text**: Gemini 2.0 Flash/Pro (2M контекст!)
- **Images**: Imagen 3 Ultra (генерация)
- **Video**: Veo 2 (генерация видео)
- **Audio TTS**: Text-to-Speech
- **Audio STT**: Speech-to-Text (Live API)
- **Embeddings**: text-embedding-004
- **Tools**: Code execution, Google Search, Function calling

## API Key

```bash
# API ключи: ~/.claude/.credentials.master.env
# Переменные: GOOGLE_API_KEY, GEMINI_API_KEY
GOOGLE_API_KEY=os.getenv('GOOGLE_API_KEY')
GEMINI_API_KEY=os.getenv('GEMINI_API_KEY')
```

## Available Models

| Model | Context | Best For |
|-------|---------|----------|
| **gemini-2.0-flash** | 1M | Fast responses, real-time |
| **gemini-2.0-flash-thinking** | 1M | Complex reasoning |
| **gemini-2.0-pro** (preview) | 2M | Highest quality |
| **gemini-1.5-pro** | 2M | Long documents |
| **gemini-1.5-flash** | 1M | Cost-effective |
| **gemini-1.5-flash-8b** | 1M | Ultra-fast, cheap |
| **imagen-3-ultra** | - | Image generation |
| **veo-2** | - | Video generation |

## When to Use Gemini

**Best for:**
- Multimodal tasks (text + images + video + audio)
- Massive context (up to 2M tokens!)
- Native image generation (Imagen 3 Ultra)
- Video generation (Veo 2)
- Long document processing
- Real-time streaming (Live API)
- Code execution in sandbox

**Advantages:**
- Largest context window (2M!)
- Native multimodal - all formats
- Built-in Imagen 3 & Veo 2
- Excellent reasoning (thinking models)
- Google Search grounding
- Live API for real-time audio/video

## Dependencies

```bash
pip install google-generativeai
```

## Basic Usage

### Setup Client

```python
import google.generativeai as genai
import os

genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Available models
MODELS = {
    "gemini-3-pro": "Flagship model, best quality",
    "gemini-3-pro-vision": "Optimized for vision tasks",
    "gemini-3-flash": "Fast, efficient, cheaper",
    "gemini-2.0-flash-exp": "Experimental features"
}
```

### Text Generation

```python
def gemini_chat(prompt: str, system_prompt: str = None,
                model_name: str = "gemini-3-pro"):
    """
    Chat with Gemini 3 Pro.

    Models:
        - gemini-3-pro: Best quality (2M context)
        - gemini-3-flash: Fast & cheap
        - gemini-3-pro-vision: Vision optimized
    """
    model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=system_prompt
    )

    response = model.generate_content(prompt)
    return response.text

# Simple usage
result = gemini_chat("Explain quantum computing")
```

### Image Understanding

```python
import PIL.Image

def analyze_image(image_path: str, prompt: str):
    """Analyze image with Gemini 3 Pro Vision."""

    model = genai.GenerativeModel("gemini-3-pro-vision")
    image = PIL.Image.open(image_path)

    response = model.generate_content([prompt, image])
    return response.text

def analyze_multiple_images(image_paths: list, prompt: str):
    """Analyze multiple images at once."""

    model = genai.GenerativeModel("gemini-3-pro-vision")
    images = [PIL.Image.open(p) for p in image_paths]

    response = model.generate_content([prompt] + images)
    return response.text
```

### Native Image Generation (Imagen 3 / Nano Banana Pro)

```python
def generate_image(prompt: str, output_path: str,
                   aspect_ratio: str = "1:1"):
    """
    Generate image with Gemini's native Imagen 3.

    aspect_ratio: "1:1", "16:9", "9:16", "4:3", "3:4"
    """
    model = genai.GenerativeModel("gemini-3-pro")

    response = model.generate_content(
        f"Generate an image: {prompt}",
        generation_config={
            "response_mime_type": "image/png",
            "image_generation_config": {
                "aspect_ratio": aspect_ratio,
                "quality": "high"
            }
        }
    )

    # Save image
    if response.candidates[0].content.parts[0].inline_data:
        image_data = response.candidates[0].content.parts[0].inline_data.data
        with open(output_path, 'wb') as f:
            f.write(image_data)
        return output_path

    return None
```

### Video Understanding

```python
def analyze_video(video_path: str, prompt: str):
    """Analyze video with Gemini 3 Pro."""

    # Upload video file
    video_file = genai.upload_file(video_path)

    # Wait for processing
    import time
    while video_file.state.name == "PROCESSING":
        time.sleep(2)
        video_file = genai.get_file(video_file.name)

    model = genai.GenerativeModel("gemini-3-pro-vision")
    response = model.generate_content([prompt, video_file])

    return response.text

def analyze_youtube(youtube_url: str, prompt: str):
    """Analyze YouTube video."""

    model = genai.GenerativeModel("gemini-3-pro-vision")
    response = model.generate_content([
        prompt,
        {"youtube_url": youtube_url}
    ])

    return response.text
```

### Audio Understanding

```python
def analyze_audio(audio_path: str, prompt: str):
    """Analyze audio/podcast with Gemini."""

    audio_file = genai.upload_file(audio_path)

    model = genai.GenerativeModel("gemini-3-pro")
    response = model.generate_content([prompt, audio_file])

    return response.text

def transcribe_audio(audio_path: str):
    """Transcribe audio to text."""

    return analyze_audio(
        audio_path,
        "Transcribe this audio accurately. Include speaker labels if multiple speakers."
    )
```

### Long Document Processing (2M context!)

```python
def process_long_document(file_path: str, prompt: str):
    """Process very long documents using 2M context."""

    # Upload document
    doc_file = genai.upload_file(file_path)

    model = genai.GenerativeModel("gemini-3-pro")
    response = model.generate_content([prompt, doc_file])

    return response.text

def summarize_codebase(files: dict):
    """
    Summarize entire codebase using 2M context.

    Args:
        files: {"path/to/file.py": "content", ...}
    """
    context = "# Codebase\n\n"
    for path, content in files.items():
        context += f"## {path}\n```\n{content}\n```\n\n"

    return gemini_chat(
        f"{context}\n\nProvide a comprehensive analysis of this codebase.",
        system_prompt="You are a senior software architect."
    )
```

### Google Search Grounding

```python
def search_grounded_response(query: str):
    """Get response grounded in Google Search results."""

    model = genai.GenerativeModel(
        "gemini-3-pro",
        tools=[{"google_search": {}}]
    )

    response = model.generate_content(query)
    return response.text
```

### Structured Output (JSON)

```python
def structured_output(prompt: str, schema: dict):
    """Get structured JSON output."""

    model = genai.GenerativeModel("gemini-3-pro")

    response = model.generate_content(
        prompt,
        generation_config={
            "response_mime_type": "application/json",
            "response_schema": schema
        }
    )

    import json
    return json.loads(response.text)
```

### Streaming

```python
def stream_response(prompt: str):
    """Stream response for long outputs."""

    model = genai.GenerativeModel("gemini-3-pro")

    response = model.generate_content(prompt, stream=True)

    for chunk in response:
        yield chunk.text
```

### Multi-turn Chat

```python
def create_chat_session(system_prompt: str = None):
    """Create a multi-turn chat session."""

    model = genai.GenerativeModel(
        "gemini-3-pro",
        system_instruction=system_prompt
    )

    chat = model.start_chat(history=[])
    return chat

def chat_message(chat, message: str):
    """Send message in chat session."""
    response = chat.send_message(message)
    return response.text

# Usage
chat = create_chat_session("You are a helpful coding assistant.")
response1 = chat_message(chat, "Write a Python function to sort a list")
response2 = chat_message(chat, "Now add type hints to it")
```

## Advanced Features

### Code Execution

```python
def execute_code(prompt: str):
    """Let Gemini write and execute code."""

    model = genai.GenerativeModel(
        "gemini-3-pro",
        tools=[{"code_execution": {}}]
    )

    response = model.generate_content(prompt)
    return response.text
```

### Function Calling

```python
def with_functions(prompt: str, functions: list):
    """Use function calling."""

    model = genai.GenerativeModel(
        "gemini-3-pro",
        tools=functions
    )

    response = model.generate_content(prompt)
    return response
```

## Nano Banana Pro Prompt Templates

### Photorealistic Portrait
```python
prompt = """
Generate image: Professional headshot photograph
- Subject: confident business professional
- Camera: Sony A7R IV with 85mm f/1.4 lens
- Lighting: soft natural window light with reflector fill
- Background: clean gradient, subtle bokeh
- Quality: 8K, ultra-sharp focus on eyes
- Style: natural, authentic expression
"""
```

### Product Photography
```python
prompt = """
Generate image: E-commerce product photo
- Product: [description]
- Background: pure white seamless
- Lighting: soft diffused studio lighting
- Style: professional, clean, commercial
- Quality: high resolution, color accurate
"""
```

### Creative Illustration
```python
prompt = """
Generate image: Digital illustration
- Subject: [description]
- Style: [cyberpunk/fantasy/minimalist/anime]
- Color palette: [colors]
- Mood: [atmosphere]
- Composition: dynamic, rule of thirds
"""
```

## API Pricing Reference

| Model | Input | Output |
|-------|-------|--------|
| gemini-3-pro | $1.25/1M tokens | $5/1M tokens |
| gemini-3-flash | $0.075/1M tokens | $0.30/1M tokens |
| Image generation | $0.02/image | - |

## Quick Reference

| Task | Code |
|------|------|
| Text generation | `model.generate_content(prompt)` |
| Image analysis | `model.generate_content([prompt, image])` |
| Image generation | Use `response_mime_type: "image/png"` |
| Video analysis | Upload file, then generate_content |
| Long documents | Upload file (2M context!) |
| Streaming | `stream=True` |
| JSON output | `response_mime_type: "application/json"` |

---

## 🎬 Veo 2 - Video Generation

### Overview

Veo 2 - Google's flagship video generation model.

| Feature | Value |
|---------|-------|
| Resolution | Up to 4K |
| Duration | Up to 2 minutes |
| Input | Text, Image |
| Output | Video with audio |

### Generate Video from Text

```python
def generate_video_veo(prompt: str, duration: int = 10):
    """
    Generate video with Veo 2.

    Args:
        prompt: Video description
        duration: Duration in seconds (5-120)
    """
    import requests

    api_key = os.getenv('GEMINI_API_KEY')

    response = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/videos:generate",
        headers={"x-goog-api-key": api_key},
        json={
            "model": "veo-2",
            "prompt": prompt,
            "videoConfig": {
                "durationSeconds": duration,
                "aspectRatio": "16:9"
            }
        }
    )

    return response.json()  # Returns operation ID

def get_video_result(operation_id: str):
    """Get generated video URL."""
    import requests

    api_key = os.getenv('GEMINI_API_KEY')

    response = requests.get(
        f"https://generativelanguage.googleapis.com/v1beta/{operation_id}",
        headers={"x-goog-api-key": api_key}
    )

    data = response.json()
    if data.get("done"):
        return data["response"]["videoUri"]
    return None
```

### Generate Video from Image

```python
def image_to_video(image_path: str, prompt: str, duration: int = 10):
    """Generate video starting from an image."""

    import base64

    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode()

    # Use Gemini API with video generation
    response = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/videos:generate",
        headers={"x-goog-api-key": os.getenv('GEMINI_API_KEY')},
        json={
            "model": "veo-2",
            "prompt": prompt,
            "image": {
                "inlineData": {
                    "mimeType": "image/png",
                    "data": image_data
                }
            },
            "videoConfig": {
                "durationSeconds": duration
            }
        }
    )

    return response.json()
```

---

## 🖼️ Imagen 3 Ultra - Image Generation

### Generate High-Quality Images

```python
def generate_image_imagen(prompt: str, output_path: str,
                          aspect_ratio: str = "1:1",
                          style: str = None):
    """
    Generate image with Imagen 3 Ultra.

    Args:
        prompt: Image description
        output_path: Where to save
        aspect_ratio: "1:1", "16:9", "9:16", "4:3", "3:4"
        style: "photorealistic", "digital_art", "illustration"
    """
    import requests
    import base64

    api_key = os.getenv('GEMINI_API_KEY')

    payload = {
        "model": "imagen-3-ultra",
        "prompt": prompt,
        "aspectRatio": aspect_ratio,
        "numberOfImages": 1
    }

    if style:
        payload["style"] = style

    response = requests.post(
        "https://generativelanguage.googleapis.com/v1beta/images:generate",
        headers={"x-goog-api-key": api_key},
        json=payload
    )

    data = response.json()
    if "predictions" in data:
        image_bytes = base64.b64decode(data["predictions"][0]["bytesBase64Encoded"])
        with open(output_path, "wb") as f:
            f.write(image_bytes)
        return output_path

    return None

def edit_image(image_path: str, mask_path: str, prompt: str, output_path: str):
    """Edit image with mask (inpainting)."""

    import base64

    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode()

    with open(mask_path, "rb") as f:
        mask_data = base64.b64encode(f.read()).decode()

    response = requests.post(
        "https://generativelanguage.googleapis.com/v1beta/images:edit",
        headers={"x-goog-api-key": os.getenv('GEMINI_API_KEY')},
        json={
            "model": "imagen-3-ultra",
            "prompt": prompt,
            "image": {"bytesBase64Encoded": image_data},
            "mask": {"bytesBase64Encoded": mask_data}
        }
    )

    data = response.json()
    if "predictions" in data:
        result = base64.b64decode(data["predictions"][0]["bytesBase64Encoded"])
        with open(output_path, "wb") as f:
            f.write(result)
        return output_path

    return None
```

---

## 🔊 Text-to-Speech (TTS)

```python
def text_to_speech(text: str, output_path: str,
                   voice: str = "en-US-Wavenet-D",
                   speaking_rate: float = 1.0):
    """
    Convert text to speech using Google Cloud TTS via Gemini.

    Voices:
        - en-US-Wavenet-A to J (various English voices)
        - ru-RU-Wavenet-A to E (Russian)
        - Multiple languages available
    """
    from google.cloud import texttospeech

    client = texttospeech.TextToSpeechClient()

    synthesis_input = texttospeech.SynthesisInput(text=text)

    voice_config = texttospeech.VoiceSelectionParams(
        language_code=voice.split("-")[0] + "-" + voice.split("-")[1],
        name=voice
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=speaking_rate
    )

    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice_config,
        audio_config=audio_config
    )

    with open(output_path, "wb") as f:
        f.write(response.audio_content)

    return output_path
```

---

## 🎤 Live API - Real-time Audio/Video

### Real-time Audio Streaming

```python
async def live_audio_session():
    """
    Real-time audio conversation with Gemini Live API.

    Supports:
    - Real-time speech input
    - Real-time speech output
    - Tool use during conversation
    """
    import asyncio
    from google import genai

    client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

    config = {
        "model": "gemini-2.0-flash-live",
        "generation_config": {
            "response_modalities": ["AUDIO"],
            "speech_config": {
                "voice_config": {
                    "prebuilt_voice_config": {"voice_name": "Puck"}
                }
            }
        }
    }

    async with client.aio.live.connect(**config) as session:
        # Send audio
        await session.send({"data": audio_bytes, "mime_type": "audio/pcm"})

        # Receive response
        async for response in session.receive():
            if response.data:
                # Audio response
                yield response.data
            elif response.text:
                # Text response
                print(response.text)

# Available voices: Puck, Charon, Kore, Fenrir, Aoede
```

### Live Video Analysis

```python
async def live_video_analysis(video_stream):
    """Analyze video in real-time."""

    config = {
        "model": "gemini-2.0-flash-live",
        "generation_config": {
            "response_modalities": ["TEXT"]
        }
    }

    async with client.aio.live.connect(**config) as session:
        async for frame in video_stream:
            await session.send({
                "data": frame,
                "mime_type": "image/jpeg"
            })

            response = await session.receive()
            yield response.text
```

---

## 📊 Embeddings

```python
def get_embedding(text: str, model: str = "text-embedding-004"):
    """
    Generate embedding vector.

    Models:
        - text-embedding-004: Latest, best quality (768 dims)
        - textembedding-gecko: Older model
    """
    result = genai.embed_content(
        model=model,
        content=text,
        task_type="retrieval_document"
    )

    return result['embedding']

def get_embeddings_batch(texts: list):
    """Batch embedding for multiple texts."""

    result = genai.embed_content(
        model="text-embedding-004",
        content=texts,
        task_type="retrieval_document"
    )

    return result['embedding']

# Task types:
# - retrieval_document: For indexing documents
# - retrieval_query: For search queries
# - semantic_similarity: For comparing texts
# - classification: For text classification
# - clustering: For grouping similar texts
```

---

## 🧠 Thinking Models (Deep Reasoning)

```python
def deep_reasoning(prompt: str):
    """
    Use Gemini 2.0 Flash Thinking for complex problems.

    Shows explicit reasoning steps before answer.
    """
    model = genai.GenerativeModel("gemini-2.0-flash-thinking-exp")

    response = model.generate_content(prompt)

    # Response includes thinking process
    return {
        "thinking": response.candidates[0].content.parts[0].text,
        "answer": response.candidates[0].content.parts[-1].text
    }
```

---

## 🔧 Built-in Tools

### Google Search Grounding

```python
def grounded_search(query: str):
    """Get response grounded in real-time Google Search."""

    model = genai.GenerativeModel(
        "gemini-2.0-flash",
        tools=["google_search"]
    )

    response = model.generate_content(query)

    return {
        "text": response.text,
        "grounding_metadata": response.candidates[0].grounding_metadata
    }
```

### Code Execution (Sandbox)

```python
def execute_code(prompt: str):
    """Let Gemini write and execute Python code."""

    model = genai.GenerativeModel(
        "gemini-2.0-flash",
        tools=["code_execution"]
    )

    response = model.generate_content(prompt)

    # Get execution results
    for part in response.candidates[0].content.parts:
        if hasattr(part, 'executable_code'):
            print(f"Code: {part.executable_code.code}")
        if hasattr(part, 'code_execution_result'):
            print(f"Result: {part.code_execution_result.output}")

    return response.text
```

### URL Context

```python
def analyze_url(url: str, prompt: str):
    """Analyze content from URL."""

    model = genai.GenerativeModel("gemini-2.0-flash")

    response = model.generate_content([
        prompt,
        {"url": url}
    ])

    return response.text
```

---

## 💰 API Pricing Reference (2025)

### Text Models
| Model | Input | Output |
|-------|-------|--------|
| gemini-2.0-flash | $0.10/1M | $0.40/1M |
| gemini-2.0-pro | $1.25/1M | $5.00/1M |
| gemini-1.5-pro | $1.25/1M | $5.00/1M |
| gemini-1.5-flash | $0.075/1M | $0.30/1M |
| gemini-1.5-flash-8b | $0.0375/1M | $0.15/1M |

### Media Generation
| Model | Price |
|-------|-------|
| Imagen 3 Ultra | $0.04/image |
| Veo 2 | ~$0.05/second |

### Other
| Service | Price |
|---------|-------|
| Embeddings (text-embedding-004) | $0.00001/1K chars |
| Live API | Based on audio duration |

---

## 🔗 API Endpoints Reference

| Endpoint | Purpose |
|----------|---------|
| `generateContent` | Text/multimodal generation |
| `streamGenerateContent` | Streaming responses |
| `embedContent` | Text embeddings |
| `countTokens` | Token counting |
| `images:generate` | Imagen 3 generation |
| `images:edit` | Image editing |
| `videos:generate` | Veo 2 video generation |
| `live.connect` | Real-time audio/video |

---

## Quick Reference

| Task | Code |
|------|------|
| Text generation | `model.generate_content(prompt)` |
| Image analysis | `model.generate_content([prompt, image])` |
| Generate image | Imagen 3 API |
| Generate video | Veo 2 API |
| Embeddings | `genai.embed_content(model, content)` |
| Streaming | `stream=True` |
| Search grounding | `tools=["google_search"]` |
| Code execution | `tools=["code_execution"]` |
| Live audio | `client.aio.live.connect()` |

---

## Tips

1. **2M context** - загружай огромные документы и кодовые базы
2. **Imagen 3 Ultra** - лучшее качество изображений от Google
3. **Veo 2** - генерация видео до 2 минут в 4K
4. **Live API** - реальное время для аудио/видео
5. **Thinking models** - для сложного reasoning
6. **Code execution** - безопасный sandbox для кода
7. **Google Search** - grounding для актуальной информации
8. **gemini-2.0-flash** - лучший баланс скорость/качество
