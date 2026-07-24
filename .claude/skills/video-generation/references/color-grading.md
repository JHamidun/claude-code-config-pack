# Color grading — LUT + ffmpeg recipes

Цвет накладывается **последним** видео-фильтром (после монтажа, перед финальным loudnorm-проходом).
Готовый CLI: `video-editor/scripts/color_grade.py` (авто-санирует .cube, экранирует пути).

## LUTs в `skills/video-generation/luts/`

- `Kodak2383_D55.cube` — голливудский плёночный лук (Resolve Film Look, LUT_3D_SIZE 33). Bundled, дефолт.
- Добавить ещё: `git clone https://github.com/YahiaAngelo/Film-Luts` (G'MIC коллекция) или сгенерить из даташитов плёнки (`spectral_film_lut`).

> **Гоча:** ffmpeg `lut3d` не понимает ключ `LUT_3D_INPUT_RANGE` (хочет `DOMAIN_MIN/MAX`) → «Invalid data». `color_grade.py._sanitize_cube()` вырезает эту строку во временную копию автоматически. Если применяешь .cube вручную и видишь «Error initializing filters» — убери `LUT_3D_INPUT_RANGE`.
>
> **Windows-гоча:** двоеточие диска в пути ломает парсер фильтров (`:` = разделитель опций). Экранируй: `lut3d=file=C\:/path/x.cube`. Запуск через PowerShell (Git Bash калечит пути).
>
> **Самый надёжный обход (когда `C\:` всё равно даёт `No option name near`):** скопируй .cube в
> рабочую папку и ссылайся ОТНОСИТЕЛЬНЫМ путём без двоеточия — `cp LUT build/lut.cube`, затем
> `lut3d=build/lut.cube:interp=tetrahedral`. Двоеточия в пути нет → парсер не ломается ни в каком шелле.
> (Так делает `scripts/talking-head/grade_preview.py`.)

## Применить LUT

```bash
# через скрипт (рекомендуется)
python video-editor/scripts/color_grade.py in.mp4 out.mp4 --lut kodak2383
python video-editor/scripts/color_grade.py in.mp4 out.mp4 --lut kodak2383 --strength 0.7   # 70% силы
python video-editor/scripts/color_grade.py in.mp4 out.mp4 --look film         # LUT+lifted blacks+vignette+grain
python video-editor/scripts/color_grade.py in.mp4 out.mp4 --look teal-orange   # без LUT-файла

# сырые ffmpeg-эквиваленты
ffmpeg -i in.mp4 -vf "lut3d=file=C\:/.../Kodak2383_D55.cube:interp=tetrahedral" -c:v libx264 -crf 18 -pix_fmt yuv420p out.mp4
# 70% сила
ffmpeg -i in.mp4 -filter_complex "[0:v]split[a][b];[a]lut3d=file=LUT[l];[b][l]blend=all_expr='A*0.3+B*0.7'" out.mp4
```

## ⚠️ Яркий уличный футаж: LUT выбивает света (пересвет лица/одежды)

Kodak-LUT (и любой контрастный print-эмулятор) на **ярком дневном футаже** (белая футболка,
кожа на солнце) выбивает света в клиппинг → «лицо/одежда СИЯЮТ, аж слепит» (реальная жалоба
заказчика). Фикс — **придавить света и чуть снизить экспозицию ДО LUT**, тогда LUT работает на
нормально-экспонированном входе и ничего не клиппит:

```bash
# спад светов (1.0→0.72) + −9% экспозиции + лёгкая гамма, потом LUT
ffmpeg -i in.mp4 -vf "curves=all='0/0 0.5/0.40 1/0.72',eq=brightness=-0.09:gamma=0.95,lut3d=file=C\:/.../Kodak2383_D55.cube:interp=tetrahedral,eq=saturation=1.04" -c:v libx264 -crf 20 -pix_fmt yuv420p out.mp4
```

`curves all='0/0 0.5/0.40 1/0.72'` — тени на месте, света притянуты ЖЁСТКО; `brightness=-0.09:gamma=0.95` —
общий минус. Саму `contrast`-добавку у LUT убрать (она клиппит).

> **Калибровка по боли (2026-06):** первый, мягкий вариант (`1/0.86, brightness=-0.04`) заказчик
> ДВАЖДЫ забраковал — «картинка супер светлая, не такой белой». Дефолт для **яркого дневного
> футажа** (белая одежда на солнце) — СИЛЬНЫЙ: `1/0.72, brightness=-0.09`. Для тёмного
> кинематографичного b-roll спад почти незаметен. Проверять на самом ярком кадре (burn на стопе,
> сравнить варианты 0.86 / 0.78 / 0.72 рядом — белая футболка должна стать ОФФ-вайт с деталями).

## Built-in looks (без LUT-файла)

```bash
# teal-orange кинолук
ffmpeg -i in.mp4 -vf "colorbalance=rs=0.05:gs=-0.05:bs=-0.15:rm=0.03:gm=-0.03:bm=-0.08:rh=0.12:gh=-0.05:bh=-0.18,curves=all='0/0 0.25/0.20 0.5/0.50 0.75/0.82 1/1'" out.mp4
# плёночное зерно
ffmpeg -i in.mp4 -vf "noise=c0s=25:c0f=t+u" -tune grain out.mp4
# хроматическая аберрация (фриндж)
ffmpeg -i in.mp4 -vf "rgbashift=rh=-4:gh=4" -pix_fmt yuv420p out.mp4
```

## Hald CLUT (правка в любом фоторедакторе)

```bash
# 1) идентичный Hald + кадр-референс рядом
ffmpeg -f lavfi -i haldclutsrc=8 -i in.mp4 -ss 4 -frames:v 1 -filter_complex "[1]scale=-1:512[b];[0][b]hstack" hald_edit.png
# 2) покрасить hald_edit.png в Lightroom/GIMP → hald_graded.png
# 3) применить
ffmpeg -i in.mp4 -i hald_graded.png -filter_complex haldclut -pix_fmt yuv420p -c:v libx264 -crf 18 out.mp4
```

## Color match между шотами (Python)

```python
import cv2
from skimage import exposure  # pip install scikit-image
ref = cv2.cvtColor(cv2.imread("ref.png"), cv2.COLOR_BGR2RGB)
src = cv2.cvtColor(cv2.imread("src.png"), cv2.COLOR_BGR2RGB)
matched = exposure.match_histograms(src, ref, channel_axis=-1)
cv2.imwrite("out.png", cv2.cvtColor(matched.astype("uint8"), cv2.COLOR_RGB2BGR))
```

Полный film-pipeline (LUT + lifted blacks + teal-orange + vignette + grain) и сравнение инструментов → `video-editor/references/montage-research-report.md` §2G/§3F.
