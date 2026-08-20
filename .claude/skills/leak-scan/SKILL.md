---
name: leak-scan
description: "PII/деанон перед публикацией (leak_scan.py) + prompt-injection в чужом скилле (skill_injection_scan.py). Триггеры: «обезличь репо», «проверь скилл перед установкой»."
metadata:
  version: 2.0.0
  updated: 2026-08-02
---

# leak-scan

## Overview — два направления

Скилл закрывает **обе** границы безопасности вокруг авто-загружаемого каталога `~/.claude/`:

| Направление | Скрипт | Вопрос | Что ловит |
|-------------|--------|--------|-----------|
| **ИСХОДЯЩЕЕ** (мои данные наружу) | `scripts/leak_scan.py` | «не утечёт ли что-то личное, если я это опубликую?» | PII, деанон-маркеры (248 паттернов) |
| **ВХОДЯЩЕЕ** (чужой код внутрь) | `scripts/skill_injection_scan.py` | «безопасно ли ставить этот скачанный скилл/плагин/агент?» | prompt-injection и тихий захват полномочий |

Оба скрипта — чистый stdlib Python, UTF-8 stdout (Windows-совместимо), **ничего не меняют на диске**. Направления независимы: перед публикацией своего — ИСХОДЯЩЕЕ; перед установкой чужого с GitHub — ВХОДЯЩЕЕ.

---

## ИСХОДЯЩЕЕ: PII/деанон перед публикацией (`leak_scan.py`)

Single consolidated scanner (`scripts/leak_scan.py`, 248 patterns) that finds personal-data and deanonymization leaks before anything goes public. Consolidated from `leak_scan_v37.py` (37 audit passes + multi-model review). Pure Python UTF-8 — it exists because of a hard-won lesson.

## Critical lesson — why this script, not grep

**`grep -F` with Cyrillic on Windows SILENTLY fails to match** (codepage mismatch) — it returns "clean" while leaks remain. NEVER verify depersonalization with grep/ripgrep for Russian text. ALWAYS use this Python UTF-8 scanner (or LLM agents) as the source of truth.

## Two-stage protocol (MANDATORY)

Regex alone gives FALSE confidence. A 248-pattern scan once passed a repo "clean" — then a semantic LLM review of the same repo found a real client name in an example, a live API credit-balance, real production resource names, a private multi-account auth gateway, and ToS-grey subscription-bypass tooling. None matched a literal pattern. So ALWAYS run BOTH stages before declaring clean:

**Stage 1 — regex scan** (`scripts/leak_scan.py`): catches literal tells (names, emails, IPs, keys, tokens, known clients, national IDs). Fast, deterministic, exhaustive for what it knows.

**Stage 2 — semantic review** (LLM): read the actual content (skill bodies, examples, READMEs) and hunt for what regex CANNOT see:
- **Real proper nouns in examples** — client/company/person names, project codenames, product names (not in the pattern list)
- **Live account state** — credit balances, quotas, plan tiers, index/bucket/resource names, account IDs
- **Private infrastructure** — your servers/ports/paths, internal tools, multi-account setups, hardcoded home-dir conventions
- **Bespoke-business reveals** — a skill that exposes your employer, market, vertical, methodology, or a real client engagement even with names removed
- **Vendor/credential lock-in & ToS-grey tooling** — cookie/session bypass, reverse-engineered internal APIs, skills that only work with your private paid key
- **Dependencies on unshipped private files** — references to scripts/DBs/configs not in the public artifact

For a multi-file repo, fan out a few read-only agents over slices of the tree for Stage 2 (cap concurrency ~2-3 to avoid rate limits). Diff new content against the already-public baseline to separate newly-introduced leaks from pre-accepted ones.

## When to Use

- Before pushing/publishing a repo, skill, pack, gist, or archive publicly
- Auditing an already-public artifact for leaks ("did I leave anything in?")
- Verifying a depersonalized build matches the zero-identity standard

## Usage

```bash
python ~/.claude/skills/leak-scan/scripts/leak_scan.py <dir-or-file> [--allow SUBSTR ...]
```

- `target` — directory (recursive) or single file. Scans text files by extension; skips `.git/` and `_*`-prefixed working files.
- `--allow SUBSTR` — extra allowlisted substring (repeatable) for project-specific intended strings.
- Output is forced UTF-8 (safe for Cyrillic on any console).

**Exit codes:** `0` clean · `1` matches found · `2` target not found.

```bash
# Quick gate before a push (note: pipe loses exit code — check the printed FOUND/CLEAN)
python ~/.claude/skills/leak-scan/scripts/leak_scan.py ./my-public-repo
```

## What it catches (248 patterns)

| Group | Examples |
|-------|----------|
| Identity | real names, handles, personal emails, personal domains |
| Infra | server IPs, internal Docker IPs, gateway/hook ports, hostnames |
| Clients/brands | your employer, your clients (+ localized forms) |
| Secrets | `sk-ant`, `sk-proj`, `AIza`, `ghp_`, `xoxb`, `ntn_`, `pplx-`, JWT, Telegram bot tokens |
| National ID formats | tax/residence IDs, phone (multiple formats) |
| Deanon fingerprints | timezone, specific hardware model, region defaults, telltale counts, voice IDs |
| Stego | zero-width characters |

Allowlist covers placeholders (`your-username`, `YOUR_*`, `${HOME}`, `${WORKSPACE}`) and credited public OSS authors (garrytan, obra/Jesse Vincent, mvanhorn, Anthropic, …).

## Reading the results — intended vs real leak

Not every hit is a leak. After running, triage:

- **Real leak** → scrub: secrets, national IDs, server IPs, private client names, personal emails, hardware/timezone fingerprints.
- **Intended/unavoidable** → keep: a public marketplace's own `owner/repo` in its install command and `repository`/`author.url` fields necessarily name the repo. Decide identity policy (full name vs handle vs placeholder) with the user before deciding these are acceptable.
- **Baseline pre-existing** → if a hit already lives in the live public source, it was previously accepted; flag it but don't treat it as newly introduced.

To compare a new build against an already-published baseline, scan both and diff the hit sets by path.

## Extending patterns

Patterns and allowlist are inline in `scripts/leak_scan.py` (`LEAK_PATTERNS`, `ALLOWLIST_SUBSTRINGS`). Add new leaks/placeholders there. For one-off intended strings, prefer `--allow` over editing the file.

---

## ВХОДЯЩЕЕ: проверка чужого скилла/плагина/агента перед установкой (`skill_injection_scan.py`)

Любой сторонний скилл или плагин, скачанный с GitHub, попадает в авто-загружаемый каталог `~/.claude/` **без единой проверки** — а его SKILL.md уходит в контекст модели, его хуки выполняются на каждом вызове инструмента, его `.mcp.json` может поднять чужой сервер с моими правами. Этот скрипт — гейт перед тем, как чужой код станет частью моего окружения.

Идея и часть правил — из `virgiliojr94/book-to-skill` (`tools/scan_generated_skill.py`), адаптировано под этот конфиг и расширено проверками hooks / MCP / npm-lifecycle, которых у источника нет.

### Когда запускать

- Скачал скилл/плагин/агента с GitHub и **до** копирования в `~/.claude/skills|plugins|agents`.
- Оцениваешь чужой репозиторий, из которого хочешь забрать код себе.
- Ревизия уже установленного стороннего пакета («а что оно вообще делает при загрузке?»).

### Использование

```bash
python ~/.claude/skills/leak-scan/scripts/skill_injection_scan.py <цель> [опции]
```

- `<цель>` — каталог скилла (со `SKILL.md`), каталог плагина (с `plugin.json`), каталог агентов/команд, сборник (`skills/`+`agents/`+`hooks/`), **или** одиночный `.md`. Тип определяется автоматически.
- `--min-severity CRITICAL|WARN|INFO` — порог печати (по умолчанию INFO).
- `--allow RULE_ID` — заглушить правило (повторяемо), напр. `--allow hooks.registered` для заведомо доверенного пакета с хуком.
- `--include-vendor` — сканировать и `node_modules/dist/build` (по умолчанию помечаются как **не проверенные**, а не молча пропускаются).
- `--json` — машинный вывод. `--list-rules` — список всех правил.

**Коды выхода:** `0` чисто · `1` есть находки (CRITICAL/WARN) · `2` скан не завершён достоверно (симлинк-цель, превышен лимит).

```bash
# Гейт перед установкой (пайп теряет код возврата — смотри печатное CRITICAL/ЧИСТО)
python ~/.claude/skills/leak-scan/scripts/skill_injection_scan.py ./downloaded-skill
```

### Что ловит (35 правил, severity CRITICAL/WARN/INFO)

| Группа | Правила | Сигнал |
|--------|---------|--------|
| Невидимый Unicode | `unicode.invisible` | ZWSP/ZWNJ/ZWJ/word-joiner/BOM, bidi-override (trojan source), теговый блок U+E0000–E007F. Emoji-ZWJ (👨‍💻) не флагуется |
| Prompt-injection | `prompt.ignore_previous` (RU+EN), `disregard_system`, `role_reassignment`, `fake_system_prefix`, `system_tag`, `chat_template_tag` (`<\|im_start\|>`, `[INST]`), `tool_call_tag`, `covert_directive`, `autonomy_grab`, `memory_write` | фразы-перехваты, поддельные `system:`/`<system>`, разделители чат-шаблонов, приказ действовать скрытно/дописать себя в CLAUDE.md |
| Скрытое в Markdown | `md.hidden_directive`, `md.hidden_style` | инструкция в HTML-комментарии или под `display:none`/белым шрифтом |
| Фронтматтер-захват | `frontmatter.allowed_tools`, `model_invocation_enabled`, `permission_mode` | скилл сам себе выдаёт `Bash(*)`/`*`, включает автовызов, понижает режим разрешений |
| Эксфильтрация | `tool.exfiltration_shape`, `net.suspicious_sink`, `code.credential_exfil_chain`, `content.base64_blob` | секрет по сети на литеральный посторонний хост; webhook.site/ngrok/paste-сервисы; чтение кред + отправка в одном файле; длинный base64-блоб |
| Опасный код | `code.remote_exec`, `dynamic_eval`, `detached_spawn`, `destructive`, `claude_config_write` | `curl\|sh`, исполнение декодированного base64, фоновый отвязанный процесс, `rm -rf ~`, запись в мой конфиг Claude Code |
| **Хуки** (нет у источника) | `hooks.registered`, `hooks.dangerous_command` | плагин регистрирует хук, что выполнится **на каждом** вызове инструмента (matcher `*`) |
| **MCP** (нет у источника) | `mcp.server_declared`, `mcp.arbitrary_command`, `mcp.remote_server` | `.mcp.json` поднимает сервер с произвольной командой (`bash -c …`) или удалённый хост, куда уходит сессия |
| **npm lifecycle** (нет у источника) | `npm.lifecycle_script`, `npm.obfuscated_lifecycle` | `postinstall/preinstall`, исполняющий код при `npm install`; вскрывает и локальный скрипт, который тот вызывает (кейс camofox — postinstall маскировал `spawn`) |
| Файловая система | `fs.symlink`, `fs.binary_artifact` | симлинк (содержимое не проверено, может указывать наружу); исполняемый бинарник без исходников |

### Как читать результат

- **CRITICAL** — не устанавливать, пока не понятно, зачем это в пакете.
- **WARN** — бывает легитимно (хук, MCP-сервер, объявленный `allowed-tools`), но должно быть заявлено в README пакета; сверь, что ожидаемо.
- Правила ловят **форму, а не смысл**: текст про безопасность/LLM может совпасть (напр. статья, объясняющая инъекции). Всегда смотри строку в контексте — `> excerpt` печатается рядом.
- ЧИСТО — не гарантия: прочитай `SKILL.md` и скрипты глазами. Скан — первый барьер, не последний.

### Расширение правил

Правила инлайн в `scripts/skill_injection_scan.py`: текстовые — `_TEXT_RULES`, кодовые — `_CODE_RULES`, структурные (JSON) — функции `_scan_hooks` / `_scan_mcp` / `_scan_package_json` / `_scan_json_file`. Полный список id — `--list-rules`. Для разового доверия — `--allow RULE_ID`, не редактируй файл.
