"""
MAX Messenger CLI for Claude Code.
Full-featured client for reading, sending, and managing MAX chats.

Session: ~/.claude/max_session.db
Credentials: ~/.claude/.credentials.master.env (MAX_PHONE)
Protocol: WebSocket JSON (WEB mode), wss://ws-api.oneme.ru/websocket

Usage:
    python max_client.py dialogs
    python max_client.py send <chat_id> "Hello!"
    python max_client.py read-chat <chat_id>
    python max_client.py listen --chat <chat_id>
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

# Add tools dir to path for max_core import
sys.path.insert(0, str(Path(__file__).parent))


def load_env() -> None:
    env_path = Path.home() / ".claude" / ".credentials.master.env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                key, value = key.strip(), value.strip()
                if key and not os.environ.get(key):
                    os.environ[key] = value


load_env()

MAX_PHONE = os.environ.get("MAX_PHONE", "")

from max_core import MaxClient, MaxError
from max_core.methods import messages as msg_api
from max_core.methods import chats as chat_api
from max_core.methods import channels as ch_api
from max_core.methods import groups as grp_api
from max_core.methods import users as usr_api
from max_core.methods import profile as prof_api
from max_core.methods import uploads as up_api


# ─────────────────────────── Formatting ───────────────────────────────

def fmt_ts(ms: int) -> str:
    if not ms:
        return ""
    try:
        return datetime.fromtimestamp(ms / 1000).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(ms)


def fmt_user(u) -> str:
    if not u:
        return "(unknown)"
    return f"{u.display_name} (id={u.id})"


def print_messages(msgs, label: str = "") -> None:
    if label:
        print(f"\n── {label} ──")
    for m in msgs:
        ts = fmt_ts(m.time)
        reply = f" ↩{m.reply_to}" if m.reply_to else ""
        print(f"[{ts}] id={m.id} from={m.sender_id}{reply}")
        print(f"  {m.text or '(no text)'}")


def print_chats(chats) -> None:
    for c in chats:
        unread = f" [{c.unread_count} unread]" if c.unread_count else ""
        muted = " [muted]" if c.muted else ""
        print(f"  {c.id:>15}  {c.type:<10}  {c.name or '(private)'}{unread}{muted}")


# ─────────────────────────── Client factory ───────────────────────────

def get_phone(args) -> str:
    phone = getattr(args, "phone", None) or MAX_PHONE
    if not phone:
        print("ERROR: Set MAX_PHONE in ~/.claude/.credentials.master.env or pass --phone")
        sys.exit(1)
    return phone


async def make_client(args) -> MaxClient:
    phone = get_phone(args)
    client = MaxClient(phone=phone)
    await client.connect()
    await client.authorize()
    return client


# ─────────────────────────── Commands ─────────────────────────────────

async def cmd_dialogs(client: MaxClient, args) -> None:
    """List all chats from session cache."""
    chats = chat_api.get_cached_chats(client)
    if not chats:
        print("No chats cached. Try re-authorizing.")
        return
    print(f"{'ID':>15}  {'Type':<10}  Name")
    print("-" * 60)
    print_chats(chats)
    print(f"\nTotal: {len(chats)} chats")


async def cmd_read_chat(client: MaxClient, args) -> None:
    """Read messages from a chat."""
    chat_id = int(args.target)
    limit = getattr(args, "limit", 30)
    msgs = await chat_api.get_chat_messages(client, chat_id, limit=limit)
    print_messages(msgs, label=f"chat_id={chat_id}")
    print(f"\n{len(msgs)} messages")


async def cmd_chat_info(client: MaxClient, args) -> None:
    """Get chat info."""
    chat_id = int(args.target)
    chat = await chat_api.get_chat(client, chat_id)
    print(f"ID:      {chat.id}")
    print(f"Type:    {chat.type}")
    print(f"Name:    {chat.name}")
    print(f"Members: {chat.members_count}")
    print(f"Unread:  {chat.unread_count}")
    print(f"Muted:   {chat.muted}")


async def cmd_send(client: MaxClient, args) -> None:
    """Send a text message."""
    chat_id = int(args.target)
    text = " ".join(args.text)
    m = await msg_api.send_message(client, chat_id, text)
    print(f"Sent: id={m.id}")


async def cmd_reply(client: MaxClient, args) -> None:
    """Reply to a message."""
    chat_id = int(args.chat)
    reply_to = str(args.msg_id)
    text = " ".join(args.text)
    m = await msg_api.send_message(client, chat_id, text, reply_to=reply_to)
    print(f"Replied: id={m.id}")


async def cmd_edit(client: MaxClient, args) -> None:
    """Edit a message."""
    await msg_api.edit_message(client, int(args.chat), str(args.msg_id), " ".join(args.text))
    print("Edited.")


async def cmd_delete(client: MaxClient, args) -> None:
    """Delete messages."""
    chat_id = int(args.chat)
    ids = [str(i) for i in args.msg_ids]
    for_me = getattr(args, "for_me", False)
    await msg_api.delete_message(client, chat_id, ids, for_me=for_me)
    print(f"Deleted {len(ids)} message(s).")


async def cmd_pin(client: MaxClient, args) -> None:
    """Pin a message."""
    await msg_api.pin_message(client, int(args.chat), str(args.msg_id))
    print("Pinned.")


async def cmd_react(client: MaxClient, args) -> None:
    """Add reaction to a message."""
    await msg_api.add_reaction(client, int(args.chat), str(args.msg_id), args.emoji)
    print(f"Reacted with {args.emoji}")


async def cmd_send_file(client: MaxClient, args) -> None:
    """Send a file (photo or document)."""
    chat_id = int(args.target)
    path = args.file
    ext = Path(path).suffix.lower()
    if ext in (".jpg", ".jpeg", ".png", ".webp"):
        m = await up_api.upload_photo(client, chat_id, path)
    else:
        caption = getattr(args, "caption", "") or ""
        m = await up_api.upload_file(client, chat_id, path, caption=caption)
    print(f"Sent file: id={m.id}")


async def cmd_broadcast(client: MaxClient, args) -> None:
    """Send a message to multiple chats."""
    text = " ".join(args.text)
    targets = [int(t) for t in args.targets]
    delay = getattr(args, "delay", 2)
    results = []
    for chat_id in targets:
        try:
            m = await msg_api.send_message(client, chat_id, text)
            results.append(f"✓ {chat_id}: id={m.id}")
        except Exception as e:
            results.append(f"✗ {chat_id}: {e}")
        await asyncio.sleep(delay)
    for r in results:
        print(r)


async def cmd_mark_read(client: MaxClient, args) -> None:
    """Mark chat as read."""
    chat_id = int(args.target)
    # Get last message id first
    msgs = await chat_api.get_chat_messages(client, chat_id, limit=1)
    if msgs:
        await chat_api.mark_read(client, chat_id, msgs[0].id)
        print(f"Marked read up to msg {msgs[0].id}")
    else:
        print("No messages found.")


async def cmd_mark_unread(client: MaxClient, args) -> None:
    """Mark chat as unread."""
    await chat_api.mark_unread(client, int(args.target))
    print("Marked unread.")


async def cmd_mute(client: MaxClient, args) -> None:
    """Mute a chat."""
    await chat_api.mute_chat(client, int(args.target), mute=True)
    print("Muted.")


async def cmd_unmute(client: MaxClient, args) -> None:
    """Unmute a chat."""
    await chat_api.mute_chat(client, int(args.target), mute=False)
    print("Unmuted.")


async def cmd_join(client: MaxClient, args) -> None:
    """Join a channel by @username."""
    await chat_api.join_chat(client, link=args.target)
    print(f"Joined {args.target}")


async def cmd_leave(client: MaxClient, args) -> None:
    """Leave a chat/channel/group."""
    await chat_api.leave_chat(client, int(args.target))
    print("Left.")


async def cmd_members(client: MaxClient, args) -> None:
    """Get members of a group or channel."""
    chat_id = int(args.target)
    count = getattr(args, "count", 500)
    members = await chat_api.get_chat_members(client, chat_id, count=count)
    for m in members:
        print(f"  {m.get('userId', '?'):>12}  {m.get('role', 'MEMBER'):<10}  {m.get('firstName','')} {m.get('lastName','')}")
    print(f"\nTotal: {len(members)}")


async def cmd_create_group(client: MaxClient, args) -> None:
    """Create a new group."""
    ids = [int(i) for i in args.user_ids]
    result = await grp_api.create_group(client, args.name, ids)
    print(f"Group created: {json.dumps(result.get('payload', {}), ensure_ascii=False)}")


async def cmd_create_channel(client: MaxClient, args) -> None:
    """Create a new channel."""
    result = await ch_api.create_channel(client, args.name)
    print(f"Channel created: {json.dumps(result.get('payload', {}), ensure_ascii=False)}")


async def cmd_invite(client: MaxClient, args) -> None:
    """Invite users to a group."""
    group_id = int(args.group)
    user_ids = [int(i) for i in args.user_ids]
    await grp_api.invite_users(client, group_id, user_ids)
    print(f"Invited {len(user_ids)} user(s).")


async def cmd_kick(client: MaxClient, args) -> None:
    """Remove users from a group."""
    group_id = int(args.group)
    user_ids = [int(i) for i in args.user_ids]
    await grp_api.remove_users(client, group_id, user_ids)
    print(f"Removed {len(user_ids)} user(s).")


async def cmd_user_info(client: MaxClient, args) -> None:
    """Get info about a user."""
    user_id = int(args.user)
    u = await usr_api.get_user(client, user_id)
    if not u:
        print("User not found.")
        return
    print(f"ID:        {u.id}")
    print(f"Name:      {u.display_name}")
    print(f"Phone:     {u.phone}")
    print(f"Username:  {u.username}")
    print(f"Bio:       {u.about}")
    print(f"Bot:       {u.is_bot}")


async def cmd_search_phone(client: MaxClient, args) -> None:
    """Search user by phone number."""
    u = await usr_api.search_by_phone(client, args.phone)
    if not u:
        print("Not found.")
    else:
        print(fmt_user(u))


async def cmd_block(client: MaxClient, args) -> None:
    """Block a user."""
    await usr_api.block_user(client, int(args.user))
    print("Blocked.")


async def cmd_unblock(client: MaxClient, args) -> None:
    """Unblock a user."""
    await usr_api.unblock_user(client, int(args.user))
    print("Unblocked.")


async def cmd_add_contact(client: MaxClient, args) -> None:
    """Add user to contacts."""
    await usr_api.add_contact(client, int(args.user))
    print("Added to contacts.")


async def cmd_set_bio(client: MaxClient, args) -> None:
    """Update profile bio."""
    await prof_api.change_profile(client, bio=" ".join(args.text))
    print("Bio updated.")


async def cmd_set_name(client: MaxClient, args) -> None:
    """Update profile name."""
    await prof_api.change_profile(client, first_name=args.first, last_name=args.last or "")
    print("Name updated.")


async def cmd_online_status(client: MaxClient, args) -> None:
    """Check online status of a user."""
    user_id = int(args.user)
    result = await client.invoke(35, {"contactIds": [user_id]})
    presence = result.get("payload", {}).get("presence", {})
    for uid, info in presence.items():
        seen = info.get("seen", 0)
        if seen:
            from datetime import datetime
            dt = datetime.fromtimestamp(seen)
            print(f"User {uid}: last seen {dt.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print(f"User {uid}: online now or hidden")


async def cmd_public_search(client: MaxClient, args) -> None:
    """Search public channels and groups."""
    query = " ".join(args.query)
    count = getattr(args, "count", 10)
    result = await client.invoke(60, {"query": query, "count": count})
    items = result.get("payload", {}).get("result", [])
    print(f"{'ID':>20}  {'Members':>8}  {'Type':<10}  Name")
    print("-" * 70)
    for item in items:
        chat = item.get("chat", {})
        cid = chat.get("id", chat.get("cid", ""))
        title = chat.get("title", "")
        members = chat.get("participantsCount", 0)
        ctype = chat.get("type", "")
        link = chat.get("link", "")
        print(f"  {cid:>20}  {members:>8}  {ctype:<10}  {title}")
        if link:
            print(f"{'':>20}  {'':>8}  {'':>10}  {link}")
    print(f"\n{len(items)} results for '{query}'")


async def cmd_global_search(client: MaxClient, args) -> None:
    """Search across all chats and public channels."""
    query = " ".join(args.query)
    count = getattr(args, "count", 10)
    result = await client.invoke(68, {"query": query, "count": count})
    items = result.get("payload", {}).get("result", [])
    for item in items:
        section = item.get("section", "")
        chat = item.get("chat", {})
        title = chat.get("title", chat.get("name", ""))
        cid = item.get("chatId", chat.get("id", ""))
        highlights = item.get("highlights", [])
        members = chat.get("participantsCount", 0)
        print(f"  [{section}] {title} (id={cid}, members={members})")
        if highlights:
            print(f"    highlights: {', '.join(highlights[:5])}")
    print(f"\n{len(items)} results for '{query}'")


async def cmd_chat_media(client: MaxClient, args) -> None:
    """Get media files from a chat (photos, videos, files)."""
    chat_id = int(args.target)
    media_type = getattr(args, "type", "PHOTO").upper()
    limit = getattr(args, "limit", 20)
    result = await client.invoke(51, {"chatId": chat_id, "type": media_type, "limit": limit})
    payload = result.get("payload", {})
    msgs = payload.get("messages", [])
    total = payload.get("total", 0)
    print(f"Media type={media_type}, total={total}, fetched={len(msgs)}")
    for m in msgs:
        ts = fmt_ts(m.get("time", 0))
        text = m.get("text", "")[:60]
        attaches = m.get("attaches", [])
        print(f"  [{ts}] {text} ({len(attaches)} attachments)")


async def cmd_mentions(client: MaxClient, args) -> None:
    """Get last mentions (@you) across chats."""
    chat_id = getattr(args, "chat", None)
    payload = {"messageId": "0", "limit": getattr(args, "limit", 20)}
    if chat_id:
        payload["chatId"] = int(chat_id)
    result = await client.invoke(127, payload)
    mentions = result.get("payload", {}).get("mentions", [])
    if not mentions:
        print("No mentions found.")
        return
    for m in mentions:
        print(f"  chat={m.get('chatId')} msg={m.get('messageId')} from={m.get('userId')}")
    print(f"\n{len(mentions)} mentions")


async def cmd_set_photo(client: MaxClient, args) -> None:
    """Set profile photo from a file or preset avatar."""
    preset = getattr(args, "preset", None)
    if preset:
        # Use preset avatar
        result = await client.invoke(25, {})
        avatars = result.get("payload", {}).get("presetAvatars", [])
        all_avs = []
        for cat in avatars:
            for av in cat.get("avatars", []):
                all_avs.append(av)
        if preset == "list":
            for i, cat in enumerate(avatars):
                print(f"\n{cat.get('name', '?')}:")
                for av in cat.get("avatars", []):
                    print(f"  id={av['id']}  {av['url'][:60]}...")
            return
        # Find by id
        av = next((a for a in all_avs if str(a["id"]) == str(preset)), None)
        if not av:
            print(f"Avatar id={preset} not found. Use --preset list")
            return
        await client.invoke(22, {"avatarId": av["id"]})
        print(f"Set preset avatar id={av['id']}")
    else:
        # Upload from file
        file_path = args.file
        upload_result = await client.invoke(81, {})
        upload_url = upload_result.get("payload", {}).get("url", "")
        if not upload_url:
            print("Failed to get upload URL")
            return
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                with open(file_path, "rb") as f:
                    data = aiohttp.FormData()
                    data.add_field("file", f, filename=file_path)
                    await session.post(upload_url, data=data)
            print(f"Photo uploaded from {file_path}")
        except ImportError:
            print("aiohttp required: pip install aiohttp")


async def cmd_refresh_token(client: MaxClient, args) -> None:
    """Refresh and save auth token."""
    result = await client.invoke(97, {})
    token = result.get("payload", {}).get("token", "")
    if token:
        from max_core import session as sess
        sess.save_token(client.phone, token)
        print(f"Token refreshed: {token[:30]}...")
    else:
        print("No token in response")


async def cmd_pinned(client: MaxClient, args) -> None:
    """Get pinned messages in a chat."""
    msgs = await chat_api.get_pinned(client, int(args.target))
    print_messages(msgs, label="Pinned messages")


async def cmd_search(client: MaxClient, args) -> None:
    """Search messages in a chat by text."""
    chat_id = int(args.chat)
    query = " ".join(args.query)
    limit = getattr(args, "limit", 20)
    from max_core.protocol import Opcode
    result = await client.invoke(Opcode.CHAT_HISTORY, {
        "chatId": chat_id, "query": query, "limit": limit,
    })
    msgs = result.get("payload", {}).get("messages", [])
    from max_core.types import MaxMessage
    parsed = [MaxMessage.from_dict(m, chat_id=chat_id) for m in msgs]
    print_messages(parsed, label=f'Search "{query}" in chat {chat_id}')
    print(f"\n{len(parsed)} results")


async def cmd_typing(client: MaxClient, args) -> None:
    """Send typing indicator to a chat."""
    from max_core.protocol import Opcode
    await client.invoke(Opcode.CHAT_TYPING, {"chatId": int(args.target)})
    print("Typing indicator sent.")


async def cmd_archive(client: MaxClient, args) -> None:
    """Archive a chat."""
    from max_core.protocol import Opcode
    await client.invoke(Opcode.SETTINGS_UPDATE, {"chatId": int(args.target), "archived": True})
    print("Archived.")


async def cmd_unarchive(client: MaxClient, args) -> None:
    """Unarchive a chat."""
    from max_core.protocol import Opcode
    await client.invoke(Opcode.SETTINGS_UPDATE, {"chatId": int(args.target), "archived": False})
    print("Unarchived.")


async def cmd_folders(client: MaxClient, args) -> None:
    """List chat folders."""
    from max_core.protocol import Opcode
    result = await client.invoke(Opcode.FOLDERS_GET, {"limit": 50})
    payload = result.get("payload", {})
    folders = payload.get("folders", [])
    order = payload.get("foldersOrder", [])
    print(f"Folders ({len(folders)}):")
    for f in folders:
        fid = f.get("id", "")
        title = f.get("title", "")
        filters = f.get("filters", [])
        print(f"  {fid:<30}  {title}  filters={filters}")
    if order:
        print(f"\nOrder: {order}")


async def cmd_active_sessions(client: MaxClient, args) -> None:
    """List active devices/sessions."""
    result = await client.invoke(96, {})
    sessions = result.get("payload", {}).get("sessions", [])
    print(f"Active sessions ({len(sessions)}):")
    for s in sessions:
        current = " [CURRENT]" if s.get("current") else ""
        ts = fmt_ts(s.get("time", 0))
        print(f"  {s.get('client', '?'):<15}  {s.get('info', ''):<30}  {s.get('location', '')}{current}  {ts}")


async def cmd_export_chat(client: MaxClient, args) -> None:
    """Export full chat history to JSON file."""
    chat_id = int(args.target)
    output = getattr(args, "output", None) or f"max_export_{chat_id}.json"
    limit = getattr(args, "limit", 1000)

    all_msgs = []
    before_time = None
    from max_core.protocol import Opcode
    while len(all_msgs) < limit:
        batch = min(50, limit - len(all_msgs))
        payload = {"chatId": chat_id, "limit": batch}
        if before_time:
            payload["beforeTime"] = before_time
        result = await client.invoke(Opcode.CHAT_HISTORY, payload)
        msgs = result.get("payload", {}).get("messages", [])
        if not msgs:
            break
        all_msgs.extend(msgs)
        before_time = msgs[-1].get("time", 0)
        if len(msgs) < batch:
            break
        print(f"  fetched {len(all_msgs)}...")

    with open(output, "w", encoding="utf-8") as f:
        json.dump(all_msgs, f, ensure_ascii=False, indent=2)
    print(f"Exported {len(all_msgs)} messages to {output}")


async def cmd_user_messages(client: MaxClient, args) -> None:
    """Get messages from a specific user in a chat."""
    chat_id = int(args.chat)
    user_id = int(args.user)
    limit = getattr(args, "limit", 50)

    from max_core.protocol import Opcode
    result = await client.invoke(Opcode.CHAT_HISTORY, {"chatId": chat_id, "limit": limit})
    msgs = result.get("payload", {}).get("messages", [])
    filtered = [m for m in msgs if m.get("sender") == user_id or m.get("userId") == user_id]

    from max_core.types import MaxMessage
    parsed = [MaxMessage.from_dict(m, chat_id=chat_id) for m in filtered]
    print_messages(parsed, label=f"Messages from user {user_id} in chat {chat_id}")
    print(f"\n{len(parsed)} messages (from {len(msgs)} total)")


async def cmd_resolve_channel(client: MaxClient, args) -> None:
    """Resolve channel info by @username."""
    chat = await ch_api.resolve_by_username(client, args.username)
    print(f"ID:      {chat.id}")
    print(f"Name:    {chat.name}")
    print(f"Members: {chat.members_count}")
    print(f"Type:    {chat.type}")


async def cmd_parse_channel(client: MaxClient, args) -> None:
    """Parse all posts from a channel. Resolves by @username, fetches history."""
    username = args.target.lstrip("@")
    limit = getattr(args, "limit", 100)
    output = getattr(args, "output", None)

    chat = await ch_api.resolve_by_username(client, username)
    print(f"Channel: {chat.name} (id={chat.id}, members={chat.members_count})")

    # Need to join first to read history
    try:
        from max_core.protocol import Opcode
        await client.invoke(Opcode.CHAT_JOIN, {"chatId": chat.id})
    except MaxError:
        pass  # already joined or public

    all_msgs = []
    before_time = None
    while len(all_msgs) < limit:
        batch_size = min(50, limit - len(all_msgs))
        from max_core.protocol import Opcode
        payload = {"chatId": chat.id, "limit": batch_size}
        if before_time:
            payload["beforeTime"] = before_time
        result = await client.invoke(Opcode.CHAT_HISTORY, payload)
        msgs = result.get("payload", {}).get("messages", [])
        if not msgs:
            break
        all_msgs.extend(msgs)
        before_time = msgs[-1].get("time", 0)
        if len(msgs) < batch_size:
            break

    print(f"Fetched {len(all_msgs)} posts\n")

    rows = []
    for m in all_msgs:
        text = m.get("text", "")
        ts = fmt_ts(m.get("time", 0))
        msg_id = m.get("id", "")
        sender = m.get("sender", m.get("userId", 0))
        attaches = m.get("attaches", [])
        row = {
            "id": msg_id,
            "time": ts,
            "sender": sender,
            "text": text[:200],
            "attachments": len(attaches),
        }
        rows.append(row)
        print(f"[{ts}] id={msg_id} from={sender} attach={len(attaches)}")
        if text:
            print(f"  {text[:120]}")

    if output:
        with open(output, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)
        print(f"\nSaved to {output}")

    print(f"\nTotal: {len(all_msgs)} posts from @{username}")


async def cmd_parse_members(client: MaxClient, args) -> None:
    """Parse all members of a channel/group. Resolves by @username or chat_id."""
    target = args.target
    output = getattr(args, "output", None)

    # Resolve target
    if target.lstrip("@").isalpha() or not target.lstrip("-").isdigit():
        chat = await ch_api.resolve_by_username(client, target)
        chat_id = chat.id
        print(f"Channel: {chat.name} (id={chat_id}, members={chat.members_count})")
    else:
        chat_id = int(target)

    # Join first
    try:
        from max_core.protocol import Opcode
        await client.invoke(Opcode.CHAT_JOIN, {"chatId": chat_id})
    except MaxError:
        pass

    # Fetch members
    from max_core.protocol import Opcode
    all_members = []
    marker = None
    while True:
        payload = {"chatId": chat_id, "count": 500}
        if marker:
            payload["marker"] = marker
        result = await client.invoke(Opcode.CHAT_MEMBERS, payload)
        members = result.get("payload", {}).get("members", [])
        if not members:
            break
        all_members.extend(members)
        marker = result.get("payload", {}).get("marker")
        if not marker or len(members) < 500:
            break

    print(f"\n{'User ID':>12}  {'Role':<10}  Name")
    print("-" * 50)

    rows = []
    for m in all_members:
        uid = m.get("userId", 0)
        role = m.get("role", "MEMBER")
        fname = m.get("firstName", "")
        lname = m.get("lastName", "")
        nick = m.get("alias", m.get("nick", ""))
        name = f"{fname} {lname}".strip() or nick or str(uid)
        print(f"  {uid:>12}  {role:<10}  {name}")
        rows.append({"userId": uid, "role": role, "name": name, "nick": nick})

    if output:
        with open(output, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)
        print(f"\nSaved to {output}")

    print(f"\nTotal: {len(all_members)} members")


async def cmd_channel_stats(client: MaxClient, args) -> None:
    """Get channel stats: members count, last posts activity."""
    target = args.target
    if target.lstrip("@").isalpha() or not target.lstrip("-").isdigit():
        chat = await ch_api.resolve_by_username(client, target)
        chat_id = chat.id
    else:
        chat_id = int(target)
        chat = await ch_api.resolve_by_id(client, chat_id)

    print(f"Channel:  {chat.name}")
    print(f"ID:       {chat.id}")
    print(f"Members:  {chat.members_count}")
    print(f"Type:     {chat.type}")

    # Fetch recent posts for activity stats
    from max_core.protocol import Opcode
    try:
        await client.invoke(Opcode.CHAT_JOIN, {"chatId": chat_id})
    except MaxError:
        pass

    result = await client.invoke(Opcode.CHAT_HISTORY, {"chatId": chat_id, "limit": 50})
    msgs = result.get("payload", {}).get("messages", [])

    if msgs:
        first_ts = msgs[-1].get("time", 0)
        last_ts = msgs[0].get("time", 0)
        print(f"\nLast 50 posts:")
        print(f"  Newest: {fmt_ts(last_ts)}")
        print(f"  Oldest: {fmt_ts(first_ts)}")
        if last_ts and first_ts and last_ts != first_ts:
            days = (last_ts - first_ts) / (1000 * 86400)
            if days > 0:
                print(f"  Frequency: {50 / days:.1f} posts/day")

        # Unique senders
        senders = set(m.get("sender", m.get("userId", 0)) for m in msgs)
        print(f"  Unique authors: {len(senders)}")

        # Attachments stats
        with_attach = sum(1 for m in msgs if m.get("attaches"))
        print(f"  With attachments: {with_attach}/{len(msgs)}")
    else:
        print("\nNo posts found (need to join first?)")


async def cmd_sessions(client: MaxClient, args) -> None:
    """List saved MAX sessions."""
    from max_core import session as sess
    sessions = sess.list_sessions()
    for s in sessions:
        status = "✓ active" if s["has_token"] else "✗ no token"
        print(f"  {s['phone']:<16}  {status}  updated={s['updated_at']}")


async def cmd_listen(client: MaxClient, args) -> None:
    """
    Listen for incoming messages (notification mode).
    Prints incoming messages. Use Ctrl+C to stop.
    Optional: --chat N  to filter by chat_id.
    Optional: --ai      to reply via AI Gateway.
    """
    filter_chat = getattr(args, "chat", None)
    use_ai = getattr(args, "ai", False)
    ai_model = getattr(args, "model", "claude-sonnet-4-5-20250929")

    print(f"Listening for messages{f' in chat {filter_chat}' if filter_chat else ''}...")
    print("Press Ctrl+C to stop.\n")

    async def handler(packet: dict) -> None:
        from max_core.protocol import Opcode as Op
        opcode = packet.get("opcode")
        payload = packet.get("payload", {})

        if opcode == Op.NOTIF_MESSAGE:
            chat_id = payload.get("chatId")
            if filter_chat and chat_id != int(filter_chat):
                return
            m_data = payload.get("message", {})
            text = m_data.get("text", "")
            sender = payload.get("userId", "?")
            msg_id = payload.get("msgId", "")
            ts = fmt_ts(payload.get("time", 0))
            print(f"[{ts}] chat={chat_id} from={sender}: {text}")

            if use_ai and text:
                await _ai_reply(client, chat_id, msg_id, text, model=ai_model)

        elif opcode == Op.NOTIF_TYPING:
            chat_id = payload.get("chatId")
            if not filter_chat or chat_id == int(filter_chat):
                print(f"  [typing] chat={chat_id} user={payload.get('userId')}")

    client._notification_handler = handler

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nStopped.")


async def _ai_reply(client: MaxClient, chat_id: int, msg_id: str, text: str, model: str) -> None:
    """Send message to AI Gateway and reply in chat."""
    try:
        ai_url = os.environ.get("AI_GATEWAY_URL", "http://YOUR_SERVER_IP:8001/v1")
        ai_key = os.environ.get("AI_GATEWAY_KEY", os.environ.get("ANTHROPIC_API_KEY", ""))

        import urllib.request
        req_body = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": text}],
            "max_tokens": 1024,
        }).encode()
        req = urllib.request.Request(
            f"{ai_url}/chat/completions",
            data=req_body,
            headers={"Authorization": f"Bearer {ai_key}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        reply_text = data["choices"][0]["message"]["content"]
        await msg_api.send_message(client, chat_id, reply_text, reply_to=str(msg_id))
        print(f"  → AI replied: {reply_text[:80]}...")
    except Exception as e:
        print(f"  AI reply failed: {e}")


# ─────────────────────────── Main ─────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="max_client",
        description="MAX Messenger CLI — аналог tg_client.py для MAX",
    )
    p.add_argument("--phone", default="", help="Phone number (overrides MAX_PHONE env)")
    sub = p.add_subparsers(dest="command", required=True)

    # ── Read ──
    d = sub.add_parser("dialogs", help="List all cached chats")

    rc = sub.add_parser("read-chat", help="Read messages from a chat")
    rc.add_argument("target", help="chat_id")
    rc.add_argument("--limit", type=int, default=30)

    ci = sub.add_parser("chat-info", help="Get chat info")
    ci.add_argument("target", help="chat_id")

    pm = sub.add_parser("pinned", help="Get pinned messages")
    pm.add_argument("target", help="chat_id")

    mb = sub.add_parser("members", help="Get chat members")
    mb.add_argument("target", help="chat_id")
    mb.add_argument("--count", type=int, default=500)

    # ── Send ──
    sn = sub.add_parser("send", help="Send a message")
    sn.add_argument("target", help="chat_id")
    sn.add_argument("text", nargs="+")

    rp = sub.add_parser("reply", help="Reply to a message")
    rp.add_argument("chat", help="chat_id")
    rp.add_argument("msg_id", help="Message ID to reply to")
    rp.add_argument("text", nargs="+")

    ed = sub.add_parser("edit", help="Edit a message")
    ed.add_argument("chat", help="chat_id")
    ed.add_argument("msg_id")
    ed.add_argument("text", nargs="+")

    dl = sub.add_parser("delete", help="Delete messages")
    dl.add_argument("chat", help="chat_id")
    dl.add_argument("msg_ids", nargs="+")
    dl.add_argument("--for-me", action="store_true")

    pn = sub.add_parser("pin", help="Pin a message")
    pn.add_argument("chat", help="chat_id")
    pn.add_argument("msg_id")

    rx = sub.add_parser("react", help="Add reaction")
    rx.add_argument("chat", help="chat_id")
    rx.add_argument("msg_id")
    rx.add_argument("emoji")

    sf = sub.add_parser("send-file", help="Send a file or photo")
    sf.add_argument("target", help="chat_id")
    sf.add_argument("file", help="Path to file")
    sf.add_argument("--caption", default="")

    bc = sub.add_parser("broadcast", help="Send to multiple chats")
    bc.add_argument("text", nargs="+")
    bc.add_argument("--targets", nargs="+", required=True, help="chat_ids")
    bc.add_argument("--delay", type=float, default=2.0)

    # ── Chat management ──
    mr = sub.add_parser("mark-read", help="Mark chat as read")
    mr.add_argument("target", help="chat_id")

    mu = sub.add_parser("mark-unread", help="Mark chat as unread")
    mu.add_argument("target", help="chat_id")

    mt = sub.add_parser("mute", help="Mute a chat")
    mt.add_argument("target", help="chat_id")

    um = sub.add_parser("unmute", help="Unmute a chat")
    um.add_argument("target", help="chat_id")

    jn = sub.add_parser("join", help="Join a channel by @username")
    jn.add_argument("target", help="@username")

    lv = sub.add_parser("leave", help="Leave a chat")
    lv.add_argument("target", help="chat_id")

    # ── Groups & Channels ──
    cg = sub.add_parser("create-group", help="Create a group")
    cg.add_argument("name")
    cg.add_argument("user_ids", nargs="+", help="User IDs to invite")

    cc = sub.add_parser("create-channel", help="Create a channel")
    cc.add_argument("name")

    iv = sub.add_parser("invite", help="Invite users to group")
    iv.add_argument("group", help="group_id")
    iv.add_argument("user_ids", nargs="+")

    kk = sub.add_parser("kick", help="Remove users from group")
    kk.add_argument("group", help="group_id")
    kk.add_argument("user_ids", nargs="+")

    rc2 = sub.add_parser("resolve-channel", help="Resolve channel by @username")
    rc2.add_argument("username")

    # ── Parsing ──
    pc = sub.add_parser("parse-channel", help="Parse posts from a channel")
    pc.add_argument("target", help="@username")
    pc.add_argument("--limit", type=int, default=100, help="Max posts to fetch")
    pc.add_argument("--output", "-o", help="Save to JSON file")

    pm2 = sub.add_parser("parse-members", help="Parse members of a channel/group")
    pm2.add_argument("target", help="@username or chat_id")
    pm2.add_argument("--output", "-o", help="Save to JSON file")

    cs = sub.add_parser("channel-stats", help="Channel stats and activity")
    cs.add_argument("target", help="@username or chat_id")

    # ── Search & Export ──
    sr = sub.add_parser("search", help="Search messages in a chat")
    sr.add_argument("chat", help="chat_id")
    sr.add_argument("query", nargs="+")
    sr.add_argument("--limit", type=int, default=20)

    ex = sub.add_parser("export-chat", help="Export chat history to JSON")
    ex.add_argument("target", help="chat_id")
    ex.add_argument("--output", "-o", default="")
    ex.add_argument("--limit", type=int, default=1000)

    um = sub.add_parser("user-messages", help="Messages from a user in chat")
    um.add_argument("chat", help="chat_id")
    um.add_argument("user", help="user_id")
    um.add_argument("--limit", type=int, default=50)

    # ── Misc ──
    sub.add_parser("typing", help="Send typing indicator").add_argument("target", help="chat_id")
    sub.add_parser("archive", help="Archive a chat").add_argument("target", help="chat_id")
    sub.add_parser("unarchive", help="Unarchive a chat").add_argument("target", help="chat_id")
    sub.add_parser("folders", help="List chat folders")
    sub.add_parser("active-sessions", help="List active devices")

    # ── Users ──
    ui = sub.add_parser("user-info", help="Get user info by id")
    ui.add_argument("user", help="user_id")

    sp = sub.add_parser("search-phone", help="Search user by phone")
    sp.add_argument("phone")

    bl = sub.add_parser("block", help="Block a user")
    bl.add_argument("user", help="user_id")

    ub = sub.add_parser("unblock", help="Unblock a user")
    ub.add_argument("user", help="user_id")

    ac = sub.add_parser("add-contact", help="Add user to contacts")
    ac.add_argument("user", help="user_id")

    # ── Profile ──
    sb = sub.add_parser("set-bio", help="Update profile bio")
    sb.add_argument("text", nargs="+")

    sn2 = sub.add_parser("set-name", help="Update profile name")
    sn2.add_argument("first")
    sn2.add_argument("last", nargs="?", default="")

    sp2 = sub.add_parser("set-photo", help="Set profile photo")
    sp2.add_argument("file", nargs="?", default="", help="Path to photo file")
    sp2.add_argument("--preset", help="Preset avatar ID or 'list' to browse")

    sub.add_parser("refresh-token", help="Refresh and save auth token")

    # ── Discovery & Status ──
    ol = sub.add_parser("online-status", help="Check user online status")
    ol.add_argument("user", help="user_id")

    ps = sub.add_parser("public-search", help="Search public channels/groups")
    ps.add_argument("query", nargs="+")
    ps.add_argument("--count", type=int, default=10)

    gs = sub.add_parser("global-search", help="Search across all chats")
    gs.add_argument("query", nargs="+")
    gs.add_argument("--count", type=int, default=10)

    cm = sub.add_parser("chat-media", help="Get media from a chat")
    cm.add_argument("target", help="chat_id")
    cm.add_argument("--type", default="PHOTO", choices=["PHOTO", "VIDEO", "FILE", "AUDIO"])
    cm.add_argument("--limit", type=int, default=20)

    mn = sub.add_parser("mentions", help="Get recent @mentions")
    mn.add_argument("--chat", help="Filter by chat_id")
    mn.add_argument("--limit", type=int, default=20)

    # ── Session ──
    sub.add_parser("sessions", help="List saved sessions")

    # ── Listen ──
    ls = sub.add_parser("listen", help="Listen for incoming messages")
    ls.add_argument("--chat", help="Filter by chat_id")
    ls.add_argument("--ai", action="store_true", help="Reply via AI Gateway")
    ls.add_argument("--model", default="claude-sonnet-4-5-20250929", help="AI model for replies")

    return p


COMMAND_MAP = {
    "dialogs":          cmd_dialogs,
    "read-chat":        cmd_read_chat,
    "chat-info":        cmd_chat_info,
    "pinned":           cmd_pinned,
    "members":          cmd_members,
    "send":             cmd_send,
    "reply":            cmd_reply,
    "edit":             cmd_edit,
    "delete":           cmd_delete,
    "pin":              cmd_pin,
    "react":            cmd_react,
    "send-file":        cmd_send_file,
    "broadcast":        cmd_broadcast,
    "mark-read":        cmd_mark_read,
    "mark-unread":      cmd_mark_unread,
    "mute":             cmd_mute,
    "unmute":           cmd_unmute,
    "join":             cmd_join,
    "leave":            cmd_leave,
    "create-group":     cmd_create_group,
    "create-channel":   cmd_create_channel,
    "invite":           cmd_invite,
    "kick":             cmd_kick,
    "resolve-channel":  cmd_resolve_channel,
    "parse-channel":    cmd_parse_channel,
    "parse-members":    cmd_parse_members,
    "channel-stats":    cmd_channel_stats,
    "search":           cmd_search,
    "export-chat":      cmd_export_chat,
    "user-messages":    cmd_user_messages,
    "typing":           cmd_typing,
    "archive":          cmd_archive,
    "unarchive":        cmd_unarchive,
    "folders":          cmd_folders,
    "active-sessions":  cmd_active_sessions,
    "set-photo":        cmd_set_photo,
    "refresh-token":    cmd_refresh_token,
    "online-status":    cmd_online_status,
    "public-search":    cmd_public_search,
    "global-search":    cmd_global_search,
    "chat-media":       cmd_chat_media,
    "mentions":         cmd_mentions,
    "user-info":        cmd_user_info,
    "search-phone":     cmd_search_phone,
    "block":            cmd_block,
    "unblock":          cmd_unblock,
    "add-contact":      cmd_add_contact,
    "set-bio":          cmd_set_bio,
    "set-name":         cmd_set_name,
    "sessions":         cmd_sessions,
    "listen":           cmd_listen,
}


async def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # sessions command doesn't need a live connection
    if args.command == "sessions":
        from max_core import session as sess
        sessions = sess.list_sessions()
        if not sessions:
            print("No sessions saved.")
        for s in sessions:
            status = "✓ active" if s["has_token"] else "✗ no token"
            print(f"  {s['phone']:<16}  {status}  updated={s['updated_at']}")
        return

    handler = COMMAND_MAP.get(args.command)
    if not handler:
        print(f"Unknown command: {args.command}")
        sys.exit(1)

    client = await make_client(args)
    try:
        await handler(client, args)
    except MaxError as e:
        print(f"MAX Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        pass
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
