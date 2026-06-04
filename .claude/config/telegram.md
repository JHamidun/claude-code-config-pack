# Telegram

> Add your Telegram account details here.

| Field | Value |
|-------|-------|
| Account | @YourUsername |
| API ID | YOUR_TELEGRAM_API_ID |
| API Hash | YOUR_TELEGRAM_API_HASH |
| Phone | +1234567890 |

## Bot Tokens
Store in `~/.claude/.credentials.master.env`:
```
BOT_TOKEN=your_bot_token
```

## Telethon Client
```python
import os
api_id = int(os.getenv('TELEGRAM_API_ID'))
api_hash = os.getenv('TELEGRAM_API_HASH')
```
