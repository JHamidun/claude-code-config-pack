# Stealth-скрапинг: patchright + curl_cffi

> Два стелс-инструмента для обхода анти-ботов. Установлены и проверены 2026-07-19
> (Python 3.13, Windows). Общий референс для skills: `playwright-automation`,
> `tender-search-ru`, `headhunter`, `ad-spy`.

## TL;DR — какой инструмент когда

| Нужно | Инструмент | Почему |
|-------|-----------|--------|
| Дёрнуть JSON-API / голый HTML, который банит `requests` | **curl_cffi** (`impersonate="chrome"`) | Нет браузера → быстро и легко; подделывает TLS/JA3-отпечаток под Chrome. WAF видит «настоящий Chrome». |
| Страница требует исполнения JS / клики / логин, и стоит анти-бот | **patchright** | Полный браузер, но скрывает `navigator.webdriver`, CDP-утечки (`Runtime.enable`), чинит `window.chrome`. |
| Cloudflare Turnstile / Datadome / Kasada / Akamai challenge | **patchright** (браузер) или **curl_cffi** (если challenge только TLS/JA3-based) | Пробуй сначала curl_cffi (дёшево), не пробило — patchright. |
| Обычный сайт без защиты | стоковый `playwright` / `requests` | Стелс не нужен, лишний оверхед. |

**Принцип:** начинай с самого лёгкого (curl_cffi без браузера) → эскалируй к patchright
(браузер) только когда нужен реальный рендеринг JS или защита ловит именно браузерную
автоматизацию.

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
