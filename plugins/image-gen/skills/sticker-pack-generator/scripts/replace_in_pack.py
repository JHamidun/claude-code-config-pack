"""Replace stickers in existing pack with new webms via /replacesticker.

Maps each pack doc by emoji → mapping name → webm-dir/<name>.webm.
Robust to FloodWaitError. Resumable via progress file.

Usage:
    python replace_in_pack.py --short mypack --webm-dir ./webms --mapping mapping.json
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
    mapping = load_mapping(mapping_path)
    emoji_to_name = {norm_emoji(item['emoji']): item['name'] for item in mapping}
    docs_by_name = {}
    for d in pack.documents:
        name = emoji_to_name.get(norm_emoji(emoji_by_docid.get(d.id, '')))
        if name: docs_by_name[name] = d
    print(f'pack: {len(pack.documents)} docs, mapped {len(docs_by_name)}')

    bot = await client.get_entity('Stickers')
    done = load_progress(progress_path)

    todo = []
    for item in mapping:
        name, emoji = item['name'], item['emoji']
        if name in done: continue
        webm = os.path.join(webm_dir, f'{name}.webm')
        if not os.path.exists(webm) or name not in docs_by_name:
            continue
        todo.append((name, emoji, docs_by_name[name], webm))
    print(f'todo: {len(todo)}\n')

    for idx, (name, emoji, target, webm) in enumerate(todo):
        print(f'[{idx+1:>2}/{len(todo)}] {name} ({emoji})...', flush=True)
        ok = False
        for attempt in range(8):
            try:
                async with client.conversation(bot, timeout=180) as conv:
                    await conv.send_message('/cancel'); await asyncio.sleep(1.2)
                    await conv.send_message('/replacesticker'); await asyncio.sleep(1.2)
                    await conv.get_response(timeout=25)
                    await client.send_file(bot, file=target); await asyncio.sleep(2.5)
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

    print(f'\nDone. Pack: https://t.me/addstickers/{short}')
    await client.disconnect()


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--short', required=True)
    ap.add_argument('--webm-dir', required=True)
    ap.add_argument('--mapping', required=True)
    ap.add_argument('--progress', default='replace_progress.txt')
    args = ap.parse_args()
    asyncio.run(main(args.short, args.webm_dir, args.mapping, args.progress))
