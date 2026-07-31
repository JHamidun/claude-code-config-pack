# Higgsfield sandbox — media-processing scripts (ffmpeg/curl, дословно из debug)

Песочница = Debian + ffmpeg 5.1.9 + Python 3.11.2 + jq. Это вспомогательные команды бэкенда/песочницы (помимо montage,
см. skill-montage-detail.md). Забрать в наш video-editor/video-generation.

## 1. Превью / постер-кадр + миниатюры
```bash
# постер видео (1-я сек = обход чёрных кадров)
ffmpeg -y -i input.mp4 -ss 00:00:01 -vframes 1 -q:v 2 -vf "scale=1280:720:force_original_aspect_ratio=decrease" output_poster.jpg
# лёгкая миниатюра картинки (ширина 320, lanczos)
ffmpeg -y -i input.png -vf "scale=320:-1:flags=lanczos" -q:v 3 thumbnail.jpg
```

## 2. Thumbnail grid / contact sheet из видео
```bash
# 3×3 (9 кадров, для 15с шаг 1.5с)
ffmpeg -y -i input.mp4 -vf "fps=1/1.5,scale=320:180,tile=3x3" -vframes 1 grid_3x3.jpg
# 4×3 (12 кадров, шаг 1.2с)
ffmpeg -y -i input.mp4 -vf "fps=1/1.2,scale=320:180,tile=4x3" -vframes 1 grid_4x3.jpg
```

## 3. Сборка финала + конвертация
```bash
# concat без перекодирования (одинаковые codec/res)
printf "file 'clip_1.mp4'\nfile 'clip_2.mp4'\nfile 'clip_3.mp4'\n" > filelist.txt
ffmpeg -y -f concat -safe 0 -i filelist.txt -c copy output_final.mp4
# MOV/WebM → web MP4 (H.264/AAC, yuv420p для iOS)
ffmpeg -y -i input.mov -c:v libx264 -preset slow -crf 22 -c:a aac -b:a 128k -pix_fmt yuv420p output_web.mp4
```

## 4. Watermark / брендинг
```bash
# PNG-лого в правый нижний угол, отступ 20px
ffmpeg -y -i video.mp4 -i logo.png -filter_complex "[1:v]scale=150:-1[logo];[0:v][logo]overlay=main_w-under_w-20:main_h-under_h-20" -c:a copy output_watermarked.mp4
# копирайт-текст в угол
ffmpeg -y -i video.mp4 -vf "drawtext=text='© Brand 2026':x=w-tw-20:y=h-th-20:fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:fontsize=16:fontcolor=white:box=1:boxcolor=black@0.4" -c:a copy output_branded.mp4
```

## 5. Превью для плеера в чате (faststart) + HLS
```bash
# moov-атом в начало = мгновенный старт без полной загрузки
ffmpeg -y -i output_final.mp4 -c copy -map_metadata 0 -movflags +faststart web_playable.mp4
# адаптивный HLS (m3u8 + .ts чанки по 4с)
ffmpeg -y -i input.mp4 -c:v libx264 -c:a aac -s 854x480 -pix_fmt yuv420p -f hls -hls_time 4 -hls_playlist_type vod -hls_segment_filename "segment_%03d.ts" playlist.m3u8
```

## 6. cURL — загрузка/скачивание ассетов
```bash
# скачать рендер с CDN (retry+timeout, follow redirects для S3)
curl -sL --retry 3 --connect-timeout 10 -o ./local_clip.mp4 "https://cdn.higgsfield.ai/v1/jobs/job_abc123/video.mp4"
# multipart-загрузка на API
curl -s -X POST -H "Authorization: Bearer $HF_JWT_TOKEN" -F "files[]=@./render_final.mp4" "https://api.higgsfield.ai/v1/assets/upload"
# 2-этап S3 presigned: запросить URL → PUT файл
PRESIGNED_DATA=$(curl -s -X POST -H "Authorization: Bearer $HF_JWT_TOKEN" -H "Content-Type: application/json" -d '{"filename":"render_final.mp4","content_type":"video/mp4"}' "https://api.higgsfield.ai/v1/assets/presigned-url")
UPLOAD_URL=$(echo "$PRESIGNED_DATA" | jq -r '.upload_url')
curl -X PUT -H "Content-Type: video/mp4" --upload-file ./render_final.mp4 "$UPLOAD_URL"
```

→ Забрать: poster `-ss 1s` (анти-чёрный-кадр), grid `fps=1/N,tile=AxB` (дешёвый contact-sheet для раскадровок), faststart для веб-плеера, presigned-S3 паттерн. У нас montage уже сильнее (ASS-караоке > drawtext, blurred-bg reframe).

---

## 7. Аудио — микс/нормализация/обрезка
```bash
# VO+BGM с автодакингом (sidechaincompress)
ffmpeg -y -i original_video.mp4 -i ambient_music.mp3 -filter_complex \
"[0:a]volume=1.0[voice];[1:a]volume=0.2[bgm_quiet];[bgm_quiet][voice]sidechaincompress=threshold=0.15:ratio=4:release=500:attack=15[mixed_audio]" \
-map 0:v -map "[mixed_audio]" -c:v copy -c:a aac -b:a 192k output_podcast.mp4
# EBU R128 loudnorm (broadcast)
ffmpeg -y -i input.mp3 -af loudnorm=I=-16:TP=-1.5:LRA=11:print_format=summary output_normalized.mp3
# обрезка музыки под видео + fade-out (15с, затухание за 2с)
ffmpeg -y -i music.mp3 -af "afade=t=out:st=13:d=2" -t 15 music_cut.mp3
```

## 8. Субтитры — SRT/ASS караоке
```bash
# SRT с кастом-стилем
ffmpeg -y -i video.mp4 -vf "subtitles=subs.srt:force_style='FontName=Arial,FontSize=18,PrimaryColour=&H00FFFF,Alignment=2,MarginV=25'" -c:a copy out.mp4
# ASS караоке word-highlight (агент генерит .ass с тегами {\k...})
ffmpeg -y -i video.mp4 -vf "ass=karaoke_dynamics.ass" -c:a copy result.mp4
```

## 9. Цветокор / LUT
```bash
# .cube LUT (film look / teal-orange)
ffmpeg -y -i raw_render.mp4 -vf "lut3d=file='cinematic_vibe.cube'" -c:a copy graded_film.mp4
# мануальный (контраст/насыщенность/охлаждение)
ffmpeg -y -i input.mp4 -vf "eq=contrast=1.1:brightness=-0.02:saturation=1.3,hue=h=5" -c:a copy corrected.mp4
```

## 10. Скорость / GIF
```bash
# slow-mo ×2 (видео setpts + аудио atempo)
ffmpeg -y -i input.mp4 -filter_complex "[0:v]setpts=2.0*PTS[v];[0:a]atempo=0.5[a]" -map "[v]" -map "[a]" output_slow.mp4
# бумеранг (forward+reverse)
ffmpeg -y -i clip.mp4 -filter_complex "[0:v]reverse[r];[0:v][r]concat=n=2:v=1:a=0" output_boomerang.mp4
# GIF c генерацией палитры (качество)
ffmpeg -y -i video.mp4 -filter_complex "[0:v]fps=12,scale=480:-1:flags=lanczos,split[a][b];[a]palettegen[p];[b][p]paletteuse" animation.gif
```

## 11. Image — PIL + ffprobe
```python
# upscale ×2 LANCZOS + UnsharpMask (анти-мыло)
from PIL import Image, ImageFilter
img = Image.open('input.webp').convert('RGB'); w,h = img.size
up = img.resize((w*2,h*2), Image.Resampling.LANCZOS)
up.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3)).save('output_4k.jpg', quality=95, subsampling=0)
# оверлей текста с обводкой (мем/watermark) — anchor mm
from PIL import ImageDraw, ImageFont
d=ImageDraw.Draw(img); f=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",48)
d.text((w/2,h/2),"LIMITED EDITION",font=f,fill="white",stroke_width=2,stroke_fill="black",anchor="mm"); img.save('branded.png')
```
```bash
ffprobe -v error -show_entries stream=width,height,codec_name,pix_fmt -of json input.mp4   # детект
ffmpeg -y -i image.webp output.png                                                          # webp→png
```
→ Забрать: sidechaincompress-ducking (порог 0.15/ratio4), loudnorm I=-16 (соцсети), GIF palettegen/paletteuse, PIL UnsharpMask-апскейл, бумеранг reverse+concat. (наш video-editor: silence_cut/beat_sync/transitions/color_grade уже покрывают; их eq/lut3d/boomerang — referenced patterns.)

---

## 12. Переходы — xfade
```bash
# dissolve переход 1с между двумя 5с-клипами (offset=len-dur=4)
ffmpeg -y -i clip1.mp4 -i clip2.mp4 -filter_complex \
"[0:v][1:v]xfade=transition=dissolve:duration=1:offset=4[v];[0:a][1:a]acrossfade=d=1[a]" \
-map "[v]" -map "[a]" output_fade.mp4
# transition= типы: fade · wipeleft/wiperight · circleopen/circleclose · slideup/slidedown · dissolve
# (требует одинаковые res/fps/pix_fmt у обоих клипов)
```

## 13. Композ — chromakey / blend / PiP
```bash
# зелёный экран (colorkey #00FF00) на фон
ffmpeg -y -i background.mp4 -i greenscreen_hero.mp4 -filter_complex \
"[1:v]colorkey=0x00FF00:0.1:0.1[hero_cut];[0:v][hero_cut]overlay=x=0:y=0:shortest=1[out]" -map "[out]" -c:v libx264 -pix_fmt yuv420p out.mp4
# blend Multiply (лого с прозрачностью)
ffmpeg -y -i video.mp4 -i logo.png -filter_complex "[0:v][1:v]blend=all_mode='multiply':all_opacity=0.8[out]" -map "[out]" out.mp4
# picture-in-picture (доп. видео в правый верхний угол, ширина 480)
ffmpeg -y -i main.mp4 -i pip.mp4 -filter_complex "[1:v]scale=480:-1[p];[0:v][p]overlay=x=main_w-under_w-10:y=10[out]" -map "[out]" out.mp4
```

## 14. Веб-сайты — TanStack Start → Cloudflare Workers
Скелет `/ws/website-templates/frontend/`: package.json, vite.config.ts (Vite+SSR+Cloudflare), tsconfig, components.json (shadcn), bunfig.toml, bun.lock, `src/{entry-client.tsx, entry-server.tsx, styles.css(Tailwind), routes/{__root.tsx, index.tsx}}` (файловый роутинг).
```bash
bun install
bun run build                      # Nitro/Cloudflare server-сборка
npx wrangler deploy --name "my-landing-page" --compatibility-date "2026-06-07"
```

## 15. Документы — рендер/конвертация
```bash
# PPTX → PDF (LibreOffice headless)
soffice --headless --invisible --convert-to pdf --outdir <out_dir> <in.pptx>
# PDF → JPG страницы (150 DPI) → slide-1.jpg, slide-2.jpg …
pdftoppm -jpeg -r 150 <in.pdf> <out_dir>/slide
# Excalidraw JSON → PNG
npx -y @excalidraw/utils export diagram.excalidraw --output diagram.png --width 1920
```
```javascript
// jsx_preview виджет → PNG: JSX компилируется в HTML → скриншот Puppeteer
const puppeteer = require('puppeteer');
(async () => {
  const b = await puppeteer.launch({ args: ['--no-sandbox'] });
  const p = await b.newPage(); await p.setViewport({ width: 1200, height: 800 });
  await p.goto('file:///.../compiled_widget.html', { waitUntil: 'networkidle0' });
  await p.screenshot({ path: '/.../widget_snapshot.png', fullPage: true }); await b.close();
})();
```
→ Забрать: xfade-каталог + acrossfade (наш transitions.py покрывает), colorkey/blend/PiP для композа, **wrangler deploy** паттерн (для наших лендингов), **soffice+pdftoppm+@excalidraw/utils+puppeteer-screenshot** — готовый док-рендер-конвейер (= наши export-pdf/pptx/excalidraw скиллы).

## 12b. Глитч-переход (RGB split + chromashift)
```bash
ffmpeg -y -i clip1.mp4 -i clip2.mp4 -filter_complex \
"[0:v]split[v1][v2];[v1]crop=iw:ih-20:0:10,scale=iw:ih,chromashift=cbh=10:cgh=-5[glitch];[v2][glitch]vstack=inputs=2[stacked];[stacked]scale=1920:1080[v1_final];[v1_final][1:v]xfade=transition=fade:duration=0.3:offset=4.7[v]" -map "[v]" output_glitch.mp4
```
