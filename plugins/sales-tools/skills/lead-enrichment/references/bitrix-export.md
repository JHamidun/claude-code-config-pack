# Bitrix24 export → bitrix_data.json

Mode B step 2. The match/aggregate scripts expect a single `bitrix_data.json`. Produce it via
the `bitrix24` skill (REST/webhook). Pull once, cache, reuse — the export is the slow part.

## Required shape

```json
{
  "companies":            {"<cid>": {"TITLE": "...", "ASSIGNED_BY_ID": "..."}},
  "company_ids_to_inn":   {"<cid>": "7707083893"},
  "deals_by_company":     {"<cid>": [{"ID","TITLE","CATEGORY_ID","STAGE_ID","OPPORTUNITY","DATE_CREATE","ASSIGNED_BY_ID"}]},
  "contacts_by_company":  {"<cid>": [{"ID","NAME","LAST_NAME","SECOND_NAME","POST","PHONE":[{"VALUE":""}],"EMAIL":[{"VALUE":""}]}]},
  "deal_activities":      {"<deal_id>": [{"CREATED","TYPE_ID","SUBJECT","COMPLETED"}]},
  "activities_by_company":{"<cid>": [{"CREATED","TYPE_ID","SUBJECT","COMPLETED"}]},
  "timeline_by_company":  {"<cid>": [{"CREATED","COMMENT"}]},
  "categories":           {"<category_id>": "Воронка B2B"},
  "stages":               {"<STAGE_ID>": "Назначена встреча"},
  "users":                {"<uid>": {"name": "Имя Фамилия"}}
}
```

## How to pull (bitrix24 skill)

- `crm.company.list` (select TITLE, ASSIGNED_BY_ID, UF_* INN field) → `companies` + `company_ids_to_inn`.
  INN often lives in a user field (e.g. `UF_CRM_INN`) or the requisite (`crm.requisite.list` → RQ_INN). Map cid→INN from whichever the portal uses.
- `crm.deal.list` by COMPANY_ID → `deals_by_company`.
- `crm.contact.list` + `crm.company.contact.items.get` → `contacts_by_company` (PHONE/EMAIL are multifields → `crm.contact.list` with `select:["PHONE","EMAIL"]`).
- `crm.activity.list` by OWNER (deal/company) → `deal_activities` / `activities_by_company`.
- `crm.timeline.comment.list` → `timeline_by_company`.
- `crm.dealcategory.list` + `crm.status.list` (ENTITY_ID=DEAL_STAGE_*) → `categories` / `stages`.
- `user.get` → `users` (id → name).

Use **batch** (`batch` method, 50 calls/request) to stay under rate limits on large portals.

## ACT_TYPES (TYPE_ID → label)

`1 Звонок · 2 Встреча · 3 Задача · 4 Email · 6 СМС · 7 Чат` (used by `bitrix_aggregate.py`).

## Base URL

Pass `--base https://your-portal.bitrix24.ru` to aggregate/build scripts to make card URLs clickable
(`/crm/company/details/<cid>/`, `/crm/contact/details/<cid>/`).
