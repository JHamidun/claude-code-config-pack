#!/usr/bin/env python3
"""
pplx-max.py — Perplexity Max subscription wrapper with Claude Opus 4.7 Thinking.

Usage:
  python pplx-max.py "your query here"
  python pplx-max.py --mode reasoning "deep question"     # default
  python pplx-max.py --mode pro "broad search"            # pro mode
  python pplx-max.py --mode "deep research" "research"    # deep research (slow)
"""
import os
import sys
import io
import json
import argparse
from dotenv import load_dotenv

# Force UTF-8 stdout on Windows (cp1251 default breaks on Unicode)
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

load_dotenv(os.path.expanduser('~/.claude/.credentials.master.env'))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('query', nargs='+', help='Search query')
    ap.add_argument('--mode', default='reasoning',
                    choices=['auto', 'pro', 'reasoning', 'deep research'])
    ap.add_argument('--model', default=None,
                    help='Override model (default: claude-4.7-opus-thinking for reasoning)')
    args = ap.parse_args()

    query = ' '.join(args.query)
    mode = args.mode
    model = args.model
    if model is None:
        if mode == 'reasoning':
            model = 'claude-4.7-opus-thinking'
        elif mode == 'pro':
            model = 'claude-4.7-opus'

    cookies_str = os.getenv('PERPLEXITY_COOKIES', '')
    if not cookies_str:
        print('ERROR: PERPLEXITY_COOKIES not set', file=sys.stderr)
        sys.exit(1)

    cookies = json.loads(cookies_str)
    from perplexity import Client
    c = Client(cookies)

    result = c.search(query, mode=mode, model=model, stream=False)

    if not isinstance(result, dict):
        print(f'Unexpected result type: {type(result)}', file=sys.stderr)
        sys.exit(2)

    answer = result.get('answer', '')
    print(answer)

    # Sources
    sources = []
    for ch in result.get('chunks', []):
        if isinstance(ch, dict):
            url = ch.get('url')
            title = ch.get('title') or ch.get('name', '')
            if url:
                sources.append((title[:80], url))

    if not sources:
        srcs_raw = result.get('sources') or []
        if isinstance(srcs_raw, str):
            try:
                srcs_raw = json.loads(srcs_raw)
            except Exception:
                srcs_raw = []
        for s in srcs_raw:
            if isinstance(s, dict):
                url = s.get('url')
                title = s.get('title') or s.get('name', '')
                if url:
                    sources.append((title[:80], url))

    if sources:
        print('\n--- SOURCES ---')
        seen = set()
        for i, (title, url) in enumerate(sources, 1):
            if url in seen:
                continue
            seen.add(url)
            print(f'[{i}] {title}\n    {url}')


if __name__ == '__main__':
    main()
