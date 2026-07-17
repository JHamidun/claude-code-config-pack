# Models & Subscription

## Claude Code Max Subscription

С подпиской Claude Code Max доступны ВСЕ модели без ограничений:

| Алиас | Model ID | Название | Дата релиза |
|-------|----------|----------|-------------|
| `model: "opus"` | `claude-opus-4-8` | Claude Opus 4.8 | — |
| `model: "sonnet"` | `claude-sonnet-5` | Claude Sonnet 5 | — |
| `model: "haiku"` | `claude-haiku-4-5-20251001` | Claude Haiku 4.5 | 15.10.2025 |
| `model: "fable"` | `claude-fable-5` | Claude Fable 5 | — |

> Алиасы `opus`/`sonnet`/`haiku` всегда указывают на текущую версию — код с алиасом не устаревает.

### Предыдущие версии (доступны через API)

| Model ID | Название |
|----------|----------|
| `claude-opus-4-6` | Claude Opus 4.6 |
| `claude-sonnet-4-5-20250929` | Claude Sonnet 4.5 |
| `claude-opus-4-5-20251101` | Claude Opus 4.5 |
| `claude-opus-4-1-20250805` | Claude Opus 4.1 |
| `claude-opus-4-20250514` | Claude Opus 4 |
| `claude-sonnet-4-20250514` | Claude Sonnet 4 |
| `claude-3-7-sonnet-20250219` | Claude Sonnet 3.7 |

## Использование в субагентах

```python
# Haiku - быстрая модель для простых задач
Task(
    subagent_type="general-purpose",
    model="haiku",
    prompt="..."
)

# Sonnet - балансирует скорость и качество
Task(
    subagent_type="general-purpose",
    model="sonnet",
    prompt="..."
)

# Opus - максимальное качество для сложных задач (теперь 4.8!)
Task(
    subagent_type="general-purpose",
    model="opus",
    prompt="..."
)
```

## Рекомендации

- **Haiku 4.5**: Простые задачи, быстрые операции, код-генерация
- **Sonnet 5**: Сбалансированный выбор для большинства задач
- **Opus 4.8**: Сложные задачи, архитектурные решения, глубокий анализ, extended thinking
- **Fable 5**: Текстовые задачи, длинные документы, воркеры в мульти-агентных пайплайнах

## Текущая конфигурация

- **Аутентификация**: Claude Code Max subscription
- **Модель по умолчанию**: Opus 4.8 (алиас `opus` → `claude-opus-4-8`)
- **Доступные модели**: haiku, sonnet, opus, fable (все через подписку)
