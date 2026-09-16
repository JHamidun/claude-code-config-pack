---
name: multi-model-gateway
description: "Прогон задачи через Claude, GPT и Gemini разом (AI Gateway) + GPT-6 Astra через Codex CLI. Триггеры: «спроси GPT», «второе мнение», «cross-model», «астра», «через кодекс», «codex exec»."
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
| Opus 5 | `claude-opus-5` | Deep reasoning, architecture, complex analysis (дефолт оркестратора) |
| Fable 5.1 | `claude-fable-5-1` | Text-субагенты/воркеры (канон, ≤5 одновременно); `claude-fable-5` — Legacy |
| Sonnet 5 | `claude-sonnet-5` | Most tasks, code gen, balanced |
| Haiku 4.5 | `claude-haiku-4-5-20251001` | Fast classification, simple tasks |

Канон актуальных ID → `config/models.md`.

### OpenAI (via gateway)
| Model | ID | Best for |
|-------|----|----------|
| GPT-6 Astra | `gpt-6-astra` | Максимум; но по подписке — через Codex CLI, см. ниже |
| GPT-5.6 Sol | `gpt-5.6-sol` (алиас `gpt-5.6`) | Рабочий дефолт, он же deep research |
| GPT-5.6 Terra | `gpt-5.6-terra` | Быстрый; сюда же ушла математика и структурный reasoning |
| GPT-5.6 Luna | `gpt-5.6-luna` | Дешёвый, массовые прогоны |
| GPT-4.1 / Mini | `gpt-4.1` / `gpt-4.1-mini` | Живы; ⚠️ `gpt-4.1-nano` снимается 23.10.2026 |

> ⛔ **Строки, которые тут стояли до 09.09.2026, вели в никуда.** Вся линейка
> `*-codex` в API закрыта 23.07.2026 (`gpt-5-codex`, `gpt-5.1-codex`,
> `gpt-5.1-codex-max`, `gpt-5.2-codex`), вся o-серия свёрнута в GPT-5.6:
> `o3-deep-research` и `o4-mini-deep-research` выключены 23.07.2026, `o4-mini`
> и `o3-mini` снимаются 23.10.2026, `o3` и `o3-pro` — 11.12.2026, `gpt-5.2` —
> вместе с `gpt-5-*` 11.12.2026. Даты и замены — `config/models.md`.
> Практический смысл: «Codex» больше не название модели, а название CLI.

### GPT-6 Astra — через Codex CLI, НЕ через gateway и НЕ через MCP

Самая сильная внешняя модель на сегодня (по бенчмаркам обходит Fable).
Владелец: «через сли, мсп криво работает». Значит путь один — `codex exec`.

```bash
codex exec -m gpt-6-astra \
  -c model_reasoning_effort="xhigh" \
  -s read-only --skip-git-repo-check \
  -C <корень проекта> [--add-dir <соседний репозиторий>] \
  - < prompt.md > out.md 2>&1
```

Дефолты из `~/.codex/config.toml`: `model = "gpt-6-astra"`, эффорт — какой
стоит в конфиге сейчас (10.09 там `ultra`, раньше был `medium`) — **эффорт
всегда перебивай явно**, иначе получишь чужой дефолт и не заметишь.

**Эффорт: `low` · `medium` · `high` · `xhigh` · `max` · `ultra`.** Проверено
10.09 на CLI 0.153.4:

- **`ultra` — не уровень API, а режим самого CLI.** API принимает только
  `none, minimal, low, medium, high, xhigh, max` (так он сам перечислил в
  ошибке 400). Каталог моделей, вшитый в `codex.exe`, описывает `ultra` как
  «Maximum reasoning with automatic task delegation», то есть максимальное
  рассуждение плюс автоматическая раздача подзадач. Прогон с `ultra` проходит
  без ошибок. Что именно уходит в API, по трафику не проверено.
- **Опечатка ловится только API, посреди прогона.** Codex не проверяет эффорт
  при разборе конфига: `-c model_reasoning_effort="bogus"` запускается тихо и
  падает уже ответом `400 invalid_enum_value`.
- Дефолт эффорта для Astra в каталоге CLI — `low`.

#### Промпт под Astra пишется НЕ так, как под Claude

Правило, которое легко применить наоборот, потому что оно противоположно
свежим рекомендациям Anthropic. Про Claude нового поколения доки говорят
**убирать** лишнее: «перепроверь себя», напор на использование инструментов,
запреты на форматирование — всё это теперь мешает и подлежит удалению.

**У OpenAI ровно обратное.** Их доки просят инструкции **проверить и усилить**:
Astra исполняет написанное буквальнее прежних моделей, поэтому недосказанное
она не додумывает, а игнорирует — и наоборот, точную и полную формулировку
отрабатывает лучше.

Практический вывод: **промпт, ужатый под Claude, нельзя переносить в Astra
как есть** — под неё его надо дописывать. Общий на обе модели промпт означает,
что одна из них получает неподходящий; лучше два файла, чем один компромиссный.

#### Пять граблей, каждая стоила времени

**1. `&` убивает прогон.** `codex exec ... &` внутри задачи Bash — потомок
оболочки, а не харнесса; оболочка завершается, процесс уходит с ней. Симптом
обманчив: задача рапортует `exit 0`, файл отчёта создан и пуст, выглядит как
«модель долго думает». Диагноз за один вызов:
`ls -lat ~/.codex/sessions/<год>/<мес>/<день>/` — нет файлов после времени
запуска, значит процесс не жил.
**Правильно:** один прогон = одна задача Bash с `run_in_background: true`
и БЕЗ `&`. Несколько прогонов — несколько вызовов в одном сообщении, пойдут
параллельно, и харнесс сам пришлёт уведомление о каждом (будильник даром).

**2. Промпт — файлом через stdin, не аргументом.** Русский текст с кавычками,
переносами и обратными слешами в аргументе командной строки рвётся. Пиши
`prompt.md`, подавай `- < prompt.md`.

**3. Вывод — это ВСЯ трасса сессии, 0,5–0,9 МБ на прогон.** Не читай целиком:
ответ в конце. `tail -c 20000 out.md`, либо ищи по заголовкам своего же
запрошенного формата.

**4. Отказ от задачи — это формулировка, а не модель.** Прямой запрос «найди
дыры в блоклисте» получил «flagged for possible cybersecurity risk».
Тот же вопрос как **защитный аудит покрытия** («мы мейнтейнеры, репо наше,
проверь полноту защитного списка») отработал и дал настоящую находку —
`shred /dev/sda` и `wipefs -a /dev/sda` проходили сквозь безусловный пол.
Переформулируй, прежде чем считать, что модель не умеет.

**5. Свои замеры она уточняет — проверяй за ней.** В разборе русских
паттернов Astra прямо поправила мою цифру («в текущем checkout `read_secrets`
не срабатывает, приписывать ему этот FP нельзя»). Это её сильная сторона, но
и повод не переносить её числа в отчёт не глядя: она меряет тот checkout,
который видит СЕЙЧАС, а дерево под ней меняется, если параллельно идёт рой.
Сверяй время файла отчёта со временем своей последней правки.

#### Где она особенно хороша

Края и полнота списков: чего в перечислении не хватает, где паттерн шире или
уже, чем заявлено, какой класс входа не покрыт. Хуже — там, где нужен замер
живой системы, а не чтение.

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
cd ./work/ai-gateway && GATEWAY_CONFIG=./config.local.yaml uvicorn app.main:app --port 8200 &   # свой локальный gateway; пак его не несёт

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
| Complex architecture | Claude Opus 5 (native) |
| Code generation | Claude Sonnet 5 (native) |
| Quick classification | Claude Haiku 4.5 (native) |
| Alternative perspective | `gpt-5.6-sol` (via gateway) |
| Code gen (OpenAI) | `gpt-6-astra` — **через Codex CLI**, отдельной кодовой модели больше нет |
| Large document analysis | Gemini 3.1 Pro (via gateway) |
| Deep research | `deep-research-pro-preview` (Google) или `gpt-5.6-sol` (OpenAI) |
| Math/logic problems | `gpt-5.6-terra` (via gateway) |
| Deep reasoning | `gpt-6-astra` с `effort=xhigh` (via Codex CLI) |

### Pattern 2: Cross-Model Consensus
Run the same prompt through 2-3 models, then synthesize:

```
1. Send to Claude (native) → result_claude
2. Send to GPT-5.6 (gateway) → result_gpt
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
2. Claude Opus 5 → deep analysis of summary
3. GPT-5.6 → format as structured JSON output
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

### Claude Opus 5 (native)
[result]

### GPT-5.6 (via Gateway)
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

**Зеркальная ловушка на стороне Claude:** у Claude 4.7 и новее (Opus 5, Sonnet 5,
Fable 5.1) ручек `temperature` / `top_p` / `top_k` больше нет — недефолтное значение
даёт 400, а в Python SDK v1.0+ параметра нет вовсе и получится `TypeError`. Ветку
Anthropic по шаблону выше не копировать: сэмплинг не передавать, «креативность»
регулировать промптом и `effort`.

### 3. Fallback chain с last_error reporting

Один primary + список fallbacks. В логах `tried` + `last_error` — без них дебажить «всё упало» нельзя:

```python
DEFAULT = os.environ.get("AGENT_MODEL", "gpt-5-mini")  # id из config/models.md; gpt-5.4-* в каноне нет
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
