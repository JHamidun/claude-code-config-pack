# Image Generator — справочник по фотографии и промпт-шаблонам

Вынесено из тела агента `image-generator` (2026-08-20). Читать, когда нужен конкретный
подбор техники под задачу или готовый шаблон промпта; для обычной генерации не требуется.

## Камеры

| Камера | Сильная сторона | Для чего |
|--------|-----------------|----------|
| Sony A7III | Динамический диапазон, натуральные цвета | Портреты, editorial |
| Sony A7R IV | 61 МП, предельная детализация | Fashion, beauty, крупная печать |
| Canon EOS R5 | Быстрый AF, тона кожи | Репортаж, события, свадьбы |
| Hasselblad X2D | Средний формат, тональная глубина | High fashion, fine art |
| Nikon Z9 | Универсальность, цветонаука | Документалистика, пейзаж |
| Fujifilm GFX 100S | Средний формат, плёночные симуляции | Editorial, предметка |

## Объективы

| Объектив | Характер | Для чего |
|----------|----------|----------|
| 24mm f/1.4 | Широкий, драматичный | Архитектура, environmental-портрет |
| 35mm f/1.4 | Естественная перспектива | Стрит, документалистика, ростовой |
| 50mm f/1.2 | Классика, мягкое боке | Lifestyle, editorial |
| 85mm f/1.4 | Портретный король | Хедшоты, beauty, fashion |
| 135mm f/2 | Плавный рисунок, отделение от фона | Fashion, editorial |
| 70-200mm f/2.8 | Универсальный зум | События, спорт, дикая природа |
| 100mm f/2.8 Macro | 1:1, предельная резкость | Предметка, украшения, еда |

## Естественный свет

| Схема | Условия | Настроение | Ключевые слова |
|-------|---------|-----------|----------------|
| Golden Hour | Рассвет/закат, 15-30 мин | Тёплое, романтичное | "golden hour, warm backlight, sun flare" |
| Blue Hour | До рассвета / после заката | Холодное, эфемерное | "blue hour, cool tones, twilight ambiance" |
| Overcast | Облачность | Ровное, нейтральное | "overcast sky, soft diffused light, no harsh shadows" |
| Dappled | Сквозь листву/жалюзи | Фактурное | "dappled sunlight, shadow patterns, filtered light" |
| Window Light | Большое окно сбоку | Живописное | "soft window light, Vermeer-style illumination" |

## Студийные схемы

| Схема | Постановка | Настроение | Для чего |
|-------|-----------|-----------|----------|
| Rembrandt | Ключ 45°, треугольник на щеке | Драматично, классика | Портрет, хедшот |
| Butterfly | Ключ сверху, тень под носом | Гламур | Beauty, fashion |
| Split | Ключ 90°, половина лица | Драма, нуар | Арт |
| Loop | Ключ 30-45°, малая тень носа | Выигрышно, естественно | Корпоратив, editorial |
| Clamshell | Ключ сверху + заполнение снизу | Ровно | Beauty, косметика |
| Rim/Edge | Свет сзади, контурная подсветка | Отделение, драма | Силуэты, предметка |
| High Key | Несколько мягких, почти без теней | Чисто, светло | Предметка, fashion, медицина |
| Low Key | Один жёсткий, тёмный фон | Кинематографично | Fine art, драматический портрет |

## Плёнка и цветокоррекция

| Плёнка | Характер | Ключевые слова |
|--------|----------|----------------|
| Kodak Portra 400 | Тёплая кожа, пастель | "Portra 400, warm tones, creamy highlights" |
| Kodak Ektar 100 | Насыщенно, контрастно | "Ektar 100, vivid colors, high saturation" |
| Fuji Pro 400H | Мягкая пастель, холодок | "Pro 400H, pastel tones, airy feel" |
| Cinestill 800T | Кино-halation, вольфрам | "Cinestill 800T, halation, cinematic glow" |
| Ilford HP5+ | Классика ч/б | "HP5+, black and white, medium grain" |

| Цифровой стиль | Ключевые слова |
|----------------|----------------|
| VSCO | "VSCO-style, faded, lifted shadows" |
| Teal-Orange | "teal and orange color grade, cinematic" |
| Clean Editorial | "clean edit, neutral tones, sharp detail" |
| HDR Realism | "HDR, detailed shadows and highlights" |
| Desaturated Film | "desaturated, muted colors, editorial look" |

## Негативные промпты

**Портреты:** deformed, disfigured, extra fingers, extra limbs, fused fingers, mutated hands,
bad anatomy, wrong proportions, blurry eyes, cross-eyed, asymmetric face, plastic skin, waxy
skin, airbrushed skin, uncanny valley, mannequin, bad teeth, floating hair, disconnected limbs

**Предметка:** shadows on white background, color cast, lens distortion, barrel distortion,
reflections of photographer, dirty surface, dust particles, uneven lighting, perspective
distortion, chromatic aberration, motion blur, low contrast

**Пейзаж/сцены:** oversaturated, HDR artifacts, halos around objects, banding in sky,
repeated patterns, tiling artifacts, unnatural colors, floating objects

**Общее:** watermark, signature, text overlay, logo, copyright notice, low quality, low
resolution, jpeg artifacts, pixelated, blurry, cropped, cut off, out of frame, poorly
composed, ugly, poorly drawn, childish, amateur, stock photo watermark

## Соотношения сторон

| Ratio | Размер | Применение |
|-------|--------|-----------|
| 1:1 | 1024x1024 | Соцсети, аватары, превью |
| 16:9 | 1920x1080 | Презентации, hero, обложки YouTube |
| 9:16 | 1080x1920 | Stories, Reels, Shorts |
| 4:3 | 1600x1200 | Блог, статьи |
| 3:2 | 1800x1200 | Печать, портфолио |
| 2:3 | 1200x1800 | Pinterest, вертикальные постеры |
| 21:9 | 2520x1080 | Ультраширокие баннеры |

## Шаблоны промптов

**Портрет/хедшот**
```
Professional headshot of [subject], [expression], direct eye contact.
Shot on Sony A7R IV with 85mm f/1.4 GM at f/2.0, shallow depth of field.
Rembrandt lighting with soft fill card, 5500K.
Clean gradient background from [color1] to [color2].
Natural skin texture with visible pores, no airbrushing.
8K, Kodak Portra 400 emulation, subtle film grain.
```

**Предметка**
```
Professional product photography of [product] on [surface].
[top-down / 45-degree / eye-level], centered composition.
Shot on Fujifilm GFX 100S with 100mm f/2.8 Macro.
High-key: large softbox above, white reflectors both sides.
Sharp throughout at f/8. Clean [color] background, no visible shadows.
8K, color-calibrated, e-commerce ready.
```

**Пейзаж**
```
[Scene], expansive view, [season/time of day].
Shot on Nikon Z9 with 24mm f/1.4 at f/11. [Golden hour / Blue hour / Storm light].
Rich detail foreground to background, deep depth of field.
[Kodak Ektar 100 / Fuji Velvia]. 8K, HDR dynamic range, no oversaturation.
```

**Диаграмма/инфографика**
```
Clean professional [flowchart / architecture / process diagram].
Flat design, [blue-gray / brand colors]. Clear hierarchy, readable labels.
White background, thin lines, rounded corners. Modern tech aesthetic.
High contrast, vector-clean edges, presentation-ready.
```

**Иллюстрация**
```
[watercolor / oil painting / digital art / anime] illustration of [subject].
Style of [Studio Ghibli / Moebius / James Jean]. [warm earth / neon / pastels].
[Centered / rule of thirds / dynamic diagonal] composition.
Rich detail, [brushstrokes / clean digital / grainy]. High resolution.
```

**UI-мокап**
```
Modern [mobile app / web dashboard / landing page] UI design.
[Light / dark mode], [minimalist / glassmorphism / material design].
[Color scheme] accent, clean typography. Device frame: [iPhone 15 Pro / MacBook].
Sharp text, consistent design system, 2x retina resolution.
```
