# Каталог инструментов

> Файлы в `~/.claude/tools/` и `~/.claude/scripts/`, пригодные к повторному
> использованию. Разовые скрипты под конкретные проекты (курс, выгрузка чата,
> сборка PDF) сюда не входят — они лежат там же, но переиспользованию не подлежат.
> Запуск: `python ~/.claude/<папка>/<файл> --help`.

## tools/

- `audit_usage.py` — Skills & Agents Usage Auditor Анализирует использование skills и agents за последние N дней
- `auto_title_session.py` — Auto-title для Claude Code сессий Запускается на Stop hook и добавляет заголовок к текущей сесси
- `claude_cli.py` — Claude CLI wrapper — call Claude models via the claude CLI binary.
- `figma_api.py` — Figma API helper for Claude Code.
- `fix_session_titles.py` — Вернуть именам сессий смысл, когда Claude Code их не сгенерировал.
- `gmail_download_attachments.py` — Download PDF attachments from Gmail messages. Usage: python gmail_download_attachments.py <email
- `gmail_multi_auth.py` — Gmail Multi-Account OAuth Authorization One-time setup: authorizes each Google account and saves
- `gmail_search.py` — Gmail Multi-Account Search Search emails across all authorized Gmail accounts.
- `gmail_send.py` — Отправка писем через Gmail — то, чего в конфиге не было.
- `memory_hooks.py` — Memory hooks for Claude Code - automatic context saving.
- `prompt_router.py` — Prompt Router — UserPromptSubmit hook script. Reads prompt from stdin JSON, matches keywords fro
- `quick_audit.py` — Quick Skills & Agents Audit (без анализа использования) Просто перечисляет все файлы и даёт базо
- `search_chats.py` — Claude Code Chat Search — SQLite FTS5 full-text search over session history.
- `tg_bot.py` — tg_bot.py — полный инструмент Telegram Bot API: ВСЁ, что умеет бот, из CLI.
- `tg_client.py` — Telegram CLI for Claude Code. Full-featured Telethon client for reading, searching, downloading,
- `vector_memory.py` — Vector Memory Manager - stores session context in Qdrant (local mode).
- `yadisk_public.py` — Публичные папки Яндекс.Диска: посмотреть и скачать.

## scripts/

- `brazil_law_client.py` — Brazil Law client — зеркало garant_client.py для бразильского права.
- `build_digests_from_db.py` — build_digests_from_db.py — дайджесты сессий ИЗ chats.db (а не локальных .jsonl).
- `cleanup_final.py` — Final cleanup: delete duplicate old PDFs + raw Plaud artifacts + rename Presentation.
- `cleanup_local.py` — Cleanup local D:\\Alexander_AI_Training\\: remove duplicate Plaud raw artifacts.
- `config_links.py` — Проверка связности конфига: ведут ли ссылки туда, где что-то есть.
- `config_lint.py` — config_lint.py - Linter for the Claude Code config (Windows 11).
- `download_presentation.py` — Mirror locally the existing Presentation.pdf (4.3MB) from Drive.
- `f4_apply_descriptions.py` — Ф4: заменяет frontmatter-поле `description` в SKILL.md (тримы + zombie-фиксы). Метод: точечная r
- `garant_client.py` — garant_client.py — прямой HTTP-клиент к внутреннему API системы ГАРАНТ (internet.garant.ru), рев
- `glavbukh_client.py` — клиент к warm-browser демону «Системы Главбух» (glavbukh_daemon.js).
- `local_collect.py` — Collect all Alexander training recordings into D:\Alexander_AI_Training\ .
- `memory_fit.py` — Удержать индекс памяти в пределах, за которыми он молча обрезается.
- `memory_graph.py` — memory_graph.py - Граф знаний памяти (Layer 1: из курированных заметок).
- `outlook_sent_zoom.py` — Search Outlook sent items for Zoom links sent to Alexander.
- `plugins_gc.py` — plugins_gc.py — сборщик мусора для кэша плагинов Claude Code (~/.claude/plugins, ~2
- `redownload_transcripts.py` — Re-download new transcripts from Drive (locally deleted by mistake).
- `sanitize_config_secrets.py` — sanitize_config_secrets.py — move real credential VALUES from config/*.md into .credentials.mast
- `text_sanitize.py` — text_sanitize — strip invisible Unicode from extracted text before it enters model context.
