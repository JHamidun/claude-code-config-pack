# Claude API — рецепты с неочевидной формой запроса

Читать, когда нужен режим сложнее обычного `messages.create`: vision, PDF, tools,
batch, computer use, extended thinking. Здесь только то, что не угадывается —
точные имена типов блоков, версионные строки тулов и форма ответа.

## Vision

Картинка — отдельный блок `image` перед текстовым, `media_type` обязателен и должен
совпадать с реальным форматом файла (по расширению верить нельзя, если файл пришёл извне).

```python
import base64

with open(path, "rb") as f:
    data = base64.standard_b64encode(f.read()).decode("utf-8")

client.messages.create(
    model=MODEL, max_tokens=1024,
    messages=[{"role": "user", "content": [
        {"type": "image",
         "source": {"type": "base64", "media_type": "image/png", "data": data}},
        {"type": "text", "text": prompt},
    ]}],
)
```

## PDF

Тот же приём, но тип блока — `document`, а не `image`; `media_type` — `application/pdf`.

```python
{"type": "document",
 "source": {"type": "base64", "media_type": "application/pdf", "data": pdf_b64}}
```

## Tool use

Схема инструмента — JSON Schema в поле `input_schema` (не `parameters`, как в OpenAI).
Ответ приходит блоками: вызов инструмента лежит в блоке с `type == "tool_use"`,
и он не обязательно первый — перебирай `message.content`, а не бери `[0]`.

```python
weather_tool = {
    "name": "get_weather",
    "description": "Get weather for a location",
    "input_schema": {
        "type": "object",
        "properties": {"location": {"type": "string", "description": "City name"}},
        "required": ["location"],
    },
}

msg = client.messages.create(model=MODEL, max_tokens=1024,
                             tools=[weather_tool],
                             messages=[{"role": "user", "content": prompt}])
for block in msg.content:
    if block.type == "tool_use":
        block.name, block.input, block.id   # результат вернуть в следующем сообщении
```

## Extended thinking

Ответ содержит блоки двух типов: `thinking` и `text`. `max_tokens` должен быть заметно
больше `budget_tokens`, иначе на сам ответ места не остаётся.

```python
resp = client.messages.create(
    model=MODEL, max_tokens=16000,
    thinking={"type": "enabled", "budget_tokens": 10000},
    messages=[{"role": "user", "content": prompt}],
)
thinking = next((b.thinking for b in resp.content if b.type == "thinking"), None)
answer   = next((b.text     for b in resp.content if b.type == "text"), None)
```

## Batch API (скидка 50%)

Каждый запрос обёрнут в `{"custom_id": ..., "params": {...}}`, где `params` — обычное тело
`messages.create`. Обработка идёт до 24 часов, результат забирается отдельным вызовом
после `processing_status == "ended"`.

```python
batch = client.messages.batches.create(requests=[
    {"custom_id": f"request-{i}",
     "params": {"model": MODEL, "max_tokens": 1024,
                "messages": [{"role": "user", "content": req}]}}
    for i, req in enumerate(requests)
])

b = client.messages.batches.retrieve(batch.id)
if b.processing_status == "ended":
    for r in client.messages.batches.results(batch.id):
        r.custom_id, r.result.message.content[0].text
```

## Computer use

Тулы задаются версионными строками — их не угадать, сверяй с доками при обновлении:

```python
tools=[
    {"type": "computer_20250124", "name": "computer",
     "display_width_px": 1920, "display_height_px": 1080},
    {"type": "text_editor_20250124", "name": "str_replace_editor"},
    {"type": "bash_20250124", "name": "bash"},
]
```

Модель возвращает действия (клик, скриншот, ввод) — исполнять их и возвращать результат
обязан твой код: сам API экраном не управляет.

## Server-side web search

```python
tools=[{"type": "web_search", "name": "web_search"}]
```

Поиск выполняется на стороне сервера Anthropic — локальной реализации инструмента не нужно.

## Streaming

```python
with client.messages.stream(model=MODEL, max_tokens=4096,
                            messages=[{"role": "user", "content": prompt}]) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

## Эндпоинты

| Эндпоинт | Назначение |
|---|---|
| `messages.create` | генерация |
| `messages.stream` | стриминг |
| `messages.batches.create` | батч (−50%) |
| `messages.count_tokens` | подсчёт токенов до отправки |
| `completions.create` | легаси, для нового кода не использовать |
