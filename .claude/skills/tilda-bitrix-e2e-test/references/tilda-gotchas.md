# Tilda Form Automation Gotchas

> Сниппеты ниже написаны на сыром Playwright API (`page.click`, `page.evaluate`,
> `page.locator`). Инструмент этого навыка — **Playwright MCP plugin**, а он объекта
> `page` напрямую не даёт. Перевод: `page.click(sel)` → `browser_click` по ref из
> снапшота; `page.evaluate(fn)` → `browser_evaluate` с той же функцией;
> `page.locator(...)` и любой другой сырой код — только внутри
> `browser_run_code_unsafe(async (page) => { ... })`. Как есть не вставляются.

## 1. Radio Buttons — Click Intercepted

**Problem**: Tilda wraps radio inputs with custom `div.t-radio__indicator` overlay. Clicking `<input type="radio">` is intercepted.

**Solution**: Click on the label TEXT element, not the input:
```javascript
// Wrong:
page.click('input[type="radio"][value="corporate"]');
// Right:
page.click('text=Корпоративная книга');
```

## 2. Privacy Checkbox — Opens Link Instead of Toggling

**Problem**: Checkbox label contains `<a href="/privacy">`, clicking the label navigates to /privacy page.

**Solution**: Use direct DOM manipulation via `page.evaluate()`:
```javascript
await page.evaluate(() => {
  const checkbox = document.querySelector('.t-popup_show .t-checkbox__control');
  checkbox.click();
});
```

## 3. Multiple Matching Fields When Popup Is Open

**Problem**: When a popup form is open, both popup AND inline form fields exist in DOM. Selectors like `textbox "Email"` match multiple elements.

**Solution**: Scope selectors to the visible popup container:
```javascript
const popup = page.locator('.t-popup_show');
await popup.locator('input[name="Email"]').fill('test@example.com');
```

Or use `browser_fill_form` with specific element refs from snapshot.

## 4. Yandex SmartCaptcha After Multiple Submissions

**Problem**: After 2-3 form submissions from the same IP, Tilda returns `needcaptcha:1` and shows Yandex SmartCaptcha.

**Detection**: Captcha iframe `#captchaIframeBox` appears after form submit.

**Solution** (речь о капче на СВОЁМ сайте, который ты и тестируешь):
navigate nested iframes to click the "I'm not a robot" checkbox:
```javascript
// Structure: #captchaIframeBox > iframe > iframe[data-testid="checkbox-iframe"] > .CheckboxCaptcha-Anchor
const captchaBox = document.querySelector('#captchaIframeBox');
const outerIframe = captchaBox.querySelector('iframe');
const outerDoc = outerIframe.contentDocument;
const innerIframe = outerDoc.querySelector('iframe[data-testid="checkbox-iframe"]');
const innerDoc = innerIframe.contentDocument;
innerDoc.querySelector('.CheckboxCaptcha-Anchor').click();
```

Wait 2-3 seconds after click, then re-submit the form.

## 5. Tilda Form Submission Endpoint

Forms submit to `https://forms.tildaapi.com/procces/` (note: "procces" not "process" — Tilda typo).

## 6. Step-Form Navigation

Step-forms use `.t-form__step` containers. Each step has a "Далее" (Next) button. The final step has the submit button.

To advance: click the step's "Next" button, wait for next step to become visible.

## 7. Checkbox Arrays

Tilda converts selected checkboxes into a hidden field value (comma-separated IDs).
In Bitrix24 these arrive as array fields: `UF_SOME_MULTI: [2336, 2337]`.
Сравнивай их как множества — порядок элементов не гарантирован.

## 8. UTM Cookie (TILDAUTM)

Tilda stores UTM params from URL in a `TILDAUTM` cookie on first page load. This cookie is supposed to be included when the form is submitted. If UTMs are not reaching Bitrix24, verify:
1. The cookie is set (check via DevTools)
2. Tilda→Б24 integration maps cookie values to UTM fields

## 9. IDN Domains

WebFetch tool does NOT support internationalized domain names (кириллические `.рф`).
Always use Playwright for navigation.

Punycode conversion: `пример.рф` → `xn--e1afmkfd.xn--p1ai`

## 10. Windows Bash + Python Encoding

When running Python scripts via Bash on Windows to query Bitrix24 API (Cyrillic responses), always add:
```python
import sys
sys.stdout.reconfigure(encoding='utf-8')
```

Also handle `None` values before slicing: `(data.get('COMMENTS') or '')[:200]`
