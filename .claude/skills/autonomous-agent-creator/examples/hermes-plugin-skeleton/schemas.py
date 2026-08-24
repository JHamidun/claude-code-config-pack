SCHEMA_TOOL_ONE = {
    "type": "function",
    "function": {
        "name": "tool_one",
        "description": (
            "Description of tool_one. When called, do X then Y. "
            "Present the results as a formatted list."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "param1": {
                    "type": "string",
                    "description": "What param1 is"
                },
                "param2": {
                    "type": "integer",
                    "description": "What param2 is"
                }
            },
            "required": ["param1"]
        }
    }
}

SCHEMA_TOOL_TWO = {
    "type": "function",
    "function": {
        "name": "tool_two",
        "description": (
            "Description of tool_two. Use when the user asks to search. "
            "After receiving results, present the top 3 with brief summaries."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                }
            },
            "required": ["query"]
        }
    }
}
