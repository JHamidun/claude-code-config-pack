# Маска: rembg seed + SAM2 propagate + per-frame chromakey UNION

## Проблема

Нужна чёткая прозрачная альфа-маска через 90 кадров анимации (30fps × 3s) когда:
- персонаж **белый** (e.g. яйцо в одежде/тоге)
- фон **тоже белый** (классический cartoon)
- есть **motion blur** на быстрых кадрах (прыжки, броски)
- иногда **реквизит отделяется** от персонажа (микрофон, мяч, шар)

## Почему наивные подходы провалились

| Подход | Что ломается |
|--------|-------------|
| ffmpeg `colorkey=white` | Жёсткая граница, мелкие детали не ловятся, белые части персонажа становятся прозрачными |
| rembg на каждом кадре отдельно | Теряет белое тело на motion-blur кадрах, мерцает между кадрами (нет temporal consistency) |
| SAM2 один клик в центре | Кликает в face — захватывает только цветные части (волосы, лицо). Белое тело без edge-градиента не цепляется |
| UNION rembg+chromakey per-frame (без SAM2) | На motion-blur кадрах оба теряют → большие дыры |
| v6: UNION с threshold=235 | Хватает офф-вайт края → белые halo вокруг персонажа |

## Рабочее решение

```
SEED (frame 0):
  rembg(frame 0)         ← хорошо работает на статике, ловит белое тело
  chromakey(frame 0)     ← ловит non-white props (мик, очки, банан)
  UNION (rembg ∪ ck)     ← полный контур всего что должно быть видно
  morph close 3x3        ← заполняет дыры в контуре

SAM2:
  init_state(frame_dir)
  add_new_mask(seed, frame_idx=0, obj_id=1)
  propagate_in_video()    ← temporal memory трекает через motion blur
                           ← но теряет реквизит когда он отделяется

PER-FRAME final alpha:
  for each i in 0..89:
    alpha_i = SAM2_mask[i] ∪ chromakey(rgb[i])  ← chromakey ловит отлетевший реквизит
    morph close 3x3
    threshold: a<60→0, a>180→255               ← убирает trails и призраки

→ RGBA PNG sequence → yuva420p → alpha_encoder → webm
```

## Почему это работает

- **rembg на статике справляется** — нет motion blur на кадре 0
- **SAM2 умеет тысячу кадров** через temporal memory: если дать ему хорошую seed-маску, он трекает её правильно даже через motion-blur кадры (которые ломают rembg)
- **chromakey per-frame покрывает edge case** — когда реквизит отлетает от персонажа физически, SAM2 (один obj_id) держит большой блоб (тело) и теряет мелкий улетающий объект. Chromakey на каждом кадре ловит любой не-белый пиксель, включая отлетевший
- **morph close + threshold** убирает «призраки» (faint trails из-за временной интерполяции SAM2) и заполняет мелкие дыры

## Параметры (battle-tested на 75 стикерах)

| Параметр | Значение | Почему |
|----------|----------|--------|
| `chromakey threshold t` | 215 | 235 захватывает офф-вайт края (halo). 200 пропускает светлые элементы. 215 — sweet spot. |
| morph kernel | `cv2.MORPH_ELLIPSE (3,3)` | Минимум что закрывает 1-2 пиксельные дыры без раздутия |
| alpha threshold low | `<60 → 0` | Убивает faint trails от SAM2 интерполяции |
| alpha threshold high | `>180 → 255` | Делает edges чёткими |
| SAM2 model | `sam2.1_hiera_small.pt` | tiny слишком слаб, base/large — overkill для 90 кадров |
| SAM2 propagate | bfloat16 autocast | На high-end GPU ~12 it/s, на mid-range GPU ~5 it/s |
| ffmpeg JPEG quality | `-qmin 1 -q:v 1` | SAM2 init_state читает JPEG — нужно сохранить качество |
| fps | 30 | Стандарт для Telegram |
| длительность | `-t 3` | Жёсткий лимит Telegram = 3s |
| резолюция | `crop='min(iw,ih)' + scale=512:512` | Crop в квадрат потом ресайз — избегаем растяжки |

## Альтернативы которые тоже работают

- Для **простых случаев** (цветной персонаж на белом): достаточно rembg + median±1 temporal smoothing
- Для **очень сложных** (несколько отдельных персонажей в кадре): multi-obj SAM2 с разными obj_id, по одному per character/prop
- Для **studio-quality**: SAM2 + добавить point-prompts на отлетающий реквизит на конкретных кадрах

## Не работает

- ❌ ffmpeg alpha matting (`-filter_complex alphamerge`) с маской от rembg per-frame — мерцание между кадрами
- ❌ BiRefNet на CPU — OOM или 10x медленнее rembg
- ❌ ONNX birefnet на GPU без `nvidia-cublas-cu12` в PATH — silent CPU fallback
- ❌ Encoding video VP9 alpha через ffmpeg — alpha теряется в muxer
