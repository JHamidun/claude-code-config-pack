# n8n: REST API и синтаксис выражений (справочник)

> Читать, когда собираешь воркфлоу **программно** (через API, а не в UI) или когда
> нужен точный синтаксис выражения/ноды. Для обычной работы с каталогом готовых
> воркфлоу этот файл не нужен — всё в теле навыка.

## REST API

База — `N8N_SERVER_URL` / `N8N_CLOUD_URL` (обе уже включают `/api/v1`).
Заголовок авторизации: `X-N8N-API-KEY: <ключ>`, тело — `application/json`.

| Эндпоинт | Метод | Назначение |
|----------|-------|-----------|
| `/workflows` | GET | список (фильтр `?active=true`) |
| `/workflows` | POST | создать |
| `/workflows/{id}` | GET | получить |
| `/workflows/{id}` | PATCH | обновить (в т.ч. `{"active": true/false}`) |
| `/workflows/{id}` | DELETE | удалить |
| `/workflows/{id}/execute` | POST | запустить вручную |
| `/executions` | GET | список запусков (`workflowId`, `status`: success/error/waiting, `limit`) |
| `/executions/{id}` | GET | детали запуска |
| `/credentials` | GET | список credentials |

Тело создания воркфлоу — `{"name", "nodes", "connections", "settings"}`:

```python
import os, requests

BASE_URL = os.getenv('N8N_SERVER_URL')      # или N8N_CLOUD_URL
API_KEY  = os.getenv('N8N_SERVER_API_KEY')  # или N8N_CLOUD_API_KEY
headers = {"X-N8N-API-KEY": API_KEY, "Content-Type": "application/json"}

def create_workflow(name: str, nodes: list, connections: dict):
    payload = {"name": name, "nodes": nodes, "connections": connections, "settings": {}}
    return requests.post(f"{BASE_URL}/workflows", headers=headers, json=payload).json()
```

Пример пары нод и связи между ними (позиция `[x, y]` — координаты на холсте,
`connections` адресует ноды по **имени**, а не по id):

```python
webhook_node = {
    "name": "Webhook", "type": "n8n-nodes-base.webhook", "typeVersion": 1,
    "position": [250, 300],
    "parameters": {"path": "my-webhook", "httpMethod": "POST"},
}
respond_node = {
    "name": "Respond", "type": "n8n-nodes-base.respondToWebhook", "typeVersion": 1,
    "position": [450, 300],
    "parameters": {"respondWith": "json",
                   "responseBody": "={{ JSON.stringify({ success: true }) }}"},
}
connections = {"Webhook": {"main": [[{"node": "Respond", "type": "main", "index": 0}]]}}
```

Вызов вебхука снаружи идёт не по API-базе, а по адресу инстанса:
`{host}/webhook/{path}` (у Cloud — `https://<имя>.app.n8n.cloud/webhook/...`,
у сервера — `http://<ip>:5678/webhook/...`).

## Выражения

Значение поля становится выражением, только если строка начинается с `=`:
`"value": "={{ $json.name }}"`. Без ведущего `=` n8n подставит текст буквально —
это самая частая причина «почему в поле стоит `{{ $json.x }}`».

```javascript
{{ $json.field }}                    // текущий item
{{ $node["NodeName"].json.field }}   // данные другой ноды (старый синтаксис)
{{ $("NodeName").item.json.field }}  // тот же смысл, новый синтаксис
{{ $node["NodeName"].data }}         // все items ноды

{{ DateTime.now().toFormat('yyyy-MM-dd') }}          // даты — Luxon, не Date
{{ DateTime.fromISO($json.date).plus({ days: 7 }) }}
{{ $uuid() }}
{{ $hash('sha256', $json.data) }}                    // нужен, напр., для CAPI
{{ encodeURIComponent($json.query) }}
```

Внутри `{{ }}` доступен обычный JS: `.map/.filter/.reduce`, шаблонные строки,
тернарник, `Math.*`, `JSON.parse/stringify`.

## Ходовые ноды

| Нода (`n8n-nodes-base.*`) | Назначение |
|---------------------------|-----------|
| `webhook` | HTTP-триггер |
| `scheduleTrigger` | расписание/cron |
| `httpRequest` | исходящий HTTP |
| `code` | произвольный JS/Python |
| `set` | задать/переписать поля |
| `if` · `switch` | ветвление на 2 / на N |
| `merge` | слияние потоков |
| `splitInBatches` | обработка пачками |
| `respondToWebhook` | ответ вызывающему |

**Code-нода** получает items через `$input.all()` и обязана вернуть массив
`[{json: {...}}, ...]` — вернуть голый объект или строку значит уронить ноду:

```javascript
return $input.all().filter(item => item.json.status === 'active');
return [{ json: { total: $input.all().reduce((s, i) => s + i.json.amount, 0) } }];
```

**Merge** различает режимы: `append` (склеить всё), `mergeByIndex` (по позиции),
`mergeByKey` (по значению поля — задаются `propertyName1` / `propertyName2`),
`multiplex` (все комбинации).

**Schedule** принимает cron: `"rule": {"cronExpression": "0 9 * * *"}`.

**httpRequest** с телом и постраничным обходом:

```javascript
{
  "method": "POST", "url": "https://api.example.com/users",
  "authentication": "predefinedCredential", "credential": "myApiCredential",
  "sendBody": true, "bodyContentType": "json",
  "body": { "name": "={{ $json.name }}" },
  "options": {
    "headers": { "X-Custom-Header": "value" },
    "pagination": {
      "type": "offset",
      "paginationCompleteWhen": "receiveSpecificStatusCodes",
      "statusCodes": "404"
    }
  }
}
```

**Webhook** отдаёт данные в `$json.body`, `$json.query`, `$json.headers`;
`responseMode` = `onReceived` (ответить сразу) или `responseNode` (ответ отдаёт
`respondToWebhook`).

## Ошибки

Отдельный воркфлоу с нодой **Error Trigger** ловит падения других воркфлоу; в нём
доступны `{{ $json.error.message }}`, `{{ $json.error.node }}`,
`{{ $json.execution.id }}`.

Ретрай с нарастающей паузой, если он нужен вручную внутри Code-ноды:

```javascript
const maxRetries = 3;
for (let attempt = 1; attempt <= maxRetries; attempt++) {
  try { return result; }
  catch (error) {
    if (attempt === maxRetries) throw error;
    await new Promise(r => setTimeout(r, 1000 * attempt));
  }
}
```
