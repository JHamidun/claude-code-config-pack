# Windows-specific gotchas для AI-видео пайплайна

## §1 — subprocess encoding (CRITICAL)

Bез `encoding='utf-8', errors='replace'` — cp1251 краш на UnicodeDecodeError при чтении ffmpeg stderr с любыми non-ASCII символами:

```python
import subprocess

result = subprocess.run(
    ['ffmpeg', '-i', 'in.mp4', 'out.mp4'],
    capture_output=True,
    text=True,
    encoding='utf-8',     # MANDATORY на Windows
    errors='replace',     # не падать на edge cases
)
print(result.stderr)
```

Это **первая** правка которую забывают. Симптом: "UnicodeDecodeError: 'charmap' codec can't decode byte".

## §2 — PYTHONIOENCODING=utf-8 для print()

Без этого `print('Готово')` raises `UnicodeEncodeError` в Windows console.

```bash
# В .env проекта:
PYTHONIOENCODING=utf-8

# Или per-script:
set PYTHONIOENCODING=utf-8 && python script.py
```

Или в начале скрипта:

```python
import sys
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
```

### Combining-диакритика рушит print даже после reconfigure

`print()` строки с **combining acute U+0301** (ударение, напр. `што́рма`) падает на cp1251 даже когда обычная кириллица проходит — combining-кодпоинт не мапится. Реальный баг: `gen_vo_fix.py` сгенерил `vo_01`, затем `print(f"… {текст_с_ударением} …")` уронил скрипт `UnicodeEncodeError` → `vo_11` не дорегенерился.

Фикс — НЕ интерполируй строку с диакритикой в `print`, используй numeric format:

```python
print("regenerated vo_%02d" % n)        # OK — без самого текста
# НЕ: print(f"regenerated: {text}")      # text='…што́рма…' → crash
```

(Сам combining-знак в TTS-вводе — норм и нужен, см. `audio.md` §3; проблема только в выводе на консоль.)

## §3 — ffmpeg drawtext + кириллица = крах (workaround через PIL)

ffmpeg `drawtext` с кириллицей на Windows падает из-за font cache + filter parser encoding mismatch. Симптомы: пустой текст, или "Failed to parse expression", или странные глифы.

**Workaround: рендерить text как transparent PNG через PIL и overlay'ить:**

```python
from PIL import Image, ImageDraw, ImageFont

img = Image.new('RGBA', (1080, 1920), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)
font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 48)  # absolute path mandatory
draw.text((100, 100), 'Your Channel Name', fill=(255, 255, 255), font=font)
img.save('overlay.png')
```

Затем:

```bash
ffmpeg -i video.mp4 -i overlay.png -filter_complex \
  "[0:v][1:v]overlay=0:0:enable='between(t,0,3)'" \
  -c:a copy out.mp4
```

## §4 — PIL ImageFont absolute path

Relative paths fail на Windows. Всегда абсолют:

```python
font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 48)        # OK
font = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 48)      # Segoe UI
font = ImageFont.truetype('C:/Windows/Fonts/calibri.ttf', 48)      # Calibri
```

НЕ `'arial.ttf'` — fails если cwd не Fonts dir.

## §5 — Playwright MCP clipboard

Для browser-automation paste (Runway, etc.):

```javascript
// В browser_evaluate:
await navigator.clipboard.writeText(text);   // CORRECT
```

**НЕ** `document.execCommand('copy')` — deprecated, не работает в современной Runway UI и большинстве SaaS-приложений.

## §6 — ASCII-only paths для Yandex Disk / Runway / ffmpeg

Cyrillic в paths = silent failures across pipeline.

| Bad | Good |
|---|---|
| `${HOME}/видео Анимация/` | `${HOME}/video-animation/` |
| `terra ролик финал.mp4` | `terra-final.mp4` |
| `Не одобренные варианты генерации/` | `_rejected_variants/` |

Кириллица OK в display names (frontmatter, заголовки в UI), но НЕ в file paths которые пойдут через ffmpeg, Yandex API, Runway upload.

Симптомы: Yandex "Done!" но папка не создана, ffmpeg `No such file or directory`, Runway upload 0-byte.

## §7 — Yandex Disk multipart upload bug

Multipart create produces 0-byte file (size:0, text/plain) при 201 OK. **НЕ** `files={...}`. Raw PUT:

```python
import requests

# Step 1: получить upload_url
h = {'Authorization': f'OAuth {os.getenv("YANDEX_DISK_TOKEN")}'}
resp = requests.get(
    'https://cloud-api.yandex.net/v1/disk/resources/upload',
    params={'path': '/terra-final/final.mp4', 'overwrite': 'true'},
    headers=h,
)
upload_url = resp.json()['href']

# Step 2: raw PUT (НЕ files=)
with open('final.mp4', 'rb') as f:
    requests.put(upload_url, data=f.read(), timeout=600)

# Step 3: verify (всегда)
verify = requests.get(
    'https://cloud-api.yandex.net/v1/disk/resources',
    params={'path': '/terra-final/final.mp4', 'fields': 'size,mime_type'},
    headers=h,
).json()
assert verify['size'] > 0, f'Empty upload! {verify}'
```

## §8 — Backslash vs forward-slash в Python paths

На Windows используй forward-slash в Python strings — backslash требует escaping и ломает f-strings:

```python
path = '${HOME}/.claude/skills/video-pipeline'   # OK
path = '${HOME}\\.claude\\skills\\video-pipeline'  # OK но громоздко
path = '${HOME}\.claude'  # SyntaxWarning, fails иногда
```

Dля os calls Python принимает оба, для ffmpeg в shell оба работают.

## §9 — Long path support

Windows historically cap 260 char paths. Включи long path support если работаешь с глубокими структурами:

```
Win+R → regedit →
HKLM\SYSTEM\CurrentControlSet\Control\FileSystem\LongPathsEnabled = 1
```

Или в скриптах используй prefix `\\?\${HOME}\...` (но ломает совместимость с ffmpeg).

## §10b — zoompan d=N ЗАМОРАЖИВАЕТ видео (КРИТИЧНО для punch-in на клипах)

`zoompan=...:d=N` на ВИДЕОвходе держит ПЕРВЫЙ входной кадр N раз → клип = статичное ФОТО с
зумом. Заказчик ловит сразу («оживлённые фото вместо видео»). `d` = выходных кадров на КАЖДЫЙ
входной кадр. Для движущегося зума на ВИДЕО (сохранить нативное движение Veo/Seedance):

```bash
# ВЕРНО — d=1 + зум по 'on' (глобальный счётчик выходных кадров)
zoompan=z='min(1.0+0.0012*on,1.14)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30
# НЕВЕРНО — d=125 = заморозка первого кадра
```

`crop` с `t` в width/height НЕ спасает (crop размеры считаются один раз при init, только x/y
per-frame). Скорость зума нормировать под длину клипа: `rate = travel / (dur*fps)`.

## §11 — субтитры вылезают за экран (ASS WrapStyle + кегль)

`WrapStyle 2` (без переноса) + фикс. кегль → длинные RU-слова уезжают за 1080px. Динамический
кегль на строку: `fontsize = clamp(SAFE_W/(len(text)*0.60), 48, base)`, SAFE_W = W−2·margin;
+ `WrapStyle 0` как страховка-перенос. Реализовано в `video-editor/scripts/karaoke_captions.py`.

## §12 — Транскрипция RU: Deepgram Nova-3 > WhisperX для детекта повторов

WhisperX СХЛОПЫВАЕТ повторы (двойное «Далее я бы предлож… Далее я бы предложил» → одно слово
в транскрипте) → дубль остаётся в звуке, проверка по транскрипту врёт. Deepgram Nova-3 пишет
как слышит. Гоча Deepgram: на полном длинном файле дропает первые ~15с (VAD) → чанки по 30с +
ретрай на 408. `DEEPGRAM_API_KEY` в creds. Детали → `video-editor/references/talking-head-broll-reel.md`.

## §13 — ffmpeg `volumedetect` ничего не печатает (замер громкости)

При замере уровня (музыка-vs-голос, проверка микса) `volumedetect` пишет итог `mean_volume:` /
`max_volume:` на уровне **INFO** в stderr. Грабли:

- **`-v error` СКРЫВАЕТ итог** → парсер получает пусто. Используй `-hide_banner -nostats` (дефолтный info), НЕ `-v error`.
- **Очень короткие окна (<~1с)** часто дают `n_samples: 0` → ничего. Бери окно ≥1с.
- **`-ss` ставь ПОСЛЕ `-i`** (точный seek по декодированному потоку); `-ss` до `-i` бывает капризным.

```python
subprocess.run(["ffmpeg","-hide_banner","-nostats","-i",v,"-ss",str(t),"-t","1.0",
                "-af","volumedetect","-f","null","-"], capture_output=True, text=True,
               encoding="utf-8", errors="replace")  # парсить mean_volume из .stderr
```

Готовый замер баланса: `video-editor/scripts/talking-head/audio_balance_check.py`.

## §10 — VSCode terminal не Git Bash для Python

Если запускаешь Python с кириллицей в args — используй PowerShell или cmd, **не** Git Bash. MSYS path mangling конвертит `/start` → `C:/Program Files/Git/start` и ломает аргументы.

Для Telethon-тестов: чистый Python, не tg_client.py из Bash. (См. memory `feedback_msys_path_mangling`.)
