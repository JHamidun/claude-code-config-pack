#!/usr/bin/env python3
"""
pplx-max.py — Perplexity Max subscription wrapper with Claude Opus 4.7 Thinking.

Usage:
  python pplx-max.py "your query here"
  python pplx-max.py --mode reasoning "deep question"     # default
  python pplx-max.py --mode pro "broad search"            # pro mode
  python pplx-max.py --mode "deep research" "research"    # deep research (slow)
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
import io
import json
import argparse

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:  # не молчим: без него не подхватятся креды
    print('ERROR: python-dotenv не установлен. pip install python-dotenv perplexity',
          file=sys.stderr)
    raise SystemExit(1)

# Force UTF-8 stdout on Windows (cp1251 default breaks on Unicode)
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

load_dotenv(os.path.expanduser('~/.claude/.credentials.master.env'))


def _as_dict(value):
    """Строка с JSON внутри встречается в нескольких полях ответа — разворачиваем."""
    if isinstance(value, str):
        try:
            return json.loads(value)
        except Exception:
            return None
    return value


def extract_answer(result):
    """Достать текст ответа.

    Форма ответа у Perplexity менялась: раньше текст лежал в result['answer'],
    сейчас — в result['blocks'][i]['markdown_block']['answer']. Наивное
    result.get('answer', '') на новой форме отдаёт пустую строку, и скрипт
    печатает пустоту с кодом 0 — то есть поломка выглядит как успешный пустой
    ответ. Поэтому перебираем известные формы, а не одну.
    """
    direct = result.get('answer')
    nested = _as_dict(direct)          # answer иногда приходит JSON-строкой
    if isinstance(nested, dict):       # проверяем ДО сырой строки, иначе напечатаем JSON
        for key in ('answer', 'text'):
            val = nested.get(key)
            if isinstance(val, str) and val.strip():
                return val
    if isinstance(direct, str) and direct.strip():
        return direct

    parts = []
    for block in result.get('blocks') or []:
        if not isinstance(block, dict):
            continue
        md = block.get('markdown_block') or {}
        val = md.get('answer')
        if isinstance(val, str) and val.strip():
            parts.append(val)
            continue
        for chunk in md.get('chunks') or []:
            if isinstance(chunk, str):
                parts.append(chunk)
    if parts:
        return ''.join(parts) if len(parts) > 1 else parts[0]

    for key in ('text', 'output', 'content'):
        val = result.get(key)
        if isinstance(val, str) and val.strip():
            return val
    return ''


def extract_sources(result):
    """Ссылки: из chunks, из sources и из web_result_block внутри blocks."""
    sources = []

    def add(title, url):
        if url:
            sources.append((str(title or '')[:80], url))

    for ch in result.get('chunks') or []:
        if isinstance(ch, dict):
            add(ch.get('title') or ch.get('name'), ch.get('url'))

    srcs_raw = _as_dict(result.get('sources')) or result.get('sources') or []
    if isinstance(srcs_raw, list):
        for s in srcs_raw:
            if isinstance(s, dict):
                add(s.get('title') or s.get('name'), s.get('url'))

    for block in result.get('blocks') or []:
        if not isinstance(block, dict):
            continue
        web = block.get('web_result_block') or {}
        for s in web.get('web_results') or []:
            if isinstance(s, dict):
                add(s.get('name') or s.get('title'), s.get('url'))

    return sources


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

    answer = extract_answer(result)
    if not answer.strip():
        # Пустой ответ — это ОШИБКА, а не результат. Молчаливый exit 0 хуже
        # отсутствия инструмента: пустота уезжает дальше по пайплайну как факт.
        print('ERROR: Perplexity вернул ответ, из которого не удалось достать текст.\n'
              f'  Ключи верхнего уровня: {sorted(result.keys())}\n'
              '  Обычно это значит одно из двух: протухли PERPLEXITY_COOKIES\n'
              '  (перелогинься и обнови session-token) либо изменилась форма ответа —\n'
              '  тогда смотри, где теперь лежит текст, и допиши ветку в extract_answer().',
              file=sys.stderr)
        sys.exit(3)

    print(answer)

    sources = extract_sources(result)
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
