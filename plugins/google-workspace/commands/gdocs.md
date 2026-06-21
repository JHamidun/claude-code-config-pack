# Google Docs Operations

/gdocs - Работа с Google Docs

## Описание
Чтение и редактирование Google Документов.

## Использование
```
/gdocs read <doc_id>          - Прочитать документ
/gdocs summary <doc_id>       - Краткое содержание документа
/gdocs search <запрос>        - Найти документы по запросу
```

## Инструкции для Claude

При вызове этой команды:

1. **Загрузи credentials:**
```python
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

with open('${HOME}/.claude/google_oauth_token.json', 'r') as f:
    token_data = json.load(f)
creds = Credentials.from_authorized_user_info(token_data)
docs = build('docs', 'v1', credentials=creds)
```

2. **Чтение документа:**
```python
document = docs.documents().get(documentId=doc_id).execute()
title = document.get('title', 'Untitled')

# Извлечение текста
content = document.get('body', {}).get('content', [])
text = ''
for element in content:
    if 'paragraph' in element:
        for elem in element['paragraph'].get('elements', []):
            if 'textRun' in elem:
                text += elem['textRun'].get('content', '')
```

3. **Поиск документов (через Drive API):**
```python
drive = build('drive', 'v3', credentials=creds)
results = drive.files().list(
    q="mimeType='application/vnd.google-apps.document' and name contains 'запрос'",
    fields='files(id, name, modifiedTime)'
).execute()
```

4. **Вставка текста в документ:**
```python
requests = [
    {
        'insertText': {
            'location': {'index': 1},
            'text': 'Новый текст\n'
        }
    }
]
docs.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
```

## Примеры
- `/gdocs read 1abc...xyz` - прочитать документ
- `/gdocs summary 1abc...xyz` - получить summary документа
- `/gdocs search AI News` - найти документы с "AI News"
