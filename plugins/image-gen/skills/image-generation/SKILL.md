---
name: image-generation
description: "AI image generation prompt engineering for DALL-E 3, Gemini Imagen, Stable Diffusion, Midjourney. Use when asked to generate, create, or draw images. Also covers the Krestinin surrealism preset for ad creatives — triggers: «креатив для vk ads», «сюрреализм магритт», «несочетаемые пары для рекламы», «рекламный креатив сюрреализм», «креатив магритт дали»."
---

# Image Generation Skill

Expert image prompt engineering for AI image generators (DALL-E 3, Midjourney, Stable Diffusion, Gemini/Nano Banana Pro).

> **See Also - Specialized API Skills:**
> - **[gemini-3-pro](gemini-3-pro.md)** - Full Gemini suite: Imagen 3, Veo 2 video, TTS, Live API, embeddings
> - **[nano-banana-pro](nano-banana-pro.md)** - Photorealistic portrait templates for Gemini; Gemini-замена DALL-E 3 для сюрреалистичных рекламных пар (без VPN)
> - **[openai-dalle](openai-dalle.md)** - Full OpenAI suite: DALL-E 3, Sora 2, Whisper, GPT-4o, TTS
>
> **See Also - References:**
> - **[references/vk-ads-surrealism-preset.md](references/vk-ads-surrealism-preset.md)** - пресет «эксперт / Магритт-Дали» для рекламных креативов (несочетаемые пары → сюрреализм)
>
> **Considered and rejected (2026-07-20):** inference.sh `belt` CLI (github.com/inference-sh/skills, 628★) — aggregator for 50+ image models incl. FLUX/Reve/Gemini. FLUX and Reve are already reachable via `replicate` skill (1000+ models incl. `black-forest-labs/flux-1.1-pro` and Reve 2.1); Gemini already default here. `belt` adds a second paywalled account (`belt login`, credit system, no published pricing) and a `curl | sh` installer for zero net-new model access — not adopted.

## When to Use
- User asks to create/generate an image
- User needs help writing image prompts
- User wants photorealistic or artistic AI images
- User mentions DALL-E, Midjourney, Stable Diffusion, Gemini image generation

## Prompt Reference Database
Load reference prompts from: `${WORKSPACE}/.claude/prompts/image_prompts_reference.json`

## Core Prompt Structure

### 1. Subject
```
[Main subject] + [Detailed description] + [Pose/Action]
```
Examples:
- "a stylish young woman with confident expression, standing with hands in pockets"
- "a sleek futuristic sports car shaped like a stylized scorpion"
- "a tall humanoid robot with muscular athletic build"

### 2. Clothing/Appearance (for portraits)
```
[Clothing items] + [Colors] + [Style] + [Accessories]
```
Examples:
- "wearing oversized blazer in charcoal grey, minimal gold jewelry, edgy street style"
- "dark sleeveless top, loose wide-legged denim pants, patterned white sneakers"

### 3. Environment
```
[Location type] + [Details] + [Atmosphere]
```
Examples:
- "seamless white studio background with soft diffused lighting"
- "bright cozy living room with cream-colored sofa and green houseplants"
- "urban cafe through glass window with blurred cityscape"

### 4. Lighting
```
[Light type] + [Direction] + [Quality] + [Color]
```
Examples:
- "soft natural light from large windows"
- "dramatic side lighting with high-contrast shadows"
- "studio lighting with clean highlights and minimal shadows"
- "golden hour warm lighting with rim light"

### 5. Camera/Technical
```
[Lens/focal length] + [Angle] + [DOF] + [Film type if applicable]
```
Examples:
- "shot on 85mm lens, shallow depth of field"
- "35mm film photography with rough grainy textures"
- "fisheye lens with extreme distortion"

### 6. Style/Quality
```
[Resolution] + [Style keywords] + [Mood]
```
Examples:
- "8K ultra-detailed, photorealistic, professional quality"
- "editorial fashion photography, high-end magazine look"
- "cinematic composition, dramatic atmosphere"

## Category Templates

### Fashion/Portrait
```
[Quality] photo of [subject description], wearing [detailed clothing],
[pose], [expression], [background/environment], [lighting style],
[camera settings], [style keywords]
```

### Character Integration (Real + Fictional)
```
[Quality] image of [real person description] with [fictional character],
[interaction/pose], [environment], [lighting], [style modifiers],
preserving face exactly as reference
```

### Product Photography
```
[Product description] on [surface/background], [lighting setup],
[camera angle], [reflections/shadows], [quality keywords]
```

### Cinematic Still
```
[Shot type] of [subject] in [dramatic setting], [lighting mood],
[color grading], film still aesthetic, [genre keywords]
```

## Model-Specific Parameters

### Midjourney
```
--ar [aspect ratio] --v [version] --style raw --q [quality 0.25-2]
```
- `--ar 16:9` for widescreen
- `--ar 9:16` for vertical/mobile
- `--ar 1:1` for square
- `--v 6.0` for latest version
- `--style raw` for less stylized

### Stable Diffusion
```json
{
  "steps": 30-60,
  "cfg_scale": 7-12,
  "sampler": "DPM++ 2M Karras",
  "width": 1024,
  "height": 1024
}
```

### DALL-E 3
- Natural language prompts work best
- Be descriptive and specific
- Include style references

### Gemini (DEFAULT — always use this)
- **Default model:** `gemini-3.1-flash-image-preview` (Nano Banana 2 — fast, cheap, 4K)
- **Pro model:** `gemini-3-pro-image-preview` (Nano Banana Pro — higher quality, slower)
- **API:** `from google import genai` + `GOOGLE_API_KEY`
- Supports detailed structured prompts
- Excellent for text rendering and photorealism
- Use `response_modalities=['IMAGE', 'TEXT']`
- Remove `GEMINI_API_KEY` from env if set (SDK conflict)
```python
os.environ.pop('GEMINI_API_KEY', None)
client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))
response = client.models.generate_content(
    model='gemini-3.1-flash-image-preview',  # or 'gemini-3-pro-image-preview' for max quality
    contents=prompt,
    config=types.GenerateContentConfig(response_modalities=['IMAGE', 'TEXT']),
)
```

## Negative Prompts

### General
```
blur, low quality, low resolution, grainy, pixelated, jpeg artifacts
```

### Anatomy (for people)
```
extra limbs, deformed hands, extra fingers, distorted face, ugly,
disfigured, bad anatomy, wrong proportions
```

### Style Conflicts
```
cartoon, anime, illustration, painting, sketch, 3d render
(when photorealistic is needed)
```

### Artifacts
```
watermark, text, logo, frame, border, signature, username
```

## Quality Boosters

Add these for better results:
- "8K" / "4K ultra HD"
- "hyper-realistic" / "photorealistic"
- "ultra-detailed"
- "sharp focus"
- "professional photography"
- "high-end magazine quality"
- "masterpiece"

## Example Full Prompts

### Fashion Portrait
```
Hyper-realistic fashion photo of a confident young woman with natural
makeup, wearing an oversized charcoal grey blazer over white t-shirt,
high-waisted black trousers, minimal gold jewelry. Standing with one
hand in pocket, direct eye contact with camera. Seamless white studio
background, soft diffused studio lighting with clean highlights.
Shot on medium format camera, 85mm lens, shallow depth of field.
Professional fashion photography, editorial style, 8K ultra-detailed.

Negative: blur, grainy, extra fingers, deformed, cartoon, watermark
```

### Character Integration
```
Photorealistic 8K image of a smiling young Asian woman taking a selfie
with Judy Hopps from Zootopia. Both characters standing side by side
in a dark cinema hall, large movie screen visible behind them.
The woman has long black hair, wearing white strapless top with stars.
Judy in her police uniform, smiling. Cinematic lighting, ultra-detailed,
preserve human face exactly as uploaded reference.

Negative: cartoon style on human, deformed face, blurry, low quality
```

### Sci-Fi/Robot
```
Hyperrealistic 8k photo in bright cozy living room. Subject standing
with humanoid robot partner behind them. Robot: tall athletic build,
silver and gunmetal plates, visible cable muscles, glowing blue eyes,
V-shaped torso. Robot's arm wrapped protectively around subject.
Natural sunlight through white curtains, green houseplants, warm neutral
walls. Realistic skin texture, detailed metal surfaces with micro-scratches,
accurate global illumination. Photoreal, cinematic lighting.

Negative: cartoon, anime, low res, horror, grotesque, human skin on robot
```

### Product Shot
```
Sleek black smartphone floating at 45-degree angle above polished
dark marble surface. Dramatic side lighting creating elegant shadows
and specular highlights on screen. Subtle reflection on marble.
Pure black background, product photography style, 8K ultra-detailed,
sharp focus, professional commercial quality.

Negative: blur, reflections showing environment, dust, fingerprints, text
```

## Face Preservation (for character integration)

When user wants their face in the image:
```
"Use the exact same face from the uploaded photo without altering
any facial features or identity. Preserve the face, hairstyle,
body type, clothing, and overall style exactly as in the reference."
```

## Workflow

1. **Clarify vision**: What style, mood, purpose?
2. **Identify elements**: Subject, environment, lighting, style
3. **Choose model**: DALL-E, MJ, SD, or Gemini
4. **Build prompt**: Layer details from general to specific
5. **Add technical params**: Resolution, aspect ratio, model settings
6. **Craft negatives**: Based on potential issues
7. **Generate & iterate**: Refine based on results

## Tips for Best Results

1. **Be specific about details**: Colors, materials, textures
2. **Describe lighting precisely**: Source, quality, direction
3. **Include style references**: "editorial", "cinematic", "product photography"
4. **Layer information**: Main subject first, then context
5. **Use concrete terms**: "charcoal grey" > "dark color"
6. **Specify camera settings**: Adds realism to prompts
7. **Negative prompts matter**: Prevent common issues
8. **Match prompt to model**: Each AI has strengths

## Common Issues & Fixes

| Issue | Solution |
|-------|----------|
| Blurry output | Add "sharp focus", "high resolution" |
| Wrong hands | Add "anatomically correct hands" to prompt, "deformed hands" to negative |
| Cartoon-ish | Add "photorealistic", "photograph", add "cartoon, illustration" to negative |
| Wrong style | Be more specific about style, use negative prompts |
| Text appearing | Add "no text, no watermark" to negative |
