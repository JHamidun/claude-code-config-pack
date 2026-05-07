---
name: openai-dalle
description: "OpenAI API Skill (Full Suite)"
---

# OpenAI API Skill (Full Suite)

> **See Also:**
> - **[image-generation](image-generation.md)** - General prompt engineering for all image generators
> - **[gemini-3-pro](gemini-3-pro.md)** - Gemini suite: Imagen 3, Veo 2, TTS, Live API
> - **[nano-banana-pro](nano-banana-pro.md)** - Photorealistic portrait templates (Gemini)

## Overview

Expert skill for using OpenAI API - полный набор возможностей:
- **Text**: GPT-5.1, o3 (reasoning)
- **Images**: DALL-E 3
- **Video**: Sora 2 (с синхронным аудио)
- **Audio TTS**: Text-to-Speech (6 голосов)
- **Audio STT**: Whisper (транскрипция)
- **Embeddings**: text-embedding-3-small/large
- **Moderation**: контент-фильтрация

## API Key

```bash
# Уже настроен в .env.agents
OPENAI_API_KEY=YOUR_OPENAI_API_KEY
```

## Dependencies

```bash
pip install openai
```

## DALL-E 3 Image Generation

### Basic Image Generation

```python
from openai import OpenAI
import os
import requests

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def generate_image(prompt: str, size: str = "1024x1024",
                   quality: str = "standard", style: str = "vivid"):
    """
    Generate image with DALL-E 3.

    Args:
        prompt: Image description
        size: "1024x1024", "1792x1024", "1024x1792"
        quality: "standard" or "hd"
        style: "vivid" or "natural"

    Returns:
        URL of generated image
    """
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size=size,
        quality=quality,
        style=style,
        n=1
    )

    return response.data[0].url

def generate_and_save_image(prompt: str, output_path: str,
                            size: str = "1024x1024"):
    """Generate and save image to file."""
    url = generate_image(prompt, size)

    # Download image
    response = requests.get(url)
    with open(output_path, 'wb') as f:
        f.write(response.content)

    return output_path
```

### DALL-E 3 Best Practices

```python
# Good prompt structure for DALL-E 3
def create_dalle_prompt(
    subject: str,
    style: str,
    composition: str,
    lighting: str,
    details: list = None
) -> str:
    """
    Create optimized DALL-E 3 prompt.

    Example:
        create_dalle_prompt(
            subject="a futuristic city skyline",
            style="cyberpunk digital art",
            composition="wide angle aerial view",
            lighting="neon lights at night, rain reflections",
            details=["flying cars", "holographic billboards", "mega towers"]
        )
    """
    prompt_parts = [subject]

    if style:
        prompt_parts.append(f"in {style} style")

    if composition:
        prompt_parts.append(composition)

    if lighting:
        prompt_parts.append(f"with {lighting}")

    if details:
        prompt_parts.append(f"featuring {', '.join(details)}")

    return ", ".join(prompt_parts)
```

### DALL-E 3 Prompt Templates

#### Photorealistic Portrait
```python
prompt = """
Photorealistic portrait photograph of [subject description],
professional studio lighting with soft key light,
shallow depth of field, shot on Sony A7R IV with 85mm f/1.4 lens,
8K resolution, natural skin texture, catchlights in eyes
"""
```

#### Product Photography
```python
prompt = """
Professional product photography of [product],
clean white background, soft diffused studio lighting,
multiple reflections for dimension, sharp focus,
e-commerce ready, high-end advertising quality
"""
```

#### Digital Art / Illustration
```python
prompt = """
Digital illustration of [subject],
[art style: cyberpunk / fantasy / minimalist / anime],
vibrant color palette with [colors],
dynamic composition, detailed [specific elements],
trending on ArtStation, masterpiece quality
"""
```

#### Architectural Visualization
```python
prompt = """
Architectural visualization of [building/interior],
modern minimalist design, natural lighting through large windows,
clean lines, premium materials (marble, wood, glass),
interior design magazine quality, wide angle view
"""
```

#### Infographic / Diagram
```python
prompt = """
Clean professional infographic showing [concept],
flat design style, corporate color palette (blue, white, gray),
clear visual hierarchy, minimal text,
business presentation quality
"""
```

## GPT-4o / o1 Text Generation

### Basic Chat Completion

```python
def chat_completion(prompt: str, system_prompt: str = None,
                    model: str = "gpt-5.1"):
    """
    Get chat completion from GPT-5.1.

    Models:
        - gpt-5.1: Latest flagship model (best quality)
        - gpt-5.1-mini: Faster, cheaper version
        - gpt-4o: Previous gen, still excellent
        - o3: Best reasoning (expensive, complex tasks)
        - o3-mini: Good reasoning (faster than o3)
        - o1-preview: Previous reasoning model
    """
    messages = []

    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model=model,
        messages=messages
    )

    return response.choices[0].message.content
```

### Structured Output

```python
def structured_output(prompt: str, schema: dict, model: str = "gpt-5.1"):
    """Get structured JSON output."""
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )

    import json
    return json.loads(response.choices[0].message.content)
```

### Vision (GPT-5.1 with Images)

```python
import base64

def analyze_image(image_path: str, prompt: str):
    """Analyze image with GPT-5.1 vision."""

    # Read and encode image
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')

    response = client.chat.completions.create(
        model="gpt-5.1",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_data}"
                        }
                    }
                ]
            }
        ]
    )

    return response.choices[0].message.content

def analyze_image_url(image_url: str, prompt: str):
    """Analyze image from URL."""
    response = client.chat.completions.create(
        model="gpt-5.1",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            }
        ]
    )

    return response.choices[0].message.content
```

## o3 Reasoning Models

### When to Use o3

- Complex multi-step reasoning
- Math and scientific problems
- Code generation with complex logic
- Strategic planning & analysis
- PhD-level research tasks

```python
def reasoning_task(prompt: str, use_mini: bool = False):
    """
    Use o3 for complex reasoning.

    Note: o3 models support system prompts (unlike o1).
    """
    model = "o3-mini" if use_mini else "o3"

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content
```

## Complete Workflow Examples

### Generate Image for Presentation

```python
def create_presentation_visual(topic: str, output_dir: str):
    """Create visual for presentation slide."""

    # Generate image prompt
    prompt = f"""
    Professional business illustration for presentation slide about {topic},
    clean modern design, corporate color palette (blue, white, gray),
    minimalist style, suitable for executive presentation,
    high contrast for projection, no text in image
    """

    # Generate image
    output_path = f"{output_dir}/{topic.replace(' ', '_')}.png"
    return generate_and_save_image(prompt, output_path, size="1792x1024")
```

### Generate Product Images

```python
def create_product_images(product_name: str, product_description: str,
                          output_dir: str, count: int = 3):
    """Generate multiple product images."""

    angles = ["front view", "45-degree angle", "lifestyle context"]
    paths = []

    for i, angle in enumerate(angles[:count]):
        prompt = f"""
        Professional product photography of {product_name},
        {product_description},
        {angle}, clean white background,
        soft studio lighting, e-commerce quality,
        8K resolution, sharp focus throughout
        """

        path = f"{output_dir}/{product_name}_{i+1}.png"
        generate_and_save_image(prompt, path)
        paths.append(path)

    return paths
```

### Analyze & Improve Image

```python
def analyze_and_suggest_improvements(image_path: str):
    """Analyze image and suggest improvements."""

    analysis = analyze_image(
        image_path,
        """Analyze this image and provide:
        1. What's in the image (detailed description)
        2. Technical quality assessment (lighting, composition, focus)
        3. Suggested improvements
        4. An improved prompt for regenerating this image
        Format as JSON."""
    )

    return analysis
```

## API Pricing Reference (as of 2025)

| Model | Input | Output |
|-------|-------|--------|
| gpt-5.1 | $5/1M tokens | $15/1M tokens |
| gpt-5.1-mini | $0.50/1M tokens | $1.50/1M tokens |
| gpt-4o | $2.50/1M tokens | $10/1M tokens |
| o3 | $20/1M tokens | $80/1M tokens |
| o3-mini | $5/1M tokens | $20/1M tokens |
| DALL-E 3 Standard | $0.04/image | - |
| DALL-E 3 HD | $0.08/image | - |

## Quick Reference

| Task | Code |
|------|------|
| Generate image | `client.images.generate(model="dall-e-3", prompt=...)` |
| Chat completion | `client.chat.completions.create(model="gpt-5.1", messages=...)` |
| Vision analysis | Include image_url in messages content |
| Structured output | `response_format={"type": "json_object"}` |
| Reasoning | Use `o3` or `o3-mini` model |

---

## 🎬 Sora 2 - Video Generation

### Overview

Sora 2 Pro - flagship video generation с синхронным аудио (высшее качество).

| Model | Resolution | Price/sec | Quality |
|-------|------------|-----------|---------|
| sora-2 | 720x1280, 1280x720 | $0.10 | Standard |
| **sora-2-pro** | 720x1280, 1280x720 | $0.30 | **Highest** |

| Feature | Value |
|---------|-------|
| Input | Text, Image |
| Output | Video with synced audio |
| Duration | 5-60 seconds |

### Generate Video from Text

```python
def generate_video(prompt: str, duration: int = 10, resolution: str = "1280x720",
                   pro: bool = True):
    """
    Generate video with Sora 2 Pro.

    Args:
        prompt: Video description
        duration: Duration in seconds (5-60)
        resolution: "1280x720" (landscape) or "720x1280" (portrait)
        pro: Use sora-2-pro for highest quality
    """
    model = "sora-2-pro" if pro else "sora-2"

    response = client.videos.generate(
        model=model,
        prompt=prompt,
        duration=duration,
        resolution=resolution
    )

    return response.id  # Video generation ID

def get_video_status(video_id: str):
    """Check video generation status."""
    response = client.videos.retrieve(video_id)

    return {
        "status": response.status,  # "pending", "processing", "completed", "failed"
        "url": response.url if response.status == "completed" else None,
        "error": response.error if response.status == "failed" else None
    }

def wait_for_video(video_id: str, timeout: int = 600):
    """Wait for video completion and return URL."""
    import time

    start = time.time()
    while time.time() - start < timeout:
        status = get_video_status(video_id)

        if status["status"] == "completed":
            return status["url"]
        elif status["status"] == "failed":
            raise Exception(f"Video failed: {status['error']}")

        time.sleep(10)

    raise TimeoutError("Video generation timed out")
```

### Generate Video from Image

```python
def generate_video_from_image(image_url: str, prompt: str, duration: int = 10):
    """Generate video from starting image."""

    response = client.videos.generate(
        model="sora-2",
        prompt=prompt,
        duration=duration,
        image=image_url  # Starting frame
    )

    return response.id
```

### Sora 2 Prompt Tips

```python
# Good video prompts include:
# - Camera movement (dolly, pan, zoom, tracking shot)
# - Action/motion description
# - Environment details
# - Lighting conditions
# - Style reference

video_prompt = """
Cinematic drone shot slowly rising over a futuristic Tokyo at night,
neon signs reflecting in rain-soaked streets below,
flying cars passing between towering skyscrapers,
volumetric fog, cyberpunk atmosphere,
smooth camera movement, 4K quality
"""
```

---

## 🎤 Whisper - Speech to Text

### Transcribe Audio

```python
def transcribe_audio(audio_path: str, language: str = None):
    """
    Transcribe audio to text with Whisper.

    Supported formats: mp3, mp4, mpeg, mpga, m4a, wav, webm
    Max file size: 25 MB
    """
    with open(audio_path, "rb") as audio_file:
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language=language,  # ISO-639-1 code, e.g., "en", "ru", "es"
            response_format="text"  # "json", "text", "srt", "vtt", "verbose_json"
        )

    return response

def transcribe_with_timestamps(audio_path: str):
    """Transcribe with word-level timestamps."""

    with open(audio_path, "rb") as audio_file:
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json",
            timestamp_granularities=["word", "segment"]
        )

    return {
        "text": response.text,
        "words": response.words,
        "segments": response.segments
    }
```

### Translate Audio to English

```python
def translate_audio(audio_path: str):
    """Translate any language audio to English text."""

    with open(audio_path, "rb") as audio_file:
        response = client.audio.translations.create(
            model="whisper-1",
            file=audio_file
        )

    return response.text
```

### Generate SRT Subtitles

```python
def generate_subtitles(audio_path: str, output_path: str):
    """Generate SRT subtitle file from audio."""

    with open(audio_path, "rb") as audio_file:
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="srt"
        )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(response)

    return output_path
```

---

## 🔊 TTS - Text to Speech

### Available Voices

| Voice | Description |
|-------|-------------|
| alloy | Neutral, versatile |
| echo | Warm, conversational |
| fable | Expressive, British |
| onyx | Deep, authoritative |
| nova | Friendly, upbeat |
| shimmer | Soft, calm |

### Generate Speech

```python
def text_to_speech(text: str, output_path: str, voice: str = "alloy",
                   model: str = "tts-1-hd"):
    """
    Convert text to speech.

    Args:
        text: Text to convert (max 4096 chars)
        output_path: Output file path (.mp3, .opus, .aac, .flac, .wav, .pcm)
        voice: alloy, echo, fable, onyx, nova, shimmer
        model: tts-1 (faster) or tts-1-hd (higher quality)
    """
    response = client.audio.speech.create(
        model=model,
        voice=voice,
        input=text
    )

    response.stream_to_file(output_path)
    return output_path

def text_to_speech_stream(text: str, voice: str = "alloy"):
    """Stream audio for real-time playback."""

    response = client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=text
    )

    # Returns audio bytes for streaming
    return response.content
```

### Generate Podcast/Audiobook

```python
def generate_audiobook(chapters: list, output_dir: str, voice: str = "fable"):
    """Generate audiobook from chapters."""

    paths = []
    for i, chapter in enumerate(chapters):
        # Split long chapters into chunks (4096 char limit)
        chunks = [chapter[i:i+4000] for i in range(0, len(chapter), 4000)]

        chapter_audio = []
        for j, chunk in enumerate(chunks):
            path = f"{output_dir}/chapter_{i+1}_part_{j+1}.mp3"
            text_to_speech(chunk, path, voice=voice, model="tts-1-hd")
            chapter_audio.append(path)

        paths.append(chapter_audio)

    return paths
```

---

## 📊 Embeddings

### Generate Embeddings

```python
def get_embedding(text: str, model: str = "text-embedding-3-small"):
    """
    Generate embedding vector.

    Models:
        - text-embedding-3-small: 1536 dims, cheaper
        - text-embedding-3-large: 3072 dims, better quality
    """
    response = client.embeddings.create(
        model=model,
        input=text
    )

    return response.data[0].embedding

def get_embeddings_batch(texts: list, model: str = "text-embedding-3-small"):
    """Generate embeddings for multiple texts."""

    response = client.embeddings.create(
        model=model,
        input=texts
    )

    return [item.embedding for item in response.data]
```

### Semantic Search Example

```python
import numpy as np

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def semantic_search(query: str, documents: list, top_k: int = 5):
    """Search documents by semantic similarity."""

    # Embed query and documents
    query_embedding = get_embedding(query)
    doc_embeddings = get_embeddings_batch(documents)

    # Calculate similarities
    similarities = []
    for i, doc_emb in enumerate(doc_embeddings):
        sim = cosine_similarity(query_embedding, doc_emb)
        similarities.append((i, sim, documents[i]))

    # Sort by similarity
    similarities.sort(key=lambda x: x[1], reverse=True)

    return similarities[:top_k]
```

---

## 🛡️ Moderation

```python
def check_moderation(text: str):
    """Check content for policy violations."""

    response = client.moderations.create(input=text)

    result = response.results[0]

    return {
        "flagged": result.flagged,
        "categories": {
            cat: flagged
            for cat, flagged in result.categories.model_dump().items()
            if flagged
        },
        "scores": result.category_scores.model_dump()
    }
```

---

## 💰 API Pricing Reference (2025)

### Text Models
| Model | Input | Output |
|-------|-------|--------|
| gpt-5.1 | $5/1M tokens | $15/1M tokens |
| gpt-5.1-mini | $0.50/1M | $1.50/1M |
| gpt-4o | $2.50/1M | $10/1M |
| o3 | $20/1M | $80/1M |
| o3-mini | $5/1M | $20/1M |

### Image & Video
| Model | Price |
|-------|-------|
| DALL-E 3 Standard | $0.04/image |
| DALL-E 3 HD | $0.08/image |
| Sora 2 | $0.10/second |
| Sora 2 Pro | $0.30/second |

### Audio
| Model | Price |
|-------|-------|
| Whisper | $0.006/minute |
| TTS | $0.015/1K chars |
| TTS HD | $0.030/1K chars |

### Embeddings
| Model | Price |
|-------|-------|
| text-embedding-3-small | $0.02/1M tokens |
| text-embedding-3-large | $0.13/1M tokens |

---

---

## 🔍 Web Search (Built-in)

```python
def search_and_answer(query: str):
    """
    GPT with built-in web search for real-time info.

    Available in gpt-5.1 and o3 models.
    """
    response = client.chat.completions.create(
        model="gpt-5.1",
        messages=[{"role": "user", "content": query}],
        tools=[{"type": "web_search"}]
    )

    return response.choices[0].message.content

def search_with_citations(query: str):
    """Get answer with source citations."""

    response = client.responses.create(
        model="gpt-5.1",
        input=query,
        tools=[{"type": "web_search_preview"}]
    )

    # Extract citations
    citations = []
    for item in response.output:
        if hasattr(item, 'annotations'):
            for ann in item.annotations:
                if ann.type == "url_citation":
                    citations.append({
                        "title": ann.title,
                        "url": ann.url
                    })

    return {
        "text": response.output_text,
        "citations": citations
    }
```

---

## 📄 File & Document Handling

```python
def upload_file(file_path: str, purpose: str = "assistants"):
    """
    Upload file to OpenAI.

    Purposes:
        - assistants: For Assistants API
        - fine-tune: For fine-tuning
        - batch: For batch processing
    """
    with open(file_path, "rb") as f:
        file = client.files.create(file=f, purpose=purpose)
    return file.id

def analyze_document(file_path: str, prompt: str):
    """Analyze PDF, DOCX, or other documents."""

    # Upload file
    file_id = upload_file(file_path, "assistants")

    # Create assistant with file
    assistant = client.beta.assistants.create(
        model="gpt-5.1",
        tools=[{"type": "file_search"}],
        tool_resources={"file_search": {"vector_store_ids": []}}
    )

    # Create vector store and add file
    vector_store = client.beta.vector_stores.create(name="doc_store")
    client.beta.vector_stores.files.create(
        vector_store_id=vector_store.id,
        file_id=file_id
    )

    # Query
    thread = client.beta.threads.create()
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=prompt
    )

    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=assistant.id
    )

    messages = client.beta.threads.messages.list(thread_id=thread.id)
    return messages.data[0].content[0].text.value
```

---

## 🖥️ Computer Use (Operator)

```python
def computer_use_task(task: str):
    """
    Let GPT control computer via Operator.

    Can interact with:
        - Web browsers
        - Desktop applications
        - File system
    """
    response = client.responses.create(
        model="computer-use-preview",
        tools=[{
            "type": "computer_use_preview",
            "display_width": 1920,
            "display_height": 1080,
            "environment": "browser"  # or "desktop"
        }],
        input=task,
        truncation="auto"
    )

    return response
```

---

## 🔄 Realtime API (Voice)

```python
import asyncio
import websockets

async def realtime_conversation():
    """
    Real-time voice conversation with GPT.

    Supports:
        - Voice input/output
        - Function calling
        - Interruptions
    """
    uri = "wss://api.openai.com/v1/realtime"

    async with websockets.connect(
        uri,
        extra_headers={
            "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
            "OpenAI-Beta": "realtime=v1"
        }
    ) as ws:
        # Configure session
        await ws.send(json.dumps({
            "type": "session.update",
            "session": {
                "model": "gpt-4o-realtime-preview",
                "voice": "alloy",
                "modalities": ["text", "audio"],
                "turn_detection": {"type": "server_vad"}
            }
        }))

        # Send audio
        await ws.send(json.dumps({
            "type": "input_audio_buffer.append",
            "audio": base64_audio_data
        }))

        # Receive responses
        async for message in ws:
            data = json.loads(message)
            if data["type"] == "response.audio.delta":
                yield base64.b64decode(data["delta"])
```

---

## 🤖 Assistants API

```python
def create_assistant(name: str, instructions: str, tools: list = None):
    """Create a persistent assistant."""

    return client.beta.assistants.create(
        name=name,
        instructions=instructions,
        model="gpt-5.1",
        tools=tools or [
            {"type": "code_interpreter"},
            {"type": "file_search"}
        ]
    )

def chat_with_assistant(assistant_id: str, message: str, thread_id: str = None):
    """Chat with assistant."""

    if not thread_id:
        thread = client.beta.threads.create()
        thread_id = thread.id

    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=message
    )

    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread_id,
        assistant_id=assistant_id
    )

    messages = client.beta.threads.messages.list(thread_id=thread_id)
    return messages.data[0].content[0].text.value
```

---

## 🔧 Code Interpreter

```python
def run_code(prompt: str, files: list = None):
    """
    Let GPT write and execute Python code.

    Features:
        - Matplotlib charts
        - Data analysis
        - File processing
    """
    assistant = client.beta.assistants.create(
        model="gpt-5.1",
        tools=[{"type": "code_interpreter"}]
    )

    thread = client.beta.threads.create()

    # Attach files if provided
    attachments = []
    if files:
        for file_path in files:
            file_id = upload_file(file_path, "assistants")
            attachments.append({
                "file_id": file_id,
                "tools": [{"type": "code_interpreter"}]
            })

    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=prompt,
        attachments=attachments
    )

    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=assistant.id
    )

    messages = client.beta.threads.messages.list(thread_id=thread.id)
    return messages.data[0].content
```

---

## 📦 Batch API (50% Discount)

```python
def create_batch(requests: list):
    """
    Process multiple requests with 50% discount.

    Max 24 hour processing time.
    """
    import json

    # Create JSONL file
    batch_file = []
    for i, req in enumerate(requests):
        batch_file.append({
            "custom_id": f"request-{i}",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": req
        })

    # Write to file
    with open("batch_input.jsonl", "w") as f:
        for line in batch_file:
            f.write(json.dumps(line) + "\n")

    # Upload
    file = client.files.create(
        file=open("batch_input.jsonl", "rb"),
        purpose="batch"
    )

    # Create batch
    batch = client.batches.create(
        input_file_id=file.id,
        endpoint="/v1/chat/completions",
        completion_window="24h"
    )

    return batch.id

def get_batch_results(batch_id: str):
    """Get batch results."""
    batch = client.batches.retrieve(batch_id)

    if batch.status == "completed":
        output_file = client.files.content(batch.output_file_id)
        return output_file.text

    return {"status": batch.status}
```

---

## 🔗 API Endpoints Reference

| Endpoint | Purpose |
|----------|---------|
| `v1/chat/completions` | Text generation |
| `v1/responses` | Responses API (with tools) |
| `v1/images/generations` | DALL-E 3 images |
| `v1/images/edits` | Image editing |
| `v1/videos` | Sora 2 videos |
| `v1/audio/speech` | TTS generation |
| `v1/audio/transcriptions` | Whisper STT |
| `v1/audio/translations` | Audio translation |
| `v1/embeddings` | Text embeddings |
| `v1/moderations` | Content moderation |
| `v1/realtime` | Realtime voice API |
| `v1/assistants` | Assistants API |
| `v1/threads` | Conversation threads |
| `v1/files` | File management |
| `v1/vector_stores` | Vector storage |
| `v1/fine-tuning` | Model fine-tuning |
| `v1/batch` | Batch processing (50% off) |

---

## Quick Reference

| Task | Code |
|------|------|
| Generate image | `client.images.generate(model="dall-e-3", prompt=...)` |
| Generate video | `client.videos.generate(model="sora-2", prompt=...)` |
| Transcribe audio | `client.audio.transcriptions.create(model="whisper-1", file=...)` |
| Text to speech | `client.audio.speech.create(model="tts-1-hd", voice=..., input=...)` |
| Chat completion | `client.chat.completions.create(model="gpt-5.1", messages=...)` |
| Get embedding | `client.embeddings.create(model="text-embedding-3-small", input=...)` |
| Check moderation | `client.moderations.create(input=...)` |

---

## Tips

1. **DALL-E 3** - автоматически улучшает промпты, будь конкретен
2. **Sora 2** - описывай движение камеры и действия для лучших результатов
3. **Whisper** - поддерживает 100+ языков автоматически
4. **TTS** - используй `tts-1-hd` для качественного аудио, `tts-1` для скорости
5. **Embeddings** - `text-embedding-3-small` достаточен для большинства задач
6. **o3** - используй только для сложного reasoning (дорого)
7. **Batch API** - для массовых операций со скидкой 50%
