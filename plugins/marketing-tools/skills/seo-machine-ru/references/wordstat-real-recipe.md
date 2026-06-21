# Wordstat: как реально достать частоты (проверено 2026-06)

> Боевой рецепт, проверенный на реальном прогоне. Wordstat — единственный источник абсолютной частотности под Яндекс. Здесь пути по убыванию надёжности и что из них СРАБОТАЛО.

## TL;DR — что работает

**Рабочий способ:** залогиненный браузер на `wordstat.yandex.ru` → дёргать internal API `POST /wordstat/api/getTable` (fetch со страницы, куки идут сами, CSRF не нужен). Один вызов = частота + расширения + ассоциации по фразе. Цикл по списку фраз снимает всё ядро за секунды.

**Обычно НЕ работает:** Direct API v4 (`api.direct.yandex.com/v4/json/`, метод `CreateNewWordstatReport`) — OAuth-токен принимается, но возвращает `error 58: "No access — fill out app access request in Direct interface"`. Нужен отдельный одобренный доступ к Яндекс.Директ API (заявка + ожидание). Если будете делать свой клиент Direct API — тело запроса слать UTF-8-байтами (`json.dumps(..., ensure_ascii=False).encode("utf-8")`), иначе `error 501 "Request encoding is not UTF8"`.

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
  "searchValue": "система управления задачами",
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
  "totalValue": 3400,                      // <- ЧАСТОТА базовой фразы (показов/мес)
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
  const phrases = ["система управления задачами","таск-менеджер для команды", /* ...весь список... */];
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

Понадобится **ваш** аккаунт Яндекса. Положите креды в `.env` (см. `.env.example`): `YANDEX_LOGIN` + `YANDEX_PASSWORD`.
Поток входа (новый Яндекс ID): ввести логин/email → «Далее» → экран пуш-кода → кнопка **«Войти с паролем»** → ввести пароль → **2FA** (пуш на устройства Яндекс ИЛИ SMS). **2FA проходит только владелец аккаунта** — подтвердить на телефоне или ввести 6-значный код. После входа **сессия в профиле браузера сохраняется** (persistent), повторный логин не нужен.

- Playwright MCP использует персистентный профиль (`…/ms-playwright/mcp-chrome-*`) — логин там переживает перезапуски (часто УЖЕ залогинен — проверяй первым делом).
- chrome-devtools MCP — отдельный профиль, может быть не залогинен.
- **Никогда не коммить `.env` с кредами** (он в `.gitignore`).

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

Тиры, выведенные из ширины suggest/«ощущения рынка», **завышают в 5–10×**. На реальном прогоне оценки вида «~18 000» оказывались **~2 000**, а «~2 200» → **~120**; точные узкие лонг-тейлы часто = **0–3** показа, тогда как категорийный head — крупнейший по объёму. **Вывод:** всегда снимать реальный Wordstat перед приоритизацией; точные коммерческие лонг-тейлы держать как страницы под конверсию/AEO, не ждать от них трафика.

## Связки
- Скоринг по реальным объёмам: `scripts/opportunity_scorer.py`.
- Упаковка ядра+статьи в Word для стейкхолдера: `scripts/build_report_docx.py`.
- Рабочий пример (структура артефактов): `examples/`.
