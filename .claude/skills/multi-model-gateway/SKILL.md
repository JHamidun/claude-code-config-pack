---
name: multi-model-gateway
description: "Прогон задачи через Claude, GPT и Gemini разом (AI Gateway): сравнение, консенсус. Триггеры: «спроси GPT», «второе мнение», «cross-model»."
---

> ⚠️ **NO-KEY GUARD (обязательно):** этот функционал требует ОПЦИОНАЛЬНОГО стороннего API-ключа. Перед вызовом проверь ключ в `.credentials.master.env`. Если ключ отсутствует, пустой или placeholder (`your_*_api_key`) — **НЕ проси пользователя оплатить счёт, включить биллинг или купить API**. Скажи одной строкой: «Эта функция опциональна и требует свой API-ключ (например, бесплатный ключ на aistudio.google.com); из коробки всё остальное работает по подписке Claude» — и предложи альтернативу или продолжай без неё.

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
| Opus 4.8 | `claude-opus-4-8` | Deep reasoning, architecture, complex analysis (дефолт оркестратора) |
| Fable 5 | `claude-fable-5` | Text-субагенты/воркеры (канон, ≤5 одновременно) |
| Sonnet 4.5 | `claude-sonnet-4-5-20250929` | Most tasks, code gen, balanced |
| Haiku 4.5 | `claude-haiku-4-5-20251001` | Fast classification, simple tasks |

Канон актуальных ID → `config/models.md`.

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
cd ${WORKSPACE}/projects/ai-gateway && GATEWAY_CONFIG=./config.local.yaml uvicorn app.main:app --port 8200 &

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
| Complex architecture | Claude Opus 4.8 (native) |
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

#### Consensus verification protocol (mandatory for Pattern 2)

1. **MODEL_ECHO** — в каждый промпт добавляй: «First line of your reply MUST be: `MODEL_ECHO=<exact model id you are running as>`». Ловит silent fallback (gateway/провайдер тихо подменил модель — «консенсус GPT+Gemini» на деле два ответа одной модели). Эхо не совпало с запрошенной моделью → пометить ответ как degraded.
2. **Триаж вместо свалки** — раскладывай ответы в четыре списка, а не в общий синтез:
   - `AGREEMENTS` — сходятся 2+ модели;
   - `<MODEL>-only` — уникальные факты/аргументы одной модели (отдельный список на каждую);
   - `CONFLICTS` — одно утверждение, разные значения/выводы (каждый конфликт адьюдицировать, не усреднять).
3. **Rule D: evidence > votes** — конфликты НЕ решаются подсчётом голосов. Одна модель с проверяемым первоисточником (URL резолвится, значение есть на странице) бьёт консенсус двух без источника: тренировочные корпуса пересекаются, согласие-без-источника — слабый сигнал (consensus hallucination). Согласие всех моделей без первоисточника — жёлтый флаг, помечай `[CONSENSUS-only]`, не выдавай за факт.

### Pattern 3: Chain of Models
Each model does what it's best at:

```
1. Gemini 3.1 Pro → summarize large input (2M context)
2. Claude Opus 4.8 → deep analysis of summary
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

### Claude Opus 4.8 (native)
[result]

### GPT-5.4 (via Gateway)
[result]

### Gemini 3.1 Pro (via Gateway)
[result]

### Synthesis
[combined best answer with reasoning]
```

## Admin & Monitoring

- Credentials: из .credentials.master.env (GATEWAY_ADMIN_USER / GATEWAY_ADMIN_PASSWORD). Экспортируй в шелл перед curl: `export GATEWAY_ADMIN_USER=... GATEWAY_ADMIN_PASSWORD=...`
- Dashboard: https://gateway.your-monitoring-domain.com/admin (логин из .credentials.master.env)
- Stats API: `curl -u "$GATEWAY_ADMIN_USER:$GATEWAY_ADMIN_PASSWORD" https://gateway.your-monitoring-domain.com/admin/stats?hours=24`
- Logs API: `curl -u "$GATEWAY_ADMIN_USER:$GATEWAY_ADMIN_PASSWORD" https://gateway.your-monitoring-domain.com/admin/logs?limit=50`

---

## Production patterns — direct multi-provider client

Когда нужно ходить мимо AI Gateway (latency-critical, gateway недоступен, dev/staging без gateway-сетки), реализуй прямого мульти-провайдерного клиента в коде агента.

### 1. Provider routing by model name prefix

Маршрутизация по началу имени модели — не нужен лишний `--provider` параметр:

```python
def _route(model: str):
    m = model.lower()
    if m.startswith("claude"):
        return _anthropic_call
    if m.startswith("gemini"):
        return _gemini_call
    if m.startswith(("gpt", "o1", "o3", "o4", "chatgpt")):
        return _openai_compat("https://api.openai.com/v1/chat/completions", OPENAI_KEY)
    if m.startswith(("kimi", "moonshot")):
        return _openai_compat("https://api.moonshot.cn/v1/chat/completions", KIMI_KEY)
    if m.startswith("mistral"):
        return _openai_compat("https://api.mistral.ai/v1/chat/completions", MISTRAL_KEY)
    if m.startswith("deepseek"):
        return _openai_compat("https://api.deepseek.com/v1/chat/completions", DEEPSEEK_KEY)
    if m.startswith(("grok", "xai")):
        return _openai_compat("https://api.x.ai/v1/chat/completions", XAI_KEY)
    if m.startswith(("sonar", "pplx", "llama-3.1-sonar")):
        return _openai_compat("https://api.perplexity.ai/chat/completions", PPLX_KEY)
    return _openai_compat(AI_GATEWAY_URL + "/chat/completions", GATEWAY_KEY)
```

Anthropic и Gemini нужны отдельные функции — у них своя schema (Anthropic Messages API, Gemini generateContent). Остальные OpenAI-совместимые — одна функция с разным base URL.

### 2. GPT-5.x trap — `max_completion_tokens` (не `max_tokens`)

**HTTP 400** на любую GPT-5.x / o-series модель если передаёшь `max_tokens`:

```text
"Unsupported parameter: 'max_tokens' is not supported with this model.
 Use 'max_completion_tokens' instead."
```

Дискриминатор:

```python
def _uses_max_completion_tokens(model: str) -> bool:
    m = model.lower()
    return m.startswith(("gpt-5", "o1", "o3", "o4"))

if _uses_max_completion_tokens(model):
    payload["max_completion_tokens"] = max_tokens
    # gpt-5 / o-series IGNORE temperature — некоторые версии 400 на её передачу
else:
    payload["max_tokens"] = max_tokens
    payload["temperature"] = temperature
```

`gpt-4o*` — старая schema. Только `gpt-5*` / `o*` — новая.

### 3. Fallback chain с last_error reporting

Один primary + список fallbacks. В логах `tried` + `last_error` — без них дебажить «всё упало» нельзя:

```python
DEFAULT = os.environ.get("AGENT_MODEL", "gpt-5.4-mini")
FALLBACK = [m for m in os.environ.get(
    "AGENT_MODEL_FALLBACK",
    "gemini-3-flash-preview,deepseek-chat,kimi-k2-0905-preview"
).split(",") if m]

def chat(messages, *, model=None, **kwargs):
    tried, last_error = [], "no attempt"
    for m in [model or DEFAULT, *FALLBACK]:
        tried.append(m)
        try:
            return _route(m)(m, messages, **kwargs)
        except Exception as e:
            last_error = f"{m}: {type(e).__name__}: {str(e)[:160]}"
            log.warning("model %s failed: %s", m, last_error)
    raise RuntimeError(f"all models failed ({', '.join(tried)}): {last_error}")
```

### 4. Orphan-tool-message filter ⚠️ CRITICAL

Если хранишь tool-call trace между ходами агента (обязательно для tool-driven агентов — иначе LLM забывает `draft_ts` который только что вернул `generate_draft`), кросс-провайдерный fallback ломается.

OpenAI / DeepSeek / Kimi (strict OpenAI schema) **возвращают HTTP 400** если в `messages` есть `role: "tool"` без предшествующего `role: "assistant"` с матчащим `tool_calls[*].id`. Случается когда:

- LLM упал mid-loop (timeout, 5xx) и в memory успели лечь tool-результаты без assistant.tool_calls
- Конкурентные writes в history.jsonl
- Reset частичной памяти

Симптом:

```text
HTTP 400: {"error": {"message": "Messages with role 'tool' must be a response
to a preceding message with 'tool_calls'"}}
```

И **все** провайдеры из fallback chain валятся — история одна на всех.

Фильтр **перед** запросом:

```python
def filter_orphan_tools(hist: list[dict]) -> list[dict]:
    cleaned = []
    expecting_ids: set[str] = set()
    for m in hist:
        role = m.get("role")
        if role == "assistant":
            tcs = m.get("tool_calls") or []
            expecting_ids = {tc["id"] for tc in tcs if tc.get("id")}
            cleaned.append(m)
        elif role == "tool":
            tcid = m.get("tool_call_id")
            if tcid in expecting_ids:
                cleaned.append(m)
                expecting_ids.discard(tcid)
            # else: drop orphan silently
        else:
            expecting_ids.clear()
            cleaned.append(m)
    return cleaned
```

Идемпотентный — можно применять перед каждым `_route(m)` вызовом.

### 5. Tool-call trace persistence

Сохранять только финальный `assistant.content` недостаточно — теряется состояние tool-loop. Pattern:

```python
def respond(user_id, user_text):
    hist = memory.load(user_id)
    hist = filter_orphan_tools(hist)
    messages = [system_prompt, *hist, {"role": "user", "content": user_text}]
    memory.append(user_id, {"role": "user", "content": user_text})

    base_len = len(messages)
    final_text, full_trace = run_tool_loop(messages)  # returns (str, list[dict])

    # Записать ВСЕ новые messages турна: assistant.tool_calls + tool результаты
    for msg in full_trace[base_len:]:
        memory.append(user_id, msg)

    memory.append(user_id, {"role": "assistant", "content": final_text})
    return final_text
```

Без этого на следующем ходу нет `draft_ts` в контексте — агент спрашивает «какой draft_ts вы имеете в виду?» вместо того чтобы помнить.

### 6. Cred lazy loader (env → file → docker secret)

Единая точка чтения секретов, никогда не логируется:

```python
from functools import lru_cache

@lru_cache(maxsize=1)
def _file_creds() -> dict[str, str]:
    out = {}
    home = Path.home() / ".claude" / ".credentials.master.env"
    if home.exists():
        for line in home.read_text(encoding="utf-8").splitlines():
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            out[k.strip()] = v.strip().strip('"').strip("'")
    return out

def cred_get(name: str, default=None):
    if name in os.environ and os.environ[name]:
        return os.environ[name]
    fc = _file_creds()
    if name in fc and fc[name]:
        return fc[name]
    ds = Path(f"/run/secrets/{name}")
    if ds.exists():
        return ds.read_text(encoding="utf-8").strip()
    return default

def cred_require(name: str) -> str:
    v = cred_get(name)
    if not v:
        raise RuntimeError(f"credential {name} not found")
    return v
```

Один pattern — все провайдеры. Никаких `os.environ["OPENAI_API_KEY"]` разбросанных по коду.
