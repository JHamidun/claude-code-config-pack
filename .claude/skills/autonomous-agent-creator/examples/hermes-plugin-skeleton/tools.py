import logging

logger = logging.getLogger(__name__)


def tool_one(param1: str, param2: int = 0, **kwargs):
    """Handle tool_one calls.

    Args:
        param1: Primary input string.
        param2: Optional numeric parameter.
        **kwargs: Extra context injected by Hermes (_user_id, _chat_id, etc).

    Returns:
        dict with ok=True/False and data/error.
    """
    try:
        # Your logic here
        result = f"Processed {param1} with {param2}"
        return {"ok": True, "data": {"result": result}}
    except Exception as e:
        logger.error(f"tool_one failed: {e}", exc_info=True)
        return {"ok": False, "error": str(e)}


def tool_two(query: str, **kwargs):
    """Handle tool_two calls.

    Args:
        query: Search query string.
        **kwargs: Extra context injected by Hermes.

    Returns:
        dict with ok=True/False and data/error.
    """
    try:
        # Your logic here
        results = []
        return {"ok": True, "data": {"results": results, "total": len(results)}}
    except Exception as e:
        logger.error(f"tool_two failed: {e}", exc_info=True)
        return {"ok": False, "error": str(e)}
