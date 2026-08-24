---
name: kimi
description: "Kimi K2 (Moonshot AI, KIMI_API_KEY, kimi-k2-thinking): глубокий reasoning, код-анализ, алгоритмы. Триггеры: «спроси кими», «Kimi K2»."
---

# Kimi K2 API Skill

## Overview

Expert skill for Kimi K2 (Moonshot AI) - specialized in deep reasoning and code analysis.

## API Key

```bash
# API ключи: ~/.claude/.credentials.master.env
# Переменная: KIMI_API_KEY
export KIMI_API_KEY="$(grep -m1 '^KIMI_API_KEY=' ~/.claude/.credentials.master.env | cut -d= -f2-)"
export KIMI_BASE_URL=https://api.moonshot.ai/v1
export KIMI_MODEL=kimi-k2-thinking
```

## When to Use Kimi K2

**Best for:**
- Deep code review (kimi-code-reviewer agent)
- Complex debugging (kimi-debugging-specialist agent)
- Performance optimization (kimi-performance-optimizer agent)
- Algorithm design (kimi-algorithm-specialist agent)
- Code refactoring (kimi-refactoring-specialist agent)
- Testing strategy (kimi-testing-strategist agent)
- Senior coding tasks (kimi-senior-coder agent)

**Advantages:**
- Excellent reasoning capabilities
- Strong code analysis
- Thinking process visible
- Good for multi-step problems
- 128K context window

## Dependencies

```bash
pip install openai  # Uses OpenAI-compatible API
```

## Basic Usage

### Setup Client

```python
from openai import OpenAI
import os

client = OpenAI(
    api_key=os.getenv('KIMI_API_KEY'),
    base_url=os.getenv('KIMI_BASE_URL', 'https://api.moonshot.ai/v1')
)

MODEL = os.getenv('KIMI_MODEL', 'kimi-k2-thinking')
```

### Deep Reasoning

```python
def kimi_reason(problem: str, show_thinking: bool = True):
    """
    Use Kimi K2 for complex reasoning tasks.

    Args:
        problem: The problem to analyze
        show_thinking: Whether to include thinking process
    """
    system = """You are an expert problem solver.
    Think step by step and show your reasoning process.
    Be thorough and consider edge cases."""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": problem}
        ],
        temperature=0.7,
        max_tokens=8192
    )

    return response.choices[0].message.content

# Usage
result = kimi_reason("Design an algorithm to find the shortest path in a weighted graph with negative edges")
```

### Code Review

```python
def kimi_code_review(code: str, language: str = "python"):
    """
    Comprehensive code review with Kimi K2.

    Returns:
        - Bugs and issues
        - Security vulnerabilities
        - Performance concerns
        - Best practices violations
        - Improvement suggestions
    """
    prompt = f"""Review this {language} code thoroughly:

```{language}
{code}
```

Analyze for:
1. **Bugs**: Logic errors, edge cases, null checks
2. **Security**: Injection, XSS, authentication issues
3. **Performance**: Complexity, memory leaks, inefficiencies
4. **Style**: Naming, structure, readability
5. **Best Practices**: SOLID, DRY, error handling

Provide specific line numbers and fix suggestions."""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=8192
    )

    return response.choices[0].message.content

# Usage
review = kimi_code_review("""
def process_user(user_id):
    user = db.query(f"SELECT * FROM users WHERE id = {user_id}")
    return user
""")
```

### Debugging Analysis

```python
def kimi_debug(error: str, code: str, context: str = ""):
    """
    Analyze and fix bugs with Kimi K2.

    Args:
        error: Error message or description
        code: Relevant code
        context: Additional context (stack trace, logs)
    """
    prompt = f"""Debug this issue:

**Error:**
{error}

**Code:**
```
{code}
```

**Context:**
{context}

Provide:
1. Root cause analysis
2. Step-by-step fix
3. Prevention strategy
4. Test cases to verify fix"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=8192
    )

    return response.choices[0].message.content
```

### Performance Optimization

```python
def kimi_optimize(code: str, metrics: str = ""):
    """
    Analyze and optimize code performance.

    Args:
        code: Code to optimize
        metrics: Performance metrics if available
    """
    prompt = f"""Optimize this code for performance:

```
{code}
```

{f"Current metrics: {metrics}" if metrics else ""}

Analyze:
1. Time complexity - current and optimized
2. Space complexity - memory usage
3. Bottlenecks - hot paths, expensive operations
4. Caching opportunities
5. Algorithm alternatives

Provide optimized version with benchmarks."""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=8192
    )

    return response.choices[0].message.content
```

### Algorithm Design

```python
def kimi_algorithm(problem: str, constraints: str = ""):
    """
    Design optimal algorithm for a problem.

    Args:
        problem: Problem description
        constraints: Time/space constraints
    """
    prompt = f"""Design an algorithm for:

**Problem:**
{problem}

**Constraints:**
{constraints if constraints else "Optimize for time, then space"}

Provide:
1. Problem analysis
2. Multiple approaches with trade-offs
3. Optimal solution with complexity analysis
4. Implementation in Python
5. Test cases
6. Edge cases handling"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        max_tokens=8192
    )

    return response.choices[0].message.content
```

### Refactoring

```python
def kimi_refactor(code: str, goals: str = ""):
    """
    Refactor code for better quality.

    Args:
        code: Code to refactor
        goals: Specific refactoring goals
    """
    prompt = f"""Refactor this code:

```
{code}
```

Goals: {goals if goals else "Improve readability, maintainability, and testability"}

Apply:
1. SOLID principles
2. Design patterns where appropriate
3. Clean code practices
4. Better naming conventions
5. Proper abstraction levels

Show before/after with explanations."""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=8192
    )

    return response.choices[0].message.content
```

### Testing Strategy

```python
def kimi_test_strategy(code: str, requirements: str = ""):
    """
    Create comprehensive testing strategy.

    Args:
        code: Code to test
        requirements: Specific requirements
    """
    prompt = f"""Create a testing strategy for:

```
{code}
```

{f"Requirements: {requirements}" if requirements else ""}

Include:
1. Unit tests - all functions and methods
2. Integration tests - component interactions
3. Edge cases - boundaries, nulls, errors
4. Performance tests - load, stress
5. Security tests - if applicable

Provide test code with assertions."""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=8192
    )

    return response.choices[0].message.content
```

## Agent Integration

Готовый агент ровно один — `agents/kimi-algorithm-specialist.md` (алгоритмы, глубокий
reasoning). Остальные роли (ревью, дебаг, рефакторинг, тесты, перф) закрываются кодом
из этого файла: свой промпт + вызов `client.chat.completions.create(model=MODEL, …)`.

Реестра агентов в `agents.json` в паке нет — это не используемый механизм. Имена
`kimi-code-reviewer`, `kimi-senior-coder`, `kimi-refactoring-specialist`,
`kimi-debugging-specialist`, `kimi-performance-optimizer`, `kimi-testing-strategist`
не резолвятся ни во что — не пытайся их спавнить.

## Slash Commands

```bash
# Deep reasoning — единственная существующая команда
/kimi-reasoning "complex problem description"
```

Команд `/kimi-review` и `/kimi-fix` в системе нет (в `commands/` лежит только
`kimi-reasoning.md`). Для ревью и фикса — либо агент `code-reviewer` / `/health bugs`,
либо прямой вызов функций выше.

## Tips

1. **Thinking model** - kimi-k2-thinking shows reasoning process
2. **Low temperature** - Use 0.2-0.3 for code tasks
3. **128K context** - Can analyze large codebases
4. **Structured prompts** - Use clear sections for best results
5. **Chain of thought** - Encourage step-by-step reasoning
6. **Specific questions** - Ask for line numbers and concrete fixes
