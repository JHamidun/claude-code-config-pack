---
description: Deep code review using Kimi K2 (security, performance, quality)
argument-hint: [file path or directory]
---

# 🔍 Kimi K2 Code Review: $ARGUMENTS

Запускаю **глубокий анализ кода** с помощью @code-reviewer (model: kimi-k2-thinking)...

---

## 📋 Что проверяется:

### 🔒 Security (CRITICAL)
- SQL injection, XSS, command injection
- Authentication/authorization flaws
- Insecure data handling
- Secrets in code
- Input validation gaps
- OWASP Top 10 vulnerabilities

### ⚡ Performance
- Algorithm complexity analysis
- Database query optimization (N+1 queries)
- Memory leaks
- Blocking operations
- Caching opportunities

### 📊 Code Quality
- SOLID principles
- Design patterns
- Code smells
- DRY violations
- Naming conventions
- Readability

### ✅ Best Practices
- Error handling
- Logging
- Type hints
- Documentation
- Test coverage
- Edge cases

---

## 🎯 Review Execution:

@code-reviewer, проведи **comprehensive code review** для: **$ARGUMENTS**

**Инструкции:**

1. **Прочитай весь код** внимательно
2. **Security first** - найди все потенциальные уязвимости
3. **Performance** - проанализируй complexity и bottlenecks
4. **Quality** - проверь соответствие best practices
5. **Приоритизируй** - сначала CRITICAL, потом HIGH, MEDIUM, LOW
6. **Будь конкретным** - укажи line numbers и code snippets
7. **Дай фиксы** - покажи КАК исправить каждую проблему
8. **Объясни impact** - почему это важно

**Output format:**
- Structured JSON с categorized issues
- Overall score (0-100)
- Recommendation: APPROVE / REQUEST_CHANGES / REJECT
- Конкретные fixes для каждой проблемы
- Список good practices (что сделано хорошо)

---

## 📈 Review Levels:

Kimi K2 проводит review на уровне **SWE-bench 65.8%** - это:
- Лучше чем GPT-4 (52.3%)
- Лучше чем Claude Sonnet 4 (58.6%)
- Лучше чем Gemini 2.5 Flash (54.1%)

**Специализация Kimi K2:**
- Exceptional код analysis
- Deep algorithm understanding
- Strong security knowledge
- Math reasoning для complexity

---

## 🚀 После Review:

Когда review готов:

1. **Критичные проблемы** - исправь немедленно
2. **High priority** - исправь до merge
3. **Medium/Low** - создай issues для future fixes
4. **Apply fixes** - используй предложенные решения
5. **Re-review** - если много изменений

---

**Начинаю review с Kimi K2...** 🔍