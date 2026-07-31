# Models & Subscription — указатель

> **ЕДИНЫЙ КАНОН моделей (все ID, алиасы, image, внешние) → `config/models.md`.** Здесь — только ядро для рантайма.

## Claude Code Max Subscription

- **Аутентификация:** Claude Code Max subscription — ВСЕ модели доступны без ограничений (не по API).
- **Актуальные алиасы:** `opus` → `claude-opus-4-8` (Opus 4.8, дефолт оркестратора/сессии) · `fable` → `claude-fable-5` (Fable 5) · `sonnet` → `claude-sonnet-4-5-20250929` · `haiku` → `claude-haiku-4-5-20251001`.
- **⚠️ Text-субагенты — ТОЛЬКО Fable 5** (`model: "fable"`), ≤5 одновременно; Fable упал на лимите → подхватить Opus (resume + смена model).
- Предыдущие версии (opus-4-6/4-5/4-1/4, sonnet-4/3.7 и т.д.) — через API, список в `config/models.md`.

```python
Task(subagent_type="general-purpose", model="fable", prompt="...")  # text-воркер (дефолт)
Task(subagent_type="general-purpose", model="haiku", prompt="...")  # простое/быстрое
Task(subagent_type="general-purpose", model="opus",  prompt="...")  # оркестратор/сложное
```

Какую модель для какой задачи (decision tree) → `rules/model-selection.md`.
