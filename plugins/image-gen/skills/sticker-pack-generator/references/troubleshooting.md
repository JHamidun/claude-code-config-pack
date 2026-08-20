# Troubleshooting — реальные провалы и фиксы

Из production-сессии май 2026 (75-стикерный пак `promptegga`).

## Encoding

### `ffmpeg -pix_fmt yuva420p ... .webm` даёт yuv420p без alpha
- **Причина**: libvpx-vp9 muxer в ffmpeg роняет дополнительный alpha поток
- **Фикс**: использовать только Google `webm-tools/alpha_encoder` через WSL

### alpha_encoder файл >256KB
- **Причина**: дефолтный VBR с высоким bitrate
- **Фикс**: пропатчить cfg на CBR + 50kbps в alpha_encoder.cc, или передать `--end-usage=cbr --target-bitrate=50`

### alpha_encoder error "vpxenc not found"
- **Причина**: alpha_encoder вызывает `../../libvpx/vpxenc` относительно CWD
- **Фикс**:
  1. `ln -sf /opt/libvpx /libvpx`
  2. Всегда `cd /tmp/randomdir` перед запуском alpha_encoder

### WSL bash `nohup &` умирает
- **Причина**: WSL session завершается когда parent команда возвращается
- **Фикс**: использовать `bash -c '<sync command>'` с реальным завершением; для batch — `run_in_background:true` из host

## Mask quality

### Белое тело персонажа становится прозрачным
- **Причина**: rembg на motion-blur кадре не различает тело от фона
- **Фикс**: rembg на frame 0 → seed маска → SAM2 propagate. См. [sam2-rembg-pipeline.md](sam2-rembg-pipeline.md)

### SAM2 single click теряет белые части
- **Причина**: один клик в центре попадает на цветную деталь (лицо/волосы), белое тело без edge не цепляется
- **Фикс**: `predictor.add_new_mask(seed_mask)` вместо `add_new_points_or_box(points)`

### Мик/реквизит отлетает и пропадает
- **Причина**: SAM2 (один obj_id) трекает большой блоб, теряет отделившийся объект
- **Фикс**: per-frame UNION с chromakey: `alpha_i = SAM2[i] ∪ chromakey(rgb[i])`

### Белое halo вокруг персонажа (v6 regression)
- **Причина**: chromakey threshold 235 захватывает off-white края → halo
- **Фикс**: понизить до 215 + morph close 3x3 + alpha threshold (a<60→0, a>180→255)

### Мерцание между кадрами (rembg-only)
- **Причина**: rembg обрабатывает каждый кадр независимо → разные маски
- **Фикс**: SAM2 propagation для temporal consistency

### Призрачные trails
- **Причина**: SAM2 интерполирует через bfloat16 → faint trails при движении
- **Фикс**: alpha threshold `np.where(a<60, 0, a)` после union

## Performance

### rembg на CPU супер медленно
- **Причина**: ORT CPU provider
- **Фикс**:
  ```python
  session = new_session('isnet-general-use',
                        providers=['CUDAExecutionProvider','CPUExecutionProvider'])
  ```
  + установить `nvidia-cublas-cu12` через pip + `os.add_dll_directory` перед import

### BiRefNet OOM на 32GB your-server server
- **Причина**: BiRefNet требует ~40GB VRAM при batch processing
- **Фикс**: переехать на локальную машину с дискретной видеокартой

### your-server 3-wide parallel rembg в 30x медленнее single
- **Причина**: ONNX thread thrashing на vCPU без isolation
- **Фикс**: либо `--single-thread` ONNX, либо локальная GPU

## Telegram

### FloodWaitError после ~37 replace
- **Причина**: @Stickers rate-limit
- **Фикс**: `try/except FloodWaitError: await asyncio.sleep(fw.seconds+5)` + 8 retries + 2.5s pause between

### Пак показывает старый стикер после replace
- **Причина**: Telegram локальный кеш
- **Фикс**: пользователю — удалить пак и добавить заново. Серверный пропагейт ~1ч.

### Стикеры в паке не маппятся на 75-имён список
- **Причина**: эмодзи в паке нестандартные (тестовые загрузки, garbage)
- **Фикс**: map by emoji (с VS16 norm) → name; ADD missing; DELETE extras

### VS16 ломает сравнение эмодзи
- **Причина**: ❤️ может быть `❤️` или просто `❤`
- **Фикс**: `e.replace('️', '')` перед сравнением

### Telethon SQLite session locked
- **Причина**: два процесса открыли .session файл
- **Фикс**: один процесс на сессию; если убил — удали `*.session-journal`

### @Stickers /delsticker требует forward
- **Причина**: бот ожидает actual sticker message, не имя
- **Фикс**: `await client.send_file(bot, file=document)` где document = doc object из StickerSet

## Pipeline mistakes

### Все «новые» версии в test pack оказались одним файлом
- **Причина**: использовал sed-chain `sed -i s/v3/v4/g` поверх базового скрипта — substitution не сматчилась с реальной WEBM-переменной, все варианты ссылались на тот же файл
- **Фикс**: писать каждый вариант как отдельный самостоятельный скрипт с прямым путём, без sed

### Pipe `| tail -8` блокирует длинный процесс
- **Причина**: tail буферизует до EOF; long-running process получает SIGPIPE и умирает или зависает
- **Фикс**: всегда `> file.log 2>&1` + Monitor с grep, никогда `| tail`

### Monitor шумит на каждой строке прогресс-бара
- **Причина**: rembg/SAM2 пишут `\r`-обновляемые прогресс-бары, monitor их интерпретирует как строки
- **Фикс**: `grep -E --line-buffered "^\[|^Done|ERR"` — match только осмысленные события
