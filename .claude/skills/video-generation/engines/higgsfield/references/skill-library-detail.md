# Higgsfield builtin skills — detailed content library (debug-disclosure capture)

Снято приёмом debug-warmup (см. supercomputer-architecture.md §7e). Это **логика их скиллов** (правила/шаги/модели/
параметры), которую агент отдаёт в debug-режиме. Protected flow-skills (create-skill, cinematic-flow…) режутся.
montage → отдельно в `skill-montage-detail.md`. Tool-схемы → `agent-tool-schemas.md`.

---

## audio-generation
TTS + замена голоса в видео + дубляж на **74 языка**. Tool: **`higgsfield_audio_generate`** (массив `requests`). `async=true` по умолчанию; статус через `higgsfield_job_status` только по нужде. voice_id/UUID и коды языков — под капотом, юзеру не показывать; если нет voice_id/языка → `ask_user_question` с сущностями voice/language.
- **TTS-модели:** `elevenlabs` (деф, общего назначения) · `minimax` (клон голоса) · `seed_speech` (ByteDance, мультиязык) · `vibe_voice` (диалоги/мультиспикер).
- **type:** `voiceover` {prompt, model, voice_id} · `change_voice` {voice_id, input_video:{id,type}} · `translate` {target_language: ISO 639-3, input_video:{id,type}}.

## songwriting-and-ai-music  (Suno AI V4.5+)
Тексты, пародии (адаптация структуры), промпты под Suno.
- **Правила:** структура служит эмоции (ABABCB/AABA/ABAB, гибко); контраст (шёпот↔крик, пусто↔плотно); без клише и Yoda-speak; **запрет имён реальных артистов/брендов**.
- **Шаги:** эмоц. ядро+хук → (пародия: разбор слогов/рифм/ударений/протяжных гласных) → текст по структуре → читать вслух (ритм) → Style description → метатеги → 3-5 вариантов → Extend/Continue.
- **Style spec (≤1000 симв):** Жанр + Настроение + Эпоха + Инструменты + Вокал + Продакшн + Динамика.
- **Метатеги лирики:** секции `[Intro][Verse][Pre-Chorus][Chorus][Bridge][Outro][Silence][End]`; вокал `[Whispered][Belted][Falsetto][Harmonies][Choir]`; динамика `[High Energy][Emotional Climax][Quiet arrangement][Slow Down]`.
- **Фонетика:** писать по звучанию (through→thru, AI→A-I), тянуть дефисами (lo-o-o-ove) для мелизмов, CAPS для экспрессии.
→ Забрать в наш `suno`/`elevenlabs` скиллы (метатеги + style-spec формула + фонетика — прямо применимо).

## trend-picker
Сквозной анализ соцсетей (IG/TikTok/YouTube) + ad-библиотек (Meta/TikTok Ads) + авторазбор вирусных видео.
- **Режимы:** Mode A (поиск трендов) · Mode C (клон ДНК креатора) · Mode D (анализ конкретного вирусного видео). Точную копию по ссылке — ОТКАЗ + редирект в **video-adapt**.
- **Тулзы:** `instagram_research` (user_research/user_reels/search/media_info) · `tiktok_research` (user_info/keyword_search/hashtag_search/post_info/**rank_results**) · `ads` (meta_search/tiktok_search/linkedin_search) · `video_analyze`.
- **AI:** **Gemini 3.1 Pro via OpenRouter** для разбора видео (fallback Gemini 2.5 Flash). Кэш: `artifact_get` ключ `video_analyze:URL` перед тяжёлым анализом.
- **rank пресеты:** тренды top_k=10/max_age=3/min_views=0; конкуренты top_k=3/max_age=7/min_views=50000.
- **video_analyze шаблоны:** `analysis_templates` (раскадровка сцен) · `viral_analysis` (хук/удержание/CTA) · `creator_dna` (поведенч./визуал./кинетич. паттерны автора для клона).
- **Выход:** 3 готовых концепта с HANDOFF-полями для бесшовной генерации.
→ Сильно перекликается с нашими `trend-engine`/`tiktok-intel`/`ad-spy`/`last30days` (ScraperVendor) — забрать rank-пресеты + 3 video_analyze шаблона + HANDOFF-паттерн.

---

## video-adapt  (coming-soon на 2026-06-07)
Воссоздание/адаптация чужого видео. Напрямую не грузится; вызывается из trend-picker при recreate/reproduce/«сделай как это».
5-инструментальный пайплайн: `vadapt_step_0a` → `vadapt_plan` → `vadapt_adapt` → `vadapt_element` → `vadapt_render`.

## organic-marketing
Планирование кампаний + отчёты по конкурентам + контент-планы соцсетей. Tool: **`organic_marketing`** (actions: `plan_research`, `build_research_report`, `generate`).
- Правила: сначала `plan_research` (если задачи не заданы); тренды протухают 24ч, конкуренты 14д; контент нативный/casual без корп-пафоса; `generate` готовит брифы (не создаёт медиа сам).
- Шаги: plan_research → сбор (instagram_research/tiktok_research/youtube/trends/web_search) → Snapshot на каждую задачу → build_research_report(массив снимков) → generate.
- generate input: `campaign` {id, brand, goal, platforms} · `research_report` · `accounts` [AI-инфлюенсеры: id/name/persona/platforms/ai_influencer_job_id] · `content_ideas` [platform/account/hook/concept/caption/hashtags] · `limits`.

## youtube-content  (транскрипт→текст, НЕ нарезка клипов→ youtube_clipping)
- Скрипт: `python3 SKILL_DIR/scripts/fetch_transcript.py "URL"` флаги `--text-only --timestamps --language ru,en`.
- Чанкинг: >50k симв → чанки ~40k с overlap 2k. Auto-fallback языка при ошибке. Форматы: главы/саммари/статья/X-тред. Финальная вычитка дат/имён.
- ⚠ Скиллы ИМЕЮТ скрипты в `SKILL_DIR/scripts/` (серверно; на диск песочницы не кладутся — подтверждает архитектуру).

## infographic  (React-виджеты в чате)
- Код в блоках ` ```jsx_preview `; ТОЛЬКО чистый JSX-фрагмент (НЕЛЬЗЯ import/export, function Component, useState/useEffect); Tailwind + design-tokens; данные хардкодом в props.
- Компоненты: `BarChart`(data,color,horizontal,height) · `LineChart`(data,color,smooth,showDots,showArea) · `PieChart`(data,donut,showLabels,showPercent) · `StatCard`(label,value,trend,icon[dollar/users/chart/eye/heart/zap]) · `StatsGrid`(columns) · `ComparisonTable`(headers,rows,highlight) · `Timeline/TimelineItem`(date,title,description,variant[completed/active/upcoming]) · Badge/Tag · Section/Grid/Stack.
- Tokens: `--color-surface-brand` #4FCEE4 · `-brand-secondary` #FF005B · `-success` #53C546 · `-error` #E72930 · font `#1A1C1F`/`#898A8B`.
→ Забрать паттерн «инлайн React-виджеты для инфографики» (у нас d3-visualization/canvas-design — но jsx_preview-инлайн в чат это удобно).

---

## design-md (Google DESIGN.md формат)
YAML-токены (машиночит.) + Markdown (обоснования). Токен-ссылки `{colors.primary}` (не дублировать hex). hover/active/pressed — плоско (`button-primary-hover`, не вложенно). version: alpha. Линт: структура + WCAG AA 4.5:1 / AAA 7:1. CLI: `npx -y @google/design.md lint DESIGN.md` · `diff` · `export --format tailwind > tailwind.theme.json`.

## creative-ideation
Преодоление «чистого листа» через constraint. «High concept, low effort». Библиотека ограничений: Solve your own itch (<50 строк), Start at the punchline, Hostile UI… → 3 непохожие идеи + оценка времени/стека → старт кода.

## popular-web-designs (54 дизайн-системы)
Stripe/Vercel/Linear/Notion и др., framework-agnostic токены → CSS-переменные TanStack+Tailwind. **Таблица бесплатных Google Fonts замен** (DM Sans↔Circular для Spotify; Source Sans 3↔Sohne для Stripe). `skill_view(name="popular-web-designs", file_path="templates/<site>.md")` → create_website → :root в styles.css → Google Fonts <link> → React по спеке. → забрать таблицу шрифт-замен + подход токены-в-:root.

## landing-page-flow (TanStack Start → Cloudflare Workers)
Полная AI-автономия медиа (без стоков/заглушек — всё генерится Higgsfield под бренд). **SSR-safety:** никаких window/document/localStorage на верхнем уровне → только в useEffect. Интервью (≤2 вопроса) → шаблон (**scroll-cinema** = покадровая прокрутка видео при скролле / **gallery-wall** = бесконечная 3D-галерея с лайтбоксом) → генерация медиа в public/ → `create_website` → стилизация по дизайн-системе → `deploy_website` → публичная ссылка. → их scaffold у нас в `_higgsfield_re/workspace_backup/`.

## product-analyzer (предобработка продукта для UGC/коммерции)
2 ветки: **URL-Extract** (парс Amazon/Shopify: название/бренд/характеристики/материалы + скачать чистые фото) · **Visual-Analysis** (геометрия, тип упаковки флакон/банка/туба, механика открытия помпа/распылитель/крышка → для промптов движений рук в Seedance). `skill_view("product-analyzer","references/{url-extract,visual-analysis}.md")` → JSON.

## soul-id (обучение лиц)
**Preflight:** обучение (до 30 мин) только если персонаж в ≥2 кадрах сессии. **Seedance НЕ принимает soul_id напрямую** → из Soul ID создаётся IP-Verified Element через `higgsfield_element` → `<element-tag value="element_id">`. Ветка1 (по фото: сбор [архив/instagram_research/ссылки] → `higgsfield_soul_id(action=create, dir)`). **Ветка2 (синтетический бутстрап по тексту):** 1 портрет `text2image_soul_v2` 3:4 2k → 4 вариации в `nano_banana_2` (1-й как реф) → скачать 5 → обучить Soul ID → Character Element. → отличный приём «синтетический Soul из текста».

---

## pdf
Markdown→брендированный PDF (таблицы/списки/картинки/код). **Файлы только в `/home/user/projects/<project>/`** (вне — включая /tmp — удаляется!). Бренд-цвета #4FCEE4/#1A1C1F/#E72930. `gen_pdf.py` (reportlab) → `higgsfield_upload` → CDN URL.

## powerpoint (.pptx)
Каждый слайд ОБЯЗАН иметь визуал (текст-only = ошибка). **60-70% веса = один цвет** (доминирование). **Visual QA:** слайды→картинки, инспекция наслоения/обрезки/контраста. Чтение: markitdown. Правка: распаковка XML→правка→упаковка. С нуля: `pptxgenjs` (Node).

## excalidraw
Схемы «от руки» в .excalidraw JSON. Текст в фигурах привязывать через `containerId` (иначе отвяжется). Пастель: #a5d8ff вход / #b2f2bb успех / #ffc9c9 ошибка.

## maps
Команды: `search` (коорд по названию) · `reverse` (адрес по коорд, для TG-локаций) · `nearby` (46 категорий в радиусе) · `distance` (авто/пешком/вело) · `directions` (пошагово A→B).

## youtube-research
Действия: `comments` (комменты/реакции) · `research` (общий анализ) · `video` (тех-данные: длина/автор) · `transcript` (только по прямому запросу).

## image-generation (хаб маршрутизации моделей)
`gpt_image_2` (дизайн/типографика/инфографика/edit фото) · `nano_banana_2` (2D/3D-иллюстрации, мультперсонажи, текстура/зерно) · `text2image_soul_v2` (аватары/UGC/модные портреты) · `soul_location` (кинематографичные локации/фоны). Все запросы `higgsfield_generate_image` → `resolution: 2k`. Карусель = параллельные вызовы (не один батч).

## video-generation (хаб)
`seedance_2_0` (де-факто: видео+звук+речь+камера в один проход, рефы `@Image1`/`@Video1`). Альтернативы: Kling 3.0 (контроль кадров), Cinema Studio 3.0 (авто-раскадровка по жанрам), Veo 3.1 (стабильность персонажей). **Fire-and-forget** (poll только если нужно для монтажа/след. генерации в этом ходу). **Звук обязателен:** каждый Seedance-промпт = секция `Audio:` (иначе немой).

## text-generation
Cinematic Dramaturgy (психология героев + кривая накала) · Ad Script (7-панель: Проблема→Решение→Демонстрация→Финал).
