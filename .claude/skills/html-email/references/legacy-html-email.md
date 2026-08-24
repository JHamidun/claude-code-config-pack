<!-- Расширенный материал навыка 'html-email': таблицы, рецепты и антипаттерны,
     которые не поместились в SKILL.md. Канон — ../SKILL.md, он читается всегда;
     этот файл открывается по ссылке из него, когда нужны подробности. -->

---
name: html-email
description: HTML-письма с табличной разметкой для Outlook / Gmail / Apple Mail / mobile clients. Не современный CSS — старая школа: tables, inline styles, fallbacks. Чтобы письмо не разваливалось у 30% получателей.
when_to_use: Юзер просит «email-newsletter», «письмо рассылки», «marketing email», «transactional email». Не для in-app uploaded HTML — только для **отправки** через email-сервис.
---

# HTML email

Email — это HTML 1999-го года. Outlook рендерит через Word engine. Gmail режет CSS. Mobile клиенты переопределяют. Никакого Flexbox или Grid.

## Что НЕ работает в email

- ❌ CSS Flexbox / Grid (Outlook 2007-2019 — не работают)
- ❌ External CSS (`<link rel>`) — большинство клиентов сечёт
- ❌ JavaScript (security)
- ❌ Видео / animated GIFs (Outlook показывает первый кадр)
- ❌ Web fonts (только safe fonts: Arial, Helvetica, Georgia, Times)
- ❌ Background images (частично — только на body, и не везде)
- ❌ position: absolute / fixed
- ❌ Border-radius (старый Outlook — нет)
- ❌ ::before / ::after pseudo-elements

## Что работает

- ✅ `<table>`, `<tr>`, `<td>` для layout
- ✅ Inline styles (style="..." на каждом элементе)
- ✅ Image `<img>` с inline width/height
- ✅ Color, font-size, padding, margin
- ✅ MSO conditional comments для Outlook hacks

## Каркас

```html
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <title>Subject line preview</title>
  <!--[if mso]>
  <noscript>
    <xml>
      <o:OfficeDocumentSettings>
        <o:PixelsPerInch>96</o:PixelsPerInch>
      </o:OfficeDocumentSettings>
    </xml>
  </noscript>
  <![endif]-->
  <style>
    /* Минимум external — fallback */
    @media only screen and (max-width: 620px) {
      .container { width: 100% !important; }
      .responsive-img { width: 100% !important; height: auto !important; }
      .stack { display: block !important; width: 100% !important; }
    }
  </style>
</head>
<body style="margin:0;padding:0;background:#f4f4f4;font-family:Arial,sans-serif;">
  <!-- Preheader (preview text in inbox) — скрытый -->
  <div style="display:none;font-size:1px;color:#fff;line-height:1px;max-height:0;max-width:0;opacity:0;overflow:hidden;">
    Preview text шириной до 100 символов
  </div>

  <!-- Outer wrapper -->
  <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background:#f4f4f4;">
    <tr>
      <td align="center" style="padding:32px 16px;">
        <!-- Container -->
        <table role="presentation" class="container" cellpadding="0" cellspacing="0" border="0" width="600"
               style="width:600px;max-width:100%;background:#ffffff;border-radius:8px;overflow:hidden;">

          <!-- Header -->
          <tr><td style="padding:32px;text-align:center;background:#1B1DAA;">
            <a href="https://your-domain.com" style="text-decoration:none;">
              <span style="color:#fff;font-size:24px;font-weight:bold;">yourname</span>
            </a>
          </td></tr>

          <!-- Hero -->
          <tr><td style="padding:48px 32px;text-align:center;">
            <h1 style="margin:0 0 16px;font-size:28px;font-weight:bold;color:#111;line-height:1.2;">
              Заголовок письма
            </h1>
            <p style="margin:0;font-size:16px;line-height:1.5;color:#555;">
              Подзаголовок в одну-две строки. Главная идея письма видна без скролла.
            </p>
          </td></tr>

          <!-- CTA -->
          <tr><td style="padding:0 32px 48px;text-align:center;">
            <table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 auto;">
              <tr><td style="background:#3B5BDB;border-radius:6px;">
                <a href="https://your-domain.com/cta" target="_blank"
                   style="display:inline-block;padding:14px 32px;color:#fff;text-decoration:none;font-weight:bold;font-size:16px;">
                  Главное действие →
                </a>
              </td></tr>
            </table>
          </td></tr>

          <!-- Footer -->
          <tr><td style="padding:24px 32px;background:#f9f9f9;border-top:1px solid #eee;text-align:center;font-size:12px;color:#999;">
            © 2026 YourName · <a href="%unsubscribe_link%" style="color:#999;">Отписаться</a>
          </td></tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
```

## Правила

| Правило | Почему |
|---|---|
| Таблицы для layout, не div | Outlook |
| Inline styles ВСЁ | Gmail strip'ает `<head> <style>` |
| Width 600px max | Стандарт для desktop email |
| Cellpadding=0 cellspacing=0 border=0 | сбросить default рамки |
| `role="presentation"` | accessibility — таблица не для данных |
| Bulletproof button (table-based) | display:inline-block надёжнее в Outlook |
| Preheader text | первое что юзер видит в inbox |

## Bulletproof button

Не `<a>` со стилями — используй table-wrap:
```html
<table role="presentation" cellpadding="0" cellspacing="0">
  <tr>
    <td style="border-radius:6px;background:#3B5BDB;">
      <a href="..." style="display:inline-block;padding:14px 32px;color:#fff;text-decoration:none;">
        Click me
      </a>
    </td>
  </tr>
</table>
```

## Mobile responsive

```html
<!-- В <head>: -->
<style>
  @media only screen and (max-width: 620px) {
    .container { width: 100% !important; padding: 0 !important; }
    .stack { display: block !important; width: 100% !important; }
    h1 { font-size: 22px !important; }
  }
</style>

<!-- В body: -->
<table>
  <tr>
    <td class="stack" style="width:50%;">Левая колонка</td>
    <td class="stack" style="width:50%;">Правая (стэкается на mobile)</td>
  </tr>
</table>
```

## Тестирование

- **Litmus** / **Email on Acid** — paid services with all major email clients
- **Mail-tester.com** — спам-score test
- **Самостоятельно**: отправь себе на Gmail, Outlook web, Apple Mail iPhone
- **Можно через MJML** — компилирует human-friendly markup → bulletproof HTML

## MJML alternative

Если правда не хочется писать tables — используй MJML:
```bash
npm i -g mjml
mjml email.mjml -o email.html
```

```xml
<mjml>
  <mj-body>
    <mj-section>
      <mj-column>
        <mj-text>Hello!</mj-text>
        <mj-button href="https://...">Click</mj-button>
      </mj-column>
    </mj-section>
  </mj-body>
</mjml>
```

MJML компилирует в правильные tables.

## Антипаттерны

- Использовать flexbox / grid → не работает в Outlook
- External CSS file → Gmail strips
- `<style>` в `<body>` → не везде применяется
- Web fonts через @font-face → fallback к Arial у 60% получателей
- Огромные изображения (>1MB) → грузится медленно, deliverability страдает
- Не fallback для disabled images → пустой email с иконками-обрезками
- Не тестить в Outlook → в проде разваливается у 30%
- Спам-trigger words («free», «winner», «click here») → попадает в junk
