# Multi-face keyframes — несколько РЕАЛЬНЫХ узнаваемых лиц в одном кадре

Когда в кадре должны быть **конкретные реальные люди** (команда, поздравление, корпоративный эпик), а не «похожие актёры». Главный урок проекта «клиентский трибьют» (поздравление [Client], июнь 2026): держать 3-4 настоящих лица в одном кинокадре — отдельная задача, и провайдер для неё выбирается иначе, чем для одиночного героя.

## TL;DR — какой провайдер

| Лиц в кадре | Провайдер | Почему |
|---|---|---|
| 0–1 | **Nano Banana Pro** (`gemini-3-pro-image-preview`) | Лучший кинолук, надёжно держит одно лицо через reference-фото |
| 2 | **Nano Banana Pro** | Ещё держит, но проверяй второго |
| **3–4 конкретных** | **GPT-Image-2** (`gpt-image-2-2026-04-21`) через `/v1/images/edits` с НЕСКОЛЬКИМИ `image[]` | Держит мультилицо заметно ТОЧНЕЕ; Nano даёт «похожих незнакомцев» на 3-4 |

**Эмпирика (десятки итераций с реальной правкой пользователя):** Nano Banana Pro надёжен на 1-2 лицах; на 3-4 конкретных людях вторичные лица «плывут» — становятся похожими, но чужими людьми (юзер: «вообще не тот», «какой-то левый чел»). GPT-Image-2 с мультиреференсом держит каждое лицо точнее, **но** склонен к «постановочному групповому фото» (все смотрят в камеру, статичная поза) → лечится явным киношным промптом.

## GPT-Image-2 multi-reference (рабочий рецепт)

`/v1/images/edits` принимает НЕСКОЛЬКО `image[]` в multipart — каждый референс = одно лицо. Модель сшивает их в сцену по промпту.

```python
import os, json, base64, io, urllib.request, urllib.error
from PIL import Image

OPENAI_KEY = os.environ["OPENAI_API_KEY"]
MODEL = "gpt-image-2-2026-04-21"

# Кинопромпт — ОБЯЗАТЕЛЬНО гасит "posed group photo"
STYLE = (" Candid CINEMATIC FILM STILL captured mid-action — NOT a posed group photo, the people are NOT "
         "looking at the camera, a natural in-the-moment documentary shot. Shot on ARRI Alexa, 50mm "
         "anamorphic lens, dramatic chiaroscuro lighting, teal-and-orange color grade, volumetric haze, "
         "35mm film grain, shallow depth of field, in the style of Roger Deakins, epic movie still, "
         "ultra-wide cinematic framing. No text, no captions, no logos.")

def build_body(prompt, face_files, refs_dir, boundary):
    parts = [
        f'--{boundary}\r\nContent-Disposition: form-data; name="model"\r\n\r\n{MODEL}\r\n',
        f'--{boundary}\r\nContent-Disposition: form-data; name="prompt"\r\n\r\n{prompt}\r\n',
        f'--{boundary}\r\nContent-Disposition: form-data; name="size"\r\n\r\n1536x1024\r\n',
        f'--{boundary}\r\nContent-Disposition: form-data; name="quality"\r\n\r\nhigh\r\n',
        f'--{boundary}\r\nContent-Disposition: form-data; name="n"\r\n\r\n1\r\n',
    ]
    body = ''.join(parts).encode()
    for i, fn in enumerate(face_files):
        with open(f"{refs_dir}/{fn}", "rb") as f:
            img = f.read()
        body += (
            f'--{boundary}\r\nContent-Disposition: form-data; name="image[]"; filename="ref{i}.jpg"\r\n'
            f'Content-Type: image/jpeg\r\n\r\n'
        ).encode() + img + b'\r\n'
    body += f'--{boundary}--\r\n'.encode()
    return body

def gen(prompt, face_files, refs_dir, out_png, boundary="----cine_1"):
    body = build_body(prompt + STYLE, face_files, refs_dir, boundary)
    req = urllib.request.Request(
        'https://api.openai.com/v1/images/edits', data=body,
        headers={'Authorization': f'Bearer {OPENAI_KEY}',
                 'Content-Type': f'multipart/form-data; boundary={boundary}'})
    with urllib.request.urlopen(req, timeout=420) as resp:
        result = json.loads(resp.read())
    png = base64.b64decode(result['data'][0]['b64_json'])
    im = Image.open(io.BytesIO(png)).convert("RGB")
    # crop 21:9 cinemascope из 1536x1024 (берём верхне-центральную треть)
    w, h = im.size; H21 = 658
    off = int((h - H21) * 0.30)
    im.crop((0, off, w, off + H21)).save(out_png)
```

**Промпт сцены — три обязательных приёма:**

1. **`Use the reference photos as their EXACT faces.`** — в конце промпта, прямое указание.
2. **Дизамбигуация людей словами** — описывай отличительные черты каждого, иначе модель путает похожих:
   - `the BALDING bearded CAPTAIN ... in the center` (= главный герой: высокий лоб, залысины)
   - `a YOUNGER man with a FULL HEAD of dark hair and a dark beard` (= YourFirstName: густая шевелюра)
   - `a man in light amber-tinted glasses`, `a woman with a short dark bob`, `a blonde woman with round glasses`
3. **Анти-«левый чел»:** `EVERY visible face must match one of these reference people; do NOT invent or add any other faces.` — без этого модель дорисовывает посторонних в массовку.

**Параллелизм:** `ThreadPoolExecutor(max_workers=4)`, генерируй **3-4 варианта на сцену** (gc1/gc2/gc3/gc4) и давай человеку выбрать — лица из партии в партию пляшут, выбор из 3-4 почти всегда даёт годный. **Отвергнутые варианты НЕ удаляй** — складывай в `_review/`; человек может передумать, а ре-генерация стоит времени (и доверия — урок: не уничтожай артефакты молча).

## Nano Banana Pro multi-reference (для 1-2 лиц + как fallback)

```python
import os
os.environ.pop("GEMINI_API_KEY", None)   # CRITICAL до import
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
MODEL = "gemini-3-pro-image-preview"

def lf(path):
    with open(path, "rb") as f:
        return f.read()

# Передаём референсы как Part.from_bytes ПЕРЕД текстом
parts = [types.Part.from_bytes(data=lf(p), mime_type="image/jpeg") for p in face_paths] + [prompt]
resp = client.models.generate_content(
    model=MODEL, contents=parts,
    config=types.GenerateContentConfig(response_modalities=["IMAGE", "TEXT"]))
for cand in (resp.candidates or []):
    for part in ((getattr(cand, "content", None) and cand.content.parts) or []):
        inl = getattr(part, "inline_data", None)
        if inl and inl.data:
            open(out_png, "wb").write(inl.data)
```

Преимущество Nano: **нативный 21:9 cinemascope** (GPT-Image-2 max 1536x1024 → нужен crop с потерей) и более «настоящий» кинолук. Недостаток: на 3-4 лицах дрейфует.

Идентичность **НЕ** сохраняется между отдельными `generate_content` вызовами — для серии сцен либо переподавай те же reference-фото каждый раз (как здесь), либо reference-chaining (см. `nano-banana-pro` skill).

## Hero / ensemble баланс

Когда есть **главный герой + команда** (а не просто толпа), пользователь хочет тонкого баланса (урок пользователя): главный должен быть заметнее, но НЕ один в кадре, команда должна «занимать внимание» как ансамбль. В промпт:

```
The clear HERO and leader is the man from reference photo 1 (he has a HIGH RECEDING HAIRLINE and a
full dark beard) and he is the most prominent. Around him his team is ALSO prominent and clearly
visible as an ensemble: among them a YOUNGER man with a FULL HEAD of dark hair (reference photo 2)
and other teammates (reference photos 3 and 4).
```

Не «выделяй одного и поставь остальных фоном» — это считывается как «все остальные неважны». Формулируй «hero most prominent, team also prominent as an ensemble».

## Контактный лист для ревью ≤ 2000px

Чтобы показать человеку/vision-API все варианты разом — собирай contact sheet, но **ширина ≤ 2000px**, иначе many-image read падает (`image dimensions exceed max 2000px`). Тайл 21:9 ~640×274, 4 колонки. См. `_tribute_project/scripts/contact_sheet.py` (PIL, подпись каждого тайла именем файла).

## Биометрический QA (5 точек на лицо)

При выборе варианта сверяй с референсом по 5 признакам: **(1) лоб/линия волос** (залысины vs густая шевелюра), **(2) борода/щетина**, **(3) расстояние между глаз**, **(4) форма носа**, **(5) видимые приметы** (очки, родинки). Порог приёмки для ансамбля: **≥3/5 на второстепенных** лицах достаточно (требовать 5/5 на массовке нереалистично), но **главный герой обязан нести самую отличительную черту** (залысины и борода у главного героя). Если у героя черта потерялась — вариант брак, даже если остальные ок.

## Чеклист перед анимацией

- [ ] Каждое видимое лицо = один из референсов (нет «левых» людей)
- [ ] Главный несёт свою отличительную черту (≥3/5 биометрии на второстепенных)
- [ ] Главного видно как главного, команда — как ансамбль (если так задумано)
- [ ] Не «постановочное фото»: люди в действии, не смотрят в камеру (для GPT-Image-2 — критично)
- [ ] Похожих людей развёл словами (залысины vs шевелюра, очки, причёска)
- [ ] 21:9 получен нативно (Nano) или кропом 0.30-сверху (GPT-Image-2)
- [ ] Сгенерено 3-4 варианта/сцена, человек выбрал лучший; отвергнутые → `_review/` (не удалять)

## Анимация multi-face keyframe

Лица решены на стадии keyframe → анимируй **Seedance start-only** (см. `runway-seedance.md`), но добавь в clip-prompt **анти-дрейф-суффикс**, чтобы за 5 секунд лица не «поплыли»:

```
Cinematic film look, photorealistic, smooth natural motion. No text overlays, no warping,
no extra or deformed limbs, stable consistent faces, no identity drift.
```

Держи движение медленным (slow push-in / slow dolly) — резкое движение провоцирует морфинг лиц. Проверено на 4 командных кадрах «клиентского трибьюта».
