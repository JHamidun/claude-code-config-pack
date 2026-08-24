---
description: "Google Cloud Storage: бакеты, объекты, upload/download файлов. Триггеры: «GCS», «бакет google», «залей в cloud storage»."
argument-hint: "[buckets | list <bucket> | upload <bucket> <file> | download <bucket> <object>]"
---

# Google Cloud Storage Operations

/gcloud-storage - Работа с Google Cloud Storage

## Описание
Управление бакетами и объектами в Google Cloud Storage.

## Использование
```
/gcloud-storage buckets                    - Список бакетов
/gcloud-storage list <bucket>              - Файлы в бакете
/gcloud-storage upload <bucket> <file>     - Загрузить файл
/gcloud-storage download <bucket> <object> - Скачать файл
```

## Инструкции для Claude

### Вариант 1: REST API (через googleapiclient)

1. **Загрузи credentials:**
```python
import os
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import io

with open(os.path.expanduser('~/.claude/google_oauth_token.json'), 'r') as f:
    token_data = json.load(f)
creds = Credentials.from_authorized_user_info(token_data)
storage = build('storage', 'v1', credentials=creds)
```

2. **Список бакетов:**
```python
buckets = storage.buckets().list(project='your-gcp-project-id').execute()
for b in buckets.get('items', []):
    print(f"{b['name']} | {b['location']} | created: {b['timeCreated']}")
```

3. **Файлы в бакете:**
```python
objects = storage.objects().list(
    bucket='my-bucket',
    prefix='uploads/',  # опциональный фильтр по папке
    maxResults=50
).execute()
for obj in objects.get('items', []):
    size_mb = int(obj.get('size', 0)) / (1024 * 1024)
    print(f"{obj['name']} | {size_mb:.1f} MB | {obj['contentType']}")
```

4. **Загрузить файл:**
```python
import os
media = MediaFileUpload(os.path.expanduser('~/report.pdf'), mimetype='application/pdf')
obj = storage.objects().insert(
    bucket='my-bucket',
    name='reports/report-2026-03.pdf',
    media_body=media
).execute()
print(f"Загружен: {obj['name']} ({obj['size']} bytes)")
```

5. **Скачать файл:**
```python
import os
request = storage.objects().get_media(bucket='my-bucket', object='reports/report.pdf')
fh = io.FileIO(os.path.expanduser('~/Downloads/report.pdf'), 'wb')
downloader = MediaIoBaseDownload(fh, request)
done = False
while not done:
    status, done = downloader.next_chunk()
    print(f"Download {int(status.progress() * 100)}%")
```

6. **Удалить объект:**
```python
storage.objects().delete(bucket='my-bucket', object='old-file.txt').execute()
```

### Вариант 2: Client Library (рекомендуется для сложных операций)

```bash
pip install google-cloud-storage
```

```python
import os
from google.cloud import storage as gcs

client = gcs.Client(project='your-gcp-project-id', credentials=creds)

# Список бакетов
for bucket in client.list_buckets():
    print(bucket.name)

# Загрузка
bucket = client.bucket('my-bucket')
blob = bucket.blob('uploads/file.txt')
blob.upload_from_filename(os.path.expanduser('~/file.txt'))

# Скачивание
blob = bucket.blob('uploads/file.txt')
blob.download_to_filename(os.path.expanduser('~/Downloads/file.txt'))

# Signed URL (временная ссылка, 1 час)
from datetime import timedelta
url = blob.generate_signed_url(expiration=timedelta(hours=1))
print(url)
```

## Примеры
- `/gcloud-storage buckets` - все бакеты проекта
- `/gcloud-storage list my-bucket` - файлы в бакете
- `/gcloud-storage upload my-bucket report.pdf` - загрузить файл
- `/gcloud-storage download my-bucket data.csv` - скачать файл
