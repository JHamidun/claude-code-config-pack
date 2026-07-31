# Motion graphics — Python (movis) + Manim, плюс dep-free ffmpeg

Три уровня сложности для анимированной графики (титры, lower-thirds, каунтеры, kinetic-текст,
data-viz). Соц-UI оверлеи (IG/TG) — отдельно в `remotion-overlays.md`.

## Уровень 0 — dep-free ffmpeg (`scripts/motion_graphics.py`) ✓ протестирован

Накладывает анимированный элемент на готовое видео. PIL для кириллицы (ffmpeg drawtext её ломает).

```bash
python scripts/motion_graphics.py like-counter in.mp4 out.mp4 --to 15000 --start 1 --end 5
python scripts/motion_graphics.py progress    in.mp4 out.mp4 --start 2 --end 8 --color FF4444
python scripts/motion_graphics.py countdown   in.mp4 out.mp4 --from 3 --at 0
python scripts/motion_graphics.py lower-third  in.mp4 out.mp4 --name "Your Name" --sub "CPO YourProduct" --in 1 --out 6
python scripts/motion_graphics.py pop          in.mp4 out.mp4 --text "СКИДКА 50%" --at 3 --x 0.5 --y 0.4
```

Гоча: числовые каунтеры — drawtext (ASCII-цифры, ОК); текст с кириллицей — PIL-PNG overlay
(lower-third/pop). Путь шрифта в drawtext экранируется (`C\:/...`).

## Уровень 1 — movis (Python, кифреймы + изинг, MIT) ✓ установлен

Композитинг со слоями/анимацией прямо в Python. Для lower-thirds, титров, простых сцен.

```python
import movis as mv

scene = mv.layer.Composition(size=(1920, 1080), duration=8.0)
bar = scene.add_layer(mv.layer.Rectangle(size=(600, 80), color="#1a1a1a"))
bar.transform.position.enable_motion().extend(
    times=[0.0, 0.5], values=[(-300, 980), (300, 980)], easings=["ease_out"])
name = scene.add_layer(mv.layer.Text("Your Name", font_size=42, color="white"))
name.opacity.enable_motion().extend([0.4, 0.9], [0.0, 1.0])
scene.write_video("lower_third.mp4")
```

Для прозрачности рендерь на отдельном слое и экспортируй с alpha, либо накладывай результат
ffmpeg-overlay (colorkey/chromakey) — проще держать соц-UI на Remotion.

## Уровень 2 — Manim (Python, объяснялки/data-viz/математика, MIT) ✓ установлен

Для kinetic-типографики, графиков, «как это работает» анимаций. LaTeX (MiKTeX) НЕ обязателен для
обычного `Text` (нужен только для формул).

```python
# manim_title.py
from manim import *
class TitleCard(Scene):
    def construct(self):
        title = Text("Результат", font_size=72, color=WHITE)
        sub = Text("за 30 дней", font_size=36, color=YELLOW).next_to(title, DOWN)
        self.play(Write(title), run_time=0.8)
        self.play(FadeIn(sub, shift=UP*0.3), run_time=0.5)
        self.wait(2)
        self.play(FadeOut(VGroup(title, sub)), run_time=0.4)
```

```bash
manim -qh --transparent manim_title.py TitleCard -o title.mov   # alpha .mov
ffmpeg -i main.mp4 -i title.mov -filter_complex "[0:v][1:v]overlay=0:0:enable='between(t,0,4)'[v]" -map "[v]" -map 0:a -c:a copy titled.mp4
```

Гоча Windows: для формул нужен MiKTeX (~4ГБ, miktex.org); для текста — нет. `--transparent` даёт
alpha .mov (qtrle).

## Уровень 3 — Remotion (React→video, лучшее качество соц-UI) — см. `remotion-overlays.md`

## Когда что

| Нужно | Инструмент |
|---|---|
| Каунтер/прогресс/титр поверх видео, быстро | `motion_graphics.py` (ffmpeg) |
| Lower-third/сцена с кифреймами в Python | movis |
| Объяснялка/график/data-viz/математика | Manim |
| Соц-UI хром (IG/TG/TikTok), kinetic-типографика премиум | Remotion |
