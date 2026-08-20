# Skill & Agent Dev

> Author skills/agents/plugins/MCP, prompt engineering, Claude API & CLI.

Part of the **[hamidun marketplace](../../README.md)**.

## What's inside

| Skill | What it does |
|-------|--------------|
| `claude-api` | Anthropic Claude API (ANTHROPIC_API_KEY) из Python: text, vision, tool use, streaming. |
| `claude-cli-runner` | Запуск Claude из Python БЕЗ API-ключа — claude CLI по подписке; модуль claude_cli.py. |
| `content-policy` | What NOT to reproduce — protected UI of big companies, unverified brands. The legal and ethical boundary. |
| `context-engineering` | Оптимизация контекста LLM: progressive disclosure, компрессия, structured references. |
| `llm-evals` | Evaluate LLMs and agents — golden sets, two-tier grading (programmatic metrics + LLM judge), model sweeps, keep/rollback verdicts. |
| `mcp-builder` | Разработка MCP-серверов (Python FastMCP / TS SDK) и дизайн инструментов агента. |
| `prompt-engineering` | Промпт-инжиниринг: системные промпты, few-shot, structured outputs. |
| `sharing-skills` | Отправка своего навыка в upstream-репозиторий через PR: ветка, коммит, пуш. |
| `skill-creator` | Создание, правка и эвалы навыков, оптимизация description. |
| `tool-search-protocol` | Don't refuse an MCP/connector capability outright — search via tool_search first; the tool may exist but be hidden. |

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
