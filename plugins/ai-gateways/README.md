# Multi-Model Gateways

> Route to GPT, Gemini, Kimi, DeepSeek, Perplexity for cross-model work; Jev decision model for yes/no, choice and scoring.

Part of the **[hamidun marketplace](../../README.md)**.

## What's inside

| Skill | What it does |
|-------|--------------|
| `deepseek` | DeepSeek API (deepseek-chat): кодогенерация, reasoning, 128K контекст. |
| `gemini-3-pro` | Google AI API (GOOGLE_API_KEY): Gemini text 2M контекст, embeddings, TTS, grounding. |
| `jev` | Jev (TypeSafe) — модель решений вместо LLM: да/нет, выбор из N, оценка по шкале за 0,3 с и копейки. |
| `kimi` | Kimi K2 (Moonshot AI, KIMI_API_KEY, kimi-k2-thinking): глубокий reasoning, код-анализ, алгоритмы. |
| `multi-model-gateway` | Прогон задачи через Claude, GPT и Gemini разом (AI Gateway) + GPT-6 Astra через Codex CLI. |
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
