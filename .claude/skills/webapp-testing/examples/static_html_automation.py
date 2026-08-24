"""Example: automating a local HTML file through a file:// URL.

Запускать как скрипт. При импорте не делает НИЧЕГО: браузер поднимается только
в main(), иначе `import static_html_automation` (линтер, автодополнение) открывал
бы Chromium.

Путь к странице — аргументом или переменной окружения, а не правкой кода:
    python static_html_automation.py path/to/your/file.html
    WEBAPP_TEST_HTML  тот же путь переменной окружения
    WEBAPP_TEST_OUT   куда класть скриншоты (умолчание ./webapp-test-out)

`Path.as_uri()` вместо ручного `file://` + os.path.abspath: на Windows абсолютный
путь начинается с диска (`C:\\...`), и склейка `f'file://{path}'` даёт неверный URL.
"""
# UTF-8 на выход. Консоль Windows по умолчанию cp1251/cp866/cp1252, и первый же
# не-ASCII символ (кириллица, →, ✓) валит процесс UnicodeEncodeError — обычно на
# --help, то есть ДО любой полезной работы. errors="replace" оставляет вывод
# читаемым, если терминал всё же не UTF-8.
import sys as _sys
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT_DIR = Path(os.environ.get("WEBAPP_TEST_OUT") or (Path.cwd() / "webapp-test-out"))


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    raw = argv[0] if argv else os.environ.get("WEBAPP_TEST_HTML", "")
    if not raw:
        print(__doc__)
        return 2

    html_file = Path(raw).expanduser().resolve()
    if not html_file.is_file():
        print(f"ОТКАЗ: нет файла {html_file}")
        return 2

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    file_url = html_file.as_uri()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1920, 'height': 1080})

        # Navigate to local HTML file
        page.goto(file_url)

        # Take screenshot
        page.screenshot(path=str(OUT_DIR / "static_page.png"), full_page=True)

        # Interact with elements
        page.click('text=Click Me')
        page.fill('#name', 'John Doe')
        page.fill('#email', 'john@example.com')

        # Submit form
        page.click('button[type="submit"]')
        page.wait_for_timeout(500)

        # Take final screenshot
        page.screenshot(path=str(OUT_DIR / "after_submit.png"), full_page=True)

        browser.close()

    print(f"Static HTML automation completed! Artifacts: {OUT_DIR}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
