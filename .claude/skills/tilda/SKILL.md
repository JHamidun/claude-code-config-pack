---
name: tilda
description: "Tilda через внутренний API: потоки (Feeds), посты, страницы, SEO/og, обложки CDN, T123. Триггеры: «тильда», «не то превью в телеграме»."
---

# Tilda — управление сайтом через API

> Внутренний (не публичный) API Tilda для проектов, потоков (Feeds), постов, страниц и блоков.
> Собран реверс-инжинирингом `sendRequest` / `td__ajax`.

> ⚠️ **Это внутренний API. Tilda его не документирует, не поддерживает и не обязана
> сохранять.** Он может измениться без предупреждения в любой день — тогда часть рецептов
> ниже перестанет работать, и это не поломка навыка. Публичный API Tilda
> (<https://help.tilda.cc/api>) умеет только чтение и на порядок беднее; всё, что здесь
> написано, существует потому, что через публичный этого не сделать.
> Для боевых процессов держи ручной запасной путь через UI.

## Что тебе понадобится

| Что | Зачем | Где взять |
|---|---|---|
| Свой аккаунт Tilda | всё остальное | tilda.cc — на платном тарифе; Feeds есть не на всех |
| `TILDA_EMAIL` / `TILDA_PASSWORD` в окружении | логин для сессионных вызовов | свои же учётные данные |
| `TILDA_PUBLIC_KEY` / `TILDA_UPLOAD_KEY` | загрузка файлов на Tilda CDN | Настройки проекта → API |
| Playwright | половина API работает только из залогиненной вкладки | `pip install playwright && playwright install chromium` |
| `requests` | HTTP-часть клиента `scripts/tilda_feeds.py` | `pip install requests` |

Ключи кладутся в переменные окружения или в свой `~/.claude/.credentials.master.env`
(образец — `~/.claude/templates/.credentials.master.env.example`). В репозиторий — никогда.

## Когда использовать

- Создание/редактирование/удаление постов в потоках (МЕРОПРИЯТИЯ, БЛОГ, МАТЕРИАЛЫ)
- Массовое обновление карточек (обложки, описания, даты, теги, ссылки) — за минуты вместо часов в UI
- Изменение настроек блоков на страницах (например `input1` Feed-блока — лимит постов)
- CSV-импорт постов
- Загрузка обложек на Tilda CDN
- Публикация страниц
- Авторизация и поддержание сессии для всего вышеперечисленного

## ⚠️ Главные принципы (выученное на ошибках)

1. **Используй прямой `fetch('/submit/')` через urlencoded, а не `sendRequest`** — `sendRequest` через MCP Playwright виснет на 30+ сек, теряет контекст.
2. **`posts_Add` принимает ТОЛЬКО `{title, feeduid, partuid}`** — возвращает новый `uid`. Остальные поля заполняются отдельным `posts_Edit`.
3. **Имя API — `posts_GetList`, не `posts_List`.** `posts_Delete`, не `posts_Remove`.
4. **`posts_Active` — toggle, не setter.** Хочешь установить `active=y` → проверь текущее состояние и вызывай только если выключено.
5. **Список постов возвращается как OBJECT keyed by uid**, не массив. `Object.entries(resp.data.posts)`.
6. **Body — `application/x-www-form-urlencoded`**, не FormData. FormData возвращает «Неизвестная ошибка при отправке запроса».
7. **CSV-импорт: запрещены `;` в текстовых полях** — Tilda CSV parser ломается. Заменяй `,` или удаляй.
8. **Tilda CDN не принимает PDF** — используй Yandex Disk для документов.
9. **Inline CSS с `;` в `descr` — ломает CSV import. Делай без inline-стилей или замени `;` → `,` после строки.**
10. **PostUid — короткий ID типа `l2sv7pzxj1`**, генерируется сервером.
11. **`image` И `mediadata` ОБА должны быть установлены** — иначе обложка не отрендерится в карточке.
12. **Лимит постов на странице — поле `input1` Feed-блока (тип 897)**. Если на сайте видно 3 поста из 42 активных — это `input1=3`.
13. **`posts_Edit` БЕЗ поля `title` обнуляет заголовок!** Возвращает `error: "Post title is empty"` либо тихо ставит пустоту. ВСЕГДА передавай `title` в каждый `posts_Edit`, даже если только обложку меняешь. Поведение: Tilda трактует отсутствие поля как пустую строку, не как «не трогать». Это касается ВСЕХ полей — `posts_Edit` это не PATCH с partial update, это PUT всего поста.
14. **`posts_Edit` СБРАСЫВАЕТ `parts` и `active`** если их не передать. Перед каждым Edit делай `posts_Get`, забирай `p.parts` и явно передавай `parts: p.parts`, `active: 'y'`. Иначе пост пропадёт из правильной категории МЕДИА/БЛОГ и станет неактивным. См. troubleshooting «posts_Edit обнулил parts/active».
15. **API возвращает `descr`/`title` HTML-encoded на transport уровне** (`«` → `&laquo;`). Это **не баг**, это transport encoding. Render на сайте показывает `«` корректно. Двойное `&amp;laquo;` в API response — вот это **баг**: значит фактически stored `&laquo;` literal, страница показывает `&laquo;` text. Decoder через `textarea.innerHTML → .value` итеративно. См. troubleshooting «иероглифы в descr».
16. **FormData работает для `/submit/`** — это противоречит старой записи в скилле. В апреле 2026 проверено: `new FormData()` принимается для `posts_Get`, `posts_Edit`, `posts_Active`, `posts_GetList`. URLSearchParams тоже работает. **Что НЕ работает: `feeds_Publish`** — возвращает «Неизвестная ошибка», но изменения и так автопубликуются если `active=y`.
17. **Поле `text` для тела поста — это JSON-массив блоков**: `text=JSON.stringify([{ty:'html', co:'<HTML>'}])`. На API возврате всё HTML-encoded для transport. Нельзя оставлять `text` пустым — иначе reading time на странице будет «1 минута», даже если карточка большая. Tilda поддерживает несколько `ty` блоков (см. ниже секцию «Block types»). **Правильный выбор: используй `text` (не `html`)** — Tilda тогда применяет нативные стили `t-redactor__text`, `t-redactor__h2`, `t-redactor__quote`. С `html` стили не работают, текст рендерится без форматирования.
18. **Поле `mediatype` обязательно** для image-постов: `mediatype=image`. Без него обложка может не отрендериться корректно даже при заполненных `image` + `mediadata`.
19. **`feeds.tilda.ru/submit/` отвечает RELOGIN из Python `requests.Session` с куками от Playwright** — даже если PHPSESSID для feeds.tilda.ru есть. Решение: делай fetch ИЗНУТРИ страницы `feeds.tilda.ru/posts/?feeduid=...` через `page.evaluate()` с `credentials:'include'`. Same-origin запрос работает, Python session — нет. См. `references/auth.md` секцию «Handshake-цепочка».
20. **Чтобы попасть на `feeds.tilda.ru/posts/?feeduid=...` после логина, нужна handshake-цепочка** (порядок важен): `tilda.cc/login/` → `tilda.cc/projects/projectinfo/?projectid=X` → `tilda.cc/projects/manage/?projectid=X` → **`tilda.cc/page/?pageid=Y&projectid=X`** (любой реальный pageid проекта) → `feeds.tilda.ru/feeds/?projectid=X` → `feeds.tilda.ru/posts/?feeduid=Z&projectid=X`. Без шага через page editor feeds.tilda.ru редиректит обратно на `tilda.ru/projects/`. Подтверждено 2026-04-25 на webinar covers v6.
21. **Substring matching webinar→post иногда промахивается** на small differences (тире vs длинное тире, пробелы, кавычки, `(не)` vs `(не )`). Подготовь hardcoded `OVERRIDES = {slug: postuid, ...}` map для известных пар, чтобы не зависеть от fuzzy matching. Особенно важно перед массовым PUT — иначе обновишь не тот пост.
22. **CSS `content: var(--xxx)` в HTML-шаблонах для рендера обложек** — удобный паттерн для batch-генерации SVG/PNG из одного template. Для каждого slug подставляй CSS-переменные через regex replace в `:root`. Безопаснее чем string interpolation в HTML (не нужен XSS escape), но требует `replace('"', '\\"')` для кавычек внутри значений. Пример в `webinar_assets/render_covers_v6.py`.
23. **🚨 `posts_Get` НЕ возвращает поле `active`** — только `posts_GetList` отдаёт его. Если ты копируешь поля из `posts_Get` в `posts_Edit` payload, поле `active` будет отсутствовать → Tilda молча сбросит в `""` → пост невидим на сайте. **Всегда дополнительно вызывай `posts_GetList` чтобы получить `active` и `parts`**, ИЛИ используй готовый helper `safe_in_page_edit(page, feeduid, postuid, **updates)` из `scripts/tilda_feeds.py`. **Этот баг повторно случился 2026-04-25 на 46 постах МЕРОПРИЯТИЯ** — потому что предыдущий троублешут запомнил «передавай active», но не объяснил что `posts_Get` его НЕ возвращает. После применения обложек ВСЕГДА проверяй что `active` count не уменьшился: `sum(p.get('active')=='y' for p in posts_GetList().data.posts.values())`.
24. **🚨 `posts_GetList` НЕ возвращает поля `image`/`mediadata`/`descr`/`text`** — только `posts_Get` возвращает реальные значения. Это значит проверка типа `p.get('image')` через `posts_GetList` даёт false negative — выглядит будто image не установлен, хотя он есть. **Чтобы проверить реальное состояние post после edit — вызывай `posts_Get` для конкретного uid.** Симметрично #23: `posts_Get` без `active`/`parts`, `posts_GetList` без `image`/`descr`/`text`/`mediadata`. Полная картина = оба эндпоинта вместе. Verified 2026-04-26.
25. **T123 Custom HTML блоки (`data-record-type="131"`) — отдельный мир.** Рендерятся как `<div id="rec<recordid>">` с произвольным HTML/CSS/JS внутри. Используются когда нужен кастомный дизайн которого нет в стандартных Tilda-блоках. Поля настроек: `code` (HTML тело), `body_html` (доп. блок), `css` (стили), `js` (скрипты). Сохраняются через `comm=saverecord` на `/page/submit/` с `recordid=<rec>`, `pageid=<pageid>`, `<field>=<value>`. **`onlythisfield` не обязательное** — можно слать сразу несколько полей, главное `comm=saverecord`.
26. **🚨 ACE editor в T123 НЕ автосинхронизируется с `<textarea name="code">`** — если правишь HTML через `editor.setValue(...)`, перед save надо вручную обновить textarea: `document.querySelector('textarea[name="code"]').value = editor.getValue()`. Иначе `saverecord` отправит старое содержимое. Verified 2026-04-29 на example.com /workshop SEO fix.
27. **Большие HTML (>2KB) ломают `evaluate_script` если передавать одной строкой.** Решение — chunked upload через base64 + atob + TextDecoder UTF-8: разбей HTML на куски по ~2KB, помести в массив строк, на странице сделай `atob(chunks.join(''))` → `new TextDecoder('utf-8').decode(bytes)` → `editor.setValue(decoded)`. Альтернатива — залить HTML на свой сервер и `fetch()` оттуда (CORS должен быть `*`). Проверено на 24 КБ карусели.
28. **Программное создание T123 блока:** `window.tp__addRecord(131, '<after_recid>', null)` — создаёт новый блок типа 131 после указанного recid. Возвращает Promise с новым recordid. Полезно когда нужно добавить блок ниже существующего без UI.
29. **`<script type="application/ld+json">` напрямую в `code` Tilda T123 валидируется DOMParser-ом и может корраптить closing tag.** Обход: вместо raw `<script>` вставляй JS который через `document.createElement('script')` + `JSON.stringify(schemas)` создаёт элемент рантаймом. Tilda DOMParser не трогает строковые JSON-литералы внутри JS-кода. Verified 2026-04-29 на example.com (4 JSON-LD schemas).
30. **🚨 Pattern: T123 shim + payload SVG на CDN — для гигантских страниц (100KB+ HTML).** Вместо запихивания всего в `code` (где есть лимит и DOMParser-валидация) используй: (а) HTML wrap as base64 inside `<svg><text id="payload">...</text></svg>` → upload на Tilda CDN; (б) в T123 `code` вставь shim ~3.7KB который фетчит payload SVG → atob → инжектит в `<div id="th-mount">`. Bonus: bootstrap-вариант — T123 загружает `<script src="https://your-server.example.com/runner.js">`, runner.js (на твоём сервере) знает payload URL, и обновления контента не требуют re-publish в Tilda. Проверено на лендинге 116 КБ и блоге 134 КБ.
31. **🚨 Tilda CDN отвергает mp4/mp3 для некоторых проектов** (проверено на проекте, созданном через tilda.ru). Workaround: храни видео/аудио на собственном сервере (`/var/www/your-site/media/`, `/media/audio/`) и линкуй абсолютным URL. Аудио обёрнутое в mp4-контейнер с fake video тоже отвергается.
32. **Tilda CDN upload требует `Origin: https://tilda.ru` + `Referer: https://tilda.ru/`** для проектов созданных через tilda.ru (не tilda.cc). Без этих хедеров — 403/JS error. Старый skill говорил «Origin: https://feeds.tilda.ru» — это работает для основного проекта (старый проект), но НЕ для новых проектов. Если 403 — попробуй оба варианта.
33. **🟢 `saverecord` для T123 РАБОТАЕТ — корректный набор полей** (проверено на боевом проекте): `comm=saverecord` + `pageid` + `projectid` + `recordid` + `code=<full_html>`. **БЕЗ `onlythisfield`** — этот параметр работает для стандартных Tilda-блоков (типа `input1` Feed-блока 897), но для T123 ломает запись. Server отвечает plain text `OK` (2 байта), не JSON. Verify через повторный GET `/page/edit/` с тем же recordid → проверь `data.record.code`. После save → `/page/publish/` (отдаёт JSON с link/wslink). Пример рабочего payload:
```js
await fetch('/page/submit/', {
  method:'POST', credentials:'include',
  headers:{'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8'},
  body: new URLSearchParams({
    comm:'saverecord', pageid, projectid, recordid,
    code: newHtml,  // FULL HTML, без onlythisfield
  }).toString(),
});  // → "OK"
```
**ВАЖНО про чтение текущего code:** API `/page/edit/` (POST с `pageid+projectid+recordid`) возвращает JSON `{record: {code, tplid, ...}, tpl}`. Поле `record.code` **HTML-encoded** (как `&lt;style&gt;`) — декодируй через `textarea.innerHTML → .value` перед обработкой. Никогда не отправляй назад HTML-encoded версию — Tilda её удвоит.
34. **Custom domain через A-record на Tilda IP `176.57.66.20`.** HTTPS provisioning через Let's Encrypt занимает ~24h после смены DNS. Без HTTPS — `https://your-domain.ru` отдаёт чужой сертификат (соседний клиент Tilda на том же IP). Проверка: `curl -I https://your-domain.ru` должен вернуть `Server: TildaSN`.
35. **`<projectsubdomain>.tilda.ws` — публичный preview.** Например `one-warm-saury.tilda.ws` — Tilda выдаёт случайное трёхсловное имя. Если изменения видны на preview но не на custom domain — это CDN cache (5-15 мин). Если НЕ видны даже на preview — `saverecord` не отработал, см. п.33.
36. **🚨 SEO / og / title страницы редактируются ТОЛЬКО через Page Settings, НЕ через saverecord.** Открой форму из списка страниц проекта: `td__showform__EditPageSettings('<pageid>')` (вызывать со вкладки `tilda.ru/projects/?projectid=X`, НЕ из page-editor) → появляется попап с inputs по `name`: `title`, `descr`, `meta_title`, `meta_descr`, `meta_keywords`, `fb_title`, `fb_descr`, `fb_img` (og:image, URL-строка), `link_canonical`, `nosearch`, `meta_nofollow`. Меняешь `.value` нужных → клик `input.js-ps-popup-submit` (текст «Сохранить изменения») → `comm=savepagesettings` уходит сам. Потом `/page/publish/` чтобы применилось. **Title в `<title>` живёт ЗДЕСЬ, не в T123-коде.** Verified 2026-06-11 (techpred школа: title/fb_descr/meta_descr).
37. **🚨 Чекбоксы Page Settings читать через `.checked`, НЕ `.value`.** У `<input type=checkbox name=nosearch>` атрибут `value` всегда `"on"` независимо от состояния — поэтому дамп формы по `.value` даёт ЛОЖНУЮ тревогу «noindex включён». Реальное состояние = `el.checked`. `nosearch=on` (checked) = страница закрыта от поиска, `meta_nofollow=on` = nofollow. Снять = `if(el.checked) el.click()`. Verified 2026-06-11 (ложная noindex-паника на школе).
38. **🚨 og/twitter/canonical НИКОГДА не клади в project-head — только в Page Settings конкретной страницы.** Project-head (`tilda.ru/projects/editheadcode/?projectid=X` → `textarea[name="headcode"]`) — ОБЩИЙ `<head>`-код для ВСЕХ страниц проекта, и он идёт в `<head>` раньше page-level тегов. Скрейперы (Telegram, FB) берут ПЕРВЫЙ встреченный og-тег → если в project-head лежит og:title/og:url/twitter:title одной из страниц, ВСЕ остальные страницы шарят её превью. Хуже того, `<link rel=canonical>` в project-head делает все страницы «каноникой» одной — прямой SEO-вред. **Правило: в project-head только verification-меты, og:locale, общие схемы; всё страничное (og:title/description/image, twitter:*, canonical) — в Page Settings.** Правка project-head: меняешь textarea + синхронишь ACE (`ace.edit(document.querySelector('.ace_editor')).setValue(v,-1)`) → клик `.js-btn-save` → republish страниц. Verified 2026-06-11 (превью школы показывало конференцию).
39. **🚨 После смены og — сбрось кэш Telegram-превью через @WebpageBot.** Telegram кэширует превью ссылки и сам не обновляет даже после правки og. Отправь URL боту @WebpageBot (руками или Telethon) → ответ «Link previews was updated successfully». Слать обе формы (https и http), если домен пока на http. Без этого новый баннер/заголовок в превью не появится. Verified многократно (aimipt, школа).
40. **🚨 Заливка большого/полного-документа T123 через S3, а не localhost.** Для HTML 50KB+ (целая страница в одном T123): залей файл в любое S3-совместимое хранилище (boto3, свои креды в переменных окружения, `ACL=public-read`, ContentType `text/html`) → в браузере (вкладка tilda.ru, залогинен) `fetch(s3_url)` → `saverecord`. **НЕ через `http://127.0.0.1`** — Chrome PNA (Private Network Access) блокирует fetch с localhost из https-страницы НАМЕРТВО, даже с заголовком `Access-Control-Allow-Private-Network`. S3-хранилище в нужной юрисдикции даёт правильный CORS и MIME из коробки. (Свой сервер — тоже вариант, но S3 надёжнее.) Проверено.
41. **🚨 Кросс-доменный POST к tilda.ru работает ТОЛЬКО со вкладки на домене tilda.ru.** `fetch('https://tilda.ru/page/submit/', {credentials:'include'})` со вкладки `techpred.online` или любого чужого домена → `Failed to fetch` (CORS + куки не уходят). Перед saverecord/publish/page-settings навигируй вкладку на `tilda.ru/projects/?projectid=X`. Verified 2026-06-11.
42. **🚨 Длинные fetch-цепочки в одном `evaluate` таймаутят протокол DevTools (~30 c).** saverecord полного документа + publish + verify в одном `evaluate_script` → `Runtime.callFunctionOn timed out`, хотя запрос на сервере прошёл. Паттерн: положи результат в `window.__x = 'PENDING'`, запусти fetch без await (`.then(t => window.__x = t)`), верни сразу `'STARTED'`; следующим коротким `evaluate` опрашивай `window.__x` в цикле. (Родственно fire-and-forget `window.BG`, но именно из-за protocol-timeout, а не длины цикла.)
43. **Tilda отдаёт 403 на `curl` с query-string** (`?cb=...`) — бот-защита. Live-страницу после правок проверяй ТОЛЬКО из браузера (chrome-devtools `navigate` + читать сырой HTML через `fetch` с той же вкладки), не через curl. Без query-string curl обычно проходит, но кэш не сбивается.
44. **`.t123 a` link-bleed: дефолтный оранжевый цвет ссылок Tilda бьёт твою вёрстку.** Внутри T123 Tilda применяет свой `.t-text a {color: #ff8562}` к ссылкам без явного цвета (ghost-кнопки на тёмном фоне особенно). Фикс: `.t123 a{color:inherit !important} .t123 a span{color:inherit !important}`, а цветным ссылкам (footer-dim, tg-blue) дай бОльшую специфичность `.t123 .footer__col a{color:... !important}`.

## Endpoint и формат

```
POST https://feeds.tilda.ru/submit/        # Posts/Feeds API
POST https://tilda.cc/page/edit/           # Get block settings
POST https://tilda.cc/page/submit/         # Save block field
POST https://tilda.cc/page/publish/        # Publish page

Content-Type: application/x-www-form-urlencoded; charset=UTF-8
Cookie: <сессия после логина на tilda.cc/login/>
```

Тело: `action=<имя>&<field>=<value>&...` (URL-encoded).
Ответ Feeds API: `{data: {...}|[], error: "" | "сообщение"}`.

## Быстрый старт (Python)

```python
from skills.tilda.scripts.tilda_feeds import TildaFeedsClient, TildaCDN, TildaPageEditor

# Получи cookies через ручной логин или Playwright export
COOKIES = {'tildauid': '...', 'PHPSESSID': '...'}

client = TildaFeedsClient(COOKIES)
posts = client.list_posts('100000000001')  # data.posts — Object keyed by uid

# Создать + заполнить + активировать
new = client.add_post('100000000001', 'Заголовок поста')
uid = new['data']['uid']
client.edit_post(uid, title='...', descr='...', date='2025-04-26 12:00',
                 url='https://...', image='https://static.tildacdn.com/...webp',
                 mediadata='https://static.tildacdn.com/...webp', tags='AI, Воркшоп')
client.ensure_active(uid, '100000000001')  # idempotent (НЕ toggle)

# Загрузить обложку на CDN (без авторизации)
cdn = TildaCDN()  # ключи берутся из окружения: TILDA_PUBLIC_KEY / TILDA_UPLOAD_KEY
url = cdn.upload('cover.webp')

# Изменить настройки блока на странице (например, лимит Feed-блока)
page = TildaPageEditor(COOKIES)
page.save_field(pageid='70000004', recordid='1000000001', field='input1', value='50')
page.publish('70000004', '12345678')  # → опубликует страницу
```

## Быстрый старт (JavaScript / Playwright)

```javascript
// На открытой https://feeds.tilda.ru/posts/?feeduid=100000000001
const t = new TildaFeed('100000000001');
const posts = await t.list({items: 500});  // Object keyed by uid

const uid = await t.add('Заголовок');
await t.edit(uid, {descr:'...', date:'2025-04-26 12:00', image:'...', mediadata:'...'});
await t.ensureActive(uid);

// Bulk обновление обложек по нормализованному title
await t.bulkSetCovers({
  'воркшоп иитрансформация в компании': 'https://static.tildacdn.com/...webp',
  // ...
});
```

## Структура

| Файл | Содержит |
|------|----------|
| `references/feeds-api.md` | Все API actions: posts_Get/GetList/Add/Edit/Active/Delete/Restore/Pin/Reorder/Duplicate, feeds_GetList/Get, parts_GetList |
| `references/text-blocks.md` | **Block types для `text` поля** (text/heading/quote/br/html), готовые рецепты форматирования (TOC, embeds, цветные коробки, стат-карточки, footer-паттерн), типичные ошибки |
| `references/pages-api.md` | Pages API: чтение/правка настроек блоков (input1 для лимита Feed-блока 897), saverecord, publish |
| `references/cdn-upload.md` | Tilda CDN: endpoint, ключи, формат файлов, Python пример, ограничения |
| `references/csv-import.md` | CSV формат: разделители, escape, известные колонки, гочи |
| `references/auth.md` | Логин, cookies, домены tilda.cc/tilda.ru, капча, Python session |
| `references/troubleshooting.md` | Типичные проблемы и решения (лимит постов, кривой импорт, MCP виснет, неактивные после Active) |
| `scripts/tilda_feeds.py` | Python клиент: TildaFeedsClient, TildaCDN, TildaPageEditor — все CRUD + bulk helpers |
| `scripts/browser_helper.js` | JS классы для DevTools/Playwright: TildaFeed, TildaPage, captureSubmits + fire-and-forget pattern |

## Свои ID: где взять

Все числовые идентификаторы ниже — **твои**, они видны в URL и в ответах API.
Ни один из них не «секретный», но выписать их один раз стоит: без `projectid` и `feeduid`
не работает даже handshake-цепочка авторизации.

| ID | Где увидеть |
|---|---|
| `projectid` | URL списка страниц: `tilda.ru/projects/?projectid=<...>` |
| `pageid` | открой страницу в редакторе: `tilda.cc/page/?pageid=<...>&projectid=<...>` |
| `feeduid` | `feeds.tilda.ru/feeds/?projectid=<...>` → открыть поток, `feeds.tilda.ru/posts/?feeduid=<...>` |
| `recordid` блока | в DOM редактора: `[data-record-type="897"]` → `el.id` без префикса `record` |
| `publickey` / `uploadkey` | Настройки проекта → API |
| preview-хост | `<projectsubdomain>.tilda.ws` — виден в настройках домена проекта |

Программно список потоков и страниц: `feeds_GetList` с `projectid` и
`https://tilda.ru/projects/?projectid=<...>`.

**Заведи себе табличку и держи её ВНЕ пака** (например `~/tilda-ids.md`), чтобы она не
уехала вместе с конфигом, если ты им поделишься:

```
projectid:    12345678
domain:       example.com
hostname:     myproject-dev.tilda.ws   (preview)

feeduids:
  100000000001  — БЛОГ
  100000000002  — МЕРОПРИЯТИЯ

pageids:
  70000001  — / (главная)
  70000004  — /events   (recordid 1000000001 — Feed-блок 897, поле input1)

CDN upload:
  publickey:   TILDA_PUBLIC_KEY  (env)
  uploadkey:   TILDA_UPLOAD_KEY  (env)
  endpoint:    https://upload.tildacdn.com/api/upload/
```

## Workflow для типовой задачи «обновить N постов»

1. Открыть `https://feeds.tilda.ru/posts/?feeduid=<feeduid>` в Playwright (сессия должна быть залогинена)
2. В одном `browser_evaluate` блоке:
   - `fetch /submit/ posts_GetList` → найти uid целевых постов
   - Для каждого: `fetch /submit/ posts_Edit` с полями
   - Если нужны новые посты: `posts_Add` → `posts_Edit` для дозаполнения
   - `posts_Active` для тех у кого `active=''`
3. Финальный `posts_GetList` для верификации

**Не делай N отдельных `browser_evaluate` вызовов** — каждый вход через MCP стоит ~3-5 сек overhead. Лучше один большой `evaluate` с циклом внутри.

Для длинных циклов (50+ постов) — fire-and-forget с `window.BG`:
```javascript
window.BG = {step:'init', results:[]};
(async () => { /* долгий цикл */ window.BG.step='done'; })();
return {kicked:true};  // вернётся мгновенно
// Потом отдельно: return window.BG;
```

## Workflow «изменить лимит постов на странице»

```javascript
// 1. Открой редактор страницы
// https://tilda.cc/page/?pageid=<pageid>&projectid=<projectid>

// 2. Найди recordid Feed-блока (тип 897)
const blocks = [...document.querySelectorAll('[data-record-type="897"]')]
  .map(el => el.id.replace(/^record/, ''));

// 3. Сохрани новое значение input1 (количество постов)
await fetch('/page/submit/', {
  method:'POST',
  headers:{'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8'},
  body: new URLSearchParams({
    comm:'saverecord', pageid:'70000004', recordid: blocks[0],
    onlythisfield:'input1', input1:'50',
  }).toString(),
  credentials:'include',
});

// 4. Опубликуй страницу
await fetch('/page/publish/', {
  method:'POST',
  headers:{'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8'},
  body: new URLSearchParams({pageid:'70000004', projectid:'12345678'}).toString(),
  credentials:'include',
});
// Изменения видны на проде через 1-5 минут (CDN кэш)
```

## Antipatterns (никогда так не делай)

- ❌ `sendRequest('posts_List', ...)` через `browser_evaluate` — виснет, неправильное имя
- ❌ `FormData` для `/submit/` — сервер не парсит
- ❌ `posts_Add` с полями данных — игнорирует всё кроме title/feeduid/partuid
- ❌ Inline CSS с `;` в descr — ломает CSV import при следующем импорте
- ❌ Загрузка PDF на Tilda CDN — отклоняется
- ❌ Множественные мелкие `evaluate` вместо одного большого блока
- ❌ Игнорирование `error` в ответе — Tilda пишет туда читаемый русский текст
- ❌ `posts_Active` без проверки текущего состояния — это TOGGLE
- ❌ Установка только `image` без `mediadata` — обложка не отрисуется в карточке
- ❌ Изменение `input1` без последующего publish — изменения не попадут на прод

## Разборы реальных случаев

### 1. Создание 4 постов в Feed МЕРОПРИЯТИЯ (2026-04-25)
**Симптом:** `posts_Add` через `sendRequest` создал 3 пустых "Основы методологии Agile" + ошибка на 4-м.
**Причина:** posts_Add не принимает данные. + sendRequest колбэки виснут в MCP.
**Решение:** repurpose 3 broken через posts_Edit (заполнение полями) + 1 новый через add+edit. Через прямой fetch /submit/ urlencoded. Все 4 за 2 секунды.
**Файл:** `webinar_assets/tilda_meropriyatiya_4new.json`

### 2. На /events видно 3 поста из 42 активных (2026-04-25)
**Симптом:** в Feed 42 активных поста, на сайте только 3 верхних.
**Причина:** `input1=3` в Feed-блоке 897 на странице /events.
**Решение:** один POST `/page/submit/ saverecord input1=50` + один POST `/page/publish/`. 5 секунд.

### 3. CSV-импорт сломал 16 постов (предыдущая сессия)
**Симптом:** posts с пустыми title и кашей в date/mediadata после CSV import.
**Причина:** inline CSS с `;` (`text-align:center;margin:30px`) в `Description` — Tilda CSV parser сплитнул по `;`.
**Решение:** восстановление 16 постов через `posts_Edit` каждого uid вручную. Урок: всегда replace `;` → `,` перед CSV.

### 4. БЛОГ — 127 постов с двойным экранированием entities (2026-04-25)
**Симптом:** На карточках БЛОГа на сайте видны literal `&amp;amp;mdash;`, `&amp;amp;quot;` вместо `—`, `"`. На API возврате `descr` содержит `&amp;amp;mdash;`.
**Причина:** Цикл `posts_Get → posts_Edit` без декодирования накапливал уровни HTML-encoding. Каждый раунд: `&` → `&amp;` при сохранении.
**Решение:** итеративный decode через `textarea.innerHTML → .value` до стабильности (≤5 проходов), потом resave с actual chars. Tilda на сохранение не encode actual `«»—`, а на API-возврат снова encode для transport — это норма.

```javascript
const decode = (s) => { const ta = document.createElement('textarea'); ta.innerHTML = s; return ta.value; };
const decodeAll = (s) => {
  let prev = s, curr = decode(s);
  let g = 0;
  while (prev !== curr && g++ < 5) { prev = curr; curr = decode(curr); }
  return curr;
};
```

**Truncation gotcha:** Tilda обрезает descr на ~250 chars. Если обрезка пришлась на середину entity, остаётся фрагмент `&amp;am…`. После decodeAll получаем `&am…` — невалидный entity, на странице видится как text. Дополнительный regex для хвоста:

```javascript
const stripBrokenTail = (s) => s.replace(/\s*&[^;\s]*…?\s*$/, '…');
```

127/127 постов починены за один скан + 2 broken-tail прохода. Финальный скан: 0 с `&amp;amp;`.

### 5. МЕДИА — даты карточек не совпадают с постерами (2026-04-25)
**Симптом:** На постере прямого эфира видна дата «9 февраля, 20:00 МСК», в Tilda карточка показывает 22.02.2024.
**Причина:** Поле `date` ставилось от балды/импорта, не из источника.
**Решение:** проверка дат по оригинальным источникам, batch posts_Edit с правильными `date` (формат `YYYY-MM-DD HH:MM`):
- **Ведомости/Коммерсантъ/РБК статьи** → `curl + grep '"datePublished":"[^"]*"'` из source HTML
- **VK видео** → `fetch('/al_video.php?act=show&al=1&module=videofeed&video=-{group_id}_{video_id}', {credentials:'include'})` на vkvideo.ru, ищи `"date":<unix_ts>` в response
- **RuTube** → `https://rutube.ru/api/video/{vid}/?format=json` → `created_ts`
- **Постеры прямых эфиров** — текст на изображении («9 февраля, 20:00 МСК») — самый надёжный источник для in-house контента

### 6. МЕДИА body posts_Edit обнулил parts/active (2026-04-25)
**Симптом:** `posts_Edit` с новым `text` прошёл (`error:''`), но карточка пропала из категории «Упоминания в СМИ» и стала неактивной.
**Причина:** не передал `parts` и `active=y` → Tilda обнулил оба.
**Решение:** перед каждым posts_Edit делать posts_Get, забирать `p.parts`, явно передавать. Потом отдельный `posts_Active` с `active=y` для надёжности (на случай если Tilda всё равно сбросил).

```javascript
const p = (await sub('posts_Get', {postuid, feeduid, projectid})).data;
await sub('posts_Edit', {
  postuid, feeduid, projectid,
  title: p.title, descr: p.descr,
  text: JSON.stringify([{ty:'html', co: newHtml}]),
  mediatype: p.mediatype || 'image',
  image: p.image, thumb: p.thumb || p.image, mediadata: p.mediadata || p.image,
  parts: p.parts || '146561154411',  // КРИТИЧНО — иначе категория сбросится
  active: 'y',
  date: p.date,
  // прочие опциональные: imagealt, postalias, authorname, directlink
});
await sub('posts_Active', {postuid, feeduid, projectid, active:'y'});  // double-insure
```

### 7. Большое HTML-тело (5-7K chars) для МЕДИА-дайджеста (2026-04-25)
**Кейс:** надо вставить полноценную выжимку статьи как `text` поста. Inline в `browser_evaluate` — function body раздувается, могут быть проблемы с экранированием.
**Решение:** залить `body.html` на свой сервер (любой хост, отдающий статику с CORS), fetch из admin-сессии:

```javascript
const html = await (await fetch('https://your-server.example.com/articles/body.html')).text();
await sub('posts_Edit', {postuid, ..., text: JSON.stringify([{ty:'html', co: html}])});
```

Nginx alias `/portal/` уже отдаёт static с `Access-Control-Allow-Origin: *` — fetch из feeds.tilda.ru проходит. Это удобнее чем вкладывать длинные строки в evaluate-функцию.

### 8a. Миграция Next.js-сайта на Tilda через T123 shim + SVG payload
**Кейс:** перенос landing 17 секций (~116KB HTML) и blog SPA с 201 статьёй (134KB HTML) на Tilda без переписывания в нативные блоки.

**Архитектура:**
1. Сборка финального HTML на стороне (Next.js export → одна single-file страница)
2. Wrap в SVG: `<svg xmlns="http://www.w3.org/2000/svg"><text id="payload" style="display:none">BASE64_ENCODED_HTML</text></svg>`
3. Upload SVG на Tilda CDN → получаешь `tild<hex>/file.svg` URL (149KB landing, 146KB blog)
4. В T123 блоке `code` — шим ~3.7KB который:
   - `fetch(PAYLOAD_URL)` → достаёт base64 из `<text id="payload">`
   - `atob()` → `TextDecoder('utf-8').decode()`
   - `document.body.innerHTML = decoded` (или injects в `<div id="th-mount">`)
   - Вытаскивает `<script>` теги отдельно через `new Function()` — innerHTML не выполняет inline scripts

**Bonus pattern (bootstrap):** вместо хардкода `__PAYLOAD_URL__` в T123 шиме — пусть T123 загружает `<script src="https://your-server.example.com/tilda/blog-runner.js">`, а `blog-runner.js` (на твоём nginx с `no-cache` header) знает payload URL. Тогда обновления = scp нового JS на свой сервер, без re-publish в Tilda.

**T123 IDs того проекта (пример структуры):**
- Landing: pageid `138379196`, T123 recordid `2220451661`
- Blog: pageid `138390926` (slug=blog), T123 recordid `2220572931`

**Проблема (Phase I, 2026-05-01):** `saverecord` для этих T123 тихо не пишет в БД (см. принцип #33). Live остался на старом payload, требуется ручной save через ACE editor.

**Headers для CDN upload (иначе, чем для проектов с tilda.cc):**
```python
# Для проекта, созданного через tilda.ru (а не tilda.cc):
publickey = 'uiyejbdskjfiowe32'
# uploadkey — JWT, может expire, бери свежий из Tildaupload_UPLOADKEY на странице редактора
headers = {'Origin': 'https://tilda.ru', 'Referer': 'https://tilda.ru/'}
```

### 8b. feeds_Publish не работает (2026-04-25)
**Симптом:** `posts_Edit` + `posts_Active` прошли, но при попытке `feeds_Publish` возвращается `{error:"Неизвестная ошибка при отправке запроса"}`.
**Причина:** неизвестна, action либо не существует, либо требует другой endpoint.
**Решение:** не звать `feeds_Publish` вообще. Изменения автопубликуются в feed-блоках на сайте сразу как `active=y`. Verify через `curl https://<твой-домен>/blog/tpost/{postuid}-...` через 5-10 сек после Edit.

## Альтернатива: Tilda публичный API (read-only)

Для бэкапа страниц или экспорта структуры:
```
GET https://api.tildacc.com/v1/getprojectslist/?publickey=&secretkey=
GET https://api.tildacc.com/v1/getpagefullexport/?publickey=&secretkey=&pageid=
```
Документация: https://help-ru.tilda.cc/api

**Не позволяет редактировать** — только читать. Для редактирования всегда используй внутренний API через сессию tilda.cc.
