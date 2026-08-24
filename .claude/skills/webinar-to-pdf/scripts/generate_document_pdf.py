"""Generate PDF from HTML document using Playwright page.pdf().

Usage:
    python generate_document_pdf.py --url http://127.0.0.1:8889/document.html --output document.pdf

For text documents (summaries, instructions, transcripts) with normal flow layout.
"""

import asyncio
import argparse
import os
from playwright.async_api import async_playwright


async def generate_document_pdf(html_url: str, output_path: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(html_url, wait_until='networkidle')
        await page.pdf(
            path=output_path,
            format='A4',
            print_background=True,
            margin={
                'top': '10mm',
                'bottom': '10mm',
                'left': '10mm',
                'right': '10mm'
            }
        )
        await browser.close()

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f'PDF created: {output_path} ({size_mb:.1f} MB)')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate PDF from HTML document')
    parser.add_argument('--url', required=True, help='URL of the HTML document')
    parser.add_argument('--output', required=True, help='Output PDF path')
    args = parser.parse_args()

    asyncio.run(generate_document_pdf(args.url, args.output))
