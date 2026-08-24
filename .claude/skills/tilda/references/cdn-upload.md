# Tilda CDN — загрузка изображений

## Endpoint

```
POST https://upload.tildacdn.com/api/upload/
Content-Type: multipart/form-data
```

## Параметры

| Поле | Значение | Описание |
|------|----------|----------|
| `publickey` | env `TILDA_PUBLIC_KEY` (Настройки проекта → API) | публичный ключ проекта |
| `uploadkey` | env `TILDA_UPLOAD_KEY` (Настройки проекта → API) | ключ загрузки |
| `acceptedFiles` | `image/*` | тип принимаемых файлов |
| `files` | binary | сам файл (FormData с именем `files`) |

**Где взять ключи проекта:** на странице редактора Tilda в HTML встроен скрипт с этими константами. Открой `tildauploadwindow` или ищи `publickey` в исходниках страницы редактора Feed.

```javascript
// В консоли страницы редактора:
const publickey = document.body.innerHTML.match(/publickey['":\s]+["']([^"']+)/)?.[1];
const uploadkey = document.body.innerHTML.match(/uploadkey['":\s]+["']([^"']+)/)?.[1];
```

## Headers (важно)

```
Origin: https://feeds.tilda.ru
```

Без `Origin` сервер может вернуть 403.

## Response

```json
{
  "result": [
    {
      "cdnUrl": "https://static.tildacdn.com/tild6432-3065-4133-a166-623034653564/2025-04-26-vorkshop-.webp",
      "fileName": "2025-04-26-vorkshop-.webp",
      "size": 53242,
      ...
    }
  ]
}
```

`cdnUrl` — итоговая ссылка для использования в `image` / `mediadata` поля поста или в HTML тела.

## Поддерживаемые форматы

✅ webp, jpg, jpeg, png, gif, svg, bmp
✅ mp4, webm, mov (видео)
❌ pdf, doc, xls, txt — отклоняются с ошибкой

**Альтернатива для документов:** Yandex Disk + публикация (см. `pages-api.md`).

## Оптимальный размер

Для карточек Feed-блока 897:
- **Соотношение:** 16:9
- **Разрешение:** 1200×675 webp
- **Качество webp:** 85-90
- **Вес:** 50-200 KB

```python
from PIL import Image
img = Image.open('cover.png').convert('RGB').resize((1200, 675), Image.LANCZOS)
img.save('cover.webp', 'WEBP', quality=90)
```

## Python пример загрузки

```python
import requests
from pathlib import Path

import os
PUBLIC = os.getenv('TILDA_PUBLIC_KEY')
UPLOAD = os.getenv('TILDA_UPLOAD_KEY')

def upload_to_tilda(local_path: Path) -> str:
    with open(local_path, 'rb') as f:
        files = {'files': (local_path.name, f, 'image/webp')}
        data = {'publickey': PUBLIC, 'uploadkey': UPLOAD, 'acceptedFiles': 'image/*'}
        r = requests.post(
            'https://upload.tildacdn.com/api/upload/',
            data=data, files=files,
            headers={'Origin': 'https://feeds.tilda.ru'},
            timeout=60,
        )
    resp = r.json()
    if isinstance(resp, dict) and resp.get('result'):
        return resp['result'][0].get('cdnUrl')
    raise RuntimeError(f'Upload failed: {resp}')

url = upload_to_tilda(Path('cover.webp'))
print(url)  # https://static.tildacdn.com/tild.../cover.webp
```

## Кэширование на CDN

- Один раз загруженный файл получает уникальный `tild_<hex>` префикс — он навсегда
- Замена файла = новый upload + новый URL
- На стороне сайта Tilda кэширует обложки агрессивно — после правки `image` поста подожди 1-5 минут или сделай Ctrl+Shift+R

## Известные публичные ключи проектов

| Проект | publickey | uploadkey |
|--------|-----------|-----------|
| основной проект | env `TILDA_PUBLIC_KEY` | env `TILDA_UPLOAD_KEY` |
| второй проект | (получи через `document.body.innerHTML.match(/publickey/)` на странице редактора) | — |

**Внимание:** `publickey` — публичный, безопасно держать в коде. `uploadkey` — тоже публичный, привязан к проекту. Любой человек с этими двумя ключами может загружать на ваш CDN — это by design Tilda.

## Bulk upload N файлов

```python
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

files = list(Path('covers/').glob('*.webp'))
with ThreadPoolExecutor(max_workers=6) as ex:
    urls = list(ex.map(upload_to_tilda, files))
mapping = dict(zip([f.stem for f in files], urls))
```

## Запросы из Python без логина

CDN-загрузки работают **без авторизации** — нужны только `publickey` и `uploadkey`. Это удобно для серверных скриптов, не требует session cookies. Но для использования URL в постах через `posts_Edit` всё равно нужна авторизация на feeds.tilda.ru.
