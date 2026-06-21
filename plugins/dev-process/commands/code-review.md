---
description: Комплексный code review с проверкой всех аспектов
argument-hint: [file path или PR number]
---

# Code Review: $ARGUMENTS

## 1. Структурный анализ

### Читаемость
- Понятные названия переменных и функций?
- Есть docstrings/комментарии для сложной логики?
- Код следует style guide проекта?

### Архитектура
- Соблюдается ли принцип единой ответственности?
- Нет дублирования кода (DRY)?
- Правильная декомпозиция на функции/классы?

## 2. Функциональность

### Логика
- Код делает то, что должен?
- Обработаны edge cases?
- Нет логических ошибок?

### Тесты
```bash
# Запусти тесты
pytest $ARGUMENTS -v

# Проверь coverage
pytest $ARGUMENTS --cov --cov-report=html
```

Coverage должен быть >80% для новых фич.

## 3. Безопасность

### Проверь на уязвимости:
- SQL injection (используется ли ORM/параметризованные запросы?)
- XSS (экранируется ли user input?)
- Аутентификация/авторизация на месте?
- Секреты не в коде (используются env vars)?

### Security scan
```bash
# Python
bandit -r $ARGUMENTS

# npm
npm audit

# SAST
semgrep --config=auto $ARGUMENTS
```

## 4. Производительность

### Оптимизация
- Нет N+1 запросов к БД?
- Используется кэширование где нужно?
- Эффективные алгоритмы (O(n) vs O(n²))?

### Profiling (если нужно)
```bash
# Python
python -m cProfile $ARGUMENTS

# Node.js
node --prof $ARGUMENTS
```

## 5. Maintainability

### Зависимости
- Минимальное количество dependencies?
- Все dependencies актуальные?
- Нет конфликтов версий?

### Документация
- README обновлён?
- API docs актуальны?
- Есть примеры использования?

## 6. Git лучшие практики

### Commits
- Атомарные коммиты (один логический change)?
- Понятные commit messages?
- Нет debug кода/комментариев?

### Branch
- Актуальная ветка (merged с main)?
- Нет merge conflicts?
- Clean history (нет "fix typo" коммитов)?

## Итоговый чеклист

**Code Quality:**
- [ ] Читаемый и понятный код
- [ ] Следует style guide
- [ ] Нет code smells

**Functionality:**
- [ ] Работает как ожидается
- [ ] Тесты покрывают функциональность
- [ ] Edge cases обработаны

**Security:**
- [ ] Нет очевидных уязвимостей
- [ ] Security scanners прошли
- [ ] Секреты в env vars

**Performance:**
- [ ] Нет очевидных bottlenecks
- [ ] Эффективные алгоритмы
- [ ] Кэширование где нужно

**Documentation:**
- [ ] Код задокументирован
- [ ] README актуален
- [ ] Changelog обновлён

## Рекомендации

### 👍 Approve - если:
- Все чеклисты пройдены
- Код улучшает кодовую базу
- Готов к production

### 🔄 Request Changes - если:
- Есть критичные проблемы
- Нужны тесты
- Security issues

### 💬 Comment - если:
- Есть suggestions для улучшения
- Нужно обсуждение подхода
- Вопросы по implementation

---

**Final Score:** [Оцени от 1 до 10]

**Summary:** [Краткий вердикт и ключевые моменты]
