"""
Reusable Telethon helpers for posting to YOUR Telegram channel with FULL formatting:
rich captions (quote + expandable blockquotes + spoiler + inline links), scheduled
albums (photos AND video can be mixed in ONE media group), and a follow-up media post.

Battle-tested on a real launch campaign. Pairs with the `cards-creator`
skill (which builds the card PNGs) — see cards-creator/scripts/render_cards.py and
gen_card_images.py.

--------------------------------------------------------------------------------
KEY GOTCHAS (the whole reason this file exists)
--------------------------------------------------------------------------------
1. Telethon 1.39 html_parse SUPPORTS: <b> <i> <u> <s> <code> <pre> <a href> <blockquote>.
   It does NOT create a spoiler entity for <spoiler>/<tg-spoiler>, and it does NOT honour
   the `expandable`/`collapsed` attribute on <blockquote>. Markdown `||spoiler||` also fails.
   -> So: parse HTML normally, then MUTATE entities in Python:
        * expandable list  = MessageEntityBlockquote.collapsed = True
        * blurred spoiler  = append MessageEntitySpoiler(offset, length) manually
2. Entity offsets are UTF-16 code units -> use _u16(). Keep emoji OUT of spoiler spans
   (or the offsets must be measured on the exact substring, which _u16 does correctly).
3. When you pass formatting_entities=, DO NOT also pass parse_mode= (mutually exclusive).
4. Caption goes on the FIRST media item only. Caption limit: ~1024 normally, ~4096 on a
   Premium account. Check YOUR account: without Premium the cap is 1024 chars
   and long rich captions will be rejected.
5. Media group max = 10 items. Photos + a video CAN be mixed in one album.
6. schedule= wants a tz-aware datetime; build it in MSK (UTC+3), Telethon converts.
7. NEVER delete other scheduled posts (user content). list_scheduled() reports; you add.
8. channel identifier comes from $TG_CHANNEL (your channel @username, no @).
   Session file = ~/.claude/telegram_session (created on first login).
   API creds = env vars TELEGRAM_API_ID / TELEGRAM_API_HASH — get your own pair at
   https://my.telegram.org -> API development tools (free). Never reuse someone else's:
   Telegram revokes a key that logs in from two places at once.

--------------------------------------------------------------------------------
USAGE
--------------------------------------------------------------------------------
    import asyncio
    from tg_rich_post import client, schedule_album, schedule_media, list_scheduled, MSK
    from datetime import datetime

    HTML = '''Hook text...
    <blockquote>A pull-quote (stays a normal quote).</blockquote>
    <blockquote><b>📊 A LIST</b>
    line 1
    line 2</blockquote>
    Link: <a href="https://example.com">тут</a>.
    Если честно: SPOILER_SENTENCE_VERBATIM конец.'''

    async def main():
        c = client(); await c.start()
        _, sched = await list_scheduled(c, CHANNEL)   # report, never delete
        ids = await schedule_album(c, CHANNEL,
                  files=[f'png/series-{i:02d}.png' for i in range(1,10)],
                  html=HTML, when=datetime(2026,5,29,18,0,tzinfo=MSK),
                  spoilers=['SPOILER_SENTENCE_VERBATIM'])   # first blockquote stays a quote, rest expandable
        await schedule_media(c, CHANNEL, 'clip.mp4',
                  when=datetime(2026,5,29,18,5,tzinfo=MSK), caption='Короткий коммент')
        await c.disconnect()
    asyncio.run(main())
"""
import os
import sys

if __name__ == "__main__" and ("--help" in sys.argv or "-h" in sys.argv):
    # This file is a helper LIBRARY, not a CLI: import it. --help prints the
    # module docstring (gotchas + API) without touching Telegram or credentials.
    print(__doc__)
    print("Import it:  from tg_rich_post import client, build_caption, send_album, delete_scheduled")
    sys.exit(0)
from datetime import timezone, timedelta
from telethon import TelegramClient
from telethon.extensions.html import parse as html_parse
from telethon.tl.types import MessageEntityBlockquote, MessageEntitySpoiler
from telethon.tl.functions.messages import GetScheduledHistoryRequest, DeleteScheduledMessagesRequest

MSK = timezone(timedelta(hours=3))
SESSION = os.path.expanduser(os.getenv('TELEGRAM_SESSION', '~/.claude/telegram_session'))
# Your channel's @username without the @. Set TG_CHANNEL once in your environment.
CHANNEL = os.getenv('TG_CHANNEL', '')


def _creds():
    """api_id/api_hash from the environment. Get your own pair at my.telegram.org."""
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    if not api_id or not api_hash:
        raise RuntimeError(
            'TELEGRAM_API_ID / TELEGRAM_API_HASH are not set. Get your own pair at '
            'https://my.telegram.org -> API development tools (free), then export them '
            '(template: ~/.claude/templates/.credentials.master.env.example). '
            'Do not borrow someone else\'s pair: two simultaneous logins revoke it.'
        )
    return int(api_id), api_hash


def client():
    api_id, api_hash = _creds()
    return TelegramClient(SESSION, api_id, api_hash)


def _u16(s):
    return len(s.encode('utf-16-le')) // 2


def build_caption(html, expandable='all_but_first', spoilers=()):
    """Parse HTML -> (text, entities), then add what Telethon can't:
      expandable: 'all' | 'all_but_first' | 'none' | list[int] of 0-based blockquote indices to collapse
      spoilers:   iterable of exact tag-free substrings present in the parsed text to blur
    """
    text, ents = html_parse(html)
    bqs = sorted((e for e in ents if isinstance(e, MessageEntityBlockquote)), key=lambda e: e.offset)
    if expandable == 'all':
        idxs = range(len(bqs))
    elif expandable == 'all_but_first':
        idxs = range(1, len(bqs))
    elif expandable == 'none':
        idxs = []
    else:
        idxs = expandable
    for i in idxs:
        if 0 <= i < len(bqs):
            bqs[i].collapsed = True
    for phrase in spoilers:
        idx = text.find(phrase)
        if idx < 0:
            raise ValueError(f'spoiler phrase not found in parsed text: {phrase[:50]!r}')
        ents.append(MessageEntitySpoiler(_u16(text[:idx]), _u16(phrase)))
    return text, ents


async def list_scheduled(c, channel=None):
    """Return (entity, sorted_messages). Report only — never delete user content."""
    channel = channel or CHANNEL
    if not channel:
        raise RuntimeError("No channel: pass channel= or set TG_CHANNEL to your channel's @username (no @).")
    e = await c.get_entity(channel)
    s = await c(GetScheduledHistoryRequest(peer=e, hash=0))
    return e, sorted(s.messages, key=lambda m: m.date)


async def schedule_album(c, channel, files, html, when, spoilers=(), expandable='all_but_first'):
    """Schedule a media group (<=10 photos/videos) with a rich caption on the first item."""
    e = await c.get_entity(channel)
    text, ents = build_caption(html, expandable, spoilers)
    if len(text) > 4096:
        raise ValueError(f'caption {len(text)} chars > 4096 (Premium cap)')
    for f in files:
        assert os.path.exists(f), f'missing file: {f}'
    msgs = await c.send_file(e, file=list(files), caption=text,
                             formatting_entities=ents, schedule=when)
    return [m.id for m in msgs] if isinstance(msgs, list) else [msgs.id]


async def schedule_media(c, channel, file, when, caption='', html=None,
                         spoilers=(), expandable='all_but_first'):
    """Schedule a single photo/video. Pass html= for a rich caption, else plain caption=."""
    e = await c.get_entity(channel)
    assert os.path.exists(file), f'missing file: {file}'
    if html:
        text, ents = build_caption(html, expandable, spoilers)
        m = await c.send_file(e, file=file, caption=text, formatting_entities=ents, schedule=when)
    else:
        m = await c.send_file(e, file=file, caption=caption, schedule=when)
    return m.id


async def delete_scheduled(c, channel, ids):
    """Delete OWN scheduled posts by id (e.g. to re-schedule an edited version)."""
    e = await c.get_entity(channel)
    await c(DeleteScheduledMessagesRequest(peer=e, id=list(ids)))


# ---- standard reusable footer (3 links) — EDIT THIS ONCE for your channel ----
# Template. Replace links/labels with your own, or drop lines you don't have.
FOOTER_HTML = (
    '⚡️ <a href="https://t.me/your_channel">&lt;Название канала&gt;</a>\n'
    '📲 <a href="https://t.me/your_bot">&lt;что даёт твой бот&gt;</a>\n'
    '📰 <a href="https://your-site.example.com/">&lt;что на твоём сайте&gt;</a>'
)
