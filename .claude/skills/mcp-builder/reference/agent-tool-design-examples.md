# Agent Tool Design — развёрнутые Python-примеры к каждому принципу

> [MERGED 2026-07-18] Бывший отдельный скилл `agent-tool-design`, влит в `mcp-builder` как reference.
> Ценность файла: рабочие Python-примеры к каждому принципу agent-centric design (разделы 1-10)
> + уникальный раздел 11 «Tool-loop ergonomics» — production-паттерны самого tool-loop'а
> (implicit args injection, error contract, idempotency, staged/auto mode, from_cache, MAX_TOOL_ITERATIONS).
> Загружай на Phase 1.1 (принципы) и при реализации tool-loop'а поверх OpenAI-совместимых API.

## Overview

Принципы проектирования инструментов специально для AI агентов. Основано на рекомендациях Anthropic Engineering.

## When to Use

- Создание MCP серверов
- Проектирование API для агентов
- Оптимизация существующих tools
- Review tool definitions

---

## 1. Ergonomic, Agent-Specific Design

**Ключевое отличие:** Tools должны быть спроектированы для недетерминистичных агентов, а не для детерминистичных систем.

### Плохо: Много мелких tools
```python
# Слишком много отдельных endpoints
@mcp.tool()
def list_users(): ...

@mcp.tool()
def list_events(): ...

@mcp.tool()
def create_event(): ...

@mcp.tool()
def check_availability(): ...
```

### Хорошо: Консолидированный workflow
```python
@mcp.tool()
def schedule_meeting(
    title: str,
    attendees: list[str],
    duration_minutes: int = 60,
    preferred_times: list[str] = None
) -> dict:
    """
    Schedule a meeting with automatic availability checking.

    Internally handles:
    - Looking up attendees
    - Checking calendar availability
    - Finding optimal time slot
    - Creating calendar event
    - Sending invitations

    Args:
        title: Meeting title
        attendees: List of email addresses or names
        duration_minutes: Meeting length (default 60)
        preferred_times: Optional list of preferred time ranges

    Returns:
        {
            "event_id": "evt_123",
            "scheduled_time": "2025-01-15 10:00",
            "attendees_confirmed": ["alice@co.com", "bob@co.com"],
            "calendar_link": "https://..."
        }
    """
    # Один tool делает полный workflow
```

---

## 2. Response Format Control

### Enum для выбора детализации
```python
from enum import Enum

class ResponseFormat(str, Enum):
    CONCISE = "concise"   # Экономит токены
    DETAILED = "detailed"  # Включает IDs для chaining

@mcp.tool()
def search_contacts(
    query: str,
    response_format: ResponseFormat = ResponseFormat.CONCISE
) -> str:
    """
    Search contacts by name, email, or organization.

    Args:
        query: Search query
        response_format:
            - "concise": Name and email only (saves tokens)
            - "detailed": Full profile with IDs for follow-up calls
    """
    contacts = db.search(query)

    if response_format == ResponseFormat.CONCISE:
        return "\n".join(f"- {c.name} <{c.email}>" for c in contacts)
    else:
        return json.dumps([{
            "id": c.id,
            "name": c.name,
            "email": c.email,
            "phone": c.phone,
            "organization": c.org,
            "last_interaction": c.last_seen
        } for c in contacts])
```

---

## 3. Semantic Identifiers

### Плохо: Криптографические UUIDs
```python
# Agent легко hallucinate-ит такие ID
return {"user_id": "a7f3b8c2-9d4e-5f6a-b1c2-d3e4f5a6b7c8"}
```

### Хорошо: Семантически осмысленные ID
```python
# Agent понимает и запоминает лучше
return {"user_id": "user_alice_smith_42"}

# Или 0-indexed для списков
return {"contacts": [
    {"index": 0, "name": "Alice"},
    {"index": 1, "name": "Bob"},
    {"index": 2, "name": "Charlie"}
]}
```

---

## 4. Actionable Error Messages

### Плохо: Технические ошибки
```python
raise McpError(ErrorCode.InvalidParams, "Error 400: Bad Request")
```

### Хорошо: Guidance в ошибках
```python
@mcp.tool()
def search_logs(
    query: str,
    start_date: str = None,
    end_date: str = None,
    limit: int = 100
) -> str:
    results = db.search_logs(query, start_date, end_date, limit)

    if len(results) >= limit:
        # Направляем agent к лучшей стратегии
        return json.dumps({
            "results": results[:limit],
            "truncated": True,
            "total_matches": db.count_matches(query),
            "suggestion": (
                "Results truncated. For more efficient searching, try:\n"
                "1. Add date filters: start_date='2025-01-01'\n"
                "2. Use more specific query terms\n"
                "3. Make multiple small searches rather than one broad query"
            )
        })

    return json.dumps({"results": results, "truncated": False})
```

---

## 5. Tool Namespacing

### Prefix-based grouping (рекомендуется)
```python
# По сервису
@mcp.tool()
def github_search_issues(): ...

@mcp.tool()
def github_create_pr(): ...

@mcp.tool()
def jira_search_issues(): ...

@mcp.tool()
def jira_create_ticket(): ...
```

### Или по ресурсу
```python
@mcp.tool()
def github_issues_search(): ...

@mcp.tool()
def github_issues_create(): ...

@mcp.tool()
def github_prs_search(): ...

@mcp.tool()
def github_prs_create(): ...
```

**Тестируй оба подхода** - разница в performance может быть значительной.

---

## 6. Description Best Practices

### Плохо: Минимальное описание
```python
@mcp.tool()
def search(q: str) -> str:
    """Search for stuff."""
```

### Хорошо: Как инструкция для нового коллеги
```python
@mcp.tool()
def search_knowledge_base(
    query: str,
    category: str = None,
    max_results: int = 10
) -> str:
    """
    Search the internal knowledge base for documentation and guides.

    The knowledge base contains:
    - Technical documentation (API specs, architecture)
    - Process guides (onboarding, deployment)
    - FAQs and troubleshooting

    Query syntax:
    - Simple text: "deployment guide"
    - Exact phrase: '"error handling"'
    - Exclude terms: "python -javascript"

    Categories available:
    - "technical": API docs, architecture
    - "process": How-to guides
    - "faq": Common questions

    Args:
        query: Search query (supports syntax above)
        category: Filter by category (optional)
        max_results: Maximum results to return (1-50, default 10)

    Returns:
        Markdown-formatted list of matching documents with:
        - Title and relevance score
        - Brief excerpt
        - Link to full document

    Example:
        search_knowledge_base("deploy docker", category="process")
    """
```

---

## 7. Parameter Naming

### Плохо: Неоднозначные имена
```python
def create_task(user, project, name): ...
```

### Хорошо: Явные имена
```python
def create_task(
    assignee_email: str,      # Не "user"
    project_id: str,          # Не "project"
    task_title: str,          # Не "name"
    due_date: str = None,
    priority: str = "medium"  # Явные defaults
): ...
```

---

## 8. Token Efficiency

### Eliminate Low-Signal Fields
```python
# Плохо - много бесполезных полей
return {
    "uuid": "a7f3b8c2-9d4e-5f6a...",
    "created_at": "2025-01-14T10:30:00.000Z",
    "updated_at": "2025-01-14T10:30:00.000Z",
    "mime_type": "image/jpeg",
    "256px_url": "https://...",
    "512px_url": "https://...",
    "1024px_url": "https://...",
    "metadata": {...}
}

# Хорошо - только нужное
return {
    "id": "img_sunset_beach",
    "name": "Sunset at Beach",
    "url": "https://..."  # Один URL, не три размера
}
```

### Pagination with Sensible Defaults
```python
@mcp.tool()
def list_documents(
    folder: str = None,
    page: int = 1,
    per_page: int = 20,        # Разумный default
    sort_by: str = "modified",
    sort_order: str = "desc"   # Новые сверху
) -> str:
    """
    List documents with smart defaults.

    Defaults optimized for typical agent workflows:
    - 20 items per page (enough context, not overwhelming)
    - Sorted by modification date (most relevant first)
    - Descending order (newest first)
    """
```

---

## 9. Evaluation-Driven Development

### Создавай реалистичные test cases
```python
# Слабый тест
"Schedule a meeting with jane@acme.corp"

# Сильный тест (реальный workflow)
"""
Schedule a meeting with Jane from sales next week
about Q1 planning. Attach the budget spreadsheet
from the shared drive and reserve conference room B.
"""
```

### Метрики для отслеживания
- **Accuracy** - правильность результата
- **Runtime** - время выполнения
- **Token consumption** - использование токенов
- **Call frequency** - сколько раз вызывается
- **Error rate** - процент ошибок

### Claude как reviewer
Используй Claude Code для анализа transcripts и автоматического рефакторинга tools.

---

## 10. Complete Example: Agent-Optimized MCP Server

```python
from fastmcp import FastMCP
from enum import Enum
from pydantic import BaseModel, Field

mcp = FastMCP("CRM Agent Tools")

class ResponseFormat(str, Enum):
    CONCISE = "concise"
    DETAILED = "detailed"

class ContactSearchInput(BaseModel):
    query: str = Field(..., description="Name, email, or company")
    response_format: ResponseFormat = ResponseFormat.CONCISE
    limit: int = Field(default=10, ge=1, le=50)

@mcp.tool()
def crm_search_contacts(input: ContactSearchInput) -> str:
    """
    Search CRM contacts by name, email, or company.

    Best practices:
    - Use concise format for browsing
    - Use detailed format when you need IDs for follow-up
    - Start with broad search, then refine

    Args:
        query: Search term (name, email fragment, or company)
        response_format: "concise" (default) or "detailed"
        limit: Max results (1-50, default 10)

    Returns:
        Concise: List of "Name <email>" entries
        Detailed: JSON with full contact info and IDs
    """
    contacts = crm.search(input.query, limit=input.limit)

    if not contacts:
        return "No contacts found. Try:\n- Broader search terms\n- Partial email match"

    if input.response_format == ResponseFormat.CONCISE:
        return "\n".join(
            f"{i}. {c.name} <{c.email}> - {c.company}"
            for i, c in enumerate(contacts)
        )
    else:
        return json.dumps([{
            "index": i,
            "contact_id": f"contact_{c.name.lower().replace(' ', '_')}",
            "name": c.name,
            "email": c.email,
            "phone": c.phone,
            "company": c.company,
            "last_contact": c.last_interaction.isoformat()
        } for i, c in enumerate(contacts)])

@mcp.tool()
def crm_create_deal(
    contact_index_or_id: str,
    deal_title: str,
    value: float,
    stage: str = "lead",
    notes: str = None
) -> str:
    """
    Create a new deal in CRM linked to a contact.

    This tool handles the full workflow:
    1. Resolves contact (by index from search or ID)
    2. Creates deal record
    3. Links to contact
    4. Sets initial stage

    Args:
        contact_index_or_id: Either index from search (0, 1, 2...)
                            or contact ID (contact_john_doe)
        deal_title: Name for this deal
        value: Expected deal value in USD
        stage: Pipeline stage (lead, qualified, proposal, closed)
        notes: Optional notes about the deal

    Returns:
        Created deal with ID and link
    """
    # Resolve contact
    contact = resolve_contact(contact_index_or_id)

    # Create deal
    deal = crm.create_deal(
        contact_id=contact.id,
        title=deal_title,
        value=value,
        stage=stage,
        notes=notes
    )

    return f"""Deal created successfully:
- ID: deal_{deal.id}
- Title: {deal.title}
- Value: ${deal.value:,.2f}
- Contact: {contact.name}
- Stage: {deal.stage}
- Link: {deal.url}

Next steps: Use crm_update_deal to change stage or add activities."""

if __name__ == "__main__":
    mcp.run()
```

---

## Summary Checklist

- [ ] **Consolidated workflows** - один tool = полный use case
- [ ] **Response format control** - concise vs detailed
- [ ] **Semantic IDs** - понятные, не UUID
- [ ] **Actionable errors** - guidance, не коды
- [ ] **Clear namespacing** - prefix группировка
- [ ] **Explicit parameters** - `user_id` не `user`
- [ ] **Token efficiency** - только нужные поля
- [ ] **Rich descriptions** - как для нового коллеги
- [ ] **Evaluation tests** - реалистичные сценарии

---

## Source

[Anthropic Engineering: Writing Tools for Agents](https://www.anthropic.com/engineering/writing-tools-for-agents)

---

## 11. Tool-loop ergonomics (production patterns)

Раздел 1–10 — про **дизайн** инструментов (schemas, descriptions, error messages). Этот раздел — про **сам loop**, в котором инструменты запускаются. Накоплено эмпирически на агентах с tool-call'ингом через OpenAI-совместимые API.

### 11.1 Implicit args injection (не давай LLM подбирать `user_id`)

`user_id`, `chat_id`, `session_id`, `tenant_id` — **runtime context** агента, не данные которые юзер может задать в чате. Если положить их в JSON schema, LLM начнёт «угадывать» или впишет в значения из чата (`user_id: "12345 (от пользователя)"`).

Правило: **schema видит только то, что LLM реально должен выбрать**. Privileged args инжектятся в `execute()`:

```python
SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "publish_draft",
            "description": "Deliver a draft to the user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "draft_ts": {"type": "string"},
                    "mode": {"type": "string", "enum": ["preview", "auto"]},
                },
                "required": ["draft_ts"],
            },
        },
    },
    # user_id и chat_id НЕ в schema
]

def execute(user_id: str, chat_id: int, name: str, args: dict) -> str:
    fn = HANDLERS[name]
    # Privileged tools получают user_id+chat_id явно
    if name in ("publish_draft", "send_photo_to_user", "generate_cover_image"):
        result = fn(user_id, chat_id, **args)
    else:
        result = fn(user_id, **args)
    return json.dumps(result, ensure_ascii=False)
```

Side-effect: token saving на каждом tool-call'е (нет лишних полей в request).

### 11.2 Error contract — никогда не raise, всегда return

Handler не должен **бросать исключение** из `execute()`. Иначе loop падает мимо LLM и юзер видит «❌ агент упал» вместо адаптивной реакции.

```python
def h_add_source(user_id: str, *, ref: str, slug: str | None = None) -> dict:
    s = _current_slug(user_id, slug)
    if not s:
        return {"error": "no current topic"}
    if not _validate_ref(ref):
        return {"error": f"invalid ref: {ref}",
                "hint": "use @channel, r/sub, x:@handle, or https://..."}
    return {"ok": True, "added": ref, "sources": cfg["sources"]}

def execute(user_id, chat_id, name, args):
    fn = HANDLERS.get(name)
    if fn is None:
        return json.dumps({"error": f"unknown tool: {name}"})
    try:
        result = fn(user_id, **args)
    except TypeError as e:
        result = {"error": f"bad args: {e}"}
    except Exception as e:
        result = {"error": f"{type(e).__name__}: {str(e)[:200]}"}
    return json.dumps(result, ensure_ascii=False)
```

Внутри handler — нормальные exceptions ловятся и преобразуются в `{"error": ...}`. На уровне execute — финальный safety net. LLM видит JSON и в следующем shot'е может сказать «не удалось, попробуем иначе».

### 11.3 Idempotency для stage tools

Если у tool есть концепция этапа (draft / storyboard / scene_references), он должен **сначала проверить сохранённый артефакт** и переиспользовать его, если задача та же. Юзер должен мочь спросить «покажи раскадровку» второй раз без перерасхода credits.

```python
def h_generate_storyboard(user_id, *, draft_ts, scenes=4,
                          voiceover_text=None, style_notes=None) -> dict:
    saved = _load_stage(user_id, draft_ts, "storyboard")

    # Если уже есть и параметры совпадают — отдаём кеш
    if saved and not style_notes and saved.get("scenes_count") == scenes:
        return {"ok": True, "stage": "storyboard",
                "prompts": saved["prompts"], "from_cache": True}

    prompts = _llm_director(voiceover_text, scenes, style_notes)
    _save_stage(user_id, draft_ts, "storyboard",
                {"prompts": prompts, "scenes_count": scenes})
    return {"ok": True, "stage": "storyboard", "prompts": prompts}
```

`style_notes` — sentinel для **forced refresh**. Юзер говорит «третью сцену помягче» → агент дёргает с `style_notes=...` → кеш игнорируется.

### 11.4 Staged vs auto mode — explicit opt-in в system prompt

Когда pipeline дорогой (Veo credits, ElevenLabs minutes) или результат критичен, дай агенту **явный opt-in** на пошаговый режим. Решение «сразу всё или по шагам» снимается с агента и кладётся в system prompt:

```text
Video pipeline — two modes:

FULL AUTO (default): user says "make a video", "сделай ролик" without
specifying stages → call enqueue_video(provider="veo-full").

STAGED: user says "поэтапно", "по шагам", "дай утвердить", "покажи
раскадровку", "сценарий сначала" → do ONLY the first stage and stop.
Wait for user approval before next stage:
1. write_voiceover_script → show text, ask approval
2. generate_storyboard → show prompts, ask approval
3. generate_scene_references → send photo album, ask approval
4. render_final_video → uses saved artefacts, delivers mp4
```

### 11.5 Stage artefact persistence

Stages нужно куда-то сохранять. Структура:

```text
data/users/<user_id>/topics/<slug>/drafts/<ts>-stages/
  voiceover.json     # {"text": "...", "target_sec": 30}
  storyboard.json    # {"prompts": ["..."], "lang": "ru", "scenes_count": 4}
  references.json    # {"paths": ["/abs/...", ...]}
```

Final stage (`render_final_video`) проверяет **все** артефакты на месте и **сам** возвращает `{"error": "missing stages: storyboard"}` без расхода credits, если что-то не сделано. Pre-flight check **до** API вызова, не во время.

### 11.6 `from_cache` flag в response

Если результат tool'а большой (список из 50 каналов, 30 кандидатов), и юзер может попросить «покажи ещё раз», добавь в response `from_cache: true` чтобы LLM не делал лишних tool-call'ов:

```python
return {
    "ok": True,
    "candidates": rows,
    "count": len(rows),
    "from_cache": cached_hit,
}
```

В system prompt — правило: `«If a tool returns from_cache: true, don't re-run it within the next 3 turns unless user explicitly asks for fresh data.»`

### 11.7 Tool loop budget — `MAX_TOOL_ITERATIONS = 6`

Защита от infinite loop'а когда LLM зацикливается:

```python
MAX_TOOL_ITERATIONS = 6

def run_tool_loop(messages):
    work = list(messages)
    for _ in range(MAX_TOOL_ITERATIONS):
        msg = _call_with_tools(work)
        tool_calls = msg.get("tool_calls") or []
        if not tool_calls:
            return (msg.get("content") or "").strip(), work
        work.append({"role": "assistant",
                     "content": msg.get("content") or "",
                     "tool_calls": tool_calls})
        for tc in tool_calls:
            result = execute(uid, chat_id, tc["function"]["name"],
                             json.loads(tc["function"]["arguments"] or "{}"))
            work.append({"role": "tool", "tool_call_id": tc["id"],
                         "name": tc["function"]["name"], "content": result})
    return "⚠️ too many steps — try rephrasing.", work
```

6 итераций — empirical sweet spot. Меньше — агент не успевает сделать stage 1 → stage 2 → publish за один ход. Больше — реальные loops съедают tokens без прогресса.

Можно добавить detection: если последние 2 tool calls идентичны (same name + same args), bail early.
