# Tilda Pages API — редактирование настроек блоков и публикация

> Эндпоинты для редактирования страниц и блоков. Работают на домене `tilda.cc` (или `tilda.ru`) после логина.

## Открыть редактор страницы

```
GET https://tilda.cc/page/?pageid=<pageid>&projectid=<projectid>
```

После загрузки в `window` доступны функции:
- `tp__record__getRecordElement(recordid)` — DOM элемент блока
- `edrec__editRecordSettings(recordid)` — открыть UI настройки блока
- `tp__saveOnlyOneFieldInRecord(recordid, fieldName, fieldName, value)` — сохранить одно поле
- `tp__pagePublish()` — открыть UI публикации

## Получить настройки блока (record)

```
POST https://tilda.cc/page/edit/
Content-Type: application/x-www-form-urlencoded

comm=editrecordsettings
pageid=<pageid>
recordid=<recordid>
tab=settings
```

Ответ — JSON с полем `record` содержащим все настройки блока:
```json
{
  "record": {
    "id": "1000000001",
    "pageid": "70000004",
    "tplid": "897",          // тип блока (897 = Feed Posts)
    "input1": "3",            // <-- количество постов на странице
    "blocks": "3",            // количество колонок
    "balign": "center",
    "imgratio": "16_9",
    "title_typo": "{...}",    // typography JSON-encoded
    ...
  }
}
```

## Сохранить одно поле блока

```
POST https://tilda.cc/page/submit/
Content-Type: application/x-www-form-urlencoded

comm=saverecord
pageid=<pageid>
recordid=<recordid>
onlythisfield=<fieldName>
<fieldName>=<value>
```

Ответ: `OK` (plain text) при успехе.

Пример: установить лимит постов на странице Feed-блока.
```
comm=saverecord&pageid=70000004&recordid=1000000001&onlythisfield=input1&input1=50
```

## Опубликовать страницу

```
POST https://tilda.cc/page/publish/
Content-Type: application/x-www-form-urlencoded

pageid=<pageid>
projectid=<projectid>
```

Ответ:
```json
{
  "projectid": "12345678",
  "customdomain": "example.com",
  "publishonepage": "yes",
  "pageid": "70000004",
  "linkstr": "https://example.com/events",
  "link": "https://example.com/events",
  "wslink": "https://myproject-dev.tilda.ws/events"
}
```

После этого правки видны на проде по `link`.

## Поиск блока на странице через DOM

```javascript
// На открытой странице редактора:
document.querySelectorAll('[data-record-type]').forEach(el => {
  console.log(el.id, el.getAttribute('data-record-type'), el.innerText.slice(0,80));
});
```

Типы блоков (`data-record-type`):
- `396` — заголовок (Cover/Title block)
- `897` — Feeds Posts Grid (с фильтрами «Все/Актуальные/Прошедшие»)
- `123` — Hero block
- `124` — text block
- `156` — image block
- `T848` — другая разновидность Feed-листинга
- `BF704` — карусель Feed-постов
- См. полный каталог в Tilda Block Library

## Известные поля Feed-блока 897 (на примере страницы /events)

| Поле | Значение | Что делает |
|------|----------|------------|
| `tplid` | `897` | тип блока |
| `input1` | `3 / 6 / 12 / 50` | **количество постов на странице** |
| `blocks` | `3` | колонок в гриде |
| `balign` | `center` | выравнивание блока |
| `dateformat` | `4` | формат даты (1..6 разные локализации) |
| `feed_partpos` | `i` | где показывать категорию |
| `feed_datepos` | `i` | где показывать дату |
| `feed_pp_imgpos` | `bt` | положение картинки в попапе поста |
| `imgratio` | `16_9` / `1_1` / `4_3` | соотношение сторон обложки |
| `img_borderradius` | `20px` | скругление углов карточки |
| `feed_sortrelevants` | `random / date_desc` | как сортировать «Актуальные» |
| `vindentpx` | `10px` | вертикальные отступы |
| `checkbox3..8` | `on` / off | разные включатели (показывать дату, описание, переход и т.д.) |
| `menu_active_textcolor` | `#ffffff` | цвет активной табы |
| `menu_active_itembg` | `#2d2fe8` | фон активной табы |
| `title_typo` | JSON | типографика заголовка |
| `descr_typo` | JSON | типографика описания |
| `popupimg_borderradius` | `20px` | скругление картинки в попапе |

**Важно:** `input1` — главный параметр для отображения каталога. Если стоит `3` — пользователь видит только 3 поста независимо от того сколько активных в фиде. По умолчанию у Tilda обычно `6` или `12`.

## Типичная задача: «увеличить лимит постов на странице»

```javascript
// 1. Найти recordid Feed-блока (тип 897 или подобный)
// 2. Сохранить новое значение
const params = new URLSearchParams({
  comm: 'saverecord',
  pageid: '70000004',
  recordid: '1000000001',
  onlythisfield: 'input1',
  input1: '50',  // или 100, или сколько нужно
});
await fetch('/page/submit/', {
  method:'POST',
  headers:{'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8'},
  body: params.toString(),
  credentials:'include',
});
// Ответ "OK"

// 3. Опубликовать
await fetch('/page/publish/', {
  method:'POST',
  headers:{'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8'},
  body: new URLSearchParams({pageid:'70000004', projectid:'12345678'}).toString(),
  credentials:'include',
});
```

## Pagination в Feed-блоке

В блоке 897 есть встроенная пагинация. Если `input1=12`, а в фиде 50 активных постов — пользователь видит 12 + кнопку «Показать ещё». Если хочешь показать ВСЕ сразу без пагинации — ставь `input1` в большее число чем количество постов в фиде.

## Список всех блоков на странице

```javascript
// На открытой странице редактора:
const all = [...document.querySelectorAll('[data-record-type]')];
const blocks = all.map(el => ({
  recordid: el.id.replace(/^record/, ''),
  tplid: el.getAttribute('data-record-type'),
  preview: (el.innerText||'').slice(0, 60).replace(/\n/g,' '),
}));
console.table(blocks);
```

## Пример таблицы pageids проекта (projectid=12345678)

| pageid | URL | Title |
|--------|-----|-------|
| 70000001 | / (главная) | заголовок главной |
| 70000002 | /materials | Бесплатные материалы |
| 70000003 | /request | Заявка на персональную консультацию |
| 70000004 | /events | Мероприятия |
| 70000005 | /blog (template) | Шаблон поста БЛОГ |

Свой полный список — `https://tilda.ru/projects/?projectid=<твой projectid>`.

## Сохранить несколько полей одновременно

`saverecord` поддерживает только одно поле через `onlythisfield`. Для нескольких — по очереди:

```javascript
async function saveField(recordid, field, value, pageid='70000004') {
  const body = new URLSearchParams({
    comm:'saverecord', pageid, recordid,
    onlythisfield: field, [field]: value,
  }).toString();
  return (await fetch('/page/submit/', {
    method:'POST',
    headers:{'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8'},
    body, credentials:'include',
  })).text();
}

await saveField('1000000001', 'input1', '50');
await saveField('1000000001', 'blocks', '3');
await saveField('1000000001', 'feed_sortrelevants', 'date_desc');
```

## Cross-page block copy — Fish library (НЕТ native «Скопировать на другую страницу»)

В Tilda Studio **нет** UI «Copy to another page». В контекст-меню блока (`getContextMenuConfig`) есть только: Копировать (clipboard same-page), Вставить, Дублировать, Вырезать, **«Добавить блок в библиотеку»**. Cross-page перенос делается через project-wide Fish library.

```javascript
// 1. На SOURCE странице (editor) — добавить блок в библиотеку.
//    ВАЖНО: должен быть открыт editor нужной source-страницы (window.pageid = SOURCE).
const recEl = document.getElementById('record<SOURCE_REC>');
const fullhtml = `<html>${document.head.outerHTML}<body><div id="allrecords" class="t-records">${recEl.outerHTML}</div></body></html>`;
await fetch('/page/submit/', {method:'POST', credentials:'include',
  headers:{'content-type':'application/x-www-form-urlencoded'},
  body: new URLSearchParams({
    comm:'library_addfish',
    pageid: String(window.pageid),
    recordid: '<SOURCE_REC>',
    title: 'Имя блока в библиотеке',
    fullhtml
  })});

// 2. Получить fish_id из списка
const fishes = await (await fetch('/page/submit/', {method:'POST', credentials:'include',
  headers:{'content-type':'application/x-www-form-urlencoded'},
  body: new URLSearchParams({comm:'library_getfishes', pageid: String(window.pageid)})})).json();
const fish_id = fishes.find(f => f.title === 'Имя блока в библиотеке').id;

// 3. На DESTINATION странице (editor) — вставить fish после конкретного блока
const r = await fetch('/page/submit/', {method:'POST', credentials:'include',
  headers:{'content-type':'application/x-www-form-urlencoded'},
  body: new URLSearchParams({
    comm:'addfishrecord',
    pageid: String(window.pageid),
    afterid: '<EXISTING_REC_TO_INSERT_AFTER>',  // или beforeid:'<X>'
    fishid: fish_id,
    with_code: 'yes'
  })});
// Response html содержит recordid="<NEW_REC>"
```

Также есть `copyrecord_tobuf` / `pasterecord_frombuf` (server-side per-user buffer), но **они тоже ограничены тем же набором данных, что и fish**.

## ⚠️ T396 Zero Block cross-page paste — НЕ переносит content molecules

**Подвох:** для T396 (Zero Block) `library_addfish` + `addfishrecord` копирует record metadata, артборд, CSS-скоупинг — но **molecule-content** (тексты/картинки внутри карточек) хранится отдельно и привязан к page_id. После вставки на новую страницу Zero Block рендерит **default-content из source HTML**, а не визуальный результат с source страницы.

**Кейс из практики:** на странице блок «Кейсы» (`rec1000000002`) в source-HTML содержит один набор логотипов, а визуально показывает совсем другой — потому что рядом на той же странице живёт T123 polish (`rec1000000004`) с JS, который при `DOMContentLoaded` делает `querySelector('.tn-elem__...').textContent = ...`, подменяя текст и `background-image` логотипов. Source-HTML при этом врёт: то, что видит человек, собирается уже в браузере.

После переноса `rec1000000002` на главную через fish получаем default-контент из source-HTML. Polish T123 (`rec1000000004`), если его не перенести и не перепривязать к новому rec id, не сработает.

**Правильный pattern**:
1. Перенести Zero Block (rec1000000002) через fish → получить новый recid `Y_zero` на destination
2. Перенести polish T123 (`rec1000000004`) через fish → получить новый recid `Y_polish`
3. На destination — **сразу после publish/save** изменить JS в polish: заменить все ссылки `#rec<ORIGINAL>` → `#rec<Y_zero>` в селекторах. Селекторы класса `.tn-elem__<recid><molecule_id>` строятся как конкатенация, при копировании molecule_id **СОХРАНЯЕТСЯ**, меняется только префикс recid. Достаточно `code.replace(/<ORIGINAL_REC>/g, '<Y_zero>')`.
4. `saverecord` patch'нутого polish в `code` field rec `Y_polish`.

**Альтернатива (хуже)**: T123 iframe на HTML, лежащем на своём сервере, с postMessage auto-resize. Работает, но плохо: внешняя зависимость, latency, и в Tilda такой блок уже не редактируется.

## T123 size limit

`code` field в T123 **отвергает payloads >25KB** ошибкой `"Error. Too much data in code"`. Для длинного контента — минимизируй (выкини нерелевантные replacements из polish-скриптов). 6-8KB заведомо проходит.

## Удалить запись (block)

```
POST https://tilda.cc/page/submit/
comm=deleterecord&pageid=<PAGEID>&recordid=<RECID>
```
Ответ: `OK`. Также есть `library_delfish` (удалить fish из библиотеки): `comm=library_delfish&fishid=<ID>&pageid=<ANY>`.

## Альтернатива: Tilda публичный API (read-only export)

Для read-only задач (бэкап страниц, миграция) есть официальный API:
```
GET https://api.tildacc.com/v1/getprojectslist/?publickey=&secretkey=
GET https://api.tildacc.com/v1/getpagefullexport/?publickey=&secretkey=&pageid=
```

Документация: https://help-ru.tilda.cc/api

Этот API **не позволяет редактировать** — только читать. Для редактирования используй внутренний `/page/edit/` + `/page/submit/`.
