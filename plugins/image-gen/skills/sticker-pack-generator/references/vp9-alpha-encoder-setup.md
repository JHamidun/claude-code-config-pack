# VP9 alpha_encoder setup (WSL Ubuntu 22.04)

## Зачем

FFmpeg/libvpx **не умеет** правильно муксить VP9 alpha в WebM. На выходе всегда yuv420p без альфы, даже если кодируешь yuva420p — мукс роняет дополнительный поток. Telegram требует именно `BlockAdditional` mux (Matroska feature), который делает **только** Google'овский `alpha_encoder` из `webm-tools`.

## Установка (WSL Ubuntu 22.04, root)

```bash
sudo apt update
sudo apt install -y build-essential cmake yasm git pkg-config

# 1) libvpx
cd /opt
sudo git clone https://chromium.googlesource.com/webm/libvpx
cd libvpx
sudo ./configure --enable-vp9 --enable-vp9-encoder --enable-vp8-encoder \
  --enable-multi-res-encoding --enable-experimental --disable-examples \
  --disable-docs --disable-unit-tests
sudo make -j$(nproc)

# 2) libwebm
cd /opt
sudo git clone https://chromium.googlesource.com/webm/libwebm
cd libwebm
sudo mkdir -p build && cd build
sudo cmake .. && sudo make -j$(nproc)

# 3) webm-tools (содержит alpha_encoder)
cd /opt
sudo git clone https://chromium.googlesource.com/webm/webm-tools
cd webm-tools/alpha_encoder
```

## Патч для cbr 50kbps (≤256KB)

В дефолтной сборке `alpha_encoder` использует VBR с высоким битрейтом → файл ~340KB → Telegram отвергнет. Патч:

```bash
# В alpha_encoder.cc найти блок установки cfg перед vpx_codec_enc_init:
# Добавить:
#   cfg.rc_end_usage = VPX_CBR;
#   cfg.rc_target_bitrate = 50;  // kbps
# или вызывать через флаги --end-usage=cbr --target-bitrate=50
sudo nano alpha_encoder.cc  # либо patch -p1 < cbr.patch
```

Пересобрать:
```bash
sudo make
```

## Симлинк для относительного пути

`alpha_encoder` вызывает `../../libvpx/vpxenc` относительно своего CWD. Если запускать из `/tmp/foo` — `vpxenc` ожидается в `/libvpx/vpxenc`. Сделай симлинк:

```bash
sudo ln -sf /opt/libvpx /libvpx
ls -la /libvpx/vpxenc  # должен резолвиться
```

## Использование

```bash
# Из Windows-хоста через WSL
wsl -d Ubuntu-22.04 -u root bash -c \
  "cd /tmp && wd=\$(mktemp -d) && cd \$wd && \
   /opt/webm-tools/alpha_encoder/alpha_encoder \
   -w 512 -h 512 -i /mnt/c/path/to/input.yuva -o /mnt/c/path/to/output.webm -c vp9"
```

**Критично**: `cd $wd` обязателен — иначе относительный путь к vpxenc сломается.

## Smoke test

```bash
ffmpeg -f lavfi -i "color=red:size=512x512:duration=3:rate=30" \
  -f lavfi -i "color=black:size=512x512:duration=3:rate=30" \
  -filter_complex "[0:v][1:v]alphamerge" -pix_fmt yuva420p -f rawvideo /tmp/t.yuva
cd /tmp/encwd
/opt/webm-tools/alpha_encoder/alpha_encoder -w 512 -h 512 -i /tmp/t.yuva -o /tmp/t.webm -c vp9
ffprobe /tmp/t.webm  # должен показать VP9 + alpha track
ls -la /tmp/t.webm   # должно быть <256KB
```

## Pitfalls

- **WSL `nohup &` умирает** после возврата команды. Запускай через `bash -c` с реальным завершением, или из background-job на хосте.
- **WSL пути**: `C:\path` → `/mnt/c/path` (lowercase, без `:`). Helper:
  ```python
  def to_wsl(p):
      p = p.replace('\\','/')
      if len(p)>1 and p[1]==':': return f'/mnt/{p[0].lower()}{p[2:]}'
      return p
  ```
- **Параллельный батч в WSL**: используй `xargs -P 4` поверх `/tmp/<random>/encode_one.sh`. Каждый encode_one создаёт свой `mktemp -d` и `cd` туда.
