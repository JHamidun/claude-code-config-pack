# CLAUDE — НАВИГАЦИЯ ПО КОНФИГУ

> Читай при каждом запуске. Это навигационный хаб: короткое ядро здесь, детали — в подключаемых файлах. `rules/` грузятся всегда; `config/` — по требованию (Read когда нужно).

## РЕЖИМ РАБОТЫ — АВТОНОМНЫЙ

- Proceed autonomously when the task is clear — no need to ask for permission first.
- NEVER suggest /compact, NEVER mention context size, NEVER pause to manage context. Auto-compact handles this automatically — just keep working.
- Keep working until the task is complete — no need to pause between steps.
- Go straight to execution — skip summarizing what you're about to do.
- NEVER ask "shall I do X?" or "start with Y?" — just do it. Show results, not plans.
- Единственная причина остановиться: нужна информация, которую может дать только пользователь (доступы, необратимые решения, неоднозначный выбор).
- **БЕСПЛАТНО ИЗ КОРОБКИ:** работает ТОЛЬКО подписка Claude (Max/Pro). Все сторонние API (Gemini, OpenAI, ElevenLabs и т.д.) — ОПЦИОНАЛЬНЫ и требуют личных ключей пользователя. Если ключа нет — НИКОГДА не проси оплатить/включить биллинг: сообщи, что фича опциональна, и предложи путь без неё.

## ИЕРАРХИЯ ИНСТРУКЦИЙ + SKILLS-FIRST

- **Приоритет при конфликте:** явная просьба пользователя → «РЕЖИМ РАБОТЫ» (этот блок) → `rules/` → дефолтное поведение. Пример: «NEVER suggest /compact» из этого блока сильнее любого справочника про управление контекстом.
- **Skills-first:** почти под любую задачу есть готовый skill — вызывай его через Skill tool ДО ad-hoc реализации. Карта: `rules/routing.md` (ходовые триггеры) → `config/routing-ext.md` (полная карта всех триггеров, Read по требованию).
- **Память применяй невидимо** (как собственный опыт, не «судя по памяти») — см. `rules/auto-learning.md`.
- **Тяжёлые локальные задачи** (векторизация, индексация, батч-обработка) запускай осознанно и под ресурс-гардом — никакого молчаливого фонового крона.

---

## ПРАВИЛА (`rules/` — авто-загрузка каждую сессию)

**Поведенческое ядро (грузится всегда):** `routing` (→ `config/routing-ext`) · `autonomous-mode` · `personality` · `dont-do` · `delegation` · `scaling` · `model-selection` · `models` (→ `config/models` канон) · `quality-gates` · `security` · `security-hardening` · `permissions` · `auto-learning` · `context7` · `user-profile`.

**Справочники (по требованию → `config/rules-ref/`):** `onboarding` · `plugins-catalog` · `hooks` · `headless-ci` · `prompt-caching` · `context-management` · `worktrees`.

Индекс всех правил с описаниями → `rules/README.md`.

---

## КОНФИГУРАЦИЯ (`config/`)

| Что | Файл |
|-----|------|
| **Реестр проектов** | `config/projects-registry.md` |
| **Полная карта роутинга (все триггеры)** | `config/routing-ext.md` |
| **MCP-серверы (полный реестр + «когда нужен»)** | `config/mcp-servers.md` |
| **Вынесенные справочники rules** | `config/rules-ref/` |
| API-ключи (единый источник) | `.credentials.master.env` |
| Серверы | `config/server-primary.md`, `config/server-secondary.md` |
| Cloudflare / AWS / Google Workspace | `config/cloudflare.md`, `config/aws.md`, `config/google-workspace.md` |
| Telegram / Email / БД | `config/telegram.md`, `config/email.md`, `config/databases.md` |
| Медиа / Мониторинг / Оркестратор | `config/tools.md`, `config/monitoring.md`, `config/orchestrator.md` |

> Все секреты — только в `.credentials.master.env` (в `.gitignore`). В конфигах — ссылки вида `${VAR_NAME}`, не значения. Каталог с описаниями → `config/README.md`.

---

## ОПЦИОНАЛЬНЫЕ ИНТЕГРАЦИИ

> Подключай по мере необходимости — не обязательны для базовой работы.

| Инструмент | Как вызвать / путь |
|-----------|--------------------|
| **Локальная база знаний** (Obsidian и т.п.) | Локальный vault + MCP-мост (порт задаётся в `settings.json`/`mcp.json`) |
| **Семантическая память** | Локальный векторный стор; тяжёлая индексация — только вручную, под ресурс-гардом |
| **Get Shit Done (планирование фаз)** | `/gsd:new-project`, `/gsd:next`, `/gsd:autonomous` |

---

## MCP (кратко; полный реестр → `config/mcp-servers.md`)

- **Local (`settings.json`):** `filesystem` и другие локальные серверы. Часть интеграций (context7, github и пр.) подключается через плагины.
- **Cloud (подписка Max, авто):** Airtable · Canva · Context7 · Figma · Gamma · Gmail · Google Calendar · Granola · Mermaid Chart · n8n — доступны, если подключены в аккаунте.
- **Доступные (`mcp.json`, включить при необходимости):** дополнительные серверы с колонкой «когда нужен» → `config/mcp-servers.md`.

---

## ПОИСК ПО ЧАТАМ (Chat Search)

- **Скрипт:** `~/.claude/tools/search_chats.py` · **БД:** `~/.claude/chats.db` (FTS5 + BM25) · **Архив:** `~/.claude/projects/<your-project>/archive/`.
- **Команды:** `/search-chats <q>` (полнотекст) · `index` (инкрементальная индексация) · `archive` (сессии старше 14 дней) · `archive-large` (крупные сессии старше 3 дней).
- **3-слойный поиск (token-aware):** `search` (компактный индекс, окно `--days`) → `timeline <id>` (контекст вокруг якоря) → `get <id,id>` (полные тексты по id).

---

## ИНСТРУМЕНТЫ (точные счётчики → `scripts/config_lint.py`)

285 готовых скиллов `skills/` · 74 агента `agents/` (57 в корне + 17 в подкаталогах health/meta/testing) · 155 команд `commands/` (98 в корне + 57 в gsd/) · 17 правил `rules/` (ядро) + `config/rules-ref/` (справочники) · 33 плагина включено (каталог → `config/rules-ref/plugins-catalog.md`).

> Числа выше — срез на 2026-08-16; они дрейфуют с каждым обновлением пака. Актуальные цифры всегда пересчитывай через `scripts/config_lint.py`, не цитируй по памяти: прошлый срез разошёлся с диском на восемь агентов ровно потому, что его написали руками.

---

## ДОКУМЕНТАЦИЯ ПРОЕКТОВ

> Складывай сюда доки под свои проекты. В комплекте идут:

| Тема | Файл |
|------|------|
| Beads (issue tracking) | `docs/beads-quickstart.md` |
| Оркестратор (спеки, quality gates, шаблоны отчётов) | `docs/orchestrator/` |
| _Твой проект_ | _добавь `docs/<PROJECT>_DOCS.md` и строку сюда_ |

---

## БЫСТРЫЕ ССЫЛКИ (замени плейсхолдеры на свои)

- **Основной сервер:** `ssh your-server` (`YOUR_SERVER_IP`)
- **N8N Cloud:** `https://your-name.app.n8n.cloud` · **N8N Server:** `http://YOUR_SERVER_IP:5678`
- **Мониторинг / статус:** задаётся в `config/monitoring.md`

---

## OWNER

Заполни свою идентичность и контакты в `rules/user-profile.md` (имя, email, каналы, предпочтения по языку и тону). Этот файл авто-загружается каждую сессию и питает персональные ответы — держи его актуальным и **не коммить** личные данные в публичные репозитории.