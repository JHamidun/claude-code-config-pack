# Google Workspace CLI (`gws`) — оценка vs наш стек

> Референс-оценка находки `googleworkspace/cli` (из @usefulrepa). **Вердикт: ДОПОЛНИТЬ позже, не мигрировать сейчас.** Наши 14 `g*`-команд (OAuth-скрипты) остаются каноном. Ничего не заменяем.

## Что это
- Официальный (но **НЕ officially supported**) CLI Google от команды googleworkspace. Rust, npm `@googleworkspace/cli`, бинарь `gws`.
- Команды **генерируются из Google Discovery Service** → авто-подхват новых эндпоинтов.
- Вывод **structured JSON** (+ NDJSON стриминг для пагинации), `--page-all`, `--dry-run`, helper-команды `+send`/`+agenda`/`+upload`.
- Model Armor (детект prompt-injection в ответах) — бонус к нашему trust-boundary правилу.
- Статус на 2026-03: **v0.22.5, pre-1.0, breaking changes до 1.0**. Testing-mode OAuth (unverified app) ограничен ~25 scopes.

## Установка (когда решим внедрять)
```bash
npm install -g @googleworkspace/cli   # или brew install googleworkspace-cli
gws auth setup && gws auth login       # нужен свой OAuth-клиент + браузер (интерактив)
# альтернатива без OAuth-флоу: GOOGLE_WORKSPACE_CLI_TOKEN=<токен с нужными scopes>
```
Из вашего региона: гео-блока нет (googleapis.com), прокси/платный ключ НЕ нужны. Единственная трата — разовый OAuth-флоу (нужен браузер юзера, в non-interactive не завершить).

## Покрытие vs наши команды
| Наша команда | API | gws покрывает? |
|---|---|---|
| gmail | Gmail | ✅ |
| gsheets | Sheets | ✅ |
| gdocs | Docs | ✅ |
| gcalendar | Calendar | ✅ |
| gdrive | Drive | ✅ |
| gchat | Chat | ✅ |
| gtasks | Tasks | ✅ |
| gmeet | Meet | ⚠️ частично (через Calendar/Events; отдельного Meet REST нет) |
| gcontacts | People API | ❌ не Workspace-core |
| gsearch-console | Search Console | ❌ |
| ganalytics | GA4 Data API | ❌ |
| gads | Google Ads API | ❌ |
| gtranslate | Cloud Translation | ❌ (GCP) |
| gcloud-storage | GCS | ❌ (GCP → `gcloud`) |
| — | Admin, Apps Script, Model Armor | gws-only (у нас нет) |

**Итого:** gws закрывает 7/14 (Workspace-core). Остальные 7 (Ads/GA4/Search Console/Contacts/Translate/GCS/Meet) остаются на наших скриптах в любом случае.

## Рекомендация: ДОПОЛНИТЬ (не мигрировать, не сейчас)
- **Оставить каноном** наши OAuth-скрипты: работают на уже авторизованном `google_oauth_token.json` + service account (shared sheets), покрывают все 14 incl. не-Workspace, ноль миграции.
- **Плюсы gws для агента:** чистый JSON (Claude не пишет Python каждый вызов), Discovery-авто-обновление, Model Armor, авто-пагинация. Ценно для read-heavy JSON-запросов к Workspace-7.
- **Почему не мигрировать сейчас:** (1) pre-1.0 volatile, не supported Google; (2) разовая OAuth-переавторизация + свой OAuth-клиент; (3) testing-mode ~25 scope cap при нашем зоопарке API; (4) половину команд (не-Workspace) всё равно не заменит.
- **Триггер к внедрению:** gws выходит на ~1.0 ИЛИ появляется задача, где нужен именно чистый JSON от Workspace-API массово. Тогда — разовый `gws auth setup` юзером, `gws` как ОПЦИОНАЛЬНЫЙ быстрый путь рядом с командами, не вместо.

**Не дубль** (даёт JSON/Discovery/Model Armor), но и **не замена** — слишком pre-1.0 + auth-миграция.
