---
name: playwright-automation
description: Browser automation with Playwright - testing, scraping, screenshots, AND a live daemon-browser controllable via CLI (bdo.py) for parallel online work that does NOT collide with the singleton MCP playwright plugin
---

# Playwright Automation Skill

## Overview

Автоматизация браузера с Playwright: тестирование, скрапинг, скриншоты, PDF генерация.
+ **Live Browser daemon** — онлайн-управление видимым браузером через CLI, параллельно MCP-плагину.

## Live Browser (параллельные сессии, онлайн-управление) ⭐

**Проблема:** MCP playwright-плагин (`mcp__plugin_playwright__*`) — singleton. Вторая
сессия Claude Code получает `Browser is already in use`. Параллельно работать нельзя.

### Способ 1 (ОСНОВНОЙ) — пул MCP-серверов `playwright-live1..10`

**Уже настроено:** в `~/.claude/settings.json` → `mcpServers` прописаны 10 серверов
`playwright-live1` … `playwright-live10`, каждый со своим профилем
`${HOME}/.claude/pw-profiles/live{N}/` и разрешён в `permissions.allow`
(`mcp__playwright-live{N}__*`). Шаблон каждого:
```json
"playwright-live1": { "command": "npx",
  "args": ["@playwright/mcp@latest", "--user-data-dir", "${HOME}/.claude/pw-profiles/live1"] }
```
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

**Установлено (2026-07-19):** `patchright` 1.61.2, браузер `chromium-1228` (Chrome for
Testing 149) в общем `ms-playwright`. Пакет отдельный от playwright, но браузеры делит.

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
- **`channel="chrome"`** требует установленного системного Chrome (есть на этой машине:
  `C:\Program Files\Google\Chrome\Application\chrome.exe`). Без него — bundled Chromium, тогда
  UA содержит `HeadlessChrome` (косметика, но некоторые чеки это ловят).
- **Не панацея.** Для полностью JS-независимых страниц (голый HTML/JSON API) лишний браузер не
  нужен — быстрее и незаметнее `curl_cffi` с TLS-имперсонацией. Карта выбора инструмента и
  таблица «симптом бана → инструмент» — в `references/stealth-scraping.md`.

Полный референс (оба инструмента, сниппеты из smoke, таблица симптомов): `references/stealth-scraping.md`.

## When to Use

- E2E тестирование
- Web scraping
- Автоматизация задач
- Скриншоты и PDF
- Browser automation

## Installation

```bash
# Python
pip install playwright
playwright install

# Node.js
npm init playwright@latest
```

## Basic Usage

### Python

```python
from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto("https://example.com")
        print(page.title())

        browser.close()

run()
```

### Async Python

```python
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        await page.goto("https://example.com")
        print(await page.title())

        await browser.close()

asyncio.run(main())
```

### Node.js

```javascript
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  await page.goto('https://example.com');
  console.log(await page.title());

  await browser.close();
})();
```

## Selectors

```python
# CSS selectors
page.click("button.submit")
page.fill("#email", "test@example.com")

# Text selectors
page.click("text=Sign in")
page.click("button:has-text('Submit')")

# XPath
page.click("//button[@type='submit']")

# Combined
page.click("article >> text=Read more")

# Nth element
page.click(".item >> nth=0")  # First
page.click(".item >> nth=-1") # Last

# Visible
page.click("button:visible")

# Role-based
page.get_by_role("button", name="Submit")
page.get_by_label("Email")
page.get_by_placeholder("Enter email")
page.get_by_text("Welcome")
```

## Common Actions

```python
# Navigation
page.goto("https://example.com")
page.go_back()
page.go_forward()
page.reload()

# Clicking
page.click("#button")
page.dblclick("#element")
page.click("#element", button="right")

# Typing
page.fill("#input", "text")
page.type("#input", "text", delay=100)  # With delay
page.press("#input", "Enter")

# Selecting
page.select_option("#dropdown", "value")
page.select_option("#dropdown", label="Option 1")

# Checkboxes
page.check("#checkbox")
page.uncheck("#checkbox")

# Hover
page.hover("#element")

# Drag & Drop
page.drag_and_drop("#source", "#target")

# File upload
page.set_input_files("#file-input", "path/to/file.pdf")
page.set_input_files("#file-input", [
    "file1.pdf",
    "file2.pdf"
])
```

## Waiting

```python
# Wait for selector
page.wait_for_selector("#element")
page.wait_for_selector("#element", state="visible")
page.wait_for_selector("#element", timeout=5000)

# Wait for navigation
page.wait_for_url("**/success")
page.wait_for_load_state("networkidle")

# Wait for function
page.wait_for_function("window.loaded === true")

# Explicit wait
page.wait_for_timeout(1000)  # 1 second

# Wait for response
with page.expect_response("**/api/users") as response_info:
    page.click("#load-users")
response = response_info.value
```

## Screenshots & PDF

```python
# Full page screenshot
page.screenshot(path="screenshot.png", full_page=True)

# Element screenshot
element = page.locator("#chart")
element.screenshot(path="chart.png")

# With options
page.screenshot(
    path="screenshot.png",
    type="jpeg",
    quality=80,
    clip={"x": 0, "y": 0, "width": 800, "height": 600}
)

# PDF (Chromium only)
page.pdf(
    path="page.pdf",
    format="A4",
    margin={"top": "1cm", "bottom": "1cm"}
)
```

## Web Scraping

```python
# Get text
text = page.locator("#title").inner_text()

# Get attribute
href = page.locator("a").get_attribute("href")

# Get all elements
items = page.locator(".item").all()
for item in items:
    print(item.inner_text())

# Extract structured data
products = page.locator(".product").all()
data = []
for product in products:
    data.append({
        "name": product.locator(".name").inner_text(),
        "price": product.locator(".price").inner_text(),
        "link": product.locator("a").get_attribute("href")
    })

# Execute JavaScript
result = page.evaluate("document.title")
data = page.evaluate("""
    () => {
        return Array.from(document.querySelectorAll('.item'))
            .map(el => ({
                title: el.querySelector('.title').innerText,
                price: el.querySelector('.price').innerText
            }));
    }
""")
```

## Network Interception

```python
# Block resources
page.route("**/*.{png,jpg,jpeg}", lambda route: route.abort())

# Modify requests
def handle_route(route):
    headers = route.request.headers
    headers["Authorization"] = "Bearer token123"
    route.continue_(headers=headers)

page.route("**/api/**", handle_route)

# Mock responses
page.route("**/api/users", lambda route: route.fulfill(
    status=200,
    content_type="application/json",
    body='[{"id": 1, "name": "Test"}]'
))

# Capture responses
responses = []

def capture(response):
    if "/api/" in response.url:
        responses.append({
            "url": response.url,
            "status": response.status,
            "body": response.json()
        })

page.on("response", capture)
```

## Testing with Playwright

```python
# test_example.py
from playwright.sync_api import Page, expect

def test_homepage(page: Page):
    page.goto("https://example.com")

    # Assertions
    expect(page).to_have_title("Example Domain")
    expect(page.locator("h1")).to_be_visible()
    expect(page.locator("h1")).to_have_text("Example Domain")

def test_login(page: Page):
    page.goto("https://app.example.com/login")

    page.fill("#email", "test@example.com")
    page.fill("#password", "password123")
    page.click("button[type='submit']")

    # Wait for redirect
    expect(page).to_have_url("**/dashboard")
    expect(page.locator(".welcome")).to_contain_text("Welcome")
```

### Running Tests

```bash
# Run tests
pytest tests/

# With browser visible
pytest --headed

# Specific browser
pytest --browser chromium
pytest --browser firefox
pytest --browser webkit

# Parallel
pytest -n 4

# Generate report
pytest --html=report.html
```

## Page Object Model

```python
# pages/login_page.py
class LoginPage:
    def __init__(self, page):
        self.page = page
        self.email_input = page.locator("#email")
        self.password_input = page.locator("#password")
        self.submit_button = page.locator("button[type='submit']")

    def goto(self):
        self.page.goto("/login")

    def login(self, email: str, password: str):
        self.email_input.fill(email)
        self.password_input.fill(password)
        self.submit_button.click()

# test_login.py
def test_login(page: Page):
    login_page = LoginPage(page)
    login_page.goto()
    login_page.login("user@example.com", "password")

    expect(page).to_have_url("**/dashboard")
```

## Browser Contexts

```python
# Isolated contexts (like incognito)
context1 = browser.new_context()
context2 = browser.new_context()

page1 = context1.new_page()
page2 = context2.new_page()

# With options
context = browser.new_context(
    viewport={"width": 1920, "height": 1080},
    locale="ru-RU",
    timezone_id="UTC",
    geolocation={"latitude": 55.75, "longitude": 37.62},
    permissions=["geolocation"]
)

# Mobile emulation
iphone = playwright.devices["iPhone 13"]
context = browser.new_context(**iphone)

# With authentication state
context = browser.new_context(storage_state="auth.json")

# Save authentication state
context.storage_state(path="auth.json")
```

## Authentication

```python
# Save auth state once
def setup_auth():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        page.goto("https://app.example.com/login")
        page.fill("#email", "user@example.com")
        page.fill("#password", "password")
        page.click("button[type='submit']")

        # Wait for auth to complete
        page.wait_for_url("**/dashboard")

        # Save state
        page.context.storage_state(path="auth.json")
        browser.close()

# Reuse auth state
def test_with_auth():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(storage_state="auth.json")
        page = context.new_page()

        # Already logged in
        page.goto("https://app.example.com/dashboard")
```

## Tips

1. **Headless** - используй `headless=False` для отладки
2. **Slow motion** - `slow_mo=100` для наблюдения
3. **Trace** - записывай trace для debug
4. **Auto-wait** - Playwright автоматически ждёт
5. **Locators** - предпочитай role-based selectors
6. **Contexts** - изолируй тесты в контекстах
7. **Codegen** - используй `playwright codegen` для записи
