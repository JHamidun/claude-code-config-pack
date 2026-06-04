"""Delete non-mapping stickers and duplicates from a pack via /delsticker.

Usage:
    python clean_pack.py --short mypack --mapping mapping.json
    python clean_pack.py --short mypack --mapping mapping.json --dry-run
"""
import sys, io, asyncio, os, argparse
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
from telethon import TelegramClient
from telethon.errors import FloodWaitError
from telethon.tl.functions.messages import GetStickerSetRequest
from telethon.tl.types import InputStickerSetShortName

from _telethon_base import load_credentials, load_mapping, norm_emoji


async def main(short, mapping_path, dry_run=False):
    api_id, api_hash, session = load_credentials()
    client = TelegramClient(session, api_id, api_hash)
    await client.start()
    pack = await client(GetStickerSetRequest(
        stickerset=InputStickerSetShortName(short_name=short), hash=0))
    emoji_by_docid = {}
    for pk in pack.packs:
        for did in pk.documents:
            emoji_by_docid.setdefault(did, pk.emoticon)
    mapping = load_mapping(mapping_path)
    std_emojis = {norm_emoji(item['emoji']) for item in mapping}

    to_delete = []
    kept = set()
    for d in pack.documents:
        e = norm_emoji(emoji_by_docid.get(d.id, ''))
        if e not in std_emojis:
            to_delete.append((d, e or '<no emoji>', 'non-standard'))
        elif e in kept:
            to_delete.append((d, e, 'duplicate'))
        else:
            kept.add(e)
    print(f'will delete {len(to_delete)} stickers')
    if dry_run:
        for d, e, why in to_delete:
            print(f'  - {e} ({why})')
        return

    bot = await client.get_entity('Stickers')
    for i, (d, e, why) in enumerate(to_delete):
        print(f'[{i+1}/{len(to_delete)}] {e} ({why})...', flush=True)
        for attempt in range(5):
            try:
                async with client.conversation(bot, timeout=120) as conv:
                    await conv.send_message('/cancel'); await asyncio.sleep(1.2)
                    await conv.send_message('/delsticker'); await asyncio.sleep(1.2)
                    await conv.get_response(timeout=15)
                    await client.send_file(bot, file=d); await asyncio.sleep(2.5)
                    r = await conv.get_response(timeout=20)
                    txt = (r.text or '').lower()
                    if 'sure' in txt or 'yes' in txt or 'удалить' in txt or 'уверен' in txt:
                        await conv.send_message('Yes, I am sure!'); await asyncio.sleep(1.5)
                        try: await conv.get_response(timeout=10)
                        except Exception: pass
                    print(f'   {txt[:60]}')
                break
            except FloodWaitError as fw:
                print(f'   FLOOD {fw.seconds+5}s')
                await asyncio.sleep(fw.seconds + 5)
            except Exception as ex:
                print(f'   err {ex}'); await asyncio.sleep(5)
        await asyncio.sleep(2)
    print(f'\nDone. Pack: https://t.me/addstickers/{short}')
    await client.disconnect()


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--short', required=True)
    ap.add_argument('--mapping', required=True)
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    asyncio.run(main(args.short, args.mapping, dry_run=args.dry_run))
