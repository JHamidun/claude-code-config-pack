# MCP-серверы — полный реестр

> Справочник, читается по требованию (не в авто-load промпта). Перенесён из CLAUDE.md (C9) 2026-07-18.
> Короткая сводка + указатель — в CLAUDE.md. Здесь — полный список с колонкой «когда нужен».

## Local (settings.json — грузятся при каждой сессии)

| Сервер | Назначение |
|--------|-----------|
| filesystem | Файловые операции (${WORKSPACE}, ${HOME}) |

> chrome-devtools — встроен в VSCode расширение (не в settings.json mcpServers).
> context7 и github мигрированы на плагины (быстрее, нет cold start от npx).

### Local, disabled по умолчанию (включить в settings.json при необходимости)

| Сервер | Назначение | Когда нужен | Как включить |
|--------|-----------|-------------|--------------|
| fns-check | KYC-проверка контрагентов РФ по ИНН/ОГРН: ЕГРЮЛ/ЕГРИП + ЕФРСБ + Прозрачный бизнес + ФССП + КАД → детерминированный вердикт риска (`check_contractor`). Код-аудит пройден 2026-07-19 (чист, только официальные API, без ключей). Установлен из аудированного клона в `~/.claude/mcps/mcp-fns-check/` | KYC контрагентов РФ: лиды (lead-enrichment), тендеры (tender-search-ru), юрпроверка (company-lawyer), [WealthCo] KYC | В `settings.json` → `mcpServers.fns-check` поставить `"disabled": false`, перезапуск сессии. ⚠️ ФССП/КАД/ПБ гео-блочат не-РФ IP (451/503) → вердикт деградирует до `manual_review_required`; ЕГРЮЛ работает отовсюду |
| pageindex | PageIndex MCP (`npx @pageindex/mcp`) — обёртка ОБЛАКА VectifyAI (api.pageindex.ai): vectorless reasoning-RAG по загруженным документам. ⚠️ Требует отдельный PAGEINDEX_API_KEY с dash.pageindex.ai (НЕ наш OpenAI), документы уходят в их облако. **Основной путь у нас — локальный движок** `~/.claude/mcps/pageindex/` (venv + `pi.py index/tree/pages/ask`, ключ OPENAI_API_KEY из credentials.master.env, документы не покидают машину) — см. skill research-docs, секция PageIndex | Длинные структурированные PDF: договоры 20+ стр. (kp-deck post-КП), банковские выписки (portfolio-review), финдоки [WealthCo], годовые отчёты | Локальный движок работает уже сейчас без MCP. Облачный MCP: получить ключ на dash.pageindex.ai → `"disabled": false` + env PAGEINDEX_API_KEY, перезапуск сессии |

## Cloud MCP (от подписки Max — автоматически)

| Сервер | Назначение |
|--------|-----------|
| Airtable | Базы данных, таблицы, записи |
| Canva | Дизайн: генерация, редактирование, экспорт |
| Context7 | Документация библиотек (дублирует плагин) |
| Figma | Дизайн-контекст, скриншоты, диаграммы |
| Gamma | AI презентации и документы |
| Gmail | Поиск, чтение, черновики |
| Google Calendar | События, свободные слоты |
| Granola | Транскрипты встреч |
| Mermaid Chart | Рендер Mermaid диаграмм |
| n8n | Поиск и запуск workflow |

## Доступные (mcp.json — включить при необходимости; ревизия Ф6 2026-07-18, мёртвые → mcp.json.archive)

| Сервер | Назначение | Когда нужен |
|--------|-----------|-------------|
| affine | AFFiNE workspace (YourProduct docs) | Документация, база знаний Company |
| postgres | SQL операции (your-server) | Работа с БД |
| redis | Кеш и pub/sub (your-server) | Работа с кешем |
| dalle | DALL-E генерация через OpenAI | Генерация изображений |
| replicate | 1000+ AI моделей | Специализированные AI задачи |
| elevenlabs | TTS, voice cloning | Озвучка |
| apify | Web scraping (1600+ Actors) | Сбор данных |
| n8n | Workflow automation (SSE, local) | Автоматизация |
| puppeteer | Browser automation | Screenshots |
| brave-search | Web search API | Research |
| memory | Knowledge Graph | Multi-agent context |
| sequentialthinking | Step-by-step reasoning | Сложный анализ |
| everything | MCP test/debug server | Тестирование MCP |
| figma-mcp | Figma HTTP MCP (mcp.figma.com) | Альтернатива плагину |
| playwright | Browser automation | Альтернатива плагину |

Уникальные рабочие в `.mcp.json` (легаси-каталог, инертен при enableAllProjectMcpServers=false): docker, todoist, microsoft-365, suno.

## Советы по выбору (ex-skill mcp-usage)

- **Skills-first для медиа-задач** — MCP-серверы генерации НЕ дефолт: изображения → skill `image-generation` (канон NB2, НЕ dalle MCP), озвучка/TTS → skill `elevenlabs` (НЕ Replicate Riffusion/Bark), транскрипция → skill `deepgram` (НЕ Replicate Whisper), апскейл → Replicate Real-ESRGAN (skill `image-enhancer`).
- **Стоимость (pay-per-use — учитывай перед массовыми вызовами):** dalle ~$0.04–0.12/картинка · elevenlabs ~$0.30/1000 симв · replicate ~$0.0001–0.01/сек · apify $5/мес бесплатно, дальше pay-per-use. Остальные — free/API-limits.
- **Комбинирование:** один сервер на задачу; multi-server пайплайны (research → контент → медиа → публикация) собирай через skills/commands, а не цепочку MCP.
- Полный старый гид `${WORKSPACE}/.claude/MCP_SERVERS_GUIDE.md` — АРХИВ от 2025-11-30 («24 сервера», DALL-E как основной, sqlite/fetch/time живыми): противоречит текущему канону, НЕ использовать как источник истины.

> Вынесено в `mcp.json.archive` (npm 404 / дубли / мёртвое, у каждой записи `_archive_reason`): sqlite, fetch, time, microsoft-office + 35 записей легаси-каталога .mcp.json. Файловые операции — конвертация через skill `file-converter`/офисные скиллы (pdf/xlsx/docx), время — системное.
