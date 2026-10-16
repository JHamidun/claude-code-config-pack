---
name: claude-api
description: "Claude API из Python по ключу ANTHROPIC_API_KEY: vision, tool use, batch. Триггеры: «claude api», «anthropic sdk». БЕЗ ключа → claude-cli-runner; n8n-эндпоинт → agent-api-server."
---

# Claude API — из Python по ключу

Оплата идёт по токенам, поэтому решай в первую очередь, нужен ли вообще API:
подписка Claude Code делает то же самое **бесплатно** через CLI — навык `claude-cli-runner`.
API берут, когда нужен ключ в чужом окружении (сервер, CI, бот) или программный batch.

## Что выбрать

| | CLI по подписке | API по ключу |
|---|---|---|
| Авторизация | встроенная в Claude Code, ключ не нужен | `ANTHROPIC_API_KEY` |
| Цена вызова | 0 — входит в подписку | по токенам, деньги со счёта |
| Умеет | text, JSON, streaming, system prompt | ещё vision/PDF, tool use, адаптивное мышление (`thinking` + `effort`), Batch API |
| Где живёт | своя машина и сервер, где залогинен CLI | любой сервер с ключом |

**Дефолт для своих скриптов и воркеров — CLI:** он не тратит деньги и не требует раздавать ключ.
Ключ берут, когда без него никак: автономный бот на чужом сервере, картинки/PDF на вход,
tool use, массовый прогон через Batch.

## Модели

Выбирай класс под задачу, а точный ID бери из `config/models.md`: ID устаревают быстрее,
чем этот файл. Там же перечислены Legacy-замены и снятые ID (вызов с ними вернёт ошибку).

| Класс | Под что |
|-------|---------|
| Opus | сложный reasoning, research |
| Sonnet | баланс качество/цена — дефолт для большинства задач |
| Haiku | быстро и дёшево: классификация, массовая разметка |
| Fable | text-субагенты (канон воркеров) |

В примерах ниже и в `references/recipes.md` ID спрятан в переменной `MODEL`:

```python
MODEL = "<ID из config/models.md>"   # класс Sonnet подходит для большинства задач
```

## Путь 1. CLI по подписке (без ключа)

Модуль `~/.claude/tools/claude_cli.py`; короткая шпаргалка — навык `claude-cli-runner`.

```python
import os, sys
sys.path.insert(0, os.path.expanduser("~/.claude/tools"))
from claude_cli import claude, claude_json, claude_stream

answer = claude("Fix spelling: Привет мр", system="You are a proofreader", model=MODEL)
data = claude_json("List 3 colors as JSON array", model=MODEL)   # уже разобранный dict
for chunk in claude_stream("Write a story", model=MODEL):         # streaming
    print(chunk, end="")
```

Есть ещё `claude_async` и `validate_response` — сигнатуры в самом модуле.

- **`model=` передавай явно:** дефолт модуля может отставать от текущего поколения.
- **`max_tokens` в CLI-режиме принимается и игнорируется** — у CLI нет такого флага;
  длину ответа ограничивай словами в промпте.
- **Требования:** CLI установлен (`npm install -g @anthropic-ai/claude-code`) либо путь к бинарю
  лежит в переменной `CLAUDE_CLI_PATH`. На сервере проверь `ssh your-server "which claude"`
  и живую авторизацию `ssh your-server "claude -p 'Hello'"`; логин на headless-сервере — навык
  `claude-server-auth`.

### Гард рекурсии

Модуль считает вложенность через переменную окружения `CLAUDE_CLI_DEPTH` и по умолчанию пускает
ровно один уровень (`CLAUDE_CLI_MAX_DEPTH=1`): попытка уйти глубже роняет `RecursionGuardError`
вместо запуска процесса. Причина: вызов `claude()` изнутри сессии Claude Code порождает дочерний CLI,
а тот при том же коде порождает следующий — без счётчика это не ошибка, а лавина процессов,
которая молча съедает машину. Осознанный лишний уровень разрешается точечно:
`allow_nested=True` или `CLAUDE_CLI_MAX_DEPTH=2`.

## Путь 2. API по ключу

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

Минимальный вызов:

```python
msg = client.messages.create(
    model=MODEL,
    max_tokens=4096,
    system="You are a helpful assistant.",
    messages=[{"role": "user", "content": prompt}],
)
msg.content[0].text
```

Многоходовый диалог — история целиком в `messages` при каждом вызове (API без состояния):
`[{"role":"user",...},{"role":"assistant",...},{"role":"user",...}]`.

<!-- no-key-block -->
## Ключа нет — что тогда

**Это нормальный случай, а не поломка.** Ключ `ANTHROPIC_API_KEY` оплачивается
отдельно от подписки Claude Code, и большинству он не нужен:

- **CLI по подписке** (Путь 1 выше, навык `claude-cli-runner`) делает то же самое через
  уже оплаченную подписку — бесплатно, тем же набором моделей. Дефолт для всего, что
  запускается на своей машине;
- ключ берут, когда код исполняется **в чужом окружении** (сервер, CI, бот) или нужен
  Batch API.

Без ключа `Anthropic(api_key=None)` падает так:
`anthropic.AuthenticationError` либо `TypeError: Could not resolve authentication method`.
Ни то ни другое не подсказывает «возьми CLI вместо API» — поэтому решай до кода.

## Что ломается, если не знать

- **`max_tokens` обязателен в каждом запросе.** Без него запрос падает — это не «разумный дефолт», а требуемое поле.
- **Новый токенизатор у Sonnet 5 и Opus 5:** тот же текст даёт примерно на 30% больше токенов, и лимиты `max_tokens`, подобранные под прошлое поколение (4.6), начнут обрезать ответ — пересчитай.
- **Ответ — список блоков.** `message.content[0].text` работает только для чистого текстового ответа. Как только включены tools или thinking, первым блоком может оказаться `tool_use`/`thinking` — перебирай `content` по `block.type`.
- **Vision берёт PNG, JPEG, GIF, WebP; PDF идёт другим типом блока** (`document`, не `image`).
- **Схема инструмента — `input_schema`**, а не `parameters` как в OpenAI SDK. Перенос кода один-в-один даст ошибку валидации.
- **Batch API — минус 50% цены**, но обработка до 24 часов. Для интерактива не годится, для массовых прогонов (разметка, переводы, оценки) — дефолт.
- **Мышление задаётся `thinking={"type": "adaptive"}` + `effort`** (`low`/`medium`/`high`/`xhigh`/`max`). Старая ручная форма снята: `budget_tokens` и `thinking={"type":"enabled"}` на Claude 4.7+ возвращают **400**. Отключать мышление (`{"type":"disabled"}`) можно только при effort ≤ high и не на Fable 5.1. `effort` управляет объёмом размышления, а не длиной видимого ответа — краткость просить словами.

## Цены

Абсолютные цены ($ за миллион токенов) меняются от поколения к поколению и здесь не дублируются:
смотри страницу Pricing в документации Anthropic. Устойчивое правило одно — **Batch API даёт
скидку 50%** на input и output.

## Справочник

`references/recipes.md` — vision, PDF, tool use, extended thinking, batch, computer use,
web search, streaming, таблица эндпоинтов. Открывай, когда нужен режим сложнее обычного
`messages.create`: там точные имена типов блоков и версионные строки тулов
(`computer_20250124` и подобные), которые не угадываются.

Свежие детали API (новые параметры, версии тулов) — через context7:
`python ~/.claude/tools/context7_docs.py search anthropic`.

## Не этим навыком

- Поднять OpenAI-совместимый HTTP-эндпоинт для n8n/IDE → `agent-api-server`.
- Сравнить ответы Claude, GPT и Gemini между собой → `multi-model-gateway`.
