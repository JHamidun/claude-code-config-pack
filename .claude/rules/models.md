# Models & Subscription

## Claude Code Max Subscription

С подпиской Claude Code Max доступны ВСЕ модели без ограничений:

| Алиас | Model ID | Название | Дата релиза |
|-------|----------|----------|-------------|
| `model: "opus"` | `claude-opus-4-6` | Claude Opus 4.6 | 04.02.2026 |
| `model: "sonnet"` | `claude-sonnet-4-5-20250929` | Claude Sonnet 4.5 | 29.09.2025 |
| `model: "haiku"` | `claude-haiku-4-5-20251001` | Claude Haiku 4.5 | 15.10.2025 |

### Предыдущие версии (доступны через API)

| Model ID | Название |
|----------|----------|
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

# Opus - максимальное качество для сложных задач (теперь 4.6!)
Task(
    subagent_type="general-purpose",
    model="opus",
    prompt="..."
)
```

## Рекомендации

- **Haiku 4.5**: Простые задачи, быстрые операции, код-генерация
- **Sonnet 4.5**: Сбалансированный выбор для большинства задач
- **Opus 4.6**: Сложные задачи, архитектурные решения, глубокий анализ, extended thinking

## Текущая конфигурация

- **Аутентификация**: Claude Code Max subscription
- **Модель по умолчанию**: Opus 4.6 (алиас `opus` → `claude-opus-4-6`)
- **Доступные модели**: haiku, sonnet, opus (все через подписку)
