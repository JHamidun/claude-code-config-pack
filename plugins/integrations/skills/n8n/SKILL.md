---
name: n8n
description: "n8n workflow automation: API, ноды, MCP + локальный каталог 2061 готового воркфлоу. Триггеры: «сценарий в n8n», «нода n8n», «автоматизация»."
---

# n8n

## Сначала ищи готовый воркфлоу, потом строй с нуля

**ПЕРЕД сборкой любого n8n-воркфлоу с нуля проверь локальный каталог** (grep по
папке или локальный FastAPI-поиск, оба ниже). Ходовая интеграция —
Telegram/RSS/OpenAI/CRM/Slack — почти наверняка уже собрана, и перевесить
credentials да поправить две-три ноды быстрее и надёжнее, чем рисовать граф
заново.

## Каталог Zie619 (локально)

Источник: [github.com/Zie619/n8n-workflows](https://github.com/Zie619/n8n-workflows).
**Бейдж репозитория заявляет «4,343 workflows» — это неверно.** Проверка через
GitHub Trees API (`git/trees/main?recursive=1`) и локальный `git ls-tree` даёт на
текущем `main` **2061** JSON-файл: README не обновили после дедупа коллекции.
Ориентируйся на 2061, иначе будешь искать несуществующее.

```text
~/.claude/skills/n8n/catalog/    # git clone --depth 1, ~55 MB
├── workflows/                   # 2061 JSON в 188 папках по интеграции (Telegram/, Openai/, Rssfeedread/, Slack/…)
├── context/                     # def_categories.json, search_categories.json, unique_categories.json — маппинг node-type → 15 бизнес-категорий
├── database/workflows.db        # SQLite FTS5, уже проиндексирована (2061 запись)
├── .venv_search/                # venv с FastAPI/uvicorn (см. гочу Python 3.13)
├── run.py                       # launcher локального поиск-сервера
└── api_server.py                # FastAPI-приложение
```

Каждый файл — самостоятельный JSON в формате n8n-импорта
(`{id, meta, name, tags, nodes, active, pinData, settings, versionId, connections}`).
Имя кодирует интеграции и тип триггера: `1941_Telegram_Stickynote_Automate_Triggered.json`.

Метрики каталога (`/api/stats`): 311 уникальных интеграций, 30 774 ноды, триггеры
Webhook 588 / Manual 582 / Scheduled 244 / мультитриггер 647, сложность low 467 /
medium 844 / high 750, активных 215 из 2061. Категории (`/api/categories`): AI Agent
Development, Business Process Automation, CRM & Sales, Cloud Storage & File
Management, Communication & Messaging, Creative Content & Video Automation, Creative
Design Automation, Data Processing & Analysis, E-commerce & Retail, Financial &
Accounting, Marketing & Advertising Automation, Project Management, Social Media
Management, Technical Infrastructure & DevOps, Web Scraping & Data Extraction,
Uncategorized.

### Поиск 1 — локальный FastAPI + FTS5 (полнотекст, фильтры, <100 мс)

БД уже собрана, индексировать заново не нужно:

```bash
cd ~/.claude/skills/n8n/catalog
./.venv_search/Scripts/python.exe run.py --port 8123 --skip-index
# --reindex вместо --skip-index — только если папка workflows/ изменилась
```

Веб-UI `http://127.0.0.1:8123/`, Swagger `/docs`. Эндпоинты:

| Эндпоинт | Что делает |
|----------|-----------|
| `GET /api/workflows?q=<term>&per_page=N` | полнотекст по имени/описанию/интеграциям |
| `GET /api/workflows/category/{category}` | фильтр по бизнес-категории |
| `GET /api/workflows/{filename}` | детали без скачивания |
| `GET /api/workflows/{filename}/download` | **raw JSON, готовый к импорту в n8n** |
| `GET /api/categories` · `/api/integrations` · `/api/stats` | справочники и метрики |

**Гоча (Python 3.13):** `requirements.txt` пинует `pydantic==2.5.3`, а эта версия на
3.13 не собирается — падает в maturin/rust с `ForwardRef._evaluate() missing
'recursive_guard'` (файл рассчитан на 3.9–3.12). Ставить без пинов, код приложения
менять не нужно — API не завязан на конкретный минорный pydantic:

```bash
python -m venv .venv_search
./.venv_search/Scripts/python.exe -m pip install fastapi uvicorn pydantic PyJWT passlib httpx requests psutil email-validator python-multipart
```

### Поиск 2 — grep по папке (без сервера, мгновенно)

```bash
find ~/.claude/skills/n8n/catalog/workflows -iname "*rss*"
ls ~/.claude/skills/n8n/catalog/workflows/Telegram/
grep -ril "n8n-nodes-base.openAi" ~/.claude/skills/n8n/catalog/workflows
```

Grep точен по node-type, но не ранжирует и не знает синонимов, поэтому находит
заметно меньше: `q=openai` в FTS даёт 507 совпадений против 32 у точного grep по
node-type — FTS матчит ещё имя, описание и смежные интеграции. Замер на этом же
каталоге: `q=telegram` → 185, `q=rss` → 9.

### Поиск 3 — онлайн, без установки

`https://zie619.github.io/n8n-workflows` — тот же каталог, кнопка «Direct
Downloads» отдаёт JSON без клонирования репо. Годится для разового поиска.

### Импорт найденного в наш n8n

1. Забрать raw JSON: `GET /api/workflows/{filename}/download` либо просто Read файла
   из `workflows/<Категория>/`.
2. Импорт — UI (Workflows → Import from File) или `POST {BASE_URL}/workflows`.
   **Перед импортом по API убери `id` и `versionId`** — n8n сгенерирует свои, чужие
   вызовут конфликт.
3. **Credentials-гоча:** шаблоны каталога хранят только *тип* credential (например
   `telegramApi`), без секретов. Сразу после импорта ноды падают с «credential not
   found», пока вручную не перевесишь их на наши реальные credentials.
4. Проверь `typeVersion` нод: старые шаблоны тянут устаревшие версии, n8n предложит
   апгрейд при открытии.

## Готовые рецепты

| Рецепт | Что делает | Где |
|--------|-----------|-----|
| **CAPI без кода** | CRM webhook (HubSpot/Битрикс24/своя) → нормализация → SHA-256 → Meta Conversions API → Test Events; квал-лид, оплата, LTV server-side | `references/recipe-capi-meta.md` |
| **Программатическая AI-SEO фабрика** | массовая генерация SEO-страниц под длинный хвост: n8n + Perplexity + OpenAI, «1 запрос = 1 статья = 1 страница» | скилл `ai-seo-agent-pipeline` |

Методологию не дублируем: зачем CAPI, 7 параметров матчинга, хеширование, Event ID
дедупликация, офлайн-конверсии, атрибуция — в скилле `capi-no-code-setup` (n8n там
один из четырёх инструментов наряду с Zapier/Make/Albato).

## Доступы

Ключи — в `~/.claude/.credentials.master.env`, в коде только `os.getenv`:

```python
N8N_SERVER_URL      # http://<ip>:5678/api/v1   — self-hosted
N8N_SERVER_API_KEY
N8N_CLOUD_URL       # https://<имя>.app.n8n.cloud/api/v1 — managed
N8N_CLOUD_API_KEY
N8N_MCP_SERVER_URL  # https://<имя>.app.n8n.cloud/mcp-server/http
N8N_MCP_ACCESS_TOKEN
```

Оба инстанса живые, выбор по задаче: self-hosted — свои ноды и никаких лимитов,
cloud — обновления и аптайм не на нас.

## MCP

```json
{
  "mcpServers": {
    "n8n": {
      "url": "https://<имя>.app.n8n.cloud/mcp-server/http",
      "transport": "http",
      "headers": { "Authorization": "Bearer <N8N_MCP_ACCESS_TOKEN>" }
    }
  }
}
```

**Доступ по MCP включается в настройках самого воркфлоу** в n8n — без этого сервер
отвечает, но воркфлоу для него не существует.

## Справочник

Точный синтаксис выражений (`{{ $json… }}`, Luxon-даты, `$hash`), контракт Code-ноды,
режимы Merge, таблица эндпоинтов REST API и шаблон создания воркфлоу кодом →
`references/api-and-expressions.md`. Нужен, когда собираешь граф программно или
правишь выражение в ноде; для работы с каталогом не требуется.

