---
name: multi-model-gateway
description: "Orchestrate tasks across Claude, GPT, and Gemini via AI Gateway. Use when user asks for cross-model comparison, multi-model consensus, or wants to leverage specific model strengths."
---

# Multi-Model Gateway Orchestrator

Route tasks to the best AI model (or multiple models) through AI Gateway v2.

## When to use

- "compare models", "ask GPT", "ask Gemini", "cross-model", "consensus"
- Tasks that benefit from a specific model's strengths
- Validation: run same analysis through 2-3 models, compare results
- When one model is rate-limited, route to another

## Available Models

### Claude (native in Claude Code, also via gateway)
| Model | ID | Best for |
|-------|----|----------|
| Opus 4.6 | `claude-opus-4-6` | Deep reasoning, architecture, complex analysis |
| Sonnet 4.5 | `claude-sonnet-4-5-20250929` | Most tasks, code gen, balanced |
| Haiku 4.5 | `claude-haiku-4-5-20251001` | Fast classification, simple tasks |

### OpenAI (via gateway)
| Model | ID | Best for |
|-------|----|----------|
| GPT-5.4 | `gpt-5.4` | Latest flagship, best quality |
| GPT-5.4 Pro | `gpt-5.4-pro` | Pro tier, higher limits |
| GPT-5.1 Codex | `gpt-5.1-codex` | Code generation |
| GPT-4.1 | `gpt-4.1` | Balanced quality/speed |
| GPT-4.1 Mini | `gpt-4.1-mini` | Fast, cheap |
| o4-mini | `o4-mini` | Reasoning, math (latest) |
| o3-pro | `o3-pro` | Deep reasoning (premium) |

### Gemini (via gateway)
| Model | ID | Best for |
|-------|----|----------|
| Gemini 3.1 Pro | `gemini-3.1-pro-preview` | Latest flagship |
| Gemini 3 Flash | `gemini-3-flash-preview` | Fast, good quality |
| Gemini 2.5 Pro | `gemini-2.5-pro` | Stable, 2M context |
| Gemini 2.5 Flash | `gemini-2.5-flash` | Fast, long context |
| Deep Research | `deep-research-pro-preview` | In-depth research |

## Gateway Access

```bash
# Local gateway (start once):
cd ${WORKSPACE}/projects/ai-gateway && GATEWAY_CONFIG=./config.local.yaml uvicorn app.main:app --port YOUR_PORT &

# Call any model:
curl -s http://localhost:GATEWAY_PORT/v1/messages \
  -H "Content-Type: application/json" \
  -d '{
    "model": "MODEL_NAME",
    "max_tokens": 4096,
    "messages": [{"role": "user", "content": "PROMPT"}]
  }'
```

## Orchestration Patterns

### Pattern 1: Best Model Selection
Analyze the task and pick the optimal model:

| Task type | Recommended model |
|-----------|------------------|
| Complex architecture | Claude Opus 4.6 (native) |
| Code generation | Claude Sonnet 4.5 (native) |
| Quick classification | Claude Haiku 4.5 (native) |
| Alternative perspective | GPT-5.4 (via gateway) |
| Code gen (OpenAI) | gpt-5.1-codex (via gateway) |
| Large document analysis | Gemini 3.1 Pro (via gateway) |
| Deep research | deep-research-pro-preview (via gateway) |
| Math/logic problems | o4-mini (via gateway) |
| Deep reasoning | o3-pro (via gateway) |

### Pattern 2: Cross-Model Consensus
Run the same prompt through 2-3 models, then synthesize:

```
1. Send to Claude (native) → result_claude
2. Send to GPT-5.4 (gateway) → result_gpt
3. Send to Gemini 3.1 Pro (gateway) → result_gemini
4. Compare and synthesize best answer
```

Use `dispatching-parallel-agents` skill to run agents in parallel.

### Pattern 3: Chain of Models
Each model does what it's best at:

```
1. Gemini 3.1 Pro → summarize large input (2M context)
2. Claude Opus 4.6 → deep analysis of summary
3. GPT-5.4 → format as structured JSON output
```

## Agents

| Agent | Description |
|-------|-------------|
| `gpt-agent` | Calls GPT models via gateway |
| `gemini-agent` | Calls Gemini models via gateway |

Claude models are called natively (no gateway needed for Claude Code).

## Dispatching Example

```
# Ask GPT for a second opinion:
Agent(subagent_type="gpt-agent", prompt="Analyze this architecture: ...")

# Ask Gemini to process a large doc:
Agent(subagent_type="gemini-agent", prompt="Summarize this 100-page doc: ...")

# Parallel consensus (both at once):
Agent(subagent_type="gpt-agent", prompt="...", run_in_background=true)
Agent(subagent_type="gemini-agent", prompt="...", run_in_background=true)
```

## Response Format

When presenting multi-model results:

```
## Cross-Model Analysis

### Claude Opus 4.6 (native)
[result]

### GPT-5.4 (via Gateway)
[result]

### Gemini 3.1 Pro (via Gateway)
[result]

### Synthesis
[combined best answer with reasoning]
```

## Admin & Monitoring

- Dashboard: https://gateway.your-monitoring-domain.com/admin (admin / YOUR_GATEWAY_PASSWORD)
- Stats API: `curl -u admin:YOUR_GATEWAY_PASSWORD https://gateway.your-monitoring-domain.com/admin/stats?hours=24`
- Logs API: `curl -u admin:YOUR_GATEWAY_PASSWORD https://gateway.your-monitoring-domain.com/admin/logs?limit=50`
