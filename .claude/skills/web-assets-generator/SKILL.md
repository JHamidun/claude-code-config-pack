---
name: web-assets-generator
description: "Фавиконы, PWA-иконки, og-images и брендовые баннеры: HTML-шаблон → скриншот. Триггеры: «сделай баннер», «og картинка», «обложка для анонса», «фавикон»."
---

# Web Assets Generator Skill

Generate favicons, PWA icons, social media images, and other web assets.

## When to Use
- User needs favicon for website
- PWA manifest icons required
- Social media meta images (Open Graph, Twitter Cards)
- App store screenshots
- Brand asset generation
- **Branded social/event banner** (og-image, webinar cover, announcement card) — лучше
  не Pillow-текстом, а вёрсткой → скриншот. См. **`references/branded-social-banner.md`**:
  готовый шаблон `assets/banner-template.html` (1200×630, dark editorial: grid + brand
  glow + eyebrow/H1/date-pill/host-row) + `scripts/cut_avatars.py` (портреты → кружки с
  вырезанным фоном через birefnet-portrait). Рендер: chrome-devtools navigate file:// →
  resize 1200×630 → screenshot. Доставка: CDN/S3 → Tilda Page Settings `fb_img` или
  Telegram `sendPhoto` → file_id. Обкатано на og-баннерах edu-проектов и вебинар-баннерах.

## Asset Types

### Favicons
```
favicon.ico          - 16x16, 32x32 (legacy browsers)
favicon-16x16.png    - 16x16
favicon-32x32.png    - 32x32
apple-touch-icon.png - 180x180 (iOS)
```

### PWA Icons (manifest.json)
```json
{
  "icons": [
    { "src": "icon-72x72.png", "sizes": "72x72", "type": "image/png" },
    { "src": "icon-96x96.png", "sizes": "96x96", "type": "image/png" },
    { "src": "icon-128x128.png", "sizes": "128x128", "type": "image/png" },
    { "src": "icon-144x144.png", "sizes": "144x144", "type": "image/png" },
    { "src": "icon-152x152.png", "sizes": "152x152", "type": "image/png" },
    { "src": "icon-192x192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "icon-384x384.png", "sizes": "384x384", "type": "image/png" },
    { "src": "icon-512x512.png", "sizes": "512x512", "type": "image/png" }
  ]
}
```

### Social Media Images
```
og-image.png         - 1200x630 (Facebook, LinkedIn)
twitter-card.png     - 1200x600 (Twitter summary_large_image)
twitter-square.png   - 800x800 (Twitter summary)
```

## HTML Meta Tags

```html
<!-- Favicons -->
<link rel="icon" type="image/x-icon" href="/favicon.ico">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">

<!-- PWA -->
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#4A90D9">

<!-- Open Graph -->
<meta property="og:image" content="https://example.com/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">

<!-- Twitter -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="https://example.com/twitter-card.png">
```

## Generation Methods

### Using Python (Pillow)
```python
from PIL import Image, ImageDraw, ImageFont

def create_icon(size, bg_color, text, output_path):
    img = Image.new('RGBA', (size, size), bg_color)
    draw = ImageDraw.Draw(img)

    # Add text/logo
    font_size = size // 2
    font = ImageFont.truetype("arial.ttf", font_size)
    bbox = draw.textbbox((0, 0), text, font=font)
    x = (size - bbox[2]) // 2
    y = (size - bbox[3]) // 2
    draw.text((x, y), text, fill="white", font=font)

    img.save(output_path)

# Generate all sizes
sizes = [16, 32, 72, 96, 128, 144, 152, 180, 192, 384, 512]
for size in sizes:
    create_icon(size, "#4A90D9", "A", f"icon-{size}x{size}.png")
```

### Using Sharp (Node.js)
```javascript
const sharp = require('sharp');

async function generateIcons(inputSvg) {
  const sizes = [16, 32, 72, 96, 128, 144, 152, 180, 192, 384, 512];

  for (const size of sizes) {
    await sharp(inputSvg)
      .resize(size, size)
      .png()
      .toFile(`icon-${size}x${size}.png`);
  }
}
```

### Using ImageMagick (CLI)
```bash
# From SVG to multiple PNGs
for size in 16 32 72 96 128 144 152 180 192 384 512; do
  convert -background none -resize ${size}x${size} logo.svg icon-${size}x${size}.png
done

# Create ICO with multiple sizes
convert favicon-16x16.png favicon-32x32.png favicon.ico
```

## Social Image Templates

### Open Graph Image (1200x630)
```python
def create_og_image(title, subtitle, bg_color, output_path):
    img = Image.new('RGB', (1200, 630), bg_color)
    draw = ImageDraw.Draw(img)

    # Title
    title_font = ImageFont.truetype("arial-bold.ttf", 60)
    draw.text((60, 200), title, fill="white", font=title_font)

    # Subtitle
    sub_font = ImageFont.truetype("arial.ttf", 30)
    draw.text((60, 300), subtitle, fill="#cccccc", font=sub_font)

    # Logo in corner
    # logo = Image.open("logo.png").resize((100, 100))
    # img.paste(logo, (1040, 480))

    img.save(output_path)
```

## Checklist

- [ ] favicon.ico (multi-size)
- [ ] favicon-16x16.png
- [ ] favicon-32x32.png
- [ ] apple-touch-icon.png (180x180)
- [ ] PWA icons (72-512px)
- [ ] manifest.json
- [ ] og-image.png (1200x630)
- [ ] twitter-card.png (1200x600)
- [ ] HTML meta tags added
