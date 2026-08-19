# Multi-Model Gateways

> Route to GPT, Gemini, Kimi, DeepSeek, Perplexity for cross-model work.

Part of the **[hamidun marketplace](../../README.md)**.

## What's inside

| Skill | What it does |
|-------|--------------|
| `deepseek` | DeepSeek API (deepseek-chat): кодогенерация, reasoning, 128K контекст. |
| `gemini-3-pro` | Google AI API (GOOGLE_API_KEY): Gemini text 2M контекст, embeddings, TTS, grounding. |
| `kimi` | Kimi K2 (Moonshot AI, KIMI_API_KEY, kimi-k2-thinking): глубокий reasoning, код-анализ, алгоритмы. |
| `multi-model-gateway` | Run a task across Claude, GPT and Gemini via AI Gateway: comparison, consensus, second opinion. |
| `perplexity` | Perplexity веб-поиск и research с источниками: дефолт pplx-max.py по подписке Max. |

### Agents

- `gemini-agent`
- `gpt-agent`
- `kimi-algorithm-specialist`

### Commands

- `/kimi-reasoning`

## Install

```text
/plugin marketplace add JHamidun/claude-code-config-pack
/plugin install ai-gateways@hamidun
```

Enable it with `/plugin` — the skills then activate automatically when relevant.

## Related plugins

`skill-dev`

---

MIT © [Zhemal Khamidun](https://github.com/JHamidun)
