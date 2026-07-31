"""Post / replace channel STORIES for @yourchannel with carousel cards adapted to 9:16.

SELF-CONTAINED: depends only on telethon + this skill's files (no cross-skill imports).
Creds/session come from the global ~/.claude environment (every skill uses these):
  ~/.claude/.credentials.master.env  -> TELEGRAM_API_ID / TELEGRAM_API_HASH
  ~/.claude/telegram_session.session -> authorized Telethon session

WHY THIS EXISTS
---------------
Carousel cards are 1080x1350 (4:5). Telegram STORIES are 1080x1920 (9:16). If you post a
4:5 image as a story, Telegram zooms it to fill the height and CROPS THE SIDES (e.g. the
headline "DYNAMIC" shows as "NAMIC"). Fix: first run build_story_frames.py to letterbox each
card onto a seamless 9:16 canvas (edge rows stretched + blurred into the top/bottom bands),
then post THOSE (story_png/story-NN.png), not png/series-NN.png.

GOTCHAS (learned 2026-05-29, hard-won)
--------------------------------------
1. DAILY STORY LIMIT is tied to channel BOOST LEVEL. @yourchannel was level 8 and could
   post ~8 stories/day; the 9th+ fail with `RPCError 400: BOOSTS_REQUIRED` even though
   GetBoostsStatus shows a healthy level. CanSendStoryRequest also raises BOOSTS_REQUIRED
   once the cap is hit. The cap counts stories SENT in the period, not currently active —
   deleting does NOT free a slot the same day. Plan the card count to the boost level.
2. To FIX already-posted stories without spending quota, use EditStoryRequest to swap the
   media in place (see cmd 'edit'). This is the ONLY way to repair live stories same-day.
3. EditStoryRequest asserts caption and entities must BOTH be set or BOTH be None. To keep an
   existing caption while swapping media, pass media ONLY (omit caption/entities entirely).
4. Session sqlite locks: we connect on a COPY of the .session file (see _client()).
5. period must be 86400 (24h) for channel stories; privacy_rules=[InputPrivacyValueAllowAll()].

USAGE
-----
  python build_story_frames.py                 # png/series-*.png -> story_png/story-*.png
  python post_stories.py post   <channel> [cover_caption]   # post all story_png/story-*.png
  python post_stories.py edit   <channel> <id1,id2,...>     # swap media of existing story ids
  python post_stories.py list   <channel>      # boost level, quota, active story ids
Story frames are read from $STORY_DIR or ./story_png (CWD), matching build_story_frames.py.
"""
import sys, io, os, asyncio, shutil, random
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from telethon import TelegramClient
from telethon.tl.functions.premium import GetBoostsStatusRequest
from telethon.tl.functions.stories import (SendStoryRequest, EditStoryRequest,
                                           GetPeerStoriesRequest, CanSendStoryRequest)
from telethon.tl.types import InputPrivacyValueAllowAll, InputMediaUploadedPhoto

CRED = os.path.expanduser('~/.claude/.credentials.master.env')
SESSION_MAIN = os.path.expanduser('~/.claude/telegram_session.session')
STORY_DIR = os.environ.get('STORY_DIR', os.path.join(os.getcwd(), 'story_png'))


def _creds():
    c = open(CRED, encoding='utf-8').read()
    api_id = int(c.split('TELEGRAM_API_ID=')[1].split('\n')[0].strip())
    api_hash = c.split('TELEGRAM_API_HASH=')[1].split('\n')[0].strip()
    return api_id, api_hash


def _client():
    """Connect on a COPY of the authorized session to dodge sqlite locks. Returns (client, copy_path)."""
    cp = os.path.expanduser('~/.claude/telegram_session_cardsst.session')
    shutil.copy(SESSION_MAIN, cp)
    api_id, api_hash = _creds()
    return TelegramClient(cp[:-len('.session')], api_id, api_hash), cp


def _frames():
    return sorted(os.path.join(STORY_DIR, f) for f in os.listdir(STORY_DIR)
                  if f.startswith('story-') and f.endswith('.png'))


async def run(cmd, channel, ids=None, cover_caption=None):
    c, cp = _client(); await c.start()
    e = await c.get_entity(channel)
    print('channel:', e.title)

    if cmd == 'list':
        b = await c(GetBoostsStatusRequest(peer=e))
        print(f'boost level={b.level} boosts={b.boosts}')
        try:
            r = await c(CanSendStoryRequest(peer=e)); print('can_send:', r)
        except Exception as ex:
            print('can_send: BLOCKED ->', type(ex).__name__, ex)
        ps = await c(GetPeerStoriesRequest(peer=e))
        items = ps.stories.stories if hasattr(ps.stories, 'stories') else []
        print('active ids:', [s.id for s in items])

    elif cmd == 'post':
        for i, f in enumerate(_frames()):
            up = await c.upload_file(f)
            kw = dict(peer=e, media=InputMediaUploadedPhoto(file=up),
                      privacy_rules=[InputPrivacyValueAllowAll()],
                      random_id=random.randrange(1 << 62), period=86400)
            if i == 0 and cover_caption:
                kw['caption'] = cover_caption
            try:
                await c(SendStoryRequest(**kw)); print(f'  posted {os.path.basename(f)}')
            except Exception as ex:
                print(f'  BLOCKED {os.path.basename(f)} -> {type(ex).__name__} {ex}')

    elif cmd == 'edit':
        frames = _frames()
        for sid, f in zip(ids, frames):
            up = await c.upload_file(f)
            try:  # media-only swap preserves the existing caption (no quota spent)
                await c(EditStoryRequest(peer=e, id=sid, media=InputMediaUploadedPhoto(file=up)))
                print(f'  story {sid} <- {os.path.basename(f)} OK')
            except Exception as ex:
                print(f'  story {sid} ERR {type(ex).__name__} {ex}')

    await c.disconnect()
    os.remove(cp)


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'list'
    channel = sys.argv[2] if len(sys.argv) > 2 else 'your_username'
    arg3 = sys.argv[3] if len(sys.argv) > 3 else None
    ids = [int(x) for x in arg3.split(',')] if (cmd == 'edit' and arg3) else None
    cap = arg3 if (cmd == 'post' and arg3) else None
    asyncio.run(run(cmd, channel, ids, cap))
