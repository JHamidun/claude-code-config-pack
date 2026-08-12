# Stealth-скрапинг: curl_cffi + patchright + Fortress + Camoufox

> Четыре независимых пути обхода анти-ботов, **все установлены и проверены запуском**
> (Python 3.13, Windows): curl_cffi и patchright — 2026-07-19, Fortress и Camoufox — 2026-08-11.
> Общий референс для skills: `playwright-automation`, `tender-search-ru`, `headhunter`, `ad-spy`.
>
> **Зачем четыре.** Разные движки дают разные отпечатки, поэтому их можно гонять
> **параллельно с одного IP** — цель не свяжет сессии между собой. Один Chromium в десяти
> копиях такого не даёт: отпечаток у всех одинаковый.

## TL;DR — какой инструмент когда

| Нужно | Инструмент | Почему |
|-------|-----------|--------|
| Дёрнуть JSON-API / голый HTML, который банит `requests` | **curl_cffi** (`impersonate="chrome"`) | Нет браузера → быстро и легко; подделывает TLS/JA3-отпечаток под Chrome. WAF видит «настоящий Chrome». |
| Страница требует исполнения JS / клики / логин, и стоит анти-бот | **patchright** | Полный браузер, но скрывает `navigator.webdriver`, CDP-утечки (`Runtime.enable`), чинит `window.chrome`. |
| Cloudflare Turnstile / Datadome / Kasada / Akamai challenge | **patchright** (браузер) или **curl_cffi** (если challenge только TLS/JA3-based) | Пробуй сначала curl_cffi (дёшево), не пробило — patchright. |
| **Chromium-детектор ловит patchright** (видит JS-патчи в геттерах) | **Fortress** (Chromium 151, C++) | Подмена в самом движке: `webdriver`-геттер отдаёт `[native code]`. Замер 7/7. Подключение по CDP, код не меняется |
| **Chromium как класс уже спалён** / нужна гео-привязка к прокси | **Camoufox** (Firefox) | Другой движок + подмена на уровне C++ **до** того, как значение увидит JS. Детекторы, заточенные под CDP-артефакты Chromium, на нём не срабатывают. |
| Обычный сайт без защиты | стоковый `playwright` / `requests` | Стелс не нужен, лишний оверхед. |

**Принцип:** начинай с самого лёгкого (curl_cffi без браузера) → эскалируй к patchright
(браузер) только когда нужен реальный рендеринг JS или защита ловит именно браузерную
автоматизацию → Camoufox как **третья нога**, когда Chromium как класс уже не проходит.

**Слои подмены — почему это не дубли, а разные уровни:**

| Инструмент | Что подделывает | На каком слое |
| ---------- | --------------- | ------------- |
| curl_cffi | TLS/JA3-отпечаток | сетевой, браузера нет вообще |
| patchright | `navigator.webdriver`, CDP-утечки, `window.chrome` | CDP/JS-рантайм Chromium — **после** того, как значение выдал движок |
| **Fortress** | `navigator.*`, WebGL, геттеры прототипов | **C++ движка Chromium (Blink/V8/BoringSSL) — до JS**; геттеры отдают `[native code]` |
| Camoufox | `navigator.*`, WebGL vendor/renderer, AudioContext, геометрия экрана, WebRTC-IP, шрифты | **C++ движка Firefox — до JS**; отпечаток генерит BrowserForge по реальным распределениям устройств |

---

## Установка

```bash
pip install patchright curl_cffi
patchright install chromium      # ~40 сек, кладёт chromium-1228 (Chrome for Testing) в ms-playwright
```

- Версии на момент установки: `patchright` 1.61.2, `curl_cffi` 0.15.0.
- patchright — **отдельный пакет** от playwright, но браузеры делит через общий
  `~/AppData/Local/ms-playwright/`. Если долго/тяжело качать браузер — можно пропустить
  `patchright install chromium` и использовать `channel="chrome"` (системный Chrome). На этой
  машине системный Chrome есть: `C:\Program Files\Google\Chrome\Application\chrome.exe`.
- curl_cffi ставит бандл BoringSSL-форка curl — браузер не нужен вообще.

---

## curl_cffi — TLS/JA3 имперсонация без браузера

Обычный `requests` выдаёт себя TLS-отпечатком (JA3) питоновского OpenSSL + UA
`python-requests/x`. WAF (Cloudflare, Akamai) это ловит на уровне рукопожатия — ещё до
первого HTTP-запроса. curl_cffi подделывает cipher-suites, extensions, порядок и HTTP/2
SETTINGS так, что JA3/JA4/Akamai-хэш совпадают с реальным Chrome/Safari/Firefox.

### Рабочий сниппет (из smoke)

```python
from curl_cffi import requests   # НЕ стандартный requests

# 37 профилей: chrome, chrome131, safari, safari17_0, edge, firefox, ...
r = requests.get("https://example.com/api", impersonate="chrome", timeout=30)
print(r.status_code, r.json())

# сессия с куками (как requests.Session)
s = requests.Session(impersonate="chrome")
s.get("https://example.com/login")
s.post("https://example.com/api", json={"q": "x"})

# прокси — тот же синтаксис, что у requests
r = requests.get(url, impersonate="chrome",
                 proxies={"https": "http://user:pass@host:port"})
```

### Доказательство маскировки (smoke 2026-07-19, tls.browserleaks.com/json)

| | curl_cffi `impersonate=chrome` | plain `requests` (baseline) |
|---|---|---|
| JA3 hash | `24d6f5452f7090726de59704f2b8698a` (канон Chrome) | `a48c0d5f95b1ef98f560f324fd275da1` |
| JA4 | `t13d1516h2_...` (HTTP/2) | `t13d1812h1_...` (HTTP/1.1) |
| Akamai h2 hash | `52d84b11737d980aef856699f885ca86` | (пусто — нет HTTP/2) |
| User-Agent | `...Chrome/146...` | `python-requests/2.33.0` |

**Вывод:** отпечатки полностью разные; curl_cffi неотличим от Chrome на уровне TLS+HTTP/2.

### Гочи curl_cffi

- Импорт `from curl_cffi import requests` — тень стандартного `requests`. В одном файле
  держи алиас: `from curl_cffi import requests as cffi`.
- `impersonate="chrome"` = «последний Chrome». Для стабильности можно пиннить: `chrome131`,
  `chrome124`, `safari17_0` и т.д. (полный список — `curl_cffi.requests.BrowserType`).
- Подделывается TLS/HTTP2, но **не** JS-fingerprint. Если сайт грузит челлендж через JS
  (Turnstile в браузере) — curl_cffi не исполнит его, нужен patchright.
- Свои `headers` можно передавать, но не ломай порядок/значения, которые ставит impersonate
  (лучше добавлять, а не заменять `User-Agent`).

---

## patchright — стелс-браузер (drop-in Playwright)

Стелс-форк Playwright. Тот же API — меняется одна строка импорта. Убирает то, чем
стоковый Playwright палится: `navigator.webdriver=true`, CDP-команда `Runtime.enable`
(её ловят Cloudflare/Datadome), пустой `window.chrome`, аномалии permissions/console.

```python
# было:  from playwright.sync_api import sync_playwright
from patchright.sync_api import sync_playwright
# async: from patchright.async_api import async_playwright
```

### Best-practice конфиг (максимальная невидимость)

```python
from patchright.sync_api import sync_playwright

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=r"${HOME}\.claude\pw-profiles\stealth1",
        channel="chrome",     # реальный Chrome (не bundled) -> нет HeadlessChrome в UA
        headless=False,        # для max-стелса; headless=True тоже проходит webdriver-чек
        no_viewport=True,
    )
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto("https://target.example/", wait_until="networkidle")
    # ... обычные playwright-действия: click / fill / evaluate / screenshot ...
    ctx.close()
```

### Доказательство (smoke 2026-07-19, bot.sannysoft.com)

| Конфиг | Результат |
|--------|-----------|
| Наивный `launch(headless=True)`, bundled Chromium | 19 passed. WebDriver побеждён, но `HeadlessChrome` в UA, нет `window.chrome`, 0 плагинов. |
| **Best: `launch_persistent_context(channel="chrome", headless=True)`** | **28 passed / 3 failed / 0 warn.** `navigator.webdriver=False`, `window.chrome` есть, реальные плагины, реальный GPU (ANGLE NVIDIA your GPU), permissions/chrome-object OK. |

3 остаточных FAIL best-конфига = только UA-строка содержит `HeadlessChrome`
(User Agent Old, HEADCHR_UA) + CHR_MEMORY. Косметика headless — уходит при `headless=False`.

### Гочи patchright (обязательно)

- **Отдельный пакет + браузер.** `pip install patchright` и `patchright install chromium`.
  Не путать импорты (`patchright`, не `playwright`).
- **Не ломай стелс своими руками.** Документированно теряет невидимость при:
  `add_init_script`, кастомных `--headless`-флагах, `page.route()`/перехвате запросов,
  ручном переопределении `user_agent`/`headers`/`viewport`. Доверься дефолтам +
  `channel="chrome"` + persistent context.
- **Persistent context > launch().** Лучший результат — `launch_persistent_context`, не
  `browser.launch()` + `new_context()`. Профиль лочится одним процессом (нельзя два процесса
  на один `user_data_dir`).
- **`channel="chrome"`** требует системного Chrome. Без него — bundled Chromium, тогда UA
  содержит `HeadlessChrome` (некоторые чеки это ловят, но core-antidetect всё равно проходит).
- Не универсальный обход капчи. Скрывает автоматизацию, но интерактивную капчу (reCAPTCHA v2
  клик) всё равно решает человек/сервис.

---

## `scripts/pw_guard.py` — детектор блокировки и skip-лист (вызывается из `bdo.py`)

Стелс уменьшает шанс бана, но не отменяет его. Забаненная страница — это **не ошибка**:
приходит 200, `innerText` на 300 символов, парсер честно достаёт из них ноль результатов.
Снаружи «забанили» неотличимо от «ничего не нашлось» — и это самый дорогой класс багов,
потому что пайплайн идёт дальше с пустыми данными. Поэтому бан ловим явно.

```python
from pw_guard import is_blocked, assert_not_blocked, should_skip_frame, window_snapshot

page.goto(url, wait_until="domcontentloaded")
blocked, reason = is_blocked(page)      # ВСЕГДА после goto, ДО парсинга
if blocked:
    raise RuntimeError(f"blocked: {reason}")   # или assert_not_blocked(page)
```

**Три функции:**

| Функция | Что делает | Почему так |
| --- | --- | --- |
| `is_blocked(page) -> (bool, reason)` | 19 паттернов по title + `innerText`: Cloudflare, Datadome, PerimeterX, Kasada, hCaptcha, 403/429, RU-заслоны («Доступ ограничен», SmartCaptcha) | Возвращает **имя** паттерна, а не просто False — по логу видно, кто именно забанил и чем лечить |
| `should_skip_frame(url)` | Skip-лист антибот-iframe (recaptcha, px-captcha, datadome, arkose…) | Эти фреймы висят по таймауту и засоряют снапшот. Вызывается автоматически внутри `aria_snapshot()` |
| `window_snapshot(...)` | Окно 80K + **обязательный хвост 5K** | Пагинация и футер-навигация живут в подвале; обрезав их, дальше идти нечем |

Пустое тело (`innerText` < 40 символов) тоже считается блокировкой — это ровно тот
silent failure, ради которого детектор и написан.

**Где уже подключено (не дублируй):**

- `bdo.py` → `report_block()` на `goto` и `newtab`; отдельная команда `blocked`;
  `aria` и `text` идут через `window_snapshot`.
- Заслон = **exit 3** и явная причина в stderr. `--allow-blocked` понижает до warning
  (exit 0), когда бан ожидаем и обрабатывается вызывающим.

**Живая проверка (2026-08-01, patchright, headless):**

```text
$ python pw_guard.py https://example.com
blocked=False reason=
raw_chars=232 -> window_chars=232 truncated=False

$ python pw_guard.py "https://www.google.com/search?q=playwright+stealth"
blocked=True reason=google_unusual_traffic: 'Our systems have detected unusual traffic'
raw_chars=391

$ python bdo.py --port 9611 goto "https://www.google.com/search?q=test+query"
ERR blocked: google_unusual_traffic: ...     # exit 3
```

391 символа «выдачи» — это и есть тот самый пустой результат, который без детектора
уехал бы дальше по пайплайну как «ничего не нашлось».

> Идеи детектора и skip-листа взяты из `camofox-browser`, сам пакет — нет
> (маскированный `spawn` в postinstall + телеметрия с целевым URL, см. врезку ниже).

---

## Fortress — Chromium с патчами в C++ ✅ УСТАНОВЛЕН

Форк Chromium 151: 34 патча в Blink, V8 и BoringSSL. Отличие от patchright принципиальное —
там подмена живёт в CDP/JS-слое и её видно по геттерам, здесь значения меняются
**в самом движке**, до того как их увидит JS.

```text
бинарь: ${WORKSPACE}/browsers/fortress/tilion-fortress/chrome.exe   (532 МБ, BSD-3)
```

Работает через CDP, код менять не нужно — подключается тем же patchright или playwright:

```bash
# 1) поднять браузер с открытым CDP-портом
"${WORKSPACE}/browsers/fortress/tilion-fortress/chrome.exe" \
  --headless=new --remote-debugging-port=9333 \
  --user-data-dir=/tmp/fortress-prof --no-first-run --no-default-browser-check
```

```python
# 2) подключиться к уже запущенному браузеру
from patchright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:9333")
    page = (browser.contexts[0] if browser.contexts else browser.new_context()).new_page()
```

**Замер на этой машине (2026-08, Chromium 151.0.7908.0), 7 из 7:**

| Проверка | Результат |
| -------- | --------- |
| `navigator.webdriver` | `false` |
| UA | без `HeadlessChrome` |
| `window.chrome` | `object` |
| plugins / mimeTypes | 5 / 2 (не пусто) |
| `permissions.query` | `[native code]` |
| геттер `webdriver` | `[native code]` — **JS-инъекции не видно** |
| `cdc_` / `__driver` | отсутствуют |

### Гочи Fortress

1. **🚨 Локаль по умолчанию индонезийская.** Замер отдал `navigator.languages = ['id-ID','id','en']`.
   Российский или бразильский IP плюс индонезийский язык — сам по себе сигнал. Перед работой
   выставляй язык под задачу (`--lang=ru-RU` и заголовок `Accept-Language`), иначе маскировка
   отпечатка спасает, а несоответствие локали и гео выдаёт.
2. **Отпечаток «средний», а не твой.** Отдаёт 4 ядра, 8 ГБ, WebGL `AMD Radeon` — при том что
   машина 16-ядерная с your GPU. Это by design, но помни: значения не совпадут с реальным железом,
   если цель сверяет их с чем-то ещё.
3. **Windows-сборки нет в свежем релизе.** В `v150` только Linux. Windows-архивы лежат
   в `v149` (stable) и `v151` (latest) — если обновляешься, проверяй список ассетов.
4. Ошибка `Sandbox cannot access executable` при первом запуске из непривычного пути — Chromium
   ругается на песочницу, на работу через CDP не влияет.

## Camoufox — Firefox с подменой в C++ ✅ УСТАНОВЛЕН

Вторая независимая нога: другой движок (Gecko), поэтому детекторы, заточенные под Chromium,
на нём не срабатывают в принципе.

```text
venv:   ${WORKSPACE}/browsers/camoufox-venv    (227 МБ + бинарь Firefox-форка в AppData)
запуск: ${WORKSPACE}/browsers/camoufox-venv/Scripts/python.exe
```

**Замер на этой машине:** `Firefox/152.0` (Gecko), `webdriver = false`, `platform = Win32`,
12 ядер, `languages = ['en-US','en']`.

```bash
# если понадобится переустановить
python -m venv ${WORKSPACE}/browsers/camoufox-venv
${WORKSPACE}/browsers/camoufox-venv/Scripts/pip install -U "camoufox[geoip]"
${WORKSPACE}/browsers/camoufox-venv/Scripts/python.exe -m camoufox fetch
```

```python
from camoufox.sync_api import Camoufox

# os/humanize/geoip — весь стелс задаётся тут, руками ничего не патчим
with Camoufox(os="windows", humanize=True, geoip=True,
              proxy={"server": "http://user:pass@host:port"}) as browser:
    page = browser.new_page()
    page.goto("https://example.com")
```

**Что даёт сверх patchright:**

- **Другой движок.** Детекторы, заточенные под CDP-артефакты Chromium (`Runtime.enable`, следы `Page.*`), на Firefox просто не срабатывают — там другая поверхность.
- **`geoip=True`** — автосогласование locale, timezone и координат с IP прокси. Руками это муторно и легко забыть, а рассинхрон «немецкий IP + московская таймзона» палит сразу.
- **`humanize=True`** — человекоподобное движение курсора на уровне движка.

**Честная цена (знать до установки):**

| Что | Сколько |
| --- | ------- |
| Диск | ~470 МБ (Windows), ~630 МБ (Linux); распакованным в 2-3 раза больше |
| Окружение | обязательно отдельный venv (`playwright<1.61`) |
| Лицензия браузера | **MPL-2.0** — файловый copyleft. Личное использование и скиллы не задевает; выстрелит только если вшивать браузер в дистрибутив клиенту (`installer-builder`) — тогда тащи текст MPL и ссылку на исходники |
| Питон-обёртка | MIT |

> **Почему не REST-обёртка `camofox-browser`** (8210★): её собственный стелс-вклад — 11 строк
> вызова этого же движка. При этом в `postinstall` намеренно замаскирован `spawn`
> («to avoid triggering static code scanners»), а телеметрия включена по умолчанию и шлёт
> целевой URL на сторонний Worker. Идеи из неё забраны в `scripts/pw_guard.py`, сам пакет — нет.

---

## Таблица: симптом бана → инструмент

| Симптом | Первый шаг | Если не помогло |
|---------|-----------|-----------------|
| `requests`/curl отдаёт 403 / «Access Denied» / Cloudflare 1020 сразу | curl_cffi `impersonate="chrome"` | patchright (браузер) |
| Пустой/усечённый HTML, контент грузится JS-ом | patchright (нужен рендер) | + прокси, `channel="chrome"` |
| Бесконечный Cloudflare Turnstile / «Checking your browser» | patchright `channel="chrome"`, persistent, `headless=False` | резидентный прокси |
| Datadome / PerimeterX / Kasada challenge-cookie | patchright (скрывает CDP/webdriver) | curl_cffi если challenge чисто TLS-based |
| Работает с браузера, но `playwright` палится (`navigator.webdriver`) | patchright (drop-in) | — |
| Гео-блок по IP (напр. zakupki.gov.ru из не-РФ) | RU-прокси/агрегатор (rostender), затем patchright под анти-ботом | — |
| Рейт-лимит / IP-бан после N запросов | ротация прокси (оба инструмента поддерживают `proxies=`) | снизить частоту, случайные задержки |
| Мобильная выдача отличается | curl_cffi `impersonate="chrome"` + мобильный UA / patchright device emulation | — |

---

## Легально и этично

- Только публичные данные, уважай `robots.txt` и ToS, не долби рейт-лимиты.
- Стелс — для доступа к тому, что и так открыто в браузере, а не для обхода авторизации/paywall.
- Логины/капчи под push — открывай видимое окно (`headless=False`) и проси пользователя войти руками.
