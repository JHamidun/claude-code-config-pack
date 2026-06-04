---
name: deepseek
description: "DeepSeek API Skill"
---

# DeepSeek API Skill

## Overview

Expert skill for using DeepSeek API - advanced coding assistant with 128K context and strong reasoning capabilities.

## API Key

```bash
# API ключи: ~/.claude/.credentials.master.env
# Переменная: DEEPSEEK_API_KEY
DEEPSEEK_API_KEY=os.getenv('DEEPSEEK_API_KEY')
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat
```

## When to Use DeepSeek

**Best for:**
- Complex code generation and refactoring
- Large codebase analysis (128K context!)
- Code review and debugging
- Algorithm design
- Technical documentation
- Math and reasoning problems

**Advantages:**
- 128K context window (huge!)
- Strong coding capabilities
- Excellent reasoning
- Cost-effective (cheaper than GPT-4)
- Fast inference

## Dependencies

```bash
pip install openai  # DeepSeek uses OpenAI-compatible API
```

## Basic Usage

### Chat Completion

```python
from openai import OpenAI
import os

# DeepSeek uses OpenAI-compatible API
client = OpenAI(
    api_key=os.getenv('DEEPSEEK_API_KEY'),
    base_url=os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1')
)

def deepseek_chat(prompt: str, system_prompt: str = None,
                  model: str = "deepseek-chat"):
    """
    Chat with DeepSeek.

    Models:
        - deepseek-chat: General purpose (fast, smart)
        - deepseek-coder: Optimized for coding
        - deepseek-reasoner: Best for complex reasoning
    """
    messages = []

    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.7,
        max_tokens=4096
    )

    return response.choices[0].message.content
```

### Code Generation

```python
def generate_code(task: str, language: str = "python"):
    """Generate code with DeepSeek Coder."""

    system_prompt = f"""You are an expert {language} developer.
    Write clean, well-documented, production-ready code.
    Include type hints, docstrings, and error handling.
    Follow best practices and design patterns."""

    return deepseek_chat(
        prompt=task,
        system_prompt=system_prompt,
        model="deepseek-coder"
    )
```

### Code Review

```python
def review_code(code: str, focus: list = None):
    """Review code for issues and improvements."""

    focus_areas = focus or ["security", "performance", "readability", "best practices"]

    system_prompt = """You are a senior code reviewer.
    Analyze the code thoroughly and provide:
    1. Security issues (CRITICAL)
    2. Performance problems
    3. Code quality issues
    4. Suggestions for improvement
    5. Good practices found

    Be specific with line numbers and provide fixes."""

    prompt = f"""Review this code focusing on: {', '.join(focus_areas)}

```
{code}
```

Provide structured feedback."""

    return deepseek_chat(prompt, system_prompt, model="deepseek-coder")
```

### Large Codebase Analysis (128K context!)

```python
def analyze_codebase(files: dict):
    """
    Analyze multiple files at once using 128K context.

    Args:
        files: {"path/to/file.py": "file content", ...}
    """

    # Build context with all files
    context = "# Codebase Analysis\n\n"
    for path, content in files.items():
        context += f"## File: {path}\n```\n{content}\n```\n\n"

    system_prompt = """You are a senior software architect.
    Analyze this codebase and provide:
    1. Architecture overview
    2. Code quality assessment
    3. Potential issues and technical debt
    4. Suggestions for improvement
    5. Security concerns"""

    return deepseek_chat(context + "\nAnalyze this codebase.", system_prompt)
```

### Reasoning Tasks

```python
def solve_problem(problem: str):
    """Solve complex reasoning problem with DeepSeek Reasoner."""

    system_prompt = """You are an expert problem solver.
    Think step by step.
    Show your reasoning clearly.
    Verify your solution."""

    return deepseek_chat(
        prompt=problem,
        system_prompt=system_prompt,
        model="deepseek-reasoner"
    )
```

## Advanced Patterns

### Streaming Response

```python
def stream_response(prompt: str):
    """Stream response for long outputs."""

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        stream=True
    )

    for chunk in response:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
```

### Function Calling

```python
def with_functions(prompt: str, functions: list):
    """Use function calling with DeepSeek."""

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        tools=[{"type": "function", "function": f} for f in functions],
        tool_choice="auto"
    )

    return response.choices[0]
```

### JSON Mode

```python
def structured_output(prompt: str):
    """Get structured JSON output."""

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "Respond in valid JSON format only."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )

    import json
    return json.loads(response.choices[0].message.content)
```

## Use Case Templates

### Refactor Code

```python
def refactor_code(code: str, goals: list):
    """Refactor code with specific goals."""

    prompt = f"""Refactor this code with these goals:
{chr(10).join(f'- {g}' for g in goals)}

Original code:
```
{code}
```

Provide the refactored code with explanations."""

    return deepseek_chat(prompt, model="deepseek-coder")
```

### Debug Code

```python
def debug_code(code: str, error: str):
    """Debug code with error message."""

    prompt = f"""Debug this code that produces the following error:

Error: {error}

Code:
```
{code}
```

1. Explain what's causing the error
2. Provide the fixed code
3. Explain what was changed"""

    return deepseek_chat(prompt, model="deepseek-coder")
```

### Generate Tests

```python
def generate_tests(code: str, framework: str = "pytest"):
    """Generate tests for code."""

    prompt = f"""Generate comprehensive tests for this code using {framework}:

```
{code}
```

Include:
- Unit tests for each function
- Edge cases
- Error handling tests
- Integration tests if applicable"""

    return deepseek_chat(prompt, model="deepseek-coder")
```

## API Pricing

| Model | Input | Output |
|-------|-------|--------|
| deepseek-chat | $0.14/1M tokens | $0.28/1M tokens |
| deepseek-coder | $0.14/1M tokens | $0.28/1M tokens |
| deepseek-reasoner | $0.55/1M tokens | $2.19/1M tokens |

**Note:** DeepSeek is ~10-20x cheaper than GPT-4!

## Quick Reference

| Task | Model | Code |
|------|-------|------|
| General chat | deepseek-chat | `deepseek_chat(prompt)` |
| Code generation | deepseek-coder | `generate_code(task)` |
| Code review | deepseek-coder | `review_code(code)` |
| Codebase analysis | deepseek-chat | `analyze_codebase(files)` |
| Complex reasoning | deepseek-reasoner | `solve_problem(problem)` |

## Tips

1. **Use 128K context** - можно загружать целые репозитории
2. **deepseek-coder** лучше для кода, чем deepseek-chat
3. **Дешевле GPT-4** - используй для heavy tasks
4. **OpenAI-compatible** - тот же синтаксис что и OpenAI
5. **Streaming** - используй для длинных ответов
6. **JSON mode** - для структурированных данных
