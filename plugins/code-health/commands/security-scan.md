---
description: "Security-аудит проекта: секреты в коде, pip/npm audit, OWASP Top 10, конфигурация DEBUG/CORS. Триггеры: «аудит безопасности», «проверь на уязвимости»."
argument-hint: "[путь к проекту]"
---

# Комплексный Security Audit

**Аргументы:** $ARGUMENTS (путь к проекту или пусто для текущей директории)

## Задача

Проведи комплексный security audit проекта по всем направлениям.

## Чеклист проверки

### 1. Секреты в коде
```bash
# Поиск потенциальных секретов
grep -rn --include="*.py" --include="*.js" --include="*.ts" --include="*.env*" \
  -E "(api_key|apikey|secret|password|token|credential|auth).*=" . 2>/dev/null | head -50

# Проверка .gitignore
cat .gitignore 2>/dev/null | grep -E "(\.env|secret|credential|key)"
```

### 2. Уязвимости зависимостей

**Python:**
```bash
pip audit 2>/dev/null || echo "pip-audit not installed"
safety check 2>/dev/null || echo "safety not installed"
```

**Node.js:**
```bash
npm audit 2>/dev/null || echo "Not a Node.js project"
```

### 3. OWASP Top 10 проверка

Проверь код на:
- **Injection** (SQL, Command, XSS)
- **Broken Authentication**
- **Sensitive Data Exposure**
- **Security Misconfiguration**
- **Insecure Deserialization**

### 4. Конфигурация

- DEBUG режим выключен?
- HTTPS enforced?
- CORS правильно настроен?
- Rate limiting есть?

## Формат отчёта

```markdown
# Security Audit Report

**Дата:** [дата]
**Проект:** [название]

## Критические (требуют немедленного исправления)
- [ ] Issue 1

## Высокий риск
- [ ] Issue 2

## Средний риск
- [ ] Issue 3

## Рекомендации
- Recommendation 1
```

## После аудита

Предложи конкретные fixes для найденных проблем.
