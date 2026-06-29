# Outlook / Exchange Operations

/outlook - Work with Exchange email (your-work-email@company.com)

## Usage
```
/outlook inbox [count]        - Recent emails
/outlook unread               - Unread emails
/outlook search <query>       - Search emails
/outlook read <item_id>       - Read specific email
/outlook send <to> <subject>  - Send email
/outlook reply <item_id>      - Reply to email
/outlook folders              - List folders
```

## Instructions for Claude

**Account:** your-work-email@company.com
**Credentials:** EXCHANGE_PASSWORD from ~/.claude/.credentials.master.env

### Setup

```python
import os
from exchangelib import Credentials, Account, Configuration, DELEGATE
from exchangelib import Message, Mailbox, HTMLBody

password = os.getenv('EXCHANGE_PASSWORD')
if not password:
    from dotenv import load_dotenv
    load_dotenv('${HOME}/.claude/.credentials.master.env')
    password = os.getenv('EXCHANGE_PASSWORD')

email = 'your-work-email@company.com'
server = 'mail.company.com'

credentials = Credentials(username=email, password=password)
config = Configuration(server=server, credentials=credentials)

# IMPORTANT: autodiscover=False + explicit server — autodiscover не работает
account = Account(
    primary_smtp_address=email,
    config=config,
    autodiscover=False,
    access_type=DELEGATE
)
```

### Read inbox

```python
# Latest emails
for item in account.inbox.all().order_by('-datetime_received')[:10]:
    print(f"From: {item.sender.email_address}")
    print(f"Subject: {item.subject}")
    print(f"Date: {item.datetime_received}")
    print(f"ID: {item.id}")
    print()

# Unread only
for item in account.inbox.filter(is_read=False).order_by('-datetime_received')[:20]:
    print(f"[UNREAD] {item.subject} - from {item.sender.email_address}")
```

### Search

```python
# By subject
items = account.inbox.filter(subject__contains='report')

# By sender
items = account.inbox.filter(sender__email_address='someone@example.com')

# By date range
from datetime import datetime, timedelta
from exchangelib import EWSDateTime, EWSTimeZone
tz = EWSTimeZone.localzone()
since = tz.localize(EWSDateTime(2026, 2, 1))
items = account.inbox.filter(datetime_received__gt=since)

# Full text
items = account.inbox.filter(body__contains='keyword')
```

### Send email

```python
msg = Message(
    account=account,
    subject='Subject',
    body=HTMLBody('<p>Email body</p>'),
    to_recipients=[Mailbox(email_address='recipient@example.com')],
    cc_recipients=[Mailbox(email_address='cc@example.com')],  # optional
)
msg.send()
```

### Reply

```python
item = account.inbox.get(id=item_id)
item.reply(
    subject=f'Re: {item.subject}',
    body=HTMLBody('<p>Reply text</p>')
)
```

### List folders

```python
for folder in account.root.walk():
    print(f"{folder.absolute} ({folder.total_count} items)")
```

### Attachments

```python
# Read attachments
for item in account.inbox.filter(has_attachments=True)[:5]:
    for attachment in item.attachments:
        if hasattr(attachment, 'content'):
            with open(f'${HOME}/.claude/downloads/{attachment.name}', 'wb') as f:
                f.write(attachment.content)

# Send with attachment
from exchangelib import FileAttachment
msg = Message(account=account, subject='With attachment', body='See attached')
with open('file.pdf', 'rb') as f:
    attachment = FileAttachment(name='file.pdf', content=f.read())
msg.attach(attachment)
msg.send()
```

## Dependencies

```bash
pip install exchangelib
```

## Notes

- **Server:** mail.company.com (explicit, NOT autodiscover)
- **autodiscover=False** — обязательно, autodiscover не находит сервер
- Account is migrating from company.com to your-email@your-domain.com
- For OAuth2 (Office 365): use `OAuth2Credentials` instead of basic `Credentials`
