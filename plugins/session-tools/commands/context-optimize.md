---
description: "Сборка оптимального контекста под тип задачи (bug fix / feature / review / refactoring / testing) по принципам Context Engineering: релевантные источники, few-shot, компрессия токенов. Триггеры: «оптимизируй контекст», «собери контекст под задачу», «context engineering». Методология целиком → skill context-engineering."
argument-hint: "[тип задачи] \"<описание>\""
---

Оптимизируй контекст для текущей задачи используя Context Engineering принципы.

## Что делает эта команда:

1. **Анализирует тип задачи**:
   - Bug fix → Загружает error logs, git blame, related tests
   - New feature → Загружает requirements, architecture, similar code
   - Code review → Загружает git history, test coverage, review examples
   - Refactoring → Загружает dependency graph, code metrics, tests
   - Testing → Загружает edge cases, test examples, requirements

2. **Собирает релевантный контекст** из multiple sources:
   - CLAUDE.md (project instructions)
   - Memory MCP (previous context)
   - Linear MCP (tasks)
   - GitHub MCP (code history)
   - Sentry MCP (errors)
   - Filesystem MCP (codebase)

3. **Оптимизирует token usage**:
   - Prioritizes by relevance
   - Truncates long sources
   - Applies compression
   - Removes duplicates

4. **Добавляет few-shot examples** для улучшения результатов

## Пример использования:

```bash
# Bug fix
/context-optimize bug_fix "NoneType error in auth.py"

# New feature
/context-optimize new_feature "Add OAuth2 authentication"

# Code review
/context-optimize code_review "Review Your Project security"
```

## Output:

Возвращает JSON с оптимизированным контекстом:
- Релевантные источники данных
- Few-shot примеры
- Token usage stats
- Примененные оптимизации

## Принципы:

**Context Engineering > Prompt Engineering**
- Правильный контекст важнее clever prompts
- Меньше токенов, больше качества
- Dynamic assembly from multiple sources
- Relevance filtering

**Based on:**
- [LangChain Context Engineering](https://blog.langchain.com/the-rise-of-context-engineering/)
- [12 Factor Agents](https://github.com/humanlayer/12-factor-agents)
- [Anthropic MCP Best Practices](https://www.anthropic.com/engineering/writing-tools-for-agents)