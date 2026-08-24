# Audio для видео: Lyria 2 + ElevenLabs Music + TTS

## §1 — Lyria 2 (Vertex AI, commercial-safe)

**Auth: OAuth2 service account ONLY.** API key возвращает `401 UNAUTHENTICATED` immediately.

Env vars в `~/.claude/.credentials.master.env`:

```
GOOGLE_CLOUD_PROJECT_ID=<project_id>
GOOGLE_SERVICE_ACCOUNT_KEY_PATH=/abs/path/to/service-account.json
```

НЕ конфликтует с `GOOGLE_API_KEY` (которая для Veo / google-genai SDK).

### Generation

```python
import os, base64
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession

creds = service_account.Credentials.from_service_account_file(
    os.environ['GOOGLE_SERVICE_ACCOUNT_KEY_PATH'],
    scopes=['https://www.googleapis.com/auth/cloud-platform'],  # exact scope
)
session = AuthorizedSession(creds)

PROJECT_ID = os.environ['GOOGLE_CLOUD_PROJECT_ID']
url = (
    f'https://us-central1-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}'
    f'/locations/us-central1/publishers/google/models/lyria-002:predict'
)

# CRITICAL: seed и sample_count > 1 ВЗАИМОИСКЛЮЧАЮЩИ → 400 INVALID_ARGUMENT
# Передавай ОДНО из двух, не оба
body = {
    'instances': [{
        'prompt': 'Dark mystery cinematic underscore, low strings, sub-bass pulse, no melody',
        'negative_prompt': 'vocals, lyrics, pop, drums',
        'sample_count': 1,
        # 'seed': 42,  # ← НЕЛЬЗЯ если sample_count > 1
    }],
}

resp = session.post(url, json=body, timeout=300)
resp.raise_for_status()

audio_b64 = resp.json()['predictions'][0]['bytesBase64Encoded']
with open('bgm.wav', 'wb') as f:
    f.write(base64.b64decode(audio_b64))
```

**Output spec:** WAV, **~30s fixed length**, 48kHz stereo. Commercial-safe license.

### Длинные треки — acrossfade несколько 30s sample'ов

```bash
ffmpeg -i bgm_01.wav -i bgm_02.wav -filter_complex \
  "[0:a][1:a]acrossfade=d=1.5:c1=tri:c2=tri[out]" \
  -map "[out]" bgm_60s.wav
```

Для 3+: цепочкой, каждый раз acrossfade с предыдущим результатом.

### Регион / model ID

- Регион: **us-central1** (для других — 404)
- Model: `lyria-002` (для `lyria-001` — 404)
- Wrong region + right model = 404
- Right region + wrong model = 404

## §1b — Lyria 3 quick path (Generative Language API, dev/demo)

**Альтернатива §1** когда OAuth service-account setup лишний (dev, prototype, demo).
Lyria 3 доступна через **обычный `GOOGLE_API_KEY`** на том же эндпоинте что и Gemini.

Модели:
- `models/lyria-3-clip-preview` — short clips (~30s), быстрее
- `models/lyria-3-pro-preview` — длиннее, выше качество

**Tradeoffs vs Lyria 2 (Vertex AI):**
- ✅ Один env var (`GOOGLE_API_KEY`), без service-account JSON
- ✅ Один и тот же ключ для Veo + Gemini + Lyria + Flash Image
- ❌ `-preview` модели = **не commercial-safe license**. Для прода — §1 Vertex AI Lyria 2
- ❌ Schema другая (`responseModalities: ["AUDIO"]`, не `predict`)

### Generation

```python
import os, json, base64, urllib.request

key = os.environ['GOOGLE_API_KEY']
model = 'lyria-3-clip-preview'  # или 'lyria-3-pro-preview'
url = (
    f'https://generativelanguage.googleapis.com/v1beta/models/'
    f'{model}:generateContent?key={key}'
)

payload = {
    'contents': [{'role': 'user', 'parts': [{
        'text': 'Calm cinematic piano pad, soft strings, 70bpm, reflective, '
                'instrumental only, no vocals'
    }]}],
    'generationConfig': {'responseModalities': ['AUDIO']},
}

req = urllib.request.Request(
    url,
    data=json.dumps(payload).encode(),
    headers={'Content-Type': 'application/json'},
    method='POST',
)
with urllib.request.urlopen(req, timeout=120) as r:
    data = json.loads(r.read())

# Извлечение inline audio
parts = data['candidates'][0]['content']['parts']
for p in parts:
    inline = p.get('inlineData') or p.get('inline_data')
    if inline and 'data' in inline:
        mime = inline.get('mimeType', 'audio/mpeg')
        ext = 'mp3' if 'mpeg' in mime else 'wav'
        with open(f'bgm.{ext}', 'wb') as f:
            f.write(base64.b64decode(inline['data']))
        break
```

**Грабли:**
- Ответ в `candidates[0].content.parts[*].inlineData.data` — base64-encoded
- MIME обычно `audio/mpeg` (mp3), не WAV. Проверяй и конвертируй через ffmpeg если pipeline ждёт WAV
- 401 → проверь что `GOOGLE_API_KEY` не пустой (часто конфликтует с `GEMINI_API_KEY` — `os.environ.pop('GEMINI_API_KEY', None)` ДО запроса)
- 404 на model → fallback: `lyria-3-pro-preview`. List models: `GET /v1beta/models?key=...` отфильтруй `lyria`

### LLM-генерируемый mood prompt

Lyria даёт лучший результат когда prompt **описательный**, а не «happy music». Pipeline: пост → LLM-mood-director → Lyria prompt:

```python
mood_sys = (
    "You compose a prompt for a text-to-music model describing background "
    "music for a video. 1 line, 15-25 words, specify genre, instruments, "
    "tempo, mood. Example: 'calm cinematic piano and soft synth pads, "
    "70bpm, reflective, gentle strings, minimalist'. Do not copy words "
    "from the post. Instrumental only."
)
mood_prompt = llm_chat([
    {'role': 'system', 'content': mood_sys},
    {'role': 'user', 'content': post_text[:1200]},
]).strip().strip('"')

audio = lyria_generate(mood_prompt)
```

Этот pattern даёт уникальный трек **под конкретный пост**, а не generic library track.

## §2 — ElevenLabs Music (`client.music.compose`)

```python
from elevenlabs import ElevenLabs

client = ElevenLabs(api_key=os.environ['ELEVENLABS_API_KEY'])

result = client.music.compose(
    prompt='Tense underscore, sub-bass pulse, sparse percussion, no vocals',
    music_length_ms=30000,        # ← НЕ length_ms (см. ниже)
    force_instrumental=True,       # инструментал без вокала
    model_id='music_v1',
)

with open('bgm.mp3', 'wb') as f:
    for chunk in result:
        f.write(chunk)
```

### CRITICAL — имена параметров (current SDK)

В установленном SDK правильные имена — **`music_length_ms`**, **`force_instrumental`**, **`model_id='music_v1'`**.
`length_ms=...` → **`TypeError`** (старая сигнатура, ловит at runtime). Проверено в production (проект [Client], 2026).

> Для инструментала `force_instrumental=True` надёжнее, чем «no vocals» в тексте промпта.

### Named-artist policy (CRITICAL)

Это **всегда** возвращает `content_policy_violation`:

- `'in the style of [Named Artist]'`
- `'[Artist]-style vocal'`
- `'sounds like [Track] by [Artist]'`
- `'[Composer] cinematic'`

**Workaround = ТОЛЬКО descriptor substitution:**

| Запрещено | Заменить на дескрипторы |
|---|---|
| `Hans Zimmer cinematic` | `Massive orchestral underscore, sub-bass pulse, brass swells, heroic` |
| `in the style of Vangelis` | `Synthesized 80s sci-fi, analog warm pads, slow arpeggios` |
| `Lo-fi hip-hop like Nujabes` | `Jazzy lo-fi, soft vinyl crackle, lazy drum samples, mellow piano` |
| `Sounds like Lord of the Rings` | `Celtic strings, choir swells, epic fantasy underscore` |

### Длинные треки (>30s)

2 сегмента по 30s с narrative handoff в prompt'е:

```python
seg1 = client.music.compose(
    prompt='Dark mystery cinematic, low strings, builds slowly',
    music_length_ms=30000, force_instrumental=True, model_id='music_v1',
)
seg2 = client.music.compose(
    prompt='Continues from dark mystery, transitions into battle, percussion enters',
    music_length_ms=30000, force_instrumental=True, model_id='music_v1',
)
```

Конкатенируй **БЕЗ crossfade** — на музыке crossfade jarring. Direct concat работает с handoff prompt'ом.

## §3 — ElevenLabs TTS — production voice IDs

### Свой клонированный голос

`<YOUR_VOICE_ID>` — идентификатор ТВОЕГО голоса; пак не поставляется ни с каким.
Берётся в кабинете ElevenLabs → Voices → свой голос → **ID**
(https://elevenlabs.io/app/voice-lab), либо `GET /v1/voices` — клоны помечены
`category: "cloned"`. Держи его в `ELEVENLABS_VOICE_ID_RU`
(`~/.claude/.credentials.master.env`), а не в тексте скрипта: скрипты озвучки
читают именно эту переменную.

```python
import os
audio = client.text_to_speech.convert(
    voice_id=os.getenv('ELEVENLABS_VOICE_ID_RU'),   # свой клон, НЕ HeyGen-голос
    text='Сегодня разберём, как…',
    model_id='eleven_multilingual_v2',
    voice_settings={
        'stability': 0.55,
        'similarity_boost': 0.80,
        'style': 0.15,
        'use_speaker_boost': True,
    },
)
```

Отклонения от этих параметров → voice cracks, потеря тембра, over-acting. **Не править.**

### EN voices on RU (эмпирически лучше native RU)

| Voice | voice_id | Use | Settings (production) |
|---|---|---|---|
| Matthew Villain | `bwCXcoVxWNYMlC6Esa8u` | mystical / усталый воин / book trailer narrator | `stability=0.30, similarity=0.80, style=0.40, speaker_boost=True` |
| George | `JBFqnCBsd6RMkjVDRZzb` | **тёплый рассказчик** — поздравления, трибьюты, award VO | `stability=0.35, similarity=0.85, style=0.35, speaker_boost=True` |
| Brian | (см. ElevenLabs catalog) | confident male, корпоративные шортсы | — |

Модель: `eleven_multilingual_v2`. На русском тексте дают тембр заметно лучше native RU voices (подтверждено на коротких вертикальных роликах).

**Выбор тона под жанр:** Matthew = «усталый ветеран» (мрачный книжный трейлер); **George = тёплый/человечный** (корпоративное поздравление — там выбрали именно George, не «трейлерного» Matthew). Перед коммитом прогони 2-3 реплики на каждого кандидата по дуге ролика (открытие + кульминация + развязка), не одну фразу.

### Russian VO — ударения (combining acute U+0301)

ElevenLabs иногда ставит неверное ударение на омографах/редких словах (`шторма́` вместо `што́рма`). Фикс — вставить **combining acute accent U+0301** прямо после ударной гласной в тексте TTS:

```python
text = "Каждая большая история начинается со што́рма."  # о + U+0301
```

Если знак ударения не помогает — перефразируй на слово, где ударение однозначно (`начинается с бу́ри`). Всегда **прослушивай** результат на ударных/редких словах перед сборкой.

> Грабли (Windows): `print()` строки с combining-диакритикой падает на cp1251 даже когда обычная кириллица проходит — печатай через numeric format (`print("regenerated vo_%02d" % n)`), см. `windows.md` §2.

### Settings ranges (general)

| Параметр | Range | Эффект |
|---|---|---|
| `stability` | 0.20–0.35 | expressive, актёрская подача |
| `stability` | >0.60 | robotic, монотонный |
| `similarity_boost` | 0.80–0.90 | character lock, держит тембр |
| `style` | 0.2 | intimate, разговорный |
| `style` | 0.8 | dramatic, театральный |
| `use_speaker_boost` | True | всегда True для production |

Тестируй 5-10 voice IDs с identical text прежде чем commit к final.

## §4 — Когда что использовать

| Задача | Решение |
|---|---|
| Background music под cinematic trailer | **Lyria 2** (commercial-safe license, lush) |
| Quick BGM под шортс | **ElevenLabs Music** (быстрее, не нужен service account) |
| **Полный 60s+ оркестровый score с дугой** (шторм→триумф) | ElevenLabs Music / Lyria, либо локальный `ace-step`. Онлайн-Suno в пак не входит: он ходил в чужой оплаченный аккаунт по cookie |
| **Песня со словами** под ролик | **Suno** (`make_instrumental=False`) — единственный из трёх кто поёт |
| Voiceover своим голосом RU | **ElevenLabs TTS** — свой клон (`$ELEVENLABS_VOICE_ID_RU`) + settings из §3 |
| Voiceover актёрский EN | **ElevenLabs TTS** Matthew Villain или Brian |
| Voiceover тёплый рассказчик RU (трибьют) | **ElevenLabs TTS** George `JBFqnCBsd6RMkjVDRZzb` |
| Voiceover «корпоративный» RU | **ElevenLabs TTS** EN voices на RU тексте через `eleven_multilingual_v2` |
| Кинематографический score для книжного трейлера | **Lyria 2** 2×30s + acrossfade |
| Лицензионно чистый score для коммерческого ролика | **Lyria 2** (Vertex AI, commercial-safe) |

## §4b — Длинный score / песня + климакс-нарезка

Клиента к Suno в паке нет: он работал через долгоживущую cookie чужого оплаченного
аккаунта. Уроки ниже сняты на нём, но применимы к любому генератору длинных треков —
ElevenLabs Music, Lyria, локальный `ace-step`.

- **2 дубля на запрос.** Один и тот же промпт возвращает ДВА независимых рендера, заметно разных (у [Client] дубль 2 имел теплее French-horn/choir, чем дубль 1). Слушай оба, выбирай ухом, а не по порядку.
- **CDN 403-пока-рендерится.** `https://cdn1.suno.ai/{clip_id}.mp3` отдаёт 403 пока считается (5-10 мин), 200 когда готов. Не падай на 403 — loop с backoff 5-10с до 200.
- **Промпт инструментала:** одно предложение `[solo instrument] over [ensemble], builds to [climax], then [resolution]`, имена инструментов (cello, timpani, French horn, choir), БЕЗ жанровых тегов и БЕЗ имён артистов. Даёт стабильные 60-62с вместо разброса 50/70с.
- **Климакс-нарезка длинного трека под короткое видео.** Suno часто выдаёт 3+ мин. Не обрезай с начала — найди энергетический пик (RMS по секундам, сглаживание) и вырежи окно ~62с так, чтобы **кульминация легла на ~47с куска** (под «вершину» нарратива, за ~10-15с до конца ролика). Готовый скрипт: `scripts/climax_cut.py IN.mp3 OUT.mp3 --win 62 --climax-at 47` (fade in 1.5 / out 3).

```python
# суть analyze_cut.py
rms = [rms_per_0.5s]; sm = smooth(rms, k=5)
climax_t = argmax(sm) * 0.5
start = max(0, climax_t - CLIMAX_AT)         # кульминация трека → 47с куска
if start + WIN > dur: start = max(0, dur - WIN)
# ffmpeg -ss start -t WIN -af "afade=in:0:1.5,afade=out:(WIN-3):3"
```

### Narration-only path (без поющих слов) — рекомендуется для трибьютов

Поющий текст рискует исказиться/прозвучать нелепо. Надёжнее: **Suno чистый инструментал** (`make_instrumental=True`, в промпте `instrumental, no vocals`) + отдельный **ElevenLabs TTS** закадр, статический баланс (без sidechain), `loudnorm I=-14`. На практике заказчик ролика выбрал именно этот путь: «текст песни не нравится, лучше музыка и закадр». Развязывает тайминг музыки и голоса.

## §5 — Sound effects (ElevenLabs)

```python
fx = client.text_to_sound_effects.convert(
    text='heavy door slam with reverb',
    duration_seconds=2.0,
    prompt_influence=0.7,
)
```

Для production используется редко — обычно дешевле взять Freesound / Pixabay royalty-free.

## §6 — TTS-with-timestamps → ASS karaoke БЕЗ Whisper-pass

**Зачем.** Стандартный путь субтитров — `TTS → Whisper ASR → ASS karaoke`. Whisper-пасс дорогой по времени и **ошибается на сложных словах** (имена, термины, кириллица). Если **текст озвучки известен заранее** (мы же его сами и подавали в TTS), ASR избыточен.

ElevenLabs эндпоинт `/v1/text-to-speech/{voice_id}/with-timestamps` возвращает audio **и** per-character `start_time/end_time`. Из этого билдится ASS karaoke с точностью «до символа», без второго прохода.

### Запрос

```python
import os, json, base64, urllib.request

key = os.environ['ELEVENLABS_API_KEY']
voice_id = os.environ['ELEVENLABS_VOICE_ID_RU']   # свой клон (ElevenLabs, НЕ HeyGen)
url = f'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/with-timestamps'

payload = {
    'text': 'Сегодня разберём, как…',
    'model_id': 'eleven_multilingual_v2',
    'voice_settings': {'stability': 0.5, 'similarity_boost': 0.75},
}
req = urllib.request.Request(
    url,
    data=json.dumps(payload).encode(),
    headers={
        'xi-api-key': key,
        'Content-Type': 'application/json',
        'Accept': 'application/json',  # JSON, не audio/mpeg
    },
    method='POST',
)
with urllib.request.urlopen(req, timeout=120) as r:
    data = json.loads(r.read())

audio = base64.b64decode(data['audio_base64'])
with open('vo.mp3', 'wb') as f:
    f.write(audio)

al = data['alignment']
chars   = al['characters']                          # ['С', 'е', 'г', ...]
starts  = al['character_start_times_seconds']       # [0.00, 0.04, 0.08, ...]
ends    = al['character_end_times_seconds']         # [0.04, 0.08, 0.12, ...]
timing  = [{'ch': c, 'start': s, 'end': e}
           for c, s, e in zip(chars, starts, ends)]
```

### Char-timings → words

```python
def chars_to_words(timing):
    words = []
    buf, buf_start = [], None
    for t in timing:
        ch = t['ch']
        if ch.isspace() or ch in ',.;:!?—–-\n':
            if buf:
                words.append((''.join(buf), buf_start, t['start']))
                buf, buf_start = [], None
        else:
            if buf_start is None:
                buf_start = t['start']
            buf.append(ch)
    if buf:
        words.append((''.join(buf), buf_start, timing[-1]['end']))
    return words   # [(word, start_sec, end_sec), ...]
```

### ASS karaoke с per-word highlight

```python
def t_ass(sec):
    h = int(sec // 3600); m = int((sec % 3600) // 60); s = sec - h*3600 - m*60
    return f'{h}:{m:02d}:{s:05.2f}'

ASS_HEAD = """[Script Info]
ScriptType: v4.00+
PlayResX: 720
PlayResY: 1280
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,DejaVu Sans,44,&H00FFFFFF,&H0000F0FF,&H00000000,&H90000000,1,0,0,0,100,100,0,0,1,4,0,2,30,30,160,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

def build_ass(words, words_per_cue=3):
    events = []
    for i in range(0, len(words), words_per_cue):
        group = words[i:i + words_per_cue]
        cue_start = group[0][1]
        cue_end   = group[-1][2]
        parts, prev_end = [], cue_start
        for (w, ws, we) in group:
            if ws > prev_end + 0.01:
                parts.append(f'{{\\k{int((ws - prev_end) * 100)}}}')
            parts.append(f'{{\\kf{max(1, int((we - ws) * 100))}}}{w} ')
            prev_end = we
        events.append(
            f'Dialogue: 0,{t_ass(cue_start)},{t_ass(cue_end)},'
            f'Cap,,0,0,0,,{"".join(parts).rstrip()}'
        )
    return ASS_HEAD + '\n'.join(events) + '\n'

open('caps.ass', 'w', encoding='utf-8').write(build_ass(chars_to_words(timing)))
```

### Burn

```bash
ffmpeg -y -i mixed.mp4 -vf "ass=caps.ass" -c:a copy final.mp4
```

ASS-стиль выше даёт **жёлтую заливку активного слова** (SecondaryColour `&H0000F0FF&` = yellow в ASS BGR-format) + жирный белый текст + 4px чёрная обводка + полупрозрачная подложка. Меняй `Fontsize`, `MarginV` под аспект.

### Tradeoffs vs Whisper + SubMagic

| | TTS-with-timestamps | Whisper + SubMagic |
|---|---|---|
| Точность слов | 100% (исходный текст) | 92–96% (ASR ошибки на терминах/именах) |
| Время | +0s (already in TTS response) | +30–60s Whisper-pass + SubtitleService poll |
| Стоимость | $0 (ElevenLabs charge тот же) | +your subtitle API call |
| Кириллица | Идеально | Whisper-big-v3 хорошо, но не идеально |
| Стили субтитров | DIY через ASS template | Готовые шаблоны SubtitleService |
| B-roll auto-подбор | Нет | SubtitleService умеет |

**Когда что выбрать:**
- **TTS-with-timestamps**: AI-narration pipeline где TTS-текст — известный input. Шортсы, буктрейлеры, объяснялки.
- **Whisper + SubMagic**: пост-обработка уже существующего видео (interview, podcast cut, podcast-shorts) где исходный текст недоступен.

### Грабли

- `Accept: application/json` обязательно — иначе вернётся `audio/mpeg` без timestamps
- `alignment` поле опускается если `enable_logging=false` или для очень коротких текстов
- Per-char timings включают пробелы/пунктуацию — фильтруй через `isspace()` при сборке слов
- ASS BGR (не RGB): `&H0000F0FF&` = жёлтый. `&HFFFFFFFF&` = белый. Используй конвертер `ass_color = "&H00" + "".join(reversed([rgb[i:i+2] for i in (4,2,0)]))`
