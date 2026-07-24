# Carousel quickstart — reference-channel-style deck for @yourchannel

Self-contained template to copy: **`../handoff/examples/opus48-cards.html`** (+ `styles.css` + its
images sit next to it — `cd` there and `python render_cards.py opus48-cards.html` renders out of the box).
That deck contains every card type we use: cover-photo, comparison **table**, **bar-chart**,
**split + cutout**, **navy photo-band**, **terminal-mock**, **stat-strip + effort grid**, CTA,
plus the collage DNA: **sticker**, **speech bubble**, **3D-object-in-air**, **handwritten scribble** (Caveat).

## 5 steps

**1. Scratch dir (NOT inside the skill):**
```bash
mkdir ~/cards-X && cd ~/cards-X
cp ~/.claude/skills/cards-creator/handoff/cards/styles.css .   # base classes
```

**2. Images — gpt-image-2 (единый стиль через wrapper, РЕКОМЕНДУЕТСЯ):**
- `python ../scripts/card_image_generator.py generate cards.json ./img` — вся колода ОДНИМ шаблоном (`photoreal-3d` дефолт / `flat-editorial` / `isometric` / `real-photo`), бренд-палитра прибита в шаблоне. `"cut":true` в карточке → сразу rembg-вырезка `_t.png`. Одна картинка на пробу: `card_image_generator.py test "<subject>" photoreal-3d --cut --size 1536x1024`.
- Правило единства: ВСЕ иллюстрации колоды — одним template (не мешать flat+3d).
- **Cut background** вручную (если картинка не через wrapper; gpt-image-2 НЕ умеет прозрачный фон):
  ```bash
  python ~/.claude/skills/cards-creator/scripts/cut_bg.py name.png   # -> name_t.png  (rembg isnet + alpha matting)
  ```
- If a metaphor isn't obvious as an illustration → use a **real photo** as a full band + `.band-cap` caption (e.g. conductor+orchestra).

**3. Build `series.html`** from the template: keep the `.card` blocks you need, rewrite text, point `<img>` at your cutouts. **≤10 cards** (album max). Dense beats airy — fill height (`flex:1` hero, `justify-content:space-between`, bottom takeaway band). **Бренд-лого в углу:** копируй `handoff/cards/logo.png` рядом с series.html + `.card.inner::after` правило (см. SKILL «Бренд-логотип»). Цветовой ритм: 1-2 карточки сделай navy/terra среди cream.

**4. Render + eyeball:**
```bash
python ~/.claude/skills/cards-creator/scripts/render_cards.py series.html   # -> ./png/series-NN.png
```
Check each: no overflow, headline highlight intact, cutouts grounded, numbers correct.

**5. Publish / schedule** (album + optional video, spoiler / expandable quotes / links, UTC time):
use **`~/.claude/skills/tg-post/scripts/tg_rich_post.py`** — `schedule_album()`, `schedule_media()`, `build_caption()`, `list_scheduled()`, `FOOTER_HTML`.
Premium caption ≤4096. Verify with `GetScheduledHistoryRequest`. **Never delete others' scheduled posts** — only your own ids. Session sqlite locks → work on a `.session` copy. Set `sys.stdout` to utf-8 (cp1251 console dies on emoji).

**6. Сторис канала (9:16)** — карточки 4:5 в сторис РЕЖЕТ по бокам. Вписать в кадр:
```bash
python ~/.claude/skills/cards-creator/scripts/build_story_frames.py        # png/series-* -> story_png/story-*
python ~/.claude/skills/cards-creator/scripts/post_stories.py list your_username   # лимит = boost level!
python ~/.claude/skills/cards-creator/scripts/post_stories.py post your_username
# починить уже висящие кривые без расхода квоты: ... post_stories.py edit your_username 3,4,5,...
```

**Эталон под копирование:** `handoff/examples/opus48-final.html` (+ `opus48-final.cards.json`, готовые 9:16 в `opus48-stories/`) — рендерится из коробки: `cd handoff/examples && python ../../scripts/render_cards.py opus48-final.html`.

**Кампания «новость под ключ» (пост+карусель+сторис+видео одной цепочкой):** см. `tg-post/references/launch-campaign.md` — анатомия поста, концовка с голосованием, спойлер-логика, точные команды. Канонический скрипт: `tg-post/references/examples/opus48-campaign.py`.

See `cards-creator/SKILL.md` → «ПЛОТНЫЕ КАРТОЧКИ», «v3», «v4» for the full design DNA, and `tg-post/SKILL.md` → «ПЛАНИРОВАНИЕ И ПУБЛИКАЦИЯ» for the Telethon gotchas.
