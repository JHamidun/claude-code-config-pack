---
name: api-documentation
description: "Документация API из кода: OpenAPI/Swagger, Postman, REST/GraphQL/gRPC. Триггеры: «задокументируй API». НЕ: кодбаза→openwiki; чужие репо→deepwiki."
keywords: api, documentation, openapi, swagger, postman, rest, graphql, api-docs
---

# API Documentation Generator

Генерация документации API из кода: OpenAPI/Swagger спека, Postman-коллекция,
Markdown-референс, интерактивные доки. REST, GraphQL, gRPC.

## Порядок работы

Спека первична, всё остальное производно. Postman-коллекция, Markdown-референс и
SDK-сниппеты генерируются **из** OpenAPI, а не пишутся параллельно — иначе через
две недели четыре документа расходятся, и никто не знает, какой из них правда.

1. Прочитать код эндпоинтов → собрать OpenAPI спеку.
2. Из спеки — Postman-коллекция (`npx openapi-to-postman`).
3. Из спеки — Markdown-референс для людей.
4. Поднять интерактивные доки (Swagger UI / ReDoc) поверх той же спеки.

## 1. OpenAPI

**FastAPI генерит спеку сам** — отдельный файл писать не нужно:

```python
app = FastAPI(title="My API", version="1.0.0",
              docs_url="/docs", redoc_url="/redoc")
```

Спека доступна на `/openapi.json`, Swagger UI на `/docs`, ReDoc на `/redoc`.
Качество спеки = качество аннотаций: `response_model`, `tags`, `Path(..., ge=1)`,
`Query(False, description=...)` и docstring с описанием ошибок попадают в неё
дословно. Плохая docstring → плохая спека, чинить надо код, а не спеку.

Для Express/TypeScript спека собирается из Zod-схем (`@asteasolutions/zod-to-openapi`
или аналог) — тот же принцип: схема валидации и есть источник документации.

Полный скелет спеки вручную (`components/schemas`, переиспользуемые `responses`,
`securitySchemes`, примеры в ответах) → `references/openapi-postman-templates.md`.

## 2. Postman

```bash
npx openapi-to-postman -s openapi.yaml -o postman-collection.json -p
```

Флаг `-p` подставляет примеры из спеки в тела запросов — без него коллекция
приходит с пустыми телами и её нельзя прогнать, не заполняя каждый запрос руками.

Что генератор НЕ сделает и что надо дописать: `event`-скрипт на login, который
кладёт токен в `pm.environment.set('auth_token', ...)`, и `{{auth_token}}` в
коллекционном `auth`. Без этого Runner не проходит коллекцию целиком.
Шаблон коллекции с этими скриптами → `references/openapi-postman-templates.md`.

## 3. Markdown-референс

Порядок разделов: Base URL → Authentication → Endpoints → Error Handling →
Rate Limiting → Webhooks → SDK examples → Changelog. Аутентификация до эндпоинтов,
потому что без токена ни один пример ниже не запускается.

На каждый эндпоинт: таблица параметров (тип, required, default, ограничения),
рабочий `curl`, пример успешного ответа, список кодов ошибок с телом ответа.
Полный шаблон → `references/markdown-reference-template.md`.

## 4. Интерактивные доки

**Flask** (в FastAPI встроено):
```python
from flask_swagger_ui import get_swaggerui_blueprint
bp = get_swaggerui_blueprint('/docs', '/static/openapi.json',
                             config={'app_name': "My API"})
app.register_blueprint(bp, url_prefix='/docs')
```

**ReDoc** — одна статическая страница поверх любой спеки:
```html
<redoc spec-url='/openapi.json'></redoc>
<script src="https://cdn.jsdelivr.net/npm/redoc@latest/bundles/redoc.standalone.js"></script>
```

## Правила

1. **Примеры должны запускаться.** Прогони хотя бы один `curl` из доков перед
   сдачей: нерабочий пример хуже отсутствующего — по нему пробуют и делают вывод,
   что сломан API.
2. **Документируй ошибки, а не только happy path.** Для каждого эндпоинта: какие
   коды он отдаёт и что в теле. Клиент пишет обработку по этому списку.
3. **Rate limits и заголовки лимитов** — в доки. Клиент не может угадать, где
   потолок, и упирается в него на проде.
4. **Спека версионируется вместе с кодом**, в том же PR. Отдельный «апдейт доков
   потом» не случается.
5. **SemVer для версии API**, ломающие изменения — только в мажорной.

## Инструменты

- `openapi-to-postman` — спека → коллекция
- `openapi-validator` — валидация спеки в CI
- Swagger Editor — визуальная правка спеки
- ReDoc / Stoplight — статические доки из спеки
