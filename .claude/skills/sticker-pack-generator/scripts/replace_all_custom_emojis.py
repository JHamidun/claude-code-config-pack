#!/usr/bin/env python3
"""
replace_all_custom_emojis.py — bulk replace custom emojis in a Telegram pack.

Args:
  --pack-short-name <name>
  --mapping-json <map.json>    { "<emoji>": "<path/to/local.webm>", ... }
  --force                      ignore progress.txt and restart

Auth via env:
  TG_API_ID
  TG_API_HASH
  TG_SESSION_PATH       default: ~/.telegram_session
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--pack-short-name", required=True)
    p.add_argument("--mapping-json", required=True, type=Path)
    p.add_argument("--force", action="store_true")
    p.add_argument("--progress-file", type=Path, default=Path("progress.txt"))
    return p.parse_args()


def load_progress(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {ln.strip() for ln in path.read_text(encoding="utf-8").splitlines()
            if ln.strip()}


def append_progress(path: Path, key: str) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(key + "\n")


async def run(args: argparse.Namespace) -> None:
    try:
        from telethon import TelegramClient  # type: ignore
        from telethon.tl.functions.messages import (  # type: ignore
            GetStickerSetRequest, UploadStickerFileRequest,
        )
        from telethon.tl.functions.stickers import ReplaceStickerRequest  # type: ignore
        try:
            from telethon.tl.functions.stickers import AddStickerToSetRequest  # type: ignore
        except ImportError:
            AddStickerToSetRequest = None  # type: ignore
        from telethon.tl.types import (  # type: ignore
            InputStickerSetShortName, InputStickerSetItem, InputDocument,
        )
    except ImportError:
        sys.exit("telethon required: pip install telethon")

    api_id = os.environ.get("TG_API_ID")
    api_hash = os.environ.get("TG_API_HASH")
    if not api_id or not api_hash:
        sys.exit("TG_API_ID and TG_API_HASH env vars required")
    session_path = os.environ.get(
        "TG_SESSION_PATH",
        str(Path.home() / ".telegram_session"),
    )

    mapping: dict[str, str] = json.loads(
        args.mapping_json.read_text(encoding="utf-8"))
    if not isinstance(mapping, dict) or not mapping:
        sys.exit(f"mapping must be a non-empty dict: {args.mapping_json}")

    if args.force and args.progress_file.exists():
        args.progress_file.unlink()
    done = load_progress(args.progress_file)
    print(f"[i] {len(mapping)} planned, {len(done)} already done")

    async with TelegramClient(session_path, int(api_id), api_hash) as client:
        if not await client.is_user_authorized():
            sys.exit("session not authorized — run telethon login flow first")

        pack = await client(GetStickerSetRequest(
            stickerset=InputStickerSetShortName(short_name=args.pack_short_name),
            hash=0,
        ))
        existing: dict[str, object] = {}
        # `pack.packs` is list[StickerPack(emoticon, documents=[doc_ids])]
        doc_by_id = {d.id: d for d in pack.documents}
        for sp in pack.packs:
            for did in sp.documents:
                if did in doc_by_id:
                    existing.setdefault(sp.emoticon, doc_by_id[did])
        print(f"[i] pack has {len(pack.documents)} stickers, "
              f"{len(existing)} unique emoji slots")

        me = await client.get_me()
        for emoji, local_path in mapping.items():
            if emoji in done:
                print(f"[skip] {emoji} already done")
                continue
            lp = Path(local_path)
            if not lp.exists():
                print(f"[warn] missing file for {emoji}: {lp}")
                continue

            uploaded = await client(UploadStickerFileRequest(
                user_id=me.id,
                media=await client.upload_file(str(lp)),
            ))
            new_doc = InputDocument(
                id=uploaded.id,
                access_hash=uploaded.access_hash,
                file_reference=uploaded.file_reference,
            )

            if emoji in existing:
                old = existing[emoji]
                old_doc = InputDocument(
                    id=old.id, access_hash=old.access_hash,
                    file_reference=old.file_reference,
                )
                await client(ReplaceStickerRequest(
                    sticker=old_doc,
                    new_sticker=InputStickerSetItem(
                        document=new_doc, emoji=emoji,
                    ),
                ))
                print(f"[ok] replaced {emoji}")
            else:
                if AddStickerToSetRequest is None:
                    print(f"[warn] {emoji} new but AddStickerToSetRequest "
                          "unavailable in this telethon")
                else:
                    await client(AddStickerToSetRequest(
                        stickerset=InputStickerSetShortName(
                            short_name=args.pack_short_name),
                        sticker=InputStickerSetItem(
                            document=new_doc, emoji=emoji),
                    ))
                    print(f"[ok] added {emoji}")
            append_progress(args.progress_file, emoji)

    print("[done]")


def main() -> None:
    args = parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
