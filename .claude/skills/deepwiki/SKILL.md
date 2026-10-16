---
name: deepwiki
description: "Доки любого GitHub-репо через DeepWiki/gitmcp.io и llms.txt. Триггеры: «как устроен этот репозиторий». НЕ пакеты npm/pypi → rules/context7.md; свой репо → openwiki."
---

# DeepWiki: GitHub Repository Documentation

Fetch and analyze documentation for any GitHub repository.

## When to Use

- **DeepWiki**: Any GitHub repository documentation
- **Context7** (`rules/context7.md`, скрипт `~/.claude/tools/context7_docs.py`): npm/pypi packages with published docs

## Method 0 — llms.txt preflight (когда краулить придётся)

Многие проекты уже отдают готовый срез доков для LLM. Спросить — секунда, краулить — минуты,
поэтому пробуй preflight перед обходом сайта. Если точный путь к нужному файлу уже известен —
бери файл, preflight не нужен.

```bash
python ~/.claude/tools/llms_txt.py https://docs.example.com          # или сразу несколько доменов
python ~/.claude/tools/llms_txt.py https://svelte.dev --full --save ./llms   # llms-full.txt целиком
```

- `[FOUND]` → бери этот текст как источник, дальше по Methods 1-3 идти не нужно.
- `[NONE ]` → llms.txt нет, спокойно переходи к Method 1 (корректная деградация, не ошибка).

Проверяется `/llms.txt` и `/llms-full.txt` рядом с путём и в корне домена.
**Валидация по телу, а не по коду ответа:** SPA-сайты отдают 200 + HTML на любой
несуществующий путь (проверено: `your-domain.com/llms.txt` → 200 `text/html`), поэтому
скрипт режет HTML-заглушки и отдаёт `found=false` вместо вёрстки под видом доков.

Из Python: `from llms_txt import discover, parse` (`sys.path` → `~/.claude/tools`).

## Methods

### Method 1: gitmcp.io и deepwiki.com — GET-ом доки НЕ отдают (проверено 22.08.2026)

`https://gitmcp.io/{owner}/{repo}` — это **MCP-эндпоинт**, а не страница с документацией.
Обычный GET отвечает 200 + лендинг «как подключить этот MCP к Cursor / Claude Desktop /
Windsurf / VSCode»: весь текст страницы (≈3 000 знаков) — куски `mcp.json`. Документации
там нет ни строки, и WebFetch вернёт именно эти конфиги. Адрес годится только чтобы
подключить его как MCP-сервер — тянуть его WebFetch'ем бессмысленно.

`https://deepwiki.com/{owner}/{repo}` GET-ом отдаёт 200 и **оглавление вики + список
«Relevant source files»** — по нему видно, из чего собран репозиторий и какие темы
разобраны. Текст самих статей рисует скрипт, в HTML его нет (на подстранице возвращается
та же оболочка), так что за прозой — Method 2/3 или браузерный навык (`dev-browser`,
`playwright-automation`).

**Рабочий порядок:** Method 0 (llms.txt) → Method 2 (raw README) → Method 3 (gh api);
deepwiki.com — когда нужна карта репозитория, а не текст.

### Method 2: Raw GitHub README
```
WebFetch: https://raw.githubusercontent.com/{owner}/{repo}/HEAD/README.md
```
`HEAD` = дефолтная ветка репозитория, какой бы она ни была. Ветку `main` не зашивать:
у `langchain-ai/langchain` дефолтная — `master`, и `/main/README.md` отдаёт **404**,
тогда как `/HEAD/README.md` — 200 (проверено на нём и на `microsoft/playwright-python`).

### Method 3: GitHub API
```bash
gh api repos/{owner}/{repo}/readme --jq '.content' | base64 -d
```

## Process

1. User provides GitHub repo URL or name
2. Fetch documentation: Method 0 (llms.txt), затем Method 2 (raw README на `HEAD`)
3. If fails, fallback to Method 3 (`gh api`); карта репозитория — deepwiki.com
4. Summarize key sections: setup, API, examples
5. Answer user's specific questions about the repo

## Examples

```
User: "документация для langchain"
-> python ~/.claude/tools/llms_txt.py https://python.langchain.com   # Method 0
-> WebFetch https://raw.githubusercontent.com/langchain-ai/langchain/HEAD/README.md

User: "как использовать playwright python"
-> WebFetch https://raw.githubusercontent.com/microsoft/playwright-python/HEAD/README.md
```

## Notes
- For npm/pypi packages — Context7, но **скриптом, не MCP** (канон `rules/context7.md`):
  `python ~/.claude/tools/context7_docs.py search <name>` → `docs /org/project --topic <тема>`
- For private repos, use `gh` CLI with authenticated access
- Cache results in memory for repeated queries
