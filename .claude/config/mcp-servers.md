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
| Конвертация файлов | skills `file-converter`/`pdf`/`xlsx`/`docx`/`pptx` | файловые MCP |

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
| ~~pageindex~~ | ❌ облачный, умеет только OAuth через браузер и открывал вкладки пачками — из шаблона убран. Длинные структурированные PDF (договоры 20+ стр., выписки, годовые отчёты) → локальный движок (см. гочи) |
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
| descript / lovable | Облачный монтаж Descript и сайты Lovable. Оба — **OAuth**. У descript токен живёт 8 часов и без refresh (сервер не выдаёт его без `offline_access`), потом нужен повторный вход |
| trivago | Поиск отелей (по направлению и по радиусу) и динамика цен, **без ключа** |
| runway-official | **Официальный** облачный Runway, `https://mcp.runwayml.com/mcp`: изображения и видео (Gen-4.5, Seedance, Kling, Veo, GPT Image, Nano Banana Pro — набор зависит от тарифа), результат падает в библиотеку Runway. Вход через аккаунт Runway (OAuth, ключ не нужен), **расходует кредиты аккаунта**; опционально — нужен свой аккаунт |
| heygen | **Официальный** облачный HeyGen, `https://mcp.heygen.com/mcp/v1/`: видео с аватаром (Video Agent), аватары, голоса, шаблоны, папки, перевод. OAuth по аккаунту HeyGen, **кредиты плана** (не API-ключ); опционально. Навык `heygen` с API-ключами остаётся для того, что делается скриптами |
| elevenlabs (облачный) | **Официальный** облачный ElevenLabs. ⚠️ Адрес в Claude Code — **`https://api.us.elevenlabs.io/v1/mcp`**, а не `api.elevenlabs.io` из доки: сервер сам называет ресурсом `api.us…`, и Claude Code на адресе из доки пишет «Protected resource … does not match expected» и не соединяется (для аккаунтов в изолированных регионах — `api.eu/in/sg.residency.elevenlabs.io/v1/mcp`). Права по доке — **агенты (чтение и запись) и Text to Speech**, по описанию самого сервера ещё `image_video_generation`, `voice_generation`, `flows`, `speech_history_read`. Клон голоса, эффекты, музыка, скорость, словари произношения — по-прежнему навык `elevenlabs` (ключ). Удаление агента необратимо |
| ozon-shopping | Поиск, карточки, сравнение и отзывы Ozon (только чтение) с отсевом накрученных отзывов: `ozon_search`, `ozon_product`, `ozon_reviews`, `ozon_compare`, `ozon_status`. Это **фасад** навыка `ozon-shopping` (`skills/ozon-shopping/server/ozon-safe-mcp.mjs`) над проверенным `neosheps/ozon-shopping-mcp@2ec1c70`, а не сам upstream. Сессию создаёт пользователь: `node ~/.claude/skills/ozon-shopping/scripts/ozon-audit.mjs setup` |
| blender + cadquery | 3D/CAD, локальные stdio-серверы. Живут в `.mcp.json` папки-воркспейса, не глобально: старт Blender 40–100 с, CadQuery 60–175 с под нагрузкой. Там же `MCP_TIMEOUT=300000` (ниже не опускать: CadQuery стартовал за 174 с), deny на 17 GUI-инструментов Blender, одобрение — `.claude/settings.local.json` → `enabledMcpjsonServers`. Шаблон папки и сборка runtime — `templates/3d-workspace/` (`SETUP.md`) |

Семь серверов от skillsmp до trivago — удалённые HTTP-серверы, ставятся одной командой в пользовательский scope:

```bash
claude mcp add --transport http --scope user <name> <url>
# например: claude mcp add --transport http --scope user trivago https://mcp.trivago.com/mcp
```

Адреса и готовые блоки — в `mcp.json` пака (секция `servers`). Серверам без ключа (skillsmp, excalidraw, trivago) больше ничего не нужно. OAuth-серверам (publora, higgsfield, descript, lovable) — один раз войти: `/mcp` → сервер → Authenticate, вход проходит в браузере. До входа сервер числится в `/mcp` как требующий авторизации, а его инструментов в сессии нет. Правила `permissions.ask` для excalidraw и publora уже стоят в `settings.json` пака. В шаблон автоустановки (`templates/mcp-servers.json`) эти серверы намеренно не входят: `scripts/mcp_install.py` ставит шаблон целиком, а эти подключаются по выбору.

Тем же способом подключаются и облачные `runway-official`, `heygen`, `elevenlabs` (адреса — в таблице выше): все три с OAuth, ключ не нужен, тратятся кредиты их аккаунта.

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
- ⚠️ **Конфиг ссылается на `${ПЕРЕМЕННАЯ}`, а Claude Code подставляет её из окружения процесса** — файл `.credentials.master.env` он не читает. Признак: сервер или плагин числится настроенным, ключ в credentials лежит, а подключение падает с «badly formatted» или 403 — значит подставилась пустота. Проверять ключ отдельно (`curl` с ним руками): он может быть живым. Лечение: завести переменную в окружение пользователя, либо выключить плагин (`settings.json` → `enabledPlugins` → `false`; включение обратно — `true`). Так «шумели» при каждом старте плагины `greptile`, `github`, `sourcegraph`.
- ⚠️ **Тот же класс, но без npx: медленный собственный сервер.** Признак: `claude mcp list` то Connected, то Failed у одного и того же сервера в зависимости от загрузки машины. Лечится `MCP_TIMEOUT` (например, 120000).
- 🩹 **«Failed to connect» — симптом, а не диагноз: запусти сервер руками и прочитай трассировку, прежде чем крутить таймаут.** Один из случаев: Python-сервер падал с `ImportError: cannot import name 'Icon' from 'mcp.types'`, потому что на машине два пакета `mcp` — 1.26.0 в системном `site-packages` (его ждёт `fastmcp`) и старый 1.12.4 в пользовательском (`…\Roaming\Python\Python313\site-packages`), который шёл первым в `sys.path` и перекрывал новый. Лечение: отодвинуть пользовательский пакет в сторону (переименовать папку).
- ⚠️ MCP-сервер Miro (`mcp.miro.com`) на обычный REST-токен отвечает **403**: ему нужен OAuth-токен своего скоупа. Эндпоинта `api.miro.com/v1/mcp` не существует (404). Рабочий путь без OAuth — REST: `python ~/.claude/tools/miro_client.py` по `MIRO_ACCESS_TOKEN` (скоупы `boards:write, boards:read`).
- ⚠️ **Как авторизовать облачные серверы со статусом «Needs authentication»:** `claude mcp login <имя>` нужен настоящий терминал — из фонового Bash он печатает адрес и тут же выходит.
  - Окно ждёт согласия **около 5 минут**, потом закрывается само без токена. Нажимать Allow нужно **только в самой новой вкладке**: вкладка от прежней попытки отвечает «Invalid state parameter» / «Authorization session mismatch».
  - Повторный `login` для сервера, который уже авторизован, сбрасывает его токен: не запускай `mcp login` руками для «подключённого».
  - Состояние после входа: `claude mcp list` (или `claude mcp get <имя>`). Токен доступа живёт от часа до суток, обновляется сам; если «Needs authentication» вернулось, войди ещё раз.
  - ⚠️ **«Нажал Allow, страница пишет Authentication successful, а токена нет».** Это не ошибка пользователя и не таймаут. Клиент 2.1.28x сверяет параметр `iss` в ответе авторизации (RFC 9207) с издателем из метаданных и выбрасывает ответ при расхождении; страница «успешно» рисуется ДО этой проверки, окно консоли закрывается, и со стороны это неотличимо от «не нажал». Увидеть ошибку можно, запустив вход в консоли, которая не закрывается: `cmd /k "<путь к claude.exe>" mcp login <имя>`, в конце будет `Couldn't complete authentication … Issuer mismatch in authorization response (RFC 9207)`. Так у Descript: его сервер авторизации отдаёт `iss` другого домена вместо `https://api.descript.com`.
- ⚠️ **Ozon: регистрировать фасад, а не upstream.** В `~/.claude.json` стоит `node ~/.claude/skills/ozon-shopping/server/ozon-safe-mcp.mjs`. Сам `neosheps/ozon-shopping-mcp` сервером не заводить: у него есть инструмент `ozon_setup_session` (по вызову модели открывает окно Chrome), сырой текст чужих отзывов идёт в контекст, а сообщения об ошибках советуют `npx ozon-shopping-mcp@latest` (в `permissions.deny` такое запрещено). Обновление upstream только через аудит разницы коммитов: `skills/ozon-shopping/references/audit-and-install.md`.
