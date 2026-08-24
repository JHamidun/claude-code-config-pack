"""Start HTTP server for Playwright to access HTML files.

Usage:
    python start_server.py --dir /path/to/html/files --port 8889

Playwright itself opens file:// fine. A server is needed only when the page pulls its
own resources: fetch/XHR to local JSON and <script type="module"> are blocked by the
browser's CORS policy under file://.
Always use 127.0.0.1 (NOT localhost) — Playwright sometimes fails to resolve localhost.
"""

import http.server
import argparse
import os


def start_server(directory: str, port: int = 8889):
    os.chdir(directory)
    print(f'Serving {directory} at http://127.0.0.1:{port}/')
    print('Press Ctrl+C to stop')

    server = http.server.HTTPServer(
        ('127.0.0.1', port),
        http.server.SimpleHTTPRequestHandler
    )
    server.serve_forever()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Start HTTP server for Playwright')
    parser.add_argument('--dir', required=True, help='Directory with HTML files')
    parser.add_argument('--port', type=int, default=8889, help='Port (default: 8889)')
    args = parser.parse_args()

    start_server(args.dir, args.port)
