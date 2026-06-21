---
name: gamma
description: "Gamma.app AI presentations and documents. Use when asked to create presentations, slides, or pitch decks with AI."
---

# Gamma.app API Skill

## Overview

Expert skill for using Gamma.app - AI-powered presentation and document generation platform.

## API Key

```bash
# Configured in .env.agents
GAMMA_API_KEY=YOUR_GAMMA_API_KEY
```

## When to Use Gamma

**Best for:**
- AI-generated presentations
- Slide decks from text/outline
- Professional documents
- One-pagers and pitch decks
- Interactive web pages
- Marketing materials
- Reports and proposals

**Advantages:**
- Beautiful AI-generated designs
- Multiple export formats (PDF, PPT, Web)
- Automatic layout and styling
- Image integration
- Brand customization
- Collaborative editing
- Embed support

## Dependencies

```bash
pip install requests
```

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/v1/presentations` | POST | Create presentation |
| `/v1/presentations/{id}` | GET | Get presentation |
| `/v1/presentations/{id}` | PUT | Update presentation |
| `/v1/presentations/{id}/export` | POST | Export to PDF/PPT |
| `/v1/generate` | POST | Generate from prompt |
| `/v1/templates` | GET | List templates |

## Basic Usage

### Setup Client

```python
import requests
import os

GAMMA_API_KEY = os.getenv('GAMMA_API_KEY')
BASE_URL = "https://api.gamma.app"

headers = {
    "Authorization": f"Bearer {GAMMA_API_KEY}",
    "Content-Type": "application/json"
}
```

### Generate Presentation from Prompt

```python
def generate_presentation(prompt: str, slides_count: int = 10, style: str = "professional"):
    """
    Generate presentation from text prompt.

    Args:
        prompt: Topic or detailed description
        slides_count: Number of slides (5-20)
        style: "professional", "creative", "minimal", "bold"
    """
    payload = {
        "prompt": prompt,
        "slides_count": slides_count,
        "style": style,
        "include_images": True
    }

    response = requests.post(
        f"{BASE_URL}/v1/generate",
        headers=headers,
        json=payload
    )

    return response.json()

# Usage
result = generate_presentation(
    prompt="AI in Healthcare: Current trends, applications, and future outlook",
    slides_count=12,
    style="professional"
)
print(f"Presentation ID: {result['id']}")
print(f"URL: {result['url']}")
```

### Create Presentation from Outline

```python
def create_from_outline(title: str, outline: list, template: str = None):
    """
    Create presentation from structured outline.

    Args:
        title: Presentation title
        outline: List of slide topics/content
        template: Optional template ID
    """
    payload = {
        "title": title,
        "slides": [
            {"content": slide} for slide in outline
        ]
    }

    if template:
        payload["template_id"] = template

    response = requests.post(
        f"{BASE_URL}/v1/presentations",
        headers=headers,
        json=payload
    )

    return response.json()

# Usage
outline = [
    "Introduction to Machine Learning",
    "Types of ML: Supervised, Unsupervised, Reinforcement",
    "Real-world Applications",
    "Getting Started with ML",
    "Future of Machine Learning"
]

presentation = create_from_outline(
    title="Machine Learning 101",
    outline=outline
)
```

### Export Presentation

```python
def export_presentation(presentation_id: str, format: str = "pdf"):
    """
    Export presentation to file.

    Args:
        presentation_id: ID of presentation
        format: "pdf", "pptx", "html"
    """
    payload = {
        "format": format
    }

    response = requests.post(
        f"{BASE_URL}/v1/presentations/{presentation_id}/export",
        headers=headers,
        json=payload
    )

    result = response.json()
    return result.get("download_url")

# Usage
pdf_url = export_presentation("pres_123abc", format="pdf")
pptx_url = export_presentation("pres_123abc", format="pptx")
```

### Get Presentation

```python
def get_presentation(presentation_id: str):
    """Get presentation details."""

    response = requests.get(
        f"{BASE_URL}/v1/presentations/{presentation_id}",
        headers=headers
    )

    return response.json()
```

### List Templates

```python
def list_templates(category: str = None):
    """
    Get available templates.

    Categories: "business", "education", "marketing", "pitch", "report"
    """
    params = {}
    if category:
        params["category"] = category

    response = requests.get(
        f"{BASE_URL}/v1/templates",
        headers=headers,
        params=params
    )

    return response.json()["templates"]
```

### Update Presentation

```python
def update_slide(presentation_id: str, slide_index: int, content: dict):
    """Update specific slide content."""

    payload = {
        "slides": [
            {
                "index": slide_index,
                "content": content
            }
        ]
    }

    response = requests.put(
        f"{BASE_URL}/v1/presentations/{presentation_id}",
        headers=headers,
        json=payload
    )

    return response.json()
```

## Style Options

| Style | Description | Best For |
|-------|-------------|----------|
| `professional` | Clean, corporate look | Business, reports |
| `creative` | Bold colors, dynamic layouts | Marketing, pitches |
| `minimal` | Lots of whitespace, simple | Tech, startups |
| `bold` | Strong typography, impactful | Sales, presentations |
| `elegant` | Sophisticated, refined | Luxury, formal |

## Content Types

Gamma supports various content blocks:

| Block | Description |
|-------|-------------|
| `text` | Rich text content |
| `heading` | Title/subtitle |
| `bullet_list` | Bullet points |
| `numbered_list` | Numbered items |
| `image` | Images with captions |
| `chart` | Data visualizations |
| `table` | Data tables |
| `quote` | Blockquotes |
| `embed` | External embeds (YouTube, etc.) |

## Complete Example

```python
import requests
import os
import time

class GammaClient:
    def __init__(self):
        self.api_key = os.getenv('GAMMA_API_KEY')
        self.base_url = "https://api.gamma.app"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def generate(self, prompt: str, **kwargs):
        """Generate presentation from prompt."""
        payload = {
            "prompt": prompt,
            "slides_count": kwargs.get("slides_count", 10),
            "style": kwargs.get("style", "professional"),
            "include_images": kwargs.get("include_images", True)
        }

        response = requests.post(
            f"{self.base_url}/v1/generate",
            headers=self.headers,
            json=payload
        )
        return response.json()

    def export(self, presentation_id: str, format: str = "pdf"):
        """Export to file format."""
        response = requests.post(
            f"{self.base_url}/v1/presentations/{presentation_id}/export",
            headers=self.headers,
            json={"format": format}
        )
        return response.json().get("download_url")

    def create_and_export(self, prompt: str, format: str = "pdf"):
        """Generate and export in one call."""
        # Generate
        result = self.generate(prompt)
        presentation_id = result["id"]

        # Wait for generation
        time.sleep(5)

        # Export
        download_url = self.export(presentation_id, format)

        return {
            "id": presentation_id,
            "url": result["url"],
            "download_url": download_url
        }

# Usage
gamma = GammaClient()
presentation = gamma.create_and_export(
    prompt="Quarterly Sales Report Q4 2024: Key metrics, achievements, and 2025 outlook",
    format="pptx"
)
print(f"View: {presentation['url']}")
print(f"Download: {presentation['download_url']}")
```

## Use Cases

| Scenario | Approach |
|----------|----------|
| Quick pitch deck | `generate()` with "pitch" style |
| Detailed report | `create_from_outline()` with sections |
| Marketing materials | `generate()` with "creative" style |
| Training content | `create_from_outline()` with detailed content |
| Sales presentation | `generate()` with "bold" style |

## Tips

1. **Detailed prompts** - более детальные промпты дают лучшие результаты
2. **Outline структура** - для контроля используй outline вместо prompt
3. **Templates** - проверь доступные шаблоны перед созданием
4. **Export timing** - дай время на генерацию перед экспортом
5. **Branding** - настрой цвета и шрифты через templates
6. **Images** - Gamma автоматически подбирает релевантные изображения
7. **Iteration** - используй `update_slide()` для точечных правок
