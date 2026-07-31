# DALL-E / gpt-image prompt templates (перенесено из SKILL.md при компактизации 2026-07-19)

> Шаблоны писались под DALL-E 3, работают и для gpt-image-2 (тот же endpoint `images.generate`).
> Канон: дефолт генерации картинок = NB2 (`config/models.md`, skill `image-generation`) — эти шаблоны для случаев, когда нужен именно OpenAI.

## Хелпер сборки промпта

```python
def create_image_prompt(subject: str, style: str, composition: str,
                        lighting: str, details: list = None) -> str:
    """
    Example:
        create_image_prompt(
            subject="a futuristic city skyline",
            style="cyberpunk digital art",
            composition="wide angle aerial view",
            lighting="neon lights at night, rain reflections",
            details=["flying cars", "holographic billboards", "mega towers"]
        )
    """
    parts = [subject]
    if style:
        parts.append(f"in {style} style")
    if composition:
        parts.append(composition)
    if lighting:
        parts.append(f"with {lighting}")
    if details:
        parts.append(f"featuring {', '.join(details)}")
    return ", ".join(parts)
```

## Photorealistic Portrait

```text
Photorealistic portrait photograph of [subject description],
professional studio lighting with soft key light,
shallow depth of field, shot on Sony A7R IV with 85mm f/1.4 lens,
8K resolution, natural skin texture, catchlights in eyes
```

## Product Photography

```text
Professional product photography of [product],
clean white background, soft diffused studio lighting,
multiple reflections for dimension, sharp focus,
e-commerce ready, high-end advertising quality
```

## Digital Art / Illustration

```text
Digital illustration of [subject],
[art style: cyberpunk / fantasy / minimalist / anime],
vibrant color palette with [colors],
dynamic composition, detailed [specific elements],
trending on ArtStation, masterpiece quality
```

## Architectural Visualization

```text
Architectural visualization of [building/interior],
modern minimalist design, natural lighting through large windows,
clean lines, premium materials (marble, wood, glass),
interior design magazine quality, wide angle view
```

## Infographic / Diagram

```text
Clean professional infographic showing [concept],
flat design style, corporate color palette (blue, white, gray),
clear visual hierarchy, minimal text,
business presentation quality
```

## Presentation Visual (слайды)

```text
Professional business illustration for presentation slide about [topic],
clean modern design, corporate color palette (blue, white, gray),
minimalist style, suitable for executive presentation,
high contrast for projection, no text in image
```

## Sora prompt tips (видео)

Хороший видео-промпт включает: движение камеры (dolly, pan, zoom, tracking shot),
описание действия, детали окружения, свет, стилевой референс.

```text
Cinematic drone shot slowly rising over a futuristic Tokyo at night,
neon signs reflecting in rain-soaked streets below,
flying cars passing between towering skyscrapers,
volumetric fog, cyberpunk atmosphere,
smooth camera movement, 4K quality
```
