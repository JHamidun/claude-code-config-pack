# Multi-Model Gateways

> Route to GPT, Gemini, Kimi, DeepSeek, Perplexity for cross-model work.

Part of the **[hamidun marketplace](../../README.md)**.

## What's inside

| Skill | What it does |
|-------|--------------|
| `deepseek` | DeepSeek API (DEEPSEEK_API_KEY, deepseek-chat, OpenAI-совместимый эндпоинт) — кодогенерация, рефакторинг, reasoning, 128K контекст. |
| `gemini-3-pro` | Google AI Suite через API (GOOGLE_API_KEY): Gemini text (2M контекст), embeddings, TTS/STT (Live API), code execution, Google Search grounding… |
| `kimi` | Kimi K2 (Moonshot AI, KIMI_API_KEY, kimi-k2-thinking) — глубокий reasoning, код-анализ, алгоритмы. |
| `multi-model-gateway` | Orchestrate tasks across Claude, GPT, and Gemini via AI Gateway. |
| `perplexity` | Perplexity — веб-поиск и research с реалтайм-информацией и источниками. |

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
