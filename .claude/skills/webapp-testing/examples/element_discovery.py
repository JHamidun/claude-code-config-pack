"""Example: discovering buttons, links and inputs on a page.

Запускать как скрипт. При импорте не делает НИЧЕГО: браузер поднимается только
в main(), иначе `import element_discovery` (линтер, автодополнение) открывал бы
Chromium и ходил на страницу.

Настройки — переменными окружения, а не правкой кода:
    WEBAPP_TEST_URL   адрес страницы (умолчание http://localhost:5173)
    WEBAPP_TEST_OUT   куда класть артефакты (умолчание ./webapp-test-out)
"""
import os
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = os.environ.get("WEBAPP_TEST_URL", "http://localhost:5173")
OUT_DIR = Path(os.environ.get("WEBAPP_TEST_OUT") or (Path.cwd() / "webapp-test-out"))


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    shot = OUT_DIR / "page_discovery.png"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Navigate to page and wait for it to fully load
        page.goto(URL)
        page.wait_for_load_state('networkidle')

        # Discover all buttons on the page
        buttons = page.locator('button').all()
        print(f"Found {len(buttons)} buttons:")
        for i, button in enumerate(buttons):
            text = button.inner_text() if button.is_visible() else "[hidden]"
            print(f"  [{i}] {text}")

        # Discover links
        links = page.locator('a[href]').all()
        print(f"\nFound {len(links)} links:")
        for link in links[:5]:  # Show first 5
            text = link.inner_text().strip()
            href = link.get_attribute('href')
            print(f"  - {text} -> {href}")

        # Discover input fields
        inputs = page.locator('input, textarea, select').all()
        print(f"\nFound {len(inputs)} input fields:")
        for input_elem in inputs:
            name = input_elem.get_attribute('name') or input_elem.get_attribute('id') or "[unnamed]"
            input_type = input_elem.get_attribute('type') or 'text'
            print(f"  - {name} ({input_type})")

        # Take screenshot for visual reference
        page.screenshot(path=str(shot), full_page=True)
        print(f"\nScreenshot saved to {shot}")

        browser.close()


if __name__ == '__main__':
    main()
