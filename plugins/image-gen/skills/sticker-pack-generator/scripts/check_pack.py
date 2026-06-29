"""Dump state of a Telegram sticker pack.

Usage:
    python check_pack.py --short mypack
    python check_pack.py --short mypack --mapping mapping.json   # check coverage
"""
import sys, io, asyncio, os, argparse
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
from telethon import TelegramClient
from telethon.tl.functions.messages import GetStickerSetRequest
from telethon.tl.types import InputStickerSetShortName

from _telethon_base import load_credentials, load_mapping, norm_emoji


async def main(short, mapping_path=None):
    api_id, api_hash, session = load_credentials()
    client = TelegramClient(session, api_id, api_hash)
    await client.start()
    pack = await client(GetStickerSetRequest(
        stickerset=InputStickerSetShortName(short_name=short), hash=0))
    emoji_by_docid = {}
    for pk in pack.packs:
        for did in pk.documents:
            emoji_by_docid.setdefault(did, pk.emoticon)
    emojis_present = {norm_emoji(e) for e in emoji_by_docid.values()}
    print(f'Pack "{short}": {len(pack.documents)} stickers, {len(emojis_present)} unique emojis')

    if mapping_path:
        mapping = load_mapping(mapping_path)
        std = {norm_emoji(item['emoji']) for item in mapping}
        missing = [(item['name'], item['emoji'])
                   for item in mapping if norm_emoji(item['emoji']) not in emojis_present]
        extras = [e for e in emojis_present if e not in std]
        print(f'\nMissing from mapping: {len(missing)}')
        for n, e in missing:
            print(f'  - {n} ({e})')
        print(f'\nNon-mapped extras in pack: {len(extras)}')
        for e in extras[:30]:
            print(f'  - {e}')

    await client.disconnect()


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--short', required=True)
    ap.add_argument('--mapping')
    args = ap.parse_args()
    asyncio.run(main(args.short, args.mapping))
