# Model Selection Guide

> **КАНОН (config/models.md):** движок ВСЕХ text-субагентов = **Fable 5** (`model: "fable"`), ≤5 одновременно (комфорт 3-4); Fable упал на лимите → подхватить Opus (resume + смена model). **Opus 4.8** = основная сессия / оркестратор. Уровни ниже (opus/standard/light) выбирают СЛОЖНОСТЬ задачи — глубину промпта, контекст, верификацию — а НЕ движок воркера.

## Модели (компакт)

| Алиас | Модель | Роль |
|-------|--------|------|
| `opus` | Opus 4.8 (`claude-opus-4-8`) | Оркестратор сессии; максимум reasoning; 1M контекст |
| `fable` | Fable 5 (`claude-fable-5`) | **Движок ВСЕХ text-воркеров** (дефолт спавна) |
| `haiku` | Haiku 4.5 | Массовые дешёвые прогоны (10+ параллельных), классификация |
| `sonnet` | Sonnet 4.5 | Доступен, но для воркеров НЕ дефолт (легаси) |

## Уровни сложности задачи

| Уровень | Что означает для промпта воркера |
|---------|----------------------------------|
| **opus-level** | Богатый контекст, явные quality-gates, верификация результата; оркестрирует сессия (Opus) |
| **standard-level** | Обычный промпт с целью и file paths; Fable справляется сам |
| **light-level** | Короткий промпт, низкий effort; для 10+ параллельных простых прогонов допустим `model: "haiku"` |

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

## Spawn Patterns

```python
Task(subagent_type="general-purpose", model="fable", prompt="...")  # text-воркер (ВСЕГДА дефолт)
Task(subagent_type="general-purpose", model="haiku", prompt="...")  # массовое простое (10+ параллельных)
Task(subagent_type="general-purpose", model="opus",  prompt="...")  # оркестратор / подхват после лимита Fable
```

- В frontmatter агентов: `model: fable` (канон, проставлен во всех agents/; исключение — orchestrator.md = opus).
- Смена модели сессии: `/model opus|fable|sonnet|haiku`.

## External Models (via AI Gateway)

| Model | When to Use |
|-------|------------|
| GPT-5.6 (Codex CLI) / GPT-5.4 | Cross-model validation, второе мнение, function calling |
| Gemini 3.1 Pro | 2M context, multimodal, Google ecosystem |
| Gemini Flash Image (NB2) | Image generation (канон → config/models.md) |
| o4-mini | Math, logic, structured reasoning |
| Kimi K2 | Algorithm problems, deep reasoning |
| deep-research-pro | Multi-step research with citations |

## Cost-Efficiency Rules

1. Text-воркеры = Fable всегда; уровень сложности регулируй промптом/контекстом, не сменой движка.
2. ≤5 Fable одновременно; при rate-limit снижай параллелизм, упал — Opus подхватывает.
3. Haiku — для high-volume параллельных простых задач (10+), не для нюансных.
4. Opus не спавнить как воркера без причины — он оркестратор сессии.
5. External models стоят реальных денег — только когда Claude-модели не умеют (медиа, 2M контекст, кросс-валидация).

---

Полный каталог ID/алиасов (Opus 4.8, Fable 5, image-модели NB2/Lite/Pro, внешние) → `config/models.md`.
