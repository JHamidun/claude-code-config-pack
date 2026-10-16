---
description: Добавление аутентификации в проект
argument-hint: "[method] (jwt|oauth2|session|firebase|auth0)"
---

# Add Auth: $ARGUMENTS

Методы: `jwt` (stateless) · `oauth2` (Google, GitHub) · `session` (stateful,
Redis-стор) · `firebase` · `auth0` · `passport` (Node). Метод не указан —
предложи исходя из стека и того, нужен ли выход из системы на сервере
(нужен → session, не нужен → jwt).

## Что собрать

1. **User-модель**: email и username уникальные с индексами, `hashed_password`,
   `is_active`, `is_superuser`, таймстемпы. Пароль в открытом виде не хранится
   и не логируется нигде.
2. **Хеширование**: bcrypt (passlib `CryptContext` / `bcrypt` с salt rounds ≥10).
   Не sha256, не md5 — они считаются слишком быстро для перебора.
3. **Токены**: access короткоживущий (30 мин), refresh отдельный (7 дней).
   В payload — только идентификатор (`sub`) и `exp`, никаких ролей и почт:
   payload не зашифрован, его читает кто угодно.
4. **Middleware/dependency** проверки токена: единый 401 для «нет токена»,
   «токен битый» и «пользователя нет» — разные ответы дают перебор аккаунтов.
5. **Роуты**: `POST /auth/register`, `POST /auth/login`, `GET /auth/me`,
   `POST /auth/refresh`, `POST /auth/forgot-password`, `POST /auth/reset-password`.
6. **Тесты**: регистрация, логин, доступ к защищённому роуту с токеном и БЕЗ
   него (негативный кейс обязателен — без него тест зелёный при выключенной
   проверке).

## Жёсткие границы

- Секреты только из окружения. Захардкоженный `SECRET_KEY` в коде — блокер,
  даже в примере: он переезжает в прод копипастом.
- `/forgot-password` отвечает одинаково независимо от того, есть ли такой
  email («если адрес существует, письмо отправлено») — иначе форма становится
  перечислителем пользователей.
- Session-cookie: `httpOnly: true`, `secure` в проде, разумный `maxAge`.
- Password reset токен одноразовый и с истечением.

## Переменные окружения

```
JWT_SECRET · JWT_ALGORITHM=HS256 · ACCESS_TOKEN_EXPIRE_MINUTES=30 · REFRESH_TOKEN_EXPIRE_DAYS=7
GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET · GITHUB_CLIENT_ID / GITHUB_CLIENT_SECRET
SESSION_SECRET · REDIS_URL
SMTP_HOST · SMTP_PORT · SMTP_USER · SMTP_PASSWORD   (для сброса пароля)
```

## Отдай в конце

Метод, созданные файлы, список роутов, добавленные зависимости (для FastAPI:
`python-jose[cryptography]`, `passlib[bcrypt]`, `python-multipart`) и шаги:
задать реальный секрет в `.env` → миграция под User → прогнать тесты →
проверить OpenAPI-доки.
