# MCP-серверы — «когда нужен» и гочи

> Это НЕ реестр включённого и НЕ счётчики. Список серверов и их `disabled`-флаги протухают за дни.
> **Источник истины: `~/.claude/settings.json` → `mcpServers`** (плюс `mcp.json`, `.mcp.json` для легаси-каталога) и `/mcp` в сессии.
> Здесь — только то, что не протухает: зачем сервер нужен, чем его заменить и обо что об него бьются.

## Правило выбора: skills-first

MCP-сервер — не дефолт под медиа/генерацию. Сначала skill:

| Задача | Канон | НЕ через |
| --- | --- | --- |
| Изображения | skill `image-generation` (NB2) | dalle MCP |
| Озвучка/TTS | skill `elevenlabs` | Replicate Riffusion/Bark |
| Транскрипция | skill `deepgram` | Replicate Whisper |
| Апскейл | skill `image-enhancer` (Real-ESRGAN) | ручной replicate |
| Конвертация файлов | skills `file-converter`/`pdf`/`xlsx`/`docx` | файловые MCP |

Multi-server пайплайны (research → контент → медиа → публикация) собирай через skills/commands, а не цепочкой MCP-вызовов. Один сервер на задачу.

## Когда какой сервер нужен

| Сервер | Когда нужен |
| --- | --- |
| filesystem | Файловые операции вне текущего cwd (${WORKSPACE}, ${HOME}) |
| second-brain | Семантический поиск по личной памяти/переписке (`brain_search`, remember, contacts) |
| notebooklm | Подкасты / deep research / quiz из загруженных документов |
| plaud | Записи и транскрипты диктофона Plaud |
| google-studio, runway | Медиа-генерация, когда skill-обёртки не хватает |
| playwright (пул) | Параллельная браузерная работа несколькими сессиями сразу |
| fns-check | KYC контрагентов РФ по ИНН/ОГРН: лиды (lead-enrichment), тендеры, юрпроверка, [WealthCo] |
| pageindex | Длинные структурированные PDF: договоры 20+ стр., выписки, годовые отчёты |
| affine | Документация и база знаний Company |
| postgres / redis | БД и кеш на your-server |
| apify | Массовый web scraping (1600+ Actors) |
| brave-search | Веб-поиск в research |
| n8n | Поиск и запуск workflow |
| memory / sequentialthinking | Multi-agent контекст, пошаговый разбор |
| everything | Отладка самого MCP-протокола |
| figma-mcp / context7 / github | Альтернатива одноимённым плагинам (плагин обычно быстрее — нет cold start от npx) |

Часть серверов (Airtable, Canva, Figma, Gamma, Gmail, Google Calendar, Granola, Mermaid Chart, n8n, Context7 и т.п.) может приходить cloud-коннекторами от подписки — их в `settings.json` НЕТ вообще: наличие видно только по `/mcp` и в настройках коннекторов claude.ai. Отсутствие сервера в settings.json не означает, что его нет.

## Гочи (проверено, не протухает)

- ⚠️ **`npx <pkg>@latest` в команде сервера резолвит реестр на КАЖДОМ старте** — измерено 38–41 с против дефолтного таймаута 30 с: сервер молча отбрасывается и выглядит как «плагин выпал». Пиньте версию (2.7–4.2 с) и/или ставьте `MCP_TIMEOUT=120000`. Это была причина флапа браузерных MCP; конфиг при этом не менялся вовсе.
- ⚠️ Браузерный MCP-плагин — синглтон: параллельная сессия занимает его целиком. Для одновременной работы — пул playwright-инстансов или skill `playwright-automation` (bdo.py).
- ⚠️ fns-check: ФССП/КАД/«Прозрачный бизнес» гео-блочат не-РФ IP (451/503) → вердикт деградирует до `manual_review_required`; ЕГРЮЛ отвечает отовсюду.
- ⚠️ pageindex через `npx @pageindex/mcp` — это ОБЛАКО VectifyAI: нужен отдельный PAGEINDEX_API_KEY и документы уходят наружу. Локальный движок `~/.claude/mcps/pageindex/` (`pi.py index/tree/pages/ask`) работает на OPENAI_API_KEY и данные с машины не выпускает — он и есть основной путь (skill `research-docs`).
- Стоимость pay-per-use (учитывай перед массовыми вызовами): dalle ~$0.04–0.12/картинка · elevenlabs ~$0.30/1000 симв · replicate ~$0.0001–0.01/сек · apify $5/мес бесплатно, дальше по факту.
- Ключи — только через `${VAR_NAME}` из `.credentials.master.env`, никогда plaintext в конфиге.
- Мёртвые/дублирующие записи вынесены в `mcp.json.archive` (у каждой `_archive_reason`); `.mcp.json` инертен при `enableAllProjectMcpServers=false`.
- ❌ `${WORKSPACE}/.claude/MCP_SERVERS_GUIDE.md` — архив от 2025-11-30, противоречит канону (DALL-E как основной и т.п.). Не использовать как источник истины.
