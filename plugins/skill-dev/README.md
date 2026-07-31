# Skill & Agent Dev

> Author skills/agents/plugins/MCP, prompt engineering, Claude API & CLI.

Part of the **[hamidun marketplace](../../README.md)**.

## What's inside

| Skill | What it does |
|-------|--------------|
| `claude-api` | Anthropic Claude API (ANTHROPIC_API_KEY) из Python: text generation, vision, tool use, streaming. |
| `claude-cli-runner` | Запуск моделей Claude из Python БЕЗ API-ключа — через claude CLI binary с авторизацией подписки Claude Code. |
| `content-policy` | What NOT to reproduce — protected UI of big companies, unverified brands. The legal and ethical boundary. |
| `context-engineering` | Паттерны оптимизации контекста LLM: progressive disclosure, semantic compression, structured references, summary-first / layered / delta /… |
| `llm-evals` | Evaluate LLMs and agents — golden sets, two-tier grading (programmatic metrics + LLM judge), model sweeps, keep/rollback verdicts. |
| `mcp-builder` | Guide for building high-quality MCP (Model Context Protocol) servers in Python (FastMCP) or Node/TypeScript (MCP SDK). |
| `prompt-engineering` | Промпт-инжиниринг: системные промпты, few-shot, chain-of-thought, structured outputs, декомпозиция, оценка и итерация промптов. |
| `sharing-skills` | Use when you've developed a broadly useful skill and want to contribute it upstream via pull request |
| `skill-creator` | Create new skills, modify and improve existing skills, and measure skill performance. |
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
