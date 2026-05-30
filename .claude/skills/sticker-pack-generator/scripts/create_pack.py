"""Create a new Telegram video sticker pack via /newvideopack.

Usage:
    python create_pack.py --short mypack --title "My Pack" \
        --webm-dir ./webms --mapping mapping.json
"""
import sys, io, asyncio, os, argparse
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
from telethon import TelegramClient
from telethon.errors import FloodWaitError

from _telethon_base import (load_credentials, load_mapping,
                            load_progress, mark_done)


async def main(short, title, webm_dir, mapping_path, progress_path):
    api_id, api_hash, session = load_credentials()
    client = TelegramClient(session, api_id, api_hash)
    await client.start()
    bot = await client.get_entity('Stickers')
    mapping = load_mapping(mapping_path)
    done = load_progress(progress_path)

    # If pack doesn't exist yet — create with first sticker
    first_done = bool(done)
    if not first_done:
        first = mapping[0]
        webm = os.path.join(webm_dir, f'{first["name"]}.webm')
        if not os.path.exists(webm):
            raise SystemExit(f'first sticker webm missing: {webm}')
        async with client.conversation(bot, timeout=240) as conv:
            await conv.send_message('/cancel'); await asyncio.sleep(1.2)
            await conv.send_message('/newvideopack'); await asyncio.sleep(1.2)
            await conv.get_response(timeout=20)
            await conv.send_message(title); await asyncio.sleep(2)
            await conv.get_response(timeout=20)
            await conv.send_file(webm, force_document=True); await asyncio.sleep(3.5)
            await conv.get_response(timeout=25)
            await conv.send_message(first['emoji']); await asyncio.sleep(2)
            await conv.get_response(timeout=20)
        mark_done(progress_path, first['name'])
        print(f'created pack with first sticker {first["name"]}')
        remaining = mapping[1:]
    else:
        remaining = [m for m in mapping if m['name'] not in done]

    # Subsequent stickers via /addsticker
    for idx, item in enumerate(remaining):
        name, emoji = item['name'], item['emoji']
        webm = os.path.join(webm_dir, f'{name}.webm')
        if not os.path.exists(webm):
            print(f'  - {name}: NO WEBM, skip'); continue
        print(f'[{idx+1}/{len(remaining)}] add {name} ({emoji})...', flush=True)
        ok = False
        for attempt in range(8):
            try:
                async with client.conversation(bot, timeout=180) as conv:
                    await conv.send_message('/cancel'); await asyncio.sleep(1.2)
                    await conv.send_message('/addsticker'); await asyncio.sleep(1.2)
                    await conv.get_response(timeout=25)
                    await conv.send_message(short); await asyncio.sleep(2)
                    r = await conv.get_response(timeout=25)
                    # If we haven't published yet, /addsticker may not find short_name yet
                    # Try via "send /publish" first if response indicates pack draft state
                    await conv.send_file(webm, force_document=True); await asyncio.sleep(3.5)
                    await conv.get_response(timeout=25)
                    await conv.send_message(emoji); await asyncio.sleep(1.5)
                    try: await conv.get_response(timeout=12)
                    except Exception: pass
                    ok = True
                print('   OK'); break
            except FloodWaitError as fw:
                print(f'   FLOOD {fw.seconds+5}s'); await asyncio.sleep(fw.seconds + 5)
            except Exception as e:
                print(f'   err {e}'); await asyncio.sleep(5)
        if ok: mark_done(progress_path, name)
        await asyncio.sleep(2.5)

    # Publish (if not yet)
    async with client.conversation(bot, timeout=120) as conv:
        await conv.send_message('/cancel'); await asyncio.sleep(1.2)
        await conv.send_message('/publish'); await asyncio.sleep(2)
        r = await conv.get_response(timeout=20)
        await conv.send_message(short); await asyncio.sleep(2)
        try: await conv.get_response(timeout=15)
        except Exception: pass

    print(f'\nDone. Pack: https://t.me/addstickers/{short}')
    await client.disconnect()


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--short', required=True)
    ap.add_argument('--title', required=True)
    ap.add_argument('--webm-dir', required=True)
    ap.add_argument('--mapping', required=True)
    ap.add_argument('--progress', default='create_progress.txt')
    args = ap.parse_args()
    asyncio.run(main(args.short, args.title, args.webm_dir,
                     args.mapping, args.progress))
