---
description: Анализ codebase health с метриками и рекомендациями
argument-hint: [путь к проекту или директории]
---

# 📊 Analyze: $ARGUMENTS

Проанализируй **$ARGUMENTS** и дай recommendations

## Checks:

### Code Quality
- Lines of code
- Cyclomatic complexity
- Code duplication
- Documentation coverage
- Type hints coverage (Python)
- ESLint issues (JS/TS)

### Architecture
- File structure
- Dependencies
- Circular imports
- Unused files
- Missing tests

### Security
- Known vulnerabilities (npm audit, safety)
- Hardcoded secrets
- SQL injection risks
- XSS vulnerabilities

### Performance
- N+1 queries
- Inefficient loops
- Memory leaks potential
- Bundle size (frontend)

### Best Practices
- Error handling
- Logging strategy
- Configuration management
- Environment variables

## Output:
- Health score (0-100)
- Critical issues
- Recommendations
- Quick wins

**Запускай анализ! 📊**
