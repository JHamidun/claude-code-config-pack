---
description: "Google Cloud Translation v2: перевод текста и батчей, определение языка. Триггеры: «переведи через google», «определи язык». Качественный перевод → /translate."
argument-hint: "[translate <текст> <язык> | detect <текст> | languages]"
---

# Google Cloud Translation Operations

/gtranslate - Работа с Google Cloud Translation API

## Описание
Перевод текста, определение языка и список поддерживаемых языков через Translation API v2.

## Использование
```
/gtranslate translate <текст> <язык>  - Перевести текст
/gtranslate detect <текст>            - Определить язык
/gtranslate languages                 - Поддерживаемые языки
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
translate = build('translate', 'v2', credentials=creds)
```

2. **Перевести текст:**
```python
result = translate.translations().list(
    q='Hello, how are you?',
    target='ru'
).execute()
for t in result.get('translations', []):
    print(f"Перевод: {t['translatedText']}")
    print(f"Исходный язык: {t.get('detectedSourceLanguage', 'указан')}")
```

3. **Перевести с указанием исходного языка:**
```python
result = translate.translations().list(
    q='Привет, мир!',
    source='ru',
    target='en'
).execute()
print(result['translations'][0]['translatedText'])
```

4. **Перевести несколько текстов:**
```python
result = translate.translations().list(
    q=['Привет', 'Как дела?', 'Спасибо'],
    target='pt'
).execute()
for t in result['translations']:
    print(t['translatedText'])
```

5. **Определить язык:**
```python
result = translate.detections().list(
    q='Bonjour le monde'
).execute()
for detection in result['detections']:
    for d in detection:
        print(f"Язык: {d['language']} | confidence: {d['confidence']:.2f}")
```

6. **Список поддерживаемых языков:**
```python
result = translate.languages().list(target='ru').execute()
for lang in result['languages']:
    code = lang['language']
    name = lang.get('name', '')
    print(f"{code}: {name}")
```

## Популярные коды языков
- `ru` - русский
- `en` - английский
- `pt` - португальский
- `es` - испанский
- `de` - немецкий
- `fr` - французский
- `zh` - китайский
- `ja` - японский
- `ar` - арабский
- `ko` - корейский

## Примеры
- `/gtranslate translate "Meeting at 3pm" ru` - перевести на русский
- `/gtranslate detect "Guten Morgen"` - определить язык
- `/gtranslate languages` - все поддерживаемые языки
