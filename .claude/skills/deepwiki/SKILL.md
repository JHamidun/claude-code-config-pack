---
name: deepwiki
description: "Доки любого GitHub-репо через DeepWiki/gitmcp.io и llms.txt. Триггеры: «как устроен этот репозиторий»."
---

# DeepWiki: GitHub Repository Documentation

Fetch and analyze documentation for any GitHub repository.

## When to Use

- **DeepWiki**: Any GitHub repository documentation
- **Context7** (separate skill): npm/pypi packages with published docs

## Method 0 — llms.txt preflight (ВСЕГДА первым, до любого краулинга)

Многие проекты уже отдают готовый срез доков для LLM. Спросить — секунда, краулить — минуты.

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

### Method 1: gitmcp.io (preferred)
Convert any GitHub URL to gitmcp.io format:
```
https://github.com/{owner}/{repo} -> https://gitmcp.io/{owner}/{repo}
```

Fetch via WebFetch:
```
WebFetch: https://gitmcp.io/{owner}/{repo}
Prompt: "Get the main documentation, API reference, and getting started guide"
```

### Method 2: Raw GitHub README
```
WebFetch: https://raw.githubusercontent.com/{owner}/{repo}/main/README.md
```

### Method 3: GitHub API
```bash
gh api repos/{owner}/{repo}/readme --jq '.content' | base64 -d
```

## Process

1. User provides GitHub repo URL or name
2. Fetch documentation using Method 1 (gitmcp.io)
3. If fails, fallback to Method 2 or 3
4. Summarize key sections: setup, API, examples
5. Answer user's specific questions about the repo

## Examples

```
User: "документация для langchain"
-> WebFetch https://gitmcp.io/langchain-ai/langchain

User: "как использовать playwright python"
-> WebFetch https://gitmcp.io/microsoft/playwright-python
```

## Notes
- For npm packages, use Context7 MCP instead
- For private repos, use `gh` CLI with authenticated access
- Cache results in memory for repeated queries
