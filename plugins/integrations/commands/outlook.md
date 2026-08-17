---
description: "РАБОЧАЯ почта компании you@company.example через локальный Outlook (COM): входящие, непрочитанные, поиск, чтение, отправка, папки. Триггеры: «outlook», «рабочая почта», «письма компании», «рабочие треды», «exchange». Личная почта → /gmail. Полный набор Workspace → skill google-workspace."
argument-hint: "[inbox | unread | search <запрос> | read <номер|EntryID> | folders | send --to … --subject …]"
---

# /outlook

Рабочий путь — локальный Outlook через COM, скрипт
`~/.claude/skills/google-workspace/scripts/outlook_local.py`. Приложение стоит на
машине, учётная запись настроена, пароль не нужен. Проверено: 5166 писем.

```bash
python ~/.claude/skills/google-workspace/scripts/outlook_local.py inbox --limit 10
python ~/.claude/skills/google-workspace/scripts/outlook_local.py unread
python ~/.claude/skills/google-workspace/scripts/outlook_local.py search "конференция" --days 60
python ~/.claude/skills/google-workspace/scripts/outlook_local.py search "лендинг" --field body
python ~/.claude/skills/google-workspace/scripts/outlook_local.py read 2 --full
python ~/.claude/skills/google-workspace/scripts/outlook_local.py folders
python ~/.claude/skills/google-workspace/scripts/outlook_local.py send --to кому@x.ru --subject "Тема" --body "Текст" --yes
```

Отправка требует `--yes` — без него письмо собирается и показывается, но не уходит.

За граблями (DASL-поиск, поиск по имени вместо адреса) — Skill `google-workspace`.

> **Сетевой путь `exchangelib` на mail.company.example НЕ РАБОТАЕТ — не пробовать.**
> Падает `RecursionError` в urllib3 ещё до авторизации, воспроизводится стабильно,
> пароль ни при чём. Здесь лежало 150 строк такого кода — удалены.
>
> Оттуда же был удалён пример поиска `items.Restrict("[Subject] like '%счёт%'")`:
> Outlook отвергает его («Условие неверно»). Рабочий вариант — DASL
> `@SQL="urn:schemas:httpmail:subject" like '%…%'`, он зашит в скрипт.
