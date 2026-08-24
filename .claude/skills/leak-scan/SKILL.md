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
| **ИСХОДЯЩЕЕ** (мои данные наружу) | `scripts/leak_scan.py` | «не утечёт ли что-то личное, если я это опубликую?» | общие формы секретов + твой личный словарь опознавания |
| **ВХОДЯЩЕЕ** (чужой код внутрь) | `scripts/skill_injection_scan.py` | «безопасно ли ставить этот скачанный скилл/плагин/агент?» | prompt-injection и тихий захват полномочий |

Оба скрипта — чистый stdlib Python, UTF-8 stdout (Windows-совместимо), **ничего не меняют на диске**. Направления независимы: перед публикацией своего — ИСХОДЯЩЕЕ; перед установкой чужого с GitHub — ВХОДЯЩЕЕ.

---

## ИСХОДЯЩЕЕ: PII/деанон перед публикацией (`leak_scan.py`)

Single consolidated scanner (`scripts/leak_scan.py`) that finds personal-data and deanonymization leaks before anything goes public. Pure Python UTF-8 — it exists because of a hard-won lesson.

Паттерны живут в двух слоях, и это принципиально:

| Слой | Где лежит | Что ищет |
|------|-----------|----------|
| `GENERIC_PATTERNS` | в самом `leak_scan.py` | формы секретов, ни к кому не привязанные: `sk-ant`, `AIza`, `ghp_`, JWT, токены ботов, SMTP-ключи, форматы телефонов, невидимый Unicode |
| `IDENTITY_PATTERNS` | **внешний файл, в пак НЕ входит** | твои имена, почты, домены, IP серверов, номера документов, названия клиентов |

Инструмент, который ищет утечки, сам легко становится крупнейшей из них: если личный
словарь лежит в коде, опубликовать сканер значит опубликовать каталог всего частного
разом. Поэтому второй слой вынесен наружу.

### Первый запуск: заведи свой словарь (5 минут, один раз)

```bash
# Windows
copy "%USERPROFILE%\.claude\skills\leak-scan\scripts\identity.example.json" "%USERPROFILE%\.claude\leak-scan-identity.json"
# macOS / Linux
cp ~/.claude/skills/leak-scan/scripts/identity.example.json ~/.claude/leak-scan-identity.json
```

Открой копию и впиши СВОИ признаки вместо заглушек (`YOURNAME`, `you@example.com`,
`your-domain.example`, `203.0.113.x`, `Acme Corp`) — по паре `["метка", "регулярка"]`.
Начни с малого: имя и фамилия во всех падежах, личные почты, домены, IP своих серверов,
имена клиентов. Дополняй по мере находок.

Скрипт ищет словарь по трём адресам, в порядке убывания приоритета: `$LEAK_SCAN_IDENTITY`
(путь в переменной окружения) → `~/.claude/leak-scan-identity.json` → `identity.local.json`
рядом со скиллом. Файл **не коммить** — он по определению личный.

Без словаря сканер продолжает работать, но ловит только общие формы секретов и печатает
предупреждение в stderr. Молчание при отсутствующем словаре — не «чисто», а «личное не
проверялось».

## Critical lesson — why this script, not grep

**`grep -F` with Cyrillic on Windows SILENTLY fails to match** (codepage mismatch) — it returns "clean" while leaks remain. NEVER verify depersonalization with grep/ripgrep for Russian text. ALWAYS use this Python UTF-8 scanner (or LLM agents) as the source of truth.

## Two-stage protocol (MANDATORY)

Regex alone gives FALSE confidence. A 248-pattern scan once passed a repo "clean" — then a semantic LLM review of the same repo found a real client name in an example, a live API credit-balance, real production resource names, a private multi-account auth gateway, and ToS-grey subscription-bypass tooling. None matched a literal pattern. So ALWAYS run BOTH stages before declaring clean:

**Stage 1 — regex scan** (`scripts/leak_scan.py`): catches literal tells (names, emails, IPs, keys, tokens, known clients, national IDs). Fast, deterministic, exhaustive for what it knows — but «что оно знает» о тебе задаёт твой `leak-scan-identity.json`, см. выше.

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

- `target` — directory (recursive) or single file. Scans text files by extension; skips only `.git/` and `__pycache__/`.
- `--allow SUBSTR` — extra allowlisted substring (repeatable) for project-specific intended strings.
- Output is forced UTF-8 (safe for Cyrillic on any console).

**Что НЕ проверено — печатается всегда, до вердикта.** Файлы с расширением вне
списка текстовых перечисляются блоком «НЕ ПРОВЕРЕНО», и тогда «CLEAN» звучит как
«чисто В ПРОВЕРЕННОЙ ЧАСТИ». Иначе «не смотрел» неотличимо от «посмотрел и не
нашёл» — на этом уже один раз проехал служебный `.canarybak` со словарём
детектора внутри.

Файлы с именем на `_` **раньше пропускались, теперь читаются** (имя ничего не
говорит о содержимом) и лишь помечаются в отчёте отдельной строкой — чтобы было
видно, что находка пришла из служебного черновика.

**Exit codes:** `0` clean · `1` matches found · `2` target not found.

```bash
# Quick gate before a push (note: pipe loses exit code — check the printed FOUND/CLEAN)
python ~/.claude/skills/leak-scan/scripts/leak_scan.py ./my-public-repo
```

## What it catches

| Group | Слой | Examples |
|-------|------|----------|
| Secrets | generic | `sk-ant`, `sk-proj`, `AIza`, `ghp_`, `xoxb`, `ntn_`, `pplx-`, JWT, Telegram bot tokens, SMTP-ключи |
| Secrets | generic (добавлено 22.08.2026) | легаси `sk-…48`, `github_pat_`, `gho_/ghu_/ghs_/ghr_`, AWS `AKIA…`, приватные ключи `-----BEGIN … PRIVATE KEY`, Stripe `sk_live_`/`rk_live_`, Telethon StringSession, присваивание вида `api_key = "…"` |
| Phone / national ID cues | generic | форматы телефонов, слова-маркеры номеров документов |
| Infra (generic) | generic | внутренние адреса Docker-моста |
| Stego | generic | zero-width characters |
| Identity | твой словарь | real names, handles, personal emails, personal domains |
| Infra (личная) | твой словарь | server IPs, gateway/hook ports, hostnames |
| Clients/brands | твой словарь | your employer, your clients (+ localized forms) |
| National IDs (значения) | твой словарь | конкретные номера твоих документов |
| Deanon fingerprints | твой словарь | timezone, specific hardware model, region defaults, telltale counts, voice IDs |

Строки нижней половины таблицы ищутся, **только если заведён** `leak-scan-identity.json`.

Allowlist covers placeholders (`your-username`, `YOUR_*`, `${HOME}`, `${WORKSPACE}`) and credited public OSS authors (garrytan, obra/Jesse Vincent, mvanhorn, Anthropic, …).

## Reading the results — intended vs real leak

Not every hit is a leak. After running, triage:

- **Real leak** → scrub: secrets, national IDs, server IPs, private client names, personal emails, hardware/timezone fingerprints.
- **Intended/unavoidable** → keep: a public marketplace's own `owner/repo` in its install command and `repository`/`author.url` fields necessarily name the repo. Decide identity policy (full name vs handle vs placeholder) with the user before deciding these are acceptable.
- **Baseline pre-existing** → if a hit already lives in the live public source, it was previously accepted; flag it but don't treat it as newly introduced.

To compare a new build against an already-published baseline, scan both and diff the hit sets by path.

## Extending patterns

- **Личные признаки** (твоё имя, домен, клиент) → в `~/.claude/leak-scan-identity.json`, а НЕ в код скрипта. Иначе сканер снова станет носителем утечки.
- **Новая форма секрета** (ключ очередного сервиса, чей префикс узнаваем) → `GENERIC_PATTERNS` в `scripts/leak_scan.py`: это безлично и полезно всем.
- **Ложные срабатывания-плейсхолдеры** → `ALLOWLIST_SUBSTRINGS` там же.
- **Разовая нарочная строка** → флаг `--allow SUBSTR`, без правки файлов.

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
