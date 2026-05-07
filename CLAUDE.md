# CLAUDE BRAIN — НАВИГАЦИЯ

> Читай при каждом запуске. Навигация по ресурсам. Детали — в подключаемых файлах.

## РЕЖИМ РАБОТЫ — АВТОНОМНЫЙ

- Proceed autonomously when the task is clear — no need to ask for permission first.
- NEVER suggest /compact, NEVER mention context size, NEVER pause to manage context. Auto-compact handles this automatically. You have 1M tokens — just keep working.
- Keep working until the task is complete — no need to pause between steps.
- Go straight to execution — skip summarizing what you're about to do.
- NEVER ask "shall I do X?" or "start with Y?" — just do it. Show results, not plans.
- Единственная причина остановиться: нужна информация которую только пользователь может дать.

---

## ПРАВИЛА (авто-загрузка из ~/.claude/rules/)

| Файл | Назначение |
|------|------------|
| `rules/routing.md` | Маршрутная карта задача → skill/agent |
| `rules/delegation.md` | Уровни сложности + обязательные делегации |
| `rules/scaling.md` | Decision tree: Level 0-3, parallel agents, worktrees |
| `rules/context7.md` | Context7 MCP auto-invoke |
| `rules/context-management.md` | Когда compact/clear/subagent, лимиты контекста |
| `rules/model-selection.md` | Какую модель для какой задачи (decision tree) |
| `rules/auto-learning.md` | vector_memory.py learn/decide |
| `rules/autonomous-mode.md` | Автономный режим, не спрашивай разрешения |
| `rules/security.md` | API ключи, SSH, формат изображений |
| `rules/security-hardening.md` | Sandbox, audit logging, commercial deployment |
| `rules/permissions.md` | Permission modes, sandbox, trust levels |
| `rules/quality-gates.md` | Build checks, systematic debugging |
| `rules/dont-do.md` | Что запрещено |
| `rules/personality.md` | Стиль общения и приоритеты |
| `rules/hooks.md` | Документация по всем hooks |
| `rules/models.md` | Модели Claude Code (Opus 4.6, Sonnet 4.5, Haiku 4.5) |
| `rules/onboarding.md` | First-time setup guide для новых пользователей |
| `rules/headless-ci.md` | Claude -p, CI/CD интеграция, автоматизация |
| `rules/prompt-caching.md` | Оптимизация кеширования, экономия для B2B |
| `rules/plugins-catalog.md` | Каталог всех установленных плагинов |
| `rules/user-profile.md` | Профиль пользователя, контакты, предпочтения |
| `rules/worktrees.md` | Git worktrees как стандартный workflow |

---

## КОНФИГУРАЦИЯ (~/.claude/config/)

| Что | Файл |
|-----|------|
| **Реестр проектов** | `config/projects-registry.md` |
| Модели AI (все провайдеры) | `config/models.md` |
| API ключи | `.credentials.master.env` |
| Сервер your-server | `config/server-primary.md` |
| Сервер Secondary-Server | `config/server-secondary.md` |
| Cloudflare | `config/cloudflare.md` |
| AWS | `config/aws.md` |
| Google Workspace | `config/google-workspace.md` |
| Telegram | `config/telegram.md` |
| Email | `config/email.md` |
| Базы данных | `config/databases.md` |
| Медиа/инструменты | `config/tools.md` |
| Мониторинг | `config/monitoring.md` |
| Оркестратор | `config/orchestrator.md` |
| ScraperVendor | `.credentials.master.env` (configure if needed) |

---

## OPTIONAL: SCRAPE & INTELLIGENCE STACK (3rd-party API)

| Скилл | Назначение | Триггеры |
|-------|------------|----------|
| `last30days` | 30-дневный research по 11 соцсетям | "last30", "что обсуждают", "тренды" |
| `social-intel` | Кросс-платформенное досье на человека/компанию | "досье на", "найди соцсети", "KYC" |
| `ad-spy` | Мониторинг рекламы конкурентов (FB/Google/LinkedIn/Reddit) | "реклама конкурентов", "ad library" |
| `tiktok-intel` | TikTok/Instagram тренды, инфлюенсеры, TikTok Shop | "тикток тренды", "инфлюенсеры" |
| `linkedin` | LinkedIn профили, компании, посты, ad library | "LinkedIn", "обогати контакт" |

---

## KNOWLEDGE & DEVELOPMENT TOOLS

| Инструмент | Назначение | Как вызвать |
|-----------|------------|-------------|
| **Obsidian** | Локальный Knowledge Base | Vault: `~/Obsidian/Knowledge-Base/`, MCP: WebSocket :OBSIDIAN_PORT |
| **Get Shit Done** | Фреймворк разработки с фазами и верификацией | `/gsd:new-project`, `/gsd:next`, `/gsd:autonomous` |
| **Video Factory** | Полный пайплайн: тренды → сценарий → аватар → видео → YouTube | Agent `video-factory`, `/video-factory topic` |

---

## ИНСТРУМЕНТЫ

| Что | Где | Кол-во |
|-----|-----|--------|
| Навыки | `skills/` | 259 (все dir/SKILL.md формат) |
| Агенты | `agents/` | 49 files |
| Команды | `commands/` | 166 |
| Правила | `rules/` | 23 |
| Плагины | `settings.json` | см. settings.json |
| MCP серверы | `settings.json` + `mcp.json` + cloud | 1 local + 19 доступных + 10 cloud (от подписки) |

---

## ПЛАГИНЫ (см. settings.json)

### Core Development
- code-review, pr-review-toolkit (PR review automation)
- superpowers (core enhancements)
- agent-sdk-dev (agent development)
- security-guidance (security best practices)
- plugin-dev (toolkit для создания плагинов)
- skill-creator (создание и бенчмарк скиллов)
- semgrep (static analysis with Semgrep rules)

### Language Servers
- pyright-lsp (Python type checking, autocomplete)
- typescript-lsp (TypeScript/JavaScript intelligence)

### Frontend & Design
- frontend-design (UI/UX development)
- playwright (browser testing)
- figma (Figma design integration)

### Integrations
- greptile (AI code review for GitHub/GitLab)
- slack (official Slack MCP)
- linear (official Linear MCP)
- context7 (документация библиотек и фреймворков)
- github (GitHub operations, PR, issues)
- sentry (мониторинг ошибок)
- notion (база знаний Notion)
- firecrawl (web scraping и extraction)
- coderabbit (AI code review)
- sourcegraph (code search across repositories)
- legalzoom (legal document analysis)
- adspirer-ads-agent (Google/Meta/LinkedIn ad campaigns)
- telegram (Channels — управление через Telegram)

### Development Workflow
- feature-dev, code-simplifier
- commit-commands, ralph-loop, playground
- claude-code-setup, claude-md-management
- dev-browser (browser with persistent state, cookies)

### AI & ML
- huggingface-skills (HuggingFace models)

### Disabled
- mintlify, zapier, laravel-boost

---

## KNOWLEDGE WORK SKILLS (из anthropics/knowledge-work-plugins)

Установлены вручную из open-source плагинов Claude Cowork. Маршруты — в `rules/routing.md`.

### Product Management
| Тип | Название | Назначение |
|-----|----------|------------|
| skill | `feature-spec` | PRD и спецификации продукта |
| skill | `metrics-tracking` | Продуктовые метрики, OKR, North Star |
| skill | `roadmap-management` | Приоритизация и планирование роадмапа |
| skill | `stakeholder-comms` | Апдейты для стейкхолдеров (G/Y/R) |
| skill | `user-research-synthesis` | Синтез UX-исследований |
| cmd | `/write-spec` | Написать PRD (заменил /prd) |
| cmd | `/competitive-brief` | Конкурентный бриф |
| cmd | `/metrics-review` | Обзор продуктовых метрик |
| cmd | `/roadmap-update` | Обновление роадмапа |
| cmd | `/stakeholder-update` | Стейкхолдер-апдейт |
| cmd | `/synthesize-research` | Синтез UX-исследований |
| cmd | `/sprint-planning-pm` | Планирование спринта (PM) |

### Sales
| Тип | Название | Назначение |
|-----|----------|------------|
| skill | `account-research` | Исследование компании/аккаунта |
| skill | `call-prep` | Подготовка к звонку |
| skill | `competitive-intelligence` | Конкурентная разведка (HTML battlecard) |
| skill | `create-an-asset` | Генерация sales-материалов |
| skill | `daily-briefing` | Утренний sales-брифинг |
| skill | `draft-outreach` | Персонализированный outreach |
| cmd | `/call-summary` | Саммари звонка |
| cmd | `/forecast` | Sales прогноз |
| cmd | `/pipeline-review` | Обзор пайплайна |

### Marketing
| Тип | Название | Назначение |
|-----|----------|------------|
| skill | `brand-voice` | Бренд-голос и tone of voice |
| skill | `campaign-planning` | Планирование кампаний |
| skill | `competitive-analysis-mktg` | Конкурентный анализ (маркетинг) |
| skill | `content-creation` | Создание маркетингового контента |
| skill | `performance-analytics` | Маркетинг-аналитика (ROAS, CPL) |
| cmd | `/brand-review` | Обзор бренда |
| cmd | `/campaign-plan` | План кампании |
| cmd | `/draft-content` | Драфт контента |
| cmd | `/email-sequence` | Email-последовательность |
| cmd | `/performance-report` | Маркетинг performance отчёт |
| cmd | `/seo-audit` | SEO-аудит |
| cmd | `/competitive-brief-mktg` | Конкурентный бриф (маркетинг) |

---

## MCP СЕРВЕРЫ

### Local (settings.json — грузятся при каждой сессии)

| Сервер | Назначение |
|--------|-----------|
| filesystem | Файловые операции (${WORKSPACE}, ${HOME}) |

> chrome-devtools — встроен в VSCode расширение (не в settings.json mcpServers).
> context7 и github мигрированы на плагины (быстрее, нет cold start от npx).

### Cloud MCP (от подписки Max — автоматически)

| Сервер | Назначение |
|--------|-----------|
| Airtable | Базы данных, таблицы, записи |
| Canva | Дизайн: генерация, редактирование, экспорт |
| Context7 | Документация библиотек (дублирует плагин) |
| Figma | Дизайн-контекст, скриншоты, диаграммы |
| Gamma | AI презентации и документы |
| Gmail | Поиск, чтение, черновики |
| Google Calendar | События, свободные слоты |
| Granola | Транскрипты встреч |
| Mermaid Chart | Рендер Mermaid диаграмм |
| n8n | Поиск и запуск workflow |

### Доступные (mcp.json — включить при необходимости)

| Сервер | Назначение | Когда нужен |
|--------|-----------|-------------|
| postgres | SQL операции (your-server) | Работа с БД |
| redis | Кеш и pub/sub (your-server) | Работа с кешем |
| sqlite | Локальная БД (Your Bot) | Лёгкие БД задачи |
| dalle | DALL-E генерация через OpenAI | Генерация изображений |
| replicate | 1000+ AI моделей | Специализированные AI задачи |
| elevenlabs | TTS, voice cloning | Озвучка |
| apify | Web scraping (1600+ Actors) | Сбор данных |
| n8n | Workflow automation (SSE, local) | Автоматизация |
| puppeteer | Browser automation | Screenshots |
| brave-search | Web search API | Research |
| fetch | Web content → markdown | Парсинг |
| memory | Knowledge Graph | Multi-agent context |
| sequentialthinking | Step-by-step reasoning | Сложный анализ |
| time | Время/timezone | Планирование |
| microsoft-office | PPTX, XLSX, DOCX | Офисные документы |
| everything | MCP test/debug server | Тестирование MCP |
| figma-mcp | Figma HTTP MCP (mcp.figma.com) | Альтернатива плагину |
| playwright | Browser automation | Альтернатива плагину |

---

## ПОИСК ПО ЧАТАМ (Chat Search)

| Компонент | Путь |
|-----------|------|
| Скрипт | `${WORKSPACE}/tools/search_chats.py` |
| SQLite БД | `~/.claude/chats.db` (FTS5, ~30 MB) |
| Архив сессий | `~/.claude/projects/C--Users-youruser/archive/` |
| Команда | `/search-chats` |

**Использование:**
- `/search-chats запрос` — полнотекстовый поиск по всей истории
- `/search-chats index` — обновить индекс (инкрементально)
- `/search-chats archive` — заархивировать старые сессии (>14 дней)
- `/search-chats archive-large` — заархивировать тяжёлые сессии (>20MB, >3 дней)

**Архитектура:** SQLite FTS5 + BM25 ранжирование, 0 внешних зависимостей. Архивированные сессии остаются в индексе и доступны для поиска.

---

## ДОКУМЕНТАЦИЯ ПРОЕКТОВ

| Проект | Файл |
|--------|------|
| Сервер Secondary-Server | `docs/SECONDARY_SERVER_ACCESS.md` |
| Beads (issue tracking) | `docs/beads-quickstart.md` |
| Оркестратор (спеки) | `docs/orchestrator/` |

---

## БЫСТРЫЕ ССЫЛКИ

- **Сервер your-server:** `ssh your-server` (YOUR_SERVER_IP)
- **N8N Cloud:** https://your-name.app.n8n.cloud
- **N8N Server:** http://YOUR_SERVER_IP:5678
