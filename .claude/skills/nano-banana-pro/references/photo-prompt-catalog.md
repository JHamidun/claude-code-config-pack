# Каталог съёмочных параметров для промптов

> Вынесено из тела навыка. Читать, когда нужно назвать конкретную камеру, объектив,
> схему света или плёнку — то есть когда фотореализм задаётся техникой, а не сюжетом.
> Для реставрации фото это не нужно: там параметры уже зашиты в мастер-шаблон.

## Core Prompt Categories

### 1. Photorealism & Professional Photography

#### Camera & Equipment Specifications
```
Ultra-sharp, full-color large-format image shot with [Camera] and [Lens]
```

**Best Cameras:**
- Sony A7III, Sony A7R IV - detail & dynamic range
- Canon EOS R5 - fast autofocus, video
- Nikon Z9 - sports, action
- Hasselblad X2D - medium format, fashion
- RED V-Raptor - cinematic

**Best Lenses:**
- 85mm f/1.4 - portraits, bokeh
- 50mm f/1.2 - natural perspective
- 35mm f/1.4 - environmental portraits
- 24-70mm f/2.8 - versatility
- 70-200mm f/2.8 - compression, sports

#### Lighting Setups
```
Three-point lighting setup:
- Key light at 45 degrees (warm, 5600K)
- Fill light at -30 degrees (soft, 50% intensity)
- Rim light from behind (golden, highlights hair/shoulders)
- Vignette effect for focus
```

**Lighting Terms:**
- Golden Hour - warm, soft, magical
- Blue Hour - cool, moody, cinematic
- Rembrandt lighting - triangle shadow on cheek
- Butterfly lighting - shadow under nose, beauty
- Loop lighting - slight shadow on opposite side
- Split lighting - dramatic half-face shadow

#### Film Aesthetics
```
Shot on [Film Stock], [ISO], natural film grain
```

**Film Stocks:**
- Kodak Portra 400 - warm skin tones, wedding
- Kodak Ektar 100 - vivid colors, landscape
- Fuji Pro 400H - soft pastels, fashion
- Ilford HP5 - classic B&W, street
- Cinestill 800T - cinematic, tungsten, halation

### 2. Portrait Prompts

#### Professional Headshot
```json
{
  "subject": {
    "age": 35,
    "gender": "female",
    "expression": "confident smile, eyes engaged",
    "skin": "natural texture with visible pores, subtle makeup",
    "hair": "styled professionally, individual strands visible"
  },
  "photography": {
    "camera": "Sony A7III",
    "lens": "85mm f/1.4",
    "aperture": "f/2.0",
    "lighting": "soft natural light from large window, reflector fill"
  },
  "style": {
    "background": "clean gradient, subtle bokeh",
    "color_grade": "neutral with slight warmth",
    "quality": "8K resolution, ultra-sharp focus on eyes"
  },
  "preserve_original": true
}
```

#### Emotional Film Photography
```
Golden Hour portrait of [subject], shot on Kodak Portra 400
Natural backlight creating golden rim around hair
Soft catchlights in eyes, natural skin texture
Expression: [emotion] - subtle, genuine
Background: [setting] with beautiful bokeh
Film grain: subtle, organic
```

#### 2000s Mirror Selfie (Nostalgia)
```json
{
  "era": "2000s",
  "setting": "bathroom mirror selfie",
  "subject": {
    "clothing": ["low-rise jeans", "baby tee", "chunky belt"],
    "accessories": ["flip phone", "dangly earrings", "butterfly clips"],
    "pose": "classic mirror selfie angle"
  },
  "aesthetics": {
    "quality": "early digital camera, slight blur",
    "flash": "direct flash, harsh shadows",
    "color": "slightly oversaturated",
    "timestamp": "bottom right corner"
  }
}
```

### 3. Creative & Experimental

#### Dense Crowd Compositions
```
Aerial view of massive crowd gathered in [location]
Thousands of people, each with distinct features and clothing
"Where's Waldo" style complexity
Every person has unique appearance, no repetition
Photorealistic quality, natural lighting
```

#### Temporal Consistency (Age Progression)
```
Photo series of same person aging through the years:
- Age 20: [description]
- Age 40: [description]
- Age 60: [description]
- Age 80: [description]
Keep facial features exactly consistent across all ages
Same bone structure, eye shape, unique characteristics
```

#### Recursive/Infinite Loop (Droste Effect)
```
Image containing itself recursively (Droste effect)
[Subject] holding a frame showing the same scene
Infinite regression, each iteration smaller but detailed
Mathematical precision in the recursion
```

#### Coordinate-Based Generation
```
Photograph taken at exact coordinates:
Latitude: [X], Longitude: [Y]
Time: [HH:MM], Date: [YYYY-MM-DD]
Season: [season]
Weather conditions: [weather]
Capture the atmosphere and location authentically
```

#### Conceptual Interpretations
```
"How [profession] sees [object]"
Example: "How engineers see the Golden Gate Bridge"
- Show technical annotations
- Structural analysis overlays
- Material specifications
- Force vectors and stress points
```

### 4. Technical Best Practices

#### Face Preservation (Critical for consistency)
```
ALWAYS include in prompts for consistent faces:
- "Keep facial features exactly consistent"
- "preserve_original: true"
- "Same bone structure, eye shape, nose, lips"
- Reference specific features to maintain
```

#### Detail Emphasis
```
Request micro-details:
- "Individual hair strands visible"
- "Natural skin pores and texture"
- "Fabric fibers and weave pattern"
- "Reflections in eyes showing light source"
- "Subtle imperfections for realism"
```

#### Quality Specifiers
```
Resolution & Quality keywords:
- "8K resolution"
- "Ultra-sharp"
- "RAW quality"
- "Uncompressed"
- "Professional retouching"
- "Magazine quality"
```

### 5. Structured JSON Prompt Format

For maximum control, use JSON structure:

```json
{
  "image_type": "portrait | landscape | product | abstract",
  "subject": {
    "description": "detailed subject description",
    "age": "approximate age if person",
    "expression": "emotional state",
    "clothing": ["item1", "item2"],
    "accessories": ["item1", "item2"],
    "pose": "body position description"
  },
  "environment": {
    "setting": "location description",
    "time_of_day": "golden hour | midday | night | etc",
    "weather": "sunny | overcast | rain | etc",
    "background": "background details"
  },
  "photography": {
    "camera": "camera model",
    "lens": "lens specification",
    "aperture": "f-stop value",
    "shutter_speed": "if relevant",
    "iso": "ISO value",
    "film_stock": "if film aesthetic"
  },
  "lighting": {
    "type": "natural | studio | mixed",
    "key_light": "main light description",
    "fill_light": "fill light if any",
    "rim_light": "rim/back light if any",
    "color_temperature": "warm | neutral | cool"
  },
  "style": {
    "color_grade": "color palette description",
    "mood": "emotional tone",
    "quality": "resolution and sharpness",
    "post_processing": "editing style"
  },
  "constraints": {
    "preserve_original": true,
    "avoid": ["elements to avoid"],
    "emphasis": ["elements to emphasize"]
  }
}
```

### 6. Use Case Templates

#### E-commerce Product
```
Professional product photography of [product]
White seamless background, soft diffused lighting
Multiple catch lights for dimension
Sharp focus throughout, no shadows on background
8K resolution, color-accurate
```

#### Social Media Portrait
```
Instagram-worthy portrait of [subject]
[Setting] with aesthetic background
Natural posing, candid feel
Soft editing, skin smoothing (subtle)
Square format, centered composition
Warm color grade, slight lift in shadows
```

#### Editorial Fashion
```
High-fashion editorial shot for [magazine]
Model wearing [outfit] in [setting]
Dramatic lighting, strong shadows
Bold color story: [colors]
Shot by [photographer style reference]
Full-length, dynamic pose
```

#### Real Estate/Architecture
```
Architectural photography of [building/interior]
Wide-angle lens (24mm), straight verticals
HDR technique, balanced exposure
Blue hour exterior / natural light interior
Clean, aspirational aesthetic
Remove distracting elements
```

## Quick Reference Card

| Goal | Key Terms |
|------|-----------|
| Sharp portrait | 85mm f/1.4, eye focus, catchlights |
| Cinematic | 35mm, shallow DOF, film grain, color grade |
| Natural | Golden hour, soft light, candid pose |
| Professional | Studio lighting, clean background, sharp |
| Vintage | Film stock, grain, era-specific styling |
| Dramatic | High contrast, Rembrandt lighting, shadows |
| Soft/Dreamy | Backlit, overexposed background, pastel |

## Common Mistakes to Avoid

1. **Vague descriptions** - Be specific about every element
2. **Missing lighting** - Always specify light source and quality
3. **Generic cameras** - Name specific equipment for realism
4. **Ignoring background** - Background affects entire image mood
5. **Skipping texture** - Request micro-details for realism
6. **No color direction** - Specify color palette and temperature
