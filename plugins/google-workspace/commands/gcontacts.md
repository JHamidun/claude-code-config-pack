---
description: "Google Контакты (People API): список, поиск, детали, создание контактов. Триггеры: «контакты google», «найди контакт», «телефон из контактов», «создай контакт»."
argument-hint: "[list <N> | search <запрос> | get <resourceName> | create <имя> <email>]"
---

# Google Contacts Operations

/gcontacts - Работа с Google Контактами

## Описание
Просмотр, поиск и создание контактов через Google People API.

## Использование
```
/gcontacts list [количество]     - Список контактов
/gcontacts search <запрос>       - Поиск контактов
/gcontacts get <resourceName>    - Детали контакта
/gcontacts create <имя> <email>  - Создать контакт
```

## Инструкции для Claude

1. **Загрузи credentials:**
```python
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

with open('${HOME}/.claude/google_oauth_token.json', 'r') as f:
    token_data = json.load(f)
creds = Credentials.from_authorized_user_info(token_data)
people = build('people', 'v1', credentials=creds)
```

2. **Список контактов:**
```python
results = people.people().connections().list(
    resourceName='people/me',
    pageSize=100,
    personFields='names,emailAddresses,phoneNumbers,organizations'
).execute()
connections = results.get('connections', [])

for person in connections:
    names = person.get('names', [{}])
    name = names[0].get('displayName', 'Без имени') if names else 'Без имени'
    emails = [e['value'] for e in person.get('emailAddresses', [])]
    phones = [p['value'] for p in person.get('phoneNumbers', [])]
    print(f"{name} | {', '.join(emails)} | {', '.join(phones)}")
```

3. **Поиск контактов:**
```python
results = people.people().searchContacts(
    query='Иван',
    readMask='names,emailAddresses,phoneNumbers',
    pageSize=10
).execute()
for result in results.get('results', []):
    person = result.get('person', {})
    name = person.get('names', [{}])[0].get('displayName', '')
    print(name)
```

4. **Создать контакт:**
```python
contact = people.people().createContact(body={
    'names': [{'givenName': 'Иван', 'familyName': 'Петров'}],
    'emailAddresses': [{'value': 'ivan@example.com'}],
    'phoneNumbers': [{'value': '+1234567890'}],
    'organizations': [{'name': 'Company', 'title': 'Manager'}]
}).execute()
print(f"Создан: {contact['resourceName']}")
```

5. **Детали контакта:**
```python
person = people.people().get(
    resourceName='people/c1234567890',
    personFields='names,emailAddresses,phoneNumbers,organizations,addresses,birthdays'
).execute()
```

## personFields (доступные поля)
- `names` - ФИО
- `emailAddresses` - email
- `phoneNumbers` - телефоны
- `organizations` - компании
- `addresses` - адреса
- `birthdays` - дни рождения
- `urls` - ссылки
- `biographies` - заметки

## Примеры
- `/gcontacts list 20` - первые 20 контактов
- `/gcontacts search "Company"` - поиск по Company
- `/gcontacts create "John Doe" "john@example.com"` - новый контакт
