---
name: yandex
description: "Сервисы Яндекса по одному OAuth-токену: Метрика, Директ, Диск, Вебмастер, Wordstat, Трекер, Календарь, умный дом. Триггеры: «яндекс», «директ», «вебмастер», «метрика», «яндекс диск». НЕ Google Analytics/Ads."
allowed-tools: "Bash(python:*) Bash(curl:*) WebFetch Read Write Edit"
type: actionable
---

# Yandex Services Manager

20 сервисов Яндекса через один OAuth-токен. Полный справочник эндпоинтов (параметры,
rate limits, коды ошибок) → `references/api-endpoints.md`; тело держит доступы, CLI и грабли.

## Что понадобится

| Нужно | Платно? | Где взять |
|---|---|---|
| Аккаунт Яндекса | нет | — |
| **Своё OAuth-приложение** | нет | https://oauth.yandex.ru/client/new — чужой `client_id` не подойдёт |
| `YANDEX_OAUTH_TOKEN` | нет | по своему `client_id`, см. ниже |
| Счётчик Метрики / кабинет Директа | сам доступ бесплатен | нужен свой сайт и своя рекламная кампания; Директ тратит деньги на показах, API — нет |
| `pip install requests python-dotenv caldav vobject` | нет | — |

### Регистрация приложения (один раз, 5 минут)

1. Открой https://oauth.yandex.ru/client/new, создай приложение.
2. Отметь права под те сервисы, которые собираешься дёргать: Метрика
   (`metrika:read`, `metrika:write`), Директ (`direct:api`), Диск (`cloud_api:disk.*`),
   Вебмастер, Календарь, Трекер, умный дом. **Скоупы решают всё:** не отмеченный скоуп
   даёт 403 на живом токене, и выглядит это как «API сломался».
3. Тип приложения — «Веб-сервисы», Redirect URI можно
   `https://oauth.yandex.ru/verification_code`.
4. Забери `client_id` и получи токен, открыв в браузере:
   `https://oauth.yandex.ru/authorize?response_type=token&client_id=ТВОЙ_CLIENT_ID`
   Токен придёт в адресной строке после `#access_token=`.

## Credentials

Ключи живут в `~/.claude/.credentials.master.env` (создаётся из
`~/.claude/templates/.credentials.master.env.example`), читаются через `os.getenv`.
Токен в текст навыка, в скрипт и в git не попадает.

```bash
YANDEX_OAUTH_TOKEN=            # обязательный, см. выше
YANDEX_OAUTH_CLIENT_ID=        # свой client_id — по нему обновляют протухший токен
YANDEX_METRIKA_COUNTER_ID=     # ID своего счётчика Метрики (для metrika-подкоманд)
YANDEX_EMAIL=                  # только если нужен IMAP/SMTP или CalDAV
YANDEX_PASSWORD=               # только для SMTP-логина; лучше пароль приложения, не основной
```

Заголовок для большинства API: `Authorization: OAuth {token}`.

Токен протух (401) → открой
`https://oauth.yandex.ru/authorize?response_type=token&client_id={YANDEX_OAUTH_CLIENT_ID}`
и обнови `YANDEX_OAUTH_TOKEN`.

## Карта сервисов

| Сервис | Base URL |
|--------|----------|
| Metrika | `https://api-metrika.yandex.net` |
| Direct | `https://api.direct.yandex.com/json/v5/` |
| Mail | IMAP `imap.yandex.ru:993` / SMTP `smtp.yandex.ru:465` |
| Disk | `https://cloud-api.yandex.net/v1/disk` |
| Webmaster | `https://api.webmaster.yandex.net/v4` |
| Audience | `https://api-audience.yandex.ru/v1` |
| Calendar | CalDAV `https://caldav.yandex.ru` |
| Tracker | `https://api.tracker.yandex.net/v2` |
| Forms | `https://api.forms.yandex.net/v1` |
| IoT | `https://api.iot.yandex.net/v1.0` |
| Telemost | `https://cloud-api.yandex.net/v1/telemost` |
| Wordstat | `https://api.direct.yandex.com/v4/json/` (legacy v4!) |

Остальные (Sprav, PromoPages, AdFox, MediaMetrika, AppMetrica, Pay, BSAPI, Partner)
→ `references/api-endpoints.md`.

## CLI

`scripts/yandex_api.py` — субкоманды: `metrika · disk · webmaster · iot · direct ·
audience · telemost · calendar · wordstat`.

```bash
python ~/.claude/skills/yandex/scripts/yandex_api.py metrika report --metrics "ym:s:visits,ym:s:pageviews" --date1 "7daysAgo" --date2 "today"
python ~/.claude/skills/yandex/scripts/yandex_api.py disk ls /
python ~/.claude/skills/yandex/scripts/yandex_api.py iot devices
python ~/.claude/skills/yandex/scripts/yandex_api.py webmaster sites
```

Свой счётчик Метрики, если не знаешь его ID:

```bash
curl -H "Authorization: OAuth $YANDEX_OAUTH_TOKEN" \
  "https://api-metrika.yandex.net/management/v1/counters?per_page=100"
```

Прямой вызов — обычный `requests` с заголовком `OAuth {token}`; справочники
метрик и дименсий Метрики (`ym:s:*`, `ym:pv:*`, UTM) — в `references/api-endpoints.md`.

## Грабли по сервисам (проверено на практике)

**Disk — upload двухшаговый и PUT только RAW BODY:**

```python
# GET /resources/upload?path=/file.txt&overwrite=true → href
# ❌ requests.put(href, files={'file': f})  — создаёт ПУСТОЙ файл (size:0, mime:text/plain), но возвращает 201 OK
# ✅ with open(path,'rb') as f: requests.put(href, data=f.read(), timeout=600)
# после заливки проверить: GET /resources?path=...&fields=size,mime_type — size:0 → перезалить raw PUT
```

**Metrika:**

- E-commerce-метрики → 400, если модуль не включён на счётчике.
- Page speed (`ym:pv:avgPageLoadTime`) в API не работает, хотя есть в документации.
- Максимум ~20 метрик на запрос — цели батчить по 20 (`ym:s:goal{id}reaches`).
- `ym:pv:` — уровень страниц, `ym:s:` — сессий; не смешивать в одном запросе.
- Windows: `PYTHONIOENCODING=utf-8` + `sys.stdout.reconfigure(encoding='utf-8')`.
- Дименсия `ym:s:referer` отдаёт полные URL источников — включая внутренние порталы
  компаний, откуда к тебе приходят. Это ценный срез, но в отчёт, который уйдёт наружу,
  такие URL класть нельзя: они выдают клиента.
- Глубокий отчёт по 9 срезам (daily, источники, UTM, демография, гео, устройства, цели,
  поисковые фразы, рефереры) → рецепт целиком в `references/metrika-deep-analytics.md`.

**Direct:** авторизация `Bearer {token}` (не `OAuth`!), все запросы POST с JSON-телом,
заголовки `Accept-Language: ru` и опционально `Client-Login`.

**Mail:** OAuth в IMAP — через XOAUTH2:
`auth_string = f"user={EMAIL}\x01auth=Bearer {TOKEN}\x01\x01"; imap.authenticate("XOAUTH2", lambda x: auth_string.encode())`.
SMTP-логин — паролем (`YANDEX_PASSWORD`; заведи пароль приложения, а не основной пароль аккаунта).

**Calendar:** библиотека `caldav`, username = email, password = OAuth-токен.

**Webmaster:** сначала `GET /user` → `user_id`, все остальные пути от него.

**Tracker:** обязательный заголовок `X-Org-ID` (или `X-Cloud-Org-ID`).

**Wordstat:** живёт в legacy Direct API v4 — методы `CreateNewWordstatReport` →
`GetWordstatReportList` (ждать готовности) → `GetWordstatReport` → `DeleteWordstatReport`.

## Ошибки

401 — обновить токен (см. выше) · 403 — не хватает OAuth-скоупов у приложения ·
429 — backoff и retry · 503 — повторить через 30 с.

## Performance-маркетинг: цели и офлайн-конверсии

API-часть работы с целями Метрики и передачей квал-лидов. За **методологией**
(автостратегии, обучение кампаний, масштабирование) → навык `yandex-direct-pro-ru`.

| Reference | Что внутри | Когда читать |
|-----------|-----------|--------------|
| `references/offline-conversions.md` | 6-шаговая передача квал-лидов из CRM в Метрику через Client ID: `getClientID` → хранение в CRM → `POST .../offline_conversions/upload` (пример CSV) → цель «квалифицированный лид» → автостратегия Директа | «передать Client ID», «офлайн-конверсии», оптимизация на квал-лиды |
| `references/metrika-goals-setup.md` | Автоцели vs JS-события; микро/макроконверсии (60 с/90 с/скролл ≥70%); составная цель (форма ИЛИ квиз ИЛИ «Спасибо» ИЛИ клик по телефону); создание целей через API | «настроить цель Метрики», «составная цель», «микроконверсии» |

Связанные навыки: `yandex-direct-pro-ru` (методология Директа) ·
`capi-no-code-setup` (server-side конверсии без кода) · `vk-ads-pro-ru` (дальнейшая
обработка семантики Wordstat под ключи VK: чистка операторов, ВЧ-мусор, мягкая
минусовка). Здесь только выгрузка фраз через API — что с ними делать дальше,
решается в кабинете нужной площадки.
