# Higgsfield Supercomputer — устройство и работа через API (заметки от 2026-06-07)

Работа идёт через сессию своей учётной записи на платном тарифе. CLI `hf.exe` v0.1.40, авторизован.
Токены — в `~/.claude/.credentials.master.env` → `HIGGSFIELD_ACCESS_TOKEN` (hf_…) + `HIGGSFIELD_REFRESH_TOKEN`.

## 1. Архитектура

Supercomputer — оркестратор поверх нескольких LLM (модель выбирается в настройках чата). Он подключает
**employees** (суб-агентов), каждый привязан к своему **flow-skill**; те дёргают бэкенд генерации **jobs**
(тот же, который оборачивает публичный CLI), складывают результаты в **folders** (Files/Memory) и умеют
подтверждение перед запуском (approval gate) и задачи по расписанию.

```
user msg → claudesfield orchestrator (Claude/Gemini/GPT/Grok)
        → loads EMPLOYEE (sub-agent) + its flow-skill
        → prompt-enhancement (short RU → rich EN prompt)
        → picks job_set_type + params
        → [approval gate if "Ask before generation"]
        → POST job to fnf.higgsfield.ai/jobs  (server-side)
        → poll /jobs/{id}/status → /assets/{id}/detail
        → store to folder, stream to UI via SSE
```

### Хосты и эндпоинты

| Host | Purpose |
|---|---|
| `fnf.higgsfield.ai/claudesfield/chats` | create chat |
| `…/claudesfield/chats/{id}/messages` | **send msg** — body `{text, message_id, parent_message_id}` (scriptable) |
| `…/claudesfield/chats/{id}/config` | set orchestrator model / employee / approval |
| `…/claudesfield/models` | orchestrator LLM list (see §2) |
| `…/claudesfield/attachments?chat_id=` | chat media |
| `notification.higgsfield.ai/chats/{id}/stream` | **SSE agent stream** (auth = Clerk bearer; EventSource w/o header fails) |
| `notification.higgsfield.ai/chats/{id}/resume` | resume stream |
| `fnf.higgsfield.ai/jobs` (POST) / `/jobs/{id}` / `/jobs/{id}/status` | **generation backend** (create→poll). Same as CLI `hf generate create`. |
| `fnf.higgsfield.ai/assets/{id}/detail` | final asset record (urls + params) |
| `fnf.higgsfield.ai/folders?surface=claudesfield` | Files / Memory (folder per chat) |
| `fnf-higgsclaw-cron.higgsfield.ai/api/v1/jobs?chat_id=` | **Scheduled tasks** (cron runtime, "higgsclaw") |
| `fnf.higgsfield.ai/job-sets/costs` | per-model credit costs (see §4) |
| `fnf.higgsfield.ai/workspaces/wallet` | live credit balance |
| `skills-marketplace.higgsfield.ai/api/v1/{skills,ai-employees}/{builtin,personal}` | skills/employees catalog (builtin = public; personal = Clerk auth) |
| `clerk.higgsfield.ai/v1/client/sessions/{sid}/tokens` | auth (Clerk JWT, like Suno) |
| `mcp.higgsfield.ai/mcp` | MCP connector |

### Пример записи задания (`GET /jobs/{id}`)

```json
{"job_set_type":"nano_banana_flash","params":{"width":1024,"height":1024,"aspect_ratio":"1:1",
 "resolution":"1k","batch_size":1,"medias":[],"reference_elements":[]},"status":"completed",
 "results":{"raw":{"type":"image","url":"https://d8j0ntlcm91z4.cloudfront.net/user_.../hf_...png"}},
 "folder_ids":["…"]}
```
Грабли: подпись в интерфейсе «Nano Banana Pro» соответствует job_set_type `nano_banana_flash`. Результат
отдаётся с cloudfront `d8j0ntlcm91z4.cloudfront.net`.

## 2. Модели оркестратора (`/claudesfield/models`) — выбираются в настройках чата

`google/gemini-orchestrator` (default) · **anthropic/claude-opus-4.8** · claude-opus-4.6 · claude-sonnet-4.6 ·
gemini-3-flash · gemini-3.5-flash · gemini-3.1-pro · openai/gpt-5.5-pro · openai/gpt-5.5 · x-ai/grok-4.3.

## 3. Встроенный каталог (skills-marketplace, публичная часть)

**21 skills:** popular-web-designs, landing-page-flow, video-adapt, soul-id, **montage**, pdf, excalidraw,
trend-picker, organic-marketing, powerpoint, maps, create-skill, youtube-research, youtube-content,
audio-generation, songwriting-and-ai-music (Suno), infographic, product-analyzer, design-md,
creative-ideation, brand-analyzer.

**21 employees → flow-skill:** Cinematic Director→cinematic-flow, Unboxing/Tutorial/Try-On/Product/UGC
Creators→ugc-*-flow, Product Animator→productMD-flow, Typography Animator→typographyMD-flow, TV Ad
Director→tv-ad, Infographic Animator→infographicMD-flow, Product Photographer→product-photoshoot, Podcast
Producer→podcast-flow, Premium/Motion Designer→highMD-flow/classicMD-flow, Video Generator→video-generation,
Amazon Listing Designer→amazon-product-listing, Image Generator→image-generation, Cartoon
Animator→cartoon-flow, Text Generator→text-generation, AI Influencer→ai-influencer-flow, Personal
Clipper→personal-clipper-flow.

> Через API отдаются только **метаданные** скиллов (имя, описание, примеры). Тела скиллов и их скрипты
> работают на стороне сервиса, наружу не выдаются. Сохранённые метаданные — в `sc_skills_builtin.json` /
> `sc_employees_builtin.json`.

## 4. Стоимость в кредитах (`/job-sets/costs`; цифры зависят от тарифа учётной записи)

- seedance_2_0: 480p 3 / 720p **4.5** / 1080p 9 cr/sec; seedance_2_0_fast: 480p 1.5 / 720p 3.5 / 1080p 7.
- kling3_0: pro 1.5-2 / std 1.25-1.75 per sec. cinematic_studio_3_0 / marketing_studio_video: 720p 5 / 1080p 10.
- recraft_v4_1 image: 1k 1.25 / 2k 8 cr. (our 7×5s 720p Seedance reel ≈ 157 cr).

## 5. Как посмотреть, с какими параметрами уходит задание

1. Карточки шагов в интерфейсе показывают: какой employee подключился, какой получился enhanced prompt,
   какие выбраны `job_set_type` и params.
2. Настройка «Ask before generation» ставит подтверждение перед запуском — параметры видно до старта.
3. Точные параметры выполненного задания и ссылку на результат отдаёт `GET /jobs/{id}`. У многошаговых
   сотрудников так же видно каждое звено цепочки.
4. Отправка сообщений и чтение потока скриптуются с Clerk-токеном: `POST …/chats/{id}/messages` и
   SSE `notification.higgsfield.ai/chats/{id}/stream`.

## 6. Карта соответствий с нашим стеком

| Higgsfield | Our equivalent |
|---|---|
| Orchestrator (pluggable LLM) | our main loop + `orchestrator` agent / Task subagents |
| Employees (sub-agents + flow-skill) | `agents/` + `~/.claude/skills/*` |
| Skills (montage, audio, maps, pdf, powerpoint…) | we already have most: video-editor montage toolkit, elevenlabs/suno, maps-places, pdf, pptx, youtube-transcript… |
| jobs generation backend | `hf.exe generate create <jst>` ИЛИ напрямую `fnf.higgsfield.ai/jobs` + наши Veo/Seedance/Runway |
| Files/Memory (folders) | `~/.claude/projects/.../memory/` + scratchpad |
| Scheduled tasks (higgsclaw cron) | `/schedule` + CronCreate |
| Connectors (Slack/Drive/Notion/Gmail/Figma+30) | our MCP servers + skills |
| prompt-enhancement step | a reusable enhancer skill/sub-step |
| approval gate | our permission modes / AskUserQuestion |
| Virality Predictor (brain_activity) | `hf generate create brain_activity --video` |

## 7. Как ведёт себя Cinematic Director (cinematic-flow)

Перед генерацией сотрудник предлагает **Soul anchoring** — «создать персонажа и локацию в Soul, чтобы кадр
держался стабильно» → варианты [персонаж + локация / только персонаж / только локация / из текста /
пропустить]. Стабильность кадров у «кинематографического» сотрудника держится на связке **Soul Character +
Soul Location → раскадровка и кейфреймы → видео Seedance**. Оркестратор ведёт диалог ветвлением (один вопрос
на фазу), prompt-enhancement отрабатывает всегда (короткий русский промпт → развёрнутый английский).
Наш аналог: flow-skill, который при необходимости делает `hf soul-id create` и дальше цепляет keyframe→video.

**Шаги в режиме Auto Run:** `Enhanced prompt` → `cinematic-dramaturg` (промежуточный этап, пишет драматургию
сцены; в публичном каталоге из 21 скилла его нет) → `Painting the frame` (кейфрейм через Nano) → задание на
видео Seedance. То есть flow-skill складывается из нескольких этапов, часть которых в каталоге не значится.
Каждый шаг генерации = создание задания на `fnf.higgsfield.ai/jobs` с job_set_type и params.

## 7b. Песочница выполнения и шаблон промпта

**На каждый чат поднимается своя bash-песочница.** В интерфейсе видны карточки «Running terminal / Command / Input»:
```
$ mkdir -p output && curl -sL -o output/final.mp4 "https://d8j0ntlcm91z4.cloudfront.net/user_.../hf_...mp4"
# cwd: /home/user/{chat_id}
```
→ Песочница — Linux-окружение с рабочим каталогом по chat_id (`/home/user/{chat_id}/`): туда `curl`-ом
скачиваются результаты заданий, там же выполняется shell (в том числе **ffmpeg** для скилла `montage`).
По устройству это LLM + bash-песочница + jobs-API как инструменты + скиллы как инструкции — форма, знакомая
по Claude Code и Agent SDK. Команды терминала показываются в интерфейсе, так что ход выполнения виден по шагам.

**Шаблон кинематографического промпта** — то, что выдаёт этап `cinematic-dramaturg`. Структуру можно
переиспользовать у себя:
```
Narrative Summary: <1-sentence story/arc>
Scene Setup: <environment, props, lighting, weather; camera placement = distance + height + lens (e.g. "40mm, 10ft behind, 2ft above, low eye-line")>
Dynamic Description: <multi-shot. each shot = lens (24/35/40/75mm) + camera move (low tracking MS / high-angle wide / tight CU) + subject action + SPEED in km/h; transitions written as "Hard Cut to <lens>, <angle>"; "Cut on the pulse">
Acting: <micro-pauses before reactions, precise eye-line, wet living eyes with catch-lights, visible breath/chest rise>
Audio: <layered sound design: ambient + foley + mechanical + room tone>
Negatives: No subtitles. No text overlay. No captions. No title cards. No watermarks.
```
Что подставляется по умолчанию: конкретные фокусные расстояния, дистанция и высота камеры, скорости движения
в км/ч, список планов с жёсткими склейками, атмосферные детали (лужи, неоновое свечение, дымка ~20 м), блики
в глазах. → перенести в наш prompt-engineering в `video-generation`.

## 7c. Конвейер сборки ролика в скилле `montage`

Задача на монтаж, шаги терминала в `/home/user/{chat_id}/`:

1. `Viewing skill montage / Searching files: *.(mp3|wav|ogg)` → `$ find . -name "*.mp3" -o -name "*.wav"`
2. **Аудио не нашлось → фоновая дорожка синтезируется средствами самого ffmpeg (lavfi)**, без обращения
   к внешнему сервису:
   ```bash
   ffmpeg -f lavfi -i "sine=frequency=65:duration=5" \
     -filter_complex "apulsator=hz=4,tremolo=f=4:d=0.8,lowpass=f=150,volume=3" -y bgm.mp3
   # richer harmonic bass bed:
   ffmpeg -f lavfi -i "sine=frequency=55:duration=5" \
     -i "aevalsrc=0.5*sin(2*PI*110*t)+0.25*sin(2*PI*220*t)+0.12*sin(2*PI*330*t):d=5" \
     -filter_complex "[0:a]apulsator=hz=4,lowpass=f=120,volume=2[sub]; ... amix ..." bgm.mp3
   ```
3. Probe: `ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate -of csv=s=x:p=0 output/final.mp4` → `960x960x24/1` (Seedance 1:1 output = 960×960@24fps).
4. Font: `find /usr/share/fonts -name "*.ttf"` → uses `/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf`.
5. **Итоговая сборка (рефрейм 9:16 + вжигание субтитров + фоновая дорожка):**
   ```bash
   ffmpeg -i output/final.mp4 -i bgm.mp3 -filter_complex \
   "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=luma_radius=20:luma_power=3[bg]; \
    [0:v]scale=1080:1080[fg]; \
    [bg][fg]overlay=(W-w)/2:(H-h)/2,drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='НЕОНОВЫЙ КОТ':fontcolor=cyan:fontsize=90:borderw=10:bordercolor=magenta:x=(w-text_w)/2:y=1550[v]; \
    [0:a][1:a]amix=inputs=2:weights=1.0 0.4[a]" \
   -map "[v]" -map "[a]" \
   -c:v libx264 -preset slow -crf 18 -profile:v high -level 4.1 -pix_fmt yuv420p \
   -c:a aac -b:a 192k -ar 44100 -movflags +faststart -y output/final_reels.mp4
   ```
   = blurred-bg reframe 960×960→1080×1920 (square fg centered over blurred fill) + drawtext subtitle (DejaVuSans-Bold,
   cyan, magenta 10px border, fontsize 90, y=1550) + `amix weights=1.0 0.4` (video audio + bgm) + x264 crf18/high/4.1 + aac192k + faststart.

**Что берём себе:** (а) процедурная фоновая дорожка через ffmpeg lavfi (sine + гармоники aevalsrc +
apulsator/tremolo/lowpass + amix) — музыкальная подложка без внешнего сервиса, добавить в montage-toolkit
нашего video-editor; (б) montage — это ровно ffmpeg-конвейер в bash-песочнице (то есть наш video-editor,
подтверждено); (в) рефрейм у них через оверлей на размытом фоне, субтитры вжигаются drawtext
DejaVuSans-Bold (у нас ASS-караоке — лучше). В песочнице ffmpeg 5.1.9 Debian, fontconfig/freetype включены.

## 8. Что через API не отдаётся

- Тела скиллов (SKILL.md) и системный промпт оркестратора живут на стороне сервиса: публичны только
  метаданные, остальное можно оценить лишь по наблюдаемому поведению.
- Часть настроек продукта в клиент приходит в закрытом виде — состав фич снаружи не разобрать.
- Многошаговые цепочки видно целиком только при реальном выполнении, а оно тратит кредиты: вход и ветвление
  зафиксированы, остальное достраивается по шагам.
- Задокументировано и пригодно к работе: модели и параметры, API заданий, стоимости, каталог сотрудников,
  общая схема работы.

## 9. Набор инструментов агента и окружение песочницы

У агента 15 наборов инструментов — это его рабочая поверхность:

- artifacts (artifact_get/put), ask_user_question, debugging (terminal, process, web_search, web_extract, extract_document),
- **delegation (delegate_task → порождает дочерних суб-агентов)**, higgsfield_assets (upload, attachments_list, balance),
- higgsfield_generate (generate_image, generate_video, models_explore, job_status), higgsfield_identity (element=char/loc/prop, soul_id),
- image_gen, memory, scheduling (schedule=cron), search (web_search),
- **skills (skills_list, skill_view, skill_manage=create/edit/delete)**, terminal (terminal, process), todo, web.

Манифест скилла (на примере `montage`): name, description, **allowed-tools: Bash, Read, Write, Edit, Glob, Grep,
AskUserQuestion** — набор в стиле Claude Code. Окружение песочницы: **gVisor** (ядро 4.19.0-gvisor), 5 ГБ в /home,
Python 3.11.2, ffmpeg 5.1.9.

Ограничение: `skill_view` отдаёт только метаданные скилла, без тела — это штатное поведение, а не сбой.
Ориентироваться в таких случаях приходится на наблюдаемые шаги выполнения (см. §5 и `flow-playbooks.md`).

→ На наш стек эти 15 наборов ложатся так: delegation→Task/agents, skills→skills, memory→memory/,
scheduling→/schedule, higgsfield_*→скилл higgsfield, terminal→Bash, web→WebFetch/firecrawl.
