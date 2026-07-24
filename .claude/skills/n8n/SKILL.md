---
name: n8n
description: "n8n workflow automation — API integration, nodes, triggers, expressions, MCP, 400+ integrations. Ready-made recipes: CAPI через n8n, server-side события Meta, передать квал-лид в Meta, LTV в Pixel, webhook CRM в Facebook (CRM webhook → SHA-256 → Meta Conversions API), programmatic AI-SEO factory. EN: n8n CAPI workflow, server-side Meta events, CRM webhook to Facebook Conversions API."
---

# N8N Workflow Automation Skill

## Overview

Expert skill for using n8n - powerful workflow automation platform with 400+ integrations.

## ПРАВИЛО: сначала ищи готовый воркфлоу, потом строй с нуля

**ПЕРЕД сборкой любого n8n-воркфлоу с нуля — сначала проверь каталог 2061 готового воркфлоу ниже** (grep по папке или локальный FastAPI-поиск). Часто нужная интеграция (Telegram/RSS/OpenAI/CRM/Slack/...) уже собрана — быстрее адаптировать готовый JSON (перевесить credentials, поправить 2-3 ноды), чем рисовать граф с нуля.

## Каталог 4343 готовых воркфлоу (Zie619)

Источник: [github.com/Zie619/n8n-workflows](https://github.com/Zie619/n8n-workflows) (55.7k★). **Важно:** бейдж репозитория заявляет «4,343 workflows», но верифицировано (GitHub Trees API `git/trees/main?recursive=1` + локальный `git ls-tree`) — на текущем `main` реально **2061** JSON-файл воркфлоу. Бейдж в README не обновлён после чистки/дедупа коллекции — ориентируйся на реальную цифру 2061, не на маркетинговую 4343.

### Где лежит локально

```text
~/.claude/skills/n8n/catalog/       # git clone --depth 1, ~55 MB
├── workflows/                           # 2061 JSON, сгруппированы в 188 папок по интеграции
│   ├── Telegram/                        #   (Telegram, Openai, Rssfeedread, Slack, Httprequest...)
│   ├── Openai/
│   ├── Rssfeedread/
│   └── ...
├── context/                             # def_categories.json / search_categories.json / unique_categories.json
│                                         #   (маппинг node-type → 15 бизнес-категорий, полезно для grep-подхода)
├── database/workflows.db                # SQLite FTS5, уже проиндексирована (2061 записей)
├── .venv_search/                        # venv с FastAPI/uvicorn (см. ниже — версии requirements.txt не собираются на Python 3.13)
├── run.py                               # launcher локального поиск-сервера
├── api_server.py                        # FastAPI-приложение
└── README.md
```

Каждый воркфлоу — самостоятельный JSON в формате n8n-импорта: `{id, meta, name, tags, nodes, active, pinData, settings, versionId, connections}`. Имя файла кодирует интеграции/тип триггера, напр. `1941_Telegram_Stickynote_Automate_Triggered.json`.

Метрики каталога (из `/api/stats`): 311 уникальных интеграций, 30774 нод суммарно, 4 типа триггера (Webhook 588 / Manual 582 / Scheduled 244 / Complex-мультитриггер 647), 3 уровня сложности (low 467 / medium 844 / high 750), 215 активных / 1846 неактивных шаблонов. 15 бизнес-категорий + Uncategorized (через `/api/categories`): AI Agent Development, Business Process Automation, CRM & Sales, Cloud Storage & File Management, Communication & Messaging, Creative Content & Video Automation, Creative Design Automation, Data Processing & Analysis, E-commerce & Retail, Financial & Accounting, Marketing & Advertising Automation, Project Management, Social Media Management, Technical Infrastructure & DevOps, Web Scraping & Data Extraction.

### Как искать нужный воркфлоу — 3 способа

**1. Локальный FastAPI + SQLite FTS5 (рекомендуется — полнотекст, фильтры, <100мс)**

БД уже собрана. Запуск сервера (Python 3.13 gotcha ниже):

```bash
cd ~/.claude/skills/n8n/catalog
./.venv_search/Scripts/python.exe run.py --port 8123 --skip-index   # переиспользовать готовую БД
# или --reindex вместо --skip-index, если папка workflows/ изменилась
```

Веб-UI: `http://127.0.0.1:8123/` · Swagger: `http://127.0.0.1:8123/docs`. Ключевые эндпоинты:

| Эндпоинт | Что делает |
|----------|-----------|
| `GET /api/workflows?q=<term>&per_page=N` | полнотекстовый поиск по имени/описанию/интеграциям |
| `GET /api/workflows/category/{category}` | фильтр по одной из 15 бизнес-категорий |
| `GET /api/workflows/{filename}` | детали воркфлоу (без скачивания) |
| `GET /api/workflows/{filename}/download` | **raw JSON, готовый к импорту в n8n** |
| `GET /api/categories` · `/api/integrations` · `/api/stats` | справочники и метрики |

**Gotcha (Python 3.13):** `requirements.txt` пинует `pydantic==2.5.3` / `pydantic-core` — эта версия не собирается на Python 3.13 (падает в maturin/rust: `ForwardRef._evaluate() missing 'recursive_guard'`, т.к. `requirements.txt` рассчитан на 3.9-3.12). Фикс — ставить без пинов последние версии:
```bash
python -m venv .venv_search
./.venv_search/Scripts/python.exe -m pip install fastapi uvicorn pydantic PyJWT passlib httpx requests psutil email-validator python-multipart
```
Приложение работает без изменений кода — API не завязан на конкретный минорный pydantic.

**2. Grep по папке (без установки, мгновенно)** — когда сервер поднимать не нужно:

```bash
# по имени файла/папке интеграции (папки = 188 шт, по имени ноды: Telegram, Openai, Rssfeedread...)
find /c/~/.claude/skills/n8n/catalog/workflows -iname "*rss*"
ls /c/~/.claude/skills/n8n/catalog/workflows/Telegram/

# по точному node-type внутри JSON (точнее чем FTS, который матчит широко)
grep -ril "n8n-nodes-base.openAi" /c/~/.claude/skills/n8n/catalog/workflows
```
Grep даёт точные совпадения по node-type, но без ранжирования/синонимов — FTS находит больше (например `q=openai` — 507 совпадений против 32 у точного grep по node-type, т.к. FTS матчит ещё в названии/описании/связанных интеграциях).

**3. Веб-UI без установки** — `https://zie619.github.io/n8n-workflows` — тот же каталог онлайн, «Direct Downloads» скачивает JSON без клонирования репо. Годится, если каталог локально не поднят или это одноразовый поиск.

### Как забрать найденный воркфлоу и адаптировать под наш n8n

1. Скачать raw JSON — `GET /api/workflows/{filename}/download` (локальный сервер) или Read/скопировать файл напрямую из `workflows/<Категория>/<filename>.json`.
2. Импорт в наш n8n:
   - **Cloud** (`your-name.app.n8n.cloud`) — UI: Workflows → Import from File; либо API `POST {N8N_CLOUD_URL}/workflows` с телом JSON (см. `create_workflow()` выше в этом скилле).
   - **Server** (`YOUR_SERVER_IP:5678`) — аналогично через UI или `POST {N8N_SERVER_URL}/workflows`.
   - Перед импортом по API убери/не задавай `id`/`versionId` — n8n сгенерирует свои.
3. **Credentials-gotcha:** воркфлоу из каталога хранят только *тип* credential (напр. `telegramApi`), без секретов. После импорта ноды будут падать с "credential not found", пока вручную не перевесишь на реальные credentials Company (Telegram bot token, OpenAI key и т.д. — уже настроены в нашем n8n).
4. Проверь ноды на актуальность версий (`typeVersion`) — старые шаблоны из каталога иногда используют устаревшие версии нод, при открытии n8n сам предложит апгрейд.

### Смоук-тест поиска (реально выполнено, локальный FastAPI-сервер)

| Запрос | Результат | Примеры |
|--------|-----------|---------|
| `q=telegram` | 185 совпадений | `1941_Telegram_Stickynote_Automate_Triggered.json` — Telegram echo-bot (Webhook); `0748_Noop_Telegram_Automation_Scheduled.json` — RSS to Telegram (Scheduled) |
| `q=rss` | 9 совпадений | `1180_Rssfeedread_Htmlextract_Create_Scheduled.json` — Get only new RSS with Photo; `1176_Rssfeedread_Slack_Automation_Scheduled.json` — Post RSS feed items to Slack |
| `q=openai` | 507 совпадений | `Academic Assistant Chatbot (Telegram + OpenAI).json`; `1543_Manual_Openai_Automation_Triggered.json` — Summarize Google Sheets feedback via GPT-4 |

Поиск и скачивание (`/download`) проверены живьём — сервер поднимается, БД индексируется, JSON скачивается в валидном n8n-импорт формате.

## Ready-Made Workflow Recipes (методология)

Готовые рецепты на базе n8n  — конкретные workflow «под ключ»:

| Рецепт | Что делает | Reference |
|--------|-----------|-----------|
| **CAPI без кода через n8n** | CRM webhook (your CRM/HubSpot/Битрикс24) → нормализация → SHA-256 → Meta Conversions API → Test Events. Передача квал-лида/оплаты/LTV в Meta server-side. | `references/recipe-capi-meta.md` |
| **Программатическая AI-SEO фабрика** | Массовая генерация SEO-страниц под длинный хвост на n8n + Perplexity + OpenAI («1 запрос = 1 статья = 1 страница»). | скилл `ai-seo-agent-pipeline` |

**Cross-links на методологию (не дублируем здесь):**
- `capi-no-code-setup` — полная методология server-side трекинга: зачем CAPI, 7 параметров матчинга, хеширование, Event ID дедупликация, офлайн-конверсии, атрибуция. n8n — один из 4 инструментов (Zapier/Make/n8n/Albato); reference выше даёт готовый n8n-workflow.
- `ai-seo-agent-pipeline` — второй n8n-рецепт из того же курса.

**Two versions available:**
1. **Server (self-hosted)** - full control, no limits
2. **Cloud (managed)** - reliability, auto-updates

## API Keys

```python
import os

# API keys: ~/.claude/.credentials.master.env

# 1. SERVER VERSION (self-hosted on your-server)
N8N_SERVER_URL = os.getenv('N8N_SERVER_URL')  # http://YOUR_SERVER_IP:5678/api/v1
N8N_SERVER_API_KEY = os.getenv('N8N_SERVER_API_KEY')

# 2. CLOUD VERSION (n8n.cloud - managed)
N8N_CLOUD_URL = os.getenv('N8N_CLOUD_URL')  # https://your-name.app.n8n.cloud/api/v1
N8N_CLOUD_API_KEY = os.getenv('N8N_CLOUD_API_KEY')

# 3. MCP SERVER (for Claude integration)
N8N_MCP_SERVER_URL = os.getenv('N8N_MCP_SERVER_URL')  # https://your-name.app.n8n.cloud/mcp-server/http
N8N_MCP_ACCESS_TOKEN = os.getenv('N8N_MCP_ACCESS_TOKEN')
```

## MCP Integration (Claude)

n8n supports MCP (Model Context Protocol) for direct integration with Claude:

```json
// Add to mcp.json for Claude Desktop/Code
{
  "mcpServers": {
    "n8n": {
      "url": "https://your-name.app.n8n.cloud/mcp-server/http",
      "transport": "http",
      "headers": {
        "Authorization": "Bearer <N8N_MCP_ACCESS_TOKEN>"
      }
    }
  }
}
```

**Important:** MCP access must be enabled in workflow settings in n8n.

## When to Use N8N

**Best for:**
- Workflow automation
- API integrations (400+ ready-made)
- Scheduled tasks (cron)
- Data transformations
- Webhook handlers
- Multi-step automations
- No-code/low-code scenarios

**Advantages:**
- Visual workflow editor
- 400+ integrations
- Self-hosted option
- Custom code nodes (JS/Python)
- Webhook support
- Scheduling
- Error handling

## Basic Concepts

### Nodes

```
Trigger Node → Processing Node → Action Node
     ↓              ↓               ↓
  Webhook       Transform        Send Email
  Schedule       Filter          Slack Message
  App Event      Merge           Database Write
```

### Workflow Structure

```json
{
  "nodes": [
    {
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "position": [250, 300],
      "parameters": {
        "path": "my-webhook",
        "httpMethod": "POST"
      }
    },
    {
      "name": "Transform",
      "type": "n8n-nodes-base.set",
      "position": [450, 300],
      "parameters": {
        "values": {
          "string": [
            {
              "name": "message",
              "value": "={{ $json.body.text }}"
            }
          ]
        }
      }
    }
  ],
  "connections": {
    "Webhook": {
      "main": [
        [{ "node": "Transform", "type": "main", "index": 0 }]
      ]
    }
  }
}
```

## Expressions

### Basic Syntax

```javascript
// Access current item data
{{ $json.fieldName }}
{{ $json.nested.field }}
{{ $json.array[0] }}

// Access data from other nodes
{{ $node["NodeName"].json.field }}
{{ $("NodeName").item.json.field }}

// Access all items from a node
{{ $node["NodeName"].data }}
```

### JavaScript Expressions

```javascript
// String manipulation
{{ $json.name.toUpperCase() }}
{{ $json.email.split('@')[0] }}
{{ `Hello ${$json.name}!` }}

// Date operations
{{ new Date().toISOString() }}
{{ DateTime.now().toFormat('yyyy-MM-dd') }}
{{ DateTime.fromISO($json.date).plus({ days: 7 }) }}

// Conditionals
{{ $json.status === 'active' ? 'Yes' : 'No' }}
{{ $json.amount > 100 ? 'large' : 'small' }}

// Array operations
{{ $json.items.length }}
{{ $json.items.map(i => i.name).join(', ') }}
{{ $json.items.filter(i => i.active) }}
```

### Built-in Functions

```javascript
// String
{{ $json.text.trim() }}
{{ $json.text.replace('old', 'new') }}
{{ $json.text.includes('keyword') }}

// Numbers
{{ Math.round($json.amount * 100) / 100 }}
{{ parseInt($json.value) }}

// JSON
{{ JSON.stringify($json.data) }}
{{ JSON.parse($json.jsonString) }}

// URL
{{ encodeURIComponent($json.query) }}

// Crypto
{{ $uuid() }}
{{ $hash('sha256', $json.data) }}
```

## Data Transformation

### Set Node (Transform)

```javascript
// Set new fields
{
  "values": {
    "string": [
      { "name": "fullName", "value": "={{ $json.firstName }} {{ $json.lastName }}" }
    ],
    "number": [
      { "name": "total", "value": "={{ $json.price * $json.quantity }}" }
    ],
    "boolean": [
      { "name": "isVIP", "value": "={{ $json.totalPurchases > 1000 }}" }
    ]
  }
}
```

### Code Node (JavaScript)

```javascript
// Process each item
for (const item of $input.all()) {
  item.json.processed = true;
  item.json.timestamp = new Date().toISOString();
}
return $input.all();

// Create new items
return [
  { json: { name: 'Item 1', value: 100 } },
  { json: { name: 'Item 2', value: 200 } }
];

// Filter items
return $input.all().filter(item => item.json.status === 'active');

// Aggregate
const total = $input.all().reduce((sum, item) => sum + item.json.amount, 0);
return [{ json: { total } }];
```

### Merge Node

```javascript
// Merge modes:
// - Append: Combine all items
// - Merge by Index: Match items by position
// - Merge by Key: Match items by field value
// - Multiplex: Create all combinations

// Merge by Key configuration
{
  "mode": "mergeByKey",
  "propertyName1": "id",
  "propertyName2": "userId",
  "options": {
    "clash_handling": "overwrite"
  }
}
```

## API Usage

### Dependencies

```bash
pip install requests
```

### Setup Client

```python
import requests
import os

# Choose version
USE_CLOUD = False  # True for cloud, False for server

if USE_CLOUD:
    BASE_URL = os.getenv('N8N_CLOUD_URL')
    API_KEY = os.getenv('N8N_CLOUD_API_KEY')
else:
    BASE_URL = os.getenv('N8N_SERVER_URL')
    API_KEY = os.getenv('N8N_SERVER_API_KEY')

headers = {
    "X-N8N-API-KEY": API_KEY,
    "Content-Type": "application/json"
}
```

### List Workflows

```python
def list_workflows(active_only: bool = False):
    """Get all workflows."""

    params = {}
    if active_only:
        params["active"] = "true"

    response = requests.get(
        f"{BASE_URL}/workflows",
        headers=headers,
        params=params
    )

    workflows = response.json()["data"]

    return [
        {
            "id": w["id"],
            "name": w["name"],
            "active": w["active"],
            "updatedAt": w["updatedAt"]
        }
        for w in workflows
    ]
```

### Get Workflow Details

```python
def get_workflow(workflow_id: str):
    """Get workflow by ID."""

    response = requests.get(
        f"{BASE_URL}/workflows/{workflow_id}",
        headers=headers
    )

    return response.json()
```

### Create Workflow

```python
def create_workflow(name: str, nodes: list, connections: dict):
    """
    Create new workflow.

    Args:
        name: Workflow name
        nodes: List of node definitions
        connections: Node connections map
    """
    payload = {
        "name": name,
        "nodes": nodes,
        "connections": connections,
        "settings": {}
    }

    response = requests.post(
        f"{BASE_URL}/workflows",
        headers=headers,
        json=payload
    )

    return response.json()

# Example: Simple HTTP Request workflow
webhook_node = {
    "name": "Webhook",
    "type": "n8n-nodes-base.webhook",
    "typeVersion": 1,
    "position": [250, 300],
    "parameters": {
        "path": "my-webhook",
        "httpMethod": "POST"
    }
}

response_node = {
    "name": "Respond",
    "type": "n8n-nodes-base.respondToWebhook",
    "typeVersion": 1,
    "position": [450, 300],
    "parameters": {
        "respondWith": "json",
        "responseBody": "={{ JSON.stringify({ success: true }) }}"
    }
}

connections = {
    "Webhook": {
        "main": [[{"node": "Respond", "type": "main", "index": 0}]]
    }
}

workflow = create_workflow("My Webhook", [webhook_node, response_node], connections)
```

### Activate/Deactivate Workflow

```python
def activate_workflow(workflow_id: str, activate: bool = True):
    """Activate or deactivate workflow."""

    response = requests.patch(
        f"{BASE_URL}/workflows/{workflow_id}",
        headers=headers,
        json={"active": activate}
    )

    return response.json()
```

### Execute Workflow

```python
def execute_workflow(workflow_id: str, data: dict = None):
    """
    Execute workflow manually.

    Args:
        workflow_id: Workflow to execute
        data: Input data for workflow
    """
    payload = {}
    if data:
        payload["data"] = data

    response = requests.post(
        f"{BASE_URL}/workflows/{workflow_id}/execute",
        headers=headers,
        json=payload
    )

    return response.json()

# Usage
result = execute_workflow("123", {"name": "John", "email": "john@example.com"})
```

### Get Executions

```python
def get_executions(workflow_id: str = None, status: str = None, limit: int = 20):
    """
    Get workflow executions.

    Args:
        workflow_id: Filter by workflow
        status: "success", "error", "waiting"
        limit: Max results
    """
    params = {"limit": limit}

    if workflow_id:
        params["workflowId"] = workflow_id
    if status:
        params["status"] = status

    response = requests.get(
        f"{BASE_URL}/executions",
        headers=headers,
        params=params
    )

    return response.json()["data"]
```

### Delete Workflow

```python
def delete_workflow(workflow_id: str):
    """Delete workflow."""

    response = requests.delete(
        f"{BASE_URL}/workflows/{workflow_id}",
        headers=headers
    )

    return response.status_code == 200
```

## Workflow Templates

### HTTP API Wrapper

```python
http_api_workflow = {
    "name": "API Wrapper",
    "nodes": [
        {
            "name": "Webhook",
            "type": "n8n-nodes-base.webhook",
            "position": [250, 300],
            "parameters": {
                "path": "api",
                "httpMethod": "={{$parameter.httpMethod}}",
                "responseMode": "responseNode"
            }
        },
        {
            "name": "HTTP Request",
            "type": "n8n-nodes-base.httpRequest",
            "position": [450, 300],
            "parameters": {
                "url": "https://api.example.com/data",
                "method": "GET"
            }
        },
        {
            "name": "Respond",
            "type": "n8n-nodes-base.respondToWebhook",
            "position": [650, 300],
            "parameters": {
                "respondWith": "json"
            }
        }
    ]
}
```

### Scheduled Data Sync

```python
sync_workflow = {
    "name": "Daily Data Sync",
    "nodes": [
        {
            "name": "Schedule",
            "type": "n8n-nodes-base.scheduleTrigger",
            "position": [250, 300],
            "parameters": {
                "rule": {
                    "interval": [{"field": "cronExpression", "expression": "0 9 * * *"}]
                }
            }
        },
        {
            "name": "Fetch Data",
            "type": "n8n-nodes-base.httpRequest",
            "position": [450, 300],
            "parameters": {
                "url": "https://api.source.com/data",
                "method": "GET"
            }
        },
        {
            "name": "Transform",
            "type": "n8n-nodes-base.code",
            "position": [650, 300],
            "parameters": {
                "jsCode": "return items.map(item => ({ json: { ...item.json, processed: true } }));"
            }
        },
        {
            "name": "Save",
            "type": "n8n-nodes-base.httpRequest",
            "position": [850, 300],
            "parameters": {
                "url": "https://api.destination.com/import",
                "method": "POST"
            }
        }
    ]
}
```

## HTTP Requests

### HTTP Request Node

```javascript
// Basic GET
{
  "method": "GET",
  "url": "https://api.example.com/users",
  "authentication": "predefinedCredential",
  "credential": "myApiCredential"
}

// POST with JSON body
{
  "method": "POST",
  "url": "https://api.example.com/users",
  "sendBody": true,
  "bodyContentType": "json",
  "body": {
    "name": "={{ $json.name }}",
    "email": "={{ $json.email }}"
  }
}

// With headers
{
  "options": {
    "headers": {
      "X-Custom-Header": "value"
    }
  }
}
```

### Pagination

```javascript
// Loop through pages
{
  "options": {
    "pagination": {
      "type": "offset",
      "paginationCompleteWhen": "receiveSpecificStatusCodes",
      "statusCodes": "404"
    }
  }
}
```

## Error Handling

### Error Trigger

```javascript
// Catch errors from workflow
{
  "errorTriggerType": "workflow"
}

// Access error info
{{ $json.error.message }}
{{ $json.error.node }}
{{ $json.execution.id }}
```

### Try/Catch Pattern

```
Start → HTTP Request → Success Path
           ↓
     Error Handler → Slack Alert
```

### Retry Logic

```javascript
// In Code node
const maxRetries = 3;
let retries = 0;

while (retries < maxRetries) {
  try {
    // Make request
    return result;
  } catch (error) {
    retries++;
    if (retries === maxRetries) throw error;
    await new Promise(r => setTimeout(r, 1000 * retries));
  }
}
```

## Common Patterns

### Webhook → Process → Respond

```
Webhook → Validate → Transform → Database → Respond

// Webhook with custom response
{
  "responseMode": "lastNode",
  "responseData": "firstEntryJson"
}
```

### Scheduled Data Sync

```
Schedule → Fetch API → Transform → Upsert DB → Log

// Every hour sync
{
  "rule": { "cronExpression": "0 * * * *" }
}
```

### Multi-step Approval

```
Form Submit → Create Ticket → Wait for Approval → Process
                    ↓
              Send Notification
```

### Data Pipeline

```
Trigger → Extract (API) → Transform → Load (DB) → Report
              ↓
         Error Handler → Alert
```

## Common Node Types

| Node | Description |
|------|-------------|
| `webhook` | HTTP webhook trigger |
| `schedule` | Cron/schedule trigger |
| `httpRequest` | Make HTTP requests |
| `code` | Custom JS/Python code |
| `set` | Set/transform data |
| `if` | Conditional logic |
| `switch` | Multi-branch routing |
| `merge` | Combine data streams |
| `splitInBatches` | Batch processing |
| `function` | Custom JS function |

## Common Triggers

### Webhook Trigger

```javascript
// Webhook node configuration
{
  "path": "my-webhook",
  "httpMethod": "POST",
  "responseMode": "onReceived",
  "responseData": "allEntries"
}

// Access webhook data
{{ $json.body }}           // POST body
{{ $json.query }}          // Query params
{{ $json.headers }}        // Headers
```

### Schedule Trigger

```javascript
// Cron expressions
{
  "rule": {
    "cronExpression": "0 9 * * *"  // Every day at 9 AM
  }
}

// Common patterns:
// "*/5 * * * *"    - Every 5 minutes
// "0 * * * *"      - Every hour
// "0 9 * * 1-5"    - Weekdays at 9 AM
// "0 0 1 * *"      - First of month
```

### App Triggers

```javascript
// Gmail Trigger
{
  "pollTimes": {
    "item": [{ "mode": "everyMinute" }]
  },
  "filters": {
    "readStatus": "unread"
  }
}

// Slack Trigger
{
  "channel": "#general",
  "event": "message"
}
```

## Trigger Webhook

```python
import os

def trigger_webhook(webhook_path: str, data: dict, use_cloud: bool = False):
    """Trigger n8n webhook."""

    if use_cloud:
        # Cloud version
        webhook_url = f"https://your-name.app.n8n.cloud/webhook/{webhook_path}"
    else:
        # Server version
        webhook_url = f"http://YOUR_SERVER_IP:5678/webhook/{webhook_path}"

    response = requests.post(webhook_url, json=data)
    return response.json()

# Usage
result = trigger_webhook("my-webhook", {"message": "Hello from Python!"})
```

## Popular Integrations

| Category | Nodes |
|----------|-------|
| **AI** | OpenAI, Claude, Gemini, Ollama |
| **Communication** | Telegram, Slack, Discord, Email |
| **CRM** | HubSpot, Salesforce, Pipedrive |
| **Databases** | PostgreSQL, MySQL, MongoDB, Redis |
| **Storage** | Google Drive, Dropbox, S3 |
| **Dev** | GitHub, GitLab, Jira, Linear |
| **Marketing** | Mailchimp, Sendgrid, ActiveCampaign |
| **Productivity** | Notion, Airtable, Google Sheets |

## Server vs Cloud

| Feature | Server | Cloud |
|---------|--------|-------|
| Control | Full | Limited |
| Updates | Manual | Auto |
| Scaling | Manual | Auto |
| Cost | Server costs | Subscription |
| Uptime | Your responsibility | 99.9% SLA |
| Custom nodes | Yes | Limited |

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/workflows` | GET | List workflows |
| `/workflows` | POST | Create workflow |
| `/workflows/{id}` | GET | Get workflow |
| `/workflows/{id}` | PATCH | Update workflow |
| `/workflows/{id}` | DELETE | Delete workflow |
| `/workflows/{id}/execute` | POST | Execute workflow |
| `/executions` | GET | List executions |
| `/executions/{id}` | GET | Get execution |
| `/credentials` | GET | List credentials |

## Best Practices

1. **Naming** - use clear node names
2. **Error handling** - add error handling to workflows
3. **Logging** - log important steps
4. **Testing** - test workflows before production
5. **Modular** - break large workflows into sub-processes
6. **Credentials** - store secrets in credentials
7. **Documentation** - add sticky notes with descriptions

## Tips

1. **Webhooks** - use for API endpoints
2. **Schedule** - for periodic tasks
3. **Code nodes** - when complex logic is needed
4. **Error handling** - add Error Trigger nodes
5. **Credentials** - store API keys in n8n, not in workflows
6. **Testing** - use Execute Workflow before activation
7. **Versioning** - export workflows as JSON
8. **Logging** - add Set nodes for debugging
9. **Webhook testing** - use n8n test URL
10. **Expression tester** - built-in expression tester
11. **Execution history** - analyze past executions
12. **Sub-workflows** - reuse logic
13. **Wait node** - for async processes
14. **Batch processing** - for large volumes of data
