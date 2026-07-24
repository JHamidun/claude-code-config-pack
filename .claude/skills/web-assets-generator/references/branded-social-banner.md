# Branded social/og banner via HTML render (not Pillow)

> For polished branded cards (og-image, webinar/event banners, announcement covers),
> lay out an HTML template and screenshot it — instead of `draw.text` in Pillow.
> Vector layout → screenshot = crisp text at any size, real fonts, gradients, glassy
> circles, overlapping avatars. Pillow text is fine for flat icons, not for brand cards.
> Battle-tested on edu-project og-banners and webinar/event banners.

## Recipe

1. **Template** — start from `assets/banner-template.html` (1200×630, dark editorial:
   subtle grid + radial brand glow + eyebrow / kicker / H1-with-accent / sub / date-pill /
   host row with avatar circles + brand chips). Edit `:root` colors and the text nodes.
   Russian typography: «ёлочки», длинное тире —, неразрывные пробелы у чисел («68 000 ₽»).

2. **Avatars (optional)** — cut portrait backgrounds to transparent PNG first:
   `python scripts/cut_avatars.py` (edit the SRC list). Uses `birefnet-portrait` +
   alpha_matting + largest-connected-component (scipy.ndimage) + gaussian feather —
   smooth edges, no stray objects. Drop results next to the HTML as `avatar_1.png` etc.
   The `.host-pic` circle sits portrait on a brand radial fill, `img{width:112%;bottom:-5%}`
   crops to face; `.host-pic+.host-pic{margin-left:-18px}` overlaps them.
   No portraits → delete the `.host-pics` block.

3. **Render** (chrome-devtools MCP, exact pixels):
   - `navigate_page` → `file:///abs/path/banner.html`
   - `resize_page` → width 1200, height 630   ← sets the real viewport so the shot is 1:1
   - `take_screenshot` format png → `banner.png`
   - (Playwright equivalent: `browser_navigate` + `browser_resize` + `browser_take_screenshot`.)
   Read the PNG back to eyeball it before shipping.

4. **Deliver**
   - **Website og**: upload PNG to CDN/S3 → set in Tilda Page Settings `fb_img` (NOT
     project-head — see tilda skill #38) → refresh Telegram cache via @WebpageBot.
   - **Telegram bot**: `curl -F chat_id=<admin> -F photo=@banner.png .../sendPhoto` →
     take `result.photo[-1].file_id` → store as the bot's banner id (reused infinitely,
     no re-upload). Send to "me" (Saved Messages) via Telethon to hand the file to the user.

## Why screenshot beats Pillow here
- Real web fonts (Inter etc.) with proper kerning/weights — no bundled .ttf juggling.
- CSS gradients, radial glows, border-radius circles, overlap, shadows — trivial vs Pillow math.
- Text wrapping, letter-spacing, multi-weight inline (`<b>name</b> <span class=role>`) for free.
- One template → many cards by swapping text + `:root` vars.

## Gotchas
- `resize_page` BEFORE screenshot — otherwise you get the default viewport, wrong crop.
- `@import` Google Fonts needs network; if offline, the shot still renders in a fallback
  font — keep a webfont `<link>` and let it load (chrome-devtools waits for `load`).
- For retina-crisp output you can render at 2× (resize 2400×1260, CSS in px stays the same
  only if you scale the `.banner` — simplest is keep 1200×630, it's already sharp as vector).
- Avatar cut on CUDA-less Windows prints an onnxruntime CUDA warning — harmless, CPU path runs.
