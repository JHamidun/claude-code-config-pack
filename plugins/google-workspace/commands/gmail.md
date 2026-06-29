# Gmail Operations

/gmail - Работа с Gmail

## Описание
Чтение, поиск и отправка email через Gmail API.

## Использование
```
/gmail inbox [количество]     - Последние письма
/gmail unread                 - Непрочитанные письма
/gmail search <запрос>        - Поиск писем
/gmail read <message_id>      - Прочитать письмо
/gmail send <кому> <тема>     - Отправить письмо
```

## Инструкции для Claude

**ВАЖНО:** Для Gmail нужны дополнительные OAuth scopes. Если токен не работает, нужно переавторизоваться с Gmail scopes.

1. **Загрузи credentials:**
```python
import json
import base64
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

with open('${HOME}/.claude/google_oauth_token.json', 'r') as f:
    token_data = json.load(f)
creds = Credentials.from_authorized_user_info(token_data)
gmail = build('gmail', 'v1', credentials=creds)
```

2. **Получить письма:**
```python
# Последние письма
results = gmail.users().messages().list(
    userId='me',
    maxResults=10,
    labelIds=['INBOX']
).execute()
messages = results.get('messages', [])

# Непрочитанные
results = gmail.users().messages().list(
    userId='me',
    q='is:unread',
    maxResults=20
).execute()
```

3. **Прочитать письмо:**
```python
msg = gmail.users().messages().get(
    userId='me',
    id=message_id,
    format='full'
).execute()

# Извлечь заголовки
headers = {h['name']: h['value'] for h in msg['payload']['headers']}
subject = headers.get('Subject', '')
sender = headers.get('From', '')
date = headers.get('Date', '')

# Извлечь тело письма
def get_body(payload):
    if 'body' in payload and payload['body'].get('data'):
        return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
    return ''

body = get_body(msg['payload'])
```

4. **Отправить письмо:**
```python
def send_email(to, subject, body):
    message = MIMEText(body)
    message['to'] = to
    message['subject'] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    gmail.users().messages().send(
        userId='me',
        body={'raw': raw}
    ).execute()
```

5. **Поиск писем:**
```python
# Gmail query syntax
results = gmail.users().messages().list(
    userId='me',
    q='from:example@gmail.com subject:отчёт after:2025/01/01'
).execute()
```

## Gmail Query Syntax
- `from:email@example.com` - от кого
- `to:email@example.com` - кому
- `subject:слово` - в теме
- `is:unread` - непрочитанные
- `is:starred` - с пометкой
- `has:attachment` - с вложением
- `after:2025/01/01` - после даты
- `before:2025/12/31` - до даты

## Примеры
- `/gmail inbox 5` - последние 5 писем
- `/gmail unread` - непрочитанные
- `/gmail search "from:boss@company.com"` - письма от босса
- `/gmail read abc123` - прочитать письмо по ID
