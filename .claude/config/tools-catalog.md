# Каталог инструментов

> Файлы в `~/.claude/tools/` и `~/.claude/scripts/`, пригодные к повторному
> использованию. Разовые скрипты под конкретные проекты (курс, выгрузка чата,
> сборка PDF) сюда не входят — они лежат там же, но переиспользованию не подлежат.
> Запуск: `python ~/.claude/<папка>/<файл> --help`.

## tools/

- `claude_cli.py` — Claude CLI wrapper — call Claude models via the claude CLI binary.
- `figma_api.py` — Figma API helper for Claude Code.
- `gmail_download_attachments.py` — Download PDF attachments from Gmail messages. Usage: python gmail_download_attachments.py <email
- `gmail_search.py` — Gmail Multi-Account Search Search emails across all authorized Gmail accounts.
- `gmail_send.py` — Отправка писем через Gmail — то, чего в конфиге не было.
- `prompt_router.py` — Prompt Router — UserPromptSubmit hook script. Reads prompt from stdin JSON, matches keywords fro
- `search_chats.py` — Claude Code Chat Search — SQLite FTS5 full-text search over session history.
- `tg_bot.py` — tg_bot.py — полный инструмент Telegram Bot API: ВСЁ, что умеет бот, из CLI.
- `tg_client.py` — Telegram CLI for Claude Code. Full-featured Telethon client for reading, searching, downloading,
- `vector_memory.py` — Vector Memory Manager - stores session context in Qdrant (local mode).
- `yadisk_public.py` — Публичные папки Яндекс.Диска: посмотреть и скачать.

## scripts/

- `config_links.py` — Проверка связности конфига: ведут ли ссылки туда, где что-то есть.
- `config_lint.py` — config_lint.py - Linter for the Claude Code config (Windows 11).
- `memory_fit.py` — Удержать индекс памяти в пределах, за которыми он молча обрезается.
- `memory_graph.py` — memory_graph.py - Граф знаний памяти (Layer 1: из курированных заметок).
- `plugins_gc.py` — plugins_gc.py — сборщик мусора для кэша плагинов Claude Code (~/.claude/plugins, ~2
- `sanitize_config_secrets.py` — sanitize_config_secrets.py — move real credential VALUES from config/*.md into .credentials.mast
- `text_sanitize.py` — text_sanitize — strip invisible Unicode from extracted text before it enters model context.

> Каталог собирается по ФАКТУ публикуемого дерева, а не по домашней папке автора.
> Раньше он строился из личного ~/.claude: 16 записей вели к файлам, которых в паке
> нет, и столько же реальных скриптов не были упомянуты вовсе. Проверка молчала,
> потому что смотрела туда же, откуда каталог и собирали. Сверить: 
> `CLAUDE_CONFIG_DIR=<пак>/.claude python .claude/scripts/config_links.py`.

Ещё в паке есть (добавь описание, если пользуешься): `agent_api_server.py`, `email_client.py`, `fix_student_config.py`, `gdrive_client.py`, `gdrive_upload.py`, `ha_client.py`, `kb.py`, `llms_txt.py`, `mascot_hooks_fix.py`, `memory_brief.py`, `miro_client.py`, `osint_client.py`, `perplexity_helper.py`, `places_search.py`, `setup_runtime.py`, `sms_client.py`, `webhook_server.py`.
