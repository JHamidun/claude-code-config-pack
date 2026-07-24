# Yandex Forms — официальный REST API

База: `https://api.forms.yandex.net/v1`
OpenAPI (полный, 57 методов / 260 схем) сохранён:
`${WORKSPACE}/yandex_forms_ref/openapi_official.json`
(openapi.json публичный — отдаёт 200 без авторизации).

## Авторизация
- OAuth-токен Яндекса со scope **`forms:write`** (для чтения — `forms:read`).
- Заголовок организации: **`X-Org-Id`** (Яндекс 360) ИЛИ **`X-Cloud-Org-Id`** (Yandex Cloud).
- `Authorization: OAuth <token>`.

Текущий `YANDEX_OAUTH_TOKEN` из кред:
- `/v1/users/me/` работает → `your-email@example.com`, `cloud_uid: <ваш uid>`.
- Но БЕЗ scope `forms:write` + корректного `X-Org-Id` создание форм даёт 401/403.
- Чтобы включить: перевыпустить токен с `forms:write` на oauth.yandex.ru и узнать Org-Id
  (Яндекс 360 admin / `/v1/...` users me содержит подсказки по org).

## Ключевые эндпоинты
| Метод | Эндпоинт |
|---|---|
| Создать форму | `POST /surveys/` |
| Добавить вопрос | `POST /surveys/{id}/questions/` |
| Опубликовать | `POST /surveys/{id}/publish/` |
| Список вопросов | `GET  /surveys/{id}/questions/` |
| Ответы | `GET  /surveys/{id}/answers/` |
| Текущий юзер | `GET  /users/me/` |

## Когда применять
Официальный API предпочтителен для headless/CI (без браузера). Пока нет токена с
`forms:write` + Org-Id — использовать ПУТЬ 1 (gateway через залогиненный браузер,
см. `gateway_api.md`). Как только токен появится — переписать билдер на чистый Python
по схемам из openapi_official.json.
