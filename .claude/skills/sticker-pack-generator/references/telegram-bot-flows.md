# Telethon flows для @Stickers

## Базовый клиент

```python
import asyncio, os
from telethon import TelegramClient

cred = open(os.path.expanduser('~/.claude/.credentials.master.env'), encoding='utf-8').read()
API_ID = int(cred.split('TELEGRAM_API_ID=')[1].split('\n')[0].strip())
API_HASH = cred.split('TELEGRAM_API_HASH=')[1].split('\n')[0].strip()
SESSION = os.path.expanduser('~/.claude/telegram_session')

client = TelegramClient(SESSION, API_ID, API_HASH)
await client.start()  # первый раз попросит phone/SMS code
bot = await client.get_entity('Stickers')
```

## /newpack — создать пак

```python
async with client.conversation(bot, timeout=180) as conv:
    await conv.send_message('/cancel'); await asyncio.sleep(1.2)
    await conv.send_message('/newvideopack'); await asyncio.sleep(1.2)  # для video stickers
    await conv.get_response(timeout=20)  # "Choose name"
    await conv.send_message(TITLE); await asyncio.sleep(2)  # human-readable title
    await conv.get_response(timeout=20)  # "Now send the first sticker"
    # Затем для каждого стикера:
    await conv.send_file(webm, force_document=True); await asyncio.sleep(3.5)
    await conv.get_response(timeout=20)
    await conv.send_message(emoji); await asyncio.sleep(1.5)
    await conv.get_response(timeout=20)
    # после всех:
    await conv.send_message('/publish'); await asyncio.sleep(2)
    # бот спросит short_name (URL alias)
    await conv.send_message(SHORT_NAME); await asyncio.sleep(2)
```

## /addsticker — добавить к существующему

```python
async with client.conversation(bot, timeout=180) as conv:
    await conv.send_message('/cancel'); await asyncio.sleep(1.2)
    await conv.send_message('/addsticker'); await asyncio.sleep(1.2)
    await conv.get_response(timeout=20)  # "Choose pack"
    await conv.send_message(SHORT_NAME); await asyncio.sleep(2)
    await conv.get_response(timeout=20)
    await conv.send_file(webm, force_document=True); await asyncio.sleep(3.5)
    await conv.get_response(timeout=20)
    await conv.send_message(emoji); await asyncio.sleep(1.5)
```

## /replacesticker — заменить контент сохранив эмодзи (СТИКЕР-ПАК)

```python
# Нужен ИСХОДНЫЙ document object из пакета:
from telethon.tl.functions.messages import GetStickerSetRequest
from telethon.tl.types import InputStickerSetShortName

pack = await client(GetStickerSetRequest(
    stickerset=InputStickerSetShortName(short_name=SHORT_NAME), hash=0))
emoji_by_docid = {}
for pk in pack.packs:
    for did in pk.documents:
        emoji_by_docid.setdefault(did, pk.emoticon)
target = None
for d in pack.documents:
    if emoji_by_docid.get(d.id, '').replace('️','') == TARGET_EMOJI.replace('️',''):
        target = d; break

async with client.conversation(bot, timeout=180) as conv:
    await conv.send_message('/cancel'); await asyncio.sleep(1.2)
    await conv.send_message('/replacesticker'); await asyncio.sleep(1.2)
    await conv.get_response(timeout=20)  # "Choose pack or send sticker"
    await client.send_file(bot, file=target); await asyncio.sleep(2.5)
    await conv.get_response(timeout=20)
    await conv.send_file(new_webm, force_document=True); await asyncio.sleep(3.5)
    await conv.get_response(timeout=20)  # "Send emoji" (опционально)
    await conv.send_message(emoji); await asyncio.sleep(1.5)
```

## /replaceemoji — заменить custom emoji в EMOJI-ПАКЕ (HIDDEN COMMAND)

ВАЖНО: `/replaceemoji`, `/addemoji`, `/delemoji`, `/editemoji` — **скрытые команды**
@Stickers, не показанные в `/help`. Они работают ТОЛЬКО для emoji-паков. Для emoji-паков
`/replacesticker` НЕ работает (бот скажет "Не выбран набор стикеров").

Custom emoji document **НЕЛЬЗЯ переслать** через `client.send_file(bot, file=Document)` —
получишь `DocumentInvalidError: ... can't be used in inline mode (caused by SendMediaRequest)`.
Единственный способ "отправить" custom emoji боту — как `MessageEntityCustomEmoji` внутри
текстового сообщения (как обычный пользователь использует кастомные эмодзи).

```python
from telethon.tl.functions.messages import GetStickerSetRequest, SendMessageRequest
from telethon.tl.types import (InputStickerSetShortName, MessageEntityCustomEmoji,
                                DocumentAttributeCustomEmoji)
import random

pack = await client(GetStickerSetRequest(
    stickerset=InputStickerSetShortName(short_name=SHORT_NAME), hash=0))
emoji_by_docid = {}
for pk in pack.packs:
    for did in pk.documents:
        emoji_by_docid.setdefault(did, pk.emoticon)
target = None; alt = ''
for d in pack.documents:
    if emoji_by_docid.get(d.id, '').replace('️','') == TARGET_EMOJI.replace('️',''):
        target = d
        for attr in (d.attributes or []):
            if isinstance(attr, DocumentAttributeCustomEmoji):
                alt = attr.alt; break
        break

async with client.conversation(bot, timeout=180) as conv:
    await conv.send_message('/cancel'); await asyncio.sleep(1.2)
    await conv.send_message('/replaceemoji'); await asyncio.sleep(1.5)
    await conv.get_response(timeout=20)  # "Choose emoji set or send custom emoji"
    # Step A: указываем emoji-пак по short_name
    await conv.send_message(SHORT_NAME); await asyncio.sleep(2)
    await conv.get_response(timeout=20)  # "Please send custom emoji you want to replace"
    # Step B: посылаем custom emoji как entity в текстовом сообщении
    utf16_len = len(alt.encode('utf-16-le')) // 2
    ent = MessageEntityCustomEmoji(offset=0, length=utf16_len, document_id=target.id)
    in_peer = await client.get_input_entity(bot)
    await client(SendMessageRequest(peer=in_peer, message=alt, entities=[ent],
                                     random_id=random.getrandbits(63)))
    await asyncio.sleep(3)
    await conv.get_response(timeout=20)  # "Emoji to replace: ⌨️. Now send new webm"
    await conv.send_file(new_webm, force_document=True); await asyncio.sleep(3.5)
    await conv.get_response(timeout=20)
    await conv.send_message(emoji); await asyncio.sleep(1.5)
```

Аналогично для /delemoji (удалить custom emoji) и /addemoji (добавить новый):
- /addemoji + SHORT_NAME → send_file(new_webm) → send_message(emoji)
- /delemoji + SHORT_NAME → send custom emoji entity → confirm "Yes, I am sure!"

## /delsticker — удалить из пака

```python
async with client.conversation(bot, timeout=180) as conv:
    await conv.send_message('/cancel'); await asyncio.sleep(1.2)
    await conv.send_message('/delsticker'); await asyncio.sleep(1.2)
    await conv.get_response(timeout=15)  # "Send the sticker"
    await client.send_file(bot, file=target_doc); await asyncio.sleep(2.5)
    r = await conv.get_response(timeout=20)
    txt = (r.text or '').lower()
    if 'sure' in txt or 'yes' in txt or 'удалить' in txt:
        await conv.send_message('Yes, I am sure!'); await asyncio.sleep(1.5)
        await conv.get_response(timeout=10)
```

## FloodWaitError

```python
from telethon.errors import FloodWaitError

for attempt in range(8):
    try:
        # ... в client.conversation ...
        break
    except FloodWaitError as fw:
        await asyncio.sleep(fw.seconds + 5)
    except Exception as e:
        await asyncio.sleep(5)
```

## Idempotent progress

```python
PROGRESS = '/path/to/done.txt'
def load_done():
    if not os.path.exists(PROGRESS): return set()
    return set(open(PROGRESS, encoding='utf-8').read().splitlines())
def mark_done(name):
    with open(PROGRESS, 'a', encoding='utf-8') as f:
        f.write(name + '\n')
```

## VS16 normalization

VS16 (variation selector 16, `️`) появляется в некоторых эмодзи (❤️, ✍️, 😮💨). Сравнение должно нормализовать:

```python
def norm(e): return e.replace('️', '')  # U+FE0F
```

## SQLite session lock

Файл `~/.claude/telegram_session.session` это SQLite — если два процесса откроют — `database is locked`. Решение:
- Не запускай два python с одной сессией параллельно
- Или используй разные session-файлы (`telegram_session_2.session` и т.д.)
- НЕ убивай python через `taskkill` пока он работает — оставит `journal` файл, который при следующем старте может ругаться. Решение если убил: удалить `*.session-journal`, сессия восстановится.

## Limit and pacing

- @Stickers выдаёт FloodWait после ~37 быстрых replace в одной серии. Реальный лимит — несколько в секунду + sliding window.
- Безопасный темп: 2.5s между replace, 3.5s после send_file.
- После FloodWait — продолжает работать (просто паузим).
- Resume через progress file работает идеально.
