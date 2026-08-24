# Bitrix24 Lead Fields — что проверять и где взять состав своего портала

Стандартные поля лида одинаковы на всех порталах. Кастомные (`UF_*`) — уникальны:
их создаёт администратор конкретного портала, и ни имена, ни ID у двух порталов
не совпадают. Поэтому таблицу своих полей нельзя переписать из чужой инструкции —
её надо один раз выгрузить из API и сохранить рядом.

## Standard Lead Fields (есть везде)

| Field | Type | Description |
|-------|------|-------------|
| `ID` | int | Идентификатор лида |
| `TITLE` | string | Заголовок; при интеграции с Tilda обычно URL лендинга |
| `STATUS_ID` | string | Стадия (`NEW`, `IN_PROCESS`, `JUNK`, кастомные `UC_*`) |
| `SOURCE_ID` | string | Источник. **ID источников настраиваются на портале** — сверяй через `crm.status.list?filter[ENTITY_ID]=SOURCE` |
| `CONTACT_ID` | int | Связанный контакт — там лежат имя, почта и телефон |
| `DATE_CREATE` | datetime | Время создания; по нему фильтруешь свои тестовые лиды |
| `UTM_SOURCE` | string | UTM source (из Tilda часто приходит пустым, см. Фазу 5.5) |
| `UTM_MEDIUM` | string | UTM medium |
| `UTM_CAMPAIGN` | string | UTM campaign |
| `UTM_CONTENT` | string | UTM content |
| `UTM_TERM` | string | UTM term |
| `COMMENTS` | string | Комментарий; может быть `None` — перед срезом делай `(x or '')[:200]` |

## Как выгрузить UF-поля своего портала

```python
import os, sys, json, urllib.request
sys.stdout.reconfigure(encoding='utf-8')

BASE = f"{os.environ['BITRIX_BASE_URL'].rstrip('/')}/{os.environ['BITRIX_WEBHOOK_PATH'].strip('/')}"

fields = json.loads(urllib.request.urlopen(f"{BASE}/crm.lead.fields.json").read())["result"]
for code, meta in sorted(fields.items()):
    if code.startswith("UF_"):
        print(code, "|", meta.get("type"), "|", meta.get("formLabel") or meta.get("title"))
        # у enumeration список допустимых значений с ID лежит здесь:
        for item in meta.get("items") or []:
            print("    ", item["ID"], "=", item["VALUE"])
```

Вывод и есть твоя таблица соответствия. Сохрани её в свой проект — навык её не знает
и знать не может.

## Шаблон: заполни под свой портал

| Поле | Тип | Что означает | Значения (ID = подпись) |
|---|---|---|---|
| `UF_...` | enumeration | [что за вопрос в форме] | `0000` = [вариант 1], `0000` = [вариант 2] |
| `UF_...` | string | [свободный текст] | — |
| `UF_...` | array[enum] | [множественный выбор — чекбоксы] | `0000` = …, `0000` = … |
| `UF_...` | string | Google Click ID | требует маппинга в коннекторе Tilda |
| `UF_...` | string | Yandex Metrika UID | требует интеграции с Метрикой |
| `UF_...` | string | название формы Tilda | приходит из заголовка формы |

## Гоча: ID статусов переиспользуют

Названия стадий меняют, а строковый `STATUS_ID` остаётся прежним. Один и тот же
`UC_XXXXXX` через полгода может означать другую стадию воронки — и отчёт, построенный
по сохранённой таблице, будет уверенно неправильным.

Правило: **имена стадий всегда из живого ответа API**, не из файла:

```
crm.status.list.json?filter[ENTITY_ID]=STATUS
```

То же касается источников (`ENTITY_ID=SOURCE`) и типов контактов.

## Гоча: множественный выбор приходит массивом

Чекбоксы Tilda склеивает в одно скрытое поле через запятую, а Битрикс24 раскладывает
их в массив ID: `UF_SOME_MULTI: [2336, 2337]`. При сверке сравнивай множества,
а не строки — порядок элементов не гарантирован.
