import json
from functools import wraps

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

    Args:
        ctx: Plugin context with register_tool(), get_env(), logger.
    """
    from . import schemas, tools

    for tool_name, handler in TOOL_BINDINGS.items():
        schema_key = f"SCHEMA_{tool_name.upper()}"
        schema = getattr(schemas, schema_key, None)
        if schema is None:
            ctx.logger.warning(
                f"No schema found for {tool_name} (expected schemas.{schema_key})"
            )
            continue
        ctx.register_tool(
            tool_name,
            "custom",
            schema,
            handler=_wrap(handler),
        )
    ctx.logger.info(f"Plugin registered {len(TOOL_BINDINGS)} tools")


def _post_import():
    """Wire tool handlers after module is fully loaded."""
    from . import tools

    TOOL_BINDINGS["tool_one"] = tools.tool_one
    TOOL_BINDINGS["tool_two"] = tools.tool_two


_post_import()
