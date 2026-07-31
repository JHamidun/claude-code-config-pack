---
description: "Google Drive: список последних файлов, поиск по имени, чтение и метаданные файла (Drive API v3). Триггеры: «google drive», «гугл диск», «найди файл на диске», «файлы drive». НЕ Яндекс.Диск → skill yandex."
argument-hint: "[list <N> | search <запрос> | read <file_id> | info <file_id>]"
---

# Google Drive Operations

/gdrive - Работа с Google Drive

## Описание
Поиск, чтение и управление файлами на Google Drive пользователя.

## Использование
```
/gdrive list [количество]     - Список последних файлов
/gdrive search <запрос>       - Поиск файлов по имени
/gdrive read <file_id>        - Прочитать содержимое файла
/gdrive info <file_id>        - Информация о файле
```

## Инструкции для Claude

При вызове этой команды:

1. **Загрузи OAuth токен:**
```python
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

with open('${HOME}/.claude/google_oauth_token.json', 'r') as f:
    token_data = json.load(f)
creds = Credentials.from_authorized_user_info(token_data)
drive = build('drive', 'v3', credentials=creds)
```

2. **Операции:**

**Список файлов:**
```python
results = drive.files().list(
    pageSize=10,
    fields='files(id, name, mimeType, modifiedTime, size)'
).execute()
```

**Поиск:**
```python
results = drive.files().list(
    q=f"name contains '{query}'",
    pageSize=20,
    fields='files(id, name, mimeType)'
).execute()
```

**Информация о файле:**
```python
file = drive.files().get(
    fileId=file_id,
    fields='id,name,mimeType,size,createdTime,modifiedTime,webViewLink'
).execute()
```

3. **Типы файлов Google:**
- `application/vnd.google-apps.document` - Google Doc
- `application/vnd.google-apps.spreadsheet` - Google Sheet
- `application/vnd.google-apps.presentation` - Google Slides

4. **Для чтения содержимого Google Docs/Sheets** используй соответствующие API (Docs API, Sheets API).

## Примеры
- `/gdrive list 5` - показать 5 последних файлов
- `/gdrive search отчёт` - найти файлы со словом "отчёт"
- `/gdrive read 1abc...xyz` - прочитать файл по ID
