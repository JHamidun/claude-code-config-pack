# Skill & Agent Dev

> Author skills/agents/plugins/MCP, prompt engineering, Claude API & CLI.

Part of the **[hamidun marketplace](../../README.md)**.

## What's inside

| Skill | What it does |
|-------|--------------|
| `claude-api` | Claude API из Python по ключу ANTHROPIC_API_KEY: vision, tool use, batch. |
| `claude-cli-runner` | Запуск Claude из Python БЕЗ API-ключа — claude CLI по подписке; модуль claude_cli.py. |
| `content-policy` | Что НЕ воспроизводить: защищённые UI крупных продуктов, бренды, шрифты, brand-цвета. |
| `context-engineering` | Оптимизация контекста LLM: progressive disclosure, компрессия, structured references. |
| `llm-evals` | Эвалы LLM/агентов: golden-set, LLM-судья + метрики, вердикт keep/rollback, свип моделей и effort. |
| `mcp-builder` | Разработка MCP-серверов (Python FastMCP / TS SDK) и дизайн инструментов агента. |
| `prompt-engineering` | Промпт-инжиниринг: системные промпты, few-shot, structured outputs. |
| `sharing-skills` | Отправка своего навыка в upstream-репозиторий через PR: ветка, коммит, пуш. |
| `skill-creator` | Создание, правка и эвалы навыков, оптимизация description. |
| `tool-search-protocol` | До отказа «нет интеграции» с Slack/Drive/Linear — сначала поиск инструмента через ToolSearch и claude mcp list. |
| `web-to-cli` | CLI для сервиса без API и MCP по трафику своей сессии: карта API, клиент с doctor и dry-run. |

### Agents

- `meta-agent-v3`
- `prompt-engineer`

## Install

```text
/plugin marketplace add JHamidun/claude-code-config-pack
/plugin install skill-dev@hamidun
```

Enable it with `/plugin` — the skills then activate automatically when relevant.

## Credits

sharing-skills is adapted from **Superpowers** by Jesse Vincent / Prime Radiant — https://github.com/obra/superpowers.

## Related plugins

`ai-gateways`

---

MIT © [Zhemal Khamidun](https://github.com/JHamidun)
