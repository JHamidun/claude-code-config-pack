#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Postiz public API client — stdlib only, no dependencies.

Postiz is self-hosted: point it at YOUR instance.

    POSTIZ_URL=http://localhost:4007     # base URL of your Postiz, no trailing slash
    POSTIZ_API_KEY=...                   # Settings -> Developers -> Public API

Both go into ~/.claude/.credentials.master.env (or plain environment variables).

    python postiz_cli.py channels
    python postiz_cli.py publish "text" [--platforms x,linkedin]
    python postiz_cli.py schedule 2026-09-01T10:00:00Z "text" [--platforms x]
    python postiz_cli.py list [--from 2026-08-01] [--to 2026-08-31]
    python postiz_cli.py delete <post_id>
    python postiz_cli.py upload <file>

Auth header carries the raw key with NO "Bearer" prefix — that is a real Postiz
quirk, adding the prefix returns 401.
"""
import argparse
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request
import uuid

TIMEOUT = 60


def _load_env_file():
    """Read ~/.claude/.credentials.master.env if the vars are not already set."""
    path = os.path.join(os.path.expanduser('~'), '.claude', '.credentials.master.env')
    if not os.path.isfile(path):
        return
    try:
        with open(path, encoding='utf-8') as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                k, v = line.split('=', 1)
                k, v = k.strip(), v.strip()
                if k and v and k not in os.environ:
                    os.environ[k] = v
    except OSError:
        pass


def config():
    _load_env_file()
    url = (os.getenv('POSTIZ_URL') or '').rstrip('/')
    key = os.getenv('POSTIZ_API_KEY') or ''
    missing = [n for n, v in (('POSTIZ_URL', url), ('POSTIZ_API_KEY', key)) if not v]
    if missing:
        sys.exit(
            'Not configured: %s.\n'
            'Postiz is self-hosted — deploy your own instance first (see SKILL.md),\n'
            'then put POSTIZ_URL and POSTIZ_API_KEY into ~/.claude/.credentials.master.env.'
            % ', '.join(missing)
        )
    return url + '/public/v1', key


def request(method, path, key, body=None, raw=None, content_type=None):
    req = urllib.request.Request(path, method=method)
    req.add_header('Authorization', key)  # raw key, NO "Bearer"
    data = raw
    if body is not None:
        data = json.dumps(body).encode('utf-8')
        req.add_header('Content-Type', 'application/json')
    if content_type:
        req.add_header('Content-Type', content_type)
    try:
        with urllib.request.urlopen(req, data=data, timeout=TIMEOUT) as resp:
            text = resp.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        detail = e.read().decode('utf-8', 'replace')[:800]
        hint = ''
        if e.code == 401:
            hint = '\nHint: the Authorization header takes the raw key, without "Bearer ".'
        if e.code == 429:
            hint = '\nHint: default rate limit is 30 requests/hour (API_LIMIT env in your deploy).'
        sys.exit('HTTP %s from %s\n%s%s' % (e.code, path, detail, hint))
    except urllib.error.URLError as e:
        sys.exit('Cannot reach %s: %s\nIs your Postiz instance running and POSTIZ_URL correct?'
                 % (path, e.reason))
    try:
        return json.loads(text) if text.strip() else {}
    except ValueError:
        return {'raw': text}


def get_integrations(base, key):
    data = request('GET', base + '/integrations', key)
    return data if isinstance(data, list) else data.get('integrations', data)


def pick(integrations, platforms):
    """platforms: comma-separated identifiers ('x,linkedin'); empty = all."""
    if not platforms:
        return integrations
    wanted = {p.strip().lower() for p in platforms.split(',') if p.strip()}
    chosen = [i for i in integrations
              if str(i.get('identifier', '')).lower() in wanted
              or str(i.get('name', '')).lower() in wanted]
    if not chosen:
        sys.exit('None of the requested platforms are connected: %s\nConnected: %s'
                 % (', '.join(sorted(wanted)),
                    ', '.join(sorted({str(i.get('identifier')) for i in integrations})) or '(none)'))
    return chosen


def build_posts(integrations, text):
    posts = []
    for i in integrations:
        posts.append({
            'integration': {'id': i['id']},
            'value': [{'content': text}],
            'group': 'post',
            'settings': {'__type': i.get('identifier', 'x')},
        })
    return posts


def cmd_channels(args, base, key):
    for i in get_integrations(base, key):
        print('%-38s %-14s %s' % (i.get('id'), i.get('identifier'), i.get('name')))


def cmd_publish(args, base, key):
    ints = pick(get_integrations(base, key), args.platforms)
    body = {'type': 'now', 'posts': build_posts(ints, args.text)}
    print(json.dumps(request('POST', base + '/posts', key, body), ensure_ascii=False, indent=2))


def cmd_schedule(args, base, key):
    ints = pick(get_integrations(base, key), args.platforms)
    body = {'type': 'schedule', 'date': args.date, 'posts': build_posts(ints, args.text)}
    print(json.dumps(request('POST', base + '/posts', key, body), ensure_ascii=False, indent=2))


def cmd_list(args, base, key):
    q = []
    if args.date_from:
        q.append('startDate=' + args.date_from)
    if args.date_to:
        q.append('endDate=' + args.date_to)
    path = base + '/posts' + ('?' + '&'.join(q) if q else '')
    print(json.dumps(request('GET', path, key), ensure_ascii=False, indent=2))


def cmd_delete(args, base, key):
    print(json.dumps(request('DELETE', base + '/posts/' + args.post_id, key),
                     ensure_ascii=False, indent=2))


def cmd_upload(args, base, key):
    path = args.file
    if not os.path.isfile(path):
        sys.exit('No such file: ' + path)
    boundary = uuid.uuid4().hex
    ctype = mimetypes.guess_type(path)[0] or 'application/octet-stream'
    with open(path, 'rb') as fh:
        payload = fh.read()
    body = b''.join([
        ('--%s\r\n' % boundary).encode(),
        ('Content-Disposition: form-data; name="file"; filename="%s"\r\n'
         % os.path.basename(path)).encode(),
        ('Content-Type: %s\r\n\r\n' % ctype).encode(),
        payload,
        ('\r\n--%s--\r\n' % boundary).encode(),
    ])
    out = request('POST', base + '/upload', key, raw=body,
                  content_type='multipart/form-data; boundary=' + boundary)
    print(json.dumps(out, ensure_ascii=False, indent=2))


def main():
    p = argparse.ArgumentParser(description='Postiz public API client (self-hosted).')
    sub = p.add_subparsers(dest='cmd', required=True)

    sub.add_parser('channels', help='list connected integrations')

    sp = sub.add_parser('publish', help='publish now')
    sp.add_argument('text')
    sp.add_argument('--platforms', default='', help='comma-separated, e.g. x,linkedin')

    sp = sub.add_parser('schedule', help='schedule for later')
    sp.add_argument('date', help='ISO 8601, e.g. 2026-09-01T10:00:00Z')
    sp.add_argument('text')
    sp.add_argument('--platforms', default='')

    sp = sub.add_parser('list', help='list posts')
    sp.add_argument('--from', dest='date_from', default='')
    sp.add_argument('--to', dest='date_to', default='')

    sp = sub.add_parser('delete', help='delete a post')
    sp.add_argument('post_id')

    sp = sub.add_parser('upload', help='upload media')
    sp.add_argument('file')

    args = p.parse_args()
    base, key = config()
    {'channels': cmd_channels, 'publish': cmd_publish, 'schedule': cmd_schedule,
     'list': cmd_list, 'delete': cmd_delete, 'upload': cmd_upload}[args.cmd](args, base, key)


if __name__ == '__main__':
    main()
