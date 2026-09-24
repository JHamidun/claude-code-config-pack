# MCP-серверы — «когда нужен» и гочи

> Это НЕ реестр включённого и НЕ счётчики. Список серверов и их `disabled`-флаги протухают за дни.
> **Источник истины: `~/.claude.json` → `mcpServers`** и `/mcp` в сессии.
> ⚠️ Секция `mcpServers` в `~/.claude/settings.json` **не читается вовсе** — молча, без ошибки
> и без строки в логе. Серверы при этом выглядят настроенными и не поднимаются ни разу.
> Пак кладёт свои в `~/.claude.json` скриптом `scripts/mcp_install.py` (шаблон —
> `templates/mcp-servers.json`); твои одноимённые он не трогает, свои помнит в
> `~/.claude/.ccpack-mcp.txt`. Проверять правку, не перезапуская сессию: `claude mcp list`
> из нового процесса.
> Здесь — только то, что не протухает: зачем сервер нужен, чем его заменить и обо что об него бьются.

## Правило выбора: skills-first

MCP-сервер — не дефолт под медиа/генерацию. Сначала skill:

| Задача | Канон | НЕ через |
| --- | --- | --- |
| Изображения | skill `image-generation` (NB2) | dalle MCP |
| Озвучка/TTS | skill `elevenlabs` | Replicate Riffusion/Bark |
| Транскрипция | skill `deepgram` | Replicate Whisper |
| Апскейл | skill `image-enhancer` (Real-ESRGAN) | ручной replicate |
| Конвертация файлов | skills `file-converter`/`pdf`/`xlsx`/`pptx` | файловые MCP |

Multi-server пайплайны (research → контент → медиа → публикация) собирай через skills/commands, а не цепочкой MCP-вызовов. Один сервер на задачу.

## Когда какой сервер нужен

| Сервер | Когда нужен |
| --- | --- |
| filesystem | Файловые операции вне текущего cwd (рабочий каталог проекта, домашний каталог) |
| second-brain | Семантический поиск по личной памяти/переписке (`brain_search`, remember, contacts) |
| notebooklm | Подкасты / deep research / quiz из загруженных документов |
| plaud | Записи и транскрипты диктофона Plaud |
| google-studio, runway | Медиа-генерация, когда skill-обёртки не хватает |
| playwright (пул) | Параллельная браузерная работа несколькими сессиями сразу |
| fns-check | KYC контрагентов РФ по ИНН/ОГРН: квалификация лидов, тендеры, юрпроверка |
| pageindex | Длинные структурированные PDF: договоры 20+ стр., выписки, годовые отчёты |
| affine | Документация и база знаний Company |
| postgres / redis | БД и кеш на your-server |
| apify | Массовый web scraping (1600+ Actors) |
| brave-search | Веб-поиск в research |
| n8n | Поиск и запуск workflow |
| memory / sequentialthinking | Multi-agent контекст, пошаговый разбор |
| everything | Отладка самого MCP-протокола |
| figma-mcp / context7 / github | Альтернатива одноимённым плагинам (плагин обычно быстрее — нет cold start от npx) |
| skillsmp | Поиск чужих навыков из skill-manager: `search_skills`, `get_skill`, `list_categories`. Только чтение, **без ключа** |
| excalidraw | Схема прямо в чате: `read_me`, `create_view`, чекпоинты. **Без ключа.** Адрес **`https://mcp.excalidraw.com/mcp`** (голый хост отдаёт 308). `export_to_excalidraw` публикует схему по публичной ссылке → стоит в `permissions.ask` |
| publora | Публикации в соцсети и LinkedIn-аналитика. Список инструментов виден без входа, а вызовы требуют **OAuth**: `/mcp` → publora → Authenticate. Всё публикующее и удаляющее (create/update/delete_post, reactions, comments, reshare, delete/prune media) — в `permissions.ask`; загрузка медиа (`get_upload_url`, `complete_media`) идёт без подтверждения — сама ничего не публикует |
| higgsfield | Генерация через MCP Higgsfield (generate_image/video/audio, jobs_wait, media_upload). **OAuth.** Рецепты — `skills/video-generation/engines/higgsfield/references/mcp-app-skills/`; без OAuth работает CLI `hf` из того же движка |
| descript / lovable | Облачный монтаж Descript и сайты Lovable. Оба — **OAuth** |
| trivago | Поиск отелей (по направлению и по радиусу) и динамика цен, **без ключа** |
| blender + cadquery | 3D/CAD, локальные stdio-серверы. Живут в `.mcp.json` папки-воркспейса, не глобально: старт Blender 40–100 с, CadQuery 60–175 с под нагрузкой. Там же `MCP_TIMEOUT=300000` (ниже не опускать: CadQuery стартовал за 174 с), deny на 17 GUI-инструментов Blender, одобрение — `.claude/settings.local.json` → `enabledMcpjsonServers`. Шаблон папки и сборка runtime — `templates/3d-workspace/` (`SETUP.md`) |

Семь серверов от skillsmp до trivago — удалённые HTTP-серверы, ставятся одной командой в пользовательский scope:

```bash
claude mcp add --transport http --scope user <name> <url>
# например: claude mcp add --transport http --scope user trivago https://mcp.trivago.com/mcp
```

Адреса и готовые блоки — в `mcp.json` пака (секция `servers`). Серверам без ключа (skillsmp, excalidraw, trivago) больше ничего не нужно. OAuth-серверам (publora, higgsfield, descript, lovable) — один раз войти: `/mcp` → сервер → Authenticate, вход проходит в браузере. До входа сервер числится в `/mcp` как требующий авторизации, а его инструментов в сессии нет. Правила `permissions.ask` для excalidraw и publora уже стоят в `settings.json` пака. В шаблон автоустановки (`templates/mcp-servers.json`) эти серверы намеренно не входят: `scripts/mcp_install.py` ставит шаблон целиком, а эти подключаются по выбору.

Часть серверов (Airtable, Canva, Figma, Gamma, Gmail, Google Calendar, Granola, Mermaid Chart, n8n, Context7 и т.п.) может приходить cloud-коннекторами от подписки — их в `settings.json` НЕТ вообще: наличие видно только по `/mcp` и в настройках коннекторов claude.ai. Отсутствие сервера в settings.json не означает, что его нет.

## Гочи (проверено, не протухает)

- ⚠️ **`npx <pkg>@latest` в команде сервера резолвит реестр на КАЖДОМ старте** — измерено 38–41 с против дефолтного таймаута 30 с: сервер молча отбрасывается и выглядит как «плагин выпал». Пиньте версию (2.7–4.2 с) и/или ставьте `MCP_TIMEOUT=120000`. Это была причина флапа браузерных MCP; конфиг при этом не менялся вовсе.
- ⚠️ Браузерный MCP-плагин — синглтон: параллельная сессия занимает его целиком. Для одновременной работы — пул playwright-инстансов или skill `playwright-automation` (bdo.py).
- ⚠️ fns-check: ФССП/КАД/«Прозрачный бизнес» гео-блочат не-РФ IP (451/503) → вердикт деградирует до `manual_review_required`; ЕГРЮЛ отвечает отовсюду.
- ⚠️ pageindex через `npx @pageindex/mcp` — это ОБЛАКО VectifyAI: нужен отдельный PAGEINDEX_API_KEY и документы уходят наружу. Локальный движок работает на OPENAI_API_KEY и данные с машины не выпускает — он и есть основной путь (skill `research-docs`). В пак он не входит (это клон стороннего репозитория со своим venv): `git clone https://github.com/VectifyAI/PageIndex ~/.claude/mcps/pageindex` + venv по их README, свою обёртку `pi.py` (index/tree/pages/ask) написать поверх.
- Стоимость pay-per-use (учитывай перед массовыми вызовами): dalle ~$0.04–0.12/картинка · elevenlabs ~$0.30/1000 симв · replicate ~$0.0001–0.01/сек · apify $5/мес бесплатно, дальше по факту.
- Ключи — только через `${VAR_NAME}` из `.credentials.master.env`, никогда plaintext в конфиге.
- `.mcp.json` инертен при `enableAllProjectMcpServers=false` — это справочник для копирования блоков, а не живой конфиг.
- ⚠️ **`claude mcp add` из-под работающей сессии теряет записи.** Из семи подряд добавленных HTTP-серверов два пропали, хотя каждая команда ответила «Added… File modified»; позже так же исчезли ещё один сервер и проектная запись. `~/.claude.json` одновременно переписывают живая сессия и её агенты. Правило: после любых `mcp add` через 15–20 с перечитать `mcpServers` и довнести пропавшее — `python -c "import json,pathlib; print(sorted(json.load(open(pathlib.Path.home()/'.claude.json',encoding='utf-8')).get('mcpServers',{})))"`. Проектные серверы надёжнее класть в `.mcp.json` папки проекта, а не в `~/.claude.json`.
- ⚠️ **`--env KEY=VAL` у `claude mcp add` — вариадический флаг** и съедает следующее слово как ещё одну переменную: `--env A=B blender -- exe` → «missing required argument». На Windows не спасает и `add-json`: npm-обёртка `claude` ломает кавычки внутри JSON («Invalid input»). Серверы с env — через `.mcp.json` проекта или правкой JSON Python-ом.
- ⚠️ **Проектный `.mcp.json` не одобряет сам себя.** `enabledMcpjsonServers` в `.claude/settings.json` проекта не действует — `claude mcp list` показывает «Pending approval». Работает то же поле в `.claude/settings.local.json` (или ответ на вопрос при первом запуске).
- ⚠️ **`claude mcp list` под нагрузкой врёт «Failed to connect» про stdio-серверы на Python**: у нас так «падали» семь серверов разом (second-brain, plaud, notebooklm, google-studio, runway, context7, screencast), пока машину грузили три агента, — а в самой сессии их инструменты при этом работали. Проверять повторно в тишине, прежде чем чинить.
- ⚠️ **Плагин Exa (`exa@claude-plugins-official`, семантический поиск людей, компаний и статей) требует OAuth**: `/mcp` → plugin:exa:exa → Authenticate (или `EXA_API_KEY`). Плагин ходит на `https://mcp.exa.ai/mcp?client=claude-code-plugin` — там без входа 401; голый `https://mcp.exa.ai/mcp` отвечает анонимно, но плагин на него не ходит.
- ❌ Старые «MCP_SERVERS_GUIDE»-конспекты (архивы 2025 года) противоречат канону — например, называют DALL-E основной моделью картинок. Источник истины по MCP — этот файл плюс `/mcp` в сессии.
