"""
Telegram CLI for Claude Code.
Full-featured Telethon client for reading, searching, downloading, and parsing Telegram data.

Session: ~/.claude/telegram_session.session
Credentials: ~/.claude/.credentials.master.env (TELEGRAM_API_ID, TELEGRAM_API_HASH)
Account: @YourUsername (Premium)
"""

import asyncio
import argparse
import json
import os
import sys
import io
from datetime import datetime
from pathlib import Path

# Fix Windows encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def load_env():
    env_path = Path.home() / ".claude" / ".credentials.master.env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip()
                if key and not os.environ.get(key):
                    os.environ[key] = value

try:
    from telethon import TelegramClient
except ImportError:
    sys.exit("ERROR: telethon is not installed. Install it with: pip install telethon")
from telethon.tl.types import (
    Channel, Chat, User,
    MessageMediaPhoto, MessageMediaDocument, MessageMediaWebPage,
    MessageMediaContact, MessageMediaGeo, MessageMediaPoll,
    DocumentAttributeFilename, DocumentAttributeVideo, DocumentAttributeAudio,
    MessageActionPinMessage,
    InputPeerChannel, InputPeerUser, InputPeerChat,
    ReactionEmoji,
    InputMessagesFilterPhotos, InputMessagesFilterVideo,
    InputMessagesFilterDocument, InputMessagesFilterUrl,
    InputMessagesFilterVoice, InputMessagesFilterMusic,
    InputMessagesFilterGif,
)
from telethon.tl.functions.messages import (
    GetDialogFiltersRequest,
    SetTypingRequest, GetPollResultsRequest,
    SendReactionRequest,
)
from telethon.tl.functions.contacts import GetContactsRequest, BlockRequest, UnblockRequest
from telethon.tl.functions.channels import (
    GetFullChannelRequest, JoinChannelRequest, LeaveChannelRequest,
    EditBannedRequest, InviteToChannelRequest, GetChannelRecommendationsRequest,
)
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.functions.stories import GetPeerStoriesRequest
from telethon.tl.types import ChatBannedRights

SESSION_PATH = str(Path.home() / ".claude" / "telegram_session")
DOWNLOAD_DIR = str(Path.home() / ".claude" / "downloads")


def get_api_credentials():
    """Resolve Telegram API credentials lazily — never at import time.

    Returns (api_id, api_hash). Exits with a clear message if missing/invalid.
    """
    load_env()
    api_id_raw = os.environ.get("TELEGRAM_API_ID", "")
    api_hash = os.environ.get("TELEGRAM_API_HASH", "")
    if not api_id_raw or not api_hash:
        sys.exit(
            "ERROR: TELEGRAM_API_ID / TELEGRAM_API_HASH are not set.\n"
            "Get them at https://my.telegram.org/apps and put them into\n"
            "~/.claude/.credentials.master.env (or export as environment variables)."
        )
    try:
        api_id = int(api_id_raw)
    except ValueError:
        sys.exit(f"ERROR: TELEGRAM_API_ID must be an integer, got: {api_id_raw!r}")
    return api_id, api_hash


def fmt_date(dt):
    if dt is None:
        return ""
    return dt.strftime("%Y-%m-%d %H:%M")


def fmt_user(user):
    if user is None:
        return "Unknown"
    parts = []
    if user.first_name:
        parts.append(user.first_name)
    if user.last_name:
        parts.append(user.last_name)
    name = " ".join(parts) or "NoName"
    if user.username:
        name += f" (@{user.username})"
    return name


def fmt_media(msg):
    """Describe media type in a message."""
    if not msg.media:
        return ""
    if isinstance(msg.media, MessageMediaPhoto):
        return "[PHOTO]"
    if isinstance(msg.media, MessageMediaDocument):
        doc = msg.media.document
        if doc:
            for attr in doc.attributes:
                if isinstance(attr, DocumentAttributeVideo):
                    dur = f" {attr.duration}s" if attr.duration else ""
                    return f"[VIDEO{dur}]"
                if isinstance(attr, DocumentAttributeAudio):
                    dur = f" {attr.duration}s" if attr.duration else ""
                    if attr.voice:
                        return f"[VOICE{dur}]"
                    return f"[AUDIO{dur}]"
                if isinstance(attr, DocumentAttributeFilename):
                    return f"[FILE: {attr.file_name}]"
            return "[DOCUMENT]"
    if isinstance(msg.media, MessageMediaContact):
        return f"[CONTACT: {msg.media.first_name} {msg.media.last_name or ''} +{msg.media.phone_number}]"
    if isinstance(msg.media, MessageMediaGeo):
        return f"[GEO: {msg.media.geo.lat}, {msg.media.geo.long}]"
    if isinstance(msg.media, MessageMediaPoll):
        question = msg.media.poll.question
        q_text = question.text if hasattr(question, "text") else str(question)
        return f"[POLL: {q_text}]"
    if isinstance(msg.media, MessageMediaWebPage):
        wp = msg.media.webpage
        if hasattr(wp, "title") and wp.title:
            return f"[LINK: {wp.title}]"
        return "[LINK]"
    return f"[MEDIA: {type(msg.media).__name__}]"


# ========== COMMANDS ==========

async def cmd_dialogs(client, args):
    """List recent dialogs."""
    limit = args.limit or 30
    print(f"=== Recent dialogs (limit {limit}) ===\n")
    async for dialog in client.iter_dialogs(limit=limit):
        entity = dialog.entity
        dtype = "user" if isinstance(entity, User) else "channel" if isinstance(entity, Channel) else "group"
        unread = f" [{dialog.unread_count} unread]" if dialog.unread_count else ""
        username = ""
        if hasattr(entity, "username") and entity.username:
            username = f" @{entity.username}"
        print(f"  [{dtype}] {dialog.name}{username}{unread}")
        if dialog.message:
            media = fmt_media(dialog.message)
            text = dialog.message.text or ""
            print(f"    Last: {fmt_date(dialog.message.date)} — {media}{text[:80]}")
        print()


async def cmd_read_chat(client, args):
    """Read messages from a specific chat/user."""
    limit = args.limit or 50
    entity = await client.get_entity(args.target)
    name = fmt_user(entity) if isinstance(entity, User) else getattr(entity, "title", args.target)
    print(f"=== Chat with {name} (last {limit} messages) ===\n")

    messages = []
    async for msg in client.iter_messages(entity, limit=limit):
        messages.append(msg)

    for msg in reversed(messages):
        sender = "You" if msg.out else name
        if msg.sender and not msg.out:
            sender = fmt_user(msg.sender) if isinstance(msg.sender, User) else str(msg.sender_id)
        media = fmt_media(msg)
        text = msg.text or ""
        fwd = ""
        if msg.forward:
            fwd_name = ""
            if msg.forward.sender:
                fwd_name = fmt_user(msg.forward.sender) if isinstance(msg.forward.sender, User) else getattr(msg.forward.sender, "title", "")
            elif msg.forward.chat:
                fwd_name = getattr(msg.forward.chat, "title", "")
            fwd = f" [FWD from {fwd_name}]" if fwd_name else " [FWD]"
        reply = ""
        if msg.reply_to:
            rid = getattr(msg.reply_to, 'reply_to_msg_id', None)
            if rid is not None:
                reply = f" [reply to #{rid}]"
        print(f"[{fmt_date(msg.date)}] {sender}:{fwd}{reply} {media}{text}")

    print(f"\n--- End of {limit} messages ---")


async def cmd_read_channel(client, args):
    """Read channel posts."""
    limit = args.limit or 30
    entity = await client.get_entity(args.target)
    title = getattr(entity, "title", args.target)
    print(f"=== Channel: {title} (last {limit} posts) ===\n")

    messages = []
    async for msg in client.iter_messages(entity, limit=limit):
        messages.append(msg)

    for msg in reversed(messages):
        media = fmt_media(msg)
        text = msg.text or ""
        views = f" | {msg.views} views" if msg.views else ""
        replies = f" | {msg.replies.replies} replies" if msg.replies else ""
        reactions_str = ""
        if msg.reactions and msg.reactions.results:
            r_parts = []
            for r in msg.reactions.results:
                emoji = getattr(r.reaction, "emoticon", "?")
                r_parts.append(f"{emoji}{r.count}")
            reactions_str = f" | reactions: {' '.join(r_parts)}"
        print(f"[{fmt_date(msg.date)}] #{msg.id}{views}{replies}{reactions_str}")
        print(f"  {media}{text[:500]}")
        print()


async def cmd_search(client, args):
    """Search messages globally or in a specific chat."""
    limit = args.limit or 30
    entity = None
    if args.chat:
        entity = await client.get_entity(args.chat)
        scope = getattr(entity, "title", None) or args.chat
    else:
        scope = "all chats"

    print(f"=== Search '{args.query}' in {scope} (limit {limit}) ===\n")

    async for msg in client.iter_messages(entity, search=args.query, limit=limit):
        chat_name = ""
        if not args.chat and msg.chat:
            chat_name = getattr(msg.chat, "title", None) or getattr(msg.chat, "first_name", "") or str(msg.chat_id)
            chat_name = f" [{chat_name}]"
        sender = "You" if msg.out else ""
        if msg.sender and not msg.out:
            sender = fmt_user(msg.sender) if isinstance(msg.sender, User) else str(msg.sender_id)
        media = fmt_media(msg)
        text = msg.text or ""
        print(f"[{fmt_date(msg.date)}]{chat_name} {sender}: {media}{text[:300]}")
        print()


async def cmd_mentions(client, args):
    """Find mentions of @YourUsername."""
    limit = args.limit or 30
    me = await client.get_me()
    print(f"=== Mentions of @{me.username} (limit {limit}) ===\n")

    count = 0
    async for dialog in client.iter_dialogs(limit=100):
        if count >= limit:
            break
        try:
            async for msg in client.iter_messages(dialog.entity, search=f"@{me.username}", limit=5):
                if count >= limit:
                    break
                if msg.out:
                    continue
                sender = fmt_user(msg.sender) if isinstance(msg.sender, User) else str(msg.sender_id)
                print(f"[{fmt_date(msg.date)}] [{dialog.name}] {sender}: {(msg.text or '(media)')[:300]}")
                print()
                count += 1
        except Exception:
            continue
    print(f"--- Found {count} mentions ---")


async def cmd_parse_comments(client, args):
    """Parse comments on a channel post with full user info."""
    limit = args.limit or 100
    entity = await client.get_entity(args.channel)
    post_id = int(args.post_id)
    title = getattr(entity, "title", args.channel)
    print(f"=== Comments on {title} post #{post_id} (limit {limit}) ===\n")

    comments = []
    async for msg in client.iter_messages(entity, reply_to=post_id, limit=limit):
        comments.append(msg)

    for msg in reversed(comments):
        sender = msg.sender
        if isinstance(sender, User):
            name = fmt_user(sender)
            premium = " [Premium]" if sender.premium else ""
            print(f"[{fmt_date(msg.date)}] {name}{premium}: {(msg.text or fmt_media(msg))[:500]}")
        elif isinstance(sender, Channel):
            print(f"[{fmt_date(msg.date)}] {sender.title} (channel): {(msg.text or fmt_media(msg))[:500]}")
        else:
            print(f"[{fmt_date(msg.date)}] ID:{msg.sender_id}: {(msg.text or fmt_media(msg))[:500]}")

    print(f"\n--- {len(comments)} comments ---")


async def cmd_parse_commenters(client, args):
    """Parse PEOPLE who commented on a post — full profiles for lead generation."""
    limit = args.limit or 200
    entity = await client.get_entity(args.channel)
    post_id = int(args.post_id)
    title = getattr(entity, "title", args.channel)
    print(f"=== Commenters on {title} post #{post_id} ===\n")

    seen_users = {}
    try:
        async for msg in client.iter_messages(entity, reply_to=post_id, limit=limit):
            sender = msg.sender
            if isinstance(sender, User) and sender.id not in seen_users:
                seen_users[sender.id] = {
                    "id": sender.id,
                    "first_name": sender.first_name or "",
                    "last_name": sender.last_name or "",
                    "username": sender.username or "",
                    "phone": sender.phone or "",
                    "premium": bool(sender.premium),
                    "bot": bool(sender.bot),
                    "verified": bool(sender.verified),
                    "comment": (msg.text or "")[:200],
                    "date": fmt_date(msg.date),
                    "bio": "",
                    "personal_channel_id": None,
                }
    except Exception as e:
        if "MsgIdInvalid" in str(type(e).__name__):
            print(f"Post #{post_id} not found or has no comments.\n")
            return
        raise

    # Enrich with bio and personal channel
    for uid in list(seen_users.keys()):
        try:
            full = await client(GetFullUserRequest(uid))
            seen_users[uid]["bio"] = full.full_user.about or ""
            if full.full_user.personal_channel_id:
                seen_users[uid]["personal_channel_id"] = full.full_user.personal_channel_id
        except Exception:
            pass

    print(f"Found {len(seen_users)} unique commenters:\n")
    for u in seen_users.values():
        name = f"{u['first_name']} {u['last_name']}".strip()
        username = f" @{u['username']}" if u['username'] else ""
        premium = " [Premium]" if u['premium'] else ""
        verified = " [Verified]" if u['verified'] else ""
        bio = f"\n    Bio: {u['bio'][:150]}" if u['bio'] else ""
        ch = f"\n    Personal channel: {u['personal_channel_id']}" if u['personal_channel_id'] else ""
        print(f"  {name}{username}{premium}{verified}{bio}{ch}")
        print(f"    Comment: {u['comment'][:100]}")

    if args.output:
        Path(args.output).write_text(json.dumps(list(seen_users.values()), ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nSaved to {args.output}")


async def cmd_participants(client, args):
    """List participants of a group/channel with full profile info."""
    limit = args.limit or 200
    entity = await client.get_entity(args.target)
    title = getattr(entity, "title", args.target)
    print(f"=== Participants of {title} (limit {limit}) ===\n")

    users = []
    async for user in client.iter_participants(entity, limit=limit):
        info = {
            "id": user.id,
            "first_name": user.first_name or "",
            "last_name": user.last_name or "",
            "username": user.username or "",
            "phone": user.phone or "",
            "premium": bool(user.premium),
            "bot": bool(user.bot),
            "verified": bool(user.verified),
        }
        users.append(info)
        name = f"{info['first_name']} {info['last_name']}".strip()
        username = f" @{info['username']}" if info['username'] else ""
        premium = " [Premium]" if info['premium'] else ""
        print(f"  {name}{username}{premium}")

    print(f"\n--- {len(users)} participants ---")

    if args.output:
        Path(args.output).write_text(json.dumps(users, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Saved to {args.output}")


async def cmd_contacts(client, args):
    """List contacts."""
    limit = args.limit or 100
    result = await client(GetContactsRequest(hash=0))
    users = result.users if hasattr(result, "users") else []
    print(f"=== Contacts ({min(limit, len(users))} of {len(users)}) ===\n")

    for user in users[:limit]:
        phone = f" +{user.phone}" if user.phone else ""
        username = f" @{user.username}" if user.username else ""
        name = f"{user.first_name or ''} {user.last_name or ''}".strip()
        print(f"  {name}{username}{phone}")


async def cmd_folders(client, args):
    """List Telegram folders."""
    result = await client(GetDialogFiltersRequest())
    filters = result.filters if hasattr(result, 'filters') else result
    print("=== Telegram Folders ===\n")
    for f in filters:
        if hasattr(f, "title"):
            title = f.title if isinstance(f.title, str) else getattr(f.title, "text", str(f.title))
            print(f"  [{f.id}] {title}")


async def cmd_folder_chats(client, args):
    """List chats in a specific folder."""
    folder_name = args.folder_name.lower()
    result = await client(GetDialogFiltersRequest())
    filters = result.filters if hasattr(result, 'filters') else result

    target_filter = None
    for f in filters:
        if hasattr(f, "title"):
            title = f.title if isinstance(f.title, str) else getattr(f.title, "text", str(f.title))
            if folder_name in title.lower():
                target_filter = f
                break

    if not target_filter:
        print(f"Folder '{args.folder_name}' not found")
        return

    title = target_filter.title if isinstance(target_filter.title, str) else getattr(target_filter.title, "text", str(target_filter.title))
    print(f"=== Chats in folder '{title}' ===\n")

    if hasattr(target_filter, "include_peers"):
        for peer in target_filter.include_peers:
            try:
                entity = await client.get_entity(peer)
                name = getattr(entity, "title", None) or fmt_user(entity)
                username = f" @{entity.username}" if hasattr(entity, "username") and entity.username else ""
                print(f"  {name}{username}")
            except Exception as e:
                print(f"  (peer {peer} — error: {e})")


async def cmd_user_info(client, args):
    """Get full info about a user/channel."""
    entity = await client.get_entity(args.target)

    if isinstance(entity, User):
        print(f"=== User Info ===")
        print(f"  Name: {entity.first_name or ''} {entity.last_name or ''}")
        print(f"  Username: @{entity.username}" if entity.username else "  Username: none")
        print(f"  Phone: +{entity.phone}" if entity.phone else "  Phone: hidden")
        print(f"  ID: {entity.id}")
        print(f"  Bot: {entity.bot}")
        print(f"  Premium: {entity.premium}")
        print(f"  Verified: {entity.verified}")
        print(f"  Restricted: {entity.restricted}")
        if entity.restriction_reason:
            print(f"  Restriction: {entity.restriction_reason}")
        # Bio
        try:
            from telethon.tl.functions.users import GetFullUserRequest
            full = await client(GetFullUserRequest(entity))
            if full.full_user.about:
                print(f"  Bio: {full.full_user.about}")
            if full.full_user.personal_channel_id:
                print(f"  Personal channel ID: {full.full_user.personal_channel_id}")
        except Exception:
            pass
        # Profile photos count
        photos = await client.get_profile_photos(entity, limit=0)
        print(f"  Profile photos: {photos.total}")
    elif isinstance(entity, (Channel, Chat)):
        print(f"=== Channel/Group Info ===")
        print(f"  Title: {entity.title}")
        print(f"  Username: @{entity.username}" if hasattr(entity, "username") and entity.username else "  Username: none")
        print(f"  ID: {entity.id}")
        if hasattr(entity, "participants_count") and entity.participants_count:
            print(f"  Members: {entity.participants_count}")
        if hasattr(entity, "megagroup"):
            print(f"  Megagroup: {entity.megagroup}")
        if hasattr(entity, "broadcast"):
            print(f"  Broadcast: {entity.broadcast}")
        if hasattr(entity, "verified"):
            print(f"  Verified: {entity.verified}")
        if hasattr(entity, "noforwards"):
            print(f"  Copy protected: {entity.noforwards}")
        # Full info
        try:
            full = await client(GetFullChannelRequest(entity))
            fc = full.full_chat
            if fc.about:
                print(f"  Description: {fc.about[:300]}")
            if hasattr(fc, "linked_chat_id") and fc.linked_chat_id:
                print(f"  Linked chat ID: {fc.linked_chat_id}")
            if hasattr(fc, "online_count") and fc.online_count:
                print(f"  Online now: {fc.online_count}")
        except Exception:
            pass


async def cmd_download(client, args):
    """Download media from a chat/channel."""
    limit = args.limit or 10
    entity = await client.get_entity(args.target)
    name = getattr(entity, "title", None) or fmt_user(entity) if isinstance(entity, User) else args.target
    out_dir = Path(args.output or DOWNLOAD_DIR) / str(entity.id)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"=== Downloading media from {name} (limit {limit}) → {out_dir} ===\n")

    count = 0
    async for msg in client.iter_messages(entity, limit=limit * 3):
        if count >= limit:
            break
        if msg.media and not isinstance(msg.media, MessageMediaWebPage):
            try:
                path = await client.download_media(msg, file=str(out_dir))
                if path:
                    print(f"  [{fmt_date(msg.date)}] #{msg.id} → {Path(path).name}")
                    count += 1
            except Exception as e:
                print(f"  [{fmt_date(msg.date)}] #{msg.id} — error: {e}")

    print(f"\n--- Downloaded {count} files to {out_dir} ---")


async def cmd_download_photo(client, args):
    """Download profile photos of a user/channel."""
    entity = await client.get_entity(args.target)
    name = getattr(entity, "title", None) or fmt_user(entity)
    out_dir = Path(args.output or DOWNLOAD_DIR) / f"photos_{entity.id}"
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"=== Profile photos of {name} → {out_dir} ===\n")

    count = 0
    async for photo in client.iter_profile_photos(entity, limit=args.limit or 10):
        path = await client.download_media(photo, file=str(out_dir))
        if path:
            print(f"  Photo {count + 1} → {Path(path).name}")
            count += 1

    print(f"\n--- Downloaded {count} photos ---")


async def cmd_pinned(client, args):
    """Get pinned messages in a chat."""
    entity = await client.get_entity(args.target)
    name = getattr(entity, "title", None) or fmt_user(entity)
    print(f"=== Pinned messages in {name} ===\n")

    count = 0
    async for msg in client.iter_messages(entity, filter=None, limit=500):
        if msg.pinned:
            sender = "You" if msg.out else ""
            if msg.sender and not msg.out:
                sender = fmt_user(msg.sender) if isinstance(msg.sender, User) else str(msg.sender_id)
            media = fmt_media(msg)
            print(f"[{fmt_date(msg.date)}] #{msg.id} {sender}: {media}{(msg.text or '')[:300]}")
            print()
            count += 1
            if count >= (args.limit or 20):
                break

    print(f"--- {count} pinned messages ---")


async def cmd_admin_log(client, args):
    """View admin log of a channel/group (bans, deletes, edits, etc.)."""
    entity = await client.get_entity(args.target)
    title = getattr(entity, "title", args.target)
    limit = args.limit or 30
    print(f"=== Admin log of {title} (limit {limit}) ===\n")

    count = 0
    async for event in client.iter_admin_log(entity, limit=limit):
        user = fmt_user(event.user) if event.user else "Unknown"
        action = type(event.action).__name__.replace("ChannelAdminLogEvent", "")
        print(f"[{fmt_date(event.date)}] {user}: {action}")
        if hasattr(event, "old") and event.old:
            print(f"    Old: {str(event.old)[:200]}")
        if hasattr(event, "new") and event.new:
            print(f"    New: {str(event.new)[:200]}")
        print()
        count += 1

    print(f"--- {count} events ---")


async def cmd_drafts(client, args):
    """Show unsent message drafts."""
    print("=== Unsent Drafts ===\n")
    drafts = await client.get_drafts()
    count = 0
    for draft in drafts:
        if draft.text:
            name = ""
            try:
                entity = await draft.get_entity()
                name = getattr(entity, "title", None) or fmt_user(entity)
            except Exception:
                name = str(draft.entity)
            print(f"  [{name}] {draft.text[:200]}")
            print(f"    Date: {fmt_date(draft.date)}")
            print()
            count += 1
    print(f"--- {count} drafts ---")


async def cmd_export_chat(client, args):
    """Export chat messages to JSON."""
    limit = args.limit or 500
    entity = await client.get_entity(args.target)
    name = getattr(entity, "title", None) or fmt_user(entity)
    output = args.output or f"chat_export_{entity.id}.json"

    print(f"=== Exporting {name} (limit {limit}) → {output} ===\n")

    messages = []
    async for msg in client.iter_messages(entity, limit=limit):
        sender_name = ""
        if msg.sender:
            sender_name = fmt_user(msg.sender) if isinstance(msg.sender, User) else getattr(msg.sender, "title", str(msg.sender_id))
        messages.append({
            "id": msg.id,
            "date": fmt_date(msg.date),
            "sender_id": msg.sender_id,
            "sender_name": sender_name,
            "out": msg.out,
            "text": msg.text or "",
            "media": fmt_media(msg) if msg.media else None,
            "reply_to": msg.reply_to.reply_to_msg_id if msg.reply_to else None,
            "forward": bool(msg.forward),
            "views": msg.views,
            "pinned": msg.pinned,
        })
        if len(messages) % 100 == 0:
            print(f"  Exported {len(messages)} messages...")

    messages.reverse()
    Path(output).write_text(json.dumps(messages, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n--- Exported {len(messages)} messages to {output} ---")


async def cmd_user_messages(client, args):
    """Find all messages from a specific user in a group/channel."""
    limit = args.limit or 50
    entity = await client.get_entity(args.target)
    user = await client.get_entity(args.user)
    group_name = getattr(entity, "title", args.target)
    user_name = fmt_user(user)

    print(f"=== Messages from {user_name} in {group_name} (limit {limit}) ===\n")

    messages = []
    async for msg in client.iter_messages(entity, from_user=user, limit=limit):
        messages.append(msg)

    for msg in reversed(messages):
        media = fmt_media(msg)
        print(f"[{fmt_date(msg.date)}] #{msg.id}: {media}{(msg.text or '')[:300]}")
        print()

    print(f"--- {len(messages)} messages ---")


async def cmd_channel_stats(client, args):
    """Get channel/group statistics."""
    entity = await client.get_entity(args.target)
    title = getattr(entity, "title", args.target)

    print(f"=== Stats for {title} ===\n")

    try:
        full = await client(GetFullChannelRequest(entity))
        fc = full.full_chat
        print(f"  Members: {getattr(fc, 'participants_count', 'N/A')}")
        print(f"  Admins: {getattr(fc, 'admins_count', 'N/A')}")
        print(f"  Banned: {getattr(fc, 'kicked_count', 'N/A')}")
        print(f"  Online: {getattr(fc, 'online_count', 'N/A')}")
        if fc.about:
            print(f"  Description: {fc.about[:300]}")

        # Recent posts stats
        print(f"\n  Recent posts engagement:")
        count = 0
        async for msg in client.iter_messages(entity, limit=20):
            if msg.text or msg.media:
                views = msg.views or 0
                replies = msg.replies.replies if msg.replies else 0
                reactions_count = sum(r.count for r in msg.reactions.results) if msg.reactions else 0
                print(f"    #{msg.id} [{fmt_date(msg.date)}]: {views} views, {replies} comments, {reactions_count} reactions")
                count += 1
        print(f"\n  Analyzed {count} recent posts")
    except Exception as e:
        print(f"  Error: {e}")
        print("  (Stats may require admin access or channel with stats enabled)")


# ========== MESSAGING ==========

async def cmd_send(client, args):
    """Send a text message to a user/group/channel."""
    entity = await client.get_entity(args.target)
    name = getattr(entity, "title", None) or fmt_user(entity)

    kwargs = {}
    if args.reply_to:
        kwargs["reply_to"] = int(args.reply_to)
    if args.schedule:
        from datetime import timezone
        kwargs["schedule"] = datetime.fromisoformat(args.schedule).replace(tzinfo=timezone.utc)

    msg = await client.send_message(entity, args.text, **kwargs)
    scheduled = " (scheduled)" if args.schedule else ""
    print(f"Sent to {name}{scheduled}: #{msg.id}")


async def cmd_send_file(client, args):
    """Send a file/photo/video to a user/group/channel."""
    entity = await client.get_entity(args.target)
    name = getattr(entity, "title", None) or fmt_user(entity)

    kwargs = {}
    if args.caption:
        kwargs["caption"] = args.caption
    if args.reply_to:
        kwargs["reply_to"] = int(args.reply_to)
    if args.voice:
        kwargs["voice_note"] = True
    if args.video_note:
        kwargs["video_note"] = True

    msg = await client.send_file(entity, args.file, **kwargs)
    print(f"Sent file to {name}: #{msg.id}")


async def cmd_forward(client, args):
    """Forward messages from one chat to another."""
    from_entity = await client.get_entity(args.source)
    to_entity = await client.get_entity(args.target)
    msg_ids = [int(x.strip()) for x in args.ids.split(",")]

    result = await client.forward_messages(to_entity, msg_ids, from_entity)
    count = len(result) if isinstance(result, list) else 1
    print(f"Forwarded {count} message(s) to {getattr(to_entity, 'title', args.target)}")


async def cmd_reply(client, args):
    """Reply to a specific message."""
    entity = await client.get_entity(args.target)
    msg = await client.send_message(entity, args.text, reply_to=int(args.msg_id))
    print(f"Replied to #{args.msg_id}: #{msg.id}")


async def cmd_edit(client, args):
    """Edit own message."""
    entity = await client.get_entity(args.target)
    msg = await client.edit_message(entity, int(args.msg_id), args.text)
    print(f"Edited #{msg.id}")


async def cmd_delete(client, args):
    """Delete messages by IDs."""
    entity = await client.get_entity(args.target)
    msg_ids = [int(x.strip()) for x in args.ids.split(",")]
    result = await client.delete_messages(entity, msg_ids)
    print(f"Deleted {len(msg_ids)} message(s)")


async def cmd_react(client, args):
    """React to a message with an emoji."""
    entity = await client.get_entity(args.target)
    await client(SendReactionRequest(
        peer=entity,
        msg_id=int(args.msg_id),
        reaction=[ReactionEmoji(emoticon=args.emoji)]
    ))
    print(f"Reacted {args.emoji} to #{args.msg_id}")


async def cmd_schedule(client, args):
    """Send a scheduled message."""
    from datetime import timezone
    entity = await client.get_entity(args.target)
    schedule_dt = datetime.fromisoformat(args.datetime).replace(tzinfo=timezone.utc)
    msg = await client.send_message(entity, args.text, schedule=schedule_dt)
    print(f"Scheduled to {getattr(entity, 'title', args.target)} at {args.datetime}: #{msg.id}")


async def cmd_create_poll(client, args):
    """Create a poll in a chat."""
    from telethon.tl.types import InputMediaPoll, Poll, PollAnswer
    entity = await client.get_entity(args.target)
    answers = [PollAnswer(text=opt.strip(), option=bytes([i])) for i, opt in enumerate(args.options.split("|"))]
    poll = InputMediaPoll(poll=Poll(
        id=0,
        question=args.question,
        answers=answers,
        quiz=args.quiz if hasattr(args, "quiz") else False,
    ))
    msg = await client.send_message(entity, file=poll)
    print(f"Poll created in {getattr(entity, 'title', args.target)}: #{msg.id}")


# ========== GROUP/CHANNEL MANAGEMENT ==========

async def cmd_pin(client, args):
    """Pin a message in a chat."""
    entity = await client.get_entity(args.target)
    await client.pin_message(entity, int(args.msg_id), notify=not args.silent)
    silent = " (silent)" if args.silent else ""
    print(f"Pinned #{args.msg_id}{silent}")


async def cmd_unpin(client, args):
    """Unpin a message."""
    entity = await client.get_entity(args.target)
    await client.unpin_message(entity, int(args.msg_id) if args.msg_id else None)
    target = f"#{args.msg_id}" if args.msg_id else "all"
    print(f"Unpinned {target}")


async def cmd_invite(client, args):
    """Invite a user to a group/channel."""
    entity = await client.get_entity(args.target)
    user = await client.get_entity(args.user)
    if isinstance(entity, Channel):
        await client(InviteToChannelRequest(entity, [user]))
    else:
        from telethon.tl.functions.messages import AddChatUserRequest
        await client(AddChatUserRequest(entity.id, user, fwd_limit=100))
    print(f"Invited {fmt_user(user)} to {getattr(entity, 'title', args.target)}")


async def cmd_kick(client, args):
    """Kick a user from a group/channel."""
    entity = await client.get_entity(args.target)
    user = await client.get_entity(args.user)
    if isinstance(entity, Channel):
        rights = ChatBannedRights(until_date=None, view_messages=True)
        await client(EditBannedRequest(entity, user, rights))
        # Immediately unban so they can rejoin
        rights = ChatBannedRights(until_date=None, view_messages=False)
        await client(EditBannedRequest(entity, user, rights))
    else:
        from telethon.tl.functions.messages import DeleteChatUserRequest
        await client(DeleteChatUserRequest(entity.id, user))
    print(f"Kicked {fmt_user(user)} from {getattr(entity, 'title', args.target)}")


async def cmd_ban(client, args):
    """Ban a user from a group/channel."""
    entity = await client.get_entity(args.target)
    user = await client.get_entity(args.user)
    rights = ChatBannedRights(until_date=None, view_messages=True)
    await client(EditBannedRequest(entity, user, rights))
    print(f"Banned {fmt_user(user)} from {getattr(entity, 'title', args.target)}")


async def cmd_unban(client, args):
    """Unban a user."""
    entity = await client.get_entity(args.target)
    user = await client.get_entity(args.user)
    rights = ChatBannedRights(until_date=None, view_messages=False)
    await client(EditBannedRequest(entity, user, rights))
    print(f"Unbanned {fmt_user(user)} from {getattr(entity, 'title', args.target)}")


async def cmd_create_group(client, args):
    """Create a new group."""
    users = [await client.get_entity(u.strip()) for u in args.users.split(",")]
    result = await client.create_group(args.name, users)
    print(f"Created group: {args.name}")


async def cmd_create_channel(client, args):
    """Create a new channel."""
    result = await client.create_channel(args.name, about=args.about or "")
    print(f"Created channel: {args.name}")


async def cmd_edit_chat(client, args):
    """Edit group/channel title, description, or photo."""
    entity = await client.get_entity(args.target)
    if args.title:
        from telethon.tl.functions.channels import EditTitleRequest
        await client(EditTitleRequest(entity, args.title))
        print(f"Title changed to: {args.title}")
    if args.about:
        from telethon.tl.functions.channels import EditPhotoRequest
        from telethon.tl.functions.messages import EditChatAboutRequest
        await client(EditChatAboutRequest(entity, args.about))
        print(f"Description updated")
    if args.photo:
        photo = await client.upload_file(args.photo)
        from telethon.tl.functions.channels import EditPhotoRequest
        from telethon.tl.types import InputChatUploadedPhoto
        await client(EditPhotoRequest(entity, InputChatUploadedPhoto(file=photo)))
        print(f"Photo updated")


# ========== ACCOUNT ACTIONS ==========

async def cmd_join(client, args):
    """Join a group or channel."""
    entity = await client.get_entity(args.target)
    if isinstance(entity, Channel):
        await client(JoinChannelRequest(entity))
    else:
        from telethon.tl.functions.messages import ImportChatInviteRequest
        await client(ImportChatInviteRequest(args.target))
    print(f"Joined {getattr(entity, 'title', args.target)}")


async def cmd_leave(client, args):
    """Leave a group or channel."""
    entity = await client.get_entity(args.target)
    if isinstance(entity, Channel):
        await client(LeaveChannelRequest(entity))
    else:
        from telethon.tl.functions.messages import DeleteChatUserRequest
        me = await client.get_me()
        await client(DeleteChatUserRequest(entity.id, me))
    print(f"Left {getattr(entity, 'title', args.target)}")


async def cmd_mark_read(client, args):
    """Mark chat as read."""
    entity = await client.get_entity(args.target)
    await client.send_read_acknowledge(entity)
    print(f"Marked as read: {getattr(entity, 'title', args.target)}")


async def cmd_archive(client, args):
    """Archive a chat."""
    entity = await client.get_entity(args.target)
    from telethon.tl.functions.folders import EditPeerFoldersRequest
    from telethon.tl.types import InputFolderPeer
    peer = await client.get_input_entity(entity)
    await client(EditPeerFoldersRequest([InputFolderPeer(peer=peer, folder_id=1)]))
    print(f"Archived: {getattr(entity, 'title', args.target)}")


async def cmd_unarchive(client, args):
    """Unarchive a chat."""
    entity = await client.get_entity(args.target)
    from telethon.tl.functions.folders import EditPeerFoldersRequest
    from telethon.tl.types import InputFolderPeer
    peer = await client.get_input_entity(entity)
    await client(EditPeerFoldersRequest([InputFolderPeer(peer=peer, folder_id=0)]))
    print(f"Unarchived: {getattr(entity, 'title', args.target)}")


async def cmd_mute(client, args):
    """Mute a chat."""
    entity = await client.get_entity(args.target)
    from telethon.tl.functions.account import UpdateNotifySettingsRequest
    from telethon.tl.types import InputPeerNotifySettings, InputNotifyPeer
    peer = await client.get_input_entity(entity)
    await client(UpdateNotifySettingsRequest(
        peer=InputNotifyPeer(peer=peer),
        settings=InputPeerNotifySettings(mute_until=2**31 - 1)
    ))
    print(f"Muted: {getattr(entity, 'title', args.target)}")


async def cmd_unmute(client, args):
    """Unmute a chat."""
    entity = await client.get_entity(args.target)
    from telethon.tl.functions.account import UpdateNotifySettingsRequest
    from telethon.tl.types import InputPeerNotifySettings, InputNotifyPeer
    peer = await client.get_input_entity(entity)
    await client(UpdateNotifySettingsRequest(
        peer=InputNotifyPeer(peer=peer),
        settings=InputPeerNotifySettings(mute_until=0)
    ))
    print(f"Unmuted: {getattr(entity, 'title', args.target)}")


async def cmd_block(client, args):
    """Block a user."""
    user = await client.get_entity(args.target)
    peer = await client.get_input_entity(user)
    await client(BlockRequest(id=peer))
    print(f"Blocked: {fmt_user(user)}")


async def cmd_unblock(client, args):
    """Unblock a user."""
    user = await client.get_entity(args.target)
    peer = await client.get_input_entity(user)
    await client(UnblockRequest(id=peer))
    print(f"Unblocked: {fmt_user(user)}")


async def cmd_set_bio(client, args):
    """Update own bio/about."""
    await client(UpdateProfileRequest(about=args.text))
    print(f"Bio updated: {args.text[:70]}")


async def cmd_set_name(client, args):
    """Update own first/last name."""
    kwargs = {}
    if args.first:
        kwargs["first_name"] = args.first
    if args.last:
        kwargs["last_name"] = args.last
    await client(UpdateProfileRequest(**kwargs))
    print(f"Name updated: {args.first or ''} {args.last or ''}")


async def cmd_set_photo(client, args):
    """Set own profile photo."""
    from telethon.tl.functions.photos import UploadProfilePhotoRequest
    photo = await client.upload_file(args.file)
    await client(UploadProfilePhotoRequest(file=photo))
    print(f"Profile photo updated")


# ========== ADVANCED SEARCH / INFO ==========

async def cmd_search_media(client, args):
    """Search by media type in a chat."""
    entity = await client.get_entity(args.target)
    name = getattr(entity, "title", None) or fmt_user(entity)
    limit = args.limit or 30

    filters_map = {
        "photo": InputMessagesFilterPhotos(),
        "video": InputMessagesFilterVideo(),
        "document": InputMessagesFilterDocument(),
        "url": InputMessagesFilterUrl(),
        "voice": InputMessagesFilterVoice(),
        "music": InputMessagesFilterMusic(),
        "gif": InputMessagesFilterGif(),
    }
    media_filter = filters_map.get(args.type)
    if not media_filter:
        print(f"Unknown type: {args.type}. Use: {', '.join(filters_map.keys())}")
        return

    print(f"=== {args.type.upper()} in {name} (limit {limit}) ===\n")
    count = 0
    async for msg in client.iter_messages(entity, limit=limit, filter=media_filter):
        sender_name = fmt_user(msg.sender) if isinstance(msg.sender, User) else "Channel"
        text = (msg.text or "")[:100]
        print(f"[{fmt_date(msg.date)}] #{msg.id} {sender_name}: {fmt_media(msg)}{text}")
        count += 1
    print(f"\n--- {count} results ---")


async def cmd_search_date(client, args):
    """Search messages in a date range."""
    entity = await client.get_entity(args.target)
    name = getattr(entity, "title", None) or fmt_user(entity)
    limit = args.limit or 50

    from datetime import timezone
    offset_date = datetime.fromisoformat(args.end).replace(tzinfo=timezone.utc) if args.end else None
    min_date = datetime.fromisoformat(args.start).replace(tzinfo=timezone.utc) if args.start else None

    print(f"=== Messages in {name} from {args.start or 'beginning'} to {args.end or 'now'} (limit {limit}) ===\n")

    messages = []
    async for msg in client.iter_messages(entity, limit=limit, offset_date=offset_date):
        if min_date and msg.date.replace(tzinfo=timezone.utc) < min_date:
            break
        messages.append(msg)

    for msg in reversed(messages):
        sender_name = fmt_user(msg.sender) if isinstance(msg.sender, User) else "Channel"
        print(f"[{fmt_date(msg.date)}] #{msg.id} {sender_name}: {(msg.text or fmt_media(msg))[:200]}")

    print(f"\n--- {len(messages)} messages ---")


async def cmd_links(client, args):
    """Extract all URLs from a chat."""
    entity = await client.get_entity(args.target)
    name = getattr(entity, "title", None) or fmt_user(entity)
    limit = args.limit or 100

    print(f"=== Links in {name} (limit {limit}) ===\n")

    count = 0
    async for msg in client.iter_messages(entity, limit=limit, filter=InputMessagesFilterUrl()):
        urls = []
        if msg.entities:
            for ent in msg.entities:
                if hasattr(ent, "url") and ent.url:
                    urls.append(ent.url)
                elif hasattr(ent, "offset"):
                    text = (msg.text or "")[ent.offset:ent.offset + ent.length]
                    if text.startswith("http"):
                        urls.append(text)
        if msg.media and isinstance(msg.media, MessageMediaWebPage):
            wp = msg.media.webpage
            if hasattr(wp, "url") and wp.url:
                urls.append(wp.url)
        for url in urls:
            sender_name = fmt_user(msg.sender) if isinstance(msg.sender, User) else "Channel"
            print(f"[{fmt_date(msg.date)}] {sender_name}: {url}")
            count += 1
    print(f"\n--- {count} links ---")


async def cmd_hashtags(client, args):
    """Search messages by hashtag in a chat."""
    entity = await client.get_entity(args.target)
    name = getattr(entity, "title", None) or fmt_user(entity)
    tag = args.tag if args.tag.startswith("#") else f"#{args.tag}"
    limit = args.limit or 50

    print(f"=== {tag} in {name} (limit {limit}) ===\n")

    count = 0
    async for msg in client.iter_messages(entity, limit=limit, search=tag):
        sender_name = fmt_user(msg.sender) if isinstance(msg.sender, User) else "Channel"
        print(f"[{fmt_date(msg.date)}] #{msg.id} {sender_name}: {(msg.text or '')[:200]}")
        count += 1
    print(f"\n--- {count} messages ---")


async def cmd_common_groups(client, args):
    """Get common groups with a user."""
    user = await client.get_entity(args.target)
    from telethon.tl.functions.messages import GetCommonChatsRequest
    result = await client(GetCommonChatsRequest(user_id=user, max_id=0, limit=100))
    print(f"=== Common groups with {fmt_user(user)} ===\n")
    for chat in result.chats:
        members = getattr(chat, "participants_count", "?")
        print(f"  {chat.title} ({members} members)")
    print(f"\n--- {len(result.chats)} groups ---")


async def cmd_similar_channels(client, args):
    """Get similar/recommended channels."""
    entity = await client.get_entity(args.target)
    title = getattr(entity, "title", args.target)
    try:
        result = await client(GetChannelRecommendationsRequest(channel=entity))
        print(f"=== Similar to {title} ===\n")
        for ch in result.chats:
            members = getattr(ch, "participants_count", "?")
            username = f" @{ch.username}" if ch.username else ""
            print(f"  {ch.title}{username} ({members} members)")
        print(f"\n--- {len(result.chats)} channels ---")
    except Exception as e:
        print(f"Error: {e}\n(Recommendations require channel with enough subscribers)")


async def cmd_stories(client, args):
    """View stories of a user/channel."""
    entity = await client.get_entity(args.target)
    name = getattr(entity, "title", None) or fmt_user(entity)
    peer = await client.get_input_entity(entity)
    try:
        result = await client(GetPeerStoriesRequest(peer=peer))
        stories = result.stories.stories if result.stories else []
        print(f"=== Stories of {name} ({len(stories)} stories) ===\n")
        for s in stories:
            date = fmt_date(s.date)
            views = getattr(s, "views", None)
            views_str = f" ({views.views_count} views)" if views else ""
            caption = getattr(s, "caption", "") or ""
            print(f"  [{date}] Story #{s.id}{views_str}")
            if caption:
                print(f"    {caption[:200]}")
    except Exception as e:
        print(f"Error: {e}\n(User may not have active stories)")


async def cmd_saved(client, args):
    """Read saved messages (bookmarks)."""
    limit = args.limit or 30
    me = await client.get_me()
    print(f"=== Saved Messages (limit {limit}) ===\n")

    async for msg in client.iter_messages("me", limit=limit):
        media = fmt_media(msg) if msg.media else ""
        text = (msg.text or "")[:300]
        fwd = ""
        if msg.forward:
            fwd_name = ""
            if msg.forward.sender:
                fwd_name = fmt_user(msg.forward.sender) if isinstance(msg.forward.sender, User) else getattr(msg.forward.sender, "title", "")
            elif msg.forward.sender_name:
                fwd_name = msg.forward.sender_name
            fwd = f" [from: {fwd_name}]" if fwd_name else ""
        print(f"[{fmt_date(msg.date)}] #{msg.id}{fwd}: {media}{text}")

    print()


async def cmd_blocked_list(client, args):
    """List blocked users."""
    from telethon.tl.functions.contacts import GetBlockedRequest
    result = await client(GetBlockedRequest(offset=0, limit=args.limit or 100))
    users = {u.id: u for u in result.users}
    print(f"=== Blocked users ({len(result.blocked)}) ===\n")
    for b in result.blocked:
        user = users.get(b.peer_id.user_id)
        if user:
            print(f"  {fmt_user(user)} (blocked {fmt_date(b.date)})")


async def cmd_unread(client, args):
    """Show chats with unread messages."""
    limit = args.limit or 30
    print(f"=== Unread chats (limit {limit}) ===\n")
    count = 0
    async for dialog in client.iter_dialogs(limit=200):
        if dialog.unread_count > 0:
            dtype = "channel" if dialog.is_channel else "group" if dialog.is_group else "user"
            print(f"  [{dtype}] {dialog.name}: {dialog.unread_count} unread")
            count += 1
            if count >= limit:
                break
    print(f"\n--- {count} chats with unread ---")


async def cmd_poll_results(client, args):
    """Get poll vote results."""
    entity = await client.get_entity(args.target)
    msg = await client.get_messages(entity, ids=int(args.msg_id))
    if not msg or not msg.media or not isinstance(msg.media, MessageMediaPoll):
        print("Message is not a poll")
        return

    poll = msg.media.poll
    results = msg.media.results
    print(f"=== Poll: {poll.question} ===\n")
    for i, answer in enumerate(poll.answers):
        answer_text = answer.text
        voters = 0
        if results and results.results:
            for r in results.results:
                if r.option == answer.option:
                    voters = r.voters
                    break
        print(f"  {answer_text}: {voters} votes")
    total = results.total_voters if results else 0
    print(f"\nTotal voters: {total}")


async def cmd_broadcast(client, args):
    """Send a message to multiple users (from comma-separated list or file)."""
    if args.file:
        targets = Path(args.file).read_text(encoding="utf-8").strip().splitlines()
    else:
        targets = [t.strip() for t in args.targets.split(",")]

    delay = float(args.delay or 2)
    total = len(targets)
    sent = 0
    failed = 0

    print(f"=== Broadcasting to {total} targets (delay {delay}s) ===\n")

    for i, target in enumerate(targets):
        target = target.strip()
        if not target:
            continue
        try:
            entity = await client.get_entity(target)
            await client.send_message(entity, args.text)
            name = getattr(entity, "title", None) or fmt_user(entity)
            print(f"  [{i+1}/{total}] Sent to {name}")
            sent += 1
            if i < total - 1:
                await asyncio.sleep(delay)
        except Exception as e:
            print(f"  [{i+1}/{total}] FAILED {target}: {e}")
            failed += 1

    print(f"\n--- Sent: {sent}, Failed: {failed} ---")


# ========== STAR GIFTS ==========

async def cmd_star_gifts(client, args):
    """List available star gifts."""
    from telethon import functions
    result = await client(functions.payments.GetStarGiftsRequest(hash=0))
    gifts = getattr(result, 'gifts', [])
    print(f"Available star gifts: {len(gifts)}")
    for g in gifts[:20]:
        stars = getattr(g, 'stars', '?')
        limited = ' [LIMITED]' if getattr(g, 'limited', False) else ''
        sold = getattr(g, 'sold_count', 0)
        avail = getattr(g, 'availability_remains', '?')
        print(f"  ID:{getattr(g, 'id', '?')} | {stars} stars{limited} | sold:{sold} | remaining:{avail}")


async def cmd_send_star_gift(client, args):
    """Send a star gift to a user."""
    from telethon import functions, types
    target = await client.get_entity(args.target)
    result = await client(functions.payments.SendStarGiftRequest(
        peer=target,
        gift_id=args.gift_id,
        message=types.TextWithEntities(text=args.message or '', entities=[]) if args.message else None,
        hide_name=args.anonymous or False,
    ))
    print(f"Star gift sent to {args.target}")


# ========== STORIES (EXTENDED) ==========

async def cmd_post_story(client, args):
    """Post a story (photo/video)."""
    from telethon import functions, types
    import os

    peer = 'me'
    if args.channel:
        peer = await client.get_entity(args.channel)
    else:
        peer = await client.get_me()

    # Upload media
    file = await client.upload_file(args.file)

    # Determine media type
    ext = os.path.splitext(args.file)[1].lower()
    if ext in ('.mp4', '.mov', '.avi', '.mkv'):
        media = types.InputMediaUploadedDocument(
            file=file, mime_type='video/mp4', attributes=[
                types.DocumentAttributeVideo(duration=0, w=1080, h=1920, round_message=False, supports_streaming=True)
            ]
        )
    else:
        media = types.InputMediaUploadedPhoto(file=file)

    result = await client(functions.stories.SendStoryRequest(
        peer=peer,
        media=media,
        caption=args.caption or '',
        privacy_rules=[types.InputPrivacyValueAllowAll()] if not args.contacts_only else [types.InputPrivacyValueAllowContacts()],
        period=args.period or 86400,  # 24h default
    ))
    print(f"Story posted! ID: {getattr(result, 'id', '?')}")


async def cmd_story_views(client, args):
    """Get viewers of a story."""
    from telethon import functions
    me = await client.get_me()
    result = await client(functions.stories.GetStoryViewsListRequest(
        peer=me,
        id=args.story_id,
        offset='',
        limit=args.limit or 100,
        q='',
    ))
    viewers = getattr(result, 'views', [])
    print(f"Story #{args.story_id} viewers: {len(viewers)}")
    for v in viewers:
        user_id = getattr(v, 'user_id', '?')
        date = getattr(v, 'date', '')
        print(f"  User {user_id} | {date}")


async def cmd_story_albums(client, args):
    """List story albums."""
    from telethon import functions
    peer = await client.get_entity(args.target) if args.target else await client.get_me()
    result = await client(functions.stories.GetAlbumsRequest(peer=peer, hash=0))
    albums = getattr(result, 'albums', [])
    print(f"Story albums: {len(albums)}")
    for a in albums:
        print(f"  ID:{getattr(a, 'id', '?')} | {getattr(a, 'title', '?')} | stories: {getattr(a, 'count', '?')}")


# ========== PREMIUM ==========

async def cmd_boost(client, args):
    """Boost a channel."""
    from telethon import functions
    peer = await client.get_entity(args.channel)
    try:
        result = await client(functions.premium.ApplyBoostRequest(peer=peer))
        print(f"Boosted {args.channel}!")
    except Exception as e:
        print(f"Boost failed: {e}")


# ========== STORIES EXTENDED ==========

async def cmd_edit_story(client, args):
    """Edit a story caption."""
    from telethon import functions
    peer = await client.get_entity(args.channel) if args.channel else await client.get_me()
    await client(functions.stories.EditStoryRequest(
        peer=peer, id=args.story_id,
        caption=args.caption or '',
    ))
    print(f"Story #{args.story_id} edited")


async def cmd_pin_story(client, args):
    """Pin/unpin a story."""
    from telethon import functions
    peer = await client.get_entity(args.channel) if args.channel else await client.get_me()
    await client(functions.stories.TogglePinnedRequest(
        peer=peer, id=[args.story_id], pinned=not args.unpin
    ))
    print(f"Story #{args.story_id} {'unpinned' if args.unpin else 'pinned'}")


async def cmd_story_reactions(client, args):
    """Get reactions on a story."""
    from telethon import functions
    peer = await client.get_entity(args.channel) if args.channel else await client.get_me()
    result = await client(functions.stories.GetStoryReactionsListRequest(
        peer=peer, id=args.story_id, offset='', limit=args.limit or 100,
    ))
    reactions = getattr(result, 'reactions', [])
    print(f"Story #{args.story_id} reactions: {len(reactions)}")
    for r in reactions:
        user_id = getattr(r, 'peer_id', '?')
        emoji = getattr(r, 'reaction', '?')
        print(f"  {user_id} → {emoji}")


async def cmd_react_story(client, args):
    """React to a story with emoji."""
    from telethon import functions, types
    peer = await client.get_entity(args.target)
    await client(functions.stories.SendReactionRequest(
        peer=peer, story_id=args.story_id,
        reaction=types.ReactionEmoji(emoticon=args.emoji),
    ))
    print(f"Reacted {args.emoji} to story #{args.story_id}")


async def cmd_stealth_mode(client, args):
    """Activate stealth mode for viewing stories anonymously."""
    from telethon import functions
    result = await client(functions.stories.ActivateStealthModeRequest(
        past=True, future=True
    ))
    print("Stealth mode activated! You can view stories anonymously for 25 minutes.")


async def cmd_story_archive(client, args):
    """View stories archive."""
    from telethon import functions
    peer = await client.get_entity(args.target) if args.target else await client.get_me()
    result = await client(functions.stories.GetStoriesArchiveRequest(
        peer=peer, offset_id=0, limit=args.limit or 50
    ))
    stories_list = getattr(result, 'stories', [])
    print(f"Archived stories: {len(stories_list)}")
    for s in stories_list:
        sid = getattr(s, 'id', '?')
        date = getattr(s, 'date', '')
        caption = getattr(s, 'caption', '') or ''
        print(f"  #{sid} | {date} | {caption[:60]}")


async def cmd_export_story_link(client, args):
    """Export a link to a story."""
    from telethon import functions
    peer = await client.get_entity(args.target) if args.target else await client.get_me()
    result = await client(functions.stories.ExportStoryLinkRequest(
        peer=peer, id=args.story_id
    ))
    print(f"Story link: {getattr(result, 'link', result)}")


# ========== STARS / PAYMENTS ==========

async def cmd_stars_balance(client, args):
    """Check Telegram Stars balance."""
    from telethon import functions, types
    result = await client(functions.payments.GetStarsStatusRequest(peer=types.InputPeerSelf()))
    balance = getattr(result, 'balance', '?')
    print(f"Stars balance: {balance}")


async def cmd_stars_history(client, args):
    """View Stars transaction history."""
    from telethon import functions, types
    result = await client(functions.payments.GetStarsTransactionsRequest(
        peer=types.InputPeerSelf(), offset='', limit=args.limit or 20,
        inbound=args.inbound or False, outbound=args.outbound or False,
    ))
    transactions = getattr(result, 'history', [])
    print(f"Stars transactions: {len(transactions)}")
    for t in transactions:
        stars = getattr(t, 'stars', '?')
        date = getattr(t, 'date', '')
        title = getattr(t, 'title', '') or getattr(t, 'description', '') or ''
        direction = '<-' if getattr(t, 'stars', 0) > 0 else '->'
        print(f"  {direction} {stars} stars | {date} | {title[:50]}")


async def cmd_saved_gifts(client, args):
    """View received star gifts."""
    from telethon import functions, types
    peer = await client.get_entity(args.target) if args.target else types.InputPeerSelf()
    result = await client(functions.payments.GetSavedStarGiftsRequest(
        peer=peer, offset='', limit=args.limit or 20
    ))
    gifts = getattr(result, 'gifts', [])
    print(f"Saved gifts: {len(gifts)}")
    for g in gifts:
        from_id = getattr(g, 'from_id', '?')
        date = getattr(g, 'date', '')
        stars = getattr(g, 'stars', '?')
        print(f"  From {from_id} | {date} | {stars} stars")


async def cmd_convert_gift(client, args):
    """Convert a star gift to stars."""
    from telethon import functions, types
    await client(functions.payments.ConvertStarGiftRequest(
        stargift=types.InputSavedStarGiftUser(msg_id=args.msg_id)
    ))
    print("Gift converted to stars!")


async def cmd_gift_premium(client, args):
    """Gift Telegram Premium to a user."""
    from telethon import functions, types
    target = await client.get_entity(args.target)
    options = await client(functions.payments.GetPremiumGiftCodeOptionsRequest(
        peer=target, boost_peer=None
    ))
    print("Premium gift options:")
    for o in options:
        months = getattr(o, 'months', '?')
        amount = getattr(o, 'amount', '?')
        currency = getattr(o, 'currency', '?')
        print(f"  {months} months = {amount} {currency}")


async def cmd_giveaway_info(client, args):
    """Get info about a giveaway."""
    from telethon import functions
    peer = await client.get_entity(args.channel)
    result = await client(functions.payments.GetGiveawayInfoRequest(
        peer=peer, msg_id=args.msg_id
    ))
    print(f"Giveaway info: {result.stringify() if hasattr(result, 'stringify') else result}")


# ========== BUSINESS ==========

async def cmd_set_business_hours(client, args):
    """Set business working hours."""
    from telethon import functions, types
    if args.clear:
        await client(functions.account.UpdateBusinessWorkHoursRequest(business_work_hours=None))
        print("Business hours cleared")
    else:
        periods = []
        for day in range(7):
            periods.append(types.BusinessWeeklyOpen(
                start_minute=day * 1440 + int(args.open.split(':')[0]) * 60 + int(args.open.split(':')[1]),
                end_minute=day * 1440 + int(args.close.split(':')[0]) * 60 + int(args.close.split(':')[1]),
            ))
        await client(functions.account.UpdateBusinessWorkHoursRequest(
            business_work_hours=types.BusinessWorkHours(
                timezone_id=args.timezone or 'UTC',
                weekly_open=periods
            )
        ))
        print(f"Business hours set: {args.open}-{args.close} ({args.timezone or 'UTC'})")


async def cmd_set_business_location(client, args):
    """Set business location."""
    from telethon import functions, types
    if args.clear:
        await client(functions.account.UpdateBusinessLocationRequest(business_location=None))
        print("Business location cleared")
    else:
        await client(functions.account.UpdateBusinessLocationRequest(
            business_location=types.BusinessLocation(
                address=args.address,
                geo_point=None,
            )
        ))
        print(f"Business location set: {args.address}")


async def cmd_set_business_greeting(client, args):
    """Set business auto-greeting message."""
    from telethon import functions, types
    if args.clear:
        await client(functions.account.UpdateBusinessGreetingMessageRequest(message=None))
        print("Greeting cleared")
    else:
        await client(functions.account.UpdateBusinessGreetingMessageRequest(
            message=types.InputBusinessGreetingMessage(
                shortcut_id=0,
                recipients=types.InputBusinessRecipients(new_chats=True, existing_chats=True),
                no_activity_days=args.days or 7,
            )
        ))
        print(f"Business greeting set (inactivity: {args.days or 7} days)")


async def cmd_set_business_away(client, args):
    """Set business away auto-reply."""
    from telethon import functions, types
    if args.clear:
        await client(functions.account.UpdateBusinessAwayMessageRequest(message=None))
        print("Away message cleared")
    else:
        await client(functions.account.UpdateBusinessAwayMessageRequest(
            message=types.InputBusinessAwayMessage(
                shortcut_id=0,
                recipients=types.InputBusinessRecipients(new_chats=True, existing_chats=True),
                schedule=types.BusinessAwayMessageScheduleAlways(),
                offline_only=args.offline_only or False,
            )
        ))
        print("Business away message set")


async def cmd_business_links(client, args):
    """List business chat links."""
    from telethon import functions
    result = await client(functions.account.GetBusinessChatLinksRequest())
    links = getattr(result, 'links', [])
    print(f"Business links: {len(links)}")
    for l in links:
        url = getattr(l, 'link', '?')
        title = getattr(l, 'title', '') or ''
        print(f"  {url} | {title}")


# ========== ACCOUNT EXTENDED ==========

async def cmd_set_birthday(client, args):
    """Set your birthday."""
    from telethon import functions, types
    if args.clear:
        await client(functions.account.UpdateBirthdayRequest(birthday=None))
        print("Birthday cleared")
    else:
        parts = args.date.split('-')
        await client(functions.account.UpdateBirthdayRequest(
            birthday=types.Birthday(
                day=int(parts[2]) if len(parts) == 3 else int(parts[1]),
                month=int(parts[1]) if len(parts) == 3 else int(parts[0]),
                year=int(parts[0]) if len(parts) == 3 and len(parts[0]) == 4 else None
            )
        ))
        print(f"Birthday set: {args.date}")


async def cmd_set_emoji_status(client, args):
    """Set emoji status."""
    from telethon import functions, types
    if args.clear:
        await client(functions.account.UpdateEmojiStatusRequest(emoji_status=types.EmojiStatusEmpty()))
        print("Emoji status cleared")
    else:
        await client(functions.account.UpdateEmojiStatusRequest(
            emoji_status=types.EmojiStatus(document_id=int(args.emoji_id))
        ))
        print(f"Emoji status set: {args.emoji_id}")


async def cmd_close_friends(client, args):
    """Manage close friends list."""
    from telethon import functions
    if args.add:
        users = [await client.get_entity(u) for u in args.add]
        user_ids = [u.id for u in users]
        await client(functions.contacts.EditCloseFriendsRequest(id=user_ids))
        print(f"Added {len(user_ids)} users to close friends")
    else:
        print("Use --add @user1 @user2 to set close friends list")


async def cmd_online_count(client, args):
    """Get online users count in a chat."""
    from telethon import functions
    peer = await client.get_entity(args.chat)
    result = await client(functions.messages.GetOnlinesRequest(peer=peer))
    count = getattr(result, 'onlines', 0)
    print(f"Online in {args.chat}: {count} users")


async def cmd_contact_birthdays(client, args):
    """Get contacts' birthdays."""
    from telethon import functions
    result = await client(functions.contacts.GetBirthdaysRequest())
    contacts = getattr(result, 'contacts', [])
    users = {u.id: u for u in getattr(result, 'users', [])}
    print(f"Contact birthdays: {len(contacts)}")
    for c in contacts:
        uid = getattr(c, 'contact_id', '?')
        birthday = getattr(c, 'birthday', None)
        user = users.get(uid)
        name = fmt_user(user) if user else str(uid)
        if birthday:
            day = getattr(birthday, 'day', '?')
            month = getattr(birthday, 'month', '?')
            print(f"  {name}: {day}/{month}")


async def cmd_resolve_phone(client, args):
    """Find a user by phone number."""
    from telethon import functions
    result = await client(functions.contacts.ResolvePhoneRequest(phone=args.phone))
    peer = getattr(result, 'peer', None)
    users = getattr(result, 'users', [])
    if users:
        u = users[0]
        print(f"Found: {fmt_user(u)} (ID: {u.id})")
    else:
        print(f"No user found for +{args.phone}")


# ========== CHANNELS EXTENDED ==========

async def cmd_toggle_forum(client, args):
    """Toggle forum mode for a group/channel."""
    from telethon import functions
    peer = await client.get_entity(args.channel)
    await client(functions.channels.ToggleForumRequest(channel=peer, enabled=not args.disable))
    print(f"Forum mode {'disabled' if args.disable else 'enabled'} for {args.channel}")


async def cmd_export_msg_link(client, args):
    """Export a permanent link to a message."""
    from telethon import functions
    peer = await client.get_entity(args.channel)
    result = await client(functions.channels.ExportMessageLinkRequest(
        channel=peer, id=args.msg_id, grouped=False, thread=False
    ))
    print(f"Link: {getattr(result, 'link', result)}")


async def cmd_set_channel_emoji(client, args):
    """Set channel emoji status."""
    from telethon import functions, types
    peer = await client.get_entity(args.channel)
    if args.clear:
        await client(functions.channels.UpdateEmojiStatusRequest(
            channel=peer, emoji_status=types.EmojiStatusEmpty()
        ))
        print("Channel emoji status cleared")
    else:
        await client(functions.channels.UpdateEmojiStatusRequest(
            channel=peer, emoji_status=types.EmojiStatus(document_id=int(args.emoji_id))
        ))
        print(f"Channel emoji status set: {args.emoji_id}")


async def cmd_toggle_signatures(client, args):
    """Toggle message signatures in channel."""
    from telethon import functions
    peer = await client.get_entity(args.channel)
    await client(functions.channels.ToggleSignaturesRequest(
        channel=peer, signatures_enabled=not args.disable, profiles_enabled=args.profiles or False
    ))
    print(f"Signatures {'disabled' if args.disable else 'enabled'} for {args.channel}")


# ========== MESSAGES EXTRAS ==========

async def cmd_translate_msg(client, args):
    """Translate a message."""
    from telethon import functions
    peer = await client.get_entity(args.chat)
    result = await client(functions.messages.TranslateTextRequest(
        peer=peer, id=[args.msg_id], to_lang=args.lang or 'en'
    ))
    translations = getattr(result, 'result', [])
    for t in translations:
        print(f"Translation ({args.lang or 'en'}): {getattr(t, 'text', t)}")


async def cmd_transcribe_voice(client, args):
    """Transcribe a voice message."""
    from telethon import functions
    peer = await client.get_entity(args.chat)
    result = await client(functions.messages.TranscribeAudioRequest(
        peer=peer, msg_id=args.msg_id
    ))
    text = getattr(result, 'text', '')
    pending = getattr(result, 'pending', False)
    print(f"Transcription{'(pending)' if pending else ''}: {text}")


# --- AI commands ---

async def cmd_ai_compose(client, args):
    """Compose/improve text with Telegram AI."""
    from telethon import functions, types
    text_obj = types.TextWithEntities(text=args.text, entities=[])
    result = await client(functions.messages.ComposeMessageWithAIRequest(
        text=text_obj,
        proofread=args.proofread or False,
        emojify=args.emojify or False,
        translate_to_lang=args.translate or None,
        change_tone=args.tone or None,
    ))
    composed = getattr(result, 'text', result)
    if hasattr(composed, 'text'):
        print(f"AI result: {composed.text}")
    else:
        print(f"AI result: {composed}")


async def cmd_ai_proofread(client, args):
    """Proofread text with Telegram AI."""
    from telethon import functions, types
    text_obj = types.TextWithEntities(text=args.text, entities=[])
    result = await client(functions.messages.ComposeMessageWithAIRequest(
        text=text_obj, proofread=True
    ))
    composed = getattr(result, 'text', result)
    print(f"Proofread: {composed.text if hasattr(composed, 'text') else composed}")


async def cmd_ai_emojify(client, args):
    """Add emojis to text with Telegram AI."""
    from telethon import functions, types
    text_obj = types.TextWithEntities(text=args.text, entities=[])
    result = await client(functions.messages.ComposeMessageWithAIRequest(
        text=text_obj, emojify=True
    ))
    composed = getattr(result, 'text', result)
    print(f"Emojified: {composed.text if hasattr(composed, 'text') else composed}")


async def cmd_ai_translate(client, args):
    """Translate text with Telegram AI."""
    from telethon import functions, types
    text_obj = types.TextWithEntities(text=args.text, entities=[])
    result = await client(functions.messages.ComposeMessageWithAIRequest(
        text=text_obj, translate_to_lang=args.lang
    ))
    composed = getattr(result, 'text', result)
    print(f"Translation ({args.lang}): {composed.text if hasattr(composed, 'text') else composed}")


async def cmd_ai_change_tone(client, args):
    """Change text tone with Telegram AI."""
    from telethon import functions, types
    text_obj = types.TextWithEntities(text=args.text, entities=[])
    result = await client(functions.messages.ComposeMessageWithAIRequest(
        text=text_obj, change_tone=args.tone
    ))
    composed = getattr(result, 'text', result)
    print(f"Tone ({args.tone}): {composed.text if hasattr(composed, 'text') else composed}")


# --- Chat management ---

async def cmd_set_auto_delete(client, args):
    """Set auto-delete timer for messages."""
    from telethon import functions
    peer = await client.get_entity(args.chat)
    await client(functions.messages.SetHistoryTTLRequest(
        peer=peer, period=args.seconds
    ))
    if args.seconds == 0:
        print(f"Auto-delete disabled for {args.chat}")
    else:
        hours = args.seconds / 3600
        print(f"Auto-delete set to {hours:.0f}h for {args.chat}")


async def cmd_create_topic(client, args):
    """Create a forum topic."""
    from telethon import functions
    peer = await client.get_entity(args.channel)
    result = await client(functions.channels.CreateForumTopicRequest(
        channel=peer, title=args.title,
        icon_color=args.color or None,
    ))
    print(f"Topic '{args.title}' created")


async def cmd_chat_themes(client, args):
    """List available chat themes."""
    from telethon import functions
    result = await client(functions.account.GetChatThemesRequest(hash=0))
    themes = getattr(result, 'themes', [])
    print(f"Chat themes: {len(themes)}")
    for t in themes:
        slug = getattr(t, 'slug', '?')
        title = getattr(t, 'title', '?')
        print(f"  {slug}: {title}")


async def cmd_toggle_sponsored(client, args):
    """Toggle sponsored messages (ads) on/off."""
    from telethon import functions
    await client(functions.account.ToggleSponsoredMessagesRequest(
        enabled=not args.disable
    ))
    print(f"Sponsored messages {'disabled' if args.disable else 'enabled'}")


# --- Account/Profile extended ---

async def cmd_set_personal_channel(client, args):
    """Link a personal channel to your profile."""
    from telethon import functions, types
    if args.clear:
        await client(functions.account.UpdatePersonalChannelRequest(channel=types.InputChannelEmpty()))
        print("Personal channel cleared")
    else:
        channel = await client.get_entity(args.channel)
        await client(functions.account.UpdatePersonalChannelRequest(channel=channel))
        print(f"Personal channel set: {args.channel}")


async def cmd_set_color(client, args):
    """Set profile/reply color."""
    from telethon import functions
    await client(functions.account.UpdateColorRequest(
        for_profile=args.profile or False,
        color=args.color_id,
        background_emoji_id=int(args.emoji_id) if args.emoji_id else None,
    ))
    target = "profile" if args.profile else "replies"
    print(f"{target.title()} color set to {args.color_id}")


async def cmd_paid_msg_revenue(client, args):
    """Check paid messages revenue."""
    from telethon import functions, types
    result = await client(functions.account.GetPaidMessagesRevenueRequest(
        user_id=types.InputUserSelf()
    ))
    print(f"Paid messages revenue: {result}")


async def cmd_saved_music(client, args):
    """List saved music IDs."""
    from telethon import functions
    result = await client(functions.account.GetSavedMusicIdsRequest(hash=0))
    ids = getattr(result, 'ids', [])
    print(f"Saved music: {len(ids)} tracks")
    for mid in ids[:20]:
        print(f"  ID: {mid}")


async def cmd_set_wallpaper(client, args):
    """Set chat wallpaper."""
    from telethon import functions, types
    if args.reset:
        await client(functions.account.ResetWallPapersRequest())
        print("Wallpapers reset to default")
    else:
        result = await client(functions.account.GetWallPapersRequest(hash=0))
        wallpapers = getattr(result, 'wallpapers', [])
        print(f"Available wallpapers: {len(wallpapers)}")
        for w in wallpapers[:10]:
            slug = getattr(w, 'slug', '?')
            print(f"  {slug}")


# --- Stickers & Emoji ---
async def cmd_my_stickers(client, args):
    """List your sticker sets."""
    from telethon import functions
    result = await client(functions.messages.GetMyStickersRequest(offset_id=0, limit=args.limit or 20))
    sets = getattr(result, 'sets', [])
    print(f"Your sticker sets: {len(sets)}")
    for s in sets:
        title = getattr(s, 'title', '?')
        short = getattr(s, 'short_name', '?')
        count = getattr(s, 'count', 0)
        print(f"  {title} (@{short}) — {count} stickers")

async def cmd_emoji_packs(client, args):
    """List installed emoji packs."""
    from telethon import functions
    result = await client(functions.messages.GetEmojiStickersRequest(hash=0))
    sets = getattr(result, 'sets', [])
    print(f"Emoji packs: {len(sets)}")
    for s in sets:
        title = getattr(s, 'title', '?')
        short = getattr(s, 'short_name', '?')
        count = getattr(s, 'count', 0)
        print(f"  {title} (@{short}) — {count} emoji")

async def cmd_featured_stickers(client, args):
    """List featured/trending sticker sets."""
    from telethon import functions
    result = await client(functions.messages.GetFeaturedStickersRequest(hash=0))
    sets = getattr(result, 'sets', [])
    print(f"Featured stickers: {len(sets)}")
    for s in sets[:20]:
        sset = getattr(s, 'set', s)
        title = getattr(sset, 'title', '?')
        short = getattr(sset, 'short_name', '?')
        print(f"  {title} (@{short})")

async def cmd_install_stickers(client, args):
    """Install a sticker set."""
    from telethon import functions, types
    result = await client(functions.messages.InstallStickerSetRequest(
        stickerset=types.InputStickerSetShortName(short_name=args.short_name),
        archived=False
    ))
    print(f"Sticker set @{args.short_name} installed!")

async def cmd_uninstall_stickers(client, args):
    """Uninstall a sticker set."""
    from telethon import functions, types
    await client(functions.messages.UninstallStickerSetRequest(
        stickerset=types.InputStickerSetShortName(short_name=args.short_name)
    ))
    print(f"Sticker set @{args.short_name} uninstalled")


# --- Privacy ---
async def cmd_get_privacy(client, args):
    """Get privacy settings for a key."""
    from telethon import functions, types
    keys = {
        'phone': types.InputPrivacyKeyPhoneNumber(),
        'lastseen': types.InputPrivacyKeyStatusTimestamp(),
        'photo': types.InputPrivacyKeyProfilePhoto(),
        'bio': types.InputPrivacyKeyAbout(),
        'birthday': types.InputPrivacyKeyBirthday(),
        'forwards': types.InputPrivacyKeyForwards(),
        'calls': types.InputPrivacyKeyPhoneCall(),
        'invite': types.InputPrivacyKeyChatInvite(),
        'voice': types.InputPrivacyKeyVoiceMessages(),
        'messages': types.InputPrivacyKeyStatusTimestamp(),
    }
    key = keys.get(args.key)
    if not key:
        print(f"Unknown key. Available: {', '.join(keys.keys())}")
        return
    result = await client(functions.account.GetPrivacyRequest(key=key))
    rules = getattr(result, 'rules', [])
    print(f"Privacy for '{args.key}': {len(rules)} rules")
    for r in rules:
        print(f"  {type(r).__name__}")

async def cmd_set_privacy(client, args):
    """Set privacy to everybody/contacts/nobody."""
    from telethon import functions, types
    keys = {
        'phone': types.InputPrivacyKeyPhoneNumber(),
        'lastseen': types.InputPrivacyKeyStatusTimestamp(),
        'photo': types.InputPrivacyKeyProfilePhoto(),
        'bio': types.InputPrivacyKeyAbout(),
        'birthday': types.InputPrivacyKeyBirthday(),
        'forwards': types.InputPrivacyKeyForwards(),
        'calls': types.InputPrivacyKeyPhoneCall(),
        'invite': types.InputPrivacyKeyChatInvite(),
        'voice': types.InputPrivacyKeyVoiceMessages(),
    }
    values = {
        'everybody': [types.InputPrivacyValueAllowAll()],
        'contacts': [types.InputPrivacyValueAllowContacts()],
        'nobody': [types.InputPrivacyValueDisallowAll()],
    }
    key = keys.get(args.key)
    rules = values.get(args.value)
    if not key:
        print(f"Unknown key. Available: {', '.join(keys.keys())}")
        return
    if not rules:
        print(f"Unknown value. Use: everybody, contacts, nobody")
        return
    await client(functions.account.SetPrivacyRequest(key=key, rules=rules))
    print(f"Privacy for '{args.key}' set to '{args.value}'")

async def cmd_sessions(client, args):
    """List active sessions/devices."""
    from telethon import functions
    result = await client(functions.account.GetAuthorizationsRequest())
    auths = getattr(result, 'authorizations', [])
    print(f"Active sessions: {len(auths)}")
    for a in auths:
        current = " [CURRENT]" if getattr(a, 'current', False) else ""
        device = getattr(a, 'device_model', '?')
        platform = getattr(a, 'platform', '?')
        app = getattr(a, 'app_name', '?')
        country = getattr(a, 'country', '?')
        ip = getattr(a, 'ip', '?')
        date = getattr(a, 'date_active', '')
        print(f"  {device} ({platform}) — {app} | {country} {ip} | {date}{current}")


# --- Misc ---
async def cmd_nearby(client, args):
    """Find nearby users/groups (requires location)."""
    from telethon import functions, types
    result = await client(functions.contacts.GetLocatedRequest(
        geo_point=types.InputGeoPoint(lat=float(args.lat), long=float(args.lon)),
        self_expires=0,
    ))
    peers = getattr(result, 'updates', [])
    print(f"Nearby results: {len(peers)}")
    for p in peers:
        print(f"  {type(p).__name__}: {p}")

async def cmd_report(client, args):
    """Report a user/channel/message."""
    from telethon import functions, types
    peer = await client.get_entity(args.target)
    reasons = {
        'spam': types.InputReportReasonSpam(),
        'violence': types.InputReportReasonViolence(),
        'porn': types.InputReportReasonPornography(),
        'abuse': types.InputReportReasonChildAbuse(),
        'copyright': types.InputReportReasonCopyright(),
        'fake': types.InputReportReasonFake(),
        'drugs': types.InputReportReasonIllegalDrugs(),
        'personal': types.InputReportReasonPersonalDetails(),
        'other': types.InputReportReasonOther(),
    }
    reason = reasons.get(args.reason, types.InputReportReasonOther())
    await client(functions.account.ReportPeerRequest(
        peer=peer, reason=reason, message=args.message or ''
    ))
    print(f"Reported {args.target} for {args.reason}")

async def cmd_add_contact(client, args):
    """Add a contact by phone or username."""
    from telethon import functions, types
    result = await client(functions.contacts.AddContactRequest(
        id=await client.get_entity(args.target),
        first_name=args.first_name or '',
        last_name=args.last_name or '',
        phone=args.phone or '',
        add_phone_privacy_exception=True,
    ))
    print(f"Contact added: {args.target}")

async def cmd_delete_contact(client, args):
    """Delete a contact."""
    from telethon import functions
    target = await client.get_entity(args.target)
    result = await client(functions.contacts.DeleteContactsRequest(id=[target]))
    print(f"Contact deleted: {args.target}")


# --- Account / Settings (batch 5) ---
async def cmd_ringtones(client, args):
    """List saved notification ringtones."""
    from telethon import functions
    result = await client(functions.account.GetSavedRingtonesRequest(hash=0))
    tones = getattr(result, 'ringtones', [])
    print(f"Saved ringtones: {len(tones)}")
    for t in tones:
        print(f"  ID:{getattr(t, 'id', '?')} | size:{getattr(t, 'size', '?')}")

async def cmd_global_privacy(client, args):
    """View/set global privacy settings."""
    from telethon import functions
    if args.set:
        from telethon import types
        await client(functions.account.SetGlobalPrivacySettingsRequest(
            settings=types.GlobalPrivacySettings(
                archive_and_mute_new_noncontact_peers=args.archive_new or False,
                keep_archived_unmuted=args.keep_archived or False,
                keep_archived_folders=args.keep_folders or False,
                hide_read_marks=args.hide_read or False,
                new_noncontact_peers_require_premium=args.require_premium or False,
            )
        ))
        print("Global privacy updated")
    else:
        result = await client(functions.account.GetGlobalPrivacySettingsRequest())
        s = getattr(result, 'settings', result)
        print(f"Archive new chats: {getattr(s, 'archive_and_mute_new_noncontact_peers', '?')}")
        print(f"Keep archived unmuted: {getattr(s, 'keep_archived_unmuted', '?')}")
        print(f"Hide read marks: {getattr(s, 'hide_read_marks', '?')}")
        print(f"Require Premium for new: {getattr(s, 'new_noncontact_peers_require_premium', '?')}")

async def cmd_reorder_usernames(client, args):
    """Reorder your usernames."""
    from telethon import functions
    await client(functions.account.ReorderUsernamesRequest(order=args.usernames))
    print(f"Usernames reordered: {', '.join(args.usernames)}")

async def cmd_connected_bots(client, args):
    """List bots connected to your account (business)."""
    from telethon import functions
    result = await client(functions.account.GetConnectedBotsRequest())
    bots = getattr(result, 'connected_bots', [])
    print(f"Connected bots: {len(bots)}")
    for b in bots:
        bot_id = getattr(b, 'bot_id', '?')
        print(f"  Bot ID: {bot_id}")

async def cmd_web_sessions(client, args):
    """List active web sessions (Telegram Web logins)."""
    from telethon import functions
    result = await client(functions.account.GetWebAuthorizationsRequest())
    auths = getattr(result, 'authorizations', [])
    print(f"Web sessions: {len(auths)}")
    for a in auths:
        domain = getattr(a, 'domain', '?')
        platform = getattr(a, 'platform', '?')
        browser = getattr(a, 'browser', '?')
        date = getattr(a, 'date_active', '')
        ip = getattr(a, 'ip', '?')
        region = getattr(a, 'region', '?')
        print(f"  {domain} | {browser}/{platform} | {ip} ({region}) | {date}")

async def cmd_account_ttl(client, args):
    """Get/set account self-destruct timer."""
    from telethon import functions, types
    if args.days:
        await client(functions.account.SetAccountTTLRequest(
            ttl=types.AccountDaysTTL(days=args.days)
        ))
        print(f"Account TTL set to {args.days} days")
    else:
        result = await client(functions.account.GetAccountTTLRequest())
        days = getattr(result, 'days', '?')
        print(f"Account self-destruct: {days} days of inactivity")

async def cmd_content_settings(client, args):
    """Toggle sensitive content (18+) visibility."""
    from telethon import functions
    if args.show:
        await client(functions.account.SetContentSettingsRequest(sensitive_enabled=True))
        print("Sensitive content enabled")
    elif args.hide:
        await client(functions.account.SetContentSettingsRequest(sensitive_enabled=False))
        print("Sensitive content disabled")
    else:
        result = await client(functions.account.GetContentSettingsRequest())
        enabled = getattr(result, 'sensitive_enabled', '?')
        can_change = getattr(result, 'sensitive_can_change', '?')
        print(f"Sensitive content: {'enabled' if enabled else 'disabled'} (can change: {can_change})")

async def cmd_contact_photo(client, args):
    """Set/suggest profile photo for a contact."""
    from telethon import functions
    target = await client.get_entity(args.target)
    file = await client.upload_file(args.file)
    result = await client(functions.photos.UploadContactProfilePhotoRequest(
        user_id=target, file=file,
        suggest=args.suggest or False, save=not args.suggest,
    ))
    action = "suggested" if args.suggest else "set"
    print(f"Photo {action} for {args.target}")

async def cmd_collectible_emoji(client, args):
    """List collectible emoji statuses."""
    from telethon import functions
    result = await client(functions.account.GetCollectibleEmojiStatusesRequest(hash=0))
    statuses = getattr(result, 'statuses', [])
    print(f"Collectible emoji statuses: {len(statuses)}")
    for s in statuses:
        doc_id = getattr(s, 'document_id', '?')
        print(f"  Emoji document ID: {doc_id}")

async def cmd_notify_settings(client, args):
    """View notification settings for a chat."""
    from telethon import functions, types
    if args.target == 'users':
        peer = types.InputNotifyUsers()
    elif args.target == 'groups':
        peer = types.InputNotifyChats()
    elif args.target == 'channels':
        peer = types.InputNotifyBroadcasts()
    else:
        entity = await client.get_entity(args.target)
        peer = types.InputNotifyPeer(peer=entity)
    result = await client(functions.account.GetNotifySettingsRequest(peer=peer))
    mute = getattr(result, 'mute_until', '?')
    preview = getattr(result, 'show_previews', '?')
    print(f"Notifications for {args.target}:")
    print(f"  Muted until: {mute}")
    print(f"  Preview: {preview}")

async def cmd_auto_save(client, args):
    """View auto-save settings."""
    from telethon import functions
    result = await client(functions.account.GetAutoSaveSettingsRequest())
    print(f"Auto-save settings:")
    users = getattr(result, 'users_settings', None)
    chats = getattr(result, 'chats_settings', None)
    broadcasts = getattr(result, 'broadcasts_settings', None)
    if users: print(f"  Users: photos={getattr(users, 'photos', '?')}, videos={getattr(users, 'videos', '?')}")
    if chats: print(f"  Groups: photos={getattr(chats, 'photos', '?')}, videos={getattr(chats, 'videos', '?')}")
    if broadcasts: print(f"  Channels: photos={getattr(broadcasts, 'photos', '?')}, videos={getattr(broadcasts, 'videos', '?')}")

async def cmd_live_story(client, args):
    """Start a live story stream."""
    from telethon import functions
    peer = await client.get_entity(args.channel) if args.channel else await client.get_me()
    try:
        result = await client(functions.stories.StartLiveRequest(peer=peer))
        print(f"Live story started!")
    except Exception as e:
        print(f"Live story error: {e}")


# --- Bot Management (batch 5) ---
async def cmd_bot_info(client, args):
    """Get info about a bot."""
    from telethon import functions
    bot = await client.get_entity(args.bot)
    result = await client(functions.bots.GetBotInfoRequest(
        bot=bot, lang_code=args.lang or 'en'
    ))
    desc = getattr(result, 'description', '?')
    about = getattr(result, 'about', '?')
    print(f"Bot: {args.bot}")
    print(f"  Description: {desc}")
    print(f"  About: {about}")
    cmds = getattr(result, 'commands', [])
    if cmds:
        print(f"  Commands ({len(cmds)}):")
        for c in cmds:
            print(f"    /{getattr(c, 'command', '?')} — {getattr(c, 'description', '')}")

async def cmd_bot_commands(client, args):
    """Get commands of a bot."""
    from telethon import functions, types
    result = await client(functions.bots.GetBotCommandsRequest(
        scope=types.BotCommandScopeDefault(),
        lang_code=args.lang or ''
    ))
    print(f"Bot commands: {len(result)}")
    for c in result:
        print(f"  /{getattr(c, 'command', '?')} — {getattr(c, 'description', '')}")

async def cmd_admined_bots(client, args):
    """List bots you administer."""
    from telethon import functions
    result = await client(functions.bots.GetAdminedBotsRequest())
    bots = getattr(result, 'bots', result) if not isinstance(result, list) else result
    print(f"Your bots:")
    if isinstance(bots, list):
        for b in bots:
            name = getattr(b, 'first_name', '?')
            uname = getattr(b, 'username', '?')
            print(f"  {name} @{uname} (ID: {getattr(b, 'id', '?')})")
    else:
        print(f"  {bots}")

async def cmd_popular_bots(client, args):
    """List popular app bots."""
    from telethon import functions
    result = await client(functions.bots.GetPopularAppBotsRequest(
        offset='', limit=args.limit or 20
    ))
    bots = getattr(result, 'users', [])
    print(f"Popular bots: {len(bots)}")
    for b in bots:
        name = getattr(b, 'first_name', '?')
        uname = getattr(b, 'username', '?')
        print(f"  {name} @{uname}")

async def cmd_bot_recommendations(client, args):
    """Get bot recommendations."""
    from telethon import functions
    bot = await client.get_entity(args.bot)
    result = await client(functions.bots.GetBotRecommendationsRequest(bot=bot))
    users = getattr(result, 'users', [])
    print(f"Recommended bots (similar to {args.bot}):")
    for u in users:
        name = getattr(u, 'first_name', '?')
        uname = getattr(u, 'username', '?')
        print(f"  {name} @{uname}")

async def cmd_shared_folders(client, args):
    """List shared chat folders (chatlists)."""
    from telethon import functions
    result = await client(functions.messages.GetDialogFiltersRequest())
    filters = getattr(result, 'filters', result) if not isinstance(result, list) else result
    print(f"Chat folders:")
    if isinstance(filters, list):
        for f in filters:
            title = getattr(f, 'title', '?')
            fid = getattr(f, 'id', '?')
            print(f"  [{fid}] {title}")

async def cmd_top_peers(client, args):
    """Get top peers (most contacted)."""
    from telethon import functions
    result = await client(functions.contacts.GetTopPeersRequest(
        correspondents=True, bots_pm=True, bots_inline=True,
        phone_calls=False, forward_users=True, forward_chats=True, groups=True, channels=True,
        offset=0, limit=args.limit or 20, hash=0
    ))
    categories = getattr(result, 'categories', [])
    print(f"Top peers ({len(categories)} categories):")
    for cat in categories:
        ctype = type(getattr(cat, 'category', cat)).__name__
        peers = getattr(cat, 'peers', [])
        print(f"\n  {ctype} ({len(peers)}):")
        for p in peers[:5]:
            peer = getattr(p, 'peer', p)
            rating = getattr(p, 'rating', 0)
            print(f"    {peer} (rating: {rating:.2f})")

async def cmd_search_global(client, args):
    """Search messages globally across all chats."""
    from telethon import functions, types
    result = await client(functions.messages.SearchGlobalRequest(
        q=args.query, filter=types.InputMessagesFilterEmpty(),
        min_date=None, max_date=None,
        offset_rate=0, offset_peer=types.InputPeerEmpty(),
        offset_id=0, limit=args.limit or 20,
    ))
    messages = getattr(result, 'messages', [])
    print(f"Global search '{args.query}': {len(messages)} results")
    for m in messages:
        peer = getattr(m, 'peer_id', '?')
        text = getattr(m, 'message', '') or ''
        date = getattr(m, 'date', '')
        print(f"  [{date}] {peer}: {text[:80]}")


async def cmd_get_replies(client, args):
    """Get replies/thread for a message."""
    from telethon import functions
    peer = await client.get_entity(args.chat)
    result = await client(functions.messages.GetRepliesRequest(
        peer=peer, msg_id=args.msg_id,
        offset_id=0, offset_date=None, add_offset=0,
        limit=args.limit or 50, max_id=0, min_id=0, hash=0
    ))
    messages = getattr(result, 'messages', [])
    print(f"Replies to #{args.msg_id}: {len(messages)}")
    for m in messages:
        sender = getattr(m, 'from_id', '?')
        text = getattr(m, 'message', '') or ''
        date = fmt_date(getattr(m, 'date', None))
        print(f"  [{date}] {sender}: {text[:80]}")


async def cmd_export_folder_invite(client, args):
    """Export invite link for a chat folder."""
    from telethon import functions, types
    result = await client(functions.chatlists.ExportChatlistInviteRequest(
        chatlist=types.InputChatlistDialogFilter(filter_id=args.folder_id),
        title=args.title or 'Shared Folder',
        peers=[]
    ))
    link = getattr(result, 'invite', result)
    url = getattr(link, 'url', link)
    print(f"Folder invite: {url}")


async def cmd_join_folder(client, args):
    """Join a shared folder by invite link."""
    from telethon import functions, types
    slug = args.slug.split('/')[-1] if '/' in args.slug else args.slug
    result = await client(functions.chatlists.CheckChatlistInviteRequest(slug=slug))
    peers = getattr(result, 'already_peers', []) + getattr(result, 'missing_peers', [])
    peer_inputs = []
    for p in peers:
        try:
            entity = await client.get_entity(p)
            peer_inputs.append(await client.get_input_entity(entity))
        except Exception:
            pass
    if peer_inputs:
        await client(functions.chatlists.JoinChatlistInviteRequest(slug=slug, peers=peer_inputs))
        print(f"Joined folder with {len(peer_inputs)} chats")
    else:
        print("No chats to join")


async def cmd_check_username(client, args):
    """Check if a username is available."""
    from telethon import functions
    result = await client(functions.account.CheckUsernameRequest(username=args.username))
    print(f"@{args.username}: {'AVAILABLE' if result else 'TAKEN'}")


async def cmd_update_status(client, args):
    """Set online/offline status."""
    from telethon import functions
    await client(functions.account.UpdateStatusRequest(offline=args.offline))
    print(f"Status: {'offline' if args.offline else 'online'}")


async def cmd_password_status(client, args):
    """Check 2FA password status."""
    from telethon import functions
    result = await client(functions.account.GetPasswordRequest())
    has_pwd = getattr(result, 'has_password', False)
    hint = getattr(result, 'hint', '') or ''
    email = getattr(result, 'email_unconfirmed_pattern', '') or ''
    print(f"2FA: {'enabled' if has_pwd else 'disabled'}")
    if hint: print(f"  Hint: {hint}")
    if email: print(f"  Recovery email: {email}")


async def cmd_delete_messages(client, args):
    """Delete messages by IDs (bulk)."""
    peer = await client.get_entity(args.chat)
    ids = [int(x) for x in args.ids.split(',')]
    result = await client.delete_messages(peer, ids, revoke=not args.me_only)
    count = getattr(result, 'pts_count', len(ids))
    print(f"Deleted {count} messages")


async def cmd_clear_history(client, args):
    """Clear entire chat history."""
    from telethon import functions
    peer = await client.get_entity(args.chat)
    await client(functions.messages.DeleteHistoryRequest(
        peer=peer, max_id=0, just_clear=True, revoke=not args.me_only,
    ))
    print(f"Chat history cleared: {args.chat}")


async def cmd_read_history(client, args):
    """Mark entire chat as read."""
    from telethon import functions
    peer = await client.get_entity(args.chat)
    await client(functions.messages.ReadHistoryRequest(peer=peer, max_id=0))
    print(f"Chat marked as read: {args.chat}")


async def cmd_send_typing(client, args):
    """Send typing indicator to a chat."""
    from telethon import functions, types
    peer = await client.get_entity(args.chat)
    actions = {
        'typing': types.SendMessageTypingAction(),
        'upload_photo': types.SendMessageUploadPhotoAction(progress=0),
        'record_video': types.SendMessageRecordVideoAction(),
        'record_audio': types.SendMessageRecordAudioAction(),
        'choose_sticker': types.SendMessageChooseStickerAction(),
        'cancel': types.SendMessageCancelAction(),
    }
    action = actions.get(args.action, types.SendMessageTypingAction())
    await client(functions.messages.SetTypingRequest(peer=peer, action=action))
    print(f"Typing '{args.action}' sent to {args.chat}")


async def cmd_export_contact_token(client, args):
    """Export your contact token for sharing."""
    from telethon import functions
    result = await client(functions.contacts.ExportContactTokenRequest())
    token = getattr(result, 'url', result)
    print(f"Contact token: {token}")


async def cmd_import_contact_token(client, args):
    """Import a contact by token."""
    from telethon import functions
    result = await client(functions.contacts.ImportContactTokenRequest(token=args.token))
    if hasattr(result, 'first_name'):
        print(f"Imported: {result.first_name} {getattr(result, 'last_name', '')} @{getattr(result, 'username', '?')}")
    else:
        print(f"Imported: {result}")


async def cmd_create_sticker_set(client, args):
    """Create a new sticker set via API (not @Stickers bot)."""
    from telethon import functions, types
    user = await client.get_me()
    file = await client.upload_file(args.file)
    sticker = types.InputStickerSetItem(
        document=types.InputMediaUploadedDocument(
            file=file, mime_type='image/webp' if args.file.endswith('.webp') else 'video/webm',
            attributes=[types.DocumentAttributeFilename(file_name=args.file.split('/')[-1].split('\\')[-1])]
        ),
        emoji=args.emoji or '\U0001f600',
    )
    result = await client(functions.stickers.CreateStickerSetRequest(
        user_id=user, title=args.title, short_name=args.short_name,
        stickers=[sticker],
        emojis=args.emoji_type or False,
    ))
    print(f"Sticker set created: t.me/addstickers/{args.short_name}")


async def cmd_change_phone(client, args):
    """Change phone number on account (sends code to new phone)."""
    from telethon import functions, types
    result = await client(functions.account.SendChangePhoneCodeRequest(
        phone_number=args.phone,
        settings=types.CodeSettings(allow_flashcall=False, current_number=False, allow_app_hash=False)
    ))
    phone_hash = result.phone_code_hash
    print(f"Code sent to {args.phone}. Enter the code:")
    code = input("Code: ").strip()
    await client(functions.account.ChangePhoneRequest(
        phone_number=args.phone, phone_code_hash=phone_hash, phone_code=code
    ))
    print(f"Phone changed to {args.phone}!")


async def cmd_takeout(client, args):
    """Start GDPR data takeout/export."""
    from telethon import functions
    result = await client(functions.account.InitTakeoutSessionRequest(
        contacts=args.contacts or False,
        message_users=args.users or False,
        message_chats=args.chats or False,
        message_megagroups=args.groups or False,
        message_channels=args.channels or False,
        files=args.files or False,
        file_max_size=args.max_size or 524288000,
    ))
    takeout_id = getattr(result, 'id', '?')
    print(f"Takeout session started! ID: {takeout_id}")
    print("Use Telegram Desktop to complete the export.")


async def cmd_mark_unread(client, args):
    """Mark a chat as unread."""
    from telethon import functions, types
    peer = await client.get_entity(args.chat)
    await client(functions.messages.MarkDialogUnreadRequest(
        peer=types.InputDialogPeer(peer=peer), unread=True
    ))
    print(f"Marked as unread: {args.chat}")


async def cmd_scheduled_messages(client, args):
    """View scheduled messages in a chat."""
    from telethon import functions
    peer = await client.get_entity(args.chat)
    result = await client(functions.messages.GetScheduledHistoryRequest(
        peer=peer, hash=0
    ))
    messages = getattr(result, 'messages', [])
    print(f"Scheduled messages in {args.chat}: {len(messages)}")
    for m in messages:
        date = getattr(m, 'date', '')
        text = getattr(m, 'message', '') or ''
        mid = getattr(m, 'id', '?')
        print(f"  #{mid} | {date} | {text[:60]}")


async def cmd_delete_scheduled(client, args):
    """Delete a scheduled message."""
    from telethon import functions
    peer = await client.get_entity(args.chat)
    ids = [int(x) for x in args.ids.split(',')]
    await client(functions.messages.DeleteScheduledMessagesRequest(
        peer=peer, id=ids
    ))
    print(f"Deleted {len(ids)} scheduled messages")


async def cmd_report_spam(client, args):
    """Report a chat as spam."""
    from telethon import functions
    peer = await client.get_entity(args.chat)
    await client(functions.messages.ReportSpamRequest(peer=peer))
    print(f"Reported as spam: {args.chat}")


async def cmd_toggle_join_request(client, args):
    """Toggle join request approval for channel/group."""
    from telethon import functions
    peer = await client.get_entity(args.channel)
    await client(functions.channels.ToggleJoinRequestRequest(
        channel=peer, enabled=not args.disable
    ))
    print(f"Join requests {'disabled' if args.disable else 'enabled'} for {args.channel}")


async def cmd_set_discussion(client, args):
    """Link a discussion group to a channel."""
    from telethon import functions
    channel = await client.get_entity(args.channel)
    if args.clear:
        from telethon.tl.types import InputChannelEmpty
        await client(functions.channels.SetDiscussionGroupRequest(
            broadcast=channel, group=InputChannelEmpty()
        ))
        print(f"Discussion group removed from {args.channel}")
    else:
        group = await client.get_entity(args.group)
        await client(functions.channels.SetDiscussionGroupRequest(
            broadcast=channel, group=group
        ))
        print(f"Discussion group set: {args.group} -> {args.channel}")


async def cmd_get_scheduled_history(client, args):
    """Alias: see scheduled-messages."""
    await cmd_scheduled_messages(client, args)


async def cmd_toggle_slow_mode(client, args):
    """Set slow mode delay for a group."""
    from telethon import functions
    peer = await client.get_entity(args.chat)
    await client(functions.channels.ToggleSlowModeRequest(
        channel=peer, seconds=args.seconds
    ))
    if args.seconds == 0:
        print(f"Slow mode disabled for {args.chat}")
    else:
        print(f"Slow mode set to {args.seconds}s for {args.chat}")


async def cmd_set_chat_photo(client, args):
    """Set group/channel photo."""
    from telethon import functions, types
    peer = await client.get_entity(args.chat)
    file = await client.upload_file(args.file)
    await client(functions.channels.EditPhotoRequest(
        channel=peer, photo=types.InputChatUploadedPhoto(file=file)
    ))
    print(f"Chat photo updated: {args.chat}")


async def cmd_get_invite_link(client, args):
    """Get/create invite link for a chat."""
    from telethon import functions
    peer = await client.get_entity(args.chat)
    result = await client(functions.messages.ExportChatInviteRequest(
        peer=peer, legacy_revoke_permanent=False,
        title=args.title or None,
        expire_date=None, usage_limit=args.limit or None,
    ))
    link = getattr(result, 'link', result)
    print(f"Invite link: {link}")


async def cmd_vote(client, args):
    """Vote in a poll."""
    from telethon import functions
    peer = await client.get_entity(args.chat)
    options = [bytes([int(x)]) for x in args.options.split(',')]
    await client(functions.messages.SendVoteRequest(peer=peer, msg_id=args.msg_id, options=options))
    print(f"Voted in poll #{args.msg_id}")


async def cmd_msg_readers(client, args):
    """See who read a message (small groups only)."""
    from telethon import functions
    peer = await client.get_entity(args.chat)
    result = await client(functions.messages.GetMessageReadParticipantsRequest(peer=peer, msg_id=args.msg_id))
    readers = list(result)
    print(f"Message #{args.msg_id} read by {len(readers)} users")
    for r in readers:
        uid = getattr(r, 'user_id', r)
        date = getattr(r, 'date', '')
        print(f"  User {uid} | {date}")


async def cmd_msg_views(client, args):
    """Get view count for channel messages."""
    from telethon import functions
    peer = await client.get_entity(args.chat)
    ids = [int(x) for x in args.ids.split(',')]
    result = await client(functions.messages.GetMessagesViewsRequest(peer=peer, id=ids, increment=False))
    views = getattr(result, 'views', [])
    for v in views:
        count = getattr(v, 'views', 0)
        forwards = getattr(v, 'forwards', 0)
        replies = getattr(getattr(v, 'replies', None), 'replies', 0) if getattr(v, 'replies', None) else 0
        print(f"  Views: {count} | Forwards: {forwards} | Replies: {replies}")


async def cmd_unread_mentions(client, args):
    """Get unread mentions in a chat."""
    from telethon import functions
    peer = await client.get_entity(args.chat)
    result = await client(functions.messages.GetUnreadMentionsRequest(
        peer=peer, offset_id=0, add_offset=0, limit=args.limit or 20, max_id=0, min_id=0
    ))
    messages = getattr(result, 'messages', [])
    print(f"Unread mentions: {len(messages)}")
    for m in messages:
        text = getattr(m, 'message', '') or ''
        date = fmt_date(getattr(m, 'date', None))
        print(f"  [{date}] #{m.id}: {text[:80]}")


async def cmd_read_mentions(client, args):
    """Mark all mentions as read."""
    from telethon import functions
    peer = await client.get_entity(args.chat)
    await client(functions.messages.ReadMentionsRequest(peer=peer))
    print(f"Mentions marked as read: {args.chat}")


async def cmd_unread_reactions(client, args):
    """Get unread reactions in a chat."""
    from telethon import functions
    peer = await client.get_entity(args.chat)
    result = await client(functions.messages.GetUnreadReactionsRequest(
        peer=peer, offset_id=0, add_offset=0, limit=args.limit or 20, max_id=0, min_id=0
    ))
    messages = getattr(result, 'messages', [])
    print(f"Unread reactions: {len(messages)}")
    for m in messages:
        text = getattr(m, 'message', '') or ''
        print(f"  #{m.id}: {text[:60]}")


async def cmd_read_reactions(client, args):
    """Mark all reactions as read."""
    from telethon import functions
    peer = await client.get_entity(args.chat)
    await client(functions.messages.ReadReactionsRequest(peer=peer))
    print(f"Reactions marked as read: {args.chat}")


async def cmd_edit_admin(client, args):
    """Set/remove admin rights for a user in channel/group."""
    from telethon import functions, types
    channel = await client.get_entity(args.channel)
    user = await client.get_entity(args.user)
    if args.remove:
        rights = types.ChatAdminRights()
    else:
        rights = types.ChatAdminRights(
            change_info=True, post_messages=args.can_post or False,
            edit_messages=args.can_edit or False, delete_messages=True,
            ban_users=True, invite_users=True, pin_messages=True,
            manage_call=True, other=True, manage_topics=True,
        )
    await client(functions.channels.EditAdminRequest(
        channel=channel, user_id=user, admin_rights=rights, rank=args.rank or ''
    ))
    action = "removed admin from" if args.remove else "promoted"
    print(f"{action} {args.user} in {args.channel}")


async def cmd_edit_channel_title(client, args):
    """Change channel/group title."""
    from telethon import functions
    channel = await client.get_entity(args.channel)
    await client(functions.channels.EditTitleRequest(channel=channel, title=args.title))
    print(f"Title changed to: {args.title}")


async def cmd_edit_channel_about(client, args):
    """Change channel/group description."""
    from telethon import functions
    channel = await client.get_entity(args.channel)
    await client(functions.messages.EditChatAboutRequest(peer=channel, about=args.about))
    print(f"Description updated for {args.channel}")


async def cmd_get_sticker_set(client, args):
    """Get sticker set info by short name."""
    from telethon import functions, types
    result = await client(functions.messages.GetStickerSetRequest(
        stickerset=types.InputStickerSetShortName(short_name=args.short_name), hash=0
    ))
    sset = getattr(result, 'set', None)
    docs = getattr(result, 'documents', [])
    if sset:
        print(f"Pack: {getattr(sset, 'title', '?')} (@{getattr(sset, 'short_name', '?')})")
        print(f"  Stickers: {len(docs)} | Animated: {getattr(sset, 'animated', False)} | Video: {getattr(sset, 'videos', False)}")


async def cmd_add_sticker(client, args):
    """Add a sticker to an existing set."""
    from telethon import functions, types
    file = await client.upload_file(args.file)
    uploaded = await client(functions.messages.UploadMediaRequest(
        peer='me', media=types.InputMediaUploadedDocument(
            file=file, mime_type='image/webp' if args.file.endswith('.webp') else 'video/webm',
            attributes=[types.DocumentAttributeFilename(file_name=args.file.split('/')[-1].split('\\')[-1])]
        )
    ))
    doc = uploaded.document
    await client(functions.stickers.AddStickerToSetRequest(
        stickerset=types.InputStickerSetShortName(short_name=args.short_name),
        sticker=types.InputStickerSetItem(
            document=types.InputDocument(id=doc.id, access_hash=doc.access_hash, file_reference=doc.file_reference),
            emoji=args.emoji or '\U0001f600'
        )
    ))
    print(f"Sticker added to @{args.short_name}")


async def cmd_remove_sticker(client, args):
    """Remove a sticker from a set."""
    from telethon import functions, types
    result = await client(functions.messages.GetStickerSetRequest(
        stickerset=types.InputStickerSetShortName(short_name=args.short_name), hash=0
    ))
    docs = getattr(result, 'documents', [])
    if args.index < 0 or args.index >= len(docs):
        print(f"Invalid index {args.index}. Pack has {len(docs)} stickers (0-{len(docs)-1})")
        return
    doc = docs[args.index]
    await client(functions.stickers.RemoveStickerFromSetRequest(
        sticker=types.InputDocument(id=doc.id, access_hash=doc.access_hash, file_reference=doc.file_reference)
    ))
    print(f"Sticker #{args.index} removed from @{args.short_name}")


async def cmd_fave_sticker(client, args):
    """Add/remove sticker from favorites."""
    from telethon import functions, types
    result = await client(functions.messages.GetStickerSetRequest(
        stickerset=types.InputStickerSetShortName(short_name=args.short_name), hash=0
    ))
    docs = getattr(result, 'documents', [])
    if args.index >= len(docs):
        print(f"Invalid index. Pack has {len(docs)} stickers")
        return
    doc = docs[args.index]
    await client(functions.messages.FaveStickerRequest(
        id=types.InputDocument(id=doc.id, access_hash=doc.access_hash, file_reference=doc.file_reference),
        unfave=args.unfave or False
    ))
    print(f"Sticker {'unfaved' if args.unfave else 'faved'}")


async def cmd_save_gif(client, args):
    """Save a GIF from a message."""
    from telethon import functions, types
    peer = await client.get_entity(args.chat)
    msgs = await client.get_messages(peer, ids=[args.msg_id])
    if not msgs or not msgs[0] or not msgs[0].media:
        print("Message has no media")
        return
    doc = msgs[0].media.document
    if doc:
        await client(functions.messages.SaveGifRequest(
            id=types.InputDocument(id=doc.id, access_hash=doc.access_hash, file_reference=doc.file_reference),
            unsave=args.unsave or False
        ))
        print(f"GIF {'unsaved' if args.unsave else 'saved'}")


async def cmd_kill_session(client, args):
    """Terminate a specific session by hash."""
    from telethon import functions
    await client(functions.account.ResetAuthorizationRequest(hash=int(args.session_hash)))
    print(f"Session terminated")


async def cmd_kill_web_session(client, args):
    """Terminate a specific web session."""
    from telethon import functions
    await client(functions.account.ResetWebAuthorizationRequest(hash=int(args.session_hash)))
    print(f"Web session terminated")


async def cmd_import_contacts(client, args):
    """Import contacts from a CSV file (phone,first_name,last_name)."""
    from telethon import functions, types
    import csv
    contacts = []
    with open(args.file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 2:
                contacts.append(types.InputPhoneContact(
                    client_id=len(contacts),
                    phone=row[0].strip(),
                    first_name=row[1].strip(),
                    last_name=row[2].strip() if len(row) > 2 else ''
                ))
    result = await client(functions.contacts.ImportContactsRequest(contacts=contacts))
    imported = getattr(result, 'imported', [])
    print(f"Imported {len(imported)} of {len(contacts)} contacts")


async def cmd_contact_statuses(client, args):
    """Get online statuses of all contacts."""
    from telethon import functions
    result = await client(functions.contacts.GetStatusesRequest())
    for s in result:
        uid = getattr(s, 'user_id', '?')
        status = getattr(s, 'status', None)
        status_str = type(status).__name__ if status else 'unknown'
        print(f"  User {uid}: {status_str}")


async def cmd_user_photos(client, args):
    """Get all profile photos of a user."""
    from telethon import functions
    user = await client.get_entity(args.target)
    result = await client(functions.photos.GetUserPhotosRequest(
        user_id=user, offset=0, max_id=0, limit=args.limit or 20
    ))
    photos = getattr(result, 'photos', [])
    print(f"Photos of {args.target}: {len(photos)}")
    for i, p in enumerate(photos):
        pid = getattr(p, 'id', '?')
        date = getattr(p, 'date', '')
        print(f"  [{i}] ID:{pid} | {date}")


async def cmd_pinned_stories(client, args):
    """Get pinned stories."""
    from telethon import functions
    peer = await client.get_entity(args.target) if args.target else await client.get_me()
    result = await client(functions.stories.GetPinnedStoriesRequest(
        peer=peer, offset_id=0, limit=args.limit or 20
    ))
    stories_list = getattr(result, 'stories', [])
    print(f"Pinned stories: {len(stories_list)}")
    for s in stories_list:
        sid = getattr(s, 'id', '?')
        caption = getattr(s, 'caption', '') or ''
        print(f"  #{sid}: {caption[:60]}")


async def cmd_check_gift_code(client, args):
    """Check a gift code."""
    from telethon import functions
    result = await client(functions.payments.CheckGiftCodeRequest(slug=args.code))
    months = getattr(result, 'months', '?')
    used = getattr(result, 'used_date', None)
    print(f"Gift code: {months} months Premium")
    if used:
        print(f"  Already used: {used}")
    else:
        print(f"  Available to redeem!")


async def cmd_apply_gift_code(client, args):
    """Apply/redeem a gift code."""
    from telethon import functions
    await client(functions.payments.ApplyGiftCodeRequest(slug=args.code))
    print(f"Gift code applied!")


async def cmd_toggle_antispam(client, args):
    """Toggle anti-spam in a group."""
    from telethon import functions
    channel = await client.get_entity(args.channel)
    await client(functions.channels.ToggleAntiSpamRequest(
        channel=channel, enabled=not args.disable
    ))
    print(f"Anti-spam {'disabled' if args.disable else 'enabled'} for {args.channel}")


async def cmd_leave_folder(client, args):
    """Leave a shared chat folder."""
    from telethon import functions, types
    await client(functions.chatlists.LeaveChatlistRequest(
        chatlist=types.InputChatlistDialogFilter(filter_id=args.folder_id),
        peers=[]
    ))
    print(f"Left shared folder #{args.folder_id}")


# --- Forum topics ---

async def cmd_get_forum_topics(client, args):
    """List forum topics in a group."""
    from telethon import functions
    peer = await client.get_entity(args.channel)
    result = await client(functions.channels.GetForumTopicsRequest(
        channel=peer, offset_date=None, offset_id=0, offset_topic=0,
        limit=args.limit or 50, q=args.query or ''
    ))
    topics = getattr(result, 'topics', [])
    print(f"Forum topics: {len(topics)}")
    for t in topics:
        tid = getattr(t, 'id', '?')
        title = getattr(t, 'title', '?')
        closed = ' [CLOSED]' if getattr(t, 'closed', False) else ''
        pinned = ' [PINNED]' if getattr(t, 'pinned', False) else ''
        print(f"  #{tid}: {title}{closed}{pinned}")


async def cmd_edit_forum_topic(client, args):
    """Edit a forum topic title/icon."""
    from telethon import functions
    peer = await client.get_entity(args.channel)
    await client(functions.channels.EditForumTopicRequest(
        channel=peer, topic_id=args.topic_id,
        title=args.title or None,
        icon_emoji_id=int(args.icon) if args.icon else None,
    ))
    print(f"Topic #{args.topic_id} updated")


async def cmd_close_forum_topic(client, args):
    """Close/reopen a forum topic."""
    from telethon import functions
    peer = await client.get_entity(args.channel)
    await client(functions.channels.EditForumTopicRequest(
        channel=peer, topic_id=args.topic_id, closed=not args.reopen
    ))
    print(f"Topic #{args.topic_id} {'reopened' if args.reopen else 'closed'}")


async def cmd_delete_topic(client, args):
    """Delete a forum topic and all its messages."""
    from telethon import functions
    peer = await client.get_entity(args.channel)
    await client(functions.channels.DeleteTopicHistoryRequest(
        channel=peer, top_msg_id=args.topic_id
    ))
    print(f"Topic #{args.topic_id} deleted")


# --- Messages (album, stories, gifs) ---

async def cmd_send_album(client, args):
    """Send multiple photos/videos as an album."""
    from telethon.tl.types import InputMediaUploadedPhoto, InputMediaUploadedDocument, DocumentAttributeVideo
    import os
    peer = await client.get_entity(args.chat)
    files = args.files
    media_list = []
    for f in files:
        uploaded = await client.upload_file(f)
        ext = os.path.splitext(f)[1].lower()
        if ext in ('.mp4', '.mov', '.avi', '.mkv'):
            media_list.append(InputMediaUploadedDocument(
                file=uploaded, mime_type='video/mp4',
                attributes=[DocumentAttributeVideo(duration=0, w=0, h=0, supports_streaming=True)]
            ))
        else:
            media_list.append(InputMediaUploadedPhoto(file=uploaded))
    result = await client.send_file(peer, media_list, caption=args.caption or '')
    print(f"Album sent: {len(files)} files to {args.chat}")


async def cmd_delete_story(client, args):
    """Delete stories by IDs."""
    from telethon import functions
    peer = await client.get_entity(args.target) if args.target else await client.get_me()
    ids = [int(x) for x in args.ids.split(',')]
    result = await client(functions.stories.DeleteStoriesRequest(peer=peer, id=ids))
    print(f"Deleted {len(ids)} stories")


async def cmd_get_saved_gifs(client, args):
    """List saved GIFs."""
    from telethon import functions
    result = await client(functions.messages.GetSavedGifsRequest(hash=0))
    gifs = getattr(result, 'gifs', [])
    print(f"Saved GIFs: {len(gifs)}")
    for i, g in enumerate(gifs[:args.limit or 20]):
        size = getattr(g, 'size', '?')
        print(f"  [{i}] ID:{g.id} | {size} bytes")


# --- Account ---

async def cmd_set_2fa(client, args):
    """Set or change 2FA password."""
    pwd = args.password
    hint = args.hint or ''
    try:
        await client.edit_2fa(current_password=args.current or None, new_password=pwd, hint=hint)
        print(f"2FA password set (hint: '{hint}')")
    except Exception as e:
        print(f"2FA error: {e}")


async def cmd_remove_2fa(client, args):
    """Remove 2FA password."""
    try:
        await client.edit_2fa(current_password=args.current, new_password=None)
        print("2FA password removed")
    except Exception as e:
        print(f"2FA error: {e}")


async def cmd_set_username(client, args):
    """Set or change your username."""
    from telethon import functions
    await client(functions.account.UpdateUsernameRequest(username=args.username))
    print(f"Username set to @{args.username}")


# --- Channels (send-as, join-to-send, history, left) ---

async def cmd_get_send_as(client, args):
    """Get available 'send as' identities for a channel."""
    from telethon import functions
    peer = await client.get_entity(args.channel)
    result = await client(functions.channels.GetSendAsRequest(peer=peer))
    peers = getattr(result, 'peers', [])
    print(f"Send-as options for {args.channel}:")
    for p in peers:
        peer_obj = getattr(p, 'peer', p)
        print(f"  {peer_obj}")


async def cmd_toggle_join_to_send(client, args):
    """Toggle whether users must join to send messages."""
    from telethon import functions
    channel = await client.get_entity(args.channel)
    await client(functions.channels.ToggleJoinToSendRequest(
        channel=channel, enabled=not args.disable
    ))
    print(f"Join-to-send {'disabled' if args.disable else 'enabled'}")


async def cmd_toggle_history_hidden(client, args):
    """Toggle whether chat history is hidden for new members."""
    from telethon import functions
    channel = await client.get_entity(args.channel)
    await client(functions.channels.TogglePreHistoryHiddenRequest(
        channel=channel, enabled=not args.show
    ))
    print(f"History {'visible' if args.show else 'hidden'} for new members")


async def cmd_get_left_channels(client, args):
    """List channels you have left."""
    from telethon import functions
    result = await client(functions.channels.GetLeftChannelsRequest(offset=0))
    chats = getattr(result, 'chats', [])
    print(f"Left channels: {len(chats)}")
    for c in chats:
        title = getattr(c, 'title', '?')
        uname = getattr(c, 'username', '') or ''
        print(f"  {title}" + (f" @{uname}" if uname else ""))


# --- Stickers (move, thumb) ---

async def cmd_move_sticker(client, args):
    """Move sticker position within a set."""
    from telethon import functions, types
    result = await client(functions.messages.GetStickerSetRequest(
        stickerset=types.InputStickerSetShortName(short_name=args.short_name), hash=0
    ))
    docs = getattr(result, 'documents', [])
    if args.index >= len(docs):
        print(f"Invalid index. Pack has {len(docs)} stickers")
        return
    doc = docs[args.index]
    await client(functions.stickers.ChangeStickerPositionRequest(
        sticker=types.InputDocument(id=doc.id, access_hash=doc.access_hash, file_reference=doc.file_reference),
        position=args.position
    ))
    print(f"Sticker #{args.index} moved to position {args.position}")


async def cmd_set_sticker_thumb(client, args):
    """Set sticker set thumbnail."""
    from telethon import functions, types
    file = await client.upload_file(args.file)
    uploaded = await client(functions.messages.UploadMediaRequest(
        peer='me', media=types.InputMediaUploadedDocument(
            file=file, mime_type='image/webp',
            attributes=[types.DocumentAttributeFilename(file_name='thumb.webp')]
        )
    ))
    doc = uploaded.document
    await client(functions.stickers.SetStickerSetThumbRequest(
        stickerset=types.InputStickerSetShortName(short_name=args.short_name),
        thumb=types.InputDocument(id=doc.id, access_hash=doc.access_hash, file_reference=doc.file_reference),
    ))
    print(f"Thumbnail set for @{args.short_name}")


# --- Gifts (transfer, upgrade) ---

async def cmd_transfer_gift(client, args):
    """Transfer a star gift to another user."""
    from telethon import functions, types
    target = await client.get_entity(args.target)
    await client(functions.payments.TransferStarGiftRequest(
        stargift=types.InputSavedStarGiftUser(msg_id=args.msg_id),
        to_id=target,
    ))
    print(f"Gift transferred to {args.target}")


async def cmd_upgrade_gift(client, args):
    """Upgrade a star gift."""
    from telethon import functions, types
    await client(functions.payments.UpgradeStarGiftRequest(
        stargift=types.InputSavedStarGiftUser(msg_id=args.msg_id),
        keep_original_details=args.keep or False,
    ))
    print(f"Gift upgraded!")


async def cmd_set_chat_theme(client, args):
    """Set theme for a specific chat."""
    from telethon import functions
    peer = await client.get_entity(args.chat)
    emoticon = args.theme if args.theme else ''
    await client(functions.messages.SetChatThemeRequest(peer=peer, emoticon=emoticon))
    print(f"Chat theme {'cleared' if not emoticon else 'set to ' + emoticon} for {args.chat}")

async def cmd_send_paid_media(client, args):
    """Send paid media (stars required to view)."""
    from telethon import functions, types
    peer = await client.get_entity(args.chat)
    file = await client.upload_file(args.file)
    import os
    ext = os.path.splitext(args.file)[1].lower()
    if ext in ('.mp4', '.mov', '.avi'):
        media = types.InputMediaUploadedDocument(
            file=file, mime_type='video/mp4',
            attributes=[types.DocumentAttributeVideo(duration=0, w=0, h=0, supports_streaming=True)]
        )
    else:
        media = types.InputMediaUploadedPhoto(file=file)
    paid = types.InputMediaPaidMedia(stars_amount=args.stars, extended_media=[media])
    await client.send_file(peer, paid, caption=args.caption or '')
    print(f"Paid media sent ({args.stars} stars) to {args.chat}")

async def cmd_report_message(client, args):
    """Report specific messages in a chat."""
    from telethon import functions, types
    peer = await client.get_entity(args.chat)
    ids = [int(x) for x in args.ids.split(',')]
    reasons = {
        'spam': types.InputReportReasonSpam(),
        'violence': types.InputReportReasonViolence(),
        'porn': types.InputReportReasonPornography(),
        'copyright': types.InputReportReasonCopyright(),
        'other': types.InputReportReasonOther(),
    }
    reason = reasons.get(args.reason, types.InputReportReasonOther())
    await client(functions.messages.ReportRequest(
        peer=peer, id=ids, reason=reason, message=args.message or ''
    ))
    print(f"Reported {len(ids)} messages in {args.chat}")

async def cmd_rename_sticker_set(client, args):
    """Rename a sticker set."""
    from telethon import functions, types
    await client(functions.stickers.RenameStickerSetRequest(
        stickerset=types.InputStickerSetShortName(short_name=args.short_name),
        title=args.title
    ))
    print(f"Sticker set @{args.short_name} renamed to '{args.title}'")

async def cmd_delete_sticker_set(client, args):
    """Delete an entire sticker set."""
    from telethon import functions, types
    await client(functions.stickers.DeleteStickerSetRequest(
        stickerset=types.InputStickerSetShortName(short_name=args.short_name)
    ))
    print(f"Sticker set @{args.short_name} deleted")

async def cmd_set_bot_info(client, args):
    """Set bot description/about (you must own the bot)."""
    from telethon import functions
    bot = await client.get_entity(args.bot)
    await client(functions.bots.SetBotInfoRequest(
        bot=bot, lang_code=args.lang or '',
        name=args.name or None,
        about=args.about or None,
        description=args.description or None,
    ))
    print(f"Bot info updated for {args.bot}")

async def cmd_set_bot_commands_custom(client, args):
    """Set commands for your bot."""
    from telethon import functions, types
    import json
    cmds_data = json.loads(args.commands)
    commands = [types.BotCommand(command=c['command'], description=c['description']) for c in cmds_data]
    await client(functions.bots.SetBotCommandsRequest(
        scope=types.BotCommandScopeDefault(),
        lang_code=args.lang or '',
        commands=commands
    ))
    print(f"Set {len(commands)} bot commands")

async def cmd_reset_bot_commands(client, args):
    """Reset bot commands."""
    from telethon import functions, types
    await client(functions.bots.ResetBotCommandsRequest(
        scope=types.BotCommandScopeDefault(),
        lang_code=args.lang or ''
    ))
    print("Bot commands reset")

async def cmd_set_notify_settings(client, args):
    """Set notification settings for a chat."""
    from telethon import functions, types
    if args.target in ('users', 'groups', 'channels'):
        peers = {'users': types.InputNotifyUsers(), 'groups': types.InputNotifyChats(), 'channels': types.InputNotifyBroadcasts()}
        peer = peers[args.target]
    else:
        entity = await client.get_entity(args.target)
        peer = types.InputNotifyPeer(peer=entity)
    settings = types.InputPeerNotifySettings(
        show_previews=not args.no_preview if args.no_preview else None,
        silent=args.silent or None,
        mute_until=2147483647 if args.mute else (0 if args.unmute else None),
    )
    await client(functions.account.UpdateNotifySettingsRequest(peer=peer, settings=settings))
    print(f"Notification settings updated for {args.target}")

async def cmd_stars_subscriptions(client, args):
    """List Stars subscriptions."""
    from telethon import functions, types
    result = await client(functions.payments.GetStarsSubscriptionsRequest(
        peer=types.InputPeerSelf(), offset='', missing_balance=False
    ))
    subs = getattr(result, 'subscriptions', [])
    print(f"Stars subscriptions: {len(subs)}")
    for s in subs:
        title = getattr(s, 'title', '?')
        pricing = getattr(s, 'pricing', None)
        print(f"  {title}: {pricing}")

async def cmd_get_recent_stickers(client, args):
    """Get recently used stickers."""
    from telethon import functions
    result = await client(functions.messages.GetRecentStickersRequest(hash=0, attached=False))
    stickers = getattr(result, 'stickers', [])
    print(f"Recent stickers: {len(stickers)}")
    for i, s in enumerate(stickers[:args.limit or 20]):
        emoji = ''
        for attr in getattr(s, 'attributes', []):
            if hasattr(attr, 'alt'):
                emoji = attr.alt
                break
        print(f"  [{i}] ID:{s.id} {emoji}")

async def cmd_get_recent_locations(client, args):
    """Get recent live locations in a chat."""
    from telethon import functions
    peer = await client.get_entity(args.chat)
    result = await client(functions.messages.GetRecentLocationsRequest(peer=peer, limit=args.limit or 20, hash=0))
    messages = getattr(result, 'messages', [])
    print(f"Recent locations: {len(messages)}")
    for m in messages:
        geo = getattr(getattr(m, 'media', None), 'geo', None)
        if geo:
            lat = getattr(geo, 'lat', '?')
            lon = getattr(geo, 'long', '?')
            print(f"  #{m.id}: {lat}, {lon}")


# --- Niche: Link Preview, Screenshot Notify, Auto-Download, Craft/Upgrade Gift, Unique Gift ---

async def cmd_get_web_page_preview(client, args):
    """Preview a URL — extract title, description, embed info."""
    from telethon.tl.functions.messages import GetWebPagePreviewRequest
    result = await client(GetWebPagePreviewRequest(message=args.url))
    wp = getattr(result, 'webpage', None) if hasattr(result, 'webpage') else result
    if not wp or getattr(wp, 'CONSTRUCTOR_ID', 0) == 0xeb1477e8:
        print("No preview available for this URL.")
        return
    print(f"URL: {getattr(wp, 'url', '?')}")
    print(f"Display URL: {getattr(wp, 'display_url', '?')}")
    print(f"Type: {getattr(wp, 'type', '?')}")
    print(f"Site: {getattr(wp, 'site_name', '?')}")
    print(f"Title: {getattr(wp, 'title', '?')}")
    desc = getattr(wp, 'description', '')
    if desc:
        print(f"Description: {desc[:300]}")
    print(f"Embed URL: {getattr(wp, 'embed_url', '-')}")
    print(f"Embed type: {getattr(wp, 'embed_type', '-')}")
    print(f"Embed size: {getattr(wp, 'embed_width', '?')}x{getattr(wp, 'embed_height', '?')}")
    if getattr(wp, 'photo', None):
        print(f"Photo: yes (id={wp.photo.id})")
    if getattr(wp, 'document', None):
        print(f"Document: yes (id={wp.document.id}, mime={getattr(wp.document, 'mime_type', '?')})")
    print(f"Hash: {getattr(wp, 'hash', '?')}")


async def cmd_send_screenshot_notification(client, args):
    """Notify the peer that you took a screenshot of the chat."""
    import random as _rnd
    from telethon.tl.functions.messages import SendScreenshotNotificationRequest
    from telethon.tl.types import InputReplyToMessage
    peer = await client.get_input_entity(args.chat)
    reply_to = InputReplyToMessage(reply_to_msg_id=int(args.msg_id)) if args.msg_id else InputReplyToMessage(reply_to_msg_id=0)
    await client(SendScreenshotNotificationRequest(
        peer=peer,
        reply_to=reply_to,
        random_id=_rnd.randrange(-2**63, 2**63),
    ))
    print(f"Screenshot notification sent to {args.chat}")


async def cmd_get_auto_download_settings(client, args):
    """Show current auto-download settings (low/medium/high data)."""
    from telethon.tl.functions.account import GetAutoDownloadSettingsRequest
    result = await client(GetAutoDownloadSettingsRequest())
    for label, settings in [("Low", result.low), ("Medium", result.medium), ("High", result.high)]:
        print(f"\n=== {label} data ===")
        print(f"  Disabled: {getattr(settings, 'disabled', '?')}")
        print(f"  Photo size max: {getattr(settings, 'photo_size_max', '?')} bytes")
        print(f"  Video size max: {getattr(settings, 'video_size_max', '?')} bytes")
        print(f"  File size max: {getattr(settings, 'file_size_max', '?')} bytes")
        print(f"  Video upload maxbitrate: {getattr(settings, 'video_upload_maxbitrate', '?')}")
        print(f"  Small queue active: {getattr(settings, 'small_queue_active_operations_max', '?')}")
        print(f"  Large queue active: {getattr(settings, 'large_queue_active_operations_max', '?')}")


async def cmd_save_auto_download_settings(client, args):
    """Update auto-download settings for a tier (low/high)."""
    from telethon.tl.functions.account import SaveAutoDownloadSettingsRequest
    from telethon.tl.types import AutoDownloadSettings
    settings = AutoDownloadSettings(
        photo_size_max=int(args.photo_max) if args.photo_max else 1048576,
        video_size_max=int(args.video_max) if args.video_max else 15728640,
        file_size_max=int(args.file_max) if args.file_max else 3145728,
        disabled=args.disabled,
    )
    await client(SaveAutoDownloadSettingsRequest(
        settings=settings,
        low=args.tier == "low",
        high=args.tier == "high",
    ))
    print(f"Auto-download settings updated for tier={args.tier}")


async def cmd_upgrade_star_gift(client, args):
    """Upgrade a received star gift to unique (costs Stars)."""
    from telethon.tl.functions.payments import UpgradeStarGiftRequest, GetStarGiftUpgradePreviewRequest
    from telethon.tl.types import InputSavedStarGiftUser
    if args.preview:
        result = await client(GetStarGiftUpgradePreviewRequest(gift_id=int(args.gift_id)))
        print(f"Upgrade preview for gift #{args.gift_id}:")
        sample = getattr(result, 'sample_attributes', [])
        for attr in sample:
            print(f"  {attr.__class__.__name__}: {attr}")
        return
    stargift = InputSavedStarGiftUser(msg_id=int(args.msg_id))
    result = await client(UpgradeStarGiftRequest(
        stargift=stargift,
        keep_original_details=args.keep_details,
    ))
    print(f"Gift upgraded! Result: {result}")


async def cmd_get_unique_star_gift(client, args):
    """Get info about a unique star gift by its slug."""
    from telethon.tl.functions.payments import GetUniqueStarGiftRequest
    result = await client(GetUniqueStarGiftRequest(slug=args.slug))
    gift = getattr(result, 'gift', result)
    print(f"Slug: {args.slug}")
    print(f"Title: {getattr(gift, 'title', '?')}")
    print(f"Num: {getattr(gift, 'num', '?')}")
    print(f"Owner ID: {getattr(gift, 'owner_id', '?')}")
    print(f"Availability issued: {getattr(gift, 'availability_issued', '?')}")
    print(f"Availability total: {getattr(gift, 'availability_total', '?')}")
    attrs = getattr(gift, 'attributes', [])
    for a in attrs:
        print(f"  Attr: {a.__class__.__name__}: {a}")


async def cmd_get_saved_star_gifts(client, args):
    """List saved star gifts for self or a peer."""
    from telethon.tl.functions.payments import GetSavedStarGiftsRequest
    peer = await client.get_input_entity(args.peer) if args.peer else await client.get_input_entity("me")
    result = await client(GetSavedStarGiftsRequest(
        peer=peer, offset=args.offset or "", limit=args.limit,
        exclude_unsaved=args.exclude_unsaved,
        sort_by_value=args.sort_by_value,
    ))
    gifts = getattr(result, 'gifts', [])
    print(f"Saved star gifts: {len(gifts)} (count={getattr(result, 'count', '?')})")
    for g in gifts:
        gift_obj = getattr(g, 'gift', None)
        stars = getattr(gift_obj, 'stars', '?') if gift_obj else '?'
        msg_id = getattr(g, 'msg_id', '?')
        from_id = getattr(g, 'from_id', '?')
        date = getattr(g, 'date', '?')
        saved = getattr(g, 'unsaved', False)
        print(f"  msg_id={msg_id} from={from_id} stars={stars} date={date} unsaved={saved}")


async def cmd_gift_withdrawal_url(client, args):
    """Get TON withdrawal URL for a unique star gift (requires 2FA)."""
    from telethon.tl.functions.payments import GetStarGiftWithdrawalUrlRequest
    from telethon.tl.functions.account import GetPasswordRequest
    from telethon.tl.types import InputSavedStarGiftUser
    password_info = await client(GetPasswordRequest())
    import hashlib
    from telethon.password import compute_check
    srp = compute_check(password_info, args.password)
    stargift = InputSavedStarGiftUser(msg_id=int(args.msg_id))
    result = await client(GetStarGiftWithdrawalUrlRequest(stargift=stargift, password=srp))
    print(f"Withdrawal URL: {getattr(result, 'url', result)}")


# ========== ARGPARSE ==========

async def main():
    parser = argparse.ArgumentParser(description="Telegram CLI for Claude Code")
    sub = parser.add_subparsers(dest="command", help="Command")

    # --- Read ---
    p = sub.add_parser("dialogs", help="List recent dialogs")
    p.add_argument("--limit", type=int, default=30)

    p = sub.add_parser("read-chat", help="Read chat with a user/group")
    p.add_argument("target", help="Username, phone, or name")
    p.add_argument("--limit", type=int, default=50)

    p = sub.add_parser("read-channel", help="Read channel posts with reactions")
    p.add_argument("target", help="Channel username or link")
    p.add_argument("--limit", type=int, default=30)

    # --- Search ---
    p = sub.add_parser("search", help="Search messages globally or in chat")
    p.add_argument("query", help="Search query")
    p.add_argument("--chat", help="Search in specific chat only")
    p.add_argument("--limit", type=int, default=30)

    p = sub.add_parser("mentions", help="Find mentions of @YourUsername")
    p.add_argument("--limit", type=int, default=30)

    # --- Parsing people ---
    p = sub.add_parser("parse-comments", help="Parse comments on a channel post")
    p.add_argument("channel", help="Channel username")
    p.add_argument("post_id", help="Post ID")
    p.add_argument("--limit", type=int, default=100)

    p = sub.add_parser("parse-commenters", help="Parse PEOPLE who commented (for leads)")
    p.add_argument("channel", help="Channel username")
    p.add_argument("post_id", help="Post ID")
    p.add_argument("--limit", type=int, default=200)
    p.add_argument("--output", help="Save JSON to file")

    p = sub.add_parser("participants", help="List group/channel members with profiles")
    p.add_argument("target", help="Group/channel username")
    p.add_argument("--limit", type=int, default=200)
    p.add_argument("--output", help="Save JSON to file")

    p = sub.add_parser("user-messages", help="All messages from a user in a group")
    p.add_argument("target", help="Group/channel")
    p.add_argument("user", help="User to filter by")
    p.add_argument("--limit", type=int, default=50)

    # --- Info ---
    p = sub.add_parser("contacts", help="List contacts")
    p.add_argument("--limit", type=int, default=100)

    sub.add_parser("folders", help="List Telegram folders")

    p = sub.add_parser("folder-chats", help="List chats in a folder")
    p.add_argument("folder_name", help="Folder name (partial match)")

    p = sub.add_parser("user-info", help="Full user/channel info (bio, photos, etc)")
    p.add_argument("target", help="Username or phone")

    p = sub.add_parser("channel-stats", help="Channel engagement statistics")
    p.add_argument("target", help="Channel username")

    # --- Download ---
    p = sub.add_parser("download", help="Download media from chat/channel")
    p.add_argument("target", help="Chat/channel username")
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--output", help="Output directory")

    p = sub.add_parser("download-photo", help="Download profile photos")
    p.add_argument("target", help="Username")
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--output", help="Output directory")

    # --- Export ---
    p = sub.add_parser("export-chat", help="Export chat to JSON")
    p.add_argument("target", help="Chat/channel username")
    p.add_argument("--limit", type=int, default=500)
    p.add_argument("--output", help="Output JSON file")

    # --- Admin ---
    p = sub.add_parser("pinned", help="Get pinned messages")
    p.add_argument("target", help="Chat/channel")
    p.add_argument("--limit", type=int, default=20)

    p = sub.add_parser("admin-log", help="View admin actions log")
    p.add_argument("target", help="Channel/group")
    p.add_argument("--limit", type=int, default=30)

    sub.add_parser("drafts", help="Show unsent message drafts")

    # --- Messaging ---
    p = sub.add_parser("send", help="Send a text message")
    p.add_argument("target", help="User/group/channel")
    p.add_argument("text", help="Message text")
    p.add_argument("--reply-to", help="Reply to message ID")
    p.add_argument("--schedule", help="Schedule ISO datetime (UTC), e.g. 2026-02-10T15:00:00")

    p = sub.add_parser("send-file", help="Send a file/photo/video")
    p.add_argument("target", help="User/group/channel")
    p.add_argument("file", help="Path to file")
    p.add_argument("--caption", help="Caption text")
    p.add_argument("--reply-to", help="Reply to message ID")
    p.add_argument("--voice", action="store_true", help="Send as voice note")
    p.add_argument("--video-note", action="store_true", help="Send as video circle")

    p = sub.add_parser("forward", help="Forward messages between chats")
    p.add_argument("source", help="Source chat")
    p.add_argument("target", help="Destination chat")
    p.add_argument("ids", help="Comma-separated message IDs")

    p = sub.add_parser("reply", help="Reply to a specific message")
    p.add_argument("target", help="Chat")
    p.add_argument("msg_id", help="Message ID to reply to")
    p.add_argument("text", help="Reply text")

    p = sub.add_parser("edit", help="Edit own message")
    p.add_argument("target", help="Chat")
    p.add_argument("msg_id", help="Message ID to edit")
    p.add_argument("text", help="New text")

    p = sub.add_parser("delete", help="Delete messages by IDs")
    p.add_argument("target", help="Chat")
    p.add_argument("ids", help="Comma-separated message IDs")

    p = sub.add_parser("react", help="React to a message with emoji")
    p.add_argument("target", help="Chat")
    p.add_argument("msg_id", help="Message ID")
    p.add_argument("emoji", help="Emoji to react with")

    p = sub.add_parser("schedule", help="Send a scheduled message")
    p.add_argument("target", help="User/group/channel")
    p.add_argument("datetime", help="ISO datetime (UTC), e.g. 2026-02-10T15:00:00")
    p.add_argument("text", help="Message text")

    p = sub.add_parser("create-poll", help="Create a poll")
    p.add_argument("target", help="Chat")
    p.add_argument("question", help="Poll question")
    p.add_argument("options", help="Options separated by |")
    p.add_argument("--quiz", action="store_true", help="Create as quiz")

    p = sub.add_parser("broadcast", help="Send message to multiple users")
    p.add_argument("text", help="Message text")
    p.add_argument("--targets", help="Comma-separated usernames")
    p.add_argument("--file", help="File with one username per line")
    p.add_argument("--delay", type=float, default=2, help="Delay between sends (seconds)")

    # --- Group/Channel management ---
    p = sub.add_parser("pin", help="Pin a message")
    p.add_argument("target", help="Chat")
    p.add_argument("msg_id", help="Message ID")
    p.add_argument("--silent", action="store_true", help="Pin without notification")

    p = sub.add_parser("unpin", help="Unpin a message")
    p.add_argument("target", help="Chat")
    p.add_argument("--msg-id", help="Message ID (omit to unpin all)")

    p = sub.add_parser("invite", help="Invite user to group/channel")
    p.add_argument("target", help="Group/channel")
    p.add_argument("user", help="Username to invite")

    p = sub.add_parser("kick", help="Kick user from group")
    p.add_argument("target", help="Group/channel")
    p.add_argument("user", help="Username to kick")

    p = sub.add_parser("ban", help="Ban user from group")
    p.add_argument("target", help="Group/channel")
    p.add_argument("user", help="Username to ban")

    p = sub.add_parser("unban", help="Unban user")
    p.add_argument("target", help="Group/channel")
    p.add_argument("user", help="Username to unban")

    p = sub.add_parser("create-group", help="Create a new group")
    p.add_argument("name", help="Group name")
    p.add_argument("users", help="Comma-separated usernames to add")

    p = sub.add_parser("create-channel", help="Create a new channel")
    p.add_argument("name", help="Channel name")
    p.add_argument("--about", help="Channel description")

    p = sub.add_parser("edit-chat", help="Edit group/channel settings")
    p.add_argument("target", help="Group/channel")
    p.add_argument("--title", help="New title")
    p.add_argument("--about", help="New description")
    p.add_argument("--photo", help="New photo file path")

    # --- Account actions ---
    p = sub.add_parser("join", help="Join a group/channel")
    p.add_argument("target", help="Channel/group username or invite link")

    p = sub.add_parser("leave", help="Leave a group/channel")
    p.add_argument("target", help="Channel/group")

    p = sub.add_parser("mark-read", help="Mark chat as read")
    p.add_argument("target", help="Chat to mark read")

    p = sub.add_parser("archive", help="Archive a chat")
    p.add_argument("target", help="Chat to archive")

    p = sub.add_parser("unarchive", help="Unarchive a chat")
    p.add_argument("target", help="Chat to unarchive")

    p = sub.add_parser("mute", help="Mute a chat")
    p.add_argument("target", help="Chat to mute")

    p = sub.add_parser("unmute", help="Unmute a chat")
    p.add_argument("target", help="Chat to unmute")

    p = sub.add_parser("block", help="Block a user")
    p.add_argument("target", help="User to block")

    p = sub.add_parser("unblock", help="Unblock a user")
    p.add_argument("target", help="User to unblock")

    p = sub.add_parser("set-bio", help="Update own bio")
    p.add_argument("text", help="New bio text")

    p = sub.add_parser("set-name", help="Update own name")
    p.add_argument("--first", help="First name")
    p.add_argument("--last", help="Last name")

    p = sub.add_parser("set-photo", help="Set own profile photo")
    p.add_argument("file", help="Photo file path")

    # --- Advanced search / info ---
    p = sub.add_parser("search-media", help="Search by media type in chat")
    p.add_argument("target", help="Chat")
    p.add_argument("type", help="Type: photo, video, document, url, voice, music, gif")
    p.add_argument("--limit", type=int, default=30)

    p = sub.add_parser("search-date", help="Search messages by date range")
    p.add_argument("target", help="Chat")
    p.add_argument("--start", help="Start date ISO, e.g. 2026-01-01")
    p.add_argument("--end", help="End date ISO, e.g. 2026-02-01")
    p.add_argument("--limit", type=int, default=50)

    p = sub.add_parser("links", help="Extract all URLs from a chat")
    p.add_argument("target", help="Chat")
    p.add_argument("--limit", type=int, default=100)

    p = sub.add_parser("hashtags", help="Search by hashtag in chat")
    p.add_argument("target", help="Chat")
    p.add_argument("tag", help="Hashtag to search")
    p.add_argument("--limit", type=int, default=50)

    p = sub.add_parser("common-groups", help="Get common groups with user")
    p.add_argument("target", help="User")

    p = sub.add_parser("similar-channels", help="Get recommended similar channels")
    p.add_argument("target", help="Channel")

    p = sub.add_parser("stories", help="View stories of a user/channel")
    p.add_argument("target", help="User/channel")

    p = sub.add_parser("saved", help="View saved messages")
    p.add_argument("--limit", type=int, default=30)

    p = sub.add_parser("blocked-list", help="List blocked users")
    p.add_argument("--limit", type=int, default=100)

    p = sub.add_parser("unread", help="Show chats with unread messages")
    p.add_argument("--limit", type=int, default=30)

    p = sub.add_parser("poll-results", help="Get poll vote results")
    p.add_argument("target", help="Chat")
    p.add_argument("msg_id", help="Poll message ID")

    # --- Star Gifts ---
    sp = sub.add_parser("star-gifts", help="List available star gifts")

    sp = sub.add_parser("send-star-gift", help="Send a star gift to a user")
    sp.add_argument("target", help="Target @username")
    sp.add_argument("gift_id", type=int, help="Gift ID (from star-gifts)")
    sp.add_argument("--message", "-m", help="Message with gift")
    sp.add_argument("--anonymous", action="store_true", help="Hide sender name")

    # --- Stories (extended) ---
    sp = sub.add_parser("post-story", help="Post a story (photo/video)")
    sp.add_argument("file", help="Photo or video file path")
    sp.add_argument("--caption", "-c", help="Story caption")
    sp.add_argument("--channel", help="Post to channel instead of personal")
    sp.add_argument("--contacts-only", action="store_true", help="Visible to contacts only")
    sp.add_argument("--period", type=int, default=86400, help="Story duration in seconds (default 24h)")

    sp = sub.add_parser("story-views", help="Get story viewers")
    sp.add_argument("story_id", type=int, help="Story ID")
    sp.add_argument("--limit", "-n", type=int, default=100)

    sp = sub.add_parser("story-albums", help="List story albums")
    sp.add_argument("target", nargs="?", help="Target user/channel")

    # --- Premium ---
    sp = sub.add_parser("boost-channel", help="Boost a channel")
    sp.add_argument("channel", help="Channel to boost")

    # --- Stories extended ---
    sp = sub.add_parser("edit-story", help="Edit a story caption")
    sp.add_argument("story_id", type=int)
    sp.add_argument("--caption", "-c", help="New caption")
    sp.add_argument("--channel", help="Channel story")

    sp = sub.add_parser("pin-story", help="Pin/unpin a story")
    sp.add_argument("story_id", type=int)
    sp.add_argument("--channel", help="Channel story")
    sp.add_argument("--unpin", action="store_true")

    sp = sub.add_parser("story-reactions", help="Get reactions on a story")
    sp.add_argument("story_id", type=int)
    sp.add_argument("--channel", help="Channel story")
    sp.add_argument("--limit", "-n", type=int, default=100)

    sp = sub.add_parser("react-story", help="React to a story")
    sp.add_argument("target", help="Story owner @username")
    sp.add_argument("story_id", type=int)
    sp.add_argument("emoji", help="Reaction emoji")

    sp = sub.add_parser("stealth-mode", help="Activate stealth mode for stories")

    sp = sub.add_parser("story-archive", help="View stories archive")
    sp.add_argument("target", nargs="?", help="Target user")
    sp.add_argument("--limit", "-n", type=int, default=50)

    sp = sub.add_parser("export-story-link", help="Export link to a story")
    sp.add_argument("story_id", type=int)
    sp.add_argument("target", nargs="?", help="Story owner")

    # --- Stars / Payments ---
    sp = sub.add_parser("stars-balance", help="Check Stars balance")

    sp = sub.add_parser("stars-history", help="Stars transaction history")
    sp.add_argument("--limit", "-n", type=int, default=20)
    sp.add_argument("--inbound", action="store_true", help="Only incoming")
    sp.add_argument("--outbound", action="store_true", help="Only outgoing")

    sp = sub.add_parser("saved-gifts", help="View received star gifts")
    sp.add_argument("target", nargs="?", help="Target user")
    sp.add_argument("--limit", "-n", type=int, default=20)

    sp = sub.add_parser("convert-gift", help="Convert star gift to stars")
    sp.add_argument("msg_id", type=int, help="Gift message ID")

    sp = sub.add_parser("gift-premium", help="Gift Premium options")
    sp.add_argument("target", help="Target @username")

    sp = sub.add_parser("giveaway-info", help="Get giveaway info")
    sp.add_argument("channel", help="Channel with giveaway")
    sp.add_argument("msg_id", type=int, help="Giveaway message ID")

    # --- Business ---
    sp = sub.add_parser("set-business-hours", help="Set business hours")
    sp.add_argument("--open", default="09:00", help="Opening time HH:MM")
    sp.add_argument("--close", default="18:00", help="Closing time HH:MM")
    sp.add_argument("--timezone", default="UTC")
    sp.add_argument("--clear", action="store_true")

    sp = sub.add_parser("set-business-location", help="Set business location")
    sp.add_argument("address", nargs="?", help="Address text")
    sp.add_argument("--clear", action="store_true")

    sp = sub.add_parser("set-business-greeting", help="Set business greeting")
    sp.add_argument("--days", type=int, default=7, help="Inactivity days")
    sp.add_argument("--clear", action="store_true")

    sp = sub.add_parser("set-business-away", help="Set business away message")
    sp.add_argument("--offline-only", action="store_true")
    sp.add_argument("--clear", action="store_true")

    sp = sub.add_parser("business-links", help="List business chat links")

    # --- Account extended ---
    sp = sub.add_parser("set-birthday", help="Set birthday")
    sp.add_argument("date", nargs="?", help="YYYY-MM-DD or MM-DD")
    sp.add_argument("--clear", action="store_true")

    sp = sub.add_parser("set-emoji-status", help="Set emoji status")
    sp.add_argument("emoji_id", nargs="?", help="Custom emoji document ID")
    sp.add_argument("--clear", action="store_true")

    sp = sub.add_parser("close-friends", help="Manage close friends")
    sp.add_argument("--add", nargs="+", help="Users to add")

    sp = sub.add_parser("online-count", help="Online users in chat")
    sp.add_argument("chat", help="Chat/group")

    sp = sub.add_parser("contact-birthdays", help="Contacts birthdays")

    sp = sub.add_parser("resolve-phone", help="Find user by phone number")
    sp.add_argument("phone", help="Phone number (without +)")

    # --- Channels extended ---
    sp = sub.add_parser("toggle-forum", help="Toggle forum mode")
    sp.add_argument("channel")
    sp.add_argument("--disable", action="store_true")

    sp = sub.add_parser("export-msg-link", help="Export message link")
    sp.add_argument("channel")
    sp.add_argument("msg_id", type=int)

    sp = sub.add_parser("set-channel-emoji", help="Set channel emoji status")
    sp.add_argument("channel")
    sp.add_argument("emoji_id", nargs="?")
    sp.add_argument("--clear", action="store_true")

    sp = sub.add_parser("toggle-signatures", help="Toggle channel signatures")
    sp.add_argument("channel")
    sp.add_argument("--disable", action="store_true")
    sp.add_argument("--profiles", action="store_true", help="Show profile photos")

    # --- Messages extras ---
    sp = sub.add_parser("translate-msg", help="Translate a message")
    sp.add_argument("chat")
    sp.add_argument("msg_id", type=int)
    sp.add_argument("--lang", "-l", default="en")

    sp = sub.add_parser("transcribe-voice", help="Transcribe voice message")
    sp.add_argument("chat")
    sp.add_argument("msg_id", type=int)

    # --- AI commands ---
    sp = sub.add_parser("ai-compose", help="Compose text with Telegram AI")
    sp.add_argument("text", help="Text to compose/improve")
    sp.add_argument("--proofread", action="store_true", help="Proofread mode")
    sp.add_argument("--emojify", action="store_true", help="Add emojis")
    sp.add_argument("--translate", help="Translate to language code")
    sp.add_argument("--tone", help="Change tone (formal, casual, etc)")

    sp = sub.add_parser("ai-proofread", help="Proofread text with AI")
    sp.add_argument("text", help="Text to proofread")

    sp = sub.add_parser("ai-emojify", help="Add emojis with AI")
    sp.add_argument("text", help="Text to emojify")

    sp = sub.add_parser("ai-translate", help="Translate with AI")
    sp.add_argument("text", help="Text to translate")
    sp.add_argument("--lang", "-l", required=True, help="Target language code")

    sp = sub.add_parser("ai-change-tone", help="Change text tone with AI")
    sp.add_argument("text", help="Text to modify")
    sp.add_argument("--tone", "-t", required=True, help="Desired tone")

    # --- Chat management ---
    sp = sub.add_parser("set-auto-delete", help="Set message auto-delete timer")
    sp.add_argument("chat", help="Chat/group")
    sp.add_argument("seconds", type=int, help="TTL in seconds (0=disable, 86400=1day, 604800=1week)")

    sp = sub.add_parser("create-topic", help="Create forum topic")
    sp.add_argument("channel", help="Forum channel")
    sp.add_argument("title", help="Topic title")
    sp.add_argument("--color", type=int, help="Icon color")

    sp = sub.add_parser("chat-themes", help="List chat themes")

    sp = sub.add_parser("toggle-sponsored", help="Toggle sponsored messages")
    sp.add_argument("--disable", action="store_true")

    # --- Account/Profile extended ---
    sp = sub.add_parser("set-personal-channel", help="Link channel to profile")
    sp.add_argument("channel", nargs="?", help="Channel to link")
    sp.add_argument("--clear", action="store_true")

    sp = sub.add_parser("set-color", help="Set profile/reply color")
    sp.add_argument("color_id", type=int, help="Color ID")
    sp.add_argument("--emoji-id", help="Background emoji document ID")
    sp.add_argument("--profile", action="store_true", help="Set profile color (vs reply color)")

    sp = sub.add_parser("paid-msg-revenue", help="Check paid messages revenue")

    sp = sub.add_parser("saved-music", help="List saved music")

    sp = sub.add_parser("set-wallpaper", help="Manage wallpapers")
    sp.add_argument("--reset", action="store_true", help="Reset to default")

    # --- Stickers & Emoji ---
    sp = sub.add_parser("my-stickers", help="List your sticker sets")
    sp.add_argument("--limit", "-n", type=int, default=20)

    sp = sub.add_parser("emoji-packs", help="List installed emoji packs")

    sp = sub.add_parser("featured-stickers", help="Trending sticker sets")

    sp = sub.add_parser("install-stickers", help="Install a sticker set")
    sp.add_argument("short_name", help="Sticker set short name")

    sp = sub.add_parser("uninstall-stickers", help="Remove a sticker set")
    sp.add_argument("short_name", help="Sticker set short name")

    # --- Privacy ---
    sp = sub.add_parser("get-privacy", help="Get privacy settings")
    sp.add_argument("key", help="phone|lastseen|photo|bio|birthday|forwards|calls|invite|voice")

    sp = sub.add_parser("set-privacy", help="Set privacy level")
    sp.add_argument("key", help="phone|lastseen|photo|bio|birthday|forwards|calls|invite|voice")
    sp.add_argument("value", help="everybody|contacts|nobody")

    sp = sub.add_parser("sessions", help="List active sessions/devices")

    # --- Misc ---
    sp = sub.add_parser("nearby", help="Find nearby users/groups")
    sp.add_argument("lat", help="Latitude")
    sp.add_argument("lon", help="Longitude")

    sp = sub.add_parser("report", help="Report user/channel")
    sp.add_argument("target", help="@username to report")
    sp.add_argument("reason", help="spam|violence|porn|abuse|copyright|fake|drugs|personal|other")
    sp.add_argument("--message", "-m", help="Report description")

    sp = sub.add_parser("add-contact", help="Add contact")
    sp.add_argument("target", help="@username or phone")
    sp.add_argument("--first-name", "-f", default="")
    sp.add_argument("--last-name", "-l", default="")
    sp.add_argument("--phone", "-p", default="")

    sp = sub.add_parser("delete-contact", help="Delete contact")
    sp.add_argument("target", help="@username")

    # --- Account / Settings (batch 5) ---
    sp = sub.add_parser("ringtones", help="List saved ringtones")

    sp = sub.add_parser("global-privacy", help="Global privacy settings")
    sp.add_argument("--set", action="store_true", help="Set mode")
    sp.add_argument("--archive-new", action="store_true")
    sp.add_argument("--keep-archived", action="store_true")
    sp.add_argument("--keep-folders", action="store_true")
    sp.add_argument("--hide-read", action="store_true")
    sp.add_argument("--require-premium", action="store_true")

    sp = sub.add_parser("reorder-usernames", help="Reorder usernames")
    sp.add_argument("usernames", nargs="+", help="Usernames in desired order")

    sp = sub.add_parser("connected-bots", help="List connected business bots")

    sp = sub.add_parser("web-sessions", help="List web sessions")

    sp = sub.add_parser("account-ttl", help="Account self-destruct timer")
    sp.add_argument("--days", type=int, help="Set TTL in days (e.g. 365)")

    sp = sub.add_parser("content-settings", help="Sensitive content (18+)")
    sp.add_argument("--show", action="store_true")
    sp.add_argument("--hide", action="store_true")

    sp = sub.add_parser("contact-photo", help="Set photo for contact")
    sp.add_argument("target", help="@username")
    sp.add_argument("file", help="Photo file path")
    sp.add_argument("--suggest", action="store_true", help="Suggest instead of set")

    sp = sub.add_parser("collectible-emoji", help="List collectible emoji statuses")

    sp = sub.add_parser("notify-settings", help="Notification settings")
    sp.add_argument("target", help="users|groups|channels or @chat")

    sp = sub.add_parser("auto-save", help="Auto-save settings")

    sp = sub.add_parser("live-story", help="Start live story")
    sp.add_argument("--channel", help="Channel for live")

    # --- Bot Management (batch 5) ---
    sp = sub.add_parser("bot-info", help="Get bot info and commands")
    sp.add_argument("bot", help="@botusername")
    sp.add_argument("--lang", default="en")

    sp = sub.add_parser("bot-commands", help="Get bot commands")
    sp.add_argument("--lang", default="")

    sp = sub.add_parser("admined-bots", help="List your bots")

    sp = sub.add_parser("popular-bots", help="Popular app bots")
    sp.add_argument("--limit", "-n", type=int, default=20)

    sp = sub.add_parser("bot-recommendations", help="Similar bots")
    sp.add_argument("bot", help="@botusername")

    sp = sub.add_parser("shared-folders", help="List shared chat folders")

    sp = sub.add_parser("top-peers", help="Most contacted peers")
    sp.add_argument("--limit", "-n", type=int, default=20)

    sp = sub.add_parser("search-global", help="Search across all chats")
    sp.add_argument("query", help="Search query")
    sp.add_argument("--limit", "-n", type=int, default=20)

    sp = sub.add_parser("get-replies", help="Get thread replies for a message")
    sp.add_argument("chat", help="Chat/channel")
    sp.add_argument("msg_id", type=int, help="Message ID")
    sp.add_argument("--limit", "-n", type=int, default=50)

    sp = sub.add_parser("export-folder-invite", help="Export folder invite link")
    sp.add_argument("folder_id", type=int, help="Folder filter ID")
    sp.add_argument("--title", default="Shared Folder")

    sp = sub.add_parser("join-folder", help="Join shared folder by link")
    sp.add_argument("slug", help="Invite slug or full link")

    sp = sub.add_parser("check-username", help="Check username availability")
    sp.add_argument("username", help="Username to check")

    sp = sub.add_parser("update-status", help="Set online/offline")
    sp.add_argument("--offline", action="store_true")

    sp = sub.add_parser("password-status", help="Check 2FA status")

    sp = sub.add_parser("delete-messages", help="Delete messages by IDs")
    sp.add_argument("chat", help="Chat")
    sp.add_argument("ids", help="Comma-separated message IDs")
    sp.add_argument("--me-only", action="store_true", help="Delete only for me")

    sp = sub.add_parser("clear-history", help="Clear chat history")
    sp.add_argument("chat", help="Chat to clear")
    sp.add_argument("--me-only", action="store_true")

    sp = sub.add_parser("read-history", help="Mark chat as read")
    sp.add_argument("chat", help="Chat to mark")

    sp = sub.add_parser("send-typing", help="Send typing indicator")
    sp.add_argument("chat", help="Chat")
    sp.add_argument("--action", "-a", default="typing", help="typing|upload_photo|record_video|record_audio|choose_sticker|cancel")

    sp = sub.add_parser("export-contact-token", help="Export your contact token")

    sp = sub.add_parser("import-contact-token", help="Import contact by token")
    sp.add_argument("token", help="Contact token")

    # Final batch
    sp = sub.add_parser("create-sticker-set", help="Create sticker set via API")
    sp.add_argument("title", help="Pack title")
    sp.add_argument("short_name", help="Short name (ends in _by_botname)")
    sp.add_argument("file", help="First sticker file (webp/webm)")
    sp.add_argument("--emoji", default="\U0001f600", help="Emoji for sticker")
    sp.add_argument("--emoji-type", action="store_true", help="Custom emoji pack")

    sp = sub.add_parser("change-phone", help="Change phone number")
    sp.add_argument("phone", help="New phone number with country code")

    sp = sub.add_parser("takeout", help="Start GDPR data export")
    sp.add_argument("--contacts", action="store_true")
    sp.add_argument("--users", action="store_true")
    sp.add_argument("--chats", action="store_true")
    sp.add_argument("--groups", action="store_true")
    sp.add_argument("--channels", action="store_true")
    sp.add_argument("--files", action="store_true")
    sp.add_argument("--max-size", type=int, default=524288000, help="Max file size bytes")

    sp = sub.add_parser("mark-unread", help="Mark chat as unread")
    sp.add_argument("chat")

    sp = sub.add_parser("scheduled-messages", help="View scheduled messages")
    sp.add_argument("chat")

    sp = sub.add_parser("delete-scheduled", help="Delete scheduled messages")
    sp.add_argument("chat")
    sp.add_argument("ids", help="Comma-separated message IDs")

    sp = sub.add_parser("report-spam", help="Report chat as spam")
    sp.add_argument("chat")

    sp = sub.add_parser("toggle-join-request", help="Toggle join approval")
    sp.add_argument("channel")
    sp.add_argument("--disable", action="store_true")

    sp = sub.add_parser("set-discussion", help="Link discussion group to channel")
    sp.add_argument("channel")
    sp.add_argument("group", nargs="?")
    sp.add_argument("--clear", action="store_true")

    sp = sub.add_parser("toggle-slow-mode", help="Set slow mode delay")
    sp.add_argument("chat")
    sp.add_argument("seconds", type=int, help="0=off, 10/30/60/300/900/3600")

    sp = sub.add_parser("set-chat-photo", help="Set group/channel photo")
    sp.add_argument("chat")
    sp.add_argument("file", help="Photo file")

    sp = sub.add_parser("get-invite-link", help="Get/create invite link")
    sp.add_argument("chat")
    sp.add_argument("--title", help="Link title")
    sp.add_argument("--limit", type=int, help="Usage limit")

    # --- Last batch (25 commands) ---
    sp = sub.add_parser("vote", help="Vote in a poll")
    sp.add_argument("chat")
    sp.add_argument("msg_id", type=int)
    sp.add_argument("options", help="Comma-separated option indices (0,1,...)")

    sp = sub.add_parser("msg-readers", help="Who read a message")
    sp.add_argument("chat")
    sp.add_argument("msg_id", type=int)

    sp = sub.add_parser("msg-views", help="Message view counts")
    sp.add_argument("chat")
    sp.add_argument("ids", help="Comma-separated message IDs")

    sp = sub.add_parser("unread-mentions", help="Unread mentions in chat")
    sp.add_argument("chat")
    sp.add_argument("--limit", "-n", type=int, default=20)

    sp = sub.add_parser("read-mentions", help="Mark mentions as read")
    sp.add_argument("chat")

    sp = sub.add_parser("unread-reactions", help="Unread reactions in chat")
    sp.add_argument("chat")
    sp.add_argument("--limit", "-n", type=int, default=20)

    sp = sub.add_parser("read-reactions", help="Mark reactions as read")
    sp.add_argument("chat")

    sp = sub.add_parser("edit-admin", help="Set/remove admin")
    sp.add_argument("channel")
    sp.add_argument("user")
    sp.add_argument("--remove", action="store_true")
    sp.add_argument("--rank", default="", help="Admin title")
    sp.add_argument("--can-post", action="store_true")
    sp.add_argument("--can-edit", action="store_true")

    sp = sub.add_parser("edit-channel-title", help="Change channel title")
    sp.add_argument("channel")
    sp.add_argument("title")

    sp = sub.add_parser("edit-channel-about", help="Change channel description")
    sp.add_argument("channel")
    sp.add_argument("about")

    sp = sub.add_parser("get-sticker-set", help="Get sticker set info")
    sp.add_argument("short_name")

    sp = sub.add_parser("add-sticker", help="Add sticker to existing set")
    sp.add_argument("short_name")
    sp.add_argument("file", help="Sticker file (webp/webm)")
    sp.add_argument("--emoji", default="\U0001f600")

    sp = sub.add_parser("remove-sticker", help="Remove sticker from set")
    sp.add_argument("short_name")
    sp.add_argument("index", type=int, help="Sticker index (0-based)")

    sp = sub.add_parser("fave-sticker", help="Add sticker to favorites")
    sp.add_argument("short_name")
    sp.add_argument("index", type=int)
    sp.add_argument("--unfave", action="store_true")

    sp = sub.add_parser("save-gif", help="Save GIF from message")
    sp.add_argument("chat")
    sp.add_argument("msg_id", type=int)
    sp.add_argument("--unsave", action="store_true")

    sp = sub.add_parser("kill-session", help="Terminate a session")
    sp.add_argument("session_hash", help="Session hash from 'sessions' command")

    sp = sub.add_parser("kill-web-session", help="Terminate a web session")
    sp.add_argument("session_hash")

    sp = sub.add_parser("import-contacts", help="Import contacts from CSV")
    sp.add_argument("file", help="CSV file: phone,first_name,last_name")

    sp = sub.add_parser("contact-statuses", help="Online statuses of contacts")

    sp = sub.add_parser("user-photos", help="All profile photos of a user")
    sp.add_argument("target")
    sp.add_argument("--limit", "-n", type=int, default=20)

    sp = sub.add_parser("pinned-stories", help="Pinned stories")
    sp.add_argument("target", nargs="?")
    sp.add_argument("--limit", "-n", type=int, default=20)

    sp = sub.add_parser("check-gift-code", help="Check a gift code")
    sp.add_argument("code")

    sp = sub.add_parser("apply-gift-code", help="Redeem a gift code")
    sp.add_argument("code")

    sp = sub.add_parser("toggle-antispam", help="Toggle anti-spam")
    sp.add_argument("channel")
    sp.add_argument("--disable", action="store_true")

    sp = sub.add_parser("leave-folder", help="Leave shared folder")
    sp.add_argument("folder_id", type=int)

    # --- Forum ---
    sp = sub.add_parser("get-forum-topics", help="List forum topics")
    sp.add_argument("channel")
    sp.add_argument("--limit", "-n", type=int, default=50)
    sp.add_argument("--query", "-q", default="", help="Search query")

    sp = sub.add_parser("edit-forum-topic", help="Edit forum topic")
    sp.add_argument("channel")
    sp.add_argument("topic_id", type=int)
    sp.add_argument("--title", help="New title")
    sp.add_argument("--icon", help="Icon emoji document ID")

    sp = sub.add_parser("close-forum-topic", help="Close/reopen forum topic")
    sp.add_argument("channel")
    sp.add_argument("topic_id", type=int)
    sp.add_argument("--reopen", action="store_true")

    sp = sub.add_parser("delete-topic", help="Delete forum topic")
    sp.add_argument("channel")
    sp.add_argument("topic_id", type=int)

    # --- Messages (album, stories, gifs) ---
    sp = sub.add_parser("send-album", help="Send album (multiple photos/videos)")
    sp.add_argument("chat")
    sp.add_argument("files", nargs="+", help="Photo/video files")
    sp.add_argument("--caption", "-c", default="")

    sp = sub.add_parser("delete-story", help="Delete stories")
    sp.add_argument("ids", help="Comma-separated story IDs")
    sp.add_argument("target", nargs="?", help="Story owner")

    sp = sub.add_parser("get-saved-gifs", help="List saved GIFs")
    sp.add_argument("--limit", "-n", type=int, default=20)

    # --- Account ---
    sp = sub.add_parser("set-2fa", help="Set 2FA password")
    sp.add_argument("password", help="New password")
    sp.add_argument("--hint", default="", help="Password hint")
    sp.add_argument("--current", help="Current password (if changing)")

    sp = sub.add_parser("remove-2fa", help="Remove 2FA password")
    sp.add_argument("current", help="Current password")

    sp = sub.add_parser("set-username", help="Set/change username")
    sp.add_argument("username")

    # --- Channels (send-as, join-to-send, history, left) ---
    sp = sub.add_parser("get-send-as", help="Get send-as options")
    sp.add_argument("channel")

    sp = sub.add_parser("toggle-join-to-send", help="Toggle join-to-send")
    sp.add_argument("channel")
    sp.add_argument("--disable", action="store_true")

    sp = sub.add_parser("toggle-history-hidden", help="Toggle history for new members")
    sp.add_argument("channel")
    sp.add_argument("--show", action="store_true", help="Show history (default=hide)")

    sp = sub.add_parser("get-left-channels", help="List left channels")

    # --- Stickers (move, thumb) ---
    sp = sub.add_parser("move-sticker", help="Move sticker position")
    sp.add_argument("short_name")
    sp.add_argument("index", type=int, help="Current index")
    sp.add_argument("position", type=int, help="New position")

    sp = sub.add_parser("set-sticker-thumb", help="Set sticker set thumbnail")
    sp.add_argument("short_name")
    sp.add_argument("file", help="Thumbnail file (webp)")

    # --- Gifts ---
    sp = sub.add_parser("transfer-gift", help="Transfer star gift")
    sp.add_argument("target", help="@username")
    sp.add_argument("msg_id", type=int, help="Gift message ID")

    sp = sub.add_parser("upgrade-gift", help="Upgrade star gift")
    sp.add_argument("msg_id", type=int)
    sp.add_argument("--keep", action="store_true", help="Keep original details")

    # Final 12 commands
    sp = sub.add_parser("set-chat-theme", help="Set theme for specific chat")
    sp.add_argument("chat")
    sp.add_argument("theme", nargs="?", default="", help="Theme emoticon (empty=clear)")

    sp = sub.add_parser("send-paid-media", help="Send paid media (stars)")
    sp.add_argument("chat")
    sp.add_argument("file", help="Media file")
    sp.add_argument("--stars", type=int, required=True, help="Stars price")
    sp.add_argument("--caption", "-c", default="")

    sp = sub.add_parser("report-message", help="Report specific messages")
    sp.add_argument("chat")
    sp.add_argument("ids", help="Comma-separated message IDs")
    sp.add_argument("reason", help="spam|violence|porn|copyright|other")
    sp.add_argument("--message", "-m", default="")

    sp = sub.add_parser("rename-sticker-set", help="Rename sticker set")
    sp.add_argument("short_name")
    sp.add_argument("title", help="New title")

    sp = sub.add_parser("delete-sticker-set", help="Delete entire sticker set")
    sp.add_argument("short_name")

    sp = sub.add_parser("set-bot-info", help="Set bot info (owner only)")
    sp.add_argument("bot", help="@botusername")
    sp.add_argument("--name", help="Bot display name")
    sp.add_argument("--about", help="Short bio")
    sp.add_argument("--description", help="Full description")
    sp.add_argument("--lang", default="")

    sp = sub.add_parser("set-bot-commands", help="Set bot commands (JSON)")
    sp.add_argument("commands", help='JSON: [{"command":"start","description":"Begin"}]')
    sp.add_argument("--lang", default="")

    sp = sub.add_parser("reset-bot-commands", help="Reset bot commands")
    sp.add_argument("--lang", default="")

    sp = sub.add_parser("set-notify-settings", help="Set notification settings")
    sp.add_argument("target", help="users|groups|channels or @chat")
    sp.add_argument("--mute", action="store_true")
    sp.add_argument("--unmute", action="store_true")
    sp.add_argument("--silent", action="store_true")
    sp.add_argument("--no-preview", action="store_true")

    sp = sub.add_parser("stars-subscriptions", help="List Stars subscriptions")

    sp = sub.add_parser("get-recent-stickers", help="Recently used stickers")
    sp.add_argument("--limit", "-n", type=int, default=20)

    sp = sub.add_parser("get-recent-locations", help="Recent live locations")
    sp.add_argument("chat")
    sp.add_argument("--limit", "-n", type=int, default=20)

    # --- Niche: Link Preview, Screenshot, Auto-Download, Gift Craft/Auction ---
    sp = sub.add_parser("get-web-page-preview", help="Preview URL — title, description, embed")
    sp.add_argument("url", help="URL to preview")

    sp = sub.add_parser("send-screenshot-notification", help="Notify peer you took a screenshot")
    sp.add_argument("chat")
    sp.add_argument("--msg-id", default=None, help="Reply-to message ID (optional)")

    sp = sub.add_parser("get-auto-download-settings", help="Show auto-download settings")

    sp = sub.add_parser("save-auto-download-settings", help="Update auto-download tier settings")
    sp.add_argument("tier", choices=["low", "high"], help="Which tier to update")
    sp.add_argument("--photo-max", help="Max photo size bytes (default 1MB)")
    sp.add_argument("--video-max", help="Max video size bytes (default 15MB)")
    sp.add_argument("--file-max", help="Max file size bytes (default 3MB)")
    sp.add_argument("--disabled", action="store_true", help="Disable auto-download for this tier")

    sp = sub.add_parser("upgrade-star-gift", help="Upgrade star gift to unique (costs Stars)")
    sp.add_argument("--msg-id", help="Message ID of the received gift")
    sp.add_argument("--gift-id", help="Gift ID (for --preview)")
    sp.add_argument("--keep-details", action="store_true", help="Keep original sender details")
    sp.add_argument("--preview", action="store_true", help="Preview upgrade attributes")

    sp = sub.add_parser("get-unique-star-gift", help="Get unique star gift info by slug")
    sp.add_argument("slug", help="Unique gift slug")

    sp = sub.add_parser("get-saved-star-gifts", help="List saved star gifts")
    sp.add_argument("--peer", default=None, help="Peer (default=self)")
    sp.add_argument("--limit", "-n", type=int, default=20)
    sp.add_argument("--offset", default="")
    sp.add_argument("--exclude-unsaved", action="store_true")
    sp.add_argument("--sort-by-value", action="store_true")

    sp = sub.add_parser("gift-withdrawal-url", help="Get TON withdrawal URL for unique gift (2FA)")
    sp.add_argument("msg_id", help="Message ID of the gift")
    sp.add_argument("password", help="2FA password")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    api_id, api_hash = get_api_credentials()
    client = TelegramClient(SESSION_PATH, api_id, api_hash)
    await client.connect()

    if not await client.is_user_authorized():
        print("ERROR: Session not authorized. Run telegram_auth.py first.")
        await client.disconnect()
        sys.exit(1)

    commands = {
        # Read
        "dialogs": cmd_dialogs,
        "read-chat": cmd_read_chat,
        "read-channel": cmd_read_channel,
        # Search
        "search": cmd_search,
        "mentions": cmd_mentions,
        # Parse people
        "parse-comments": cmd_parse_comments,
        "parse-commenters": cmd_parse_commenters,
        "participants": cmd_participants,
        "user-messages": cmd_user_messages,
        # Info
        "contacts": cmd_contacts,
        "folders": cmd_folders,
        "folder-chats": cmd_folder_chats,
        "user-info": cmd_user_info,
        "channel-stats": cmd_channel_stats,
        # Download
        "download": cmd_download,
        "download-photo": cmd_download_photo,
        # Export & Admin
        "export-chat": cmd_export_chat,
        "pinned": cmd_pinned,
        "admin-log": cmd_admin_log,
        "drafts": cmd_drafts,
        # Messaging
        "send": cmd_send,
        "send-file": cmd_send_file,
        "forward": cmd_forward,
        "reply": cmd_reply,
        "edit": cmd_edit,
        "delete": cmd_delete,
        "react": cmd_react,
        "schedule": cmd_schedule,
        "create-poll": cmd_create_poll,
        "broadcast": cmd_broadcast,
        # Group management
        "pin": cmd_pin,
        "unpin": cmd_unpin,
        "invite": cmd_invite,
        "kick": cmd_kick,
        "ban": cmd_ban,
        "unban": cmd_unban,
        "create-group": cmd_create_group,
        "create-channel": cmd_create_channel,
        "edit-chat": cmd_edit_chat,
        # Account
        "join": cmd_join,
        "leave": cmd_leave,
        "mark-read": cmd_mark_read,
        "archive": cmd_archive,
        "unarchive": cmd_unarchive,
        "mute": cmd_mute,
        "unmute": cmd_unmute,
        "block": cmd_block,
        "unblock": cmd_unblock,
        "set-bio": cmd_set_bio,
        "set-name": cmd_set_name,
        "set-photo": cmd_set_photo,
        # Advanced search / info
        "search-media": cmd_search_media,
        "search-date": cmd_search_date,
        "links": cmd_links,
        "hashtags": cmd_hashtags,
        "common-groups": cmd_common_groups,
        "similar-channels": cmd_similar_channels,
        "stories": cmd_stories,
        "saved": cmd_saved,
        "blocked-list": cmd_blocked_list,
        "unread": cmd_unread,
        "poll-results": cmd_poll_results,
        # Stars & Gifts
        "star-gifts": cmd_star_gifts,
        "send-star-gift": cmd_send_star_gift,
        # Stories (extended)
        "post-story": cmd_post_story,
        "story-views": cmd_story_views,
        "story-albums": cmd_story_albums,
        # Premium
        "boost-channel": cmd_boost,
        # Stories extended
        "edit-story": cmd_edit_story,
        "pin-story": cmd_pin_story,
        "story-reactions": cmd_story_reactions,
        "react-story": cmd_react_story,
        "stealth-mode": cmd_stealth_mode,
        "story-archive": cmd_story_archive,
        "export-story-link": cmd_export_story_link,
        # Stars / Payments
        "stars-balance": cmd_stars_balance,
        "stars-history": cmd_stars_history,
        "saved-gifts": cmd_saved_gifts,
        "convert-gift": cmd_convert_gift,
        "gift-premium": cmd_gift_premium,
        "giveaway-info": cmd_giveaway_info,
        # Business
        "set-business-hours": cmd_set_business_hours,
        "set-business-location": cmd_set_business_location,
        "set-business-greeting": cmd_set_business_greeting,
        "set-business-away": cmd_set_business_away,
        "business-links": cmd_business_links,
        # Account extended
        "set-birthday": cmd_set_birthday,
        "set-emoji-status": cmd_set_emoji_status,
        "close-friends": cmd_close_friends,
        "online-count": cmd_online_count,
        "contact-birthdays": cmd_contact_birthdays,
        "resolve-phone": cmd_resolve_phone,
        # Channels extended
        "toggle-forum": cmd_toggle_forum,
        "export-msg-link": cmd_export_msg_link,
        "set-channel-emoji": cmd_set_channel_emoji,
        "toggle-signatures": cmd_toggle_signatures,
        # Messages extras
        "translate-msg": cmd_translate_msg,
        "transcribe-voice": cmd_transcribe_voice,
        # AI
        "ai-compose": cmd_ai_compose,
        "ai-proofread": cmd_ai_proofread,
        "ai-emojify": cmd_ai_emojify,
        "ai-translate": cmd_ai_translate,
        "ai-change-tone": cmd_ai_change_tone,
        # Chat management
        "set-auto-delete": cmd_set_auto_delete,
        "create-topic": cmd_create_topic,
        "chat-themes": cmd_chat_themes,
        "toggle-sponsored": cmd_toggle_sponsored,
        # Account/Profile extended
        "set-personal-channel": cmd_set_personal_channel,
        "set-color": cmd_set_color,
        "paid-msg-revenue": cmd_paid_msg_revenue,
        "saved-music": cmd_saved_music,
        "set-wallpaper": cmd_set_wallpaper,
        # Stickers & Emoji
        "my-stickers": cmd_my_stickers,
        "emoji-packs": cmd_emoji_packs,
        "featured-stickers": cmd_featured_stickers,
        "install-stickers": cmd_install_stickers,
        "uninstall-stickers": cmd_uninstall_stickers,
        # Privacy
        "get-privacy": cmd_get_privacy,
        "set-privacy": cmd_set_privacy,
        "sessions": cmd_sessions,
        # Misc
        "nearby": cmd_nearby,
        "report": cmd_report,
        "add-contact": cmd_add_contact,
        "delete-contact": cmd_delete_contact,
        # Account / Settings (batch 5)
        "ringtones": cmd_ringtones,
        "global-privacy": cmd_global_privacy,
        "reorder-usernames": cmd_reorder_usernames,
        "connected-bots": cmd_connected_bots,
        "web-sessions": cmd_web_sessions,
        "account-ttl": cmd_account_ttl,
        "content-settings": cmd_content_settings,
        "contact-photo": cmd_contact_photo,
        "collectible-emoji": cmd_collectible_emoji,
        "notify-settings": cmd_notify_settings,
        "auto-save": cmd_auto_save,
        "live-story": cmd_live_story,
        # Bot Management (batch 5)
        "bot-info": cmd_bot_info,
        "bot-commands": cmd_bot_commands,
        "admined-bots": cmd_admined_bots,
        "popular-bots": cmd_popular_bots,
        "bot-recommendations": cmd_bot_recommendations,
        "shared-folders": cmd_shared_folders,
        "top-peers": cmd_top_peers,
        "search-global": cmd_search_global,
        "get-replies": cmd_get_replies,
        "export-folder-invite": cmd_export_folder_invite,
        "join-folder": cmd_join_folder,
        "check-username": cmd_check_username,
        "update-status": cmd_update_status,
        "password-status": cmd_password_status,
        "delete-messages": cmd_delete_messages,
        "clear-history": cmd_clear_history,
        "read-history": cmd_read_history,
        "send-typing": cmd_send_typing,
        "export-contact-token": cmd_export_contact_token,
        "import-contact-token": cmd_import_contact_token,
        # Final batch
        "create-sticker-set": cmd_create_sticker_set,
        "change-phone": cmd_change_phone,
        "takeout": cmd_takeout,
        "mark-unread": cmd_mark_unread,
        "scheduled-messages": cmd_scheduled_messages,
        "delete-scheduled": cmd_delete_scheduled,
        "report-spam": cmd_report_spam,
        "toggle-join-request": cmd_toggle_join_request,
        "set-discussion": cmd_set_discussion,
        "toggle-slow-mode": cmd_toggle_slow_mode,
        "set-chat-photo": cmd_set_chat_photo,
        "get-invite-link": cmd_get_invite_link,
        # Last batch (25)
        "vote": cmd_vote,
        "msg-readers": cmd_msg_readers,
        "msg-views": cmd_msg_views,
        "unread-mentions": cmd_unread_mentions,
        "read-mentions": cmd_read_mentions,
        "unread-reactions": cmd_unread_reactions,
        "read-reactions": cmd_read_reactions,
        "edit-admin": cmd_edit_admin,
        "edit-channel-title": cmd_edit_channel_title,
        "edit-channel-about": cmd_edit_channel_about,
        "get-sticker-set": cmd_get_sticker_set,
        "add-sticker": cmd_add_sticker,
        "remove-sticker": cmd_remove_sticker,
        "fave-sticker": cmd_fave_sticker,
        "save-gif": cmd_save_gif,
        "kill-session": cmd_kill_session,
        "kill-web-session": cmd_kill_web_session,
        "import-contacts": cmd_import_contacts,
        "contact-statuses": cmd_contact_statuses,
        "user-photos": cmd_user_photos,
        "pinned-stories": cmd_pinned_stories,
        "check-gift-code": cmd_check_gift_code,
        "apply-gift-code": cmd_apply_gift_code,
        "toggle-antispam": cmd_toggle_antispam,
        "leave-folder": cmd_leave_folder,
        # Forum
        "get-forum-topics": cmd_get_forum_topics,
        "edit-forum-topic": cmd_edit_forum_topic,
        "close-forum-topic": cmd_close_forum_topic,
        "delete-topic": cmd_delete_topic,
        # Messages (album, stories, gifs)
        "send-album": cmd_send_album,
        "delete-story": cmd_delete_story,
        "get-saved-gifs": cmd_get_saved_gifs,
        # Account
        "set-2fa": cmd_set_2fa,
        "remove-2fa": cmd_remove_2fa,
        "set-username": cmd_set_username,
        # Channels
        "get-send-as": cmd_get_send_as,
        "toggle-join-to-send": cmd_toggle_join_to_send,
        "toggle-history-hidden": cmd_toggle_history_hidden,
        "get-left-channels": cmd_get_left_channels,
        # Stickers
        "move-sticker": cmd_move_sticker,
        "set-sticker-thumb": cmd_set_sticker_thumb,
        # Gifts
        "transfer-gift": cmd_transfer_gift,
        "upgrade-gift": cmd_upgrade_gift,
        # Final 12
        "set-chat-theme": cmd_set_chat_theme,
        "send-paid-media": cmd_send_paid_media,
        "report-message": cmd_report_message,
        "rename-sticker-set": cmd_rename_sticker_set,
        "delete-sticker-set": cmd_delete_sticker_set,
        "set-bot-info": cmd_set_bot_info,
        "set-bot-commands": cmd_set_bot_commands_custom,
        "reset-bot-commands": cmd_reset_bot_commands,
        "set-notify-settings": cmd_set_notify_settings,
        "stars-subscriptions": cmd_stars_subscriptions,
        "get-recent-stickers": cmd_get_recent_stickers,
        "get-recent-locations": cmd_get_recent_locations,
        # Niche: link preview, screenshot, auto-download, gift craft/auction
        "get-web-page-preview": cmd_get_web_page_preview,
        "send-screenshot-notification": cmd_send_screenshot_notification,
        "get-auto-download-settings": cmd_get_auto_download_settings,
        "save-auto-download-settings": cmd_save_auto_download_settings,
        "upgrade-star-gift": cmd_upgrade_star_gift,
        "get-unique-star-gift": cmd_get_unique_star_gift,
        "get-saved-star-gifts": cmd_get_saved_star_gifts,
        "gift-withdrawal-url": cmd_gift_withdrawal_url,
    }

    try:
        await commands[args.command](client, args)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
