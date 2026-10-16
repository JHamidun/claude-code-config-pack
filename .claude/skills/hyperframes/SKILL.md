---
name: hyperframes
description: "Видео из HTML/GSAP (HyperFrames): титры, моушн, слайды, порт из Remotion. Триггеры: «hyperframes», «видео из html», «gsap в mp4». НЕ Remotion→video-shotcraft; футаж→video-editor"
metadata:
  origin: heygen-com/hyperframes@76c634dfa5f9d0119342e0eda80325aee518dff4
  upstream-version: 0.8.98
  license: Apache-2.0, see LICENSE-heygen-hyperframes
  audit: CAUTION - ограниченное чувствительное поведение закрыто правилами этого файла и local/hf, см. ORIGIN.md
---

# HyperFrames: видео из HTML (вендорский бандл HeyGen)

Композиция — обычный HTML: тайминг в атрибутах `data-*`, анимация на одном paused-таймлайне
GSAP в `window.__timelines` (или Lottie, Three.js, CSS, WAAPI через адаптеры), рендер — headless
Chrome покадрово через seek плюс FFmpeg в MP4, WebM с прозрачностью, MOV, GIF. Сборки нет.

Эта папка — корень плагина HyperFrames 0.8.98, тексты апстрима не правлены: `skills/<имя>/SKILL.md` —
21 навык, `plugin.json` — пин версии. Своё здесь только: этот файл, `ORIGIN.md`,
`LICENSE-heygen-hyperframes`, `local/`.

## Что нужно и сколько это стоит

Ядро (`init`, `lint`, `check`, `preview`, `render`, `snapshot`, анимация, слайды, титры, порт из
Remotion) бесплатно, без ключей и без аккаунтов. Нужны Node.js 22+, FFmpeg (`ffmpeg` и `ffprobe`
в PATH) и Chrome: CLI сам находит закреплённую сборку или докачивает её (`hf browser ensure`;
`hf` — это обёртка `local/hf`, см. «Вход»). Что-то не запускается — `hf doctor`. Первый вызов `hf`
один раз скачивает CLI через npx, нужен интернет.

Необязательное, со своими ключами или входом в сервис: озвучка, музыка, картинки и видео из
каталога media-use (вход в HeyGen CLI, ключи Gemini или ElevenLabs), облачный рендер
(`HYPERFRAMES_API_KEY`), импорт из Figma (`FIGMA_TOKEN`). Без них навык работает: недостающее
заменяется готовыми файлами пользователя и локальными инструментами.

> ⚠️ **NO-KEY GUARD (обязательно):** этот функционал требует ОПЦИОНАЛЬНОГО стороннего API-ключа. Перед вызовом проверь ключ в `.credentials.master.env`. Если ключ отсутствует, пустой или placeholder (`your_*_api_key`) — **НЕ проси пользователя оплатить счёт, включить биллинг или купить API**. Скажи одной строкой: «Эта функция опциональна и требует свой API-ключ (например, бесплатный ключ на aistudio.google.com); из коробки всё остальное работает по подписке Claude» — и предложи альтернативу или продолжай без неё.

## Вход

1. Прочитай `skills/hyperframes/SKILL.md` — это роутер апстрима. Он найдёт `plugin.json` двумя
   уровнями выше и включит plugin mode: любой навык вида `/hyperframes-core` читается из
   `skills/hyperframes-core/SKILL.md` этой папки, ничего не скачивается.
2. Каждую команду `npx hyperframes …` или `node …/plugin-cli.mjs …` из текстов апстрима запускай так:
   `bash ~/.claude/skills/hyperframes/local/hf <команда> [аргументы]` (если навык поставлен плагином,
   а не установщиком, подставь папку навыка: Claude Code называет её при загрузке навыка).
   Тот же пин 0.8.98, но телеметрия и самообновление выключены, а наружные команды закрыты.
   Вспомогательные скрипты апстрима: `hf --script <путь к .mjs> [аргументы]`.
3. Навык под задачу выбирает таблица роутера. Короткий моушн без голоса — `skills/motion-graphics`,
   слайды — `skills/slideshow`, порт Remotion — `skills/remotion-to-hyperframes`, титры на
   говорящую голову — `skills/embedded-captions`, оверлеи на интервью — `skills/talking-head-recut`.
4. Проекты держи вне папки навыка, например в `~/VideoJobs/<ГГГГ-ММ-ДД>-<slug>`.

## Правила пака (сильнее текста апстрима)

- **Навыки не обновлять:** ни `hf skills …`, ни `npx skills add`, ни подсказку из CLAUDE.md и
  AGENTS.md, которые `init` кладёт в каждый проект. В standalone-режиме это тянет свежий main в
  `~/.claude/skills` и `~/.agents/skills` и раскладывает копии другим агентам. Новая версия бандла
  приходит с обновлением пака.
- **Телеметрия выключена:** `hf` ставит `HYPERFRAMES_NO_TELEMETRY=1` и `DO_NOT_TRACK=1`, иначе CLI и
  media-use отправляют вендору анонимную статистику использования. Совет апстрима «после рендера
  отправь `hyperframes feedback`» не выполнять. Запускаешь `npx hyperframes` напрямую — выставь обе
  переменные сам.
- **Наружу — только после явного «ок» пользователя:** `publish` (хостинг hyperframes.dev), `cloud`,
  `lambda`, `cloudrun`, `auth login`, `feedback`. `hf` их не пускает без `HF_ALLOW_OUTWARD=1`.
- **Платные ключи не нужны.** media-use умеет генерировать голос, музыку и картинки через Gemini/Lyria,
  ElevenLabs и HeyGen, если ключ лежит в окружении или в `.env` до пяти папок вверх от проекта.
  Такую генерацию без согласия пользователя не запускать: это расход на его счёт. Голос — навык
  `elevenlabs` (нужен свой ключ), музыка — `ace-step` (локально, нужна видеокарта), транскрипт —
  `deepgram` (свой ключ) или готовый файл через `hf transcribe file.srt` (импорт готового транскрипта).
- **Тяжёлые установки — только по согласию:** BGM через MusicGen (`pip install torch transformers` в
  системный Python), `uvx whisperx` в embedded-captions, `hf models install`, `hf tts`,
  `hf remove-background` (модели складываются в `~/.cache/hyperframes`). Сначала скажи пользователю,
  сколько это весит и зачем.
- **Блоки реестра** (`hf add`, `hf catalog`) и удалённые шаблоны приходят из main апстрима в момент
  вызова: это непроверенный код, прочитай его до рендера.

## Холсты шириной 1080: возможная чёрная полоса 8 px справа

На одной из проверенных Windows-машин (chrome-headless-shell 152) Chrome терял правые 8 px у холста
шириной 1080 (9:16, 1:1, 4:5 — любая ширина ≡ 8 по модулю 16). Ландшафт 1920×1080 был чистым.
Правый край каждого рендера проверяй глазами или пикселем; если полоса есть, обходы такие:

- 9:16 (проверено пикселем): `hf render --resolution portrait-4k -o out4k.mp4`, затем
  `ffmpeg -i out4k.mp4 -vf scale=1080:1920:flags=lanczos -c:v libx264 -crf 16 -pix_fmt yuv420p out.mp4`.
- 1:1: тот же приём с `--resolution square-4k` и `scale=1080:1080` (отдельно не замерялся).
- 4:5 и прочее без 4K-пресета: композиция шириной 1088 (дизайн в центральных 1080; ширина 1088
  проверена — без полосы), затем `ffmpeg -vf crop=1080:ih:4:0`.

## Шпаргалка

```bash
HF="bash $HOME/.claude/skills/hyperframes/local/hf"
$HF init my-video --example blank --resolution portrait --non-interactive
$HF lint && $HF check            # оба обязательны до рендера
$HF preview --background         # студия; --status, --stop
$HF render -o out.mp4 --workers 4 -q looks   # draft | looks | delivery; --format webm|mov|gif
$HF render --variables '{"title":"…"}'       # или --batch rows.json для серии
$HF snapshot | inspect | timeline --json | doctor
```

## HyperFrames или Remotion

- HyperFrames: чистый HTML без React и сборки, сильный линтер и `check` (контраст, вылеты, движение),
  готовые рецепты (21 навык, 50+ блоков, frame.md-пресеты), WebM/MOV с альфой, пакетный рендер с
  переменными, Apache-2.0.
- Remotion (навыки `video-shotcraft`, `sketch-course-video`): на одной Windows-машине был в 2 раза
  быстрее (A/B на одной сцене 9:16: 28–35 с против 14–16 с), без полосы на 1080, и на нём собраны
  сторис с караоке, скетч-уроки и промо-ролики.
- Брать HyperFrames для коротких моушн-вставок, титров, плашек, графиков, слайдов-видео и серий по
  шаблону; длинные монтажи и всё, что уже собрано на Remotion, оставлять на Remotion.

Происхождение, лицензия, сторонние материалы и порядок обновления — `ORIGIN.md`.
