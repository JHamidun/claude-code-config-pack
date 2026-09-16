# AI Models & Services — ЕДИНЫЙ КАНОН

> Канон моделей: Claude Code (подписка Max), image/медиа, внешние API.
> Обновлён 2026-09-06 (сверка с живой таблицей моделей и страницей снятий на platform.claude.com).
> Используй ТОЛЬКО эти model ID — они проверены.

---

## Claude Code — подписка Max (актуальные алиасы)

С подпиской Claude Code Max доступны ВСЕ модели без ограничений. Аутентификация — подписка, не API.

| Алиас | Model ID | Название | Роль |
|-------|----------|----------|------|
| `model: "fable"` | `claude-fable-5-1` | Claude Fable 5.1 | **Дефолт ВСЕХ text-субагентов**; вышла 01.09.2026 |
| `model: "opus"` | `claude-opus-5` | Claude Opus 5 | Оркестратор / основная сессия |
| `model: "sonnet"` | `claude-sonnet-5` | Claude Sonnet 5 | Доступен, но для text-субагентов НЕ дефолт |
| `model: "haiku"` | `claude-haiku-4-5-20251001` | Claude Haiku 4.5 | Быстрые/простые операции, классификация |

> **У современных моделей идентификатор БЕЗ даты — сам ID и есть закреплённый
> снапшот.** Датированные суффиксы остались только у Haiku 4.5.

> **Маршрутизация из доков Anthropic:** начинать с **Opus 5** для большинства
> нагрузок; **Fable 5.1** — «for demanding reasoning and long-horizon agentic
> work, or when your evals on Claude Opus 5 at higher effort still fall short».

> **Обновлено 06.09.2026.** Было `claude-fable-5` — она помечена **Legacy** с
> выходом Fable 5.1 (01.09.2026). Сверено с живой таблицей
> `platform.claude.com/docs/en/about-claude/models/overview`; домен
> `docs.claude.com` теперь редиректит туда.
>
> **Маршрутизация из доков Anthropic:** начинать с **Opus 5** для большинства
> нагрузок; **Fable 5.1** — «for demanding reasoning and long-horizon agentic
> work, or when your evals on Claude Opus 5 at higher effort still fall short».
>
> **Обновлено 06.09.2026.** Было `claude-fable-5` — она помечена **Legacy** с
> выходом Fable 5.1 (01.09.2026). Сверено с
> `platform.claude.com/docs/en/about-claude/models/overview` (домен
> `docs.claude.com` теперь редиректит туда). Ранее здесь стояли
> `claude-opus-4-8` и `claude-sonnet-4-5-20250929` — тоже устарели.
>
> **Урок дороже самой правки.** Таблица отставала на недели, и этого никто не
> замечал, потому что алиас `opus` продолжал работать. Устаревший идентификатор
> не падает — он молча отдаёт вчерашнюю модель. Поэтому в остальных файлах пиши
> **алиас** (`opus`/`fable`/`haiku`), а точные ID держи только здесь и сверяй
> раз в месяц с тем, что реально отвечает.

### Правило субагентов

- Дефолт text-воркеров — **Fable 5.1** (`model: "fable"`). Промптить намерениями
  (цель, а не пошагово): Opus — оркестратор, Fable — воркеры в изолированном контексте.
- Fable упал на лимите → подхватить **Opus** (resume + смена model).
- Старые дефолты «sonnet для субагентов / haiku для поиска» — это фолбэк-логика
  выбора УРОВНЯ, а не движка; рантайм-дефолт text-воркеров остаётся Fable.

**Про число одновременных.** Здесь до 06.09.2026 стояло «≤5 одновременно» — это
была эвристика против rate-limit, и она противоречила `rules/delegation.md`, где
записано обратное. **Решение владельца (не требование доков): числом не
ограничивать** — потолок и так стоит внутри одного Workflow (`min(16, ядер−2)`),
а масштаб набирается параллельными волнами. Обрыв роя почти всегда означает упор
в лимит подписки, и лечится он сменой подписки плюс `resumeFromRunId`.

⚠️ **Что доки говорят на самом деле — а говорят они про оба рычага.** Anthropic
называет и условия делегирования, и прямые численные ограничения
(`CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`, `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`,
SDK `max_budget_usd`). Так что «не число, а поводы» — это выбор владельца, а не
цитата; приписывать его докам нельзя.

Что в доках действительно есть: «Claude Opus 5 delegates more readily than earlier
models» и «**do not use subagents to verify or double-check your own work**».
То есть рой на широкую задачу — да; субагент, перечитывающий то, что сессия
только что написала сама, — нет. **Исполнитель и независимый проверяющий внутри
одного навыка — это НЕ тот случай**: там проверяется чужая работа, и такой
конвейер законен.

```python
# Fable 5.1 — дефолт text-субагентов
Task(subagent_type="general-purpose", model="fable", prompt="...")
# Haiku — быстрая модель для простых задач
Task(subagent_type="general-purpose", model="haiku", prompt="...")
# Opus — оркестратор / максимальная сложность
Task(subagent_type="general-purpose", model="opus", prompt="...")
```

### Legacy — живые, но старые (вызывать незачем, менять по правой колонке)

| Model ID | На что менять |
|----------|---------------|
| `claude-fable-5` | `claude-fable-5-1` |
| `claude-opus-4-8` · `claude-opus-4-7` · `claude-opus-4-6` · `claude-opus-4-5-20251101` | `claude-opus-5` |
| `claude-sonnet-4-6` · `claude-sonnet-4-5-20250929` | `claude-sonnet-5` |

### ⛔ СНЯТЫ — вызов вернёт ошибку

Проверено по `platform.claude.com/docs/en/about-claude/model-deprecations` 06.09.2026.
Раньше этот список стоял под заголовком «доступны через API» — неверно с февраля.

| Model ID | Снята |
|----------|-------|
| `claude-opus-4-1-20250805` | 05.08.2026 |
| `claude-opus-4-20250514` | 15.06.2026 |
| `claude-sonnet-4-20250514` | 15.06.2026 |
| `claude-3-7-sonnet-20250219` | 19.02.2026 |
| `claude-3-5-sonnet-20240620` · `claude-3-5-sonnet-20241022` | 28.10.2025 |
| `claude-3-5-haiku-20241022` | 19.02.2026 |
| `claude-3-haiku-20240307` | 20.04.2026 |
| `claude-3-opus-20240229` | 05.01.2026 |
| весь `claude-2.*`, `claude-instant-*` | 21.07.2025 и раньше |

---

## ⚠️ Из коробки — только подписка Claude (БЕСПЛАТНО для пользователя)

Свежая установка работает БЕЗ единого стороннего ключа: весь текст/код/reasoning — Opus по подписке Claude. Все таблицы внешних моделей ниже — ОПЦИОНАЛЬНЫЕ платные интеграции.

**Правило NO-KEY:** прежде чем вызывать любой внешний API (Gemini, OpenAI, ElevenLabs…) — проверь ключ в `.credentials.master.env`. Ключ отсутствует/пустой/placeholder (`your_*_api_key`) → НЕ вызывай API и НЕ проси пользователя оплатить или включить биллинг. Ответь: «Эта функция опциональна, нужен свой API-ключ» + как получить (для Gemini: aistudio.google.com, есть бесплатный tier) — и предложи альтернативу.

## Контекст использования

**Claude Code работает на Opus 5 через подписку** (не по API).
Opus закрывает текстовые, кодовые и reasoning задачи внутри Claude Code; text-субагенты — Fable 5.1.

Внешние модели по API нужны в двух случаях:
1. **В Claude Code** — только для того, что Opus не может (медиа, поиск, embeddings)
2. **В автономных ботах/агентах** — для любых задач, т.к. они работают вне Claude Code

### Модели для использования в Claude Code (только то, что Opus не может)

| Задача | Модель | Провайдер |
|--------|--------|-----------|
| **Генерация картинок** | Лестница: `gemini-3.1-flash-image-preview` (NB2 Flash — дёшево, дефолт) → `gemini-3-pro-image-preview` (NB Pro — подороже) → `gpt-image-2.5-sunburst` (**лучшее**). Обложки news — `gemini-3.1-flash-lite-image` | Google / OpenAI |
| **Генерация видео** | `veo-3.1-generate-preview` (Google) **или Seedance 2.5** (ByteDance, через Runway). ⚠️ У OpenAI видео больше нет: `sora-2*` и `/v1/videos` гаснут 24.09.2026 | Google / Runway |
| **Видео с аватаром** | HeyGen API (skill `heygen`) | HeyGen |
| **TTS / озвучка** | `eleven_multilingual_v2` или `tts-1-hd` | ElevenLabs / OpenAI |
| **Транскрипция** | `gpt-transcribe` или Deepgram API (⚠️ `whisper-1` снимается 26.02.2027) | OpenAI / Deepgram |
| **Deep Research** | `gpt-5.6-sol` или `deep-research-pro-preview-12-2025` — ⚠️ `o3-deep-research` ВЫКЛЮЧЕНА 23.07.2026 | OpenAI / Google |
| **Online search** | `sonar` (Perplexity) — но WebFetch/WebSearch часто достаточно | Perplexity |
| **Embeddings** | `text-embedding-3-large` или `gemini-embedding-001` | OpenAI / Google |

**НЕ вызывай внешние API для:** текста, кода, reasoning, ревью, рефакторинга — Opus/Fable через подписку делают это сами.

---

## Image-модели — лестница трёх ступеней

**Решение владельца 09.09.2026, дословно:** «дешёвый вариант это Нано Банана 2
Флеш, есть подороже Нано Банана Про, и есть лучший — вот этот GPT Image 2.5».

До этого канон был устроен иначе и это стоит отметить, чтобы не откатили назад:
верхней ступенью считалась Nano Banana Pro, а OpenAI стоял сбоку как «для
особых случаев». Теперь ступеней три, и выбор идёт **по цене задачи**, а не по
вендору.

| Ступень | Model ID | Когда берём |
|---|---|---|
| 🥉 **Дешёвая — дефолт** | `gemini-3.1-flash-image-preview` (NB2 Flash) | Массовое, черновики, всё, где качество «достаточно». Быстро, 4K |
| ⤷ ещё дешевле | `gemini-3.1-flash-lite-image` (NB2 Lite) | ×2 дешевле и быстрее, качество держит. **Дефолт новостных обложек ваших новостных проектов** |
| 🥈 **Подороже** | `gemini-3-pro-image-preview` (NB Pro) | Когда Flash не вытянул: сложная сцена, мелкие детали |
| 🥇 **Лучшее** | `gpt-image-2.5-sunburst` | Флагман. Точность инструкции, текст на картинке, до 16 референсов, `input_fidelity`, прозрачный фон, `quality` до `max` |
| ⤷ он же быстрее | `gpt-image-2.5-flare` | **Та же цена и те же параметры**, ниже задержка. Не «дешёвый тир»: у 2.5 цена считается токенами, а не за картинку |
| прошлое поколение | `gpt-image-2-2026-04-21` | Живо, снятие не объявлено. ⚠️ `gpt-image-1.5` снимается 01.12.2026, `gpt-image-1` — 23.10.2026 |

**Ступень выбирается по цене ошибки, а не по вендору.** Обложка новости, которых
двадцать в день, — Lite. Картинка, которую увидит клиент, — Sunburst. Пачка,
где важна одна и та же личность на всех кадрах, — Sunburst с
`input_fidelity="high"`, потому что этого у Gemini просто нет.

Правила (полный список запретов — HIGH-канон в `rules/dont-do.md`, там же остаётся):

- **КЛЮЧ: `GOOGLE_API_KEY`** (НЕ GEMINI_API_KEY — конфликт SDK). Перед вызовом: `os.environ.pop('GEMINI_API_KEY', None)`.
- SDK: `from google import genai` + `types.GenerateContentConfig(response_modalities=['IMAGE', 'TEXT'])`. Старый SDK `google.generativeai` запрещён.
- Запрещённые image-модели (см. rules/dont-do.md): `gemini-2.0-flash-exp-image-generation`, `gemini-2.0-flash-exp`, `gemini-2.0-flash`, `gemini-2.5-flash-image` (NB1 устарела), `gemini-pro-vision`; `imagen-*` напрямую в Claude Code нельзя (в автономных ботах через Gemini SDK — ОК).
- Модель генерирует **JPEG, не PNG** — проверяй формат перед сохранением.

```python
from google import genai
from google.genai import types
import os

os.environ.pop('GEMINI_API_KEY', None)  # SDK conflict
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",   # Nano Banana 2 (default, fast, 4K)
    # model="gemini-3.1-flash-lite-image",    # NB2 Lite (×2 дешевле/быстрее; дефолт обложек ваших новостных проектов)
    # model="gemini-3-pro-image-preview",     # Nano Banana Pro (средняя ступень; верхняя — gpt-image-2.5-sunburst через OpenAI SDK)
    contents="Generate image: описание картинки...",
    config=types.GenerateContentConfig(response_modalities=['IMAGE', 'TEXT'])
)
# ВАЖНО: модель генерирует JPEG, не PNG!
with open("image.jpg", "wb") as f:
    f.write(response.candidates[0].content.parts[0].inline_data.data)
```

---

## Внешние модели (кратко)

| Модель | Когда |
|--------|-------|
| **`gpt-6-astra`** — ТОЛЬКО через Codex CLI (`codex exec`), не через gateway и не через MCP | Сильнейшая внешняя на 06.09.2026, по бенчмаркам выше Fable. Профиль: края и полнота списков — чего в перечислении не хватает, где паттерн шире/уже заявленного. Запуск и пять граблей (`&` убивает прогон; эффорт по умолчанию medium; вывод 0,5–0,9 МБ трассы; отказ лечится переформулировкой в защитный аудит) → skill `multi-model-gateway` |
| `gpt-5.6` (вкл. `-sol`/`-ultra` тиры через Codex CLI по подписке) | Актуальный флагман OpenAI: кросс-валидация, ревью вторым мнением. Гайд промптинга — memory `gpt56-prompting-guide`. С 10.08.2026 есть отдельный `gpt-5.6-cyber` под security-задачи |
| `gemini-3.1-pro-preview` | 2M контекст, multimodal. **Всё ещё старший Pro:** Gemini 3.5 Pro задерживается, релиза нет |
| **Gemini 3.7 Flash** — ⚠️ API-идентификатор НЕ ПОДТВЕРЖДЁН | Вышел 13.08.2026, заявлен как самый сильный «рабочий» для кода и агентных задач, вводная цена до 31.12.2026. Точный id перед использованием сверить с `ai.google.dev/gemini-api/docs/changelog` — не подставлять по догадке |
| `gpt-5.6-terra` | Математика, структурный reasoning. ⚠️ `o4-mini` снимается 23.10.2026, `o3-pro` — 11.12.2026 |
| Kimi K2 | Алгоритмы, глубокий reasoning |
| `deep-research-pro-preview-12-2025` / `gpt-5.6-sol` | Multi-step research с цитатами. ⚠️ `o3-deep-research` выключена 23.07.2026 |

Таблицы ниже (боты/агенты) сверены с докам OpenAI 09.09.2026.

---

## Модели для автономных ботов и агентов

Когда создаёшь ботов, агентов или автономные системы — выбирай модель по задаче:

> ⚠️ **Строки Anthropic в таблицах ниже приведены к актуальным ID 06.09.2026.**
> Прежние (`claude-opus-4-5-20251101`, `claude-sonnet-4-5-20250929`) — из API-снимка
> 30.01.2026; они продолжают отвечать, и в этом опасность: устаревший ID не даёт
> ошибки, он молча отдаёт вчерашнюю модель. Перед тем как вписать любой ID в бота,
> сверь его с `GET https://api.anthropic.com/v1/models` и с таблицей подписки Max
> в начале файла.
> Внутри самого пака (агенты, шаблоны, Task) полные ID не нужны вовсе — там алиасы
> `opus` / `fable` / `haiku`.

### Текст / Чат

| Уровень | Model ID | Провайдер | Env Var |
|---------|----------|-----------|---------|
| Лучший | `gpt-5.2` | OpenAI | OPENAI_API_KEY |
| Быстрый | `gpt-5-mini` | OpenAI | OPENAI_API_KEY |
| Дешёвый | `gpt-5-nano` | OpenAI | OPENAI_API_KEY |
| Лучший (Anthropic) | `claude-opus-5` | Anthropic | ANTHROPIC_API_KEY |
| Быстрый (Anthropic) | `claude-sonnet-5` | Anthropic | ANTHROPIC_API_KEY |
| Дешёвый (Anthropic) | `claude-haiku-4-5-20251001` | Anthropic | ANTHROPIC_API_KEY |
| Лучший (Google) | `gemini-3-pro-preview` | Google | GEMINI_API_KEY |
| Быстрый (Google) | `gemini-3-flash-preview` | Google | GEMINI_API_KEY |
| Альтернатива | `deepseek-chat` | DeepSeek | DEEPSEEK_API_KEY |

### Код (автономные агенты)

> ⚠️ Все четыре модели, что стояли здесь до 09.09.2026, **выключены**:
> `gpt-5.2-codex`, `gpt-5.1-codex-max` (обе 23.07.2026), `codex-mini-latest`
> (12.02.2026). Линейка `*-codex` в API закрыта целиком — её заменили обычные
> модели. Единственный живой `-codex` это `gpt-5.3-codex-spark`, и он
> research preview только для ChatGPT Pro, без доступа по API.

| Уровень | Model ID | Провайдер | Env Var |
|---------|----------|-----------|---------|
| Максимум | `gpt-6-astra` | OpenAI | OPENAI_API_KEY |
| Рабочий дефолт | `gpt-5.6-sol` (алиас `gpt-5.6`) | OpenAI | OPENAI_API_KEY |
| Быстрый | `gpt-5.6-terra` | OpenAI | OPENAI_API_KEY |
| Дешёвый | `gpt-5.6-luna` | OpenAI | OPENAI_API_KEY |

### Reasoning

> ⚠️ Вся o-серия свёрнута в GPT-5.6: `o3-deep-research` и `o4-mini-deep-research`
> выключены 23.07.2026; `o4-mini`, `o3-mini`, `o1*` снимаются 23.10.2026;
> `o3`, `o3-pro`, `gpt-5-*` — 11.12.2026. Замена по докам OpenAI — `gpt-5.6-sol`,
> а «pro»-режим теперь параметр: `reasoning.mode: pro`, а не отдельная модель.

| Уровень | Model ID | Провайдер | Env Var |
|---------|----------|-----------|---------|
| Максимум | `gpt-6-astra`, `reasoning.effort: max` | OpenAI | OPENAI_API_KEY |
| Глубокий | `gpt-5.6-sol` + `reasoning.mode: pro` | OpenAI | OPENAI_API_KEY |
| Быстрый | `gpt-5.6-terra` | OpenAI | OPENAI_API_KEY |
| Альтернатива | `deepseek-reasoner` | DeepSeek | DEEPSEEK_API_KEY |

**Эффорт у `gpt-6-astra`:** `low` · `medium` · `high` · `xhigh` · `max`.
Значения `none` он **не поддерживает** — если раньше стояло `none` или
`minimal`, доки велят начинать с `low`. Контекст 1 050 000, вывод до 128 000,
срез знаний 30.04.2026. Цена $10/$50 за миллион, кэш-чтение $1.

### Медиа / Специализированные

| Задача | Model ID | Провайдер | Env Var |
|--------|----------|-----------|---------|
| Картинки (OpenAI flagship) | `gpt-image-2.5-sunburst` | OpenAI | OPENAI_API_KEY |
| Картинки (OpenAI быстрый) | `gpt-image-2.5-flare` | OpenAI | OPENAI_API_KEY |
| Картинки (OpenAI прошлое поколение, живо) | `gpt-image-2-2026-04-21` | OpenAI | OPENAI_API_KEY |
| Картинки (Gemini default, NB2) | `gemini-3.1-flash-image-preview` | Google | GOOGLE_API_KEY |
| Картинки (NB2 Lite — обложки news/wealth) | `gemini-3.1-flash-lite-image` | Google | GOOGLE_API_KEY |
| Картинки (Gemini pro, NB Pro) | `gemini-3-pro-image-preview` | Google | GOOGLE_API_KEY |
| Картинки (Imagen) | `imagen-4.0-ultra-generate-001` | Google | GEMINI_API_KEY |
| Картинки (Imagen fast) | `imagen-4.0-fast-generate-001` | Google | GEMINI_API_KEY |
| Видео | **у OpenAI видео больше нет.** Живые пути: `veo-3.1-generate-preview` (Google) · Seedance 2.5 (Runway) — см. предупреждение ниже | Google / Runway | GOOGLE_API_KEY / RUNWAY_JWT |
| Видео (Google) | `veo-3.1-generate-preview` | Google | GEMINI_API_KEY |
| Видео (Google fast) | `veo-3.0-fast-generate-001` | Google | GEMINI_API_KEY |
| Видео аватары | HeyGen / D-ID API | HeyGen/D-ID | HEYGEN/DID_API_KEY |
| TTS | `tts-1-hd` | OpenAI | OPENAI_API_KEY |
| TTS (ElevenLabs) | `eleven_multilingual_v2` | ElevenLabs | ELEVENLABS_API_KEY |
| Транскрипция | `gpt-transcribe` (⚠️ `whisper-1` снимается 26.02.2027) | OpenAI | OPENAI_API_KEY |
| Realtime voice | `gpt-realtime-2.1` (⚠️ `gpt-realtime` снимается 20.01.2027) | OpenAI | OPENAI_API_KEY |
| Deep Research | `gpt-5.6-sol` — ⚠️ `o3-deep-research` ВЫКЛЮЧЕНА 23.07.2026 | OpenAI | OPENAI_API_KEY |
| Deep Research (Google) | `deep-research-pro-preview-12-2025` | Google | GEMINI_API_KEY |
| Online search | `sonar` | Perplexity | PERPLEXITY_API_KEY |
| Embeddings | `text-embedding-3-large` | OpenAI | OPENAI_API_KEY |
| Embeddings (Google) | `gemini-embedding-001` | Google | GEMINI_API_KEY |
| 1000+ моделей | Replicate | Replicate | REPLICATE_API_KEY |

> ## ⛔ У OpenAI больше нет видео
>
> **Videos API и все `sora-2*` выключаются 24.09.2026.** В таблице снятий
> OpenAI колонка «замена» у всех шести строк пустая — предлагать нечего,
> продукт закрыт целиком: `Videos API`, `sora-2`, `sora-2-pro`,
> `sora-2-2025-10-06`, `sora-2-2025-12-08`, `sora-2-pro-2025-10-06`.
>
> **Но «замены нет» — это про OpenAI, а не про нас.** Два живых пути:
>
> | Путь | Модель | Чем берёт |
> |---|---|---|
> | **Google, по API** | `veo-3.1-generate-preview` · `-fast-` · `-lite-` | Свой ключ, без подписки, кадр-в-видео, звук в кадре. Все три — **Preview, не GA**; дата снятия не объявлена |
> | **Runway, по подписке** | **Seedance 2.5** (ByteDance) | Мультикадр в одной генерации, до 30 с, до 50 референсов, звук, правка и продление готового видео |
>
> Разница по назначению, а не «что лучше»: Veo — отдельная сцена по ключу;
> Seedance 2.5 — целая сцена со сменой планов, ракурсов и темпа, которую иначе
> пришлось бы собирать монтажом из четырёх генераций.
>
> **Seedance 2.5 — спеки, снятые с help.runwayml.com 09.09.2026** (страницу
> отдаёт только браузер: на WebFetch она возвращает 403):
>
> | | |
> |---|---|
> | Вход | текст, картинка, видео, аудио |
> | Длительность | **4–30 с** либо Auto |
> | Разрешения | 480p · 720p · 1080p |
> | Кадр | Auto, 21:9, 16:9, 4:3, 1:1, 3:4, 9:16 · выход MP4/MOV |
> | Референсы | **до 50 за генерацию**: 30 картинок + 10 видео (по 30 с) + 10 аудио. В Keyframe первый и последний кадр идут ДОПОЛНИТЕЛЬНО к этим 50 |
> | Кредиты | 1080p — 68/с · 720p — 30/с · 480p — 20/с (входное видео добавляет половину этих ставок) |
> | Режимы | **Reference · Keyframe · Edit · Extend** |
> | План | на всех платных; на free — нет |
>
> ⚠️ **Две страницы Runway противоречат друг другу про разрешение:** таблица
> спеков в справке даёт 480p/720p/**1080p** и прайс за 1080p, а FAQ на
> продуктовой странице пишет «480p and 720p». Обе цитаты прочитаны дословно.
> Верить таблице спеков (там же и цена), но 1080p проверить первым же прогоном.
>
> **Три вещи, на которых легко ошибиться:**
> - **Extend возвращает ТОЛЬКО новый кусок.** Продлил 30-секундное видео на
>   5 секунд — получил клип на 5 секунд, а не на 35. Склейка отдельно.
> - **Таймкоды в промпте задают темп, а не точку монтажа.** Действие встанет
>   рядом с указанной секундой, не на ней. Кадровая точность — только в посте.
> - **Edit не даёт менять длину и пропорции** — берёт их у исходного видео.
>
> ⛔ **Прежний рецепт «Sora, когда на кадре кириллица» больше не выполним.**
> Veo кириллицу корёжит, и это не лечится сменой провайдера — текст класть
> **оверлеем на монтаже**, а у модели просить кадр без надписей.
>
> ⚠️ **Идентификатора Seedance 2.5 для API официальные страницы НЕ называют**
> — там только имена в интерфейсе. Поэтому `runway_client.py` его не
> угадывает, а спрашивает у `/v1/profile/features` и берёт свежайшую версию;
> константа `seedance_2_5` — только запасной вариант, и она не проверена.
>
> Точка входа — skill `video-generation`. Runway ходит по `RUNWAY_JWT`
> (живёт ~30 дней): срок проверяется `runway_client.py token-status` **без
> сети**, потому что протухший токен виден только как 401 и читается как
> «сломался Runway».

---

## Полный список доступных моделей (из API)

> Снимок от 30.01.2026 — до релизов Opus 4.6, Opus 4.8 и Fable 5; актуальные Claude-алиасы — в таблице подписки Max выше.

### OpenAI — сверено 09.09.2026 по `developers.openai.com/api/docs/deprecations`

> Прошлый снимок был от 30.01.2026 и перечислял как «доступные» восемь моделей,
> которые к сентябрю уже выключены. Держать список «что есть» бессмысленно — он
> протухает молча. Держим список **что УМЕРЛО и когда**, потому что именно он
> отвечает на вопрос «почему вызов упал».

**Живые и рекомендованные:**

```
gpt-6-astra                                  флагман, 1,05M контекст, effort до max
gpt-5.6-sol (алиас gpt-5.6), gpt-5.6-terra, gpt-5.6-luna
gpt-5.6-cyber
gpt-image-2.5-sunburst, gpt-image-2.5-flare  ← новое поколение картинок, 08.09.2026
gpt-image-2, gpt-image-2-2026-04-21          прошлое поколение, снятие не объявлено
gpt-realtime-2.1, gpt-realtime-2, gpt-transcribe
text-embedding-3-large
```

**⛔ УЖЕ ВЫКЛЮЧЕНЫ — вызов вернёт ошибку:**

| Когда | Что |
|---|---|
| 12.05.2026 | `dall-e-2`, `dall-e-3` |
| 23.07.2026 | `gpt-5-codex`, `gpt-5.1-codex`, `gpt-5.1-codex-max`, `gpt-5.1-codex-mini`, `gpt-5.2-codex`, `o3-deep-research`, `o4-mini-deep-research`, `computer-use-preview`, `gpt-5-chat-latest`, `gpt-5.1-chat-latest` |
| 10.08.2026 | `gpt-5.2-chat-latest`, `gpt-5.3-chat-latest` |
| 26.08.2026 | Assistants API целиком |
| 31.08.2026 | `gpt-5.4`, `gpt-5.4-mini` — **только в Codex**; по своему ключу API живут |
| 12.02.2026 | `codex-mini-latest` |

**⏳ СНИМАЮТСЯ — заменить заранее:**

| Дата | Что | На что |
|---|---|---|
| **24.09.2026** | `sora-2`, `sora-2-pro`, весь Videos API | замены нет, см. предупреждение выше |
| 23.10.2026 | `gpt-image-1`, `o4-mini`, `o3-mini`, `o1*`, `gpt-4.1-nano`, `gpt-4o-2024-05-13` | `gpt-image-2.5-*` / `gpt-5.6-terra` / `gpt-5.6-luna` |
| 30.11.2026 | Evals platform, Agent Builder, `v1/prompts` | — |
| 01.12.2026 | `gpt-image-1.5`, `gpt-image-1-mini`, `chatgpt-image-latest` | `gpt-image-2.5-sunburst` |
| 11.12.2026 | `gpt-5`, `gpt-5-mini`, `gpt-5-nano`, `gpt-5-pro`, `o3`, `o3-pro` | `gpt-5.6-sol` / `terra` / `luna` |
| 20.01.2027 | `gpt-realtime`, `gpt-audio`, `gpt-4o-*-realtime/audio` | `gpt-realtime-2.1` |
| 26.02.2027 | `whisper-1`, `gpt-4o-transcribe` | `gpt-transcribe` |

**Правило уведомления OpenAI:** обычные модели снимают минимум за 6 месяцев,
специализированные (`*-chat-latest`, `*-codex`, deep research) — за 3, preview —
могут за две недели. То есть за `-codex` и preview-моделями следить чаще.

### Anthropic (9 моделей в API-снимке)

```
claude-opus-4-5-20251101
claude-sonnet-4-5-20250929
claude-haiku-4-5-20251001
```

+ после снимка вышли: `claude-opus-4-6`, `claude-opus-4-8`, `claude-fable-5`, а затем
`claude-sonnet-5` (30.06), `claude-opus-5` (24.07) и `claude-fable-5-1` (01.09) — все по подписке Max.
Снятые из этого снимка удалены 06.09.2026, полный перечень — в разделе «⛔ СНЯТЫ» выше.

### Google Gemini (47 моделей) — ключевые

```
gemini-3.1-pro-preview, gemini-3-pro-image-preview, gemini-3.1-flash-image-preview, gemini-3.1-flash-lite-image, gemini-3-flash-preview
gemini-2.5-pro, gemini-2.5-flash, gemini-2.5-flash-image, gemini-2.5-flash-lite
gemini-2.0-flash, gemini-2.0-flash-lite
imagen-4.0-ultra-generate-001, imagen-4.0-generate-001, imagen-4.0-fast-generate-001
veo-3.1-generate-preview, veo-3.1-fast-generate-preview
veo-3.0-generate-001, veo-3.0-fast-generate-001
nano-banana-pro-preview
deep-research-pro-preview-12-2025
```

### DeepSeek (2 модели)

```
deepseek-chat
deepseek-reasoner
```

### Perplexity

```
sonar (Online search + answer)
```

---

## ЗАПРЕЩЕНО

> HIGH-канон запретов живёт в `rules/dont-do.md` (авто-load) — здесь дубль для полноты справочника.

- `gemini-pro-vision` — устаревшая, retired
- `imagen-*` — для генерации через Gemini SDK, не напрямую
- Старый SDK `google.generativeai` — используй `from google import genai`
- Сохранять jpg как .png — всегда проверяй формат
- Любые модели `gemini-1.0-*`, `gemini-1.5-*` — retired, вернут 404
- Image: `gemini-2.0-flash-exp-image-generation`, `gemini-2.0-flash-exp`, `gemini-2.0-flash`, `gemini-2.5-flash-image` (NB1 — есть NB2)

## API ключи

Все ключи: `~/.claude/.credentials.master.env`