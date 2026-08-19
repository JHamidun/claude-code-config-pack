---
name: claude-cli-runner
description: "Запуск Claude из Python БЕЗ API-ключа — claude CLI по подписке; модуль claude_cli.py. Триггеры: «клод из скрипта», «без API ключа»."
---

# Claude CLI Runner

Use this skill when the user needs to run Claude models from Python code WITHOUT API keys — via the `claude` CLI binary that uses Claude Code's built-in authentication.

## When to Use

- User asks to "run Claude from Python" or "call Claude without API key"
- User needs to process text with Claude in a backend/script
- User wants to integrate Claude into a project that doesn't have API keys configured
- User mentions "claude CLI" or "claude binary"

## Module Location

`~/.claude/tools/claude_cli.py`

## Quick Usage

```python
import sys
sys.path.insert(0, "~/.claude/tools")
from claude_cli import claude, claude_async, claude_json, claude_stream, validate_response

# Simple call
result = claude("Fix spelling: Привет мр")

# With system prompt and model
result = claude(
    "Review this code for bugs",
    system="You are a senior developer",
    model="claude-opus-4-8",
)

# Async
result = await claude_async("Translate to English: ...")

# JSON output
data = claude_json("List 3 colors as JSON array")

# Streaming
for chunk in claude_stream("Write a story"):
    print(chunk, end="")

# Validate LLM response
ok, cleaned = validate_response(original_text, llm_response)
```

## Available Models

- `claude-opus-4-8` — most capable (алиас `opus`)
- `claude-fable-5` — канон text-субагентов/воркеров (алиас `fable`, ≤5 одновременно)
- `claude-sonnet-4-5` — balanced (default)
- `claude-haiku-4-5` — fastest, cheapest

Канон актуальных ID/алиасов → `config/models.md`.

## Requirements

Claude CLI must be installed: `npm install -g @anthropic-ai/claude-code`

Or set `CLAUDE_CLI_PATH` env var to the binary path.

## On Server (your-server)

```bash
ssh your-server "which claude"  # verify installation
ssh your-server "claude -p --model claude-sonnet-4-5 'Hello'"  # test
```
