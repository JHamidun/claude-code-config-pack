# Quick reference — code examples

Load this when you need a starting skeleton to copy rather than guidance. For the
authoritative language-specific patterns and quality checklists, prefer
[🐍 Python Guide](./python_mcp_server.md) and [⚡ TypeScript Guide](./node_mcp_server.md) —
those are the reference of record; this file is a fast copy-paste layer on top.

## FastMCP server (Python)

```python
# server.py
from fastmcp import FastMCP

mcp = FastMCP("My Server")

@mcp.tool()
def add_numbers(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b

@mcp.tool()
def get_user(user_id: str) -> dict:
    """Fetch user information by ID."""
    return {"id": user_id, "name": "John Doe", "email": "john@example.com"}

@mcp.resource("file://{path}")
def read_file(path: str) -> str:
    """Read contents of a file."""
    with open(path, 'r') as f:
        return f.read()

if __name__ == "__main__":
    mcp.run()
```

## Basic TypeScript server

```typescript
// src/index.ts
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

const server = new Server(
  { name: "my-mcp-server", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "get_weather",
        description: "Get current weather for a city",
        inputSchema: {
          type: "object",
          properties: {
            city: { type: "string", description: "City name" }
          },
          required: ["city"]
        }
      },
      {
        name: "search",
        description: "Search for information",
        inputSchema: {
          type: "object",
          properties: {
            query: { type: "string" },
            limit: { type: "number", default: 10 }
          },
          required: ["query"]
        }
      }
    ]
  };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  switch (name) {
    case "get_weather": {
      const city = args?.city as string;
      return { content: [{ type: "text", text: `Weather in ${city}: Sunny, 22°C` }] };
    }
    case "search": {
      const query = args?.query as string;
      return { content: [{ type: "text", text: `Results for "${query}": [...]` }] };
    }
    default:
      throw new Error(`Unknown tool: ${name}`);
  }
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch(console.error);
```

## Tool definition with a full docstring

The docstring is the tool's entire interface as far as the agent is concerned — Args,
Returns, and when to use it all come from here.

```python
@mcp.tool()
def create_github_issue(
    title: str,
    body: str,
    repo: str,
    labels: list[str] = None,
    assignees: list[str] = None
) -> dict:
    """
    Create a new issue in a GitHub repository.

    Args:
        title: Issue title (required)
        body: Issue description in markdown (required)
        repo: Repository in format 'owner/repo' (required)
        labels: List of label names to apply
        assignees: List of GitHub usernames to assign

    Returns:
        Created issue with id, url, and number
    """
    return {
        "id": 12345,
        "number": 42,
        "url": f"https://github.com/{repo}/issues/42"
    }
```

## Input validation with Pydantic

```python
from pydantic import BaseModel, Field, validator

class SearchInput(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    limit: int = Field(default=10, ge=1, le=100)
    filters: dict = Field(default_factory=dict)

    @validator('query')
    def sanitize_query(cls, v):
        return v.strip()

@mcp.tool()
def search(input: SearchInput) -> list:
    """Search with validated input."""
    return perform_search(input.query, input.limit, input.filters)
```

## Resources

```python
# Static resource
@mcp.resource("config://settings")
def get_settings() -> str:
    """Get application settings."""
    return json.dumps({"theme": "dark", "language": "en"})

# Dynamic resource with URI template
@mcp.resource("user://{user_id}/profile")
def get_user_profile(user_id: str) -> str:
    """Get user profile by ID."""
    return json.dumps(fetch_user(user_id))
```

## Prompts

```python
@mcp.prompt()
def code_review_prompt(code: str, language: str) -> str:
    """Generate a code review prompt."""
    return f"""Please review this {language} code:

```{language}
{code}
```

Check for:
1. Bugs and errors
2. Security issues
3. Performance problems
4. Code style
"""

@mcp.prompt()
def summarize_prompt(text: str, max_words: int = 100) -> str:
    """Generate a summarization prompt."""
    return f"Summarize the following text in {max_words} words or less:\n\n{text}"
```

## Client configuration

### mcp.json (VS Code)

Secrets go through `inputs` with `"password": true`, never inline in `env` — an
inline key ends up committed with the config file.

```json
{
  "servers": {
    "my-server": {
      "type": "stdio",
      "command": "python",
      "args": ["path/to/server.py"],
      "env": { "API_KEY": "${input:api_key}" }
    },
    "npm-server": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@my-org/mcp-server"]
    }
  },
  "inputs": [
    {
      "id": "api_key",
      "type": "promptString",
      "description": "API Key",
      "password": true
    }
  ]
}
```

### claude_desktop_config.json

```json
{
  "mcpServers": {
    "my-server": {
      "command": "python",
      "args": ["/path/to/server.py"],
      "env": { "API_KEY": "your-key" }
    }
  }
}
```

## Error handling

```python
from mcp.types import McpError, ErrorCode

@mcp.tool()
def risky_operation(input: str) -> str:
    """Operation that might fail."""
    try:
        return do_something(input)
    except ValueError as e:
        raise McpError(ErrorCode.InvalidParams, f"Invalid input: {e}")
    except ConnectionError as e:
        raise McpError(ErrorCode.InternalError, f"Service unavailable: {e}")
    except Exception as e:
        raise McpError(ErrorCode.InternalError, f"Unexpected error: {e}")
```

## Testing

```python
# test_server.py
import pytest
from server import mcp

@pytest.mark.asyncio
async def test_get_weather():
    result = await mcp.call_tool("get_weather", {"city": "London"})
    assert "London" in result

@pytest.mark.asyncio
async def test_search():
    result = await mcp.call_tool("search", {"query": "test", "limit": 5})
    assert len(result) <= 5
```

## Publishing

```bash
# PyPI
pip install build twine
python -m build
twine upload dist/*

# npm
npm login
npm publish
```
