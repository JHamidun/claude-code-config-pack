---
name: tilda-bitrix-e2e-test
description: "E2E-тест лендингов Tilda с проверкой лидов в Битрикс24: находит формы, заполняет тестовыми данными, отправляет, сверяет лид в CRM; UTM/gclid, обход SmartCaptcha. Триггеры: «протестируй лендинг», «лиды доходят до Б24», «тест UTM через форму»."
metadata:
  version: 1.1.0
type: actionable
---

# Tilda + Bitrix24 E2E Test

Сквозной тест лендинга на Tilda: найти формы, заполнить тестовыми данными, отправить,
проверить, что лид доехал до Битрикс24 через webhook API.

## ⚠️ Тест льёт РЕАЛЬНЫЕ лиды в ЖИВУЮ CRM

Обходного пути нет: Tilda отправляет форму на свой сервер, тот дёргает боевой webhook.
Sandbox-режима у этой связки не существует. Значит:

- каждый прогон создаёт настоящие лид и контакт, их увидят менеджеры и заберёт в работу
  автоматика (автозвонок, рассылка, распределение на сотрудника);
- перед первым прогоном **предупреди тех, кто работает с воронкой**, и договорись,
  как помечать тестовые записи;
- делай тестовые данные однозначно опознаваемыми (см. Фазу 3): имя с пометкой,
  свой почтовый ящик, номер телефона, который не принадлежит живому человеку;
- после прогона **удали или переведи в JUNK** созданные лиды — иначе они попадут
  в отчётность по конверсии и испортят её;
- никогда не подставляй чужой номер телефона: по нему позвонят.

Хочешь без последствий — заведи отдельную тестовую воронку или отдельный портал
и направь вебхук туда.

## Что понадобится

| Нужно | Платно? | Где взять |
|---|---|---|
| Playwright MCP plugin | нет | браузерная автоматизация; `npx playwright install chromium` |
| Аккаунт Tilda с лендингом | да, тариф Tilda | свой сайт; чужой тестировать нельзя |
| Входящий вебхук Битрикс24 | нет | Битрикс24 → Разработчикам → Входящий вебхук, права `crm` |
| Настроенная интеграция Tilda → Б24 | нет | коннектор Data Receiver в Tilda |

Вебхук держи в переменных окружения, не в тексте навыка и не в коде:

```bash
export BITRIX_BASE_URL="https://your-portal.bitrix24.ru"
export BITRIX_WEBHOOK_PATH="rest/1/xxxxxxxxxxxx"   # выдаётся при создании вебхука
```

Обе строки можно дописать в `~/.claude/.credentials.master.env` (общий файл ключей;
заводится из `~/.claude/templates/.credentials.master.env.example`) — готовых
`BITRIX_*` в шаблоне нет, добавляешь сам.

**Ссылка вебхука = полный доступ к CRM без пароля**: по ней читают и меняют сделки,
контакты и лиды, причём отозвать её можно только удалив вебхук в портале. В git,
в скриншот и в чужой чат она попадать не должна.

## When to Use

- "протестируй лендинг" + Tilda + Bitrix24
- "проверь формы на сайте" with CRM verification
- "e2e тест заявок" on Tilda landings
- "проверь что лиды приходят в Б24"
- "тест UTM передачи" through Tilda forms

## Workflow

### Phase 1: Reconnaissance

1. Navigate to the landing via Playwright (`browser_navigate`)
2. Take a snapshot (`browser_snapshot`) to get the full DOM accessibility tree
3. Identify ALL forms by searching for:
   - **Popup forms**: anchors with `#popup:` prefix (e.g., `#popup:stepform`, `#popup:myform9`)
   - **Inline forms**: `<form>` elements in page body, identifiable by `#form{id}` anchors
   - **Step-forms**: multi-step wizard forms (Tilda `t-form__step` pattern)
4. Document each form's fields, types, and submission triggers

### Phase 2: UTM Setup

Append UTM parameters to URL before first navigation:

```
?utm_source=test_playwright&utm_medium=test_medium&utm_campaign=test_campaign&utm_content=test_content&utm_term=test_term&gclid=test_gclid
```

Tilda stores UTMs in `TILDAUTM` cookie on first page load. Navigate WITH UTM params
BEFORE opening any forms.

### Phase 3: Form Submission

For each form, generate unique test data. Главное требование — чтобы менеджер,
увидевший этот лид в CRM, за секунду понял, что это тест.

| Field | Pattern |
|-------|---------|
| Name | `ТЕСТ Playwright — {FormType}` — слово «ТЕСТ» первым, чтобы было видно в списке лидов |
| Email | `test+{formtype}+{landing}@{твой-домен}` — ящик, который ты читаешь сам |
| Phone | только свой номер. Если нужен заведомо ничей — бери код `+7 000 …`: он не выдан ни одному оператору, тогда как «красивые» `+7 999 000-00-00` вполне могут кому-то принадлежать |
| Text fields | Include test ID: `Playwright test ID: {LANDING}-{FORM}-{NNN}` |

#### Popup forms

1. Click the CTA button that triggers the popup (identified by `#popup:` href)
2. Wait for popup to appear (`.t-popup_show` class)
3. Fill fields using `browser_fill_form` or individual `browser_click` + `browser_type`
4. Submit via the submit button inside the popup

#### Step-forms (multi-step)

1. Open popup
2. For each step:
   - Fill current step's fields (radio buttons, text inputs, checkboxes)
   - Click "Далее" / "Next" to advance
3. Final step: fill contact fields (name, email, phone) + submit

#### Inline forms

1. Scroll to form section
2. Fill fields directly (no popup)
3. Submit

#### Key gotchas

Read `references/tilda-gotchas.md` for detailed solutions to common issues.

**Critical issues summary:**

- Radio buttons: click on label TEXT, not `<input>` (Tilda overlays `div.t-radio__indicator`)
- Privacy checkbox: use `browser_evaluate` with `checkbox.click()` via JS — clicking label opens /privacy link
- Scoping: when popup is open, both popup AND inline forms are in DOM — scope selectors to `.t-popup_show` container
- Checkbox groups: Tilda converts checkbox selections to hidden field values (comma-separated IDs)

### Phase 4: Captcha Handling

After 2-3 form submissions, Tilda triggers **Yandex SmartCaptcha**.

Detection: form response contains `needcaptcha:1` or captcha iframe appears.

Bypass sequence (это своя капча на своём сайте — обход чужой защиты сюда не относится):

1. Locate captcha container: `#captchaIframeBox`
2. Enter first iframe: `iframe[data-testid="checkbox-iframe"]` inside the container
3. Click the checkbox: `.CheckboxCaptcha-Anchor` or `input[type="checkbox"]`
4. Wait for verification (~2-3 seconds)
5. Re-submit the form

Для обхода по вложенным iframe нужен код в самой странице — это `browser_evaluate`
(инструмента `browser_run_code` в плагине Playwright НЕТ; сырой `page` даёт только
`browser_run_code_unsafe`). Передавай тело как функцию:

```javascript
// browser_evaluate → function:
() => {
const box = document.querySelector('#captchaIframeBox');
const outerFrame = box.querySelector('iframe');
const innerDoc = outerFrame.contentDocument;
const checkboxFrame = innerDoc.querySelector('iframe[data-testid="checkbox-iframe"]');
const checkboxDoc = checkboxFrame.contentDocument;
checkboxDoc.querySelector('.CheckboxCaptcha-Anchor').click();
}
```

### Phase 5: Bitrix24 Verification

Use `python` script via Bash (not WebFetch — encoding issues with Cyrillic).

```python
import os, sys, json, urllib.request, datetime
sys.stdout.reconfigure(encoding='utf-8')

BASE = f"{os.environ['BITRIX_BASE_URL'].rstrip('/')}/{os.environ['BITRIX_WEBHOOK_PATH'].strip('/')}"

# Отсечка — момент старта теста, а не «начало дня»: иначе в выборку попадут
# настоящие клиентские лиды, и тест «пройдёт» на чужих данных.
since = (datetime.datetime.now() - datetime.timedelta(minutes=30)).isoformat(timespec="seconds")

url = f"{BASE}/crm.lead.list.json?filter[>DATE_CREATE]={since}&order[ID]=DESC&select[]=*&select[]=UF_*"
leads = json.loads(urllib.request.urlopen(url).read())["result"]
for lead in leads:
    print(lead["ID"], lead.get("TITLE"), lead.get("STATUS_ID"), lead.get("CONTACT_ID"))
```

#### Verification checklist per lead

| Check | API field | Notes |
|-------|-----------|-------|
| Lead exists | `crm.lead.list` filter by date | Filter by DATE_CREATE > test start time |
| Contact data | `crm.contact.get?id={CONTACT_ID}` | Name, email, phone are in CONTACT entity, NOT in lead |
| Custom fields | Lead `UF_*` fields | Состав полей у каждого портала свой — см. `references/bitrix24-lead-fields.md` |
| UTM params | Lead `UTM_SOURCE`, `UTM_MEDIUM`, etc. | Often null — Tilda may not pass UTMs (см. Фазу 5.5) |
| GCLID | своё UF-поле | Requires Tilda form mapping |
| YM UID | своё UF-поле | Requires Yandex Metrika integration |
| Status | `STATUS_ID` | Check against `crm.status.list?filter[ENTITY_ID]=STATUS` |
| Form name | своё UF-поле | Tilda sends form title |

#### Important: Contact vs Lead data

Tilda→Б24 integration stores personal data (name, email, phone) in a linked **Contact**
entity, NOT directly in the lead. Always fetch `CONTACT_ID` from the lead, then query
`crm.contact.get`.

### Phase 5.5: UTM Payload Diagnosis (Deep Debug)

If UTMs are missing in Б24, diagnose WHERE the data is lost by intercepting the actual
XHR payload:

1. Monkey-patch `XMLHttpRequest.prototype.send` before form submission
2. Call `window.tildaForm.send(form, btn, formType, formKey)` directly
3. Capture the POST body sent to `forms.tildaapi.com/procces/`

```javascript
// In page.evaluate():
const origOpen = XMLHttpRequest.prototype.open;
const origSend = XMLHttpRequest.prototype.send;
XMLHttpRequest.prototype.open = function(m, u) { this.__url = u; return origOpen.apply(this, arguments); };
XMLHttpRequest.prototype.send = function(d) {
  if (this.__url && this.__url.includes('procces')) {
    console.log('CAPTURED:', d); // full POST body
  }
  return origSend.apply(this, arguments);
};
```

#### Known Tilda UTM architecture (проверено 2026-03)

Tilda form JS (`tilda-forms-1.0.min.js`) does NOT send UTMs as dedicated fields. Instead:

| Payload field | Contains UTM? | Format |
|---|---|---|
| `tildaspec-cookie` | YES — full browser cookies as string | `...TILDAUTM=utm_source%3Dfoo%7C%7C%7Cutm_medium%3Dbar%7C%7C%7C...` |
| `tildaspec-referer` | YES — full page URL with query params | `https://site.com/?utm_source=foo&gclid=bar` |
| `utm_source`, `utm_medium`, etc. | NO — these fields DO NOT EXIST in payload | — |
| `gclid` | NO — not extracted from URL | — |
| `_ym_uid` | Inside `tildaspec-cookie` only | `_ym_uid=12345...` |

**Root cause**: Tilda server-side (`forms.tildaapi.com`) receives UTM data embedded in
`tildaspec-cookie` and `tildaspec-referer` but does NOT extract/parse them into separate
fields when forwarding to the Bitrix24 webhook. The Bitrix24 Data Receiver connector must
be configured to map these.

#### Fix: add hidden inputs for gclid and _ym_uid

Add custom JS in Tilda page settings → "Custom code before </body>":

```html
<script>
document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('form').forEach(function(form) {
    // gclid from URL
    var params = new URLSearchParams(window.location.search);
    var gclid = params.get('gclid');
    if (gclid) {
      var inp = document.createElement('input');
      inp.type = 'hidden'; inp.name = 'gclid'; inp.value = gclid;
      form.appendChild(inp);
    }
    // _ym_uid from cookie
    var ymMatch = document.cookie.match(/_ym_uid=(\d+)/);
    if (ymMatch) {
      var inp2 = document.createElement('input');
      inp2.type = 'hidden'; inp2.name = '_ym_uid'; inp2.value = ymMatch[1];
      form.appendChild(inp2);
    }
  });
});
</script>
```

Then map `gclid` and `_ym_uid` to your own UF-fields in Tilda → Б24 connector settings.

### Phase 6: Report

Generate a summary table:

| Form | Landing | Lead ID | Name | Email | Phone | Custom Fields | UTMs | Status |
|------|---------|---------|------|-------|-------|--------------|------|--------|

Mark each cell with pass/fail indicator.

### Phase 7: Cleanup (не пропускать)

```python
# Удалить тестовые лиды. Перепроверь список ID глазами ПЕРЕД удалением —
# crm.lead.delete необратим и по ошибке снесёт настоящую заявку.
for lead_id in TEST_LEAD_IDS:
    urllib.request.urlopen(f"{BASE}/crm.lead.delete.json?id={lead_id}").read()
```

Нет прав на удаление — переведи в `JUNK` через `crm.lead.update` и подпиши комментарием
«Playwright e2e», чтобы лид не попал в статистику как настоящий.

## IDN Domain Handling

Кириллические домены (`.рф`) требуют punycode. Playwright конвертирует сам,
WebFetch — нет: для навигации всегда Playwright.

Пример: `пример.рф` → `xn--e1afmkfd.xn--p1ai`

## Lead Status Reference

Статусы у каждого портала свои и **их ID переиспользуют** при переименовании воронки.
Никогда не бери названия из документации — тяни живой список перед проверкой:

```
crm.status.list.json?filter[ENTITY_ID]=STATUS
```

Системные, которые есть везде:

- `NEW` = Новый лид
- `IN_PROCESS` = В работе
- `PROCESSED` = Обработан
- `CONVERTED` = Качественный лид
- `JUNK` = Некачественный лид
- `UC_*` = кастомные стадии конкретного портала

## References

- `references/tilda-gotchas.md` — решения типовых проблем автоматизации форм Tilda
- `references/bitrix24-lead-fields.md` — поля лида и как выяснить состав UF-полей своего портала
