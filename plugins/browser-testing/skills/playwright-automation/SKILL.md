---
name: playwright-automation
description: "Playwright: e2e-тесты, скрапинг + демон-браузер bdo.py (параллельные сессии). Триггеры: «e2e тест», «обойти антибот». НЕ заход с куками→dev-browser."
---

# Playwright Automation Skill

## Overview

Автоматизация браузера с Playwright: тестирование, скрапинг, скриншоты, PDF генерация.
+ **Live Browser daemon** — онлайн-управление видимым браузером через CLI, параллельно MCP-плагину.

## Live Browser (параллельные сессии, онлайн-управление) ⭐

**Проблема:** MCP playwright-плагин (`mcp__plugin_playwright__*`) — singleton. Вторая
сессия Claude Code получает `Browser is already in use`. Параллельно работать нельзя.

### Способ 1 (ОСНОВНОЙ) — пул MCP-серверов `playwright-live1..10`

**Настраивается один раз, руками.** Пул не приезжает готовым: заведи столько серверов
`playwright-live1` … `playwright-live{N}`, сколько сессий гоняешь параллельно (10 —
рабочий потолок), каждый со своим профилем `${HOME}/.claude/pw-profiles/live{N}/`.
Шаблон записи:
```json
"playwright-live1": { "command": "npx",
  "args": ["@playwright/mcp@latest", "--user-data-dir", "${HOME}/.claude/pw-profiles/live1"] }
```
Куда класть: в `.mcp.json` в корне проекта (образец — `~/.claude/templates/project.mcp.json`)
либо `claude mcp add playwright-live1 -- npx @playwright/mcp@latest --user-data-dir …`.
Проверить, что сервер реально поднялся, — `/mcp`: **наличие записи в конфиге ещё не значит,
что тул доступен**, молча не поднявшийся сервер выглядит точно так же, как отсутствующий.
Каждый номер добавь в `permissions.allow` как `mcp__playwright-live{N}__*`, иначе на каждый
вызов будет прилетать запрос доступа.
Полноценные нативные tools (то же богатство, что у плагина, но СВОЙ браузер):
`mcp__playwright-live{N}__browser_snapshot / browser_click / browser_take_screenshot /
browser_type / browser_evaluate / browser_navigate / ...`

- **Использование:** каждая сессия Claude Code берёт свой номер (1..10) → до 10 браузеров
  параллельно, не конфликтуя ни друг с другом, ни с плагином (`mcp__plugin_playwright__*`).
- Профили persistent → логины (RuTube/Gmail/...) сохраняются между сессиями.
- **После правки `mcpServers` нужен reload:** `/mcp` (reconnect) или рестарт сессии —
  иначе новые tools не появятся (MCP грузится на старте). Это умеет только пользователь.
- Нужно больше — добавить `playwright-live11`+ по тому же шаблону (другой `--user-data-dir`).
- `--isolated` вместо `--user-data-dir` = in-memory (логин не сохраняется), `--headless` = без окна
  (НЕ для RuTube/анти-бот — палят headless).

### Способ 2 (fallback) — daemon + bdo.py (CLI, без reload)

Когда нельзя reload-нуть MCP или нужен headless/фоновый браузер из Bash. Свой CDP-порт на сессию.

### Запуск daemon (видимое окно, живёт в фоне)

```bash
cd ~/.claude/skills/playwright-automation/scripts
# run_in_background=true! Daemon блокируется (держит браузер живым).
python browser_daemon.py --port 9456 --profile live-a --url https://example.com
```
- `--port` — УНИКАЛЬНЫЙ на сессию (9456, 9457, ...). Разные порты = разные браузеры параллельно.
- `--profile` — persistent-профиль в `profiles/<name>/`. Логины сохраняются между запусками
  (вошёл раз в RuTube/Gmail — профиль помнит). Разные профили = разные логины.
- `--headless` — без окна (НЕ для RuTube/анти-бот сайтов — палят headless).

### Управление — bdo.py (browser do)

Stateless: подключается к daemon по CDP-порту, делает действие, отключается (браузер жив).

```bash
python bdo.py --port 9456 url                      # текущий URL + title
python bdo.py --port 9456 goto https://site.ru     # перейти
python bdo.py --port 9456 snap                     # JSON кликабельных элементов (что нажать)
python bdo.py --port 9456 click "text=Войти"       # клик (text=/css/role=/"текст")
python bdo.py --port 9456 fill "#email" "a@b.ru"   # заполнить поле
python bdo.py --port 9456 type "#q" "запрос"        # печать по символу (триггерит JS)
python bdo.py --port 9456 press Enter              # клавиша
python bdo.py --port 9456 text [selector]          # innerText страницы/элемента
python bdo.py --port 9456 shot out.png [--full]    # скриншот → Read для анализа
python bdo.py --port 9456 eval "document.title"    # JS, вернуть результат
python bdo.py --port 9456 scroll 600               # прокрутка
python bdo.py --port 9456 upload "#file" /path.mp4 # загрузить файл в input
python bdo.py --port 9456 tabs / newtab <url> / wait <sel|ms> / quit
```

### Рабочий цикл (как «вижу и кликаю»)

1. `goto` → 2. `snap` (вижу кликабельные с селекторами) → 3. `click`/`fill` →
4. `shot` + Read png (визуальная проверка) → повтор. Для логина под капчей/push —
открыть видимое окно, попросить пользователя войти руками, дальше вести автоматически.

### Параллельность по-крупному (десятки браузеров)

- **Лучше всего:** `launch()` (НЕ persistent) + общий `storage_state.json` (логин-файл ~5КБ,
  шарится между всеми сессиями). Нет лока профиля, инжект логина в любой свежий контекст.
- persistent-профиль лочится одним процессом → для масштаба копировать профиль или
  использовать storage_state. CDP-шеринг (`connect_over_cdp`) — много вкладок в одном браузере.
- Ресурсы: headed Chrome ~0.3-0.5 ГБ RAM каждый; headless легче но палится анти-ботами.

Скрипты: `scripts/browser_daemon.py` (daemon), `scripts/bdo.py` (контроллер).

## Stealth-режим (patchright) ⭐

Когда обычный Playwright палится анти-ботом (Cloudflare Turnstile, Datadome, Kasada,
Akamai, PerimeterX) — бесконечный challenge, «Access denied», пустой контент — бери
**patchright** вместо `playwright`. Это стелс-форк с тем же API: скрывает CDP-утечки
(`Runtime.enable`), убирает `navigator.webdriver`, чинит `window.chrome`, permissions,
console-leak. **Drop-in замена одной строкой импорта.**

```python
# было:  from playwright.sync_api import sync_playwright
from patchright.sync_api import sync_playwright   # всё остальное — как в обычном Playwright
```

**Версии, на которых снят конфиг ниже:** `patchright` 1.61.2, браузер `chromium-1228`
(Chrome for Testing 149). Пакет отдельный от playwright, но каталог браузеров `ms-playwright`
делит с ним — второй раз качать не придётся. Ставится в два шага, см. «Гочи».

### Best-practice конфиг (максимальная невидимость)

Smoke на `bot.sannysoft.com`: наивный `launch(headless=True)` = 19 passed (остаётся
`HeadlessChrome` в UA, нет `window.chrome`). Рекомендованный конфиг = **28 passed / 3 failed
/ 0 warn**, `navigator.webdriver=False`, реальный GPU-renderer, `window.chrome` есть:

```python
from patchright.sync_api import sync_playwright

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=r"${HOME}\.claude\pw-profiles\stealth1",
        channel="chrome",     # реальный Chrome (не bundled Chromium) -> нет HeadlessChrome в UA
        headless=False,        # для max-стелса; headless=True тоже проходит webdriver-чек
        no_viewport=True,
    )
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto("https://target.example/")
    ...
    ctx.close()
```

### Гочи (обязательно к прочтению)

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
  нужен — быстрее и незаметнее `curl_cffi` с TLS-имперсонацией. Карта выбора инструмента и
  таблица «симптом бана → инструмент» — в `references/stealth-scraping.md`.

Полный референс (оба инструмента, сниппеты из smoke, таблица симптомов): `references/stealth-scraping.md`.

## Визуальный рекордер — `codegen` ⭐

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
