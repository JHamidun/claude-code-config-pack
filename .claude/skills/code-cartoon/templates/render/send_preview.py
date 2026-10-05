"""Owner-only silent preview in Telegram: a header message, then each video with its caption (Telegram HTML markup).

    python render/send_preview.py --chat <chat id> out/hdr.html out/preview_land.mp4:out/cap_land.html [video:caption ...]
    python render/send_preview.py --chat <chat id> --dry-run out/hdr.html out/preview_land.mp4:out/cap_land.html

Token: BOT_TOKEN or TELEGRAM_BOT_TOKEN from the environment, else TELEGRAM_BOT_TOKEN in ~/.claude/.credentials.master.env;
it is never printed. Chat: --chat, else PREVIEW_CHAT_ID from the environment or that file. Bot API limits: video ≤ 50 MB
(re-encode a preview first, workflow.md § 12), caption ≤ 1024 characters after markup. Markup: <b>, <i>, <u>, <s>, <a>,
<code>, <blockquote>. Every send prints ok, the message id and the entity types Telegram parsed — a caption that came out
as a wall of text shows here as an empty entity list.
"""
import argparse
import html
import json
import os
import re
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path

CRED = Path.home() / '.claude/.credentials.master.env'


def cred(*names):
    for n in names:
        if os.environ.get(n):
            return os.environ[n].strip()
    if CRED.exists():
        lines = CRED.read_text(encoding='utf-8').splitlines()
        for n in names:
            for line in lines:
                if line.startswith(n + '='):
                    v = line.split('=', 1)[1].strip().strip('"').strip("'")
                    if v:
                        return v
    return None


def visible_len(markup):
    return len(html.unescape(re.sub(r'<[^>]+>', '', markup)).encode('utf-16-le')) // 2


def call(token, method, fields, files=None):
    boundary = uuid.uuid4().hex
    body = b''
    for k, v in fields.items():
        body += f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
    for k, path in (files or {}).items():
        body += (f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"; filename="{os.path.basename(path)}"\r\n'
                 f'Content-Type: video/mp4\r\n\r\n').encode()
        body += Path(path).read_bytes() + b'\r\n'
    body += f'--{boundary}--\r\n'.encode()
    req = urllib.request.Request(f'https://api.telegram.org/bot{token}/{method}', data=body,
                                 headers={'Content-Type': f'multipart/form-data; boundary={boundary}'})
    try:
        return json.loads(urllib.request.urlopen(req, timeout=600).read())
    except urllib.error.HTTPError as e:                # Telegram explains the refusal in the body
        return json.loads(e.read() or b'{}')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('header')
    ap.add_argument('videos', nargs='*', help='video.mp4:caption.html')
    ap.add_argument('--chat', default=None)
    ap.add_argument('--dry-run', action='store_true', help='check files, sizes and caption lengths; send nothing')
    a = ap.parse_args()
    hdr = Path(a.header).read_text(encoding='utf-8').strip()
    items = []
    for it in a.videos:
        m = re.match(r'^(.*?\.mp4):(.+)$', it, re.I)        # the video path may carry a drive letter (D:\...)
        if not m:
            raise SystemExit(f'expected video.mp4:caption.html, got {it}')
        path, cap = m.groups()
        caption = Path(cap).read_text(encoding='utf-8').strip()
        mb = Path(path).stat().st_size / 2 ** 20
        n = visible_len(caption)
        print(f'{os.path.basename(path)}: {mb:.1f} MB, caption {n} chars' + ('  <-- over 50 MB' if mb > 50 else '')
              + ('  <-- caption over 1024' if n > 1024 else ''))
        items.append((path, caption))
    if a.dry_run:
        print(f'header {visible_len(hdr)} chars; dry run, nothing sent')
        return
    token = cred('BOT_TOKEN', 'TELEGRAM_BOT_TOKEN')
    chat = a.chat or cred('PREVIEW_CHAT_ID')
    if not token or not chat:
        raise SystemExit('need a bot token (BOT_TOKEN / TELEGRAM_BOT_TOKEN) and a chat (--chat / PREVIEW_CHAT_ID)')
    r = call(token, 'sendMessage', {'chat_id': chat, 'text': hdr, 'parse_mode': 'HTML', 'disable_notification': 'true',
                                    'disable_web_page_preview': 'true'})
    print('header', r.get('ok'), (r.get('result') or {}).get('message_id'), r.get('description', ''))
    for path, caption in items:
        port = 'port' in os.path.basename(path)
        fields = {'chat_id': chat, 'caption': caption, 'parse_mode': 'HTML', 'supports_streaming': 'true',
                  'disable_notification': 'true', 'width': '1080' if port else '1920', 'height': '1920' if port else '1080'}
        r = call(token, 'sendVideo', fields, {'video': path})
        res = r.get('result') or {}
        ents = {}
        for e in res.get('caption_entities') or []:
            ents[e['type']] = ents.get(e['type'], 0) + 1
        print(os.path.basename(path), r.get('ok'), res.get('message_id'), r.get('description', ''), 'entities', ents)


if __name__ == '__main__':
    sys.exit(main())
