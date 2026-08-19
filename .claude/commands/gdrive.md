---
description: "Google Drive: что в папке, поиск файла, скачать файл или папку, залить. Триггеры: «google drive», «гугл диск», «найди файл на диске», «скачай с диска», «расшаренная папка». НЕ Яндекс.Диск → отдельный навык под Яндекс (в пак не входит). Полный набор Workspace → skill google-workspace."
argument-hint: "[ls <id|ссылка> | find <запрос> | get <id> -o <папка> | pull <id> -o <папка>]"
---

# /gdrive

Рабочий клиент — `~/.claude/tools/gdrive_client.py`.

```bash
python ~/.claude/tools/gdrive_client.py ls <id_или_ссылка> [--recursive]
python ~/.claude/tools/gdrive_client.py find "вебинар"
python ~/.claude/tools/gdrive_client.py get <id_файла> -o ./куда/
python ~/.claude/tools/gdrive_client.py pull <id_папки> -o ./куда/ --ext mp4,m4a --min-mb 5
python ~/.claude/tools/gdrive_upload.py upload <локальная_папка> <имя_на_диске>
```

Принимает ссылку целиком — идентификатор вынимается сам. Права — из
`~/.claude/google_oauth_token.json` (скоуп `drive`, чтение и запись).

За подробностями — Skill `google-workspace`.

> Здесь лежал inline-код `files().list()` БЕЗ `supportsAllDrives` и
> `includeItemsFromAllDrives`. Без этих двух флагов API молча скрывает всё, что
> лежит на общих дисках: папка выглядит пустой, хотя файлы в ней есть. В клиенте
> флаги проставлены — и в списке, и при скачивании. Код удалён.
