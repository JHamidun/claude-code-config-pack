# Miro REST API v2 — то, чего не умеет MCP

> База: `https://api.miro.com`. CLI-обёртка: `python ~/.claude/tools/miro_client.py`.
> REST нужен там, где MCP бессилен: **коннекторы, теги, группы, app cards, embeds**,
> точечная правка элемента по id и скриптовые пайплайны (не тратят дневную квоту MCP).

## Токен за 5 минут (Enterprise не нужен)

1. miro.com → аватар → **Settings** → вкладка **Your apps**
   (прямая ссылка: `https://miro.com/app/settings/user-profile/apps`)
2. **+ Create new app**. Если нет Developer team — Miro предложит создать (бесплатная песочница)
3. Галочку **«Expire user authorization token» НЕ ставить** — иначе токен живёт 60 минут
   и его придётся обновлять через `POST /v1/oauth/token` с `grant_type=refresh_token`
4. **Permissions** → отметить `boards:read` и `boards:write`
5. Внизу страницы → **«Install app and get OAuth token»** → выбрать команду, где лежат доски
6. Положить в `~/.claude/.credentials.master.env` как `MIRO_ACCESS_TOKEN=...`

Заголовок запроса: `Authorization: Bearer <token>`.

## Эндпоинты по группам

| Группа | Основное |
|---|---|
| Доски | `GET/POST /v2/boards`, `GET/PATCH/DELETE /v2/boards/{id}`, `PUT /v2/boards/{id}` (копия) |
| Элементы (общее) | `GET /v2/boards/{id}/items`, `GET/PATCH/DELETE .../items/{item_id}` |
| Стикеры | `/v2/boards/{id}/sticky_notes` |
| Шейпы, текст, фреймы, карточки | `/shapes`, `/texts`, `/frames`, `/cards` |
| Изображения, документы, embeds | `/images`, `/documents`, `/embeds` |
| **Коннекторы** | `GET/POST /v2/boards/{id}/connectors`, `PATCH/DELETE .../connectors/{cid}` |
| **Теги** | `/v2/boards/{id}/tags`, привязка `POST /items/{item_id}?tag_id=` |
| **Группы** | `/v2/boards/{id}/groups` |
| App cards | `/v2/boards/{id}/app_cards` |
| Участники и доступ | `/v2/boards/{id}/members` |
| Массовое создание | `POST /v2/boards/{id}/items/bulk` — до 20 элементов за вызов |

## Лимиты — кредитная система

Бюджет: **100 000 кредитов в минуту на пару пользователь-приложение.**

| Уровень | Кредитов за вызов | Запросов/мин | Примеры |
|---|---|---|---|
| L1 | 50 | ~2000 | чтение доски, чтение элемента, все теги, участники |
| L2 | 100 | ~1000 | создание/правка любого элемента, список items, коннекторы, группы |
| L3 | 500 | ~200 | создание и удаление доски, удаление элемента, шаринг |
| L4 | 2000 | ~50 | копирование доски, экспорт, аудит-логи |

Заголовки ответа: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`.

**Важно про bulk:** `POST /items/bulk` считается **за каждый элемент** по L2 — 20 штук = 2000 кредитов.
Он экономит сетевую задержку, но **не кредиты**.

## Ограничения бесплатного плана

- через `POST /v2/boards` создаётся не более **3 командных досок**
- `GET /v2/boards` видит только доски, расшаренные с владельцем токена
  (режим «видеть все приватные доски компании» — Enterprise + Company Admin)

## Только Enterprise

`/v2/orgs/*` (организации, команды, проекты, группы пользователей), аудит-логи,
SCIM-провижининг, legal hold и eDiscovery, классификация данных, а также **экспорт доски**
(`/v2/orgs/{org_id}/boards/export/jobs`, требует роль Company Admin и включённый eDiscovery).

**Экспорт без Enterprise:** через REST невозможен. Варианты — выгрузка из UI (PDF / картинка / CSV),
Web SDK внутри board-приложения, либо снять `viewLink` headless-браузером
(`skills/playwright-automation`).

## Команды CLI

```bash
python ~/.claude/tools/miro_client.py whoami                    # проверить токен
python ~/.claude/tools/miro_client.py boards                    # список досок
python ~/.claude/tools/miro_client.py board <board_id>          # инфо о доске
python ~/.claude/tools/miro_client.py items <board_id> --type sticky_note --all
python ~/.claude/tools/miro_client.py sticky <board_id> --text "Идея" --x 0 --y 0
python ~/.claude/tools/miro_client.py shape <board_id> --shape rectangle --text "Этап"
python ~/.claude/tools/miro_client.py frame <board_id> --title "Спринт 1"
python ~/.claude/tools/miro_client.py connect <board_id> --from <id> --to <id>
python ~/.claude/tools/miro_client.py tags <board_id>
python ~/.claude/tools/miro_client.py bulk <board_id> --file items.json
python ~/.claude/tools/miro_client.py raw GET /v2/boards/<id>/connectors
```

У каждой команды есть `--json`. Без `MIRO_ACCESS_TOKEN` клиент печатает пошаговую инструкцию
по получению токена и выходит с кодом 2 — без трейсбека.

## Совместный сценарий с MCP

Типовой порядок: **разложить доску через MCP** (`layout_create` одним вызовом — быстро и дёшево),
**соединить элементы стрелками через REST** (`connect`), потому что коннекторов в MCP нет.
Id элементов после `layout_create` берутся через `board_list_items` или REST `GET /items`.
