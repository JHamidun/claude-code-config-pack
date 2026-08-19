---
description: "Google Docs: прочитать документ, найти документ по названию, дописать текст. Триггеры: «google docs», «гугл документ», «прочитай документ», «саммари документа». Полный набор Workspace → skill google-workspace."
argument-hint: "[read <id|ссылка> | search <запрос> | append <id> --text <текст>]"
---

# /gdocs

Рабочий код — в навыке `google-workspace`, скрипт
`~/.claude/skills/google-workspace/scripts/gdocs_client.py`.

```bash
python ~/.claude/skills/google-workspace/scripts/gdocs_client.py read <id_или_ссылка>
python ~/.claude/skills/google-workspace/scripts/gdocs_client.py read <id> --limit 2000
python ~/.claude/skills/google-workspace/scripts/gdocs_client.py search "резюме встреч"
python ~/.claude/skills/google-workspace/scripts/gdocs_client.py append <id> --text "строка" --yes
```

Принимает ссылку целиком. Права берутся из `~/.claude/google_oauth_token.json`:
у токена единственный скоуп `drive`, и Docs API на нём работает — проверено.

За подробностями (таблицы в документах, разграничение токенов, что делать при 404)
— Skill `google-workspace`.

> Раньше здесь лежал inline-код работы с Docs API. Он был рабочим, но не проверялся
> ничем: тела команд линтер связности не покрывает. Код перенесён в скрипт навыка и
> прогнан на живом документе.
