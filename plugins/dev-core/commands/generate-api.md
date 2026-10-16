---
description: Генерация полного CRUD API для ресурса
argument-hint: "[framework] [resource-name]"
---

# Generate API: $ARGUMENTS

Первый аргумент — фреймворк, второй — ресурс в единственном числе
(`/generate-api fastapi users`, `/generate-api express products`).

Фреймворки: `fastapi`, `django-rest`, `express`, `nest`, `gin`, `actix`,
`spring`, `laravel`, `rails`. Фреймворк не указан — определи по кодбазе
(зависимости, структура каталогов), не спрашивай лишний раз.

## Что сгенерировать

Слои раскладывай по конвенции проекта; если проект пустой — по слоям
фреймворка (FastAPI: `app/models/`, `app/schemas/`, `app/services/`,
`app/routers/`, `app/tests/`).

1. **Модель/entity** — id, поля ресурса, `created_at`/`updated_at` с
   автообновлением, индекс на поле поиска.
2. **Схема/DTO** — раздельно Create и Update: в Update все поля опциональны,
   иначе PATCH-семантика ломается и частичное обновление затирает поля.
   Ограничения длины и обязательности — в схеме, а не в контроллере.
3. **Сервис** — CRUD-операции, возвращают `None`/`False` на «не найдено»,
   а не бросают HTTP-исключения: слой БД не должен знать про HTTP.
4. **Роутер/контроллер** — 5 эндпоинтов, коды: 201 на create, 204 на delete,
   404 на отсутствующий id, 400 на невалидный вход. Список — с пагинацией
   (`skip`/`limit` с валидацией границ или `page`/`limit` + meta с total и
   числом страниц).
5. **Тесты** — по тесту на каждый эндпоинт, включая 404-ветку. Тест create
   проверяет и код, и тело ответа.
6. **Миграция** (если проект с миграциями) — upgrade + downgrade, индексы
   создаются и удаляются симметрично.
7. **Регистрация роутера** в главном приложении — иначе всё выше мертво.

## Отдай в конце

```
Created files: <список путей>

GET    /<plural>       List (paginated)
GET    /<plural>/{id}  Get one
POST   /<plural>       Create
PUT    /<plural>/{id}  Update
DELETE /<plural>/{id}  Delete

Next: миграции (напр. alembic upgrade head) → тесты → OpenAPI-доки
(FastAPI: http://localhost:8000/docs)
```
