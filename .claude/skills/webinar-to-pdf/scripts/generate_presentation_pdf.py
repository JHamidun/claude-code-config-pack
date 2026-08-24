"""Generate PDF from HTML slide presentation using screenshot approach.

Usage:
    python generate_presentation_pdf.py --url http://127.0.0.1:8889/presentation.html --output presentation.pdf

Each slide is captured as PNG screenshot, converted to JPEG (quality=90),
then combined into a single PDF via img2pdf.
"""

import asyncio
import argparse
import io
import os
import sys

# Зависимости названы поимённо: голый `ModuleNotFoundError: No module named 'img2pdf'`
# на верхнем уровне модуля падал ДО разбора аргументов, то есть даже `--help` не
# отвечал, а имя пакета ничего не говорило о том, чем его ставить и зачем он тут.
_MISSING = []
try:
    from playwright.async_api import async_playwright
except ImportError as _e:
    async_playwright = None
    _MISSING.append(('playwright', 'pip install playwright && playwright install chromium', str(_e)))
try:
    from PIL import Image
except ImportError as _e:
    Image = None
    _MISSING.append(('pillow', 'pip install pillow', str(_e)))
try:
    import img2pdf
except ImportError as _e:
    img2pdf = None
    _MISSING.append(('img2pdf', 'pip install img2pdf', str(_e)))


def _require_deps() -> None:
    if not _MISSING:
        return
    lines = ['[generate_presentation_pdf] не хватает зависимостей:']
    for name, cmd, err in _MISSING:
        lines.append(f'  • {name}: {err}')
        lines.append(f'       {cmd}')
    lines.append('  Все три перечислены в requirements.txt пака '
                 '(pip install -r requirements.txt).')
    sys.exit('\n'.join(lines))


async def generate_presentation_pdf(html_url: str, output_path: str, quality: int = 90):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={'width': 1920, 'height': 1080})
        await page.goto(html_url, wait_until='networkidle')
        await asyncio.sleep(2)  # Wait for images to load

        # CRITICAL: Disable ALL animations/transitions and force opacity
        # Without this, slides with CSS animations (slideIn, fade) appear empty/transparent
        await page.evaluate('''
            const style = document.createElement('style');
            style.textContent = `
                *, *::before, *::after {
                    animation: none !important;
                    animation-delay: 0s !important;
                    animation-duration: 0s !important;
                    transition: none !important;
                    transition-delay: 0s !important;
                    transition-duration: 0s !important;
                }
                .slide.active,
                .slide.active * {
                    opacity: 1 !important;
                    visibility: visible !important;
                    transform: none !important;
                }
            `;
            document.head.appendChild(style);

            // Hide UI elements (fullscreen/avatar buttons, particle canvas, progress bar)
            document.querySelectorAll('#fullscreenBtn, #avatarBtn, #progressBar, canvas').forEach(el => {
                el.style.display = 'none';
            });
        ''')

        total = await page.evaluate('document.querySelectorAll(".slide").length')
        print(f'Total slides: {total}')

        screenshots = []
        for i in range(total):
            await page.evaluate(f'''
                const slides = document.querySelectorAll('.slide');
                slides.forEach(s => {{
                    s.classList.remove('active');
                    s.style.display = 'none';
                    s.style.visibility = 'hidden';
                    s.style.opacity = '0';
                }});
                const target = slides[{i}];
                target.classList.add('active');
                target.style.display = 'flex';
                target.style.visibility = 'visible';
                target.style.opacity = '1';
                // Force opacity on ALL children with low opacity
                target.querySelectorAll('*').forEach(child => {{
                    const cs = getComputedStyle(child);
                    if (parseFloat(cs.opacity) < 0.5) {{
                        child.style.opacity = '1';
                    }}
                }});
            ''')
            await asyncio.sleep(0.3)

            png_bytes = await page.screenshot(type='png', full_page=False)

            img = Image.open(io.BytesIO(png_bytes))
            jpg_buffer = io.BytesIO()
            img.convert('RGB').save(jpg_buffer, format='JPEG', quality=quality)
            screenshots.append(jpg_buffer.getvalue())

            if (i + 1) % 10 == 0:
                print(f'  Captured {i+1}/{total} slides')

        await browser.close()
        print(f'All {total} slides captured')

        pdf_bytes = img2pdf.convert(
            screenshots,
            layout_fun=img2pdf.get_fixed_dpi_layout_fun((96, 96))
        )

        with open(output_path, 'wb') as f:
            f.write(pdf_bytes)

        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f'PDF created: {output_path} ({size_mb:.1f} MB, {total} pages)')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate PDF from HTML slides')
    parser.add_argument('--url', required=True, help='URL of the HTML presentation')
    parser.add_argument('--output', required=True, help='Output PDF path')
    parser.add_argument('--quality', type=int, default=90, help='JPEG quality (default: 90)')
    args = parser.parse_args()

    # После разбора аргументов: `--help` отвечает даже на машине без зависимостей.
    _require_deps()
    asyncio.run(generate_presentation_pdf(args.url, args.output, args.quality))
