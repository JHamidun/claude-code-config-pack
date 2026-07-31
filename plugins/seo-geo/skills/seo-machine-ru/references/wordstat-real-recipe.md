# Wordstat: как реально достать частоты (проверено 2026-06)

> Боевой рецепт из задачи по YourProduct. Wordstat — единственный источник абсолютной частотности под Яндекс. Здесь три пути по убыванию надёжности и что из них СРАБОТАЛО.

## TL;DR — что работает

**Рабочий способ:** залогиненный браузер на `wordstat.yandex.ru` → дёргать internal API `POST /wordstat/api/getTable` (fetch со страницы, куки идут сами, CSRF не нужен). Один вызов = частота + расширения + ассоциации по фразе. Цикл по списку фраз снимает всё ядро за секунды.

**НЕ работает:** Direct API v4 (`api.direct.yandex.com/v4/json/`, метод `CreateNewWordstatReport`) — токен `YANDEX_OAUTH_TOKEN` (Metrika-app) принимается, но возвращает `error 58: "No access — fill out app access request in Direct interface"`. Нужен отдельный одобренный доступ к Яндекс.Директ API (заявка + ожидание). Скрипт `yandex/scripts/yandex_api.py wordstat` оставлен и **починен по кодировке** (UTF-8-body, иначе `error 501 "Request encoding is not UTF8"`), но упирается в этот доступ.

## Internal API getTable (основной путь)

Эндпоинт:
```
POST https://wordstat.yandex.ru/wordstat/api/getTable
Content-Type: application/json     (CSRF-токен НЕ требуется; куки сессии — автоматически, same-origin)
```
Тело:
```json
{
  "currentDevice": "desktop,phone,tablet",
  "dbname": "rus",
  "filters": {"region": "225", "tableType": "popular"},
  "searchValue": "агрегатор нейросетей",
  "startDate": "01.06.2024",
  "endDate": "31.05.2026"
}
```
- `region: "225"` = Россия. (Москва=213, СПб=2, и т.д.)
- `tableType: "popular"` — таблица «популярное» (фраза + её расширения, широкое соответствие). Для точной фразы используют операторы в `searchValue` («!слово», "фраза"), но для ядра «popular» достаточно.
- Период: даёт график; таблица возвращает последний месяц периода.

Ответ (главное):
```jsonc
{
  "totalValue": 4113,                      // <- ЧАСТОТА базовой фразы (показов/мес)
  "table": {"tableData": {
    "popular": [{"text":"...","value":"..."}],      // фраза + расширения с частотами
    "associations": [{"text":"...","value":"..."}]  // «что ещё искали» (для расширения ядра)
  }}
}
```

## Готовый цикл (paste в залогиненный браузер)

`browser_evaluate` (chrome-devtools или playwright), страница — любая на `wordstat.yandex.ru`:
```js
async () => {
  const phrases = ["агрегатор нейросетей","нейросети для бизнеса", /* ...весь список... */];
  const out = {};
  for (const p of phrases) {
    const r = await fetch("https://wordstat.yandex.ru/wordstat/api/getTable", {
      method:"POST", credentials:"include", headers:{"content-type":"application/json"},
      body: JSON.stringify({currentDevice:"desktop,phone,tablet", dbname:"rus",
        filters:{region:"225", tableType:"popular"}, searchValue:p,
        startDate:"01.06.2024", endDate:"31.05.2026"})
    });
    const j = await r.json();
    out[p] = j.totalValue ?? null;
    await new Promise(s=>setTimeout(s,250));   // вежливая пауза, не словить лимит
  }
  return out;
}
```
Готовый файл-сниппет: `scripts/wordstat_browser_snippet.js`. Headless-вариант на куке: `scripts/wordstat_fetch.py`.

## Логин в браузер

Креды есть в `~/.claude/.credentials.master.env`: `YANDEX_EMAIL` + `YANDEX_PASSWORD` (аккаунт `your-email@example.com`).
Поток входа (новый Яндекс ID): ввести email → «Далее» → экран пуш-кода → кнопка **«Войти с паролем»** → ввести пароль → **2FA** (пуш на устройства Яндекс ИЛИ SMS). **2FA проходит только владелец** — попросить подтвердить на телефоне или прислать 6-значный код. После входа **сессия в профиле браузера сохраняется** (persistent), повторный логин не нужен.

- Playwright MCP использует персистентный профиль `…\ms-playwright\mcp-chrome-*` — логин там переживает перезапуски (часто УЖЕ залогинен — проверяй первым делом).
- chrome-devtools MCP профиль `…\.cache\chrome-devtools-mcp\chrome-profile` — отдельный, может быть не залогинен.

## Грабля: браузерный MCP завис («already running»)

Симптом: `list_pages`/`new_page`/`navigate` → `"browser already running for <profile>, use --isolated"`. Сервер потерял связь с живым chrome.
Лечение (НЕ трогает основной Chrome пользователя — у него другой профиль):
```powershell
# найти и убить стейл-процессы нужного профиля + снять lockfile
Get-CimInstance Win32_Process -Filter "Name='chrome.exe'" |
  Where-Object { $_.CommandLine -match 'mcp-chrome|chrome-devtools-mcp' } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
Remove-Item "<profile-dir>\lockfile" -Force -ErrorAction SilentlyContinue
```
Затем повторный `new_page` поднимает свежий браузер (профиль и логин на диске сохраняются).

## Открытое расширение ядра без логина — Яндекс Suggest

`GET https://suggest.yandex.ru/suggest-ya.cgi?v=4&uil=ru&part=<запрос>` → JSON `["part",[подсказки...]]`. Даёт реальные хвосты запросов (intent-сигнал), но БЕЗ абсолютных объёмов.
**CORS:** fetch проходит только с origin `*.yandex.ru` / `dzen.ru` (с `passport.yandex.ru` и сторонних — блок). Практика: открыть `dzen.ru`, оттуда гонять fetch-цикл.

## Урок про оценочные объёмы

Тиры, выведенные из ширины suggest/«ощущения рынка», **завышают в 5–10×**. Реальные примеры (YourProduct, РФ, май 2026): оценка «нейросети для бизнеса ~18 000» → факт **2274**; «доступ к нейросетям из россии ~2 200» → факт **122**; точные B2B-фразы («оплата по счёту юр лиц», «без впн», «внедрить в компанию») = **0–3**. Категорийный head «агрегатор нейросетей» = **4113** (крупнейший). **Вывод:** всегда снимать реальный Wordstat перед приоритизацией; точные коммерческие лонг-тейлы держать как страницы под конверсию/AEO, не ждать от них трафика.

## Связки
- Чинёный клиент Direct API: `~/.claude/skills/yandex/scripts/yandex_api.py wordstat` (когда дадут доступ).
- Скоринг по реальным объёмам: `scripts/opportunity_scorer.py`.
- Упаковка ядра+статьи в Word для стейкхолдера: `scripts/build_report_docx.py`.
- Рабочий пример (полный прогон): `examples/your-product/`.
