# Performance Analysis & Optimization

**Аргументы:** $ARGUMENTS (путь к файлу/модулю или тип анализа: cpu/memory/io/all)

## Задача

Проанализируй производительность и предложи оптимизации.

## Типы анализа

### 1. CPU Profiling

**Python:**
```python
import cProfile
import pstats

# Профилирование функции
cProfile.run('function_to_profile()', 'output.prof')

# Анализ результатов
stats = pstats.Stats('output.prof')
stats.sort_stats('cumulative')
stats.print_stats(20)
```

**Node.js:**
```bash
node --prof app.js
node --prof-process isolate-*.log > processed.txt
```

### 2. Memory Analysis

**Python:**
```python
from memory_profiler import profile

@profile
def memory_hungry_function():
    pass
```

**Node.js:**
```bash
node --inspect app.js
# Открыть chrome://inspect
```

### 3. Database Queries

```sql
-- PostgreSQL slow queries
SELECT query, calls, mean_time, total_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 20;
```

### 4. Code Review для производительности

Ищи:
- **N+1 queries** - циклы с запросами к БД
- **Неиспользуемые импорты** - лишний overhead
- **Синхронный I/O** - блокирующие операции
- **Большие объекты в памяти** - утечки
- **Отсутствие кэширования** - повторные вычисления

## Формат отчёта

```markdown
# Performance Report

## Bottlenecks найдены

| Место | Проблема | Impact | Fix |
|-------|----------|--------|-----|
| file.py:42 | N+1 query | High | Use prefetch_related |

## Метрики

- Response time: X ms → target Y ms
- Memory usage: X MB → target Y MB
- CPU usage: X% → target Y%

## Рекомендации по приоритету

1. [Critical] ...
2. [High] ...
3. [Medium] ...
```

## Инструменты

- **Python:** cProfile, memory_profiler, line_profiler, py-spy
- **Node.js:** clinic, 0x, node --prof
- **General:** Sentry performance, New Relic
