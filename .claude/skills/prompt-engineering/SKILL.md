---
name: prompt-engineering
description: "Промпт-инжиниринг: системные промпты, few-shot, structured outputs. Триггеры: «улучши промпт», «leaked prompts». Агент-обёртка→prompt-engineer."
---

# Prompt Engineering Skill

## Overview

Техники создания эффективных промптов для LLM: структура, паттерны, оптимизация.

## When to Use

- Написание системных промптов
- Оптимизация результатов LLM
- Создание агентов и ассистентов
- Настройка Claude/GPT для задач
- Улучшение качества ответов

## Reference Corpus — реальные production-промпты

Прежде чем писать системный промпт агента/бота с нуля — посмотри, как это делают вендоры на
аналогичной роли. `references/system-prompt-leaks.md` — навигация по корпусу
[asgeirtj/system_prompts_leaks](https://github.com/asgeirtj/system_prompts_leaks) (~400 verbatim
системных промптов широкий набор моделей: Claude, GPT/Codex, Gemini, Grok, Perplexity, Cursor, Copilot;
CC0). Там же: workflow diff между версиями (папка `Official/` с датированными снимками) и
дистиллят 15 приёмов, снятых с боевых промптов (два канала commentary/final, «веди с исходом»,
минимальная правка по умолчанию, tone-блоки в XML, safety-директивы буллетами и т.д.).

## Core Principles

### 1. Be Specific & Clear

```
❌ Плохо:
"Write something about dogs"

✅ Хорошо:
"Write a 200-word informative article about the health benefits
of owning a dog, targeting first-time pet owners. Include
3 specific benefits with brief explanations."
```

### 2. Provide Context

```
❌ Плохо:
"Fix this code"

✅ Хорошо:
"I have a Python FastAPI application that handles user authentication.
The following code raises a 500 error when processing login requests.
Please identify the bug and provide a fix with explanation.

```python
[code here]
```"
```

### 3. Use Examples (Few-Shot)

```
Convert product names to slugs.

Examples:
- "iPhone 15 Pro Max" → "iphone-15-pro-max"
- "Samsung Galaxy S24+" → "samsung-galaxy-s24-plus"
- "MacBook Air (M3)" → "macbook-air-m3"

Now convert: "Sony WH-1000XM5 Headphones"
```

## Prompt Patterns

### Role Pattern

```
You are an expert [ROLE] with [X] years of experience in [DOMAIN].
Your specialty is [SPECIALTY].

When responding:
- [Behavior 1]
- [Behavior 2]
- [Behavior 3]
```

**Example:**
```
You are a senior security engineer with 15 years of experience
in application security. Your specialty is identifying OWASP
Top 10 vulnerabilities in web applications.

When reviewing code:
- Identify all security vulnerabilities
- Explain the risk level (Critical/High/Medium/Low)
- Provide secure code alternatives
- Reference relevant CWE/CVE when applicable
```

### Chain of Thought (CoT)

```
Solve this step by step:

1. First, understand the problem
2. Break it into smaller parts
3. Solve each part
4. Combine the solutions
5. Verify the final answer

Problem: [PROBLEM]
```

**Example:**
```
Let's solve this step by step:

Problem: A store has 3 types of items. Type A costs $5, Type B costs $8,
Type C costs $12. A customer bought 15 items for exactly $100.
They bought at least one of each type. How many of each did they buy?

Step 1: Set up equations...
Step 2: Apply constraints...
Step 3: Solve...
```

### Output Format Pattern

```
Provide your response in the following format:

## Summary
[1-2 sentence overview]

## Analysis
[Detailed analysis]

## Recommendations
1. [First recommendation]
2. [Second recommendation]
3. [Third recommendation]

## Code Example
```language
[code]
```
```

### Persona + Task + Format

```
[PERSONA]
You are a technical writer specializing in API documentation.

[TASK]
Create documentation for the following API endpoint.

[FORMAT]
Use this structure:
- Endpoint: [method] [path]
- Description: [what it does]
- Parameters: [table of params]
- Response: [example response]
- Errors: [possible errors]

[INPUT]
POST /api/v1/users - creates new user
```

### Constraint Pattern

```
Generate [OUTPUT] with the following constraints:
- Must be under [N] words/characters
- Must include [REQUIREMENT]
- Must NOT include [EXCLUSION]
- Tone should be [TONE]
- Format as [FORMAT]
```

### Negative Prompting

```
When explaining [CONCEPT]:
- DO explain with practical examples
- DO use simple language
- DO NOT use jargon without explanation
- DO NOT assume prior knowledge
- DO NOT give overly theoretical explanations
```

## Advanced Techniques

### Self-Consistency

```
Solve this problem 3 different ways, then determine which
solution is most likely correct based on consistency.

Problem: [PROBLEM]

Solution 1:
[Let model solve]

Solution 2:
[Let model solve differently]

Solution 3:
[Let model solve another way]

Final Answer:
[Based on consistency of approaches]
```

### Tree of Thoughts

```
Consider this problem from multiple perspectives:

Perspective 1: [Approach A]
- Pros: ...
- Cons: ...
- Likelihood of success: X%

Perspective 2: [Approach B]
- Pros: ...
- Cons: ...
- Likelihood of success: Y%

Best approach: [Decision based on analysis]
```

### Reflection Pattern

```
After generating your response, review it and:
1. Check for factual errors
2. Identify potential misunderstandings
3. Note any assumptions made
4. Suggest improvements if needed

Then provide the final, refined response.
```

### Meta-Prompting

```
Before answering, first:
1. Identify what type of question this is
2. Determine what information is needed
3. Consider potential edge cases
4. Plan your response structure

Then provide your answer.
```

## System Prompts

### Agent System Prompt Template

```markdown
# [AGENT NAME]

## Role
You are [ROLE DESCRIPTION].

## Capabilities
You can:
- [Capability 1]
- [Capability 2]
- [Capability 3]

## Constraints
You must:
- [Constraint 1]
- [Constraint 2]

You must NOT:
- [Prohibition 1]
- [Prohibition 2]

## Communication Style
- Tone: [professional/casual/technical]
- Length: [concise/detailed]
- Format: [structured/conversational]

## Tools Available
- [Tool 1]: [description]
- [Tool 2]: [description]

## Examples
[Few-shot examples of expected behavior]
```

### Code Assistant Prompt

```
You are an expert programmer. When writing code:

1. Write clean, readable, maintainable code
2. Follow language-specific best practices
3. Include error handling
4. Add comments only where logic is complex
5. Consider edge cases
6. Optimize for readability over cleverness

When reviewing code:
1. Check for bugs and security issues
2. Suggest improvements with explanations
3. Praise good patterns you see
4. Be specific about line numbers

Format code responses with proper syntax highlighting.
```

## Prompt Optimization

### Iterative Refinement

```
v1: "Write a poem"
   → Too vague

v2: "Write a haiku about spring"
   → Better, but lacks style

v3: "Write a haiku about spring in the style of Matsuo Basho,
    focusing on a single moment in nature"
   → Much better

v4: "Write a haiku about spring:
    - Style: Matsuo Basho
    - Theme: A single moment of awakening in nature
    - Include: seasonal reference (kigo)
    - Mood: contemplative, peaceful"
   → Optimized
```

### Temperature Guide

| Temperature | Use Case |
|-------------|----------|
| 0.0-0.3 | Code, facts, structured output |
| 0.4-0.6 | Balanced creativity/accuracy |
| 0.7-0.9 | Creative writing, brainstorming |
| 1.0+ | Highly creative, experimental |

### Token Optimization

```
# Verbose (uses more tokens)
"Please kindly provide me with a detailed explanation of
how the process works step by step"

# Concise (saves tokens)
"Explain the process step by step"

# Even more concise
"Steps for [process]:"
```

## Testing Prompts

```python
test_cases = [
    # Edge cases
    {"input": "", "expected_behavior": "Handle empty gracefully"},
    {"input": "very long text...", "expected": "Truncate or summarize"},
    {"input": "malicious <script>", "expected": "Sanitize/reject"},

    # Normal cases
    {"input": "typical request", "expected": "Standard response"},

    # Boundary cases
    {"input": "ambiguous request", "expected": "Ask for clarification"},
]

for case in test_cases:
    response = call_llm(prompt + case["input"])
    assert validate(response, case["expected"])
```

## Claude-Specific Tips

1. **XML tags** - Claude responds well to XML structure
   ```
   <context>Background info here</context>
   <task>What to do</task>
   <format>How to format response</format>
   ```

2. **Artifacts** - For code, use artifact format
3. **Thinking** - Ask Claude to "think step by step"
4. **Constitutional AI** - Claude follows ethical guidelines

## Tips

1. **Iterate** - First prompt rarely perfect
2. **Test edge cases** - Check unusual inputs
3. **Be explicit** - Don't assume LLM understands
4. **Use structure** - Headers, bullets, numbering
5. **Provide examples** - Few-shot learning helps
6. **Set constraints** - Length, format, style
7. **Ask for reasoning** - "Explain your thinking"
