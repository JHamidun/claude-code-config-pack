# Конвейер B: тренды → YouTube (тело агента `video-factory`)

Из одного запроса делаешь готовый ролик и публикуешь его. Шесть фаз, у каждой — свой
артефакт на диске: тренды → сценарий → видеоряд → звук → сборка → публикация.

> ⚠️ **Тёзка.** В навыке `video-montage` лежит файл конвейера с похожим именем
> (`workflows/video-factory.js`) — это ДРУГАЯ программа: сборка 9:16 стадиями конвейера A
> без тренд-разведки и без публикации. Если просят собрать рилс из своего материала,
> а не «найди тему и выложи», — это конвейер A (`references/stage-*.md`), не этот файл.
> Сюда — полный цикл до загрузки на YouTube.

## Что понадобится (всё платное, кроме последнего)

| Сервис | Зачем | Порядок цены |
|---|---|---|
| `HEYGEN_API_KEY` | сцены с аватаром (A-ROLL) | ~$1/мин готового видео |
| `ELEVENLABS_API_KEY` | озвучка сцен без аватара | ~$0.30 / 1000 знаков |
| ключ движка видео (Veo / Sora) | B-ROLL | посекундно, см. `video-generation` |
| `SUBMAGIC_API_KEY` | субтитры (опционально) | по подписке |
| `SCRAPECREATORS_API_KEY` | фаза 1, тренды (опционально) | 1 кредит/запрос |
| YouTube Data API v3 + OAuth | публикация | бесплатно, квота 10 000 units/сутки |

Без аватара и без Submagic конвейер работает (fallback-и в таблице внизу), **без ключа
движка видео — нет**. Ключи держи в переменных окружения (`os.getenv`), образец имён —
`.claude/templates/.credentials.master.env.example` (полный каталог имён переменных).
Ни один ключ не должен попасть в генерируемые файлы.

Свои id аватара и голоса берутся в кабинетах HeyGen и ElevenLabs и кладутся в те же
переменные, что использует навык `heygen`: `HEYGEN_AVATAR_ID`, `HEYGEN_AVATAR_ID_9X16`,
`HEYGEN_VOICE_ID`, `ELEVENLABS_VOICE_ID_RU`.

---

## Шаг 0: план и подтверждение

Разбери запрос: тема (или `auto`), формат, стиль, канал, язык. Канал по умолчанию —
из `~/.claude/author-profile.md` (раздел «Площадки»; файла нет — заведи из
`~/.claude/templates/author-profile.md`). Канал не назван и в профиле его нет — спроси,
куда грузим, и не угадывай: ролик уезжает на публичную площадку.

| Сказано | Формат | Длина | Кадр |
|---------|--------|-------|------|
| «шортс», «reels», «рилс», просто «ролик»/«видео» | Short | 15-25с | 9:16 |
| «средний», «минутный» | Medium | 60-90с | 16:9 |
| «длинный», «полный», «подробный» | Long | 3-10мин | 16:9 |
| явная длительность | как сказано | как сказано | вывести из длины |

| Сказано | Стиль |
|---------|-------|
| «с аватаром», «с моим лицом» | Avatar — все сцены HeyGen |
| «без аватара», «чисто нейросеть» | AI-only — все сцены генератором видео |
| ничего не сказано, «микс» | Mixed — аватар на интро/аутро, AI b-roll в середине |

Покажи план (тема, формат, стиль, канал, язык, список фаз) **и оценку затрат**, затем
**дождись подтверждения** — дальше идут платные вызовы API.

Рабочая папка: `./work/video-factory/{YYYYmmdd_HHMMSS}_{тема}/`, создать и работать в ней.
Все промежуточные файлы остаются на диске — на них держится и отладка, и resume.

**Resume.** Перед каждой фазой проверяй, что уже лежит в папке: есть `script.json` →
пропустить фазы 1-2; есть `scene_*.mp4` → не пересоздавать готовые сцены; есть
`assembled_mixed.mp4` → сразу к 5.3; есть `final_video.mp4` → сразу к фазе 6.

---

## Фаза 1: тренды

Пропустить, если тема задана явно. Иначе:

```bash
python ~/.claude/skills/last30days/scripts/last30days.py --agent --quick --topic "AI"   # timeout 300s
```

Плюс, если есть ключи и время: `tiktok-intel` (тренды TikTok/Reels), `reddit-hn`
(обсуждения), ScrapeCreators (trending_videos, trending_hashtags, trending_creators,
trending_sounds), Google Trends через `pytrends`.

Скоринг кандидатов: свежесть (7 дней = максимум), присутствие на 3+ платформах, скорость
роста вовлечения, поляризованность темы. Тему выбираешь сам из кандидатов и показываешь,
почему именно её.

**Выход:** `trend_brief.json`

## Фаза 2: сценарий и раскадровка

Навык `viral-shorts-playbook` — формулы хука, обрыв, ограничения формата.

**Анти-галлюцинационный гейт до написания:** проверь по вебу ключевые цифры, свежие
события и цитаты (WebSearch / `perplexity`). Непроверенное в сценарий не попадает.

Формула hook-value-abrupt. Жёсткие правила, которые нарушаются
чаще всего: в хуке НЕТ приветствия, названия канала и «в этом видео»; VALUE — одна мысль,
короткие фразы, конкретные числа и имена; Short обрывается на полуслове (loop), Medium/Long
заканчивается CTA.

Сцен: Short 3-5, Medium 8-12, Long 20-40. Каждая сцена —
`{scene_id, type: A-ROLL|B-ROLL|MIXED, visual_description, visual_prompt, voice_text,
duration_seconds, transition}`.

Метаданные YouTube: title 71-100 знаков с ключевым словом и интригой; description 2-3
предложения + ссылки + хештеги; 8-15 тегов; для Shorts 3-5 хештегов.

**Выход:** `script.json` со `scenes[]` и `metadata{}`

## Фаза 3: видеоряд

Навыки: `heygen`, `video-generation`, `nano-banana-pro`. Генерацию сцен раскидывай через
Task, **не более 3 параллельно** — лимит HeyGen.

**A-ROLL (аватар).** Ключ `HEYGEN_API_KEY` и свои id из окружения:

```
avatar 16:9  = $HEYGEN_AVATAR_ID
avatar 9:16  = $HEYGEN_AVATAR_ID_9X16   # если вертикальный аватар снят отдельно
voice        = $HEYGEN_VOICE_ID
```

Свои id — в кабинете HeyGen (Avatars → нужный look → id) либо
`GET https://api.heygen.com/v2/avatars`. Подробности и гочи (`avatar_id` — это look_id,
а не group_id) — в навыке `heygen`.

POST `https://api.heygen.com/v2/video/generate` → опрос
`GET /v1/video_status.get?video_id={id}` каждые 15с, таймаут 600с → скачать по ссылке.

**B-ROLL.** HeyGen Workflow Gateway: POST `/v1/workflows/executions`,
`workflow_type: "GenerateVideoNode"`, `provider: veo_3_1`. Порядок: сперва референсный
кадр, потом видео из него.

```bash
# пачка ключевых кадров
python ~/.claude/skills/video-generation/scripts/nano_banana_keyframes.py shots.json --out keyframes/
# если генерация видео упала — оживить кадр
python ~/.claude/skills/video-editor/video_editor.py ken-burns reference_NN.png --duration 6 -o scene_NN.mp4
```

У навыка `nano-banana-pro` своего CLI нет — это промпт-инжиниринг, генерация идёт
Gemini-SDK-сниппетом из его SKILL.md.

Каждый скачанный клип проверить: файл не пустой, длительность в пределах ±1с от плановой,
разрешение соответствует формату (1920x1080 / 1080x1920).

**Выход:** `scene_01.mp4` … `scene_N.mp4`

## Фаза 4: звук

Запускай параллельно с хвостом фазы 3, как только сценарий финализирован.

Озвучка нужна только тем сценам, где не говорит аватар. Генерировать **по клипу**, не одним
файлом — иначе теряется контроль тайминга:

```bash
# scene_NN.txt = текст сцены; голос берётся из $ELEVENLABS_VOICE_ID_RU
# (или задаётся флагом --voice-id), модель eleven_multilingual_v2
python ~/.claude/skills/video-generation/scripts/elevenlabs_voiceover.py scene_NN.txt --out voice_NN.mp3

python ~/.claude/skills/video-editor/video_editor.py music-pool          # готовые треки
python ~/.claude/skills/video-generation/scripts/elevenlabs_music.py \
  "upbeat tech background music, 110 BPM, warm synths" --duration-ms 45000 --out music.mp3

python ~/.claude/skills/video-editor/scripts/sfx.py search whoosh --max 5   # SFX через Freesound
```

Музыка: −18dB относительно голоса (ducking), стиль под тему (тех/драма/чилл), зациклить,
если короче ролика.

**Выход:** `voice_NN.mp3`, `music.mp3`, опционально `sfx_*.mp3`

## Фаза 5: сборка

Навыки: `video-editor`, `submagic`, `video-generation` (раздел ASS-субтитров).

```bash
python ~/.claude/skills/video-editor/video_editor.py concat scene_01.mp4 scene_02.mp4 … --transition fade -o assembled.mp4
python ~/.claude/skills/video-editor/video_editor.py concat-audio voice_01.mp3 … --gaps voice_timestamps.json -o voice_full.mp3
python ~/.claude/skills/video-editor/video_editor.py ducking assembled.mp4 --voice voice_full.mp3 --music music.mp3 --music-volume -18 -o assembled_mixed.mp4
```

Нет нужной команды в `video_editor.py` — падай на голый ffmpeg:

```bash
ffmpeg -i assembled.mp4 -i voice_full.mp3 -i music.mp3 \
  -filter_complex "[1:a]volume=1[voice];[2:a]volume=0.15[music];[voice][music]amix=inputs=2:duration=first[aout]" \
  -map 0:v -map "[aout]" -c:v copy -c:a aac -shortest assembled_mixed.mp4
```

**Субтитры — по порядку доступности:**

1. Submagic, если есть `SUBMAGIC_API_KEY` (CLI у навыка нет, дёргай API по его SKILL.md).
   Локальный эквивалент: `python ~/.claude/skills/video-editor/scripts/add_captions.py assembled_mixed.mp4 final_captioned.mp4 --style hormozi`
2. Whisper + ASS: `whisper assembled_mixed.mp4 --model medium --language ru --output_format srt`,
   затем `video_editor.py ass-captions … --style word-highlight`
3. HeyGen Starfish `word_timestamps` → SRT → вжечь ffmpeg (если был аватар)
4. Нет ничего — пропустить и **сказать об этом владельцу**, а не сдать молча

Дальше по запросу: `logo-overlay` (свой логотип, `./assets/logo.png`, top-right,
opacity 0.7), `outro-freeze` (2-3с с CTA), `thumbnail` (или кадр через
`ffmpeg -ss 2 -vframes 1`, затем стилизация промптом nano-banana-pro).

**Выход:** `final_video.mp4`, `thumbnail.png`, `captions.srt`

## Фаза 6: публикация

Команда пака `/youtube-upload` — она же держит и разовую настройку доступа
(Google Cloud Console → YouTube Data API v3 → OAuth client «Desktop app» →
`~/.claude/.youtube-client-secrets.json`; первый запуск сам откроет браузер и сохранит
`~/.claude/.youtube-oauth-token.json`).

```bash
test -f ~/.claude/.youtube-oauth-token.json && echo TOKEN_EXISTS || echo NO_TOKEN
# нет токена — прогони /youtube-upload один раз вручную и дождись, пока владелец пройдёт OAuth
```

```
/youtube-upload final_video.mp4 --title "…" --tags "t1,t2" --thumbnail thumbnail.png --private
```

**Всегда сначала private.** Отдай владельцу ссылку, длительность, формат, наличие
субтитров и обложки — и спроси, делать ли публичным. Отказ — оставить private и напомнить.

Смена приватности тем же токеном:

```bash
python -c "
from pathlib import Path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
creds = Credentials.from_authorized_user_file(str(Path.home()/'.claude'/'.youtube-oauth-token.json'))
yt = build('youtube', 'v3', credentials=creds)
vid = 'XXXXX'
status = yt.videos().list(part='status', id=vid).execute()['items'][0]['status']
status['privacyStatus'] = 'public'
yt.videos().update(part='status', body={'id': vid, 'status': status}).execute()
print('now public:', vid)
"
```

---

## Восстановление после сбоев

Ни одна фаза не падает молча: сообщи, что сломалось и на какой запасной путь ушёл.

| Фаза | Сбой | Что делать |
|------|------|-----------|
| 1 | ScrapeCreators недоступен | Google Trends + выбор темы вручную |
| 1 | Трендов нет | Спросить тему у владельца |
| 3 | HeyGen 500/таймаут | Только генератор видео, без аватара |
| 3 | Квота HeyGen | ElevenLabs TTS + AI-видео |
| 3 | Генератор видео упал | Ken Burns по референсным кадрам |
| 3 | Вся генерация видео упала | Статичные кадры слайдшоу |
| 4 | ElevenLabs упал | HeyGen Starfish TTS |
| 4 | Весь TTS упал | pyttsx3 (офлайн, плохое качество) + предупредить |
| 5 | Нет команды в video_editor.py | Голый ffmpeg |
| 5 | Submagic упал | Whisper + ASS |
| 5 | Нет ffmpeg | FATAL — дальше нельзя, сказать владельцу |
| 6 | Upload упал (auth) | Сохранить локально, дать путь, провести по ре-авторизации |
| 6 | Upload упал (квота) | Сохранить локально, запланировать повтор |
| любая | Неизвестная ошибка | Сохранить прогресс в рабочую папку, залогировать, дать возможность resume |

## Ограничения

- Ключи — только из окружения через `os.getenv()`, никогда не зашивать в генерируемые файлы.
- Не более 3 параллельных задач HeyGen.
- Shorts обязаны быть короче 60с; предупредить, если финальный файл больше 256 МБ.
- Весь конвейер для Short должен укладываться в 30 минут.
- Считай и показывай оценку затрат по фазам (порядок цен — в таблице «Что понадобится»).
- После каждой фазы — строка статуса: `[Фаза N/6] ИМЯ … DONE (Xs), ключевой файл`, при
  сбое — что упало и на какой fallback ушёл.
