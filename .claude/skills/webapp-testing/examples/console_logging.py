"""Example: capturing console logs during browser automation.

Запускать как скрипт. При импорте не делает НИЧЕГО: браузер поднимается только
в main(), иначе `import console_logging` (линтер, автодополнение) открывал бы
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
    log_path = OUT_DIR / "console.log"
    console_logs = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1920, 'height': 1080})

        # Set up console log capture
        def handle_console_message(msg):
            console_logs.append(f"[{msg.type}] {msg.text}")
            print(f"Console: [{msg.type}] {msg.text}")

        page.on("console", handle_console_message)

        # Navigate to page
        page.goto(URL)
        page.wait_for_load_state('networkidle')

        # Interact with the page (triggers console logs)
        page.click('text=Dashboard')
        page.wait_for_timeout(1000)

        browser.close()

    # Save console logs to file
    log_path.write_text('\n'.join(console_logs), encoding='utf-8')

    print(f"\nCaptured {len(console_logs)} console messages")
    print(f"Logs saved to: {log_path}")


if __name__ == '__main__':
    main()
