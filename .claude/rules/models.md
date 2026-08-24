# Models & Subscription — указатель

> **ЕДИНЫЙ КАНОН моделей (все ID, алиасы, image, внешние) → `config/models.md`.** Здесь — только ядро для рантайма.
>
> ⚠️ **Номера версий здесь намеренно не выписаны.** Это правило грузится каждую
> сессию, а канон читается по требованию — при расхождении обычно побеждает
> версия отсюда. И расхождение не падает: устаревший идентификатор молча отдаёт
> вчерашнюю модель. Поэтому в рантайме — только алиасы.

## Claude Code Max Subscription

- **Аутентификация:** Claude Code Max subscription — ВСЕ модели доступны без ограничений (не по API).
- **Актуальные алиасы:** `opus` (оркестратор/сессия) · `fable` (text-воркеры) · `sonnet` (легаси, не дефолт) · `haiku` (массовое простое). Точные model ID — `config/models.md`.
- **⚠️ Text-субагенты — ТОЛЬКО Fable 5** (`model: "fable"`), ≤5 одновременно; Fable упал на лимите → подхватить Opus (resume + смена model).
- Предыдущие версии Claude — через API, список в `config/models.md`.

```python
Task(subagent_type="general-purpose", model="fable", prompt="...")  # text-воркер (дефолт)
Task(subagent_type="general-purpose", model="haiku", prompt="...")  # простое/быстрое
Task(subagent_type="general-purpose", model="opus",  prompt="...")  # оркестратор/сложное
```

Какую модель для какой задачи (decision tree) → `rules/model-selection.md`.
