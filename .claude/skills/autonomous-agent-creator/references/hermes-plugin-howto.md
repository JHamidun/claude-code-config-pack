# Hermes Plugin Development Guide

> Step-by-step guide for creating a Hermes plugin (based on a fitness-coach plugin).

---

## 1. Directory Structure

```
my-plugin/
  plugin.yaml          # Metadata and declarations
  __init__.py          # Registration entrypoint
  schemas.py           # OpenAI function-calling schemas
  tools.py             # Tool handler implementations
  db.py                # (Optional) Database access layer
  requirements.txt     # (Optional) Python dependencies
```

Plugins live inside the Hermes container at `/app/plugins/<plugin_name>/`.
On the host, they are typically stored in a bind-mounted directory or baked into the image.

---

## 2. plugin.yaml Format

```yaml
name: my-plugin
version: "1.0.0"
description: "Human-readable description of what the plugin does"

provides_tools:
  - tool_name_one
  - tool_name_two
  - tool_name_three

requires_env:
  - DATABASE_URL        # Plugin won't load if missing
  - SOME_API_KEY        # Listed here for documentation + validation

# Optional: declare dependencies on other plugins
depends_on: []
```

Key rules:
- `provides_tools` must exactly match the keys in `TOOL_BINDINGS` dict in `__init__.py`
- `requires_env` vars are checked at boot; missing = plugin skipped with warning
- `version` is informational (no semver enforcement yet)

---

## 3. __init__.py Pattern

```python
import json
from functools import wraps

# Will be populated after tools import
TOOL_BINDINGS = {}


def _wrap(fn):
    """Adapter: ensures handler returns JSON string (Hermes protocol)."""
    @wraps(fn)
    def wrapper(**kwargs):
        result = fn(**kwargs)
        if isinstance(result, str):
            return result
        return json.dumps(result, ensure_ascii=False, default=str)
    return wrapper


def register(ctx):
    """Called by Hermes core during plugin registration.

    ctx provides:
      - ctx.register_tool(name, toolset, schema, handler=callable)
      - ctx.get_env(key) -> str | None
      - ctx.logger -> logging.Logger
    """
    from . import schemas, tools

    for tool_name, handler in TOOL_BINDINGS.items():
        schema_key = f"SCHEMA_{tool_name.upper()}"
        schema = getattr(schemas, schema_key, None)
        if schema is None:
            ctx.logger.warning(f"No schema found for {tool_name} (expected schemas.{schema_key})")
            continue
        ctx.register_tool(
            tool_name,
            "custom",       # toolset name — groups tools in the UI
            schema,
            handler=_wrap(handler),
        )
    ctx.logger.info(f"Plugin registered {len(TOOL_BINDINGS)} tools")


def _post_import():
    """Wire tool handlers after module is fully loaded."""
    from . import tools
    TOOL_BINDINGS["tool_name_one"] = tools.tool_name_one
    TOOL_BINDINGS["tool_name_two"] = tools.tool_name_two


_post_import()
```

Critical points:
- `register(ctx)` is the ONLY entrypoint Hermes calls
- Handler must accept `**kwargs` and return a JSON-serializable dict or a JSON string
- The `_wrap` adapter ensures consistent JSON output
- Import tools INSIDE functions to avoid circular imports

---

## 4. schemas.py: OpenAI Function-Calling Format

```python
SCHEMA_TOOL_NAME_ONE = {
    "type": "function",
    "function": {
        "name": "tool_name_one",
        "description": (
            "Creates a meal plan for the user. "
            "Call this when the user asks for food recommendations. "
            "After receiving results, present them as a formatted list with emojis. "
            "If calories are specified, stay within 10% of target."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "integer",
                    "description": "Telegram user ID (from context)"
                },
                "calories_target": {
                    "type": "integer",
                    "description": "Daily calorie target in kcal"
                },
                "restrictions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Dietary restrictions (e.g. ['gluten-free', 'no-dairy'])"
                }
            },
            "required": ["user_id"]
        }
    }
}
```

### Description-as-Instructions Pattern

The `description` field is the PRIMARY way to instruct the agent on:
1. **WHEN** to call the tool (triggers)
2. **HOW** to use the results (formatting, follow-up actions)
3. **CONSTRAINTS** (validation rules the agent should enforce)

Example from the fitness-coach plugin:
```python
"description": (
    "Generates a personalized workout program. "
    "Call ONLY after collecting: goal, fitness level, available equipment, injuries. "
    "If any are missing, ask the user first — do NOT call with defaults. "
    "After receiving the program, format each exercise as:\n"
    "  💪 Exercise Name — Sets x Reps (Rest: Xs)\n"
    "End with a motivational message."
)
```

This is MORE effective than system prompt instructions because it's co-located with the tool.

---

## 5. tools.py: Handler Implementations

```python
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def tool_name_one(user_id: int, calories_target: int = 2000, restrictions: list = None, **kwargs):
    """Generate a meal plan.

    Args:
        user_id: Telegram user ID.
        calories_target: Daily kcal target.
        restrictions: List of dietary restrictions.

    Returns:
        dict with ok=True/False and data/error.
    """
    try:
        # Your business logic here
        plan = _generate_plan(user_id, calories_target, restrictions or [])
        return {"ok": True, "data": {"plan": plan, "generated_at": datetime.now().isoformat()}}
    except ValueError as e:
        logger.warning(f"Invalid input for user {user_id}: {e}")
        return {"ok": False, "error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error in tool_name_one: {e}", exc_info=True)
        return {"ok": False, "error": "Internal error. Please try again."}


def tool_name_two(query: str, limit: int = 10, **kwargs):
    """Search knowledge base."""
    # Always accept **kwargs — Hermes may pass extra context fields
    results = _search(query, limit)
    return {"ok": True, "data": {"results": results, "total": len(results)}}
```

Rules:
- Always accept `**kwargs` (Hermes injects context fields like `_chat_id`, `_user_id`)
- Always return `{"ok": True/False, ...}` structure
- Never raise exceptions to the caller — catch and return error dict
- Use logging, not print()

---

## 6. db.py: Database Access Pattern

```python
import os
import logging
from contextlib import contextmanager
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

_pool = None


def get_pool():
    global _pool
    if _pool is None:
        _pool = ThreadedConnectionPool(
            minconn=1,
            maxconn=5,
            dsn=os.environ["DATABASE_URL"],
        )
    return _pool


@contextmanager
def get_cursor():
    """Context manager: auto-commit on success, rollback on error."""
    pool = get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)


# Column alias shim — handle schema differences between environments
COLUMN_MAP = {
    "user_id": "telegram_user_id",  # prod has different column name
    "created": "created_at",
}


def col(name: str) -> str:
    """Return the actual column name for the current schema."""
    return COLUMN_MAP.get(name, name)
```

Usage in tools.py:
```python
from .db import get_cursor, col

def get_user_profile(user_id: int, **kwargs):
    with get_cursor() as cur:
        cur.execute(
            f"SELECT * FROM users WHERE {col('user_id')} = %s",
            (user_id,)
        )
        row = cur.fetchone()
    if not row:
        return {"ok": False, "error": "User not found"}
    return {"ok": True, "data": dict(row)}
```

---

## 7. Testing

### Direct function calls (unit test):

```python
# test_tools.py
from my_plugin.tools import tool_name_one

def test_tool_name_one_happy_path():
    result = tool_name_one(user_id=12345, calories_target=1800)
    assert result["ok"] is True
    assert "plan" in result["data"]

def test_tool_name_one_invalid_input():
    result = tool_name_one(user_id=-1)
    assert result["ok"] is False
```

### Mock ctx for registration test:

```python
class MockCtx:
    def __init__(self):
        self.registered = {}
        self.logger = logging.getLogger("test")

    def register_tool(self, name, toolset, schema, handler=None):
        self.registered[name] = {"toolset": toolset, "schema": schema, "handler": handler}

    def get_env(self, key):
        return os.environ.get(key)

def test_register():
    ctx = MockCtx()
    from my_plugin import register
    register(ctx)
    assert "tool_name_one" in ctx.registered
    assert "tool_name_two" in ctx.registered
```

---

## 8. Deployment

### Baking into image (recommended):

```dockerfile
COPY plugins/my-plugin /app/plugins/my-plugin
```

### Bind mount (dev mode):

```yaml
volumes:
  - ./plugins/my-plugin:/app/plugins/my-plugin:ro
```

### Installing Python deps (bootstrap.sh):

```bash
#!/bin/bash
# bootstrap.sh — runs once at container start
pip install --no-cache-dir -r /app/plugins/my-plugin/requirements.txt
```

Or in Dockerfile:
```dockerfile
RUN pip install --no-cache-dir psycopg2-binary redis
```

---

## 9. Common Patterns

### Accessing user context in handlers:

Hermes injects `_chat_id`, `_user_id`, `_platform` into kwargs:
```python
def my_tool(query: str, **kwargs):
    user_id = kwargs.get("_user_id")
    platform = kwargs.get("_platform", "telegram")
    # Use for personalization, logging, access control
```

### Returning structured data for agent formatting:

```python
def search_recipes(query: str, **kwargs):
    results = db_search(query)
    return {
        "ok": True,
        "data": {
            "results": results,
            "total": len(results),
            "_agent_hint": "Present as numbered list with calories per serving"
        }
    }
```

### Error categorization:

```python
def my_tool(**kwargs):
    try:
        # ...
        return {"ok": True, "data": {...}}
    except PermissionError:
        return {"ok": False, "error": "Access denied", "retry": False}
    except TimeoutError:
        return {"ok": False, "error": "Service timeout", "retry": True}
    except Exception as e:
        return {"ok": False, "error": f"Unexpected: {e}", "retry": False}
```

The `retry` field hints to the agent whether to try again.
