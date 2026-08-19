---
description: "Google Sheets: прочитать таблицу, записать, найти таблицу, посмотреть листы. Триггеры: «google sheets», «гугл таблица», «прочитай таблицу», «запиши в таблицу», «анализ таблицы». Полный набор Workspace → skill google-workspace."
argument-hint: "[info <id> | read <id> [--tab лист] | write <id> --range … --values … | search <запрос>]"
---

# /gsheets

Рабочий код — в навыке `google-workspace`, скрипт
`~/.claude/skills/google-workspace/scripts/gsheets_client.py`.

```bash
python ~/.claude/skills/google-workspace/scripts/gsheets_client.py info <id_или_ссылка>
python ~/.claude/skills/google-workspace/scripts/gsheets_client.py read <id> --tab "Сводная" --limit 20
python ~/.claude/skills/google-workspace/scripts/gsheets_client.py search "оплаты"
python ~/.claude/skills/google-workspace/scripts/gsheets_client.py write <id> --range "'Лист1'!A1" --values '[["a","b"]]' --yes
```

Два пути доступа, оба рабочие: OAuth (`~/.claude/google_oauth_token.json`, скоуп
`drive` — Sheets API на нём проверен) и служебный ключ через флаг `--sa` — для
таблиц, расшаренных на робота, а не на человека. Запись требует `--yes`.

За подробностями — Skill `google-workspace`.

> Раньше здесь лежал inline-код (google-api + gspread). Оба пути были рабочими, но
> непроверяемыми: тела команд линтер не покрывает. Код перенесён в скрипт навыка,
> gspread-путь заменён на тот же Sheets API со служебным ключом — одна кодовая
> ветка вместо двух.
