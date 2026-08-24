---
name: openwiki
description: "Агентная wiki кодбазы CLI openwiki (langchain-ai) + авто-PR доков в CI: openwiki/, AGENTS.md. Триггеры: «agent wiki для репо». НЕ чужой репо→deepwiki."
---

# OpenWiki — agent wiki для кодбазы

CLI от **langchain-ai** (`openwiki`, npm, TypeScript, ранняя v0.2.0). Генерирует и **поддерживает в свежем виде** документацию репо, заточенную под кодинг-агентов, и обновляет её PR-ами в CI. Заполняет пробел «большой репо без актуальных доков» — агент перестаёт слепо гриповать по коду.

## Когда использовать / когда НЕТ

| Задача | Инструмент |
|--------|-----------|
| Прозаическая wiki по всему репо (архитектура/workflows/domain) + свежесть через CI | **openwiki** (этот skill) |
| Граф вызовов, callers/callees, blast-radius/impact | `codegraph` (структура, не проза — комплементарен) |
| Fetch доков ЧУЖОГО GitHub-репо | `deepwiki` (gitmcp.io) |
| OpenAPI/Swagger/Postman из API-кода | `api-documentation` |

Не дублирует ничего из перечисленного: openwiki = **пишет и держит свежей** прозу+навигацию внутри своего репо; codegraph даёт структурный граф; deepwiki читает удалённое; api-documentation — только API-спеки.

## Установка

```sh
npm install -g openwiki        # или: pnpm add -g openwiki
```

Windows: ставить именно через npm/pnpm (не bun — он тянет компиляцию нативного `better-sqlite3` и требует VS Build Tools с C++ workload). Если нативная сборка `better-sqlite3` падает — поставить Desktop development with C++ и повторить, либо запускать openwiki на своём сервере/CI-раннере (Node 22).

## Code mode — быстрый старт (локально)

```sh
cd /path/to/repo
openwiki --init          # первый прогон: выбор провайдера/ключа/модели, затем генерит openwiki/
openwiki --update        # инкрементальное обновление доков (создаёт openwiki/ если нет)
openwiki -p "..."        # one-shot, неинтерактивно (печатает финальный ответ)
```

Что создаётся в репо:
- `openwiki/` — quickstart.md + architecture / workflows / domain / operations / integrations / testing / source maps.
- `openwiki/INSTRUCTIONS.md` — **ручной** бриф scope/приоритетов wiki (openwiki его читает, но НЕ переписывает при обычных прогонах).
- `AGENTS.md` и `CLAUDE.md` в корне репо — openwiki правит ТОЛЬКО свой блок `<!-- OPENWIKI:START -->…<!-- OPENWIKI:END -->`, остальное содержимое не трогает (при первом разе — дописывает блок). Значит существующий рукописный CLAUDE.md проекта переживёт прогон.

Конфиг/секреты хранятся в `~/.openwiki/.env` (не в репо; коннектор-конфиги ссылаются на имена env-переменных, не на значения).

## Провайдер модели — приоритет по стоимости

openwiki требует LLM-провайдера. Порядок предпочтения, чтобы НЕ жечь метрируемый API:

1. **ChatGPT-подписка (0 метрируемого API)** — провайдер `openai-chatgpt`, тянет квоту Codex из ChatGPT-плана, а не per-token API:
   ```sh
   OPENWIKI_PROVIDER=openai-chatgpt openwiki code --init   # браузер-логин auth.openai.com
   ```
2. **Локальный гейтвей (0 токенов)** — `openai-compatible` на `http://127.0.0.1:GATEWAY_PORT/openai/v1` (Codex-backed; свой локальный OpenAI-совместимый прокси, в пак не входит):
   ```sh
   OPENWIKI_PROVIDER=openai-compatible
   OPENAI_COMPATIBLE_API_KEY=local            # гейтвей игнорит значение, но поле обязательно
   OPENAI_COMPATIBLE_BASE_URL=http://127.0.0.1:GATEWAY_PORT/openai/v1
   OPENWIKI_MODEL_ID=gpt-5.4-mini
   openwiki --init
   ```
   Оговорка: `openai-compatible` ходит через chat-completions; tool-calling openwiki через гейтвей НЕ верифицирован — прогнать на маленьком репо и проверить, что доки реально сгенерились, прежде чем гнать на большой боевой репо. Если tool-calling ломается — fallback на п.1 или п.3.
3. **CI (гейтвей недоступен с раннера)** — дешёвая метрируемая модель или Vertex AI:
   - OpenRouter + дешёвая модель (в шаблоне `z-ai/glm-5.2`): `OPENWIKI_PROVIDER=openrouter`, `OPENROUTER_API_KEY`, `OPENWIKI_MODEL_ID=...`.
   - Gemini AI Studio: `OPENWIKI_PROVIDER=gemini`, `GEMINI_API_KEY` (ключ `GOOGLE_API_KEY`/AI Studio есть).
   - Vertex AI ADC (без ключа): `OPENWIKI_PROVIDER=gemini-enterprise`, `GOOGLE_CLOUD_PROJECT` + workload-identity/ADC.
   - Anthropic доступен (`OPENWIKI_PROVIDER=anthropic`, `ANTHROPIC_API_KEY`), но это метрируемый API — не через Max-подписку. Использовать только если ключ уже оплачен.

Custom модель — всегда `OPENWIKI_MODEL_ID`. Дефолт онбординга — OpenAI `gpt-5.6-terra` (метрируемый — сменить на п.1/2).

## CI: авто-PR с обновлением доков

Скопировать шаблон под свой провайдер Git — они лежат в `examples/` upstream-репозитория
(`git clone --depth 1 https://github.com/langchain-ai/openwiki ./work/openwiki`):
- GitHub Actions → `.github/workflows/openwiki-update.yml`
- GitLab CI → `.gitlab-ci.yml` (или include)
- Bitbucket → `bitbucket-pipelines.yml` + расписание custom-pipeline

GitHub-шаблон (суть): по cron (напр. `0 9 * * *`) ставит Node 22 + `npm i -g openwiki`, запускает `openwiki code --update --print`, затем `peter-evans/create-pull-request` открывает PR в ветку `openwiki/update` с `add-paths: openwiki, AGENTS.md, CLAUDE.md, .github/workflows/openwiki-update.yml`. Требует `permissions: contents:write, pull-requests:write` и секрет ключа провайдера. `--init` в CI не нужен — `--update` создаёт доки при первом прогоне.

**Всегда** ставить `OPENWIKI_TELEMETRY_DISABLED: "1"` (или `DO_NOT_TRACK=1`) в env workflow.

## Каким репо это нужно в первую очередь

Кандидаты №1 — большие репо с отстающими доками: монорепо с многими ветками и «несвязанными историями», проекты с несколькими админками и разрозненными модулями. openwiki-wiki + свежий AGENTS.md/CLAUDE.md реально ускоряет навигацию кодинг-субагентов по таким репо.

Порядок внедрения (решение владельца репо — НЕ гнать вслепую, это спенд токенов + запись в боевые репо + PR):
1. Пилот на маленьком/непроизводственном репо провайдером `openai-chatgpt` или локальным гейтвеем → проверить качество openwiki/ и что CLAUDE.md проекта не пострадал.
2. Затем `openwiki --init` на целевых больших репо тем же провайдером, ревью сгенерённого, коммит.
3. Вшить CI-workflow с телеметрией OFF и дешёвым CI-провайдером (OpenRouter glm / Gemini AI Studio / Vertex AI ADC).

## Прочее

- **Формат**: Google Open Knowledge Format (OKF) v0.1 (YAML-frontmatter `type` на каждом концепт-документе; `index.md`/`log.md` — reserved).
- **Personal mode** (`openwiki personal`) — локальный «второй мозг» в `~/.openwiki/wiki` из коннекторов (Git, Notion, Gmail, X, Web Search[Tavily], HN). Если у тебя уже есть своя система персональной памяти — personal mode будет её дублировать; основной сценарий этого скилла — code mode.
- **Регион/прокси**: code mode прокси не требует, если LLM-API доступны из твоего региона; Tavily нужен только для web-search в personal mode.
- **Приватность**: телеметрия по умолчанию ON (анонимная — без контента/путей/имён репо/промптов), но всё равно вырубать через env. Перед пушем openwiki/ в публичный репо — прогнать `leak-scan`.
- Справка: https://github.com/langchain-ai/openwiki (README + `examples/`); локально — `./work/openwiki` после клонирования выше.
