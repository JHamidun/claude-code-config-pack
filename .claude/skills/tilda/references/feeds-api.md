# Tilda Feeds API — полный референс

Все запросы: `POST https://feeds.tilda.ru/submit/`
Content-Type: `application/x-www-form-urlencoded; charset=UTF-8`
Auth: session cookies от tilda.ru (после `https://tilda.cc/login/`)

Формат тела: `action=<имя>&<field>=<value>&...` (URL-encoded)
Формат ответа: `{data: <object|array|empty>, error: "" | "сообщение"}`

## posts_GetList — список постов потока

```
action=posts_GetList
feeduid=100000000001
partuid=         (пусто = все категории, или uid категории)
page=1
items=50
```

Ответ:
```json
{
  "data": {
    "page": 1,
    "items": 50,
    "total": 46,
    "totalPostInFeed": 46,
    "feedalias": "...",
    "feedType": "events",
    "projecturl": "https://example.com",
    "posts": {
      "<postuid>": {
        "title": "...",
        "badge": "",
        "date": "2025-04-26 12:00",
        "published": "",
        "views": 0,
        "likes": 0,
        "pinned": false,
        "active": "y" | ""
      },
      ...
    }
  },
  "error": ""
}
```

**`posts` — объект, не массив.** Итерируй через `Object.entries(resp.data.posts)`.
Это краткий список — нет descr/image/url. Чтобы получить полные данные конкретного поста — используй `posts_Get`.

## posts_Get — полные данные поста

```
action=posts_Get
postuid=l2sv7pzxj1
```

Ответ содержит все поля: title, descr, date, url, tags, image, mediadata, text, textoriginal, alias, parts, customFields и т.д.

## posts_Add — создать пост

**Внимание: принимает ТОЛЬКО три поля.** Остальные данные — через `posts_Edit` после создания.

```
action=posts_Add
title=Название поста        (обязательно, иначе ошибка)
feeduid=100000000001        (обязательно)
partuid=                    (пусто или uid категории)
```

Ответ:
```json
{"data": {"uid": "0f2cyd8tk1", "title": "Название поста"}, "error": ""}
```

Сразу после `posts_Add` пост невидимый (`active=''`) и без обложки/описания. Делай `posts_Edit` + `posts_Active`.

## posts_Edit — редактировать пост

```
action=posts_Edit
postuid=0f2cyd8tk1
title=Заголовок
descr=Краткое описание для карточки
date=2025-04-19 12:00       (формат: YYYY-MM-DD HH:MM)
url=https://...             (внешняя ссылка/RuTube embed)
tags=Тег1, Тег2             (через запятую с пробелом)
image=https://static.tildacdn.com/.../cover.webp
mediadata=https://static.tildacdn.com/.../cover.webp   (та же что image, для thumbnail)
text=<HTML тело>            (опционально, для постов с body)
textoriginal=<plain text>   (опционально, plain версия)
alias=custom-slug           (опционально, иначе генерится из title)
```

Ответ: `{"data": {}, "error": ""}` при успехе.

**Гочи:**
- `image` И `mediadata` оба должны быть установлены — иначе обложка не отрендерится
- `descr` без HTML — для plain карточек
- В `descr` НЕ ставь inline CSS с `;` — ломает CSV import (если поле потом будет re-импортироваться)
- `date` без секунд работает (`2025-04-26 12:00`), полный формат `2025-04-26 12:00:00` тоже ок

## posts_Active — переключить видимость (TOGGLE)

```
action=posts_Active
postuid=0f2cyd8tk1
```

**Это TOGGLE, не setter.** Если был `active=''` → станет `'y'`, и наоборот.
Чтобы гарантированно опубликовать — сначала `posts_Get` или `posts_GetList`, проверь `active`, и вызывай только если нужно.

Ответ: `{"data": {"active":"y"}, "error":""}`.

## posts_Delete — удалить пост

```
action=posts_Delete
postuid=0f2cyd8tk1
```

В UI после удаления пост попадает в Корзину (можно восстановить через `posts_Restore`). Удаление окончательное только после `posts_TrashEmpty`.

## posts_Restore — восстановить из корзины

```
action=posts_Restore
postuid=0f2cyd8tk1
```

## posts_TrashEmpty — окончательно удалить корзину

```
action=posts_TrashEmpty
feeduid=100000000001
```

## posts_GetTrash — список удалённых

```
action=posts_GetTrash
feeduid=100000000001
page=1
items=50
```

## posts_Pin / posts_Unpin — закрепить пост

```
action=posts_Pin
postuid=0f2cyd8tk1
```

## posts_Reorder — изменить порядок постов

```
action=posts_Reorder
feeduid=100000000001
postuids=uid1,uid2,uid3,...    (через запятую в нужном порядке)
```

## posts_Duplicate — клонировать пост

```
action=posts_Duplicate
postuid=0f2cyd8tk1
```

Возвращает `{data: {uid: "новый_uid"}}`. Удобно когда хочешь скопировать сложный пост и поменять только заголовок/дату.

## feeds_GetList — список потоков проекта

```
action=feeds_GetList
projectid=12345678
```

Ответ:
```json
{"data":{"feeds":[
  {"uid":"100000000001","title":"МЕРОПРИЯТИЯ","feedType":"events",...},
  ...
]},"error":""}
```

## feeds_Get — настройки одного потока

```
action=feeds_Get
feeduid=100000000001
```

Возвращает полный конфиг: alias, тип, поля, кастомные поля.

## parts_GetList — список категорий внутри потока

```
action=parts_GetList
feeduid=100000000001
```

Категории (parts) — это под-разделы потока. У МЕРОПРИЯТИЯ их обычно нет. У БЛОГ могут быть.

## CSV-импорт через UI

Сам импорт — через кнопку «Импортировать из CSV» в UI. Программно запустить можно через `tFeeds_showPopup_importFromCsv()` (если страница уже открыта в Playwright):

```javascript
// Триггер popup
tFeeds_showPopup_importFromCsv();
// Затем нужно подгрузить файл через input[type=file] в popup
```

См. `csv-import.md` для деталей формата.

## Bulk operations через UI

Внутренняя функция `tFeeds_postsList_groupOperation(uids_csv, operation)`:
- `operation`: `"remove"`, `"restore"`, `"trash-empty"`, `"active-on"`, `"active-off"`, `"pin"`, `"unpin"`
- `uids_csv`: строка `"uid1,uid2,uid3"`

Прямой API-аналог для группового удаления:
```
action=posts_GroupDelete
feeduid=100000000001
postuids=uid1,uid2,uid3
```

## Capture неизвестного XHR

Если нужно узнать неизвестный action или его поля — захвати настоящий XHR:

```javascript
window.__SUBMITS = [];
const X = window.XMLHttpRequest;
const _open = X.prototype.open, _send = X.prototype.send;
X.prototype.open = function(m,u){this._u=u;this._m=m;return _open.apply(this,arguments)};
X.prototype.send = function(b){
  if(this._u && this._u.includes('/submit/'))
    window.__SUBMITS.push({url:this._u, body: typeof b==='string' ? b.slice(0,800) : '(non-string)'});
  return _send.apply(this,arguments);
};
// Триггер действия в UI
// Прочитать window.__SUBMITS
```

Это спасло задачу с 4 постами — выяснили что action называется `posts_GetList`, а не `posts_List`.

## Pages API (страницы Tilda)

Endpoint: `https://tilda.cc/api/page/?` — но это другой стек, не /submit/.
Реальные страницы редактируются через ручной UI или Tilda публичный API
(`https://tilda.cc/api/getpagefullexport/?token=...`). Здесь не описано — см. отдельный публичный API: https://help-ru.tilda.cc/api
