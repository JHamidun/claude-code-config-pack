# -*- coding: utf-8 -*-
"""
tg_channel_comments.py — audit + publish replies/reactions ON BEHALF OF your channel.
Companion to the comment-replies skill.

ВАЖНО: публиковать ТОЛЬКО апрувнутое владельцем аккаунта. audit — read-only;
reply/react/batch — пишут в реальный публичный тред, отменить нельзя.

Настройка (один раз):
  TELEGRAM_API_ID / TELEGRAM_API_HASH — свои, бесплатно на https://my.telegram.org
      -> "API development tools". Без них скрипт не стартует.
  TELEGRAM_CHANNEL — username твоего канала без @ (или флаг --channel в каждой команде).
  TELEGRAM_SESSION — путь к файлу telethon-сессии, по умолчанию ~/.claude/telegram_session.
  Нужны права админа в канале: без них send_as недоступен.

Usage:
  python tg_channel_comments.py audit [--channel NAME] [--days 30] [--json out.json]
      List user comments with NO channel reply and NO channel reaction (with context).
  python tg_channel_comments.py reply <comment_id> --file reply.txt
      Post a reply to <comment_id> AS THE CHANNEL (verifies sender==Channel).
  python tg_channel_comments.py react <comment_id> <emoji>
      React to <comment_id> (registers from the channel; reaction must be in allowed set).
  python tg_channel_comments.py batch <plan.json>
      plan.json = {"replies":[{"id":123,"file":"r1.txt"}|{"id":123,"text":"..."}],
                   "reactions":[{"id":123,"emoji":"❤"}]}
      Posts everything with anti-spam pauses (replies 25-45s, reactions 8-18s).

Run with ABSOLUTE path in background to avoid Errno 2.
"""
import asyncio, sys, io, os, json, random, argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path
from telethon import TelegramClient
from telethon.tl.types import (Channel, User, PeerChannel, PeerUser,
                               ReactionEmoji, InputReplyToMessage, ChatReactionsAll)
from telethon.tl.functions.channels import GetFullChannelRequest, GetSendAsRequest
from telethon.tl.functions.messages import SendMessageRequest, SendReactionRequest
from telethon.errors import FloodWaitError

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", write_through=True)

SESSION = os.environ.get("TELEGRAM_SESSION") or str(Path.home() / ".claude" / "telegram_session")


def credentials():
    """Свои api_id/api_hash с https://my.telegram.org. Чужие сюда не вписывать:
    ключи привязаны к аккаунту, и лимиты/баны прилетают его владельцу."""
    api_id = os.environ.get("TELEGRAM_API_ID") or os.environ.get("TELETHON_API_ID")
    api_hash = os.environ.get("TELEGRAM_API_HASH") or os.environ.get("TELETHON_API_HASH")
    if not api_id or not api_hash:
        sys.exit(
            "Нужны свои Telegram API credentials.\n"
            "  1) https://my.telegram.org -> API development tools -> создать приложение\n"
            "  2) export TELEGRAM_API_ID=...   export TELEGRAM_API_HASH=...\n"
            "     (или положи их в свой .env и подгрузи перед запуском)"
        )
    return int(api_id), api_hash


def channel_name(args):
    name = getattr(args, "channel", None) or os.environ.get("TELEGRAM_CHANNEL")
    if not name:
        sys.exit("Укажи канал: --channel <username без @> или TELEGRAM_CHANNEL=<username>")
    return name.lstrip("@")


async def setup(c, channel):
    me = await c.get_me()
    ch = await c.get_entity(channel)
    full = await c(GetFullChannelRequest(ch))
    g = await c.get_entity(PeerChannel(full.full_chat.linked_chat_id))
    return me, ch, g, full


def allowed_reactions(full):
    av = full.full_chat.available_reactions
    if isinstance(av, ChatReactionsAll) or av is None:
        return None  # all allowed
    return {getattr(r, "emoticon", None) for r in getattr(av, "reactions", []) if getattr(r, "emoticon", None)}


async def cmd_audit(c, args):
    me, ch, g, full = await setup(c, channel_name(args))
    cutoff = datetime.now(timezone.utc) - timedelta(days=args.days)
    msgs = []
    async for m in c.iter_messages(g, limit=5000):
        if m.date < cutoff:
            break
        msgs.append(m)
    by_id = {m.id: m for m in msgs}
    children = {}
    for m in msgs:
        rt = m.reply_to.reply_to_msg_id if m.reply_to else None
        if rt:
            children.setdefault(rt, []).append(m)

    def kind(m):
        s = m.sender
        if isinstance(s, Channel):
            return "CHANNEL"
        if isinstance(s, User):
            return "ME" if s.id == me.id else "USER"
        return "OTHER"

    def owner_reacted(m):
        if not (m.reactions and m.reactions.recent_reactions):
            return False
        for r in m.reactions.recent_reactions:
            p = r.peer_id
            if isinstance(p, PeerChannel) and p.channel_id in (ch.id, g.id):
                return True
            if isinstance(p, PeerUser) and p.user_id == me.id:
                return True
        return False

    out = []
    for m in msgs:
        if kind(m) != "USER":
            continue
        # owner reply may arrive as Channel, ME, or anonymously (from_id=None when the
        # channel/admin replies into the linked group via send_as) — count all three
        replied = any(
            getattr(ch_m, "from_id", None) is None or kind(ch_m) in ("CHANNEL", "ME")
            for ch_m in children.get(m.id, [])
        )
        if replied or owner_reacted(m):
            continue
        tid = (getattr(m.reply_to, "reply_to_top_id", None) or
               (m.reply_to.reply_to_msg_id if m.reply_to else None))
        ctx = (by_id[tid].text or "")[:200] if tid and tid in by_id else ""
        s = m.sender
        nm = ((s.first_name or "") + (" @" + s.username if s.username else "")).strip()
        out.append({"id": m.id, "date": m.date.strftime("%Y-%m-%d %H:%M"),
                    "sender": nm, "text": m.text or "[media]", "context_post": ctx})
    print(f"=== UNANSWERED + UNREACTED (last {args.days}d): {len(out)} ===\n")
    for r in out:
        print(f"#{r['id']} [{r['date']}] {r['sender']}")
        print(f"  пост: {r['context_post'][:120].replace(chr(10),' ')}")
        print(f"  коммент: {r['text'][:300].replace(chr(10),' ')}\n")
    if args.json:
        Path(args.json).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"saved -> {args.json}")


async def post_reply(c, ch, g, comment_id, text):
    resp = await c(SendMessageRequest(
        peer=g, message=text,
        reply_to=InputReplyToMessage(reply_to_msg_id=comment_id),
        send_as=ch, random_id=random.randint(1, 2**62)))
    nid = None
    for u in getattr(resp, "updates", []):
        m = getattr(u, "message", None)
        if m is not None and getattr(m, "id", None):
            nid = m.id
            break
    sent = await c.get_messages(g, ids=nid) if nid else None
    ok = isinstance(sent.sender, Channel) if sent else False
    return nid, ok


async def cmd_reply(c, args):
    me, ch, g, full = await setup(c, channel_name(args))
    text = Path(args.file).read_text(encoding="utf-8") if args.file else args.text
    nid, ok = await post_reply(c, ch, g, args.comment_id, text)
    print(f"reply->#{args.comment_id} new={nid} as_channel={ok}")
    print(f"link: https://t.me/{channel_name(args)}/{args.comment_id}?comment={nid}")


async def cmd_react(c, args):
    me, ch, g, full = await setup(c, channel_name(args))
    allowed = allowed_reactions(full)
    emo = args.emoji if (allowed is None or args.emoji in allowed) else "👍"
    await c(SendReactionRequest(peer=g, msg_id=args.comment_id, add_to_recent=True,
                                reaction=[ReactionEmoji(emoticon=emo)]))
    print(f"react {emo} -> #{args.comment_id}")


async def cmd_batch(c, args):
    me, ch, g, full = await setup(c, channel_name(args))
    allowed = allowed_reactions(full)
    plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    reps = plan.get("replies", [])
    reacts = plan.get("reactions", [])
    print(f"=== REPLIES ({len(reps)}) ===")
    for i, r in enumerate(reps, 1):
        text = Path(r["file"]).read_text(encoding="utf-8") if r.get("file") else r["text"]
        try:
            nid, ok = await post_reply(c, ch, g, r["id"], text)
            print(f"[{i}/{len(reps)}] reply->#{r['id']} new={nid} as_channel={ok}")
        except FloodWaitError as e:
            print(f"[{i}] FLOOD_WAIT {e.seconds}s"); await asyncio.sleep(e.seconds + 2)
        except Exception as e:
            print(f"[{i}] reply->#{r['id']} ERROR {type(e).__name__}: {e}")
        await asyncio.sleep(random.uniform(25, 45))
    print(f"\n=== REACTIONS ({len(reacts)}) ===")
    for i, r in enumerate(reacts, 1):
        emo = r["emoji"] if (allowed is None or r["emoji"] in allowed) else "👍"
        try:
            await c(SendReactionRequest(peer=g, msg_id=r["id"], add_to_recent=True,
                                        reaction=[ReactionEmoji(emoticon=emo)]))
            print(f"[{i}/{len(reacts)}] react {emo} -> #{r['id']}")
        except FloodWaitError as e:
            print(f"[{i}] FLOOD_WAIT {e.seconds}s"); await asyncio.sleep(e.seconds + 2)
        except Exception as e:
            print(f"[{i}] react->#{r['id']} ERROR {type(e).__name__}: {e}")
        await asyncio.sleep(random.uniform(8, 18))
    print("\n=== DONE ===")


def main():
    p = argparse.ArgumentParser(description="TG channel comments: audit + reply/react as channel")
    sub = p.add_subparsers(dest="cmd", required=True)
    # --channel объявляется в каждой подкоманде, а не в корневом парсере: корневой
    # аргумент argparse затирает подкомандным дефолтом None.
    ch_help = "username канала без @ (или переменная TELEGRAM_CHANNEL)"
    a = sub.add_parser("audit"); a.add_argument("--days", type=int, default=30); a.add_argument("--json")
    a.add_argument("--channel", help=ch_help)
    r = sub.add_parser("reply"); r.add_argument("comment_id", type=int)
    r.add_argument("--file"); r.add_argument("--text"); r.add_argument("--channel", help=ch_help)
    rc = sub.add_parser("react"); rc.add_argument("comment_id", type=int); rc.add_argument("emoji")
    rc.add_argument("--channel", help=ch_help)
    b = sub.add_parser("batch"); b.add_argument("plan"); b.add_argument("--channel", help=ch_help)
    args = p.parse_args()
    handlers = {"audit": cmd_audit, "reply": cmd_reply, "react": cmd_react, "batch": cmd_batch}

    api_id, api_hash = credentials()

    async def run():
        c = TelegramClient(SESSION, api_id, api_hash)
        await c.start()
        await handlers[args.cmd](c, args)
        await c.disconnect()
    asyncio.run(run())


if __name__ == "__main__":
    main()
