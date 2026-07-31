# Higgsfield sandbox — креативные видео-эффекты (ffmpeg, дословно)

## 1. Плёнка / glow
```bash
# film grain + vignette
ffmpeg -y -i input.mp4 -vf "noise=alls=12:allf=t+u,vignette=angle=PI/4" -c:v libx264 -crf 18 -c:a copy out_grain_vignette.mp4
# halation / bloom-glow (split→downscale→gblur→upscale→screen blend 0.6)
ffmpeg -y -i input.mp4 -filter_complex "[0:v]split[main][blur];[blur]scale=iw/4:-1,gblur=sigma=20:steps=2,scale=1920:1080[glow];[main][glow]blend=all_mode='screen':all_opacity=0.6" -c:v libx264 -crf 18 -c:a copy out_halation.mp4
```

## 2. Ретро / глитч
```bash
# VHS (downscale 320×240 + rgbashift + noise + neighbor upscale)
ffmpeg -y -i input.mp4 -vf "scale=320:240,rgbashift=rh=-4:rv=2:bh=4:bv=-2,noise=alls=25:allf=t,scale=1920:1080:flags=neighbor" -c:v libx264 -crf 20 -c:a copy out_vhs.mp4
# хром-аберрация (RGB shift R/B относительно G)
ffmpeg -y -i input.mp4 -vf "rgbashift=rh=-6:rv=0:gh=0:gv=0:bh=6:bv=0" -c:v libx264 -crf 18 -c:a copy out_rgb_shift.mp4
# datamosh (убрать I-frames: -g 9999 + bsf noise drop key-frames)
ffmpeg -y -i input.mp4 -an -vcodec libx264 -g 9999 -keyint_min 9999 -sc_threshold 0 -bsf:v "noise=drop=eq(key\,1)" out_datamosh.mp4
```

## 3. Свет / деградация
```bash
# light leaks (наложение футажа screen blend 0.75)
ffmpeg -y -i main.mp4 -i light_leak.mp4 -filter_complex "[1:v]scale=1920:1080[leak];[0:v][leak]blend=all_mode='screen':all_opacity=0.75" -c:v libx264 -crf 18 -c:a copy out_light_leak.mp4
# 8-bit dither / color banding (16 цветов + Floyd-Steinberg)
ffmpeg -y -i input.mp4 -filter_complex "[0:v]format=rgb24,palettegen=colors=16[pal];[0:v][pal]paletteuse=dither=floyd_steinberg" -c:v libx264 -crf 18 out_dither.mp4
```

## 4. Scene-detect
```bash
# таймкоды смены сцен в файл (порог 0.4)
ffmpeg -y -i input.mp4 -vf "select='gt(scene,0.4)',metadata=print:file=scene_cuts.txt" -f null -
# извлечь ключевые кадры на смене сцен
ffmpeg -y -i input.mp4 -filter_complex "select='gt(scene,0.4)'" -vsync vfr -frame_pts true keyframes_%03d.png
```

## 5. Деноиз / шарп / дефликер
```bash
ffmpeg -y -i input.mp4 -vf "nlmeans=s=1.0:p=7:r=15" -c:v libx264 -crf 17 -c:a copy out_nlmeans.mp4    # HQ denoise (медленный)
ffmpeg -y -i input.mp4 -vf "hqdn3d=luma_spatial=4:chroma_spatial=3:luma_tmp=6:chroma_tmp=4.5" -c:v libx264 -crf 18 -c:a copy out_hqdn3d.mp4  # быстрый
ffmpeg -y -i input.mp4 -vf "unsharp=luma_msize_x=5:luma_msize_y=5:luma_amount=1.2:chroma_amount=0.0" -c:v libx264 -crf 18 -c:a copy out_sharpen.mp4
ffmpeg -y -i input.mp4 -vf "deflicker=size=10:mode=pm:bypass=0" -c:v libx264 -crf 18 -c:a copy out_deflicker.mp4   # таймлапс/LED мерцание
```
→ Забрать как стиль-пресеты в video-editor: halation screen-blend (киношный glow), VHS-стэк, rgbashift, light-leak screen-overlay, scene-detect для авто-нарезки, hqdn3d+unsharp для cleanup AI-видео. (Это стандартные ffmpeg-рецепты — не HF-секреты; полезны как cookbook.)
