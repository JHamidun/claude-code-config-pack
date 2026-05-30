"""Create new STATIC sticker pack via @Stickers (/newpack) and upload all images.

For static stickers (.webp), max side 512, ≤512KB per file.

Usage:
    python upload_static_pack.py \
        --short mypack \
        --title "My Pack" \
        --media-dir ./final/ \
        --mapping ../references/sample-mapping.json

Resumable via --progress file.
"""
import sys, io, asyncio, os, argparse
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
from telethon import TelegramClient
from telethon.errors import FloodWaitError

from _config import telegram_api_id, telegram_api_hash, telegram_session
from _telethon_base import load_mapping, load_progress, mark_done


async def main(short, title, media_dir, mapping_path, progress_path):
    client = TelegramClient(telegram_session(), telegram_api_id(), telegram_api_hash())
    await client.start()
    bot = await client.get_entity('Stickers')
    mapping = load_mapping(mapping_path)
    done = load_progress(progress_path)
    first_done = bool(done)

    if not first_done:
        first = mapping[0]
        media = os.path.join(media_dir, f'{first["name"]}.webp')
        if not os.path.exists(media):
            raise SystemExit(f'first sticker missing: {media}')
        async with client.conversation(bot, timeout=240) as conv:
            await conv.send_message('/cancel'); await asyncio.sleep(1.2)
            await conv.send_message('/newpack'); await asyncio.sleep(1.2)
            await conv.get_response(timeout=20)
            await conv.send_message(title); await asyncio.sleep(2)
            await conv.get_response(timeout=20)
            await conv.send_file(media, force_document=True); await asyncio.sleep(3)
            await conv.get_response(timeout=25)
            await conv.send_message(first['emoji']); await asyncio.sleep(2)
            await conv.get_response(timeout=20)
        mark_done(progress_path, first['name'])
        print(f'created pack with first sticker {first["name"]}')
        remaining = mapping[1:]
    else:
        remaining = [m for m in mapping if m['name'] not in done]

    for idx, item in enumerate(remaining):
        name, emoji = item['name'], item['emoji']
        media = os.path.join(media_dir, f'{name}.webp')
        if not os.path.exists(media):
            print(f'  - {name}: NO FILE'); continue
        print(f'[{idx+1}/{len(remaining)}] add {name} ({emoji})...', flush=True)
        ok = False
        for attempt in range(8):
            try:
                async with client.conversation(bot, timeout=180) as conv:
                    await conv.send_message('/cancel'); await asyncio.sleep(1.2)
                    await conv.send_message('/addsticker'); await asyncio.sleep(1.2)
                    await conv.get_response(timeout=25)
                    await conv.send_message(short); await asyncio.sleep(2)
                    await conv.get_response(timeout=25)
                    await conv.send_file(media, force_document=True); await asyncio.sleep(3)
                    await conv.get_response(timeout=25)
                    await conv.send_message(emoji); await asyncio.sleep(1.5)
                    try: await conv.get_response(timeout=12)
                    except Exception: pass
                    ok = True
                print('   OK'); break
            except FloodWaitError as fw:
                print(f'   FLOOD {fw.seconds+5}s'); await asyncio.sleep(fw.seconds+5)
            except Exception as e:
                print(f'   err {e}'); await asyncio.sleep(5)
        if ok: mark_done(progress_path, name)
        await asyncio.sleep(2.5)

    async with client.conversation(bot, timeout=120) as conv:
        await conv.send_message('/cancel'); await asyncio.sleep(1.2)
        await conv.send_message('/publish'); await asyncio.sleep(2)
        await conv.get_response(timeout=20)
        await conv.send_message(short); await asyncio.sleep(2)
        try: await conv.get_response(timeout=15)
        except Exception: pass
    print(f'\nDone. Pack: https://t.me/addstickers/{short}')
    await client.disconnect()


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--short', required=True)
    ap.add_argument('--title', required=True)
    ap.add_argument('--media-dir', required=True)
    ap.add_argument('--mapping', required=True)
    ap.add_argument('--progress', default='static_upload_progress.txt')
    args = ap.parse_args()
    asyncio.run(main(args.short, args.title, args.media_dir,
                     args.mapping, args.progress))
