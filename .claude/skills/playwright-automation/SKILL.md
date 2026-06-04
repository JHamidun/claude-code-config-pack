---
name: playwright-automation
description: Browser automation with Playwright - testing, scraping, screenshots
---

# Playwright Automation Skill

## Overview

Автоматизация браузера с Playwright: тестирование, скрапинг, скриншоты, PDF генерация.

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
