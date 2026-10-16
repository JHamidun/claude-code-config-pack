---
name: playwright-automation
description: "Playwright: e2e-наборы, скрапинг под антиботом (patchright), 10 параллельных сессий. Триггеры: «e2e тест», «сайт банит». НЕ разовый QA→gstack; свой логин→dev-browser."
---

# Playwright Automation Skill

Автоматизация браузера: тесты, скрапинг, скриншоты + **Live Browser daemon** — онлайн-управление видимым браузером через CLI, параллельно MCP-плагину.

## Место в семье: три браузерных скилла

У всех трёх одно ядро — переживающий вызовы браузер и снапшот доступности с refs, —
поэтому на «открой сайт и нажми» подходят все три одинаково. Разводит их не действие,
а три вещи: **чей это браузер**, **сколько живёт состояние** и **что именно мешает**.

| Скилл | Чей браузер | Формат работы | Зовут, когда |
|---|---|---|---|
| `gstack` | свой headless-демон, ~100 мс на команду, гаснет через 30 мин простоя | одиночные команды: `$B goto`, `snapshot -i`, `click @e3`, `is visible`, `console` | надо быстро убедиться, что задеплоенное живо, и увидеть дифф снапшота до/после действия |
| `dev-browser` | свой Chromium **или реальный Chrome пользователя** через расширение | TS-скрипты через `npx tsx`, именованные страницы `client.page("checkout")` живут между запусками | надо работать там, где человек уже залогинен, и копить состояние шаг за шагом |
| `playwright-automation` (этот) | свои изолированные профили: пул `playwright-live1..10`, демон `bdo.py` на своём CDP-порту | код на Python/Playwright: набор тестов, скрапер, записанный сценарий | сайт **банит** (patchright), нужен свой набор e2e или десятки браузеров параллельно |

Признак берётся из формулировки: «проверь, что на проде всё живо», «покажи, что
изменилось после клика» — `gstack`; «зайди под моим логином», «я там уже вошёл» —
`dev-browser`; «сайт меня банит», «нужен набор e2e», «десять браузеров сразу»,
«запиши сценарий» — сюда.

Если из браузерной сессии нужно сделать постоянную команду (клиент к сервису без API, карта эндпоинтов по трафику),
это skill `web-to-cli`; трафик для него записывается отсюда.

Практическая развилка по авторизации, где путаются чаще всего: `gstack` умеет
**импортировать куки** из настоящего браузера (`cookie-import-browser`), но ходит
всё равно своим headless-браузером; `dev-browser` в режиме расширения управляет
**самим окном пользователя**. Если логин защищён капчей или push-подтверждением,
импорт кук не поможет — нужен либо режим расширения `dev-browser`, либо видимое окно
демона отсюда, где человек входит руками, а дальше ведёт скрипт.

Стандартный Playwright API (селекторы, waits, route, storage_state, POM) пиши по знанию — здесь только наше: пул серверов, daemon, stealth, гочи. Предпочитай `get_by_role`/`get_by_text` над CSS-классами: динамические классы (Tailwind, CSS-modules) ломаются при первом редизайне.

## Live Browser (параллельные сессии, онлайн-управление)

**Проблема:** вторая сессия получает `Browser is already in use`.

⚠️ **Это не свойство плагина, а блокировка каталога профиля.** Chromium кладёт в
`--user-data-dir` файл `SingletonLock` и второй процесс с тем же каталогом не
поднимает. Поэтому «синглтон» лечится не заменой плагина, а **разными
профилями**: плагин и свой сервер прекрасно работают одновременно, если каталоги
у них не совпадают. Проверено 30.08 — плагин и `playwright-live1` в двух сессиях
разом.

### Способ 1 (ОСНОВНОЙ) — пул MCP-серверов `playwright-live{N}`

**Настраивается руками.** Установщик пака кладёт только `playwright-live1` (шаблон —
`~/.claude/templates/mcp-servers.json`), остальной пул не приезжает готовым: заведи столько
серверов `playwright-live1` … `playwright-live{N}`, сколько сессий гоняешь параллельно (10 —
рабочий потолок), каждый со своим профилем `~/.claude/pw-profiles/live{N}/`.
Шаблон записи (`/home/ИМЯ` замени своим домашним каталогом — **путь абсолютный, целиком**:
в JSON ни `~`, ни `${HOME}` никто не разворачивает, а на Windows переменной `HOME` обычно
нет вовсе, там `C:/Users/ИМЯ/...`):
```json
"playwright-live1": { "command": "npx",
  "args": ["@playwright/mcp@0.0.78", "--user-data-dir", "/home/ИМЯ/.claude/pw-profiles/live1"] }
```
Куда класть: в **`~/.claude.json`** → `mcpServers` (личный пул; секция `mcpServers` в
`settings.json` не читается вовсе — молча) либо в `.mcp.json` в корне проекта (образец —
`~/.claude/templates/project.mcp.json`); через CLI —
`claude mcp add playwright-live1 -- npx @playwright/mcp@0.0.78 --user-data-dir …`.
Проверить, что сервер реально поднялся, — `/mcp`: **наличие записи в конфиге ещё не значит,
что тул доступен**, молча не поднявшийся сервер выглядит точно так же, как отсутствующий.
Каждый номер добавь в `permissions.allow` как `mcp__playwright-live{N}__*`, иначе на каждый
вызов будет прилетать запрос доступа.

**Версия закреплена (как в шаблоне пака), а не `@latest`:** обновление пакета не сломает пул
внезапно. Но `npx` вообще резолвит пакет через реестр на каждом старте сессии — на замерах
с `@latest` это 38–41 с при дефолтном `MCP_TIMEOUT`, и сервер не успевал подняться.
Надёжнее локальная установка и запуск через `node` (0,3 с):
```bash
npm install --prefix ~/.claude @playwright/mcp@0.0.78
```
```json
"playwright-live2": { "command": "node",
  "args": ["/home/ИМЯ/.claude/node_modules/@playwright/mcp/cli.js",
           "--user-data-dir", "/home/ИМЯ/.claude/pw-profiles/live2"] }
```
На старте сессии поднимаются ВСЕ объявленные серверы, поэтому пул держим
небольшим: 4 сервера ≈ 1,2 с, десять — уже заметно.

**Сколько сейчас** — не по памяти, а командой:
```bash
python -c "import json,pathlib;d=json.load(open(pathlib.Path.home()/'.claude.json',encoding='utf-8'));print(sorted(k for k in d['mcpServers'] if 'playwright' in k))"
```
Добавить ещё — скопировать блок, поменять номер в имени и в `--user-data-dir`,
создать каталог профиля. Перезапуск сессии обязателен: `RefreshMcpTools` новые
серверы не поднимает.
Полноценные нативные tools (то же богатство, что у плагина, но СВОЙ браузер): `mcp__playwright-live{N}__browser_snapshot / browser_click / browser_take_screenshot / browser_type / browser_evaluate / browser_navigate / ...`

- Каждая сессия берёт свой номер (1..10) → до 10 браузеров параллельно без конфликтов.
- Профили persistent → логины (RuTube/Gmail/...) сохраняются между сессиями.
- **После правки `mcpServers` нужен reload:** `/mcp` (reconnect) или рестарт сессии — MCP грузится на старте, иначе новые tools не появятся. Это умеет только пользователь.
- Нужно больше — добавить `playwright-live11`+ по тому же шаблону (другой `--user-data-dir`).
- `--isolated` вместо `--user-data-dir` = in-memory (логин не сохраняется); `--headless` = без окна (НЕ для RuTube/анти-бот — палят headless).

### Способ 2 (fallback) — daemon + bdo.py (CLI, без reload)

Когда нельзя reload-нуть MCP или нужен headless/фоновый браузер из Bash. Свой CDP-порт на сессию.

**Запуск daemon** (видимое окно, живёт в фоне; `run_in_background=true` — daemon блокируется, держит браузер живым):

```bash
cd ~/.claude/skills/playwright-automation/scripts
python browser_daemon.py --port 9456 --profile live-a --url https://example.com
```
- `--port` — УНИКАЛЬНЫЙ на сессию (9456, 9457, ...). Разные порты = разные браузеры параллельно.
- `--profile` — persistent-профиль в `profiles/<name>/`; логины сохраняются между запусками. Разные профили = разные логины.
- `--headless` — без окна (НЕ для анти-бот сайтов).

**Управление — bdo.py** (stateless: подключается по CDP, делает действие, отключается — браузер жив):

```bash
python bdo.py --port 9456 url                      # текущий URL + title
python bdo.py --port 9456 goto https://site.ru     # перейти
python bdo.py --port 9456 snap                     # JSON кликабельных элементов (что нажать)
python bdo.py --port 9456 click "text=Войти"       # клик (text=/css/role=/"текст")
python bdo.py --port 9456 fill "#email" "<e-mail>" # заполнить поле
python bdo.py --port 9456 type "#q" "запрос"        # печать по символу (триггерит JS)
python bdo.py --port 9456 press Enter              # клавиша
python bdo.py --port 9456 text [selector]          # innerText страницы/элемента
python bdo.py --port 9456 shot out.png [--full]    # скриншот → Read для анализа
python bdo.py --port 9456 eval "document.title"    # JS, вернуть результат
python bdo.py --port 9456 scroll 600               # прокрутка
python bdo.py --port 9456 upload "#file" /path.mp4 # загрузить файл в input
python bdo.py --port 9456 tabs / newtab <url> / wait <sel|ms> / quit
```

**Рабочий цикл («вижу и кликаю»):** 1. `goto` → 2. `snap` (кликабельные с селекторами) → 3. `click`/`fill` → 4. `shot` + Read png (визуальная проверка) → повтор. Для логина под капчей/push — открыть видимое окно, попросить пользователя войти руками, дальше вести автоматически.

**Параллельность по-крупному (десятки браузеров):**
- Лучше всего: `launch()` (НЕ persistent) + общий `storage_state.json` (логин-файл ~5КБ, шарится между всеми сессиями). Нет лока профиля, инжект логина в любой свежий контекст.
- persistent-профиль лочится одним процессом → для масштаба копировать профиль или storage_state. CDP-шеринг (`connect_over_cdp`) — много вкладок в одном браузере.
- Ресурсы: headed Chrome ~0.3-0.5 ГБ RAM каждый; headless легче, но палится анти-ботами.

Скрипты: `scripts/browser_daemon.py`, `scripts/bdo.py`, `scripts/pw_guard.py` (детект бана).

## Stealth-режим (patchright)

Когда обычный Playwright палится анти-ботом (Cloudflare Turnstile, Datadome, Kasada, Akamai, PerimeterX) — бесконечный challenge, «Access denied», пустой контент — бери **patchright**: стелс-форк с тем же API, скрывает CDP-утечки (`Runtime.enable`), убирает `navigator.webdriver`, чинит `window.chrome`. Drop-in замена одной строкой импорта:

```python
# было:  from playwright.sync_api import sync_playwright
from patchright.sync_api import sync_playwright   # всё остальное — как в обычном Playwright
```

**Версии, на которых снят конфиг ниже:** `patchright` 1.61.2, браузер `chromium-1228`
(Chrome for Testing 149). Пакет отдельный от playwright, но каталог браузеров `ms-playwright`
делит с ним — второй раз качать не придётся. Ставится в два шага, см. «Гочи».

### Best-practice конфиг (максимальная невидимость)

Smoke на `bot.sannysoft.com`: наивный `launch(headless=True)` = 19 passed (остаётся `HeadlessChrome` в UA, нет `window.chrome`). Рекомендованный конфиг = **28 passed / 3 failed / 0 warn**, `navigator.webdriver=False`, реальный GPU-renderer:

```python
import os
from patchright.sync_api import sync_playwright

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        # expanduser обязателен: Python не разворачивает ни "~", ни "${HOME}" внутри
        # строки — путь уехал бы в каталог с буквальным именем. Прямые слэши Windows
        # понимает, поэтому одна форма годится на всех трёх системах.
        user_data_dir=os.path.expanduser("~/.claude/pw-profiles/stealth1"),
        channel="chrome",     # реальный Chrome (не bundled Chromium) -> нет HeadlessChrome в UA
        headless=False,        # для max-стелса; headless=True тоже проходит webdriver-чек
        no_viewport=True,
    )
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto("https://target.example/")
    ...
    ctx.close()
```

### Гочи

- **Отдельный пакет.** `pip install patchright` + `patchright install chromium`. Не путать
  импорты: `from patchright...`, не `from playwright...`.
- **Не ломай стелс своими руками.** patchright документированно теряет невидимость если
  использовать `add_init_script`, кастомные `--headless`-флаги, `route`/перехват запросов,
  или переопределять `user_agent`/`headers`/`viewport` вручную. Хочешь маскировку — доверься
  дефолтам и `channel="chrome"` + persistent context.
- **Persistent context обязателен для лучшего результата** (`launch_persistent_context`), не
  `launch()`+`new_context()`. Профиль лочится одним процессом (как у обычного Playwright).
- **`channel="chrome"`** требует **системного** Chrome — того, что стоит у тебя как обычный
  браузер (Windows: `C:\Program Files\Google\Chrome\Application\chrome.exe`, macOS:
  `/Applications/Google Chrome.app`, Linux: `google-chrome`). Не установлен — Playwright
  молча возьмёт bundled Chromium, и UA будет содержать `HeadlessChrome` (косметика, но
  часть чеков это ловит). Проверить, что канал реально нашёлся, можно по UA:
  `page.evaluate("navigator.userAgent")` — `HeadlessChrome` в строке = взялся Chromium.
- **Не панацея.** Для полностью JS-независимых страниц (голый HTML/JSON API) лишний браузер не
  нужен — быстрее и незаметнее `curl_cffi` с TLS-имперсонацией.

Карта выбора инструмента, таблица «симптом бана → инструмент», сниппеты из smoke: `references/stealth-scraping.md`.

## Визуальный рекордер — `codegen`

Кликаешь в браузере руками — на выходе готовый скрипт. Это то, ради чего обычно ставят
no-code платформы вроде Maxun (5 контейнеров: postgres + minio + backend + frontend + browser),
только здесь это одна команда и ноль постоянных сервисов.

```bash
# записать действия и сразу получить Python-скрипт
npx playwright codegen --target python -o scraper.py https://example.com

# под свой стек: python-async, javascript, playwright-test, java, csharp
npx playwright codegen --target python-async -o scraper.py https://example.com

# с авторизацией: сначала логинишься руками, состояние сохраняется
npx playwright codegen --save-storage=auth.json https://site.com/login
npx playwright codegen --load-storage=auth.json https://site.com/dashboard

# записать на конкретном браузере / мобильном устройстве
npx playwright codegen -b firefox --device "iPhone 15" https://example.com
```

**Как это ложится в остальной стек:**

1. `codegen` — записал сценарий, получил черновик селекторов
2. Переписал импорт на `patchright`, если цель под анти-ботом (см. раздел Stealth)
3. Прогон через `bdo.py`-демон, если нужен живой браузер между вызовами
4. `pw_guard.is_blocked(page)` после каждого `goto` — чтобы бан не выглядел как «ничего не нашлось»

**Гоча:** codegen генерирует селекторы по видимому тексту и `data-testid`. На динамических классах
(Tailwind, CSS-modules) они ломаются при первом же редизайне — после записи стоит заменить
хрупкие селекторы на `get_by_role` / `get_by_text`.

## pw_guard — три защиты скрапера (`scripts/pw_guard.py`)

Без зависимостей, работает и с `playwright`, и с `patchright` — принимает любой `page`.

```python
from pw_guard import is_blocked, assert_not_blocked, window_snapshot, should_skip_frame

blocked, reason = is_blocked(page)      # после КАЖДОГО goto
snippet = window_snapshot(page, offset=0, max_chars=80000)
```

- `is_blocked(page) -> (bool, reason)` — **пустой результат скрапера неотличим от «ничего не
  нашлось»**; без явной проверки бан молча уезжает в отчёт как валидный ноль. `assert_not_blocked`
  — то же, но кидает `BlockedError`.
- `window_snapshot(source, offset, max_chars=80000, tail_chars=…)` — aria-снапшот большой страницы
  это сотни тысяч символов, и MCP отдаёт их в контекст ЦЕЛИКОМ. Режет окном и **всегда подклеивает
  хвост**: пагинация и навигация живут в подвале страницы.
- `SKIP_FRAME_PATTERNS` / `should_skip_frame(url)` — антибот-iframe'ы (recaptcha, perimeterx,
  hcaptcha, px-captcha) висят по таймауту и мусорят снапшот; их пропускают, а не ждут.

Самопроверка: `python pw_guard.py <url>`.
