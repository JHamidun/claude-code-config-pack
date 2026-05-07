---
description: Автоматический fix кода на основе Kimi K2 review
argument-hint: [file path]
---

# 🔧 Kimi K2 Auto-Fix: $ARGUMENTS

Автоматическое исправление кода с помощью @code-reviewer (model: kimi-k2-thinking)...

---

## 🎯 Процесс:

### 1. Review код
@code-reviewer проведёт comprehensive review: **$ARGUMENTS**

### 2. Identify issues
Найдёт все проблемы:
- CRITICAL (security, breaking bugs)
- HIGH (performance, major issues)
- MEDIUM (code quality, best practices)
- LOW (minor improvements)

### 3. Generate fixes
Создаст исправленную версию кода:
- Устранит security vulnerabilities
- Оптимизирует performance
- Улучшит code quality
- Добавит type hints
- Улучшит error handling
- Добавит документацию

### 4. Show diff
Покажет что было изменено (git-style diff)

### 5. Apply changes
Применит исправления (с твоим одобрением)

---

## 🔒 Что фиксится автоматически:

### Security (CRITICAL):
- ✅ SQL injection → parameterized queries
- ✅ XSS vulnerabilities → proper escaping
- ✅ Command injection → input validation
- ✅ Insecure auth → secure implementations
- ✅ Secrets in code → environment variables

### Performance (HIGH):
- ✅ N+1 queries → batch loading
- ✅ Inefficient loops → optimized algorithms
- ✅ Memory leaks → proper cleanup
- ✅ Blocking operations → async/await

### Code Quality (MEDIUM):
- ✅ Missing type hints → add annotations
- ✅ Long functions → extract methods
- ✅ Code duplication → DRY refactoring
- ✅ Poor naming → descriptive names
- ✅ Missing docstrings → comprehensive docs

---

## 📝 Инструкции для агента:

@code-reviewer:

1. **Прочитай код** из: $ARGUMENTS
2. **Найди все issues** (security, performance, quality)
3. **Создай fixed version** устраняющую проблемы
4. **Покажи diff** - что изменилось и почему
5. **Объясни changes** - какие проблемы решены

**Требования к fixes:**
- Preserve functionality (не ломай работающий код)
- Fix only actual issues (не "улучшай" что работает хорошо)
- Add comments для non-obvious changes
- Maintain code style
- Add type hints
- Improve error handling

**Format output:**
```markdown
## Original Issues Found:
[список всех найденных проблем]

## Fixed Version:
[исправленный код]

## Changes Made:
[git-style diff]

## Explanation:
[почему каждое изменение было сделано]

## Remaining Suggestions:
[что ещё можно улучшить (опционально)]
```

---

**⚠️ ВАЖНО:**
Перед применением изменений:
1. Review предложенные fixes
2. Проверь что functionality сохранена
3. Run tests (если есть)
4. Commit changes с описанием fixes

---

**Начинаю auto-fix с Kimi K2...** 🔧