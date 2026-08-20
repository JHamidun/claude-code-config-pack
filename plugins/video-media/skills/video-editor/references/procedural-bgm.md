# Procedural BGM — синтез музыкальной подложки чистым ffmpeg (локально, без внешних сервисов)

Подложка собирается генераторами самого ffmpeg (`sine`, `aevalsrc`, `anoisesrc`) — аудиофайл-исходник не нужен.
Полезно как **мгновенная подложка** (drone/sub-bass/cyberpunk pad), когда генератор музыки не нужен или
недоступен: фон под короткий клип, где важнее скорость, чем «вкус».

## Базовый cyberpunk sub-bass drone

```bash
# суб-бас 55 Гц + пилообразный лид (гармоники 110/220/330 через aevalsrc) + апульсатор 4 Гц (~120 BPM)
ffmpeg -f lavfi -i "sine=frequency=55:duration=5" \
  -f lavfi -i "aevalsrc=0.5*sin(2*PI*110*t)+0.25*sin(2*PI*220*t)+0.12*sin(2*PI*330*t):d=5" \
  -filter_complex "[0:a]apulsator=hz=4,lowpass=f=120,volume=2[sub]; \
                   [1:a]apulsator=hz=4,bandpass=f=220,volume=1[synth]; \
                   [sub][synth]amix=inputs=2:weights=1.5 0.8[out]" \
  -map "[out]" -y bgm.mp3
```

Как это читать:
- `sine=frequency=55` — чистый суб-бас (нота A1). Меняй частоту под тональность (41=E1, 55=A1, 65=C2…).
- `aevalsrc=0.5*sin(2πf t)+...` — аддитивный синтез: фундамент + обертоны (полусила, четверть, осьмушка) = пилообразный «аналоговый» лид.
- `apulsator=hz=4` — амплитудная модуляция (пульс). hz = удары/сек → 4 Гц = 240 «тиков»/мин, ощущается как ~120 BPM грув.
- `lowpass/bandpass` — формируют суб и лид по частотам. `amix weights` — баланс слоёв.

## Вариации

```bash
# тёмный ambient pad (две расстроенные синусоиды + tremolo)
ffmpeg -f lavfi -i "sine=frequency=110:duration=20" -f lavfi -i "sine=frequency=110.5:duration=20" \
  -filter_complex "[0:a][1:a]amix=inputs=2,tremolo=f=0.3:d=0.5,lowpass=f=400,aecho=0.8:0.7:60:0.4,volume=2[out]" \
  -map "[out]" -y pad.mp3

# напряжённый riser/braam под переход (растущая частота + дисторшн)
ffmpeg -f lavfi -i "aevalsrc='0.4*sin(2*PI*(80+40*t)*t)':d=3" \
  -filter_complex "highpass=f=40,volume=3,acompressor" -y riser.mp3

# белый/розовый шум как атмосфера (дождь/ветер заменитель)
ffmpeg -f lavfi -i "anoisesrc=d=10:c=pink:a=0.3" -y noise.mp3
```

## Когда что
- Нужна **быстрая подложка** под короткий ролик / превью → procedural BGM (этот файл).
- Нужен **настоящий трек/драматургия** (60s+, дуга, узнаваемая музыка) → `suno` (через браузер) или `elevenlabs` Music / Lyria 2 (см. video-generation `skills/video-generation/references/audio.md`).

Типовая финальная сборка 9:16, под которую рассчитана эта подложка: blurred-bg overlay + сабы + `amix weights=1.0 0.4`
(видео + bgm). В нашем пайплайне субтитры делаются ASS-караоке вместо `drawtext` — см. `montage-toolkit.md`.
