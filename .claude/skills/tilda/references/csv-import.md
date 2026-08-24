# Tilda CSV-импорт постов

> Для bulk-создания/обновления постов в Feed без API. Полезен когда постов 50+.

## Trigger UI попап

```javascript
// На странице feeds.tilda.ru/posts/?feeduid=...
tFeeds_showPopup_importFromCsv();
```

Откроется модальное окно с input для CSV-файла.

## Формат CSV

- **Разделитель полей:** `;` (точка с запятой)
- **Кавычки:** `"` (двойные)
- **Escape кавычек внутри значения:** `\"` (а не `""` как в стандартном CSV!)
- **Перенос строк в значении:** допускается внутри `"..."`
- **Кодировка:** UTF-8 (с BOM или без)
- **Конец строки:** `\n` или `\r\n`

## Колонки (стандартный набор)

| Колонка | Описание | Пример |
|---------|----------|--------|
| `Post ID` | uid поста (для update); пусто = новый | `l2sv7pzxj1` |
| `Title` | заголовок | `Воркшоп по ИИ` |
| `Description` | описание для карточки | `Краткое описание...` |
| `Date` | дата | `2025-04-26 12:00` |
| `Cover Image` | URL обложки | `https://static.tildacdn.com/...webp` |
| `Cover Image Description` | альт-текст | `Обложка вебинара` |
| `URL` | внешняя ссылка/embed | `https://rutube.ru/video/...` |
| `Tags` | теги через запятую | `AI, Воркшоп` |
| `Category` | категория (partuid title) | `Запись вебинара` |
| `Active` | `1` / `0` — видимость | `1` |
| `Pinned` | `0` / `1` — закреплён | `0` |
| `Body` | HTML-тело поста (для длинных постов) | `<p>Текст</p>` |

Названия колонок берутся из шапки первой строки CSV. Tilda сама детектирует и сопоставляет по русским и английским вариантам.

## КРИТИЧЕСКИЕ ГОЧИ

### 1. Никаких `;` в текстовых полях

`;` — разделитель полей. Если он встретится в `Description`, `Tags` или `Body` — Tilda СЛОМАЕТСЯ, поля разъедутся в соседние колонки.

```python
# Перед записью в CSV:
descr = descr.replace(';', ',')
body = body.replace(';', ',')
tags = tags.replace(';', ', ')
```

**Разбор из практики:** inline CSS `text-align:center;margin:30px` в `Description` сломал импорт → 16 постов с пустыми заголовками и кашей в датах.

### 2. Не используй стандартный csv.QUOTE_ALL с doublequote=True

Tilda НЕ парсит `""` как escape для `"`. Нужно `\"`:

```python
import csv

with open('feed.csv', 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(
        f,
        delimiter=';',
        quotechar='"',
        doublequote=False,    # ← НЕ удваивай кавычки
        escapechar='\\',      # ← Используй backslash
    )
    w.writerow(['Post ID', 'Title', 'Description', ...])
    for p in posts:
        w.writerow([p['uid'], p['title'], p['descr'], ...])
```

### 3. CSV не обновляет, а ДУБЛИРУЕТ посты

Tilda CSV import обычно создаёт НОВЫЕ записи с новыми uid даже если в `Post ID` указан существующий uid. Поведение зависит от настроек импорта в попапе.

**Проверка:** перед массовым импортом сделай тест на 1-2 постах. Если создались дубли — удали старые через `posts_GroupOperation`:
```javascript
const broken = ['uid1','uid2','uid3'];
tFeeds_postsList_groupOperation(broken.join(','), 'remove');
```

### 4. Заголовки колонок чувствительны к точному написанию

`Title` и `title` — разные. `Cover Image` и `Image` — разные. Если попап импорта спрашивает «куда смапить колонку X» — значит её название не распозналось. Используй EXPORT существующего фида (`tFeeds_export(feeduid)`) как шаблон.

### 5. Mediadata vs Cover Image

Tilda иногда требует ОБЕ колонки одновременно:
- `Cover Image` — отображается на сайте
- `Cover Image Description` — alt-text

Если хочешь обложку которая работает в карточке Feed-блока, в feed-постах И в OG-метатегах — заполняй `Cover Image` URL-ом из CDN (см. `cdn-upload.md`).

## Пример Python генерации CSV

```python
import csv
from pathlib import Path

posts = [
    {'uid':'', 'title':'Воркшоп: ИИ', 'descr':'Описание', 'date':'2025-04-26 12:00',
     'image':'https://static.tildacdn.com/...webp',
     'url':'https://rutube.ru/video/abc/', 'tags':'AI, Воркшоп',
     'category':'Запись вебинара', 'active':'1'},
    # ...
]

def clean(s: str) -> str:
    return (s or '').replace(';', ',').replace('\r','').replace('\n', ' ')

with open('events.csv', 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f, delimiter=';', quotechar='"', doublequote=False, escapechar='\\')
    w.writerow(['Post ID','Title','Description','Date','Cover Image',
                'URL','Tags','Category','Active'])
    for p in posts:
        w.writerow([
            p['uid'],
            clean(p['title']),
            clean(p['descr']),
            p['date'],
            p['image'],
            p['url'],
            clean(p['tags']),
            clean(p['category']),
            p['active'],
        ])
```

## Когда CSV vs API

**CSV-импорт:** удобен для:
- Первоначальной заливки 50+ постов
- Однотипных bulk-операций без сложной логики
- Передачи редактору файла на правки в Excel

**API (`posts_Add` + `posts_Edit`):** обязателен для:
- Точечных правок (1-10 постов)
- Обновления существующих (CSV дублирует)
- Когда нужна верификация что каждый пост создался успешно
- Скриптов с условной логикой
- Не теряем uid после операции

**Гибрид:** генерируешь CSV → импортируешь → берёшь созданные uid через `posts_GetList` → делаешь финальные правки через `posts_Edit`.

## Export существующего фида

```javascript
// На странице feeds.tilda.ru/posts/?feeduid=100000000001
tFeeds_export('100000000001');
// Скачается CSV со всеми постами в правильной структуре
```

Используй этот файл как шаблон для своих импортов — гарантировано все колонки в правильном порядке и с правильными именами.
