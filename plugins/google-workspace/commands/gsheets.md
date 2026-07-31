---
description: "Google Sheets: чтение, запись, анализ таблиц (OAuth для личных, service account + gspread для расшаренных). Триггеры: «google sheets», «гугл таблица», «прочитай таблицу», «запиши в таблицу», «анализ таблицы»."
argument-hint: "[read <sheet_id> [лист] | analyze <sheet_id> | write <sheet_id> <данные> | search <запрос>]"
---

# Google Sheets Operations

/gsheets - Работа с Google Таблицами

## Описание
Чтение, запись и анализ данных в Google Sheets.

## Использование
```
/gsheets read <sheet_id>           - Прочитать таблицу
/gsheets read <sheet_id> <лист>    - Прочитать конкретный лист
/gsheets analyze <sheet_id>        - Анализ данных таблицы
/gsheets write <sheet_id> <данные> - Записать данные
/gsheets search <запрос>           - Найти таблицы
```

## Инструкции для Claude

### Вариант 1: OAuth (для личных таблиц)
```python
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

with open('${HOME}/.claude/google_oauth_token.json', 'r') as f:
    token_data = json.load(f)
creds = Credentials.from_authorized_user_info(token_data)
sheets = build('sheets', 'v4', credentials=creds)
```

### Вариант 2: Service Account (для расшаренных таблиц)
```python
import gspread
from google.oauth2.service_account import Credentials

creds = Credentials.from_service_account_file(
    '${HOME}/.claude/google_service_account.json',
    scopes=['https://www.googleapis.com/auth/spreadsheets']
)
client = gspread.authorize(creds)
sheet = client.open_by_key(sheet_id)
```

### Операции

**Чтение данных:**
```python
# С Google API
result = sheets.spreadsheets().values().get(
    spreadsheetId=sheet_id,
    range='Sheet1!A1:Z100'
).execute()
values = result.get('values', [])

# С gspread
worksheet = sheet.sheet1  # или sheet.worksheet('Название')
data = worksheet.get_all_records()  # как list of dicts
# или
data = worksheet.get_all_values()  # как list of lists
```

**Запись данных:**
```python
# Одна ячейка
worksheet.update('A1', 'Значение')

# Диапазон
worksheet.update('A1:C3', [
    ['A1', 'B1', 'C1'],
    ['A2', 'B2', 'C2'],
    ['A3', 'B3', 'C3']
])

# Добавить строку в конец
worksheet.append_row(['Col1', 'Col2', 'Col3'])
```

**Информация о таблице:**
```python
spreadsheet = sheets.spreadsheets().get(spreadsheetId=sheet_id).execute()
title = spreadsheet['properties']['title']
sheet_names = [s['properties']['title'] for s in spreadsheet['sheets']]
```

## Примеры
- `/gsheets read 1abc...xyz` - прочитать первый лист
- `/gsheets read 1abc...xyz "Продажи"` - прочитать лист "Продажи"
- `/gsheets analyze 1abc...xyz` - анализ данных с выводами
