# Higgsfield sandbox — титры/анимация · multi-clip монтаж · color-match · платформенные пресеты · aspect

## 1. Титры / анимация текста (drawtext, движок t/n)
```bash
# typewriter (trunc(t*15) символов/с)
ffmpeg -y -i input.mp4 -vf "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='SYSTEM REBOOT...':fontcolor=white:fontsize=40:x=100:y=h/2:text='%{expr\:text_source\:0\:trunc(t*15)}'" -c:v libx264 -crf 18 -c:a copy typewriter.mp4
# (надёжнее: посимвольно через ASS {\k})
# slide-in lower-third (drawbox+drawtext с x=if(lt(t,0.5),...))
ffmpeg -y -i input.mp4 -filter_complex "[0:v]drawbox=x='if(lt(t,0.5),-w+ow/0.5*t,if(gt(t,5),-w+ow-ow/0.5*(t-5),50))':y=h-180:w=600:h=100:color=black@0.7:t=fill[box];[box]drawtext=...:text='AUDIT AGENT':fontcolor=cyan:fontsize=24:x='if(lt(t,0.5),-w+ow/0.5*t+20,...)':y=h-160" -c:v libx264 -crf 18 -c:a copy lower_third.mp4
# fade-in/out текста (alpha=if(lt(t,1),t,if(gt(t,5),1-(t-5),1)))
ffmpeg -y -i input.mp4 -vf "drawtext=...:text='FADE':fontsize=48:x=(w-tw)/2:y=(h-th)/2:alpha='if(lt(t,1),t,if(gt(t,5),1-(t-5),1))'" -c:v libx264 -crf 18 -c:a copy fade_text.mp4
# end-card с CTA (lavfi color + лого overlay + 2 анимир. drawtext)
ffmpeg -y -f lavfi -i color=c=0x0d0d0d:s=1920x1080:d=5 -i logo.png -filter_complex "[1:v]scale=200:-1[logo];[0:v][logo]overlay=(W-w)/2:250[bg];[bg]drawtext=...:text='PROJECT COMPLETED':fontsize=40:x=(w-tw)/2:y=600:alpha='if(lt(t,1.5),t/1.5,1)',drawtext=...:text='Click link in bio':fontsize=28:x=(w-tw)/2:y=700:alpha='if(lt(t,2.5),0,if(lt(t,3.5),(t-2.5),1))'[out]" -map "[out]" -c:v libx264 -pix_fmt yuv420p endcard.mp4
```

## 2. Multi-clip xfade + beat-sync
```bash
# цепочка xfade для N клипов, накопит. offset = (prev_offset+prev_dur)-dur. 3×5с, переход 1с → offset 4, 8
ffmpeg -y -i clip1.mp4 -i clip2.mp4 -i clip3.mp4 -filter_complex "[0:v][1:v]xfade=transition=hlslice:duration=1:offset=4[v01];[v01][2:v]xfade=transition=circlecrop:duration=1:offset=8[vout]" -map "[vout]" -c:v libx264 -crf 18 out_xfade_chain.mp4
```
```python
# beat-sync: нарезать клипы по таймкодам битов (мс) → concat + наложить аудио
import subprocess
def beat_sync(srcs, audio, beats, out):   # beats=[1200,2400,3600,...] мс
    segs=[]; prev=0.0
    for i,b in enumerate(beats):
        cur=b/1000.0; seg=f"seg_{i}.mp4"
        subprocess.run(['ffmpeg','-y','-ss',str(prev),'-to',str(cur),'-i',srcs[i%len(srcs)],
            '-c:v','libx264','-crf','18','-r','30','-pix_fmt','yuv420p','-an',seg])
        segs.append(seg); prev=cur
    open("cl.txt","w").write("".join(f"file '{s}'\n" for s in segs))
    subprocess.run(['ffmpeg','-y','-f','concat','-safe','0','-i','cl.txt','-i',audio,'-c:v','copy','-c:a','aac','-shortest',out])
```
(= наш beat_sync_edit.py через librosa beat-detect.)

## 3. Color-match / white balance
```bash
ffmpeg -y -i input.mp4 -vf "colorlevels=rimin=0.02:gimin=0.01:bimin=0.0:rimax=0.98:gimax=0.97:bimax=1.0" -c:v libx264 -crf 18 -c:a copy wb.mp4   # баланс белого по каналам
ffmpeg -y -i input.mp4 -vf "curves=preset=vintage" -c:v libx264 -crf 18 -c:a copy vintage.mp4                                                  # кривые-пресет
ffmpeg -y -i raw_log.mp4 -vf "lut3d=file=slog3_to_rec709.cube" -c:v libx264 -crf 17 -c:a copy graded.mp4                                       # S-Log3→Rec.709 LUT (выравнивание камер)
```

## 4. Платформенный пресет (TikTok/Reels/Shorts) ⭐
H.264 High@4.2, yuv420p, GOP=2с (точный скраббинг+луп), аудио **-14 LUFS** (ITU-R BS.1770-4).
```bash
ffmpeg -y -i input.mp4 -c:v libx264 -profile:v high -level:v 4.2 -pix_fmt yuv420p -r 30 -g 60 -keyint_min 60 -sc_threshold 0 -bf 2 -b:v 6M -maxrate 10M -bufsize 12M -c:a aac -b:a 320k -ar 48000 -af "loudnorm=I=-14:LRA=11:TP=-1.5" mobile_ready.mp4
```

## 5. Aspect / safe-zones
```bash
# blurred-bg fill 16:9/1:1 → 9:16 (boxblur 40 фон + центр fg)
ffmpeg -y -i input_horizontal.mp4 -filter_complex "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=luma_radius=40:luma_power=3[bg];[0:v]scale=1080:-1[fg];[bg][fg]overlay=x=(W-w)/2:y=(H-h)/2:format=rgb[outv]" -map "[outv]" -map 0:a? -c:v libx264 -crf 18 -pix_fmt yuv420p vertical_filled.mp4
# letterbox/pillarbox (вписать в 1920×1080 + pad)
ffmpeg -y -i input.mp4 -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black" -c:v libx264 -crf 18 -c:a copy letterbox.mp4
# safe-zones оверлей (TikTok UI: top 220px, правый sidebar, bottom 400px красным @0.25 для контроля)
ffmpeg -y -i input_vertical.mp4 -filter_complex "[0:v]drawbox=x=0:y=0:w=iw:h=220:color=red@0.25:t=fill[top];[top]drawbox=x=iw-180:y=250:w=180:h=ih-650:color=red@0.25:t=fill[sb];[sb]drawbox=x=0:y=ih-400:w=iw:h=400:color=red@0.25:t=fill" -c:v libx264 -crf 18 -c:a copy safe_check.mp4
```
→ ⭐ Забрать: **TikTok/Reels пресет (-14 LUFS + GOP 2s + high@4.2)** = финальный экспорт-стандарт; safe-zones (top220/sidebar/bottom400); blurred-bg fill (как наш montage); xfade накопит-offset формула; beat-sync по таймкодам. (наш video-editor karaoke/beat_sync/reframe/color_grade частично сильнее.)
