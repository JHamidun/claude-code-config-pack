---
name: mcp-builder
description: "Guide for building high-quality MCP (Model Context Protocol) servers in Python (FastMCP) or Node/TypeScript (MCP SDK). Also covers agent tool design (reference/agent-tool-design-examples.md). Триггеры: создание MCP серверов, проектирование API для агентов, оптимизация существующих tools, review tool definitions, tool-loop ergonomics (error contract, idempotency, MAX_TOOL_ITERATIONS)."
license: Complete terms in LICENSE.txt
type: actionable
---

# MCP Server Development Guide

## Overview

To create high-quality MCP (Model Context Protocol) servers that enable LLMs to effectively interact with external services, use this skill. An MCP server provides tools that allow LLMs to access external services and APIs. The quality of an MCP server is measured by how well it enables LLMs to accomplish real-world tasks using the tools provided.

---

# Process

## 🚀 High-Level Workflow

Creating a high-quality MCP server involves four main phases:

### Phase 1: Deep Research and Planning

#### 1.1 Understand Agent-Centric Design Principles

Before diving into implementation, understand how to design tools for AI agents by reviewing these principles:

**Build for Workflows, Not Just API Endpoints:**
- Don't simply wrap existing API endpoints - build thoughtful, high-impact workflow tools
- Consolidate related operations (e.g., `schedule_event` that both checks availability and creates event)
- Focus on tools that enable complete tasks, not just individual API calls
- Consider what workflows agents actually need to accomplish

**Optimize for Limited Context:**
- Agents have constrained context windows - make every token count
- Return high-signal information, not exhaustive data dumps
- Provide "concise" vs "detailed" response format options
- Default to human-readable identifiers over technical codes (names over IDs)
- Consider the agent's context budget as a scarce resource

**Design Actionable Error Messages:**
- Error messages should guide agents toward correct usage patterns
- Suggest specific next steps: "Try using filter='active_only' to reduce results"
- Make errors educational, not just diagnostic
- Help agents learn proper tool usage through clear feedback

**Follow Natural Task Subdivisions:**
- Tool names should reflect how humans think about tasks
- Group related tools with consistent prefixes for discoverability
- Design tools around natural workflows, not just API structure

**Use Evaluation-Driven Development:**
- Create realistic evaluation scenarios early
- Let agent feedback drive tool improvements
- Prototype quickly and iterate based on actual agent performance

**Развёрнутые Python-примеры к каждому из этих принципов + production-паттерны tool-loop'а** (implicit args injection, error contract «никогда не raise», idempotency, staged vs auto mode, from_cache, MAX_TOOL_ITERATIONS): [🧰 Agent Tool Design Examples](./reference/agent-tool-design-examples.md) — ex-скилл agent-tool-design.

#### 1.3 Study MCP Protocol Documentation

**Fetch the latest MCP protocol documentation:**

Use WebFetch to load: `https://modelcontextprotocol.io/llms-full.txt`

This comprehensive document contains the complete MCP specification and guidelines.

#### 1.4 Study Framework Documentation

**Load and read the following reference files:**

- **MCP Best Practices**: [📋 View Best Practices](./reference/mcp_best_practices.md) - Core guidelines for all MCP servers

**For Python implementations, also load:**
- **Python SDK Documentation**: Use WebFetch to load `https://raw.githubusercontent.com/modelcontextprotocol/python-sdk/main/README.md`
- [🐍 Python Implementation Guide](./reference/python_mcp_server.md) - Python-specific best practices and examples

**For Node/TypeScript implementations, also load:**
- **TypeScript SDK Documentation**: Use WebFetch to load `https://raw.githubusercontent.com/modelcontextprotocol/typescript-sdk/main/README.md`
- [⚡ TypeScript Implementation Guide](./reference/node_mcp_server.md) - Node/TypeScript-specific best practices and examples

#### 1.5 Exhaustively Study API Documentation

To integrate a service, read through **ALL** available API documentation:
- Official API reference documentation
- Authentication and authorization requirements
- Rate limiting and pagination patterns
- Error responses and status codes
- Available endpoints and their parameters
- Data models and schemas

**To gather comprehensive information, use web search and the WebFetch tool as needed.**

#### 1.6 Create a Comprehensive Implementation Plan

Based on your research, create a detailed plan that includes:

**Tool Selection:**
- List the most valuable endpoints/operations to implement
- Prioritize tools that enable the most common and important use cases
- Consider which tools work together to enable complex workflows

**Shared Utilities and Helpers:**
- Identify common API request patterns
- Plan pagination helpers
- Design filtering and formatting utilities
- Plan error handling strategies

**Input/Output Design:**
- Define input validation models (Pydantic for Python, Zod for TypeScript)
- Design consistent response formats (e.g., JSON or Markdown), and configurable levels of detail (e.g., Detailed or Concise)
- Plan for large-scale usage (thousands of users/resources)
- Implement character limits and truncation strategies (e.g., 25,000 tokens)

**Error Handling Strategy:**
- Plan graceful failure modes
- Design clear, actionable, LLM-friendly, natural language error messages which prompt further action
- Consider rate limiting and timeout scenarios
- Handle authentication and authorization errors

---

### Phase 2: Implementation

Now that you have a comprehensive plan, begin implementation following language-specific best practices.

#### 2.1 Set Up Project Structure

**For Python:**
- Create a single `.py` file or organize into modules if complex (see [🐍 Python Guide](./reference/python_mcp_server.md))
- Use the MCP Python SDK for tool registration
- Define Pydantic models for input validation

**For Node/TypeScript:**
- Create proper project structure (see [⚡ TypeScript Guide](./reference/node_mcp_server.md))
- Set up `package.json` and `tsconfig.json`
- Use MCP TypeScript SDK
- Define Zod schemas for input validation

#### 2.2 Implement Core Infrastructure First

**To begin implementation, create shared utilities before implementing tools:**
- API request helper functions
- Error handling utilities
- Response formatting functions (JSON and Markdown)
- Pagination helpers
- Authentication/token management

#### 2.3 Implement Tools Systematically

For each tool in the plan:

**Define Input Schema:**
- Use Pydantic (Python) or Zod (TypeScript) for validation
- Include proper constraints (min/max length, regex patterns, min/max values, ranges)
- Provide clear, descriptive field descriptions
- Include diverse examples in field descriptions

**Write Comprehensive Docstrings/Descriptions:**
- One-line summary of what the tool does
- Detailed explanation of purpose and functionality
- Explicit parameter types with examples
- Complete return type schema
- Usage examples (when to use, when not to use)
- Error handling documentation, which outlines how to proceed given specific errors

**Implement Tool Logic:**
- Use shared utilities to avoid code duplication
- Follow async/await patterns for all I/O
- Implement proper error handling
- Support multiple response formats (JSON and Markdown)
- Respect pagination parameters
- Check character limits and truncate appropriately

**Add Tool Annotations:**
- `readOnlyHint`: true (for read-only operations)
- `destructiveHint`: false (for non-destructive operations)
- `idempotentHint`: true (if repeated calls have same effect)
- `openWorldHint`: true (if interacting with external systems)

#### 2.4 Follow Language-Specific Best Practices

**At this point, load the appropriate language guide:**

**For Python: Load [🐍 Python Implementation Guide](./reference/python_mcp_server.md) and ensure the following:**
- Using MCP Python SDK with proper tool registration
- Pydantic v2 models with `model_config`
- Type hints throughout
- Async/await for all I/O operations
- Proper imports organization
- Module-level constants (CHARACTER_LIMIT, API_BASE_URL)

**For Node/TypeScript: Load [⚡ TypeScript Implementation Guide](./reference/node_mcp_server.md) and ensure the following:**
- Using `server.registerTool` properly
- Zod schemas with `.strict()`
- TypeScript strict mode enabled
- No `any` types - use proper types
- Explicit Promise<T> return types
- Build process configured (`npm run build`)

---

### Phase 3: Review and Refine

After initial implementation:

#### 3.1 Code Quality Review

To ensure quality, review the code for:
- **DRY Principle**: No duplicated code between tools
- **Composability**: Shared logic extracted into functions
- **Consistency**: Similar operations return similar formats
- **Error Handling**: All external calls have error handling
- **Type Safety**: Full type coverage (Python type hints, TypeScript types)
- **Documentation**: Every tool has comprehensive docstrings/descriptions

#### 3.2 Test and Build

**Important:** MCP servers are long-running processes that wait for requests over stdio/stdin or sse/http. Running them directly in your main process (e.g., `python server.py` or `node dist/index.js`) will cause your process to hang indefinitely.

**Safe ways to test the server:**
- Use the evaluation harness (see Phase 4) - recommended approach
- Run the server in tmux to keep it outside your main process
- Use a timeout when testing: `timeout 5s python server.py`

**For Python:**
- Verify Python syntax: `python -m py_compile your_server.py`
- Check imports work correctly by reviewing the file
- To manually test: Run server in tmux, then test with evaluation harness in main process
- Or use the evaluation harness directly (it manages the server for stdio transport)

**For Node/TypeScript:**
- Run `npm run build` and ensure it completes without errors
- Verify dist/index.js is created
- To manually test: Run server in tmux, then test with evaluation harness in main process
- Or use the evaluation harness directly (it manages the server for stdio transport)

#### 3.3 Use Quality Checklist

To verify implementation quality, load the appropriate checklist from the language-specific guide:
- Python: see "Quality Checklist" in [🐍 Python Guide](./reference/python_mcp_server.md)
- Node/TypeScript: see "Quality Checklist" in [⚡ TypeScript Guide](./reference/node_mcp_server.md)

---

### Phase 4: Create Evaluations

After implementing your MCP server, create comprehensive evaluations to test its effectiveness.

**Load [✅ Evaluation Guide](./reference/evaluation.md) for complete evaluation guidelines.**

#### 4.1 Understand Evaluation Purpose

Evaluations test whether LLMs can effectively use your MCP server to answer realistic, complex questions.

#### 4.2 Create 10 Evaluation Questions

To create effective evaluations, follow the process outlined in the evaluation guide:

1. **Tool Inspection**: List available tools and understand their capabilities
2. **Content Exploration**: Use READ-ONLY operations to explore available data
3. **Question Generation**: Create 10 complex, realistic questions
4. **Answer Verification**: Solve each question yourself to verify answers

#### 4.3 Evaluation Requirements

Each question must be:
- **Independent**: Not dependent on other questions
- **Read-only**: Only non-destructive operations required
- **Complex**: Requiring multiple tool calls and deep exploration
- **Realistic**: Based on real use cases humans would care about
- **Verifiable**: Single, clear answer that can be verified by string comparison
- **Stable**: Answer won't change over time

#### 4.4 Output Format

Create an XML file with this structure:

```xml
<evaluation>
  <qa_pair>
    <question>Find discussions about AI model launches with animal codenames. One model needed a specific safety designation that uses the format ASL-X. What number X was being determined for the model named after a spotted wild cat?</question>
    <answer>3</answer>
  </qa_pair>
<!-- More qa_pairs... -->
</evaluation>
```

---

# Reference Files

## 📚 Documentation Library

Load these resources as needed during development:

### Core MCP Documentation (Load First)
- **MCP Protocol**: Fetch from `https://modelcontextprotocol.io/llms-full.txt` - Complete MCP specification
- [📋 MCP Best Practices](./reference/mcp_best_practices.md) - Universal MCP guidelines including:
  - Server and tool naming conventions
  - Response format guidelines (JSON vs Markdown)
  - Pagination best practices
  - Character limits and truncation strategies
  - Tool development guidelines
  - Security and error handling standards

### SDK Documentation (Load During Phase 1/2)
- **Python SDK**: Fetch from `https://raw.githubusercontent.com/modelcontextprotocol/python-sdk/main/README.md`
- **TypeScript SDK**: Fetch from `https://raw.githubusercontent.com/modelcontextprotocol/typescript-sdk/main/README.md`

### Language-Specific Implementation Guides (Load During Phase 2)
- [🐍 Python Implementation Guide](./reference/python_mcp_server.md) - Complete Python/FastMCP guide with:
  - Server initialization patterns
  - Pydantic model examples
  - Tool registration with `@mcp.tool`
  - Complete working examples
  - Quality checklist

- [⚡ TypeScript Implementation Guide](./reference/node_mcp_server.md) - Complete TypeScript guide with:
  - Project structure
  - Zod schema patterns
  - Tool registration with `server.registerTool`
  - Complete working examples
  - Quality checklist

### Agent Tool Design Examples (Load During Phase 1.1 / tool-loop implementation)
- [🧰 Agent Tool Design Examples](./reference/agent-tool-design-examples.md) - Python-примеры принципов agent-centric design (consolidated workflows, response format control, semantic IDs, actionable errors, namespacing, token efficiency) + tool-loop ergonomics (раздел 11)

### Evaluation Guide (Load During Phase 4)
- [✅ Evaluation Guide](./reference/evaluation.md) - Complete evaluation creation guide with:
  - Question creation guidelines
  - Answer verification strategies
  - XML format specifications
  - Example questions and answers
  - Running an evaluation with the provided scripts

---

# Quick Reference - Code Examples

## Python MCP Server Implementation

### Basic MCP Server (Python SDK)

```python
# server.py
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import asyncio

# Create server
server = Server("my-mcp-server")

# Define a tool
@server.tool()
async def get_weather(city: str) -> str:
    """Get current weather for a city."""
    # Your API call here
    return f"Weather in {city}: Sunny, 22°C"

@server.tool()
async def search_database(query: str, limit: int = 10) -> str:
    """Search the database for matching records."""
    # Database query here
    results = [{"id": 1, "name": "Result 1"}]
    return str(results)

# Run server
async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream)

if __name__ == "__main__":
    asyncio.run(main())
```

### FastMCP Implementation (Simplified Approach)

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

## TypeScript MCP Server Implementation

### Basic TypeScript Server

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

// List available tools
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

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  switch (name) {
    case "get_weather":
      const city = args?.city as string;
      return {
        content: [
          { type: "text", text: `Weather in ${city}: Sunny, 22°C` }
        ]
      };

    case "search":
      const query = args?.query as string;
      return {
        content: [
          { type: "text", text: `Results for "${query}": [...]` }
        ]
      };

    default:
      throw new Error(`Unknown tool: ${name}`);
  }
});

// Start server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch(console.error);
```

## Tool Design Examples

### Comprehensive Tool Definition

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
    # Implementation
    return {
        "id": 12345,
        "number": 42,
        "url": f"https://github.com/{repo}/issues/42"
    }
```

### Input Validation with Pydantic

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
    # input is already validated
    return perform_search(input.query, input.limit, input.filters)
```

## Resources Examples

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
    user = fetch_user(user_id)
    return json.dumps(user)

# File resource
@mcp.resource("file://{path}")
def read_file(path: str) -> str:
    """Read file contents."""
    with open(path, 'r') as f:
        return f.read()
```

## Prompts Examples

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

## Configuration Examples

### mcp.json (VS Code)

```json
{
  "servers": {
    "my-server": {
      "type": "stdio",
      "command": "python",
      "args": ["path/to/server.py"],
      "env": {
        "API_KEY": "${input:api_key}"
      }
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
      "env": {
        "API_KEY": "your-key"
      }
    }
  }
}
```

## Error Handling Example

```python
from mcp.types import McpError, ErrorCode

@mcp.tool()
def risky_operation(input: str) -> str:
    """Operation that might fail."""
    try:
        result = do_something(input)
        return result
    except ValueError as e:
        raise McpError(
            ErrorCode.InvalidParams,
            f"Invalid input: {e}"
        )
    except ConnectionError as e:
        raise McpError(
            ErrorCode.InternalError,
            f"Service unavailable: {e}"
        )
    except Exception as e:
        raise McpError(
            ErrorCode.InternalError,
            f"Unexpected error: {e}"
        )
```

## Testing Example

```python
# test_server.py
import pytest
from server import mcp

@pytest.mark.asyncio
async def test_get_weather():
    result = await mcp.call_tool("get_weather", {"city": "London"})
    assert "London" in result
    assert "°C" in result

@pytest.mark.asyncio
async def test_search():
    result = await mcp.call_tool("search", {"query": "test", "limit": 5})
    assert isinstance(result, list)
    assert len(result) <= 5
```

## Publishing Commands

```bash
# PyPI
pip install build twine
python -m build
twine upload dist/*

# npm
npm login
npm publish
```

## Quick Best Practices Checklist

1. **Clear descriptions** - Document every tool with comprehensive docstrings
2. **Typed parameters** - Use strong typing and input validation (Pydantic/Zod)
3. **Error handling** - Return actionable, LLM-friendly error messages
4. **Idempotent** - Repeated calls produce same result (where applicable)
5. **Rate limiting** - Protect against abuse
6. **Logging** - Log important operations for debugging
7. **Security** - Validate permissions and sanitize inputs
8. **One tool = one task** - Don't overload tools with multiple responsibilities
9. **Test locally** - Verify functionality before publishing
10. **Version with semver** - Follow semantic versioning principles
