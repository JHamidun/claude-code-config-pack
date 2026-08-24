---
name: python-fullstack-dev
description: "Разработка на Python: Django, FastAPI, Flask, data science, тесты, деплой. Триггеры: «напиши на питоне», «python-скрипт», «поправь питон-код». НЕ Telegram-бот→telegram-bot-toolkit."
---

# Python Full-Stack Development

Covers Django, FastAPI, Flask, SQLAlchemy, pytest and deployment. Telegram bots are
a separate skill (`telegram-bot-toolkit`) — they have their own runtime and gotchas.

## Project conventions

Pick these unless the existing repo already decided otherwise; consistency inside one
repo beats any of them individually.

- **Layout:** `src/<package>/` with `api/`, `models/`, `services/`, `utils/`; `tests/`
  as a sibling of `src/`, never inside the package. The `src/` layout forces tests to
  run against the installed package, so a missing `__init__` or a bad packaging config
  fails in CI instead of silently passing because the cwd happened to be importable.
- **Installer:** `uv` by default (`uv venv`, `uv pip install -r requirements.txt`),
  Poetry when the project already uses it, plain `venv` as the fallback.
- **Requires-python:** `>=3.11`. Formatters and linters pinned to the same target.

```toml
[tool.black]
line-length = 100
target-version = ['py311']

[tool.ruff]
line-length = 100
select = ["E", "F", "I", "N", "W"]

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
```

`strict = true` is deliberate: turning mypy on without it catches almost nothing on a
codebase that has no annotations yet, and the "we have type checking" claim becomes
false.

## Quality gate after changes

```bash
ruff check . && black --check . && mypy src/ && pytest -q
```

Run it before reporting a task done. `pytest -q` alone is not enough — a type error
that mypy would catch usually survives a green test run.

## Pitfalls worth naming

**N+1 queries.** Iterating a queryset and touching a related object issues one query
per row. `select_related('category')` for FK/one-to-one (SQL JOIN),
`prefetch_related('orders__items')` for reverse/many-to-many (second query + join in
Python). Watch for this in serializers too — a `SerializerMethodField` that walks a
relation reintroduces N+1 that the viewset's queryset had already solved.

**Read-modify-write races on counters.** `product.stock -= 1; product.save()` loses
updates whenever two requests overlap: both read the same value. Use either

```python
Product.objects.filter(id=pk, stock__gt=0).update(stock=F('stock') - 1)   # atomic in SQL
```

or `select_for_update()` inside `transaction.atomic()` when you must read the value
before deciding. `F()` is cheaper but cannot branch on the result; the row lock can.

**Loading a whole table into memory.** `list(User.objects.all())` is fine at 1k rows
and fatal at 10M. Use `.iterator(chunk_size=1000)` for one-pass processing, or
`Paginator` when you need stable page boundaries.

**Pydantic v1 idioms in a v2 project.** `orm_mode` is now `from_attributes`,
`@validator` is `@field_validator`, `.dict()` is `.model_dump()`. Check which major
version the project pins before writing models — the v1 spellings either warn or stop
working depending on the exact v2 release, and the resulting model silently does not
read ORM attributes.

**Async session leaks in FastAPI.** A `get_db` dependency must yield inside
`async with async_session() as session:` — returning a session created outside the
context manager keeps connections checked out until the pool is exhausted, which
looks like a hang under load, not like an error.

## Testing

Test DB: `sqlite+aiosqlite:///:memory:` for unit and API tests; run the migration or
`Base.metadata.create_all` in the fixture and drop it after, so tests never depend on
the order they ran in. Override the DB dependency with
`app.dependency_overrides[get_db]` and **clear it in the fixture teardown** — a
leftover override silently poisons every later test in the session.

Async tests need `pytest-asyncio` plus `@pytest.mark.asyncio`; without the marker the
coroutine is never awaited and the test passes without asserting anything.

## Deployment

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Two things are not style choices: install requirements **before** copying the source
(otherwise every code edit invalidates the dependency layer and rebuilds take minutes),
and drop to a non-root `USER` (a container escape from a root process is an escape as
root on the host).

`--reload` and bind-mounted source belong in `docker-compose.yml` for local work only;
shipping them to production means the app restarts on any file write and serves code
that is not in the image.
