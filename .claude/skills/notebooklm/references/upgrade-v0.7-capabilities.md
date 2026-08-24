# notebooklm-py v0.7.x — upgrade & new capabilities

> Пакет тот же самый, на котором построен навык (`teng-lin/notebooklm-py`) — просто основной
> текст написан под запиненную старую версию. Мигрировать ничего не нужно, только апгрейд
> плюс новые возможности авторизации и MCP.

## Version delta (сверялось на 0.3.4 vs 0.7.3)

Свою версию смотри через `notebooklm --version`, актуальную — на PyPI.

| | 0.3.4 | 0.7.3 |
|---|---|---|
| MCP server (`notebooklm mcp`) | ❌ нет | ✅ есть (stdio + HTTP) |
| Master-token auth | ❌ (только `auth check`) | ✅ self-healing токен |
| Browser-cookie import | ❌ | ✅ Chrome/Edge без Playwright |
| REST API server (FastAPI localhost) | ❌ | ✅ (экспериментально) |
| Артефакты (audio/video/slide-deck/quiz/flashcards/infographic/data-table/mind-map/report/cinematic-video) | ✅ уже все | ✅ |
| `source add-research` / `research` group / `share` / `metadata` | ✅ уже есть | ✅ |

Вывод: генерация артефактов полная уже в 0.3.4. **Реальная ценность 0.7.x = авторизация
(снимает главную боль навыка) + MCP-сервер (offload тяжёлого анализа мимо своего токен-бюджета).**

## Что чинит апгрейд

Основной текст навыка прямо жалуется:

> "Long-running operations (`artifact wait` for 10+ min, multilang loops) WILL hit auth expiry.
> Solution: refresh tokens between calls."

Костыль на 0.3.4 — Playwright-скрипт `refresh-nb-auth.py` перед каждым вызовом CLI.

**Master-token auth в 0.7.x self-heals истёкшую сессию**: чеканит свежие cookies по запросу.
Это ровно то, что нужно headless-серверу и любому расписанию, где генерация идёт 10-25 минут
и обязана пережить истечение `storage_state`.

## Апгрейд — команда + ОБЯЗАТЕЛЬНАЯ верификация

⚠️ **Если от CLI зависит что-то работающее по расписанию — не апгрейдить вслепую.**
Флаги CLI между версиями уже менялись (в основном тексте есть целая таблица переименований),
и молча упавший ночной прогон выглядит не как ошибка, а как «ничего не сгенерировалось».

```bash
export PYTHONIOENCODING=utf-8

# 1. Апгрейд (чистый Python, MIT, без GPU и весов)
python -m pip install -U "notebooklm-py[browser]"   # browser-extra тянет Playwright ~170MB Chromium при первом login

# 2. Верификация версии
notebooklm --version

# 3. СВЕРИТЬ, что флаги не поехали (сравнить с SKILL.md):
notebooklm generate audio --help          # проверь --format / --length / -n живы
notebooklm download audio --help          # проверь позиционный output + -n
notebooklm artifact wait --help           # проверь --timeout / --interval / --json
notebooklm language --help

# 4. Проверить новые группы
notebooklm auth --help    # ждём token-минтинг подкоманды (master-token)
notebooklm mcp --help     # ждём serve (stdio + --transport http)

# 5. Smoke-тест на черновом ноутбуке, не на боевых данных:
notebooklm auth check --test --json
```

**Если флаги изменились** — обнови свои скрипты ДО того, как оставишь новую версию.
Откат: `pip install notebooklm-py==0.3.4`.

## Master-token auth (headless / расписание)

Заменяет Playwright-костыль `refresh-nb-auth.py`. Точный синтаксис сверь через
`notebooklm auth --help` после апгрейда; по README доступны три пути:

- `notebooklm login` — интерактивный Playwright (как в 0.3.4), ЛИБО
- **cookie-import** — переиспользовать живую сессию Chrome/Edge без Playwright, ЛИБО
- **master-token** — долговечный токен, чеканит свежие cookies on-demand, самовосстанавливается.
  Для сервера и cron это предпочтительный режим: убирает цикл «истекло → refresh → повтор».
- Мульти-аккаунт профили: переключение Google-аккаунтов без релогина.

## MCP server — offload тяжёлого анализа

`notebooklm mcp serve` (stdio) даёт агенту прямой доступ к ноутбукам как к инструменту.
Кейс: делегировать тяжёлый анализ и RAG внутрь NotebookLM (бесплатно, вне своего токен-бюджета),
а агент только оркестрирует и полирует результат.

```bash
# Локальный stdio (для Claude Code / Desktop)
notebooklm mcp serve

# Подключить как MCP-сервер (в интерактивной сессии):
claude mcp add-json notebooklm '{"command":"notebooklm","args":["mcp","serve"]}'

# Удалённый HTTP-коннектор (self-host за туннелем, для мобильного клиента):
notebooklm mcp serve --transport http --host 0.0.0.0
```

Локальный stdio MCP — дёшево и аддитивно, подключать ПОСЛЕ апгрейда и проверки auth.
Удалённый HTTP — только если реально нужен доступ с телефона; помни, что наружу при этом
торчит доступ к твоему Google-аккаунту, так что без туннеля или авторизации не выставлять.

## Гоча: недокументированные Google API (важно)

> "This library uses **undocumented Google APIs that can change without notice**…
> Not affiliated with Google… APIs may break… Rate limits apply."

- NotebookLM в 2026 ребрендился в **Gemini Notebook** — внутренние эндпоинты дрейфуют,
  отсюда и переименования команд CLI. Ожидай поломок при апдейтах Google; держи pin известной
  рабочей версии и апгрейдь осознанно.
- Rate limits недокументированы (~50 req/hour эмпирически). Multilang-циклы идут близко к границе.
- Платного ключа нет: авторизация — обычный Google-логин, NotebookLM бесплатен для личного
  использования. Прокси и VPN не требуются.

## Итоговая рекомендация

**Дополнить, не мигрировать.** Ценность 0.7.x — self-healing auth (снимает главный костыль
навыка) и локальный MCP. Апгрейд лёгкий (чистый Python), но если от CLI зависит расписание,
выполняй с верификацией флагов по чек-листу выше, а не вслепую. Фичи генерации
(video / slides → pptx / quiz и прочее) есть уже в 0.3.4 — там дублирования нет.
