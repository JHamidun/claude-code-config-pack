# Модели: таблицы выбора, внешние движки, стоимость

> Вынесено из `rules/models.md` 05.09 — нужно при планировании работы,
> а не в каждом запросе. Канон идентификаторов → `config/models.md`.

## Quick Decision Table (уровень, не движок)

| Task Type | Level | Why |
|-----------|-------|-----|
| Architecture decisions | opus-level | Deep reasoning, tradeoff analysis |
| Complex debugging | opus-level | Root cause analysis, multi-file context |
| Code implementation | standard (opus-level if complex) | Routine vs complex |
| Code review | standard | Pattern matching |
| Quick search/exploration | light | Simple queries |
| File operations | light | Rename, move, simple edits |
| Writing documentation | standard | Good prose, fast enough |
| Security audit | opus-level | Thoroughness matters most |
| Refactoring | standard | Pattern recognition, speed |
| Test writing | standard | Coverage patterns, mocking |
| Bug hunting | opus-level | Systematic root cause analysis |
| Translation/i18n | light | Simple string operations |
| Data migration scripts | standard | Structured, predictable logic |
| API design | opus-level | Consistency, edge cases, naming |


## Decision Flow for Subagents

1. Search/lookup/classification? -> light-level (короткий промпт; массово — haiku)
2. Generates or modifies code? -> standard-level (Fable, обычный промпт)
3. Reasoning about tradeoffs or security? -> opus-level (расширенный контекст + верификация)
4. Worker in a multi-agent pipeline? -> Fable (default)
5. Orchestrator of a multi-agent pipeline? -> сессия/Opus (не спавнить лишнего оркестратора)

### Калибровка уровня

- ВНИЗ к light: exploring codebase, rename/search-and-replace, классификация, commit messages, well-defined boilerplate/CRUD.
- ВВЕРХ к opus-level: production-дебаг, дизайн систем/API, security-аудит, решения при неполной информации, 500K+ контекст.


## External Models (via AI Gateway)

| Model | When to Use |
|-------|------------|
| GPT-5.6 (Codex CLI) / GPT-5.4 | Cross-model validation, второе мнение, function calling |
| Gemini 3.1 Pro | 2M context, multimodal, Google ecosystem |
| Gemini Flash Image (NB2) | Image generation (канон → config/models.md) |
| `gpt-5.6-terra` | Math, logic, structured reasoning (⚠️ `o4-mini` снимается 23.10.2026) |
| Kimi K2 | Algorithm problems, deep reasoning |
| deep-research-pro | Multi-step research with citations |


## Cost-Efficiency Rules

1. При rate-limit снижай параллелизм; Fable упал на лимите — Opus подхватывает (resume + смена model).
2. Haiku — для high-volume параллельных простых задач (10+), не для нюансных.
3. Opus не спавнить как воркера без причины — он оркестратор сессии.
4. External models стоят реальных денег — только когда Claude-модели не умеют (медиа, 2M контекст, кросс-валидация).
