---
name: claude-api
description: "Anthropic Claude API (ANTHROPIC_API_KEY) из Python: text, vision, tool use, streaming. Триггеры: «claude api». БЕЗ ключа → claude-cli-runner."
---

# Claude API — из Python по ключу

Оплата идёт по токенам, поэтому решай в первую очередь, нужен ли вообще API:
подписка Claude Code делает то же самое **бесплатно** через CLI — навык `claude-cli-runner`.
API берут, когда нужен ключ в чужом окружении (сервер, CI, бот) или программный batch.

## Ключ и модели

Ключ читается через `os.getenv('ANTHROPIC_API_KEY')` — и никогда не хардкодится в коде:
захардкоженный ключ уезжает в репозиторий вместе с файлом.

Своего файла ключей в паке нет — он твой. Заведи один раз:

```bash
cp ~/.claude/templates/.credentials.master.env.example ~/.claude/.credentials.master.env
# впиши ANTHROPIC_API_KEY=... (ключ берётся на console.anthropic.com)
```

`.credentials.master.env` уже в `.gitignore` пака — не коммить его и не класть в архив.
Вариант без файла: обычная переменная окружения `ANTHROPIC_API_KEY` — код её увидит так же.

```bash
pip install anthropic
```

```python
from anthropic import Anthropic
import os
client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
```

| Модель | ID | Под что | Контекст |
|--------|-----|---------|----------|
| Opus 5 | `claude-opus-5` | сложный reasoning, research | 1M |
| Sonnet 5 | `claude-sonnet-5` | баланс качество/цена | 200K |
| Haiku 4.5 | `claude-haiku-4-5-20251001` | быстро и дёшево | 200K |
| Fable 5 | `claude-fable-5` | text-субагенты | 200K |

ID устаревают быстрее, чем этот файл: **канон → `config/models.md`**, сверяйся там перед запуском.

<!-- no-key-block -->
## Ключа нет — что тогда

**Это нормальный случай, а не поломка.** Ключ `ANTHROPIC_API_KEY` оплачивается
отдельно от подписки Claude Code, и большинству он не нужен:

- **навык `claude-cli-runner`** делает то же самое через уже оплаченную подписку —
  бесплатно, тем же набором моделей. Дефолт для всего, что запускается на своей машине;
- ключ берут, когда код исполняется **в чужом окружении** (сервер, CI, бот) или нужен
  Batch API.

Без ключа `Anthropic(api_key=None)` падает так:
`anthropic.AuthenticationError` либо `TypeError: Could not resolve authentication method`.
Ни то ни другое не подсказывает «возьми CLI вместо API» — поэтому решай до кода.

## Что ломается, если не знать

- **`max_tokens` обязателен в каждом запросе.** Без него запрос падает — это не «разумный дефолт», а требуемое поле.
- **Ответ — список блоков.** `message.content[0].text` работает только для чистого текстового ответа. Как только включены tools или thinking, первым блоком может оказаться `tool_use`/`thinking` — перебирай `content` по `block.type`.
- **Vision берёт PNG, JPEG, GIF, WebP; PDF идёт другим типом блока** (`document`, не `image`).
- **Схема инструмента — `input_schema`**, а не `parameters` как в OpenAI SDK. Перенос кода один-в-один даст ошибку валидации.
- **Batch API — минус 50% цены**, но обработка до 24 часов. Для интерактива не годится, для массовых прогонов (разметка, переводы, оценки) — дефолт.
- **Extended thinking**: `max_tokens` должен быть заметно больше `budget_tokens`, иначе бюджет съест ответ.

## Минимальный вызов

```python
msg = client.messages.create(
    model="claude-sonnet-5",
    max_tokens=4096,
    system="You are a helpful assistant.",
    messages=[{"role": "user", "content": prompt}],
)
msg.content[0].text
```

Многоходовый диалог — история целиком в `messages` при каждом вызове (API без состояния):
`[{"role":"user",...},{"role":"assistant",...},{"role":"user",...}]`.

## Цены (2025, $/1M токенов)

| Модель | Input | Output |
|--------|-------|--------|
| Opus 5 | $15 | $75 |
| Sonnet 5 | $3 | $15 |
| Haiku 4.5 | $0.25 | $1.25 |
| Batch API | −50% | −50% |

## Справочник

`references/recipes.md` — vision, PDF, tool use, extended thinking, batch, computer use,
web search, streaming, таблица эндпоинтов. Открывай, когда нужен режим сложнее обычного
`messages.create`: там точные имена типов блоков и версионные строки тулов
(`computer_20250124` и подобные), которые не угадываются.
