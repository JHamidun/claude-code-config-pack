---
name: deepseek
description: "DeepSeek API (deepseek-chat): кодогенерация, reasoning, 128K контекст. Триггеры: «дипсик», «спроси deepseek», «дешёвая кодогенерация»."
---

# DeepSeek API Skill

## Overview

Expert skill for using DeepSeek API - advanced coding assistant with 128K context and strong reasoning capabilities.

## API Key

Ключ берётся из `~/.claude/.credentials.master.env`. Впиши в него **сам ключ**, а не
код на Python:

```bash
# ~/.claude/.credentials.master.env
DEEPSEEK_API_KEY=sk-ВСТАВЬ_СЮДА_СВОЙ_КЛЮЧ   # получить: https://platform.deepseek.com/api_keys
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat
```

Строка вида `DEEPSEEK_API_KEY=os.getenv('DEEPSEEK_API_KEY')` — **не** настройка ключа.
Это непустая строка: любая проверка `if not key` посчитает ключ заданным, запрос уйдёт
с этим текстом вместо ключа и вернётся голый `401` без единого намёка на причину. Ровно
то же относится к оставленной заглушке `your_deepseek_api_key`.

Файл никем не подгружается автоматически — окружение надо наполнить явно:

```python
import os
from pathlib import Path
from dotenv import load_dotenv      # pip install python-dotenv

load_dotenv(Path.home() / '.claude' / '.credentials.master.env')


def deepseek_key() -> str:
    """Ключ DeepSeek или громкий отказ. Молча ходить с мусором вместо ключа нельзя."""
    key = (os.getenv('DEEPSEEK_API_KEY') or '').strip()
    if not key:
        raise RuntimeError(
            'DEEPSEEK_API_KEY не задан. Впиши ключ в ~/.claude/.credentials.master.env '
            '(строка DEEPSEEK_API_KEY=sk-...), ключ берётся на '
            'https://platform.deepseek.com/api_keys'
        )
    bogus = key.startswith(('os.getenv', 'your_', '<', '${')) or key in {'sk-', 'CHANGEME'}
    if bogus or not key.startswith('sk-'):
        raise RuntimeError(
            f'DEEPSEEK_API_KEY выглядит не как ключ, а как заглушка: {key[:24]!r}. '
            'Ключи DeepSeek начинаются с "sk-". Запрос с таким значением вернёт 401 '
            'без объяснения причины — исправь ~/.claude/.credentials.master.env.'
        )
    return key
```

Вызывай `deepseek_key()` вместо `os.getenv('DEEPSEEK_API_KEY')` во всех примерах ниже:
проверка `if not key` пропускает и `os.getenv(...)`, и `your_deepseek_api_key`.

### Ловушка `OPENAI_API_KEY` (проверено на openai 2.24.0)

DeepSeek ходит через OpenAI-совместимый SDK, и `OpenAI(api_key=None, …)` **не падает**,
а молча берёт `OPENAI_API_KEY` из окружения. Два исхода, оба без внятного сообщения:

| Что в окружении | Что происходит |
|---|---|
| ни `DEEPSEEK_API_KEY`, ни `OPENAI_API_KEY` | `OpenAIError: The api_key client option must be set … or by setting the **OPENAI_API_KEY** environment variable` — про DeepSeek ни слова, ищешь не там |
| есть `OPENAI_API_KEY` (а он есть у многих) | клиент создаётся молча и отправляет **чужой ключ OpenAI на api.deepseek.com** → голый `401` без причины. Ключ при этом утёк на сторонний хост |

Поэтому ключ передаётся **явно и только из `deepseek_key()`**, а клиент собирается
через фабрику ниже — она проверяет, что уехал именно ключ DeepSeek.

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
- Cost-effective (cheaper than GPT-5.x)
- Fast inference

## Dependencies

```bash
pip install openai  # DeepSeek uses OpenAI-compatible API
```

## Basic Usage

### Chat Completion

```python
import os

from openai import AuthenticationError, OpenAI

# DeepSeek uses OpenAI-compatible API.
# api_key передаём ЯВНО: с api_key=None SDK молча подставит OPENAI_API_KEY
# и отправит чужой ключ на api.deepseek.com (см. «Ловушка OPENAI_API_KEY»).


def deepseek_client() -> OpenAI:
    key = deepseek_key()                      # громко падает на пустом/заглушечном ключе
    client = OpenAI(
        api_key=key,
        base_url=os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1'),
    )
    if client.api_key != key:                 # страховка от подмены из окружения
        raise RuntimeError(
            'клиент собран не с ключом DeepSeek — проверь OPENAI_API_KEY в окружении'
        )
    return client


client = deepseek_client()

def deepseek_chat(prompt: str, system_prompt: str = None,
                  model: str = "deepseek-chat"):
    """
    Chat with DeepSeek.

    Models:
        - deepseek-chat: General purpose, coding, refactoring (fast, smart)
        - deepseek-reasoner: Best for complex reasoning
    """
    messages = []

    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    messages.append({"role": "user", "content": prompt})

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=4096
        )
    except AuthenticationError as e:
        # Голый 401 ничего не объясняет — назови, ЧТО именно уехало на сервер.
        sent = (client.api_key or '')[:8]
        raise RuntimeError(
            f'DeepSeek отверг ключ (401). На api.deepseek.com ушёл ключ, '
            f'начинающийся на {sent!r}. Ключи DeepSeek начинаются с "sk-" и берутся '
            f'на https://platform.deepseek.com/api_keys; ключ OpenAI здесь не подойдёт. '
            f'Проверь DEEPSEEK_API_KEY в ~/.claude/.credentials.master.env. Ответ: {e}'
        ) from e

    return response.choices[0].message.content
```

### Code Generation

```python
def generate_code(task: str, language: str = "python"):
    """Generate code with DeepSeek."""

    system_prompt = f"""You are an expert {language} developer.
    Write clean, well-documented, production-ready code.
    Include type hints, docstrings, and error handling.
    Follow best practices and design patterns."""

    return deepseek_chat(
        prompt=task,
        system_prompt=system_prompt,
        model="deepseek-chat"
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

    return deepseek_chat(prompt, system_prompt, model="deepseek-chat")
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

    return deepseek_chat(prompt, model="deepseek-chat")
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

    return deepseek_chat(prompt, model="deepseek-chat")
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

    return deepseek_chat(prompt, model="deepseek-chat")
```

## API Pricing

| Model | Input | Output |
|-------|-------|--------|
| deepseek-chat | $0.14/1M tokens | $0.28/1M tokens |
| deepseek-reasoner | $0.55/1M tokens | $2.19/1M tokens |

**Note:** DeepSeek is ~10-20x cheaper than GPT-5.x!

## Quick Reference

| Task | Model | Code |
|------|-------|------|
| General chat | deepseek-chat | `deepseek_chat(prompt)` |
| Code generation | deepseek-chat | `generate_code(task)` |
| Code review | deepseek-chat | `review_code(code)` |
| Codebase analysis | deepseek-chat | `analyze_codebase(files)` |
| Complex reasoning | deepseek-reasoner | `solve_problem(problem)` |

## Tips

1. **Use 128K context** - можно загружать целые репозитории
2. **deepseek-chat** для кода/рефакторинга, **deepseek-reasoner** для сложного reasoning
3. **Дешевле GPT-5.x** - используй для heavy tasks
4. **OpenAI-compatible** - тот же синтаксис что и OpenAI
5. **Streaming** - используй для длинных ответов
6. **JSON mode** - для структурированных данных
