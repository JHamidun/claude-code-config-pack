# Custom Emoji as Channel Reactions

How to wire a custom emoji set into a Telegram channel as reactions.

## Prerequisites

- Custom emoji set already published (see `static-vs-video-vs-emoji-spec.md`
  for spec and `telegram-bot-flows.md` for `/newemojipack` flow).
- Channel admin rights on `@your_channel`.
- Premium subscription on the ACCOUNT that adds custom emoji as reactions.
  Free accounts can use them (sender/reactor side requires Premium; viewer
  side does NOT).

## UI Path

Telegram app -> Channel info -> Edit -> Reactions -> (toggle "Custom") ->
"Add custom emoji" -> pick from your published custom emoji sets.

Notes:
- "All emoji" toggle lets ANY custom emoji be used as reaction. That is
  usually noisy — for branded channels, prefer the curated list.
- Each channel has a numeric ceiling on how many distinct reactions can be
  configured. Currently ~100 — well above any practical curated set.

## Common Curated Pattern

Highest engagement empirically comes from a mix:

- **~8 custom emoji** (your branded set) for identity / signature.
- Standard reactions (👍 ❤️ 🔥 🥰 👏 😁 🤔 🤯 😱 🤬 😢 🎉 🤩 🤮 💩 🙏)
  remain enabled in parallel — never disable them, they carry baseline
  engagement.

Why 8 custom: enough to map to a vocabulary (yes / no / fire / sad / wtf /
clap / brain / heart) without overwhelming the reaction picker. More than
~12 custom and users default to the standard set anyway.

## Channel Boost Level vs Story Limit

Channel boosts are separate from reactions, but they share the same
"channel premium" axis worth knowing during a sticker-pack campaign.

Boost level (granted by Premium subscribers boosting your channel) caps
the **daily story limit**:

| Boost level | Stories/day |
|-------------|-------------|
| 1 | 1 |
| 2 | 2 |
| ... | ... |
| 8 | 8 |
| ... | scales |

If you launch a sticker pack and the campaign plan includes 4 daily
stories (teasers, drops, recap, behind-the-scenes), you need boost level
4+. Worth lining up boosters before the launch day.

Boost level also unlocks:
- More custom reactions slot count.
- Custom channel emoji status.
- Backgrounds, profile color, etc.

Not directly relevant to the sticker pipeline, but every boost helps the
campaign cadence.

## document_id Mapping (For Code Use)

When you want to programmatically post messages containing your custom
emoji (see `custom-emoji-posting.md`), pin the `document_id` per
emoji alt.

Why pin: `document_id` is stable per uploaded WEBM. If you re-upload an
emoji (fixing a frame), the `document_id` changes. Code that hardcodes
old IDs will silently render fallback text instead of the emoji.

Pin them at publish time:

```python
from telethon.tl.functions.messages import GetStickerSetRequest
from telethon.tl.types import InputStickerSetShortName

pack = await client(GetStickerSetRequest(
    InputStickerSetShortName('<your_pack_name>'),
    hash=0,
))

mapping = {}
for p in pack.packs:
    for alt_emoji in p.emoticons:
        for doc_id in p.documents:
            mapping[alt_emoji] = doc_id

# persist
import json, pathlib
pathlib.Path('<HOME>/.claude/sticker-pack-generator/emoji_docids.json').write_text(
    json.dumps(mapping, ensure_ascii=False, indent=2)
)
```

After re-upload, re-run and diff against the persisted file. Any changed
`document_id` means dependent code needs updating.

## Verification Checklist

After enabling reactions:

1. Open the channel as a NON-admin Premium account. Long-press a post,
   confirm the custom emoji appear in the reaction picker.
2. Open the channel as a NON-admin FREE account. Confirm:
   - Free account CAN see existing reactions (with the custom emoji
     rendered correctly).
   - Free account CANNOT pick a custom emoji as new reaction (gets
     Premium upsell prompt). This is expected.
3. From a Premium account, react with one of your custom emoji. Confirm
   it renders at ~64x64 px (jumbo size) on mobile, ~32x32 on desktop.

## Common Pitfalls

- Reaction shows as a generic placeholder emoji on some clients — your
  custom emoji WEBM is over 64 KB or has wrong pixel format. Re-encode
  per `static-vs-video-vs-emoji-spec.md`.
- Reaction picker doesn't show custom set — channel admin forgot to add
  the set, or the set is in "Owner-only" visibility. Republish via
  BotFather to ensure public visibility.
- `document_id` returns empty in `GetStickerSetRequest` — the emoji set
  short name is wrong, or the set is unpublished. Use the exact
  `<short_name>` from the t.me/addemoji/<short_name> link.

## Cross-References

- Spec / encoding constraints: `static-vs-video-vs-emoji-spec.md`
- Bot flow to publish the set: `telegram-bot-flows.md`
- Programmatic use of custom emoji: `custom-emoji-posting.md`
