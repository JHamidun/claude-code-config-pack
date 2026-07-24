# Posting Messages with Custom Emoji Inline

How to post a Telegram message where custom emoji render INLINE in the
text (not as reactions). Uses Telethon `MessageEntityCustomEmoji`.

## Why This Is Nontrivial

You cannot just paste a custom emoji into a message string and expect
Telegram clients to render it. The message body carries a plain alt
character (e.g. `🔥`), and a parallel `entities` list tells the client:
"at this offset, this many UTF-16 units, render document_id X instead."

Get the offset wrong by one and the entity points into the middle of a
neighboring character — clients fall back to plain text.

## Minimal Telethon Flow

```python
from telethon.tl.functions.messages import GetStickerSetRequest
from telethon.tl.types import (
    InputStickerSetShortName,
    MessageEntityCustomEmoji,
)

# 1. Resolve your emoji set into an alt -> document_id map.
pack = await client(GetStickerSetRequest(
    InputStickerSetShortName('<your_pack_short_name>'),
    hash=0,
))
doc_by_alt = {}
for p in pack.packs:
    for alt_emoji in p.emoticon:
        for doc_id in p.documents:
            doc_by_alt[alt_emoji] = doc_id

# 2. Build the text and entity for a single custom emoji.
text = 'Привет 🔥 как дела'

# Offset is in UTF-16 code units, NOT Python chars.
off = len(text.split('🔥')[0].encode('utf-16-le')) // 2

entities = [
    MessageEntityCustomEmoji(
        offset=off,
        length=2,                       # 🔥 is a surrogate pair -> 2
        document_id=doc_by_alt['🔥'],
    ),
]

# 3. Send.
await client.send_message(
    '@your_channel',
    text,
    formatting_entities=entities,
)
```

The recipient sees `Привет <your_branded_fire> как дела` with the custom
emoji rendered inline at line-height.

## The UTF-16 Offset Rule

This is the rule everyone gets wrong on first try.

Telegram message entity offsets and lengths are measured in
**UTF-16 code units**, not Python characters, not bytes.

Practical consequences:

| Emoji | UTF-16 length |
|-------|---------------|
| `✦` (BMP) | 1 |
| `🔥` (surrogate pair, non-BMP) | 2 |
| `🤣` (surrogate pair, non-BMP) | 2 |
| `🤩` (surrogate pair, non-BMP) | 2 |
| `👨👩👧` (ZWJ sequence, 4 codepoints + ZWJ) | 11 |
| `a`, `я` (BMP letter) | 1 |

ZWJ sequences are rare in practice — most emoji you'll bind to custom
overrides are single-codepoint surrogate pairs (length 2).

## Helper: Offset Calculator

```python
def utf16_off(text: str, ch_idx: int) -> int:
    """UTF-16 code-unit offset of text[:ch_idx]."""
    return len(text[:ch_idx].encode('utf-16-le')) // 2

def utf16_len(s: str) -> int:
    """UTF-16 code-unit length of substring s."""
    return len(s.encode('utf-16-le')) // 2
```

Use:

```python
text = 'Привет 🔥 как дела'
i = text.index('🔥')
off = utf16_off(text, i)
ln  = utf16_len('🔥')   # 2
```

## Multi-Emoji Sequencing

When you have multiple custom emoji in one message, build entities
left-to-right. Each entity's offset is independent of the others
(it is the UTF-16 offset in the FINAL text), not cumulative.

```python
text = '🔥 запуск 🤩 и ✦ финал'
entities = []

for char_substr in ['🔥', '🤩', '✦']:
    i = text.index(char_substr)
    entities.append(MessageEntityCustomEmoji(
        offset=utf16_off(text, i),
        length=utf16_len(char_substr),
        document_id=doc_by_alt[char_substr],
    ))

await client.send_message('@your_channel', text, formatting_entities=entities)
```

If the same emoji appears twice (`'🔥 ... 🔥'`), `str.index` only finds the
first. Iterate with `enumerate` over characters or use `re.finditer`:

```python
import re
for m in re.finditer(re.escape('🔥'), text):
    i = m.start()
    entities.append(MessageEntityCustomEmoji(
        offset=utf16_off(text, i),
        length=utf16_len('🔥'),
        document_id=doc_by_alt['🔥'],
    ))
```

## Common Failure Modes

| Symptom | Cause |
|---------|-------|
| Custom emoji renders as plain alt (🔥 instead of branded) | `document_id` wrong / stale (set re-uploaded), or recipient client doesn't support custom emoji (old Telegram version) |
| Custom emoji renders at wrong position (shifted) | Offset measured in Python chars instead of UTF-16 units |
| Entity ignored entirely | `length` is 0 or doesn't match UTF-16 width of substring at that offset |
| Free account sender — message goes through but custom emoji shows alt | Sender is not Premium. Premium IS required to USE custom emoji inline. Receivers don't need Premium to see them. |
| `MessageEntityCustomEmoji` raises on send | `document_id` is an `int` but should be `int` of correct shape — re-fetch via `GetStickerSetRequest` and don't hand-construct |

## Channel vs Private Chat

- Posting to your channel: sender must be channel admin + Premium.
- Posting to private chat or group: sender must be Premium.
- All recipients see the rendered custom emoji regardless of their own
  Premium status.

## Bot Caveat

Bots (via Bot API) currently CANNOT send custom emoji inline. The Bot
API rejects `custom_emoji` entity types. If you need a bot to post with
custom emoji, route through a userbot (Telethon, MTProto) instead.

## Cross-References

- Resolve document_id mapping: `channel-reactions-setup.md`
- Encode the WEBMs first: `static-vs-video-vs-emoji-spec.md`,
  `vp9-alpha-encoder-setup.md`
- Bot vs userbot flow: `telegram-bot-flows.md`
