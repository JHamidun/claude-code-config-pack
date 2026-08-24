---
name: publora-post
description: "Publora: публикация в 10 соцсетей по API + эксклюзивы — LinkedIn-аналитика, реакции и комментарии на чужие посты. Триггеры: «реакции linkedin», «запланируй пост через publora»."
---

# Publora Post — публикация и аналитика по API

Публикация, планирование и аналитика постов через [Publora](https://publora.com) (MCP + REST).
**Платформа — это параметр**: механика одна для всех, различаются только лимиты и `platformSettings`.

> **Что понадобится.** `PUBLORA_API_KEY` — свой, из кабинета Publora
> (Settings → API). Сервис платный: Starter 15 постов/мес (X недоступен),
> Pro 100, Premium 500. Без ключа навык всё равно полезен: он отдаёт готовый
> текст для ручной вставки (manual-режим в `scripts/lib/backend_selector.py`).
>
> Альтернатива без абонплаты — **self-hosted Postiz** (`scripts/lib/postiz_client.py`):
> хостишь сам, `POSTIZ_API_KEY` + `POSTIZ_BASE_URL` со своим доменом.
> Ни один хост в коде не зашит: без `POSTIZ_BASE_URL` клиент упадёт с внятной ошибкой,
> а не уедет на чужой сервер.

## Разграничение (не перепутай)

Если развёрнут свой Postiz — обычную публикацию дешевле гнать через него, а Publora
оставить на то, чего Postiz не умеет **принципиально**:

1. **LinkedIn-аналитика** — `linkedin_post_stats`, `linkedin_account_stats`, `linkedin_followers`, `linkedin_profile_summary` (+ REST `/linkedin-post-statistics`).
2. **LinkedIn-реакции и комментарии** — `linkedin_create_reaction`, `linkedin_create_comment` (+ REST `/linkedin-comments`, `/linkedin-reactions`).
3. **Telegram-доставка через Publora** — в Postiz платформы Telegram нет вообще
   (для собственного канала обычно проще Bot API — навык `tg-bot-publish`).

Обычную публикацию (X, LinkedIn, Instagram, TikTok, Threads, Bluesky, YouTube, Facebook, Mastodon)
и всё, чего в Publora нет (Reddit, Pinterest, Slack, Discord, LinkedIn Pages), — через свой **Postiz**,
если он развёрнут.

- **publora-post (этот скилл)** — механика доставки на любую платформу + LinkedIn-эксклюзивы.
- **tg-post** — пишет посты в личный Telegram-канал твоим голосом. Контент — там, доставка — здесь или в `tg-bot-publish`.
- **linkedin-post-author / linkedin-post-writer / linkedin-comment-drafter** — контент и стратегия LinkedIn; сюда приходят только за доставкой и статистикой.

## Как пользоваться (общая механика)

1. **MCP**: сервер `publora` (`https://mcp.publora.com`, `Authorization: Bearer $PUBLORA_API_KEY`).
2. **REST fallback** (если MCP недоступен или нужны `platformSettings`): `https://api.publora.com/api/v1`, заголовок `x-publora-key: sk_...` (НЕ `Authorization: Bearer`).
3. **Подключённые аккаунты**: `GET /platform-connections` → берёшь platform ID нужной платформы.
4. **Публикация**: `create_post` c `platforms: ["<platform-id>", ...]` (можно несколько платформ разом), `content`, `scheduledTime` (ISO 8601, ОБЯЗАТЕЛЕН — для «сейчас» ставь now + 1 мин).
5. **Медиа**: `get_upload_url` (`postGroupId`, `fileName`, `contentType`, `type: image|video`) → PUT файла по presigned URL.
6. **Управление**: `list_posts` / `update_post` / `delete_post`.
7. **LinkedIn аналитика и engagement**: `linkedin_post_stats`, `linkedin_account_stats`, `linkedin_followers`, `linkedin_profile_summary`, `linkedin_create_reaction`, `linkedin_create_comment` (+ REST `/linkedin-comments`, `/linkedin-reactions`, `/linkedin-post-statistics`).
8. **Платформо-специфика** (лимиты, форматы, настройки, troubleshooting) — в references ниже.

### Platform ID форматы

| Платформа | ID | Пример |
|---|---|---|
| X/Twitter | `twitter-{id}` | `twitter-123456789` |
| Threads | `threads-{id}` | `threads-12345` |
| Instagram | `instagram-{id}` | `instagram-11223344` |
| TikTok | `tiktok-{id}` | `tiktok-99887766` |
| Bluesky | `bluesky-{did}` | `bluesky-did:plc:abc123xyz` |
| Telegram | `telegram-{chat_id}` | `telegram-1001234567890` |
| LinkedIn | `linkedin-{id}` | `linkedin-XXXXXXXXXX` |
| YouTube | `youtube-{channel_id}` | `youtube-UCxxx` |
| Facebook | `facebook-{page_id}` | `facebook-112233445566` |
| Mastodon | `mastodon-{id}` | `mastodon-456` |

### Ключевые лимиты-грабли (полные таблицы в references)

- X: 280 симв (emoji = 2), авто-треддинг, ручной разрыв `---`, видео ≤ 2 мин, нужен платный Pro-план.
- Threads: 500 симв, максимум 1 хэштег, карусель 2-10 картинок.
- Instagram: **только JPEG** (PNG упадёт), только Business-аккаунт, текст-only постов нет.
- TikTok: только видео, ≥ 23 FPS, неаудированное приложение = только `SELF_ONLY` (приватные).
- Bluesky: 300 симв, картинки ~1 МБ, app password (не основной пароль).
- Telegram (Bot API): caption ≤ 1 024 симв при медиа, видео ≤ 50 МБ, бот должен быть админом.
- LinkedIn: 3 000 симв (первые 210 видимы), никакого rich text, карусель = PDF-документ.
- Планы Publora: Starter 15 постов/мес (X недоступен), Pro 100, Premium 500.

## References (полные тела бывших скиллов)

| Платформа / задача | Файл |
|---|---|
| X/Twitter | `references/x-post/SKILL.md` |
| Threads | `references/threads-post/SKILL.md` |
| Instagram | `references/instagram-post/SKILL.md` |
| TikTok | `references/tiktok-post/SKILL.md` |
| Bluesky | `references/bluesky-post/SKILL.md` |
| Telegram | `references/telegram-post/SKILL.md` |
| YouTube / Facebook / Mastodon | `references/social-post/SKILL.md` |
| LinkedIn публикация + comments/reactions REST (url_parser, PubloraClient, реакции INTEREST-маппинг) | `references/linkedin-post/SKILL.md` |
| LinkedIn аналитика (post/account stats, followers, thread engagement, окно ответа автора) | `references/linkedin-analytics/SKILL.md` |

## Инструменты внутри навыка

| Файл | Что делает |
|---|---|
| `scripts/lib/url_parser.py` | LinkedIn URL → URN (пост, коммент, share). Запусти без аргументов — прогонит примеры |
| `scripts/lib/publora_client.py` | REST-клиент Publora (посты, комменты, реакции, статистика) |
| `scripts/lib/postiz_client.py` | REST-клиент своего Postiz (только посты; реакций и комментов на чужие посты у него нет) |
| `scripts/lib/backend_selector.py` | Выбор бэкенда по переменным окружения: `postiz` → `publora` → `diy` → `manual` |
| `scripts/lib/approval.py` | Карточка подтверждения перед отправкой |
| `scripts/post_comment.py` | CLI: комментарий или реакция по ссылке на пост |

Подробности — в `references/linkedin-post/SKILL.md`.

Этими же `lib/*` пользуются `linkedin-post-writer` и `linkedin-comment-drafter`
(`lib.active_backend()`, `lib.url_parser`, `lib.approval`) — если навык удалить,
они останутся без бэкенда доставки.
