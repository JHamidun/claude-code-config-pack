---
name: agent-tool-design
description: Best practices for designing tools for AI agents (from Anthropic Engineering)
---

# Agent Tool Design Skill

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
