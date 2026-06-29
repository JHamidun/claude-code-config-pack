"""Add missing stickers to an existing pack via /addsticker.

Compares pack's present emojis with mapping; adds whatever's missing.
Resumable via progress file.

Usage:
    python add_to_pack.py --short mypack --webm-dir ./webms --mapping mapping.json
    python add_to_pack.py --short mypack --webm-dir ./webms --mapping mapping.json \
        --progress ./done.txt
"""
import sys, io, asyncio, os, argparse
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
from telethon import TelegramClient
from telethon.errors import FloodWaitError
from telethon.tl.functions.messages import GetStickerSetRequest
from telethon.tl.types import InputStickerSetShortName

from _telethon_base import (load_credentials, load_mapping, norm_emoji,
                            load_progress, mark_done)


async def main(short, webm_dir, mapping_path, progress_path):
    api_id, api_hash, session = load_credentials()
    client = TelegramClient(session, api_id, api_hash)
    await client.start()
    pack = await client(GetStickerSetRequest(
        stickerset=InputStickerSetShortName(short_name=short), hash=0))
    emoji_by_docid = {}
    for pk in pack.packs:
        for did in pk.documents:
            emoji_by_docid.setdefault(did, pk.emoticon)
    present_emojis = {norm_emoji(e) for e in emoji_by_docid.values()}
    mapping = load_mapping(mapping_path)
    bot = await client.get_entity('Stickers')
    done = load_progress(progress_path)

    todo = []
    for item in mapping:
        name, emoji = item['name'], item['emoji']
        if name in done: continue
        webm = os.path.join(webm_dir, f'{name}.webm')
        if not os.path.exists(webm):
            print(f'  - {name}: NO WEBM, skip'); continue
        if norm_emoji(emoji) in present_emojis:
            print(f'  - {name} ({emoji}): emoji already in pack, skip'); mark_done(progress_path, name); continue
        todo.append((name, emoji, webm))
    print(f'todo: {len(todo)}\n')

    for idx, (name, emoji, webm) in enumerate(todo):
        print(f'[{idx+1:>2}/{len(todo)}] add {name} ({emoji})...', flush=True)
        ok = False
        for attempt in range(8):
            try:
                async with client.conversation(bot, timeout=180) as conv:
                    await conv.send_message('/cancel'); await asyncio.sleep(1.2)
                    await conv.send_message('/addsticker'); await asyncio.sleep(1.2)
                    await conv.get_response(timeout=25)
                    await conv.send_message(short); await asyncio.sleep(2)
                    await conv.get_response(timeout=25)
                    await conv.send_file(webm, force_document=True); await asyncio.sleep(3.5)
                    r = await conv.get_response(timeout=25)
                    await conv.send_message(emoji); await asyncio.sleep(1.5)
                    try: await conv.get_response(timeout=12)
                    except Exception: pass
                    ok = True
                print('   OK'); break
            except FloodWaitError as fw:
                wait = fw.seconds + 5
                print(f'   FLOOD {wait}s'); await asyncio.sleep(wait)
            except Exception as e:
                print(f'   err {e}, retry 5s'); await asyncio.sleep(5)
        if ok: mark_done(progress_path, name)
        await asyncio.sleep(2.5)

    async with client.conversation(bot, timeout=60) as conv:
        await conv.send_message('/cancel'); await asyncio.sleep(1)
        await conv.send_message('/done'); await asyncio.sleep(1)
    print(f'\nDone. Pack: https://t.me/addstickers/{short}')
    await client.disconnect()


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--short', required=True)
    ap.add_argument('--webm-dir', required=True)
    ap.add_argument('--mapping', required=True)
    ap.add_argument('--progress', default='add_progress.txt')
    args = ap.parse_args()
    asyncio.run(main(args.short, args.webm_dir, args.mapping, args.progress))
