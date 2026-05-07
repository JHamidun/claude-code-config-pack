---
name: claude-api
description: "Claude API Skill"
---

# Claude API Skill

## Overview

Expert skill for using Anthropic Claude API - Claude 4.5 Sonnet, Opus, and Haiku models for text generation, vision, and tool use.

## API Key

```bash
# Ключ берётся из ~/.claude/.credentials.master.env
# ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}

# Models
CLAUDE_SONNET_MODEL=claude-sonnet-4-5-20250514
CLAUDE_OPUS_MODEL=claude-opus-4-5-20250514
CLAUDE_HAIKU_MODEL=claude-haiku-4-5-20250514
```

## When to Use Claude API

**Best for:**
- Complex reasoning and analysis
- Long-form content generation
- Code generation and review
- Vision/image analysis
- Tool use and function calling
- Projects where subscription isn't available

**Advantages:**
- 200K context window
- Advanced reasoning (especially Opus)
- Excellent instruction following
- Strong safety and ethics
- Vision capabilities

## Dependencies

```bash
pip install anthropic
```

## Models

| Model | ID | Best For | Context |
|-------|-----|----------|---------|
| Claude 4.5 Opus | claude-opus-4-5-20250514 | Complex reasoning, research | 200K |
| Claude 4.5 Sonnet | claude-sonnet-4-5-20250514 | Balanced performance | 200K |
| Claude 4.5 Haiku | claude-haiku-4-5-20250514 | Fast, cost-effective | 200K |

## Basic Usage

### Setup Client

```python
from anthropic import Anthropic
import os

client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
```

### Text Generation

```python
def chat(prompt: str, system: str = None, model: str = "claude-sonnet-4-5-20250514"):
    """
    Chat with Claude.

    Models:
        - claude-opus-4-5-20250514: Best quality
        - claude-sonnet-4-5-20250514: Balanced
        - claude-haiku-4-5-20250514: Fast & cheap
    """
    message = client.messages.create(
        model=model,
        max_tokens=4096,
        system=system or "You are a helpful assistant.",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return message.content[0].text

# Usage
response = chat("Explain quantum computing", model="claude-sonnet-4-5-20250514")
```

### Vision (Image Analysis)

```python
import base64

def analyze_image(image_path: str, prompt: str):
    """Analyze image with Claude Vision."""

    with open(image_path, "rb") as f:
        image_data = base64.standard_b64encode(f.read()).decode("utf-8")

    # Determine media type
    if image_path.endswith(".png"):
        media_type = "image/png"
    elif image_path.endswith(".gif"):
        media_type = "image/gif"
    elif image_path.endswith(".webp"):
        media_type = "image/webp"
    else:
        media_type = "image/jpeg"

    message = client.messages.create(
        model="claude-sonnet-4-5-20250514",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]
    )

    return message.content[0].text
```

### Tool Use (Function Calling)

```python
def with_tools(prompt: str, tools: list):
    """Use Claude with tools/function calling."""

    message = client.messages.create(
        model="claude-sonnet-4-5-20250514",
        max_tokens=1024,
        tools=tools,
        messages=[{"role": "user", "content": prompt}]
    )

    # Check if tool was called
    for block in message.content:
        if block.type == "tool_use":
            return {
                "tool": block.name,
                "input": block.input,
                "id": block.id
            }

    return message.content[0].text

# Example tool definition
weather_tool = {
    "name": "get_weather",
    "description": "Get weather for a location",
    "input_schema": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "City name"
            }
        },
        "required": ["location"]
    }
}

result = with_tools("What's the weather in London?", [weather_tool])
```

### Streaming

```python
def stream_chat(prompt: str, system: str = None):
    """Stream response for real-time output."""

    with client.messages.stream(
        model="claude-sonnet-4-5-20250514",
        max_tokens=4096,
        system=system or "You are a helpful assistant.",
        messages=[{"role": "user", "content": prompt}]
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
```

### Multi-turn Conversation

```python
def multi_turn(messages: list, system: str = None):
    """
    Multi-turn conversation with message history.

    messages format:
        [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
    """
    response = client.messages.create(
        model="claude-sonnet-4-5-20250514",
        max_tokens=4096,
        system=system,
        messages=messages
    )

    return response.content[0].text

# Usage
history = []
history.append({"role": "user", "content": "My name is Alice"})
response = multi_turn(history)
history.append({"role": "assistant", "content": response})
history.append({"role": "user", "content": "What's my name?"})
response = multi_turn(history)  # "Your name is Alice"
```

### Extended Thinking (Beta)

```python
def with_thinking(prompt: str, budget_tokens: int = 10000):
    """Use extended thinking for complex reasoning."""

    response = client.messages.create(
        model="claude-sonnet-4-5-20250514",
        max_tokens=16000,
        thinking={
            "type": "enabled",
            "budget_tokens": budget_tokens
        },
        messages=[{"role": "user", "content": prompt}]
    )

    result = {"thinking": None, "response": None}

    for block in response.content:
        if block.type == "thinking":
            result["thinking"] = block.thinking
        elif block.type == "text":
            result["response"] = block.text

    return result
```

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| model | string | Model ID |
| max_tokens | int | Max output tokens (required) |
| system | string | System prompt |
| messages | array | Conversation messages |
| temperature | float | 0-1, randomness |
| top_p | float | Nucleus sampling |
| top_k | int | Top-k sampling |
| tools | array | Function definitions |
| stream | bool | Enable streaming |

## API Pricing (2025)

| Model | Input | Output |
|-------|-------|--------|
| Claude 4.5 Opus | $15/1M tokens | $75/1M tokens |
| Claude 4.5 Sonnet | $3/1M tokens | $15/1M tokens |
| Claude 4.5 Haiku | $0.25/1M tokens | $1.25/1M tokens |

## Quick Reference

| Task | Code |
|------|------|
| Chat | `client.messages.create(model, max_tokens, messages)` |
| Vision | Include image block in messages |
| Tools | Add `tools` parameter |
| Stream | `client.messages.stream(...)` |
| Thinking | Add `thinking` parameter |

---

## 🔍 Web Search (Built-in)

```python
def search_and_answer(query: str):
    """
    Claude with built-in web search for real-time info.

    Requires server-side implementation via MCP or Claude.ai.
    """
    response = client.messages.create(
        model="claude-sonnet-4-5-20250514",
        max_tokens=4096,
        tools=[{
            "type": "web_search",
            "name": "web_search"
        }],
        messages=[{"role": "user", "content": query}]
    )

    return response.content[0].text
```

---

## 📄 File & Document Handling

```python
def analyze_pdf(pdf_path: str, prompt: str):
    """
    Analyze PDF document with Claude.

    Uses base64 encoding for document content.
    """
    import base64

    with open(pdf_path, "rb") as f:
        pdf_data = base64.standard_b64encode(f.read()).decode("utf-8")

    message = client.messages.create(
        model="claude-sonnet-4-5-20250514",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_data
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]
    )

    return message.content[0].text
```

---

## 🖥️ Computer Use

```python
def computer_use_task(task: str, display_size: tuple = (1920, 1080)):
    """
    Let Claude control computer for automation tasks.

    Requires computer_use tool and screen access.
    """
    response = client.messages.create(
        model="claude-sonnet-4-5-20250514",
        max_tokens=4096,
        tools=[
            {
                "type": "computer_20241022",
                "name": "computer",
                "display_width_px": display_size[0],
                "display_height_px": display_size[1]
            },
            {
                "type": "text_editor_20241022",
                "name": "str_replace_editor"
            },
            {
                "type": "bash_20241022",
                "name": "bash"
            }
        ],
        messages=[{"role": "user", "content": task}]
    )

    return response
```

---

## 📦 Batch API (50% Discount)

```python
def create_batch(requests: list):
    """
    Process multiple requests with 50% discount.

    Max 24 hour processing time.
    """
    batch = client.messages.batches.create(
        requests=[
            {
                "custom_id": f"request-{i}",
                "params": {
                    "model": "claude-sonnet-4-5-20250514",
                    "max_tokens": 1024,
                    "messages": [{"role": "user", "content": req}]
                }
            }
            for i, req in enumerate(requests)
        ]
    )

    return batch.id

def get_batch_results(batch_id: str):
    """Get batch results."""

    batch = client.messages.batches.retrieve(batch_id)

    if batch.processing_status == "ended":
        results = []
        for result in client.messages.batches.results(batch_id):
            results.append({
                "custom_id": result.custom_id,
                "response": result.result.message.content[0].text
            })
        return results

    return {"status": batch.processing_status}
```

---

## 🔧 MCP Integration

```python
def with_mcp_tools(prompt: str, mcp_server: str):
    """
    Use Claude with MCP (Model Context Protocol) tools.

    MCP servers provide external capabilities like:
    - File system access
    - Database queries
    - API integrations
    - Browser automation
    """
    # MCP tools are typically configured at the client level
    # See Claude Desktop or Claude Code for MCP integration

    # Example: using MCP tools in messages
    response = client.messages.create(
        model="claude-sonnet-4-5-20250514",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
        # MCP tools injected by client
    )

    return response
```

---

## 🔗 API Endpoints Reference

| Endpoint | Purpose |
|----------|---------|
| `messages.create` | Text generation |
| `messages.stream` | Streaming responses |
| `messages.batches.create` | Batch processing |
| `messages.count_tokens` | Token counting |
| `completions.create` | Legacy completions |

---

## 💰 Updated Pricing (2025)

| Model | Input | Output |
|-------|-------|--------|
| Claude 4.5 Opus | $15/1M | $75/1M |
| Claude 4.5 Sonnet | $3/1M | $15/1M |
| Claude 4.5 Haiku | $0.25/1M | $1.25/1M |
| Batch API | 50% discount | 50% discount |

---

## Tips

1. **Opus** - лучший для сложного reasoning и исследований
2. **Sonnet** - оптимальный баланс качество/цена
3. **Haiku** - быстрый и дешевый для простых задач
4. `max_tokens` обязателен для всех запросов
5. Vision поддерживает PNG, JPEG, GIF, WebP, PDF
6. Extended thinking для математики и логики
7. Используй streaming для длинных ответов
8. **Batch API** - 50% скидка для массовых операций
9. **Computer Use** - автоматизация через GUI
10. **MCP** - расширение через внешние серверы
