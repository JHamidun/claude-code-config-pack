# Carousel quickstart — editorial deck for your channel

No sample deck ships with this pack (the originals are the author's real channel cards).
The starter skeleton — `.card` container, brand tokens, base classes — lives in
`cards-creator/SKILL.md` → **«Шаг 3»**; the card-type catalogue is in **«Типы карточек»**.
Build the first deck from those, keep it, and copy *it* from then on.

A dense deck normally carries: cover-photo, comparison **table**, **bar-chart**,
**split + cutout**, **navy photo-band**, **terminal-mock**, **stat-strip + effort grid**, CTA,
plus the collage DNA: **sticker**, **speech bubble**, **3D-object-in-air**, **handwritten scribble** (Caveat).

## 5 steps

**1. Scratch dir (NOT inside the skill):**
```bash
mkdir ~/cards-X && cd ~/cards-X
# create styles.css + series.html from SKILL.md «Шаг 3», or copy them from your previous deck
```

**2. Images — gpt-image-2 (единый стиль через wrapper, РЕКОМЕНДУЕТСЯ):**
- `python ~/.claude/skills/cards-creator/scripts/card_image_generator.py generate cards.json ./img` — вся колода ОДНИМ шаблоном (`photoreal-3d` дефолт / `flat-editorial` / `isometric` / `real-photo`), бренд-палитра прибита в шаблоне. `"cut":true` в карточке → сразу rembg-вырезка `_t.png`. Одна картинка на пробу: `card_image_generator.py test "<subject>" photoreal-3d --cut --size 1536x1024`.
- Правило единства: ВСЕ иллюстрации колоды — одним template (не мешать flat+3d).
- **Cut background** вручную (если картинка не через wrapper; gpt-image-2 НЕ умеет прозрачный фон):
  ```bash
  python ~/.claude/skills/cards-creator/scripts/cut_bg.py name.png   # -> name_t.png  (rembg isnet + alpha matting)
  ```
- If a metaphor isn't obvious as an illustration → use a **real photo** as a full band + `.band-cap` caption (e.g. conductor+orchestra).

**3. Build `series.html`**: one `<section class="card">` per card, in posting order; point `<img>` at your cutouts. **≤10 cards** (album max). Dense beats airy — fill height (`flex:1` hero, `justify-content:space-between`, bottom takeaway band). **Бренд-лого в углу:** положи свой `logo.png` рядом с `series.html` + правило `.card.inner::after` (см. SKILL «Бренд-логотип»). Цветовой ритм: 1-2 карточки сделай navy/terra среди cream.

**4. Render + eyeball:**
```bash
python ~/.claude/skills/cards-creator/scripts/render_cards.py series.html   # -> ./png/series-NN.png
```
Check each: no overflow, headline highlight intact, cutouts grounded, numbers correct.

**5. Publish** — album via your bot (Bot API, skill `tg-bot-publish`). The bot must be a channel
admin with *Post Messages*; the HTML caption rides on the first image, 10 files max:
```bash
python ~/.claude/tools/tg_bot.py --token MYBOT --dry-run album --to @yourchannel \
  png/series-01.png png/series-02.png --text "<b>Заголовок</b>"
```
Caption ≤4096 chars, HTML tags: `<b> <i> <tg-spoiler> <blockquote expandable> <a href>`.
Bot API has **no scheduled posts** — cron the same command, or write the few Telethon lines
(`send_file(..., schedule=dt)`) if you need a user-account deferred album. Set `sys.stdout` to
utf-8 when scripting on Windows (cp1251 console dies on emoji).

**6. Сторис канала (9:16)** — карточки 4:5 в сторис РЕЖЕТ по бокам. Вписать в кадр:
```bash
python ~/.claude/skills/cards-creator/scripts/build_story_frames.py        # png/series-* -> story_png/story-*
python ~/.claude/skills/cards-creator/scripts/post_stories.py list your_username   # лимит = boost level!
python ~/.claude/skills/cards-creator/scripts/post_stories.py post your_username
# починить уже висящие кривые без расхода квоты: ... post_stories.py edit your_username 3,4,5,...
```

See `cards-creator/SKILL.md` → «ПЛОТНЫЕ КАРТОЧКИ», «ANTI-AIR», «Интегрированные вырезки»
for the full design DNA, and `post_stories.py`'s own docstring for the Telethon stories gotchas.
